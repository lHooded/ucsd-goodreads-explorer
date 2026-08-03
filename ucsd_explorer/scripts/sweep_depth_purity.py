#!/usr/bin/env python3
"""Sweep depth × purity × curator for more voters without quality loss."""
from __future__ import annotations

import json
import math
from pathlib import Path

import duckdb

from ucsd_explorer import db as dbmod
from ucsd_explorer.db import EXPLORER_DB, GLOBALS
from ucsd_explorer.ranking import (
    _curator_user_weight_sql,
    _rank_dynamic,
    curator_elite_keep_expr,
    normie_gate_params,
)
from ucsd_explorer.taste import _configure_duckdb, parse_poll_chart

con = duckdb.connect(str(EXPLORER_DB), read_only=True)
_configure_duckdb(con)
dbmod._CON = con

catalog = dict(
    fiction_only=True,
    exclude_picture_books=True,
    exclude_derivatives=True,
    exclude_comics=True,
    collapse_duplicates=True,
    apply_format_weight=True,
)
p0a = GLOBALS.get("global_p5_all", GLOBALS["global_p5"])
c0a = GLOBALS.get("global_mean_all", GLOBALS["global_mean"])
p0s = GLOBALS.get("global_p5_sf", GLOBALS["global_p5"])
c0s = GLOBALS.get("global_mean_sf", GLOBALS["global_mean"])

SCHOOL = [
    "1984",
    "Pride and Prejudice",
    "Brave New World",
    "Animal Farm",
    "Slaughterhouse-Five",
    "The Great Gatsby",
    "The Catcher in the Rye",
    "To Kill a Mockingbird",
    "Fahrenheit 451",
    "The Hobbit",
    "Hamlet",
    "Macbeth",
]
TARGETS = [
    p["title"] for p in parse_poll_chart() if p["rank"] <= 21 and p["title"] != "Hamlet"
]


def resolve(titles):
    out = []
    for t in titles:
        if "Moby" in t:
            hit = con.execute(
                """SELECT work_id,title,n FROM work_scores
              WHERE title ILIKE '%Moby-Dick%' OR title ILIKE 'Moby Dick%'
              ORDER BY n DESC LIMIT 1"""
            ).fetchone()
        else:
            hit = con.execute(
                """SELECT work_id,title,n FROM work_scores
              WHERE title=? OR title ILIKE ?||' (%' OR title ILIKE ?||'%'
              ORDER BY CASE WHEN title=? THEN 0 WHEN title ILIKE ?||' (%' THEN 1 ELSE 2 END, n DESC
              LIMIT 1""",
                [t, t, t, t, t],
            ).fetchone()
        if hit:
            out.append({"q": t, "work_id": hit[0], "global_n": int(hit[2])})
    return out


targets = resolve(TARGETS)
schools = resolve(SCHOOL)
target_ids = {x["work_id"] for x in targets}
school_ids = {x["work_id"] for x in schools}
gn = {r[0]: int(r[1]) for r in con.execute("SELECT work_id,n FROM work_scores").fetchall()}


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def n_active(cs, depth, purity):
    _we, gate_sql, gate_args, _ = _curator_user_weight_sql(
        pct=True,
        mode="deweight",
        strictness=cs,
        deep=True,
        normie_depth=depth,
        normie_purity=purity,
    )
    keep = curator_elite_keep_expr(cs)
    return con.execute(
        f"""
      WITH curator_pool AS (
        SELECT c.*, row_number() OVER (ORDER BY c.curator_pct_weight DESC) AS elite_rank,
               count(*) OVER () AS n_pass
        FROM user_curator_deep_weight c WHERE TRUE {gate_sql}
      )
      SELECT count(*) FROM curator_pool WHERE elite_rank <= {keep}
    """,
        gate_args,
    ).fetchone()[0]


def run(cs, depth, purity, sf_only):
    ranked, _ = _rank_dynamic(
        method="curator_deep_pct_tilt",
        min_n=5 if sf_only else 10,
        max_n=0,
        bayesian_m=30.0,
        p0=p0s if sf_only else p0a,
        c0=c0s if sf_only else c0a,
        picky_max=GLOBALS["median_user_five_rate"],
        q="",
        limit=120,
        taste=None,
        sf_only=sf_only,
        catalog=catalog,
        curator_strictness=float(cs),
        curator_strictness_mode="deweight",
        normie_depth=float(depth),
        normie_purity=float(purity),
    )
    items = []
    for i, row in enumerate(ranked, 1):
        wid = row[0]
        items.append(
            {
                "rank": i,
                "work_id": wid,
                "title": row[2],
                "votes": int(row[5]),
                "global_n": gn.get(wid, 0),
                "is_target": wid in target_ids,
                "is_school": wid in school_ids,
            }
        )
    top50, top100 = items[:50], items[:100]
    obsc_cut = 8000 if sf_only else 15000
    pop_cut = 20000 if sf_only else 50000
    obscure = [x for x in top100 if x["global_n"] < obsc_cut]
    popular = [x for x in top50 if x["global_n"] >= pop_cut]
    return {
        "n_active": n_active(cs, depth, purity),
        "s50": sum(1 for x in top50 if x["is_school"]),
        "t50": sum(1 for x in top50 if x["is_target"]),
        "med_all": med([x["votes"] for x in top100]),
        "med_obscure": med([x["votes"] for x in obscure]) if obscure else None,
        "med_popular": (
            med([x["votes"] for x in popular])
            if popular
            else med([x["votes"] for x in top50])
        ),
        "top8": [x["title"][:36] for x in top50[:8]],
    }


# Baseline: old combined ~65 feel (depth 65 + purity ~55–65)
print("Baseline depth65 purity55…", flush=True)
base_all = run(20, 65, 55, False)
base_sf = run(20, 65, 55, True)
print("  ALL", {k: base_all[k] for k in ("n_active", "s50", "med_popular", "med_obscure")})
print("  SF ", {k: base_sf[k] for k in ("n_active", "s50", "med_popular", "med_obscure")})

# Acceptable = no worse than baseline on school/votes floors, maximize active + SF obscure
# Floors relative to baseline with a little slack.
ALL_POP_FLOOR = max(180, int((base_all["med_popular"] or 0) * 0.75))
ALL_OBSC_FLOOR = max(100, int((base_all["med_obscure"] or 0) * 0.75))
SF_OBSC_FLOOR = max(40, int((base_sf["med_obscure"] or 0)))  # at least match baseline SF
S50_MAX = max(2, base_all["s50"] + 1)

DEPTHS = [40, 50, 55, 60, 65, 70, 80]
PURITIES = [0, 25, 35, 45, 55, 65, 80]
CURS = [0, 15, 20, 35]

rows = []
for cs in CURS:
    for d in DEPTHS:
        for p in PURITIES:
            print(f"rank cur={cs} d={d} p={p}…", flush=True)
            allr = run(cs, d, p, False)
            sfr = run(cs, d, p, True)
            gates = normie_gate_params(d, p)
            # Hard constraints for "no hurt"
            ok = (
                allr["s50"] <= S50_MAX
                and (allr["med_popular"] or 0) >= ALL_POP_FLOOR
                and (allr["med_obscure"] or 0) >= ALL_OBSC_FLOOR
                and (sfr["med_obscure"] or 0) >= SF_OBSC_FLOOR
            )
            # Score: maximize curators + SF obscure, mild school penalty
            score = (
                math.log10(max(allr["n_active"], 1)) * 3.0
                + math.log10(max(sfr["med_obscure"] or 1, 1)) * 2.0
                + math.log10(max(allr["med_obscure"] or 1, 1))
                - 1.5 * allr["s50"]
                - 0.5 * sfr["s50"]
            )
            if not ok:
                score -= 20.0
            rows.append(
                {
                    "curator_s": cs,
                    "depth": d,
                    "purity": p,
                    "ok": ok,
                    "score": round(score, 3),
                    "gates": gates,
                    "all": {k: allr[k] for k in allr if k != "top8"},
                    "sf": {k: sfr[k] for k in sfr if k != "top8"},
                    "all_top8": allr["top8"],
                    "sf_top8": sfr["top8"],
                }
            )

ok_rows = [r for r in rows if r["ok"]]
best = max(ok_rows or rows, key=lambda r: r["score"])
# Also max-active among ok
most = max(ok_rows or rows, key=lambda r: (r["all"]["n_active"], r["score"]))

# vs baseline active gain
print("\nOK settings:", len(ok_rows), "/", len(rows))
print(
    "BEST score",
    best["curator_s"],
    best["depth"],
    best["purity"],
    "active",
    best["all"]["n_active"],
    "s50",
    best["all"]["s50"],
    "pop",
    best["all"]["med_popular"],
    "obsc",
    best["all"]["med_obscure"],
    "sf_obsc",
    best["sf"]["med_obscure"],
)
print(
    "MOST active ok",
    most["curator_s"],
    most["depth"],
    most["purity"],
    "active",
    most["all"]["n_active"],
    "gain vs base",
    most["all"]["n_active"] - base_all["n_active"],
)
print("best top8", best["all_top8"])

# Top 10 ok by score
top = sorted(ok_rows or rows, key=lambda r: -r["score"])[:12]
print("\nTop ok:")
for r in top:
    print(
        f"  cur={r['curator_s']:2} d={r['depth']:2} p={r['purity']:2} "
        f"n={r['all']['n_active']:5} s50={r['all']['s50']} "
        f"pop={r['all']['med_popular']} obsc={r['all']['med_obscure']} "
        f"sf_obsc={r['sf']['med_obscure']} score={r['score']}"
    )

payload = {
    "baseline": {"curator": 20, "depth": 65, "purity": 55, "all": base_all, "sf": base_sf},
    "floors": {
        "s50_max": S50_MAX,
        "all_pop": ALL_POP_FLOOR,
        "all_obsc": ALL_OBSC_FLOOR,
        "sf_obsc": SF_OBSC_FLOOR,
    },
    "recommended": best,
    "most_active_ok": most,
    "top_ok": [{k: v for k, v in r.items() if k not in ("all_top8", "sf_top8")} for r in top],
    "n_ok": len(ok_rows),
    "n_tried": len(rows),
}
Path("ucsd_explorer/data/depth_purity_sweep.json").write_text(json.dumps(payload, indent=2, default=str))
Path("ucsd_explorer/data/deep_strictness_recommend.json").write_text(
    json.dumps(
        {
            "method": "curator_deep_pct_tilt",
            "curator_strictness": best["curator_s"],
            "curator_strictness_mode": "deweight",
            "normie_depth": best["depth"],
            "normie_purity": best["purity"],
            "n_active": best["all"]["n_active"],
            "med_votes_popular": best["all"]["med_popular"],
            "med_votes_obscure": best["all"]["med_obscure"],
            "sf_med_votes_obscure": best["sf"]["med_obscure"],
            "s50": best["all"]["s50"],
            "note": "Split depth/purity; maximize curators subject to vote/school floors vs baseline.",
        },
        indent=2,
    )
    + "\n"
)
print("done")
con.close()
dbmod._CON = None

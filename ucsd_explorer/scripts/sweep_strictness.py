#!/usr/bin/env python3
"""Validate new strictness endpoints + dual sweep for optimal settings."""
import json
import math
from pathlib import Path

import duckdb

from ucsd_explorer import db as dbmod
from ucsd_explorer.db import EXPLORER_DB, GLOBALS
from ucsd_explorer.ranking import (
    CURATOR_ELITE_FLOOR,
    _curator_user_weight_sql,
    _rank_dynamic,
    curator_elite_keep_expr,
    normie_strictness_params,
)
from ucsd_explorer.taste import _configure_duckdb, parse_poll_chart

con = duckdb.connect(str(EXPLORER_DB))
_configure_duckdb(con)
dbmod._CON = con

print("=== param curve ===")
for ns in range(0, 101, 10):
    print(f"  normie {ns:3}: {normie_strictness_params(ns)}")

print("\n=== endpoint probes ===")
catalog = dict(
    fiction_only=True,
    exclude_picture_books=True,
    exclude_derivatives=True,
    exclude_comics=True,
    collapse_duplicates=True,
    apply_format_weight=True,
)
p0, c0 = GLOBALS["global_p5"], GLOBALS["global_mean"]


def probe(cs, ns, label):
    we, gate_sql, gate_args, et = _curator_user_weight_sql(
        pct=True, mode="deweight", strictness=cs, deep=True, normie_strictness=ns
    )
    keep = curator_elite_keep_expr(cs)
    n = con.execute(
        f"""
        WITH curator_pool AS (
          SELECT c.*, row_number() OVER (ORDER BY c.curator_pct_weight DESC) AS elite_rank,
                 count(*) OVER () AS n_pass
          FROM user_curator_deep_weight c WHERE TRUE {gate_sql}
        ),
        curator_active AS (SELECT * FROM curator_pool WHERE elite_rank <= {keep})
        SELECT (SELECT count(*) FROM curator_pool), (SELECT count(*) FROM curator_active)
        """,
        gate_args,
    ).fetchone()
    ranked, _ = _rank_dynamic(
        method="curator_deep_pct_tilt",
        min_n=10,
        max_n=0,
        bayesian_m=30,
        p0=p0,
        c0=c0,
        picky_max=GLOBALS["median_user_five_rate"],
        q="",
        limit=15,
        taste=None,
        sf_only=False,
        catalog=catalog,
        curator_strictness=float(cs),
        curator_strictness_mode="deweight",
        normie_strictness=float(ns),
    )
    votes = [int(r[5]) for r in ranked[:10]]
    print(
        f"{label}: pool={n[0]} active={n[1]} top10_votes med={sorted(votes)[len(votes)//2]} "
        f"max={max(votes)} titles={[r[2][:24] for r in ranked[:4]]}"
    )
    return dict(
        label=label,
        cs=cs,
        ns=ns,
        pool=n[0],
        active=n[1],
        med_votes=sorted(votes)[len(votes) // 2],
        max_votes=max(votes),
        top=[r[2] for r in ranked[:8]],
        votes=votes,
    )


endpoints = []
for cs, ns, lab in [
    (0, 0, "both off"),
    (0, 100, "normie max"),
    (100, 0, "curator max"),
    (100, 100, "both max"),
    (50, 70, "mid"),
    (35, 70, "preset-ish"),
]:
    endpoints.append(probe(cs, ns, lab))

assert endpoints[0]["active"] > 5000, "off should keep huge cohort"
assert endpoints[2]["active"] <= CURATOR_ELITE_FLOOR + 5, (
    f"curator max should be ~100, got {endpoints[2]['active']}"
)
assert endpoints[1]["med_votes"] <= 80, (
    f"normie max votes should be <=50ish, got {endpoints[1]['med_votes']}"
)
print("endpoint asserts OK")

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
TARGETS = [p["title"] for p in parse_poll_chart() if p["rank"] <= 21 and p["title"] != "Hamlet"]


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
            out.append({"q": t, "work_id": hit[0], "title": hit[1], "global_n": int(hit[2])})
    return out


targets = resolve(TARGETS)
schools = resolve(SCHOOL)
target_ids = {x["work_id"] for x in targets}
school_ids = {x["work_id"] for x in schools}
gn = {r[0]: int(r[1]) for r in con.execute("SELECT work_id,n FROM work_scores").fetchall()}
poll_ids = {r[0] for r in con.execute("SELECT work_id FROM poll_works").fetchall()}


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


CUR_S = [0, 20, 35, 50, 70, 100]
NORM_S = [0, 25, 40, 55, 70, 85, 100]
rows = []
for cs in CUR_S:
    for ns in NORM_S:
        print(f"sweep cur={cs} norm={ns}…", flush=True)
        we, gate_sql, gate_args, _ = _curator_user_weight_sql(
            pct=True, mode="deweight", strictness=cs, deep=True, normie_strictness=ns
        )
        keep = curator_elite_keep_expr(cs)
        n_active = con.execute(
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
        ranked, _ = _rank_dynamic(
            method="curator_deep_pct_tilt",
            min_n=10,
            max_n=0,
            bayesian_m=30.0,
            p0=p0,
            c0=c0,
            picky_max=GLOBALS["median_user_five_rate"],
            q="",
            limit=150,
            taste=None,
            sf_only=False,
            catalog=catalog,
            curator_strictness=float(cs),
            curator_strictness_mode="deweight",
            normie_strictness=float(ns),
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
                    "is_poll": wid in poll_ids,
                }
            )
        top100, top50 = items[:100], items[:50]
        obscure = [x for x in top100 if x["global_n"] < 15000]
        popular = [x for x in top50 if x["global_n"] >= 50000]
        t50 = sum(1 for x in top50 if x["is_target"])
        s50 = sum(1 for x in top50 if x["is_school"])
        t100 = sum(1 for x in top100 if x["is_target"])
        s100 = sum(1 for x in top100 if x["is_school"])
        poll100 = sum(1 for x in top100 if x["is_poll"])
        med_obsc = med([x["votes"] for x in obscure]) if obscure else None
        med_pop = (
            med([x["votes"] for x in popular])
            if popular
            else med([x["votes"] for x in top50])
        )
        med_all = med([x["votes"] for x in top100])
        q = -2.5 * s50 - 1.0 * (s100 - s50) + 0.35 * t50 + 0.15 * (t100 - t50)
        if med_obsc:
            q += min(med_obsc / 80.0, 3.0)
        if med_pop is not None:
            if med_pop < 25:
                q -= (25 - med_pop) / 8.0
            elif med_pop > 400:
                q -= math.log10(med_pop / 400.0) * 2.0
        if n_active < 40:
            q -= (40 - n_active) / 15.0
        rows.append(
            {
                "curator_s": cs,
                "normie_s": ns,
                "n_active": n_active,
                "t50": t50,
                "s50": s50,
                "t100": t100,
                "s100": s100,
                "poll100": poll100,
                "med_votes_top100": med_all,
                "med_votes_obscure": med_obsc,
                "med_votes_popular": med_pop,
                "n_obscure_top100": len(obscure),
                "quality": round(q, 2),
                "normie_gates": normie_strictness_params(ns),
                "top10": [
                    {
                        "title": x["title"][:40],
                        "votes": x["votes"],
                        "tag": (
                            "T"
                            if x["is_target"]
                            else ("S" if x["is_school"] else ("P" if x["is_poll"] else ""))
                        ),
                    }
                    for x in top50[:10]
                ],
            }
        )

best = max(rows, key=lambda r: r["quality"])
qs = sorted([r["quality"] for r in rows], reverse=True)
cut = qs[max(0, len(qs) // 4)]
cands = [r for r in rows if r["quality"] >= cut]
cands.sort(
    key=lambda r: (
        -1 if 40 <= (r["med_votes_popular"] or 0) <= 250 else 0,
        -(r["med_votes_obscure"] or 0),
        -r["quality"],
        r["s50"],
        -r["t50"],
    )
)
rec = cands[0]

payload = {
    "endpoints": endpoints,
    "sweep": [{k: v for k, v in r.items() if k != "top10"} for r in rows],
    "best_quality": {k: v for k, v in best.items() if k != "top10"},
    "recommended": {k: v for k, v in rec.items() if k != "top10"},
    "recommended_top10": rec["top10"],
    "design": {
        "curator": "0=off; 100=top ~100 by weight; log-linear K",
        "normie": "0=off; primary=min_deep log-linear 2→20; share secondary; max≈≤50 popular votes",
    },
}
Path("ucsd_explorer/data/deep_normie_strictness_sweep.json").write_text(
    json.dumps(payload, indent=2)
)
Path("ucsd_explorer/data/deep_strictness_recommend.json").write_text(
    json.dumps(
        {
            "method": "curator_deep_pct_tilt",
            "curator_strictness": rec["curator_s"],
            "curator_strictness_mode": "deweight",
            "normie_strictness": rec["normie_s"],
            "quality": rec["quality"],
            "n_active": rec["n_active"],
            "med_votes_popular": rec["med_votes_popular"],
            "med_votes_obscure": rec["med_votes_obscure"],
        },
        indent=2,
    )
    + "\n"
)

print(
    "\nBEST",
    best["curator_s"],
    best["normie_s"],
    "q",
    best["quality"],
    "active",
    best["n_active"],
    "s50",
    best["s50"],
    "pop",
    best["med_votes_popular"],
    "obsc",
    best["med_votes_obscure"],
)
print(
    "REC ",
    rec["curator_s"],
    rec["normie_s"],
    "q",
    rec["quality"],
    "active",
    rec["n_active"],
    "s50",
    rec["s50"],
    "pop",
    rec["med_votes_popular"],
    "obsc",
    rec["med_votes_obscure"],
)
for x in rec["top10"]:
    print(f"  [{x['tag']:1}] {x['title']}  v={x['votes']}")
print("\nquality grid")
print("cur\\norm", *NORM_S)
for cs in CUR_S:
    vals = [
        next(r["quality"] for r in rows if r["curator_s"] == cs and r["normie_s"] == ns)
        for ns in NORM_S
    ]
    print(f"{cs:7}", *[f"{v:5.1f}" for v in vals])
print("\nn_active grid")
for cs in CUR_S:
    vals = [
        next(r["n_active"] for r in rows if r["curator_s"] == cs and r["normie_s"] == ns)
        for ns in NORM_S
    ]
    print(f"{cs:7}", *[f"{v:5}" for v in vals])
print("\npopular votes grid")
for cs in CUR_S:
    vals = [
        next(
            r["med_votes_popular"]
            for r in rows
            if r["curator_s"] == cs and r["normie_s"] == ns
        )
        for ns in NORM_S
    ]
    print(f"{cs:7}", *[f"{v:5}" for v in vals])
con.close()
dbmod._CON = None
print("done")

#!/usr/bin/env python3
"""Pivotal: how many deep curators, and equal vs weighted?

Before reverse-engineering a new jury, check whether capping deep curators
to ~4.8k (equal votes) hurts vs the weighted full deep pool the app prefers.

Also flag odd pockets inside deep curators (high commercial share, tiny depth,
extreme activity) so we don't treat the mint as gospel.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_deep_size_sweep
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    load_eval_sets,
    materialize_base,
)
from curators_explorer.scripts.research_residual_enthusiasm import (
    author_disjoint_sets,
    heldout_recall,
    load_sticky,
    probe_metrics,
    rank_scored,
    top15,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "deep_size_sweep.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "DEEP_SIZE_SWEEP_REPORT.md"

MAX_N = 120_000
MAX_HIGHS = 12
MAX_LOWS = 12
LOW_MAX = 3
MIN_APPEAR = 40
SHRINK_K = 50.0
SEED = 11

# Caps to try (None = all deep). Include prior diagnosis size ~4774.
CAPS = [2000, 3000, 4774, 6000, 8000, 10000, 15000, None]
# Weight modes: equal; raw curator weight; app-like powers
WEIGHT_MODES = [
    ("equal", None),
    ("w_raw", 1.0),  # multiply by stored weight as-is (like expo applied to already-scored w)
    ("w_expo_0.6", 0.6),  # ~deweight slider 15
    ("w_expo_1.0", 1.0),  # ~deweight slider 25 — but applied to weight again; see note
]

# Cleaner: for weighted modes use power(curator_pct_weight, expo) with expo in {0.6,1,2}
# and "raw" = use curator_pct_weight directly (expo=1 on stored score).
WEIGHT_SPECS = [
    ("equal", "1.0"),
    ("stored_w", "j.w"),
    ("stored_w_pow0.6", "power(greatest(j.w, 1e-9), 0.6)"),
    ("stored_w_pow1", "power(greatest(j.w, 1e-9), 1.0)"),
    ("stored_w_pow2", "power(greatest(j.w, 1e-9), 2.0)"),
]


def ensure_deep_table(con) -> int:
    n = con.execute("SELECT count(*) FROM ex.user_curator_deep_weight").fetchone()[0]
    print(f"  deep curators available: {n:,}", flush=True)
    return int(n)


def mass_profile(con) -> dict[str, Any]:
    total = float(
        con.execute("SELECT sum(curator_pct_weight) FROM ex.user_curator_deep_weight").fetchone()[0]
    )
    rows = []
    for k in [500, 1000, 2000, 3000, 4774, 6000, 8000, 10000, 15000, 19841]:
        r = con.execute(
            f"""
            WITH ranked AS (
                SELECT curator_pct_weight AS w,
                       row_number() OVER (ORDER BY curator_pct_weight DESC) AS rn
                FROM ex.user_curator_deep_weight
            )
            SELECT count(*), sum(w), sum(w) / {total}
            FROM ranked WHERE rn <= {k}
            """
        ).fetchone()
        rows.append({"top_k": k, "n": int(r[0]), "mass": float(r[1]), "mass_frac": float(r[2])})
    kish = {}
    for expo in [0.0, 0.6, 1.0, 2.0, 4.0]:
        r = con.execute(
            f"""
            WITH w AS (
                SELECT power(greatest(curator_pct_weight, 1e-9), {expo}) AS ww
                FROM ex.user_curator_deep_weight
            )
            SELECT sum(ww), (sum(ww)*sum(ww))/nullif(sum(ww*ww),0)
            FROM w
            """
        ).fetchone()
        kish[str(expo)] = {"sum_w": float(r[0]), "kish_n_eff": float(r[1])}
    return {"cum_mass": rows, "kish_by_expo": kish, "total_stored_mass": total}


def flag_weird_subsets(con) -> dict[str, Any]:
    """Pockets inside deep mint that may distort a reverse-engineered jury."""
    out: dict[str, Any] = {}
    # High commercial share near the mint cap
    out["high_com"] = con.execute(
        """
        SELECT count(*),
               avg(com_share), avg(deep_share), avg(n_deep), avg(n_normie)
        FROM ex.user_curator_deep_weight
        WHERE com_share >= 0.15
        """
    ).fetchone()
    out["high_com"] = {
        "n": int(out["high_com"][0]),
        "mean_com_share": float(out["high_com"][1] or 0),
        "mean_deep_share": float(out["high_com"][2] or 0),
        "mean_n_deep": float(out["high_com"][3] or 0),
        "mean_n_normie": float(out["high_com"][4] or 0),
    }
    # Floor deep_share (barely qualified)
    out["floor_deep_share"] = {
        "n": int(
            con.execute(
                """
                SELECT count(*) FROM ex.user_curator_deep_weight
                WHERE deep_share <= 0.40
                """
            ).fetchone()[0]
        )
    }
    # Hyper-active outliers
    out["hyper_active"] = {
        "n_rated_p99": float(
            con.execute(
                "SELECT approx_quantile(n_rated, 0.99) FROM ex.user_curator_deep_weight"
            ).fetchone()[0]
        ),
        "n_above_2k": int(
            con.execute(
                "SELECT count(*) FROM ex.user_curator_deep_weight WHERE n_rated >= 2000"
            ).fetchone()[0]
        ),
    }
    # Top-weight users' mean traits vs bottom half of deep
    out["top500_vs_bottom_half"] = {}
    for label, sql in (
        (
            "top500",
            """
            SELECT avg(deep_share), avg(com_share), avg(n_deep), avg(n_normie), avg(n_rated)
            FROM (
              SELECT * FROM ex.user_curator_deep_weight
              ORDER BY curator_pct_weight DESC LIMIT 500
            )
            """,
        ),
        (
            "bottom_half",
            """
            SELECT avg(deep_share), avg(com_share), avg(n_deep), avg(n_normie), avg(n_rated)
            FROM (
              SELECT *, row_number() OVER (ORDER BY curator_pct_weight DESC) AS rn,
                     count(*) OVER () AS n
              FROM ex.user_curator_deep_weight
            ) WHERE rn > n/2
            """,
        ),
    ):
        r = con.execute(sql).fetchone()
        out["top500_vs_bottom_half"][label] = {
            "deep_share": float(r[0]),
            "com_share": float(r[1]),
            "n_deep": float(r[2]),
            "n_normie": float(r[3]),
            "n_rated": float(r[4]),
        }
    return out


def make_jury(con, *, cap: int | None, name: str) -> int:
    if cap is None:
        con.execute(
            f"""
            CREATE OR REPLACE TABLE {name} AS
            SELECT user_id, curator_pct_weight AS w
            FROM ex.user_curator_deep_weight
            """
        )
    else:
        con.execute(
            f"""
            CREATE OR REPLACE TABLE {name} AS
            SELECT user_id, curator_pct_weight AS w
            FROM ex.user_curator_deep_weight
            ORDER BY curator_pct_weight DESC
            LIMIT {int(cap)}
            """
        )
    return int(con.execute(f"SELECT count(*) FROM {name}").fetchone()[0])


def build_pairs(con, jury: str, pairs: str) -> int:
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {pairs} AS
        WITH rated AS (
            SELECT e.user_id, e.work_id, e.rating, j.w
            FROM ex.all_rating_events e
            JOIN {jury} j USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
        ),
        highs AS (
            SELECT user_id, work_id, w,
                row_number() OVER (
                    PARTITION BY user_id
                    ORDER BY hash(user_id || '-' || work_id || '-h{SEED}')
                ) AS rn
            FROM rated WHERE rating = 5
        ),
        lows AS (
            SELECT user_id, work_id, w,
                row_number() OVER (
                    PARTITION BY user_id
                    ORDER BY hash(user_id || '-' || work_id || '-l{SEED}')
                ) AS rn
            FROM rated WHERE rating <= {LOW_MAX}
        )
        SELECT h.user_id, h.work_id AS winner, l.work_id AS loser, h.w AS w
        FROM highs h JOIN lows l USING (user_id)
        WHERE h.rn <= {MAX_HIGHS} AND l.rn <= {MAX_LOWS}
        """
    )
    return int(con.execute(f"SELECT count(*) FROM {pairs}").fetchone()[0])


def rank_pairwise(con, pairs: str, weight_sql: str) -> list[dict]:
    weight_sql_pairs = weight_sql.replace("j.w", "w")
    sql = f"""
        WITH wins AS (
            SELECT winner AS work_id,
                   sum({weight_sql_pairs})::DOUBLE AS wins,
                   count(*)::BIGINT AS n_win_edges
            FROM {pairs} GROUP BY 1
        ),
        losses AS (
            SELECT loser AS work_id,
                   sum({weight_sql_pairs})::DOUBLE AS losses,
                   count(*)::BIGINT AS n_loss_edges
            FROM {pairs} GROUP BY 1
        ),
        agg AS (
            SELECT
                coalesce(wi.work_id, lo.work_id) AS work_id,
                coalesce(wi.wins, 0) AS wins,
                coalesce(lo.losses, 0) AS losses,
                (coalesce(wi.n_win_edges, 0) + coalesce(lo.n_loss_edges, 0)) AS n_edges
            FROM wins wi
            FULL OUTER JOIN losses lo USING (work_id)
        )
        SELECT
            work_id,
            ((n_edges::DOUBLE / (n_edges + {SHRINK_K}))
              * (wins / nullif(wins + losses, 0)))::DOUBLE AS score,
            n_edges::DOUBLE AS n_c,
            0.0::DOUBLE AS n_a,
            n_edges::DOUBLE AS n_eff
        FROM agg
        WHERE n_edges >= {MIN_APPEAR}
    """
    return rank_scored(con, sql)


def main() -> None:
    t_all = time.time()
    # Need work_rarity from materialize_base
    con = _con()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    print("Setup (base tables only)…", flush=True)
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    n_deep = ensure_deep_table(con)
    adj = author_disjoint_sets(con)

    print("\n=== weight mass / Kish n_eff ===", flush=True)
    mass = mass_profile(con)
    for row in mass["cum_mass"]:
        print(
            f"  top{row['top_k']}: mass_frac={row['mass_frac']:.3f}",
            flush=True,
        )
    for expo, v in mass["kish_by_expo"].items():
        print(f"  expo={expo}: kish_n_eff={v['kish_n_eff']:.0f}", flush=True)

    print("\n=== weird pockets in deep mint ===", flush=True)
    weird = flag_weird_subsets(con)
    print(f"  high_com (com_share≥0.15): n={weird['high_com']['n']}", flush=True)
    print(f"  floor deep_share≤0.40: n={weird['floor_deep_share']['n']}", flush=True)
    print(
        f"  hyper n_rated≥2000: {weird['hyper_active']['n_above_2k']} "
        f"(p99 n_rated={weird['hyper_active']['n_rated_p99']:.0f})",
        flush=True,
    )
    t5, bh = weird["top500_vs_bottom_half"]["top500"], weird["top500_vs_bottom_half"]["bottom_half"]
    print(
        f"  top500 vs bottom-half: deep_share {t5['deep_share']:.2f} vs {bh['deep_share']:.2f}, "
        f"n_deep {t5['n_deep']:.1f} vs {bh['n_deep']:.1f}",
        flush=True,
    )

    # Reference: full deep + stored_w pairwise
    print("\n=== building full-deep pairs (reference) ===", flush=True)
    make_jury(con, cap=None, name="jury_sweep")
    n_pairs_full = build_pairs(con, "jury_sweep", "pairs_sweep")
    print(f"  pairs={n_pairs_full:,}", flush=True)
    ref_rows = rank_pairwise(con, "pairs_sweep", "w")
    ref_ids = {r["work_id"] for r in ref_rows[:50]}
    ref_probe = probe_metrics(ref_rows, ev, sticky)
    ref_hold = heldout_recall(ref_rows, adj["test_works"])
    print(
        f"  REF full+stored_w: pos50={ref_probe['pos50']} "
        f"heldout@50={ref_hold['recall@50']:.3f} sticky50={ref_probe['sticky50']}",
        flush=True,
    )

    runs = []
    # Restrict sweep weight modes to avoid explosion: equal, stored_w, stored_w_pow2
    # and caps of interest. Full factorial of CAPS × key modes.
    modes = [
        ("equal", "1.0"),
        ("stored_w", "w"),
        ("pow2", "power(greatest(w, 1e-9), 2.0)"),
    ]
    for cap in CAPS:
        label_cap = "all" if cap is None else str(cap)
        print(f"\n=== cap={label_cap} ===", flush=True)
        n_j = make_jury(con, cap=cap, name="jury_sweep")
        n_p = build_pairs(con, "jury_sweep", "pairs_sweep")
        print(f"  jury={n_j:,} pairs={n_p:,}", flush=True)
        for mode_name, wsql in modes:
            rows = rank_pairwise(con, "pairs_sweep", wsql)
            probe = probe_metrics(rows, ev, sticky)
            hold = heldout_recall(rows, adj["test_works"])
            ids50 = {r["work_id"] for r in rows[:50]}
            j50 = len(ids50 & ref_ids) / max(len(ids50 | ref_ids), 1)
            run = {
                "cap": cap,
                "cap_label": label_cap,
                "mode": mode_name,
                "n_jury": n_j,
                "n_pairs": n_p,
                "probe": probe,
                "heldout": hold,
                "jaccard50_vs_full_stored_w": j50,
                "top10": [
                    {"rank": r["rank"], "title": r["title"], "author": r["author"]}
                    for r in rows[:10]
                ],
            }
            runs.append(run)
            print(
                f"  {mode_name}: pos50={probe['pos50']} fill50={probe['filler50']} "
                f"sticky50={probe['sticky50']} held@50={hold['recall@50']:.3f} "
                f"J50_vs_ref={j50:.3f}",
                flush=True,
            )

    # Pick recommended: maximize heldout@50 then pos50 then J50 vs ref among non-degenerate
    def score_run(r: dict) -> tuple:
        return (
            r["heldout"]["recall@50"],
            r["probe"]["pos50"],
            -r["probe"]["filler50"],
            r["jaccard50_vs_full_stored_w"],
        )

    best = max(runs, key=score_run)
    # Also note best among weighted-all
    best_all_w = max(
        (r for r in runs if r["cap"] is None and r["mode"] != "equal"),
        key=score_run,
        default=None,
    )
    best_eq_cap = max(
        (r for r in runs if r["mode"] == "equal"),
        key=score_run,
        default=None,
    )

    results = {
        "meta": {
            "n_deep": n_deep,
            "ref": {
                "mode": "all+stored_w",
                "probe": ref_probe,
                "heldout": ref_hold,
                "top10": top15(ref_rows)[:10],
            },
            "note": (
                "App prefers deweight over equal elite. Kish n_eff at expo~1 is ~9k; "
                "top-4774 only holds ~58% of stored weight mass."
            ),
        },
        "mass_profile": mass,
        "weird_subsets": weird,
        "runs": runs,
        "recommendation": {
            "best_overall": {
                "cap": best["cap_label"],
                "mode": best["mode"],
                "heldout@50": best["heldout"]["recall@50"],
                "pos50": best["probe"]["pos50"],
            },
            "best_all_weighted": None
            if not best_all_w
            else {
                "mode": best_all_w["mode"],
                "heldout@50": best_all_w["heldout"]["recall@50"],
                "pos50": best_all_w["probe"]["pos50"],
            },
            "best_equal_cap": None
            if not best_eq_cap
            else {
                "cap": best_eq_cap["cap_label"],
                "heldout@50": best_eq_cap["heldout"]["recall@50"],
                "pos50": best_eq_cap["probe"]["pos50"],
            },
        },
    }
    OUT_JSON.write_text(json.dumps(results, indent=2, default=float) + "\n")

    lines = [
        "# Deep curator size × weight sweep (pivotal)",
        "",
        "Before reverse-engineering a new jury: does capping deep curators to ~focus size,",
        "or turning weights into equal votes, hurt pairwise quality?",
        "",
        "## Weight mass (caution)",
        "",
        f"- Deep pool: **{n_deep:,}** users; stored weight sum ≈ {mass['total_stored_mass']:.0f}",
        "- Cumulative mass of top-k:",
        "",
    ]
    for row in mass["cum_mass"]:
        lines.append(
            f"- top {row['top_k']:>5}: **{100*row['mass_frac']:.1f}%** of stored mass"
        )
    lines += ["", "Kish n_eff if we power-weight stored scores:", ""]
    for expo, v in mass["kish_by_expo"].items():
        lines.append(f"- expo={expo}: n_eff ≈ **{v['kish_n_eff']:.0f}**")
    lines += [
        "",
        "App guidance historically: prefer **weighted** over equal-elite; deweight≈15–25",
        "corresponds to soft power emphasis (expo ~0.6–1), not a hard top-4.8k gate.",
        "",
        "## Weird pockets in the mint (deep ≠ perfect)",
        "",
        f"- com_share ≥ 0.15: **{weird['high_com']['n']:,}** users "
        f"(mean n_deep={weird['high_com']['mean_n_deep']:.1f})",
        f"- deep_share ≤ 0.40 (near floor): **{weird['floor_deep_share']['n']:,}**",
        f"- n_rated ≥ 2000: **{weird['hyper_active']['n_above_2k']:,}** "
        f"(p99≈{weird['hyper_active']['n_rated_p99']:.0f})",
        f"- top500 vs bottom-half of deep: deep_share "
        f"{t5['deep_share']:.2f} vs {bh['deep_share']:.2f}, "
        f"n_deep {t5['n_deep']:.1f} vs {bh['n_deep']:.1f}",
        "",
        "## Pairwise sweep",
        "",
        "| cap | mode | pos50 | sticky50 | fill50 | held@50 | held@200 | J50 vs full+w |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in runs:
        lines.append(
            f"| {r['cap_label']} | {r['mode']} | {r['probe']['pos50']} | "
            f"{r['probe']['sticky50']} | {r['probe']['filler50']} | "
            f"{r['heldout']['recall@50']:.3f} | {r['heldout']['recall@200']:.3f} | "
            f"{r['jaccard50_vs_full_stored_w']:.3f} |"
        )
    lines += [
        "",
        "## Reference head (all deep, stored weight)",
        "",
    ]
    for r in ref_rows[:12]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    lines += [
        "",
        "## Recommendation (for reverse-engineering target)",
        "",
        f"- Naive best in sweep: **cap={best['cap_label']} / {best['mode']}** "
        f"(held@50={best['heldout']['recall@50']:.3f}, pos50={best['probe']['pos50']})",
    ]
    if best_all_w:
        lines.append(
            f"- Full-pool weighted: **{best_all_w['mode']}** "
            f"(held@50={best_all_w['heldout']['recall@50']:.3f}, pos50={best_all_w['probe']['pos50']})"
        )
    if best_eq_cap:
        lines.append(
            f"- Best equal-vote cap: **{best_eq_cap['cap_label']}** "
            f"(held@50={best_eq_cap['heldout']['recall@50']:.3f}, pos50={best_eq_cap['probe']['pos50']})"
        )
    lines += [
        "",
        "### Critical caution (do not skip)",
        "",
        "1. **Poll held-out / pos50 are contaminated teachers.** Deep curators are minted from",
        "   poll-depth signals. Smaller elites will look “better” on those probes partly because",
        "   they are the densest poll-aligned core — not because we independently discovered them.",
        "2. **Wider deep pools dilute pairwise and admit local canons** (e.g. full+weighted head",
        "   includes Turkish literary islands). That is a real mint imperfection to flag, not proof",
        "   that “all 20k equal” is the right jury.",
        "3. **App deweight ≠ top-4.8k hard gate.** Soft weighting keeps many users at low mass",
        "   (Kish n_eff ~9–15k at expo 0.6–1). Hard-capping to focus size threw away ~40%+ of mass.",
        "4. **For reverse-engineering:** treat as teacher something like **top ~3–8k by weight**",
        "   (sweet spot in sweep before dilution) *or* full deep with **pocket filters**",
        "   (drop near-floor deep_share / high com_share / maybe language islands), with soft",
        "   weights — and score candidate juries on **overlap with deep** + head sanity, not only",
        "   poll held-out. Watch for shortcuts that only recreate the mint score ranking.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    print(
        f"Recommendation: cap={best['cap_label']} mode={best['mode']} "
        f"held@50={best['heldout']['recall@50']:.3f} pos50={best['probe']['pos50']}",
        flush=True,
    )


if __name__ == "__main__":
    main()

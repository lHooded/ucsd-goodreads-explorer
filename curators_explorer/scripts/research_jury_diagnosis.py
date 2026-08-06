#!/usr/bin/env python3
"""Diagnose: is the mess in the jury (focus vs deep curators) or the ranking?

1) Overlap: behavioral focus top-slice vs deep curators.
2) Equal-size common books: top ~N deep curators (by weight) vs focus —
   most common 5★ books in each jury.
3) Within-jury pairwise (no anti contrast) on:
   - focus (equal votes)
   - deep-capped (equal votes)
   - deep-capped (weighted by curator weight)

If deep-capped pairwise looks like the old good curator world while focus
pairwise stays messy → jury selection is the bottleneck.
If both look similar → ordering method (or something else) is the issue.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_jury_diagnosis
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_feature_sensitivity import (
    _moments,
    build_affinity,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    load_eval_sets,
    materialize_base,
)
from curators_explorer.scripts.research_residual_enthusiasm import (
    WEIGHTS_CAREFUL,
    author_disjoint_sets,
    heldout_recall,
    load_sticky,
    load_weights,
    pick_cohorts,
    probe_metrics,
    rank_scored,
    top15,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    build_user_features,
    filler_eval,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "jury_diagnosis.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "JURY_DIAGNOSIS_REPORT.md"

MAX_N = 120_000
MAX_HIGHS = 12
MAX_LOWS = 12
LOW_MAX = 3
MIN_APPEAR = 40
SHRINK_K = 50.0
SEED = 11
COMMON_TOP = 25


def setup_juries(con, w: dict[str, Any]) -> dict[str, Any]:
    moments = _moments(con)
    g = w["gates"]
    build_affinity(
        con,
        moments,
        classic_terms=w["classic_terms"],
        anti_terms=w["anti_terms"],
        normie_terms=w["normie_terms"],
        lam_a=float(w.get("lambda_anti", 0.85)),
        lam_n=float(w.get("lambda_normie", 0.75)),
        series_gate=float(g["series_gate"]),
        mega_gate=float(g["mega_gate"]),
        binge_gate=float(g["binge_gate"]),
        span_gate=float(g["span_gate"]),
    )
    cohorts = pick_cohorts(con, top_frac=float(w.get("top_frac", 0.06)))
    n_focus = int(cohorts["n_focus"])

    # Equal-size deep elite
    con.execute(
        f"""
        CREATE OR REPLACE TABLE jury_deep_capped AS
        SELECT user_id, curator_pct_weight AS w
        FROM ex.user_curator_deep_weight
        ORDER BY curator_pct_weight DESC
        LIMIT {n_focus}
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_focus AS
        SELECT user_id, 1.0::DOUBLE AS w
        FROM cohort_focus_top
        """
    )
    # Full deep for overlap stats
    n_deep_all = con.execute(
        "SELECT count(*) FROM ex.user_curator_deep_weight"
    ).fetchone()[0]
    n_deep_cap = con.execute("SELECT count(*) FROM jury_deep_capped").fetchone()[0]
    n_f = con.execute("SELECT count(*) FROM jury_focus").fetchone()[0]

    overlap_all = con.execute(
        """
        SELECT count(*) FROM jury_focus f
        JOIN ex.user_curator_deep_weight d USING (user_id)
        """
    ).fetchone()[0]
    overlap_cap = con.execute(
        """
        SELECT count(*) FROM jury_focus f
        JOIN jury_deep_capped d USING (user_id)
        """
    ).fetchone()[0]

    # Affinity of deep-capped vs focus (are deep users "focus-like"?)
    aff = con.execute(
        """
        SELECT
            avg(CASE WHEN f.user_id IS NOT NULL THEN a.classic_affinity END),
            avg(CASE WHEN d.user_id IS NOT NULL THEN a.classic_affinity END),
            avg(CASE WHEN d.user_id IS NOT NULL THEN a.series_share_5 END),
            avg(CASE WHEN f.user_id IS NOT NULL THEN a.series_share_5 END)
        FROM user_affinity a
        LEFT JOIN jury_focus f USING (user_id)
        LEFT JOIN jury_deep_capped d USING (user_id)
        WHERE f.user_id IS NOT NULL OR d.user_id IS NOT NULL
        """
    ).fetchone()

    meta = {
        "n_focus": n_f,
        "n_deep_all": int(n_deep_all),
        "n_deep_capped": int(n_deep_cap),
        "overlap_focus_deep_all": int(overlap_all),
        "overlap_focus_deep_capped": int(overlap_cap),
        "jaccard_focus_deep_capped": float(overlap_cap)
        / max(n_f + n_deep_cap - overlap_cap, 1),
        "pct_focus_in_deep_all": float(overlap_all) / max(n_f, 1),
        "pct_deep_capped_in_focus": float(overlap_cap) / max(n_deep_cap, 1),
        "mean_affinity_focus": float(aff[0]) if aff[0] is not None else None,
        "mean_affinity_deep_capped": float(aff[1]) if aff[1] is not None else None,
        "mean_series_deep_capped": float(aff[2]) if aff[2] is not None else None,
        "mean_series_focus": float(aff[3]) if aff[3] is not None else None,
        "cohorts": cohorts,
    }
    print(
        f"  focus={n_f:,} deep_all={n_deep_all:,} deep_capped={n_deep_cap:,}\n"
        f"  overlap focus∩deep_all={overlap_all:,} ({100*overlap_all/max(n_f,1):.1f}% of focus)\n"
        f"  overlap focus∩deep_capped={overlap_cap:,} "
        f"(Jaccard={meta['jaccard_focus_deep_capped']:.3f})",
        flush=True,
    )
    return meta


def common_five_star_books(con, jury_table: str, *, weighted: bool, limit: int = COMMON_TOP):
    """Most commonly 5★'d mid-pop books in a jury."""
    w_expr = "j.w" if weighted else "1.0"
    rows = con.execute(
        f"""
        WITH hits AS (
            SELECT
                e.work_id,
                sum({w_expr})::DOUBLE AS w_hits,
                count(*)::BIGINT AS n_hits,
                count(DISTINCT e.user_id)::BIGINT AS n_users
            FROM ex.all_rating_events e
            JOIN {jury_table} j USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE e.rating = 5
              AND wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
            GROUP BY e.work_id
        )
        SELECT
            h.work_id,
            s.title,
            s.author,
            h.n_users,
            h.w_hits,
            h.n_users::DOUBLE / (SELECT count(*) FROM {jury_table}) AS exposure
        FROM hits h
        JOIN ex.work_scores s USING (work_id)
        ORDER BY {"h.w_hits" if weighted else "h.n_users"} DESC, h.n_users DESC
        LIMIT {limit}
        """
    ).fetchall()
    out = []
    for i, r in enumerate(rows, 1):
        out.append(
            {
                "rank": i,
                "work_id": str(r[0]),
                "title": r[1],
                "author": r[2],
                "n_users": int(r[3]),
                "w_hits": float(r[4]),
                "exposure": float(r[5]),
            }
        )
    return out


def jaccard_work_lists(a: list[dict], b: list[dict], k: int = 25) -> float:
    sa = {x["work_id"] for x in a[:k]}
    sb = {x["work_id"] for x in b[:k]}
    return len(sa & sb) / max(len(sa | sb), 1)


def build_pairs_for_jury(con, jury_table: str, pair_table: str) -> int:
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {pair_table} AS
        WITH rated AS (
            SELECT e.user_id, e.work_id, e.rating, j.w
            FROM ex.all_rating_events e
            JOIN {jury_table} j USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
        ),
        highs AS (
            SELECT
                user_id, work_id, w,
                row_number() OVER (
                    PARTITION BY user_id
                    ORDER BY hash(user_id || '-' || work_id || '-h{SEED}')
                ) AS rn
            FROM rated WHERE rating = 5
        ),
        lows AS (
            SELECT
                user_id, work_id, w,
                row_number() OVER (
                    PARTITION BY user_id
                    ORDER BY hash(user_id || '-' || work_id || '-l{SEED}')
                ) AS rn
            FROM rated WHERE rating <= {LOW_MAX}
        )
        SELECT
            h.user_id,
            h.work_id AS winner,
            l.work_id AS loser,
            h.w AS w
        FROM highs h
        JOIN lows l USING (user_id)
        WHERE h.rn <= {MAX_HIGHS} AND l.rn <= {MAX_LOWS}
        """
    )
    return int(con.execute(f"SELECT count(*) FROM {pair_table}").fetchone()[0])


def rank_within_jury_pairwise(
    con, pair_table: str, *, weighted: bool, min_appear: int = MIN_APPEAR, k: float = SHRINK_K
) -> list[dict]:
    w_expr = "w" if weighted else "1.0"
    sql = f"""
        WITH wins AS (
            SELECT winner AS work_id, sum({w_expr})::DOUBLE AS wins, count(*)::BIGINT AS n_win_edges
            FROM {pair_table} GROUP BY 1
        ),
        losses AS (
            SELECT loser AS work_id, sum({w_expr})::DOUBLE AS losses, count(*)::BIGINT AS n_loss_edges
            FROM {pair_table} GROUP BY 1
        ),
        agg AS (
            SELECT
                coalesce(w.work_id, l.work_id) AS work_id,
                coalesce(w.wins, 0) AS wins,
                coalesce(l.losses, 0) AS losses,
                (coalesce(w.n_win_edges, 0) + coalesce(l.n_loss_edges, 0)) AS n_edges
            FROM wins w
            FULL OUTER JOIN losses l USING (work_id)
        )
        SELECT
            work_id,
            (
                (n_edges::DOUBLE / (n_edges + {k}))
                * (wins / nullif(wins + losses, 0))
            )::DOUBLE AS score,
            n_edges::DOUBLE AS n_c,
            0.0::DOUBLE AS n_a,
            n_edges::DOUBLE AS n_eff
        FROM agg
        WHERE n_edges >= {min_appear}
    """
    return rank_scored(con, sql)


def exposure_map(con, jury_table: str) -> dict[str, float]:
    n = con.execute(f"SELECT count(*) FROM {jury_table}").fetchone()[0]
    rows = con.execute(
        f"""
        SELECT e.work_id, count(DISTINCT e.user_id)::DOUBLE / {n}
        FROM ex.all_rating_events e
        JOIN {jury_table} j USING (user_id)
        WHERE e.rating = 5
        GROUP BY e.work_id
        """
    ).fetchall()
    return {str(w): float(x) for w, x in rows}


def annotate(rows: list[dict], expo: dict[str, float]) -> list[dict]:
    out = []
    for r in rows:
        d = dict(r)
        d["exposure_5"] = expo.get(r["work_id"])
        out.append(d)
    return out


def main() -> None:
    t_all = time.time()
    con = _con()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    print("Setup…", flush=True)
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    label_cohorts(con)
    w = load_weights()
    print(f"  weights: {w.get('source', WEIGHTS_CAREFUL.name)}", flush=True)

    print("\n=== juries + overlap ===", flush=True)
    meta = setup_juries(con, w)
    adj = author_disjoint_sets(con)

    print("\n=== most common 5★ books (equal-size juries) ===", flush=True)
    common_focus = common_five_star_books(con, "jury_focus", weighted=False)
    common_deep_eq = common_five_star_books(con, "jury_deep_capped", weighted=False)
    common_deep_w = common_five_star_books(con, "jury_deep_capped", weighted=True)
    j_fe = jaccard_work_lists(common_focus, common_deep_eq)
    j_fw = jaccard_work_lists(common_focus, common_deep_w)
    print(f"  Jaccard top{COMMON_TOP} focus vs deep-equal: {j_fe:.3f}", flush=True)
    print(f"  Jaccard top{COMMON_TOP} focus vs deep-weighted: {j_fw:.3f}", flush=True)

    print("\n=== within-jury pairwise ===", flush=True)
    n_pf = build_pairs_for_jury(con, "jury_focus", "pairs_jury_focus")
    n_pd = build_pairs_for_jury(con, "jury_deep_capped", "pairs_jury_deep")
    print(f"  pairs focus={n_pf:,} deep_capped={n_pd:,}", flush=True)

    expo_f = exposure_map(con, "jury_focus")
    expo_d = exposure_map(con, "jury_deep_capped")

    methods = {}

    def record(name: str, rows: list[dict], expo: dict[str, float]) -> None:
        rows = annotate(rows, expo)
        methods[name] = {
            "probe": probe_metrics(rows, ev, sticky),
            "fill": filler_eval(rows, con),
            "heldout_author_disjoint": heldout_recall(rows, adj["test_works"]),
            "top15": [
                {
                    **{k: r[k] for k in ("rank", "title", "author", "score", "n_c")},
                    "exposure_5": r.get("exposure_5"),
                }
                for r in rows[:15]
            ],
            "top50_ids": [r["work_id"] for r in rows[:50]],
        }
        p = methods[name]["probe"]
        h = methods[name]["heldout_author_disjoint"]
        print(
            f"  {name}: pos50={p['pos50']} anti50={p['anti50']} fill50={p['filler50']} "
            f"sticky50={p['sticky50']} heldout@200={h['recall@200']:.3f} "
            f"heldout@50={h.get('recall@50', 0):.3f}",
            flush=True,
        )

    record("pairwise_focus_equal", rank_within_jury_pairwise(con, "pairs_jury_focus", weighted=False), expo_f)
    record("pairwise_deep_capped_equal", rank_within_jury_pairwise(con, "pairs_jury_deep", weighted=False), expo_d)
    record("pairwise_deep_capped_weighted", rank_within_jury_pairwise(con, "pairs_jury_deep", weighted=True), expo_d)

    # Pairwise list overlaps
    def jac50(a: str, b: str) -> float:
        sa, sb = set(methods[a]["top50_ids"]), set(methods[b]["top50_ids"])
        return len(sa & sb) / max(len(sa | sb), 1)

    pair_overlap = {
        "focus_vs_deep_equal": jac50("pairwise_focus_equal", "pairwise_deep_capped_equal"),
        "focus_vs_deep_weighted": jac50("pairwise_focus_equal", "pairwise_deep_capped_weighted"),
        "deep_equal_vs_weighted": jac50("pairwise_deep_capped_equal", "pairwise_deep_capped_weighted"),
    }
    print(
        f"  pairwise top50 Jaccard focus↔deep_eq={pair_overlap['focus_vs_deep_equal']:.3f} "
        f"focus↔deep_w={pair_overlap['focus_vs_deep_weighted']:.3f}",
        flush=True,
    )

    results = {
        "meta": meta,
        "common_books": {
            "focus": common_focus,
            "deep_capped_equal": common_deep_eq,
            "deep_capped_weighted": common_deep_w,
            "jaccard_focus_deep_equal": j_fe,
            "jaccard_focus_deep_weighted": j_fw,
        },
        "pairwise_overlap_top50": pair_overlap,
        "methods": {k: {kk: vv for kk, vv in v.items() if kk != "top50_ids"} for k, v in methods.items()},
    }
    # keep ids in json lightly
    for k, v in methods.items():
        results["methods"][k]["top50_ids"] = v["top50_ids"]

    OUT_JSON.write_text(json.dumps(results, indent=2, default=float) + "\n")

    def fmt_common(rows: list[dict]) -> list[str]:
        return [
            f"- {r['rank']}. {r['title']} — {r['author']} "
            f"(users={r['n_users']}, exposure={r['exposure']:.1%})"
            for r in rows[:15]
        ]

    def fmt_pair(name: str) -> list[str]:
        lines = []
        for r in methods[name]["top15"]:
            ex = r.get("exposure_5")
            ex_s = f"{ex:.1%}" if ex is not None else "?"
            lines.append(
                f"- {r['rank']}. {r['title']} — {r['author']} "
                f"(pair_n={r.get('n_c')}, exposure_5={ex_s})"
            )
        return lines

    lines = [
        "# Jury diagnosis: focus vs deep curators",
        "",
        "Question: is the messy pairwise list about **who we listen to**, or **how we order books**?",
        "",
        "## Overlap",
        "",
        f"- Behavioral focus (top affinity slice): **{meta['n_focus']:,}** users",
        f"- Deep curators (all): **{meta['n_deep_all']:,}**",
        f"- Deep capped to same size: **{meta['n_deep_capped']:,}** (highest curator weights)",
        f"- Focus ∩ deep(all): **{meta['overlap_focus_deep_all']:,}** "
        f"({100*meta['pct_focus_in_deep_all']:.1f}% of focus)",
        f"- Focus ∩ deep(capped): **{meta['overlap_focus_deep_capped']:,}** "
        f"(Jaccard **{meta['jaccard_focus_deep_capped']:.3f}**)",
        f"- Mean classic_affinity: focus={meta['mean_affinity_focus']:.2f}, "
        f"deep_capped={meta['mean_affinity_deep_capped']:.2f}",
        f"- Mean series_share: focus={meta['mean_series_focus']:.3f}, "
        f"deep_capped={meta['mean_series_deep_capped']:.3f}",
        "",
        "## Most common 5★ books (same jury size)",
        "",
        f"Top-{COMMON_TOP} Jaccard focus vs deep-equal: **{j_fe:.3f}**; "
        f"vs deep-weighted: **{j_fw:.3f}**",
        "",
        "### Focus jury",
        "",
        *fmt_common(common_focus),
        "",
        "### Deep capped (equal count)",
        "",
        *fmt_common(common_deep_eq),
        "",
        "### Deep capped (weight-summed 5★s)",
        "",
        *fmt_common(common_deep_w),
        "",
        "## Within-jury pairwise (no anti contrast)",
        "",
        "| method | pos50 | anti50 | filler50 | sticky50 | heldout@50 | heldout@200 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in (
        "pairwise_focus_equal",
        "pairwise_deep_capped_equal",
        "pairwise_deep_capped_weighted",
    ):
        p = methods[name]["probe"]
        h = methods[name]["heldout_author_disjoint"]
        lines.append(
            f"| {name} | {p['pos50']} | {p['anti50']} | {p['filler50']} | "
            f"{p['sticky50']} | {h['recall@50']:.3f} | {h['recall@200']:.3f} |"
        )
    lines += [
        "",
        f"Pairwise top50 Jaccard focus↔deep_eq=**{pair_overlap['focus_vs_deep_equal']:.3f}**, "
        f"focus↔deep_w=**{pair_overlap['focus_vs_deep_weighted']:.3f}**",
        "",
        "### Pairwise — focus equal",
        "",
        *fmt_pair("pairwise_focus_equal"),
        "",
        "### Pairwise — deep capped equal",
        "",
        *fmt_pair("pairwise_deep_capped_equal"),
        "",
        "### Pairwise — deep capped weighted",
        "",
        *fmt_pair("pairwise_deep_capped_weighted"),
        "",
        "## How to read this",
        "",
        "- **Low overlap + different common books** → we have been listening to a different crowd than deep curators.",
        "- **Deep pairwise looks good / focus pairwise messy** → jury selection is the main issue.",
        "- **Both pairwise lists look alike (good or bad)** → ordering method (or shared data limits) dominates.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)


if __name__ == "__main__":
    main()

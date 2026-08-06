#!/usr/bin/env python3
"""Hard/soft jury and hard/conservative-fuzzy community hierarchical audit."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy.stats import spearmanr

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo
from curators_explorer.scripts.research_hierarchical_read_selection import (
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
    combine,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ASSIGNMENTS = DATA_DIR / "jury_fuzzy_community_assignments.parquet"
CANDIDATES = DATA_DIR / "overnight_uncertainty_full.json"
POINT = DATA_DIR / "hierarchical_read_selection.json"
OUT_JSON = DATA_DIR / "hierarchical_membership_audit.json"
OUT_REPORT = DATA_DIR / "HIERARCHICAL_MEMBERSHIP_AUDIT_REPORT.md"


def empty_part(label, k, n_works):
    return {
        "label": label, "k": k,
        "wins": np.zeros((n_works, k), dtype=np.float64),
        "losses": np.zeros((n_works, k), dtype=np.float64),
    }


def fill_part(rows, label, k, n_works):
    part = empty_part(label, k, n_works)
    for work_idx, community, wins, losses in rows:
        part["wins"][int(work_idx), int(community)] = float(wins or 0.0)
        part["losses"][int(work_idx), int(community)] = float(losses or 0.0)
    return part


def aggregate_hard(con, label, k, n_works, user_weight):
    rows = con.execute(
        f"""
        SELECT work_idx, {label} AS community,
               sum(({user_weight}) * CASE WHEN rating=5 AND n_high>0
                   THEN n_side/n_high ELSE 0 END) AS wins,
               sum(({user_weight}) * CASE WHEN rating BETWEEN 1 AND 3 AND n_low>0
                   THEN n_side/n_low ELSE 0 END) AS losses
        FROM candidate_state
        GROUP BY work_idx, community
        """
    ).fetchall()
    return fill_part(rows, label, k, n_works)


def aggregate_fuzzy(con, label, k, n_works, user_weight):
    rows = con.execute(
        f"""
        WITH expanded AS (
            SELECT work_idx, rating, n_high, n_low, n_side,
                   {label}_a AS community, ({user_weight}) * {label}_wa AS weight
            FROM candidate_state
            UNION ALL
            SELECT work_idx, rating, n_high, n_low, n_side,
                   {label}_b AS community, ({user_weight}) * {label}_wb AS weight
            FROM candidate_state
        )
        SELECT work_idx, community,
               sum(weight * CASE WHEN rating=5 AND n_high>0
                   THEN n_side/n_high ELSE 0 END) AS wins,
               sum(weight * CASE WHEN rating BETWEEN 1 AND 3 AND n_low>0
                   THEN n_side/n_low ELSE 0 END) AS losses
        FROM expanded
        GROUP BY work_idx, community
        """
    ).fetchall()
    return fill_part(rows, label, k, n_works)


def metric(parts):
    return combine(
        parts, prior_strength=8.0, book_prior_strength=50.0,
        book_evidence_cap=math.inf, min_mass=10.0, evidence_z=1.0,
        gamma=1.0, all_low=False,
    )


def summarize(label, candidate, fit, baseline):
    ranking = fit["ranking"].tolist()
    base_ranking = baseline["ranking"].tolist()
    common = fit["estimable"] & baseline["estimable"]
    common_idx = np.flatnonzero(common)
    catalog_idx = np.flatnonzero(fit["estimable"])
    rank_map = {int(i): rank + 1 for rank, i in enumerate(ranking)}
    return {
        "label": label,
        "rankable": int(fit["estimable"].sum()),
        "jaccard50": jaccard(base_ranking, ranking, 50),
        "jaccard200": jaccard(base_ranking, ranking, 200),
        "rbo": rbo(base_ranking, ranking),
        "common_score_spearman": float(
            spearmanr(baseline["score"][common_idx], fit["score"][common_idx]).statistic
        ),
        "score_catalog_spearman": float(
            spearmanr(
                np.log1p([candidate[i]["catalog_n"] for i in catalog_idx]),
                fit["score"][catalog_idx],
            ).statistic
        ),
        "median_top200_u": float(
            100 * np.median(fit["uncertainty"][ranking[:200]])
        ),
        "top50": [
            {
                "rank": rank, "work_id": candidate[i]["work_id"],
                "title": candidate[i]["title"], "author": candidate[i]["author"],
                "score": float(100 * fit["score"][i]),
                "u": float(100 * fit["uncertainty"][i]),
                "baseline_rank": None,
            }
            for rank, i in enumerate(ranking[:50], start=1)
        ],
        "rank_by_work_id": {
            candidate[i]["work_id"]: rank for i, rank in rank_map.items()
        },
    }


def main():
    t0 = time.time()
    candidate_payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidate = sorted(candidate_payload["books"], key=lambda row: int(row["work_idx"]))
    point = json.loads(POINT.read_text(encoding="utf-8"))
    point_by_id = {row["work_id"]: row for row in point["books"]}
    n_works = len(candidate)
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("CREATE TEMP TABLE candidates(work_idx INTEGER, work_id VARCHAR)")
    con.executemany(
        "INSERT INTO candidates VALUES (?, ?)",
        [(i, row["work_id"]) for i, row in enumerate(candidate)],
    )
    con.execute(
        f"CREATE TEMP TABLE assignments AS SELECT * FROM read_parquet('{ASSIGNMENTS}')"
    )
    con.execute(
        f"""
        CREATE TEMP TABLE user_balance AS
        SELECT o.user_id,
               count(*) FILTER (WHERE o.rating=5)::DOUBLE AS n_high,
               count(*) FILTER (WHERE o.rating BETWEEN 1 AND 3)::DOUBLE AS n_low,
               least(count(*) FILTER (WHERE o.rating=5),
                     count(*) FILTER (WHERE o.rating BETWEEN 1 AND 3), 12)::DOUBLE AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN assignments a USING (user_id)
        JOIN ex.work_stats s USING (work_id)
        WHERE o.rating>0 AND s.n BETWEEN 100 AND {MAX_CATALOG_N}
        GROUP BY o.user_id
        """
    )
    fuzzy_columns = ", ".join(
        f"a.{label}_a, a.{label}_wa, a.{label}_b, a.{label}_wb"
        for label, _k in PARTITIONS
    )
    hard_columns = ", ".join(f"a.{label}" for label, _k in PARTITIONS)
    # The fuzzy export intentionally stores only fuzzy columns. Hard labels are joined from
    # the previously validated hard-assignment artifact.
    hard_path = DATA_DIR / "jury_community_assignments.parquet"
    con.execute(
        f"""
        CREATE TEMP TABLE candidate_state AS
        SELECT c.work_idx, o.rating, a.jury_q, a.hard_jury,
               {fuzzy_columns}, {', '.join(f'h.{label}' for label, _k in PARTITIONS)},
               coalesce(b.n_high,0) AS n_high,
               coalesce(b.n_low,0) AS n_low, coalesce(b.n_side,0) AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN candidates c USING (work_id)
        JOIN assignments a USING (user_id)
        JOIN read_parquet('{hard_path}') h USING (user_id)
        LEFT JOIN user_balance b USING (user_id)
        WHERE o.rating=5 OR o.rating BETWEEN 1 AND 3
        """
    )
    variants = (
        ("soft jury / hard communities", "jury_q", False),
        ("hard jury / hard communities", "CASE WHEN hard_jury THEN 1.0 ELSE 0.0 END", False),
        ("soft jury / fuzzy90 communities", "jury_q", True),
        ("hard jury / fuzzy90 communities", "CASE WHEN hard_jury THEN 1.0 ELSE 0.0 END", True),
    )
    fits = {}
    for variant_label, weight, fuzzy in variants:
        print(f"Aggregating {variant_label}…", flush=True)
        parts = []
        for label, k in PARTITIONS:
            aggregator = aggregate_fuzzy if fuzzy else aggregate_hard
            parts.append(aggregator(con, label, k, n_works, weight))
        fits[variant_label] = metric(parts)
    con.close()
    baseline = fits[variants[0][0]]
    stored = np.asarray([point_by_id[row["work_id"]]["score"] for row in candidate])
    reproduction_error = float(np.max(np.abs(100 * baseline["score"] - stored)))
    if reproduction_error > 1e-3:
        raise RuntimeError(f"soft/hard point reproduction failed: {reproduction_error}")
    summaries = [summarize(label, candidate, fits[label], baseline) for label, *_ in variants]
    baseline_rank = {
        candidate[i]["work_id"]: rank + 1
        for rank, i in enumerate(baseline["ranking"])
    }
    for summary in summaries:
        for row in summary["top50"]:
            row["baseline_rank"] = baseline_rank.get(row["work_id"])
    focus_ids = [candidate[i]["work_id"] for i in baseline["ranking"][:20]]
    focus = []
    for work_id in focus_ids:
        source = point_by_id[work_id]
        focus.append(
            {
                "work_id": work_id, "title": source["title"], "author": source["author"],
                "soft_hard_rank": baseline_rank[work_id],
                **{
                    summary["label"]: summary["rank_by_work_id"].get(work_id)
                    for summary in summaries[1:]
                },
            }
        )
    membership_trajectory = []
    for i in baseline["ranking"]:
        work_id = candidate[i]["work_id"]
        membership_trajectory.append(
            {
                "work_id": work_id,
                **{
                    summary["label"]: summary["rank_by_work_id"].get(work_id)
                    for summary in summaries
                },
            }
        )
    for summary in summaries:
        del summary["rank_by_work_id"]
    result = {
        "meta": {
            "purpose": "hierarchical hard/soft jury and conservative fuzzy-community audit",
            "runtime_seconds": time.time() - t0, "candidate_books": n_works,
            "point_reproduction_max_abs_error": reproduction_error,
        },
        "variants": summaries,
        "baseline_top20_trajectory": focus,
        "membership_trajectory": membership_trajectory,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hierarchical jury/community membership audit", "", "## Result", "",
        "The corrected hierarchical estimator is crossed with equal-weight hard versus "
        "bootstrap-probability soft juries and hard versus conservative mean-max-0.90 "
        "top-two community memberships. Every user's fuzzy memberships sum to one.", "",
        "| variant | rankable | J@50 | J@200 | RBO | score rho | pop rho | med top200 u |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['label']} | {row['rankable']} | {row['jaccard50']:.3f} | "
            f"{row['jaccard200']:.3f} | {row['rbo']:.3f} | "
            f"{row['common_score_spearman']:.3f} | {row['score_catalog_spearman']:.3f} | "
            f"{row['median_top200_u']:.2f} |"
        )
    lines += [
        "", "## Baseline-head rank trajectories", "",
        "| baseline | book | hard jury | soft fuzzy90 | hard fuzzy90 |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in focus:
        lines.append(
            f"| {row['soft_hard_rank']} | {row['title']} — {row['author']} | "
            f"{row['hard jury / hard communities']} | "
            f"{row['soft jury / fuzzy90 communities']} | "
            f"{row['hard jury / fuzzy90 communities']} |"
        )
    lines += [
        "", "Fuzzy-community movement is an audit, not automatic improvement: smoothing "
        "mechanically reduces apparent community disagreement. The hard-jury path tests the "
        "existing jury boundary but does not refit that boundary.", "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_REPORT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

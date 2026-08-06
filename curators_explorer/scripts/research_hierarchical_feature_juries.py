#!/usr/bin/env python3
"""Propagate plausible and adversarial jury-feature definitions hierarchically."""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy.stats import spearmanr

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo
from curators_explorer.scripts.research_hierarchical_membership_audit import (
    aggregate_fuzzy,
    aggregate_hard,
    metric,
)
from curators_explorer.scripts.research_hierarchical_read_selection import (
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ASSIGNMENTS = DATA_DIR / "jury_feature_variant_assignments.parquet"
CANDIDATES = DATA_DIR / "overnight_uncertainty_full.json"
POINT = DATA_DIR / "hierarchical_read_selection.json"
MEMBERSHIP = DATA_DIR / "hierarchical_membership_audit.json"
BOUNDARY = DATA_DIR / "hierarchical_candidate_boundary.json"
OUT_JSON = DATA_DIR / "hierarchical_feature_juries.json"
OUT_REPORT = DATA_DIR / "HIERARCHICAL_FEATURE_JURIES_REPORT.md"

JURIES = (
    ("rich_behavior_global", "plausible baseline"),
    ("rich_no_direct_activity", "plausible shelf-size ablation"),
    ("generic_behavior_only", "adversarial estimand ablation"),
)


def summarize(label, role, fit, baseline, candidate, soft_ranking):
    ranking = fit["ranking"].tolist()
    base = baseline["ranking"].tolist()
    common = np.flatnonzero(fit["estimable"] & baseline["estimable"])
    rank_map = {candidate[i]["work_id"]: rank+1 for rank, i in enumerate(ranking)}
    return {
        "label": label, "role": role,
        "rankable": int(fit["estimable"].sum()),
        "jaccard50_vs_baseline_hard": jaccard(base, ranking, 50),
        "jaccard200_vs_baseline_hard": jaccard(base, ranking, 200),
        "rbo_vs_baseline_hard": rbo(base, ranking),
        "jaccard50_vs_soft_point": jaccard(soft_ranking, ranking, 50),
        "jaccard200_vs_soft_point": jaccard(soft_ranking, ranking, 200),
        "score_spearman_vs_baseline_hard": float(
            spearmanr(fit["score"][common], baseline["score"][common]).statistic
        ),
        "score_catalog_spearman": float(
            spearmanr(
                np.log1p([candidate[i]["catalog_n"] for i in fit["ranking"]]),
                fit["score"][fit["ranking"]],
            ).statistic
        ),
        "median_top200_u": float(
            100*np.median(fit["uncertainty"][fit["ranking"][:200]])
        ),
        "rank_by_work_id": rank_map,
        "top100": [
            {
                "rank": rank, "work_id": candidate[i]["work_id"],
                "title": candidate[i]["title"], "author": candidate[i]["author"],
                "score": float(100*fit["score"][i]),
                "u": float(100*fit["uncertainty"][i]),
                "baseline_hard_rank": None,
            }
            for rank, i in enumerate(ranking[:100], start=1)
        ],
    }


def main():
    t0 = time.time()
    candidate_payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidate = sorted(candidate_payload["books"], key=lambda row: int(row["work_idx"]))
    point = json.loads(POINT.read_text(encoding="utf-8"))
    point_ranking = [
        row["work_id"] for row in point["books"] if row["hierarchical_rank"] is not None
    ]
    expanded = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    trajectory_ids = list(point_ranking[:200])
    trajectory_ids.extend(
        row["work_id"] for row in expanded["expanded_mass10_top200"]
        if row["work_id"] not in set(trajectory_ids)
    )
    idx_by_id = {row["work_id"]: i for i, row in enumerate(candidate)}
    soft_ranking = [idx_by_id[work_id] for work_id in point_ranking]
    membership = json.loads(MEMBERSHIP.read_text(encoding="utf-8"))
    expected_hard = next(
        row for row in membership["variants"]
        if row["label"] == "hard jury / hard communities"
    )

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
    jury_columns = ", ".join(f"a.{label}" for label, _role in JURIES)
    hard_columns = ", ".join(f"a.{label}" for label, _k in PARTITIONS)
    fuzzy_columns = ", ".join(
        f"a.{label}_a, a.{label}_wa, a.{label}_b, a.{label}_wb"
        for label, _k in PARTITIONS
    )
    con.execute(
        f"""
        CREATE TEMP TABLE candidate_state AS
        SELECT c.work_idx, o.rating, {jury_columns}, {hard_columns}, {fuzzy_columns},
               coalesce(b.n_high,0) AS n_high,
               coalesce(b.n_low,0) AS n_low, coalesce(b.n_side,0) AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN candidates c USING (work_id)
        JOIN assignments a USING (user_id)
        LEFT JOIN user_balance b USING (user_id)
        WHERE o.rating=5 OR o.rating BETWEEN 1 AND 3
        """
    )
    fits = {}
    for jury, role in JURIES:
        for fuzzy in (False, True):
            community = "fuzzy90" if fuzzy else "hard"
            variant = f"{jury} / {community}"
            print(f"Aggregating {variant}…", flush=True)
            parts = []
            weight = f"CASE WHEN {jury} THEN 1.0 ELSE 0.0 END"
            for label, k in PARTITIONS:
                fn = aggregate_fuzzy if fuzzy else aggregate_hard
                parts.append(fn(con, label, k, len(candidate), weight))
            fits[variant] = metric(parts)
    con.close()

    baseline_label = "rich_behavior_global / hard"
    baseline = fits[baseline_label]
    baseline_ids = [candidate[i]["work_id"] for i in baseline["ranking"][:50]]
    observed_ids = [row["work_id"] for row in expected_hard["top50"]]
    reproduction_j50 = jaccard(
        [idx_by_id[x] for x in observed_ids],
        baseline["ranking"].tolist(), 50,
    )
    if reproduction_j50 != 1.0:
        raise RuntimeError("feature export failed to reproduce baseline hard head")
    summaries = []
    for jury, role in JURIES:
        for community in ("hard", "fuzzy90"):
            label = f"{jury} / {community}"
            summaries.append(
                summarize(label, role, fits[label], baseline, candidate, soft_ranking)
            )
    baseline_rank = {
        candidate[i]["work_id"]: rank+1 for rank, i in enumerate(baseline["ranking"])
    }
    for summary in summaries:
        for row in summary["top100"]:
            row["baseline_hard_rank"] = baseline_rank.get(row["work_id"])
    trajectory = []
    for work_id in trajectory_ids:
        trajectory.append(
            {
                "work_id": work_id,
                "title": candidate[idx_by_id[work_id]]["title"],
                "author": candidate[idx_by_id[work_id]]["author"],
                "soft_point_rank": point_ranking.index(work_id)+1,
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
            "purpose": "hierarchical propagation of alternative jury feature families",
            "runtime_seconds": time.time()-t0,
            "candidate_books": len(candidate),
            "baseline_head_reproduction_jaccard50": reproduction_j50,
            "trajectory_books": len(trajectory_ids),
            "trajectory_scope": "union of old and expanded-prior mass-10 top 200",
        },
        "variants": summaries,
        "soft_point_top200_trajectory": trajectory,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hierarchical jury-feature-family audit", "", "## Result", "",
        "The baseline rich-behavior jury, the plausible no-direct-activity jury, and the "
        "generic-only adversarial ablation are propagated through hard and conservative "
        "fuzzy90 communities. Communities remain frozen to the baseline 20,000-user space.",
        "", "| jury / communities | role | rankable | J@50 hard | J@200 hard | RBO hard | J@50 soft | J@200 soft | score rho | pop rho | med u |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['label']} | {row['role']} | {row['rankable']} | "
            f"{row['jaccard50_vs_baseline_hard']:.3f} | {row['jaccard200_vs_baseline_hard']:.3f} | "
            f"{row['rbo_vs_baseline_hard']:.3f} | {row['jaccard50_vs_soft_point']:.3f} | "
            f"{row['jaccard200_vs_soft_point']:.3f} | {row['score_spearman_vs_baseline_hard']:.3f} | "
            f"{row['score_catalog_spearman']:.3f} | {row['median_top200_u']:.2f} |"
        )
    lines += ["", "## Soft-point head trajectories", "",
              "| # | book | baseline hard | no-activity hard | no-activity fuzzy | generic hard |",
              "|---:|---|---:|---:|---:|---:|"]
    for row in trajectory[:50]:
        lines.append(
            f"| {row['soft_point_rank']} | {row['title']} — {row['author']} | "
            f"{row['rich_behavior_global / hard']} | "
            f"{row['rich_no_direct_activity / hard']} | "
            f"{row['rich_no_direct_activity / fuzzy90']} | "
            f"{row['generic_behavior_only / hard']} |"
        )
    lines += ["", "The no-activity path is a plausible constituency perturbation. The "
              "generic-only path removes the feature family that defines the literary "
              "estimand and is therefore a falsification diagnostic, not an equal-vote veto.", ""]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_REPORT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

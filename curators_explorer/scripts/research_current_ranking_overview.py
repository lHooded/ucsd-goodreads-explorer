#!/usr/bin/env python3
"""Join the current soft-jury ranking to evidence, uncertainty, and trajectories."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SOFT_MEMBERSHIP = DATA_DIR / "soft_membership_full.json"
SOFT_BOOTSTRAP = DATA_DIR / "soft_jury_bootstrap_full.json"
JURY_BOOTSTRAP = DATA_DIR / "overnight_jury_bootstrap_full.json"
TRAJECTORIES = DATA_DIR / "temporal_trajectories.json"
EVENTS = DATA_DIR / "temporal_rated_events_full.parquet"
WEIGHTS = DATA_DIR / "soft_jury_weights.parquet"
OUT_JSON = DATA_DIR / "current_best_ranking_overview.json"
OUT_REPORT = DATA_DIR / "CURRENT_BEST_RANKING_OVERVIEW.md"


def chosen_variant(payload, label):
    return next(row for row in payload["variants"] if row["label"] == label)


def main():
    membership = json.loads(SOFT_MEMBERSHIP.read_text(encoding="utf-8"))
    soft_boot = json.loads(SOFT_BOOTSTRAP.read_text(encoding="utf-8"))
    jury_boot = json.loads(JURY_BOOTSTRAP.read_text(encoding="utf-8"))
    temporal = json.loads(TRAJECTORIES.read_text(encoding="utf-8"))
    point = chosen_variant(membership, "soft jury q / hard communities")
    ranking = chosen_variant(soft_boot, "soft jury q")
    point_by_id = {row["work_id"]: row for row in point["top100"]}
    jury_by_id = {row["work_id"]: row for row in jury_boot["books"]}
    trajectory_by_id = {
        row["work_id"]: row for row in temporal["central_trajectories"]
    }
    declines = {
        row["work_id"]: row
        for row in temporal["all_direction_consistent_declines"]
    }
    rises = {
        row["work_id"]: row
        for row in temporal["all_direction_consistent_rises"]
    }

    con = duckdb.connect()
    con.execute("PRAGMA threads=8")
    con.execute("CREATE TEMP TABLE ranked(work_id VARCHAR PRIMARY KEY)")
    con.executemany(
        "INSERT INTO ranked VALUES (?)",
        [(row["work_id"],) for row in ranking["books"]],
    )
    evidence_rows = con.execute(
        f"""
        WITH user_work AS (
            SELECT e.user_id, e.work_id, max(e.rating)::INTEGER AS rating
            FROM read_parquet('{EVENTS}') e JOIN ranked r USING (work_id)
            GROUP BY e.user_id, e.work_id
        )
        SELECT u.work_id,
               count(*)::BIGINT AS full_archive_raters,
               count(*) FILTER (WHERE w.jury_q>0)::BIGINT AS soft_jury_raters,
               count(*) FILTER (
                   WHERE w.jury_q>0 AND (u.rating=5 OR u.rating<=3)
               )::BIGINT AS soft_pair_readers,
               sum(w.jury_q) FILTER (
                   WHERE w.jury_q>0 AND (u.rating=5 OR u.rating<=3)
               ) AS soft_pair_mass,
               pow(sum(w.jury_q) FILTER (
                   WHERE w.jury_q>0 AND (u.rating=5 OR u.rating<=3)
               ), 2) / nullif(sum(w.jury_q*w.jury_q) FILTER (
                   WHERE w.jury_q>0 AND (u.rating=5 OR u.rating<=3)
               ), 0) AS soft_pair_kish,
               count(*) FILTER (WHERE w.hard_jury)::BIGINT AS hard_jury_raters
        FROM user_work u
        LEFT JOIN read_parquet('{WEIGHTS}') w USING (user_id)
        GROUP BY u.work_id
        """
    ).fetchall()
    evidence = {
        row[0]: {
            "full_archive_raters": int(row[1]),
            "soft_jury_raters": int(row[2]),
            "soft_pair_readers": int(row[3]),
            "soft_pair_mass": None if row[4] is None else float(row[4]),
            "soft_pair_kish": None if row[5] is None else float(row[5]),
            "hard_jury_raters": int(row[6]),
        }
        for row in evidence_rows
    }
    con.close()

    books = []
    for row in ranking["books"]:
        work_id = row["work_id"]
        point_row = point_by_id.get(work_id, {})
        jury_row = jury_by_id.get(work_id, {})
        trajectory = trajectory_by_id.get(work_id)
        if work_id in declines:
            trajectory_status = "decline_consistent"
            path_row = declines[work_id]
        elif work_id in rises:
            trajectory_status = "rise_consistent"
            path_row = rises[work_id]
        elif trajectory is not None:
            trajectory_status = "clock_sensitive"
            path_row = None
        else:
            trajectory_status = "insufficient"
            path_row = None
        books.append(
            {
                **row,
                **evidence.get(work_id, {}),
                "community_coverage": point_row.get("coverage"),
                "analytic_u": point_row.get("uncertainty"),
                "jury_u80_hard_refit": jury_row.get("jury_boot_u80"),
                "jury_eligibility_hard_refit": jury_row.get(
                    "jury_boot_eligible_rate"
                ),
                "trajectory_status": trajectory_status,
                "early_p5": None if trajectory is None else trajectory["early_p5"],
                "late_p5": None if trajectory is None else trajectory["late_p5"],
                "delta_p5": None if trajectory is None else trajectory["delta_p5"],
                "delta_mean_jury_q": None
                if trajectory is None else trajectory["delta_mean_q"],
                "trajectory_path_min": None
                if path_row is None else path_row["path_delta_min"],
                "trajectory_path_max": None
                if path_row is None else path_row["path_delta_max"],
            }
        )
    result = {
        "method": {
            "jury": "bootstrap inclusion probability q; total mass 4929",
            "communities": "hard assignments across nine k/seed partitions",
            "book_score": "exact expected-inclusion 5-star versus <=3-star, equal-community lower-tail score",
            "n_rankable": ranking["n_rankable"],
            "reader_bootstrap_replicates": soft_boot["meta"]["replicates"],
            "mean_reader_bootstrap_jaccard200": ranking[
                "bootstrap_jaccard200_mean"
            ],
            "median_top200_reader_u80": ranking["top200_median_u80"],
            "score_catalog_spearman": point["score_catalog_spearman"],
        },
        "books": books,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Current best distributed-canon ranking",
        "",
        "## Method snapshot",
        "",
        "This is the current preferred point ranking: exact expected-inclusion pair votes, "
        "continuous bootstrap jury weights totaling 4,929 juror equivalents, and the existing "
        "hard community assignments across nine perturbed partitions. The hard jury and "
        "conservative fuzzy-community path remain sensitivity audits.",
        "",
        f"- Rankable books: **{result['method']['n_rankable']}**.",
        f"- Reader-bootstrap mean Jaccard@200: "
        f"**{result['method']['mean_reader_bootstrap_jaccard200']:.3f}**.",
        f"- Median top-200 reader `u80`: "
        f"**{result['method']['median_top200_reader_u80']:.2f} points**.",
        f"- Score versus catalog readership rho: "
        f"**{result['method']['score_catalog_spearman']:.3f}**; popularity is not rewarded.",
        "",
        "`uR` is the conditional 10th–90th reader-bootstrap half-width. `uJ` is the analogous "
        "hard-jury-refit width and is shown as a separate diagnostic. Eligibility must be read "
        "alongside both. Reader counts below are descriptive raw raters, not the capped "
        "effective mass used by the score.",
        "",
        "## Top 30: score, uncertainty, and evidence",
        "",
        "| # | book | score | uR | uJ | eligible | top200 | full raters | jury pair readers | Kish pair n | coverage |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in books[:30]:
        uj = "—" if row["jury_u80_hard_refit"] is None else f"{row['jury_u80_hard_refit']:.1f}"
        cov = "—" if row["community_coverage"] is None else f"{100*row['community_coverage']:.0f}%"
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | {row['score']:.1f} | "
            f"{row['u80']:.1f} | {uj} | {100*row['eligible_rate']:.0f}% | "
            f"{100*row['top200_rate']:.0f}% | {row['full_archive_raters']:,} | "
            f"{row['soft_pair_readers']:,} | {row['soft_pair_kish']:.0f} | {cov} |"
        )
    lines += [
        "",
        "## Top 30: temporal trajectories",
        "",
        "Primary trajectory excludes each user's first account week and largest import day. "
        "A consistent arrow means the sign agrees across all four Goodreads activity paths; "
        "`mixed` means the direction changes with the clock/import rule.",
        "",
        "| # | book | early→late p5 | change | Δ jury-q | trajectory |",
        "|---:|---|---:|---:|---:|---|",
    ]
    status_label = {
        "decline_consistent": "↓ consistent",
        "rise_consistent": "↑ consistent",
        "clock_sensitive": "mixed",
        "insufficient": "insufficient",
    }
    for row in books[:30]:
        if row["delta_p5"] is None:
            path = delta = dq = "—"
        else:
            path = f"{row['early_p5']:.3f}→{row['late_p5']:.3f}"
            delta = f"{row['delta_p5']:+.3f}"
            dq = f"{row['delta_mean_jury_q']:+.3f}"
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | {path} | "
            f"{delta} | {dq} | {status_label[row['trajectory_status']]} |"
        )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Expand the hierarchical candidate universe below the pair-mass-10 boundary."""

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
    ASSIGNMENTS,
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
    aggregate_partition,
    combine,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
POINT = DATA_DIR / "hierarchical_read_selection.json"
OUT_JSON = DATA_DIR / "hierarchical_candidate_boundary.json"
OUT_REPORT = DATA_DIR / "HIERARCHICAL_CANDIDATE_BOUNDARY_REPORT.md"
MIN_EXPANDED_MASS = 2.0


def main():
    t0 = time.time()
    prior_point = json.loads(POINT.read_text(encoding="utf-8"))
    old_ranking = [
        row["work_id"] for row in prior_point["books"]
        if row["hierarchical_rank"] is not None
    ]
    old_top = set(old_ranking[:200])
    old_universe = {row["work_id"] for row in prior_point["books"]}

    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute(
        f"CREATE TEMP TABLE assignments AS SELECT * FROM read_parquet('{ASSIGNMENTS}') WHERE jury_q>0"
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
    con.execute(
        f"""
        CREATE TEMP TABLE eligible AS
        SELECT s.work_id, s.n AS catalog_n, ws.title, ws.author
        FROM ex.work_stats s
        JOIN ex.work_scores ws USING (work_id)
        LEFT JOIN ex.work_flags f USING (work_id)
        WHERE s.n BETWEEN 100 AND {MAX_CATALOG_N}
          AND NOT coalesce(f.is_excluded,FALSE)
          AND NOT coalesce(f.is_nonfiction,FALSE)
          AND NOT coalesce(f.is_comic,FALSE)
          AND NOT coalesce(f.is_picture_book,FALSE)
          AND NOT coalesce(f.is_derivative,FALSE)
          AND NOT coalesce(f.is_duplicate,FALSE)
          AND NOT coalesce(f.is_collection,FALSE)
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE work_mass AS
        SELECT o.work_id,
               sum(a.jury_q * CASE
                   WHEN o.rating=5 AND b.n_high>0 THEN b.n_side/b.n_high
                   WHEN o.rating BETWEEN 1 AND 3 AND b.n_low>0 THEN b.n_side/b.n_low
                   ELSE 0 END) AS pair_mass
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN assignments a USING (user_id)
        JOIN user_balance b USING (user_id)
        JOIN eligible e USING (work_id)
        WHERE o.rating=5 OR o.rating BETWEEN 1 AND 3
        GROUP BY o.work_id
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE candidates AS
        SELECT (row_number() OVER (ORDER BY e.work_id)-1)::INTEGER AS work_idx,
               e.*, m.pair_mass
        FROM eligible e JOIN work_mass m USING (work_id)
        WHERE m.pair_mass >= {MIN_EXPANDED_MASS}
        """
    )
    works_rows = con.execute(
        "SELECT work_idx, work_id, title, author, catalog_n, pair_mass FROM candidates ORDER BY work_idx"
    ).fetchall()
    works = [
        {
            "work_idx": int(row[0]), "work_id": str(row[1]),
            "title": row[2], "author": row[3], "catalog_n": int(row[4]),
            "sql_pair_mass": float(row[5]),
        }
        for row in works_rows
    ]
    labels = ", ".join(f"a.{label}" for label, _k in PARTITIONS)
    con.execute(
        f"""
        CREATE TEMP TABLE candidate_state AS
        SELECT c.work_idx, o.user_id, o.is_read, o.rating, o.is_reviewed,
               a.jury_q, {labels},
               coalesce(b.n_high,0) AS n_high,
               coalesce(b.n_low,0) AS n_low, coalesce(b.n_side,0) AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN candidates c USING (work_id)
        JOIN assignments a USING (user_id)
        LEFT JOIN user_balance b USING (user_id)
        """
    )
    partitions = []
    for label, k in PARTITIONS:
        print(f"Aggregating expanded {label}…", flush=True)
        partitions.append(aggregate_partition(con, label, k, len(works)))
    state_rows = int(con.execute("SELECT count(*) FROM candidate_state").fetchone()[0])
    con.close()

    expanded = combine(
        partitions, prior_strength=8.0, book_prior_strength=50.0,
        book_evidence_cap=math.inf, min_mass=MIN_EXPANDED_MASS,
        evidence_z=1.0, gamma=1.0, all_low=False,
    )
    ranking2 = expanded["ranking"].tolist()
    ranking10 = [i for i in ranking2 if expanded["pair_mass"][i] >= 10.0]
    rank2 = {int(i): rank+1 for rank, i in enumerate(ranking2)}
    rank10 = {int(i): rank+1 for rank, i in enumerate(ranking10)}
    id10 = [works[i]["work_id"] for i in ranking10]
    old_idx = {row["work_id"]: row for row in prior_point["books"]}
    rows = []
    for i in ranking2:
        work = works[i]
        old = old_idx.get(work["work_id"])
        rows.append(
            {
                **work, "expanded_rank_mass2": rank2[i],
                "expanded_rank_mass10": rank10.get(i),
                "old_rank": None if old is None else old["hierarchical_rank"],
                "score": float(100*expanded["score"][i]),
                "u": float(100*expanded["uncertainty"][i]),
                "pair_mass": float(expanded["pair_mass"][i]),
                "coverage": float(expanded["coverage"][i]),
                "outside_old_universe": work["work_id"] not in old_universe,
            }
        )
    below10_top200 = [row for row in rows[:200] if row["pair_mass"] < 10]
    mass10_top200 = sorted(
        (row for row in rows if row["expanded_rank_mass10"] is not None),
        key=lambda row: row["expanded_rank_mass10"],
    )[:200]
    new_top200 = [row for row in rows[:200] if row["work_id"] not in old_top]
    boundary_watch = [
        row for row in rows if row["pair_mass"] < 10 and row["expanded_rank_mass2"] <= 500
    ]
    counts = {
        "mass_ge_2": len(rows),
        "mass_ge_5": sum(row["pair_mass"] >= 5 for row in rows),
        "mass_ge_10": len(ranking10),
        "mass_ge_20": sum(row["pair_mass"] >= 20 for row in rows),
        "below10_in_expanded_top200": len(below10_top200),
        "outside_old_in_expanded_top200": sum(
            row["outside_old_universe"] for row in rows[:200]
        ),
    }
    result = {
        "meta": {
            "purpose": "expanded candidate-boundary audit with priors learned on mass>=2 universe",
            "runtime_seconds": time.time()-t0, "candidate_state_rows": state_rows,
            "predictive_heterogeneity_floor": expanded["heterogeneity_floor"],
            "score_catalog_spearman_mass10": float(spearmanr(
                np.log1p([works[i]["catalog_n"] for i in ranking10]),
                expanded["score"][ranking10],
            ).statistic),
        },
        "counts": counts,
        "comparison": {
            "mass10_vs_old_jaccard50": jaccard(old_ranking, id10, 50),
            "mass10_vs_old_jaccard200": jaccard(old_ranking, id10, 200),
            "mass10_vs_old_rbo": rbo(old_ranking, id10),
        },
        "expanded_top200": rows[:200],
        "expanded_mass10_top200": mass10_top200,
        "expanded_books": rows,
        "old_top200_trajectory": [row for row in rows if row["work_id"] in old_top],
        "new_top200": new_top200,
        "below10_top200": below10_top200,
        "boundary_watch_top500": boundary_watch,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hierarchical candidate-boundary audit", "", "## Result", "",
        "The eligible universe is expanded from 1,146 near-evidence candidates to every "
        "eligible fiction work with soft expected pair mass at least 2. Empirical global and "
        "community priors are relearned on this expanded population; publication ranking can "
        "still impose mass 10 afterward.", "",
        f"- Expanded candidates: **{counts['mass_ge_2']:,}** at mass>=2; "
        f"**{counts['mass_ge_5']:,}** at mass>=5; **{counts['mass_ge_10']:,}** at mass>=10.",
        f"- Expanded-prior mass-10 versus old ranking: J@50 **{result['comparison']['mass10_vs_old_jaccard50']:.3f}**, "
        f"J@200 **{result['comparison']['mass10_vs_old_jaccard200']:.3f}**, RBO **{result['comparison']['mass10_vs_old_rbo']:.3f}**.",
        f"- Sub-10 books in expanded top 200: **{counts['below10_in_expanded_top200']}**; "
        f"books outside the old universe in that top 200: **{counts['outside_old_in_expanded_top200']}**.",
        "", "## Expanded-prior top 50", "",
        "| # | book | score ±u | mass10 rank | old rank | pair mass | coverage | catalog n |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows[:50]:
        mass10 = "—" if row["expanded_rank_mass10"] is None else row["expanded_rank_mass10"]
        old = "—" if row["old_rank"] is None else row["old_rank"]
        lines.append(
            f"| {row['expanded_rank_mass2']} | {row['title']} — {row['author']} | "
            f"{row['score']:.1f} ±{row['u']:.1f} | {mass10} | {old} | "
            f"{row['pair_mass']:.1f} | {100*row['coverage']:.0f}% | {row['catalog_n']:,} |"
        )
    lines += ["", "## Sub-10 boundary watch within expanded top 500", "",
              "| expanded # | book | score ±u | pair mass | coverage | catalog n |",
              "|---:|---|---:|---:|---:|---:|"]
    for row in boundary_watch[:60]:
        lines.append(
            f"| {row['expanded_rank_mass2']} | {row['title']} — {row['author']} | "
            f"{row['score']:.1f} ±{row['u']:.1f} | {row['pair_mass']:.1f} | "
            f"{100*row['coverage']:.0f}% | {row['catalog_n']:,} |"
        )
    lines += ["", "Changing the prior population is a model specification, not merely "
              "adding rows. A large common-book shift would mean the old candidate-conditioned "
              "prior must be retired even if no low-mass book enters the head.", ""]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_REPORT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

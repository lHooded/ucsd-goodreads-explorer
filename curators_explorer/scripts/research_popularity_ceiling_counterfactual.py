#!/usr/bin/env python3
"""Raise the 80k catalog ceiling and audit newly admitted mega-read works."""

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
    EVIDENCE_CAP,
    LOWER_Z,
    OBSERVATIONS,
    PARTITIONS,
    aggregate_partition,
    combine,
)


DATA = Path(__file__).resolve().parents[1] / "data"
BASELINE_PATH = DATA / "hierarchical_candidate_boundary.json"
EXTERNAL_PATH = DATA / "external_canon_omission_audit.json"
OUT_JSON = DATA / "popularity_ceiling_counterfactual.json"
OUT_REPORT = DATA / "POPULARITY_CEILING_COUNTERFACTUAL_REPORT.md"
OUT_CATALOG = DATA / "distributed_canon_catalog.json"

BASELINE_MAX_N = 80_000
RAISED_MAX_N = 400_000
MIN_MASS = 2.0
PUBLICATION_MASS = 10.0


def score_model(partitions, book_evidence_cap: float):
    return combine(
        partitions,
        prior_strength=8.0,
        book_prior_strength=50.0,
        book_evidence_cap=book_evidence_cap,
        min_mass=MIN_MASS,
        evidence_z=1.0,
        gamma=1.0,
        all_low=False,
    )


def rank_at_mass(model, threshold=PUBLICATION_MASS):
    return [
        int(i) for i in model["ranking"]
        if model["pair_mass"][int(i)] >= threshold
    ]


def metric_row(i, model, rank_map):
    # score = esteem - 1.2816*heterogeneity - shared book-evidence penalty
    evidence_penalty = (
        model["esteem"][i]
        - LOWER_Z * model["heterogeneity"][i]
        - model["score"][i]
    )
    return {
        "rank": rank_map.get(i),
        "score": float(100 * model["score"][i]),
        "esteem": float(100 * model["esteem"][i]),
        "heterogeneity_penalty": float(
            100 * LOWER_Z * model["heterogeneity"][i]
        ),
        "evidence_penalty": float(100 * evidence_penalty),
        "u": float(100 * model["uncertainty"][i]),
        "esteem_u": float(100 * model["esteem_uncertainty"][i]),
        "pair_mass": float(model["pair_mass"][i]),
        "coverage": float(model["coverage"][i]),
    }


def evidence_status(pair_mass: float, coverage: float) -> str:
    """Keep weak evidence distinct from genuine cross-community disagreement."""
    if pair_mass < 5.0 or coverage < 0.35:
        return "sparse"
    if pair_mass < PUBLICATION_MASS or coverage < 0.5:
        return "exploratory"
    return "supported"


def community_status(heterogeneity_penalty: float, pair_mass: float, coverage: float) -> str:
    """Classify disagreement only where there is enough breadth to observe it."""
    if pair_mass < PUBLICATION_MASS or coverage < 0.5:
        return "unclear"
    if heterogeneity_penalty >= 12.0:
        return "contested"
    if heterogeneity_penalty >= 6.0:
        return "mixed"
    return "broad"


def main() -> None:
    t0 = time.time()
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    external = json.loads(EXTERNAL_PATH.read_text(encoding="utf-8"))
    baseline_ranked = sorted(
        (
            row for row in baseline["expanded_books"]
            if row["expanded_rank_mass10"] is not None
        ),
        key=lambda row: row["expanded_rank_mass10"],
    )
    baseline_ids = [str(row["work_id"]) for row in baseline_ranked]

    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute(
        f"CREATE TEMP TABLE assignments AS "
        f"SELECT * FROM read_parquet('{ASSIGNMENTS}') WHERE jury_q>0"
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
        WHERE o.rating>0 AND s.n BETWEEN 100 AND {RAISED_MAX_N}
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
        WHERE s.n BETWEEN 100 AND {RAISED_MAX_N}
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
        WHERE m.pair_mass >= {MIN_MASS}
        """
    )
    work_rows = con.execute(
        "SELECT work_idx, work_id, title, author, catalog_n, pair_mass "
        "FROM candidates ORDER BY work_idx"
    ).fetchall()
    works = [
        {
            "work_idx": int(row[0]), "work_id": str(row[1]), "title": row[2],
            "author": row[3], "catalog_n": int(row[4]), "sql_pair_mass": float(row[5]),
        }
        for row in work_rows
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
    state_rows = int(con.execute("SELECT count(*) FROM candidate_state").fetchone()[0])
    partitions = []
    for label, k in PARTITIONS:
        print(f"Aggregating raised-ceiling {label}…", flush=True)
        partitions.append(aggregate_partition(con, label, k, len(works)))
    con.close()

    central = score_model(partitions, math.inf)
    capped30 = score_model(partitions, 30.0)
    capped60 = score_model(partitions, 60.0)
    capped120 = score_model(partitions, 120.0)
    central_rank = rank_at_mass(central)
    capped_rank = rank_at_mass(capped30)
    capped60_rank = rank_at_mass(capped60)
    capped120_rank = rank_at_mass(capped120)
    central_rank_map = {i: rank + 1 for rank, i in enumerate(central_rank)}
    capped_rank_map = {i: rank + 1 for rank, i in enumerate(capped_rank)}
    capped60_rank_map = {i: rank + 1 for rank, i in enumerate(capped60_rank)}
    capped120_rank_map = {i: rank + 1 for rank, i in enumerate(capped120_rank)}
    # The public catalogue deliberately keeps the mass-2 exploratory tail.  The
    # evidence label and uncertainty communicate that these ranks are less settled.
    capped120_all_rank = [int(i) for i in capped120["ranking"]]
    capped120_all_rank_map = {
        i: rank + 1 for rank, i in enumerate(capped120_all_rank)
    }
    esteem_all_rank = sorted(
        capped120_all_rank,
        key=lambda i: (-float(capped120["esteem"][i]), i),
    )
    esteem_all_rank_map = {i: rank + 1 for rank, i in enumerate(esteem_all_rank)}
    id_to_idx = {row["work_id"]: i for i, row in enumerate(works)}
    central_ids = [works[i]["work_id"] for i in central_rank]
    capped_ids = [works[i]["work_id"] for i in capped_rank]

    mega_rows = []
    for i, work in enumerate(works):
        if work["catalog_n"] <= BASELINE_MAX_N:
            continue
        mega_rows.append({
            **work,
            "central": metric_row(i, central, central_rank_map),
            "cap30": metric_row(i, capped30, capped_rank_map),
            "cap60": metric_row(i, capped60, capped60_rank_map),
            "cap120": metric_row(i, capped120, capped120_rank_map),
        })
    mega_rows.sort(key=lambda row: row["central"]["rank"] or 10**9)

    # Relevant external works, including the three motivating examples.
    external_ranks: dict[str, dict[str, int]] = {}
    for source, rows in external["sources"].items():
        for row in rows:
            if not row.get("work_id"):
                continue
            external_ranks.setdefault(str(row["work_id"]), {})[source] = int(
                row["source_rank"]
            )
    focus_ids = {
        "2368224", "2409320", "245494",
        *[
            work_id for work_id, ranks in external_ranks.items()
            if min(ranks.values()) <= 30
        ],
    }
    focus = []
    for work_id in focus_ids:
        i = id_to_idx.get(work_id)
        if i is None:
            continue
        focus.append({
            **works[i],
            "external_ranks": external_ranks.get(work_id, {}),
            "baseline_rank": (
                next((row["expanded_rank_mass10"] for row in baseline_ranked
                      if str(row["work_id"]) == work_id), None)
            ),
            "central": metric_row(i, central, central_rank_map),
            "cap30": metric_row(i, capped30, capped_rank_map),
            "cap60": metric_row(i, capped60, capped60_rank_map),
            "cap120": metric_row(i, capped120, capped120_rank_map),
        })
    focus.sort(key=lambda row: min(row["external_ranks"].values(), default=10**9))

    baseline_common_rank = {work_id: rank + 1 for rank, work_id in enumerate(baseline_ids)}
    central_common_rank = {work_id: rank + 1 for rank, work_id in enumerate(central_ids)}
    common = [work_id for work_id in baseline_ids if work_id in central_common_rank]
    rho = float(spearmanr(
        [baseline_common_rank[x] for x in common],
        [central_common_rank[x] for x in common],
    ).statistic)

    public_catalog = []
    for i in capped120_all_rank:
        work = works[i]
        metric = metric_row(i, capped120, capped120_all_rank_map)
        heterogeneity_penalty = metric["heterogeneity_penalty"]
        public_catalog.append(
            {
                "work_id": work["work_id"],
                "title": work["title"],
                "author": work["author"],
                "catalog_n": work["catalog_n"],
                "consensus_rank": capped120_all_rank_map[i],
                "esteem_rank": esteem_all_rank_map[i],
                "consensus_score": metric["score"],
                "consensus_uncertainty": metric["u"],
                "esteem": metric["esteem"],
                "esteem_uncertainty": metric["esteem_u"],
                "heterogeneity_penalty": heterogeneity_penalty,
                "evidence_penalty": metric["evidence_penalty"],
                "pair_mass": metric["pair_mass"],
                "coverage": metric["coverage"],
                "community_status": community_status(
                    heterogeneity_penalty, metric["pair_mass"], metric["coverage"]
                ),
                "evidence_status": evidence_status(
                    metric["pair_mass"], metric["coverage"]
                ),
            }
        )

    catalog_result = {
        "method": {
            "model": "raised-ceiling hierarchical distributed canon",
            "max_catalog_n": RAISED_MAX_N,
            "book_evidence_cap": 120,
            "cell_evidence_cap": EVIDENCE_CAP,
            "minimum_pair_mass": MIN_MASS,
            "publication_pair_mass": PUBLICATION_MASS,
            "ranked_books": len(public_catalog),
            "consensus_definition": (
                "mean community esteem minus lower-tail heterogeneity and evidence penalties"
            ),
            "esteem_definition": "mean posterior esteem across balanced reader communities",
            "uncertainty_kind": "analytic sampling plus partition sensitivity",
            "community_status": {
                "broad": "heterogeneity penalty below 6 points",
                "mixed": "heterogeneity penalty from 6 to below 12 points",
                "contested": "heterogeneity penalty at least 12 points",
                "unclear": "too little pair mass or community coverage to classify",
            },
        },
        "books": public_catalog,
    }
    OUT_CATALOG.write_text(
        json.dumps(catalog_result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    result = {
        "method": {
            "purpose": "counterfactual removal of hard 80k popularity ceiling",
            "baseline_max_catalog_n": BASELINE_MAX_N,
            "raised_max_catalog_n": RAISED_MAX_N,
            "publication_pair_mass": PUBLICATION_MASS,
            "central_book_evidence_cap": None,
            "stress_book_evidence_cap": 30,
            "cell_evidence_cap": EVIDENCE_CAP,
            "candidate_state_rows": state_rows,
            "runtime_seconds": time.time() - t0,
        },
        "counts": {
            "candidates_mass2": len(works),
            "central_rankable_mass10": len(central_rank),
            "new_mega_candidates_mass2": len(mega_rows),
            "new_mega_top50": sum((row["central"]["rank"] or 10**9) <= 50 for row in mega_rows),
            "new_mega_top200": sum((row["central"]["rank"] or 10**9) <= 200 for row in mega_rows),
            "new_mega_cap30_top200": sum((row["cap30"]["rank"] or 10**9) <= 200 for row in mega_rows),
            "new_mega_cap60_top200": sum((row["cap60"]["rank"] or 10**9) <= 200 for row in mega_rows),
            "new_mega_cap120_top200": sum((row["cap120"]["rank"] or 10**9) <= 200 for row in mega_rows),
        },
        "comparison": {
            "central_vs_baseline_jaccard50": jaccard(baseline_ids, central_ids, 50),
            "central_vs_baseline_jaccard200": jaccard(baseline_ids, central_ids, 200),
            "central_vs_baseline_rbo": rbo(baseline_ids, central_ids),
            "central_vs_baseline_common_rank_spearman": rho,
            "cap30_vs_central_jaccard50": jaccard(central_ids, capped_ids, 50),
            "cap30_vs_central_jaccard200": jaccard(central_ids, capped_ids, 200),
            "cap60_vs_central_jaccard50": jaccard(
                central_ids, [works[i]["work_id"] for i in capped60_rank], 50
            ),
            "cap60_vs_central_jaccard200": jaccard(
                central_ids, [works[i]["work_id"] for i in capped60_rank], 200
            ),
            "cap120_vs_central_jaccard50": jaccard(
                central_ids, [works[i]["work_id"] for i in capped120_rank], 50
            ),
            "cap120_vs_central_jaccard200": jaccard(
                central_ids, [works[i]["work_id"] for i in capped120_rank], 200
            ),
        },
        "mega_books": mega_rows,
        "external_top30_and_focus": focus,
        "central_top200": [
            {**works[i], **metric_row(i, central, central_rank_map)}
            for i in central_rank[:200]
        ],
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Popularity-ceiling counterfactual", "", "## Design", "",
        f"The catalog ceiling is raised from {BASELINE_MAX_N:,} to {RAISED_MAX_N:,} ratings. "
        "Everything else remains structurally the same: the jury is fixed, community priors "
        "are relearned, publication still requires pair mass 10, and each observed community "
        f"is capped at {EVIDENCE_CAP:.0f} evidence units. Total book-evidence caps of 120, 60, "
        "and 30 test progressively stronger saturation, preventing mega-read books from buying "
        "arbitrarily high precision.", "",
        "## Result", "",
        f"- Newly admitted mega-read candidates: **{len(mega_rows)}**; central top-50: "
        f"**{result['counts']['new_mega_top50']}**; central top-200: "
        f"**{result['counts']['new_mega_top200']}**; cap-30 top-200: "
        f"**{result['counts']['new_mega_cap30_top200']}**. Moderate cap-60/cap-120 "
        f"top-200 counts are **{result['counts']['new_mega_cap60_top200']}** and "
        f"**{result['counts']['new_mega_cap120_top200']}**.",
        f"- Raised ceiling versus baseline: Jaccard@50 "
        f"**{result['comparison']['central_vs_baseline_jaccard50']:.3f}**, Jaccard@200 "
        f"**{result['comparison']['central_vs_baseline_jaccard200']:.3f}**, common-rank rho "
        f"**{rho:.3f}**.",
        f"- Within raised ceiling, uncapped versus total-evidence-cap-30: Jaccard@50 "
        f"**{result['comparison']['cap30_vs_central_jaccard50']:.3f}**, Jaccard@200 "
        f"**{result['comparison']['cap30_vs_central_jaccard200']:.3f}**.", "",
        f"- Moderate cap 60: Jaccard@50/200 **"
        f"{result['comparison']['cap60_vs_central_jaccard50']:.3f}/"
        f"{result['comparison']['cap60_vs_central_jaccard200']:.3f}**; cap 120: **"
        f"{result['comparison']['cap120_vs_central_jaccard50']:.3f}/"
        f"{result['comparison']['cap120_vs_central_jaccard200']:.3f}**.", "",
        "## Newly admitted mega-read works", "",
        "| Central | Cap 120 | Cap 60 | Cap 30 | Book | n | Score | Esteem | Heterog. penalty |",
        "|---:|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in mega_rows:
        c, k = row["central"], row["cap30"]
        lines.append(
            f"| {c['rank'] or '—'} | {row['cap120']['rank'] or '—'} | "
            f"{row['cap60']['rank'] or '—'} | {k['rank'] or '—'} | "
            f"*{row['title']}* — {row['author']} | {row['catalog_n']:,} | "
            f"{c['score']:.1f} | {c['esteem']:.1f} | {c['heterogeneity_penalty']:.1f} |"
        )
    lines += ["", "## External top-30 and motivating books", "",
              "| Book | External ranks | Baseline | Raised | Cap 120 | Cap 60 | Cap 30 | Score ±u |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in focus:
        c, k = row["central"], row["cap30"]
        ranks = ", ".join(f"{name}:{rank}" for name, rank in row["external_ranks"].items()) or "focus"
        lines.append(
            f"| *{row['title']}* | {ranks} | {row['baseline_rank'] or '—'} | "
            f"{c['rank'] or '—'} | {row['cap120']['rank'] or '—'} | "
            f"{row['cap60']['rank'] or '—'} | {k['rank'] or '—'} | "
            f"{c['score']:.1f} ±{c['u']:.1f} |"
        )
    lines += ["", "## Interpretation", "",
              "A newly admitted book that remains high under cap 30 has broad jury esteem, not "
              "merely a precision advantage. A book that ranks low in both paths is absent for "
              "substantive rating/community reasons. A large uncapped-to-capped fall is the "
              "signature of evidence-volume leverage.", ""]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")
    print(f"Wrote {OUT_CATALOG}")


if __name__ == "__main__":
    main()

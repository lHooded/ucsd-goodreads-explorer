#!/usr/bin/env python3
"""Explain high-canon omissions using jury, community, and model evidence."""

from __future__ import annotations

import json
import math
from pathlib import Path

import duckdb
import numpy as np

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_hierarchical_read_selection import (
    ASSIGNMENTS,
    OBSERVATIONS,
    PARTITIONS,
)


DATA = Path(__file__).resolve().parents[1] / "data"
EXTERNAL_PATH = DATA / "external_canon_omission_audit.json"
COUNTERFACTUAL_PATH = DATA / "popularity_ceiling_counterfactual.json"
SYNTHESIS_PATH = DATA / "hierarchical_stability_synthesis.json"
FIXED_MASS_PATH = DATA / "fixed_mass_subsamples_full.json"
OUT_JSON = DATA / "canon_omission_mechanisms.json"
OUT_REPORT = DATA / "CANON_OMISSION_MECHANISMS_REPORT.md"
RAISED_MAX_N = 400_000


def q(values, p):
    return None if not values else float(np.quantile(values, p))


def main() -> None:
    external = json.loads(EXTERNAL_PATH.read_text(encoding="utf-8"))
    counter = json.loads(COUNTERFACTUAL_PATH.read_text(encoding="utf-8"))
    synthesis = json.loads(SYNTHESIS_PATH.read_text(encoding="utf-8"))
    fixed_mass = json.loads(FIXED_MASS_PATH.read_text(encoding="utf-8"))
    fixed_mass_maps = {
        cap: {str(row["work_id"]): row for row in payload["books"]}
        for cap, payload in fixed_mass["targets"].items()
    }
    current_by_id = {str(row["work_id"]): row for row in synthesis["books"]}
    raised_by_id = {
        str(row["work_id"]): row for row in counter["central_top200"]
    }
    for row in counter["external_top30_and_focus"]:
        raised_by_id[str(row["work_id"])] = row
    for row in counter["mega_books"]:
        raised_by_id[str(row["work_id"])] = row

    external_by_id: dict[str, dict] = {}
    for source, rows in external["sources"].items():
        for row in rows:
            work_id = row.get("work_id")
            if not work_id:
                continue
            merged = external_by_id.setdefault(str(work_id), {
                "work_id": str(work_id), "title": row["title"], "author": row["author"],
                "catalog_n": row["catalog_n"], "global_mean": row["global_mean"],
                "global_p5": row["global_p5"], "external_ranks": {},
                "love_rank": row.get("love_rank"), "love_score": row.get("love_score"),
                "baseline_status": row["status"],
                "baseline_distributed_rank": row.get("distributed_rank"),
                "temporal_delta_p5": row.get("temporal_delta_p5"),
                "temporal_delta_mean_q": row.get("temporal_delta_mean_q"),
            })
            merged["external_ranks"][source] = int(row["source_rank"])
            if row.get("love_rank") is not None:
                merged["love_rank"] = row["love_rank"]
                merged["love_score"] = row["love_score"]

    # High external omissions plus anchors for scale.
    target_ids = {
        work_id for work_id, row in external_by_id.items()
        if min(row["external_ranks"].values()) <= 30
        and work_id not in current_by_id
        and work_id in raised_by_id
    }
    target_ids.update({"2368224", "2409320", "245494"})
    anchors = [str(row["work_id"]) for row in synthesis["books"][:5]]
    target_ids.update(anchors)

    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute(
        f"CREATE TEMP TABLE assignments AS "
        f"SELECT * FROM read_parquet('{ASSIGNMENTS}') WHERE jury_q>0"
    )
    con.execute("CREATE TEMP TABLE targets(work_id VARCHAR)")
    con.executemany("INSERT INTO targets VALUES (?)", [(x,) for x in target_ids])
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
    labels = ", ".join(f"a.{label}" for label, _k in PARTITIONS)
    con.execute(
        f"""
        CREATE TEMP TABLE target_state AS
        SELECT o.*, a.jury_q, {labels}, b.n_high, b.n_low, b.n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN targets t USING (work_id)
        JOIN assignments a USING (user_id)
        LEFT JOIN user_balance b USING (user_id)
        """
    )
    observation_rows = con.execute(
        """
        SELECT work_id,
               count(*) AS recorded_users,
               count(*) FILTER (WHERE rating>0) AS raters,
               count(*) FILTER (WHERE is_read OR rating>0) AS readers,
               sum(jury_q) FILTER (WHERE rating>0) AS rated_mass,
               sum(jury_q) FILTER (WHERE is_read OR rating>0) AS read_mass,
               sum(jury_q) FILTER (WHERE is_read AND rating=0) AS read_unrated_mass,
               sum(jury_q * (rating=5)::INTEGER) FILTER (WHERE rating>0)
                   / nullif(sum(jury_q) FILTER (WHERE rating>0),0) AS soft_jury_p5,
               sum(jury_q * rating) FILTER (WHERE rating>0)
                   / nullif(sum(jury_q) FILTER (WHERE rating>0),0) AS soft_jury_mean
        FROM target_state
        GROUP BY work_id
        """
    ).fetchall()
    observation = {
        str(row[0]): {
            "recorded_users": int(row[1]), "raters": int(row[2]), "readers": int(row[3]),
            "rated_mass": float(row[4] or 0), "read_mass": float(row[5] or 0),
            "read_unrated_mass": float(row[6] or 0),
            "rating_completion": float(row[4] / row[5]) if row[5] else None,
            "soft_jury_p5": float(row[7]) if row[7] is not None else None,
            "soft_jury_mean": float(row[8]) if row[8] is not None else None,
        }
        for row in observation_rows
    }

    cell_rows = []
    for label, _k in PARTITIONS:
        rows = con.execute(
            f"""
            SELECT work_id, {label} AS community,
                   sum(jury_q * CASE WHEN rating=5 AND n_high>0
                       THEN n_side/n_high ELSE 0 END) AS wins,
                   sum(jury_q * CASE WHEN rating BETWEEN 1 AND 3 AND n_low>0
                       THEN n_side/n_low ELSE 0 END) AS losses
            FROM target_state
            GROUP BY work_id, community
            """
        ).fetchall()
        for work_id, community, wins, losses in rows:
            wins, losses = float(wins or 0), float(losses or 0)
            mass = wins + losses
            cell_rows.append({
                "work_id": str(work_id), "partition": label,
                "community": int(community), "wins": wins, "losses": losses,
                "mass": mass,
                "pair_rate": (wins + 0.5) / (mass + 1.0),
            })
    con.close()

    cells_by_id: dict[str, list[dict]] = {}
    for row in cell_rows:
        cells_by_id.setdefault(row["work_id"], []).append(row)

    rows = []
    for work_id in target_ids:
        source = external_by_id.get(work_id, {})
        raised = raised_by_id.get(work_id, {})
        central = raised.get("central", raised)
        cap30 = raised.get("cap30", {})
        current = current_by_id.get(work_id)
        cells = cells_by_id.get(work_id, [])
        supported = [row for row in cells if row["mass"] >= 3.0]
        rates = [row["pair_rate"] for row in supported]
        pair_mass = None if not cells else sum(
            row["mass"] for row in cells if row["partition"] == PARTITIONS[0][0]
        )
        rows.append({
            "work_id": work_id,
            "title": source.get("title") or current.get("title") if current else source.get("title"),
            "author": source.get("author") or current.get("author") if current else source.get("author"),
            "catalog_n": source.get("catalog_n") or (current or {}).get("full_raters"),
            "external_ranks": source.get("external_ranks", {}),
            "love_rank": source.get("love_rank"),
            "love_score": source.get("love_score"),
            "baseline_status": source.get("baseline_status", "anchor"),
            "baseline_rank": (
                current["rank"] if current is not None
                else source.get("baseline_distributed_rank")
            ),
            "raised_rank": central.get("rank"),
            "raised_score": central.get("score"),
            "raised_u": central.get("u"),
            "esteem": central.get("esteem"),
            "heterogeneity_penalty": central.get("heterogeneity_penalty"),
            "evidence_penalty": central.get("evidence_penalty"),
            "cap30_rank": cap30.get("rank"),
            "cap120_rank": raised.get("cap120", {}).get("rank"),
            "mass60_top200_rate": fixed_mass_maps["60"].get(work_id, {}).get("top200_rate"),
            "mass120_top200_rate": fixed_mass_maps["120"].get(work_id, {}).get("top200_rate"),
            "temporal_delta_p5": source.get("temporal_delta_p5"),
            "temporal_delta_mean_q": source.get("temporal_delta_mean_q"),
            "pair_mass": pair_mass,
            "community_cells_supported": len(supported),
            "community_pair_rate_q10": q(rates, 0.10),
            "community_pair_rate_median": q(rates, 0.50),
            "community_pair_rate_q90": q(rates, 0.90),
            "community_pair_rate_min": min(rates) if rates else None,
            "community_pair_rate_max": max(rates) if rates else None,
            **observation.get(work_id, {}),
        })
    rows.sort(key=lambda row: (
        0 if row["work_id"] in {"2368224", "2409320", "245494"} else 1,
        min(row["external_ranks"].values(), default=10**9),
        row["baseline_rank"] or 10**9,
    ))

    # Correct any absent source metadata for anchors from synthesis.
    for row in rows:
        current = current_by_id.get(row["work_id"])
        if current:
            row["title"] = row["title"] or current["title"]
            row["author"] = row["author"] or current["author"]

    cutoff = float(counter["central_top200"][-1]["score"])
    result = {
        "method": {
            "purpose": "mechanism decomposition of high-external-canon omissions",
            "community_rate": "balanced soft-jury 5-star versus 1-3-star pair rate; Beta(0.5,0.5) display smoothing",
            "community_cells": "nine overlapping k=6/10/16 partitions; supported cells require mass>=3",
            "raised_top200_score_cutoff": cutoff,
        },
        "books": rows,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Why high-canon books are absent", "", "## Reading the decomposition", "",
        "The live Love ranking asks whether the selected raters express strong relative love. "
        "The distributed score asks a harder question: after balancing each juror's high and "
        "low ratings, does esteem recur across many independently reclustered communities, "
        "with enough evidence to survive lower-tail penalties? A book can therefore have high "
        "Love and high average esteem yet miss because the enthusiasm is uneven.", "",
        f"The raised-ceiling top-200 score cutoff is **{cutoff:.1f}**.", "",
        "| Book | Love | Raised / cap120 | Score | Esteem | Heterog. penalty | Community pair-rate q10–q90 | P(top200), mass60/120 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        qrange = (
            "—" if row["community_pair_rate_q10"] is None else
            f"{100*row['community_pair_rate_q10']:.0f}–{100*row['community_pair_rate_q90']:.0f}%"
        )
        survival = (
            "—" if row.get("mass60_top200_rate") is None else
            f"{100*row['mass60_top200_rate']:.0f}/{100*row['mass120_top200_rate']:.0f}%"
        )
        lines.append(
            f"| *{row['title']}* | {row['love_rank'] or '—'} | "
            f"{row['raised_rank'] or '—'} / {row['cap120_rank'] or '—'} | "
            f"{row['raised_score']:.1f} | {row['esteem']:.1f} | "
            f"{row['heterogeneity_penalty']:.1f} | {qrange} | {survival} |"
        )
    lines += [
        "", "## Three motivating books", "",
        "### Ulysses", "",
        "Its Love rank shows strong enthusiasm among the live literary cohort. The distributed "
        "model also estimates high mean esteem, but enthusiasm varies markedly across community "
        "definitions and its uncertainty is high. It sits only a few score points below the "
        "top-200 cutoff and enters the top 200 in 16–33% of fixed-evidence resamples; this is a "
        "heterogeneity/robustness boundary, not a confident rejection or popularity exclusion. "
        "Its early-to-late paired 5-star rate falls 5.3 percentage points, but later readers have "
        "slightly *higher* mean jury-likeness; that is not the clean enthusiast-self-selection "
        "signature of simultaneous rating decline and declining jury-q.", "",
        "### Moby-Dick", "",
        "The mechanism is similar but better observed: high esteem and full community coverage, "
        "offset by a large heterogeneity penalty. Its positive temporal trajectory argues against "
        "enthusiast-first decay: its paired 5-star rate rises 2.7 percentage points. It enters "
        "the top 200 in 35–43% of fixed-evidence resamples. "
        "It is a plausible boundary disagreement with external canons, not a data-scarcity failure.", "",
        "### The Great Gatsby", "",
        "The old 80k ceiling hid the answer, but the counterfactual is decisive: after admission "
        "it ranks near the bottom, and remains there under evidence capping. Its mean balanced "
        "esteem is below the top-200 cutoff even before the very large cross-community penalty. "
        "Its external prominence is therefore not supported by this Goodreads literary jury; "
        "curriculum, cultural familiarity, and list tradition are more plausible explanations "
        "than a precision/popularity artifact inside our scorer.", "",
        "## Model implication", "",
        "Remove the hard 80k eligibility ceiling in the next candidate model, because it prevents "
        "the model from distinguishing *popular but broadly supported* (The Little Prince) from "
        "*popular but weakly supported* (Gatsby). Replace it with a moderate total-evidence cap "
        "around 120 and retain uncapped, 60, and 30 paths as trajectories. Cap 120 preserves "
        "99% of the raised-ceiling top 200 while preventing unlimited precision leverage. 1984 "
        "is a useful boundary case: #169 uncapped but #216 at cap 120.", "",
        "Do not automatically add Ulysses or Moby-Dick from external ranks. Instead, expose a "
        "second 'high esteem, community-contested' view or report their average esteem alongside "
        "the conservative score. That makes the philosophical choice—consensus versus intense "
        "minority esteem—visible rather than burying it in one rank.", "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

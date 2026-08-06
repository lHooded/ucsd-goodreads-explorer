#!/usr/bin/env python3
"""Joint whole-reader and teacher-jury bootstrap for the expanded-prior model."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy import sparse

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard
from curators_explorer.scripts.research_hierarchical_read_selection import (
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
    combine,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ASSIGNMENTS = DATA_DIR / "jury_feature_variant_assignments.parquet"
JURY_CHECKPOINT = DATA_DIR / "hierarchical_jury_bootstrap_full_checkpoint.npz"
BOUNDARY = DATA_DIR / "hierarchical_candidate_boundary.json"
SEED = 20_260_811


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--reps", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    if args.reps is None:
        args.reps = 40 if args.mode == "quick" else 1_000
    return args


def paths(mode):
    stem = f"hierarchical_joint_bootstrap_{mode}"
    return DATA_DIR / f"{stem}.json", DATA_DIR / f"{stem.upper()}_REPORT.md"


def query_matrix(con, label, event_sql, k, n_users, n_works):
    values = con.execute(
        f"""
        SELECT user_idx, work_idx * {k} + {label} AS cell, {event_sql} AS value
        FROM pair_events
        WHERE {event_sql} > 0
        """
    ).fetchnumpy()
    return sparse.coo_matrix(
        (
            values["value"].astype(np.float32),
            (values["user_idx"].astype(np.int32), values["cell"].astype(np.int64)),
        ),
        shape=(n_users, n_works * k),
    ).tocsr()


def build_blocks():
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    # The feature-variant export preserves the exact broad-user order used by the packed
    # jury masks. Its first 20,000 rows are also byte-for-byte assignment-compatible with
    # jury_community_assignments.parquet (validated when that export is built).
    con.execute(
        f"""
        CREATE TEMP TABLE assignments AS
        SELECT (row_number() OVER ()-1)::INTEGER AS user_idx, user_id, jury_q,
               {', '.join(label for label, _k in PARTITIONS)}
        FROM read_parquet('{ASSIGNMENTS}') WHERE baseline_broad
        """
    )
    n_users = int(con.execute("SELECT count(*) FROM assignments").fetchone()[0])
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
        FROM ex.work_stats s JOIN ex.work_scores ws USING (work_id)
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
    labels = ", ".join(f"a.{label}" for label, _k in PARTITIONS)
    con.execute(
        f"""
        CREATE TEMP TABLE pair_events_raw AS
        SELECT o.work_id, a.user_idx, o.rating, a.jury_q, {labels},
               b.n_high, b.n_low, b.n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN assignments a USING (user_id)
        JOIN user_balance b USING (user_id)
        JOIN eligible e USING (work_id)
        WHERE o.rating=5 OR o.rating BETWEEN 1 AND 3
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE work_mass AS
        SELECT work_id,
               sum(jury_q * CASE WHEN rating=5 AND n_high>0 THEN n_side/n_high
                   WHEN rating BETWEEN 1 AND 3 AND n_low>0 THEN n_side/n_low
                   ELSE 0 END) AS pair_mass
        FROM pair_events_raw GROUP BY work_id
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE candidates AS
        SELECT (row_number() OVER (ORDER BY e.work_id)-1)::INTEGER AS work_idx,
               e.*, m.pair_mass
        FROM eligible e JOIN work_mass m USING (work_id)
        WHERE m.pair_mass>=2
        """
    )
    rows = con.execute(
        "SELECT work_idx,work_id,title,author,catalog_n,pair_mass "
        "FROM candidates ORDER BY work_idx"
    ).fetchall()
    works = [
        {
            "work_idx": int(row[0]), "work_id": str(row[1]),
            "title": row[2], "author": row[3], "catalog_n": int(row[4]),
            "soft_pair_mass": float(row[5]),
        }
        for row in rows
    ]
    con.execute(
        f"""
        CREATE TEMP TABLE pair_events AS
        SELECT c.work_idx, p.user_idx, p.rating, p.jury_q,
               {', '.join(f'p.{label}' for label, _k in PARTITIONS)},
               p.n_high, p.n_low, p.n_side
        FROM pair_events_raw p JOIN candidates c USING (work_id)
        """
    )
    win_sql = "CASE WHEN rating=5 AND n_high>0 THEN n_side/n_high ELSE 0 END"
    loss_sql = "CASE WHEN rating BETWEEN 1 AND 3 AND n_low>0 THEN n_side/n_low ELSE 0 END"
    blocks = []
    for label, k in PARTITIONS:
        print(f"Building expanded joint block {label}...", flush=True)
        blocks.append(
            {
                "label": label, "k": k,
                "positive": query_matrix(con, label, win_sql, k, n_users, len(works)),
                "negative": query_matrix(con, label, loss_sql, k, n_users, len(works)),
            }
        )
    q_rows = con.execute(
        "SELECT user_idx,jury_q FROM assignments ORDER BY user_idx"
    ).fetchall()
    q = np.asarray([float(row[1]) for row in q_rows], dtype=np.float32)
    event_rows = int(con.execute("SELECT count(*) FROM pair_events").fetchone()[0])
    con.close()
    return works, q, blocks, event_rows


def project(weights, blocks, n_works):
    projected = []
    for block in blocks:
        k = block["k"]
        projected.append(
            (
                np.asarray(weights @ block["positive"], dtype=np.float64).reshape(
                    len(weights), n_works, k
                ),
                np.asarray(weights @ block["negative"], dtype=np.float64).reshape(
                    len(weights), n_works, k
                ),
            )
        )
    return projected


def fit(parts):
    return combine(
        parts, prior_strength=8.0, book_prior_strength=50.0,
        book_evidence_cap=math.inf, min_mass=2.0, evidence_z=1.0,
        gamma=1.0, all_low=False,
    )


def published_ranking(metric):
    eligible = metric["pair_mass"] >= 10.0
    ranking = np.flatnonzero(eligible)
    return eligible, ranking[np.argsort(-metric["score"][ranking], kind="stable")]


def point_fit(q, blocks, n_works):
    projected = project(q[None, :], blocks, n_works)
    parts = [
        {
            "label": block["label"], "k": block["k"],
            "wins": values[0][0], "losses": values[1][0],
        }
        for block, values in zip(blocks, projected)
    ]
    return fit(parts)


def run_draws(masks, blocks, n_works, reps, batch_size):
    scores = np.full((reps, n_works), np.nan, dtype=np.float32)
    ranks = np.zeros((reps, n_works), dtype=np.uint16)
    masses = np.zeros((reps, n_works), dtype=np.float32)
    for start in range(0, reps, batch_size):
        count = min(batch_size, reps-start)
        weights = np.empty((count, masks.shape[1]), dtype=np.float32)
        for offset, draw in enumerate(range(start, start+count)):
            reader = np.random.default_rng(SEED+draw).poisson(
                1.0, masks.shape[1]
            ).astype(np.float32)
            weights[offset] = masks[draw % len(masks)] * reader
        projected = project(weights, blocks, n_works)
        for offset in range(count):
            parts = [
                {
                    "label": block["label"], "k": block["k"],
                    "wins": values[0][offset], "losses": values[1][offset],
                }
                for block, values in zip(blocks, projected)
            ]
            metric = fit(parts)
            eligible, ranking = published_ranking(metric)
            scores[start+offset, eligible] = (100*metric["score"][eligible]).astype(
                np.float32
            )
            masses[start+offset] = metric["pair_mass"].astype(np.float32)
            ranks[start+offset, ranking] = np.arange(
                1, len(ranking)+1, dtype=np.uint16
            )
        print(f"  completed {start+count}/{reps}", flush=True)
    return scores, ranks, masses


def write_report(result, path):
    meta, summary = result["meta"], result["summary"]
    lines = [
        "# Expanded-prior joint reader-by-jury bootstrap", "", "## Result", "",
        "Each draw takes one saved teacher-composition jury refit and independently "
        "Poisson-resamples whole Goodreads users within it. Global, book, community, and "
        "predictive-heterogeneity terms are then relearned on the expanded mass-2 prior "
        "population; the publication threshold remains pair mass 10.", "",
        f"- Replicates: **{meta['replicates']:,}** across **{meta['jury_masks']}** saved "
        f"jury refits; expanded works: **{meta['expanded_candidates']:,}**.",
        f"- Mean Jaccard@50/200: **{summary['jaccard50_mean']:.3f} / "
        f"{summary['jaccard200_mean']:.3f}** (10th percentiles "
        f"{summary['jaccard50_q10']:.3f} / {summary['jaccard200_q10']:.3f}).",
        f"- Median point-top-200 joint `u80`: **{summary['median_joint_u80']:.2f}** "
        f"points; median eligibility: **{100*summary['median_eligibility']:.0f}%**; "
        f"median top-200 inclusion: **{100*summary['median_top200_rate']:.0f}%**.",
        f"- Recomputed soft point matches the stored expanded ranking at J@50/200 "
        f"**{meta['point_validation_j50']:.3f}/{meta['point_validation_j200']:.3f}** "
        f"with maximum top-200 score error **{meta['point_validation_max_score_error']:.4f}**.",
        "", "## Expanded-prior point head", "",
        "| # | book | score | analytic u | joint u80 | eligibility | top200 | joint rank q10-q90 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["books"][:50]:
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | {row['score']:.1f} | "
            f"{row['analytic_u']:.1f} | {row['joint_u80']:.1f} | "
            f"{100*row['eligibility_rate']:.0f}% | {100*row['top200_rate']:.0f}% | "
            f"{row['rank_q10']:.0f}-{row['rank_q90']:.0f} |"
        )
    lines += [
        "", "`joint u80` is half the conditional 10th-90th percentile score interval. "
        "Use max(analytic u, joint u80) as the provisional display envelope: the analytic "
        "and bootstrap widths overlap, so quadrature would double count. Feature-family, "
        "Gamma, fixed-mass, and temporal trajectories remain separate systematic paths.", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    out_json, out_report = paths(args.mode)
    t0 = time.time()
    works, q, blocks, event_rows = build_blocks()
    n_works = len(works)
    with np.load(JURY_CHECKPOINT, allow_pickle=False) as saved:
        completed = int(saved["completed"])
        packed = saved["selected_packed"][:completed]
    masks = np.unpackbits(packed, axis=1)[:, :len(q)].astype(np.float32)
    if not np.all(masks.sum(axis=1) == 4_929):
        raise RuntimeError("saved jury masks do not each contain 4,929 users")

    point = point_fit(q, blocks, n_works)
    point_eligible, point_ranking = published_ranking(point)
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    stored = boundary["expanded_mass10_top200"]
    stored_ids = [row["work_id"] for row in stored]
    point_ids = [works[i]["work_id"] for i in point_ranking[:200]]
    stored_scores = {row["work_id"]: row["score"] for row in stored}
    validation_error = max(
        abs(100*point["score"][i]-stored_scores[works[i]["work_id"]])
        for i in point_ranking[:200] if works[i]["work_id"] in stored_scores
    )
    validation_j50 = jaccard(stored_ids, point_ids, 50)
    validation_j200 = jaccard(stored_ids, point_ids, 200)
    if validation_j50 < 1 or validation_j200 < 1 or validation_error > 1e-3:
        raise RuntimeError(
            f"expanded point reproduction failed: J={validation_j50}/{validation_j200}, "
            f"score error={validation_error}"
        )

    scores, ranks, masses = run_draws(
        masks, blocks, n_works, args.reps, args.batch_size
    )
    j50, j200 = [], []
    for draw in ranks:
        order = np.flatnonzero(draw > 0)
        order = order[np.argsort(draw[order], kind="stable")]
        j50.append(jaccard(point_ranking.tolist(), order.tolist(), 50))
        j200.append(jaccard(point_ranking.tolist(), order.tolist(), 200))

    analytic = {row["work_id"]: row["u"] for row in stored}
    books = []
    for rank, i in enumerate(point_ranking[:200], start=1):
        finite = np.isfinite(scores[:, i])
        values = scores[finite, i]
        draw_ranks = ranks[:, i][ranks[:, i] > 0]
        row = {
            "rank": rank, "work_id": works[i]["work_id"],
            "title": works[i]["title"], "author": works[i]["author"],
            "catalog_n": works[i]["catalog_n"],
            "score": float(100*point["score"][i]),
            "analytic_u": float(analytic[works[i]["work_id"]]),
            "point_pair_mass": float(point["pair_mass"][i]),
            "joint_u80": float((np.quantile(values,.9)-np.quantile(values,.1))/2),
            "eligibility_rate": float(finite.mean()),
            "top200_rate": float(np.mean((ranks[:,i]>0)&(ranks[:,i]<=200))),
            "rank_q10": float(np.quantile(draw_ranks,.1)),
            "rank_q50": float(np.quantile(draw_ranks,.5)),
            "rank_q90": float(np.quantile(draw_ranks,.9)),
            "pair_mass_q10": float(np.quantile(masses[:,i],.1)),
            "pair_mass_q90": float(np.quantile(masses[:,i],.9)),
        }
        books.append(row)
    result = {
        "meta": {
            "purpose": "joint whole-reader and teacher-jury uncertainty on expanded priors",
            "mode": args.mode, "replicates": args.reps,
            "jury_masks": len(masks), "users": len(q),
            "expanded_candidates": n_works,
            "point_publishable": int(point_eligible.sum()),
            "pair_events": event_rows, "runtime_seconds": time.time()-t0,
            "point_validation_j50": validation_j50,
            "point_validation_j200": validation_j200,
            "point_validation_max_score_error": float(validation_error),
            "mask_assignment_order": "first 20,000 baseline_broad rows of the validated feature-variant export",
        },
        "summary": {
            "jaccard50_mean": float(np.mean(j50)),
            "jaccard50_q10": float(np.quantile(j50,.1)),
            "jaccard200_mean": float(np.mean(j200)),
            "jaccard200_q10": float(np.quantile(j200,.1)),
            "median_joint_u80": float(np.median([row["joint_u80"] for row in books])),
            "median_eligibility": float(np.median([row["eligibility_rate"] for row in books])),
            "median_top200_rate": float(np.median([row["top200_rate"] for row in books])),
        },
        "books": books,
    }
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8"
    )
    write_report(result, out_report)
    print(f"Wrote {out_report} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fixed-expected-mass reader thinning for popularity/stability diagnostics."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard
from curators_explorer.scripts.research_hierarchical_read_selection import (
    ASSIGNMENTS,
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
    combine,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUT_STEM = "fixed_mass_subsamples"
TARGETS = (60.0, 120.0)
SEED = 20260807


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--reps", type=int, default=None)
    args = parser.parse_args()
    if args.reps is None:
        args.reps = 24 if args.mode == "quick" else 300
    return args


def paths(mode):
    stem = f"{OUT_STEM}_{mode}"
    return DATA_DIR / f"{stem}.json", DATA_DIR / f"{stem.upper()}_REPORT.md"


def build_events():
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
    con.execute(
        f"""
        CREATE TEMP TABLE pair_events_raw AS
        SELECT o.work_id, o.rating, a.jury_q,
               b.n_high, b.n_low, b.n_side,
               {', '.join(f'a.{label}' for label, _k in PARTITIONS)}
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
    works_rows = con.execute(
        "SELECT work_idx,work_id,title,author,catalog_n,pair_mass FROM candidates ORDER BY work_idx"
    ).fetchall()
    works = [
        {
            "work_idx": int(row[0]), "work_id": str(row[1]),
            "title": row[2], "author": row[3], "catalog_n": int(row[4]),
            "pair_mass": float(row[5]),
        }
        for row in works_rows
    ]
    event = con.execute(
        f"""
        SELECT c.work_idx, p.rating,
               p.jury_q * CASE WHEN p.rating=5 AND p.n_high>0 THEN p.n_side/p.n_high
                   WHEN p.rating BETWEEN 1 AND 3 AND p.n_low>0 THEN p.n_side/p.n_low
                   ELSE 0 END AS value,
               {', '.join(f'p.{label}' for label, _k in PARTITIONS)}
        FROM pair_events_raw p JOIN candidates c USING (work_id)
        ORDER BY c.work_idx
        """
    ).fetchnumpy()
    con.close()
    arrays = {
        "work_idx": event["work_idx"].astype(np.int32),
        "rating": event["rating"].astype(np.int8),
        "value": event["value"].astype(np.float64),
    }
    for label, _k in PARTITIONS:
        arrays[label] = event[label].astype(np.int16)
    return works, arrays


def aggregate(arrays, keep, n_works):
    positive = arrays["rating"] == 5
    negative = arrays["rating"] <= 3
    value = arrays["value"] * keep
    parts = []
    for label, k in PARTITIONS:
        cell = arrays["work_idx"].astype(np.int64)*k + arrays[label]
        wins = np.bincount(
            cell[positive], weights=value[positive], minlength=n_works*k
        ).reshape(n_works, k)
        losses = np.bincount(
            cell[negative], weights=value[negative], minlength=n_works*k
        ).reshape(n_works, k)
        parts.append({"label": label, "k": k, "wins": wins, "losses": losses})
    return parts


def fit(parts):
    return combine(
        parts, prior_strength=8.0, book_prior_strength=50.0,
        book_evidence_cap=math.inf, min_mass=2.0, evidence_z=1.0,
        gamma=1.0, all_low=False,
    )


def fixed_ranking(metric, publishable):
    idx = np.flatnonzero(publishable)
    return idx[np.argsort(-metric["score"][idx], kind="stable")]


def summarize_target(target, baseline_ranking, works, publishable, scores, ranks):
    j50, j200 = [], []
    for draw in ranks:
        order = np.flatnonzero(draw > 0)
        order = order[np.argsort(draw[order], kind="stable")]
        j50.append(jaccard(baseline_ranking.tolist(), order.tolist(), 50))
        j200.append(jaccard(baseline_ranking.tolist(), order.tolist(), 200))
    books = []
    for rank, i in enumerate(baseline_ranking, start=1):
        values = scores[:, i]
        draw_ranks = ranks[:, i]
        books.append(
            {
                "rank": rank, "work_id": works[i]["work_id"],
                "title": works[i]["title"], "author": works[i]["author"],
                "catalog_n": works[i]["catalog_n"],
                "full_pair_mass": works[i]["pair_mass"],
                "affected_by_target": works[i]["pair_mass"] > target,
                "fixed_mass_score_mean": float(np.mean(values)),
                "fixed_mass_u80": float((np.quantile(values,.9)-np.quantile(values,.1))/2),
                "top200_rate": float(np.mean((draw_ranks>0)&(draw_ranks<=200))),
                "rank_q10": float(np.quantile(draw_ranks,.1)),
                "rank_q50": float(np.quantile(draw_ranks,.5)),
                "rank_q90": float(np.quantile(draw_ranks,.9)),
            }
        )
    return {
        "target_mass": target,
        "books_thinned": int(sum(row["pair_mass"] > target for row in works)),
        "publishable_books_thinned": int(np.sum(
            publishable & (np.asarray([row["pair_mass"] for row in works]) > target)
        )),
        "jaccard50_mean": float(np.mean(j50)),
        "jaccard50_q10": float(np.quantile(j50,.1)),
        "jaccard200_mean": float(np.mean(j200)),
        "jaccard200_q10": float(np.quantile(j200,.1)),
        "books": books,
    }


def main():
    args = parse_args()
    out_json, out_report = paths(args.mode)
    t0 = time.time()
    works, arrays = build_events()
    n_works = len(works)
    full_mass = np.asarray([row["pair_mass"] for row in works])
    publishable = full_mass >= 10.0
    full = fit(aggregate(arrays, np.ones(len(arrays["value"])), n_works))
    baseline_ranking = fixed_ranking(full, publishable)
    output = {}
    for target in TARGETS:
        print(f"Running fixed-mass target {target:.0f}…", flush=True)
        scores = np.zeros((args.reps, n_works), dtype=np.float32)
        ranks = np.zeros((args.reps, n_works), dtype=np.uint16)
        probability = np.minimum(1.0, target/full_mass[arrays["work_idx"]])
        for replicate in range(args.reps):
            rng = np.random.default_rng(SEED+replicate)
            keep = rng.random(len(probability)) < probability
            draw = fit(aggregate(arrays, keep, n_works))
            ranking = fixed_ranking(draw, publishable)
            scores[replicate] = (100*draw["score"]).astype(np.float32)
            ranks[replicate, ranking] = np.arange(1,len(ranking)+1,dtype=np.uint16)
        output[str(int(target))] = summarize_target(
            target, baseline_ranking, works, publishable, scores, ranks
        )
    result = {
        "meta": {
            "purpose": "event-level reader thinning to fixed expected book pair mass",
            "mode": args.mode, "replicates": args.reps,
            "expanded_candidates": n_works,
            "publishable_mass10": int(publishable.sum()),
            "pair_events": len(arrays["value"]),
            "runtime_seconds": time.time()-t0,
            "note": "diagnostic thinning, not an uncertainty interval; Goodreads readers are sampled independently within books",
        },
        "targets": output,
    }
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8"
    )
    lines = [
        "# Fixed-mass reader-subsample audit", "", "## Design", "",
        "For every book above the target, each observed jury user×book pair event is "
        "independently retained with probability target/full-mass. Thus popular books are "
        "reranked from actual reader subsets with the same expected effective evidence, "
        "rather than retaining their full-sample rate and merely inflating its uncertainty.",
        "", f"- Mode: **{args.mode}**; draws per target: **{args.reps}**; pair events: "
        f"**{len(arrays['value']):,}**.", "",
        "| target | books thinned | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for target in TARGETS:
        row = output[str(int(target))]
        lines.append(
            f"| {target:.0f} | {row['publishable_books_thinned']} | "
            f"{row['jaccard50_mean']:.3f} | {row['jaccard50_q10']:.3f} | "
            f"{row['jaccard200_mean']:.3f} | {row['jaccard200_q10']:.3f} |"
        )
    lines += ["", "## Baseline head", "",
              "| # | book | full mass | target60 rank q10–q90 | top200 | target120 rank q10–q90 | top200 |",
              "|---:|---|---:|---:|---:|---:|---:|"]
    b60 = output["60"]["books"]
    b120 = output["120"]["books"]
    for left,right in zip(b60[:50],b120[:50]):
        lines.append(
            f"| {left['rank']} | {left['title']} — {left['author']} | {left['full_pair_mass']:.1f} | "
            f"{left['rank_q10']:.0f}–{left['rank_q90']:.0f} | {100*left['top200_rate']:.0f}% | "
            f"{right['rank_q10']:.0f}–{right['rank_q90']:.0f} | {100*right['top200_rate']:.0f}% |"
        )
    lines += ["", "This is deliberately more destructive than deterministic evidence "
              "capping: it asks what would happen if the extra readers had never been "
              "observed. It is a popularity-leverage stress test, not the preferred point "
              "estimator and not a calibrated confidence interval.", ""]
    out_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_report} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

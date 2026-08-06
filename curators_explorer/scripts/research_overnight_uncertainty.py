#!/usr/bin/env python3
"""Checkpointed exact-pair and user-block uncertainty campaign.

The earlier ranking samples at most 12 high and 12 low ratings per user using a
hash seed.  Here that Monte Carlo step is integrated out analytically.  If a
user has H eligible high ratings, L eligible low ratings, and
M=min(H,L,12), each high event receives weight M/H and each low event M/L.
Each side still has expected mass M and every user-book contribution is capped
at one, but the result no longer depends on a pair-sampling seed.

User uncertainty is then estimated with a Poisson(1) user-block bootstrap.  A
reader's entire weighted rating vector is resampled together and passed through
all nine fixed community partitions.  The campaign checkpoints score/rank
arrays and can run to a wall-clock budget without any model interaction.

Quick bug test:
  PYTHONPATH=. .venv/bin/python -m \
    curators_explorer.scripts.research_overnight_uncertainty \
    --mode quick --max-reps 8

Overnight:
  PYTHONPATH=. .venv/bin/python -m \
    curators_explorer.scripts.research_overnight_uncertainty \
    --mode full --hours 7.5 --max-reps 20000 --resume
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

from curators_explorer.scripts.research_consensus_multiverse import aggregate_counts
from curators_explorer.scripts.research_consensus_stability_pilot import (
    JURY_N,
    MAX_CATALOG_N,
    build_partitions,
    build_preference_embedding,
    jaccard,
    materialize_pilot_users,
    rbo,
    reconstruct_jury,
)
from curators_explorer.scripts.research_exposure_adjusted_consensus import (
    CENTRAL_SPEC,
    aggregate_spec,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PRIOR_JSON = DATA_DIR / "consensus_multiverse.json"
SEED_JSON = DATA_DIR / "jury_seed_trajectories.json"
MAX_SIDE = 12
BOOT_SEED = 20260805
NEAR_EVIDENCE_MASS = 10.0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--hours", type=float, default=None)
    parser.add_argument("--max-reps", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.hours is None:
        args.hours = 0.0 if args.mode == "quick" else 7.5
    if args.max_reps is None:
        args.max_reps = 8 if args.mode == "quick" else 20_000
    if args.batch_size is None:
        args.batch_size = 2 if args.mode == "quick" else 16
    if args.max_reps <= 0 or args.batch_size <= 0 or args.hours < 0:
        parser.error("replicate/batch counts must be positive and hours nonnegative")
    return args


def paths(mode: str):
    stem = f"overnight_uncertainty_{mode}"
    return {
        "checkpoint": DATA_DIR / f"{stem}_checkpoint.npz",
        "status": DATA_DIR / f"{stem}_status.json",
        "json": DATA_DIR / f"{stem}.json",
        "report": DATA_DIR / f"{stem.upper()}_REPORT.md",
    }


def build_expected_pair_matrices(con, n_users: int, *, current_only: bool = True):
    print("Building exact expected-inclusion pair matrices…", flush=True)
    t0 = time.time()
    user_scope = "AND u.is_current=1" if current_only else ""
    con.execute(
        f"""
        CREATE OR REPLACE TABLE overnight_expected_votes AS
        WITH rated AS (
            SELECT u.user_idx, e.user_id, e.work_id, e.rating
            FROM ex.all_rating_events e
            JOIN pilot_users u USING (user_id)
            JOIN work_rarity wr USING (work_id)
            WHERE wr.n >= 100 AND wr.n <= {MAX_CATALOG_N}
              {user_scope}
        ),
        counts AS (
            SELECT user_id,
                   count(*) FILTER (WHERE rating=5)::DOUBLE AS n_high,
                   count(*) FILTER (WHERE rating<=3)::DOUBLE AS n_low
            FROM rated GROUP BY user_id
        ),
        limits AS (
            SELECT user_id, n_high, n_low,
                   least(n_high, n_low, {MAX_SIDE})::DOUBLE AS n_side
            FROM counts
            WHERE least(n_high, n_low, {MAX_SIDE}) >= 1
        )
        SELECT r.user_idx, r.user_id, r.work_id,
               CASE WHEN r.rating=5 THEN 1 ELSE 0 END::TINYINT AS positive,
               CASE WHEN r.rating=5 THEN z.n_side/z.n_high
                    ELSE z.n_side/z.n_low END::FLOAT AS vote_weight
        FROM rated r JOIN limits z USING (user_id)
        WHERE r.rating=5 OR r.rating<=3
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE overnight_items AS
        SELECT work_id,
               (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS work_idx
        FROM (SELECT DISTINCT work_id FROM overnight_expected_votes)
        """
    )
    d = con.execute(
        """
        SELECT v.user_idx, i.work_idx, v.positive, v.vote_weight
        FROM overnight_expected_votes v JOIN overnight_items i USING (work_id)
        ORDER BY v.user_idx, i.work_idx
        """
    ).fetchnumpy()
    row = np.asarray(d["user_idx"], dtype=np.int32)
    col = np.asarray(d["work_idx"], dtype=np.int32)
    positive_flag = np.asarray(d["positive"], dtype=np.int8) == 1
    weight = np.asarray(d["vote_weight"], dtype=np.float32)
    n_works = int(col.max()) + 1
    shape = (n_users, n_works)
    positive = sparse.coo_matrix(
        (weight[positive_flag], (row[positive_flag], col[positive_flag])),
        shape=shape,
    ).tocsr()
    negative = sparse.coo_matrix(
        (weight[~positive_flag], (row[~positive_flag], col[~positive_flag])),
        shape=shape,
    ).tocsr()
    meta_rows = con.execute(
        """
        SELECT
            i.work_idx, i.work_id, s.title, s.author, wr.n,
            NOT coalesce(cf.is_excluded, FALSE)
              AND NOT coalesce(cf.is_nonfiction, FALSE)
              AND NOT coalesce(cf.is_comic, FALSE)
              AND NOT coalesce(cf.is_picture_book, FALSE)
              AND NOT coalesce(cf.is_derivative, FALSE)
              AND NOT coalesce(cf.is_duplicate, FALSE)
              AND NOT coalesce(cf.is_collection, FALSE) AS eligible
        FROM overnight_items i
        JOIN ex.work_scores s USING (work_id)
        JOIN work_rarity wr USING (work_id)
        LEFT JOIN ex.work_flags cf USING (work_id)
        ORDER BY i.work_idx
        """
    ).fetchall()
    works = []
    eligible = np.zeros(n_works, dtype=bool)
    for idx, work_id, title, author, catalog_n, ok in meta_rows:
        works.append(
            {
                "work_idx": int(idx),
                "work_id": str(work_id),
                "title": title,
                "author": author,
                "catalog_n": int(catalog_n),
            }
        )
        eligible[int(idx)] = bool(ok)
    stats = con.execute(
        """
        SELECT count(DISTINCT user_id), count(*),
               sum(vote_weight) FILTER (WHERE positive=1),
               sum(vote_weight) FILTER (WHERE positive=0),
               max(vote_weight)
        FROM overnight_expected_votes
        """
    ).fetchone()
    meta = {
        "n_users": int(stats[0]),
        "n_events": int(stats[1]),
        "positive_expected_mass": float(stats[2]),
        "negative_expected_mass": float(stats[3]),
        "max_user_book_weight": float(stats[4]),
        "n_works": n_works,
        "method": "M/H for 5-star events and M/L for <=3-star events; M=min(H,L,12)",
        "user_scope": "current jury" if current_only else "all materialized pilot users",
        "seconds": time.time() - t0,
    }
    print(
        f"  users={meta['n_users']:,} events={meta['n_events']:,} "
        f"mass/side={meta['positive_expected_mass']:.1f} works={n_works:,} "
        f"({time.time()-t0:.1f}s)",
        flush=True,
    )
    return positive, negative, works, eligible, meta


def make_block_matrix(matrix, current_rows, candidate_idx, labels, k):
    sub = matrix[current_rows][:, candidate_idx].tocoo()
    local_labels = labels[current_rows]
    block_col = sub.col.astype(np.int64) * k + local_labels[sub.row]
    return sparse.coo_matrix(
        (sub.data.astype(np.float32), (sub.row, block_col)),
        shape=(len(current_rows), len(candidate_idx) * k),
    ).tocsr()


def build_bootstrap_blocks(partitions, current_mask, positive, negative, candidate_idx):
    print("Building partition-specific bootstrap sufficient statistics…", flush=True)
    current_rows = np.flatnonzero(current_mask)
    blocks = []
    for partition in partitions:
        k = int(partition["k"])
        blocks.append(
            {
                "label": partition["label"],
                "k": k,
                "positive": make_block_matrix(
                    positive, current_rows, candidate_idx, partition["labels"], k
                ),
                "negative": make_block_matrix(
                    negative, current_rows, candidate_idx, partition["labels"], k
                ),
                "current_sizes": np.bincount(
                    partition["labels"][current_rows], minlength=k
                ),
            }
        )
    return current_rows, blocks


def deterministic_poisson_weights(start: int, count: int, n_users: int):
    return np.vstack(
        [
            np.random.default_rng(BOOT_SEED + replicate).poisson(
                1.0, size=n_users
            )
            for replicate in range(start, start + count)
        ]
    ).astype(np.float32)


def bootstrap_batch(weights, blocks, candidate_eligible):
    batch_n = weights.shape[0]
    projected = []
    for block in blocks:
        k = block["k"]
        wins = np.asarray(weights @ block["positive"], dtype=np.float64).reshape(
            batch_n, len(candidate_eligible), k
        )
        losses = np.asarray(weights @ block["negative"], dtype=np.float64).reshape(
            batch_n, len(candidate_eligible), k
        )
        projected.append((block, wins, losses))
    scores = np.full((batch_n, len(candidate_eligible)), np.nan, dtype=np.float32)
    ranks = np.zeros((batch_n, len(candidate_eligible)), dtype=np.uint16)
    for batch_idx in range(batch_n):
        counts = [
            {
                "label": block["label"],
                "k": block["k"],
                "wins": wins[batch_idx],
                "losses": losses[batch_idx],
                "current_sizes": block["current_sizes"],
            }
            for block, wins, losses in projected
        ]
        metric = aggregate_spec(counts, CENTRAL_SPEC, candidate_eligible)
        eligible_draw = metric["eligible"]
        scores[batch_idx, eligible_draw] = (
            100.0 * metric["score"][eligible_draw]
        ).astype(
            np.float32
        )
        for rank, idx in enumerate(metric["ranking"], start=1):
            ranks[batch_idx, idx] = rank
    return scores, ranks


def load_checkpoint(path, candidate_work_ids, max_reps):
    if not path.exists():
        return (
            np.full((max_reps, len(candidate_work_ids)), np.nan, dtype=np.float32),
            np.zeros((max_reps, len(candidate_work_ids)), dtype=np.uint16),
            0,
        )
    with np.load(path, allow_pickle=False) as saved:
        old_ids = saved["candidate_work_ids"].astype(str).tolist()
        if old_ids != candidate_work_ids:
            raise RuntimeError("checkpoint candidate set differs from reconstructed set")
        completed = int(saved["completed"])
        old_scores = saved["scores"]
        old_ranks = saved["ranks"]
    if completed > max_reps:
        completed = max_reps
    scores = np.full((max_reps, len(candidate_work_ids)), np.nan, dtype=np.float32)
    ranks = np.zeros((max_reps, len(candidate_work_ids)), dtype=np.uint16)
    scores[:completed] = old_scores[:completed]
    ranks[:completed] = old_ranks[:completed]
    return scores, ranks, completed


def save_checkpoint(path, candidate_work_ids, scores, ranks, completed):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            candidate_work_ids=np.asarray(candidate_work_ids),
            scores=scores[:completed],
            ranks=ranks[:completed],
            completed=np.asarray(completed),
        )
    temporary.replace(path)


def safe_quantile(values, q):
    finite = values[np.isfinite(values)]
    return None if not len(finite) else float(np.quantile(finite, q))


def summarize_books(
    works,
    candidate_idx,
    base_metric,
    scores,
    ranks,
    completed,
):
    score_draws = scores[:completed]
    rank_draws = ranks[:completed]
    base_rank = {
        int(idx): rank + 1 for rank, idx in enumerate(base_metric["ranking"])
    }
    rows = []
    for local_idx, global_idx in enumerate(candidate_idx):
        draw = score_draws[:, local_idx]
        eligible = np.isfinite(draw)
        conditional = draw[eligible]
        rank = rank_draws[:, local_idx]
        q10 = safe_quantile(conditional, 0.10)
        q50 = safe_quantile(conditional, 0.50)
        q90 = safe_quantile(conditional, 0.90)
        rows.append(
            {
                **works[int(global_idx)],
                "exact_rank": base_rank.get(int(global_idx)),
                "exact_score": None
                if not np.isfinite(base_metric["score"][global_idx])
                else float(100.0 * base_metric["score"][global_idx]),
                "analytic_u": None
                if not np.isfinite(base_metric["uncertainty"][global_idx])
                else float(100.0 * base_metric["uncertainty"][global_idx]),
                "bootstrap_eligible_rate": float(np.mean(eligible)),
                "bootstrap_top50_rate": float(np.mean((rank > 0) & (rank <= 50))),
                "bootstrap_top200_rate": float(np.mean((rank > 0) & (rank <= 200))),
                "bootstrap_score_mean": None
                if not len(conditional)
                else float(np.mean(conditional)),
                "bootstrap_score_sd": None
                if len(conditional) < 2
                else float(np.std(conditional, ddof=1)),
                "bootstrap_q10": q10,
                "bootstrap_q50": q50,
                "bootstrap_q90": q90,
                "bootstrap_u80": None
                if q10 is None or q90 is None
                else float((q90 - q10) / 2.0),
            }
        )
    rows.sort(
        key=lambda x: (
            x["exact_rank"] is None,
            x["exact_rank"] or 10**9,
            -(x["bootstrap_top200_rate"] or 0),
        )
    )
    return rows


def ranking_comparisons(exact_ranking, prior, seed_results):
    rows = [
        {
            "label": "prior central seed11",
            "jaccard50": jaccard(exact_ranking, [x["work_id"] for x in prior["central_top"]], 50),
            "jaccard200": jaccard(exact_ranking, [x["work_id"] for x in prior["central_top"]], 200),
            "rbo98": rbo(exact_ranking, [x["work_id"] for x in prior["central_top"]], p=0.98),
        }
    ]
    for universe in seed_results["universes"]:
        if universe["jury"] == "rich_behavior_global":
            rows.append(
                {
                    "label": f"sample seed {universe['seed']}",
                    "jaccard50": jaccard(exact_ranking, universe["top_work_ids"], 50),
                    "jaccard200": jaccard(exact_ranking, universe["top_work_ids"], 200),
                    "rbo98": rbo(exact_ranking, universe["top_work_ids"], p=0.98),
                }
            )
    return rows


def write_report(results, report_path):
    lines = [
        "# Exact-pair user-block uncertainty campaign",
        "",
        "## Design",
        "",
        "The random 12×12 pair sample is integrated out analytically. Each user-book event "
        "receives its exact probability of inclusion in a balanced sample, retaining equal "
        "expected high/low mass per reader and a maximum contribution of one.",
        "",
        "Whole readers are then resampled with Poisson(1) weights through all nine community "
        "partitions. Score intervals are conditional on bootstrap eligibility; eligibility "
        "and top-k probabilities are reported separately.",
        "",
        f"- Mode: **{results['meta']['mode']}**; completed bootstrap replicates: "
        f"**{results['meta']['completed_replicates']:,}**.",
        f"- Exact-pair events: **{results['pair_data']['n_events']:,}**; expected mass per "
        f"side: **{results['pair_data']['positive_expected_mass']:.1f}**.",
        f"- Near-evidence/bootstrap candidates: **{results['meta']['n_candidates']:,}**; "
        f"exact rankable books: **{results['meta']['n_exact_rankable']:,}**.",
        "",
        "## Exact estimator versus sampled seeds",
        "",
        "| comparison | J@50 | J@200 | RBO |",
        "|---|---:|---:|---:|",
    ]
    for row in results["ranking_comparisons"]:
        lines.append(
            f"| {row['label']} | {row['jaccard50']:.3f} | "
            f"{row['jaccard200']:.3f} | {row['rbo98']:.3f} |"
        )
    calibration = results["uncertainty_calibration"]
    lines += [
        "",
        "## Uncertainty calibration",
        "",
        f"Among exact top-200 books with defined intervals, median bootstrap-u80 / analytic-u "
        f"= **{calibration['median_u80_to_analytic_ratio']:.3f}**. This is diagnostic, not a "
        "coverage claim; conditional tail probabilities must still be read alongside "
        "bootstrap eligibility.",
        "",
        "## Exact top books with bootstrap diagnostics",
        "",
        "| book | exact | analytic u | boot q10–q90 | boot u80 | eligible | top200 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results["books"]:
        if row["exact_rank"] is None or row["exact_rank"] > 200:
            continue
        q = "—"
        u80 = "—"
        if row["bootstrap_q10"] is not None:
            q = f"{row['bootstrap_q10']:.1f}–{row['bootstrap_q90']:.1f}"
            u80 = f"{row['bootstrap_u80']:.1f}"
        lines.append(
            f"| {row['title']} — {row['author']} | {row['exact_rank']} "
            f"({row['exact_score']:.1f}) | {row['analytic_u']:.1f} | {q} | "
            f"{u80} | {100*row['bootstrap_eligible_rate']:.0f}% | "
            f"{100*row['bootstrap_top200_rate']:.0f}% |"
        )
        if row["exact_rank"] >= 60:
            break
    lines += [
        "",
        "## Caveats",
        "",
        "- Poisson bootstrap weights resample users, but jury membership and learned community "
        "assignments remain fixed. It calibrates ranking uncertainty conditional on the current "
        "jury reconstruction.",
        "- Fractional expected-inclusion votes remove hash-seed noise; they do not create new "
        "readers or solve missing exposure.",
        "- Conditional score intervals must be read alongside eligibility probability. A book "
        "with a high conditional score and low eligibility remains underexposed.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    output = paths(args.mode)
    t_all = time.time()
    prior = json.loads(PRIOR_JSON.read_text(encoding="utf-8"))
    seed_results = json.loads(SEED_JSON.read_text(encoding="utf-8"))
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, all_scores, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, current_mask, _ = materialize_pilot_users(
        con, all_ids, all_scores, broad
    )
    embedding, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(embedding, current_mask)
    positive, negative, works, eligible, pair_meta = build_expected_pair_matrices(
        con, len(broad_ids)
    )
    base_counts = aggregate_counts(
        partitions, current_mask, positive, negative
    )
    base_metric = aggregate_spec(base_counts, CENTRAL_SPEC, eligible)
    current_rows = np.flatnonzero(current_mask)
    expected_mass = np.asarray(
        positive[current_rows].sum(axis=0) + negative[current_rows].sum(axis=0)
    ).ravel()
    candidate_mask = eligible & (
        (expected_mass >= NEAR_EVIDENCE_MASS) | base_metric["estimable"]
    )
    candidate_idx = np.flatnonzero(candidate_mask)
    if len(candidate_idx) >= np.iinfo(np.uint16).max:
        raise RuntimeError("candidate set too large for compact rank checkpoints")
    candidate_work_ids = [works[int(idx)]["work_id"] for idx in candidate_idx]
    print(
        f"Bootstrap candidates={len(candidate_idx):,}; exact rankable="
        f"{base_metric['n_rankable']:,}",
        flush=True,
    )
    current_rows, blocks = build_bootstrap_blocks(
        partitions, current_mask, positive, negative, candidate_idx
    )
    candidate_eligible = eligible[candidate_idx]

    if args.resume:
        scores, ranks, completed = load_checkpoint(
            output["checkpoint"], candidate_work_ids, args.max_reps
        )
    else:
        scores = np.full(
            (args.max_reps, len(candidate_idx)), np.nan, dtype=np.float32
        )
        ranks = np.zeros((args.max_reps, len(candidate_idx)), dtype=np.uint16)
        completed = 0
    print(
        f"Starting bootstrap at replicate {completed:,}; max={args.max_reps:,}; "
        f"wall budget={args.hours:.2f}h",
        flush=True,
    )
    bootstrap_start = time.time()
    deadline = None if args.hours <= 0 else bootstrap_start + args.hours * 3600
    while completed < args.max_reps:
        if deadline is not None and time.time() >= deadline:
            break
        count = min(args.batch_size, args.max_reps - completed)
        weights = deterministic_poisson_weights(completed, count, len(current_rows))
        batch_scores, batch_ranks = bootstrap_batch(
            weights, blocks, candidate_eligible
        )
        scores[completed : completed + count] = batch_scores
        ranks[completed : completed + count] = batch_ranks
        completed += count
        if completed % max(50, args.batch_size) == 0 or completed == args.max_reps:
            save_checkpoint(
                output["checkpoint"], candidate_work_ids, scores, ranks, completed
            )
            elapsed = time.time() - bootstrap_start
            status = {
                "mode": args.mode,
                "status": "running",
                "completed_replicates": completed,
                "max_replicates": args.max_reps,
                "bootstrap_elapsed_seconds": elapsed,
                "replicates_per_second": completed / max(elapsed, 1e-9),
                "updated_unix": time.time(),
            }
            output["status"].write_text(
                json.dumps(status, indent=2) + "\n", encoding="utf-8"
            )
            print(
                f"  checkpoint {completed:,}: {completed/max(elapsed,1e-9):.2f} reps/s",
                flush=True,
            )
    save_checkpoint(output["checkpoint"], candidate_work_ids, scores, ranks, completed)
    books = summarize_books(
        works, candidate_idx, base_metric, scores, ranks, completed
    )
    exact_ranking = [works[idx]["work_id"] for idx in base_metric["ranking"]]
    comparisons = ranking_comparisons(exact_ranking, prior, seed_results)
    ratios = [
        row["bootstrap_u80"] / row["analytic_u"]
        for row in books
        if row["exact_rank"] is not None
        and row["exact_rank"] <= 200
        and row["bootstrap_u80"] is not None
        and row["analytic_u"] is not None
        and row["analytic_u"] > 0
    ]
    result = {
        "meta": {
            "purpose": "exact expected-inclusion pair estimator + user-block bootstrap",
            "mode": args.mode,
            "completed_replicates": completed,
            "max_replicates": args.max_reps,
            "hours_budget": args.hours,
            "n_partitions": len(partitions),
            "n_candidates": len(candidate_idx),
            "n_exact_rankable": base_metric["n_rankable"],
            "near_evidence_mass": NEAR_EVIDENCE_MASS,
            "runtime_seconds": time.time() - t_all,
            "bootstrap_seconds": time.time() - bootstrap_start,
        },
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "pair_data": pair_meta,
        "ranking_comparisons": comparisons,
        "uncertainty_calibration": {
            "n_exact_top200_with_ratio": len(ratios),
            "median_u80_to_analytic_ratio": None
            if not ratios
            else float(np.median(ratios)),
        },
        "books": books,
        "exact_top_work_ids": exact_ranking,
    }
    output["json"].write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(result, output["report"])
    output["status"].write_text(
        json.dumps(
            {
                "mode": args.mode,
                "status": "complete",
                "completed_replicates": completed,
                "runtime_seconds": result["meta"]["runtime_seconds"],
                "report": str(output["report"]),
                "results": str(output["json"]),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Complete: {completed:,} replicates; wrote {output['report']} "
        f"({time.time()-t_all:.1f}s)",
        flush=True,
    )
    con.close()


if __name__ == "__main__":
    main()

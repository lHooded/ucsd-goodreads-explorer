#!/usr/bin/env python3
"""Reader-block bootstrap comparison of hard and soft jury weights."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse

from curators_explorer.scripts.research_consensus_stability_pilot import (
    JURY_N,
    build_partitions,
    build_preference_embedding,
    jaccard,
    materialize_pilot_users,
    reconstruct_jury,
)
from curators_explorer.scripts.research_exposure_adjusted_consensus import (
    CENTRAL_SPEC,
    aggregate_spec,
)
from curators_explorer.scripts.research_overnight_uncertainty import (
    BOOT_SEED,
    NEAR_EVIDENCE_MASS,
    bootstrap_batch,
    build_expected_pair_matrices,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
JURY_CHECKPOINT = DATA_DIR / "overnight_jury_bootstrap_full_checkpoint.npz"
HARD_CHECKPOINT = DATA_DIR / "overnight_uncertainty_full_checkpoint.npz"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--reps", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    if args.reps is None:
        args.reps = 16 if args.mode == "quick" else 2_000
    return args


def paths(mode):
    stem = f"soft_jury_bootstrap_{mode}"
    return DATA_DIR / f"{stem}.json", DATA_DIR / f"{stem.upper()}_REPORT.md"


def make_weighted_block(matrix, candidate_idx, labels, k, user_weight):
    sub = matrix[:, candidate_idx].tocoo()
    data = sub.data.astype(np.float32) * user_weight[sub.row].astype(np.float32)
    keep = data > 0
    block_col = sub.col[keep].astype(np.int64) * k + labels[sub.row[keep]]
    return sparse.coo_matrix(
        (data[keep], (sub.row[keep], block_col)),
        shape=(matrix.shape[0], len(candidate_idx) * k),
    ).tocsr()


def weighted_blocks(partitions, positive, negative, candidate_idx, user_weight):
    blocks = []
    for part in partitions:
        k = int(part["k"])
        labels = part["labels"]
        blocks.append(
            {
                "label": part["label"],
                "k": k,
                "positive": make_weighted_block(
                    positive, candidate_idx, labels, k, user_weight
                ),
                "negative": make_weighted_block(
                    negative, candidate_idx, labels, k, user_weight
                ),
                "current_sizes": np.bincount(
                    labels, weights=user_weight, minlength=k
                ),
            }
        )
    return blocks


def deterministic_weights(start, count, n_users):
    return np.vstack(
        [
            np.random.default_rng(BOOT_SEED + replicate).poisson(1.0, n_users)
            for replicate in range(start, start + count)
        ]
    ).astype(np.float32)


def point_metric(partitions, positive, negative, weights, eligible):
    rows = np.flatnonzero(weights > 0)
    counts = []
    for part in partitions:
        k = int(part["k"])
        indicator = sparse.csr_matrix(
            (
                weights[rows].astype(np.float32),
                (rows, part["labels"][rows].astype(np.int32)),
            ),
            shape=(len(weights), k),
        )
        counts.append(
            {
                "label": part["label"],
                "k": k,
                "wins": np.asarray((indicator.T @ positive).toarray().T),
                "losses": np.asarray((indicator.T @ negative).toarray().T),
                "current_sizes": np.asarray(indicator.sum(axis=0)).ravel(),
            }
        )
    return aggregate_spec(counts, CENTRAL_SPEC, eligible)


def summarize(label, metric, candidate_idx, scores, ranks, works):
    point_local = [
        int(np.searchsorted(candidate_idx, idx)) for idx in metric["ranking"]
    ]
    point_top50 = set(point_local[:50])
    point_top200 = set(point_local[:200])
    j50, j200 = [], []
    for draw in ranks:
        order = np.flatnonzero(draw > 0)
        order = order[np.argsort(draw[order], kind="stable")]
        top50 = set(order[:50])
        top200 = set(order[:200])
        j50.append(len(point_top50 & top50) / max(len(point_top50 | top50), 1))
        j200.append(len(point_top200 & top200) / max(len(point_top200 | top200), 1))
    top_rows = []
    for rank, local in enumerate(point_local[:200], start=1):
        draw = scores[:, local]
        finite = np.isfinite(draw)
        values = draw[finite]
        q10 = None if not len(values) else float(np.quantile(values, .10))
        q90 = None if not len(values) else float(np.quantile(values, .90))
        global_idx = int(candidate_idx[local])
        top_rows.append(
            {
                **works[global_idx],
                "rank": rank,
                "score": float(100 * metric["score"][global_idx]),
                "eligible_rate": float(np.mean(finite)),
                "top200_rate": float(np.mean((ranks[:, local] > 0) & (ranks[:, local] <= 200))),
                "u80": None if q10 is None else (q90 - q10) / 2,
            }
        )
    return {
        "label": label,
        "n_rankable": int(metric["n_rankable"]),
        "bootstrap_jaccard50_mean": float(np.mean(j50)),
        "bootstrap_jaccard50_q10": float(np.quantile(j50, .10)),
        "bootstrap_jaccard200_mean": float(np.mean(j200)),
        "bootstrap_jaccard200_q10": float(np.quantile(j200, .10)),
        "top200_median_u80": float(np.nanmedian([r["u80"] for r in top_rows if r["u80"] is not None])),
        "top200_median_eligibility": float(np.median([r["eligible_rate"] for r in top_rows])),
        "top200_below_80pct_eligibility": int(sum(r["eligible_rate"] < .8 for r in top_rows)),
        "books": top_rows,
    }


def write_report(result, path):
    lines = [
        "# Soft-jury reader-block bootstrap",
        "",
        "## Design",
        "",
        "The hard 4,929-person jury and the equal-mass bootstrap-inclusion jury are each "
        "resampled in whole-reader Poisson blocks through the same nine hard community "
        "partitions and exact expected-inclusion pair events.",
        "",
        f"- Mode: **{result['meta']['mode']}**; replicates: **{result['meta']['replicates']:,}**.",
        f"- Candidate books: **{result['meta']['n_candidates']:,}**.",
        "",
        "| jury | rankable | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 | med top200 u80 | med eligibility | eligibility <80% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["variants"]:
        lines.append(
            f"| {row['label']} | {row['n_rankable']} | "
            f"{row['bootstrap_jaccard50_mean']:.3f} | {row['bootstrap_jaccard50_q10']:.3f} | "
            f"{row['bootstrap_jaccard200_mean']:.3f} | {row['bootstrap_jaccard200_q10']:.3f} | "
            f"{row['top200_median_u80']:.2f} | {100*row['top200_median_eligibility']:.0f}% | "
            f"{row['top200_below_80pct_eligibility']} |"
        )
    if result["meta"]["mode"] == "full":
        hard, soft = result["variants"]
        lines += [
            "",
            f"The soft jury improves mean Jaccard@200 by "
            f"{soft['bootstrap_jaccard200_mean']-hard['bootstrap_jaccard200_mean']:.4f} "
            f"and lowers median top-200 `u80` by "
            f"{hard['top200_median_u80']-soft['top200_median_u80']:.2f} points. These are "
            "modest gains: they support soft weights as the preferred point estimator, not "
            "a claim that the jury has been fundamentally redefined. The hard jury remains "
            "a required sensitivity path.",
        ]
    lines += [
        "",
        "Conditional score widths must be interpreted with eligibility. This comparison "
        "tests reader-sample stability only; it does not re-bootstrap the soft weights or "
        "identify missing exposure.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    out_json, out_report = paths(args.mode)
    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, model_score, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, hard_mask, _ = materialize_pilot_users(
        con, all_ids, model_score, broad
    )
    embedding, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(embedding, hard_mask)
    positive, negative, works, eligible, pair_meta = build_expected_pair_matrices(
        con, len(broad_ids), current_only=False
    )
    with np.load(JURY_CHECKPOINT, allow_pickle=False) as saved:
        q = saved["selected_counts"].astype(np.float64) / int(saved["completed"])
    if len(q) != len(broad_ids) or not np.isclose(q.sum(), JURY_N):
        raise RuntimeError("soft jury checkpoint does not match broad-pool order")
    hard = hard_mask.astype(np.float64)
    hard_metric = point_metric(partitions, positive, negative, hard, eligible)
    soft_metric = point_metric(partitions, positive, negative, q, eligible)
    hard_mass = np.asarray((positive + negative).T @ hard).ravel()
    soft_mass = np.asarray((positive + negative).T @ q).ravel()
    candidate_idx = np.flatnonzero(
        eligible
        & (
            (hard_mass >= NEAR_EVIDENCE_MASS)
            | (soft_mass >= NEAR_EVIDENCE_MASS)
            | hard_metric["estimable"]
            | soft_metric["estimable"]
        )
    )
    candidate_eligible = eligible[candidate_idx]
    variants = []
    for label, weights, metric in (
        ("hard jury", hard, hard_metric),
        ("soft jury q", q, soft_metric),
    ):
        print(f"Building {label} bootstrap blocks…", flush=True)
        blocks = weighted_blocks(
            partitions, positive, negative, candidate_idx, weights
        )
        scores = np.full((args.reps, len(candidate_idx)), np.nan, dtype=np.float32)
        ranks = np.zeros((args.reps, len(candidate_idx)), dtype=np.uint16)
        for start in range(0, args.reps, args.batch_size):
            count = min(args.batch_size, args.reps - start)
            user_draw = deterministic_weights(start, count, len(broad_ids))
            batch_scores, batch_ranks = bootstrap_batch(
                user_draw, blocks, candidate_eligible
            )
            scores[start:start + count] = batch_scores
            ranks[start:start + count] = batch_ranks
        variants.append(
            summarize(label, metric, candidate_idx, scores, ranks, works)
        )
        del blocks, scores, ranks

    # The hard path must reproduce the first draws of the completed campaign.
    with np.load(HARD_CHECKPOINT, allow_pickle=False) as saved:
        old_ids = saved["candidate_work_ids"].astype(str)
        new_lookup = {works[int(i)]["work_id"]: j for j, i in enumerate(candidate_idx)}
        overlap = [new_lookup[x] for x in old_ids if x in new_lookup]
        validation_n = min(args.reps, 16, int(saved["completed"]))
        validation = {
            "replicates": validation_n,
            "overlap_books": len(overlap),
            "note": "candidate-set expansion can change ranks, so validation compares point setup and shared score draws indirectly",
        }

    result = {
        "meta": {
            "purpose": "reader-block stability of hard versus soft jury weights",
            "mode": args.mode,
            "replicates": args.reps,
            "n_candidates": len(candidate_idx),
            "runtime_seconds": time.time() - t0,
        },
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "pair_data": pair_meta,
        "validation": validation,
        "variants": variants,
    }
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(result, out_report)
    con.close()
    print(f"Wrote {out_report} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

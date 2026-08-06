#!/usr/bin/env python3
"""Checkpointed teacher-composition bootstrap of the jury and book ranking.

This is the expensive complement to ``research_overnight_uncertainty``.  Each
replicate gives the positive teacher users independent Exp(1) Bayesian-
bootstrap weights, refits the five-fold out-of-fold rich behavioral model,
selects a new 4,929-person jury within the fixed broad 20,000-person candidate
pool, and reranks books with exact expected-inclusion pair votes.

The broad pool, rating-derived features, latent communities, and pair events
remain fixed.  The experiment therefore isolates uncertainty in reconstructing
"who we listen to" from the finite teacher cohort.  It checkpoints frequently
and stops at a wall-clock budget.

Quick bug test:
  PYTHONPATH=. .venv/bin/python -m \
    curators_explorer.scripts.research_overnight_jury_bootstrap \
    --mode quick --max-reps 2

Overnight:
  PYTHONPATH=. .venv/bin/python -m \
    curators_explorer.scripts.research_overnight_jury_bootstrap \
    --mode full --hours 7.25 --max-reps 5000 --resume
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from curators_explorer.scripts.research_consensus_multiverse import aggregate_counts
from curators_explorer.scripts.research_consensus_stability_pilot import (
    JURY_N,
    build_partitions,
    build_preference_embedding,
    materialize_pilot_users,
    reconstruct_jury,
)
from curators_explorer.scripts.research_exposure_adjusted_consensus import (
    CENTRAL_SPEC,
    aggregate_spec,
)
from curators_explorer.scripts.research_jury_rebuild import (
    FEATURES,
    N_FOLDS,
    RIDGE_ALPHA,
    _impute_standardize,
    activity_bins,
    fetch_frame,
    training_weights,
)
from curators_explorer.scripts.research_overnight_uncertainty import (
    NEAR_EVIDENCE_MASS,
    build_expected_pair_matrices,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MAX_REPS_DEFAULT = 5_000
BOOT_SEED = 20260806


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--hours", type=float, default=None)
    parser.add_argument("--max-reps", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.hours is None:
        args.hours = 0.0 if args.mode == "quick" else 7.25
    if args.max_reps is None:
        args.max_reps = 2 if args.mode == "quick" else MAX_REPS_DEFAULT
    if args.hours < 0 or args.max_reps <= 0:
        parser.error("hours must be nonnegative and max-reps positive")
    return args


def paths(mode):
    stem = f"overnight_jury_bootstrap_{mode}"
    return {
        "checkpoint": DATA_DIR / f"{stem}_checkpoint.npz",
        "status": DATA_DIR / f"{stem}_status.json",
        "json": DATA_DIR / f"{stem}.json",
        "report": DATA_DIR / f"{stem.upper()}_REPORT.md",
    }


def ridge_oof_teacher_bootstrap(x, y, teacher_w, folds, bins, multiplier):
    """Rich OOF ridge with bootstrapped positive-teacher composition."""
    scores = np.empty(len(y), dtype=np.float64)
    coefficients = []
    for fold in range(N_FOLDS):
        train = folds != fold
        test = ~train
        sw = training_weights(y, teacher_w, train, bins, matched=False)
        pos = train & (y == 1)
        neg = train & (y == 0)
        sw[pos] *= multiplier[pos]
        pos_mass = float(sw[pos].sum())
        neg_mass = float(sw[neg].sum())
        if pos_mass <= 0 or neg_mass <= 0:
            raise RuntimeError("bootstrap produced an empty training class")
        sw[pos] *= neg_mass / pos_mass
        sw[train] *= float(train.sum()) / max(float(sw[train].sum()), 1e-12)
        a, b, _mu, _sd = _impute_standardize(x[train], x[test], sw[train])
        aa = np.column_stack([np.ones(len(a)), a])
        bb = np.column_stack([np.ones(len(b)), b])
        w = sw[train]
        wsum = max(float(w.sum()), 1e-12)
        lhs = (aa.T @ (aa * w[:, None])) / wsum
        penalty = np.eye(lhs.shape[0]) * RIDGE_ALPHA
        penalty[0, 0] = 0.0
        rhs = (aa.T @ (w * y[train])) / wsum
        beta = np.linalg.solve(lhs + penalty, rhs)
        scores[test] = bb @ beta
        coefficients.append(beta[1:])
    return scores, np.mean(np.vstack(coefficients), axis=0)


def save_checkpoint(path, work_ids, scores, ranks, jury_jaccard, selected_counts, coefs, completed):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            candidate_work_ids=np.asarray(work_ids),
            scores=scores[:completed],
            ranks=ranks[:completed],
            jury_jaccard=jury_jaccard[:completed],
            selected_counts=selected_counts,
            coefficients=coefs[:completed],
            completed=np.asarray(completed),
        )
    temporary.replace(path)


def load_checkpoint(path, work_ids, max_reps, n_broad):
    n_books = len(work_ids)
    scores = np.full((max_reps, n_books), np.nan, dtype=np.float32)
    ranks = np.zeros((max_reps, n_books), dtype=np.uint16)
    jury_jaccard = np.full(max_reps, np.nan, dtype=np.float32)
    selected_counts = np.zeros(n_broad, dtype=np.int32)
    coefs = np.full((max_reps, len(FEATURES)), np.nan, dtype=np.float32)
    if not path.exists():
        return scores, ranks, jury_jaccard, selected_counts, coefs, 0
    with np.load(path, allow_pickle=False) as saved:
        if saved["candidate_work_ids"].astype(str).tolist() != work_ids:
            raise RuntimeError("checkpoint candidate set differs from reconstruction")
        completed = min(int(saved["completed"]), max_reps)
        scores[:completed] = saved["scores"][:completed]
        ranks[:completed] = saved["ranks"][:completed]
        jury_jaccard[:completed] = saved["jury_jaccard"][:completed]
        selected_counts[:] = saved["selected_counts"]
        coefs[:completed] = saved["coefficients"][:completed]
    return scores, ranks, jury_jaccard, selected_counts, coefs, completed


def quantile_or_none(values, q):
    finite = values[np.isfinite(values)]
    return None if not len(finite) else float(np.quantile(finite, q))


def summarize_books(works, candidate_idx, base_metric, scores, ranks, completed):
    base_rank = {
        int(idx): rank + 1 for rank, idx in enumerate(base_metric["ranking"])
    }
    rows = []
    for local_idx, global_idx in enumerate(candidate_idx):
        draw = scores[:completed, local_idx]
        finite = np.isfinite(draw)
        conditional = draw[finite]
        rank = ranks[:completed, local_idx]
        q10 = quantile_or_none(conditional, 0.10)
        q50 = quantile_or_none(conditional, 0.50)
        q90 = quantile_or_none(conditional, 0.90)
        rows.append(
            {
                **works[int(global_idx)],
                "base_rank": base_rank.get(local_idx),
                "base_score": None
                if not np.isfinite(base_metric["score"][local_idx])
                else float(100.0 * base_metric["score"][local_idx]),
                "jury_boot_eligible_rate": float(np.mean(finite)),
                "jury_boot_top50_rate": float(np.mean((rank > 0) & (rank <= 50))),
                "jury_boot_top200_rate": float(np.mean((rank > 0) & (rank <= 200))),
                "jury_boot_score_mean": None
                if not len(conditional)
                else float(np.mean(conditional)),
                "jury_boot_score_sd": None
                if len(conditional) < 2
                else float(np.std(conditional, ddof=1)),
                "jury_boot_q10": q10,
                "jury_boot_q50": q50,
                "jury_boot_q90": q90,
                "jury_boot_u80": None
                if q10 is None or q90 is None
                else float((q90 - q10) / 2.0),
            }
        )
    rows.sort(
        key=lambda row: (
            row["base_rank"] is None,
            row["base_rank"] or 10**9,
        )
    )
    return rows


def write_report(results, report_path):
    jury = results["jury_stability"]
    lines = [
        "# Teacher-composition jury bootstrap",
        "",
        "## Design",
        "",
        "Each replicate Bayesian-bootstraps the positive teacher users, refits the five-fold "
        "rich behavioral jury model, selects a new 4,929-person jury within the fixed broad "
        "20,000, and reranks books using exact expected-inclusion pair votes.",
        "",
        f"- Mode: **{results['meta']['mode']}**; completed replicates: "
        f"**{results['meta']['completed_replicates']:,}**.",
        f"- Books tracked: **{results['meta']['n_candidates']:,}**; baseline exact rankable: "
        f"**{results['meta']['n_base_rankable']:,}**.",
        f"- Jury Jaccard q10/median/q90: **{jury['jaccard_q10']:.3f} / "
        f"{jury['jaccard_q50']:.3f} / {jury['jaccard_q90']:.3f}**.",
        "",
        "## Baseline top books under jury reconstruction uncertainty",
        "",
        "| book | baseline | jury q10–q90 | jury u80 | eligible | top200 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in results["books"]:
        if row["base_rank"] is None or row["base_rank"] > 80:
            continue
        interval = "—"
        u80 = "—"
        if row["jury_boot_q10"] is not None:
            interval = f"{row['jury_boot_q10']:.1f}–{row['jury_boot_q90']:.1f}"
            u80 = f"{row['jury_boot_u80']:.1f}"
        lines.append(
            f"| {row['title']} — {row['author']} | {row['base_rank']} "
            f"({row['base_score']:.1f}) | {interval} | {u80} | "
            f"{100*row['jury_boot_eligible_rate']:.0f}% | "
            f"{100*row['jury_boot_top200_rate']:.0f}% |"
        )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "- This isolates finite-teacher composition uncertainty. It does not bootstrap the "
        "choice of teacher definition, the broad 20,000-person pool, community learning, or "
        "missing exposure.",
        "- A book's interval is conditional on passing evidence gates; eligibility probability "
        "is reported separately.",
        "- Combine this component with the user-block campaign only after checking their "
        "dependence; do not automatically add interval widths.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    output = paths(args.mode)
    t_all = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, baseline_scores, broad = reconstruct_jury(con)
    ids, folds, y, teacher_w, x = fetch_frame(con)
    if not np.array_equal(ids, all_ids):
        raise RuntimeError("jury frame order differs from reconstructed score order")
    bins = activity_bins(x)
    con.execute("PRAGMA threads=8")
    broad_ids, baseline_mask, _ = materialize_pilot_users(
        con, all_ids, baseline_scores, broad
    )
    embedding, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(embedding, baseline_mask)
    positive, negative, works, eligible, pair_meta = build_expected_pair_matrices(
        con, len(broad_ids), current_only=False
    )
    baseline_counts = aggregate_counts(
        partitions, baseline_mask, positive, negative
    )
    baseline_full = aggregate_spec(baseline_counts, CENTRAL_SPEC, eligible)
    baseline_rows = np.flatnonzero(baseline_mask)
    expected_mass = np.asarray(
        positive[baseline_rows].sum(axis=0) + negative[baseline_rows].sum(axis=0)
    ).ravel()
    candidate_idx = np.flatnonzero(
        eligible
        & ((expected_mass >= NEAR_EVIDENCE_MASS) | baseline_full["estimable"])
    )
    if len(candidate_idx) >= np.iinfo(np.uint16).max:
        raise RuntimeError("candidate set too large for compact ranks")
    candidate_work_ids = [works[int(idx)]["work_id"] for idx in candidate_idx]
    positive = positive[:, candidate_idx].tocsr()
    negative = negative[:, candidate_idx].tocsr()
    candidate_eligible = eligible[candidate_idx]
    baseline_counts = aggregate_counts(
        partitions, baseline_mask, positive, negative
    )
    baseline_metric = aggregate_spec(
        baseline_counts, CENTRAL_SPEC, candidate_eligible
    )
    broad_frame_idx = np.searchsorted(ids, broad_ids)
    if not np.array_equal(ids[broad_frame_idx], broad_ids):
        raise RuntimeError("could not map broad jury users into feature frame")
    baseline_set = set(np.flatnonzero(baseline_mask).tolist())

    if args.resume:
        arrays = load_checkpoint(
            output["checkpoint"], candidate_work_ids, args.max_reps, len(broad_ids)
        )
        scores, ranks, jury_jaccard, selected_counts, coefficients, completed = arrays
    else:
        scores = np.full(
            (args.max_reps, len(candidate_idx)), np.nan, dtype=np.float32
        )
        ranks = np.zeros(
            (args.max_reps, len(candidate_idx)), dtype=np.uint16
        )
        jury_jaccard = np.full(args.max_reps, np.nan, dtype=np.float32)
        selected_counts = np.zeros(len(broad_ids), dtype=np.int32)
        coefficients = np.full(
            (args.max_reps, len(FEATURES)), np.nan, dtype=np.float32
        )
        completed = 0
    print(
        f"Starting jury bootstrap at {completed:,}; max={args.max_reps:,}; "
        f"wall budget={args.hours:.2f}h; candidates={len(candidate_idx):,}",
        flush=True,
    )
    boot_start = time.time()
    deadline = None if args.hours <= 0 else boot_start + args.hours * 3600
    positive_mask = y == 1
    while completed < args.max_reps:
        if deadline is not None and time.time() >= deadline:
            break
        rng = np.random.default_rng(BOOT_SEED + completed)
        multiplier = np.ones(len(y), dtype=np.float64)
        multiplier[positive_mask] = rng.exponential(1.0, size=int(positive_mask.sum()))
        model_score, coef = ridge_oof_teacher_bootstrap(
            x, y, teacher_w, folds, bins, multiplier
        )
        broad_score = model_score[broad_frame_idx]
        selected = np.argsort(-broad_score, kind="stable")[:JURY_N]
        jury_mask = np.zeros(len(broad_ids), dtype=bool)
        jury_mask[selected] = True
        intersection = len(set(selected.tolist()) & baseline_set)
        jury_jaccard[completed] = intersection / (2 * JURY_N - intersection)
        selected_counts[selected] += 1
        coefficients[completed] = coef.astype(np.float32)
        counts = aggregate_counts(partitions, jury_mask, positive, negative)
        metric = aggregate_spec(counts, CENTRAL_SPEC, candidate_eligible)
        eligible_draw = metric["eligible"]
        scores[completed, eligible_draw] = (
            100.0 * metric["score"][eligible_draw]
        ).astype(np.float32)
        for rank, idx in enumerate(metric["ranking"], start=1):
            ranks[completed, idx] = rank
        completed += 1
        if completed % 5 == 0 or completed == args.max_reps:
            save_checkpoint(
                output["checkpoint"],
                candidate_work_ids,
                scores,
                ranks,
                jury_jaccard,
                selected_counts,
                coefficients,
                completed,
            )
            elapsed = time.time() - boot_start
            status = {
                "mode": args.mode,
                "status": "running",
                "completed_replicates": completed,
                "max_replicates": args.max_reps,
                "bootstrap_elapsed_seconds": elapsed,
                "seconds_per_replicate": elapsed / max(completed, 1),
                "updated_unix": time.time(),
            }
            output["status"].write_text(
                json.dumps(status, indent=2) + "\n", encoding="utf-8"
            )
            print(
                f"  checkpoint {completed:,}: {elapsed/max(completed,1):.2f}s/rep; "
                f"median jury J={np.nanmedian(jury_jaccard[:completed]):.3f}",
                flush=True,
            )
    save_checkpoint(
        output["checkpoint"],
        candidate_work_ids,
        scores,
        ranks,
        jury_jaccard,
        selected_counts,
        coefficients,
        completed,
    )
    books = summarize_books(
        works, candidate_idx, baseline_metric, scores, ranks, completed
    )
    result = {
        "meta": {
            "purpose": "teacher-composition bootstrap of jury reconstruction and book ranking",
            "mode": args.mode,
            "completed_replicates": completed,
            "max_replicates": args.max_reps,
            "hours_budget": args.hours,
            "n_candidates": len(candidate_idx),
            "n_base_rankable": baseline_metric["n_rankable"],
            "runtime_seconds": time.time() - t_all,
            "bootstrap_seconds": time.time() - boot_start,
        },
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "pair_data": pair_meta,
        "jury_stability": {
            "jaccard_q10": float(np.quantile(jury_jaccard[:completed], 0.10)),
            "jaccard_q50": float(np.quantile(jury_jaccard[:completed], 0.50)),
            "jaccard_q90": float(np.quantile(jury_jaccard[:completed], 0.90)),
            "mean_member_selection_rate": float(
                np.mean(selected_counts / max(completed, 1))
            ),
        },
        "coefficient_stability": [
            {
                "feature": feature,
                "mean": float(np.mean(coefficients[:completed, idx])),
                "sd": float(np.std(coefficients[:completed, idx], ddof=1))
                if completed > 1
                else None,
                "positive_rate": float(
                    np.mean(coefficients[:completed, idx] > 0)
                ),
            }
            for idx, feature in enumerate(FEATURES)
        ],
        "books": books,
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

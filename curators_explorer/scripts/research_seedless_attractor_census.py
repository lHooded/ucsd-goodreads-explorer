#!/usr/bin/env python3
"""Census nonlinear ratings-only jury attractors from random starts.

This searches for self-consistent juries without literary or genre seeds.  A jury
weights readers; books receive degree-corrected signed support; readers are then
reweighted by agreement with those books.  Random starts expose multiple basins.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts import research_seedless_spectral_pilot as spectral


DATA = Path(__file__).resolve().parents[1] / "data"
MATRIX_CACHE = DATA / "seedless_spectral_pilot_matrix_b500.npz"

CONFIG = {
    **spectral.DEFAULTS,
    "min_book_n": 500,
    "degree_alpha": 1.0,
}


def load_payload() -> dict[str, np.ndarray]:
    with np.load(MATRIX_CACHE, allow_pickle=False) as saved:
        return {key: saved[key] for key in saved.files}


def normalize_columns(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=0, keepdims=True)
    return x / np.maximum(norm, 1e-20)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -12.0, 12.0)))


def initialize_juries(n_users: int, starts: int, seed: int) -> np.ndarray:
    """Sparse random cohorts plus their complements, all with mean weight one."""
    rng = np.random.default_rng(seed)
    juries = np.empty((n_users, starts), dtype=np.float32)
    paired = (starts + 1) // 2
    for j in range(paired):
        selected = rng.random(n_users) < 0.03
        weights = np.where(selected, 20.0, 0.4).astype(np.float32)
        weights /= weights.mean()
        juries[:, j] = weights
        complement = 2.0 - np.minimum(weights, 2.0)
        complement = np.maximum(complement, 0.05)
        complement /= complement.mean()
        if j + paired < starts:
            juries[:, j + paired] = complement
    return juries


def iterate_attractors(
    operator: spectral.ProjectedOperator,
    starts: int,
    iterations: int,
    beta: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, float]]]:
    weights = initialize_juries(operator.shape[0], starts, seed)
    previous_books = None
    history = []
    for iteration in range(iterations):
        raw_books = operator.rmatmat(weights)
        scale = np.sqrt(np.mean(raw_books**2, axis=0, keepdims=True))
        books = np.tanh(raw_books / np.maximum(1.5 * scale, 1e-12)).astype(np.float32)
        user_signal = operator.matmat(books)
        user_signal -= user_signal.mean(axis=0, keepdims=True)
        user_signal /= np.maximum(user_signal.std(axis=0, keepdims=True), 1e-12)
        target = sigmoid(beta * user_signal).astype(np.float32)
        target /= target.mean(axis=0, keepdims=True)
        weights = 0.35 * weights + 0.65 * target
        weights /= weights.mean(axis=0, keepdims=True)
        normalized_books = normalize_columns(raw_books)
        if previous_books is None:
            similarity = np.full(starts, np.nan)
        else:
            similarity = np.sum(previous_books * normalized_books, axis=0)
        previous_books = normalized_books
        history.append(
            {
                "iteration": iteration + 1,
                "mean_step_correlation": float(np.nanmean(similarity))
                if iteration
                else float("nan"),
                "q10_step_correlation": float(np.nanquantile(similarity, 0.10))
                if iteration
                else float("nan"),
                "q90_step_correlation": float(np.nanquantile(similarity, 0.90))
                if iteration
                else float("nan"),
                "mean_effective_user_share": float(
                    np.mean((weights.sum(axis=0) ** 2 / np.sum(weights**2, axis=0)) / weights.shape[0])
                ),
            }
        )
        print(
            f"iteration {iteration+1}/{iterations}: step corr "
            f"{history[-1]['mean_step_correlation']:.4f}",
            flush=True,
        )
    final_books = normalize_columns(operator.rmatmat(weights))
    return weights, final_books, history


def cluster_directions(book_vectors: np.ndarray, threshold: float) -> list[list[int]]:
    similarity = book_vectors.T @ book_vectors
    unassigned = set(range(book_vectors.shape[1]))
    clusters = []
    while unassigned:
        candidates = sorted(
            unassigned,
            key=lambda j: -sum(similarity[j, k] >= threshold for k in unassigned),
        )
        center = candidates[0]
        members = sorted(k for k in unassigned if similarity[center, k] >= threshold)
        clusters.append(members)
        unassigned.difference_update(members)
    return sorted(clusters, key=lambda members: (-len(members), members[0]))


def weighted_preferences(matrix: Any, weights: np.ndarray) -> dict[str, np.ndarray]:
    signed = np.asarray(matrix.T @ weights).ravel().astype(np.float64)
    absolute = np.asarray(abs(matrix).T @ weights).ravel().astype(np.float64)
    binary = matrix.copy()
    binary.data = np.ones_like(binary.data)
    reader_mass = np.asarray(binary.T @ weights).ravel().astype(np.float64)
    mean = np.divide(signed, absolute, out=np.zeros_like(signed), where=absolute > 0)
    reliability = reader_mass / (reader_mass + 25.0)
    return {"score": mean * reliability, "mean": mean, "reader_mass": reader_mass}


def posthoc_head(
    preference: dict[str, np.ndarray],
    work_ids: np.ndarray,
    meta: dict[str, dict[str, Any]],
    eval_sets: dict[str, Any],
    limit: int = 300,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    eligible = np.flatnonzero(preference["reader_mass"] >= 25)
    order = eligible[np.argsort(-preference["score"][eligible], kind="stable")][:limit]
    rows = []
    for rank, index in enumerate(order, 1):
        work_id = str(work_ids[index])
        book = meta.get(work_id, {})
        rows.append(
            {
                "rank": rank,
                "work_id": work_id,
                "title": book.get("title", work_id),
                "author": book.get("author", ""),
                "score": float(preference["score"][index]),
                "reader_mass": float(preference["reader_mass"][index]),
            }
        )
    metrics = {}
    for name in ("exact_lit", "broad_lit", "anti", "filler"):
        for k in (50, 200):
            metrics[f"{name}{k}"] = sum(
                row["work_id"] in eval_sets[name] for row in rows[:k]
            )
    return rows, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=32)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--beta", type=float, default=2.5)
    parser.add_argument("--seed", type=int, default=20260806)
    parser.add_argument("--cluster-threshold", type=float, default=0.92)
    parser.add_argument("--tag", default="full")
    args = parser.parse_args()
    t0 = time.time()
    payload = load_payload()
    matrix, matrix_meta = spectral.build_matrix(payload)
    operator, operator_meta = spectral.make_operator(matrix, payload, CONFIG)
    weights, book_vectors, history = iterate_attractors(
        operator, args.starts, args.iterations, args.beta, args.seed
    )
    clusters = cluster_directions(book_vectors, args.cluster_threshold)
    similarities = book_vectors.T @ book_vectors
    frozen = []
    for basin_id, members in enumerate(clusters, 1):
        centroid_weights = np.mean(weights[:, members], axis=1)
        preference = weighted_preferences(matrix, centroid_weights)
        frozen.append((basin_id, members, centroid_weights, preference))

    # Equal-basin center candidates. These are frozen before semantic context.
    basin_scores = np.stack([item[3]["score"] for item in frozen])
    basin_reader_mass = np.stack([item[3]["reader_mass"] for item in frozen])
    basin_mean = np.mean(basin_scores, axis=0)
    basin_sd = np.std(basin_scores, axis=0)
    consensus_preferences = {
        "equal_basin_mean": {
            "score": basin_mean,
            "mean": basin_mean,
            "reader_mass": np.min(basin_reader_mass, axis=0),
        },
        "equal_basin_q10": {
            "score": np.quantile(basin_scores, 0.10, axis=0),
            "mean": basin_mean,
            "reader_mass": np.min(basin_reader_mass, axis=0),
        },
        "equal_basin_mean_minus_sd": {
            "score": basin_mean - basin_sd,
            "mean": basin_mean,
            "reader_mass": np.min(basin_reader_mass, axis=0),
        },
    }

    # Semantic context is loaded only after every basin and book score is frozen.
    print("Loading post-hoc semantic context", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    basins = []
    for basin_id, members, centroid_weights, preference in frozen:
        rows, metrics = posthoc_head(
            preference, payload["work_ids"], meta, eval_sets
        )
        within = similarities[np.ix_(members, members)]
        basins.append(
            {
                "basin": basin_id,
                "starts": [int(x) for x in members],
                "size": len(members),
                "within_direction_correlation_mean": float(within.mean()),
                "effective_user_share": float(
                    (centroid_weights.sum() ** 2 / np.sum(centroid_weights**2))
                    / len(centroid_weights)
                ),
                "metrics": metrics,
                "head": rows,
            }
        )
    consensus_rankings = []
    for name, preference in consensus_preferences.items():
        rows, metrics = posthoc_head(
            preference, payload["work_ids"], meta, eval_sets, limit=500
        )
        consensus_rankings.append({"name": name, "metrics": metrics, "head": rows})
    result = {
        "method": {
            "purpose": "seedless nonlinear jury-attractor census",
            "allowed_discovery_columns": ["user_id", "work_id", "rating"],
            "semantic_data_loaded_after_scores_frozen": True,
            "starts": args.starts,
            "iterations": args.iterations,
            "beta": args.beta,
            "seed": args.seed,
            "cluster_threshold": args.cluster_threshold,
            "runtime_seconds": time.time() - t0,
        },
        "matrix": {**matrix_meta, "shape": list(matrix.shape)},
        "operator": operator_meta,
        "trajectory": history,
        "pairwise_final_direction_correlation": {
            "q05": float(np.quantile(similarities[np.triu_indices(args.starts, 1)], 0.05)),
            "median": float(np.median(similarities[np.triu_indices(args.starts, 1)])),
            "q95": float(np.quantile(similarities[np.triu_indices(args.starts, 1)], 0.95)),
        },
        "basins": basins,
        "consensus_rankings": consensus_rankings,
    }
    stem = f"seedless_attractor_census_{args.tag}"
    out_json = DATA / f"{stem}.json"
    out_report = DATA / f"{stem.upper()}_REPORT.md"
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Seedless nonlinear jury-attractor census",
        "",
        "Discovery used only `(user_id, work_id, rating)`. Random reader cohorts were iteratively "
        "reweighted by agreement with degree-corrected signed book support. Titles, authors, and "
        "evaluation lists were loaded only after convergence, basin clustering, and scoring.",
        "",
        f"Starts: **{args.starts}**; iterations: **{args.iterations}**; beta: **{args.beta}**; "
        f"basins at correlation ≥{args.cluster_threshold}: **{len(basins)}**; runtime: "
        f"**{result['method']['runtime_seconds']:.1f}s**.",
        "",
        "## Contraction trajectory",
        "",
        "| iteration | mean step corr | q10 | q90 | effective user share |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in history:
        lines.append(
            f"| {row['iteration']} | {row['mean_step_correlation']:.4f} | "
            f"{row['q10_step_correlation']:.4f} | {row['q90_step_correlation']:.4f} | "
            f"{row['mean_effective_user_share']:.3f} |"
        )
    lines += ["", "## Equal-basin center candidates", ""]
    for ranking in consensus_rankings:
        m = ranking["metrics"]
        lines += [
            f"### {ranking['name']}",
            "",
            f"Exact literary @50/200: **{m['exact_lit50']}/{m['exact_lit200']}**; broad "
            f"literary: **{m['broad_lit50']}/{m['broad_lit200']}**; anti: "
            f"**{m['anti50']}/{m['anti200']}**.",
            "",
        ]
        for row in ranking["head"][:30]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"({row['score']:.3f}; minimum basin reader mass={row['reader_mass']:.0f})"
            )
        lines.append("")
    lines += ["## Basins", ""]
    for basin in basins:
        m = basin["metrics"]
        lines += [
            f"### Basin {basin['basin']} ({basin['size']} starts)",
            "",
            f"Within-basin direction correlation: **{basin['within_direction_correlation_mean']:.3f}**; "
            f"effective reader share: **{basin['effective_user_share']:.3f}**; exact literary "
            f"@50/200: **{m['exact_lit50']}/{m['exact_lit200']}**; broad literary: "
            f"**{m['broad_lit50']}/{m['broad_lit200']}**; anti: "
            f"**{m['anti50']}/{m['anti200']}**.",
            "",
        ]
        for row in basin["head"][:20]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"({row['score']:.3f}; reader mass={row['reader_mass']:.0f})"
            )
        lines.append("")
    out_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_report}")


if __name__ == "__main__":
    main()

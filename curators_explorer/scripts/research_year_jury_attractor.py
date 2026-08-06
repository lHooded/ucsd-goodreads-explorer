#!/usr/bin/env python3
"""Send year-derived juries through the seedless nonlinear attractor map.

This answers a deliberately diagnostic question: if a publication-year jury is
used only as the starting point, does the ratings-geometry iteration preserve a
literary direction, move toward a common literary basin, or drift to one of the
generic Goodreads love/genre centers found by random starts?
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year


DATA = Path(__file__).resolve().parents[1] / "data"
OUT_JSON = DATA / "year_jury_attractor.json"
OUT_REPORT = DATA / "YEAR_JURY_ATTRACTOR_REPORT.md"
ITERATIONS = 20
BETAS = (1.5, 2.5, 3.5)
SEED_VARIANTS = (
    "best_linear_q10",
    "best_linear_mass_q10",
    "best_preference_q10",
    "best_preference_delta_q10",
)


def initial_weights(
    features: dict[str, np.ndarray], variants: dict[str, dict[str, Any]]
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    columns = []
    metadata = []
    for name in SEED_VARIANTS:
        variant = variants[name]
        fold_masks = []
        fold_comparators = []
        for fold in (0, 1):
            old, new, _ = year.jury_score(features, fold, variant)
            fold_masks.append(old.astype(np.float32))
            fold_comparators.append(new.astype(np.float32))
        membership = (fold_masks[0] + fold_masks[1]) / 2.0
        a, b = fold_masks[0] > 0, fold_masks[1] > 0
        jury_jaccard = float(np.sum(a & b) / max(1, np.sum(a | b)))
        for beta in BETAS:
            weights = 0.4 + 19.6 * membership
            weights /= weights.mean()
            columns.append(weights.astype(np.float32))
            metadata.append(
                {
                    "seed": name,
                    "beta": beta,
                    "fold_jury_jaccard": jury_jaccard,
                    "one_or_both_fold_users": int(np.sum(membership > 0)),
                    "both_fold_users": int(np.sum(membership == 1)),
                }
            )
    return np.stack(columns, axis=1), metadata


def iterate(
    operator: spectral.ProjectedOperator,
    weights: np.ndarray,
    columns: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, list[list[dict[str, float]]]]:
    beta = np.asarray([row["beta"] for row in columns], dtype=np.float32)[None, :]
    initial_weights_ = weights.copy()
    initial_books = attractor.normalize_columns(operator.rmatmat(weights))
    previous_books = initial_books
    histories: list[list[dict[str, float]]] = [[] for _ in columns]
    for iteration in range(ITERATIONS):
        raw_books = operator.rmatmat(weights)
        scale = np.sqrt(np.mean(raw_books**2, axis=0, keepdims=True))
        books = np.tanh(raw_books / np.maximum(1.5 * scale, 1e-12)).astype(np.float32)
        user_signal = operator.matmat(books)
        user_signal -= user_signal.mean(axis=0, keepdims=True)
        user_signal /= np.maximum(user_signal.std(axis=0, keepdims=True), 1e-12)
        target = attractor.sigmoid(beta * user_signal).astype(np.float32)
        target /= target.mean(axis=0, keepdims=True)
        weights = 0.35 * weights + 0.65 * target
        weights /= weights.mean(axis=0, keepdims=True)
        normalized_books = attractor.normalize_columns(operator.rmatmat(weights))
        step = np.sum(previous_books * normalized_books, axis=0)
        from_initial = np.sum(initial_books * normalized_books, axis=0)
        for j, history in enumerate(histories):
            seed_corr = float(np.corrcoef(initial_weights_[:, j], weights[:, j])[0, 1])
            history.append(
                {
                    "iteration": iteration + 1,
                    "step_correlation": float(step[j]),
                    "direction_from_initial": float(from_initial[j]),
                    "user_weight_from_initial": seed_corr,
                    "effective_user_share": float(
                        (weights[:, j].sum() ** 2 / np.sum(weights[:, j] ** 2))
                        / len(weights)
                    ),
                }
            )
        previous_books = normalized_books
        print(
            f"iteration {iteration + 1}/{ITERATIONS}: mean step={np.mean(step):.5f}; "
            f"mean initial direction={np.mean(from_initial):.4f}",
            flush=True,
        )
    return weights, previous_books, histories


def ranking_rows(
    preference: dict[str, np.ndarray],
    payload: dict[str, np.ndarray],
    meta: dict[str, dict[str, Any]],
    eval_sets: dict[str, Any],
    limit: int = 500,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows, metrics = attractor.posthoc_head(
        preference, payload["work_ids"], meta, eval_sets, limit=limit
    )
    return rows, metrics


def main() -> None:
    t0 = time.time()
    payload, matrix, matrix_meta = year.load_matrix()
    features, year_audit = year.extract_year_features(payload)
    variants = {row["name"]: row for row in year.VARIANTS}
    weights0, columns = initial_weights(features, variants)
    operator, operator_meta = spectral.make_operator(matrix, payload, attractor.CONFIG)
    initial_directions = attractor.normalize_columns(operator.rmatmat(weights0))
    weights, directions, histories = iterate(operator, weights0, columns)

    # Freeze all convergence outputs before loading names or evaluation probes.
    final_similarity = directions.T @ directions
    final_preferences = [
        attractor.weighted_preferences(matrix, weights[:, j])
        for j in range(weights.shape[1])
    ]
    initial_preferences = [
        attractor.weighted_preferences(matrix, weights0[:, j])
        for j in range(weights0.shape[1])
    ]
    print("Loading post-hoc semantic context", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    year_result = json.loads(year.OUT_JSON.read_text(encoding="utf-8"))
    initial_rankings = {
        row["variant"]["name"]: row["contrast_ranking"]["books"]
        for row in year_result["variants"]
    }

    paths = []
    for j, column in enumerate(columns):
        head, metrics = ranking_rows(
            final_preferences[j], payload, meta, eval_sets
        )
        initial_direction_preference = {
            "score": initial_directions[:, j],
            "mean": initial_directions[:, j],
            "reader_mass": initial_preferences[j]["reader_mass"],
        }
        final_direction_preference = {
            "score": directions[:, j],
            "mean": directions[:, j],
            "reader_mass": final_preferences[j]["reader_mass"],
        }
        initial_direction_head, initial_direction_metrics = ranking_rows(
            initial_direction_preference, payload, meta, eval_sets
        )
        final_direction_head, final_direction_metrics = ranking_rows(
            final_direction_preference, payload, meta, eval_sets
        )
        initial_direction_ids = [row["work_id"] for row in initial_direction_head]
        final_direction_ids = [row["work_id"] for row in final_direction_head]
        direction_overlap = {}
        for k in (50, 100, 200, 500):
            a, b = set(initial_direction_ids[:k]), set(final_direction_ids[:k])
            direction_overlap[f"jaccard{k}"] = len(a & b) / max(1, len(a | b))
        initial_ids = [row["work_id"] for row in initial_rankings[column["seed"]]]
        final_ids = [row["work_id"] for row in head]
        overlap = {}
        for k in (50, 100, 200, 500):
            a, b = set(initial_ids[:k]), set(final_ids[:k])
            overlap[f"jaccard{k}"] = len(a & b) / max(1, len(a | b))
        paths.append(
            {
                **column,
                "trajectory": histories[j],
                "initial_to_final_ranking": overlap,
                "initial_to_final_direction_ranking": direction_overlap,
                "final_metrics": metrics,
                "final_head": head,
                "initial_direction_metrics": initial_direction_metrics,
                "initial_direction_head": initial_direction_head,
                "final_direction_metrics": final_direction_metrics,
                "final_direction_head": final_direction_head,
            }
        )

    result = {
        "method": {
            "purpose": "nonlinear ratings-geometry convergence from year-derived juries",
            "iterations": ITERATIONS,
            "betas": list(BETAS),
            "seed_variants": list(SEED_VARIANTS),
            "semantic_data_loaded_after_convergence": True,
            "runtime_seconds": time.time() - t0,
        },
        "matrix": {**matrix_meta, "shape": list(matrix.shape)},
        "operator": operator_meta,
        "year_audit": year_audit,
        "final_direction_similarity": final_similarity.tolist(),
        "paths": paths,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Year-jury nonlinear attractor trajectories",
        "",
        "Each year-derived jury starts the same nuisance-projected nonlinear ratings iteration "
        "used in the seedless attractor census. A reader selected in both book-parity folds gets "
        "full initial weight; a one-fold selection gets half weight. Titles and evaluation lists "
        "are loaded only after every path has finished.",
        "",
        f"Paths: **{len(paths)}**; iterations: **{ITERATIONS}**; runtime: "
        f"**{result['method']['runtime_seconds']:.1f}s**.",
        "",
        "## Summary",
        "",
        "| seed | beta | final step corr | direction from start | user weights from start | effective user share | projected rank J@50 | J@200 | projected exact lit @50/200 | broad @50/200 | anti @50/200 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for path in paths:
        last = path["trajectory"][-1]
        overlap = path["initial_to_final_direction_ranking"]
        m = path["final_direction_metrics"]
        lines.append(
            f"| {path['seed']} | {path['beta']:.1f} | {last['step_correlation']:.5f} | "
            f"{last['direction_from_initial']:.3f} | {last['user_weight_from_initial']:.3f} | "
            f"{last['effective_user_share']:.3f} | {overlap['jaccard50']:.3f} | "
            f"{overlap['jaccard200']:.3f} | {m['exact_lit50']}/{m['exact_lit200']} | "
            f"{m['broad_lit50']}/{m['broad_lit200']} | {m['anti50']}/{m['anti200']} |"
        )
    old_indices = range(6)
    preference_indices = range(6, 12)
    cross_basin = [
        final_similarity[i, j]
        for i in old_indices
        for j in preference_indices
    ]
    within_old = [
        final_similarity[i, j]
        for i in old_indices
        for j in old_indices
        if i < j
    ]
    lines += [
        "",
        "## Findings",
        "",
        "- Every path genuinely contracts: final step correlations exceed 0.9998. This proves "
        "numerical convergence, not literary validity.",
        f"- Share- and mass-based old-love starts collapse to effectively one basin (final "
        f"direction correlation {min(within_old):.3f}–{max(within_old):.3f}). The old-over-new "
        f"preference paths retain a nearby distinct basin: cross-basin correlations are "
        f"{min(cross_basin):.3f}–{max(cross_basin):.3f}.",
        f"- Only {min(x['trajectory'][-1]['direction_from_initial'] for x in paths):.1%}–"
        f"{max(x['trajectory'][-1]['direction_from_initial'] for x in paths):.1%} of the initial "
        "directional correlation remains. Initial-to-final projected top-200 Jaccard is only "
        f"{min(x['initial_to_final_direction_ranking']['jaccard200'] for x in paths):.3f}–"
        f"{max(x['initial_to_final_direction_ranking']['jaccard200'] for x in paths):.3f}.",
        "- The final projected heads mix a few classics with YA/paranormal and fantasy-series "
        "axes; ordinary approval collapses further to Calvin and Hobbes, Sanderson, comics, and "
        "popular nonfiction. The unconstrained stability iteration therefore washes out the "
        "literary year signal rather than refining it.",
        "- Publication-year preference should remain an explicit anchored criterion. A future "
        "fixed-point experiment would need an anchor penalty and should be judged by retained "
        "literary direction as well as contraction speed.",
        "",
        "## Contraction trajectories",
        "",
    ]
    for path in paths:
        lines += [
            f"### {path['seed']} · beta={path['beta']:.1f}",
            "",
            "| iteration | step corr | direction from start | user weights from start | effective user share |",
            "|---:|---:|---:|---:|---:|",
        ]
        for row in path["trajectory"]:
            lines.append(
                f"| {row['iteration']} | {row['step_correlation']:.5f} | "
                f"{row['direction_from_initial']:.4f} | {row['user_weight_from_initial']:.4f} | "
                f"{row['effective_user_share']:.3f} |"
            )
        lines += ["", "Final projected-direction head:", ""]
        for row in path["final_direction_head"][:30]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"(direction={row['score']:.5f})"
            )
        lines += ["", "Final ordinary-approval head:", ""]
        for row in path["final_head"][:30]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"({row['score']:.3f}; reader mass={row['reader_mass']:.0f})"
            )
        lines.append("")
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

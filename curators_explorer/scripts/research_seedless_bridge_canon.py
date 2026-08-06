#!/usr/bin/env python3
"""Seedless bridge-reader canon pilot.

Fit a ratings-only spectral taste subspace, then identify readers whose five-star
books span that subspace rather than remaining directionally concentrated.  No
title, author, list, or semantic flag is loaded until rankings are frozen.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from curators_explorer.scripts import research_seedless_spectral_pilot as spectral


DATA = Path(__file__).resolve().parents[1] / "data"
MATRIX_CACHE = DATA / "seedless_spectral_pilot_matrix_b500.npz"
OUT_JSON = DATA / "seedless_bridge_canon_pilot.json"
OUT_REPORT = DATA / "SEEDLESS_BRIDGE_CANON_PILOT_REPORT.md"

CONFIG = {
    **spectral.DEFAULTS,
    "min_book_n": 500,
    "rank": 16,
    "oversample": 8,
    "power_iters": 8,
}
SUBSPACE_MODES = 8
COHORT_QUANTILE = 0.90
SHRINK_READERS = 25.0


def load_payload() -> dict[str, np.ndarray]:
    with np.load(MATRIX_CACHE, allow_pickle=False) as saved:
        payload = {key: saved[key] for key in saved.files}
    cached = json.loads(str(payload["config_json"]))
    wanted = spectral.extraction_config(CONFIG)
    if {key: cached.get(key) for key in spectral.EXTRACTION_KEYS} != wanted:
        raise RuntimeError(f"Cache extraction settings do not match: {cached} != {wanted}")
    return payload


def bridge_statistics(
    matrix: Any,
    book_vectors: np.ndarray,
) -> dict[str, np.ndarray | float]:
    """Rotation-invariant directional dispersion of each user's positive books."""
    embedding = np.asarray(book_vectors[:SUBSPACE_MODES].T, dtype=np.float64)
    book_norm = np.linalg.norm(embedding, axis=1)
    coo = matrix.tocoo(copy=False)
    positive = coo.data > 0
    rows = coo.row[positive]
    cols = coo.col[positive]
    n_users = matrix.shape[0]
    count = np.bincount(rows, minlength=n_users).astype(np.float64)
    norm_sum = np.bincount(rows, weights=book_norm[cols], minlength=n_users)
    vector_sum = np.empty((n_users, SUBSPACE_MODES), dtype=np.float64)
    for j in range(SUBSPACE_MODES):
        vector_sum[:, j] = np.bincount(
            rows, weights=embedding[cols, j], minlength=n_users
        )
    coherence = np.sum(vector_sum**2, axis=1) / np.maximum(norm_sum**2, 1e-30)
    dispersion = np.clip(1.0 - coherence, 0.0, 1.0)
    strength = norm_sum / np.maximum(count, 1.0)
    valid = (count >= 4) & np.isfinite(strength) & (strength > 0)
    median_strength = float(np.median(strength[valid]))
    scaled_strength = np.sqrt(np.clip(strength / median_strength, 0.0, 9.0))
    bridge_metric = dispersion * scaled_strength
    specialist_metric = coherence * scaled_strength
    bridge_cut = float(np.quantile(bridge_metric[valid], COHORT_QUANTILE))
    specialist_cut = float(np.quantile(specialist_metric[valid], COHORT_QUANTILE))
    return {
        "count": count,
        "dispersion": dispersion,
        "strength": strength,
        "bridge_metric": bridge_metric,
        "specialist_metric": specialist_metric,
        "bridge": valid & (bridge_metric >= bridge_cut),
        "specialist": valid & (specialist_metric >= specialist_cut),
        "median_strength": median_strength,
        "bridge_cut": bridge_cut,
        "specialist_cut": specialist_cut,
    }


def preference_score(matrix: Any, cohort: np.ndarray) -> dict[str, np.ndarray]:
    weight = cohort.astype(np.float32)
    signed = np.asarray(matrix.T @ weight).ravel().astype(np.float64)
    absolute = np.asarray(abs(matrix).T @ weight).ravel().astype(np.float64)
    binary = matrix.copy()
    binary.data = np.ones_like(binary.data)
    readers = np.asarray(binary.T @ weight).ravel().astype(np.float64)
    mean = np.divide(signed, absolute, out=np.zeros_like(signed), where=absolute > 0)
    reliability = readers / (readers + SHRINK_READERS)
    score = mean * reliability
    uncertainty = np.sqrt(np.maximum(1.0 - mean**2, 1e-6) / np.maximum(readers, 1.0))
    return {
        "score": score,
        "mean": mean,
        "readers": readers,
        "uncertainty": uncertainty,
    }


def exposure_enrichment(
    matrix: Any, cohort: np.ndarray, prior_readers: float = 50.0
) -> dict[str, np.ndarray]:
    """Book exposure enrichment over the cohort's population share."""
    binary = matrix.copy()
    binary.data = np.ones_like(binary.data)
    cohort_count = np.asarray(binary.T @ cohort.astype(np.float32)).ravel().astype(np.float64)
    all_count = np.asarray(binary.getnnz(axis=0)).ravel().astype(np.float64)
    base = float(np.mean(cohort))
    posterior = (cohort_count + prior_readers * base) / (all_count + prior_readers)
    eps = 1e-8
    score = np.log((posterior + eps) / (1.0 - posterior + eps)) - math.log(
        base / (1.0 - base)
    )
    uncertainty = np.sqrt(
        1.0 / np.maximum(cohort_count + prior_readers * base, 1.0)
        + 1.0
        / np.maximum(
            all_count - cohort_count + prior_readers * (1.0 - base), 1.0
        )
    )
    return {
        "score": score,
        "mean": posterior - base,
        "readers": all_count,
        "uncertainty": uncertainty,
    }


def rank_order(score: np.ndarray, readers: np.ndarray, minimum: int = 25) -> np.ndarray:
    eligible = np.flatnonzero(readers >= minimum)
    return eligible[np.argsort(-score[eligible], kind="stable")]


def ranking_stability(
    full: dict[str, np.ndarray],
    halves: list[dict[str, np.ndarray]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    full_order = rank_order(full["score"], full["readers"])
    for label, half in enumerate(halves):
        half_order = rank_order(half["score"], half["readers"], minimum=12)
        rows: dict[str, float] = {}
        for k in (50, 100, 200, 500):
            a, b = set(full_order[:k].tolist()), set(half_order[:k].tolist())
            rows[f"jaccard{k}"] = len(a & b) / max(1, len(a | b))
        common = (full["readers"] >= 25) & (half["readers"] >= 12)
        rows["score_spearman"] = float(
            spearmanr(full["score"][common], half["score"][common]).statistic
        )
        rows["common_books"] = int(common.sum())
        result[f"half{label}"] = rows
    return result


def fit_partition(
    matrix: Any,
    payload: dict[str, np.ndarray],
    user_indices: np.ndarray | None,
    seed: int,
    label: str,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray | float]]:
    operator, _ = spectral.make_operator(matrix, payload, CONFIG, user_indices)
    fit = spectral.randomized_svd(
        operator,
        CONFIG["rank"],
        CONFIG["oversample"],
        CONFIG["power_iters"],
        seed,
        label,
    )
    bridge = bridge_statistics(matrix, fit["v"])
    return fit, bridge


def metric_summary(values: np.ndarray, valid: np.ndarray) -> dict[str, float]:
    return {
        "q05": float(np.quantile(values[valid], 0.05)),
        "q25": float(np.quantile(values[valid], 0.25)),
        "median": float(np.quantile(values[valid], 0.50)),
        "q75": float(np.quantile(values[valid], 0.75)),
        "q95": float(np.quantile(values[valid], 0.95)),
    }


def posthoc_ranking(
    name: str,
    values: dict[str, np.ndarray],
    work_ids: np.ndarray,
    meta: dict[str, dict[str, Any]],
    eval_sets: dict[str, Any],
    limit: int = 500,
) -> dict[str, Any]:
    order = rank_order(values["score"], values["readers"])[:limit]
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
                "score": float(values["score"][index]),
                "raw_preference": float(values["mean"][index]),
                "sampled_readers": int(values["readers"][index]),
                "uncertainty": float(values["uncertainty"][index]),
            }
        )
    metrics = {}
    for target_name in ("exact_lit", "broad_lit", "anti", "filler"):
        target = eval_sets[target_name]
        for k in (50, 200, 500):
            metrics[f"{target_name}{k}"] = sum(
                row["work_id"] in target for row in rows[:k]
            )
    return {"name": name, "metrics": metrics, "books": rows}


def main() -> None:
    t0 = time.time()
    payload = load_payload()
    matrix, matrix_meta = spectral.build_matrix(payload)
    print(f"Loaded {matrix.shape} matrix with {matrix.nnz:,} edges", flush=True)

    full_fit, full_bridge = fit_partition(matrix, payload, None, 311, "bridge-full")
    cohorts: dict[str, dict[str, np.ndarray]] = {
        "bridge": preference_score(matrix, np.asarray(full_bridge["bridge"])),
        "specialist": preference_score(matrix, np.asarray(full_bridge["specialist"])),
        "all_eligible": preference_score(matrix, np.ones(matrix.shape[0], dtype=bool)),
        "bridge_exposure": exposure_enrichment(
            matrix, np.asarray(full_bridge["bridge"])
        ),
        "specialist_exposure": exposure_enrichment(
            matrix, np.asarray(full_bridge["specialist"])
        ),
    }
    contrast = cohorts["bridge"]["score"] - cohorts["specialist"]["score"]
    contrast_readers = np.minimum(
        cohorts["bridge"]["readers"], cohorts["specialist"]["readers"]
    )
    cohorts["bridge_minus_specialist"] = {
        "score": contrast,
        "mean": contrast,
        "readers": contrast_readers,
        "uncertainty": np.sqrt(
            cohorts["bridge"]["uncertainty"] ** 2
            + cohorts["specialist"]["uncertainty"] ** 2
        ),
    }

    half_cohorts: dict[str, list[dict[str, np.ndarray]]] = {
        key: [] for key in cohorts
    }
    half_meta = []
    for parity in (0, 1):
        indices = np.flatnonzero((payload["user_ids"] % 2) == parity)
        half_matrix = matrix[indices].tocsr()
        fit, bridge = fit_partition(
            half_matrix, payload, indices, 411 + parity, f"bridge-half{parity}"
        )
        bridge_score = preference_score(half_matrix, np.asarray(bridge["bridge"]))
        specialist_score = preference_score(half_matrix, np.asarray(bridge["specialist"]))
        all_score = preference_score(
            half_matrix, np.ones(half_matrix.shape[0], dtype=bool)
        )
        half_cohorts["bridge"].append(bridge_score)
        half_cohorts["specialist"].append(specialist_score)
        half_cohorts["all_eligible"].append(all_score)
        half_cohorts["bridge_exposure"].append(
            exposure_enrichment(half_matrix, np.asarray(bridge["bridge"]))
        )
        half_cohorts["specialist_exposure"].append(
            exposure_enrichment(half_matrix, np.asarray(bridge["specialist"]))
        )
        half_cohorts["bridge_minus_specialist"].append(
            {
                "score": bridge_score["score"] - specialist_score["score"],
                "mean": bridge_score["score"] - specialist_score["score"],
                "readers": np.minimum(
                    bridge_score["readers"], specialist_score["readers"]
                ),
                "uncertainty": np.sqrt(
                    bridge_score["uncertainty"] ** 2
                    + specialist_score["uncertainty"] ** 2
                ),
            }
        )
        half_meta.append(
            {
                "parity": parity,
                "users": len(indices),
                "bridge_users": int(np.sum(bridge["bridge"])),
                "specialist_users": int(np.sum(bridge["specialist"])),
                "subspace_alignment_to_full": spectral.subspace_alignment(
                    full_fit["v"], fit["v"], cuts=(1, 2, 4, 6, 8, 12, 16)
                ),
            }
        )

    # Freeze every ratings-only score before opening title or semantic data.
    stability = {
        name: ranking_stability(values, half_cohorts[name])
        for name, values in cohorts.items()
    }
    valid = np.asarray(full_bridge["count"]) >= 4
    discovery_summary = {
        "matrix": {**matrix_meta, "shape": list(matrix.shape)},
        "config": CONFIG,
        "subspace_modes": SUBSPACE_MODES,
        "cohort_quantile": COHORT_QUANTILE,
        "bridge_users": int(np.sum(full_bridge["bridge"])),
        "specialist_users": int(np.sum(full_bridge["specialist"])),
        "dispersion_quantiles": metric_summary(
            np.asarray(full_bridge["dispersion"]), valid
        ),
        "strength_quantiles": metric_summary(
            np.asarray(full_bridge["strength"]), valid
        ),
        "half_fits": half_meta,
        "ranking_stability": stability,
    }

    print("Loading post-hoc titles and lists after rankings are frozen", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    rankings = [
        posthoc_ranking(name, values, payload["work_ids"], meta, eval_sets)
        for name, values in cohorts.items()
    ]
    result = {
        "method": {
            "purpose": "rotation-invariant seedless bridge-reader canon pilot",
            "allowed_discovery_columns": ["user_id", "work_id", "rating"],
            "semantic_data_loaded_after_scores_frozen": True,
            "runtime_seconds": time.time() - t0,
        },
        "discovery": discovery_summary,
        "evaluation": {
            "exact_lit_candidates": len(eval_sets["exact_lit"]),
            "broad_lit_candidates": len(
                eval_sets["broad_lit"] & set(payload["work_ids"].tolist())
            ),
        },
        "rankings": rankings,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Seedless bridge-reader canon pilot",
        "",
        "## Design",
        "",
        "Discovery used only `(user_id, work_id, rating)`. A reader's bridge score is the "
        "directional dispersion of their sampled five-star books inside the leading stable "
        "ratings-only taste subspace, multiplied by structural signal strength. It is invariant "
        "to rotations of tied spectral modes. The top 10% form the bridge cohort; the top 10% "
        "by directional concentration form the specialist cohort.",
        "",
        f"Matrix: **{matrix.shape[0]:,} readers × {matrix.shape[1]:,} works**; "
        f"bridge readers: **{discovery_summary['bridge_users']:,}**; specialist readers: "
        f"**{discovery_summary['specialist_users']:,}**; runtime: "
        f"**{result['method']['runtime_seconds']:.1f}s**.",
        "",
        "Titles, authors, and literary/anti lists were loaded only after cohort membership, "
        "book scores, and half-sample stability were frozen.",
        "",
        "## Ranking stability",
        "",
        "| ranking | half | score Spearman | J@50 | J@100 | J@200 | J@500 | common books |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, halves in stability.items():
        for half_name, row in halves.items():
            lines.append(
                f"| {name} | {half_name[-1]} | {row['score_spearman']:.3f} | "
                f"{row['jaccard50']:.3f} | {row['jaccard100']:.3f} | "
                f"{row['jaccard200']:.3f} | {row['jaccard500']:.3f} | "
                f"{row['common_books']:,} |"
            )
    lines += ["", "## Post-hoc evaluation", ""]
    for ranking in rankings:
        metrics = ranking["metrics"]
        lines += [
            f"### {ranking['name']}",
            "",
            f"Exact literary seed overlap @50/200/500: **{metrics['exact_lit50']} / "
            f"{metrics['exact_lit200']} / {metrics['exact_lit500']}**. Broad literary "
            f"overlap: **{metrics['broad_lit50']} / {metrics['broad_lit200']} / "
            f"{metrics['broad_lit500']}**. Anti overlap: **{metrics['anti50']} / "
            f"{metrics['anti200']} / {metrics['anti500']}**.",
            "",
        ]
        for row in ranking["books"][:30]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"({row['score']:.3f} ± {row['uncertainty']:.3f}; "
                f"sample readers={row['sampled_readers']:,})"
            )
        lines.append("")
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

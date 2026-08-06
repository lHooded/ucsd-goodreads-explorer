#!/usr/bin/env python3
"""Approximate ratings-only book contributions to bipartite nestedness.

For uniformly weighted, activity-stratified anchor books, measure whether a
book's audience overlap exceeds a bipartite configuration expectation, scaled
by the smaller audience. Independent anchor panels provide uncertainty and a
stability test. Semantic context is loaded only after all scores are frozen.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.sparse import coo_matrix
from scipy.stats import spearmanr

from curators_explorer.scripts import research_seedless_spectral_pilot as spectral


DATA = Path(__file__).resolve().parents[1] / "data"
CACHE = DATA / "seedless_spectral_pilot_matrix_b500.npz"
FULL_CACHE = DATA / "seedless_nestedness_full_incidence_matrix.npz"
OUT_JSON = DATA / "seedless_nestedness_contribution_pilot.json"
OUT_REPORT = DATA / "SEEDLESS_NESTEDNESS_CONTRIBUTION_PILOT_REPORT.md"

PANELS = 4
ANCHORS_PER_PANEL = 512
BATCH = 64
SEED = 20260806
FULL_USERS = 120_000


def load_or_build_full_incidence() -> tuple[dict[str, np.ndarray], Any, dict[str, Any]]:
    if FULL_CACHE.exists():
        with np.load(FULL_CACHE, allow_pickle=False) as saved:
            payload = {key: saved[key] for key in saved.files}
        matrix = coo_matrix(
            (
                np.ones(len(payload["row"]), dtype=np.float32),
                (payload["row"], payload["col"]),
            ),
            shape=(len(payload["user_ids"]), len(payload["work_ids"])),
        ).tocsr()
        matrix.sum_duplicates()
        matrix.data[:] = 1.0
        print(f"Loaded full-incidence cache {FULL_CACHE}", flush=True)
        return payload, matrix, {"sampled_edges": int(matrix.nnz), "source": FULL_CACHE.name}

    con = spectral.extraction_connection()
    print("Building complete-incidence user sample", flush=True)
    con.execute(
        """
        CREATE TEMP TABLE eligible_books AS
        SELECT (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS bi, work_id
        FROM (
            SELECT work_id
            FROM ex.all_rating_events
            WHERE rating > 0
            GROUP BY work_id
            HAVING count(*) >= 500
        )
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE sampled_users AS
        SELECT (row_number() OVER (ORDER BY user_id)-1)::INTEGER AS ui, user_id
        FROM (
            SELECT e.user_id
            FROM ex.all_rating_events e
            JOIN eligible_books b USING (work_id)
            WHERE e.rating > 0
            GROUP BY e.user_id
            HAVING count(DISTINCT e.work_id) >= 5
            ORDER BY hash(e.user_id, {SEED})
            LIMIT {FULL_USERS}
        )
        """
    )
    users = con.execute("SELECT ui,user_id FROM sampled_users ORDER BY ui").fetchnumpy()
    books = con.execute("SELECT bi,work_id FROM eligible_books ORDER BY bi").fetchnumpy()
    edges = con.execute(
        """
        SELECT DISTINCT u.ui,b.bi
        FROM ex.all_rating_events e
        JOIN sampled_users u USING (user_id)
        JOIN eligible_books b USING (work_id)
        WHERE e.rating > 0
        ORDER BY u.ui,b.bi
        """
    ).fetchnumpy()
    con.close()
    payload = {
        "row": spectral.clean_array(edges["ui"], np.int32),
        "col": spectral.clean_array(edges["bi"], np.int32),
        "user_ids": spectral.clean_array(users["user_id"], np.int64),
        "work_ids": np.asarray(books["work_id"], dtype=str),
    }
    matrix = coo_matrix(
        (
            np.ones(len(payload["row"]), dtype=np.float32),
            (payload["row"], payload["col"]),
        ),
        shape=(len(payload["user_ids"]), len(payload["work_ids"])),
    ).tocsr()
    matrix.sum_duplicates()
    matrix.data[:] = 1.0
    np.savez_compressed(FULL_CACHE, **payload)
    print(
        f"Wrote {FULL_CACHE} ({FULL_CACHE.stat().st_size/2**20:.1f} MiB)", flush=True
    )
    return payload, matrix, {"sampled_edges": int(matrix.nnz), "source": FULL_CACHE.name}


def stratified_anchors(degree: np.ndarray, count: int, rng: np.random.Generator) -> np.ndarray:
    positive = np.flatnonzero(degree > 0)
    order = positive[np.argsort(degree[positive], kind="stable")]
    strata = np.array_split(order, count)
    return np.asarray([rng.choice(group) for group in strata if len(group)], dtype=np.int32)


def panel_contribution(
    binary: Any,
    degree: np.ndarray,
    anchors: np.ndarray,
    configuration_constant: float,
) -> dict[str, np.ndarray]:
    n_books = binary.shape[1]
    total = np.zeros(n_books, dtype=np.float64)
    total_sq = np.zeros(n_books, dtype=np.float64)
    positive = np.zeros(n_books, dtype=np.float64)
    comparisons = np.zeros(n_books, dtype=np.int32)
    for start in range(0, len(anchors), BATCH):
        selected = anchors[start : start + BATCH]
        overlap = (binary.T @ binary[:, selected]).toarray().astype(np.float64)
        anchor_degree = degree[selected][None, :]
        focal_degree = degree[:, None]
        smaller = np.minimum(focal_degree, anchor_degree)
        larger = np.maximum(focal_degree, anchor_degree)
        valid = (smaller > 0) & (larger >= 1.02 * smaller)
        observed = overlap / np.maximum(smaller, 1.0)
        expected = configuration_constant * larger
        residual = observed - expected
        for offset, anchor in enumerate(selected):
            valid[anchor, offset] = False
        residual[~valid] = 0.0
        total += residual.sum(axis=1)
        total_sq += (residual**2).sum(axis=1)
        positive += ((residual > 0) & valid).sum(axis=1)
        comparisons += valid.sum(axis=1)
    mean = np.divide(total, comparisons, out=np.zeros_like(total), where=comparisons > 0)
    variance = np.divide(total_sq, comparisons, out=np.zeros_like(total_sq), where=comparisons > 0) - mean**2
    uncertainty = np.sqrt(np.maximum(variance, 0.0) / np.maximum(comparisons, 1))
    positive_share = np.divide(
        positive, comparisons, out=np.zeros_like(positive), where=comparisons > 0
    )
    return {
        "score": mean,
        "uncertainty": uncertainty,
        "positive_share": positive_share,
        "comparisons": comparisons,
    }


def order(score: np.ndarray, comparisons: np.ndarray, minimum: int = 400) -> np.ndarray:
    eligible = np.flatnonzero(comparisons >= minimum)
    return eligible[np.argsort(-score[eligible], kind="stable")]


def stability(reference: dict[str, np.ndarray], other: dict[str, np.ndarray]) -> dict[str, float]:
    a = order(reference["score"], reference["comparisons"])
    b = order(other["score"], other["comparisons"])
    result = {}
    for k in (50, 100, 200, 500):
        aa, bb = set(a[:k].tolist()), set(b[:k].tolist())
        result[f"jaccard{k}"] = len(aa & bb) / max(1, len(aa | bb))
    valid = (reference["comparisons"] >= 400) & (other["comparisons"] >= 400)
    result["spearman"] = float(
        spearmanr(reference["score"][valid], other["score"][valid]).statistic
    )
    return result


def posthoc_rows(
    score: dict[str, np.ndarray],
    work_ids: np.ndarray,
    meta: dict[str, dict[str, Any]],
    eval_sets: dict[str, Any],
    limit: int = 500,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    ranking = order(score["score"], score["comparisons"])[:limit]
    rows = []
    for rank, index in enumerate(ranking, 1):
        work_id = str(work_ids[index])
        book = meta.get(work_id, {})
        rows.append(
            {
                "rank": rank,
                "work_id": work_id,
                "title": book.get("title", work_id),
                "author": book.get("author", ""),
                "score": float(score["score"][index]),
                "uncertainty": float(score["uncertainty"][index]),
                "positive_share": float(score["positive_share"][index]),
                "sampled_degree": int(score["degree"][index]),
            }
        )
    metrics = {}
    for name in ("exact_lit", "broad_lit", "anti", "filler"):
        for k in (50, 200, 500):
            metrics[f"{name}{k}"] = sum(
                row["work_id"] in eval_sets[name] for row in rows[:k]
            )
    return rows, metrics


def main() -> None:
    global OUT_JSON, OUT_REPORT
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-incidence", action="store_true")
    args = parser.parse_args()
    t0 = time.time()
    if args.full_incidence:
        payload, binary, matrix_meta = load_or_build_full_incidence()
        OUT_JSON = DATA / "seedless_nestedness_contribution_full_incidence.json"
        OUT_REPORT = DATA / "SEEDLESS_NESTEDNESS_CONTRIBUTION_FULL_INCIDENCE_REPORT.md"
    else:
        with np.load(CACHE, allow_pickle=False) as saved:
            payload = {key: saved[key] for key in saved.files}
        matrix, matrix_meta = spectral.build_matrix(payload)
        binary = matrix.copy().astype(np.float32)
        binary.data = np.ones_like(binary.data)
    degree = np.asarray(binary.getnnz(axis=0)).ravel().astype(np.float64)
    row_degree = np.asarray(binary.getnnz(axis=1)).ravel().astype(np.float64)
    edges = float(binary.nnz)
    configuration_constant = float(
        np.sum(row_degree * np.maximum(row_degree - 1.0, 0.0))
        / max(edges * (edges - 1.0), 1.0)
    )
    print(
        f"Matrix {binary.shape}, {binary.nnz:,} edges; configuration C={configuration_constant:.3e}",
        flush=True,
    )
    rng = np.random.default_rng(SEED)
    panels = []
    for panel in range(PANELS):
        anchors = stratified_anchors(degree, ANCHORS_PER_PANEL, rng)
        print(f"panel {panel+1}/{PANELS}: {len(anchors)} anchors", flush=True)
        panels.append(panel_contribution(binary, degree, anchors, configuration_constant))

    scores = np.stack([panel["score"] for panel in panels])
    combined = {
        "score": scores.mean(axis=0),
        "uncertainty": scores.std(axis=0, ddof=1) / math.sqrt(PANELS),
        "positive_share": np.mean(
            np.stack([panel["positive_share"] for panel in panels]), axis=0
        ),
        "comparisons": np.min(
            np.stack([panel["comparisons"] for panel in panels]), axis=0
        ),
        "degree": degree,
    }
    panel_stability = [stability(combined, panel) for panel in panels]

    # Scores and stability are frozen before any title/list context is loaded.
    print("Loading post-hoc semantic context", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    rows, metrics = posthoc_rows(combined, payload["work_ids"], meta, eval_sets)
    result = {
        "method": {
            "purpose": "seedless approximate item nestedness contribution",
            "allowed_discovery_columns": ["user_id", "work_id", "rating"],
            "semantic_data_loaded_after_scores_frozen": True,
            "panels": PANELS,
            "anchors_per_panel": ANCHORS_PER_PANEL,
            "configuration_constant": configuration_constant,
            "complete_user_collections": bool(args.full_incidence),
            "runtime_seconds": time.time() - t0,
        },
        "matrix": {**matrix_meta, "shape": list(binary.shape)},
        "panel_stability": panel_stability,
        "metrics": metrics,
        "books": rows,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Seedless nestedness-contribution pilot",
        "",
        "The score is a book's average excess audience containment against stratified random "
        "book panels, after subtracting a bipartite degree-configuration expectation. Discovery "
        "used only rating-tuple structure; titles, authors, and evaluation lists were loaded "
        "after scores and panel stability were frozen.",
        "",
        f"Matrix: **{binary.shape[0]:,} readers × {binary.shape[1]:,} works**; panels: "
        f"**{PANELS} × {ANCHORS_PER_PANEL} anchors**; runtime: "
        f"**{result['method']['runtime_seconds']:.1f}s**.",
        "",
        "## Independent-panel stability",
        "",
        "| panel | Spearman | J@50 | J@100 | J@200 | J@500 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for i, row in enumerate(panel_stability, 1):
        lines.append(
            f"| {i} | {row['spearman']:.3f} | {row['jaccard50']:.3f} | "
            f"{row['jaccard100']:.3f} | {row['jaccard200']:.3f} | "
            f"{row['jaccard500']:.3f} |"
        )
    lines += [
        "",
        "## Post-hoc ranking",
        "",
        f"Exact literary @50/200/500: **{metrics['exact_lit50']}/{metrics['exact_lit200']}/"
        f"{metrics['exact_lit500']}**; broad literary: **{metrics['broad_lit50']}/"
        f"{metrics['broad_lit200']}/{metrics['broad_lit500']}**; anti: "
        f"**{metrics['anti50']}/{metrics['anti200']}/{metrics['anti500']}**.",
        "",
    ]
    for row in rows[:100]:
        lines.append(
            f"{row['rank']}. *{row['title']}* — {row['author']} "
            f"({row['score']:.6f} ± {row['uncertainty']:.6f}; "
            f"positive panels={row['positive_share']:.3f}; sampled readers={row['sampled_degree']:,})"
        )
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

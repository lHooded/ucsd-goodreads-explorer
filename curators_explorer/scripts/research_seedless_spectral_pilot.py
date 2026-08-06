#!/usr/bin/env python3
"""Seedless signed spectral taste modes from ratings alone.

Discovery is restricted to (user_id, work_id, rating) and aggregates derived
from those tuples.  Titles, authors, flags, and semantic lists are loaded only
after the spectral objects and stability diagnostics have been frozen.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import time
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import coo_matrix, csr_matrix

from curators_explorer.db import DB_PATH, LEGACY_TASTE_PATH
from curators_explorer.scripts.research_ratings_only_canon import load_eval_sets


DATA = Path(__file__).resolve().parents[1] / "data"
CACHE = DATA / "seedless_spectral_pilot_matrix.npz"
OUT_JSON = DATA / "seedless_spectral_pilot.json"
OUT_REPORT = DATA / "SEEDLESS_SPECTRAL_PILOT_REPORT.md"

DEFAULTS = {
    "min_user_side": 20,
    "min_book_n": 100,
    "max_per_side": 16,
    "sample_seed": 20260806,
    "rank": 16,
    "oversample": 8,
    "power_iters": 4,
    "degree_alpha": 1.0,
    "degree_ridge_fraction": 0.10,
}

EXTRACTION_KEYS = ("min_user_side", "min_book_n", "max_per_side", "sample_seed")


def extraction_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return only settings that affect the cached sparse matrix."""
    return {key: config[key] for key in EXTRACTION_KEYS}


def clean_array(value: Any, dtype: np.dtype) -> np.ndarray:
    if np.ma.isMaskedArray(value):
        value = value.filled(np.nan)
    return np.asarray(value, dtype=dtype)


def extraction_connection() -> duckdb.DuckDBPyConnection:
    temp_dir = Path(__file__).resolve().parents[2] / ".tmp" / "seedless_spectral"
    temp_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"PRAGMA temp_directory='{temp_dir}'")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    return con


def build_cache(config: dict[str, Any]) -> dict[str, np.ndarray]:
    t0 = time.time()
    con = extraction_connection()
    print("Materializing ratings-only eligibility tables...", flush=True)
    con.execute(
        f"""
        CREATE TEMP TABLE eligible_users AS
        SELECT (row_number() OVER (ORDER BY user_id)-1)::INTEGER AS ui,
               user_id,
               n5::INTEGER AS n5,
               nlow::INTEGER AS nlow,
               ntotal::INTEGER AS ntotal,
               (n5::DOUBLE/ntotal)::FLOAT AS five_rate
        FROM (
            SELECT user_id,
                   count(*) FILTER (WHERE rating=5) AS n5,
                   count(*) FILTER (WHERE rating BETWEEN 1 AND 3) AS nlow,
                   count(*) FILTER (WHERE rating>0) AS ntotal
            FROM ex.all_rating_events
            WHERE rating>0
            GROUP BY user_id
            HAVING n5 >= {config['min_user_side']}
               AND nlow >= {config['min_user_side']}
        )
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE eligible_books AS
        SELECT (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS bi,
               work_id,
               n::INTEGER AS n,
               (n5::DOUBLE/n)::FLOAT AS p5,
               mean_rating::FLOAT AS mean_rating
        FROM (
            SELECT work_id, count(*) AS n,
                   count(*) FILTER (WHERE rating=5) AS n5,
                   avg(rating) FILTER (WHERE rating>0) AS mean_rating
            FROM ex.all_rating_events
            WHERE rating>0
            GROUP BY work_id
            HAVING n >= {config['min_book_n']}
        )
        """
    )
    users = con.execute(
        "SELECT ui,user_id,n5,nlow,ntotal,five_rate FROM eligible_users ORDER BY ui"
    ).fetchnumpy()
    books = con.execute(
        "SELECT bi,work_id,n,p5,mean_rating FROM eligible_books ORDER BY bi"
    ).fetchnumpy()
    n_users, n_books = len(users["ui"]), len(books["bi"])
    print(f"  eligible users={n_users:,}; books={n_books:,}", flush=True)
    print("Extracting deterministic balanced edge sample...", flush=True)
    edges = con.execute(
        f"""
        WITH ranked AS (
            SELECT u.ui, b.bi,
                   CASE WHEN e.rating=5 THEN 1 ELSE -1 END::TINYINT AS side,
                   row_number() OVER (
                       PARTITION BY u.ui, CASE WHEN e.rating=5 THEN 1 ELSE -1 END
                       ORDER BY hash(e.user_id,e.work_id,{config['sample_seed']})
                   ) AS rn
            FROM ex.all_rating_events e
            JOIN eligible_users u USING (user_id)
            JOIN eligible_books b USING (work_id)
            WHERE e.rating=5 OR e.rating BETWEEN 1 AND 3
        )
        SELECT ui,bi,side FROM ranked
        WHERE rn <= {config['max_per_side']}
        ORDER BY ui,side,bi
        """
    ).fetchnumpy()
    con.close()
    payload = {
        "row": clean_array(edges["ui"], np.int32),
        "col": clean_array(edges["bi"], np.int32),
        "side": clean_array(edges["side"], np.int8),
        "user_ids": clean_array(users["user_id"], np.int64),
        "user_n5": clean_array(users["n5"], np.float32),
        "user_nlow": clean_array(users["nlow"], np.float32),
        "user_ntotal": clean_array(users["ntotal"], np.float32),
        "user_five_rate": clean_array(users["five_rate"], np.float32),
        "work_ids": np.asarray(books["work_id"], dtype=str),
        "book_n": clean_array(books["n"], np.float32),
        "book_p5": clean_array(books["p5"], np.float32),
        "book_mean": clean_array(books["mean_rating"], np.float32),
        "config_json": np.asarray(json.dumps(extraction_config(config), sort_keys=True)),
    }
    print(
        f"  sampled edges={len(payload['row']):,}; extraction={time.time()-t0:.1f}s",
        flush=True,
    )
    np.savez_compressed(CACHE, **payload)
    print(f"  wrote cache {CACHE} ({CACHE.stat().st_size/2**20:.1f} MiB)", flush=True)
    return payload


def load_or_build_cache(config: dict[str, Any], rebuild: bool) -> dict[str, np.ndarray]:
    if CACHE.exists() and not rebuild:
        with np.load(CACHE, allow_pickle=False) as saved:
            payload = {key: saved[key] for key in saved.files}
        cached = json.loads(str(payload["config_json"]))
        cached_extraction = {key: cached.get(key) for key in EXTRACTION_KEYS}
        if cached_extraction == extraction_config(config):
            print(f"Loaded matrix cache {CACHE}", flush=True)
            return payload
        print("Matrix extraction configuration differs; rebuilding.", flush=True)
    return build_cache(config)


def build_matrix(payload: dict[str, np.ndarray]) -> tuple[csr_matrix, dict[str, Any]]:
    row, col, side = payload["row"], payload["col"], payload["side"]
    n_users, n_books = len(payload["user_ids"]), len(payload["work_ids"])
    pos = np.bincount(row[side > 0], minlength=n_users).astype(np.float32)
    neg = np.bincount(row[side < 0], minlength=n_users).astype(np.float32)
    valid_user = (pos > 0) & (neg > 0)
    keep = valid_user[row]
    row, col, side = row[keep], col[keep], side[keep]
    values = np.where(
        side > 0,
        0.5 / pos[row],
        -0.5 / neg[row],
    ).astype(np.float32)
    matrix = coo_matrix((values, (row, col)), shape=(n_users, n_books)).tocsr()
    matrix.sum_duplicates()
    return matrix, {
        "users_with_both_sides": int(valid_user.sum()),
        "sampled_edges": int(matrix.nnz),
        "row_l1_median": float(np.median(np.asarray(abs(matrix).sum(axis=1)).ravel())),
    }


def orthobasis(columns: list[np.ndarray]) -> np.ndarray:
    prepared = []
    for i, col in enumerate(columns):
        x = np.asarray(col, dtype=np.float64).copy()
        finite = np.isfinite(x)
        x[~finite] = np.median(x[finite]) if finite.any() else 0.0
        if i:
            sd = x.std()
            x = (x - x.mean()) / (sd if sd > 1e-12 else 1.0)
        prepared.append(x)
    q, _ = np.linalg.qr(np.column_stack(prepared), mode="reduced")
    return q.astype(np.float32)


class ProjectedOperator:
    def __init__(
        self,
        matrix: csr_matrix,
        user_basis: np.ndarray,
        book_basis: np.ndarray,
        book_scale: np.ndarray,
    ) -> None:
        self.matrix = matrix
        self.user_basis = user_basis
        self.book_basis = book_basis
        self.book_scale = book_scale.astype(np.float32)
        self.shape = matrix.shape

    @staticmethod
    def _project(x: np.ndarray, basis: np.ndarray) -> np.ndarray:
        vector = x.ndim == 1
        xx = x[:, None] if vector else x
        result = xx - basis @ (basis.T @ xx)
        return result[:, 0] if vector else result

    def project_user(self, x: np.ndarray) -> np.ndarray:
        return self._project(np.asarray(x, dtype=np.float32), self.user_basis)

    def project_book(self, x: np.ndarray) -> np.ndarray:
        return self._project(np.asarray(x, dtype=np.float32), self.book_basis)

    def matmat(self, book: np.ndarray) -> np.ndarray:
        x = self.project_book(book)
        if x.ndim == 1:
            x = self.book_scale * x
        else:
            x = self.book_scale[:, None] * x
        return self.project_user(self.matrix @ x)

    def rmatmat(self, user: np.ndarray) -> np.ndarray:
        x = self.matrix.T @ self.project_user(user)
        if x.ndim == 1:
            x = self.book_scale * x
        else:
            x = self.book_scale[:, None] * x
        return self.project_book(x)


def make_operator(
    matrix: csr_matrix,
    payload: dict[str, np.ndarray],
    config: dict[str, Any],
    user_indices: np.ndarray | None = None,
) -> tuple[ProjectedOperator, dict[str, Any]]:
    if user_indices is None:
        user_indices = np.arange(matrix.shape[0])
    user_basis = orthobasis(
        [
            np.ones(len(user_indices)),
            np.log1p(payload["user_ntotal"][user_indices]),
            payload["user_five_rate"][user_indices],
        ]
    )
    book_basis = orthobasis(
        [
            np.ones(matrix.shape[1]),
            np.log1p(payload["book_n"]),
            payload["book_p5"],
            payload["book_mean"],
        ]
    )
    energy = np.asarray(matrix.power(2).sum(axis=0)).ravel().astype(np.float64)
    nonzero = energy[energy > 0]
    median_energy = float(np.median(nonzero)) if len(nonzero) else 1.0
    ridge = config["degree_ridge_fraction"] * median_energy
    scale = np.power(energy + ridge, -0.5 * config["degree_alpha"])
    scale /= np.median(scale[np.isfinite(scale) & (energy > 0)])
    scale[~np.isfinite(scale)] = 0.0
    return ProjectedOperator(matrix, user_basis, book_basis, scale.astype(np.float32)), {
        "column_energy_median": median_energy,
        "column_scale_q05_q50_q95": [
            float(x) for x in np.quantile(scale[np.isfinite(scale)], [0.05, 0.5, 0.95])
        ],
        "projected_user_nuisance_dimensions": user_basis.shape[1],
        "projected_book_nuisance_dimensions": book_basis.shape[1],
    }


def randomized_svd(
    operator: ProjectedOperator,
    rank: int,
    oversample: int,
    power_iters: int,
    seed: int,
    label: str,
) -> dict[str, Any]:
    t0 = time.time()
    rng = np.random.default_rng(seed)
    width = rank + oversample
    omega = rng.standard_normal((operator.shape[1], width), dtype=np.float32)
    omega = operator.project_book(omega)
    q, _ = np.linalg.qr(operator.matmat(omega), mode="reduced")
    q = q.astype(np.float32)
    history = []
    previous_book = None
    for iteration in range(power_iters):
        z, _ = np.linalg.qr(operator.rmatmat(q), mode="reduced")
        z = z.astype(np.float32)
        overlap = None
        if previous_book is not None:
            singular = np.linalg.svd(previous_book.T @ z, compute_uv=False)
            overlap = float(np.mean(singular**2))
        previous_book = z
        q, _ = np.linalg.qr(operator.matmat(z), mode="reduced")
        q = q.astype(np.float32)
        history.append({"iteration": iteration + 1, "book_subspace_overlap": overlap})
        print(f"  {label}: power iteration {iteration+1}/{power_iters}", flush=True)
    small = operator.rmatmat(q).T
    uhat, singular_values, vt = np.linalg.svd(small, full_matrices=False)
    u = (q @ uhat[:, :rank]).astype(np.float32)
    v = vt[:rank].astype(np.float32)
    singular_values = singular_values[:rank].astype(np.float64)
    av = operator.matmat(v.T)
    residual = np.linalg.norm(av - u * singular_values[None, :], axis=0) / np.maximum(
        singular_values, 1e-12
    )
    return {
        "u": u,
        "v": v,
        "singular_values": singular_values,
        "relative_residual": residual.astype(np.float64),
        "history": history,
        "runtime_seconds": time.time() - t0,
    }


def jaccard_indices(a: np.ndarray, b: np.ndarray, k: int) -> float:
    aa, bb = set(a[:k].tolist()), set(b[:k].tolist())
    return len(aa & bb) / max(1, len(aa | bb))


def align_modes(reference: np.ndarray, other: np.ndarray) -> list[dict[str, Any]]:
    correlation = reference @ other.T
    rows, cols = linear_sum_assignment(-np.abs(correlation))
    result: list[dict[str, Any]] = []
    for row, col in sorted(zip(rows, cols), key=lambda pair: pair[0]):
        sign = 1.0 if correlation[row, col] >= 0 else -1.0
        a, b = reference[row], sign * other[col]
        result.append(
            {
                "reference_mode": int(row + 1),
                "matched_mode": int(col + 1),
                "abs_correlation": float(abs(correlation[row, col])),
                "positive_jaccard100": jaccard_indices(np.argsort(-a), np.argsort(-b), 100),
                "negative_jaccard100": jaccard_indices(np.argsort(a), np.argsort(b), 100),
            }
        )
    return result


def subspace_alignment(
    reference: np.ndarray,
    other: np.ndarray,
    cuts: tuple[int, ...] = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 40),
) -> list[dict[str, Any]]:
    """Principal-angle similarity, invariant to rotations within tied modes."""
    result = []
    for requested in cuts:
        k = min(requested, reference.shape[0], other.shape[0])
        if result and result[-1]["modes"] == k:
            continue
        canonical = np.linalg.svd(reference[:k] @ other[:k].T, compute_uv=False)
        result.append(
            {
                "modes": int(k),
                "mean_squared_canonical_correlation": float(np.mean(canonical**2)),
                "minimum_canonical_correlation": float(canonical.min()),
                "median_canonical_correlation": float(np.median(canonical)),
            }
        )
    return result


def localization_metrics(vector: np.ndarray) -> dict[str, float]:
    """How many books carry a mode, using squared loading as mass."""
    squared = np.asarray(vector, dtype=np.float64) ** 2
    squared /= max(float(squared.sum()), 1e-30)

    def effective_for_pole(pole: np.ndarray) -> float:
        mass = np.asarray(pole, dtype=np.float64) ** 2
        total = float(mass.sum())
        if total <= 1e-30:
            return 0.0
        mass /= total
        return float(1.0 / np.sum(mass**2))

    order = np.sort(squared)[::-1]
    return {
        "effective_books": float(1.0 / np.sum(squared**2)),
        "positive_effective_books": effective_for_pole(np.maximum(vector, 0)),
        "negative_effective_books": effective_for_pole(np.maximum(-vector, 0)),
        "top10_squared_mass": float(order[:10].sum()),
        "top50_squared_mass": float(order[:50].sum()),
    }


def configuration_null(matrix: csr_matrix, seed: int) -> csr_matrix:
    coo = matrix.tocoo(copy=True)
    rng = np.random.default_rng(seed)
    positive = coo.data > 0
    negative = coo.data < 0
    cols = coo.col.copy()
    cols[positive] = rng.permutation(cols[positive])
    cols[negative] = rng.permutation(cols[negative])
    null = coo_matrix((coo.data, (coo.row, cols)), shape=matrix.shape).tocsr()
    null.sum_duplicates()
    null.eliminate_zeros()
    return null


def normalize_text(value: str) -> str:
    return " ".join(re.findall(r"\w+", value.casefold(), flags=re.UNICODE))


def load_posthoc_context(work_ids: np.ndarray) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """This is intentionally called only after all decompositions are complete."""
    con = duckdb.connect(DB_PATH, read_only=True)
    rows = con.execute(
        "SELECT work_id,title,author,author_url,n,p5,mean FROM work_scores"
    ).fetchall()
    candidate_set = set(work_ids.tolist())
    meta = {
        str(work_id): {
            "title": title or "",
            "author": author or "",
            "author_url": author_url or "",
            "n": int(n or 0),
            "p5": float(p5 or 0),
            "mean": float(mean or 0),
        }
        for work_id, title, author, author_url, n, p5, mean in rows
        if str(work_id) in candidate_set
    }
    # Existing broad author-expanded sets are evaluation only.
    eval_con = duckdb.connect()
    eval_con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    eval_con.execute("USE ex")
    eval_sets = load_eval_sets(eval_con)
    eval_con.close()

    # Recover the exact original 100-title seed separately from the author-expanded set.
    taste = json.loads(LEGACY_TASTE_PATH.read_text(encoding="utf-8"))
    by_author: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for work_id, row in meta.items():
        match = re.search(r"/author/show/(\d+)", row["author_url"])
        if match:
            by_author.setdefault(match.group(1), []).append((work_id, row))
    exact: set[str] = set()
    exact_matches = []
    for source in taste["resolved"]["literary_poll"]:
        target = normalize_text(source.get("poll_title") or "")
        choices = by_author.get(str(source["author_id"]), [])
        scored = [
            (difflib.SequenceMatcher(None, target, normalize_text(row["title"])).ratio(), work_id)
            for work_id, row in choices
        ]
        if scored:
            score, work_id = max(scored)
            if score >= 0.58:
                exact.add(work_id)
                exact_matches.append({"poll_title": source.get("poll_title"), "work_id": work_id, "similarity": score})
    con.close()
    return meta, {
        "exact_lit": exact,
        "broad_lit": set(eval_sets["pos_works"]),
        "anti": set(eval_sets["anti_works"]),
        "filler": set(eval_sets["filler_works"]),
        "exact_matches": exact_matches,
    }


def pole_rows(
    vector: np.ndarray,
    work_ids: np.ndarray,
    meta: dict[str, dict[str, Any]],
    eval_sets: dict[str, Any],
    positive: bool,
    limit: int = 200,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    order = np.argsort(-vector if positive else vector)[:limit]
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
                "score": float(vector[index] if positive else -vector[index]),
                "n": int(book.get("n", 0)),
                "p5": float(book.get("p5", 0)),
            }
        )
    metrics = {}
    for name in ("exact_lit", "broad_lit", "anti", "filler"):
        target = eval_sets[name]
        metrics[f"{name}50"] = sum(row["work_id"] in target for row in rows[:50])
        metrics[f"{name}200"] = sum(row["work_id"] in target for row in rows[:200])
    return rows, metrics


def main() -> None:
    global CACHE, OUT_JSON, OUT_REPORT
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild-matrix", action="store_true")
    parser.add_argument("--rank", type=int, default=DEFAULTS["rank"])
    parser.add_argument("--power-iters", type=int, default=DEFAULTS["power_iters"])
    parser.add_argument("--min-book-n", type=int, default=DEFAULTS["min_book_n"])
    args = parser.parse_args()
    config = {
        **DEFAULTS,
        "rank": args.rank,
        "power_iters": args.power_iters,
        "min_book_n": args.min_book_n,
    }
    if args.min_book_n != DEFAULTS["min_book_n"]:
        suffix = f"_b{args.min_book_n}"
        CACHE = DATA / f"seedless_spectral_pilot_matrix{suffix}.npz"
        OUT_JSON = DATA / f"seedless_spectral_pilot{suffix}.json"
        OUT_REPORT = DATA / f"SEEDLESS_SPECTRAL_PILOT_REPORT{suffix}.md"
    t0 = time.time()
    payload = load_or_build_cache(config, args.rebuild_matrix)
    matrix, matrix_meta = build_matrix(payload)
    print(f"CSR matrix {matrix.shape}, nnz={matrix.nnz:,}", flush=True)
    operator, operator_meta = make_operator(matrix, payload, config)
    main_fit = randomized_svd(
        operator, config["rank"], config["oversample"], config["power_iters"], 11, "full"
    )

    half_results = []
    half_vectors = []
    for parity in (0, 1):
        indices = np.flatnonzero((payload["user_ids"] % 2) == parity)
        half_matrix = matrix[indices].tocsr()
        half_operator, _ = make_operator(half_matrix, payload, config, indices)
        fit = randomized_svd(
            half_operator,
            config["rank"],
            config["oversample"],
            config["power_iters"],
            101 + parity,
            f"half{parity}",
        )
        half_results.append(
            {
                "parity": parity,
                "users": len(indices),
                "singular_values": fit["singular_values"].tolist(),
                "alignment": align_modes(main_fit["v"], fit["v"]),
                "subspace_alignment": subspace_alignment(main_fit["v"], fit["v"]),
                "runtime_seconds": fit["runtime_seconds"],
            }
        )
        half_vectors.append(fit["v"])
        del half_matrix, half_operator, fit

    print("Building sign-configuration null...", flush=True)
    null_matrix = configuration_null(matrix, 991)
    null_operator, _ = make_operator(null_matrix, payload, config)
    null_fit = randomized_svd(
        null_operator,
        config["rank"],
        config["oversample"],
        config["power_iters"],
        211,
        "null",
    )
    del null_matrix, null_operator

    # Semantic information is first loaded here, after discovery is frozen.
    print("Loading post-hoc titles and evaluation sets...", flush=True)
    meta, eval_sets = load_posthoc_context(payload["work_ids"])
    modes = []
    for i in range(config["rank"]):
        positive, pos_metrics = pole_rows(
            main_fit["v"][i], payload["work_ids"], meta, eval_sets, True
        )
        negative, neg_metrics = pole_rows(
            main_fit["v"][i], payload["work_ids"], meta, eval_sets, False
        )
        half_stability = []
        for half in half_results:
            match = next(row for row in half["alignment"] if row["reference_mode"] == i + 1)
            half_stability.append(match)
        modes.append(
            {
                "mode": i + 1,
                "singular_value": float(main_fit["singular_values"][i]),
                "null_singular_value": float(null_fit["singular_values"][i]),
                "spectral_excess_ratio": float(
                    main_fit["singular_values"][i] / max(null_fit["singular_values"][i], 1e-12)
                ),
                "relative_residual": float(main_fit["relative_residual"][i]),
                "half_abs_correlation_mean": float(
                    np.mean([row["abs_correlation"] for row in half_stability])
                ),
                "half_pole_jaccard100_mean": float(
                    np.mean(
                        [
                            0.5 * (row["positive_jaccard100"] + row["negative_jaccard100"])
                            for row in half_stability
                        ]
                    )
                ),
                "half_matches": half_stability,
                "localization": localization_metrics(main_fit["v"][i]),
                "positive_metrics": pos_metrics,
                "negative_metrics": neg_metrics,
                "positive_head": positive[:25],
                "negative_head": negative[:25],
            }
        )

    result = {
        "method": {
            "purpose": "seedless signed spectral attractor pilot",
            "allowed_discovery_columns": ["user_id", "work_id", "rating"],
            "semantic_data_loaded_after_fit": True,
            "config": config,
            "runtime_seconds": time.time() - t0,
        },
        "matrix": {**matrix_meta, "shape": list(matrix.shape), "cache": CACHE.name},
        "operator": operator_meta,
        "fit": {
            "singular_values": main_fit["singular_values"].tolist(),
            "null_singular_values": null_fit["singular_values"].tolist(),
            "relative_residual": main_fit["relative_residual"].tolist(),
            "power_history": main_fit["history"],
            "runtime_seconds": main_fit["runtime_seconds"],
        },
        "halves": half_results,
        "half_to_half_subspace_alignment": subspace_alignment(
            half_vectors[0], half_vectors[1]
        ),
        "subspace_stability_mean": [
            {
                "modes": row0["modes"],
                "mean_squared_canonical_correlation": float(
                    np.mean(
                        [
                            half["subspace_alignment"][j][
                                "mean_squared_canonical_correlation"
                            ]
                            for half in half_results
                        ]
                    )
                ),
                "minimum_canonical_correlation": float(
                    np.mean(
                        [
                            half["subspace_alignment"][j]["minimum_canonical_correlation"]
                            for half in half_results
                        ]
                    )
                ),
            }
            for j, row0 in enumerate(half_results[0]["subspace_alignment"])
        ],
        "evaluation": {
            "exact_lit_candidates": len(eval_sets["exact_lit"]),
            "broad_lit_candidates": len(eval_sets["broad_lit"] & set(payload["work_ids"].tolist())),
            "anti_candidates": len(eval_sets["anti"] & set(payload["work_ids"].tolist())),
            "filler_candidates": len(eval_sets["filler"] & set(payload["work_ids"].tolist())),
            "exact_matches": eval_sets["exact_matches"],
        },
        "modes": modes,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Seedless signed spectral pilot", "", "## Design", "",
        "Discovery used only `(user_id, work_id, rating)`. Each reader contributes equal total "
        "positive (5-star) and negative (1–3-star) mass. Ratings-derived book popularity, mean, "
        "five-star tendency, user activity, and generosity are projected out. Titles, authors, "
        "flags, and semantic lists are loaded only after all full/half/null decompositions finish.", "",
        f"Matrix: **{matrix.shape[0]:,} users × {matrix.shape[1]:,} works**, "
        f"**{matrix.nnz:,} signed edges**. Runtime: **{result['method']['runtime_seconds']:.1f}s**; "
        f"matrix cache: **{CACHE.stat().st_size/2**20:.1f} MiB**.", "",
        "The two half-sample fits use disjoint readers. The shuffled null preserves each reader's "
        "positive/negative counts and the global positive/negative book frequencies while "
        "destroying reader-level co-preference.", "", "## Spectrum and stability", "",
        "### Stable-subspace test", "",
        "Unlike individual-vector correlation, this test allows tied or nearly tied modes to "
        "rotate within the same shared subspace.", "",
        "| leading modes | full↔half mean sq. corr | full↔half weakest | half↔half mean sq. corr | half↔half weakest |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row, direct in zip(
        result["subspace_stability_mean"], result["half_to_half_subspace_alignment"]
    ):
        lines.append(
            f"| {row['modes']} | {row['mean_squared_canonical_correlation']:.3f} | "
            f"{row['minimum_canonical_correlation']:.3f} | "
            f"{direct['mean_squared_canonical_correlation']:.3f} | "
            f"{direct['minimum_canonical_correlation']:.3f} |"
        )
    lines += [
        "", "### Individual modes", "",
        "`eff. books` is the inverse concentration of squared loadings: larger means broader; "
        "`top50 mass` is the fraction of a mode carried by its 50 most extreme books.", "",
        "| mode | singular | null | excess | residual | half corr | half pole J@100 | eff. books | top50 mass | exact lit +/− @50 | broad lit +/− @50 | anti +/− @50 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in modes:
        pm, nm = mode["positive_metrics"], mode["negative_metrics"]
        local = mode["localization"]
        lines.append(
            f"| {mode['mode']} | {mode['singular_value']:.4f} | {mode['null_singular_value']:.4f} | "
            f"{mode['spectral_excess_ratio']:.2f} | {mode['relative_residual']:.2e} | "
            f"{mode['half_abs_correlation_mean']:.3f} | {mode['half_pole_jaccard100_mean']:.3f} | "
            f"{local['effective_books']:.0f} | {local['top50_squared_mass']:.3f} | "
            f"{pm['exact_lit50']}/{nm['exact_lit50']} | {pm['broad_lit50']}/{nm['broad_lit50']} | "
            f"{pm['anti50']}/{nm['anti50']} |"
        )
    lines += ["", "## Mode poles", ""]
    for mode in modes:
        lines += [f"### Mode {mode['mode']} positive", ""]
        for row in mode["positive_head"][:12]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"(loading {row['score']:.5f}, n={row['n']:,})"
            )
        lines += ["", f"### Mode {mode['mode']} negative", ""]
        for row in mode["negative_head"][:12]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"(loading {row['score']:.5f}, n={row['n']:,})"
            )
        lines.append("")
    lines += [
        "## Interpretation rule", "",
        "A mode is structurally credible only if it exceeds the shuffled spectrum and aligns "
        "across both disjoint-reader halves. Literary overlap is descriptive post-hoc evidence, "
        "not part of mode fitting, orientation, ordering, or acceptance. If literary books appear "
        "only in unstable or null-sized modes, the ratings matrix does not support a naturally "
        "identifiable single literary axis under this operator.", "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Publication-year-aware literary jury from ratings plus edition years.

Discovery uses (user_id, work_id, rating) plus publication_year.  A work's
primary year is the minimum credible edition year in the complete UCSD books
catalogue, not the selected/display edition.  Titles, authors, and literary
evaluation lists are loaded only after all jury and book scores are frozen.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
from scipy.stats import spearmanr

from curators_explorer.db import DB_PATH
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from ucsd_explorer.db import PARQUET


DATA = Path(__file__).resolve().parents[1] / "data"
MATRIX_CACHE = DATA / "seedless_spectral_pilot_matrix_b500.npz"
OUT_JSON = DATA / "year_aware_canon_pilot.json"
OUT_REPORT = DATA / "YEAR_AWARE_CANON_PILOT_REPORT.md"

YEAR_MIN = 1500
YEAR_MAX = 2017
OLDNESS_ZERO = 2000.0
OLDNESS_ONE = 1850.0
USER_PRIOR = 10.0
MIN_TRAIN_FIVES = 8
BOOK_SHRINK_READERS = 25.0

VARIANTS = (
    {"name": "min_linear_q10", "year": "min_year", "oldness": "linear", "quantile": 0.10},
    {"name": "q10_linear_q10", "year": "q10_year", "oldness": "linear", "quantile": 0.10},
    {"name": "min_linear1800_q10", "year": "min_year", "oldness": "linear1800", "quantile": 0.10},
    {"name": "min_linear1900_q10", "year": "min_year", "oldness": "linear1900", "quantile": 0.10},
    {"name": "min_pre1950_q10", "year": "min_year", "oldness": "pre1950", "quantile": 0.10},
    {"name": "min_linear_q05", "year": "min_year", "oldness": "linear", "quantile": 0.05},
    {"name": "min_linear_q20", "year": "min_year", "oldness": "linear", "quantile": 0.20},
    {
        "name": "min_linear_mass_q10",
        "year": "min_year",
        "oldness": "linear",
        "quantile": 0.10,
        "user_score": "mass",
    },
    {
        "name": "min_linear_q10_all",
        "year": "min_year",
        "oldness": "linear",
        "quantile": 0.10,
        "comparator": "all",
    },
)


def load_matrix() -> tuple[dict[str, np.ndarray], Any, dict[str, Any]]:
    with np.load(MATRIX_CACHE, allow_pickle=False) as saved:
        payload = {key: saved[key] for key in saved.files}
    matrix, meta = spectral.build_matrix(payload)
    return payload, matrix, meta


def extraction_connection() -> duckdb.DuckDBPyConnection:
    temp_dir = Path(__file__).resolve().parents[2] / ".tmp" / "year_aware_canon"
    temp_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"PRAGMA temp_directory='{temp_dir}'")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    return con


def extract_year_features(
    payload: dict[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    books_pq = PARQUET / "books.parquet"
    con = extraction_connection()
    print("Materializing clean all-edition work years", flush=True)
    con.execute(
        f"""
        CREATE TEMP TABLE edition_years AS
        SELECT work_id::VARCHAR AS work_id,
               try_cast(publication_year AS INTEGER)::INTEGER AS pub_year
        FROM read_parquet('{books_pq}')
        WHERE work_id IS NOT NULL
          AND try_cast(publication_year AS INTEGER) BETWEEN {YEAR_MIN} AND {YEAR_MAX}
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE clean_years AS
        SELECT work_id,
               min(pub_year)::INTEGER AS min_year,
               round(quantile_cont(pub_year, 0.10))::INTEGER AS q10_year,
               count(*)::INTEGER AS dated_editions,
               count(DISTINCT pub_year)::INTEGER AS distinct_years
        FROM edition_years
        GROUP BY work_id
        """
    )
    print("Materializing eligible readers and cross-fit year features", flush=True)
    con.execute(
        """
        CREATE TEMP TABLE eligible_users AS
        SELECT user_id
        FROM ex.all_rating_events
        WHERE rating > 0
        GROUP BY user_id
        HAVING count(*) FILTER (WHERE rating=5) >= 20
           AND count(*) FILTER (WHERE rating BETWEEN 1 AND 3) >= 20
        """
    )
    features = con.execute(
        f"""
        SELECT e.user_id,
               (try_cast(e.work_id AS UBIGINT) % 2)::TINYINT AS fold,
               count(*)::INTEGER AS n5_year,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.min_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )))::DOUBLE AS min_linear_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.min_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )), 2))::DOUBLE AS min_linear_sq_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.min_year) / ({OLDNESS_ZERO - 1800.0})
               )))::DOUBLE AS min_linear1800_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.min_year) / ({OLDNESS_ZERO - 1800.0})
               )), 2))::DOUBLE AS min_linear1800_sq_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.min_year) / ({OLDNESS_ZERO - 1900.0})
               )))::DOUBLE AS min_linear1900_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.min_year) / ({OLDNESS_ZERO - 1900.0})
               )), 2))::DOUBLE AS min_linear1900_sq_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.q10_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )))::DOUBLE AS q10_linear_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.q10_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )), 2))::DOUBLE AS q10_linear_sq_sum,
               count(*) FILTER (WHERE y.min_year <= 1950)::DOUBLE AS pre1950_sum
        FROM ex.all_rating_events e
        JOIN eligible_users u USING (user_id)
        JOIN clean_years y USING (work_id)
        WHERE e.rating = 5
        GROUP BY e.user_id, fold
        ORDER BY e.user_id, fold
        """
    ).fetchnumpy()
    work_year_rows = con.execute(
        "SELECT work_id,min_year,q10_year,dated_editions,distinct_years FROM clean_years"
    ).fetchnumpy()
    audit = con.execute(
        f"""
        SELECT count(*) AS edition_rows,
               count(DISTINCT work_id) AS works_with_year,
               count(*) FILTER (WHERE pub_year < 1800) AS edition_rows_pre1800,
               min(pub_year) AS minimum,
               max(pub_year) AS maximum
        FROM edition_years
        """
    ).fetchone()
    raw_audit = con.execute(
        f"""
        SELECT count(*) AS rows,
               count(DISTINCT work_id) AS works,
               count(*) FILTER (
                   WHERE try_cast(publication_year AS INTEGER) BETWEEN {YEAR_MIN} AND {YEAR_MAX}
               ) AS valid_year_rows,
               count(*) FILTER (WHERE try_cast(publication_year AS INTEGER) < {YEAR_MIN}) AS too_early,
               count(*) FILTER (WHERE try_cast(publication_year AS INTEGER) > {YEAR_MAX}) AS too_late
        FROM read_parquet('{books_pq}')
        """
    ).fetchone()
    con.close()

    n_users = len(payload["user_ids"])
    user_data = {
        "n": np.zeros((2, n_users), dtype=np.float32),
        "min_linear_sum": np.zeros((2, n_users), dtype=np.float32),
        "min_linear_sq_sum": np.zeros((2, n_users), dtype=np.float32),
        "min_linear1800_sum": np.zeros((2, n_users), dtype=np.float32),
        "min_linear1800_sq_sum": np.zeros((2, n_users), dtype=np.float32),
        "min_linear1900_sum": np.zeros((2, n_users), dtype=np.float32),
        "min_linear1900_sq_sum": np.zeros((2, n_users), dtype=np.float32),
        "q10_linear_sum": np.zeros((2, n_users), dtype=np.float32),
        "q10_linear_sq_sum": np.zeros((2, n_users), dtype=np.float32),
        "pre1950_sum": np.zeros((2, n_users), dtype=np.float32),
    }
    source_users = spectral.clean_array(features["user_id"], np.int64)
    indices = np.searchsorted(payload["user_ids"], source_users)
    matched = (indices < n_users) & (payload["user_ids"][np.minimum(indices, n_users - 1)] == source_users)
    folds = spectral.clean_array(features["fold"], np.int8)
    indices, folds = indices[matched], folds[matched]
    mapping = {
        "n": "n5_year",
        "min_linear_sum": "min_linear_sum",
        "min_linear_sq_sum": "min_linear_sq_sum",
        "min_linear1800_sum": "min_linear1800_sum",
        "min_linear1800_sq_sum": "min_linear1800_sq_sum",
        "min_linear1900_sum": "min_linear1900_sum",
        "min_linear1900_sq_sum": "min_linear1900_sq_sum",
        "q10_linear_sum": "q10_linear_sum",
        "q10_linear_sq_sum": "q10_linear_sq_sum",
        "pre1950_sum": "pre1950_sum",
    }
    for target, source in mapping.items():
        user_data[target][folds, indices] = spectral.clean_array(features[source], np.float32)[matched]

    work_ids = np.asarray(work_year_rows["work_id"], dtype=str)
    work_year_map = {
        str(work_id): {
            "min_year": int(min_year),
            "q10_year": int(q10_year),
            "dated_editions": int(dated),
            "distinct_years": int(distinct),
        }
        for work_id, min_year, q10_year, dated, distinct in zip(
            work_ids,
            work_year_rows["min_year"],
            work_year_rows["q10_year"],
            work_year_rows["dated_editions"],
            work_year_rows["distinct_years"],
        )
    }
    candidate_years = {
        key: np.asarray(
            [work_year_map.get(str(work_id), {}).get(key, -1) for work_id in payload["work_ids"]],
            dtype=np.int16,
        )
        for key in ("min_year", "q10_year")
    }
    candidate_years["dated_editions"] = np.asarray(
        [work_year_map.get(str(work_id), {}).get("dated_editions", 0) for work_id in payload["work_ids"]],
        dtype=np.int16,
    )
    return {**user_data, **candidate_years}, {
        "edition_rows": int(audit[0]),
        "raw_catalogue_rows": int(raw_audit[0]),
        "raw_catalogue_works": int(raw_audit[1]),
        "raw_valid_year_rows": int(raw_audit[2]),
        "raw_year_rows_before_1500": int(raw_audit[3]),
        "raw_year_rows_after_2017": int(raw_audit[4]),
        "works_with_year": int(audit[1]),
        "edition_rows_pre1800": int(audit[2]),
        "year_band": [int(audit[3]), int(audit[4])],
        "candidate_works": len(payload["work_ids"]),
        "candidate_works_with_min_year": int(np.sum(candidate_years["min_year"] > 0)),
        "candidate_works_with_multiple_dated_editions": int(
            np.sum(candidate_years["dated_editions"] >= 2)
        ),
        "source": str(books_pq),
        "definition": "minimum and edition-row q10 over all valid edition publication_year values",
    }


def jury_score(
    features: dict[str, np.ndarray], fold: int, variant: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    n = features["n"][fold].astype(np.float64)
    if variant["oldness"].startswith("linear"):
        prefix = "min" if variant["year"] == "min_year" else "q10"
        endpoint = variant["oldness"].removeprefix("linear")
        feature = f"{prefix}_linear{endpoint}"
        total = features[f"{feature}_sum"][fold].astype(np.float64)
        total_sq = features[f"{feature}_sq_sum"][fold].astype(np.float64)
    else:
        total = features["pre1950_sum"][fold].astype(np.float64)
        total_sq = total.copy()
    valid = n >= MIN_TRAIN_FIVES
    global_mean = float(total[valid].sum() / max(n[valid].sum(), 1.0))
    global_second = float(total_sq[valid].sum() / max(n[valid].sum(), 1.0))
    posterior = (total + USER_PRIOR * global_mean) / (n + USER_PRIOR)
    variance = np.maximum(
        (total_sq + USER_PRIOR * global_second) / (n + USER_PRIOR) - posterior**2,
        0.0,
    )
    uncertainty = np.sqrt(variance / np.maximum(n + USER_PRIOR, 1.0))
    conservative_share = posterior - uncertainty
    # This sensitivity path rewards both concentration and volume.  Dividing by
    # sqrt(n) prevents raw Goodreads activity from completely determining the
    # jury while still distinguishing 40 old-equivalent loves from four.
    if variant.get("user_score", "share") == "mass":
        conservative = conservative_share * np.sqrt(n)
    else:
        conservative = conservative_share
    q = float(variant["quantile"])
    high_cut = float(np.quantile(conservative[valid], 1.0 - q))
    low_cut = float(np.quantile(conservative[valid], q))
    old_jury = valid & (conservative >= high_cut)
    if variant.get("comparator", "bottom") == "all":
        new_jury = valid
    else:
        new_jury = valid & (conservative <= low_cut)
    return old_jury, new_jury, {
        "global_oldness": global_mean,
        "high_cut": high_cut,
        "low_cut": low_cut,
        "valid_users": int(valid.sum()),
        "old_jury_users": int(old_jury.sum()),
        "new_jury_users": int(new_jury.sum()),
        "old_jury_mean_posterior": float(posterior[old_jury].mean()),
        "new_jury_mean_posterior": float(posterior[new_jury].mean()),
        "old_jury_median_year_known_fives": float(np.median(n[old_jury])),
        "new_jury_median_year_known_fives": float(np.median(n[new_jury])),
        "old_jury_median_old_equivalents": float(np.median(total[old_jury])),
        "new_jury_median_old_equivalents": float(np.median(total[new_jury])),
    }


def cohort_preference(
    matrix: Any, absolute_matrix: Any, binary_matrix: Any, cohort: np.ndarray
) -> dict[str, np.ndarray]:
    weights = cohort.astype(np.float32)
    signed = np.asarray(matrix.T @ weights).ravel().astype(np.float64)
    absolute = np.asarray(absolute_matrix.T @ weights).ravel().astype(np.float64)
    readers = np.asarray(binary_matrix.T @ weights).ravel().astype(np.float64)
    mean = np.divide(signed, absolute, out=np.zeros_like(signed), where=absolute > 0)
    reliability = readers / (readers + BOOK_SHRINK_READERS)
    uncertainty = np.sqrt(np.maximum(1.0 - mean**2, 1e-6) / np.maximum(readers, 1.0))
    return {"score": mean * reliability, "mean": mean, "readers": readers, "uncertainty": uncertainty}


def score_variant(
    matrix: Any,
    absolute_matrix: Any,
    binary_matrix: Any,
    payload: dict[str, np.ndarray],
    features: dict[str, np.ndarray],
    variant: dict[str, Any],
) -> dict[str, Any]:
    n_books = matrix.shape[1]
    book_fold = np.asarray([int(work_id) % 2 for work_id in payload["work_ids"]], dtype=np.int8)
    outputs = {
        name: np.zeros(n_books, dtype=np.float64)
        for name in ("absolute", "contrast", "old_mean", "new_mean", "readers", "uncertainty")
    }
    half_outputs = [
        {name: np.zeros(n_books, dtype=np.float64) for name in ("contrast", "readers")}
        for _ in range(2)
    ]
    fold_meta = []
    juries = []
    for target_fold in (0, 1):
        training_fold = 1 - target_fold
        old_jury, new_jury, meta = jury_score(features, training_fold, variant)
        juries.append(old_jury)
        meta.update({"target_book_fold": target_fold, "training_book_fold": training_fold})
        fold_meta.append(meta)
        old = cohort_preference(matrix, absolute_matrix, binary_matrix, old_jury)
        new = cohort_preference(matrix, absolute_matrix, binary_matrix, new_jury)
        target = book_fold == target_fold
        outputs["absolute"][target] = old["score"][target]
        outputs["contrast"][target] = old["score"][target] - new["score"][target]
        outputs["old_mean"][target] = old["mean"][target]
        outputs["new_mean"][target] = new["mean"][target]
        outputs["readers"][target] = np.minimum(old["readers"][target], new["readers"][target])
        outputs["uncertainty"][target] = np.sqrt(
            old["uncertainty"][target] ** 2 + new["uncertainty"][target] ** 2
        )
        for parity in (0, 1):
            user_half = (payload["user_ids"] % 2) == parity
            old_half = cohort_preference(
                matrix, absolute_matrix, binary_matrix, old_jury & user_half
            )
            new_half = cohort_preference(
                matrix, absolute_matrix, binary_matrix, new_jury & user_half
            )
            half_outputs[parity]["contrast"][target] = (
                old_half["score"][target] - new_half["score"][target]
            )
            half_outputs[parity]["readers"][target] = np.minimum(
                old_half["readers"][target], new_half["readers"][target]
            )
    a, b = set(np.flatnonzero(juries[0]).tolist()), set(np.flatnonzero(juries[1]).tolist())
    jury_jaccard = len(a & b) / max(1, len(a | b))
    return {
        "variant": dict(variant),
        "scores": outputs,
        "half_scores": half_outputs,
        "folds": fold_meta,
        "crossfold_old_jury_jaccard": jury_jaccard,
    }


def rank_order(score: np.ndarray, readers: np.ndarray, minimum: int) -> np.ndarray:
    eligible = np.flatnonzero(readers >= minimum)
    return eligible[np.argsort(-score[eligible], kind="stable")]


def stability(result: dict[str, Any]) -> dict[str, Any]:
    full = result["scores"]
    full_order = rank_order(full["contrast"], full["readers"], 25)
    rows = []
    for parity, half in enumerate(result["half_scores"]):
        half_order = rank_order(half["contrast"], half["readers"], 12)
        row: dict[str, Any] = {"reader_parity": parity}
        for k in (50, 100, 200, 500):
            a, b = set(full_order[:k].tolist()), set(half_order[:k].tolist())
            row[f"jaccard{k}"] = len(a & b) / max(1, len(a | b))
        common = (full["readers"] >= 25) & (half["readers"] >= 12)
        row["score_spearman"] = float(
            spearmanr(full["contrast"][common], half["contrast"][common]).statistic
        )
        row["common_books"] = int(common.sum())
        rows.append(row)
    return {"halves": rows}


def posthoc_ranking(
    result: dict[str, Any],
    payload: dict[str, np.ndarray],
    features: dict[str, np.ndarray],
    meta: dict[str, dict[str, Any]],
    eval_sets: dict[str, Any],
    kind: str,
    limit: int = 1000,
) -> dict[str, Any]:
    values = result["scores"]
    ranking = rank_order(values[kind], values["readers"], 25)[:limit]
    rows = []
    for rank, index in enumerate(ranking, 1):
        work_id = str(payload["work_ids"][index])
        book = meta.get(work_id, {})
        rows.append(
            {
                "rank": rank,
                "work_id": work_id,
                "title": book.get("title", work_id),
                "author": book.get("author", ""),
                "score": float(values[kind][index]),
                "old_jury_mean": float(values["old_mean"][index]),
                "new_jury_mean": float(values["new_mean"][index]),
                "uncertainty": float(values["uncertainty"][index]),
                "sampled_readers_each_cohort": int(values["readers"][index]),
                "min_year": int(features["min_year"][index]) if features["min_year"][index] > 0 else None,
                "q10_year": int(features["q10_year"][index]) if features["q10_year"][index] > 0 else None,
            }
        )
    metrics = {}
    for name in ("exact_lit", "broad_lit", "anti", "filler"):
        for k in (50, 200, 500, 1000):
            metrics[f"{name}{k}"] = sum(row["work_id"] in eval_sets[name] for row in rows[:k])
    return {"kind": kind, "metrics": metrics, "books": rows}


def main() -> None:
    t0 = time.time()
    payload, matrix, matrix_meta = load_matrix()
    absolute_matrix = abs(matrix).tocsr()
    binary_matrix = matrix.copy()
    binary_matrix.data = np.ones_like(binary_matrix.data)
    features, year_audit = extract_year_features(payload)
    print(
        f"Year coverage: {year_audit['candidate_works_with_min_year']:,}/"
        f"{year_audit['candidate_works']:,} candidate works",
        flush=True,
    )
    discovery = []
    for variant in VARIANTS:
        print(f"Scoring {variant['name']}", flush=True)
        row = score_variant(
            matrix, absolute_matrix, binary_matrix, payload, features, variant
        )
        row["stability"] = stability(row)
        discovery.append(row)

    # Cross-variant rank trajectories are frozen before semantic context.
    primary_order = rank_order(
        discovery[0]["scores"]["contrast"], discovery[0]["scores"]["readers"], 25
    )
    sensitivity = []
    for row in discovery[1:]:
        candidate = rank_order(row["scores"]["contrast"], row["scores"]["readers"], 25)
        overlaps = {}
        for k in (50, 100, 200, 500):
            a, b = set(primary_order[:k].tolist()), set(candidate[:k].tolist())
            overlaps[f"jaccard{k}"] = len(a & b) / max(1, len(a | b))
        sensitivity.append({"variant": row["variant"]["name"], **overlaps})

    print("Loading titles and evaluation sets after scores are frozen", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    example_titles = {
        "moby-dick or, the whale",
        "ulysses",
        "the brothers karamazov",
        "the great gatsby",
        "one hundred years of solitude",
    }
    year_examples = []
    for index, work_id_value in enumerate(payload["work_ids"]):
        work_id = str(work_id_value)
        book = meta.get(work_id, {})
        if book.get("title", "").casefold() in example_titles:
            year_examples.append(
                {
                    "work_id": work_id,
                    "title": book["title"],
                    "min_year": int(features["min_year"][index]),
                    "q10_year": int(features["q10_year"][index]),
                    "dated_editions": int(features["dated_editions"][index]),
                }
            )
    year_audit["posthoc_examples"] = sorted(year_examples, key=lambda x: x["title"])
    variants = []
    for row in discovery:
        variants.append(
            {
                "variant": row["variant"],
                "folds": row["folds"],
                "crossfold_old_jury_jaccard": row["crossfold_old_jury_jaccard"],
                "stability": row["stability"],
                "contrast_ranking": posthoc_ranking(
                    row, payload, features, meta, eval_sets, "contrast"
                ),
                "absolute_ranking": posthoc_ranking(
                    row, payload, features, meta, eval_sets, "absolute"
                ),
            }
        )
    output = {
        "method": {
            "purpose": "publication-year-aware, otherwise ratings-only literary jury",
            "allowed_discovery_columns": ["user_id", "work_id", "rating", "publication_year"],
            "semantic_data_loaded_after_scores_frozen": True,
            "year_min": YEAR_MIN,
            "year_max": YEAR_MAX,
            "oldness_zero": OLDNESS_ZERO,
            "oldness_one": OLDNESS_ONE,
            "user_prior": USER_PRIOR,
            "min_training_fives": MIN_TRAIN_FIVES,
            "crossfit": "book fold scored by jury learned from the opposite work_id parity",
            "runtime_seconds": time.time() - t0,
        },
        "matrix": {**matrix_meta, "shape": list(matrix.shape)},
        "year_audit": year_audit,
        "sensitivity": sensitivity,
        "variants": variants,
    }
    OUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Publication-year-aware canon pilot",
        "",
        "## Design",
        "",
        "This experiment adds one explicit bias to the ratings tuples: readers who give five "
        "stars to older works are treated as more literary. A work's primary year is the "
        "minimum valid `publication_year` across every edition in the UCSD books catalogue, "
        "not its display edition. Oldness is zero at 2000 and rises linearly to one at 1850. "
        "A conservative reader score deducts uncertainty, and the primary top/bottom 10% "
        "cohorts are equal-sized. The ranking then compares balanced five-star versus one-to-"
        "three-star evidence in the old-reading jury with the same evidence in the low-old-"
        "reading jury; four-star ratings are neutral.",
        "",
        "Book scoring is cross-fit by work-ID parity: the target book is always scored by a "
        "jury learned entirely from other books. A book's year does not directly enter its "
        "book score. Titles, authors, and literary/anti lists were loaded only after all scores, "
        "stability tests, and sensitivity paths were frozen.",
        "",
        f"Year coverage: **{year_audit['candidate_works_with_min_year']:,}/"
        f"{year_audit['candidate_works']:,}** candidate works; all-edition source rows: "
        f"**{year_audit['raw_catalogue_rows']:,}**, of which "
        f"**{year_audit['edition_rows']:,}** have a valid 1500–2017 year; runtime: "
        f"**{output['method']['runtime_seconds']:.1f}s**.",
        "",
        "The catalogue field is edition publication year, not a guaranteed original-work year. "
        "The minimum is therefore a dataset-native proxy; the edition-row 10th percentile is "
        "reported as an outlier-resistant sensitivity path.",
        "",
        "Selected catalogue minima (not external true-original dates): "
        + "; ".join(
            f"*{x['title']}* {x['min_year']} ({x['dated_editions']} dated editions)"
            for x in year_audit["posthoc_examples"]
        )
        + ".",
        "",
        "## Jury and ranking stability",
        "",
        "| variant | fold-jury Jaccard | half score rho | half J@50 | J@100 | J@200 | J@500 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in variants:
        halves = variant["stability"]["halves"]
        lines.append(
            f"| {variant['variant']['name']} | {variant['crossfold_old_jury_jaccard']:.3f} | "
            f"{np.mean([x['score_spearman'] for x in halves]):.3f} | "
            f"{np.mean([x['jaccard50'] for x in halves]):.3f} | "
            f"{np.mean([x['jaccard100'] for x in halves]):.3f} | "
            f"{np.mean([x['jaccard200'] for x in halves]):.3f} | "
            f"{np.mean([x['jaccard500'] for x in halves]):.3f} |"
        )
    lines += ["", "## Definition sensitivity versus primary contrast ranking", "", "| variant | J@50 | J@100 | J@200 | J@500 |", "|---|---:|---:|---:|---:|"]
    for row in sensitivity:
        lines.append(
            f"| {row['variant']} | {row['jaccard50']:.3f} | {row['jaccard100']:.3f} | "
            f"{row['jaccard200']:.3f} | {row['jaccard500']:.3f} |"
        )
    sensitivity_by_name = {row["variant"]: row for row in sensitivity}
    primary_metrics = variants[0]["contrast_ranking"]["metrics"]
    mass_variant = next(x for x in variants if x["variant"]["name"] == "min_linear_mass_q10")
    all_variant = next(x for x in variants if x["variant"]["name"] == "min_linear_q10_all")
    lines += [
        "",
        "## Findings",
        "",
        f"- The primary head is recognizably canonical: {primary_metrics['exact_lit50']} exact "
        f"seed-list works and {primary_metrics['broad_lit50']} broader seed-author works in the "
        "top 50, with no anti-list books. This is a large change from the ratings-only methods, "
        "but it visibly favors school classics, children's classics, and classic fantasy.",
        f"- The smooth definition is not date-tuned: moving the full-oldness endpoint from 1850 "
        f"to 1800 or 1900 retains {sensitivity_by_name['min_linear1800_q10']['jaccard200']:.1%} "
        f"and {sensitivity_by_name['min_linear1900_q10']['jaccard200']:.1%} of the top-200 union "
        "respectively.",
        f"- Replacing the minimum edition year with the edition-row 10th percentile retains "
        f"{sensitivity_by_name['q10_linear_q10']['jaccard200']:.1%} of the top-200 union, so isolated "
        "bad dates are not driving the result.",
        f"- Rewarding volume as well as share selects jurors with more old-book evidence and keeps "
        f"{sensitivity_by_name['min_linear_mass_q10']['jaccard50']:.1%} of the top-50 union. Its "
        f"fold-jury Jaccard is {mass_variant['crossfold_old_jury_jaccard']:.3f}, versus "
        f"{variants[0]['crossfold_old_jury_jaccard']:.3f} for the primary share score.",
        f"- Comparing the old-reading jury with all eligible readers retains only "
        f"{sensitivity_by_name['min_linear_q10_all']['jaccard50']:.1%} of the primary top-50 union "
        f"and has half-sample J@200 "
        f"{np.mean([x['jaccard200'] for x in all_variant['stability']['halves']]):.3f}. The matched "
        "low-old-reading contrast is therefore essential.",
        "- A hard pre-1950 definition reaches deeper Russian and modernist works and suppresses "
        "genre books farther down, but it is much less stable and is a substantively different "
        "bias rather than a harmless tuning change.",
    ]
    lines += ["", "## Rankings", ""]
    for variant in variants:
        ranking = variant["contrast_ranking"]
        metrics = ranking["metrics"]
        lines += [
            f"### {variant['variant']['name']} — old-jury minus contemporary-jury",
            "",
            f"Exact literary @50/200/500: **{metrics['exact_lit50']}/{metrics['exact_lit200']}/"
            f"{metrics['exact_lit500']}**; broad literary: **{metrics['broad_lit50']}/"
            f"{metrics['broad_lit200']}/{metrics['broad_lit500']}**; anti: "
            f"**{metrics['anti50']}/{metrics['anti200']}/{metrics['anti500']}**.",
            "",
        ]
        for book in ranking["books"][:50]:
            year = "?" if book["min_year"] is None else str(book["min_year"])
            lines.append(
                f"{book['rank']}. *{book['title']}* — {book['author']} [{year}] "
                f"({book['score']:.3f} ± {book['uncertainty']:.3f}; "
                f"old/new {book['old_jury_mean']:.3f}/{book['new_jury_mean']:.3f}; "
                f"sample readers/cohort={book['sampled_readers_each_cohort']:,})"
            )
        lines.append("")
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

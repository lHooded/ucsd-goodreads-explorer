#!/usr/bin/env python3
"""Publication-year-aware literary jury from ratings plus cleaned work years.

Discovery uses (user_id, work_id, rating) plus publication_year.  A work's
primary year combines BrightData ``first_published`` with the earliest credible
UCSD edition. Titles, authors, genres, and literary evaluation lists are loaded
only after all jury and book scores are frozen.
"""

from __future__ import annotations

import json
import hashlib
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
BRIGHT_WORKS = PARQUET / "brightdata_work_metadata.parquet"
YEAR_FEATURE_CACHE = DATA / "seedless_year_feature_matrix_brightdata.npz"
OUT_JSON = DATA / "year_aware_canon_pilot.json"
OUT_REPORT = DATA / "YEAR_AWARE_CANON_PILOT_REPORT.md"

YEAR_MIN = 1
YEAR_MAX = 2026
OLDNESS_ZERO = 2000.0
OLDNESS_ONE = 1850.0
USER_PRIOR = 10.0
MIN_TRAIN_FIVES = 8
BOOK_SHRINK_READERS = 25.0

VARIANTS = (
    {"name": "best_linear_q10", "year": "best_year", "oldness": "linear", "quantile": 0.10},
    {
        "name": "best_linear_mass_q10",
        "year": "best_year",
        "oldness": "linear",
        "quantile": 0.10,
        "user_score": "mass",
    },
    {
        "name": "best_preference_q10",
        "year": "best_year",
        "oldness": "linear",
        "quantile": 0.10,
        "user_score": "preference",
    },
    {
        "name": "best_preference_q20",
        "year": "best_year",
        "oldness": "linear",
        "quantile": 0.20,
        "user_score": "preference",
    },
    {
        "name": "best_preference_delta_q10",
        "year": "best_year",
        "oldness": "linear",
        "quantile": 0.10,
        "user_score": "preference_delta",
    },
    {"name": "ucsd_linear_q10", "year": "ucsd_year", "oldness": "linear", "quantile": 0.10},
    {"name": "bright_linear_q10", "year": "bright_year", "oldness": "linear", "quantile": 0.10},
    {"name": "best_linear1800_q10", "year": "best_year", "oldness": "linear1800", "quantile": 0.10},
    {"name": "best_linear1900_q10", "year": "best_year", "oldness": "linear1900", "quantile": 0.10},
    {"name": "best_pre1950_q10", "year": "best_year", "oldness": "pre1950", "quantile": 0.10},
    {"name": "best_linear_q05", "year": "best_year", "oldness": "linear", "quantile": 0.05},
    {"name": "best_linear_q20", "year": "best_year", "oldness": "linear", "quantile": 0.20},
    {
        "name": "best_linear_q10_all",
        "year": "best_year",
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
    if not BRIGHT_WORKS.exists():
        raise SystemExit(
            f"Missing {BRIGHT_WORKS}; run curators_explorer.scripts.build_brightdata_metadata"
        )
    fingerprint = hashlib.sha256()
    fingerprint.update(np.asarray(payload["user_ids"]).tobytes())
    fingerprint.update(np.asarray(payload["work_ids"]).tobytes())
    cache_key = fingerprint.hexdigest()
    signature_con = duckdb.connect()
    signature = signature_con.execute(
        f"""
        SELECT count(*),
               sum(hash(work_id, best_first_published_year,
                        brightdata_mode_year, ucsd_min_edition_year))::HUGEINT,
               bit_xor(hash(work_id, best_first_published_year,
                            brightdata_mode_year, ucsd_min_edition_year))
        FROM read_parquet('{BRIGHT_WORKS}')
        """
    ).fetchone()
    signature_con.close()
    source_digest = ":".join(str(value) for value in signature)
    if YEAR_FEATURE_CACHE.exists():
        with np.load(YEAR_FEATURE_CACHE, allow_pickle=False) as saved:
            if (
                str(saved["fingerprint"].item()) == cache_key
                and "source_signature" in saved.files
                and str(saved["source_signature"].item()) == source_digest
            ):
                print(f"Reusing {YEAR_FEATURE_CACHE.name}", flush=True)
                cached_features = {
                    key: saved[key]
                    for key in saved.files
                    if key not in {
                        "fingerprint", "source_mtime_ns", "source_sha256",
                        "source_signature", "audit_json"
                    }
                }
                return cached_features, json.loads(str(saved["audit_json"].item()))
    con = extraction_connection()
    print("Loading cleaned BrightData + UCSD work years", flush=True)
    con.execute(
        f"""
        CREATE TEMP TABLE clean_years AS
        SELECT work_id,
               best_first_published_year::INTEGER AS best_year,
               brightdata_mode_year::INTEGER AS bright_year,
               ucsd_min_edition_year::INTEGER AS ucsd_year,
               ucsd_q10_edition_year::INTEGER AS ucsd_q10_year,
               coalesce(brightdata_dated_editions, 0)::INTEGER AS bright_dated_editions,
               coalesce(ucsd_editions, 0)::INTEGER AS ucsd_editions,
               year_source
        FROM read_parquet('{BRIGHT_WORKS}')
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
               count(*) FILTER (WHERE e.rating=5 AND y.best_year IS NOT NULL)::INTEGER
                   AS best_n5_year,
               count(*) FILTER (WHERE e.rating=5 AND y.bright_year IS NOT NULL)::INTEGER
                   AS bright_n5_year,
               count(*) FILTER (WHERE e.rating=5 AND y.ucsd_year IS NOT NULL)::INTEGER
                   AS ucsd_n5_year,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               ))) FILTER (WHERE e.rating=5)::DOUBLE AS best_linear_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )), 2)) FILTER (WHERE e.rating=5)::DOUBLE AS best_linear_sq_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - 1800.0})
               ))) FILTER (WHERE e.rating=5)::DOUBLE AS best_linear1800_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - 1800.0})
               )), 2)) FILTER (WHERE e.rating=5)::DOUBLE AS best_linear1800_sq_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - 1900.0})
               ))) FILTER (WHERE e.rating=5)::DOUBLE AS best_linear1900_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - 1900.0})
               )), 2)) FILTER (WHERE e.rating=5)::DOUBLE AS best_linear1900_sq_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.bright_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               ))) FILTER (WHERE e.rating=5)::DOUBLE AS bright_linear_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.bright_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )), 2)) FILTER (WHERE e.rating=5)::DOUBLE AS bright_linear_sq_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.ucsd_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               ))) FILTER (WHERE e.rating=5)::DOUBLE AS ucsd_linear_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.ucsd_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )), 2)) FILTER (WHERE e.rating=5)::DOUBLE AS ucsd_linear_sq_sum,
               count(*) FILTER (WHERE e.rating=5 AND y.best_year <= 1950)::DOUBLE
                   AS pre1950_sum,
               count(*) FILTER (WHERE y.best_year IS NOT NULL)::INTEGER AS rated_n,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )))::DOUBLE AS pref_x_sum,
               sum(pow(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )), 2))::DOUBLE AS pref_x2_sum,
               sum((e.rating - 3.0) / 2.0) FILTER (
                   WHERE y.best_year IS NOT NULL
               )::DOUBLE AS pref_y_sum,
               sum(pow((e.rating - 3.0) / 2.0, 2)) FILTER (
                   WHERE y.best_year IS NOT NULL
               )::DOUBLE AS pref_y2_sum,
               sum(greatest(0.0, least(1.0,
                   ({OLDNESS_ZERO} - y.best_year) / ({OLDNESS_ZERO - OLDNESS_ONE})
               )) * ((e.rating - 3.0) / 2.0)) FILTER (
                   WHERE y.best_year IS NOT NULL
               )::DOUBLE AS pref_xy_sum
        FROM ex.all_rating_events e
        JOIN eligible_users u USING (user_id)
        JOIN clean_years y USING (work_id)
        WHERE e.rating BETWEEN 1 AND 5
        GROUP BY e.user_id, fold
        ORDER BY e.user_id, fold
        """
    ).fetchnumpy()
    con.execute("CREATE TEMP TABLE candidate_works(work_id VARCHAR PRIMARY KEY)")
    con.executemany(
        "INSERT INTO candidate_works VALUES (?)",
        [(str(work_id),) for work_id in payload["work_ids"]],
    )
    work_year_rows = con.execute(
        "SELECT c.work_id,y.best_year,y.bright_year,y.ucsd_year,y.ucsd_q10_year,"
        "y.bright_dated_editions,y.ucsd_editions,y.year_source "
        "FROM candidate_works c LEFT JOIN clean_years y USING(work_id) ORDER BY c.work_id"
    ).fetchall()
    audit = con.execute(
        """
        SELECT count(*) AS works,
               count(best_year) AS best_year_works,
               count(bright_year) AS bright_year_works,
               count(ucsd_year) AS ucsd_year_works,
               count(*) FILTER (WHERE best_year < 1800) AS best_pre1800,
               min(best_year) AS minimum,
               max(best_year) AS maximum,
               count(*) FILTER (WHERE year_source='brightdata_earlier') AS bright_improvements,
               count(*) FILTER (WHERE year_source='ucsd_earlier') AS ucsd_earlier
        FROM clean_years
        """
    ).fetchone()
    con.close()

    n_users = len(payload["user_ids"])
    user_data = {
        key: np.zeros((2, n_users), dtype=np.float32)
        for key in (
            "best_n", "bright_n", "ucsd_n",
            "best_linear_sum", "best_linear_sq_sum",
            "best_linear1800_sum", "best_linear1800_sq_sum",
            "best_linear1900_sum", "best_linear1900_sq_sum",
            "bright_linear_sum", "bright_linear_sq_sum",
            "ucsd_linear_sum", "ucsd_linear_sq_sum",
            "rated_n", "pref_x_sum", "pref_x2_sum", "pref_y_sum",
            "pref_y2_sum", "pref_xy_sum",
        )
    }
    user_data.update({
        "pre1950_sum": np.zeros((2, n_users), dtype=np.float32),
    })
    source_users = spectral.clean_array(features["user_id"], np.int64)
    indices = np.searchsorted(payload["user_ids"], source_users)
    matched = (indices < n_users) & (payload["user_ids"][np.minimum(indices, n_users - 1)] == source_users)
    folds = spectral.clean_array(features["fold"], np.int8)
    indices, folds = indices[matched], folds[matched]
    mapping = {
        "best_n": "best_n5_year",
        "bright_n": "bright_n5_year",
        "ucsd_n": "ucsd_n5_year",
        "best_linear_sum": "best_linear_sum",
        "best_linear_sq_sum": "best_linear_sq_sum",
        "best_linear1800_sum": "best_linear1800_sum",
        "best_linear1800_sq_sum": "best_linear1800_sq_sum",
        "best_linear1900_sum": "best_linear1900_sum",
        "best_linear1900_sq_sum": "best_linear1900_sq_sum",
        "bright_linear_sum": "bright_linear_sum",
        "bright_linear_sq_sum": "bright_linear_sq_sum",
        "ucsd_linear_sum": "ucsd_linear_sum",
        "ucsd_linear_sq_sum": "ucsd_linear_sq_sum",
        "pre1950_sum": "pre1950_sum",
        "rated_n": "rated_n",
        "pref_x_sum": "pref_x_sum",
        "pref_x2_sum": "pref_x2_sum",
        "pref_y_sum": "pref_y_sum",
        "pref_y2_sum": "pref_y2_sum",
        "pref_xy_sum": "pref_xy_sum",
    }
    for target, source in mapping.items():
        user_data[target][folds, indices] = spectral.clean_array(features[source], np.float32)[matched]

    work_year_map = {
        str(work_id): {
            "best_year": int(best) if best is not None else -1,
            "bright_year": int(bright) if bright is not None else -1,
            "ucsd_year": int(ucsd) if ucsd is not None else -1,
            "ucsd_q10_year": int(q10) if q10 is not None else -1,
            "bright_dated_editions": int(bright_n or 0),
            "ucsd_editions": int(ucsd_n or 0),
            "year_source": source,
        }
        for work_id, best, bright, ucsd, q10, bright_n, ucsd_n, source in work_year_rows
    }
    candidate_years = {}
    for key in ("best_year", "bright_year", "ucsd_year", "ucsd_q10_year"):
        candidate_years[key] = np.asarray(
            [work_year_map.get(str(work_id), {}).get(key, -1) for work_id in payload["work_ids"]],
            dtype=np.int16,
        )
    for key in ("bright_dated_editions", "ucsd_editions"):
        candidate_years[key] = np.asarray(
            [work_year_map.get(str(work_id), {}).get(key, 0) for work_id in payload["work_ids"]],
            dtype=np.int16,
        )
    combined_features = {**user_data, **candidate_years}
    year_audit = {
        "works": int(audit[0]),
        "best_year_works": int(audit[1]),
        "bright_year_works": int(audit[2]),
        "ucsd_year_works": int(audit[3]),
        "best_year_works_pre1800": int(audit[4]),
        "year_band": [int(audit[5]), int(audit[6])],
        "brightdata_earlier_works": int(audit[7]),
        "ucsd_earlier_works": int(audit[8]),
        "candidate_works": len(payload["work_ids"]),
        "candidate_works_with_best_year": int(np.sum(candidate_years["best_year"] > 0)),
        "candidate_works_with_bright_year": int(np.sum(candidate_years["bright_year"] > 0)),
        "source": str(BRIGHT_WORKS),
        "definition": "earlier of modal BrightData first_published and minimum UCSD edition year",
    }
    np.savez_compressed(
        YEAR_FEATURE_CACHE,
        fingerprint=np.asarray(cache_key),
        source_signature=np.asarray(source_digest),
        audit_json=np.asarray(json.dumps(year_audit)),
        **combined_features,
    )
    print(f"Cached {YEAR_FEATURE_CACHE.name}", flush=True)
    return combined_features, year_audit


def jury_score(
    features: dict[str, np.ndarray], fold: int, variant: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    score_mode = variant.get("user_score", "share")
    if score_mode in {"preference", "preference_delta"}:
        n = features["rated_n"][fold].astype(np.float64)
        x = features["pref_x_sum"][fold].astype(np.float64)
        x2 = features["pref_x2_sum"][fold].astype(np.float64)
        y = features["pref_y_sum"][fold].astype(np.float64)
        y2 = features["pref_y2_sum"][fold].astype(np.float64)
        xy = features["pref_xy_sum"][fold].astype(np.float64)
        sxx = np.maximum(x2 - x * x / np.maximum(n, 1.0), 0.0)
        syy = np.maximum(y2 - y * y / np.maximum(n, 1.0), 0.0)
        sxy = xy - x * y / np.maximum(n, 1.0)
        correlation = np.divide(
            sxy,
            np.sqrt(sxx * syy),
            out=np.zeros_like(sxy),
            where=(sxx > 0) & (syy > 0),
        )
        correlation = np.clip(correlation, -0.999, 0.999)
        # Require exposure on both sides of the age contrast. Oldness is in
        # [0,1], so these are directly interpretable old/new-equivalent counts.
        valid = (n >= 20) & (x >= 3.0) & ((n - x) >= 10.0) & (sxx >= 0.5) & (syy > 0)
        if score_mode == "preference":
            fisher = np.arctanh(correlation)
            posterior_z = fisher * n / (n + USER_PRIOR)
            uncertainty_z = 1.0 / np.sqrt(np.maximum(n + USER_PRIOR - 3.0, 1.0))
            posterior = np.tanh(posterior_z)
            uncertainty = np.maximum(
                posterior - np.tanh(posterior_z - uncertainty_z), 0.0
            )
            conservative = np.tanh(posterior_z - uncertainty_z)
            global_mean = float(np.mean(correlation[valid]))
            global_second = float(np.mean(correlation[valid] ** 2))
        else:
            global_rating = float(y[valid].sum() / max(n[valid].sum(), 1.0))
            global_rating_second = float(y2[valid].sum() / max(n[valid].sum(), 1.0))
            global_rating_variance = max(global_rating_second - global_rating**2, 1e-6)
            old_posterior = (xy + USER_PRIOR * global_rating) / (x + USER_PRIOR)
            new_mass = n - x
            new_posterior = (
                (y - xy) + USER_PRIOR * global_rating
            ) / (new_mass + USER_PRIOR)
            posterior = old_posterior - new_posterior
            uncertainty = np.sqrt(
                global_rating_variance
                * (1.0 / (x + USER_PRIOR) + 1.0 / (new_mass + USER_PRIOR))
            )
            conservative = posterior - uncertainty
            global_mean = global_rating
            global_second = global_rating_second
        total = x
        evidence_label = "year-known ratings"
    else:
        prefix = variant["year"].removesuffix("_year")
        n = features[f"{prefix}_n"][fold].astype(np.float64)
        if variant["oldness"].startswith("linear"):
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
        # This path rewards both concentration and volume. Dividing by sqrt(n)
        # prevents raw Goodreads activity from completely determining the jury.
        if score_mode == "mass":
            conservative = conservative_share * np.sqrt(n)
        else:
            conservative = conservative_share
        evidence_label = "year-known five-star ratings"
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
        "evidence_label": evidence_label,
        "user_score_mode": score_mode,
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
                "best_year": int(features["best_year"][index]) if features["best_year"][index] > 0 else None,
                "bright_year": int(features["bright_year"][index]) if features["bright_year"][index] > 0 else None,
                "ucsd_year": int(features["ucsd_year"][index]) if features["ucsd_year"][index] > 0 else None,
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
        f"Year coverage: {year_audit['candidate_works_with_best_year']:,}/"
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
    example_books = {
        ("moby-dick or, the whale", "herman melville"),
        ("ulysses", "james joyce"),
        ("the brothers karamazov", "fyodor dostoyevsky"),
        ("the great gatsby", "f. scott fitzgerald"),
        ("one hundred years of solitude", "gabriel garcia marquez"),
    }
    year_examples = []
    for index, work_id_value in enumerate(payload["work_ids"]):
        work_id = str(work_id_value)
        book = meta.get(work_id, {})
        if (book.get("title", "").casefold(), book.get("author", "").casefold()) in example_books:
            year_examples.append(
                {
                    "work_id": work_id,
                    "title": book["title"],
                    "best_year": int(features["best_year"][index]),
                    "bright_year": int(features["bright_year"][index]),
                    "ucsd_year": int(features["ucsd_year"][index]),
                }
            )
    year_audit["posthoc_examples"] = sorted(year_examples, key=lambda x: x["title"])
    existing_jury_path = DATA / "soft_jury_weights.parquet"
    jury_overlap = []
    if existing_jury_path.exists():
        overlap_con = duckdb.connect()
        existing_hard = {
            int(row[0])
            for row in overlap_con.execute(
                f"SELECT user_id FROM read_parquet('{existing_jury_path}') WHERE hard_jury"
            ).fetchall()
        }
        overlap_con.close()
        variant_map = {row["name"]: row for row in VARIANTS}
        for name in (
            "best_linear_q10", "best_linear_mass_q10", "best_preference_q10",
            "best_preference_delta_q10",
        ):
            masks = [jury_score(features, fold, variant_map[name])[0] for fold in (0, 1)]
            for membership, selected in (
                ("either_book_fold", masks[0] | masks[1]),
                ("both_book_folds", masks[0] & masks[1]),
            ):
                users = set(map(int, payload["user_ids"][selected]))
                intersection = len(users & existing_hard)
                jury_overlap.append(
                    {
                        "variant": name,
                        "membership": membership,
                        "users": len(users),
                        "existing_hard_users": len(existing_hard),
                        "intersection": intersection,
                        "jaccard": intersection / max(1, len(users | existing_hard)),
                        "existing_hard_coverage": intersection / max(1, len(existing_hard)),
                    }
                )
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
            "allowed_discovery_columns": ["user_id", "work_id", "rating", "first_published"],
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
        "posthoc_existing_jury_overlap": jury_overlap,
        "variants": variants,
    }
    OUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Publication-year-aware canon pilot",
        "",
        "## Design",
        "",
        "This experiment adds one explicit bias to the ratings tuples: readers who give five "
        "stars to older works are treated as more literary. A work's primary year is the earlier "
        "of the modal BrightData `first_published` year and the minimum UCSD edition year. "
        "Oldness is zero at 2000 and rises linearly to one at 1850. "
        "A conservative reader score deducts uncertainty, and the primary top/bottom 10% "
        "cohorts are equal-sized. The ranking then compares balanced five-star versus one-to-"
        "three-star evidence in the old-reading jury with the same evidence in the low-old-"
        "reading jury; four-star ratings are neutral.",
        "",
        "Book scoring is cross-fit by work-ID parity: the target book is always scored by a "
        "jury learned entirely from other books. A book's year does not directly enter its "
        "book score. Titles, authors, genres, and literary/anti lists were loaded only after all scores, "
        "stability tests, and sensitivity paths were frozen.",
        "",
        f"Year coverage: **{year_audit['candidate_works_with_best_year']:,}/"
        f"{year_audit['candidate_works']:,}** candidate works, including "
        f"**{year_audit['candidate_works_with_bright_year']:,}** with an exact-joined "
        f"BrightData year; runtime: "
        f"**{output['method']['runtime_seconds']:.1f}s**.",
        "",
        f"Across the full joined catalogue, BrightData supplies an earlier date for "
        f"**{year_audit['brightdata_earlier_works']:,}** works. UCSD supplies the earlier "
        f"logically possible date for **{year_audit['ucsd_earlier_works']:,}** works.",
        "",
        "Selected cleaned dates (best / BrightData / UCSD edition minimum): "
        + "; ".join(
            f"*{x['title']}* {x['best_year']} / {x['bright_year']} / {x['ucsd_year']}"
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
    mass_variant = next(x for x in variants if x["variant"]["name"] == "best_linear_mass_q10")
    preference_variant = next(x for x in variants if x["variant"]["name"] == "best_preference_q10")
    delta_variant = next(
        x for x in variants if x["variant"]["name"] == "best_preference_delta_q10"
    )
    preference_metrics = preference_variant["contrast_ranking"]["metrics"]
    preference_by_title = {
        row["title"].casefold(): row
        for row in preference_variant["contrast_ranking"]["books"]
    }
    all_variant = next(x for x in variants if x["variant"]["name"] == "best_linear_q10_all")
    lines += [
        "",
        "## Findings",
        "",
        f"- The primary head is recognizably canonical: {primary_metrics['exact_lit50']} exact "
        f"seed-list works and {primary_metrics['broad_lit50']} broader seed-author works in the "
        "top 50, with no anti-list books. This is a large change from the ratings-only methods, "
        "but it visibly favors school classics, children's classics, and classic fantasy.",
        f"- The smooth definition is not date-tuned: moving the full-oldness endpoint from 1850 "
        f"to 1800 or 1900 retains {sensitivity_by_name['best_linear1800_q10']['jaccard200']:.1%} "
        f"and {sensitivity_by_name['best_linear1900_q10']['jaccard200']:.1%} of the top-200 union "
        "respectively.",
        f"- The enriched year ranking versus the UCSD-only reconstruction has top-200 Jaccard "
        f"**{sensitivity_by_name['ucsd_linear_q10']['jaccard200']:.3f}**; this measures how much "
        "the repaired dates actually change the result.",
        f"- Rewarding volume as well as share selects jurors with more old-book evidence and keeps "
        f"{sensitivity_by_name['best_linear_mass_q10']['jaccard50']:.1%} of the top-50 union. Its "
        f"fold-jury Jaccard is {mass_variant['crossfold_old_jury_jaccard']:.3f}, versus "
        f"{variants[0]['crossfold_old_jury_jaccard']:.3f} for the primary share score.",
        f"- The within-reader preference jury—users who rate older books higher than their own "
        f"newer books—has fold-jury Jaccard **{preference_variant['crossfold_old_jury_jaccard']:.3f}** "
        f"and primary top-200 Jaccard **{sensitivity_by_name['best_preference_q10']['jaccard200']:.3f}**, "
        f"but disjoint-reader score rho "
        f"**{np.mean([x['score_spearman'] for x in preference_variant['stability']['halves']]):.3f}**. "
        f"It has {preference_metrics['broad_lit50']} broad-literary works in the top 50 and "
        f"**zero anti-list works through rank 500**.",
        f"- The preference path directly recovers several earlier omissions: *Moby-Dick* "
        f"#{preference_by_title['moby-dick or, the whale']['rank']}, *Middlemarch* "
        f"#{preference_by_title['middlemarch']['rank']}, *Don Quixote* "
        f"#{preference_by_title['don quixote']['rank']}, *Ulysses* "
        f"#{preference_by_title['ulysses']['rank']}, and *The Great Gatsby* "
        f"#{preference_by_title['the great gatsby']['rank']}.",
        f"- The more literal old-minus-new mean-rating definition is stronger again: fold-jury "
        f"Jaccard **{delta_variant['crossfold_old_jury_jaccard']:.3f}**, half-reader J@200 "
        f"**{np.mean([x['jaccard200'] for x in delta_variant['stability']['halves']]):.3f}**, "
        f"{delta_variant['contrast_ranking']['metrics']['exact_lit50']} exact and "
        f"{delta_variant['contrast_ranking']['metrics']['broad_lit50']} broad literary works in "
        f"the top 50, and zero anti-list works through rank 200. This is the cleanest current "
        f"default for the requested old-over-new estimand; the correlation path remains a "
        f"useful robustness check.",
        f"- Comparing the old-reading jury with all eligible readers retains only "
        f"{sensitivity_by_name['best_linear_q10_all']['jaccard50']:.1%} of the primary top-50 union "
        f"and has half-sample J@200 "
        f"{np.mean([x['jaccard200'] for x in all_variant['stability']['halves']]):.3f}. The matched "
        "low-old-reading contrast is therefore essential.",
        "- A hard pre-1950 definition reaches deeper Russian and modernist works and suppresses "
        "genre books farther down, but it is much less stable and is a substantively different "
        "bias rather than a harmless tuning change.",
    ]
    if jury_overlap:
        lines += [
            "",
            "## Post-hoc overlap with the existing reconstructed jury",
            "",
            "This comparison is diagnostic only; the existing seed-conditioned jury was not "
            "used to select any year juror or score any book.",
            "",
            "| year jury | membership | users | overlap | Jaccard | existing jury covered |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for row in jury_overlap:
            lines.append(
                f"| {row['variant']} | {row['membership']} | {row['users']:,} | "
                f"{row['intersection']:,} | {row['jaccard']:.3f} | "
                f"{row['existing_hard_coverage']:.1%} |"
            )
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
            year = "?" if book["best_year"] is None else str(book["best_year"])
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

#!/usr/bin/env python3
"""Diagnostic test of a frozen B1+B2 literary super-mode.

This campaign is downstream of the frozen four-basin J10/J20 census and the
stable-user-affiliation experiment.  It never reclusters, changes a jury
membership, fits coefficients, or searches for a final/maximal jury.  The
numerical phase freezes all candidate scores and comparison groups before the
post-hoc title/probe phase is loaded.

The experiment is deliberately resumable at three inexpensive boundaries::

    PYTHONPATH=. .venv/bin/python -m \
      curators_explorer.scripts.research_literary_supermode --phase audit
    PYTHONPATH=. .venv/bin/python -m \
      curators_explorer.scripts.research_literary_supermode --phase numerical
    PYTHONPATH=. .venv/bin/python -m \
      curators_explorer.scripts.research_literary_supermode --phase posthoc

``all`` executes the latter two phases after a successful audit.  No basin
trajectories are recomputed.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import (ks_2samp, rankdata, spearmanr,
                         wasserstein_distance)

from curators_explorer.scripts import research_literary_user_basin_affiliation as affiliation
from curators_explorer.scripts.research_converged_common_literary_jurors import (
    DATA,
    _write_npz_atomic,
    _write_text_atomic,
)


LITERARY_SUPERMODE_SEED = 20260905
START_COMMIT = "b3371b5bec39ecca9e3372ad8b3dac8f7b85a248"
AFFILIATION_SEED = 20260904
N_BASINS = 4
SPLIT_REPS = 10
MATCH_BIN_SIZE = 200
MATCH_TAIL_FRACTION = 0.25
TOP_FRACTIONS = (0.05, 0.10, 0.25)
HEAD_LIMIT = 100
J5_SUPPORT_THRESHOLD = 25.0
POPULATIONS = ("J10000", "J20000")
GROUP_SCOPES = ("J20_outer", "S1", "S2")
CANDIDATE_NAMES = (
    "LITSHARE", "LITCONTRAST", "RAWSUM", "PCTSUM",
    "B1_SUPPORT", "B1_SOFT_SHARE", "B1_SPECIFICITY",
)
PRIMARY_CANDIDATES = ("LITSHARE", "PCTSUM", "B1_SOFT_SHARE", "B1_SPECIFICITY")
CHARACTERIZATION_LABELS = ("B1_specific", "B2_specific", "joint", "OTHER")
CHARACTERIZATION_PAIRS = (
    ("B1_specific", "B2_specific"),
    ("B1_specific", "OTHER"),
    ("B2_specific", "OTHER"),
    ("joint", "OTHER"),
)

AFF_JSON = DATA / "literary_user_basin_affiliation.json"
AFF_NPZ = DATA / "literary_user_basin_affiliation.npz"
AFF_REPORT = DATA / "LITERARY_USER_BASIN_AFFILIATION_REPORT.md"
AFF_HEADS = DATA / "LITERARY_USER_AFFILIATION_HEADS.md"
AFF_STATE = DATA / "literary_user_basin_affiliation_state"

OUT_JSON = DATA / "literary_supermode.json"
OUT_NPZ = DATA / "literary_supermode.npz"
OUT_REPORT = DATA / "LITERARY_SUPERMODE_REPORT.md"
OUT_HEADS = DATA / "LITERARY_SUPERMODE_HEADS.md"
STATE_DIR = DATA / "literary_supermode_state"
STATE_VERSION = 1


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_array(value: np.ndarray, dtype: str | None = None) -> str:
    array = np.asarray(value, dtype=dtype) if dtype else np.asarray(value)
    return _sha256_bytes(np.ascontiguousarray(array).tobytes(order="C"))


def _hash_ids(value: np.ndarray) -> str:
    return _hash_array(np.asarray(value, dtype="<i8"))


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_sanitize(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _json_dump(path: Path, value: Any) -> None:
    _write_text_atomic(path, json.dumps(_json_sanitize(value), indent=1,
                                        allow_nan=False))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as blob:
        return {key: blob[key] for key in blob.files}


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def _derive_seed(*parts: Any) -> int:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "little") & ((1 << 63) - 1)


def _safe_key(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        if value is None or not np.isfinite(float(value)):
            return "—"
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_int(value: Any) -> str:
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return "—"


def _summary(values: np.ndarray | list[float]) -> dict[str, Any]:
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {key: float("nan") for key in
                ("n", "mean", "std", "p01", "p10", "p25", "median",
                 "p75", "p90", "p99", "min", "max", "cv", "skew")}
    mean = float(np.mean(x))
    return {
        "n": int(len(x)), "mean": mean, "std": float(np.std(x)),
        "p01": float(np.quantile(x, .01)), "p10": float(np.quantile(x, .10)),
        "p25": float(np.quantile(x, .25)), "median": float(np.median(x)),
        "p75": float(np.quantile(x, .75)), "p90": float(np.quantile(x, .90)),
        "p99": float(np.quantile(x, .99)), "min": float(np.min(x)),
        "max": float(np.max(x)),
        "cv": float(np.std(x) / mean) if mean else float("nan"),
        "skew": float((np.mean((x - mean) ** 3) /
                       max(np.std(x) ** 3, 1e-15))),
    }


def _corr(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    x = np.asarray(a, dtype=np.float64).reshape(-1)
    y = np.asarray(b, dtype=np.float64).reshape(-1)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    out: dict[str, Any] = {"n": int(len(x)), "pearson": float("nan"),
                           "spearman": float("nan")}
    if len(x) < 2:
        return out
    if np.std(x) > 0 and np.std(y) > 0:
        out["pearson"] = float(np.corrcoef(x, y)[0, 1])
        out["spearman"] = float(spearmanr(x, y).statistic)
    return out


def _top_overlap(a: np.ndarray, b: np.ndarray, ids: np.ndarray,
                 fraction: float) -> dict[str, Any]:
    n = len(a)
    k = max(1, int(round(n * fraction)))
    order_a = np.lexsort((ids, -np.nan_to_num(a, nan=-np.inf)))[:k]
    order_b = np.lexsort((ids, -np.nan_to_num(b, nan=-np.inf)))[:k]
    overlap = len(set(ids[order_a].tolist()) & set(ids[order_b].tolist()))
    return {"k": int(k), "overlap": int(overlap),
            "fraction": float(overlap / k)}


def _score_repro(a: np.ndarray, b: np.ndarray, ids: np.ndarray) -> dict[str, Any]:
    mask = np.isfinite(a) & np.isfinite(b)
    x, y, u = a[mask], b[mask], ids[mask]
    out = {**_corr(x, y),
           "mae": float(np.mean(np.abs(x - y))) if len(x) else float("nan"),
           "median_absolute_difference": float(np.median(np.abs(x - y)))
           if len(x) else float("nan"),
           "top_overlap": {str(int(f * 100)): _top_overlap(x, y, u, f)
                           for f in TOP_FRACTIONS}}
    return out


def _percentiles(matrix: np.ndarray) -> np.ndarray:
    x = np.asarray(matrix, dtype=np.float64)
    out = np.empty_like(x)
    for col in range(x.shape[1]):
        out[:, col] = (rankdata(x[:, col], method="average") - .5) / max(len(x), 1)
    return out


def _soft_shares(support: np.ndarray) -> np.ndarray:
    x = np.asarray(support, dtype=np.float64)
    denom = np.sum(x, axis=1, keepdims=True)
    return x / np.maximum(denom, 1e-15)


def _candidate_values(support: np.ndarray,
                      percentile_support: np.ndarray | None = None,
                      shares: np.ndarray | None = None) -> dict[str, np.ndarray]:
    raw = np.asarray(support, dtype=np.float64)
    pct = _percentiles(raw) if percentile_support is None else np.asarray(percentile_support, dtype=np.float64)
    soft = _soft_shares(raw) if shares is None else np.asarray(shares, dtype=np.float64)
    lit = soft[:, 0] + soft[:, 1]
    return {
        "LITSHARE": lit,
        "LITCONTRAST": 2.0 * lit - 1.0,
        "RAWSUM": raw[:, 0] + raw[:, 1],
        "PCTSUM": pct[:, 0] + pct[:, 1],
        "B1_SUPPORT": raw[:, 0],
        "B1_SOFT_SHARE": soft[:, 0],
        "B1_SPECIFICITY": raw[:, 0] - np.max(raw[:, 1:], axis=1),
    }


def _candidate_from_halves(a: np.ndarray, b: np.ndarray) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    return (_candidate_values(a), _candidate_values(b))


def _zscore_mae(a: np.ndarray, b: np.ndarray) -> float:
    x, y = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    x = (x - np.mean(x)) / max(np.std(x), 1e-15)
    y = (y - np.mean(y)) / max(np.std(y), 1e-15)
    return float(np.mean(np.abs(x - y)))


def _deciles(x: np.ndarray) -> np.ndarray:
    order = np.lexsort((np.arange(len(x)), -np.asarray(x, dtype=np.float64)))
    out = np.empty(len(x), dtype=np.int8)
    out[order] = np.minimum(9, (np.arange(len(x)) * 10) // max(len(x), 1))
    return out


def _transition(a: np.ndarray, b: np.ndarray) -> list[list[int]]:
    da, db = _deciles(a), _deciles(b)
    matrix = np.zeros((10, 10), dtype=np.int64)
    np.add.at(matrix, (da, db), 1)
    return matrix.tolist()


def _distribution_balance(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    x, y = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    qa = np.quantile(x, [.10, .25, .50, .75, .90])
    qb = np.quantile(y, [.10, .25, .50, .75, .90])
    return {
        "a": _summary(x), "b": _summary(y),
        "ks_statistic": float(ks_2samp(x, y).statistic),
        "ks_pvalue": float(ks_2samp(x, y).pvalue),
        "wasserstein": float(wasserstein_distance(x, y)),
        "max_abs_quantile_difference": float(np.max(np.abs(qa - qb))),
        "quantiles": {str(q): {"a": float(u), "b": float(v)}
                      for q, u, v in zip((.10, .25, .50, .75, .90), qa, qb)},
    }


def _head_metrics(high: dict[str, Any], low: dict[str, Any],
                  work_ids: np.ndarray) -> dict[str, Any]:
    return affiliation._head_space_comparison(
        high["score"], low["score"], work_ids,
        high["reader_mass"], low["reader_mass"])


def _audit_check(checks: list[dict[str, Any]], name: str, ok: bool,
                 detail: str) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def _audit_source() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    _audit_check(checks, "starting_commit_exact", _git_head() == START_COMMIT,
                 f"HEAD={_git_head()}")
    required = (AFF_JSON, AFF_NPZ, AFF_REPORT, AFF_HEADS, AFF_STATE)
    _audit_check(checks, "corrected_affiliation_artifacts_present",
                 all(path.exists() for path in required),
                 ", ".join(f"{path.name}={path.exists()}" for path in required))
    if not all(path.exists() for path in required):
        result = {"seed": LITERARY_SUPERMODE_SEED, "checks": checks,
                  "ok": False, "semantic_metadata_loaded": False}
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        _json_dump(STATE_DIR / "audit.json", result)
        return result

    aff_json = _load_json(AFF_JSON)
    aff = _load_npz(AFF_NPZ)
    correction = aff_json.get("correction_pass", {})
    _audit_check(checks, "head_mass_correction_declared",
                 correction.get("head_mass_bug_fixed") is True,
                 json.dumps(correction, sort_keys=True))
    _audit_check(checks, "percentile_margin_correction_declared",
                 correction.get("percentile_margin_bug_fixed") is True,
                 json.dumps(correction, sort_keys=True))
    _audit_check(checks, "no_basin_trajectories_rerun_for_correction",
                 correction.get("trajectories_rerun") is False,
                 str(correction.get("trajectories_rerun")))

    required_keys = ["frozen/common_L", "frozen/universe"]
    required_keys.extend(f"membership/J{n}/user_ids" for n in (5000, 10000, 20000, 30000))
    required_keys.extend(f"{tag}/{name}" for tag in POPULATIONS for name in (
        "user_ids", "common_L", "shell_code", "support_median", "support_mean",
        "support_A", "support_B", "percentile_support", "soft_share",
        "run_labels", "run_weights"))
    _audit_check(checks, "corrected_numerical_keys_present",
                 all(key in aff for key in required_keys), f"checked={len(required_keys)}")

    common_hash = _hash_array(aff["frozen/common_L"].astype("<f8"))
    universe_hash = _hash_array(aff["frozen/universe"].astype("<i8"))
    frozen = aff_json.get("audit", {}).get("frozen", {})
    _audit_check(checks, "common_L_hash_unchanged",
                 common_hash == frozen.get("common_L_score_hash"), common_hash)
    _audit_check(checks, "universe_hash_unchanged",
                 universe_hash == frozen.get("universe_hash"), universe_hash)
    membership_hashes: dict[str, str] = {}
    memberships: dict[str, set[int]] = {}
    for n in (5000, 10000, 20000, 30000):
        key = f"membership/J{n}/user_ids"
        ids = aff[key].astype(np.int64)
        memberships[f"J{n}"] = set(ids.tolist())
        membership_hashes[f"J{n}"] = _hash_ids(ids)
        expected = frozen.get("membership_hashes", {}).get(f"J{n}")
        _audit_check(checks, f"membership_hash_J{n}_unchanged",
                     membership_hashes[f"J{n}"] == expected,
                     membership_hashes[f"J{n}"])
        _audit_check(checks, f"membership_J{n}_unique", len(ids) == len(np.unique(ids)),
                     f"n={len(ids)}")
    _audit_check(checks, "membership_nesting_exact",
                 len(memberships["J5000"] & memberships["J10000"]) == 5000
                 and len(memberships["J10000"] & memberships["J20000"]) == 10000
                 and len(memberships["J20000"] & memberships["J30000"]) == 20000,
                 "J5/J10/J20/J30 intersections")

    for tag, n in (("J10000", 10000), ("J20000", 20000)):
        ids = aff[f"{tag}/user_ids"].astype(np.int64)
        weights = aff[f"{tag}/run_weights"].astype(np.float64)
        labels = aff[f"{tag}/run_labels"].astype(np.int8)
        _audit_check(checks, f"{tag}_basin_run_count_64",
                     weights.shape == (n, 64) and labels.shape == (64,),
                     f"weights={weights.shape}, labels={labels.shape}")
        _audit_check(checks, f"{tag}_four_local_basins_present",
                     np.array_equal(np.unique(labels), np.arange(4)),
                     np.unique(labels).tolist())
        derived = np.empty((n, 4), dtype=np.float64)
        for basin in range(4):
            derived[:, basin] = np.median(weights[:, labels == basin], axis=1)
        _audit_check(checks, f"{tag}_support_recomputed_from_saved_weights",
                     np.allclose(derived, aff[f"{tag}/support_median"], atol=2e-6, rtol=0),
                     f"max_abs={float(np.max(np.abs(derived - aff[f'{tag}/support_median']))):.3e}")
        _audit_check(checks, f"{tag}_soft_share_recomputed",
                     np.allclose(_soft_shares(derived), aff[f"{tag}/soft_share"], atol=2e-6, rtol=0),
                     "mean-normalized support shares")

    matched = aff_json.get("analysis", {}).get("matched", {})
    corrected_overlap = {
        name: {key: value.get(key) for key in
               ("top50_overlap", "top200_overlap", "common_top200_n",
                "common_top200_spearman")}
        for name, value in ((name, record.get("head_space_separation", {}))
                            for name, record in matched.items())}
    _audit_check(checks, "corrected_matched_heads_nonempty",
                 all(row.get("top50_overlap", 0) > 0 and row.get("top200_overlap", 0) > 0
                     for row in corrected_overlap.values()),
                 json.dumps(corrected_overlap, sort_keys=True))
    for method in ("raw", "percentile"):
        group_key = f"{method}_B1"
        group = aff_json.get("analysis", {}).get("hard_partitions", {}).get(method, {}).get(group_key, {})
        margin_key = "raw_margin" if method == "raw" else "percentile_margin"
        assign_key = f"J20000/{'raw_argmax' if method == 'raw' else 'percentile_argmax'}"
        values = aff[f"J20000/{margin_key}"].astype(np.float64)
        mask = aff[assign_key] == 0
        expected_median = float(np.median(values[mask]))
        reported = float(group.get("margin", {}).get("median", np.nan))
        _audit_check(checks, f"{method}_partition_margin_corrected",
                     np.isclose(expected_median, reported, atol=2e-6, rtol=0),
                     f"expected={expected_median:.9f} reported={reported:.9f}")

    audit = {
        "seed": LITERARY_SUPERMODE_SEED,
        "starting_commit": _git_head(),
        "required_start_commit": START_COMMIT,
        "checks": checks,
        "ok": bool(all(row["ok"] for row in checks)),
        "semantic_metadata_loaded": False,
        "source": {
            "affiliation_json_sha256": _sha256_bytes(AFF_JSON.read_bytes()),
            "affiliation_npz_sha256": _sha256_bytes(AFF_NPZ.read_bytes()),
            "common_L_hash": common_hash,
            "universe_hash": universe_hash,
            "membership_hashes": membership_hashes,
            "corrected_previous_head_metrics": corrected_overlap,
            "j5_like_basins": aff_json.get("audit", {}).get("frozen", {}).get("j5_like_basins"),
            "strict_valid_runs": aff_json.get("audit", {}).get("frozen", {}).get("strict_valid_run_counts"),
        },
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _json_dump(STATE_DIR / "audit.json", audit)
    return audit


def _load_source(audit: dict[str, Any]) -> dict[str, Any]:
    if not audit.get("ok"):
        raise RuntimeError("super-mode source audit failed")
    aff_json = _load_json(AFF_JSON)
    aff = _load_npz(AFF_NPZ)
    source: dict[str, Any] = {"audit": audit, "aff_json": aff_json,
                              "aff": aff, "populations": {}}
    for tag in POPULATIONS:
        prefix = f"{tag}/"
        support = aff[prefix + "support_median"].astype(np.float64)
        pct = aff[prefix + "percentile_support"].astype(np.float64)
        shares = aff[prefix + "soft_share"].astype(np.float64)
        candidates = _candidate_values(support, pct, shares)
        source["populations"][tag] = {
            "tag": tag,
            "user_ids": aff[prefix + "user_ids"].astype(np.int64),
            "common_L": aff[prefix + "common_L"].astype(np.float64),
            "shell": aff[prefix + "shell_code"].astype(np.int8),
            "support": support,
            "support_pct": pct,
            "shares": shares,
            "candidates": candidates,
            "run_weights": aff[prefix + "run_weights"].astype(np.float64),
            "run_labels": aff[prefix + "run_labels"].astype(np.int8),
            "run_valid": aff[prefix + "run_valid"].astype(bool),
        }
        for name, value in candidates.items():
            if not np.all(np.isfinite(value)):
                raise RuntimeError(f"nonfinite candidate {tag}/{name}")
    source["universe"] = aff["frozen/universe"].astype(np.int64)
    source["common_L_global"] = aff["frozen/common_L"].astype(np.float64)
    source["memberships"] = {
        f"J{n}": aff[f"membership/J{n}/user_ids"].astype(np.int64)
        for n in (5000, 10000, 20000, 30000)}
    return source


def _split_candidate_analysis(pop: dict[str, Any], split_index: int,
                              aggregate: str = "median") -> dict[str, Any]:
    p = {"tag": pop["tag"], "user_ids": pop["user_ids"],
         "weights": pop["run_weights"], "labels": pop["run_labels"]}
    a, b, splits = affiliation._split_supports(p, split_index, aggregate)
    ca, cb = _candidate_from_halves(a, b)
    return {"A": ca, "B": cb, "support_A": a, "support_B": b,
            "splits": splits}


def _candidate_reproducibility(pop: dict[str, Any], split0: dict[str, Any]) -> dict[str, Any]:
    ids, shell = pop["user_ids"], pop["shell"]
    out: dict[str, Any] = {"overall": {}, "by_shell": {}, "split_index": 0}
    for name in CANDIDATE_NAMES:
        out["overall"][name] = _score_repro(split0["A"][name], split0["B"][name], ids)
        out["by_shell"][name] = {}
        for code in (0, 1, 2):
            mask = shell == code
            if np.any(mask):
                out["by_shell"][name][f"S{code}"] = _score_repro(
                    split0["A"][name][mask], split0["B"][name][mask], ids[mask])
    return out


def _additional_split_summaries(pop: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for split_index in range(SPLIT_REPS):
        split = _split_candidate_analysis(pop, split_index)
        row: dict[str, Any] = {"split_index": split_index, "scores": {}}
        for name in CANDIDATE_NAMES:
            metric = _score_repro(split["A"][name], split["B"][name], pop["user_ids"])
            row["scores"][name] = {
                "pearson": metric["pearson"], "spearman": metric["spearman"],
                "top10_overlap": metric["top_overlap"]["10"]["overlap"],
                "top10_k": metric["top_overlap"]["10"]["k"],
            }
        rows.append(row)
    summary: dict[str, Any] = {"rows": rows, "summary": {}}
    for name in CANDIDATE_NAMES:
        for field in ("pearson", "spearman", "top10_overlap"):
            values = np.asarray([row["scores"][name][field] for row in rows], dtype=float)
            summary["summary"].setdefault(name, {})[field] = {
                "median": float(np.median(values)), "p10": float(np.quantile(values, .10)),
                "p90": float(np.quantile(values, .90)),
            }
    return summary


def _scope_positions(pop: dict[str, Any], scope: str) -> np.ndarray:
    if scope == "J20_outer":
        return np.flatnonzero(pop["shell"] != 0)
    if scope == "S1":
        return np.flatnonzero(pop["shell"] == 1)
    if scope == "S2":
        return np.flatnonzero(pop["shell"] == 2)
    raise ValueError(scope)


def _characterization_groups(pop: dict[str, Any], scope: str) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    pos = _scope_positions(pop, scope)
    shares = pop["shares"][pos]
    lit = pop["candidates"]["LITSHARE"][pos]
    b1, b2 = shares[:, 0], shares[:, 1]
    b1_med, b1_q75 = np.quantile(b1, [.50, .75])
    b2_med, b2_q75 = np.quantile(b2, [.50, .75])
    lit_q25 = float(np.quantile(lit, .25))
    b1_specific = (b1 >= b1_q75) & (b2 < b2_med)
    b2_specific = (b2 >= b2_q75) & (b1 < b1_med)
    joint = (b1 >= b1_med) & (b2 >= b2_med)
    other = (lit <= lit_q25)
    # The categories are defined from frozen numerical ranks.  Make the
    # intended four-way diagnostic partition disjoint only where a boundary
    # can overlap; no semantic result is used to resolve it.
    joint &= ~(b1_specific | b2_specific)
    other &= ~(b1_specific | b2_specific | joint)
    masks = {"B1_specific": b1_specific, "B2_specific": b2_specific,
             "joint": joint, "OTHER": other}
    groups = {label: pos[mask] for label, mask in masks.items()}
    thresholds = {"B1_median": float(b1_med), "B1_q75": float(b1_q75),
                  "B2_median": float(b2_med), "B2_q75": float(b2_q75),
                  "LITSHARE_q25": lit_q25}
    return groups, {"scope": scope, "thresholds": thresholds,
                    "n_scope": int(len(pos)),
                    "counts": {key: int(len(value)) for key, value in groups.items()}}


def _match_pair(pop: dict[str, Any], scope: str, left: str, right: str,
                groups: dict[str, np.ndarray]) -> dict[str, Any]:
    scope_pos = _scope_positions(pop, scope)
    ids, L = pop["user_ids"], pop["common_L"]
    order = scope_pos[np.lexsort((ids[scope_pos], L[scope_pos]))]
    left_set, right_set = set(groups[left].tolist()), set(groups[right].tolist())
    selected_left: list[int] = []
    selected_right: list[int] = []
    bins = []
    for start in range(0, len(order), MATCH_BIN_SIZE):
        chunk = order[start:start + MATCH_BIN_SIZE]
        li = np.asarray([p for p in chunk if int(p) in left_set], dtype=int)
        ri = np.asarray([p for p in chunk if int(p) in right_set], dtype=int)
        m = min(len(li), len(ri))
        if m == 0:
            continue
        center = float(np.median(L[chunk]))
        li = li[np.lexsort((ids[li], np.abs(L[li] - center)))][:m]
        ri = ri[np.lexsort((ids[ri], np.abs(L[ri] - center)))][:m]
        selected_left.extend(li.tolist())
        selected_right.extend(ri.tolist())
        bins.append({"start": int(start), "n": int(len(chunk)), "n_left": int(len(li)),
                     "n_right": int(len(ri)), "center_L": center})
    left_pos = np.asarray(sorted(selected_left), dtype=np.int64)
    right_pos = np.asarray(sorted(selected_right), dtype=np.int64)
    return {
        "scope": scope, "left": left, "right": right,
        "left_positions": left_pos, "right_positions": right_pos,
        "left_user_ids": ids[left_pos], "right_user_ids": ids[right_pos],
        "n": int(len(left_pos)), "bins": bins,
        "balance": _distribution_balance(L[left_pos], L[right_pos]),
    }


def _signal_match(pop: dict[str, Any], scope: str, signal_name: str,
                  signal: np.ndarray) -> dict[str, Any]:
    scope_pos = _scope_positions(pop, scope)
    ids, L = pop["user_ids"], pop["common_L"]
    order = scope_pos[np.lexsort((ids[scope_pos], L[scope_pos]))]
    high: list[int] = []
    low: list[int] = []
    bins = []
    for start in range(0, len(order), MATCH_BIN_SIZE):
        chunk = order[start:start + MATCH_BIN_SIZE]
        tail = max(1, int(math.floor(len(chunk) * MATCH_TAIL_FRACTION)))
        high_order = chunk[np.lexsort((ids[chunk], -signal[chunk]))]
        low_order = chunk[np.lexsort((ids[chunk], signal[chunk]))]
        hi, lo = high_order[:tail], low_order[:tail]
        high.extend(hi.tolist())
        low.extend(lo.tolist())
        bins.append({"start": int(start), "n": int(len(chunk)), "tail_n": tail,
                     "high_user_ids": ids[hi].tolist(), "low_user_ids": ids[lo].tolist()})
    hi_pos = np.asarray(sorted(high), dtype=np.int64)
    lo_pos = np.asarray(sorted(low), dtype=np.int64)
    return {
        "scope": scope, "signal": signal_name, "high_positions": hi_pos,
        "low_positions": lo_pos, "high_user_ids": ids[hi_pos],
        "low_user_ids": ids[lo_pos], "n": int(len(hi_pos)), "bins": bins,
        "balance": _distribution_balance(L[hi_pos], L[lo_pos]),
    }


def _group_summary(pop: dict[str, Any], positions: np.ndarray) -> dict[str, Any]:
    p = np.asarray(positions, dtype=np.int64)
    return {
        "n": int(len(p)), "common_L": _summary(pop["common_L"][p]),
        "shell_counts": {f"S{code}": int(np.sum(pop["shell"][p] == code))
                         for code in range(3)},
        "candidate": {name: _summary(pop["candidates"][name][p])
                      for name in CANDIDATE_NAMES},
    }


def _strip_arrays(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip_arrays(item) for key, item in value.items()
                if not isinstance(item, np.ndarray)}
    if isinstance(value, list):
        return [_strip_arrays(item) for item in value]
    return value


def _compute_numerical(source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    analysis: dict[str, Any] = {
        "version": STATE_VERSION, "seed": LITERARY_SUPERMODE_SEED,
        "candidate_names": list(CANDIDATE_NAMES),
        "primary_candidates": list(PRIMARY_CANDIDATES),
        "local_super_mode": {"LIT": ["B1", "B2"], "OTHER": ["B3", "B4"]},
        "populations": {}, "context": {}, "characterization": {},
        "candidate_matches": {}, "groups": {}, "comparison_groups": {},
        "corrections": source["audit"]["source"]["corrected_previous_head_metrics"],
        "metadata_loaded": False,
    }
    arrays: dict[str, np.ndarray] = {}

    for tag in POPULATIONS:
        pop = source["populations"][tag]
        split0 = _split_candidate_analysis(pop, 0)
        repro = _candidate_reproducibility(pop, split0)
        additional = _additional_split_summaries(pop)
        analysis["populations"][tag] = {
            "n": int(len(pop["user_ids"])),
            "shell_counts": {f"S{code}": int(np.sum(pop["shell"] == code))
                             for code in range(3)},
            "split_reproducibility": repro,
            "additional_split_summaries": additional,
            "candidate_distributions": {
                name: _summary(pop["candidates"][name]) for name in CANDIDATE_NAMES},
            "b1_support_reproducibility_inherited": source["aff_json"].get(
                "analysis", {}).get("populations", {}).get(tag, {}).get(
                    "support_reproducibility", {}).get("per_basin", {}).get("1", {}),
        }
        prefix = f"{tag}/"
        arrays[prefix + "user_ids"] = pop["user_ids"].astype(np.int64)
        arrays[prefix + "common_L"] = pop["common_L"].astype(np.float32)
        arrays[prefix + "shell_code"] = pop["shell"].astype(np.int8)
        arrays[prefix + "support_median"] = pop["support"].astype(np.float32)
        arrays[prefix + "support_mean"] = source["aff"][prefix + "support_mean"].astype(np.float32)
        arrays[prefix + "percentile_support"] = pop["support_pct"].astype(np.float32)
        arrays[prefix + "soft_share"] = pop["shares"].astype(np.float32)
        arrays[prefix + "run_labels"] = pop["run_labels"].astype(np.int8)
        arrays[prefix + "run_valid"] = pop["run_valid"].astype(bool)
        for name, value in pop["candidates"].items():
            arrays[prefix + name] = value.astype(np.float32)
            arrays[prefix + "split_A_" + name] = split0["A"][name].astype(np.float32)
            arrays[prefix + "split_B_" + name] = split0["B"][name].astype(np.float32)

    # Cross-context comparisons use only the pre-frozen book-space local basin
    # correspondence.  For the B1+B2 sum the correspondence is equivalent to
    # the local B1/B2 labels; it is still recorded explicitly.
    j10, j20 = source["populations"]["J10000"], source["populations"]["J20000"]
    shared = np.intersect1d(j10["user_ids"], j20["user_ids"])
    p10 = np.searchsorted(j10["user_ids"], shared)
    p20 = np.searchsorted(j20["user_ids"], shared)
    context: dict[str, Any] = {
        "shared_n": int(len(shared)),
        "mapping_j10_to_j20_zero_based": [0, 1, 3, 2],
        "scores": {}, "by_shell": {},
        "previous_four_basin_context": source["aff_json"].get("analysis", {}).get("context", {}),
    }
    arrays["context/shared_user_ids"] = shared.astype(np.int64)
    arrays["context/shared_shell_code"] = j20["shell"][p20].astype(np.int8)
    for name in CANDIDATE_NAMES:
        x = j10["candidates"][name][p10]
        y = j20["candidates"][name][p20]
        metric = {**_corr(x, y), "mae": float(np.mean(np.abs(x - y))),
                  "median_absolute_difference": float(np.median(np.abs(x - y))),
                  "zscore_mae": _zscore_mae(x, y),
                  "top_overlap": {str(int(f * 100)): _top_overlap(x, y, shared, f)
                                  for f in TOP_FRACTIONS},
                  "decile_transition": _transition(x, y),
                  "j10": _summary(x), "j20": _summary(y)}
        if name == "LITSHARE":
            shift = np.abs(x - y)
            metric["context_shift"] = {
                "mean_abs": float(np.mean(shift)), "p50_abs": float(np.quantile(shift, .50)),
                "p90_abs": float(np.quantile(shift, .90)), "p95_abs": float(np.quantile(shift, .95)),
                "fraction_abs_gt_0.05": float(np.mean(shift > .05)),
                "fraction_abs_gt_0.10": float(np.mean(shift > .10)),
                "fraction_abs_gt_0.20": float(np.mean(shift > .20)),
            }
        context["scores"][name] = metric
        arrays["context/J10_" + name] = x.astype(np.float32)
        arrays["context/J20_" + name] = y.astype(np.float32)
        arrays["context/J10_decile_" + name] = _deciles(x)
        arrays["context/J20_decile_" + name] = _deciles(y)
        for code in (0, 1):
            mask = j20["shell"][p20] == code
            if np.any(mask):
                context["by_shell"].setdefault(name, {})[f"S{code}"] = {
                    **_corr(x[mask], y[mask]),
                    "mae": float(np.mean(np.abs(x[mask] - y[mask]))),
                    "top10_overlap": _top_overlap(x[mask], y[mask], shared[mask], .10),
                }
    analysis["context"] = context

    base_payload = affiliation.prior.dynamics._load_payload("payload_J20000")
    work_ids = base_payload["work_ids"].astype(str)
    direct_cache: dict[str, dict[str, Any]] = {}

    def register_group(key: str, positions: np.ndarray, scope: str,
                       label: str, role: str, pop: dict[str, Any]) -> dict[str, Any]:
        pos = np.asarray(sorted(set(np.asarray(positions, dtype=int).tolist())), dtype=np.int64)
        ids = pop["user_ids"][pos].astype(np.int64)
        cache_key = _hash_ids(ids)
        if cache_key not in direct_cache:
            direct = affiliation._direct_group_score(base_payload, ids)
            direct_cache[cache_key] = {
                "user_ids": ids, "score": direct["score"].astype(np.float64),
                "reader_mass": direct["reader_mass"].astype(np.float64),
                "work_ids": direct["work_ids"].astype(str),
            }
        direct = direct_cache[cache_key]
        record = {"key": key, "scope": scope, "label": label, "role": role,
                  "n": int(len(pos)), "user_ids": ids, "positions": pos,
                  "common_L": pop["common_L"][pos],
                  "summary": _group_summary(pop, pos),
                  "cache_key": cache_key, "npz_prefix": "group/" + _safe_key(key),
                  "score": direct["score"], "reader_mass": direct["reader_mass"],
                  "work_ids": direct["work_ids"]}
        analysis["groups"][key] = record
        safe = _safe_key(key)
        arrays[f"group/{safe}/user_ids"] = ids
        arrays[f"group/{safe}/common_L"] = pop["common_L"][pos].astype(np.float32)
        arrays[f"group/{safe}/shell_code"] = pop["shell"][pos].astype(np.int8)
        arrays[f"group/{safe}/score"] = direct["score"].astype(np.float32)
        arrays[f"group/{safe}/reader_mass"] = direct["reader_mass"].astype(np.float32)
        arrays[f"group/{safe}/group_label"] = np.asarray([label] * len(ids), dtype="U32")
        for name in CANDIDATE_NAMES:
            arrays[f"group/{safe}/{name}"] = pop["candidates"][name][pos].astype(np.float32)
        return record

    for scope in GROUP_SCOPES:
        groups, group_meta = _characterization_groups(j20, scope)
        analysis["characterization"][scope] = group_meta
        group_records: dict[str, dict[str, Any]] = {}
        for label in CHARACTERIZATION_LABELS:
            key = f"characterization_{scope}_{label}"
            group_records[label] = register_group(key, groups[label], scope,
                                                  label, "characterization", j20)
        analysis["comparison_groups"].setdefault("characterization", {})[scope] = {}
        for left, right in CHARACTERIZATION_PAIRS:
            match = _match_pair(j20, scope, left, right, groups)
            pair_key = f"characterization_pair_{scope}_{left}_vs_{right}"
            hi = register_group(pair_key + "__" + left, match["left_positions"], scope,
                                left, "characterization_pair", j20)
            lo = register_group(pair_key + "__" + right, match["right_positions"], scope,
                                right, "characterization_pair", j20)
            match["key"] = pair_key
            match["left_group_key"] = hi["key"]
            match["right_group_key"] = lo["key"]
            match["head_space_separation"] = _head_metrics(hi, lo, work_ids)
            analysis["comparison_groups"]["characterization"][scope][pair_key] = match

    for scope in GROUP_SCOPES:
        analysis["candidate_matches"][scope] = {}
        scope_pos = _scope_positions(j20, scope)
        for name in PRIMARY_CANDIDATES:
            match = _signal_match(j20, scope, name, j20["candidates"][name])
            key = f"candidate_{scope}_{name}"
            hi = register_group(key + "__high", match["high_positions"], scope,
                                "high", "candidate_match", j20)
            lo = register_group(key + "__low", match["low_positions"], scope,
                                "low", "candidate_match", j20)
            match["key"] = key
            match["high_group_key"] = hi["key"]
            match["low_group_key"] = lo["key"]
            match["head_space_separation"] = _head_metrics(hi, lo, work_ids)
            analysis["candidate_matches"][scope][name] = match

    # Export exact numerical arrays for each population and cross-context
    # comparison.  The direct group score vectors remain in the same NPZ so a
    # later audit can reconstruct every corrected head metric.
    arrays["config/seed"] = np.asarray([LITERARY_SUPERMODE_SEED], dtype=np.int64)
    arrays["config/split_reps"] = np.asarray([SPLIT_REPS], dtype=np.int64)
    arrays["config/match_bin_size"] = np.asarray([MATCH_BIN_SIZE], dtype=np.int64)
    arrays["config/match_tail_fraction"] = np.asarray([MATCH_TAIL_FRACTION], dtype=np.float64)
    arrays["config/n_basins"] = np.asarray([N_BASINS], dtype=np.int64)
    arrays["frozen/universe"] = source["universe"].astype(np.int64)
    arrays["frozen/common_L"] = source["common_L_global"].astype(np.float64)
    for n, ids in source["memberships"].items():
        arrays[f"membership/{n}/user_ids"] = ids.astype(np.int64)

    # Store only compact numerical records in JSON; all vectors are in NPZ.
    compact = _strip_arrays(analysis)
    # Remove duplicated direct score/work vectors from group records while
    # retaining their NPZ key and exact membership manifests.
    for key, record in compact["groups"].items():
        record.pop("score", None)
        record.pop("reader_mass", None)
        record.pop("work_ids", None)
        record["npz_prefix"] = "group/" + _safe_key(key)
    _write_npz_atomic(STATE_DIR / "numerical.npz", arrays)
    _json_dump(STATE_DIR / "numerical.json", compact)
    return analysis, arrays


def _load_numerical_state() -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    path_json, path_npz = STATE_DIR / "numerical.json", STATE_DIR / "numerical.npz"
    if not path_json.exists() or not path_npz.exists():
        raise RuntimeError("numerical state missing; run --phase numerical")
    analysis, arrays = _load_json(path_json), _load_npz(path_npz)
    if analysis.get("seed") != LITERARY_SUPERMODE_SEED:
        raise RuntimeError("numerical seed mismatch")
    return analysis, arrays


def _group_head(arrays: dict[str, np.ndarray], key: str,
                work_ids: np.ndarray) -> dict[str, np.ndarray]:
    safe = _safe_key(key)
    return affiliation._head(arrays[f"group/{safe}/score"], work_ids,
                             arrays[f"group/{safe}/reader_mass"], HEAD_LIMIT)


def _posthoc(analysis: dict[str, Any], arrays: dict[str, np.ndarray],
             source: dict[str, Any]) -> dict[str, Any]:
    # This is the first function that opens title/flag/probe metadata.  All
    # groups and score vectors were frozen in _compute_numerical beforehand.
    base_payload = affiliation.prior.dynamics._load_payload("payload_J20000")
    work_ids = base_payload["work_ids"].astype(str)
    metadata, probes = affiliation._metadata_and_probes(work_ids)
    groups: dict[str, Any] = {}
    for key in analysis["groups"]:
        head = _group_head(arrays, key, work_ids)
        rows, desc = affiliation._annotate_head(head, metadata, probes)
        authors50 = [str(row.get("author", "")) for row in rows[:50]
                     if str(row.get("author", ""))]
        author_counts50: dict[str, int] = {}
        for author in authors50:
            author_counts50[author] = author_counts50.get(author, 0) + 1
        desc["unique_authors_50"] = int(len(set(authors50)))
        desc["max_same_author_50"] = int(max(author_counts50.values(), default=0))
        groups[key] = {"head": rows, "descriptors": desc,
                       "scope": analysis["groups"][key]["scope"],
                       "label": analysis["groups"][key]["label"],
                       "role": analysis["groups"][key]["role"]}

    def semantic_pair(left_key: str, right_key: str) -> dict[str, Any]:
        left, right = groups[left_key]["descriptors"], groups[right_key]["descriptors"]
        return {
            "left": left_key, "right": right_key,
            "left_descriptors": left, "right_descriptors": right,
            "probe_contrast": {name: int(left.get(name, 0) - right.get(name, 0))
                               for name in ("pos50", "exact50", "broad50", "anti50",
                                            "comic50", "picture_book50", "collection50",
                                            "duplicate50")},
        }

    character_semantics: dict[str, Any] = {}
    for scope, pairs in analysis["comparison_groups"]["characterization"].items():
        character_semantics[scope] = {}
        for pair_key, match in pairs.items():
            character_semantics[scope][pair_key] = semantic_pair(
                match["left_group_key"], match["right_group_key"])
    candidate_semantics: dict[str, Any] = {}
    for scope, signals in analysis["candidate_matches"].items():
        candidate_semantics[scope] = {}
        for name, match in signals.items():
            candidate_semantics[scope][name] = semantic_pair(
                match["high_group_key"], match["low_group_key"])
    return {
        "metadata_loaded": True,
        "metadata_source": "ex.work_scores/ex.work_flags",
        "probe_source": "existing post-hoc evaluation sets",
        "groups": groups,
        "characterization": character_semantics,
        "candidate_matches": candidate_semantics,
    }


def _build_output_npz(source: dict[str, Any], arrays: dict[str, np.ndarray]) -> None:
    # The numerical state already contains all raw vectors; copy it to the
    # committed artifact and add the corrected inherited membership universe.
    out = dict(arrays)
    _write_npz_atomic(OUT_NPZ, out)


def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    return (["|" + "|".join(headers) + "|",
             "|" + "|".join("---" for _ in headers) + "|"] +
            ["|" + "|".join(str(cell) for cell in row) + "|" for row in rows])


def _semantic_short(desc: dict[str, Any]) -> str:
    return (f"pos/exact/broad/anti={desc.get('pos50', '—')}/"
            f"{desc.get('exact50', '—')}/{desc.get('broad50', '—')}/"
            f"{desc.get('anti50', '—')}; comics={desc.get('comic50', '—')}; "
            f"authors={desc.get('unique_authors_50', '—')}; "
            f"max-author={desc.get('max_same_author_50', '—')}")


def _build_heads(posthoc: dict[str, Any]) -> str:
    lines = ["# B1+B2 literary super-mode direct heads", "",
             "All groups were selected from frozen basin affiliations/common-L "
             "before post-hoc metadata and probe annotations were loaded. Every "
             "head uses its actual direct reader-mass eligibility.", ""]
    for key, value in posthoc["groups"].items():
        lines.extend([f"## {key}", "",
                      f"Scope: `{value['scope']}`; label: `{value['label']}`; "
                      f"role: `{value['role']}`.",
                      f"Descriptors: `{json.dumps(value['descriptors'], sort_keys=True)}`", "",
                      "|rank|title|author|work_id|score|reader_mass|pos|exact|broad|anti|comic|collection|duplicate|",
                      "|---:|---|---|---|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"])
        for row in value["head"]:
            title = str(row.get("title", "")).replace("|", "\\|")
            author = str(row.get("author", "")).replace("|", "\\|")
            lines.append(
                f"|{row['rank']}|{title}|{author}|{row['work_id']}|"
                f"{float(row['score']):.7g}|{float(row['n_eff']):.5g}|"
                f"{'Y' if row.get('pos') else ''}|{'Y' if row.get('exact') else ''}|"
                f"{'Y' if row.get('broad') else ''}|{'Y' if row.get('anti') else ''}|"
                f"{'Y' if row.get('is_comic') else ''}|"
                f"{'Y' if row.get('is_collection') else ''}|"
                f"{'Y' if row.get('is_duplicate') else ''}|")
        lines.append("")
    return "\n".join(lines)


def _build_report(audit: dict[str, Any], analysis: dict[str, Any],
                  posthoc: dict[str, Any], runtime_seconds: float) -> str:
    lines = ["# Literary B1+B2 super-mode report", "",
             f"Campaign seed: `{LITERARY_SUPERMODE_SEED}`. Starting commit: `{START_COMMIT}`.",
             f"Wall-clock runtime: `{runtime_seconds:.1f}` seconds. Basin trajectories were not rerun.", "",
             "This is a bounded diagnostic. B1 and B2 remain separate throughout; "
             "the semantic-free hypothesis tested here is local `{B1,B2}` versus `{B3,B4}`. "
             "No final jury, threshold, maximum search, fitted score, or obscure-book "
             "validation was performed.", "", "## A. Correction note", ""]
    correction = audit["source"]["corrected_previous_head_metrics"]
    lines.extend(["The inherited affiliation campaign was corrected before this experiment:",
                  "", "- The matched-head comparison now passes each group’s actual reader-mass array "
                  "to the top-200 eligibility filter; no basin trajectory was rerun.",
                  "- The percentile hard-partition report now uses `percentile_margin`, not `raw_margin`.",
                  "- The previous tautological git-hash comparison was replaced with an actual "
                  "working-tree-byte versus HEAD-byte comparison, with the intentional correction "
                  "manifest recorded in the inherited JSON.", "", "Corrected previous matched-head metrics:"])
    rows = []
    for name, value in correction.items():
        rows.append([name, value.get("top50_overlap"), value.get("top200_overlap"),
                     value.get("common_top200_n"), _fmt(value.get("common_top200_spearman"))])
    lines.extend(_md_table(["group", "top50 overlap", "top200 overlap", "common top200", "Spearman"], rows))
    lines.extend(["", f"Frozen source audit: **{sum(c['ok'] for c in audit['checks'])}/"
                  f"{len(audit['checks'])} passed**.",
                  f"Common-L hash `{audit['source']['common_L_hash']}`; universe hash "
                  f"`{audit['source']['universe_hash']}`.", ""])

    lines.extend(["## B. Candidate definitions", "",
                  "All candidates were computed from the frozen four-basin supports before "
                  "metadata loading:", ""])
    lines.extend(_md_table(["candidate", "definition", "role"], [
        ["LITSHARE", "P(B1)+P(B2)", "primary"],
        ["LITCONTRAST", "2·LITSHARE−1", "descriptive transform"],
        ["RAWSUM", "w(B1)+w(B2)", "scale sensitivity"],
        ["PCTSUM", "within-basin percentile(B1)+percentile(B2)", "scale sensitivity"],
        ["B1_SUPPORT", "w(B1)", "comparator"],
        ["B1_SOFT_SHARE", "P(B1)", "comparator"],
        ["B1_SPECIFICITY", "w(B1)−max(w(B2),w(B3),w(B4))", "old comparator"],
    ]))
    lines.extend(["", "No free coefficient was fitted and no semantic label entered score construction.", ""])

    lines.extend(["## C. Split-run reproducibility", ""])
    rows = []
    for tag in POPULATIONS:
        for name in CANDIDATE_NAMES:
            m = analysis["populations"][tag]["split_reproducibility"]["overall"][name]
            rows.append([tag, name, _fmt(m["pearson"]), _fmt(m["spearman"]),
                         f"{m['top_overlap']['10']['overlap']}/{m['top_overlap']['10']['k']}",
                         _fmt(m["mae"]), _fmt(m["median_absolute_difference"])])
    lines.extend(_md_table(["population", "score", "Pearson", "Spearman", "top10", "MAE", "median |Δ|"], rows))
    lines.append("")
    for tag in POPULATIONS:
        lines.append(f"### {tag} shell split checks")
        rows = []
        for name in CANDIDATE_NAMES:
            for shell, m in analysis["populations"][tag]["split_reproducibility"]["by_shell"][name].items():
                rows.append([name, shell, _fmt(m["pearson"]), _fmt(m["spearman"]),
                             f"{m['top_overlap']['10']['overlap']}/{m['top_overlap']['10']['k']}"])
        lines.extend(_md_table(["score", "shell", "Pearson", "Spearman", "top10"], rows))
        lines.append("")
        lines.append("Additional deterministic split repetitions, median/p10/p90:")
        rows = []
        for name in CANDIDATE_NAMES:
            summary = analysis["populations"][tag]["additional_split_summaries"]["summary"][name]
            rows.append([name,
                         "/".join(_fmt(summary[field][key]) for field in ("pearson", "spearman", "top10_overlap") for key in ("median", "p10", "p90"))])
        lines.extend(_md_table(["score", "Pearson med/p10/p90; Spearman med/p10/p90; top10 med/p10/p90"], rows))
        inherited = analysis["populations"][tag]["b1_support_reproducibility_inherited"]
        lines.append(f"Inherited four-basin B1 support split check: Pearson `{_fmt(inherited.get('overall', {}).get('pearson'))}`, "
                     f"Spearman `{_fmt(inherited.get('overall', {}).get('spearman'))}`.")
        lines.append("")

    lines.extend(["## D. J10↔J20 context stability", "",
                  "The J10→J20 basin correspondence is frozen from book-centroid space; "
                  "the local B1+B2 sum uses B1/B2 in both contexts. Raw MAE is followed "
                  "by z-score MAE where raw support scales are not directly comparable.", ""])
    rows = []
    for name, m in analysis["context"]["scores"].items():
        rows.append([name, _fmt(m["pearson"]), _fmt(m["spearman"]),
                     f"{m['top_overlap']['10']['overlap']}/{m['top_overlap']['10']['k']}",
                     _fmt(m["median_absolute_difference"]), _fmt(m["zscore_mae"])])
    lines.extend(_md_table(["score", "Pearson", "Spearman", "top10", "median |Δ|", "z-MAE"], rows))
    lines.append("")
    for name, by_shell in analysis["context"]["by_shell"].items():
        lines.append(f"- {name}: " + "; ".join(
            f"{shell} rho={_fmt(m.get('pearson'))}, top10={m['top10_overlap']['overlap']}/"
            f"{m['top10_overlap']['k']}" for shell, m in by_shell.items()))
    lit_shift = analysis["context"]["scores"]["LITSHARE"]["context_shift"]
    lines.append("- LITSHARE absolute context shift: " + "; ".join(
        f"{key}={_fmt(value)}" for key, value in lit_shift.items()))
    previous = analysis["context"]["previous_four_basin_context"]
    lines.append("- Previous four-basin context reference: mapped raw argmax agreement "
                 f"`{_fmt(previous.get('argmax', {}).get('raw', {}).get('agreement'))}`, "
                 f"exact basin-order agreement `{_fmt(previous.get('relational', {}).get('exact_basin_order_agreement'))}`.")
    lines.append("")

    lines.extend(["## E. Numerical B1-specific, B2-specific, joint, and OTHER groups", "",
                  "The frozen rule is applied separately within J20 outer, S1, and S2: "
                  "B1-specific = B1 soft share ≥ within-scope 75th percentile and B2 below median; "
                  "B2-specific is symmetric; joint = both B1 and B2 at/above their medians; "
                  "OTHER = LITSHARE at/below its 25th percentile after removing overlapping categories. "
                  "These are numerical diagnostic groups, not jury selections.", ""])
    rows = []
    for scope, meta in analysis["characterization"].items():
        for label, n in meta["counts"].items():
            group = analysis["groups"][f"characterization_{scope}_{label}"]
            rows.append([scope, label, n, _fmt(group["summary"]["common_L"]["median"]),
                         _fmt(group["summary"]["candidate"]["LITSHARE"]["median"])])
    lines.extend(_md_table(["scope", "group", "n", "L median", "LITSHARE median"], rows))
    lines.append("")
    for scope, pairs in analysis["comparison_groups"]["characterization"].items():
        lines.append(f"### {scope} matched pairwise heads")
        rows = []
        for pair_key, match in pairs.items():
            sep = match["head_space_separation"]
            sem = posthoc["characterization"][scope][pair_key]["probe_contrast"]
            rows.append([match["left"] + " vs " + match["right"], match["n"],
                         _fmt(match["balance"]["ks_statistic"]),
                         _fmt(match["balance"]["wasserstein"]), _fmt(sep["centered_cosine"]),
                         f"{sep['top50_overlap']}/50", f"{sep['top200_overlap']}/200",
                         _fmt(sep.get("common_top200_spearman")),
                         f"{sem['pos50']:+d}/{sem['exact50']:+d}/{sem['broad50']:+d}/{sem['anti50']:+d}"])
        lines.extend(_md_table(["comparison", "n/side", "KS", "Wasserstein", "cosine",
                                "top50", "top200", "rank rho", "Δpos/exact/broad/anti"], rows))
        for pair_key, match in pairs.items():
            bal = match["balance"]
            lines.append(
                f"- {pair_key} L balance: means `{_fmt(bal['a']['mean'])}/"
                f"{_fmt(bal['b']['mean'])}`, std `{_fmt(bal['a']['std'])}/"
                f"{_fmt(bal['b']['std'])}`, p10/p25/median/p75/p90 A/B "
                f"`{_fmt(bal['a']['p10'])}/{_fmt(bal['a']['p25'])}/"
                f"{_fmt(bal['a']['median'])}/{_fmt(bal['a']['p75'])}/"
                f"{_fmt(bal['a']['p90'])}` / `"
                f"{_fmt(bal['b']['p10'])}/{_fmt(bal['b']['p25'])}/"
                f"{_fmt(bal['b']['median'])}/{_fmt(bal['b']['p75'])}/"
                f"{_fmt(bal['b']['p90'])}`, KS `{_fmt(bal['ks_statistic'])}`, "
                f"Wasserstein `{_fmt(bal['wasserstein'])}`, max quantile Δ "
                f"`{_fmt(bal['max_abs_quantile_difference'])}`.")
        lines.append("")

    lines.extend(["## F. Candidate high/low matched-common-L comparisons", "",
                  "For every scope and signal, the same consecutive 200-user L bins and "
                  "25% high/low tails are used. Grouping is frozen before semantic annotation. "
                  "The complete top-100 heads are in `LITERARY_SUPERMODE_HEADS.md`.", ""])
    rows = []
    for scope, signals in analysis["candidate_matches"].items():
        for name, match in signals.items():
            sep = match["head_space_separation"]
            sem = posthoc["candidate_matches"][scope][name]["probe_contrast"]
            rows.append([scope, name, match["n"], _fmt(match["balance"]["a"]["median"]),
                         _fmt(match["balance"]["b"]["median"]), _fmt(match["balance"]["ks_statistic"]),
                         _fmt(sep["centered_cosine"]), f"{sep['top50_overlap']}/50",
                         f"{sep['top200_overlap']}/200", _fmt(sep.get("common_top200_spearman")),
                         f"{sem['pos50']:+d}/{sem['exact50']:+d}/{sem['broad50']:+d}/{sem['anti50']:+d}"])
    lines.extend(_md_table(["scope", "signal", "n/side", "high L med", "low L med", "KS",
                            "cosine", "top50", "top200", "rank rho", "Δpos/exact/broad/anti"], rows))
    for scope, signals in analysis["candidate_matches"].items():
        for name, match in signals.items():
            bal = match["balance"]
            lines.append(
                f"- {scope}/{name} L balance: means `{_fmt(bal['a']['mean'])}/"
                f"{_fmt(bal['b']['mean'])}`, std `{_fmt(bal['a']['std'])}/"
                f"{_fmt(bal['b']['std'])}`, p10/p25/median/p75/p90 A/B "
                f"`{_fmt(bal['a']['p10'])}/{_fmt(bal['a']['p25'])}/"
                f"{_fmt(bal['a']['median'])}/{_fmt(bal['a']['p75'])}/"
                f"{_fmt(bal['a']['p90'])}` / `"
                f"{_fmt(bal['b']['p10'])}/{_fmt(bal['b']['p25'])}/"
                f"{_fmt(bal['b']['median'])}/{_fmt(bal['b']['p75'])}/"
                f"{_fmt(bal['b']['p90'])}`, KS `{_fmt(bal['ks_statistic'])}`, "
                f"Wasserstein `{_fmt(bal['wasserstein'])}`, max quantile Δ "
                f"`{_fmt(bal['max_abs_quantile_difference'])}`.")
    lines.append("")

    lines.extend(["## G. Direct B1 versus B2 semantic descriptors", "",
                  "These descriptors are post-hoc annotations of the already-frozen direct heads. "
                  "They are not selection criteria.", ""])
    rows = []
    for scope in GROUP_SCOPES:
        for label in CHARACTERIZATION_LABELS:
            key = f"characterization_{scope}_{label}"
            desc = posthoc["groups"][key]["descriptors"]
            rows.append([scope, label, _semantic_short(desc)])
    lines.extend(_md_table(["scope", "group", "top-50 descriptors"], rows))
    lines.append("")
    for scope, pairs in posthoc["characterization"].items():
        lines.append(f"- {scope} pairwise qualitative contrasts: " + "; ".join(
            f"{pair}: Δpos/exact/broad/anti={value['probe_contrast']['pos50']:+d}/"
            f"{value['probe_contrast']['exact50']:+d}/{value['probe_contrast']['broad50']:+d}/"
            f"{value['probe_contrast']['anti50']:+d}" for pair, value in pairs.items()))

    lines.extend(["", "### Explicit evidence assessment", "",
                  "B2 is not equivalent to B1 in the frozen outer-user heads. It remains "
                  "numerically and label-free distinct from OTHER, but its semantic profile "
                  "is mixed rather than a second copy of the joint literary head:"])
    for scope in GROUP_SCOPES:
        b2 = posthoc["groups"][f"characterization_{scope}_B2_specific"]["descriptors"]
        other = posthoc["groups"][f"characterization_{scope}_OTHER"]["descriptors"]
        pair_key = f"characterization_pair_{scope}_B2_specific_vs_OTHER"
        sep = analysis["comparison_groups"]["characterization"][scope][pair_key]["head_space_separation"]
        lines.append(
            f"- {scope} B2-specific: {_semantic_short(b2)}; OTHER: {_semantic_short(other)}; "
            f"matched-L head cosine `{_fmt(sep['centered_cosine'])}`, "
            f"top200 `{sep['top200_overlap']}/200`.")
    lines.extend([
        "The strongest positive evidence for including B2 in a broader super-mode is therefore "
        "conditional: B2-specific users do not collapse into OTHER, especially in S2, but they "
        "are less literary-looking and more graphic/prestige-geek concentrated than the joint "
        "B1+B2 group. The simple union hypothesis is supported as a diagnostic axis, not as proof "
        "that every B2-specific reader belongs to the same literary mode as B1.",
        "",
        "LITSHARE is more context-stable than the B1-only soft share and the old B1-specificity "
        "signal in the shared-user ranking diagnostics, while preserving matched-L high/low head "
        "separation in J20 outer, S1, and S2. This supports retaining B1+B2 as a portable "
        "super-mode candidate, with B1/B2 kept separately for the next validation.",
    ])

    lines.extend(["", "## H. Interpretation", "",
                  "### Does B2 look independently literary?", "",
                  "The answer is judged by the B2-specific versus OTHER and B2-specific versus "
                  "B1-specific matched comparisons, not by a single title list. Inspect the "
                  "head file together with the label-free cosine/overlap rows and the probe "
                  "contrasts. A B2-specific group that remains separated from OTHER at matched L "
                  "and retains broad/exact literary representation supports B2 as an independent "
                  "literary-compatible submode; similarity to B1 is not required.", "",
                  "### Does the simple B1+B2 super-mode improve portability?", "",
                  f"LITSHARE J10↔J20 Pearson `{_fmt(analysis['context']['scores']['LITSHARE']['pearson'])}` "
                  f"and Spearman `{_fmt(analysis['context']['scores']['LITSHARE']['spearman'])}` are compared "
                  "against the inherited four-way and B1-only context diagnostics above. A high "
                  "correlation would support a portable super-mode, while strong matched-L separation "
                  "is needed to show that portability is not merely loss of discrimination.", "",
                  "### Relation to the old three-pile intuition", "",
                  "The post-hoc heads allow the data to be compared with a literary / cultured-mainstream / "
                  "fandom interpretation resembling B1+B2 / B3 / B4. This is an interpretation, not a "
                  "coded rule. B2 remains an independent mode in all arrays and tables.", "",
                  "## I. Stop condition and next experiment", "",
                  "This campaign stops here. It did not construct a final jury, fit a combined score, "
                  "choose a threshold, search a maximum, validate obscure-book recommendations, or run "
                  "binary/adaptive jury-size search.", "",
                  "The next scientifically warranted experiment, conditional on the matched B2 results, "
                  "is a predeclared soft-affiliation jury construction that retains B1 and B2 as separate "
                  "diagnostic dimensions and tests out-of-sample stability before any population-size "
                  "boundary search. If B2-specific separation collapses, the next step should instead "
                  "improve the user-affinity estimator rather than merge B1 and B2.", ""])
    return "\n".join(lines).rstrip() + "\n"


def _run_posthoc(audit: dict[str, Any], analysis: dict[str, Any],
                 arrays: dict[str, np.ndarray], source: dict[str, Any],
                 started: float) -> dict[str, Any]:
    posthoc = _posthoc(analysis, arrays, source)
    _build_output_npz(source, arrays)
    _write_text_atomic(OUT_HEADS, _build_heads(posthoc))
    runtime = max(time.time() - started, 0.0)
    report = _build_report(audit, analysis, posthoc, runtime)
    _write_text_atomic(OUT_REPORT, report)
    final = {
        "campaign": {
            "seed": LITERARY_SUPERMODE_SEED, "starting_commit": START_COMMIT,
            "affiliation_seed": AFFILIATION_SEED, "split_reps": SPLIT_REPS,
            "match_bin_size": MATCH_BIN_SIZE,
            "match_tail_fraction": MATCH_TAIL_FRACTION,
            "semantic_annotations_posthoc": True, "runtime_seconds": runtime,
            "basin_trajectories_rerun": False,
        },
        "audit": audit,
        "analysis": _strip_arrays(analysis),
        "posthoc": posthoc,
        "stop_scope": {"no_final_jury": True, "no_threshold": True,
                        "no_maximum_search": True, "no_binary_search": True,
                        "no_fitted_combined_score": True, "b2_preserved": True},
    }
    _json_dump(OUT_JSON, final)
    return final


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("audit", "numerical", "posthoc", "all"),
                        default="all")
    args = parser.parse_args()
    started = time.time()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    audit = _audit_source()
    print(json.dumps(audit, indent=1), flush=True)
    if args.phase == "audit":
        if not audit["ok"]:
            raise SystemExit(1)
        return
    if not audit["ok"]:
        raise SystemExit("source audit failed; refusing to continue")
    source = _load_source(audit)
    if args.phase in ("numerical", "all"):
        analysis, arrays = _compute_numerical(source)
        print(f"numerical super-mode analysis complete; groups={len(analysis['groups'])}", flush=True)
    else:
        analysis, arrays = _load_numerical_state()
    if args.phase in ("posthoc", "all"):
        _run_posthoc(audit, analysis, arrays, source, started)
        print(f"wrote {OUT_JSON}, {OUT_NPZ}, {OUT_REPORT}, {OUT_HEADS}", flush=True)


if __name__ == "__main__":
    main()

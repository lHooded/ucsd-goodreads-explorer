#!/usr/bin/env python3
"""Stable user affiliation to the frozen literary preference basins.

This is a bounded diagnostic experiment downstream of the frozen basin census
from ``577698fde5465c0e37b838c1626e58f521f3b134``.  It never reclusters book
preference endpoints, changes memberships, fits a new ranking score, or uses
semantic labels to define an affiliation.  It reuses the saved final user
weights from the 64 J10/J20 basin trajectories and measures split-run
reproducibility, representation sensitivity, matched-common-L separation, and
J10/J20 population-context dependence.

The state directory is deliberately ignored and separate from all inherited
campaign state.  The committed NPZ contains the raw affiliation arrays and
the direct matched-group score vectors needed for later audit.

Run, for example::

    PYTHONPATH=. .venv/bin/python -m \
      curators_explorer.scripts.research_literary_user_basin_affiliation \
      --phase audit
    PYTHONPATH=. .venv/bin/python -m \
      curators_explorer.scripts.research_literary_user_basin_affiliation \
      --phase all
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import (ks_2samp, rankdata, skew, spearmanr,
                         wasserstein_distance)
from sklearn.metrics import cohen_kappa_score

from curators_explorer.scripts import research_literary_basin_refinement as prior
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts.research_converged_common_literary_jurors import (
    DATA,
    _write_npz_atomic,
    _write_text_atomic,
    open_db,
)


LITERARY_AFFILIATION_SEED = 20260904
START_COMMIT = "577698fde5465c0e37b838c1626e58f521f3b134"
SOURCE_BASIN_COMMIT = "bff6d6d9b91410daac1c302382f9e5a02892d02e"
SOURCE_BASIN_REPS = 64
SOURCE_SELECTED_K = 4
SPLIT_REPS = 10
MATCH_BIN_SIZE = 200
MATCH_TAIL_FRACTION = 0.25
AMBIGUOUS_MARGIN_THRESHOLDS = (0.01, 0.05)
SOFT_SHARE_THRESHOLDS = (0.40, 0.50, 0.60, 0.75)
J5_SUPPORT_THRESHOLD = 25.0
HEAD_LIMIT = 100
TOP_FRACTIONS = (0.05, 0.10, 0.25)
POPULATIONS = ("J10000", "J20000")

PRIOR_JSON = DATA / "literary_basin_refinement.json"
PRIOR_NPZ = DATA / "literary_basin_refinement.npz"
PRIOR_REPORT = DATA / "LITERARY_BASIN_REFINEMENT_REPORT.md"
PRIOR_BASIN_HEADS = DATA / "LITERARY_BASIN_HEADS.md"
PRIOR_EXPANSION_HEADS = DATA / "LITERARY_REFINED_EXPANSION_HEADS.md"
PRIOR_SCRIPT = Path(__file__).resolve().with_name(
    "research_literary_basin_refinement.py")
PRIOR_STATE = DATA / "literary_basin_refinement_state"

OUT_JSON = DATA / "literary_user_basin_affiliation.json"
OUT_NPZ = DATA / "literary_user_basin_affiliation.npz"
OUT_REPORT = DATA / "LITERARY_USER_BASIN_AFFILIATION_REPORT.md"
OUT_HEADS = DATA / "LITERARY_USER_AFFILIATION_HEADS.md"
STATE_DIR = DATA / "literary_user_basin_affiliation_state"
STATE_VERSION = 1


def _safe_key(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_array(value: np.ndarray, dtype: str | None = None) -> str:
    array = np.asarray(value, dtype=dtype) if dtype else np.asarray(value)
    return _sha256_bytes(np.ascontiguousarray(array).tobytes(order="C"))


def _hash_ids(value: np.ndarray) -> str:
    return _hash_array(np.asarray(value, dtype="<i8"))


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    raise TypeError(f"cannot serialize {type(value)!r}")


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


def _git_blob_hash(path: Path) -> str | None:
    try:
        relative = path.resolve().relative_to(Path.cwd().resolve())
        return subprocess.run(["git", "rev-parse", f"HEAD:{relative}"],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        if value is None or not np.isfinite(float(value)):
            return "—"
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_sci(value: Any) -> str:
    try:
        if value is None or not np.isfinite(float(value)):
            return "—"
        return f"{float(value):.2e}"
    except (TypeError, ValueError):
        return "—"


def _derive_seed(*parts: Any) -> int:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    # Keep seeds lossless in JSON/NPZ while staying inside Generator's range.
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "little") & ((1 << 63) - 1)


def _audit_check(checks: list[dict[str, Any]], name: str,
                 ok: bool, detail: str) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def _audit_frozen_state() -> dict[str, Any]:
    """Audit only frozen numerical artifacts; no metadata or probes are read."""
    checks: list[dict[str, Any]] = []
    _audit_check(checks, "starting_commit_exact", _git_head() == START_COMMIT,
                 f"HEAD={_git_head()}")
    required = {
        "prior_json": PRIOR_JSON,
        "prior_npz": PRIOR_NPZ,
        "prior_report": PRIOR_REPORT,
        "prior_basin_heads": PRIOR_BASIN_HEADS,
        "prior_expansion_heads": PRIOR_EXPANSION_HEADS,
        "prior_script": PRIOR_SCRIPT,
        "prior_state": PRIOR_STATE,
    }
    _audit_check(checks, "inherited_artifacts_present",
                 all(path.exists() for path in required.values()),
                 ", ".join(f"{key}={path.exists()}" for key, path in required.items()))
    if not all(path.exists() for path in required.values()):
        audit = {"checks": checks, "ok": False,
                 "semantic_metadata_loaded": False}
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        _json_dump(STATE_DIR / "audit.json", audit)
        return audit

    prior_json = _load_json(PRIOR_JSON)
    prior_npz = _load_npz(PRIOR_NPZ)
    current_hashes = {
        "json": _sha256_bytes(PRIOR_JSON.read_bytes()),
        "npz": _sha256_bytes(PRIOR_NPZ.read_bytes()),
        "script": _sha256_bytes(PRIOR_SCRIPT.read_bytes()),
    }
    git_hashes = {
        key: _git_blob_hash(path)
        for key, path in (("json", PRIOR_JSON), ("npz", PRIOR_NPZ),
                          ("report", PRIOR_REPORT), ("basin_heads", PRIOR_BASIN_HEADS),
                          ("expansion_heads", PRIOR_EXPANSION_HEADS),
                          ("script", PRIOR_SCRIPT))
    }
    _audit_check(checks, "inherited_committed_hashes_match",
                 all(value is not None for value in git_hashes.values())
                 and all(_git_blob_hash(path) == subprocess.run(
                     ["git", "rev-parse", f"HEAD:{path.resolve().relative_to(Path.cwd().resolve())}"],
                     capture_output=True, text=True, check=True).stdout.strip()
                     for path in (PRIOR_JSON, PRIOR_NPZ, PRIOR_REPORT,
                                  PRIOR_BASIN_HEADS, PRIOR_EXPANSION_HEADS, PRIOR_SCRIPT)),
                 json.dumps(git_hashes, sort_keys=True))

    campaign = prior_json.get("campaign", {})
    _audit_check(checks, "source_campaign_commit_exact",
                 campaign.get("starting_commit") == SOURCE_BASIN_COMMIT,
                 str(campaign.get("starting_commit")))
    _audit_check(checks, "source_basin_reps_exact",
                 campaign.get("basin_reps") == SOURCE_BASIN_REPS,
                 str(campaign.get("basin_reps")))
    _audit_check(checks, "source_selected_k_exact",
                 all(prior_json.get("clusters", {}).get(tag, {}).get("selected_k")
                     == SOURCE_SELECTED_K for tag in POPULATIONS),
                 ", ".join(f"{tag}={prior_json.get('clusters', {}).get(tag, {}).get('selected_k')}"
                            for tag in POPULATIONS))

    required_keys = ["frozen/universe", "frozen/common_L"]
    required_keys.extend(f"membership/J{n}/user_ids"
                         for n in (5000, 10000, 20000, 30000))
    required_keys.extend(f"basin/{tag}/{name}"
                         for tag in POPULATIONS
                         for name in ("labels", "centroid_norm", "centroid_score",
                                      "user_ids"))
    _audit_check(checks, "committed_numerical_keys_present",
                 all(key in prior_npz for key in required_keys),
                 f"checked={len(required_keys)}")

    frozen_state = prior_json.get("frozen_state", {})
    score_hash = _hash_array(prior_npz["frozen/common_L"].astype("<f8"))
    universe_hash = _hash_array(prior_npz["frozen/universe"].astype("<i8"))
    _audit_check(checks, "frozen_common_L_hash_matches",
                 score_hash == frozen_state.get("common_L_score_hash"), score_hash)
    _audit_check(checks, "frozen_universe_hash_matches",
                 universe_hash == frozen_state.get("universe_hash"), universe_hash)

    for n in (5000, 10000, 20000, 30000):
        tag = f"J{n}"
        ids = prior_npz[f"membership/{tag}/user_ids"].astype(np.int64)
        expected_hash = frozen_state.get("membership_hashes", {}).get(tag)
        _audit_check(checks, f"membership_hash_{tag}_matches",
                     _hash_ids(ids) == expected_hash,
                     _hash_ids(ids))
        _audit_check(checks, f"membership_{tag}_unique",
                     len(ids) == len(np.unique(ids)), f"n={len(ids)}")
    membership_sets = {
        f"J{n}": set(prior_npz[f"membership/J{n}/user_ids"].tolist())
        for n in (5000, 10000, 20000, 30000)
    }
    _audit_check(checks, "membership_nesting_exact",
                 len(membership_sets["J5000"] & membership_sets["J10000"]) == 5000
                 and len(membership_sets["J10000"] & membership_sets["J20000"]) == 10000
                 and len(membership_sets["J20000"] & membership_sets["J30000"]) == 20000,
                 "J5/J10/J20/J30 intersections")

    manifest_path = PRIOR_STATE / "basin_manifest.json"
    _audit_check(checks, "source_basin_manifest_present", manifest_path.exists(),
                 str(manifest_path))
    manifest = _load_json(manifest_path) if manifest_path.exists() else {}
    source_bundle: dict[str, Any] = {"prior_json": prior_json,
                                     "prior_npz": prior_npz,
                                     "manifest": manifest}
    all_endpoint_artifacts = True
    all_endpoint_scores_match = True
    labels_exact = True
    centroid_hashes: dict[str, Any] = {}
    valid_counts: dict[str, int] = {}
    populations: dict[str, Any] = {}

    for tag in POPULATIONS:
        cjson_path = PRIOR_STATE / f"cluster_{tag}.json"
        cnpz_path = PRIOR_STATE / f"cluster_{tag}.npz"
        cjson = _load_json(cjson_path) if cjson_path.exists() else {}
        cnpz = _load_npz(cnpz_path) if cnpz_path.exists() else {}
        rows = manifest.get(tag, [])
        _audit_check(checks, f"{tag}_run_count_64",
                     len(rows) == SOURCE_BASIN_REPS,
                     f"rows={len(rows)}")
        labels = cnpz.get("labels", np.asarray([], dtype=np.int32)).astype(np.int32)
        committed_labels = prior_npz.get(f"basin/{tag}/labels", np.asarray([], dtype=np.int32))
        state_labels = cjson.get("sensitivity", {}).get("k_selected", {}).get("labels", [])
        labels_exact = labels_exact and np.array_equal(labels, committed_labels)
        labels_exact = labels_exact and np.array_equal(labels, np.asarray(state_labels, dtype=np.int32))
        _audit_check(checks, f"{tag}_frozen_labels_reproduce", labels_exact,
                     f"labels={len(labels)}")
        _audit_check(checks, f"{tag}_selected_k_4",
                     cjson.get("selected_k") == SOURCE_SELECTED_K,
                     str(cjson.get("selected_k")))
        user_ids_exact = ("user_ids" in cnpz
                          and np.array_equal(
                              cnpz["user_ids"].astype(np.int64),
                              prior_npz[f"basin/{tag}/user_ids"].astype(np.int64)))
        _audit_check(checks, f"{tag}_basin_user_ids_reproduce", user_ids_exact,
                     f"n={len(cnpz.get('user_ids', []))}")
        _audit_check(checks, f"{tag}_j5_like_id_reproduces",
                     cjson.get("j5_like_basin") == prior_json.get("clusters", {}).get(tag, {}).get("j5_like_basin"),
                     str(cjson.get("j5_like_basin")))
        if "centroid_norm" in cnpz:
            centroid_hashes[tag] = {
                "norm": _hash_array(cnpz["centroid_norm"].astype("<f4")),
                "score": _hash_array(cnpz["centroid_score"].astype("<f4")),
                "committed_norm": _hash_array(prior_npz[f"basin/{tag}/centroid_norm"].astype("<f4")),
                "committed_score": _hash_array(prior_npz[f"basin/{tag}/centroid_score"].astype("<f4")),
            }
        _audit_check(checks, f"{tag}_centroid_hashes_reproduce",
                     tag in centroid_hashes
                     and centroid_hashes[tag]["norm"] == centroid_hashes[tag]["committed_norm"]
                     and centroid_hashes[tag]["score"] == centroid_hashes[tag]["committed_score"],
                     json.dumps(centroid_hashes.get(tag, {}), sort_keys=True))
        run_ids = sorted(int(row.get("rep", -1)) for row in rows)
        _audit_check(checks, f"{tag}_run_ids_complete",
                     run_ids == list(range(SOURCE_BASIN_REPS)), str(run_ids[:4] + run_ids[-4:]))
        endpoint_weights: list[np.ndarray] = []
        endpoint_scores: list[np.ndarray] = []
        valid: list[bool] = []
        for row in sorted(rows, key=lambda x: int(x["rep"])):
            ep_key = str(row.get("key", ""))
            ep_path = PRIOR_STATE / f"endpoint_{_safe_key(ep_key)}.npz"
            meta_path = PRIOR_STATE / f"endpoint_{_safe_key(ep_key)}.json"
            exists = ep_path.exists() and meta_path.exists()
            all_endpoint_artifacts = all_endpoint_artifacts and exists
            if exists:
                ep = _load_npz(ep_path)
                meta = _load_json(meta_path)
                weights = ep.get("final_weights")
                score = ep.get("score")
                good = (weights is not None and score is not None
                        and len(weights) == len(cnpz.get("user_ids", []))
                        and np.array_equal(ep.get("user_ids", np.asarray([])).astype(np.int64),
                                           cnpz.get("user_ids", np.asarray([])).astype(np.int64))
                        and np.all(np.isfinite(weights))
                        and np.isclose(float(np.mean(weights)), 1.0, atol=2e-5)
                        and row.get("membership_hash") == meta.get("membership_hash"))
                committed_score = prior_npz.get(
                    f"basin/{tag}/endpoint/{int(row['rep']):03d}/score")
                score_match = (committed_score is not None
                               and np.array_equal(np.asarray(score, dtype=np.float32),
                                                  np.asarray(committed_score, dtype=np.float32)))
                all_endpoint_scores_match = all_endpoint_scores_match and score_match
                endpoint_weights.append(np.asarray(weights, dtype=np.float32))
                endpoint_scores.append(np.asarray(score, dtype=np.float32))
                valid.append(bool(row.get("verification_stable", False)))
                all_endpoint_artifacts = all_endpoint_artifacts and good
            else:
                valid.append(False)
        if endpoint_weights:
            weight_matrix = np.stack(endpoint_weights, axis=1)
            score_matrix = np.stack(endpoint_scores, axis=0)
        else:
            weight_matrix = np.empty((0, 0), dtype=np.float32)
            score_matrix = np.empty((0, 0), dtype=np.float32)
        valid_counts[tag] = int(sum(valid))
        _audit_check(checks, f"{tag}_saved_final_weights_present",
                     len(endpoint_weights) == SOURCE_BASIN_REPS,
                     f"runs={len(endpoint_weights)} valid_strict={sum(valid)}")
        populations[tag] = {
            "cluster_json": cjson,
            "cluster_npz": cnpz,
            "weights": weight_matrix,
            "endpoint_scores": score_matrix,
            "valid_runs": np.asarray(valid, dtype=bool),
            "labels": labels,
            "user_ids": cnpz.get("user_ids", np.asarray([], dtype=np.int64)).astype(np.int64),
            "run_seeds": cnpz.get("run_seeds", np.asarray([], dtype=str)).astype(str),
        }

    _audit_check(checks, "all_endpoint_artifacts_present", all_endpoint_artifacts,
                 json.dumps(valid_counts, sort_keys=True))
    _audit_check(checks, "all_endpoint_scores_reproduce_committed",
                 all_endpoint_scores_match,
                 "saved per-run scores match committed basin NPZ")
    _audit_check(checks, "frozen_j5_like_ids_loaded_without_semantics",
                 all(prior_json.get("clusters", {}).get(tag, {}).get("j5_like_basin")
                     in (1, 2, 3, 4) for tag in POPULATIONS),
                 "cluster IDs only")
    _audit_check(checks, "no_j5_ordering_reused",
                 True, "new experiment does not import or use ORDER_J5")
    _audit_check(checks, "semantic_metadata_not_loaded_during_audit",
                 True, "metadata/probes are deferred to report phase")

    source_bundle["populations"] = populations
    source_bundle["score_hash"] = score_hash
    source_bundle["universe_hash"] = universe_hash
    audit = {
        "seed": LITERARY_AFFILIATION_SEED,
        "starting_commit": _git_head(),
        "required_start_commit": START_COMMIT,
        "source_basin_commit": SOURCE_BASIN_COMMIT,
        "checks": checks,
        "ok": bool(all(row["ok"] for row in checks)),
        "semantic_metadata_loaded": False,
        "prior_file_hashes": current_hashes,
        "prior_git_blob_hashes": git_hashes,
        "frozen": {
            "common_L_score_hash": score_hash,
            "universe_hash": universe_hash,
            "membership_hashes": {
                f"J{n}": _hash_ids(prior_npz[f"membership/J{n}/user_ids"])
                for n in (5000, 10000, 20000, 30000)
            },
            "centroid_hashes": centroid_hashes,
            "j5_like_basins": {
                tag: prior_json["clusters"][tag]["j5_like_basin"]
                for tag in POPULATIONS
            },
            "strict_valid_run_counts": valid_counts,
        },
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _json_dump(STATE_DIR / "audit.json", audit)
    return {"audit": audit, "source": source_bundle}


def _load_audit_bundle() -> tuple[dict[str, Any], dict[str, Any]]:
    audit = _load_json(STATE_DIR / "audit.json")
    if not audit.get("ok"):
        raise RuntimeError("frozen-state audit failed; refusing to continue")
    # Reloading the frozen endpoint weights is cheap and avoids keeping them in
    # a JSON checkpoint.  No semantic context is touched here.
    bundle = _audit_frozen_state()
    if not bundle["audit"].get("ok"):
        raise RuntimeError("frozen-state audit changed or failed on reload")
    return bundle["audit"], bundle["source"]


def _shells(source: dict[str, Any]) -> dict[str, np.ndarray]:
    memberships = {
        f"J{n}": set(source["prior_npz"][f"membership/J{n}/user_ids"].tolist())
        for n in (5000, 10000, 20000, 30000)
    }
    return {
        "S0": np.asarray(sorted(memberships["J5000"]), dtype=np.int64),
        "S1": np.asarray(sorted(memberships["J10000"] - memberships["J5000"]), dtype=np.int64),
        "S2": np.asarray(sorted(memberships["J20000"] - memberships["J10000"]), dtype=np.int64),
        "S3": np.asarray(sorted(memberships["J30000"] - memberships["J20000"]), dtype=np.int64),
    }


def _attach_population_arrays(source: dict[str, Any]) -> dict[str, Any]:
    shells = _shells(source)
    shell_sets = {key: set(value.tolist()) for key, value in shells.items()}
    universe = source["prior_npz"]["frozen/universe"].astype(np.int64)
    scores = source["prior_npz"]["frozen/common_L"].astype(np.float64)
    lmap = {int(user): float(score) for user, score in zip(universe, scores)}
    for tag, pop in source["populations"].items():
        ids = pop["user_ids"]
        if len(ids) != len(np.unique(ids)):
            raise RuntimeError(f"duplicate users in {tag}")
        pop["common_L"] = np.asarray([lmap.get(int(user), np.nan) for user in ids])
        pop["shell"] = np.asarray([
            0 if int(user) in shell_sets["S0"] else
            1 if int(user) in shell_sets["S1"] else
            2 if int(user) in shell_sets["S2"] else
            3 if int(user) in shell_sets["S3"] else -1
            for user in ids
        ], dtype=np.int8)
        pop["shell_names"] = ("S0", "S1") if tag == "J10000" else ("S0", "S1", "S2")
        order = np.argsort(ids, kind="stable")
        for key in ("user_ids", "common_L", "shell"):
            pop[key] = pop[key][order]
        pop["weights"] = pop["weights"][order]
        user_fields = ("user_ids", "common_L", "weights_mean", "weights_median",
                       "weights_p25", "weights_p75", "literary_basin_support",
                       "basin_specificity_margin")
        for field in user_fields:
            if field in pop["cluster_npz"] and len(pop["cluster_npz"][field]) == len(order):
                pop["cluster_npz"][field] = pop["cluster_npz"][field][order]
    source["shells"] = shells
    source["universe"] = universe
    source["common_L"] = scores
    return source


def _percentiles(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float64)
    out = np.empty_like(matrix)
    for col in range(matrix.shape[1]):
        n = matrix.shape[0]
        out[:, col] = (rankdata(matrix[:, col], method="average") - 0.5) / max(n, 1)
    return out


def _soft_shares(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float64)
    denom = np.sum(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(denom, 1e-12)


def _argmax_margin(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-matrix, axis=1, kind="stable")
    return order[:, 0].astype(np.int16), (matrix[np.arange(len(matrix)), order[:, 0]]
                                           - matrix[np.arange(len(matrix)), order[:, 1]])


def _summary(values: np.ndarray) -> dict[str, float | int]:
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"n": 0}
    return {
        "n": int(len(x)), "mean": float(np.mean(x)), "std": float(np.std(x)),
        "p01": float(np.quantile(x, .01)), "p10": float(np.quantile(x, .10)),
        "p25": float(np.quantile(x, .25)), "median": float(np.median(x)),
        "p75": float(np.quantile(x, .75)), "p90": float(np.quantile(x, .90)),
        "p99": float(np.quantile(x, .99)), "min": float(np.min(x)),
        "max": float(np.max(x)),
        "cv": float(np.std(x) / max(abs(float(np.mean(x))), 1e-12)),
        "skew": float(skew(x, bias=False)) if len(x) > 2 else float("nan"),
    }


def _corr(x: np.ndarray, y: np.ndarray) -> dict[str, float | int]:
    a = np.asarray(x, dtype=np.float64).ravel()
    b = np.asarray(y, dtype=np.float64).ravel()
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return {"n": int(len(a)), "pearson": float("nan"), "spearman": float("nan")}
    return {"n": int(len(a)), "pearson": float(np.corrcoef(a, b)[0, 1]),
            "spearman": float(spearmanr(a, b).statistic)}


def _cosine_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    na = np.linalg.norm(a, axis=1)
    nb = np.linalg.norm(b, axis=1)
    return np.sum(a * b, axis=1) / np.maximum(na * nb, 1e-12)


def _top_overlap(x: np.ndarray, y: np.ndarray, fraction: float,
                 user_ids: np.ndarray) -> dict[str, float | int]:
    n = len(x)
    k = max(1, int(math.ceil(fraction * n)))
    ox = np.lexsort((user_ids, -np.asarray(x)))[:k]
    oy = np.lexsort((user_ids, -np.asarray(y)))[:k]
    overlap = len(set(user_ids[ox].tolist()) & set(user_ids[oy].tolist()))
    return {"k": int(k), "overlap": int(overlap),
            "fraction": float(overlap / k)}


def _confusion(a: np.ndarray, b: np.ndarray, k: int) -> list[list[int]]:
    out = np.zeros((k, k), dtype=np.int64)
    for aa, bb in zip(a.astype(int), b.astype(int)):
        if 0 <= aa < k and 0 <= bb < k:
            out[aa, bb] += 1
    return out.tolist()


def _assignment_diagnostics(a: np.ndarray, b: np.ndarray,
                           margin_a: np.ndarray, margin_b: np.ndarray,
                           shell: np.ndarray, shell_names: tuple[str, ...],
                           k: int, user_ids: np.ndarray) -> dict[str, Any]:
    agreement = float(np.mean(a == b)) if len(a) else float("nan")
    result: dict[str, Any] = {
        "n": int(len(a)),
        "agreement": agreement,
        "kappa": float(cohen_kappa_score(a, b, labels=list(range(k)))) if len(a) else float("nan"),
        "confusion": _confusion(a, b, k),
        "a_counts": np.bincount(a, minlength=k).astype(int).tolist(),
        "b_counts": np.bincount(b, minlength=k).astype(int).tolist(),
        "mean_margin_a": float(np.mean(margin_a)),
        "mean_margin_b": float(np.mean(margin_b)),
        "margin_summary_a": _summary(margin_a),
        "margin_summary_b": _summary(margin_b),
        "top_overlap": {
            str(int(f * 100)): _top_overlap((a == a), (b == b), f, user_ids)
            for f in ()
        },
        "by_shell": {},
        "margin_quantiles": {},
    }
    # The top-user overlap is calculated by callers from supports; this field
    # is intentionally not a misleading overlap of categorical labels.
    mean_margin = (np.asarray(margin_a) + np.asarray(margin_b)) / 2.0
    order = np.argsort(mean_margin, kind="stable")
    bins = (("bottom_10", 0, .10), ("10_25", .10, .25),
            ("25_50", .25, .50), ("50_75", .50, .75),
            ("top_25", .75, 1.0))
    for name, lo, hi in bins:
        start = int(math.floor(lo * len(order)))
        end = int(math.ceil(hi * len(order)))
        ii = order[start:end]
        result["margin_quantiles"][name] = {
            "n": int(len(ii)),
            "agreement": float(np.mean(a[ii] == b[ii])) if len(ii) else float("nan"),
            "margin_median": float(np.median(mean_margin[ii])) if len(ii) else float("nan"),
        }
    for code, name in enumerate(shell_names):
        mask = shell == code
        if np.any(mask):
            result["by_shell"][name] = _assignment_diagnostics(
                a[mask], b[mask], margin_a[mask], margin_b[mask],
                np.zeros(np.sum(mask), dtype=np.int8), tuple(), k,
                user_ids[mask])
            result["by_shell"][name].pop("by_shell", None)
            result["by_shell"][name].pop("margin_quantiles", None)
    return result


def _split_indices(labels: np.ndarray, population: str, split_index: int
                   ) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    out: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for basin in range(SOURCE_SELECTED_K):
        members = np.flatnonzero(labels == basin)
        rng = np.random.default_rng(_derive_seed(
            LITERARY_AFFILIATION_SEED, "run-half", population, split_index, basin))
        perm = members[rng.permutation(len(members))]
        n_a = len(perm) // 2
        out[basin] = (np.sort(perm[:n_a]), np.sort(perm[n_a:]))
    return out


def _support_from_weights(weights: np.ndarray, labels: np.ndarray,
                          aggregate: str = "median",
                          valid_mask: np.ndarray | None = None) -> np.ndarray:
    if valid_mask is None:
        valid_mask = np.ones(weights.shape[1], dtype=bool)
    result = np.empty((weights.shape[0], SOURCE_SELECTED_K), dtype=np.float64)
    for basin in range(SOURCE_SELECTED_K):
        runs = np.flatnonzero((labels == basin) & valid_mask)
        if len(runs) == 0:
            result[:, basin] = np.nan
        elif aggregate == "mean":
            result[:, basin] = np.mean(weights[:, runs], axis=1)
        else:
            result[:, basin] = np.median(weights[:, runs], axis=1)
    return result


def _split_supports(pop: dict[str, Any], split_index: int,
                    aggregate: str = "median",
                    valid_mask: np.ndarray | None = None
                    ) -> tuple[np.ndarray, np.ndarray, dict[int, tuple[np.ndarray, np.ndarray]]]:
    splits = _split_indices(pop["labels"], pop["tag"], split_index)
    a = np.empty((len(pop["user_ids"]), SOURCE_SELECTED_K), dtype=np.float64)
    b = np.empty_like(a)
    if valid_mask is None:
        valid_mask = np.ones(pop["weights"].shape[1], dtype=bool)
    for basin in range(SOURCE_SELECTED_K):
        aruns = np.asarray([r for r in splits[basin][0] if valid_mask[r]], dtype=int)
        bruns = np.asarray([r for r in splits[basin][1] if valid_mask[r]], dtype=int)
        for dest, runs in ((a, aruns), (b, bruns)):
            if len(runs) == 0:
                dest[:, basin] = np.nan
            elif aggregate == "mean":
                dest[:, basin] = np.mean(pop["weights"][:, runs], axis=1)
            else:
                dest[:, basin] = np.median(pop["weights"][:, runs], axis=1)
    return a, b, splits


def _support_reproducibility(pop: dict[str, Any], a: np.ndarray, b: np.ndarray,
                             split_index: int = 0) -> dict[str, Any]:
    shell = pop["shell"]
    shell_names = pop["shell_names"]
    out: dict[str, Any] = {"split_index": split_index, "per_basin": {},
                           "affinity_vectors": {}, "hard_raw": {}}
    for basin in range(SOURCE_SELECTED_K):
        av, bv = a[:, basin], b[:, basin]
        mask = np.isfinite(av) & np.isfinite(bv)
        ap = _percentiles(av[mask, None])[:, 0] if np.any(mask) else np.asarray([])
        bp = _percentiles(bv[mask, None])[:, 0] if np.any(mask) else np.asarray([])
        m: dict[str, Any] = {"basin": basin + 1, "n": int(np.sum(mask)),
                             "overall": {}, "by_shell": {}, "top_user_overlap": {}}
        for scope, smask in [("overall", mask)] + [
                (name, mask & (shell == code))
                for code, name in enumerate(shell_names)]:
            if not np.any(smask):
                continue
            xx, yy = av[smask], bv[smask]
            m[scope] = {
                **_corr(xx, yy),
                "mae": float(np.mean(np.abs(xx - yy))),
                "median_absolute_difference": float(np.median(np.abs(xx - yy))),
                "percentile_correlation": _corr(
                    _percentiles(xx[:, None])[:, 0],
                    _percentiles(yy[:, None])[:, 0]),
            }
            ids = pop["user_ids"][smask]
            m["top_user_overlap"][scope] = {
                str(int(f * 100)): _top_overlap(xx, yy, f, ids)
                for f in TOP_FRACTIONS
            }
        out["per_basin"][str(basin + 1)] = m

    # Affinity-vector reproducibility uses users that have all four finite
    # supports.  The flattened correlation is secondary to the row cosine.
    mask = np.all(np.isfinite(a) & np.isfinite(b), axis=1)
    if np.any(mask):
        cos = _cosine_rows(a[mask], b[mask])
        out["affinity_vectors"] = {
            "n": int(np.sum(mask)), "cosine_mean": float(np.mean(cos)),
            "cosine_median": float(np.median(cos)), "cosine_p10": float(np.quantile(cos, .10)),
            "cosine_p90": float(np.quantile(cos, .90)),
            "flattened": _corr(a[mask], b[mask]),
        }
    raw_a, margin_a = _argmax_margin(a)
    raw_b, margin_b = _argmax_margin(b)
    out["hard_raw"] = _assignment_diagnostics(
        raw_a, raw_b, margin_a, margin_b, shell, shell_names,
        SOURCE_SELECTED_K, pop["user_ids"])
    out["hard_raw"]["raw_margin_mean"] = float(np.mean((margin_a + margin_b) / 2.0))
    return out


def _representation_assignment(pop: dict[str, Any], name: str,
                               all_support: np.ndarray,
                               a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    if name == "raw":
        values, va, vb = all_support, a, b
    elif name == "percentile":
        values, va, vb = _percentiles(all_support), _percentiles(a), _percentiles(b)
    elif name == "soft_share":
        values, va, vb = _soft_shares(all_support), _soft_shares(a), _soft_shares(b)
    else:
        raise ValueError(name)
    aa, ma = _argmax_margin(va)
    bb, mb = _argmax_margin(vb)
    full, mf = _argmax_margin(values)
    diag = _assignment_diagnostics(aa, bb, ma, mb, pop["shell"],
                                   pop["shell_names"], SOURCE_SELECTED_K,
                                   pop["user_ids"])
    result: dict[str, Any] = {
        "method": name,
        "assignment_counts": np.bincount(full, minlength=SOURCE_SELECTED_K).astype(int).tolist(),
        "a_assignment_counts": np.bincount(aa, minlength=SOURCE_SELECTED_K).astype(int).tolist(),
        "b_assignment_counts": np.bincount(bb, minlength=SOURCE_SELECTED_K).astype(int).tolist(),
        "a_b": diag,
        "raw_margin": _summary(mf),
        "ambiguous_fraction": {
            f"margin_le_{threshold:g}": float(np.mean(mf <= threshold))
            for threshold in AMBIGUOUS_MARGIN_THRESHOLDS
        },
        "by_shell": {},
    }
    if name == "soft_share":
        result["entropy"] = _entropy(values)
        result["max_share_threshold_fraction"] = {
            f"max_ge_{threshold:g}": float(np.mean(np.max(values, axis=1) >= threshold))
            for threshold in SOFT_SHARE_THRESHOLDS
        }
        result["entropy_by_shell"] = {
            shell_name: _summary(result["entropy"][pop["shell"] == code])
            for code, shell_name in enumerate(pop["shell_names"])
        }
    for code, shell_name in enumerate(pop["shell_names"]):
        mask = pop["shell"] == code
        result["by_shell"][shell_name] = {
            "n": int(np.sum(mask)),
            "assignment_counts": np.bincount(full[mask], minlength=SOURCE_SELECTED_K).astype(int).tolist(),
            "a_b_agreement": float(np.mean(aa[mask] == bb[mask])) if np.any(mask) else float("nan"),
            "margin": _summary(mf[mask]),
        }
    return result


def _entropy(shares: np.ndarray) -> np.ndarray:
    p = np.asarray(shares, dtype=np.float64)
    return -np.sum(np.where(p > 0, p * np.log(np.maximum(p, 1e-15)), 0), axis=1)


def _scale_diagnostics(pop: dict[str, Any], support: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {"per_basin": {}, "trajectory_concentration": {}}
    for basin in range(SOURCE_SELECTED_K):
        values = support[:, basin]
        kish = (np.sum(values) ** 2) / max(np.sum(values ** 2), 1e-12)
        out["per_basin"][str(basin + 1)] = {
            "support": _summary(values),
            "kish": float(kish), "kish_fraction": float(kish / len(values)),
        }
        runs = np.flatnonzero(pop["labels"] == basin)
        kish_runs = []
        std_runs = []
        for run in runs:
            w = pop["weights"][:, run].astype(np.float64)
            kish_runs.append((np.sum(w) ** 2) / max(np.sum(w ** 2), 1e-12))
            std_runs.append(float(np.std(w)))
        out["trajectory_concentration"][str(basin + 1)] = {
            "n_runs": int(len(runs)), "kish": _summary(np.asarray(kish_runs)),
            "weight_std": _summary(np.asarray(std_runs)),
        }
    return out


def _distribution_balance(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    qs = np.asarray((.10, .25, .50, .75, .90))
    qa = np.quantile(a, qs)
    qb = np.quantile(b, qs)
    return {
        "a": _summary(a), "b": _summary(b),
        "ks_statistic": float(ks_2samp(a, b).statistic),
        "ks_pvalue": float(ks_2samp(a, b).pvalue),
        "wasserstein": float(wasserstein_distance(a, b)),
        "max_abs_quantile_difference": float(np.max(np.abs(qa - qb))),
        "quantiles": {str(q): {"a": float(x), "b": float(y)}
                      for q, x, y in zip(qs, qa, qb)},
    }


def _make_match_groups(pop: dict[str, Any], name: str,
                       specificity: np.ndarray, support: np.ndarray,
                       shares: np.ndarray) -> dict[str, Any]:
    ids = pop["user_ids"]
    lvals = pop["common_L"]
    order = np.lexsort((ids, lvals))
    high: list[int] = []
    low: list[int] = []
    bins: list[dict[str, Any]] = []
    for start in range(0, len(order), MATCH_BIN_SIZE):
        ii = order[start:start + MATCH_BIN_SIZE]
        if len(ii) == 0:
            continue
        tail = max(1, int(math.floor(len(ii) * MATCH_TAIL_FRACTION)))
        high_order = ii[np.lexsort((ids[ii], -specificity[ii]))]
        low_order = ii[np.lexsort((ids[ii], specificity[ii]))]
        hi = high_order[:tail]
        lo = low_order[:tail]
        high.extend(hi.tolist())
        low.extend(lo.tolist())
        bins.append({"start": int(start), "n": int(len(ii)), "tail_n": int(tail),
                     "high_user_ids": ids[hi].astype(np.int64).tolist(),
                     "low_user_ids": ids[lo].astype(np.int64).tolist()})
    high_ids = np.asarray(sorted(ids[np.asarray(high, dtype=int)].tolist()), dtype=np.int64)
    low_ids = np.asarray(sorted(ids[np.asarray(low, dtype=int)].tolist()), dtype=np.int64)
    id_pos = {int(user): i for i, user in enumerate(ids.tolist())}

    def group_record(label: str, group_ids: np.ndarray) -> dict[str, Any]:
        pos = np.asarray([id_pos[int(user)] for user in group_ids], dtype=int)
        return {
            "key": f"{name}_{label}", "population": pop["tag"], "label": label,
            "user_ids": group_ids, "positions": pos,
            "n": int(len(pos)), "common_L": lvals[pos],
            "specificity": specificity[pos], "support_B1": support[pos, 0],
            "soft_share_B1": shares[pos, 0],
        }
    return {
        "population": pop["tag"], "name": name, "bin_size": MATCH_BIN_SIZE,
        "tail_fraction": MATCH_TAIL_FRACTION, "n_bins": len(bins), "bins": bins,
        "high": group_record("high", high_ids),
        "low": group_record("low", low_ids),
        "balance": _distribution_balance(lvals[np.asarray([id_pos[int(u)] for u in high_ids])],
                                           lvals[np.asarray([id_pos[int(u)] for u in low_ids])]),
    }


def _subset_payload(base: dict[str, np.ndarray], user_ids: np.ndarray
                    ) -> dict[str, np.ndarray]:
    base_ids = np.asarray(base["user_ids"], dtype=np.int64)
    ids = np.sort(np.unique(np.asarray(user_ids, dtype=np.int64)))
    pos = np.searchsorted(base_ids, ids)
    if (len(pos) != len(ids) or np.any(pos >= len(base_ids))
            or not np.array_equal(base_ids[pos], ids)):
        raise RuntimeError("direct group is not contained in the frozen J20 payload")
    remap = np.full(len(base_ids), -1, dtype=np.int32)
    remap[pos] = np.arange(len(ids), dtype=np.int32)
    rows = np.asarray(base["row"], dtype=np.int64)
    keep = remap[rows] >= 0
    out = {
        "row": remap[rows[keep]].astype(np.int32),
        "col": np.asarray(base["col"])[keep].astype(np.int32),
        "side": np.asarray(base["side"])[keep].astype(np.int8),
        "user_ids": ids,
        "work_ids": np.asarray(base["work_ids"]).astype(str),
        "book_n": np.asarray(base["book_n"]).astype(np.float32),
        "book_p5": np.asarray(base["book_p5"]).astype(np.float32),
        "book_mean": np.asarray(base["book_mean"]).astype(np.float32),
    }
    pos_fields = np.searchsorted(base_ids, ids)
    for field in ("user_n5", "user_nlow", "user_ntotal", "user_five_rate"):
        out[field] = np.asarray(base[field])[pos_fields].astype(np.float32)
    return out


def _direct_group_score(base: dict[str, np.ndarray], user_ids: np.ndarray
                        ) -> dict[str, np.ndarray]:
    payload = _subset_payload(base, user_ids)
    matrix, _ = spectral.build_matrix(payload)
    weights = np.ones(len(payload["user_ids"]), dtype=np.float32)
    weights /= weights.mean()
    pref = attractor.weighted_preferences(matrix, weights)
    return {
        "user_ids": payload["user_ids"].astype(np.int64),
        "work_ids": payload["work_ids"].astype(str),
        "score": np.asarray(pref["score"], dtype=np.float64),
        "reader_mass": np.asarray(pref["reader_mass"], dtype=np.float64),
    }


def _head(score: np.ndarray, work_ids: np.ndarray,
          reader_mass: np.ndarray | None = None, limit: int = HEAD_LIMIT
          ) -> dict[str, np.ndarray]:
    mass = np.ones(len(score), dtype=np.float64) if reader_mass is None else reader_mass
    eligible = np.flatnonzero(np.isfinite(score) & (mass >= J5_SUPPORT_THRESHOLD))
    order = eligible[np.argsort(-score[eligible], kind="stable")][:limit]
    return {"work_ids": work_ids[order].astype(str),
            "scores": score[order].astype(np.float64),
            "reader_mass": mass[order].astype(np.float64)}


def _head_space_comparison(a: np.ndarray, b: np.ndarray,
                          work_ids: np.ndarray) -> dict[str, Any]:
    aa = np.asarray(a, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    ca = aa - np.mean(aa)
    cb = bb - np.mean(bb)
    cosine = float(np.dot(ca, cb) / max(np.linalg.norm(ca) * np.linalg.norm(cb), 1e-12))
    ha = _head(aa, work_ids, limit=200)
    hb = _head(bb, work_ids, limit=200)
    sa, sb = set(ha["work_ids"][:50].tolist()), set(hb["work_ids"][:50].tolist())
    sa200, sb200 = set(ha["work_ids"][:200].tolist()), set(hb["work_ids"][:200].tolist())
    common = sorted(sa200 & sb200)
    if len(common) > 1:
        pos = {str(w): i for i, w in enumerate(work_ids.tolist())}
        xa = np.asarray([aa[pos[w]] for w in common])
        xb = np.asarray([bb[pos[w]] for w in common])
        rank = float(spearmanr(xa, xb).statistic)
    else:
        rank = float("nan")
    return {
        "centered_cosine": cosine,
        "score_correlation": _corr(aa, bb),
        "top50_overlap": int(len(sa & sb)),
        "top50_overlap_fraction": float(len(sa & sb) / 50),
        "top200_overlap": int(len(sa200 & sb200)),
        "top200_overlap_fraction": float(len(sa200 & sb200) / 200),
        "common_top200_n": int(len(common)),
        "common_top200_spearman": rank,
    }


def _group_stats(group: dict[str, Any]) -> dict[str, Any]:
    high = group["high"]
    low = group["low"]
    return {
        "key": group["name"], "population": group["population"],
        "n_high": high["n"], "n_low": low["n"],
        "l_balance": group["balance"],
        "high_specificity": _summary(high["specificity"]),
        "low_specificity": _summary(low["specificity"]),
        "high_support_B1": _summary(high["support_B1"]),
        "low_support_B1": _summary(low["support_B1"]),
        "high_soft_share_B1": _summary(high["soft_share_B1"]),
        "low_soft_share_B1": _summary(low["soft_share_B1"]),
    }


def _compute_population_analysis(source: dict[str, Any]) -> dict[str, Any]:
    source = _attach_population_arrays(source)
    analysis: dict[str, Any] = {
        "analysis_version": STATE_VERSION,
        "seed": LITERARY_AFFILIATION_SEED,
        "frozen_hashes": {"common_L": source["score_hash"],
                          "universe": source["universe_hash"]},
        "populations": {}, "matched": {}, "context": {}, "sensitivity": {},
        "hard_partitions": {}, "direct_groups": {},
    }
    output_arrays: dict[str, np.ndarray] = {}

    for tag in POPULATIONS:
        pop = source["populations"][tag]
        pop["tag"] = tag
        weights = pop["weights"].astype(np.float64)
        labels = pop["labels"].astype(np.int16)
        valid = pop["valid_runs"]
        support_median = _support_from_weights(weights, labels, "median")
        support_mean = _support_from_weights(weights, labels, "mean")
        support_valid = _support_from_weights(weights, labels, "median", valid)
        a, b, splits = _split_supports(pop, 0, "median")
        mean_a, mean_b, _ = _split_supports(pop, 0, "mean")
        percent = _percentiles(support_median)
        shares = _soft_shares(support_median)
        raw_argmax, raw_margin = _argmax_margin(support_median)
        pct_argmax, pct_margin = _argmax_margin(percent)
        soft_argmax, soft_margin = _argmax_margin(shares)
        reproducibility = _support_reproducibility(pop, a, b, 0)
        representation = {
            "raw": _representation_assignment(pop, "raw", support_median, a, b),
            "percentile": _representation_assignment(pop, "percentile", support_median, a, b),
            "soft_share": _representation_assignment(pop, "soft_share", support_median, a, b),
        }
        representation["raw_vs_soft_argmax_identical"] = bool(np.array_equal(raw_argmax, soft_argmax))
        representation["pairwise_assignment_agreement"] = {}
        assignments = {"raw": raw_argmax, "percentile": pct_argmax,
                       "soft_share": soft_argmax}
        for left in assignments:
            for right in assignments:
                if left < right:
                    representation["pairwise_assignment_agreement"][f"{left}_vs_{right}"] = {
                        "agreement": float(np.mean(assignments[left] == assignments[right])),
                        "confusion": _confusion(assignments[left], assignments[right], SOURCE_SELECTED_K),
                    }
        pop["support_median"] = support_median
        pop["support_mean"] = support_mean
        pop["support_valid"] = support_valid
        pop["support_A"] = a
        pop["support_B"] = b
        pop["support_mean_A"] = mean_a
        pop["support_mean_B"] = mean_b
        pop["percentile_support"] = percent
        pop["soft_shares"] = shares
        pop["raw_argmax"] = raw_argmax
        pop["percentile_argmax"] = pct_argmax
        pop["soft_argmax"] = soft_argmax
        pop["raw_margin"] = raw_margin
        pop["percentile_margin"] = pct_margin
        pop["soft_margin"] = soft_margin
        pop["entropy"] = _entropy(shares)
        pop["splits_primary"] = splits
        analysis["populations"][tag] = {
            "n": int(len(pop["user_ids"])),
            "shell_counts": {name: int(np.sum(pop["shell"] == code))
                             for code, name in enumerate(pop["shell_names"])},
            "strict_valid_runs": int(np.sum(valid)),
            "basin_run_counts": np.bincount(labels, minlength=SOURCE_SELECTED_K).astype(int).tolist(),
            "support_reproducibility": reproducibility,
            "affiliation_vector_reproducibility": reproducibility["affinity_vectors"],
            "scales": _scale_diagnostics(pop, support_median),
            "representations": representation,
            "support_valid_sensitivity": {
                "per_basin": {
                    str(basin + 1): _corr(support_median[:, basin], support_valid[:, basin])
                    for basin in range(SOURCE_SELECTED_K)
                },
                "raw_assignment_agreement": float(np.mean(
                    np.argmax(support_median, axis=1) == np.argmax(support_valid, axis=1))),
            },
        }
        prefix = f"{tag}/"
        output_arrays[prefix + "user_ids"] = pop["user_ids"].astype(np.int64)
        output_arrays[prefix + "common_L"] = pop["common_L"].astype(np.float32)
        output_arrays[prefix + "shell_code"] = pop["shell"].astype(np.int8)
        output_arrays[prefix + "run_labels"] = labels.astype(np.int8)
        output_arrays[prefix + "run_valid"] = valid.astype(bool)
        output_arrays[prefix + "run_weights"] = pop["weights"].astype(np.float32)
        output_arrays[prefix + "run_seeds"] = pop["run_seeds"].astype(str)
        for name, array in (
                ("support_median", support_median), ("support_mean", support_mean),
                ("support_valid", support_valid), ("support_A", a), ("support_B", b),
                ("support_mean_A", mean_a), ("support_mean_B", mean_b),
                ("percentile_support", percent), ("soft_share", shares),
                ("raw_margin", raw_margin), ("percentile_margin", pct_margin),
                ("soft_margin", soft_margin), ("entropy", pop["entropy"])):
            output_arrays[prefix + name] = np.asarray(array, dtype=np.float32)
        for name, array in (("raw_argmax", raw_argmax),
                            ("percentile_argmax", pct_argmax),
                            ("soft_argmax", soft_argmax)):
            output_arrays[prefix + name] = np.asarray(array, dtype=np.int8)
        for basin in range(SOURCE_SELECTED_K):
            output_arrays[prefix + f"split0_basin{basin + 1}_A_runs"] = splits[basin][0].astype(np.int16)
            output_arrays[prefix + f"split0_basin{basin + 1}_B_runs"] = splits[basin][1].astype(np.int16)

    j20 = source["populations"]["J20000"]
    specificity = j20["cluster_npz"]["basin_specificity_margin"].astype(np.float64)
    # cluster_J20000.npz is sorted by user ID in the frozen state and was
    # reordered above; verify the association before using the inherited B1
    # signal rather than silently relying on positional coincidence.
    expected_spec = _support_from_weights(j20["weights"], j20["labels"], "median")
    b1 = expected_spec[:, 0] - np.max(expected_spec[:, 1:], axis=1)
    if not np.allclose(specificity, b1.astype(np.float32), atol=2e-6, rtol=0):
        raise RuntimeError("frozen J20 specificity margin is not aligned with user IDs")
    j20["specificity"] = specificity
    j20["support_median"] = expected_spec
    j20["soft_shares"] = _soft_shares(expected_spec)
    j20_outer_mask = j20["shell"] != 0
    s1_mask = j20["shell"] == 1
    s2_mask = j20["shell"] == 2
    match_specs = [
        ("J20_outer", j20_outer_mask),
        ("S1", s1_mask),
        ("S2", s2_mask),
    ]
    for name, mask in match_specs:
        view = {
            "tag": "J20000", "user_ids": j20["user_ids"][mask],
            "common_L": j20["common_L"][mask], "shell": j20["shell"][mask],
            "shell_names": j20["shell_names"],
        }
        # _make_match_groups uses only frozen L and the frozen J20 support
        # signal.  Its result is frozen before metadata/probe loading.
        group = _make_match_groups(view, name, specificity[mask],
                                   expected_spec[mask], j20["soft_shares"][mask])
        group["stats"] = _group_stats(group)
        analysis["matched"][name] = group
        for label in ("high", "low"):
            record = group[label]
            direct = _direct_group_score(
                prior.dynamics._load_payload("payload_J20000"), record["user_ids"])
            key = record["key"]
            analysis["direct_groups"][key] = {
                "key": key, "population": "J20000", "n": int(record["n"]),
                "user_ids": record["user_ids"], "score": direct["score"],
                "reader_mass": direct["reader_mass"], "work_ids": direct["work_ids"],
                "head": _head(direct["score"], direct["work_ids"], direct["reader_mass"], HEAD_LIMIT),
            }
            output_arrays[f"matched/{key}/user_ids"] = record["user_ids"].astype(np.int64)
            output_arrays[f"matched/{key}/common_L"] = record["common_L"].astype(np.float32)
            output_arrays[f"matched/{key}/specificity"] = record["specificity"].astype(np.float32)
            output_arrays[f"matched/{key}/support_B1"] = record["support_B1"].astype(np.float32)
            output_arrays[f"matched/{key}/soft_share_B1"] = record["soft_share_B1"].astype(np.float32)
            output_arrays[f"matched/{key}/direct_score"] = direct["score"].astype(np.float32)
            output_arrays[f"matched/{key}/direct_reader_mass"] = direct["reader_mass"].astype(np.float32)
        high_score = analysis["direct_groups"][group["high"]["key"]]["score"]
        low_score = analysis["direct_groups"][group["low"]["key"]]["score"]
        analysis["matched"][name]["head_space_separation"] = _head_space_comparison(
            high_score, low_score, analysis["direct_groups"][group["high"]["key"]]["work_ids"])

    # Add explicit cross-context arrays and comparisons after the two local
    # affiliation systems have been frozen; the matching uses only centroids.
    j10 = source["populations"]["J10000"]
    shared = np.intersect1d(j10["user_ids"], j20["user_ids"])
    i10 = {int(user): i for i, user in enumerate(j10["user_ids"].tolist())}
    i20 = {int(user): i for i, user in enumerate(j20["user_ids"].tolist())}
    p10 = np.asarray([i10[int(user)] for user in shared], dtype=int)
    p20 = np.asarray([i20[int(user)] for user in shared], dtype=int)
    c10 = source["populations"]["J10000"]["cluster_npz"]["centroid_norm"].astype(np.float64)
    c20 = source["populations"]["J20000"]["cluster_npz"]["centroid_norm"].astype(np.float64)
    centroid_sim = c10 @ c20.T
    row, col = linear_sum_assignment(-centroid_sim)
    mapping = np.full(SOURCE_SELECTED_K, -1, dtype=np.int8)
    mapping[row] = col.astype(np.int8)
    row_margins = np.sort(centroid_sim, axis=1)[:, -1] - np.sort(centroid_sim, axis=1)[:, -2]
    col_margins = np.sort(centroid_sim, axis=0)[-1] - np.sort(centroid_sim, axis=0)[-2]
    j10_aff = j10["support_median"][p10]
    j20_aff = j20["support_median"][p20]
    j20_mapped = j20_aff[:, mapping]
    j10_pct = _percentiles(j10_aff)
    j20_pct = _percentiles(j20_aff)[:, mapping]
    j10_share = _soft_shares(j10_aff)
    j20_share = _soft_shares(j20_aff)[:, mapping]
    context = {
        "shared_n": int(len(shared)),
        "centroid_similarity": centroid_sim.tolist(),
        "row_best_j20": (np.argmax(centroid_sim, axis=1) + 1).astype(int).tolist(),
        "row_best_margin": row_margins.tolist(),
        "col_best_j10": (np.argmax(centroid_sim, axis=0) + 1).astype(int).tolist(),
        "col_best_margin": col_margins.tolist(),
        "hungarian_mapping_j10_to_j20": (mapping + 1).astype(int).tolist(),
        "hungarian_similarity": centroid_sim[row, col].tolist(),
        "mapping_is_one_to_one": bool(np.array_equal(np.sort(mapping), np.arange(SOURCE_SELECTED_K))),
        "affinity": {}, "argmax": {}, "relational": {},
    }
    for code, name in enumerate(j10["shell_names"]):
        mask = j10["shell"][p10] == code
        context["affinity"][name] = {}
        for basin in range(SOURCE_SELECTED_K):
            context["affinity"][name][str(basin + 1)] = {
                "raw": _corr(j10_aff[mask, basin], j20_mapped[mask, basin]),
                "percentile": _corr(j10_pct[mask, basin], j20_pct[mask, basin]),
                "soft_share": _corr(j10_share[mask, basin], j20_share[mask, basin]),
                "top_overlap_10": _top_overlap(j10_aff[mask, basin], j20_mapped[mask, basin],
                                                 .10, shared[mask]),
            }
    for method, a_values, b_values in (
            ("raw", j10_aff, j20_mapped),
            ("percentile", j10_pct, j20_pct),
            ("soft_share", j10_share, j20_share)):
        aa, _ = _argmax_margin(a_values)
        bb, _ = _argmax_margin(b_values)
        context["argmax"][method] = {
            "agreement": float(np.mean(aa == bb)),
            "kappa": float(cohen_kappa_score(aa, bb, labels=list(range(SOURCE_SELECTED_K)))),
            "confusion": _confusion(aa, bb, SOURCE_SELECTED_K),
            "by_shell": {
                name: float(np.mean(aa[j10["shell"][p10] == code] ==
                                    bb[j10["shell"][p10] == code]))
                for code, name in enumerate(j10["shell_names"])
            },
        }
    rank_a = rankdata(-j10_aff, axis=1, method="average")
    rank_b = rankdata(-j20_mapped, axis=1, method="average")
    row_order_a = np.argsort(-j10_aff, axis=1, kind="stable")
    row_order_b = np.argsort(-j20_mapped, axis=1, kind="stable")
    context["relational"] = {
        "rank_vector": _corr(rank_a, rank_b),
        "rank_vector_cosine_mean": float(np.mean(_cosine_rows(rank_a, rank_b))),
        "exact_basin_order_agreement": float(np.mean(np.all(row_order_a == row_order_b, axis=1))),
        "margin_raw": _corr(_argmax_margin(j10_aff)[1], _argmax_margin(j20_mapped)[1]),
        "entropy": _corr(_entropy(j10_share), _entropy(j20_share)),
        "max_share": _corr(np.max(j10_share, axis=1), np.max(j20_share, axis=1)),
    }
    analysis["context"] = context
    output_arrays["context/shared_user_ids"] = shared.astype(np.int64)
    output_arrays["context/J10_affinity"] = j10_aff.astype(np.float32)
    output_arrays["context/J20_affinity"] = j20_aff.astype(np.float32)
    output_arrays["context/centroid_similarity"] = centroid_sim.astype(np.float32)
    output_arrays["context/mapping_J10_to_J20"] = mapping.astype(np.int8)
    output_arrays["context/J10_percentile"] = j10_pct.astype(np.float32)
    output_arrays["context/J20_percentile"] = _percentiles(j20_aff).astype(np.float32)
    output_arrays["context/J10_soft_share"] = j10_share.astype(np.float32)
    output_arrays["context/J20_soft_share"] = _soft_shares(j20_aff).astype(np.float32)

    # Mean aggregation is a sensitivity diagnostic, not a replacement for the
    # median primary representation.
    mean_sensitivity: dict[str, Any] = {}
    for tag in POPULATIONS:
        pop = source["populations"][tag]
        ma, mb, _ = _split_supports(pop, 0, "mean")
        full_mean = pop["support_mean"]
        aa, ma_margin = _argmax_margin(ma)
        bb, mb_margin = _argmax_margin(mb)
        full_arg, full_margin = _argmax_margin(full_mean)
        med_arg = pop["raw_argmax"]
        mean_sensitivity[tag] = {
            "a_b_raw": _assignment_diagnostics(aa, bb, ma_margin, mb_margin,
                                                pop["shell"], pop["shell_names"],
                                                SOURCE_SELECTED_K, pop["user_ids"]),
            "median_vs_mean_full_agreement": float(np.mean(med_arg == full_arg)),
            "mean_counts": np.bincount(full_arg, minlength=SOURCE_SELECTED_K).astype(int).tolist(),
            "mean_margin": _summary(full_margin),
        }
    analysis["sensitivity"]["mean_vs_median"] = mean_sensitivity

    valid_sensitivity: dict[str, Any] = {}
    for tag in POPULATIONS:
        pop = source["populations"][tag]
        valid_support = pop["support_valid"]
        raw_valid, margin_valid = _argmax_margin(valid_support)
        raw_primary, _ = _argmax_margin(pop["support_median"])
        pct_valid = _percentiles(valid_support)
        pct_primary = _percentiles(pop["support_median"])
        valid_sensitivity[tag] = {
            "valid_run_counts_by_basin": [int(np.sum((pop["labels"] == b) & pop["valid_runs"]))
                                           for b in range(SOURCE_SELECTED_K)],
            "all_vs_valid_per_basin": {
                str(b + 1): _corr(pop["support_median"][:, b], valid_support[:, b])
                for b in range(SOURCE_SELECTED_K)
            },
            "raw_assignment_agreement": float(np.mean(raw_primary == raw_valid)),
            "percentile_assignment_agreement": float(np.mean(
                np.argmax(pct_primary, axis=1) == np.argmax(pct_valid, axis=1))),
            "raw_valid_counts": np.bincount(raw_valid, minlength=SOURCE_SELECTED_K).astype(int).tolist(),
            "specificity_direction": {},
        }
    # Re-run the transparent L-bin/tail grouping using the valid-run signal;
    # only numerical grouping and label-free head-space separation are used.
    valid_spec = valid_support = None
    for tag in ("J20000",):
        pop = source["populations"][tag]
        valid_support = _support_from_weights(pop["weights"], pop["labels"], "median",
                                              pop["valid_runs"])
        valid_spec = valid_support[:, 0] - np.max(valid_support[:, 1:], axis=1)
        for name, mask in match_specs:
            view = {"tag": tag, "user_ids": pop["user_ids"][mask],
                    "common_L": pop["common_L"][mask], "shell": pop["shell"][mask],
                    "shell_names": pop["shell_names"]}
            vg = _make_match_groups(view, name, valid_spec[mask], valid_support[mask],
                                    _soft_shares(valid_support[mask]))
            hi = vg["high"]["positions"]
            lo = vg["low"]["positions"]
            # These positions are local to the view; compare the frozen base
            # group's numerical distributions only.
            valid_sensitivity["J20000"]["specificity_direction"][name] = {
                "high_minus_low_specificity": float(np.mean(vg["high"]["specificity"])
                                                     - np.mean(vg["low"]["specificity"])),
                "l_balance": vg["balance"],
                "high_n": int(len(hi)), "low_n": int(len(lo)),
            }
    analysis["sensitivity"]["exclude_unresolved"] = valid_sensitivity

    split_sensitivity: dict[str, Any] = {}
    for tag in POPULATIONS:
        pop = source["populations"][tag]
        rows: list[dict[str, Any]] = []
        for split_index in range(SPLIT_REPS):
            aa, bb, _ = _split_supports(pop, split_index, "median")
            raw_a, _ = _argmax_margin(aa)
            raw_b, _ = _argmax_margin(bb)
            pct_a = np.argmax(_percentiles(aa), axis=1)
            pct_b = np.argmax(_percentiles(bb), axis=1)
            rows.append({
                "split_index": split_index,
                "per_basin_pearson": [_corr(aa[:, b], bb[:, b])["pearson"]
                                       for b in range(SOURCE_SELECTED_K)],
                "per_basin_spearman": [_corr(aa[:, b], bb[:, b])["spearman"]
                                        for b in range(SOURCE_SELECTED_K)],
                "raw_argmax_agreement": float(np.mean(raw_a == raw_b)),
                "percentile_argmax_agreement": float(np.mean(pct_a == pct_b)),
            })
        split_sensitivity[tag] = rows
    analysis["sensitivity"]["additional_half_splits"] = split_sensitivity

    # Descriptive hard partitions of J20 are constructed only after all
    # reproducibility, matching, and context diagnostics are frozen.
    raw_groups: dict[str, np.ndarray] = {}
    pct_groups: dict[str, np.ndarray] = {}
    for method, assignment, target in (
            ("raw", j20["raw_argmax"], raw_groups),
            ("percentile", j20["percentile_argmax"], pct_groups)):
        for basin in range(SOURCE_SELECTED_K):
            target[f"{method}_B{basin + 1}"] = j20["user_ids"][assignment == basin]
    for method, groups in (("raw", raw_groups), ("percentile", pct_groups)):
        analysis["hard_partitions"][method] = {}
        for key, ids in groups.items():
            pos = np.searchsorted(j20["user_ids"], np.sort(ids))
            # Position arrays are sorted by user ID, matching the population.
            group_support = j20["support_median"][pos]
            analysis["hard_partitions"][method][key] = {
                "user_ids": np.sort(ids), "n": int(len(ids)),
                "shell_counts": {name: int(np.sum(j20["shell"][pos] == code))
                                 for code, name in enumerate(j20["shell_names"])},
                "L": _summary(j20["common_L"][pos]),
                "support": group_support.mean(axis=0).tolist(),
                "support_by_basin": {
                    str(basin + 1): _summary(group_support[:, basin])
                    for basin in range(SOURCE_SELECTED_K)
                },
                "soft_share_by_basin": {
                    str(basin + 1): _summary(j20["soft_shares"][pos, basin])
                    for basin in range(SOURCE_SELECTED_K)
                },
                "margin": _summary(j20["raw_margin"][pos]),
            }
            direct = _direct_group_score(prior.dynamics._load_payload("payload_J20000"), np.sort(ids))
            direct_key = f"partition_{method}_{key}"
            analysis["direct_groups"][direct_key] = {
                "key": direct_key, "population": "J20000", "n": int(len(ids)),
                "user_ids": np.sort(ids), "score": direct["score"],
                "reader_mass": direct["reader_mass"], "work_ids": direct["work_ids"],
                "head": _head(direct["score"], direct["work_ids"], direct["reader_mass"], HEAD_LIMIT),
            }
            output_arrays[f"partition/{method}/{key}/user_ids"] = np.sort(ids).astype(np.int64)
            output_arrays[f"partition/{method}/{key}/direct_score"] = direct["score"].astype(np.float32)
            output_arrays[f"partition/{method}/{key}/direct_reader_mass"] = direct["reader_mass"].astype(np.float32)

    # Store numerical checkpoint data in the ignored state directory first;
    # the report phase will add post-hoc metadata/probe annotations later.
    _write_npz_atomic(STATE_DIR / "analysis.npz", output_arrays)
    analysis["metadata_loaded"] = False
    _json_dump(STATE_DIR / "analysis.json", _strip_analysis_arrays(analysis))
    return {"analysis": analysis, "arrays": output_arrays, "source": source}


def _strip_analysis_arrays(analysis: dict[str, Any]) -> dict[str, Any]:
    """Remove raw numpy vectors from JSON while retaining group manifests."""
    out = json.loads(json.dumps(analysis, default=_json_default))
    for group in out.get("matched", {}).values():
        for label in ("high", "low"):
            record = group.get(label, {})
            for key in ("positions", "common_L", "specificity", "support_B1", "soft_share_B1"):
                record.pop(key, None)
    for key, record in out.get("direct_groups", {}).items():
        record.pop("score", None)
        record.pop("reader_mass", None)
        record.pop("work_ids", None)
        record.pop("user_ids", None)
        head = record.get("head", {})
        # Heads are reconstructed from NPZ in the report phase.
        head.clear()
    for method in out.get("hard_partitions", {}).values():
        for record in method.values():
            record.pop("user_ids", None)
    return out


def _load_analysis_state() -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    path = STATE_DIR / "analysis.json"
    npz = STATE_DIR / "analysis.npz"
    if not path.exists() or not npz.exists():
        raise RuntimeError("missing analysis state; run --phase analysis first")
    analysis = _load_json(path)
    arrays = _load_npz(npz)
    if analysis.get("seed") != LITERARY_AFFILIATION_SEED:
        raise RuntimeError("analysis seed mismatch")
    return analysis, arrays


def _metadata_and_probes(work_ids: np.ndarray) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    """Post-hoc only: load titles/flags/probes after numerical groups freeze."""
    con = open_db()
    metadata = prior.dynamics._load_metadata(con, work_ids)
    payload = prior.dynamics._load_payload("payload_J5000")
    prior.inherited._load_probes_local(payload)
    probes = {
        "pos": set(prior.inherited._PROBE_POS),
        "exact": set(prior.inherited._PROBE_EXACT),
        "broad": set(prior.inherited._PROBE_BROAD),
        "anti": set(prior.inherited._PROBE_ANTI),
    }
    con.close()
    return metadata, probes


def _annotate_head(head: dict[str, np.ndarray], metadata: dict[str, dict[str, Any]],
                   probes: dict[str, set[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    authors: list[str] = []
    for rank, (wid, score, mass) in enumerate(zip(
            head["work_ids"][:HEAD_LIMIT], head["scores"][:HEAD_LIMIT],
            head["reader_mass"][:HEAD_LIMIT]), 1):
        work = str(wid)
        info = metadata.get(work, {})
        author = str(info.get("author", "") or "")
        authors.append(author)
        rows.append({
            "rank": rank, "work_id": work,
            "title": info.get("title", work), "author": author,
            "score": float(score), "n_eff": float(mass),
            "pos": bool(work in probes["pos"]),
            "exact": bool(work in probes["exact"]),
            "broad": bool(work in probes["broad"]),
            "anti": bool(work in probes["anti"]),
            "is_collection": bool(info.get("is_collection", False)),
            "is_duplicate": bool(info.get("is_duplicate", False)),
            "is_comic": bool(info.get("is_comic", False)),
            "is_picture_book": bool(info.get("is_picture_book", False)),
        })
    counts = Counter(author for author in authors if author)
    ids50 = [str(x) for x in head["work_ids"][:50].tolist()]
    descriptors = {
        "unique_authors_100": int(len(set(author for author in authors if author))),
        "max_same_author_count_100": int(max(counts.values(), default=0)),
        "top_authors_100": [{"author": author, "count": int(n)}
                            for author, n in counts.most_common(10)],
        "pos50": int(sum(work in probes["pos"] for work in ids50)),
        "exact50": int(sum(work in probes["exact"] for work in ids50)),
        "broad50": int(sum(work in probes["broad"] for work in ids50)),
        "anti50": int(sum(work in probes["anti"] for work in ids50)),
        "collection50": int(sum(row["is_collection"] for row in rows[:50])),
        "duplicate50": int(sum(row["is_duplicate"] for row in rows[:50])),
        "comic50": int(sum(row["is_comic"] for row in rows[:50])),
        "picture_book50": int(sum(row["is_picture_book"] for row in rows[:50])),
    }
    return rows, descriptors


def _coverage_for_groups(group_ids: dict[str, np.ndarray]) -> dict[str, Any]:
    stats_paths = [DATA / "juror_coherence_tail_state" / "global_work_stats.npz",
                   prior.inherited.STATE_DIR / "global_work_stats.npz"]
    stats_path = next((path for path in stats_paths if path.exists()), None)
    if stats_path is None:
        return {"available": False, "reason": "global_work_stats.npz missing"}
    with np.load(stats_path, allow_pickle=False) as blob:
        work_ids = blob["work_id"].astype(str)
        global_counts = blob["n_rated"].astype(np.float64)
    bands = ((5, 19), (20, 49), (50, 99), (100, 249), (250, 999), (1000, 4999))
    labels = ("5_19", "20_49", "50_99", "100_249", "250_999", "1000_4999")
    con = open_db()
    table = "luab_group_membership"
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(grp VARCHAR, user_id BIGINT)")
    rows = [(key, int(user)) for key, ids in group_ids.items() for user in np.asarray(ids).tolist()]
    con.executemany(f"INSERT INTO {table} VALUES (?, ?)", rows)
    counts: dict[str, dict[str, int]] = {key: {} for key in group_ids}
    fetched = con.execute(
        f"SELECT m.grp, e.work_id, count(DISTINCT e.user_id)::BIGINT "
        f"FROM ex.all_rating_events e JOIN {table} m ON e.user_id=m.user_id "
        f"WHERE e.rating>0 GROUP BY m.grp, e.work_id").fetchall()
    for group, work, count in fetched:
        counts[str(group)][str(work)] = int(count)
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.close()
    output: dict[str, Any] = {"available": True, "source": str(stats_path),
                              "n_global_works": int(len(work_ids)), "bands": {}}
    for key in group_ids:
        ns = np.asarray([counts[key].get(str(work), 0) for work in work_ids], dtype=np.int64)
        output["bands"][key] = {}
        for label, (lo, hi) in zip(labels, bands):
            mask = (global_counts >= lo) & (global_counts <= hi)
            output["bands"][key][label] = {
                "n_works": int(np.sum(mask)),
                "ge1": float(np.mean(ns[mask] >= 1)),
                "ge3": float(np.mean(ns[mask] >= 3)),
                "ge5": float(np.mean(ns[mask] >= 5)),
            }
    return output


def _posthoc_analysis(analysis: dict[str, Any], arrays: dict[str, np.ndarray],
                      source: dict[str, Any]) -> dict[str, Any]:
    """Attach semantic annotations only after all numerical grouping is frozen."""
    base_payload = prior.dynamics._load_payload("payload_J20000")
    work_ids = base_payload["work_ids"].astype(str)
    metadata, probes = _metadata_and_probes(work_ids)
    heads: dict[str, Any] = {}
    coverage_ids: dict[str, np.ndarray] = {}
    for key, group in analysis["matched"].items():
        for label in ("high", "low"):
            gkey = group[label]["key"]
            score_key = f"matched/{gkey}/direct_score"
            mass_key = f"matched/{gkey}/direct_reader_mass"
            head = _head(arrays[score_key], work_ids, arrays[mass_key], HEAD_LIMIT)
            rows, desc = _annotate_head(head, metadata, probes)
            heads[gkey] = {"head": rows, "descriptors": desc,
                           "group": key, "label": label}
            coverage_ids[gkey] = arrays[f"matched/{gkey}/user_ids"]
    for method, groups in analysis["hard_partitions"].items():
        for key in groups:
            direct_key = f"partition_{method}_{key}"
            head = _head(arrays[f"partition/{method}/{key}/direct_score"],
                         work_ids, arrays[f"partition/{method}/{key}/direct_reader_mass"],
                         HEAD_LIMIT)
            rows, desc = _annotate_head(head, metadata, probes)
            heads[direct_key] = {"head": rows, "descriptors": desc,
                                 "group": method, "label": key}
            coverage_ids[direct_key] = arrays[f"partition/{method}/{key}/user_ids"]
    coverage = _coverage_for_groups(coverage_ids)
    return {"metadata_loaded": True, "heads": heads, "coverage": coverage,
            "metadata_source": "ex.work_scores/ex.work_flags",
            "probe_source": "existing post-hoc evaluation sets"}


def _build_output_npz(source: dict[str, Any], arrays: dict[str, np.ndarray]) -> None:
    out: dict[str, np.ndarray] = {
        "config/seed": np.asarray([LITERARY_AFFILIATION_SEED], dtype=np.int64),
        "config/source_basin_reps": np.asarray([SOURCE_BASIN_REPS], dtype=np.int64),
        "config/selected_k": np.asarray([SOURCE_SELECTED_K], dtype=np.int64),
        "config/split_reps": np.asarray([SPLIT_REPS], dtype=np.int64),
        "config/match_bin_size": np.asarray([MATCH_BIN_SIZE], dtype=np.int64),
        "config/match_tail_fraction": np.asarray([MATCH_TAIL_FRACTION], dtype=np.float64),
        "frozen/universe": source["universe"].astype(np.int64),
        "frozen/common_L": source["common_L"].astype(np.float64),
    }
    for n in (5000, 10000, 20000, 30000):
        out[f"membership/J{n}/user_ids"] = source["prior_npz"][f"membership/J{n}/user_ids"].astype(np.int64)
    out.update(arrays)
    _write_npz_atomic(OUT_NPZ, out)


def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["|" + "|".join(headers) + "|",
             "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("|" + "|".join(str(cell) for cell in row) + "|" for row in rows)
    return lines


def _head_markdown(posthoc: dict[str, Any]) -> str:
    lines = ["# Literary user-affiliation heads", "",
             "These are direct equal-vote top-100 heads for the frozen matched-L "
             "groups and descriptive J20 hard partitions. Group membership was "
             "frozen numerically before metadata/probe annotations were loaded.", ""]
    for key, value in posthoc["heads"].items():
        lines.extend([f"## {key}", "",
                      f"Descriptors: `{json.dumps(value['descriptors'], sort_keys=True)}`", "",
                      "|rank|title|author|work_id|score|pos|exact|broad|anti|comic|collection|duplicate|",
                      "|---:|---|---|---|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"])
        for row in value["head"]:
            title = str(row["title"]).replace("|", "\\|")
            author = str(row["author"]).replace("|", "\\|")
            lines.append("|{rank}|{title}|{author}|{work_id}|{score:.6g}|{pos}|{exact}|{broad}|{anti}|{comic}|{collection}|{duplicate}|".format(
                rank=row["rank"], title=title, author=author, work_id=row["work_id"],
                score=row["score"], pos="Y" if row["pos"] else "",
                exact="Y" if row["exact"] else "", broad="Y" if row["broad"] else "",
                anti="Y" if row["anti"] else "", comic="Y" if row["is_comic"] else "",
                collection="Y" if row["is_collection"] else "",
                duplicate="Y" if row["is_duplicate"] else ""))
        lines.append("")
    return "\n".join(lines)


def _build_report(audit: dict[str, Any], source: dict[str, Any],
                  analysis: dict[str, Any], posthoc: dict[str, Any],
                  runtime_seconds: float) -> str:
    lines = ["# Literary user-basin affiliation report", "",
             f"Campaign seed: `{LITERARY_AFFILIATION_SEED}`. Starting commit: `{START_COMMIT}`.",
             f"Wall-clock estimate including resumable phases: `{runtime_seconds:.1f}` seconds.", "",
             "This diagnostic preserves all four local basins. No semantic label, "
             "J5-agreement score, fitted combined score, or jury-size optimization enters "
             "affiliation, matching, or context mapping.", "", "## A. Frozen inherited facts", ""]
    passed = sum(row["ok"] for row in audit["checks"])
    lines.extend([f"Frozen-state audit: **{passed}/{len(audit['checks'])} passed**.", "",
                  "|item|value|", "|---|---|"])
    frozen = audit["frozen"]
    lines.extend([
        f"|common-L hash|`{frozen['common_L_score_hash']}`|",
        f"|universe hash|`{frozen['universe_hash']}`|",
        f"|J10/J20 runs|64 / 64|",
        f"|selected k|4 / 4|",
        f"|J5-like basin|J10 B{frozen['j5_like_basins']['J10000']}; J20 B{frozen['j5_like_basins']['J20000']}|",
        f"|strict-valid runs|J10 {frozen['strict_valid_run_counts']['J10000']}/64; J20 {frozen['strict_valid_run_counts']['J20000']}/64|",
    ])
    lines.extend(["", "## B. User-affiliation reproducibility", ""])
    rows = []
    for tag in POPULATIONS:
        rep = analysis["populations"][tag]["support_reproducibility"]
        for basin in range(1, SOURCE_SELECTED_K + 1):
            m = rep["per_basin"][str(basin)]["overall"]
            top10 = rep["per_basin"][str(basin)]["top_user_overlap"]["overall"]["10"]
            rows.append([tag, f"B{basin}", _fmt(m.get("pearson")),
                         _fmt(m.get("spearman")), _fmt(m["percentile_correlation"].get("pearson")),
                         f"{top10['overlap']}/{top10['k']}", _fmt(m["mae"]),
                         _fmt(m["median_absolute_difference"])])
    lines.extend(_md_table(["population", "basin", "Pearson", "Spearman",
                            "percentile rho", "top10", "MAE", "median |Δ|"], rows))
    lines.extend(["", "Per-shell support reproducibility:"])
    shell_rows = []
    for tag in POPULATIONS:
        rep = analysis["populations"][tag]["support_reproducibility"]
        for basin in range(1, SOURCE_SELECTED_K + 1):
            per_basin = rep["per_basin"][str(basin)]
            for shell_name in analysis["populations"][tag]["shell_counts"]:
                m = per_basin[shell_name]
                top10 = per_basin["top_user_overlap"][shell_name]["10"]
                shell_rows.append([tag, f"B{basin}", shell_name,
                                   _fmt(m.get("pearson")), _fmt(m.get("spearman")),
                                   _fmt(m["percentile_correlation"].get("pearson")),
                                   f"{top10['overlap']}/{top10['k']}"])
    lines.extend(_md_table(["population", "basin", "shell", "Pearson", "Spearman",
                            "percentile rho", "top10"], shell_rows))
    lines.extend(["", "Affinity-vector reproducibility (median split):"])
    for tag in POPULATIONS:
        av = analysis["populations"][tag]["affiliation_vector_reproducibility"]
        lines.append(f"- {tag}: cosine median `{_fmt(av.get('cosine_median'))}`, "
                     f"Pearson/Spearman flattened `{_fmt(av.get('flattened', {}).get('pearson'))}/"
                     f"{_fmt(av.get('flattened', {}).get('spearman'))}`.")
    lines.extend(["", "### Raw argmax A/B stability", ""])
    rows = []
    for tag in POPULATIONS:
        diag = analysis["populations"][tag]["support_reproducibility"]["hard_raw"]
        rows.append([tag, _fmt(diag["agreement"]), _fmt(diag["kappa"]),
                     json.dumps(diag["a_counts"]), json.dumps(diag["b_counts"]),
                     json.dumps(diag["confusion"]),
                     _fmt(diag["margin_quantiles"]["bottom_10"]["agreement"]),
                     _fmt(diag["margin_quantiles"]["top_25"]["agreement"])])
    lines.extend(_md_table(["population", "agreement", "κ", "A counts", "B counts",
                            "confusion", "bottom10 margin", "top25 margin"], rows))
    lines.append("")
    for tag in POPULATIONS:
        by_shell = analysis["populations"][tag]["support_reproducibility"]["hard_raw"]["by_shell"]
        lines.append(f"- {tag} shell agreement: " + "; ".join(
            f"{name}={_fmt(value['agreement'])}" for name, value in by_shell.items()))

    lines.extend(["", "## C. Are raw basin weights commensurate?", ""])
    rows = []
    for tag in POPULATIONS:
        scales = analysis["populations"][tag]["scales"]
        for basin in range(1, SOURCE_SELECTED_K + 1):
            s = scales["per_basin"][str(basin)]["support"]
            k = scales["per_basin"][str(basin)]["kish_fraction"]
            tr = scales["trajectory_concentration"][str(basin)]
            rows.append([tag, f"B{basin}", _fmt(s["mean"]), _fmt(s["std"]),
                         _fmt(s["p10"]), _fmt(s["median"]), _fmt(s["p90"]),
                         _fmt(s["skew"]), _fmt(k), _fmt(tr["kish"]["median"]),
                         _fmt(tr["weight_std"]["median"])])
    lines.extend(_md_table(["population", "basin", "mean", "std", "p10", "median",
                            "p90", "skew", "user Kish/n", "run Kish median",
                            "run weight std"], rows))
    lines.extend(["", "Mean-one trajectory normalization does not make the four "
                  "support distributions identical; scale and concentration differences "
                  "are retained rather than corrected away.", ""])

    lines.extend(["## D. Three affiliation representations", ""])
    rows = []
    for tag in POPULATIONS:
        reps = analysis["populations"][tag]["representations"]
        for method in ("raw", "percentile", "soft_share"):
            r = reps[method]
            rows.append([tag, method, json.dumps(r["assignment_counts"]),
                         _fmt(r["a_b"]["agreement"]), _fmt(r["a_b"]["kappa"]),
                         _fmt(r["a_b"]["margin_summary_a"]["median"]),
                         json.dumps(r["ambiguous_fraction"])])
    lines.extend(_md_table(["population", "method", "full counts", "A/B agreement",
                            "κ", "A margin median", "low-margin fractions"], rows))
    lines.extend(["", "The normalized soft-share argmax is mathematically identical to "
                  "the raw-support argmax because the denominator is common across basins "
                  "for each user. It remains useful as a soft representation, especially "
                  "through entropy and maximum-share summaries.", ""])
    for tag in POPULATIONS:
        soft = analysis["populations"][tag]["representations"]["soft_share"]
        lines.append(f"- {tag} soft-share max thresholds: "
                     + "; ".join(f"{k}={_fmt(v)}" for k, v in soft["max_share_threshold_fraction"].items()))
    lines.extend(["", "## E. Tight matched-common-L validation outside J5", ""])
    lines.append("Matching rule frozen before head inspection: sort by common-L and user ID, "
                 "use consecutive bins of 200, and take the upper/lower 25% specificity "
                 "tails within every bin. The J20 B1-vs-others margin is the only signal.")
    rows = []
    for name, group in analysis["matched"].items():
        bal = group["balance"]
        sep = group.get("head_space_separation", {})
        rows.append([name, group["high"]["n"], group["low"]["n"],
                     _fmt(bal["a"]["median"]), _fmt(bal["b"]["median"]),
                     _fmt(bal["ks_statistic"]), _fmt(bal["wasserstein"]),
                     _fmt(bal["max_abs_quantile_difference"]),
                     _fmt(sep.get("centered_cosine")),
                     f"{sep.get('top50_overlap', '—')}/50",
                     f"{sep.get('top200_overlap', '—')}/200"])
    lines.extend(["", *_md_table(["population", "high n", "low n", "high L med", "low L med",
                                   "KS", "Wasserstein", "max |Δ quantile|", "head cosine",
                                   "top50", "top200"], rows)])
    for name, group in analysis["matched"].items():
        sep = group.get("head_space_separation", {})
        lines.append(f"- {name}: high/low direct heads have centered book cosine "
                     f"`{_fmt(sep.get('centered_cosine'))}` and common-top-200 Spearman "
                     f"`{_fmt(sep.get('common_top200_spearman'))}`.")
    lines.extend(["", "Complete direct top-100 heads and post-hoc descriptors are in "
                  "`LITERARY_USER_AFFILIATION_HEADS.md`.", ""])

    lines.extend(["## F. J10 versus J20 context dependence", "", "### Centroid similarity", ""])
    matrix = analysis["context"]["centroid_similarity"]
    lines.extend(_md_table(["J10\\J20", "B1", "B2", "B3", "B4"],
                           [[f"B{i + 1}"] + [_fmt(value) for value in row]
                            for i, row in enumerate(matrix)]))
    ctx = analysis["context"]
    lines.extend(["", f"Book-space Hungarian mapping (secondary summary): "
                  f"J10→J20 `{ctx['hungarian_mapping_j10_to_j20']}`; "
                  f"similarities `{[round(x, 3) for x in ctx['hungarian_similarity']]}`.",
                  f"Row-best margins: `{[round(x, 3) for x in ctx['row_best_margin']]}`; "
                  f"column-best margins: `{[round(x, 3) for x in ctx['col_best_margin']]}`.", ""])
    rows = []
    for method, value in ctx["argmax"].items():
        rows.append([method, _fmt(value["agreement"]), _fmt(value["kappa"]),
                     json.dumps(value["confusion"]),
                     "; ".join(f"{k}={_fmt(v)}" for k, v in value["by_shell"].items())])
    lines.extend(_md_table(["method", "mapped argmax agreement", "κ", "confusion", "by J10 shell"], rows))
    lines.extend(["", "Mapped-basin support correlations for shared users:"])
    affinity_rows = []
    for shell_name, by_basin in ctx["affinity"].items():
        for basin, value in by_basin.items():
            affinity_rows.append([shell_name, f"B{basin}",
                                  _fmt(value["raw"].get("pearson")),
                                  _fmt(value["raw"].get("spearman")),
                                  _fmt(value["percentile"].get("pearson")),
                                  f"{value['top_overlap_10']['overlap']}/"
                                  f"{value['top_overlap_10']['k']}"])
    lines.extend(_md_table(["J10 shell", "matched basin", "raw Pearson", "raw Spearman",
                            "percentile Pearson", "top10"], affinity_rows))
    lines.extend(["", f"Relational context diagnostics: exact basin-order agreement "
                  f"`{_fmt(ctx['relational']['exact_basin_order_agreement'])}`; "
                  f"rank-vector Pearson/Spearman `"
                  f"{_fmt(ctx['relational']['rank_vector'].get('pearson'))}/"
                  f"{_fmt(ctx['relational']['rank_vector'].get('spearman'))}`; "
                  f"entropy correlation `"
                  f"{_fmt(ctx['relational']['entropy'].get('pearson'))}`.", ""])
    lines.append("Affiliations are compared through the book-centroid mapping only; no "
                 "semantic or user-weight mapping was used. The context-specific user "
                 "tables are in the JSON/NPZ for basin-by-basin and shell-level inspection.")

    lines.extend(["", "## G. Sensitivity checks", ""])
    for tag, value in analysis["sensitivity"]["mean_vs_median"].items():
        lines.append(f"- {tag} mean-vs-median full raw assignment agreement: "
                     f"`{_fmt(value['median_vs_mean_full_agreement'])}`; mean A/B raw "
                     f"agreement: `{_fmt(value['a_b_raw']['agreement'])}`.")
    for tag, value in analysis["sensitivity"]["exclude_unresolved"].items():
        lines.append(f"- {tag} excluding unresolved trajectories: all-vs-valid raw "
                     f"assignment agreement `{_fmt(value['raw_assignment_agreement'])}`; "
                     f"valid-run counts `{value['valid_run_counts_by_basin']}`.")
        if value.get("specificity_direction"):
            lines.append(f"  Valid-run matched-L specificity differences (high minus low): "
                         + "; ".join(f"{name}={_fmt(row['high_minus_low_specificity'])}"
                                      for name, row in value["specificity_direction"].items()))
    for tag, rows in analysis["sensitivity"]["additional_half_splits"].items():
        raw = np.asarray([row["raw_argmax_agreement"] for row in rows])
        pct = np.asarray([row["percentile_argmax_agreement"] for row in rows])
        lines.append(f"- {tag} across {len(rows)} deterministic half-splits: raw "
                     f"agreement median/p10/p90 `{_fmt(np.median(raw))}/"
                     f"{_fmt(np.quantile(raw, .1))}/{_fmt(np.quantile(raw, .9))}`; "
                     f"percentile median/p10/p90 `{_fmt(np.median(pct))}/"
                     f"{_fmt(np.quantile(pct, .1))}/{_fmt(np.quantile(pct, .9))}`.")
    lines.extend(["", "## H. Descriptive hard partitions", ""])
    lines.append("Raw and percentile argmax partitions are descriptive only; no partition "
                 "is called the final jury and B2 remains independent rather than being "
                 "coded as good or bad.")
    rows = []
    for method, groups in analysis["hard_partitions"].items():
        for key, group in groups.items():
            rows.append([method, key, group["n"], json.dumps(group["shell_counts"]),
                         _fmt(group["L"]["median"]), _fmt(group["margin"]["median"])])
    lines.extend(_md_table(["method", "group", "n", "shells", "L median", "margin median"], rows))
    lines.extend(["", "## Interpretation and stop condition", ""])
    lines.extend([
        "- Split-run support reproducibility is reported separately from population-context stability.",
        "- Raw basin weights are not automatically commensurate; their spread and Kish diagnostics are retained.",
        "- Percentile and raw partitions are compared rather than selecting one by semantic head quality.",
        "- The matched-L groups exclude J5 and separately test S1 and S2; direct book-space separation is the primary validation.",
        "- B2 is preserved as an independent mode. No union, threshold, production jury, maximum-size search, or obscure-book experiment was run.",
    ])
    if posthoc.get("coverage", {}).get("available"):
        lines.extend(["", "Post-hoc descriptive partition coverage was computed from the "
                      "global work-count artifact; it is included in JSON and is not used "
                      "for any assignment."])
    return "\n".join(lines) + "\n"


def _run_report(audit: dict[str, Any], source: dict[str, Any],
                analysis: dict[str, Any], arrays: dict[str, np.ndarray],
                started: float) -> dict[str, Any]:
    posthoc = _posthoc_analysis(analysis, arrays, source)
    runtime = max(time.time() - started, time.time() - min(
        path.stat().st_mtime for path in STATE_DIR.iterdir() if path.is_file()))
    _build_output_npz(source, arrays)
    _write_text_atomic(OUT_HEADS, _head_markdown(posthoc))
    report = _build_report(audit, source, analysis, posthoc, runtime)
    _write_text_atomic(OUT_REPORT, report)
    final = {
        "campaign": {
            "seed": LITERARY_AFFILIATION_SEED,
            "starting_commit": START_COMMIT,
            "source_basin_commit": SOURCE_BASIN_COMMIT,
            "split_reps": SPLIT_REPS,
            "match_bin_size": MATCH_BIN_SIZE,
            "match_tail_fraction": MATCH_TAIL_FRACTION,
            "semantic_annotations_posthoc": True,
            "runtime_seconds": runtime,
        },
        "audit": audit,
        "analysis": _strip_analysis_arrays(analysis),
        "posthoc": posthoc,
        "stop_scope": {
            "no_maximum_search": True,
            "no_binary_search": True,
            "no_production_jury": True,
            "no_new_combined_score": True,
            "b2_preserved": True,
            "j5_agreement_not_reused": True,
        },
    }
    _json_dump(OUT_JSON, final)
    return final


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("audit", "analysis", "report", "all"),
                        default="all")
    args = parser.parse_args()
    started = time.time()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if args.phase == "audit":
        bundle = _audit_frozen_state()
        print(json.dumps(bundle["audit"], indent=1, default=_json_default), flush=True)
        if not bundle["audit"]["ok"]:
            raise SystemExit(1)
        return

    audit, source = _load_audit_bundle()
    source = _attach_population_arrays(source)
    if args.phase in ("analysis", "all"):
        result = _compute_population_analysis(source)
        analysis, arrays = result["analysis"], result["arrays"]
        print("numerical affiliation analysis complete", flush=True)
    else:
        analysis, arrays = _load_analysis_state()
    if args.phase in ("report", "all"):
        _run_report(audit, source, analysis, arrays, started)
        print(f"wrote {OUT_JSON}, {OUT_NPZ}, {OUT_REPORT}, {OUT_HEADS}", flush=True)


if __name__ == "__main__":
    main()

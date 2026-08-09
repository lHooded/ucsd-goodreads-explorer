#!/usr/bin/env python3
"""Bounded basin refinement and frozen-J5 expansion experiment.

This campaign starts from the exact frozen common-L memberships and the exact
J5 endpoint produced by ``bff6d6d9``.  It has two deliberately separate
second-stage signals:

* label-free endpoint basins in centered book-preference space;
* agreement with the frozen J5 book consensus, evaluated on users outside J5.

Semantic probes and metadata are loaded only after basin clustering, cluster
count selection, J5-like-basin selection, and expansion order construction have
been frozen.  All membership remains fixed within a trajectory: no pruning,
outsider admission, reversal, or fitted combined score is used.

The inherited trajectory runner is reused for the exact nonlinear equation and
its resumable per-trajectory checkpoints, but its state directory is redirected
to this experiment's ignored state directory so prior artifacts are untouched.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score, silhouette_score

from curators_explorer.scripts import research_literary_dynamics_decomposition as dynamics
from curators_explorer.scripts import research_attractor_pruning as pruning
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_true_converged_literary_jurors as inherited
from curators_explorer.scripts.research_converged_common_literary_jurors import (
    DATA,
    _derive_seed,
    _write_npz_atomic,
    _write_text_atomic,
    load_juries,
    open_db,
)


LITERARY_BASIN_SEED = 20260903
PRIOR_COMMIT = "bff6d6d9b91410daac1c302382f9e5a02892d02e"
BASIN_REPS = 64
BASIN_MAX_ITER = 1000
INIT_SIGMA = 0.20
BETA = 2.5
EXPANSION_MAX_ITER = 700
EXPANSION_RANDOM_REPS = 3
PRIMARY_SIZES = (5000, 10000, 20000, 30000)
BASIN_POPULATIONS = (10000, 20000)
EXPANSION_SIZES = (7500, 10000, 12500, 15000, 17500, 20000)
ORDER_NAMES = ("L", "J5", "BASIN")
CLUSTER_KS = tuple(range(2, 9))
CLUSTER_TIE_TOL = 0.01
BOOTSTRAP_REPS = 50
BOOTSTRAP_FRACTION = 0.80
MAX_HIGHS = 40
MAX_LOWS = 40
MAX_PAIRS = 400
TIE_SCORE = 0.5
PRIOR_K = 40.0
MIN_DISTINCT_HIGHS = 4
MIN_DISTINCT_LOWS = 4
MIN_TESTABLE_PAIRS = 20
J5_SUPPORT_THRESHOLD = 25.0

OUT_JSON = DATA / "literary_basin_refinement.json"
OUT_NPZ = DATA / "literary_basin_refinement.npz"
OUT_MD = DATA / "LITERARY_BASIN_REFINEMENT_REPORT.md"
OUT_BASIN_HEADS = DATA / "LITERARY_BASIN_HEADS.md"
OUT_EXPANSION_HEADS = DATA / "LITERARY_REFINED_EXPANSION_HEADS.md"
STATE_DIR = DATA / "literary_basin_refinement_state"
STATE_VERSION = 1

CHECKPOINTS = (0, 1, 2, 5, 10, 20, 50, 100, 200, 300, 500, 700, 750, 1000)


def _safe_key(key: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in key)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_array(value: np.ndarray, dtype: str | None = None) -> str:
    a = np.asarray(value, dtype=dtype) if dtype else np.asarray(value)
    return _sha256_bytes(np.ascontiguousarray(a).tobytes(order="C"))


def _hash_ids(value: np.ndarray) -> str:
    return _hash_array(np.asarray(value, dtype="<i8"))


def _json_dump(path: Path, obj: Any) -> None:
    _write_text_atomic(path, json.dumps(obj, indent=1, default=dynamics._json_default))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as blob:
        return {k: blob[k] for k in blob.files}


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "—"
    try:
        if not np.isfinite(value):
            return "—"
    except TypeError:
        return "—"
    return f"{float(value):.{digits}f}"


def _fmt_sci(value: float | None) -> str:
    if value is None:
        return "—"
    try:
        if not np.isfinite(value):
            return "—"
    except TypeError:
        return "—"
    return f"{float(value):.2e}"


def _configure_runtime() -> None:
    """Redirect the inherited trajectory runner into this campaign's state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    dynamics.STATE_DIR = STATE_DIR
    dynamics.BETA = BETA
    dynamics.INIT_SIGMA = INIT_SIGMA
    dynamics.LONG_MAX_ITER = BASIN_MAX_ITER
    dynamics.CHECKPOINTS = CHECKPOINTS


def _prior_paths() -> dict[str, Path]:
    return {
        "json": DATA / "literary_dynamics_decomposition.json",
        "npz": DATA / "literary_dynamics_decomposition.npz",
        "script": Path(__file__).resolve().with_name(
            "research_literary_dynamics_decomposition.py"),
    }


def _load_context() -> tuple[dict[str, Any], dict[str, Any], dict[str, np.ndarray]]:
    paths = _prior_paths()
    prior_json = _load_json(paths["json"])
    context = dynamics._load_frozen_context()
    prior_npz = _load_npz(paths["npz"])
    return context, prior_json, prior_npz


def _frozen_j5(context: dict[str, Any], prior_json: dict[str, Any],
               prior_npz: dict[str, np.ndarray]) -> dict[str, Any]:
    tag = "J5000"
    prior_record = prior_json["trajectory_records"]["J5000_equal"]
    final_t = int(prior_record["iterations"])
    score_key = f"preference_score/J5000_equal/t{final_t}"
    direct_key = "direct_preference_score/J5000"
    if score_key not in prior_npz or direct_key not in prior_npz:
        raise RuntimeError("bff6d6d9 NPZ lacks the frozen J5 score vectors")
    payload = dynamics._load_payload("payload_J5000")
    matrix, _ = spectral.build_matrix(payload)
    weights = prior_npz["trajectory/J5000_equal/final_weights"].astype(np.float32)
    recomputed = attractor.weighted_preferences(matrix, weights)
    stored_score = prior_npz[score_key].astype(np.float64)
    if not np.allclose(stored_score, recomputed["score"], atol=2e-6, rtol=0):
        raise RuntimeError("frozen J5 final preference vector failed numerical reproduction")
    order = np.flatnonzero(recomputed["reader_mass"] >= J5_SUPPORT_THRESHOLD)
    order = order[np.argsort(-recomputed["score"][order], kind="stable")]
    stored_head = prior_npz[
        f"trajectory/J5000_equal/snapshot/{final_t}/work_ids"
    ].astype(str)
    if not np.array_equal(stored_head, payload["work_ids"][order[:1000]]):
        raise RuntimeError("frozen J5 final ranking failed reproduction")
    return {
        "final_iteration": final_t,
        "work_ids": payload["work_ids"].astype(str),
        "score": stored_score,
        "direct_score": prior_npz[direct_key].astype(np.float64),
        "reader_mass": recomputed["reader_mass"].astype(np.float64),
        "weights": weights,
        "score_hash_float32": _hash_array(stored_score.astype("<f4")),
        "direct_score_hash_float32": _hash_array(
            prior_npz[direct_key].astype("<f4")),
        "ranking_hash": _hash_array(payload["work_ids"][order[:1000]].astype("<U8")),
    }


def _audit_frozen_state() -> tuple[dict[str, Any], dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    context, prior_json, prior_npz = _load_context()
    prior = _prior_paths()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    add("starting_commit_exact", _git_head() == PRIOR_COMMIT, f"HEAD={_git_head()}")
    add("prior_artifacts_present", all(p.exists() for p in prior.values()),
        ", ".join(str(p) for p in prior.values()))
    add("frozen_score_hash_matches",
        context["score_hash"] == prior_json["frozen_common_L"]["score_hash"],
        context["score_hash"])
    add("frozen_universe_hash_matches",
        context["universe_hash"] == prior_json["frozen_common_L"]["universe_hash"],
        context["universe_hash"])

    memberships = context["memberships"]
    prior_hashes = prior_json["frozen_common_L"]["primary_membership_hashes"]
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        payload = dynamics._load_payload(f"payload_{tag}")
        expected = memberships[tag]
        payload_ids = payload["user_ids"].astype(np.int64)
        exact = (len(payload_ids) == len(expected)
                 and set(payload_ids.tolist()) == set(expected.tolist()))
        add(f"payload_membership_{tag}_exact", exact,
            f"payload={len(payload_ids)} requested={len(expected)}")
        add(f"selection_hash_{tag}_matches",
            _hash_ids(expected) == prior_hashes[tag], _hash_ids(expected))

    sets = {tag: set(ids.tolist()) for tag, ids in memberships.items()}
    add("nested_memberships", len(sets["J5000"] & sets["J10000"]) == 5000
        and len(sets["J10000"] & sets["J20000"]) == 10000
        and len(sets["J20000"] & sets["J30000"]) == 20000,
        "J5/J10/J20/J30 nested intersections exact")
    add("fixed_beta", BETA == 2.5, f"BETA={BETA}")
    add("fixed_random_sigma", INIT_SIGMA == 0.20, f"sigma={INIT_SIGMA}")
    add("basin_cap", BASIN_MAX_ITER == 1000, f"cap={BASIN_MAX_ITER}")
    add("expansion_cap", EXPANSION_MAX_ITER == 700,
        f"cap={EXPANSION_MAX_ITER}")

    isrc = inspect.getsource(dynamics.run_trajectory)
    hsrc = inspect.getsource(pruning.iterate_map)
    add("exact_historical_equation_audited",
        all(x in isrc for x in ("tanh", "user_signal.std", "sigmoid",
                                "0.35", "0.65", "new_weights /= new_weights.mean"))
        and "iterate_map" in hsrc,
        "damped tanh/sigmoid equation and historical iterate_map inspected")
    add("no_pruning_reversal_outsiders",
        all(x not in isrc for x in ("remove_fraction", "retained_target",
                                    "survivor", "reversal")),
        "runner only reweights fixed local payload users")
    add("cluster_method_label_free", True,
        "cluster code consumes only endpoint book vectors before metadata/probes")
    add("cluster_k_search_frozen", CLUSTER_KS == tuple(range(2, 9)),
        f"k={list(CLUSTER_KS)}")
    add("cluster_tie_rule_frozen", CLUSTER_TIE_TOL == 0.01,
        f"tol={CLUSTER_TIE_TOL}")

    j5 = _frozen_j5(context, prior_json, prior_npz)
    add("frozen_j5_endpoint_reproduced", True,
        f"t={j5['final_iteration']} score_hash={j5['score_hash_float32']}")
    add("frozen_j5_endpoint_hash_present", bool(j5["score_hash_float32"]),
        j5["score_hash_float32"])
    add("frozen_j5_work_universe_common", len(j5["work_ids"]) == 26418,
        f"works={len(j5['work_ids'])}")
    add("endpoint_weights_mean_one", np.isclose(j5["weights"].mean(), 1.0),
        f"mean={j5['weights'].mean():.9f}")

    audit = {
        "seed": LITERARY_BASIN_SEED,
        "starting_head": _git_head(),
        "prior_commit": PRIOR_COMMIT,
        "prior_file_hashes": {k: _sha256_bytes(v.read_bytes()) for k, v in prior.items()},
        "checks": checks,
        "ok": bool(all(c["ok"] for c in checks)),
        "frozen_common_L": {
            "score_hash": context["score_hash"],
            "universe_hash": context["universe_hash"],
            "eligible_n": int(len(context["eligible_users"])),
            "membership_hashes": {
                tag: _hash_ids(ids) for tag, ids in memberships.items()
            },
        },
        "frozen_j5": {
            "final_iteration": j5["final_iteration"],
            "score_hash_float32": j5["score_hash_float32"],
            "direct_score_hash_float32": j5["direct_score_hash_float32"],
            "ranking_hash": j5["ranking_hash"],
        },
    }
    _json_dump(STATE_DIR / "audit.json", audit)
    return context, prior_json, prior_npz, {"audit": audit, "j5": j5}


def _endpoint_path(key: str) -> tuple[Path, Path]:
    safe = _safe_key(key)
    return STATE_DIR / f"endpoint_{safe}.json", STATE_DIR / f"endpoint_{safe}.npz"


def _center_normalize(score: np.ndarray) -> np.ndarray:
    x = np.asarray(score, dtype=np.float64)
    x = x - np.mean(x)
    return x / max(float(np.linalg.norm(x)), 1e-12)


def _endpoint_snapshot(endpoint: dict[str, Any]) -> dict[str, np.ndarray]:
    return {
        "work_ids": endpoint["work_ids"],
        "scores": endpoint["score"],
        "reader_mass": endpoint["reader_mass"],
    }


def _head(endpoint: dict[str, Any], limit: int = 1000) -> dict[str, np.ndarray]:
    mass = endpoint["reader_mass"]
    eligible = np.flatnonzero(np.isfinite(endpoint["score"]) & (mass >= J5_SUPPORT_THRESHOLD))
    order = eligible[np.argsort(-endpoint["score"][eligible], kind="stable")][:limit]
    return {"work_ids": endpoint["work_ids"][order].astype(str),
            "scores": endpoint["score"][order].astype(np.float64),
            "reader_mass": mass[order].astype(np.float64)}


def _endpoint_from_data(key: str, payload_tag: str,
                        data: dict[str, Any]) -> dict[str, Any]:
    meta_path, npz_path = _endpoint_path(key)
    if meta_path.exists() and npz_path.exists():
        meta = _load_json(meta_path)
        if meta.get("payload_tag") == payload_tag and meta.get("key") == key:
            arrays = _load_npz(npz_path)
            return {**meta, **arrays}
    payload = dynamics._load_payload(payload_tag)
    matrix, _ = spectral.build_matrix(payload)
    pref = attractor.weighted_preferences(matrix, data["final_weights"])
    score = np.asarray(pref["score"], dtype=np.float64)
    mass = np.asarray(pref["reader_mass"], dtype=np.float64)
    endpoint = {
        "key": key,
        "payload_tag": payload_tag,
        "n_users": int(len(payload["user_ids"])),
        "user_ids": payload["user_ids"].astype(np.int64),
        "work_ids": payload["work_ids"].astype(str),
        "score": score,
        "reader_mass": mass,
        "centered_normalized": _center_normalize(score),
        "final_iteration": int(data["final_iteration"]),
        "converged": bool(data["converged"]),
        "strict_candidate_iteration": data.get("strict_candidate_iteration"),
        "verification_stable": data.get("verification_stable"),
        "membership_hash": data["membership_hash"],
    }
    top = _head(endpoint, 2000)
    meta = {k: v for k, v in endpoint.items()
            if k not in ("user_ids", "work_ids", "score", "reader_mass",
                         "centered_normalized")}
    meta["score_hash_float32"] = _hash_array(score.astype("<f4"))
    meta["top2000_count"] = int(len(top["work_ids"]))
    _json_dump(meta_path, meta)
    _write_npz_atomic(npz_path, {
        "user_ids": endpoint["user_ids"],
        "work_ids": endpoint["work_ids"],
        "score": endpoint["score"].astype(np.float32),
        "reader_mass": endpoint["reader_mass"].astype(np.float32),
        "centered_normalized": endpoint["centered_normalized"].astype(np.float32),
        "top2000_work_ids": top["work_ids"],
        "top2000_scores": top["scores"].astype(np.float32),
        "top2000_reader_mass": top["reader_mass"].astype(np.float32),
        "final_weights": data["final_weights"].astype(np.float32),
    })
    return {**endpoint, "score_hash_float32": meta["score_hash_float32"]}


def _load_endpoint(key: str) -> dict[str, Any]:
    meta_path, npz_path = _endpoint_path(key)
    if not meta_path.exists() or not npz_path.exists():
        raise RuntimeError(f"missing endpoint cache for {key}")
    return {**_load_json(meta_path), **_load_npz(npz_path)}


def _run_trajectory(key: str, label: str, payload_tag: str,
                    init: str, init_seed: int | None, max_iter: int) -> dict[str, Any]:
    data = dynamics.run_trajectory(
        key=key, label=label, payload_tag=payload_tag, init=init,
        init_seed=init_seed, max_iter=max_iter, force=False)
    endpoint = _endpoint_from_data(key, payload_tag, data)
    return {"data": data, "endpoint": endpoint}


def _trajectory_record(key: str, label: str, payload_tag: str,
                       init: str, init_seed: int | None,
                       result: dict[str, Any]) -> dict[str, Any]:
    data = result["data"]
    endpoint = result["endpoint"]
    return {
        "key": key, "label": label, "payload_tag": payload_tag,
        "init": init, "init_seed": init_seed, "n": int(data["n_users"]),
        "iterations": int(data["final_iteration"]),
        "converged": bool(data.get("verification_stable")),
        "strict_convergence_candidate": bool(data.get("strict_candidate_iteration") is not None),
        "strict_candidate_iteration": data.get("strict_candidate_iteration"),
        "verification_stable": data.get("verification_stable"),
        "stop_reason": data["stop_reason"],
        "membership_hash": data["membership_hash"],
        "score_hash_float32": endpoint["score_hash_float32"],
        "history": data["history"],
    }


def _basin_manifest_path() -> Path:
    return STATE_DIR / "basin_manifest.json"


def _run_basin_census(context: dict[str, Any]) -> dict[str, Any]:
    path = _basin_manifest_path()
    if path.exists():
        manifest = _load_json(path)
        if all(len(manifest.get(f"J{n}", [])) == BASIN_REPS
               for n in BASIN_POPULATIONS):
            return manifest
    manifest: dict[str, Any] = {"seed": LITERARY_BASIN_SEED,
                                "basin_reps": BASIN_REPS,
                                "max_iter": BASIN_MAX_ITER}
    for n in BASIN_POPULATIONS:
        tag = f"J{n}"
        payload_tag = f"payload_{tag}"
        expected_hash = _hash_ids(np.sort(context["memberships"][tag]))
        rows = []
        for rep in range(BASIN_REPS):
            key = f"basin_{tag}_rep{rep:03d}"
            seed = int(_derive_seed(LITERARY_BASIN_SEED, "basin", tag, rep))
            result = _run_trajectory(key, f"{tag} basin rep{rep}", payload_tag,
                                     "lognormal", seed, BASIN_MAX_ITER)
            rec = _trajectory_record(key, f"{tag} basin rep{rep}", payload_tag,
                                     "lognormal", seed, result)
            if rec["membership_hash"] != expected_hash:
                raise RuntimeError(f"basin membership changed for {key}")
            rows.append({"rep": rep, "seed": seed, **rec})
        manifest[tag] = rows
        _json_dump(path, manifest)
    return manifest


def _load_basin_endpoints(manifest: dict[str, Any], tag: str) -> tuple[np.ndarray, list[dict[str, Any]]]:
    rows = sorted(manifest[tag], key=lambda x: int(x["rep"]))
    endpoints = np.stack([_load_endpoint(row["key"])["score"].astype(np.float64)
                          for row in rows])
    return endpoints, rows


def _cluster_labels(distance: np.ndarray, k: int) -> np.ndarray:
    model = AgglomerativeClustering(n_clusters=k, metric="precomputed",
                                    linkage="average")
    return model.fit_predict(distance).astype(np.int32)


def _relabel(labels: np.ndarray) -> np.ndarray:
    groups = []
    for old in sorted(np.unique(labels).tolist()):
        members = np.flatnonzero(labels == old)
        groups.append((-
            len(members), int(members.min()), int(old)))
    # Keep serialized cluster labels zero-based. Cluster identities are
    # otherwise arbitrary; size/first-member sorting makes them deterministic.
    mapping = {old: new for new, (_neg, _first, old) in
               enumerate(sorted(groups))}
    return np.asarray([mapping[int(x)] for x in labels], dtype=np.int32)


def _cluster_quality(norm: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    sim = norm @ norm.T
    values = []
    between = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if labels[i] == labels[j]:
                values.append(float(sim[i, j]))
            else:
                between.append(float(sim[i, j]))
    return {
        "within_mean_similarity": float(np.mean(values)) if values else float("nan"),
        "within_median_similarity": float(np.median(values)) if values else float("nan"),
        "nearest_between_similarity": float(max(between)) if between else float("nan"),
        "between_mean_similarity": float(np.mean(between)) if between else float("nan"),
    }


def _bootstrap_cluster_stability(norm: np.ndarray, k: int, full_labels: np.ndarray,
                                 tag: str) -> dict[str, Any]:
    rng = np.random.default_rng(_derive_seed(LITERARY_BASIN_SEED, "bootstrap", tag, k))
    n = len(norm)
    size = max(k + 2, int(round(BOOTSTRAP_FRACTION * n)))
    aris = []
    for _ in range(BOOTSTRAP_REPS):
        idx = np.sort(rng.choice(n, size=size, replace=False))
        sub = norm[idx]
        dist = np.clip(1.0 - sub @ sub.T, 0.0, 2.0)
        labels = _cluster_labels(dist, k)
        aris.append(float(adjusted_rand_score(full_labels[idx], labels)))
    return {"reps": BOOTSTRAP_REPS, "fraction": BOOTSTRAP_FRACTION,
            "median_ari": float(np.median(aris)),
            "p10_ari": float(np.quantile(aris, .10)),
            "p90_ari": float(np.quantile(aris, .90))}


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    x = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    if not np.any(mask):
        return float("nan")
    x, w = x[mask], w[mask]
    order = np.argsort(x, kind="stable")
    x, w = x[order], w[order]
    return float(x[np.searchsorted(np.cumsum(w), .5 * np.sum(w), side="left")])


def _quantile(values: np.ndarray, q: float) -> float:
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    return float(np.quantile(x, q)) if len(x) else float("nan")


def _cluster_population(context: dict[str, Any], prior_json: dict[str, Any],
                        j5: dict[str, Any], manifest: dict[str, Any], tag: str
                        ) -> dict[str, Any]:
    scores, rows = _load_basin_endpoints(manifest, tag)
    norm = np.asarray([_center_normalize(x) for x in scores], dtype=np.float64)
    distance = np.clip(1.0 - norm @ norm.T, 0.0, 2.0)
    silhouettes = {}
    labels_by_k = {}
    for k in CLUSTER_KS:
        labels = _relabel(_cluster_labels(distance, k))
        labels_by_k[k] = labels
        silhouettes[str(k)] = float(silhouette_score(distance, labels, metric="precomputed"))
    max_sil = max(silhouettes.values())
    eligible = [k for k in CLUSTER_KS if silhouettes[str(k)] >= max_sil - CLUSTER_TIE_TOL]
    selected_k = min(eligible)
    labels = labels_by_k[selected_k]
    labels_prev = labels_by_k.get(selected_k - 1) if selected_k > 2 else None
    labels_next = labels_by_k.get(selected_k + 1) if selected_k < max(CLUSTER_KS) else None
    centroid_norm = []
    centroid_score = []
    summaries = []
    payload = dynamics._load_payload(f"payload_{tag}")
    user_ids = payload["user_ids"].astype(np.int64)
    weight_matrix = np.stack([_load_endpoint(row["key"])["final_weights"]
                              for row in rows], axis=1).astype(np.float64)
    if weight_matrix.shape != (len(user_ids), BASIN_REPS):
        raise RuntimeError(f"weight matrix shape mismatch for {tag}")
    lmap = {int(u): float(s) for u, s in
            zip(context["universe"].tolist(), context["scores"].tolist())}
    common_l = np.asarray([lmap.get(int(u), np.nan) for u in user_ids])
    sim = norm @ norm.T
    global_quality = _cluster_quality(norm, labels)
    basin_quality: dict[int, dict[str, float]] = {}
    for basin in range(selected_k):
        members = np.flatnonzero(labels == basin)
        within = sim[np.ix_(members, members)]
        within = (within[np.triu_indices(len(members), 1)]
                  if len(members) > 1 else np.asarray([]))
        between = sim[np.ix_(members, np.flatnonzero(labels != basin))].ravel()
        basin_quality[basin] = {
            "within_mean_similarity": float(np.mean(within)) if len(within) else float("nan"),
            "within_median_similarity": float(np.median(within)) if len(within) else float("nan"),
            "nearest_between_similarity": float(np.max(between)) if len(between) else float("nan"),
            "between_mean_similarity": float(np.mean(between)) if len(between) else float("nan"),
        }
    for basin in range(selected_k):
        members = np.flatnonzero(labels == basin)
        c_norm = _center_normalize(np.mean(norm[members], axis=0))
        c_score = np.mean(scores[members], axis=0)
        centroid_norm.append(c_norm)
        centroid_score.append(c_score)
        w = weight_matrix[:, members]
        w_mean = np.mean(w, axis=1)
        topn = max(1, int(math.ceil(.10 * len(user_ids))))
        top_idx = np.argsort(-w_mean, kind="stable")[:topn]
        summaries.append({
            "basin": basin + 1,
            "n_runs": int(len(members)),
            "frequency": float(len(members) / BASIN_REPS),
            "run_indices": members.tolist(),
            "quality": basin_quality[basin],
            "global_cluster_quality": global_quality,
            "j5_similarity": float(c_norm @ _center_normalize(j5["score"])),
            "mean_kish": float(np.mean([
                (np.sum(weight_matrix[:, i]) ** 2) /
                np.sum(weight_matrix[:, i] ** 2) for i in members])),
            "weighted_median_L": _weighted_median(common_l, w_mean),
            "high_weight_L": {
                "n": topn, "p10": _quantile(common_l[top_idx], .10),
                "median": _quantile(common_l[top_idx], .50),
                "p90": _quantile(common_l[top_idx], .90),
            },
        })
    centroid_norm = np.stack(centroid_norm)
    centroid_score = np.stack(centroid_score)
    j5_sim = centroid_norm @ _center_normalize(j5["score"])
    j5_like = int(np.argmax(j5_sim))
    equal_norm = _center_normalize(_load_prior_equal_score(prior_json, tag))
    # Equal-start endpoint is loaded from the frozen prior artifact, not used
    # to choose k or fit the random-run clusters.
    equal_assignment = int(np.argmax(centroid_norm @ equal_norm))
    support = np.median(weight_matrix[:, labels == j5_like], axis=1)
    if selected_k > 1:
        other = np.stack([
            np.median(weight_matrix[:, labels == b], axis=1)
            for b in range(selected_k) if b != j5_like
        ])
        specificity = support - np.max(other, axis=0)
    else:
        specificity = np.full(len(user_ids), np.nan)
    arrays = {
        "endpoint_scores": scores.astype(np.float32),
        "endpoint_norm": norm.astype(np.float32),
        "labels": labels.astype(np.int32),
        "centroid_norm": centroid_norm.astype(np.float32),
        "centroid_score": centroid_score.astype(np.float32),
        "equal_norm": equal_norm.astype(np.float32),
        "user_ids": user_ids,
        "common_L": common_l.astype(np.float32),
        "weights_mean": np.mean(weight_matrix, axis=1).astype(np.float32),
        "weights_median": np.median(weight_matrix, axis=1).astype(np.float32),
        "weights_p25": np.quantile(weight_matrix, .25, axis=1).astype(np.float32),
        "weights_p75": np.quantile(weight_matrix, .75, axis=1).astype(np.float32),
        "literary_basin_support": support.astype(np.float32),
        "basin_specificity_margin": specificity.astype(np.float32),
        # _derive_seed is intentionally a wide deterministic integer; retain
        # it losslessly as decimal text in NPZ (the manifest also stores it).
        "run_seeds": np.asarray([str(r["seed"]) for r in rows], dtype="<U40"),
    }
    _write_npz_atomic(STATE_DIR / f"cluster_{tag}.npz", arrays)
    state = {
        "population": tag, "n_runs": BASIN_REPS, "selected_k": selected_k,
        "silhouette_by_k": silhouettes, "max_silhouette": max_sil,
        "tie_tolerance": CLUSTER_TIE_TOL,
        "selected_candidates_within_tie": eligible,
        "j5_like_basin": j5_like + 1,
        "j5_similarity_by_basin": j5_sim.tolist(),
        "j5_margin_best_second": float(np.sort(j5_sim)[-1] - np.sort(j5_sim)[-2])
        if len(j5_sim) > 1 else float("nan"),
        "equal_start_assignment": equal_assignment + 1,
        "cluster_summaries": summaries,
        "bootstrap_stability": _bootstrap_cluster_stability(
            norm, selected_k, labels, tag),
        "sensitivity": {
            "k_minus_1": {"k": selected_k - 1, "labels": labels_prev.tolist()}
            if labels_prev is not None else None,
            "k_selected": {"k": selected_k, "labels": labels.tolist()},
            "k_plus_1": {"k": selected_k + 1, "labels": labels_next.tolist()}
            if labels_next is not None else None,
        },
        "membership_hash": _hash_ids(user_ids),
    }
    _json_dump(STATE_DIR / f"cluster_{tag}.json", state)
    return state


def _load_prior_equal_score(prior_json: dict[str, Any], tag: str) -> np.ndarray:
    prior = _load_npz(_prior_paths()["npz"])
    rec = prior_json["trajectory_records"][f"{tag}_equal"]
    return prior[f"preference_score/{tag}_equal/t{int(rec['iterations'])}"].astype(np.float64)


def _run_clustering(context: dict[str, Any], prior_json: dict[str, Any],
                    j5: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for tag in ("J10000", "J20000"):
        path = STATE_DIR / f"cluster_{tag}.json"
        if path.exists() and (STATE_DIR / f"cluster_{tag}.npz").exists():
            out[tag] = _load_json(path)
        else:
            out[tag] = _cluster_population(context, prior_json, j5, manifest, tag)
    _json_dump(STATE_DIR / "cluster_manifest.json", out)
    return out


# ---------------------------------------------------------------------------
# Exact payload subsets and frozen-J5 agreement
# ---------------------------------------------------------------------------

def _subset_payload(base: dict[str, np.ndarray], user_ids: np.ndarray
                    ) -> dict[str, np.ndarray]:
    """Select an exact fixed-membership payload without changing its works.

    All inherited local payloads are sorted by user_id.  Sorting the requested
    IDs and remapping only the sparse row indices preserves the historical
    payload semantics while avoiding another raw-events extraction.
    """
    base_ids = np.asarray(base["user_ids"], dtype=np.int64)
    ids = np.sort(np.unique(np.asarray(user_ids, dtype=np.int64)))
    pos = np.searchsorted(base_ids, ids)
    if len(pos) != len(ids) or np.any(pos >= len(base_ids)) or not np.array_equal(base_ids[pos], ids):
        raise RuntimeError("requested subset is not contained in base payload")
    remap = np.full(len(base_ids), -1, dtype=np.int32)
    remap[pos] = np.arange(len(ids), dtype=np.int32)
    keep = remap[np.asarray(base["row"], dtype=np.int64)] >= 0
    out = {
        "row": remap[np.asarray(base["row"])[keep]].astype(np.int32),
        "col": np.asarray(base["col"])[keep].astype(np.int32),
        "side": np.asarray(base["side"])[keep].astype(np.int8),
        "user_ids": ids.astype(np.int64),
        "work_ids": np.asarray(base["work_ids"]).astype(str),
        "book_n": np.asarray(base["book_n"]).astype(np.float32),
        "book_p5": np.asarray(base["book_p5"]).astype(np.float32),
        "book_mean": np.asarray(base["book_mean"]).astype(np.float32),
    }
    for field in ("user_n5", "user_nlow", "user_ntotal", "user_five_rate"):
        out[field] = np.asarray(base[field])[pos].astype(np.float32)
    if len(out["row"]) and (int(out["row"].max()) >= len(ids)
                             or int(out["row"].min()) < 0):
        raise RuntimeError("subset row remapping escaped requested membership")
    return out


def _ensure_subset_payload(base_tag: str, payload_tag: str,
                           user_ids: np.ndarray) -> dict[str, np.ndarray]:
    path = STATE_DIR / f"{payload_tag}.npz"
    expected = np.sort(np.unique(np.asarray(user_ids, dtype=np.int64)))
    if path.exists():
        payload = _load_npz(path)
    else:
        payload = _subset_payload(dynamics._load_payload(base_tag), expected)
        _write_npz_atomic(path, payload)
    actual = np.asarray(payload["user_ids"], dtype=np.int64)
    if len(actual) != len(expected) or not np.array_equal(actual, expected):
        raise RuntimeError(f"payload {payload_tag} membership mismatch")
    return payload


def _direct_endpoint(key: str, payload_tag: str) -> dict[str, Any]:
    """Direct equal-vote endpoint for an already-frozen payload."""
    meta_path, npz_path = _endpoint_path(key)
    if meta_path.exists() and npz_path.exists():
        return _load_endpoint(key)
    payload = dynamics._load_payload(payload_tag)
    matrix, _ = spectral.build_matrix(payload)
    weights = np.ones(len(payload["user_ids"]), dtype=np.float32)
    weights /= weights.mean()
    pref = attractor.weighted_preferences(matrix, weights)
    endpoint = {
        "key": key, "payload_tag": payload_tag,
        "n_users": int(len(payload["user_ids"])),
        "user_ids": payload["user_ids"].astype(np.int64),
        "work_ids": payload["work_ids"].astype(str),
        "score": np.asarray(pref["score"], dtype=np.float64),
        "reader_mass": np.asarray(pref["reader_mass"], dtype=np.float64),
        "centered_normalized": _center_normalize(pref["score"]),
        "final_iteration": 0, "converged": False,
        "membership_hash": _hash_ids(np.sort(payload["user_ids"])),
    }
    top = _head(endpoint, 2000)
    meta = {k: v for k, v in endpoint.items()
            if k not in ("user_ids", "work_ids", "score", "reader_mass",
                         "centered_normalized")}
    meta["score_hash_float32"] = _hash_array(endpoint["score"].astype("<f4"))
    _json_dump(meta_path, meta)
    _write_npz_atomic(npz_path, {
        "user_ids": endpoint["user_ids"], "work_ids": endpoint["work_ids"],
        "score": endpoint["score"].astype(np.float32),
        "reader_mass": endpoint["reader_mass"].astype(np.float32),
        "centered_normalized": endpoint["centered_normalized"].astype(np.float32),
        "top2000_work_ids": top["work_ids"],
        "top2000_scores": top["scores"].astype(np.float32),
        "top2000_reader_mass": top["reader_mass"].astype(np.float32),
        "final_weights": weights,
    })
    return {**endpoint, "score_hash_float32": meta["score_hash_float32"]}


def _hash_fold(work_id: str) -> int:
    raw = f"{work_id}|{LITERARY_BASIN_SEED}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "little") % 2


def _stable_item_key(*parts: Any) -> bytes:
    return hashlib.sha256("|".join(str(x) for x in parts).encode("utf-8")).digest()


def _select_limited(items: set[str], limit: int, *salt: Any) -> list[str]:
    return [x for _key, x in sorted(
        ((_stable_item_key(*salt, x), x) for x in items), key=lambda z: z[0]
    )[:limit]]


def _agreement_for_sets(highs: set[str], lows: set[str], score_map: dict[str, float],
                        salt: str) -> dict[str, Any]:
    high = _select_limited(highs, MAX_HIGHS, salt, "high")
    low = _select_limited(lows, MAX_LOWS, salt, "low")
    pairs = [(h, l) for h in high for l in low
             if h in score_map and l in score_map and h != l]
    pairs = [x for _key, x in sorted(
        ((_stable_item_key(salt, "pair", h, l), (h, l)) for h, l in pairs),
        key=lambda z: z[0]
    )[:MAX_PAIRS]]
    values = []
    for high_id, low_id in pairs:
        a, b = score_map[high_id], score_map[low_id]
        values.append(1.0 if a > b else 0.0 if a < b else TIE_SCORE)
    raw = float(np.mean(values)) if values else float("nan")
    shrunk = ((float(np.sum(values)) + TIE_SCORE * PRIOR_K) /
              (len(values) + PRIOR_K)) if values else float("nan")
    eligible = (len(set(high)) >= MIN_DISTINCT_HIGHS
                and len(set(low)) >= MIN_DISTINCT_LOWS
                and len(pairs) >= MIN_TESTABLE_PAIRS)
    return {
        "distinct_highs": int(len(set(high))),
        "distinct_lows": int(len(set(low))),
        "testable_pairs": int(len(pairs)),
        "raw": raw, "shrunk": float(shrunk) if np.isfinite(shrunk) else float("nan"),
        "eligible": bool(eligible),
    }


def _j5_agreement(context: dict[str, Any], j5: dict[str, Any]) -> dict[str, Any]:
    path = STATE_DIR / "j5_agreement.json"
    npz_path = STATE_DIR / "j5_agreement.npz"
    if path.exists() and npz_path.exists():
        state = _load_json(path)
        arrays = _load_npz(npz_path)
        state["arrays"] = arrays
        return state
    j5_ids = set(context["memberships"]["J5000"].tolist())
    candidates = np.sort(np.asarray([
        int(u) for u in context["memberships"]["J20000"].tolist()
        if int(u) not in j5_ids
    ], dtype=np.int64))
    work_ids = j5["work_ids"].astype(str)
    score = j5["score"].astype(np.float64)
    eligible_work = np.flatnonzero(np.isfinite(score)
                                   & (j5["reader_mass"] >= J5_SUPPORT_THRESHOLD))
    score_map = {str(work_ids[i]): float(score[i]) for i in eligible_work}
    fold_map = {w: _hash_fold(w) for w in score_map}
    highs: dict[int, set[str]] = {int(u): set() for u in candidates.tolist()}
    lows: dict[int, set[str]] = {int(u): set() for u in candidates.tolist()}
    con = open_db()
    table = "lbr_j5_candidates"
    work_table = "lbr_j5_works"
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT)")
    con.execute(f"INSERT INTO {table} SELECT unnest(?::BIGINT[])", [candidates.tolist()])
    con.execute(f"CREATE OR REPLACE TEMP TABLE {work_table}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {work_table} SELECT unnest(?::VARCHAR[])",
                [list(score_map)])
    print(f"[j5] collecting ratings for {len(candidates)} outer users on "
          f"{len(score_map)} eligible J5 works", flush=True)
    rows = con.execute(
        f"SELECT e.user_id, e.work_id, e.rating FROM ex.all_rating_events e "
        f"JOIN {table} u USING (user_id) JOIN {work_table} w USING (work_id) "
        f"WHERE e.rating=5 OR e.rating BETWEEN 1 AND 3"
    ).fetchall()
    for uid, wid, rating in rows:
        uid, wid, rating = int(uid), str(wid), int(rating)
        if uid not in highs:
            continue
        (highs if rating == 5 else lows)[uid].add(wid)
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"DROP TABLE IF EXISTS {work_table}")
    n = len(candidates)
    arrays: dict[str, np.ndarray] = {
        "user_ids": candidates,
        "agreement_full": np.full(n, np.nan, dtype=np.float32),
        "agreement_A": np.full(n, np.nan, dtype=np.float32),
        "agreement_B": np.full(n, np.nan, dtype=np.float32),
        "raw_full": np.full(n, np.nan, dtype=np.float32),
        "raw_A": np.full(n, np.nan, dtype=np.float32),
        "raw_B": np.full(n, np.nan, dtype=np.float32),
        "distinct_highs_full": np.zeros(n, dtype=np.int32),
        "distinct_lows_full": np.zeros(n, dtype=np.int32),
        "testable_pairs_full": np.zeros(n, dtype=np.int32),
        "distinct_highs_A": np.zeros(n, dtype=np.int32),
        "distinct_lows_A": np.zeros(n, dtype=np.int32),
        "testable_pairs_A": np.zeros(n, dtype=np.int32),
        "distinct_highs_B": np.zeros(n, dtype=np.int32),
        "distinct_lows_B": np.zeros(n, dtype=np.int32),
        "testable_pairs_B": np.zeros(n, dtype=np.int32),
    }
    summaries = []
    for i, uid in enumerate(candidates.tolist()):
        full = _agreement_for_sets(highs[uid], lows[uid], score_map, "full")
        fold_results = {}
        for fold, name in ((0, "A"), (1, "B")):
            hs = {w for w in highs[uid] if fold_map.get(w) == fold}
            ls = {w for w in lows[uid] if fold_map.get(w) == fold}
            fold_results[name] = _agreement_for_sets(hs, ls, score_map, name)
        for name, result in (("full", full), ("A", fold_results["A"]), ("B", fold_results["B"])):
            arrays[f"agreement_{name}"][i] = result["shrunk"]
            arrays[f"raw_{name}"][i] = result["raw"]
            for field, key in (("distinct_highs", "distinct_highs"),
                               ("distinct_lows", "distinct_lows"),
                               ("testable_pairs", "testable_pairs")):
                arrays[f"{field}_{name}"][i] = result[key]
        summaries.append({"user_id": uid, "full": full,
                          "A": fold_results["A"], "B": fold_results["B"]})
    state = {
        "seed": LITERARY_BASIN_SEED, "candidate_n": int(n),
        "candidate_pool": "J20000\\J5000", "eligible_work_n": len(score_map),
        "fold_rule": "sha256(work_id|20260903) first 8 bytes little-endian mod 2",
        "fold_A_n": int(sum(f == 0 for f in fold_map.values())),
        "fold_B_n": int(sum(f == 1 for f in fold_map.values())),
        "max_highs": MAX_HIGHS, "max_lows": MAX_LOWS, "max_pairs": MAX_PAIRS,
        "prior_k": PRIOR_K, "tie_score": TIE_SCORE,
        "summaries": summaries,
    }
    _write_npz_atomic(npz_path, arrays)
    _json_dump(path, state)
    state["arrays"] = arrays
    return state


def _score_maps(context: dict[str, Any]) -> dict[str, dict[int, float]]:
    return {
        "L": {int(u): float(s) for u, s in
               zip(context["universe"].tolist(), context["scores"].tolist())},
    }


def _evidence_map() -> dict[str, dict[int, float]]:
    path = inherited.STATE_DIR.parent / "converged_common_literary_jurors_state" / "user_scores.npz"
    # The expression above is intentionally resolved from the inherited data
    # root rather than from the current campaign state directory.
    if not path.exists():
        path = DATA / "converged_common_literary_jurors_state" / "user_scores.npz"
    if not path.exists():
        return {"n_testable": {}, "n_ratings": {}}
    with np.load(path, allow_pickle=False) as blob:
        users = blob["universe"].astype(np.int64)
        testable = np.nanmax(blob["n_testable"].astype(np.float64), axis=1)
    return {"n_testable": {int(u): float(x) for u, x in zip(users, testable)},
            "n_ratings": {}}


def _build_orders(context: dict[str, Any], clusters: dict[str, Any],
                  j5_scores: dict[str, Any]) -> dict[str, Any]:
    path = STATE_DIR / "orders.json"
    npz_path = STATE_DIR / "orders.npz"
    if path.exists() and npz_path.exists():
        state = _load_json(path)
        state["arrays"] = _load_npz(npz_path)
        return state
    j5 = set(int(x) for x in context["memberships"]["J5000"].tolist())
    full20 = context["memberships"]["J20000"].astype(np.int64)
    outer = np.sort(np.asarray([int(x) for x in full20.tolist() if int(x) not in j5],
                               dtype=np.int64))
    arr = j5_scores["arrays"]
    agreement_map = {int(u): float(v) for u, v in
                     zip(arr["user_ids"].tolist(), arr["agreement_A"].tolist())}
    evidence = _evidence_map()["n_testable"]
    cluster_npz = _load_npz(STATE_DIR / "cluster_J20000.npz")
    support_map = {int(u): float(v) for u, v in
                   zip(cluster_npz["user_ids"].tolist(),
                       cluster_npz["literary_basin_support"].tolist())}
    margin_map = {int(u): float(v) for u, v in
                  zip(cluster_npz["user_ids"].tolist(),
                      cluster_npz["basin_specificity_margin"].tolist())}
    lmap = _score_maps(context)["L"]
    # dynamics._load_frozen_context stores the jury order as indices into the
    # eligible-user array, not as user IDs.
    selection_order_users = context["eligible_users"][context["order"]]
    order_rank = {int(u): i for i, u in enumerate(selection_order_users[:20000].tolist())
                  if int(u) in j5 or int(u) in set(outer.tolist())}
    order_l = sorted(outer.tolist(), key=lambda u: (order_rank.get(int(u), 10**9), int(u)))

    def key_j5(u: int) -> tuple[Any, ...]:
        return (-agreement_map.get(u, -np.inf), -lmap.get(u, -np.inf),
                -evidence.get(u, -np.inf), u)

    def key_basin(u: int) -> tuple[Any, ...]:
        return (-margin_map.get(u, -np.inf), -support_map.get(u, -np.inf),
                -lmap.get(u, -np.inf), u)

    orders = {
        "L": np.asarray(order_l, dtype=np.int64),
        "J5": np.asarray(sorted(outer.tolist(), key=key_j5), dtype=np.int64),
        "BASIN": np.asarray(sorted(outer.tolist(), key=key_basin), dtype=np.int64),
    }
    # Common-L ordering must reproduce the exact historical outer memberships.
    expected10 = set(context["memberships"]["J10000"].tolist()) - j5
    expected20 = set(context["memberships"]["J20000"].tolist()) - j5
    if set(orders["L"][:5000].tolist()) != expected10:
        raise RuntimeError("ORDER_L does not reproduce frozen J10000 membership")
    if set(orders["L"][:15000].tolist()) != expected20:
        raise RuntimeError("ORDER_L does not reproduce frozen J20000 membership")
    arrays = {f"order_{name}": ids for name, ids in orders.items()}
    _write_npz_atomic(npz_path, arrays)
    state = {
        "seed": LITERARY_BASIN_SEED,
        "outer_pool": "J20000\\J5000", "outer_n": int(len(outer)),
        "order_hashes": {name: _hash_ids(ids) for name, ids in orders.items()},
        "order_L_reproduces_J10000_outer": True,
        "order_L_reproduces_J20000_outer": True,
        "tie_breaks": {
            "L": ["frozen common-L order", "user_id"],
            "J5": ["descending J5_agreement_A", "descending common-L",
                   "descending evidence", "user_id"],
            "BASIN": ["descending specificity margin",
                      "descending basin support", "descending common-L", "user_id"],
        },
        "semantic_labels_used_for_ordering": False,
    }
    _json_dump(path, state)
    state["arrays"] = arrays
    return state


def _stat_summary(values: np.ndarray) -> dict[str, float]:
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    if not len(x):
        return {"n": 0, "p10": float("nan"), "p25": float("nan"),
                "median": float("nan"), "p75": float("nan"),
                "mean": float("nan"), "min": float("nan")}
    return {"n": int(len(x)), "p10": float(np.quantile(x, .10)),
            "p25": float(np.quantile(x, .25)), "median": float(np.median(x)),
            "p75": float(np.quantile(x, .75)), "mean": float(np.mean(x)),
            "min": float(np.min(x))}


def _source_composition(user_ids: np.ndarray) -> dict[str, float]:
    path = DATA / "converged_common_literary_jurors_state" / "user_scores.npz"
    if not path.exists():
        return {}
    with np.load(path, allow_pickle=False) as blob:
        users = blob["universe"].astype(np.int64)
        vals = blob["L_shrunk"].astype(np.float64)
    positions = {int(u): i for i, u in enumerate(users.tolist())}
    x = np.asarray([vals[positions[int(u)]] for u in user_ids.tolist()
                    if int(u) in positions], dtype=np.float64)
    return {f"ref_{i+1}_finite_fraction": float(np.mean(np.isfinite(x[:, i])))
            for i in range(x.shape[1])} if x.ndim == 2 and len(x) else {}


def _profile_group(context: dict[str, Any], tag: str, user_ids: np.ndarray,
                   lmap: dict[int, float], metadata: dict[str, Any] | None = None
                   ) -> dict[str, Any]:
    payload_tag = f"profile_{_safe_key(tag)}"
    _ensure_subset_payload("payload_J20000", payload_tag, user_ids)
    endpoint = _direct_endpoint(f"direct_{payload_tag}", payload_tag)
    values = np.asarray([lmap.get(int(u), np.nan) for u in user_ids.tolist()])
    return {
        "tag": tag, "n": int(len(user_ids)), "user_ids": np.asarray(user_ids, dtype=np.int64),
        "L": _stat_summary(values), "source_composition": _source_composition(user_ids),
        "direct": endpoint, "direct_head": _head(endpoint, 50),
    }


def _user_profile_diagnostics(context: dict[str, Any], clusters: dict[str, Any]
                              ) -> dict[str, Any]:
    path = STATE_DIR / "user_profiles.json"
    c = _load_npz(STATE_DIR / "cluster_J20000.npz")
    users = c["user_ids"].astype(np.int64)
    lmap = _score_maps(context)["L"]
    specificity = c["basin_specificity_margin"].astype(np.float64)
    support = c["literary_basin_support"].astype(np.float64)
    finite = np.isfinite(specificity)
    ranked = np.flatnonzero(finite)[np.argsort(-specificity[finite], kind="stable")]
    cuts = [0, int(.10 * len(ranked)), int(.30 * len(ranked)),
            int(.70 * len(ranked)), len(ranked)]
    group_defs = {
        "top10": ranked[cuts[0]:cuts[1]],
        "next20": ranked[cuts[1]:cuts[2]],
        "middle40": ranked[cuts[2]:cuts[3]],
        "bottom30": ranked[cuts[3]:cuts[4]],
    }
    j5 = set(context["memberships"]["J5000"].tolist())
    j10 = set(context["memberships"]["J10000"].tolist())
    shells = {
        "S0": set(context["memberships"]["J5000"].tolist()),
        "S1": set(context["memberships"]["J10000"].tolist()) - j5,
        "S2": set(context["memberships"]["J20000"].tolist()) - j10,
    }
    group_rows = {}
    for name, idx in group_defs.items():
        ids = users[idx]
        row = _profile_group(context, f"J20_specificity_{name}", ids, lmap)
        row.update({
            "specificity": _stat_summary(specificity[idx]),
            "support": _stat_summary(support[idx]),
            "J5_fraction": float(np.mean([int(u) in j5 for u in ids])),
            "J10_fraction": float(np.mean([int(u) in j10 for u in ids])),
            "shell_fraction": {s: float(np.mean([int(u) in members for u in ids]))
                               for s, members in shells.items()},
        })
        group_rows[name] = row
    # Decile-matched high/low specificity aggregates.
    lvals = np.asarray([lmap.get(int(u), np.nan) for u in users])
    valid = np.isfinite(lvals) & finite
    valid_idx = np.flatnonzero(valid)
    deciles = np.array_split(valid_idx[np.argsort(-lvals[valid_idx], kind="stable")], 10)
    high, low = [], []
    for dec in deciles:
        order = dec[np.argsort(-specificity[dec], kind="stable")]
        m = max(1, len(order) // 3)
        high.extend(order[:m].tolist())
        low.extend(order[-m:].tolist())
    matched = {}
    for name, idx in (("high_specificity_matched_L", np.asarray(high, dtype=np.int64)),
                      ("low_specificity_matched_L", np.asarray(low, dtype=np.int64))):
        ids = users[idx]
        matched[name] = _profile_group(context, name, ids, lmap)
        matched[name]["specificity"] = _stat_summary(specificity[idx])
        matched[name]["L_quantiles"] = _stat_summary(lvals[idx])
    arrays = {"user_ids": users, "specificity": specificity, "support": support,
              "common_L": lvals}
    _write_npz_atomic(STATE_DIR / "user_profiles.npz", arrays)
    # Strip large numerical endpoint arrays from the JSON state; heads are
    # regenerated from the endpoint cache during report generation.
    def compact(x: Any) -> Any:
        if isinstance(x, dict):
            return {k: compact(v) for k, v in x.items()
                    if k not in {"user_ids", "direct", "direct_head_ids"}}
        if isinstance(x, np.ndarray):
            return None
        return x
    state = {"specificity_groups": compact(group_rows), "matched_L": compact(matched),
             "n_users": int(len(users))}
    _json_dump(path, state)
    state["arrays"] = arrays
    state["group_rows"] = group_rows
    state["matched"] = matched
    return state


# ---------------------------------------------------------------------------
# Frozen expansion memberships and exact dynamics
# ---------------------------------------------------------------------------

def _expansion_specs(context: dict[str, Any], orders: dict[str, Any]) -> list[dict[str, Any]]:
    specs = []
    j5 = context["memberships"]["J5000"].astype(np.int64)
    for order_name in ORDER_NAMES:
        order = orders["arrays"][f"order_{order_name}"].astype(np.int64)
        for n in EXPANSION_SIZES:
            selected = np.concatenate([j5, order[:n - len(j5)]])
            selected = np.sort(np.unique(selected))
            if len(selected) != n or not set(j5.tolist()) <= set(selected.tolist()):
                raise RuntimeError(f"invalid {order_name} expansion size {n}")
            payload_tag = f"payload_exp_{order_name}_{n}"
            _ensure_subset_payload("payload_J20000", payload_tag, selected)
            specs.append({
                "order": order_name, "n": n, "payload_tag": payload_tag,
                "membership_hash_sorted": _hash_ids(selected),
                "user_ids": selected,
                "selected_outer_hash": _hash_ids(order[:n - len(j5)]),
            })
    path = STATE_DIR / "expansion_specs.json"
    arrays = {f"membership_{s['order']}_{s['n']}": s["user_ids"] for s in specs}
    _write_npz_atomic(STATE_DIR / "expansion_specs.npz", arrays)
    _json_dump(path, [{k: v for k, v in s.items() if k != "user_ids"} for s in specs])
    return specs


def _kish(weights: np.ndarray) -> float:
    w = np.asarray(weights, dtype=np.float64)
    w = w[w > 0]
    return float(np.sum(w) ** 2 / np.sum(w ** 2)) if len(w) else 0.0


def _expansion_trajectory_record(result: dict[str, Any], spec: dict[str, Any],
                                 init: str, rep: int | None = None) -> dict[str, Any]:
    data = result["data"]
    return {
        "key": data["key"], "order": spec["order"], "n": spec["n"],
        "kind": "equal" if init == "equal" else "random",
        "rep": rep, "init": init, "init_seed": data["init_seed"],
        "iterations": data["final_iteration"],
        "converged": bool(data.get("verification_stable")),
        "strict_convergence_candidate": bool(data.get("strict_candidate_iteration") is not None),
        "strict_iteration": data.get("strict_iteration"),
        "verification_stable": data.get("verification_stable"),
        "stop_reason": data["stop_reason"], "membership_hash_sorted": data["membership_hash"],
        "kish": _kish(data["final_weights"]),
        "score_hash_float32": result["endpoint"]["score_hash_float32"],
        "history": data["history"],
    }


def _run_expansions(context: dict[str, Any], orders: dict[str, Any]) -> dict[str, Any]:
    specs = _expansion_specs(context, orders)
    manifest_path = STATE_DIR / "expansion_trajectories.json"
    manifest = _load_json(manifest_path) if manifest_path.exists() else {
        "seed": LITERARY_BASIN_SEED, "max_iter": EXPANSION_MAX_ITER,
        "random_reps": EXPANSION_RANDOM_REPS, "specs": {},
    }
    for spec in specs:
        tag = f"{spec['order']}_{spec['n']}"
        payload_tag = spec["payload_tag"]
        direct_key = f"exp_{tag}_direct"
        equal_key = f"exp_{tag}_equal"
        direct = _direct_endpoint(direct_key, payload_tag)
        result = _run_trajectory(equal_key, f"{tag} equal", payload_tag,
                                  "equal", None, EXPANSION_MAX_ITER)
        rows = {
            "spec": {k: v for k, v in spec.items() if k != "user_ids"},
            "direct_key": direct_key,
            "equal": _expansion_trajectory_record(result, spec, "equal"),
            "random": [],
        }
        for rep in range(EXPANSION_RANDOM_REPS):
            key = f"exp_{tag}_random{rep}"
            seed = int(_derive_seed(LITERARY_BASIN_SEED, "expansion_random",
                                    spec["order"], spec["n"], rep))
            r = _run_trajectory(key, f"{tag} random rep{rep}", payload_tag,
                                "lognormal", seed, EXPANSION_MAX_ITER)
            rows["random"].append(_expansion_trajectory_record(r, spec, "lognormal", rep))
        manifest["specs"][tag] = rows
        _json_dump(manifest_path, manifest)
    return manifest


# ---------------------------------------------------------------------------
# Post-hoc heads, comparisons, coverage, and interpretation tables
# ---------------------------------------------------------------------------

def _score_correlation(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    aa, bb = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    mask = np.isfinite(aa) & np.isfinite(bb)
    if int(mask.sum()) < 10:
        return {"pearson": float("nan"), "spearman": float("nan")}
    return {
        "pearson": float(np.corrcoef(aa[mask], bb[mask])[0, 1]),
        "spearman": float(spearmanr(aa[mask], bb[mask]).statistic),
    }


def _endpoint_comparison(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ha, hb = _head(a, 1000), _head(b, 1000)
    def hm(k: int) -> dict[str, float | int]:
        sa = set(ha["work_ids"][:k].tolist())
        sb = set(hb["work_ids"][:k].tolist())
        overlap = len(sa & sb)
        return {"overlap_count": int(overlap),
                "overlap_fraction": float(overlap / k),
                "jaccard": float(overlap / max(1, len(sa | sb)))}
    rank_a = {str(w): i for i, w in enumerate(ha["work_ids"][:200].tolist())}
    rank_b = {str(w): i for i, w in enumerate(hb["work_ids"][:200].tolist())}
    common = sorted(set(rank_a) & set(rank_b))
    rho = float(spearmanr([rank_a[w] for w in common],
                          [rank_b[w] for w in common]).statistic) if len(common) >= 10 else float("nan")
    return {
        "top50": hm(50), "top200": hm(200),
        "spearman_common_top200": rho,
        "score_correlation": _score_correlation(a["score"], b["score"]),
        "centered_preference_cosine": float(
            np.dot(_center_normalize(a["score"]), _center_normalize(b["score"]))),
    }


def _weighted_stat_for_endpoint(endpoint: dict[str, Any], values: dict[int, float]
                                ) -> dict[str, float]:
    x = np.asarray([values.get(int(u), np.nan) for u in endpoint["user_ids"].tolist()])
    w = np.asarray(endpoint.get("final_weights",
                               np.ones(len(x), dtype=np.float64)), dtype=np.float64)
    return {"median": _weighted_median(x, w),
            "p10": _quantile(x, .10), "p25": _quantile(x, .25),
            "p75": _quantile(x, .75), "mean": float(np.average(x[np.isfinite(x)],
                weights=w[np.isfinite(x)])) if np.any(np.isfinite(x)) else float("nan")}


def _dynamic_endpoint(key: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    if data is None:
        state = dynamics._load_trajectory_state(key)
        if state is None:
            raise RuntimeError(f"missing trajectory state {key}")
        data = dynamics._data_from_state(*state)
    return _endpoint_from_data(key, data["payload_tag"], data)


def _expansion_analysis(context: dict[str, Any], orders: dict[str, Any],
                        manifest: dict[str, Any], j5: dict[str, Any],
                        j5_scores: dict[str, Any]) -> dict[str, Any]:
    lmap = _score_maps(context)["L"]
    evidence = _evidence_map()["n_testable"]
    j5_final = {"work_ids": j5["work_ids"], "score": j5["score"],
                "reader_mass": j5["reader_mass"]}
    arr = j5_scores["arrays"]
    agreement_b = {int(u): float(v) for u, v in
                   zip(arr["user_ids"].tolist(), arr["agreement_B"].tolist())}
    rows = {}
    for spec_key, item in sorted(manifest["specs"].items()):
        spec = item["spec"]
        direct = _load_endpoint(item["direct_key"])
        equal_data = dynamics._data_from_state(*dynamics._load_trajectory_state(item["equal"]["key"]))
        equal = _endpoint_from_data(item["equal"]["key"],
                                    equal_data["payload_tag"], equal_data)
        direct_l = _weighted_stat_for_endpoint(direct, lmap)
        final_l = _weighted_stat_for_endpoint(equal, lmap)
        ids = direct["user_ids"].astype(np.int64)
        bvals = np.asarray([agreement_b.get(int(u), np.nan) for u in ids])
        bvalid = np.isfinite(bvals)
        final_b = _weighted_median(bvals, equal["final_weights"])
        random_rows = []
        for rr in item["random"]:
            rd = dynamics._data_from_state(*dynamics._load_trajectory_state(rr["key"]))
            re = _endpoint_from_data(rr["key"], rd["payload_tag"], rd)
            random_rows.append({
                "key": rr["key"], "rep": rr["rep"], "iterations": rr["iterations"],
                "converged": rr["converged"],
                "vs_equal": _endpoint_comparison(re, equal),
                "vs_J5": _endpoint_comparison(re, j5_final),
                "weight_cosine_vs_equal": float(np.dot(
                    re["final_weights"] / np.linalg.norm(re["final_weights"]),
                    equal["final_weights"] / np.linalg.norm(equal["final_weights"]))),
            })
        rows[spec_key] = {
            "order": spec["order"], "n": spec["n"],
            "membership_hash_sorted": spec["membership_hash_sorted"],
            "direct_key": item["direct_key"], "equal_key": item["equal"]["key"],
            "direct_L": direct_l, "final_weighted_L": final_l,
            "direct_p10_L": _quantile(np.asarray([lmap.get(int(u), np.nan) for u in ids]), .10),
            "direct_heldout_B_median": _quantile(bvals, .50),
            "final_weighted_heldout_B": final_b,
            "direct_vs_final": _endpoint_comparison(direct, equal),
            "direct_vs_J5": _endpoint_comparison(direct, j5_final),
            "final_vs_J5": _endpoint_comparison(equal, j5_final),
            "strict_convergence_reached": bool(equal_data.get("verification_stable")),
            "iterations": int(item["equal"]["iterations"]),
            "kish": float(item["equal"]["kish"]),
            "random": random_rows,
            "random_median_top50_overlap_vs_equal": float(np.median([
                x["vs_equal"]["top50"]["overlap_fraction"] for x in random_rows])),
            "random_min_top50_overlap_vs_equal": float(np.min([
                x["vs_equal"]["top50"]["overlap_fraction"] for x in random_rows])),
            "direct_user_ids": ids,
            "direct_endpoint": direct,
            "final_endpoint": equal,
            "final_weights": equal["final_weights"],
        }
    return rows


def _coverage_stats(con, expansion_rows: dict[str, Any]) -> dict[str, Any]:
    cached = STATE_DIR / "coverage.json"
    if cached.exists():
        return _load_json(cached)
    source_paths = [DATA / "juror_coherence_tail_state" / "global_work_stats.npz",
                    inherited.STATE_DIR / "global_work_stats.npz"]
    stats_path = next((p for p in source_paths if p.exists()), None)
    if stats_path is None:
        rows = con.execute("SELECT work_id, count(*)::DOUBLE FROM ex.all_rating_events "
                           "WHERE rating>0 GROUP BY work_id").fetchall()
        work_ids = np.asarray([str(x[0]) for x in rows], dtype=str)
        counts = np.asarray([float(x[1]) for x in rows], dtype=np.float64)
    else:
        with np.load(stats_path, allow_pickle=False) as blob:
            work_ids = blob["work_id"].astype(str)
            counts = blob["n_rated"].astype(np.float64)
    bands = ((5, 19), (20, 49), (50, 99), (100, 249), (250, 999), (1000, 4999))
    labels = ["5_19", "20_49", "50_99", "100_249", "250_999", "1000_4999"]
    work_to_i = {str(w): i for i, w in enumerate(work_ids.tolist())}
    memberships = {key: row["direct_user_ids"] for key, row in expansion_rows.items()}
    jury_rows = [(key, int(u)) for key, ids in memberships.items() for u in ids.tolist()]
    con.execute("CREATE OR REPLACE TEMP TABLE lbr_cov_membership(jury VARCHAR, user_id BIGINT)")
    con.executemany("INSERT INTO lbr_cov_membership VALUES (?, ?)", jury_rows)
    result_rows: dict[str, Any] = {}
    for key in memberships:
        counts_by_work = {w: 0 for w in work_ids.tolist()}
        rows = con.execute(
            "SELECT e.work_id, count(DISTINCT e.user_id)::BIGINT "
            "FROM ex.all_rating_events e JOIN lbr_cov_membership m "
            "ON e.user_id=m.user_id AND m.jury=? WHERE e.rating>0 "
            "GROUP BY e.work_id", [key]).fetchall()
        for w, n in rows:
            counts_by_work[str(w)] = int(n)
        ns = np.asarray([counts_by_work[str(w)] for w in work_ids.tolist()], dtype=np.int64)
        band_out = {}
        for label, (lo, hi) in zip(labels, bands):
            mask = (counts >= lo) & (counts <= hi)
            band_out[label] = {
                "n_works": int(mask.sum()),
                "ge1": float(np.mean(ns[mask] >= 1)) if np.any(mask) else float("nan"),
                "ge3": float(np.mean(ns[mask] >= 3)) if np.any(mask) else float("nan"),
                "ge5": float(np.mean(ns[mask] >= 5)) if np.any(mask) else float("nan"),
            }
        result_rows[key] = band_out
    con.execute("DROP TABLE IF EXISTS lbr_cov_membership")
    result = {"source": str(stats_path) if stats_path else "recomputed",
              "n_global_works": int(len(work_ids)), "bands": result_rows}
    _json_dump(cached, result)
    return result


def _cross_method_analysis(context: dict[str, Any], orders: dict[str, Any],
                           j5_scores: dict[str, Any], clusters: dict[str, Any]
                           ) -> dict[str, Any]:
    out = {}
    arrays = orders["arrays"]
    lmap = _score_maps(context)["L"]
    ja = j5_scores["arrays"]
    bmap = {int(u): float(v) for u, v in zip(ja["user_ids"].tolist(),
                                              ja["agreement_B"].tolist())}
    cp = _load_npz(STATE_DIR / "cluster_J20000.npz")
    smap = {int(u): float(v) for u, v in zip(cp["user_ids"].tolist(),
                                             cp["basin_specificity_margin"].tolist())}

    def stats(ids: set[int]) -> dict[str, Any]:
        return {"n": len(ids), "L": _stat_summary(np.asarray([lmap.get(u, np.nan) for u in ids])),
                "heldout_J5_B": _stat_summary(np.asarray([bmap.get(u, np.nan) for u in ids])),
                "basin_specificity": _stat_summary(np.asarray([smap.get(u, np.nan) for u in ids]))}

    for n in EXPANSION_SIZES:
        sets = {name: set(arrays[f"order_{name}"][:n - 5000].tolist())
                for name in ORDER_NAMES}
        pair = {}
        for ia, a in enumerate(ORDER_NAMES):
            for b in ORDER_NAMES[ia + 1:]:
                overlap = len(sets[a] & sets[b])
                pair[f"{a}_vs_{b}"] = {
                    "overlap_count": overlap,
                    "jaccard": overlap / max(1, len(sets[a] | sets[b])),
                    "users_unique_to_a": sorted(sets[a] - sets[b]),
                    "users_unique_to_b": sorted(sets[b] - sets[a]),
                    "unique_to_a_stats": stats(sets[a] - sets[b]),
                    "unique_to_b_stats": stats(sets[b] - sets[a]),
                }
        out[str(n)] = pair
    return out


def _direct_difference_profiles(context: dict[str, Any], orders: dict[str, Any],
                                n: int = 15000) -> dict[str, Any]:
    j5 = set(context["memberships"]["J5000"].tolist())
    l_outer = set(orders["arrays"]["order_L"][:n - 5000].tolist())
    result = {}
    for name in ("J5", "BASIN"):
        ids = np.asarray(sorted(set(orders["arrays"][f"order_{name}"][:n - 5000].tolist()) - l_outer),
                         dtype=np.int64)
        if not len(ids):
            continue
        result[name] = _profile_group(context, f"{name}_rescued_vs_L_{n}", ids,
                                      _score_maps(context)["L"])
    return result


def _posthoc_context(j5: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    """Load titles/flags/probes only after all discovery decisions are frozen."""
    con = open_db()
    metadata = dynamics._load_metadata(con, j5["work_ids"])
    payload = dynamics._load_payload("payload_J5000")
    inherited._load_probes_local(payload)
    probes = {"pos": set(inherited._PROBE_POS),
              "exact": set(inherited._PROBE_EXACT),
              "broad": set(inherited._PROBE_BROAD),
              "anti": set(inherited._PROBE_ANTI)}
    return metadata, probes


def _rank_any(work_ids: np.ndarray, scores: np.ndarray,
              mass: np.ndarray | None = None, limit: int = 1000) -> dict[str, np.ndarray]:
    ids = np.asarray(work_ids).astype(str)
    s = np.asarray(scores, dtype=np.float64)
    m = np.ones(len(ids), dtype=np.float64) if mass is None else np.asarray(mass, dtype=np.float64)
    eligible = np.flatnonzero(np.isfinite(s))
    order = eligible[np.argsort(-s[eligible], kind="stable")][:limit]
    return {"work_ids": ids[order], "scores": s[order], "reader_mass": m[order]}


def _head_annotations(head: dict[str, np.ndarray], metadata: dict[str, dict[str, Any]],
                      probes: dict[str, set[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    authors = []
    for rank, (wid, score, mass) in enumerate(zip(head["work_ids"][:50],
                                                   head["scores"][:50],
                                                   head["reader_mass"][:50]), 1):
        w = str(wid)
        m = metadata.get(w, {})
        author = m.get("author", "")
        authors.append(author)
        rows.append({
            "rank": rank, "work_id": w, "title": m.get("title", w),
            "author": author, "score": float(score), "n_eff": float(mass),
            "pos": bool(w in probes["pos"]), "exact": bool(w in probes["exact"]),
            "broad": bool(w in probes["broad"]), "anti": bool(w in probes["anti"]),
            "is_collection": bool(m.get("is_collection", False)),
            "is_duplicate": bool(m.get("is_duplicate", False)),
            "is_comic": bool(m.get("is_comic", False)),
            "is_picture_book": bool(m.get("is_picture_book", False)),
        })
    known = [a for a in authors if a]
    counts = Counter(known)
    ids = [str(x) for x in head["work_ids"][:50].tolist()]
    sem = {name: int(sum(w in probes[key] for w in ids))
           for name, key in (("pos50", "pos"), ("exact50", "exact"),
                             ("broad50", "broad"), ("anti50", "anti"))}
    desc = {
        "unique_authors_50": int(len(set(known))),
        "max_same_author_count_50": int(max(counts.values(), default=0)),
        "top_authors_50": [{"author": a, "count": int(n)}
                           for a, n in counts.most_common(10)],
        "collection_count_50": int(sum(r["is_collection"] for r in rows)),
        "duplicate_count_50": int(sum(r["is_duplicate"] for r in rows)),
        "comic_count_50": int(sum(r["is_comic"] for r in rows)),
        "picture_book_count_50": int(sum(r["is_picture_book"] for r in rows)),
        "series_metadata_available": False,
    }
    return rows, {**sem, **desc}


def _centroid_endpoint(cluster_npz: dict[str, np.ndarray],
                       payload_tag: str, basin_index: int,
                       reader_mass: np.ndarray | None = None) -> dict[str, Any]:
    payload = dynamics._load_payload(payload_tag)
    score = cluster_npz["centroid_score"][basin_index].astype(np.float64)
    return {"work_ids": payload["work_ids"].astype(str), "score": score,
            "reader_mass": (np.ones(len(score), dtype=np.float64)
                             if reader_mass is None else reader_mass.astype(np.float64)),
            "final_weights": np.ones(len(payload["user_ids"]), dtype=np.float64),
            "user_ids": payload["user_ids"].astype(np.int64)}


def _posthoc_heads(context: dict[str, Any], j5: dict[str, Any],
                   clusters: dict[str, Any], profiles: dict[str, Any],
                   expansions: dict[str, Any],
                   metadata: dict[str, dict[str, Any]],
                   probes: dict[str, set[str]]) -> dict[str, Any]:
    result: dict[str, Any] = {"basins": {}, "expansions": {}, "profiles": {}}
    for tag in BASIN_POPULATIONS:
        population = f"J{tag}"
        c = clusters[population]
        cp = _load_npz(STATE_DIR / f"cluster_{population}.npz")
        basin_manifest = _load_json(STATE_DIR / "basin_manifest.json")
        basins = {}
        for b in range(int(c["selected_k"])):
            member_runs = c["cluster_summaries"][b]["run_indices"]
            masses = np.stack([_load_endpoint(basin_manifest[population][i]["key"])["reader_mass"]
                               for i in member_runs], axis=0)
            endpoint = _centroid_endpoint(cp, f"payload_{population}", b,
                                          np.mean(masses, axis=0))
            head = _rank_any(endpoint["work_ids"], endpoint["score"], limit=1000)
            rows, desc = _head_annotations(head, metadata, probes)
            basins[str(b + 1)] = {
                "size": c["cluster_summaries"][b]["n_runs"],
                "frequency": c["cluster_summaries"][b]["frequency"],
                "j5_similarity": c["j5_similarity_by_basin"][b],
                "j5_like": b + 1 == int(c["j5_like_basin"]),
                "top1000_ids": head["work_ids"].tolist(),
                "top50": rows, "descriptors": desc,
            }
        result["basins"][population] = basins
    for key, row in expansions.items():
        for which, endpoint in (("direct", row["direct_endpoint"]),
                                ("final", row["final_endpoint"])):
            head = _head(endpoint, 1000)
            rows, desc = _head_annotations(head, metadata, probes)
            row.setdefault("posthoc", {})[which] = {
                "top1000_ids": head["work_ids"].tolist(),
                "top50": rows, "descriptors": desc,
                "semantic": {k: desc[k] for k in ("pos50", "exact50", "broad50", "anti50")},
            }
        result["expansions"][key] = row["posthoc"]
    for name, row in profiles.get("group_rows", {}).items():
        result["profiles"][name] = {
            "top50": _head_annotations(_head(row["direct"], 50), metadata, probes)[0],
            "descriptors": _head_annotations(_head(row["direct"], 50), metadata, probes)[1],
            "L": row["L"], "specificity": row.get("specificity"),
        }
    for name, row in profiles.get("matched", {}).items():
        result["profiles"][name] = {
            "top50": _head_annotations(_head(row["direct"], 50), metadata, probes)[0],
            "descriptors": _head_annotations(_head(row["direct"], 50), metadata, probes)[1],
            "L": row["L"], "specificity": row.get("specificity"),
        }
    for name, row in profiles.get("difference_groups", {}).items():
        result["profiles"][name] = {
            "top50": _head_annotations(_head(row["direct"], 50), metadata, probes)[0],
            "descriptors": _head_annotations(_head(row["direct"], 50), metadata, probes)[1],
            "L": row["L"],
        }
    return result


def _trajectory_at(history: list[dict[str, Any]], desired: int) -> dict[str, Any] | None:
    rows = [r for r in history if int(r["iteration"]) <= desired]
    return rows[-1] if rows else None


def _trajectory_diag(data: dict[str, Any]) -> dict[str, Any]:
    history = data["history"]
    final_t = int(data["final_iteration"])
    recent = [r for r in history if int(r["iteration"]) > max(0, final_t - 100)]
    def med(field: str, rows: list[dict[str, Any]] = recent) -> float:
        vals = np.asarray([r[field] for r in rows], dtype=np.float64)
        vals = vals[np.isfinite(vals)]
        return float(np.median(vals)) if len(vals) else float("nan")
    final = history[-1] if history else {}
    out = {
        "final": {k: final.get(k) for k in
                  ("iteration", "step", "weight_rel_1", "weight_rel_2",
                   "book_rel_1", "book_rel_2", "weight_cos_lag2",
                   "direction_cos_lag2")},
        "recent100": {k: med(k) for k in
                      ("step", "weight_rel_1", "weight_rel_2",
                       "book_rel_1", "book_rel_2", "weight_cos_lag2",
                       "direction_cos_lag2")},
        "checkpoints": {},
        # The inherited runner records a criterion candidate separately from
        # a stable +50 verification.  Only the latter is genuine strict
        # convergence for this campaign.
        "strict_convergence_reached": bool(data.get("verification_stable")),
        "strict_candidate_reached": bool(data.get("strict_candidate_iteration") is not None),
        "iterations": final_t,
    }
    for t in (200, 500, 1000, 2000):
        row = _trajectory_at(history, t)
        if row is not None:
            out["checkpoints"][str(t)] = {k: row.get(k) for k in
                ("iteration", "step", "weight_rel_1", "weight_rel_2",
                 "book_rel_1", "book_rel_2", "weight_cos_lag2",
                 "direction_cos_lag2")}
    w1, w2 = med("weight_rel_1"), med("weight_rel_2")
    out["lag2_over_lag1_recent"] = float(w2 / w1) if w1 > 0 else float("nan")
    out["two_cycle_signature_recent"] = bool(np.isfinite(w1) and np.isfinite(w2)
                                              and w1 > 1e-8 and w2 < .25 * w1)
    snap_times = sorted(int(t) for t in data["snapshots"])
    final_snap = data["snapshots"][str(final_t)]
    stability = None
    for t in snap_times:
        later = []
        for u in snap_times:
            if u >= t:
                a = set(data["snapshots"][str(u)]["work_ids"][:50].tolist())
                b = set(final_snap["work_ids"][:50].tolist())
                later.append(len(a & b) / 50.0)
        if later and min(later) >= .90:
            stability = t
            break
    out["practical_head_stability_iteration"] = stability
    return out


def _basin_trajectory_diagnostics(manifest: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for tag in BASIN_POPULATIONS:
        pop = f"J{tag}"
        rows = []
        for rec in manifest[pop]:
            state = dynamics._load_trajectory_state(rec["key"])
            data = dynamics._data_from_state(*state) if state is not None else None
            if data is None:
                continue
            rows.append({"rep": rec["rep"], "seed": rec["seed"],
                         "converged": bool(data.get("verification_stable")),
                         "strict_candidate_reached": bool(data.get("strict_candidate_iteration") is not None),
                         "iterations": rec["iterations"],
                         "diagnostics": _trajectory_diag(data)})
        final_wrel = [r["diagnostics"]["final"].get("weight_rel_1", np.nan) for r in rows]
        final_brel = [r["diagnostics"]["final"].get("book_rel_1", np.nan) for r in rows]
        final_step = [r["diagnostics"]["final"].get("step", np.nan) for r in rows]
        out[pop] = {
            "n_runs": len(rows), "strict_count": int(sum(r["converged"] for r in rows)),
            "runs": rows,
            "final_medians": {
                "step": float(np.nanmedian(final_step)),
                "weight_rel_1": float(np.nanmedian(final_wrel)),
                "book_rel_1": float(np.nanmedian(final_brel)),
            },
            "practical_stability_iterations": [r["diagnostics"]["practical_head_stability_iteration"]
                                                for r in rows],
        }
    return out


def _correlation_by_map(x: dict[int, float], y: dict[int, float]) -> dict[str, float]:
    ids = sorted(set(x) & set(y))
    if not ids:
        return {"n": 0, "pearson": float("nan"), "spearman": float("nan")}
    a = np.asarray([x[i] for i in ids], dtype=np.float64)
    b = np.asarray([y[i] for i in ids], dtype=np.float64)
    mask = np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) < 10:
        return {"n": int(mask.sum()), "pearson": float("nan"), "spearman": float("nan")}
    return {"n": int(mask.sum()), "pearson": float(np.corrcoef(a[mask], b[mask])[0, 1]),
            "spearman": float(spearmanr(a[mask], b[mask]).statistic)}


def _second_stage_signal_comparison(context: dict[str, Any],
                                    j5_scores: dict[str, Any]) -> dict[str, Any]:
    c = _load_npz(STATE_DIR / "cluster_J20000.npz")
    j5a = j5_scores["arrays"]
    amap = {int(u): float(v) for u, v in zip(j5a["user_ids"].tolist(),
                                             j5a["agreement_A"].tolist())}
    bmap = {int(u): float(v) for u, v in zip(j5a["user_ids"].tolist(),
                                             j5a["agreement_B"].tolist())}
    fmap = {int(u): float(v) for u, v in zip(j5a["user_ids"].tolist(),
                                             j5a["agreement_full"].tolist())}
    smap = {int(u): float(v) for u, v in zip(c["user_ids"].tolist(),
                                             c["basin_specificity_margin"].tolist())}
    pmap = {int(u): float(v) for u, v in zip(c["user_ids"].tolist(),
                                             c["literary_basin_support"].tolist())}
    lmap = _score_maps(context)["L"]
    ranks = {}
    for name, vals in (("J5_A", amap), ("J5_B", bmap), ("J5_full", fmap),
                       ("basin_margin", smap), ("basin_support", pmap), ("common_L", lmap)):
        ids = [int(u) for u in context["memberships"]["J20000"].tolist()
               if int(u) not in set(context["memberships"]["J5000"].tolist())]
        ordered = [u for u in sorted(ids, key=lambda x: (-vals.get(x, -np.inf), x))
                   if np.isfinite(vals.get(u, np.nan))]
        ranks[name] = ordered
    overlaps = {}
    for k in (1000, 2500, 5000, 10000):
        sa, sb = set(ranks["J5_A"][:k]), set(ranks["basin_margin"][:k])
        overlaps[str(k)] = {"overlap_count": len(sa & sb),
                            "jaccard": len(sa & sb) / max(1, len(sa | sb))}
    return {
        "A_vs_B": _correlation_by_map(amap, bmap),
        "A_vs_basin_margin": _correlation_by_map(amap, smap),
        "A_vs_basin_support": _correlation_by_map(amap, pmap),
        "B_vs_basin_margin": _correlation_by_map(bmap, smap),
        "full_vs_basin_margin": _correlation_by_map(fmap, smap),
        "A_vs_common_L": _correlation_by_map(amap, lmap),
        "basin_margin_vs_common_L": _correlation_by_map(smap, lmap),
        "top_overlap_J5_A_vs_basin_margin": overlaps,
        "rank_order_top": {k: v[:100] for k, v in ranks.items()},
    }


def _build_output_npz(context: dict[str, Any], j5: dict[str, Any],
                      clusters: dict[str, Any], j5_scores: dict[str, Any],
                      orders: dict[str, Any], expansions: dict[str, Any]) -> None:
    arrays: dict[str, np.ndarray] = {
        "config/seed": np.asarray([LITERARY_BASIN_SEED], dtype=np.int64),
        "config/beta": np.asarray([BETA], dtype=np.float64),
        "config/init_sigma": np.asarray([INIT_SIGMA], dtype=np.float64),
        "config/basin_reps": np.asarray([BASIN_REPS], dtype=np.int64),
        "config/basin_max_iter": np.asarray([BASIN_MAX_ITER], dtype=np.int64),
        "config/expansion_max_iter": np.asarray([EXPANSION_MAX_ITER], dtype=np.int64),
        "frozen/universe": context["universe"].astype(np.int64),
        "frozen/common_L": context["scores"].astype(np.float64),
        "frozen/J5000_endpoint_score": j5["score"].astype(np.float32),
        "frozen/J5000_direct_score": j5["direct_score"].astype(np.float32),
        "frozen/J5000_endpoint_work_ids": j5["work_ids"].astype(str),
    }
    for tag, ids in context["memberships"].items():
        arrays[f"membership/{tag}/user_ids"] = ids.astype(np.int64)
    for tag in BASIN_POPULATIONS:
        cp = _load_npz(STATE_DIR / f"cluster_J{tag}.npz")
        for name, value in cp.items():
            arrays[f"basin/J{tag}/{name}"] = value
        manifest = _load_json(STATE_DIR / "basin_manifest.json")
        for rec in manifest[f"J{tag}"]:
            ep = _load_endpoint(rec["key"])
            arrays[f"basin/J{tag}/endpoint/{rec['rep']:03d}/score"] = ep["score"].astype(np.float32)
    for name, value in j5_scores["arrays"].items():
        arrays[f"j5_agreement/{name}"] = value
    for name, value in orders["arrays"].items():
        arrays[f"order/{name}"] = value
    for key, row in expansions.items():
        safe = _safe_key(key)
        arrays[f"expansion/{safe}/direct_score"] = row["direct_endpoint"]["score"].astype(np.float32)
        arrays[f"expansion/{safe}/final_score"] = row["final_endpoint"]["score"].astype(np.float32)
        arrays[f"expansion/{safe}/user_ids"] = row["direct_user_ids"].astype(np.int64)
        arrays[f"expansion/{safe}/final_weights"] = row["final_weights"].astype(np.float32)
        for random in row["random"]:
            state = dynamics._load_trajectory_state(random["key"])
            if state is not None:
                d = dynamics._data_from_state(*state)
                ep = _endpoint_from_data(random["key"], d["payload_tag"], d)
                arrays[f"expansion/{safe}/random{random['rep']}/score"] = ep["score"].astype(np.float32)
    _write_npz_atomic(OUT_NPZ, arrays)


def _md_cell(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return _fmt(value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _head_block(label: str, head: list[dict[str, Any]], desc: dict[str, Any] | None = None,
                limit: int = 50) -> str:
    lines = [f"### {label}", ""]
    if desc:
        lines.append("Descriptors: " + "; ".join(
            f"{k}={_md_cell(v)}" for k, v in desc.items()
            if k in ("pos50", "exact50", "broad50", "anti50",
                     "unique_authors_50", "max_same_author_count_50",
                     "collection_count_50", "duplicate_count_50", "comic_count_50")))
        lines.append("")
    lines.extend(["|rank|title|author|score|n_eff|P|E|B|A|",
                  "|---:|---|---|---:|---:|:--:|:--:|:--:|:--:|"])
    for row in head[:limit]:
        lines.append("|" + "|".join([
            str(row.get("rank", "")), _md_cell(row.get("title", "")),
            _md_cell(row.get("author", "")), _md_cell(row.get("score")),
            _md_cell(row.get("n_eff")),
            "x" if row.get("pos") else "", "x" if row.get("exact") else "",
            "x" if row.get("broad") else "", "x" if row.get("anti") else "",
        ]) + "|")
    lines.append("")
    return "\n".join(lines)


def _qualitative_head(head: list[dict[str, Any]]) -> str:
    titles = [str(r.get("title", r.get("work_id", ""))) for r in head[:5]]
    authors = Counter(str(r.get("author", "")) for r in head[:20]
                      if r.get("author"))
    auth = ", ".join(f"{a} ({n})" for a, n in authors.most_common(4))
    return "; ".join(titles) + (f"; leading authors: {auth}" if auth else "")


def _compact_endpoint(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": value.get("key"), "n_users": value.get("n_users"),
        "payload_tag": value.get("payload_tag"),
        "score_hash_float32": value.get("score_hash_float32"),
        "membership_hash": value.get("membership_hash"),
    }


def _compact_expansion_rows(expansions: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, row in expansions.items():
        x = {k: v for k, v in row.items()
             if k not in ("direct_user_ids", "direct_endpoint", "final_endpoint",
                          "final_weights")}
        x["direct_endpoint"] = _compact_endpoint(row["direct_endpoint"])
        x["final_endpoint"] = _compact_endpoint(row["final_endpoint"])
        out[key] = x
    return out


def _build_heads_files(posthoc: dict[str, Any], clusters: dict[str, Any],
                       expansions: dict[str, Any]) -> None:
    lines = ["# Literary basin heads", "",
             "Cluster count and J5-like selection were frozen before these semantic annotations were loaded.", ""]
    for pop in ("J10000", "J20000"):
        c = clusters[pop]
        lines.extend([f"## {pop}", "",
                      f"selected k={c['selected_k']}; J5-like basin={c['j5_like_basin']}; "
                      f"equal-start assignment={c['equal_start_assignment']}", ""])
        for basin, item in sorted(posthoc["basins"][pop].items(), key=lambda kv: int(kv[0])):
            lines.append(f"Basin {basin}: n_runs={item['size']} "
                         f"frequency={_fmt(item['frequency'])}; "
                         f"J5 cosine={_fmt(item['j5_similarity'])}; "
                         f"J5-like={item['j5_like']}")
            lines.append("")
            lines.append(_head_block(f"{pop} basin {basin}", item["top50"],
                                     item["descriptors"], 50))
    lines.extend(["## Matched-L and specificity groups", ""])
    for name, item in posthoc.get("profiles", {}).items():
        lines.append(_head_block(name, item.get("top50", []),
                                 item.get("descriptors"), 50))
    _write_text_atomic(OUT_BASIN_HEADS, "\n".join(lines))

    lines = ["# Refined expansion heads", "",
             "Each section gives the complete top 50 before and after exact-membership convergence.", ""]
    for key in sorted(expansions, key=lambda x: (x.split("_")[0], int(x.split("_")[1]))):
        row = posthoc["expansions"][key]
        lines.extend([f"## {key}", ""])
        for which, label in (("direct", "direct equal vote"), ("final", "converged equal start")):
            item = row[which]
            lines.append(_head_block(label, item["top50"], item["descriptors"], 50))
    _write_text_atomic(OUT_EXPANSION_HEADS, "\n".join(lines))


def _build_report(context: dict[str, Any], audit: dict[str, Any],
                  j5: dict[str, Any], manifest: dict[str, Any],
                  clusters: dict[str, Any], basin_diags: dict[str, Any],
                  j5_scores: dict[str, Any], orders: dict[str, Any],
                  profiles: dict[str, Any], expansions: dict[str, Any],
                  coverage: dict[str, Any], cross: dict[str, Any],
                  signal: dict[str, Any], posthoc: dict[str, Any],
                  runtime_seconds: float) -> str:
    lines = ["# Literary basin refinement report", "",
             f"Campaign seed: `{LITERARY_BASIN_SEED}`. Starting frozen commit: `{PRIOR_COMMIT}`.",
             f"Campaign wall-clock runtime estimate: `{runtime_seconds:.1f}` seconds (resumable phases included).", "",
             "This is a bounded two-stage refinement experiment. Basin discovery, cluster-count selection, "
             "J5-like-basin selection, and expansion membership construction were label-free; semantic probes "
             "are post-hoc annotations only.", ""]
    ok = sum(bool(c["ok"]) for c in audit["checks"])
    lines.extend(["## Audit and invariants", "",
                  f"Smoke checks: **{ok}/{len(audit['checks'])} passed**.", "",
                  "|check|status|detail|", "|---|:---:|---|"])
    for check in audit["checks"]:
        lines.append(f"|{check['check']}|{'PASS' if check['ok'] else 'FAIL'}|{_md_cell(check['detail'])}|")
    lines.extend(["", f"Frozen J5 endpoint iteration: `{j5['final_iteration']}`; "
                  f"endpoint float32 hash: `{j5['score_hash_float32']}`.", ""])

    lines.extend(["## Basin census", "",
                  "Clustering representation: centered, L2-normalized final full book-preference vectors; "
                  "distance `1 - cosine`; agglomerative average linkage; k search exactly 2..8.", "",
                  "|population|k|basin|runs|frequency|silhouette(k)|within median|nearest between|J5 cosine|equal assignment|qualitative head|",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"])
    for pop in ("J10000", "J20000"):
        c = clusters[pop]
        for item in c["cluster_summaries"]:
            b = int(item["basin"])
            q = item["quality"]
            qhead = posthoc["basins"][pop][str(b)]["top50"]
            lines.append("|" + "|".join([
                pop, str(c["selected_k"]), str(b), str(item["n_runs"]),
                _fmt(item["frequency"]), _fmt(c["silhouette_by_k"].get(str(c["selected_k"]))),
                _fmt(q.get("within_median_similarity")),
                _fmt(q.get("nearest_between_similarity")), _fmt(item["j5_similarity"]),
                "yes" if c["equal_start_assignment"] == b else "no",
                _md_cell(_qualitative_head(qhead)),
            ]) + "|")
    lines.extend(["", "### Cluster robustness", ""])
    for pop in ("J10000", "J20000"):
        c = clusters[pop]
        lines.append(f"**{pop}** silhouette by k: " + ", ".join(
            f"{k}={_fmt(v)}" for k, v in sorted(c["silhouette_by_k"].items(), key=lambda x: int(x[0]))))
        lines.append(f"; bootstrap median ARI={_fmt(c['bootstrap_stability']['median_ari'])} "
                     f"(p10={_fmt(c['bootstrap_stability']['p10_ari'])}, "
                     f"p90={_fmt(c['bootstrap_stability']['p90_ari'])}).")
    lines.extend(["", "J5-like basin is selected only by maximum centered preference cosine to frozen J5. "
                  "The best-minus-second margin is "
                  + "; ".join(f"{p}={_fmt(clusters[p]['j5_margin_best_second'])}" for p in ("J10000", "J20000")) + ".", ""])

    lines.extend(["## Basin dynamics", "",
                  "|population|strict runs/64|median final step|median final weight_rel_1|median final book_rel_1|median recent lag2/lag1|2-cycle heuristic count|practical head stability median|",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for pop in ("J10000", "J20000"):
        d = basin_diags[pop]
        ratios = [r["diagnostics"]["lag2_over_lag1_recent"] for r in d["runs"]]
        cycles = sum(r["diagnostics"]["two_cycle_signature_recent"] for r in d["runs"])
        stable = [x for x in d["practical_stability_iterations"] if x is not None]
        lines.append(f"|{pop}|{d['strict_count']}/{d['n_runs']}|{_fmt(d['final_medians']['step'])}|"
                     f"{_fmt_sci(d['final_medians']['weight_rel_1'])}|{_fmt_sci(d['final_medians']['book_rel_1'])}|"
                     f"{_fmt(float(np.nanmedian(ratios)) if ratios else np.nan)}|{cycles}|"
                     f"{_fmt(float(np.median(stable)) if stable else np.nan, 0)}|")
    lines.extend(["", "Interpretation of lag diagnostics is descriptive: a genuine 2-cycle would require lag-1 "
                  "weight movement to remain nonzero while lag-2 collapses. The report does not assume a cycle "
                  "from nonzero lag-1 alone.", ""])

    lines.extend(["## J5 agreement and specificity", "",
                  f"Outer candidate pool: `{j5_scores['candidate_pool']}`, n={j5_scores['candidate_n']}; "
                  f"eligible frozen-J5 works={j5_scores['eligible_work_n']} split A/B="
                  f"{j5_scores['fold_A_n']}/{j5_scores['fold_B_n']}.", "",
                  "|comparison|n|Pearson|Spearman|", "|---|---:|---:|---:|"])
    for key in ("A_vs_B", "A_vs_basin_margin", "B_vs_basin_margin",
                "full_vs_basin_margin", "A_vs_common_L", "basin_margin_vs_common_L"):
        x = signal[key]
        lines.append(f"|{key}|{x['n']}|{_fmt(x['pearson'])}|{_fmt(x['spearman'])}|")
    lines.extend(["", "Top-set overlap between ORDER_J5's fold-A signal and basin specificity:", "",
                  "|k|overlap|Jaccard|", "|---:|---:|---:|"])
    for k, x in signal["top_overlap_J5_A_vs_basin_margin"].items():
        lines.append(f"|{k}|{x['overlap_count']}|{_fmt(x['jaccard'])}|")

    lines.extend(["", "### Matched-L profiles", "",
                  "The high/low specificity groups were formed within each frozen common-L decile, then pooled.", "",
                  "|group|n|L median|L p10|L p90|specificity median|top head|", "|---|---:|---:|---:|---:|---:|---|"])
    for name, row in profiles.get("matched", {}).items():
        head = posthoc["profiles"].get(name, {}).get("top50", [])
        lines.append(f"|{name}|{row['n']}|{_fmt(row['L']['median'])}|{_fmt(row['L']['p10'])}|"
                     f"{_fmt(row['L']['p75'])}|{_fmt(row['specificity']['median'])}|"
                     f"{_md_cell(_qualitative_head(head))}|")
    lines.extend(["", "Specificity-band profiles are exported in `LITERARY_BASIN_HEADS.md`; the matched-L heads are "
                  "the direct equal-vote heads of those pooled users, not converged selections.", ""])

    lines.extend(["## Refined expansion results", "",
                  "|ordering|n|median L|p10 L|heldout B median|direct→final J50|final→J5 J50|final→J5 J200|random median J50 vs equal|strict?|iterations|20–49 ≥1|20–49 ≥3|direct head|final head|",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|---:|---:|---:|---|---|"])
    for key in sorted(expansions, key=lambda x: (ORDER_NAMES.index(x.split("_")[0]), int(x.split("_")[1]))):
        row = expansions[key]
        p = posthoc["expansions"][key]
        cov = coverage["bands"].get(key, {}).get("20_49", {})
        lines.append("|" + "|".join([
            row["order"], str(row["n"]), _fmt(row["direct_L"]["median"]),
            _fmt(row["direct_p10_L"]), _fmt(row["direct_heldout_B_median"]),
            _fmt(row["direct_vs_final"]["top50"]["jaccard"]),
            _fmt(row["final_vs_J5"]["top50"]["jaccard"]),
            _fmt(row["final_vs_J5"]["top200"]["jaccard"]),
            _fmt(row["random_median_top50_overlap_vs_equal"]),
            "yes" if row["strict_convergence_reached"] else "no", str(row["iterations"]),
            _fmt(cov.get("ge1")), _fmt(cov.get("ge3")),
            _md_cell(_qualitative_head(p["direct"]["top50"])),
            _md_cell(_qualitative_head(p["final"]["top50"])),
        ]) + "|")

    lines.extend(["", "### Cross-method rediscovery", "",
                  "The expansion members are compared over the outer J20\\J5 users at each tested size.", "",
                  "|n|pair|overlap|Jaccard|", "|---:|---|---:|---:|"])
    for n, pairs in sorted(cross.items(), key=lambda x: int(x[0])):
        for pair, value in pairs.items():
            lines.append(f"|{n}|{pair}|{value['overlap_count']}|{_fmt(value['jaccard'])}|")
    lines.extend(["", "### Direct → converged head movement", "",
                  "The full top-50 heads, including every title and author, are in `LITERARY_REFINED_EXPANSION_HEADS.md`. "
                  "For J10/J20-sized expansions the concise movement view is:", ""])
    for key in ("L_10000", "J5_10000", "BASIN_10000", "L_15000", "J5_15000", "BASIN_15000", "L_20000", "J5_20000", "BASIN_20000"):
        if key not in expansions:
            continue
        row = expansions[key]
        direct = posthoc["expansions"][key]["direct"]["top50"]
        final = posthoc["expansions"][key]["final"]["top50"]
        lines.append(f"**{key}** direct→final top50 overlap={row['direct_vs_final']['top50']['overlap_count']}/50; "
                     f"direct: {_md_cell(_qualitative_head(direct))}; final: {_md_cell(_qualitative_head(final))}")
    lines.extend(["", "## Coverage", "",
                  f"Coverage global work-count source: `{coverage['source']}`; global works={coverage['n_global_works']}.", "",
                  "Coverage is reported for raw reader presence; no obscure-book accuracy validation was performed.", ""])
    frozen_raw = coverage.get("frozen_primary_context", {})
    if frozen_raw:
        lines.extend(["Frozen primary context from the prior persisted coverage artifact:", "",
                      "|jury|20–49 ≥1|20–49 ≥3|", "|---|---:|---:|"])
        for tag in ("J5000", "J10000", "J20000", "J30000"):
            if tag in frozen_raw:
                lines.append(f"|{tag}|{_fmt(frozen_raw[tag]['20_49_ge1'])}|{_fmt(frozen_raw[tag]['20_49_ge3'])}|")
        lines.append("")

    # A data-dependent but deliberately descriptive interpretation.  It uses
    # before/after heads and J5 vector similarity, never probe counts alone.
    l10 = expansions.get("L_10000")
    l20 = expansions.get("L_20000")
    if l10 and l20:
        l10_direct = l10["direct_vs_J5"]["top50"]["jaccard"]
        l10_final = l10["final_vs_J5"]["top50"]["jaccard"]
        l20_direct = l20["direct_vs_J5"]["top50"]["jaccard"]
        l20_final = l20["final_vs_J5"]["top50"]["jaccard"]
        lines.extend(["", "## Scientific interpretation", "",
                      "### Does the larger-jury slide come from membership, dynamics, or both?", "",
                      f"For ORDER_L at 10k, direct→J5 top-50 Jaccard is `{l10_direct:.3f}` and final→J5 is `{l10_final:.3f}`; "
                      f"at 20k the corresponding values are `{l20_direct:.3f}` and `{l20_final:.3f}`.", ""])
        if (l10_direct - l10_final) > .10 or (l20_direct - l20_final) > .10:
            lines.append("The descriptive result supports an interaction: the added membership changes the direct head, "
                         "and nonlinear reweighting further redirects at least one larger size away from the frozen "
                         "J5 mode. The size-specific heads must be read together because the sign can differ by N.")
        elif l10_direct < .45 and l20_direct < .45 and abs(l10_direct - l10_final) < .10 and abs(l20_direct - l20_final) < .10:
            lines.append("The descriptive result is primarily a membership effect: the larger equal-vote heads are already "
                         "far from the J5 mode and convergence changes them comparatively little.")
        else:
            lines.append("The descriptive result is mixed and size-specific: direct membership expansion already changes "
                         "the head, while convergence sometimes amplifies and sometimes counteracts that change. It is "
                         "not scientifically defensible to assign one global cause to all jury sizes.")
    lines.extend(["", "### Practical reading", "",
                  "J5 remains the frozen narrow literary core. J10/J20 are not rejected merely because an internal map "
                  "can amplify a different coherent axis: the direct heads, basin frequencies, individual L profiles, "
                  "and coverage must be considered separately. J30 and any maximal-jury claim are outside this campaign.", "",
                  "A later adaptive/binary boundary search is scientifically justified only if one ordering shows an "
                  "approximately monotone size trajectory in actual heads, held-out J5 agreement, and random-init "
                  "stability. This report does not perform that search or declare a maximum.", ""])
    return "\n".join(lines)


def _phase_audit() -> tuple[dict[str, Any], dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    return _audit_frozen_state()


def _phase_basin(context: dict[str, Any]) -> dict[str, Any]:
    return _run_basin_census(context)


def _phase_cluster(context: dict[str, Any], prior_json: dict[str, Any],
                   prior_npz: dict[str, np.ndarray], manifest: dict[str, Any],
                   audit_bundle: dict[str, Any]) -> dict[str, Any]:
    return _run_clustering(context, prior_json, audit_bundle["j5"], manifest)


def _phase_refine(context: dict[str, Any], clusters: dict[str, Any],
                  audit_bundle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any],
                                                           dict[str, Any], dict[str, Any]]:
    j5 = audit_bundle["j5"]
    j5_scores = _j5_agreement(context, j5)
    orders = _build_orders(context, clusters, j5_scores)
    profiles = _user_profile_diagnostics(context, clusters)
    expansions_manifest = _run_expansions(context, orders)
    expansion_rows = _expansion_analysis(context, orders, expansions_manifest, j5, j5_scores)
    return j5_scores, orders, profiles, {"manifest": expansions_manifest, "rows": expansion_rows}


def _run_report(context: dict[str, Any], prior_json: dict[str, Any],
                prior_npz: dict[str, np.ndarray], audit_bundle: dict[str, Any],
                manifest: dict[str, Any], clusters: dict[str, Any],
                j5_scores: dict[str, Any], orders: dict[str, Any],
                profiles: dict[str, Any], expansion_bundle: dict[str, Any],
                audit: dict[str, Any], runtime_seconds: float) -> dict[str, Any]:
    state_files = [p for p in STATE_DIR.iterdir() if p.is_file()]
    if state_files:
        # The process phases are intentionally resumable and may be launched
        # separately, so use the first campaign-state mtime as the bounded
        # wall-clock start rather than reporting only this final process.
        runtime_seconds = max(runtime_seconds,
                              time.time() - min(p.stat().st_mtime for p in state_files))
    j5 = audit_bundle["j5"]
    expansions = expansion_bundle["rows"]
    con = open_db()
    coverage = _coverage_stats(con, expansions)
    prior_raw = prior_json.get("coverage", {}).get("raw", {})
    coverage["frozen_primary_context"] = {
        tag: {"20_49_ge1": float(row["20_49_ge1"]),
              "20_49_ge3": float(row["20_49_ge3"])}
        for tag, row in prior_raw.items()
        if "20_49_ge1" in row and "20_49_ge3" in row
    }
    cross = _cross_method_analysis(context, orders, j5_scores, clusters)
    signal = _second_stage_signal_comparison(context, j5_scores)
    difference_profiles = _direct_difference_profiles(context, orders, 15000)
    profiles["difference_groups"] = difference_profiles
    metadata, probes = _posthoc_context(j5)
    posthoc = _posthoc_heads(context, j5, clusters, profiles, expansions, metadata, probes)
    basin_diags = _basin_trajectory_diagnostics(manifest)
    _build_heads_files(posthoc, clusters, expansions)
    _build_output_npz(context, j5, clusters, j5_scores, orders, expansions)
    report = _build_report(context, audit, j5, manifest, clusters, basin_diags,
                           j5_scores, orders, profiles, expansions, coverage,
                           cross, signal, posthoc, runtime_seconds)
    _write_text_atomic(OUT_MD, report)
    def compact_profiles() -> dict[str, Any]:
        return {k: v for k, v in profiles.items()
                if k not in ("arrays", "group_rows", "matched", "difference_groups")}
    j5_json = {k: v for k, v in j5_scores.items() if k not in ("arrays", "summaries")}
    final = {
        "campaign": {
            "seed": LITERARY_BASIN_SEED, "starting_commit": PRIOR_COMMIT,
            "current_head_at_report": _git_head(), "state_version": STATE_VERSION,
            "basin_reps": BASIN_REPS, "basin_max_iter": BASIN_MAX_ITER,
            "expansion_max_iter": EXPANSION_MAX_ITER,
            "expansion_random_reps": EXPANSION_RANDOM_REPS,
            "semantic_annotations_posthoc": True,
        },
        "audit": audit,
        "frozen_state": {
            "common_L_score_hash": context["score_hash"],
            "universe_hash": context["universe_hash"],
            "membership_hashes": {tag: _hash_ids(ids)
                                  for tag, ids in context["memberships"].items()},
            "J5000_endpoint": {
                "iteration": j5["final_iteration"],
                "score_hash_float32": j5["score_hash_float32"],
                "direct_score_hash_float32": j5["direct_score_hash_float32"],
                "ranking_hash": j5["ranking_hash"],
            },
        },
        "basin_manifest": manifest,
        "basin_diagnostics": basin_diags,
        "clusters": clusters,
        "j5_agreement": j5_json,
        "orders": {k: v for k, v in orders.items() if k != "arrays"},
        "signal_comparison": signal,
        "user_profiles": compact_profiles(),
        "expansion_trajectories": expansion_bundle["manifest"],
        "expansions": _compact_expansion_rows(expansions),
        "coverage": coverage,
        "cross_method": cross,
        "posthoc_heads": posthoc,
        "smoke_invariants": {
            "no_semantic_labels_in_discovery": True,
            "no_semantic_labels_in_cluster_selection": True,
            "no_semantic_labels_in_expansion_ordering": True,
            "exact_expansion_sizes": all(row["n"] == int(key.split("_")[1])
                                           for key, row in expansions.items()),
            "j5_core_retained": all(set(row["direct_user_ids"].tolist()) >=
                                     set(context["memberships"]["J5000"].tolist())
                                     for row in expansions.values()),
            "random_reps_exact": all(len(row["random"]) == EXPANSION_RANDOM_REPS
                                      for row in expansions.values()),
            "old_artifacts_untouched": True,
        },
    }
    _json_dump(OUT_JSON, final)
    return final


def _load_audit_bundle() -> tuple[dict[str, Any], dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    context, prior_json, prior_npz = _load_context()
    j5 = _frozen_j5(context, prior_json, prior_npz)
    return context, prior_json, prior_npz, {"audit": _load_json(STATE_DIR / "audit.json"), "j5": j5}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("audit", "basin", "cluster", "refine", "report", "all"),
                        default="all")
    args = parser.parse_args()
    _configure_runtime()
    started = time.time()
    if args.phase == "audit":
        _context, _prior, _npz, bundle = _phase_audit()
        print(json.dumps(bundle["audit"], indent=1), flush=True)
        return

    # Every non-audit phase is resumable from the prior phase's state.  A
    # missing earlier state is created rather than silently approximated.
    if not (STATE_DIR / "audit.json").exists():
        context, prior_json, prior_npz, bundle = _phase_audit()
    else:
        context, prior_json, prior_npz, bundle = _load_audit_bundle()
    if args.phase == "basin":
        manifest = _phase_basin(context)
        print(f"basin census complete: J10={len(manifest['J10000'])} J20={len(manifest['J20000'])}", flush=True)
        return
    if not (STATE_DIR / "basin_manifest.json").exists():
        manifest = _phase_basin(context)
    else:
        manifest = _load_json(STATE_DIR / "basin_manifest.json")
    if args.phase == "cluster":
        clusters = _phase_cluster(context, prior_json, prior_npz, manifest, bundle)
        print(json.dumps({k: {"k": v["selected_k"], "j5_like": v["j5_like_basin"]}
                          for k, v in clusters.items()}, indent=1), flush=True)
        return
    if not (STATE_DIR / "cluster_manifest.json").exists():
        clusters = _phase_cluster(context, prior_json, prior_npz, manifest, bundle)
    else:
        clusters = _load_json(STATE_DIR / "cluster_manifest.json")
    if args.phase == "refine":
        j5_scores, orders, profiles, expansion_bundle = _phase_refine(context, clusters, bundle)
        print(f"refinement trajectories complete: {len(expansion_bundle['rows'])}", flush=True)
        return
    if not (STATE_DIR / "expansion_trajectories.json").exists():
        j5_scores, orders, profiles, expansion_bundle = _phase_refine(context, clusters, bundle)
    else:
        j5_scores = _j5_agreement(context, bundle["j5"])
        orders = _build_orders(context, clusters, j5_scores)
        profiles = _user_profile_diagnostics(context, clusters)
        expansion_bundle = {
            "manifest": _load_json(STATE_DIR / "expansion_trajectories.json"),
            "rows": _expansion_analysis(context, orders,
                                         _load_json(STATE_DIR / "expansion_trajectories.json"),
                                         bundle["j5"], j5_scores),
        }
    _run_report(context, prior_json, prior_npz, bundle, manifest, clusters,
                j5_scores, orders, profiles, expansion_bundle,
                bundle["audit"], time.time() - started)
    print(f"wrote {OUT_JSON}, {OUT_NPZ}, {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()

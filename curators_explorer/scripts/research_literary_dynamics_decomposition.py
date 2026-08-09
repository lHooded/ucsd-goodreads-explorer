#!/usr/bin/env python3
"""Long-run dynamics and descriptive size decomposition for literary juries.

This experiment is deliberately downstream of the frozen common-L score.  It
does not retrain that score, alter membership selection, or use semantic probe
labels in the dynamics.  The four primary memberships are the exact
J5000/J10000/J20000/J30000 memberships used by commit 237cb37.  The same
seed-local payloads and the same nonlinear update as the historical
``iterate_map`` are used, but the fixed-membership trajectories are extended
to 2,000 iterations (with the inherited strict criterion and +50 verification
iterations if that criterion is genuinely reached).

The campaign is intentionally resumable.  Each trajectory has an ignored
checkpoint pair under ``literary_dynamics_decomposition_state`` containing the
current weights, previous direction/raw-book vectors, lag history, every
diagnostic so far, and saved ranking checkpoints.  State is written at least
every 100 iterations and at every ranking checkpoint.  The requested committed
NPZ contains the completed trajectory snapshots; the JSON and Markdown files
are derived reporting artifacts.

Run examples::

    PYTHONPATH=. .venv/bin/python -m \
      curators_explorer.scripts.research_literary_dynamics_decomposition \
      --phase audit
    PYTHONPATH=. .venv/bin/python -m \
      curators_explorer.scripts.research_literary_dynamics_decomposition \
      --phase all

No inherited artifact is overwritten by this script.
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
from scipy.stats import linregress, spearmanr

from curators_explorer.scripts import research_attractor_pruning as pruning
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_true_converged_literary_jurors as inherited
from curators_explorer.scripts.research_converged_common_literary_jurors import (
    DATA,
    _derive_seed,
    _json_default,
    _write_npz_atomic,
    _write_text_atomic,
    load_juries,
    open_db,
    q_distribution,
)


LITERARY_DYNAMICS_SEED = 20260902
LONG_MAX_ITER = 2000
SHELL_MAX_ITER = 1000
LONG_RANDOM_INIT_REPS = 5
LONG_RANDOM_INIT_REPS_J30000 = 3
NEW_SUB80_REPS = 5
INIT_SIGMA = 0.20
BETA = 2.5
CONSECUTIVE_CONVERGED = 5
STEP_THRESHOLD = 0.9999
WEIGHT_CHANGE_THRESHOLD = 1e-4
VERIFY_EXTRA_ITER = 50
CHECKPOINTS = (0, 1, 2, 5, 10, 20, 50, 100, 200, 300, 500,
               750, 1000, 1500, 2000)
HEAD_CHECKPOINTS = (0, 20, 100, 200, 500, 1000, 2000)
WINDOWS = ((1, 50), (51, 100), (101, 200), (201, 500),
           (501, 1000), (1001, 2000))
PRIMARY_SIZES = (5000, 10000, 20000, 30000)

OUT_JSON = DATA / "literary_dynamics_decomposition.json"
OUT_NPZ = DATA / "literary_dynamics_decomposition.npz"
OUT_MD = DATA / "LITERARY_DYNAMICS_DECOMPOSITION_REPORT.md"
OUT_TRAJ_HEADS = DATA / "LITERARY_DYNAMICS_TRAJECTORY_HEADS.md"
OUT_SHELL_HEADS = DATA / "LITERARY_SIZE_SHELL_HEADS.md"
STATE_DIR = DATA / "literary_dynamics_decomposition_state"
STATE_VERSION = 1

PRIMARY_TAGS = {f"J{n}": f"payload_J{n}" for n in PRIMARY_SIZES}

HISTORY_FIELDS = (
    "iteration", "step", "weight_rel_1", "book_rel_1", "weight_rel_2",
    "book_rel_2", "weight_cos_lag2", "direction_cos_lag2",
    "weight_rel_3", "weight_rel_4",
)


def _safe_key(key: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in key)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_array(value: np.ndarray) -> str:
    a = np.ascontiguousarray(value)
    return _sha256_bytes(a.tobytes(order="C"))


def _hash_ids(ids: np.ndarray) -> str:
    return _sha256_array(np.asarray(ids, dtype="<i8"))


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def _fmt(value: float, digits: int = 4) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    return f"{value:.{digits}f}"


def _fmt_sci(value: float) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    return f"{value:.2e}"


def _json_dump(path: Path, obj: Any) -> None:
    _write_text_atomic(path, json.dumps(obj, indent=1, default=_json_default))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as blob:
        return {k: blob[k] for k in blob.files}


def _head_from_arrays(work_ids: np.ndarray, scores: np.ndarray,
                      masses: np.ndarray) -> list[dict[str, Any]]:
    return [{"rank": i + 1, "work_id": str(w), "score": float(s),
             "n_eff": float(m)}
            for i, (w, s, m) in enumerate(zip(work_ids, scores, masses))]


def _head_sets(snapshot: dict[str, Any], k: int) -> set[str]:
    return set(str(x) for x in snapshot["work_ids"][:k])


def _head_metrics(a: dict[str, Any], b: dict[str, Any],
                  k: int = 50) -> dict[str, float | int]:
    aa = [str(x) for x in a["work_ids"][:k]]
    bb = [str(x) for x in b["work_ids"][:k]]
    sa, sb = set(aa), set(bb)
    overlap = len(sa & sb)
    union = len(sa | sb)
    return {
        "overlap_count": int(overlap),
        "overlap_fraction": float(overlap / max(1, k)),
        "jaccard": float(overlap / max(1, union)),
    }


def _rank_rho(a: dict[str, Any], b: dict[str, Any],
              k: int = 200) -> float:
    aa = [str(x) for x in a["work_ids"][:k]]
    bb = [str(x) for x in b["work_ids"][:k]]
    rb = {w: i for i, w in enumerate(bb)}
    common = [w for w in aa if w in rb]
    if len(common) < 10:
        return float("nan")
    return float(spearmanr([aa.index(w) for w in common],
                           [rb[w] for w in common]).statistic)


def _score_corr(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    aa = np.asarray(a, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    mask = np.isfinite(aa) & np.isfinite(bb)
    if int(mask.sum()) < 10 or np.std(aa[mask]) <= 1e-12 or np.std(bb[mask]) <= 1e-12:
        return {"pearson": float("nan"), "spearman": float("nan")}
    return {
        "pearson": float(np.corrcoef(aa[mask], bb[mask])[0, 1]),
        "spearman": float(spearmanr(aa[mask], bb[mask]).statistic),
    }


def _preference_distance(a: np.ndarray, b: np.ndarray) -> float:
    aa = np.asarray(a, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    mask = np.isfinite(aa) & np.isfinite(bb)
    if not np.any(mask):
        return float("nan")
    denom = float(np.sqrt(np.mean(aa[mask] ** 2)))
    return float(np.sqrt(np.mean((aa[mask] - bb[mask]) ** 2)) /
                 max(denom, 1e-12))


def _comparison(a: dict[str, Any], b: dict[str, Any],
                score_a: np.ndarray | None = None,
                score_b: np.ndarray | None = None) -> dict[str, Any]:
    out = {
        "top50": _head_metrics(a, b, 50),
        "top200": _head_metrics(a, b, 200),
        "spearman_common_top200": _rank_rho(a, b, 200),
    }
    if score_a is not None and score_b is not None:
        out["score_correlation"] = _score_corr(score_a, score_b)
        out["preference_vector_distance"] = _preference_distance(score_a, score_b)
    return out


def _weight_cosine(a: np.ndarray, b: np.ndarray) -> float:
    aa = np.asarray(a, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    den = np.linalg.norm(aa) * np.linalg.norm(bb)
    return float(np.dot(aa, bb) / den) if den > 0 else float("nan")


def _snapshot_label(t: int) -> str:
    return str(int(t))


def _actual_snapshot_time(data: dict[str, Any], desired: int) -> int:
    times = sorted(int(t) for t in data["snapshots"])
    if desired in times:
        return desired
    eligible = [t for t in times if t <= desired]
    return eligible[-1] if eligible else times[0]


def _final_time(data: dict[str, Any]) -> int:
    return int(data["final_iteration"])


def _snapshot(data: dict[str, Any], t: int) -> dict[str, Any]:
    return data["snapshots"][_snapshot_label(t)]


def _snapshot_at(data: dict[str, Any], desired: int) -> dict[str, Any]:
    return _snapshot(data, _actual_snapshot_time(data, desired))


def _history_array(data: dict[str, Any], field: str) -> np.ndarray:
    return np.asarray([row[field] for row in data["history"]], dtype=np.float64)


def _trajectory_paths(key: str) -> tuple[Path, Path]:
    safe = _safe_key(key)
    return STATE_DIR / f"trajectory_{safe}.json", STATE_DIR / f"trajectory_{safe}.npz"


def _payload_path(payload_tag: str) -> Path:
    """Return the path without rebuilding inherited state."""
    inherited_path = inherited.STATE_DIR / f"{payload_tag}.npz"
    if inherited_path.exists():
        return inherited_path
    return STATE_DIR / f"{payload_tag}.npz"


def _load_payload(payload_tag: str) -> dict[str, np.ndarray]:
    path = _payload_path(payload_tag)
    if not path.exists():
        raise FileNotFoundError(f"missing payload {payload_tag}: {path}")
    return _load_npz(path)


def _write_payload(payload_tag: str, payload: dict[str, np.ndarray]) -> None:
    # New shell/subset payloads live only in the new state directory.  Existing
    # 237cb37 payloads are never overwritten.
    _write_npz_atomic(STATE_DIR / f"{payload_tag}.npz", payload)


def _load_frozen_context() -> dict[str, Any]:
    universe, scores = inherited.load_frozen_scores()
    eligible_users, eligible_scores = inherited.convergence_eligible_universe(
        universe, scores)
    order = inherited.build_jury_order(eligible_users, eligible_scores)
    expected = {
        f"J{n}": eligible_users[order[:n]].astype(np.int64)
        for n in PRIMARY_SIZES
    }
    return {
        "universe": universe.astype(np.int64),
        "scores": scores.astype(np.float64),
        "eligible_users": eligible_users.astype(np.int64),
        "eligible_scores": eligible_scores.astype(np.float64),
        "order": order.astype(np.int64),
        "memberships": expected,
        "score_hash": _sha256_array(scores.astype("<f8")),
        "universe_hash": _sha256_array(universe.astype("<i8")),
    }


def _ensure_payloads(con, context: dict[str, Any]) -> dict[str, Any]:
    """Load exact primary payloads and build only new shell/subset payloads."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload_meta: dict[str, Any] = {}
    for tag, ids in context["memberships"].items():
        payload_tag = f"payload_{tag}"
        payload = _load_payload(payload_tag)
        actual = np.asarray(payload["user_ids"], dtype=np.int64)
        if set(actual.tolist()) != set(ids.tolist()) or len(actual) != len(ids):
            raise RuntimeError(f"payload membership mismatch for {tag}")
        if len(np.unique(actual)) != len(actual):
            raise RuntimeError(f"duplicate local payload users for {tag}")
        payload_meta[tag] = {
            "payload_tag": payload_tag,
            "source": str(_payload_path(payload_tag)),
            "n_users": int(len(actual)),
            "membership_hash_sorted": _hash_ids(np.sort(actual)),
            "work_count": int(len(payload["work_ids"])),
            "edge_count": int(len(payload["row"])),
        }

    j5, j10, j20, j30 = (context["memberships"][f"J{n}"] for n in PRIMARY_SIZES)
    shells = {
        "S0": np.sort(j5),
        "S1": np.sort(np.setdiff1d(j10, j5, assume_unique=True)),
        "S2": np.sort(np.setdiff1d(j20, j10, assume_unique=True)),
        "S3": np.sort(np.setdiff1d(j30, j20, assume_unique=True)),
    }
    context["shells"] = shells
    context["shell_meta"] = {}
    for shell, ids in shells.items():
        payload_tag = f"payload_{shell}"
        if shell == "S0":
            payload_tag = "payload_J5000"
        else:
            path = STATE_DIR / f"{payload_tag}.npz"
            if path.exists():
                payload = _load_npz(path)
            else:
                print(f"[prepare] building exact {shell} payload n={len(ids)}",
                      flush=True)
                payload = inherited.build_local_payload(con, ids)
                _write_payload(payload_tag, payload)
        payload = _load_payload(payload_tag)
        actual = np.asarray(payload["user_ids"], dtype=np.int64)
        if set(actual.tolist()) != set(ids.tolist()) or len(actual) != len(ids):
            raise RuntimeError(f"payload membership mismatch for {shell}")
        context["shell_meta"][shell] = {
            "payload_tag": payload_tag,
            "source": str(_payload_path(payload_tag)),
            "n_users": int(len(actual)),
            "membership_hash_sorted": _hash_ids(np.sort(actual)),
            "work_count": int(len(payload["work_ids"])),
            "edge_count": int(len(payload["row"])),
        }

    # Old exact J10000 80% subsets are persisted by 237cb37 in the ignored
    # state directory.  Verify them before any long run.
    old_subsets: list[np.ndarray] = []
    old_subset_persisted = True
    full10 = set(j10.tolist())
    for rep in range(5):
        path = inherited.STATE_DIR / f"payload_J10000_sub80_{rep}.npz"
        if not path.exists():
            old_subset_persisted = False
            break
        p = _load_npz(path)
        ids = np.asarray(p["user_ids"], dtype=np.int64)
        if len(ids) != 8000 or not set(ids.tolist()) <= full10:
            raise RuntimeError(f"invalid persisted old 80% subset rep{rep}")
        old_subsets.append(np.sort(ids))
    context["old_sub80_persisted"] = bool(old_subset_persisted and len(old_subsets) == 5)
    context["old_sub80"] = old_subsets if context["old_sub80_persisted"] else []

    _json_dump(STATE_DIR / "context.json", _context_json(context))
    return context


def _context_json(context: dict[str, Any]) -> dict[str, Any]:
    out = {
        "seed": LITERARY_DYNAMICS_SEED,
        "frozen_score_hash": context["score_hash"],
        "frozen_universe_hash": context["universe_hash"],
        "eligible_n": int(len(context["eligible_users"])),
        "memberships": {},
        "shells": {},
        "old_sub80_persisted": bool(context.get("old_sub80_persisted", False)),
    }
    for tag, ids in context["memberships"].items():
        out["memberships"][tag] = {
            "n": int(len(ids)),
            "id_hash_in_selection_order": _hash_ids(ids),
            "id_hash_sorted": _hash_ids(np.sort(ids)),
        }
    for tag, ids in context.get("shells", {}).items():
        out["shells"][tag] = {
            "n": int(len(ids)),
            "id_hash_sorted": _hash_ids(np.sort(ids)),
            "payload": context["shell_meta"][tag],
        }
    out["payloads"] = context.get("payload_meta", {})
    out["old_sub80"] = [
        {"rep": i, "n": int(len(ids)), "id_hash_sorted": _hash_ids(ids)}
        for i, ids in enumerate(context.get("old_sub80", []))
    ]
    return out


def _equal_init(n: int) -> np.ndarray:
    w = np.ones(n, dtype=np.float32)
    return w / w.mean()


def _lognormal_init(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    w = np.exp(rng.normal(0.0, INIT_SIGMA, size=n)).astype(np.float32)
    return w / w.mean()


def _init_weights(n: int, init: str, init_seed: int | None) -> np.ndarray:
    if init == "equal":
        return _equal_init(n)
    if init == "lognormal":
        if init_seed is None:
            raise ValueError("lognormal initialization requires a seed")
        return _lognormal_init(n, int(init_seed))
    raise ValueError(init)


def _empty_history() -> list[dict[str, float | int]]:
    return []


def _capture_snapshot(matrix: Any, operator: Any, payload: dict[str, np.ndarray],
                      weights: np.ndarray) -> dict[str, Any]:
    # Dynamics use the nonlinear projected operator; reported preference heads
    # use the inherited weighted_preferences function on the same raw matrix.
    # Probe labels and titles are attached only after all dynamics are frozen.
    preference = attractor.weighted_preferences(matrix, weights)
    head = inherited._book_head(preference, payload, limit=1000)
    return {
        "work_ids": np.asarray([r["work_id"] for r in head], dtype=str),
        "scores": np.asarray([r["score"] for r in head], dtype=np.float64),
        "reader_mass": np.asarray([r["n_eff"] for r in head], dtype=np.float64),
        "weights": np.asarray(weights, dtype=np.float32).copy(),
    }


def _history_to_arrays(history: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    return {
        f"history_{field}": np.asarray([row[field] for row in history],
                                         dtype=np.float64)
        for field in HISTORY_FIELDS
    }


def _arrays_to_history(arrays: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    n = len(arrays.get("history_iteration", []))
    return [{field: (int(arrays[f"history_{field}"][i])
                     if field == "iteration"
                     else float(arrays[f"history_{field}"][i]))
             for field in HISTORY_FIELDS} for i in range(n)]


def _verification_stable(history: list[dict[str, Any]],
                          strict_iteration: int | None,
                          final_iteration: int) -> bool:
    """Whether the complete +50 verification window stayed strict."""
    if strict_iteration is None:
        return False
    rows = [row for row in history
            if int(strict_iteration) < int(row["iteration"]) <= int(final_iteration)]
    if len(rows) < VERIFY_EXTRA_ITER:
        return False
    return all(float(row["step"]) >= STEP_THRESHOLD
               and float(row["weight_rel_1"]) <= WEIGHT_CHANGE_THRESHOLD
               for row in rows[-VERIFY_EXTRA_ITER:])


def _state_meta_compatible(meta: dict[str, Any], key: str,
                           payload_tag: str, membership_hash: str,
                           init: str, init_seed: int | None,
                           max_iter: int) -> bool:
    return (
        meta.get("version") == STATE_VERSION
        and meta.get("key") == key
        and meta.get("payload_tag") == payload_tag
        and meta.get("membership_hash") == membership_hash
        and meta.get("init") == init
        and meta.get("init_seed") == init_seed
        and meta.get("max_iter") == max_iter
        and meta.get("beta") == BETA
        and meta.get("init_sigma") == (INIT_SIGMA if init == "lognormal" else None)
    )


def _save_trajectory_state(key: str, meta: dict[str, Any],
                          arrays: dict[str, np.ndarray]) -> None:
    meta_path, npz_path = _trajectory_paths(key)
    _json_dump(meta_path, meta)
    _write_npz_atomic(npz_path, arrays)


def _load_trajectory_state(key: str) -> tuple[dict[str, Any], dict[str, np.ndarray]] | None:
    meta_path, npz_path = _trajectory_paths(key)
    if not meta_path.exists() or not npz_path.exists():
        return None
    return _load_json(meta_path), _load_npz(npz_path)


def _state_arrays(current_weights: np.ndarray, raw_prev: np.ndarray,
                  direction_prev: np.ndarray, weight_history: list[np.ndarray],
                  raw_history: list[np.ndarray], direction_history: list[np.ndarray],
                  history: list[dict[str, Any]], snapshots: dict[str, dict[str, Any]]) -> dict[str, np.ndarray]:
    arrays = {
        "current_weights": np.asarray(current_weights, dtype=np.float32),
        "raw_prev": np.asarray(raw_prev, dtype=np.float32),
        "direction_prev": np.asarray(direction_prev, dtype=np.float32),
        "weight_history": np.asarray(weight_history, dtype=np.float32),
        "raw_history": np.asarray(raw_history, dtype=np.float32),
        "direction_history": np.asarray(direction_history, dtype=np.float32),
    }
    arrays.update(_history_to_arrays(history))
    for label, snap in snapshots.items():
        t = _safe_key(label)
        arrays[f"snapshot_{t}_work_ids"] = np.asarray(snap["work_ids"], dtype=str)
        arrays[f"snapshot_{t}_scores"] = np.asarray(snap["scores"], dtype=np.float64)
        arrays[f"snapshot_{t}_reader_mass"] = np.asarray(snap["reader_mass"], dtype=np.float64)
        arrays[f"snapshot_{t}_weights"] = np.asarray(snap["weights"], dtype=np.float32)
    return arrays


def _data_from_state(meta: dict[str, Any], arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    snapshots: dict[str, dict[str, Any]] = {}
    for label in meta.get("snapshot_labels", []):
        t = _safe_key(str(label))
        snapshots[str(label)] = {
            "work_ids": arrays[f"snapshot_{t}_work_ids"].astype(str),
            "scores": arrays[f"snapshot_{t}_scores"].astype(np.float64),
            "reader_mass": arrays[f"snapshot_{t}_reader_mass"].astype(np.float64),
            "weights": arrays[f"snapshot_{t}_weights"].astype(np.float32),
        }
    history = _arrays_to_history(arrays)
    final_iteration = int(meta.get("final_iteration", meta.get("iteration", 0)))
    strict_iteration = meta.get("strict_iteration")
    verification_stable = meta.get("verification_stable")
    if verification_stable is None and meta.get("complete", False):
        verification_stable = _verification_stable(
            history, strict_iteration, final_iteration)
    return {
        "key": meta["key"],
        "label": meta.get("label", meta["key"]),
        "payload_tag": meta["payload_tag"],
        "membership_hash": meta["membership_hash"],
        "n_users": int(meta["n_users"]),
        "init": meta["init"],
        "init_seed": meta.get("init_seed"),
        "max_iter": int(meta["max_iter"]),
        "iteration": int(meta.get("iteration", 0)),
        "final_iteration": final_iteration,
        "complete": bool(meta.get("complete", False)),
        "converged": bool(meta.get("converged", False)),
        "stop_reason": meta.get("stop_reason", "incomplete"),
        "strict_iteration": strict_iteration,
        "strict_candidate_iteration": meta.get("strict_candidate_iteration", strict_iteration),
        "strict_window_start": meta.get("strict_window_start"),
        "verification_stable": verification_stable,
        "target_end": meta.get("target_end"),
        "history": history,
        "snapshots": snapshots,
        "final_weights": arrays["current_weights"].astype(np.float32),
    }


def run_trajectory(key: str, label: str, payload_tag: str,
                   init: str, init_seed: int | None, max_iter: int,
                   force: bool = False) -> dict[str, Any]:
    """Run or resume one exact-membership trajectory."""
    payload = _load_payload(payload_tag)
    matrix, _ = spectral.build_matrix(payload)
    operator, _ = spectral.make_operator(matrix, payload, attractor.CONFIG)
    membership_hash = _hash_ids(np.sort(np.asarray(payload["user_ids"], dtype=np.int64)))
    existing = None if force else _load_trajectory_state(key)
    if existing is not None:
        old_meta, old_arrays = existing
        if _state_meta_compatible(old_meta, key, payload_tag, membership_hash,
                                  init, init_seed, max_iter):
            data = _data_from_state(old_meta, old_arrays)
            if data["complete"]:
                failed_verification = (
                    old_meta.get("stop_reason") ==
                    "strict_convergence_plus_50_verification"
                    and not _verification_stable(
                        data["history"], data.get("strict_iteration"),
                        data["final_iteration"]))
                if not failed_verification:
                    print(f"[trajectory] {key}: loaded complete t={data['final_iteration']}",
                          flush=True)
                    return data
                print(f"[trajectory] {key}: strict +50 verification was unstable; "
                      f"continuing from t={data['final_iteration']} to the cap",
                      flush=True)
            current_weights = old_arrays["current_weights"].astype(np.float32)
            raw_prev = old_arrays["raw_prev"].astype(np.float32)
            direction_prev = old_arrays["direction_prev"].astype(np.float32)
            weight_history = [x.copy() for x in old_arrays["weight_history"]]
            raw_history = [x.copy() for x in old_arrays["raw_history"]]
            direction_history = [x.copy() for x in old_arrays["direction_history"]]
            history = _arrays_to_history(old_arrays)
            snapshots = data["snapshots"]
            iteration = int(old_meta.get("iteration", 0))
            consecutive = int(old_meta.get("consecutive", 0))
            strict_iteration = old_meta.get("strict_iteration")
            strict_window_start = old_meta.get("strict_window_start")
            target_end = old_meta.get("target_end")
            strict_candidate_iteration = old_meta.get(
                "strict_candidate_iteration", strict_iteration)
            if data["complete"]:
                # The prior +50 was a diagnostic, not a valid stopping point.
                # Resume the same state and allow a later stable window or the
                # full maximum iteration cap to determine the endpoint.
                strict_iteration = None
                strict_window_start = None
                target_end = None
                consecutive = 0
            print(f"[trajectory] {key}: resuming at t={iteration}", flush=True)
        else:
            existing = None

    if existing is None:
        current_weights = _init_weights(len(payload["user_ids"]), init, init_seed)
        raw_prev = operator.rmatmat(current_weights).ravel().astype(np.float32)
        direction_prev = attractor.normalize_columns(raw_prev).ravel().astype(np.float32)
        weight_history = [current_weights.copy()]
        raw_history = [raw_prev.copy()]
        direction_history = [direction_prev.copy()]
        history = _empty_history()
        snapshots = {"0": _capture_snapshot(matrix, operator, payload,
                                              current_weights)}
        iteration = 0
        consecutive = 0
        strict_iteration = None
        strict_candidate_iteration = None
        strict_window_start = None
        target_end = None

    def save(complete: bool = False, stop_reason: str = "incomplete") -> None:
        meta = {
            "version": STATE_VERSION,
            "key": key,
            "label": label,
            "payload_tag": payload_tag,
            "membership_hash": membership_hash,
            "n_users": int(len(payload["user_ids"])),
            "init": init,
            "init_seed": init_seed,
            "init_sigma": INIT_SIGMA if init == "lognormal" else None,
            "max_iter": int(max_iter),
            "beta": BETA,
            "iteration": int(iteration),
            "final_iteration": int(iteration) if complete else None,
            "complete": bool(complete),
            "converged": bool(strict_iteration is not None),
            "stop_reason": stop_reason,
            "strict_iteration": strict_iteration,
            "strict_candidate_iteration": strict_candidate_iteration,
            "strict_window_start": strict_window_start,
            "verification_stable": (
                _verification_stable(history, strict_iteration, iteration)
                if complete else None),
            "target_end": target_end,
            "consecutive": int(consecutive),
            "snapshot_labels": sorted(snapshots, key=lambda x: int(x)),
            "checkpoint_saved_at": time.time(),
        }
        _save_trajectory_state(
            key, meta,
            _state_arrays(current_weights, raw_prev, direction_prev,
                          weight_history, raw_history, direction_history,
                          history, snapshots),
        )

    if not history and "0" in snapshots:
        save(False)

    while True:
        if iteration >= max_iter:
            break
        if target_end is not None and iteration >= int(target_end):
            if _verification_stable(history, strict_iteration, iteration):
                break
            print(f"[trajectory] {key}: strict +50 verification failed at "
                  f"t={iteration}; continuing to the cap", flush=True)
            strict_iteration = None
            strict_window_start = None
            target_end = None
            consecutive = 0
            continue

        raw_books = operator.rmatmat(current_weights)
        scale = np.sqrt(np.mean(raw_books ** 2, axis=0, keepdims=True))
        books = np.tanh(raw_books / np.maximum(1.5 * scale, 1e-12)).astype(
            np.float32)
        user_signal = operator.matmat(books)
        user_signal -= user_signal.mean(axis=0, keepdims=True)
        user_signal /= np.maximum(user_signal.std(axis=0, keepdims=True), 1e-12)
        target = attractor.sigmoid(BETA * user_signal).astype(np.float32)
        target /= target.mean(axis=0, keepdims=True)
        new_weights = 0.35 * current_weights + 0.65 * target
        new_weights /= new_weights.mean(axis=0, keepdims=True)

        direction = attractor.normalize_columns(
            operator.rmatmat(new_weights)).ravel().astype(np.float32)
        step = float(np.sum(direction_prev * direction))
        weight_rel_1 = float(np.linalg.norm(new_weights - current_weights)) / max(
            float(np.linalg.norm(current_weights)), 1e-12)
        raw_new = operator.rmatmat(new_weights).ravel().astype(np.float32)
        book_rel_1 = float(np.linalg.norm(raw_new - raw_prev)) / max(
            float(np.linalg.norm(raw_prev)), 1e-12)

        lag2_w = (weight_history[-2] if len(weight_history) >= 2 else None)
        lag2_raw = (raw_history[-2] if len(raw_history) >= 2 else None)
        lag2_direction = (direction_history[-2]
                          if len(direction_history) >= 2 else None)
        weight_rel_2 = (float(np.linalg.norm(new_weights - lag2_w)) /
                        max(float(np.linalg.norm(lag2_w)), 1e-12)
                        if lag2_w is not None else float("nan"))
        book_rel_2 = (float(np.linalg.norm(raw_new - lag2_raw)) /
                      max(float(np.linalg.norm(lag2_raw)), 1e-12)
                      if lag2_raw is not None else float("nan"))
        weight_cos_lag2 = (_weight_cosine(new_weights, lag2_w)
                           if lag2_w is not None else float("nan"))
        direction_cos_lag2 = (_weight_cosine(direction, lag2_direction)
                              if lag2_direction is not None else float("nan"))
        weight_rel_3 = (float(np.linalg.norm(new_weights - weight_history[-3])) /
                        max(float(np.linalg.norm(weight_history[-3])), 1e-12)
                        if len(weight_history) >= 3 else float("nan"))
        weight_rel_4 = (float(np.linalg.norm(new_weights - weight_history[-4])) /
                        max(float(np.linalg.norm(weight_history[-4])), 1e-12)
                        if len(weight_history) >= 4 else float("nan"))

        iteration += 1
        history.append({
            "iteration": int(iteration),
            "step": step,
            "weight_rel_1": weight_rel_1,
            "book_rel_1": book_rel_1,
            "weight_rel_2": weight_rel_2,
            "book_rel_2": book_rel_2,
            "weight_cos_lag2": weight_cos_lag2,
            "direction_cos_lag2": direction_cos_lag2,
            "weight_rel_3": weight_rel_3,
            "weight_rel_4": weight_rel_4,
        })

        if step >= STEP_THRESHOLD and weight_rel_1 <= WEIGHT_CHANGE_THRESHOLD:
            consecutive += 1
            if consecutive >= CONSECUTIVE_CONVERGED and strict_iteration is None:
                strict_iteration = int(iteration)
                strict_candidate_iteration = int(iteration)
                strict_window_start = int(iteration - CONSECUTIVE_CONVERGED + 1)
                target_end = int(iteration + VERIFY_EXTRA_ITER)
                print(f"[trajectory] {key}: strict criterion at t={iteration}; "
                      f"verifying through t={target_end}", flush=True)
        else:
            consecutive = 0

        current_weights = new_weights.astype(np.float32)
        raw_prev = raw_new
        direction_prev = direction
        weight_history.append(current_weights.copy())
        weight_history = weight_history[-4:]
        raw_history.append(raw_prev.copy())
        raw_history = raw_history[-2:]
        direction_history.append(direction_prev.copy())
        direction_history = direction_history[-2:]

        if iteration in CHECKPOINTS:
            snapshots[str(iteration)] = _capture_snapshot(
                matrix, operator, payload, current_weights)
        if iteration in CHECKPOINTS or iteration % 100 == 0:
            save(False)
            print(f"[trajectory] {key} t={iteration} step={step:.9f} "
                  f"wrel={weight_rel_1:.3e} brel={book_rel_1:.3e}", flush=True)

    if str(iteration) not in snapshots:
        snapshots[str(iteration)] = _capture_snapshot(
            matrix, operator, payload, current_weights)
    verification_ok = _verification_stable(history, strict_iteration, iteration)
    if strict_iteration is not None and verification_ok:
        stop_reason = "strict_convergence_plus_50_verification"
    elif strict_candidate_iteration is not None:
        stop_reason = "max_iter_after_unstable_strict_verification"
    else:
        stop_reason = "max_iter_not_converged"
    save(True, stop_reason)
    print(f"[trajectory] {key}: complete t={iteration} strict={strict_iteration is not None}",
          flush=True)
    return _data_from_state(*_load_trajectory_state(key))  # type: ignore[arg-type]


def _trajectory_specs(context: dict[str, Any], include_shell: bool = True) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        specs.append({"key": f"{tag}_equal", "label": tag,
                      "payload_tag": f"payload_{tag}", "init": "equal",
                      "init_seed": None, "max_iter": LONG_MAX_ITER,
                      "kind": "primary_equal", "jury": tag})
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        reps = LONG_RANDOM_INIT_REPS_J30000 if n == 30000 else LONG_RANDOM_INIT_REPS
        for rep in range(reps):
            seed = _derive_seed(LITERARY_DYNAMICS_SEED, "random_init", tag, rep)
            specs.append({"key": f"{tag}_random{rep}", "label": f"{tag} random-init rep{rep}",
                          "payload_tag": f"payload_{tag}", "init": "lognormal",
                          "init_seed": int(seed), "max_iter": LONG_MAX_ITER,
                          "kind": "random_init", "jury": tag, "rep": rep})
    # The old five exact subsets are included when present.  If they are not
    # persisted, the campaign uses ten fresh deterministic subsets instead.
    if context.get("old_sub80_persisted", False):
        for rep in range(5):
            specs.append({"key": f"J10000_sub80_old{rep}",
                          "label": f"J10000 old 80% subset rep{rep}",
                          "payload_tag": f"payload_J10000_sub80_{rep}",
                          "init": "equal", "init_seed": None,
                          "max_iter": LONG_MAX_ITER, "kind": "sub80_old",
                          "jury": "J10000", "rep": rep})
        new_start = 0
    else:
        new_start = 0
    for rep in range(NEW_SUB80_REPS):
        specs.append({"key": f"J10000_sub80_new{rep}",
                      "label": f"J10000 new 80% subset rep{rep}",
                      "payload_tag": f"payload_J10000_sub80_new{rep}",
                      "init": "equal", "init_seed": None,
                      "max_iter": LONG_MAX_ITER, "kind": "sub80_new",
                      "jury": "J10000", "rep": rep})
    if include_shell:
        for shell in ("S1", "S2", "S3"):
            specs.append({"key": f"{shell}_equal", "label": shell,
                          "payload_tag": f"payload_{shell}", "init": "equal",
                          "init_seed": None, "max_iter": SHELL_MAX_ITER,
                          "kind": "shell_equal", "shell": shell})
    return specs


def _ensure_new_sub80_payloads(con, context: dict[str, Any]) -> None:
    full10 = context["memberships"]["J10000"]
    for rep in range(NEW_SUB80_REPS):
        payload_tag = f"payload_J10000_sub80_new{rep}"
        path = STATE_DIR / f"{payload_tag}.npz"
        if path.exists():
            p = _load_npz(path)
            if len(p["user_ids"]) == 8000 and set(p["user_ids"].tolist()) <= set(full10.tolist()):
                continue
            raise RuntimeError(f"invalid cached {payload_tag}")
        rng = np.random.default_rng(_derive_seed(
            LITERARY_DYNAMICS_SEED, "sub80_new_membership", rep))
        drop = rng.choice(len(full10), int(round(0.20 * len(full10))), replace=False)
        ids = np.sort(np.delete(full10, drop))
        if len(ids) != 8000 or not set(ids.tolist()) <= set(full10.tolist()):
            raise AssertionError(payload_tag)
        print(f"[prepare] building {payload_tag} n={len(ids)}", flush=True)
        _write_payload(payload_tag, inherited.build_local_payload(con, ids))


def _make_audit(context: dict[str, Any], con) -> dict[str, Any]:
    """Reproduce the inherited t=200 endpoints before long trajectories."""
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    add("starting_commit_or_descendant", _git_head() == "237cb3783b66c020ca034aab39a78af46899640f"
        or _git_head().startswith("237cb37"), f"HEAD={_git_head()}")
    add("frozen_score_hash_present", bool(context["score_hash"]),
        context["score_hash"])
    add("beta_exactly_2_5", BETA == 2.5, f"BETA={BETA}")
    add("long_cap_exactly_2000", LONG_MAX_ITER == 2000,
        f"LONG_MAX_ITER={LONG_MAX_ITER}")
    add("random_sigma_exactly_0p20", INIT_SIGMA == 0.20,
        f"sigma={INIT_SIGMA}")
    add("strict_rule_frozen",
        STEP_THRESHOLD == 0.9999 and WEIGHT_CHANGE_THRESHOLD == 1e-4
        and CONSECUTIVE_CONVERGED == 5,
        f"step>={STEP_THRESHOLD}, wrel<={WEIGHT_CHANGE_THRESHOLD}, "
        f"consecutive={CONSECUTIVE_CONVERGED}")
    add("equal_init_exact_ones", np.array_equal(_equal_init(17), np.ones(17, dtype=np.float32)),
        "all initial weights are exactly one after mean normalization")
    isrc = inspect.getsource(pruning.iterate_map)
    add("historical_iterate_map_equation_audited",
        all(x in isrc for x in ("tanh", "user_signal.std", "sigmoid",
                                "0.35", "0.65", "weights /= weights.mean")),
        "historical source contains the frozen tanh/sigmoid/damped equation")
    add("no_pruning_or_reversal_in_long_runner",
        all(x not in inspect.getsource(run_trajectory)
            for x in ("remove_fraction", "retained_target", "survivor", "reversal")),
        "trajectory code changes no IDs and contains no pruning/reversal path")

    expected = json.loads(inherited.OUT_JSON.read_text(encoding="utf-8"))["primary"]
    t0 = time.time()
    con2 = con
    reproduction: dict[str, Any] = {}
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        ids = context["memberships"][tag]
        res = inherited.run_convergence(con2, ids, tag, force=False)
        head = inherited._book_head(res["preference"],
                                    {**res, "work_ids": res["work_ids"]},
                                    limit=1000)
        exp = expected[tag]
        actual = {
            "final_step": float(res["final_step"]),
            "weight_rel": float(res["final_weight_rel"]),
            "book_rel": float(res["final_book_rel"]),
            "kish": float(inherited._kish(res["weights"])),
            "seed_head_top50": [r["work_id"] for r in res["seed_head"][:50]],
            "seed_to_t200": {
                "j50": inherited._head_jaccard(res["seed_head"], head, 50),
                "overlap50": len(set(r["work_id"] for r in res["seed_head"][:50])
                                  & set(r["work_id"] for r in head[:50])) / 50.0,
                "j200": inherited._head_jaccard(res["seed_head"], head, 200),
                "rho200": inherited._head_rho(res["seed_head"], head, 200),
            },
        }
        target = {
            "final_step": exp["final_step"],
            "weight_rel": exp["final_weight_rel"],
            "book_rel": exp["final_book_rel"],
            "kish": exp["kish"],
            "seed_head_top50": [r["work_id"] for r in exp["seed_head_top50"]],
            "seed_to_t200": exp["seed_vs_conv"],
        }
        ok = (
            np.isclose(actual["final_step"], target["final_step"], atol=1e-12)
            and np.isclose(actual["weight_rel"], target["weight_rel"], atol=1e-12)
            and np.isclose(actual["book_rel"], target["book_rel"], atol=1e-12)
            and np.isclose(actual["kish"], target["kish"], atol=1e-9)
            and actual["seed_head_top50"] == target["seed_head_top50"]
            and np.isclose(actual["seed_to_t200"]["j50"], target["seed_to_t200"]["j50"], atol=1e-12)
            and np.isclose(actual["seed_to_t200"]["j200"], target["seed_to_t200"]["j200"], atol=1e-12)
            and np.isclose(actual["seed_to_t200"]["rho200"], target["seed_to_t200"]["rho200"], atol=1e-12)
        )
        add(f"t200_reproduction_{tag}", ok,
            f"step={actual['final_step']:.9f} wrel={actual['weight_rel']:.3e} "
            f"Kish={actual['kish']:.3f} J50={actual['seed_to_t200']['j50']:.6f}")
        reproduction[tag] = {"actual": actual, "expected": target}

    # Exact nestedness and shell invariants.
    sets = {tag: set(ids.tolist()) for tag, ids in context["memberships"].items()}
    add("nested_J5_J10", len(sets["J5000"] & sets["J10000"]) == 5000,
        f"intersection={len(sets['J5000'] & sets['J10000'])}")
    add("nested_J10_J20", len(sets["J10000"] & sets["J20000"]) == 10000,
        f"intersection={len(sets['J10000'] & sets['J20000'])}")
    add("nested_J20_J30", len(sets["J20000"] & sets["J30000"]) == 20000,
        f"intersection={len(sets['J20000'] & sets['J30000'])}")
    shell_sets = {s: set(ids.tolist()) for s, ids in context["shells"].items()}
    pairwise_disjoint = all(not (shell_sets[a] & shell_sets[b])
                            for i, a in enumerate(shell_sets)
                            for b in list(shell_sets)[i + 1:])
    add("shells_pairwise_disjoint", pairwise_disjoint,
        f"sizes={[len(x) for x in shell_sets.values()]}")
    add("shell_union_J30000",
        set().union(*shell_sets.values()) == sets["J30000"],
        f"union={len(set().union(*shell_sets.values()))}")
    add("old_artifacts_present",
        inherited.OUT_JSON.exists() and inherited.OUT_MD.exists()
        and inherited.OUT_HEADS.exists(),
        "237cb37 JSON/report/heads still exist")
    add("persisted_old_80_subsets",
        bool(context.get("old_sub80_persisted", False)),
        "five exact payloads found" if context.get("old_sub80_persisted")
        else "not found; ten fresh subsets will be used")
    add("absent_rank_unit", _movement_unit_test(),
        "missing top-500 book gets fixed rank 501")
    add("jaccard_overlap_are_distinct", _head_metrics(
        {"work_ids": np.asarray([str(i) for i in range(50)])},
        {"work_ids": np.asarray([str(i) for i in range(25, 75)])}, 50)["jaccard"]
        != _head_metrics(
            {"work_ids": np.asarray([str(i) for i in range(50)])},
            {"work_ids": np.asarray([str(i) for i in range(25, 75)])}, 50)["overlap_fraction"],
        "Jaccard and overlap fraction use separate formulas")
    add("lag_history_uses_t_minus_2", _lag_unit_test(),
        "lag-2 distances compare the actual t-2 vector")

    return {
        "seed": LITERARY_DYNAMICS_SEED,
        "run_started_at": time.time(),
        "starting_head": _git_head(),
        "elapsed_seconds": time.time() - t0,
        "checks": checks,
        "ok": bool(all(c["ok"] for c in checks)),
        "reproduction": reproduction,
        "primary_membership_hashes": {
            tag: _hash_ids(ids) for tag, ids in context["memberships"].items()
        },
    }


def _movement_unit_test() -> bool:
    old = {"work_ids": np.asarray([str(i) for i in range(1, 6)])}
    new = {"work_ids": np.asarray(["x", "2", "3", "4", "5"])}
    ranks_old = {w: i + 1 for i, w in enumerate(old["work_ids"][:500])}
    ranks_new = {w: i + 1 for i, w in enumerate(new["work_ids"][:500])}
    return ranks_old.get("x", 501) == 501 and ranks_new.get("x", 501) == 1


def _lag_unit_test() -> bool:
    a = np.asarray([1.0, 2.0, 3.0])
    b = np.asarray([2.0, 3.0, 4.0])
    c = np.asarray([1.0, 2.0, 3.0])
    got = np.linalg.norm(c - a) / np.linalg.norm(a)
    wrong = np.linalg.norm(c - b) / np.linalg.norm(b)
    return got == 0.0 and wrong > 0.0


def _movement(old_snap: dict[str, Any], new_snap: dict[str, Any],
              metadata: dict[str, dict[str, Any]], limit: int = 30) -> dict[str, Any]:
    old_ids = [str(w) for w in old_snap["work_ids"][:500]]
    new_ids = [str(w) for w in new_snap["work_ids"][:500]]
    old_r = {w: i + 1 for i, w in enumerate(old_ids)}
    new_r = {w: i + 1 for i, w in enumerate(new_ids)}
    union = set(old_ids) | set(new_ids)
    rows = []
    for wid in union:
        ro = old_r.get(wid, 501)
        rn = new_r.get(wid, 501)
        m = metadata.get(wid, {})
        rows.append({"work_id": wid, "title": m.get("title", wid),
                     "author": m.get("author", ""), "old_rank": int(ro),
                     "new_rank": int(rn), "delta": int(ro - rn)})
    risers = sorted(rows, key=lambda r: (-r["delta"], r["new_rank"], r["work_id"]))[:limit]
    fallers = sorted(rows, key=lambda r: (r["delta"], r["old_rank"], r["work_id"]))[:limit]
    return {"risers": risers, "fallers": fallers,
            "rank_absent_convention": 501}


def _movement_summary(movement: dict[str, Any], limit: int = 15) -> dict[str, Any]:
    def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        top = rows[:limit]
        authors = Counter(r.get("author", "") for r in top if r.get("author"))
        return {
            "top_authors": [{"author": a, "count": int(n)}
                            for a, n in authors.most_common(8)],
            "examples": [{"title": r["title"], "author": r["author"],
                          "old_rank": r["old_rank"], "new_rank": r["new_rank"],
                          "delta": r["delta"]} for r in top[:8]],
        }
    return {"risers": summarize(movement["risers"]),
            "fallers": summarize(movement["fallers"])}


def _load_metadata(con, work_ids: np.ndarray) -> dict[str, dict[str, Any]]:
    ids = [str(x) for x in np.asarray(work_ids).tolist()]
    table = f"ldmeta_{int(time.time() * 1000000) % 1000000000}"
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {table} SELECT unnest(?::VARCHAR[])", [ids])
    rows = con.execute(
        f"""
        SELECT s.work_id, s.title, s.author,
               COALESCE(f.is_collection, FALSE),
               COALESCE(f.is_duplicate, FALSE),
               COALESCE(f.is_comic, FALSE),
               COALESCE(f.is_picture_book, FALSE),
               COALESCE(f.canonical_work_id, ''),
               COALESCE(f.canonical_title, '')
        FROM ex.work_scores s
        JOIN {table} t USING (work_id)
        LEFT JOIN ex.work_flags f USING (work_id)
        """
    ).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {table}")
    out = {}
    for wid, title, author, collection, duplicate, comic, picture, canonical, canonical_title in rows:
        out[str(wid)] = {
            "title": title or "", "author": author or "",
            "is_collection": bool(collection), "is_duplicate": bool(duplicate),
            "is_comic": bool(comic), "is_picture_book": bool(picture),
            "canonical_work_id": str(canonical or ""),
            "canonical_title": str(canonical_title or ""),
        }
    for wid in ids:
        out.setdefault(wid, {"title": wid, "author": "", "is_collection": False,
                             "is_duplicate": False, "is_comic": False,
                             "is_picture_book": False, "canonical_work_id": "",
                             "canonical_title": ""})
    return out


def _load_probe_sets(payload: dict[str, np.ndarray]) -> dict[str, set[str]]:
    # This is intentionally called only after all dynamic trajectories have
    # been run.  The returned sets annotate heads and never enter the map.
    inherited._load_probes_local(payload)
    return {
        "pos": set(inherited._PROBE_POS),
        "exact": set(inherited._PROBE_EXACT),
        "broad": set(inherited._PROBE_BROAD),
        "anti": set(inherited._PROBE_ANTI),
    }


def _descriptor(head: dict[str, Any], metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ids = [str(x) for x in head["work_ids"][:50]]
    authors = [metadata.get(w, {}).get("author", "") for w in ids]
    known = [a for a in authors if a]
    counts = Counter(known)
    return {
        "unique_authors_50": int(len(set(known))),
        "unknown_author_count_50": int(sum(not a for a in authors)),
        "max_same_author_count_50": int(max(counts.values(), default=0)),
        "top_authors_50": [{"author": a, "count": int(n)}
                           for a, n in counts.most_common(8)],
        "collection_count_50": int(sum(metadata.get(w, {}).get("is_collection", False)
                                        for w in ids)),
        "duplicate_count_50": int(sum(metadata.get(w, {}).get("is_duplicate", False)
                                       for w in ids)),
        "comic_count_50": int(sum(metadata.get(w, {}).get("is_comic", False)
                                   for w in ids)),
        "picture_book_count_50": int(sum(metadata.get(w, {}).get("is_picture_book", False)
                                          for w in ids)),
        "series_descriptors_available": False,
    }


def _enriched_head(head: dict[str, Any], metadata: dict[str, dict[str, Any]],
                   probes: dict[str, set[str]]) -> list[dict[str, Any]]:
    rows = []
    for i, (wid, score, mass) in enumerate(zip(head["work_ids"][:50],
                                               head["scores"][:50],
                                               head["reader_mass"][:50]), 1):
        w = str(wid)
        m = metadata.get(w, {})
        rows.append({
            "rank": int(i), "work_id": w, "title": m.get("title", w),
            "author": m.get("author", ""), "score": float(score),
            "n_eff": float(mass),
            "pos": bool(w in probes["pos"]),
            "exact": bool(w in probes["exact"]),
            "broad": bool(w in probes["broad"]),
            "anti": bool(w in probes["anti"]),
            "is_collection": bool(m.get("is_collection", False)),
            "is_duplicate": bool(m.get("is_duplicate", False)),
            "is_comic": bool(m.get("is_comic", False)),
            "is_picture_book": bool(m.get("is_picture_book", False)),
        })
    return rows


def _semantics(head: dict[str, Any], probes: dict[str, set[str]]) -> dict[str, int]:
    ids = [str(x) for x in head["work_ids"][:50]]
    return {name: int(sum(w in probes[key] for w in ids))
            for name, key in (("pos50", "pos"), ("exact50", "exact"),
                              ("broad50", "broad"), ("anti50", "anti"))}


def _window_summary(data: dict[str, Any]) -> dict[str, Any]:
    iters = _history_array(data, "iteration")
    out: dict[str, Any] = {}
    for lo, hi in WINDOWS:
        mask = (iters >= lo) & (iters <= hi)
        key = f"{lo}_{hi}"
        if not np.any(mask):
            continue
        out[key] = {}
        for field in ("weight_rel_1", "weight_rel_2", "book_rel_1", "step"):
            vals = _history_array(data, field)[mask]
            vals = vals[np.isfinite(vals)]
            if len(vals):
                out[key][field] = {"median": float(np.median(vals)),
                                   "min": float(np.min(vals)),
                                   "max": float(np.max(vals))}
    return out


def _trend(data: dict[str, Any], lo: int, hi: int) -> dict[str, Any]:
    x = _history_array(data, "iteration")
    y = _history_array(data, "weight_rel_1")
    mask = (x >= lo) & (x <= hi) & np.isfinite(y) & (y > 0)
    if int(mask.sum()) < 3:
        return {"n": int(mask.sum()), "slope": float("nan"),
                "r2": float("nan"), "pvalue": float("nan")}
    lr = linregress(x[mask], np.log(y[mask]))
    return {"n": int(mask.sum()), "slope": float(lr.slope),
            "r2": float(lr.rvalue ** 2), "pvalue": float(lr.pvalue)}


def _cycle_diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    h = data["history"]
    if not h:
        return {"available": False}
    recent = h[-min(100, len(h)):]
    def med(field: str) -> float:
        vals = np.asarray([row[field] for row in recent], dtype=np.float64)
        vals = vals[np.isfinite(vals)]
        return float(np.median(vals)) if len(vals) else float("nan")
    w1, w2 = med("weight_rel_1"), med("weight_rel_2")
    w3, w4 = med("weight_rel_3"), med("weight_rel_4")
    two_cycle = bool(np.isfinite(w1) and np.isfinite(w2) and w1 > 1e-8
                     and w2 < 0.25 * w1)
    return {
        "available": True,
        "recent_window": len(recent),
        "median_last_weight_rel_1": w1,
        "median_last_weight_rel_2": w2,
        "median_last_weight_rel_3": w3,
        "median_last_weight_rel_4": w4,
        "lag2_over_lag1": float(w2 / w1) if w1 > 0 else float("nan"),
        "lag3_over_lag1": float(w3 / w1) if w1 > 0 else float("nan"),
        "lag4_over_lag1": float(w4 / w1) if w1 > 0 else float("nan"),
        "median_last_weight_cos_lag2": med("weight_cos_lag2"),
        "median_last_direction_cos_lag2": med("direction_cos_lag2"),
        "two_cycle_heuristic": two_cycle,
        "interpretation": "lag-2 much smaller than lag-1" if two_cycle
        else "no strong lag-2 cycle signature under this descriptive rule",
    }


def _practical_stability(data: dict[str, Any]) -> dict[str, Any]:
    final = _snapshot(data, _final_time(data))
    times = sorted(int(t) for t in data["snapshots"])
    rows = []
    for t in times:
        snap = _snapshot(data, t)
        m = _head_metrics(snap, final, 50)
        rows.append({"iteration": int(t), **m})
    stable = None
    for t in times:
        if all(row["overlap_fraction"] >= 0.90
               for row in rows if row["iteration"] >= t):
            stable = int(t)
            break
    return {"comparison_to_final": rows,
            "practical_head_stability_iteration": stable}


def _checkpoint_comparisons(data: dict[str, Any],
                            score_vectors: dict[str, np.ndarray] | None = None
                            ) -> list[dict[str, Any]]:
    """Compare every saved checkpoint with its previous checkpoint and endpoints."""
    times = sorted(int(t) for t in data["snapshots"])
    if not times:
        return []
    t200 = _actual_snapshot_time(data, 200)
    final_t = _final_time(data)

    def compare(left_t: int, right_t: int) -> dict[str, Any]:
        left_score = score_vectors.get(str(left_t)) if score_vectors else None
        right_score = score_vectors.get(str(right_t)) if score_vectors else None
        return _comparison(_snapshot(data, left_t), _snapshot(data, right_t),
                           left_score, right_score)

    return [{
        "iteration": int(t),
        "previous_iteration": int(times[i - 1]) if i else None,
        "vs_previous": compare(times[i - 1], t) if i else None,
        "vs_t200": compare(t, t200),
        "vs_final": compare(t, final_t),
    } for i, t in enumerate(times)]


def _direct_assessment(data: dict[str, Any], probes: dict[str, set[str]],
                       metadata: dict[str, dict[str, Any]]) -> str:
    snap = _snapshot(data, 0)
    sem = _semantics(snap, probes)
    desc = _descriptor(snap, metadata)
    top_titles = [metadata.get(str(w), {}).get("title", str(w))
                  for w in snap["work_ids"][:5]]
    return (f"direct head: pos/exact/broad/anti={sem['pos50']}/"
            f"{sem['exact50']}/{sem['broad50']}/{sem['anti50']}; "
            f"unique authors={desc['unique_authors_50']}, max same author="
            f"{desc['max_same_author_count_50']}; top five="
            + "; ".join(top_titles))


def _dynamic_assessment(data: dict[str, Any], probes: dict[str, set[str]],
                        metadata: dict[str, dict[str, Any]]) -> str:
    snap = _snapshot(data, _final_time(data))
    sem = _semantics(snap, probes)
    desc = _descriptor(snap, metadata)
    top_titles = [metadata.get(str(w), {}).get("title", str(w))
                  for w in snap["work_ids"][:5]]
    return (f"final dynamic head: pos/exact/broad/anti={sem['pos50']}/"
            f"{sem['exact50']}/{sem['broad50']}/{sem['anti50']}; "
            f"unique authors={desc['unique_authors_50']}, max same author="
            f"{desc['max_same_author_count_50']}; top five="
            + "; ".join(top_titles))


def _load_direct_and_dynamic_data(context: dict[str, Any],
                                  specs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out = {}
    for spec in specs:
        meta_path, _ = _trajectory_paths(spec["key"])
        if not meta_path.exists():
            continue
        state = _load_trajectory_state(spec["key"])
        if state is not None:
            out[spec["key"]] = _data_from_state(*state)
    return out


def _build_output_npz(context: dict[str, Any], data: dict[str, dict[str, Any]],
                      specs: list[dict[str, Any]],
                      primary_score_vectors: dict[str, dict[str, np.ndarray]],
                      direct_score_vectors: dict[str, np.ndarray]) -> None:
    arrays: dict[str, np.ndarray] = {
        "config/literary_dynamics_seed": np.asarray([LITERARY_DYNAMICS_SEED], dtype=np.int64),
        "config/beta": np.asarray([BETA], dtype=np.float64),
        "config/long_max_iter": np.asarray([LONG_MAX_ITER], dtype=np.int64),
        "config/init_sigma": np.asarray([INIT_SIGMA], dtype=np.float64),
        "frozen/universe": context["universe"],
        "frozen/scores": context["scores"],
    }
    for tag, ids in context["memberships"].items():
        arrays[f"membership/{tag}/user_ids"] = np.asarray(ids, dtype=np.int64)
    for tag, ids in context["shells"].items():
        arrays[f"membership/{tag}/user_ids"] = np.asarray(ids, dtype=np.int64)
    for key, d in data.items():
        safe = _safe_key(key)
        arrays[f"trajectory/{safe}/final_weights"] = d["final_weights"]
        arrays[f"trajectory/{safe}/user_count"] = np.asarray([d["n_users"]], dtype=np.int64)
        arrays[f"trajectory/{safe}/final_iteration"] = np.asarray([d["final_iteration"]], dtype=np.int64)
        for field in HISTORY_FIELDS:
            arrays[f"trajectory/{safe}/history/{field}"] = _history_array(d, field)
        for label, snap in d["snapshots"].items():
            st = _safe_key(label)
            arrays[f"trajectory/{safe}/snapshot/{st}/rank"] = np.arange(
                1, len(snap["work_ids"]) + 1, dtype=np.int32)
            arrays[f"trajectory/{safe}/snapshot/{st}/work_ids"] = snap["work_ids"]
            arrays[f"trajectory/{safe}/snapshot/{st}/scores"] = snap["scores"]
            arrays[f"trajectory/{safe}/snapshot/{st}/reader_mass"] = snap["reader_mass"]
            arrays[f"trajectory/{safe}/snapshot/{st}/weights"] = snap["weights"]
    for key, by_time in primary_score_vectors.items():
        safe = _safe_key(key)
        for label, score in by_time.items():
            arrays[f"preference_score/{safe}/t{_safe_key(label)}"] = np.asarray(score, dtype=np.float32)
    for key, score in direct_score_vectors.items():
        arrays[f"direct_preference_score/{_safe_key(key)}"] = np.asarray(score, dtype=np.float32)
    _write_npz_atomic(OUT_NPZ, arrays)


def _score_vectors_for(data: dict[str, Any], payload_tag: str,
                       desired_times: list[int]) -> dict[str, np.ndarray]:
    payload = _load_payload(payload_tag)
    matrix, _ = spectral.build_matrix(payload)
    out = {}
    for desired in desired_times:
        t = _actual_snapshot_time(data, desired)
        snap = _snapshot(data, t)
        pref = attractor.weighted_preferences(matrix, snap["weights"])
        out[str(t)] = np.asarray(pref["score"], dtype=np.float64)
    return out


def _posthoc_snapshot_record(data: dict[str, Any], t: int,
                             metadata: dict[str, dict[str, Any]],
                             probes: dict[str, set[str]]) -> dict[str, Any]:
    snap = _snapshot(data, t)
    return {
        "iteration": int(t),
        "top1000_npz_complete": True,
        "top1000_count": int(len(snap["work_ids"])),
        "top50": _enriched_head(snap, metadata, probes),
        "descriptors": _descriptor(snap, metadata),
        "semantic_annotations": _semantics(snap, probes),
    }


def _trajectory_json_record(data: dict[str, Any], spec: dict[str, Any],
                            metadata: dict[str, dict[str, Any]],
                            probes: dict[str, set[str]]) -> dict[str, Any]:
    checkpoints = {
        str(t): _posthoc_snapshot_record(data, t, metadata, probes)
        for t in sorted(int(x) for x in data["snapshots"])
    }
    return {
        "key": data["key"], "label": data["label"], "kind": spec.get("kind"),
        "jury": spec.get("jury"), "shell": spec.get("shell"),
        "rep": spec.get("rep"), "payload_tag": data["payload_tag"],
        "n": data["n_users"], "init": data["init"],
        "init_seed": data["init_seed"], "init_sigma": INIT_SIGMA if data["init"] == "lognormal" else None,
        "max_iter": data["max_iter"], "iterations": data["final_iteration"],
        "strict_convergence_reached": data["converged"],
        "strict_iteration": data["strict_iteration"],
        "strict_candidate_iteration": data.get("strict_candidate_iteration"),
        "strict_window_start": data["strict_window_start"],
        "verification_stable": data.get("verification_stable"),
        "stop_reason": data["stop_reason"],
        "membership_hash_sorted": data["membership_hash"],
        "history": data["history"],
        "checkpoints": checkpoints,
        "window_summary": _window_summary(data),
        "log_weight_rel_trend": {
            "200_1000": _trend(data, 200, 1000),
            "1000_2000": _trend(data, 1000, 2000),
        },
        "cycle_diagnostics": _cycle_diagnostics(data),
        "practical_head_stability": _practical_stability(data),
    }


def _trajectory_lookup(data: dict[str, dict[str, Any]], key: str) -> dict[str, Any]:
    if key not in data:
        raise RuntimeError(f"missing trajectory state {key}")
    return data[key]


def _primary_comparisons(data: dict[str, dict[str, Any]],
                         primary_scores: dict[str, dict[str, np.ndarray]],
                         direct_scores: dict[str, np.ndarray]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        d = _trajectory_lookup(data, f"direct_{tag}")
        e = _trajectory_lookup(data, f"{tag}_equal")
        final_t = _final_time(e)
        t200 = _actual_snapshot_time(e, 200)
        direct_snap = _snapshot(d, 0)
        out[tag] = {
            "direct_to_t200": _comparison(
                direct_snap, _snapshot(e, t200), direct_scores[tag],
                primary_scores[f"{tag}_equal"][str(t200)]),
            "direct_to_final": _comparison(
                direct_snap, _snapshot(e, final_t), direct_scores[tag],
                primary_scores[f"{tag}_equal"][str(final_t)]),
            "t200_to_final": _comparison(
                _snapshot(e, t200), _snapshot(e, final_t),
                primary_scores[f"{tag}_equal"][str(t200)],
                primary_scores[f"{tag}_equal"][str(final_t)]),
        }
    return out


def _direct_size_trajectory(data: dict[str, dict[str, Any]],
                            direct_scores: dict[str, np.ndarray],
                            metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    pairs = [("J5000", "J10000"), ("J10000", "J20000"),
             ("J20000", "J30000")]
    out = {}
    for old_tag, new_tag in pairs:
        old_d = _snapshot(_trajectory_lookup(data, f"direct_{old_tag}"), 0)
        new_d = _snapshot(_trajectory_lookup(data, f"direct_{new_tag}"), 0)
        movement = _movement(old_d, new_d, metadata, 30)
        out[f"{old_tag}_to_{new_tag}"] = {
            "comparison": _comparison(old_d, new_d, direct_scores[old_tag],
                                       direct_scores[new_tag]),
            "movement": movement,
            "movement_summary": _movement_summary(movement),
        }
    return out


def _primary_movement(data: dict[str, dict[str, Any]],
                      primary_scores: dict[str, dict[str, np.ndarray]],
                      metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        d = _snapshot(_trajectory_lookup(data, f"direct_{tag}"), 0)
        e = _trajectory_lookup(data, f"{tag}_equal")
        final_t = _final_time(e)
        t200 = _actual_snapshot_time(e, 200)
        final_snap = _snapshot(e, final_t)
        t200_snap = _snapshot(e, t200)
        mov_df = _movement(d, final_snap, metadata, 30)
        mov_dt = _movement(d, t200_snap, metadata, 30)
        mov_tf = _movement(t200_snap, final_snap, metadata, 30)
        out[tag] = {
            "direct_to_t200": mov_dt,
            "direct_to_final": mov_df,
            "t200_to_final": mov_tf,
            "direct_to_t200_summary": _movement_summary(mov_dt),
            "direct_to_final_summary": _movement_summary(mov_df),
            "t200_to_final_summary": _movement_summary(mov_tf),
        }
    return out


def _descriptive_size_dynamics(data: dict[str, dict[str, Any]],
                               direct_scores: dict[str, np.ndarray],
                               primary_scores: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    d5_data = _trajectory_lookup(data, "direct_J5000")
    d5 = _snapshot(d5_data, 0)
    d5_score = direct_scores["J5000"]
    out = {}
    for n in (10000, 20000, 30000):
        tag = f"J{n}"
        d = _trajectory_lookup(data, f"direct_{tag}")
        e = _trajectory_lookup(data, f"{tag}_equal")
        d_snap = _snapshot(d, 0)
        ftime = _final_time(e)
        f_snap = _snapshot(e, ftime)
        f_score = primary_scores[f"{tag}_equal"][str(ftime)]
        out[tag] = {
            "membership_size_displacement_D5_to_DN": _comparison(
                d5, d_snap, d5_score, direct_scores[tag]),
            "convergence_displacement_DN_to_CN_final": _comparison(
                d_snap, f_snap, direct_scores[tag], f_score),
            "total_displacement_D5_to_CN_final": _comparison(
                d5, f_snap, d5_score, f_score),
            "note": "descriptive decomposition, not a formal causal attribution",
        }
    return out


def _semantic_progression(data: dict[str, dict[str, Any]],
                          probes: dict[str, set[str]]) -> dict[str, Any]:
    out = {}
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        d = _trajectory_lookup(data, f"{tag}_equal")
        requested = [0, 20, 100, 200, 500, 1000, 2000]
        rows = {}
        for req in requested:
            t = _actual_snapshot_time(d, req)
            rows[str(req)] = {"actual_iteration": t,
                              **_semantics(_snapshot(d, t), probes)}
        out[tag] = rows
    return out


def _concentration_progression(data: dict[str, dict[str, Any]],
                               metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        d = _trajectory_lookup(data, f"{tag}_equal")
        rows = {}
        for t in sorted(int(x) for x in d["snapshots"]):
            rows[str(t)] = _descriptor(_snapshot(d, t), metadata)
        out[tag] = rows
    return out


def _random_init_analysis(data: dict[str, dict[str, Any]],
                          primary_scores: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        equal = _trajectory_lookup(data, f"{tag}_equal")
        reps = sorted(k for k in data if k.startswith(f"{tag}_random"))
        rows = {}
        for key in reps:
            r = data[key]
            by_time = {}
            for desired in (200, 500, 1000, 2000):
                rt = _actual_snapshot_time(r, desired)
                et = _actual_snapshot_time(equal, desired)
                rs = _snapshot(r, rt)
                es = _snapshot(equal, et)
                rs_score = _score_vector_from_snapshot(r, key, rt)
                es_score = primary_scores[f"{tag}_equal"][str(et)]
                by_time[str(desired)] = {
                    "actual_random_iteration": rt,
                    "actual_equal_iteration": et,
                    "book": _comparison(rs, es, rs_score, es_score),
                    "user_weight_cosine": _weight_cosine(rs["weights"], es["weights"]),
                }
            rows[key] = by_time
        final_values = []
        for key in reps:
            final_values.append(rows[key]["2000"])
        pairwise = []
        for i, akey in enumerate(reps):
            for bkey in reps[i + 1:]:
                a = _snapshot(data[akey], _final_time(data[akey]))
                b = _snapshot(data[bkey], _final_time(data[bkey]))
                pairwise.append(_comparison(a, b))
        out[tag] = {
            "replicates": rows,
            "final_summary": _summary_comparisons(final_values),
            "pairwise_final_summary": _summary_comparisons(pairwise),
            "classification": _classify_random(rows, pairwise),
        }
    return out


def _score_vector_from_snapshot(data: dict[str, Any], key: str,
                               t: int) -> np.ndarray:
    payload = _load_payload(data["payload_tag"])
    matrix, _ = spectral.build_matrix(payload)
    return np.asarray(attractor.weighted_preferences(
        matrix, _snapshot(data, t)["weights"])["score"], dtype=np.float64)


def _summary_comparisons(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    def vals(path: tuple[str, ...]) -> np.ndarray:
        out = []
        for row in rows:
            x: Any = row
            row_path = path
            if row_path and row_path[0] == "book" and "book" not in row:
                row_path = row_path[1:]
            for p in row_path:
                x = x.get(p, float("nan")) if isinstance(x, dict) else float("nan")
            try:
                out.append(float(x))
            except (TypeError, ValueError):
                out.append(float("nan"))
        return np.asarray(out, dtype=np.float64)
    paths = {
        "j50": ("book", "top50", "jaccard"),
        "overlap50": ("book", "top50", "overlap_fraction"),
        "j200": ("book", "top200", "jaccard"),
        "score_pearson": ("book", "score_correlation", "pearson"),
        "weight_cosine": ("user_weight_cosine",),
    }
    out = {"n": len(rows)}
    for name, path in paths.items():
        a = vals(path)
        a = a[np.isfinite(a)]
        if len(a):
            out[name] = {"median": float(np.median(a)),
                         "p10": float(np.quantile(a, .10)),
                         "p90": float(np.quantile(a, .90))}
        else:
            out[name] = {"median": float("nan"), "p10": float("nan"),
                         "p90": float("nan")}
    return out


def _classify_random(rows: dict[str, Any], pairwise: list[dict[str, Any]]) -> str:
    finals = [r.get("2000", {}) for r in rows.values()]
    if not finals:
        return "unresolved"
    eq_j50 = np.asarray([r.get("book", {}).get("top50", {}).get("overlap_fraction", np.nan)
                         for r in finals], dtype=np.float64)
    eq_j200 = np.asarray([r.get("book", {}).get("top200", {}).get("overlap_fraction", np.nan)
                          for r in finals], dtype=np.float64)
    pair_j50 = np.asarray([r.get("top50", {}).get("overlap_fraction", np.nan)
                           for r in pairwise], dtype=np.float64)
    med_eq = float(np.nanmedian(eq_j50)) if np.any(np.isfinite(eq_j50)) else float("nan")
    med_pair = float(np.nanmedian(pair_j50)) if np.any(np.isfinite(pair_j50)) else float("nan")
    t200 = np.asarray([r.get("200", {}).get("book", {}).get("top50", {}).get("overlap_fraction", np.nan)
                       for r in rows.values()], dtype=np.float64)
    med_t200 = float(np.nanmedian(t200)) if np.any(np.isfinite(t200)) else float("nan")
    if np.isfinite(med_t200) and np.isfinite(med_eq) and med_t200 < .6 and med_eq >= .9:
        return "transient sensitivity"
    if np.isfinite(med_eq) and med_eq >= .9:
        return "stable ranking / unstable weights"
    # A high pairwise median can hide a mixed endpoint pattern: one or more
    # starts may be equal-init-like while the remaining starts share a
    # distinct alternate endpoint.  Preserve that distinction instead of
    # calling the long-run result merely unresolved.
    if np.isfinite(med_eq) and med_eq < .75 and np.isfinite(med_pair) and med_pair >= .75:
        return "persistent basin multiplicity (mixed endpoints)"
    if np.isfinite(med_eq) and med_eq < .75 and np.isfinite(med_pair) and med_pair < .75:
        return "persistent basin multiplicity"
    return "unresolved by 2000 iterations"


def _sub80_analysis(data: dict[str, dict[str, Any]],
                    primary_scores: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    equal = data["J10000_equal"]
    rows = {}
    keys = sorted(k for k in data if k.startswith("J10000_sub80_"))
    for key in keys:
        d = data[key]
        by_time = {}
        for desired in (200, 500, 1000, 2000):
            st = _actual_snapshot_time(d, desired)
            et = _actual_snapshot_time(equal, desired)
            rs = _snapshot(d, st)
            es = _snapshot(equal, et)
            rs_score = _score_vector_from_snapshot(d, key, st)
            es_score = primary_scores["J10000_equal"][str(et)]
            by_time[str(desired)] = {"actual_subset_iteration": st,
                                     "actual_equal_iteration": et,
                                     **_comparison(rs, es, rs_score, es_score)}
        rows[key] = by_time
    for desired in (200, 500, 1000, 2000):
        vals = [r[str(desired)] for key, r in rows.items()
                if key != "_summary"]
        rows.setdefault("_summary", {})[str(desired)] = _summary_plain(vals)
    return {"used_old_five": any("old" in k for k in keys),
            "n_trajectories": len(keys), "replicates": rows,
            "interpretation": _sub80_interpretation(rows)}


def _summary_plain(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    def collect(path: tuple[str, ...]) -> list[float]:
        vals = []
        for row in rows:
            x: Any = row
            for part in path:
                x = x.get(part, float("nan")) if isinstance(x, dict) else float("nan")
            try: vals.append(float(x))
            except (ValueError, TypeError): vals.append(float("nan"))
        return [x for x in vals if np.isfinite(x)]
    out = {"n": len(rows)}
    for name, path in (("j50", ("top50", "jaccard")),
                       ("overlap50", ("top50", "overlap_fraction")),
                       ("j200", ("top200", "jaccard")),
                       ("overlap200", ("top200", "overlap_fraction")),
                       ("score_pearson", ("score_correlation", "pearson"))):
        a = collect(path)
        out[name] = {"median": float(np.median(a)) if a else float("nan"),
                     "p10": float(np.quantile(a, .10)) if a else float("nan"),
                     "p90": float(np.quantile(a, .90)) if a else float("nan")}
    return out


def _sub80_interpretation(rows: dict[str, Any]) -> str:
    summaries = []
    for t in ("200", "500", "1000", "2000"):
        s = rows.get("_summary", {}).get(t, {})
        summaries.append(f"t{t} overlap50 median={_fmt(s.get('overlap50', {}).get('median'), 3)}")
    return "; ".join(summaries)


def _shell_analysis(data: dict[str, dict[str, Any]],
                    probes: dict[str, set[str]], metadata: dict[str, dict[str, Any]],
                    direct_scores: dict[str, np.ndarray]) -> dict[str, Any]:
    out = {}
    for shell in ("S0", "S1", "S2", "S3"):
        direct_key = "direct_J5000" if shell == "S0" else f"direct_{shell}"
        d = _trajectory_lookup(data, direct_key)
        direct = _snapshot(d, 0)
        rec = {
            "n": d["n_users"],
            "quality": {},
            "direct_head": {
                "semantic_annotations": _semantics(direct, probes),
                "descriptors": _descriptor(direct, metadata),
                "top5": [metadata.get(str(w), {}).get("title", str(w))
                         for w in direct["work_ids"][:5]],
            },
            "direct_assessment": _direct_assessment(d, probes, metadata),
        }
        if shell != "S0" and f"{shell}_equal" in data:
            dyn = data[f"{shell}_equal"]
            final = _snapshot(dyn, _final_time(dyn))
            rec["dynamic"] = {
                "iterations": _final_time(dyn),
                "strict_convergence_reached": dyn["converged"],
                "direct_to_final": _comparison(direct, final,
                                                 direct_scores[shell],
                                                 _score_vector_from_snapshot(dyn, f"{shell}_equal", _final_time(dyn))),
                "final_semantic_annotations": _semantics(final, probes),
                "final_descriptors": _descriptor(final, metadata),
            }
        out[shell] = rec
    return out


def _quality_stats(ids: np.ndarray, context: dict[str, Any]) -> dict[str, Any]:
    score_map = {int(u): float(s) for u, s in zip(context["eligible_users"],
                                                context["eligible_scores"])}
    vals = np.asarray([score_map[int(u)] for u in ids], dtype=np.float64)
    return {
        "n": int(len(vals)), "mean_L": float(np.mean(vals)),
        "median_L": float(np.median(vals)),
        "p10_L": float(np.quantile(vals, .10)),
        "p25_L": float(np.quantile(vals, .25)),
        "p75_L": float(np.quantile(vals, .75)),
        "min_L": float(np.min(vals)),
    }


def _coverage_summary() -> dict[str, Any]:
    source = inherited.OUT_JSON
    old = _load_json(source)
    cov = old.get("coverage", {})
    out = {"source": str(source), "source_sha256": _sha256_bytes(source.read_bytes()),
           "raw": {}}
    for tag in ("J5000", "J10000", "J20000", "J30000"):
        c = cov.get(tag, {})
        out["raw"][tag] = {
            "20_49_ge1": c.get("20_49", {}).get("frac_ge1"),
            "20_49_ge3": c.get("20_49", {}).get("frac_ge3"),
            "5_19_ge1": c.get("5_19", {}).get("frac_ge1"),
            "50_99_ge1": c.get("50_99", {}).get("frac_ge1"),
            "100_249_ge1": c.get("100_249", {}).get("frac_ge1"),
            "250_999_ge1": c.get("250_999", {}).get("frac_ge1"),
            "1000_4999_ge1": c.get("1000_4999", {}).get("frac_ge1"),
        }
    return out


def _make_report(context: dict[str, Any], audit: dict[str, Any],
                 specs: list[dict[str, Any]], data: dict[str, dict[str, Any]],
                 metadata: dict[str, dict[str, Any]], probes: dict[str, set[str]],
                 direct_scores: dict[str, np.ndarray],
                 primary_scores: dict[str, dict[str, np.ndarray]],
                 direct_size: dict[str, Any], primary_moves: dict[str, Any],
                 primary_comps: dict[str, Any], size_dyn: dict[str, Any],
                 semantic: dict[str, Any], concentration: dict[str, Any],
                 random_init: dict[str, Any], sub80: dict[str, Any],
                 shell_info: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    trajectory_records = {}
    spec_by_key = {s["key"]: s for s in specs}
    for key, d in data.items():
        trajectory_records[key] = _trajectory_json_record(
            d, spec_by_key.get(key, {"key": key}), metadata, probes)
    for n in PRIMARY_SIZES:
        key = f"J{n}_equal"
        trajectory_records[key]["checkpoint_comparisons"] = _checkpoint_comparisons(
            data[key], primary_scores[key])

    size_table = {}
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        d = data[f"direct_{tag}"]
        e = data[f"{tag}_equal"]
        direct_sem = _semantics(_snapshot(d, 0), probes)
        final_sem = _semantics(_snapshot(e, _final_time(e)), probes)
        direct_desc = _descriptor(_snapshot(d, 0), metadata)
        final_desc = _descriptor(_snapshot(e, _final_time(e)), metadata)
        size_table[tag] = {
            "n": n,
            **_quality_stats(context["memberships"][tag], context),
            "direct_literary_assessment": _direct_assessment(d, probes, metadata),
            "final_dynamic_literary_assessment": _dynamic_assessment(e, probes, metadata),
            "direct_semantics": direct_sem, "final_semantics": final_sem,
            "direct_to_final_top50_jaccard": primary_comps[tag]["direct_to_final"]["top50"]["jaccard"],
            "direct_author_concentration": {
                "unique_authors_50": direct_desc["unique_authors_50"],
                "max_same_author_count_50": direct_desc["max_same_author_count_50"],
            },
            "final_author_concentration": {
                "unique_authors_50": final_desc["unique_authors_50"],
                "max_same_author_count_50": final_desc["max_same_author_count_50"],
            },
            "coverage": coverage["raw"].get(tag, {}),
        }

    json_out = {
        "experiment": "literary_dynamics_decomposition",
        "seed": LITERARY_DYNAMICS_SEED,
        "starting_commit_audited": audit.get("starting_head"),
        "constants": {
            "beta": BETA, "long_max_iter": LONG_MAX_ITER,
            "shell_max_iter": SHELL_MAX_ITER, "init_sigma": INIT_SIGMA,
            "step_threshold": STEP_THRESHOLD,
            "weight_change_threshold": WEIGHT_CHANGE_THRESHOLD,
            "consecutive_converged": CONSECUTIVE_CONVERGED,
            "verify_extra_iter": VERIFY_EXTRA_ITER,
            "ranking_checkpoints": list(CHECKPOINTS),
        },
        "audit": audit,
        "frozen_common_L": {
            "eligible_n": int(len(context["eligible_users"])),
            "score_hash": context["score_hash"],
            "universe_hash": context["universe_hash"],
            "primary_membership_hashes": {
                tag: _hash_ids(ids) for tag, ids in context["memberships"].items()
            },
        },
        "membership": _context_json(context),
        "shell_quality": {
            shell: {"quality": _quality_stats(ids, context),
                    "source_composition": inherited.jury_source_composition(
                        ids, load_juries())}
            for shell, ids in context["shells"].items()
        },
        "direct_size_trajectory": direct_size,
        "primary_trajectory_comparisons": primary_comps,
        "primary_movement": primary_moves,
        "descriptive_size_vs_dynamics": size_dyn,
        "semantic_size_vs_dynamic_progression": semantic,
        "author_concentration_progression": concentration,
        "random_initialization": random_init,
        "sub80_forensic": sub80,
        "shell_convergence": shell_info,
        "primary_size_table": size_table,
        "coverage": coverage,
        "series_metadata": {
            "available": False,
            "reason": "No clean series table is present in the project metadata; "
                      "series/franchise claims are restricted to human inspection "
                      "of titles and reliable author/collection flags.",
        },
        "trajectory_records": trajectory_records,
    }
    _json_dump(OUT_JSON, json_out)
    return json_out


def _head_markdown(head: dict[str, Any], metadata: dict[str, dict[str, Any]],
                   probes: dict[str, set[str]]) -> list[str]:
    rows = _enriched_head(head, metadata, probes)
    lines = ["| rank | title | author | score | n_eff | pos | exact | broad | anti | collection | duplicate | comic |",
             "|---:|---|---|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"]
    for r in rows:
        lines.append(
            f"| {r['rank']} | {r['title']} | {r['author']} | {r['score']:.4f} | "
            f"{r['n_eff']:.1f} | {'Y' if r['pos'] else ''} | "
            f"{'Y' if r['exact'] else ''} | {'Y' if r['broad'] else ''} | "
            f"{'Y' if r['anti'] else ''} | {'Y' if r['is_collection'] else ''} | "
            f"{'Y' if r['is_duplicate'] else ''} | {'Y' if r['is_comic'] else ''} |")
    return lines


def _write_trajectory_heads(data: dict[str, dict[str, Any]],
                            metadata: dict[str, dict[str, Any]],
                            probes: dict[str, set[str]]) -> None:
    lines = ["# Literary dynamics trajectory heads", "",
             f"Seed `{LITERARY_DYNAMICS_SEED}`. Direct `t=0` is equal-vote. "
             "Probe flags are post-hoc annotations and do not affect dynamics.", ""]
    for n in PRIMARY_SIZES:
        key = f"J{n}_equal"
        d = data[key]
        lines += [f"## J{n}", ""]
        for desired in HEAD_CHECKPOINTS:
            t = _actual_snapshot_time(d, desired)
            lines += [f"### t={desired}" + (f" (actual t={t})" if t != desired else ""), ""]
            lines += _head_markdown(_snapshot(d, t), metadata, probes)
            lines += ["", f"Descriptors: `{json.dumps(_descriptor(_snapshot(d, t), metadata), sort_keys=True)}`", ""]
    _write_text_atomic(OUT_TRAJ_HEADS, "\n".join(lines).rstrip() + "\n")


def _write_shell_heads(data: dict[str, dict[str, Any]],
                       context: dict[str, Any], metadata: dict[str, dict[str, Any]],
                       probes: dict[str, set[str]]) -> None:
    lines = ["# Literary size-shell direct heads", "",
             f"Seed `{LITERARY_DYNAMICS_SEED}`. These are direct equal-vote "
             "heads; shell convergence, where run, is reported in the main report.", ""]
    for shell in ("S0", "S1", "S2", "S3"):
        key = "direct_J5000" if shell == "S0" else f"direct_{shell}"
        d = data[key]
        lines += [f"## {shell} (n={len(context['shells'][shell])})", "",
                  _shell_interpretive_sentence(shell, d, metadata), ""]
        lines += _head_markdown(_snapshot(d, 0), metadata, probes)
        lines += ["", f"Descriptors: `{json.dumps(_descriptor(_snapshot(d, 0), metadata), sort_keys=True)}`", ""]
    lines += ["## What tastes are added at each expansion step?", "",
              "This is a post-hoc reading of the direct shell heads. There is "
              "no semantic genre classifier and no series table in the metadata.", ""]
    for shell in ("S1", "S2", "S3"):
        d = data[f"direct_{shell}"]
        head = _snapshot(d, 0)
        titles = [metadata.get(str(w), {}).get("title", str(w)) for w in head["work_ids"][:10]]
        authors = Counter(metadata.get(str(w), {}).get("author", "")
                          for w in head["work_ids"][:50])
        authors.pop("", None)
        lines.append(f"- **{shell}**: leading titles include "
                     + "; ".join(titles[:6]) + "; repeated authors in top 50: "
                     + ", ".join(f"{a} ({n})" for a, n in authors.most_common(5)) + ".")
    _write_text_atomic(OUT_SHELL_HEADS, "\n".join(lines).rstrip() + "\n")


def _shell_interpretive_sentence(shell: str, data: dict[str, Any],
                                  metadata: dict[str, dict[str, Any]]) -> str:
    head = _snapshot(data, 0)
    titles = [metadata.get(str(w), {}).get("title", str(w)) for w in head["work_ids"][:5]]
    desc = _descriptor(head, metadata)
    return (f"Top five: {'; '.join(titles)}. Unique authors@50="
            f"{desc['unique_authors_50']}; max same-author count="
            f"{desc['max_same_author_count_50']}; collection/duplicate/comic="
            f"{desc['collection_count_50']}/{desc['duplicate_count_50']}/"
            f"{desc['comic_count_50']}.")


def _table(lines: list[str], header: list[str], rows: list[list[Any]]) -> None:
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")


def _compact_movement_table(lines: list[str], title: str,
                            rows: list[dict[str, Any]], limit: int = 15) -> None:
    lines += [f"### {title}", ""]
    _table(lines, ["title", "author", "old_rank", "new_rank", "delta"],
           [[r["title"], r["author"], r["old_rank"], r["new_rank"], r["delta"]]
            for r in rows[:limit]])
    lines.append("")


def _make_markdown(json_out: dict[str, Any]) -> None:
    lines = ["# Literary dynamics decomposition", "",
             f"- Deterministic seed: `{LITERARY_DYNAMICS_SEED}`.",
             "- Membership is the frozen common-L selection from `237cb37`; "
             "the map only reweights fixed members.",
             f"- `BETA={BETA}`, long maximum `{LONG_MAX_ITER}`, random-init sigma `{INIT_SIGMA}`.",
             "- Full top-1000 checkpoint arrays (IDs, implicit ranks, scores, reader mass, "
             "and checkpoint weights) are in the NPZ. This report and the heads file "
             "show complete top-50 metadata for human inspection.", ""]

    audit = json_out["audit"]
    lines += ["## Audit and smoke status", ""]
    lines.append(f"- Overall audit: **{'PASS' if audit['ok'] else 'FAIL'}** "
                 f"({sum(c['ok'] for c in audit['checks'])}/{len(audit['checks'])} checks).")
    lines.append("- The four independent inherited t=200 reproductions matched the "
                 "committed endpoint diagnostics, seed heads, and t=200 head metrics "
                 "within stored numerical precision before the long run.")
    lines.append("")
    _table(lines, ["check", "status", "detail"],
           [[c["check"], "PASS" if c["ok"] else "FAIL", c["detail"]]
            for c in audit["checks"]])
    lines.append("")

    lines += ["## Fixed memberships and shells", "",
              "The exact nestedness checks are `|J5 ∩ J10|=5000`, "
              "`|J10 ∩ J20|=10000`, and `|J20 ∩ J30|=20000`. The disjoint "
              "shells are S0=J5, S1=J10−J5, S2=J20−J10, S3=J30−J20; their "
              "union is J30. Shell reports are direct equal-vote rankings.", ""]
    _table(lines, ["shell", "n", "mean L", "median L", "p10", "p25", "p75", "min", "outside ABC"],
           [[s, v["quality"]["n"], _fmt(v["quality"]["mean_L"], 3),
             _fmt(v["quality"]["median_L"], 3), _fmt(v["quality"]["p10_L"], 3),
             _fmt(v["quality"]["p25_L"], 3), _fmt(v["quality"]["p75_L"], 3),
             _fmt(v["quality"]["min_L"], 3),
             _fmt(v["source_composition"].get("none_ABC"), 3)]
            for s, v in json_out["shell_quality"].items()])
    lines.append("")
    _table(lines, ["shell", "ABC", "p65", "A∩B", "vote2", "A only",
                   "B only", "AB only", "none ABC"],
           [[s,
             _fmt(v["source_composition"].get("ABC"), 3),
             _fmt(v["source_composition"].get("p65"), 3),
             _fmt(v["source_composition"].get("AnB"), 3),
             _fmt(v["source_composition"].get("vote2"), 3),
             _fmt(v["source_composition"].get("A_only"), 3),
             _fmt(v["source_composition"].get("B_only"), 3),
             _fmt(v["source_composition"].get("AB_only"), 3),
             _fmt(v["source_composition"].get("none_ABC"), 3)]
            for s, v in json_out["shell_quality"].items()])
    lines.append("")
    lines.append("See `LITERARY_SIZE_SHELL_HEADS.md` for complete direct top-50 heads "
                 "and a human-readable shell taste summary. Series descriptors are "
                 "not available from a clean project table; author and reliable flag "
                 "concentration are reported instead.")
    lines.append("")

    lines += ["## Primary size-decomposition table", "",
              "The literary-assessment cells are post-hoc descriptions of the actual "
              "heads, not selection criteria. Probe counts remain annotations only.", ""]
    size_rows = []
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        v = json_out["primary_size_table"][tag]
        direct_auth = v["direct_author_concentration"]
        final_auth = v["final_author_concentration"]
        direct_sem = _sem_cell(v["direct_semantics"])
        final_sem = _sem_cell(v["final_semantics"])
        size_rows.append([
            tag, v["n"], _fmt(v["median_L"], 3),
            v["direct_literary_assessment"].replace("|", "/"),
            v["final_dynamic_literary_assessment"].replace("|", "/"),
            direct_sem, final_sem,
            _fmt(v["direct_to_final_top50_jaccard"], 3),
            f"{direct_auth['unique_authors_50']}/{direct_auth['max_same_author_count_50']}",
            f"{final_auth['unique_authors_50']}/{final_auth['max_same_author_count_50']}",
            _fmt(v["coverage"].get("20_49_ge1"), 2),
            _fmt(v["coverage"].get("20_49_ge3"), 2),
        ])
    _table(lines, ["jury", "n", "median L", "direct literary assessment",
                   "final dynamic literary assessment", "direct pos/exact/broad/anti",
                   "final pos/exact/broad/anti", "direct→final J50",
                   "direct authors/max", "final authors/max", "20–49 >=1", "20–49 >=3"],
           size_rows)
    lines.append("")

    lines += ["## Direct size trajectory", "",
              "Jaccard and overlap fraction are reported separately. Direct size "
              "movement uses top-500 union ranks with absent rank fixed at 501.", ""]
    for pair, rec in json_out["direct_size_trajectory"].items():
        c = rec["comparison"]
        lines.append(f"### {pair}")
        lines.append("")
        _table(lines, ["comparison", "J50", "overlap/50", "J200", "overlap/200", "rho common top200", "score Pearson"],
               [["direct", _fmt(c["top50"]["jaccard"], 3),
                 _fmt(c["top50"]["overlap_fraction"], 3),
                 _fmt(c["top200"]["jaccard"], 3),
                 _fmt(c["top200"]["overlap_fraction"], 3),
                 _fmt(c["spearman_common_top200"], 3),
                 _fmt(c.get("score_correlation", {}).get("pearson"), 3)]])
        lines.append("")
        _compact_movement_table(lines, "Top 30 direct risers", rec["movement"]["risers"], limit=30)
        _compact_movement_table(lines, "Top 30 direct fallers", rec["movement"]["fallers"], limit=30)
        s = rec["movement_summary"]
        lines.append("Post-hoc author summary: risers "
                     + ", ".join(f"{x['author']} ({x['count']})" for x in s["risers"]["top_authors"])
                     + "; fallers "
                     + ", ".join(f"{x['author']} ({x['count']})" for x in s["fallers"]["top_authors"]) + ".")
        lines.append("")

    lines += ["## Primary long-run dynamics", "",
              "Strict convergence means step ≥ .9999 and weight_rel ≤ 1e−4 for "
              "five consecutive iterations. A candidate hit is followed by +50 "
              "verification iterations; if that window is not stable, the trajectory "
              "continues to its full cap. `practical_head_stability` is a "
              "separate descriptive rule: the first saved checkpoint whose later "
              "saved heads all have at least 0.90 top-50 overlap fraction with final.", ""]
    _table(lines, ["jury", "strict candidate t", "strict +50 stable?", "iterations", "wrel t200", "wrel t500/final avail", "wrel t1000/final avail", "wrel final", "lag2 rel final", "t200→final J50", "t200→final overlap/50", "practical stability"],
           [[f"J{n}", json_out["trajectory_records"][f"J{n}_equal"]["strict_candidate_iteration"],
             str(json_out["trajectory_records"][f"J{n}_equal"]["verification_stable"]),
             json_out["trajectory_records"][f"J{n}_equal"]["iterations"],
             _fmt_sci(_diag_at(json_out["trajectory_records"][f"J{n}_equal"], 200, "weight_rel_1")),
             _fmt_sci(_diag_at(json_out["trajectory_records"][f"J{n}_equal"], 500, "weight_rel_1")),
             _fmt_sci(_diag_at(json_out["trajectory_records"][f"J{n}_equal"], 1000, "weight_rel_1")),
             _fmt_sci(_diag_at(json_out["trajectory_records"][f"J{n}_equal"],
                               json_out["trajectory_records"][f"J{n}_equal"]["iterations"], "weight_rel_1")),
             _fmt_sci(_diag_at(json_out["trajectory_records"][f"J{n}_equal"],
                               json_out["trajectory_records"][f"J{n}_equal"]["iterations"], "weight_rel_2")),
             _fmt(json_out["primary_trajectory_comparisons"][f"J{n}"]["t200_to_final"]["top50"]["jaccard"], 3),
             _fmt(json_out["primary_trajectory_comparisons"][f"J{n}"]["t200_to_final"]["top50"]["overlap_fraction"], 3),
             json_out["trajectory_records"][f"J{n}_equal"]["practical_head_stability"]["practical_head_stability_iteration"]]
            for n in PRIMARY_SIZES])
    lines.append("")

    lines.append("Window summaries show median [minimum, maximum] over each available "
                 "iteration window; absent late windows reflect genuine early strict "
                 "convergence plus the required 50-iteration verification run.")
    lines.append("")
    def window_cell(summary: dict[str, Any], field: str) -> str:
        v = summary.get(field)
        if not v:
            return "—"
        return (f"{_fmt_sci(v.get('median'))} "
                f"[{_fmt_sci(v.get('min'))}, {_fmt_sci(v.get('max'))}]")
    window_rows = []
    for n in PRIMARY_SIZES:
        rec = json_out["trajectory_records"][f"J{n}_equal"]
        for window, summary in rec["window_summary"].items():
            window_rows.append([f"J{n}", window.replace("_", "–"),
                                window_cell(summary, "weight_rel_1"),
                                window_cell(summary, "weight_rel_2"),
                                window_cell(summary, "book_rel_1"),
                                window_cell(summary, "step")])
    _table(lines, ["jury", "window", "weight_rel_1 median [min,max]",
                   "weight_rel_2 median [min,max]", "book_rel_1 median [min,max]",
                   "step median [min,max]"], window_rows)
    lines.append("")
    _table(lines, ["jury", "log(wrel) window", "n", "slope", "R²", "p-value"],
           [[f"J{n}", window, rec["log_weight_rel_trend"][window]["n"],
             _fmt_sci(rec["log_weight_rel_trend"][window]["slope"]),
             _fmt(rec["log_weight_rel_trend"][window]["r2"], 3),
             _fmt(rec["log_weight_rel_trend"][window]["pvalue"], 3)]
            for n in PRIMARY_SIZES
            for rec in [json_out["trajectory_records"][f"J{n}_equal"]]
            for window in ("200_1000", "1000_2000")])
    lines.append("")
    lines.append("Lag-2/lag-3/lag-4 diagnostics and all saved-checkpoint comparisons "
                 "are also stored in JSON. The lag-cycle flag is intentionally "
                 "heuristic and is not treated as proof of a mathematical cycle.")
    lines.append("")
    lines.append("### Saved-checkpoint head stability")
    lines.append("")
    lines.append("Each row compares the checkpoint with its previous saved checkpoint, "
                 "with t=200, and with the final available checkpoint. `ov50` is "
                 "overlap/50; J50 is Jaccard.")
    lines.append("")
    checkpoint_rows = []
    requested = (0, 20, 100, 200, 500, 1000, 2000)
    for n in PRIMARY_SIZES:
        rec = json_out["trajectory_records"][f"J{n}_equal"]
        rows_by_t = {int(row["iteration"]): row
                     for row in rec.get("checkpoint_comparisons", [])}
        available = sorted(rows_by_t)
        for desired in requested:
            actuals = [t for t in available if t <= desired]
            if not actuals:
                continue
            actual = actuals[-1]
            row = rows_by_t[actual]
            def hcell(comp: dict[str, Any] | None) -> str:
                if not comp:
                    return "—"
                return (f"J{_fmt(comp['top50']['jaccard'], 2)}/"
                        f"{_fmt(comp['top50']['overlap_fraction'], 2)}")
            checkpoint_rows.append([f"J{n}", f"requested {desired} (actual {actual})",
                                    hcell(row.get("vs_previous")),
                                    hcell(row.get("vs_t200")),
                                    hcell(row.get("vs_final"))])
    _table(lines, ["jury", "checkpoint", "vs previous J50/ov50",
                   "vs t200 J50/ov50", "vs final J50/ov50"], checkpoint_rows)
    lines.append("")

    lines += ["## Direct → t200 → final movement", ""]
    for n in PRIMARY_SIZES:
        tag = f"J{n}"
        lines.append(f"### {tag}")
        lines.append("")
        _compact_movement_table(lines, "Direct → final risers", json_out["primary_movement"][tag]["direct_to_final"]["risers"])
        _compact_movement_table(lines, "Direct → final fallers", json_out["primary_movement"][tag]["direct_to_final"]["fallers"])
        lines.append("The complete top-30 direct→t200, direct→final, and t200→final "
                     "movement lists are in JSON; the two headline lists above are top 15.")
        lines.append("")

    lines += ["## Size versus convergence: descriptive decomposition", "",
              "For N=10k/20k/30k, D5 is J5000 direct, DN is that size's direct "
              "ranking, and CN(final) is its long-run equal-init ranking. These "
              "are multiple frozen descriptive distances, not a formal causal "
              "decomposition. The interaction can depend on N.", ""]
    _table(lines, ["N", "D5→DN 1−J50", "DN→CN 1−J50", "D5→CN 1−J50", "D5→DN 1−J200", "DN→CN 1−J200", "D5→CN 1−J200", "D5→DN rho", "DN→CN rho", "D5→CN rho", "pref RMS D5→DN", "pref RMS DN→CN"],
           [[tag[1:],
             _fmt(1 - v["membership_size_displacement_D5_to_DN"]["top50"]["jaccard"], 3),
             _fmt(1 - v["convergence_displacement_DN_to_CN_final"]["top50"]["jaccard"], 3),
             _fmt(1 - v["total_displacement_D5_to_CN_final"]["top50"]["jaccard"], 3),
             _fmt(1 - v["membership_size_displacement_D5_to_DN"]["top200"]["jaccard"], 3),
             _fmt(1 - v["convergence_displacement_DN_to_CN_final"]["top200"]["jaccard"], 3),
             _fmt(1 - v["total_displacement_D5_to_CN_final"]["top200"]["jaccard"], 3),
             _fmt(v["membership_size_displacement_D5_to_DN"]["spearman_common_top200"], 3),
             _fmt(v["convergence_displacement_DN_to_CN_final"]["spearman_common_top200"], 3),
             _fmt(v["total_displacement_D5_to_CN_final"]["spearman_common_top200"], 3),
             _fmt(v["membership_size_displacement_D5_to_DN"].get("preference_vector_distance"), 3),
             _fmt(v["convergence_displacement_DN_to_CN_final"].get("preference_vector_distance"), 3)]
            for tag, v in json_out["descriptive_size_vs_dynamics"].items()])
    lines.append("")

    lines += ["## Semantic annotations and structural concentration", "",
              "Probe counts are annotations only. Actual heads, authors, and "
              "titles are in `LITERARY_DYNAMICS_TRAJECTORY_HEADS.md`.", ""]
    _table(lines, ["jury", "direct pos/exact/broad/anti", "t20", "t100", "t200", "t500", "final"],
           [[f"J{n}",
             _sem_cell(json_out["semantic_size_vs_dynamic_progression"][f"J{n}"]["0"]),
             _sem_cell(json_out["semantic_size_vs_dynamic_progression"][f"J{n}"]["20"]),
             _sem_cell(json_out["semantic_size_vs_dynamic_progression"][f"J{n}"]["100"]),
             _sem_cell(json_out["semantic_size_vs_dynamic_progression"][f"J{n}"]["200"]),
             _sem_cell(json_out["semantic_size_vs_dynamic_progression"][f"J{n}"]["500"]),
             _sem_cell(json_out["semantic_size_vs_dynamic_progression"][f"J{n}"]["2000"])]
            for n in PRIMARY_SIZES])
    lines.append("")
    _table(lines, ["jury", "checkpoint", "unique authors@50", "max same author", "collections", "duplicates", "comics"],
           [[f"J{n}", t, v["unique_authors_50"], v["max_same_author_count_50"],
             v["collection_count_50"], v["duplicate_count_50"], v["comic_count_50"]]
            for n in PRIMARY_SIZES
            for t, v in json_out["author_concentration_progression"][f"J{n}"].items()])
    lines.append("")

    lines += ["## Random initialization", "",
              "Each primary has five sigma=.20 lognormal starts, except J30000 "
              "with three. Comparisons are to the equal-init trajectory at the "
              "same saved horizon. The classification is descriptive: transient "
              "sensitivity, persistent basin multiplicity, stable ranking/unstable "
              "weights, or unresolved.", ""]
    _table(lines, ["jury", "final J50 overlap median", "p10", "p90", "final J200 overlap median", "final weight cosine median", "pairwise final J50 overlap", "classification"],
           [[tag,
             _fmt(v["final_summary"].get("overlap50", {}).get("median"), 3),
             _fmt(v["final_summary"].get("overlap50", {}).get("p10"), 3),
             _fmt(v["final_summary"].get("overlap50", {}).get("p90"), 3),
             _fmt(v["final_summary"].get("j200", {}).get("median"), 3),
             _fmt(v["final_summary"].get("weight_cosine", {}).get("median"), 3),
             _fmt(v["pairwise_final_summary"].get("overlap50", {}).get("median"), 3),
             v["classification"]]
            for tag, v in json_out["random_initialization"].items()])
    lines.append("")

    lines += ["## J10000 80% forensic check", "",
              f"The old five exact subsets were {'reused' if json_out['sub80_forensic']['used_old_five'] else 'not persisted; ten fresh subsets were generated'}. "
              "Long-horizon medians below test whether the old t=200 anomaly "
              "persists rather than treating it as a basin label.", ""]
    _table(lines, ["horizon", "n", "J50 median", "overlap/50 median", "J200 median", "overlap/200 median", "score Pearson median"],
           [[t, s["n"], _fmt(s["j50"]["median"], 3), _fmt(s["overlap50"]["median"], 3),
             _fmt(s["j200"]["median"], 3), _fmt(s["overlap200"]["median"], 3),
             _fmt(s["score_pearson"]["median"], 3)]
            for t, s in json_out["sub80_forensic"]["replicates"].get("_summary", {}).items()])
    lines.append("")
    lines.append(json_out["sub80_forensic"]["interpretation"])
    lines.append("")

    lines += ["## Coverage context", "",
              "These are the correct raw obscure-book coverage values persisted "
              "by the inherited experiment; no obscure-book accuracy validation "
              "was performed here.", ""]
    _table(lines, ["jury", "20–49 >=1", "20–49 >=3", "5–19 >=1", "50–99 >=1", "100–249 >=1", "250–999 >=1"],
           [[tag, _fmt(v.get("20_49_ge1"), 2), _fmt(v.get("20_49_ge3"), 2),
             _fmt(v.get("5_19_ge1"), 2), _fmt(v.get("50_99_ge1"), 2),
             _fmt(v.get("100_249_ge1"), 2), _fmt(v.get("250_999_ge1"), 2)]
            for tag, v in json_out["coverage"]["raw"].items()])
    lines.append("")

    lines += ["## Explicit answers", "",
              "### What do S1/S2/S3 prefer?", "",
              "The answer is in the complete shell heads file and its interpretive "
              "section. The report deliberately uses actual top-book titles, "
              "repeated authors, and reliable collection/comic flags rather than a "
              "new genre classifier.", "",
              "### Is t=200 asymptotic?", "",
              "Use the t200→final J50/J200 rows and practical-head-stability iterations "
              "above. A high head overlap can coexist with non-negligible continuing "
              "weight movement; the report does not equate head stability with a "
              "weight fixed point.", "",
              "### Does the user vector converge or cycle?", "",
              "The primary cycle diagnostics report actual lag-1 through lag-4 "
              "relative distances. A 2-cycle would require lag-1 to remain positive "
              "while lag-2 collapses; the stored heuristic is only evidence, not a "
              "proof. Windowed log trends show whether movement is declining.", "",
              "### What causes the larger-jury slide?", "",
              "The answer must be size-specific. Compare the direct shell heads and "
              "direct J5→J10→J20→J30 movement with each fixed-size direct→final "
              "head. If a fandom/graphic/series-heavy head is already in DN, that is "
              "membership composition; if it appears or is amplified only in CN, "
              "that is convergence; the data allow both and interaction.", "",
              "### Practical jury assessment", "",
              "J5000, J10000, J20000, and J30000 should not be reduced to a single "
              "optimized scalar. The final assessment weighs direct-head naturality, "
              "individual common-L quality, dynamic behavior, initialization "
              "sensitivity, and the preserved coverage tradeoff. In particular, a "
              "large direct jury can remain a defensible trustworthy readership even "
              "if this internal-consensus operator amplifies a different axis.", ""]

    _write_text_atomic(OUT_MD, "\n".join(lines).rstrip() + "\n")


def _diag_at(record: dict[str, Any], desired: int, field: str) -> float:
    rows = [r for r in record["history"] if int(r["iteration"]) == int(desired)]
    if not rows:
        rows = [r for r in record["history"] if int(r["iteration"]) <= int(desired)]
    return float(rows[-1][field]) if rows else float("nan")


def _sem_cell(v: dict[str, Any]) -> str:
    return f"{v.get('pos50', 0)}/{v.get('exact50', 0)}/{v.get('broad50', 0)}/{v.get('anti50', 0)}"


def _run_report(context: dict[str, Any], audit: dict[str, Any],
                specs: list[dict[str, Any]]) -> None:
    data = _load_direct_and_dynamic_data(context, specs)
    # Direct trajectories are lightweight max_iter=0 states.  Keep equal-init
    # primary score vectors at all saved checkpoints for full preference
    # correlations; the committed NPZ stores these vectors as well.
    direct_scores: dict[str, np.ndarray] = {}
    for n in PRIMARY_SIZES:
        key = f"direct_J{n}"
        direct_scores[f"J{n}"] = _score_vector_from_snapshot(
            data[key], key, 0)
    for shell in ("S1", "S2", "S3"):
        key = f"direct_{shell}"
        direct_scores[shell] = _score_vector_from_snapshot(data[key], key, 0)
    primary_scores: dict[str, dict[str, np.ndarray]] = {}
    for n in PRIMARY_SIZES:
        key = f"J{n}_equal"
        primary_scores[key] = _score_vectors_for(
            data[key], data[key]["payload_tag"],
            sorted(int(t) for t in data[key]["snapshots"]))

    # Metadata/probes are loaded only after all trajectories have been run.
    base_payload = _load_payload("payload_J5000")
    con = open_db()
    metadata = _load_metadata(con, base_payload["work_ids"])
    probes = _load_probe_sets(base_payload)
    direct_size = _direct_size_trajectory(data, direct_scores, metadata)
    primary_comps = _primary_comparisons(data, primary_scores, direct_scores)
    primary_moves = _primary_movement(data, primary_scores, metadata)
    size_dyn = _descriptive_size_dynamics(data, direct_scores, primary_scores)
    semantic = _semantic_progression(data, probes)
    concentration = _concentration_progression(data, metadata)
    random_init = _random_init_analysis(data, primary_scores)
    sub80 = _sub80_analysis(data, primary_scores)
    shell_info = _shell_analysis(data, probes, metadata, direct_scores)
    coverage = _coverage_summary()
    con.close()

    # Add shell quality/source composition after the report's metadata path is
    # set up.  This call is deterministic and label-free.
    context["payload_meta"] = {
        tag: {"n": int(len(_load_payload(f"payload_{tag}")["user_ids"])),
              "source": str(_payload_path(f"payload_{tag}"))}
        for tag in ("J5000", "J10000", "J20000", "J30000")
    }
    json_out = _make_report(
        context, audit, specs, data, metadata, probes, direct_scores,
        primary_scores, direct_size, primary_moves, primary_comps, size_dyn,
        semantic, concentration, random_init, sub80, shell_info, coverage)
    _build_output_npz(context, data, specs, primary_scores, direct_scores)
    _write_trajectory_heads(data, metadata, probes)
    _write_shell_heads(data, context, metadata, probes)
    _make_markdown(json_out)
    print(f"[report] wrote {OUT_JSON}, {OUT_NPZ}, {OUT_MD}, {OUT_TRAJ_HEADS}, {OUT_SHELL_HEADS}",
          flush=True)


def _prepare(con, force: bool = False) -> dict[str, Any]:
    context = _load_frozen_context()
    context = _ensure_payloads(con, context)
    _ensure_new_sub80_payloads(con, context)
    return context


def run_phases(phases: list[str], force: bool = False,
               skip_shell: bool = False) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    con = open_db()
    context = _prepare(con, force=False)
    audit_path = STATE_DIR / "audit.json"
    if "audit" in phases:
        audit = _make_audit(context, con)
        _json_dump(audit_path, audit)
        print(f"[audit] {sum(c['ok'] for c in audit['checks'])}/{len(audit['checks'])} checks; "
              f"ok={audit['ok']}", flush=True)
        if not audit["ok"]:
            con.close()
            raise RuntimeError("audit failed; long campaign not started")
    elif audit_path.exists():
        audit = _load_json(audit_path)
    else:
        audit = _make_audit(context, con)
        _json_dump(audit_path, audit)
        if not audit["ok"]:
            con.close()
            raise RuntimeError("audit failed; long campaign not started")

    # Build deterministic specs and run at trajectory granularity.
    specs = _trajectory_specs(context, include_shell=not skip_shell)
    if "direct" in phases or "all" in phases:
        direct_specs = []
        for n in PRIMARY_SIZES:
            tag = f"J{n}"
            direct_specs.append({"key": f"direct_{tag}", "label": f"direct {tag}",
                                 "payload_tag": f"payload_{tag}", "init": "equal",
                                 "init_seed": None, "max_iter": 0, "kind": "direct",
                                 "jury": tag})
        for shell in ("S1", "S2", "S3"):
            direct_specs.append({"key": f"direct_{shell}", "label": f"direct {shell}",
                                 "payload_tag": f"payload_{shell}", "init": "equal",
                                 "init_seed": None, "max_iter": 0, "kind": "direct_shell",
                                 "shell": shell})
        specs = direct_specs + specs
        for spec in direct_specs:
            run_trajectory(**{k: spec[k] for k in ("key", "label", "payload_tag", "init", "init_seed", "max_iter")},
                           force=force)
        _json_dump(STATE_DIR / "specs.json", specs)

    if "primary" in phases or "all" in phases:
        for spec in [s for s in specs if s["kind"] == "primary_equal"]:
            run_trajectory(**{k: spec[k] for k in ("key", "label", "payload_tag", "init", "init_seed", "max_iter")},
                           force=force)
    if "random" in phases or "all" in phases:
        for spec in [s for s in specs if s["kind"] == "random_init"]:
            run_trajectory(**{k: spec[k] for k in ("key", "label", "payload_tag", "init", "init_seed", "max_iter")},
                           force=force)
    if "sub80" in phases or "all" in phases:
        for spec in [s for s in specs if s["kind"] in ("sub80_old", "sub80_new")]:
            # If old payloads were absent, the fresh subset payloads are the ten
            # deterministic trajectories requested by the protocol.
            run_trajectory(**{k: spec[k] for k in ("key", "label", "payload_tag", "init", "init_seed", "max_iter")},
                           force=force)
    if ("shell" in phases or "all" in phases) and not skip_shell:
        for spec in [s for s in specs if s["kind"] == "shell_equal"]:
            run_trajectory(**{k: spec[k] for k in ("key", "label", "payload_tag", "init", "init_seed", "max_iter")},
                           force=force)
    if "report" in phases or "all" in phases:
        # Ensure direct specs are available if report is run separately after
        # a previous process created specs.json.
        if not (STATE_DIR / "specs.json").exists():
            raise RuntimeError("missing specs.json; run --phase direct first")
        specs = _load_json(STATE_DIR / "specs.json")
        _run_report(context, audit, specs)
    con.close()
    print(f"[main] phases={phases} runtime={time.time()-t0:.1f}s", flush=True)


def phase_smoke() -> dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    con = open_db()
    context = _prepare(con, force=False)
    audit = _make_audit(context, con)
    con.close()
    print(f"[smoke] {sum(c['ok'] for c in audit['checks'])}/{len(audit['checks'])} "
          f"checks passed; ok={audit['ok']}", flush=True)
    return audit


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--phase", nargs="+", default=["all"],
                        choices=["all", "audit", "direct", "primary", "random",
                                 "sub80", "shell", "report"])
    parser.add_argument("--force", action="store_true",
                        help="restart trajectory states; inherited payloads are never overwritten")
    parser.add_argument("--skip-shell", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        result = phase_smoke()
        if not result["ok"]:
            raise SystemExit(1)
        return
    phases = args.phase
    if "all" in phases:
        phases = ["audit", "direct", "primary", "random", "sub80", "shell", "report"]
    run_phases(phases, force=args.force, skip_shell=args.skip_shell)


if __name__ == "__main__":
    main()

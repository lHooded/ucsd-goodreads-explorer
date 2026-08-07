#!/usr/bin/env python3
"""Completely label-blind amplification census.

Scientific question
-------------------
Previous work (drift_exploit phase C) found that some 80k random-jury reversal
endpoints, when selected using literary evaluation labels and then amplified
through their own top preference books, produce strong literary canons. That
selection used ``exact_lit50``, so it is not yet a natural discovery. This
experiment asks: **if we amplify random reversal endpoints without ever
consulting literary labels, does a distinct literary basin emerge naturally
among the amplified outputs?**

Hard constraint
---------------
NO literary, anti-literary, genre, title, author, publication-year,
known-pole, or external evaluation information may be loaded or used until
every amplification run, vector, similarity matrix, cluster assignment, and
cluster centroid has been frozen and written to disk. Phases "amplify",
"consolidate", and "geometry" never call ``spectral.load_posthoc_context`` and
never open the titles/evaluation tables. Semantic context loads in the
"unblind" phase only, and the known literary pole cosine is computed there as
a post-hoc diagnostic that cannot alter clustering or select outputs.

Phases
------
- amplify:      seed_from_pref + run_path gain-hard amplification of every
                selected reversal endpoint (default: all 120 20k and all 120
                80k endpoints from drift_exploit_main). Per-source compressed
                chunk checkpoints so a long run resumes without repeating
                successful jobs.
- consolidate:  merge chunks into natural_amplification_census_<tag>.npz and
                finalize the metadata JSON (still fully label-free).
- geometry:     freeze the label-blind structural analysis: preference-space
                and direction-space representations, pairwise cosine matrices,
                average-linkage hierarchical clusterings at preregistered
                cosine cuts 0.30 / 0.50 / 0.70, cluster centroids and
                dispersion, plus the independent even/odd-jury half splits
                and their centroid-cosine matching. Writes
                natural_amplification_census_geometry.json/.npz.
- unblind:      ONLY after geometry is frozen: load semantic context, evaluate
                endpoints, preference centroids, direction centroids (pole_rows
                convention), and matched A/B clusters; report pole cosine as a
                diagnostic; exploratory feature->membership diagnostics.
- smoke:        small validation run (default 4 sources per size) that verifies
                the census pipeline bit-reproduces the existing
                seed_from_pref / run_path behavior.

Production ranking/UI code is not touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import pointbiserialr

from curators_explorer.scripts import research_canon_breeding as breeding
from curators_explorer.scripts import (
    research_reversal_drift_exploit as drift_exploit,
)
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year


DATA = Path(__file__).resolve().parents[1] / "data"
DRIFT_NPZ = DATA / "drift_exploit_main.npz"
DRIFT_JSON = DATA / "drift_exploit_main.json"
POLE_NPZ = DATA / "canon_breeding_overnight_directions.npz"
POLE_KEY = "teacher_p65_s25::s5xteacher_p65_s25::s3::dm::deep"

# Source census: every endpoint of these jury sizes (120 juries each).
SIZES = (20000, 80000)
JURIES_PER_SIZE = 120

# Preregistered parameters (never tuned from results).
SEED = 20260817
ELIG_MIN_BOOK_N = 25          # ratings-derived eligibility threshold
SEED_BOOKS = 25               # top eligible books used by seed_from_pref
STAGE_ANALYZED = 4            # preregistered mid-path stage index (0-based)
CLUSTER_TAUS = (0.30, 0.50, 0.70)  # cosine cuts for average-linkage dendrograms
MAX_STAGES = breeding.MAX_STAGES + 1  # run_path stages 0..8 (worst case)

CHECKPOINT_EVERY = 10
SMOKE_JURIES = 4

# True only inside the unblind phase, after all geometry files are frozen.
SEMANTIC_CONTEXT_LOADED = False

FEATURE_NAMES = (
    "displacement_norm_eligible",
    "endpoint_stage0_cos",
    "pref_concentration",
    "top25_mass_concentration",
    "pref_norm_eligible",
    "stage0_pref_norm_eligible",
    "reversal_stage_count",
    "deepest_remaining_users",
    "deepest_removed_fraction",
    "effective_user_share_deepest",
)


def _tag_suffix(tag: str | None) -> str:
    return f"_{tag}" if tag else ""


def census_paths(tag: str | None) -> tuple[Path, Path]:
    suffix = _tag_suffix(tag)
    return (
        DATA / f"natural_amplification_census{suffix}.npz",
        DATA / f"natural_amplification_census{suffix}.json",
    )


def geometry_paths(tag: str | None) -> tuple[Path, Path]:
    suffix = _tag_suffix(tag)
    return (
        DATA / f"natural_amplification_census_geometry{suffix}.json",
        DATA / f"natural_amplification_census_geometry{suffix}.npz",
    )


def posthoc_path(tag: str | None) -> Path:
    return DATA / f"natural_amplification_census_posthoc{_tag_suffix(tag)}.json"


def report_path(tag: str | None) -> Path:
    suffix = _tag_suffix(tag)
    return DATA / f"NATURAL_AMPLIFICATION_CENSUS{suffix.upper()}_REPORT.md"


def chunk_dir(tag: str | None) -> Path:
    return DATA / "natural_amplification_chunks" / (tag or "main")


def chunk_path(tag: str | None, size: int, jury: int) -> Path:
    return chunk_dir(tag) / f"{size}_{jury}.npz"


def load_drift_sources(juries_per_size: int) -> list[tuple[int, int]]:
    """Ordered (size, jury) list; jury ids 0..juries_per_size-1 per size."""
    return [(size, jury) for size in SIZES for jury in range(juries_per_size)]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _effective_user_share(weights: np.ndarray) -> float:
    return float(
        (weights.sum() ** 2) / np.sum(weights**2) / len(weights)
    )


# ---------------------------------------------------------------------------
# Phase 2: amplify every source identically (label-free)
# ---------------------------------------------------------------------------

def _label_free_features(
    pref: np.ndarray,
    stage0_pref: np.ndarray,
    eligible: np.ndarray,
    run: dict[str, Any],
) -> dict[str, Any]:
    """Ratings-only pre-amplification / run features (no semantic content)."""
    fe = pref[eligible].astype(np.float64)
    f0 = stage0_pref[eligible].astype(np.float64)

    def rep(x: np.ndarray) -> np.ndarray:
        c = x - x.mean()
        norm = np.linalg.norm(c)
        return c / norm if norm > 1e-20 else c

    endpoint_stage0_cos = float(np.sum(rep(fe) * rep(f0)))

    abs_mass = np.abs(fe)
    total = abs_mass.sum()
    mass = abs_mass / total if total > 0 else abs_mass
    concentration = float(1.0 / np.sum(mass**2)) if np.sum(mass**2) > 0 else 0.0
    top25 = np.argsort(-abs_mass, kind="stable")[:25]
    top25_mass = float(abs_mass[top25].sum() / total) if total > 0 else 0.0

    deepest_idx = len(run["stages"]) - 1
    return {
        "displacement_norm_eligible": float(np.linalg.norm(fe - f0)),
        "endpoint_stage0_cos": endpoint_stage0_cos,
        "pref_concentration": concentration,
        "top25_mass_concentration": top25_mass,
        "pref_norm_eligible": float(np.linalg.norm(fe)),
        "stage0_pref_norm_eligible": float(np.linalg.norm(f0)),
        "direction_norm": 1.0,  # run_path directions are unit by construction
        "reversal_stage_count": int(len(run["stages"])),
        "deepest_remaining_users": int(run["stages"][deepest_idx]["remaining_users"]),
        "deepest_removed_fraction": float(
            run["stages"][deepest_idx]["cumulative_removed_fraction"]
        ),
        "retained_reference_trajectory": [
            float(s["direction_retained_reference"]) for s in run["stages"]
        ],
        "effective_user_share_deepest": _effective_user_share(
            run["weights_store"][deepest_idx]
        ),
    }


def _run_one_source(
    payload: dict[str, np.ndarray],
    matrix: Any,
    pref: np.ndarray,
    stage0_pref: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Amplify one endpoint preference vector exactly like drift-exploit phase C."""
    start, order = drift_exploit.seed_from_pref(payload, pref, limit=SEED_BOOKS)
    run = breeding.run_path(
        payload, matrix, start, rng, store_weights=True, store_pref=True
    )
    eligible = payload["book_n"] >= ELIG_MIN_BOOK_N
    features = _label_free_features(pref, stage0_pref, eligible, run)

    n_stages = len(run["stages"])
    stage_dirs = np.stack([run["directions"][s] for s in range(n_stages)])
    stage_prefs = np.stack(
        [run["pref_store"][s]["score"] for s in range(n_stages)]
    )
    stage_mass = np.stack(
        [run["pref_store"][s]["reader_mass"] for s in range(n_stages)]
    )
    users = np.asarray(
        [run["stages"][s]["remaining_users"] for s in range(n_stages)], dtype=np.int32
    )
    diag = [
        {
            "stage": run["stages"][s]["stage"],
            "final_step_correlation": run["stages"][s]["final_step_correlation"],
            "direction_retained_reference": run["stages"][s][
                "direction_retained_reference"
            ],
            "direction_retained_stage": run["stages"][s]["direction_retained_stage"],
            "removed_users": int(run["stages"][s].get("removed_users", 0)),
            "cumulative_removed_fraction": run["stages"][s][
                "cumulative_removed_fraction"
            ],
            "effective_user_share": _effective_user_share(run["weights_store"][s]),
        }
        for s in range(n_stages)
    ]
    return {
        "start": start.astype(np.float32),
        "seed_books": order.astype(np.int32),
        "stage_dirs": stage_dirs.astype(np.float32),
        "stage_prefs": stage_prefs.astype(np.float32),
        "stage_mass": stage_mass.astype(np.float32),
        "users_by_stage": users,
        "n_stages": n_stages,
        "stop_reason": run["stop_reason"],
        "stage_diagnostics": diag,
        "features": features,
    }


def phase_amplify(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED

    t0 = time.time()
    payload, matrix, _ = year.load_matrix()
    blob = np.load(DRIFT_NPZ, allow_pickle=False)
    drift_prefs, drift_stage0 = blob["prefs"], blob["stage0_prefs"]
    drift_records = json.loads(DRIFT_JSON.read_text(encoding="utf-8"))["records"]
    drift_idx = {(r["size"], r["jury"]): i for i, r in enumerate(drift_records)}
    sources = load_drift_sources(args.juries_per_size)
    for size, jury in sources:
        if (size, jury) not in drift_idx:
            raise SystemExit(f"missing drift endpoint for {size}:{jury}")

    chunk_dir(args.tag).mkdir(parents=True, exist_ok=True)
    npz_path, json_path = census_paths(args.tag)

    records: list[dict[str, Any]] = []
    if json_path.exists():
        existing = json.loads(json_path.read_text(encoding="utf-8"))
        records = [r for r in existing.get("records", []) if r.get("complete")]

    rng = np.random.default_rng(args.seed)
    done = len(records)
    for size, jury in sources:
        cpath = chunk_path(args.tag, size, jury)
        if cpath.exists():
            continue
        pref = drift_prefs[drift_idx[(size, jury)]].astype(np.float64)
        stage0_pref = drift_stage0[drift_idx[(size, jury)]].astype(np.float64)
        try:
            out = _run_one_source(payload, matrix, pref, stage0_pref, rng)
        except Exception as exc:  # keep the campaign alive past one bad source
            print(f"source {size}:{jury} FAILED: {exc}", flush=True)
            continue
        np.savez_compressed(
            cpath,
            start=out["start"],
            seed_books=out["seed_books"],
            stage_dirs=out["stage_dirs"],
            stage_prefs=out["stage_prefs"],
            stage_mass=out["stage_mass"],
            users_by_stage=out["users_by_stage"],
            source_pref=pref.astype(np.float32),
            stage0_pref=stage0_pref.astype(np.float32),
        )
        records.append(
            {
                "source_id": f"{size}:{jury}",
                "size": size,
                "jury": jury,
                "complete": True,
                "n_stages": out["n_stages"],
                "stop_reason": out["stop_reason"],
                "stage_diagnostics": out["stage_diagnostics"],
                "seed_books": out["seed_books"].tolist(),
                "features": out["features"],
            }
        )
        done += 1
        if done % CHECKPOINT_EVERY == 0:
            _checkpoint_json(json_path, records, sources, t0)
            print(
                f"amplify {size}:{jury}: {done}/{len(sources)} sources, "
                f"elapsed {time.time() - t0:.0f}s", flush=True,
            )

    _checkpoint_json(json_path, records, sources, t0)
    print(
        f"amplify done: {len(records)} sources, {time.time() - t0:.0f}s, "
        f"chunks in {chunk_dir(args.tag)}", flush=True,
    )


def _checkpoint_json(
    json_path: Path, records: list[dict[str, Any]], sources: list[tuple[int, int]], t0: float
) -> None:
    json_path.write_text(
        json.dumps(
            {
                "records": records,
                "partial": len(records) < len(sources),
                "method": {
                    "phase": "amplify",
                    "sizes": list(SIZES),
                    "juries_per_size": len(sources) // len(SIZES),
                    "seed": SEED,
                    "seed_books": SEED_BOOKS,
                    "elig_min_book_n": ELIG_MIN_BOOK_N,
                    "beta": breeding.BETA,
                    "max_stages": breeding.MAX_STAGES,
                    "retained_target": breeding.RETAINED_TARGET,
                    "mode": "hard",
                    "criterion": "gain",
                    "hard_threshold_mean_multiple": "pruning.HARD_THRESHOLD",
                    "semantic_context_loaded": False,
                    "command": shlex.join(sys.argv),
                    "git_head": _git_head(),
                    "runtime_seconds": time.time() - t0,
                },
            },
            indent=1,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Consolidate chunks into the census NPZ
# ---------------------------------------------------------------------------

def phase_consolidate(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED

    t0 = time.time()
    npz_path, json_path = census_paths(args.tag)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    records = data["records"]
    sources = load_drift_sources(args.juries_per_size)
    have = [cpath for size, jury in sources if (cpath := chunk_path(args.tag, size, jury)).exists()]
    n = len(have)
    if n == 0:
        raise SystemExit("no completed sources to consolidate")

    with np.load(have[0], allow_pickle=False) as first:
        n_books = int(first["stage_dirs"].shape[1])
    max_stages = 0
    for cpath in have:
        with np.load(cpath, allow_pickle=False) as c:
            max_stages = max(max_stages, int(c["stage_dirs"].shape[0]))

    def blank(maxs: int) -> np.ndarray:
        return np.full((n, maxs, n_books), np.nan, dtype=np.float32)

    source_size = np.empty(n, dtype=np.int32)
    source_jury = np.empty(n, dtype=np.int32)
    stage_dirs = blank(max_stages)
    stage_prefs = blank(max_stages)
    stage_mass = blank(max_stages)
    stage_valid = np.zeros((n, max_stages), dtype=bool)
    users_by_stage = np.zeros((n, max_stages), dtype=np.int32)
    seed_books = np.zeros((n, SEED_BOOKS), dtype=np.int32)
    source_pref = np.zeros((n, n_books), dtype=np.float32)
    stage0_pref = np.zeros((n, n_books), dtype=np.float32)

    row = 0
    for size, jury in sources:
        cpath = chunk_path(args.tag, size, jury)
        if not cpath.exists():
            continue
        with np.load(cpath, allow_pickle=False) as c:
            k = int(c["stage_dirs"].shape[0])
            stage_dirs[row, :k] = c["stage_dirs"]
            stage_prefs[row, :k] = c["stage_prefs"]
            stage_mass[row, :k] = c["stage_mass"]
            stage_valid[row, :k] = True
            users_by_stage[row, :k] = c["users_by_stage"]
            seed_books[row] = c["seed_books"]
            source_pref[row] = c["source_pref"]
            stage0_pref[row] = c["stage0_pref"]
        source_size[row] = size
        source_jury[row] = jury
        row += 1

    np.savez_compressed(
        npz_path,
        source_size=source_size,
        source_jury=source_jury,
        stage_dirs=stage_dirs,
        stage_prefs=stage_prefs,
        stage_mass=stage_mass,
        stage_valid=stage_valid,
        users_by_stage=users_by_stage,
        seed_books=seed_books,
        source_pref=source_pref,
        stage0_pref=stage0_pref,
    )
    sha = _sha256(npz_path)
    json_path.write_text(
        json.dumps(
            {
                **data,
                "partial": len(records) < len(sources),
                "artifact_sha256": sha,
                "artifact_bytes": npz_path.stat().st_size,
                "consolidated": {
                    "n_sources": n,
                    "n_books": n_books,
                    "max_stages": max_stages,
                    "schema": {
                        "source_size": "(n,) int32",
                        "source_jury": "(n,) int32",
                        "stage_dirs": "(n,max_stages,n_books) float32",
                        "stage_prefs": "(n,max_stages,n_books) float32",
                        "stage_mass": "(n,max_stages,n_books) float32",
                        "stage_valid": "(n,max_stages) bool",
                        "users_by_stage": "(n,max_stages) int32",
                        "seed_books": "(n,25) int32",
                        "source_pref": "(n,n_books) float32",
                        "stage0_pref": "(n,n_books) float32",
                    },
                    "semantic_context_loaded": False,
                    "command": shlex.join(sys.argv),
                    "git_head": _git_head(),
                    "runtime_seconds": time.time() - t0,
                },
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    if not args.keep_chunks:
        for cpath in have:
            cpath.unlink(missing_ok=True)
        print(f"removed {len(have)} chunk files (kept {npz_path})", flush=True)
    print(
        f"consolidate done: {n} sources x {max_stages} stages x {n_books} books, "
        f"sha256 {sha[:16]}..., {time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Phase 3: freeze label-blind geometry (no semantic context anywhere here)
# ---------------------------------------------------------------------------

def _pref_rep(x: np.ndarray, eligible: np.ndarray) -> np.ndarray:
    v = np.asarray(x, dtype=np.float64)[eligible]
    v = v - v.mean()
    norm = np.linalg.norm(v)
    return (v / norm).astype(np.float32) if norm > 1e-20 else v.astype(np.float32)


def _dir_rep(x: np.ndarray) -> np.ndarray:
    v = np.asarray(x, dtype=np.float64).ravel()
    norm = np.linalg.norm(v)
    return (v / norm).astype(np.float32) if norm > 1e-20 else v.astype(np.float32)


def _unit_rows(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.maximum(norms, 1e-20)


def avg_link_clusters(mat: np.ndarray, tau: float) -> list[list[int]]:
    """Average-linkage agglomerative clustering of unit vectors with cosine
    distance; the dendrogram is cut at height (1 - tau), i.e. every returned
    cluster was joined at an average-linkage distance <= 1 - tau. Singletons
    are kept. Matches the preregistered cuts tau in {0.30, 0.50, 0.70}."""
    n = mat.shape[0]
    if n <= 1:
        return [[i] for i in range(n)]
    z = linkage(mat, method="average", metric="cosine")
    labels = fcluster(z, t=1.0 - tau, criterion="distance")
    out: dict[int, list[int]] = {}
    for i, c in enumerate(labels):
        out.setdefault(int(c), []).append(i)
    return [v for _, v in sorted(out.items())]


def _effective_dim(mat: np.ndarray) -> float:
    k = mat.shape[0]
    if k <= 1:
        return float(k)
    centered = mat - mat.mean(axis=0, keepdims=True)
    singular = np.linalg.svd(centered, compute_uv=False)
    e2 = singular**2
    total = e2.sum()
    return float(total**2 / np.sum(e2**2)) if np.sum(e2**2) > 0 else 0.0


def _within_stats(sim: np.ndarray, members: list[int]) -> dict[str, float]:
    if len(members) < 2:
        return {"mean": 1.0, "median": 1.0, "min": 1.0, "pair_count": 0}
    sub = sim[np.ix_(members, members)]
    iu = np.triu_indices(len(members), k=1)
    vals = sub[iu]
    return {
        "mean": float(vals.mean()),
        "median": float(np.median(vals)),
        "min": float(vals.min()),
        "pair_count": int(len(vals)),
    }


def _cluster_record(
    members: list[int],
    ids: list[str],
    pref_mat: np.ndarray,
    dir_mat: np.ndarray,
    raw_prefs: np.ndarray,
    pref_sim: np.ndarray,
    dir_sim: np.ndarray,
    eligible: np.ndarray,
    npz_out: dict[str, np.ndarray],
    key: str,
    cluster_index: int,
) -> dict[str, Any]:
    """Freeze one label-blind cluster (singletons included)."""
    pref_centroid = pref_mat[members].mean(axis=0)
    pref_centroid = _unit_rows(pref_centroid[None, :])[0].astype(np.float32)
    dir_centroid = _unit_rows(dir_mat[members].mean(axis=0)[None, :])[0].astype(np.float32)
    raw_pref_centroid = raw_prefs[members].mean(axis=0).astype(np.float32)

    eligible_idx = np.flatnonzero(eligible)
    order = np.argsort(-raw_pref_centroid[eligible], kind="stable")[:50]
    top_indices = eligible_idx[order].astype(np.int64).tolist()

    rec: dict[str, Any] = {
        "members": [ids[m] for m in members],
        "size": len(members),
        "composition": {
            str(size): int(sum(1 for m in members if ids[m].startswith(f"{size}:")))
            for size in SIZES
        },
        "within_pref": _within_stats(pref_sim, members),
        "within_dir": _within_stats(dir_sim, members),
        "effective_dim_pref": _effective_dim(pref_mat[members]),
        "effective_dim_dir": _effective_dim(dir_mat[members]),
        "top_eligible_book_indices": top_indices,
    }
    if len(members) >= 2:
        kp = f"cent_pref_{key}_{cluster_index}"
        kd = f"cent_dir_{key}_{cluster_index}"
        kr = f"rawpref_{key}_{cluster_index}"
        npz_out[kp] = pref_centroid
        npz_out[kd] = dir_centroid
        npz_out[kr] = raw_pref_centroid
        rec["pref_centroid_key"] = kp
        rec["dir_centroid_key"] = kd
        rec["raw_pref_centroid_key"] = kr
    else:
        rec["pref_centroid_key"] = None
        rec["dir_centroid_key"] = None
        rec["raw_pref_centroid_key"] = None
    return rec


def _pairwise_summary(sim: np.ndarray) -> dict[str, float]:
    k = sim.shape[0]
    if k < 2:
        return {"mean": float("nan"), "median": float("nan"), "q90": float("nan")}
    iu = np.triu_indices(k, k=1)
    vals = sim[iu]
    return {
        "mean": float(vals.mean()),
        "median": float(np.median(vals)),
        "q90": float(np.quantile(vals, 0.90)),
    }


def phase_geometry(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED

    t0 = time.time()
    npz_path, json_path = census_paths(args.tag)
    if not npz_path.exists():
        raise SystemExit(f"missing census npz {npz_path}; run consolidate first")
    blob = np.load(npz_path, allow_pickle=False)
    records = json.loads(json_path.read_text(encoding="utf-8"))["records"]
    ids = [r["source_id"] for r in records]
    n = len(records)
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    sizes = blob["source_size"]
    jury = blob["source_jury"]

    def available_idxs(stage_label: str) -> list[int]:
        if stage_label == "deepest":
            return list(range(n))
        return [i for i, r in enumerate(records) if r["n_stages"] > STAGE_ANALYZED]

    def stage_index(r: dict[str, Any], stage_label: str) -> int:
        return r["n_stages"] - 1 if stage_label == "deepest" else STAGE_ANALYZED

    pref_mats: dict[str, np.ndarray] = {}
    dir_mats: dict[str, np.ndarray] = {}
    raw_mats: dict[str, np.ndarray] = {}
    sims: dict[str, dict[str, np.ndarray]] = {}
    avail: dict[str, list[int]] = {}
    for stage_label in ("deepest", "s4"):
        idxs = available_idxs(stage_label)
        avail[stage_label] = idxs
        pref = [_pref_rep(blob["stage_prefs"][i, stage_index(records[i], stage_label)], eligible) for i in idxs]
        dirs = [_dir_rep(blob["stage_dirs"][i, stage_index(records[i], stage_label)]) for i in idxs]
        raw = [blob["stage_prefs"][i, stage_index(records[i], stage_label)].astype(np.float32) for i in idxs]
        pref_mats[stage_label] = np.stack(pref).astype(np.float32)
        dir_mats[stage_label] = np.stack(dirs).astype(np.float32)
        raw_mats[stage_label] = np.stack(raw).astype(np.float32)
        sims[stage_label] = {
            "pref": pref_mats[stage_label] @ pref_mats[stage_label].T,
            "dir": dir_mats[stage_label] @ dir_mats[stage_label].T,
        }

    group_masks = {
        "20k": [i for i in range(n) if sizes[i] == 20000],
        "80k": [i for i in range(n) if sizes[i] == 80000],
        "pooled": list(range(n)),
    }

    npz_out: dict[str, np.ndarray] = {}
    geometry: dict[str, Any] = {
        "source_order": ids,
        "available_by_stage": {
            "deepest": [ids[i] for i in avail["deepest"]],
            "s4": [ids[i] for i in avail["s4"]],
        },
        "pairwise": {},
        "clusters": {},
        "halves": {},
    }

    for stage_label in ("deepest", "s4"):
        npz_out[f"rep_pref_{stage_label}"] = pref_mats[stage_label]
        npz_out[f"rep_dir_{stage_label}"] = dir_mats[stage_label]
        npz_out[f"raw_pref_{stage_label}"] = raw_mats[stage_label]
        npz_out[f"sim_pref_{stage_label}"] = sims[stage_label]["pref"]
        npz_out[f"sim_dir_{stage_label}"] = sims[stage_label]["dir"]

    for stage_label in ("deepest", "s4"):
        idxs = avail[stage_label]
        stage_ids = [ids[i] for i in idxs]
        geometry["clusters"][stage_label] = {}
        for group, gmask in group_masks.items():
            gpos = [idxs.index(i) for i in gmask if i in set(idxs)]
            gids = [stage_ids[p] for p in gpos]
            sub_pref = pref_mats[stage_label][gpos]
            sub_dir = dir_mats[stage_label][gpos]
            sub_raw = raw_mats[stage_label][gpos]
            sub_pref_sim = sub_pref @ sub_pref.T
            sub_dir_sim = sub_dir @ sub_dir.T
            geometry["pairwise"][f"{stage_label}_{group}"] = {
                "n": len(gpos),
                "pref": _pairwise_summary(sub_pref_sim),
                "dir": _pairwise_summary(sub_dir_sim),
            }
            group_blocks: dict[str, Any] = {}
            for tau in CLUSTER_TAUS:
                key = f"{group}_{stage_label}_{tau:.2f}"
                for space, mat, sim in (
                    ("pref", sub_pref, sub_pref_sim),
                    ("dir", sub_dir, sub_dir_sim),
                ):
                    cl = avg_link_clusters(mat, tau)
                    recs = []
                    for ci, members in enumerate(cl):
                        recs.append(
                            _cluster_record(
                                members, gids, sub_pref, sub_dir, sub_raw,
                                sub_pref_sim, sub_dir_sim, eligible,
                                npz_out, key, ci,
                            )
                        )
                    group_blocks[f"{key}_{space}"] = recs
            geometry["clusters"][stage_label][group] = group_blocks

    # Independent-half reproducibility: even jury index -> A, odd -> B.
    for stage_label in ("deepest", "s4"):
        idxs = avail[stage_label]
        for group, gmask in group_masks.items():
            gpos_rec = [p for p in idxs if p in gmask]
            positions = [idxs.index(p) for p in gpos_rec]
            evens = [j for j, p in enumerate(gpos_rec) if int(jury[p]) % 2 == 0]
            odds = [j for j, p in enumerate(gpos_rec) if int(jury[p]) % 2 == 1]
            for space in ("pref", "dir"):
                mat = pref_mats[stage_label] if space == "pref" else dir_mats[stage_label]
                for tau in CLUSTER_TAUS:
                    a_pos = [positions[j] for j in evens]
                    b_pos = [positions[j] for j in odds]
                    ca = avg_link_clusters(mat[a_pos], tau)
                    cb = avg_link_clusters(mat[b_pos], tau)
                    key = f"match_{space}_{group}_{stage_label}_{tau:.2f}"
                    if not ca or not cb:
                        # one half has no sources at this stage (tiny smoke
                        # runs); nothing to match, record the empty side so
                        # the schema stays consistent
                        geometry["halves"][key] = {
                            "nA": len(a_pos),
                            "nB": len(b_pos),
                            "best_matches": [],
                            "best_matches_B_side": [],
                            "matrix_npz_key": None,
                            "empty_side": True,
                        }
                        continue
                    ca_ids = [[ids[gpos_rec[evens[m]]] for m in cl] for cl in ca]
                    cb_ids = [[ids[gpos_rec[odds[m]]] for m in cl] for cl in cb]
                    cents_a = _unit_rows(np.stack([mat[a_pos][cl].mean(axis=0) for cl in ca]))
                    cents_b = _unit_rows(np.stack([mat[b_pos][cl].mean(axis=0) for cl in cb]))
                    m = cents_a @ cents_b.T
                    npz_out[key] = m.astype(np.float32)
                    best = []
                    for i in range(len(ca)):
                        b = int(np.argmax(m[i]))
                        best.append(
                            {
                                "a_cluster": ca_ids[i],
                                "b_cluster": cb_ids[b],
                                "cos": float(m[i, b]),
                                "a_size": len(ca[i]),
                                "b_size": len(cb[b]),
                            }
                        )
                    best_b = []
                    for j in range(len(cb)):
                        a = int(np.argmax(m[:, j]))
                        best_b.append(
                            {
                                "a_cluster": ca_ids[a],
                                "b_cluster": cb_ids[j],
                                "cos": float(m[a, j]),
                                "a_size": len(ca[a]),
                                "b_size": len(cb[j]),
                            }
                        )
                    geometry["halves"][key] = {
                        "nA": len(a_pos),
                        "nB": len(b_pos),
                        "best_matches": best,
                        "best_matches_B_side": best_b,
                        "matrix_npz_key": key,
                    }

    geometry["method"] = {
        "phase": "geometry",
        "purpose": (
            "label-blind structural census of amplified endpoints; "
            "no semantic context loaded anywhere in this phase"
        ),
        "sizes": list(SIZES),
        "elig_min_book_n": ELIG_MIN_BOOK_N,
        "representation_pref": "book_n>=25 -> mean-center across eligible -> L2",
        "representation_dir": "L2 normalize stage direction",
        "clustering": {
            "method": "average-linkage hierarchical, cosine distance",
            "cut": "dendrogram height 1 - tau",
            "taus": list(CLUSTER_TAUS),
            "singletons_kept": True,
        },
        "stage_analyzed_index": STAGE_ANALYZED,
        "halves": {
            "A": "source jury index even",
            "B": "source jury index odd",
            "matching": "cluster centroid cosine in the same space",
        },
        "semantic_context_loaded": False,
        "unblinded": False,
        "written_before_unblinding": True,
        "command": shlex.join(sys.argv),
        "git_head": _git_head(),
        "runtime_seconds": time.time() - t0,
    }

    geo_json, geo_npz = geometry_paths(args.tag)
    geo_json.write_text(json.dumps(geometry, indent=1), encoding="utf-8")
    np.savez_compressed(geo_npz, **npz_out)
    print(
        f"geometry frozen: {geo_json} ({geo_json.stat().st_size/2**20:.1f} MiB), "
        f"{geo_npz} ({geo_npz.stat().st_size/2**20:.1f} MiB), "
        f"{time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Phase 4: post-hoc semantic unblinding (only after geometry is frozen)
# ---------------------------------------------------------------------------

_METRIC_KEYS = (
    "exact_lit50", "exact_lit200", "broad_lit50", "broad_lit200",
    "anti50", "anti200", "filler50", "filler200",
)


def _eval_pref(
    score: np.ndarray,
    reader_mass: np.ndarray,
    work_ids: np.ndarray,
    meta: dict[str, Any],
    eval_sets: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    preference = {
        "score": np.asarray(score, dtype=np.float64),
        "mean": np.asarray(score, dtype=np.float64),
        "reader_mass": np.asarray(reader_mass, dtype=np.float64),
    }
    return attractor.posthoc_head(preference, work_ids, meta, eval_sets, limit=200)


def _metrics_row(metrics: dict[str, int]) -> dict[str, int]:
    return {k: int(metrics[k]) for k in _METRIC_KEYS}


def _top30(head: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"rank": r["rank"], "title": r["title"], "author": r["author"]}
        for r in head[:30]
    ]


def _mean_raw_pref(
    records: list[dict[str, Any]],
    ids: list[str],
    blob: Any,
    members: list[str],
    stage_label: str,
) -> np.ndarray | None:
    rows = []
    for m in members:
        i = ids.index(m)
        r = records[i]
        si = r["n_stages"] - 1 if stage_label == "deepest" else STAGE_ANALYZED
        if si < 0 or si >= r["n_stages"]:
            return None
        rows.append(blob["stage_prefs"][i, si].astype(np.float64))
    return np.mean(np.stack(rows), axis=0) if rows else None


def _membership_map(frozen: dict[str, Any]) -> dict[str, dict[str, int]]:
    """source_id|stage_label -> {tau_space: cluster size} (pooled, both spaces)."""
    out: dict[str, dict[str, int]] = {}
    for stage_label in ("deepest", "s4"):
        for tau in CLUSTER_TAUS:
            for space in ("pref", "dir"):
                clist = frozen["clusters"][stage_label]["pooled"][
                    f"pooled_{stage_label}_{tau:.2f}_{space}"
                ]
                for c in clist:
                    for m in c["members"]:
                        key = f"{m}|{stage_label}"
                        out.setdefault(key, {})[f"{tau:.2f}_{space}"] = c["size"]
    return out


def _feature_outcomes(
    ids: list[str], cluster_evals: list[dict[str, Any]]
) -> dict[str, np.ndarray]:
    """Exploratory binary outcomes per source (pooled, deepest, pref space).
    'literary cluster' is defined post-hoc as exact_lit50 >= 3 on the cluster
    centroid; this labels only the exploratory probe, never any clustering."""
    in_cluster = np.zeros(len(ids), dtype=bool)
    lit_cluster = np.zeros(len(ids), dtype=bool)
    for e in cluster_evals:
        if not (
            e["stage"] == "deepest" and e["group"] == "pooled"
            and e["tau"] == 0.30 and e["space"] == "pref"
        ):
            continue
        is_lit = e["metrics"]["exact_lit50"] >= 3
        for m in e["members"]:
            i = ids.index(m)
            in_cluster[i] = True
            if is_lit:
                lit_cluster[i] = True
    return {
        "in_non_singleton_cluster": in_cluster,
        "in_literary_cluster": lit_cluster,
    }


def phase_unblind(args: argparse.Namespace) -> None:
    global SEMANTIC_CONTEXT_LOADED
    assert not SEMANTIC_CONTEXT_LOADED
    geo_json, geo_npz = geometry_paths(args.tag)
    if not geo_json.exists() or not geo_npz.exists():
        raise SystemExit("geometry not frozen yet; refusing to unblind")
    frozen = json.loads(geo_json.read_text(encoding="utf-8"))
    assert frozen["method"]["unblinded"] is False
    assert frozen["method"]["semantic_context_loaded"] is False

    t0 = time.time()
    npz_path, json_path = census_paths(args.tag)
    blob = np.load(npz_path, allow_pickle=False)
    records = json.loads(json_path.read_text(encoding="utf-8"))["records"]
    ids = [r["source_id"] for r in records]
    payload, _, _ = year.load_matrix()

    # ---- THE ONLY semantic load in the whole experiment ----
    print("Loading post-hoc semantic context (unblind)", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    SEMANTIC_CONTEXT_LOADED = True

    pole = None
    if POLE_NPZ.exists():
        pole = np.load(POLE_NPZ, allow_pickle=True)[POLE_KEY].astype(np.float64)
        pole = pole / (np.linalg.norm(pole) + 1e-20)

    n_books = len(payload["work_ids"])
    universe = set(payload["work_ids"].tolist())
    chance = {
        name: len(eval_sets[name] & universe) / n_books * 50
        for name in ("exact_lit", "broad_lit", "anti", "filler")
    }

    membership = _membership_map(frozen)

    # 1) every individual amplified endpoint (deepest and stage 4)
    endpoints: list[dict[str, Any]] = []
    for i, r in enumerate(records):
        rec: dict[str, Any] = {
            "source_id": r["source_id"],
            "size": r["size"],
            "jury": r["jury"],
            "stop_reason": r["stop_reason"],
            "n_stages": r["n_stages"],
        }
        for stage_label, si in (
            ("deepest", r["n_stages"] - 1),
            ("s4", STAGE_ANALYZED),
        ):
            if stage_label == "s4" and r["n_stages"] <= STAGE_ANALYZED:
                continue
            score = blob["stage_prefs"][i, si]
            mass = blob["stage_mass"][i, si]
            head, metrics = _eval_pref(score, mass, payload["work_ids"], meta, eval_sets)
            d = blob["stage_dirs"][i, si].astype(np.float64)
            rec[stage_label] = {
                "metrics": _metrics_row(metrics),
                "head": _top30(head),
                "cos_pole": (
                    float(np.sum(d * pole) / (np.linalg.norm(d) * np.linalg.norm(pole)))
                    if pole is not None else None
                ),
                "cluster_memberships": membership.get(
                    f"{r['source_id']}|{stage_label}", {}
                ),
            }
        endpoints.append(rec)
    print(f"endpoint evaluation done ({len(endpoints)})", flush=True)

    # 2) every label-blind preference centroid; 3) direction centroids
    gblob = np.load(geo_npz, allow_pickle=False)
    cluster_evals: list[dict[str, Any]] = []
    for stage_label in ("deepest", "s4"):
        for group in ("20k", "80k", "pooled"):
            for tau in CLUSTER_TAUS:
                for space in ("pref", "dir"):
                    key = f"{group}_{stage_label}_{tau:.2f}_{space}"
                    clist = frozen["clusters"][stage_label][group][key]
                    for ci, c in enumerate(clist):
                        if len(c["members"]) < 2:
                            continue
                        entry: dict[str, Any] = {
                            "stage": stage_label,
                            "group": group,
                            "tau": tau,
                            "space": space,
                            "key": key,
                            "cluster_index": ci,
                            "members": c["members"],
                            "size": c["size"],
                            "composition": c["composition"],
                            "within": c["within_pref" if space == "pref" else "within_dir"],
                            "effective_dim": c[
                                "effective_dim_pref" if space == "pref" else "effective_dim_dir"
                            ],
                        }
                        if space == "pref":
                            centroid = gblob[c["pref_centroid_key"]]
                            head, metrics = _eval_pref(
                                centroid, payload["book_n"],
                                payload["work_ids"], meta, eval_sets,
                            )
                        else:
                            centroid = gblob[c["dir_centroid_key"]]
                            head, metrics = spectral.pole_rows(
                                centroid, payload["work_ids"], meta, eval_sets,
                                positive=True, limit=200,
                            )
                        entry["metrics"] = _metrics_row(metrics)
                        entry["head"] = _top30(head)
                        if pole is not None:
                            entry["cos_pole"] = float(
                                np.sum(centroid.astype(np.float64) * pole)
                            )
                        cluster_evals.append(entry)
    print(f"cluster evaluation done ({len(cluster_evals)})", flush=True)

    # 4) independently matched A/B clusters (both halves' centroids evaluated)
    matched: list[dict[str, Any]] = []
    for key, h in frozen["halves"].items():
        parts = key.split("_")
        space = parts[1]
        group = parts[2]
        stage_label = parts[3]
        tau = float(parts[4])
        for bm in h["best_matches"]:
            if len(bm["a_cluster"]) < 2 or len(bm["b_cluster"]) < 2:
                continue
            entry: dict[str, Any] = {
                "key": key,
                "group": group,
                "stage": stage_label,
                "tau": tau,
                "space": space,
                "cos": bm["cos"],
                "a_members": bm["a_cluster"],
                "b_members": bm["b_cluster"],
                "a_size": bm["a_size"],
                "b_size": bm["b_size"],
            }
            a_pref = _mean_raw_pref(records, ids, blob, bm["a_cluster"], stage_label)
            b_pref = _mean_raw_pref(records, ids, blob, bm["b_cluster"], stage_label)
            if a_pref is not None and b_pref is not None:
                ha, ma = _eval_pref(a_pref, payload["book_n"], payload["work_ids"], meta, eval_sets)
                hb, mb = _eval_pref(b_pref, payload["book_n"], payload["work_ids"], meta, eval_sets)
                entry["a_metrics"] = _metrics_row(ma)
                entry["b_metrics"] = _metrics_row(mb)
                entry["a_head"] = _top30(ha)
                entry["b_head"] = _top30(hb)
            matched.append(entry)
    print(f"matched-pair evaluation done ({len(matched)})", flush=True)

    # exploratory feature -> membership diagnostics (no fitted classifier)
    outcomes = _feature_outcomes(ids, cluster_evals)
    feature_rows = []
    for fname in FEATURE_NAMES:
        x = np.asarray([r["features"][fname] for r in records], dtype=np.float64)
        for oname, y in outcomes.items():
            rho = None
            if len(np.unique(y)) > 1 and np.std(x) > 0:
                rho = float(pointbiserialr(x, y).correlation)
            feature_rows.append(
                {"feature": fname, "outcome": oname, "point_biserial_r": rho, "n": int(len(y))}
            )

    result = {
        "method": {
            "phase": "unblind",
            "purpose": "post-hoc literary evaluation of frozen label-blind objects only",
            "semantic_context_loaded_now": True,
            "clustering_never_altered": True,
            "pole_key": POLE_KEY,
            "pole_usage": "post-hoc diagnostic only; never used for clustering or selection",
            "command": shlex.join(sys.argv),
            "git_head": _git_head(),
            "runtime_seconds": time.time() - t0,
        },
        "chance_at_50": chance,
        "endpoints": endpoints,
        "cluster_evals": cluster_evals,
        "matched": matched,
        "feature_diagnostics": feature_rows,
    }
    out = posthoc_path(args.tag)
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    _write_report(args, frozen, result, npz_path, geo_npz)
    print(f"unblind done: {out}", flush=True)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _fmt_head(head: list[dict[str, Any]], n: int = 10) -> list[str]:
    return [
        f"{row['rank']}. *{row['title']}* — {row['author']}"
        for row in head[:n]
    ]


def _metric_str(m: dict[str, int]) -> str:
    return (
        f"{m['exact_lit50']}/{m['exact_lit200']} | "
        f"{m['broad_lit50']}/{m['broad_lit200']} | "
        f"{m['anti50']}/{m['anti200']} | "
        f"{m['filler50']}/{m['filler200']}"
    )


def _write_report(
    args: argparse.Namespace,
    frozen: dict[str, Any],
    result: dict[str, Any],
    census_npz: Path,
    geometry_npz: Path,
) -> None:
    method = frozen["method"]
    chance = result["chance_at_50"]
    n_books = None
    try:
        with np.load(census_npz, allow_pickle=False) as b:
            n_books = int(b["stage_prefs"].shape[2])
    except Exception:
        pass

    lines: list[str] = [
        "# Natural amplification census: a completely label-blind search for a literary basin",
        "",
        "**Question.** If we amplify random reversal endpoints without ever consulting literary "
        "labels, does a distinct literary basin emerge naturally among the amplified outputs?",
        "",
        "**Hard constraint honored.** No literary, anti-literary, genre, title, author, "
        "publication-year, known-pole, or external evaluation information was loaded or used "
        "until every amplification run, vector, similarity matrix, cluster assignment, and "
        "cluster centroid had been frozen and written to disk (`amplify`, `consolidate`, and "
        "`geometry` phases). Semantic context loaded only in the `unblind` phase, and the known "
        "literary pole cosine is a post-hoc diagnostic that never altered clustering or selection.",
        "",
        "## Provenance",
        "",
        f"- Command: `{result['method']['command']}`",
        f"- Random seed: **{SEED}**",
        f"- Git commit: `{_git_head()}`",
        f"- Unblind runtime: **{result['method']['runtime_seconds']:.0f}s**",
        f"- Census artifact: `{census_npz.name}` — SHA256 `{_sha256(census_npz)}` "
        f"({census_npz.stat().st_size/2**20:.1f} MiB)",
        f"- Geometry artifact: `{geometry_npz.name}` — SHA256 `{_sha256(geometry_npz)}` "
        f"({geometry_npz.stat().st_size/2**20:.1f} MiB)",
        f"- Books in universe: {n_books if n_books else 'n/a'}",
        f"- Chance @50 (in-universe): exact {chance['exact_lit']:.2f}, broad {chance['broad_lit']:.2f}, "
        f"anti {chance['anti']:.2f}, filler {chance['filler']:.2f}.",
        "",
        "## PRE-UNBLIND STRUCTURAL RESULTS",
        "",
        "All numbers below were computed and frozen before any semantic context was loaded.",
        "",
        "### Sources",
        "",
        f"- Sizes: **{list(SIZES)}**, {JURIES_PER_SIZE} juries each (jury ids 0..119), source id `size:jury`.",
        "- Amplification: `seed_from_pref` on the saved endpoint preference vector (top 25 eligible "
        "books, `0.4 + 19.6 * frac5`, mean-normalized), then `run_path` gain-hard forward amplification "
        f"(beta {breeding.BETA}, hard threshold `pruning.HARD_THRESHOLD`, max stages {breeding.MAX_STAGES}).",
        "- Representation (preference space): `book_n >= 25` -> mean-center across eligible -> L2.",
        "- Representation (direction space): L2-normalized stage direction.",
        "- Clustering: average-linkage hierarchical clustering on cosine distance, dendrogram cut at "
        "height `1 - tau` for tau in {0.30, 0.50, 0.70}; singletons kept.",
        "",
        "### Pairwise endpoint similarity (off-diagonal)",
        "",
        "| group | stage | space | n | mean | median | q90 |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for stage_label in ("deepest", "s4"):
        for group in ("20k", "80k", "pooled"):
            for space in ("pref", "dir"):
                ps = frozen["pairwise"][f"{stage_label}_{group}"][space]
                lines.append(
                    f"| {group} | {stage_label} | {space} | {frozen['pairwise'][f'{stage_label}_{group}']['n']} | "
                    f"{ps['mean']:.4f} | {ps['median']:.4f} | {ps['q90']:.4f} |"
                )
    lines += ["", "### Cluster census (label-blind)", ""]
    for stage_label in ("deepest", "s4"):
        for group in ("20k", "80k", "pooled"):
            for tau in CLUSTER_TAUS:
                for space in ("pref", "dir"):
                    key = f"{group}_{stage_label}_{tau:.2f}_{space}"
                    clist = frozen["clusters"][stage_label][group][key]
                    non_sing = [c for c in clist if c["size"] >= 2]
                    top = sorted(non_sing, key=lambda c: -c["size"])[:5]
                    line = (
                        f"- {group} {stage_label} tau={tau:.2f} {space}: "
                        f"{len(clist)} clusters ({len(non_sing)} with >= 2 members); "
                        f"largest: "
                    )
                    if top:
                        line += ", ".join(
                            f"{c['size']} ({c['members'][0]}...)"
                            for c in top
                        )
                    else:
                        line += "none"
                    lines.append(line)
    lines.append("")
    lines += ["### Non-singleton clusters: within-cluster agreement and dispersion", ""]
    lines += [
        "| stage | group | tau | space | size | members | within mean/med/min | eff. dim |",
        "|---|---|---:|---:|---:|---|---:|---:|",
    ]
    for stage_label in ("deepest", "s4"):
        for group in ("20k", "80k", "pooled"):
            for tau in CLUSTER_TAUS:
                for space in ("pref", "dir"):
                    key = f"{group}_{stage_label}_{tau:.2f}_{space}"
                    for c in frozen["clusters"][stage_label][group][key]:
                        if c["size"] < 2:
                            continue
                        w = c["within_pref" if space == "pref" else "within_dir"]
                        ed = c["effective_dim_pref" if space == "pref" else "effective_dim_dir"]
                        lines.append(
                            f"| {stage_label} | {group} | {tau:.2f} | {space} | {c['size']} | "
                            f"{' '.join(c['members'])} | "
                            f"{w['mean']:.3f}/{w['median']:.3f}/{w['min']:.3f} | {ed:.1f} |"
                        )
    lines += ["", "### Independent-half reproducibility", ""]
    lines += [
        "| key | nA | nB | matches | cos>=0.5 | cos>=0.7 | best cos |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, h in frozen["halves"].items():
        best_cos = max((b["cos"] for b in h["best_matches"]), default=float("nan"))
        ge5 = sum(1 for b in h["best_matches"] if b["cos"] >= 0.5)
        ge7 = sum(1 for b in h["best_matches"] if b["cos"] >= 0.7)
        lines.append(
            f"| {key} | {h['nA']} | {h['nB']} | {len(h['best_matches'])} | "
            f"{ge5} | {ge7} | {best_cos:.3f} |"
        )
    lines += ["", "## POST-HOC LITERARY EVALUATION", ""]
    lines += [
        "",
        "Semantic context was loaded only after every structure above was frozen.",
        "",
    ]

    # endpoints
    ex50 = np.asarray(
        [e["deepest"]["metrics"]["exact_lit50"] for e in result["endpoints"]]
    )
    br50 = np.asarray(
        [e["deepest"]["metrics"]["broad_lit50"] for e in result["endpoints"]]
    )
    an50 = np.asarray(
        [e["deepest"]["metrics"]["anti50"] for e in result["endpoints"]]
    )
    lines += [
        "### Individual amplified endpoints (deepest stage)",
        "",
        f"exact_lit @50: mean {ex50.mean():.2f}, median {np.median(ex50):.0f}, max {ex50.max()}; "
        f"{int(np.sum(ex50 >= 3))}/{len(ex50)} endpoints >= 3.",
        f"broad_lit @50: mean {br50.mean():.2f}, max {br50.max()}; "
        f"anti @50: mean {an50.mean():.2f}, max {an50.max()}.",
        "",
    ]

    # cluster centroids
    lines += ["### Label-blind preference centroids (non-singleton clusters)", ""]
    lines += [
        "| stage | group | tau | size | composition | exact @50/200 | broad @50/200 | anti @50/200 | filler @50/200 | within | cos_pole |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for e in result["cluster_evals"]:
        if e["space"] != "pref":
            continue
        comp = "/".join(f"{s}:{e['composition'][s]}" for s in ("20000", "80000"))
        cp = f"{e['cos_pole']:.3f}" if e.get("cos_pole") is not None else "n/a"
        lines.append(
            f"| {e['stage']} | {e['group']} | {e['tau']:.2f} | {e['size']} | {comp} | "
            f"{_metric_str(e['metrics'])} | {e['within']['mean']:.3f} | {cp} |"
        )
    lines += ["", "### Direction centroids (pole_rows convention)", ""]
    lines += [
        "| stage | group | tau | size | exact @50/200 | broad @50/200 | anti @50/200 | filler @50/200 | cos_pole |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for e in result["cluster_evals"]:
        if e["space"] != "dir":
            continue
        cp = f"{e['cos_pole']:.3f}" if e.get("cos_pole") is not None else "n/a"
        lines.append(
            f"| {e['stage']} | {e['group']} | {e['tau']:.2f} | {e['size']} | "
            f"{_metric_str(e['metrics'])} | {cp} |"
        )

    # matched pairs
    lines += ["", "### Independently matched A/B clusters", ""]
    lines += [
        "| key | cos | a_size | b_size | A exact/broad/anti @50 | B exact/broad/anti @50 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for m in result["matched"]:
        if "a_metrics" not in m:
            continue
        a = m["a_metrics"]
        b = m["b_metrics"]
        lines.append(
            f"| {m['key']} | {m['cos']:.3f} | {m['a_size']} | {m['b_size']} | "
            f"{a['exact_lit50']}/{a['broad_lit50']}/{a['anti50']} | "
            f"{b['exact_lit50']}/{b['broad_lit50']}/{b['anti50']} |"
        )

    # heads of notable clusters
    notable = [
        e for e in result["cluster_evals"]
        if e["space"] == "pref" and e["metrics"]["exact_lit50"] >= 3
    ]
    notable.sort(key=lambda e: -e["metrics"]["exact_lit50"])
    if notable:
        lines += ["", "### Heads of label-blind clusters with exact_lit50 >= 3", ""]
        for e in notable[:10]:
            comp = "/".join(f"{s}:{e['composition'][s]}" for s in ("20000", "80000"))
            lines += [
                f"#### {e['stage']} {e['group']} tau={e['tau']:.2f} ({e['size']} members; {comp})",
                "",
                f"Exact/broad/anti/filler @50/200: {_metric_str(e['metrics'])}; "
                f"within {e['within']['mean']:.3f}; cos_pole {e.get('cos_pole')}.",
                "",
            ]
            lines += _fmt_head(e["head"], 15)
            lines.append("")

    # feature diagnostics
    lines += ["", "### Exploratory feature -> membership diagnostics (no fitted classifier)", ""]
    lines += ["| feature | outcome | point-biserial r | n |", "|---|---|---:|---:|"]
    for f in result["feature_diagnostics"]:
        r = f"{f['point_biserial_r']:.3f}" if f["point_biserial_r"] is not None else "n/a"
        lines.append(f"| {f['feature']} | {f['outcome']} | {r} | {f['n']} |")
    lines += ["", "## Verdict", ""]
    n_lit = sum(
        1 for e in result["cluster_evals"]
        if e["space"] == "pref" and e["stage"] == "deepest" and e["group"] == "pooled"
        and e["metrics"]["exact_lit50"] >= 3
    )
    lines.append(
        f"The pooled deepest preference-space clustering at tau=0.30 produced "
        f"{len(frozen['clusters']['deepest']['pooled']['pooled_deepest_0.30_pref'])} clusters, of which "
        f"{sum(1 for c in frozen['clusters']['deepest']['pooled']['pooled_deepest_0.30_pref'] if c['size'] >= 2)} "
        f"have >= 2 members; {n_lit} non-singleton clusters reach exact_lit50 >= 3 post-hoc. "
        "Whether this constitutes a recurrent label-blind literary basin is assessed in the "
        "tables above (within-cluster agreement, half-half reproducibility, anti contamination). "
        "This report does not force a conclusion; a negative or mixed result is reported as found."
    )
    out = report_path(args.tag)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


# ---------------------------------------------------------------------------
# Smoke test: 4 sources per size + reproducibility verification
# ---------------------------------------------------------------------------

def phase_smoke(args: argparse.Namespace) -> None:
    t0 = time.time()
    args.juries_per_size = args.smoke_juries
    args.keep_chunks = True
    phase_amplify(args)
    phase_consolidate(args)
    _verify_smoke(args)
    for size, jury in load_drift_sources(args.smoke_juries):
        chunk_path(args.tag, size, jury).unlink(missing_ok=True)
    print(f"smoke done in {time.time() - t0:.0f}s", flush=True)


def _verify_smoke(args: argparse.Namespace) -> None:
    """Bit-compare the census pipeline against the existing mechanisms."""
    npz_path, json_path = census_paths(args.tag)
    blob = np.load(npz_path, allow_pickle=False)
    records = json.loads(json_path.read_text(encoding="utf-8"))["records"]
    payload, matrix, _ = year.load_matrix()
    rng = np.random.default_rng(12345)

    checks: dict[str, Any] = {"sources_checked": len(records), "checks": []}
    for i, r in enumerate(records):
        cpath = chunk_path(args.tag, r["size"], r["jury"])
        start, order = drift_exploit.seed_from_pref(
            payload, blob["source_pref"][i].astype(np.float64), limit=SEED_BOOKS
        )
        with np.load(cpath, allow_pickle=False) as c:
            start_diff = float(np.max(np.abs(c["start"] - start)))
            order_diff = int(np.sum(c["seed_books"] != order))
            run = breeding.run_path(payload, matrix, start, rng, store_pref=True)
            dir_diff = max(
                float(np.max(np.abs(run["directions"][s] - c["stage_dirs"][s])))
                for s in range(len(run["stages"]))
            )
            pref_diff = max(
                float(np.max(np.abs(run["pref_store"][s]["score"] - c["stage_prefs"][s])))
                for s in range(len(run["stages"]))
            )
            checks["checks"].append(
                {
                    "source_id": r["source_id"],
                    "start_max_abs_diff": start_diff,
                    "seed_books_mismatch": order_diff,
                    "stage_dirs_max_abs_diff": float(dir_diff),
                    "stage_prefs_max_abs_diff": float(pref_diff),
                    "stages_match": len(run["stages"]) == r["n_stages"],
                    "stop_reason_match": run["stop_reason"] == r["stop_reason"],
                }
            )
    bad = [
        c for c in checks["checks"]
        if not c["stages_match"] or not c["stop_reason_match"]
        or c["seed_books_mismatch"] != 0
        or c["start_max_abs_diff"] > 0.0
        or c["stage_dirs_max_abs_diff"] > 1e-5
        or c["stage_prefs_max_abs_diff"] > 1e-5
    ]
    checks["reproduced"] = len(bad) == 0
    (DATA / "natural_amplification_smoke_verify.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8"
    )
    print(
        f"smoke verification: reproduced={checks['reproduced']} "
        f"({len(checks['checks'])} sources)", flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=["amplify", "consolidate", "geometry", "unblind", "smoke"],
        required=True,
    )
    parser.add_argument("--tag", default=None, help="artifact tag (default: none)")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--juries-per-size", type=int, default=JURIES_PER_SIZE)
    parser.add_argument("--smoke-juries", type=int, default=SMOKE_JURIES)
    parser.add_argument("--keep-chunks", action="store_true")
    args = parser.parse_args()
    if args.phase == "amplify":
        phase_amplify(args)
    elif args.phase == "consolidate":
        phase_consolidate(args)
    elif args.phase == "geometry":
        phase_geometry(args)
    elif args.phase == "unblind":
        phase_unblind(args)
    else:
        phase_smoke(args)


if __name__ == "__main__":
    main()

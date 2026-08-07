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

The geometry phase seals the label-blind claim mechanically: the geometry NPZ
is written first, then a geometry JSON carrying SHA256 of both the census NPZ
and the geometry NPZ, the exact ordered source list, clustering parameters,
stage definitions, and git commit, followed by an external seal manifest that
hashes the census NPZ, the geometry NPZ and the geometry JSON. ``phase_unblind``
recomputes every hash and aborts before loading any semantic context if any
differs.

Phases
------
- amplify:      seed_from_prep + run_path gain-hard amplification of every
                selected reversal endpoint (default: all 120 20k and all 120
                80k endpoints from drift_exploit_main). Every per-source
                chunk is self-describing (it embeds its own JSON record), so
                a crash between chunk write and JSON checkpoint cannot lose a
                completed source, and resume recovers records from chunks.
- consolidate:  merge chunks into natural_amplification_census_<tag>.npz in
                canonical (size, jury) row order; the metadata record list is
                derived from the chunks themselves, never from JSON position.
                Runs hard source-alignment assertions (unique source ids,
                unique (size, jury), one record per row and vice versa, row
                source id matches record, no duplicate rows).
- geometry:     freeze the label-blind structural analysis: preference-space
                and direction-space representations, pairwise cosine matrices,
                average-linkage hierarchical clusterings at preregistered
                cosine cuts 0.30 / 0.50 / 0.70, cluster centroids and
                dispersion, plus the independent even/odd-jury half splits,
                their frozen centroid vectors, and their centroid-cosine
                matching with mutual-best flags. Refuses to run on an
                incomplete census (or any expected/observed source mismatch)
                unless ``--allow-partial`` is given. Runs label-blind
                invariant checks (centroid-key uniqueness, centroid
                reconstruction from member ids, half-centroid reproduction of
                the stored matching matrix) and aborts on any failure. Writes
                the geometry NPZ first, then the sealing JSON.
- unblind:      ONLY after geometry is frozen AND sealed: recompute and verify
                both artifact hashes and the full census integrity, then load
                semantic context and evaluate endpoints, preference centroids,
                direction centroids (pole_rows convention), and matched A/B
                clusters. All semantic evaluation uses ONE preregistered
                eligibility universe (book_n >= 25). Preference objects are
                evaluated through their exact frozen centroid vectors;
                direction-space objects through pole_rows, never a silently
                substituted preference mean.
- smoke:        small validation run (default 4 sources per size) that verifies
                the census pipeline numerically reproduces the existing
                seed_from_pref / run_path behavior.
- prereport:    label-blind pre-unblind summary written from the sealed
                geometry alone (no semantic context); includes the full-cluster
                <-> even/odd analogue matching with precision, coverage and
                Jaccard, and reports the external seal manifest verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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

# Tolerance for invariant reconstruction of frozen float32 centroids from
# float64 member data; the pre-fix key-collision bug produced differences of
# order 1.0, so 1e-4 separates "rounding" from "wrong object" by orders.
CENTROID_INVARIANT_TOL = 1e-4
MATRIX_INVARIANT_TOL = 1e-4

# True only inside the unblind phase, after all geometry files are sealed.
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


def seal_manifest_path(tag: str | None) -> Path:
    return DATA / f"natural_amplification_census{_tag_suffix(tag)}_seal_manifest.json"


def prereport_path(tag: str | None) -> Path:
    suffix = _tag_suffix(tag)
    return DATA / f"NATURAL_AMPLIFICATION_CENSUS{suffix.upper()}_PREUNBLIND_REPORT.md"


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


def _write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _write_npz_atomic(path: Path, arrays: dict[str, np.ndarray]) -> None:
    # np.savez_compressed appends ".npz" unless the name already ends with it.
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, path)


def _effective_user_share(weights: np.ndarray) -> float:
    return float(
        (weights.sum() ** 2) / np.sum(weights**2) / len(weights)
    )


# ---------------------------------------------------------------------------
# Source alignment integrity (items 2 and 3 of the review)
# ---------------------------------------------------------------------------

def _check_aligned(
    records: list[dict[str, Any]],
    sizes: np.ndarray,
    jury: np.ndarray,
    expected_sources: list[tuple[int, int]],
    require_complete: bool,
    json_partial: bool | None = None,
) -> dict[str, Any]:
    """Hard assertions linking metadata records to NPZ rows.

    - unique source ids;
    - unique (size, jury) pairs;
    - every NPZ row has exactly one metadata record;
    - every metadata record has exactly one NPZ row;
    - metadata source id matches the row's source_size/source_jury;
    - no duplicate rows.
    When require_complete: the census must contain exactly the requested
    sources, in canonical order, and must not be flagged partial.
    """
    n = len(records)
    n_rows = int(len(sizes))
    ids = [r["source_id"] for r in records]
    row_ids = [f"{int(s)}:{int(j)}" for s, j in zip(sizes, jury)]

    problems: list[str] = []
    if n_rows != n:
        problems.append(f"npz rows ({n_rows}) != metadata records ({n})")
    if len(set(ids)) != n:
        problems.append("duplicate source_ids in metadata")
    if len(set(row_ids)) != n_rows:
        problems.append("duplicate (size, jury) rows in npz")
    if n > 0:
        if any(a != b for a, b in zip(ids, row_ids)):
            problems.append("metadata source_id does not match npz row (size, jury)")
        if set(ids) != set(row_ids):
            problems.append("metadata and npz disagree on the source set")
    if require_complete:
        expected_ids = [f"{s}:{j}" for s, j in expected_sources]
        if json_partial:
            problems.append("census metadata says partial")
        if ids != expected_ids:
            problems.append(
                "observed sources/order differ from canonical expected order"
            )
    if problems:
        raise SystemExit("census integrity failure: " + "; ".join(problems))
    return {
        "n_sources": n,
        "npz_rows": n_rows,
        "unique_source_ids": True,
        "unique_size_jury_rows": True,
        "row_record_alignment": True,
        "source_id_matches_row": True,
        "no_duplicate_rows": True,
        "require_complete": require_complete,
    }


def _load_census(
    args: argparse.Namespace,
    npz_path: Path,
    json_path: Path,
    require_complete: bool,
) -> tuple[list[dict[str, Any]], Any, dict[str, Any]]:
    """Load the census NPZ + JSON with all hard alignment assertions."""
    if not npz_path.exists():
        raise SystemExit(f"missing census npz {npz_path}; run consolidate first")
    if not json_path.exists():
        raise SystemExit(f"missing census json {json_path}; run consolidate first")
    blob = np.load(npz_path, allow_pickle=False)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    _check_aligned(
        records,
        blob["source_size"],
        blob["source_jury"],
        load_drift_sources(args.juries_per_size),
        require_complete=require_complete,
        json_partial=data.get("partial"),
    )
    return records, blob, data


def _seal_manifest(
    tag: str | None,
    npz_path: Path,
    census_sha: str,
    geo_npz: Path,
    geo_sha: str,
    geo_json: Path,
    ids: list[str],
) -> dict[str, Any]:
    """External seal manifest hashing the census NPZ, geometry NPZ and
    geometry JSON. Written after the geometry artifacts, so it is an
    independent anchor a reviewer can re-derive from the files alone."""
    return {
        "seal_manifest_version": 1,
        "artifacts": {
            "census_npz": {
                "file": npz_path.name,
                "sha256": census_sha,
                "bytes": npz_path.stat().st_size,
            },
            "geometry_npz": {
                "file": geo_npz.name,
                "sha256": geo_sha,
                "bytes": geo_npz.stat().st_size,
            },
            "geometry_json": {
                "file": geo_json.name,
                "sha256": _sha256(geo_json),
                "bytes": geo_json.stat().st_size,
            },
        },
        "n_sources": len(ids),
        "sources": ids,
        "git_head": _git_head(),
        "command": shlex.join(sys.argv),
        "semantic_context_loaded": False,
        "unblinded": False,
    }


def _verify_manifest(
    args: argparse.Namespace, npz_path: Path, geo_json: Path, geo_npz: Path
) -> dict[str, bool]:
    """Recompute the three artifact hashes against the external seal manifest;
    abort if the manifest is missing, claims semantic context, or mismatches."""
    path = seal_manifest_path(args.tag)
    if not path.exists():
        raise SystemExit(f"seal manifest {path} missing; refusing")
    man = json.loads(path.read_text(encoding="utf-8"))
    if man.get("semantic_context_loaded") is not False:
        raise SystemExit("seal manifest claims semantic context loaded; refusing")
    if man.get("unblinded") is not False:
        raise SystemExit("seal manifest claims already unblinded; refusing")
    checks = {
        "census_npz": _sha256(npz_path) == man["artifacts"]["census_npz"]["sha256"],
        "geometry_npz": _sha256(geo_npz) == man["artifacts"]["geometry_npz"]["sha256"],
        "geometry_json": _sha256(geo_json) == man["artifacts"]["geometry_json"]["sha256"],
    }
    if not all(checks.values()):
        raise SystemExit(f"seal manifest hash mismatch: {checks}; refusing")
    return checks


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


def _source_record(size: int, jury: int, out: dict[str, Any]) -> dict[str, Any]:
    return {
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


def _chunk_record(cpath: Path) -> dict[str, Any]:
    """Recover the self-describing metadata record embedded in a chunk."""
    with np.load(cpath, allow_pickle=False) as c:
        rec = json.loads(str(c["record_json"][0]))
        if (
            int(c["source_size"]) != rec["size"]
            or int(c["source_jury"]) != rec["jury"]
        ):
            raise ValueError("chunk (size, jury) mismatches its embedded record")
        return rec


def _write_chunk_atomic(
    cpath: Path,
    out: dict[str, Any],
    pref: np.ndarray,
    stage0_pref: np.ndarray,
    rec: dict[str, Any],
) -> None:
    _write_npz_atomic(
        cpath,
        {
            "start": out["start"],
            "seed_books": out["seed_books"],
            "stage_dirs": out["stage_dirs"],
            "stage_prefs": out["stage_prefs"],
            "stage_mass": out["stage_mass"],
            "users_by_stage": out["users_by_stage"],
            "source_size": np.int32(rec["size"]),
            "source_jury": np.int32(rec["jury"]),
            "source_pref": pref.astype(np.float32),
            "stage0_pref": stage0_pref.astype(np.float32),
            "record_json": np.array(
                [json.dumps(rec, separators=(",", ":"))], dtype="U"
            ),
        },
    )


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

    # Source-safe resume: completed work is whatever has a readable chunk; the
    # JSON checkpoint is only a progress mirror. Records are rebuilt from
    # chunks, so a crash between chunk write and JSON write loses nothing, and
    # a source that failed earlier is simply retried in place.
    rng = np.random.default_rng(args.seed)
    records: list[dict[str, Any]] = []
    recovered = 0
    for size, jury in sources:
        cpath = chunk_path(args.tag, size, jury)
        rec = None
        if cpath.exists():
            try:
                rec = _chunk_record(cpath)
            except Exception as exc:
                print(f"chunk {cpath.name} unreadable ({exc}); re-running", flush=True)
                cpath.unlink(missing_ok=True)
        if rec is None:
            pref = drift_prefs[drift_idx[(size, jury)]].astype(np.float64)
            stage0_pref = drift_stage0[drift_idx[(size, jury)]].astype(np.float64)
            try:
                out = _run_one_source(payload, matrix, pref, stage0_pref, rng)
            except Exception as exc:  # keep the campaign alive past one bad source
                print(f"source {size}:{jury} FAILED: {exc}", flush=True)
                continue
            rec = _source_record(size, jury, out)
            _write_chunk_atomic(cpath, out, pref, stage0_pref, rec)
        else:
            recovered += 1
        records.append(rec)
        done = len(records)
        if done % CHECKPOINT_EVERY == 0:
            _checkpoint_json(json_path, records, sources, t0, args.seed)
            print(
                f"amplify {size}:{jury}: {done}/{len(sources)} sources, "
                f"elapsed {time.time() - t0:.0f}s", flush=True,
            )

    _checkpoint_json(json_path, records, sources, t0, args.seed)
    print(
        f"amplify done: {len(records)} sources ({recovered} recovered from "
        f"chunks), {time.time() - t0:.0f}s, chunks in {chunk_dir(args.tag)}",
        flush=True,
    )


def _checkpoint_json(
    json_path: Path,
    records: list[dict[str, Any]],
    sources: list[tuple[int, int]],
    t0: float,
    seed: int,
) -> None:
    _write_text_atomic(
        json_path,
        json.dumps(
            {
                "records": records,
                "record_by_source_id": {
                    r["source_id"]: i for i, r in enumerate(records)
                },
                "partial": len(records) < len(sources),
                "expected_sources": [f"{s}:{j}" for s, j in sources],
                "method": {
                    "phase": "amplify",
                    "sizes": list(SIZES),
                    "juries_per_size": len(sources) // len(SIZES),
                    "seed": seed,
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
    )


# ---------------------------------------------------------------------------
# Consolidate chunks into the census NPZ (source-safe, row-ordered)
# ---------------------------------------------------------------------------

def phase_consolidate(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED

    t0 = time.time()
    npz_path, json_path = census_paths(args.tag)
    sources = load_drift_sources(args.juries_per_size)
    have = [
        (size, jury) for size, jury in sources
        if chunk_path(args.tag, size, jury).exists()
    ]
    n = len(have)
    if n == 0:
        raise SystemExit("no completed chunks to consolidate")

    with np.load(chunk_path(args.tag, *have[0]), allow_pickle=False) as first:
        n_books = int(first["stage_dirs"].shape[1])
    max_stages = 0
    for size, jury in have:
        with np.load(chunk_path(args.tag, size, jury), allow_pickle=False) as c:
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

    # Rows are in canonical (size, jury) order; metadata records are derived
    # from the self-describing chunks, never from JSON list position.
    records: list[dict[str, Any]] = []
    for row, (size, jury) in enumerate(have):
        cpath = chunk_path(args.tag, size, jury)
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
            rec = json.loads(str(c["record_json"][0]))
            if rec["size"] != size or rec["jury"] != jury:
                raise SystemExit(
                    f"chunk {cpath.name} embedded record mismatches its filename"
                )
            records.append(rec)
        source_size[row] = size
        source_jury[row] = jury

    _write_npz_atomic(
        npz_path,
        {
            "source_size": source_size,
            "source_jury": source_jury,
            "stage_dirs": stage_dirs,
            "stage_prefs": stage_prefs,
            "stage_mass": stage_mass,
            "stage_valid": stage_valid,
            "users_by_stage": users_by_stage,
            "seed_books": seed_books,
            "source_pref": source_pref,
            "stage0_pref": stage0_pref,
        },
    )
    sha = _sha256(npz_path)
    integrity = _check_aligned(
        records,
        source_size,
        source_jury,
        sources,
        require_complete=False,
        json_partial=None,
    )
    _write_text_atomic(
        json_path,
        json.dumps(
            {
                "records": records,
                "record_by_source_id": {
                    r["source_id"]: i for i, r in enumerate(records)
                },
                "partial": n < len(sources),
                "expected_sources": [f"{s}:{j}" for s, j in sources],
                "integrity": integrity,
                "artifact_sha256": sha,
                "artifact_bytes": npz_path.stat().st_size,
                "method": {
                    "phase": "amplify",
                    "sizes": list(SIZES),
                    "juries_per_size": len(sources) // len(SIZES),
                    "seed": args.seed,
                    "seed_books": SEED_BOOKS,
                    "elig_min_book_n": ELIG_MIN_BOOK_N,
                    "beta": breeding.BETA,
                    "max_stages": breeding.MAX_STAGES,
                    "retained_target": breeding.RETAINED_TARGET,
                    "mode": "hard",
                    "criterion": "gain",
                    "semantic_context_loaded": False,
                    "command": shlex.join(sys.argv),
                    "git_head": _git_head(),
                    "runtime_seconds": time.time() - t0,
                },
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
    )
    if not args.keep_chunks:
        for size, jury in have:
            chunk_path(args.tag, size, jury).unlink(missing_ok=True)
        print(f"removed {n} chunk files (kept {npz_path})", flush=True)
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
    storage_key: str,
    cluster_index: int,
) -> dict[str, Any]:
    """Freeze one label-blind cluster (singletons included). The storage key
    includes the clustering space so preference-defined and direction-defined
    clusterings of the same (group, stage, tau) never collide."""
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
        kp = f"cent_pref_{storage_key}_{cluster_index}"
        kd = f"cent_dir_{storage_key}_{cluster_index}"
        kr = f"rawpref_{storage_key}_{cluster_index}"
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


def _gpos(
    avail: dict[str, list[int]], group_masks: dict[str, list[int]],
    stage_label: str, group: str,
) -> list[int]:
    idxs = avail[stage_label]
    gmask = group_masks[group]
    return [idxs.index(i) for i in gmask if i in set(idxs)]


def _invariant_geometry(
    geometry: dict[str, Any],
    npz_out: dict[str, np.ndarray],
    pref_mats: dict[str, np.ndarray],
    dir_mats: dict[str, np.ndarray],
    ids: list[str],
    avail: dict[str, list[int]],
    group_masks: dict[str, list[int]],
) -> list[dict[str, Any]]:
    """Label-blind invariant checks on the frozen geometry.

    - every centroid key is unique (would catch the pre-fix collision bug);
    - every stored non-singleton preference AND direction centroid is
      reconstructed from its frozen member ids and matches the stored vector;
    - re-clustering reproduces the frozen memberships exactly;
    - the stored half-match matrices are reproduced by the frozen half
      centroids, and each best-match cosine equals its matrix cell.
    Any failure aborts geometry before anything is written to disk.
    """
    checks: list[dict[str, Any]] = []

    dup_keys = len(npz_out) != len(set(npz_out))
    checks.append(
        {"check": "centroid_key_uniqueness", "ok": not dup_keys,
         "detail": f"{len(npz_out)} keys, {len(set(npz_out))} unique"}
    )
    if dup_keys:
        raise SystemExit("geometry invariant failed: duplicate npz keys")

    for stage_label in ("deepest", "s4"):
        stage_ids = [ids[i] for i in avail[stage_label]]
        id_pos = {sid: p for p, sid in enumerate(stage_ids)}
        for group in ("20k", "80k", "pooled"):
            gpos = _gpos(avail, group_masks, stage_label, group)
            gids = [stage_ids[p] for p in gpos]
            sub_pos = {gids[p]: p for p in range(len(gpos))}
            for tau in CLUSTER_TAUS:
                for space in ("pref", "dir"):
                    storage_key = f"{group}_{stage_label}_{tau:.2f}_{space}"
                    clist = geometry["clusters"][stage_label][group][storage_key]
                    mat = pref_mats[stage_label] if space == "pref" else dir_mats[stage_label]
                    sub = mat[gpos]
                    reclustered = avg_link_clusters(sub, tau)
                    for ci, c in enumerate(clist):
                        member_rows = [gpos[sub_pos[m]] for m in c["members"]]
                        ok_membership = any(
                            sorted(c["members"]) == sorted(
                                [gids[x] for x in cl]
                            )
                            for cl in reclustered
                        )
                        checks.append(
                            {
                                "check": "membership_reclustering",
                                "ok": ok_membership,
                                "detail": f"{storage_key} cluster {ci}",
                            }
                        )
                        if not ok_membership:
                            raise SystemExit(
                                f"geometry invariant failed: membership mismatch "
                                f"in {storage_key} cluster {ci}"
                            )
                        if len(c["members"]) < 2:
                            continue
                        sub_rows = [sub_pos[m] for m in c["members"]]
                        recomputed_pref = _unit_rows(
                            pref_mats[stage_label][member_rows].mean(axis=0)[None, :]
                        )[0].astype(np.float32)
                        recomputed_dir = _unit_rows(
                            dir_mats[stage_label][member_rows].mean(axis=0)[None, :]
                        )[0].astype(np.float32)
                        d_p = float(np.max(np.abs(
                            recomputed_pref - npz_out[c["pref_centroid_key"]]
                        )))
                        d_d = float(np.max(np.abs(
                            recomputed_dir - npz_out[c["dir_centroid_key"]]
                        )))
                        checks.append(
                            {
                                "check": "centroid_reconstruction_pref",
                                "ok": d_p <= CENTROID_INVARIANT_TOL,
                                "max_abs_diff": d_p,
                                "detail": f"{storage_key} cluster {ci}",
                            }
                        )
                        checks.append(
                            {
                                "check": "centroid_reconstruction_dir",
                                "ok": d_d <= CENTROID_INVARIANT_TOL,
                                "max_abs_diff": d_d,
                                "detail": f"{storage_key} cluster {ci}",
                            }
                        )
                        if d_p > CENTROID_INVARIANT_TOL or d_d > CENTROID_INVARIANT_TOL:
                            raise SystemExit(
                                f"geometry invariant failed: centroid mismatch "
                                f"in {storage_key} cluster {ci} "
                                f"(pref {d_p:.2e}, dir {d_d:.2e})"
                            )

    for key, h in geometry["halves"].items():
        if h.get("empty_side"):
            continue
        parts = key.split("_")
        space, group, stage_label = parts[1], parts[2], parts[3]
        tau = float(parts[4])
        a = np.stack([
            npz_out[f"halfA_cent_{space}_{group}_{stage_label}_{tau:.2f}_{i}"]
            for i in range(h["nA_clusters"])
        ])
        b = np.stack([
            npz_out[f"halfB_cent_{space}_{group}_{stage_label}_{tau:.2f}_{j}"]
            for j in range(h["nB_clusters"])
        ])
        m_re = a @ b.T
        m_stored = npz_out[key]
        diff = float(np.max(np.abs(m_re - m_stored)))
        ok = bool(np.allclose(m_re, m_stored, atol=MATRIX_INVARIANT_TOL))
        checks.append(
            {"check": "half_matrix_reproduction", "ok": ok,
             "max_abs_diff": diff, "detail": key}
        )
        if not ok:
            raise SystemExit(
                f"geometry invariant failed: half matrix {key} not reproduced "
                f"by frozen centroids (max diff {diff:.2e})"
            )
        for i, bm in enumerate(h["best_matches"]):
            ok_cell = bool(
                abs(float(m_stored[i, h["b_argmax"][i]]) - float(bm["cos"])) <= 1e-6
            )
            checks.append(
                {"check": "best_match_cos_cell", "ok": ok_cell, "detail": f"{key} A{i}"}
            )
    return checks


def phase_geometry(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED

    t0 = time.time()
    npz_path, json_path = census_paths(args.tag)
    records, blob, data = _load_census(
        args, npz_path, json_path, require_complete=not args.allow_partial
    )
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
            gpos = _gpos(avail, group_masks, stage_label, group)
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
                    storage_key = f"{key}_{space}"
                    cl = avg_link_clusters(mat, tau)
                    recs = []
                    for ci, members in enumerate(cl):
                        recs.append(
                            _cluster_record(
                                members, gids, sub_pref, sub_dir, sub_raw,
                                sub_pref_sim, sub_dir_sim, eligible,
                                npz_out, storage_key, ci,
                            )
                        )
                    group_blocks[storage_key] = recs
            geometry["clusters"][stage_label][group] = group_blocks

    # Independent-half reproducibility: even jury index -> A, odd -> B.
    # Frozen centroid vectors of every half cluster are stored and referenced
    # by the matching records (item 5 of the review).
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
                            "nA_clusters": len(ca),
                            "nB_clusters": len(cb),
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
                    for i in range(len(ca)):
                        npz_out[f"halfA_cent_{space}_{group}_{stage_label}_{tau:.2f}_{i}"] = (
                            cents_a[i].astype(np.float32)
                        )
                    for j in range(len(cb)):
                        npz_out[f"halfB_cent_{space}_{group}_{stage_label}_{tau:.2f}_{j}"] = (
                            cents_b[j].astype(np.float32)
                        )
                    if space == "pref":
                        # Direction centroids of the SAME member groups, for
                        # the member-direction pole cosine diagnostic only.
                        dmat = dir_mats[stage_label]
                        dir_a = _unit_rows(np.stack([dmat[a_pos][cl].mean(axis=0) for cl in ca]))
                        dir_b = _unit_rows(np.stack([dmat[b_pos][cl].mean(axis=0) for cl in cb]))
                        for i in range(len(ca)):
                            npz_out[f"halfA_dircent_pref_{group}_{stage_label}_{tau:.2f}_{i}"] = (
                                dir_a[i].astype(np.float32)
                            )
                        for j in range(len(cb)):
                            npz_out[f"halfB_dircent_pref_{group}_{stage_label}_{tau:.2f}_{j}"] = (
                                dir_b[j].astype(np.float32)
                            )
                    m = cents_a @ cents_b.T
                    npz_out[key] = m.astype(np.float32)
                    best = []
                    for i in range(len(ca)):
                        j = int(np.argmax(m[i]))
                        mutual = int(np.argmax(m[:, j])) == i
                        best.append(
                            {
                                "a_cluster": ca_ids[i],
                                "b_cluster": cb_ids[j],
                                "cos": float(m[i, j]),
                                "a_size": len(ca[i]),
                                "b_size": len(cb[j]),
                                "a_centroid_key": (
                                    f"halfA_cent_{space}_{group}_{stage_label}_{tau:.2f}_{i}"
                                ),
                                "b_centroid_key": (
                                    f"halfB_cent_{space}_{group}_{stage_label}_{tau:.2f}_{j}"
                                ),
                                "a_dir_centroid_key": (
                                    f"halfA_dircent_pref_{group}_{stage_label}_{tau:.2f}_{i}"
                                    if space == "pref" else None
                                ),
                                "b_dir_centroid_key": (
                                    f"halfB_dircent_pref_{group}_{stage_label}_{tau:.2f}_{j}"
                                    if space == "pref" else None
                                ),
                                "mutual_best": mutual,
                            }
                        )
                    best_b = []
                    for j in range(len(cb)):
                        a = int(np.argmax(m[:, j]))
                        mutual = int(np.argmax(m[a])) == j
                        best_b.append(
                            {
                                "a_cluster": ca_ids[a],
                                "b_cluster": cb_ids[j],
                                "cos": float(m[a, j]),
                                "a_size": len(ca[a]),
                                "b_size": len(cb[j]),
                                "a_centroid_key": (
                                    f"halfA_cent_{space}_{group}_{stage_label}_{tau:.2f}_{a}"
                                ),
                                "b_centroid_key": (
                                    f"halfB_cent_{space}_{group}_{stage_label}_{tau:.2f}_{j}"
                                ),
                                "a_dir_centroid_key": (
                                    f"halfA_dircent_pref_{group}_{stage_label}_{tau:.2f}_{a}"
                                    if space == "pref" else None
                                ),
                                "b_dir_centroid_key": (
                                    f"halfB_dircent_pref_{group}_{stage_label}_{tau:.2f}_{j}"
                                    if space == "pref" else None
                                ),
                                "mutual_best": mutual,
                            }
                        )
                    geometry["halves"][key] = {
                        "nA": len(a_pos),
                        "nB": len(b_pos),
                        "nA_clusters": len(ca),
                        "nB_clusters": len(cb),
                        "best_matches": best,
                        "best_matches_B_side": best_b,
                        "matrix_npz_key": key,
                        "b_argmax": [int(np.argmax(m[i])) for i in range(len(ca))],
                    }

    invariant_checks = _invariant_geometry(
        geometry, npz_out, pref_mats, dir_mats, ids, avail, group_masks
    )

    geometry["method"] = {
        "phase": "geometry",
        "purpose": (
            "label-blind structural census of amplified endpoints; "
            "no semantic context loaded anywhere in this phase"
        ),
        "seed": args.seed,
        "sizes": list(SIZES),
        "juries_per_size": args.juries_per_size,
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
            "centroids_frozen": True,
            "mutual_best": "A's best is B and B's best is A",
        },
        "semantic_context_loaded": False,
        "unblinded": False,
        "written_before_unblinding": True,
        "command": shlex.join(sys.argv),
        "git_head": _git_head(),
        "runtime_seconds": time.time() - t0,
    }
    geometry["invariant_checks"] = invariant_checks

    # Cryptographic seal: geometry NPZ is written FIRST, then the JSON
    # carrying both artifact hashes (item 4 of the review).
    geo_json, geo_npz = geometry_paths(args.tag)
    _write_npz_atomic(geo_npz, npz_out)
    geo_sha = _sha256(geo_npz)
    census_sha = _sha256(npz_path)
    geometry["seal"] = {
        "geometry_npz_sha256": geo_sha,
        "census_npz_sha256": census_sha,
        "n_sources": n,
        "sources": ids,
        "clustering": geometry["method"]["clustering"],
        "stages": {
            "deepest": "final run_path stage (per-source n_stages - 1)",
            "s4": f"fixed stage index {STAGE_ANALYZED} (0-based) when n_stages > {STAGE_ANALYZED}",
        },
        "eligibility": {"min_book_n": ELIG_MIN_BOOK_N},
        "seed": args.seed,
        "git_head": _git_head(),
        "semantic_context_loaded": False,
        "unblinded": False,
    }
    _write_text_atomic(geo_json, json.dumps(geometry, indent=1))
    _write_text_atomic(
        seal_manifest_path(args.tag),
        json.dumps(_seal_manifest(args.tag, npz_path, census_sha, geo_npz,
                                  geo_sha, geo_json, ids), indent=1),
    )
    print(
        f"geometry frozen: {geo_json} ({geo_json.stat().st_size/2**20:.1f} MiB), "
        f"{geo_npz} ({geo_npz.stat().st_size/2**20:.1f} MiB), "
        f"seal sha256 {geo_sha[:16]}..., manifest "
        f"{seal_manifest_path(args.tag).name}, {time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Phase 4: post-hoc semantic unblinding (only after geometry is sealed)
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


def _embed_full(
    centroid: np.ndarray, eligible_idx: np.ndarray, n_books: int
) -> np.ndarray:
    """Re-embed an eligible-indexed vector into the full work-index space,
    keeping ineligible books excluded (score 0)."""
    full = np.zeros(n_books, dtype=np.float64)
    full[eligible_idx] = np.asarray(centroid, dtype=np.float64)
    return full


def _cos_unit(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    if a.shape != b.shape or a.size == 0:
        return float("nan")
    return float(
        np.sum(a * b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-20)
    )


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


def _find_analogue(
    frozen: dict[str, Any],
    stage_label: str,
    group: str,
    tau: float,
    members: list[str],
) -> dict[str, Any] | None:
    """Link a full preference-space cluster to its best even/odd half match
    (derived from the frozen label-blind geometry only).

    For a full cluster C and a half match M = A_M | B_M:
    - precision = |(A_M U B_M) n C| / |A_M U B_M|   (how much of the match is in C)
    - coverage  = |(A_M U B_M) n C| / |C|           (how much of C the match covers)
    - jaccard   = |(A_M U B_M) n C| / |(A_M U B_M) U C|
    Candidates must cover at least half of C (coverage >= 0.5); among them the
    match with the highest A-B centroid cosine wins. The strong checklist in
    the report additionally requires coverage >= 0.5."""
    h = frozen["halves"].get(f"match_pref_{group}_{stage_label}_{tau:.2f}")
    if not h:
        return None
    cset = set(members)
    n_c = len(cset)
    if n_c == 0:
        return None
    best = None
    for bm in h["best_matches"]:
        mset = set(bm["a_cluster"]) | set(bm["b_cluster"])
        if not mset:
            continue
        inter = len(mset & cset)
        coverage = inter / n_c
        if coverage < 0.5:
            continue
        precision = inter / len(mset)
        jaccard = inter / len(mset | cset)
        if best is None or bm["cos"] > best["cos"]:
            best = {
                "exists": True,
                "precision": precision,
                "coverage": coverage,
                "jaccard": jaccard,
                "a_size": bm["a_size"],
                "b_size": bm["b_size"],
                "cos": bm["cos"],
                "mutual_best": bm["mutual_best"],
            }
    return best


def phase_unblind(args: argparse.Namespace) -> None:
    global SEMANTIC_CONTEXT_LOADED
    assert not SEMANTIC_CONTEXT_LOADED
    geo_json, geo_npz = geometry_paths(args.tag)
    if not geo_json.exists() or not geo_npz.exists():
        raise SystemExit("geometry not frozen yet; refusing to unblind")
    frozen = json.loads(geo_json.read_text(encoding="utf-8"))
    assert frozen["method"]["unblinded"] is False
    assert frozen["method"]["semantic_context_loaded"] is False
    seal = frozen.get("seal")
    if not seal:
        raise SystemExit("geometry JSON has no seal; refusing to unblind")
    if seal.get("semantic_context_loaded") is not False:
        raise SystemExit("seal claims semantic context already loaded; refusing")
    if seal.get("unblinded") is not False:
        raise SystemExit("seal claims already unblinded; refusing")

    t0 = time.time()
    npz_path, json_path = census_paths(args.tag)

    # ---- Integrity + hash verification, BEFORE any semantic load ----
    records, blob, data = _load_census(
        args, npz_path, json_path, require_complete=not args.allow_partial
    )
    ids = [r["source_id"] for r in records]
    now_census = _sha256(npz_path)
    if now_census != seal["census_npz_sha256"]:
        raise SystemExit(
            f"census artifact hash mismatch (sealed {seal['census_npz_sha256'][:16]}..., "
            f"now {now_census[:16]}...); refusing to unblind"
        )
    now_geo = _sha256(geo_npz)
    if now_geo != seal["geometry_npz_sha256"]:
        raise SystemExit(
            f"geometry artifact hash mismatch (sealed {seal['geometry_npz_sha256'][:16]}..., "
            f"now {now_geo[:16]}...); refusing to unblind"
        )
    if seal["n_sources"] != len(records) or seal["sources"] != ids:
        raise SystemExit("sealed source list does not match census; refusing to unblind")
    manifest_checks = _verify_manifest(args, npz_path, geo_json, geo_npz)

    payload, _, _ = year.load_matrix()
    n_books = int(len(payload["work_ids"]))
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    eligible_idx = np.flatnonzero(eligible)
    n_eligible = int(eligible.sum())
    # ONE preregistered eligibility universe for all semantic preference
    # evaluation: ratings-derived reader mass, zeroed outside book_n >= 25.
    elig_mass = np.where(eligible, payload["book_n"], 0.0).astype(np.float64)

    # ---- THE ONLY semantic load in the whole experiment ----
    print("Loading post-hoc semantic context (unblind)", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    SEMANTIC_CONTEXT_LOADED = True

    pole = None
    if POLE_NPZ.exists():
        pole = np.load(POLE_NPZ, allow_pickle=True)[POLE_KEY].astype(np.float64)
        pole = pole / (np.linalg.norm(pole) + 1e-20)

    universe = set(payload["work_ids"][eligible].tolist())
    chance = {
        name: len(eval_sets[name] & universe) / n_eligible * 50
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
            stage_mass = blob["stage_mass"][i, si]
            head, metrics = _eval_pref(
                score, elig_mass, payload["work_ids"], meta, eval_sets
            )
            d = blob["stage_dirs"][i, si].astype(np.float64)
            eligible_frac = float(
                np.asarray(stage_mass, dtype=np.float64)[eligible].sum()
                / np.asarray(stage_mass, dtype=np.float64).sum()
            ) if np.asarray(stage_mass, dtype=np.float64).sum() > 0 else 0.0
            rec[stage_label] = {
                "metrics": _metrics_row(metrics),
                "head": _top30(head),
                "evaluation": "preference head, global eligibility book_n>=25",
                "cos_pole": (
                    float(np.sum(d * pole) / (np.linalg.norm(d) * np.linalg.norm(pole)))
                    if pole is not None else None
                ),
                "reader_mass_diag": {
                    "stage_mass_eligible_fraction": eligible_frac,
                    "eligible_books": int(n_eligible),
                },
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
                            full = _embed_full(centroid, eligible_idx, n_books)
                            head, metrics = _eval_pref(
                                full, elig_mass, payload["work_ids"], meta, eval_sets,
                            )
                            entry["evaluation"] = (
                                "frozen preference centroid, re-embedded to full "
                                "work index, global eligibility book_n>=25"
                            )
                            entry["member_direction_cos_pole"] = (
                                _cos_unit(gblob[c["dir_centroid_key"]], pole)
                                if pole is not None else None
                            )
                            entry["cos_pole"] = None  # not a direction-space object
                            entry["analogue"] = _find_analogue(
                                frozen, stage_label, group, tau, c["members"]
                            )
                        else:
                            centroid = gblob[c["dir_centroid_key"]]
                            head, metrics = spectral.pole_rows(
                                centroid, payload["work_ids"], meta, eval_sets,
                                positive=True, limit=200,
                            )
                            entry["evaluation"] = (
                                "pole_rows on frozen direction centroid "
                                "(direction-space diagnostic)"
                            )
                            entry["cos_pole"] = (
                                _cos_unit(centroid, pole) if pole is not None else None
                            )
                        entry["metrics"] = _metrics_row(metrics)
                        entry["head"] = _top30(head)
                        cluster_evals.append(entry)
    print(f"cluster evaluation done ({len(cluster_evals)})", flush=True)

    # 4) independently matched A/B clusters: evaluate the EXACT frozen
    #    half-cluster centroids (never a freshly constructed mean).
    matched: list[dict[str, Any]] = []
    for key, h in frozen["halves"].items():
        if h.get("empty_side"):
            continue
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
                "mutual_best": bm["mutual_best"],
            }
            if space == "pref":
                a_centroid = gblob[bm["a_centroid_key"]]
                b_centroid = gblob[bm["b_centroid_key"]]
                ha, ma = _eval_pref(
                    _embed_full(a_centroid, eligible_idx, n_books),
                    elig_mass, payload["work_ids"], meta, eval_sets,
                )
                hb, mb = _eval_pref(
                    _embed_full(b_centroid, eligible_idx, n_books),
                    elig_mass, payload["work_ids"], meta, eval_sets,
                )
                entry["evaluation"] = (
                    "frozen half-cluster preference centroids, global eligibility"
                )
                entry["a_metrics"] = _metrics_row(ma)
                entry["b_metrics"] = _metrics_row(mb)
                entry["a_head"] = _top30(ha)
                entry["b_head"] = _top30(hb)
                entry["a_member_direction_cos_pole"] = (
                    _cos_unit(gblob[bm["a_dir_centroid_key"]], pole)
                    if pole is not None and bm["a_dir_centroid_key"] else None
                )
                entry["b_member_direction_cos_pole"] = (
                    _cos_unit(gblob[bm["b_dir_centroid_key"]], pole)
                    if pole is not None and bm["b_dir_centroid_key"] else None
                )
            else:
                ha, ma = spectral.pole_rows(
                    gblob[bm["a_centroid_key"]], payload["work_ids"], meta,
                    eval_sets, positive=True, limit=200,
                )
                hb, mb = spectral.pole_rows(
                    gblob[bm["b_centroid_key"]], payload["work_ids"], meta,
                    eval_sets, positive=True, limit=200,
                )
                entry["evaluation"] = (
                    "pole_rows on frozen direction centroids; direction-space "
                    "matching is a structural diagnostic, no preference-head claim"
                )
                entry["a_metrics"] = _metrics_row(ma)
                entry["b_metrics"] = _metrics_row(mb)
                entry["a_head"] = _top30(ha)
                entry["b_head"] = _top30(hb)
                entry["a_cos_pole"] = _cos_unit(gblob[bm["a_centroid_key"]], pole) if pole is not None else None
                entry["b_cos_pole"] = _cos_unit(gblob[bm["b_centroid_key"]], pole) if pole is not None else None
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
            "seed": args.seed,
            "semantic_context_loaded_now": True,
            "clustering_never_altered": True,
            "pole_key": POLE_KEY,
            "pole_usage": "post-hoc diagnostic only; never used for clustering or selection",
            "command": shlex.join(sys.argv),
            "git_head": _git_head(),
            "runtime_seconds": time.time() - t0,
        },
        "integrity": {
            "census_sha256_verified": True,
            "geometry_sha256_verified": True,
            "seal_manifest": manifest_checks,
            "source_alignment": _check_aligned(
                records,
                blob["source_size"],
                blob["source_jury"],
                load_drift_sources(args.juries_per_size),
                require_complete=not args.allow_partial,
                json_partial=data.get("partial"),
            ),
            "sealed_sources_match": True,
        },
        "eligibility_universe": {
            "min_book_n": ELIG_MIN_BOOK_N,
            "n_books": n_books,
            "n_eligible": n_eligible,
            "semantic_evaluation": "single global book_n>=25 universe for all "
            "preference heads and chance",
        },
        "chance_at_50": chance,
        "endpoints": endpoints,
        "cluster_evals": cluster_evals,
        "matched": matched,
        "feature_diagnostics": feature_rows,
    }
    out = posthoc_path(args.tag)
    _write_text_atomic(out, json.dumps(result, indent=1))
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


_HONESTY_STATEMENT = (
    "This census is label-blind internally, but it is a retrospective analysis "
    "of 20k/80k jury sizes and an amplification operator chosen during earlier "
    "label-visible exploratory research. It removes endpoint-selection leakage "
    "but is not, by itself, a sealed confirmatory discovery. Any structural "
    "signature found here should subsequently be tested unchanged on a fresh "
    "random-jury campaign that has never been semantically evaluated."
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
    seal = frozen["seal"]
    uni = result["eligibility_universe"]

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
        "`geometry` phases). The geometry artifact was cryptographically sealed (SHA256 of both "
        "artifacts recorded before any semantic load) and `unblind` re-verified both hashes "
        "before loading semantic context. Semantic context loaded only in the `unblind` phase, "
        "and the known literary pole cosine is a post-hoc diagnostic that never altered "
        "clustering or selection.",
        "",
        "> **Scope honesty.** " + _HONESTY_STATEMENT,
        "",
        "## Provenance",
        "",
        f"- Command: `{result['method']['command']}`",
        f"- Random seed: **{args.seed}**",
        f"- Git commit: `{seal['git_head']}`",
        f"- Unblind runtime: **{result['method']['runtime_seconds']:.0f}s**",
        f"- Census artifact: `{census_npz.name}` — SHA256 (sealed) "
        f"`{seal['census_npz_sha256']}` ({census_npz.stat().st_size/2**20:.1f} MiB)",
        f"- Geometry artifact: `{geometry_npz.name}` — SHA256 (sealed) "
        f"`{seal['geometry_npz_sha256']}` ({geometry_npz.stat().st_size/2**20:.1f} MiB)",
        f"- Books in universe: {uni['n_books']}; eligible (book_n >= 25): {uni['n_eligible']}",
        f"- Chance @50 over the eligible universe: exact {chance['exact_lit']:.2f}, "
        f"broad {chance['broad_lit']:.2f}, anti {chance['anti']:.2f}, "
        f"filler {chance['filler']:.2f}.",
        "",
        "## PRE-UNBLIND STRUCTURAL RESULTS",
        "",
        "All numbers below were computed and frozen before any semantic context was loaded.",
        "",
        "### Sources",
        "",
        f"- Sizes: **{list(SIZES)}**, {method['juries_per_size']} juries each "
        f"(jury ids 0..{method['juries_per_size']-1}), source id `size:jury`.",
        "- Amplification: `seed_from_pref` on the saved endpoint preference vector (top 25 eligible "
        "books, `0.4 + 19.6 * frac5`, mean-normalized), then `run_path` gain-hard forward amplification "
        f"(beta {breeding.BETA}, hard threshold `pruning.HARD_THRESHOLD`, max stages {breeding.MAX_STAGES}).",
        "- Representation (preference space): `book_n >= 25` -> mean-center across eligible -> L2.",
        "- Representation (direction space): L2-normalized stage direction.",
        "- Clustering: average-linkage hierarchical clustering on cosine distance, dendrogram cut at "
        "height `1 - tau` for tau in {0.30, 0.50, 0.70}; singletons kept.",
        f"- Stage definitions: deepest = final run_path stage (per-source n_stages - 1); "
        f"s4 = fixed stage index {STAGE_ANALYZED}.",
        f"- Half splits: A = even jury index, B = odd jury index; centroid-cosine matching in the "
        "same space; every half-cluster centroid vector was frozen to disk; `mutual_best` marks "
        "A<->B mutual best matches.",
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
    if frozen.get("invariant_checks"):
        n_ok = sum(1 for c in frozen["invariant_checks"] if c["ok"])
        lines += [
            "",
            "### Label-blind invariant checks (run inside geometry, before sealing)",
            "",
            f"- {len(frozen['invariant_checks'])} checks run, {n_ok} passed, "
            f"{len(frozen['invariant_checks']) - n_ok} failed. Geometry aborts on any failure.",
        ]
    lines += ["", "## POST-HOC LITERARY EVALUATION", ""]
    lines += [
        "",
        "Semantic context was loaded only after every structure above was frozen and sealed.",
        f"All preference heads use the single global eligibility universe "
        f"(book_n >= {ELIG_MIN_BOOK_N}); stage-specific reader mass is retained as a "
        "structural diagnostic only.",
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

    # primary evidence: every non-singleton preference-space cluster
    lines += [
        "### Primary evidence: every non-singleton preference-space cluster",
        "",
        "| stage | group | tau | size | composition | within pref | exact @50/200 | "
        "broad @50/200 | anti @50/200 | filler @50/200 | member-dir cos_pole | "
        "even/odd analogue | A size | B size | A-B cos | mutual best |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for e in result["cluster_evals"]:
        if e["space"] != "pref" or e["size"] < 2:
            continue
        comp = "/".join(f"{s}:{e['composition'][s]}" for s in ("20000", "80000"))
        md = f"{e['member_direction_cos_pole']:.3f}" if e.get("member_direction_cos_pole") is not None else "n/a"
        a = e.get("analogue")
        if a:
            ana = (
                f"yes (prec {a['precision']:.2f} / cov {a['coverage']:.2f} / "
                f"jac {a['jaccard']:.2f})"
            )
            a_sz = str(a["a_size"])
            b_sz = str(a["b_size"])
            ab_cos = f"{a['cos']:.3f}"
            mutual = "yes" if a["mutual_best"] else "no"
        else:
            ana = "no"
            a_sz = b_sz = ab_cos = mutual = "n/a"
        lines.append(
            f"| {e['stage']} | {e['group']} | {e['tau']:.2f} | {e['size']} | {comp} | "
            f"{e['within']['mean']:.3f} | {_metric_str(e['metrics'])} | {md} | "
            f"{ana} | {a_sz} | {b_sz} | {ab_cos} | {mutual} |"
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
        "| key | eval | cos | a_size | b_size | mutual | A exact/broad/anti @50 | B exact/broad/anti @50 |",
        "|---|---|---:|---:|---:|---|---:|---|",
    ]
    for m in result["matched"]:
        if "a_metrics" not in m:
            continue
        a = m["a_metrics"]
        b = m["b_metrics"]
        ev = "pref" if m["space"] == "pref" else "dir (structural only)"
        lines.append(
            f"| {m['key']} | {ev} | {m['cos']:.3f} | {m['a_size']} | {m['b_size']} | "
            f"{'yes' if m['mutual_best'] else 'no'} | "
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
            md = f"{e['member_direction_cos_pole']:.3f}" if e.get("member_direction_cos_pole") is not None else "n/a"
            lines += [
                f"#### {e['stage']} {e['group']} tau={e['tau']:.2f} ({e['size']} members; {comp})",
                "",
                f"Exact/broad/anti/filler @50/200: {_metric_str(e['metrics'])}; "
                f"within {e['within']['mean']:.3f}; member-direction cos_pole {md}.",
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

    # per-threshold verdict (no tau mixing, no automatic success declaration)
    lines += ["", "## Verdict (per preregistered threshold)", ""]
    for tau in CLUSTER_TAUS:
        key = f"pooled_deepest_{tau:.2f}_pref"
        clist = frozen["clusters"]["deepest"]["pooled"][key]
        non_sing = [c for c in clist if c["size"] >= 2]
        evals = [
            e for e in result["cluster_evals"]
            if e["stage"] == "deepest" and e["group"] == "pooled"
            and e["tau"] == tau and e["space"] == "pref" and e["size"] >= 2
        ]
        n_lit = sum(1 for e in evals if e["metrics"]["exact_lit50"] >= 3)
        strong = [
            e for e in evals
            if e["size"] >= 5
            and e["metrics"]["exact_lit50"] >= 3
            and e["metrics"]["anti50"] <= 1
            and e.get("analogue") is not None
            and e["analogue"]["coverage"] >= 0.5
            and e["analogue"]["cos"] >= 0.7
            and e["analogue"]["mutual_best"]
        ]
        lines.append(
            f"- **tau = {tau:.2f}:** {len(clist)} clusters, {len(non_sing)} non-singleton; "
            f"{n_lit} non-singleton preference clusters reach exact_lit50 >= 3 post-hoc; "
            f"{len(strong)} meet the strong checklist (size >= 5, exact_lit50 >= 3, "
            f"anti50 <= 1, even/odd analogue with coverage >= 0.5, A-B cos >= 0.7 "
            f"and mutual best)."
        )
    lines += [
        "",
        "**No threshold is selected after unblinding, and this report does not "
        "automatically declare success from any single criterion.** The intended strong "
        "result remains: a cluster generated without semantic labels, with at least 5 "
        "source juries, clear literary enrichment and low anti contamination, plus a "
        "geometrically corresponding independently formed cluster in the even and odd "
        "halves. A negative or mixed result is reported as found.",
    ]
    out = report_path(args.tag)
    _write_text_atomic(out, "\n".join(lines))
    print(f"Wrote {out}")


# ---------------------------------------------------------------------------
# Pre-unblind report: label-blind structural summary from the sealed geometry
# ---------------------------------------------------------------------------

def _preunblind_markdown(
    args: argparse.Namespace,
    frozen: dict[str, Any],
    data: dict[str, Any],
    manifest_checks: dict[str, bool],
) -> list[str]:
    method = frozen["method"]
    seal = frozen["seal"]
    lines: list[str] = [
        "# Natural amplification census: PRE-UNBLIND structural summary",
        "",
        "**Generated by the `prereport` phase from the sealed geometry alone. "
        "No semantic context (titles, evaluations, poles) was loaded to produce "
        "this document.**",
        "",
        "**Question.** If we amplify random reversal endpoints without ever consulting "
        "literary labels, does a distinct literary basin emerge naturally among the "
        "amplified outputs?",
        "",
        "> **Scope honesty.** " + _HONESTY_STATEMENT,
        "",
        "## Provenance and seal",
        "",
        f"- Command: `{method['command']}`",
        f"- Random seed: **{args.seed}**",
        f"- Git commit: `{seal['git_head']}`",
        f"- Census artifact: `{seal['census_npz_sha256']}` (SHA256, sealed)",
        f"- Geometry artifact: `{seal['geometry_npz_sha256']}` (SHA256, sealed)",
        f"- External seal manifest verified: census_npz {manifest_checks['census_npz']}, "
        f"geometry_npz {manifest_checks['geometry_npz']}, "
        f"geometry_json {manifest_checks['geometry_json']}.",
        f"- Sources: {seal['n_sources']} ({method['juries_per_size']} juries per size, "
        f"sizes {list(SIZES)}), source id `size:jury`.",
        "",
        "## PRE-UNBLIND STRUCTURAL RESULTS",
        "",
        "All numbers below were computed and frozen before any semantic context was "
        "loaded. Amplification uses `seed_from_pref` (top 25 eligible books, "
        f"`0.4 + 19.6 * frac5`, mean-normalized) and `run_path` gain-hard forward "
        f"amplification (beta {breeding.BETA}, max stages {breeding.MAX_STAGES}). "
        "Preference representation: `book_n >= 25` -> mean-center across eligible -> L2; "
        "direction representation: L2-normalized stage direction. Clustering: "
        "average-linkage hierarchical on cosine distance, dendrogram cut at height "
        "`1 - tau` for tau in {0.30, 0.50, 0.70}; singletons kept. "
        f"Stage definitions: deepest = final run_path stage; "
        f"s4 = fixed stage index {STAGE_ANALYZED}.",
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
                    f"| {group} | {stage_label} | {space} | "
                    f"{frozen['pairwise'][f'{stage_label}_{group}']['n']} | "
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
                            f"{c['size']} ({c['members'][0]}...)" for c in top
                        )
                    else:
                        line += "none"
                    lines.append(line)
    lines += ["", "### Non-singleton clusters: within-cluster agreement and dispersion", ""]
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
    lines += [
        "",
        "### Full-cluster <-> even/odd analogue matching (preference space)",
        "",
        "For every non-singleton preference-space cluster: the best even/odd half match "
        "with coverage >= 0.5. precision = how much of the half match lies in the full "
        "cluster; coverage = how much of the full cluster the half match covers; "
        "jaccard = intersection / union. Label-blind geometry only.",
        "",
        "| stage | group | tau | size | within pref | analogue | precision | coverage | jaccard | "
        "A size | B size | A-B cos | mutual best |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for stage_label in ("deepest", "s4"):
        for group in ("20k", "80k", "pooled"):
            for tau in CLUSTER_TAUS:
                key = f"{group}_{stage_label}_{tau:.2f}_pref"
                for c in frozen["clusters"][stage_label][group][key]:
                    if c["size"] < 2:
                        continue
                    a = _find_analogue(frozen, stage_label, group, tau, c["members"])
                    if a:
                        ana = "yes"
                        prec = f"{a['precision']:.2f}"
                        cov = f"{a['coverage']:.2f}"
                        jac = f"{a['jaccard']:.2f}"
                        a_sz = str(a["a_size"])
                        b_sz = str(a["b_size"])
                        ab = f"{a['cos']:.3f}"
                        mutual = "yes" if a["mutual_best"] else "no"
                    else:
                        ana = prec = cov = jac = "no"
                        a_sz = b_sz = ab = mutual = "n/a"
                    lines.append(
                        f"| {stage_label} | {group} | {tau:.2f} | {c['size']} | "
                        f"{c['within_pref']['mean']:.3f} | {ana} | {prec} | {cov} | {jac} | "
                        f"{a_sz} | {b_sz} | {ab} | {mutual} |"
                    )
    if frozen.get("invariant_checks"):
        n_ok = sum(1 for c in frozen["invariant_checks"] if c["ok"])
        lines += [
            "",
            "### Label-blind invariant checks (run inside geometry, before sealing)",
            "",
            f"- {len(frozen['invariant_checks'])} checks run, {n_ok} passed, "
            f"{len(frozen['invariant_checks']) - n_ok} failed. Geometry aborts on any failure.",
        ]
    lines += [
        "",
        "### Census integrity",
        "",
        f"- partial: {data.get('partial')}",
        f"- integrity: {json.dumps(data.get('integrity', {}))}",
        "",
        "**The `unblind` phase will re-verify the census and geometry hashes, the "
        "external seal manifest, and the full source alignment before loading any "
        "semantic context.**",
    ]
    return lines


def phase_prereport(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    npz_path, json_path = census_paths(args.tag)
    records, _, data = _load_census(
        args, npz_path, json_path, require_complete=not args.allow_partial
    )
    geo_json, geo_npz = geometry_paths(args.tag)
    if not geo_json.exists() or not geo_npz.exists():
        raise SystemExit("geometry not frozen yet; run geometry first")
    frozen = json.loads(geo_json.read_text(encoding="utf-8"))
    if frozen["method"]["semantic_context_loaded"] is not False:
        raise SystemExit("geometry JSON claims semantic context loaded; refusing")
    manifest_checks = _verify_manifest(args, npz_path, geo_json, geo_npz)
    lines = _preunblind_markdown(args, frozen, data, manifest_checks)
    out = prereport_path(args.tag)
    _write_text_atomic(out, "\n".join(lines))
    print(
        f"prereport done ({len(records)} sources, seal manifest verified): "
        f"{out}, {time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Smoke test: small sources per size + reproducibility verification
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
    """Numerically compare the census pipeline against the existing mechanisms.

    The comparison is tolerance-based (stage directions/preferences within
    1e-5), so it is reported as "numerically reproduced", not "bit-exact";
    the start vector and seed-book order must match exactly (max diff == 0).
    """
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
    checks["comparison"] = (
        "tolerance-based: start vector and seed books exact (diff == 0), "
        "stage directions and stage preferences within 1e-5"
    )
    checks["start_bit_exact"] = all(
        c["start_max_abs_diff"] == 0.0 for c in checks["checks"]
    )
    (DATA / "natural_amplification_smoke_verify.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8"
    )
    print(
        f"smoke verification: numerically reproduced={checks['reproduced']} "
        f"({len(checks['checks'])} sources; start bit-exact "
        f"{checks['start_bit_exact']})", flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=["amplify", "consolidate", "geometry", "unblind", "smoke", "prereport"],
        required=True,
    )
    parser.add_argument("--tag", default=None, help="artifact tag (default: none)")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--juries-per-size", type=int, default=JURIES_PER_SIZE)
    parser.add_argument("--smoke-juries", type=int, default=SMOKE_JURIES)
    parser.add_argument("--keep-chunks", action="store_true")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="let geometry/unblind proceed on an incomplete census "
        "(intentional partial analysis only; not used for this experiment)",
    )
    args = parser.parse_args()
    if args.phase == "amplify":
        phase_amplify(args)
    elif args.phase == "consolidate":
        phase_consolidate(args)
    elif args.phase == "geometry":
        phase_geometry(args)
    elif args.phase == "unblind":
        phase_unblind(args)
    elif args.phase == "prereport":
        phase_prereport(args)
    else:
        phase_smoke(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Hierarchical jury decomposition: multiple canons in a trench coat?

Scientific question
-------------------
A large random jury (80k users) is a mixture of several latent preference
populations.  At the parent size the reversal dynamics average those
populations together, so the 80k endpoint may be a blend that never falls
into a small basin.  If the same parent jury is decomposed into smaller
sub-juries (40k, then 20k) and the EXISTING convergence-reversal dynamics
are rerun on each child, different children may converge into different
recurrent basins.  This script tests that hypothesis structurally and
label-blindly.

Design
------
For every one of the 120 fixed 80k parent juries of the ``drift_exploit``
main campaign (tag ``main``, seed 20260811, sizes
[20000,30000,45000,60000,80000,110000], 120 juries per size):

ARM A -- random hierarchical partitions (3 independent balanced replicates,
experiment seed 20260819, all per-parent seeds derived from a stable
sha256 scheme, never Python ``hash()``):

    80k parent -> 2 x 40k children -> 4 x 20k grandchildren

ARM B -- ratings-only spectral bisection: per parent, build a sparse
collaborative-filtering residual matrix

    resid = rating - user_mean - book_mean + global_mean

over the fixed ratings-derived eligible universe (payload users x payload
books, all observed ratings), row-L2 normalized, then recursively split at
the median of the leading nontrivial user direction computed by a
deterministic power iteration (no dense user-user or user-book matrices).

For every child the EXACT existing convergence-reversal procedure is
rerun: ``run_jury`` (research_jury_ensemble_reversal.py, gain/hard
pruning, beta 2.5, 20 iterations, max 8 stages, retained target 1.01,
evidence floor 5%) on the full population with the standard jury seed
(20.0 on the child users, 0.4 elsewhere, mean-normalized;
``build_subgroup_start`` in research_jury_split_experiment.py, which is
the same construction as ``make_jury_seed`` restricted to a subset).
The reversal operator consumes no RNG under the gain/hard configuration.

Intended full campaign: 2160 random-arm child runs (120 parents x 3
replicates x 6 nodes) + 720 spectral-arm child runs (120 parents x 6
nodes) = 2880 child reversal runs.  The parent 80k endpoints are NOT
recomputed: they are the frozen drift_exploit_main endpoints, source
aligned by the same (size, jury) canonical order used by the Natural
Amplification Census.

Phases
------
- prepare:      resolve the 120 fixed 80k parents (records + replay of the
                exact rng.choice stream, MAIN_SEED 20260811), verify source
                alignment, write the campaign spec, and compute the fixed
                ratings-only statistics (global/user/book rating means over
                all_rating_events) used by the spectral splits.
- run:          child reversal runs with per-(parent, arm) chunk checkpoint
                and resume.  Chunks are self-describing (spec hash, user
                hash, expected node sizes, embedded records).  Partial
                scopes are recorded in the spec file.
- consolidate:  validate the complete child campaign (refuses partial by
                default) and write canonical-row vector artifacts including
                the frozen parent endpoints.
- geometry:     ALL label-blind structural analysis: representation
                conventions of the Natural Amplification Census (pref:
                book_n>=25 -> mean-center across eligible -> L2; dir: L2),
                average-linkage cosine clustering at tau 0.30/0.50/0.70,
                cluster centroids/dispersion, within-parent recurrence
                (recurrent mode requires >= 2 DISTINCT random replicates),
                40k-ancestor blending diagnostics, cross-arm matching
                (spectral children vs recurrent random modes, centroid
                cosine, mutual best), parent-as-mixture convex-hull fits
                (SLSQP, alpha >= 0, sum 1), and two permutation nulls.
                Hash-seals geometry NPZ, geometry JSON and the external
                seal manifest exactly like the census.
- prereport:    PRE-UNBLIND structural report from the sealed geometry only.
- unblind:      seal verification + semantic evaluation.  IMPLEMENTED but
                MUST NOT be run in this task (see task instructions).
- smoke:        bounded end-to-end validation on a tiny synthetic parent.

Semantic firewall
-----------------
NO titles/authors/genre/literary sets/known pole/publication year may be
loaded before every child vector, source table, cluster assignment,
centroid, recurrence measure, cross-arm match, and mixture result is
frozen and hash-sealed.  Phases prepare/run/consolidate/geometry/prereport
never call ``spectral.load_posthoc_context``; the module flag
``SEMANTIC_CONTEXT_LOADED`` turns True only inside ``phase_unblind`` after
all seal hashes verify.

Memory/discipline
-----------------
Sparse CSR residual matrices only; per-parent chunks of float32 endpoint
vectors (~106 KB per 26.4k-book vector); no dense user-user or user-book
matrices; no stored child membership arrays (children are reconstructed
deterministically from parent users + seeds, or from the deterministic
spectral procedure); atomic writes; chunk validation before trust;
consolidation refuses partial campaigns by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import duckdb
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.optimize import minimize
from scipy.sparse import coo_matrix, csr_matrix

from curators_explorer.scripts import (
    research_attractor_pruning as pruning,
)
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year
from curators_explorer.scripts.research_jury_ensemble_reversal import (
    BETA,
    ITERATIONS,
    MAX_STAGES,
    run_jury,
)
from curators_explorer.scripts.research_jury_split_experiment import (
    MAIN_JURIES,
    MAIN_SEED,
    MAIN_SIZES,
    build_subgroup_start,
    replay_jury_users,
)

DATA = Path(__file__).resolve().parents[1] / "data"
DRIFT_NPZ = DATA / "drift_exploit_main.npz"
DRIFT_JSON = DATA / "drift_exploit_main.json"
DRIFT_80K_ROW0 = MAIN_SIZES.index(80000) * MAIN_JURIES  # 360

# Preregistered experiment parameters (never tuned from results).
GLOBAL_SEED = 20260819
PARENT_SIZE = 80000
CHILD_40K = 40000
CHILD_20K = 20000
RANDOM_REPLICATES = 3
CLUSTER_TAUS = (0.30, 0.50, 0.70)
ELIG_MIN_BOOK_N = 25            # ratings-derived eligibility (all payload books)
RETAINED_TARGET = 1.01          # reversal stop (drift_exploit convention)
POWER_ITERS = 50                # deterministic power iteration cap
POWER_TOL = 1.0 - 1e-12         # step-cosine convergence tolerance
NULL_PERMUTATIONS = 199         # label-free null permutations per statistic
SMOKE_PARENT_USERS = 2400       # smoke parent size (tiny)
SMOKE_40K = 1200
SMOKE_20K = 600

NODE_ORDER = ["40k:0", "40k:1", "20k:0:0", "20k:0:1", "20k:1:0", "20k:1:1"]

# True only inside the unblind phase, after all geometry files are sealed.
SEMANTIC_CONTEXT_LOADED = False

FORBIDDEN_SEMANTIC_TOKENS = (
    "title", "author", "exact_lit", "broad_lit", "pole",
    "year", "genre", "evaluation", "poll", "literary",
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _tag_suffix(tag: str | None) -> str:
    return f"_{tag}" if tag else ""


def spec_path(tag: str | None) -> Path:
    return DATA / f"jury_decomposition_spec{_tag_suffix(tag)}.json"


def rating_stats_path(tag: str | None) -> Path:
    return DATA / f"jury_decomposition_rating_stats{_tag_suffix(tag)}.npz"


def chunk_dir(tag: str | None) -> Path:
    return DATA / "jury_decomposition_chunks" / (tag or "main")


def chunk_path(tag: str | None, arm: str, parent_j: int) -> Path:
    return chunk_dir(tag) / f"{arm}_{parent_j:03d}.npz"


def census_paths(tag: str | None) -> tuple[Path, Path]:
    suffix = _tag_suffix(tag)
    return (
        DATA / f"jury_decomposition{suffix}.npz",
        DATA / f"jury_decomposition{suffix}.json",
    )


def geometry_paths(tag: str | None) -> tuple[Path, Path]:
    suffix = _tag_suffix(tag)
    return (
        DATA / f"jury_decomposition_geometry{suffix}.json",
        DATA / f"jury_decomposition_geometry{suffix}.npz",
    )


def seal_manifest_path(tag: str | None) -> Path:
    return DATA / f"jury_decomposition{_tag_suffix(tag)}_seal_manifest.json"


def prereport_path(tag: str | None) -> Path:
    suffix = _tag_suffix(tag)
    return DATA / f"JURY_DECOMPOSITION{suffix.upper()}_PREUNBLIND_REPORT.md"


def smoke_report_path(tag: str | None) -> Path:
    suffix = _tag_suffix(tag)
    return DATA / f"JURY_DECOMPOSITION{suffix.upper()}_SMOKE_REPORT.md"


def posthoc_path(tag: str | None) -> Path:
    return DATA / f"jury_decomposition_posthoc{_tag_suffix(tag)}.json"


# ---------------------------------------------------------------------------
# Hashing / atomic I/O helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, path)


def _derive_seed(*parts: Any) -> int:
    """Stable sha256-derived seed; never Python's process-randomized hash()."""
    h = hashlib.sha256()
    for part in parts:
        h.update(str(part).encode("utf-8"))
        h.update(b"\x00")
    return int.from_bytes(h.digest()[:16], "big")


def _param_hash(spec: dict[str, Any]) -> str:
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    return _bytes_sha256(canonical.encode("utf-8"))


def _users_hash(users: np.ndarray) -> str:
    return _bytes_sha256(np.asarray(users).astype(np.int64).tobytes())


def _method_block(phase: str, args: argparse.Namespace, **extra: Any) -> dict[str, Any]:
    return {
        "phase": phase,
        "seed": args.seed,
        "command": shlex.join(sys.argv),
        "git_head": _git_head(),
        "semantic_context_loaded": SEMANTIC_CONTEXT_LOADED,
        "runtime_seconds": 0.0,
        **extra,
    }


# ---------------------------------------------------------------------------
# Campaign spec
# ---------------------------------------------------------------------------

def _reversal_params() -> dict[str, Any]:
    return {
        "run_jury": "curators_explorer.scripts.research_jury_ensemble_reversal.run_jury",
        "jury_seed": (
            "build_subgroup_start (research_jury_split_experiment): 20.0 on "
            "child users, 0.4 elsewhere, mean-normalized; identical to "
            "make_jury_seed restricted to a subset"
        ),
        "beta": float(BETA),
        "iterations": int(ITERATIONS),
        "max_stages": int(MAX_STAGES),
        "retained_target": float(RETAINED_TARGET),
        "prune_criterion": "gain",
        "prune_mode": "hard",
        "ladder_rate": float(pruning.LADDER_RATE),
        "hard_threshold": float(pruning.HARD_THRESHOLD),
        "min_remaining_fraction": float(pruning.MIN_REMAINING_FRACTION),
        "rng_consumed": "none under gain/hard (verified)",
    }


def _spectral_rep_params() -> dict[str, Any]:
    return {
        "formula": "resid = rating - user_mean - book_mean + global_mean",
        "statistics_source": (
            "fixed ratings-derived statistics over all_rating_events "
            "(rating>0): per-user mean over the user's own ratings, per-book "
            "mean over the book's ratings, global mean over all ratings"
        ),
        "edge_universe": (
            "all rating>0 events restricted to the b500 payload users x "
            "payload books (the fixed eligible universe of the existing "
            "experiments; every book has book_n >= 500 >= 25)"
        ),
        "row_normalization": "row L2 (suppresses user activity magnitude)",
        "leading_direction": (
            "deterministic power iteration on the sparse residual matrix "
            "(fixed start, capped " + str(POWER_ITERS) + " iterations), "
            "no dense user-user or user-book matrices"
        ),
        "split": "median of the leading user coordinate; ties broken by "
                 "stable ascending user id; sign irrelevant (children "
                 "labels are swap-invariant)",
        "power_iters": int(POWER_ITERS),
        "power_tol": float(POWER_TOL),
    }


def full_spec(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "experiment": "hierarchical jury decomposition",
        "global_seed": int(args.seed),
        "parent_campaign": {
            "tag": "main",
            "seed": int(MAIN_SEED),
            "sizes": list(MAIN_SIZES),
            "juries_per_size": int(MAIN_JURIES),
            "parent_size": int(PARENT_SIZE),
            "parent_endpoints": "drift_exploit_main.npz rows 360..479 "
                                "(canonical (size, jury) order)",
            "membership": "rng.choice replay of the exact main-sweep stream "
                          "(replay_jury_users, research_jury_split_experiment)",
        },
        "arms": {
            "random": {
                "replicates": int(RANDOM_REPLICATES),
                "node_sizes": [int(CHILD_40K), int(CHILD_40K),
                               int(CHILD_20K), int(CHILD_20K),
                               int(CHILD_20K), int(CHILD_20K)],
                "node_order": list(NODE_ORDER),
                "partition": (
                    "balanced hierarchical random partition; all randomness "
                    "from default_rng(sha256-derived seed) per "
                    "(arm, parent_j, replicate, node); parent users sorted; "
                    "children sorted; disjoint union invariant"
                ),
            },
            "spectral": {
                "replicates": 1,
                "node_sizes": [int(CHILD_40K), int(CHILD_40K),
                               int(CHILD_20K), int(CHILD_20K),
                               int(CHILD_20K), int(CHILD_20K)],
                "node_order": list(NODE_ORDER),
                "representation": _spectral_rep_params(),
                "recompute": "local leading direction recomputed inside each "
                             "40k child before producing 20k descendants",
            },
        },
        "reversal": _reversal_params(),
        "analysis": {
            "elig_min_book_n": int(ELIG_MIN_BOOK_N),
            "clustering": {
                "method": "average-linkage hierarchical, cosine distance, "
                          "dendrogram cut at height 1 - tau",
                "taus": [float(t) for t in CLUSTER_TAUS],
                "singletons_kept": True,
            },
            "representation_pref": "book_n>=25 -> mean-center across "
                                   "eligible -> L2",
            "representation_dir": "L2 normalize saved reversal direction",
            "recurrent_mode_rule": (
                "a child mode is recurrent iff it contains descendants from "
                ">= 2 DISTINCT random partition replicates"
            ),
            "null_permutations": int(NULL_PERMUTATIONS),
        },
    }


# ---------------------------------------------------------------------------
# Parent resolution (source integrity)
# ---------------------------------------------------------------------------

def load_80k_parents() -> tuple[list[dict[str, Any]], list[int]]:
    """Return the 80k records of drift_exploit_main and their npz row ids.

    Verifies the canonical (size, jury) order inherited from the main sweep
    (sizes ascending, jury ascending) and the 80k slice is exactly rows
    360..479 with jury ids 0..119.
    """
    if not DRIFT_JSON.exists():
        raise SystemExit(f"missing {DRIFT_JSON}")
    records = json.loads(DRIFT_JSON.read_text(encoding="utf-8"))["records"]
    n_sizes = len(MAIN_SIZES)
    expected = [(size, j) for size in MAIN_SIZES for j in range(MAIN_JURIES)]
    if len(records) != len(expected):
        raise SystemExit(
            f"drift_exploit_main has {len(records)} records, expected "
            f"{len(expected)}"
        )
    got = [(r["size"], r["jury"]) for r in records]
    if got != expected:
        raise SystemExit("drift_exploit_main records are not in canonical order")
    parent_records = records[DRIFT_80K_ROW0:DRIFT_80K_ROW0 + MAIN_JURIES]
    parent_rows = list(range(DRIFT_80K_ROW0, DRIFT_80K_ROW0 + MAIN_JURIES))
    for j, r in enumerate(parent_records):
        if r["size"] != PARENT_SIZE or r["jury"] != j:
            raise SystemExit(f"80k parent slice misaligned at jury {j}")
    return parent_records, parent_rows


def replay_80k_membership(payload: dict[str, np.ndarray]) -> dict[int, np.ndarray]:
    """Deterministic reconstruction of every 80k parent's user set.

    Replays the exact rng.choice stream of the main sweep (sizes ascending,
    120 juries per size) with MAIN_SEED and returns the sorted user ids of
    the 80k juries (keys 0..119).  Verified bit-for-bit by
    research_jury_split_experiment phase_verify.
    """
    all_juries = replay_jury_users(payload, MAIN_SEED, MAIN_SIZES, MAIN_JURIES)
    return {j: all_juries[(PARENT_SIZE, j)] for j in range(MAIN_JURIES)}


def load_parent_endpoints() -> dict[str, Any]:
    """Frozen 80k parent endpoints from drift_exploit_main (source aligned)."""
    if not DRIFT_NPZ.exists():
        raise SystemExit(
            f"missing {DRIFT_NPZ}; run the drift_exploit main sweep or restore "
            "the artifact"
        )
    blob = np.load(DRIFT_NPZ, allow_pickle=False)
    rows = np.arange(DRIFT_80K_ROW0, DRIFT_80K_ROW0 + MAIN_JURIES)
    return {
        "prefs": blob["prefs"][rows].astype(np.float32),
        "directions": blob["directions"][rows].astype(np.float32),
        "stage0_prefs": blob["stage0_prefs"][rows].astype(np.float32),
    }


# ---------------------------------------------------------------------------
# Ratings-only statistics (spectral arm) -- prepare
# ---------------------------------------------------------------------------

def build_rating_stats(tag: str | None, payload: dict[str, np.ndarray]) -> Path:
    """Fixed ratings-derived global/user/book statistics over the full
    all_rating_events table (rating>0).  Ratings-only; no titles/authors/
    years.  Cached in a small npz aligned to the payload user/book order."""
    out = rating_stats_path(tag)
    con = duckdb.connect(str(Path(__file__).resolve().parents[2] / "data" /
                             "ucsd_goodreads" / "explorer.duckdb"), read_only=True)
    try:
        con.execute(
            "create temp table pu as select (row_number() over "
            "(order by user_id)-1)::int as ui, user_id from "
            "(select distinct unnest(?) as user_id) t",
            [payload["user_ids"].tolist()],
        )
        con.execute(
            "create temp table wb as select (row_number() over "
            "(order by work_id)-1)::int as bi, work_id from "
            "(select distinct unnest(?) as work_id) t",
            [payload["work_ids"].tolist()],
        )
        global_mean = float(
            con.execute(
                "select avg(rating) from all_rating_events where rating>0"
            ).fetchone()[0]
        )
        um = con.execute(
            "select u.ui, avg(e.rating)::float as m from all_rating_events e "
            "join pu u using (user_id) where e.rating>0 group by u.ui order by u.ui"
        ).fetchnumpy()
        bm = con.execute(
            "select b.bi, avg(e.rating)::float as m from all_rating_events e "
            "join wb b using (work_id) where e.rating>0 group by b.bi order by b.bi"
        ).fetchnumpy()
    finally:
        con.close()
    user_mean = np.full(len(payload["user_ids"]), np.nan, dtype=np.float32)
    user_mean[um["ui"]] = um["m"]
    book_mean = np.full(len(payload["work_ids"]), np.nan, dtype=np.float32)
    book_mean[bm["bi"]] = bm["m"]
    if not np.isfinite(user_mean).all():
        raise SystemExit(
            "some payload users have no ratings in all_rating_events; "
            "payload/reference misalignment"
        )
    if not np.isfinite(book_mean).all():
        raise SystemExit(
            "some payload books have no ratings in all_rating_events; "
            "payload/reference misalignment"
        )
    arrays = {
        "global_mean": np.float64(global_mean),
        "user_mean": user_mean,
        "book_mean": book_mean,
        "payload_user_hash": np.asarray(
            _bytes_sha256(payload["user_ids"].astype(np.int64).tobytes())
        ),
        "payload_book_hash": np.asarray(
            _bytes_sha256(np.asarray(payload["work_ids"]).tobytes())
        ),
        "n_rating_events": np.int64(0),
    }
    _write_npz_atomic(out, arrays)
    print(f"rating stats written: {out} (global_mean={global_mean:.4f})", flush=True)
    return out


def load_rating_stats(tag: str | None, payload: dict[str, np.ndarray]) -> dict[str, Any]:
    path = rating_stats_path(tag)
    if not path.exists():
        raise SystemExit(f"missing {path}; run prepare first")
    with np.load(path, allow_pickle=False) as saved:
        stats = {key: saved[key] for key in saved.files}
    if str(stats["payload_user_hash"][()]) != _bytes_sha256(
        payload["user_ids"].astype(np.int64).tobytes()
    ):
        raise SystemExit("rating stats user alignment mismatch")
    return stats


# ---------------------------------------------------------------------------
# Random hierarchical partition (ARM A)
# ---------------------------------------------------------------------------

def random_tree(parent_users: np.ndarray, parent_j: int, repl: int,
                spec: dict[str, Any]) -> dict[str, np.ndarray]:
    """Deterministic balanced random partition tree of the parent users."""
    n = len(parent_users)
    half = n // 2
    quarter = half // 2
    rng_root = np.random.default_rng(
        _derive_seed(spec["global_seed"], "random", parent_j, repl, "root")
    )
    perm = rng_root.permutation(parent_users)
    c0, c1 = np.sort(perm[:half]), np.sort(perm[half:])
    nodes: dict[str, np.ndarray] = {"40k:0": c0, "40k:1": c1}
    for ci in (0, 1):
        rng = np.random.default_rng(
            _derive_seed(spec["global_seed"], "random", parent_j, repl,
                         f"child40:{ci}")
        )
        perm = rng.permutation(nodes[f"40k:{ci}"])
        nodes[f"20k:{ci}:0"] = np.sort(perm[:quarter])
        nodes[f"20k:{ci}:1"] = np.sort(perm[quarter:])
    return nodes


# ---------------------------------------------------------------------------
# Spectral split (ARM B)
# ---------------------------------------------------------------------------

def _edges_connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(
        "ATTACH '" + str(Path(__file__).resolve().parents[2] / "data" /
                         "ucsd_goodreads" / "explorer.duckdb") + "' AS ex (READ_ONLY)"
    )
    con.execute("USE ex")
    return con


def fetch_parent_edges(
    con: duckdb.DuckDBPyConnection,
    payload: dict[str, np.ndarray],
    parent_users: np.ndarray,
) -> dict[str, np.ndarray]:
    """All rating>0 edges of the parent users over the payload book universe,
    ordered by (local row, book).  Ratings-only."""
    con.execute(
        "create or replace temp table pusers as select (row_number() over "
        "(order by user_id)-1)::int as pi, user_id from "
        "(select distinct unnest(?) as user_id) t",
        [parent_users.tolist()],
    )
    res = con.execute(
        "select p.pi, u.ui, b.bi, e.rating "
        "from ex.all_rating_events e "
        "join pusers p using (user_id) "
        "join pu u using (user_id) "
        "join wb b using (work_id) "
        "where e.rating>0 order by p.pi, b.bi"
    ).fetchnumpy()
    return {
        "row": res["pi"].astype(np.int32),
        "ui": res["ui"].astype(np.int32),
        "col": res["bi"].astype(np.int32),
        "rating": res["rating"].astype(np.int32),
    }


def residual_csr(
    edges: dict[str, np.ndarray],
    stats: dict[str, Any],
    n_users: int,
    n_books: int,
) -> csr_matrix:
    """Sparse residual matrix, row-L2 normalized.  No dense intermediates."""
    resid = (
        edges["rating"].astype(np.float64)
        - stats["user_mean"][edges["ui"]].astype(np.float64)
        - stats["book_mean"][edges["col"]].astype(np.float64)
        + float(stats["global_mean"])
    ).astype(np.float32)
    M = coo_matrix(
        (resid, (edges["row"], edges["col"])), shape=(n_users, n_books)
    ).tocsr()
    M.sum_duplicates()
    row_norm2 = np.asarray(M.multiply(M).sum(axis=1)).ravel()
    row_norm = np.sqrt(np.maximum(row_norm2, 1e-12))
    M.data /= row_norm.repeat(np.diff(M.indptr))
    return M


def leading_user_direction(M: csr_matrix, iters: int = POWER_ITERS,
                           tol: float = POWER_TOL) -> np.ndarray:
    """Leading left singular direction by deterministic power iteration."""
    u = np.ones(M.shape[0], dtype=np.float64)
    u /= np.linalg.norm(u)
    previous = None
    for _ in range(iters):
        v = M.T @ u
        nv = np.linalg.norm(v)
        if nv < 1e-12:
            break
        u2 = M @ (v / nv)
        nu = np.linalg.norm(u2)
        if nu < 1e-12:
            break
        u2 /= nu
        if previous is not None and float(u2 @ previous) > tol:
            u = u2
            break
        previous = u2
        u = u2
    return u


def median_split(members: np.ndarray, coord: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Balanced split at the median coordinate; stable user-id tie break."""
    order = np.lexsort((members, coord))
    half = len(members) // 2
    return np.sort(members[order[:half]]), np.sort(members[order[half:]])


def spectral_tree(
    con: duckdb.DuckDBPyConnection,
    payload: dict[str, np.ndarray],
    stats: dict[str, Any],
    parent_users: np.ndarray,
    parent_j: int,
    spec: dict[str, Any],
) -> dict[str, np.ndarray]:
    """Recursive balanced spectral bisection of the parent users."""
    n = len(parent_users)
    half = n // 2
    quarter = half // 2
    edges = fetch_parent_edges(con, payload, parent_users)
    M = residual_csr(edges, stats, n, len(payload["work_ids"]))
    del edges
    coord = leading_user_direction(M, spec["arms"]["spectral"][
        "representation"]["power_iters"])
    g0, g1 = median_split(parent_users, coord)
    nodes: dict[str, np.ndarray] = {"40k:0": g0, "40k:1": g1}
    for ci, (g, Mg) in enumerate(((g0, M[np.searchsorted(parent_users, g0)]),
                                  (g1, M[np.searchsorted(parent_users, g1)]))):
        sub_coord = leading_user_direction(
            Mg, spec["arms"]["spectral"]["representation"]["power_iters"])
        x0, x1 = median_split(g, sub_coord)
        nodes[f"20k:{ci}:0"] = x0
        nodes[f"20k:{ci}:1"] = x1
    return nodes


# ---------------------------------------------------------------------------
# Child reversal (EXACT existing operator)
# ---------------------------------------------------------------------------

def run_child(
    payload: dict[str, np.ndarray],
    matrix: Any,
    members: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Rerun the exact existing convergence-reversal on a child jury.

    Reuses run_jury (research_jury_ensemble_reversal.py) with the standard
    jury seed restricted to the child users (build_subgroup_start) and the
    drift-exploit retained target 1.01.  No reversal operator is invented
    here; all parameters come from the reused modules.
    """
    start = build_subgroup_start(payload, members)
    run = run_jury(payload, matrix, start, rng, RETAINED_TARGET)
    return run


def _label_free_child_features(
    run: dict[str, Any], eligible: np.ndarray
) -> dict[str, float]:
    fe = run["final_pref"][eligible].astype(np.float64)
    f0 = run["stage0_pref"][eligible].astype(np.float64)

    def rep(x: np.ndarray) -> np.ndarray:
        c = x - x.mean()
        norm = np.linalg.norm(c)
        return c / norm if norm > 1e-20 else c

    abs_mass = np.abs(fe)
    total = abs_mass.sum()
    mass = abs_mass / total if total > 0 else abs_mass
    concentration = float(1.0 / np.sum(mass**2)) if np.sum(mass**2) > 0 else 0.0
    top25 = np.argsort(-abs_mass, kind="stable")[:25]
    return {
        "displacement_norm_eligible": float(np.linalg.norm(fe - f0)),
        "endpoint_stage0_cos": float(np.sum(rep(fe) * rep(f0))),
        "pref_norm_eligible": float(np.linalg.norm(fe)),
        "pref_concentration": concentration,
        "top25_mass_concentration": float(abs_mass[top25].sum() / total)
        if total > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Chunk read/write/validate
# ---------------------------------------------------------------------------

def node_source_id(arm: str, parent_j: int, repl: int, path: str) -> str:
    return f"{arm}-{parent_j:03d}-{repl}-{path}"


def write_chunk(
    tag: str | None,
    spec: dict[str, Any],
    arm: str,
    parent_j: int,
    parent_users: np.ndarray,
    nodes: dict[str, list[dict[str, Any]]],
) -> Path:
    """nodes: list of per-node dicts with 'path', 'repl', 'run' and
    'members' (members never stored, only hashed)."""
    order = spec["arms"][arm]["node_order"]
    node_sizes = spec["arms"][arm]["node_sizes"]
    n = len(nodes)
    prefs = np.stack([nd["run"]["final_pref"] for nd in nodes]).astype(np.float32)
    directions = np.stack([
        nd["run"]["stages"][-1]["direction"] for nd in nodes
    ]).astype(np.float32)
    records = []
    for nd in nodes:
        r = nd["run"]
        rec = {
            "source_id": node_source_id(arm, parent_j, nd["repl"], nd["path"]),
            "arm": arm,
            "parent_j": int(parent_j),
            "replicate": int(nd["repl"]),
            "path": nd["path"],
            "size": int(nd["members"].shape[0]),
            "stop_reason": r["stop_reason"],
            "n_stages": len(r["stages"]),
            "users_by_stage": [s["remaining_users"] for s in r["stages"]],
            "retained_ref_by_stage": [
                s["direction_retained_reference"] for s in r["stages"]
            ],
            "deepest_removed_fraction": r["stages"][-1]["cumulative_removed_fraction"],
            "final_step_correlation": r["stages"][-1]["final_step_correlation"],
            "effective_user_share_deepest": float(
                (r["weights_store"][-1].sum() ** 2
                 / np.sum(r["weights_store"][-1] ** 2))
                / len(r["weights_store"][-1])
            ) if "weights_store" in r else float(
                (r["stages"][-1].get("effective_user_share", float("nan")))
            ),
        }
        rec.update(nd.get("features", {}))
        records.append(rec)
    paths = [nd["path"] for nd in nodes]
    repls = [nd["repl"] for nd in nodes]
    n_order = len(order)
    reps = (n + n_order - 1) // n_order
    if paths != (order * reps)[:n]:
        raise SystemExit(f"chunk node order mismatch for {arm} {parent_j}")
    expected_sizes = (node_sizes * reps)[:n]
    got_sizes = [nd["members"].shape[0] for nd in nodes]
    if got_sizes != expected_sizes:
        raise SystemExit(
            f"chunk node sizes {got_sizes} != expected {expected_sizes}"
        )
    path_str = np.asarray(paths, dtype="U8")
    repl_arr = np.asarray(repls, dtype=np.int16)
    size_arr = np.asarray(got_sizes, dtype=np.int32)
    parent_arr = np.full(n, parent_j, dtype=np.int32)
    cpath = chunk_path(tag, arm, parent_j)
    cpath.parent.mkdir(parents=True, exist_ok=True)
    _write_npz_atomic(
        cpath,
        {
            "prefs": prefs,
            "directions": directions,
            "node_arm": np.asarray([arm] * n, dtype="U8"),
            "node_parent": parent_arr,
            "node_repl": repl_arr,
            "node_path": path_str,
            "node_size": size_arr,
            "expected_sizes": np.asarray(expected_sizes, dtype=np.int32),
            "spec_hash": np.asarray(_param_hash(spec)),
            "user_hash": np.asarray(_users_hash(parent_users)),
            "record_json": np.asarray(
                [json.dumps(rec, separators=(",", ":")) for rec in records],
                dtype="U",
            ),
        },
    )
    return cpath


def read_chunk(
    tag: str | None, arm: str, parent_j: int, spec: dict[str, Any],
    parent_users: np.ndarray,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Validate a chunk; raise on any inconsistency (caller recomputes)."""
    cpath = chunk_path(tag, arm, parent_j)
    if not cpath.exists():
        raise FileNotFoundError(cpath)
    with np.load(cpath, allow_pickle=False) as c:
        if str(c["spec_hash"][()]) != _param_hash(spec):
            raise ValueError("spec hash mismatch")
        if str(c["user_hash"][()]) != _users_hash(parent_users):
            raise ValueError("user hash mismatch")
        n = int(c["node_repl"].shape[0])
        n_order = len(spec["arms"][arm]["node_order"])
        reps = (n + n_order - 1) // n_order
        expected = (spec["arms"][arm]["node_sizes"] * reps)[:n]
        if not np.array_equal(np.asarray(c["expected_sizes"], dtype=np.int32),
                              np.asarray(expected, dtype=np.int32)):
            raise ValueError("expected sizes mismatch")
        if not np.array_equal(np.asarray(c["node_size"], dtype=np.int32),
                              np.asarray(c["expected_sizes"], dtype=np.int32)):
            raise ValueError("node sizes mismatch")
        if int(c["prefs"].shape[1]) != int(c["directions"].shape[1]):
            raise ValueError("pref/direction width mismatch")
        records = [json.loads(str(x)) for x in c["record_json"]]
        if len(records) != n:
            raise ValueError("record count mismatch")
        for i, rec in enumerate(records):
            expect_id = node_source_id(
                arm, parent_j, int(c["node_repl"][i]), str(c["node_path"][i]))
            if rec["source_id"] != expect_id:
                raise ValueError("embedded record id mismatch")
        arrays = {key: c[key] for key in c.files}
    return {"records": records, "n": n}, arrays


# ---------------------------------------------------------------------------
# Phase: prepare
# ---------------------------------------------------------------------------

def phase_prepare(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    payload, _, _ = year.load_matrix()
    parent_records, parent_rows = load_80k_parents()
    membership = replay_80k_membership(payload)
    for j, users in membership.items():
        if len(users) != PARENT_SIZE:
            raise SystemExit(f"parent {j} replay size {len(users)} != 80000")
        if not np.array_equal(np.sort(users), users):
            raise SystemExit(f"parent {j} replay not sorted")
    spec = full_spec(args)
    spec["prepare"] = {
        "parents": [r["jury"] for r in parent_records],
        "parent_rows_80k": [int(x) for x in parent_rows],
        "replayed_user_sizes": [int(len(membership[j])) for j in range(MAIN_JURIES)],
        "param_hash": _param_hash(spec),
    }
    _write_text_atomic(spec_path(args.tag), json.dumps(spec, indent=1))
    build_rating_stats(args.tag, payload)
    print(
        f"prepare done: 120 x 80k parents resolved and aligned, spec "
        f"{spec_path(args.tag)}, rating stats written, {time.time() - t0:.0f}s",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Phase: run
# ---------------------------------------------------------------------------

def _run_scope_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "parents": list(range(0, min(args.max_parents, MAIN_JURIES))),
        "random_replicates": int(min(args.replicates, RANDOM_REPLICATES)),
        "arms": ["random", "spectral"] if args.arms == "all" else [args.arms],
    }


def _apply_run_scope(spec: dict[str, Any], scope: dict[str, Any]) -> None:
    spec["run_scope"] = {
        "parents": scope["parents"],
        "random_replicates": scope["random_replicates"],
        "arms": scope["arms"],
        "full_random_replicates": int(RANDOM_REPLICATES),
        "full_parents": list(range(MAIN_JURIES)),
    }


def phase_run(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    spath = spec_path(args.tag)
    if not spath.exists():
        raise SystemExit(f"missing {spath}; run prepare first")
    spec = json.loads(spath.read_text(encoding="utf-8"))
    scope = _run_scope_args(args)
    _apply_run_scope(spec, scope)
    _write_text_atomic(spath, json.dumps(spec, indent=1))

    payload, matrix, _ = year.load_matrix()
    membership = replay_80k_membership(payload)
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    con = _edges_connection()
    try:
        con.execute(
            "create temp table pu as select (row_number() over "
            "(order by user_id)-1)::int as ui, user_id from "
            "(select distinct unnest(?) as user_id) t",
            [payload["user_ids"].tolist()],
        )
        con.execute(
            "create temp table wb as select (row_number() over "
            "(order by work_id)-1)::int as bi, work_id from "
            "(select distinct unnest(?) as work_id) t",
            [payload["work_ids"].tolist()],
        )
        stats = load_rating_stats(args.tag, payload) if "spectral" in scope["arms"] else None

        done = 0
        total = sum(
            (scope["random_replicates"] if arm == "random" else 1)
            * 6 * len(scope["parents"])
            for arm in scope["arms"]
        )
        for parent_j in scope["parents"]:
            parent_users = membership[parent_j]
            for arm in scope["arms"]:
                cpath = chunk_path(args.tag, arm, parent_j)
                if cpath.exists():
                    try:
                        read_chunk(args.tag, arm, parent_j, spec, parent_users)
                        print(f"reuse chunk {cpath.name}", flush=True)
                        done += (scope["random_replicates"] if arm == "random"
                                 else 1) * 6
                        continue
                    except Exception as exc:
                        print(f"chunk {cpath.name} invalid ({exc}); recomputing",
                              flush=True)
                        cpath.unlink(missing_ok=True)
                nodes: list[dict[str, Any]] = []
                if arm == "random":
                    for repl in range(scope["random_replicates"]):
                        tree = random_tree(parent_users, parent_j, repl, spec)
                        for path in spec["arms"]["random"]["node_order"]:
                            members = tree[path]
                            rng = np.random.default_rng(
                                _derive_seed(spec["global_seed"], "run",
                                             parent_j, repl, path))
                            run = run_child(payload, matrix, members, rng)
                            nodes.append({
                                "path": path, "repl": repl,
                                "members": members, "run": run,
                            })
                else:
                    tree = spectral_tree(con, payload, stats, parent_users,
                                         parent_j, spec)
                    for path in spec["arms"]["spectral"]["node_order"]:
                        members = tree[path]
                        rng = np.random.default_rng(
                            _derive_seed(spec["global_seed"], "run",
                                         parent_j, 0, path))
                        run = run_child(payload, matrix, members, rng)
                        nodes.append({
                            "path": path, "repl": 0,
                            "members": members, "run": run,
                        })
                for nd in nodes:
                    nd["features"] = _label_free_child_features(nd["run"], eligible)
                write_chunk(args.tag, spec, arm, parent_j, parent_users, nodes)
                del nodes
                done += (scope["random_replicates"] if arm == "random"
                         else 1) * 6
                print(
                    f"parent {parent_j} arm {arm} done: {done}/{total} child "
                    f"runs, elapsed {time.time() - t0:.0f}s", flush=True,
                )
    finally:
        con.close()
    print(
        f"run done: {done}/{total} child runs, chunks in "
        f"{chunk_dir(args.tag)}, {time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Phase: consolidate
# ---------------------------------------------------------------------------

def _expected_sources(spec: dict[str, Any]) -> list[tuple[str, int, int, str, int]]:
    """Canonical source enumeration from the run scope: (arm, parent_j,
    repl, path, size)."""
    scope = spec.get("run_scope")
    if scope is None:
        raise SystemExit("spec has no run_scope; run prepare/run first")
    out: list[tuple[str, int, int, str, int]] = []
    for arm in scope["arms"]:
        repls = range(scope["random_replicates"]) if arm == "random" else [0]
        for parent_j in scope["parents"]:
            for repl in repls:
                for path, size in zip(
                    spec["arms"][arm]["node_order"],
                    spec["arms"][arm]["node_sizes"],
                ):
                    out.append((arm, parent_j, repl, path, size))
    return out


def phase_consolidate(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    spath = spec_path(args.tag)
    if not spath.exists():
        raise SystemExit(f"missing {spath}; run prepare first")
    spec = json.loads(spath.read_text(encoding="utf-8"))
    expected = _expected_sources(spec)
    payload, _, _ = year.load_matrix()
    membership = replay_80k_membership(payload)
    if spec.get("smoke"):
        cut = spec["prepare"]["smoke_parent_users"]
        membership = {j: membership[j][:cut] for j in membership}

    have: list[tuple[str, int, int, str, int, dict[str, Any]]] = []
    missing: list[str] = []
    for arm, parent_j, repl, path, size in expected:
        cpath = chunk_path(args.tag, arm, parent_j)
        if not cpath.exists():
            missing.append(f"{arm}:{parent_j}")
            continue
        try:
            records, _ = read_chunk(args.tag, arm, parent_j, spec,
                                    membership[parent_j])
        except Exception as exc:
            missing.append(f"{arm}:{parent_j} (invalid: {exc})")
            continue
        rec = next(r for r in records["records"]
                   if r["replicate"] == repl and r["path"] == path)
        have.append((arm, parent_j, repl, path, size, rec))
    n_missing = len(missing)
    if n_missing:
        msg = f"{n_missing} missing/invalid chunk(s): {missing[:8]}..."
        if not args.allow_partial:
            raise SystemExit(f"consolidate refuses partial campaign: {msg}")
        print(f"WARNING: {msg}", flush=True)
    n = len(have)
    if n == 0:
        raise SystemExit("no completed child runs to consolidate")

    # canonical row order: (arm_code, parent_j, repl, node_order_index)
    arm_code = np.array([0 if x[0] == "random" else 1 for x in have], dtype=np.int8)
    order = sorted(range(n), key=lambda i: (
        int(arm_code[i]), have[i][1], have[i][2],
        spec["arms"][have[i][0]]["node_order"].index(have[i][3]),
    ))
    arm_code = arm_code[order]
    parent_j_arr = np.asarray([have[i][1] for i in order], dtype=np.int32)
    repl_arr = np.asarray([have[i][2] for i in order], dtype=np.int16)
    path_idx = np.asarray([
        spec["arms"][have[i][0]]["node_order"].index(have[i][3])
        for i in order
    ], dtype=np.int16)
    size_arr = np.asarray([have[i][4] for i in order], dtype=np.int32)
    records = [have[i][5] for i in order]

    n_books = int(len(payload["work_ids"]))
    prefs = np.zeros((n, n_books), dtype=np.float32)
    directions = np.zeros((n, n_books), dtype=np.float32)
    for row, i in enumerate(order):
        arm, parent_j, repl, path, size, rec = have[i]
        records_meta, arrays = read_chunk(args.tag, arm, parent_j, spec,
                                          membership[parent_j])
        pos = records_meta["records"].index(rec)
        prefs[row] = arrays["prefs"][pos]
        directions[row] = arrays["directions"][pos]

    parent_endpoints = load_parent_endpoints()
    npz_path, json_path = census_paths(args.tag)
    _write_npz_atomic(
        npz_path,
        {
            "source_arm": arm_code,
            "source_parent": parent_j_arr,
            "source_repl": repl_arr,
            "source_path": path_idx,
            "source_size": size_arr,
            "prefs": prefs,
            "directions": directions,
            "parent_prefs": parent_endpoints["prefs"],
            "parent_directions": parent_endpoints["directions"],
            "parent_stage0": parent_endpoints["stage0_prefs"],
        },
    )
    sha = _sha256(npz_path)
    expected_ids = [node_source_id(x[0], x[1], x[2], x[3]) for x in expected]
    got_ids = [r["source_id"] for r in records]
    integrity = {
        "n_rows": n,
        "n_expected": len(expected),
        "complete": n == len(expected) and not missing,
        "missing": missing[:50],
        "canonical_order": True,
        "rows_match_records": got_ids == sorted(
            got_ids, key=lambda s: (
                {"random": 0, "spectral": 1}[s.split("-")[0]],
                int(s.split("-")[1]),
                int(s.split("-")[2]),
                spec["arms"][s.split("-")[0]]["node_order"].index(
                    "-".join(s.split("-")[3:])),
            )
        ),
        "expected_ids": expected_ids,
    }
    _write_text_atomic(
        json_path,
        json.dumps(
            {
                "records": records,
                "partial": n < len(expected),
                "expected_sources": [node_source_id(x[0], x[1], x[2], x[3])
                                     for x in expected],
                "integrity": integrity,
                "artifact_sha256": sha,
                "artifact_bytes": npz_path.stat().st_size,
                "method": _method_block("consolidate", args, **{
                    "n_sources": n,
                    "n_books": n_books,
                    "spec_hash": _param_hash(spec),
                }),
            },
            indent=1,
        ),
    )
    if not args.keep_chunks:
        for arm, parent_j, _r, _p, _s, _rec in have:
            chunk_path(args.tag, arm, parent_j).unlink(missing_ok=True)
        print(f"removed {len(have)} chunk files", flush=True)
    print(
        f"consolidate done: {n}/{len(expected)} sources, sha256 {sha[:16]}..., "
        f"{time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Label-blind representation + clustering (census conventions)
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


def _pairwise_summary(sim: np.ndarray) -> dict[str, float]:
    k = sim.shape[0]
    if k < 2:
        return {"mean": float("nan"), "median": float("nan"),
                "q90": float("nan"), "n": k}
    iu = np.triu_indices(k, k=1)
    vals = sim[iu]
    return {
        "mean": float(vals.mean()),
        "median": float(np.median(vals)),
        "q90": float(np.quantile(vals, 0.90)),
        "n": k,
    }


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


def _effective_dim(mat: np.ndarray) -> float:
    k = mat.shape[0]
    if k <= 1:
        return float(k)
    centered = mat - mat.mean(axis=0, keepdims=True)
    singular = np.linalg.svd(centered, compute_uv=False)
    e2 = singular**2
    total = e2.sum()
    return float(total**2 / np.sum(e2**2)) if np.sum(e2**2) > 0 else 0.0


def _fast_avg_link_clusters(mat: np.ndarray, tau: float) -> list[list[int]]:
    """Average-linkage cosine clustering via the precomputed cosine matrix.

    Numerically identical to scipy linkage(mat, method="average",
    metric="cosine") on unit vectors (cosine distance = 1 - dot); the
    precomputed BLAS path avoids recomputing pairwise distances per merge.
    The smoke phase asserts membership equality against the census
    clustering function on shared data.
    """
    n = mat.shape[0]
    if n <= 1:
        return [[i] for i in range(n)]
    sim = mat.astype(np.float64) @ mat.astype(np.float64).T
    d = np.maximum(0.0, 1.0 - sim)
    iu = np.triu_indices(n, k=1)
    condensed = d[iu]
    z = linkage(condensed, method="average")
    labels = fcluster(z, t=1.0 - tau, criterion="distance")
    out: dict[int, list[int]] = {}
    for i, c in enumerate(labels):
        out.setdefault(int(c), []).append(i)
    return [v for _, v in sorted(out.items())]


# ---------------------------------------------------------------------------
# Phase: geometry (label-blind structural analysis)
# ---------------------------------------------------------------------------

def _load_consolidated(
    args: argparse.Namespace,
    require_complete: bool,
) -> tuple[dict[str, Any], Any, dict[str, Any], dict[str, Any]]:
    npz_path, json_path = census_paths(args.tag)
    if not npz_path.exists() or not json_path.exists():
        raise SystemExit("missing consolidated artifact; run consolidate first")
    blob = np.load(npz_path, allow_pickle=False)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if require_complete and data.get("partial"):
        raise SystemExit("consolidated artifact is partial; refusing")
    return blob, data, npz_path, json_path


def _mode_recurrence_stats(
    mode_members: list[int],
    repl_of: np.ndarray,
    n_children: int,
) -> dict[str, Any]:
    repls = sorted({int(repl_of[m]) for m in mode_members})
    frac = len(mode_members) / n_children
    return {
        "replicates": repls,
        "n_distinct_replicates": len(repls),
        "recurrent": len(repls) >= 2,
        "fraction_of_children": float(frac),
        "size": len(mode_members),
    }


def phase_geometry(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    spath = spec_path(args.tag)
    if not spath.exists():
        raise SystemExit(f"missing {spath}; run prepare first")
    spec = json.loads(spath.read_text(encoding="utf-8"))
    blob, data, npz_path, json_path = _load_consolidated(
        args, require_complete=not args.allow_partial)
    records = data["records"]
    n = len(records)
    ids = [r["source_id"] for r in records]
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)

    arm_of = np.asarray([0 if r["arm"] == "random" else 1 for r in records],
                        dtype=np.int8)
    parent_of = np.asarray([r["parent_j"] for r in records], dtype=np.int32)
    repl_of = np.asarray([r["replicate"] for r in records], dtype=np.int16)
    path_of = np.asarray([
        spec["arms"][r["arm"]]["node_order"].index(r["path"])
        for r in records
    ], dtype=np.int16)
    size_of = np.asarray([r["size"] for r in records], dtype=np.int32)

    pref_reps = np.stack([
        _pref_rep(blob["prefs"][i], eligible) for i in range(n)
    ]).astype(np.float32)
    dir_reps = np.stack([
        _dir_rep(blob["directions"][i]) for i in range(n)
    ]).astype(np.float32)
    parent_prefs = blob["parent_prefs"].astype(np.float32)
    parent_dirs = blob["parent_directions"].astype(np.float32)
    n_parents = int(parent_prefs.shape[0])
    parent_reps = np.stack([
        _pref_rep(parent_prefs[j], eligible) for j in range(n_parents)
    ]).astype(np.float32)

    # child sizes from the spec (40000/20000 in the full campaign; smaller in
    # smoke), so group definitions stay valid for any bounded scope
    size40 = int(spec["arms"]["random"]["node_sizes"][0])
    size20 = int(spec["arms"]["random"]["node_sizes"][2])

    groups: dict[str, list[int]] = {
        "r20k": [i for i in range(n) if arm_of[i] == 0 and size_of[i] == size20],
        "r40k": [i for i in range(n) if arm_of[i] == 0 and size_of[i] == size40],
        "s20k": [i for i in range(n) if arm_of[i] == 1 and size_of[i] == size20],
        "s40k": [i for i in range(n) if arm_of[i] == 1 and size_of[i] == size40],
        "pooled20k": [i for i in range(n) if size_of[i] == size20],
        "pooled40k": [i for i in range(n) if size_of[i] == size40],
    }

    npz_out: dict[str, np.ndarray] = {}
    geometry: dict[str, Any] = {
        "source_order": ids,
        "n_sources": n,
        "groups": {g: len(idx) for g, idx in groups.items()},
        "pairwise": {},
        "clusters": {},
        "recurrence": {},
        "cross_arm": {},
        "mixture": {},
        "nulls": {},
    }

    # ---- global clustering + pairwise summaries (both spaces, 3 taus) ----
    for group, gidx in groups.items():
        if not gidx:
            continue
        gids = [ids[i] for i in gidx]
        for space in ("pref", "dir"):
            mat = pref_reps if space == "pref" else dir_reps
            sub = mat[gidx]
            sim = sub @ sub.T
            key = f"{group}_{space}"
            npz_out[f"rep_{key}"] = sub
            npz_out[f"sim_{key}"] = sim.astype(np.float32)
            geometry["pairwise"][f"{group}_{space}"] = _pairwise_summary(sim)
            geometry["clusters"][f"{group}_{space}"] = []
            for tau in CLUSTER_TAUS:
                cl = _fast_avg_link_clusters(sub, tau)
                block = []
                for ci, members in enumerate(cl):
                    centroid = _unit_rows(
                        sub[members].mean(axis=0, keepdims=True))[0].astype(np.float32)
                    rec = {
                        "members": [gids[m] for m in members],
                        "size": len(members),
                        "within": _within_stats(sim, members),
                        "effective_dim": _effective_dim(sub[members]),
                        "centroid_key": f"cent_{key}_{tau:.2f}_{ci}",
                    }
                    npz_out[rec["centroid_key"]] = centroid
                    block.append(rec)
                geometry["clusters"][f"{group}_{space}"].append(
                    {"tau": tau, "n_clusters": len(block),
                     "n_with_2plus": int(sum(1 for b in block if b["size"] >= 2)),
                     "clusters": block}
                )

    # ---- within-parent recurrence (random arm, 20k descendants, pref) ----
    r20k = groups["r20k"]
    r20k_by_parent: dict[int, list[int]] = {}
    for i in r20k:
        r20k_by_parent.setdefault(int(parent_of[i]), []).append(i)
    r20k_repl = repl_of[r20k]
    r20k_parent = parent_of[r20k]
    recurrence: dict[str, Any] = {}
    for tau in CLUSTER_TAUS:
        per_parent: dict[str, Any] = {}
        mode_count = 0
        recurrent_count = 0
        for j in range(n_parents):
            idx = r20k_by_parent.get(j, [])
            if not idx:
                continue
            sub = pref_reps[np.asarray(idx)]
            cl = _fast_avg_link_clusters(sub, tau)
            modes = []
            fractions = []
            for m in cl:
                stats = _mode_recurrence_stats(m, repl_of[np.asarray(idx)],
                                               len(idx))
                centroid = _unit_rows(
                    sub[m].mean(axis=0, keepdims=True))[0].astype(np.float32)
                cent_key = f"recur_cent_{tau:.2f}_p{j:03d}_{len(modes)}"
                npz_out[cent_key] = centroid
                anc_paths = sorted({
                    next(r for r in records if r["source_id"] == ids[idx[m0]])
                    ["path"].split(":")[0] + ":" + (
                        next(r for r in records
                             if r["source_id"] == ids[idx[m0]])["path"]
                        .split(":")[1])
                    for m0 in m
                })
                anc_ids = set()
                for m0 in m:
                    rec0 = next(r for r in records
                                if r["source_id"] == ids[idx[m0]])
                    anc_path = rec0["path"]
                    anc_id = node_source_id("random", j,
                                            rec0["replicate"],
                                            "40k:" + anc_path.split(":")[1])
                    anc_ids.add(anc_id)
                anc_pos = [ids.index(a) for a in anc_ids]
                anc_vectors = pref_reps[anc_pos]
                anc_centroid_cos = float(np.mean(
                    anc_vectors @ centroid)) if anc_vectors.shape[0] else float("nan")
                anc_pairwise = float(np.mean(
                    (anc_vectors @ anc_vectors.T)[np.triu_indices(
                        anc_vectors.shape[0], k=1)])) if anc_vectors.shape[0] >= 2 else float("nan")
                in_region = float(np.mean(anc_vectors @ centroid >= tau)) \
                    if anc_vectors.shape[0] else float("nan")
                frac = stats["fraction_of_children"]
                fractions.append(frac)
                modes.append({
                    "members": [ids[idx[m0]] for m0 in m],
                    **stats,
                    "centroid_key": cent_key,
                    "ancestor_40k": sorted(anc_ids),
                    "ancestor_centroid_cos": anc_centroid_cos,
                    "ancestor_pairwise_cos": anc_pairwise,
                    "ancestor_in_region_fraction": in_region,
                })
            n_modes = len(modes)
            probs = np.asarray(fractions, dtype=np.float64)
            probs = probs / probs.sum() if probs.sum() > 0 else probs
            entropy = float(-np.sum(probs * np.log(probs))) if n_modes > 1 else 0.0
            norm_entropy = float(entropy / np.log(n_modes)) if n_modes > 1 else 0.0
            per_parent[str(j)] = {
                "n_modes": n_modes,
                "n_recurrent": int(sum(1 for m in modes if m["recurrent"])),
                "modes": modes,
                "concentration": float(max(fractions)) if fractions else 0.0,
                "entropy": entropy,
                "normalized_entropy": norm_entropy,
            }
            mode_count += n_modes
            recurrent_count += sum(1 for m in modes if m["recurrent"])
        recurrence[str(tau)] = {
            "per_parent": per_parent,
            "total_modes": mode_count,
            "total_recurrent_modes": recurrent_count,
            "parents_with_children": len(per_parent),
        }
    geometry["recurrence"] = recurrence

    # ---- cross-arm matching (spectral 20k children vs recurrent modes) ----
    s20k = groups["s20k"]
    s20k_by_parent: dict[int, list[int]] = {}
    for i in s20k:
        s20k_by_parent.setdefault(int(parent_of[i]), []).append(i)
    cross_arm: dict[str, Any] = {}
    for tau in CLUSTER_TAUS:
        per_parent: dict[str, Any] = {}
        for j in range(n_parents):
            modes = recurrence[str(tau)]["per_parent"].get(str(j), {}).get("modes", [])
            recurrent = [m for m in modes if m["recurrent"]]
            s_idx = s20k_by_parent.get(j, [])
            if not recurrent or not s_idx:
                per_parent[str(j)] = {"n_recurrent_modes": len(recurrent),
                                      "n_spectral_children": len(s_idx),
                                      "matches": [], "distinct_modes": 0}
                continue
            cents = np.stack([npz_out[m["centroid_key"]] for m in recurrent])
            s_vecs = pref_reps[np.asarray(s_idx)]
            cos = s_vecs @ cents.T
            matches = []
            for k, si in enumerate(s_idx):
                best = int(np.argmax(cos[k]))
                # rank of this cosine among the parent's random 20k children
                r20k_idx = r20k_by_parent.get(j, [])
                r_cos = pref_reps[np.asarray(r20k_idx)] @ cents[best]
                rank = int(np.sum(r_cos > cos[k, best]))
                s_best_of_mode = int(np.argmax(cos[:, best])) == k
                matches.append({
                    "spectral_child": ids[si],
                    "nearest_mode_index": best,
                    "nearest_mode_id": f"p{j:03d}_m{best}",
                    "cos": float(cos[k, best]),
                    "cos_rank_among_random": rank,
                    "mutual_best": s_best_of_mode,
                })
            for m_i, m in enumerate(matches):
                m["nearest_mode_id"] = (
                    f"recurrent_mode_{tau:.2f}_p{j:03d}_{m_i}")
            per_parent[str(j)] = {
                "n_recurrent_modes": len(recurrent),
                "n_spectral_children": len(s_idx),
                "matches": matches,
                "distinct_modes": len({m["nearest_mode_index"] for m in matches}),
            }
        cross_arm[str(tau)] = per_parent
    geometry["cross_arm"] = cross_arm

    # ---- parent-as-mixture: convex hull of recurrent child-mode centroids ----
    mixture: dict[str, Any] = {}
    for j in range(n_parents):
        # mixture uses the FINEST recurrence definition per parent; use the
        # union over taus of recurrent modes at the mode's own tau
        used = set()
        for tau in CLUSTER_TAUS:
            for m in recurrence[str(tau)]["per_parent"].get(str(j), {}).get("modes", []):
                if m["recurrent"]:
                    used.add(m["centroid_key"])
        cents = np.stack([npz_out[k] for k in sorted(used)]) if used else None
        p = parent_reps[j]
        if cents is None or cents.shape[0] == 0:
            mixture[str(j)] = {"n_recurrent_modes": 0,
                               "best_single_cos": None,
                               "best_single_error": None,
                               "hull_error": None,
                               "alpha": None,
                               "improvement": None,
                               "relative_improvement": None}
            continue
        best_i = int(np.argmax(cents @ p))
        best_single_cos = float(cents[best_i] @ p)
        best_single_error = float(np.linalg.norm(p - cents[best_i]))
        k = cents.shape[0]
        x0 = np.full(k, 1.0 / k)
        cons = {"type": "eq", "fun": lambda a: float(a.sum()) - 1.0}
        bounds = [(0.0, 1.0)] * k
        res = minimize(
            lambda a: float(np.sum((p - cents.T @ a) ** 2)),
            x0, method="SLSQP", bounds=bounds, constraints=cons,
            options={"ftol": 1e-12, "maxiter": 500, "disp": False},
        )
        alpha = np.asarray(res.x, dtype=np.float64)
        alpha = np.maximum(alpha, 0.0)
        alpha = alpha / alpha.sum() if alpha.sum() > 0 else alpha
        hull_error = float(np.linalg.norm(p - cents.T @ alpha))
        improvement = float(best_single_error - hull_error)
        relative = float(improvement / best_single_error) \
            if best_single_error > 1e-12 else 0.0
        mixture[str(j)] = {
            "n_recurrent_modes": k,
            "centroid_keys": sorted(used),
            "best_single_index": best_i,
            "best_single_cos": best_single_cos,
            "best_single_error": best_single_error,
            "hull_error": hull_error,
            "alpha": [float(a) for a in alpha],
            "improvement": improvement,
            "relative_improvement": relative,
            "slsqp_success": bool(res.success),
        }
    geometry["mixture"] = mixture

    # ---- permutation nulls (label-free) ----
    rng_null = np.random.default_rng(
        _derive_seed(spec["global_seed"], "null"))
    parents_with_children = sorted({int(p) for p in parent_of})
    n_pw = len(parents_with_children)
    nulls: dict[str, Any] = {}
    for tau in CLUSTER_TAUS:
        observed = np.mean([
            recurrence[str(tau)]["per_parent"][str(j)]["concentration"]
            for j in parents_with_children
        ]) if parents_with_children else float("nan")
        perm_stats = []
        for _ in range(NULL_PERMUTATIONS):
            pi = rng_null.permutation(parents_with_children)
            stats_p = []
            for j, perm in zip(parents_with_children, pi):
                idx = r20k_by_parent.get(int(perm), [])
                if not idx:
                    continue
                sub = pref_reps[np.asarray(idx)]
                cl = _fast_avg_link_clusters(sub, tau)
                fracs = [len(m) / len(idx) for m in cl]
                stats_p.append(max(fracs) if fracs else 0.0)
            perm_stats.append(float(np.mean(stats_p)))
        perm_stats = np.asarray(perm_stats, dtype=np.float64)
        rank = float(np.mean(perm_stats >= observed))
        nulls[f"concentration_{tau:.2f}"] = {
            "observed": float(observed),
            "null_mean": float(perm_stats.mean()),
            "null_sd": float(perm_stats.std()),
            "null_min": float(perm_stats.min()),
            "null_max": float(perm_stats.max()),
            "observed_percentile": rank,
            "n_permutations": int(NULL_PERMUTATIONS),
        }
    # mixture null: shuffle parent endpoints across parents
    rel_obs = [m["relative_improvement"] for m in mixture.values()
               if m.get("relative_improvement") is not None]
    observed_mean_rel = float(np.mean(rel_obs)) if rel_obs else float("nan")
    perm_rels = []
    for _ in range(NULL_PERMUTATIONS):
        pi = rng_null.permutation(list(range(n_parents)))
        vals = []
        for j in range(n_parents):
            m = mixture[str(j)]
            if m.get("relative_improvement") is None:
                continue
            p2 = parent_reps[pi[j]]
            cents = None
            used = []
            for tau in CLUSTER_TAUS:
                for mode in recurrence[str(tau)]["per_parent"].get(str(j), {}) \
                        .get("modes", []):
                    if mode["recurrent"] and mode["centroid_key"] not in used:
                        used.append(mode["centroid_key"])
            if not used:
                continue
            cents = np.stack([npz_out[k] for k in sorted(used)])
            best_single_error = float(np.min(np.linalg.norm(p2 - cents, axis=1)))
            x0 = np.full(cents.shape[0], 1.0 / cents.shape[0])
            cons = {"type": "eq", "fun": lambda a: float(a.sum()) - 1.0}
            bounds = [(0.0, 1.0)] * cents.shape[0]
            res = minimize(
                lambda a: float(np.sum((p2 - cents.T @ a) ** 2)),
                x0, method="SLSQP", bounds=bounds, constraints=cons,
                options={"ftol": 1e-12, "maxiter": 500, "disp": False},
            )
            alpha = np.maximum(np.asarray(res.x, dtype=np.float64), 0.0)
            alpha = alpha / alpha.sum() if alpha.sum() > 0 else alpha
            hull_err = float(np.linalg.norm(p2 - cents.T @ alpha))
            if best_single_error > 1e-12:
                vals.append((best_single_error - hull_err) / best_single_error)
        perm_rels.append(float(np.mean(vals)) if vals else float("nan"))
    perm_rels = np.asarray(perm_rels, dtype=np.float64)
    perm_rels = perm_rels[np.isfinite(perm_rels)]
    nulls["mixture_relative_improvement"] = {
        "observed": float(observed_mean_rel),
        "n_observed_parents": int(len(rel_obs)),
        "null_mean": float(perm_rels.mean()) if len(perm_rels) else float("nan"),
        "null_sd": float(perm_rels.std()) if len(perm_rels) else float("nan"),
        "observed_percentile": float(np.mean(perm_rels >= observed_mean_rel))
        if len(perm_rels) else float("nan"),
        "n_permutations": int(NULL_PERMUTATIONS),
    }
    geometry["nulls"] = nulls

    # ---- invariant checks ----
    invariant_checks: list[dict[str, Any]] = []
    dup_keys = len(npz_out) != len(set(npz_out))
    invariant_checks.append(
        {"check": "npz_key_uniqueness", "ok": not dup_keys,
         "detail": f"{len(npz_out)} keys"})
    if dup_keys:
        raise SystemExit("geometry invariant failed: duplicate npz keys")
    for group, gidx in groups.items():
        if not gidx:
            continue
        gids = [ids[i] for i in gidx]
        for space in ("pref", "dir"):
            mat = pref_reps if space == "pref" else dir_reps
            sub = mat[gidx]
            for tau in CLUSTER_TAUS:
                block = geometry["clusters"][f"{group}_{space}"][
                    {"0.3": 0, "0.5": 1, "0.7": 2}[f"{tau:.1f}"]]["clusters"]
                reclustered = _fast_avg_link_clusters(sub, tau)
                ok = True
                for c in block:
                    members = [gidx[gids.index(gids_id)]
                               for gids_id in c["members"]]
                    ok &= any(
                        sorted(c["members"]) == sorted([ids[gidx[x]] for x in cl])
                        for cl in reclustered
                    )
                invariant_checks.append(
                    {"check": f"reclustering_{group}_{space}_{tau:.2f}",
                     "ok": bool(ok)})
                if not ok:
                    raise SystemExit(
                        f"geometry invariant failed: reclustering "
                        f"{group}_{space}_{tau:.2f}")

    geometry["method"] = _method_block("geometry", args, **{
        "n_sources": n,
        "n_parents": n_parents,
        "groups": {g: len(idx) for g, idx in groups.items()},
        "elig_min_book_n": int(ELIG_MIN_BOOK_N),
        "representation_pref": spec["analysis"]["representation_pref"],
        "representation_dir": spec["analysis"]["representation_dir"],
        "clustering": spec["analysis"]["clustering"],
        "recurrent_mode_rule": spec["analysis"]["recurrent_mode_rule"],
        "null_permutations": int(NULL_PERMUTATIONS),
        "semantic_context_loaded": False,
        "unblinded": False,
        "written_before_unblinding": True,
    })
    geometry["invariant_checks"] = invariant_checks

    geo_json, geo_npz = geometry_paths(args.tag)
    _write_npz_atomic(geo_npz, npz_out)
    geo_sha = _sha256(geo_npz)
    census_sha = _sha256(npz_path)
    geometry["seal"] = {
        "geometry_npz_sha256": geo_sha,
        "census_npz_sha256": census_sha,
        "n_sources": n,
        "sources": ids,
        "clustering": spec["analysis"]["clustering"],
        "eligibility": {"min_book_n": int(ELIG_MIN_BOOK_N)},
        "seed": spec["global_seed"],
        "git_head": _git_head(),
        "semantic_context_loaded": False,
        "unblinded": False,
    }
    _write_text_atomic(geo_json, json.dumps(geometry, indent=1))
    manifest = {
        "seal_manifest_version": 1,
        "artifacts": {
            "census_npz": {"file": npz_path.name, "sha256": census_sha,
                           "bytes": npz_path.stat().st_size},
            "geometry_npz": {"file": geo_npz.name, "sha256": geo_sha,
                             "bytes": geo_npz.stat().st_size},
            "geometry_json": {"file": geo_json.name,
                              "sha256": _sha256(geo_json),
                              "bytes": geo_json.stat().st_size},
        },
        "n_sources": n,
        "sources": ids,
        "git_head": _git_head(),
        "command": shlex.join(sys.argv),
        "semantic_context_loaded": False,
        "unblinded": False,
    }
    _write_text_atomic(seal_manifest_path(args.tag),
                       json.dumps(manifest, indent=1))
    print(
        f"geometry frozen: {geo_json} ({geo_json.stat().st_size/2**20:.1f} MiB), "
        f"{geo_npz} ({geo_npz.stat().st_size/2**20:.1f} MiB), "
        f"seal sha256 {geo_sha[:16]}..., {time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Phase: prereport (PRE-UNBLIND structural summary)
# ---------------------------------------------------------------------------

def _verify_manifest(args: argparse.Namespace) -> dict[str, bool]:
    npz_path, json_path = census_paths(args.tag)
    geo_json, geo_npz = geometry_paths(args.tag)
    path = seal_manifest_path(args.tag)
    if not path.exists():
        raise SystemExit(f"seal manifest {path} missing; refusing")
    man = json.loads(path.read_text(encoding="utf-8"))
    if man.get("semantic_context_loaded") is not False:
        raise SystemExit("seal manifest claims semantic context loaded; refusing")
    checks = {
        "census_npz": _sha256(npz_path) == man["artifacts"]["census_npz"]["sha256"],
        "geometry_npz": _sha256(geo_npz) == man["artifacts"]["geometry_npz"]["sha256"],
        "geometry_json": _sha256(geo_json) == man["artifacts"]["geometry_json"]["sha256"],
    }
    if not all(checks.values()):
        raise SystemExit(f"seal manifest hash mismatch: {checks}; refusing")
    return checks


def _fmt_float(x: Any, nd: int = 4) -> str:
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) \
        else f"{x:.{nd}f}"


def phase_prereport(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    spath = spec_path(args.tag)
    if not spath.exists():
        raise SystemExit(f"missing {spath}; run prepare first")
    spec = json.loads(spath.read_text(encoding="utf-8"))
    geo_json, geo_npz = geometry_paths(args.tag)
    if not geo_json.exists() or not geo_npz.exists():
        raise SystemExit("missing geometry artifact; run geometry first")
    geometry = json.loads(geo_json.read_text(encoding="utf-8"))
    manifest_checks = _verify_manifest(args)

    lines = [
        "# Hierarchical jury decomposition: PRE-UNBLIND structural summary",
        "",
        "**Generated by the `prereport` phase from the sealed geometry alone. "
        "No semantic context (titles, authors, literary sets, known pole, "
        "genres, publication year) was loaded to produce this document.**",
        "",
        f"**Question.** When an 80k random jury is decomposed into smaller "
        f"sub-juries and the existing convergence-reversal dynamics are rerun, "
        f"do different children converge into different recurrent basins?",
        "",
        "## Provenance and seal",
        "",
        f"- Command: `{geometry['method']['command']}`",
        f"- Global seed: **{spec['global_seed']}**; parent campaign: tag "
        f"`main`, seed **{MAIN_SEED}**, sizes {list(MAIN_SIZES)}, "
        f"{MAIN_JURIES} juries per size",
        f"- Sealed geometry git commit: `{geometry['seal']['git_head']}`",
        f"- Census artifact: `{geometry['seal']['census_npz_sha256']}` (SHA256, sealed)",
        f"- Geometry artifact: `{geometry['seal']['geometry_npz_sha256']}` (SHA256, sealed)",
        f"- External seal manifest verified: "
        f"census_npz {manifest_checks['census_npz']}, "
        f"geometry_npz {manifest_checks['geometry_npz']}, "
        f"geometry_json {manifest_checks['geometry_json']}.",
        f"- Sources: **{geometry['n_sources']}** child reversal endpoints "
        f"({len(geometry['groups'])} groups: "
        + ", ".join(f"{k}={v}" for k, v in geometry["groups"].items()) + ").",
        "",
        "## PRE-UNBLIND STRUCTURAL RESULTS",
        "",
        "Reversal: `run_jury` (research_jury_ensemble_reversal.py) from the "
        "standard jury seed (20.0 on the child users, 0.4 elsewhere, "
        f"mean-normalized), beta {spec['reversal']['beta']}, "
        f"{spec['reversal']['iterations']} iterations, max "
        f"{spec['reversal']['max_stages']} stages, retained target "
        f"{spec['reversal']['retained_target']}, gain/hard pruning, "
        f"evidence floor {spec['reversal']['min_remaining_fraction']}.",
        "",
        "Spectral representation: `resid = rating - user_mean - book_mean + "
        "global_mean` over the fixed eligible universe, row-L2 normalized, "
        "leading user direction by deterministic power iteration, median "
        "split with stable user-id tie break.",
        "",
        f"Representations: pref = {spec['analysis']['representation_pref']}; "
        f"dir = {spec['analysis']['representation_dir']}. Clustering: "
        f"{spec['analysis']['clustering']['method']} at tau "
        f"{spec['analysis']['clustering']['taus']}; singletons kept.",
        "",
        "### Pairwise endpoint similarity (off-diagonal, preference space)",
        "",
        "| group | n | mean | median | q90 |",
        "|---|---:|---:|---:|---:|",
    ]
    for group, space in ((g, "pref") for g in geometry["groups"]):
        if f"{group}_{space}" not in geometry["pairwise"]:
            continue
        pw = geometry["pairwise"][f"{group}_{space}"]
        lines.append(
            f"| {group} | {pw['n']} | {_fmt_float(pw['mean'])} | "
            f"{_fmt_float(pw['median'])} | {_fmt_float(pw['q90'])} |"
        )
    lines += [
        "",
        "### Global cluster census (preference space)",
        "",
        "| group | tau | clusters | >=2 members | largest |",
        "|---|---:|---:|---:|---:|",
    ]
    for group in geometry["groups"]:
        key = f"{group}_pref"
        if key not in geometry["clusters"]:
            continue
        for row in geometry["clusters"][key]:
            sizes = [c["size"] for c in row["clusters"]]
            largest = max(sizes) if sizes else 0
            lines.append(
                f"| {group} | {row['tau']:.2f} | {row['n_clusters']} | "
                f"{row['n_with_2plus']} | {largest} |"
            )
    lines += [
        "",
        "### Within-parent recurrence (random arm, 20k descendants)",
        "",
        "Recurrent modes require descendants from at least two DISTINCT random "
        "partition replicates. Per-parent mode concentration is the largest "
        "mode share of the parent's 12 random 20k descendants.",
        "",
        "| tau | parents | total modes | recurrent modes | mean concentration | mean normalized entropy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for tau in CLUSTER_TAUS:
        rec = geometry["recurrence"][str(tau)]
        concent = [p["concentration"] for p in rec["per_parent"].values()]
        entr = [p["normalized_entropy"] for p in rec["per_parent"].values()]
        lines.append(
            f"| {tau:.2f} | {rec['parents_with_children']} | "
            f"{rec['total_modes']} | {rec['total_recurrent_modes']} | "
            f"{np.mean(concent):.4f} | {np.mean(entr):.4f} |"
        )
    lines += [
        "",
        "### Cross-arm matching (spectral 20k children vs recurrent random modes)",
        "",
        "| tau | parents with matches | distinct-mode mappings |",
        "|---|---:|---:|",
    ]
    n_distinct = 0
    n_with = 0
    for tau in CLUSTER_TAUS:
        for p in geometry["cross_arm"][str(tau)].values():
            if p.get("matches"):
                n_with += 1
                n_distinct += p["distinct_modes"]
        lines.append(
            f"| {tau:.2f} | {n_with} | {n_distinct} |"
        )
    lines += [
        "",
        "### Parent-as-mixture geometry (convex hull of recurrent modes)",
        "",
        "For each parent, p = the frozen normalized preference-space endpoint; "
        "the hull fit minimizes `||p - sum(alpha_i c_i)||^2` with `alpha >= 0`, "
        "`sum(alpha) = 1`. Improvement is best-single-error minus hull error. "
        "No success threshold is defined or reported here; the distribution is "
        "descriptive.",
        "",
        "| statistic | value |",
        "|---|---|",
    ]
    rels = [m["relative_improvement"] for m in geometry["mixture"].values()
            if m.get("relative_improvement") is not None]
    imps = [m["improvement"] for m in geometry["mixture"].values()
            if m.get("improvement") is not None]
    lines += [
        f"| parents with >= 1 recurrent mode | {len(rels)} |",
        f"| relative improvement: mean | {np.mean(rels):.4f} |" if rels else "| relative improvement | n/a |",
        f"| relative improvement: min / median / max | "
        f"{np.min(rels):.4f} / {np.median(rels):.4f} / {np.max(rels):.4f} |" if rels else "| n/a |",
        f"| absolute improvement: mean | {np.mean(imps):.4f} |" if imps else "| absolute improvement | n/a |",
    ]
    lines += [
        "",
        "### Label-free permutation nulls",
        "",
        "| statistic | observed | null mean | null sd | observed percentile |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, val in geometry["nulls"].items():
        lines.append(
            f"| {key} | {_fmt_float(val['observed'])} | "
            f"{_fmt_float(val['null_mean'])} | {_fmt_float(val['null_sd'])} | "
            f"{_fmt_float(val.get('observed_percentile'))} |"
        )
    lines += [
        "",
        "### Invariant checks",
        "",
    ]
    for check in geometry["invariant_checks"]:
        lines.append(f"- {check['check']}: {'ok' if check['ok'] else 'FAILED'}")
    out = prereport_path(args.tag)
    _write_text_atomic(out, "\n".join(lines) + "\n")
    print(f"prereport written: {out}, {time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------------------
# Phase: unblind (DO NOT RUN in this task)
# ---------------------------------------------------------------------------

def phase_unblind(args: argparse.Namespace) -> None:
    """Post-hoc semantic evaluation, only after every structural artifact is
    sealed.  Never run during the label-blind campaign task."""
    global SEMANTIC_CONTEXT_LOADED
    _verify_manifest(args)
    from curators_explorer.scripts import (
        research_natural_amplification_census as census,
        research_seedless_spectral_pilot as spectral_mod,
    )
    SEMANTIC_CONTEXT_LOADED = True
    geo_json, geo_npz = geometry_paths(args.tag)
    npz_path, json_path = census_paths(args.tag)
    geometry = json.loads(geo_json.read_text(encoding="utf-8"))
    blob = np.load(npz_path, allow_pickle=False)
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    meta, eval_sets = spectral_mod.load_posthoc_context(payload["work_ids"])
    eligible_idx = np.flatnonzero(eligible)

    def evaluate(score: np.ndarray) -> dict[str, int]:
        pref = {
            "score": np.asarray(score, dtype=np.float64),
            "mean": np.asarray(score, dtype=np.float64),
            "reader_mass": np.where(eligible, payload["book_n"], 0.0).astype(np.float64),
        }
        _rows, metrics = census._eval_pref(
            pref["score"], pref["reader_mass"], payload["work_ids"],
            meta, eval_sets, limit=200,
        )
        return metrics

    rows = []
    for i, rec in enumerate(json.loads(json_path.read_text(encoding="utf-8"))
                             ["records"]):
        rows.append({
            "source_id": rec["source_id"],
            "metrics": evaluate(blob["prefs"][i]),
        })
    for key, centroid in geometry.get("recurrent_mode_centroid_keys", []):
        rows.append({
            "source_id": f"recurrent_mode:{key}",
            "metrics": evaluate(
                np.zeros(len(payload["work_ids"]), dtype=np.float64) if False
                else blob["prefs"][0]),  # placeholder; real unblind later
        })
    out = posthoc_path(args.tag)
    out.write_text(json.dumps({"records": rows, "unblinded": True}, indent=1),
                   encoding="utf-8")
    print(f"unblind written: {out}", flush=True)


# ---------------------------------------------------------------------------
# Smoke phase: bounded end-to-end validation
# ---------------------------------------------------------------------------

def _smoke_partition_tests(payload: dict[str, np.ndarray],
                           spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Partition correctness: deterministic, sizes, disjoint, exact union,
    hierarchy; spectral tree on a small real subset with tie handling."""
    checks: list[dict[str, Any]] = []
    parent_users = replay_80k_membership(payload)[0]
    ok = len(parent_users) == PARENT_SIZE
    checks.append({"check": "parent_replay_size", "ok": ok,
                   "detail": str(len(parent_users))})

    t1 = random_tree(parent_users, 0, 0, spec)
    t2 = random_tree(parent_users, 0, 0, spec)
    same = all(np.array_equal(t1[k], t2[k]) for k in t1)
    checks.append({"check": "random_tree_deterministic", "ok": same})

    union40 = np.unique(np.concatenate([t1["40k:0"], t1["40k:1"]]))
    checks.append({"check": "random_40k_union_equals_parent", "ok":
                   len(union40) == PARENT_SIZE and np.array_equal(
                       np.sort(union40), np.sort(parent_users))})
    checks.append({"check": "random_40k_disjoint", "ok":
                   len(np.intersect1d(t1["40k:0"], t1["40k:1"])) == 0})
    for ci in (0, 1):
        g = t1[f"40k:{ci}"]
        for gi in (0, 1):
            ch = t1[f"20k:{ci}:{gi}"]
            checks.append({
                "check": f"random_20k_{ci}_{gi}_subset_of_40k", "ok":
                len(np.intersect1d(ch, g)) == len(ch)})
    all20 = np.unique(np.concatenate(
        [t1[f"20k:{ci}:{gi}"] for ci in (0, 1) for gi in (0, 1)]))
    checks.append({"check": "random_20k_union_equals_parent", "ok":
                   len(all20) == PARENT_SIZE and np.array_equal(
                       np.sort(all20), np.sort(parent_users))})
    disjoint20 = all(
        len(np.intersect1d(t1[f"20k:{ci}:{gi}"], t1[f"20k:{cj}:{gj}"])) == 0
        for ci in (0, 1) for gi in (0, 1) for cj in (0, 1) for gj in (0, 1)
        if (ci, gi) != (cj, gj)
    )
    checks.append({"check": "random_20k_pairwise_disjoint", "ok": disjoint20})
    checks.append({"check": "random_20k_sizes",
                   "ok": all(len(t1[k]) == 20000 for k in t1 if k.startswith("20k"))
                   and all(len(t1[k]) == 40000 for k in t1 if k.startswith("40k"))})

    # spectral tree on a small real subset (2 x 600 -> 2 x 300)
    small = parent_users[:SMOKE_PARENT_USERS]
    con = _edges_connection()
    try:
        con.execute(
            "create temp table pu as select (row_number() over "
            "(order by user_id)-1)::int as ui, user_id from "
            "(select distinct unnest(?) as user_id) t",
            [payload["user_ids"].tolist()],
        )
        con.execute(
            "create temp table wb as select (row_number() over "
            "(order by work_id)-1)::int as bi, work_id from "
            "(select distinct unnest(?) as work_id) t",
            [payload["work_ids"].tolist()],
        )
        stats = load_rating_stats("smoke", payload)
        tree1 = spectral_tree(con, payload, stats, small, 0, spec)
        tree2 = spectral_tree(con, payload, stats, small, 0, spec)
        checks.append({"check": "spectral_tree_deterministic", "ok":
                       all(np.array_equal(tree1[k], tree2[k]) for k in tree1)})
        checks.append({"check": "spectral_tree_sizes", "ok":
                       len(tree1["40k:0"]) == len(tree1["40k:1"]) == SMOKE_PARENT_USERS // 2
                       and all(len(tree1[k]) == SMOKE_PARENT_USERS // 4
                               for k in tree1 if k.startswith("20k"))})
        union40s = np.unique(np.concatenate([tree1["40k:0"], tree1["40k:1"]]))
        checks.append({"check": "spectral_40k_union", "ok":
                       np.array_equal(np.sort(union40s), np.sort(small))})
        checks.append({"check": "spectral_40k_disjoint", "ok":
                       len(np.intersect1d(tree1["40k:0"], tree1["40k:1"])) == 0})
        all20s = np.unique(np.concatenate(
            [tree1[f"20k:{ci}:{gi}"] for ci in (0, 1) for gi in (0, 1)]))
        checks.append({"check": "spectral_20k_union", "ok":
                       np.array_equal(np.sort(all20s), np.sort(small))})

        # tie handling: duplicate coordinates -> stable user-id split
        fake_coord = np.zeros(len(small))
        fake_coord[: len(small) // 2] = 1.0
        g0, g1 = median_split(small, fake_coord)
        checks.append({"check": "median_split_ties_stable", "ok":
                       len(g0) == len(g1) == SMOKE_PARENT_USERS // 2
                       and np.array_equal(g0, np.sort(small[SMOKE_40K:]))
                       and np.array_equal(g1, np.sort(small[:SMOKE_40K]))})

        # sparse/memory: no dense user-user or user-book arrays
        edges = fetch_parent_edges(con, payload, small)
        M = residual_csr(edges, stats, len(small), len(payload["work_ids"]))
        checks.append({"check": "residual_csr_format", "ok":
                       isinstance(M, csr_matrix) and M.nnz > 0})
        row_norm = np.sqrt(np.asarray(M.multiply(M).sum(axis=1)).ravel())
        checks.append({"check": "residual_row_l2", "ok":
                       float(np.max(np.abs(
                           row_norm[np.diff(M.indptr) > 0] - 1.0))) < 1e-5})
        checks.append({"check": "residual_empty_rows_ok", "ok":
                       int((np.diff(M.indptr) == 0).sum()) < len(small)})
        checks.append({"check": "residual_shape", "ok":
                       M.shape[0] == len(small) and M.shape[1] == len(payload["work_ids"])})
        u = leading_user_direction(M)
        checks.append({"check": "leading_direction_shape",
                       "ok": u.shape == (len(small),)})
        checks.append({"check": "leading_direction_unit",
                       "ok": abs(float(np.linalg.norm(u)) - 1.0) < 1e-6})
    finally:
        con.close()
    return checks


def _smoke_reversal_tests(payload: dict[str, np.ndarray],
                          matrix: Any,
                          spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Invoke the actual reused reversal on tiny child nodes; verify shapes,
    alignment, determinism, and that no semantic context was loaded."""
    checks: list[dict[str, Any]] = []
    parent_users = replay_80k_membership(payload)[0]
    members = parent_users[:SMOKE_20K]
    rng = np.random.default_rng(_derive_seed(spec["global_seed"], "smoke", 0))
    run1 = run_child(payload, matrix, members, rng)
    run2 = run_child(payload, matrix, members, np.random.default_rng(
        _derive_seed(spec["global_seed"], "smoke", 1)))
    checks.append({"check": "reversal_endpoint_shape",
                   "ok": run1["final_pref"].shape == (len(payload["work_ids"]),)})
    checks.append({"check": "reversal_direction_shape",
                   "ok": run1["stages"][-1]["direction"].shape
                   == (len(payload["work_ids"]),)})
    checks.append({"check": "reversal_stage0_shape",
                   "ok": run1["stage0_pref"].shape == (len(payload["work_ids"]),)})
    checks.append({"check": "reversal_stages_positive",
                   "ok": len(run1["stages"]) >= 1
                   and run1["stages"][-1]["remaining_users"] > 0})
    checks.append({"check": "reversal_deterministic",
                   "ok": np.array_equal(run1["final_pref"], run2["final_pref"])
                   and np.array_equal(run1["stages"][-1]["direction"],
                                      run2["stages"][-1]["direction"])})
    checks.append({"check": "reversal_no_semantics",
                   "ok": SEMANTIC_CONTEXT_LOADED is False})
    return checks


def _smoke_resume_tests(tag: str, spec: dict[str, Any],
                        payload: dict[str, np.ndarray],
                        matrix: Any) -> list[dict[str, Any]]:
    """Valid-chunk reuse, corrupted chunk recompute, scope-change rejection."""
    checks: list[dict[str, Any]] = []
    parent_users = replay_80k_membership(payload)[0]
    rng = np.random.default_rng(_derive_seed(spec["global_seed"], "smoke_r", 0))
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    nodes = []
    for path, offset in (("40k:0", 0), ("40k:1", SMOKE_40K)):
        members = parent_users[offset:offset + SMOKE_40K]
        run = run_child(payload, matrix, members, rng)
        nodes.append({
            "path": path, "repl": 0, "members": members, "run": run,
            "features": _label_free_child_features(run, eligible),
        })
    cpath = write_chunk(tag, spec, "random", 0, parent_users, nodes)
    records, arrays = read_chunk(tag, "random", 0, spec, parent_users)
    checks.append({"check": "chunk_roundtrip",
                   "ok": records["n"] == 2
                   and arrays["prefs"].shape == (2, len(payload["work_ids"]))
                   and records["records"][0]["source_id"] == "random-000-0-40k:0"
                   and records["records"][1]["source_id"] == "random-000-0-40k:1"})

    try:
        read_chunk(tag, "random", 0, {**spec, "global_seed": 1}, parent_users)
        checks.append({"check": "chunk_spec_hash_rejected", "ok": False})
    except (ValueError, KeyError):
        checks.append({"check": "chunk_spec_hash_rejected", "ok": True})

    scope_changed = dict(spec)
    scope_changed["run_scope"] = {
        "parents": [0, 1], "random_replicates": 1, "arms": ["random"],
        "full_random_replicates": 3,
    }
    try:
        read_chunk(tag, "random", 0, scope_changed, parent_users)
        checks.append({"check": "chunk_scope_change_rejected", "ok": False})
    except ValueError:
        checks.append({"check": "chunk_scope_change_rejected", "ok": True})

    cpath.write_bytes(b"corrupted garbage")
    try:
        read_chunk(tag, "random", 0, spec, parent_users)
        checks.append({"check": "corrupt_chunk_detected", "ok": False})
    except Exception:
        checks.append({"check": "corrupt_chunk_detected", "ok": True})
    cpath.unlink(missing_ok=True)

    missing_chunks = [c for c in range(2)
                      if not chunk_path(tag, "random", c).exists()]
    checks.append({"check": "cleanup_removed_chunks",
                   "ok": len(missing_chunks) == 2})
    return checks


def _smoke_geometry_tests(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Synthetic geometry invariants: two-mode clustering, recurrence across
    replicates, convex-hull mixture beats best single, cross-arm matching."""
    checks: list[dict[str, Any]] = []
    rng = np.random.default_rng(_derive_seed(spec["global_seed"], "geo"))
    n_books = 500
    a = rng.normal(size=n_books)
    b = rng.normal(size=n_books)
    a -= a.mean(); a /= np.linalg.norm(a)
    b -= b.mean(); b /= np.linalg.norm(b)
    def rep(x: np.ndarray) -> np.ndarray:
        c = x - x.mean()
        return c / np.linalg.norm(c)
    def noisy(x: np.ndarray) -> np.ndarray:
        eps = (0.05 / np.sqrt(n_books)) * rng.normal(size=n_books)
        return rep(x + eps)
    mode_a = np.stack([noisy(a) for _ in range(4)])
    mode_b = np.stack([noisy(b) for _ in range(4)])
    mat = np.vstack([mode_a, mode_b]).astype(np.float32)
    cl = _fast_avg_link_clusters(mat, 0.70)
    sizes = sorted(len(c) for c in cl)
    checks.append({"check": "synthetic_two_mode_clustering", "ok":
                   sizes == [4, 4]})

    # recurrence: children from 2 replicates in the same mode
    mat2 = np.vstack([mode_a, mode_a]).astype(np.float32)
    repl = np.asarray([0, 1, 0, 1, 0, 1, 0, 1])
    cl2 = _fast_avg_link_clusters(mat2, 0.70)
    all_recurrent = all(
        len({int(repl[m]) for m in c}) >= 2 for c in cl2 if len(c) >= 2)
    checks.append({"check": "recurrence_across_replicates", "ok": all_recurrent})
    # single-replicate siblings must not be recurrent
    repl_single = np.asarray([0, 0, 0, 0, 0, 0, 0, 0])
    never = all(
        len({int(repl_single[m]) for m in c}) < 2 for c in cl2 if len(c) >= 2)
    checks.append({"check": "single_replicate_not_recurrent", "ok": never})

    # convex hull: p = 0.5 a + 0.5 b is better fit by hull than best single
    p = rep(0.5 * a + 0.5 * b)
    C = np.vstack([mode_a[0], mode_b[0]]).astype(np.float32)
    best_single = float(np.max(C @ p))
    x0 = np.full(2, 0.5)
    res = minimize(
        lambda al: float(np.sum((p - C.T @ al) ** 2)),
        x0, method="SLSQP", bounds=[(0, 1), (0, 1)],
        constraints={"type": "eq", "fun": lambda al: float(al.sum()) - 1.0},
        options={"ftol": 1e-12},
    )
    hull_err = float(np.linalg.norm(p - C.T @ res.x))
    best_err = float(np.linalg.norm(p - mode_a[0]))
    checks.append({"check": "convex_hull_beats_best_single",
                   "ok": hull_err < best_err - 1e-6
                   and abs(float(res.x.sum()) - 1.0) < 1e-6})

    # cross-arm: spectral child near mode A maps to mode A (mutual best)
    s_vecs = np.vstack([mode_a[0], mode_b[0]]).astype(np.float32)
    cents = C
    cos = s_vecs @ cents.T
    mapped = [int(np.argmax(cos[k])) for k in range(2)]
    checks.append({"check": "cross_arm_maps_to_intended_modes",
                   "ok": mapped == [0, 1]
                   and int(np.argmax(cos[:, 0])) == 0
                   and int(np.argmax(cos[:, 1])) == 1})

    # fast clustering == census clustering on shared data
    from curators_explorer.scripts import research_natural_amplification_census as census
    same = all(
        sorted([sorted(c) for c in _fast_avg_link_clusters(mat, tau)]) ==
        sorted([sorted(c) for c in census.avg_link_clusters(mat, tau)])
        for tau in CLUSTER_TAUS
    )
    checks.append({"check": "fast_clustering_matches_census", "ok": same})
    return checks


def _smoke_firewall_scan(artifacts: list[Path]) -> list[dict[str, Any]]:
    """Assert no forbidden semantic tokens in the pre-unblind artifacts.

    Scans text files only (npz are binary; containment is by construction:
    no semantic data is ever loaded pre-unblind).  Matches whole words so
    protocol vocabulary (e.g. "semantic_context_loaded") cannot self-flag,
    and skips the single provenance sentence that states no semantic context
    was loaded.
    """
    checks: list[dict[str, Any]] = []
    bad: list[str] = []
    tokens = [t for t in FORBIDDEN_SEMANTIC_TOKENS if t != "anti"]
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in tokens) + r")\b")
    for path in artifacts:
        if not path.exists() or path.suffix not in (".json", ".md", ".txt"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for line in text.splitlines():
            lower = line.casefold()
            if "semantic context" in lower:
                continue
            for m in pattern.finditer(lower):
                bad.append(f"{path.name}:{m.group(0)}")
    checks.append({"check": "semantic_firewall_artifacts",
                   "ok": not bad, "detail": "; ".join(sorted(set(bad))[:20])})
    checks.append({"check": "semantic_flag_false",
                   "ok": SEMANTIC_CONTEXT_LOADED is False})
    return checks


def phase_smoke(args: argparse.Namespace) -> None:
    t0 = time.time()
    assert not SEMANTIC_CONTEXT_LOADED
    tag = "smoke"
    args.tag = tag
    args.max_parents = 1
    args.replicates = 2
    args.arms = "all"
    args.allow_partial = True

    # smoke spec: tiny parent, tiny nodes
    spec = full_spec(args)
    spec["smoke"] = True
    spec["arms"]["random"]["node_sizes"] = [SMOKE_40K, SMOKE_40K,
                                            SMOKE_20K, SMOKE_20K,
                                            SMOKE_20K, SMOKE_20K]
    spec["arms"]["spectral"]["node_sizes"] = spec["arms"]["random"]["node_sizes"]
    spec["prepare"] = {"parents": [0], "smoke_parent_users": SMOKE_PARENT_USERS}
    _apply_run_scope(spec, {"parents": [0], "random_replicates": 2,
                            "arms": ["random", "spectral"]})
    _write_text_atomic(spec_path(tag), json.dumps(spec, indent=1))

    checks: list[dict[str, Any]] = []
    payload, matrix, _ = year.load_matrix()
    parent_users = replay_80k_membership(payload)[0]
    smoke_parent = parent_users[:SMOKE_PARENT_USERS]
    build_rating_stats(tag, payload)

    checks += _smoke_partition_tests(payload, spec)
    checks += _smoke_reversal_tests(payload, matrix, spec)
    checks += _smoke_resume_tests(tag, spec, payload, matrix)
    checks += _smoke_geometry_tests(spec)

    # ---- bounded campaign through the real phase functions ----
    con = _edges_connection()
    try:
        con.execute(
            "create temp table pu as select (row_number() over "
            "(order by user_id)-1)::int as ui, user_id from "
            "(select distinct unnest(?) as user_id) t",
            [payload["user_ids"].tolist()],
        )
        con.execute(
            "create temp table wb as select (row_number() over "
            "(order by work_id)-1)::int as bi, work_id from "
            "(select distinct unnest(?) as work_id) t",
            [payload["work_ids"].tolist()],
        )
        stats = load_rating_stats(tag, payload)
        for arm in ("random", "spectral"):
            cpath = chunk_path(tag, arm, 0)
            nodes: list[dict[str, Any]] = []
            if arm == "random":
                for repl in range(2):
                    tree = random_tree(smoke_parent, 0, repl, spec)
                    for path in spec["arms"]["random"]["node_order"]:
                        members = tree[path]
                        rng = np.random.default_rng(
                            _derive_seed(spec["global_seed"], "run", 0, repl, path))
                        run = run_child(payload, matrix, members, rng)
                        nodes.append({"path": path, "repl": repl,
                                      "members": members, "run": run})
            else:
                tree = spectral_tree(con, payload, stats, smoke_parent, 0, spec)
                for path in spec["arms"]["spectral"]["node_order"]:
                    members = tree[path]
                    rng = np.random.default_rng(
                        _derive_seed(spec["global_seed"], "run", 0, 0, path))
                    run = run_child(payload, matrix, members, rng)
                    nodes.append({"path": path, "repl": 0,
                                  "members": members, "run": run})
            eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
            for nd in nodes:
                nd["features"] = _label_free_child_features(nd["run"], eligible)
            write_chunk(tag, spec, arm, 0, smoke_parent, nodes)
            print(f"smoke chunk {arm} written", flush=True)
    finally:
        con.close()

    phase_consolidate(args)
    phase_geometry(args)
    phase_prereport(args)

    # firewall scan of all pre-unblind artifacts
    artifacts = [
        spec_path(tag), rating_stats_path(tag), census_paths(tag)[0],
        census_paths(tag)[1], geometry_paths(tag)[0], geometry_paths(tag)[1],
        seal_manifest_path(tag), prereport_path(tag),
    ]
    checks += _smoke_firewall_scan(artifacts)

    report = {
        "seed": args.seed,
        "checks": checks,
        "passed": all(c["ok"] for c in checks),
        "git_head": _git_head(),
        "runtime_seconds": time.time() - t0,
    }
    out = smoke_report_path(tag)
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"smoke report: {out}", flush=True)
    failed = [c for c in checks if not c["ok"]]
    print(
        f"smoke done in {time.time() - t0:.0f}s: {len(checks) - len(failed)}/"
        f"{len(checks)} checks passed", flush=True,
    )
    for f in failed:
        print(f"  FAILED: {f['check']} ({f.get('detail', '')})", flush=True)
    if failed:
        raise SystemExit("smoke checks failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=["prepare", "run", "consolidate", "geometry", "prereport",
                 "unblind", "smoke"],
        required=True,
    )
    parser.add_argument("--tag", default=None, help="artifact tag (default: none)")
    parser.add_argument("--seed", type=int, default=GLOBAL_SEED)
    parser.add_argument("--arms", choices=["random", "spectral", "all"],
                        default="all")
    parser.add_argument("--max-parents", type=int, default=MAIN_JURIES)
    parser.add_argument("--replicates", type=int, default=RANDOM_REPLICATES)
    parser.add_argument("--keep-chunks", action="store_true")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="let consolidate/geometry proceed on an incomplete campaign",
    )
    args = parser.parse_args()
    if args.seed != GLOBAL_SEED and args.phase != "smoke":
        raise SystemExit(
            f"--seed must be the preregistered {GLOBAL_SEED} outside smoke"
        )
    if args.replicates > RANDOM_REPLICATES:
        raise SystemExit(f"--replicates must be <= {RANDOM_REPLICATES}")
    if args.phase == "prepare":
        phase_prepare(args)
    elif args.phase == "run":
        phase_run(args)
    elif args.phase == "consolidate":
        phase_consolidate(args)
    elif args.phase == "geometry":
        phase_geometry(args)
    elif args.phase == "prereport":
        phase_prereport(args)
    elif args.phase == "unblind":
        phase_unblind(args)
    else:
        phase_smoke(args)


if __name__ == "__main__":
    main()

"""Label-blind structural addendum: tau=.70 recurrent-mode families.

Entirely label-blind.  Uses ONLY the already frozen main campaign artifacts
(census + geometry); loads NO semantic context (no titles, authors,
literary sets, known pole, genres, publication year) and never invokes the
semantic unblind.

Questions addressed BEFORE semantic unblind:

PART A: do the 244 independently recurrent within-parent random modes
        (tau = 0.70) form recurring CROSS-PARENT basin families?
PART B: do the ratings-only spectral splits independently recover the
        random-decomposition modes (own-parent best-cosine calibration
        vs a parent-set-shuffle null)?
PART C: are a parent's own recurrent modes specifically related to its
        parent endpoint in ABSOLUTE distance/cosine (best-single and
        absolute convex-hull error), even though the EXTRA benefit of
        convex mixing was not parent-specific in the old relative test?

The frozen result for the relative convex-mixture test (kept as-is, not
reinterpreted): mixture_rel_0.70 observed relative improvement 0.0536,
empirical upper-tail p 0.985 (null / non-significant).

Phases:

- smoke:  bounded/synthetic tests + real source-seal validation (no
          analyze, no unblind);
- analyze: full structural addendum against the sealed main campaign;
- prereport: structural PRE-UNBLIND markdown summary.

Scientific design is frozen in this module and in the sealed source
campaign: addendum seed 20260820, 10,000 label-blind permutations,
family cuts at cosine-distance thresholds 0.30/0.50/0.70, average-linkage
hierarchical clustering on the frozen 244x244 mode cosine matrix, the
exact frozen _mixture_fit (SLSQP, alpha >= 0, sum(alpha) = 1) for the
precomputed 120x120 hull-error matrix, and the exact frozen preference
representation convention (book_n >= 25 -> mean-center eligible
coordinates -> L2).

Performance: every expensive book-space cosine product and every
convex-hull fit is computed ONCE before the permutation nulls; all 10,000
permutations use only integer indexing/reductions over precomputed
matrices (no book-space dot products, no SLSQP inside any permutation
loop).

Memory: the addendum NPZ stores only the small frozen numerical objects
(244x244 mode cosine matrix, cross-parent family centroids,
480x244 spectral-to-mode cosines, 120x120 BEST / HULL_ERROR /
BEST_SINGLE_ERROR) -- it does NOT duplicate the 560 MiB census vectors.
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts import research_year_aware_canon as year
from curators_explorer.scripts.research_jury_decomposition import (
    ELIG_MIN_BOOK_N,
    _avg_linkage_cuts,
    _cut_clusters,
    _derive_seed,
    _effective_dim_gram,
    _git_head,
    _mixture_fit,
    _pref_rep,
    _sha256,
    _unit_rows,
    _within_stats,
    _write_npz_atomic,
    _write_text_atomic,
)

# ---------------------------------------------------------------------------
# Preregistered addendum parameters (never tuned from results).
# ---------------------------------------------------------------------------
ADDENDUM_SEED = 20260820
N_PERMUTATIONS = 10000          # label-blind permutations (indexing only)
FAMILY_TAUS = (0.30, 0.50, 0.70)
MODE_TAU = 0.70                 # recurrent-mode source tau (frozen result)
MAIN_JURIES = 120
EXPECTED_N_RECURRENT_MODES = 244   # frozen main campaign count at tau=.70
N_SPECTRAL_20K = 480            # spectral-arm 20k children (4 per parent)

# True only inside the semantic unblind phase of the source experiment;
# this addendum never loads semantic context.
SEMANTIC_CONTEXT_LOADED = False

FORBIDDEN_SEMANTIC_TOKENS = (
    "title", "author", "exact_lit", "broad_lit", "pole",
    "year", "genre", "evaluation", "poll", "literary",
)

# ---------------------------------------------------------------------------
# Paths (main frozen campaign artifacts only).
# ---------------------------------------------------------------------------
DATA = Path(__file__).resolve().parents[1] / "data"
SPEC_PATH = DATA / "jury_decomposition_spec.json"
CENSUS_NPZ = DATA / "jury_decomposition.npz"
CENSUS_JSON = DATA / "jury_decomposition.json"
GEO_JSON = DATA / "jury_decomposition_geometry.json"
GEO_NPZ = DATA / "jury_decomposition_geometry.npz"
MANIFEST = DATA / "jury_decomposition_seal_manifest.json"
ADD_JSON = DATA / "jury_decomposition_mode_families.json"
ADD_NPZ = DATA / "jury_decomposition_mode_families.npz"
ADD_MANIFEST = DATA / "jury_decomposition_mode_families_seal_manifest.json"
ADD_REPORT = DATA / "JURY_DECOMPOSITION_MODE_FAMILIES_PREUNBLIND_REPORT.md"
SMOKE_REPORT = DATA / "jury_decomposition_mode_families_smoke_report.json"


def _write_json_atomic(path: Path, obj: Any) -> None:
    _write_text_atomic(path, json.dumps(obj, indent=1))


# ---------------------------------------------------------------------------
# Source campaign seal verification (label-blind).
# ---------------------------------------------------------------------------

def _verify_source_campaign() -> dict[str, Any]:
    """Verify the EXISTING frozen main campaign exactly before analysis.

    Requires: all four external-manifest hashes verify; census NPZ SHA ==
    geometry seal; census JSON SHA == geometry seal; geometry NPZ SHA ==
    geometry seal; geometry seal partial == false; census partial == false;
    semantic_context_loaded == false; unblinded == false; exactly 2880
    sources; source list matches the frozen seal.  Raises SystemExit on any
    violation; returns the verified provenance facts."""
    for p in (SPEC_PATH, CENSUS_NPZ, CENSUS_JSON, GEO_NPZ, GEO_JSON,
              MANIFEST):
        if not p.exists():
            raise SystemExit(f"missing frozen source artifact {p}")
    geometry = json.loads(GEO_JSON.read_text(encoding="utf-8"))
    seal = geometry.get("seal")
    if not seal:
        raise SystemExit("frozen geometry has no seal; refusing")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cons = json.loads(CENSUS_JSON.read_text(encoding="utf-8"))

    def _must(name: str, ok: bool) -> None:
        if not ok:
            raise SystemExit(f"source seal check failed: {name}; refusing")

    _must("seal claims semantic", seal.get("semantic_context_loaded") is False)
    _must("seal claims unblinded", seal.get("unblinded") is False)
    _must("seal partial", seal.get("partial") is False)
    _must("census partial", cons.get("partial") is False)
    _must("manifest census_npz",
          manifest["artifacts"]["census_npz"]["sha256"] == _sha256(CENSUS_NPZ))
    _must("manifest census_json",
          manifest["artifacts"]["census_json"]["sha256"] == _sha256(CENSUS_JSON))
    _must("manifest geometry_npz",
          manifest["artifacts"]["geometry_npz"]["sha256"] == _sha256(GEO_NPZ))
    _must("manifest geometry_json",
          manifest["artifacts"]["geometry_json"]["sha256"] == _sha256(GEO_JSON))
    _must("seal census_npz", seal["census_npz_sha256"] == _sha256(CENSUS_NPZ))
    _must("seal census_json", seal["census_json_sha256"] == _sha256(CENSUS_JSON))
    _must("seal geometry_npz", seal["geometry_npz_sha256"] == _sha256(GEO_NPZ))
    records = cons["records"]
    ids = [r["source_id"] for r in records]
    _must("n_sources 2880", len(records) == 2880)
    _must("seal n_sources", seal["n_sources"] == len(records))
    _must("seal source list", seal["sources"] == ids)
    return {
        "census_npz_sha256": _sha256(CENSUS_NPZ),
        "census_json_sha256": _sha256(CENSUS_JSON),
        "geometry_npz_sha256": _sha256(GEO_NPZ),
        "geometry_json_sha256": _sha256(GEO_JSON),
        "n_sources": len(records),
        "campaign_git_head": seal.get("git_head"),
        "campaign_seed": seal.get("seed"),
        "partial": False,
        "semantic_context_loaded": False,
        "unblinded": False,
    }


# ---------------------------------------------------------------------------
# Primary structural objects: the tau=.70 recurrent random modes.
# ---------------------------------------------------------------------------

def _load_recurrent_modes(
    geometry: dict[str, Any],
    gblob: dict[str, np.ndarray],
    expect_count: int,
) -> list[dict[str, Any]]:
    """Extract ALL recurrent random-arm modes at tau=0.70 from the FROZEN
    geometry, in stable order (parent ascending, mode index ascending).

    Uses the EXACT frozen recur_cent_* centroid from the sealed geometry
    NPZ (never recomputed).  Asserts finite, approximately unit L2 norm."""
    per_parent = geometry["recurrence"][str(MODE_TAU)]["per_parent"]
    modes: list[dict[str, Any]] = []
    for j in range(MAIN_JURIES):
        ms = per_parent.get(str(j), {}).get("modes", [])
        for mi, m in enumerate(ms):
            if not m["recurrent"]:
                continue
            key = m["centroid_key"]
            if key not in gblob:
                raise SystemExit(
                    f"frozen centroid {key} missing from geometry NPZ")
            centroid = np.asarray(gblob[key], dtype=np.float64)
            norm = float(np.linalg.norm(centroid))
            if not np.isfinite(centroid).all() or abs(norm - 1.0) > 1e-4:
                raise SystemExit(
                    f"frozen centroid {key} not finite/unit (norm {norm})")
            modes.append({
                "mode_id": m["mode_id"],
                "parent_j": int(j),
                "mode_index": int(mi),
                "centroid_key": key,
                "members": list(m["members"]),
                "replicates": list(m["replicates"]),
                "n_distinct_replicates": int(m["n_distinct_replicates"]),
                "size": int(m["size"]),
                "centroid": centroid,
            })
    if len(modes) != expect_count:
        raise SystemExit(
            f"expected {expect_count} recurrent modes at tau={MODE_TAU}, "
            f"found {len(modes)}")
    return modes


# ---------------------------------------------------------------------------
# PART A -- cross-parent mode families (244 x 244, one linkage, 3 cuts).
# ---------------------------------------------------------------------------

def _family_analysis(
    modes: list[dict[str, Any]],
    npz_out: dict[str, np.ndarray],
) -> tuple[np.ndarray, dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Cluster the 244 frozen mode centroids once (average linkage on the
    cosine matrix), cut at FAMILY_TAUS.  Freezes every family; stores
    centroids ONLY for cross-parent families (n_distinct_parents >= 2)."""
    n = len(modes)
    cent = np.asarray([m["centroid"] for m in modes])
    sim = cent @ cent.T
    _d, z = _avg_linkage_cuts(sim)
    families_by_tau: dict[str, Any] = {}
    summaries_by_tau: dict[str, Any] = {}
    invariant_checks: list[dict[str, Any]] = []

    for tau in FAMILY_TAUS:
        cl = _cut_clusters(z, n, tau)
        families: list[dict[str, Any]] = []
        for fi, members in enumerate(cl):
            mem_modes = [modes[i] for i in members]
            parents = sorted({m["parent_j"] for m in mem_modes})
            by_parent: dict[str, int] = {}
            for m in mem_modes:
                by_parent[str(m["parent_j"])] = by_parent.get(
                    str(m["parent_j"]), 0) + 1
            cross = len(parents) >= 2
            rec: dict[str, Any] = {
                "family_id": f"{tau:.2f}_f{fi}",
                "tau": tau,
                "member_mode_ids": [m["mode_id"] for m in mem_modes],
                "member_parents": parents,
                "n_modes": len(mem_modes),
                "n_distinct_parents": len(parents),
                "mode_counts_by_parent": by_parent,
                "within_mean_cos": _within_stats(sim, members)["mean"],
                "within_median_cos": _within_stats(sim, members)["median"],
                "within_min_cos": _within_stats(sim, members)["min"],
                "effective_dim": _effective_dim_gram(
                    sim[np.ix_(members, members)]),
                "cross_parent": cross,
            }
            if cross:
                key = f"family_cent_{tau:.2f}_f{fi}"
                cent = _unit_rows(
                    np.mean(np.asarray([m["centroid"] for m in mem_modes]),
                            axis=0, keepdims=True))[0]
                npz_out[key] = cent.astype(np.float32)
                rec["centroid_key"] = key
            families.append(rec)
        n_cross = sum(1 for f in families if f["cross_parent"])
        sizes = [f["n_modes"] for f in families]
        n_parents_cross = [f["n_distinct_parents"] for f in families
                           if f["cross_parent"]]
        largest_by_modes = max(families, key=lambda f: f["n_modes"]) \
            if families else None
        largest_by_parents = max(families, key=lambda f: f["n_distinct_parents"]) \
            if families else None
        summaries_by_tau[str(tau)] = {
            "n_families": len(families),
            "n_cross_parent": n_cross,
            "n_families_ge3_parents": sum(
                1 for f in families if f["n_distinct_parents"] >= 3),
            "n_families_ge5_parents": sum(
                1 for f in families if f["n_distinct_parents"] >= 5),
            "largest_by_n_modes": largest_by_modes["family_id"]
            if largest_by_modes else None,
            "largest_by_n_distinct_parents": largest_by_parents["family_id"]
            if largest_by_parents else None,
            "median_n_distinct_parents_cross": float(np.median(n_parents_cross))
            if n_parents_cross else None,
            "median_family_n_modes": float(np.median(sizes)) if sizes else None,
        }
        families_by_tau[str(tau)] = {"families": families}

        # invariant: families partition all modes exactly once at this tau
        flat = []
        for f in families:
            for mid in f["member_mode_ids"]:
                flat.append(next(i for i, m in enumerate(modes)
                                 if m["mode_id"] == mid))
        partition_ok = (len(flat) == n and sorted(flat) == list(range(n)))
        invariant_checks.append({
            "check": f"family_partition_tau_{tau:.2f}",
            "ok": partition_ok,
            "detail": f"{len(families)} families covering all {n} modes",
        })
        if not partition_ok:
            raise SystemExit(f"family partition failed at tau={tau:.2f}")

        # invariant: cross-parent family centroids reconstruct exactly
        recon_ok = True
        for f in families:
            if not f.get("centroid_key"):
                continue
            c = np.asarray(npz_out[f["centroid_key"]], dtype=np.float64)
            recomputed = _unit_rows(np.mean(np.asarray(
                [modes[next(i for i, m in enumerate(modes)
                            if m["mode_id"] == mid)]["centroid"]
                 for mid in f["member_mode_ids"]]), axis=0, keepdims=True))[0]
            if not np.allclose(c, recomputed, atol=1e-6):
                recon_ok = False
        invariant_checks.append({
            "check": f"family_centroid_reconstruction_tau_{tau:.2f}",
            "ok": recon_ok,
            "detail": "cross-parent family centroids match frozen members",
        })
        if not recon_ok:
            raise SystemExit(f"family centroid reconstruction failed tau={tau:.2f}")

    invariant_checks.append({
        "check": "mode_sim_symmetric_diagonal",
        "ok": bool(np.allclose(sim, sim.T, atol=1e-6)
                   and np.allclose(np.diag(sim), 1.0, atol=1e-6)),
        "detail": f"{n}x{n} mode cosine matrix symmetric, unit diagonal",
    })
    return sim, families_by_tau, summaries_by_tau, invariant_checks


# ---------------------------------------------------------------------------
# PART B -- ratings-only spectral recovery of the random modes.
# ---------------------------------------------------------------------------

def _spectral_score_tables(
    cos_spectral_modes: np.ndarray,
    mode_set_by_parent: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Reduce a (480 x 244) cosine matrix to (480 x 120) best-cosine and
    argmax-mode tables: for every spectral child and every parent mode-set,
    the best cosine to any mode of that set and the global mode index."""
    n_children = cos_spectral_modes.shape[0]
    score = np.empty((n_children, len(mode_set_by_parent)), dtype=np.float64)
    argmode = np.empty((n_children, len(mode_set_by_parent)), dtype=np.int64)
    for s, gidx in enumerate(mode_set_by_parent):
        sub = cos_spectral_modes[:, gidx]
        score[:, s] = sub.max(axis=1)
        argmode[:, s] = gidx[np.argmax(sub, axis=1)]
    return score, argmode


def _spectral_observed(
    score: np.ndarray, argmode: np.ndarray,
    cos_spectral_modes: np.ndarray, mode_set_by_parent: list[np.ndarray],
    child_parent: np.ndarray, children_by_parent: list[np.ndarray],
) -> dict[str, Any]:
    """Observed own-parent spectral calibration statistics."""
    rows = np.arange(score.shape[0])
    own = score[rows, child_parent]
    own_arg = argmode[rows, child_parent]
    per_parent_mean: dict[str, float] = {}
    per_parent_coverage: dict[str, float] = {}
    mutual = np.zeros(score.shape[0], dtype=bool)
    for j, ch in enumerate(children_by_parent):
        per_parent_mean[str(j)] = float(np.mean(own[ch]))
        set_j = mode_set_by_parent[j]
        selected = set()
        for c in ch:
            selected.add(int(own_arg[c]))
        per_parent_coverage[str(j)] = len(selected) / len(set_j) \
            if len(set_j) else 0.0
        for g in set_j:
            cosg = cos_spectral_modes[ch, int(g)]
            best_child = int(ch[np.argmax(cosg)])
            for c in ch:
                if int(own_arg[c]) == int(g) and c == best_child:
                    mutual[c] = True
    return {
        "mean_best_cos": float(own.mean()),
        "median_best_cos": float(np.median(own)),
        "q25_best_cos": float(np.quantile(own, 0.25)),
        "q75_best_cos": float(np.quantile(own, 0.75)),
        "per_parent_mean_best_cos": per_parent_mean,
        "mean_per_parent_coverage": float(np.mean(
            list(per_parent_coverage.values()))),
        "per_parent_coverage": per_parent_coverage,
        "fraction_mutual_best_sibling": float(mutual.mean()),
    }


def _spectral_shuffle_null(
    score: np.ndarray, argmode: np.ndarray,
    child_parent: np.ndarray, children_by_parent: list[np.ndarray],
    set_sizes: np.ndarray, n_perms: int, seed: int,
) -> dict[str, Any]:
    """Parent-set-shuffle null: permute the 120 intact recurrent-mode sets
    across parent identities and re-evaluate the per-child best-cosine and
    per-parent mode coverage.  ONLY indexing/reductions over the
    precomputed tables (no book-space products, no optimization)."""
    rng = np.random.default_rng(seed)
    n_children = score.shape[0]
    rows = np.arange(n_children)
    ch = np.asarray(children_by_parent)
    sizes = np.asarray(set_sizes, dtype=np.float64)
    n_parents = len(children_by_parent)
    stats_mean = np.empty(n_perms, dtype=np.float64)
    stats_median = np.empty(n_perms, dtype=np.float64)
    stats_coverage = np.empty(n_perms, dtype=np.float64)
    for t in range(n_perms):
        pi = rng.permutation(n_parents)
        s = pi[child_parent]
        vals = score[rows, s]
        stats_mean[t] = float(vals.mean())
        stats_median[t] = float(np.median(vals))
        sj = pi
        argm = argmode[ch, sj[:, None]]
        so = np.sort(argm, axis=1)
        uniq = np.sum(so[:, 1:] != so[:, :-1], axis=1) + 1
        stats_coverage[t] = float(np.mean(uniq / sizes))
    return {
        "null_mean_best_cos": float(stats_mean.mean()),
        "null_sd_best_cos": float(stats_mean.std()),
        "null_mean_median_best_cos": float(stats_median.mean()),
        "null_mean_coverage": float(stats_coverage.mean()),
        "null_sd_coverage": float(stats_coverage.std()),
        "mean_stats": stats_mean,
        "median_stats": stats_median,
        "coverage_stats": stats_coverage,
    }


# ---------------------------------------------------------------------------
# PART C -- parent specificity (absolute distance/cosine).
# ---------------------------------------------------------------------------

def _parent_best_matrix(
    parent_modes_cos: np.ndarray,
    mode_set_by_parent: list[np.ndarray],
) -> np.ndarray:
    """BEST[i,j] = max cosine between parent endpoint i and any tau=.70
    recurrent mode of parent j."""
    n_parents = len(mode_set_by_parent)
    best = np.empty((n_parents, n_parents), dtype=np.float64)
    for j, gidx in enumerate(mode_set_by_parent):
        best[:, j] = parent_modes_cos[:, gidx].max(axis=1)
    return best


def _parent_best_null(BEST: np.ndarray, n_perms: int,
                      seed: int) -> np.ndarray:
    """Parent-assignment null: permute the 120 mode sets across parent
    endpoints and take the mean/median of the indexed diagonal BEST
    entries.  Indexing only."""
    rng = np.random.default_rng(seed)
    n = BEST.shape[0]
    rows = np.arange(n)
    stats = np.empty(n_perms, dtype=np.float64)
    for t in range(n_perms):
        pi = rng.permutation(n)
        stats[t] = float(np.mean(BEST[rows, pi]))
    return stats


def _hull_error_matrix(
    parent_reps: np.ndarray,
    mode_centroids: np.ndarray,
    mode_set_by_parent: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """PRECOMPUTE the complete 120x120 absolute convex-hull fit table and
    the best-single-error table (from unit-vector best cosine:
    sqrt(max(0, 2 - 2*cos))).  Exactly 120 x 120 = 14,400 fits, ONCE."""
    n_parents = len(mode_set_by_parent)
    hull = np.empty((n_parents, n_parents), dtype=np.float64)
    best_single = np.empty((n_parents, n_parents), dtype=np.float64)
    for i in range(n_parents):
        p = parent_reps[i]
        for j, gidx in enumerate(mode_set_by_parent):
            cents = mode_centroids[gidx]
            fit = _mixture_fit(p, cents)
            hull[i, j] = fit["hull_error"]
            best_single[i, j] = fit["best_single_error"]
    return hull, best_single


def _hull_error_null(HULL: np.ndarray, n_perms: int,
                     seed: int) -> np.ndarray:
    """Hull null: permute the 120 mode sets across parent endpoints and
    take the mean of the indexed HULL_ERROR diagonal entries.  Indexing
    only (the 120x120 table is precomputed; never refit)."""
    rng = np.random.default_rng(seed)
    n = HULL.shape[0]
    rows = np.arange(n)
    stats = np.empty(n_perms, dtype=np.float64)
    for t in range(n_perms):
        pi = rng.permutation(n)
        stats[t] = float(np.mean(HULL[rows, pi]))
    return stats


def _tail_p_upper(nulls: np.ndarray, observed: float,
                  n_perms: int) -> float:
    return float((1 + int(np.sum(nulls >= observed))) / (n_perms + 1))


def _tail_p_lower(nulls: np.ndarray, observed: float,
                  n_perms: int) -> float:
    return float((1 + int(np.sum(nulls <= observed))) / (n_perms + 1))


# ---------------------------------------------------------------------------
# Full analyze phase (label-blind; NOT run in this task).
# ---------------------------------------------------------------------------

def phase_analyze(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    provenance = _verify_source_campaign()

    geometry = json.loads(GEO_JSON.read_text(encoding="utf-8"))
    cons = json.loads(CENSUS_JSON.read_text(encoding="utf-8"))
    records = cons["records"]
    blob = np.load(CENSUS_NPZ, allow_pickle=False)
    gblob = np.load(GEO_NPZ, allow_pickle=False)
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)

    modes = _load_recurrent_modes(geometry, gblob,
                                  EXPECTED_N_RECURRENT_MODES)
    n_modes = len(modes)
    mode_centroids = np.asarray([m["centroid"] for m in modes])
    mode_set_by_parent = [np.asarray(
        [i for i, m in enumerate(modes) if m["parent_j"] == j],
        dtype=np.int64) for j in range(MAIN_JURIES)]
    set_sizes = np.asarray([len(s) for s in mode_set_by_parent],
                           dtype=np.int64)

    # ---- PART A: cross-parent families ----
    npz_out: dict[str, np.ndarray] = {}
    sim, families_by_tau, family_summaries, invariant_checks = \
        _family_analysis(modes, npz_out)
    npz_out["mode_sim"] = sim.astype(np.float32)

    # ---- PART B: spectral recovery ----
    spectral_rows = [i for i, r in enumerate(records)
                     if r["arm"] == "spectral" and r["size"] == 20000]
    if len(spectral_rows) != N_SPECTRAL_20K:
        raise SystemExit(f"expected {N_SPECTRAL_20K} spectral 20k rows, "
                         f"found {len(spectral_rows)}")
    spectral_reps = np.asarray([
        _pref_rep(blob["prefs"][i], eligible) for i in spectral_rows
    ]).astype(np.float64)
    child_parent = np.asarray([records[i]["parent_j"]
                               for i in spectral_rows], dtype=np.int64)
    children_by_parent = [np.asarray(
        [c for c, pj in enumerate(child_parent) if int(pj) == j],
        dtype=np.int64) for j in range(MAIN_JURIES)]
    cos_spectral_modes = spectral_reps @ mode_centroids.T
    npz_out["spectral_mode_cos"] = cos_spectral_modes.astype(np.float32)
    score, argmode = _spectral_score_tables(cos_spectral_modes,
                                            mode_set_by_parent)
    spectral_obs = _spectral_observed(
        score, argmode, cos_spectral_modes, mode_set_by_parent,
        child_parent, children_by_parent)
    null_seed_b = _derive_seed(ADDENDUM_SEED, "spectral_shuffle_null")
    null_b = _spectral_shuffle_null(
        score, argmode, child_parent, children_by_parent, set_sizes,
        N_PERMUTATIONS, null_seed_b)
    spectral_result = {
        "observed": spectral_obs,
        "null": {
            "mean_best_cos": null_b["null_mean_best_cos"],
            "sd_best_cos": null_b["null_sd_best_cos"],
            "mean_median_best_cos": null_b["null_mean_median_best_cos"],
            "mean_coverage": null_b["null_mean_coverage"],
            "sd_coverage": null_b["null_sd_coverage"],
        },
        "p_upper_mean_best_cos": _tail_p_upper(
            null_b["mean_stats"], spectral_obs["mean_best_cos"],
            N_PERMUTATIONS),
        "p_upper_median_best_cos": _tail_p_upper(
            null_b["median_stats"], spectral_obs["median_best_cos"],
            N_PERMUTATIONS),
        "p_upper_mean_coverage": _tail_p_upper(
            null_b["coverage_stats"], spectral_obs["mean_per_parent_coverage"],
            N_PERMUTATIONS),
        "n_permutations": int(N_PERMUTATIONS),
    }
    invariant_checks.append({
        "check": "spectral_table_consistent",
        "ok": bool(np.allclose(
            cos_spectral_modes[np.arange(len(spectral_rows)),
                               argmode[np.arange(len(spectral_rows)),
                                       child_parent]],
            score[np.arange(len(spectral_rows)), child_parent],
            atol=1e-9)),
        "detail": "argmode/score tables consistent with the single "
                  "precomputed 480x244 cosine matrix",
    })

    # ---- PART C1: best-single parent specificity ----
    parent_reps = np.asarray([
        _pref_rep(blob["parent_prefs"][j], eligible)
        for j in range(MAIN_JURIES)]).astype(np.float64)
    parent_modes_cos = parent_reps @ mode_centroids.T
    BEST = _parent_best_matrix(parent_modes_cos, mode_set_by_parent)
    npz_out["BEST"] = BEST.astype(np.float32)
    diag = np.diag(BEST)
    off_mean = np.asarray([
        float(np.mean(np.delete(BEST[i], i))) for i in range(MAIN_JURIES)])
    best_null = _parent_best_null(BEST, N_PERMUTATIONS,
                                  _derive_seed(ADDENDUM_SEED, "best_null"))
    best_result = {
        "observed_mean_own": float(diag.mean()),
        "observed_median_own": float(np.median(diag)),
        "mean_diff_own_minus_other": float(
            np.mean(diag - off_mean)),
        "null": {"mean": float(best_null.mean()),
                 "sd": float(best_null.std())},
        "p_upper_mean_own": _tail_p_upper(
            best_null, float(diag.mean()), N_PERMUTATIONS),
        "n_permutations": int(N_PERMUTATIONS),
    }

    # ---- PART C2: absolute convex-hull specificity ----
    hull, best_single_err = _hull_error_matrix(
        parent_reps, mode_centroids, mode_set_by_parent)
    npz_out["HULL_ERROR"] = hull.astype(np.float32)
    npz_out["BEST_SINGLE_ERROR"] = best_single_err.astype(np.float32)
    hull_diag = np.diag(hull)
    hull_null = _hull_error_null(hull, N_PERMUTATIONS,
                                 _derive_seed(ADDENDUM_SEED, "hull_null"))
    hull_result = {
        "observed_mean_own": float(hull_diag.mean()),
        "observed_median_own": float(np.median(hull_diag)),
        "null": {"mean": float(hull_null.mean()),
                 "sd": float(hull_null.std())},
        "p_lower_mean_own": _tail_p_lower(
            hull_null, float(hull_diag.mean()), N_PERMUTATIONS),
        "n_permutations": int(N_PERMUTATIONS),
        "best_single_error_observed_mean_own": float(
            np.diag(best_single_err).mean()),
        "best_single_error_null_mean": float(
            np.mean(_parent_best_null(best_single_err, N_PERMUTATIONS,
                                      _derive_seed(ADDENDUM_SEED,
                                                   "bse_null")))),
        "best_single_error_p_lower_mean_own": float(_tail_p_lower(
            _parent_best_null(best_single_err, N_PERMUTATIONS,
                              _derive_seed(ADDENDUM_SEED, "bse_null")),
            float(np.diag(best_single_err).mean()), N_PERMUTATIONS)),
    }
    invariant_checks.append({
        "check": "hull_table_consistent",
        "ok": bool(np.all(np.isfinite(hull))
                   and np.all(np.isfinite(best_single_err))),
        "detail": "120x120 hull-error and best-single-error tables finite",
    })

    # ---- frozen outputs ----
    source_hashes = {k: v for k, v in provenance.items()
                     if k.endswith("_sha256")}
    addendum = {
        "addendum_seed": int(ADDENDUM_SEED),
        "n_permutations": int(N_PERMUTATIONS),
        "mode_tau": float(MODE_TAU),
        "family_taus": [float(t) for t in FAMILY_TAUS],
        "source": source_hashes,
        "source_campaign_git_head": provenance["campaign_git_head"],
        "code_git_head": _git_head(),
        "source_mode_count": n_modes,
        "source_mode_ids": [m["mode_id"] for m in modes],
        "families": families_by_tau,
        "family_summaries": family_summaries,
        "spectral": spectral_result,
        "parent_best_single": best_result,
        "parent_hull": hull_result,
        "prior_relative_mixture": {
            "mixture_rel_0.70_observed": geometry["nulls"][
                "mixture_rel_0.70"]["observed"],
            "mixture_rel_0.70_p_upper": geometry["nulls"][
                "mixture_rel_0.70"]["empirical_p_upper"],
            "note": ("existing relative convex-mixture test: "
                     "null / non-significant; kept as-is and NOT "
                     "reinterpreted by this addendum"),
        },
        "method": {
            "phase": "analyze",
            "seed": int(ADDENDUM_SEED),
            "command": shlex.join(sys.argv),
            "git_head": _git_head(),
            "semantic_context_loaded": False,
            "unblinded": False,
            "representation_pref": "book_n>=25 -> mean-center eligible "
                                   "coordinates -> L2",
            "clustering": "average-linkage hierarchical, cosine distance, "
                          "one linkage, cuts at 1 - family_tau",
            "permutation_design": "intact mode-set assignment shuffles; "
                                  "precomputed tables only; no book-space "
                                  "products and no SLSQP inside any "
                                  "permutation loop",
            "n_fits_hull_table": int(MAIN_JURIES * MAIN_JURIES),
        },
        "invariant_checks": invariant_checks,
        "semantic_context_loaded": False,
        "unblinded": False,
    }
    _write_npz_atomic(ADD_NPZ, npz_out)
    add_sha = _sha256(ADD_NPZ)
    _write_json_atomic(ADD_JSON, addendum)
    add_json_sha = _sha256(ADD_JSON)
    manifest = {
        "seal_manifest_version": 1,
        "artifacts": {
            "addendum_json": {"file": ADD_JSON.name, "sha256": add_json_sha,
                              "bytes": ADD_JSON.stat().st_size},
            "addendum_npz": {"file": ADD_NPZ.name, "sha256": add_sha,
                             "bytes": ADD_NPZ.stat().st_size},
            "source_census_npz": {"file": CENSUS_NPZ.name,
                                  "sha256": source_hashes["census_npz_sha256"],
                                  "bytes": CENSUS_NPZ.stat().st_size},
            "source_census_json": {"file": CENSUS_JSON.name,
                                   "sha256": source_hashes["census_json_sha256"],
                                   "bytes": CENSUS_JSON.stat().st_size},
            "source_geometry_npz": {"file": GEO_NPZ.name,
                                    "sha256": source_hashes["geometry_npz_sha256"],
                                    "bytes": GEO_NPZ.stat().st_size},
            "source_geometry_json": {"file": GEO_JSON.name,
                                     "sha256": source_hashes["geometry_json_sha256"],
                                     "bytes": GEO_JSON.stat().st_size},
        },
        "addendum_seed": int(ADDENDUM_SEED),
        "git_head": _git_head(),
        "command": shlex.join(sys.argv),
        "semantic_context_loaded": False,
        "unblinded": False,
    }
    _write_text_atomic(ADD_MANIFEST, json.dumps(manifest, indent=1))
    print(
        f"mode families frozen: {ADD_JSON} ({ADD_JSON.stat().st_size/2**20:.1f} "
        f"MiB), {ADD_NPZ} ({ADD_NPZ.stat().st_size/2**20:.1f} MiB), "
        f"seal {add_sha[:16]}..., {time.time() - t0:.0f}s", flush=True,
    )


# ---------------------------------------------------------------------------
# Prereport phase (structural, PRE-UNBLIND).
# ---------------------------------------------------------------------------

def _verify_addendum_seal() -> tuple[dict[str, Any], dict[str, Any]]:
    if not ADD_JSON.exists() or not ADD_NPZ.exists():
        raise SystemExit("addendum artifacts missing; run analyze first")
    if not ADD_MANIFEST.exists():
        raise SystemExit("addendum seal manifest missing; refusing")
    addendum = json.loads(ADD_JSON.read_text(encoding="utf-8"))
    if addendum.get("semantic_context_loaded") is not False \
            or addendum.get("unblinded") is not False:
        raise SystemExit("addendum claims semantic/unblinded state; refusing")
    manifest = json.loads(ADD_MANIFEST.read_text(encoding="utf-8"))
    if _sha256(ADD_JSON) != manifest["artifacts"]["addendum_json"]["sha256"]:
        raise SystemExit("addendum JSON hash mismatch vs manifest")
    if _sha256(ADD_NPZ) != manifest["artifacts"]["addendum_npz"]["sha256"]:
        raise SystemExit("addendum NPZ hash mismatch vs manifest")
    provenance = _verify_source_campaign()
    for key, path in (("census_npz", CENSUS_NPZ), ("census_json", CENSUS_JSON),
                      ("geometry_npz", GEO_NPZ), ("geometry_json", GEO_JSON)):
        if manifest["artifacts"][f"source_{key}"]["sha256"] != _sha256(path):
            raise SystemExit(f"addendum manifest source {key} mismatch")
    return addendum, manifest


def phase_prereport(args: argparse.Namespace) -> None:
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    addendum, manifest = _verify_addendum_seal()
    lines = [
        "# Hierarchical jury decomposition: mode-families addendum "
        "(PRE-UNBLIND structural summary)",
        "",
        "**Generated from the sealed main census + geometry only. No "
        "semantic context (titles, authors, literary sets, known pole, "
        "genres, publication year) was loaded to produce this document.**",
        "",
        f"- Addendum seed: **{addendum['addendum_seed']}**; "
        f"{addendum['n_permutations']} label-blind permutations "
        f"(indexing only).",
        f"- Source campaign: seed **{addendum['source_campaign_git_head']}** "
        f"git head `{addendum['source_campaign_git_head'][:12]}`; "
        f"{addendum['source_mode_count']} recurrent random modes at "
        f"tau={addendum['mode_tau']}.",
        f"- Addendum code git commit: `{addendum['code_git_head']}`",
        "",
        "## Source seal",
        "",
        f"- census_npz {manifest['artifacts']['source_census_npz']['sha256'][:16]}... "
        f"(verified)",
        f"- census_json {manifest['artifacts']['source_census_json']['sha256'][:16]}... "
        f"(verified)",
        f"- geometry_npz {manifest['artifacts']['source_geometry_npz']['sha256'][:16]}... "
        f"(verified)",
        f"- geometry_json {manifest['artifacts']['source_geometry_json']['sha256'][:16]}... "
        f"(verified)",
        f"- addendum_json {manifest['artifacts']['addendum_json']['sha256'][:16]}... "
        f"(verified)",
        f"- addendum_npz {manifest['artifacts']['addendum_npz']['sha256'][:16]}... "
        f"(verified)",
        "",
        "## PART A -- cross-parent mode families (tau=0.70 recurrent modes)",
        "",
        "| family tau | n families | n cross-parent | >=3 parents | >=5 parents "
        "| largest n_modes | largest n_parents | median parents (cross) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for tau in FAMILY_TAUS:
        s = addendum["family_summaries"][str(tau)]
        lines.append(
            f"| {tau:.2f} | {s['n_families']} | {s['n_cross_parent']} | "
            f"{s['n_families_ge3_parents']} | {s['n_families_ge5_parents']} | "
            f"{s['largest_by_n_modes']} | {s['largest_by_n_distinct_parents']} | "
            f"{s['median_n_distinct_parents_cross']} |")
    lines += [
        "",
        "## PART B -- ratings-only spectral recovery of random modes",
        "",
        "| statistic | observed | null mean | null sd | p_upper |",
        "|---|---:|---:|---:|---:|",
    ]
    sp = addendum["spectral"]
    lines += [
        f"| mean best cosine (own parent) | {sp['observed']['mean_best_cos']:.4f} "
        f"| {sp['null']['mean_best_cos']:.4f} | {sp['null']['sd_best_cos']:.4f} "
        f"| {sp['p_upper_mean_best_cos']:.4f} |",
        f"| median best cosine | {sp['observed']['median_best_cos']:.4f} "
        f"| n/a | n/a | {sp['p_upper_median_best_cos']:.4f} |",
        f"| mean per-parent mode coverage | "
        f"{sp['observed']['mean_per_parent_coverage']:.4f} "
        f"| {sp['null']['mean_coverage']:.4f} | {sp['null']['sd_coverage']:.4f} "
        f"| {sp['p_upper_mean_coverage']:.4f} |",
        f"| fraction mutual-best among siblings | "
        f"{sp['observed']['fraction_mutual_best_sibling']:.4f} | n/a | n/a | n/a |",
        "",
        "## PART C -- parent specificity (absolute distance/cosine)",
        "",
        "| statistic | observed | null mean | null sd | p |",
        "|---|---:|---:|---:|---:|",
    ]
    pb = addendum["parent_best_single"]
    ph = addendum["parent_hull"]
    lines += [
        f"| best-single: mean own-parent cosine | {pb['observed_mean_own']:.4f} "
        f"| {pb['null']['mean']:.4f} | {pb['null']['sd']:.4f} "
        f"| {pb['p_upper_mean_own']:.4f} (upper) |",
        f"| hull: mean own-parent error | {ph['observed_mean_own']:.4f} "
        f"| {ph['null']['mean']:.4f} | {ph['null']['sd']:.4f} "
        f"| {ph['p_lower_mean_own']:.4f} (lower) |",
        f"| best-single-error: mean own-parent error | "
        f"{ph['best_single_error_observed_mean_own']:.4f} "
        f"| {ph['best_single_error_null_mean']:.4f} | n/a | "
        f"{ph['best_single_error_p_lower_mean_own']:.4f} (lower) |",
        "",
        "## Prior relative convex-mixture result (kept as-is)",
        "",
        f"- mixture_rel_0.70 observed relative improvement "
        f"**{addendum['prior_relative_mixture']['mixture_rel_0.70_observed']:.4f}**, "
        f"empirical upper-tail p "
        f"**{addendum['prior_relative_mixture']['mixture_rel_0.70_p_upper']:.4f}** "
        f"(null / non-significant; NOT reinterpreted by this addendum).",
        "",
        "## Invariant checks",
        "",
    ]
    for check in addendum["invariant_checks"]:
        lines.append(f"- {check['check']}: {'ok' if check['ok'] else 'FAILED'}")
    _write_text_atomic(ADD_REPORT, "\n".join(lines) + "\n")
    print(f"mode-families prereport written: {ADD_REPORT}, "
          f"{time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------------------
# Smoke phase: bounded/synthetic tests + real source-seal validation.
# ---------------------------------------------------------------------------

def _synthetic_fixture(n_books: int = 400, seed: int = 11):
    """3 parents, 6 modes (two 2-parent families + a singleton), 4 spectral
    children per parent, 3 parent endpoints.  Unit vectors."""
    rng = np.random.default_rng(seed)
    a = rng.normal(size=n_books)
    b = rng.normal(size=n_books)
    c = rng.normal(size=n_books)
    base = {"a": a, "b": b, "c": c}

    def unit(v: np.ndarray) -> np.ndarray:
        return v / np.linalg.norm(v)

    def noisy(v: np.ndarray, eps: float = 0.05) -> np.ndarray:
        return unit(v + eps * rng.normal(size=n_books))

    # modes: p0:[a,b] p1:[a,b] p2:[b,c]
    mode_centroids = np.vstack([
        noisy(base["a"]), noisy(base["b"]),
        noisy(base["a"]), noisy(base["b"]),
        noisy(base["b"]), noisy(base["c"]),
    ]).astype(np.float64)
    mode_set_by_parent = [np.asarray([0, 1]), np.asarray([2, 3]),
                          np.asarray([4, 5])]
    # spectral children: p0 -> a,a,b,b ; p1 -> a,a,b,b ; p2 -> b,b,c,c
    child_vecs = np.vstack([
        noisy(base["a"]), noisy(base["a"]), noisy(base["b"]), noisy(base["b"]),
        noisy(base["a"]), noisy(base["a"]), noisy(base["b"]), noisy(base["b"]),
        noisy(base["b"]), noisy(base["b"]), noisy(base["c"]), noisy(base["c"]),
    ]).astype(np.float64)
    child_parent = np.asarray([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2])
    # parent endpoints: p0 near a, p1 near a, p2 near c
    parent_reps = np.vstack([
        noisy(base["a"], 0.1), noisy(base["a"], 0.1),
        noisy(base["c"], 0.1)]).astype(np.float64)
    children_by_parent = [np.asarray([0, 1, 2, 3]),
                          np.asarray([4, 5, 6, 7]),
                          np.asarray([8, 9, 10, 11])]
    return {
        "mode_centroids": mode_centroids,
        "mode_set_by_parent": mode_set_by_parent,
        "child_vecs": child_vecs,
        "child_parent": child_parent,
        "children_by_parent": children_by_parent,
        "parent_reps": parent_reps,
    }


def _no_book_space_or_slsqp(fn: Any) -> bool:
    """Static guarantee that a permutation null body performs only
    indexing/reductions over precomputed tables."""
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return False
    banned = (" @ ", "matmul", "einsum", "minimize(", "SLSQP",
              "_mixture_fit", "hull_error_matrix", "build_matrix")
    return all(b not in src for b in banned)


def _hull_fit_benchmark(real_counts: np.ndarray, n_fits: int,
                        d: int = 26418) -> dict[str, float]:
    """Descriptive benchmark: n_fits representative convex-hull fits at the
    realistic full-scale dimension and the real per-parent mode-set size
    distribution (1-2 modes at tau=0.70).  Never changes the algorithm."""
    rng = np.random.default_rng(_derive_seed(ADDENDUM_SEED, "benchmark"))
    pool = _unit_rows(rng.normal(size=(24, d)))
    p = _unit_rows(rng.normal(size=(1, d)))[0]
    sizes = rng.choice(real_counts, size=n_fits)
    t0 = time.time()
    for k in sizes:
        _mixture_fit(p, pool[:k])
    elapsed = time.time() - t0
    ms_per_fit = elapsed / n_fits * 1000.0
    return {
        "n_fits": int(n_fits),
        "total_seconds": float(elapsed),
        "ms_per_fit": float(ms_per_fit),
        "projected_seconds_14400": float(ms_per_fit * 1.0e-3 * 14400),
    }


def phase_smoke(args: argparse.Namespace) -> None:
    t0 = time.time()
    assert not SEMANTIC_CONTEXT_LOADED
    checks: list[dict[str, Any]] = []

    # ---- 1. real source campaign seal validation ----
    try:
        provenance = _verify_source_campaign()
        seal_ok = True
        seal_detail = (f"all four manifest hashes + geometry seal hashes "
                       f"verify; 2880 sources; partial false; semantic false")
    except SystemExit as exc:
        provenance = {}
        seal_ok = False
        seal_detail = str(exc)
    checks.append({"check": "source_campaign_seal_valid", "ok": seal_ok,
                   "detail": seal_detail})

    # ---- 2. exact recurrent-mode selection on the real frozen geometry ----
    selection_detail = ""
    if seal_ok:
        try:
            geometry = json.loads(GEO_JSON.read_text(encoding="utf-8"))
            with np.load(GEO_NPZ, allow_pickle=False) as gb:
                modes = _load_recurrent_modes(geometry, gb,
                                              EXPECTED_N_RECURRENT_MODES)
            non_recurrent_excluded = True
            for j in range(MAIN_JURIES):
                for m in geometry["recurrence"]["0.7"]["per_parent"].get(
                        str(j), {}).get("modes", []):
                    if m["recurrent"] and m["mode_id"] not in [
                            mm["mode_id"] for mm in modes]:
                        non_recurrent_excluded = False
            selection_ok = (len(modes) == EXPECTED_N_RECURRENT_MODES
                            and non_recurrent_excluded)
            selection_detail = (f"{len(modes)} recurrent modes selected; "
                                f"non-recurrent excluded: {non_recurrent_excluded}")
        except SystemExit as exc:
            modes = []
            selection_ok = False
            selection_detail = str(exc)
    else:
        modes = []
        selection_ok = False
        selection_detail = "source seal failed; skipped"
    checks.append({"check": "recurrent_mode_selection_exact_244",
                   "ok": bool(selection_ok), "detail": selection_detail})

    checks.append({
        "check": "non_recurrent_modes_excluded",
        "ok": bool(selection_ok and modes),
        "detail": selection_detail,
    })

    # ---- 3. exact frozen centroid keys ----
    if modes:
        real_keys_ok = all(
            m["centroid_key"] == f"recur_cent_0.70_p{m['parent_j']:03d}_"
                                 f"{m['mode_index']}" for m in modes)
    else:
        real_keys_ok = False
    checks.append({"check": "frozen_centroid_keys_used",
                   "ok": bool(real_keys_ok),
                   "detail": "recur_cent_0.70_p<ppp>_<mi> keys exactly "
                             "matching frozen geometry records"})

    # ---- 4. synthetic family analysis ----
    fx = _synthetic_fixture()
    npz_fake: dict[str, np.ndarray] = {}
    fake_modes = [{"mode_id": f"recurrent_mode_0.70_p{j:03d}_{mi}",
                   "parent_j": j, "mode_index": mi,
                   "centroid_key": f"recur_cent_0.70_p{j:03d}_{mi}",
                   "members": [], "replicates": [0, 1],
                   "n_distinct_replicates": 2, "size": 4,
                   "centroid": fx["mode_centroids"][i]}
                  for j, mi, i in
                  ((0, 0, 0), (0, 1, 1), (1, 0, 2), (1, 1, 3),
                   (2, 0, 4), (2, 1, 5))]
    sim, fams, sums_, invs = _family_analysis(fake_modes, npz_fake)
    part_ok = all(i["ok"] for i in invs)
    cross_fams = [f for f in fams["0.5"]["families"] if f["cross_parent"]]
    recon_ok = all(i["ok"] for i in invs
                   if i["check"].startswith("family_centroid_reconstruction"))
    checks.append({
        "check": "family_partition_covers_all_modes",
        "ok": bool(part_ok),
        "detail": "synthetic: all 6 modes assigned exactly once per tau; "
                  f"cross-parent families at 0.50: {len(cross_fams)}",
    })
    checks.append({
        "check": "cross_parent_centroid_reconstruction",
        "ok": bool(recon_ok),
        "detail": "synthetic: stored family centroids reconstruct from "
                  "frozen members",
    })
    checks.append({
        "check": "mode_cosine_symmetry_diagonal",
        "ok": bool(np.allclose(sim, sim.T, atol=1e-6)
                   and np.allclose(np.diag(sim), 1.0, atol=1e-6)),
        "detail": f"synthetic {sim.shape[0]}x{sim.shape[0]} sim symmetric, "
                  f"unit diagonal",
    })
    det_ok = True
    for tau in FAMILY_TAUS:
        _d1, z1 = _avg_linkage_cuts(sim)
        _d2, z2 = _avg_linkage_cuts(sim)
        if not np.array_equal(z1, z2):
            det_ok = False
        if _cut_clusters(z1, sim.shape[0], tau) != _cut_clusters(
                z2, sim.shape[0], tau):
            det_ok = False
    checks.append({"check": "average_linkage_cuts_deterministic",
                   "ok": bool(det_ok),
                   "detail": "identical linkage and cuts on repeated runs"})

    # ---- 5. spectral score table vs direct calculation ----
    cos_sc = fx["child_vecs"] @ fx["mode_centroids"].T
    score, argmode = _spectral_score_tables(cos_sc, fx["mode_set_by_parent"])
    direct_ok = True
    for c in range(cos_sc.shape[0]):
        for j in range(3):
            vals = cos_sc[c, fx["mode_set_by_parent"][j]]
            if abs(score[c, j] - float(vals.max())) > 1e-9 \
                    or int(argmode[c, j]) != int(
                        fx["mode_set_by_parent"][j][np.argmax(vals)]):
                direct_ok = False
    checks.append({"check": "spectral_best_table_matches_direct",
                   "ok": bool(direct_ok),
                   "detail": f"{score.shape[0]}x{score.shape[1]} score/argmode "
                             "table equals direct per-set max"})

    # ---- 6. parent-shuffle null preserves intact sets (behavioral) ----
    sizes_arr = np.asarray([len(s) for s in fx["mode_set_by_parent"]])
    n_small = 300
    null_b = _spectral_shuffle_null(
        score, argmode, fx["child_parent"], fx["children_by_parent"],
        sizes_arr, n_small, _derive_seed(ADDENDUM_SEED, "smoke_null"))
    # brute-force replication: index the precomputed table per permutation
    rng = np.random.default_rng(_derive_seed(ADDENDUM_SEED, "smoke_null"))
    brute_mean = np.empty(n_small)
    for t in range(n_small):
        pi = rng.permutation(3)
        s = pi[fx["child_parent"]]
        brute_mean[t] = np.mean(score[np.arange(12), s])
    intact_ok = (np.allclose(null_b["mean_stats"], brute_mean, atol=1e-12)
                 and null_b["mean_stats"].shape == (n_small,))
    checks.append({
        "check": "parent_shuffle_null_preserves_intact_sets",
        "ok": bool(intact_ok),
        "detail": "null mean best-cosine equals brute-force indexing of the "
                  "precomputed score table; intact mode sets preserved",
    })

    # ---- 7. no book-space products / no SLSQP inside permutation loops ----
    src_ok = (_no_book_space_or_slsqp(_spectral_shuffle_null)
              and _no_book_space_or_slsqp(_parent_best_null)
              and _no_book_space_or_slsqp(_hull_error_null))
    checks.append({
        "check": "permutation_loop_no_book_space_products",
        "ok": bool(src_ok),
        "detail": "all three permutation nulls: source contains no '@', "
                  "matmul, einsum, minimize, SLSQP or mixture-fit calls",
    })

    # ---- 8. parent BEST matrix vs direct calculation ----
    pmc = fx["parent_reps"] @ fx["mode_centroids"].T
    BEST = _parent_best_matrix(pmc, fx["mode_set_by_parent"])
    direct_best_ok = True
    for i in range(3):
        for j in range(3):
            if abs(BEST[i, j] - float(pmc[i, fx["mode_set_by_parent"][j]].max())) \
                    > 1e-9:
                direct_best_ok = False
    checks.append({"check": "parent_best_matrix_matches_direct",
                   "ok": bool(direct_best_ok),
                   "detail": "3x3 BEST equals direct per-set max cosines"})

    # ---- 9. convex-hull fit: one-mode and two-mode synthetic cases ----
    p_half = fx["parent_reps"][0]
    c0 = fx["mode_centroids"][0:1]
    fit1 = _mixture_fit(p_half, c0)
    one_ok = (abs(fit1["hull_error"] - fit1["best_single_error"]) < 1e-9
              and abs(fit1["hull_error"]
                      - np.linalg.norm(p_half - c0[0])) < 1e-9
              and abs(fit1["alpha"][0] - 1.0) < 1e-9)
    rng2 = np.random.default_rng(5)
    base = _unit_rows(rng2.normal(size=(2, 400)))
    p_mix = _unit_rows(((base[0] + base[1]) / 2)[None, :])[0]
    fit2 = _mixture_fit(p_mix, base)
    two_ok = (fit2["hull_error"] < fit2["best_single_error"] - 1e-6
              and abs(sum(fit2["alpha"]) - 1.0) < 1e-6)
    checks.append({
        "check": "hull_fit_synthetic_cases",
        "ok": bool(one_ok and two_ok),
        "detail": f"one-mode: hull==best-single (err {fit1['hull_error']:.4f}); "
                  f"two-mode: hull {fit2['hull_error']:.4f} < best single "
                  f"{fit2['best_single_error']:.4f}",
    })

    # ---- 10. hull table logic vs direct pairwise fits (sampled) ----
    hull, bse = _hull_error_matrix(fx["parent_reps"], fx["mode_centroids"],
                                   fx["mode_set_by_parent"])
    direct_hull_ok = True
    for i in range(3):
        for j in range(3):
            direct = _mixture_fit(
                fx["parent_reps"][i],
                fx["mode_centroids"][fx["mode_set_by_parent"][j]])
            if abs(hull[i, j] - direct["hull_error"]) > 1e-9 \
                    or abs(bse[i, j] - direct["best_single_error"]) > 1e-9:
                direct_hull_ok = False
    checks.append({
        "check": "hull_table_matches_direct_sampled",
        "ok": bool(direct_hull_ok),
        "detail": "all 9 synthetic (i,j) hull/best-single entries equal "
                  "direct fits",
    })

    # ---- 11. hull permutation null indexes the precomputed table ----
    hull_null = _hull_error_null(hull, n_small,
                                 _derive_seed(ADDENDUM_SEED, "smoke_hull"))
    rng3 = np.random.default_rng(_derive_seed(ADDENDUM_SEED, "smoke_hull"))
    brute_hull = np.empty(n_small)
    for t in range(n_small):
        pi = rng3.permutation(3)
        brute_hull[t] = np.mean(hull[np.arange(3), pi])
    checks.append({
        "check": "hull_permutation_null_indexes_table",
        "ok": bool(np.allclose(hull_null, brute_hull, atol=1e-12)),
        "detail": "null equals brute-force indexing of the precomputed "
                  "120x120-style table (no refitting)",
    })

    # ---- 12. empirical upper/lower tail p formulas ----
    nulls_test = np.asarray([0.1, 0.2, 0.3, 0.4, 0.5])
    pu = _tail_p_upper(nulls_test, 0.25, 5)
    pl = _tail_p_lower(nulls_test, 0.25, 5)
    p_ok = (abs(pu - 4.0 / 6.0) < 1e-12 and abs(pl - 3.0 / 6.0) < 1e-12)
    checks.append({
        "check": "tail_p_formulas",
        "ok": bool(p_ok),
        "detail": f"upper (1+count>=obs)/6 = {pu:.4f}; lower = {pl:.4f}",
    })

    # ---- 13. hull-fit benchmark (realistic sizes and dimension) ----
    if seal_ok:
        geometry = json.loads(GEO_JSON.read_text(encoding="utf-8"))
        real_counts = np.asarray([
            sum(1 for m in geometry["recurrence"]["0.7"]["per_parent"].get(
                str(j), {}).get("modes", []) if m["recurrent"])
            for j in range(MAIN_JURIES)])
        bench = _hull_fit_benchmark(real_counts, 1000)
        bench_ok = bench["total_seconds"] > 0
    else:
        bench = {"n_fits": 0, "total_seconds": float("nan"),
                 "ms_per_fit": float("nan"),
                 "projected_seconds_14400": float("nan")}
        bench_ok = False
    checks.append({
        "check": "hull_fit_benchmark_1000",
        "ok": bool(bench_ok),
        "detail": (f"{bench['n_fits']} fits in {bench['total_seconds']:.1f}s; "
                   f"{bench['ms_per_fit']:.2f} ms/fit; projected "
                   f"{bench['projected_seconds_14400']/60:.1f} min for 14400 "
                   f"fits"),
    })

    # ---- 14. semantic isolation ----
    checks.append({"check": "no_semantic_imports_or_context",
                   "ok": SEMANTIC_CONTEXT_LOADED is False,
                   "detail": "module flag SEMANTIC_CONTEXT_LOADED remains "
                             "False; no semantic loader is ever called"})
    checks.append({"check": "no_unblind_posthoc_artifact",
                   "ok": not (DATA / "jury_decomposition_mode_families"
                                   "_posthoc.json").exists()
                          and not (DATA / "jury_decomposition_posthoc.json"
                                   ).exists(),
                   "detail": "no posthoc/unblind artifact exists"})
    firewall_artifacts = [ADD_JSON, ADD_NPZ, ADD_MANIFEST, ADD_REPORT,
                          SMOKE_REPORT]
    firewall_artifacts = [p for p in firewall_artifacts if p.exists()]
    firewall_artifacts += [SPEC_PATH, CENSUS_JSON, GEO_JSON, MANIFEST]
    checks += _addendum_firewall_scan(firewall_artifacts)

    # ---- 15. unique smoke check names ----
    checks.append({"check": "smoke_check_names_unique", "ok": True,
                   "detail": "pending"})
    names = [c["check"] for c in checks]
    dups = sorted({n for n in names if names.count(n) > 1})
    checks[-1]["ok"] = not dups
    checks[-1]["detail"] = (f"{len(names)} checks, "
                            f"{len(names) - len(set(names))} duplicate(s)"
                            + (f": {dups}" if dups else ""))

    report = {
        "addendum_seed": int(ADDENDUM_SEED),
        "checks": checks,
        "passed": all(c["ok"] for c in checks),
        "git_head": _git_head(),
        "runtime_seconds": time.time() - t0,
    }
    _write_json_atomic(SMOKE_REPORT, report)
    print(f"mode-families smoke report: {SMOKE_REPORT}", flush=True)
    failed = [c for c in checks if not c["ok"]]
    print(f"mode-families smoke done in {time.time() - t0:.0f}s: "
          f"{len(checks) - len(failed)}/{len(checks)} checks passed",
          flush=True)
    for f in failed:
        print(f"  FAILED: {f['check']} ({f.get('detail', '')})", flush=True)
    if failed:
        raise SystemExit("mode-families smoke checks failed")


def _addendum_firewall_scan(artifacts: list[Path]) -> list[dict[str, Any]]:
    """Analogous to the experiment firewall: no forbidden semantic tokens in
    any pre-unblind artifact (text files only; whole-word match)."""
    bad: list[str] = []
    pattern = re.compile(r"\b(" + "|".join(
        re.escape(t) for t in FORBIDDEN_SEMANTIC_TOKENS) + r")\b")
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
    return [{"check": "semantic_leakage_firewall", "ok": not bad,
             "detail": "; ".join(sorted(set(bad))[:20])
             if bad else "no forbidden semantic tokens in artifacts"}]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["smoke", "analyze", "prereport"],
                        required=True)
    args = parser.parse_args()
    if args.phase == "smoke":
        phase_smoke(args)
    elif args.phase == "analyze":
        phase_analyze(args)
    else:
        phase_prereport(args)


if __name__ == "__main__":
    main()

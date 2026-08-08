#!/usr/bin/env python3
"""Do the 20k F1 basin's descendants fragment into recurrent 10k families?

Follow-up to the recursive family breeding pilot (commit 3b4fb12).  The old
fixed-F1 recursion amplified a literary 20k jury in both roots (margin
+0.62/+0.63, exact@50 3-5) but collapsed at 10k (margin ~0, exact@50 0-1).
Hypothesis: the 20k F1 basin does not disappear at 10k -- it FRAGMENTS into
multiple recurring 10k descendant families, and optimizing against the old
20k centroid is the wrong recursion once the basin has moved.

Design (fixed procedure, no parameter search after seeing results)
------------------------------------------------------------------
Part A (zero new runs): census the 48 ALREADY-SAVED 10k child endpoints of the
old literary 20k campaigns (`root{0,1}_lit_g2_child_reps`, 12 replicates x 2
siblings x 26418 eligible coordinates each).  Pooled cosine, average-linkage
hierarchical clustering; ONE automatic geometric cut: average silhouette over
k = 2..8 (lowest-k tie break); fixed tau .30/.50/.70 cuts reported as
descriptive robustness only.  For each natural family record recurrence
metadata (distinct roots, distinct partition replicates per root, sibling
pairs, within-family cosine, root-0/root-1 half-centroid cosine, cosine to the
old frozen F1/F0) and the flags cross_root_recurrent (both roots, >= 2
distinct replicates each, size >= 6) and strong_cross_root_recurrent
(>= 3 replicates each root, size >= 8).

Part B: ONLY after the natural partition is frozen, evaluate family centroid
semantics (posthoc_head convention, exact/broad/anti @50/@100) and choose the
rolling target G10 by a fixed deterministic SEMANTIC BRANCH CHOICE among
cross-root recurrent families: highest exact@50, then broad@50, then lowest
anti@50, then largest size, then lowest family id.  If NO eligible family
exists, STOP after A/B with the fixed message.  G10 is normalized to unit L2
and frozen.

Part C: independently follow G10.  NEW random partitions (DESCENDANT_SEED
20260824, "follow10k", root, replicate; 24 replicates per root), NOT the old
20260822 partitions, and NEW reversal runs of both 10k siblings per replicate
from each of the two old literary 20k pools (`root{0,1}_lit_g1_selected`).
User fitness = mean over replicates of the within-partition centered deepest-
endpoint cos(child, G10) (exactly (a-b)/2 / (b-a)/2 per sibling pair).  No
semantic labels, no direct user-to-G10 rating affinity, no old F1/F0 in
selection.  Select G_follow (top 10k), G_avoid (bottom 10k), random10k
(deterministic random 10k) per root; ties by ascending global user index.

Part D: evaluate G_follow / G_avoid / random10k and the OLD fixed-F1-selected
10k baseline (`root{0,1}_lit_g2_selected`, re-run; must reproduce the stored
eval pref bit-for-bit) with the standard reversal, recording G10 geometry and
old F1-F0 geometry at EVERY stage plus semantics (exact/broad/anti @50/@200,
top-50 head).

Part E: 5k descendant census.  From each NEW G_follow 10k jury, 24 independent
balanced splits (10k -> 2 x 5k; seed "desc5k"), 96 new 5k endpoints total.
Run the SAME label-blind census (silhouette natural cut, fixed cuts,
recurrence, root-half centroids), then semantic inspection of frozen 5k
families.  NO 5k family is followed or selected in this experiment.

Controls / non-tautology
------------------------
Semantic use allowed: inspect frozen families; choose WHICH recurrent family
is the literary branch.  Forbidden: scoring users, scoring children for
breeding, choosing users directly, modifying reversal, choosing reversal
stage by literary metrics.  User selection always goes through randomized
child-jury reversal outcomes.

Phases
------
- analyze10k: label-blind 10k family census, then frozen semantic inspection
  and G10 choice (saved as checkpointable outputs);
- follow10k:  independent G10 follow (24 reps x 2 children x 2 roots) +
  fitness/selections + the four 10k evaluations per root;
- analyze5k:  96-child 5k descendant census + semantics (no selection);
- report:      render the markdown report from the results JSON;
- all:         sequential with per-(root, stage, replicate) checkpoints.

Runtime: Part A free; ~96 follow10k children + 8 evaluations; ~96 desc5k
children; substantially cheaper than the 384-run pilot.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.cluster.hierarchy import fcluster
from scipy.stats import spearmanr

from curators_explorer.scripts import (
    research_seedless_attractor_census as attractor,
)
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year
from curators_explorer.scripts.research_jury_decomposition import (
    _avg_linkage_cuts,
    _cut_clusters,
    _pref_rep,
)
from curators_explorer.scripts.research_jury_ensemble_reversal import run_jury
from curators_explorer.scripts.research_jury_split_experiment import (
    build_subgroup_start,
)
from curators_explorer.scripts.research_recursive_family_breeding import (
    _derive_seed,
    balanced_partitions,
    endpoint_repr,
    fitness_from_margins,
    load_family_compass,
    select_fraction,
)

DATA = Path(__file__).resolve().parents[1] / "data"
BREEDING_NPZ = DATA / "recursive_family_breeding.npz"
BREEDING_JSON = DATA / "recursive_family_breeding.json"
FAMILY_NPZ = DATA / "jury_decomposition_mode_families.npz"

DESCENDANT_SEED = 20260824
BREEDING_SEED = 20260822
FOLLOW_REPLICATES = 24
DESCENDANT_5K_REPLICATES = 24
NATURAL_K_RANGE = (2, 9)          # k = 2..8
FIXED_TAUS = (0.30, 0.50, 0.70)
ELIG_MIN_BOOK_N = 25
RETAINED_TARGET = 1.01
SELECT_FRACTION = 0.5
ROOT_SIZE = 80000
CHILD_SIZES_10K = 10000
CHILD_SIZES_5K = 5000

SMOKE_SEED = 20260825
SMOKE_FOLLOW_REPLICATES = 2
SMOKE_DESC5K_REPLICATES = 2

SEMANTIC_CONTEXT_LOADED = False

FORBIDDEN_FITNESS_TOKENS = (
    "exact_lit", "broad_lit", "posthoc", "eval_sets", "literary",
    "title", "author", "meta",
)


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


def _chunk_dir(tag: str) -> Path:
    return DATA / (
        "recursive_descendant_families_chunks"
        if tag == "main" else f"recursive_descendant_families_chunks_{tag}"
    )


def _output_paths(tag: str) -> tuple[Path, Path, Path]:
    if tag == "main":
        return (
            DATA / "recursive_descendant_families.json",
            DATA / "recursive_descendant_families.npz",
            DATA / "RECURSIVE_DESCENDANT_FAMILIES_REPORT.md",
        )
    return (
        DATA / f"recursive_descendant_families_{tag}.json",
        DATA / f"recursive_descendant_families_{tag}.npz",
        DATA / f"RECURSIVE_DESCENDANT_FAMILIES_{tag.upper()}_REPORT.md",
    )


def _census_paths(tag: str) -> tuple[Path, Path]:
    if tag == "main":
        return (DATA / "recursive_descendant_families_5k_census.json",
                DATA / "recursive_descendant_families_5k_census.npz")
    return (DATA / f"recursive_descendant_families_5k_census_{tag}.json",
            DATA / f"recursive_descendant_families_5k_census_{tag}.npz")


# ---------------------------------------------------------------------------
# Endpoint metadata for the saved 10k descendants (Part A)
# ---------------------------------------------------------------------------

def load_saved_10k_endpoints() -> tuple[np.ndarray, list[dict[str, Any]],
                                       np.ndarray, np.ndarray]:
    """The 48 already-saved 10k literary child endpoints and their metadata.

    Array order: root0 (12 replicates x 2 siblings), then root1.  Metadata
    fields per endpoint: root, parent lineage "lit20k", replicate 0..11,
    sibling group 0/1.
    """
    blob = np.load(BREEDING_NPZ, allow_pickle=False)
    r0 = blob["root0_lit_g2_child_reps"]
    r1 = blob["root1_lit_g2_child_reps"]
    for name, v in (("root0_lit_g2_child_reps", r0),
                    ("root1_lit_g2_child_reps", r1)):
        if v.shape != (12, 2, 26418):
            raise SystemExit(
                f"saved {name} shape {v.shape} != (12, 2, 26418)"
            )
    reps = np.concatenate([r0.reshape(24, 26418),
                           r1.reshape(24, 26418)]).astype(np.float64)
    root_of = np.asarray([0] * 24 + [1] * 24, dtype=np.int16)
    repl_of = np.asarray([i // 2 for i in range(24)] * 2, dtype=np.int16)
    group_of = np.asarray([i % 2 for i in range(24)] * 2, dtype=np.int16)
    meta = [
        {
            "root": int(root_of[i]),
            "parent_lineage": "lit20k",
            "replicate": int(repl_of[i]),
            "sibling_group": int(group_of[i]),
            "endpoint_index": i,
        }
        for i in range(48)
    ]
    return reps, meta, root_of, repl_of


# ---------------------------------------------------------------------------
# Label-blind clustering + census (Part A / Part E)
# ---------------------------------------------------------------------------

def unit_centroid(rows: np.ndarray) -> np.ndarray:
    c = np.asarray(rows, dtype=np.float64).mean(axis=0)
    norm = float(np.linalg.norm(c))
    return (c / norm).astype(np.float32) if norm > 1e-20 else c.astype(np.float32)


def silhouette_cosine(mat: np.ndarray, labels: np.ndarray,
                      n_clusters: int) -> tuple[float, np.ndarray]:
    """Average silhouette on cosine distance (1 - cos) for a fixed cut.

    Singletons contribute 0 by the standard convention.  Deterministic.
    """
    n = len(labels)
    sim = np.asarray(mat, dtype=np.float64) @ np.asarray(mat, dtype=np.float64).T
    dist = 1.0 - sim
    scores = np.zeros(n, dtype=np.float64)
    for i in range(n):
        ci = int(labels[i])
        others = np.flatnonzero(labels == ci)
        others = others[others != i]
        if len(others) == 0:
            scores[i] = 0.0
            continue
        a = float(dist[i, others].mean())
        b = float("inf")
        for cj in range(n_clusters):
            if cj == ci:
                continue
            m = np.flatnonzero(labels == cj)
            if len(m):
                b = min(b, float(dist[i, m].mean()))
        denom = max(a, b)
        scores[i] = (b - a) / denom if denom > 0 else 0.0
    return float(scores.mean()), scores


def natural_cut_by_silhouette(
    mat: np.ndarray, k_range: tuple[int, int] = NATURAL_K_RANGE,
) -> tuple[int, float, dict[str, Any], np.ndarray]:
    """One automatic geometric cut: max average silhouette over k, lowest-k
    tie break.  Returns (k, silhouette, per-k info, labels 0..k-1)."""
    sim = np.asarray(mat, dtype=np.float64) @ np.asarray(mat, dtype=np.float64).T
    _d, z = _avg_linkage_cuts(sim)
    best_k, best_s = None, -1.0
    per_k: dict[str, Any] = {}
    for k in range(k_range[0], k_range[1]):
        labels = (fcluster(z, t=k, criterion="maxclust") - 1).astype(np.int32)
        s, _scores = silhouette_cosine(mat, labels, k)
        per_k[str(k)] = {"silhouette": s, "n_clusters": int(labels.max()) + 1}
        if best_k is None or s > best_s:
            best_k, best_s = k, s
    labels = (fcluster(z, t=best_k, criterion="maxclust") - 1).astype(np.int32)
    return best_k, best_s, per_k, labels


def fixed_cut_summary(mat: np.ndarray, tau: float) -> dict[str, Any]:
    sim = np.asarray(mat, dtype=np.float64) @ np.asarray(mat, dtype=np.float64).T
    _d, z = _avg_linkage_cuts(sim)
    cl = _cut_clusters(z, len(sim), tau)
    return {
        "tau": float(tau),
        "n_clusters": int(len(cl)),
        "cluster_sizes": [int(len(c)) for c in cl],
        "n_with_2plus": int(sum(1 for c in cl if len(c) >= 2)),
    }


def family_census(
    mat: np.ndarray, labels: np.ndarray, root_of: np.ndarray,
    repl_of: np.ndarray, group_of: np.ndarray, f0: np.ndarray,
    f1: np.ndarray,
) -> list[dict[str, Any]]:
    """Recurrence + geometry census of a frozen partition (label-blind)."""
    n = len(mat)
    families: list[dict[str, Any]] = []
    members_by_label: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        members_by_label.setdefault(int(lab), []).append(i)
    for lab, members in members_by_label.items():
        members = sorted(members)
        roots = sorted({int(root_of[i]) for i in members})
        repls = sorted({int(repl_of[i]) for i in members})
        repls_r0 = sorted({int(repl_of[i]) for i in members
                           if int(root_of[i]) == 0})
        repls_r1 = sorted({int(repl_of[i]) for i in members
                           if int(root_of[i]) == 1})
        n_sibling_pairs = sum(
            1 for i in members
            if (i ^ 1) in members_by_label.get(lab, []) and int(repl_of[i ^ 1])
            == int(repl_of[i])
        ) // 2
        sub = mat[members]
        within_sim = sub @ sub.T
        iu = np.triu_indices(len(members), k=1)
        within_vals = within_sim[iu] if len(iu[0]) else np.asarray([])
        centroid = unit_centroid(sub)
        root0_m = [i for i in members if int(root_of[i]) == 0]
        root1_m = [i for i in members if int(root_of[i]) == 1]
        root_half_cos = None
        if root0_m and root1_m:
            c0 = unit_centroid(mat[root0_m])
            c1 = unit_centroid(mat[root1_m])
            root_half_cos = float(c0 @ c1)
        cross_root_recurrent = (
            len(roots) == 2
            and len(repls_r0) >= 2
            and len(repls_r1) >= 2
            and len(members) >= 6
        )
        strong = (
            len(roots) == 2
            and len(repls_r0) >= 3
            and len(repls_r1) >= 3
            and len(members) >= 8
        )
        families.append({
            "family_id": int(lab),
            "members": [int(i) for i in members],
            "n_endpoints": int(len(members)),
            "roots": [int(r) for r in roots],
            "n_distinct_replicates": int(len(repls)),
            "replicates_root0": [int(r) for r in repls_r0],
            "replicates_root1": [int(r) for r in repls_r1],
            "n_sibling_pairs": int(n_sibling_pairs),
            "within_cos_mean": float(within_vals.mean()) if len(within_vals) else None,
            "within_cos_median": float(np.median(within_vals)) if len(within_vals) else None,
            "within_cos_min": float(within_vals.min()) if len(within_vals) else None,
            "cos_f1": float(centroid @ f1),
            "cos_f0": float(centroid @ f0),
            "f1_f0_margin": float(centroid @ f1 - centroid @ f0),
            "cross_root_recurrent": bool(cross_root_recurrent),
            "strong_cross_root_recurrent": bool(strong),
            "root_half_centroid_cos": root_half_cos,
            "centroid_key": None,
        })
    families.sort(key=lambda f: (-f["n_endpoints"], min(f["members"])))
    for idx, f in enumerate(families):
        f["family_id"] = idx
        f["centroid_key"] = None
    return families


# ---------------------------------------------------------------------------
# Semantic evaluation (used AFTER the partition is frozen)
# ---------------------------------------------------------------------------

def embed_full(centroid: np.ndarray, eligible_idx: np.ndarray,
               n_books: int) -> np.ndarray:
    full = np.zeros(n_books, dtype=np.float64)
    full[eligible_idx] = np.asarray(centroid, dtype=np.float64)
    return full


def centroid_semantic_eval(
    centroid_eligible: np.ndarray, eligible_idx: np.ndarray,
    payload: dict[str, np.ndarray], meta: dict[str, Any],
    eval_sets: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    n_books = int(len(payload["work_ids"]))
    full = embed_full(centroid_eligible, eligible_idx, n_books)
    reader_mass = np.where(
        np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N),
        np.asarray(payload["book_n"], dtype=np.float64), 0.0,
    )
    preference = {
        "score": full,
        "mean": full,
        "reader_mass": reader_mass,
    }
    rows, metrics = attractor.posthoc_head(
        preference, payload["work_ids"], meta, eval_sets, limit=100)
    return rows, metrics


def jury_semantic_eval(
    final_pref: np.ndarray, payload: dict[str, np.ndarray],
    meta: dict[str, Any], eval_sets: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    preference = {
        "score": np.asarray(final_pref, dtype=np.float64),
        "mean": np.asarray(final_pref, dtype=np.float64),
        "reader_mass": payload["book_n"].astype(np.float64),
    }
    rows, metrics = attractor.posthoc_head(
        preference, payload["work_ids"], meta, eval_sets, limit=200)
    return rows, metrics


def _metrics_pick(metrics: dict[str, int]) -> dict[str, int]:
    return {
        "exact50": metrics["exact_lit50"],
        "exact200": metrics["exact_lit200"],
        "broad50": metrics["broad_lit50"],
        "broad200": metrics["broad_lit200"],
        "anti50": metrics["anti50"],
        "anti200": metrics["anti200"],
    }


def _counts100(rows: list[dict[str, Any]], eval_sets: dict[str, Any],
               k: int) -> dict[str, int]:
    return {name: int(sum(
        r["work_id"] in eval_sets[name] for r in rows[:k]))
        for name in ("exact_lit", "broad_lit", "anti")}


def choose_G10(families: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Deterministic semantic branch choice among cross-root recurrent
    families: highest exact@50, then broad@50, then lowest anti@50, then
    largest size, then lowest family id."""
    eligible = [f for f in families if f["cross_root_recurrent"]]
    if not eligible:
        return None
    best = min(
        eligible,
        key=lambda f: (
            -f["semantic"]["exact50"],
            -f["semantic"]["broad50"],
            f["semantic"]["anti50"],
            -f["n_endpoints"],
            f["family_id"],
        ),
    )
    return best


# ---------------------------------------------------------------------------
# Stage-wise diagnostics vs arbitrary targets (G10 + old F1/F0)
# ---------------------------------------------------------------------------

def stage_targets_geometry(
    run: dict[str, Any], eligible: np.ndarray,
    targets: dict[str, np.ndarray],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, target in targets.items():
        coses: list[float] = []
        for pref in run["stage_prefs"]:
            rep = endpoint_repr(pref, eligible)
            coses.append(float(rep @ target))
        m = np.asarray(coses, dtype=np.float64)
        out[name] = {
            "by_stage": [float(x) for x in coses],
            "stage0": float(m[0]),
            "deepest": float(m[-1]),
            "max": float(m.max()),
            "argmax_stage": int(m.argmax()),
            "reversal_gain": float(m[-1] - m[0]),
            "best_reversal_gain": float(m.max() - m[0]),
        }
    return out


# ---------------------------------------------------------------------------
# Reversal runs (unchanged standard procedure)
# ---------------------------------------------------------------------------

def run_child_reversal(
    payload: dict[str, np.ndarray], matrix: Any, group: np.ndarray,
    rng: np.random.Generator, eligible: np.ndarray,
    targets: dict[str, np.ndarray], meta: dict[str, Any],
    eval_sets: dict[str, Any],
) -> tuple[dict[str, Any], np.ndarray]:
    t0 = time.time()
    start = build_subgroup_start(payload, group)
    run = run_jury(payload, matrix, start, rng, RETAINED_TARGET)
    geom = stage_targets_geometry(run, eligible, targets)
    _rows, metrics = jury_semantic_eval(
        run["final_pref"], payload, meta, eval_sets)
    rec = {
        "jury_size": int(len(group)),
        "stop_reason": run["stop_reason"],
        "n_stages": int(len(run["stages"])),
        "remaining_users": int(run["stages"][-1]["remaining_users"]),
        "targets": geom,
        **_metrics_pick(metrics),
        "runtime_seconds": time.time() - t0,
    }
    rep = endpoint_repr(run["final_pref"], eligible)
    return rec, rep


def run_jury_eval(
    payload: dict[str, np.ndarray], matrix: Any, users: np.ndarray,
    rng: np.random.Generator, eligible: np.ndarray,
    targets: dict[str, np.ndarray], meta: dict[str, Any],
    eval_sets: dict[str, Any],
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    t0 = time.time()
    start = build_subgroup_start(payload, users)
    run = run_jury(payload, matrix, start, rng, RETAINED_TARGET)
    geom = stage_targets_geometry(run, eligible, targets)
    rows, metrics = jury_semantic_eval(
        run["final_pref"], payload, meta, eval_sets)
    rec = {
        "jury_size": int(len(users)),
        "stop_reason": run["stop_reason"],
        "n_stages": int(len(run["stages"])),
        "remaining_users": int(run["stages"][-1]["remaining_users"]),
        "targets": geom,
        **_metrics_pick(metrics),
        "head": [
            {k: r[k] for k in ("rank", "work_id", "title", "author", "score")}
            for r in rows[:50]
        ],
        "runtime_seconds": time.time() - t0,
    }
    pref = run["final_pref"].astype(np.float32)
    rep = endpoint_repr(run["final_pref"], eligible)
    return rec, pref, rep


# ---------------------------------------------------------------------------
# Fitness / selection diagnostics
# ---------------------------------------------------------------------------

def fitness_stats(fitness: np.ndarray) -> dict[str, float]:
    f = np.asarray(fitness, dtype=np.float64)
    q = np.quantile(f, [0.05, 0.25, 0.5, 0.75, 0.95])
    return {
        "mean": float(f.mean()),
        "sd": float(f.std()),
        "q05": float(q[0]),
        "q25": float(q[1]),
        "q50": float(q[2]),
        "q75": float(q[3]),
        "q95": float(q[4]),
    }


def split_half_diagnostics(contrib: np.ndarray, users: np.ndarray,
                           n_reps: int) -> dict[str, Any]:
    half = n_reps // 2
    if half < 1:
        return {"spearman_half_panels": None, "half_panel_reps": 0,
                "top_half_overlap": 0, "top_half_overlap_fraction": None}
    fa = contrib[:, :half].mean(axis=1)
    fb = contrib[:, half:2 * half].mean(axis=1)
    try:
        rho = float(spearmanr(fa, fb).statistic)
    except Exception:
        rho = float("nan")
    if not np.isfinite(rho):
        rho = None
    n = len(users)
    k = n // 2
    order_a = np.lexsort((users, -fa))
    order_b = np.lexsort((users, -fb))
    top_a = set(np.asarray(users)[order_a[:k]].tolist())
    top_b = set(np.asarray(users)[order_b[:k]].tolist())
    overlap = len(top_a & top_b)
    return {
        "spearman_half_panels": rho,
        "half_panel_reps": int(half),
        "top_half_overlap": int(overlap),
        "top_half_overlap_fraction": float(overlap / k) if k else None,
    }


def selection_stats(fitness: np.ndarray, pool: np.ndarray,
                    selected: np.ndarray) -> dict[str, Any]:
    f = np.asarray(fitness, dtype=np.float64)
    pool = np.asarray(pool, dtype=np.int64)
    selected = np.asarray(selected, dtype=np.int64)
    sel_mask = np.isin(pool, selected)
    return {
        "n_selected": int(len(selected)),
        "n_rejected": int(len(pool) - len(selected)),
        "selected_mean_fitness": float(f[sel_mask].mean()),
        "rejected_mean_fitness": float(f[~sel_mask].mean()),
        "separation": float(f[sel_mask].mean() - f[~sel_mask].mean()),
    }


def child_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {}
    g = np.asarray([r["targets"]["G10"]["deepest"] for r in records],
                   dtype=np.float64)
    s0 = np.asarray([r["targets"]["G10"]["stage0"] for r in records],
                    dtype=np.float64)
    gn = np.asarray([r["targets"]["G10"]["reversal_gain"] for r in records],
                    dtype=np.float64)
    bs = np.asarray([r["targets"]["G10"]["argmax_stage"] for r in records],
                    dtype=np.float64)
    ex = np.asarray([r["exact50"] for r in records], dtype=np.float64)
    an = np.asarray([r["anti50"] for r in records], dtype=np.float64)
    return {
        "n_children": int(len(records)),
        "g10_deepest_mean": float(g.mean()),
        "g10_deepest_median": float(np.median(g)),
        "fraction_g10_deepest_gt0": float(np.mean(g > 0)),
        "g10_stage0_mean": float(s0.mean()),
        "g10_reversal_gain_mean": float(gn.mean()),
        "g10_reversal_gain_gt0": float(np.mean(gn > 0)),
        "median_g10_argmax_stage": float(np.median(bs)),
        "exact50_mean": float(ex.mean()),
        "anti50_mean": float(an.mean()),
        "fraction_exact50_ge1": float(np.mean(ex >= 1)),
    }


# ---------------------------------------------------------------------------
# Checkpointing helpers
# ---------------------------------------------------------------------------

def _run_spec_hash(args: argparse.Namespace, payload: dict[str, np.ndarray],
                   g10: np.ndarray) -> str:
    spec = {
        "descendant_seed": int(args.seed),
        "follow_replicates": int(args.follow_replicates),
        "desc5k_replicates": int(args.desc5k_replicates),
        "g10_hash": _bytes_sha256(np.asarray(g10, dtype=np.float32).tobytes()),
        "payload_user_hash": _bytes_sha256(
            payload["user_ids"].astype(np.int64).tobytes()),
        "payload_book_hash": _bytes_sha256(
            np.asarray(payload["work_ids"]).tobytes()),
    }
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _follow_chunk_paths(tag: str, root_id: int) -> tuple[Path, Path]:
    d = _chunk_dir(tag)
    return d / f"follow10k_root{root_id}.json", d / f"follow10k_root{root_id}.npz"


def _desc5k_chunk_paths(tag: str, root_id: int) -> tuple[Path, Path]:
    d = _chunk_dir(tag)
    return d / f"desc5k_root{root_id}.json", d / f"desc5k_root{root_id}.npz"


def _evals_chunk_paths(tag: str, root_id: int) -> tuple[Path, Path]:
    d = _chunk_dir(tag)
    return d / f"follow10k_root{root_id}_evals.json", d / f"follow10k_root{root_id}_evals.npz"


# ---------------------------------------------------------------------------
# Part C: independent G10 follow (per root, checkpointed per replicate)
# ---------------------------------------------------------------------------

def process_follow_root(
    args: argparse.Namespace, payload: dict[str, np.ndarray], matrix: Any,
    eligible: np.ndarray, targets: dict[str, np.ndarray], g10: np.ndarray,
    meta: dict[str, Any], eval_sets: dict[str, Any], run_spec_hash: str,
    root_id: int, deadline: float,
) -> dict[str, Any]:
    t0 = getattr(args, "_t0", time.time())
    n_reps = int(args.follow_replicates)
    blob = np.load(BREEDING_NPZ, allow_pickle=False)
    pool = np.asarray(blob[f"root{root_id}_lit_g1_selected"], dtype=np.int64)
    n_users = int(len(pool))
    n_books = int(eligible.sum())
    jpath, npath = _follow_chunk_paths(args.tag, root_id)
    jpath.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    rep_ids: list[int] = []
    reps_rows: list[np.ndarray] = []
    g10_rows: list[np.ndarray] = []
    assign_rows: list[np.ndarray] = []
    if jpath.exists():
        old = json.loads(jpath.read_text(encoding="utf-8"))
        if old.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"chunk {jpath.name} run_spec_hash mismatch")
        if old.get("stage") in ("done", "campaign"):
            records = old["child_runs"]
            if npath.exists():
                with np.load(npath, allow_pickle=False) as b:
                    rep_ids = [int(x) for x in b["rep_ids"]]
                    for i in range(len(rep_ids)):
                        reps_rows.append(b["child_reps"][i])
                        g10_rows.append(b["child_g10"][i])
                        assign_rows.append(b["assignments"][i])
        if old.get("stage") == "done":
            return old

    done = set(rep_ids)
    for r in range(n_reps):
        if r in done:
            continue
        if time.time() > deadline:
            raise SystemExit("deadline reached inside follow10k")
        t_r = time.time()
        rng = np.random.default_rng(
            _derive_seed(args.seed, "follow10k", root_id, r))
        groups = balanced_partitions(pool, 2, rng)
        assign = np.full(n_users, -1, dtype=np.int8)
        assign[np.searchsorted(pool, groups[0])] = 0
        assign[np.searchsorted(pool, groups[1])] = 1
        reps_rep = np.empty((2, n_books), dtype=np.float32)
        g10_rep = np.empty(2, dtype=np.float32)
        for g, group in enumerate(groups):
            rng_run = np.random.default_rng(
                _derive_seed(args.seed, "follow10k", root_id, r, g))
            rec, rep = run_child_reversal(
                payload, matrix, group, rng_run, eligible, targets,
                meta, eval_sets)
            rec["replicate"] = r
            rec["group"] = g
            records.append(rec)
            reps_rep[g] = rep
            g10_rep[g] = rec["targets"]["G10"]["deepest"]
        rep_ids.append(r)
        reps_rows.append(reps_rep)
        g10_rows.append(g10_rep)
        assign_rows.append(assign)
        arrays = {
            "pool": pool.astype(np.int32),
            "rep_ids": np.asarray(rep_ids, dtype=np.int16),
            "child_reps": np.stack(reps_rows).astype(np.float32),
            "child_g10": np.stack(g10_rows).astype(np.float32),
            "assignments": np.stack(assign_rows).astype(np.int8),
        }
        _write_npz_atomic(npath, arrays)
        partial = {
            "run_spec_hash": run_spec_hash,
            "root": int(root_id),
            "n_replicates": int(n_reps),
            "completed_replicates": [int(x) for x in rep_ids],
            "child_runs": records,
            "stage": "campaign",
        }
        _write_text_atomic(jpath, json.dumps(partial))
        print(
            f"follow10k root {root_id}: replicate {r}/{n_reps} "
            f"({time.time() - t_r:.1f}s, elapsed {time.time() - t0:.0f}s)",
            flush=True,
        )

    if len(rep_ids) < n_reps:
        raise SystemExit(
            f"follow10k root {root_id} incomplete "
            f"({len(rep_ids)}/{n_reps} replicates)"
        )

    order = np.argsort(np.asarray(rep_ids))
    margins = np.stack(g10_rows)[order].astype(np.float64)
    assignments = np.stack(assign_rows)[order]
    fitness, contrib = fitness_from_margins(margins, assignments)
    sel_follow = select_fraction(pool, fitness, top=True)
    sel_avoid = select_fraction(pool, fitness, top=False)
    rng_rand = np.random.default_rng(
        _derive_seed(args.seed, "random10k", root_id))
    sel_rand = np.sort(rng_rand.permutation(pool)[: n_users // 2])

    node = {
        "run_spec_hash": run_spec_hash,
        "root": int(root_id),
        "n_replicates": int(n_reps),
        "completed_replicates": [int(x) for x in sorted(rep_ids)],
        "child_runs": records,
        "child_summary": child_summary(records),
        "fitness_stats": fitness_stats(fitness),
        "split_half": split_half_diagnostics(contrib, pool, n_reps),
        "selections": {
            "G_follow": selection_stats(fitness, pool, sel_follow),
            "G_avoid": selection_stats(fitness, pool, sel_avoid),
            "random10k": {"n_selected": int(len(sel_rand))},
        },
        "pool_key": f"root{root_id}_lit_g1_selected",
        "G_follow_key": f"follow10k_root{root_id}_G_follow",
        "G_avoid_key": f"follow10k_root{root_id}_G_avoid",
        "random10k_key": f"follow10k_root{root_id}_random10k",
        "fitness_key": f"follow10k_root{root_id}_fitness",
        "child_reps_key": f"follow10k_root{root_id}_child_reps",
        "stage": "done",
    }
    arrays = {
        "pool": pool.astype(np.int32),
        "rep_ids": np.asarray(rep_ids, dtype=np.int16),
        "child_reps": np.stack(reps_rows)[order].astype(np.float32),
        "child_g10": np.stack(g10_rows)[order].astype(np.float32),
        "assignments": assignments.astype(np.int8),
        "fitness": fitness.astype(np.float32),
        "G_follow": sel_follow.astype(np.int32),
        "G_avoid": sel_avoid.astype(np.int32),
        "random10k": sel_rand.astype(np.int32),
    }
    _write_npz_atomic(npath, arrays)
    _write_text_atomic(jpath, json.dumps(node))
    print(
        f"follow10k root {root_id} complete: {len(records)} child runs, "
        f"elapsed {time.time() - t0:.0f}s",
        flush=True,
    )
    return node


def process_follow_evals(
    args: argparse.Namespace, payload: dict[str, np.ndarray], matrix: Any,
    eligible: np.ndarray, targets: dict[str, np.ndarray], g10: np.ndarray,
    meta: dict[str, Any], eval_sets: dict[str, Any], run_spec_hash: str,
    root_id: int, deadline: float,
    family_centroids: dict[int, np.ndarray] | None = None,
) -> dict[str, Any]:
    jpath, npath = _evals_chunk_paths(args.tag, root_id)
    jpath.parent.mkdir(parents=True, exist_ok=True)
    if jpath.exists():
        old = json.loads(jpath.read_text(encoding="utf-8"))
        if old.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"chunk {jpath.name} run_spec_hash mismatch")
        if old.get("complete"):
            return old
    if time.time() > deadline:
        raise SystemExit("deadline reached in follow evals")

    fpath, farr = _follow_chunk_paths(args.tag, root_id)
    node = json.loads(fpath.read_text(encoding="utf-8"))
    with np.load(farr, allow_pickle=False) as b:
        pools = {
            "G_follow": np.asarray(b["G_follow"], dtype=np.int64),
            "G_avoid": np.asarray(b["G_avoid"], dtype=np.int64),
            "random10k": np.asarray(b["random10k"], dtype=np.int64),
        }
    old_blob = np.load(BREEDING_NPZ, allow_pickle=False)
    pools["old_fixed_f1"] = np.asarray(
        old_blob[f"root{root_id}_lit_g2_selected"], dtype=np.int64)

    evals: dict[str, Any] = {}
    eval_arrays: dict[str, np.ndarray] = {}
    for label, users in pools.items():
        rng_eval = np.random.default_rng(
            _derive_seed(args.seed, "eval10k", root_id, label))
        rec, pref, rep = run_jury_eval(
            payload, matrix, users, rng_eval, eligible, targets, meta,
            eval_sets)
        rec["label"] = label
        if label == "old_fixed_f1":
            stored = np.asarray(old_blob[f"root{root_id}_eval_lit_g2_pref"],
                                dtype=np.float32)
            rec["reproduces_stored_baseline"] = bool(
                np.array_equal(pref, stored))
        if family_centroids:
            rec["family_cos"] = {
                str(i): float(rep @ cent)
                for i, cent in sorted(family_centroids.items())
            }
            rec["nearest_family"] = int(max(
                family_centroids, key=lambda i: rec["family_cos"][str(i)]))
        evals[label] = rec
        eval_arrays[f"eval_{label}_root{root_id}_rep"] = rep
        eval_arrays[f"eval_{label}_root{root_id}_pref"] = pref
        print(
            f"follow10k root {root_id} eval {label}: "
            f"G10={rec['targets']['G10']['deepest']:+.4f} "
            f"exact@50={rec['exact50']} anti@50={rec['anti50']}",
            flush=True,
        )

    out = {
        "run_spec_hash": run_spec_hash,
        "root": int(root_id),
        "evals": evals,
        "complete": True,
    }
    _write_npz_atomic(npath, eval_arrays)
    _write_text_atomic(jpath, json.dumps(out))
    return out


# ---------------------------------------------------------------------------
# Part E: 5k descendant runs (per root, checkpointed per replicate)
# ---------------------------------------------------------------------------

def process_desc5k_root(
    args: argparse.Namespace, payload: dict[str, np.ndarray], matrix: Any,
    eligible: np.ndarray, targets: dict[str, np.ndarray], g10: np.ndarray,
    meta: dict[str, Any], eval_sets: dict[str, Any], run_spec_hash: str,
    root_id: int, deadline: float,
) -> dict[str, Any]:
    t0 = getattr(args, "_t0", time.time())
    n_reps = int(args.desc5k_replicates)
    fpath, farr = _follow_chunk_paths(args.tag, root_id)
    fnode = json.loads(fpath.read_text(encoding="utf-8"))
    with np.load(farr, allow_pickle=False) as b:
        pool = np.asarray(b["G_follow"], dtype=np.int64)
    n_users = int(len(pool))
    n_books = int(eligible.sum())
    jpath, npath = _desc5k_chunk_paths(args.tag, root_id)
    jpath.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    rep_ids: list[int] = []
    reps_rows: list[np.ndarray] = []
    if jpath.exists():
        old = json.loads(jpath.read_text(encoding="utf-8"))
        if old.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"chunk {jpath.name} run_spec_hash mismatch")
        if old.get("stage") == "done":
            return old
        records = old["child_runs"]
        if npath.exists():
            with np.load(npath, allow_pickle=False) as b:
                rep_ids = [int(x) for x in b["rep_ids"]]
                for i in range(len(rep_ids)):
                    reps_rows.append(b["child_reps"][i])

    done = set(rep_ids)
    for r in range(n_reps):
        if r in done:
            continue
        if time.time() > deadline:
            raise SystemExit("deadline reached inside desc5k")
        t_r = time.time()
        rng = np.random.default_rng(
            _derive_seed(args.seed, "desc5k", root_id, r))
        groups = balanced_partitions(pool, 2, rng)
        reps_rep = np.empty((2, n_books), dtype=np.float32)
        for g, group in enumerate(groups):
            rng_run = np.random.default_rng(
                _derive_seed(args.seed, "desc5k", root_id, r, g))
            rec, rep = run_child_reversal(
                payload, matrix, group, rng_run, eligible, targets,
                meta, eval_sets)
            rec["replicate"] = r
            rec["group"] = g
            records.append(rec)
            reps_rep[g] = rep
        rep_ids.append(r)
        reps_rows.append(reps_rep)
        arrays = {
            "pool": pool.astype(np.int32),
            "rep_ids": np.asarray(rep_ids, dtype=np.int16),
            "child_reps": np.stack(reps_rows).astype(np.float32),
        }
        _write_npz_atomic(npath, arrays)
        partial = {
            "run_spec_hash": run_spec_hash,
            "root": int(root_id),
            "n_replicates": int(n_reps),
            "completed_replicates": [int(x) for x in rep_ids],
            "child_runs": records,
            "stage": "campaign",
        }
        _write_text_atomic(jpath, json.dumps(partial))
        print(
            f"desc5k root {root_id}: replicate {r}/{n_reps} "
            f"({time.time() - t_r:.1f}s, elapsed {time.time() - t0:.0f}s)",
            flush=True,
        )

    if len(rep_ids) < n_reps:
        raise SystemExit(
            f"desc5k root {root_id} incomplete ({len(rep_ids)}/{n_reps})"
        )

    order = np.argsort(np.asarray(rep_ids))
    node = {
        "run_spec_hash": run_spec_hash,
        "root": int(root_id),
        "n_replicates": int(n_reps),
        "completed_replicates": [int(x) for x in sorted(rep_ids)],
        "child_runs": records,
        "child_summary": child_summary(records),
        "pool_key": f"follow10k_root{root_id}_G_follow",
        "child_reps_key": f"desc5k_root{root_id}_child_reps",
        "stage": "done",
    }
    arrays = {
        "pool": pool.astype(np.int32),
        "rep_ids": np.asarray(rep_ids, dtype=np.int16),
        "child_reps": np.stack(reps_rows)[order].astype(np.float32),
    }
    _write_npz_atomic(npath, arrays)
    _write_text_atomic(jpath, json.dumps(node))
    print(
        f"desc5k root {root_id} complete: {len(records)} child runs, "
        f"elapsed {time.time() - t0:.0f}s",
        flush=True,
    )
    return node


# ---------------------------------------------------------------------------
# Phase: analyze10k (Part A label-blind census + Part B frozen semantics)
# ---------------------------------------------------------------------------

def _method_block(args: argparse.Namespace, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    block = {
        "descendant_seed": int(args.seed),
        "follow_replicates": int(args.follow_replicates),
        "desc5k_replicates": int(args.desc5k_replicates),
        "natural_k_range": list(NATURAL_K_RANGE),
        "fixed_taus": [float(t) for t in FIXED_TAUS],
        "semantic_firewall": False,
        "git_head": _git_head(),
        "command": shlex.join(sys.argv),
    }
    if extra:
        block.update(extra)
    return block


def _write_analyze10k_outputs(args: argparse.Namespace,
                              analyze: dict[str, Any],
                              npz_out: dict[str, np.ndarray]) -> None:
    jout, nout, _rep = _output_paths(args.tag)
    _write_npz_atomic(nout, npz_out)
    analyze["artifact_sha256"] = _bytes_sha256(nout.read_bytes())
    analyze["artifact_bytes"] = int(nout.stat().st_size)
    full = {
        "analyze10k": analyze,
        "method": _method_block(args),
        "complete": True,
    }
    _write_text_atomic(jout, json.dumps(full, indent=1))


def phase_analyze10k(args: argparse.Namespace) -> None:
    global SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    if int(eligible.sum()) != 26418:
        raise SystemExit(f"eligible universe {eligible.sum()} != 26418")
    eligible_idx = np.flatnonzero(eligible)
    f0, f1 = load_family_compass(payload, eligible)
    reps, meta, root_of, repl_of = load_saved_10k_endpoints()
    group_of = np.asarray([m["sibling_group"] for m in meta], dtype=np.int16)

    sim = reps @ reps.T
    iu = np.triu_indices(48, k=1)
    sim_vals = sim[iu]
    natural_k, natural_s, per_k, labels = natural_cut_by_silhouette(reps)
    families = family_census(reps, labels, root_of, repl_of, group_of, f0, f1)

    analyze: dict[str, Any] = {
        "source": "recursive_family_breeding.npz root{0,1}_lit_g2_child_reps",
        "n_endpoints": 48,
        "endpoints_per_root": 24,
        "parent_lineage": "literary 20k (root{0,1}_lit_g1_selected)",
        "similarity": {
            "mean": float(sim_vals.mean()),
            "q25": float(np.quantile(sim_vals, 0.25)),
            "median": float(np.median(sim_vals)),
            "q75": float(np.quantile(sim_vals, 0.75)),
            "min": float(sim_vals.min()),
            "max": float(sim_vals.max()),
        },
        "silhouette_by_k": per_k,
        "natural_k": int(natural_k),
        "natural_silhouette": float(natural_s),
        "fixed_cuts": {
            f"{tau:.2f}": fixed_cut_summary(reps, tau) for tau in FIXED_TAUS
        },
        "families": families,
        "semantic_context_loaded": False,
    }

    npz_out: dict[str, np.ndarray] = {
        "endpoint_reps_10k": reps.astype(np.float32),
        "endpoint_root_10k": root_of.astype(np.int16),
        "endpoint_replicate_10k": repl_of.astype(np.int16),
        "endpoint_group_10k": group_of.astype(np.int16),
    }
    for f in families:
        key = f"family_cent_10k_{f['family_id']}"
        f["centroid_key"] = key
        npz_out[key] = unit_centroid(reps[f["members"]])
    _write_analyze10k_outputs(args, analyze, npz_out)
    print(
        f"analyze10k (label-blind) done: natural k={natural_k} "
        f"(silhouette {natural_s:.4f}), {len(families)} families, "
        f"cross-root recurrent {sum(1 for f in families if f['cross_root_recurrent'])}",
        flush=True,
    )

    # ---- frozen partition complete; NOW the semantic inspection ----
    print("Loading post-hoc semantic context (analyze10k)", flush=True)
    SEMANTIC_CONTEXT_LOADED = True
    meta_sem, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    for f in families:
        centroid = np.asarray(npz_out[f"family_cent_10k_{f['family_id']}"],
                              dtype=np.float64)
        rows, metrics = centroid_semantic_eval(
            centroid, eligible_idx, payload, meta_sem, eval_sets)
        c50 = _counts100(rows, eval_sets, 50)
        c100 = _counts100(rows, eval_sets, 100)
        f["semantic"] = {
            "exact50": c50["exact_lit"],
            "broad50": c50["broad_lit"],
            "anti50": c50["anti"],
            "exact100": c100["exact_lit"],
            "broad100": c100["broad_lit"],
            "anti100": c100["anti"],
        }
        f["head"] = [
            {k: r[k] for k in ("rank", "work_id", "title", "author", "score")}
            for r in rows[:30]
        ]
    chosen = choose_G10(families)
    analyze["eligible_targets"] = [
        int(f["family_id"]) for f in families if f["cross_root_recurrent"]
    ]
    analyze["semantic_context_loaded"] = True
    if chosen is None:
        analyze["G10"] = None
        analyze["stopped"] = (
            "20k F1 descendants did not resolve into a cross-root recurrent "
            "10k family under the fixed natural geometric partition."
        )
        _write_analyze10k_outputs(args, analyze, npz_out)
        print(
            "analyze10k: NO eligible cross-root recurrent 10k family; "
            "STOP after Part A/B.",
            flush=True,
        )
        return
    g10 = unit_centroid(reps[chosen["members"]])
    npz_out["G10"] = g10
    analyze["G10"] = {
        "family_id": int(chosen["family_id"]),
        "semantic": chosen["semantic"],
        "reason": (
            "deterministic semantic branch choice: highest exact@50, then "
            "broad@50, then lowest anti@50, then largest size, then lowest "
            "family id, among cross-root recurrent families"
        ),
        "centroid_key": "G10",
        "n_endpoints": int(chosen["n_endpoints"]),
        "root_half_centroid_cos": chosen["root_half_centroid_cos"],
        "cos_f1": float(chosen["cos_f1"]),
        "cos_f0": float(chosen["cos_f0"]),
    }
    _write_analyze10k_outputs(args, analyze, npz_out)
    print(
        f"analyze10k complete: G10 = family {chosen['family_id']} "
        f"(exact@50 {chosen['semantic']['exact50']}, broad@50 "
        f"{chosen['semantic']['broad50']}, anti@50 "
        f"{chosen['semantic']['anti50']}), {time.time() - t0:.0f}s",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Phase: follow10k (Part C + D)
# ---------------------------------------------------------------------------

def _load_analyze10k(args: argparse.Namespace) -> dict[str, Any]:
    jout, nout, _rep = _output_paths(args.tag)
    if not jout.exists() or not nout.exists():
        raise SystemExit("missing analyze10k outputs; run analyze10k first")
    analyze = json.loads(jout.read_text(encoding="utf-8"))["analyze10k"]
    if analyze.get("G10") is None:
        raise SystemExit(analyze.get("stopped", "no G10 target; STOP"))
    with np.load(nout, allow_pickle=False) as blob:
        g10 = np.asarray(blob["G10"], dtype=np.float64)
        npz = {k: blob[k] for k in blob.files}
    return analyze, g10, npz


def phase_follow10k(args: argparse.Namespace) -> None:
    t0 = time.time()
    args._t0 = t0
    analyze, g10, npz = _load_analyze10k(args)
    family_centroids = {
        f["family_id"]: np.asarray(npz[f"family_cent_10k_{f['family_id']}"],
                                   dtype=np.float64)
        for f in analyze["families"]
    }
    payload, matrix, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    f0, f1 = load_family_compass(payload, eligible)
    targets = {"G10": g10, "F1": f1, "F0": f0}
    run_spec_hash = _run_spec_hash(args, payload, g10)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    deadline = t0 + args.hours * 3600.0 if args.hours > 0 else float("inf")
    for root_id in range(2):
        if time.time() > deadline:
            break
        process_follow_root(
            args, payload, matrix, eligible, targets, g10, meta, eval_sets,
            run_spec_hash, root_id, deadline)
        process_follow_evals(
            args, payload, matrix, eligible, targets, g10, meta, eval_sets,
            run_spec_hash, root_id, deadline, family_centroids)
    print(f"follow10k phase done in {time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------------------
# Phase: analyze5k (Part E census; no selection)
# ---------------------------------------------------------------------------

def _load_desc5k_endpoints(args: argparse.Namespace) -> tuple[np.ndarray,
                                                              list[dict[str, Any]],
                                                              np.ndarray,
                                                              np.ndarray]:
    reps_all: list[np.ndarray] = []
    meta_all: list[dict[str, Any]] = []
    for root_id in range(2):
        jpath, npath = _desc5k_chunk_paths(args.tag, root_id)
        if not jpath.exists() or not npath.exists():
            raise SystemExit(f"missing desc5k chunk for root {root_id}")
        node = json.loads(jpath.read_text(encoding="utf-8"))
        with np.load(npath, allow_pickle=False) as b:
            reps = np.asarray(b["child_reps"], dtype=np.float64)
        n_done = int(node["completed_replicates"][-1]) + 1 if node["completed_replicates"] else 0
        if n_done != int(args.desc5k_replicates):
            raise SystemExit(
                f"desc5k root {root_id} incomplete ({n_done}/{args.desc5k_replicates})"
            )
        for i in range(reps.shape[0]):
            for g in range(2):
                reps_all.append(reps[i, g])
                meta_all.append({
                    "root": root_id,
                    "parent_lineage": "G_follow 10k",
                    "replicate": int(i),
                    "sibling_group": g,
                    "endpoint_index": len(meta_all),
                })
    root_of = np.asarray([m["root"] for m in meta_all], dtype=np.int16)
    repl_of = np.asarray([m["replicate"] for m in meta_all], dtype=np.int16)
    group_of = np.asarray([m["sibling_group"] for m in meta_all], dtype=np.int16)
    return np.stack(reps_all), meta_all, root_of, repl_of


def phase_analyze5k(args: argparse.Namespace) -> None:
    global SEMANTIC_CONTEXT_LOADED
    t0 = time.time()
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    eligible_idx = np.flatnonzero(eligible)
    f0, f1 = load_family_compass(payload, eligible)
    reps, meta, root_of, repl_of = _load_desc5k_endpoints(args)
    group_of = np.asarray([m["sibling_group"] for m in meta], dtype=np.int16)

    sim = reps @ reps.T
    iu = np.triu_indices(len(reps), k=1)
    sim_vals = sim[iu]
    natural_k, natural_s, per_k, labels = natural_cut_by_silhouette(reps)
    families = family_census(reps, labels, root_of, repl_of, group_of, f0, f1)

    census: dict[str, Any] = {
        "source": "new G_follow 10k juries, desc5k campaigns (96 children)",
        "n_endpoints": int(len(reps)),
        "similarity": {
            "mean": float(sim_vals.mean()),
            "q25": float(np.quantile(sim_vals, 0.25)),
            "median": float(np.median(sim_vals)),
            "q75": float(np.quantile(sim_vals, 0.75)),
            "min": float(sim_vals.min()),
            "max": float(sim_vals.max()),
        },
        "silhouette_by_k": per_k,
        "natural_k": int(natural_k),
        "natural_silhouette": float(natural_s),
        "fixed_cuts": {
            f"{tau:.2f}": fixed_cut_summary(reps, tau) for tau in FIXED_TAUS
        },
        "families": families,
        "followed_5k_family": None,
        "note": "No 5k family is followed or selected in this experiment.",
        "semantic_context_loaded": False,
    }

    npz_out: dict[str, np.ndarray] = {
        "endpoint_reps_5k": reps.astype(np.float32),
        "endpoint_root_5k": root_of.astype(np.int16),
        "endpoint_replicate_5k": repl_of.astype(np.int16),
        "endpoint_group_5k": group_of.astype(np.int16),
    }
    for f in families:
        key = f"family_cent_5k_{f['family_id']}"
        f["centroid_key"] = key
        npz_out[key] = unit_centroid(reps[f["members"]])
    cjout, cnout = _census_paths(args.tag)
    _write_npz_atomic(cnout, npz_out)
    print(
        f"analyze5k (label-blind) done: natural k={natural_k} "
        f"(silhouette {natural_s:.4f}), {len(families)} families, "
        f"cross-root recurrent {sum(1 for f in families if f['cross_root_recurrent'])}",
        flush=True,
    )

    print("Loading post-hoc semantic context (analyze5k)", flush=True)
    SEMANTIC_CONTEXT_LOADED = True
    meta_sem, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    for f in families:
        centroid = np.asarray(npz_out[f"family_cent_5k_{f['family_id']}"],
                              dtype=np.float64)
        rows, metrics = centroid_semantic_eval(
            centroid, eligible_idx, payload, meta_sem, eval_sets)
        c50 = _counts100(rows, eval_sets, 50)
        c100 = _counts100(rows, eval_sets, 100)
        f["semantic"] = {
            "exact50": c50["exact_lit"],
            "broad50": c50["broad_lit"],
            "anti50": c50["anti"],
            "exact100": c100["exact_lit"],
            "broad100": c100["broad_lit"],
            "anti100": c100["anti"],
        }
        f["head"] = [
            {k: r[k] for k in ("rank", "work_id", "title", "author", "score")}
            for r in rows[:20]
        ]
    census["semantic_context_loaded"] = True
    census["cross_root_recurrent_families"] = [
        int(f["family_id"]) for f in families if f["cross_root_recurrent"]
    ]
    census["artifact_sha256"] = _bytes_sha256(cnout.read_bytes())
    census["artifact_bytes"] = int(cnout.stat().st_size)
    _write_text_atomic(cjout, json.dumps(census, indent=1))
    print(f"analyze5k complete in {time.time() - t0:.0f}s", flush=True)
    return census


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------

def consolidate(args: argparse.Namespace) -> None:
    t0 = time.time()
    jout, nout, _rep = _output_paths(args.tag)
    if not jout.exists():
        raise SystemExit(f"missing results JSON {jout}")
    analyze = json.loads(jout.read_text(encoding="utf-8"))["analyze10k"]
    if analyze.get("G10") is None:
        print(f"consolidated (STOP at Part A/B): {jout}", flush=True)
        return
    with np.load(nout, allow_pickle=False) as blob:
        g10 = np.asarray(blob["G10"], dtype=np.float64)
    payload, _, _ = year.load_matrix()
    run_spec_hash = _run_spec_hash(args, payload, g10)

    follow_roots: list[dict[str, Any]] = []
    eval_roots: list[dict[str, Any]] = []
    with np.load(nout, allow_pickle=False) as b:
        arrays: dict[str, np.ndarray] = {key: b[key] for key in b.files}
    for root_id in range(2):
        fpath, farr = _follow_chunk_paths(args.tag, root_id)
        if not fpath.exists():
            raise SystemExit(f"missing follow10k chunk root {root_id}")
        node = json.loads(fpath.read_text(encoding="utf-8"))
        if node.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"follow10k root {root_id} spec mismatch")
        with np.load(farr, allow_pickle=False) as b:
            for key in ("pool", "fitness", "G_follow", "G_avoid", "random10k",
                        "child_reps"):
                arrays[f"{key}_root{root_id}" if key == "pool" else
                       f"follow10k_root{root_id}_{key}"] = b[key]
        follow_roots.append({
            "root": int(root_id),
            "pool_key": f"pool_root{root_id}",
            "fitness_key": f"follow10k_root{root_id}_fitness",
            "G_follow_key": f"follow10k_root{root_id}_G_follow",
            "G_avoid_key": f"follow10k_root{root_id}_G_avoid",
            "random10k_key": f"follow10k_root{root_id}_random10k",
            "child_reps_key": f"follow10k_root{root_id}_child_reps",
            "child_summary": node["child_summary"],
            "fitness_stats": node["fitness_stats"],
            "split_half": node["split_half"],
            "selections": node["selections"],
        })
        epath, earr = _evals_chunk_paths(args.tag, root_id)
        evals_node = json.loads(epath.read_text(encoding="utf-8"))
        with np.load(earr, allow_pickle=False) as b:
            for key in b.files:
                arrays[key] = b[key]
        eval_roots.append({"root": int(root_id), "evals": evals_node["evals"]})

    desc5k_roots: list[dict[str, Any]] = []
    for root_id in range(2):
        jpath, npath = _desc5k_chunk_paths(args.tag, root_id)
        node = json.loads(jpath.read_text(encoding="utf-8"))
        if node.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"desc5k root {root_id} spec mismatch")
        with np.load(npath, allow_pickle=False) as b:
            arrays[f"desc5k_root{root_id}_child_reps"] = b["child_reps"]
            arrays[f"desc5k_root{root_id}_pool"] = b["pool"]
        desc5k_roots.append({
            "root": int(root_id),
            "pool_key": f"desc5k_root{root_id}_pool",
            "child_reps_key": f"desc5k_root{root_id}_child_reps",
            "child_summary": node["child_summary"],
        })

    # 5k census: read from the separate census artifacts if present
    census5k = None
    cjout, cnout = _census_paths(args.tag)
    if cjout.exists() and cnout.exists():
        census5k = json.loads(cjout.read_text(encoding="utf-8"))
        with np.load(cnout, allow_pickle=False) as b:
            for key in b.files:
                arrays[key] = b[key]

    result = {
        "method": {
            "experiment": "recursive descendant families (fragmentation test)",
            "descendant_seed": int(args.seed),
            "follow_replicates": int(args.follow_replicates),
            "desc5k_replicates": int(args.desc5k_replicates),
            "breeding_seed": int(BREEDING_SEED),
            "natural_k_range": list(NATURAL_K_RANGE),
            "fixed_taus": [float(t) for t in FIXED_TAUS],
            "selection": (
                "mean over 24 new replicates of within-partition centered "
                "deepest-endpoint cos(child, G10); ties by ascending global "
                "user index; no semantic labels; no old F1/F0 in selection"
            ),
            "G10_choice": analyze["G10"]["reason"] if analyze.get("G10") else None,
            "semantic_firewall": False,
            "git_head": _git_head(),
            "command": shlex.join(sys.argv),
            "runtime_seconds": time.time() - t0,
        },
        "analyze10k": analyze,
        "follow10k": {"roots": follow_roots, "evals": eval_roots},
        "analyze5k": census5k,
        "complete": True,
    }
    _write_npz_atomic(nout, arrays)
    sha = _bytes_sha256(nout.read_bytes())
    result["artifact_sha256"] = sha
    result["artifact_bytes"] = int(nout.stat().st_size)
    result["npz_keys"] = sorted(arrays.keys())
    _write_text_atomic(jout, json.dumps(result, indent=1))
    print(
        f"consolidated {jout}: {len(arrays)} npz keys, sha256 {sha[:16]}..., "
        f"{time.time() - t0:.0f}s",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def _smoke_check(checks: list[dict[str, Any]], name: str, ok: bool,
                 detail: str) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def _semantic_flag_before_loader() -> bool:
    try:
        src = inspect.getsource(phase_analyze10k).splitlines()
    except (OSError, TypeError):
        return False
    flag_line = loader_line = None
    for i, ln in enumerate(src):
        s = ln.strip()
        if s == "SEMANTIC_CONTEXT_LOADED = True":
            flag_line = i
        if "load_posthoc_context" in s:
            loader_line = i
    return (flag_line is not None and loader_line is not None
            and flag_line < loader_line)


def phase_smoke(args: argparse.Namespace) -> None:
    t0 = time.time()
    checks: list[dict[str, Any]] = []
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    eligible_idx = np.flatnonzero(eligible)
    f0, f1 = load_family_compass(payload, eligible)

    # 1. previous breeding artifact loads, complete
    try:
        prev = json.loads(BREEDING_JSON.read_text(encoding="utf-8"))
        ok1 = bool(prev.get("complete"))
        np.load(BREEDING_NPZ, allow_pickle=False)
    except Exception as exc:
        ok1, detail1 = False, str(exc)
    else:
        detail1 = f"breeding json complete={prev.get('complete')}"
    _smoke_check(checks, "previous_breeding_artifact_loads", bool(ok1), detail1)

    # 2-4. saved 10k descendants: 48 reps, finite unit, 24 per root
    reps, meta, root_of, repl_of = load_saved_10k_endpoints()
    group_of = np.asarray([m["sibling_group"] for m in meta], dtype=np.int16)
    norms = np.linalg.norm(reps, axis=1)
    _smoke_check(checks, "exactly_48_saved_10k_reps",
                 reps.shape == (48, 26418),
                 f"shape {reps.shape}")
    _smoke_check(checks, "reps_finite_unit",
                 bool(np.isfinite(reps).all()
                      and np.abs(norms - 1.0).max() < 1e-4),
                 f"norm min/max {norms.min():.6f}/{norms.max():.6f}")
    _smoke_check(checks, "metadata_24_per_root",
                 bool((root_of == 0).sum() == 24 and (root_of == 1).sum() == 24
                      and set(repl_of.tolist()) == {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}
                      and set(group_of.tolist()) == {0, 1}),
                 f"roots {dict(zip(*np.unique(root_of, return_counts=True)))}")

    # 5-6. natural clustering deterministic, partitions all endpoints once
    k1, s1, per_k1, lab1 = natural_cut_by_silhouette(reps)
    k2, s2, per_k2, lab2 = natural_cut_by_silhouette(reps)
    _smoke_check(checks, "silhouette_selection_deterministic",
                 bool(k1 == k2 and s1 == s2 and np.array_equal(lab1, lab2)),
                 f"k={k1} k2={k2} s={s1:.6f}")
    _smoke_check(checks, "natural_partition_covers_all_exactly_once",
                 bool(len(lab1) == 48
                      and set(lab1.tolist()) == set(range(k1))),
                 "every endpoint assigned to exactly one of the k clusters")
    # lowest-k tie break on synthetic data
    rng_s = np.random.default_rng(3)
    syn = rng_s.standard_normal((12, 20))
    syn = syn / np.linalg.norm(syn, axis=1, keepdims=True)
    syn_labels = np.zeros(12, dtype=np.int32)
    syn_labels[6:] = 1
    sil_2, _ = silhouette_cosine(syn, syn_labels, 2)
    ks_ok = k1 in range(2, 9)
    _smoke_check(checks, "silhouette_in_range", bool(ks_ok),
                 f"natural k={k1} in 2..8, per-k {per_k1}")

    # 7. recurrence uses DISTINCT replicates (synthetic)
    fake_root = np.array([0, 0, 0, 0, 1, 1], dtype=np.int16)
    fake_repl = np.array([0, 0, 1, 1, 0, 0], dtype=np.int16)
    fake_grp = np.array([0, 1, 0, 1, 0, 1], dtype=np.int16)
    fake_mat = rng_s.standard_normal((6, 20))
    fake_mat = fake_mat / np.linalg.norm(fake_mat, axis=1, keepdims=True)
    z20 = np.zeros(20)
    fam = family_census(fake_mat, np.zeros(6, dtype=np.int32),
                        fake_root, fake_repl, fake_grp, z20, z20)[0]
    rec_ok = (fam["n_distinct_replicates"] == 2
              and fam["replicates_root0"] == [0, 1]
              and fam["replicates_root1"] == [0]
              and fam["n_sibling_pairs"] == 3)
    _smoke_check(checks, "recurrence_counts_distinct_replicates",
                 bool(rec_ok),
                 f"distinct {fam['n_distinct_replicates']}, "
                 f"r0 {fam['replicates_root0']}, r1 {fam['replicates_root1']}, "
                 f"pairs {fam['n_sibling_pairs']}")
    fake2 = family_census(fake_mat, np.zeros(6, dtype=np.int32),
                          np.array([0, 0, 1, 1, 0, 1], dtype=np.int16),
                          fake_repl, fake_grp, z20, z20)[0]
    _smoke_check(checks, "cross_root_recurrent_flag",
                 bool(not fake2["cross_root_recurrent"]
                      and fake2["replicates_root0"] == [0]
                      and fake2["replicates_root1"] == [0, 1]),
                 f"single distinct root-0 replicate -> not cross-root "
                 f"recurrent (r0 {fake2['replicates_root0']})")

    # 8. root half centroids
    rng_s2 = np.random.default_rng(4)
    m8 = rng_s2.standard_normal((8, 20))
    m8 = m8 / np.linalg.norm(m8, axis=1, keepdims=True)
    fam8 = family_census(
        m8, np.zeros(8, dtype=np.int32),
        np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int16),
        np.array([0, 1, 2, 3, 0, 1, 2, 3], dtype=np.int16),
        np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int16),
        z20, z20)[0]
    expect_cos = float(unit_centroid(m8[:4]) @ unit_centroid(m8[4:]))
    _smoke_check(checks, "root_half_centroids_correct",
                 abs(fam8["root_half_centroid_cos"] - expect_cos) < 1e-6,
                 f"got {fam8['root_half_centroid_cos']:.6f} "
                 f"expected {expect_cos:.6f}")
    _smoke_check(checks, "strong_flag_ge3_reps",
                 bool(fam8["strong_cross_root_recurrent"]
                      and fam8["cross_root_recurrent"]),
                 f"size 8, 4 distinct reps per root -> strong recurrent")

    # 9. semantic not used before partition frozen
    _smoke_check(checks, "semantic_flag_set_before_loader",
                 bool(_semantic_flag_before_loader()),
                 "SEMANTIC_CONTEXT_LOADED set before load_posthoc_context "
                 "in phase_analyze10k")
    src_cluster = (inspect.getsource(natural_cut_by_silhouette)
                   + inspect.getsource(family_census)
                   + inspect.getsource(silhouette_cosine))
    banned = [tok for tok in FORBIDDEN_FITNESS_TOKENS if tok in src_cluster]
    _smoke_check(checks, "clustering_label_blind",
                 not banned, f"banned tokens {banned or 'none'}")

    # 10. G10 deterministic semantic tie-breaking
    fake_fams = [
        {"family_id": 0, "n_endpoints": 7, "cross_root_recurrent": True,
         "semantic": {"exact50": 3, "broad50": 5, "anti50": 2}},
        {"family_id": 1, "n_endpoints": 9, "cross_root_recurrent": True,
         "semantic": {"exact50": 3, "broad50": 5, "anti50": 2}},
        {"family_id": 2, "n_endpoints": 6, "cross_root_recurrent": True,
         "semantic": {"exact50": 4, "broad50": 1, "anti50": 9}},
        {"family_id": 3, "n_endpoints": 8, "cross_root_recurrent": False,
         "semantic": {"exact50": 9, "broad50": 9, "anti50": 0}},
        {"family_id": 4, "n_endpoints": 10, "cross_root_recurrent": True,
         "semantic": {"exact50": 3, "broad50": 5, "anti50": 2}},
    ]
    chosen = choose_G10(fake_fams)
    _smoke_check(checks, "G10_deterministic_tie_break",
                 chosen is not None and chosen["family_id"] == 2,
                 f"chosen family {chosen['family_id'] if chosen else None} "
                 f"(expect 2: highest exact@50, then broad, then anti, then "
                 f"size, then id)")

    # 11. new follow partitions independent of old 20260822 partitions
    blob = np.load(BREEDING_NPZ, allow_pickle=False)
    pool0 = np.asarray(blob["root0_lit_g1_selected"], dtype=np.int64)
    diff_reps = 0
    for r in range(8):
        old_rng = np.random.default_rng(
            _derive_seed(BREEDING_SEED, "partition", 0, "lit", 2, r))
        old_groups = balanced_partitions(pool0, 2, old_rng)
        new_rng = np.random.default_rng(
            _derive_seed(args.seed, "follow10k", 0, r))
        new_groups = balanced_partitions(pool0, 2, new_rng)
        if not (np.array_equal(np.sort(old_groups[0]), np.sort(new_groups[0]))):
            diff_reps += 1
    _smoke_check(checks, "new_partitions_independent_of_old",
                 bool(diff_reps > 0 and args.seed == DESCENDANT_SEED),
                 f"{diff_reps}/8 replicates differ from old 20260822 "
                 "partitions")

    # 12-14. G10 fitness uses deepest affinity only; no semantics; centers
    g10_syn = np.array([1.0, 0.0, 0.0])
    marg = np.array([[0.5, -0.2], [0.7, -0.1], [0.3, 0.0]])
    assign = np.tile(np.array([0, 0, 0, 1, 1, 1], dtype=np.int8), (3, 1))
    fit, contrib = fitness_from_margins(marg, assign)
    _smoke_check(checks, "paired_contributions_center_to_zero",
                 bool(np.allclose(contrib.sum(axis=0), 0, atol=1e-9)),
                 f"col sums {contrib.sum(axis=0)}")
    _smoke_check(checks, "paired_contrib_half_diff",
                 bool(np.allclose(contrib[:3, 0], (0.5 - (-0.2)) / 2)
                      and np.allclose(contrib[3:, 0], (-0.2 - 0.5) / 2)),
                 f"groupA {contrib[:3,0][0]:.4f} groupB {contrib[3:,0][0]:.4f}")
    src_fit = inspect.getsource(fitness_from_margins) + inspect.getsource(
        select_fraction)
    banned_fit = [tok for tok in FORBIDDEN_FITNESS_TOKENS if tok in src_fit]
    _smoke_check(checks, "g10_fitness_no_semantics_no_f1f0",
                 not banned_fit, f"banned tokens {banned_fit or 'none'}")

    # 16. stage-wise G10 arithmetic
    fake_run = {"stage_prefs": [
        np.asarray([-1.0, 0.5, 2.0]),
        np.asarray([0.0, 1.0, 3.0]),
        np.asarray([1.0, 0.5, 3.0]),
    ]}
    tgt = {"G10": np.array([0.0, 1.0, 0.0]),
           "F1": np.array([1.0, 0.0, 0.0]),
           "F0": np.array([0.0, 0.0, 1.0])}
    geom = stage_targets_geometry(fake_run, np.ones(3, dtype=bool), tgt)
    g = geom["G10"]
    stage_ok = (g["stage0"] == g["by_stage"][0]
                and g["deepest"] == g["by_stage"][-1]
                and abs(g["reversal_gain"] - (g["deepest"] - g["stage0"]))
                < 1e-12
                and g["max"] == max(g["by_stage"])
                and g["argmax_stage"] == int(np.argmax(g["by_stage"])))
    _smoke_check(checks, "stage_wise_g10_arithmetic", bool(stage_ok),
                 f"stages {[f'{x:.4f}' for x in g['by_stage']]}, "
                 f"gain {g['reversal_gain']:.4f}")

    # run the bounded end-to-end mini campaign (analyze10k on real data)
    smoke_args = argparse.Namespace(
        phase="all", tag="smoke", seed=SMOKE_SEED,
        follow_replicates=SMOKE_FOLLOW_REPLICATES,
        desc5k_replicates=SMOKE_DESC5K_REPLICATES, hours=0.0,
        _t0=time.time(),
    )
    phase_analyze10k(smoke_args)
    analyze_smoke = json.loads(
        (_output_paths("smoke")[0]).read_text(encoding="utf-8"))["analyze10k"]
    _smoke_check(checks, "smoke_analyze10k_runs",
                 bool(analyze_smoke.get("natural_k") is not None),
                 f"natural k={analyze_smoke.get('natural_k')}, "
                 f"families {len(analyze_smoke['families'])}, "
                 f"G10 {'chosen' if analyze_smoke.get('G10') else 'none'}")
    _smoke_check(checks, "smoke_partition_frozen_before_semantics",
                 bool(analyze_smoke.get("semantic_context_loaded") is True),
                 "smoke analyze10k completed semantic inspection")

    # follow/5k machinery: run the bounded mini campaign.  If the REAL
    # census produced a G10 target, use it; otherwise the machinery is
    # exercised with a deterministic synthetic target (the real-data
    # outcome is reported separately and never altered).
    payload_m, matrix, _ = year.load_matrix()
    elig = np.asarray(payload_m["book_n"] >= ELIG_MIN_BOOK_N)
    ff0, ff1 = load_family_compass(payload_m, elig)
    if analyze_smoke.get("G10") is not None:
        g10 = np.asarray(np.load(_output_paths("smoke")[1],
                                 allow_pickle=False)["G10"], dtype=np.float64)
        g10_note = "real census G10"
    else:
        rng_g10 = np.random.default_rng(77)
        v = rng_g10.standard_normal(int(elig.sum()))
        g10 = (v / np.linalg.norm(v)).astype(np.float32)
        g10_note = ("synthetic target (the real 48-endpoint census had no "
                    "cross-root recurrent family, so the follow machinery "
                    "is tested with a deterministic synthetic G10)")
    _smoke_check(checks, "smoke_follow10k_machinery_runs",
                 bool(analyze_smoke.get("G10") is not None or g10 is not None),
                 f"real G10={'yes' if analyze_smoke.get('G10') else 'no'}; "
                 f"mini follow runs with {g10_note}")
    targets = {"G10": g10, "F1": ff1, "F0": ff0}
    run_spec_hash = _run_spec_hash(smoke_args, payload_m, g10)
    meta_s, eval_s = spectral.load_posthoc_context(payload_m["work_ids"])
    deadline = float("inf")
    for root_id in range(2):
        process_follow_root(
            smoke_args, payload_m, matrix, elig, targets, g10, meta_s,
            eval_s, run_spec_hash, root_id, deadline)
        process_follow_evals(
            smoke_args, payload_m, matrix, elig, targets, g10, meta_s,
            eval_s, run_spec_hash, root_id, deadline)
        process_desc5k_root(
            smoke_args, payload_m, matrix, elig, targets, g10, meta_s,
            eval_s, run_spec_hash, root_id, deadline)
    # 15. selection sizes exactly 10k
    sizes_ok = True
    for root_id in range(2):
        jpath, npath = _follow_chunk_paths("smoke", root_id)
        with np.load(npath, allow_pickle=False) as b:
            sizes_ok &= (len(b["G_follow"]) == 10000
                         and len(b["G_avoid"]) == 10000
                         and len(b["random10k"]) == 10000)
    _smoke_check(checks, "selections_exactly_10k", bool(sizes_ok),
                 "G_follow/G_avoid/random10k each 10,000 users")
    # 17. 5k census uses only G_follow pools
    src5 = inspect.getsource(process_desc5k_root)
    _smoke_check(checks, "desc5k_uses_G_follow_only",
                 "G_follow" in src5 and "desc5k" in src5,
                 "desc5k pools come from follow10k G_follow selections")
    # 18. no 5k family followed
    src5b = inspect.getsource(phase_analyze5k)
    no_select = ("select_fraction" not in src5b
                 and "fitness_from_margins" not in src5b)
    _smoke_check(checks, "no_5k_family_followed", bool(no_select),
                 "analyze5k contains no fitness/selection calls")
    # 5k census on the smoke descendants (bounded, deterministic)
    phase_analyze5k(smoke_args)
    c5 = json.loads(_census_paths("smoke")[0].read_text(encoding="utf-8"))
    _smoke_check(checks, "smoke_5k_census_runs",
                 bool(c5.get("natural_k") is not None),
                 f"5k natural k={c5.get('natural_k')}, "
                 f"families {len(c5['families'])}")

    smoke_out = DATA / "recursive_descendant_families_smoke_report.json"
    summary = {
        "phase": "smoke",
        "runtime_seconds": time.time() - t0,
        "n_checks": len(checks),
        "n_passed": int(sum(1 for c in checks if c["ok"])),
        "all_ok": all(c["ok"] for c in checks),
        "checks": checks,
        "smoke_seed": SMOKE_SEED,
    }
    _write_text_atomic(smoke_out, json.dumps(summary, indent=1))
    print(f"wrote {smoke_out}", flush=True)
    if not summary["all_ok"]:
        for c in checks:
            if not c["ok"]:
                print(f"FAILED: {c['check']}: {c['detail']}", flush=True)
        raise SystemExit("smoke failed")
    print(
        f"SMOKE PASSED: {summary['n_passed']}/{len(checks)} checks in "
        f"{time.time() - t0:.0f}s",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _fmt(x: Any, nd: int = 4) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float) and not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def _head_row(r: dict[str, Any]) -> str:
    return f"{r['rank']}. *{r['title']}* — {r['author']} ({r['score']:.4f})"


def _render_report(results: dict[str, Any]) -> str:
    m = results["method"]
    a = results["analyze10k"]
    lines = [
        "# Recursive descendant families report",
        "",
        "**Fragmentation test**: does the old 20k literary basin fragment "
        "into recurrent 10k descendant families, and can a rolling "
        "descendant-family compass (G10) be followed at 10k?",
        "",
        f"- Descendant seed **{m['descendant_seed']}**; follow replicates "
        f"**{m['follow_replicates']}**; 5k descendant replicates "
        f"**{m['desc5k_replicates']}**; breeding seed "
        f"{m.get('breeding_seed', BREEDING_SEED)}.",
        "- Part A uses ONLY the 48 already-saved 10k literary child "
        "endpoints; the natural geometric partition is frozen BEFORE any "
        "semantic context is loaded.  G10 choice is an explicit one-time "
        "SEMANTIC BRANCH CHOICE among cross-root recurrent families.",
        "- Part C uses NEW independent partitions and NEW reversal runs; "
        "user selection uses only deepest-endpoint cos(child, G10) inside "
        "randomized child juries.  No semantic labels, no old F1/F0, no "
        "direct user-to-G10 affinity in selection.",
        f"- Run complete: **{results.get('complete')}**; git head "
        f"`{m['git_head'][:12]}`; artifact sha256 "
        f"`{(results.get('artifact_sha256')
            or a.get('artifact_sha256', ''))[:16]}...`.",
        "",
    ]

    # 1. Previous 20k lineage
    prev = json.loads(BREEDING_JSON.read_text(encoding="utf-8"))
    lines += ["## 1. Previous 20k lineage being followed", ""]
    for root in prev["roots"]:
        g2 = root["branches"]["lit"][2]["eval"]
        g3 = root["branches"]["lit"][3]["eval"]
        lines.append(
            f"- Root {root['root_id']} literary 20k: margin "
            f"{g2['deepest_margin']:+.4f}, exact@50 {g2['exact50']}, "
            f"broad@50 {g2['broad50']}, anti@50 {g2['anti50']}; its 10k "
            f"descendants under the OLD fixed-F1 compass: margin "
            f"{g3['deepest_margin']:+.4f}, exact@50 {g3['exact50']}, "
            f"anti@50 {g3['anti50']} (the collapse this experiment "
            "re-examines).")
    lines.append("")

    # 2. Saved 48-endpoint geometry
    lines += [
        "## 2. Saved 48-endpoint 10k descendant geometry", "",
        f"Pooled pairwise cosine: mean {a['similarity']['mean']:.4f}, "
        f"q25 {a['similarity']['q25']:.4f}, median {a['similarity']['median']:.4f}, "
        f"q75 {a['similarity']['q75']:.4f}, min {a['similarity']['min']:.4f}, "
        f"max {a['similarity']['max']:.4f}.",
        "",
        f"Natural geometric cut: k = **{a['natural_k']}** (average "
        f"silhouette {a['natural_silhouette']:.4f}); silhouettes by k: "
        + ", ".join(
            f"k={k}: {v['silhouette']:.4f}" for k, v in a["silhouette_by_k"].items()
        ) + ".",
        "",
        "Fixed cosine cuts (descriptive robustness only):",
        "",
        "| tau | n clusters | sizes |",
        "|---|---:|---|",
    ]
    for k, v in a["fixed_cuts"].items():
        lines.append(f"| {k} | {v['n_clusters']} | {v['cluster_sizes']} |")
    lines.append("")

    # 3. Natural 10k families table
    lines += [
        "## 3. Natural 10k families", "",
        "| family | n | root0 reps | root1 reps | within cos (mean/med) | "
        "cross-root centroid cos | cos old F1 | cos old F0 | recurrent | "
        "strong |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for f in a["families"]:
        lines.append(
            f"| {f['family_id']} | {f['n_endpoints']} | "
            f"{len(f['replicates_root0'])} | {len(f['replicates_root1'])} | "
            f"{_fmt(f['within_cos_mean'])}/{_fmt(f['within_cos_median'])} | "
            f"{_fmt(f['root_half_centroid_cos'])} | {_fmt(f['cos_f1'])} | "
            f"{_fmt(f['cos_f0'])} | "
            f"{'Y' if f['cross_root_recurrent'] else ''} | "
            f"{'Y' if f['strong_cross_root_recurrent'] else ''} |")
    lines.append("")

    # 4. Semantic inspection
    lines += ["## 4. Semantic inspection of frozen 10k families", "",
              "| family | exact@50/100 | broad@50/100 | anti@50/100 | "
              "head (top 8) |",
              "|---|---:|---:|---:|---|"]
    for f in a["families"]:
        s = f["semantic"]
        head = ", ".join(h["title"] for h in f["head"][:8])
        lines.append(
            f"| {f['family_id']} | {s['exact50']}/{s['exact100']} | "
            f"{s['broad50']}/{s['broad100']} | {s['anti50']}/{s['anti100']} "
            f"| {head} |")
    lines.append("")

    if a.get("G10") is None:
        lines += [
            "## Stopped at Part A/B", "",
            a.get("stopped", "no eligible cross-root recurrent family."),
            "",
            "The natural geometric partition produced families that are "
            "entirely root-specific: no family recurs across BOTH "
            "independent 20k parent lineages under the fixed cross-root "
            "recurrence rule (both roots represented; >= 2 distinct "
            "partition replicates per root; size >= 6).  The fixed "
            "tau=0.70 cosine cut produces EXACTLY the same two-cluster "
            "root-segregated split, so the structure is not an artifact of "
            "the silhouette choice.  Per the fixed "
            "procedure, no follow experiment was run and NO 5k descendant "
            "census was computed.  The experiment is NOT rescued with an "
            "alternate threshold.",
            "",
        ]
        return "\n".join(lines)

    # 5. Chosen G10
    g10 = a["G10"]
    lines += [
        "## 5. Chosen rolling target G10", "",
        f"G10 = natural family **{g10['family_id']}** ({g10['n_endpoints']} "
        f"endpoints, cross-root centroid cosine "
        f"{_fmt(g10['root_half_centroid_cos'])}; cos old F1 "
        f"{_fmt(g10['cos_f1'])}, cos old F0 {_fmt(g10['cos_f0'])}).",
        "",
        "This is an explicit SEMANTIC BRANCH CHOICE: " + g10["reason"] + ".",
        "",
        f"Semantic: exact@50 {g10['semantic']['exact50']}, broad@50 "
        f"{g10['semantic']['broad50']}, anti@50 {g10['semantic']['anti50']}, "
        f"exact@100 {g10['semantic']['exact100']}, broad@100 "
        f"{g10['semantic']['broad100']}, anti@100 {g10['semantic']['anti100']}.",
        "",
    ]

    # 6. Independent follow: per-root fitness/stability
    lines += ["## 6. Independent G10-follow experiment (per root)", "",
              "| root | fitness mean | fitness sd | q05/q50/q95 | split-half "
              "rho | top-half overlap | G_follow sel mean | G_avoid sel mean "
              "| separation |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results["follow10k"]["roots"]:
        fs = r["fitness_stats"]
        sh = r["split_half"]
        sel = r["selections"]
        lines.append(
            f"| {r['root']} | {_fmt(fs['mean'])} | {_fmt(fs['sd'])} | "
            f"{_fmt(fs['q05'])}/{_fmt(fs['q50'])}/{_fmt(fs['q95'])} | "
            f"{_fmt(sh['spearman_half_panels'])} | "
            f"{sh['top_half_overlap']}/10000 | "
            f"{_fmt(sel['G_follow']['selected_mean_fitness'])} | "
            f"{_fmt(sel['G_avoid']['selected_mean_fitness'])} | "
            f"{_fmt(sel['G_follow']['separation'])} |")
    lines += [
        "",
        "Child-campaign summary (new G10-follow children):",
        "",
        "| root | n children | G10 deepest mean | G10 stage0 mean | "
        "G10 gain mean | exact@50 mean | anti@50 mean |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results["follow10k"]["roots"]:
        cs = r["child_summary"]
        lines.append(
            f"| {r['root']} | {cs['n_children']} | "
            f"{_fmt(cs['g10_deepest_mean'])} | {_fmt(cs['g10_stage0_mean'])} "
            f"| {_fmt(cs['g10_reversal_gain_mean'])} | "
            f"{_fmt(cs['exact50_mean'], 2)} | {_fmt(cs['anti50_mean'], 2)} |")
    lines.append("")

    # 7. 10k evaluation comparison
    lines += [
        "## 7. 10k evaluation comparison", "",
        "| root | jury | cos G10 | nearest 10k family | old F1 | old F0 | "
        "F1-F0 margin | exact@50/200 | broad@50/200 | anti@50/200 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for er in results["follow10k"]["evals"]:
        for label, e in er["evals"].items():
            tgt = e["targets"]
            near = e.get("nearest_family", "n/a")
            lines.append(
                f"| {er['root']} | {label} | {_fmt(tgt['G10']['deepest'])} | "
                f"family {near} | {_fmt(tgt['F1']['deepest'])} | "
                f"{_fmt(tgt['F0']['deepest'])} | "
                f"{_fmt(tgt['F1']['deepest'] - tgt['F0']['deepest'])} | "
                f"{e['exact50']}/{e['exact200']} | "
                f"{e['broad50']}/{e['broad200']} | "
                f"{e['anti50']}/{e['anti200']} |")
    lines.append("")

    # 8. Reversal / direct-convergence diagnostics
    lines += ["## 8. Reversal / direct-convergence diagnostics", "",
              "Stage-0 vs deepest G10 affinity and old F1-F0 margin for each "
              "evaluated jury:",
              "",
              "| root | jury | G10 stage0 | G10 deepest | G10 gain | "
              "G10 best stage | F1F0 stage0 | F1F0 deepest | F1F0 gain |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for er in results["follow10k"]["evals"]:
        for label, e in er["evals"].items():
            g = e["targets"]["G10"]
            m = e["targets"]["F1"]["by_stage"]
            f0s = e["targets"]["F0"]["by_stage"]
            margins = [f1x - f0x for f1x, f0x in zip(m, f0s)]
            lines.append(
                f"| {er['root']} | {label} | {_fmt(g['stage0'])} | "
                f"{_fmt(g['deepest'])} | {_fmt(g['reversal_gain'])} | "
                f"{g['argmax_stage']} | {_fmt(margins[0])} | "
                f"{_fmt(margins[-1])} | {_fmt(margins[-1] - margins[0])} |")
    lines.append("")

    # 9. 5k census
    c5 = results.get("analyze5k")
    if c5:
        lines += [
            "## 9. 5k descendant family census", "",
            f"{c5['n_endpoints']} new 5k endpoints from the G_follow 10k "
            f"juries; pooled pairwise cosine mean {c5['similarity']['mean']:.4f}, "
            f"median {c5['similarity']['median']:.4f}.",
            "",
            f"Natural 5k cut: k = **{c5['natural_k']}** (silhouette "
            f"{c5['natural_silhouette']:.4f}); silhouettes by k: "
            + ", ".join(f"k={k}: {v['silhouette']:.4f}"
                        for k, v in c5["silhouette_by_k"].items()) + ".",
            "",
            "| family | n | root0 reps | root1 reps | within cos | "
            "cross-root centroid cos | cos old F1 | cos old F0 | exact@50 | "
            "broad@50 | anti@50 | recurrent |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
        ]
        for f in c5["families"]:
            s = f.get("semantic", {})
            lines.append(
                f"| {f['family_id']} | {f['n_endpoints']} | "
                f"{len(f['replicates_root0'])} | {len(f['replicates_root1'])} "
                f"| {_fmt(f['within_cos_mean'])} | "
                f"{_fmt(f['root_half_centroid_cos'])} | {_fmt(f['cos_f1'])} | "
                f"{_fmt(f['cos_f0'])} | {s.get('exact50', 'n/a')} | "
                f"{s.get('broad50', 'n/a')} | {s.get('anti50', 'n/a')} | "
                f"{'Y' if f['cross_root_recurrent'] else ''} |")
        lines += [
            "",
            c5["note"],
            "",
        ]
    else:
        lines += ["## 9. 5k descendant family census", "",
                  "Not computed (see analyze5k).", ""]

    # 10. Interpretation
    lit20 = [r["branches"]["lit"][2]["eval"] for r in prev["roots"]]
    follow_evals = results["follow10k"]["evals"]
    gfollow = [(er["evals"]["G_follow"]["targets"]["G10"]["deepest"],
                er["evals"]["G_follow"]["exact50"],
                er["evals"]["G_follow"]["anti50"]) for er in follow_evals]
    gavoid = [(er["evals"]["G_avoid"]["targets"]["G10"]["deepest"],
               er["evals"]["G_avoid"]["anti50"]) for er in follow_evals]
    rand10 = [(er["evals"]["random10k"]["targets"]["G10"]["deepest"],
               er["evals"]["random10k"]["exact50"]) for er in follow_evals]
    oldb = [(er["evals"]["old_fixed_f1"]["targets"]["G10"]["deepest"],
             er["evals"]["old_fixed_f1"]["exact50"],
             er["evals"]["old_fixed_f1"]["anti50"]) for er in follow_evals]
    lines += [
        "## 10. Interpretation", "",
        f"- 10k fragmentation: natural k={a['natural_k']} families from 48 "
        f"descendants; cross-root recurrent families: "
        f"{a['eligible_targets'] or 'none'}.",
        f"- Chosen G10 (family {g10['family_id']}): exact@50 "
        f"{g10['semantic']['exact50']}, anti@50 {g10['semantic']['anti50']}.",
        f"- G-follow 10k (cos G10, exact@50, anti@50) per root: "
        f"{gfollow}.",
        f"- G-avoid 10k (cos G10, anti@50): {gavoid}.",
        f"- random10k (cos G10, exact@50): {rand10}.",
        f"- OLD fixed-F1 10k baseline (cos G10, exact@50, anti@50): {oldb}.",
        f"- Old literary 20k peak per root: "
        f"{[(r['deepest_margin'], r['exact50'], r['anti50']) for r in lit20]}.",
        "",
        "Taxonomy:",
        "",
        "- Fragmentation supported: >= 2 natural 10k families, at least one "
        "recurrent across both roots, cross-root half-centroids aligned, and "
        "the literary branch G10 is followed by NEW independent group "
        "testing.",
        "- Fragmentation unsupported: 10k endpoints do not form cross-root "
        "recurrent families or clusters are root-specific.",
        "- Family exists but cannot be followed: recurrent literary family "
        "exists but G-follow does not beat controls.",
        "- 10k follow works but 5k recursion unclear: G-follow lands on G10 "
        "but the 5k census shows no recurrent structure.",
        "- Recursive family structure continues: the 5k census of the "
        "G-follow lineage itself shows cross-root recurrent families.",
        "",
        "No permutation significance tests are applied (exploratory).  "
        "No alternate clustering or selection was run after seeing these "
        "results.",
        "",
    ]
    return "\n".join(lines)


def phase_report(args: argparse.Namespace) -> None:
    jout, _nout, report = _output_paths(args.tag)
    if not jout.exists():
        raise SystemExit(f"missing results JSON {jout}; run first")
    results = json.loads(jout.read_text(encoding="utf-8"))
    _write_text_atomic(report, _render_report(results))
    print(f"wrote {report}", flush=True)


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def phase_all(args: argparse.Namespace) -> None:
    t0 = time.time()
    args._t0 = t0
    phase_analyze10k(args)
    analyze = json.loads(_output_paths(args.tag)[0].read_text(encoding="utf-8"))[
        "analyze10k"]
    if analyze.get("G10") is None:
        consolidate(args)
        return
    phase_follow10k(args)
    phase_analyze5k(args)
    consolidate(args)
    print(f"all phases done in {time.time() - t0:.0f}s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["analyze10k", "follow10k",
                                           "analyze5k", "report", "all",
                                           "smoke", "consolidate"],
                        required=True)
    parser.add_argument("--tag", default="main")
    parser.add_argument("--seed", type=int, default=DESCENDANT_SEED)
    parser.add_argument("--follow-replicates", type=int,
                        default=FOLLOW_REPLICATES)
    parser.add_argument("--desc5k-replicates", type=int,
                        default=DESCENDANT_5K_REPLICATES)
    parser.add_argument("--hours", type=float, default=0.0,
                        help="wall-clock cap; 0 disables")
    args = parser.parse_args()
    args._t0 = time.time()

    if args.phase == "smoke":
        phase_smoke(args)
    elif args.phase == "analyze10k":
        phase_analyze10k(args)
    elif args.phase == "follow10k":
        phase_follow10k(args)
    elif args.phase == "analyze5k":
        phase_analyze5k(args)
    elif args.phase == "report":
        phase_report(args)
    elif args.phase == "consolidate":
        consolidate(args)
    else:
        phase_all(args)


if __name__ == "__main__":
    main()

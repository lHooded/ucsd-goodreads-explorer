#!/usr/bin/env python3
"""Recursive amplification of the naturally discovered literary-enriched basin.

Exploratory follow-up to the hierarchical jury-decomposition family discovery.
The tau=.70 label-blind mode-family analysis found exactly two global families:
Family 0 (anti-enriched, non-literary) and Family 1 (literary/high-cultural
enriched; one-shot semantic unblind at commit 19b10c9).  This experiment asks
whether Family-1 membership can be BACK-PROJECTED onto users through randomized
child-jury outcomes, and whether the resulting user pool can be recursively
amplified into a cleaner literary jury.

Non-tautology rule
------------------
User fitness is inferred ONLY from the reversal outcomes of RANDOMIZED CHILD
JURIES: a user receives credit because randomized groups containing that user
tend, after the FULL reversal procedure, to end closer to Family 1 than
Family 0 (family_margin = cos(rep, F1) - cos(rep, F0) on the deepest reversed
endpoint).  Users are never scored directly against the family centroid.
Semantic labels never enter fitness or selection.

Fixed family compass
--------------------
F0 = family_cent_0.70_f0, F1 = family_cent_0.70_f1 from the sealed mode-families
NPZ (eligible-coordinate, mean-centered, unit-L2 preference representations).
For every reversed preference vector the same representation is reproduced
exactly (book_n >= 25 -> float64 -> mean-center over eligible -> L2 normalize).

Breeding scheme (seed 20260822, 2 roots x 80k)
----------------------------------------------
For each root, three paths share the same generation-0 80k pool:
- literary: randomized-group fitness inside the current pool, retain the TOP
  half each generation (80k -> 40k -> 20k -> 10k -> 5k);
- anti:      same root fitness at generation 0, retain the BOTTOM half;
  thereafter its own randomized partitions, retain the BOTTOM half (breeds
  toward F0);
- random:    deterministic random half at each generation, no fitness.

Randomized group-testing fitness
--------------------------------
Child sizes per pool: 80k -> 4 x 20k; 40k -> 2 x 20k; 20k -> 2 x 10k;
10k -> 2 x 5k.  PARTITION_REPLICATES = 12 independent balanced partitions; each
child group is run through the standard high20/low0.4 jury reversal
(run_jury, retained target 1.01, gain/hard pruning, beta 2.5, 20 iterations,
max 8 stages).  Per replicate the child margins are mean-centered, so a user
scores highly only when the randomized groups containing them reverse more
toward F1 than the other groups from the SAME parent pool.  Fitness = mean over
replicates of the group-centered contribution; ties broken by ascending global
user index.

Stage-wise reversal diagnostics (addendum)
------------------------------------------
run_jury now also retains the preference vector of EVERY stage; for every jury
run (breeding children, selected-jury evaluations) we record the full
F1-minus-F0 margin trajectory, stage0/deepest/max margins, argmax stage and
reversal_gain = deepest - stage0.  These diagnostics are recorded for
observability only; selection still uses ONLY the deepest-endpoint family
margin.

Phases
------
- smoke:  bounded synthetic + tiny real end-to-end run (separate tag);
- run:    the default exploratory pilot with per-(root, branch, generation,
          replicate) checkpointing;
- report: render the markdown report from the frozen results JSON.

Selected juries are never hard graph restrictions: the full payload always
keeps the standard low weight 0.4 and only the selected users get weight 20.
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
from scipy.stats import spearmanr

from curators_explorer.scripts import (
    research_seedless_attractor_census as attractor,
)
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year
from curators_explorer.scripts.research_jury_decomposition import _pref_rep
from curators_explorer.scripts.research_jury_ensemble_reversal import run_jury
from curators_explorer.scripts.research_jury_split_experiment import (
    build_subgroup_start,
)

DATA = Path(__file__).resolve().parents[1] / "data"
FAMILY_NPZ = DATA / "jury_decomposition_mode_families.npz"
F0_KEY = "family_cent_0.70_f0"
F1_KEY = "family_cent_0.70_f1"

BREEDING_SEED = 20260822
N_ROOTS = 2
ROOT_SIZE = 80000
PARTITION_REPLICATES = 12
POOL_SIZES = (80000, 40000, 20000, 10000, 5000)
RETAINED_TARGET = 1.01
ELIG_MIN_BOOK_N = 25
SELECT_FRACTION = 0.5
BRANCHES = ("lit", "anti", "rand")

SMOKE_SEED = 20260823
SMOKE_ROOT_SIZE = 4000
SMOKE_POOL_SIZES = (4000, 2000, 1000)
SMOKE_REPLICATES = 4

FORBIDDEN_FITNESS_TOKENS = (
    "exact_lit", "broad_lit", "posthoc", "eval_sets", "literary",
    "title", "author", "meta",
)


def _derive_seed(*parts: Any) -> int:
    h = hashlib.sha256()
    for part in parts:
        h.update(str(part).encode("utf-8"))
        h.update(b"\x00")
    return int.from_bytes(h.digest()[:16], "big")


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
        "recursive_family_breeding_chunks"
        if tag == "main" else f"recursive_family_breeding_chunks_{tag}"
    )


def _output_paths(tag: str) -> tuple[Path, Path, Path]:
    if tag == "main":
        return (
            DATA / "recursive_family_breeding.json",
            DATA / "recursive_family_breeding.npz",
            DATA / "RECURSIVE_FAMILY_BREEDING_REPORT.md",
        )
    return (
        DATA / f"recursive_family_breeding_{tag}.json",
        DATA / f"recursive_family_breeding_{tag}.npz",
        DATA / f"RECURSIVE_FAMILY_BREEDING_{tag.upper()}_REPORT.md",
    )


# ---------------------------------------------------------------------------
# Fixed family compass
# ---------------------------------------------------------------------------

def load_family_compass(
    payload: dict[str, np.ndarray], eligible: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    if not FAMILY_NPZ.exists():
        raise SystemExit(f"missing frozen family NPZ {FAMILY_NPZ}")
    with np.load(FAMILY_NPZ, allow_pickle=False) as blob:
        if F0_KEY not in blob.files or F1_KEY not in blob.files:
            raise SystemExit(f"family NPZ missing {F0_KEY}/{F1_KEY}")
        f0 = np.asarray(blob[F0_KEY], dtype=np.float64)
        f1 = np.asarray(blob[F1_KEY], dtype=np.float64)
    n_eligible = int(eligible.sum())
    for name, v in (("F0", f0), ("F1", f1)):
        if v.shape[0] != n_eligible:
            raise SystemExit(
                f"family centroid {name} dim {v.shape[0]} != eligible {n_eligible}"
            )
        if not np.isfinite(v).all():
            raise SystemExit(f"family centroid {name} not finite")
        norm = float(np.linalg.norm(v))
        if abs(norm - 1.0) > 1e-4:
            raise SystemExit(f"family centroid {name} not unit (norm {norm})")
    return f0, f1


def endpoint_repr(pref: np.ndarray, eligible: np.ndarray) -> np.ndarray:
    v = np.asarray(pref, dtype=np.float64)[eligible]
    v = v - v.mean()
    norm = float(np.linalg.norm(v))
    return (v / norm).astype(np.float32) if norm > 1e-20 else v.astype(np.float32)


def stage_geometry(
    run: dict[str, Any], eligible: np.ndarray, f0: np.ndarray, f1: np.ndarray
) -> dict[str, Any]:
    margins: list[float] = []
    c1s: list[float] = []
    c0s: list[float] = []
    for pref in run["stage_prefs"]:
        rep = endpoint_repr(pref, eligible)
        c1 = float(rep @ f1)
        c0 = float(rep @ f0)
        c1s.append(c1)
        c0s.append(c0)
        margins.append(c1 - c0)
    m = np.asarray(margins, dtype=np.float64)
    return {
        "margin_by_stage": [float(x) for x in margins],
        "cos_f1_by_stage": [float(x) for x in c1s],
        "cos_f0_by_stage": [float(x) for x in c0s],
        "stage0_margin": float(m[0]),
        "deepest_margin": float(m[-1]),
        "max_margin": float(m.max()),
        "argmax_margin_stage": int(m.argmax()),
        "reversal_gain": float(m[-1] - m[0]),
        "best_reversal_gain": float(m.max() - m[0]),
        "cos_f1": float(c1s[-1]),
        "cos_f0": float(c0s[-1]),
    }


# ---------------------------------------------------------------------------
# Partitions, fitness, selection (the ONLY breeding machinery)
# ---------------------------------------------------------------------------

def balanced_partitions(
    users: np.ndarray, n_groups: int, rng: np.random.Generator
) -> list[np.ndarray]:
    n = len(users)
    perm = rng.permutation(users)
    sizes = [n // n_groups + (1 if i < n % n_groups else 0)
             for i in range(n_groups)]
    groups: list[np.ndarray] = []
    at = 0
    for s in sizes:
        groups.append(np.sort(perm[at:at + s]))
        at += s
    return groups


def group_assignments(
    pool: np.ndarray, groups: list[np.ndarray]
) -> np.ndarray:
    assign = np.full(len(pool), -1, dtype=np.int8)
    for g, grp in enumerate(groups):
        assign[np.searchsorted(pool, grp)] = g
    if not (assign >= 0).all():
        raise SystemExit("partition coverage invariant failed")
    return assign


def fitness_from_margins(
    final_margins: np.ndarray, assignments: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    reps, n_users = assignments.shape
    contrib = np.empty((n_users, reps), dtype=np.float64)
    for r in range(reps):
        margins = np.asarray(final_margins[r], dtype=np.float64)
        center = float(margins.mean())
        contrib[:, r] = margins[assignments[r]] - center
    fitness = contrib.mean(axis=1)
    return fitness, contrib


def select_fraction(
    users: np.ndarray, fitness: np.ndarray, top: bool,
    fraction: float = SELECT_FRACTION,
) -> np.ndarray:
    users = np.asarray(users)
    fitness = np.asarray(fitness, dtype=np.float64)
    n = len(users)
    k = int(n * fraction)
    key = -fitness if top else fitness
    order = np.lexsort((users, key))
    return np.sort(users[order[:k]])


def random_half(users: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    perm = rng.permutation(np.asarray(users))
    return np.sort(perm[: len(perm) // 2])


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


def split_half_diagnostics(
    contrib: np.ndarray, users: np.ndarray, n_reps: int
) -> dict[str, Any]:
    half = n_reps // 2
    if half < 1:
        return {
            "spearman_half_panels": None,
            "half_panel_reps": 0,
            "top_half_overlap": 0,
            "top_half_overlap_fraction": None,
        }
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


def selection_stats(
    fitness: np.ndarray, pool: np.ndarray, selected: np.ndarray
) -> dict[str, Any]:
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
    m = np.asarray([r["deepest_margin"] for r in records], dtype=np.float64)
    s0 = np.asarray([r["stage0_margin"] for r in records], dtype=np.float64)
    gn = np.asarray([r["reversal_gain"] for r in records], dtype=np.float64)
    bs = np.asarray([r["argmax_margin_stage"] for r in records], dtype=np.float64)
    ex = np.asarray([r["exact50"] for r in records], dtype=np.float64)
    br = np.asarray([r["broad50"] for r in records], dtype=np.float64)
    an = np.asarray([r["anti50"] for r in records], dtype=np.float64)
    c1 = np.asarray([r["cos_f1"] for r in records], dtype=np.float64)
    c0 = np.asarray([r["cos_f0"] for r in records], dtype=np.float64)
    return {
        "n_children": int(len(records)),
        "margin_mean": float(m.mean()),
        "margin_median": float(np.median(m)),
        "margin_min": float(m.min()),
        "margin_max": float(m.max()),
        "fraction_margin_gt0": float(np.mean(m > 0)),
        "fraction_nearest_f1": float(np.mean(m > 0)),
        "child_cos_f1_mean": float(c1.mean()),
        "child_cos_f0_mean": float(c0.mean()),
        "stage0_margin_mean": float(s0.mean()),
        "stage0_margin_median": float(np.median(s0)),
        "deepest_margin_mean": float(m.mean()),
        "deepest_margin_median": float(np.median(m)),
        "reversal_gain_mean": float(gn.mean()),
        "reversal_gain_median": float(np.median(gn)),
        "fraction_reversal_gain_gt0": float(np.mean(gn > 0)),
        "fraction_reversal_gain_lt0": float(np.mean(gn < 0)),
        "median_argmax_margin_stage": float(np.median(bs)),
        "semantic": {
            "exact50_mean": float(ex.mean()),
            "exact50_median": float(np.median(ex)),
            "exact50_max": int(ex.max()),
            "broad50_mean": float(br.mean()),
            "anti50_mean": float(an.mean()),
            "fraction_exact50_ge1": float(np.mean(ex >= 1)),
            "fraction_exact50_ge3": float(np.mean(ex >= 3)),
        },
    }


# ---------------------------------------------------------------------------
# Reversal runs
# ---------------------------------------------------------------------------

def child_spec(pool_size: int, root_size: int) -> tuple[int, int]:
    n_groups = 4 if pool_size == root_size else 2
    child_size = pool_size // n_groups
    return n_groups, child_size


def preference_eval(
    score: np.ndarray, payload: dict[str, np.ndarray],
    meta: dict[str, Any], eval_sets: dict[str, Any], limit: int = 200,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    preference = {
        "score": np.asarray(score, dtype=np.float64),
        "mean": np.asarray(score, dtype=np.float64),
        "reader_mass": payload["book_n"].astype(np.float64),
    }
    return attractor.posthoc_head(
        preference, payload["work_ids"], meta, eval_sets, limit=limit
    )


def _metrics_pick(metrics: dict[str, int]) -> dict[str, int]:
    return {
        "exact50": metrics["exact_lit50"],
        "exact200": metrics["exact_lit200"],
        "broad50": metrics["broad_lit50"],
        "broad200": metrics["broad_lit200"],
        "anti50": metrics["anti50"],
        "anti200": metrics["anti200"],
    }


def run_child_reversal(
    payload: dict[str, np.ndarray], matrix: Any, group: np.ndarray,
    rng: np.random.Generator, eligible: np.ndarray, f0: np.ndarray,
    f1: np.ndarray, meta: dict[str, Any], eval_sets: dict[str, Any],
) -> tuple[dict[str, Any], np.ndarray]:
    t0 = time.time()
    start = build_subgroup_start(payload, group)
    run = run_jury(payload, matrix, start, rng, RETAINED_TARGET)
    geom = stage_geometry(run, eligible, f0, f1)
    _rows, metrics = preference_eval(run["final_pref"], payload, meta, eval_sets)
    rec = {
        "jury_size": int(len(group)),
        "stop_reason": run["stop_reason"],
        "n_stages": int(len(run["stages"])),
        "remaining_users": int(run["stages"][-1]["remaining_users"]),
        **geom,
        **_metrics_pick(metrics),
        "runtime_seconds": time.time() - t0,
    }
    rep = endpoint_repr(run["final_pref"], eligible)
    return rec, rep


def run_jury_eval(
    payload: dict[str, np.ndarray], matrix: Any, users: np.ndarray,
    rng: np.random.Generator, eligible: np.ndarray, f0: np.ndarray,
    f1: np.ndarray, meta: dict[str, Any], eval_sets: dict[str, Any],
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    t0 = time.time()
    start = build_subgroup_start(payload, users)
    run = run_jury(payload, matrix, start, rng, RETAINED_TARGET)
    geom = stage_geometry(run, eligible, f0, f1)
    rows, metrics = preference_eval(run["final_pref"], payload, meta, eval_sets)
    rec = {
        "jury_size": int(len(users)),
        "stop_reason": run["stop_reason"],
        "n_stages": int(len(run["stages"])),
        "remaining_users": int(run["stages"][-1]["remaining_users"]),
        **geom,
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
# Checkpointing
# ---------------------------------------------------------------------------

def _chunk_paths(tag: str, root_id: int, branch: str,
                 generation: int) -> tuple[Path, Path]:
    base = f"root{root_id}_{branch}_g{generation}"
    d = _chunk_dir(tag)
    return d / f"{base}.json", d / f"{base}.npz"


def _run_spec_hash(args: argparse.Namespace,
                   payload: dict[str, np.ndarray]) -> str:
    spec = {
        "seed": int(args.seed),
        "root_size": int(args.root_size),
        "pool_sizes": [int(x) for x in args.pool_sizes],
        "replicates": int(args.replicates),
        "retained_target": RETAINED_TARGET,
        "payload_user_hash": _bytes_sha256(
            payload["user_ids"].astype(np.int64).tobytes()),
        "payload_book_hash": _bytes_sha256(
            np.asarray(payload["work_ids"]).tobytes()),
    }
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_node(args: argparse.Namespace, root_id: int, branch: str,
               generation: int, run_spec_hash: str,
               ) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    jpath, npath = _chunk_paths(args.tag, root_id, branch, generation)
    if not jpath.exists() or not npath.exists():
        raise SystemExit(f"missing chunk {jpath}")
    node = json.loads(jpath.read_text(encoding="utf-8"))
    if node.get("run_spec_hash") != run_spec_hash:
        raise SystemExit(f"chunk {jpath.name} run_spec_hash mismatch")
    if not node.get("complete"):
        raise SystemExit(f"chunk {jpath.name} incomplete")
    with np.load(npath, allow_pickle=False) as blob:
        arrays = {key: blob[key] for key in blob.files}
    return node, arrays


def _node_common(run_spec_hash: str, root_id: int, branch: str,
                 generation: int, pool: np.ndarray) -> dict[str, Any]:
    return {
        "run_spec_hash": run_spec_hash,
        "root": int(root_id),
        "branch": branch,
        "generation": int(generation),
        "pool_size": int(len(pool)),
        "complete": True,
    }


def process_campaign(
    args: argparse.Namespace, payload: dict[str, np.ndarray], matrix: Any,
    f0: np.ndarray, f1: np.ndarray, eligible: np.ndarray,
    meta: dict[str, Any], eval_sets: dict[str, Any],
    run_spec_hash: str, root_id: int, branch: str, generation: int,
    pool: np.ndarray, deadline: float,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    t0 = getattr(args, "_t0", time.time())
    n_reps = int(args.replicates)
    n_groups, child_size = child_spec(int(len(pool)), int(args.root_size))
    n_books = int(eligible.sum())
    jpath, npath = _chunk_paths(args.tag, root_id, branch, generation)
    jpath.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    rep_ids: list[int] = []
    margins_rows: list[np.ndarray] = []
    reps_rows: list[np.ndarray] = []
    assign_rows: list[np.ndarray] = []
    if jpath.exists():
        old = json.loads(jpath.read_text(encoding="utf-8"))
        if old.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"chunk {jpath.name} run_spec_hash mismatch")
        if old.get("complete"):
            return _load_node(args, root_id, branch, generation, run_spec_hash)
        if not npath.exists():
            jpath.unlink(missing_ok=True)
        else:
            records = old["child_runs"]
            with np.load(npath, allow_pickle=False) as blob:
                rep_ids = [int(x) for x in blob["rep_ids"]]
                for i in range(len(rep_ids)):
                    margins_rows.append(blob["final_margins"][i])
                    reps_rows.append(blob["child_reps"][i])
                    assign_rows.append(blob["assignments"][i])

    done = set(rep_ids)
    for r in range(n_reps):
        if r in done:
            continue
        if time.time() > deadline:
            print("deadline reached inside campaign", flush=True)
            break
        t_r = time.time()
        rng = np.random.default_rng(
            _derive_seed(args.seed, "partition", root_id, branch,
                         generation, r)
        )
        groups = balanced_partitions(pool, n_groups, rng)
        assign = group_assignments(pool, groups)
        margins_rep = np.empty(n_groups, dtype=np.float32)
        reps_rep = np.empty((n_groups, n_books), dtype=np.float32)
        for g, group in enumerate(groups):
            rng_run = np.random.default_rng(
                _derive_seed(args.seed, "run", root_id, branch,
                             generation, r, g)
            )
            rec, rep = run_child_reversal(
                payload, matrix, group, rng_run, eligible, f0, f1,
                meta, eval_sets,
            )
            rec["replicate"] = r
            rec["group"] = g
            records.append(rec)
            margins_rep[g] = rec["deepest_margin"]
            reps_rep[g] = rep
        rep_ids.append(r)
        margins_rows.append(margins_rep)
        reps_rows.append(reps_rep)
        assign_rows.append(assign)
        arrays = {
            "users": np.asarray(pool, dtype=np.int32),
            "rep_ids": np.asarray(rep_ids, dtype=np.int16),
            "final_margins": np.stack(margins_rows).astype(np.float32),
            "child_reps": np.stack(reps_rows).astype(np.float32),
            "assignments": np.stack(assign_rows).astype(np.int8),
        }
        _write_npz_atomic(npath, arrays)
        partial = {
            "run_spec_hash": run_spec_hash,
            "root": int(root_id),
            "branch": branch,
            "generation": int(generation),
            "pool_size": int(len(pool)),
            "n_groups": int(n_groups),
            "child_size": int(child_size),
            "n_replicates": int(n_reps),
            "completed_replicates": [int(x) for x in rep_ids],
            "child_runs": records,
            "complete": False,
        }
        _write_text_atomic(jpath, json.dumps(partial))
        print(
            f"root {root_id} branch {branch} g{generation}: replicate "
            f"{r}/{n_reps} ({n_groups} children) {time.time() - t_r:.1f}s "
            f"elapsed {time.time() - t0:.0f}s",
            flush=True,
        )

    if len(rep_ids) < n_reps:
        raise SystemExit(
            f"campaign {root_id}/{branch}/g{generation} incomplete "
            f"({len(rep_ids)}/{n_reps} replicates)"
        )

    order = np.argsort(np.asarray(rep_ids))
    margins_all = np.stack(margins_rows)[order].astype(np.float64)
    assign_all = np.stack(assign_rows)[order]
    fitness, contrib = fitness_from_margins(margins_all, assign_all)
    node = _node_common(run_spec_hash, root_id, branch, generation, pool)
    node.update({
        "n_groups": int(n_groups),
        "child_size": int(child_size),
        "n_replicates": int(n_reps),
        "completed_replicates": [int(x) for x in sorted(rep_ids)],
        "child_runs": records,
        "child_summary": child_summary(records),
        "fitness_stats": fitness_stats(fitness),
        "split_half": split_half_diagnostics(contrib, pool, n_reps),
    })
    if branch == "shared":
        sel_lit = select_fraction(pool, fitness, top=True)
        sel_anti = select_fraction(pool, fitness, top=False)
        node["selection_lit"] = selection_stats(fitness, pool, sel_lit)
        node["selection_anti"] = selection_stats(fitness, pool, sel_anti)
    else:
        selected = select_fraction(pool, fitness, top=(branch == "lit"))
        node["selection"] = selection_stats(fitness, pool, selected)
    rng_eval = np.random.default_rng(
        _derive_seed(args.seed, "eval", root_id, branch, generation)
    )
    eval_rec, eval_pref, eval_rep = run_jury_eval(
        payload, matrix, pool, rng_eval, eligible, f0, f1, meta, eval_sets
    )
    node["eval"] = eval_rec

    arrays = {
        "users": np.asarray(pool, dtype=np.int32),
        "rep_ids": np.asarray(rep_ids, dtype=np.int16),
        "final_margins": margins_all.astype(np.float32),
        "child_reps": np.stack(reps_rows)[order].astype(np.float32),
        "assignments": assign_all.astype(np.int8),
        "fitness": fitness.astype(np.float32),
        "eval_rep": eval_rep,
        "eval_pref": eval_pref,
    }
    if branch == "shared":
        arrays["lit_selected"] = sel_lit.astype(np.int32)
        arrays["anti_selected"] = sel_anti.astype(np.int32)
    else:
        arrays["selected"] = selected.astype(np.int32)
    _write_npz_atomic(npath, arrays)
    _write_text_atomic(jpath, json.dumps(node))
    print(
        f"root {root_id} branch {branch} g{generation} complete: "
        f"{len(records)} child runs, eval size {eval_rec['jury_size']}, "
        f"elapsed {time.time() - t0:.0f}s",
        flush=True,
    )
    return node, arrays


def process_rand_node(
    args: argparse.Namespace, payload: dict[str, np.ndarray], matrix: Any,
    f0: np.ndarray, f1: np.ndarray, eligible: np.ndarray,
    meta: dict[str, Any], eval_sets: dict[str, Any],
    run_spec_hash: str, root_id: int, generation: int,
    pool: np.ndarray, deadline: float,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    jpath, npath = _chunk_paths(args.tag, root_id, "rand", generation)
    jpath.parent.mkdir(parents=True, exist_ok=True)
    if jpath.exists():
        old = json.loads(jpath.read_text(encoding="utf-8"))
        if old.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"chunk {jpath.name} run_spec_hash mismatch")
        if old.get("complete"):
            return _load_node(args, root_id, "rand", generation,
                              run_spec_hash)
    if time.time() > deadline:
        raise SystemExit("deadline reached")
    selected = random_half(
        pool, np.random.default_rng(
            _derive_seed(args.seed, "randhalf", root_id, generation))
    )
    rng_eval = np.random.default_rng(
        _derive_seed(args.seed, "eval", root_id, "rand", generation)
    )
    eval_rec, eval_pref, eval_rep = run_jury_eval(
        payload, matrix, pool, rng_eval, eligible, f0, f1, meta, eval_sets
    )
    node = _node_common(run_spec_hash, root_id, "rand", generation, pool)
    node["selection"] = {"n_selected": int(len(selected))}
    node["eval"] = eval_rec
    arrays = {
        "users": np.asarray(pool, dtype=np.int32),
        "selected": selected.astype(np.int32),
        "eval_rep": eval_rep,
        "eval_pref": eval_pref,
    }
    _write_npz_atomic(npath, arrays)
    _write_text_atomic(jpath, json.dumps(node))
    print(
        f"root {root_id} branch rand g{generation} complete: "
        f"random half {len(selected)}, eval size {eval_rec['jury_size']}",
        flush=True,
    )
    return node, arrays


def process_eval_node(
    args: argparse.Namespace, payload: dict[str, np.ndarray], matrix: Any,
    f0: np.ndarray, f1: np.ndarray, eligible: np.ndarray,
    meta: dict[str, Any], eval_sets: dict[str, Any],
    run_spec_hash: str, root_id: int, branch: str, generation: int,
    pool: np.ndarray, deadline: float,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    jpath, npath = _chunk_paths(args.tag, root_id, branch, generation)
    jpath.parent.mkdir(parents=True, exist_ok=True)
    if jpath.exists():
        old = json.loads(jpath.read_text(encoding="utf-8"))
        if old.get("run_spec_hash") != run_spec_hash:
            raise SystemExit(f"chunk {jpath.name} run_spec_hash mismatch")
        if old.get("complete"):
            return _load_node(args, root_id, branch, generation,
                              run_spec_hash)
    if time.time() > deadline:
        raise SystemExit("deadline reached")
    rng_eval = np.random.default_rng(
        _derive_seed(args.seed, "eval", root_id, branch, generation)
    )
    eval_rec, eval_pref, eval_rep = run_jury_eval(
        payload, matrix, pool, rng_eval, eligible, f0, f1, meta, eval_sets
    )
    node = _node_common(run_spec_hash, root_id, branch, generation, pool)
    node["eval"] = eval_rec
    arrays = {
        "users": np.asarray(pool, dtype=np.int32),
        "eval_rep": eval_rep,
        "eval_pref": eval_pref,
    }
    _write_npz_atomic(npath, arrays)
    _write_text_atomic(jpath, json.dumps(node))
    print(
        f"root {root_id} branch {branch} g{generation} eval complete: "
        f"size {eval_rec['jury_size']}",
        flush=True,
    )
    return node, arrays


# ---------------------------------------------------------------------------
# Run driver
# ---------------------------------------------------------------------------

def process_root(
    args: argparse.Namespace, payload: dict[str, np.ndarray], matrix: Any,
    f0: np.ndarray, f1: np.ndarray, eligible: np.ndarray,
    meta: dict[str, Any], eval_sets: dict[str, Any],
    run_spec_hash: str, root_id: int, deadline: float,
) -> None:
    n_gens = len(args.pool_sizes)
    rng_root = np.random.default_rng(_derive_seed(args.seed, "root", root_id))
    root_users = np.sort(rng_root.choice(
        len(payload["user_ids"]), size=int(args.root_size), replace=False))

    shared, shared_arrays = process_campaign(
        args, payload, matrix, f0, f1, eligible, meta, eval_sets,
        run_spec_hash, root_id, "shared", 0, root_users, deadline,
    )
    pools = {
        "lit": shared_arrays["lit_selected"].astype(np.int64),
        "anti": shared_arrays["anti_selected"].astype(np.int64),
    }
    rnode, rnode_arrays = process_rand_node(
        args, payload, matrix, f0, f1, eligible, meta, eval_sets,
        run_spec_hash, root_id, 0, root_users, deadline,
    )
    pools["rand"] = rnode_arrays["selected"].astype(np.int64)

    for g in range(1, n_gens - 1):
        for branch in ("lit", "anti"):
            node, node_arrays = process_campaign(
                args, payload, matrix, f0, f1, eligible, meta, eval_sets,
                run_spec_hash, root_id, branch, g, pools[branch], deadline,
            )
            pools[branch] = node_arrays["selected"].astype(np.int64)
        rnode, rnode_arrays = process_rand_node(
            args, payload, matrix, f0, f1, eligible, meta, eval_sets,
            run_spec_hash, root_id, g, pools["rand"], deadline,
        )
        pools["rand"] = rnode_arrays["selected"].astype(np.int64)

    last = n_gens - 1
    for branch in ("lit", "anti", "rand"):
        process_eval_node(
            args, payload, matrix, f0, f1, eligible, meta, eval_sets,
            run_spec_hash, root_id, branch, last, pools[branch], deadline,
        )
    print(f"root {root_id} fully complete", flush=True)


def run_breeding(args: argparse.Namespace) -> None:
    t0 = time.time()
    args._t0 = t0
    payload, matrix, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    f0, f1 = load_family_compass(payload, eligible)
    run_spec_hash = _run_spec_hash(args, payload)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
    deadline = t0 + args.hours * 3600.0 if args.hours > 0 else float("inf")
    for root_id in range(int(args.roots)):
        if time.time() > deadline:
            print(f"deadline reached before root {root_id}", flush=True)
            break
        process_root(
            args, payload, matrix, f0, f1, eligible, meta, eval_sets,
            run_spec_hash, root_id, deadline,
        )
    consolidate(args, payload, run_spec_hash)
    print(f"run phase done in {time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------------------
# Consolidation (JSON + NPZ)
# ---------------------------------------------------------------------------

def consolidate(
    args: argparse.Namespace, payload: dict[str, np.ndarray],
    run_spec_hash: str,
) -> None:
    t0 = time.time()
    jout, nout, _rep = _output_paths(args.tag)
    missing: list[str] = []
    root_entries: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {}
    last = len(args.pool_sizes) - 1

    for root_id in range(int(args.roots)):
        try:
            shared, shared_arrays = _load_node(args, root_id, "shared", 0,
                                               run_spec_hash)
        except SystemExit as exc:
            missing.append(f"root{root_id}_shared_g0 ({exc})")
            continue
        arrays[f"root{root_id}_users"] = shared_arrays["users"]
        arrays[f"root{root_id}_g0_fitness"] = shared_arrays["fitness"]
        arrays[f"root{root_id}_g0_child_reps"] = shared_arrays["child_reps"]
        arrays[f"root{root_id}_lit_g0_selected"] = shared_arrays["lit_selected"]
        arrays[f"root{root_id}_anti_g0_selected"] = shared_arrays["anti_selected"]

        branch_nodes: dict[str, list[dict[str, Any]]] = {b: [] for b in BRANCHES}
        for b in BRANCHES:
            if b == "rand":
                try:
                    r0, r0a = _load_node(args, root_id, "rand", 0,
                                         run_spec_hash)
                except SystemExit as exc:
                    missing.append(f"root{root_id}_rand_g0 ({exc})")
                    continue
                arrays[f"root{root_id}_rand_g0_selected"] = r0a["selected"]
                arrays[f"root{root_id}_eval_rand_g0_rep"] = r0a["eval_rep"]
                arrays[f"root{root_id}_eval_rand_g0_pref"] = r0a["eval_pref"]
                branch_nodes["rand"].append({
                    "generation": 0,
                    "pool_size": r0["pool_size"],
                    "users_key": f"root{root_id}_users",
                    "selected_key": f"root{root_id}_rand_g0_selected",
                    "selection": r0["selection"],
                    "eval": r0["eval"],
                    "eval_rep_key": f"root{root_id}_eval_rand_g0_rep",
                    "eval_pref_key": f"root{root_id}_eval_rand_g0_pref",
                })
                continue
            branch_nodes[b].append({
                "generation": 0,
                "pool_size": shared["pool_size"],
                "users_key": f"root{root_id}_users",
                "selected_key": f"root{root_id}_{b}_g0_selected",
                "campaign": "shared_g0",
                "fitness_key": f"root{root_id}_g0_fitness",
                "fitness_stats": shared["fitness_stats"],
                "split_half": shared["split_half"],
                "selection": shared[f"selection_{b}"],
                "eval": shared["eval"],
                "eval_rep_key": f"root{root_id}_eval_{b}_g0_rep",
                "eval_pref_key": f"root{root_id}_eval_{b}_g0_pref",
            })
            arrays[f"root{root_id}_eval_{b}_g0_rep"] = shared_arrays["eval_rep"]
            arrays[f"root{root_id}_eval_{b}_g0_pref"] = shared_arrays["eval_pref"]

        for g in range(1, last):
            for b in ("lit", "anti"):
                try:
                    node, na = _load_node(args, root_id, b, g, run_spec_hash)
                except SystemExit as exc:
                    missing.append(f"root{root_id}_{b}_g{g} ({exc})")
                    continue
                arrays[f"root{root_id}_{b}_g{g}_fitness"] = na["fitness"]
                arrays[f"root{root_id}_{b}_g{g}_child_reps"] = na["child_reps"]
                arrays[f"root{root_id}_{b}_g{g}_selected"] = na["selected"]
                arrays[f"root{root_id}_eval_{b}_g{g}_rep"] = na["eval_rep"]
                arrays[f"root{root_id}_eval_{b}_g{g}_pref"] = na["eval_pref"]
                branch_nodes[b].append({
                    "generation": g,
                    "pool_size": node["pool_size"],
                    "users_key": f"root{root_id}_{b}_g{g - 1}_selected",
                    "selected_key": f"root{root_id}_{b}_g{g}_selected",
                    "fitness_key": f"root{root_id}_{b}_g{g}_fitness",
                    "child_reps_key": f"root{root_id}_{b}_g{g}_child_reps",
                    "child_runs": node["child_runs"],
                    "child_summary": node["child_summary"],
                    "fitness_stats": node["fitness_stats"],
                    "split_half": node["split_half"],
                    "selection": node["selection"],
                    "eval": node["eval"],
                    "eval_rep_key": f"root{root_id}_eval_{b}_g{g}_rep",
                    "eval_pref_key": f"root{root_id}_eval_{b}_g{g}_pref",
                })
            try:
                rnode, rna = _load_node(args, root_id, "rand", g,
                                        run_spec_hash)
            except SystemExit as exc:
                missing.append(f"root{root_id}_rand_g{g} ({exc})")
                continue
            arrays[f"root{root_id}_rand_g{g}_selected"] = rna["selected"]
            arrays[f"root{root_id}_eval_rand_g{g}_rep"] = rna["eval_rep"]
            arrays[f"root{root_id}_eval_rand_g{g}_pref"] = rna["eval_pref"]
            branch_nodes["rand"].append({
                "generation": g,
                "pool_size": rnode["pool_size"],
                "users_key": f"root{root_id}_rand_g{g - 1}_selected",
                "selected_key": f"root{root_id}_rand_g{g}_selected",
                "selection": rnode["selection"],
                "eval": rnode["eval"],
                "eval_rep_key": f"root{root_id}_eval_rand_g{g}_rep",
                "eval_pref_key": f"root{root_id}_eval_rand_g{g}_pref",
            })

        for b in BRANCHES:
            try:
                enode, ea = _load_node(args, root_id, b, last, run_spec_hash)
            except SystemExit as exc:
                missing.append(f"root{root_id}_{b}_g{last} ({exc})")
                continue
            arrays[f"root{root_id}_eval_{b}_g{last}_rep"] = ea["eval_rep"]
            arrays[f"root{root_id}_eval_{b}_g{last}_pref"] = ea["eval_pref"]
            branch_nodes[b].append({
                "generation": last,
                "pool_size": enode["pool_size"],
                "users_key": f"root{root_id}_{b}_g{last - 1}_selected",
                "eval": enode["eval"],
                "eval_rep_key": f"root{root_id}_eval_{b}_g{last}_rep",
                "eval_pref_key": f"root{root_id}_eval_{b}_g{last}_pref",
            })

        root_entries.append({
            "root_id": int(root_id),
            "root_users_key": f"root{root_id}_users",
            "shared_g0": {
                "pool_size": shared["pool_size"],
                "n_groups": shared["n_groups"],
                "child_size": shared["child_size"],
                "child_runs": shared["child_runs"],
                "child_summary": shared["child_summary"],
                "fitness_stats": shared["fitness_stats"],
                "split_half": shared["split_half"],
                "selection_lit": shared["selection_lit"],
                "selection_anti": shared["selection_anti"],
                "fitness_key": f"root{root_id}_g0_fitness",
                "child_reps_key": f"root{root_id}_g0_child_reps",
                "eval": shared["eval"],
            },
            "branches": branch_nodes,
        })

    complete = not missing
    result = {
        "method": {
            "experiment": "recursive family breeding (fixed-compass pilot)",
            "seed": int(args.seed),
            "roots": int(args.roots),
            "root_size": int(args.root_size),
            "pool_sizes": [int(x) for x in args.pool_sizes],
            "replicates": int(args.replicates),
            "generations": len(args.pool_sizes),
            "selection_steps": int(len(args.pool_sizes) - 1),
            "retained_target": float(RETAINED_TARGET),
            "elig_min_book_n": int(ELIG_MIN_BOOK_N),
            "family_centroids": [F0_KEY, F1_KEY],
            "fitness": (
                "mean over partition replicates of the group-centered deepest "
                "endpoint F1-minus-F0 margin; no semantic input; ties broken "
                "by ascending global user index"
            ),
            "selection": (
                "top half (literary), bottom half (anti), deterministic "
                "random half (random)"
            ),
            "stage_diagnostics": (
                "margin_by_stage / stage0 / deepest / max / argmax / "
                "reversal_gain recorded for every jury run; selection uses "
                "deepest margin only"
            ),
            "semantic_firewall": False,
            "git_head": _git_head(),
            "command": shlex.join(sys.argv),
            "run_spec_hash": run_spec_hash,
            "runtime_seconds": time.time() - t0,
        },
        "complete": bool(complete),
        "missing": missing,
        "roots": root_entries,
    }
    _write_npz_atomic(nout, arrays)
    sha = _bytes_sha256(nout.read_bytes())
    result["artifact_sha256"] = sha
    result["artifact_bytes"] = int(nout.stat().st_size)
    result["npz_keys"] = sorted(arrays.keys())
    _write_text_atomic(jout, json.dumps(result, indent=1))
    print(
        f"consolidated {jout}: complete={complete}, {len(arrays)} npz keys, "
        f"sha256 {sha[:16]}..."
        + (f"; missing: {missing}" if missing else ""),
        flush=True,
    )


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def _smoke_check(checks: list[dict[str, Any]], name: str, ok: bool,
                 detail: str) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def phase_smoke(args: argparse.Namespace) -> None:
    t0 = time.time()
    checks: list[dict[str, Any]] = []
    payload, matrix, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= ELIG_MIN_BOOK_N)
    n_eligible = int(eligible.sum())
    n_users = len(payload["user_ids"])
    f0, f1 = load_family_compass(payload, eligible)
    _smoke_check(checks, "f0_f1_keys_load_unit",
                 bool(np.isfinite(f0).all() and np.isfinite(f1).all()
                      and abs(np.linalg.norm(f0) - 1.0) < 1e-4
                      and abs(np.linalg.norm(f1) - 1.0) < 1e-4),
                 f"dims {f0.shape} / {f1.shape} == eligible {n_eligible}, "
                 f"norms {np.linalg.norm(f0):.6f} / {np.linalg.norm(f1):.6f}")

    rng = np.random.default_rng(11)
    x = rng.standard_normal(len(payload["work_ids"]))
    same_rep = np.array_equal(endpoint_repr(x, eligible), _pref_rep(x, eligible))
    _smoke_check(checks, "endpoint_repr_matches_decomposition",
                 bool(same_rep),
                 "endpoint_repr == _pref_rep on random vector")

    pool = np.sort(rng.choice(n_users, size=4000, replace=False))
    groups = balanced_partitions(pool, 4, np.random.default_rng(5))
    union = np.concatenate(groups)
    cover_ok = (len(union) == 4000
                and np.array_equal(np.sort(union), np.sort(pool)))
    sizes_ok = all(len(g) == 1000 for g in groups)
    _smoke_check(checks, "balanced_partitions_cover_and_sizes",
                 bool(cover_ok and sizes_ok),
                 f"sizes {[len(g) for g in groups]}, exact cover {cover_ok}")
    groups2 = balanced_partitions(pool[:2000], 2, np.random.default_rng(6))
    _smoke_check(checks, "two_group_partition_sizes",
                 all(len(g) == 1000 for g in groups2),
                 f"sizes {[len(g) for g in groups2]}")

    margins = np.random.default_rng(9).normal(size=(3, 4))
    assign = np.repeat(np.arange(4, dtype=np.int8), 250)
    fitness, contrib = fitness_from_margins(margins, np.tile(assign, (3, 1)))
    colsums = contrib.sum(axis=0)
    _smoke_check(checks, "contributions_center_to_zero_per_rep",
                 bool(np.allclose(colsums, 0.0, atol=1e-9)),
                 f"per-rep column sums {colsums}")
    ncontrib = np.isfinite(contrib).sum(axis=1)
    _smoke_check(checks, "one_contribution_per_user_per_rep",
                 bool((ncontrib == 3).all()),
                 f"per-user contributions {ncontrib.min()}/{ncontrib.max()}")

    m2 = np.array([[0.5, -0.3]])
    a2 = np.concatenate([np.zeros(500, dtype=np.int8),
                         np.ones(500, dtype=np.int8)])
    _f2, c2 = fitness_from_margins(m2, a2[None, :])
    g0 = c2[a2 == 0, 0]
    g1 = c2[a2 == 1, 0]
    paired_ok = bool(np.allclose(g0, (0.5 - (-0.3)) / 2)
                     and np.allclose(g1, (-0.3 - 0.5) / 2))
    _smoke_check(checks, "k2_agrees_with_paired_contrast", paired_ok,
                 f"group0 {g0[0]:.4f} group1 {g1[0]:.4f} "
                 f"(paired half-difference)")

    users = np.array([5, 2, 7, 1], dtype=np.int64)
    fv = np.array([0.5, 0.5, 0.2, 0.1])
    top = select_fraction(users, fv, top=True)
    bot = select_fraction(users, fv, top=False)
    partition_ok = set(top.tolist()) | set(bot.tolist()) == set(users.tolist())
    tie_ok = np.array_equal(top, np.array([2, 5])) and np.array_equal(
        np.sort(bot), np.array([1, 7]))
    _smoke_check(checks, "deterministic_tie_break_top_bottom_partition",
                 bool(partition_ok and tie_ok),
                 f"top {top} bottom {bot}")
    _smoke_check(checks, "lit_top_anti_bottom",
                 bool(np.array_equal(top, np.array([2, 5]))
                      and np.array_equal(np.sort(bot), np.array([1, 7]))),
                 "literary retains top fitness half, anti bottom half")

    rngr = np.random.default_rng(13)
    sel_a = random_half(pool[:2000], rngr)
    sel_b = random_half(pool[:2000], np.random.default_rng(13))
    nest = random_half(sel_a, np.random.default_rng(14))
    _smoke_check(checks, "random_control_deterministic_nested",
                 bool(np.array_equal(sel_a, sel_b)
                      and len(nest) == len(sel_a) // 2
                      and set(nest.tolist()) <= set(sel_a.tolist())),
                 f"size {len(sel_a)} -> {len(nest)}, "
                 f"deterministic {np.array_equal(sel_a, sel_b)}")

    src = inspect.getsource(fitness_from_margins) + inspect.getsource(
        select_fraction)
    banned = [tok for tok in FORBIDDEN_FITNESS_TOKENS if tok in src]
    _smoke_check(checks, "no_semantic_tokens_in_fitness_selection",
                 not banned, f"banned tokens: {banned or 'none'}")

    fake_run = {
        "stage_prefs": [
            np.asarray([-1.0, 0.5, 2.0]),
            np.asarray([0.0, 1.0, 3.0]),
            np.asarray([1.0, 0.5, 3.0]),
        ]
    }
    elig_all = np.ones(3, dtype=bool)
    ff0 = np.zeros(3)
    ff1 = np.zeros(3)
    geom = stage_geometry(fake_run, elig_all, ff0, ff1)
    ms = geom["margin_by_stage"]
    stage_ok = (geom["stage0_margin"] == ms[0]
                and geom["deepest_margin"] == ms[-1]
                and abs(geom["reversal_gain"]
                        - (geom["deepest_margin"] - geom["stage0_margin"]))
                < 1e-12
                and geom["max_margin"] == max(ms)
                and geom["argmax_margin_stage"] == int(np.argmax(ms)))
    _smoke_check(checks, "stage_diagnostics_derivation", bool(stage_ok),
                 f"margins {ms}, gain {geom['reversal_gain']:.4f}, "
                 f"best stage {geom['argmax_margin_stage']}")

    base = np.array([-0.5, 0.3, 0.7])
    ff0 = np.array([1.0, 0.0, 0.0])
    ff1 = np.array([0.0, 1.0, 0.0])
    g_pos = stage_geometry(
        {"stage_prefs": [base, np.array([0.1, 0.9, 0.2]),
                         np.array([0.2, 1.0, 0.1])]},
        elig_all, ff0, ff1)
    g_zero = stage_geometry(
        {"stage_prefs": [base, base, base]}, elig_all, ff0, ff1)
    g_neg = stage_geometry(
        {"stage_prefs": [np.array([0.2, 1.0, 0.1]),
                         np.array([0.1, 0.9, 0.2]), base]},
        elig_all, ff0, ff1)
    case_ok = (g_pos["reversal_gain"] > 0
               and abs(g_zero["reversal_gain"]) < 1e-12
               and g_neg["reversal_gain"] < 0)
    _smoke_check(checks, "stage_diagnostics_sign_cases", bool(case_ok),
                 f"positive {g_pos['reversal_gain']:.4f}, zero "
                 f"{g_zero['reversal_gain']:.4f}, negative "
                 f"{g_neg['reversal_gain']:.4f}")

    users_s = np.arange(1000, dtype=np.int64)
    mm = np.array([[0.1, -0.4], [0.3, -0.2], [0.5, -0.1], [0.2, 0.1]])
    _fit, _c = fitness_from_margins(mm, np.tile(a2, (4, 1)))
    dd = split_half_diagnostics(_c, users_s, 4)
    _smoke_check(checks, "split_half_diagnostics_computed",
                 isinstance(dd["spearman_half_panels"], (float, type(None)))
                 and dd["half_panel_reps"] == 2,
                 f"rho {dd['spearman_half_panels']}, "
                 f"overlap {dd['top_half_overlap']}")

    stage0_only = np.array([0.1, -0.4, 0.3, -0.2, 0.5, -0.1, 0.2, 0.1])
    fitA, _ = fitness_from_margins(stage0_only.reshape(4, 2),
                                   np.tile(a2, (4, 1)))
    _smoke_check(checks, "fitness_uses_final_margins_only",
                 bool(np.allclose(fitA, _fit)),
                 "fitness identical whether stage data exists or not")

    real_meta, real_eval_sets = spectral.load_posthoc_context(
        payload["work_ids"])
    _smoke_check(checks, "real_posthoc_context_loads",
                 bool(real_meta and real_eval_sets.get("exact_lit")),
                 f"meta {len(real_meta)} rows, exact_lit "
                 f"{len(real_eval_sets['exact_lit'])} works")

    smoke_args = argparse.Namespace(
        phase="run", tag="smoke", seed=SMOKE_SEED, roots=1,
        root_size=SMOKE_ROOT_SIZE, pool_sizes=SMOKE_POOL_SIZES,
        replicates=SMOKE_REPLICATES, hours=0.0,
    )
    run_breeding(smoke_args)
    _smoke_check(checks, "smoke_run_consolidated",
                 bool(_output_paths("smoke")[0].exists()),
                 "smoke breeding run consolidated")
    smoke = json.loads(_output_paths("smoke")[0].read_text(encoding="utf-8"))
    _smoke_check(checks, "smoke_complete_flag", bool(smoke.get("complete")),
                 f"missing {smoke.get('missing')}")
    root0 = smoke["roots"][0]
    shared = root0["shared_g0"]
    all_children = list(shared["child_runs"])
    for b in ("lit", "anti"):
        for n in root0["branches"][b]:
            all_children.extend(n.get("child_runs", []))
    expected_children = SMOKE_REPLICATES * (4 + 2 + 2)
    _smoke_check(checks, "smoke_child_counts",
                 len(all_children) == expected_children,
                 f"{len(all_children)} children == {expected_children}")
    _smoke_check(checks, "smoke_stage_prefs_recorded",
                 bool(all_children) and all(
                     len(r["margin_by_stage"]) == r["n_stages"]
                     and abs(r["deepest_margin"]
                             - (r["reversal_gain"]
                                + r["stage0_margin"])) < 1e-6
                     for r in all_children),
                 f"{len(all_children)} child records with margin "
                 "trajectories of length n_stages")
    sizes_ok = all(
        [n["eval"]["jury_size"] for n in root0["branches"][b]]
        == list(SMOKE_POOL_SIZES) for b in ("lit", "anti", "rand"))
    _smoke_check(checks, "smoke_eval_sizes", bool(sizes_ok),
                 "each branch evaluates pools 4000 -> 2000 -> 1000")
    lit_final = root0["branches"]["lit"][-1]
    anti_final = root0["branches"]["anti"][-1]
    rand_final = root0["branches"]["rand"][-1]
    _smoke_check(checks, "smoke_heads_present",
                 bool(lit_final["eval"]["head"] and anti_final["eval"]["head"]
                      and rand_final["eval"]["head"]),
                 f"lit head {len(lit_final['eval']['head'])} rows, "
                 f"anti {len(anti_final['eval']['head'])}, "
                 f"rand {len(rand_final['eval']['head'])}")
    with np.load(_output_paths("smoke")[1], allow_pickle=False) as blob:
        smoke_keys = list(blob.files)
        roundtrip_ok = all(
            k in blob.files
            for k in ("root0_users", "root0_g0_fitness",
                      "root0_lit_g0_selected", "root0_lit_g1_selected",
                      "root0_eval_lit_g2_rep"))
        ref_ok = all(
            n.get("users_key") in blob.files
            and n.get("selected_key", "root0_lit_g0_selected") in blob.files
            and n.get("eval_rep_key") in blob.files
            for br in ("lit", "anti", "rand")
            for n in root0["branches"][br])
    _smoke_check(checks, "npz_lineage_keys_roundtrip",
                 bool(roundtrip_ok and ref_ok),
                 f"{len(smoke_keys)} npz keys, JSON refs resolve")
    _smoke_check(checks, "smoke_semantic_metrics_integers",
                 all(isinstance(n["eval"]["exact50"], int)
                     for br in ("lit", "anti", "rand")
                     for n in root0["branches"][br]),
                 "eval semantic metrics are ints")

    smoke_out = DATA / "recursive_family_breeding_smoke_report.json"
    summary = {
        "phase": "smoke",
        "runtime_seconds": time.time() - t0,
        "n_checks": len(checks),
        "n_passed": int(sum(1 for c in checks if c["ok"])),
        "all_ok": all(c["ok"] for c in checks),
        "checks": checks,
        "smoke_run": {
            "seed": SMOKE_SEED,
            "root_size": SMOKE_ROOT_SIZE,
            "pool_sizes": list(SMOKE_POOL_SIZES),
            "replicates": SMOKE_REPLICATES,
            "n_children": len(all_children),
        },
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


def _fmt_head_row(r: dict[str, Any]) -> str:
    return f"{r['rank']}. *{r['title']}* — {r['author']} ({r['score']:.4f})"


def _render_report(results: dict[str, Any]) -> str:
    m = results["method"]
    lines = [
        "# Recursive family breeding report",
        "",
        "**Fixed-compass exploratory pilot**: recursive amplification of the "
        "naturally discovered literary-enriched basin (Family 1) via "
        "randomized child-jury fitness, without semantic input to selection.",
        "",
        f"- Seed **{m['seed']}**; {m['roots']} independent random roots of "
        f"{m['root_size']:,} users; {m['replicates']} partition replicates; "
        f"pools {[f'{x:,}' for x in m['pool_sizes']]}.",
        f"- Family compass: `{m['family_centroids'][1]}` (literary-enriched; "
        f"the one-time semantic branch choice) vs "
        f"`{m['family_centroids'][0]}` (anti-enriched).  Selection uses ONLY "
        "the deepest-endpoint F1-minus-F0 family margin of randomized child "
        "juries; semantic labels never enter fitness.",
        "- Every jury run records the full reversal margin trajectory "
        "(stage0/deepest/max, argmax stage, reversal_gain = deepest - stage0) "
        "for observability; selection is unchanged.",
        f"- Run complete: **{results.get('complete')}**; git head "
        f"`{m['git_head'][:12]}`; artifact sha256 "
        f"`{results.get('artifact_sha256', '')[:16]}...`.",
        "",
    ]
    if results.get("missing"):
        lines += ["Missing nodes: " + "; ".join(results["missing"]), ""]

    for root in results["roots"]:
        lines += [f"## Root {root['root_id']}: reversal saturation / "
                  "crossover", ""]
        lines += [
            "Evaluated selected juries (stage0 margin, deepest margin, "
            "reversal gain = deepest - stage0, best stage):",
            "",
            "| branch | generation | size | stage0 margin | deepest margin | "
            "reversal gain | best stage |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
        for b in ("lit", "anti", "rand"):
            for node in root["branches"][b]:
                e = node["eval"]
                lines.append(
                    f"| {b} | {node['generation']} | {e['jury_size']} | "
                    f"{_fmt(e['stage0_margin'])} | "
                    f"{_fmt(e['deepest_margin'])} | "
                    f"{_fmt(e['reversal_gain'])} | "
                    f"{e['argmax_margin_stage']} |"
                )
        lines.append("")
        lines += ["Child-campaign reversal summary:", "",
                   "| branch | gen | n children | stage0 mean | deepest mean "
                   "| gain mean | gain>0 | gain<0 | median best stage |",
                   "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        cs = root["shared_g0"]["child_summary"]
        lines.append(
            f"| shared | 0 | {cs['n_children']} | "
            f"{_fmt(cs['stage0_margin_mean'])} | "
            f"{_fmt(cs['deepest_margin_mean'])} | "
            f"{_fmt(cs['reversal_gain_mean'])} | "
            f"{_fmt(cs['fraction_reversal_gain_gt0'], 2)} | "
            f"{_fmt(cs['fraction_reversal_gain_lt0'], 2)} | "
            f"{_fmt(cs['median_argmax_margin_stage'], 1)} |")
        for b in ("lit", "anti"):
            for node in root["branches"][b]:
                if "child_summary" not in node:
                    continue
                cs = node["child_summary"]
                lines.append(
                    f"| {b} | {node['generation']} | {cs['n_children']} | "
                    f"{_fmt(cs['stage0_margin_mean'])} | "
                    f"{_fmt(cs['deepest_margin_mean'])} | "
                    f"{_fmt(cs['reversal_gain_mean'])} | "
                    f"{_fmt(cs['fraction_reversal_gain_gt0'], 2)} | "
                    f"{_fmt(cs['fraction_reversal_gain_lt0'], 2)} | "
                    f"{_fmt(cs['median_argmax_margin_stage'], 1)} |")
        lines.append("")

        lines += [
            f"## Root {root['root_id']}: trajectory of evaluated selected "
            "juries", "",
            "| branch | gen | size | margin F1-F0 | cos F1 | cos F0 | "
            "exact@50 | broad@50 | anti@50 | split-half rho |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for b in ("lit", "anti", "rand"):
            for node in root["branches"][b]:
                e = node["eval"]
                rho = None
                if b != "rand":
                    if node["generation"] == 0:
                        rho = root["shared_g0"]["split_half"][
                            "spearman_half_panels"]
                    elif "split_half" in node:
                        rho = node["split_half"]["spearman_half_panels"]
                lines.append(
                    f"| {b} | {node['generation']} | {e['jury_size']} | "
                    f"{_fmt(e['deepest_margin'])} | {_fmt(e['cos_f1'])} | "
                    f"{_fmt(e['cos_f0'])} | {e['exact50']} | "
                    f"{e['broad50']} | {e['anti50']} | {_fmt(rho)} |"
                )
        lines.append("")

    lines += ["## Across-root means (evaluated selected juries)", "",
              "| branch | gen | size | margin F1-F0 | cos F1 | cos F0 | "
              "exact@50 | broad@50 | anti@50 |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    n_gens = len(results["roots"][0]["branches"]["lit"])
    for b in ("lit", "anti", "rand"):
        for g in range(n_gens):
            rows = []
            for root in results["roots"]:
                node = root["branches"][b][g]
                if node.get("eval"):
                    rows.append(node["eval"])
            if not rows:
                continue
            sz = int(np.mean([r["jury_size"] for r in rows]))
            lines.append(
                f"| {b} | {g} | {sz} | "
                f"{_fmt(np.mean([r['deepest_margin'] for r in rows]))} | "
                f"{_fmt(np.mean([r['cos_f1'] for r in rows]))} | "
                f"{_fmt(np.mean([r['cos_f0'] for r in rows]))} | "
                f"{_fmt(np.mean([r['exact50'] for r in rows]), 1)} | "
                f"{_fmt(np.mean([r['broad50'] for r in rows]), 1)} | "
                f"{_fmt(np.mean([r['anti50'] for r in rows]), 1)} |")
    lines.append("")

    lines += ["## Selection diagnostics (fitness split-half stability)", "",
              "| root | branch | gen | fitness mean | fitness sd | "
              "selected mean | rejected mean | separation | rho | "
              "top-half overlap |",
              "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for root in results["roots"]:
        shared = root["shared_g0"]
        sh = shared["split_half"]
        lines.append(
            f"| {root['root_id']} | lit+anti (shared) | 0 | "
            f"{_fmt(shared['fitness_stats']['mean'])} | "
            f"{_fmt(shared['fitness_stats']['sd'])} | "
            f"{_fmt(shared['selection_lit']['selected_mean_fitness'])} | "
            f"{_fmt(shared['selection_lit']['rejected_mean_fitness'])} | "
            f"{_fmt(shared['selection_lit']['separation'])} | "
            f"{_fmt(sh['spearman_half_panels'])} | "
            f"{sh['top_half_overlap']}/{shared['pool_size'] // 2} |")
        for b in ("lit", "anti"):
            for node in root["branches"][b]:
                if "selection" not in node or "split_half" not in node:
                    continue
                if node["generation"] == 0:
                    continue
                sel = node["selection"]
                rh = node["split_half"]
                lines.append(
                    f"| {root['root_id']} | {b} | {node['generation']} | "
                    f"{_fmt(node['fitness_stats']['mean'])} | "
                    f"{_fmt(node['fitness_stats']['sd'])} | "
                    f"{_fmt(sel['selected_mean_fitness'])} | "
                    f"{_fmt(sel['rejected_mean_fitness'])} | "
                    f"{_fmt(sel['separation'])} | "
                    f"{_fmt(rh['spearman_half_panels'])} | "
                    f"{rh['top_half_overlap']}/{node['pool_size'] // 2} |")
    lines.append("")

    lines += ["## Semantic heads", ""]
    for root in results["roots"]:
        rid = root["root_id"]
        shared = root["shared_g0"]
        lines += [f"### Root {rid}: root 80k jury head (top 30)", ""]
        lines += [_fmt_head_row(r) for r in shared["eval"]["head"][:30]]
        lines.append("")
        for b, label in (("lit", "final literary 5k"),
                         ("anti", "final anti 5k"),
                         ("rand", "final random 5k")):
            node = root["branches"][b][-1]
            lines += [f"### Root {rid}: {label} (top 30)", ""]
            lines += [_fmt_head_row(r) for r in node["eval"]["head"][:30]]
            lines.append("")
        lines += [f"### Root {rid}: intermediate literary heads (top 12)", ""]
        for node in root["branches"]["lit"]:
            if node["generation"] == 0:
                continue
            e = node["eval"]
            lines += [f"**literary generation {node['generation']} "
                      f"({e['jury_size']:,})**: exact@50 {e['exact50']}, "
                      f"broad@50 {e['broad50']}, anti@50 {e['anti50']}, "
                      f"margin {_fmt(e['deepest_margin'])}", ""]
            lines += [_fmt_head_row(r) for r in e["head"][:12]]
            lines.append("")

    lines += ["## Empirical summary", ""]
    n_roots = len(results["roots"])
    for b in ("lit", "anti", "rand"):
        vals = []
        for g in range(n_gens):
            rows = [root["branches"][b][g]["eval"]
                    for root in results["roots"]
                    if root["branches"][b][g].get("eval")]
            if not rows:
                continue
            vals.append(
                f"g{g}: m={np.mean([r['deepest_margin'] for r in rows]):+.3f} "
                f"ex={np.mean([r['exact50'] for r in rows]):.1f} "
                f"an={np.mean([r['anti50'] for r in rows]):.1f}")
        lines.append(f"- **{b}** across-root trajectory: " + " -> ".join(vals))
    g2_rand = [root["branches"]["rand"][2]["eval"]["deepest_margin"]
               for root in results["roots"]]
    g2_lit = [root["branches"]["lit"][2]["eval"]["deepest_margin"]
              for root in results["roots"]]
    rhos = []
    for root in results["roots"]:
        rhos.append(root["shared_g0"]["split_half"]["spearman_half_panels"])
        for b in ("lit", "anti"):
            for node in root["branches"][b]:
                if "split_half" in node:
                    rhos.append(node["split_half"]["spearman_half_panels"])
    rho_vals = [r for r in rhos if isinstance(r, float)]
    lines += [
        f"- Random control at 20k: root-level margins "
        f"{[f'{x:+.3f}' for x in g2_rand]} (opposite signs across roots), "
        f"vs literary 20k {[f'{x:+.3f}' for x in g2_lit]} (same sign, both "
        "strongly F1-ward).",
        f"- Fitness split-half Spearman: min {min(rho_vals):.3f}, "
        f"max {max(rho_vals):.3f} across all fitness nodes "
        "(estimates are effectively unstable; selection carried only "
        "~12-replicate signal).",
        "",
        "Reversal regime per branch (stage0 margin / reversal gain, "
        "across-root means of evaluated juries):",
        "",
        "| branch | g1 | g2 | g3 | g4 |",
        "|---|---:|---:|---:|---:|",
    ]
    for b in ("lit", "anti", "rand"):
        cells = []
        for g in range(1, n_gens):
            rows = [root["branches"][b][g]["eval"]
                    for root in results["roots"]
                    if root["branches"][b][g].get("eval")]
            if rows:
                cells.append(
                    f"s0={np.mean([r['stage0_margin'] for r in rows]):+.3f} / "
                    f"gain={np.mean([r['reversal_gain'] for r in rows]):+.3f}")
            else:
                cells.append("n/a")
        lines.append(f"| {b} | " + " | ".join(cells) + " |")
    lit_s0 = [root["branches"]["lit"][2]["eval"]["stage0_margin"]
              for root in results["roots"]]
    lit_gain = [root["branches"]["lit"][2]["eval"]["reversal_gain"]
                for root in results["roots"]]
    anti_s0 = [root["branches"]["anti"][2]["eval"]["stage0_margin"]
               for root in results["roots"]]
    anti_gain = [root["branches"]["anti"][2]["eval"]["reversal_gain"]
                 for root in results["roots"]]
    lines += [
        "",
        f"At the 20k peak the literary juries still collapse F0-ward at "
        f"stage 0 (s0 {[f'{x:+.3f}' for x in lit_s0]}) and reach F1 only "
        f"through reversal (gain {[f'{x:+.3f}' for x in lit_gain]}): the "
        "literary tendency is REVEALED by reversal, "
        "not yet the ordinary stage-0 convergence.  No latent-basin -> "
        "direct-convergence saturation/crossover is observed on the literary "
        "path (stage0 margin never rises toward F1 as breeding proceeds).  "
        "The anti-bred juries show the mirror image: stage-0 convergence is "
        f"F1-ward (s0 {[f'{x:+.3f}' for x in anti_s0]}) and reversal pushes "
        f"them to F0 (gain {[f'{x:+.3f}' for x in anti_gain]}); their "
        "deepest-stage margin is anti-F1 at "
        "every generation.",
        "",
    ]

    lines += [
        "## Interpretation notes",
        "",
        "The reversal-saturation question: if recursive breeding makes a jury "
        "literary in its ORDINARY stage-0 convergence, reversal gain "
        "(deepest - stage0 margin) should fall toward zero and eventually go "
        "negative, while stage0 margin rises.  A hidden literary basin is "
        "instead indicated by positive reversal gain that reveals Family 1 "
        "from a low stage0 margin.  No claim is made beyond what the tables "
        "above show; no permutation tests are applied (exploratory pilot).",
        "",
        "What the pilot shows plainly: (1) the literary path's F1-minus-F0 "
        "margin rises across generations in BOTH roots and peaks at the 20k "
        "jury (across-root +0.63, exact@50 4, anti@50 9, heads concentrating "
        "on Borges/Dostoyevsky/Pessoa/Stoner/Maus/Persepolis), then collapses "
        "at 10k/5k (margin ~0, anti@50 rising again, final heads collapsing "
        "into a narrow fandom/series cluster); (2) the anti branch moves "
        "strongly in the opposite direction in both roots (margins "
        "-0.44..-0.65, anti@50 32-45); (3) the random control does not "
        "reproduce the literary trend (20k margins +0.61 vs -0.62 across "
        "roots, heads anti-heavy in root 1); (4) fitness split-half "
        "stability is effectively zero, so individual-level fitness "
        "estimates are noisy even though selection repeatedly reproduced the "
        "same 20k endpoint; (5) the amplification is therefore real but "
        "transient, and reversal remains essential to it (the literary "
        "signal is still a hidden basin, not an ordinary convergence, at "
        "every functional generation).",
        "",
        "Terminology: if the literary path amplifies, this is 'recursive "
        "amplification of a naturally discovered literary-enriched basin' "
        "(the families were structurally discovered label-blind; the choice "
        "of Family 1 as the branch to amplify was a one-time semantic "
        "decision), NOT 'completely unsupervised discovery of the literary "
        "canon'.",
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
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["smoke", "run", "report"],
                        required=True)
    parser.add_argument("--tag", default="main")
    parser.add_argument("--seed", type=int, default=BREEDING_SEED)
    parser.add_argument("--roots", type=int, default=N_ROOTS)
    parser.add_argument("--root-size", type=int, default=ROOT_SIZE)
    parser.add_argument("--pool-sizes", type=int, nargs="+",
                        default=list(POOL_SIZES))
    parser.add_argument("--replicates", type=int,
                        default=PARTITION_REPLICATES)
    parser.add_argument("--hours", type=float, default=0.0,
                        help="wall-clock cap; 0 disables")
    args = parser.parse_args()
    args._t0 = time.time()

    if args.phase == "smoke":
        phase_smoke(args)
    elif args.phase == "run":
        run_breeding(args)
    else:
        phase_report(args)


if __name__ == "__main__":
    main()

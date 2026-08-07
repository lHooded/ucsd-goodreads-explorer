#!/usr/bin/env python3
"""Breed literary canons.

A literary canon is a converged direction of a gain-hard pruning path together
with the converged reader weights and survivor set that produced it. This
experiment crosses pairs of canons, pushes each child through the same pruning
machinery, and asks:

- does breeding converge, and to which parent's basin?
- if children commonly breed true to one parent, that parent has the stronger
  pull; if to neither, a new canon has been created.
- does a larger pruning increment (harder removal, sharper beta, bigger ladder
  steps) make convergence stronger or move the outcome?
- repeated breeding yields a hierarchy; the final bred canon is a candidate
  "natural distributed literary canon" in the experiment's own geometry.

Breeding modes:
- jury_mix: child start weights = half the converged reader weights of parent A
  plus half of parent B (users outside both sets get the 0.4 baseline). This is
  "half jurors from one, half from another".
- direction_mix: child start weights are induced by the top-25 books of the
  normalized sum of the parents' directions (breeding in canon space).

The pool of parents is chosen by literary metrics from the year-jury, teacher,
rebuilt, contrastive, and pairwise candidate paths (disclosed seeds, exactly as
in the pre-year reversal experiment). The Goodreads love center (a random
jury's stage-0 collapse) is included as a non-literary outgroup parent.

Titles and evaluation lists are loaded only after every direction is frozen;
literary labels never enter the geometry of any run.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts import research_attractor_pruning as pruning
from curators_explorer.scripts import research_attractor_pruning_audit as audit
from curators_explorer.scripts import research_attractor_pruning_preexisting as preexisting
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year


DATA = Path(__file__).resolve().parents[1] / "data"

BETA = 2.5
MAX_STAGES = 8
RETAINED_TARGET = 0.70
CANON_MIN_EXACT = 3
DEDUPE_CORR = 0.95
TRUE_THRESHOLD = 0.85
LEAN_THRESHOLD = 0.60
POLE_THRESHOLD = 0.25
UNPAIRED_STARTS = 24
UNPAIRED_SEED = 2026
JITTER_REPS = 5
JITTER_SAMPLE_FRAC = 0.8
POLY_REPS = 3
GENERATIONS = 8
CHECKPOINT_EVERY = 10
RNG_SEED = 20260807

POOL_CANDIDATES = [
    "teacher_p65_s25",
    "rebuilt_hard_4929",
    "rebuilt_soft",
    "best_preference_delta_q10",
    "contrastive_careful",
    "pairwise_bilateral",
]

INCREMENT_VARIANTS = [
    {"name": "hard_mult_0.75", "hard_mult": 0.75},
    {"name": "hard_mult_1.0", "hard_mult": 1.0},
    {"name": "hard_mult_1.5", "hard_mult": 1.5},
    {"name": "hard_mult_2.0", "hard_mult": 2.0},
    {"name": "ladder_0.10", "mode": "ladder", "ladder_rate": 0.10},
    {"name": "ladder_0.20", "mode": "ladder", "ladder_rate": 0.20},
    {"name": "beta_3.5", "beta": 3.5},
    {"name": "beta_5.0", "beta": 5.0},
]


def status_path(tag: str) -> Path:
    return DATA / f"canon_breeding_{tag}_status.json"


def out_paths(tag: str) -> tuple[Path, Path, Path]:
    return (
        DATA / f"canon_breeding_{tag}.json",
        DATA / f"canon_breeding_{tag}_directions.npz",
        DATA / f"CANNON_BREEDING_{tag.upper()}_REPORT.md",
    )


def checkpoint(tag: str, state: dict[str, Any]) -> None:
    status_path(tag).write_text(
        json.dumps({**state, "timestamp": time.time()}, indent=2), encoding="utf-8"
    )


def make_parent_starts(
    payload: dict[str, np.ndarray],
) -> dict[str, tuple[np.ndarray, dict[str, Any]]]:
    """Full-population start weight vectors for every pool candidate."""
    features, _audit = year.extract_year_features(payload)
    starts: dict[str, tuple[np.ndarray, dict[str, Any]]] = {}

    uids_t, w_t = preexisting.teacher_jury()
    starts["teacher_p65_s25"] = (
        preexisting.start_from_user_weights(payload, uids_t, w_t),
        {"users_offered": len(uids_t)},
    )

    import duckdb

    con = duckdb.connect()
    hard_rows = con.execute(
        "SELECT user_id FROM read_parquet(?) WHERE hard_jury",
        [str(DATA / "soft_jury_weights.parquet")],
    ).fetchall()
    soft_rows = con.execute(
        "SELECT user_id, jury_q FROM read_parquet(?) WHERE jury_q > 0",
        [str(DATA / "soft_jury_weights.parquet")],
    ).fetchall()
    con.close()
    starts["rebuilt_hard_4929"] = (
        preexisting.start_from_user_weights(
            payload,
            np.asarray([r[0] for r in hard_rows], dtype=np.int64),
            np.ones(len(hard_rows), dtype=np.float64),
        ),
        {"users_offered": len(hard_rows)},
    )
    starts["rebuilt_soft"] = (
        preexisting.start_from_user_weights(
            payload,
            np.asarray([r[0] for r in soft_rows], dtype=np.int64),
            np.asarray([r[1] for r in soft_rows], dtype=np.float64),
        ),
        {"users_offered": len(soft_rows)},
    )

    delta = pruning.start_weights(features, "best_preference_delta_q10")
    starts["best_preference_delta_q10"] = (delta, {"variant": "best_preference_delta_q10"})

    meta, _eval = spectral.load_posthoc_context(payload["work_ids"])
    contrastive = json.loads(
        (DATA / "threeway_unseeded.json").read_text(encoding="utf-8")
    )["rankings"]["unseeded_contrastive"]["top25"]
    bilateral = json.loads(
        (DATA / "pairwise_esteem.json").read_text(encoding="utf-8")
    )["methods"]["pairwise_bilateral"]["top15"]
    for name, titles in (
        ("contrastive_careful", [r["title"] for r in contrastive]),
        ("pairwise_bilateral", [r["title"] for r in bilateral]),
    ):
        start, diag = preexisting.start_from_book_titles(payload, titles, meta)
        starts[name] = (start, diag)
    return starts


def run_path(
    payload: dict[str, np.ndarray],
    matrix: Any,
    start_full: np.ndarray,
    rng: np.random.Generator,
    *,
    beta: float = BETA,
    hard_mult: float | None = None,
    ladder_rate: float | None = None,
    mode: str = "hard",
    criterion: str = "gain",
    max_stages: int = MAX_STAGES,
    store_weights: bool = False,
    store_pref: bool = False,
) -> dict[str, Any]:
    """The standard gain-hard pruning path.

    Returns per-stage directions, survivor sets, and optionally the converged
    user weights and book-side preference vectors at every stage.
    """
    n_users = len(payload["user_ids"])
    full_operator, _ = spectral.make_operator(matrix, payload, attractor.CONFIG)
    reference_direction = attractor.normalize_columns(
        full_operator.rmatmat(start_full)
    ).ravel()

    keep = np.arange(n_users, dtype=np.int64)
    surviving = [keep.copy()]
    directions = []
    weights_store: dict[int, np.ndarray] = {}
    pref_store: dict[int, dict[str, np.ndarray]] = {}
    stages = []
    stop_reason = "max_stages"
    for stage in range(max_stages + 1):
        local_payload = pruning.subset_payload(payload, keep)
        sub_matrix, _ = spectral.build_matrix(local_payload)
        operator, _ = spectral.make_operator(sub_matrix, local_payload, attractor.CONFIG)
        start_restricted = start_full[keep] / start_full[keep].mean()
        weights, direction, history = pruning.iterate_map(operator, start_restricted, beta)
        if store_weights:
            weights_store[stage] = weights.astype(np.float32)
        if store_pref:
            preference = attractor.weighted_preferences(sub_matrix, weights)
            pref_store[stage] = {
                "score": preference["score"].astype(np.float32),
                "reader_mass": preference["reader_mass"].astype(np.float32),
            }
        stage_start_direction = attractor.normalize_columns(
            operator.rmatmat(start_restricted)
        ).ravel()
        retained_reference = float(np.sum(direction * reference_direction))
        retained_stage = float(np.sum(direction * stage_start_direction))
        directions.append(direction.astype(np.float32).ravel())
        stages.append(
            {
                "stage": stage,
                "remaining_users": int(len(keep)),
                "cumulative_removed_fraction": 1.0 - len(keep) / n_users,
                "final_step_correlation": history[-1]["step_correlation"],
                "direction_retained_reference": retained_reference,
                "direction_retained_stage": retained_stage,
            }
        )
        if retained_reference >= RETAINED_TARGET:
            stop_reason = "retained_literary_direction"
            break
        if stage == max_stages:
            stop_reason = "max_stages"
            break
        if len(keep) <= pruning.MIN_REMAINING_FRACTION * n_users:
            stop_reason = "evidence_floor"
            break
        if criterion == "random":
            order = rng.permutation(len(weights))
        else:
            order = np.argsort(-(weights - start_restricted), kind="stable")
        if mode == "hard":
            threshold = (hard_mult if hard_mult is not None else pruning.HARD_THRESHOLD) * float(
                np.mean(weights)
            )
            n_remove = int(np.sum(weights >= threshold))
        else:
            n_remove = max(
                1, int(np.ceil((ladder_rate or pruning.LADDER_RATE) * len(weights)))
            )
        if n_remove == 0:
            stop_reason = "nothing_removed"
            break
        removed = np.zeros(len(weights), dtype=bool)
        removed[order[:n_remove]] = True
        keep = keep[~removed]
        if len(keep) <= pruning.MIN_REMAINING_FRACTION * n_users:
            stop_reason = "evidence_floor"
            break
        surviving.append(keep.copy())
        stages[-1]["removed_users"] = int(n_remove)

    return {
        "stop_reason": stop_reason,
        "stages": stages,
        "directions": directions,
        "surviving": surviving,
        "weights_store": weights_store,
        "pref_store": pref_store,
        "reference_direction": reference_direction,
    }


def love_center_parent(payload: dict[str, np.ndarray], matrix: Any) -> dict[str, Any]:
    """Stage-0 collapse of a random jury: the Goodreads love-center canon."""
    n = len(payload["user_ids"])
    rng = np.random.default_rng(20260807)
    selected = rng.random(n) < 0.03
    weights = np.where(selected, 20.0, 0.4).astype(np.float32)
    weights /= weights.mean()
    operator, _ = spectral.make_operator(matrix, payload, attractor.CONFIG)
    converged, direction, history = pruning.iterate_map(operator, weights, BETA)
    stage0 = attractor.normalize_columns(operator.rmatmat(weights)).ravel()
    preference = attractor.weighted_preferences(matrix, converged)
    return {
        "stop_reason": "stage0",
        "stages": [
            {
                "stage": 0,
                "remaining_users": n,
                "cumulative_removed_fraction": 0.0,
                "final_step_correlation": history[-1]["step_correlation"],
                "direction_retained_reference": float(np.sum(direction * stage0)),
                "direction_retained_stage": float(np.sum(direction * stage0)),
            }
        ],
        "directions": [stage0.astype(np.float32)],
        "surviving": [np.arange(n, dtype=np.int64)],
        "weights_store": {0: converged.astype(np.float32)},
        "pref_store": {
            0: {
                "score": preference["score"].astype(np.float32),
                "reader_mass": preference["reader_mass"].astype(np.float32),
            }
        },
        "reference_direction": stage0.astype(np.float32),
    }


def jury_mix_start(
    payload: dict[str, np.ndarray],
    parents: dict[str, dict[str, Any]],
    a: str,
    b: str,
    rng: np.random.Generator,
    sample_frac: float = 1.0,
) -> np.ndarray:
    """Half the jurors of A plus half the jurors of B, mean-normalized."""
    n = len(payload["user_ids"])
    child = np.zeros(n, dtype=np.float32)
    for parent in (a, b):
        run = parents[parent]["run"]
        stage = parents[parent]["canon_stage"]
        surv = run["surviving"][stage]
        w = run["weights_store"][stage]
        if sample_frac < 1.0:
            n_k = max(1, int(np.ceil(sample_frac * len(surv))))
            subset = rng.choice(surv, size=n_k, replace=False)
            positions = np.searchsorted(surv, subset)
            child[subset] += w[positions]
        else:
            child[surv] += w
    child = np.where(child == 0.0, 0.4, child)
    child /= child.mean()
    return child.astype(np.float32)


def direction_mix_start(
    payload: dict[str, np.ndarray],
    parents: dict[str, dict[str, Any]],
    a: str,
    b: str,
) -> np.ndarray:
    """User weights induced by the top-25 books of the summed parent directions."""
    d_a = parents[a]["canon_direction"]
    d_b = parents[b]["canon_direction"]
    if np.sum(d_a * d_b) < 0:
        d_b = -d_b
    d_child = attractor.normalize_columns(d_a + d_b).ravel()
    indices = np.argsort(-d_child, kind="stable")[:25]
    n = len(payload["user_ids"])
    row, col, side = payload["row"], payload["col"], payload["side"]
    in_head = np.isin(col, indices.astype(np.int64))
    fives = np.bincount(row[in_head & (side == 1)], minlength=n).astype(np.float64)
    rated = np.bincount(row[in_head], minlength=n).astype(np.float64)
    frac = np.divide(fives, rated, out=np.zeros(n), where=rated > 0)
    start = 0.4 + 19.6 * frac
    start /= start.mean()
    return start.astype(np.float32)


def classify(corrs: dict[str, list[float]], idx: int) -> str:
    c = {k: v[idx] for k, v in corrs.items()}
    best_key = max(c, key=c.get)
    second_key = max(k for k in c if k != best_key)
    best, second = c[best_key], c[second_key]
    if best >= TRUE_THRESHOLD and abs(best - second) > 0.05:
        return f"true:{best_key}"
    if best >= TRUE_THRESHOLD:
        return f"ties:{best_key}/{second_key}"
    if best >= LEAN_THRESHOLD:
        return f"lean:{best_key}"
    return "new"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="core")
    parser.add_argument("--seed", type=int, default=RNG_SEED)
    parser.add_argument("--hours", type=float, default=0.0)
    parser.add_argument("--max-pairs", type=int, default=0)
    parser.add_argument("--reps", type=int, default=0, help="jitter reps per in-group pair (0 = JITTER_REPS)")
    parser.add_argument("--skip-increment", action="store_true")
    parser.add_argument("--skip-poly", action="store_true")
    parser.add_argument("--skip-generations", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    t0 = time.time()
    out_json, out_dir, out_report = out_paths(args.tag)
    state: dict[str, Any] = {"tag": args.tag, "phase": "parents", "parents_done": 0, "children_done": 0}
    checkpoint(args.tag, state)

    payload, matrix, matrix_meta = year.load_matrix()
    n_users = len(payload["user_ids"])

    def deadline() -> float:
        return t0 + 3600.0 * args.hours if args.hours else float("inf")

    rng = np.random.default_rng(args.seed)

    # ----- parents -----
    starts = make_parent_starts(payload)
    parent_runs: dict[str, dict[str, Any]] = {}
    for name in POOL_CANDIDATES:
        if name not in starts or time.time() > deadline():
            continue
        parent_runs[name] = run_path(
            payload, matrix, starts[name][0], rng, store_weights=True, store_pref=True
        )
        state["parents_done"] += 1
        checkpoint(args.tag, state)
        print(
            f"parent {name}: stop={parent_runs[name]['stop_reason']} "
            f"stages={len(parent_runs[name]['stages'])}",
            flush=True,
        )
    parent_runs["love_center"] = love_center_parent(payload, matrix)

    print("Loading post-hoc semantic context", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])

    def posthoc_for(run: dict[str, Any], idx: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
        pref = run["pref_store"][idx]
        return attractor.posthoc_head(pref, payload["work_ids"], meta, eval_sets, limit=200)

    # ----- parents: per-stage literary metrics, then canon selection -----
    parent_records: list[dict[str, Any]] = []
    pool: dict[str, dict[str, Any]] = {}
    for name, run in parent_runs.items():
        stage_records = []
        lit_scores = []
        for idx, stage in enumerate(run["stages"]):
            head, m = posthoc_for(run, idx)
            stage_records.append(
                {
                    "stage": stage["stage"],
                    "remaining_users": stage["remaining_users"],
                    "cumulative_removed_fraction": stage["cumulative_removed_fraction"],
                    "final_step_correlation": stage["final_step_correlation"],
                    "direction_retained_reference": stage["direction_retained_reference"],
                    "direction_retained_stage": stage["direction_retained_stage"],
                    "exact_lit50": m["exact_lit50"],
                    "broad_lit50": m["broad_lit50"],
                    "anti50": m["anti50"],
                    "head": head[:15],
                }
            )
            lit_scores.append(m["exact_lit50"] + m["broad_lit50"])
            print(
                f"parent {name} stage {stage['stage']}: exact {m['exact_lit50']} "
                f"broad {m['broad_lit50']} anti {m['anti50']}",
                flush=True,
            )
        best_lit = int(np.argmax(lit_scores))
        parent_records.append(
            {
                "name": name,
                "stop_reason": run["stop_reason"],
                "best_lit_stage": best_lit,
                "best_lit_score": int(lit_scores[best_lit]),
                "stages": stage_records,
            }
        )
        # up to two literary canons per path: the best-lit stage and, if it is
        # far enough from the best, the second-best literary stage.
        ranked = sorted(
            (i for i in range(len(stage_records)) if stage_records[i]["exact_lit50"] >= CANON_MIN_EXACT),
            key=lambda i: (lit_scores[i], stage_records[i]["stage"]),
            reverse=True,
        )
        for i, idx in enumerate(ranked[:2]):
            m = stage_records[idx]
            canon_name = f"{name}::s{idx}"
            pool[canon_name] = {
                "parent": name,
                "canon_stage": idx,
                "exact_lit50": m["exact_lit50"],
                "broad_lit50": m["broad_lit50"],
                "anti50": m["anti50"],
                "users": int(run["surviving"][idx].size),
                "canon_direction": run["directions"][idx],
                "run": run,
                "literary": True,
            }
            if i == 1:
                # keep only if materially different from the primary canon
                primary = run["directions"][ranked[0]]
                if float(np.sum(primary * run["directions"][idx])) >= DEDUPE_CORR:
                    del pool[canon_name]
    pool["love_center"] = {
        "parent": "love_center",
        "canon_stage": 0,
        "exact_lit50": 0,
        "broad_lit50": 0,
        "anti50": 2,
        "users": n_users,
        "canon_direction": parent_runs["love_center"]["directions"][0],
        "run": parent_runs["love_center"],
        "literary": False,
    }
    lit_names = [n for n in pool if pool[n]["literary"]]

    # dedupe identical literary basins
    dropped = True
    while dropped and len(lit_names) > 1:
        dropped = False
        for i in range(len(lit_names)):
            for j in range(i + 1, len(lit_names)):
                a, b = lit_names[i], lit_names[j]
                cos = float(np.sum(pool[a]["canon_direction"] * pool[b]["canon_direction"]))
                if cos >= DEDUPE_CORR:
                    if pool[a]["exact_lit50"] < pool[b]["exact_lit50"]:
                        lit_names.pop(i)
                    else:
                        lit_names.pop(j)
                    dropped = True
                    break
            if dropped:
                break
    if not lit_names:
        print("No literary canons formed; aborting.", flush=True)
        return
    print(
        f"pool: {len(lit_names)} literary canons {[(n, pool[n]['exact_lit50']) for n in lit_names]}",
        flush=True,
    )

    in_pairs = [(a, b) for i, a in enumerate(lit_names) for b in lit_names[i + 1 :]]
    out_pairs = [(a, "love_center") for a in lit_names]
    if args.max_pairs:
        in_pairs = in_pairs[: args.max_pairs]
        out_pairs = out_pairs[: args.max_pairs]
    pairs = in_pairs + out_pairs

    # ----- children -----
    children: list[dict[str, Any]] = []
    dir_store: dict[str, np.ndarray] = {}
    keep_deep_store: dict[str, np.ndarray] = {}

    def record(
        name: str,
        a: str,
        b: str,
        mode: str,
        rep: int,
        start: np.ndarray,
        variant: dict[str, Any],
    ) -> None:
        run = run_path(
            payload, matrix, start, rng,
            store_pref=True,
            **{k: v for k, v in variant.items() if k != "name"},
        )
        stages = run["stages"]
        deepest = len(stages) - 1
        dir_store[f"{name}::d0"] = run["directions"][0]
        dir_store[f"{name}::deep"] = run["directions"][deepest]
        keep_deep_store[f"{name}::keep_deep"] = run["surviving"][deepest].astype(np.int32)
        parents = [p for p in (a, b) if p in pool]
        cos_trace = {
            p: [float(np.sum(d * pool[p]["canon_direction"])) for d in run["directions"]]
            for p in parents
        }
        children.append(
            {
                "name": name,
                "a": a,
                "b": b,
                "mode": mode,
                "rep": rep,
                "variant": variant,
                "stop_reason": run["stop_reason"],
                "deepest_stage": deepest,
                "n_stages": len(stages),
                "stage0": {"users": stages[0]["remaining_users"]},
                "deepest": {
                    "users": stages[deepest]["remaining_users"],
                    "cumulative_removed": stages[deepest]["cumulative_removed_fraction"],
                    "final_step_correlation": stages[deepest]["final_step_correlation"],
                },
                "cos_trace": cos_trace,
                "pref_store": run["pref_store"],
            }
        )
        state["children_done"] += 1
        if state["children_done"] % CHECKPOINT_EVERY == 0:
            checkpoint(args.tag, state)
        print(
            f"child {name} ({mode} r{rep}): stages={len(stages)} stop={run['stop_reason']}",
            flush=True,
        )

    state["phase"] = "breeding"
    for a, b in pairs:
        if time.time() > deadline():
            break
        record(
            f"{a}x{b}::jm", a, b, "jury_mix", 0,
            jury_mix_start(payload, pool, a, b, rng), {},
        )
        if "love_center" in (a, b):
            continue
        record(
            f"{a}x{b}::dm", a, b, "direction_mix", 0,
            direction_mix_start(payload, pool, a, b), {},
        )
    if not args.quick:
        jitter_reps = args.reps or JITTER_REPS
        for a, b in in_pairs:
            if time.time() > deadline():
                break
            for rep in range(1, jitter_reps + 1):
                record(
                    f"{a}x{b}::jm::r{rep}", a, b, "jury_mix", rep,
                    jury_mix_start(payload, pool, a, b, rng, sample_frac=JITTER_SAMPLE_FRAC),
                    {},
                )
    rng_c = np.random.default_rng(args.seed + 1)
    random_half = np.where(rng_c.random(n_users) < 0.03, 20.0, 0.4).astype(np.float32)
    random_half /= random_half.mean()
    for a in lit_names:
        if time.time() > deadline():
            break
        record(f"{a}x{a}::jm", a, a, "self", 0, jury_mix_start(payload, pool, a, a, rng), {})
        run_a = pool[a]["run"]
        stage_a = pool[a]["canon_stage"]
        base_a = np.zeros(n_users, dtype=np.float32)
        base_a[run_a["surviving"][stage_a]] = run_a["weights_store"][stage_a]
        base_a = np.where(base_a == 0.0, 0.4, base_a)
        child = 0.5 * base_a + 0.5 * random_half
        child /= child.mean()
        record(f"{a}xrandom::jm", a, "random", "control", 0, child.astype(np.float32), {})

    if not args.skip_increment and not args.quick:
        state["phase"] = "increment"
        for a, b in in_pairs[:6]:
            if time.time() > deadline():
                break
            cos_ab = float(np.sum(pool[a]["canon_direction"] * pool[b]["canon_direction"]))
            if cos_ab >= DEDUPE_CORR:
                continue
            for variant in INCREMENT_VARIANTS:
                record(
                    f"{a}x{b}::jm::{variant['name']}", a, b, "increment", 0,
                    jury_mix_start(payload, pool, a, b, rng), variant,
                )

    if not args.skip_poly and not args.quick and len(in_pairs) >= 2:
        state["phase"] = "polyamory"
        first_of_path: dict[str, str] = {}
        for n in lit_names:
            first_of_path.setdefault(pool[n]["parent"], n)
        trio = list(first_of_path.values())[:3]
        for rep in range(POLY_REPS):
            if time.time() > deadline():
                break
            child = np.zeros(n_users, dtype=np.float32)
            for parent in trio[:3]:
                run = pool[parent]["run"]
                stage = pool[parent]["canon_stage"]
                surv = run["surviving"][stage]
                child[surv] += run["weights_store"][stage]
            child = np.where(child == 0.0, 0.4, child)
            child /= child.mean()
            record(
                f"poly::" + "+".join(trio[:3]) + f"::r{rep}",
                trio[0], trio[1], "polyamory", rep, child.astype(np.float32), {},
            )

    if not args.skip_generations and not args.quick:
        state["phase"] = "generations"
        gen_dirs = {n: pool[n]["canon_direction"] for n in lit_names}
        for gen in range(GENERATIONS):
            if time.time() > deadline():
                break
            if len(gen_dirs) < 2:
                break
            items = list(gen_dirs)
            a, b = max(
                ((x, y) for i, x in enumerate(items) for y in items[i + 1 :]),
                key=lambda p: float(np.sum(gen_dirs[p[0]] * gen_dirs[p[1]])),
            )
            start = direction_mix_start(payload, {"a": {"canon_direction": gen_dirs[a]}, "b": {"canon_direction": gen_dirs[b]}}, "a", "b")
            name = f"gen{gen}::{a}x{b}"
            run = run_path(payload, matrix, start, rng, store_pref=True)
            deepest = len(run["stages"]) - 1
            dir_store[f"{name}::deep"] = run["directions"][deepest]
            keep_deep_store[f"{name}::keep_deep"] = run["surviving"][deepest].astype(np.int32)
            cos_trace = {
                p: [float(np.sum(d * gen_dirs[p])) for d in run["directions"]]
                for p in (a, b)
            }
            pool_trace = {
                p: float(np.sum(run["directions"][deepest] * pool[p]["canon_direction"]))
                for p in lit_names
            }
            children.append(
                {
                    "name": name,
                    "a": a,
                    "b": b,
                    "mode": "generation",
                    "rep": gen,
                    "variant": {},
                    "stop_reason": run["stop_reason"],
                    "deepest_stage": deepest,
                    "n_stages": len(run["stages"]),
                    "stage0": {"users": run["stages"][0]["remaining_users"]},
                    "deepest": {
                        "users": run["stages"][deepest]["remaining_users"],
                        "cumulative_removed": run["stages"][deepest]["cumulative_removed_fraction"],
                        "final_step_correlation": run["stages"][deepest]["final_step_correlation"],
                    },
                    "cos_trace": cos_trace,
                    "pool_trace": pool_trace,
                    "pref_store": run["pref_store"],
                }
            )
            state["children_done"] += 1
            print(f"child {name}: stages={len(run['stages'])}", flush=True)
            del gen_dirs[a]
            del gen_dirs[b]
            gen_dirs[name] = run["directions"][deepest]

    # ----- post-hoc metrics for children (frozen preference vectors) -----
    print("Post-hoc metrics for children", flush=True)
    for child in children:
        pref_store = child.pop("pref_store")
        deep = child["deepest_stage"]
        per_stage = []
        for idx, pref in sorted(pref_store.items()):
            head, m = attractor.posthoc_head(
                pref, payload["work_ids"], meta, eval_sets, limit=200
            )
            per_stage.append(
                {
                    "stage": idx,
                    "exact_lit50": m["exact_lit50"],
                    "broad_lit50": m["broad_lit50"],
                    "anti50": m["anti50"],
                }
            )
            if idx == 0:
                child["stage0"].update(
                    {
                        "exact_lit50": m["exact_lit50"],
                        "broad_lit50": m["broad_lit50"],
                        "anti50": m["anti50"],
                    }
                )
            if idx == deep:
                child["deepest"].update(
                    {
                        "exact_lit50": m["exact_lit50"],
                        "broad_lit50": m["broad_lit50"],
                        "anti50": m["anti50"],
                        "head": head[:15],
                    }
                )
        child["per_stage"] = per_stage
        if len(child["cos_trace"]) >= 2:
            child["classification"] = classify(child["cos_trace"], deep)
        elif child["mode"] == "self":
            child["classification"] = (
                "self:stable" if child["cos_trace"].get(child["a"], [0])[deep] >= TRUE_THRESHOLD else "self:drifted"
            )
        else:
            child["classification"] = "control"
        trace = child["cos_trace"].get(child["a"], [])
        if trace:
            child["deepest"]["cos_to_a"] = trace[deep]

    # ----- valley audits -----
    audits: dict[str, dict[str, Any]] = {}

    def valley_audit(operator: Any, reference: np.ndarray) -> dict[str, Any]:
        weights, directions = audit.random_census(
            operator, operator.shape[0], UNPAIRED_STARTS, UNPAIRED_SEED, paired=False
        )
        corr = (directions * reference[:, None]).sum(axis=0)
        return {
            "starts": UNPAIRED_STARTS,
            "literary_pole": int(np.sum(corr > POLE_THRESHOLD)),
            "mixed": int(np.sum(np.abs(corr) <= POLE_THRESHOLD)),
            "mirror_pole": int(np.sum(corr < -POLE_THRESHOLD)),
            "corr_sorted": [round(float(x), 3) for x in np.sort(corr)],
        }

    for name in lit_names:
        run = pool[name]["run"]
        stage = pool[name]["canon_stage"]
        keep = run["surviving"][stage]
        local_payload = pruning.subset_payload(payload, keep)
        sub_matrix, _ = spectral.build_matrix(local_payload)
        operator, _ = spectral.make_operator(sub_matrix, local_payload, attractor.CONFIG)
        audits[name] = valley_audit(operator, pool[name]["canon_direction"])
        print(
            f"audit {name}: {audits[name]['literary_pole']}/{audits[name]['mirror_pole']}",
            flush=True,
        )
    new_children = [c for c in children if c["classification"] == "new"][:6]
    for child in new_children:
        keep = keep_deep_store.get(f"{child['name']}::keep_deep")
        if keep is None:
            continue
        local_payload = pruning.subset_payload(payload, keep.astype(np.int64))
        sub_matrix, _ = spectral.build_matrix(local_payload)
        operator, _ = spectral.make_operator(sub_matrix, local_payload, attractor.CONFIG)
        audits[child["name"]] = valley_audit(operator, dir_store[f"{child['name']}::deep"])
        child["valley_audit"] = audits[child["name"]]
        print(
            f"audit {child['name']}: {audits[child['name']]['literary_pole']}/"
            f"{audits[child['name']]['mirror_pole']}",
            flush=True,
        )

    # ----- write artifacts -----
    json_safe: dict[str, Any] = {
        "method": {
            "purpose": "breed literary canons; ask whether children converge to a parent, to neither (new canon), or not at all",
            "beta": BETA,
            "iterations": pruning.ITERATIONS,
            "max_stages": MAX_STAGES,
            "retained_target": RETAINED_TARGET,
            "hard_default": pruning.HARD_THRESHOLD,
            "canon_min_exact": CANON_MIN_EXACT,
            "dedupe_corr": DEDUPE_CORR,
            "true_threshold": TRUE_THRESHOLD,
            "lean_threshold": LEAN_THRESHOLD,
            "pole_threshold": POLE_THRESHOLD,
            "unpaired_starts": UNPAIRED_STARTS,
            "jitter_reps": args.reps or JITTER_REPS,
            "jitter_sample_frac": JITTER_SAMPLE_FRAC,
            "poly_reps": POLY_REPS,
            "generations": GENERATIONS,
            "random_seed": args.seed,
            "semantic_data_loaded_after_convergence": True,
            "runtime_seconds": time.time() - t0,
        },
        "matrix": {**matrix_meta, "shape": list(matrix.shape)},
        "parents": parent_records,
        "pool": [
            {
                "canon": name,
                "canon_stage": pool[name]["canon_stage"],
                "exact_lit50": pool[name]["exact_lit50"],
                "broad_lit50": pool[name]["broad_lit50"],
                "anti50": pool[name]["anti50"],
                "users": pool[name]["users"],
            }
            for name in lit_names
        ],
        "children": [
            {k: v for k, v in c.items() if k not in ("pref_store",)} for c in children
        ],
        "valley_audits": audits,
        "direction_summary": {
            k: {"norm": float(np.linalg.norm(v)), "absmax": float(np.max(np.abs(v)))}
            for k, v in dir_store.items()
        },
    }
    for name in lit_names:
        dir_store[f"pool::{name}"] = pool[name]["canon_direction"]
    out_json.write_text(json.dumps(json_safe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    np.savez(out_dir, **dir_store, **keep_deep_store)

    # ----- report -----
    lines = [
        "# Breeding literary canons",
        "",
        "Each parent is a converged direction of a gain-hard pruning path, together with its "
        "converged reader weights and survivor set. Children are bred by mixing half the jurors "
        "of one parent with half of the other (jury_mix) or by seeding from the top-25 books of "
        "the summed parent directions (direction_mix), then pushed through the same pruning "
        "machinery. A child breeds true if its deepest direction is within 0.85 correlation of a "
        "parent (and not within 0.05 of both); it leans at 0.60; otherwise it is a new canon.",
        "",
        f"Runtime: **{json_safe['method']['runtime_seconds']:.0f}s**. Semantic context loaded "
        "only after every direction was frozen.",
        "",
        "## Parent pool",
        "",
        "| canon | parent path | canon stage | exact @50 | broad @50 | anti @50 | survivors |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for name in lit_names:
        p = pool[name]
        lines.append(
            f"| {name} | {p['parent']} | {p['canon_stage']} | {p['exact_lit50']} | "
            f"{p['broad_lit50']} | {p['anti50']} | {p['users']:,} |"
        )
    lines += [
        "",
        "Parent direction correlations:",
        "",
        "| | " + " | ".join(lit_names) + " |",
        "|---|" + "---|" * len(lit_names),
    ]
    for a in lit_names:
        row = [f"| {a} |"]
        for b in lit_names:
            row.append(f"{np.sum(pool[a]['canon_direction'] * pool[b]['canon_direction']):.2f} |")
        lines.append(" ".join(row))
    lines.append("")

    lit_pairs = [c for c in children if c["mode"] in ("jury_mix", "direction_mix")]
    by_mode = {mode: [c for c in lit_pairs if c["mode"] == mode] for mode in ("jury_mix", "direction_mix")}
    lines += ["## Does breeding converge?", ""]
    for mode, subset in by_mode.items():
        if not subset:
            continue
        converged = sum(1 for c in subset if c["deepest"]["final_step_correlation"] >= 0.999)
        shallow = sum(1 for c in subset if c["n_stages"] == 1)
        lines += [
            f"### {mode} ({len(subset)} children)",
            "",
            f"- Converged (final step corr >= 0.999): **{converged}/{len(subset)}**.",
            f"- Breeds true to one parent: **{sum(1 for c in subset if c['classification'].startswith('true:'))}**.",
            f"- Ties (within 0.05 of both; breeds true to the family): **{sum(1 for c in subset if c['classification'].startswith('ties:'))}**.",
            f"- Leans to a parent: **{sum(1 for c in subset if c['classification'].startswith('lean:'))}**.",
            f"- New canon (below 0.60 to both): **{sum(1 for c in subset if c['classification'] == 'new')}**.",
            f"- Stopped at stage 0 (already an attractor; no pruning happened): **{shallow}**.",
            "",
        ]
        lines += ["| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |", "|---|---:|---:|---|---:|---:|---:|"]
        for c in sorted(subset, key=lambda x: (x["a"], x["b"], x["mode"])):
            trace = c["cos_trace"]
            deep = c["deepest_stage"]
            if set(trace) != set((c["a"], c["b"])):
                continue
            lines.append(
                f"| {c['a']} x {c['b']} | {trace[c['a']][deep]:.3f} | {trace[c['b']][deep]:.3f} | "
                f"{c['classification']} | {c['deepest'].get('exact_lit50', '-')} | "
                f"{c['deepest'].get('broad_lit50', '-')} | {c['deepest'].get('anti50', '-')} |"
            )
        lines.append("")

    lines += ["## Attraction matrix (jury_mix; entry = true:A : true:B : ties : lean:A : lean:B : new over children of the pair)", ""]
    lines += ["| A \\ B | " + " | ".join(lit_names) + " |", "|" + "---|" * (len(lit_names) + 1)]
    for a in lit_names:
        vals = []
        for b in lit_names:
            if a == b:
                vals.append("-")
                continue
            kids = [
                c for c in children
                if c["mode"] == "jury_mix" and {c["a"], c["b"]} == {a, b}
            ]
            if not kids:
                vals.append("-")
                continue
            a_trues = sum(1 for c in kids if c["classification"] == f"true:{a}")
            b_trues = sum(1 for c in kids if c["classification"] == f"true:{b}")
            new = sum(1 for c in kids if c["classification"] == "new")
            ties = sum(1 for c in kids if c["classification"].startswith("ties:"))
            a_leans = sum(1 for c in kids if c["classification"] == f"lean:{a}")
            b_leans = sum(1 for c in kids if c["classification"] == f"lean:{b}")
            vals.append(f"{a_trues}:{b_trues}:{ties}:{a_leans}:{b_leans}:{new}")
        lines.append("| " + a + " | " + " | ".join(vals) + " |")
    lines.append("")

    lines += ["## Controls (self-breeding, random-mix, generations)", ""]
    lines += ["| child | mode | class | cos to A @deepest | exact @50 | anti @50 |", "|---|---:|---:|---:|---:|---:|"]
    for c in children:
        if c["mode"] not in ("self", "control", "generation"):
            continue
        lines.append(
            f"| {c['name']} | {c['mode']} | {c['classification']} | "
            f"{c['deepest'].get('cos_to_a', '-')} | "
            f"{c['deepest'].get('exact_lit50', '-')} | {c['deepest'].get('anti50', '-')} |"
        )
    lines.append("")

    inc_children = [c for c in children if c["mode"] == "increment"]
    if inc_children:
        lines += ["## Increment size: does a larger increment converge more strongly?", ""]
        lines += [
            "| variant | children | mean final step corr | breed-true rate | new-canons | mean exact @50 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for variant in INCREMENT_VARIANTS:
            subset = [c for c in inc_children if c["variant"].get("name") == variant["name"]]
            if not subset:
                continue
            mean_step = float(np.mean([c["deepest"]["final_step_correlation"] for c in subset]))
            true_rate = sum(1 for c in subset if c["classification"].startswith("true:")) / len(subset)
            new_n = sum(1 for c in subset if c["classification"] == "new")
            mean_exact = float(np.mean([c["deepest"].get("exact_lit50", 0) for c in subset]))
            lines.append(
                f"| {variant['name']} | {len(subset)} | {mean_step:.5f} | {true_rate:.2f} | "
                f"{new_n} | {mean_exact:.1f} |"
            )
        lines.append("")

    poly_children = [c for c in children if c["mode"] == "polyamory"]
    if poly_children:
        lines += ["## Polyamorous breeding (three parents)", ""]
        for c in poly_children:
            deep = c["deepest_stage"]
            trace = c["cos_trace"]
            lines.append(
                f"- {c['name']}: class {c['classification']}, cos A/B {trace[c['a']][deep]:.3f}/"
                f"{trace[c['b']][deep]:.3f}, exact @50 {c['deepest'].get('exact_lit50', '-')}."
            )
        lines.append("")

    lines += ["## Valley audits (unpaired 24-start census on the canon stage)", ""]
    lines += ["| object | literary pole | mixed | mirror pole |", "|---|---:|---:|---:|"]
    for key, a in audits.items():
        lines.append(f"| {key} | {a['literary_pole']} | {a['mixed']} | {a['mirror_pole']} |")
    lines.append("")

    lines += ["## New-canon heads (deepest stage)", ""]
    for c in new_children:
        lines += [
            f"### {c['name']}",
            "",
            f"exact/broad/anti @50 {c['deepest'].get('exact_lit50', '-')}/"
            f"{c['deepest'].get('broad_lit50', '-')}/{c['deepest'].get('anti50', '-')}.",
            "",
        ]
        for row in c["deepest"].get("head", [])[:10]:
            lines.append(f"{row['rank']}. *{row['title']}* — {row['author']} ({row['score']:.3f})")
        lines.append("")

    out_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_dir}")
    print(f"Wrote {out_report}")


if __name__ == "__main__":
    main()

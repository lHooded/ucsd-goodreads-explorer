#!/usr/bin/env python3
"""Ensemble convergence-reversal: do many reversed random juries point at a literary center?

Hypothesis under test
---------------------
Goodreads' dominant reader is non-literary, so a randomly drawn jury iterated through
the nonlinear attractor map collapses toward the Goodreads center, i.e. AWAY from any
literary head. The convergence-reversal technique (gain-hard pruning of the strongest
proponents of the converged direction, then restart from the same seed) pushes a
literary-leaning seed back toward a literary valley. This experiment asks what happens
when the seed is a PURE RANDOM jury: after reversal, each jury drifts toward some
non-center group. Do those groups, taken together, average out to a literary center?

Because individual reversed juries may land in different non-center basins (literary,
paranormal-romance, fantasy, YA), a plain mean of their endpoints can cancel. We
therefore compare several label-free "processed averages" and also census the basins by
clustering the endpoint preference scores. Literary labels are applied only after every
direction, preference, aggregate, and cluster is frozen.

Evaluation lens
---------------
Literary verdicts are computed in PREFERENCE space (weighted_preferences), matching the
project's established convention; in direction space the degree-corrected operator
already surfaces classics at the center, which would inflate literary counts. Endpoint
directions are kept only for the pairwise-agreement statistic; the basin census clusters
preference scores, which group genres more cleanly than near-orthogonal 26K-dim
directions.

Design
------
- For each jury size n in a sweep, draw K disjoint random juries.
- Jury seed weights members 20.0, everyone else 0.4 (census convention).
- run_jury reproduces the standard map: stage 0 collapses on the full population; later
  stages apply gain-hard pruning and restart from the same jury seed.
- Per jury we keep the stage-0 and deepest-stage book-space direction (for clustering)
  and the stage-0 and deepest-stage preference score vector (for literary scoring).
- Aggregates (label-free): preference-space center, plain mean, coordinate median,
  agreement-weighted consensus, mean displacement; direction-space cluster census.
- Controls: one pooled "big jury" of size n*K, and the preference-space center head.
- Titles / evaluation lists load only after all geometry is frozen.

Memory / disk discipline: single process, sequential juries, no ProcessPool; transient
per-stage objects freed each jury; four 26,418-vectors kept per jury; checkpoints every
N juries; wall-clock safety cap; per-jury failures are skipped, not fatal.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts import research_attractor_pruning as pruning
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year


DATA = Path(__file__).resolve().parents[1] / "data"

BETA = 2.5
ITERATIONS = 20
MAX_STAGES = 8
CLUSTER_THRESHOLD = 0.3
DEFAULT_SEED = 20260807
CHECKPOINT_EVERY = 10


def make_jury_seed(payload: dict[str, np.ndarray], n: int, rng: np.random.Generator) -> np.ndarray:
    n_users = len(payload["user_ids"])
    n = min(n, n_users)
    selected = rng.choice(n_users, size=n, replace=False)
    start = np.full(n_users, 0.4, dtype=np.float32)
    start[selected] = 20.0
    start /= start.mean()
    return start


def run_jury(
    payload: dict[str, np.ndarray],
    matrix,
    start_full: np.ndarray,
    rng: np.random.Generator,
    retained_target: float,
) -> dict[str, Any]:
    """Standard map from a random-jury seed: collapse then gain-hard reversal."""
    n_users = len(payload["user_ids"])
    full_operator, _ = spectral.make_operator(matrix, payload, attractor.CONFIG)
    reference_direction = attractor.normalize_columns(
        full_operator.rmatmat(start_full)
    ).ravel()

    keep = np.arange(n_users, dtype=np.int64)
    stages: list[dict[str, Any]] = []
    stop_reason = "max_stages"
    stage0_pref: np.ndarray | None = None
    last_pref: np.ndarray | None = None
    for stage in range(MAX_STAGES + 1):
        local_payload = pruning.subset_payload(payload, keep)
        sub_matrix, _ = spectral.build_matrix(local_payload)
        operator, _ = spectral.make_operator(sub_matrix, local_payload, attractor.CONFIG)
        start_restricted = start_full[keep] / start_full[keep].mean()
        weights, direction, history = pruning.iterate_map(operator, start_restricted, BETA)
        stage_start_direction = attractor.normalize_columns(
            operator.rmatmat(start_restricted)
        ).ravel()
        preference = attractor.weighted_preferences(sub_matrix, weights)
        if stage == 0:
            stage0_pref = preference["score"].astype(np.float32)
        last_pref = preference["score"].astype(np.float32)
        stages.append(
            {
                "stage": stage,
                "remaining_users": int(len(keep)),
                "cumulative_removed_fraction": 1.0 - len(keep) / n_users,
                "final_step_correlation": history[-1]["step_correlation"],
                "direction_retained_reference": float(np.sum(direction * reference_direction)),
                "direction_retained_stage": float(np.sum(direction * stage_start_direction)),
                "effective_user_share": float(
                    (weights.sum() ** 2 / np.sum(weights**2)) / len(weights)
                ),
                "direction": direction.astype(np.float32),
            }
        )
        if stages[-1]["direction_retained_reference"] >= retained_target:
            stop_reason = "retained_target"
            break
        if stage == MAX_STAGES:
            stop_reason = "max_stages"
            break
        if len(keep) <= pruning.MIN_REMAINING_FRACTION * n_users:
            stop_reason = "evidence_floor"
            break
        removed, n_removed = pruning.remove_fraction(
            weights, start_restricted, "gain", "hard", pruning.LADDER_RATE, rng
        )
        if n_removed == 0:
            stop_reason = "nothing_removed"
            break
        keep = keep[~removed]
        if len(keep) <= pruning.MIN_REMAINING_FRACTION * n_users:
            stop_reason = "evidence_floor"
            break
    return {
        "stop_reason": stop_reason,
        "stages": stages,
        "stage0_pref": stage0_pref,
        "final_pref": last_pref,
    }


def _unit(x: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(x))
    return x / norm if norm > 1e-20 else x


def preference_head(
    score: np.ndarray,
    payload: dict[str, np.ndarray],
    meta: dict[str, Any],
    eval_sets: dict[str, Any],
    limit: int = 50,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """posthoc_head for a preference score vector, all books eligible."""
    preference = {
        "score": np.asarray(score, dtype=np.float64),
        "mean": np.asarray(score, dtype=np.float64),
        "reader_mass": payload["book_n"].astype(np.float64),
    }
    return attractor.posthoc_head(preference, payload["work_ids"], meta, eval_sets, limit=limit)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[2000, 5000, 10000])
    parser.add_argument("--juries", type=int, default=40, help="juries per size")
    parser.add_argument("--hours", type=float, default=0.0, help="wall-clock cap; 0 disables")
    parser.add_argument("--retained-target", type=float, default=1.01,
                        help="kept >1 so random juries prune deeply instead of stopping early")
    parser.add_argument("--cluster-threshold", type=float, default=CLUSTER_THRESHOLD)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--tag", default="ensemble")
    args = parser.parse_args()

    t0 = time.time()
    payload, matrix, matrix_meta = year.load_matrix()
    n_users = len(payload["user_ids"])
    n_books = len(payload["work_ids"])

    rng = np.random.default_rng(args.seed)
    deadline = t0 + args.hours * 3600.0 if args.hours > 0 else float("inf")

    groups: list[dict[str, Any]] = []
    for size in args.sizes:
        records: list[dict[str, Any]] = []
        dir0: list[np.ndarray] = []
        dirdeep: list[np.ndarray] = []
        pref0: list[np.ndarray] = []
        prefdeep: list[np.ndarray] = []
        for j in range(args.juries):
            if time.time() > deadline:
                print(f"wall-clock cap reached at size={size} jury={j}", flush=True)
                break
            t_j = time.time()
            start_full = make_jury_seed(payload, size, rng)
            try:
                run = run_jury(payload, matrix, start_full, rng, args.retained_target)
            except Exception as exc:  # keep the campaign alive past one bad jury
                print(f"jury {j} size {size} FAILED: {exc}", flush=True)
                continue
            dir0.append(run["stages"][0]["direction"])
            dirdeep.append(run["stages"][-1]["direction"])
            pref0.append(run["stage0_pref"])
            prefdeep.append(run["final_pref"])
            records.append(
                {
                    "jury": j,
                    "size": size,
                    "stop_reason": run["stop_reason"],
                    "n_stages": len(run["stages"]),
                    "deepest_users": run["stages"][-1]["remaining_users"],
                    "deepest_removed_fraction": run["stages"][-1]["cumulative_removed_fraction"],
                    "retained_ref_by_stage": [
                        s["direction_retained_reference"] for s in run["stages"]
                    ],
                    "users_by_stage": [s["remaining_users"] for s in run["stages"]],
                    "runtime_seconds": time.time() - t_j,
                }
            )
            print(
                f"size={size} jury={j} stop={run['stop_reason']} "
                f"stages={len(run['stages'])} users={run['stages'][-1]['remaining_users']:,} "
                f"({time.time() - t_j:.1f}s)",
                flush=True,
            )
            if (j + 1) % CHECKPOINT_EVERY == 0:
                _checkpoint(args.tag, [g["size"] for g in groups], size, len(records))

        if dirdeep:
            groups.append(
                {
                    "size": size,
                    "records": records,
                    "dir0": np.stack(dir0).astype(np.float32),
                    "dirdeep": np.stack(dirdeep).astype(np.float32),
                    "pref0": np.stack(pref0).astype(np.float32),
                    "prefdeep": np.stack(prefdeep).astype(np.float32),
                }
            )
            _checkpoint(args.tag, [g["size"] for g in groups], None, None)

    print("Loading post-hoc semantic context", flush=True)
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])

    size_results = []
    for group in groups:
        size = group["size"]
        records = group["records"]
        dirdeep, pref0, prefdeep = group["dirdeep"], group["pref0"], group["prefdeep"]
        k = dirdeep.shape[0]

        # Agreement weights come from endpoint-direction geometry.
        sim = dirdeep @ dirdeep.T
        agreement = (
            (sim.sum(axis=1) - np.diag(sim)) / (k - 1) if k > 1 else np.ones(k)
        )
        agr_weights = np.clip(agreement, 0.0, None)

        # Preference-space processed averages (the literary verdict).
        aggregates = {
            "center_stage0": pref0.mean(axis=0),
            "plain_mean": prefdeep.mean(axis=0),
            "coordinate_median": np.median(prefdeep, axis=0),
            "agreement_consensus": (
                (agr_weights @ prefdeep) if agr_weights.sum() > 0 else prefdeep.mean(axis=0)
            ),
            "mean_displacement": (prefdeep - pref0).mean(axis=0),
        }
        agg_results = {}
        for name, score in aggregates.items():
            head, metrics = preference_head(score, payload, meta, eval_sets, limit=50)
            agg_results[name] = {"metrics": metrics, "head": head[:20]}

        # Per-jury preference-space endpoint metrics.
        per_jury_metrics = []
        for j in range(k):
            _head, metrics = preference_head(prefdeep[j], payload, meta, eval_sets, limit=50)
            per_jury_metrics.append(metrics)

        # Basin census on between-jury preference-score correlation (genres group;
        # raw 26K-dim direction vectors stay nearly orthogonal). Literary-ness is each
        # cluster's mean member preference head.
        pref_centered = prefdeep - prefdeep.mean(axis=1, keepdims=True)
        pref_unit = pref_centered / np.maximum(
            np.linalg.norm(pref_centered, axis=1, keepdims=True), 1e-12
        )
        clusters = attractor.cluster_directions(pref_unit.T, args.cluster_threshold)
        cluster_rows = []
        for members in clusters:
            member_pref = prefdeep[members].mean(axis=0)
            head, metrics = preference_head(member_pref, payload, meta, eval_sets, limit=50)
            cluster_rows.append(
                {
                    "size": len(members),
                    "members": [int(m) for m in members],
                    "metrics": metrics,
                    "head": head[:12],
                }
            )
        cluster_rows.sort(key=lambda row: -row["size"])

        # Big-jury control: one random jury of size n*K (capped).
        big_n = min(size * k, int(0.5 * n_users))
        big_seed = make_jury_seed(payload, big_n, rng)
        big_run = run_jury(payload, matrix, big_seed, rng, args.retained_target)
        big_head, big_metrics = preference_head(
            big_run["final_pref"], payload, meta, eval_sets, limit=50
        )

        size_results.append(
            {
                "size": size,
                "juries": k,
                "records": records,
                "agreement_stats": {
                    "mean": float(np.mean(agreement)),
                    "median": float(np.median(agreement)),
                    "min": float(np.min(agreement)),
                    "max": float(np.max(agreement)),
                },
                "aggregates": agg_results,
                "clusters": cluster_rows,
                "per_jury_metrics": per_jury_metrics,
                "big_jury": {
                    "n": big_n,
                    "stop_reason": big_run["stop_reason"],
                    "metrics": big_metrics,
                    "head": big_head[:20],
                },
            }
        )

    result = {
        "method": {
            "purpose": (
                "reverse the convergence of many random juries and test whether their "
                "ensemble averages toward a literary center"
            ),
            "beta": BETA,
            "iterations": ITERATIONS,
            "max_stages": MAX_STAGES,
            "retained_target": args.retained_target,
            "cluster_threshold": args.cluster_threshold,
            "seed": args.seed,
            "sizes": args.sizes,
            "juries_per_size": args.juries,
            "evaluation_space": "preference",
            "chance_at_50": {
                "exact_lit": 54 / n_books * 50,
                "broad_lit": 424 / n_books * 50,
                "anti": 3258 / n_books * 50,
            },
            "semantic_data_loaded_after_geometry": True,
            "runtime_seconds": time.time() - t0,
        },
        "matrix": {**matrix_meta, "shape": list(matrix.shape)},
        "sizes": [
            {
                "size": sr["size"],
                "juries": sr["juries"],
                "agreement_stats": sr["agreement_stats"],
                "aggregates": sr["aggregates"],
                "clusters": sr["clusters"],
                "per_jury_metrics": sr["per_jury_metrics"],
                "big_jury": sr["big_jury"],
                "records_summary": {
                    "stop_reasons": _stop_counts(sr["records"]),
                    "median_runtime_seconds": float(
                        np.median([r["runtime_seconds"] for r in sr["records"]])
                    ),
                    "median_deepest_users": float(
                        np.median([r["deepest_users"] for r in sr["records"]])
                    ),
                },
            }
            for sr in size_results
        ],
    }
    out_json = DATA / f"jury_ensemble_reversal_{args.tag}.json"
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_report(args, result)
    print(f"Wrote {out_json}")


def _stop_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        counts[r["stop_reason"]] = counts.get(r["stop_reason"], 0) + 1
    return counts


def _checkpoint(tag: str, completed_sizes, in_progress_size, in_progress_juries) -> None:
    status = {
        "tag": tag,
        "completed_sizes": completed_sizes,
        "in_progress_size": in_progress_size,
        "in_progress_juries": in_progress_juries,
        "timestamp": time.time(),
    }
    (DATA / f"jury_ensemble_reversal_{tag}_status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )


def _fmt_head(head: list[dict[str, Any]], n: int = 10) -> list[str]:
    return [
        f"{row['rank']}. *{row['title']}* — {row['author']} ({row['score']:.3f})"
        for row in head[:n]
    ]


def _write_report(args, result: dict[str, Any]) -> None:
    chance = result["method"]["chance_at_50"]
    lines = [
        "# Ensemble convergence-reversal of random juries",
        "",
        "Each random jury is iterated through the standard map (stage 0 collapses to the "
        "Goodreads center), then gain-hard convergence reversal prunes the strongest "
        "proponents of the converged direction and restarts from the same jury seed. This "
        "report asks whether the reversed endpoints of many random juries, taken together, "
        "point at a literary center. Literary scoring is done in preference space after all "
        "directions, preferences, aggregates, and clusters are frozen; endpoint directions "
        "feed only the pairwise-agreement statistic, and the basin census clusters preference "
        "scores.",
        "",
        f"Sizes: **{args.sizes}**; juries per size: **{args.juries}**; runtime: "
        f"**{result['method']['runtime_seconds']:.1f}s**. Chance @50: exact "
        f"{chance['exact_lit']:.2f}, broad {chance['broad_lit']:.2f}, anti "
        f"{chance['anti']:.2f}.",
        "",
    ]
    for sr in result["sizes"]:
        size, k = sr["size"], sr["juries"]
        lines += [
            f"## Jury size {size:,} ({k} juries)",
            "",
            f"Endpoint agreement (mean pairwise direction correlation): mean "
            f"{sr['agreement_stats']['mean']:.3f}, median {sr['agreement_stats']['median']:.3f} "
            f"(min {sr['agreement_stats']['min']:.3f}, max {sr['agreement_stats']['max']:.3f}). "
            f"Stop reasons: {sr['records_summary']['stop_reasons']}; median deepest users "
            f"{sr['records_summary']['median_deepest_users']:,.0f}.",
            "",
            "### Processed averages (preference space)",
            "",
            "| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |",
            "|---|---|---|---|",
        ]
        for name in (
            "center_stage0",
            "plain_mean",
            "coordinate_median",
            "agreement_consensus",
            "mean_displacement",
        ):
            m = sr["aggregates"][name]["metrics"]
            lines.append(
                f"| {name} | {m['exact_lit50']}/{m['exact_lit200']} | "
                f"{m['broad_lit50']}/{m['broad_lit200']} | {m['anti50']}/{m['anti200']} |"
            )
        big = sr["big_jury"]
        lines += [
            f"| big_jury_control (n={big['n']:,}) | {big['metrics']['exact_lit50']}/{big['metrics']['exact_lit200']} | "
            f"{big['metrics']['broad_lit50']}/{big['metrics']['broad_lit200']} | "
            f"{big['metrics']['anti50']}/{big['metrics']['anti200']} |",
            "",
        ]

        if sr["per_jury_metrics"]:
            ex = np.array([m["exact_lit50"] for m in sr["per_jury_metrics"]])
            br = np.array([m["broad_lit50"] for m in sr["per_jury_metrics"]])
            an = np.array([m["anti50"] for m in sr["per_jury_metrics"]])
            lines += [
                "### Per-jury endpoint distribution (@50)",
                "",
                f"exact_lit: mean {ex.mean():.2f}, median {np.median(ex):.0f}, max {ex.max()}; "
                f"broad_lit: mean {br.mean():.2f}, max {br.max()}; anti: mean {an.mean():.2f}. "
                f"{int(np.sum(ex >= 3))}/{k} juries reach exact_lit50 >= 3; "
                f"{int(np.sum(br >= 5))}/{k} reach broad_lit50 >= 5.",
                "",
            ]

        lines += [
            "### Basin census (clustered endpoint preference scores)",
            "",
            f"Preference-correlation threshold {args.cluster_threshold}; "
            f"{len(sr['clusters'])} basins. Literary metrics are each basin's mean member "
            "preference head.",
            "",
            "| basin | juries | exact @50 | broad @50 | anti @50 |",
            "|---:|---:|---:|---:|---:|",
        ]
        for i, cl in enumerate(sr["clusters"], 1):
            m = cl["metrics"]
            lines.append(
                f"| {i} | {cl['size']} | {m['exact_lit50']} | {m['broad_lit50']} | {m['anti50']} |"
            )
        lines.append("")
        for i, cl in enumerate(sr["clusters"][:3], 1):
            lines += [f"#### Basin {i} ({cl['size']} juries) head", ""]
            lines += _fmt_head(cl["head"], 10)
            lines.append("")

        lines += ["### Aggregate heads", ""]
        for name in (
            "center_stage0",
            "agreement_consensus",
            "plain_mean",
            "mean_displacement",
        ):
            head = sr["aggregates"][name]["head"]
            lines += [f"#### {name}", ""]
            lines += _fmt_head(head, 12)
            lines.append("")

    out_report = DATA / f"JURY_ENSEMBLE_REVERSAL_{args.tag.upper()}_REPORT.md"
    out_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_report}")


if __name__ == "__main__":
    main()

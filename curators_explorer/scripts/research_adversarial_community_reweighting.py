#!/usr/bin/env python3
"""Stress the expanded-prior ranking under bounded community influence changes."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo
from curators_explorer.scripts.research_fixed_mass_subsamples import (
    aggregate,
    build_events,
    fit,
)
from curators_explorer.scripts.research_hierarchical_read_selection import (
    EVIDENCE_CAP,
    LOWER_Z,
    expit,
    logit,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BOUNDARY = DATA_DIR / "hierarchical_candidate_boundary.json"
RATIOS = (1.5, 2.0)
SEED = 20_260_813


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--reps", type=int, default=None)
    args = parser.parse_args()
    if args.reps is None:
        args.reps = 80 if args.mode == "quick" else 1_000
    return args


def paths(mode):
    stem = f"adversarial_community_reweighting_{mode}"
    return DATA_DIR / f"{stem}.json", DATA_DIR / f"{stem.upper()}_REPORT.md"


def partition_components(part):
    """Reproduce the central cell posterior and book-level penalty."""
    wins, losses = part["wins"], part["losses"]
    n = wins + losses
    global_p = (wins.sum() + 2.0) / (n.sum() + 4.0)
    book_n = n.sum(axis=1)
    book_p = (wins.sum(axis=1) + 50.0 * global_p) / (book_n + 50.0)
    book_var = book_p * (1.0-book_p) / (book_n + 51.0)
    community_p = (wins.sum(axis=0)+2.0) / (n.sum(axis=0)+4.0)
    prior_mean = expit(
        logit(book_p)[:, None] + logit(community_p)[None, :] - logit(global_p)
    )
    scale = np.minimum(1.0, EVIDENCE_CAP/np.maximum(n, 1.0))
    n_eff = n*scale
    alpha = wins*scale + 8.0*prior_mean
    beta = losses*scale + 8.0*(1.0-prior_mean)
    post_mean = alpha/(alpha+beta)
    observed = n >= 3.0
    observed_n = observed.sum(axis=1)
    equal_mean = post_mean.mean(axis=1)
    observed_mu = np.divide(
        (post_mean*observed).sum(axis=1), observed_n,
        out=equal_mean.copy(), where=observed_n>0,
    )
    raw_var = np.divide(
        (((post_mean-observed_mu[:,None])**2)*observed).sum(axis=1),
        observed_n-1, out=np.zeros_like(equal_mean), where=observed_n>1,
    )
    estimator_var = n_eff*post_mean*(1.0-post_mean)/(8.0+n_eff)**2
    observed_estimator_var = np.divide(
        (estimator_var*observed).sum(axis=1), observed_n,
        out=np.zeros_like(equal_mean), where=observed_n>0,
    )
    observed_tau2 = np.maximum(raw_var-observed_estimator_var, 0.0)
    coverage = observed_n/part["k"]
    reference = (coverage>=0.75) & (book_n>=50.0)
    floor2 = float(np.median(observed_tau2[reference])) if reference.sum()>=10 else 0.0025
    tau = np.sqrt(coverage*observed_tau2 + (1.0-coverage)*floor2)
    penalty = LOWER_Z*tau + np.sqrt(book_var)
    return {
        "post_mean": post_mean,
        "penalty": penalty,
        "equal_score": equal_mean-penalty,
    }


def bounded_worst_mean(values, ratio):
    """Minimum mean over weights whose largest/smallest ratio is at most ratio."""
    ordered = np.sort(values, axis=1)
    prefix = np.cumsum(ordered, axis=1)
    total = prefix[:, -1]
    choices = [total/values.shape[1]]
    k = values.shape[1]
    for m in range(1, k):
        low = prefix[:, m-1]
        choices.append((ratio*low + total-low)/(m*ratio+k-m))
    return np.min(np.vstack(choices), axis=0)


def ranking(scores, publishable):
    idx = np.flatnonzero(publishable)
    return idx[np.argsort(-scores[idx], kind="stable")]


def random_paths(components, ratio, reps, publishable, point_ranking):
    n_works = len(components[0]["penalty"])
    draws = np.zeros((reps, n_works), dtype=np.float32)
    rng = np.random.default_rng(SEED + int(100*ratio))
    half_log = math.log(ratio)/2.0
    for component in components:
        k = component["post_mean"].shape[1]
        raw = np.exp(rng.uniform(-half_log, half_log, size=(reps, k)))
        weights = raw/raw.sum(axis=1, keepdims=True)
        contribution = component["post_mean"] @ weights.T
        contribution -= component["penalty"][:,None]
        draws += (contribution.T/len(components)).astype(np.float32)
    ranks = np.zeros((reps, n_works), dtype=np.uint16)
    j50, j200 = [], []
    for draw in range(reps):
        order = ranking(draws[draw], publishable)
        ranks[draw, order] = np.arange(1,len(order)+1,dtype=np.uint16)
        j50.append(jaccard(point_ranking.tolist(), order.tolist(), 50))
        j200.append(jaccard(point_ranking.tolist(), order.tolist(), 200))
    return draws, ranks, {
        "jaccard50_mean": float(np.mean(j50)),
        "jaccard50_q10": float(np.quantile(j50,.1)),
        "jaccard200_mean": float(np.mean(j200)),
        "jaccard200_q10": float(np.quantile(j200,.1)),
    }


def main():
    args = parse_args()
    out_json, out_report = paths(args.mode)
    t0 = time.time()
    works, arrays = build_events()
    parts = aggregate(arrays, np.ones(len(arrays["value"])), len(works))
    point = fit(parts)
    publishable = point["pair_mass"] >= 10.0
    point_ranking = ranking(point["score"], publishable)
    components = [partition_components(part) for part in parts]
    reproduced = np.mean(
        np.vstack([item["equal_score"] for item in components]), axis=0
    )
    formula_error = float(np.max(np.abs(reproduced-point["score"])))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    stored = boundary["expanded_mass10_top200"]
    stored_ids = [row["work_id"] for row in stored]
    point_ids = [works[i]["work_id"] for i in point_ranking[:200]]
    validation_j200 = jaccard(stored_ids, point_ids, 200)
    if formula_error > 1e-10 or validation_j200 != 1.0:
        raise RuntimeError(
            f"point validation failed: formula={formula_error}, J200={validation_j200}"
        )

    robust = {}
    random = {}
    for ratio in RATIOS:
        print(f"Running community ratio {ratio:.1f}...", flush=True)
        robust_score = np.mean(
            np.vstack([
                bounded_worst_mean(item["post_mean"], ratio)-item["penalty"]
                for item in components
            ]), axis=0,
        )
        robust_order = ranking(robust_score, publishable)
        robust_rank = {int(i): rank+1 for rank,i in enumerate(robust_order)}
        robust[str(ratio)] = {
            "ratio": ratio,
            "jaccard50": jaccard(point_ranking.tolist(), robust_order.tolist(), 50),
            "jaccard200": jaccard(point_ranking.tolist(), robust_order.tolist(), 200),
            "rbo": rbo(point_ranking.tolist(), robust_order.tolist()),
            "score": robust_score,
            "rank": robust_rank,
        }
        draws, ranks, summary = random_paths(
            components, ratio, args.reps, publishable, point_ranking
        )
        random[str(ratio)] = {"draws": draws, "ranks": ranks, "summary": summary}

    work_idx = {row["work_id"]: i for i,row in enumerate(works)}
    rows = []
    for point_rank, work_id in enumerate(point_ids, start=1):
        i = work_idx[work_id]
        row = {
            "rank": point_rank, "work_id": work_id,
            "title": works[i]["title"], "author": works[i]["author"],
            "score": float(100*point["score"][i]),
            "pair_mass": float(point["pair_mass"][i]),
        }
        for ratio in RATIOS:
            key = str(ratio)
            robust_row = robust[key]
            draw = random[key]
            draw_ranks = draw["ranks"][:,i]
            row[f"robust_{key}_score"] = float(100*robust_row["score"][i])
            row[f"robust_{key}_drop"] = float(100*(point["score"][i]-robust_row["score"][i]))
            row[f"robust_{key}_rank"] = robust_row["rank"].get(i)
            row[f"random_{key}_top200_rate"] = float(
                np.mean((draw_ranks>0)&(draw_ranks<=200))
            )
            row[f"random_{key}_rank_q10"] = float(np.quantile(draw_ranks,.1))
            row[f"random_{key}_rank_q90"] = float(np.quantile(draw_ranks,.9))
        row["community_status"] = (
            "broadly_stable"
            if row["robust_2.0_rank"] <= 200 and row["random_2.0_top200_rate"] >= .8
            else "mixture_sensitive"
        )
        rows.append(row)

    result = {
        "meta": {
            "purpose": "bounded shared and book-specific community influence stress",
            "mode": args.mode, "replicates_per_ratio": args.reps,
            "expanded_candidates": len(works),
            "publishable_mass10": int(publishable.sum()),
            "point_formula_max_abs_error": formula_error,
            "point_boundary_jaccard200": validation_j200,
            "runtime_seconds": time.time()-t0,
            "interpretation": "ratio R means no community receives more than R times another within a partition",
        },
        "ratios": {
            key: {
                **value["summary"],
                "robust_jaccard50": robust[key]["jaccard50"],
                "robust_jaccard200": robust[key]["jaccard200"],
                "robust_rbo": robust[key]["rbo"],
            }
            for key,value in random.items()
        },
        "counts": {
            "broadly_stable": sum(row["community_status"]=="broadly_stable" for row in rows),
            "mixture_sensitive": sum(row["community_status"]=="mixture_sensitive" for row in rows),
        },
        "books": rows,
    }
    out_json.write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n", encoding="utf-8"
    )
    lines = [
        "# Adversarial community-influence audit", "", "## Design", "",
        "Communities start with equal influence. The shared-mixture path repeatedly changes "
        "those influences for the entire catalog while limiting the largest community weight "
        "to R times the smallest. The least-favourable path gives each individual book the "
        "most adverse mixture allowed by the same bound. The latter is intentionally severe "
        "and remains a sensitivity bound, not the point score.", "",
        f"- Mode: **{args.mode}**; shared mixtures per bound: **{args.reps:,}**.",
        f"- Point validation: formula error **{formula_error:.2g}**; stored top-200 "
        f"Jaccard **{validation_j200:.3f}**.", "",
        "| max community ratio | shared mean J@50 | shared q10 J@50 | shared mean J@200 | shared q10 J@200 | least-favourable J@50 | least-favourable J@200 |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for ratio in RATIOS:
        row = result["ratios"][str(ratio)]
        lines.append(
            f"| {ratio:.1f} | {row['jaccard50_mean']:.3f} | {row['jaccard50_q10']:.3f} | "
            f"{row['jaccard200_mean']:.3f} | {row['jaccard200_q10']:.3f} | "
            f"{row['robust_jaccard50']:.3f} | {row['robust_jaccard200']:.3f} |"
        )
    lines += [
        "", f"Within the point top 200, **{result['counts']['broadly_stable']}** books are "
        f"broadly stable and **{result['counts']['mixture_sensitive']}** are mixture-sensitive "
        "under the preregistered R=2 rule.", "", "## Point head trajectories", "",
        "| # | book | point | R1.5 worst score/rank | R2 worst score/rank | R2 shared ranks | R2 top200 | status |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows[:60]:
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | {row['score']:.1f} | "
            f"{row['robust_1.5_score']:.1f}/{row['robust_1.5_rank']} | "
            f"{row['robust_2.0_score']:.1f}/{row['robust_2.0_rank']} | "
            f"{row['random_2.0_rank_q10']:.0f}-{row['random_2.0_rank_q90']:.0f} | "
            f"{100*row['random_2.0_top200_rate']:.0f}% | {row['community_status']} |"
        )
    lines += [
        "", "The least-favourable path compounds the central model's existing disagreement "
        "penalty, so it should flag dependence rather than replace the main ranking. Shared "
        "mixtures are the cleaner test of whether a common change in community influence "
        "destabilizes the catalog.", "",
    ]
    out_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_report} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

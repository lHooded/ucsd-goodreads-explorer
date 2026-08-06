#!/usr/bin/env python3
"""Hard-versus-soft jury and community membership ablation.

Jury mass is the empirical probability that a broad-pool user enters the jury
across completed teacher-composition refits. Community mass is a sparse top-two
cosine-centroid responsibility, calibrated by its mean maximum responsibility.
Every user's community responsibilities sum to one, so soft membership never
creates multiple full votes.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.stats import spearmanr

from curators_explorer.scripts.research_consensus_stability_pilot import (
    JURY_N,
    build_partitions,
    build_preference_embedding,
    jaccard,
    materialize_pilot_users,
    rbo,
    reconstruct_jury,
)
from curators_explorer.scripts.research_exposure_adjusted_consensus import (
    CENTRAL_SPEC,
    aggregate_spec,
)
from curators_explorer.scripts.research_overnight_uncertainty import (
    build_expected_pair_matrices,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CHECKPOINT = DATA_DIR / "overnight_jury_bootstrap_full_checkpoint.npz"
EXACT_JSON = DATA_DIR / "overnight_uncertainty_full.json"
TARGETS = (0.90, 0.75, 0.60)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    return parser.parse_args()


def outputs(mode):
    stem = f"soft_membership_{mode}"
    return DATA_DIR / f"{stem}.json", DATA_DIR / f"{stem.upper()}_REPORT.md"


def weighted_counts(partitions, user_weight, positive, negative, responsibilities=None):
    out = []
    rows = np.flatnonzero(user_weight > 0)
    for pidx, part in enumerate(partitions):
        k = int(part["k"])
        if responsibilities is None:
            indicator = sparse.csr_matrix(
                (
                    user_weight[rows].astype(np.float32),
                    (rows, part["labels"][rows].astype(np.int32)),
                ),
                shape=(len(user_weight), k),
            )
            wins = np.asarray((indicator.T @ positive).toarray().T, dtype=np.float64)
            losses = np.asarray((indicator.T @ negative).toarray().T, dtype=np.float64)
            sizes = np.asarray(indicator.sum(axis=0)).ravel()
        else:
            member = responsibilities[pidx] * user_weight[:, None]
            wins = np.asarray(positive.T @ member, dtype=np.float64)
            losses = np.asarray(negative.T @ member, dtype=np.float64)
            sizes = member.sum(axis=0)
        out.append(
            {
                "label": part["label"],
                "k": k,
                "wins": wins,
                "losses": losses,
                "current_sizes": sizes,
            }
        )
    return out


def centroid_similarities(embedding, labels, k):
    centers = np.zeros((k, embedding.shape[1]), dtype=np.float64)
    np.add.at(centers, labels, embedding)
    sizes = np.bincount(labels, minlength=k).astype(float)
    centers /= np.maximum(sizes[:, None], 1.0)
    centers /= np.maximum(np.linalg.norm(centers, axis=1)[:, None], 1e-12)
    return np.asarray(embedding @ centers.T, dtype=np.float64)


def top_two_responsibilities(similarities, temperature):
    logits = similarities / temperature
    logits -= logits.max(axis=1, keepdims=True)
    probability = np.exp(logits)
    probability /= probability.sum(axis=1, keepdims=True)
    if probability.shape[1] > 2:
        keep = np.argpartition(probability, -2, axis=1)[:, -2:]
        sparse_probability = np.zeros_like(probability)
        rr = np.arange(len(probability))[:, None]
        sparse_probability[rr, keep] = probability[rr, keep]
        probability = sparse_probability
        probability /= probability.sum(axis=1, keepdims=True)
    return probability


def calibrate_responsibilities(similarities, reference_weight, target):
    def fit(temp):
        p = top_two_responsibilities(similarities, temp)
        mean_max = float(np.average(p.max(axis=1), weights=reference_weight))
        return p, mean_max

    low, high = 1e-4, 20.0
    for _ in range(45):
        middle = (low + high) / 2.0
        _p, mean_max = fit(middle)
        if mean_max > target:
            low = middle
        else:
            high = middle
    p, mean_max = fit((low + high) / 2.0)
    entropy = -(p * np.log(np.maximum(p, 1e-12))).sum(axis=1)
    return p.astype(np.float32), {
        "temperature": float((low + high) / 2.0),
        "weighted_mean_max_membership": mean_max,
        "weighted_mean_effective_memberships": float(
            np.average(np.exp(entropy), weights=reference_weight)
        ),
        "argmax_fidelity": None,
    }


def ranking_summary(label, metric, baseline, works):
    base_rank = baseline["ranking"]
    ranking = metric["ranking"]
    common = np.flatnonzero(baseline["eligible"] & metric["eligible"])
    rho = None
    if len(common) > 1:
        rho = float(spearmanr(baseline["score"][common], metric["score"][common]).statistic)
    base_top = set(base_rank[:200])
    this_top = set(ranking[:200])
    top_for_diag = np.asarray(ranking[:200], dtype=int)
    finite_uncertainty = metric["uncertainty"][top_for_diag]
    finite_heterogeneity = metric["heterogeneity"][top_for_diag]
    finite_partition = metric["partition_sd"][top_for_diag]
    entrants = [
        {
            "work_id": works[i]["work_id"],
            "title": works[i]["title"],
            "author": works[i]["author"],
            "rank": ranking.index(i) + 1,
        }
        for i in ranking[:200] if i not in base_top
    ]
    leavers = [
        {
            "work_id": works[i]["work_id"],
            "title": works[i]["title"],
            "author": works[i]["author"],
            "old_rank": base_rank.index(i) + 1,
        }
        for i in base_rank[:200] if i not in this_top
    ]
    eligible_gain = np.flatnonzero(metric["eligible"] & ~baseline["eligible"])
    eligible_loss = np.flatnonzero(baseline["eligible"] & ~metric["eligible"])
    pop_idx = np.flatnonzero(metric["eligible"])
    pop_rho = None
    if len(pop_idx) > 1:
        pop_rho = float(
            spearmanr(
                np.log1p([works[i]["catalog_n"] for i in pop_idx]),
                metric["score"][pop_idx],
            ).statistic
        )
    return {
        "label": label,
        "n_rankable": int(metric["n_rankable"]),
        "eligible_gain": int(len(eligible_gain)),
        "eligible_loss": int(len(eligible_loss)),
        "jaccard_50": jaccard(base_rank, ranking, 50),
        "jaccard_200": jaccard(base_rank, ranking, 200),
        "rbo": rbo(base_rank, ranking),
        "common_rankable_score_spearman": rho,
        "score_catalog_spearman": pop_rho,
        "median_top200_uncertainty": float(np.nanmedian(finite_uncertainty)),
        "median_top200_partition_sd": float(np.nanmedian(finite_partition)),
        "median_top200_heterogeneity": float(np.nanmedian(finite_heterogeneity)),
        "entrants": entrants,
        "leavers": leavers,
        "top100": [
            {
                **works[i],
                "rank": rank,
                "score": float(100 * metric["score"][i]),
                "uncertainty": float(100 * metric["uncertainty"][i]),
                "coverage": float(metric["coverage"][i]),
            }
            for rank, i in enumerate(ranking[:100], start=1)
        ],
    }


def write_report(result, path):
    b = result["variants"][0]
    q = result["jury_weights"]
    lines = [
        "# Soft jury and community membership pilot",
        "",
        "## Design",
        "",
        "The hard jury is compared with bootstrap inclusion weights `q_u`. These weights sum "
        "to exactly 4,929 juror equivalents and remain bounded by one. Community alternatives "
        "use top-two cosine-centroid responsibilities summing to one per user; truncating at "
        "two prevents infinitesimal memberships from fabricating universal exposure.",
        "",
        f"- Mode: **{result['meta']['mode']}**; community partitions: "
        f"**{result['meta']['n_partitions']}**.",
        f"- Soft-jury nonzero users: **{q['nonzero_users']:,}**; Kish effective users: "
        f"**{q['kish_effective_users']:.1f}**; total mass: **{q['total_mass']:.1f}**.",
        f"- Exact hard baseline: **{b['n_rankable']}** rankable books.",
        "",
        "## Ablation results",
        "",
        "| variant | rankable | gain/loss | J@50 | J@200 | RBO | score ρ | pop ρ | med partition u | med heterogeneity |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["variants"]:
        lines.append(
            f"| {row['label']} | {row['n_rankable']} | +{row['eligible_gain']}/-{row['eligible_loss']} | "
            f"{row['jaccard_50']:.3f} | {row['jaccard_200']:.3f} | {row['rbo']:.3f} | "
            f"{row['common_rankable_score_spearman']:.3f} | {row['score_catalog_spearman']:.3f} | "
            f"{100*row['median_top200_partition_sd']:.2f} | "
            f"{100*row['median_top200_heterogeneity']:.2f} |"
        )
    if result["meta"]["mode"] == "full":
        lines += [
            "",
            "## Decision",
            "",
            "Use bootstrap jury-inclusion probability as the preferred continuous jury "
            "weight, while retaining the hard 4,929-person cut as a sensitivity axis. The "
            "soft jury preserves exactly the same total mass and produces only modest head "
            "movement.",
            "",
            "Do not make fuzzy community membership the default. The 0.90 mean-primary "
            "top-two version is useful as a conservative audit, but the 0.75 and 0.60 paths "
            "change eligibility and the ranking substantially while mechanically shrinking "
            "partition sensitivity. That is smoothing, not demonstrated discovery of a truer "
            "consensus.",
        ]
    lines += [
        "",
        "## Guardrails",
        "",
        "- A fall in estimated heterogeneity under fuzzy communities is partly mechanical; it "
        "is not by itself evidence of a truer consensus.",
        "- Soft jury mass tests uncertainty at the existing jury boundary. It does not discover "
        "a new estimand or repair missing exposure.",
        "- Community weights remain an audit/aggregation layer. They do not nominate books.",
        "- Rankability gains are evidence gains, not automatic evidence of canonical status.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    out_json, out_report = outputs(args.mode)
    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, scores, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, hard_mask, _ = materialize_pilot_users(con, all_ids, scores, broad)
    embedding, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(embedding, hard_mask)
    positive, negative, works, eligible, pair_meta = build_expected_pair_matrices(
        con, len(broad_ids), current_only=False
    )

    with np.load(CHECKPOINT, allow_pickle=False) as saved:
        completed = int(saved["completed"])
        q = saved["selected_counts"].astype(np.float64) / completed
    if len(q) != len(broad_ids) or not np.isclose(q.sum(), JURY_N):
        raise RuntimeError("soft jury checkpoint does not match reconstructed broad pool")
    hard_weight = hard_mask.astype(np.float64)
    hard_counts = weighted_counts(partitions, hard_weight, positive, negative)
    baseline = aggregate_spec(hard_counts, CENTRAL_SPEC, eligible)
    exact = json.loads(EXACT_JSON.read_text(encoding="utf-8"))
    expected_top = exact["exact_top_work_ids"]
    observed_top = [works[i]["work_id"] for i in baseline["ranking"]]
    if expected_top != observed_top:
        raise RuntimeError("hard weighted baseline does not reproduce completed exact ranking")

    variants = [("hard jury / hard communities", hard_weight, None)]
    variants.append(("soft jury q / hard communities", q, None))
    target_values = TARGETS[:1] if args.mode == "quick" else TARGETS
    calibration = {}
    for target in target_values:
        memberships = []
        part_meta = []
        for part in partitions:
            sim = centroid_similarities(embedding, part["labels"], int(part["k"]))
            membership, meta = calibrate_responsibilities(sim, q, target)
            meta["argmax_fidelity"] = float(
                np.mean(np.argmax(membership, axis=1) == part["labels"])
            )
            memberships.append(membership)
            part_meta.append({"partition": part["label"], **meta})
        label = f"top2 communities mean-max {target:.2f}"
        calibration[label] = part_meta
        variants.append((f"hard jury / {label}", hard_weight, memberships))
        variants.append((f"soft jury q / {label}", q, memberships))

    summaries = []
    for label, weights, membership in variants:
        print(f"Scoring {label}…", flush=True)
        counts = weighted_counts(
            partitions, weights, positive, negative, responsibilities=membership
        )
        metric = aggregate_spec(counts, CENTRAL_SPEC, eligible)
        summaries.append(ranking_summary(label, metric, baseline, works))

    result = {
        "meta": {
            "purpose": "hard-versus-soft jury and community membership ablation",
            "mode": args.mode,
            "runtime_seconds": time.time() - t0,
            "n_partitions": len(partitions),
            "n_works": len(works),
            "community_membership": "top-two centroid responsibilities; per-user sum one",
        },
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "pair_data": pair_meta,
        "jury_weights": {
            "source_replicates": completed,
            "total_mass": float(q.sum()),
            "nonzero_users": int(np.sum(q > 0)),
            "kish_effective_users": float(q.sum() ** 2 / np.sum(q * q)),
            "hard_jury_users": int(hard_mask.sum()),
            "hard_soft_weight_correlation": float(
                np.corrcoef(hard_weight, q)[0, 1]
            ),
        },
        "community_calibration": calibration,
        "variants": summaries,
    }
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(result, out_report)
    con.close()
    print(f"Wrote {out_report} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

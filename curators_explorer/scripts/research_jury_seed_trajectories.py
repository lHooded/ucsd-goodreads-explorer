#!/usr/bin/env python3
"""Jury feature-family × pair-sampling-seed consensus trajectories.

This extends the joint multiverse along two axes that were previously deferred:

* which generic behavioral feature family reconstructs the jury;
* which deterministic balanced within-user book sample defines pair votes.

The analysis keeps the rating threshold (5★ versus ≤3★), jury size (4,929),
community partitions, and exposure estimator fixed.  It reports evidence loss
separately from semantic rank movement and intersects survivors with the prior
50-book joint robust tier.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_jury_seed_trajectories
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import svds

from curators_explorer.scripts.research_consensus_multiverse import (
    aggregate_counts,
)
from curators_explorer.scripts.research_consensus_stability_pilot import (
    BROAD_N,
    CLUSTER_COUNTS,
    CLUSTER_SEEDS,
    EMBED_DIM,
    JURY_N,
    MAX_CATALOG_N,
    MAX_ITEM_POOL_SHARE,
    MIN_ITEM_POOL_SUPPORT,
    cosine_kmeans,
    jaccard,
    rbo,
)
from curators_explorer.scripts.research_exposure_adjusted_consensus import (
    CENTRAL_SPEC,
    aggregate_spec,
)
from curators_explorer.scripts.research_jury_rebuild import (
    FEATURES,
    GENERIC_FEATURES,
    NO_ACTIVITY_FEATURES,
    activity_bins,
    fetch_frame,
    materialize_behavior_features,
    materialize_model_frame,
    materialize_rich_behavior_features,
    ridge_oof,
)
from curators_explorer.scripts.research_purity_strictness_sweep import make_jury
from curators_explorer.scripts.research_ratings_only_canon import (
    _con,
    materialize_base,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    materialize_work_author_year,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PRIOR_JSON = DATA_DIR / "consensus_multiverse.json"
OUT_JSON = DATA_DIR / "jury_seed_trajectories.json"
OUT_MD = DATA_DIR / "JURY_SEED_TRAJECTORIES_REPORT.md"

JURY_MODELS = (
    {
        "label": "rich_behavior_global",
        "description": "generic + author/series/year behavior",
        "features": FEATURES,
        "role": "plausible",
    },
    {
        "label": "rich_no_direct_activity",
        "description": "rich behavior without direct shelf-size variables",
        "features": NO_ACTIVITY_FEATURES,
        "role": "plausible",
    },
    {
        "label": "generic_behavior_only",
        "description": "generic rating/popularity behavior; no author/series/year panel",
        "features": GENERIC_FEATURES,
        "role": "adversarial_ablation",
    },
)
PAIR_SEEDS = (11, 23, 47, 89, 131)
BASE_JURY = "rich_behavior_global"
BASE_SEED = 11
MAX_SIDE = 12


def reconstruct_jury_models(con):
    print("Reconstructing behavioral jury feature families…", flush=True)
    t0 = time.time()
    materialize_base(con)
    teacher = make_jury(con, purity=65, strictness=25, name="jury_teacher")
    materialize_work_author_year(con)
    generic_meta = materialize_behavior_features(con)
    rich_meta = materialize_rich_behavior_features(con)
    frame_meta = materialize_model_frame(con)
    ids, folds, y, teacher_w, x = fetch_frame(con)
    bins = activity_bins(x)
    scores = {}
    coefficients = {}
    selected = {}
    for spec in JURY_MODELS:
        label = spec["label"]
        print(f"  fitting {label} ({len(spec['features'])} features)", flush=True)
        score, coef = ridge_oof(
            x,
            y,
            teacher_w,
            folds,
            bins,
            spec["features"],
            matched=False,
        )
        scores[label] = score
        coefficients[label] = coef
        order = np.argsort(-score, kind="stable")
        selected[label] = ids[order[:JURY_N]]
    baseline_set = set(int(x) for x in selected[BASE_JURY])
    overlaps = {}
    for spec in JURY_MODELS:
        label = spec["label"]
        ids_set = set(int(x) for x in selected[label])
        intersection = len(ids_set & baseline_set)
        overlaps[label] = {
            "with_baseline_n": intersection,
            "with_baseline_jaccard": intersection / len(ids_set | baseline_set),
        }
    meta = {
        "teacher": teacher,
        "generic_features": generic_meta,
        "rich_features": rich_meta,
        "frame": frame_meta,
        "models": [
            {
                "label": spec["label"],
                "description": spec["description"],
                "n_features": len(spec["features"]),
                "role": spec["role"],
                **overlaps[spec["label"]],
                "top_coefficients": [
                    [name, float(value)]
                    for name, value in sorted(
                        coefficients[spec["label"]].items(),
                        key=lambda item: -abs(item[1]),
                    )[:15]
                ],
            }
            for spec in JURY_MODELS
        ],
        "seconds": time.time() - t0,
    }
    return ids, scores, selected, meta


def materialize_analysis_users(con, ids, scores, selected):
    baseline_score = scores[BASE_JURY]
    baseline_order = np.argsort(-baseline_score, kind="stable")
    baseline_broad = [int(x) for x in ids[baseline_order[:BROAD_N]]]
    union = set(baseline_broad)
    for values in selected.values():
        union.update(int(x) for x in values)
    score_by_id = {int(uid): float(score) for uid, score in zip(ids, baseline_score)}
    outsiders = sorted(union - set(baseline_broad), key=lambda uid: -score_by_id[uid])
    ordered = baseline_broad + outsiders
    baseline_selected = set(int(x) for x in selected[BASE_JURY])
    rows = [
        (
            idx,
            uid,
            score_by_id[uid],
            int(uid in baseline_selected),
            idx + 1,
        )
        for idx, uid in enumerate(ordered)
    ]
    con.execute(
        """
        CREATE OR REPLACE TABLE pilot_users(
            user_idx INTEGER, user_id BIGINT, behavior_score DOUBLE,
            is_current INTEGER, broad_rank INTEGER
        )
        """
    )
    con.executemany("INSERT INTO pilot_users VALUES (?, ?, ?, ?, ?)", rows)
    selected_sets = {
        label: set(int(x) for x in values) for label, values in selected.items()
    }
    masks = {
        label: np.asarray([uid in selected_set for uid in ordered], dtype=bool)
        for label, selected_set in selected_sets.items()
    }
    return np.asarray(ordered, dtype=np.int64), masks, {
        "n_analysis_users": len(ordered),
        "n_baseline_broad": len(baseline_broad),
        "n_added_for_alternative_juries": len(outsiders),
        "all_juries_complete": all(int(mask.sum()) == JURY_N for mask in masks.values()),
    }


def build_fixed_preference_embedding(con, n_users: int):
    """Fit on the original rich-model top 20k; project alternative-jury outsiders."""
    print("Building baseline-frozen centered preference embedding…", flush=True)
    t0 = time.time()
    max_support = int(BROAD_N * MAX_ITEM_POOL_SHARE)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE pilot_embed_items AS
        WITH support AS (
            SELECT e.work_id, count(*)::BIGINT AS n_users
            FROM ex.all_rating_events e JOIN pilot_users u USING (user_id)
            WHERE u.broad_rank <= {BROAD_N}
            GROUP BY e.work_id
            HAVING count(*) BETWEEN {MIN_ITEM_POOL_SUPPORT} AND {max_support}
        )
        SELECT work_id,
               (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS item_idx,
               n_users
        FROM support
        """
    )
    d = con.execute(
        """
        SELECT u.user_idx, i.item_idx, e.rating, f.mean_rating, i.n_users
        FROM ex.all_rating_events e
        JOIN pilot_users u USING (user_id)
        JOIN pilot_embed_items i USING (work_id)
        JOIN jury_model_frame f USING (user_id)
        ORDER BY u.user_idx
        """
    ).fetchnumpy()
    row = np.asarray(d["user_idx"], dtype=np.int32)
    col = np.asarray(d["item_idx"], dtype=np.int32)
    rating = np.asarray(d["rating"], dtype=np.float32)
    user_mean = np.asarray(d["mean_rating"], dtype=np.float32)
    support = np.asarray(d["n_users"], dtype=np.float32)
    value = (rating - user_mean) * np.sqrt(
        np.maximum(np.log((BROAD_N + 1.0) / (support + 1.0)), 0.05)
    )
    n_items = int(col.max()) + 1
    matrix = sparse.coo_matrix(
        (value.astype(np.float32), (row, col)), shape=(n_users, n_items)
    ).tocsr()
    row_norm = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
    matrix = sparse.diags(1.0 / np.maximum(row_norm, 1e-8)) @ matrix
    baseline_matrix = matrix[:BROAD_N]
    k = min(EMBED_DIM, min(baseline_matrix.shape) - 1)
    _u, s, vt = svds(
        baseline_matrix, k=k, which="LM", random_state=17
    )
    order = np.argsort(-s)
    s = s[order]
    vt = vt[order]
    embedding = np.asarray(matrix @ vt.T, dtype=np.float32)
    norm = np.linalg.norm(embedding, axis=1)
    embedding /= np.maximum(norm[:, None], 1e-8)
    meta = {
        "n_fit_users": BROAD_N,
        "n_projected_users": n_users - BROAD_N,
        "n_items": n_items,
        "n_events_all_users": int(matrix.nnz),
        "embedding_dim": int(k),
        "singular_values": [float(x) for x in s],
        "signal": "baseline-frozen centered rating residual × mild inverse-popularity weight",
        "seconds": time.time() - t0,
    }
    print(
        f"  fit=({BROAD_N}, {n_items}) projected={n_users-BROAD_N:,} "
        f"nnz={matrix.nnz:,} dim={k} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return embedding, meta


def build_fixed_partitions(embedding, baseline_mask):
    """Fit communities on the original top 20k and assign projected outsiders."""
    print("Fitting baseline-frozen community partitions…", flush=True)
    fit_embedding = embedding[:BROAD_N]
    partitions = []
    for k in CLUSTER_COUNTS:
        for seed in CLUSTER_SEEDS:
            _fit_labels, centers, fit = cosine_kmeans(fit_embedding, k, seed)
            labels = np.argmax(embedding @ centers.T, axis=1).astype(np.int16)
            partitions.append(
                {
                    "label": f"k{k}_s{seed}",
                    "k": k,
                    "seed": seed,
                    "labels": labels,
                    "broad_sizes": np.bincount(labels, minlength=k),
                    "current_sizes": np.bincount(labels[baseline_mask], minlength=k),
                    **fit,
                }
            )
    return partitions


def build_seed_vote_matrices(con, n_users: int, seed: int):
    print(f"Building balanced pair sample seed={seed}…", flush=True)
    t0 = time.time()
    vote_table = f"js_votes_{seed}"
    item_table = f"js_items_{seed}"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {vote_table} AS
        WITH rated AS (
            SELECT u.user_idx, e.user_id, e.work_id, e.rating
            FROM ex.all_rating_events e
            JOIN pilot_users u USING (user_id)
            JOIN work_rarity wr USING (work_id)
            WHERE wr.n >= 100 AND wr.n <= {MAX_CATALOG_N}
        ),
        highs0 AS (
            SELECT *, row_number() OVER (
                PARTITION BY user_id
                ORDER BY hash(user_id || '-' || work_id || '-h{seed}')
            ) AS rn
            FROM rated WHERE rating = 5
        ),
        lows0 AS (
            SELECT *, row_number() OVER (
                PARTITION BY user_id
                ORDER BY hash(user_id || '-' || work_id || '-l{seed}')
            ) AS rn
            FROM rated WHERE rating <= 3
        ),
        hc AS (SELECT user_id, count(*) AS n_high FROM highs0 GROUP BY user_id),
        lc AS (SELECT user_id, count(*) AS n_low FROM lows0 GROUP BY user_id),
        limits AS (
            SELECT h.user_id,
                   least(h.n_high, l.n_low, {MAX_SIDE})::INTEGER AS n_side
            FROM hc h JOIN lc l USING (user_id)
            WHERE least(h.n_high, l.n_low, {MAX_SIDE}) >= 1
        ),
        votes AS (
            SELECT h.user_idx, h.user_id, h.work_id, 1::TINYINT AS positive
            FROM highs0 h JOIN limits z USING (user_id) WHERE h.rn <= z.n_side
            UNION ALL
            SELECT l.user_idx, l.user_id, l.work_id, 0::TINYINT AS positive
            FROM lows0 l JOIN limits z USING (user_id) WHERE l.rn <= z.n_side
        )
        SELECT * FROM votes
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {item_table} AS
        SELECT work_id,
               (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS work_idx
        FROM (SELECT DISTINCT work_id FROM {vote_table})
        """
    )
    d = con.execute(
        f"""
        SELECT v.user_idx, i.work_idx, v.positive
        FROM {vote_table} v JOIN {item_table} i USING (work_id)
        ORDER BY v.user_idx, i.work_idx
        """
    ).fetchnumpy()
    row = np.asarray(d["user_idx"], dtype=np.int32)
    col = np.asarray(d["work_idx"], dtype=np.int32)
    positive_flag = np.asarray(d["positive"], dtype=np.int8) == 1
    n_works = int(col.max()) + 1
    shape = (n_users, n_works)
    positive = sparse.coo_matrix(
        (
            np.ones(int(positive_flag.sum()), dtype=np.float32),
            (row[positive_flag], col[positive_flag]),
        ),
        shape=shape,
    ).tocsr()
    negative = sparse.coo_matrix(
        (
            np.ones(int((~positive_flag).sum()), dtype=np.float32),
            (row[~positive_flag], col[~positive_flag]),
        ),
        shape=shape,
    ).tocsr()
    meta_rows = con.execute(
        f"""
        SELECT
            i.work_idx, i.work_id, s.title, s.author, wr.n,
            NOT coalesce(cf.is_excluded, FALSE)
              AND NOT coalesce(cf.is_nonfiction, FALSE)
              AND NOT coalesce(cf.is_comic, FALSE)
              AND NOT coalesce(cf.is_picture_book, FALSE)
              AND NOT coalesce(cf.is_derivative, FALSE)
              AND NOT coalesce(cf.is_duplicate, FALSE)
              AND NOT coalesce(cf.is_collection, FALSE) AS eligible
        FROM {item_table} i
        JOIN ex.work_scores s USING (work_id)
        JOIN work_rarity wr USING (work_id)
        LEFT JOIN ex.work_flags cf USING (work_id)
        ORDER BY i.work_idx
        """
    ).fetchall()
    works = []
    eligible = np.zeros(n_works, dtype=bool)
    for idx, work_id, title, author, catalog_n, ok in meta_rows:
        works.append(
            {
                "work_idx": int(idx),
                "work_id": str(work_id),
                "title": title,
                "author": author,
                "catalog_n": int(catalog_n),
            }
        )
        eligible[int(idx)] = bool(ok)
    stats = con.execute(
        f"""
        SELECT count(DISTINCT user_id), count(*),
               count(*) FILTER (WHERE positive=1),
               count(*) FILTER (WHERE positive=0)
        FROM {vote_table}
        """
    ).fetchone()
    meta = {
        "seed": seed,
        "n_users": int(stats[0]),
        "n_votes": int(stats[1]),
        "positive_votes": int(stats[2]),
        "negative_votes": int(stats[3]),
        "n_works": n_works,
        "seconds": time.time() - t0,
    }
    return positive, negative, works, eligible, meta


def make_universe(label: str, jury: str, seed: int, metric, works):
    return {
        "label": label,
        "jury": jury,
        "seed": seed,
        "metric": metric,
        "works": works,
        "ranking": [works[idx]["work_id"] for idx in metric["ranking"]],
        "n_rankable": metric["n_rankable"],
    }


def rank_map(universe):
    return {work_id: rank + 1 for rank, work_id in enumerate(universe["ranking"])}


def score_map(universe, field="score"):
    metric = universe["metric"]
    return {
        universe["works"][idx]["work_id"]: float(100.0 * metric[field][idx])
        for idx in metric["ranking"]
        if np.isfinite(metric[field][idx])
    }


def diagnose(universes, baseline, gamma15_baseline, prior):
    maps = {universe["label"]: rank_map(universe) for universe in universes}
    base_map = maps[baseline["label"]]
    scores = score_map(baseline)
    uncertainty = score_map(baseline, "uncertainty")
    gamma15_scores = score_map(gamma15_baseline)
    metadata = {}
    for universe in universes:
        metadata.update({x["work_id"]: x for x in universe["works"]})
    plausible_juries = [x for x in JURY_MODELS if x["role"] == "plausible"]
    jury_labels = [f"{x['label']}__seed{BASE_SEED}" for x in plausible_juries]
    adversarial_labels = [
        f"{x['label']}__seed{BASE_SEED}"
        for x in JURY_MODELS
        if x["role"] == "adversarial_ablation"
    ]
    seed_labels = [f"{BASE_JURY}__seed{seed}" for seed in PAIR_SEEDS]
    plausible_cross_labels = [
        f"{jury['label']}__seed{seed}"
        for jury in plausible_juries
        for seed in PAIR_SEEDS
    ]
    missing = max(x["n_rankable"] for x in universes) + 1
    prior_ids = {x["work_id"] for x in prior["jointly_robust"]}
    rows = []
    for work_id, central_rank in sorted(base_map.items(), key=lambda item: item[1]):
        jury_present = np.asarray([work_id in maps[label] for label in jury_labels])
        seed_present = np.asarray([work_id in maps[label] for label in seed_labels])
        jury_ranks = np.asarray([maps[label].get(work_id, missing) for label in jury_labels])
        seed_ranks = np.asarray([maps[label].get(work_id, missing) for label in seed_labels])
        cross_ranks = np.asarray(
            [maps[label].get(work_id, missing) for label in plausible_cross_labels]
        )
        adversarial_present = np.asarray(
            [work_id in maps[label] for label in adversarial_labels]
        )
        adversarial_ranks = np.asarray(
            [maps[label].get(work_id, missing) for label in adversarial_labels]
        )
        row = {
            **metadata[work_id],
            "central_rank": central_rank,
            "central_score": scores.get(work_id),
            "central_uncertainty": uncertainty.get(work_id),
            "gamma15_score": gamma15_scores.get(work_id),
            "jury_rankable_rate": float(np.mean(jury_present)),
            "jury_top200_rate": float(np.mean(jury_ranks <= 200)),
            "seed_rankable_rate": float(np.mean(seed_present)),
            "seed_top200_rate": float(np.mean(seed_ranks <= 200)),
            "cross_top200_rate": float(np.mean(cross_ranks <= 200)),
            "jury_rank_range": int(jury_ranks.max() - jury_ranks.min()),
            "seed_rank_range": int(seed_ranks.max() - seed_ranks.min()),
            "cross_rank_range": int(cross_ranks.max() - cross_ranks.min()),
            "adversarial_rankable_rate": float(np.mean(adversarial_present)),
            "adversarial_top200_rate": float(np.mean(adversarial_ranks <= 200)),
            "in_prior_joint_robust": work_id in prior_ids,
            "jury_ranks": {label: int(rank) for label, rank in zip(jury_labels, jury_ranks)},
            "seed_ranks": {label: int(rank) for label, rank in zip(seed_labels, seed_ranks)},
        }
        rows.append(row)
    central = [x for x in rows if x["central_rank"] <= 200]
    axis_robust = [
        x
        for x in central
        if x["central_score"] >= 50
        and x["gamma15_score"] is not None
        and x["gamma15_score"] >= 50
        and x["jury_top200_rate"] == 1.0
        and x["seed_top200_rate"] >= 0.80
        and x["cross_top200_rate"] >= 0.80
    ]
    cumulative = [x for x in axis_robust if x["in_prior_joint_robust"]]
    feature_sensitive = [
        x
        for x in central
        if x["jury_rankable_rate"] == 1.0 and x["jury_top200_rate"] < 1.0
    ]
    feature_evidence = [x for x in central if x["jury_rankable_rate"] < 1.0]
    seed_sensitive = [
        x
        for x in central
        if x["seed_rankable_rate"] == 1.0 and x["seed_top200_rate"] < 0.80
    ]
    seed_evidence = [x for x in central if x["seed_rankable_rate"] < 1.0]
    adversarial_rankable = [x for x in central if x["adversarial_rankable_rate"] > 0]
    feature_sensitive.sort(key=lambda x: (-x["jury_rank_range"], x["central_rank"]))
    feature_evidence.sort(key=lambda x: (x["jury_rankable_rate"], x["central_rank"]))
    seed_sensitive.sort(key=lambda x: (-x["seed_rank_range"], x["central_rank"]))
    seed_evidence.sort(key=lambda x: (x["seed_rankable_rate"], x["central_rank"]))
    return (
        rows,
        axis_robust,
        cumulative,
        feature_sensitive,
        feature_evidence,
        seed_sensitive,
        seed_evidence,
        adversarial_rankable,
    )


def stability_rows(universes, baseline):
    base = baseline["ranking"]
    rows = []
    for universe in universes:
        rows.append(
            {
                "label": universe["label"],
                "jury": universe["jury"],
                "seed": universe["seed"],
                "n_rankable": universe["n_rankable"],
                "jaccard50": jaccard(base, universe["ranking"], 50),
                "jaccard200": jaccard(base, universe["ranking"], 200),
                "rbo98": rbo(base, universe["ranking"], p=0.98),
            }
        )
    return rows


def write_book_table(lines, rows, limit=40):
    lines += [
        "| book | base | score ± u | Γ1.5 | jury | seeds | crossed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows[:limit]:
        lines.append(
            f"| {row['title']} — {row['author']} | {row['central_rank']} | "
            f"{row['central_score']:.1f} ± {row['central_uncertainty']:.1f} | "
            f"{row['gamma15_score']:.1f} | {100*row['jury_top200_rate']:.0f}%/"
            f"{100*row['jury_rankable_rate']:.0f}% | {100*row['seed_top200_rate']:.0f}%/"
            f"{100*row['seed_rankable_rate']:.0f}% | {100*row['cross_top200_rate']:.0f}% |"
        )


def write_report(results):
    lines = [
        "# Jury-feature and pair-seed trajectories",
        "",
        "## Design",
        "",
        "Two plausible rich-behavior jury reconstructions and one generic-only adversarial "
        "ablation are crossed with five deterministic balanced pair samples. Jury size, "
        "5★ versus ≤3★ semantics, and the exposure-adjusted score are fixed. The latent "
        "space and communities are fitted only on the original rich-model top 20,000; "
        "alternative-jury outsiders are projected into that frozen space.",
        "",
        f"- Universes: **{results['meta']['n_universes']}**.",
        f"- Analysis users: **{results['population']['n_analysis_users']:,}**; alternative "
        f"juries add **{results['population']['n_added_for_alternative_juries']:,}** people "
        "outside the rich-model top 20,000.",
        f"- Previous-central versus new-central Jaccard@200: "
        f"**{results['prior_baseline_comparison']['jaccard200']:.3f}**.",
        "",
        "## Jury reconstruction overlap",
        "",
        "| jury | role | features | overlap with baseline | Jaccard |",
        "|---|---|---:|---:|---:|",
    ]
    for model in results["jury_reconstruction"]["models"]:
        lines.append(
            f"| {model['label']} | {model['role']} | {model['n_features']} | "
            f"{model['with_baseline_n']:,} | {model['with_baseline_jaccard']:.3f} |"
        )
    lines += [
        "",
        "## One-factor stability",
        "",
        "| universe | rankable | J@50 | J@200 | RBO |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in results["stability"]:
        if row["jury"] == BASE_JURY or row["seed"] == BASE_SEED:
            lines.append(
                f"| {row['label']} | {row['n_rankable']} | {row['jaccard50']:.3f} | "
                f"{row['jaccard200']:.3f} | {row['rbo98']:.3f} |"
            )
    counts = results["counts"]
    lines += [
        "",
        "## Result",
        "",
        f"- **{counts['axis_robust']}** central books pass the new feature/seed axes.",
        f"- **{counts['cumulative_robust']}** of the prior 50 jointly robust books also pass; "
        "this is the current cumulative core.",
        f"- Plausible feature family: **{counts['feature_sensitive']}** semantic and "
        f"**{counts['feature_evidence_sensitive']}** evidence-sensitive central books.",
        f"- The generic-only ablation can rank only **{counts['adversarial_rankable']}** "
        "central books. Its 4% jury overlap and evidence collapse make it a useful "
        "falsification test, not an equal-vote veto on the literary estimand.",
        f"- Pair seed: **{counts['seed_sensitive']}** semantic and "
        f"**{counts['seed_evidence_sensitive']}** evidence-sensitive central books.",
        "",
        "A sampling-seed failure means the book's estimate depends on which finite set of each "
        "reader's high/low ratings was sampled. It should be addressed by repeated-sample "
        "aggregation or by using all bounded per-user votes, not interpreted as constituency "
        "disagreement.",
        "",
        "## Cumulative robust core",
        "",
    ]
    write_book_table(lines, results["cumulative_robust"], limit=60)
    lines += ["", "## Plausible feature-family-sensitive books", ""]
    if results["feature_sensitive"]:
        write_book_table(lines, results["feature_sensitive"])
    else:
        lines.append("None among books rankable under both plausible feature-family juries.")
    lines += ["", "## Pair-sampling-seed-sensitive books", ""]
    if results["seed_sensitive"]:
        write_book_table(lines, results["seed_sensitive"])
    else:
        lines.append("None among books rankable under every pair-sampling seed.")
    lines += [
        "",
        "## Recommendation",
        "",
        results["recommendation"],
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    t_all = time.time()
    prior = json.loads(PRIOR_JSON.read_text(encoding="utf-8"))
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    ids, scores, selected, jury_meta = reconstruct_jury_models(con)
    con.execute("PRAGMA threads=8")
    analysis_ids, masks, population_meta = materialize_analysis_users(
        con, ids, scores, selected
    )
    embedding, embedding_meta = build_fixed_preference_embedding(
        con, len(analysis_ids)
    )
    partitions = build_fixed_partitions(embedding, masks[BASE_JURY])

    seed_data = {}
    seed_meta = []
    for seed in PAIR_SEEDS:
        positive, negative, works, eligible, meta = build_seed_vote_matrices(
            con, len(analysis_ids), seed
        )
        seed_data[seed] = (positive, negative, works, eligible)
        seed_meta.append(meta)

    universes = []
    gamma15_baseline = None
    for seed in PAIR_SEEDS:
        positive, negative, works, eligible = seed_data[seed]
        for spec in JURY_MODELS:
            label = spec["label"]
            counts = aggregate_counts(partitions, masks[label], positive, negative)
            metric = aggregate_spec(counts, CENTRAL_SPEC, eligible, selection_gamma=1.0)
            universe = make_universe(f"{label}__seed{seed}", label, seed, metric, works)
            universes.append(universe)
            if label == BASE_JURY and seed == BASE_SEED:
                gamma15_metric = aggregate_spec(
                    counts, CENTRAL_SPEC, eligible, selection_gamma=1.5
                )
                gamma15_baseline = make_universe(
                    f"{label}__seed{seed}__gamma1p5",
                    label,
                    seed,
                    gamma15_metric,
                    works,
                )
    baseline = next(
        x for x in universes if x["jury"] == BASE_JURY and x["seed"] == BASE_SEED
    )
    diagnostics = diagnose(universes, baseline, gamma15_baseline, prior)
    (
        rows,
        axis_robust,
        cumulative,
        feature_sensitive,
        feature_evidence,
        seed_sensitive,
        seed_evidence,
        adversarial_rankable,
    ) = diagnostics
    stability = stability_rows(universes, baseline)
    prior_ranking = [x["work_id"] for x in prior["central_top"]]
    prior_comparison = {
        "jaccard50": jaccard(prior_ranking, baseline["ranking"], 50),
        "jaccard200": jaccard(prior_ranking, baseline["ranking"], 200),
        "rbo98": rbo(prior_ranking, baseline["ranking"], p=0.98),
    }
    recommendation = (
        "Use the cumulative survivors as the strongest current tier, while retaining all axis "
        "rates rather than converting survival into a new opaque score. Replace the single "
        "pair sample with repeated-seed aggregation before product use. Next calibrate ±u with "
        "user-block resampling. Keep the generic-only jury as an adversarial audit rather than "
        "part of the literary estimand: removing all author/series/year behavior destroys the "
        "jury reconstruction instead of providing a nearby specification."
    )
    results = {
        "meta": {
            "purpose": "jury feature-family × pair-sampling-seed trajectories",
            "n_universes": len(universes),
            "jury_models": [x["label"] for x in JURY_MODELS],
            "pair_seeds": list(PAIR_SEEDS),
            "runtime_seconds": time.time() - t_all,
        },
        "population": population_meta,
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "pair_data": seed_meta,
        "prior_baseline_comparison": prior_comparison,
        "stability": stability,
        "counts": {
            "axis_robust": len(axis_robust),
            "cumulative_robust": len(cumulative),
            "feature_sensitive": len(feature_sensitive),
            "feature_evidence_sensitive": len(feature_evidence),
            "seed_sensitive": len(seed_sensitive),
            "seed_evidence_sensitive": len(seed_evidence),
            "adversarial_rankable": len(adversarial_rankable),
        },
        "axis_robust": axis_robust,
        "cumulative_robust": cumulative,
        "feature_sensitive": feature_sensitive,
        "feature_evidence_sensitive": feature_evidence,
        "seed_sensitive": seed_sensitive,
        "seed_evidence_sensitive": seed_evidence,
        "adversarial_rankable": adversarial_rankable,
        "central_top": rows[:200],
        "book_diagnostics": rows,
        "universes": [
            {
                "label": x["label"],
                "jury": x["jury"],
                "seed": x["seed"],
                "n_rankable": x["n_rankable"],
                "top_work_ids": x["ranking"],
            }
            for x in universes
        ],
        "recommendation": recommendation,
    }
    OUT_JSON.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(results)
    print(f"Wrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    con.close()


if __name__ == "__main__":
    main()

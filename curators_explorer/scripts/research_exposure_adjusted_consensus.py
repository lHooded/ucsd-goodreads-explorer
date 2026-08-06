#!/usr/bin/env python3
"""Exposure-adjusted pilot for a distributed literary consensus.

The preceding community-stability pilot deliberately stress-tested a plausible
ranking, but its community-top-k and leave-one-out diagnostics still mixed
preference with exposure.  This revision separates four quantities:

* conditional esteem among jurors who rated the book,
* between-community taste heterogeneity,
* observed exposure breadth,
* epistemic uncertainty.

Popularity is allowed to determine whether there is enough evidence and how
wide uncertainty is.  It is not a positive term in the score, and evidence in
each community is capped so blockbusters cannot accumulate unlimited leverage.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_exposure_adjusted_consensus
"""

from __future__ import annotations

import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from scipy.stats import spearmanr

from curators_explorer.scripts.research_consensus_stability_pilot import (
    BROAD_N,
    JURY_N,
    MAX_CATALOG_N,
    RUSSIAN_AUTHOR_MARKERS,
    TOP_SAVE,
    build_partitions,
    build_preference_embedding,
    jaccard,
    materialize_pilot_users,
    rbo,
    reconstruct_jury,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


OUT_JSON = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "exposure_adjusted_consensus.json"
)
OUT_MD = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "EXPOSURE_ADJUSTED_CONSENSUS_REPORT.md"
)
PREVIOUS_PILOT_JSON = (
    Path(__file__).resolve().parents[1] / "data" / "consensus_stability_pilot.json"
)

VOTE_SAMPLE_PER_SIDE = 12
VOTE_SEED = 11
LOWER_TAIL_Z = 1.2815515655446004  # Normal 10th percentile.
MIN_VALID_PARTITION_RATE = 2.0 / 3.0
MIN_DISTRIBUTED_COVERAGE = 0.50

# A small one-factor-at-a-time multiverse. None of these values is selected by
# a literary/non-literary probe pile.
CENTRAL_SPEC = {
    "label": "central",
    "min_community_readers": 3,
    "evidence_cap": 30,
    "prior_strength": 4.0,
    "min_global_readers": 30,
}
SPECIFICATIONS = [
    CENTRAL_SPEC,
    {**CENTRAL_SPEC, "label": "community_min_2", "min_community_readers": 2},
    {**CENTRAL_SPEC, "label": "community_min_5", "min_community_readers": 5},
    {**CENTRAL_SPEC, "label": "evidence_cap_15", "evidence_cap": 15},
    {**CENTRAL_SPEC, "label": "evidence_cap_60", "evidence_cap": 60},
    {**CENTRAL_SPEC, "label": "prior_strength_2", "prior_strength": 2.0},
    {**CENTRAL_SPEC, "label": "prior_strength_8", "prior_strength": 8.0},
    {**CENTRAL_SPEC, "label": "global_min_20", "min_global_readers": 20},
    {**CENTRAL_SPEC, "label": "global_min_50", "min_global_readers": 50},
]


def build_conditional_vote_matrices(con, n_users: int):
    """One binary high/low observation per sampled user-book.

    Every included user contributes the same number of positive and negative
    books (up to 12 on each side). This preserves the within-user comparison
    idea while preventing a user's number of available lows from multiplying
    the weight of every high, or vice versa.
    """
    print("Building balanced user-book conditional preference votes…", flush=True)
    t0 = time.time()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE pilot_conditional_votes AS
        WITH rated AS (
            SELECT u.user_idx, e.user_id, e.work_id, e.rating
            FROM ex.all_rating_events e
            JOIN pilot_users u USING (user_id)
            JOIN work_rarity wr USING (work_id)
            WHERE u.is_current = 1
              AND wr.n >= 100 AND wr.n <= {MAX_CATALOG_N}
        ),
        highs0 AS (
            SELECT *, row_number() OVER (
                PARTITION BY user_id
                ORDER BY hash(user_id || '-' || work_id || '-h{VOTE_SEED}')
            ) AS rn
            FROM rated WHERE rating = 5
        ),
        lows0 AS (
            SELECT *, row_number() OVER (
                PARTITION BY user_id
                ORDER BY hash(user_id || '-' || work_id || '-l{VOTE_SEED}')
            ) AS rn
            FROM rated WHERE rating <= 3
        ),
        hc AS (SELECT user_id, count(*) AS n_high FROM highs0 GROUP BY user_id),
        lc AS (SELECT user_id, count(*) AS n_low FROM lows0 GROUP BY user_id),
        limits AS (
            SELECT h.user_id,
                   least(h.n_high, l.n_low, {VOTE_SAMPLE_PER_SIDE})::INTEGER AS n_side
            FROM hc h JOIN lc l USING (user_id)
            WHERE least(h.n_high, l.n_low, {VOTE_SAMPLE_PER_SIDE}) >= 1
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
        """
        CREATE OR REPLACE TABLE pilot_conditional_items AS
        SELECT work_id,
               (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS work_idx
        FROM (SELECT DISTINCT work_id FROM pilot_conditional_votes)
        """
    )
    d = con.execute(
        """
        SELECT v.user_idx, i.work_idx, v.positive
        FROM pilot_conditional_votes v
        JOIN pilot_conditional_items i USING (work_id)
        ORDER BY v.user_idx, i.work_idx
        """
    ).fetchnumpy()
    rows = np.asarray(d["user_idx"], dtype=np.int32)
    cols = np.asarray(d["work_idx"], dtype=np.int32)
    outcomes = np.asarray(d["positive"], dtype=np.int8)
    n_works = int(cols.max()) + 1
    shape = (n_users, n_works)
    pos_mask = outcomes == 1
    neg_mask = ~pos_mask
    positive = sparse.coo_matrix(
        (np.ones(int(pos_mask.sum()), dtype=np.float32), (rows[pos_mask], cols[pos_mask])),
        shape=shape,
    ).tocsr()
    negative = sparse.coo_matrix(
        (np.ones(int(neg_mask.sum()), dtype=np.float32), (rows[neg_mask], cols[neg_mask])),
        shape=shape,
    ).tocsr()

    meta_rows = con.execute(
        """
        SELECT
            i.work_idx, i.work_id, s.title, s.author, wr.n,
            NOT coalesce(cf.is_excluded, FALSE)
              AND NOT coalesce(cf.is_nonfiction, FALSE)
              AND NOT coalesce(cf.is_comic, FALSE)
              AND NOT coalesce(cf.is_picture_book, FALSE)
              AND NOT coalesce(cf.is_derivative, FALSE)
              AND NOT coalesce(cf.is_duplicate, FALSE)
              AND NOT coalesce(cf.is_collection, FALSE) AS eligible
        FROM pilot_conditional_items i
        JOIN ex.work_scores s USING (work_id)
        JOIN work_rarity wr USING (work_id)
        LEFT JOIN ex.work_flags cf USING (work_id)
        ORDER BY i.work_idx
        """
    ).fetchall()
    works: list[dict[str, Any]] = []
    eligible = np.zeros(n_works, dtype=bool)
    for idx, wid, title, author, catalog_n, ok in meta_rows:
        works.append(
            {
                "work_idx": int(idx),
                "work_id": str(wid),
                "title": title,
                "author": author,
                "catalog_n": int(catalog_n),
            }
        )
        eligible[int(idx)] = bool(ok)

    user_stats = con.execute(
        """
        SELECT count(*), sum(2 * n_side),
               min(n_side), median(n_side), max(n_side)
        FROM (
            SELECT user_id, count(*) // 2 AS n_side
            FROM pilot_conditional_votes GROUP BY user_id
        )
        """
    ).fetchone()
    meta = {
        "n_vote_users": int(user_stats[0]),
        "n_votes": int(user_stats[1]),
        "n_works": n_works,
        "side_votes_min_median_max": [
            int(user_stats[2]),
            float(user_stats[3]),
            int(user_stats[4]),
        ],
        "positive_votes": int(positive.nnz),
        "negative_votes": int(negative.nnz),
        "seconds": time.time() - t0,
    }
    print(
        f"  users={meta['n_vote_users']:,} votes={meta['n_votes']:,} "
        f"works={n_works:,} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return positive, negative, works, eligible, meta


def aggregate_partition_counts(partitions, current_mask, positive, negative):
    print("Aggregating votes by alternative reader communities…", flush=True)
    out = []
    current_rows = np.flatnonzero(current_mask)
    for part in partitions:
        k = int(part["k"])
        labels = part["labels"]
        indicator = sparse.csr_matrix(
            (
                np.ones(len(current_rows), dtype=np.float32),
                (current_rows, labels[current_mask].astype(np.int32)),
            ),
            shape=(len(labels), k),
        )
        wins = np.asarray((indicator.T @ positive).toarray().T, dtype=np.float64)
        losses = np.asarray((indicator.T @ negative).toarray().T, dtype=np.float64)
        out.append(
            {
                "label": part["label"],
                "k": k,
                "wins": wins,
                "losses": losses,
                "current_sizes": part["current_sizes"],
            }
        )
    return out


def partition_metrics(counts, spec, base_eligible, *, selection_gamma: float = 1.0):
    """Equal-community conditional esteem and noise-corrected heterogeneity."""
    wins = counts["wins"]
    losses = counts["losses"]
    n = wins + losses
    k = counts["k"]
    observed = n >= spec["min_community_readers"]
    m = observed.sum(axis=1)

    # Preserve the observed conditional rate while capping how much it can
    # overwhelm the neutral prior or narrow the posterior.
    scale = np.minimum(1.0, spec["evidence_cap"] / np.maximum(n, 1.0))
    w_eff = wins * scale
    l_eff = losses * scale
    half_prior = spec["prior_strength"] / 2.0
    alpha = w_eff + half_prior
    beta = l_eff + half_prior
    p = alpha / (alpha + beta)
    post_var = (alpha * beta) / (
        (alpha + beta) ** 2 * (alpha + beta + 1.0)
    )
    if selection_gamma > 1.0:
        # One-sided Rosenbaum-style sensitivity bound: people predisposed to a
        # positive outcome may be Γ times as likely to become observed raters.
        # On the odds scale the conservative counterfactual is odds/Γ.
        bounded_p = p / (
            selection_gamma - (selection_gamma - 1.0) * p
        )
        derivative = (bounded_p * (1.0 - bounded_p)) / np.maximum(
            p * (1.0 - p), 1e-9
        )
        post_var = post_var * derivative * derivative
        p = bounded_p

    denom = np.maximum(m, 1)
    mu = (p * observed).sum(axis=1) / denom
    second = (p * p * observed).sum(axis=1) / denom
    sample_var = np.maximum(second - mu * mu, 0.0)
    sample_var *= np.where(m > 1, m / np.maximum(m - 1, 1), 0.0)
    mean_post_var = (post_var * observed).sum(axis=1) / denom
    tau2 = np.maximum(sample_var - mean_post_var, 0.0)
    tau = np.sqrt(tau2)
    # A predictive lower-tail score: high esteem is rewarded, real
    # between-community disagreement is penalized. Sampling uncertainty is not
    # folded into the point score; it is returned separately as ±u.
    score = mu - LOWER_TAIL_Z * tau
    se_mu = np.sqrt((tau2 + mean_post_var) / denom)
    coverage = m / k
    total_n = n.sum(axis=1)
    min_cells = max(3, int(math.ceil(k * 0.25)))
    valid = (
        base_eligible
        & (total_n >= spec["min_global_readers"])
        & (m >= min_cells)
    )
    score[~valid] = np.nan
    mu[~valid] = np.nan
    tau[~valid] = np.nan
    se_mu[~valid] = np.nan
    return {
        "score": score,
        "esteem": mu,
        "heterogeneity": tau,
        "sampling_se": se_mu,
        "coverage": coverage,
        "observed_communities": m.astype(np.int16),
        "total_votes": total_n.astype(np.int32),
        "valid": valid,
    }


def nanmean_no_warning(a: np.ndarray, axis=0):
    valid = np.isfinite(a)
    den = valid.sum(axis=axis)
    num = np.where(valid, a, 0.0).sum(axis=axis)
    return np.divide(num, den, out=np.full_like(num, np.nan, dtype=float), where=den > 0)


def aggregate_spec(
    partition_counts,
    spec,
    base_eligible,
    *,
    selection_gamma: float = 1.0,
):
    pm = [
        partition_metrics(
            c, spec, base_eligible, selection_gamma=selection_gamma
        )
        for c in partition_counts
    ]
    score_mat = np.vstack([x["score"] for x in pm])
    esteem_mat = np.vstack([x["esteem"] for x in pm])
    hetero_mat = np.vstack([x["heterogeneity"] for x in pm])
    se_mat = np.vstack([x["sampling_se"] for x in pm])
    coverage_mat = np.vstack([x["coverage"] for x in pm])
    observed_mat = np.vstack([x["observed_communities"] for x in pm])
    valid = np.isfinite(score_mat)
    valid_rate = valid.mean(axis=0)
    score = nanmean_no_warning(score_mat, axis=0)
    esteem = nanmean_no_warning(esteem_mat, axis=0)
    heterogeneity = nanmean_no_warning(hetero_mat, axis=0)
    sampling_se = nanmean_no_warning(se_mat, axis=0)
    coverage = np.mean(coverage_mat, axis=0)
    observed = np.mean(observed_mat, axis=0)
    centered = np.where(valid, score_mat - score[None, :], 0.0)
    partition_den = np.maximum(valid.sum(axis=0) - 1, 1)
    partition_sd = np.sqrt((centered * centered).sum(axis=0) / partition_den)
    uncertainty = np.sqrt(sampling_se * sampling_se + partition_sd * partition_sd)
    estimable = base_eligible & (valid_rate >= MIN_VALID_PARTITION_RATE)
    # Cross-community coverage is a saturating eligibility condition, not a
    # score bonus. A book at 100% coverage receives no more points than one at
    # 50%; a book below 50% retains its estimate but is labelled underexposed.
    eligible = estimable & (coverage >= MIN_DISTRIBUTED_COVERAGE)
    score[~estimable] = np.nan
    esteem[~estimable] = np.nan
    heterogeneity[~estimable] = np.nan
    uncertainty[~estimable] = np.nan
    candidates = np.flatnonzero(eligible)
    order = candidates[np.argsort(-score[candidates], kind="stable")]
    return {
        "label": spec["label"],
        "spec": spec,
        "selection_gamma": float(selection_gamma),
        "score": score,
        "esteem": esteem,
        "heterogeneity": heterogeneity,
        "uncertainty": uncertainty,
        "sampling_se": sampling_se,
        "partition_sd": partition_sd,
        "coverage": coverage,
        "observed_communities": observed,
        "total_votes": pm[0]["total_votes"],
        "valid_partition_rate": valid_rate,
        "estimable": estimable,
        "eligible": eligible,
        # Retain the full eligible ordering. Consumers may report top-k rates,
        # but eligibility/presence diagnostics must not mistake rank >500 for
        # missing evidence.
        "ranking": [int(x) for x in order],
        "n_rankable": int(eligible.sum()),
    }


def rank_map(ranking):
    return {w: r + 1 for r, w in enumerate(ranking)}


def popularity_audit(metric, works):
    eligible = np.flatnonzero(metric["eligible"])
    top = np.asarray(metric["ranking"][:200], dtype=int)

    def corr(indices, values):
        x = np.log1p([works[i]["catalog_n"] for i in indices])
        y = np.asarray(values, dtype=float)
        rho, p = spearmanr(x, y)
        return {"n": len(indices), "spearman_rho": float(rho), "p_value": float(p)}

    return {
        "score_vs_catalog_all_rankable": corr(eligible, metric["score"][eligible]),
        "score_vs_catalog_top200": corr(top, metric["score"][top]),
        "uncertainty_vs_catalog_all_rankable": corr(
            eligible, metric["uncertainty"][eligible]
        ),
        "coverage_vs_catalog_all_rankable": corr(
            eligible, metric["coverage"][eligible]
        ),
    }


def previous_pilot_popularity_audit():
    """Reproduce the exposure confound that motivated this revision, if present."""
    if not PREVIOUS_PILOT_JSON.exists():
        return None
    previous = json.loads(PREVIOUS_PILOT_JSON.read_text(encoding="utf-8"))
    rows = [
        x
        for x in previous.get("book_diagnostics", [])
        if x.get("baseline_rank") is not None and x["baseline_rank"] <= 200
    ]
    if len(rows) < 10:
        return None
    rho, p = spearmanr(
        np.log1p([x["catalog_n"] for x in rows]),
        [x["community_top200_rate"] for x in rows],
    )
    return {"n": len(rows), "spearman_rho": float(rho), "p_value": float(p)}


def book_diagnostics(metrics, works):
    central = metrics[0]
    maps = [rank_map(m["ranking"]) for m in metrics]
    union: set[int] = set()
    for m in maps:
        union.update(m)
    missing = TOP_SAVE + 1
    rows = []
    for idx in union:
        ranks = np.asarray([m.get(idx, missing) for m in maps], dtype=float)
        central_rank = maps[0].get(idx)
        estimate_metric = central
        estimate_label = central["label"]
        if not np.isfinite(central["score"][idx]):
            alternatives = [m for m in metrics if np.isfinite(m["score"][idx])]
            if alternatives:
                estimate_metric = alternatives[0]
                estimate_label = estimate_metric["label"]
        row = {
            **works[idx],
            "central_rank": central_rank,
            "score": None
            if not np.isfinite(estimate_metric["score"][idx])
            else float(100.0 * estimate_metric["score"][idx]),
            "uncertainty": None
            if not np.isfinite(estimate_metric["uncertainty"][idx])
            else float(100.0 * estimate_metric["uncertainty"][idx]),
            "conditional_esteem": None
            if not np.isfinite(estimate_metric["esteem"][idx])
            else float(estimate_metric["esteem"][idx]),
            "heterogeneity": None
            if not np.isfinite(estimate_metric["heterogeneity"][idx])
            else float(estimate_metric["heterogeneity"][idx]),
            "estimate_spec": estimate_label,
            "exposure_coverage": float(central["coverage"][idx]),
            "mean_observed_communities": float(central["observed_communities"][idx]),
            "jury_votes": int(central["total_votes"][idx]),
            "valid_partition_rate": float(central["valid_partition_rate"][idx]),
            "spec_top50_rate": float(np.mean(ranks <= 50)),
            "spec_top200_rate": float(np.mean(ranks <= 200)),
            "spec_top500_rate": float(np.mean(ranks <= TOP_SAVE)),
            "median_spec_rank": float(np.median(ranks)),
            "worst_spec_rank": int(np.max(ranks)),
            "ranks_by_spec": {
                metric["label"]: int(rank)
                for metric, rank in zip(metrics, ranks)
            },
        }
        rows.append(row)
    rows.sort(
        key=lambda x: (
            x["central_rank"] is None,
            x["central_rank"] or missing,
            x["median_spec_rank"],
        )
    )
    return rows


def classify_books(rows):
    central_top = [x for x in rows if x["central_rank"] and x["central_rank"] <= 200]
    robust = sorted(
        [
            x
            for x in central_top
            if x["spec_top200_rate"] >= 0.8
            and x["score"] is not None
            and x["score"] >= 50.0
            and x["heterogeneity"] is not None
            and x["heterogeneity"] <= 0.08
            and x["uncertainty"] is not None
            and x["uncertainty"] <= 6.0
        ],
        key=lambda x: x["central_rank"],
    )
    contested = sorted(
        [
            x
            for x in central_top
            if x["heterogeneity"] is not None and x["heterogeneity"] > 0.08
        ],
        key=lambda x: (-x["heterogeneity"], x["central_rank"]),
    )
    evidence_sensitive = sorted(
        [
            x
            for x in central_top
            if x["spec_top200_rate"] < 0.8
            or (x["uncertainty"] is not None and x["uncertainty"] > 6.0)
        ],
        key=lambda x: (x["spec_top200_rate"], -float(x["uncertainty"] or 0)),
    )
    underexposed = sorted(
        [
            x
            for x in rows
            if x["central_rank"] is None
            and x["spec_top200_rate"] > 0
            and (
                x["jury_votes"] < CENTRAL_SPEC["min_global_readers"]
                or x["exposure_coverage"] < MIN_DISTRIBUTED_COVERAGE
            )
        ],
        key=lambda x: (-x["spec_top200_rate"], x["median_spec_rank"]),
    )
    return robust, contested, evidence_sensitive, underexposed


def slim_metric(metric):
    return {
        "label": metric["label"],
        "spec": metric["spec"],
        "n_rankable": metric["n_rankable"],
        "top_work_indices": metric["ranking"],
    }


def fmt_book(row):
    return f"{row['title']} — {row['author']}"


def write_book_table(lines, rows, limit=40):
    lines += [
        "| book | rank | score ± u | esteem | heterog. | coverage | jury votes | spec top200 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for x in rows[:limit]:
        rank = x["central_rank"] or "—"
        su = "—" if x["score"] is None else f"{x['score']:.1f} ± {x['uncertainty']:.1f}"
        esteem = "—" if x["conditional_esteem"] is None else f"{x['conditional_esteem']:.3f}"
        hetero = "—" if x["heterogeneity"] is None else f"{x['heterogeneity']:.3f}"
        lines.append(
            f"| {fmt_book(x)} | {rank} | {su} | {esteem} | {hetero} | "
            f"{100*x['exposure_coverage']:.0f}% | {x['jury_votes']} | "
            f"{100*x['spec_top200_rate']:.0f}% |"
        )


def write_report(results):
    audit = results["popularity_audit"]
    stability = results["specification_stability"]
    lines = [
        "# Exposure-adjusted distributed literary consensus pilot",
        "",
        "## What changed",
        "",
        "The earlier pilot mixed taste with exposure: rare books often vanished from a "
        "community ranking because they lacked enough readers. This revision estimates "
        "esteem conditional on observed readership and keeps exposure breadth separate.",
        "",
        "- Every juror contributes balanced sampled 5★ and ≤3★ observations.",
        "- Reader communities are equal-weighted; unobserved communities are unknown, not negative.",
        f"- Evidence is capped at {CENTRAL_SPEC['evidence_cap']} readers per book/community "
        "in the central specification.",
        f"- Distributed-rank eligibility requires at least "
        f"{100*MIN_DISTRIBUTED_COVERAGE:.0f}% observed community coverage. This is a "
        "pass/fail evidence condition, never a score bonus.",
        "- The score is the estimated 10th percentile of preference in a new observed "
        "community: mean conditional esteem minus 1.282 × noise-corrected heterogeneity.",
        "- Sampling and partition sensitivity are reported separately as the provisional ±u.",
        "",
        "## Data and specification multiverse",
        "",
        f"- Jury: **{results['meta']['jury_n']:,}**; broad clustering pool: "
        f"**{results['meta']['broad_n']:,}**.",
        f"- Balanced vote users: **{results['votes']['n_vote_users']:,}**; user-book votes: "
        f"**{results['votes']['n_votes']:,}**.",
        f"- Community partitions: **{results['meta']['n_partitions']}**; exposure/estimation "
        f"specifications: **{results['meta']['n_specifications']}**.",
        "",
        "## Residual popularity audit",
        "",
        "Popularity is not expected to have literally zero association with canonical esteem. "
        "The important design constraint is that readership is absent from the point-score "
        "formula and stops reducing uncertainty after the evidence cap.",
        "A large negative correlation is also a warning: it can reflect genuine jury taste, "
        "but also self-selection whereby obscure books are rated mainly by enthusiasts. "
        "This dataset cannot identify those explanations without an exposure model or "
        "additional interaction data.",
        "",
        "| relationship | n | Spearman ρ |",
        "|---|---:|---:|",
    ]
    for label, key in [
        ("score vs catalog readership, all rankable", "score_vs_catalog_all_rankable"),
        ("score vs catalog readership, central top 200", "score_vs_catalog_top200"),
        ("uncertainty vs catalog readership", "uncertainty_vs_catalog_all_rankable"),
        ("exposure coverage vs catalog readership", "coverage_vs_catalog_all_rankable"),
    ]:
        x = audit[key]
        lines.append(f"| {label} | {x['n']} | {x['spearman_rho']:.3f} |")
    if results["previous_pilot_popularity_audit"] is not None:
        x = results["previous_pilot_popularity_audit"]
        lines.append(
            f"| previous pilot: community-top200 vs catalog readership | "
            f"{x['n']} | {x['spearman_rho']:.3f} |"
        )

    lines += [
        "",
        "## Specification stability",
        "",
        "Each row changes one evidence rule from the central specification.",
        "",
        "| specification | rankable | J@50 | J@200 | RBO |",
        "|---|---:|---:|---:|---:|",
    ]
    for x in stability:
        lines.append(
            f"| {x['label']} | {x['n_rankable']} | {x['jaccard50']:.3f} | "
            f"{x['jaccard200']:.3f} | {x['rbo98']:.3f} |"
        )

    lines += [
        "",
        "## Provisional robust distributed tier",
        "",
        "Central top-200 books with a lower-tail score ≥50 that remain top-200 in at "
        "least 80% of evidence specifications, with noise-corrected heterogeneity ≤0.08 "
        "and provisional uncertainty ≤6 score points. These are audit thresholds, not a "
        "claim of ground truth.",
        "",
    ]
    write_book_table(lines, results["robust_distributed"])

    lines += [
        "",
        "## Contested despite high average esteem",
        "",
        "Central top-200 books with estimated between-community heterogeneity above 0.08.",
        "",
    ]
    write_book_table(lines, results["contested"], limit=30)

    lines += [
        "",
        "## Evidence/specification-sensitive central books",
        "",
    ]
    write_book_table(lines, results["evidence_sensitive"], limit=30)

    lines += [
        "",
        "## Underexposed candidates",
        "",
        "Books entering a top 200 under at least one lenient evidence specification but "
        "missing the central global-reader floor. They are unresolved rather than rejected.",
        "",
    ]
    write_book_table(lines, results["underexposed_candidates"], limit=30)

    lines += [
        "",
        "## Russian-author diagnostic example",
        "",
        "This is retained only to compare with the motivating example; author nationality "
        "does not enter any score.",
        "",
    ]
    write_book_table(lines, results["russian_diagnostics"], limit=35)

    lines += [
        "",
        "## Limits and interpretation",
        "",
        "- Conditional-on-rating esteem is not the same as the preference of everyone who "
        "might have been exposed. Goodreads ratings are missing-not-at-random.",
        "- A rare book can receive a high point estimate and wide uncertainty. It cannot be "
        "called distributed until several communities provide evidence, but it is not treated "
        "as disliked merely because other communities have no observations.",
        "- ±u is a provisional combination of within-community posterior uncertainty and "
        "partition sensitivity. The communities reuse readers, so it is not yet a calibrated "
        "frequentist confidence interval.",
        "- The score intentionally penalizes genuine taste heterogeneity. Exposure coverage "
        "is displayed beside it rather than hidden inside it.",
        "- The next multiverse should vary jury construction and pair definitions; this pilot "
        "only varies exposure/evidence estimation around the fixed rebuilt jury.",
        "",
        "## Recommendation",
        "",
        results["recommendation"],
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    t_all = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    # Deterministic cohort boundary; see the preceding pilot.
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, all_scores, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, current_mask, _ = materialize_pilot_users(
        con, all_ids, all_scores, broad
    )
    embedding, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(embedding, current_mask)
    positive, negative, works, base_eligible, vote_meta = (
        build_conditional_vote_matrices(con, len(broad_ids))
    )
    partition_counts = aggregate_partition_counts(
        partitions, current_mask, positive, negative
    )

    print("Running exposure/evidence specification multiverse…", flush=True)
    metrics = [
        aggregate_spec(partition_counts, spec, base_eligible)
        for spec in SPECIFICATIONS
    ]
    central_rank = metrics[0]["ranking"]
    stability = []
    for metric in metrics:
        rank = metric["ranking"]
        stability.append(
            {
                "label": metric["label"],
                "n_rankable": metric["n_rankable"],
                "jaccard50": jaccard(central_rank, rank, 50),
                "jaccard200": jaccard(central_rank, rank, 200),
                "rbo98": rbo(central_rank, rank, p=0.98),
            }
        )
    diagnostics = book_diagnostics(metrics, works)
    robust, contested, sensitive, underexposed = classify_books(diagnostics)
    russian = sorted(
        [
            x
            for x in diagnostics
            if any(m in (x["author"] or "").lower() for m in RUSSIAN_AUTHOR_MARKERS)
        ],
        key=lambda x: (x["central_rank"] is None, x["central_rank"] or TOP_SAVE + 1),
    )
    audit = popularity_audit(metrics[0], works)
    previous_audit = previous_pilot_popularity_audit()

    if len(robust) >= 30:
        recommendation = (
            "The exposure-adjusted pilot supports a nontrivial provisional distributed tier. "
            "Proceed to jury/pair-definition trajectories, retaining conditional esteem, "
            "heterogeneity, exposure breadth, and uncertainty as separate outputs."
        )
    else:
        recommendation = (
            "The exposure-adjusted pilot does not yet support a large distributed tier. "
            "Keep high-esteem rare books as underexposed candidates and expand the jury/pair "
            "multiverse before choosing a final presentation threshold."
        )

    results = {
        "meta": {
            "purpose": "less-popularity-dependent distributed literary consensus",
            "jury_n": JURY_N,
            "broad_n": BROAD_N,
            "n_partitions": len(partitions),
            "n_specifications": len(SPECIFICATIONS),
            "lower_tail_z": LOWER_TAIL_Z,
            "min_valid_partition_rate": MIN_VALID_PARTITION_RATE,
            "min_distributed_coverage": MIN_DISTRIBUTED_COVERAGE,
            "runtime_seconds": time.time() - t_all,
        },
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "votes": vote_meta,
        "specifications": [slim_metric(x) for x in metrics],
        "specification_stability": stability,
        "popularity_audit": audit,
        "previous_pilot_popularity_audit": previous_audit,
        "central_top": [x for x in diagnostics if x["central_rank"] is not None][:200],
        "robust_distributed": robust,
        "contested": contested,
        "evidence_sensitive": sensitive,
        "underexposed_candidates": underexposed,
        "russian_diagnostics": russian[:100],
        "book_diagnostics": diagnostics[:2500],
        "recommendation": recommendation,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_report(results)
    print(
        f"Wrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)",
        flush=True,
    )
    con.close()


if __name__ == "__main__":
    main()

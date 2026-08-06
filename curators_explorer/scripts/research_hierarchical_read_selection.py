#!/usr/bin/env python3
"""Hierarchical community pooling plus known-read/unrated sensitivity pilot."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy.stats import spearmanr

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OBSERVATIONS = DATA_DIR / "observation_ladder_full.parquet"
ASSIGNMENTS = DATA_DIR / "jury_community_assignments.parquet"
CANDIDATES = DATA_DIR / "overnight_uncertainty_full.json"
BASELINE = DATA_DIR / "soft_jury_bootstrap_full.json"
OUT_JSON = DATA_DIR / "hierarchical_read_selection.json"
OUT_REPORT = DATA_DIR / "HIERARCHICAL_READ_SELECTION_REPORT.md"

MAX_CATALOG_N = 80_000
EVIDENCE_CAP = 30.0
LOWER_Z = 1.2815515655446004
PARTITIONS = (
    ("k6_s11", 6), ("k6_s29", 6), ("k6_s47", 6),
    ("k10_s11", 10), ("k10_s29", 10), ("k10_s47", 10),
    ("k16_s11", 16), ("k16_s29", 16), ("k16_s47", 16),
)
SPECS = (
    # label, cell prior, shared book prior, book evidence cap, min mass,
    # evidence z, Γ, all-low
    ("central", 8.0, 50.0, math.inf, 10.0, 1.0, 1.0, False),
    ("book_prior_20", 8.0, 20.0, math.inf, 10.0, 1.0, 1.0, False),
    ("book_prior_100", 8.0, 100.0, math.inf, 10.0, 1.0, 1.0, False),
    ("book_cap_30", 8.0, 50.0, 30.0, 10.0, 1.0, 1.0, False),
    ("book_cap_60", 8.0, 50.0, 60.0, 10.0, 1.0, 1.0, False),
    ("book_cap_120", 8.0, 50.0, 120.0, 10.0, 1.0, 1.0, False),
    ("evidence_z_0_5", 8.0, 50.0, math.inf, 10.0, 0.5, 1.0, False),
    ("evidence_z_1_282", 8.0, 50.0, math.inf, 10.0, LOWER_Z, 1.0, False),
    ("mass_20", 8.0, 50.0, math.inf, 20.0, 1.0, 1.0, False),
    ("unrated_gamma_1_5", 8.0, 50.0, math.inf, 10.0, 1.0, 1.5, False),
    ("unrated_gamma_2", 8.0, 50.0, math.inf, 10.0, 1.0, 2.0, False),
    ("unrated_all_low", 8.0, 50.0, math.inf, 10.0, 1.0, math.inf, True),
)


def logit(p):
    p = np.clip(p, 1e-5, 1 - 1e-5)
    return np.log(p / (1 - p))


def expit(x):
    x = np.clip(x, -20, 20)
    return 1 / (1 + np.exp(-x))


def aggregate_partition(con, column, k, n_works):
    rows = con.execute(
        f"""
        SELECT work_idx, {column} AS community,
               sum(jury_q * CASE WHEN rating=5 AND n_high>0
                   THEN n_side/n_high ELSE 0 END) AS wins,
               sum(jury_q * CASE WHEN rating BETWEEN 1 AND 3 AND n_low>0
                   THEN n_side/n_low ELSE 0 END) AS losses,
               sum(jury_q * CASE WHEN is_read AND rating=0 AND n_high+1>0
                   THEN least(n_high+1,n_low,12)/(n_high+1) ELSE 0 END) AS miss_pos,
               sum(jury_q * CASE WHEN is_read AND rating=0 AND n_low+1>0
                   THEN least(n_high,n_low+1,12)/(n_low+1) ELSE 0 END) AS miss_neg,
               sum(jury_q) FILTER (WHERE rating>0) AS rated_mass,
               sum(jury_q) FILTER (WHERE is_read OR rating>0) AS read_mass,
               sum(jury_q) FILTER (WHERE is_read AND rating=0) AS read_unrated_mass,
               sum(jury_q) FILTER (WHERE NOT is_read AND rating=0) AS shelf_mass,
               count(*) FILTER (WHERE rating=5 OR rating BETWEEN 1 AND 3) AS pair_readers,
               count(*) FILTER (WHERE is_read AND rating=0) AS read_unrated_users
        FROM candidate_state
        GROUP BY work_idx, community
        """
    ).fetchall()
    keys = (
        "wins", "losses", "miss_pos", "miss_neg", "rated_mass", "read_mass",
        "read_unrated_mass", "shelf_mass", "pair_readers", "read_unrated_users",
    )
    arrays = {key: np.zeros((n_works, k), dtype=np.float64) for key in keys}
    for row in rows:
        i, c = int(row[0]), int(row[1])
        for offset, key in enumerate(keys, start=2):
            arrays[key][i, c] = 0.0 if row[offset] is None else float(row[offset])
    return {"label": column, "k": k, **arrays}


def adjusted_counts(part, gamma, all_low):
    wins = part["wins"].copy()
    losses = part["losses"].copy()
    if gamma <= 1 and not all_low:
        return wins, losses
    if all_low:
        losses += part["miss_neg"]
        return wins, losses
    observed = (wins + 0.5) / (wins + losses + 1.0)
    missing_positive = observed / (gamma - (gamma - 1.0) * observed)
    wins += part["miss_pos"] * missing_positive
    losses += part["miss_neg"] * (1.0 - missing_positive)
    return wins, losses


def partition_metric(
    part, prior_strength, book_prior_strength, book_evidence_cap,
    evidence_z, gamma, all_low,
):
    wins, losses = adjusted_counts(part, gamma, all_low)
    n = wins + losses
    global_p = (wins.sum() + 2.0) / (n.sum() + 4.0)
    book_n = n.sum(axis=1)
    book_scale = np.minimum(
        1.0, book_evidence_cap / np.maximum(book_n, 1.0)
    )
    book_n_eff = book_n * book_scale
    book_wins_eff = wins.sum(axis=1) * book_scale
    book_p = (book_wins_eff + book_prior_strength * global_p) / (
        book_n_eff + book_prior_strength
    )
    # This uncertainty is shared by every predicted community for the book.
    # It must be carried once, not divided by the number of communities.
    book_var = (book_p * (1.0 - book_p)) / (
        book_n_eff + book_prior_strength + 1.0
    )
    community_p = (wins.sum(axis=0) + 2.0) / (n.sum(axis=0) + 4.0)
    prior_mean = expit(
        logit(book_p)[:, None] + logit(community_p)[None, :] - logit(global_p)
    )
    scale = np.minimum(1.0, EVIDENCE_CAP / np.maximum(n, 1.0))
    w_eff, l_eff = wins * scale, losses * scale
    alpha = w_eff + prior_strength * prior_mean
    beta = l_eff + prior_strength * (1.0 - prior_mean)
    post_mean = alpha / (alpha + beta)
    post_var = (alpha * beta) / (
        (alpha + beta) ** 2 * (alpha + beta + 1.0)
    )
    mu = post_mean.mean(axis=1)
    observed = n >= 3.0
    observed_n = observed.sum(axis=1)
    observed_sum = (post_mean * observed).sum(axis=1)
    observed_mu = np.divide(
        observed_sum, observed_n, out=mu.copy(), where=observed_n > 0
    )
    observed_ss = (((post_mean - observed_mu[:, None]) ** 2) * observed).sum(axis=1)
    raw_var = np.divide(
        observed_ss, observed_n - 1,
        out=np.zeros_like(mu), where=observed_n > 1,
    )
    # Sampling variance of the shrunken posterior *mean*. This is smaller than
    # posterior uncertainty about the latent cell rate and is the correct term to
    # remove when estimating genuine between-community dispersion.
    n_eff = w_eff + l_eff
    cell_estimator_var = (
        n_eff * post_mean * (1.0 - post_mean) / (prior_strength + n_eff) ** 2
    )
    observed_estimator_var = np.divide(
        (cell_estimator_var * observed).sum(axis=1), observed_n,
        out=np.zeros_like(mu), where=observed_n > 0,
    )
    mean_post_var = post_var.mean(axis=1)
    observed_tau2 = np.maximum(raw_var - observed_estimator_var, 0.0)
    coverage = observed_n / part["k"]

    # Estimate out-of-sample community dispersion from books with enough breadth.
    # A book with no observations in a community has not demonstrated agreement there,
    # even when its aggregate book rate is precise.
    reference_books = (coverage >= 0.75) & (book_n >= 50.0)
    if reference_books.sum() >= 10:
        heterogeneity_floor2 = float(np.median(observed_tau2[reference_books]))
    else:
        heterogeneity_floor2 = 0.0025
    # Observed communities use the book-specific estimate; missing communities receive
    # the empirical predictive dispersion instead of artificial agreement.
    tau2 = coverage * observed_tau2 + (1.0 - coverage) * heterogeneity_floor2
    tau = np.sqrt(tau2)
    score = mu - LOWER_Z * tau - evidence_z * np.sqrt(book_var)
    sampling_se = np.sqrt((tau2 + mean_post_var) / part["k"] + book_var)
    return {
        "score": score,
        "esteem": mu,
        "heterogeneity": tau,
        "sampling_se": sampling_se,
        "coverage": coverage,
        "pair_mass": (part["wins"] + part["losses"]).sum(axis=1),
        "heterogeneity_floor": math.sqrt(heterogeneity_floor2),
    }


def combine(
    partitions, prior_strength, book_prior_strength, book_evidence_cap,
    min_mass, evidence_z, gamma, all_low,
):
    metrics = [
        partition_metric(
            part, prior_strength, book_prior_strength, book_evidence_cap,
            evidence_z, gamma, all_low,
        )
        for part in partitions
    ]
    score_matrix = np.vstack([m["score"] for m in metrics])
    esteem_matrix = np.vstack([m["esteem"] for m in metrics])
    score = score_matrix.mean(axis=0)
    esteem = esteem_matrix.mean(axis=0)
    heterogeneity = np.vstack([m["heterogeneity"] for m in metrics]).mean(axis=0)
    sampling_se = np.vstack([m["sampling_se"] for m in metrics]).mean(axis=0)
    coverage = np.vstack([m["coverage"] for m in metrics]).mean(axis=0)
    partition_sd = score_matrix.std(axis=0, ddof=1)
    esteem_partition_sd = esteem_matrix.std(axis=0, ddof=1)
    uncertainty = np.sqrt(sampling_se**2 + partition_sd**2)
    esteem_uncertainty = np.sqrt(sampling_se**2 + esteem_partition_sd**2)
    pair_mass = metrics[0]["pair_mass"]
    heterogeneity_floor = float(
        np.mean([metric["heterogeneity_floor"] for metric in metrics])
    )
    estimable = pair_mass >= min_mass
    ranking = np.flatnonzero(estimable)
    ranking = ranking[np.argsort(-score[ranking], kind="stable")]
    return {
        "score": score, "esteem": esteem, "heterogeneity": heterogeneity,
        "sampling_se": sampling_se, "partition_sd": partition_sd,
        "uncertainty": uncertainty, "esteem_uncertainty": esteem_uncertainty,
        "esteem_partition_sd": esteem_partition_sd, "coverage": coverage,
        "pair_mass": pair_mass, "heterogeneity_floor": heterogeneity_floor,
        "estimable": estimable, "ranking": ranking,
    }


def comparison(metric, baseline, works):
    ranking = metric["ranking"].tolist()
    idx_by_id = {row["work_id"]: i for i, row in enumerate(works)}
    baseline_idx = [idx_by_id[x] for x in baseline if x in idx_by_id]
    common = np.flatnonzero(metric["estimable"])
    pop_rho = float(
        spearmanr(
            np.log1p([works[i]["catalog_n"] for i in common]),
            metric["score"][common],
        ).statistic
    )
    return {
        "n_rankable": int(metric["estimable"].sum()),
        "jaccard50_vs_current": jaccard(baseline_idx, ranking, 50),
        "jaccard200_vs_current": jaccard(baseline_idx, ranking, 200),
        "rbo_vs_current": rbo(baseline_idx, ranking),
        "score_catalog_spearman": pop_rho,
        "median_top200_u": float(np.median(metric["uncertainty"][ranking[:200]]) * 100),
        "median_top200_coverage": float(np.median(metric["coverage"][ranking[:200]])),
    }


def main():
    t0 = time.time()
    candidate_json = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    works = sorted(candidate_json["books"], key=lambda row: int(row["work_idx"]))
    # Work indices in the source are global sparse-matrix columns; replace with a compact order.
    for compact_idx, row in enumerate(works):
        row["compact_idx"] = compact_idx
    n_works = len(works)
    base_json = json.loads(BASELINE.read_text(encoding="utf-8"))
    base_variant = next(v for v in base_json["variants"] if v["label"] == "soft jury q")
    baseline = [row["work_id"] for row in base_variant["books"]]

    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("CREATE TEMP TABLE candidates(work_idx INTEGER, work_id VARCHAR)")
    con.executemany(
        "INSERT INTO candidates VALUES (?, ?)",
        [(row["compact_idx"], row["work_id"]) for row in works],
    )
    print("Materializing broad-user balance and candidate states…", flush=True)
    con.execute(
        f"""
        CREATE TEMP TABLE assignments AS
        SELECT * FROM read_parquet('{ASSIGNMENTS}') WHERE jury_q>0
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE user_balance AS
        SELECT o.user_id,
               count(*) FILTER (WHERE o.rating=5)::DOUBLE AS n_high,
               count(*) FILTER (WHERE o.rating BETWEEN 1 AND 3)::DOUBLE AS n_low,
               least(count(*) FILTER (WHERE o.rating=5),
                     count(*) FILTER (WHERE o.rating BETWEEN 1 AND 3), 12)::DOUBLE AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN assignments a USING (user_id)
        JOIN ex.work_stats s USING (work_id)
        WHERE o.rating>0 AND s.n BETWEEN 100 AND {MAX_CATALOG_N}
        GROUP BY o.user_id
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE candidate_state AS
        SELECT c.work_idx, o.user_id, o.is_read, o.rating, o.is_reviewed,
               a.*, coalesce(b.n_high,0) AS n_high,
               coalesce(b.n_low,0) AS n_low, coalesce(b.n_side,0) AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN candidates c USING (work_id)
        JOIN assignments a USING (user_id)
        LEFT JOIN user_balance b USING (user_id)
        """
    )
    state_summary = con.execute(
        """
        SELECT count(*), count(DISTINCT user_id),
               count(*) FILTER (WHERE rating>0),
               count(*) FILTER (WHERE is_read AND rating=0),
               sum(jury_q) FILTER (WHERE rating>0),
               sum(jury_q) FILTER (WHERE is_read AND rating=0)
        FROM candidate_state
        """
    ).fetchone()
    partitions = []
    for label, k in PARTITIONS:
        print(f"Aggregating {label}…", flush=True)
        partitions.append(aggregate_partition(con, label, k, n_works))
    con.close()

    metrics = {}
    summaries = []
    for (
        label, prior, book_prior, book_cap, min_mass, evidence_z, gamma, all_low
    ) in SPECS:
        metric = combine(
            partitions, prior, book_prior, book_cap, min_mass, evidence_z,
            gamma, all_low,
        )
        metrics[label] = metric
        summaries.append(
            {
                "label": label,
                "prior_strength": prior,
                "book_prior_strength": book_prior,
                "book_evidence_cap": None if math.isinf(book_cap) else book_cap,
                "min_pair_mass": min_mass,
                "evidence_z": evidence_z,
                "unrated_gamma": None if math.isinf(gamma) else gamma,
                "all_unrated_low": all_low,
                "predictive_heterogeneity_floor": metric["heterogeneity_floor"],
                **comparison(metric, baseline, works),
            }
        )
    central = metrics["central"]
    central_ranking = central["ranking"].tolist()
    for summary in summaries:
        ranking = metrics[summary["label"]]["ranking"].tolist()
        summary["jaccard50_vs_central"] = jaccard(central_ranking, ranking, 50)
        summary["jaccard200_vs_central"] = jaccard(central_ranking, ranking, 200)
        summary["rbo_vs_central"] = rbo(central_ranking, ranking)
    gamma15 = metrics["unrated_gamma_1_5"]
    gamma2 = metrics["unrated_gamma_2"]
    all_low = metrics["unrated_all_low"]
    rank_maps = {
        label: {int(i): rank + 1 for rank, i in enumerate(metric["ranking"])}
        for label, metric in metrics.items()
    }
    # Rating completion is independent of partition labels; every partition sums to the same mass.
    rated_mass = partitions[0]["rated_mass"].sum(axis=1)
    read_mass = partitions[0]["read_mass"].sum(axis=1)
    unrated_mass = partitions[0]["read_unrated_mass"].sum(axis=1)
    completion = np.divide(
        rated_mass, read_mass,
        out=np.full(n_works, np.nan), where=read_mass>0,
    )
    rows = []
    rank_map = {int(i): rank + 1 for rank, i in enumerate(central["ranking"])}
    base_rank = {work_id: rank + 1 for rank, work_id in enumerate(baseline)}
    for i, work in enumerate(works):
        rows.append(
            {
                "work_id": work["work_id"], "title": work["title"],
                "author": work["author"], "catalog_n": work["catalog_n"],
                "hierarchical_rank": rank_map.get(i),
                "current_rank": base_rank.get(work["work_id"]),
                "score": float(100*central["score"][i]),
                "esteem": float(100*central["esteem"][i]),
                "heterogeneity": float(100*central["heterogeneity"][i]),
                "u": float(100*central["uncertainty"][i]),
                "pair_mass": float(central["pair_mass"][i]),
                "observed_coverage": float(central["coverage"][i]),
                "rating_completion": None if not np.isfinite(completion[i]) else float(completion[i]),
                "read_unrated_mass": float(unrated_mass[i]),
                "gamma_1_5_score": float(100*gamma15["score"][i]),
                "gamma_2_score": float(100*gamma2["score"][i]),
                "all_unrated_low_score": float(100*all_low["score"][i]),
                "specification_trajectory": {
                    label: {
                        "rank": rank_maps[label].get(i),
                        "score": float(100 * metric["score"][i]),
                    }
                    for label, metric in metrics.items()
                },
            }
        )
    rows.sort(key=lambda row: row["hierarchical_rank"] or 10**9)
    central_summary = next(row for row in summaries if row["label"] == "central")
    top200 = central["ranking"][:200]
    selection_summary = {}
    for label, metric in (
        ("gamma_1_5", gamma15), ("gamma_2", gamma2), ("all_low", all_low)
    ):
        drops = 100 * (central["score"][top200] - metric["score"][top200])
        selection_summary[label] = {
            "median_top200_score_drop": float(np.median(drops)),
            "p90_top200_score_drop": float(np.quantile(drops, 0.9)),
            "top200_drop_gt_3": int((drops > 3.0).sum()),
            "top200_drop_gt_5": int((drops > 5.0).sum()),
        }
    result = {
        "meta": {
            "purpose": "hierarchical community pooling with known-read/unrated sensitivity",
            "runtime_seconds": time.time()-t0,
            "candidate_books": n_works,
            "partitions": len(partitions),
            "evidence_cap": EVIDENCE_CAP,
            "central_prior_strength": 8.0,
            "central_book_prior_strength": 50.0,
            "central_min_pair_mass": 10.0,
        },
        "candidate_state": {
            "rows": int(state_summary[0]), "users": int(state_summary[1]),
            "rated_rows": int(state_summary[2]),
            "read_unrated_rows": int(state_summary[3]),
            "rated_soft_mass": float(state_summary[4]),
            "read_unrated_soft_mass": float(state_summary[5]),
        },
        "specifications": summaries,
        "central": central_summary,
        "read_unrated_sensitivity": selection_summary,
        "books": rows,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hierarchical community pooling and read-selection pilot",
        "",
        "## Design",
        "",
        "Exact expected-inclusion positive/negative mass is retained. Every book×community "
        "cell receives a logistic empirical-Bayes prior combining the book-wide and "
        "community-wide rate; the book-wide component is first shrunk by 50 units toward "
        "the global rate. Observed evidence is capped at 30 and updates that prior. "
        "Missing communities therefore remain uncertain predictions rather than causing a "
        "binary coverage failure. Their heterogeneity is assigned a data-estimated predictive "
        "floor learned from well-observed books. Shared book-level uncertainty is carried once "
        "rather than divided across predicted communities. The point ranking is a conservative posterior "
        "estimate: mean community esteem minus lower-tail penalties for genuine heterogeneity "
        "and shared book uncertainty.",
        "",
        "Known-read/unrated interactions are not imputed in the central score. Separate Γ "
        "paths assign them a lower positive propensity than observed raters using capped "
        "marginal pair weights; the all-low path is an extreme bound.",
        "",
        f"- Candidate books: **{n_works:,}**; candidate states: "
        f"**{result['candidate_state']['rows']:,}** from **{result['candidate_state']['users']:,}** users.",
        f"- Rated candidate states: **{result['candidate_state']['rated_rows']:,}**; "
        f"known-read/unrated: **{result['candidate_state']['read_unrated_rows']:,}**.",
        f"- Central rankable: **{central_summary['n_rankable']:,}**; current hard-gate ranking: 300.",
        f"- Cross-community predictive heterogeneity floor: "
        f"**{100*central['heterogeneity_floor']:.1f} score points**.",
        "",
        "## Specification trajectories",
        "",
        "| specification | rankable | J@50 current | J@200 current | RBO current | J@50 central | J@200 central | RBO central | pop ρ | med top200 u | med observed coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['label']} | {row['n_rankable']} | {row['jaccard50_vs_current']:.3f} | "
            f"{row['jaccard200_vs_current']:.3f} | {row['rbo_vs_current']:.3f} | "
            f"{row['jaccard50_vs_central']:.3f} | {row['jaccard200_vs_central']:.3f} | "
            f"{row['rbo_vs_central']:.3f} | "
            f"{row['score_catalog_spearman']:.3f} | {row['median_top200_u']:.2f} | "
            f"{100*row['median_top200_coverage']:.0f}% |"
        )
    lines += [
        "",
        "## Known-read/unrated sensitivity",
        "",
        "These are score changes among the central top 200, holding the observed ratings fixed.",
        "",
        "| path | median drop | 90th-percentile drop | drop >3 | drop >5 |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in ("gamma_1_5", "gamma_2", "all_low"):
        row = selection_summary[label]
        lines.append(
            f"| {label} | {row['median_top200_score_drop']:.2f} | "
            f"{row['p90_top200_score_drop']:.2f} | {row['top200_drop_gt_3']} | "
            f"{row['top200_drop_gt_5']} |"
        )
    lines += [
        "",
        "## Central top 40",
        "",
        "| # | book | score ±u | old # | pair mass | observed coverage | rated/read | Γ1.5 | Γ2 | all-low |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows[:40]:
        old = "—" if row["current_rank"] is None else str(row["current_rank"])
        completion_text = "—" if row["rating_completion"] is None else f"{100*row['rating_completion']:.0f}%"
        lines.append(
            f"| {row['hierarchical_rank']} | {row['title']} — {row['author']} | "
            f"{row['score']:.1f} ±{row['u']:.1f} | {old} | {row['pair_mass']:.1f} | "
            f"{100*row['observed_coverage']:.0f}% | {completion_text} | "
            f"{row['gamma_1_5_score']:.1f} | {row['gamma_2_score']:.1f} | "
            f"{row['all_unrated_low_score']:.1f} |"
        )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "- This is an empirical-Bayes pilot, not a fully fitted generative multilevel model. "
        "Book-wide evidence contributes to every community prior, so uncertainty is still "
        "understated when whole communities are unobserved.",
        "- Read-unrated Γ paths approximate the marginal pair contribution the missing event "
        "would have had. They bound rating selection among recorded readers, not unrecorded exposure.",
        "- Removing a gate can admit weakly identified books. Pair mass, posterior uncertainty, "
        "and selection paths must remain visible; do not publish the central order alone.",
        "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_REPORT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

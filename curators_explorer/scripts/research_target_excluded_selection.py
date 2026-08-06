#!/usr/bin/env python3
"""Cross-fitted, target-excluded calibration of enthusiast selection Γ.

The preceding multiverse calibrated Γ by finding the observed readers nearest
each book's co-reading centroid.  That embedding included the fact that those
readers had interacted with the target book, and each reader helped define the
centroid used to score them.  This stricter audit removes both shortcuts:

* calibration books are split into item folds and entirely removed from the
  interaction matrix used to learn their reader embeddings;
* for each target, a five-fold model predicts recorded interaction for held-out
  users from target-excluded co-reading features;
* rating values are never used by the exposure model;
* the preference comparison is made only after the propensity scores are fixed.

This is still a sensitivity calibration, not identification: an absent rating
is an implicit-feedback non-interaction, not proof that the user was exposed
and declined to read or rate the book.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_target_excluded_selection
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import svds
from scipy.stats import rankdata

from curators_explorer.scripts.research_consensus_multiverse import (
    CENTRAL_PAIR,
    PAIR_VARIANTS,
    build_pair_vote_matrices,
)
from curators_explorer.scripts.research_consensus_stability_pilot import (
    JURY_N,
    MAX_ITEM_POOL_SHARE,
    MIN_ITEM_POOL_SUPPORT,
    materialize_pilot_users,
    reconstruct_jury,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MULTIVERSE_JSON = DATA_DIR / "consensus_multiverse.json"
OUT_JSON = DATA_DIR / "target_excluded_selection.json"
OUT_MD = DATA_DIR / "TARGET_EXCLUDED_SELECTION_REPORT.md"

N_ITEM_FOLDS = 5
N_USER_FOLDS = 5
EMBED_DIM = 24
RIDGE = 5.0
FRACTIONS = (0.25, 0.50, 0.75)
N_RANDOM_REPEATS = 100
SEED = 71


def load_calibration_targets() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    previous = json.loads(MULTIVERSE_JSON.read_text(encoding="utf-8"))
    rows = [
        x
        for x in previous["book_diagnostics"]
        if x["central_rank"] is not None
        and x["jury_votes"] is not None
        and x["jury_votes"] >= 100
        and x["coverage"] >= 0.80
    ]
    rows.sort(key=lambda x: x["work_id"])
    return rows, previous["selection_calibration"]


def materialize_target_table(con, targets: list[dict[str, Any]]) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE selection_targets(
            target_idx INTEGER, work_id VARCHAR, item_fold INTEGER
        )
        """
    )
    rows = [
        (idx, str(x["work_id"]), idx % N_ITEM_FOLDS)
        for idx, x in enumerate(targets)
    ]
    con.executemany("INSERT INTO selection_targets VALUES (?, ?, ?)", rows)


def build_binary_interaction_matrix(con, n_users: int):
    """Return the outcome-blind user-book matrix used for fold embeddings."""
    print("Building binary co-reading matrix…", flush=True)
    t0 = time.time()
    max_support = int(n_users * MAX_ITEM_POOL_SHARE)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE selection_embed_items AS
        WITH support AS (
            SELECT e.work_id, count(DISTINCT u.user_id)::BIGINT AS n_users
            FROM ex.all_rating_events e JOIN pilot_users u USING (user_id)
            GROUP BY e.work_id
            HAVING count(DISTINCT u.user_id)
                BETWEEN {MIN_ITEM_POOL_SUPPORT} AND {max_support}
        )
        SELECT work_id,
               (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS item_idx,
               n_users
        FROM support
        """
    )
    d = con.execute(
        """
        SELECT DISTINCT u.user_idx, i.item_idx, i.n_users
        FROM ex.all_rating_events e
        JOIN pilot_users u USING (user_id)
        JOIN selection_embed_items i USING (work_id)
        ORDER BY u.user_idx, i.item_idx
        """
    ).fetchnumpy()
    row = np.asarray(d["user_idx"], dtype=np.int32)
    col = np.asarray(d["item_idx"], dtype=np.int32)
    support = np.asarray(d["n_users"], dtype=np.float32)
    value = np.sqrt(
        np.maximum(np.log((n_users + 1.0) / (support + 1.0)), 0.05)
    ).astype(np.float32)
    n_items = int(col.max()) + 1
    matrix = sparse.coo_matrix((value, (row, col)), shape=(n_users, n_items)).tocsr()
    item_rows = con.execute(
        """
        SELECT t.target_idx, t.work_id, t.item_fold, i.item_idx
        FROM selection_targets t
        LEFT JOIN selection_embed_items i USING (work_id)
        ORDER BY t.target_idx
        """
    ).fetchall()
    target_items = {
        int(target_idx): {
            "work_id": str(work_id),
            "item_fold": int(item_fold),
            "item_idx": None if item_idx is None else int(item_idx),
        }
        for target_idx, work_id, item_fold, item_idx in item_rows
    }
    meta = {
        "n_users": n_users,
        "n_items": n_items,
        "n_events": int(matrix.nnz),
        "weighting": "binary interaction × square-root inverse-popularity weight",
        "rating_values_used": False,
        "seconds": time.time() - t0,
    }
    print(
        f"  matrix={matrix.shape} nnz={matrix.nnz:,} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return matrix, target_items, meta


def target_excluded_embedding(
    matrix: sparse.csr_matrix,
    excluded_item_indices: list[int],
    random_state: int,
) -> np.ndarray:
    """Fit a user embedding after completely removing a target item fold."""
    fold_matrix = matrix.copy()
    if excluded_item_indices:
        fold_matrix[:, np.asarray(excluded_item_indices, dtype=np.int32)] = 0
        fold_matrix.eliminate_zeros()
    row_norm = np.sqrt(
        np.asarray(fold_matrix.multiply(fold_matrix).sum(axis=1)).ravel()
    )
    fold_matrix = sparse.diags(1.0 / np.maximum(row_norm, 1e-8)) @ fold_matrix
    k = min(EMBED_DIM, min(fold_matrix.shape) - 1)
    u, s, _ = svds(fold_matrix, k=k, which="LM", random_state=random_state)
    order = np.argsort(-s)
    embedding = np.asarray(u[:, order] * s[order][None, :], dtype=np.float32)
    norm = np.linalg.norm(embedding, axis=1)
    embedding /= np.maximum(norm[:, None], 1e-8)
    return embedding


def exposure_sets(con, n_targets: int) -> list[np.ndarray]:
    """Observed target interactions among the central jury; no rating values."""
    rows = con.execute(
        f"""
        SELECT DISTINCT t.target_idx, u.user_idx
        FROM ex.all_rating_events e
        JOIN pilot_users u USING (user_id)
        JOIN selection_targets t USING (work_id)
        WHERE u.broad_rank <= {JURY_N}
        ORDER BY t.target_idx, u.user_idx
        """
    ).fetchall()
    out: list[list[int]] = [[] for _ in range(n_targets)]
    for target_idx, user_idx in rows:
        out[int(target_idx)].append(int(user_idx))
    return [np.asarray(x, dtype=np.int32) for x in out]


def fit_weighted_ridge_propensity(
    x: np.ndarray, y: np.ndarray, train: np.ndarray, test: np.ndarray
) -> np.ndarray:
    """Balanced regularized linear-probability propensity score."""
    x_train = x[train]
    y_train = y[train].astype(np.float64)
    n_pos = max(float(y_train.sum()), 1.0)
    n_neg = max(float(len(y_train) - y_train.sum()), 1.0)
    weights = np.where(
        y_train > 0,
        len(y_train) / (2.0 * n_pos),
        len(y_train) / (2.0 * n_neg),
    )
    design = np.column_stack([np.ones(len(x_train)), x_train]).astype(np.float64)
    gram = design.T @ (weights[:, None] * design)
    penalty = np.eye(gram.shape[0]) * RIDGE
    penalty[0, 0] = 1e-8
    rhs = design.T @ (weights * y_train)
    coef = np.linalg.solve(gram + penalty, rhs)
    test_design = np.column_stack([np.ones(int(test.sum())), x[test]])
    return np.asarray(test_design @ coef, dtype=np.float64)


def auc_score(y: np.ndarray, score: np.ndarray) -> float:
    pos = y == 1
    n_pos = int(pos.sum())
    n_neg = int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = rankdata(score, method="average")
    return float(
        (ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    )


def preference_voters(
    target_work_id: str,
    work_to_index: dict[str, int],
    positive: sparse.csc_matrix,
    negative: sparse.csc_matrix,
) -> tuple[np.ndarray, np.ndarray]:
    idx = work_to_index[target_work_id]
    pr = positive.indices[positive.indptr[idx] : positive.indptr[idx + 1]]
    nr = negative.indices[negative.indptr[idx] : negative.indptr[idx + 1]]
    pr = pr[pr < JURY_N]
    nr = nr[nr < JURY_N]
    users = np.concatenate([pr, nr]).astype(np.int32)
    outcome = np.concatenate(
        [np.ones(len(pr), dtype=np.float64), np.zeros(len(nr), dtype=np.float64)]
    )
    return users, outcome


def gamma_from_probabilities(p_selected: float, p_full: float) -> float:
    odds_selected = p_selected / max(1.0 - p_selected, 1e-9)
    odds_full = p_full / max(1.0 - p_full, 1e-9)
    return float(odds_selected / max(odds_full, 1e-9))


def summarize_fraction(
    fraction: float,
    records: list[dict[str, Any]],
    random_quantiles: list[dict[str, float]],
) -> dict[str, Any]:
    gamma = np.asarray([x["gamma_one_sided"] for x in records])
    selected = np.asarray([x["p_selected"] for x in records])
    full = np.asarray([x["p_full"] for x in records])
    quantiles = {
        f"q{q}": float(np.quantile(gamma, q / 100.0))
        for q in (50, 75, 90, 95)
    }
    null = {
        key: float(np.median([x[key] for x in random_quantiles]))
        for key in ("q50", "q75", "q90", "q95")
    }
    corrected = selected / (
        quantiles["q50"] - (quantiles["q50"] - 1.0) * selected
    )
    return {
        "retained_fraction": fraction,
        "n_books": len(records),
        "share_propensity_subset_higher": float(np.mean(selected > full)),
        "mean_preference_inflation": float(np.mean(selected - full)),
        "gamma_one_sided_quantiles": quantiles,
        "random_subset_gamma_quantiles_median": null,
        "uncorrected_mae_to_full": float(np.mean(np.abs(selected - full))),
        "median_gamma_corrected_mae_to_full": float(
            np.mean(np.abs(corrected - full))
        ),
    }


def calibrate(
    con,
    targets: list[dict[str, Any]],
    matrix: sparse.csr_matrix,
    target_items: dict[int, dict[str, Any]],
    exposures: list[np.ndarray],
    positive: sparse.csr_matrix,
    negative: sparse.csr_matrix,
    works: list[dict[str, Any]],
):
    print("Running target-excluded, cross-fitted propensity calibration…", flush=True)
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    permutation = rng.permutation(JURY_N)
    user_fold = np.empty(JURY_N, dtype=np.int8)
    user_fold[permutation] = np.arange(JURY_N) % N_USER_FOLDS
    work_to_index = {x["work_id"]: x["work_idx"] for x in works}
    positive = positive.tocsc()
    negative = negative.tocsc()
    records = {fraction: [] for fraction in FRACTIONS}
    random_by_fraction = {
        fraction: [dict() for _ in range(N_RANDOM_REPEATS)]
        for fraction in FRACTIONS
    }
    aucs = []
    skipped = []

    for item_fold in range(N_ITEM_FOLDS):
        fold_targets = [
            idx
            for idx, info in target_items.items()
            if info["item_fold"] == item_fold and info["item_idx"] is not None
        ]
        excluded = [target_items[idx]["item_idx"] for idx in fold_targets]
        print(
            f"  item fold {item_fold + 1}/{N_ITEM_FOLDS}: "
            f"excluding {len(excluded)} calibration books",
            flush=True,
        )
        embedding = target_excluded_embedding(matrix, excluded, SEED + item_fold)
        central_embedding = embedding[:JURY_N]
        for target_idx in fold_targets:
            target = targets[target_idx]
            work_id = str(target["work_id"])
            if work_id not in work_to_index:
                skipped.append({"work_id": work_id, "reason": "absent from pair matrix"})
                continue
            y_exposure = np.zeros(JURY_N, dtype=np.int8)
            y_exposure[exposures[target_idx]] = 1
            if y_exposure.sum() < 50:
                skipped.append({"work_id": work_id, "reason": "fewer than 50 interactions"})
                continue
            propensity = np.empty(JURY_N, dtype=np.float64)
            for fold in range(N_USER_FOLDS):
                test = user_fold == fold
                train = ~test
                propensity[test] = fit_weighted_ridge_propensity(
                    central_embedding, y_exposure, train, test
                )
            auc = auc_score(y_exposure, propensity)
            aucs.append(auc)
            voters, outcome = preference_voters(
                work_id, work_to_index, positive, negative
            )
            if len(voters) < 100:
                skipped.append({"work_id": work_id, "reason": "fewer than 100 pair voters"})
                continue
            voter_score = propensity[voters]
            order = np.argsort(-voter_score, kind="stable")
            p_full = float((outcome.sum() + 0.5) / (len(outcome) + 1.0))
            for fraction in FRACTIONS:
                keep_n = max(20, int(math.ceil(len(outcome) * fraction)))
                selected = outcome[order[:keep_n]]
                p_selected = float((selected.sum() + 0.5) / (keep_n + 1.0))
                gamma = gamma_from_probabilities(p_selected, p_full)
                records[fraction].append(
                    {
                        "work_id": work_id,
                        "title": target["title"],
                        "author": target["author"],
                        "n_full": int(len(outcome)),
                        "n_selected": int(keep_n),
                        "n_recorded_interactions": int(y_exposure.sum()),
                        "exposure_auc": auc,
                        "p_full": p_full,
                        "p_selected": p_selected,
                        "gamma": gamma,
                        "gamma_one_sided": float(max(gamma, 1.0)),
                    }
                )
                for repeat in range(N_RANDOM_REPEATS):
                    random_selected = rng.choice(
                        outcome, size=keep_n, replace=False
                    )
                    random_p = float(
                        (random_selected.sum() + 0.5) / (keep_n + 1.0)
                    )
                    random_by_fraction[fraction][repeat][work_id] = float(
                        max(gamma_from_probabilities(random_p, p_full), 1.0)
                    )

    summaries = []
    for fraction in FRACTIONS:
        null_quantiles = []
        for repeat in range(N_RANDOM_REPEATS):
            values = np.asarray(
                list(random_by_fraction[fraction][repeat].values()), dtype=float
            )
            null_quantiles.append(
                {
                    f"q{q}": float(np.quantile(values, q / 100.0))
                    for q in (50, 75, 90, 95)
                }
            )
        summaries.append(
            summarize_fraction(
                fraction, records[fraction], null_quantiles
            )
        )
    meta = {
        "n_targets_requested": len(targets),
        "n_targets_calibrated": len(records[FRACTIONS[0]]),
        "n_item_folds": N_ITEM_FOLDS,
        "n_user_folds": N_USER_FOLDS,
        "embedding_dim": EMBED_DIM,
        "propensity_model": "balanced ridge linear-probability model",
        "ridge": RIDGE,
        "outcome_used_by_propensity_model": "recorded target interaction only; rating value hidden",
        "median_exposure_auc": float(np.nanmedian(aucs)),
        "mean_exposure_auc": float(np.nanmean(aucs)),
        "seconds": time.time() - t0,
    }
    return {
        "meta": meta,
        "summaries": summaries,
        "book_records": {
            str(fraction): sorted(
                records[fraction], key=lambda x: -x["gamma_one_sided"]
            )
            for fraction in FRACTIONS
        },
        "skipped": skipped,
        "limitations": [
            "No recorded rating is treated as an implicit non-interaction; this conflates no exposure, no reading, and no Goodreads record.",
            "Calibration estimates how preference changes among high-propensity observed raters; it does not identify a rare book's actual selection odds ratio.",
            "Each item fold removes several calibration books, not just the target, to make target exclusion computationally feasible.",
        ],
    }


def write_report(results: dict[str, Any]) -> None:
    old = results["previous_calibration"]["summaries"]
    new = results["crossfit_calibration"]["summaries"]
    meta = results["crossfit_calibration"]["meta"]
    lines = [
        "# Target-excluded enthusiast-selection calibration",
        "",
        "## Outcome",
        "",
        "This audit removes the target interaction from the reader embedding and predicts "
        "recorded interaction out of fold. Rating values remain hidden until after propensity "
        "scores are fixed.",
        "",
        f"The model calibrated **{meta['n_targets_calibrated']}** books and achieved median "
        f"held-out interaction AUC **{meta['median_exposure_auc']:.3f}**. AUC measures whether "
        "co-reading features distinguish recorded readers from jury members with no recorded "
        "interaction; it is not a causal exposure validation.",
        "",
        "## Calibration comparison",
        "",
        "| retained | method | Γ q50 | Γ q75 | Γ q90 | Γ q95 | mean esteem inflation |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for prior, current in zip(old, new):
        po = prior["gamma_one_sided_quantiles"]
        pn = current["gamma_one_sided_quantiles"]
        lines.append(
            f"| {100*prior['retained_fraction']:.0f}% | old centroid | "
            f"{po['q50']:.2f} | {po['q75']:.2f} | {po['q90']:.2f} | {po['q95']:.2f} | "
            f"{100*prior['mean_preference_inflation']:.1f} pp |"
        )
        lines.append(
            f"| {100*current['retained_fraction']:.0f}% | target-excluded cross-fit | "
            f"{pn['q50']:.2f} | {pn['q75']:.2f} | {pn['q90']:.2f} | {pn['q95']:.2f} | "
            f"{100*current['mean_preference_inflation']:.1f} pp |"
        )
    lines += [
        "",
        "## Sampling-noise reference",
        "",
        "Random subsets of the same size were drawn 100 times per book. These one-sided Γ "
        "quantiles show how much apparent sensitivity arises from smaller samples alone.",
        "",
        "| retained | observed Γ q50/q75/q90 | random-subset Γ q50/q75/q90 |",
        "|---:|---:|---:|",
    ]
    for current in new:
        q = current["gamma_one_sided_quantiles"]
        n = current["random_subset_gamma_quantiles_median"]
        lines.append(
            f"| {100*current['retained_fraction']:.0f}% | "
            f"{q['q50']:.2f}/{q['q75']:.2f}/{q['q90']:.2f} | "
            f"{n['q50']:.2f}/{n['q75']:.2f}/{n['q90']:.2f} |"
        )
    q25 = new[0]["gamma_one_sided_quantiles"]
    q50 = new[1]["gamma_one_sided_quantiles"]
    lines += [
        "",
        "## Interpretation",
        "",
        f"The 25% retention scenario is deliberately harsh: Γ=1.5 is below its median, while "
        f"Γ=2 is near q75={q25['q75']:.2f}. Under 50% retention, Γ=1.5 is near "
        f"q75={q50['q75']:.2f} and Γ=2 is near q90={q50['q90']:.2f}. This supports using "
        "1.5 as a moderate and 2 as a strong stress test, not as estimated truth. The "
        "random-subset row must be consulted before attributing the whole tail to enthusiast "
        "selection.",
        "",
        "This improves leakage control but does not make selection identifiable. Absence of a "
        "Goodreads rating is not observed exposure, and the high-propensity subset is a "
        "stress-test analogue rather than a reconstruction of a rare book's missing readers.",
        "",
        "## Recommendation",
        "",
        results["recommendation"],
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    t_all = time.time()
    targets, previous = load_calibration_targets()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, all_scores, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, central_mask, _ = materialize_pilot_users(
        con, all_ids, all_scores, broad
    )
    assert int(central_mask.sum()) == JURY_N
    materialize_target_table(con, targets)
    matrix, target_items, matrix_meta = build_binary_interaction_matrix(
        con, len(broad_ids)
    )
    exposures = exposure_sets(con, len(targets))
    pair = next(x for x in PAIR_VARIANTS if x["label"] == CENTRAL_PAIR)
    positive, negative, works, _eligible, pair_meta = build_pair_vote_matrices(
        con, len(broad_ids), pair
    )
    crossfit = calibrate(
        con,
        targets,
        matrix,
        target_items,
        exposures,
        positive,
        negative,
        works,
    )
    q25 = crossfit["summaries"][0]["gamma_one_sided_quantiles"]
    recommendation = (
        f"Retain Γ=1.5 as the primary moderate sensitivity bound and Γ=2 as the strong "
        f"bound while q75/q90 under 25% retention are {q25['q75']:.2f}/{q25['q90']:.2f}. "
        "Keep Γ sensitivity separate from ±u. Next test jury feature families and pair "
        "sampling seeds; revisit these thresholds only if those axes materially alter the "
        "calibration population."
    )
    results = {
        "meta": {
            "purpose": "target-excluded cross-fitted Γ calibration",
            "runtime_seconds": time.time() - t_all,
        },
        "jury_reconstruction": jury_meta,
        "interaction_matrix": matrix_meta,
        "pair_data": pair_meta,
        "previous_calibration": previous,
        "crossfit_calibration": crossfit,
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

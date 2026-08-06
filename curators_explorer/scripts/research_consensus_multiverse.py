#!/usr/bin/env python3
"""Joint jury × pair-definition × self-selection consensus trajectories.

This follows the exposure-adjusted pilot.  It deliberately combines axes that
can interact, while retaining one-factor slices for interpretation:

* rebuilt-jury size: strict / central / broad,
* within-user preference definition,
* one-sided enthusiast self-selection bound Γ.

The full grid is small enough to audit (3 × 3 × 5 = 45 universes) and reuses
fixed sparse user-book observations and fixed latent-community partitions.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_consensus_multiverse
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
from scipy.sparse.linalg import svds

from curators_explorer.scripts.research_consensus_stability_pilot import (
    BROAD_N,
    JURY_N,
    MAX_CATALOG_N,
    TOP_SAVE,
    build_partitions,
    build_preference_embedding,
    jaccard,
    materialize_pilot_users,
    rbo,
    reconstruct_jury,
)
from curators_explorer.scripts.research_exposure_adjusted_consensus import (
    CENTRAL_SPEC,
    MIN_DISTRIBUTED_COVERAGE,
    aggregate_spec,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "consensus_multiverse.json"
OUT_MD = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "CONSENSUS_MULTIVERSE_REPORT.md"
)

JURY_VARIANTS = (
    {"label": "strict_3286", "n": 3_286},
    {"label": "central_4929", "n": JURY_N},
    {"label": "broad_7500", "n": 7_500},
)
PAIR_VARIANTS = (
    {
        "label": "five_vs_le3",
        "description": "5★ versus ≤3★",
        "high_sql": "rating = 5",
        "low_sql": "rating <= 3",
        "spec_overrides": {},
    },
    {
        "label": "five_vs_le2",
        "description": "5★ versus ≤2★",
        "high_sql": "rating = 5",
        "low_sql": "rating <= 2",
        "spec_overrides": {
            "min_community_readers": 2,
            "min_global_readers": 20,
        },
    },
    {
        "label": "ge4_vs_le2",
        "description": "≥4★ versus ≤2★",
        "high_sql": "rating >= 4",
        "low_sql": "rating <= 2",
        "spec_overrides": {
            "min_community_readers": 2,
            "min_global_readers": 20,
        },
    },
)
GAMMA_VALUES = (1.0, 1.25, 1.5, 2.0, 3.0)
CENTRAL_JURY = "central_4929"
CENTRAL_PAIR = "five_vs_le3"
CENTRAL_GAMMA = 1.0
MAX_SIDE = 12
VOTE_SEED = 11


def gamma_label(gamma: float) -> str:
    return str(gamma).replace(".", "p")


def universe_label(jury: str, pair: str, gamma: float) -> str:
    return f"{jury}__{pair}__gamma{gamma_label(gamma)}"


def build_pair_vote_matrices(con, n_users: int, pair: dict[str, Any]):
    label = pair["label"]
    print(f"Building balanced votes for {pair['description']}…", flush=True)
    t0 = time.time()
    vote_table = f"mv_votes_{label}"
    item_table = f"mv_items_{label}"
    # Reproduce the preceding pilot's central sample exactly. Alternative pair
    # definitions receive distinct deterministic salts.
    high_suffix = f"h{VOTE_SEED}" if label == CENTRAL_PAIR else f"h-{label}-{VOTE_SEED}"
    low_suffix = f"l{VOTE_SEED}" if label == CENTRAL_PAIR else f"l-{label}-{VOTE_SEED}"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {vote_table} AS
        WITH rated AS (
            SELECT u.user_idx, e.user_id, e.work_id, e.rating
            FROM ex.all_rating_events e
            JOIN pilot_users u USING (user_id)
            JOIN work_rarity wr USING (work_id)
            WHERE u.broad_rank <= {max(x['n'] for x in JURY_VARIANTS)}
              AND wr.n >= 100 AND wr.n <= {MAX_CATALOG_N}
        ),
        highs0 AS (
            SELECT *, row_number() OVER (
                PARTITION BY user_id
                ORDER BY hash(user_id || '-' || work_id || '-{high_suffix}')
            ) AS rn
            FROM rated WHERE {pair['high_sql']}
        ),
        lows0 AS (
            SELECT *, row_number() OVER (
                PARTITION BY user_id
                ORDER BY hash(user_id || '-' || work_id || '-{low_suffix}')
            ) AS rn
            FROM rated WHERE {pair['low_sql']}
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
    rows = np.asarray(d["user_idx"], dtype=np.int32)
    cols = np.asarray(d["work_idx"], dtype=np.int32)
    y = np.asarray(d["positive"], dtype=np.int8)
    n_works = int(cols.max()) + 1
    shape = (n_users, n_works)
    pos = y == 1
    positive = sparse.coo_matrix(
        (np.ones(int(pos.sum()), dtype=np.float32), (rows[pos], cols[pos])),
        shape=shape,
    ).tocsr()
    negative = sparse.coo_matrix(
        (np.ones(int((~pos).sum()), dtype=np.float32), (rows[~pos], cols[~pos])),
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
    stats = con.execute(
        f"""
        SELECT count(DISTINCT user_id), count(*),
               count(*) FILTER (WHERE positive=1),
               count(*) FILTER (WHERE positive=0)
        FROM {vote_table}
        """
    ).fetchone()
    meta = {
        "label": label,
        "description": pair["description"],
        "n_users": int(stats[0]),
        "n_votes": int(stats[1]),
        "positive_votes": int(stats[2]),
        "negative_votes": int(stats[3]),
        "n_works": n_works,
        "seconds": time.time() - t0,
    }
    print(
        f"  users={meta['n_users']:,} votes={meta['n_votes']:,} "
        f"works={n_works:,} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return positive, negative, works, eligible, meta


def aggregate_counts(partitions, jury_mask, positive, negative):
    current_rows = np.flatnonzero(jury_mask)
    out = []
    for part in partitions:
        k = int(part["k"])
        labels = part["labels"]
        indicator = sparse.csr_matrix(
            (
                np.ones(len(current_rows), dtype=np.float32),
                (current_rows, labels[jury_mask].astype(np.int32)),
            ),
            shape=(len(labels), k),
        )
        out.append(
            {
                "label": part["label"],
                "k": k,
                "wins": np.asarray(
                    (indicator.T @ positive).toarray().T, dtype=np.float64
                ),
                "losses": np.asarray(
                    (indicator.T @ negative).toarray().T, dtype=np.float64
                ),
                "current_sizes": np.bincount(labels[jury_mask], minlength=k),
            }
        )
    return out


def build_exposure_embedding(con, n_users: int):
    """Outcome-blind binary co-reading embedding for selection calibration."""
    print("Building outcome-blind exposure embedding…", flush=True)
    t0 = time.time()
    # pilot_embed_items is created by build_preference_embedding. Reuse the
    # identical item support window so only the signal, not the population,
    # changes between embeddings.
    d = con.execute(
        """
        SELECT u.user_idx, i.item_idx, i.n_users
        FROM ex.all_rating_events e
        JOIN pilot_users u USING (user_id)
        JOIN pilot_embed_items i USING (work_id)
        ORDER BY u.user_idx, i.item_idx
        """
    ).fetchnumpy()
    row = np.asarray(d["user_idx"], dtype=np.int32)
    col = np.asarray(d["item_idx"], dtype=np.int32)
    support = np.asarray(d["n_users"], dtype=np.float32)
    value = np.sqrt(np.maximum(np.log((n_users + 1.0) / (support + 1.0)), 0.05))
    n_items = int(col.max()) + 1
    mat = sparse.coo_matrix(
        (value.astype(np.float32), (row, col)), shape=(n_users, n_items)
    ).tocsr()
    row_norm = np.sqrt(np.asarray(mat.multiply(mat).sum(axis=1)).ravel())
    mat = sparse.diags(1.0 / np.maximum(row_norm, 1e-8)) @ mat
    k = min(24, min(mat.shape) - 1)
    u, s, _ = svds(mat, k=k, which="LM", random_state=19)
    order = np.argsort(-s)
    embedding = np.asarray(u[:, order] * s[order][None, :], dtype=np.float32)
    norm = np.linalg.norm(embedding, axis=1)
    embedding /= np.maximum(norm[:, None], 1e-8)
    meta = {
        "n_users": n_users,
        "n_items": n_items,
        "n_events": int(mat.nnz),
        "embedding_dim": k,
        "signal": "binary rated-book interaction × mild inverse-popularity weight; no ratings",
        "seconds": time.time() - t0,
    }
    print(
        f"  matrix={mat.shape} nnz={mat.nnz:,} dim={k} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return embedding, meta


def make_universe(jury, pair, gamma, metric, works):
    ranking = [works[i]["work_id"] for i in metric["ranking"]]
    return {
        "label": universe_label(jury["label"], pair["label"], gamma),
        "jury": jury["label"],
        "jury_n": jury["n"],
        "pair": pair["label"],
        "pair_description": pair["description"],
        "gamma": float(gamma),
        "metric": metric,
        "works": works,
        "ranking": ranking,
        "n_rankable": metric["n_rankable"],
    }


def rank_map(universe):
    return {wid: r + 1 for r, wid in enumerate(universe["ranking"])}


def universe_score_map(universe):
    metric = universe["metric"]
    return {
        universe["works"][i]["work_id"]: float(100.0 * metric["score"][i])
        for i in metric["ranking"]
        if np.isfinite(metric["score"][i])
    }


def slim_universe(universe, baseline_ranking):
    return {
        "label": universe["label"],
        "jury": universe["jury"],
        "jury_n": universe["jury_n"],
        "pair": universe["pair"],
        "pair_description": universe["pair_description"],
        "gamma": universe["gamma"],
        "n_rankable": universe["n_rankable"],
        "jaccard50": jaccard(baseline_ranking, universe["ranking"], 50),
        "jaccard200": jaccard(baseline_ranking, universe["ranking"], 200),
        "rbo98": rbo(baseline_ranking, universe["ranking"], p=0.98),
        "top_work_ids": universe["ranking"],
    }


def diagnostic_rows(universes, baseline):
    maps = {u["label"]: rank_map(u) for u in universes}
    score_maps = {u["label"]: universe_score_map(u) for u in universes}
    metadata = {}
    for u in universes:
        metadata.update({x["work_id"]: x for x in u["works"]})
    union = set()
    for m in maps.values():
        union.update(m)
    missing = max(u["n_rankable"] for u in universes) + 1

    jury_labels = [
        universe_label(j["label"], CENTRAL_PAIR, CENTRAL_GAMMA)
        for j in JURY_VARIANTS
    ]
    pair_labels = [
        universe_label(CENTRAL_JURY, p["label"], CENTRAL_GAMMA)
        for p in PAIR_VARIANTS
    ]
    gamma_labels = [
        universe_label(CENTRAL_JURY, CENTRAL_PAIR, g) for g in GAMMA_VALUES
    ]
    central_map = maps[baseline["label"]]
    central_metric = baseline["metric"]
    central_index = {x["work_id"]: i for i, x in enumerate(baseline["works"])}
    rows = []
    for wid in union:
        all_ranks = np.asarray([maps[u["label"]].get(wid, missing) for u in universes])
        jury_ranks = np.asarray([maps[x].get(wid, missing) for x in jury_labels])
        pair_ranks = np.asarray([maps[x].get(wid, missing) for x in pair_labels])
        jury_present = np.asarray([wid in maps[x] for x in jury_labels])
        pair_present = np.asarray([wid in maps[x] for x in pair_labels])
        gamma_ranks = np.asarray([maps[x].get(wid, missing) for x in gamma_labels])
        gamma_scores = {
            str(g): score_maps[label].get(wid)
            for g, label in zip(GAMMA_VALUES, gamma_labels)
        }
        critical_gamma = None
        for g in GAMMA_VALUES:
            s = gamma_scores[str(g)]
            if s is None or s < 50.0:
                critical_gamma = float(g)
                break

        idx = central_index.get(wid)
        central_rank = central_map.get(wid)
        row = {
            **metadata[wid],
            "central_rank": central_rank,
            "central_score": None,
            "central_uncertainty": None,
            "conditional_esteem": None,
            "heterogeneity": None,
            "coverage": None,
            "jury_votes": None,
            "jury_top200_rate": float(np.mean(jury_ranks <= 200)),
            "pair_top200_rate": float(np.mean(pair_ranks <= 200)),
            "jury_rankable_rate": float(np.mean(jury_present)),
            "pair_rankable_rate": float(np.mean(pair_present)),
            "gamma_top200_rate": float(np.mean(gamma_ranks <= 200)),
            "cross_top200_rate": float(np.mean(all_ranks <= 200)),
            "best_cross_rank": int(np.min(all_ranks)),
            "worst_cross_rank": int(np.max(all_ranks)),
            "jury_rank_range": int(np.max(jury_ranks) - np.min(jury_ranks)),
            "pair_rank_range": int(np.max(pair_ranks) - np.min(pair_ranks)),
            "gamma_rank_range": int(np.max(gamma_ranks) - np.min(gamma_ranks)),
            "critical_gamma_below_50": critical_gamma,
            "gamma_scores": gamma_scores,
            "one_factor_ranks": {
                "jury": {label: int(rank) for label, rank in zip(jury_labels, jury_ranks)},
                "pair": {label: int(rank) for label, rank in zip(pair_labels, pair_ranks)},
                "gamma": {label: int(rank) for label, rank in zip(gamma_labels, gamma_ranks)},
            },
        }
        if idx is not None and central_rank is not None:
            row.update(
                {
                    "central_score": float(100.0 * central_metric["score"][idx]),
                    "central_uncertainty": float(
                        100.0 * central_metric["uncertainty"][idx]
                    ),
                    "conditional_esteem": float(central_metric["esteem"][idx]),
                    "heterogeneity": float(central_metric["heterogeneity"][idx]),
                    "coverage": float(central_metric["coverage"][idx]),
                    "jury_votes": int(central_metric["total_votes"][idx]),
                }
            )
        rows.append(row)
    rows.sort(
        key=lambda x: (
            x["central_rank"] is None,
            x["central_rank"] or missing,
            x["best_cross_rank"],
        )
    )
    return rows


def classify(rows):
    central = [x for x in rows if x["central_rank"] and x["central_rank"] <= 200]
    joint_robust = sorted(
        [
            x
            for x in central
            if x["central_score"] >= 50.0
            and x["jury_top200_rate"] >= 2.0 / 3.0
            and x["pair_top200_rate"] >= 2.0 / 3.0
            and x["cross_top200_rate"] >= 2.0 / 3.0
            and x["gamma_scores"].get("1.5") is not None
            and x["gamma_scores"]["1.5"] >= 50.0
        ],
        key=lambda x: x["central_rank"],
    )
    selection_sensitive = sorted(
        [
            x
            for x in central
            if x["central_score"] >= 50.0
            and x["critical_gamma_below_50"] is not None
            and x["critical_gamma_below_50"] <= 1.5
        ],
        key=lambda x: (x["critical_gamma_below_50"], x["central_rank"]),
    )
    jury_sensitive = sorted(
        [
            x
            for x in central
            if x["jury_rankable_rate"] == 1.0
            and x["jury_top200_rate"] < 2.0 / 3.0
        ],
        key=lambda x: (x["jury_top200_rate"], -x["jury_rank_range"]),
    )
    jury_evidence_sensitive = sorted(
        [x for x in central if x["jury_rankable_rate"] < 1.0],
        key=lambda x: (x["jury_rankable_rate"], -x["jury_rank_range"]),
    )
    pair_sensitive = sorted(
        [
            x
            for x in central
            if x["pair_rankable_rate"] == 1.0
            and x["pair_top200_rate"] < 2.0 / 3.0
        ],
        key=lambda x: (x["pair_top200_rate"], -x["pair_rank_range"]),
    )
    pair_evidence_sensitive = sorted(
        [x for x in central if x["pair_rankable_rate"] < 1.0],
        key=lambda x: (x["pair_rankable_rate"], -x["pair_rank_range"]),
    )
    return (
        joint_robust,
        selection_sensitive,
        jury_sensitive,
        jury_evidence_sensitive,
        pair_sensitive,
        pair_evidence_sensitive,
    )


def summarize_axes(universes, baseline):
    base = baseline["ranking"]
    rows = []
    for u in universes:
        differs = sum(
            [
                u["jury"] != CENTRAL_JURY,
                u["pair"] != CENTRAL_PAIR,
                u["gamma"] != CENTRAL_GAMMA,
            ]
        )
        if differs <= 1:
            rows.append(
                {
                    "label": u["label"],
                    "jury": u["jury"],
                    "pair": u["pair"],
                    "gamma": u["gamma"],
                    "n_rankable": u["n_rankable"],
                    "jaccard50": jaccard(base, u["ranking"], 50),
                    "jaccard200": jaccard(base, u["ranking"], 200),
                    "rbo98": rbo(base, u["ranking"], p=0.98),
                }
            )
    crossed = [u for u in universes if u["label"] != baseline["label"]]
    cross_metrics = {
        "n": len(crossed),
        "jaccard50_mean": float(
            np.mean([jaccard(base, u["ranking"], 50) for u in crossed])
        ),
        "jaccard50_min": float(
            np.min([jaccard(base, u["ranking"], 50) for u in crossed])
        ),
        "jaccard200_mean": float(
            np.mean([jaccard(base, u["ranking"], 200) for u in crossed])
        ),
        "jaccard200_min": float(
            np.min([jaccard(base, u["ranking"], 200) for u in crossed])
        ),
        "rbo98_mean": float(np.mean([rbo(base, u["ranking"], p=0.98) for u in crossed])),
    }
    return rows, cross_metrics


def calibrate_selection_gamma(
    embedding,
    central_mask,
    positive,
    negative,
    works,
    central_metric,
):
    """Pseudo-obscure broadly observed books using outcome-blind reader affinity.

    For each well-covered book, form the centroid of embeddings for everyone
    with a sampled positive or negative observation. Retain only the readers
    nearest that exposure centroid, as a proxy for the core audience that would
    disproportionately discover an obscure title. The outcome is not used to
    form the centroid or choose the subset.

    This is a calibration heuristic, not identification. The exposure embedding
    contains binary co-reading only and never a target rating outcome; it still
    observes that the user interacted with the target book.
    """
    print("Calibrating Γ with pseudo-obscured broad-readership books…", flush=True)
    pmat = positive.tocsc()
    nmat = negative.tocsc()
    eligible_indices = np.flatnonzero(
        central_metric["eligible"]
        & (central_metric["total_votes"] >= 100)
        & (central_metric["coverage"] >= 0.80)
    )
    fractions = (0.25, 0.50, 0.75)
    records = {f: [] for f in fractions}
    central_users = set(np.flatnonzero(central_mask).tolist())
    for idx in eligible_indices:
        pr = pmat.indices[pmat.indptr[idx] : pmat.indptr[idx + 1]]
        nr = nmat.indices[nmat.indptr[idx] : nmat.indptr[idx + 1]]
        pr = np.asarray([x for x in pr if int(x) in central_users], dtype=np.int32)
        nr = np.asarray([x for x in nr if int(x) in central_users], dtype=np.int32)
        voters = np.concatenate([pr, nr])
        if len(voters) < 100:
            continue
        y = np.concatenate(
            [np.ones(len(pr), dtype=float), np.zeros(len(nr), dtype=float)]
        )
        center = embedding[voters].mean(axis=0)
        norm = float(np.linalg.norm(center))
        if norm <= 1e-9:
            continue
        similarity = embedding[voters] @ (center / norm)
        order = np.argsort(-similarity, kind="stable")
        p_full = float((y.sum() + 0.5) / (len(y) + 1.0))
        odds_full = p_full / max(1.0 - p_full, 1e-9)
        for fraction in fractions:
            keep_n = max(20, int(math.ceil(len(y) * fraction)))
            selected = y[order[:keep_n]]
            p_selected = float((selected.sum() + 0.5) / (len(selected) + 1.0))
            odds_selected = p_selected / max(1.0 - p_selected, 1e-9)
            gamma = odds_selected / max(odds_full, 1e-9)
            records[fraction].append(
                {
                    "work_id": works[idx]["work_id"],
                    "title": works[idx]["title"],
                    "author": works[idx]["author"],
                    "n_full": int(len(y)),
                    "n_selected": int(keep_n),
                    "p_full": p_full,
                    "p_selected": p_selected,
                    "gamma": float(gamma),
                    "gamma_one_sided": float(max(gamma, 1.0)),
                }
            )

    summaries = []
    for fraction in fractions:
        rows = records[fraction]
        gammas = np.asarray([x["gamma_one_sided"] for x in rows], dtype=float)
        selected_p = np.asarray([x["p_selected"] for x in rows], dtype=float)
        full_p = np.asarray([x["p_full"] for x in rows], dtype=float)
        quantiles = {
            f"q{q}": float(np.quantile(gammas, q / 100.0))
            for q in (50, 75, 90, 95)
        }
        corrected = selected_p / (
            quantiles["q50"] - (quantiles["q50"] - 1.0) * selected_p
        )
        summaries.append(
            {
                "retained_fraction": fraction,
                "n_books": len(rows),
                "share_affinity_subset_higher": float(
                    np.mean(selected_p > full_p)
                ),
                "mean_preference_inflation": float(np.mean(selected_p - full_p)),
                "gamma_one_sided_quantiles": quantiles,
                "uncorrected_mae_to_full": float(np.mean(np.abs(selected_p - full_p))),
                "median_gamma_corrected_mae_to_full": float(
                    np.mean(np.abs(corrected - full_p))
                ),
            }
        )
    return {
        "eligibility": "central rankable; >=100 jury votes; >=80% community coverage",
        "selection_proxy": "nearest readers to outcome-blind observed-reader embedding centroid",
        "summaries": summaries,
        "book_records": {
            str(f): sorted(
                records[f], key=lambda x: -x["gamma_one_sided"]
            )[:100]
            for f in fractions
        },
        "limitations": (
            "Calibration proxy only; the binary co-reading embedding includes the target "
            "interaction and the broad observed readership is itself not randomized."
        ),
    }


def fmt_book(x):
    return f"{x['title']} — {x['author']}"


def write_diag_table(lines, rows, limit=35):
    lines += [
        "| book | base | score ± u | Γ floor | jury top200/evid | pair top200/evid | crossed top200 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for x in rows[:limit]:
        score = "—"
        if x["central_score"] is not None:
            score = f"{x['central_score']:.1f} ± {x['central_uncertainty']:.1f}"
        critical = x["critical_gamma_below_50"]
        lines.append(
            f"| {fmt_book(x)} | {x['central_rank'] or '—'} | {score} | "
            f"{critical if critical is not None else '>3'} | "
            f"{100*x['jury_top200_rate']:.0f}%/{100*x['jury_rankable_rate']:.0f}% | "
            f"{100*x['pair_top200_rate']:.0f}%/{100*x['pair_rankable_rate']:.0f}% | "
            f"{100*x['cross_top200_rate']:.0f}% |"
        )


def write_report(results):
    lines = [
        "# Joint consensus multiverse: jury, pair definition, and self-selection",
        "",
        "## Why combine the axes",
        "",
        "A book can survive jury changes and pair-definition changes separately yet fail when "
        "both move together, especially after allowing enthusiast self-selection. This pilot "
        "therefore reports interpretable one-factor trajectories and a compact crossed grid.",
        "",
        "## Design",
        "",
        f"- Jury sizes: {[x['n'] for x in JURY_VARIANTS]} from the same behavioral score.",
        f"- Pair definitions: {[x['description'] for x in PAIR_VARIANTS]}.",
        "- The ≤2★ variants use proportionally lower evidence floors (2 readers/community "
        "and 20 globally versus 3/30) because those outcomes are intrinsically sparser. "
        "Coverage remains a separate reported axis.",
        f"- Selection bounds Γ: {list(GAMMA_VALUES)}; Γ=1 is no unmeasured selection, while "
        "larger Γ allows positive-outcome readers to be more likely to become observed raters.",
        f"- Full crossed universes: **{results['meta']['n_universes']}**; fixed community "
        f"partitions: **{results['meta']['n_partitions']}**.",
        f"- Distributed eligibility retains the earlier saturating "
        f"{100*MIN_DISTRIBUTED_COVERAGE:.0f}% community-coverage gate.",
        "",
        "## One-factor trajectories",
        "",
        "| universe | rankable | J@50 | J@200 | RBO |",
        "|---|---:|---:|---:|---:|",
    ]
    for x in results["one_factor_stability"]:
        lines.append(
            f"| {x['label']} | {x['n_rankable']} | {x['jaccard50']:.3f} | "
            f"{x['jaccard200']:.3f} | {x['rbo98']:.3f} |"
        )
    c = results["crossed_stability"]
    lines += [
        "",
        "## Crossed stability",
        "",
        f"Across {c['n']} non-baseline universes, mean/worst J@50 is "
        f"**{c['jaccard50_mean']:.3f}/{c['jaccard50_min']:.3f}**, mean/worst J@200 is "
        f"**{c['jaccard200_mean']:.3f}/{c['jaccard200_min']:.3f}**, and mean RBO is "
        f"**{c['rbo98_mean']:.3f}**.",
        "",
        "## Data-informed Γ calibration by pseudo-obscuring",
        "",
        "Broadly observed books were made artificially obscure by retaining only readers "
        "nearest the book's observed-reader binary co-reading centroid. Selection uses "
        "outcome-blind exposure affinity—the embedding never sees rating values. Γ is the "
        "resulting positive-odds "
        "inflation relative to the full observed readership.",
        "",
        "| readers retained | books | subset higher | mean esteem inflation | Γ q50 | Γ q75 | Γ q90 | raw MAE | corrected MAE |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for x in results["selection_calibration"]["summaries"]:
        q = x["gamma_one_sided_quantiles"]
        lines.append(
            f"| {100*x['retained_fraction']:.0f}% | {x['n_books']} | "
            f"{100*x['share_affinity_subset_higher']:.0f}% | "
            f"{100*x['mean_preference_inflation']:.1f} pp | {q['q50']:.2f} | "
            f"{q['q75']:.2f} | {q['q90']:.2f} | "
            f"{x['uncorrected_mae_to_full']:.3f} | "
            f"{x['median_gamma_corrected_mae_to_full']:.3f} |"
        )
    lines += [
        "",
        "This calibrates plausible sensitivity scenarios, not the actual Γ of a rare book. "
        "The broad comparison group is still selected, and the binary embedding includes "
        "the fact of the target interaction; treat the estimates as lower-resolution bounds.",
        "",
        "## Jointly robust provisional tier",
        "",
        "Central top-200 books with score≥50, top-200 survival in at least two-thirds of "
        "jury variants, pair variants, and all crossed universes, and a Γ=1.5 conservative "
        "score still at least 50.",
        "",
    ]
    write_diag_table(lines, results["jointly_robust"])
    lines += [
        "",
        "## Selection-sensitive central books",
        "",
        "The lower-tail consensus score falls below 50 by Γ≤1.5. This is a sensitivity "
        "statement, not proof that selection of that strength exists.",
        "",
    ]
    write_diag_table(lines, results["selection_sensitive"], limit=30)
    lines += ["", "## Jury-sensitive central books", ""]
    if results["jury_sensitive"]:
        write_diag_table(lines, results["jury_sensitive"], limit=30)
    else:
        lines.append(
            "None among books rankable under all three jury sizes. Observed jury-size "
            "failures were evidence/coverage failures rather than top-200 preference shifts."
        )
    lines += ["", "## Jury-evidence-sensitive central books", ""]
    write_diag_table(lines, results["jury_evidence_sensitive"], limit=30)
    lines += ["", "## Pair-definition-sensitive central books", ""]
    write_diag_table(lines, results["pair_sensitive"], limit=30)
    lines += ["", "## Pair-evidence-sensitive central books", ""]
    write_diag_table(lines, results["pair_evidence_sensitive"], limit=30)
    lines += [
        "",
        "## Interpretation",
        "",
        "- Γ trajectories bound unmeasured enthusiast selection; pseudo-obscuring provides "
        "a rough empirical scale, not a book-specific estimate of actual selection strength.",
        "- `±u` remains sampling/partition uncertainty. Γ sensitivity is systematic bias and "
        "must remain a separate field or trajectory.",
        "- Jury variants currently change strictness along the chosen rich-behavior score. "
        "Feature-family and soft-weight juries remain future axes.",
        "- Pair definitions test rating-threshold semantics, not every possible pair sampler. "
        "Repeated sampling seeds remain a useful later variance check.",
        "- A book missing from a strict universe because evidence falls below the coverage "
        "gate is evidence-sensitive, not necessarily disliked.",
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
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, all_scores, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, central_mask, _ = materialize_pilot_users(
        con, all_ids, all_scores, broad
    )
    embedding, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(embedding, central_mask)
    exposure_embedding, exposure_embedding_meta = build_exposure_embedding(
        con, len(broad_ids)
    )
    jury_masks = {
        x["label"]: np.arange(len(broad_ids)) < x["n"] for x in JURY_VARIANTS
    }

    pair_data = {}
    pair_meta = []
    for pair in PAIR_VARIANTS:
        positive, negative, works, eligible, meta = build_pair_vote_matrices(
            con, len(broad_ids), pair
        )
        pair_data[pair["label"]] = (positive, negative, works, eligible)
        pair_meta.append(meta)

    universes = []
    print("Running 45 crossed consensus universes…", flush=True)
    for pair in PAIR_VARIANTS:
        positive, negative, works, eligible = pair_data[pair["label"]]
        for jury in JURY_VARIANTS:
            counts = aggregate_counts(
                partitions, jury_masks[jury["label"]], positive, negative
            )
            for gamma in GAMMA_VALUES:
                pair_spec = {**CENTRAL_SPEC, **pair["spec_overrides"]}
                metric = aggregate_spec(
                    counts,
                    pair_spec,
                    eligible,
                    selection_gamma=gamma,
                )
                universes.append(make_universe(jury, pair, gamma, metric, works))

    baseline_label = universe_label(CENTRAL_JURY, CENTRAL_PAIR, CENTRAL_GAMMA)
    baseline = next(u for u in universes if u["label"] == baseline_label)
    diagnostics = diagnostic_rows(universes, baseline)
    (
        robust,
        selection_sensitive,
        jury_sensitive,
        jury_evidence_sensitive,
        pair_sensitive,
        pair_evidence_sensitive,
    ) = classify(diagnostics)
    one_factor, crossed = summarize_axes(universes, baseline)
    central_positive, central_negative, central_works, _central_eligible = pair_data[
        CENTRAL_PAIR
    ]
    selection_calibration = calibrate_selection_gamma(
        exposure_embedding,
        central_mask,
        central_positive,
        central_negative,
        central_works,
        baseline["metric"],
    )
    recommendation = (
        "Treat the jointly robust books as the current strongest candidates, not a locked "
        "canon. Next cross-fit a target-excluded exposure propensity model to validate the "
        "pseudo-obscuring Γ scale, then add behavioral feature-family and pair-sampling-seed "
        "trajectories."
    )
    results = {
        "meta": {
            "purpose": "joint jury/pair/self-selection consensus trajectories",
            "n_universes": len(universes),
            "n_partitions": len(partitions),
            "jury_variants": list(JURY_VARIANTS),
            "pair_variants": list(PAIR_VARIANTS),
            "gamma_values": list(GAMMA_VALUES),
            "central_universe": baseline_label,
            "runtime_seconds": time.time() - t_all,
        },
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "exposure_embedding": exposure_embedding_meta,
        "pair_data": pair_meta,
        "one_factor_stability": one_factor,
        "crossed_stability": crossed,
        "selection_calibration": selection_calibration,
        "universes": [slim_universe(u, baseline["ranking"]) for u in universes],
        "central_top": [x for x in diagnostics if x["central_rank"] is not None][:200],
        "jointly_robust": robust,
        "selection_sensitive": selection_sensitive,
        "jury_sensitive": jury_sensitive,
        "jury_evidence_sensitive": jury_evidence_sensitive,
        "pair_sensitive": pair_sensitive,
        "pair_evidence_sensitive": pair_evidence_sensitive,
        "book_diagnostics": diagnostics[:2500],
        "recommendation": recommendation,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(results)
    print(
        f"Wrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True
    )
    con.close()


if __name__ == "__main__":
    main()

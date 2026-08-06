#!/usr/bin/env python3
"""Focused pilot: community-robust stability of the rebuilt literary jury.

This does *not* use clusters to discover a canon. It reconstructs the current
rich behavioral jury, discovers several user partitions from centered rating
behavior, and uses those partitions only as perturbations:

* community-only rankings (diagnostic),
* equal-community weighting,
* leave-one-community-out weighting,
* bounded random community reweighting.

All ranking universes reuse fixed per-user pairwise sufficient statistics.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_consensus_stability_pilot
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

from curators_explorer.scripts.research_jury_rebuild import (
    FEATURES,
    fetch_frame,
    materialize_behavior_features,
    materialize_model_frame,
    materialize_rich_behavior_features,
    ridge_oof,
)
from curators_explorer.scripts.research_purity_strictness_sweep import make_jury
from curators_explorer.scripts.research_ratings_only_canon import _con, materialize_base
from curators_explorer.scripts.research_threeway_unseeded import (
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "consensus_stability_pilot.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "CONSENSUS_STABILITY_PILOT_REPORT.md"

JURY_N = 4_929
BROAD_N = 20_000
EMBED_DIM = 24
CLUSTER_COUNTS = (6, 10, 16)
CLUSTER_SEEDS = (11, 29, 47)
RANDOM_REWEIGHTS = 6
TOP_SAVE = 500
MAX_CATALOG_N = 120_000
MIN_ITEM_POOL_SUPPORT = 30
MAX_ITEM_POOL_SHARE = 0.80
PAIR_HIGHS = 12
PAIR_LOWS = 12
PAIR_SEED = 11
MIN_PAIR_SUPPORT = 40.0
PAIR_SHRINK = 50.0
MIXTURE_STABLE_RATE = 0.80
DISTRIBUTED_COMMUNITY_RATE = 0.50
MAX_NORMALIZED_CONCENTRATION = 0.25
MAX_DISTRIBUTED_LOO_DROP = 100

RUSSIAN_AUTHOR_MARKERS = (
    "dostoyevsky",
    "tolstoy",
    "nabokov",
    "bulgakov",
    "chekhov",
    "turgenev",
    "gogol",
    "pasternak",
    "solzhenitsyn",
    "lermontov",
    "pushkin",
    "zamyatin",
    "grossman",
)


def reconstruct_jury(con) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    """Return all candidate IDs, OOF rich scores, current jury IDs, broad IDs."""
    print("Reconstructing current rich behavioral jury…", flush=True)
    t0 = time.time()
    materialize_base(con)
    teacher = make_jury(con, purity=65, strictness=25, name="jury_teacher")
    materialize_work_author_year(con)
    generic = materialize_behavior_features(con)
    rich = materialize_rich_behavior_features(con)
    frame = materialize_model_frame(con)
    ids, folds, y, teacher_w, x = fetch_frame(con)
    # bins are unused when matched=False, but ridge_oof keeps one interface.
    bins = np.zeros(len(ids), dtype=np.int8)
    score, coef = ridge_oof(
        x,
        y,
        teacher_w,
        folds,
        bins,
        FEATURES,
        matched=False,
    )
    order = np.argsort(-score, kind="stable")
    current = ids[order[:JURY_N]]
    broad = ids[order[:BROAD_N]]
    meta = {
        "jury_n": JURY_N,
        "broad_n": BROAD_N,
        "candidate_n": len(ids),
        "teacher": teacher,
        "frame": frame,
        "generic_features": generic,
        "rich_features": rich,
        "top_coefficients": [
            [k, float(v)]
            for k, v in sorted(coef.items(), key=lambda z: -abs(z[1]))[:20]
        ],
        "seconds": time.time() - t0,
    }
    print(
        f"  current={len(current):,} broad={len(broad):,} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return meta, ids, score, broad


def materialize_pilot_users(
    con, all_ids: np.ndarray, score: np.ndarray, broad: np.ndarray
) -> tuple[np.ndarray, np.ndarray, dict[int, int]]:
    score_by_id = {int(u): float(s) for u, s in zip(all_ids, score)}
    current_set = {int(x) for x in broad[:JURY_N]}
    rows = [
        (i, int(uid), score_by_id[int(uid)], int(int(uid) in current_set), rank + 1)
        for i, (rank, uid) in enumerate(zip(range(len(broad)), broad))
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
    ids = np.asarray([r[1] for r in rows], dtype=np.int64)
    current_mask = np.asarray([bool(r[3]) for r in rows], dtype=bool)
    return ids, current_mask, {int(uid): i for i, uid in enumerate(ids)}


def build_preference_embedding(con, n_users: int) -> tuple[np.ndarray, dict[str, Any]]:
    """Sparse SVD of centered ratings, with mild inverse-popularity weighting."""
    print("Building centered user–book preference embedding…", flush=True)
    t0 = time.time()
    max_support = int(n_users * MAX_ITEM_POOL_SHARE)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE pilot_embed_items AS
        WITH support AS (
            SELECT e.work_id, count(*)::BIGINT AS n_users
            FROM ex.all_rating_events e JOIN pilot_users u USING (user_id)
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
        np.maximum(np.log((n_users + 1.0) / (support + 1.0)), 0.05)
    )
    n_items = int(col.max()) + 1
    mat = sparse.coo_matrix(
        (value.astype(np.float32), (row, col)), shape=(n_users, n_items)
    ).tocsr()
    row_norm = np.sqrt(np.asarray(mat.multiply(mat).sum(axis=1)).ravel())
    row_norm = np.maximum(row_norm, 1e-8)
    mat = sparse.diags(1.0 / row_norm) @ mat
    k = min(EMBED_DIM, min(mat.shape) - 1)
    u, s, _vt = svds(mat, k=k, which="LM", random_state=17)
    order = np.argsort(-s)
    s = s[order]
    emb = np.asarray(u[:, order] * s[None, :], dtype=np.float32)
    emb_norm = np.linalg.norm(emb, axis=1)
    emb /= np.maximum(emb_norm[:, None], 1e-8)
    meta = {
        "n_users": n_users,
        "n_items": n_items,
        "n_events": int(mat.nnz),
        "embedding_dim": int(k),
        "singular_values": [float(x) for x in s],
        "seconds": time.time() - t0,
        "signal": "row-centered rating residual × mild inverse-popularity weight",
    }
    print(
        f"  matrix={mat.shape} nnz={mat.nnz:,} dim={k} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return emb, meta


def cosine_kmeans(x: np.ndarray, k: int, seed: int, *, max_iter: int = 60):
    """Small deterministic spherical k-means, avoiding another dependency."""
    rng = np.random.default_rng(seed)
    n = len(x)
    centers = np.empty((k, x.shape[1]), dtype=np.float32)
    first = int(rng.integers(n))
    centers[0] = x[first]
    best_dist = 1.0 - x @ centers[0]
    for j in range(1, k):
        probs = np.maximum(best_dist, 1e-8)
        probs /= probs.sum()
        idx = int(rng.choice(n, p=probs))
        centers[j] = x[idx]
        best_dist = np.minimum(best_dist, 1.0 - x @ centers[j])

    labels = np.zeros(n, dtype=np.int16)
    last = None
    for iteration in range(max_iter):
        sim = x @ centers.T
        labels = np.argmax(sim, axis=1).astype(np.int16)
        if last is not None and np.array_equal(labels, last):
            break
        last = labels.copy()
        for j in range(k):
            members = x[labels == j]
            if not len(members):
                centers[j] = x[int(np.argmin(np.max(sim, axis=1)))]
                continue
            c = members.mean(axis=0)
            centers[j] = c / max(float(np.linalg.norm(c)), 1e-8)
    inertia = float(np.mean(1.0 - np.max(x @ centers.T, axis=1)))
    return labels, centers, {"iterations": iteration + 1, "cosine_inertia": inertia}


def build_partitions(emb: np.ndarray, current_mask: np.ndarray):
    print("Clustering user embedding at multiple resolutions/seeds…", flush=True)
    partitions = []
    for k in CLUSTER_COUNTS:
        for seed in CLUSTER_SEEDS:
            labels, _centers, fit = cosine_kmeans(emb, k, seed)
            broad_sizes = np.bincount(labels, minlength=k)
            current_sizes = np.bincount(labels[current_mask], minlength=k)
            partitions.append(
                {
                    "label": f"k{k}_s{seed}",
                    "k": k,
                    "seed": seed,
                    "labels": labels,
                    "broad_sizes": broad_sizes,
                    "current_sizes": current_sizes,
                    **fit,
                }
            )
            print(
                f"  k={k:2d} seed={seed}: current min/med/max="
                f"{current_sizes.min()}/{int(np.median(current_sizes))}/{current_sizes.max()}",
                flush=True,
            )
    return partitions


def build_pair_matrices(con, n_users: int):
    """Equivalent to fixed 12×12 pairs, compressed to user×book win/loss counts."""
    print("Precomputing reusable per-user pairwise counts…", flush=True)
    t0 = time.time()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE pilot_user_book_pairs AS
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
                ORDER BY hash(user_id || '-' || work_id || '-h{PAIR_SEED}')
            ) AS rn FROM rated WHERE rating=5
        ),
        lows0 AS (
            SELECT *, row_number() OVER (
                PARTITION BY user_id
                ORDER BY hash(user_id || '-' || work_id || '-l{PAIR_SEED}')
            ) AS rn FROM rated WHERE rating<=3
        ),
        highs AS (SELECT * FROM highs0 WHERE rn<={PAIR_HIGHS}),
        lows AS (SELECT * FROM lows0 WHERE rn<={PAIR_LOWS}),
        hc AS (SELECT user_id, count(*)::DOUBLE AS n_high FROM highs GROUP BY user_id),
        lc AS (SELECT user_id, count(*)::DOUBLE AS n_low FROM lows GROUP BY user_id),
        pieces AS (
            SELECT h.user_idx, h.work_id, l.n_low AS wins, 0.0::DOUBLE AS losses
            FROM highs h JOIN lc l USING (user_id)
            UNION ALL
            SELECT l.user_idx, l.work_id, 0.0::DOUBLE AS wins, h.n_high AS losses
            FROM lows l JOIN hc h USING (user_id)
        )
        SELECT user_idx, work_id, sum(wins)::DOUBLE AS wins, sum(losses)::DOUBLE AS losses
        FROM pieces GROUP BY user_idx, work_id
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE pilot_rank_items AS
        SELECT work_id, (row_number() OVER (ORDER BY work_id)-1)::INTEGER AS work_idx
        FROM (SELECT DISTINCT work_id FROM pilot_user_book_pairs)
        """
    )
    d = con.execute(
        """
        SELECT p.user_idx, i.work_idx, p.wins, p.losses
        FROM pilot_user_book_pairs p JOIN pilot_rank_items i USING (work_id)
        """
    ).fetchnumpy()
    rows = np.asarray(d["user_idx"], dtype=np.int32)
    cols = np.asarray(d["work_idx"], dtype=np.int32)
    win_v = np.asarray(d["wins"], dtype=np.float32)
    loss_v = np.asarray(d["losses"], dtype=np.float32)
    n_works = int(cols.max()) + 1
    shape = (n_users, n_works)
    wins = sparse.coo_matrix((win_v, (rows, cols)), shape=shape).tocsr()
    losses = sparse.coo_matrix((loss_v, (rows, cols)), shape=shape).tocsr()

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
        FROM pilot_rank_items i
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
    meta = {
        "n_users": n_users,
        "n_works": n_works,
        "n_user_book_rows": int(wins.nnz),
        "seconds": time.time() - t0,
        "pair_sample": {"highs": PAIR_HIGHS, "lows": PAIR_LOWS, "seed": PAIR_SEED},
    }
    print(
        f"  pair matrices={shape}, nnz={wins.nnz:,} ({time.time()-t0:.1f}s)",
        flush=True,
    )
    return wins, losses, works, eligible, meta


def rank_weights(
    wins: sparse.csr_matrix,
    losses: sparse.csr_matrix,
    weights: np.ndarray,
    eligible: np.ndarray,
    *,
    top_n: int = TOP_SAVE,
) -> dict[str, Any]:
    w = np.asarray(wins.T @ weights).ravel()
    l = np.asarray(losses.T @ weights).ravel()
    n = w + l
    score = np.zeros_like(n, dtype=np.float64)
    ok = (n >= MIN_PAIR_SUPPORT) & eligible
    score[ok] = (n[ok] / (n[ok] + PAIR_SHRINK)) * (w[ok] / n[ok])
    candidates = np.flatnonzero(ok)
    if len(candidates) > top_n:
        part = np.argpartition(score[candidates], -top_n)[-top_n:]
        candidates = candidates[part]
    order = candidates[np.argsort(-score[candidates], kind="stable")]
    return {
        "work_indices": [int(i) for i in order],
        "scores": [float(score[i]) for i in order],
        "support": [float(n[i]) for i in order],
        "n_rankable": int(ok.sum()),
        "weight_sum": float(weights.sum()),
        "kish": float(weights.sum() ** 2 / max(float(weights @ weights), 1e-12)),
    }


def jaccard(a: list[int], b: list[int], k: int) -> float:
    aa, bb = set(a[:k]), set(b[:k])
    return len(aa & bb) / max(len(aa | bb), 1)


def rbo(a: list[int], b: list[int], *, p: float = 0.98, depth: int = 500) -> float:
    """Finite extrapolated rank-biased overlap."""
    sa: set[int] = set()
    sb: set[int] = set()
    total = 0.0
    last_agreement = 0.0
    dmax = min(depth, max(len(a), len(b)))
    for d in range(1, dmax + 1):
        if d <= len(a):
            sa.add(a[d - 1])
        if d <= len(b):
            sb.add(b[d - 1])
        agreement = len(sa & sb) / d
        total += (1.0 - p) * (p ** (d - 1)) * agreement
        last_agreement = agreement
    return float(total + last_agreement * (p**dmax))


def normalized_cluster_weights(
    labels: np.ndarray,
    current_mask: np.ndarray,
    factors: np.ndarray,
) -> np.ndarray:
    w = np.zeros(len(labels), dtype=np.float64)
    w[current_mask] = factors[labels[current_mask]]
    target = float(current_mask.sum())
    if w.sum() > 0:
        w *= target / w.sum()
    return w


def run_universes(
    partitions,
    current_mask: np.ndarray,
    wins,
    losses,
    eligible,
):
    print("Running community perturbation universes…", flush=True)
    base_weights = current_mask.astype(np.float64)
    baseline = rank_weights(wins, losses, base_weights, eligible)
    universes: list[dict[str, Any]] = []
    community_universes: list[dict[str, Any]] = []
    rng = np.random.default_rng(20260805)

    for part in partitions:
        labels = part["labels"]
        k = part["k"]
        sizes = part["current_sizes"].astype(np.float64)

        # Equal total weight per nonempty community.
        equal_f = np.where(sizes > 0, 1.0 / np.maximum(sizes, 1.0), 0.0)
        eq_w = normalized_cluster_weights(labels, current_mask, equal_f)
        universes.append(
            {
                "label": f"{part['label']}:equal",
                "partition": part["label"],
                "kind": "equal_community",
                "ranking": rank_weights(wins, losses, eq_w, eligible),
            }
        )

        for c in range(k):
            # Community-only is descriptive; retain actual sample size.
            only_w = (current_mask & (labels == c)).astype(np.float64)
            community_universes.append(
                {
                    "label": f"{part['label']}:community{c}",
                    "partition": part["label"],
                    "kind": "community_only",
                    "cluster": c,
                    "ranking": rank_weights(wins, losses, only_w, eligible),
                }
            )

            loo_f = np.ones(k, dtype=np.float64)
            loo_f[c] = 0.0
            loo_w = normalized_cluster_weights(labels, current_mask, loo_f)
            universes.append(
                {
                    "label": f"{part['label']}:loo{c}",
                    "partition": part["label"],
                    "kind": "leave_one_out",
                    "cluster": c,
                    "ranking": rank_weights(wins, losses, loo_w, eligible),
                }
            )

        for r in range(RANDOM_REWEIGHTS):
            factors = np.exp(rng.uniform(math.log(0.5), math.log(2.0), size=k))
            rw = normalized_cluster_weights(labels, current_mask, factors)
            universes.append(
                {
                    "label": f"{part['label']}:random{r}",
                    "partition": part["label"],
                    "kind": "random_reweight",
                    "factors": [float(x) for x in factors],
                    "ranking": rank_weights(wins, losses, rw, eligible),
                }
            )

    base = baseline["work_indices"]
    for u in universes + community_universes:
        ranked = u["ranking"]["work_indices"]
        u["vs_baseline"] = {
            "jaccard50": jaccard(base, ranked, 50),
            "jaccard200": jaccard(base, ranked, 200),
            "rbo98": rbo(base, ranked, p=0.98),
        }
    print(
        f"  universes={len(universes)} community-only={len(community_universes)}",
        flush=True,
    )
    return baseline, universes, community_universes


def support_concentration(
    partitions,
    current_mask: np.ndarray,
    wins,
    losses,
    target_work_indices: list[int],
) -> dict[int, dict[str, float]]:
    """Normalized cluster concentration and fraction of communities with esteem.

    Raw HHI has a different floor for every k (1/k), so it cannot be averaged
    fairly across the 6-, 10-, and 16-community partitions.  Normalize each
    partition's HHI to 0 = perfectly even support and 1 = one-community support
    before aggregating across alternative partitions.
    """
    out: dict[int, dict[str, list[float]]] = {
        i: {"normalized_hhi": [], "supporting_fraction": []}
        for i in target_work_indices
    }
    win_sub = wins[:, target_work_indices]
    loss_sub = losses[:, target_work_indices]
    for part in partitions:
        labels = part["labels"]
        k = part["k"]
        indicator = sparse.csr_matrix(
            (
                np.ones(int(current_mask.sum()), dtype=np.float32),
                (
                    np.flatnonzero(current_mask),
                    labels[current_mask].astype(np.int32),
                ),
            ),
            shape=(len(labels), k),
        )
        cw = (indicator.T @ win_sub).toarray().T
        cl = (indicator.T @ loss_sub).toarray().T
        # Compare per-capita positive support. Without this adjustment an HHI
        # would call any book concentrated merely because one cluster contains
        # more jurors than another.
        community_sizes = np.maximum(part["current_sizes"].astype(float), 1.0)
        for j, work_idx in enumerate(target_work_indices):
            mass = cw[j] / community_sizes
            total = float(mass.sum())
            raw_hhi = float(((mass / total) ** 2).sum()) if total > 0 else 1.0
            normalized_hhi = (raw_hhi - 1.0 / k) / (1.0 - 1.0 / k)
            normalized_hhi = float(np.clip(normalized_hhi, 0.0, 1.0))
            support = cw[j] + cl[j]
            good = (support >= 20) & (cw[j] / np.maximum(support, 1e-9) > 0.5)
            out[work_idx]["normalized_hhi"].append(normalized_hhi)
            out[work_idx]["supporting_fraction"].append(float(good.mean()))
    return {
        i: {
            "support_hhi_normalized_mean": float(np.mean(v["normalized_hhi"])),
            "support_hhi_normalized_max": float(np.max(v["normalized_hhi"])),
            "supporting_community_fraction_mean": float(
                np.mean(v["supporting_fraction"])
            ),
        }
        for i, v in out.items()
    }


def analyze_books(
    baseline,
    universes,
    community_universes,
    partitions,
    current_mask,
    wins,
    losses,
    works,
):
    consensus_ranks = []
    for u in universes:
        consensus_ranks.append(
            {w: r + 1 for r, w in enumerate(u["ranking"]["work_indices"])}
        )
    community_ranks = [
        {w: r + 1 for r, w in enumerate(u["ranking"]["work_indices"])}
        for u in community_universes
    ]
    base_rank = {w: r + 1 for r, w in enumerate(baseline["work_indices"])}
    union = set(base_rank)
    for ranks in consensus_ranks:
        union.update(ranks)
    target = sorted(union)
    concentration = support_concentration(
        partitions, current_mask, wins, losses, baseline["work_indices"]
    )

    diagnostics = []
    missing_rank = TOP_SAVE + 1
    loo_indices = [i for i, u in enumerate(universes) if u["kind"] == "leave_one_out"]
    for idx in target:
        rs = np.asarray([r.get(idx, missing_rank) for r in consensus_ranks])
        crs = np.asarray([r.get(idx, missing_rank) for r in community_ranks])
        loo_rs = rs[loo_indices] if loo_indices else rs
        b = base_rank.get(idx, missing_rank)
        d = {
            **works[idx],
            "baseline_rank": None if b == missing_rank else int(b),
            "median_rank": float(np.median(rs)),
            "q10_rank": float(np.quantile(rs, 0.1)),
            "q90_rank": float(np.quantile(rs, 0.9)),
            "rank_sd": float(np.std(rs)),
            "top50_rate": float(np.mean(rs <= 50)),
            "top200_rate": float(np.mean(rs <= 200)),
            "top500_rate": float(np.mean(rs <= TOP_SAVE)),
            "community_top200_rate": float(np.mean(crs <= 200)),
            "max_loo_drop": float(np.max(loo_rs - b)) if b < missing_rank else None,
            **concentration.get(
                idx,
                {
                    "support_hhi_normalized_mean": None,
                    "support_hhi_normalized_max": None,
                    "supporting_community_fraction_mean": None,
                },
            ),
        }
        diagnostics.append(d)

    mixture_stable = sorted(
        [d for d in diagnostics if d["top200_rate"] >= MIXTURE_STABLE_RATE],
        key=lambda d: (d["median_rank"], -d["community_top200_rate"]),
    )
    # These are descriptive, predeclared pilot thresholds rather than a tuned
    # objective.  Keeping each axis visible prevents one stability number from
    # laundering a concentrated community preference into a global consensus.
    distributed_core = sorted(
        [
            d
            for d in mixture_stable
            if d["community_top200_rate"] >= DISTRIBUTED_COMMUNITY_RATE
            and d["support_hhi_normalized_mean"] <= MAX_NORMALIZED_CONCENTRATION
            and d["max_loo_drop"] is not None
            and d["max_loo_drop"] <= MAX_DISTRIBUTED_LOO_DROP
        ],
        key=lambda d: (d["median_rank"], -d["community_top200_rate"]),
    )
    distributed_ids = {d["work_id"] for d in distributed_core}
    community_dependent = sorted(
        [d for d in mixture_stable if d["work_id"] not in distributed_ids],
        key=lambda d: (
            -float(d["max_loo_drop"] or 0),
            -d["support_hhi_normalized_mean"],
            d["community_top200_rate"],
        ),
    )
    fragile_baseline = sorted(
        [
            d
            for d in diagnostics
            if d["baseline_rank"] is not None and d["baseline_rank"] <= 200
        ],
        key=lambda d: (d["top200_rate"], -float(d["max_loo_drop"] or 0)),
    )
    russian = sorted(
        [
            d
            for d in diagnostics
            if d["baseline_rank"] is not None
            and any(m in (d["author"] or "").lower() for m in RUSSIAN_AUTHOR_MARKERS)
        ],
        key=lambda d: d["baseline_rank"],
    )
    return (
        diagnostics,
        mixture_stable,
        distributed_core,
        community_dependent,
        fragile_baseline,
        russian,
    )


def summarize_universes(universes) -> dict[str, Any]:
    by_kind: dict[str, list[dict[str, float]]] = defaultdict(list)
    for u in universes:
        by_kind[u["kind"]].append(u["vs_baseline"])
    out = {}
    for kind, rows in by_kind.items():
        out[kind] = {"n": len(rows)} | {
            key: {
                "mean": float(np.mean([r[key] for r in rows])),
                "min": float(np.min([r[key] for r in rows])),
                "q10": float(np.quantile([r[key] for r in rows], 0.1)),
            }
            for key in ("jaccard50", "jaccard200", "rbo98")
        }
    return out


def partition_summaries(partitions, community_universes, works):
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for u in community_universes:
        by_label[u["partition"]].append(u)
    out = []
    for p in partitions:
        # Keep one seed per resolution in the human report; JSON retains all summaries.
        communities = []
        for u in sorted(by_label[p["label"]], key=lambda z: z["cluster"]):
            top = [works[i] for i in u["ranking"]["work_indices"][:5]]
            communities.append(
                {
                    "cluster": int(u["cluster"]),
                    "broad_n": int(p["broad_sizes"][u["cluster"]]),
                    "current_n": int(p["current_sizes"][u["cluster"]]),
                    "top5": [
                        {"title": x["title"], "author": x["author"]} for x in top
                    ],
                }
            )
        out.append(
            {
                "label": p["label"],
                "k": int(p["k"]),
                "seed": int(p["seed"]),
                "cosine_inertia": float(p["cosine_inertia"]),
                "communities": communities,
            }
        )
    return out


def slim_universe(u: dict[str, Any]) -> dict[str, Any]:
    return {
        k: v for k, v in u.items() if k != "ranking"
    } | {
        "top_work_indices": u["ranking"]["work_indices"],
        "n_rankable": u["ranking"]["n_rankable"],
        "kish": u["ranking"]["kish"],
    }


def fmt_book(d: dict[str, Any]) -> str:
    return f"{d['title']} — {d['author']}"


def write_report(results: dict[str, Any]) -> None:
    summary = results["universe_summary"]
    lines = [
        "# Focused pilot: community-robust literary consensus",
        "",
        "## Question",
        "",
        "Does the rebuilt jury contain a shared canonical core, or does its head depend on "
        "particular latent reader communities? Clusters are used only to perturb and audit "
        "the ranking—not to nominate books.",
        "",
        "## Design",
        "",
        f"- Current rich behavioral jury: **{JURY_N:,}** users; embedding pool: **{BROAD_N:,}**.",
        f"- User embedding: centered rating residuals over "
        f"**{results['embedding']['n_items']:,}** books, truncated to "
        f"{results['embedding']['embedding_dim']} dimensions.",
        f"- Partitions: k={list(CLUSTER_COUNTS)} × seeds={list(CLUSTER_SEEDS)} "
        f"= **{len(results['partitions'])}** alternatives.",
        f"- Universes: **{results['meta']['n_consensus_universes']}** balanced/leave-one-out/"
        f"random reweightings plus **{results['meta']['n_community_universes']}** "
        "community-only diagnostics.",
        "- Ranking: fixed within-user 5★ versus ≤3★ pair samples; user reweighting changes "
        "only precomputed sufficient statistics.",
        "",
        "## Perturbation stability",
        "",
        "| perturbation | n | mean J@50 | worst J@50 | mean J@200 | worst J@200 | mean RBO |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for kind in ("equal_community", "leave_one_out", "random_reweight"):
        s = summary[kind]
        lines.append(
            f"| {kind} | {s['n']} | {s['jaccard50']['mean']:.3f} | "
            f"{s['jaccard50']['min']:.3f} | {s['jaccard200']['mean']:.3f} | "
            f"{s['jaccard200']['min']:.3f} | {s['rbo98']['mean']:.3f} |"
        )

    lines += [
        "",
        "## Pilot result",
        "",
        f"- **{len(results['mixture_stable_core'])}** books are mixture-stable: they remain "
        f"top-200 in at least {100*MIXTURE_STABLE_RATE:.0f}% of perturbations.",
        f"- **{len(results['distributed_core'])}** of those meet all stricter "
        "cross-community tests.",
        f"- The other **{len(results['community_dependent_stable'])}** are stable for the "
        "current jury mixture but retain a detectable taste-community dependency.",
        "- This supports a compact shared core followed by contested tiers, rather than a "
        "single defensible total order extending far down the list.",
        "",
        "## Distributed robust core",
        "",
        f"A deliberately stricter tier: top-200 in at least "
        f"{100*MIXTURE_STABLE_RATE:.0f}% of mixture perturbations, top-200 in at least "
        f"{100*DISTRIBUTED_COMMUNITY_RATE:.0f}% of community-only rankings, normalized "
        f"support concentration no more than {MAX_NORMALIZED_CONCENTRATION:.2f}, and worst "
        f"observed leave-one-community-out drop no more than {MAX_DISTRIBUTED_LOO_DROP} "
        "places. These thresholds are descriptive and were not "
        "optimized against a probe list.",
        "",
        "| book | base | median | top200 | community top200 | norm. concentration | worst LOO drop* |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for d in results["distributed_core"][:40]:
        lines.append(
            f"| {fmt_book(d)} | {d['baseline_rank'] or '—'} | {d['median_rank']:.0f} | "
            f"{100*d['top200_rate']:.0f}% | {100*d['community_top200_rate']:.0f}% | "
            f"{d['support_hhi_normalized_mean']:.3f} | "
            f"{d['max_loo_drop'] if d['max_loo_drop'] is not None else '—'} |"
        )

    lines += [
        "",
        "## Mixture-stable but community-dependent",
        "",
        "These books survive at least 80% of mixture perturbations but fail one or more "
        "distributed-core tests. They are the main candidates for taste-community bias, "
        "not books to delete automatically.",
        "",
        "| book | base | median | top200 | community top200 | norm. concentration | worst LOO drop* |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for d in results["community_dependent_stable"][:35]:
        lines.append(
            f"| {fmt_book(d)} | {d['baseline_rank'] or '—'} | {d['median_rank']:.0f} | "
            f"{100*d['top200_rate']:.0f}% | {100*d['community_top200_rate']:.0f}% | "
            f"{d['support_hhi_normalized_mean']:.3f} | "
            f"{d['max_loo_drop'] if d['max_loo_drop'] is not None else '—'} |"
        )

    lines += [
        "",
        "## Fragile books from the baseline top 200",
        "",
        "| book | base | top200 | median | q90 | community top200 | max LOO drop |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for d in results["fragile_baseline"][:35]:
        lines.append(
            f"| {fmt_book(d)} | {d['baseline_rank']} | {100*d['top200_rate']:.0f}% | "
            f"{d['median_rank']:.0f} | {d['q90_rank']:.0f} | "
            f"{100*d['community_top200_rate']:.0f}% | {d['max_loo_drop']:.0f} |"
        )

    lines += [
        "",
        "## Russian-literature dependence check",
        "",
        "Author-name diagnostic only; it never enters ranking or clustering.",
        "",
        "| book | base | median | top200 | community top200 | norm. concentration | worst LOO drop* |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for d in results["russian_diagnostics"][:40]:
        lines.append(
            f"| {fmt_book(d)} | {d['baseline_rank']} | {d['median_rank']:.0f} | "
            f"{100*d['top200_rate']:.0f}% | {100*d['community_top200_rate']:.0f}% | "
            f"{d['support_hhi_normalized_mean']:.3f} | {d['max_loo_drop']:.0f} |"
        )

    lines += [
        "",
        "## Example community heads",
        "",
        "One seed at each resolution is shown to interpret—not endorse—the partitions.",
    ]
    for p in results["partitions"]:
        if p["seed"] != CLUSTER_SEEDS[0]:
            continue
        lines += ["", f"### {p['label']}", ""]
        for c in p["communities"]:
            head = "; ".join(f"{x['title']} — {x['author']}" for x in c["top5"][:3])
            lines.append(
                f"- C{c['cluster']} (current n={c['current_n']}): {head}"
            )

    lines += [
        "",
        "## Interpretation guardrails",
        "",
        "- Normalized concentration uses per-capita positive support: 0 means perfectly "
        "even community support and 1 means support confined to one community. Normalization "
        "makes different k values comparable.",
        f"- *Rankings retain only their top {TOP_SAVE}. A worst LOO drop ending at rank "
        f"{TOP_SAVE + 1} therefore means the book fell outside the saved ranking; the "
        "reported drop is a censored lower bound, not its exact final rank.",
        "- Random resampling tests variance; community perturbations test mixture dependence. "
        "Neither proves objective literary value.",
        "- A dense local canon can be perfectly stable inside one community. It belongs in "
        "the global core only if support is distributed and leave-one-out movement is small.",
        "- Goodreads exposure is still missing-not-at-random. Cross-community rank stability "
        "cannot repair books that communities never jointly encounter.",
        "- The honest result may be a small shared core followed by contested tiers rather "
        "than one precise total order.",
        "",
        "## Recommendation",
        "",
        results["recommendation"],
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    t_all = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    # Parallel floating-point aggregates can differ in their final few bits,
    # which is enough to swap a few users at the broad-pool cutoff.  Rebuild
    # the cohort deterministically, then restore parallelism for matrix work.
    con.execute("PRAGMA threads=1")

    jury_meta, all_ids, all_scores, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, current_mask, _user_index = materialize_pilot_users(
        con, all_ids, all_scores, broad
    )
    emb, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(emb, current_mask)
    wins, losses, works, eligible, pair_meta = build_pair_matrices(con, len(broad_ids))
    baseline, universes, community_universes = run_universes(
        partitions, current_mask, wins, losses, eligible
    )
    (
        diagnostics,
        mixture_stable,
        distributed_core,
        community_dependent,
        fragile,
        russian,
    ) = analyze_books(
        baseline,
        universes,
        community_universes,
        partitions,
        current_mask,
        wins,
        losses,
        works,
    )
    universe_summary = summarize_universes(universes)
    p_summary = partition_summaries(partitions, community_universes, works)

    # Interpret using structural thresholds only; no probe pile enters this decision.
    loo = universe_summary["leave_one_out"]
    if loo["jaccard200"]["mean"] >= 0.65 and len(distributed_core) >= 50:
        recommendation = (
            "The pilot supports a broad cross-community core. Proceed to a larger "
            "jury/specification multiverse, using community support concentration and "
            "leave-one-out stability as separate axes rather than optimizing a single score."
        )
    elif loo["jaccard200"]["mean"] >= 0.65 and len(distributed_core) >= 20:
        recommendation = (
            "The pilot supports a small cross-community core, but not one broad total "
            "consensus. Proceed to the larger jury/specification multiverse while preserving "
            "the distinction between robust-core and community-dependent/contested tiers."
        )
    else:
        recommendation = (
            "The pilot does not yet support a broad single consensus. Treat the stable books "
            "as a provisional core and present the remainder as community-specific or "
            "contested tiers before expanding the multiverse."
        )

    results = {
        "meta": {
            "purpose": "community perturbation pilot; clusters audit rather than nominate",
            "jury_n": JURY_N,
            "broad_n": BROAD_N,
            "cluster_counts": list(CLUSTER_COUNTS),
            "cluster_seeds": list(CLUSTER_SEEDS),
            "random_reweights_per_partition": RANDOM_REWEIGHTS,
            "classification_thresholds": {
                "mixture_top200_rate": MIXTURE_STABLE_RATE,
                "community_top200_rate": DISTRIBUTED_COMMUNITY_RATE,
                "max_normalized_support_concentration": MAX_NORMALIZED_CONCENTRATION,
                "max_leave_one_out_drop": MAX_DISTRIBUTED_LOO_DROP,
            },
            "n_consensus_universes": len(universes),
            "n_community_universes": len(community_universes),
            "runtime_seconds": time.time() - t_all,
        },
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "pair_matrix": pair_meta,
        "baseline": {
            "top": [
                {**works[i], "rank": r + 1, "score": baseline["scores"][r]}
                for r, i in enumerate(baseline["work_indices"][:100])
            ],
            "n_rankable": baseline["n_rankable"],
        },
        "universe_summary": universe_summary,
        "partitions": p_summary,
        "universes": [slim_universe(u) for u in universes],
        "community_universes": [slim_universe(u) for u in community_universes],
        "mixture_stable_core": mixture_stable[:300],
        "distributed_core": distributed_core[:300],
        "community_dependent_stable": community_dependent[:300],
        "fragile_baseline": fragile[:200],
        "russian_diagnostics": russian[:100],
        "book_diagnostics": sorted(
            diagnostics,
            key=lambda d: (d["median_rank"], -d["top200_rate"]),
        )[:2000],
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

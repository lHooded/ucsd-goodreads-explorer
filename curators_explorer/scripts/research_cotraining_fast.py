#!/usr/bin/env python3
"""Memory-safe fast co-training for ~16GB machines.

Avoids multi-process copies of huge matrices (that blew swap). Instead:
1) One compact sparse ratings matrix (capped pool).
2) Many rough weight nudges in a **single process** (still fast).
3) One bootstrap stability check at the end (same process).

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_cotraining_fast
"""

from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

from curators_explorer.scripts.research_feature_sensitivity import (
    ANTI_TERMS,
    CLASSIC_TERMS,
    NORMIE_TERMS,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    materialize_base,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    FEATURE_COLS,
    build_user_features,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "cotraining_fast.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "COTRAINING_FAST_REPORT.md"
STABILITY_JSON = Path(__file__).resolve().parents[1] / "data" / "stability_analysis.json"
WEIGHTS_OUT = Path(__file__).resolve().parents[1] / "data" / "cotrained_weights_fast.json"

# Memory knobs (16GB-safe; matrix stays well under ~1GB)
MAX_STICKY_LIKERS = 25_000
MAX_FOCUS_POOL = 50_000
MAX_ANTI_POOL = 30_000
MAX_EDGES_PER_USER = 220
N_ROUNDS = 10
CANDIDATES_PER_ROUND = 16
FINAL_BOOTS = 20
TOP_FRAC = 0.06
LAM_A = 0.85
LAM_N = 0.75
STEP_SCALE = 0.12
SEED = 11

CLASSIC_KEYS = list(CLASSIC_TERMS.keys())
ANTI_KEYS = list(ANTI_TERMS.keys())
NORMIE_KEYS = list(NORMIE_TERMS.keys())
GATE_KEYS = ("series_gate", "mega_gate", "binge_gate", "span_gate")


def _load_start_weights() -> dict[str, Any]:
    p = Path(__file__).resolve().parents[1] / "data" / "cotrained_weights.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "classic_terms": dict(CLASSIC_TERMS),
        "anti_terms": dict(ANTI_TERMS),
        "normie_terms": dict(NORMIE_TERMS),
        "gates": {
            "series_gate": 0.40,
            "mega_gate": 0.28,
            "binge_gate": 2.8,
            "span_gate": 3.0,
        },
        "lambda_anti": LAM_A,
        "lambda_normie": LAM_N,
        "top_frac": TOP_FRAC,
    }


def _load_sticky() -> list[str]:
    d = json.loads(STABILITY_JSON.read_text(encoding="utf-8"))
    return [e["work_id"] for e in d["sticky_baseline_top50"] if e["in_top50_rate"] >= 0.8]


def weights_to_vectors(w: dict[str, Any]) -> dict[str, Any]:
    return {
        "classic": {k: float(w["classic_terms"].get(k, 0.0)) for k in CLASSIC_KEYS},
        "anti": {k: float(w["anti_terms"].get(k, 0.0)) for k in ANTI_KEYS},
        "normie": {k: float(w["normie_terms"].get(k, 0.0)) for k in NORMIE_KEYS},
        "gates": {k: float(w["gates"][k]) for k in GATE_KEYS},
        "lam_a": float(w.get("lambda_anti", LAM_A)),
        "lam_n": float(w.get("lambda_normie", LAM_N)),
        "top_frac": float(w.get("top_frac", TOP_FRAC)),
    }


def vectors_to_save(wv: dict[str, Any]) -> dict[str, Any]:
    return {
        "classic_terms": wv["classic"],
        "anti_terms": wv["anti"],
        "normie_terms": wv["normie"],
        "gates": wv["gates"],
        "lambda_anti": wv["lam_a"],
        "lambda_normie": wv["lam_n"],
        "top_frac": wv["top_frac"],
    }


def build_compact(con) -> dict[str, Any]:
    """Compact pool that still keeps sticky-likers (matrix stays <<1GB)."""
    print("Building compact feature/rating bundle…", flush=True)
    t0 = time.time()
    sticky = _load_sticky()

    moments = {}
    for c in FEATURE_COLS:
        mu, sd = con.execute(
            f"SELECT avg({c}), stddev_samp({c}) FROM user_rich WHERE {c} IS NOT NULL"
        ).fetchone()
        moments[c] = (float(mu or 0), float(sd or 1) or 1.0)

    feat_select = f"""
        SELECT user_id, {", ".join(FEATURE_COLS)},
               series_share_5, mega_catalog_share_5, binge_mean_5, midpop_span_per_logn5
        FROM user_rich
    """

    # Always seed pool with people who 5★ several sticky classics
    con.execute("CREATE OR REPLACE TABLE sticky_works (work_id VARCHAR)")
    con.executemany("INSERT INTO sticky_works VALUES (?)", [(w,) for w in sticky])
    sticky_liker_ids = [
        int(r[0])
        for r in con.execute(
            f"""
            SELECT e.user_id
            FROM ex.all_rating_events e
            JOIN sticky_works s USING (work_id)
            JOIN user_rich u USING (user_id)
            WHERE e.rating = 5
            GROUP BY e.user_id
            HAVING count(DISTINCT e.work_id) >= 2
            ORDER BY count(DISTINCT e.work_id) DESC
            LIMIT {MAX_STICKY_LIKERS}
            """
        ).fetchall()
    ]
    print(f"  sticky-likers={len(sticky_liker_ids):,}", flush=True)

    # Fetch their feature rows
    con.execute("CREATE OR REPLACE TABLE pool_seed (user_id BIGINT)")
    con.executemany("INSERT INTO pool_seed VALUES (?)", [(u,) for u in sticky_liker_ids])
    sticky_rows = con.execute(
        f"{feat_select} WHERE user_id IN (SELECT user_id FROM pool_seed)"
    ).fetchall()

    focus_rows = con.execute(
        f"""
        {feat_select}
        WHERE series_share_5 <= 0.42
          AND mega_catalog_share_5 <= 0.32
          AND binge_mean_5 <= 3.0
          AND midpop_span_per_logn5 >= 2.5
        ORDER BY midpop_span_per_logn5 DESC
        LIMIT {MAX_FOCUS_POOL}
        """
    ).fetchall()
    anti_rows = con.execute(
        f"""
        {feat_select}
        WHERE series_share_5 >= 0.50 OR binge_mean_5 >= 2.4
        ORDER BY series_share_5 DESC, binge_mean_5 DESC
        LIMIT {MAX_ANTI_POOL}
        """
    ).fetchall()

    # sticky likers first, then focus, then anti
    seen: dict[int, int] = {}
    raw_rows: list[tuple] = []
    for rows in (sticky_rows, focus_rows, anti_rows):
        for r in rows:
            uid = int(r[0])
            if uid in seen:
                continue
            seen[uid] = len(raw_rows)
            raw_rows.append(r)

    n = len(raw_rows)
    Fdim = len(FEATURE_COLS)
    X = np.zeros((n, Fdim), dtype=np.float32)
    for j, c in enumerate(FEATURE_COLS):
        mu, sd = moments[c]
        for i, r in enumerate(raw_rows):
            v = r[1 + j]
            X[i, j] = (float(v if v is not None else mu) - mu) / sd
    series = np.array([float(r[1 + Fdim] or 0) for r in raw_rows], dtype=np.float32)
    mega = np.array([float(r[2 + Fdim] or 0) for r in raw_rows], dtype=np.float32)
    binge = np.array([float(r[3 + Fdim] or 0) for r in raw_rows], dtype=np.float32)
    span = np.array([float(r[4 + Fdim] or 0) for r in raw_rows], dtype=np.float32)
    user_ids = np.array([int(r[0]) for r in raw_rows], dtype=np.int64)
    uid_to_row = {int(u): i for i, u in enumerate(user_ids)}
    feat_index = {c: j for j, c in enumerate(FEATURE_COLS)}
    print(
        f"  pooled users={n:,} (sticky+focus≤{MAX_FOCUS_POOL}+anti≤{MAX_ANTI_POOL})",
        flush=True,
    )

    con.execute("CREATE OR REPLACE TABLE pool_users (user_id BIGINT)")
    con.executemany("INSERT INTO pool_users VALUES (?)", [(int(u),) for u in user_ids])

    # Cap edges, but prefer sticky + mid-pop over mega-hits (old ORDER BY n DESC
    # was dropping classics out of the top-80).
    edges = con.execute(
        f"""
        WITH ranked AS (
            SELECT
                e.user_id,
                e.work_id,
                (e.rating = 5)::BOOLEAN AS is5,
                wa.is_seriesish,
                row_number() OVER (
                    PARTITION BY e.user_id
                    ORDER BY e.rating DESC,
                      (s.work_id IS NOT NULL) DESC,
                      (wr.n BETWEEN 400 AND 40000) DESC,
                      abs(ln(wr.n + 1.0) - ln(8000.0))
                ) AS rn
            FROM ex.all_rating_events e
            JOIN pool_users p USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            JOIN work_ax wa ON wa.work_id = e.work_id
            LEFT JOIN sticky_works s ON s.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= 80000
        )
        SELECT user_id, work_id, is5, is_seriesish
        FROM ranked
        WHERE rn <= {MAX_EDGES_PER_USER}
        """
    ).fetchall()
    print(f"  edges={len(edges):,}", flush=True)

    work_ids = sorted({str(w) for _u, w, _i, _s in edges})
    work_index = {w: j for j, w in enumerate(work_ids)}
    W = len(work_ids)

    rr, cc, dd_r = [], [], []
    rr5, cc5 = [], []
    series_cols = set()
    for uid, wid, is5, is_ser in edges:
        r = uid_to_row.get(int(uid))
        c = work_index.get(str(wid))
        if r is None or c is None:
            continue
        rr.append(r)
        cc.append(c)
        dd_r.append(1.0)
        if is5:
            rr5.append(r)
            cc5.append(c)
        if is_ser:
            series_cols.add(c)

    R = sparse.csr_matrix(
        (np.array(dd_r, dtype=np.float32), (rr, cc)), shape=(n, W), dtype=np.float32
    )
    F = sparse.csr_matrix(
        (np.ones(len(rr5), dtype=np.float32), (rr5, cc5)), shape=(n, W), dtype=np.float32
    )
    # free edge lists
    del edges, rr, cc, dd_r, rr5, cc5

    sticky_cols = np.array([work_index[w] for w in sticky if w in work_index], dtype=np.int32)
    anti_ids = {
        str(r[0])
        for r in con.execute(
            "SELECT work_id FROM ex.taste_signal_works WHERE side='non_literary'"
        ).fetchall()
    }
    anti_cols = np.array(
        [work_index[w] for w in anti_ids if w in work_index], dtype=np.int32
    )
    series_cols_arr = np.array(sorted(series_cols), dtype=np.int32)

    # soft pos/neg rows
    con.execute("CREATE OR REPLACE TABLE soft_pos_works (work_id VARCHAR)")
    con.executemany("INSERT INTO soft_pos_works VALUES (?)", [(w,) for w in sticky])
    soft_pos = con.execute(
        """
        SELECT e.user_id FROM ex.all_rating_events e
        JOIN soft_pos_works s USING (work_id)
        JOIN pool_users p USING (user_id)
        WHERE e.rating = 5
        GROUP BY e.user_id HAVING count(DISTINCT e.work_id) >= 3
        """
    ).fetchall()
    soft_pos_rows = np.array(
        [uid_to_row[int(u)] for (u,) in soft_pos if int(u) in uid_to_row], dtype=np.int32
    )
    soft_neg_rows = np.where((series >= 0.55) & (binge >= 2.2))[0].astype(np.int32)

    nbytes = R.data.nbytes + R.indices.nbytes + R.indptr.nbytes
    nbytes += F.data.nbytes + F.indices.nbytes + F.indptr.nbytes
    nbytes += X.nbytes
    print(
        f"  works={W:,} sticky={len(sticky_cols)} matrix≈{nbytes/1e6:.0f}MB "
        f"({time.time()-t0:.1f}s)",
        flush=True,
    )

    return {
        "X": X,
        "feat_index": feat_index,
        "series": series,
        "mega": mega,
        "binge": binge,
        "span": span,
        "R": R,
        "F": F,
        "work_ids": work_ids,
        "sticky_cols": sticky_cols,
        "anti_cols": anti_cols,
        "series_cols": series_cols_arr,
        "soft_pos_rows": soft_pos_rows,
        "soft_neg_rows": soft_neg_rows,
        "user_ids": user_ids,
    }


def affinity_and_masks(b: dict[str, Any], wv: dict[str, Any]):
    fi = b["feat_index"]
    X = b["X"]
    classic = np.zeros(X.shape[0], dtype=np.float32)
    anti = np.zeros(X.shape[0], dtype=np.float32)
    normie = np.zeros(X.shape[0], dtype=np.float32)
    for k, coef in wv["classic"].items():
        classic += np.float32(coef) * X[:, fi[k]]
    for k, coef in wv["anti"].items():
        anti += np.float32(coef) * X[:, fi[k]]
    for k, coef in wv["normie"].items():
        normie += np.float32(coef) * X[:, fi[k]]
    focus = classic - np.float32(wv["lam_a"]) * anti - np.float32(wv["lam_n"]) * normie
    g = wv["gates"]
    gated = (
        (b["series"] <= g["series_gate"])
        & (b["mega"] <= g["mega_gate"])
        & (b["binge"] <= g["binge_gate"])
        & (b["span"] >= g["span_gate"])
    )
    anti_like = (b["series"] >= 0.45) | (b["binge"] >= 2.5)
    return focus, anti, gated, anti_like


def top_frac_mask(scores: np.ndarray, eligible: np.ndarray, frac: float) -> np.ndarray:
    idx = np.flatnonzero(eligible)
    if len(idx) == 0:
        return np.zeros(len(scores), dtype=bool)
    k = max(int(len(idx) * frac), 40)
    sub = scores[idx]
    if k >= len(idx):
        chosen = idx
    else:
        chosen = idx[np.argpartition(-sub, k)[:k]]
    m = np.zeros(len(scores), dtype=bool)
    m[chosen] = True
    return m


def contrastive_scores(b: dict[str, Any], focus_m: np.ndarray, anti_m: np.ndarray) -> np.ndarray:
    wf = focus_m.astype(np.float32)
    wa = anti_m.astype(np.float32)
    n_c = wf @ b["R"]
    n5_c = wf @ b["F"]
    n_a = wa @ b["R"]
    n5_a = wa @ b["F"]
    p5_c = np.divide(n5_c, n_c, out=np.zeros_like(n5_c), where=n_c >= 25)
    p5_a = np.divide(n5_a, n_a, out=np.zeros_like(n5_a), where=n_a >= 25)
    p5_a = np.where(n_a < 25, p5_c * np.float32(0.85), p5_a)
    score = p5_c - p5_a
    score = np.where(n_c >= 25, score, np.float32(-1e9))
    return score


def proxy_eval(b: dict[str, Any], wv: dict[str, Any]) -> dict[str, Any]:
    focus_s, anti_s, gated, anti_like = affinity_and_masks(b, wv)
    if int(gated.sum()) < 150:
        return {"ok": False, "proxy": -1e9, "reason": "gated_small"}
    focus_m = top_frac_mask(focus_s, gated, wv["top_frac"])
    anti_m = top_frac_mask(anti_s, anti_like, wv["top_frac"])
    if int(focus_m.sum()) < 80 or int(anti_m.sum()) < 80:
        return {"ok": False, "proxy": -1e9, "reason": "cohort_small"}
    scores = contrastive_scores(b, focus_m, anti_m)
    order = np.argsort(-scores)
    top50 = order[:50]
    top20 = order[:20]
    top50_set = set(int(x) for x in top50)
    sticky_in_50 = int(sum(1 for c in b["sticky_cols"] if int(c) in top50_set))
    anti50 = int(sum(1 for c in b["anti_cols"] if int(c) in top50_set))
    series20 = int(sum(1 for c in b["series_cols"] if int(c) in set(int(x) for x in top20)))
    rank_of = {int(w): i + 1 for i, w in enumerate(order[:2500])}
    sticky_ranks = [rank_of.get(int(c), 5000) for c in b["sticky_cols"]]
    mean_sticky_rank = float(np.mean(sticky_ranks)) if sticky_ranks else 9999.0
    sep = 0.0
    if len(b["soft_pos_rows"]) and len(b["soft_neg_rows"]):
        sep = float(focus_s[b["soft_pos_rows"]].mean() - focus_s[b["soft_neg_rows"]].mean())
    proxy = (
        3.0 * sticky_in_50
        - 8.0 * anti50
        - 2.0 * series20
        - 0.01 * mean_sticky_rank
        + 0.5 * sep
    )
    return {
        "ok": True,
        "proxy": proxy,
        "sticky_in_50": sticky_in_50,
        "mean_sticky_rank": mean_sticky_rank,
        "anti50": anti50,
        "series20": series20,
        "sep": sep,
        "n_gated": int(gated.sum()),
        "n_focus": int(focus_m.sum()),
        "top15_idx": [int(i) for i in order[:15]],
        "top50_idx": [int(i) for i in top50],
        "top200_idx": [int(i) for i in order[:200]],
    }


def perturb(wv: dict[str, Any], rng: random.Random, scale: float = STEP_SCALE) -> dict[str, Any]:
    out = {
        "classic": dict(wv["classic"]),
        "anti": dict(wv["anti"]),
        "normie": dict(wv["normie"]),
        "gates": dict(wv["gates"]),
        "lam_a": wv["lam_a"],
        "lam_n": wv["lam_n"],
        "top_frac": wv["top_frac"],
    }
    for block in ("classic", "anti", "normie"):
        for k in out[block]:
            out[block][k] = float(np.clip(out[block][k] + rng.uniform(-scale, scale), -2.5, 2.5))
    out["gates"]["series_gate"] = float(
        np.clip(out["gates"]["series_gate"] + rng.uniform(-0.03, 0.03), 0.18, 0.50)
    )
    out["gates"]["mega_gate"] = float(
        np.clip(out["gates"]["mega_gate"] + rng.uniform(-0.02, 0.02), 0.16, 0.36)
    )
    out["gates"]["binge_gate"] = float(
        np.clip(out["gates"]["binge_gate"] + rng.uniform(-0.12, 0.12), 1.6, 3.2)
    )
    out["gates"]["span_gate"] = float(
        np.clip(out["gates"]["span_gate"] + rng.uniform(-0.25, 0.25), 2.2, 5.5)
    )
    out["lam_a"] = float(np.clip(out["lam_a"] + rng.uniform(-0.08, 0.08), 0.4, 1.8))
    out["lam_n"] = float(np.clip(out["lam_n"] + rng.uniform(-0.08, 0.08), 0.25, 1.4))
    out["top_frac"] = float(np.clip(out["top_frac"] + rng.uniform(-0.01, 0.01), 0.03, 0.10))
    return out


def bootstrap_stability(b: dict[str, Any], wv: dict[str, Any], *, n_boot: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    base = proxy_eval(b, wv)
    if not base.get("ok"):
        return {"ok": False, "base": base}
    base50 = set(base["top50_idx"])
    base200 = set(base["top200_idx"])
    focus_s, anti_s, gated, anti_like = affinity_and_masks(b, wv)
    g_idx = np.flatnonzero(gated)
    a_idx = np.flatnonzero(anti_like)
    j50s, j200s, antis, stickies = [], [], [], []
    for _ in range(n_boot):
        g_samp = np.unique(rng.choice(g_idx, size=len(g_idx), replace=True))
        a_samp = np.unique(rng.choice(a_idx, size=len(a_idx), replace=True))
        k_g = max(int(len(g_idx) * wv["top_frac"]), 40)
        k_a = max(int(len(a_idx) * wv["top_frac"]), 40)
        g_ord = g_samp[np.argsort(-focus_s[g_samp])][:k_g]
        a_ord = a_samp[np.argsort(-anti_s[a_samp])][:k_a]
        focus_m = np.zeros(len(focus_s), dtype=bool)
        anti_m = np.zeros(len(anti_s), dtype=bool)
        focus_m[g_ord] = True
        anti_m[a_ord] = True
        scores = contrastive_scores(b, focus_m, anti_m)
        order = np.argsort(-scores)
        t50 = set(int(i) for i in order[:50])
        t200 = set(int(i) for i in order[:200])
        j50s.append(len(base50 & t50) / max(len(base50 | t50), 1))
        j200s.append(len(base200 & t200) / max(len(base200 | t200), 1))
        antis.append(sum(1 for c in b["anti_cols"] if int(c) in t50))
        stickies.append(
            sum(1 for c in b["sticky_cols"] if int(c) in t50) / max(len(b["sticky_cols"]), 1)
        )
    return {
        "ok": True,
        "j50_mean": float(np.mean(j50s)),
        "j50_sd": float(np.std(j50s)),
        "j200_mean": float(np.mean(j200s)),
        "anti50_mean": float(np.mean(antis)),
        "sticky_frac_mean": float(np.mean(stickies)),
        "base": base,
    }


def main() -> None:
    t_all = time.time()
    con = _con()
    print("One-time DuckDB setup…", flush=True)
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    label_cohorts(con)
    b = build_compact(con)

    con.close()

    start = _load_start_weights()
    current = weights_to_vectors(start)
    best = current
    best_met = proxy_eval(b, current)
    print(
        f"Start proxy={best_met['proxy']:.2f} sticky50={best_met['sticky_in_50']} "
        f"anti50={best_met['anti50']} gated={best_met.get('n_gated')}",
        flush=True,
    )
    history = [{"round": 0, "proxy": best_met["proxy"], **{k: best_met[k] for k in ('sticky_in_50','anti50','series20','mean_sticky_rank')}}]
    rng = random.Random(SEED)

    print(
        f"\nRough search (single process): {N_ROUNDS} rounds × {CANDIDATES_PER_ROUND} nudges",
        flush=True,
    )
    for rnd in range(1, N_ROUNDS + 1):
        t_r = time.time()
        cands = [best] + [perturb(best, rng) for _ in range(CANDIDATES_PER_ROUND - 1)]
        scored = []
        for wv in cands:
            met = proxy_eval(b, wv)
            # Soft veto only: never adopt worse anti than current best+1
            if met.get("ok") and met.get("anti50", 99) <= max(1, best_met.get("anti50", 0) + 1):
                scored.append((met["proxy"], wv, met))
        if not scored:
            scored = [(best_met["proxy"], best, best_met)]
        scored.sort(key=lambda t: -t[0])
        _, win_w, win_m = scored[0]
        improved = win_m["proxy"] > best_met["proxy"] + 0.05
        if improved:
            best, best_met = win_w, win_m
        history.append(
            {
                "round": rnd,
                "best_proxy": best_met["proxy"],
                "improved": improved,
                "sticky_in_50": best_met["sticky_in_50"],
                "anti50": best_met["anti50"],
                "series20": best_met["series20"],
                "mean_sticky_rank": best_met["mean_sticky_rank"],
                "elapsed_s": time.time() - t_r,
            }
        )
        print(
            f"  round {rnd}/{N_ROUNDS}: best_proxy={best_met['proxy']:.2f} "
            f"sticky50={best_met['sticky_in_50']} anti50={best_met['anti50']} "
            f"({time.time()-t_r:.1f}s)",
            flush=True,
        )

    print("\nFinal stability…", flush=True)
    stab0 = bootstrap_stability(b, current, n_boot=FINAL_BOOTS, seed=1)
    stab1 = bootstrap_stability(b, best, n_boot=FINAL_BOOTS, seed=1)
    print(
        f"  start J50={stab0['j50_mean']:.2f} anti≈{stab0['anti50_mean']:.2f}",
        flush=True,
    )
    print(
        f"  best  J50={stab1['j50_mean']:.2f} anti≈{stab1['anti50_mean']:.2f}",
        flush=True,
    )

    accept = True
    reasons = []
    if stab1["anti50_mean"] > stab0["anti50_mean"] + 0.5:
        accept = False
        reasons.append("anti50 worsened")
    if stab1["j50_mean"] < stab0["j50_mean"] - 0.04:
        accept = False
        reasons.append("J50 stability dropped")
    if best_met.get("anti50", 0) > 1:
        accept = False
        reasons.append("point anti50>1")
    if accept:
        reasons.append("accepted: proxies OK, stability OK, anti controlled")

    adopted = best if accept else current
    adopted_met = best_met if accept else proxy_eval(b, current)
    if accept:
        WEIGHTS_OUT.write_text(
            json.dumps(vectors_to_save(adopted), indent=2) + "\n", encoding="utf-8"
        )

    # Resolve top15 titles via fresh tiny duckdb connect
    con = _con()
    top15 = []
    for rank, idx in enumerate(adopted_met["top15_idx"], 1):
        wid = b["work_ids"][idx]
        row = con.execute(
            "SELECT title, author FROM ex.work_scores WHERE work_id=?", [wid]
        ).fetchone()
        top15.append(
            {
                "rank": rank,
                "work_id": wid,
                "title": row[0] if row else "?",
                "author": row[1] if row else "?",
            }
        )
    con.close()

    results = {
        "meta": {
            "memory_mode": "single-process compact pool",
            "max_sticky_likers": MAX_STICKY_LIKERS,
            "max_focus_pool": MAX_FOCUS_POOL,
            "max_anti_pool": MAX_ANTI_POOL,
            "max_edges_per_user": MAX_EDGES_PER_USER,
            "n_rounds": N_ROUNDS,
            "candidates_per_round": CANDIDATES_PER_ROUND,
            "final_boots": FINAL_BOOTS,
        },
        "start_metrics": {k: best_met[k] for k in ()},
        "history": history,
        "stability_start": {k: v for k, v in stab0.items() if k != "base"},
        "stability_best": {k: v for k, v in stab1.items() if k != "base"},
        "best_metrics": {
            k: adopted_met[k]
            for k in (
                "proxy",
                "sticky_in_50",
                "mean_sticky_rank",
                "anti50",
                "series20",
                "sep",
                "n_gated",
                "n_focus",
            )
            if k in adopted_met
        },
        "veto": {"accepted": accept, "reasons": reasons},
        "adopted_top15": top15,
        "weights_path": str(WEIGHTS_OUT) if accept else None,
    }
    # fix start metrics from history round 0
    results["start_metrics"] = {
        "proxy": history[0]["proxy"],
        "sticky_in_50": history[0]["sticky_in_50"],
        "anti50": history[0]["anti50"],
        "series20": history[0]["series20"],
        "mean_sticky_rank": history[0]["mean_sticky_rank"],
    }

    OUT_JSON.write_text(json.dumps(results, indent=2, default=float) + "\n")
    lines = [
        "# Fast co-training (16GB-safe)",
        "",
        "Single process, capped user/edge pools — no multi-process matrix copies.",
        "",
        f"## Veto: **{'ACCEPTED' if accept else 'REJECTED'}**",
        "",
    ]
    for r in reasons:
        lines.append(f"- {r}")
    lines += [
        "",
        f"- start J50={stab0['j50_mean']:.2f}, best J50={stab1['j50_mean']:.2f}",
        f"- start anti≈{stab0['anti50_mean']:.2f}, best anti≈{stab1['anti50_mean']:.2f}",
        "",
        "## Rounds",
        "",
    ]
    for h in history[1:]:
        lines.append(
            f"- round {h['round']}: proxy={h['best_proxy']:.2f} improved={h['improved']} "
            f"sticky50={h['sticky_in_50']} anti50={h['anti50']} ({h['elapsed_s']:.1f}s)"
        )
    lines += ["", "## Top 15", ""]
    for r in top15:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    if accept:
        lines += ["", f"Weights: `{WEIGHTS_OUT}`", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nVeto accepted={accept}: {reasons}", flush=True)
    print(f"Wrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reliable iterative co-training (16GB-safe).

Build once → directional soft-label nudges → cheap gates → periodic full veto.

Unlike the random-search fast path, each step reuses the careful recipe:
sticky-lovers vs series-binge effects, small STEP blend, gate tighten.
Scoring/boots use one sparse ratings matrix (no DuckDB rematerialize per boot).

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_cotraining_iter
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_cotraining_iter --steps 3
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

from curators_explorer.scripts.research_cotraining import (
    feature_effects,
    label_soft_users,
    load_sticky_ids,
    soft_negative_works,
    veto,
)
from curators_explorer.scripts.research_feature_sensitivity import (
    ANTI_TERMS,
    CLASSIC_TERMS,
    NORMIE_TERMS,
    _moments,
    build_affinity,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    evaluate,
    load_eval_sets,
    materialize_base,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    FEATURE_COLS,
    build_user_features,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "cotraining_iter.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "COTRAINING_ITER_REPORT.md"
WEIGHTS_IN = Path(__file__).resolve().parents[1] / "data" / "cotrained_weights.json"
WEIGHTS_OUT = Path(__file__).resolve().parents[1] / "data" / "cotrained_weights.json"

# Export envelope: slightly looser than current cotrained gates so tightening stays inside.
# Sized for ~16GB (uncapped edges within this pool).
LOOSE_SERIES = 0.42
LOOSE_MEGA = 0.32
LOOSE_BINGE = 2.9
LOOSE_SPAN = 3.2
MAX_ANTI_LIKE = 80_000
MAX_N = 120_000
MIN_VOTES = 30
LAM_A = 0.85
LAM_N = 0.75
TOP_FRAC = 0.06
STEP = 0.25  # milder than careful's 0.35 for multi-step
CHEAP_BOOTS = 5
FULL_BOOTS = 12
SEED = 7


def _load_start_weights() -> dict[str, Any]:
    if WEIGHTS_IN.exists():
        w = json.loads(WEIGHTS_IN.read_text(encoding="utf-8"))
        print(f"  starting from {WEIGHTS_IN}", flush=True)
        return w
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


def nudge_from_current(
    current: dict[str, Any],
    effects: dict[str, dict[str, float]],
    soft_pos_gate_pct: dict[str, float],
    *,
    step: float,
) -> dict[str, Any]:
    """Blend current weights toward soft-label targets; tighten gates only."""
    classic = dict(current["classic_terms"])
    anti = dict(current["anti_terms"])
    normie = dict(current["normie_terms"])
    gates = dict(current["gates"])

    for feat, coef in list(classic.items()):
        if feat not in effects:
            continue
        d = effects[feat]["d"]
        target = max(min(d * 1.2, 2.0), -2.0)
        classic[feat] = (1 - step) * float(coef) + step * target

    for feat, coef in list(anti.items()):
        if feat not in effects:
            continue
        d = effects[feat]["d"]
        target = max(min(-d * 1.2, 2.0), -2.0)
        anti[feat] = (1 - step) * float(coef) + step * target

    for feat, coef in list(normie.items()):
        if feat not in effects:
            continue
        d = effects[feat]["d"]
        target = max(min(-d * 0.8, 1.8), -1.8)
        s = step * 0.6
        normie[feat] = (1 - s) * float(coef) + s * target

    # tighten toward soft-pos percentiles
    sug = soft_pos_gate_pct
    gates["series_gate"] = min(
        gates["series_gate"], (1 - step) * gates["series_gate"] + step * sug["series"]
    )
    gates["mega_gate"] = min(
        gates["mega_gate"], (1 - step) * gates["mega_gate"] + step * sug["mega"]
    )
    gates["binge_gate"] = min(
        gates["binge_gate"], (1 - step) * gates["binge_gate"] + step * sug["binge"]
    )
    gates["span_gate"] = max(
        gates["span_gate"], (1 - step) * gates["span_gate"] + step * sug["span"]
    )

    return {
        "classic_terms": classic,
        "anti_terms": anti,
        "normie_terms": normie,
        "gates": gates,
        "lambda_anti": float(current.get("lambda_anti", LAM_A)),
        "lambda_normie": float(current.get("lambda_normie", LAM_N)),
        "top_frac": float(current.get("top_frac", TOP_FRAC)),
    }


def soft_pos_gate_percentiles(con) -> dict[str, float]:
    row = con.execute(
        """
        SELECT
            approx_quantile(series_share_5, 0.85::FLOAT),
            approx_quantile(mega_catalog_share_5, 0.85::FLOAT),
            approx_quantile(binge_mean_5, 0.85::FLOAT),
            approx_quantile(midpop_span_per_logn5, 0.20::FLOAT)
        FROM user_rich ur
        JOIN soft_pos_excl p USING (user_id)
        """
    ).fetchone()
    return {
        "series": float(row[0] or 0.40),
        "mega": float(row[1] or 0.28),
        "binge": float(row[2] or 2.8),
        "span": float(row[3] or 3.0),
    }


def build_bundle(con, sticky_ids: list[str], anti_ids: set[str]) -> dict[str, Any]:
    """Export user features + sparse ratings for loose-gated ∪ anti-like users."""
    print("Building sparse scoring bundle…", flush=True)
    t0 = time.time()

    moments = {}
    for c in FEATURE_COLS:
        mu, sd = con.execute(
            f"SELECT avg({c}), stddev_samp({c}) FROM user_rich WHERE {c} IS NOT NULL"
        ).fetchone()
        moments[c] = (float(mu or 0), float(sd or 1) or 1.0)

    # Cap anti-like volume for 16GB; keep all loose-gated (focus) users.
    rows = con.execute(
        f"""
        WITH focus AS (
            SELECT user_id, {", ".join(FEATURE_COLS)},
                   series_share_5, mega_catalog_share_5, binge_mean_5, midpop_span_per_logn5,
                   0 AS is_anti_only
            FROM user_rich
            WHERE series_share_5 <= {LOOSE_SERIES}
              AND mega_catalog_share_5 <= {LOOSE_MEGA}
              AND binge_mean_5 <= {LOOSE_BINGE}
              AND midpop_span_per_logn5 >= {LOOSE_SPAN}
        ),
        anti_pool AS (
            SELECT user_id, {", ".join(FEATURE_COLS)},
                   series_share_5, mega_catalog_share_5, binge_mean_5, midpop_span_per_logn5,
                   1 AS is_anti_only
            FROM user_rich
            WHERE (series_share_5 >= 0.45 OR binge_mean_5 >= 2.5)
              AND user_id NOT IN (SELECT user_id FROM focus)
            ORDER BY (series_share_5 + 0.15 * binge_mean_5) DESC
            LIMIT {MAX_ANTI_LIKE}
        )
        SELECT * FROM focus
        UNION ALL
        SELECT * FROM anti_pool
        """
    ).fetchall()
    print(
        f"  focus∪anti export users={len(rows):,} "
        f"(anti cap {MAX_ANTI_LIKE:,})",
        flush=True,
    )

    n = len(rows)
    Fdim = len(FEATURE_COLS)
    X = np.zeros((n, Fdim), dtype=np.float32)
    for j, c in enumerate(FEATURE_COLS):
        mu, sd = moments[c]
        for i, r in enumerate(rows):
            v = r[1 + j]
            X[i, j] = (float(v if v is not None else mu) - mu) / sd
    series = np.array([float(r[1 + Fdim] or 0) for r in rows], dtype=np.float32)
    mega = np.array([float(r[2 + Fdim] or 0) for r in rows], dtype=np.float32)
    binge = np.array([float(r[3 + Fdim] or 0) for r in rows], dtype=np.float32)
    span = np.array([float(r[4 + Fdim] or 0) for r in rows], dtype=np.float32)
    user_ids = np.array([int(r[0]) for r in rows], dtype=np.int64)
    uid_to_row = {int(u): i for i, u in enumerate(user_ids)}
    feat_index = {c: j for j, c in enumerate(FEATURE_COLS)}
    print(f"  users={n:,}", flush=True)

    con.execute("CREATE OR REPLACE TABLE pool_users (user_id BIGINT)")
    # batch insert
    batch = [(int(u),) for u in user_ids]
    for i in range(0, len(batch), 50_000):
        con.executemany("INSERT INTO pool_users VALUES (?)", batch[i : i + 50_000])

    edge_rel = con.execute(
        f"""
        SELECT e.user_id, e.work_id, (e.rating = 5)::BOOLEAN AS is5
        FROM ex.all_rating_events e
        JOIN pool_users p USING (user_id)
        JOIN work_rarity wr ON wr.work_id = e.work_id
        WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
        """
    )
    # Columnar fetch — avoid tens of millions of Python tuples.
    try:
        arr = edge_rel.fetchnumpy()
        e_uid = np.asarray(arr["user_id"])
        e_wid = np.asarray(arr["work_id"]).astype(str)
        e_is5 = np.asarray(arr["is5"]).astype(bool)
    except Exception:
        edges = edge_rel.fetchall()
        e_uid = np.array([int(u) for u, _, _ in edges], dtype=np.int64)
        e_wid = np.array([str(w) for _, w, _ in edges])
        e_is5 = np.array([bool(i) for _, _, i in edges])
        del edges
    print(f"  edges={len(e_uid):,} (uncapped, faithful to DuckDB scorer)", flush=True)

    # Vectorized id maps (avoid Python loops over tens of millions of edges)
    work_ids, cc = np.unique(e_wid, return_inverse=True)
    work_ids = work_ids.astype(str)
    work_index = {w: j for j, w in enumerate(work_ids)}
    W = len(work_ids)

    max_uid = int(user_ids.max()) if len(user_ids) else 0
    if max_uid <= 50_000_000:
        mapper = np.full(max_uid + 1, -1, dtype=np.int32)
        mapper[user_ids] = np.arange(n, dtype=np.int32)
        rr = mapper[e_uid.astype(np.int64, copy=False)]
        del mapper
    else:
        rr = np.fromiter(
            (uid_to_row[int(u)] for u in e_uid), dtype=np.int32, count=len(e_uid)
        )
    if (rr < 0).any():
        raise RuntimeError("edge user_id not in pool map")

    R = sparse.csr_matrix(
        (np.ones(len(rr), dtype=np.float32), (rr, cc.astype(np.int32, copy=False))),
        shape=(n, W),
        dtype=np.float32,
    )
    mask5 = e_is5
    F = sparse.csr_matrix(
        (
            np.ones(int(mask5.sum()), dtype=np.float32),
            (rr[mask5], cc[mask5].astype(np.int32, copy=False)),
        ),
        shape=(n, W),
        dtype=np.float32,
    )
    del e_uid, e_wid, e_is5, rr, cc, mask5

    sticky_cols = np.array(
        [work_index[w] for w in sticky_ids if w in work_index], dtype=np.int32
    )
    anti_cols = np.array(
        [work_index[w] for w in anti_ids if w in work_index], dtype=np.int32
    )

    soft_pos = [
        int(u)
        for (u,) in con.execute("SELECT user_id FROM soft_pos_excl").fetchall()
        if int(u) in uid_to_row
    ]
    soft_neg = [
        int(u)
        for (u,) in con.execute("SELECT user_id FROM soft_neg_excl").fetchall()
        if int(u) in uid_to_row
    ]
    soft_pos_rows = np.array([uid_to_row[u] for u in soft_pos], dtype=np.int32)
    soft_neg_rows = np.array([uid_to_row[u] for u in soft_neg], dtype=np.int32)

    nbytes = R.data.nbytes + R.indices.nbytes + R.indptr.nbytes
    nbytes += F.data.nbytes + F.indices.nbytes + F.indptr.nbytes + X.nbytes
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
        "soft_pos_rows": soft_pos_rows,
        "soft_neg_rows": soft_neg_rows,
        "sticky_ids": sticky_ids,
        "anti_ids": anti_ids,
    }


def affinities(b: dict[str, Any], w: dict[str, Any]):
    fi = b["feat_index"]
    X = b["X"]
    classic = np.zeros(X.shape[0], dtype=np.float32)
    anti = np.zeros(X.shape[0], dtype=np.float32)
    normie = np.zeros(X.shape[0], dtype=np.float32)
    for k, coef in w["classic_terms"].items():
        if k in fi:
            classic += np.float32(coef) * X[:, fi[k]]
    for k, coef in w["anti_terms"].items():
        if k in fi:
            anti += np.float32(coef) * X[:, fi[k]]
    for k, coef in w["normie_terms"].items():
        if k in fi:
            normie += np.float32(coef) * X[:, fi[k]]
    focus = (
        classic
        - np.float32(w.get("lambda_anti", LAM_A)) * anti
        - np.float32(w.get("lambda_normie", LAM_N)) * normie
    )
    g = w["gates"]
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
    k = max(int(len(idx) * frac), 50)
    if k >= len(idx):
        chosen = idx
    else:
        chosen = idx[np.argpartition(-scores[idx], k)[:k]]
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
    p5_c = np.divide(n5_c, n_c, out=np.zeros_like(n5_c), where=n_c >= MIN_VOTES)
    p5_a = np.divide(n5_a, n_a, out=np.zeros_like(n5_a), where=n_a >= MIN_VOTES)
    p5_a = np.where(n_a < MIN_VOTES, p5_c * np.float32(0.85), p5_a)
    score = p5_c - p5_a
    score = np.where(n_c >= MIN_VOTES, score, np.float32(-1e9))
    return score


def point_eval(b: dict[str, Any], w: dict[str, Any], ev: dict[str, Any]) -> dict[str, Any]:
    focus_s, anti_s, gated, anti_like = affinities(b, w)
    frac = float(w.get("top_frac", TOP_FRAC))
    if int(gated.sum()) < 200:
        return {"ok": False, "reason": "gated_small", "n_gated": int(gated.sum())}
    focus_m = top_frac_mask(focus_s, gated, frac)
    anti_m = top_frac_mask(anti_s, anti_like, frac)
    scores = contrastive_scores(b, focus_m, anti_m)
    order = np.argsort(-scores)
    top50_idx = order[:50]
    top200_idx = order[:200]
    top50_ids = {b["work_ids"][i] for i in top50_idx}

    # n_eff for evaluate(); approx with focus cohort size on the work
    wf = focus_m.astype(np.float32)
    n_c = np.asarray(wf @ b["R"]).ravel()
    rows = []
    for rank, i in enumerate(order[:500], 1):
        ii = int(i)
        rows.append(
            {
                "work_id": b["work_ids"][ii],
                "rank": rank,
                "score": float(scores[ii]),
                "n_eff": float(max(n_c[ii], 1.0)),
                "title": "",
                "author": "",
            }
        )
    met = evaluate(rows, ev)
    sticky_in_50 = sum(1 for c in b["sticky_cols"] if b["work_ids"][int(c)] in top50_ids)
    sep = 0.0
    if len(b["soft_pos_rows"]) and len(b["soft_neg_rows"]):
        sep = float(focus_s[b["soft_pos_rows"]].mean() - focus_s[b["soft_neg_rows"]].mean())
    return {
        "ok": True,
        "eval": met,
        "sticky_in_50": sticky_in_50,
        "sep": sep,
        "n_gated": int(gated.sum()),
        "n_focus": int(focus_m.sum()),
        "top50_ids": top50_ids,
        "top200_ids": {b["work_ids"][i] for i in top200_idx},
        "top15_idx": [int(i) for i in order[:15]],
    }


def bootstrap_stab(
    b: dict[str, Any],
    w: dict[str, Any],
    *,
    base_top50: set[str],
    base_top200: set[str],
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    focus_s, anti_s, gated, anti_like = affinities(b, w)
    g_idx = np.flatnonzero(gated)
    a_idx = np.flatnonzero(anti_like)
    frac = float(w.get("top_frac", TOP_FRAC))
    j50s, j200s, antis, stickies = [], [], [], []
    sticky_set = set(b["sticky_ids"])
    anti_set = set(b["anti_ids"])
    presence: dict[str, int] = {}
    for _ in range(n_boot):
        g_samp = np.unique(rng.choice(g_idx, size=len(g_idx), replace=True))
        a_samp = np.unique(rng.choice(a_idx, size=len(a_idx), replace=True))
        k_g = max(int(len(g_idx) * frac), 50)
        k_a = max(int(len(a_idx) * frac), 50)
        g_ord = g_samp[np.argsort(-focus_s[g_samp])][:k_g]
        a_ord = a_samp[np.argsort(-anti_s[a_samp])][:k_a]
        focus_m = np.zeros(len(focus_s), dtype=bool)
        anti_m = np.zeros(len(anti_s), dtype=bool)
        focus_m[g_ord] = True
        anti_m[a_ord] = True
        scores = contrastive_scores(b, focus_m, anti_m)
        order = np.argsort(-scores)
        t50 = {b["work_ids"][int(i)] for i in order[:50]}
        t200 = {b["work_ids"][int(i)] for i in order[:200]}
        j50s.append(len(base_top50 & t50) / max(len(base_top50 | t50), 1))
        j200s.append(len(base_top200 & t200) / max(len(base_top200 | t200), 1))
        antis.append(sum(1 for w_id in t50 if w_id in anti_set))
        stickies.append(sum(1 for w_id in t50 if w_id in sticky_set) / max(len(sticky_set), 1))
        for wid in t50:
            presence[wid] = presence.get(wid, 0) + 1
    n_sticky_ok = sum(
        1 for wid in sticky_set if presence.get(wid, 0) / n_boot >= 0.7
    )
    return {
        "j50_mean": float(np.mean(j50s)),
        "j50_sd": float(np.std(j50s)),
        "j200_mean": float(np.mean(j200s)),
        "anti50_mean": float(np.mean(antis)),
        "sticky_fraction_in_top50_mean": float(np.mean(stickies)),
        "n_sticky_still_ge_70pct": n_sticky_ok,
        "n_sticky": len(sticky_set),
    }


def cheap_accept(before: dict[str, Any], after: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons = []
    ok = True
    if not after.get("ok"):
        return False, [after.get("reason", "failed")]
    if after["eval"]["anti50"] > 1:
        ok = False
        reasons.append(f"anti50={after['eval']['anti50']}")
    if after["sticky_in_50"] < before["sticky_in_50"] - 2:
        ok = False
        reasons.append(
            f"sticky_in_50 {before['sticky_in_50']}→{after['sticky_in_50']}"
        )
    if after["sep"] < before["sep"] - 0.15:
        ok = False
        reasons.append(f"sep {before['sep']:.2f}→{after['sep']:.2f}")
    if ok:
        reasons.append("cheap gate ok")
    return ok, reasons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3, help="directional nudge steps")
    ap.add_argument("--step-size", type=float, default=STEP)
    ap.add_argument("--cheap-boots", type=int, default=CHEAP_BOOTS)
    ap.add_argument("--full-boots", type=int, default=FULL_BOOTS)
    args = ap.parse_args()

    t_all = time.time()

    def lap(label: str, t0: float) -> float:
        print(f"  [timing] {label}: {time.time()-t0:.1f}s (total {time.time()-t_all:.1f}s)", flush=True)
        return time.time()

    con = _con()
    ev = load_eval_sets(con)
    print("Setup…", flush=True)
    t = time.time()
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    label_cohorts(con)
    t = lap("materialize", t)

    sticky_ids = load_sticky_ids()
    moments = _moments(con)
    start_w = _load_start_weights()
    build_affinity(
        con,
        moments,
        classic_terms=start_w["classic_terms"],
        anti_terms=start_w["anti_terms"],
        normie_terms=start_w["normie_terms"],
        series_gate=start_w["gates"]["series_gate"],
        mega_gate=start_w["gates"]["mega_gate"],
        binge_gate=start_w["gates"]["binge_gate"],
        span_gate=start_w["gates"]["span_gate"],
    )
    neg_ids = soft_negative_works(con)
    label_soft_users(con, sticky_ids, neg_ids)
    effects = feature_effects(con)
    gate_pct = soft_pos_gate_percentiles(con)
    print("  top effects:", flush=True)
    for feat, e in sorted(effects.items(), key=lambda kv: -abs(kv[1]["d"]))[:8]:
        print(f"    {feat:28s} d={e['d']:+.2f}", flush=True)
    t = lap("soft labels + effects", t)

    anti_ids = {
        str(r[0])
        for r in con.execute(
            "SELECT work_id FROM ex.taste_signal_works WHERE side='non_literary'"
        ).fetchall()
    }
    con.execute("CREATE OR REPLACE TABLE sticky_works (work_id VARCHAR)")
    con.executemany(
        "INSERT INTO sticky_works VALUES (?)", [(w,) for w in sticky_ids]
    )
    b = build_bundle(con, sticky_ids, anti_ids)
    con.close()
    t = lap("sparse bundle", t)

    current = start_w
    start = json.loads(json.dumps(current))  # deep copy via json
    start_pt = point_eval(b, current, ev)
    print(
        f"Start: Q={start_pt['eval']['Q']:.1f} pos50={start_pt['eval']['pos50']} "
        f"anti50={start_pt['eval']['anti50']} sticky50={start_pt['sticky_in_50']} "
        f"sep={start_pt['sep']:.2f}",
        flush=True,
    )
    print(f"  cheap stability ({args.cheap_boots} boots)…", flush=True)
    start_cheap = bootstrap_stab(
        b,
        current,
        base_top50=start_pt["top50_ids"],
        base_top200=start_pt["top200_ids"],
        n_boot=args.cheap_boots,
        seed=SEED,
    )
    print(
        f"  J50={start_cheap['j50_mean']:.2f} anti≈{start_cheap['anti50_mean']:.2f} "
        f"sticky70={start_cheap['n_sticky_still_ge_70pct']}/{start_cheap['n_sticky']}",
        flush=True,
    )
    t = lap("start eval + cheap boots", t)

    history: list[dict[str, Any]] = []
    accepted_steps = 0
    last_pt = start_pt
    last_cheap = start_cheap
    for step_i in range(1, args.steps + 1):
        t_step = time.time()
        candidate = nudge_from_current(current, effects, gate_pct, step=args.step_size)
        cand_pt = point_eval(b, candidate, ev)
        ok, reasons = cheap_accept(last_pt, cand_pt)
        entry: dict[str, Any] = {
            "step": step_i,
            "cheap_ok": ok,
            "reasons": reasons,
            "point": {
                "Q": cand_pt.get("eval", {}).get("Q"),
                "pos50": cand_pt.get("eval", {}).get("pos50"),
                "anti50": cand_pt.get("eval", {}).get("anti50"),
                "sticky_in_50": cand_pt.get("sticky_in_50"),
                "sep": cand_pt.get("sep"),
            },
            "gates": candidate["gates"],
        }
        if not ok:
            print(f"Step {step_i}: REJECT cheap — {reasons}", flush=True)
            entry["accepted"] = False
            history.append(entry)
            print(f"  stopping early ({time.time()-t_step:.1f}s)", flush=True)
            break

        print(
            f"Step {step_i}: cheap ok — Q={cand_pt['eval']['Q']:.1f} "
            f"sticky50={cand_pt['sticky_in_50']} anti50={cand_pt['eval']['anti50']}",
            flush=True,
        )
        print(f"  cheap stability ({args.cheap_boots} boots)…", flush=True)
        cand_cheap = bootstrap_stab(
            b,
            candidate,
            base_top50=cand_pt["top50_ids"],
            base_top200=cand_pt["top200_ids"],
            n_boot=args.cheap_boots,
            seed=SEED,
        )
        stab_ok = True
        stab_reasons = []
        if cand_cheap["anti50_mean"] > 0.5:
            stab_ok = False
            stab_reasons.append(f"anti≈{cand_cheap['anti50_mean']:.2f}")
        if cand_cheap["j50_mean"] < last_cheap["j50_mean"] - 0.05:
            stab_ok = False
            stab_reasons.append(
                f"J50 {last_cheap['j50_mean']:.2f}→{cand_cheap['j50_mean']:.2f}"
            )
        if cand_cheap["n_sticky_still_ge_70pct"] < last_cheap["n_sticky_still_ge_70pct"] - 2:
            stab_ok = False
            stab_reasons.append("sticky70 dropped")
        entry["cheap_stab"] = {
            k: cand_cheap[k]
            for k in (
                "j50_mean",
                "anti50_mean",
                "n_sticky_still_ge_70pct",
                "n_sticky",
                "sticky_fraction_in_top50_mean",
            )
        }
        if not stab_ok:
            print(f"  REJECT cheap-stab — {stab_reasons}", flush=True)
            entry["accepted"] = False
            entry["reasons"] = stab_reasons
            history.append(entry)
            break

        current = candidate
        last_pt = cand_pt
        last_cheap = cand_cheap
        accepted_steps += 1
        entry["accepted"] = True
        entry["reasons"] = reasons + ["cheap-stab ok"]
        history.append(entry)
        print(
            f"  ACCEPT step {step_i}: J50={cand_cheap['j50_mean']:.2f} "
            f"({time.time()-t_step:.1f}s)",
            flush=True,
        )

    t = lap(f"{accepted_steps} accepted nudge step(s)", t)

    # Full veto vs run-start
    print(f"\nFull veto ({args.full_boots} boots)…", flush=True)
    start_full = bootstrap_stab(
        b,
        start,
        base_top50=start_pt["top50_ids"],
        base_top200=start_pt["top200_ids"],
        n_boot=args.full_boots,
        seed=SEED,
    )
    end_pt = point_eval(b, current, ev)
    end_full = bootstrap_stab(
        b,
        current,
        base_top50=end_pt["top50_ids"],
        base_top200=end_pt["top200_ids"],
        n_boot=args.full_boots,
        seed=SEED,
    )
    decision = veto(start_full, end_full, start_pt["eval"], end_pt["eval"])
    print(
        f"  start J50={start_full['j50_mean']:.2f} anti≈{start_full['anti50_mean']:.2f}",
        flush=True,
    )
    print(
        f"  end   J50={end_full['j50_mean']:.2f} anti≈{end_full['anti50_mean']:.2f}",
        flush=True,
    )
    print(f"  veto accepted={decision['accepted']}: {decision['reasons']}", flush=True)
    t = lap("full veto", t)

    adopted = current if decision["accepted"] and accepted_steps > 0 else start
    if decision["accepted"] and accepted_steps > 0:
        WEIGHTS_OUT.write_text(json.dumps(adopted, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {WEIGHTS_OUT}", flush=True)
    elif accepted_steps == 0:
        decision = {
            "accepted": False,
            "reasons": decision["reasons"] + ["no steps accepted"],
        }

    # titles for report
    con = _con()
    top15 = []
    final_pt = point_eval(b, adopted, ev)
    for rank, idx in enumerate(final_pt["top15_idx"], 1):
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
            "steps_requested": args.steps,
            "steps_accepted": accepted_steps,
            "step_size": args.step_size,
            "cheap_boots": args.cheap_boots,
            "full_boots": args.full_boots,
            "memory_mode": "single-process sparse full loose∪anti pool",
        },
        "start": {
            "eval": start_pt["eval"],
            "sticky_in_50": start_pt["sticky_in_50"],
            "sep": start_pt["sep"],
            "cheap_stab": start_cheap,
            "full_stab": start_full,
        },
        "end": {
            "eval": end_pt["eval"],
            "sticky_in_50": end_pt["sticky_in_50"],
            "sep": end_pt["sep"],
            "full_stab": end_full,
        },
        "history": history,
        "veto": decision,
        "top15": top15,
        "weights_path": str(WEIGHTS_OUT) if decision["accepted"] and accepted_steps else None,
    }
    OUT_JSON.write_text(json.dumps(results, indent=2, default=float) + "\n")
    lines = [
        "# Iterative co-training (reliable rough steps)",
        "",
        "Directional soft-label nudges on one sparse matrix; cheap gates; full veto at end.",
        "",
        f"## Veto: **{'ACCEPTED' if decision['accepted'] and accepted_steps else 'REJECTED'}**",
        "",
    ]
    for r in decision["reasons"]:
        lines.append(f"- {r}")
    lines += [
        "",
        f"- steps accepted: {accepted_steps}/{args.steps}",
        f"- start Q={start_pt['eval']['Q']:.1f} sticky50={start_pt['sticky_in_50']} "
        f"J50={start_full['j50_mean']:.2f}",
        f"- end   Q={end_pt['eval']['Q']:.1f} sticky50={end_pt['sticky_in_50']} "
        f"J50={end_full['j50_mean']:.2f}",
        "",
        "## Steps",
        "",
    ]
    for h in history:
        lines.append(
            f"- step {h['step']}: accepted={h['accepted']} "
            f"Q={h['point'].get('Q')} sticky50={h['point'].get('sticky_in_50')} "
            f"anti50={h['point'].get('anti50')} — {', '.join(h['reasons'])}"
        )
    lines += ["", "## Top 15 (adopted)", ""]
    for r in top15:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)


if __name__ == "__main__":
    main()

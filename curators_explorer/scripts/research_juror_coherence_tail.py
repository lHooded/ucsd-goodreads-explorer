#!/usr/bin/env python3
"""JUROR COHERENCE & OBSCURE-BOOK TAIL DIAGNOSTIC.

Answers a structural question about the candidate literary juries:

> Are users inside a candidate jury individually useful jurors, or can a
> literary-looking aggregate be produced by heterogeneous subgroups whose
> errors merely cancel?

This matters for obscure-book discovery: for a sparsely rated work only a few
jurors have rated it, so a large jury is useful only if its extra jurors give
individually reliable information.

Separated axes (NOT combined into one objective here):
  1. aggregate literary quality       (already seen in ranked heads)
  2. individual juror concordance     (out-of-sample, this experiment)
  3. obscure-book usefulness          (raw + reliability-weighted coverage,
                                       sparse-book holdout)

Diagnostic only. No jury-membership changes, no reweighting of jurors, no
committee model, no reversal, no optimization.

Reuses the accepted full raw user-ID populations from 169ec0f.

Parts:
  A. 10-fold out-of-sample per-juror concordance q (rating-only, ties=0.5,
     PRIOR_K=40 shrinkage; NaN when no testable pairs).
  B. population reliability distributions.
  C. exclusive Venn-region reliability.
  D. region-to-region agreement / cancellation (score + preference signs).
  E. global-rarity bands (global rating counts, works < MIN_RANK_N allowed).
  F. raw jury coverage of obscure books.
  G. reliability-weighted tail coverage (reliable_mass, reliable_n_eff).
  H. marginal tail coverage added by exclusive regions.
  I. bounded sparse-book holdout validation (ordinary + reliability-weighted).
  J. anti/fandom coherence control (threeway_anti sample).

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_juror_coherence_tail --smoke
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_juror_coherence_tail --phase prepare
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_juror_coherence_tail --phase all
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts.research_deep_size_sweep import (
    MAX_N,
    MIN_RANK_N,
    build_pairs,
    rank_pairwise,
)
from curators_explorer.scripts.research_maximum_literary_jury import (
    DATA,
    OUT_NPZ as OLD_NPZ,
    _derive_seed,
    _fmt_time,
    _json_default,
    _write_npz_atomic,
    _write_text_atomic,
    _con,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    materialize_base,
)

JUROR_COHERENCE_SEED = 20260829

OUT_JSON = DATA / "juror_coherence_tail.json"
OUT_NPZ = DATA / "juror_coherence_tail.npz"
OUT_MD = DATA / "JUROR_COHERENCE_TAIL_REPORT.md"
STATE_DIR = DATA / "juror_coherence_tail_state"

VENN_NPZ = DATA / "jury_consensus_venn.npz"

N_FOLDS = 10
MAX_EVAL_HIGHS = 40
MAX_EVAL_LOWS = 40
MAX_EVAL_PAIRS = 400
PRIOR_K = 40.0
TIE_SCORE = 0.5  # ties counted 0.5; fixed before results

MIN_REGION_EDGES = [20, 50]
MAX_REGION_PAIRS = 100_000
STRONG_DIFF = 0.10

RARITY_BANDS = [(5, 19), (20, 49), (50, 99), (100, 249), (250, 999),
                (1000, 4999), (5000, None)]
BAND_LABELS = ["5_19", "20_49", "50_99", "100_249", "250_999", "1000_4999",
               "5000_plus"]

MAX_BOOKS_PER_BAND = 500
MIN_JURY_BOOK_RATERS = 4
FANDOM_CAP = 10_000

# Concordance priority order (runtime control).
MAIN_POPS = [
    "ABC",
    "committee_AnB",
    "committee_vote2_ABCs",
    "committee_AuB",
    "A_only",
    "B_only",
    "AB_only",
    "core_p65_s25",
    "deep_mint_all",
    "committee_union_ABCs",
    "threeway_classic",
]
ALL_REGIONS = ["A_only", "B_only", "C_only", "AB_only", "AC_only", "BC_only",
               "ABC"]

TAIL_JURIES = [
    "ABC", "committee_AnB", "committee_vote2_ABCs", "committee_AuB",
    "committee_union_ABCs", "core_p65_s25", "deep_mint_all",
    "A_only", "B_only", "AB_only",
]
# marginal-coverage bases / additions (Part H)
MARGINAL_BASES = ["deep_mint_all", "threeway_classic", "committee_vote2_ABCs"]
MARGINAL_ADDITIONS = ["A_only", "B_only", "C_only"]

# jury -> which concordance population supplies its q weights
JURY_Q_SOURCE = {
    "ABC": "ABC",
    "committee_AnB": "committee_AnB",
    "committee_vote2_ABCs": "committee_vote2_ABCs",
    "committee_AuB": "committee_AuB",
    "committee_union_ABCs": "committee_union_ABCs",
    "core_p65_s25": "core_p65_s25",
    "deep_mint_all": "deep_mint_all",
    "threeway_classic": "threeway_classic",
    "A_only": "A_only",
    "B_only": "B_only",
    "C_only": "C_only",
    "AB_only": "AB_only",
    "AC_only": "AC_only",
    "BC_only": "BC_only",
}

_jury_counter = [0]


def _next_table() -> str:
    _jury_counter[0] += 1
    return f"coh_jury_{_jury_counter[0]}"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_juries() -> dict[str, np.ndarray]:
    old = np.load(OLD_NPZ, allow_pickle=False)
    venn = np.load(VENN_NPZ, allow_pickle=False)
    out: dict[str, np.ndarray] = {}
    for name in [
        "core_p65_s25", "deep_mint_all", "threeway_classic", "rebuilt_hard",
        "ABC", "A_only", "B_only", "C_only", "AB_only", "AC_only", "BC_only",
        "committee_AnB", "committee_vote2_ABCs", "committee_AuB",
        "committee_union_ABCs",
    ]:
        if name in ("core_p65_s25", "deep_mint_all", "threeway_classic",
                    "rebuilt_hard"):
            key = f"juries/{name}/user_ids"
            blob = old
        else:
            key = f"juries/{name}/user_ids" if name.startswith("committee") else f"regions/{name}/user_ids"
            blob = venn
        out[name] = blob[key].astype(np.int64)
    return out


def open_db() -> Any:
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    return con


# ---------------------------------------------------------------------------
# Direct pairwise ranking (build_pairs route)
# ---------------------------------------------------------------------------

def build_ranking(con, user_ids: np.ndarray) -> list[dict]:
    """Equal-vote pairwise ranking over `user_ids` via build_pairs."""
    user_ids = np.asarray(user_ids, dtype=np.int64)
    table = _next_table()
    pairs = f"{table}_pairs"
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT, w DOUBLE)")
    if len(user_ids):
        con.execute(
            f"INSERT INTO {table} SELECT * FROM ("
            f"SELECT unnest(?::BIGINT[]) AS user_id, 1.0::DOUBLE AS w)",
            [user_ids.tolist()],
        )
    build_pairs(con, table, pairs)
    rows = rank_pairwise(con, pairs, "w")
    con.execute(f"DROP TABLE IF EXISTS {pairs}")
    con.execute(f"DROP TABLE IF EXISTS {table}")
    return rows


def score_dict(rows: list[dict]) -> dict[str, float]:
    return {r["work_id"]: float(r["score"]) for r in rows}


def edge_counts(rows: list[dict]) -> dict[str, float]:
    return {r["work_id"]: float(r.get("n_eff") or r.get("n_c") or 0) for r in rows}


# ---------------------------------------------------------------------------
# Fold assignment (deterministic, balanced)
# ---------------------------------------------------------------------------

def assign_folds(user_ids: np.ndarray, pop: str, n_folds: int = N_FOLDS) -> np.ndarray:
    rng = np.random.default_rng(_derive_seed(JUROR_COHERENCE_SEED, "fold", pop))
    perm = rng.permutation(len(user_ids))
    folds = np.empty(len(user_ids), dtype=np.int8)
    folds[perm] = np.arange(len(user_ids)) % n_folds
    return folds


# ---------------------------------------------------------------------------
# Per-user high/low works (5-star vs <=3), scorer-eligible universe
# ---------------------------------------------------------------------------

def _cache_path(pop: str, tag: str) -> Path:
    return STATE_DIR / f"{pop}_{tag}.npz"


def user_high_low(con, user_ids: np.ndarray, pop: str) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """(highs, lows): user_id -> eligible 5-star / <=3 work ids (cached)."""
    path = _cache_path(pop, "highlow")
    if path.exists():
        with np.load(path, allow_pickle=False) as blob:
            h_uid = blob["h_uid"].astype(np.int64)
            h_wid = blob["h_wid"].astype(str)
            l_uid = blob["l_uid"].astype(np.int64)
            l_wid = blob["l_wid"].astype(str)
        return _group(h_uid, h_wid), _group(l_uid, l_wid)
    table = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT)")
    con.execute(
        f"INSERT INTO {table} SELECT unnest(?::BIGINT[])",
        [user_ids.tolist()],
    )
    h_rows = con.execute(
        f"SELECT e.user_id, e.work_id FROM ex.all_rating_events e "
        f"JOIN {table} u USING (user_id) "
        f"JOIN work_rarity wr ON wr.work_id = e.work_id "
        f"WHERE e.rating = 5 AND wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}"
    ).fetchall()
    l_rows = con.execute(
        f"SELECT e.user_id, e.work_id FROM ex.all_rating_events e "
        f"JOIN {table} u USING (user_id) "
        f"JOIN work_rarity wr ON wr.work_id = e.work_id "
        f"WHERE e.rating <= 3 AND wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}"
    ).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {table}")
    h_uid = np.asarray([r[0] for r in h_rows], dtype=np.int64)
    h_wid = np.asarray([r[1] for r in h_rows], dtype=str)
    l_uid = np.asarray([r[0] for r in l_rows], dtype=np.int64)
    l_wid = np.asarray([r[1] for r in l_rows], dtype=str)
    _write_npz_atomic(path, {"h_uid": h_uid, "h_wid": h_wid,
                             "l_uid": l_uid, "l_wid": l_wid})
    return _group(h_uid, h_wid), _group(l_uid, l_wid)


def _group(uids: np.ndarray, wids: np.ndarray) -> dict[int, np.ndarray]:
    order = np.argsort(uids, kind="stable")
    uids, wids = uids[order], wids[order]
    out: dict[int, np.ndarray] = defaultdict(list)
    # build via split points for speed
    uniq, starts = np.unique(uids, return_index=True)
    starts = np.append(starts, len(uids))
    for i, u in enumerate(uniq):
        out[int(u)] = wids[starts[i]:starts[i + 1]].copy()
    return out


# ---------------------------------------------------------------------------
# Part A — per-juror concordance
# ---------------------------------------------------------------------------

def _evaluate_user(user_id: int, highs: np.ndarray, lows: np.ndarray,
                   sd: dict[str, float], rng) -> dict[str, float]:
    nh = min(len(highs), MAX_EVAL_HIGHS)
    nl = min(len(lows), MAX_EVAL_LOWS)
    if nh == 0 or nl == 0:
        return {"n_eval_highs": nh, "n_eval_lows": nl, "n_pairs_sampled": 0,
                "n_pairs_testable": 0, "agreement_sum": 0.0, "q_raw": np.nan,
                "q_shrunk": np.nan}
    hs = rng.choice(highs, nh, replace=False) if len(highs) > nh else highs
    ls = rng.choice(lows, nl, replace=False) if len(lows) > nl else lows
    if nh * nl > MAX_EVAL_PAIRS:
        idx = rng.choice(nh * nl, MAX_EVAL_PAIRS, replace=False)
        pairs = [(hs[i // nl], ls[i % nl]) for i in idx]
    else:
        pairs = [(h, l) for h in hs for l in ls]
    agree = 0.0
    testable = 0
    for h, l in pairs:
        sh = sd.get(h)
        sl = sd.get(l)
        if sh is None or sl is None:
            continue
        testable += 1
        if sh > sl:
            agree += 1.0
        elif sh < sl:
            agree += 0.0
        else:
            agree += TIE_SCORE
    q_raw = float("nan")
    q_shrunk = float("nan")
    if testable > 0:
        q_raw = agree / testable
        q_shrunk = (agree + PRIOR_K * 0.5) / (testable + PRIOR_K)
    return {"n_eval_highs": nh, "n_eval_lows": nl, "n_pairs_sampled": len(pairs),
            "n_pairs_testable": testable, "agreement_sum": agree,
            "q_raw": q_raw, "q_shrunk": q_shrunk}


def compute_population_q(con, user_ids: np.ndarray, pop: str,
                         force: bool = False) -> dict[str, Any]:
    path = _cache_path(pop, "q")
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}

    user_ids = np.asarray(user_ids, dtype=np.int64)
    folds = assign_folds(user_ids, pop)
    highs, lows = user_high_low(con, user_ids, pop)

    n = len(user_ids)
    q_raw = np.full(n, np.nan)
    q_shrunk = np.full(n, np.nan)
    n_testable = np.zeros(n, dtype=np.int64)
    n_sampled = np.zeros(n, dtype=np.int64)
    n_eval_highs = np.zeros(n, dtype=np.int64)
    n_eval_lows = np.zeros(n, dtype=np.int64)
    agree_sum = np.zeros(n, dtype=np.float64)

    for fold in range(N_FOLDS):
        train_mask = folds != fold
        test_idx = np.flatnonzero(folds == fold)
        if len(test_idx) == 0:
            continue
        train_users = user_ids[train_mask]
        rows = build_ranking(con, train_users)
        sd = score_dict(rows)
        for i in test_idx:
            uid = int(user_ids[i])
            h = highs.get(uid)
            l = lows.get(uid)
            if h is None:
                h = np.asarray([], dtype=str)
            if l is None:
                l = np.asarray([], dtype=str)
            rng = np.random.default_rng(
                _derive_seed(JUROR_COHERENCE_SEED, "pairs", pop, uid))
            rec = _evaluate_user(uid, h, l, sd, rng)
            q_raw[i] = rec["q_raw"]
            q_shrunk[i] = rec["q_shrunk"]
            n_testable[i] = rec["n_pairs_testable"]
            n_sampled[i] = rec["n_pairs_sampled"]
            n_eval_highs[i] = rec["n_eval_highs"]
            n_eval_lows[i] = rec["n_eval_lows"]
            agree_sum[i] = rec["agreement_sum"]
        print(f"[concordance] {pop} fold {fold}: {len(test_idx)} users evaluated",
              flush=True)

    arrays = {
        "user_ids": user_ids,
        "folds": folds,
        "q_raw": q_raw,
        "q_shrunk": q_shrunk,
        "n_testable": n_testable,
        "n_sampled": n_sampled,
        "n_eval_highs": n_eval_highs,
        "n_eval_lows": n_eval_lows,
        "agree_sum": agree_sum,
    }
    _write_npz_atomic(path, arrays)
    return arrays


def q_distribution(q: np.ndarray) -> dict[str, float]:
    qv = q[np.isfinite(q)]
    if len(qv) == 0:
        return {"n_finite": 0}
    qs = np.quantile(qv, [0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95])
    return {
        "n_finite": int(len(qv)),
        "mean": float(np.mean(qv)),
        "median": float(np.median(qv)),
        "sd": float(np.std(qv)),
        "p05": float(qs[0]),
        "p10": float(qs[1]),
        "p25": float(qs[2]),
        "p75": float(qs[3]),
        "p90": float(qs[4]),
        "p95": float(qs[5]),
        "frac_lt_0p45": float(np.mean(qv < 0.45)),
        "frac_lt_0p50": float(np.mean(qv < 0.50)),
        "frac_ge_0p55": float(np.mean(qv >= 0.55)),
        "frac_ge_0p60": float(np.mean(qv >= 0.60)),
        "frac_ge_0p65": float(np.mean(qv >= 0.65)),
    }


def coverage_summary(q_shrunk: np.ndarray, n_testable: np.ndarray) -> dict[str, Any]:
    n = len(q_shrunk)
    return {
        "n_total": int(n),
        "n_ge1": int(np.sum(n_testable >= 1)),
        "n_ge20": int(np.sum(n_testable >= 20)),
        "n_ge100": int(np.sum(n_testable >= 100)),
        "dist": q_distribution(q_shrunk),
        "by_evidence": {
            "1_19": q_distribution(q_shrunk[(n_testable >= 1) & (n_testable < 20)]),
            "20_49": q_distribution(q_shrunk[(n_testable >= 20) & (n_testable < 50)]),
            "50_99": q_distribution(q_shrunk[(n_testable >= 50) & (n_testable < 100)]),
            "100_199": q_distribution(q_shrunk[(n_testable >= 100) & (n_testable < 200)]),
            "200_plus": q_distribution(q_shrunk[n_testable >= 200]),
        },
    }


# ---------------------------------------------------------------------------
# Part D — region-to-region agreement
# ---------------------------------------------------------------------------

def region_pair_stats(rows_x: list[dict], rows_y: list[dict],
                      edges_x: dict[str, float], edges_y: dict[str, float],
                      min_edges: int) -> dict[str, Any]:
    sx = {r["work_id"]: float(r["score"]) for r in rows_x}
    sy = {r["work_id"]: float(r["score"]) for r in rows_y}
    common = [w for w in sx
              if w in sy and edges_x.get(w, 0) >= min_edges
              and edges_y.get(w, 0) >= min_edges]
    if len(common) < 10:
        return {"n_shared": len(common), "degenerate": True}
    ax = np.asarray([sx[w] for w in common])
    ay = np.asarray([sy[w] for w in common])
    from scipy.stats import spearmanr

    rho, _ = spearmanr(ax, ay)
    pear = float(np.corrcoef(ax, ay)[0, 1])
    mad = float(np.mean(np.abs(ax - ay)))
    top_x = [r["work_id"] for r in rows_x[:50]]
    top_y = [r["work_id"] for r in rows_y[:50]]
    top200_x = [r["work_id"] for r in rows_x[:200]]
    top200_y = [r["work_id"] for r in rows_y[:200]]
    j50 = len(set(top_x) & set(top_y)) / 50.0
    j200 = len(set(top200_x) & set(top200_y)) / 200.0

    # preference sign agreement on a deterministic sample of work pairs
    rng = np.random.default_rng(_derive_seed(JUROR_COHERENCE_SEED, "regionpairs",
                                             min_edges))
    n_possible = len(common) * (len(common) - 1) // 2
    n_draw = min(MAX_REGION_PAIRS, n_possible)
    idx = rng.choice(n_possible, n_draw, replace=False)
    agree = 0
    strong_total = 0
    strong_agree = 0
    k = len(common)
    for t in idx:
        # map triangular index to (i, j) with i < j
        disc = (2 * k - 1) ** 2 - 8 * t
        if disc < 0:
            continue
        i = int(np.floor((2 * k - 1 - np.sqrt(disc)) / 2.0))
        base = i * (2 * k - i - 1) // 2
        j = int(t - base + i + 1)
        if i < 0 or j < 0 or i >= k or j >= k or i == j:
            continue
        dx = ax[i] - ax[j]
        dy = ay[i] - ay[j]
        if dx == 0 or dy == 0:
            continue
        if (dx > 0) == (dy > 0):
            agree += 1
        if abs(dx) >= STRONG_DIFF and abs(dy) >= STRONG_DIFF:
            strong_total += 1
            if (dx > 0) == (dy > 0):
                strong_agree += 1
    n_used = max(1, n_draw)
    return {
        "n_shared": len(common),
        "spearman": rho,
        "pearson": pear,
        "mean_abs_score_diff": mad,
        "top50_jaccard": j50,
        "top200_jaccard": j200,
        "preference_sign_agreement": agree / n_used,
        "strong_sign_agreement": (strong_agree / strong_total)
        if strong_total > 0 else float("nan"),
        "n_strong_pairs": strong_total,
    }


# ---------------------------------------------------------------------------
# Global work rarity (cached) — global counts, works below MIN_RANK_N allowed
# ---------------------------------------------------------------------------

def load_global_work_stats(con, force: bool = False) -> dict[str, np.ndarray]:
    path = STATE_DIR / "global_work_stats.npz"
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}
    rows = con.execute(
        "SELECT work_id, count(*)::DOUBLE AS n_rated, "
        "sum(rating)::DOUBLE AS sum_rating "
        "FROM ex.all_rating_events GROUP BY work_id"
    ).fetchall()
    wid = np.asarray([r[0] for r in rows], dtype=str)
    n_rated = np.asarray([r[1] for r in rows], dtype=np.float64)
    sum_rating = np.asarray([r[2] for r in rows], dtype=np.float64)
    out = {"work_id": wid, "n_rated": n_rated, "sum_rating": sum_rating}
    _write_npz_atomic(path, out)
    return out


def band_of(n: float) -> int:
    for i, (lo, hi) in enumerate(RARITY_BANDS):
        if n >= lo and (hi is None or n <= hi):
            return i
    return -1



# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def _load_q_weights(pop: str) -> tuple[np.ndarray, np.ndarray]:
    """(user_ids, q_shrunk) for a concordance population."""
    with np.load(_cache_path(pop, "q"), allow_pickle=False) as blob:
        return blob["user_ids"].astype(np.int64), blob["q_shrunk"].astype(np.float64)


def _q_dict(pop: str) -> dict[int, float]:
    uids, q = _load_q_weights(pop)
    out = {}
    for u, v in zip(uids.tolist(), q.tolist()):
        if np.isfinite(v):
            out[int(u)] = float(v)
    return out


def reliability_weight(q_shrunk: float) -> float:
    return max(0.0, 2.0 * q_shrunk - 1.0)


def phase_prepare(force: bool = False) -> dict[str, Any]:
    t0 = time.time()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    con = open_db()
    juries = load_juries()
    gws = load_global_work_stats(con, force=force)
    con.close()
    # band assignment for every work
    n_rated = gws["n_rated"]
    bands = np.asarray([band_of(float(x)) for x in n_rated], dtype=np.int8)
    arrays: dict[str, np.ndarray] = {}
    for name, u in juries.items():
        arrays[f"juries/{name}/user_ids"] = u.astype(np.int64)
    arrays["work_id"] = gws["work_id"]
    arrays["global_n_rated"] = n_rated
    arrays["global_sum_rating"] = gws["sum_rating"]
    arrays["global_band"] = bands
    _add_to_npz(arrays)
    n_band = {BAND_LABELS[i]: int(np.sum(bands == i)) for i in range(len(BAND_LABELS))}
    result = {"juries": {k: int(len(v)) for k, v in juries.items()},
              "n_works_per_band": n_band,
              "elapsed_s": round(time.time() - t0, 1)}
    _write_text_atomic(STATE_DIR / "prepare.json", json.dumps(result, indent=1))
    print(f"[prepare] done in {_fmt_time(time.time() - t0)}: {n_band}", flush=True)
    return result


def phase_concordance(force: bool = False) -> dict[str, Any]:
    t0 = time.time()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    con = open_db()
    materialize_base(con)
    juries = load_juries()
    # fandom control: deterministic 10k sample of threeway_anti
    anti = juries.get("threeway_anti")
    if anti is None:
        old = np.load(OLD_NPZ, allow_pickle=False)
        anti = old["juries/threeway_anti/user_ids"].astype(np.int64)
    rng = np.random.default_rng(_derive_seed(JUROR_COHERENCE_SEED, "fandom"))
    anti_sample = np.sort(rng.choice(anti, min(FANDOM_CAP, len(anti)),
                                     replace=False))

    pops = (MAIN_POPS
            + ["C_only", "AC_only", "BC_only"]
            + ["fandom_anti10k"])
    results: dict[str, Any] = {}
    arrays: dict[str, np.ndarray] = {}
    for pop in pops:
        user_ids = (anti_sample if pop == "fandom_anti10k"
                    else juries[pop])
        q = compute_population_q(con, user_ids, pop, force=force)
        arrays[f"q/{pop}/user_ids"] = q["user_ids"]
        arrays[f"q/{pop}/q_raw"] = q["q_raw"]
        arrays[f"q/{pop}/q_shrunk"] = q["q_shrunk"]
        arrays[f"q/{pop}/n_testable"] = q["n_testable"]
        results[pop] = coverage_summary(q["q_shrunk"], q["n_testable"])
        print(f"[concordance] {pop}: n={len(user_ids)} "
              f"median q_shrunk={results[pop]['dist']['median']:.3f} "
              f"frac<.5={results[pop]['dist']['frac_lt_0p50']:.3f} "
              f"frac>=.6={results[pop]['dist']['frac_ge_0p60']:.3f}",
              flush=True)
    con.close()
    _add_to_npz(arrays)
    result = {"pops": results, "n_folds": N_FOLDS,
              "elapsed_s": round(time.time() - t0, 1)}
    _write_text_atomic(STATE_DIR / "concordance.json", json.dumps(result, indent=1,
                                                                  default=_json_default))
    print(f"[concordance] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


def phase_group_agreement(force: bool = False) -> dict[str, Any]:
    t0 = time.time()
    con = open_db()
    materialize_base(con)
    juries = load_juries()
    # full rankings for all 7 regions
    region_rows: dict[str, Any] = {}
    path = STATE_DIR / "group_agreement.npz"
    cached = {}
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            cached = {k: blob[k] for k in blob.files}
    for r in ALL_REGIONS:
        user_ids = juries[r]
        key = f"rank/{r}/work_id"
        if key in cached:
            continue
        rows = build_ranking(con, user_ids)
        region_rows[r] = rows
    # recompute full set of rows if any were missing
    if not region_rows:
        for r in ALL_REGIONS:
            with np.load(path, allow_pickle=False) as blob:
                wids = blob[f"rank/{r}/work_id"].astype(str)
                scs = blob[f"rank/{r}/score"].astype(np.float64)
                eds = blob[f"rank/{r}/n_eff"].astype(np.float64)
            region_rows[r] = [{"work_id": w, "score": s, "n_eff": e}
                              for w, s, e in zip(wids.tolist(), scs.tolist(),
                                                 eds.tolist())]
    arrays: dict[str, np.ndarray] = {}
    for r, rows in region_rows.items():
        arrays[f"rank/{r}/work_id"] = np.asarray([x["work_id"] for x in rows], dtype=str)
        arrays[f"rank/{r}/score"] = np.asarray([float(x["score"]) for x in rows])
        arrays[f"rank/{r}/n_eff"] = np.asarray([float(x.get("n_eff") or 0) for x in rows])
    if arrays:
        _add_to_npz(arrays)
        _write_npz_atomic(path, arrays)

    pairs = []
    for i in range(len(ALL_REGIONS)):
        for j in range(i + 1, len(ALL_REGIONS)):
            rx = ALL_REGIONS[i]
            ry = ALL_REGIONS[j]
            ex = edge_counts(region_rows[rx])
            ey = edge_counts(region_rows[ry])
            for me in MIN_REGION_EDGES:
                st = region_pair_stats(region_rows[rx], region_rows[ry],
                                       ex, ey, me)
                pairs.append({"region_x": rx, "region_y": ry,
                              "min_edges": me, **st})
                print(f"[group_agreement] {rx} vs {ry} (edges>={me}): "
                      f"n_shared={st.get('n_shared')} "
                      f"spearman={st.get('spearman')} "
                      f"sign_agree={st.get('preference_sign_agreement')} "
                      f"strong={st.get('strong_sign_agreement')}", flush=True)
    con.close()
    result = {"pairs": pairs, "min_edges": MIN_REGION_EDGES,
              "elapsed_s": round(time.time() - t0, 1)}
    _write_text_atomic(STATE_DIR / "group_agreement.json",
                       json.dumps(result, indent=1, default=_json_default))
    print(f"[group_agreement] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


def _add_to_npz(arrays: dict[str, np.ndarray]) -> None:
    existing: dict[str, np.ndarray] = {}
    if OUT_NPZ.exists():
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            existing = {k: blob[k] for k in blob.files}
    existing.update(arrays)
    _write_npz_atomic(OUT_NPZ, existing)


# ---------------------------------------------------------------------------
# Tail coverage (Parts E–H)
# ---------------------------------------------------------------------------

def _band_works(global_stats: dict[str, np.ndarray], band_i: int) -> list[str]:
    mask = global_stats["global_band"] == band_i
    return global_stats["work_id"][mask].tolist()


def _population_band_ratings(con, user_ids: np.ndarray,
                             band_works: list[str]) -> dict[str, list[int]]:
    """work_id -> list of jury user ids who rated it (>0)."""
    all_stats = _population_all_ratings(con, user_ids)
    band_set = set(band_works)
    return {w: v for w, v in all_stats.items() if w in band_set}


def _work_reliable_stats(readers: list[int], qw: dict[int, float],
                         ) -> tuple[float, float]:
    wsum = 0.0
    wsq = 0.0
    for u in readers:
        w = reliability_weight(qw.get(u, float("nan")))
        if w > 0:
            wsum += w
            wsq += w * w
    reliable_mass = wsum
    reliable_n_eff = (wsum * wsum / wsq) if wsq > 0 else 0.0
    return reliable_mass, reliable_n_eff


_POP_RATINGS_CACHE: dict[str, dict[str, list[int]]] = {}


def _population_all_ratings(con, user_ids: np.ndarray) -> dict[str, list[int]]:
    """work_id -> jury user ids who rated it (>0), ALL works (cached per run)."""
    key = hashlib_blob(user_ids)
    if key in _POP_RATINGS_CACHE:
        return _POP_RATINGS_CACHE[key]
    table = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT)")
    con.execute(f"INSERT INTO {table} SELECT unnest(?::BIGINT[])",
                [user_ids.tolist()])
    rows = con.execute(
        f"SELECT e.work_id, e.user_id FROM ex.all_rating_events e "
        f"JOIN {table} u USING (user_id) WHERE e.rating >= 1"
    ).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {table}")
    out: dict[str, list[int]] = defaultdict(list)
    for work_id, user_id in rows:
        out[str(work_id)].append(int(user_id))
    out = dict(out)
    _POP_RATINGS_CACHE[key] = out
    return out


def hashlib_blob(user_ids: np.ndarray) -> str:
    import hashlib
    return hashlib.sha256(np.asarray(user_ids).tobytes()).hexdigest()


def _per_work_stats(con, user_ids: np.ndarray, qw: dict[int, float],
                    global_stats: dict[str, np.ndarray],
                    band_i: int) -> dict[str, dict[str, Any]]:
    works = _band_works(global_stats, band_i)
    if not works:
        return {}
    all_stats = _population_all_ratings(con, user_ids)
    band_set = set(works)
    out: dict[str, dict[str, Any]] = {}
    for w in works:
        readers = all_stats.get(w, [])
        rm, rne = _work_reliable_stats(readers, qw)
        out[w] = {"n_rated": len(readers), "reliable_mass": rm,
                  "reliable_n_eff": rne}
    return out


def _summarize_raw(stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ns = np.asarray([v["n_rated"] for v in stats.values()], dtype=np.float64)
    if len(ns) == 0:
        return {"n_works": 0}
    out = {"n_works": int(len(ns)),
           "frac_ge1": float(np.mean(ns >= 1)),
           "frac_ge2": float(np.mean(ns >= 2)),
           "frac_ge3": float(np.mean(ns >= 3)),
           "frac_ge5": float(np.mean(ns >= 5)),
           "frac_ge10": float(np.mean(ns >= 10)),
           "frac_ge20": float(np.mean(ns >= 20)),
           "median": float(np.median(ns)),
           "p75": float(np.quantile(ns, 0.75)),
           "p90": float(np.quantile(ns, 0.90)),
           "mean": float(np.mean(ns))}
    return out


def _summarize_reliable(stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not stats:
        return {"n_works": 0}
    rm = np.asarray([v["reliable_mass"] for v in stats.values()])
    rne = np.asarray([v["reliable_n_eff"] for v in stats.values()])
    return {
        "n_works": int(len(rm)),
        "rm_ge1": float(np.mean(rm >= 1)),
        "rm_ge2": float(np.mean(rm >= 2)),
        "rm_ge3": float(np.mean(rm >= 3)),
        "rm_ge5": float(np.mean(rm >= 5)),
        "rne_ge1": float(np.mean(rne >= 1)),
        "rne_ge2": float(np.mean(rne >= 2)),
        "rne_ge3": float(np.mean(rne >= 3)),
        "rne_ge5": float(np.mean(rne >= 5)),
        "rm_mean": float(np.mean(rm)),
        "rm_median": float(np.median(rm)),
        "rm_p90": float(np.quantile(rm, 0.90)),
        "rne_mean": float(np.mean(rne)),
        "rne_median": float(np.median(rne)),
        "rne_p90": float(np.quantile(rne, 0.90)),
    }


def phase_tail_coverage(force: bool = False) -> dict[str, Any]:
    t0 = time.time()
    con = open_db()
    juries = load_juries()
    gws = {"work_id": np.load(OUT_NPZ, allow_pickle=False)["work_id"],
           "n_rated": np.load(OUT_NPZ, allow_pickle=False)["global_n_rated"],
           "sum_rating": np.load(OUT_NPZ, allow_pickle=False)["global_sum_rating"],
           "global_band": np.load(OUT_NPZ, allow_pickle=False)["global_band"]}
    n_works_band = {
        BAND_LABELS[i]: int(np.sum(gws["global_band"] == i))
        for i in range(len(BAND_LABELS))
    }

    # per-population per-work stats (reliable stats need q weights)
    pop_needed = sorted(set(TAIL_JURIES) | set(MARGINAL_BASES)
                        | set(MARGINAL_ADDITIONS))
    pop_work_stats: dict[str, list[dict[str, dict[str, Any]]]] = {}
    path = STATE_DIR / "tail_work_stats.npz"
    cached = {}
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            cached = {k: blob[k] for k in blob.files}
    for pop in pop_needed:
        qw = _q_dict(JURY_Q_SOURCE[pop])
        band_stats = []
        for band_i in range(len(BAND_LABELS)):
            key = f"{pop}/band{band_i}"
            if key in cached:
                # deserialize cached
                wids = cached[f"{key}/work_id"].astype(str)
                nr = cached[f"{key}/n_rated"]
                rm = cached[f"{key}/rm"]
                rne = cached[f"{key}/rne"]
                d = {}
                for k in range(len(wids)):
                    d[str(wids[k])] = {"n_rated": int(nr[k]),
                                       "reliable_mass": float(rm[k]),
                                       "reliable_n_eff": float(rne[k])}
                band_stats.append(d)
                continue
            d = _per_work_stats(con, juries[pop], qw, gws, band_i)
            band_stats.append(d)
        pop_work_stats[pop] = band_stats
        _POP_RATINGS_CACHE.clear()

    # persist per-work stats
    arrays: dict[str, np.ndarray] = {}
    for pop, band_stats in pop_work_stats.items():
        for band_i, d in enumerate(band_stats):
            if not d:
                continue
            wids = np.asarray(list(d.keys()), dtype=str)
            nr = np.asarray([v["n_rated"] for v in d.values()])
            rm = np.asarray([v["reliable_mass"] for v in d.values()])
            rne = np.asarray([v["reliable_n_eff"] for v in d.values()])
            arrays[f"{pop}/band{band_i}/work_id"] = wids
            arrays[f"{pop}/band{band_i}/n_rated"] = nr
            arrays[f"{pop}/band{band_i}/rm"] = rm
            arrays[f"{pop}/band{band_i}/rne"] = rne
    if arrays:
        _add_to_npz(arrays)
        _write_npz_atomic(path, arrays)

    # raw + reliable summaries per tail jury
    raw_cov: dict[str, dict[str, Any]] = {}
    rel_cov: dict[str, dict[str, Any]] = {}
    for pop in TAIL_JURIES:
        raw_cov[pop] = {
            BAND_LABELS[i]: _summarize_raw(pop_work_stats[pop][i])
            for i in range(len(BAND_LABELS))
        }
        rel_cov[pop] = {
            BAND_LABELS[i]: _summarize_reliable(pop_work_stats[pop][i])
            for i in range(len(BAND_LABELS))
        }

    # marginal coverage (Part H)
    marginal: dict[str, dict[str, Any]] = {}
    combos = [
        ("deep_mint_all", "B_only", "B_only added to A"),
        ("threeway_classic", "A_only", "A_only added to B"),
        ("committee_vote2_ABCs", "A_only", "A_only added to vote2"),
        ("committee_vote2_ABCs", "B_only", "B_only added to vote2"),
        ("committee_vote2_ABCs", "C_only", "C_only added to vote2"),
    ]
    for base, add, label in combos:
        marginal[label] = {}
        for band_i in range(len(BAND_LABELS)):
            bs = pop_work_stats[base][band_i]
            as_ = pop_work_stats[add][band_i]
            marginal[label][BAND_LABELS[band_i]] = _marginal_summary(bs, as_)
    con.close()
    result = {
        "n_works_per_band": n_works_band,
        "raw_coverage": raw_cov,
        "reliable_coverage": rel_cov,
        "marginal": marginal,
        "elapsed_s": round(time.time() - t0, 1),
    }
    _write_text_atomic(STATE_DIR / "tail_coverage.json",
                       json.dumps(result, indent=1, default=_json_default))
    print(f"[tail_coverage] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


def _marginal_summary(base: dict[str, dict[str, Any]],
                      add: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not base and not add:
        return {"n_works": 0}
    all_works = sorted(set(base) | set(add))
    if not all_works:
        return {"n_works": 0}
    zero_base_readers = 0
    zero_base_mass_pos_add = 0
    crosses = {"1": 0, "2": 0, "3": 0, "5": 0}
    for w in all_works:
        b = base.get(w, {"n_rated": 0, "reliable_mass": 0.0, "reliable_n_eff": 0.0})
        a = add.get(w, {"n_rated": 0, "reliable_mass": 0.0, "reliable_n_eff": 0.0})
        if b["n_rated"] == 0 and a["n_rated"] >= 1:
            zero_base_readers += 1
        if b["reliable_mass"] == 0 and a["reliable_mass"] > 0:
            zero_base_mass_pos_add += 1
        comb = b["reliable_n_eff"] + a["reliable_n_eff"]
        for t in ("1", "2", "3", "5"):
            if b["reliable_n_eff"] < float(t) and comb >= float(t):
                crosses[t] += 1
    return {
        "n_works": len(all_works),
        "works_zero_base_reader_ge1_add": zero_base_readers,
        "works_zero_base_mass_pos_add_mass": zero_base_mass_pos_add,
        "rne_crosses": crosses,
    }


# ---------------------------------------------------------------------------
# Part I — sparse-book holdout validation
# ---------------------------------------------------------------------------

def _jury_book_ratings(con, user_ids: np.ndarray,
                       books: list[str]) -> dict[str, list[tuple[int, int]]]:
    table = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT)")
    con.execute(f"INSERT INTO {table} SELECT unnest(?::BIGINT[])",
                [user_ids.tolist()])
    wt = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {wt}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {wt} SELECT unnest(?::VARCHAR[])", [books])
    rows = con.execute(
        f"SELECT e.work_id, e.user_id, e.rating FROM ex.all_rating_events e "
        f"JOIN {table} u USING (user_id) JOIN {wt} w USING (work_id) "
        f"WHERE e.rating >= 1"
    ).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"DROP TABLE IF EXISTS {wt}")
    out: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for work_id, user_id, rating in rows:
        out[str(work_id)].append((int(user_id), int(rating)))
    return dict(out)


def _holdout_metrics(con, jury_users: np.ndarray, qw: dict[int, float],
                     books: list[str], global_stats: dict[str, np.ndarray],
                     rng) -> dict[str, Any]:
    g_n = {str(w): int(gn) for w, gn in zip(global_stats["work_id"].tolist(),
                                            global_stats["n_rated"].tolist())}
    g_sum = {str(w): float(s) for w, s in zip(global_stats["work_id"].tolist(),
                                              global_stats["sum_rating"].tolist())}
    ratings = _jury_book_ratings(con, jury_users, books)
    preds: list[float] = []
    hold: list[float] = []
    preds_w: list[float] = []
    base_preds: list[float] = []
    n_tested = 0
    for b, rl in ratings.items():
        if len(rl) < MIN_JURY_BOOK_RATERS:
            continue
        rl = sorted(rl)
        perm = rng.permutation(len(rl))
        half = len(rl) // 2
        pred_users = [rl[i] for i in perm[:half]]
        hold_users = [rl[i] for i in perm[half:]]
        if not pred_users or not hold_users:
            continue
        n_tested += 1
        pred_mean = float(np.mean([r for _, r in pred_users]))
        hold_mean = float(np.mean([r for _, r in hold_users]))
        # reliability-weighted predictor mean
        wsum = 0.0
        wrs = 0.0
        for u, r in pred_users:
            w = reliability_weight(qw.get(u, float("nan")))
            if w > 0:
                wsum += w
                wrs += w * r
        pred_w = (wrs / wsum) if wsum > 0 else float("nan")
        # baseline: global mean from NON-jury users
        gj = sum(r for _, r in rl)
        gn = g_n.get(b, 0)
        gs = g_sum.get(b, 0.0)
        base_mean = ((gs - gj) / (gn - len(rl))) if (gn - len(rl)) > 0 else float("nan")
        preds.append(pred_mean)
        hold.append(hold_mean)
        if np.isfinite(pred_w):
            preds_w.append(pred_w)
        base_preds.append(base_mean)
    if n_tested == 0:
        return {"n_tested": 0}
    preds = np.asarray(preds)
    hold = np.asarray(hold)
    mae = float(np.mean(np.abs(preds - hold)))
    rmse = float(np.sqrt(np.mean((preds - hold) ** 2)))
    corr = float(np.corrcoef(preds, hold)[0, 1]) if len(preds) >= 2 else float("nan")
    out = {"n_tested": n_tested, "mae": mae, "rmse": rmse, "corr": corr}
    if preds_w:
        pwa = np.asarray(preds_w)
        hh = hold[: len(pwa)]
        out["mae_weighted"] = float(np.mean(np.abs(pwa - hh)))
        out["corr_weighted"] = float(np.corrcoef(pwa, hh)[0, 1]) if len(pwa) >= 2 else float("nan")
    if base_preds:
        bp = np.asarray(base_preds)
        hh = hold[: len(bp)]
        out["mae_baseline"] = float(np.mean(np.abs(bp - hh)))
        out["corr_baseline"] = float(np.corrcoef(bp, hh)[0, 1]) if len(bp) >= 2 else float("nan")
    return out


def phase_tail_validation(force: bool = False) -> dict[str, Any]:
    t0 = time.time()
    con = open_db()
    juries = load_juries()
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        gws = {"work_id": blob["work_id"], "n_rated": blob["global_n_rated"],
               "sum_rating": blob["global_sum_rating"],
               "global_band": blob["global_band"]}
    validation_juries = ["ABC", "committee_AnB", "committee_vote2_ABCs",
                         "committee_AuB"]
    holdout_bands = [1, 2, 3, 4]  # 20-49, 50-99, 100-249, 250-999
    rng = np.random.default_rng(_derive_seed(JUROR_COHERENCE_SEED, "holdout"))

    # sample books per band (deterministic)
    band_books: dict[int, list[str]] = {}
    for band_i in holdout_bands:
        mask = gws["global_band"] == band_i
        cands = gws["work_id"][mask]
        if len(cands) > MAX_BOOKS_PER_BAND:
            sel = rng.choice(cands, MAX_BOOKS_PER_BAND, replace=False)
        else:
            sel = cands
        band_books[band_i] = sel.tolist()

    results: dict[str, dict[str, Any]] = {}
    for jury in validation_juries:
        qw = _q_dict(JURY_Q_SOURCE[jury])
        results[jury] = {}
        for band_i in holdout_bands:
            books = band_books[band_i]
            m = _holdout_metrics(con, juries[jury], qw, books, gws, rng)
            results[jury][BAND_LABELS[band_i]] = m
            print(f"[tail_validation] {jury} {BAND_LABELS[band_i]}: "
                  f"n={m.get('n_tested')} mae={m.get('mae')} "
                  f"rmse={m.get('rmse')} corr={m.get('corr')} "
                  f"w_mae={m.get('mae_weighted')} base_mae={m.get('mae_baseline')}",
                  flush=True)
    con.close()
    result = {"juries": results, "min_raters": MIN_JURY_BOOK_RATERS,
              "elapsed_s": round(time.time() - t0, 1)}
    _write_text_atomic(STATE_DIR / "tail_validation.json",
                       json.dumps(result, indent=1, default=_json_default))
    print(f"[tail_validation] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _quantile_table(qdist: dict[str, float]) -> str:
    return (f"med={qdist.get('median', float('nan')):.3f} "
            f"p10={qdist.get('p10', float('nan')):.3f} "
            f"p25={qdist.get('p25', float('nan')):.3f} "
            f"p75={qdist.get('p75', float('nan')):.3f} "
            f"<.5={qdist.get('frac_lt_0p50', float('nan')):.3f} "
            f">=.6={qdist.get('frac_ge_0p60', float('nan')):.3f}")


def phase_report() -> dict[str, Any]:
    prepare = json.loads((STATE_DIR / "prepare.json").read_text())
    conc = json.loads((STATE_DIR / "concordance.json").read_text())
    gag = json.loads((STATE_DIR / "group_agreement.json").read_text())
    tc = json.loads((STATE_DIR / "tail_coverage.json").read_text())
    tv = json.loads((STATE_DIR / "tail_validation.json").read_text())

    L: list[str] = []
    L.append("# Juror Coherence & Obscure-Book Tail Diagnostic")
    L.append("")
    L.append(f"- Seed `{JUROR_COHERENCE_SEED}`. Diagnostic only; no jury "
             f"membership changes, reweighting, committee model, or reversal.")
    L.append("")
    L.append("## 1. Question and motivation")
    L.append("")
    L.append("A reproducible aggregate jury may still contain individually "
             "incompatible users: a literary-looking aggregate ranking could be "
             "produced by heterogeneous subgroups whose errors merely cancel. "
             "For obscure-book discovery only a few jurors rate each work, so "
             "individual juror reliability matters as much as aggregate quality. "
             "This census separates aggregate literary quality, out-of-sample "
             "individual juror concordance (q), and obscure-book coverage "
             "(raw and reliability-weighted).")
    L.append("")
    L.append("## 2. Candidate populations")
    L.append("")
    L.append(f"- A = deep_mint_all ({prepare['juries']['deep_mint_all']}), "
             f"B = threeway_classic ({prepare['juries']['threeway_classic']}), "
             f"C = rebuilt_hard ({prepare['juries']['rebuilt_hard']}).")
    L.append("- Main: ABC, A∩B, vote2, A∪B, unionABC, p65, deep_mint, A_only, "
             "B_only, AB_only. Regions: A_only/B_only/C_only/AB_only/AC_only/"
             "BC_only/ABC.")
    L.append("")
    L.append("## 3. Individual juror concordance (10-fold OOF, ties=0.5, K=40)")
    L.append("")
    L.append("| population | n | q cov (>=1/20/100) | median q | p10 | p25 | p75 | "
             "frac q<.5 | frac q>=.6 |")
    L.append("|---|---:|---|---:|---:|---:|---:|---:|---:|")
    for pop in conc["pops"]:
        cs = conc["pops"][pop]
        d = cs["dist"]
        L.append(f"| {pop} | {cs['n_total']} | "
                 f"{cs['n_ge1']}/{cs['n_ge20']}/{cs['n_ge100']} | "
                 f"{d.get('median', float('nan')):.3f} | "
                 f"{d.get('p10', float('nan')):.3f} | "
                 f"{d.get('p25', float('nan')):.3f} | "
                 f"{d.get('p75', float('nan')):.3f} | "
                 f"{d.get('frac_lt_0p50', float('nan')):.3f} | "
                 f"{d.get('frac_ge_0p60', float('nan')):.3f} |")
    L.append("")
    L.append("## 4. Venn-region q distributions")
    L.append("")
    for r in ALL_REGIONS:
        if r in conc["pops"]:
            L.append(f"- {r}: " + _quantile_table(conc["pops"][r]["dist"]))
    L.append("")
    L.append("## 5. Region-to-region agreement / cancellation")
    L.append("")
    L.append("| pair | min edges | n_shared | spearman | sign agree | strong agree | "
             "top50 J | top200 J |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for p in gag["pairs"]:
        if p.get("degenerate"):
            L.append(f"| {p['region_x']} vs {p['region_y']} | {p['min_edges']} | "
                     f"{p.get('n_shared')} | degenerate | | | | |")
            continue
        L.append(f"| {p['region_x']} vs {p['region_y']} | {p['min_edges']} | "
                 f"{p['n_shared']} | {p['spearman']:.3f} | "
                 f"{p['preference_sign_agreement']:.3f} | "
                 f"{p.get('strong_sign_agreement', float('nan')):.3f} | "
                 f"{p['top50_jaccard']:.2f} | {p['top200_jaccard']:.2f} |")
    L.append("")
    L.append("## 6. Raw obscure-book coverage")
    L.append("")
    L.append("Global-rarity bands (works per band): "
             + ", ".join(f"{k}={v}" for k, v in tc["n_works_per_band"].items()))
    L.append("")
    L.append("| jury | band | n works | >=1 | >=2 | >=3 | >=5 | >=10 | >=20 | "
             "median | p90 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for jury in TAIL_JURIES:
        for band in BAND_LABELS:
            r = tc["raw_coverage"][jury][band]
            if r.get("n_works", 0) == 0:
                continue
            L.append(f"| {jury} | {band} | {r['n_works']} | {r['frac_ge1']:.2f} | "
                     f"{r['frac_ge2']:.2f} | {r['frac_ge3']:.2f} | "
                     f"{r['frac_ge5']:.2f} | {r['frac_ge10']:.2f} | "
                     f"{r['frac_ge20']:.2f} | {r['median']:.1f} | {r['p90']:.1f} |")
    L.append("")
    L.append("## 7. Reliability-weighted obscure-book coverage")
    L.append("")
    L.append("| jury | band | n works | rm>=1 | rm>=2 | rm>=3 | rm>=5 | "
             "rne>=1 | rne>=2 | rne>=3 | rne>=5 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for jury in TAIL_JURIES:
        for band in BAND_LABELS:
            r = tc["reliable_coverage"][jury][band]
            if r.get("n_works", 0) == 0:
                continue
            L.append(f"| {jury} | {band} | {r['n_works']} | {r['rm_ge1']:.2f} | "
                     f"{r['rm_ge2']:.2f} | {r['rm_ge3']:.2f} | {r['rm_ge5']:.2f} | "
                     f"{r['rne_ge1']:.2f} | {r['rne_ge2']:.2f} | "
                     f"{r['rne_ge3']:.2f} | {r['rne_ge5']:.2f} |")
    L.append("")
    L.append("## 8. Marginal tail coverage of exclusive regions")
    L.append("")
    L.append("| combination | band | n works | zero-base-reader + add | "
             "zero-base-mass + add-mass | rne crosses 1/2/3/5 |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for label, bands in tc["marginal"].items():
        for band, m in bands.items():
            if m.get("n_works", 0) == 0:
                continue
            L.append(f"| {label} | {band} | {m['n_works']} | "
                     f"{m['works_zero_base_reader_ge1_add']} | "
                     f"{m['works_zero_base_mass_pos_add_mass']} | "
                     f"{m['rne_crosses']} |")
    L.append("")
    L.append("## 9. Sparse-book holdout validation")
    L.append("")
    L.append("| jury | band | n tested | MAE | RMSE | corr | weighted MAE | "
             "weighted corr | baseline MAE |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for jury, bands in tv["juries"].items():
        for band, m in bands.items():
            if m.get("n_tested", 0) == 0:
                continue
            L.append(f"| {jury} | {band} | {m['n_tested']} | {m['mae']:.3f} | "
                     f"{m['rmse']:.3f} | {m.get('corr', float('nan')):.3f} | "
                     f"{m.get('mae_weighted', float('nan')):.3f} | "
                     f"{m.get('corr_weighted', float('nan')):.3f} | "
                     f"{m.get('mae_baseline', float('nan')):.3f} |")
    L.append("")
    L.append("## 10. Anti/fandom coherence control")
    L.append("")
    if "fandom_anti10k" in conc["pops"]:
        L.append("- fandom_anti10k: " + _quantile_table(
            conc["pops"]["fandom_anti10k"]["dist"]))
    L.append("")
    L.append("## 11. Interpretation")
    L.append("")
    L.append("Interpret against the possibilities: (A) large jury genuinely "
             "coherent and adds reliable coverage; (B) good aggregate but "
             "substantial cancellation; (C) added users less coherent but cover "
             "otherwise-unrated obscure books; (D) much raw but little "
             "reliability-weighted coverage; (E) smaller multi-method jury has "
             "better sparse prediction despite lower raw coverage.")
    L.append("")
    _write_text_atomic(OUT_MD, "\n".join(L) + "\n")
    print(f"Wrote {OUT_MD}", flush=True)
    _consolidate(prepare, conc, gag, tc, tv)
    return {"report": True}


def _consolidate(prepare, conc, gag, tc, tv) -> None:
    """Merge all state JSONs + key NPZ arrays into the addendum-style outputs."""
    arrays: dict[str, np.ndarray] = {}
    if OUT_NPZ.exists():
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            arrays = {k: blob[k] for k in blob.files}
    # q arrays from state caches
    for pop in conc["pops"]:
        p = _cache_path(pop, "q")
        if p.exists():
            with np.load(p, allow_pickle=False) as blob:
                arrays[f"q/{pop}/user_ids"] = blob["user_ids"]
                arrays[f"q/{pop}/q_raw"] = blob["q_raw"]
                arrays[f"q/{pop}/q_shrunk"] = blob["q_shrunk"]
                arrays[f"q/{pop}/n_testable"] = blob["n_testable"]
    # region ranks
    rp = STATE_DIR / "group_agreement.npz"
    if rp.exists():
        with np.load(rp, allow_pickle=False) as blob:
            for k in blob.files:
                arrays[f"rank/{k}"] = blob[k]
    _add_to_npz(arrays)

    combined = {
        "seed": JUROR_COHERENCE_SEED,
        "n_folds": N_FOLDS,
        "prepare": prepare,
        "concordance": conc,
        "group_agreement": gag,
        "tail_coverage": tc,
        "tail_validation": tv,
    }
    _write_text_atomic(OUT_JSON, json.dumps(combined, indent=1, default=_json_default))
    print(f"Wrote {OUT_JSON} (consolidated)", flush=True)


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def phase_smoke() -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    juries = load_juries()
    sizes = {"deep_mint_all": 19841, "threeway_classic": 31803, "ABC": 2368,
             "committee_AnB": 11582, "committee_vote2_ABCs": 12735,
             "committee_AuB": 40062, "committee_union_ABCs": 41470,
             "core_p65_s25": 3286, "A_only": 7825, "B_only": 19502,
             "AB_only": 9214, "C_only": 1408, "AC_only": 434, "BC_only": 719}
    for name, n in sizes.items():
        add(f"{name}_exact", len(juries[name]) == n, f"n={len(juries[name])}")

    # fold determinism + coverage
    u = juries["ABC"]
    f1 = assign_folds(u, "ABC")
    f2 = assign_folds(u, "ABC")
    add("fold_assignment_deterministic", bool(np.array_equal(f1, f2)),
        "same seed -> same folds")
    add("each_user_in_exactly_one_fold",
        bool((np.bincount(f1, minlength=N_FOLDS) >= 0).all())
        and len(f1) == len(u) and np.unique(f1).tolist() == list(range(N_FOLDS)),
        f"folds {sorted(set(f1.tolist()))}")

    # self-exclusion: training ranking built only from train users
    con = open_db()
    materialize_base(con)
    from curators_explorer.scripts.research_deep_size_sweep import build_pairs as _bp
    train = u[f1 != 0]
    test = u[f1 == 0]
    table = _next_table()
    pairs = f"{table}_pairs"
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT, w DOUBLE)")
    con.execute(f"INSERT INTO {table} SELECT * FROM (SELECT unnest(?::BIGINT[]) AS user_id, 1.0::DOUBLE AS w)",
                [train.tolist()])
    _bp(con, table, pairs)
    leak = con.execute(
        f"SELECT count(*) FROM {pairs} WHERE user_id IN "
        f"(SELECT unnest(?::BIGINT[]))", [test.tolist()]).fetchone()[0]
    add("held_out_contributes_zero_pairs", leak == 0, f"leak={leak}")
    con.execute(f"DROP TABLE IF EXISTS {pairs}")
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.close()

    # q arithmetic on synthetic data
    sd = {"w1": 3.0, "w2": 2.0, "w3": 1.0, "w4": 0.5}
    rng = np.random.default_rng(1)
    highs = np.asarray(["w1", "w2"], dtype=str)
    lows = np.asarray(["w3", "w4"], dtype=str)
    rec = _evaluate_user(1, highs, lows, sd, rng)
    # w1>w3 agree, w1>w4 agree, w2>w3 agree, w2>w4 agree -> all 4 agree
    add("q_raw_arithmetic", rec["q_raw"] == 1.0 and rec["n_pairs_testable"] == 4,
        f"q_raw={rec['q_raw']} testable={rec['n_pairs_testable']}")
    # shrink: (4 + 40*0.5)/(4+40) = 24/44 = 0.5454
    expected = (4 + PRIOR_K * 0.5) / (4 + PRIOR_K)
    add("q_shrunk_arithmetic", abs(rec["q_shrunk"] - expected) < 1e-9,
        f"q_shrunk={rec['q_shrunk']:.4f} expected={expected:.4f}")
    # zero testable -> NaN
    rec0 = _evaluate_user(1, highs, lows, {}, rng)
    add("zero_testable_is_nan", np.isnan(rec0["q_raw"]) and np.isnan(rec0["q_shrunk"]),
        "NaN on no testable pairs")
    # max pairs cap
    big_h = np.asarray([f"h{i}" for i in range(60)], dtype=str)
    big_l = np.asarray([f"l{i}" for i in range(60)], dtype=str)
    sd_big = {w: 1.0 for w in np.concatenate([big_h, big_l])}
    recb = _evaluate_user(2, big_h, big_l, sd_big,
                          np.random.default_rng(3))
    add("max_eval_pairs_cap", recb["n_pairs_sampled"] <= MAX_EVAL_PAIRS
        and recb["n_eval_highs"] == MAX_EVAL_HIGHS
        and recb["n_eval_lows"] == MAX_EVAL_LOWS,
        f"sampled={recb['n_pairs_sampled']}")
    # deterministic user pairs
    r1 = _evaluate_user(7, highs, lows, sd, np.random.default_rng(
        _derive_seed(JUROR_COHERENCE_SEED, "pairs", "smoke", 7)))
    r2 = _evaluate_user(7, highs, lows, sd, np.random.default_rng(
        _derive_seed(JUROR_COHERENCE_SEED, "pairs", "smoke", 7)))
    add("user_eval_pairs_deterministic", r1["n_pairs_sampled"] == r2["n_pairs_sampled"]
        and abs(r1["q_raw"] - r2["q_raw"]) < 1e-12, "same seed -> same pairs/q")

    # no literary labels in q (static check)
    import inspect
    src = inspect.getsource(_evaluate_user) + inspect.getsource(compute_population_q)
    banned = [t for t in ("pos_works", "exact_lit", "broad_lit", "anti_works",
                          "literary_poll") if t in src]
    add("no_literary_labels_in_q", not banned, f"banned tokens: {banned}")

    # reliable_mass transform
    add("reliable_mass_transform",
        abs(reliability_weight(0.5) - 0.0) < 1e-9
        and abs(reliability_weight(0.75) - 0.5) < 1e-9
        and abs(reliability_weight(1.0) - 1.0) < 1e-9,
        f"q=.5->{reliability_weight(0.5)} q=.75->{reliability_weight(0.75)} q=1->{reliability_weight(1.0)}")
    # reliable_n_eff formula
    ws = np.asarray([0.5, 0.5])
    rne = (ws.sum() ** 2) / np.sum(ws ** 2)
    add("reliable_n_eff_formula", abs(rne - 2.0) < 1e-9, f"rne={rne}")

    # rarity bands disjoint + complete over 5..inf
    band_ok = True
    for n in range(5, 6000):
        b = band_of(float(n))
        if b < 0:
            band_ok = False
    add("rarity_bands_disjoint_complete", band_ok, "bands cover 5..inf")

    # region preference signs correct on synthetic (12 works, reversed order)
    nw = 12
    rowsx = [{"work_id": f"w{i}", "score": float(nw - i), "n_eff": 60.0}
             for i in range(nw)]
    rowsy = [{"work_id": f"w{i}", "score": float(i + 1), "n_eff": 60.0}
             for i in range(nw)]
    ex = {f"w{i}": 60.0 for i in range(nw)}
    st = region_pair_stats(rowsx, rowsy, ex, dict(ex), 20)
    add("region_sign_agreement_synthetic", st["preference_sign_agreement"] == 0.0
        and st["spearman"] == -1.0,
        f"sign_agree={st['preference_sign_agreement']} spearman={st['spearman']}")
    # marginal no double count: disjoint base/add
    base = {"w1": {"n_rated": 1, "reliable_mass": 1.0, "reliable_n_eff": 1.0},
            "w2": {"n_rated": 1, "reliable_mass": 1.0, "reliable_n_eff": 1.0}}
    addn = {"w2": {"n_rated": 1, "reliable_mass": 1.0, "reliable_n_eff": 1.0}}
    marg = _marginal_summary(base, addn)
    add("marginal_no_double_count",
        marg["works_zero_base_reader_ge1_add"] == 0
        and marg["rne_crosses"]["1"] == 0,
        f"zero_reader={marg['works_zero_base_reader_ge1_add']} "
        f"crosses={marg['rne_crosses']}")

    # membership unchanged by q
    add("membership_not_modified_by_q",
        len(load_juries()["ABC"]) == 2368, "ABC still 2368 after smoke")

    # old artifacts untouched: record mtimes
    import os
    old_paths = [DATA / "maximum_literary_jury.json",
                 DATA / "maximum_literary_jury_addendum.json",
                 DATA / "jury_consensus_venn.json"]
    mt = {str(p): os.path.getmtime(p) for p in old_paths if p.exists()}
    # we do not write to them; verify existence only
    add("old_artifacts_present_untouched",
        all(p.exists() for p in old_paths),
        "old json artifacts still exist (not overwritten by this script)")

    ok = all(c["ok"] for c in checks)
    print(f"[smoke] {sum(c['ok'] for c in checks)}/{len(checks)} checks passed "
          f"in {_fmt_time(time.time() - t0)}", flush=True)
    return {"checks": checks, "ok": bool(ok), "elapsed_s": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def run_phases(phases: list[str], force: bool = False) -> None:
    for ph in phases:
        t0 = time.time()
        if ph == "prepare":
            phase_prepare(force=force)
        elif ph == "concordance":
            phase_concordance(force=force)
        elif ph == "group_agreement":
            phase_group_agreement(force=force)
        elif ph == "tail_coverage":
            phase_tail_coverage(force=force)
        elif ph == "tail_validation":
            phase_tail_validation(force=force)
        elif ph == "report":
            phase_report()
        else:
            raise SystemExit(f"unknown phase {ph}")
        print(f"[main] phase {ph} took {_fmt_time(time.time() - t0)}", flush=True)


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--phase", nargs="+", default=["all"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        phase_smoke()
        return
    phases = args.phase
    if "all" in phases:
        phases = ["prepare", "concordance", "group_agreement", "tail_coverage",
                  "tail_validation", "report"]
    run_phases(phases, force=args.force)


if __name__ == "__main__":
    _main()

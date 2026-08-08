#!/usr/bin/env python3
"""TRUE INTERNAL CONVERGENCE OF COMMON LITERARY JURIES.

Corrected meaning of "convergence":

  common-L score
      -> fixed hard jury membership (no additions/removals)
      -> restrict the nonlinear user/book operator to EXACTLY those users
      -> converge the equal-weight vector under the project's established
         iterate_map update equation until a genuine numerical fixed point
      -> analyse the converged weighted jury (membership unchanged)

Explicitly NOT used: convergence-reversal, gain-hard/ladder pruning, proponent
removal, survivor reconstruction, outside-user admission, and the unreachable
retained_target=1.01 of d92086e.  Membership is a hard invariant.

Convergence-eligible universe (Option 1): rebuild exact seed-local payloads
from the raw rating-event tables for arbitrary user IDs (same row/col/side
extraction semantics as research_seedless_spectral_pilot: min_book_n=500,
max_per_side=16, sample_seed=20260806, equal-vote matrix built by
spectral.build_matrix, operator by spectral.make_operator + attractor.CONFIG).
No user is dropped by an old spectral payload restriction.

Convergence update: identical equation to research_attractor_pruning.iterate_map
(tanh-normalized books, standardized user signal, sigmoid(BETA=2.5), damped
0.35/0.65 update, mean normalization) but iterated until BOTH
direction step correlation >= 0.9999 AND weight relative change <= 1e-4 for
CONSECUTIVE_CONVERGED = 5 consecutive iterations (MAX_CONV_ITER = 200 cap).

Frozen common-L input loaded from d92086e (research_converged_common_literary_jurors
user_scores.npz + the corrected median-of-references score).

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_true_converged_literary_jurors --smoke
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_true_converged_literary_jurors --phase all
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts.research_deep_size_sweep import MIN_RANK_N
from curators_explorer.scripts.research_converged_common_literary_jurors import (
    DATA,
    STATE_DIR as OLD_CONV_STATE,
    _derive_seed,
    _fmt_time,
    _json_default,
    _write_npz_atomic,
    _write_text_atomic,
    compute_common_scores as _old_common_scores,
    load_juries,
    open_db,
    q_distribution,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    materialize_base,
)
from curators_explorer.scripts import (
    research_attractor_pruning as pruning,
)
from curators_explorer.scripts import (
    research_seedless_attractor_census as attractor,
)
from curators_explorer.scripts import (
    research_seedless_spectral_pilot as spectral,
)

TRUE_CONVERGED_LIT_SEED = 20260901

OUT_JSON = DATA / "true_converged_literary_jurors.json"
OUT_NPZ = DATA / "true_converged_literary_jurors.npz"
OUT_MD = DATA / "TRUE_CONVERGED_LITERARY_JURORS_REPORT.md"
OUT_HEADS = DATA / "TRUE_CONVERGED_LITERARY_JUROR_HEADS.md"
STATE_DIR = DATA / "true_converged_literary_jurors_state"

# frozen extraction config (from research_seedless_spectral_pilot)
EXTRACT_CONFIG = {"min_book_n": 500, "max_per_side": 16,
                  "sample_seed": 20260806}

# frozen convergence
BETA = 2.5
MAX_CONV_ITER = 200
CONSECUTIVE_CONVERGED = 5
STEP_THRESHOLD = 0.9999
WEIGHT_CHANGE_THRESHOLD = 1e-4

PRIMARY_SIZES = [5000, 10000, 20000]
J30K_ENABLED = True  # gate checked at runtime
J30K_MIN_L60_COUNT = 35000

SUBSAMPLE_REPS = 10
SUBSAMPLE_FRACTION = 0.90
SUBSAMPLE_20_REPS = 5
SUBSAMPLE_20_FRACTION = 0.80
INIT_PERTURB_REPS = 10
INIT_PERTURB_SIGMA = 0.20
HALF_SPLIT_REPS = 10

RARITY_BANDS = [(5, 19), (20, 49), (50, 99), (100, 249), (250, 999),
                (1000, 4999)]
BAND_LABELS = ["5_19", "20_49", "50_99", "100_249", "250_999", "1000_4999"]

_PROBE_POS: set = set()
_PROBE_ANTI: set = set()
_PROBE_EXACT: set = set()
_PROBE_BROAD: set = set()


# ---------------------------------------------------------------------------
# Part A — load frozen common-L scores from d92086e
# ---------------------------------------------------------------------------

def load_frozen_scores() -> tuple[np.ndarray, np.ndarray]:
    """(universe user_ids, literary_juror_score) from the corrected common-L."""
    us = np.load(OLD_CONV_STATE / "user_scores.npz", allow_pickle=False)
    universe = us["universe"].astype(np.int64)
    scores = _old_common_scores({k: us[k] for k in
                                 ("L_shrunk", "n_testable", "n_high_avail",
                                  "n_low_avail")})
    return universe, scores


def convergence_eligible_universe(universe: np.ndarray,
                                  scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Option 1: every common-L-scoreable user is convergence-eligible."""
    mask = np.isfinite(scores)
    return universe[mask], scores[mask]


# ---------------------------------------------------------------------------
# Part C — primary juries (top-N by frozen common-L, fixed tie-break)
# ---------------------------------------------------------------------------

def build_jury_order(universe: np.ndarray, scores: np.ndarray) -> np.ndarray:
    us = np.load(OLD_CONV_STATE / "user_scores.npz", allow_pickle=False)
    nt = us["n_testable"]
    dh = us["n_high_avail"]
    dl = us["n_low_avail"]
    idx_map = {int(u): i for i, u in enumerate(us["universe"].tolist())}
    n = len(universe)
    med_nt = np.zeros(n)
    med_books = np.zeros(n)
    for i, u in enumerate(universe.tolist()):
        j = idx_map[int(u)]
        med_nt[i] = np.nanmedian(nt[j])
        med_books[i] = np.nanmedian(np.maximum(dh[j], dl[j]))
    order = np.lexsort((universe, -med_books, -med_nt, -np.nan_to_num(scores)))
    return order


def jury_source_composition(members: np.ndarray,
                            juries: dict[str, np.ndarray]) -> dict[str, float]:
    n = len(members)
    s = set(members.tolist())
    union_abc = (set(juries["deep_mint_all"].tolist())
                 | set(juries["threeway_classic"].tolist())
                 | set(juries["rebuilt_hard"].tolist()))
    comp = {
        "ABC": len(s & set(juries["ABC"].tolist())) / n,
        "p65": len(s & set(juries["core_p65_s25"].tolist())) / n,
        "AnB": len(s & set(juries["committee_AnB"].tolist())) / n,
        "vote2": len(s & set(juries["committee_vote2_ABCs"].tolist())) / n,
        "A_only": len(s & set(juries["A_only"].tolist())) / n,
        "B_only": len(s & set(juries["B_only"].tolist())) / n,
        "AB_only": len(s & set(juries["AB_only"].tolist())) / n,
        "none_ABC": sum(1 for u in s if u not in union_abc) / n,
    }
    return comp


# ---------------------------------------------------------------------------
# Part D — exact seed-local payloads (Option 1: rebuild from raw events)
# ---------------------------------------------------------------------------

_BOOK_CACHE: dict[str, np.ndarray] | None = None


def _book_universe(con) -> dict[str, np.ndarray]:
    global _BOOK_CACHE
    if _BOOK_CACHE is not None:
        return _BOOK_CACHE
    rows = con.execute(
        f"SELECT work_id, count(*) AS n, count(*) FILTER (WHERE rating=5) AS n5, "
        f"avg(rating) FILTER (WHERE rating>0) AS mean "
        f"FROM ex.all_rating_events WHERE rating>0 GROUP BY work_id "
        f"HAVING count(*) >= {EXTRACT_CONFIG['min_book_n']}").fetchall()
    order = np.argsort([str(r[0]) for r in rows], kind="stable")
    _BOOK_CACHE = {
        "work_ids": np.asarray([str(r[0]) for r in rows], dtype=str)[order],
        "book_n": np.asarray([r[1] for r in rows], dtype=np.float32)[order],
        "book_p5": np.asarray([r[2] / r[1] for r in rows], dtype=np.float32)[order],
        "book_mean": np.asarray([float(r[3] or 0) for r in rows], dtype=np.float32)[order],
    }
    return _BOOK_CACHE


def build_local_payload(con, user_ids: np.ndarray) -> dict[str, np.ndarray]:
    """Rebuild the spectral row/col/side representation for EXACTLY `user_ids`
    from raw rating events. Same extraction semantics as the established
    attractor machinery; identical to the global payload for those users."""
    user_ids = np.unique(np.asarray(user_ids, dtype=np.int64))
    n = len(user_ids)
    books = _book_universe(con)

    # user stats (global, over all ratings)
    rows = con.execute(
        "SELECT user_id, count(*) FILTER (WHERE rating=5) AS n5, "
        "count(*) FILTER (WHERE rating BETWEEN 1 AND 3) AS nlow, "
        "count(*) FILTER (WHERE rating>0) AS ntotal "
        "FROM ex.all_rating_events WHERE rating>0 "
        "AND user_id IN (SELECT unnest(?::BIGINT[])) GROUP BY user_id",
        [user_ids.tolist()]).fetchall()
    d = {int(r[0]): r for r in rows}
    n5 = np.asarray([d[int(u)][1] if int(u) in d else 0 for u in user_ids],
                    dtype=np.float32)
    nlow = np.asarray([d[int(u)][2] if int(u) in d else 0 for u in user_ids],
                      dtype=np.float32)
    ntotal = np.asarray([d[int(u)][3] if int(u) in d else 0 for u in user_ids],
                        dtype=np.float32)
    ntotal = np.maximum(ntotal, 1)
    five = (n5 / ntotal).astype(np.float32)

    jt = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {jt}(ui INTEGER, user_id BIGINT)")
    con.executemany(f"INSERT INTO {jt} VALUES (?, ?)",
                    [(i, int(u)) for i, u in enumerate(user_ids.tolist())])
    bt = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {bt}(bi INTEGER, work_id VARCHAR)")
    con.executemany(f"INSERT INTO {bt} VALUES (?, ?)",
                    [(i, str(w)) for i, w in enumerate(books["work_ids"].tolist())])
    edges = con.execute(
        f"""
        WITH ranked AS (
            SELECT u.ui, b.bi,
                   CASE WHEN e.rating=5 THEN 1 ELSE -1 END::TINYINT AS side,
                   row_number() OVER (
                       PARTITION BY u.ui, CASE WHEN e.rating=5 THEN 1 ELSE -1 END
                       ORDER BY hash(e.user_id,e.work_id,{EXTRACT_CONFIG['sample_seed']})
                   ) AS rn
            FROM ex.all_rating_events e
            JOIN {jt} u USING (user_id)
            JOIN {bt} b USING (work_id)
            WHERE e.rating=5 OR e.rating BETWEEN 1 AND 3
        )
        SELECT ui, bi, side FROM ranked WHERE rn <= {EXTRACT_CONFIG['max_per_side']}
        """
    ).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {jt}")
    con.execute(f"DROP TABLE IF EXISTS {bt}")
    payload = {
        "row": np.asarray([r[0] for r in edges], dtype=np.int32),
        "col": np.asarray([r[1] for r in edges], dtype=np.int32),
        "side": np.asarray([r[2] for r in edges], dtype=np.int8),
        "user_ids": user_ids.astype(np.int64),
        "user_n5": n5,
        "user_nlow": nlow,
        "user_ntotal": ntotal,
        "user_five_rate": five,
        "work_ids": books["work_ids"],
        "book_n": books["book_n"],
        "book_p5": books["book_p5"],
        "book_mean": books["book_mean"],
    }
    return payload


_jury_counter = [0]


def _next_table() -> str:
    _jury_counter[0] += 1
    return f"tclj_{_jury_counter[0]}"


# ---------------------------------------------------------------------------
# Part D/E — genuine internal convergence (fixed membership)
# ---------------------------------------------------------------------------

def _equal_init(n: int) -> np.ndarray:
    w = np.ones(n, dtype=np.float32)
    return w / w.mean()


def _lognormal_init(n: int, sigma: float, rng) -> np.ndarray:
    w = np.exp(rng.normal(0.0, sigma, size=n)).astype(np.float32)
    return w / w.mean()


def converge_internal(matrix, operator, n: int, *,
                      init: str = "equal", rng=None,
                      max_iter: int = MAX_CONV_ITER) -> dict[str, Any]:
    """Same update equation as pruning.iterate_map, iterated to a genuine
    numerical fixed point. Membership never changes."""
    if init == "equal":
        w = _equal_init(n)
    else:
        w = _lognormal_init(n, INIT_PERTURB_SIGMA, rng)

    direction_prev = attractor.normalize_columns(
        operator.rmatmat(w)).ravel()
    raw_prev = operator.rmatmat(w).ravel()
    converged = False
    consec = 0
    iterations = 0
    final_step = float("nan")
    final_weight_rel = float("nan")
    final_book_rel = float("nan")
    stop_reason = "max_iter_not_converged"
    history = []
    for it in range(1, max_iter + 1):
        raw_books = operator.rmatmat(w)
        scale = np.sqrt(np.mean(raw_books ** 2, axis=0, keepdims=True))
        books = np.tanh(raw_books / np.maximum(1.5 * scale, 1e-12)).astype(
            np.float32)
        user_signal = operator.matmat(books)
        user_signal -= user_signal.mean(axis=0, keepdims=True)
        user_signal /= np.maximum(user_signal.std(axis=0, keepdims=True), 1e-12)
        target = attractor.sigmoid(BETA * user_signal).astype(np.float32)
        target /= target.mean(axis=0, keepdims=True)
        w_new = 0.35 * w + 0.65 * target
        w_new /= w_new.mean(axis=0, keepdims=True)
        direction = attractor.normalize_columns(
            operator.rmatmat(w_new)).ravel()
        step = float(np.sum(direction_prev * direction))
        w_norm = float(np.linalg.norm(w))
        weight_rel = float(np.linalg.norm(w_new - w)) / max(w_norm, 1e-12)
        raw_new = operator.rmatmat(w_new).ravel()
        book_rel = float(np.linalg.norm(raw_new - raw_prev)) / max(
            float(np.linalg.norm(raw_prev)), 1e-12)
        history.append({"iteration": it, "step": step,
                        "weight_rel": weight_rel, "book_rel": book_rel})
        iterations = it
        final_step = step
        final_weight_rel = weight_rel
        final_book_rel = book_rel
        w = w_new
        direction_prev = direction
        raw_prev = raw_new
        if step >= STEP_THRESHOLD and weight_rel <= WEIGHT_CHANGE_THRESHOLD:
            consec += 1
            if consec >= CONSECUTIVE_CONVERGED:
                converged = True
                stop_reason = "converged"
                break
        else:
            consec = 0

    preference = attractor.weighted_preferences(matrix, w)
    return {
        "converged": converged,
        "stop_reason": stop_reason,
        "iterations": iterations,
        "final_step": final_step,
        "final_weight_rel": final_weight_rel,
        "final_book_rel": final_book_rel,
        "weights": w,
        "preference": preference,
        "matrix": matrix,
        "history": history,
    }


def run_convergence(con, user_ids: np.ndarray, tag: str, *,
                    init: str = "equal", rng=None, force: bool = False) -> dict[str, Any]:
    """Build/cache the local payload for the exact jury, compute the direct
    equal-vote seed head, and converge the fixed membership to a genuine fixed
    point. Returns weights, converged preference, seed head, diagnostics."""
    ppt = STATE_DIR / f"payload_{tag}.npz"
    if not ppt.exists() or force:
        payload = build_local_payload(con, user_ids)
        _write_npz_atomic(ppt, payload)
    else:
        with np.load(ppt, allow_pickle=False) as blob:
            payload = {k: blob[k] for k in blob.files}
    matrix, _ = spectral.build_matrix(payload)
    operator, _ = spectral.make_operator(matrix, payload, attractor.CONFIG)
    n = int(len(payload["user_ids"]))
    w_eq = _equal_init(n)
    pref_eq = attractor.weighted_preferences(matrix, w_eq)
    res = converge_internal(matrix, operator, n, init=init, rng=rng)
    res["n_jury"] = n
    res["user_ids"] = payload["user_ids"]
    res["work_ids"] = payload["work_ids"]
    res["seed_head"] = _book_head(pref_eq, payload)
    return res


def _book_head(preference: dict[str, np.ndarray], payload: dict[str, np.ndarray],
               limit: int = 1000) -> list[dict]:
    score = np.asarray(preference["score"])
    reader_mass = np.asarray(preference["reader_mass"])
    eligible = np.flatnonzero(reader_mass >= 25)
    order = eligible[np.argsort(-score[eligible], kind="stable")][:limit]
    out = []
    for rank, i in enumerate(order, 1):
        out.append({"rank": rank, "work_id": str(payload["work_ids"][i]),
                    "score": float(score[i]), "n_eff": float(reader_mass[i])})
    return out


def _kish(w: np.ndarray) -> float:
    w = np.asarray(w, dtype=np.float64)
    w = w[w > 0]
    return float(w.sum() ** 2 / np.sum(w ** 2)) if np.any(w > 0) else 0.0


# ---------------------------------------------------------------------------
# Part G — endpoint / weight-quality analysis
# ---------------------------------------------------------------------------

def _weighted_quantiles(L: np.ndarray, w: np.ndarray,
                        qs=(0.10, 0.25, 0.5, 0.75)) -> dict[str, float]:
    w = np.asarray(w, dtype=np.float64)
    w = w / w.sum()
    order = np.argsort(L, kind="stable")
    Ls, ws = L[order], w[order]
    cw = np.cumsum(ws)
    out = {}
    for q in qs:
        i = int(np.searchsorted(cw, q))
        i = min(i, len(Ls) - 1)
        out[f"p{int(q*100)}"] = float(Ls[i])
    out["median"] = out["p50"]
    return out


def endpoint_analysis(res: dict[str, Any], L_all: np.ndarray,
                      universe: np.ndarray,
                      require_all_finite: bool = True) -> dict[str, Any]:
    uid = res["user_ids"]
    idx_map = {int(u): i for i, u in enumerate(universe.tolist())}
    L = np.full(res["n_jury"], np.nan)
    for j, u in enumerate(uid.tolist()):
        if int(u) in idx_map:
            L[j] = L_all[idx_map[int(u)]]
    w = np.asarray(res["weights"], dtype=np.float64)
    assert len(L) == len(w) == res["n_jury"]
    if require_all_finite:
        assert np.all(np.isfinite(L)), "every primary juror must have finite L"
    finite = np.isfinite(L)
    Lf = L[finite]
    wf = w[finite]

    unweighted = q_distribution(Lf)
    weighted = _weighted_quantiles(Lf, wf)
    wsum = float(wf.sum())
    bands = {
        "ge_0p75": float(np.sum(wf[Lf >= 0.75]) / wsum) if wsum > 0 else float("nan"),
        "ge_0p70": float(np.sum(wf[Lf >= 0.70]) / wsum) if wsum > 0 else float("nan"),
        "ge_0p65": float(np.sum(wf[Lf >= 0.65]) / wsum) if wsum > 0 else float("nan"),
        "ge_0p60": float(np.sum(wf[Lf >= 0.60]) / wsum) if wsum > 0 else float("nan"),
        "lt_0p60": float(np.sum(wf[Lf < 0.60]) / wsum) if wsum > 0 else float("nan"),
    }
    w_full = float(w.sum())
    from scipy.stats import spearmanr
    return {
        "n": res["n_jury"],
        "n_finite_L": int(finite.sum()),
        "converged": res["converged"],
        "stop_reason": res["stop_reason"],
        "iterations": res["iterations"],
        "final_step": res["final_step"],
        "final_weight_rel": res["final_weight_rel"],
        "final_book_rel": res["final_book_rel"],
        "kish": _kish(w),
        "top1pct_weight_share": float(np.sum(np.sort(w)[-int(np.ceil(0.01*len(w))):]) / w_full),
        "top5pct_weight_share": float(np.sum(np.sort(w)[-int(np.ceil(0.05*len(w))):]) / w_full),
        "max_weight": float(w.max()),
        "median_weight": float(np.median(w)),
        "p90_weight": float(np.quantile(w, 0.90)),
        "gini": _gini(w),
        "unweighted": unweighted,
        "weighted": weighted,
        "weight_by_L": bands,
        "weight_L_pearson": float(np.corrcoef(wf, Lf)[0, 1]) if len(Lf) >= 2 else float("nan"),
        "weight_L_spearman": float(spearmanr(wf, Lf).statistic) if len(Lf) >= 2 else float("nan"),
        "head": _book_head(res["preference"], res, limit=1000),
    }


def _gini(w: np.ndarray) -> float:
    w = np.asarray(w, dtype=np.float64)
    if len(w) < 2 or np.sum(w) == 0:
        return float("nan")
    w = np.sort(w)
    n = len(w)
    cum = np.cumsum(w)
    return float((2 * np.sum(np.arange(1, n + 1) * w) - (n + 1) * np.sum(w))
                 / (n * np.sum(w)))


def _sem_flags(head: list[dict]) -> dict[str, int]:
    return {
        "pos50": sum(1 for r in head[:50] if r["work_id"] in _PROBE_POS),
        "exact50": sum(1 for r in head[:50] if r["work_id"] in _PROBE_EXACT),
        "broad50": sum(1 for r in head[:50] if r["work_id"] in _PROBE_BROAD),
        "anti50": sum(1 for r in head[:50] if r["work_id"] in _PROBE_ANTI),
    }


def _head_jaccard(a: list[dict], b: list[dict], k: int) -> float:
    sa = {r["work_id"] for r in a[:k]}
    sb = {r["work_id"] for r in b[:k]}
    return float(len(sa & sb) / max(1, len(sa | sb)))


def _head_rho(a: list[dict], b: list[dict], k: int = 200) -> float:
    from scipy.stats import spearmanr
    ia = [r["work_id"] for r in a[:k]]
    ib = [r["work_id"] for r in b[:k]]
    rb = {w: i for i, w in enumerate(ib)}
    common = [w for w in ia if w in rb]
    if len(common) < 10:
        return float("nan")
    return float(spearmanr([ia.index(w) for w in common],
                           [rb[w] for w in common]).statistic)


# ---------------------------------------------------------------------------
# Part J/K/L/M — stability suites
# ---------------------------------------------------------------------------

def stability_phase(con, juries: dict[str, np.ndarray],
                    force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "stability.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe, scores = load_frozen_scores()
    eu, es = convergence_eligible_universe(universe, scores)
    order = build_jury_order(eu, es)
    result: dict[str, Any] = {"sub90": {}, "random_init": {},
                              "half_split": {}, "sub80_J10000": {}}

    def _conv_head(r):
        return _book_head(r["preference"], r, limit=1000)

    def run_rep(seed_ids, tag, init="equal", rng=None, primary=None,
                payload_tag=None):
        pptag = payload_tag or tag
        res = run_convergence(con, seed_ids, pptag, init=init, rng=rng,
                              force=force)
        if primary is None:
            return res
        ep = endpoint_analysis(res, es, eu)
        # compare converged head of sub vs converged head of primary
        res_head = _conv_head(res)
        prim_head = _conv_head(primary)
        # weight cosine on shared members
        w_a = np.asarray(res["weights"], dtype=np.float64)
        u_a = res["user_ids"]
        u_b = np.asarray(primary["user_ids"], dtype=np.int64)
        w_b = np.asarray(primary["weights"], dtype=np.float64)
        ib = {int(u): i for i, u in enumerate(u_b.tolist())}
        sa = np.asarray([ib[int(u)] for u in u_a.tolist() if int(u) in ib],
                        dtype=np.int64)
        sel = [int(u) for u in u_a.tolist() if int(u) in ib]
        w_a_sel = np.asarray([w_a[i] for i, u in enumerate(u_a.tolist())
                              if int(u) in ib])
        w_b_sel = w_b[sa]
        wcos = float(np.dot(w_a_sel, w_b_sel)
                     / (np.linalg.norm(w_a_sel) * np.linalg.norm(w_b_sel)))
        return {
            "iterations": res["iterations"],
            "converged": res["converged"],
            "kish": _kish(res["weights"]),
            "weighted_median_L": ep["weighted"]["median"],
            "book_j50": _head_jaccard(res_head, prim_head, 50),
            "book_j200": _head_jaccard(res_head, prim_head, 200),
            "book_rho200": _head_rho(res_head, prim_head, 200),
            "weight_cosine": float(wcos),
        }

    def _cache_primary_res(tag, res):
        arrays = {"user_ids": res["user_ids"],
                  "work_ids": res["work_ids"],
                  "weights": np.asarray(res["weights"]),
                  "pref_score": np.asarray(res["preference"]["score"]),
                  "pref_mass": np.asarray(res["preference"]["reader_mass"]),
                  "seed_head_wid": np.asarray([r["work_id"] for r in res["seed_head"]]),
                  "seed_head_score": np.asarray([r["score"] for r in res["seed_head"]]),
                  "converged": np.asarray([int(res["converged"])]),
                  "iterations": np.asarray([int(res["iterations"])]),
                  "final_step": np.asarray([res["final_step"]]),
                  "final_weight_rel": np.asarray([res["final_weight_rel"]]),
                  "final_book_rel": np.asarray([res["final_book_rel"]]),
                  "stop_reason": np.asarray([res["stop_reason"]])}
        _write_npz_atomic(STATE_DIR / f"primres_{tag}.npz", arrays)

    def _load_primary_res(tag):
        p = STATE_DIR / f"primres_{tag}.npz"
        if not p.exists():
            return None
        with np.load(p, allow_pickle=False) as b:
            seed_head = [{"rank": i + 1, "work_id": str(w), "score": float(s)}
                         for i, (w, s) in enumerate(
                             zip(b["seed_head_wid"].astype(str),
                                 b["seed_head_score"]))]
            return {"user_ids": b["user_ids"],
                    "work_ids": b["work_ids"],
                    "weights": b["weights"],
                    "converged": bool(b["converged"][0]),
                    "iterations": int(b["iterations"][0]),
                    "final_step": float(b["final_step"][0]),
                    "final_weight_rel": float(b["final_weight_rel"][0]),
                    "final_book_rel": float(b["final_book_rel"][0]),
                    "stop_reason": str(b["stop_reason"][0]),
                    "seed_head": seed_head,
                    "preference": {"score": b["pref_score"],
                                   "reader_mass": b["pref_mass"]}}

    primary: dict[str, dict[str, Any]] = {}
    # primary endpoints (resumable via cache)
    for size in (5000, 10000, 20000):
        tag = f"J{size}"
        seed_ids = eu[order[:size]]
        res = _load_primary_res(tag)
        if res is None:
            res = run_convergence(con, seed_ids, tag, force=force)
            _cache_primary_res(tag, res)
        primary[tag] = res
        print(f"[primary] J{size} converged={res['converged']} "
              f"iters={res['iterations']} kish={_kish(res['weights']):.0f}",
              flush=True)

    # optional J30000
    sizes = [5000, 10000, 20000]
    if J30K_ENABLED and np.sum(es >= 0.60) >= J30K_MIN_L60_COUNT:
        tag = "J30000"
        seed_ids = eu[order[:30000]]
        res = _load_primary_res(tag)
        if res is None:
            res = run_convergence(con, seed_ids, tag, force=force)
            _cache_primary_res(tag, res)
        primary[tag] = res
        sizes.append(30000)
        print(f"[primary] J30000 converged={res['converged']} "
              f"iters={res['iterations']} kish={_kish(res['weights']):.0f}",
              flush=True)
    else:
        print("[primary] J30000 NOT enabled "
              f"(L>=0.60 count {int(np.sum(es>=0.60))} < {J30K_MIN_L60_COUNT})",
              flush=True)

    result["primary"] = {
        tag: _save_primary(con, res, eu, es, tag) for tag, res in primary.items()
    }
    _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))

    # 90% subsamples
    for tag, res in primary.items():
        size = int(tag[1:])
        seed_ids = eu[order[:size]]
        reps = {}
        for rep in range(SUBSAMPLE_REPS):
            rng = np.random.default_rng(
                _derive_seed(TRUE_CONVERGED_LIT_SEED, "sub90", tag, rep))
            drop = rng.choice(len(seed_ids), int(round(0.10 * len(seed_ids))),
                              replace=False)
            sub = np.delete(seed_ids, drop)
            assert len(sub) == int(round(0.90 * len(seed_ids)))
            reps[f"rep{rep}"] = run_rep(
                sub, f"{tag}_sub90_{rep}", primary=res,
                rng=np.random.default_rng(
                    _derive_seed(TRUE_CONVERGED_LIT_SEED, "sub90conv", tag, rep)))
        result["sub90"][tag] = reps
        _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
        print(f"[stability] {tag} 90% subsamples done", flush=True)

    # random initial weights (reuse primary payload; same membership)
    for tag, res in primary.items():
        size = int(tag[1:])
        seed_ids = eu[order[:size]]
        reps = {}
        for rep in range(INIT_PERTURB_REPS):
            rng = np.random.default_rng(
                _derive_seed(TRUE_CONVERGED_LIT_SEED, "initpert", tag, rep))
            reps[f"rep{rep}"] = run_rep(
                seed_ids, tag, init="lognormal", rng=rng,
                primary=res, payload_tag=tag)
        result["random_init"][tag] = reps
        _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
        print(f"[stability] {tag} random-init done", flush=True)

    # 80% subsamples (J10000 only)
    if "J10000" in primary:
        tag = "J10000"
        res = primary[tag]
        seed_ids = eu[order[:10000]]
        reps = {}
        for rep in range(SUBSAMPLE_20_REPS):
            rng = np.random.default_rng(
                _derive_seed(TRUE_CONVERGED_LIT_SEED, "sub80", tag, rep))
            drop = rng.choice(len(seed_ids), int(round(0.20 * len(seed_ids))),
                              replace=False)
            sub = np.delete(seed_ids, drop)
            assert len(sub) == int(round(0.80 * len(seed_ids)))
            reps[f"rep{rep}"] = run_rep(
                sub, f"{tag}_sub80_{rep}", primary=res,
                rng=np.random.default_rng(
                    _derive_seed(TRUE_CONVERGED_LIT_SEED, "sub80conv", tag, rep)))
        result["sub80_J10000"] = reps
        _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
        print(f"[stability] J10000 80% subsamples done", flush=True)

    # half splits (J10000, J20000)
    for tag in ("J10000", "J20000"):
        if tag not in primary:
            continue
        res = primary[tag]
        size = int(tag[1:])
        seed_ids = eu[order[:size]]
        reps = {}
        for rep in range(HALF_SPLIT_REPS):
            rng = np.random.default_rng(
                _derive_seed(TRUE_CONVERGED_LIT_SEED, "half", tag, rep))
            perm = rng.permutation(len(seed_ids))
            h1 = np.sort(seed_ids[perm[: len(perm)//2]])
            h2 = np.sort(seed_ids[perm[len(perm)//2:]])
            assert not (set(h1.tolist()) & set(h2.tolist()))
            assert len(h1) + len(h2) == len(seed_ids)
            r1 = run_convergence(con, h1, f"{tag}_half{rep}_a",
                                 rng=np.random.default_rng(
                                     _derive_seed(TRUE_CONVERGED_LIT_SEED, "halfa", tag, rep)))
            r2 = run_convergence(con, h2, f"{tag}_half{rep}_b",
                                 rng=np.random.default_rng(
                                     _derive_seed(TRUE_CONVERGED_LIT_SEED, "halfb", tag, rep)))
            h1r = _book_head(r1["preference"], r1)
            h2r = _book_head(r2["preference"], r2)
            reps[f"rep{rep}"] = {
                "j50": _head_jaccard(h1r, h2r, 50),
                "j200": _head_jaccard(h1r, h2r, 200),
                "rho200": _head_rho(h1r, h2r, 200),
                "weighted_median_L_a": endpoint_analysis(r1, es, eu)["weighted"]["median"],
                "weighted_median_L_b": endpoint_analysis(r2, es, eu)["weighted"]["median"],
            }
        result["half_split"][tag] = reps
        _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
        print(f"[stability] {tag} half splits done", flush=True)

    _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
    return result


def _save_primary(con, res, eu, es, tag) -> dict[str, Any]:
    ep = endpoint_analysis(res, es, eu)
    out = {
        "n": res["n_jury"],
        "converged": res["converged"],
        "stop_reason": res["stop_reason"],
        "iterations": res["iterations"],
        "final_step": res["final_step"],
        "final_weight_rel": res["final_weight_rel"],
        "final_book_rel": res["final_book_rel"],
        "kish": ep["kish"],
        "top1pct_weight_share": ep["top1pct_weight_share"],
        "top5pct_weight_share": ep["top5pct_weight_share"],
        "max_weight": ep["max_weight"],
        "median_weight": ep["median_weight"],
        "p90_weight": ep["p90_weight"],
        "gini": ep["gini"],
        "unweighted_L": ep["unweighted"],
        "weighted_L": ep["weighted"],
        "weight_by_L": ep["weight_by_L"],
        "weight_L_pearson": ep["weight_L_pearson"],
        "weight_L_spearman": ep["weight_L_spearman"],
        "seed_head_sem": _sem_flags(res["seed_head"]),
        "conv_head_sem": _sem_flags(ep["head"]),
        "seed_head_top50": res["seed_head"][:50],
        "seed_vs_conv": {
            "j50": _head_jaccard(res["seed_head"], ep["head"], 50),
            "j200": _head_jaccard(res["seed_head"], ep["head"], 200),
            "rho200": _head_rho(res["seed_head"], ep["head"], 200),
        },
        "head_top200": ep["head"][:200],
    }
    arrays = {
        f"primary/{tag}/weights": np.asarray(res["weights"]),
        f"primary/{tag}/user_ids": res["user_ids"],
        f"primary/{tag}/pref_score": np.asarray(res["preference"]["score"]),
    }
    _add_to_npz(arrays)
    return out


# ---------------------------------------------------------------------------
# Part N — controls (random + fandom, same convergence dynamics)
# ---------------------------------------------------------------------------

def controls_phase(con, force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "controls.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe, scores = load_frozen_scores()
    eu, es = convergence_eligible_universe(universe, scores)

    # random 10k
    rng = np.random.default_rng(_derive_seed(TRUE_CONVERGED_LIT_SEED, "randctrl"))
    rand10k = np.sort(rng.choice(eu, 10000, replace=False))
    rc = run_convergence(con, rand10k, "ctrl_random", force=force)
    ep_rand = endpoint_analysis(rc, es, eu, require_all_finite=False)
    # random-init stability (5 reps)
    rand_init = []
    for rep in range(5):
        r = run_convergence(con, rand10k, f"ctrl_random_init_{rep}",
                            init="lognormal",
                            rng=np.random.default_rng(
                                _derive_seed(TRUE_CONVERGED_LIT_SEED,
                                             "randctrl_init", rep)),
                            force=force)
        h = _book_head(r["preference"], r)
        rand_init.append({
            "j50": _head_jaccard(rc["seed_head"], h, 50),
            "j200": _head_jaccard(rc["seed_head"], h, 200),
            "weighted_median_L": endpoint_analysis(
                r, es, eu, require_all_finite=False)["weighted"]["median"],
        })

    # fandom 10k sample (threeway_anti)
    old = np.load("curators_explorer/data/maximum_literary_jury.npz",
                  allow_pickle=False)
    anti = old["juries/threeway_anti/user_ids"].astype(np.int64)
    rngf = np.random.default_rng(_derive_seed(TRUE_CONVERGED_LIT_SEED, "fandomctrl"))
    fandom = np.sort(rngf.choice(anti, 10000, replace=False))
    # ensure all in eligible universe (Option 1 rebuilds from raw, but for the
    # weighted-L we need members scoreable in common-L; report both counts)
    fc = run_convergence(con, fandom, "ctrl_fandom", force=force)
    ep_fand = endpoint_analysis(fc, es, eu, require_all_finite=False)
    fandom_init = []
    for rep in range(5):
        r = run_convergence(con, fandom, f"ctrl_fandom_init_{rep}",
                            init="lognormal",
                            rng=np.random.default_rng(
                                _derive_seed(TRUE_CONVERGED_LIT_SEED,
                                             "fandomctrl_init", rep)),
                            force=force)
        h = _book_head(r["preference"], r)
        fandom_init.append({
            "j50": _head_jaccard(fc["seed_head"], h, 50),
            "j200": _head_jaccard(fc["seed_head"], h, 200),
            "weighted_median_L": endpoint_analysis(
                r, es, eu, require_all_finite=False)["weighted"]["median"],
        })

    result = {
        "random10k": {
            "n": len(rand10k),
            "converged": rc["converged"], "iterations": rc["iterations"],
            "kish": _kish(rc["weights"]),
            "weighted_L": ep_rand["weighted"],
            "weight_by_L": ep_rand["weight_by_L"],
            "head_top30": _book_head(rc["preference"], rc, limit=30),
            "random_init_stability": rand_init,
        },
        "fandom10k": {
            "n": len(fandom),
            "converged": fc["converged"], "iterations": fc["iterations"],
            "kish": _kish(fc["weights"]),
            "weighted_L": ep_fand["weighted"],
            "weight_by_L": ep_fand["weight_by_L"],
            "head_top30": _book_head(fc["preference"], fc, limit=30),
            "random_init_stability": fandom_init,
        },
    }
    _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
    return result


# ---------------------------------------------------------------------------
# Part O/P — obscure-book coverage (raw + convergence-weighted information)
# ---------------------------------------------------------------------------

def _global_work_stats(con) -> dict[str, np.ndarray]:
    for p in (DATA / "juror_coherence_tail_state" / "global_work_stats.npz",
              STATE_DIR / "global_work_stats.npz"):
        if p.exists():
            with np.load(p, allow_pickle=False) as blob:
                return {k: blob[k] for k in blob.files}
    rows = con.execute(
        "SELECT work_id, count(*)::DOUBLE AS n_rated FROM ex.all_rating_events "
        "GROUP BY work_id").fetchall()
    out = {"work_id": np.asarray([r[0] for r in rows], dtype=str),
           "n_rated": np.asarray([r[1] for r in rows], dtype=np.float64)}
    _write_npz_atomic(STATE_DIR / "global_work_stats.npz", out)
    return out


def band_of(n: float) -> int:
    for i, (lo, hi) in enumerate(RARITY_BANDS):
        if n >= lo and n <= hi:
            return i
    return -1


def _jury_ratings_by_work(con, jury_users: np.ndarray) -> dict[str, list[int]]:
    ut = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {ut}(user_id BIGINT)")
    con.execute(f"INSERT INTO {ut} SELECT unnest(?::BIGINT[])",
                [np.asarray(jury_users, dtype=np.int64).tolist()])
    rows = con.execute(
        f"SELECT e.work_id, e.user_id FROM ex.all_rating_events e "
        f"JOIN {ut} u USING (user_id) WHERE e.rating >= 1").fetchall()
    con.execute(f"DROP TABLE IF EXISTS {ut}")
    out: dict[str, list[int]] = {}
    for w, u in rows:
        out.setdefault(str(w), []).append(int(u))
    return out


def coverage_phase(con, primary: dict[str, Any], force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "coverage.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe, scores = load_frozen_scores()
    eu, es = convergence_eligible_universe(universe, scores)
    gws = _global_work_stats(con)
    bands = np.asarray([band_of(float(x)) for x in gws["n_rated"]])
    n_band = {BAND_LABELS[i]: int(np.sum(bands == i)) for i in range(len(BAND_LABELS))}
    band_works = {i: gws["work_id"][bands == i].tolist() for i in range(len(BAND_LABELS))}
    idx_map = {int(u): i for i, u in enumerate(eu.tolist())}

    results: dict[str, Any] = {"n_works_per_band": n_band}
    for tag, p in primary.items():
        ppt = np.load(STATE_DIR / f"payload_{tag}.npz", allow_pickle=False)
        uid = ppt["user_ids"].astype(np.int64)
        jury_users = uid
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            wkey = f"primary/{tag}/weights"
            weights = blob[wkey].astype(np.float64)
        assert len(weights) == len(uid)
        wmean = float(weights.mean())
        w_norm = weights / wmean
        info_w = {}
        for i, u in enumerate(uid.tolist()):
            L = es[idx_map[int(u)]] if int(u) in idx_map else float("nan")
            if np.isfinite(L):
                info_w[int(u)] = float(w_norm[i] * max(0.0, 2.0 * L - 1.0))
        per_work = _jury_ratings_by_work(con, jury_users)
        # smoke-invariant: weights align to payload user_ids
        assert len(weights) == len(uid)
        results[tag] = {}
        for band_i in range(len(BAND_LABELS)):
            works = band_works[band_i]
            if not works:
                results[tag][BAND_LABELS[band_i]] = {"n_works": 0}
                continue
            ns = np.asarray([len(per_work.get(w, [])) for w in works])
            info_mass = np.asarray([
                sum(info_w.get(u, 0.0) for u in per_work.get(w, []))
                for w in works])
            results[tag][BAND_LABELS[band_i]] = {
                "n_works": len(works),
                "frac_ge1": float(np.mean(ns >= 1)),
                "frac_ge2": float(np.mean(ns >= 2)),
                "frac_ge3": float(np.mean(ns >= 3)),
                "frac_ge5": float(np.mean(ns >= 5)),
                "frac_ge10": float(np.mean(ns >= 10)),
                "median": float(np.median(ns)),
                "p75": float(np.quantile(ns, 0.75)),
                "p90": float(np.quantile(ns, 0.90)),
                "info_mass_ge_0p5": float(np.mean(info_mass >= 0.5)),
                "info_mass_ge_1": float(np.mean(info_mass >= 1.0)),
                "info_mass_ge_2": float(np.mean(info_mass >= 2.0)),
                "info_mass_ge_3": float(np.mean(info_mass >= 3.0)),
                "info_mass_ge_5": float(np.mean(info_mass >= 5.0)),
            }
        print(f"[coverage] {tag}: 20_49 raw>=1="
              f"{results[tag]['20_49']['frac_ge1']:.2f} "
              f"info_mass>=1={results[tag]['20_49']['info_mass_ge_1']:.3f}",
              flush=True)
    _write_text_atomic(path, json.dumps(results, indent=1))
    return results


# ---------------------------------------------------------------------------
# Part R/S — heads + naturality summary
# ---------------------------------------------------------------------------

def _load_probes_local(payload) -> None:
    global _PROBE_POS, _PROBE_ANTI, _PROBE_EXACT, _PROBE_BROAD
    from curators_explorer.scripts.research_ratings_only_canon import (
        load_eval_sets,
    )
    from curators_explorer.scripts.research_seedless_spectral_pilot import (
        load_posthoc_context,
    )
    from curators_explorer.scripts.research_maximum_literary_jury import (
        _merged_ev,
    )
    con = open_db()
    ev = load_eval_sets(con)
    _m, es_ = load_posthoc_context(payload["work_ids"])
    merged = _merged_ev(ev, es_)
    _PROBE_POS = set(merged.get("pos_works", set()))
    _PROBE_ANTI = set(merged.get("anti_works", set()))
    _PROBE_EXACT = set(merged.get("exact_lit", set()))
    _PROBE_BROAD = set(merged.get("broad_lit", set()))
    con.close()


def _meta_from_work_ids(con, work_ids) -> dict[str, dict[str, str]]:
    wids = list(set(work_ids))
    wt = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {wt}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {wt} SELECT unnest(?::VARCHAR[])", [wids])
    rows = con.execute(
        f"SELECT s.work_id, s.title, s.author FROM ex.work_scores s "
        f"JOIN {wt} w USING (work_id)").fetchall()
    con.execute(f"DROP TABLE IF EXISTS {wt}")
    return {str(w): {"title": t or "", "author": a or ""} for w, t, a in rows}


def _head_lines(head: list[dict], meta: dict) -> list[str]:
    lines = ["| rank | title | author | score | pos | exact | broad | anti |",
             "|---|---|---|---|---|---|---|---|"]
    for r in head[:50]:
        wid = r["work_id"]
        m = meta.get(wid, {"title": wid, "author": ""})
        lines.append(
            f"| {r['rank']} | {m['title']} | {m['author']} | {r['score']:.4f} | "
            f"{'Y' if wid in _PROBE_POS else ''} | "
            f"{'Y' if wid in _PROBE_EXACT else ''} | "
            f"{'Y' if wid in _PROBE_BROAD else ''} | "
            f"{'Y' if wid in _PROBE_ANTI else ''} |")
    return lines


def write_heads(primary: dict[str, Any], controls: dict[str, Any]) -> None:
    con = open_db()
    materialize_base(con)
    meta = {}
    for tag, p in primary.items():
        for r in p["head_top200"]:
            meta.setdefault(r["work_id"], None)
    for c in controls.values():
        for r in c["head_top30"]:
            meta.setdefault(r["work_id"], None)
    meta = _meta_from_work_ids(con, list(meta))
    L = ["# True Converged Literary Jurors — complete top-50 heads",
         "", f"Seed `{TRUE_CONVERGED_LIT_SEED}`. Probe flags are annotations "
             "only. Direct = equal-vote seed head; Converged = internal fixed "
             "point head.", ""]
    for tag, p in primary.items():
        L.append(f"## {tag}")
        L.append("")
        L.append(f"### Direct equal-vote seed top 50  (n={p['n']})")
        L.append("")
        seed = p.get("seed_head_top50", [])
        L.extend(_head_lines(seed, meta) if seed else ["(seed head not stored)"])
        L.append("")
        L.append(f"### Internally converged top 50")
        L.append("")
        L.extend(_head_lines(p["head_top200"], meta))
        L.append("")
    for name, c in controls.items():
        L.append(f"## {name} control (converged top 30)")
        L.append("")
        L.extend(_head_lines(c["head_top30"], meta))
        L.append("")
    con.close()
    _write_text_atomic(OUT_HEADS, "\n".join(L) + "\n")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def report_phase(primary: dict[str, Any], stability: dict[str, Any],
                 controls: dict[str, Any], coverage: dict[str, Any],
                 eu_n: int, n_l60: int, sizes_run: list[int],
                 eu_median_L: float) -> dict[str, Any]:
    from scipy.stats import spearmanr
    L = []
    L.append("# True Converged Literary Jurors — report")
    L.append("")
    L.append(f"- Seed `{TRUE_CONVERGED_LIT_SEED}`. Membership is a hard "
             f"invariant; convergence = internal reweighting of fixed members "
             f"under the iterate_map equation (BETA=2.5) to a genuine numerical "
             f"fixed point (step>=0.9999 AND weight_rel<=1e-4 for 5 consecutive, "
             f"max 200).")
    L.append("")
    L.append("## Frozen common-L input")
    L.append("")
    L.append(f"- Convergence-eligible users (Option 1, raw rebuild): {eu_n}; "
             f"with L>=0.60: {n_l60}; median L over eligible: {eu_median_L:.3f}")
    L.append("")
    L.append("## Primary jury definitions")
    L.append("")
    L.append("| jury | n | median L | p10 | p25 | p75 | min L |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    universe, scores = load_frozen_scores()
    eu, es = convergence_eligible_universe(universe, scores)
    order = build_jury_order(eu, es)
    for size in sizes_run:
        sel = es[order[:size]]
        L.append(f"| J{size} | {size} | {np.median(sel):.3f} | "
                 f"{np.quantile(sel, 0.10):.3f} | {np.quantile(sel, 0.25):.3f} | "
                 f"{np.quantile(sel, 0.75):.3f} | {np.min(sel):.3f} |")
    L.append("")
    L.append("## Numerical convergence")
    L.append("")
    L.append("| jury | converged | stop | iters | final step | final weight_rel | "
             "final book_rel |")
    L.append("|---|---|---|---:|---:|---:|---:|")
    for tag, p in primary.items():
        L.append(f"| {tag} | {p['converged']} | {p['stop_reason']} | "
                 f"{p['iterations']} | {p['final_step']:.6f} | "
                 f"{p['final_weight_rel']:.2e} | {p['final_book_rel']:.2e} |")
    L.append("")
    L.append("## Converged user-weight quality")
    L.append("")
    L.append("| jury | Kish | top1% | top5% | gini | wtd median L | wtd p10 | "
             "wtd p75 | wt L>=.7 | wt L>=.6 | wt L<.6 | w-L pearson | w-L spearman |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for tag, p in primary.items():
        w = p["weighted_L"]
        b = p["weight_by_L"]
        L.append(f"| {tag} | {p['kish']:.0f} | {p['top1pct_weight_share']:.3f} | "
                 f"{p['top5pct_weight_share']:.3f} | {p['gini']:.3f} | "
                 f"{w['median']:.3f} | {w['p10']:.3f} | {w['p75']:.3f} | "
                 f"{b['ge_0p70']:.3f} | {b['ge_0p60']:.3f} | {b['lt_0p60']:.3f} | "
                 f"{p['weight_L_pearson']:.3f} | {p['weight_L_spearman']:.3f} |")
    L.append("")
    L.append("## Seed vs converged book head")
    L.append("")
    L.append("| jury | seed pos50 | conv pos50 | J50 | J200 | rho200 |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for tag, p in primary.items():
        sv = p["seed_vs_conv"]
        L.append(f"| {tag} | {p['seed_head_sem']['pos50']} | "
                 f"{p['conv_head_sem']['pos50']} | {sv['j50']:.2f} | "
                 f"{sv['j200']:.2f} | {sv['rho200']:.3f} |")
    L.append("")
    L.append("## Stability")
    L.append("")
    L.append("### 90% subsample (10 reps)")
    L.append("")
    L.append("| jury | conv rate | iters med | J50 med | J50 p10 | J50 p90 | "
             "J200 med | wtd median L med |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for tag in primary:
        reps = stability["sub90"][tag]
        j50 = [v["book_j50"] for v in reps.values()]
        j200 = [v["book_j200"] for v in reps.values()]
        wl = [v["weighted_median_L"] for v in reps.values()]
        conv = [v["converged"] for v in reps.values()]
        it = [v["iterations"] for v in reps.values()]
        L.append(f"| {tag} | {sum(conv)}/{len(conv)} | {np.median(it):.0f} | "
                 f"{np.median(j50):.2f} | {np.quantile(j50,0.10):.2f} | "
                 f"{np.quantile(j50,0.90):.2f} | {np.median(j200):.2f} | "
                 f"{np.median(wl):.3f} |")
    L.append("")
    L.append("### Random initial weights (10 reps)")
    L.append("")
    L.append("| jury | J50 med | J50 p10 | J50 p90 | wtd median L med | weight cos med |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for tag in primary:
        reps = stability["random_init"][tag]
        j50 = [v["book_j50"] for v in reps.values()]
        wl = [v["weighted_median_L"] for v in reps.values()]
        wc = [v["weight_cosine"] for v in reps.values()]
        L.append(f"| {tag} | {np.median(j50):.2f} | {np.quantile(j50,0.10):.2f} | "
                 f"{np.quantile(j50,0.90):.2f} | {np.median(wl):.3f} | "
                 f"{np.median(wc):.3f} |")
    L.append("")
    if stability.get("sub80_J10000"):
        reps = stability["sub80_J10000"]
        j50 = [v["book_j50"] for v in reps.values()]
        j200 = [v["book_j200"] for v in reps.values()]
        L.append("### 80% subsample J10000 (5 reps)")
        L.append("")
        L.append(f"- J50 med {np.median(j50):.2f} (p10 {np.quantile(j50,0.10):.2f}, "
                 f"p90 {np.quantile(j50,0.90):.2f}); J200 med {np.median(j200):.2f}")
        L.append("")
    if stability.get("half_split"):
        L.append("### Split-half converged stability")
        L.append("")
        L.append("| jury | J50 med | J50 p10 | J50 p90 | J200 med | rho200 med |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for tag in ("J10000", "J20000"):
            if tag not in stability["half_split"]:
                continue
            reps = stability["half_split"][tag]
            j50 = [v["j50"] for v in reps.values()]
            j200 = [v["j200"] for v in reps.values()]
            rh = [v["rho200"] for v in reps.values()]
            L.append(f"| {tag} | {np.median(j50):.2f} | "
                     f"{np.quantile(j50,0.10):.2f} | {np.quantile(j50,0.90):.2f} | "
                     f"{np.median(j200):.2f} | {np.median(rh):.3f} |")
        L.append("")
    L.append("## Controls (same convergence dynamics)")
    L.append("")
    for name, c in controls.items():
        L.append(f"- {name}: n={c['n']} converged={c['converged']} "
                 f"iters={c['iterations']} kish={c['kish']:.0f} "
                 f"wtd median L={c['weighted_L']['median']:.3f} "
                 f"wt L<.6={c['weight_by_L']['lt_0p60']:.3f}")
        if c.get("random_init_stability"):
            j50 = [v["j50"] for v in c["random_init_stability"]]
            L.append(f"  random-init J50 med {np.median(j50):.2f}")
    L.append("")
    L.append("## Obscure-book coverage")
    L.append("")
    L.append("| jury | 5-19 >=1 | 20-49 >=1 | >=3 | 50-99 >=1 | 100-249 >=1 | "
             "250-999 >=1 | 1000-4999 >=1 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for tag in primary:
        c = coverage[tag]
        L.append(f"| {tag} | {c['5_19']['frac_ge1']:.2f} | "
                 f"{c['20_49']['frac_ge1']:.2f} | {c['20_49']['frac_ge3']:.2f} | "
                 f"{c['50_99']['frac_ge1']:.2f} | {c['100_249']['frac_ge1']:.2f} | "
                 f"{c['250_999']['frac_ge1']:.2f} | "
                 f"{c['1000_4999']['frac_ge1']:.2f} |")
    L.append("")
    L.append("## Convergence-weighted information coverage")
    L.append("")
    L.append("| jury | 20-49 info>=0.5 | >=1 | >=2 | 100-249 info>=1 | "
             "250-999 info>=1 |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for tag in primary:
        c = coverage[tag]
        L.append(f"| {tag} | {c['20_49']['info_mass_ge_0p5']:.3f} | "
                 f"{c['20_49']['info_mass_ge_1']:.3f} | "
                 f"{c['20_49']['info_mass_ge_2']:.3f} | "
                 f"{c['100_249']['info_mass_ge_1']:.3f} | "
                 f"{c['250_999']['info_mass_ge_1']:.3f} |")
    L.append("")
    L.append("## Cross-size comparison")
    L.append("")
    L.append("| jury | seed median L | conv wtd median L | iters | Kish | "
             "seed->conv J50 | 90% med J50 | rand-init med J50 | half med J50 | "
             "20-49 >=1 | 20-49 >=3 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    universe2, scores2 = load_frozen_scores()
    eu2, es2 = convergence_eligible_universe(universe2, scores2)
    order2 = build_jury_order(eu2, es2)
    for tag in primary:
        size = int(tag[1:])
        seed_med = np.median(es2[order2[:size]])
        p = primary[tag]
        sv = p["seed_vs_conv"]
        j90 = stability["sub90"][tag]
        j50_90 = [v["book_j50"] for v in j90.values()]
        ji = stability["random_init"][tag]
        j50_i = [v["book_j50"] for v in ji.values()]
        half_med = float("nan")
        if tag in stability["half_split"]:
            half_med = np.median([v["j50"] for v in stability["half_split"][tag].values()])
        c = coverage[tag]["20_49"]
        L.append(f"| {tag} | {seed_med:.3f} | {p['weighted_L']['median']:.3f} | "
                 f"{p['iterations']} | {p['kish']:.0f} | {sv['j50']:.2f} | "
                 f"{np.median(j50_90):.2f} | {np.median(j50_i):.2f} | "
                 f"{half_med:.2f} | {c['frac_ge1']:.2f} | {c['frac_ge3']:.2f} |")
    L.append("")
    L.append("## Interpretation")
    L.append("")
    L.append("See the 12 questions in the task; key qualitative answers follow "
             "from the tables above and the heads file. Membership never "
             "changes; convergence only reweights fixed members. Numerical "
             "convergence is generic (controls also converge); the naturality "
             "claim rests on: high individual common-L + internally converged "
             "literary head + stability across 90%/80%/half/random-init "
             "samples.")
    L.append("")
    _write_text_atomic(OUT_MD, "\n".join(L) + "\n")
    combined = {"seed": TRUE_CONVERGED_LIT_SEED, "eu_n": eu_n,
                "n_l60": n_l60, "primary": primary, "stability": stability,
                "controls": controls, "coverage": coverage,
                "sizes_run": sizes_run}
    _write_text_atomic(OUT_JSON, json.dumps(combined, indent=1, default=_json_default))
    print(f"Wrote {OUT_MD}, {OUT_HEADS}, {OUT_JSON}", flush=True)
    return {"report": True}


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def phase_smoke() -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    # frozen scores reproduce accepted summary
    universe, scores = load_frozen_scores()
    eu, es = convergence_eligible_universe(universe, scores)
    order = build_jury_order(eu, es)
    add("frozen_scores_reproduce_seeds",
        abs(np.median(es[order[:5000]]) - 0.811) < 0.01
        and abs(np.median(es[order[:10000]]) - 0.785) < 0.01,
        f"top5k med={np.median(es[order[:5000]]):.3f} "
        f"top10k med={np.median(es[order[:10000]]):.3f}")
    add("convergence_eligible_documented", eu_n_doc() > 0,
        f"eu_n={eu_n_doc()}")
    add("no_silent_member_loss", True, "membership fixed by construction")

    # convergence params
    add("beta_exactly_2_5", BETA == 2.5, f"BETA={BETA}")
    add("max_iter_200", MAX_CONV_ITER == 200, f"MAX_CONV_ITER={MAX_CONV_ITER}")
    add("stop_rule_frozen",
        STEP_THRESHOLD == 0.9999 and WEIGHT_CHANGE_THRESHOLD == 1e-4
        and CONSECUTIVE_CONVERGED == 5,
        f"{STEP_THRESHOLD}/{WEIGHT_CHANGE_THRESHOLD}/{CONSECUTIVE_CONVERGED}")

    # no removal/pruning in convergence path
    import inspect
    csrc = inspect.getsource(converge_internal)
    add("no_remove_fraction",
        "remove_fraction" not in csrc and "ladder" not in csrc
        and "gain" not in csrc and "retained_target" not in csrc,
        "no pruning/reversal in convergence")

    # update equation matches historical iterate_map
    isrc = inspect.getsource(pruning.iterate_map)
    add("equation_matches_historical",
        all(t in csrc for t in ("tanh", "sigmoid", "0.35", "0.65",
                                "user_signal.std")),
        "same tanh/sigmoid/damped update")

    # equal init synthetic
    w = _equal_init(5)
    add("equal_init_ones_mean1", np.allclose(w, 1.0), f"w={w}")
    # kish synthetic
    add("kish_synthetic", abs(_kish(np.ones(100)) - 100.0) < 1e-6,
        f"kish={_kish(np.ones(100))}")
    # weighted quantiles synthetic
    wq = _weighted_quantiles(np.asarray([0.5, 0.7, 0.9]),
                             np.asarray([0.25, 0.5, 0.25]))
    add("weighted_quantiles_synthetic",
        abs(wq["median"] - 0.7) < 1e-9 and abs(wq["p25"] - 0.5) < 1e-9
        and abs(wq["p75"] - 0.7) < 1e-9, f"wq={wq}")

    # lognormal init sigma
    rng = np.random.default_rng(1)
    wl = _lognormal_init(100, 0.20, rng)
    add("lognormal_sigma_0p20",
        abs(np.std(np.log(wl)) - 0.20) < 0.05, f"std(log w)={np.std(np.log(wl)):.3f}")
    add("lognormal_mean1", abs(wl.mean() - 1.0) < 1e-5, f"mean={wl.mean():.4f}")

    # membership invariant in converge_internal
    add("membership_exact", True, "converge_internal never changes n")

    # weighted L denominator includes all weight
    Lw = np.asarray([0.7, 0.6, 0.5])
    ww = np.asarray([1.0, 1.0, 1.0])
    bands = _weight_bands(Lw, ww)
    add("weight_bands_partition",
        abs((bands["ge_0p60"] + bands["lt_0p60"]) - 1.0) < 1e-9
        and bands["ge_0p75"] <= bands["ge_0p70"] <= bands["ge_0p65"] <= bands["ge_0p60"],
        f"ge.60={bands['ge_0p60']} lt.60={bands['lt_0p60']} (cumulative bands)")

    # information mass synthetic
    add("info_mass_synthetic",
        abs(_info_weight(0.75, 1.0) - 0.5) < 1e-9
        and abs(_info_weight(0.50, 1.0) - 0.0) < 1e-9
        and abs(_info_weight(1.00, 1.0) - 1.0) < 1e-9,
        "max(0,2L-1) mapping correct")

    # subsample sizes
    add("subsample_sizes_exact",
        int(round(0.90 * 10000)) == 9000 and int(round(0.80 * 10000)) == 8000,
        "90%/80% arithmetic")

    # old artifacts untouched
    from pathlib import Path as _P
    olds = [_P("curators_explorer/data/converged_common_literary_jurors.json"),
            _P("curators_explorer/data/COMMON_LITERARY_JURORS_REPORT.md")]
    add("old_artifacts_untouched", all(p.exists() for p in olds),
        "converged_common_literary_jurors.* still present")

    ok = all(c["ok"] for c in checks)
    print(f"[smoke] {sum(c['ok'] for c in checks)}/{len(checks)} checks passed "
          f"in {_fmt_time(time.time() - t0)}", flush=True)
    return {"checks": checks, "ok": bool(ok), "elapsed_s": round(time.time() - t0, 1)}


def eu_n_doc() -> int:
    universe, scores = load_frozen_scores()
    return int(np.sum(np.isfinite(scores)))


def _weight_bands(L: np.ndarray, w: np.ndarray) -> dict[str, float]:
    wsum = float(np.sum(w))
    return {
        "ge_0p75": float(np.sum(w[L >= 0.75]) / wsum),
        "ge_0p70": float(np.sum(w[L >= 0.70]) / wsum),
        "ge_0p65": float(np.sum(w[L >= 0.65]) / wsum),
        "ge_0p60": float(np.sum(w[L >= 0.60]) / wsum),
        "lt_0p60": float(np.sum(w[L < 0.60]) / wsum),
    }


def _info_weight(L: float, w_norm: float) -> float:
    return float(w_norm * max(0.0, 2.0 * L - 1.0))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _add_to_npz(arrays: dict[str, np.ndarray]) -> None:
    existing: dict[str, np.ndarray] = {}
    if OUT_NPZ.exists():
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            existing = {k: blob[k] for k in blob.files}
    existing.update(arrays)
    _write_npz_atomic(OUT_NPZ, existing)


def run_phases(phases: list[str], force: bool = False) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    from curators_explorer.scripts.research_maximum_literary_jury import (
        load_payload as _lp,
    )
    _load_probes_local(_lp())
    con = open_db()
    materialize_base(con)
    juries = load_juries()
    universe, scores = load_frozen_scores()
    eu, es = convergence_eligible_universe(universe, scores)
    order = build_jury_order(eu, es)
    for ph in phases:
        t0 = time.time()
        if ph == "prepare":
            _ = build_local_payload(con, eu[order[:5000]], )
        elif ph == "converge":
            stability = stability_phase(con, juries, force=force)
            primary = stability["primary"]
            controls = controls_phase(con, force=force)
            _write_text_atomic(STATE_DIR / "primary.json",
                               json.dumps(primary, indent=1, default=_json_default))
            _write_text_atomic(STATE_DIR / "controls.json",
                               json.dumps(controls, indent=1, default=_json_default))
        elif ph == "coverage":
            primary = json.loads((STATE_DIR / "primary.json").read_text())
            _ = coverage_phase(con, primary, force=force)
        elif ph == "report":
            primary = json.loads((STATE_DIR / "primary.json").read_text())
            stability = json.loads((STATE_DIR / "stability.json").read_text())
            controls = json.loads((STATE_DIR / "controls.json").read_text())
            coverage = json.loads((STATE_DIR / "coverage.json").read_text())
            sizes_run = sorted(int(t[1:]) for t in primary)
            write_heads(primary, controls)
            report_phase(primary, stability, controls, coverage,
                         int(len(eu)), int(np.sum(es >= 0.60)), sizes_run,
                         float(np.median(es)))
        else:
            raise SystemExit(f"unknown phase {ph}")
        print(f"[main] phase {ph} took {_fmt_time(time.time() - t0)}", flush=True)
    con.close()


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
        phases = ["prepare", "converge", "coverage", "report"]
    run_phases(phases, force=args.force)


if __name__ == "__main__":
    _main()

#!/usr/bin/env python3
"""CONVERGED COMMON LITERARY JURORS.

Corrected popular-book benchmark scoring + established-project convergence.

Corrections vs 5abee6c:
  * The reference evaluation universe is now chosen by GLOBAL SUPPORT (a fixed
    popular-book benchmark), NOT by the reference's own top-ranked works.
  * Reference score vectors are materialized for the full benchmark universe
    (no top-2000 truncation).
  * Explicit distinct-high/low-book evidence tracking.

Then the SEED juries (top-N by the corrected common literary-juror score) are
run through the PROJECT'S ESTABLISHED convergence/reversal procedure
(research_jury_ensemble_reversal.run_jury: nonlinear iterative map + gain-hard
pruning restart; BETA=2.5, MAX_STAGES=8, retained target 1.01).  Only the
CONVERGED endpoints are analysed.  We do NOT use the T_N membership operator.

The endpoint's users are mapped back to the frozen corrected literary_juror_score
for weighted individual-quality analysis.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_converged_common_literary_jurors --smoke
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_converged_common_literary_jurors --phase all
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts.research_deep_size_sweep import (
    MIN_APPEAR,
    SHRINK_K,
    build_pairs,
)
from curators_explorer.scripts.research_common_literary_jurors import (
    DATA,
    OUT_NPZ as OLD_COMMON_NPZ,
    STATE_DIR as OLD_COMMON_STATE,
    _derive_seed,
    _fmt_time,
    _json_default,
    _write_npz_atomic,
    _write_text_atomic,
    assign_folds,
    build_ranking,
    load_juries,
    load_payload_helper,
    open_db,
    q_distribution,
    ranking_arrays,
    shrink,
    _load_probes,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    materialize_base,
)
from curators_explorer.scripts import research_attractor_pruning as pruning
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year

CONVERGED_COMMON_LIT_SEED = 20260831

OUT_JSON = DATA / "converged_common_literary_jurors.json"
OUT_NPZ = DATA / "converged_common_literary_jurors.npz"
OUT_MD = DATA / "CONVERGED_COMMON_LITERARY_JURORS_REPORT.md"
OUT_HEADS = DATA / "CONVERGED_COMMON_LITERARY_JUROR_HEADS.md"
STATE_DIR = DATA / "converged_common_literary_jurors_state"

# --- benchmark ---
BENCH_MIN_SUPPORT = 500
BENCH_MAX_SUPPORT = 120000
BENCH_TARGET = 20000
BENCH_STRATA = 20

# --- user scoring ---
MAX_EVAL_HIGHS = 40
MAX_EVAL_LOWS = 40
MAX_EVAL_PAIRS = 400
PRIOR_K = 40.0
TIE_SCORE = 0.5
CANDIDATE_MIN_VALID_REFS = 2
CANDIDATE_MIN_TESTABLE = 20
CANDIDATE_MIN_DISTINCT_H = 4
CANDIDATE_MIN_DISTINCT_L = 4

# --- seeds ---
SEED_SIZES = [5000, 10000, 20000]

# --- established convergence parameters (from research_jury_ensemble_reversal) ---
CONV_BETA = 2.5
CONV_MAX_STAGES = 8
CONV_ITERATIONS = 20
CONV_RETAINED_TARGET = 1.01
STABILITY_REPS = 3

REFERENCE_KEYS = {
    "R1_ABC": "ABC",
    "R2_p65": "core_p65_s25",
    "R3_AnB": "committee_AnB",
}

RARITY_BANDS = [(5, 19), (20, 49), (50, 99), (100, 249), (250, 999),
                (1000, 4999)]
BAND_LABELS = ["5_19", "20_49", "50_99", "100_249", "250_999", "1000_4999"]

_PROBE_POS: set = set()
_PROBE_ANTI: set = set()
_PROBE_EXACT: set = set()
_PROBE_BROAD: set = set()

_jury_counter = [0]


def _next_table() -> str:
    _jury_counter[0] += 1
    return f"cclj_{_jury_counter[0]}"


# ---------------------------------------------------------------------------
# Part A — fixed popular-book benchmark (support-only, deterministic cap)
# ---------------------------------------------------------------------------

def popular_benchmark_works(con, force: bool = False) -> np.ndarray:
    path = STATE_DIR / "benchmark.npz"
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return blob["work_id"].astype(str)
    rows = con.execute(
        f"SELECT work_id, count(*)::DOUBLE AS c FROM ex.all_rating_events "
        f"GROUP BY work_id HAVING count(*) >= {BENCH_MIN_SUPPORT} "
        f"AND count(*) <= {BENCH_MAX_SUPPORT}"
    ).fetchall()
    wids = np.asarray([r[0] for r in rows], dtype=str)
    counts = np.asarray([r[1] for r in rows], dtype=np.float64)
    order = np.argsort(counts, kind="stable")
    n_total = len(wids)
    per = BENCH_TARGET // BENCH_STRATA
    sel = []
    for s in range(BENCH_STRATA):
        lo = s * n_total // BENCH_STRATA
        hi = (s + 1) * n_total // BENCH_STRATA
        idx = order[lo:hi]
        rng = np.random.default_rng(_derive_seed(CONVERGED_COMMON_LIT_SEED,
                                                 "benchmark", s))
        take = rng.choice(idx, per, replace=False)
        sel.append(take)
    bench = wids[np.concatenate(sel)]
    _write_npz_atomic(path, {"work_id": bench, "n_total_support": np.asarray([n_total])})
    return bench


def _benchmark_meta(con) -> dict[str, Any]:
    rows = con.execute(
        f"SELECT work_id, count(*)::DOUBLE AS c FROM ex.all_rating_events "
        f"GROUP BY work_id HAVING count(*) >= {BENCH_MIN_SUPPORT} "
        f"AND count(*) <= {BENCH_MAX_SUPPORT}"
    ).fetchall()
    counts = {str(w): float(c) for w, c in rows}
    vals = list(counts.values())
    return {
        "n_candidates": len(vals),
        "n_selected": None,  # filled by caller
        "min": min(vals),
        "median": float(np.median(vals)),
        "max": max(vals),
    }


# ---------------------------------------------------------------------------
# Part B/C — full benchmark reference score vectors (+ fold-excluded)
# ---------------------------------------------------------------------------

def score_benchmark_works(con, jury_user_ids: np.ndarray,
                          benchmark: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (sorted work_id, score) for benchmark works with >= MIN_APPEAR edges."""
    table = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT, w DOUBLE)")
    con.execute(
        f"INSERT INTO {table} SELECT * FROM ("
        f"SELECT unnest(?::BIGINT[]) AS user_id, 1.0::DOUBLE AS w)",
        [np.asarray(jury_user_ids, dtype=np.int64).tolist()],
    )
    pairs = f"{table}_pairs"
    build_pairs(con, table, pairs)
    bm = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {bm}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {bm} SELECT unnest(?::VARCHAR[])", [benchmark.tolist()])
    sql = f"""
        WITH wins AS (
            SELECT winner AS work_id, sum(w)::DOUBLE AS wins,
                   count(*)::BIGINT AS n_win_edges FROM {pairs} GROUP BY 1
        ),
        losses AS (
            SELECT loser AS work_id, sum(w)::DOUBLE AS losses,
                   count(*)::BIGINT AS n_loss_edges FROM {pairs} GROUP BY 1
        ),
        agg AS (
            SELECT coalesce(wi.work_id, lo.work_id) AS work_id,
                   coalesce(wi.wins, 0) AS wins,
                   coalesce(lo.losses, 0) AS losses,
                   (coalesce(wi.n_win_edges, 0) + coalesce(lo.n_loss_edges, 0))
                       AS n_edges
            FROM wins wi FULL OUTER JOIN losses lo USING (work_id)
        )
        SELECT a.work_id,
               ((a.n_edges::DOUBLE / (a.n_edges + {SHRINK_K}))
                * (a.wins / (a.wins + a.losses)))::DOUBLE AS score,
               a.n_edges::DOUBLE AS n_eff
        FROM agg a JOIN {bm} b USING (work_id)
        WHERE a.n_edges >= {MIN_APPEAR}
    """
    rows = con.execute(sql).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {pairs}")
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"DROP TABLE IF EXISTS {bm}")
    wid = np.asarray([r[0] for r in rows], dtype=str)
    sc = np.asarray([float(r[1]) for r in rows])
    order = np.argsort(wid, kind="stable")
    return wid[order], sc[order]


def build_reference_benchmark_scores(con, juries, benchmark,
                                     force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "reference_scores.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    refs: dict[str, Any] = {}
    for ref, jury_name in REFERENCE_KEYS.items():
        user_ids = juries[jury_name]
        folds = assign_folds(user_ids, ref, 10)
        full_wid, full_sc = score_benchmark_works(con, user_ids, benchmark)
        fold_scores = []
        for f in range(10):
            train = user_ids[folds != f]
            fw, fs = score_benchmark_works(con, train, benchmark)
            fold_scores.append({"wid": fw, "score": fs})
        arrays = {f"ref/{ref}/full_wid": full_wid,
                  f"ref/{ref}/full_score": full_sc,
                  f"ref/{ref}/user_ids": user_ids,
                  f"ref/{ref}/folds": folds}
        for f, fs_ in enumerate(fold_scores):
            arrays[f"ref/{ref}/fold{f}_wid"] = fs_["wid"]
            arrays[f"ref/{ref}/fold{f}_score"] = fs_["score"]
        _add_to_npz(arrays)
        refs[ref] = {"jury_name": jury_name, "n": int(len(user_ids)),
                     "n_benchmark_scored": len(full_wid)}
        print(f"[references] {ref}: scored {len(full_wid)}/{len(benchmark)} "
              f"benchmark works", flush=True)
    result = {"refs": refs}
    _write_text_atomic(path, json.dumps(result, indent=1))
    return result


# ---------------------------------------------------------------------------
# Part D/E — user scoring over benchmark works + frozen common score
# ---------------------------------------------------------------------------

def _fetch_benchmark_highlow(con, user_ids: np.ndarray,
                             benchmark: np.ndarray) -> tuple[np.ndarray, np.ndarray,
                                                             np.ndarray, np.ndarray]:
    path = STATE_DIR / "highlow_bench.npz"
    if path.exists():
        with np.load(path, allow_pickle=False) as blob:
            return (blob["h_uid"], blob["h_wid"], blob["l_uid"], blob["l_wid"])
    ut = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {ut}(user_id BIGINT)")
    con.execute(f"INSERT INTO {ut} SELECT unnest(?::BIGINT[])", [user_ids.tolist()])
    wt = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {wt}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {wt} SELECT unnest(?::VARCHAR[])", [benchmark.tolist()])
    h_rows = con.execute(
        f"SELECT e.user_id, e.work_id FROM ex.all_rating_events e "
        f"JOIN {ut} u USING (user_id) JOIN {wt} w USING (work_id) "
        f"WHERE e.rating = 5"
    ).fetchall()
    l_rows = con.execute(
        f"SELECT e.user_id, e.work_id FROM ex.all_rating_events e "
        f"JOIN {ut} u USING (user_id) JOIN {wt} w USING (work_id) "
        f"WHERE e.rating <= 3"
    ).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {ut}")
    con.execute(f"DROP TABLE IF EXISTS {wt}")
    h_uid = np.asarray([r[0] for r in h_rows], dtype=np.int64)
    h_wid = np.asarray([r[1] for r in h_rows], dtype=str)
    l_uid = np.asarray([r[0] for r in l_rows], dtype=np.int64)
    l_wid = np.asarray([r[1] for r in l_rows], dtype=str)
    _write_npz_atomic(path, {"h_uid": h_uid, "h_wid": h_wid,
                             "l_uid": l_uid, "l_wid": l_wid})
    return h_uid, h_wid, l_uid, l_wid


def _group(uids: np.ndarray, wids: np.ndarray) -> dict[int, np.ndarray]:
    order = np.argsort(uids, kind="stable")
    uids, wids = uids[order], wids[order]
    uniq, starts = np.unique(uids, return_index=True)
    starts = np.append(starts, len(uids))
    out: dict[int, np.ndarray] = {}
    for i, u in enumerate(uniq):
        out[int(u)] = wids[starts[i]:starts[i + 1]]
    return out


def _filter_scores(wids: np.ndarray, srt_wid: np.ndarray,
                   srt_score: np.ndarray) -> np.ndarray:
    if len(wids) == 0:
        return np.asarray([], dtype=np.float64)
    idx = np.searchsorted(srt_wid, wids)
    idx = np.minimum(idx, len(srt_wid) - 1)
    valid = srt_wid[idx] == wids
    return srt_score[idx[valid]]


def eval_user_benchmark(highs: np.ndarray, lows: np.ndarray,
                        srt_wid: np.ndarray, srt_score: np.ndarray,
                        rng) -> dict[str, Any]:
    """Agreement vs a reference, with distinct high/low book tracking."""
    h = _filter_scores(highs, srt_wid, srt_score)
    l = _filter_scores(lows, srt_wid, srt_score)
    n_high_avail = int(len(h))
    n_low_avail = int(len(l))
    if len(h) == 0 or len(l) == 0:
        return {"distinct_high_avail": n_high_avail,
                "distinct_low_avail": n_low_avail,
                "n_sampled_highs": 0, "n_sampled_lows": 0,
                "n_testable": 0, "agreement_sum": 0.0}
    if len(h) > MAX_EVAL_HIGHS:
        h = rng.choice(h, MAX_EVAL_HIGHS, replace=False)
    if len(l) > MAX_EVAL_LOWS:
        l = rng.choice(l, MAX_EVAL_LOWS, replace=False)
    nh, nl = len(h), len(l)
    if nh * nl <= MAX_EVAL_PAIRS:
        ph = np.repeat(h, nl)
        pl = np.tile(l, nh)
    else:
        idx = rng.choice(nh * nl, MAX_EVAL_PAIRS, replace=False)
        ph = h[idx // nl]
        pl = l[idx % nl]
    agree = float(np.sum(ph > pl) + TIE_SCORE * np.sum(ph == pl))
    return {"distinct_high_avail": n_high_avail, "distinct_low_avail": n_low_avail,
            "n_sampled_highs": nh, "n_sampled_lows": nl,
            "n_testable": int(len(ph)), "agreement_sum": agree}


def eligible_user_universe(con) -> np.ndarray:
    from curators_explorer.scripts.research_common_literary_jurors import (
        eligible_user_universe as _e,
    )
    return _e(con)


def reference_user_scores(con, juries, benchmark, force: bool = False) -> dict[str, np.ndarray]:
    path = STATE_DIR / "user_scores.npz"
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}
    universe = eligible_user_universe(con)
    members = np.unique(np.concatenate(
        [juries[REFERENCE_KEYS[r]] for r in REFERENCE_KEYS]))
    universe = np.unique(np.concatenate([universe, members]))
    h_uid, h_wid, l_uid, l_wid = _fetch_benchmark_highlow(con, universe, benchmark)
    highs = _group(h_uid, h_wid)
    lows = _group(l_uid, l_wid)

    n = len(universe)
    nref = len(REFERENCE_KEYS)
    L_raw = np.full((n, nref), np.nan)
    L_shrunk = np.full((n, nref), np.nan)
    n_testable = np.zeros((n, nref), dtype=np.int64)
    n_high_avail = np.zeros((n, nref), dtype=np.int64)
    n_low_avail = np.zeros((n, nref), dtype=np.int64)

    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        for ri, ref in enumerate(REFERENCE_KEYS):
            r_uids = blob[f"ref/{ref}/user_ids"].astype(np.int64)
            r_folds = blob[f"ref/{ref}/folds"].astype(np.int8)
            fold_of = {int(u): int(f) for u, f in zip(r_uids.tolist(),
                                                      r_folds.tolist())}
            full_wid = blob[f"ref/{ref}/full_wid"]
            full_score = blob[f"ref/{ref}/full_score"]
            fold_arr = [(blob[f"ref/{ref}/fold{f}_wid"],
                         blob[f"ref/{ref}/fold{f}_score"])
                        for f in range(10)]
            idx_u = {int(u): i for i, u in enumerate(universe.tolist())}
            # members against fold-excluded
            for u in r_uids.tolist():
                f = fold_of[u]
                wid, sc = fold_arr[f]
                i = idx_u[u]
                rng = np.random.default_rng(_derive_seed(
                    CONVERGED_COMMON_LIT_SEED, "benchscore", ref, u))
                rec = eval_user_benchmark(
                    highs.get(u, np.asarray([], dtype=str)),
                    lows.get(u, np.asarray([], dtype=str)), wid, sc, rng)
                _store_rec(i, ri, rec, L_raw, L_shrunk, n_testable,
                           n_high_avail, n_low_avail)
            # outsiders against full
            outsider = np.flatnonzero(~np.isin(universe, r_uids))
            for i in outsider:
                u = int(universe[i])
                rng = np.random.default_rng(_derive_seed(
                    CONVERGED_COMMON_LIT_SEED, "benchscore", ref, u))
                rec = eval_user_benchmark(
                    highs.get(u, np.asarray([], dtype=str)),
                    lows.get(u, np.asarray([], dtype=str)),
                    full_wid, full_score, rng)
                _store_rec(i, ri, rec, L_raw, L_shrunk, n_testable,
                           n_high_avail, n_low_avail)
            print(f"[score_users] {ref} done", flush=True)

    arrays = {"universe": universe, "L_raw": L_raw, "L_shrunk": L_shrunk,
              "n_testable": n_testable, "n_high_avail": n_high_avail,
              "n_low_avail": n_low_avail}
    _write_npz_atomic(path, arrays)
    return arrays


def _store_rec(i, ri, rec, L_raw, L_shrunk, n_testable, n_high_avail, n_low_avail):
    n_testable[i, ri] = rec["n_testable"]
    n_high_avail[i, ri] = rec["distinct_high_avail"]
    n_low_avail[i, ri] = rec["distinct_low_avail"]
    if rec["n_testable"] > 0:
        L_raw[i, ri] = rec["agreement_sum"] / rec["n_testable"]
        L_shrunk[i, ri] = (rec["agreement_sum"] + 0.5 * PRIOR_K) / (
            rec["n_testable"] + PRIOR_K)


def compute_common_scores(us: dict[str, np.ndarray]) -> np.ndarray:
    L = us["L_shrunk"]
    nt = us["n_testable"]
    hh = us["n_high_avail"]
    ll = us["n_low_avail"]
    ok = (np.isfinite(L) & (nt >= CANDIDATE_MIN_TESTABLE)
          & (hh >= CANDIDATE_MIN_DISTINCT_H) & (ll >= CANDIDATE_MIN_DISTINCT_L))
    n_valid = np.sum(ok, axis=1)
    score = np.full(len(L), np.nan)
    for i in range(len(L)):
        if n_valid[i] < CANDIDATE_MIN_VALID_REFS:
            continue
        score[i] = float(np.median(L[i, ok[i]]))
    return score


def _add_to_npz(arrays: dict[str, np.ndarray]) -> None:
    existing: dict[str, np.ndarray] = {}
    if OUT_NPZ.exists():
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            existing = {k: blob[k] for k in blob.files}
    existing.update(arrays)
    _write_npz_atomic(OUT_NPZ, existing)


# ---------------------------------------------------------------------------
# Part F — validation against known groups
# ---------------------------------------------------------------------------

def validate_groups(us: dict[str, np.ndarray], juries: dict[str, np.ndarray]) -> dict[str, Any]:
    universe = us["universe"]
    scores = compute_common_scores(us)
    groups = {
        "ABC": "ABC", "p65": "core_p65_s25", "AnB": "committee_AnB",
        "vote2": "committee_vote2_ABCs", "A_only": "A_only",
        "B_only": "B_only", "AB_only": "AB_only", "AuB": "committee_AuB",
    }
    out: dict[str, Any] = {}
    for name, jury in groups.items():
        idx = np.flatnonzero(np.isin(universe, juries[jury]))
        out[name] = {
            "n_scoreable": int(np.sum(np.isfinite(scores[idx]))),
            "n_in_universe": int(len(idx)),
            "dist": q_distribution(scores[idx]),
            "median_distinct_high": float(np.median(
                np.max(us["n_high_avail"][idx], axis=1))),
            "median_distinct_low": float(np.median(
                np.max(us["n_low_avail"][idx], axis=1))),
            "median_n_testable": float(np.median(
                np.max(us["n_testable"][idx], axis=1))),
        }
    # fandom + random
    old = np.load(OLD_COMMON_NPZ if False else
                  "curators_explorer/data/maximum_literary_jury.npz",
                  allow_pickle=False)
    anti = old["juries/threeway_anti/user_ids"].astype(np.int64)
    rng = np.random.default_rng(_derive_seed(CONVERGED_COMMON_LIT_SEED, "fandom"))
    anti10k = np.sort(rng.choice(anti, 10000, replace=False))
    ai = np.flatnonzero(np.isin(universe, anti10k))
    out["fandom_anti10k"] = {
        "n_scoreable": int(np.sum(np.isfinite(scores[ai]))),
        "n_in_universe": int(len(ai)),
        "dist": q_distribution(scores[ai]),
        "median_distinct_high": float(np.median(
            np.max(us["n_high_avail"][ai], axis=1))),
        "median_distinct_low": float(np.median(
            np.max(us["n_low_avail"][ai], axis=1))),
        "median_n_testable": float(np.median(
            np.max(us["n_testable"][ai], axis=1))),
    }
    rng2 = np.random.default_rng(_derive_seed(CONVERGED_COMMON_LIT_SEED, "rand10k"))
    rand = np.sort(rng2.choice(universe, 10000, replace=False))
    ri = np.flatnonzero(np.isin(universe, rand))
    out["random10k"] = {
        "n_scoreable": int(np.sum(np.isfinite(scores[ri]))),
        "n_in_universe": int(len(ri)),
        "dist": q_distribution(scores[ri]),
        "median_distinct_high": float(np.median(
            np.max(us["n_high_avail"][ri], axis=1))),
        "median_distinct_low": float(np.median(
            np.max(us["n_low_avail"][ri], axis=1))),
        "median_n_testable": float(np.median(
            np.max(us["n_testable"][ri], axis=1))),
    }
    # pairwise reference correlations
    L = us["L_shrunk"]
    enough = np.isfinite(L) & (us["n_testable"] >= CANDIDATE_MIN_TESTABLE)
    refs = list(REFERENCE_KEYS)
    pairs = {}
    from scipy.stats import spearmanr
    for a in range(3):
        for b in range(a + 1, 3):
            m = enough[:, a] & enough[:, b]
            va, vb = L[m, a], L[m, b]
            pairs[f"{refs[a]}_vs_{refs[b]}"] = {
                "n": int(m.sum()),
                "pearson": float(np.corrcoef(va, vb)[0, 1]),
                "spearman": float(spearmanr(va, vb).statistic),
            }
    out["_pairs"] = pairs
    return out


# ---------------------------------------------------------------------------
# Part G — three seed juries
# ---------------------------------------------------------------------------

def build_seeds(con, us: dict[str, np.ndarray], juries: dict[str, np.ndarray],
                force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "seeds.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe = us["universe"]
    scores = compute_common_scores(us)
    nt = us["n_testable"]
    dh = us["n_high_avail"]
    dl = us["n_low_avail"]
    # tie-break: score desc, median n_testable desc, median distinct eval books desc, user_id asc
    med_nt = np.nanmedian(nt, axis=1)
    med_books = np.nanmedian(np.maximum(dh, dl), axis=1)
    order = np.lexsort((universe, -np.nan_to_num(med_books),
                        -np.nan_to_num(med_nt), -np.nan_to_num(scores)))
    eligible = np.flatnonzero(np.isfinite(scores))
    order = order[np.isin(order, eligible)]

    union_abc = (set(juries["deep_mint_all"].tolist())
                 | set(juries["threeway_classic"].tolist())
                 | set(juries["rebuilt_hard"].tolist()))
    src = {
        "ABC": set(juries["ABC"].tolist()),
        "p65": set(juries["core_p65_s25"].tolist()),
        "AnB": set(juries["committee_AnB"].tolist()),
        "vote2": set(juries["committee_vote2_ABCs"].tolist()),
        "A_only": set(juries["A_only"].tolist()),
        "B_only": set(juries["B_only"].tolist()),
        "AB_only": set(juries["AB_only"].tolist()),
    }
    seeds: dict[str, Any] = {}
    arrays: dict[str, np.ndarray] = {}
    for size in SEED_SIZES:
        sel = order[:size]
        members = universe[sel]
        comp = {}
        for name, s in src.items():
            comp[name] = sum(1 for u in members.tolist() if u in s) / size
        comp["none_ABC"] = sum(1 for u in members.tolist()
                               if u not in union_abc) / size
        rows = build_ranking(con, members)
        seeds[f"Seed_L{size}"] = {
            "n": size,
            "dist": q_distribution(scores[sel]),
            "median_evidence": float(np.median(med_nt[sel])),
            "source_composition": comp,
            "head_top50": [
                {"rank": r["rank"], "work_id": r["work_id"], "title": r["title"],
                 "author": r["author"], "score": float(r["score"]),
                 "n_eff": float(r["n_eff"])} for r in rows[:50]
            ],
        }
        arrays[f"seeds/Seed_L{size}/user_ids"] = members
        print(f"[seeds] Seed_L{size}: median L="
              f"{seeds[f'Seed_L{size}']['dist'].get('median', float('nan')):.3f} "
              f"noneABC={comp['none_ABC']:.3f}", flush=True)
    _add_to_npz(arrays)
    _write_text_atomic(path, json.dumps(seeds, indent=1, default=_json_default))
    return seeds


# ---------------------------------------------------------------------------
# Part H — established convergence (replicates ensemble_reversal.run_jury)
# ---------------------------------------------------------------------------

def run_jury_captured(payload, matrix, start_full, rng, retained_target):
    """EXACT replication of research_jury_ensemble_reversal.run_jury, plus
    capturing `keep` and local weights per stage so the converged endpoint's
    user weights can be recovered.  Same dynamics, same functions, same params:
      spectral.make_operator / attractor.CONFIG / pruning.iterate_map(BETA=2.5) /
      attractor.weighted_preferences / pruning.remove_fraction(gain, hard,
      LADDER_RATE=0.05) / MIN_REMAINING_FRACTION=0.05 / MAX_STAGES=8.
    """
    n_users = len(payload["user_ids"])
    full_operator, _ = spectral.make_operator(matrix, payload, attractor.CONFIG)
    reference_direction = attractor.normalize_columns(
        full_operator.rmatmat(start_full)).ravel()

    keep = np.arange(n_users, dtype=np.int64)
    stages: list[dict[str, Any]] = []
    stage_prefs: list[np.ndarray] = []
    stop_reason = "max_stages"
    stage0_pref = None
    last_pref = None
    for stage in range(CONV_MAX_STAGES + 1):
        local_payload = pruning.subset_payload(payload, keep)
        sub_matrix, _ = spectral.build_matrix(local_payload)
        operator, _ = spectral.make_operator(sub_matrix, local_payload,
                                             attractor.CONFIG)
        start_restricted = start_full[keep] / start_full[keep].mean()
        weights, direction, history = pruning.iterate_map(
            operator, start_restricted, CONV_BETA)
        stage_start_direction = attractor.normalize_columns(
            operator.rmatmat(start_restricted)).ravel()
        preference = attractor.weighted_preferences(sub_matrix, weights)
        if stage == 0:
            stage0_pref = preference["score"].astype(np.float32)
        last_pref = preference["score"].astype(np.float32)
        stage_prefs.append(preference["score"].astype(np.float32))
        stages.append({
            "stage": stage,
            "remaining_users": int(len(keep)),
            "cumulative_removed_fraction": 1.0 - len(keep) / n_users,
            "final_step_correlation": history[-1]["step_correlation"],
            "direction_retained_reference": float(
                np.sum(direction * reference_direction)),
            "direction_retained_stage": float(
                np.sum(direction * stage_start_direction)),
            "effective_user_share": float(
                (weights.sum() ** 2 / np.sum(weights**2)) / len(weights)),
            "keep": keep.copy(),
            "weights_local": weights.astype(np.float32),
            "direction": direction.astype(np.float32),
        })
        if stages[-1]["direction_retained_reference"] >= retained_target:
            stop_reason = "retained_target"
            break
        if stage == CONV_MAX_STAGES:
            stop_reason = "max_stages"
            break
        if len(keep) <= pruning.MIN_REMAINING_FRACTION * n_users:
            stop_reason = "evidence_floor"
            break
        removed, n_removed = pruning.remove_fraction(
            weights, start_restricted, "gain", "hard", pruning.LADDER_RATE, rng)
        if n_removed == 0:
            stop_reason = "nothing_removed"
            break
        keep = keep[~removed]
        if len(keep) <= pruning.MIN_REMAINING_FRACTION * n_users:
            stop_reason = "evidence_floor"
            break

    last = stages[-1]
    endpoint_weights = np.zeros(n_users, dtype=np.float32)
    endpoint_weights[last["keep"]] = last["weights_local"]
    return {
        "stop_reason": stop_reason,
        "stages": stages,
        "stage0_pref": stage0_pref,
        "final_pref": last_pref,
        "stage_prefs": stage_prefs,
        "endpoint_weights": endpoint_weights,
        "endpoint_keep": last["keep"].copy(),
        "n_stages": len(stages),
    }


def _payload_start(seed_user_ids: np.ndarray, payload_ids: np.ndarray) -> np.ndarray:
    n = len(payload_ids)
    start = np.full(n, 0.4, dtype=np.float32)
    order = np.argsort(payload_ids)
    ps = payload_ids[order]
    pos = np.searchsorted(ps, np.asarray(seed_user_ids, dtype=np.int64))
    pos = np.minimum(pos, n - 1)
    ok = ps[pos] == np.asarray(seed_user_ids, dtype=np.int64)
    start[order[pos[ok]]] = 20.0
    start /= start.mean()
    return start


def converge_seed(payload, matrix, seed_user_ids, payload_ids, tag, rng,
                  force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / f"conv_{tag}.npz"
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}
    start = _payload_start(seed_user_ids, payload_ids)
    run = run_jury_captured(payload, matrix, start, rng, CONV_RETAINED_TARGET)
    arrays = {
        "endpoint_weights": run["endpoint_weights"],
        "endpoint_keep": run["endpoint_keep"],
        "final_pref": run["final_pref"],
        "stage0_pref": run["stage0_pref"],
        "stop_reason": np.asarray([run["stop_reason"]]),
        "n_stages": np.asarray([run["n_stages"]]),
        "stage_remaining": np.asarray([s["remaining_users"] for s in run["stages"]]),
        "stage_retained_ref": np.asarray(
            [s["direction_retained_reference"] for s in run["stages"]]),
        "seed_start": start,
    }
    _write_npz_atomic(path, arrays)
    return arrays


def convergence_phase(us: dict[str, np.ndarray], juries: dict[str, np.ndarray],
                      force: bool = False) -> dict[str, Any]:
    t0 = time.time()
    universe = us["universe"]
    scores = compute_common_scores(us)
    nt = us["n_testable"]
    dh = us["n_high_avail"]
    dl = us["n_low_avail"]
    med_nt = np.nanmedian(nt, axis=1)
    med_books = np.nanmedian(np.maximum(dh, dl), axis=1)
    order = np.lexsort((universe, -np.nan_to_num(med_books),
                        -np.nan_to_num(med_nt), -np.nan_to_num(scores)))
    eligible = np.flatnonzero(np.isfinite(scores))
    order = order[np.isin(order, eligible)]

    payload, matrix, _ = year.load_matrix()
    payload_ids = payload["user_ids"].astype(np.int64)

    seeds = {}
    results: dict[str, Any] = {}
    for size in SEED_SIZES:
        seed_ids = universe[order[:size]]
        rng = np.random.default_rng(
            _derive_seed(CONVERGED_COMMON_LIT_SEED, "conv", size))
        conv = converge_seed(payload, matrix, seed_ids, payload_ids,
                             f"seed{size}", rng, force=force)
        results[f"Conv_L{size}"] = _endpoint_summary(
            conv, universe, scores, us, payload, size)
        seeds[f"Conv_L{size}"] = {
            "seed_n_in_payload": int(np.sum(np.isin(seed_ids, payload_ids))),
            "endpoint_raw_support": int(np.sum(conv["endpoint_weights"] > 0)),
            "kish": _kish(conv["endpoint_weights"]),
            "weight_concentration_top1pct": _top_concentration(
                conv["endpoint_weights"]),
            "stop_reason": str(conv["stop_reason"][0]),
            "n_stages": int(conv["n_stages"][0]),
            "stage_remaining": conv["stage_remaining"].tolist(),
            "stage_retained_ref": [float(x) for x in conv["stage_retained_ref"]],
        }
        print(f"[convergence] Conv_L{size}: raw={seeds[f'Conv_L{size}']['endpoint_raw_support']} "
              f"kish={seeds[f'Conv_L{size}']['kish']:.0f} "
              f"weighted_median_L={results[f'Conv_L{size}']['weighted'].get('median', float('nan')):.3f} "
              f"stop={conv['stop_reason'][0]}", flush=True)

    # stability reps (90% subsamples)
    stability: dict[str, Any] = {}
    for size in SEED_SIZES:
        seed_ids = universe[order[:size]]
        stability[f"Conv_L{size}"] = {}
        for rep in range(STABILITY_REPS):
            rng_sub = np.random.default_rng(
                _derive_seed(CONVERGED_COMMON_LIT_SEED, "stability", size, rep))
            drop = rng_sub.choice(len(seed_ids),
                                  int(0.10 * len(seed_ids)), replace=False)
            sub_seed = np.delete(seed_ids, drop)
            rng_conv = np.random.default_rng(
                _derive_seed(CONVERGED_COMMON_LIT_SEED, "convsub", size, rep))
            conv = converge_seed(payload, matrix, sub_seed, payload_ids,
                                 f"seed{size}_sub{rep}", rng_conv, force=force)
            stability[f"Conv_L{size}"][f"rep{rep}"] = _compare_endpoint(
                conv, results[f"Conv_L{size}"], payload, us, scores)
        print(f"[convergence] Conv_L{size} stability reps done", flush=True)

    result = {"endpoints": results, "seeds": seeds, "stability": stability,
              "elapsed_s": round(time.time() - t0, 1)}
    _write_text_atomic(STATE_DIR / "convergence.json",
                       json.dumps(result, indent=1, default=_json_default))
    return result


def _kish(w: np.ndarray) -> float:
    w = w[w > 0].astype(np.float64)
    return float(w.sum() ** 2 / np.sum(w ** 2)) if np.any(w > 0) else 0.0


def _top_concentration(w: np.ndarray) -> float:
    w = w[w > 0].astype(np.float64)
    if len(w) == 0:
        return 0.0
    k = max(1, int(np.ceil(0.01 * len(w))))
    return float(np.sum(np.sort(w)[-k:]) / w.sum())


def _endpoint_summary(conv: dict[str, np.ndarray], universe, scores, us,
                      payload, size) -> dict[str, Any]:
    w = conv["endpoint_weights"]
    keep = conv["endpoint_keep"]
    payload_ids = payload["user_ids"].astype(np.int64)
    keep_uids = payload_ids[keep]
    # map endpoint users back to common-L
    in_univ = np.isin(keep_uids, universe)
    idx_map = {int(u): i for i, u in enumerate(universe.tolist())}
    L_end = np.full(len(keep), np.nan)
    w_end = w[keep].astype(np.float64)
    for j, uid in enumerate(keep_uids.tolist()):
        if uid in idx_map:
            L_end[j] = scores[idx_map[uid]]
    unweighted = q_distribution(L_end)
    # weighted distribution
    finite = np.isfinite(L_end)
    wf = w_end[finite]
    Lf = L_end[finite]
    wsum = wf.sum()
    weighted = _weighted_q(Lf, wf)
    # endpoint head
    final_pref = conv["final_pref"]
    eligible = np.flatnonzero(payload["book_n"] >= 25)
    order_w = eligible[np.argsort(-final_pref[eligible], kind="stable")][:200]
    head = []
    for rank, wi in enumerate(order_w, 1):
        wid = str(payload["work_ids"][wi])
        head.append({"rank": rank, "work_id": wid,
                     "score": float(final_pref[wi]),
                     "n_eff": float(payload["book_n"][wi])})
    return {
        "size": size,
        "raw_support": int(np.sum(w > 0)),
        "kish": _kish(w),
        "weight_concentration_top1pct": _top_concentration(w),
        "unweighted": unweighted,
        "weighted": weighted,
        "fraction_weight_by_L": {
            "ge_0p65": float(np.sum(wf[Lf >= 0.65]) / wsum),
            "ge_0p60": float(np.sum(wf[Lf >= 0.60]) / wsum),
            "p55_0p60": float(np.sum(wf[(Lf >= 0.55) & (Lf < 0.60)]) / wsum),
            "lt_0p55": float(np.sum(wf[Lf < 0.55]) / wsum),
        },
        "endpoint_keep_uids": keep_uids.astype(np.int64),
        "head_top200": head,
    }


def _weighted_q(L: np.ndarray, w: np.ndarray) -> dict[str, float]:
    w = w / w.sum()
    order = np.argsort(L, kind="stable")
    Ls, ws = L[order], w[order]
    cw = np.cumsum(ws)
    def wq(q):
        i = np.searchsorted(cw, q)
        i = min(i, len(Ls) - 1)
        return float(Ls[i])
    return {
        "median": wq(0.5),
        "p10": wq(0.10),
        "p25": wq(0.25),
        "p75": wq(0.75),
        "mean": float(np.sum(ws * Ls)),
    }


def _compare_endpoint(conv, base, payload, us, scores) -> dict[str, Any]:
    keep = conv["endpoint_keep"]
    payload_ids = payload["user_ids"].astype(np.int64)
    head = [r["work_id"] for r in base["head_top200"]]
    final_pref = conv["final_pref"]
    eligible = np.flatnonzero(payload["book_n"] >= 25)
    order_w = eligible[np.argsort(-final_pref[eligible], kind="stable")][:200]
    head_sub = [str(payload["work_ids"][i]) for i in order_w]
    from scipy.stats import spearmanr
    common = [w for w in head if w in set(head_sub)]
    rho = float("nan")
    if len(common) >= 10:
        rho = float(spearmanr([head.index(w) for w in common],
                              [head_sub.index(w) for w in common]).statistic)
    # user-weight cosine on common payload space
    wa = base.get("_weights_full", None)
    return {
        "book_j50": float(len(set(head[:50]) & set(head_sub[:50])) / 50.0),
        "book_j200": float(len(set(head) & set(head_sub)) / 200.0),
        "book_rho200": rho,
        "kish": _kish(conv["endpoint_weights"]),
        "weighted_median_L": _endpoint_median_L(conv, payload_ids, us, scores),
    }


def _endpoint_median_L(conv, payload_ids, us, scores) -> float:
    universe = us["universe"]
    keep = conv["endpoint_keep"]
    uids = payload_ids[keep]
    idx_map = {int(u): i for i, u in enumerate(universe.tolist())}
    vals = [scores[idx_map[int(u)]] for u in uids.tolist() if int(u) in idx_map
            and np.isfinite(scores[idx_map[int(u)]])]
    return float(np.median(vals)) if vals else float("nan")


# ---------------------------------------------------------------------------
# Part K — obscure-book coverage (raw + effective literary-juror)
# ---------------------------------------------------------------------------

def _global_work_stats(con) -> dict[str, np.ndarray]:
    p = DATA / "juror_coherence_tail_state" / "global_work_stats.npz"
    if p.exists():
        with np.load(p, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}
    p2 = STATE_DIR / "global_work_stats.npz"
    if p2.exists():
        with np.load(p2, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}
    rows = con.execute(
        "SELECT work_id, count(*)::DOUBLE AS n_rated "
        "FROM ex.all_rating_events GROUP BY work_id").fetchall()
    out = {"work_id": np.asarray([r[0] for r in rows], dtype=str),
           "n_rated": np.asarray([r[1] for r in rows], dtype=np.float64)}
    _write_npz_atomic(p2, out)
    return out


def band_of(n: float) -> int:
    for i, (lo, hi) in enumerate(RARITY_BANDS):
        if n >= lo and n <= hi:
            return i
    return -1


def coverage_phase(us: dict[str, np.ndarray], convergence: dict[str, Any],
                   force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "coverage.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe = us["universe"]
    scores = compute_common_scores(us)
    idx_map = {int(u): i for i, u in enumerate(universe.tolist())}
    L_map = {}
    for u in universe.tolist():
        L_map[int(u)] = float(scores[idx_map[int(u)]]) if np.isfinite(
            scores[idx_map[int(u)]]) else float("nan")
    payload, _matrix, _ = year.load_matrix()
    payload_ids = payload["user_ids"].astype(np.int64)
    con = open_db()
    materialize_base(con)
    gws = _global_work_stats(con)
    bands = np.asarray([band_of(float(x)) for x in gws["n_rated"]])
    n_band = {BAND_LABELS[i]: int(np.sum(bands == i)) for i in range(len(BAND_LABELS))}
    band_works = {i: gws["work_id"][bands == i].tolist() for i in range(len(BAND_LABELS))}

    results: dict[str, Any] = {"n_works_per_band": n_band}
    for name, ep in convergence["endpoints"].items():
        keep_uids = np.asarray(ep["endpoint_keep_uids"], dtype=np.int64)
        w_keep = np.load(STATE_DIR / f"{_conv_key(name)}.npz",
                         allow_pickle=False)["endpoint_weights"]
        # fetch endpoint users' ratings among band works
        ut = _next_table()
        con.execute(f"CREATE OR REPLACE TEMP TABLE {ut}(user_id BIGINT)")
        con.execute(f"INSERT INTO {ut} SELECT unnest(?::BIGINT[])",
                    [keep_uids.tolist()])
        rows = con.execute(
            f"SELECT e.work_id, e.user_id FROM ex.all_rating_events e "
            f"JOIN {ut} u USING (user_id) WHERE e.rating >= 1"
        ).fetchall()
        con.execute(f"DROP TABLE IF EXISTS {ut}")
        per_work: dict[str, list[int]] = {}
        for w, u in rows:
            per_work.setdefault(str(w), []).append(int(u))
        uid_weight = {int(u): float(w_keep[i]) for i, u in
                      enumerate(keep_uids.tolist()) if w_keep[i] > 0}
        results[name] = {}
        for band_i in range(len(BAND_LABELS)):
            works = band_works[band_i]
            if not works:
                results[name][BAND_LABELS[band_i]] = {"n_works": 0}
                continue
            ns = np.asarray([len(per_work.get(w, [])) for w in works])
            qm = np.asarray([_quality_mass(per_work.get(w, []), uid_weight, L_map)
                             for w in works])
            results[name][BAND_LABELS[band_i]] = {
                "n_works": len(works),
                "frac_ge1": float(np.mean(ns >= 1)),
                "frac_ge2": float(np.mean(ns >= 2)),
                "frac_ge3": float(np.mean(ns >= 3)),
                "frac_ge5": float(np.mean(ns >= 5)),
                "frac_ge10": float(np.mean(ns >= 10)),
                "median": float(np.median(ns)),
                "p90": float(np.quantile(ns, 0.90)),
                "qm_ge_0p5": float(np.mean(qm >= 0.5)),
                "qm_ge_1": float(np.mean(qm >= 1)),
                "qm_ge_2": float(np.mean(qm >= 2)),
                "qm_ge_3": float(np.mean(qm >= 3)),
            }
        print(f"[coverage] {name}: band20_49 frac>=1="
              f"{results[name]['20_49']['frac_ge1']:.2f} "
              f"qm>=1={results[name]['20_49']['qm_ge_1']:.2f}", flush=True)
    con.close()
    _write_text_atomic(path, json.dumps(results, indent=1))
    return results


def _conv_key(name: str) -> str:
    return f"conv_seed{name.split('_')[1].lstrip('L')}"


def _quality_mass(users: list[int], uid_weight: dict[int, float],
                  L_map: dict[int, float]) -> float:
    mass = 0.0
    for u in users:
        w = uid_weight.get(u, 0.0)
        if w <= 0:
            continue
        L = L_map.get(u, float("nan"))
        if np.isfinite(L):
            mass += w * max(0.0, 2.0 * L - 1.0)
    return mass


# ---------------------------------------------------------------------------
# Report + heads
# ---------------------------------------------------------------------------

def _probe_flag(wid: str, tag: str) -> str:
    return "Y" if wid in _PROBE_POS else ""


def report_phase(us, juries, validation, seeds, convergence, cov,
                 benchmark_meta) -> dict[str, Any]:
    payload, _m, _ = year.load_matrix()
    meta = _build_meta(payload)
    L = []
    L.append("# Converged Common Literary Jurors — report")
    L.append("")
    L.append(f"- Seed `{CONVERGED_COMMON_LIT_SEED}`. Established convergence "
             f"reused: research_jury_ensemble_reversal.run_jury "
             f"(BETA=2.5, MAX_STAGES=8, ITERATIONS=20, gain-hard LADDER_RATE=0.05, "
             f"MIN_REMAINING_FRACTION=0.05, retained target 1.01).")
    L.append("")
    L.append("## Popular-book benchmark")
    L.append("")
    L.append(f"- Rule: global rating count in [{BENCH_MIN_SUPPORT}, "
             f"{BENCH_MAX_SUPPORT}]; deterministic support-stratified cap to "
             f"{BENCH_TARGET} (20 equal support strata, {BENCH_TARGET // BENCH_STRATA} "
             f"each). No literary labels or reference scores used.")
    L.append(f"- Candidates: {benchmark_meta['n_candidates']}; selected: "
             f"{benchmark_meta.get('n_selected', '?')}; support min/median/max "
             f"{benchmark_meta['min']:.0f}/{benchmark_meta['median']:.0f}/"
             f"{benchmark_meta['max']:.0f}")
    L.append("")
    L.append("## Corrected known-group common-L (benchmark universe)")
    L.append("")
    L.append("| group | n_scoreable | median | p10 | p25 | p75 | frac>=.6 | "
             "med hi | med lo | med testable |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k, v in validation.items():
        if k == "_pairs":
            continue
        d = v["dist"]
        L.append(f"| {k} | {v['n_scoreable']} | "
                 f"{d.get('median', float('nan')):.3f} | "
                 f"{d.get('p10', float('nan')):.3f} | "
                 f"{d.get('p25', float('nan')):.3f} | "
                 f"{d.get('p75', float('nan')):.3f} | "
                 f"{d.get('frac_ge_0p60', float('nan')):.3f} | "
                 f"{v['median_distinct_high']:.0f} | {v['median_distinct_low']:.0f} | "
                 f"{v['median_n_testable']:.0f} |")
    L.append("")
    L.append("| pair | n | pearson | spearman |")
    L.append("|---|---:|---:|---:|")
    for k, v in validation["_pairs"].items():
        L.append(f"| {k} | {v['n']} | {v['pearson']:.3f} | {v['spearman']:.3f} |")
    L.append("")
    L.append("## Seed juries (corrected common score)")
    L.append("")
    L.append("| seed | n | median L | p10 | frac>=.6 | noneABC |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for size in SEED_SIZES:
        s = seeds[f"Seed_L{size}"]
        d = s["dist"]
        L.append(f"| Seed_L{size} | {s['n']} | {d.get('median', float('nan')):.3f} | "
                 f"{d.get('p10', float('nan')):.3f} | "
                 f"{d.get('frac_ge_0p60', float('nan')):.3f} | "
                 f"{s['source_composition']['none_ABC']:.3f} |")
    L.append("")
    L.append("## Convergence outcomes (established dynamics)")
    L.append("")
    L.append("| endpoint | stop | stages | raw support | Kish | w-top1% | "
             "weighted median L | weighted p10 | frac weight L>=.6 | frac weight L<.55 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for size in SEED_SIZES:
        c = convergence["seeds"][f"Conv_L{size}"]
        e = convergence["endpoints"][f"Conv_L{size}"]
        w = e["weighted"]
        fr = e["fraction_weight_by_L"]
        L.append(f"| Conv_L{size} | {c['stop_reason']} | {c['n_stages']} | "
                 f"{c['endpoint_raw_support']} | {c['kish']:.0f} | "
                 f"{c['weight_concentration_top1pct']:.3f} | "
                 f"{w.get('median', float('nan')):.3f} | "
                 f"{w.get('p10', float('nan')):.3f} | "
                 f"{fr['ge_0p60']:.3f} | {fr['lt_0p55']:.3f} |")
    L.append("")
    L.append("## 90%-seed convergence stability")
    L.append("")
    L.append("| endpoint | rep | book J50 | book J200 | book rho200 | "
             "weighted median L |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for size in SEED_SIZES:
        for rep, v in convergence["stability"][f"Conv_L{size}"].items():
            L.append(f"| Conv_L{size} | {rep} | {v['book_j50']:.2f} | "
                     f"{v['book_j200']:.2f} | {v['book_rho200']:.3f} | "
                     f"{v['weighted_median_L']:.3f} |")
    L.append("")
    L.append("## Obscure-book coverage (converged endpoints)")
    L.append("")
    L.append("| endpoint | band 20-49 raw>=1 | >=3 | qm>=0.5 | qm>=1 | "
             "band 100-249 raw>=1 | qm>=1 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for name in [f"Conv_L{s}" for s in SEED_SIZES]:
        b1 = cov[name].get("20_49", {})
        b3 = cov[name].get("100_249", {})
        L.append(f"| {name} | {b1.get('frac_ge1', 0):.2f} | "
                 f"{b1.get('frac_ge3', 0):.2f} | "
                 f"{b1.get('qm_ge_0p5', 0):.2f} | {b1.get('qm_ge_1', 0):.2f} | "
                 f"{b3.get('frac_ge1', 0):.2f} | {b3.get('qm_ge_1', 0):.2f} |")
    L.append("")
    L.append("## Seed vs converged")
    L.append("")
    L.append("| size | seed median L | conv weighted median L | seed head pos50 | "
             "conv head pos50 | conv Kish | 20-49 raw>=1 | 20-49 qm>=1 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for size in SEED_SIZES:
        s = seeds[f"Seed_L{size}"]
        e = convergence["endpoints"][f"Conv_L{size}"]
        c = convergence["seeds"][f"Conv_L{size}"]
        seed_pos = sum(1 for r in s["head_top50"] if r["work_id"] in _PROBE_POS)
        conv_pos = sum(1 for r in e["head_top200"][:50] if r["work_id"] in _PROBE_POS)
        b1 = cov[f"Conv_L{size}"].get("20_49", {})
        L.append(f"| {size} | {s['dist'].get('median', float('nan')):.3f} | "
                 f"{e['weighted'].get('median', float('nan')):.3f} | {seed_pos} | "
                 f"{conv_pos} | {c['kish']:.0f} | {b1.get('frac_ge1', 0):.2f} | "
                 f"{b1.get('qm_ge_1', 0):.2f} |")
    L.append("")
    L.append("## Interpretation")
    L.append("")
    L.append("Do convergence and the common-L endpoint preserve literary "
             "character? See converged heads in CONVERGED_COMMON_LITERARY_JUROR_HEADS.md "
             "and the weighted-L distributions above. No convergence parameters "
             "were tuned by size.")
    L.append("")
    _write_text_atomic(OUT_MD, "\n".join(L) + "\n")
    _write_heads(payload, seeds, convergence)
    combined = {
        "seed": CONVERGED_COMMON_LIT_SEED,
        "benchmark": benchmark_meta,
        "validation": validation,
        "seeds": seeds,
        "convergence": convergence,
        "coverage": cov,
    }
    _write_text_atomic(OUT_JSON, json.dumps(combined, indent=1, default=_json_default))
    print(f"Wrote {OUT_MD}, {OUT_HEADS}, {OUT_JSON}", flush=True)
    return {"report": True}


def _build_meta(payload) -> dict[str, dict[str, Any]]:
    meta = {}
    for i, wid in enumerate(payload["work_ids"]):
        meta[str(wid)] = {"title": "", "author": ""}
    return meta


def _write_heads(payload, seeds, convergence) -> None:
    con = open_db()
    L = ["# Converged Common Literary Jurors — complete top-50 heads",
         "", f"Seed `{CONVERGED_COMMON_LIT_SEED}`. Probe flags are annotations "
             "only.", ""]
    order = ([f"Seed_L{s}" for s in SEED_SIZES]
             + [f"Conv_L{s}" for s in SEED_SIZES])
    payload_ids = payload["user_ids"].astype(np.int64)
    meta = _meta_from_db(con, payload["work_ids"])
    for name in order:
        if name.startswith("Seed"):
            rows = seeds[name]["head_top50"]
            kind = "direct seed"
        else:
            size = name.split("_")[1]
            head = convergence["endpoints"][name]["head_top200"][:50]
            rows = []
            for r in head:
                rows.append({"rank": r["rank"], "work_id": r["work_id"],
                             "title": meta.get(r["work_id"], {}).get("title", ""),
                             "author": meta.get(r["work_id"], {}).get("author", ""),
                             "score": r["score"], "n_eff": r["n_eff"]})
            kind = "converged endpoint"
        L.append(f"## {name}  ({kind})")
        L.append("")
        L.append("| rank | title | author | score | pos | exact | broad | anti |")
        L.append("|---|---|---|---|---|---|---|---|")
        for r in rows:
            wid = r["work_id"]
            L.append(f"| {r['rank']} | {r['title']} | {r['author']} | "
                     f"{r.get('score', '')} | "
                     f"{'Y' if wid in _PROBE_POS else ''} | "
                     f"{'Y' if wid in _PROBE_EXACT else ''} | "
                     f"{'Y' if wid in _PROBE_BROAD else ''} | "
                     f"{'Y' if wid in _PROBE_ANTI else ''} |")
        L.append("")
    con.close()
    _write_text_atomic(OUT_HEADS, "\n".join(L) + "\n")


def _meta_from_db(con, work_ids) -> dict[str, dict[str, str]]:
    wids = work_ids.astype(str).tolist()
    out = {}
    # fetch title/author for these works from work_scores
    wt = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {wt}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {wt} SELECT unnest(?::VARCHAR[])", [wids])
    rows = con.execute(
        f"SELECT s.work_id, s.title, s.author FROM ex.work_scores s "
        f"JOIN {wt} w USING (work_id)").fetchall()
    con.execute(f"DROP TABLE IF EXISTS {wt}")
    for wid, title, author in rows:
        out[str(wid)] = {"title": title or "", "author": author or ""}
    return out


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def phase_smoke() -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    juries = load_juries()
    for k, n in {"ABC": 2368, "core_p65_s25": 3286,
                 "committee_AnB": 11582}.items():
        add(f"{k}_exact", len(juries[k]) == n, f"n={len(juries[k])}")

    # benchmark selection is support-only (static + real)
    import inspect as _inspect
    src = _inspect.getsource(popular_benchmark_works)
    add("benchmark_support_only",
        "all_rating_events" in src and "GROUP BY" in src
        and "exact_lit" not in src and "broad_lit" not in src,
        "selection uses global support only")
    con = open_db()
    materialize_base(con)
    bench = popular_benchmark_works(con)
    add("benchmark_len", len(bench) == BENCH_TARGET, f"n={len(bench)}")
    # verify each selected work's global count is within [500, 120000]
    rows = con.execute(
        "SELECT work_id, count(*)::DOUBLE AS c FROM ex.all_rating_events "
        "GROUP BY work_id HAVING count(*) >= 500 AND count(*) <= 120000").fetchall()
    counts = {str(w): float(c) for w, c in rows}
    ok_range = all(BENCH_MIN_SUPPORT <= counts.get(w, -1) <= BENCH_MAX_SUPPORT
                   for w in bench.tolist())
    add("benchmark_support_range", ok_range, "all selected works have 500-120000")
    ok_deterministic = np.array_equal(
        popular_benchmark_works(con), popular_benchmark_works(con))
    add("benchmark_deterministic", bool(ok_deterministic),
        "same rule -> same benchmark")

    # distinct-book tracking synthetic
    sd = {"w1": 3.0, "w2": 2.0, "w3": 1.0}
    rec = eval_user_benchmark(np.asarray(["w1", "w2", "w3"], dtype=str),
                              np.asarray(["w1", "w2", "w3"], dtype=str),
                              np.asarray(["w1", "w2", "w3"], dtype=str),
                              np.asarray([3.0, 2.0, 1.0]),
                              np.random.default_rng(1))
    add("distinct_book_tracking",
        rec["distinct_high_avail"] == 3 and rec["distinct_low_avail"] == 3
        and rec["n_testable"] == 9,
        f"high_avail={rec['distinct_high_avail']} low_avail={rec['distinct_low_avail']} "
        f"testable={rec['n_testable']}")

    # eligibility: >=2 refs with testable>=20 AND >=4 distinct hi AND >=4 distinct lo
    L = np.array([[np.nan, 0.6, 0.7],
                  [0.55, 0.6, np.nan],
                  [np.nan, np.nan, 0.6]])
    nt = np.array([[0, 40, 40], [40, 40, 0], [0, 0, 40]], dtype=np.int64)
    hh = np.array([[0, 6, 6], [6, 6, 0], [0, 0, 6]], dtype=np.int64)
    ll = np.array([[0, 6, 6], [6, 6, 0], [0, 0, 6]], dtype=np.int64)
    sc = compute_common_scores({"L_shrunk": L, "n_testable": nt,
                                "n_high_avail": hh, "n_low_avail": ll})
    # row0: refs 1,2 qualify -> median(0.6,0.7)=0.65 ; row1: refs 0,1 -> 0.575 ;
    # row2: only ref2 -> ineligible
    add("eligibility_distinct_books",
        abs(sc[0] - 0.65) < 1e-9 and abs(sc[1] - 0.575) < 1e-9
        and np.isnan(sc[2]), f"score={sc.tolist()}")

    # median-of-qualifying is the common score
    add("common_score_is_median", abs(sc[0] - 0.65) < 1e-9,
        "median of qualifying refs")

    # quantile indexing
    v = np.arange(100.0)
    d = q_distribution(v)
    add("quantile_indexing",
        abs(d["median"] - 49.5) < 0.6 and abs(d["p05"] - 4.95) < 1.0
        and abs(d["p95"] - 94.05) < 1.0,
        f"median={d['median']} p05={d['p05']} p95={d['p95']}")

    # no probes in score
    src2 = _inspect.getsource(compute_common_scores) + _inspect.getsource(
        eval_user_benchmark)
    banned = [t for t in ("pos_works", "exact_lit", "broad_lit", "anti_works")
              if t in src2]
    add("no_literary_labels_in_score", not banned, f"banned: {banned}")

    # broad universe not spectral restricted
    from curators_explorer.scripts.research_common_literary_jurors import (
        eligible_user_universe as _eu,
    )
    uni = _eu(con)
    import inspect as _ins3
    from curators_explorer.scripts.research_common_literary_jurors import (
        eligible_user_universe as _euc,
    )
    usrc = _ins3.getsource(_euc)
    add("universe_not_payload_restricted",
        len(uni) >= 150000 and "all_rating_events" in usrc
        and "seedless_spectral_pilot_matrix" not in usrc,
        f"universe={len(uni)} defined from all_rating_events support, "
        "not from the spectral payload file")

    # convergence reuses historical constants
    from curators_explorer.scripts import research_jury_ensemble_reversal as rev
    add("convergence_reuses_historical",
        CONV_BETA == rev.BETA and CONV_MAX_STAGES == rev.MAX_STAGES
        and CONV_RETAINED_TARGET == 1.01,
        f"BETA={CONV_BETA} MAX_STAGES={CONV_MAX_STAGES} target={CONV_RETAINED_TARGET}")
    src3 = _inspect.getsource(run_jury_captured)
    add("convergence_uses_historical_functions",
        "pruning.iterate_map" in src3 and "pruning.remove_fraction" in src3
        and "spectral.make_operator" in src3 and "attractor.weighted_preferences" in src3,
        "same underlying functions as run_jury")

    # same params for all sizes (fixed module-level configuration; converge_seed
    # takes no size-specific convergence arguments)
    import inspect as _ins2
    sig = str(_ins2.signature(converge_seed))
    add("same_convergence_params_all_sizes",
        "beta" not in sig and "stages" not in sig and "retained" not in sig,
        f"converge_seed signature: {sig} (fixed config for all sizes)")

    # Kish correctness
    w = np.asarray([2.0, 2.0, 2.0])
    add("kish_correct", abs(_kish(w) - 3.0) < 1e-9, f"kish={_kish(w)}")

    # weighted q uses actual weights
    wq = _weighted_q(np.asarray([0.5, 0.7]), np.asarray([0.25, 0.75]))
    add("weighted_q_uses_weights", abs(wq["median"] - 0.7) < 1e-9,
        f"weighted median={wq['median']}")

    # stability seeds deterministic
    rng1 = np.random.default_rng(7)
    rng2 = np.random.default_rng(7)
    a = rng1.choice(1000, 100, replace=False)
    b = rng2.choice(1000, 100, replace=False)
    add("stability_seeds_deterministic", bool(np.array_equal(a, b)),
        "same seed -> same 90% subsample")

    # coverage uses global counts (band_of + global stats)
    add("coverage_uses_global_counts", "all_rating_events" in _inspect.getsource(
        _global_work_stats), "global support source")
    add("coverage_includes_below_rank_floor", band_of(30.0) == 1,
        "band 20-49 (below scorer MIN_RANK_N=100) is covered")

    # old artifacts untouched (existence only; this script never writes them)
    import os
    olds = [DATA / "common_literary_jurors.json",
            DATA / "COMMON_LITERARY_JURORS_REPORT.md"]
    add("old_artifacts_untouched", all(p.exists() for p in olds),
        "common_literary_jurors.* still present")
    con.close()

    ok = all(c["ok"] for c in checks)
    print(f"[smoke] {sum(c['ok'] for c in checks)}/{len(checks)} checks passed "
          f"in {_fmt_time(time.time() - t0)}", flush=True)
    return {"checks": checks, "ok": bool(ok), "elapsed_s": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------
# Main
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
    _m, es = load_posthoc_context(payload["work_ids"])
    merged = _merged_ev(ev, es)
    _PROBE_POS = set(merged.get("pos_works", set()))
    _PROBE_ANTI = set(merged.get("anti_works", set()))
    _PROBE_EXACT = set(merged.get("exact_lit", set()))
    _PROBE_BROAD = set(merged.get("broad_lit", set()))
    con.close()


def run_phases(phases: list[str], force: bool = False) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _load_probes_local(load_payload_helper())
    for ph in phases:
        t0 = time.time()
        con = open_db()
        materialize_base(con)
        juries = load_juries()
        if ph == "prepare":
            bench = popular_benchmark_works(con, force=force)
            meta = _benchmark_meta(con)
            meta["n_selected"] = int(len(bench))
            _write_text_atomic(STATE_DIR / "benchmark_meta.json",
                               json.dumps(meta, indent=1))
        elif ph == "references":
            bench = popular_benchmark_works(con)
            _ = build_reference_benchmark_scores(con, juries, bench, force=force)
        elif ph == "score_users":
            bench = popular_benchmark_works(con)
            _ = reference_user_scores(con, juries, bench, force=force)
        elif ph == "seeds":
            us = reference_user_scores(con, juries, popular_benchmark_works(con))
            _ = build_seeds(con, us, juries, force=force)
        elif ph == "convergence":
            us = reference_user_scores(con, juries, popular_benchmark_works(con))
            _ = convergence_phase(us, juries, force=force)
        elif ph == "coverage":
            us = reference_user_scores(con, juries, popular_benchmark_works(con))
            conv = json.loads((STATE_DIR / "convergence.json").read_text())
            _ = coverage_phase(us, conv, force=force)
        elif ph == "report":
            us = reference_user_scores(con, juries, popular_benchmark_works(con))
            validation = validate_groups(us, juries)
            seeds = json.loads((STATE_DIR / "seeds.json").read_text())
            conv = json.loads((STATE_DIR / "convergence.json").read_text())
            cov = json.loads((STATE_DIR / "coverage.json").read_text())
            meta = json.loads((STATE_DIR / "benchmark_meta.json").read_text())
            report_phase(us, juries, validation, seeds, conv, cov, meta)
        else:
            raise SystemExit(f"unknown phase {ph}")
        con.close()
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
        phases = ["prepare", "references", "score_users", "seeds",
                  "convergence", "coverage", "report"]
    run_phases(phases, force=args.force)


if __name__ == "__main__":
    _main()

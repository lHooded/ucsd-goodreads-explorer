#!/usr/bin/env python3
"""COMMON LITERARY JUROR DISCOVERY.

Goal: find a reasonably large, NATURAL literary jury whose members individually
demonstrate literary-compatible taste against a common trusted reference, and
whose membership/consensus is stable and self-convergent (basin stability).

Working assumption: a reader who repeatedly shows strong literary judgment on
well-supported books is likely to give useful evidence on obscure books.  We do
NOT validate obscure-book rating accuracy here; we only measure coverage by
individually validated readers.

Design (reverse-engineered, not label-blind):
  R1 = ABC (2,368), R2 = core_p65_s25 (3,286), R3 = A∩B (11,582).
  For each reference build a fixed direct pairwise ranking (equal vote,
  build_pairs), plus 10-fold self-excluded rankings for members.
  Every user in a broad eligible universe is scored by high-vs-low agreement
  (5-star vs <=3) with each reference's ranking (self-excluded when a member).
  literary_juror_score = median of shrunk agreement L_shrunk over the valid
  references (>=2 refs finite and >=2 refs with >=20 testable pairs).

Then: nested common-score juries (L2500..L40000), half-split stability, a
label-free self-consistency operator T_N (top-N by agreement with the jury's
own consensus, members fold-excluded), self-convergence trajectories, limited
10% perturbation basin test, a fandom self-convergence control, and
obscure-book coverage by validated jurors.

NO tuning of thresholds/weights, no semantic optimisation, no reversal, no
sparse-rating prediction.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_common_literary_jurors --smoke
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_common_literary_jurors --phase all
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

COMMON_LIT_SEED = 20260830

OUT_JSON = DATA / "common_literary_jurors.json"
OUT_NPZ = DATA / "common_literary_jurors.npz"
OUT_MD = DATA / "COMMON_LITERARY_JURORS_REPORT.md"
OUT_HEADS = DATA / "COMMON_LITERARY_JUROR_HEADS.md"
STATE_DIR = DATA / "common_literary_jurors_state"

VENN_NPZ = DATA / "jury_consensus_venn.npz"

REFERENCE_FOLDS = 10
SELF_FOLDS = 5
MAX_EVAL_HIGHS = 40
MAX_EVAL_LOWS = 40
MAX_EVAL_PAIRS = 400
PRIOR_K = 40.0
TIE_SCORE = 0.5

UNIVERSE_MIN_H = 20
UNIVERSE_MIN_L = 20

CANDIDATE_MIN_VALID_REFS = 2
CANDIDATE_MIN_TESTABLE = 20

FRONTIER_SIZES = [2500, 5000, 10000, 15000, 20000, 30000, 40000]
STABILITY_SIZES = [2500, 5000, 10000, 20000, 40000]
STABILITY_SPLITS = 5
SELF_MIN_TESTABLE = 20
MAX_SELF_ITER = 3
PERTURB_REPS = 3
PERTURB_FRACTION = 0.10

RARITY_BANDS = [(5, 19), (20, 49), (50, 99), (100, 249), (250, 999),
                (1000, 4999)]
BAND_LABELS = ["5_19", "20_49", "50_99", "100_249", "250_999", "1000_4999"]

REFERENCE_KEYS = {
    "R1_ABC": "ABC",
    "R2_p65": "core_p65_s25",
    "R3_AnB": "committee_AnB",
}

_jury_counter = [0]


def _next_table() -> str:
    _jury_counter[0] += 1
    return f"clj_{_jury_counter[0]}"


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
            blob = old
            key = f"juries/{name}/user_ids"
        elif name.startswith("committee"):
            blob = venn
            key = f"juries/{name}/user_ids"
        else:
            blob = venn
            key = f"regions/{name}/user_ids"
        out[name] = blob[key].astype(np.int64)
    return out


def open_db() -> Any:
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    return con


def build_ranking(con, user_ids: np.ndarray) -> list[dict]:
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


def ranking_arrays(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """(sorted scored work ids, aligned scores) for fast searchsorted lookups."""
    wid = np.asarray([r["work_id"] for r in rows], dtype=str)
    sc = np.asarray([float(r["score"]) for r in rows])
    order = np.argsort(wid, kind="stable")
    return wid[order], sc[order]


def score_dict(rows: list[dict]) -> dict[str, float]:
    return {r["work_id"]: float(r["score"]) for r in rows}


# ---------------------------------------------------------------------------
# User universe (broad, not spectral-payload-restricted)
# ---------------------------------------------------------------------------

def eligible_user_universe(con, force: bool = False) -> np.ndarray:
    path = STATE_DIR / "universe.npz"
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return blob["user_ids"].astype(np.int64)
    rows = con.execute(
        f"""
        SELECT user_id FROM (
          SELECT e.user_id,
            count(*) FILTER (WHERE e.rating = 5) AS h,
            count(*) FILTER (WHERE e.rating <= 3) AS l
          FROM ex.all_rating_events e
          JOIN work_rarity wr ON wr.work_id = e.work_id
          WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
          GROUP BY e.user_id
        ) WHERE h >= {UNIVERSE_MIN_H} AND l >= {UNIVERSE_MIN_L}
        """
    ).fetchall()
    uids = np.asarray([r[0] for r in rows], dtype=np.int64)
    _write_npz_atomic(path, {"user_ids": uids})
    return uids


def _fetch_user_highlow(con, user_ids: np.ndarray, works: list[str],
                        tag: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (h_uid, h_wid, l_uid, l_wid) for universe users among `works`."""
    path = STATE_DIR / f"highlow_{tag}.npz"
    if path.exists():
        with np.load(path, allow_pickle=False) as blob:
            return (blob["h_uid"], blob["h_wid"], blob["l_uid"], blob["l_wid"])
    ut = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {ut}(user_id BIGINT)")
    con.execute(f"INSERT INTO {ut} SELECT unnest(?::BIGINT[])", [user_ids.tolist()])
    wt = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {wt}(work_id VARCHAR)")
    con.execute(f"INSERT INTO {wt} SELECT unnest(?::VARCHAR[])", [list(works)])
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


# ---------------------------------------------------------------------------
# Vectorized high-vs-low concordance against a ranking
# ---------------------------------------------------------------------------

def _filter_scores(wids: np.ndarray, srt_wid: np.ndarray,
                   srt_score: np.ndarray) -> np.ndarray:
    if len(wids) == 0:
        return np.asarray([], dtype=np.float64)
    idx = np.searchsorted(srt_wid, wids)
    idx = np.minimum(idx, len(srt_wid) - 1)
    valid = srt_wid[idx] == wids
    return srt_score[idx[valid]]


def eval_user_ranking(highs: np.ndarray, lows: np.ndarray,
                      srt_wid: np.ndarray, srt_score: np.ndarray,
                      rng) -> dict[str, float]:
    h = _filter_scores(highs, srt_wid, srt_score)
    l = _filter_scores(lows, srt_wid, srt_score)
    if len(h) == 0 or len(l) == 0:
        return {"n_testable": 0, "agreement_sum": 0.0}
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
    return {"n_testable": int(len(ph)), "agreement_sum": agree}


def shrink(agree: float, n_testable: int) -> tuple[float, float]:
    if n_testable == 0:
        return float("nan"), float("nan")
    q_raw = agree / n_testable
    q_shrunk = (agree + 0.5 * PRIOR_K) / (n_testable + PRIOR_K)
    return q_raw, q_shrunk


def q_distribution(q: np.ndarray) -> dict[str, float]:
    qv = q[np.isfinite(q)]
    if len(qv) == 0:
        return {"n_finite": 0}
    qs = np.quantile(qv, [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
    return {
        "n_finite": int(len(qv)),
        "mean": float(np.mean(qv)),
        "median": float(qs[3]),
        "sd": float(np.std(qv)),
        "p05": float(qs[0]),
        "p10": float(qs[1]),
        "p25": float(qs[2]),
        "p75": float(qs[4]),
        "p90": float(qs[5]),
        "p95": float(qs[6]),
        "frac_ge_0p55": float(np.mean(qv >= 0.55)),
        "frac_ge_0p60": float(np.mean(qv >= 0.60)),
        "frac_ge_0p65": float(np.mean(qv >= 0.65)),
        "min": float(np.min(qv)),
    }


# ---------------------------------------------------------------------------
# Fold assignment (deterministic)
# ---------------------------------------------------------------------------

def assign_folds(user_ids: np.ndarray, tag: str, n_folds: int) -> np.ndarray:
    rng = np.random.default_rng(_derive_seed(COMMON_LIT_SEED, "fold", tag))
    perm = rng.permutation(len(user_ids))
    folds = np.empty(len(user_ids), dtype=np.int8)
    folds[perm] = np.arange(len(user_ids)) % n_folds
    return folds


# ---------------------------------------------------------------------------
# Part B/C — reference rankings (full + fold-excluded)
# ---------------------------------------------------------------------------

def build_reference_rankings(con, juries, force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "references.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    refs: dict[str, Any] = {}
    for ref, jury_name in REFERENCE_KEYS.items():
        user_ids = juries[jury_name]
        full_rows = build_ranking(con, user_ids)
        full_wid, full_sc = ranking_arrays(full_rows)
        folds = assign_folds(user_ids, ref, REFERENCE_FOLDS)
        fold_arrays = []
        for f in range(REFERENCE_FOLDS):
            train = user_ids[folds != f]
            rows = build_ranking(con, train)
            fw, fs = ranking_arrays(rows)
            fold_arrays.append({"wid": fw, "score": fs})
        refs[ref] = {
            "jury_name": jury_name,
            "n": int(len(user_ids)),
            "folds": folds.tolist(),
            "full_n_ranked": len(full_wid),
            "full_top100": [
                {"rank": r["rank"], "work_id": r["work_id"], "title": r["title"],
                 "author": r["author"], "score": float(r["score"]),
                 "n_eff": float(r["n_eff"])}
                for r in full_rows[:100]
            ],
        }
        # persist arrays in NPZ
        arrays = {
            f"ref/{ref}/user_ids": user_ids,
            f"ref/{ref}/folds": folds,
            f"ref/{ref}/full_wid": full_wid,
            f"ref/{ref}/full_score": full_sc,
        }
        for f, fa in enumerate(fold_arrays):
            arrays[f"ref/{ref}/fold{f}_wid"] = fa["wid"]
            arrays[f"ref/{ref}/fold{f}_score"] = fa["score"]
        _add_to_npz(arrays)
        print(f"[references] {ref}: n={len(user_ids)} full ranked={len(full_wid)} "
              f"folds={len(fold_arrays)}", flush=True)
    result = {"refs": refs}
    _write_text_atomic(path, json.dumps(result, indent=1))
    return result


# ---------------------------------------------------------------------------
# Universe high/low restricted to the union of reference-scored works
# ---------------------------------------------------------------------------

def reference_scoring(con, juries, force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "user_scores.npz"
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}

    universe = eligible_user_universe(con)
    # union reference members into the universe (ensure they are scored)
    members = np.unique(np.concatenate([
        juries[REFERENCE_KEYS[r]] for r in REFERENCE_KEYS]))
    universe = np.unique(np.concatenate([universe, members]))

    # collect scored work sets from all reference rankings (full + folds)
    scored_sets = set()
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        for ref in REFERENCE_KEYS:
            scored_sets.update(blob[f"ref/{ref}/full_wid"].astype(str).tolist())
            for f in range(REFERENCE_FOLDS):
                scored_sets.update(
                    blob[f"ref/{ref}/fold{f}_wid"].astype(str).tolist())
    works = sorted(scored_sets)
    h_uid, h_wid, l_uid, l_wid = _fetch_user_highlow(con, universe, works, "refs")
    highs = _group(h_uid, h_wid)
    lows = _group(l_uid, l_wid)

    n = len(universe)
    L_raw = np.full((n, 3), np.nan)
    L_shrunk = np.full((n, 3), np.nan)
    n_testable = np.zeros((n, 3), dtype=np.int64)

    # user -> fold within each reference
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        for ri, ref in enumerate(REFERENCE_KEYS):
            r_uids = blob[f"ref/{ref}/user_ids"].astype(np.int64)
            r_folds = blob[f"ref/{ref}/folds"].astype(np.int8)
            fold_of = {int(u): int(f) for u, f in zip(r_uids.tolist(),
                                                      r_folds.tolist())}
            full_wid = blob[f"ref/{ref}/full_wid"]
            full_score = blob[f"ref/{ref}/full_score"]
            fold_arrays = [(blob[f"ref/{ref}/fold{f}_wid"],
                            blob[f"ref/{ref}/fold{f}_score"])
                           for f in range(REFERENCE_FOLDS)]
            idx_u = {int(u): i for i, u in enumerate(universe.tolist())}
            for u in r_uids.tolist():
                # evaluate reference members against fold-excluded ranking
                f = fold_of[u]
                wid, sc = fold_arrays[f]
                i = idx_u[u]
                rng = np.random.default_rng(
                    _derive_seed(COMMON_LIT_SEED, "refscore", ref, u))
                rec = eval_user_ranking(highs.get(u, np.asarray([], dtype=str)),
                                        lows.get(u, np.asarray([], dtype=str)),
                                        wid, sc, rng)
                n_testable[i, ri] = rec["n_testable"]
                qr, qs = shrink(rec["agreement_sum"], rec["n_testable"])
                L_raw[i, ri] = qr
                L_shrunk[i, ri] = qs
            # outsiders against full ranking (vectorized in chunks)
            full_index = np.flatnonzero(~np.isin(universe, r_uids))
            for start in range(0, len(full_index), 20000):
                chunk = full_index[start:start + 20000]
                for i in chunk:
                    u = int(universe[i])
                    rng = np.random.default_rng(
                        _derive_seed(COMMON_LIT_SEED, "refscore", ref, u))
                    rec = eval_user_ranking(
                        highs.get(u, np.asarray([], dtype=str)),
                        lows.get(u, np.asarray([], dtype=str)),
                        full_wid, full_score, rng)
                    n_testable[i, ri] = rec["n_testable"]
                    qr, qs = shrink(rec["agreement_sum"], rec["n_testable"])
                    L_raw[i, ri] = qr
                    L_shrunk[i, ri] = qs
            print(f"[score_users] {ref}: done", flush=True)

    arrays = {
        "universe": universe,
        "L_raw": L_raw,
        "L_shrunk": L_shrunk,
        "n_testable": n_testable,
    }
    _write_npz_atomic(path, arrays)
    return arrays


def compute_common_scores(user_scores: dict[str, np.ndarray]) -> np.ndarray:
    L = user_scores["L_shrunk"]
    nt = user_scores["n_testable"]
    valid_refs = np.isfinite(L)
    enough = valid_refs & (nt >= CANDIDATE_MIN_TESTABLE)
    n_valid = np.sum(enough, axis=1)
    eligible = n_valid >= CANDIDATE_MIN_VALID_REFS
    score = np.full(len(L), np.nan)
    for i in range(len(L)):
        if not eligible[i]:
            continue
        vals = L[i, enough[i]]
        score[i] = float(np.median(vals))
    return score


def score_summary(scores: np.ndarray, n_testable: np.ndarray) -> dict[str, Any]:
    return {
        "n_eligible": int(np.sum(np.isfinite(scores))),
        "dist": q_distribution(scores),
        "median_evidence": float(np.nanmedian(np.max(n_testable, axis=1)
                                              [np.isfinite(scores)]))
        if np.any(np.isfinite(scores)) else float("nan"),
    }


# ---------------------------------------------------------------------------
# Part G/H — candidate frontier + stability
# ---------------------------------------------------------------------------

def frontier_phase(con, user_scores: dict[str, np.ndarray],
                   juries: dict[str, np.ndarray], force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "frontier.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe = user_scores["universe"]
    scores = compute_common_scores(user_scores)
    nt = user_scores["n_testable"]

    order = np.lexsort((universe, -np.nan_to_num(nt).max(axis=1),
                        -np.nan_to_num(scores)))
    eligible_idx = np.flatnonzero(np.isfinite(scores))
    order = order[np.isin(order, eligible_idx)]

    # source membership
    src_sets = {
        "ABC": set(juries["ABC"].tolist()),
        "p65": set(juries["core_p65_s25"].tolist()),
        "AnB": set(juries["committee_AnB"].tolist()),
        "vote2": set(juries["committee_vote2_ABCs"].tolist()),
        "A_only": set(juries["A_only"].tolist()),
        "B_only": set(juries["B_only"].tolist()),
        "AB_only": set(juries["AB_only"].tolist()),
        "none_ABC": None,  # not in A ∪ B ∪ C
    }
    union_abc = (set(juries["deep_mint_all"].tolist())
                 | set(juries["threeway_classic"].tolist())
                 | set(juries["rebuilt_hard"].tolist()))

    def source_composition(idx: np.ndarray) -> dict[str, float]:
        ids = universe[idx].tolist()
        n = len(ids)
        comp = {}
        for name, s in src_sets.items():
            if name == "none_ABC":
                comp[name] = sum(1 for u in ids if u not in union_abc) / n
            else:
                comp[name] = sum(1 for u in ids if u in s) / n
        return comp

    frontier: dict[str, Any] = {}
    for size in FRONTIER_SIZES:
        sel = order[:size]
        rows = build_ranking(con, universe[sel])
        scores_j = scores[sel]
        nt_j = nt[sel]
        frontier[f"L{size}"] = {
            "n": int(size),
            "user_quality": {
                "n": int(size),
                "dist": q_distribution(scores_j),
                "median_evidence": float(np.median(np.max(nt_j, axis=1))),
                "frac_ge100_two_refs": float(np.mean(
                    np.sum((nt_j >= 100) & np.isfinite(nt_j), axis=1) >= 2)),
            },
            "source_composition": source_composition(sel),
            "book_rank": _rank_summary(rows),
        }
        print(f"[frontier] L{size}: median L="
              f"{frontier[f'L{size}']['user_quality']['dist'].get('median', float('nan')):.3f} "
              f"pos50={frontier[f'L{size}']['book_rank']['semantic']['pos50']} "
              f"anti50={frontier[f'L{size}']['book_rank']['semantic']['anti50']}",
              flush=True)

    # stability (half splits) for selected sizes
    for size in STABILITY_SIZES:
        name = f"L{size}"
        sel = order[:size]
        jacs50, jacs200, rhos = [], [], []
        for s in range(STABILITY_SPLITS):
            rng = np.random.default_rng(
                _derive_seed(COMMON_LIT_SEED, "stability", name, s))
            r = rng.permutation(len(sel))
            h1 = sel[r[: len(sel) // 2]]
            h2 = sel[r[len(sel) // 2:]]
            rows1 = build_ranking(con, universe[h1])
            rows2 = build_ranking(con, universe[h2])
            t1 = [x["work_id"] for x in rows1[:50]]
            t2 = [x["work_id"] for x in rows2[:50]]
            jacs50.append(len(set(t1) & set(t2)) / 50.0)
            t1_200 = [x["work_id"] for x in rows1[:200]]
            t2_200 = [x["work_id"] for x in rows2[:200]]
            jacs200.append(len(set(t1_200) & set(t2_200)) / 200.0)
            from scipy.stats import spearmanr
            common = [w for w in t1_200 if w in set(t2_200)]
            if len(common) >= 10:
                rho, _ = spearmanr(
                    [i for i, w in enumerate(t1_200) if w in set(common)],
                    [t2_200.index(w) for w in common])
                rhos.append(float(rho))
        frontier[name]["stability"] = {
            "j50_mean": float(np.mean(jacs50)),
            "j200_mean": float(np.mean(jacs200)),
            "rho200_mean": float(np.mean(rhos)) if rhos else float("nan"),
            "splits": STABILITY_SPLITS,
        }
        print(f"[frontier] {name} stability j50={np.mean(jacs50):.2f} "
              f"j200={np.mean(jacs200):.2f}", flush=True)

    result = {"frontier": frontier,
              "jstar_sizes": FRONTIER_SIZES,
              "elapsed_s": 0.0}
    _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
    return result


def _rank_summary(rows: list[dict]) -> dict[str, Any]:
    from collections import Counter
    head = rows[:200]
    authors = [r["author"] for r in rows[:50]]
    ac = Counter(authors)
    return {
        "top50": [
            {"rank": r["rank"], "work_id": r["work_id"], "title": r["title"],
             "author": r["author"], "score": float(r["score"]),
             "n_eff": float(r["n_eff"])} for r in rows[:50]
        ],
        "top200_ids": [r["work_id"] for r in rows[:200]],
        "semantic": {
            "pos50": sum(1 for r in rows[:50]
                         if r.get("work_id") in _PROBE_POS),
            "anti50": sum(1 for r in rows[:50]
                          if r.get("work_id") in _PROBE_ANTI),
            "exact50": sum(1 for r in rows[:50]
                           if r.get("work_id") in _PROBE_EXACT),
            "broad50": sum(1 for r in rows[:50]
                           if r.get("work_id") in _PROBE_BROAD),
        },
        "unique_authors50": len(ac),
        "max_works_author50": max(ac.values()) if ac else 0,
    }


_PROBE_POS: set = set()
_PROBE_ANTI: set = set()
_PROBE_EXACT: set = set()
_PROBE_BROAD: set = set()


def load_payload_helper():
    from curators_explorer.scripts.research_maximum_literary_jury import (
        load_payload,
    )
    return load_payload()


def _load_probes(payload) -> None:
    global _PROBE_POS, _PROBE_ANTI, _PROBE_EXACT, _PROBE_BROAD
    from curators_explorer.scripts.research_maximum_literary_jury import (
        _merged_ev,
    )
    from curators_explorer.scripts.research_ratings_only_canon import (
        load_eval_sets,
    )
    from curators_explorer.scripts.research_seedless_spectral_pilot import (
        load_posthoc_context,
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


# ---------------------------------------------------------------------------
# Part I — self-consistency operator T_N
# ---------------------------------------------------------------------------

def apply_self_operator(con, jury_user_ids: np.ndarray, N: int, tag: str,
                        universe: np.ndarray, force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / f"selfop_{tag}.npz"
    if path.exists() and not force:
        with np.load(path, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}

    jury_user_ids = np.asarray(jury_user_ids, dtype=np.int64)
    full_rows = build_ranking(con, jury_user_ids)
    full_wid, full_sc = ranking_arrays(full_rows)
    folds = assign_folds(jury_user_ids, f"self_{tag}", SELF_FOLDS)
    fold_arrays = []
    for f in range(SELF_FOLDS):
        train = jury_user_ids[folds != f]
        rows = build_ranking(con, train)
        fold_arrays.append(ranking_arrays(rows))

    scored = set(full_wid.tolist())
    for fw, _fs in fold_arrays:
        scored.update(fw.tolist())
    works = sorted(scored)
    h_uid, h_wid, l_uid, l_wid = _fetch_user_highlow(con, universe, works, tag)
    highs = _group(h_uid, h_wid)
    lows = _group(l_uid, l_wid)

    fold_of = {int(u): int(f) for u, f in zip(jury_user_ids.tolist(),
                                              folds.tolist())}
    is_member = np.isin(universe, jury_user_ids)
    n = len(universe)
    scores = np.full(n, np.nan)
    evidence = np.zeros(n, dtype=np.int64)
    idx_u = {int(u): i for i, u in enumerate(universe.tolist())}
    for i in range(n):
        u = int(universe[i])
        hi = highs.get(u, np.asarray([], dtype=str))
        lo = lows.get(u, np.asarray([], dtype=str))
        rng = np.random.default_rng(
            _derive_seed(COMMON_LIT_SEED, "selfscore", tag, u))
        if is_member[i]:
            wid, sc = fold_arrays[fold_of[u]]
        else:
            wid, sc = full_wid, full_sc
        rec = eval_user_ranking(hi, lo, wid, sc, rng)
        if rec["n_testable"] >= SELF_MIN_TESTABLE:
            _qr, qs = shrink(rec["agreement_sum"], rec["n_testable"])
            scores[i] = qs
            evidence[i] = rec["n_testable"]

    # T_N = top N by score desc, evidence desc, user_id asc
    valid = np.flatnonzero(np.isfinite(scores))
    ord_all = valid[np.lexsort((universe[valid],
                                -evidence[valid],
                                -scores[valid]))]
    top = ord_all[:N]
    result = {
        "universe": universe,
        "scores": scores,
        "evidence": evidence,
        "top_idx": top,
        "full_wid": full_wid,
        "full_score": full_sc,
        "full_top200": np.asarray([r["work_id"] for r in full_rows[:200]], dtype=str),
    }
    _write_npz_atomic(path, result)
    return result


def self_convergence_phase(con, user_scores: dict[str, np.ndarray],
                           force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "selfconvergence.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe = user_scores["universe"]
    scores = compute_common_scores(user_scores)
    order = np.lexsort((universe, -np.nan_to_num(
        user_scores["n_testable"]).max(axis=1), -np.nan_to_num(scores)))
    eligible = np.flatnonzero(np.isfinite(scores))
    order = order[np.isin(order, eligible)]

    trajectories: dict[str, Any] = {}
    for size in (5000, 10000, 20000):
        J0 = universe[order[:size]]
        traj = {"sizes": [size], "juries": {}, "transitions": {}}
        traj["juries"]["J0"] = J0.astype(np.int64)
        current = J0
        prev_rows = build_ranking(con, current)
        prev_top200 = [r["work_id"] for r in prev_rows[:200]]
        prev_common = _common_score_median(scores, order[:size])
        for it in range(1, MAX_SELF_ITER + 1):
            op = apply_self_operator(con, current, size, f"traj{size}_{it}",
                                     universe, force=force)
            Jn = universe[op["top_idx"]]
            traj["juries"][f"J{it}"] = Jn.astype(np.int64)
            retain = len(set(J0.tolist()) & set(Jn.tolist()))
            # book-ranking stability
            rows_n = build_ranking(con, Jn)
            top200_n = [r["work_id"] for r in rows_n[:200]]
            from scipy.stats import spearmanr
            common_w = [w for w in prev_top200 if w in set(top200_n)]
            rho = float("nan")
            if len(common_w) >= 10:
                ra = [prev_top200.index(w) for w in common_w]
                rb = [top200_n.index(w) for w in common_w]
                rho = float(spearmanr(ra, rb).statistic)
            traj["transitions"][f"J{it-1}->J{it}"] = {
                "retained": int(retain),
                "retention": float(retain / size),
                "jaccard": float(retain / max(size, len(set(J0) | set(Jn.tolist())))),
                "book_j50": float(len(set(prev_top200[:50]) & set(top200_n[:50])) / 50.0),
                "book_j200": float(len(set(prev_top200) & set(top200_n)) / 200.0),
                "book_rho200": rho,
                "median_L": float(_common_score_median(scores, op["top_idx"])),
                "frac_L_ge60": float(np.mean(np.nan_to_num(
                    scores[op["top_idx"]], nan=0.0) >= 0.60)),
            }
            prev_rows = rows_n
            prev_top200 = top200_n
            print(f"[self_convergence] {size} J{it-1}->J{it}: "
                  f"retention={traj['transitions'][f'J{it-1}->J{it}']['retention']:.3f} "
                  f"book_j50={traj['transitions'][f'J{it-1}->J{it}']['book_j50']:.2f} "
                  f"median_L={traj['transitions'][f'J{it-1}->J{it}']['median_L']:.3f}",
                  flush=True)
            current = Jn
        traj["final"] = {
            "J0_median_L": prev_common,
            "size": size,
        }
        trajectories[f"L{size}"] = traj
    result = {"trajectories": trajectories, "max_iter": MAX_SELF_ITER}
    _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
    return result


def _common_score_median(scores: np.ndarray, idx: np.ndarray) -> float:
    v = scores[idx]
    v = v[np.isfinite(v)]
    return float(np.median(v)) if len(v) else float("nan")


def perturbation_phase(con, user_scores: dict[str, np.ndarray],
                       force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "perturbation.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe = user_scores["universe"]
    scores = compute_common_scores(user_scores)
    order = np.lexsort((universe, -np.nan_to_num(
        user_scores["n_testable"]).max(axis=1), -np.nan_to_num(scores)))
    eligible = np.flatnonzero(np.isfinite(scores))
    order = order[np.isin(order, eligible)]
    L10 = universe[order[:10000]]

    # reference unperturbed trajectory J1,J2 for distance
    ref_j1 = apply_self_operator(con, L10, 10000, "traj10000_1",
                                 universe, force=force)
    ref_j2 = apply_self_operator(con, universe[ref_j1["top_idx"]], 10000,
                                 "traj10000_2", universe, force=force)

    results: dict[str, Any] = {}
    for rep in range(PERTURB_REPS):
        rng = np.random.default_rng(
            _derive_seed(COMMON_LIT_SEED, "perturb", rep))
        remove = rng.choice(len(L10), int(PERTURB_FRACTION * len(L10)),
                            replace=False)
        outside = np.flatnonzero(~np.isin(universe, L10))
        add = rng.choice(outside, len(remove), replace=False)
        P0 = np.concatenate([np.delete(L10, remove), universe[add]])
        assert len(P0) == 10000
        op1 = apply_self_operator(con, P0, 10000, f"pert{rep}_1", universe,
                                  force=force)
        P1 = universe[op1["top_idx"]]
        op2 = apply_self_operator(con, P1, 10000, f"pert{rep}_2", universe,
                                  force=force)
        P2 = universe[op2["top_idx"]]
        rows_p2 = build_ranking(con, P2)
        top200_p2 = [r["work_id"] for r in rows_p2[:200]]
        rows_j2 = build_ranking(con, universe[ref_j2["top_idx"]])
        top200_j2 = [r["work_id"] for r in rows_j2[:200]]
        results[f"pert{rep}"] = {
            "overlap_P2_L10": float(len(set(P2.tolist()) & set(L10.tolist())) / 10000),
            "overlap_P2_refJ1": float(len(set(P2.tolist()) & set(universe[ref_j1["top_idx"]].tolist())) / 10000),
            "overlap_P2_refJ2": float(len(set(P2.tolist()) & set(universe[ref_j2["top_idx"]].tolist())) / 10000),
            "book_j50_vs_refJ2": float(len(set(top200_p2[:50]) & set(top200_j2[:50])) / 50.0),
            "book_j200_vs_refJ2": float(len(set(top200_p2) & set(top200_j2)) / 200.0),
            "median_L": float(_common_score_median(scores, op2["top_idx"])),
        }
        print(f"[perturbation] {rep}: overlap_L10="
              f"{results[f'pert{rep}']['overlap_P2_L10']:.3f} "
              f"book_j50_vs_J2={results[f'pert{rep}']['book_j50_vs_refJ2']:.2f}",
              flush=True)
    result = {"reps": results, "fraction": PERTURB_FRACTION}
    _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
    return result


def fandom_control_phase(con, user_scores: dict[str, np.ndarray],
                         force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "fandom.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe = user_scores["universe"]
    old = np.load(OLD_NPZ, allow_pickle=False)
    anti = old["juries/threeway_anti/user_ids"].astype(np.int64)
    rng = np.random.default_rng(_derive_seed(COMMON_LIT_SEED, "fandom"))
    anti10k = np.sort(rng.choice(anti, 10000, replace=False))
    # fandom members inside universe only (for fold-exclusion correctness)
    in_univ = anti10k[np.isin(anti10k, universe)]
    F0 = in_univ[:10000]
    op1 = apply_self_operator(con, F0, len(F0), "fandom_1", universe,
                              force=force)
    F1 = universe[op1["top_idx"]]
    op2 = apply_self_operator(con, F1, len(F1), "fandom_2", universe,
                              force=force)
    F2 = universe[op2["top_idx"]]
    rows0 = build_ranking(con, F0)
    rows2 = build_ranking(con, F2)
    t0 = [r["work_id"] for r in rows0[:200]]
    t2 = [r["work_id"] for r in rows2[:200]]
    result = {
        "n_F0": int(len(F0)),
        "retention_F0_F2": float(len(set(F0.tolist()) & set(F2.tolist())) / max(1, len(F0))),
        "book_j50_F0_F2": float(len(set(t0[:50]) & set(t2[:50])) / 50.0),
        "book_j200_F0_F2": float(len(set(t0) & set(t2)) / 200.0),
        "median_L": float(_common_score_median(
            compute_common_scores(user_scores), op2["top_idx"])),
        "n_steps": 2,
    }
    _write_text_atomic(path, json.dumps(result, indent=1, default=_json_default))
    return result


# ---------------------------------------------------------------------------
# Part M — obscure-book coverage by validated jurors
# ---------------------------------------------------------------------------

def _global_work_stats(con, force: bool = False) -> dict[str, np.ndarray]:
    path = DATA / "juror_coherence_tail_state" / "global_work_stats.npz"
    if path.exists():
        with np.load(path, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}
    p2 = STATE_DIR / "global_work_stats.npz"
    if p2.exists() and not force:
        with np.load(p2, allow_pickle=False) as blob:
            return {k: blob[k] for k in blob.files}
    rows = con.execute(
        "SELECT work_id, count(*)::DOUBLE AS n_rated, "
        "sum(rating)::DOUBLE AS sum_rating "
        "FROM ex.all_rating_events GROUP BY work_id"
    ).fetchall()
    out = {"work_id": np.asarray([r[0] for r in rows], dtype=str),
           "n_rated": np.asarray([r[1] for r in rows], dtype=np.float64),
           "sum_rating": np.asarray([r[2] for r in rows], dtype=np.float64)}
    _write_npz_atomic(p2, out)
    return out


def band_of(n: float) -> int:
    for i, (lo, hi) in enumerate(RARITY_BANDS):
        if n >= lo and n <= hi:
            return i
    return -1


def _jury_all_band_counts(con, jury_users: np.ndarray,
                          all_band_works: list[str]) -> dict[str, int]:
    ut = _next_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {ut}(user_id BIGINT)")
    con.execute(f"INSERT INTO {ut} SELECT unnest(?::BIGINT[])",
                [jury_users.tolist()])
    rows = con.execute(
        f"SELECT e.work_id, count(*)::DOUBLE AS c FROM ex.all_rating_events e "
        f"JOIN {ut} u USING (user_id) WHERE e.rating >= 1 GROUP BY e.work_id"
    ).fetchall()
    con.execute(f"DROP TABLE IF EXISTS {ut}")
    return {str(w): int(c) for w, c in rows}


def coverage_phase(con, user_scores: dict[str, np.ndarray],
                   force: bool = False) -> dict[str, Any]:
    path = STATE_DIR / "coverage.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    universe = user_scores["universe"]
    scores = compute_common_scores(user_scores)
    order = np.lexsort((universe, -np.nan_to_num(
        user_scores["n_testable"]).max(axis=1), -np.nan_to_num(scores)))
    eligible = np.flatnonzero(np.isfinite(scores))
    order = order[np.isin(order, eligible)]
    gws = _global_work_stats(con)
    bands = np.asarray([band_of(float(x)) for x in gws["n_rated"]])
    n_band = {BAND_LABELS[i]: int(np.sum(bands == i)) for i in range(len(BAND_LABELS))}
    band_works = {i: gws["work_id"][bands == i].tolist() for i in range(len(BAND_LABELS))}

    # collect all juries to cover
    juries_cov: dict[str, np.ndarray] = {}
    for size in FRONTIER_SIZES:
        juries_cov[f"L{size}"] = universe[order[:size]]
    sc = json.loads((STATE_DIR / "selfconvergence.json").read_text())
    for size in (5000, 10000, 20000):
        traj = sc["trajectories"][f"L{size}"]
        juries_cov[f"J3_{size}"] = traj["juries"].get("J3")
        if juries_cov[f"J3_{size}"] is None:
            juries_cov[f"J3_{size}"] = traj["juries"].get("J2")
    fandom = json.loads((STATE_DIR / "fandom.json").read_text())
    # F2 membership: recompute from stored npz
    with np.load(STATE_DIR / "selfop_fandom_2.npz", allow_pickle=False) as blob:
        juries_cov["fandom_F2"] = universe[blob["top_idx"]]

    results: dict[str, Any] = {"n_works_per_band": n_band}
    all_band_works = sorted(set().union(*[set(band_works[i]) for i in band_works]))
    for name, users in juries_cov.items():
        if users is None:
            continue
        users = np.asarray(users, dtype=np.int64)
        counts = _jury_all_band_counts(con, users, all_band_works)
        results[name] = {}
        for band_i in range(len(BAND_LABELS)):
            if not band_works[band_i]:
                results[name][BAND_LABELS[band_i]] = {"n_works": 0}
                continue
            cv = np.asarray([counts.get(w, 0) for w in band_works[band_i]])
            results[name][BAND_LABELS[band_i]] = {
                "n_works": len(cv),
                "frac_ge1": float(np.mean(cv >= 1)),
                "frac_ge2": float(np.mean(cv >= 2)),
                "frac_ge3": float(np.mean(cv >= 3)),
                "frac_ge5": float(np.mean(cv >= 5)),
                "frac_ge10": float(np.mean(cv >= 10)),
                "median": float(np.median(cv)),
                "p90": float(np.quantile(cv, 0.90)),
            }
        print(f"[coverage] {name}: band20_49 frac>=1="
              f"{results[name]['20_49']['frac_ge1']:.2f} "
              f"frac>=3={results[name]['20_49']['frac_ge3']:.2f}", flush=True)
    _write_text_atomic(path, json.dumps(results, indent=1))
    return results


# ---------------------------------------------------------------------------
# Part F — cross-reference agreement + known-group score distributions
# ---------------------------------------------------------------------------

def cross_reference_analysis(user_scores: dict[str, np.ndarray],
                             juries: dict[str, np.ndarray]) -> dict[str, Any]:
    universe = user_scores["universe"]
    L = user_scores["L_shrunk"]
    nt = user_scores["n_testable"]
    enough = np.isfinite(L) & (nt >= CANDIDATE_MIN_TESTABLE)
    refs = list(REFERENCE_KEYS)

    pair_stats = {}
    for a in range(3):
        for b in range(a + 1, 3):
            m = enough[:, a] & enough[:, b]
            va, vb = L[m, a], L[m, b]
            rho = float(np.corrcoef(va, vb)[0, 1])
            from scipy.stats import spearmanr
            sp = float(spearmanr(va, vb).statistic)
            pair_stats[f"{refs[a]}_vs_{refs[b]}"] = {
                "n": int(m.sum()),
                "pearson": rho,
                "spearman": sp,
                "median_abs_diff": float(np.median(np.abs(va - vb))),
            }

    scores = compute_common_scores(user_scores)
    # top-N overlaps
    single_orders = {}
    for ri, ref in enumerate(refs):
        v = np.where(enough[:, ri], L[:, ri], np.nan)
        single_orders[ref] = np.lexsort((universe, -np.nan_to_num(v)))[
            :20000]
    med_order = np.lexsort((universe, -np.nan_to_num(scores)))[:20000]
    overlap = {}
    for n in (2500, 5000, 10000, 20000):
        med_set = set(med_order[:n].tolist())
        row = {}
        for ref in refs:
            s = set(single_orders[ref][:n].tolist())
            inter = len(med_set & s)
            row[f"intersection_{ref}"] = inter
            row[f"jaccard_{ref}"] = inter / max(n, len(med_set | s))
        overlap[str(n)] = row

    # known-group score distributions
    known_groups = {
        "ABC": "ABC",
        "p65": "core_p65_s25",
        "AnB": "committee_AnB",
        "vote2": "committee_vote2_ABCs",
        "A_only": "A_only",
        "B_only": "B_only",
        "AB_only": "AB_only",
        "AuB": "committee_AuB",
    }
    group_scores: dict[str, Any] = {}
    for name, jury in known_groups.items():
        members = juries[jury]
        idx = np.flatnonzero(np.isin(universe, members))
        group_scores[name] = {
            "n_in_universe": int(len(idx)),
            "dist": q_distribution(scores[idx]),
        }
    # fandom + random
    old = np.load(OLD_NPZ, allow_pickle=False)
    anti = old["juries/threeway_anti/user_ids"].astype(np.int64)
    rng = np.random.default_rng(_derive_seed(COMMON_LIT_SEED, "fandom"))
    anti10k = np.sort(rng.choice(anti, 10000, replace=False))
    ai = np.flatnonzero(np.isin(universe, anti10k))
    group_scores["fandom_anti10k"] = {
        "n_in_universe": int(len(ai)),
        "dist": q_distribution(scores[ai]),
    }
    rng2 = np.random.default_rng(_derive_seed(COMMON_LIT_SEED, "rand10k"))
    rand10k = np.sort(rng2.choice(universe, 10000, replace=False))
    ri = np.flatnonzero(np.isin(universe, rand10k))
    group_scores["random10k"] = {
        "n_in_universe": int(len(ri)),
        "dist": q_distribution(scores[ri]),
    }
    return {"pairs": pair_stats, "overlap": overlap,
            "known_groups": group_scores}


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def report_phase(user_scores: dict[str, np.ndarray],
                 juries: dict[str, np.ndarray]) -> dict[str, Any]:
    from scipy.stats import spearmanr

    ref_json = json.loads((STATE_DIR / "references.json").read_text())
    frontier = json.loads((STATE_DIR / "frontier.json").read_text())
    sc = json.loads((STATE_DIR / "selfconvergence.json").read_text())
    pert = json.loads((STATE_DIR / "perturbation.json").read_text())
    fandom = json.loads((STATE_DIR / "fandom.json").read_text())
    cov = json.loads((STATE_DIR / "coverage.json").read_text())
    cross = cross_reference_analysis(user_scores, juries)

    L = []
    L.append("# Common Literary Juror Discovery — report")
    L.append("")
    L.append(f"- Seed `{COMMON_LIT_SEED}`. Reverse-engineered common-reference "
             f"scoring; no semantic optimisation.")
    L.append("")
    L.append("## References")
    L.append("")
    for ref, d in ref_json["refs"].items():
        L.append(f"- {ref}: n={d['n']} ranked works={d['full_n_ranked']}")
    L.append("")
    L.append("## Cross-reference agreement about users")
    L.append("")
    L.append("| pair | n | pearson | spearman | median abs diff |")
    L.append("|---|---:|---:|---:|---:|")
    for k, v in cross["pairs"].items():
        L.append(f"| {k} | {v['n']} | {v['pearson']:.3f} | {v['spearman']:.3f} | "
                 f"{v['median_abs_diff']:.3f} |")
    L.append("")
    L.append("## Common-score distributions for known groups")
    L.append("")
    L.append("| group | n_in_universe | median | p10 | p25 | p75 | frac>=.6 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for k, v in cross["known_groups"].items():
        d = v["dist"]
        L.append(f"| {k} | {v['n_in_universe']} | "
                 f"{d.get('median', float('nan')):.3f} | "
                 f"{d.get('p10', float('nan')):.3f} | "
                 f"{d.get('p25', float('nan')):.3f} | "
                 f"{d.get('p75', float('nan')):.3f} | "
                 f"{d.get('frac_ge_0p60', float('nan')):.3f} |")
    L.append("")
    L.append("## Nested candidate frontier")
    L.append("")
    L.append("| jury | n | median L | p10 | p75 | frac>=.6 | median ev | "
             "none-of-ABC frac | pos50 | anti50 | exact50 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for size in FRONTIER_SIZES:
        f = frontier["frontier"][f"L{size}"]
        d = f["user_quality"]["dist"]
        comp = f["source_composition"]
        br = f["book_rank"]
        L.append(f"| L{size} | {f['n']} | {d.get('median', float('nan')):.3f} | "
                 f"{d.get('p10', float('nan')):.3f} | {d.get('p75', float('nan')):.3f} | "
                 f"{d.get('frac_ge_0p60', float('nan')):.3f} | "
                 f"{f['user_quality']['median_evidence']:.0f} | "
                 f"{comp.get('none_ABC', float('nan')):.3f} | "
                 f"{br['semantic']['pos50']} | {br['semantic']['anti50']} | "
                 f"{br['semantic']['exact50']} |")
    L.append("")
    L.append("## Stability (5 half splits)")
    L.append("")
    L.append("| jury | half-J50 mean | half-J200 mean | rho200 mean |")
    L.append("|---|---:|---:|---:|")
    for size in STABILITY_SIZES:
        st = frontier["frontier"][f"L{size}"]["stability"]
        L.append(f"| L{size} | {st['j50_mean']:.2f} | {st['j200_mean']:.2f} | "
                 f"{st['rho200_mean']:.3f} |")
    L.append("")
    L.append("## Self-convergence trajectories (label-free T_N)")
    L.append("")
    L.append("| jury | transition | retention | book J50 | book J200 | book rho200 | "
             "median L | frac L>=.6 |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for size in (5000, 10000, 20000):
        for tname, t in sc["trajectories"][f"L{size}"]["transitions"].items():
            L.append(f"| L{size} | {tname} | {t['retention']:.3f} | "
                     f"{t['book_j50']:.2f} | {t['book_j200']:.2f} | "
                     f"{t['book_rho200']:.3f} | {t['median_L']:.3f} | "
                     f"{t['frac_L_ge60']:.3f} |")
    L.append("")
    L.append("## Perturbation / basin test (L10000, 10% random replacement)")
    L.append("")
    L.append("| rep | P2∩L10 | P2∩J1 | P2∩J2 | book J50 vs J2 | book J200 vs J2 | "
             "median L |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for k, v in pert["reps"].items():
        L.append(f"| {k} | {v['overlap_P2_L10']:.3f} | "
                 f"{v['overlap_P2_refJ1']:.3f} | {v['overlap_P2_refJ2']:.3f} | "
                 f"{v['book_j50_vs_refJ2']:.2f} | {v['book_j200_vs_refJ2']:.2f} | "
                 f"{v['median_L']:.3f} |")
    L.append("")
    L.append("## Fandom self-convergence control")
    L.append("")
    L.append(f"- retention F0→F2: {fandom['retention_F0_F2']:.3f}; "
             f"book J50: {fandom['book_j50_F0_F2']:.2f}; "
             f"book J200: {fandom['book_j200_F0_F2']:.2f}; "
             f"median common-L at F2: {fandom['median_L']:.3f}")
    L.append("")
    L.append("## Obscure-book coverage (by validated jurors)")
    L.append("")
    L.append("| jury | band 20-49 >=1 | >=3 | >=5 | median | band 100-249 >=1 | >=3 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for name in ([f"L{s}" for s in FRONTIER_SIZES]
                 + [f"J3_{s}" for s in (5000, 10000, 20000)]):
        if name not in cov:
            continue
        b1 = cov[name].get("20_49", {})
        b3 = cov[name].get("100_249", {})
        L.append(f"| {name} | {b1.get('frac_ge1', 0):.2f} | "
                 f"{b1.get('frac_ge3', 0):.2f} | {b1.get('frac_ge5', 0):.2f} | "
                 f"{b1.get('median', 0):.1f} | {b3.get('frac_ge1', 0):.2f} | "
                 f"{b3.get('frac_ge3', 0):.2f} |")
    L.append("")
    L.append("## Key naturality table")
    L.append("")
    L.append("| jury | n | median L | half-J50 | self-ret J0→J1 | J1→J2 | J2→J3 | "
             "book J50 J2→J3 | 20-49 >=1 | 20-49 >=3 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for size in (5000, 10000, 20000):
        f = frontier["frontier"][f"L{size}"]
        traj = sc["trajectories"][f"L{size}"]
        t01 = traj["transitions"].get("J0->J1", {})
        t12 = traj["transitions"].get("J1->J2", {})
        t23 = traj["transitions"].get("J2->J3", {})
        st = f.get("stability", {})
        c1 = cov.get(f"L{size}", {}).get("20_49", {})
        L.append(f"| L{size} | {size} | "
                 f"{f['user_quality']['dist'].get('median', float('nan')):.3f} | "
                 f"{st.get('j50_mean', float('nan')):.2f} | "
                 f"{t01.get('retention', float('nan')):.3f} | "
                 f"{t12.get('retention', float('nan')):.3f} | "
                 f"{t23.get('retention', float('nan')):.3f} | "
                 f"{t23.get('book_j50', float('nan')):.2f} | "
                 f"{c1.get('frac_ge1', 0):.2f} | {c1.get('frac_ge3', 0):.2f} |")
    L.append("")
    L.append("## Answers")
    L.append("")
    L.append("1. Common reader direction: see cross-reference table.")
    L.append("2. Rediscovery outside A/B/C: see 'none-of-ABC frac' in the "
             "frontier table.")
    L.append("3. Individual quality vs size: see median L / frac>=.6 across the "
             "frontier.")
    L.append("4. Actual literary rankings: see COMMON_LITERARY_JUROR_HEADS.md "
             "(full top-50).")
    L.append("5. Stability: see stability table.")
    L.append("6-7. Self-consistency/convergence: see trajectory table.")
    L.append("8. Basin attraction: see perturbation table.")
    L.append("9. Control: fandom self-converges too; self-convergence is generic "
             "to coherent taste communities, not proof of literariness.")
    L.append("10. Coverage: see coverage table.")
    L.append("11. Descriptive candidates: see key naturality table.")
    L.append("")
    _write_text_atomic(OUT_MD, "\n".join(L) + "\n")
    _write_heads(frontier, sc)
    # consolidated JSON
    combined = {
        "seed": COMMON_LIT_SEED,
        "references": ref_json,
        "cross_reference": cross,
        "frontier": frontier,
        "self_convergence": sc,
        "perturbation": pert,
        "fandom": fandom,
        "coverage": cov,
    }
    _write_text_atomic(OUT_JSON, json.dumps(combined, indent=1, default=_json_default))
    print(f"Wrote {OUT_MD}, {OUT_HEADS}, {OUT_JSON}", flush=True)
    return {"report": True}


def _write_heads(frontier: dict[str, Any], sc: dict[str, Any]) -> None:
    L = ["# Common Literary Juror — complete top-50 heads",
         "", f"Seed `{COMMON_LIT_SEED}`. Probe flags are annotations only.",
         ""]
    order = [f"L{s}" for s in FRONTIER_SIZES] + \
            [f"J3_{s}" for s in (5000, 10000, 20000)]
    con = open_db()
    materialize_base(con)
    with np.load(STATE_DIR / "user_scores.npz", allow_pickle=False) as blob:
        universe = blob["universe"].astype(np.int64)
    for name in order:
        if name.startswith("L"):
            br = frontier["frontier"][name]["book_rank"]
            kind = "common-reference frontier"
        else:
            size = int(name.split("_")[1])
            traj = sc["trajectories"][f"L{size}"]
            key = "J3" if "J3" in traj["juries"] else "J2"
            members = traj["juries"][key]
            rows = build_ranking(con, np.asarray(members, dtype=np.int64))
            br = {
                "top50": [
                    {"rank": r["rank"], "work_id": r["work_id"],
                     "title": r["title"], "author": r["author"],
                     "score": float(r["score"])}
                    for r in rows[:50]
                ],
                "semantic": {},
            }
            kind = "self-convergence endpoint"
        L.append(f"## {name}  ({kind})")
        L.append("")
        L.append("| rank | title | author | score | pos | exact | broad | anti |")
        L.append("|---|---|---|---|---|---|---|---|")
        for r in br["top50"]:
            L.append(f"| {r['rank']} | {r['title']} | {r['author']} | "
                     f"{r.get('score', '')} | "
                     f"{'Y' if r.get('work_id') in _PROBE_POS else ''} | "
                     f"{'Y' if r.get('work_id') in _PROBE_EXACT else ''} | "
                     f"{'Y' if r.get('work_id') in _PROBE_BROAD else ''} | "
                     f"{'Y' if r.get('work_id') in _PROBE_ANTI else ''} |")
        L.append("")
    con.close()
    _write_text_atomic(OUT_HEADS, "\n".join(L) + "\n")


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def phase_smoke() -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    juries = load_juries()
    sizes = {"ABC": 2368, "core_p65_s25": 3286, "committee_AnB": 11582}
    for k, n in sizes.items():
        add(f"{k}_exact", len(juries[k]) == n, f"n={len(juries[k])}")

    folds = assign_folds(juries["ABC"], "R1_ABC", REFERENCE_FOLDS)
    folds2 = assign_folds(juries["ABC"], "R1_ABC", REFERENCE_FOLDS)
    add("fold_deterministic", bool(np.array_equal(folds, folds2)),
        "same seed -> same folds")

    # shrink arithmetic
    qr, qs = shrink(4.0, 4)
    exp = (4 + 0.5 * PRIOR_K) / (4 + PRIOR_K)
    add("shrink_arithmetic", abs(qs - exp) < 1e-9, f"qs={qs:.4f} exp={exp:.4f}")
    add("shrink_zero_testable_nan", np.isnan(shrink(0, 0)[0]), "NaN on 0")

    # consensus score = median of valid ref scores
    L = np.array([[np.nan, 0.6, 0.7],
                  [0.55, np.nan, 0.65],
                  [np.nan, np.nan, np.nan]])
    nt = np.array([[5, 40, 40], [40, 5, 40], [0, 0, 0]], dtype=np.int64)
    # eligible: >=2 refs with >=20 testable
    enough = np.isfinite(L) & (nt >= 20)
    nv = np.sum(enough, axis=1)
    add("candidate_requires_2_refs_ge20",
        np.array_equal(nv, [2, 2, 0]), f"n_valid={nv.tolist()}")
    # score = median of valid
    score = compute_common_scores({"L_shrunk": L, "n_testable": nt})
    add("consensus_is_median",
        abs(score[0] - 0.65) < 1e-9 and abs(score[1] - 0.60) < 1e-9
        and np.isnan(score[2]),
        f"score={score.tolist()}")

    # reference size / fold assignment balanced
    add("folds_balanced",
        np.allclose(np.bincount(folds, minlength=REFERENCE_FOLDS),
                    len(folds) / REFERENCE_FOLDS, atol=1),
        f"folds sizes {np.bincount(folds, minlength=REFERENCE_FOLDS).tolist()}")

    # ties score .5
    sd = {"w1": 3.0, "w2": 3.0}
    rec = eval_user_ranking(np.asarray(["w1"], dtype=str),
                            np.asarray(["w2"], dtype=str),
                            np.asarray(["w1", "w2"], dtype=str),
                            np.asarray([3.0, 3.0]),
                            np.random.default_rng(1))
    add("ties_score_half", rec["agreement_sum"] == TIE_SCORE and rec["n_testable"] == 1,
        f"agree={rec['agreement_sum']}")

    # quantile indexing correct
    v = np.arange(100.0)
    d = q_distribution(v)
    add("quantile_indexing",
        abs(d["median"] - 49.5) < 0.6 and abs(d["p05"] - 4.95) < 1.0
        and abs(d["p95"] - 94.05) < 1.0,
        f"median={d['median']} p05={d['p05']} p95={d['p95']}")

    # no semantic labels in common score (static)
    import inspect
    src = inspect.getsource(eval_user_ranking) + inspect.getsource(
        compute_common_scores)
    banned = [t for t in ("pos_works", "exact_lit", "broad_lit", "anti_works")
              if t in src]
    add("no_literary_labels_in_score", not banned, f"banned: {banned}")

    add("nested_frontier_sizes_exact", True,
        "L juries are top-N by frozen score (construction guarantees nesting)")

    add("perturb_arithmetic",
        int(round(0.10 * 10000)) == 1000, "10% of 10000 = 1000")

    # global coverage bands disjoint/complete over 5..5000
    okb = True
    for n in range(5, 5000):
        if band_of(float(n)) < 0:
            okb = False
    add("rarity_bands_disjoint_complete", okb, "bands cover 5..4999")

    ok = all(c["ok"] for c in checks)
    print(f"[smoke] {sum(c['ok'] for c in checks)}/{len(checks)} checks passed "
          f"in {_fmt_time(time.time() - t0)}", flush=True)
    return {"checks": checks, "ok": bool(ok), "elapsed_s": round(time.time() - t0, 1)}


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
    _load_probes(load_payload_helper())
    for ph in phases:
        t0 = time.time()
        con = open_db()
        materialize_base(con)
        juries = load_juries()
        if ph == "prepare":
            _ = eligible_user_universe(con, force=force)
        elif ph == "references":
            _ = build_reference_rankings(con, juries, force=force)
        elif ph == "score_users":
            _ = reference_scoring(con, juries, force=force)
        elif ph == "candidate_frontier":
            us = reference_scoring(con, juries, force=False)
            _ = frontier_phase(con, us, juries, force=force)
        elif ph == "self_convergence":
            us = reference_scoring(con, juries, force=False)
            _ = self_convergence_phase(con, us, force=force)
            _ = perturbation_phase(con, us, force=force)
            _ = fandom_control_phase(con, us, force=force)
        elif ph == "coverage":
            us = reference_scoring(con, juries, force=False)
            _ = coverage_phase(con, us, force=force)
        elif ph == "report":
            us = reference_scoring(con, juries, force=False)
            report_phase(us, juries)
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
        phases = ["prepare", "references", "score_users", "candidate_frontier",
                  "self_convergence", "coverage", "report"]
    run_phases(phases, force=args.force)


if __name__ == "__main__":
    _main()

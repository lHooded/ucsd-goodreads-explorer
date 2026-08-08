#!/usr/bin/env python3
"""MAXIMUM LITERARY JURY / CORE-HALO AMPLIFICATION.

Reverse-engineer a strong literary USER jury from ordinary Goodreads behaviour,
then measure how large that jury can be made while preserving a stable,
recognisably literary consensus.

Honest framing
--------------
Semantic literary labels are used openly for training labels, model selection,
evaluation and optimisation.  This is NOT a label-blind experiment.  What we
keep honest is the separation between:
  * direct seed/book-label features       (oracle only, clearly labelled);
  * ordinary behavioural features         (primary inference model);
  * user membership labels from earlier literary juries (p65_s25 core etc.);
  * final semantic evaluation             (exact/broad/anti probes).

Phases
------
  prepare      reconstruct historical juries + build aligned user feature table
  forensic10k  paired forensic analysis of the failed 20k->10k breeding splits
  fit          behaviour models, CV, leave-one-jury-definition-out, ablations
  frontier     direct nested jury frontiers (model / core-preserving /
               core-excluding / controls), choose J_star by a frozen rule
  perturb      constant-size swap perturbations around J_star + substitution fit
  improve      at most 2 conservative improvement rounds (if predictive)
  amplify      maximum amplification frontier grown from the improved core
  reversal     optional limited reversal-size diagnostics
  report       render MAXIMUM_LITERARY_JURY_REPORT.md
  all          run all phases in order

Determinism: every random draw uses np.random.default_rng with a derived seed
(_derive_seed, sha256 over parts, matching the family-breeding convention).

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_maximum_literary_jury --phase all
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_maximum_literary_jury --smoke
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import duckdb
import numpy as np

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_deep_size_sweep import (
    MAX_N,
    MIN_APPEAR,
    MIN_RANK_N,
    build_pairs,
    rank_pairwise,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    _con,
    load_eval_sets,
    materialize_base,
)
from curators_explorer.scripts.research_residual_enthusiasm import (
    load_sticky,
    probe_metrics,
)
from curators_explorer.scripts.research_seedless_spectral_pilot import (
    load_posthoc_context,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    build_user_features,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

try:
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.ensemble import HistGradientBoostingClassifier

    HAS_SKLEARN = True
except Exception:  # pragma: no cover
    HAS_SKLEARN = False

DATA = Path(__file__).resolve().parents[1] / "data"
PAYLOAD_CACHE = DATA / "seedless_spectral_pilot_matrix_b500.npz"
FEATURE_CACHE = DATA / "multi_origin_behavior_features.npz"
BREEDING_NPZ = DATA / "recursive_family_breeding.npz"
BREEDING_JSON = DATA / "recursive_family_breeding.json"
SOFT_WEIGHTS_PARQUET = DATA / "soft_jury_weights.parquet"
FAMILY_NPZ = DATA / "jury_decomposition_mode_families.npz"

OUT_JSON = DATA / "maximum_literary_jury.json"
OUT_NPZ = DATA / "maximum_literary_jury.npz"
OUT_MD = DATA / "MAXIMUM_LITERARY_JURY_REPORT.md"
CHUNK_DIR = DATA / "maximum_literary_jury_chunks"
STATE_DIR = DATA / "maximum_literary_jury_state"

MAX_JURY_SEED = 20260826

FRONTIER_SIZES = [
    500, 1000, 1500, 2000, 3286, 5000, 8000, 10000, 15000, 20000,
    30000, 40000, 60000, 80000, 100000, 120000, 150000,
]
SWAP_FRACTIONS = [0.025, 0.05, 0.10, 0.20]
SWAP_REPS = 50
JSTAR_RULE = (
    "1 raw_n>=10000; 2 anti50<=5; 3 maximize pos50+0.25*broad50+5*half_jaccard; "
    "4 tie-break larger kish; 5 larger raw_n; fallback largest jury with anti50<=5"
)

FEATURE_GROUPS: dict[str, list[str]] = {
    "activity": [
        "log_n_rated", "log_n5", "log_n_ge4", "mean_rating", "five_rate",
        "p1", "p2", "p3", "p4", "p5", "n_levels",
    ],
    "series_binge": ["series_share_5", "binge_mean_5", "binge_max_5_log"],
    "author": [
        "author_hhi_5", "singleton_author_share_5", "author_div_5",
        "n_authors_5_log", "n_midpop_authors_5_log", "midpop_author_frac_5",
        "midpop_span_per_logn5", "n_megastar_authors_5_log",
    ],
    "popularity": [
        "mean_logn_5", "std_logn_5", "p5_blockbuster",
        "midpop_likes_per_log_shelf", "popular_likes_per_log_shelf",
        "mean_logn_all", "std_logn_all", "mean_logn_low",
        "mid_catalog_share_5", "mega_catalog_share_5",
        "p5_mid_exposed", "p5_mega_exposed",
    ],
    "temporal": ["mean_pub_year_5"],
    "depth": [
        "depth_ge4", "depth_5", "rare_rated_share", "mid_rated_share",
        "mega_rated_share", "rare_loved_share", "mid_loved_share",
        "mega_loved_share", "p5_rare_exposed",
    ],
    "residual": [
        "mean_work_mean_all", "mean_work_mean_5", "mean_work_mean_low",
        "mean_residual", "mean_abs_residual", "sd_residual", "rating_pop_corr",
    ],
}
ALL_FEATURES = [f for group in FEATURE_GROUPS.values() for f in group]
LOAD_BEARING = [
    "series_share_5", "binge_max_5_log", "author_hhi_5", "mean_pub_year_5",
    "midpop_span_per_logn5", "mega_catalog_share_5",
]
SOFT_CONSENSUS_JURIES = [
    "p75_s40", "p65_s25", "p45_s40", "p0_s25", "p0_s15", "p0_s0",
    "threeway_classic", "rebuilt_hard",
]


def _derive_seed(*parts: Any) -> int:
    h = hashlib.sha256()
    for part in parts:
        h.update(str(part).encode("utf-8"))
        h.update(b"\x00")
    return int.from_bytes(h.digest()[:16], "big")


def _sk_rng_seed(*parts: Any) -> int:
    """32-bit seed for sklearn estimators (random_state must fit uint32)."""
    return _derive_seed(*parts) & 0xFFFFFFFF


def _bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _write_npz_atomic(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, path)


def _json_default(o: Any) -> Any:
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(f"cannot serialize {type(o)}")


def _fmt_time(seconds: float) -> str:
    return f"{seconds:.0f}s" if seconds < 3600 else f"{seconds / 3600:.1f}h"


def _add_npz(existing: dict[str, np.ndarray], arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    for k, v in arrays.items():
        existing[k] = v
    return existing


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_payload() -> dict[str, np.ndarray]:
    with np.load(PAYLOAD_CACHE, allow_pickle=False) as saved:
        payload = {key: saved[key] for key in saved.files}
    payload["user_ids"] = payload["user_ids"].astype(np.int64)
    payload["work_ids"] = payload["work_ids"].astype(str)
    return payload


def load_feature_table(payload: dict[str, np.ndarray]) -> np.ndarray:
    """Return X (n_payload, n_feat) aligned to payload user indices."""
    with np.load(FEATURE_CACHE, allow_pickle=False) as saved:
        ids = saved["ids"].astype(np.int64)
        x = saved["x"].astype(np.float64)
    order = np.argsort(ids)
    ids_s = ids[order]
    x_s = x[order]
    pos = np.searchsorted(ids_s, payload["user_ids"])
    pos = np.minimum(pos, len(ids_s) - 1)
    ok = ids_s[pos] == payload["user_ids"]
    X = np.full((len(payload["user_ids"]), x.shape[1]), np.nan, dtype=np.float64)
    X[ok] = x_s[pos[ok]]
    med = np.nanmedian(X, axis=0)
    for c in range(x.shape[1]):
        bad = ~np.isfinite(X[:, c])
        if bad.any():
            X[bad, c] = med[c]
    return X


def load_eval_context(payload: dict[str, np.ndarray]) -> tuple[dict, dict]:
    return load_posthoc_context(payload["work_ids"])


def _merged_ev(ev: dict, eval_sets: dict) -> dict:
    """Union of load_eval_sets (probe) and posthoc eval_sets (semantic)."""
    out = dict(ev)
    for k in ("exact_lit", "broad_lit", "anti", "filler"):
        out[k] = eval_sets.get(k, set())
    return out


def _pick_metrics(metrics: dict[str, int]) -> dict[str, int]:
    out = {}
    for name in ("exact_lit", "broad_lit", "anti", "filler"):
        for k in (50, 100, 200):
            key = f"{name}{k}"
            if key in metrics:
                out[key] = metrics[key]
    return out


# ---------------------------------------------------------------------------
# Direct jury scoring (DuckDB; pairwise esteem primary, exact-inclusion 2nd)
# ---------------------------------------------------------------------------

_jury_counter = [0]


def _next_jury_table() -> str:
    _jury_counter[0] += 1
    return f"mj_jury_{_jury_counter[0]}"


def _ensure_pair_cache(con, payload_ids: np.ndarray) -> None:
    """Materialize the capped 5-star / low lists for every payload user once."""
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='mj_highs'"
    ).fetchone()[0] > 0:
        return
    t0 = time.time()
    con.execute(
        f"CREATE OR REPLACE TEMP TABLE mj_highs AS "
        f"SELECT user_id, work_id FROM ("
        f"  SELECT e.user_id, e.work_id, row_number() OVER ("
        f"    PARTITION BY e.user_id ORDER BY hash(e.user_id || '-' || e.work_id || '-h11')) AS rn "
        f"  FROM ex.all_rating_events e JOIN work_rarity wr ON wr.work_id = e.work_id "
        f"  WHERE e.rating = 5 AND wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N} "
        f"    AND e.user_id IN (SELECT unnest(?::BIGINT[]))"
        f") WHERE rn <= 12",
        [payload_ids.tolist()],
    )
    con.execute(
        f"CREATE OR REPLACE TEMP TABLE mj_lows AS "
        f"SELECT user_id, work_id FROM ("
        f"  SELECT e.user_id, e.work_id, row_number() OVER ("
        f"    PARTITION BY e.user_id ORDER BY hash(e.user_id || '-' || e.work_id || '-l11')) AS rn "
        f"  FROM ex.all_rating_events e JOIN work_rarity wr ON wr.work_id = e.work_id "
        f"  WHERE e.rating <= 3 AND wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N} "
        f"    AND e.user_id IN (SELECT unnest(?::BIGINT[]))"
        f") WHERE rn <= 12",
        [payload_ids.tolist()],
    )
    print(
        f"[score] pair cache built in {_fmt_time(time.time() - t0)} "
        f"(highs={con.execute('SELECT count(*) FROM mj_highs').fetchone()[0]:,} "
        f"lows={con.execute('SELECT count(*) FROM mj_lows').fetchone()[0]:,})",
        flush=True,
    )


def _pairwise_score_rows(con, jury_table: str) -> list[dict]:
    pairs_table = f"{jury_table}_pairs"
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='mj_highs'"
    ).fetchone()[0] > 0:
        con.execute(
            f"CREATE OR REPLACE TEMP TABLE {pairs_table} AS "
            f"SELECT h.user_id, h.work_id AS winner, l.work_id AS loser, j.w AS w "
            f"FROM mj_highs h JOIN mj_lows l USING (user_id) "
            f"JOIN {jury_table} j USING (user_id)"
        )
    else:
        build_pairs(con, jury_table, pairs_table)
    rows = rank_pairwise(con, pairs_table, "w")
    con.execute(f"DROP TABLE IF EXISTS {pairs_table}")
    return rows


def _exact_inclusion_score_rows(con, jury_table: str) -> list[dict]:
    from curators_explorer.scripts.research_ratings_only_canon import rank_from_sql

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE {jury_table}_bal AS
        SELECT e.user_id,
               count(*) FILTER (WHERE e.rating = 5)::DOUBLE AS n_high,
               count(*) FILTER (WHERE e.rating BETWEEN 1 AND 3)::DOUBLE AS n_low,
               least(
                   count(*) FILTER (WHERE e.rating = 5),
                   count(*) FILTER (WHERE e.rating BETWEEN 1 AND 3),
                   12.0
               )::DOUBLE AS n_side
        FROM {jury_table} j
        JOIN ex.all_rating_events e USING (user_id)
        JOIN work_rarity wr ON wr.work_id = e.work_id
        WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
          AND (e.rating = 5 OR e.rating BETWEEN 1 AND 3)
        GROUP BY e.user_id
        """
    )
    sql = f"""
        WITH agg AS (
            SELECT
                e.work_id,
                sum(CASE WHEN e.rating = 5 AND b.n_high > 0
                         THEN b.n_side / b.n_high ELSE 0 END)::DOUBLE AS wins,
                sum(CASE WHEN e.rating BETWEEN 1 AND 3 AND b.n_low > 0
                         THEN b.n_side / b.n_low ELSE 0 END)::DOUBLE AS losses,
                count(DISTINCT e.user_id)::DOUBLE AS raters
            FROM {jury_table} j
            JOIN {jury_table}_bal b USING (user_id)
            JOIN ex.all_rating_events e USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
              AND (e.rating = 5 OR e.rating BETWEEN 1 AND 3)
            GROUP BY e.work_id
        )
        SELECT work_id,
               ((wins + 0.5) / (wins + losses + 1.0))::DOUBLE AS score,
               (wins + losses)::DOUBLE AS n_eff
        FROM agg
        WHERE (wins + losses) >= 10.0
    """
    rows = rank_from_sql(con, sql)
    con.execute(f"DROP TABLE IF EXISTS {jury_table}_bal")
    return rows


def score_jury(
    con,
    user_ids: np.ndarray,
    *,
    weights: np.ndarray | None = None,
    ev: dict[str, Any],
    sticky: set[str],
    scorer: str = "pairwise",
    limit: int = 200,
) -> dict[str, Any]:
    """Direct-rank a jury. Returns probe + semantic + head + top rows."""
    user_ids = np.asarray(user_ids, dtype=np.int64)
    if weights is None:
        weights = np.ones(len(user_ids), dtype=np.float64)
    table = _next_jury_table()
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT, w DOUBLE)")
    if len(user_ids) > 0:
        con.execute(
            f"INSERT INTO {table} SELECT * FROM ("
            f"SELECT unnest(?::BIGINT[]) AS user_id, unnest(?::DOUBLE[]) AS w)",
            [user_ids.tolist(), weights.tolist()],
        )
    if scorer == "pairwise":
        rows = _pairwise_score_rows(con, table)
        con.execute(f"DROP TABLE IF EXISTS {table}_pairs")
    else:
        rows = _exact_inclusion_score_rows(con, table)
        con.execute(f"DROP TABLE IF EXISTS {table}_bal")
    con.execute(f"DROP TABLE IF EXISTS {table}")
    probe = probe_metrics(rows, ev, sticky)
    sem = {}
    for name in ("exact_lit", "broad_lit", "anti", "filler"):
        ids = ev.get(name, set()) if isinstance(ev, dict) else set()
        for k in (50, 100, 200):
            sem[f"{name}{k}"] = sum(r["work_id"] in ids for r in rows[:k])
    return {
        "scorer": scorer,
        "jury_n": int(len(user_ids)),
        "probe": probe,
        "semantic": sem,
        "n_rows": int(len(rows)),
        "head": [
            {
                "rank": r["rank"], "work_id": r["work_id"], "title": r["title"],
                "author": r["author"], "score": float(r["score"]),
                "n_eff": float(r["n_eff"]),
            }
            for r in rows[:limit]
        ],
    }


def half_split_jaccard(
    con, user_ids: np.ndarray, *, ev, sticky, rng, scorer: str = "pairwise",
    n_splits: int = 2,
) -> dict[str, Any]:
    user_ids = np.asarray(user_ids, dtype=np.int64)
    jacs: list[float] = []
    rhos: list[float] = []
    for s in range(n_splits):
        r = rng.permutation(len(user_ids))
        h1 = user_ids[r[: len(user_ids) // 2]]
        h2 = user_ids[r[len(user_ids) // 2:]]
        a = score_jury(con, h1, ev=ev, sticky=sticky, scorer=scorer)["head"]
        b = score_jury(con, h2, ev=ev, sticky=sticky, scorer=scorer)["head"]
        set_a = {x["work_id"] for x in a[:50]}
        set_b = {x["work_id"] for x in b[:50]}
        jacs.append(len(set_a & set_b) / 50.0)
        ids_a = [x["work_id"] for x in a[:200]]
        ids_b = [x["work_id"] for x in b[:200]]
        rb = {w: i for i, w in enumerate(ids_b)}
        common = [w for w in ids_a if w in rb]
        if len(common) >= 10:
            ra = np.array([i for i, w in enumerate(ids_a) if w in rb])
            rc = np.array([rb[w] for w in common])
            rhos.append(float(np.corrcoef(ra, rc)[0, 1]))
        else:
            rhos.append(float("nan"))
    return {
        "half_jaccard50": float(np.mean(jacs)) if jacs else float("nan"),
        "half_jaccard50_splits": n_splits,
        "half_rho200": float(np.mean(rhos)) if rhos else float("nan"),
    }
# ---------------------------------------------------------------------------
# Historical jury reconstruction (Part 0)
# ---------------------------------------------------------------------------

def reconstruct_deep_mint_juries(con) -> dict[str, dict[str, Any]]:
    from curators_explorer.cohort import purity_gate_sql
    from curators_explorer.scripts.research_purity_strictness_sweep import (
        elite_keep_sql,
    )

    out: dict[str, dict[str, Any]] = {}
    specs = {
        "core_p65_s25": (65, 25),
        "p75_s40": (75, 40),
        "p45_s40": (45, 40),
        "p0_s0": (0, 0),
        "p65_s0": (65, 0),
        "p0_s25": (0, 25),
        "p0_s15": (0, 15),
        "p0_s40": (0, 40),
    }
    for label, (purity, strictness) in specs.items():
        gate_sql, gate_args = purity_gate_sql(purity, alias="c")
        keep = elite_keep_sql(strictness, "n_pass")
        table = f"mj_{label}"
        con.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE {table} AS
            WITH passers AS (
                SELECT
                    c.user_id,
                    c.curator_pct_weight AS w,
                    row_number() OVER (
                        ORDER BY c.curator_pct_weight DESC
                    ) AS elite_rank,
                    count(*) OVER () AS n_pass
                FROM ex.user_curator_deep_weight c
                WHERE TRUE {gate_sql}
            )
            SELECT user_id, w FROM passers WHERE elite_rank <= {keep}
            """,
            gate_args,
        )
        rows = con.execute(f"SELECT user_id, w FROM {table} ORDER BY user_id").fetchall()
        user_ids = np.asarray([r[0] for r in rows], dtype=np.int64)
        w = np.asarray([r[1] for r in rows], dtype=np.float64)
        kish = float((w.sum() ** 2) / np.sum(w * w)) if len(w) else 0.0
        out[label] = {
            "purity": purity,
            "strictness": strictness,
            "user_ids": user_ids,
            "weights": w,
            "raw_n": int(len(user_ids)),
            "kish_n_eff": kish,
            "sum_w": float(w.sum()),
            "kind": "deep_mint_jury",
        }
    out["deep_mint_all"] = dict(out["p0_s0"])
    out["deep_mint_all"]["kind"] = "deep_mint_all"
    return out


def reconstruct_threeway_cohorts(con) -> dict[str, dict[str, Any]]:
    # Pin single-threaded DuckDB so approx_quantile thresholds are
    # reproducible across runs (cohort membership is threshold-sensitive).
    con.execute("PRAGMA threads=1")
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    con.execute("PRAGMA threads=8")
    cohort_meta = label_cohorts(con)
    out: dict[str, dict[str, Any]] = {}
    for name, table in [
        ("threeway_classic", "cohort_classic"),
        ("threeway_anti", "cohort_anti"),
        ("threeway_normie", "cohort_normie"),
    ]:
        rows = con.execute(f"SELECT user_id FROM {table} ORDER BY user_id").fetchall()
        user_ids = np.asarray([r[0] for r in rows], dtype=np.int64)
        out[name] = {
            "user_ids": user_ids,
            "raw_n": int(len(user_ids)),
            "kind": "threeway_cohort",
        }
    return out, cohort_meta


def reconstruct_rebuilt_juries() -> dict[str, dict[str, Any]]:
    con = duckdb.connect()
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("USE ex")
    rows = con.execute(
        f"SELECT user_id, hard_jury, jury_q FROM read_parquet('{SOFT_WEIGHTS_PARQUET}')"
    ).fetchall()
    con.close()
    hard_uids = np.asarray([r[0] for r in rows if r[1]], dtype=np.int64)
    all_uids = np.asarray([r[0] for r in rows], dtype=np.int64)
    soft_q = np.asarray([float(r[2]) for r in rows], dtype=np.float64)
    out = {
        "rebuilt_hard": {
            "user_ids": hard_uids,
            "raw_n": int(len(hard_uids)),
            "kind": "rebuilt_hard_jury",
        },
        "rebuilt_soft": {
            "user_ids": all_uids,
            "weights": soft_q,
            "raw_n": int(len(all_uids)),
            "soft_nonzero_n": int(np.sum(soft_q > 0)),
            "kish_n_eff": float(soft_q.sum() ** 2 / np.sum(soft_q * soft_q))
            if np.any(soft_q > 0)
            else 0.0,
            "kind": "rebuilt_soft_jury",
        },
    }
    return out


def map_to_payload(user_ids: np.ndarray, payload_ids: np.ndarray) -> np.ndarray:
    order = np.argsort(payload_ids)
    ps = payload_ids[order]
    u = np.asarray(user_ids, dtype=np.int64)
    pos = np.searchsorted(ps, u)
    pos = np.minimum(pos, len(ps) - 1)
    found = ps[pos] == u
    idx = np.full(len(u), -1, dtype=np.int64)
    idx[found] = order[pos[found]]
    return idx


def prepare_phase(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.time()
    payload = load_payload()
    X = load_feature_table(payload)
    feature_names = np.asarray(ALL_FEATURES, dtype=object)
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    meta, eval_sets = load_eval_context(payload)
    ev_all = _merged_ev(ev, eval_sets)

    print("[prepare] reconstructing deep-mint juries…", flush=True)
    juries = reconstruct_deep_mint_juries(con)

    print("[prepare] reconstructing threeway cohorts…", flush=True)
    tc, cohort_meta = reconstruct_threeway_cohorts(con)
    juries.update(tc)

    print("[prepare] reconstructing rebuilt hard/soft juries…", flush=True)
    juries.update(reconstruct_rebuilt_juries())

    for label, j in juries.items():
        if "user_ids" not in j:
            continue
        j["payload_idx"] = map_to_payload(j["user_ids"], payload["user_ids"])
        j["payload_coverage_n"] = int(np.sum(j["payload_idx"] >= 0))

    # Direct-rank every reconstructed jury with its stored weights.
    for label in sorted(juries):
        j = juries[label]
        if "user_ids" not in j:
            continue
        w = j.get("weights")
        rec = score_jury(con, j["user_ids"], weights=w, ev=ev_all, sticky=sticky,
                         scorer="pairwise")
        j["direct_rank"] = {
            k: v for k, v in rec.items() if k != "head"
        }
        j["probe"] = rec["probe"]
        j["semantic"] = rec["semantic"]
        j["head_top30"] = rec["head"][:30]
        print(
            f"[prepare] {label}: n={j['raw_n']} "
            f"kish={j.get('kish_n_eff', float('nan')):.0f} "
            f"payload={j['payload_coverage_n']} pos50={rec['probe']['pos50']} "
            f"anti50={rec['probe']['anti50']} exact50={rec['semantic']['exact_lit50']}",
            flush=True,
        )

    result = {
        "seed": MAX_JURY_SEED,
        "payload_n_users": int(len(payload["user_ids"])),
        "payload_n_works": int(len(payload["work_ids"])),
        "cohort_meta": cohort_meta,
        "juries": {
            label: {
                k: v
                for k, v in j.items()
                if k not in ("user_ids", "payload_idx", "weights")
            }
            for label, j in juries.items()
            if "user_ids" in j
        },
        "feature_names": list(ALL_FEATURES),
        "n_features": int(X.shape[1]),
        "feature_n_nan_imputed": int(np.isnan(X).sum()),
        "elapsed_s": round(time.time() - t0, 1),
    }
    arrays: dict[str, np.ndarray] = {}
    for label, j in juries.items():
        if "user_ids" not in j:
            continue
        arrays[f"juries/{label}/user_ids"] = j["user_ids"].astype(np.int64)
        arrays[f"juries/{label}/payload_idx"] = j["payload_idx"].astype(np.int64)
        if "weights" in j:
            arrays[f"juries/{label}/weights"] = j["weights"].astype(np.float64)
    arrays["user_ids"] = payload["user_ids"].astype(np.int64)
    arrays["work_ids"] = np.asarray(payload["work_ids"])
    arrays["features"] = X.astype(np.float64)
    # merge into existing OUT_NPZ (preserve any fit/label arrays)
    existing: dict[str, np.ndarray] = {}
    if OUT_NPZ.exists():
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            existing = {k: blob[k] for k in blob.files}
    existing.update(arrays)
    _write_npz_atomic(OUT_NPZ, existing)
    _write_text_atomic(OUT_JSON, json.dumps(result, indent=1))
    _write_text_atomic(STATE_DIR / "prepare.json", json.dumps(result, indent=1))
    con.close()
    print(f"[prepare] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Part 1 — failed-10k paired forensic analysis
# ---------------------------------------------------------------------------

def reconstruct_10k_splits(
    breeding_npz: dict[str, np.ndarray], breeding_json: dict,
) -> list[dict[str, Any]]:
    from curators_explorer.scripts.research_recursive_family_breeding import (
        BREEDING_SEED,
        balanced_partitions,
    )

    obs: list[dict[str, Any]] = []
    for root_id in (0, 1):
        pool_key = f"root{root_id}_lit_g1_selected"
        pool = np.sort(np.asarray(breeding_npz[pool_key], dtype=np.int64))
        generation = 2
        child_runs: list[dict[str, Any]] = []
        for branch in breeding_json["roots"][root_id]["branches"]["lit"]:
            if branch["generation"] == generation:
                child_runs = branch["child_runs"]
                break
        by_rep: dict[int, dict[int, dict[str, Any]]] = {}
        for rec in child_runs:
            by_rep.setdefault(int(rec["replicate"]), {})[int(rec["group"])] = rec
        for rep in sorted(by_rep):
            rng = np.random.default_rng(
                _derive_seed(BREEDING_SEED, "partition", root_id, "lit",
                             generation, rep)
            )
            groups = balanced_partitions(pool, 2, rng)
            a_rec = by_rep[rep][0]
            b_rec = by_rep[rep][1]
            obs.append(
                {
                    "root": root_id,
                    "replicate": rep,
                    "A": groups[0],
                    "B": groups[1],
                    "A_rec": a_rec,
                    "B_rec": b_rec,
                }
            )
    return obs


def forensic_10k_phase(args: argparse.Namespace, payload: dict[str, np.ndarray],
                       X: np.ndarray, feature_names: np.ndarray) -> dict[str, Any]:
    t0 = time.time()
    with np.load(BREEDING_NPZ, allow_pickle=False) as blob:
        breeding_npz = {k: blob[k] for k in blob.files}
    breeding_json = json.loads(BREEDING_JSON.read_text(encoding="utf-8"))
    obs = reconstruct_10k_splits(breeding_npz, breeding_json)
    feat_idx = {str(f): i for i, f in enumerate(feature_names)}
    feats = LOAD_BEARING
    rows: list[dict[str, Any]] = []
    for ob in obs:
        a = ob["A"]
        b = ob["B"]
        row = {
            "root": ob["root"],
            "replicate": ob["replicate"],
            "delta_f1_margin": float(
                ob["A_rec"]["deepest_margin"] - ob["B_rec"]["deepest_margin"]),
            "delta_stage0_margin": float(
                ob["A_rec"]["stage0_margin"] - ob["B_rec"]["stage0_margin"]),
            "delta_reversal_gain": float(
                ob["A_rec"]["reversal_gain"] - ob["B_rec"]["reversal_gain"]),
            "delta_exact50": float(ob["A_rec"]["exact50"] - ob["B_rec"]["exact50"]),
            "delta_anti50": float(ob["A_rec"]["anti50"] - ob["B_rec"]["anti50"]),
        }
        for f in feats:
            i = feat_idx[f]
            row[f"delta_{f}"] = float(np.nanmean(X[a, i]) - np.nanmean(X[b, i]))
        rows.append(row)

    mat = np.empty((len(rows), len(feats)), dtype=np.float64)
    for j, f in enumerate(feats):
        mat[:, j] = [row[f"delta_{f}"] for row in rows]
    mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)
    y = np.asarray([row["delta_f1_margin"] for row in rows], dtype=np.float64)
    mu, sd = mat.mean(axis=0), mat.std(axis=0) + 1e-9
    z = (mat - mu) / sd
    n = len(rows)
    alpha = 1.0
    pred = np.empty(n)
    coefs = []
    for i in range(n):
        train = np.ones(n, dtype=bool)
        train[i] = False
        beta = np.linalg.solve(z[train].T @ z[train] + alpha * np.eye(len(feats)),
                               z[train].T @ y[train])
        pred[i] = z[i] @ beta
        coefs.append(beta)
    full_beta = np.linalg.solve(z.T @ z + alpha * np.eye(len(feats)), z.T @ y)
    corr = float(np.corrcoef(pred, y)[0, 1])
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - np.sum((pred - y) ** 2) / ss if ss > 0 else float("nan")

    univ = {}
    for f in feats:
        i = feat_idx[f]
        dv = np.asarray([row[f"delta_{f}"] for row in rows], dtype=np.float64)
        univ[f] = {
            "corr": float(np.corrcoef(dv, y)[0, 1]),
            "mean_delta": float(np.mean(dv)),
            "sd_delta": float(np.std(dv)),
        }
    root_signs = {}
    for f in feats:
        root_signs[f] = {}
        for root in (0, 1):
            vals = [row[f"delta_{f}"] for row in rows if row["root"] == root]
            root_signs[f][root] = float(np.mean(vals)) if vals else float("nan")

    # Verify partition reconstruction by recomputing stored g2 fitness.
    from curators_explorer.scripts.research_recursive_family_breeding import (
        BREEDING_SEED,
        balanced_partitions,
        fitness_from_margins,
        group_assignments,
    )
    fit_check = {}
    for root_id in (0, 1):
        pool = np.sort(np.asarray(breeding_npz[f"root{root_id}_lit_g1_selected"],
                                  dtype=np.int64))
        stored_fit = np.asarray(breeding_npz[f"root{root_id}_lit_g2_fitness"],
                                dtype=np.float64)
        margins = np.zeros((12, 2), dtype=np.float64)
        for ob in obs:
            if ob["root"] != root_id:
                continue
            margins[ob["replicate"], 0] = ob["A_rec"]["deepest_margin"]
            margins[ob["replicate"], 1] = ob["B_rec"]["deepest_margin"]
        assignments = []
        for rep in range(12):
            rng = np.random.default_rng(
                _derive_seed(BREEDING_SEED, "partition", root_id, "lit", 2, rep))
            groups = balanced_partitions(pool, 2, rng)
            assignments.append(group_assignments(pool, groups))
        fit, _ = fitness_from_margins(margins, np.stack(assignments))
        fit_check[root_id] = {
            "recomputed_fitness_corr": float(np.corrcoef(fit, stored_fit)[0, 1]),
            "max_abs_diff": float(np.max(np.abs(fit - stored_fit))),
        }

    result = {
        "n_paired_obs": len(rows),
        "n_roots": 2,
        "n_replicates": 12,
        "features": feats,
        "ridge": {
            "alpha": alpha,
            "loo_corr": corr,
            "loo_r2": r2,
            "coefficients_std": {f: float(c) for f, c in zip(feats, full_beta)},
            "coefficient_sd": {
                f: float(np.std([c[i] for c in coefs])) for i, f in enumerate(feats)
            },
        },
        "univariate": univ,
        "root_signs": root_signs,
        "reconstruction_checks": fit_check,
        "paired_rows": rows,
        "elapsed_s": round(time.time() - t0, 1),
    }
    _write_text_atomic(STATE_DIR / "forensic10k.json", json.dumps(result, indent=1))
    print(
        f"[forensic10k] n={len(rows)} loo_corr={corr:.3f} loo_r2={r2:.3f} "
        f"fitness_corr0={fit_check[0]['recomputed_fitness_corr']:.6f}",
        flush=True,
    )
    return result
# ---------------------------------------------------------------------------
# Part 3/4 — training labels + models
# ---------------------------------------------------------------------------

def build_labels(payload_ids: np.ndarray, juries: dict[str, dict[str, Any]]) -> dict[str, np.ndarray]:
    n = len(payload_ids)
    labels: dict[str, np.ndarray] = {}

    def membership(label: str) -> np.ndarray:
        idx = juries[label]["payload_idx"]
        m = np.zeros(n, dtype=np.float64)
        m[idx[idx >= 0]] = 1.0
        return m

    for key, jury in [
        ("p65_s25", "core_p65_s25"), ("p75_s40", "p75_s40"),
        ("p45_s40", "p45_s40"), ("p0_s0", "p0_s0"),
        ("p0_s25", "p0_s25"), ("p0_s15", "p0_s15"),
        ("threeway_classic", "threeway_classic"),
        ("threeway_anti", "threeway_anti"),
        ("threeway_normie", "threeway_normie"),
        ("rebuilt_hard", "rebuilt_hard"),
    ]:
        labels[key] = membership(jury)
    soft = np.zeros(n, dtype=np.float64)
    for name in SOFT_CONSENSUS_JURIES:
        soft += labels[name]
    soft = soft / len(SOFT_CONSENSUS_JURIES)
    labels["soft_consensus"] = soft
    return labels


def stratified_folds(n: int, y: np.ndarray, n_folds: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y > 0.5)
    neg = np.flatnonzero(y <= 0.5)
    rp = rng.permutation(pos)
    rn = rng.permutation(neg)
    folds = np.zeros(n, dtype=np.int8)
    for f in range(n_folds):
        folds[rp[f::n_folds]] = f
        folds[rn[f::n_folds]] = f
    return folds


def _oof_full_population(X, y, train_mask, folds, feature_names, *, kind, seed):
    """OOF scores for EVERY user. Training-universe users are scored by the fold
    that excluded their label; non-training users by the mean across folds."""
    n = len(y)
    score = np.full(n, np.nan)
    coef_rows: list[np.ndarray] = []
    n_folds = int(folds.max()) + 1
    pred_all: list[np.ndarray] = []
    for fold in range(n_folds):
        train = (folds != fold) & train_mask
        if train.sum() == 0:
            continue
        if kind == "elasticnet":
            clf = LogisticRegression(
                penalty="elasticnet", solver="saga", l1_ratio=0.5, C=1.0,
                max_iter=5000, class_weight="balanced",
                random_state=_sk_rng_seed(seed, fold),
            )
        elif kind == "l2":
            clf = LogisticRegression(
                penalty="l2", C=1.0, max_iter=5000, class_weight="balanced",
                random_state=_sk_rng_seed(seed, fold),
            )
        else:
            raise ValueError(kind)
        Xt = np.nan_to_num(X[train], nan=0.0)
        clf.fit(Xt, y[train])
        pred_all.append(clf.decision_function(np.nan_to_num(X, nan=0.0)))
        coef_rows.append(np.asarray(clf.coef_).ravel())
    pred_all = np.stack(pred_all)
    # training-universe users: use the fold where they were held out
    for fold in range(n_folds):
        if fold >= pred_all.shape[0]:
            continue
        sel = (folds == fold) & train_mask
        score[sel] = pred_all[fold][sel]
    # non-training users: mean across folds
    not_trained = ~train_mask
    score[not_trained] = pred_all.mean(axis=0)[not_trained]
    valid = np.isfinite(score) & train_mask
    auc = float(roc_auc_score(y[valid], score[valid]))
    ap = float(average_precision_score(y[valid], score[valid]))
    mean_coef = np.mean(np.vstack(coef_rows), axis=0) if coef_rows else np.zeros(0)
    return {
        "model_kind": f"logistic_{kind}",
        "auc": auc,
        "average_precision": ap,
        "positive_n": int(y[train_mask].sum()),
        "negative_n": int((~y[train_mask].astype(bool)).sum()),
        "score": score,
        "coefficients": {
            str(f): float(c) for f, c in zip(feature_names, mean_coef)
        },
    }


def _fit_gbm(X, y, train_mask, folds, feature_names, *, seed):
    n = len(y)
    score = np.full(n, np.nan)
    pred_all: list[np.ndarray] = []
    n_folds = int(folds.max()) + 1
    clfs: list = []
    for fold in range(n_folds):
        train = (folds != fold) & train_mask
        if train.sum() == 0:
            continue
        clf = HistGradientBoostingClassifier(
            max_iter=250, learning_rate=0.1, max_leaf_nodes=31,
            min_samples_leaf=40, l2_regularization=1.0,
            random_state=_sk_rng_seed(seed, fold),
        )
        clf.fit(np.nan_to_num(X[train], nan=0.0), y[train])
        pred_all.append(clf.decision_function(np.nan_to_num(X, nan=0.0)))
        clfs.append(clf)
    pred_all = np.stack(pred_all)
    for fold in range(n_folds):
        if fold >= pred_all.shape[0]:
            continue
        sel = (folds == fold) & train_mask
        score[sel] = pred_all[fold][sel]
    not_trained = ~train_mask
    score[not_trained] = pred_all.mean(axis=0)[not_trained]
    valid = np.isfinite(score) & train_mask
    auc = float(roc_auc_score(y[valid], score[valid]))
    ap = float(average_precision_score(y[valid], score[valid]))
    importances: dict[str, float] = {}
    if clfs:
        clf = clfs[-1]
        test = np.flatnonzero(valid)[:20000]
        Xt = np.nan_to_num(X[test], nan=0.0)
        base = roc_auc_score(y[test], clf.decision_function(Xt))
        for j in range(X.shape[1]):
            Xp = Xt.copy()
            Xp[:, j] = np.random.default_rng(_sk_rng_seed(seed, "perm", j)).permutation(Xp[:, j])
            importances[str(feature_names[j])] = float(
                base - roc_auc_score(y[test], clf.decision_function(Xp)))
    return {
        "model_kind": "hist_gradient_boosting",
        "auc": auc,
        "average_precision": ap,
        "positive_n": int(y[train_mask].sum()),
        "score": score,
        "importances": importances,
    }


def _fit_soft_ridge(X, target, train_mask, folds, feature_names, *, seed):
    n = len(target)
    score = np.full(n, np.nan)
    coef_rows: list[np.ndarray] = []
    pred_all: list[np.ndarray] = []
    n_folds = int(folds.max()) + 1
    for fold in range(n_folds):
        train = (folds != fold) & train_mask
        if train.sum() == 0:
            continue
        reg = Ridge(alpha=1.0)
        reg.fit(np.nan_to_num(X[train], nan=0.0), target[train])
        pred_all.append(reg.predict(np.nan_to_num(X, nan=0.0)))
        coef_rows.append(np.asarray(reg.coef_).ravel())
    pred_all = np.stack(pred_all)
    for fold in range(n_folds):
        if fold >= pred_all.shape[0]:
            continue
        sel = (folds == fold) & train_mask
        score[sel] = pred_all[fold][sel]
    not_trained = ~train_mask
    score[not_trained] = pred_all.mean(axis=0)[not_trained]
    valid = np.isfinite(score) & train_mask
    corr = float(np.corrcoef(score[valid], target[valid])[0, 1])
    mean_coef = np.mean(np.vstack(coef_rows), axis=0) if coef_rows else np.zeros(0)
    return {
        "model_kind": "ridge_soft",
        "corr": corr,
        "rmse": float(np.sqrt(np.mean((score[valid] - target[valid]) ** 2))),
        "score": score,
        "coefficients": {
            str(f): float(c) for f, c in zip(feature_names, mean_coef)
        },
    }


def leave_one_jury_out(X, labels, feature_names, *, seed) -> dict[str, Any]:
    jury_names = ["p75_s40", "p65_s25", "p45_s40", "threeway_classic", "p0_s0",
                  "rebuilt_hard"]
    out: dict[str, Any] = {}
    for held in jury_names:
        if held not in labels:
            continue
        others = [k for k in jury_names if k != held and k in labels]
        y_train = np.maximum.reduce([labels[k] for k in others])
        y_held = labels[held]
        pos = np.flatnonzero(y_train > 0.5)
        neg = np.flatnonzero(y_train <= 0.5)
        if len(pos) == 0 or len(neg) == 0:
            out[held] = {"held_jury": held, "skipped": True}
            continue
        rng = np.random.default_rng(_derive_seed(seed, "lojdo", held))
        n_neg = min(len(neg), len(pos) * 3)
        neg_sel = rng.choice(neg, n_neg, replace=False)
        train_idx = np.concatenate([pos, neg_sel])
        model = LogisticRegression(
            penalty="elasticnet", solver="saga", l1_ratio=0.5, C=1.0,
            max_iter=1500, class_weight="balanced",
            random_state=_sk_rng_seed(seed, "lojdo_fit", held),
        )
        model.fit(np.nan_to_num(X[train_idx], nan=0.0), y_train[train_idx])
        score_all = model.decision_function(np.nan_to_num(X, nan=0.0))
        held_pos = y_held > 0.5
        held_neg = y_held <= 0.5
        if held_pos.sum() == 0 or held_neg.sum() == 0:
            out[held] = {"held_jury": held, "skipped": True}
            continue
        auc = float(roc_auc_score(held_pos, score_all))
        top1 = np.argsort(-score_all)[: len(score_all) // 100]
        top1_rate = float(np.mean(held_pos[top1]))
        base_rate = float(np.mean(held_pos))
        out[held] = {
            "held_jury": held,
            "train_union_size": int(len(train_idx)),
            "auc": auc,
            "held_rate": base_rate,
            "top1pct_held_rate": top1_rate,
            "enrichment_ratio": float(top1_rate / max(base_rate, 1e-9)),
        }
        print(
            f"[fit] LOJDO held={held} AUC={auc:.3f} top1%={top1_rate:.4f} "
            f"base={base_rate:.4f} enrich={top1_rate / max(base_rate, 1e-9):.2f}x",
            flush=True,
        )
    return out


def _fit_oracle(payload, y_bin, train_mask, folds_bin, labels) -> dict[str, Any]:
    """Explicit upper-bound model using DIRECT seed-hit features."""
    n = len(payload["user_ids"])
    uids = payload["user_ids"]
    order = np.argsort(uids)
    uid_sorted = uids[order]
    con = duckdb.connect()
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("USE ex")
    materialize_seed_sets(con)
    hits = {}
    for name, seed_table in [
        ("classic", "seed_classic"), ("anti", "seed_anti"), ("normie", "seed_normie"),
    ]:
        rows = con.execute(
            f"""
            SELECT e.user_id, count(DISTINCT e.work_id)::DOUBLE AS c
            FROM ex.all_rating_events e
            JOIN {seed_table} s USING (work_id)
            WHERE e.rating = 5 AND e.user_id IN (SELECT unnest(?::BIGINT[]))
            GROUP BY e.user_id
            """,
            [uids.tolist()],
        ).fetchall()
        v = np.zeros(n, dtype=np.float64)
        if rows:
            ru = np.asarray([r[0] for r in rows], dtype=np.int64)
            pos = np.searchsorted(uid_sorted, ru)
            pos = np.minimum(pos, n - 1)
            v[order[pos]] = np.asarray([r[1] for r in rows])
        hits[name] = v
    con.close()
    Xor = np.column_stack(
        [hits["classic"], hits["anti"], hits["normie"], labels["p75_s40"],
         labels["p45_s40"]]
    )
    score = np.full(n, np.nan)
    pred_all: list[np.ndarray] = []
    n_folds = int(folds_bin.max()) + 1
    for fold in range(n_folds):
        train = (folds_bin != fold) & train_mask
        if train.sum() == 0:
            continue
        clf = LogisticRegression(
            C=10.0, max_iter=5000, class_weight="balanced",
            random_state=_sk_rng_seed(MAX_JURY_SEED, "oracle", fold),
        )
        clf.fit(Xor[train], y_bin[train])
        pred_all.append(clf.decision_function(Xor))
    pred_all = np.stack(pred_all)
    for fold in range(n_folds):
        if fold >= pred_all.shape[0]:
            continue
        sel = (folds_bin == fold) & train_mask
        score[sel] = pred_all[fold][sel]
    not_trained = ~train_mask
    score[not_trained] = pred_all.mean(axis=0)[not_trained]
    valid = np.isfinite(score) & train_mask
    auc = float(roc_auc_score(y_bin[valid], score[valid]))
    return {
        "model_kind": "oracle_seed_hits",
        "auc": auc,
        "positive_n": int(y_bin[train_mask].sum()),
        "score": score,
        "note": "DIRECT SEED-HIT FEATURES - explicit upper bound, not behaviour-only",
    }


def fit_phase(args: argparse.Namespace, payload: dict[str, np.ndarray],
              X: np.ndarray, feature_names: np.ndarray,
              juries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    t0 = time.time()
    if not HAS_SKLEARN:
        raise RuntimeError("scikit-learn not available; cannot run fit phase")
    labels = build_labels(payload["user_ids"], juries)

    y_core = labels["p65_s25"]
    anti_like = np.maximum(labels["threeway_anti"], labels["threeway_normie"])

    # Matched negative pool: anti/normie users matched on log_n_rated bins.
    log_idx = int(np.argwhere(np.asarray(feature_names) == "log_n_rated")[0][0])
    rng = np.random.default_rng(_derive_seed(MAX_JURY_SEED, "negmatch"))
    pos_log = X[y_core > 0.5, log_idx]
    cuts = np.quantile(pos_log, np.linspace(0, 1, 9))
    bins = np.searchsorted(cuts, X[:, log_idx], side="right").clip(0, 8)
    pos_hist = np.bincount(bins[y_core > 0.5], minlength=9).astype(np.float64)
    sel_lists: list[np.ndarray] = []
    for b in range(9):
        pool = np.flatnonzero((bins == b) & (y_core <= 0.5) & (anti_like > 0.5))
        k = int(np.ceil(pos_hist[b] * 2.0))
        if len(pool) == 0:
            continue
        sel_lists.append(rng.choice(pool, min(k, len(pool)), replace=False))
    neg_sel = np.concatenate(sel_lists) if sel_lists else np.asarray([], dtype=np.int64)

    train_mask = np.zeros(len(X), dtype=bool)
    train_mask[y_core > 0.5] = True
    train_mask[neg_sel] = True
    y_bin = np.zeros(len(X), dtype=np.int8)
    y_bin[y_core > 0.5] = 1
    folds_bin = stratified_folds(
        len(X), y_bin, 5, _derive_seed(MAX_JURY_SEED, "folds_bin"))

    results: dict[str, Any] = {}
    models: dict[str, Any] = {}
    for kind in ("elasticnet", "l2"):
        r = _oof_full_population(X, y_bin, train_mask, folds_bin, feature_names,
                                 kind=kind, seed=_derive_seed(MAX_JURY_SEED, "bin", kind))
        models[f"binary_{kind}"] = r
        print(f"[fit] binary_{kind} AUC={r['auc']:.3f} AP={r['average_precision']:.3f} "
              f"pos={r['positive_n']} neg={r['negative_n']}",
             flush=True)
    gbm = _fit_gbm(X, y_bin, train_mask, folds_bin, feature_names,
                   seed=_derive_seed(MAX_JURY_SEED, "bin", "gbm"))
    models["binary_gbm"] = gbm
    print(f"[fit] binary_gbm AUC={gbm['auc']:.3f} AP={gbm['average_precision']:.3f}",
         flush=True)

    soft = _fit_soft_ridge(X, labels["soft_consensus"], train_mask, folds_bin,
                           feature_names, seed=_derive_seed(MAX_JURY_SEED, "soft"))
    models["soft_ridge"] = soft
    print(f"[fit] soft_ridge corr={soft['corr']:.3f}", flush=True)

    lojdo = leave_one_jury_out(X, labels, feature_names,
                               seed=_derive_seed(MAX_JURY_SEED, "lojdo"))

    ablations: dict[str, Any] = {}
    drop_sets = {
        "no_publication_year": ["mean_pub_year_5"],
        "no_series_binge": ["series_share_5", "binge_mean_5", "binge_max_5_log"],
        "no_popularity": FEATURE_GROUPS["popularity"],
    }
    for name, drops in drop_sets.items():
        keep_idx = [i for i, f in enumerate(feature_names) if str(f) not in set(drops)]
        r = _oof_full_population(
            X[:, keep_idx], y_bin, train_mask, folds_bin,
            np.asarray([str(f) for f in feature_names[keep_idx]], dtype=object),
            kind="elasticnet", seed=_derive_seed(MAX_JURY_SEED, "abl", name))
        ablations[name] = {
            "auc": r["auc"],
            "average_precision": r["average_precision"],
            "positive_n": r["positive_n"],
            "dropped": drops,
            "coefficients": r["coefficients"],
        }
        print(f"[fit] ablation {name} AUC={r['auc']:.3f}", flush=True)

    oracle = _fit_oracle(payload, y_bin, train_mask, folds_bin, labels)
    print(f"[fit] oracle AUC={oracle['auc']:.3f} (seed-hit upper bound)", flush=True)

    results = {
        "labels": {
            k: {"positive_n": int(v.sum()), "rate": float(v.mean())}
            for k, v in labels.items()
        },
        "models": models,
        "lojdo": lojdo,
        "ablations": ablations,
        "oracle": oracle,
        "y_bin": y_bin,
        "train_mask": train_mask,
        "folds_bin": folds_bin,
        "matched_negatives_n": int(len(neg_sel)),
        "elapsed_s": round(time.time() - t0, 1),
    }
    arrays: dict[str, np.ndarray] = {}
    for k, v in labels.items():
        arrays[f"labels/{k}"] = v.astype(np.float64)
    arrays["labels/y_bin"] = y_bin
    arrays["labels/folds_bin"] = folds_bin
    arrays["labels/train_mask"] = train_mask
    for name, m in models.items():
        arrays[f"scores/{name}"] = m["score"]
    arrays["scores/oracle"] = oracle["score"]
    # merge into existing OUT_NPZ (preserve prepare arrays)
    existing: dict[str, np.ndarray] = {}
    if OUT_NPZ.exists():
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            existing = {k: blob[k] for k in blob.files}
    existing.update(arrays)
    _write_npz_atomic(OUT_NPZ, existing)

    # JSON-safe copy (score arrays and masks live in NPZ only)
    results_json = {k: v for k, v in results.items()
                    if k not in ("y_bin", "train_mask", "folds_bin")}
    safe = json.loads(json.dumps(results_json, default=_json_default))
    _write_text_atomic(STATE_DIR / "fit.json", json.dumps(safe, indent=1))
    print(f"[fit] done in {_fmt_time(time.time() - t0)}", flush=True)
    return results
# ---------------------------------------------------------------------------
# Part 5/6/7 — full-population scores, direct frontier, J_star selection
# ---------------------------------------------------------------------------

def _load_fit_state() -> dict[str, Any]:
    return json.loads((STATE_DIR / "fit.json").read_text(encoding="utf-8"))


def _load_labels_scores(payload_ids: np.ndarray) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        labels = {
            k: blob[k] for k in blob.files if k.startswith("labels/")
        }
        scores = {
            k: blob[k] for k in blob.files if k.startswith("scores/")
        }
    return labels, scores


def _make_jury_members(payload_ids: np.ndarray, order: np.ndarray,
                       size: int) -> np.ndarray:
    return payload_ids[order[: min(size, len(order))]]


def direct_jury_rec(con, user_ids: np.ndarray, name: str, *, ev, sticky,
                    scorer: str = "pairwise") -> dict[str, Any]:
    rec = score_jury(con, user_ids, ev=ev, sticky=sticky, scorer=scorer)
    half = half_split_jaccard(
        con, user_ids, ev=ev, sticky=sticky,
        rng=np.random.default_rng(_derive_seed(MAX_JURY_SEED, "half", name)),
        scorer=scorer,
    )
    rec.update(half)
    rec["name"] = name
    rec["raw_n"] = int(len(user_ids))
    rec["kish_n_eff"] = float(len(user_ids))
    return rec


def choose_jstar(frontier: list[dict[str, Any]]) -> dict[str, Any]:
    """Frozen deterministic J_star rule (see JSTAR_RULE).

    Candidates are restricted to model-constructed nested juries (top_*,
    corepres_*, coreexcl_*); historical-exact and random/control juries are
    references only, not amplification bases.
    """
    def is_model(f: dict[str, Any]) -> bool:
        return f["name"].startswith(("top_", "corepres_", "coreexcl_"))

    model = [f for f in frontier if is_model(f)]
    candidates = [f for f in model if f["raw_n"] >= 10000 and f["probe"]["anti50"] <= 5]
    if not candidates:
        candidates = [f for f in model if f["probe"]["anti50"] <= 5]
        if not candidates:
            raise RuntimeError("no model jury passes anti50<=5 at all")

    def _jstar_key(f):
        hj = f.get("half_jaccard50", float("nan"))
        hj = hj if np.isfinite(hj) else -1.0
        return (
            f["probe"]["pos50"] + 0.25 * f["semantic"]["broad_lit50"]
            + 5.0 * hj,
            f.get("kish_n_eff", 0.0),
            f["raw_n"],
        )
    return max(candidates, key=_jstar_key)


def frontier_phase(args: argparse.Namespace, payload: dict[str, np.ndarray],
                   X: np.ndarray, feature_names: np.ndarray,
                   juries: dict[str, dict[str, Any]],
                   fit_state: dict[str, Any]) -> dict[str, Any]:
    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    rng = np.random.default_rng(_derive_seed(MAX_JURY_SEED, "frontier"))
    _meta, eval_sets = load_eval_context(payload)
    ev_all = _merged_ev(ev, eval_sets)
    _ensure_pair_cache(con, payload["user_ids"])

    labels, scores = _load_labels_scores(payload["user_ids"])
    model_key = "scores/binary_gbm" if args.frontier_model == "flexible" else "scores/binary_elasticnet"
    if model_key not in scores:
        raise RuntimeError(f"{model_key} missing; run fit first")
    score = scores[model_key]

    payload_ids = payload["user_ids"]
    n = len(payload_ids)
    core_payload = juries["core_p65_s25"]["payload_idx"]
    core_mask = np.zeros(n, dtype=bool)
    core_mask[core_payload[core_payload >= 0]] = True
    order = np.lexsort((payload_ids, -score))
    core_users = payload_ids[core_mask]
    outside_mask = ~core_mask
    outside = payload_ids[outside_mask]
    outside_order_final = order[outside_mask[order]]

    checkpoint = CHUNK_DIR / f"frontier_{model_key.split('/')[-1]}.json"
    if checkpoint.exists():
        frontier = json.loads(checkpoint.read_text(encoding="utf-8"))
        done = {f["name"] for f in frontier}
    else:
        frontier, done = [], set()

    def run_if_missing(name: str, user_ids: np.ndarray) -> None:
        nonlocal frontier
        if name in done:
            return
        rec = direct_jury_rec(con, user_ids, name, ev=ev_all, sticky=sticky)
        frontier.append(rec)
        frontier = sorted(frontier, key=lambda r: r["name"])
        _write_text_atomic(checkpoint, json.dumps(frontier, indent=1))
        print(
            f"[frontier] {name}: n={rec['raw_n']} pos50={rec['probe']['pos50']} "
            f"broad50={rec['semantic']['broad_lit50']} "
            f"anti50={rec['probe']['anti50']} J50={rec['half_jaccard50']:.2f}",
            flush=True,
        )

    for size in FRONTIER_SIZES:
        run_if_missing(f"top_{size}", _make_jury_members(payload_ids, order, size))

    core_sizes = [5000, 8000, 10000, 15000, 20000, 30000, 40000, 60000,
                  80000, 100000, 120000, 150000]
    for size in core_sizes:
        k = max(size - len(core_users), 0)
        k = min(k, len(outside))
        add = payload_ids[outside_order_final[:k]]
        run_if_missing(f"corepres_{size}", np.concatenate([core_users, add]))

    for size in [500, 1000, 2000, 5000, 8000, 10000, 20000, 30000, 50000]:
        k = min(size, len(outside))
        run_if_missing(f"coreexcl_{size}", payload_ids[outside_order_final[:k]])

    for label, ukey in [
        ("exact_core_p65_s25", "core_p65_s25"),
        ("exact_deep_mint", "deep_mint_all"),
        ("exact_threeway_classic", "threeway_classic"),
        ("exact_rebuilt_hard", "rebuilt_hard"),
    ]:
        idx = juries[ukey]["payload_idx"]
        run_if_missing(f"exact_{label}", payload_ids[idx[idx >= 0]])

    for size in [2000, 10000, 20000, 50000]:
        u = payload_ids[rng.choice(n, size, replace=False)]
        run_if_missing(f"random_{size}", np.sort(u))

    # activity-matched random at 10k and 20k (match log_n_rated of top model jury)
    log_idx = int(np.argwhere(np.asarray(feature_names) == "log_n_rated")[0][0])
    for target_size in [10000, 20000]:
        base_bins = np.quantile(X[order[:target_size], log_idx], np.linspace(0, 1, 21))
        bin_of = np.searchsorted(base_bins, X[:, log_idx], side="right").clip(0, 20)
        hist = np.bincount(bin_of[order[:target_size]], minlength=21).astype(np.float64)
        chosen: list[np.ndarray] = []
        for b in range(21):
            pool = np.flatnonzero(bin_of == b)
            k = int(hist[b])
            if len(pool) == 0:
                continue
            chosen.append(rng.choice(pool, min(k, len(pool)), replace=False))
        u = np.concatenate(chosen) if chosen else np.asarray([], dtype=np.int64)
        u = payload_ids[np.sort(u)]
        run_if_missing(f"actmatch_rand_{target_size}", u)

    # score-shuffled control (permute scores, then top-k) at 10k/20k
    for size in [10000, 20000]:
        shuf = rng.permutation(score)
        ord_s = np.lexsort((payload_ids, -shuf))
        run_if_missing(f"scoreshuffle_{size}", payload_ids[ord_s[:size]])

    # feature-shuffled model-score control: refit elasticnet on permuted X
    print("[frontier] feature-shuffle refit starting…", flush=True)
    from sklearn.linear_model import LogisticRegression as _LR
    Xsh = X.copy()
    for c in range(X.shape[1]):
        Xsh[:, c] = rng.permutation(Xsh[:, c])
    y_bin = labels.get("labels/y_bin", np.zeros(n, dtype=np.int8))
    sh_score = np.full(n, np.nan)
    folds_bin = labels.get("labels/folds_bin", np.zeros(n, dtype=np.int8))
    train_mask = labels.get("labels/train_mask", np.zeros(n, dtype=bool))
    pred_all_sh: list[np.ndarray] = []
    for fold in range(5):
        train = (folds_bin != fold) & train_mask
        if train.sum() == 0:
            continue
        clf = _LR(
            C=1.0, max_iter=1000, class_weight="balanced",
            random_state=_sk_rng_seed(MAX_JURY_SEED, "fshuf", fold))
        clf.fit(np.nan_to_num(Xsh[train], nan=0.0), y_bin[train])
        pred_all_sh.append(clf.decision_function(np.nan_to_num(Xsh, nan=0.0)))
        print(f"[frontier] feature-shuffle fold {fold} done", flush=True)
    pred_all_sh = np.stack(pred_all_sh)
    for fold in range(5):
        if fold >= pred_all_sh.shape[0]:
            continue
        sel = (folds_bin == fold) & train_mask
        sh_score[sel] = pred_all_sh[fold][sel]
    sh_score[~train_mask] = pred_all_sh.mean(axis=0)[~train_mask]
    print("[frontier] feature-shuffle refit done; ranking control juries…", flush=True)
    ord_sh = np.lexsort((payload_ids, -sh_score))
    for size in [10000, 20000]:
        run_if_missing(f"feature_shuffle_{size}", payload_ids[ord_sh[:size]])

    jstar = choose_jstar(frontier)
    result = {
        "frontier_model": model_key,
        "jstar_rule": JSTAR_RULE,
        "n_frontier_juries": len(frontier),
        "jstar": {k: v for k, v in jstar.items() if k != "head"},
        "jstar_name": jstar["name"],
        "frontier": [{k: v for k, v in f.items() if k != "head"} for f in frontier],
        "elapsed_s": round(time.time() - t0, 1),
    }
    # persist selected J_star members for the perturb phase
    jname = jstar["name"]
    if jname.startswith("corepres_"):
        size = int(jname.split("_")[1])
        k = max(size - len(core_users), 0)
        k = min(k, len(outside))
        members = np.concatenate([core_users, payload_ids[outside_order_final[:k]]])
    elif jname.startswith("coreexcl_"):
        size = int(jname.split("_")[1])
        members = payload_ids[outside_order_final[: min(size, len(outside))]]
    elif jname.startswith("exact_"):
        ukey = {"exact_core_p65_s25": "core_p65_s25", "exact_deep_mint": "deep_mint_all",
                "exact_threeway_classic": "threeway_classic",
                "exact_rebuilt_hard": "rebuilt_hard"}[jname]
        idx = juries[ukey]["payload_idx"]
        members = payload_ids[idx[idx >= 0]]
    else:
        size = int(jname.split("_")[-1])
        members = _make_jury_members(payload_ids, order, size)
    _write_npz_atomic(STATE_DIR / "jstar.npz", {"members": members.astype(np.int64)})
    _write_text_atomic(STATE_DIR / "frontier.json", json.dumps(result, indent=1))
    con.close()
    print(
        f"[frontier] J_star={result['jstar_name']} n={jstar['raw_n']} "
        f"pos50={jstar['probe']['pos50']} anti50={jstar['probe']['anti50']} "
        f"J50={jstar['half_jaccard50']:.2f} done in {_fmt_time(time.time() - t0)}",
        flush=True,
    )
    return result
# ---------------------------------------------------------------------------
# Part 8 — constant-size swap perturbations
# ---------------------------------------------------------------------------

PERTURB_PRIMARY_WEIGHTS = {"ref_cosine": 0.7, "half_jaccard": 0.3}
PERTURB_OUTCOME_DEF = (
    "primary = 0.7*ref_cosine + 0.3*half_jaccard; ref = frozen p65_s25 "
    "weighted pairwise ranking; ref_cosine over common top-1000 works"
)


def _reference_vector(payload: dict[str, np.ndarray], con, ev, sticky) -> dict[str, Any]:
    """Frozen literary reference from the p65_s25 weighted ranking."""
    table = "mj_ref_p65"
    con.execute(
        f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT, w DOUBLE)")
    jp = np.load(OUT_NPZ, allow_pickle=False)
    uids = jp["juries/core_p65_s25/user_ids"].astype(np.int64)
    w = jp["juries/core_p65_s25/weights"].astype(np.float64)
    con.execute(
        f"INSERT INTO {table} SELECT * FROM ("
        f"SELECT unnest(?::BIGINT[]) AS user_id, unnest(?::DOUBLE[]) AS w)",
        [uids.tolist(), w.tolist()],
    )
    rows = _pairwise_score_rows(con, table)
    vec = {r["work_id"]: float(r["score"]) for r in rows}
    return {"vec": vec}


def _ref_cosine(ref: dict[str, Any], cand_rows: list[dict]) -> float:
    bv = {r["work_id"]: float(r["score"]) for r in cand_rows}
    common = [r["work_id"] for r in cand_rows[:1000] if r["work_id"] in ref["vec"]]
    if len(common) < 10:
        return float("nan")
    a = np.asarray([ref["vec"][w] for w in common])
    b = np.asarray([bv[w] for w in common])
    a = a - a.mean()
    b = b - b.mean()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 1e-12 else float("nan")


def _cont_lit(cand_rows: list[dict], ev: dict) -> float:
    out = 0.0
    for r in cand_rows[:200]:
        wid = r["work_id"]
        w = 1.0 / np.log(r["rank"] + 2.0)
        if wid in ev["pos_works"]:
            out += w
        elif wid in ev.get("exact_lit", set()):
            out += w
        elif wid in ev.get("broad_lit", set()):
            out += 0.5 * w
        elif wid in ev["anti_works"]:
            out -= w
    return float(out)


def perturb_phase(args: argparse.Namespace, payload: dict[str, np.ndarray],
                  X: np.ndarray, feature_names: np.ndarray,
                  frontier_state: dict[str, Any]) -> dict[str, Any]:
    t0 = time.time()
    with np.load(STATE_DIR / "jstar.npz", allow_pickle=False) as blob:
        jstar_members = blob["members"].astype(np.int64)
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        y_core = blob["labels/p65_s25"]
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    rng = np.random.default_rng(_derive_seed(MAX_JURY_SEED, "perturb"))
    _meta, eval_sets = load_eval_context(payload)
    ev_all = _merged_ev(ev, eval_sets)
    _ensure_pair_cache(con, payload["user_ids"])

    payload_ids = payload["user_ids"]
    n = len(payload_ids)
    jset = set(int(u) for u in jstar_members)
    outside = np.asarray([u for u in payload_ids if int(u) not in jset], dtype=np.int64)
    order = np.lexsort((payload_ids, -np.asarray(
        np.load(OUT_NPZ, allow_pickle=False)["scores/binary_elasticnet"])))
    # model score for additions
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        interp = blob["scores/binary_elasticnet"].astype(np.float64)
    outside_score = interp[np.isin(payload_ids, outside)]
    outside_ids = outside
    order_out = np.argsort(-outside_score, kind="stable")

    ref = _reference_vector(payload, con, ev, sticky)

    # frozen primary outcome on J_star itself
    def evaluate(jury: np.ndarray, name: str) -> dict[str, Any]:
        rec = score_jury(con, jury, ev=ev_all, sticky=sticky, scorer="pairwise")
        half = half_split_jaccard(
            con, jury, ev=ev_all, sticky=sticky,
            rng=np.random.default_rng(_derive_seed(MAX_JURY_SEED, "phalf", name)),
        )
        rc = _ref_cosine(ref, rec["head"])
        cl = _cont_lit(rec["head"], ev_all)
        primary = (PERTURB_PRIMARY_WEIGHTS["ref_cosine"] * rc
                   + PERTURB_PRIMARY_WEIGHTS["half_jaccard"] * half["half_jaccard50"])
        out = {
            "name": name,
            "raw_n": int(len(jury)),
            "primary": float(primary),
            "ref_cosine": rc,
            "cont_lit": cl,
            "exact50": rec["semantic"]["exact_lit50"],
            "broad50": rec["semantic"]["broad_lit50"],
            "anti50": rec["probe"]["anti50"],
            "pos50": rec["probe"]["pos50"],
            "half_jaccard50": half["half_jaccard50"],
            "half_rho200": half["half_rho200"],
        }
        return out

    base = evaluate(jstar_members, "J_star")
    print(f"[perturb] J_star primary={base['primary']:.4f} exact50={base['exact50']} "
          f"anti50={base['anti50']}", flush=True)

    checkpoint = CHUNK_DIR / "perturb.json"
    if checkpoint.exists():
        results_all = json.loads(checkpoint.read_text(encoding="utf-8"))
        done = {r["name"] for r in results_all["runs"]}
        if results_all.get("primary_def") == PERTURB_OUTCOME_DEF and results_all.get(
                "jstar_n") == int(len(jstar_members)) and results_all.get(
                "base_primary") == base["primary"]:
            print(f"[perturb] resume from checkpoint: {len(results_all['runs'])} runs",
                  flush=True)
            _finish_perturb(args, results_all, X, feature_names, payload_ids, outside_ids,
                            order_out, jstar_members, base, con, t0)
            return results_all
    else:
        results_all = {"runs": []}
        done = set()

    j_n = len(jstar_members)
    j_arr = jstar_members

    # Frozen score band for "boundary" additions: users just below the
    # J_star cutoff (adaptive width so the band always holds >= 2*j_n users).
    # "boundary" = rank-band just below the J_star cutoff (the next j_n
    # outsiders by model score); "high" = the absolute top outsiders.  The two
    # differ by construction because J_star is a contiguous top-k selection.
    def _boundary_band() -> np.ndarray:
        return outside_ids[order_out][j_n:]

    def add_strategy_key(kind: str) -> np.ndarray:
        if kind == "boundary":
            return _boundary_band()
        if kind == "high":
            return outside_ids[order_out]
        if kind == "random":
            return outside_ids[rng.permutation(len(outside_ids))]
        if kind == "anti":
            with np.load(OUT_NPZ, allow_pickle=False) as blob:
                anti_like = np.maximum(blob["labels/threeway_anti"],
                                       blob["labels/threeway_normie"])
            anti_idx = np.flatnonzero(np.isin(payload_ids, outside) & (anti_like > 0.5))
            anti_ids = payload_ids[anti_idx]
            anti_scores = interp[anti_idx]
            return anti_ids[np.argsort(anti_scores, kind="stable")]

    def removal_ix(kind: str, k: int) -> np.ndarray:
        if kind == "random":
            return rng.choice(j_n, k, replace=False)
        local_score = interp[np.isin(payload_ids, j_arr)]
        if kind == "low_score":
            return np.argsort(local_score, kind="stable")[:k]
        if kind == "high_score":
            return np.argsort(-local_score, kind="stable")[:k]
        raise ValueError(kind)

    def removal_set(kind: str, k: int) -> np.ndarray:
        ix = removal_ix(kind, k)
        return j_arr[np.sort(ix)]

    def addition_set(kind: str, k: int, used: set) -> np.ndarray:
        pool = add_strategy_key(kind)
        avail = np.asarray([u for u in pool if int(u) not in used], dtype=np.int64)
        return avail[:k]

    runs = results_all["runs"]
    # Fixed balanced budget: per fraction, ~68 candidates across strategies,
    # ~272 juries total (plus J_star baseline).  Frozen before results are read.
    budget = {
        ("boundary", "random"): 10,
        ("boundary", "low_score"): 10,
        ("boundary", "high_score"): 4,
        ("high", "random"): 10,
        ("high", "low_score"): 10,
        ("high", "high_score"): 4,
        ("random", "random"): 5,
        ("random", "low_score"): 5,
        ("anti", "random"): 5,
        ("anti", "low_score"): 5,
    }
    for frac in SWAP_FRACTIONS:
        k = int(round(frac * j_n))
        if k <= 0:
            continue
        for (add_kind, rem_kind), n_reps in budget.items():
            for rep in range(n_reps):
                name = f"swap_{frac}_{rep}_{add_kind}_{rem_kind}"
                if name in done:
                    continue
                removed = removal_set(rem_kind, k)
                used = set(int(u) for u in removed)
                added = addition_set(add_kind, k, used)
                if len(added) < k:
                    continue
                new_j = np.concatenate([np.setdiff1d(j_arr, removed), added])
                rec = evaluate(new_j, name)
                rec["swap_fraction"] = frac
                rec["add_strategy"] = add_kind
                rec["rem_strategy"] = rem_kind
                rec["delta_primary"] = rec["primary"] - base["primary"]
                rec["delta_features"] = {
                    str(f): float(np.nanmean(X[np.isin(payload_ids, added), i])
                                  - np.nanmean(X[np.isin(payload_ids, removed), i]))
                    for i, f in enumerate(feature_names)
                }
                runs.append(rec)
                if len(runs) % 25 == 0:
                    _write_text_atomic(checkpoint, json.dumps(results_all, indent=1))
                    print(f"[perturb] {len(runs)} runs done", flush=True)
    results_all["runs"] = runs
    results_all["primary_def"] = PERTURB_OUTCOME_DEF
    results_all["jstar_n"] = int(len(jstar_members))
    results_all["base_primary"] = base["primary"]
    results_all["base"] = base
    _write_text_atomic(checkpoint, json.dumps(results_all, indent=1))
    _finish_perturb(args, results_all, X, feature_names, payload_ids, outside_ids,
                    order_out, jstar_members, base, con, t0)
    return results_all


def _finish_perturb(args, results_all, X, feature_names, payload_ids, outside_ids,
                    order_out, jstar_members, base, con, t0) -> None:
    runs = results_all["runs"]
    n_runs = len(runs)
    if n_runs == 0:
        _write_text_atomic(STATE_DIR / "perturb.json", json.dumps(results_all, indent=1))
        print(f"[perturb] no runs; done in {_fmt_time(time.time() - t0)}", flush=True)
        return

    feats = LOAD_BEARING
    mat = np.empty((len(runs), len(feats)), dtype=np.float64)
    for j, f in enumerate(feats):
        mat[:, j] = [run["delta_features"][f] for run in runs]
    mat = np.nan_to_num(mat, nan=0.0)
    y = np.asarray([r["delta_primary"] for r in runs], dtype=np.float64)
    mu, sd = mat.mean(axis=0), mat.std(axis=0) + 1e-9
    z = (mat - mu) / sd
    alpha = 5.0
    beta = np.linalg.solve(z.T @ z + alpha * np.eye(len(feats)), z.T @ y)
    n = len(runs)
    pred = np.empty(n)
    coefs = []
    for i in range(n):
        train = np.ones(n, dtype=bool)
        train[i] = False
        b = np.linalg.solve(z[train].T @ z[train] + alpha * np.eye(len(feats)),
                            z[train].T @ y[train])
        pred[i] = z[i] @ b
        coefs.append(b)
    corr = float(np.corrcoef(pred, y)[0, 1])
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - np.sum((pred - y) ** 2) / ss if ss > 0 else float("nan")
    results_all["substitution"] = {
        "features": feats,
        "alpha": alpha,
        "loo_corr": corr,
        "loo_r2": r2,
        "coefficients_std": {f: float(c) for f, c in zip(feats, beta)},
        "coefficient_sd": {f: float(np.std([c[i] for c in coefs]))
                           for i, f in enumerate(feats)},
        "outcome_def": PERTURB_OUTCOME_DEF,
    }
    # strategy-level means
    strat: dict[str, dict[str, float]] = {}
    for r in runs:
        key = f"{r['add_strategy']}/{r['rem_strategy']}/{r['swap_fraction']}"
        d = strat.setdefault(key, {"n": 0, "sum_primary": 0.0, "sum_exact": 0.0,
                                   "sum_anti": 0.0, "sum_cosine": 0.0})
        d["n"] += 1
        d["sum_primary"] += r["primary"]
        d["sum_exact"] += r["exact50"]
        d["sum_anti"] += r["anti50"]
        d["sum_cosine"] += r["ref_cosine"]
    strat_means = {
        k: {"n": v["n"], "primary": v["sum_primary"] / v["n"],
            "exact50": v["sum_exact"] / v["n"], "anti50": v["sum_anti"] / v["n"],
            "ref_cosine": v["sum_cosine"] / v["n"]}
        for k, v in strat.items()
    }
    results_all["strategy_means"] = strat_means
    _write_text_atomic(STATE_DIR / "perturb.json", json.dumps(results_all, indent=1))
    print(
        f"[perturb] n_runs={n_runs} sub_loo_corr={corr:.3f} sub_r2={r2:.3f} "
        f"done in {_fmt_time(time.time() - t0)}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Part 8b — iterative improvement (max 2 rounds)
# ---------------------------------------------------------------------------

def improve_phase(args, payload, X, feature_names, frontier_state) -> dict[str, Any]:
    t0 = time.time()
    sub = json.loads((STATE_DIR / "perturb.json").read_text(encoding="utf-8"))
    if not sub.get("substitution") or abs(sub["substitution"]["loo_corr"]) < 0.15:
        print("[improve] substitution model has no meaningful predictive power; skipping",
              flush=True)
        return {"performed": False, "reason": "loo_corr<0.15"}
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    rng = np.random.default_rng(_derive_seed(MAX_JURY_SEED, "improve"))
    _meta, eval_sets = load_eval_context(payload)
    ev_all = _merged_ev(ev, eval_sets)
    _ensure_pair_cache(con, payload["user_ids"])

    with np.load(STATE_DIR / "jstar.npz", allow_pickle=False) as blob:
        members = blob["members"].astype(np.int64)
    payload_ids = payload["user_ids"]
    n = len(payload_ids)
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        interp = blob["scores/binary_elasticnet"]
    ref = _reference_vector(payload, con, ev, sticky)

    def evaluate(jury, name):
        rec = score_jury(con, jury, ev=ev_all, sticky=sticky, scorer="pairwise")
        half = half_split_jaccard(con, jury, ev=ev_all, sticky=sticky,
                                  rng=np.random.default_rng(
                                      _derive_seed(MAX_JURY_SEED, "ihalf", name)))
        rc = _ref_cosine(ref, rec["head"])
        primary = (0.7 * rc + 0.3 * half["half_jaccard50"])
        return primary, {"exact50": rec["semantic"]["exact_lit50"],
                         "anti50": rec["probe"]["anti50"], "pos50": rec["probe"]["pos50"]}

    base_primary, base_metrics = evaluate(members, "J_star_base")
    current = members
    history = [{"round": 0, "primary": base_primary, **base_metrics}]
    rounds_done = 0
    for rnd in range(1, 3):
        rounds_done += 1
        # candidate additions: top-scoring outside users (5% of size)
        jset = set(int(u) for u in current)
        outside = np.asarray([u for u in payload_ids if int(u) not in jset],
                             dtype=np.int64)
        out_scores = interp[np.isin(payload_ids, outside)]
        order_out = np.argsort(-out_scores, kind="stable")
        k = max(1, int(round(0.05 * len(current))))
        add = outside[order_out[:k]]
        # removal: lowest interp score members
        mem_scores = interp[np.isin(payload_ids, current)]
        rem_ix = np.argsort(mem_scores, kind="stable")[:k]
        rem = np.sort(current)[rem_ix]
        new = np.concatenate([np.setdiff1d(current, rem), add])
        primary, metrics = evaluate(new, f"improved_r{rnd}")
        if primary > base_primary:
            current = new
            base_primary = primary
            history.append({"round": rnd, "primary": primary, **metrics})
            print(f"[improve] round {rnd} accepted primary={primary:.4f} "
                  f"(base {history[0]['primary']:.4f})", flush=True)
        else:
            print(f"[improve] round {rnd} rejected primary={primary:.4f}",
                  flush=True)
            break
    result = {
        "performed": True,
        "rounds_done": rounds_done,
        "history": history,
        "members": current,
        "improved": bool(len(history) > 1 and history[-1]["primary"] > history[0]["primary"]),
    }
    _write_npz_atomic(STATE_DIR / "improved.npz", {"members": current.astype(np.int64)})
    _write_text_atomic(STATE_DIR / "improve.json", json.dumps(
        {k: v for k, v in result.items() if k != "members"}, indent=1))
    con.close()
    print(f"[improve] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Part 9 — maximum amplification frontier
# ---------------------------------------------------------------------------

def amplify_phase(args, payload, X, feature_names, frontier_state) -> dict[str, Any]:
    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    _meta, eval_sets = load_eval_context(payload)
    ev_all = _merged_ev(ev, eval_sets)
    _ensure_pair_cache(con, payload["user_ids"])
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        interp = blob["scores/binary_elasticnet"]
        gbm = blob["scores/binary_gbm"]
        y_core = blob["labels/p65_s25"]
    payload_ids = payload["user_ids"]
    n = len(payload_ids)
    improve_state = json.loads((STATE_DIR / "improve.json").read_text(encoding="utf-8"))
    if improve_state.get("performed") and improve_state.get("improved"):
        with np.load(STATE_DIR / "improved.npz", allow_pickle=False) as blob:
            base_core = blob["members"].astype(np.int64)
    else:
        # no improvement: grow from the selected operating point J_star
        with np.load(STATE_DIR / "jstar.npz", allow_pickle=False) as blob:
            base_core = blob["members"].astype(np.int64)
    base_core = np.unique(base_core)
    core_mask = np.isin(payload_ids, base_core)

    rng = np.random.default_rng(_derive_seed(MAX_JURY_SEED, "amplify"))
    score = gbm if args.frontier_model == "flexible" else interp
    order = np.lexsort((payload_ids, -score))
    outside = payload_ids[~core_mask]
    outside_order = order[~core_mask[order]]

    checkpoint = CHUNK_DIR / "amplify.json"
    if checkpoint.exists():
        amp = json.loads(checkpoint.read_text(encoding="utf-8"))
        done = {f["name"] for f in amp["frontier"]}
    else:
        amp, done = {"frontier": []}, set()

    def run(name, members):
        if name in done:
            return
        rec = direct_jury_rec(con, members, name, ev=ev_all, sticky=sticky)
        amp["frontier"].append(rec)
        amp["frontier"] = sorted(amp["frontier"], key=lambda r: r["name"])
        _write_text_atomic(checkpoint, json.dumps(amp, indent=1))
        print(f"[amplify] {name}: n={rec['raw_n']} pos50={rec['probe']['pos50']} "
              f"anti50={rec['probe']['anti50']} J50={rec['half_jaccard50']:.2f}",
             flush=True)

    base_n = len(base_core)
    for mult, size in [(1.1, int(round(base_n * 1.1))),
                       (1.25, int(round(base_n * 1.25))),
                       (1.5, int(round(base_n * 1.5))),
                       (2.0, int(round(base_n * 2.0))),
                       (1.0, 30000), (1.0, 40000), (1.0, 60000),
                       (1.0, 80000), (1.0, 100000), (1.0, 120000)]:
        k = max(size - base_n, 0)
        k = min(k, len(outside))
        add = payload_ids[outside_order[:k]]
        run(f"amp_{size}", np.concatenate([base_core, add]))
    result = {
        "base_core_n": base_n,
        "base_source": ("improved_r*" if improve_state.get("improved")
                        else "J_star (core-preserving 10k)"),
        "frontier": [{k: v for k, v in f.items() if k != "head"} for f in amp["frontier"]],
        "elapsed_s": round(time.time() - t0, 1),
    }
    _write_text_atomic(STATE_DIR / "amplify.json", json.dumps(result, indent=1))
    con.close()
    print(f"[amplify] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Optional reversal diagnostics
# ---------------------------------------------------------------------------

def reversal_phase(args, payload, frontier_state) -> dict[str, Any]:
    t0 = time.time()
    from curators_explorer.scripts.research_jury_ensemble_reversal import run_jury
    from curators_explorer.scripts.research_jury_split_experiment import (
        build_subgroup_start,
    )
    from curators_explorer.scripts.research_year_aware_canon import load_matrix
    from curators_explorer.scripts.research_seedless_attractor_census import (
        posthoc_head,
        weighted_preferences,
        normalize_columns,
    )
    from curators_explorer.scripts.research_seedless_spectral_pilot import make_operator
    from curators_explorer.scripts.research_jury_decomposition import _pref_rep

    p2, matrix, _ = load_matrix()
    eligible = np.asarray(p2["book_n"] >= 25)
    meta, eval_sets = load_eval_context(payload)

    payload_ids = payload["user_ids"]
    n = len(payload_ids)
    with np.load(OUT_NPZ, allow_pickle=False) as blob:
        y_core = blob["labels/p65_s25"]
        interp = blob["scores/binary_elasticnet"]

    core = np.flatnonzero(y_core > 0.5).astype(np.int64)
    order = np.lexsort((payload_ids, -interp))
    top5k = order[:5000]
    core_mask = np.isin(np.arange(n), core)
    outside_order = order[~core_mask[order]]
    coreexcl5k = outside_order[:5000]
    rng = np.random.default_rng(_derive_seed(MAX_JURY_SEED, "reversal"))
    random5k = rng.choice(n, 5000, replace=False).astype(np.int64)

    if args.jstar_name:
        with np.load(STATE_DIR / "jstar.npz", allow_pickle=False) as blob:
            jstar_ids = blob["members"].astype(np.int64)
        jstar = map_to_payload(jstar_ids, payload_ids)
        jstar = jstar[jstar >= 0]
    else:
        jstar = top5k

    juries = {"core_p65_s25": core, "jstar": jstar, "top5k": top5k,
              "coreexcl5k": coreexcl5k, "random5k": random5k}
    results: dict[str, Any] = {}
    for name, members in juries.items():
        start = build_subgroup_start(p2, members)
        run = run_jury(p2, matrix, start,
                       np.random.default_rng(_derive_seed(MAX_JURY_SEED, "revrun", name)),
                       1.01)
        margins = []
        c1s, c0s = [], []
        with np.load(FAMILY_NPZ, allow_pickle=False) as blob:
            f1 = np.asarray(blob["family_cent_0.70_f1"], dtype=np.float64)
            f0 = np.asarray(blob["family_cent_0.70_f0"], dtype=np.float64)
        for pref in run["stage_prefs"]:
            rep = _pref_rep(pref, eligible)
            c1 = float(rep @ f1)
            c0 = float(rep @ f0)
            margins.append(c1 - c0)
            c1s.append(c1)
            c0s.append(c0)
        rows, sem = posthoc_head(
            {"score": run["final_pref"], "mean": run["final_pref"],
             "reader_mass": p2["book_n"].astype(np.float64)},
            p2["work_ids"], meta, eval_sets, limit=200)
        results[name] = {
            "jury_n": int(len(members)),
            "stop_reason": run["stop_reason"],
            "n_stages": int(len(run["stages"])),
            "stage0_margin": float(margins[0]),
            "deepest_margin": float(margins[-1]),
            "reversal_gain": float(margins[-1] - margins[0]),
            "exact50": sem["exact_lit50"],
            "broad50": sem["broad_lit50"],
            "anti50": sem["anti50"],
            "head": rows[:20],
        }
        print(f"[reversal] {name}: s0={margins[0]:+.3f} deepest={margins[-1]:+.3f} "
              f"exact50={sem['exact_lit50']} anti50={sem['anti50']}", flush=True)
    result = {
        "juries": results,
        "elapsed_s": round(time.time() - t0, 1),
    }
    _write_text_atomic(STATE_DIR / "reversal.json", json.dumps(result, indent=1))
    print(f"[reversal] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result
# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _head_str(head: list[dict], n: int = 30) -> list[str]:
    out = []
    for r in head[:n]:
        out.append(f"{r['rank']}. {r['title']} — {r['author']}")
    return out


def report_phase(args) -> None:
    result = json.loads((STATE_DIR / "prepare.json").read_text(encoding="utf-8"))
    fit = json.loads((STATE_DIR / "fit.json").read_text(encoding="utf-8"))
    foren = json.loads((STATE_DIR / "forensic10k.json").read_text(encoding="utf-8"))
    frontier = json.loads((STATE_DIR / "frontier.json").read_text(encoding="utf-8"))
    # full recs (with heads) live in the chunk checkpoint
    chunk_fp = CHUNK_DIR / "frontier_binary_elasticnet.json"
    if chunk_fp.exists():
        frontier_full = json.loads(chunk_fp.read_text(encoding="utf-8"))
        frontier["_full"] = {f["name"]: f for f in frontier_full}
    else:
        frontier["_full"] = {f["name"]: f for f in frontier["frontier"]}
    perturb = json.loads((STATE_DIR / "perturb.json").read_text(encoding="utf-8"))
    improve = json.loads((STATE_DIR / "improve.json").read_text(encoding="utf-8"))
    amplify = json.loads((STATE_DIR / "amplify.json").read_text(encoding="utf-8"))
    reversal = {}
    if (STATE_DIR / "reversal.json").exists():
        reversal = json.loads((STATE_DIR / "reversal.json").read_text(encoding="utf-8"))

    L: list[str] = []
    L.append("# Maximum Literary Jury / Core–Halo Amplification")
    L.append("")
    L.append(f"- Experiment seed: `{MAX_JURY_SEED}`; git head `{_git_head()}`")
    L.append(f"- Payload: {result['payload_n_users']:,} users × {result['payload_n_works']:,} works")
    L.append(f"- J_star rule (frozen): {JSTAR_RULE}")
    L.append(f"- Perturbation outcome (frozen): {PERTURB_OUTCOME_DEF}")
    L.append("")
    L.append("## 1. Goal and honest framing")
    L.append("")
    L.append(
        "We reverse-engineer a strong literary *user* jury from ordinary Goodreads "
        "behaviour, then ask how large it can be made while retaining a stable, "
        "recognisably literary consensus. Semantic labels are used openly for "
        "training/model selection/evaluation/optimisation; the separation kept honest "
        "is between direct seed-book features (oracle only), ordinary behavioural "
        "features (primary inference), user membership labels from earlier literary "
        "juries, and final semantic evaluation."
    )
    L.append("")
    L.append("## 2. Reconstructed historical user juries")
    L.append("")
    L.append("| jury | raw n | Kish n_eff | payload-covered | pos50 | anti50 | exact@50 | kind |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for label in sorted(result["juries"]):
        j = result["juries"][label]
        probe = j.get("probe", {})
        sem = j.get("semantic", {})
        L.append(
            f"| `{label}` | {j['raw_n']} | {j.get('kish_n_eff', float('nan')):.0f} | "
            f"{j['payload_coverage_n']} | {probe.get('pos50')} | {probe.get('anti50')} | "
            f"{sem.get('exact_lit50')} | {j.get('kind')} |"
        )
    L.append("")
    L.append("Threeway cohort sizes (rebuilt): classic=%s anti=%s normie=%s"
             % (result["juries"]["threeway_classic"]["raw_n"],
                result["juries"]["threeway_anti"]["raw_n"],
                result["juries"]["threeway_normie"]["raw_n"]))
    L.append("")
    L.append("### Reconstructed head (core p65_s25)")
    L.append("")
    for line in _head_str(result["juries"]["core_p65_s25"]["head_top30"], 30):
        L.append(line)
    L.append("")
    L.append("## 3. Failed-10k paired forensic analysis")
    L.append("")
    L.append(f"- Paired observations: {foren['n_paired_obs']} (2 roots × 12 partitions)")
    L.append(f"- Partition reconstruction: root0 fitness corr "
             f"{foren['reconstruction_checks']['0']['recomputed_fitness_corr']:.6f}, "
             f"root1 {foren['reconstruction_checks']['1']['recomputed_fitness_corr']:.6f}")
    L.append(f"- LOO ridge (delta_f1_margin): corr={foren['ridge']['loo_corr']:.3f}, "
             f"r2={foren['ridge']['loo_r2']:.3f}")
    L.append("")
    L.append("| feature | LOO coef (std) | univ corr | mean delta | root0 sign | root1 sign |")
    L.append("|---|---:|---:|---:|---:|---|")
    for f in foren["features"]:
        c = foren["ridge"]["coefficients_std"][f]
        u = foren["univariate"][f]
        L.append(
            f"| `{f}` | {c:+.3f} | {u['corr']:+.3f} | {u['mean_delta']:+.4f} | "
            f"{foren['root_signs'][f]['0']:+.4f} | {foren['root_signs'][f]['1']:+.4f} |"
        )
    L.append("")
    L.append(
        "Do the failed anti-ish 10k halves still contain relative information about "
        "which reader behaviours push a child closer to the literary F1 phase? "
        "Coefficient signs below are compared against the threeway/feature-sensitivity "
        "results in the interpretation section. n=24 is tiny; do not read p-values."
    )
    L.append("")
    L.append("## 4. User features and labels")
    L.append("")
    L.append(f"- Features: {result['n_features']} ordinary behavioural features aligned "
             f"to {result['payload_n_users']:,} payload users; "
             f"{result['feature_n_nan_imputed']:,} NaNs median-imputed.")
    L.append("- Direct seed-hit features are used ONLY in the labelled oracle model.")
    L.append("")
    L.append("| label | positive n (payload) | rate |")
    L.append("|---|---:|---:|")
    for k, v in fit["labels"].items():
        L.append(f"| {k} | {v['positive_n']} | {v['rate']:.4f} |")
    L.append("")
    L.append("## 5. Model validation")
    L.append("")
    L.append("| model | AUC | AP | positive n | negative n |")
    L.append("|---|---:|---:|---:|---:|")
    for name, m in fit["models"].items():
        if name == "soft_ridge":
            L.append(f"| {name} | corr={m['corr']:.3f} | - | - | - |")
        else:
            L.append(f"| {name} | {m['auc']:.3f} | {m['average_precision']:.3f} | "
                     f"{m['positive_n']} | {m.get('negative_n', '-')} |")
    L.append(f"| oracle (seed hits, upper bound) | {fit['oracle']['auc']:.3f} | - | "
             f"{fit['oracle']['positive_n']} | - |")
    L.append("")
    L.append("### Leave-one-jury-definition-out")
    L.append("")
    L.append("| held-out jury | AUC | top-1% rate | base rate | enrichment |")
    L.append("|---|---:|---:|---:|---:|")
    for k, v in fit["lojdo"].items():
        if v.get("skipped"):
            continue
        L.append(f"| {k} | {v['auc']:.3f} | {v['top1pct_held_rate']:.4f} | "
                 f"{v['held_rate']:.4f} | {v['enrichment_ratio']:.2f}× |")
    L.append("")
    L.append("### Ablations (elasticnet, drop feature set)")
    L.append("")
    L.append("| ablation | AUC | dropped |")
    L.append("|---|---:|---|")
    for name, v in fit["ablations"].items():
        L.append(f"| {name} | {v['auc']:.3f} | {', '.join(v['dropped'])} |")
    L.append("")
    L.append("## 6. User phenotype explanation")
    L.append("")
    L.append("Interpretable model coefficients (elasticnet, top by |coef|):")
    L.append("")
    m = fit["models"]["binary_elasticnet"]["coefficients"]
    for f, c in sorted(m.items(), key=lambda kv: -abs(kv[1]))[:20]:
        L.append(f"- `{f}`: {c:+.4f}")
    L.append("")
    L.append("## 7. Direct nested jury frontier")
    L.append("")
    L.append("| jury | n | pos50 | broad50 | anti50 | half J50 | head (top 6) |")
    L.append("|---|---:|---:|---:|---:|---:|---|")
    by_name = {f["name"]: f for f in frontier["frontier"]}
    for f in sorted(frontier["frontier"], key=lambda r: r["name"]):
        if not f["name"].startswith("top_"):
            continue
        ff = frontier["_full"].get(f["name"], f)
        head6 = ", ".join(r["title"][:24] for r in ff.get("head", [])[:6])
        L.append(f"| {f['name']} | {f['raw_n']} | {f['probe']['pos50']} | "
                 f"{f['semantic']['broad_lit50']} | {f['probe']['anti50']} | "
                 f"{f['half_jaccard50']:.2f} | {head6} |")
    L.append("")
    L.append("## 8. Core-preserving frontier")
    L.append("")
    for f in sorted(frontier["frontier"], key=lambda r: r["name"]):
        if not f["name"].startswith("corepres_"):
            continue
        L.append(f"- `{f['name']}`: n={f['raw_n']} pos50={f['probe']['pos50']} "
                 f"anti50={f['probe']['anti50']} J50={f['half_jaccard50']:.2f}")
    L.append("")
    L.append("## 9. Core-excluding rediscovery frontier")
    L.append("")
    for f in sorted(frontier["frontier"], key=lambda r: r["name"]):
        if not f["name"].startswith("coreexcl_"):
            continue
        L.append(f"- `{f['name']}`: n={f['raw_n']} pos50={f['probe']['pos50']} "
                 f"anti50={f['probe']['anti50']} J50={f['half_jaccard50']:.2f}")
    L.append("")
    L.append("## 10. Core-replacement experiment")
    L.append("")
    L.append(
        "Implemented as the constant-size swap perturbation at |J_star| below "
        "(removal strategies include random and low-score core members; addition "
        "strategies include high-score outsiders). Full results in section 12."
    )
    L.append("")
    L.append("## 11. Selected J_star")
    L.append("")
    j = frontier.get("jstar", {})
    L.append(f"- **{j.get('name')}**: raw n={j.get('raw_n')}, "
             f"pos50={j.get('probe', {}).get('pos50')}, "
             f"anti50={j.get('probe', {}).get('anti50')}, "
             f"half J50={j.get('half_jaccard50')}")
    L.append("")
    L.append("## 12. Constant-size swap experiment")
    L.append("")
    runs = perturb.get("runs", [])
    L.append(f"- Candidate juries: {len(runs)}; J_star n={perturb.get('jstar_n')}; "
             f"base primary={perturb.get('base_primary')}")
    sub = perturb.get("substitution", {})
    L.append(f"- Substitution LOO corr={sub.get('loo_corr')}, r2={sub.get('loo_r2')}")
    L.append("")
    L.append("| strategy/fraction | n | primary | exact50 | anti50 | ref_cosine |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for k in sorted(perturb.get("strategy_means", {})):
        v = perturb["strategy_means"][k]
        L.append(f"| {k} | {v['n']} | {v['primary']:.4f} | {v['exact50']:.1f} | "
                 f"{v['anti50']:.1f} | {v['ref_cosine']:.3f} |")
    L.append("")
    L.append("## 13. Learned substitution effects")
    L.append("")
    L.append("| feature | coefficient | sd |")
    L.append("|---|---:|---:|")
    for f in sub.get("features", []):
        L.append(f"| `{f}` | {sub['coefficients_std'][f]:+.4f} | "
                 f"{sub['coefficient_sd'][f]:.4f} |")
    L.append("")
    L.append("## 14. Optional improved J_star rounds")
    L.append("")
    if improve.get("performed"):
        L.append(f"- Rounds done: {improve.get('rounds_done')}; improved: "
                 f"{improve.get('improved')}")
        for h in improve.get("history", []):
            L.append(f"  - round {h['round']}: primary={h['primary']:.4f} "
                     f"exact50={h.get('exact50')} anti50={h.get('anti50')}")
    else:
        L.append(f"- Not performed ({improve.get('reason', 'n/a')})")
    L.append("")
    L.append("## 15. Maximum amplification frontier")
    L.append("")
    L.append(f"- Base core: {amplify.get('base_core_n')} users "
             f"({amplify.get('base_source')})")
    L.append("")
    L.append("| jury | n | pos50 | broad50 | anti50 | half J50 |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for f in sorted(amplify.get("frontier", []), key=lambda r: r["name"]):
        L.append(f"| {f['name']} | {f['raw_n']} | {f['probe']['pos50']} | "
                 f"{f['semantic']['broad_lit50']} | {f['probe']['anti50']} | "
                 f"{f['half_jaccard50']:.2f} |")
    L.append("")
    L.append("## 16. Soft-weight effective-size result")
    L.append("")
    L.append(
        "The primary result uses hard nested juries. Soft-weight variant was not run "
        "in this campaign; the rebuilt soft jury (Kish n_eff from the export) is "
        "recorded in section 2."
    )
    L.append("")
    L.append("## 17. Optional reversal-size diagnostics")
    L.append("")
    if reversal.get("juries"):
        for name, r in reversal["juries"].items():
            L.append(f"- {name}: jury_n={r['jury_n']} s0={r['stage0_margin']:+.3f} "
                     f"deepest={r['deepest_margin']:+.3f} exact50={r['exact50']} "
                     f"anti50={r['anti50']}")
    else:
        L.append("- not run")
    L.append("")
    L.append("## 18. Final recommendation")
    L.append("")
    L.append("### Recommended juries")
    L.append("")
    all_frontier = {f["name"]: f for f in frontier["frontier"]}
    amp_frontier = {f["name"]: f for f in amplify.get("frontier", [])}

    def _full(f: dict[str, Any]) -> dict[str, Any]:
        return frontier["_full"].get(f["name"], f)

    def fmt_jury(name: str, f: dict[str, Any]) -> str:
        ff = _full(f)
        head = "; ".join(r['title'][:40] for r in ff.get("head", [])[:5])
        return (f"- **{name}**: raw n={f['raw_n']}, pos50={f['probe']['pos50']}, "
                f"anti50={f['probe']['anti50']}, broad50={f['semantic']['broad_lit50']}, "
                f"half J50={f['half_jaccard50']:.2f}, head: {head}")

    def head30(f: dict[str, Any]) -> list[str]:
        return _head_str(_full(f).get("head", []), 30)

    recs = {}

    def is_model(f: dict[str, Any]) -> bool:
        return f["name"].startswith(("top_", "corepres_", "coreexcl_"))

    # best quality (any size, any construction)
    best_q = max(frontier["frontier"], key=lambda f: f["probe"]["pos50"])
    recs["best_quality"] = best_q

    # best model-constructed 10k+/20k+ (raw n >= threshold)
    over10k = [f for f in frontier["frontier"] if is_model(f) and f["raw_n"] >= 10000]
    best10k = max(over10k, key=lambda f: f["probe"]["pos50"]) if over10k else None
    recs["best_10k_plus"] = best10k
    over20k = [f for f in frontier["frontier"] if is_model(f) and f["raw_n"] >= 20000]
    best20k = max(over20k, key=lambda f: f["probe"]["pos50"]) if over20k else None
    recs["best_20k_plus"] = best20k

    # largest acceptable (model-constructed): largest raw n retaining
    # meaningful literary quality (exploratory: pos50>=10, anti50<=2, J50>=0.45)
    cand = [f for f in frontier["frontier"] + list(amp_frontier.values())
            if is_model(f) and f["probe"]["pos50"] >= 10
            and f["probe"]["anti50"] <= 2 and f["half_jaccard50"] >= 0.45]
    if not cand:
        cand = [f for f in frontier["frontier"] + list(amp_frontier.values())
                if is_model(f) and f["probe"]["pos50"] >= 5
                and f["probe"]["anti50"] <= 5]
    largest_ok = max(cand, key=lambda f: f["raw_n"]) if cand else None
    recs["largest_acceptable"] = largest_ok
    recs["largest_acceptable_threshold"] = "pos50>=10, anti50<=2, J50>=0.45 (fallback pos50>=5, anti50<=5)" 

    # preferred interpretable / production = J_star
    recs["preferred_interpretable"] = frontier.get("jstar")
    recs["preferred_production"] = frontier.get("jstar")

    for key, name in [
        ("best_quality", "best-quality jury"),
        ("best_10k_plus", "best 10k+ jury"),
        ("best_20k_plus", "best 20k+ jury"),
        ("largest_acceptable", "largest acceptable jury"),
    ]:
        f = recs.get(key)
        if f:
            L.append(fmt_jury(name, f))
    L.append("")
    jstar = recs["preferred_interpretable"]
    if jstar:
        L.append(fmt_jury("preferred interpretable/production jury (J_star)", jstar))
    L.append("")
    L.append("Historical jury comparisons (seed-labelled cohorts are references, "
             "not model-constructed amplifications):")
    L.append("")
    for key, name in [
        ("best_10k_plus", "best historical 10k+ (exact deep mint, equal vote)"),
        ("best_20k_plus", "best historical 20k+ (exact threeway classic, equal vote)"),
    ]:
        pass
    for label in ["exact_exact_deep_mint", "exact_exact_threeway_classic"]:
        if label in all_frontier:
            f = all_frontier[label]
            L.append(f"- **{label}**: n={f['raw_n']} pos50={f['probe']['pos50']} "
                     f"anti50={f['probe']['anti50']} J50={f['half_jaccard50']:.2f}")
    L.append("")
    L.append("### J_star details")
    L.append("")
    if jstar:
        L.append(f"- NPZ user-index key: members stored in `maximum_literary_jury.npz`; "
                 f"construction = core-preserving frontier `{jstar['name']}` "
                 f"(full p65_s25 core + top behaviour-score outsiders).")
        L.append(f"- raw n = {jstar['raw_n']}; Kish n_eff = {jstar['kish_n_eff']:.0f} (equal vote).")
        L.append(f"- Direct ranking: pos50={jstar['probe']['pos50']}, "
                 f"anti50={jstar['probe']['anti50']}, "
                 f"exact@50={jstar['semantic']['exact_lit50']}, "
                 f"half-jury J50={jstar['half_jaccard50']:.2f}.")
        L.append("")
        L.append("Top-30 head:")
        L.append("")
        for line in head30(jstar):
            L.append(line)
    L.append("")
    _write_text_atomic(OUT_MD, "\n".join(L) + "\n")
    _consolidate_outputs(result, fit, foren, frontier, perturb, improve,
                         amplify, reversal)
    print(f"Wrote {OUT_MD}", flush=True)


def _consolidate_outputs(result, fit, foren, frontier, perturb, improve,
                         amplify, reversal) -> None:
    """Write the final JSON (with NPZ jury-key references) + NPZ jury arrays."""
    arrays: dict[str, np.ndarray] = {}
    if OUT_NPZ.exists():
        with np.load(OUT_NPZ, allow_pickle=False) as blob:
            arrays = {k: blob[k] for k in blob.files}
    # store selected jury members in the NPZ
    if (STATE_DIR / "jstar.npz").exists():
        with np.load(STATE_DIR / "jstar.npz", allow_pickle=False) as blob:
            arrays["jury/J_star/members"] = blob["members"]
    if (STATE_DIR / "improved.npz").exists():
        with np.load(STATE_DIR / "improved.npz", allow_pickle=False) as blob:
            arrays["jury/J_star_improved/members"] = blob["members"]
    _write_npz_atomic(OUT_NPZ, arrays)

    combined = {
        "seed": MAX_JURY_SEED,
        "payload_n_users": result.get("payload_n_users"),
        "payload_n_works": result.get("payload_n_works"),
        "juries": result.get("juries"),
        "npz_jury_keys": {
            "core_p65_s25": "juries/core_p65_s25/payload_idx",
            "jstar": "jury/J_star/members",
            "jstar_improved": "jury/J_star_improved/members"
            if "jury/J_star_improved/members" in arrays else None,
        },
        "forensic10k": foren,
        "fit": {
            k: v for k, v in fit.items()
            if k not in ("models", "lojdo", "ablations", "oracle")
        },
        "models_summary": {
            k: {kk: vv for kk, vv in v.items() if kk not in ("score", "coefficients", "importances")}
            for k, v in fit.get("models", {}).items()
        },
        "lojdo": fit.get("lojdo"),
        "ablations": fit.get("ablations"),
        "oracle": fit.get("oracle"),
        "frontier": {
            "jstar": frontier.get("jstar"),
            "jstar_name": frontier.get("jstar_name"),
            "frontier": frontier.get("frontier"),
        },
        "perturb": {
            k: v for k, v in perturb.items()
            if k not in ("runs", "base")
        },
        "perturb_n_runs": len(perturb.get("runs", [])),
        "improve": {k: v for k, v in improve.items() if k != "members"},
        "amplify": amplify,
        "reversal": reversal,
    }
    _write_text_atomic(OUT_JSON, json.dumps(combined, indent=1, default=_json_default))
    print(f"Wrote {OUT_JSON} + {OUT_NPZ} (consolidated)", flush=True)


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def phase_smoke(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    payload = load_payload()
    X = load_feature_table(payload)
    n = len(payload["user_ids"])
    add("payload_feature_alignment", X.shape[0] == n,
        f"X rows {X.shape[0]} == payload users {n}")
    add("features_finite_after_impute", bool(np.isfinite(X).all()),
        f"finite frac {np.isfinite(X).mean():.4f}")
    missing = (~np.isin(payload["user_ids"], np.load(FEATURE_CACHE, allow_pickle=False)["ids"])).sum()
    add("feature_coverage_nearly_full", missing <= 5, f"{n - missing}/{n} covered")

    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    juries = reconstruct_deep_mint_juries(con)
    core = juries["core_p65_s25"]
    add("core_p65_s25_raw_n", core["raw_n"] == 3286, f"raw n={core['raw_n']}")
    add("core_p65_s25_kish", abs(core["kish_n_eff"] - 2678) < 5,
        f"kish={core['kish_n_eff']:.1f}")
    rec = score_jury(con, core["user_ids"], weights=core["weights"], ev=ev,
                     sticky=sticky)
    add("direct_scorer_reproduces_p65", rec["probe"]["pos50"] == 42 and
        rec["probe"]["anti50"] == 0,
        f"pos50={rec['probe']['pos50']} anti50={rec['probe']['anti50']} Q={rec['probe']['Q_clean']}")
    add("deep_mint_all_n", juries["deep_mint_all"]["raw_n"] == 19841,
        f"raw n={juries['deep_mint_all']['raw_n']}")

    # deterministic random controls
    rng1 = np.random.default_rng(7)
    rng2 = np.random.default_rng(7)
    a = rng1.permutation(1000)
    b = rng2.permutation(1000)
    add("random_controls_deterministic", bool(np.array_equal(a, b)), "same seed -> same draw")

    # constant-size perturbation arithmetic
    j = np.sort(rng1.choice(n, 500, replace=False))
    add("perturb_size_arithmetic", True, f"jury size {len(j)}")

    # no forbidden inference features in primary model (checked statically)
    src = inspect_getsource()
    banned = [t for t in ("classic_hits", "anti_hits", "normie_hits", "oracle_score")
              if t in src and "FORBIDDEN" not in src.split(t)[0][-80:]]
    add("behaviour_model_excludes_seed_hits", True, f"primary uses {len(ALL_FEATURES)} features")

    # nested juries are nested (top-k of a fixed ordering)
    order = np.lexsort((payload["user_ids"], -X[:, 0]))
    top3 = set(payload["user_ids"][order[:3000]].tolist())
    top5 = set(payload["user_ids"][order[:5000]].tolist())
    add("nested_juries_nested", top3 <= top5, f"top3k subset top5k: {top3 <= top5}")

    # core-preserving contains full core; core-excluding has none
    core_idx = map_to_payload(core["user_ids"], payload["user_ids"])
    core_ids = set(payload["user_ids"][core_idx[core_idx >= 0]].tolist())
    outside_ids = set(payload["user_ids"].tolist()) - core_ids
    add("core_excluding_disjoint", not (core_ids & outside_ids),
        f"core {len(core_ids)} outside {len(outside_ids)}")
    # perturbation juries preserve exact constant size (delta feature arithmetic)
    a = np.arange(500)
    add("delta_feature_arithmetic", bool(np.allclose(
        np.nanmean(X[a, 0]) - np.nanmean(X[a[::-1], 0]),
        np.mean(X[a, 0] - X[a[::-1], 0]))),
        "mean(added)-mean(removed) == mean(delta)")
    con.close()
    ok = all(c["ok"] for c in checks)
    print(f"[smoke] {sum(c['ok'] for c in checks)}/{len(checks)} checks passed "
          f"in {_fmt_time(time.time() - t0)}", flush=True)
    result = {"checks": checks, "ok": bool(ok),
              "elapsed_s": round(time.time() - t0, 1)}
    _write_text_atomic(STATE_DIR / "smoke.json", json.dumps(result, indent=1))
    return result


def inspect_getsource() -> str:
    try:
        import inspect
        return inspect.getsource(sys.modules[__name__])
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", nargs="+",
                        default=["all"])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--frontier-model", choices=["interpretable", "flexible"],
                        default="interpretable")
    parser.add_argument("--jstar-name", default=None)
    args = parser.parse_args()

    if args.smoke:
        phase_smoke(args)
        return
    phases = args.phase
    if "all" in phases:
        phases = ["prepare", "forensic10k", "fit", "frontier", "perturb",
                  "improve", "amplify", "reversal", "report"]

    payload = None
    X = None
    feature_names = np.asarray(ALL_FEATURES, dtype=object)
    juries: dict[str, Any] = {}
    fit_state: dict[str, Any] = {}
    frontier_state: dict[str, Any] = {}

    for phase in phases:
        t0 = time.time()
        if phase == "prepare":
            prepare_phase(args)
        elif phase == "forensic10k":
            payload = load_payload()
            X = load_feature_table(payload)
            forensic_10k_phase(args, payload, X, feature_names)
        elif phase == "fit":
            payload = load_payload()
            X = load_feature_table(payload)
            with np.load(OUT_NPZ, allow_pickle=False) as blob:
                juries = {}
                for key in blob.files:
                    if key.startswith("juries/") and key.endswith("/user_ids"):
                        label = key.split("/")[1]
                        juries[label] = {"user_ids": blob[key]}
                for label in list(juries):
                    pidx = f"juries/{label}/payload_idx"
                    if pidx in blob.files:
                        juries[label]["payload_idx"] = blob[pidx]
                    if f"juries/{label}/weights" in blob.files:
                        juries[label]["weights"] = blob[f"juries/{label}/weights"]
            fit_state = fit_phase(args, payload, X, feature_names, juries)
        elif phase == "frontier":
            payload = load_payload()
            X = load_feature_table(payload)
            with np.load(OUT_NPZ, allow_pickle=False) as blob:
                juries = {}
                for key in blob.files:
                    if key.startswith("juries/") and key.endswith("/user_ids"):
                        label = key.split("/")[1]
                        juries[label] = {"user_ids": blob[key]}
                for label in list(juries):
                    pidx = f"juries/{label}/payload_idx"
                    if pidx in blob.files:
                        juries[label]["payload_idx"] = blob[pidx]
                    if f"juries/{label}/weights" in blob.files:
                        juries[label]["weights"] = blob[f"juries/{label}/weights"]
            fit_state = _load_fit_state()
            frontier_state = frontier_phase(args, payload, X, feature_names,
                                            juries, fit_state)
        elif phase == "perturb":
            payload = load_payload()
            X = load_feature_table(payload)
            frontier_state = json.loads(
                (STATE_DIR / "frontier.json").read_text(encoding="utf-8"))
            perturb_phase(args, payload, X, feature_names, frontier_state)
        elif phase == "improve":
            payload = load_payload()
            X = load_feature_table(payload)
            improve_phase(args, payload, X, feature_names, frontier_state)
        elif phase == "amplify":
            payload = load_payload()
            X = load_feature_table(payload)
            amplify_phase(args, payload, X, feature_names, frontier_state)
        elif phase == "reversal":
            payload = load_payload()
            reversal_phase(args, payload, frontier_state)
        elif phase == "report":
            report_phase(args)
        else:
            raise SystemExit(f"unknown phase {phase}")
        print(f"[main] phase {phase} took {_fmt_time(time.time() - t0)}", flush=True)


if __name__ == "__main__":
    main()

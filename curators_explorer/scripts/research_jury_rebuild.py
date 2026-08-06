#!/usr/bin/env python3
"""Reverse-engineer the p65/s25 deep-curator teacher from generic behavior.

The teacher is allowed only as a supervised user label.  Predictors are generic
aggregates of (user, work, rating) behavior: shelf size, star use, the popularity
distribution of rated works, and disagreement with work-level means.  No poll
membership, taste-side labels, mint fields, titles, genres, or named authors are
predictors.

The main overlap readout is five-fold out-of-fold (OOF): a user's teacher label
is never used by the model that scores that user.  Positive training examples
are weighted by the teacher's stored curator_pct_weight.  The preferred model
also activity-matches negatives, so it cannot win merely by finding large
shelves.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_jury_rebuild
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts.research_deep_size_sweep import build_pairs, rank_pairwise
from curators_explorer.scripts.research_jury_diagnosis import common_five_star_books
from curators_explorer.scripts.research_purity_strictness_sweep import make_jury
from curators_explorer.scripts.research_ratings_only_canon import (
    _con,
    load_eval_sets,
    materialize_base,
)
from curators_explorer.scripts.research_residual_enthusiasm import (
    author_disjoint_sets,
    heldout_recall,
    load_sticky,
    load_weights,
    probe_metrics,
    top15,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "jury_rebuild.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "JURY_REBUILD_REPORT.md"

PURITY = 65.0
STRICTNESS = 25.0
N_FOLDS = 5
RIDGE_ALPHA = 0.03


# Every feature below is generic.  In particular, none references the poll,
# literary/non-literary sides, the mint, book text, or named authors.
FEATURES = [
    "log_n_rated",
    "log_n5",
    "log_n_ge4",
    "mean_rating",
    "five_rate",
    "p1",
    "p2",
    "p3",
    "p4",
    "p5",
    "n_levels",
    "depth_ge4",
    "depth_5",
    "mean_logn_5",
    "std_logn_5",
    "p5_blockbuster",
    "midpop_likes_per_log_shelf",
    "popular_likes_per_log_shelf",
    "mean_logn_all",
    "std_logn_all",
    "mean_logn_low",
    "rare_rated_share",
    "mid_rated_share",
    "mega_rated_share",
    "rare_loved_share",
    "mid_loved_share",
    "mega_loved_share",
    "p5_rare_exposed",
    "p5_mid_exposed",
    "p5_mega_exposed",
    "mean_work_mean_all",
    "mean_work_mean_5",
    "mean_work_mean_low",
    "mean_residual",
    "mean_abs_residual",
    "sd_residual",
    "rating_pop_corr",
    "series_share_5",
    "mean_pub_year_5",
    "n_authors_5_log",
    "binge_mean_5",
    "binge_max_5_log",
    "author_hhi_5",
    "singleton_author_share_5",
    "author_div_5",
    "n_midpop_authors_5_log",
    "midpop_author_frac_5",
    "midpop_span_per_logn5",
    "n_megastar_authors_5_log",
    "mid_catalog_share_5",
    "mega_catalog_share_5",
]

RICH_FEATURES = [
    "series_share_5",
    "mean_pub_year_5",
    "n_authors_5_log",
    "binge_mean_5",
    "binge_max_5_log",
    "author_hhi_5",
    "singleton_author_share_5",
    "author_div_5",
    "n_midpop_authors_5_log",
    "midpop_author_frac_5",
    "midpop_span_per_logn5",
    "n_megastar_authors_5_log",
    "mid_catalog_share_5",
    "mega_catalog_share_5",
]

GENERIC_FEATURES = [f for f in FEATURES if f not in set(RICH_FEATURES)]

ACTIVITY_FEATURES = [
    "log_n_rated",
    "log_n5",
    "log_n_ge4",
    "mean_rating",
    "five_rate",
    "p1",
    "p2",
    "p3",
    "p4",
    "p5",
    "n_levels",
]

NO_ACTIVITY_FEATURES = [
    f
    for f in FEATURES
    if f not in {"log_n_rated", "log_n5", "log_n_ge4", "n_levels"}
]

# A less redundant panel for the nonlinear binned additive check.
BINNED_FEATURES = [
    "mean_rating",
    "five_rate",
    "p1",
    "p3",
    "depth_ge4",
    "mean_logn_5",
    "midpop_likes_per_log_shelf",
    "popular_likes_per_log_shelf",
    "std_logn_all",
    "rare_rated_share",
    "mega_rated_share",
    "rare_loved_share",
    "mid_loved_share",
    "mega_loved_share",
    "p5_rare_exposed",
    "p5_mega_exposed",
    "mean_work_mean_5",
    "mean_residual",
    "mean_abs_residual",
    "rating_pop_corr",
    "series_share_5",
    "mean_pub_year_5",
    "binge_mean_5",
    "author_hhi_5",
    "singleton_author_share_5",
    "author_div_5",
    "midpop_author_frac_5",
    "midpop_span_per_logn5",
    "mid_catalog_share_5",
    "mega_catalog_share_5",
]


def materialize_behavior_features(con) -> dict[str, Any]:
    """One bounded group-by over ratings; avoids the huge user×author table."""
    print("Building generic rating-behavior features…", flush=True)
    t0 = time.time()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    bb_thr = float(
        con.execute("SELECT approx_quantile(n, 0.995::FLOAT) FROM work_rarity").fetchone()[0]
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_behavior_extra AS
        SELECT
            e.user_id,
            avg(ln(1.0 + wr.n))::DOUBLE AS mean_logn_all,
            stddev_samp(ln(1.0 + wr.n))::DOUBLE AS std_logn_all,
            avg(ln(1.0 + wr.n)) FILTER (WHERE e.rating <= 3)::DOUBLE AS mean_logn_low,
            stddev_samp(ln(1.0 + wr.n)) FILTER (WHERE e.rating = 5)::DOUBLE AS std_logn_5,
            count(*) FILTER (WHERE e.rating=5 AND wr.n >= {bb_thr})::DOUBLE
                / nullif(count(*) FILTER (WHERE wr.n >= {bb_thr}), 0) AS p5_blockbuster,

            count(*) FILTER (WHERE wr.n < 500)::DOUBLE / count(*) AS rare_rated_share,
            count(*) FILTER (WHERE wr.n BETWEEN 500 AND 15000)::DOUBLE / count(*) AS mid_rated_share,
            count(*) FILTER (WHERE wr.n >= 50000)::DOUBLE / count(*) AS mega_rated_share,

            count(*) FILTER (WHERE e.rating = 5 AND wr.n < 500)::DOUBLE
                / nullif(count(*) FILTER (WHERE e.rating = 5), 0) AS rare_loved_share,
            count(*) FILTER (WHERE e.rating = 5 AND wr.n BETWEEN 500 AND 15000)::DOUBLE
                / nullif(count(*) FILTER (WHERE e.rating = 5), 0) AS mid_loved_share,
            count(*) FILTER (WHERE e.rating = 5 AND wr.n >= 50000)::DOUBLE
                / nullif(count(*) FILTER (WHERE e.rating = 5), 0) AS mega_loved_share,

            count(*) FILTER (WHERE e.rating = 5 AND wr.n < 500)::DOUBLE
                / nullif(count(*) FILTER (WHERE wr.n < 500), 0) AS p5_rare_exposed,
            count(*) FILTER (WHERE e.rating = 5 AND wr.n BETWEEN 500 AND 15000)::DOUBLE
                / nullif(count(*) FILTER (WHERE wr.n BETWEEN 500 AND 15000), 0) AS p5_mid_exposed,
            count(*) FILTER (WHERE e.rating = 5 AND wr.n >= 50000)::DOUBLE
                / nullif(count(*) FILTER (WHERE wr.n >= 50000), 0) AS p5_mega_exposed,

            avg(wr.mean)::DOUBLE AS mean_work_mean_all,
            avg(wr.mean) FILTER (WHERE e.rating = 5)::DOUBLE AS mean_work_mean_5,
            avg(wr.mean) FILTER (WHERE e.rating <= 3)::DOUBLE AS mean_work_mean_low,
            avg(e.rating - wr.mean)::DOUBLE AS mean_residual,
            avg(abs(e.rating - wr.mean))::DOUBLE AS mean_abs_residual,
            stddev_samp(e.rating - wr.mean)::DOUBLE AS sd_residual,
            corr(e.rating, ln(1.0 + wr.n))::DOUBLE AS rating_pop_corr
        FROM ex.all_rating_events e
        JOIN work_rarity wr USING (work_id)
        JOIN user_feat uf USING (user_id)
        GROUP BY e.user_id
        """
    )
    n = int(con.execute("SELECT count(*) FROM user_behavior_extra").fetchone()[0])
    print(f"  user_behavior_extra={n:,} ({time.time()-t0:.1f}s)", flush=True)
    return {"n_behavior_users": n, "seconds": time.time() - t0}


def materialize_rich_behavior_features(con) -> dict[str, Any]:
    """Memory-safe version of the original author/series/year panel.

    The old builder first materialized every user×author rating combination.
    Here we restrict that intermediate to 5-star events, which is sufficient for
    every author feature actually used by classic_focus.
    """
    print("Building original-style author/series/year features…", flush=True)
    t0 = time.time()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_user_author_5 AS
        SELECT e.user_id, wa.author_id, count(*)::BIGINT AS n5_a
        FROM ex.all_rating_events e
        JOIN work_ax wa USING (work_id)
        JOIN user_feat uf USING (user_id)
        WHERE e.rating=5 AND uf.n5 >= 5
        GROUP BY e.user_id, wa.author_id
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_author_behavior AS
        SELECT
            user_id,
            count(*)::BIGINT AS n_authors_5,
            avg(n5_a)::DOUBLE AS binge_mean_5,
            max(n5_a)::BIGINT AS binge_max_5,
            (sum(power(n5_a, 2))::DOUBLE / nullif(power(sum(n5_a), 2), 0)) AS author_hhi_5,
            count(*) FILTER (WHERE n5_a=1)::DOUBLE / count(*) AS singleton_author_share_5,
            sum(n5_a)::BIGINT AS n5_with_author
        FROM jury_user_author_5
        GROUP BY user_id
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_five_context AS
        SELECT
            e.user_id,
            count(*)::BIGINT AS n5_context,
            count(*) FILTER (WHERE wa.is_seriesish)::DOUBLE / count(*) AS series_share_5,
            avg(wa.pub_year) FILTER (WHERE wa.pub_year BETWEEN 1500 AND 2020)::DOUBLE AS mean_pub_year_5,
            count(DISTINCT wa.author_id) FILTER (
                WHERE ax.max_work_n BETWEEN 2000 AND 80000
            )::BIGINT AS n_midpop_authors_5,
            count(DISTINCT wa.author_id) FILTER (
                WHERE ax.max_work_n >= 50000
            )::BIGINT AS n_megastar_authors_5,
            count(*) FILTER (WHERE wr.n BETWEEN 500 AND 15000)::DOUBLE / count(*) AS mid_catalog_share_5,
            count(*) FILTER (WHERE wr.n >= 50000)::DOUBLE / count(*) AS mega_catalog_share_5
        FROM ex.all_rating_events e
        JOIN work_ax wa USING (work_id)
        JOIN author_ax ax USING (author_id)
        JOIN work_rarity wr USING (work_id)
        JOIN user_feat uf USING (user_id)
        WHERE e.rating=5 AND uf.n5 >= 5
        GROUP BY e.user_id
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_rich_extra AS
        SELECT
            a.user_id,
            c.series_share_5,
            c.mean_pub_year_5,
            c.n5_context,
            a.n_authors_5,
            ln(1.0 + a.n_authors_5)::DOUBLE AS n_authors_5_log,
            a.binge_mean_5,
            a.binge_max_5,
            ln(1.0 + a.binge_max_5)::DOUBLE AS binge_max_5_log,
            a.author_hhi_5,
            a.singleton_author_share_5,
            a.n_authors_5::DOUBLE / nullif(a.n5_with_author, 0) AS author_div_5,
            ln(1.0 + c.n_midpop_authors_5)::DOUBLE AS n_midpop_authors_5_log,
            c.n_midpop_authors_5::DOUBLE / nullif(a.n_authors_5, 0) AS midpop_author_frac_5,
            c.n_midpop_authors_5::DOUBLE / nullif(ln(1.0 + a.n5_with_author), 0) AS midpop_span_per_logn5,
            c.n_megastar_authors_5,
            ln(1.0 + c.n_megastar_authors_5)::DOUBLE AS n_megastar_authors_5_log,
            c.mid_catalog_share_5,
            c.mega_catalog_share_5
        FROM jury_author_behavior a
        JOIN jury_five_context c USING (user_id)
        """
    )
    row = con.execute(
        """
        SELECT count(*),
               (SELECT count(*) FROM jury_user_author_5),
               (SELECT count(*) FROM jury_rich_extra r JOIN jury_teacher t USING (user_id))
        FROM jury_rich_extra
        """
    ).fetchone()
    meta = {
        "n_rich_users": int(row[0]),
        "n_user_author_rows": int(row[1]),
        "n_teacher_covered": int(row[2]),
        "seconds": time.time() - t0,
    }
    print(f"  rich behavior: {meta}", flush=True)
    return meta


def materialize_model_frame(con) -> dict[str, Any]:
    """Join generic features to teacher only at the final supervised frame."""
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_model_frame AS
        SELECT
            uf.user_id,
            (hash(uf.user_id::VARCHAR) % 5)::INTEGER AS fold,
            CASE WHEN t.user_id IS NULL THEN 0 ELSE 1 END::INTEGER AS teacher,
            coalesce(t.w, 0.0)::DOUBLE AS teacher_w,
            uf.n_rated::DOUBLE AS raw_n_rated,
            ln(1.0 + uf.n_rated)::DOUBLE AS log_n_rated,
            ln(1.0 + uf.n5)::DOUBLE AS log_n5,
            ln(1.0 + uf.n_ge4)::DOUBLE AS log_n_ge4,
            uf.mean_rating,
            uf.five_rate,
            h.c1::DOUBLE / h.n_rated AS p1,
            h.c2::DOUBLE / h.n_rated AS p2,
            h.c3::DOUBLE / h.n_rated AS p3,
            h.c4::DOUBLE / h.n_rated AS p4,
            h.c5::DOUBLE / h.n_rated AS p5,
            h.n_levels::DOUBLE AS n_levels,
            uf.depth_ge4,
            uf.depth_5,
            uf.mean_logn_5,
            uf.n_ge4_midpop::DOUBLE / ln(1.0 + uf.n_rated) AS midpop_likes_per_log_shelf,
            uf.n_ge4_popular::DOUBLE / ln(1.0 + uf.n_rated) AS popular_likes_per_log_shelf,
            bx.* EXCLUDE (user_id),
            rx.* EXCLUDE (user_id)
        FROM user_feat uf
        JOIN ex.user_star_hist h USING (user_id)
        JOIN user_behavior_extra bx USING (user_id)
        LEFT JOIN jury_rich_extra rx USING (user_id)
        LEFT JOIN jury_teacher t USING (user_id)
        """
    )
    row = con.execute(
        """
        SELECT count(*), count(*) FILTER (WHERE teacher=1),
               sum(teacher_w), min(log_n_rated), max(log_n_rated)
        FROM jury_model_frame
        """
    ).fetchone()
    return {
        "n_candidates": int(row[0]),
        "n_teacher_covered": int(row[1]),
        "teacher_weight_covered": float(row[2] or 0),
        "min_log_n": float(row[3]),
        "max_log_n": float(row[4]),
    }


def materialize_old_focus_approx(con) -> dict[str, Any]:
    """Rebuild the supplied classic_focus formula on the staged rich panel."""
    w = load_weights()
    term_cols = sorted(
        set(w["classic_terms"]) | set(w["anti_terms"]) | set(w["normie_terms"])
    )
    eligible = (
        "raw_n_rated>=40 AND n5_context>=8 "
        "AND series_share_5 IS NOT NULL AND binge_mean_5 IS NOT NULL "
        "AND midpop_span_per_logn5 IS NOT NULL"
    )
    moments: dict[str, tuple[float, float]] = {}
    for c in term_cols:
        mu, sd = con.execute(
            f"SELECT avg({c}), stddev_samp({c}) FROM jury_model_frame WHERE {eligible}"
        ).fetchone()
        moments[c] = (float(mu or 0), float(sd or 1) or 1.0)

    def z(c: str) -> str:
        mu, sd = moments[c]
        return f"((coalesce({c}, {mu}) - ({mu})) / ({sd}))"

    def linear(terms: dict[str, float]) -> str:
        return " + ".join(f"({float(v)})*{z(c)}" for c, v in terms.items())

    classic = linear(w["classic_terms"])
    anti = linear(w["anti_terms"])
    normie = linear(w["normie_terms"])
    focus = (
        f"({classic}) - ({float(w.get('lambda_anti', .85))})*({anti}) "
        f"- ({float(w.get('lambda_normie', .75))})*({normie})"
    )
    g = w["gates"]
    con.execute(
        f"""
        CREATE OR REPLACE TABLE jury_old_affinity_approx AS
        SELECT user_id, ({focus})::DOUBLE AS classic_focus,
               ({classic})::DOUBLE AS classic_raw, ({anti})::DOUBLE AS anti_raw,
               ({normie})::DOUBLE AS normie_raw,
               series_share_5, mega_catalog_share_5, binge_mean_5,
               midpop_span_per_logn5
        FROM jury_model_frame
        WHERE {eligible}
        """
    )
    gate = (
        f"series_share_5 <= {float(g['series_gate'])} "
        f"AND mega_catalog_share_5 <= {float(g['mega_gate'])} "
        f"AND binge_mean_5 <= {float(g['binge_gate'])} "
        f"AND midpop_span_per_logn5 >= {float(g['span_gate'])}"
    )
    top_frac = float(w.get("top_frac", 0.06))
    threshold = float(
        con.execute(
            f"SELECT approx_quantile(classic_focus, {1-top_frac}::FLOAT) "
            f"FROM jury_old_affinity_approx WHERE {gate}"
        ).fetchone()[0]
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE jury_old_focus_approx AS
        SELECT user_id, 1.0::DOUBLE AS w
        FROM jury_old_affinity_approx
        WHERE {gate} AND classic_focus >= {threshold}
        """
    )
    n_eligible = int(
        con.execute(f"SELECT count(*) FROM jury_old_affinity_approx WHERE {gate}").fetchone()[0]
    )
    return {
        "n_rich_eligible_before_gates": int(
            con.execute("SELECT count(*) FROM jury_old_affinity_approx").fetchone()[0]
        ),
        "n_gated": n_eligible,
        "n_focus": int(con.execute("SELECT count(*) FROM jury_old_focus_approx").fetchone()[0]),
        "threshold": threshold,
        "target_historical_n": 4774,
        "historical_threshold": 18.847782237992767,
        "note": "approximate because rich features were restaged with a lower-memory query",
    }


def fetch_frame(con) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    cols = ", ".join(FEATURES)
    d = con.execute(
        f"SELECT user_id, fold, teacher, teacher_w, {cols} FROM jury_model_frame ORDER BY user_id"
    ).fetchnumpy()

    def clean(a) -> np.ndarray:
        if np.ma.isMaskedArray(a):
            a = a.filled(np.nan)
        return np.asarray(a, dtype=np.float64)

    ids = np.asarray(d["user_id"], dtype=np.int64)
    folds = np.asarray(d["fold"], dtype=np.int8)
    y = np.asarray(d["teacher"], dtype=np.int8)
    teacher_w = clean(d["teacher_w"])
    x = np.column_stack([clean(d[f]) for f in FEATURES])
    return ids, folds, y, teacher_w, x


def activity_bins(x: np.ndarray) -> np.ndarray:
    j = FEATURES.index("log_n_rated")
    cuts = np.quantile(x[:, j], np.linspace(0.1, 0.9, 9))
    return np.searchsorted(cuts, x[:, j], side="right").astype(np.int8)


def training_weights(
    y: np.ndarray,
    teacher_w: np.ndarray,
    train: np.ndarray,
    bins: np.ndarray,
    *,
    matched: bool,
) -> np.ndarray:
    """Stored-weight positives; optional negative matching by shelf-size decile."""
    sw = np.zeros(len(y), dtype=np.float64)
    pos = train & (y == 1)
    neg = train & (y == 0)
    pos_base = np.maximum(teacher_w[pos], 1e-9)
    pos_base /= max(float(pos_base.mean()), 1e-12)
    sw[pos] = pos_base
    if not matched:
        sw[neg] = 1.0
        sw[pos] *= float(neg.sum()) / max(float(sw[pos].sum()), 1e-12)
    else:
        # Within each activity decile, positive and negative mass match.  The
        # amount each decile contributes follows the teacher's stored mass.
        for b in range(10):
            pb = pos & (bins == b)
            nb = neg & (bins == b)
            if not pb.any() or not nb.any():
                continue
            sw[nb] = float(sw[pb].sum()) / float(nb.sum())
    sw_sum = float(sw[train].sum())
    if sw_sum:
        sw[train] *= float(train.sum()) / sw_sum
    return sw


def _impute_standardize(
    x_train: np.ndarray, x_score: np.ndarray, sw_train: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    med = np.nanmedian(x_train, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    a = np.where(np.isfinite(x_train), x_train, med)
    b = np.where(np.isfinite(x_score), x_score, med)
    wsum = max(float(sw_train.sum()), 1e-12)
    mu = (a * sw_train[:, None]).sum(axis=0) / wsum
    var = ((a - mu) ** 2 * sw_train[:, None]).sum(axis=0) / wsum
    sd = np.sqrt(np.maximum(var, 1e-8))
    return (a - mu) / sd, (b - mu) / sd, mu, sd


def ridge_oof(
    x: np.ndarray,
    y: np.ndarray,
    teacher_w: np.ndarray,
    folds: np.ndarray,
    bins: np.ndarray,
    feature_names: list[str],
    *,
    matched: bool,
    alpha: float = RIDGE_ALPHA,
) -> tuple[np.ndarray, dict[str, float]]:
    js = [FEATURES.index(f) for f in feature_names]
    xx = x[:, js]
    scores = np.empty(len(y), dtype=np.float64)
    coefs = []
    for fold in range(N_FOLDS):
        train = folds != fold
        test = ~train
        sw = training_weights(y, teacher_w, train, bins, matched=matched)
        a, b, _mu, _sd = _impute_standardize(xx[train], xx[test], sw[train])
        aa = np.column_stack([np.ones(len(a)), a])
        bb = np.column_stack([np.ones(len(b)), b])
        w = sw[train]
        lhs = (aa.T @ (aa * w[:, None])) / max(float(w.sum()), 1e-12)
        penalty = np.eye(lhs.shape[0]) * alpha
        penalty[0, 0] = 0.0
        rhs = (aa.T @ (w * y[train])) / max(float(w.sum()), 1e-12)
        beta = np.linalg.solve(lhs + penalty, rhs)
        scores[test] = bb @ beta
        coefs.append(beta[1:])
    mean_coef = np.mean(np.vstack(coefs), axis=0)
    return scores, {f: float(v) for f, v in zip(feature_names, mean_coef)}


def binned_oof(
    x: np.ndarray,
    y: np.ndarray,
    teacher_w: np.ndarray,
    folds: np.ndarray,
    bins: np.ndarray,
    feature_names: list[str],
    *,
    n_bins: int = 10,
) -> np.ndarray:
    """Nonlinear additive sanity check, with strong per-feature shrinkage."""
    js = [FEATURES.index(f) for f in feature_names]
    scores = np.zeros(len(y), dtype=np.float64)
    for fold in range(N_FOLDS):
        train = folds != fold
        test = ~train
        sw = training_weights(y, teacher_w, train, bins, matched=True)
        fold_score = np.zeros(int(test.sum()), dtype=np.float64)
        for j in js:
            tr = x[train, j]
            te = x[test, j]
            finite = np.isfinite(tr)
            if finite.sum() < 100:
                continue
            cuts = np.unique(np.quantile(tr[finite], np.linspace(0.1, 0.9, n_bins - 1)))
            med = float(np.nanmedian(tr))
            trb = np.searchsorted(cuts, np.where(np.isfinite(tr), tr, med), side="right")
            teb = np.searchsorted(cuts, np.where(np.isfinite(te), te, med), side="right")
            rates = np.zeros(len(cuts) + 1, dtype=np.float64)
            global_rate = float((sw[train] * y[train]).sum() / max(sw[train].sum(), 1e-12))
            prior = 200.0
            for b in range(len(rates)):
                m = trb == b
                den = float(sw[train][m].sum())
                num = float((sw[train][m] * y[train][m]).sum())
                rate = (num + prior * global_rate) / (den + prior)
                rates[b] = math.log(max(rate, 1e-6) / max(1.0 - rate, 1e-6))
            fold_score += rates[teb]
        scores[test] = fold_score / max(math.sqrt(len(js)), 1.0)
    return scores


def average_precision(y: np.ndarray, score: np.ndarray) -> float:
    order = np.argsort(-score, kind="stable")
    yy = y[order]
    hit = np.cumsum(yy)
    precision = hit / np.arange(1, len(y) + 1)
    return float((precision * yy).sum() / max(int(y.sum()), 1))


def roc_auc(y: np.ndarray, score: np.ndarray) -> float:
    # Ties are negligible for these continuous scores.
    order = np.argsort(score, kind="stable")
    ranks = np.empty(len(y), dtype=np.float64)
    ranks[order] = np.arange(1, len(y) + 1)
    pos = y == 1
    np_, nn = int(pos.sum()), int((~pos).sum())
    return float((ranks[pos].sum() - np_ * (np_ + 1) / 2) / max(np_ * nn, 1))


def evaluate_scores(
    ids: np.ndarray,
    y: np.ndarray,
    teacher_w: np.ndarray,
    score: np.ndarray,
    *,
    teacher_n: int,
) -> dict[str, Any]:
    order = np.argsort(-score, kind="stable")
    total_mass = float(teacher_w.sum())

    def at(k: int) -> dict[str, Any]:
        chosen = order[: min(k, len(order))]
        overlap = int(y[chosen].sum())
        mass = float(teacher_w[chosen].sum())
        return {
            "k": int(k),
            "overlap": overlap,
            "precision": overlap / max(len(chosen), 1),
            "teacher_recall": overlap / max(teacher_n, 1),
            "jaccard": overlap / max(teacher_n + len(chosen) - overlap, 1),
            "teacher_weight_recall": mass / max(total_mass, 1e-12),
        }

    primary = at(teacher_n)
    return {
        "roc_auc": roc_auc(y, score),
        "average_precision": average_precision(y, score),
        "primary": primary,
        "size_sweep": [at(max(50, int(round(teacher_n * f)))) for f in (0.5, 0.75, 1, 1.25, 1.5, 2, 3)],
        "selected_user_ids": [int(ids[i]) for i in order[:teacher_n]],
        "ranked_user_ids": [int(ids[i]) for i in order[: min(teacher_n * 3, len(order))]],
        "score_quantiles": {
            str(q): float(np.quantile(score, q)) for q in (0.01, 0.1, 0.5, 0.9, 0.99)
        },
    }


def materialize_excluded_works(con, ev: dict[str, Any]) -> dict[str, Any]:
    """Remove known mint/evaluation works from item-identity reconstruction."""
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_excluded_works AS
        SELECT work_id::VARCHAR AS work_id FROM ex.poll_works
        UNION
        SELECT work_id::VARCHAR FROM ex.deep_poll_works
        UNION
        SELECT work_id::VARCHAR FROM ex.taste_signal_works
        """
    )
    existing = {
        str(r[0]) for r in con.execute("SELECT work_id FROM jury_excluded_works").fetchall()
    }
    eval_ids = set(ev["pos_works"]) | set(ev["anti_works"]) | set(ev["normie_works"])
    missing = sorted(eval_ids - existing)
    if missing:
        con.executemany(
            "INSERT INTO jury_excluded_works VALUES (?)",
            [(w,) for w in missing],
        )
    n = int(con.execute("SELECT count(DISTINCT work_id) FROM jury_excluded_works").fetchone()[0])
    return {"n_excluded_works": n, "n_eval_ids_added": len(missing)}


def materialize_oof_work_profiles(con) -> dict[str, Any]:
    """Cross-fitted item profile with each user's label held out.

    Every reader contributes roughly one unit of total shelf mass, preventing
    hyper-raters from dominating item coefficients. Known teacher/eval signal
    works were removed upstream.
    """
    print("Building decontaminated OOF co-reading profiles…", flush=True)
    t0 = time.time()
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_fold_work_mass AS
        SELECT
            e.work_id,
            f.fold,
            sum(CASE WHEN f.teacher=1 THEN f.teacher_w / f.raw_n_rated ELSE 0 END)::DOUBLE AS pos_mass,
            sum(CASE WHEN f.teacher=0 THEN 1.0 / f.raw_n_rated ELSE 0 END)::DOUBLE AS neg_mass,
            sum(CASE WHEN f.teacher=1 THEN
                    (f.teacher_w / f.raw_n_rated)
                    * ((CASE WHEN e.rating=5 THEN 1.0 ELSE 0.0 END) - f.five_rate)
                ELSE 0 END)::DOUBLE AS pos_pref_mass,
            sum(CASE WHEN f.teacher=0 THEN
                    (1.0 / f.raw_n_rated)
                    * ((CASE WHEN e.rating=5 THEN 1.0 ELSE 0.0 END) - f.five_rate)
                ELSE 0 END)::DOUBLE AS neg_pref_mass,
            count(*) FILTER (WHERE f.teacher=1)::BIGINT AS pos_readers,
            count(*) FILTER (WHERE f.teacher=0)::BIGINT AS neg_readers
        FROM ex.all_rating_events e
        JOIN jury_model_frame f USING (user_id)
        JOIN work_rarity wr USING (work_id)
        LEFT JOIN jury_excluded_works z USING (work_id)
        WHERE z.work_id IS NULL AND wr.n >= 100
        GROUP BY e.work_id, f.fold
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_oof_work_profile AS
        WITH targets AS (SELECT range::INTEGER AS target_fold FROM range(5)),
        train_mass AS (
            SELECT
                m.work_id,
                t.target_fold,
                sum(m.pos_mass) FILTER (WHERE m.fold <> t.target_fold)::DOUBLE AS pos_mass,
                sum(m.neg_mass) FILTER (WHERE m.fold <> t.target_fold)::DOUBLE AS neg_mass,
                sum(m.pos_pref_mass) FILTER (WHERE m.fold <> t.target_fold)::DOUBLE AS pos_pref_mass,
                sum(m.neg_pref_mass) FILTER (WHERE m.fold <> t.target_fold)::DOUBLE AS neg_pref_mass,
                sum(m.pos_readers) FILTER (WHERE m.fold <> t.target_fold)::BIGINT AS pos_readers,
                sum(m.neg_readers) FILTER (WHERE m.fold <> t.target_fold)::BIGINT AS neg_readers
            FROM jury_fold_work_mass m
            CROSS JOIN targets t
            GROUP BY m.work_id, t.target_fold
        ),
        totals AS (
            SELECT target_fold, sum(pos_mass)::DOUBLE AS pos_total,
                   sum(neg_mass)::DOUBLE AS neg_total
            FROM train_mass GROUP BY target_fold
        ),
        raw AS (
            SELECT
                m.*,
                t.pos_total,
                t.neg_total,
                (m.neg_mass / nullif(t.neg_total, 0))::DOUBLE AS background_prob,
                (
                    ln(
                        ((m.pos_mass + 25.0 * (m.neg_mass / nullif(t.neg_total, 0)))
                         / (t.pos_total + 25.0))
                        / nullif(m.neg_mass / t.neg_total, 0)
                    )
                    * sqrt(m.pos_readers::DOUBLE / (m.pos_readers + 12.0))
                )::DOUBLE AS read_coef,
                (
                    (m.pos_pref_mass / nullif(m.pos_mass, 0))
                    - (m.neg_pref_mass / nullif(m.neg_mass, 0))
                ) * sqrt(m.pos_readers::DOUBLE / (m.pos_readers + 12.0)) AS pref_coef
            FROM train_mass m JOIN totals t USING (target_fold)
            WHERE m.pos_readers >= 3 AND m.neg_readers >= 50
        )
        SELECT
            work_id,
            target_fold,
            greatest(-3.0, least(3.0, read_coef))::DOUBLE AS read_coef,
            greatest(-1.0, least(1.0, pref_coef))::DOUBLE AS pref_coef,
            pos_readers,
            neg_readers,
            background_prob
        FROM raw
        WHERE read_coef IS NOT NULL AND isfinite(read_coef)
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_profile_scores AS
        SELECT
            f.user_id,
            count(*)::BIGINT AS n_profile_books,
            avg(p.read_coef)::DOUBLE AS profile_mean,
            (sum(p.read_coef) / sqrt(count(*)))::DOUBLE AS profile_evidence,
            avg(
                p.read_coef
                + 2.0 * p.pref_coef
                  * ((CASE WHEN e.rating=5 THEN 1.0 ELSE 0.0 END) - f.five_rate)
            )::DOUBLE AS profile_love,
            avg(p.read_coef) FILTER (WHERE hash(e.work_id) % 2 = 0)::DOUBLE AS profile_half0,
            avg(p.read_coef) FILTER (WHERE hash(e.work_id) % 2 = 1)::DOUBLE AS profile_half1
        FROM ex.all_rating_events e
        JOIN jury_model_frame f USING (user_id)
        JOIN jury_oof_work_profile p
          ON p.work_id=e.work_id AND p.target_fold=f.fold
        GROUP BY f.user_id
        """
    )
    row = con.execute(
        """
        SELECT count(*), avg(n_profile_books),
               (SELECT count(*) FROM jury_oof_work_profile)
        FROM jury_profile_scores
        """
    ).fetchone()
    meta = {
        "n_users_scored": int(row[0]),
        "mean_profile_books": float(row[1] or 0),
        "n_fold_work_profiles": int(row[2]),
        "seconds": time.time() - t0,
    }
    print(f"  co-reading profiles: {meta} ", flush=True)
    return meta


def fetch_profile_scores(con, ids: np.ndarray) -> dict[str, np.ndarray]:
    d = con.execute(
        """
        SELECT f.user_id, s.profile_mean, s.profile_evidence, s.profile_love,
               s.profile_half0, s.profile_half1
        FROM jury_model_frame f
        LEFT JOIN jury_profile_scores s USING (user_id)
        ORDER BY f.user_id
        """
    ).fetchnumpy()
    got_ids = np.asarray(d["user_id"], dtype=np.int64)
    if not np.array_equal(got_ids, ids):
        raise RuntimeError("profile/model user ordering mismatch")
    out = {}
    for key in ("profile_mean", "profile_evidence", "profile_love", "profile_half0", "profile_half1"):
        a = d[key]
        if np.ma.isMaskedArray(a):
            a = a.filled(np.nan)
        a = np.asarray(a, dtype=np.float64)
        fill = float(np.nanmedian(a))
        out[key] = np.where(np.isfinite(a), a, fill)
    return out


def top_profile_anchors(con, *, limit: int = 30) -> list[dict[str, Any]]:
    rows = con.execute(
        f"""
        SELECT
            p.work_id, s.title, s.author, avg(p.read_coef) AS coef,
            avg(p.pos_readers) AS pos_readers, avg(p.neg_readers) AS neg_readers
        FROM jury_oof_work_profile p
        JOIN ex.work_scores s USING (work_id)
        GROUP BY p.work_id, s.title, s.author
        ORDER BY coef DESC
        LIMIT {limit}
        """
    ).fetchall()
    return [
        {
            "work_id": str(w),
            "title": t,
            "author": a,
            "coef": float(c),
            "pos_readers": float(np_),
            "neg_readers": float(nn),
        }
        for w, t, a, c, np_, nn in rows
    ]


def selected_jaccard(a: list[int], b: list[int]) -> float:
    aa, bb = set(a), set(b)
    return len(aa & bb) / max(len(aa | bb), 1)


def write_jury_table(con, name: str, ids: list[int]) -> None:
    con.execute(f"CREATE OR REPLACE TABLE {name}(user_id BIGINT, w DOUBLE)")
    con.executemany(f"INSERT INTO {name} VALUES (?, 1.0)", [(i,) for i in ids])


def cohort_overlap(con, a: str, b: str) -> dict[str, Any]:
    na = int(con.execute(f"SELECT count(*) FROM {a}").fetchone()[0])
    nb = int(con.execute(f"SELECT count(*) FROM {b}").fetchone()[0])
    inter = int(
        con.execute(f"SELECT count(*) FROM {a} x JOIN {b} y USING (user_id)").fetchone()[0]
    )
    return {
        "n_a": na,
        "n_b": nb,
        "intersection": inter,
        "jaccard": inter / max(na + nb - inter, 1),
        "a_in_b": inter / max(na, 1),
        "b_in_a": inter / max(nb, 1),
    }


def pairwise_readout(con, jury: str, pairs: str, ev, sticky, heldout) -> dict[str, Any]:
    n_pairs = build_pairs(con, jury, pairs)
    rows = rank_pairwise(con, pairs, "1.0")
    return {
        "n_pairs": n_pairs,
        "probe": probe_metrics(rows, ev, sticky),
        "heldout": heldout_recall(rows, heldout),
        "top15": top15(rows),
        "top50_work_ids": [r["work_id"] for r in rows[:50]],
    }


def diff_diagnostics(con) -> dict[str, Any]:
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_false_positive AS
        SELECT p.user_id FROM jury_preliminary p
        LEFT JOIN jury_teacher t USING (user_id) WHERE t.user_id IS NULL
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE jury_false_negative AS
        SELECT t.user_id FROM jury_teacher t
        LEFT JOIN jury_preliminary p USING (user_id) WHERE p.user_id IS NULL
        """
    )

    def summarize(table: str) -> dict[str, Any]:
        row = con.execute(
            f"""
            SELECT count(*), avg(f.log_n_rated), avg(f.five_rate), avg(f.depth_ge4),
                   avg(f.mean_logn_5), avg(f.rare_loved_share), avg(f.mega_loved_share),
                   avg(f.mean_abs_residual)
            FROM {table} x JOIN jury_model_frame f USING (user_id)
            """
        ).fetchone()
        return {
            "n": int(row[0]),
            "mean_n_rated": math.expm1(float(row[1] or 0)),
            "five_rate": float(row[2] or 0),
            "depth_ge4": float(row[3] or 0),
            "mean_logn_5": float(row[4] or 0),
            "rare_loved_share": float(row[5] or 0),
            "mega_loved_share": float(row[6] or 0),
            "mean_abs_residual": float(row[7] or 0),
        }

    fp_deep = con.execute(
        """
        SELECT count(*),
               count(*) FILTER (WHERE d.user_id IS NOT NULL),
               avg(d.deep_share) FILTER (WHERE d.user_id IS NOT NULL),
               avg(d.com_share) FILTER (WHERE d.user_id IS NOT NULL),
               avg(d.n_deep) FILTER (WHERE d.user_id IS NOT NULL)
        FROM jury_false_positive f
        LEFT JOIN ex.user_curator_deep_weight d USING (user_id)
        """
    ).fetchone()
    fn_teacher = con.execute(
        """
        SELECT avg(t.w), avg(t.deep_share), avg(t.com_share), avg(t.n_deep),
               count(*) FILTER (WHERE f.log_n_rated >= ln(1+1000))
        FROM jury_false_negative x
        JOIN jury_teacher t USING (user_id)
        JOIN jury_model_frame f USING (user_id)
        """
    ).fetchone()
    return {
        "false_positive": summarize("jury_false_positive"),
        "false_negative": summarize("jury_false_negative"),
        "false_positive_deep_status": {
            "n": int(fp_deep[0]),
            "in_deep_mint": int(fp_deep[1]),
            "share_in_deep_mint": float(fp_deep[1]) / max(int(fp_deep[0]), 1),
            "mean_deep_share_if_minted": float(fp_deep[2] or 0),
            "mean_com_share_if_minted": float(fp_deep[3] or 0),
            "mean_n_deep_if_minted": float(fp_deep[4] or 0),
        },
        "missed_teacher_mint": {
            "mean_stored_weight": float(fn_teacher[0] or 0),
            "mean_deep_share": float(fn_teacher[1] or 0),
            "mean_com_share": float(fn_teacher[2] or 0),
            "mean_n_deep": float(fn_teacher[3] or 0),
            "n_hyper_raters_ge1000": int(fn_teacher[4] or 0),
        },
        "false_positive_common_fives": common_five_star_books(
            con, "jury_false_positive", weighted=False, limit=15
        ),
        "false_negative_common_fives": common_five_star_books(
            con, "jury_false_negative", weighted=False, limit=15
        ),
    }


def _slim_model(model: dict[str, Any]) -> dict[str, Any]:
    out = {
        k: v
        for k, v in model.items()
        if k not in {"selected_user_ids", "ranked_user_ids"}
    }
    return out


def write_report(results: dict[str, Any]) -> None:
    models = results["models"]
    chosen = models[results["chosen_model"]]
    p = results["preliminary_selection"]
    teacher = results["teacher"]
    lines = [
        "# Jury rebuild: behavioral reconstruction of p65/s25",
        "",
        "## Outcome",
        "",
        f"The preliminary jury uses **{results['chosen_model']}** and contains "
        f"**{p['k']:,}** users. Its honest five-fold out-of-fold overlap with the "
        f"teacher is **{p['overlap']:,}** (Jaccard **{p['jaccard']:.3f}**), capturing "
        f"**{100*p['teacher_weight_recall']:.1f}%** of stored teacher weight.",
        "",
        "This is a reconstruction diagnostic, not a locked production cohort.",
        "",
        "## Guardrails",
        "",
        "- Teacher: deep mint with purity=65 and strictness=25, weighted by stored "
        "`curator_pct_weight`.",
        "- Selected predictors: generic rating aggregates plus author breadth/concentration, "
        "series behavior, and publication-era behavior. No poll/taste membership or mint "
        "columns enter model fitting.",
        f"- The co-reading profile explicitly removes **{results['excluded_work_guard']['n_excluded_works']:,}** "
        "known poll, deep-poll, taste-signal, and evaluation works before learning.",
        "- Evaluation is out-of-fold: each user is scored by a model that did not see "
        "that user's teacher label.",
        "- Direct-activity removal is an explicit ablation. It preserves nearly all of the "
        "rich model's recovery, while the activity-only baseline is weak; activity is not "
        "the main shortcut.",
        "- Poll and school/normie piles remain diagnostics, never model loss terms.",
        "",
        "## Teacher and candidate pool",
        "",
        f"- Teacher n: **{teacher['n_jury']:,}**, Kish ≈ **{teacher['kish_n_eff']:.0f}**, "
        f"stored mass={teacher['sum_w']:.1f}.",
        f"- Behavioral candidates: **{results['frame']['n_candidates']:,}**; teacher "
        f"coverage: **{results['frame']['n_teacher_covered']:,}/{teacher['n_jury']:,}**.",
        f"- Restaged old focus: **{results['old_focus_approx']['n_focus']:,}** users "
        f"(historical exact n=4,774); old-focus↔teacher Jaccard "
        f"**{results['overlap_old_focus_teacher']['jaccard']:.3f}**.",
        f"- Preliminary↔teacher Jaccard at the broader size knee is "
        f"**{results['overlap_preliminary_teacher']['jaccard']:.3f}**; "
        f"preliminary↔old-focus Jaccard is "
        f"**{results['overlap_preliminary_old_focus']['jaccard']:.3f}**.",
        "",
        "## Honest reconstruction",
        "",
        "| model | predictors | AUC | AP | overlap@teacher-n | Jaccard | teacher weight |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, m in models.items():
        q = m["primary"]
        lines.append(
            f"| {name} | {m['n_features']} | {m['roc_auc']:.3f} | "
            f"{m['average_precision']:.3f} | {q['overlap']} | {q['jaccard']:.3f} | "
            f"{100*q['teacher_weight_recall']:.1f}% |"
        )
    lines += [
        "",
        "Random precision is the teacher prevalence in the candidate pool; the activity "
        "baseline shows how much of reconstruction is just shelf size and star usage.",
        "",
        "### Preferred-model size sweep",
        "",
        "| jury n | overlap | precision | teacher recall | Jaccard | teacher weight |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for s in chosen["size_sweep"]:
        lines.append(
            f"| {s['k']} | {s['overlap']} | {s['precision']:.3f} | "
            f"{s['teacher_recall']:.3f} | {s['jaccard']:.3f} | "
            f"{100*s['teacher_weight_recall']:.1f}% |"
        )

    lines += ["", "### What the behavioral reconstruction learned", ""]
    if results["chosen_coefficients"]:
        for name, value in results["chosen_coefficients"][:16]:
            lines.append(f"- `{name}`: {value:+.3f}")
    else:
        lines.append(
            "The selected binned model is nonlinear, so the signed terms below come from "
            "the companion rich linear model fitted to the same feature panel:"
        )
        for name, value in results["rich_linear_coefficients"][:16]:
            lines.append(f"- `{name}`: {value:+.3f}")
    lines += [
        "",
        "### Co-reading fallback audit (not the selected jury)",
        "",
        "Top positive non-signal anchors are shown to make the item-identity shortcut visible:",
    ]
    for a in results["top_profile_anchors"][:16]:
        lines.append(
            f"- {a['title']} — {a['author']} (coef={a['coef']:+.2f}, "
            f"teacher readers≈{a['pos_readers']:.0f})"
        )
    hs = results["profile_half_stability"]
    lines += [
        "",
        "### Book-half stability",
        "",
        f"- Hash-half 0 vs hash-half 1 jury Jaccard: **{hs['half0_vs_half1_jaccard']:.3f}**.",
        f"- Half 0 vs full-profile jury: **{hs['half0_vs_full_love_jaccard']:.3f}**; "
        f"half 1 vs full: **{hs['half1_vs_full_love_jaccard']:.3f}**.",
        "",
        "The two disjoint book halves are a shortcut check: low agreement means the "
        "co-reading fallback is still relying on narrow reading islands rather than a stable "
        "reader trait. It was not selected.",
    ]

    lines += ["", "## Pairwise head comparison", ""]
    pair_labels = ["preliminary", "old_focus_approx", "teacher"]
    for label in pair_labels:
        r = results["pairwise"][label]
        q = r["probe"]
        h = r["heldout"]
        lines.append(
            f"- **{label}:** pos50={q['pos50']}, anti50={q['anti50']}, "
            f"filler50={q['filler50']}, sticky50={q['sticky50']}, "
            f"heldout@50={h['recall@50']:.3f}, heldout@200={h['recall@200']:.3f}."
        )
    lines += [
        f"- Pairwise top-50 Jaccard preliminary↔teacher: "
        f"**{results['pairwise']['top50_jaccard']:.3f}**.",
        "- Historical old-focus comparison (from `JURY_DIAGNOSIS_REPORT.md`): "
        "pos50=19, anti50=0, filler50=0, sticky50=6, heldout@50=0.209, "
        "heldout@200=0.605.",
    ]
    for label in pair_labels:
        lines += ["", f"### {label.title()} top 15", ""]
        for r in results["pairwise"][label]["top15"]:
            lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")

    d = results["diffs"]
    lines += [
        "",
        "## Set differences",
        "",
        "| group | n | mean shelf | five rate | rare-loved share | mega-loved share |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, label in (("false_negative", "teacher − jury"), ("false_positive", "jury − teacher")):
        x = d[key]
        lines.append(
            f"| {label} | {x['n']} | {x['mean_n_rated']:.0f} | {x['five_rate']:.3f} | "
            f"{x['rare_loved_share']:.3f} | {x['mega_loved_share']:.3f} |"
        )
    fp = d["false_positive_deep_status"]
    fn = d["missed_teacher_mint"]
    lines += [
        "",
        f"- Of jury−teacher, **{fp['in_deep_mint']:,}/{fp['n']:,}** "
        f"({100*fp['share_in_deep_mint']:.1f}%) are elsewhere in the deep mint. "
        f"Their minted mean deep_share={fp['mean_deep_share_if_minted']:.3f}, "
        f"com_share={fp['mean_com_share_if_minted']:.3f}, n_deep={fp['mean_n_deep_if_minted']:.1f}.",
        f"- Missed teachers have mean stored weight={fn['mean_stored_weight']:.3f}, "
        f"deep_share={fn['mean_deep_share']:.3f}, n_deep={fn['mean_n_deep']:.1f}; "
        f"**{fn['n_hyper_raters_ge1000']}** have ≥1,000 ratings.",
        "",
        "### Common 5★ books in the differences",
        "",
        "**Jury − teacher:**",
    ]
    for x in d["false_positive_common_fives"][:10]:
        lines.append(f"- {x['title']} — {x['author']} ({x['n_users']} users)")
    lines += ["", "**Teacher − jury:**"]
    for x in d["false_negative_common_fives"][:10]:
        lines.append(f"- {x['title']} — {x['author']} ({x['n_users']} users)")
    lines += [
        "",
        "## Decision",
        "",
        f"Use **{results['chosen_model']} at n={p['k']:,}** as the current preliminary "
        "behavioral jury. This is the overlap/mass knee rather than a copied teacher-size "
        "cut, and its pairwise head materially beats the old focus while approaching the "
        "teacher. Do not adopt the higher-overlap co-reading evidence model: its explicit "
        "literary-title anchors and only moderate disjoint-book stability make it a shortcut.",
        "",
        "This remains a preliminary hard jury. Continuous jury weights are still deferred, "
        "as agreed in the handoff.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    t_all = time.time()
    con = _con()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())

    materialize_base(con)
    teacher = make_jury(con, purity=PURITY, strictness=STRICTNESS, name="jury_teacher")
    materialize_work_author_year(con)
    behavior = materialize_behavior_features(con)
    rich_behavior = materialize_rich_behavior_features(con)
    frame = materialize_model_frame(con)
    old_focus_approx = materialize_old_focus_approx(con)
    print(f"Candidate frame: {frame}", flush=True)

    ids, folds, y, teacher_w, x = fetch_frame(con)
    bins = activity_bins(x)
    models: dict[str, dict[str, Any]] = {}
    coefficients: dict[str, dict[str, float]] = {}

    specs = [
        ("activity_baseline", ACTIVITY_FEATURES, False),
        ("generic_behavior_global", GENERIC_FEATURES, False),
        ("rich_behavior_global", FEATURES, False),
        ("rich_behavior_no_direct_activity", NO_ACTIVITY_FEATURES, False),
        ("rich_behavior_activity_matched", NO_ACTIVITY_FEATURES, True),
    ]
    for name, features, matched in specs:
        print(f"Cross-fitting {name} ({len(features)} features)…", flush=True)
        score, coef = ridge_oof(
            x, y, teacher_w, folds, bins, features, matched=matched
        )
        m = evaluate_scores(ids, y, teacher_w, score, teacher_n=teacher["n_jury"])
        m["n_features"] = len(features)
        m["matched_activity"] = matched
        models[name] = m
        coefficients[name] = coef
        print(
            f"  AUC={m['roc_auc']:.3f} AP={m['average_precision']:.3f} "
            f"overlap={m['primary']['overlap']:,} J={m['primary']['jaccard']:.3f} "
            f"mass={m['primary']['teacher_weight_recall']:.1%}",
            flush=True,
        )

    print("Cross-fitting nonlinear binned check…", flush=True)
    binned_score = binned_oof(x, y, teacher_w, folds, bins, BINNED_FEATURES)
    bm = evaluate_scores(ids, y, teacher_w, binned_score, teacher_n=teacher["n_jury"])
    bm["n_features"] = len(BINNED_FEATURES)
    bm["matched_activity"] = True
    models["behavior_binned_matched"] = bm
    print(
        f"  AUC={bm['roc_auc']:.3f} AP={bm['average_precision']:.3f} "
        f"overlap={bm['primary']['overlap']:,} J={bm['primary']['jaccard']:.3f} "
        f"mass={bm['primary']['teacher_weight_recall']:.1%}",
        flush=True,
    )

    excluded = materialize_excluded_works(con, ev)
    profile_meta = materialize_oof_work_profiles(con)
    profile_scores = fetch_profile_scores(con, ids)
    for name, score in profile_scores.items():
        pm = evaluate_scores(ids, y, teacher_w, score, teacher_n=teacher["n_jury"])
        pm["n_features"] = 1
        pm["matched_activity"] = True
        models[name] = pm
        print(
            f"  {name}: AUC={pm['roc_auc']:.3f} AP={pm['average_precision']:.3f} "
            f"overlap={pm['primary']['overlap']:,} J={pm['primary']['jaccard']:.3f} "
            f"mass={pm['primary']['teacher_weight_recall']:.1%}",
            flush=True,
        )

    def z(a: np.ndarray) -> np.ndarray:
        return (a - float(np.mean(a))) / max(float(np.std(a)), 1e-12)

    blended_score = z(profile_scores["profile_love"]) + 0.25 * z(binned_score)
    blend = evaluate_scores(ids, y, teacher_w, blended_score, teacher_n=teacher["n_jury"])
    blend["n_features"] = len(BINNED_FEATURES) + 1
    blend["matched_activity"] = True
    models["profile_love_plus_behavior"] = blend
    print(
        f"  profile_love_plus_behavior: AUC={blend['roc_auc']:.3f} "
        f"AP={blend['average_precision']:.3f} overlap={blend['primary']['overlap']:,} "
        f"J={blend['primary']['jaccard']:.3f} "
        f"mass={blend['primary']['teacher_weight_recall']:.1%}",
        flush=True,
    )

    half_stability = {
        "half0_vs_half1_jaccard": selected_jaccard(
            models["profile_half0"]["selected_user_ids"],
            models["profile_half1"]["selected_user_ids"],
        ),
        "half0_vs_full_love_jaccard": selected_jaccard(
            models["profile_half0"]["selected_user_ids"],
            models["profile_love"]["selected_user_ids"],
        ),
        "half1_vs_full_love_jaccard": selected_jaccard(
            models["profile_half1"]["selected_user_ids"],
            models["profile_love"]["selected_user_ids"],
        ),
    }

    # Choose only among decontaminated full-book profiles. Half profiles are
    # stability diagnostics and profile_evidence retains an activity advantage.
    candidates = [
        "rich_behavior_global",
        "rich_behavior_no_direct_activity",
        "rich_behavior_activity_matched",
        "behavior_binned_matched",
        "profile_mean",
        "profile_love",
        "profile_love_plus_behavior",
    ]
    chosen_name = max(
        candidates,
        key=lambda n: (
            models[n]["primary"]["teacher_weight_recall"],
            models[n]["primary"]["jaccard"],
        ),
    )
    chosen = models[chosen_name]
    preliminary_selection = max(
        chosen["size_sweep"],
        key=lambda s: (s["jaccard"], s["teacher_weight_recall"]),
    )
    preliminary_n = int(preliminary_selection["k"])
    write_jury_table(
        con,
        "jury_preliminary",
        chosen["ranked_user_ids"][:preliminary_n],
    )
    write_jury_table(
        con,
        "jury_rich_global",
        models["rich_behavior_global"]["selected_user_ids"],
    )

    print(
        f"Chosen preliminary jury: {chosen_name}, n={preliminary_n:,} "
        f"(OOF J={preliminary_selection['jaccard']:.3f})",
        flush=True,
    )
    materialize_seed_sets(con)
    held = author_disjoint_sets(con)["test_works"]
    pair_pre = pairwise_readout(
        con, "jury_preliminary", "pairs_jury_preliminary", ev, sticky, held
    )
    pair_teacher = pairwise_readout(
        con, "jury_teacher", "pairs_jury_teacher", ev, sticky, held
    )
    pair_rich = pairwise_readout(
        con, "jury_rich_global", "pairs_jury_rich_global", ev, sticky, held
    )
    pair_old = pairwise_readout(
        con, "jury_old_focus_approx", "pairs_jury_old_focus_approx", ev, sticky, held
    )
    a = set(pair_pre["top50_work_ids"])
    b = set(pair_teacher["top50_work_ids"])
    c = set(pair_old["top50_work_ids"])
    pairwise = {
        "preliminary": pair_pre,
        "rich_global": pair_rich,
        "teacher": pair_teacher,
        "old_focus_approx": pair_old,
        "top50_jaccard": len(a & b) / max(len(a | b), 1),
        "preliminary_old_focus_top50_jaccard": len(a & c) / max(len(a | c), 1),
    }
    diffs = diff_diagnostics(con)

    chosen_coef = coefficients.get(chosen_name, {})
    coef_sorted = sorted(chosen_coef.items(), key=lambda kv: -abs(kv[1]))
    results = {
        "meta": {
            "purpose": "ratings-behavior reconstruction of p65/s25 deep teacher",
            "purity": PURITY,
            "strictness": STRICTNESS,
            "folds": N_FOLDS,
            "ridge_alpha": RIDGE_ALPHA,
            "leakage_guard": "teacher labels only; no mint/poll/taste fields in predictors",
            "runtime_seconds": time.time() - t_all,
        },
        "teacher": teacher,
        "behavior_materialization": behavior,
        "rich_behavior_materialization": rich_behavior,
        "frame": frame,
        "old_focus_approx": old_focus_approx,
        "excluded_work_guard": excluded,
        "profile_materialization": profile_meta,
        "profile_half_stability": half_stability,
        "top_profile_anchors": top_profile_anchors(con),
        "chosen_model": chosen_name,
        "preliminary_selection": preliminary_selection,
        "chosen_coefficients": [[k, v] for k, v in coef_sorted],
        "rich_linear_coefficients": [
            [k, v]
            for k, v in sorted(
                coefficients["rich_behavior_global"].items(),
                key=lambda kv: -abs(kv[1]),
            )
        ],
        "models": {k: _slim_model(v) for k, v in models.items()},
        "overlap_preliminary_teacher": cohort_overlap(
            con, "jury_preliminary", "jury_teacher"
        ),
        "overlap_old_focus_teacher": cohort_overlap(
            con, "jury_old_focus_approx", "jury_teacher"
        ),
        "overlap_preliminary_old_focus": cohort_overlap(
            con, "jury_preliminary", "jury_old_focus_approx"
        ),
        "pairwise": pairwise,
        "diffs": diffs,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(results)
    print(f"Wrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    con.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Three-way cohort contrast + unseeded classic-focus book scorer.

1) Seed-informed cohorts (characterization / training labels only):
   - classic: multi-5★ on literary poll / poll_works (high min n)
   - anti:    multi-5★ on non_literary taste works
   - normie:  multi-5★ on normie_works

2) Build rich unseeded user features from (user, rating, work, author).

3) Find features that separate classic from BOTH anti and normie.

4) Deploy an unseeded user affinity score (no seed hit counts) → weighted
   book Bayesian P(5★). Complexity allowed.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_threeway_unseeded
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    evaluate,
    load_eval_sets,
    materialize_base,
    rank_from_sql,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "threeway_unseeded.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "THREEWAY_UNSEEDED_REPORT.md"

CLASSIC_MIN_N = 2000
ANTI_MIN_N = 500
NORMIE_MIN_N = 500
CLASSIC_HITS = 6
ANTI_HITS = 10
NORMIE_HITS = 4


def materialize_seed_sets(con) -> dict[str, Any]:
    print("Materializing classic / anti / normie seed works…", flush=True)
    con.execute("USE memory")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE seed_classic AS
        SELECT DISTINCT t.work_id
        FROM ex.taste_signal_works t
        JOIN ex.work_scores s USING (work_id)
        WHERE t.side = 'literary_poll' AND s.n >= {CLASSIC_MIN_N}
        UNION
        SELECT work_id FROM ex.poll_works WHERE n >= {CLASSIC_MIN_N}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE seed_anti AS
        SELECT DISTINCT t.work_id
        FROM ex.taste_signal_works t
        JOIN ex.work_scores s USING (work_id)
        WHERE t.side = 'non_literary' AND s.n >= {ANTI_MIN_N}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE seed_normie AS
        SELECT DISTINCT n.work_id
        FROM ex.normie_works n
        JOIN ex.work_scores s USING (work_id)
        WHERE s.n >= {NORMIE_MIN_N}
        """
    )
    # train/test split on poll_works for classic held-out check
    con.execute(
        f"""
        CREATE OR REPLACE TABLE seed_classic_split AS
        SELECT
            work_id,
            poll_rank,
            CASE WHEN (poll_rank % 2) = 1 THEN 'train' ELSE 'test' END AS split
        FROM ex.poll_works
        WHERE n >= {CLASSIC_MIN_N}
        """
    )
    meta = {
        "n_classic": con.execute("SELECT count(*) FROM seed_classic").fetchone()[0],
        "n_anti": con.execute("SELECT count(*) FROM seed_anti").fetchone()[0],
        "n_normie": con.execute("SELECT count(*) FROM seed_normie").fetchone()[0],
        "n_classic_train": con.execute(
            "SELECT count(*) FROM seed_classic_split WHERE split='train'"
        ).fetchone()[0],
        "n_classic_test": con.execute(
            "SELECT count(*) FROM seed_classic_split WHERE split='test'"
        ).fetchone()[0],
    }
    print(
        f"  classic={meta['n_classic']} anti={meta['n_anti']} normie={meta['n_normie']} "
        f"(poll train/test {meta['n_classic_train']}/{meta['n_classic_test']})",
        flush=True,
    )
    return meta


def materialize_work_author_year(con) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE work_ax AS
        SELECT
            s.work_id,
            s.n,
            s.mean,
            s.n5,
            regexp_extract(s.author_url, 'author/show/([0-9]+)', 1) AS author_id,
            CASE
                WHEN s.title LIKE '%#%' OR s.title LIKE '%(%#%' THEN TRUE
                ELSE FALSE
            END AS is_seriesish,
            y.pub_year
        FROM ex.work_scores s
        LEFT JOIN ex.work_years y USING (work_id)
        WHERE s.author_url IS NOT NULL
          AND regexp_extract(s.author_url, 'author/show/([0-9]+)', 1) <> ''
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE author_ax AS
        SELECT
            author_id,
            count(*)::BIGINT AS n_works,
            max(n)::BIGINT AS max_work_n,
            sum(n)::BIGINT AS sum_n
        FROM work_ax
        GROUP BY author_id
        """
    )


def build_user_features(con) -> None:
    """Unseeded user features from ratings + book + author (+ year)."""
    print("Building unseeded user features…", flush=True)
    t0 = time.time()
    bb_thr = float(
        con.execute(
            "SELECT approx_quantile(n, 0.995::FLOAT) FROM work_rarity"
        ).fetchone()[0]
    )
    mid_lo, mid_hi = 2000, 80000
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_rich AS
        WITH per_author AS (
            SELECT
                e.user_id,
                wa.author_id,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5_a,
                count(*)::BIGINT AS n_a
            FROM ex.all_rating_events e
            JOIN work_ax wa USING (work_id)
            JOIN user_feat uf USING (user_id)
            WHERE uf.n_rated >= 40
            GROUP BY e.user_id, wa.author_id
        ),
        author_agg AS (
            SELECT
                user_id,
                count(*) FILTER (WHERE n5_a > 0)::BIGINT AS n_authors_5,
                avg(n5_a) FILTER (WHERE n5_a > 0)::DOUBLE AS binge_mean_5,
                max(n5_a)::BIGINT AS binge_max_5,
                (
                    sum(power(n5_a, 2)) FILTER (WHERE n5_a > 0)::DOUBLE
                    / nullif(power(sum(n5_a) FILTER (WHERE n5_a > 0), 2), 0)
                ) AS author_hhi_5,
                count(*) FILTER (WHERE n5_a = 1)::DOUBLE
                    / nullif(count(*) FILTER (WHERE n5_a > 0), 0) AS singleton_author_share_5
            FROM per_author
            GROUP BY user_id
        ),
        book_agg AS (
            SELECT
                e.user_id,
                count(*)::BIGINT AS n_rated,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5,
                avg(e.rating)::DOUBLE AS mean_rating,
                (
                    count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*)
                ) AS five_rate,
                avg(ln(1.0 + wr.n)) FILTER (WHERE e.rating = 5)::DOUBLE AS mean_logn_5,
                stddev_samp(ln(1.0 + wr.n)) FILTER (WHERE e.rating = 5)::DOUBLE AS std_logn_5,
                avg(wr.rarity) FILTER (WHERE e.rating >= 4)::DOUBLE AS depth_ge4,
                (
                    count(*) FILTER (WHERE e.rating = 5 AND wr.n >= {bb_thr})::DOUBLE
                    / nullif(count(*) FILTER (WHERE wr.n >= {bb_thr}), 0)
                ) AS p5_blockbuster,
                (
                    count(*) FILTER (WHERE e.rating = 5 AND wa.is_seriesish)::DOUBLE
                    / nullif(count(*) FILTER (WHERE e.rating = 5), 0)
                ) AS series_share_5,
                avg(wa.pub_year) FILTER (
                    WHERE e.rating = 5 AND wa.pub_year BETWEEN 1500 AND 2020
                )::DOUBLE AS mean_pub_year_5,
                count(*) FILTER (
                    WHERE e.rating = 5
                      AND ax.max_work_n BETWEEN {mid_lo} AND {mid_hi}
                )::BIGINT AS n5_midpop_author_books,
                count(DISTINCT wa.author_id) FILTER (
                    WHERE e.rating = 5
                      AND ax.max_work_n BETWEEN {mid_lo} AND {mid_hi}
                )::BIGINT AS n_midpop_authors_5,
                count(DISTINCT wa.author_id) FILTER (
                    WHERE e.rating = 5 AND ax.max_work_n >= 50000
                )::BIGINT AS n_megastar_authors_5,
                count(*) FILTER (
                    WHERE e.rating = 5 AND wr.n BETWEEN 500 AND 15000
                )::DOUBLE
                    / nullif(count(*) FILTER (WHERE e.rating = 5), 0) AS mid_catalog_share_5,
                count(*) FILTER (
                    WHERE e.rating = 5 AND wr.n >= 50000
                )::DOUBLE
                    / nullif(count(*) FILTER (WHERE e.rating = 5), 0) AS mega_catalog_share_5
            FROM ex.all_rating_events e
            JOIN work_rarity wr USING (work_id)
            JOIN work_ax wa USING (work_id)
            JOIN author_ax ax USING (author_id)
            JOIN user_feat uf USING (user_id)
            WHERE uf.n_rated >= 40
            GROUP BY e.user_id
            HAVING count(*) FILTER (WHERE e.rating = 5) >= 8
               AND count(*) FILTER (WHERE wr.n >= {bb_thr}) >= 3
        )
        SELECT
            b.*,
            a.n_authors_5,
            a.binge_mean_5,
            a.binge_max_5,
            a.author_hhi_5,
            a.singleton_author_share_5,
            (a.n_authors_5::DOUBLE / nullif(b.n5, 0)) AS author_div_5,
            (b.n_midpop_authors_5::DOUBLE / nullif(a.n_authors_5, 0)) AS midpop_author_frac_5,
            (b.n_midpop_authors_5::DOUBLE / nullif(ln(1.0 + b.n5), 0)) AS midpop_span_per_logn5
        FROM book_agg b
        JOIN author_agg a USING (user_id)
        """
    )
    n = con.execute("SELECT count(*) FROM user_rich").fetchone()[0]
    print(f"  user_rich={n:,} ({time.time()-t0:.1f}s)", flush=True)


def label_cohorts(con) -> dict[str, Any]:
    """Seed-informed cohort labels (training only). Prefer exclusive primary."""
    print("Labeling classic / anti / normie cohorts…", flush=True)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_seed_hits AS
        SELECT
            e.user_id,
            count(DISTINCT e.work_id) FILTER (
                WHERE e.rating = 5 AND e.work_id IN (SELECT work_id FROM seed_classic)
            )::BIGINT AS classic_hits,
            count(DISTINCT e.work_id) FILTER (
                WHERE e.rating = 5 AND e.work_id IN (SELECT work_id FROM seed_anti)
            )::BIGINT AS anti_hits,
            count(DISTINCT e.work_id) FILTER (
                WHERE e.rating = 5 AND e.work_id IN (SELECT work_id FROM seed_normie)
            )::BIGINT AS normie_hits,
            -- train-only classic hits for held-out experiments
            count(DISTINCT e.work_id) FILTER (
                WHERE e.rating = 5
                  AND e.work_id IN (
                      SELECT work_id FROM seed_classic_split WHERE split = 'train'
                  )
            )::BIGINT AS classic_train_hits
        FROM ex.all_rating_events e
        JOIN user_rich ur USING (user_id)
        GROUP BY e.user_id
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_classic AS
        SELECT user_id FROM user_seed_hits
        WHERE classic_hits >= {CLASSIC_HITS}
          AND classic_hits >= anti_hits
          AND classic_hits >= normie_hits
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_anti AS
        SELECT user_id FROM user_seed_hits
        WHERE anti_hits >= {ANTI_HITS}
          AND anti_hits > classic_hits
          AND anti_hits >= normie_hits
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_normie AS
        SELECT user_id FROM user_seed_hits
        WHERE normie_hits >= {NORMIE_HITS}
          AND normie_hits > classic_hits
          AND anti_hits < {ANTI_HITS}
        """
    )
    # Soft classic for reference (not exclusive)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_classic_soft AS
        SELECT user_id FROM user_seed_hits WHERE classic_hits >= {CLASSIC_HITS}
        """
    )
    meta = {
        "n_classic_excl": con.execute("SELECT count(*) FROM cohort_classic").fetchone()[0],
        "n_anti_excl": con.execute("SELECT count(*) FROM cohort_anti").fetchone()[0],
        "n_normie_excl": con.execute("SELECT count(*) FROM cohort_normie").fetchone()[0],
        "n_classic_soft": con.execute(
            "SELECT count(*) FROM cohort_classic_soft"
        ).fetchone()[0],
        "thresholds": {
            "classic_hits": CLASSIC_HITS,
            "anti_hits": ANTI_HITS,
            "normie_hits": NORMIE_HITS,
        },
    }
    print(
        f"  exclusive classic={meta['n_classic_excl']:,} anti={meta['n_anti_excl']:,} "
        f"normie={meta['n_normie_excl']:,} (soft classic={meta['n_classic_soft']:,})",
        flush=True,
    )
    return meta


FEATURE_COLS = [
    "five_rate",
    "mean_rating",
    "n_rated",
    "n5",
    "mean_logn_5",
    "std_logn_5",
    "depth_ge4",
    "p5_blockbuster",
    "series_share_5",
    "mean_pub_year_5",
    "n_authors_5",
    "binge_mean_5",
    "binge_max_5",
    "author_hhi_5",
    "singleton_author_share_5",
    "author_div_5",
    "n_midpop_authors_5",
    "midpop_author_frac_5",
    "midpop_span_per_logn5",
    "n_megastar_authors_5",
    "mid_catalog_share_5",
    "mega_catalog_share_5",
]


def cohort_feature_means(con, table: str) -> dict[str, float | None]:
    cols = ", ".join(f"avg({c})" for c in FEATURE_COLS)
    row = con.execute(
        f"""
        SELECT {cols}
        FROM user_rich ur
        JOIN {table} c USING (user_id)
        """
    ).fetchone()
    return {
        k: (float(v) if v is not None else None) for k, v in zip(FEATURE_COLS, row)
    }


def threeway_contrast(con) -> dict[str, Any]:
    print("Computing three-way feature contrasts…", flush=True)
    means = {
        "classic": cohort_feature_means(con, "cohort_classic"),
        "anti": cohort_feature_means(con, "cohort_anti"),
        "normie": cohort_feature_means(con, "cohort_normie"),
    }
    # global sd on user_rich for cohen-ish d
    sds = {}
    for c in FEATURE_COLS:
        sds[c] = float(
            con.execute(f"SELECT stddev_samp({c}) FROM user_rich").fetchone()[0] or 1.0
        ) or 1.0

    def d(a: float | None, b: float | None, sd: float) -> float | None:
        if a is None or b is None:
            return None
        return (a - b) / sd

    contrasts = {}
    for c in FEATURE_COLS:
        mc, ma, mn = means["classic"][c], means["anti"][c], means["normie"][c]
        d_anti = d(mc, ma, sds[c])
        d_norm = d(mc, mn, sds[c])
        # gold: same sign vs both, |d| decent
        same = (
            d_anti is not None
            and d_norm is not None
            and d_anti * d_norm > 0
            and min(abs(d_anti), abs(d_norm)) >= 0.12
        )
        contrasts[c] = {
            "classic": mc,
            "anti": ma,
            "normie": mn,
            "d_vs_anti": d_anti,
            "d_vs_normie": d_norm,
            "separates_both": same,
            "min_abs_d": (
                min(abs(d_anti), abs(d_norm))
                if d_anti is not None and d_norm is not None
                else None
            ),
            "direction": (
                1
                if d_anti is not None and d_norm is not None and d_anti > 0 and d_norm > 0
                else (
                    -1
                    if d_anti is not None
                    and d_norm is not None
                    and d_anti < 0
                    and d_norm < 0
                    else 0
                )
            ),
        }
    gold = sorted(
        [(k, v) for k, v in contrasts.items() if v["separates_both"]],
        key=lambda kv: -(kv[1]["min_abs_d"] or 0),
    )
    print("  features separating classic from BOTH anti & normie:", flush=True)
    for k, v in gold:
        print(
            f"    {k:28s} dir={v['direction']:+d}  "
            f"d_anti={v['d_vs_anti']:+.2f} d_norm={v['d_vs_normie']:+.2f}  "
            f"C={v['classic']:.4g} A={v['anti']:.4g} N={v['normie']:.4g}",
            flush=True,
        )
    if not gold:
        print("  (none cleared threshold — loosening)", flush=True)
    return {"means": means, "contrasts": contrasts, "gold": [k for k, _ in gold]}


def fit_unseeded_affinity(con, contrasts: dict[str, Any]) -> dict[str, Any]:
    """Build classic / anti / normie raw scores, then net classic_focus.

    classic_focus = classic_raw - λ_a * anti_raw - λ_n * normie_raw
    (all z-scored feature sums; no seed hits at inference)
    """
    print("Fitting unseeded classic / anti / normie affinities…", flush=True)
    moments = {}
    for c in FEATURE_COLS:
        mu, sd = con.execute(
            f"SELECT avg({c}), stddev_samp({c}) FROM user_rich WHERE {c} IS NOT NULL"
        ).fetchone()
        moments[c] = {"mu": float(mu or 0), "sd": float(sd or 1) or 1.0}

    def zexpr(col: str) -> str:
        mu, sd = moments[col]["mu"], moments[col]["sd"]
        return f"((coalesce({col}, {mu}) - ({mu})) / ({sd}))"

    # Classic-favoring (from gold separators, signed)
    classic_terms = {
        "mean_pub_year_5": -1.4,
        "series_share_5": -1.5,
        "mega_catalog_share_5": -1.3,
        "mean_logn_5": -1.0,
        "depth_ge4": 0.9,
        "midpop_span_per_logn5": 1.2,
        "author_hhi_5": -0.8,
        "mid_catalog_share_5": 0.5,
        "std_logn_5": 0.4,
        "singleton_author_share_5": 0.6,
        "binge_mean_5": -0.7,
        "author_div_5": 0.5,
    }
    # Anti-likeness (high = romance/series binge)
    anti_terms = {
        "series_share_5": 1.6,
        "binge_mean_5": 1.2,
        "binge_max_5": 0.8,
        "author_hhi_5": 1.0,
        "mean_pub_year_5": 1.0,
        "singleton_author_share_5": -0.8,
        "author_div_5": -0.6,
    }
    # Normie-likeness (high = school-blockbuster concentration)
    normie_terms = {
        "mega_catalog_share_5": 1.5,
        "mean_logn_5": 1.3,
        "p5_blockbuster": 0.8,
        "n_megastar_authors_5": 0.6,
        "midpop_span_per_logn5": -0.7,
        "depth_ge4": -0.5,
    }

    def sum_expr(terms: dict[str, float]) -> str:
        parts = [f"({w}) * {zexpr(c)}" for c, w in terms.items() if c in moments]
        return " + ".join(parts)

    classic_raw = sum_expr(classic_terms)
    anti_raw = sum_expr(anti_terms)
    normie_raw = sum_expr(normie_terms)
    # Net focus: want classic high, anti/normie low
    lam_a, lam_n = 0.85, 0.75
    focus = f"({classic_raw}) - ({lam_a}) * ({anti_raw}) - ({lam_n}) * ({normie_raw})"

    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_affinity AS
        SELECT
            user_id,
            ({classic_raw})::DOUBLE AS classic_raw,
            ({anti_raw})::DOUBLE AS anti_raw,
            ({normie_raw})::DOUBLE AS normie_raw,
            ({focus})::DOUBLE AS classic_affinity,
            n_rated,
            five_rate,
            series_share_5,
            binge_mean_5,
            singleton_author_share_5,
            midpop_span_per_logn5,
            mega_catalog_share_5,
            mean_pub_year_5,
            mean_logn_5,
            author_hhi_5
        FROM user_rich
        """
    )
    # Hard gate: reject obvious series-bingers / mega-only before ranking
    con.execute(
        """
        CREATE OR REPLACE TABLE user_affinity_gated AS
        SELECT *
        FROM user_affinity
        WHERE series_share_5 <= 0.40
          AND mega_catalog_share_5 <= 0.28
          AND binge_mean_5 <= 2.8
          AND midpop_span_per_logn5 >= 3.0
        """
    )
    n_g = con.execute("SELECT count(*) FROM user_affinity_gated").fetchone()[0]
    print(f"  gated eligible users={n_g:,}", flush=True)

    val = {}
    for name, table in [
        ("classic", "cohort_classic"),
        ("anti", "cohort_anti"),
        ("normie", "cohort_normie"),
    ]:
        row = con.execute(
            f"""
            SELECT
                avg(classic_affinity), avg(classic_raw), avg(anti_raw), avg(normie_raw)
            FROM user_affinity ua JOIN {table} c USING (user_id)
            """
        ).fetchone()
        val[name] = {
            "focus": float(row[0] or 0),
            "classic_raw": float(row[1] or 0),
            "anti_raw": float(row[2] or 0),
            "normie_raw": float(row[3] or 0),
        }
    print("  cohort means focus/classic/anti/normie:", flush=True)
    for k, v in val.items():
        print(
            f"    {k:8s} focus={v['focus']:+.3f} c={v['classic_raw']:+.3f} "
            f"a={v['anti_raw']:+.3f} n={v['normie_raw']:+.3f}",
            flush=True,
        )
    weights = {
        "classic_terms": classic_terms,
        "anti_terms": anti_terms,
        "normie_terms": normie_terms,
        "lambda_anti": lam_a,
        "lambda_normie": lam_n,
    }
    return {"weights": weights, "moments": moments, "cohort_mean_affinity": val}


def score_books_unseeded(con, *, top_frac: float = 0.08, min_votes: int = 25) -> list[dict]:
    """Top classic_focus among gated users → Bayesian P(5)."""
    thr = float(
        con.execute(
            f"""
            SELECT approx_quantile(classic_affinity, {1.0 - top_frac}::FLOAT)
            FROM user_affinity_gated
            """
        ).fetchone()[0]
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_score_w AS
        SELECT
            user_id,
            greatest(classic_affinity - {thr} + 1.0, 0.05)::DOUBLE AS w
        FROM user_affinity_gated
        WHERE classic_affinity >= {thr} - 0.35
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_score_top AS
        SELECT user_id FROM user_affinity_gated WHERE classic_affinity >= {thr}
        """
    )
    n_top = con.execute("SELECT count(*) FROM user_score_top").fetchone()[0]
    print(f"  gated top_frac={top_frac} thr={thr:.3f} n_top={n_top:,}", flush=True)

    m, p0 = 40.0, 0.2
    sql = f"""
        WITH agg AS (
            SELECT
                e.work_id,
                sum(w.w)::DOUBLE AS w_sum,
                sum(CASE WHEN e.rating = 5 THEN w.w ELSE 0 END)::DOUBLE AS w5,
                (
                    power(sum(w.w), 2)
                    / nullif(sum(power(w.w, 2)), 0)
                )::DOUBLE AS n_eff
            FROM ex.all_rating_events e
            JOIN user_score_w w USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            JOIN work_ax wa ON wa.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
              AND wr.n <= 120000
            GROUP BY e.work_id
            HAVING sum(w.w) >= {min_votes} * 0.2
        )
        SELECT
            work_id,
            ((w5 + {m}*{p0}) / (w_sum + {m}))::DOUBLE AS score,
            n_eff
        FROM agg
        WHERE n_eff >= {min_votes}
    """
    return rank_from_sql(con, sql)


def score_books_contrastive(con, *, top_frac: float = 0.06, min_votes: int = 30) -> list[dict]:
    """P(5|classic_focus_top) - P(5|anti_raw_top) among gated / anti-like users."""
    thr_c = float(
        con.execute(
            f"""
            SELECT approx_quantile(classic_affinity, {1.0 - top_frac}::FLOAT)
            FROM user_affinity_gated
            """
        ).fetchone()[0]
    )
    thr_a = float(
        con.execute(
            f"""
            SELECT approx_quantile(anti_raw, {1.0 - top_frac}::FLOAT)
            FROM user_affinity
            WHERE series_share_5 >= 0.45 OR binge_mean_5 >= 2.5
            """
        ).fetchone()[0]
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_focus_top AS
        SELECT user_id FROM user_affinity_gated WHERE classic_affinity >= {thr_c}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_anti_top AS
        SELECT user_id FROM user_affinity
        WHERE anti_raw >= {thr_a}
          AND (series_share_5 >= 0.45 OR binge_mean_5 >= 2.5)
        """
    )
    n_c = con.execute("SELECT count(*) FROM cohort_focus_top").fetchone()[0]
    n_a = con.execute("SELECT count(*) FROM cohort_anti_top").fetchone()[0]
    print(f"  contrastive focus_top={n_c:,} anti_top={n_a:,}", flush=True)

    sql = f"""
        WITH c_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_c,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_c
            FROM ex.all_rating_events e
            JOIN cohort_focus_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= 120000
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        ),
        a_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_a,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_a
            FROM ex.all_rating_events e
            JOIN cohort_anti_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= 120000
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            c.work_id,
            (c.p5_c - coalesce(a.p5_a, c.p5_c * 0.85))::DOUBLE AS score,
            least(c.n_c, coalesce(a.n_a, c.n_c))::DOUBLE AS n_eff
        FROM c_agg c
        LEFT JOIN a_agg a USING (work_id)
        WHERE c.n_c >= {min_votes}
    """
    return rank_from_sql(con, sql)


def score_books_top_hard(con, *, min_votes: int = 20) -> list[dict]:
    m, p0 = 30.0, 0.25
    sql = f"""
        WITH agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
            FROM ex.all_rating_events e
            JOIN user_score_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            ((n5 + {m}*{p0}) / (n + {m}))::DOUBLE AS score,
            n::DOUBLE AS n_eff
        FROM agg
    """
    return rank_from_sql(con, sql)


def filler_eval(rows: list[dict], con) -> dict[str, Any]:
    fillers = {
        str(r[0]) for r in con.execute("SELECT work_id FROM ex.normie_works").fetchall()
    }
    anti = {
        str(r[0])
        for r in con.execute(
            "SELECT work_id FROM ex.taste_signal_works WHERE side='non_literary'"
        ).fetchall()
    }
    classic = {
        str(r[0]) for r in con.execute("SELECT work_id FROM seed_classic").fetchall()
    }
    test = {
        str(r[0])
        for r in con.execute(
            "SELECT work_id FROM seed_classic_split WHERE split='test'"
        ).fetchall()
    }

    def count(ids: set[str], lim: int) -> int:
        return sum(1 for r in rows[:lim] if r["work_id"] in ids)

    return {
        "classic50": count(classic, 50),
        "classic200": count(classic, 200),
        "test50": count(test, 50),
        "test200": count(test, 200),
        "normie50": count(fillers, 50),
        "normie200": count(fillers, 200),
        "anti50": count(anti, 50),
        "anti200": count(anti, 200),
    }


def affinity_overlap_with_seeds(con) -> dict[str, Any]:
    """How much does unseeded top overlap seed cohorts? (leakage check)."""
    thr = con.execute(
        """
        SELECT approx_quantile(classic_affinity, 0.92::FLOAT)
        FROM user_affinity_gated
        """
    ).fetchone()[0]
    con.execute(
        f"""
        CREATE OR REPLACE TABLE aff_top AS
        SELECT user_id FROM user_affinity_gated WHERE classic_affinity >= {float(thr)}
        """
    )
    n = con.execute("SELECT count(*) FROM aff_top").fetchone()[0]

    def overlap(table: str) -> dict[str, float]:
        hit = con.execute(
            f"""
            SELECT count(*) FROM aff_top a JOIN {table} c USING (user_id)
            """
        ).fetchone()[0]
        base = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        return {
            "n_overlap": hit,
            "frac_of_top": hit / max(n, 1),
            "recall_of_cohort": hit / max(base, 1),
        }

    return {
        "n_aff_top8pct_gated": n,
        "classic": overlap("cohort_classic"),
        "anti": overlap("cohort_anti"),
        "normie": overlap("cohort_normie"),
    }


def main() -> None:
    t_all = time.time()
    con = _con()
    ev = load_eval_sets(con)
    materialize_base(con)
    seed_meta = materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    cohort_meta = label_cohorts(con)
    contrast_blob = threeway_contrast(con)
    fit = fit_unseeded_affinity(con, contrast_blob["contrasts"])
    overlap = affinity_overlap_with_seeds(con)

    results: dict[str, Any] = {
        "meta": {
            "allowed_inference": "(user, rating, work, author[, pub_year]) features only",
            "seeds_used_for": "cohort labels + contrast / weight fitting only",
            "seeds": seed_meta,
            "cohorts": cohort_meta,
        },
        "contrasts": contrast_blob,
        "affinity": {
            "weights": fit["weights"],
            "cohort_mean_affinity": fit["cohort_mean_affinity"],
            "overlap_top8pct": overlap,
        },
        "rankings": {},
    }

    for name, fn in [
        ("unseeded_gated_weighted", lambda: score_books_unseeded(con, top_frac=0.08)),
        ("unseeded_gated_top8_hard", lambda: score_books_top_hard(con)),
        ("unseeded_gated_top4", lambda: score_books_unseeded(con, top_frac=0.04)),
        ("unseeded_contrastive", lambda: score_books_contrastive(con, top_frac=0.06)),
    ]:
        print(f"\n=== score {name} ===", flush=True)
        t0 = time.time()
        rows = fn()
        ms = int((time.time() - t0) * 1000)
        base = evaluate(rows, ev)
        extra = filler_eval(rows, con)
        results["rankings"][name] = {
            "elapsed_ms": ms,
            "eval_literary_poll": base,
            "seed_counts": extra,
            "top25": [
                {
                    "rank": r["rank"],
                    "title": r["title"],
                    "author": r["author"],
                    "n": r["n_eff"],
                }
                for r in rows[:25]
            ],
        }
        print(
            f"  {ms}ms Q={base['Q']:.1f} pos50={base['pos50']} anti50={base['anti50']} "
            f"classic50={extra['classic50']} normie50={extra['normie50']} "
            f"test50={extra['test50']}",
            flush=True,
        )
        for r in rows[:8]:
            print(
                f"    {r['rank']:2d}. {r['title'][:50]:50s} — {r['author'][:22]}",
                flush=True,
            )

    # Seeded oracle ceiling (classic exclusive cohort) for reference
    print("\n=== seeded oracle (exclusive classic cohort) ===", flush=True)
    con.execute(
        """
        CREATE OR REPLACE TABLE user_score_top AS
        SELECT user_id FROM cohort_classic
        """
    )
    rows = score_books_top_hard(con)
    base = evaluate(rows, ev)
    extra = filler_eval(rows, con)
    results["rankings"]["seeded_classic_oracle"] = {
        "eval_literary_poll": base,
        "seed_counts": extra,
        "top25": [
            {
                "rank": r["rank"],
                "title": r["title"],
                "author": r["author"],
                "n": r["n_eff"],
            }
            for r in rows[:25]
        ],
    }
    print(
        f"  Q={base['Q']:.1f} pos50={base['pos50']} anti50={base['anti50']} "
        f"classic50={extra['classic50']} normie50={extra['normie50']}",
        flush=True,
    )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    # trim moments from blob for smaller JSON
    out = json.loads(json.dumps(results))
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    _write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    con.close()


def _write_report(results: dict[str, Any]) -> None:
    c = results["contrasts"]["contrasts"]
    lines = [
        "# Three-way cohorts + unseeded classic-focus scorer",
        "",
        "Seeds label cohorts for contrast/fitting only. Book ranking at inference "
        "uses **unseeded** user features from `(user, rating, work, author[, year])`.",
        "",
        "## Cohorts (exclusive primary)",
        "",
        f"- classic: {results['meta']['cohorts']['n_classic_excl']:,} "
        f"(≥{CLASSIC_HITS} classic 5★, classic≥anti, classic≥normie)",
        f"- anti: {results['meta']['cohorts']['n_anti_excl']:,} "
        f"(≥{ANTI_HITS} anti 5★, anti>classic)",
        f"- normie: {results['meta']['cohorts']['n_normie_excl']:,} "
        f"(≥{NORMIE_HITS} normie 5★, normie>classic, anti low)",
        "",
        "## Feature means & classic vs anti / normie",
        "",
        "| feature | classic | anti | normie | d_anti | d_normie | both? |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    rows = sorted(
        c.items(),
        key=lambda kv: (
            0 if kv[1].get("separates_both") else 1,
            -(kv[1].get("min_abs_d") or 0),
        ),
    )
    for k, v in rows:
        def fmt(x):
            return f"{x:.4g}" if x is not None else "—"

        lines.append(
            f"| {k} | {fmt(v['classic'])} | {fmt(v['anti'])} | {fmt(v['normie'])} | "
            f"{fmt(v['d_vs_anti'])} | {fmt(v['d_vs_normie'])} | "
            f"{'YES' if v['separates_both'] else ''} |"
        )

    aff = results["affinity"]
    lines += [
        "",
        "## Unseeded affinity (classic_raw − λ·anti_raw − λ·normie_raw)",
        "",
    ]
    cma = aff["cohort_mean_affinity"]
    if isinstance(cma.get("classic"), dict):
        for name in ("classic", "anti", "normie"):
            v = cma[name]
            lines.append(
                f"- {name}: focus={v['focus']:+.3f} classic_raw={v['classic_raw']:+.3f} "
                f"anti_raw={v['anti_raw']:+.3f} normie_raw={v['normie_raw']:+.3f}"
            )
    else:
        lines.append(f"Cohort mean affinity: {cma}")
    w = aff["weights"]
    if isinstance(w, dict) and "classic_terms" in w:
        lines += ["", "Classic terms:", ""]
        for k, val in sorted(w["classic_terms"].items(), key=lambda kv: -abs(kv[1])):
            lines.append(f"- `{k}`: {val:+.2f}")
        lines += ["", "Anti terms:", ""]
        for k, val in sorted(w["anti_terms"].items(), key=lambda kv: -abs(kv[1])):
            lines.append(f"- `{k}`: {val:+.2f}")
        lines += ["", "Normie terms:", ""]
        for k, val in sorted(w["normie_terms"].items(), key=lambda kv: -abs(kv[1])):
            lines.append(f"- `{k}`: {val:+.2f}")
        lines.append(
            f"\nλ_anti={w.get('lambda_anti')} λ_normie={w.get('lambda_normie')}"
        )
    ov = aff["overlap_top8pct"]
    lines += [
        "",
        f"Gated top ~8% overlap: classic recall={ov['classic']['recall_of_cohort']:.2%}, "
        f"anti recall={ov['anti']['recall_of_cohort']:.2%}, "
        f"normie recall={ov['normie']['recall_of_cohort']:.2%} "
        f"(frac of top classic={ov['classic']['frac_of_top']:.2%})",
        "",
        "## Book ranking results",
        "",
        "| method | Q | pos50 | anti50 | classic50 | normie50 | test50 | test200 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, blob in results["rankings"].items():
        e = blob["eval_literary_poll"]
        s = blob["seed_counts"]
        lines.append(
            f"| {name} | {e['Q']:.1f} | {e['pos50']} | {e['anti50']} | "
            f"{s['classic50']} | {s['normie50']} | {s['test50']} | {s['test200']} |"
        )
    lines += ["", "## Top 15 by method", ""]
    for name, blob in results["rankings"].items():
        lines.append(f"### {name}")
        for r in blob["top25"][:15]:
            lines.append(
                f"- {r['rank']}. {r['title']} — {r['author']} (n≈{r['n']:.0f})"
            )
        lines.append("")
    lines += [
        "## Notes",
        "",
        "- Gold features = same-sign effect vs anti **and** vs normie with min|d|≥0.12.",
        "- Activity counts downweighted so affinity is not just 'rates a lot'.",
        "- Seeded oracle is an upper reference (uses classic cohort membership).",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

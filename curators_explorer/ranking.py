"""Single ranking template: metric × scale mode over a curator cohort."""

from __future__ import annotations

from typing import Any

from curators_explorer.catalog import (
    catalog_score_bits,
    eligible_works_cte,
    parse_catalog_params,
    parse_sf_only,
)
from curators_explorer.cohort import build_cohort_ctes, clamp01_100
from curators_explorer.db import GLOBALS, META, execute
from curators_explorer.taste_packs import get_active_pack

METRICS = [
    {
        "id": "love",
        "label": "Love",
        "blurb": "Percentile (or star) love mass among curator raters. Coverage fixed among-raters.",
    },
    {
        "id": "bayesian",
        "label": "Bayesian mean",
        "blurb": "RYM/IMDb-style shrink of cohort mean toward curator-scope prior.",
    },
    {
        "id": "mean",
        "label": "Raw mean",
        "blurb": "Weighted mean on the active scale (no Bayesian shrink).",
    },
    {
        "id": "top_rate",
        "label": "% top",
        "blurb": "Share of 5★ (stars mode) or top-shelf percentiles (pct modes).",
    },
    {
        "id": "reads",
        "label": "Curator reads",
        "blurb": "Kish effective rater count in the active curator cohort.",
    },
]

SCALE_MODES = [
    {
        "id": "adjusted",
        "label": "Adjusted percentiles",
        "blurb": "Lit-anchored Criticker midpoints when the user has enough positive-signal ratings; else full-shelf CDF.",
    },
    {
        "id": "raw_pct",
        "label": "Raw percentiles",
        "blurb": "Full-shelf Criticker midpoints from each user's entire rating hist.",
    },
    {
        "id": "stars",
        "label": "Raw stars",
        "blurb": "Goodreads 1–5 stars (love uses (★/5)^ρ).",
    },
]

PCT_LOVE_POWER = 3.2
PCT_PRIOR = 0.50
PCT_TOP_THRESH = 0.88
PCT_BOTTOM_THRESH = 0.25
# Fixed coverage = among-raters only (slider removed).
COVERAGE = 0.0
# Skip negligible deweighted voters in the ratings scan only; membership
# (n_curators) still counts everyone who passed purity gates.
WEIGHT_EVENT_EPS = 1e-9


def _int_param(params: dict[str, Any], *keys: str, default: int) -> int:
    for key in keys:
        if key not in params:
            continue
        val = params[key]
        if val is None or val == "":
            continue
        return int(val)
    return default


def _float_param(params: dict[str, Any], *keys: str, default: float) -> float:
    for key in keys:
        if key not in params:
            continue
        val = params[key]
        if val is None or val == "":
            continue
        return float(val)
    return default


def scope_globals(sf_only: bool) -> tuple[float, float]:
    if sf_only:
        p0 = float(GLOBALS.get("global_p5_sf", GLOBALS.get("global_p5", 0.4)))
        c0 = float(GLOBALS.get("global_mean_sf", GLOBALS.get("global_mean", 3.8)))
    else:
        p0 = float(GLOBALS.get("global_p5_all", GLOBALS.get("global_p5", 0.4)))
        c0 = float(GLOBALS.get("global_mean_all", GLOBALS.get("global_mean", 3.8)))
    return p0, c0


def _scale_value_sql(scale_mode: str) -> tuple[str, str, str]:
    """Return (join_sql, value_expr, top_pred) for one rating event alias e."""
    mode = (scale_mode or "adjusted").strip().lower()
    if mode not in ("adjusted", "raw_pct", "stars"):
        mode = "adjusted"

    if mode == "stars":
        # Normalize to [0,1] for love/mean consistency; top = 5★.
        return "", "(e.rating::DOUBLE / 5.0)", "(e.rating = 5)"

    if mode == "raw_pct":
        if not META.get("has_user_star_hist"):
            # Fallback to adjusted table.
            mode = "adjusted"
        else:
            join = "JOIN user_star_hist h ON h.user_id = e.user_id"
            # Criticker midpoints from full-shelf hist.
            val = """
                CASE e.rating
                    WHEN 1 THEN ((0.0 + (h.c1::DOUBLE / h.n_rated)) / 2.0)
                    WHEN 2 THEN (
                        ((h.c1::DOUBLE / h.n_rated)
                         + ((h.c1 + h.c2)::DOUBLE / h.n_rated)) / 2.0
                    )
                    WHEN 3 THEN (
                        (((h.c1 + h.c2)::DOUBLE / h.n_rated)
                         + ((h.c1 + h.c2 + h.c3)::DOUBLE / h.n_rated)) / 2.0
                    )
                    WHEN 4 THEN (
                        (((h.c1 + h.c2 + h.c3)::DOUBLE / h.n_rated)
                         + ((h.c1 + h.c2 + h.c3 + h.c4)::DOUBLE / h.n_rated)) / 2.0
                    )
                    WHEN 5 THEN (
                        (((h.c1 + h.c2 + h.c3 + h.c4)::DOUBLE / h.n_rated) + 1.0) / 2.0
                    )
                    ELSE 0.5
                END
            """
            top = f"(({val}) >= {PCT_TOP_THRESH})"
            return join, val, top

    # adjusted
    join = "JOIN user_star_percentiles p ON p.user_id = e.user_id"
    val = """
        CASE e.rating
            WHEN 1 THEN p.pct_1
            WHEN 2 THEN p.pct_2
            WHEN 3 THEN p.pct_3
            WHEN 4 THEN p.pct_4
            WHEN 5 THEN p.pct_5
            ELSE 0.5
        END
    """
    top = f"(({val}) >= {PCT_TOP_THRESH})"
    return join, val, top


def _score_sql(metric: str, *, m: float, prior_mean: float, prior_top: float) -> str:
    """Among-raters score expressions (coverage fixed at 0)."""
    metric = (metric or "love").strip().lower()
    if metric == "reads":
        return "agg.n"
    if metric == "mean":
        return "(agg.w_rating_sum / nullif(agg.w_sum, 0))"
    if metric == "top_rate":
        return (
            f"((agg.w_top + ({m})::DOUBLE * ({prior_top})::DOUBLE)"
            f" / (agg.w_sum + ({m})::DOUBLE))"
        )
    if metric == "bayesian":
        return (
            f"((agg.w_sum / (agg.w_sum + ({m})::DOUBLE))"
            f" * (agg.w_rating_sum / nullif(agg.w_sum, 0))"
            f" + (({m})::DOUBLE / (agg.w_sum + ({m})::DOUBLE)) * ({prior_mean})::DOUBLE)"
        )
    # love (default): mass / (w_sum + m), among-raters; prior mass at PCT_PRIOR
    rp = PCT_LOVE_POWER
    mass = f"(agg.w_love + ({m})::DOUBLE * power(({PCT_PRIOR})::DOUBLE, {rp}))"
    return f"(({mass}) / (coalesce(agg.w_sum, 0) + ({m})::DOUBLE))"


def _book_filter_sql(q: str, alias: str = "w") -> tuple[str, list[Any]]:
    if not q:
        return "", []
    like = f"%{q}%"
    return (
        f" AND ({alias}.title ILIKE ? OR {alias}.author ILIKE ?"
        f" OR {alias}.book_id = ? OR {alias}.work_id = ?)",
        [like, like, q, q],
    )


def _rows_to_results(rows: list) -> list[dict[str, Any]]:
    results = []
    for i, row in enumerate(rows, start=1):
        (
            work_id,
            book_id,
            title,
            author,
            book_url,
            n,
            mean,
            std,
            n5,
            n1,
            p5,
            p_low,
            pol,
            score,
        ) = row
        results.append(
            {
                "rank": i,
                "work_id": work_id,
                "book_id": book_id,
                "title": title,
                "author": author,
                "book_url": book_url,
                "n": int(n) if n is not None else 0,
                "n5": int(n5) if n5 is not None else 0,
                "n1": int(n1) if n1 is not None else 0,
                "mean": float(mean) if mean is not None else None,
                "std": float(std) if std is not None else None,
                "p5": float(p5) if p5 is not None else None,
                "p_low": float(p_low) if p_low is not None else None,
                "polarization": float(pol) if pol is not None else None,
                "score": float(score) if score is not None else 0.0,
                "votes": int(n) if n is not None else 0,
            }
        )
    return results


def rank_books(params: dict[str, Any]) -> dict[str, Any]:
    metric = str(params.get("metric") or params.get("method") or "love").strip().lower()
    if metric.startswith("curator_"):
        # Back-compat aliases from legacy method ids.
        if "love" in metric:
            metric = "love"
        elif "mean" in metric:
            metric = "bayesian"
        elif "five" in metric or "top" in metric:
            metric = "top_rate"
        else:
            metric = "love"
    if metric not in {m["id"] for m in METRICS}:
        metric = "love"

    scale_mode = str(params.get("scale_mode") or "adjusted").strip().lower()
    if scale_mode not in {s["id"] for s in SCALE_MODES}:
        scale_mode = "adjusted"

    min_n = max(1, _int_param(params, "min_votes", "min_n", default=25))
    max_n = max(0, _int_param(params, "max_n", default=0))
    bayesian_m = max(0.0, _float_param(params, "bayesian_m", "m", default=30.0))
    limit = max(1, min(2000, _int_param(params, "limit", default=200)))
    q = str(params.get("q") or "").strip()

    deweight = clamp01_100(_float_param(params, "deweight", "curator_deweight", default=15.0))
    purity = clamp01_100(
        _float_param(params, "purity", "normie_purity", default=55.0)
    )

    sf_only = parse_sf_only(params)
    catalog = parse_catalog_params(params)
    p0, c0 = scope_globals(sf_only)

    pack = params.get("pack")
    if not isinstance(pack, dict):
        pack = get_active_pack()

    cohort_ctes, cohort_args, cohort_meta = build_cohort_ctes(
        deweight=deweight, purity=purity, pack=pack
    )

    early = eligible_works_cte(sf_only=sf_only, catalog=catalog)
    works_join = "JOIN eligible_works ew USING (work_id)" if early else ""

    scale_join, scale_val, top_pred = _scale_value_sql(scale_mode)
    love_expr = f"power(greatest(({scale_val}), 1e-9), {PCT_LOVE_POWER})"

    # Prior for bayesian / top_rate depends on scale.
    if scale_mode == "stars":
        prior_mean = c0 / 5.0  # scores on [0,1]
        prior_top = p0
    else:
        prior_mean = PCT_PRIOR
        prior_top = 0.15

    score_expr = _score_sql(
        metric, m=bayesian_m, prior_mean=prior_mean, prior_top=prior_top
    )
    soft_join, soft_where, scored = catalog_score_bits(catalog, score_expr, work_alias="w")

    ctes: list[str] = []
    args: list[Any] = list(cohort_args)
    if early:
        ctes.append(early)
    ctes.extend(cohort_ctes)
    ctes.append(
        """
            curator_cohort AS (
                SELECT coalesce(sum(w), 0)::DOUBLE AS W
                FROM curator_active
            )
        """
    )
    ctes.append(
        f"""
            filtered AS (
                SELECT
                    e.work_id,
                    e.user_id,
                    e.rating,
                    c.w AS curator_weight,
                    ({scale_val})::DOUBLE AS scale_val,
                    ({love_expr})::DOUBLE AS love_val,
                    CASE WHEN {top_pred} THEN 1.0 ELSE 0.0 END AS is_top
                FROM all_rating_events e
                JOIN curator_active c USING (user_id)
                {scale_join}
                {works_join}
                WHERE e.rating BETWEEN 1 AND 5
                  AND c.w > {WEIGHT_EVENT_EPS}
            )
        """
    )
    ctes.append(
        """
            agg AS (
                SELECT
                    work_id,
                    count(*)::BIGINT AS n_raw,
                    sum(curator_weight)::DOUBLE AS w_sum,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                    )::DOUBLE AS n,
                    sum(curator_weight * scale_val)::DOUBLE AS w_rating_sum,
                    sum(curator_weight * love_val)::DOUBLE AS w_love,
                    sum(curator_weight * is_top)::DOUBLE AS w_top,
                    sum(CASE WHEN rating = 5 THEN curator_weight ELSE 0 END)::DOUBLE AS w_five,
                    sum(CASE WHEN rating = 1 THEN curator_weight ELSE 0 END)::DOUBLE AS w_one,
                    (
                        sum(curator_weight * scale_val) / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS mean,
                    stddev_pop(scale_val)::DOUBLE AS std,
                    (
                        sum(curator_weight * is_top) / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS p5,
                    (
                        sum(
                            CASE WHEN scale_val <= {bot}
                                 THEN curator_weight ELSE 0 END
                        ) / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS p_low,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(curator_weight * is_top)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n5,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(CASE WHEN rating = 1 THEN curator_weight ELSE 0 END)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n1
                FROM filtered
                GROUP BY work_id
            )
        """.replace("{bot}", str(PCT_BOTTOM_THRESH))
    )

    book_sql, book_args = _book_filter_sql(q, alias="w")
    max_clause = "AND agg.n <= ?" if max_n > 0 else ""
    max_args: list[Any] = [max_n] if max_n > 0 else []

    with_sql = ",\n".join(ctes)
    sql = f"""
        WITH {with_sql}
        SELECT
            w.work_id, w.book_id, w.title, w.author, w.book_url,
            agg.n, agg.mean, agg.std, agg.n5, agg.n1, agg.p5, agg.p_low,
            (coalesce(agg.p5, 0) + coalesce(agg.p_low, 0)) AS polarization,
            ({scored}) AS score
        FROM agg
        JOIN works w USING (work_id)
        {soft_join}
        WHERE agg.n >= ?
          {max_clause}
          {soft_where}
          {book_sql}
        ORDER BY score DESC NULLS LAST, agg.n DESC
        LIMIT ?
    """
    args.extend([min_n] + max_args + book_args + [limit])

    rows = execute(sql, args).fetchall()
    results = _rows_to_results(rows)

    # Cohort size readout
    n_curators = execute(
        f"WITH {',\n'.join(cohort_ctes)} SELECT count(*) FROM curator_active",
        cohort_args,
    ).fetchone()[0]

    return {
        "results": results,
        "n_results": len(results),
        "params": {
            "metric": metric,
            "scale_mode": scale_mode,
            "deweight": deweight,
            "purity": purity,
            "min_votes": min_n,
            "max_n": max_n,
            "bayesian_m": bayesian_m,
            "limit": limit,
            "sf_only": sf_only,
            "coverage": COVERAGE,
            "catalog": catalog,
            "q": q,
        },
        "cohort": {**cohort_meta, "n_curators": int(n_curators or 0)},
        "globals": {"p5": p0, "mean": c0},
    }

#!/usr/bin/env python3
"""Similar-books via curator-weighted 5★ co-fan overlap.

Only users in the active curator cohort (with their ranking weights) contribute.
Cohort follows the current ranking method when it is a curator method; otherwise
defaults to deep curators (or pct / star fallbacks).

Algorithms (weighted analogues of the fan measures):

* cosine — Σw∩ / sqrt(Wa·Wb)
* jaccard — Σw∩ / (Wa + Wb − Σw∩)
* lift — Σw∩ · N / (n_a · n_b) using rating counts
* pmi — log( Σw∩ · N_curators / (Wa · Wb) )
* conditional — Σw∩ / Wa
* association — conditional × idf
"""

from __future__ import annotations

from typing import Any

from ucsd_explorer.db import execute, resolve_work_id, truthy
from ucsd_explorer.genre_gates import gate_sql_bits, parse_genre_gates
from ucsd_explorer.genres import genre_sql_bits, parse_genre_params
from ucsd_explorer.ranking import (
    CURATOR_DEEP_PCT_METHODS,
    CURATOR_METHODS,
    CURATOR_PCT_FAMILY,
    CURATOR_PCT_METHODS,
    CURATOR_PURE_PCT_METHODS,
    CURATOR_PURE_STAR_METHODS,
    CURATOR_TILT_METHODS,
    _clamp_strictness,
    _curator_user_weight_sql,
    _float_param,
    curator_elite_keep_expr,
)
from ucsd_explorer.taste_query import (
    has_curator_deep_weights,
    has_curator_pct_pure_weights,
    has_curator_pct_weights,
    has_curator_pure_weights,
    has_curator_weights,
)

SIM_METHODS = [
    {
        "id": "cosine",
        "name": "Cosine (curators)",
        "blurb": "Σw∩ / √(Wa·Wb) over curator-weighted five-starrers.",
    },
    {
        "id": "jaccard",
        "name": "Jaccard (curators)",
        "blurb": "Σw∩ / (Wa + Wb − Σw∩). Weighted fanbase overlap.",
    },
    {
        "id": "lift",
        "name": "Approx. lift (curators)",
        "blurb": "Σw∩·N / (n_a·n_b). Shared curator favorites vs rating volume.",
    },
    {
        "id": "pmi",
        "name": "PMI (curators)",
        "blurb": "log( Σw∩·N_c / (Wa·Wb) ) on the curator cohort.",
    },
    {
        "id": "conditional",
        "name": "P(B⋆⋆⋆⋆⋆ | A⋆⋆⋆⋆⋆) curators",
        "blurb": "Share of A’s curator five-starrers (by weight) who also 5★ B.",
    },
    {
        "id": "association",
        "name": "Association (cond. × IDF)",
        "blurb": "P(B|A) · log(N_c/Wb). Down-weights ubiquitous co-favorites.",
    },
]


def _curator_cohort_for_sim(params: dict[str, Any]) -> dict[str, Any]:
    """Pick curator table + weight SQL matching ranking when possible."""
    method = params.get("method") or "curator_deep_pct_love"
    if method not in CURATOR_METHODS:
        # Non-curator ranking → still use deep/pct curators for similarity
        if has_curator_deep_weights():
            method = "curator_deep_pct_love"
        elif has_curator_pct_weights():
            method = "curator_pct_love"
        elif has_curator_weights():
            method = "curator_five_rate"
        else:
            raise ValueError(
                "Curator weights missing. Run: .venv/bin/python -m ucsd_explorer.taste"
            )

    use_deep = method in CURATOR_DEEP_PCT_METHODS
    use_pct = method in CURATOR_PCT_FAMILY
    if use_deep:
        if not has_curator_deep_weights():
            raise ValueError("Deep curator tables missing.")
        table = "user_curator_deep_weight"
    elif method in CURATOR_PURE_PCT_METHODS:
        if not has_curator_pct_pure_weights():
            raise ValueError("Pure pct curator tables missing.")
        table = "user_curator_pct_pure_weight"
    elif method in CURATOR_PCT_METHODS | CURATOR_TILT_METHODS:
        if not has_curator_pct_weights():
            raise ValueError("Percentile curator tables missing.")
        table = "user_curator_pct_weight"
    elif method in CURATOR_PURE_STAR_METHODS:
        if not has_curator_pure_weights():
            raise ValueError("Pure curator tables missing.")
        table = "user_curator_pure_weight"
    else:
        if not has_curator_weights():
            raise ValueError("Curator weights missing.")
        table = "user_curator_weight"

    strictness = _clamp_strictness(
        _float_param(params, "curator_strictness", default=0.0)
    )
    mode = (params.get("curator_strictness_mode") or "deweight").strip().lower()
    if mode not in ("deweight", "gate"):
        mode = "deweight"
    normie_depth = _clamp_strictness(_float_param(params, "normie_depth", default=0.0))
    normie_purity = _clamp_strictness(_float_param(params, "normie_purity", default=0.0))
    personal_power = truthy(params.get("personal_power"))
    comedy_cap = truthy(params.get("comedy_cap"))

    weight_expr, gate_sql, gate_args, elite_t = _curator_user_weight_sql(
        pct=use_pct or use_deep,
        mode=mode,
        strictness=strictness,
        deep=use_deep,
        normie_depth=normie_depth,
        normie_purity=normie_purity,
        personal_power=bool(personal_power) if use_deep else False,
        comedy_cap=bool(comedy_cap) if use_deep else False,
    )
    wcol = "curator_pct_weight" if (use_pct or use_deep) else "curator_weight"
    keep_expr = curator_elite_keep_expr(strictness, "n_pass")
    return {
        "method": method,
        "table": table,
        "weight_expr": weight_expr,
        "gate_sql": gate_sql,
        "gate_args": gate_args,
        "elite_t": elite_t,
        "keep_expr": keep_expr,
        "wcol": wcol,
        "strictness": strictness,
        "label": table.replace("user_", "").replace("_", " "),
    }


def similar_books(book_id: str, params: dict[str, Any]) -> dict[str, Any]:
    method = params.get("sim_method") or "cosine"
    limit = min(max(1, int(params["limit"]) if params.get("limit") not in (None, "") else 40), 200)
    # Prefer sim_limit when nested under book detail
    if params.get("sim_limit") not in (None, ""):
        limit = min(max(1, int(params["sim_limit"])), 200)
    min_both = max(1, int(params["min_both"]) if params.get("min_both") not in (None, "") else 2)

    cohort = _curator_cohort_for_sim(params)
    genres = parse_genre_params(params)
    genre_gates = parse_genre_gates(params)
    gate_where, gate_args = gate_sql_bits(genre_gates, work_alias="s")
    genre_where, genre_args = genre_sql_bits(
        genres, work_alias="s", sf_via_prevalence=not bool(genre_gates)
    )
    genre_where = f"{gate_where}{genre_where}"
    genre_args = gate_args + genre_args

    resolved = resolve_work_id(book_id)
    if not resolved:
        return {"error": "not found"}
    work_id, _ = resolved
    seed = execute(
        """
        SELECT work_id, book_id, title, author, book_url, n, n5
        FROM work_scores
        WHERE work_id = ?
        """,
        [work_id],
    ).fetchone()
    if not seed:
        return {"error": "not found"}

    work_id, bid, title, author, book_url, n_a, n5_a = seed
    n5_a = int(n5_a or 0)
    n_a = int(n_a or 0)

    table = cohort["table"]
    weight_expr = cohort["weight_expr"]
    gate_sql = cohort["gate_sql"]
    gate_args = list(cohort["gate_args"])
    wcol = cohort["wcol"]
    keep_expr = cohort["keep_expr"]

    # Active curator cohort with effective weights
    curator_cte = f"""
        curator_pool AS (
            SELECT c.*,
                row_number() OVER (ORDER BY c.{wcol} DESC) AS elite_rank,
                count(*) OVER () AS n_pass
            FROM {table} c
            WHERE TRUE {gate_sql}
        ),
        curator_active AS (
            SELECT
                user_id,
                ({weight_expr})::DOUBLE AS w
            FROM curator_pool c
            WHERE elite_rank <= {keep_expr}
              AND ({weight_expr}) > 0
        )
    """

    # Population of active curators
    n_curators = int(
        execute(
            f"""
            WITH {curator_cte}
            SELECT count(*) FROM curator_active
            """,
            gate_args,
        ).fetchone()[0]
    )

    score_expr = {
        "cosine": "c.both_mass / nullif(sqrt(sm.mass * coalesce(mb.mass_b, c.both_mass)), 0)",
        "jaccard": (
            "c.both_mass / nullif(sm.mass + coalesce(mb.mass_b, 0) - c.both_mass, 0)"
        ),
        "lift": f"c.both_mass * ({n_curators})::DOUBLE / nullif(({n_a})::DOUBLE * s.n::DOUBLE, 0)",
        "pmi": (
            f"ln(greatest(c.both_mass * ({n_curators})::DOUBLE"
            f" / nullif(sm.mass * coalesce(mb.mass_b, c.both_mass), 0), 1e-12))"
        ),
        "conditional": "c.both_mass / nullif(sm.mass, 0)",
        "association": (
            f"(c.both_mass / nullif(sm.mass, 0))"
            f" * ln(({n_curators})::DOUBLE / nullif(coalesce(mb.mass_b, c.both_mass), 0))"
        ),
    }.get(method)
    if score_expr is None:
        raise ValueError(f"unknown sim_method {method}")

    need_mass_b = method in ("cosine", "jaccard", "pmi", "association")
    mass_b_cte = ""
    mass_b_join = ""
    if need_mass_b:
        mass_b_cte = """,
        mass_b AS (
            SELECT e.work_id, sum(ca.w)::DOUBLE AS mass_b
            FROM five_star_events e
            JOIN co c USING (work_id)
            JOIN curator_active ca USING (user_id)
            GROUP BY e.work_id
        )"""
        mass_b_join = "LEFT JOIN mass_b mb USING (work_id)"

    sql = f"""
        WITH {curator_cte},
        fans AS (
            SELECT f.user_id, ca.w
            FROM five_star_events f
            JOIN curator_active ca USING (user_id)
            WHERE f.work_id = ?
        ),
        seed_mass AS (
            SELECT count(*)::BIGINT AS n_fans, coalesce(sum(w), 0)::DOUBLE AS mass
            FROM fans
        ),
        co AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS both,
                sum(fans.w)::DOUBLE AS both_mass
            FROM five_star_events e
            JOIN fans USING (user_id)
            WHERE e.work_id != ?
            GROUP BY e.work_id
            HAVING count(*) >= ?
        )
        {mass_b_cte}
        SELECT
            s.work_id, s.book_id, s.title, s.author, s.book_url,
            s.n, s.n5, c.both, c.both_mass,
            {score_expr} AS score
        FROM co c
        JOIN seed_mass sm ON TRUE
        JOIN work_scores s USING (work_id)
        {mass_b_join}
        WHERE TRUE{genre_where}
        ORDER BY score DESC NULLS LAST, c.both DESC
        LIMIT ?
    """

    args = list(gate_args) + [work_id, work_id, min_both] + genre_args + [limit]
    rows = execute(sql, args).fetchall()

    # Seed curator fan mass for the response
    seed_fans = execute(
        f"""
        WITH {curator_cte},
        fans AS (
            SELECT f.user_id, ca.w
            FROM five_star_events f
            JOIN curator_active ca USING (user_id)
            WHERE f.work_id = ?
        )
        SELECT count(*), coalesce(sum(w), 0) FROM fans
        """,
        gate_args + [work_id],
    ).fetchone()
    n_seed_curators = int(seed_fans[0] or 0)
    seed_mass = float(seed_fans[1] or 0)

    results = []
    for i, r in enumerate(rows, start=1):
        results.append(
            {
                "rank": i,
                "work_id": r[0],
                "book_id": r[1],
                "title": r[2],
                "author": r[3],
                "book_url": r[4],
                "n": int(r[5]),
                "n5": int(r[6]),
                "both_fans": int(r[7]),
                "both_mass": float(r[8]) if r[8] is not None else 0.0,
                "score": float(r[9]) if r[9] is not None else 0.0,
            }
        )

    note = None
    if n_seed_curators < 1:
        note = "No curator five-starrers for this book under the current cohort."
        results = []

    return {
        "seed": {
            "work_id": work_id,
            "book_id": bid,
            "title": title,
            "author": author,
            "book_url": book_url,
            "n": n_a,
            "n5": n5_a,
            "curator_fans": n_seed_curators,
            "curator_mass": seed_mass,
        },
        "method": method,
        "curator_cohort": cohort["label"],
        "curator_method": cohort["method"],
        "n_curators": n_curators,
        "genres": genres,
        "min_both": min_both,
        "n_results": len(results),
        "methods": SIM_METHODS,
        "results": results,
        "note": note,
        "lit_weighted": False,  # obsolete; always curator-weighted now
    }

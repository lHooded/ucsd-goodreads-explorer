#!/usr/bin/env python3
"""Similar-books via 5★ co-fan overlap.

Algorithms (all symmetric except conditional):

* cosine — |F∩| / sqrt(|Fa|·|Fb|)  (industry CF default)
* jaccard — |F∩| / |F∪|
* lift — |F∩|·N / (Wa·Wb) using rating counts as watches (from Gemini notes)
* pmi — log( |F∩|·N_fans / (|Fa|·|Fb|) ) on the fan population
* conditional — |F∩| / |Fa|  (“of A’s fans, who also 5★ B”; asymmetric)
* association — conditional × idf = (|F∩|/|Fa|) · log(N_fans / |Fb|)

Optional literary weighting: each co-fan contributes their lit_weight instead of 1.
"""

from __future__ import annotations

from typing import Any

from ucsd_explorer.db import execute, resolve_work_id
from ucsd_explorer.ranking import parse_sf_only
from ucsd_explorer.taste_query import has_lit_weights

SIM_METHODS = [
    {
        "id": "cosine",
        "name": "Cosine (fans)",
        "blurb": "|F∩| / √(|Fa|·|Fb|). Best default for “liked A also liked B”.",
    },
    {
        "id": "jaccard",
        "name": "Jaccard (fans)",
        "blurb": "|F∩| / |F∪|. Pure fanbase overlap.",
    },
    {
        "id": "lift",
        "name": "Approx. lift (fans / watches)",
        "blurb": "|F∩|·N / (Wa·Wb). Rewards shared favorites relative to how often both were rated.",
    },
    {
        "id": "pmi",
        "name": "PMI (fans)",
        "blurb": "log( |F∩|·N₅ / (|Fa|·|Fb|) ). Pointwise mutual information on five-starrers.",
    },
    {
        "id": "conditional",
        "name": "P(B⋆⋆⋆⋆⋆ | A⋆⋆⋆⋆⋆)",
        "blurb": "Share of A’s five-starrers who also five-starred B. Asymmetric.",
    },
    {
        "id": "association",
        "name": "Association (cond. × IDF)",
        "blurb": "P(B|A) · log(N₅/|Fb|). Down-weights ubiquitous co-favorites.",
    },
]


def similar_books(book_id: str, params: dict[str, Any]) -> dict[str, Any]:
    method = params.get("sim_method") or params.get("method") or "cosine"
    limit = min(max(1, int(params["limit"]) if params.get("limit") not in (None, "") else 40), 200)
    min_both = max(1, int(params["min_both"]) if params.get("min_both") not in (None, "") else 3)
    use_lit = str(params.get("lit_weighted") or "").lower() in ("1", "true", "yes", "on")
    sf_only = parse_sf_only(params)

    if use_lit and not has_lit_weights():
        raise ValueError("Literary weights missing. Run: .venv/bin/python -m ucsd_explorer.taste")

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
    if n5_a < 1:
        return {
            "seed": _seed_dict(seed),
            "method": method,
            "lit_weighted": use_lit,
            "sf_only": sf_only,
            "results": [],
            "note": "No five-star events for this book.",
        }

    sf_ev = " AND is_sf" if sf_only else ""
    sf_join = " AND s.is_sf" if sf_only else ""

    # Population sizes for lift / PMI (scoped)
    n_users = int(
        execute(
            f"SELECT count(DISTINCT user_id) FROM all_rating_events WHERE TRUE{sf_ev}"
        ).fetchone()[0]
    )
    n_fan_users = int(
        execute(
            f"SELECT count(DISTINCT user_id) FROM five_star_events WHERE TRUE{sf_ev}"
        ).fetchone()[0]
    )

    if use_lit:
        co = """
            WITH fans AS (
                SELECT f.user_id, coalesce(w.lit_weight, 0)::DOUBLE AS wt
                FROM five_star_events f
                LEFT JOIN user_lit_weight w USING (user_id)
                WHERE f.work_id = ?
                  AND coalesce(w.lit_weight, 0) > 0
            ),
            seed_mass AS (
                SELECT count(*)::BIGINT AS n_fans, sum(wt)::DOUBLE AS mass
                FROM fans
            ),
            co AS (
                SELECT
                    e.work_id,
                    count(*)::BIGINT AS both,
                    sum(fans.wt)::DOUBLE AS both_mass
                FROM five_star_events e
                JOIN fans USING (user_id)
                WHERE e.work_id != ?
                GROUP BY e.work_id
                HAVING count(*) >= ?
            )
        """
        # For lit-weighted cosine use both_mass / sqrt(seed_mass * other_mass)
        # Approximate other mass via joining user_lit_weight on B's fans — expensive.
        # Faster proxy: use both_mass / sqrt(seed_mass * n5_b) with unit fans on B,
        # or compute other_mass only for candidates.
        score_expr = {
            "cosine": "c.both_mass / nullif(sqrt(sm.mass * greatest(c.both_mass, c.both)), 0)",
            # Better lit cosine: need mass_b. Compute via subquery.
            "jaccard": "c.both_mass / nullif(sm.mass + c.both_mass - c.both_mass, 0)",  # weak
            "lift": f"c.both_mass * ({n_users})::DOUBLE / nullif(({n_a})::DOUBLE * s.n::DOUBLE, 0)",
            "pmi": f"ln(greatest(c.both_mass * ({n_fan_users})::DOUBLE / nullif(sm.mass * s.n5::DOUBLE, 0), 1e-12))",
            "conditional": "c.both_mass / nullif(sm.mass, 0)",
            "association": f"(c.both_mass / nullif(sm.mass, 0)) * ln(({n_fan_users})::DOUBLE / nullif(s.n5::DOUBLE, 0))",
        }.get(method)
        if method == "cosine":
            # Proper: mass_b = sum of lit weights of B's five-starrers
            score_expr = """
                c.both_mass / nullif(sqrt(sm.mass * coalesce(mb.mass_b, c.both)), 0)
            """
            sql = f"""
                {co},
                mass_b AS (
                    SELECT e.work_id, sum(coalesce(w.lit_weight, 0))::DOUBLE AS mass_b
                    FROM five_star_events e
                    JOIN co c USING (work_id)
                    LEFT JOIN user_lit_weight w USING (user_id)
                    GROUP BY e.work_id
                )
                SELECT
                    s.work_id, s.book_id, s.title, s.author, s.book_url,
                    s.n, s.n5, c.both, c.both_mass,
                    {score_expr} AS score
                FROM co c
                JOIN seed_mass sm ON TRUE
                JOIN work_scores s USING (work_id)
                LEFT JOIN mass_b mb USING (work_id)
                WHERE TRUE{sf_join}
                ORDER BY score DESC NULLS LAST, c.both DESC
                LIMIT ?
            """
            rows = execute(sql, [work_id, work_id, min_both, limit]).fetchall()
        else:
            if score_expr is None:
                raise ValueError(f"unknown sim_method {method}")
            # Fix jaccard for weighted: both_mass / (mass_a + mass_b - both_mass)
            if method == "jaccard":
                sql = f"""
                    {co},
                    mass_b AS (
                        SELECT e.work_id, sum(coalesce(w.lit_weight, 0))::DOUBLE AS mass_b
                        FROM five_star_events e
                        JOIN co c USING (work_id)
                        LEFT JOIN user_lit_weight w USING (user_id)
                        GROUP BY e.work_id
                    )
                    SELECT
                        s.work_id, s.book_id, s.title, s.author, s.book_url,
                        s.n, s.n5, c.both, c.both_mass,
                        c.both_mass / nullif(sm.mass + coalesce(mb.mass_b, 0) - c.both_mass, 0) AS score
                    FROM co c
                    JOIN seed_mass sm ON TRUE
                    JOIN work_scores s USING (work_id)
                    LEFT JOIN mass_b mb USING (work_id)
                    WHERE TRUE{sf_join}
                    ORDER BY score DESC NULLS LAST, c.both DESC
                    LIMIT ?
                """
                rows = execute(sql, [work_id, work_id, min_both, limit]).fetchall()
            else:
                sql = f"""
                    {co}
                    SELECT
                        s.work_id, s.book_id, s.title, s.author, s.book_url,
                        s.n, s.n5, c.both, c.both_mass,
                        {score_expr} AS score
                    FROM co c
                    JOIN seed_mass sm ON TRUE
                    JOIN work_scores s USING (work_id)
                    WHERE TRUE{sf_join}
                    ORDER BY score DESC NULLS LAST, c.both DESC
                    LIMIT ?
                """
                rows = execute(sql, [work_id, work_id, min_both, limit]).fetchall()
    else:
        score_expr = {
            "cosine": f"c.both / nullif(sqrt(({n5_a})::DOUBLE * s.n5::DOUBLE), 0)",
            "jaccard": f"c.both::DOUBLE / nullif(({n5_a})::DOUBLE + s.n5::DOUBLE - c.both, 0)",
            "lift": f"c.both * ({n_users})::DOUBLE / nullif(({n_a})::DOUBLE * s.n::DOUBLE, 0)",
            "pmi": f"ln(greatest(c.both * ({n_fan_users})::DOUBLE / nullif(({n5_a})::DOUBLE * s.n5::DOUBLE, 0), 1e-12))",
            "conditional": f"c.both::DOUBLE / ({n5_a})::DOUBLE",
            "association": f"(c.both::DOUBLE / ({n5_a})::DOUBLE) * ln(({n_fan_users})::DOUBLE / nullif(s.n5::DOUBLE, 0))",
        }.get(method)
        if score_expr is None:
            raise ValueError(f"unknown sim_method {method}")

        sql = f"""
            WITH fans AS (
                SELECT user_id FROM five_star_events WHERE work_id = ?
            ),
            co AS (
                SELECT e.work_id, count(*)::BIGINT AS both
                FROM five_star_events e
                JOIN fans USING (user_id)
                WHERE e.work_id != ?
                GROUP BY e.work_id
                HAVING count(*) >= ?
            )
            SELECT
                s.work_id, s.book_id, s.title, s.author, s.book_url,
                s.n, s.n5, c.both, c.both::DOUBLE AS both_mass,
                {score_expr} AS score
            FROM co c
            JOIN work_scores s USING (work_id)
            WHERE TRUE{sf_join}
            ORDER BY score DESC NULLS LAST, c.both DESC
            LIMIT ?
        """
        rows = execute(sql, [work_id, work_id, min_both, limit]).fetchall()

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
                "score": float(r[9]) if r[9] is not None else 0.0,
            }
        )

    return {
        "seed": {
            "work_id": work_id,
            "book_id": bid,
            "title": title,
            "author": author,
            "book_url": book_url,
            "n": n_a,
            "n5": n5_a,
        },
        "method": method,
        "lit_weighted": use_lit,
        "sf_only": sf_only,
        "min_both": min_both,
        "n_results": len(results),
        "methods": SIM_METHODS,
        "results": results,
    }


def _seed_dict(seed) -> dict[str, Any]:
    return {
        "work_id": seed[0],
        "book_id": seed[1],
        "title": seed[2],
        "author": seed[3],
        "book_url": seed[4],
        "n": int(seed[5]),
        "n5": int(seed[6] or 0),
    }

#!/usr/bin/env python3
"""Taste-filter CTEs and literary user weights."""

from __future__ import annotations

from typing import Any

from ucsd_explorer.db import table_names, truthy


def has_taste_tables() -> bool:
    tables = table_names()
    return "user_author_likes" in tables or "user_taste" in tables


def has_lit_weights() -> bool:
    return "user_lit_weight" in table_names()


def has_curator_weights() -> bool:
    return "user_curator_weight" in table_names()


def has_curator_pct_weights() -> bool:
    tables = table_names()
    return "user_curator_pct_weight" in tables and "user_star_percentiles" in tables


def has_curator_pure_weights() -> bool:
    return "user_curator_pure_weight" in table_names()


def has_curator_pct_pure_weights() -> bool:
    tables = table_names()
    return (
        "user_curator_pct_pure_weight" in tables and "user_star_percentiles" in tables
    )


def has_curator_deep_weights() -> bool:
    tables = table_names()
    return "user_curator_deep_weight" in tables and "user_star_percentiles" in tables


def has_prestige() -> bool:
    """True when user_author_likes carries poll-order prestige."""
    if "user_author_likes" not in table_names():
        return False
    from ucsd_explorer.db import execute

    cols = {r[0] for r in execute("DESCRIBE user_author_likes").fetchall()}
    return "prestige" in cols


def parse_taste_params(params: dict[str, Any]) -> dict[str, Any] | None:
    if not truthy(params.get("taste_enabled")):
        return None
    max_nonlit = params.get("taste_max_nonlit")
    if max_nonlit in (None, ""):
        max_nonlit = params.get("taste_max_com")
    if max_nonlit in (None, ""):
        max_nonlit = 1
    min_lit_hits = params.get("taste_min_lit_hits")
    if min_lit_hits in (None, ""):
        min_lit_hits = 0
    min_hits = params.get("taste_min_hits")
    if min_hits in (None, ""):
        min_hits = 1
    min_lit = params.get("taste_min_lit")
    if min_lit in (None, ""):
        min_lit = 0
    return {
        "min_lit": float(min_lit),
        "max_com": float(max_nonlit),
        "min_net": float(
            params.get("taste_min_net") if params.get("taste_min_net") not in (None, "") else -1
        ),
        "min_hits": int(min_hits),
        "min_lit_hits": int(min_lit_hits),
        "include_sf_extras": truthy(params.get("taste_include_sf_extras")),
        "literary_include_fours": not truthy(params.get("taste_literary_fives_only")),
    }


def taste_eligible_cte(taste: dict[str, Any]) -> tuple[str, list[Any]]:
    """CTEs: scores → scored → eligible (users passing taste sliders).

    Literary mass uses poll-order prestige when available:
      lit_mass = Σ prestige × hits  (top-of-chart authors count more)
      lit_weight = lit_share × ln(1 + lit_mass)

    Filter thresholds still use raw hit counts (min literary books, etc.).
    """
    include_fours = bool(taste.get("literary_include_fours", True))
    include_sf = bool(taste.get("include_sf_extras"))
    use_prestige = has_prestige()

    if use_prestige:
        # ? order: fours, sf, fours, fours, sf, fours
        scores = """
        scores AS (
            SELECT
                user_id,
                sum(
                    CASE
                        WHEN side = 'literary_poll'
                            THEN CASE WHEN ? THEN n_liked ELSE n_five END
                        WHEN side = 'literary_sf' AND ?
                            THEN CASE WHEN ? THEN n_liked ELSE n_five END
                        ELSE 0
                    END
                )::BIGINT AS lit_hits,
                sum(
                    CASE WHEN side = 'non_literary' THEN n_five ELSE 0 END
                )::BIGINT AS com_hits,
                sum(
                    CASE
                        WHEN side = 'literary_poll'
                            THEN coalesce(prestige, 0)
                                 * (CASE WHEN ? THEN n_liked ELSE n_five END)
                        WHEN side = 'literary_sf' AND ?
                            THEN coalesce(prestige, 0)
                                 * (CASE WHEN ? THEN n_liked ELSE n_five END)
                        ELSE 0
                    END
                )::DOUBLE AS lit_mass
            FROM user_author_likes
            GROUP BY user_id
        )
        """
        pre_args = [
            include_fours,
            include_sf,
            include_fours,
            include_fours,
            include_sf,
            include_fours,
        ]
    else:
        scores = """
        scores AS (
            SELECT
                user_id,
                sum(
                    CASE
                        WHEN side = 'literary_poll'
                            THEN CASE WHEN ? THEN n_liked ELSE n_five END
                        WHEN side = 'literary_sf' AND ?
                            THEN CASE WHEN ? THEN n_liked ELSE n_five END
                        ELSE 0
                    END
                )::BIGINT AS lit_hits,
                sum(
                    CASE WHEN side = 'non_literary' THEN n_five ELSE 0 END
                )::BIGINT AS com_hits,
                sum(
                    CASE
                        WHEN side = 'literary_poll'
                            THEN CASE WHEN ? THEN n_liked ELSE n_five END
                        WHEN side = 'literary_sf' AND ?
                            THEN CASE WHEN ? THEN n_liked ELSE n_five END
                        ELSE 0
                    END
                )::DOUBLE AS lit_mass
            FROM user_author_likes
            GROUP BY user_id
        )
        """
        pre_args = [
            include_fours,
            include_sf,
            include_fours,
            include_fours,
            include_sf,
            include_fours,
        ]

    sql = f"""
        {scores},
        scored AS (
            SELECT
                user_id,
                lit_hits,
                com_hits,
                lit_mass,
                lit_hits::DOUBLE / nullif(lit_hits + com_hits, 0) AS lit_share,
                com_hits::DOUBLE / nullif(lit_hits + com_hits, 0) AS com_share,
                (
                    coalesce(lit_hits::DOUBLE / nullif(lit_hits + com_hits, 0), 0)
                    - coalesce(com_hits::DOUBLE / nullif(lit_hits + com_hits, 0), 0)
                ) AS net_share
            FROM scores
        ),
        eligible AS (
            SELECT
                user_id,
                lit_hits,
                com_hits,
                lit_mass,
                lit_share,
                com_share,
                net_share,
                greatest(0.0, coalesce(lit_share, 0))
                    * ln(1.0 + greatest(coalesce(lit_mass, 0), 0)) AS lit_weight
            FROM scored
            WHERE coalesce(lit_share, 0) >= ?
              AND coalesce(com_share, 0) <= ?
              AND coalesce(net_share, 0) >= ?
              AND (lit_hits + com_hits) >= ?
              AND lit_hits >= ?
        )
    """
    args = pre_args + [
        taste["min_lit"],
        taste["max_com"],
        taste["min_net"],
        taste["min_hits"],
        taste["min_lit_hits"],
    ]
    return sql, args

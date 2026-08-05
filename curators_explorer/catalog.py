"""Catalog hygiene filters (query-time only; flags live in explorer.duckdb)."""

from __future__ import annotations

from typing import Any

from curators_explorer.db import META, truthy


def has_catalog_flags() -> bool:
    return bool(META.get("has_catalog_flags"))


def has_genre_gates() -> bool:
    return bool(META.get("has_genre_gates"))


def parse_catalog_params(params: dict[str, Any]) -> dict[str, bool]:
    """UI defaults match the simplified rebuild (collections excluded)."""

    def flag(key: str, default: bool) -> bool:
        if key not in params:
            return default
        return truthy(params.get(key))

    return {
        "exclude_collections": flag("exclude_collections", True),
        "exclude_comics": flag("exclude_comics", True),
        "exclude_picture_books": flag("exclude_picture_books", True),
        "fiction_only": flag("fiction_only", True),
        "exclude_derivatives": flag("exclude_derivatives", True),
        "collapse_duplicates": flag("collapse_duplicates", True),
        "apply_format_weight": flag("apply_format_weight", True),
    }


def parse_sf_only(params: dict[str, Any]) -> bool:
    if "sf_only" in params:
        return truthy(params.get("sf_only"))
    gates = params.get("genre_gates") or params.get("gates")
    if isinstance(gates, str):
        gates = [g.strip() for g in gates.split(",") if g.strip()]
    if isinstance(gates, list):
        return [str(g).lower() for g in gates] == ["sf"]
    return False


def eligible_works_cte(
    *,
    sf_only: bool = False,
    catalog: dict[str, bool] | None = None,
) -> str | None:
    """Pre-filter work_ids before scanning ~100M rating events."""
    where_parts: list[str] = []
    joins: list[str] = []

    if sf_only and has_genre_gates():
        joins.append(
            "JOIN work_genre_gates gg"
            " ON gg.work_id = w.work_id AND gg.gate = 'sf' AND gg.passed"
        )
    elif sf_only:
        where_parts.append("coalesce(w.is_sf, FALSE)")

    if catalog and has_catalog_flags():
        joins.append("LEFT JOIN work_flags cf ON cf.work_id = w.work_id")
        where_parts.append("NOT coalesce(cf.is_excluded, FALSE)")
        if catalog.get("exclude_collections"):
            where_parts.append("NOT coalesce(cf.is_collection, FALSE)")
        if catalog.get("exclude_comics"):
            where_parts.append("NOT coalesce(cf.is_comic, FALSE)")
        if catalog.get("exclude_picture_books"):
            where_parts.append("NOT coalesce(cf.is_picture_book, FALSE)")
        if catalog.get("fiction_only"):
            where_parts.append("NOT coalesce(cf.is_nonfiction, FALSE)")
        if catalog.get("exclude_derivatives"):
            where_parts.append("NOT coalesce(cf.is_derivative, FALSE)")
        if catalog.get("collapse_duplicates"):
            where_parts.append("NOT coalesce(cf.is_duplicate, FALSE)")

    if not joins and not where_parts:
        return None

    join_sql = ("\n                " + "\n                ".join(joins)) if joins else ""
    where_sql = (
        ("\n                WHERE " + "\n                  AND ".join(where_parts))
        if where_parts
        else ""
    )
    return f"""
            eligible_works AS (
                SELECT w.work_id
                FROM works w
                {join_sql}
                {where_sql}
            )
    """


def catalog_score_bits(
    catalog: dict[str, bool] | None,
    score_expr: str,
    *,
    work_alias: str = "w",
    flags_alias: str = "cf",
) -> tuple[str, str, str]:
    """Return (join_sql, where_sql, scored_expr) for the final SELECT."""
    if not catalog or not has_catalog_flags():
        return "", "", score_expr
    # Early CTE already applied hard excludes; only format_weight remains soft.
    join = f" LEFT JOIN work_flags {flags_alias} ON {flags_alias}.work_id = {work_alias}.work_id"
    if catalog.get("apply_format_weight", True):
        scored = f"(({score_expr}) * coalesce({flags_alias}.format_weight, 1.0))"
    else:
        scored = f"({score_expr})"
    return join, "", scored

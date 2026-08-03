#!/usr/bin/env python3
"""Earliest catalogued edition year per work (from UCSD books.parquet).

``work_years.pub_year`` is ``min(publication_year)`` over *all* editions in
``books.parquet`` for that ``work_id`` — not only the ratings-filtered
``book_to_work`` map (which drops low-count first editions like Stoner 1965).

Years outside 1500–2030 are ignored (drops Hijri-looking ~13xx misentries).
This is earliest *catalogued* edition year, not necessarily literary first pub.
Manual ``original_years`` in catalog_overrides.json still win when set.

Run:
  .venv/bin/python -m ucsd_explorer.work_years
  .venv/bin/python -m ucsd_explorer.catalog_flags --years-only
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ucsd_explorer.db import DERIVED, EXPLORER_DB, META_PATH, OVERRIDES_PATH, PARQUET

# Band for edition years. Floor 1500 excludes Hijri-as-Gregorian mislabels (~139x).
YEAR_MIN_BAND = 1500
YEAR_MAX_BAND = 2030


def load_overrides() -> dict[str, Any]:
    if not OVERRIDES_PATH.exists():
        return {}
    return json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))


def apply_original_year_overrides(con, overrides: dict[str, Any] | None = None) -> int:
    """Upsert original_years overrides onto work_years. Returns count applied."""
    overrides = overrides if overrides is not None else load_overrides()
    n = 0
    for wid, y in (overrides.get("original_years") or {}).items():
        wid_s, y_i = str(wid), int(y)
        exists = con.execute(
            "SELECT 1 FROM work_years WHERE work_id = ?", [wid_s]
        ).fetchone()
        if exists:
            con.execute(
                "UPDATE work_years SET pub_year = ? WHERE work_id = ?", [y_i, wid_s]
            )
        else:
            con.execute("INSERT INTO work_years VALUES (?, ?)", [wid_s, y_i])
        n += 1
    return n


def build_work_years_table(con, books_pq: Path | None = None) -> None:
    """Rebuild work_years from all books.parquet editions (by work_id)."""
    books_pq = books_pq or (PARQUET / "books.parquet")
    print("Catalog years: aggregating publication_year (all editions)…", flush=True)
    con.execute("DROP TABLE IF EXISTS work_years")
    con.execute(
        f"""
        CREATE TABLE work_years AS
        SELECT
            work_id::VARCHAR AS work_id,
            min(try_cast(publication_year AS INTEGER))::INTEGER AS pub_year
        FROM read_parquet('{books_pq}')
        WHERE work_id IS NOT NULL
          AND try_cast(publication_year AS INTEGER)
              BETWEEN {YEAR_MIN_BAND} AND {YEAR_MAX_BAND}
        GROUP BY work_id
        """
    )
    con.execute("CREATE INDEX idx_work_years ON work_years(work_id)")
    con.execute("CREATE INDEX idx_work_years_y ON work_years(pub_year)")


# Back-compat alias used by catalog_flags inherit path
_build_work_years_table = build_work_years_table


def materialize_work_years(*, db_path: Path | None = None) -> dict[str, Any]:
    """Earliest catalogued edition year per work from the full books dump."""
    import duckdb

    db_path = db_path or EXPLORER_DB
    books_pq = PARQUET / "books.parquet"
    if not db_path.exists():
        raise SystemExit(f"Missing {db_path}")
    if not books_pq.exists():
        raise SystemExit(f"Missing {books_pq}")

    con = duckdb.connect(str(db_path))
    build_work_years_table(con, books_pq)
    n_overrides = apply_original_year_overrides(con)
    n = int(con.execute("SELECT count(*) FROM work_years").fetchone()[0])
    bounds = con.execute("SELECT min(pub_year), max(pub_year) FROM work_years").fetchone()
    stats = {
        "n_works_with_year": n,
        "n_original_year_overrides": n_overrides,
        "year_min": int(bounds[0]) if bounds and bounds[0] is not None else None,
        "year_max": int(bounds[1]) if bounds and bounds[1] is not None else None,
        "year_band": [YEAR_MIN_BAND, YEAR_MAX_BAND],
        "source": "books.parquet all editions by work_id",
    }
    print(
        f"work_years: {n:,} works · {stats['year_min']}–{stats['year_max']}"
        f" · {n_overrides} overrides",
        flush=True,
    )
    con.close()
    DERIVED.mkdir(parents=True, exist_ok=True)
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    else:
        meta = {}
    meta["work_years"] = stats
    meta["work_years_available"] = True
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return stats


def has_work_years() -> bool:
    from ucsd_explorer.db import table_names

    return "work_years" in table_names()


def year_sql_bits(
    year_min: int | None,
    year_max: int | None,
    *,
    work_alias: str = "s",
) -> tuple[str, str, list[Any]]:
    """Return (join_sql, where_sql, args) for optional publication-year range."""
    if not year_min and not year_max:
        return "", "", []
    if not has_work_years():
        return "", "", []
    join = f" LEFT JOIN work_years wy ON wy.work_id = {work_alias}.work_id"
    parts = ["wy.pub_year IS NOT NULL"]
    args: list[Any] = []
    if year_min:
        parts.append("wy.pub_year >= ?")
        args.append(int(year_min))
    if year_max:
        parts.append("wy.pub_year <= ?")
        args.append(int(year_max))
    return join, " AND " + " AND ".join(parts), args


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=EXPLORER_DB)
    args = p.parse_args()
    materialize_work_years(db_path=args.db)


if __name__ == "__main__":
    main()

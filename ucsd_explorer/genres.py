#!/usr/bin/env python3
"""Goodreads shelf/genre tags for RYM-style filtering.

Materializes ``genre_catalog`` + ``work_genres`` on the explorer DuckDB from
``book_shelves.parquet``, then provides require / include (any-of) / exclude
SQL fragments for ranking.

Run:
  .venv/bin/python -m ucsd_explorer.genres
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

from ucsd_explorer.db import DERIVED, EXPLORER_DB, META_PATH, PARQUET

# Personal / format / status shelves — not useful as genre filters.
NOISE_SHELVES = frozenset(
    {
        "to-buy",
        "to-read",
        "currently-reading",
        "read",
        "dnf",
        "abandoned",
        "tbr",
        "library",
        "kindle",
        "ebook",
        "e-book",
        "audiobook",
        "audio",
        "audible",
        "paperback",
        "hardcover",
        "english",
        "read-in-english",
        "books",
        "my-books",
        "owned",
        "i-own",
        "own-it",
        "owned-books",
        "favourites",
        "favorites",
        "favourite",
        "favorite",
        "favorite-books",
        "all-time-favorites",
        "favourites",
        "5-stars",
        "4-stars",
        "3-stars",
        "series",
        "maybe",
        "unfinished",
        "re-read",
        "reread",
        "to-reread",
        "did-not-finish",
        "abandoned",
        "on-hold",
        "physical-tbr",
        "kindle-tbr",
    }
)

# Classic SF preset — "any of" these Goodreads shelves (OR).
# Keep this tighter than bare "speculative-fiction" (which tags a lot of literary).
SF_PRESET_INCLUDE = (
    "science-fiction",
    "sci-fi",
    "scifi",
    "sf",
    "hard-sf",
    "hard-science-fiction",
    "space-opera",
    "cyberpunk",
    "military-sf",
    "military-science-fiction",
)

YEAR_SHELF_RE = re.compile(r"^read-in-\d{4}$|^read-\d{4}$|^\d{4}-reads$")

MIN_SHELF_WORKS = 80
MIN_SHELF_TOTAL = 8_000
MIN_WORK_TAG_COUNT = 5


def _is_noise(shelf: str) -> bool:
    s = (shelf or "").lower().strip()
    if not s or s in NOISE_SHELVES:
        return True
    if YEAR_SHELF_RE.match(s):
        return True
    if s.startswith("read-in-") or s.startswith("read-20"):
        return True
    return False


def has_genre_tables() -> bool:
    from ucsd_explorer.db import get_con

    try:
        con = get_con()
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        return "work_genres" in tables and "genre_catalog" in tables
    except Exception:
        return False


def parse_genre_params(params: dict[str, Any]) -> dict[str, list[str]]:
    """Parse require / include / exclude genre lists from API params.

    Accepts JSON arrays, comma-separated strings, or repeated keys.
    Empty lists mean no constraint for that bucket.
    """

    def _as_list(key: str, alt: str | None = None) -> list[str]:
        raw = params.get(key)
        if raw is None and alt:
            raw = params.get(alt)
        if raw is None or raw == "":
            return []
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, str):
            s = raw.strip()
            if s.startswith("["):
                try:
                    items = json.loads(s)
                except json.JSONDecodeError:
                    items = [x.strip() for x in s.split(",")]
            else:
                items = [x.strip() for x in s.split(",")]
        else:
            items = [raw]
        out: list[str] = []
        seen: set[str] = set()
        for x in items:
            g = str(x).lower().strip().replace(" ", "-")
            if not g or g in seen:
                continue
            seen.add(g)
            out.append(g)
        return out

    require = _as_list("genre_require", "genres_require")
    include = _as_list("genre_include", "genres_include")
    exclude = _as_list("genre_exclude", "genres_exclude")

    genre_keys = (
        "genre_require",
        "genre_include",
        "genre_exclude",
        "genres_require",
        "genres_include",
        "genres_exclude",
    )
    explicit = any(k in params for k in genre_keys)

    # Backward compat: old SF checkbox / no genre keys → SF any-of preset.
    if not explicit and not require and not include and not exclude:
        sf = params.get("sf_only", params.get("genre_sf_only"))
        if sf is None or sf == "":
            include = list(SF_PRESET_INCLUDE)
        else:
            truthy = True
            if isinstance(sf, bool):
                truthy = sf
            else:
                truthy = str(sf).strip().lower() not in (
                    "0",
                    "false",
                    "no",
                    "off",
                    "all",
                )
            if truthy:
                include = list(SF_PRESET_INCLUDE)

    return {"require": require, "include": include, "exclude": exclude}


def is_sf_preset_filter(genres: dict[str, list[str]] | None) -> bool:
    """True when include is the SF shelf preset (use is_sf prevalence gate)."""
    if not genres:
        return False
    inc = set(genres.get("include") or [])
    if not inc:
        return False
    return inc <= set(SF_PRESET_INCLUDE)


def genre_sql_bits(
    genres: dict[str, list[str]] | None,
    *,
    work_alias: str = "w",
    sf_via_prevalence: bool = True,
) -> tuple[str, list[Any]]:
    """Return (where_sql, args) restricting ``work_alias`` by genre lists.

    When ``sf_via_prevalence`` is True and include ⊆ SF_PRESET_INCLUDE, the
    filter uses ``work.is_sf`` (prevalence gate) instead of a loose tag OR.
    Pass ``sf_via_prevalence=False`` when ``genre_gates`` already applies the
    SF gate so tags stay as plain shelf filters.
    """
    if not genres:
        return "", []

    args: list[Any] = []
    parts: list[str] = []
    sf_preset = bool(sf_via_prevalence and is_sf_preset_filter(genres))

    if sf_preset:
        parts.append(f"coalesce({work_alias}.is_sf, FALSE)")
    elif not has_genre_tables():
        return "", []

    if not has_genre_tables() and not sf_preset:
        return "", []

    for g in genres.get("require") or []:
        if not has_genre_tables():
            break
        parts.append(
            f""" EXISTS (
              SELECT 1 FROM work_genres wg
              WHERE wg.work_id = {work_alias}.work_id AND wg.shelf = ?
            )"""
        )
        args.append(g)

    include = genres.get("include") or []
    if include and not sf_preset:
        if not has_genre_tables():
            return "", []
        placeholders = ", ".join(["?"] * len(include))
        parts.append(
            f""" EXISTS (
              SELECT 1 FROM work_genres wg
              WHERE wg.work_id = {work_alias}.work_id AND wg.shelf IN ({placeholders})
            )"""
        )
        args.extend(include)

    for g in genres.get("exclude") or []:
        if not has_genre_tables():
            break
        parts.append(
            f""" NOT EXISTS (
              SELECT 1 FROM work_genres wg
              WHERE wg.work_id = {work_alias}.work_id AND wg.shelf = ?
            )"""
        )
        args.append(g)

    if not parts:
        return "", []
    return " AND " + " AND ".join(parts), args


def search_genres(q: str = "", *, limit: int = 40) -> list[dict[str, Any]]:
    """Autocomplete against genre_catalog."""
    from ucsd_explorer.db import execute

    if not has_genre_tables():
        return []
    limit = min(max(1, int(limit)), 100)
    q = (q or "").strip().lower().replace(" ", "-")
    if q:
        rows = execute(
            """
            SELECT shelf, n_works, total_count
            FROM genre_catalog
            WHERE shelf LIKE ? OR shelf LIKE ?
            ORDER BY
              CASE WHEN shelf = ? THEN 0 WHEN shelf LIKE ? THEN 1 ELSE 2 END,
              total_count DESC
            LIMIT ?
            """,
            [f"{q}%", f"%{q}%", q, f"{q}%", limit],
        ).fetchall()
    else:
        rows = execute(
            """
            SELECT shelf, n_works, total_count
            FROM genre_catalog
            ORDER BY total_count DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
    return [
        {"shelf": r[0], "n_works": int(r[1]), "total_count": int(r[2])} for r in rows
    ]


def materialize_genres(
    *,
    db_path: Path | None = None,
    min_shelf_works: int = MIN_SHELF_WORKS,
    min_shelf_total: int = MIN_SHELF_TOTAL,
    min_work_tag_count: int = MIN_WORK_TAG_COUNT,
) -> dict[str, Any]:
    import duckdb

    db_path = db_path or EXPLORER_DB
    shelves_pq = PARQUET / "book_shelves.parquet"
    if not db_path.exists():
        raise SystemExit(f"Missing {db_path}")
    if not shelves_pq.exists():
        raise SystemExit(f"Missing {shelves_pq}")

    t0 = time.time()
    con = duckdb.connect(str(db_path))
    print("Genres: aggregating work×shelf…", flush=True)
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _raw_work_shelf AS
        SELECT
            btw.work_id,
            lower(s.shelf) AS shelf,
            sum(s.count)::BIGINT AS cnt
        FROM read_parquet('{shelves_pq}') s
        JOIN book_to_work btw ON s.book_id = btw.book_id
        JOIN work_scores w ON w.work_id = btw.work_id
        WHERE NOT coalesce(s.is_status, FALSE)
        GROUP BY 1, 2
        HAVING sum(s.count) >= {int(min_work_tag_count)}
        """
    )
    # Filter noise in Python for clarity / maintainability
    print("Genres: building catalog…", flush=True)
    shelf_stats = con.execute(
        """
        SELECT shelf, count(*)::BIGINT AS n_works, sum(cnt)::BIGINT AS total_count
        FROM _raw_work_shelf
        GROUP BY shelf
        HAVING count(*) >= ? AND sum(cnt) >= ?
        ORDER BY total_count DESC
        """,
        [min_shelf_works, min_shelf_total],
    ).fetchall()
    keep = [r for r in shelf_stats if not _is_noise(str(r[0]))]
    print(f"  kept {len(keep):,} genre shelves (from {len(shelf_stats):,} candidates)", flush=True)

    con.execute("DROP TABLE IF EXISTS genre_catalog")
    con.execute(
        """
        CREATE TABLE genre_catalog (
            shelf VARCHAR,
            n_works BIGINT,
            total_count BIGINT
        )
        """
    )
    con.executemany(
        "INSERT INTO genre_catalog VALUES (?, ?, ?)",
        [(str(s), int(n), int(t)) for s, n, t in keep],
    )
    con.execute("CREATE INDEX idx_genre_cat_shelf ON genre_catalog(shelf)")

    con.execute("DROP TABLE IF EXISTS work_genres")
    con.execute(
        """
        CREATE TABLE work_genres AS
        SELECT r.work_id, r.shelf, r.cnt AS count
        FROM _raw_work_shelf r
        JOIN genre_catalog g USING (shelf)
        """
    )
    con.execute("CREATE INDEX idx_wg_work ON work_genres(work_id)")
    con.execute("CREATE INDEX idx_wg_shelf ON work_genres(shelf)")
    con.execute("CREATE INDEX idx_wg_work_shelf ON work_genres(work_id, shelf)")

    n_rows = con.execute("SELECT count(*) FROM work_genres").fetchone()[0]
    n_works = con.execute("SELECT count(DISTINCT work_id) FROM work_genres").fetchone()[0]
    # Ensure SF preset shelves exist when possible
    present = {
        r[0]
        for r in con.execute("SELECT shelf FROM genre_catalog").fetchall()
    }
    sf_present = [s for s in SF_PRESET_INCLUDE if s in present]
    con.close()

    stats = {
        "n_genre_shelves": len(keep),
        "n_work_genre_rows": int(n_rows),
        "n_works_tagged": int(n_works),
        "sf_preset_shelves": sf_present,
        "min_shelf_works": min_shelf_works,
        "min_shelf_total": min_shelf_total,
        "min_work_tag_count": min_work_tag_count,
        "elapsed_s": round(time.time() - t0, 1),
        "built_at": time.time(),
    }
    print(
        f"work_genres: {n_rows:,} rows · {n_works:,} works · "
        f"{len(keep):,} shelves · SF preset {len(sf_present)}/{len(SF_PRESET_INCLUDE)} "
        f"in {stats['elapsed_s']}s",
        flush=True,
    )
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        meta["genres"] = stats
        meta["genres_available"] = True
        META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--min-shelf-works", type=int, default=MIN_SHELF_WORKS)
    p.add_argument("--min-shelf-total", type=int, default=MIN_SHELF_TOTAL)
    p.add_argument("--min-work-tag-count", type=int, default=MIN_WORK_TAG_COUNT)
    args = p.parse_args()
    materialize_genres(
        min_shelf_works=args.min_shelf_works,
        min_shelf_total=args.min_shelf_total,
        min_work_tag_count=args.min_work_tag_count,
    )


if __name__ == "__main__":
    main()

"""Goodreads shelf filters used by the curators explorer.

The UCSD explorer exposes two useful kinds of genre filter:

* raw shelf filters (require / any-of / exclude), and
* named prevalence gates, implemented in :mod:`curators_explorer.genre_gates`.

The shared warehouse's ``work_genres`` table intentionally drops very small
shelves.  A few legitimate genres requested by the UI (notably
``low-fantasy`` and ``slice-of-life``) fall below that cutoff, so this module
also builds a temporary, read-only supplement from ``book_shelves.parquet``.
It only contains shelves used by the named gates or explicitly requested by
the current query; it never changes the warehouse.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

from curators_explorer.db import ROOT, execute, get_con, table_names


# Personal / format / status shelves are not useful as genre filters.
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
        "on-hold",
        "physical-tbr",
        "kindle-tbr",
    }
)

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
RAW_SHELVES_PATH = ROOT / "data" / "ucsd_goodreads" / "parquet" / "book_shelves.parquet"

_RAW_LOCK = threading.RLock()
_RAW_READY: set[str] = set()
_RAW_TABLE_READY = False


def _is_noise(shelf: str) -> bool:
    s = (shelf or "").lower().strip()
    if not s or s in NOISE_SHELVES:
        return True
    if YEAR_SHELF_RE.match(s):
        return True
    return s.startswith("read-in-") or s.startswith("read-20")


def _normalize_shelf(value: Any) -> str:
    """Normalize the spelling users type into Goodreads shelf spelling."""

    s = str(value).lower().strip()
    # Treat children's / children's-books as the common Goodreads spellings.
    s = s.replace("’", "'").replace("'", "")
    s = s.replace("&", "and")
    return re.sub(r"\s+", "-", s)


def has_genre_tables() -> bool:
    try:
        tables = table_names()
        return "work_genres" in tables and "genre_catalog" in tables
    except Exception:
        return False


def _catalog_shelves() -> set[str]:
    if not has_genre_tables():
        return set()
    return {str(r[0]) for r in execute("SELECT shelf FROM genre_catalog").fetchall()}


def _configured_shelves() -> set[str]:
    """Return all shelf names used by named gates, lazily to avoid a cycle."""

    try:
        from curators_explorer.genre_gates import GATE_DEFS

        shelves: set[str] = {"fiction", "young-adult", "ya", "teen"}
        for definition in GATE_DEFS.values():
            for key in ("core", "soft", "compete", "compete_soft", "literary"):
                shelves.update(str(x) for x in (definition.get(key) or ()))
        return shelves
    except Exception:
        # The fallback keeps raw shelf searching useful during partial imports.
        return {"fiction", "young-adult", "ya", "teen"}


def ensure_extra_genres(shelves: set[str] | list[str] | tuple[str, ...] = ()) -> None:
    """Supplement ``work_genres`` with requested low-volume shelves.

    DuckDB permits temporary tables on a read-only connection.  The table is
    populated once per process and is deliberately limited to shelves missing
    from ``genre_catalog``.  Shelf counts retain the same ``sum >= 5`` rule as
    the normal materializer.
    """

    global _RAW_TABLE_READY
    wanted = {_normalize_shelf(s) for s in shelves if str(s).strip()}
    wanted.update(_configured_shelves())
    if not RAW_SHELVES_PATH.exists():
        return

    with _RAW_LOCK:
        catalog = _catalog_shelves()
        missing = {s for s in wanted if s not in catalog and not _is_noise(s)}
        missing -= _RAW_READY
        if not missing:
            return

        con = get_con()
        literals = ", ".join("'" + s.replace("'", "''") + "'" for s in sorted(missing))
        parquet = str(RAW_SHELVES_PATH).replace("'", "''")
        select_sql = f"""
            SELECT
                btw.work_id,
                lower(s.shelf) AS shelf,
                sum(s.count)::BIGINT AS count
            FROM read_parquet('{parquet}') s
            JOIN book_to_work btw ON s.book_id = btw.book_id
            JOIN work_scores w ON w.work_id = btw.work_id
            WHERE NOT coalesce(s.is_status, FALSE)
              AND lower(s.shelf) IN ({literals})
            GROUP BY 1, 2
            HAVING sum(s.count) >= 5
        """
        if not _RAW_TABLE_READY:
            con.execute(
                f"CREATE TEMP TABLE _curators_extra_genres AS {select_sql}"
            )
            _RAW_TABLE_READY = True
        else:
            con.execute(f"INSERT INTO _curators_extra_genres {select_sql}")
        _RAW_READY.update(missing)


def _extra_shelves() -> set[str]:
    if not _RAW_TABLE_READY:
        return set()
    return _RAW_READY


def _relation_for_shelf(shelf: str) -> str:
    """Choose the compact source containing a shelf."""

    if shelf in _catalog_shelves():
        return "work_genres"
    if shelf in _extra_shelves():
        return "_curators_extra_genres"
    # Unknown shelves are harmlessly empty, but using the temp supplement
    # lets an explicit query request a raw shelf before this function returns.
    return "_curators_extra_genres" if _RAW_TABLE_READY else "work_genres"


def parse_genre_params(params: dict[str, Any]) -> dict[str, list[str]]:
    """Parse require / include (any-of) / exclude shelf lists.

    Accepts JSON arrays, comma-separated strings, or repeated query keys.
    Unlike the UCSD explorer, curators keeps its historical all-genre default;
    the SF checkbox is only translated into the legacy SF shelf preset when it
    is explicitly on.
    """

    def _as_list(key: str, alt: str | None = None) -> list[str]:
        raw = params.get(key)
        if raw is None and alt:
            raw = params.get(alt)
        if raw is None or raw == "":
            return []
        if isinstance(raw, (list, tuple)):
            items = list(raw)
        elif isinstance(raw, str):
            value = raw.strip()
            if value.startswith("["):
                try:
                    items = json.loads(value)
                except json.JSONDecodeError:
                    items = [x.strip() for x in value.split(",")]
            else:
                items = [x.strip() for x in value.split(",")]
        else:
            items = [raw]

        out: list[str] = []
        seen: set[str] = set()
        for item in items:
            shelf = _normalize_shelf(item)
            if not shelf or shelf in seen:
                continue
            seen.add(shelf)
            out.append(shelf)
        return out

    require = _as_list("genre_require", "genres_require")
    include = _as_list("genre_include", "genres_include")
    exclude = _as_list("genre_exclude", "genres_exclude")
    explicit = any(
        key in params
        for key in (
            "genre_require",
            "genre_include",
            "genre_exclude",
            "genres_require",
            "genres_include",
            "genres_exclude",
        )
    )

    if not explicit and not require and not include and not exclude:
        sf = params.get("sf_only", params.get("genre_sf_only"))
        if isinstance(sf, bool):
            enabled = sf
        else:
            enabled = str(sf or "").strip().lower() in ("1", "true", "yes", "on")
        if enabled:
            include = list(SF_PRESET_INCLUDE)

    return {"require": require, "include": include, "exclude": exclude}


def is_sf_preset_filter(genres: dict[str, list[str]] | None) -> bool:
    if not genres:
        return False
    if genres.get("require") or genres.get("exclude"):
        return False
    include = set(genres.get("include") or [])
    return bool(include) and include <= set(SF_PRESET_INCLUDE)


def _shelf_exists_sql(shelf: str, work_alias: str) -> tuple[str, list[Any]]:
    relation = _relation_for_shelf(shelf)
    return (
        f"""EXISTS (
            SELECT 1 FROM {relation} wg
            WHERE wg.work_id = {work_alias}.work_id AND wg.shelf = ?
        )""",
        [shelf],
    )


def genre_sql_bits(
    genres: dict[str, list[str]] | None,
    *,
    work_alias: str = "w",
    sf_via_prevalence: bool = True,
) -> tuple[str, list[Any]]:
    """Return a SQL suffix and bound args for shelf filters."""

    if not genres:
        return "", []
    all_shelves = [
        *(genres.get("require") or []),
        *(genres.get("include") or []),
        *(genres.get("exclude") or []),
    ]
    ensure_extra_genres(all_shelves)
    if not has_genre_tables() and not _RAW_TABLE_READY:
        return "", []

    args: list[Any] = []
    parts: list[str] = []
    sf_preset = bool(sf_via_prevalence and is_sf_preset_filter(genres))
    if sf_preset:
        parts.append(f"coalesce({work_alias}.is_sf, FALSE)")

    for shelf in genres.get("require") or []:
        sql, sql_args = _shelf_exists_sql(shelf, work_alias)
        parts.append(sql)
        args.extend(sql_args)

    include = genres.get("include") or []
    if include and not sf_preset:
        placeholders = ", ".join("?" for _ in include)
        arms: list[str] = []
        for shelf in include:
            sql, sql_args = _shelf_exists_sql(shelf, work_alias)
            arms.append(sql)
            args.extend(sql_args)
        # Each arm has its own bound shelf, avoiding a relation-dependent IN.
        parts.append("(" + " OR ".join(arms) + ")")

    for shelf in genres.get("exclude") or []:
        sql, sql_args = _shelf_exists_sql(shelf, work_alias)
        parts.append("NOT " + sql)
        args.extend(sql_args)

    return (" AND " + " AND ".join(parts), args) if parts else ("", [])


def search_genres(q: str = "", *, limit: int = 40) -> list[dict[str, Any]]:
    """Autocomplete catalog shelves plus configured low-volume shelves."""

    ensure_extra_genres()
    if not has_genre_tables() and not _RAW_TABLE_READY:
        return []
    limit = min(max(1, int(limit)), 100)
    query = _normalize_shelf(q) if q else ""
    like_prefix = f"{query}%"
    like_any = f"%{query}%"

    sources: list[str] = []
    args: list[Any] = []
    if has_genre_tables():
        sources.append(
            """SELECT shelf, n_works, total_count
               FROM genre_catalog
               WHERE shelf LIKE ? OR shelf LIKE ?"""
        )
        args.extend([like_prefix, like_any])
    if _RAW_TABLE_READY:
        sources.append(
            """SELECT shelf, count(DISTINCT work_id)::BIGINT AS n_works,
                      sum(count)::BIGINT AS total_count
               FROM _curators_extra_genres
               WHERE shelf LIKE ? OR shelf LIKE ?
               GROUP BY shelf"""
        )
        args.extend([like_prefix, like_any])
    if not sources:
        return []

    rows = execute(
        f"""
        SELECT shelf, max(n_works)::BIGINT AS n_works,
               max(total_count)::BIGINT AS total_count
        FROM ({' UNION ALL '.join(sources)}) genres
        GROUP BY shelf
        ORDER BY
          CASE WHEN shelf = ? THEN 0 WHEN shelf LIKE ? THEN 1 ELSE 2 END,
          total_count DESC
        LIMIT ?
        """,
        args + [query, like_prefix, limit],
    ).fetchall()
    return [
        {"shelf": r[0], "n_works": int(r[1]), "total_count": int(r[2])}
        for r in rows
    ]


def genre_rows_sql() -> str:
    """Return a relation containing normal and low-volume shelf rows."""

    ensure_extra_genres()
    if _RAW_TABLE_READY:
        return "(SELECT work_id, shelf, count FROM work_genres UNION ALL SELECT work_id, shelf, count FROM _curators_extra_genres)"
    return "(SELECT work_id, shelf, count FROM work_genres)"


def main() -> None:
    """Warm the temporary supplement and print its coverage."""

    ensure_extra_genres()
    if _RAW_TABLE_READY:
        row = execute(
            "SELECT count(DISTINCT work_id), count(DISTINCT shelf) FROM _curators_extra_genres"
        ).fetchone()
        print(f"extra genre rows: {row[0]:,} works · {row[1]:,} shelves")
    else:
        print("No parquet supplement available; using work_genres only.")


if __name__ == "__main__":
    main()

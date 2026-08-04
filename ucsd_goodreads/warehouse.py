#!/usr/bin/env python3
"""Genre-agnostic UCSD Goodreads warehouse (Parquet + DuckDB).

Raw dumps stay in ``data/ucsd_goodreads/raw/``. This module builds:

* ``parquet/`` — columnar extracts (books, shelves, authors, interactions)
* ``ucsd.duckdb`` — views / macros for browsing; genre is a *filter*, not a silo

Science fiction (or fantasy, mystery, …) is expressed as SQL over shelf scores,
optionally materialized into a cached book-id list for speed.

Academic use only — do not redistribute raw Goodreads dumps.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "ucsd_goodreads" / "raw"
DEFAULT_PARQUET = ROOT / "data" / "ucsd_goodreads" / "parquet"
DEFAULT_DB = ROOT / "data" / "ucsd_goodreads" / "ucsd.duckdb"

# Shelves that are ownership / status noise — kept in book_shelves but ignored
# by genre score macros.
STATUS_SHELVES = frozenset(
    {
        "to-read",
        "currently-reading",
        "read",
        "owned",
        "books-i-own",
        "owned-books",
        "library",
        "my-library",
        "kindle",
        "ebook",
        "ebooks",
        "audiobook",
        "audiobooks",
        "audio",
        "default",
        "favorites",
        "favourites",
        "re-read",
        "reread",
        "dnf",
        "abandoned",
        "did-not-finish",
        "tbr",
        "wish-list",
        "wishlist",
    }
)

# Named genre score buckets (expandable). Each maps to shelf name sets.
GENRE_SHELF_GROUPS: dict[str, frozenset[str]] = {
    "sf_core": frozenset(
        {
            "science-fiction",
            "hard-sf",
            "hard-science-fiction",
            "space-opera",
            "cyberpunk",
            "military-science-fiction",
            "military-sf",
        }
    ),
    "sf_soft": frozenset(
        {
            "sci-fi",
            "scifi",
            "sciencefiction",
            "speculative-fiction",
        }
    ),
    "fantasy": frozenset(
        {
            "fantasy",
            "high-fantasy",
            "epic-fantasy",
            "urban-fantasy",
            "paranormal",
            "paranormal-romance",
            "magic",
            "magical",
            "harry-potter",
            "hogwarts",
            "discworld",
        }
    ),
    "romance": frozenset(
        {
            "romance",
            "contemporary-romance",
            "historical-romance",
            "romantic",
        }
    ),
    "mystery": frozenset(
        {
            "mystery",
            "thriller",
            "crime",
            "suspense",
            "detective",
        }
    ),
    "horror": frozenset(
        {
            "horror",
            "vampires",
            "werewolves",
            "shapeshifters",
            "zombie",
            "zombies",
        }
    ),
    "ya": frozenset(
        {
            "young-adult",
            "ya",
            "teen",
            "children",
            "childrens",
            "middle-grade",
        }
    ),
    "history_bio": frozenset(
        {
            "history",
            "historical",
            "historical-fiction",
            "biography",
            "memoir",
            "non-fiction",
            "nonfiction",
        }
    ),
}


def _log(msg: str) -> None:
    print(msg, flush=True)


def _need_duckdb():
    try:
        import duckdb  # noqa: F401
    except ImportError as e:
        raise SystemExit(
            "duckdb is required. From repo root:\n"
            "  python3 -m venv .venv && .venv/bin/pip install duckdb\n"
            "  .venv/bin/python -m ucsd_goodreads.warehouse …"
        ) from e
    import duckdb

    return duckdb


def open_json_gz(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _primary_author_id(book: dict[str, Any]) -> Optional[str]:
    authors = book.get("authors") or []
    if not authors:
        return None
    for a in authors:
        if (a.get("role") or "").strip() == "":
            aid = a.get("author_id")
            return str(aid) if aid is not None else None
    aid = authors[0].get("author_id")
    return str(aid) if aid is not None else None


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None or v == "":
            return default
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def export_authors(raw: Path, parquet_dir: Path) -> Path:
    """Native DuckDB JSON→Parquet (orders of magnitude faster than Python inserts)."""
    duckdb = _need_duckdb()
    src = raw / "goodreads_book_authors.json.gz"
    out = parquet_dir / "authors.parquet"
    _log(f"authors ← {src.name}")
    t0 = time.time()
    con = duckdb.connect()
    con.execute(
        f"""
        COPY (
            SELECT
                author_id::VARCHAR AS author_id,
                nullif(trim(name), '') AS name,
                try_cast(average_rating AS DOUBLE) AS average_rating,
                try_cast(ratings_count AS BIGINT) AS ratings_count,
                try_cast(text_reviews_count AS BIGINT) AS text_reviews_count
            FROM read_json(
                '{src}',
                format='newline_delimited',
                compression='gzip',
                ignore_errors=true
            )
        ) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    n = con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
    _log(f"  → {out.name} ({n:,} rows) in {time.time()-t0:.1f}s")
    con.close()
    return out


def export_books_and_shelves(raw: Path, parquet_dir: Path) -> tuple[Path, Path]:
    duckdb = _need_duckdb()
    src = raw / "goodreads_books.json.gz"
    if not src.exists() or src.stat().st_size < 1_000_000_000:
        alt = raw / "goodreads_books_fantasy_paranormal.json.gz"
        if alt.exists():
            _log(f"WARNING: using genre slice {alt.name} (full books missing/incomplete)")
            src = alt
        else:
            raise FileNotFoundError(f"Need {src}")
    books_out = parquet_dir / "books.parquet"
    shelves_out = parquet_dir / "book_shelves.parquet"
    _log(f"books+shelves ← {src.name}")
    t0 = time.time()
    con = duckdb.connect()
    status_list = ", ".join(f"'{s}'" for s in sorted(STATUS_SHELVES))

    con.execute(
        f"""
        COPY (
            SELECT
                book_id::VARCHAR AS book_id,
                coalesce(work_id::VARCHAR, book_id::VARCHAR) AS work_id,
                title,
                title_without_series,
                CASE
                    WHEN authors IS NULL OR len(authors) = 0 THEN NULL
                    ELSE authors[1].author_id::VARCHAR
                END AS author_id,
                nullif(trim(language_code), '') AS language_code,
                try_cast(average_rating AS DOUBLE) AS average_rating,
                try_cast(ratings_count AS BIGINT) AS ratings_count,
                try_cast(text_reviews_count AS BIGINT) AS text_reviews_count,
                nullif(publication_year, '') AS publication_year,
                nullif(publisher, '') AS publisher,
                nullif(num_pages, '') AS num_pages,
                nullif(isbn, '') AS isbn,
                nullif(isbn13, '') AS isbn13,
                nullif(image_url, '') AS image_url,
                coalesce(
                    nullif(url, ''),
                    'https://www.goodreads.com/book/show/' || book_id::VARCHAR
                ) AS url
            FROM read_json(
                '{src}',
                format='newline_delimited',
                compression='gzip',
                ignore_errors=true
            )
            WHERE book_id IS NOT NULL
        ) TO '{books_out}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    _log(f"  … books parquet written ({time.time()-t0:.1f}s); exploding shelves…")

    con.execute(
        f"""
        COPY (
            SELECT
                b.book_id::VARCHAR AS book_id,
                lower(trim(shelf.name)) AS shelf,
                try_cast(shelf.count AS BIGINT) AS count,
                lower(trim(shelf.name)) IN ({status_list}) AS is_status
            FROM read_json(
                '{src}',
                format='newline_delimited',
                compression='gzip',
                ignore_errors=true
            ) b,
            UNNEST(b.popular_shelves) AS u(shelf)
            WHERE b.book_id IS NOT NULL
              AND shelf.name IS NOT NULL
              AND trim(shelf.name) <> ''
        ) TO '{shelves_out}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    n_books = con.execute(f"SELECT count(*) FROM read_parquet('{books_out}')").fetchone()[0]
    n_shelves = con.execute(
        f"SELECT count(*) FROM read_parquet('{shelves_out}')"
    ).fetchone()[0]
    _log(
        f"  → {books_out.name} ({n_books:,}) · {shelves_out.name} ({n_shelves:,}) "
        f"in {time.time()-t0:.0f}s"
    )
    con.close()
    return books_out, shelves_out


def export_interactions(raw: Path, parquet_dir: Path) -> Path:
    """Map CSV ids → Goodreads book_ids and write interactions.parquet via DuckDB."""
    duckdb = _need_duckdb()
    csv_path = raw / "goodreads_interactions.csv"
    map_path = raw / "book_id_map.csv"
    out = parquet_dir / "interactions.parquet"
    if not csv_path.exists() or csv_path.stat().st_size < 3_500_000_000:
        raise FileNotFoundError(
            f"Need complete {csv_path} (~4.0G); have "
            f"{csv_path.stat().st_size if csv_path.exists() else 0:,} bytes"
        )
    _log(f"interactions ← {csv_path.name} + {map_path.name}")
    t0 = time.time()
    con = duckdb.connect()
    # DuckDB reads CSV in parallel; join map; drop zero ratings optional later.
    con.execute(
        f"""
        COPY (
            SELECT
                i.user_id::BIGINT AS user_id,
                m.book_id::VARCHAR AS book_id,
                i.rating::INTEGER AS rating,
                i.is_read::BOOLEAN AS is_read,
                i.is_reviewed::BOOLEAN AS is_reviewed
            FROM read_csv(
                '{csv_path}',
                header=true,
                columns={{
                    'user_id': 'BIGINT',
                    'book_id': 'BIGINT',
                    'is_read': 'INTEGER',
                    'rating': 'INTEGER',
                    'is_reviewed': 'INTEGER'
                }}
            ) AS i
            JOIN read_csv(
                '{map_path}',
                header=true,
                columns={{'book_id_csv': 'BIGINT', 'book_id': 'VARCHAR'}}
            ) AS m
              ON i.book_id = m.book_id_csv
            WHERE i.rating > 0
        ) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    n = con.execute(
        f"SELECT count(*) FROM read_parquet('{out}')"
    ).fetchone()[0]
    _log(f"  → {out.name} ({n:,} rated rows) in {time.time()-t0:.0f}s")
    con.close()
    return out


def build_genre_scores_sql() -> str:
    """SQL expression list for genre score columns from book_shelves."""
    parts = []
    for col, shelves in GENRE_SHELF_GROUPS.items():
        in_list = ", ".join("'" + s.replace("'", "''") + "'" for s in sorted(shelves))
        parts.append(
            f"COALESCE(SUM(CASE WHEN shelf IN ({in_list}) THEN count ELSE 0 END), 0) "
            f"AS {col}"
        )
    # Catch-all: any shelf containing 'fantasy' that isn't already counted / sci hybrid
    parts.append(
        """
        COALESCE(SUM(CASE
            WHEN shelf LIKE '%fantasy%'
                 AND shelf NOT LIKE '%sci%'
                 AND shelf NOT LIKE '%science%'
                 AND shelf NOT IN (
                     'fantasy','high-fantasy','epic-fantasy','urban-fantasy',
                     'paranormal','paranormal-romance'
                 )
            THEN count ELSE 0 END), 0) AS fantasy_extra
        """.strip()
    )
    return ",\n        ".join(parts)


def open_warehouse(db_path: Path, parquet_dir: Path, *, read_only: bool = False):
    duckdb = _need_duckdb()
    con = duckdb.connect(str(db_path), read_only=read_only)
    # Always re-bind views to current parquet paths (portable across machines).
    books = parquet_dir / "books.parquet"
    shelves = parquet_dir / "book_shelves.parquet"
    authors = parquet_dir / "authors.parquet"
    interactions = parquet_dir / "interactions.parquet"

    if books.exists():
        con.execute(
            f"CREATE OR REPLACE VIEW books AS SELECT * FROM read_parquet('{books}')"
        )
    if shelves.exists():
        con.execute(
            f"CREATE OR REPLACE VIEW book_shelves AS SELECT * FROM read_parquet('{shelves}')"
        )
    if authors.exists():
        con.execute(
            f"CREATE OR REPLACE VIEW authors AS SELECT * FROM read_parquet('{authors}')"
        )
    if interactions.exists() and interactions.stat().st_size > 1_000_000:
        con.execute(
            f"""
            CREATE OR REPLACE VIEW interactions AS
            SELECT * FROM read_parquet('{interactions}')
            """
        )

    if books.exists() and authors.exists():
        con.execute(
            """
            CREATE OR REPLACE VIEW books_enriched AS
            SELECT
                b.*,
                a.name AS author_name,
                a.average_rating AS author_avg_rating,
                a.ratings_count AS author_ratings_count
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            """
        )

    if shelves.exists():
        scores = build_genre_scores_sql()
        con.execute(
            f"""
            CREATE OR REPLACE VIEW book_genre_scores AS
            SELECT
                book_id,
                {scores}
            FROM book_shelves
            WHERE NOT is_status
            GROUP BY book_id
            """
        )
        # Convenience: SF-likeness score used by the ballot builder defaults.
        con.execute(
            """
            CREATE OR REPLACE VIEW books_with_genres AS
            SELECT
                b.*,
                a.name AS author_name,
                g.sf_core,
                g.sf_soft,
                g.fantasy + g.fantasy_extra AS fantasy,
                g.romance,
                g.mystery,
                g.horror,
                g.ya,
                g.history_bio,
                (g.sf_core + 0.35 * g.sf_soft) AS sf_score,
                (g.fantasy + g.fantasy_extra + g.romance + g.ya + g.horror) AS non_sf_score,
                CASE
                    WHEN (g.sf_core + 0.35 * g.sf_soft
                          + g.fantasy + g.fantasy_extra + g.romance + g.ya + g.horror) > 0
                    THEN (g.sf_core + 0.35 * g.sf_soft)
                         / (g.sf_core + 0.35 * g.sf_soft
                            + g.fantasy + g.fantasy_extra + g.romance + g.ya + g.horror)
                    ELSE NULL
                END AS sf_ratio
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            LEFT JOIN book_genre_scores g ON b.book_id = g.book_id
            """
        )

    # Optional materialized SF cache (created by `materialize-sf`).
    return con


def materialize_sf_book_ids(
    con,
    *,
    min_sf_core: int = 10,
    min_sf_ratio: float = 0.55,
    min_ratings: int = 50,
    table_name: str = "sf_book_ids",
) -> int:
    """Cache book_ids matching the default SF shelf filter (speedup, not a silo).

    Primary gate: sf_core + sf_ratio (SF vs fantasy/romance/YA/horror).

    Extra gates recover science-fantasy that is heavily co-shelved as fantasy
    (Book of the New Sun, some Bas-Lag) without letting YA dystopia through:
    require either a strong absolute SF core at a softer ratio, or a weaker
    core that still leans SF-ratio with negligible YA.
    """
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(
        f"""
        CREATE TABLE {table_name} AS
        SELECT book_id, work_id, title, author_name, ratings_count,
               sf_core, sf_soft, fantasy, sf_score, sf_ratio
        FROM books_with_genres
        WHERE sf_core >= {int(min_sf_core)}
          AND ratings_count >= {int(min_ratings)}
          AND (
            sf_ratio >= {float(min_sf_ratio)}
            OR (
              sf_core >= 100
              AND sf_ratio >= 0.27
              AND coalesce(ya, 0) < sf_core
            )
            OR (
              sf_core >= 25
              AND sf_ratio >= 0.32
              AND coalesce(ya, 0) < 50
              AND fantasy > 0
            )
          )
          AND lower(coalesce(title, '')) NOT LIKE 'harry potter%'
          AND lower(coalesce(title, '')) NOT LIKE 'a game of thrones%'
          AND lower(coalesce(title, '')) NOT LIKE 'a clash of kings%'
          AND lower(coalesce(title, '')) NOT LIKE 'a storm of swords%'
          AND lower(coalesce(title, '')) NOT LIKE 'a feast for crows%'
          AND lower(coalesce(title, '')) NOT LIKE 'a dance with dragons%'
        """
    )
    n = con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
    return int(n)


def build_parquet(
    raw: Path,
    parquet_dir: Path,
    *,
    skip_interactions: bool = False,
    only: Optional[str] = None,
) -> None:
    parquet_dir.mkdir(parents=True, exist_ok=True)
    steps = {
        "authors": lambda: export_authors(raw, parquet_dir),
        "books": lambda: export_books_and_shelves(raw, parquet_dir),
        "interactions": lambda: export_interactions(raw, parquet_dir),
    }
    order = ["authors", "books", "interactions"]
    if only:
        order = [only]
    for name in order:
        if name == "interactions" and skip_interactions:
            _log("skip interactions")
            continue
        steps[name]()


def build_db(
    raw: Path,
    parquet_dir: Path,
    db_path: Path,
    *,
    materialize_sf: bool = True,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = open_warehouse(db_path, parquet_dir, read_only=False)
    # Smoke counts
    for view in ("books", "book_shelves", "authors", "interactions"):
        try:
            n = con.execute(f"SELECT count(*) FROM {view}").fetchone()[0]
            _log(f"view {view}: {n:,} rows")
        except Exception as e:
            _log(f"view {view}: missing ({e})")
    if materialize_sf:
        try:
            n = materialize_sf_book_ids(con)
            _log(f"materialized sf_book_ids: {n:,} books")
        except Exception as e:
            _log(f"sf materialize skipped: {e}")
    con.execute(
        """
        CREATE OR REPLACE TABLE warehouse_meta AS
        SELECT
            current_timestamp AS built_at,
            'UCSD Goodreads Book Graph — academic use only' AS note
        """
    )
    con.close()
    _log(f"Wrote {db_path}")


def cmd_query(db_path: Path, parquet_dir: Path, sql: str) -> None:
    con = open_warehouse(db_path, parquet_dir, read_only=db_path.exists())
    rel = con.execute(sql)
    cols = [d[0] for d in rel.description]
    print("\t".join(cols))
    for row in rel.fetchall():
        print("\t".join("" if v is None else str(v) for v in row))
    con.close()


def main(argv: Optional[list[str]] = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    p.add_argument("--parquet-dir", type=Path, default=DEFAULT_PARQUET)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build-parquet", help="Convert raw dumps → parquet/")
    b.add_argument("--skip-interactions", action="store_true")
    b.add_argument(
        "--only",
        choices=["authors", "books", "interactions"],
        default=None,
    )

    d = sub.add_parser("build-db", help="Create/refresh ucsd.duckdb views")
    d.add_argument("--no-materialize-sf", action="store_true")

    a = sub.add_parser("build-all", help="parquet + duckdb")
    a.add_argument("--skip-interactions", action="store_true")
    a.add_argument("--no-materialize-sf", action="store_true")

    q = sub.add_parser("query", help="Run SQL against the warehouse")
    q.add_argument("sql")

    m = sub.add_parser(
        "materialize-sf",
        help="Refresh cached sf_book_ids table (filter speedup)",
    )
    m.add_argument("--min-sf-core", type=int, default=10)
    m.add_argument("--min-sf-ratio", type=float, default=0.55)
    m.add_argument("--min-ratings", type=int, default=50)

    args = p.parse_args(argv)

    if args.cmd == "build-parquet":
        build_parquet(
            args.raw,
            args.parquet_dir,
            skip_interactions=args.skip_interactions,
            only=args.only,
        )
    elif args.cmd == "build-db":
        build_db(
            args.raw,
            args.parquet_dir,
            args.db,
            materialize_sf=not args.no_materialize_sf,
        )
    elif args.cmd == "build-all":
        build_parquet(
            args.raw,
            args.parquet_dir,
            skip_interactions=args.skip_interactions,
        )
        build_db(
            args.raw,
            args.parquet_dir,
            args.db,
            materialize_sf=not args.no_materialize_sf,
        )
    elif args.cmd == "query":
        cmd_query(args.db, args.parquet_dir, args.sql)
    elif args.cmd == "materialize-sf":
        con = open_warehouse(args.db, args.parquet_dir, read_only=False)
        n = materialize_sf_book_ids(
            con,
            min_sf_core=args.min_sf_core,
            min_sf_ratio=args.min_sf_ratio,
            min_ratings=args.min_ratings,
        )
        _log(f"sf_book_ids: {n:,}")
        con.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Ingest explorer ballot tables into DuckDB / Parquet.

Preferred sources (first hit wins):

1. ``data/ucsd_goodreads/derived/explorer_*.parquet`` (sidecars)
2. ``ranking_explorer/data/ucsd_sf.json`` (SF export bootstrap)
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "ranking_explorer" / "data" / "ucsd_sf.json"
DEFAULT_DERIVED = ROOT / "data" / "ucsd_goodreads" / "derived"
DEFAULT_DB = ROOT / "data" / "ucsd_goodreads" / "explorer.duckdb"


def _duckdb():
    try:
        import duckdb
    except ImportError as e:
        raise SystemExit(
            "Need duckdb. Run: python3 -m venv .venv && .venv/bin/pip install duckdb"
        ) from e
    return duckdb


def ingest_ucsd_sf_json(
    json_path: Path,
    *,
    db_path: Path = DEFAULT_DB,
    derived: Path = DEFAULT_DERIVED,
) -> dict[str, Any]:
    """Load the SF explorer JSON into DuckDB via CSV staging (fast)."""
    duckdb = _duckdb()
    derived.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"Loading {json_path}…", flush=True)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    print(f"  parsed in {time.time()-t0:.1f}s", flush=True)

    books = data.get("books") or {}
    voters = data.get("voters") or []

    books_csv = derived / "_stage_books.csv"
    users_csv = derived / "_stage_users.csv"
    entries_csv = derived / "_stage_entries.csv"

    with books_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "book_id",
                "work_id",
                "title",
                "author",
                "author_url",
                "book_url",
                "avg_rating",
                "ratings_count",
                "list_rank",
                "list_voters",
            ]
        )
        for bid, b in books.items():
            w.writerow(
                [
                    str(bid),
                    str(b.get("work_id") or bid),
                    b.get("title") or "",
                    b.get("author") or "",
                    b.get("author_url") or "",
                    b.get("book_url") or "",
                    b.get("avg_rating") if b.get("avg_rating") is not None else "",
                    int(b.get("ratings_count") or 0),
                    int(b.get("list_rank") or 0),
                    int(b.get("list_voters") or 0),
                ]
            )

    n_entries = 0
    with users_csv.open("w", encoding="utf-8", newline="") as uf, entries_csv.open(
        "w", encoding="utf-8", newline=""
    ) as ef:
        uw = csv.writer(uf)
        ew = csv.writer(ef)
        uw.writerow(
            ["user_id", "books_read", "ballot_size", "num_unique_authors"]
        )
        ew.writerow(["user_id", "book_id", "rank", "rating"])
        for v in voters:
            uid = str(v.get("user_id") or v.get("vote_id") or "")
            ballot = v.get("ballot") or []
            uw.writerow(
                [
                    uid,
                    int(v.get("books_read") or 0),
                    int(v.get("ballot_size") or len(ballot)),
                    int(v.get("num_unique_authors") or 0),
                ]
            )
            for e in ballot:
                rating = e.get("rating")
                ew.writerow(
                    [
                        uid,
                        str(e.get("book_id")),
                        int(e.get("rank") or 0),
                        int(rating) if rating not in (None, "") else "",
                    ]
                )
                n_entries += 1

    print(
        f"  staged CSV: {len(books):,} books, {len(voters):,} users, "
        f"{n_entries:,} entries ({time.time()-t0:.1f}s)",
        flush=True,
    )

    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    con.execute(
        f"""
        CREATE TABLE books AS
        SELECT
            book_id,
            work_id,
            nullif(title, '') AS title,
            nullif(author, '') AS author,
            nullif(author_url, '') AS author_url,
            nullif(book_url, '') AS book_url,
            try_cast(avg_rating AS DOUBLE) AS avg_rating,
            try_cast(ratings_count AS BIGINT) AS ratings_count,
            try_cast(list_rank AS INTEGER) AS list_rank,
            try_cast(list_voters AS INTEGER) AS list_voters
        FROM read_csv(
            '{books_csv}',
            header=true,
            columns={{
                'book_id': 'VARCHAR',
                'work_id': 'VARCHAR',
                'title': 'VARCHAR',
                'author': 'VARCHAR',
                'author_url': 'VARCHAR',
                'book_url': 'VARCHAR',
                'avg_rating': 'VARCHAR',
                'ratings_count': 'VARCHAR',
                'list_rank': 'VARCHAR',
                'list_voters': 'VARCHAR'
            }}
        )
        """
    )
    con.execute(
        f"""
        CREATE TABLE users AS
        SELECT
            user_id,
            try_cast(books_read AS INTEGER) AS books_read,
            try_cast(ballot_size AS INTEGER) AS ballot_size,
            try_cast(num_unique_authors AS INTEGER) AS num_unique_authors
        FROM read_csv(
            '{users_csv}',
            header=true,
            columns={{
                'user_id': 'VARCHAR',
                'books_read': 'VARCHAR',
                'ballot_size': 'VARCHAR',
                'num_unique_authors': 'VARCHAR'
            }}
        )
        """
    )
    con.execute(
        f"""
        CREATE TABLE ballot_entries AS
        SELECT
            user_id,
            book_id,
            try_cast(rank AS INTEGER) AS rank,
            try_cast(nullif(rating, '') AS INTEGER) AS rating
        FROM read_csv(
            '{entries_csv}',
            header=true,
            columns={{
                'user_id': 'VARCHAR',
                'book_id': 'VARCHAR',
                'rank': 'VARCHAR',
                'rating': 'VARCHAR'
            }}
        )
        """
    )
    con.execute("CREATE INDEX idx_be_book ON ballot_entries(book_id)")
    con.execute("CREATE INDEX idx_be_user ON ballot_entries(user_id)")

    books_pq = derived / "explorer_books.parquet"
    users_pq = derived / "explorer_users.parquet"
    entries_pq = derived / "explorer_ballot_entries.parquet"
    con.execute(f"COPY books TO '{books_pq}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.execute(f"COPY users TO '{users_pq}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.execute(
        f"COPY ballot_entries TO '{entries_pq}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )

    meta = {
        "source": str(json_path),
        "list_id": data.get("list_id"),
        "list_title": data.get("list_title"),
        "n_voters": len(voters),
        "n_books": len(books),
        "n_entries": n_entries,
        "anti_spam_applicable": data.get("anti_spam_applicable", False),
        "built_at": time.time(),
    }
    (derived / "explorer_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    con.close()

    for p in (books_csv, users_csv, entries_csv):
        try:
            p.unlink()
        except OSError:
            pass

    print(
        f"Wrote {db_path.name}: {meta['n_voters']:,} voters, "
        f"{meta['n_books']:,} books, {meta['n_entries']:,} entries "
        f"in {time.time()-t0:.1f}s",
        flush=True,
    )
    return meta


def open_explorer_db(db_path: Path = DEFAULT_DB, derived: Path = DEFAULT_DERIVED):
    """Open explorer DB, rebuilding from parquet sidecars if needed."""
    duckdb = _duckdb()
    books_pq = derived / "explorer_books.parquet"
    users_pq = derived / "explorer_users.parquet"
    entries_pq = derived / "explorer_ballot_entries.parquet"

    if not db_path.exists():
        if not (books_pq.exists() and users_pq.exists() and entries_pq.exists()):
            raise FileNotFoundError(
                f"No {db_path} and no parquet sidecars in {derived}. "
                f"Run: .venv/bin/python -m ucsd_explorer.ingest"
            )
        con = duckdb.connect(str(db_path))
        con.execute(
            f"CREATE TABLE books AS SELECT * FROM read_parquet('{books_pq}')"
        )
        con.execute(
            f"CREATE TABLE users AS SELECT * FROM read_parquet('{users_pq}')"
        )
        con.execute(
            f"CREATE TABLE ballot_entries AS SELECT * FROM read_parquet('{entries_pq}')"
        )
        return con

    return duckdb.connect(str(db_path), read_only=True)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path, default=DEFAULT_JSON)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = p.parse_args()
    ingest_ucsd_sf_json(args.json, db_path=args.db)

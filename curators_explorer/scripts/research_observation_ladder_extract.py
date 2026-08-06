#!/usr/bin/env python3
"""Collapse all Goodreads interactions to one observation state per user/work."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb

from curators_explorer.db import DB_PATH


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW = ROOT / "data" / "ucsd_goodreads" / "raw"
INTERACTIONS = RAW / "goodreads_interactions.csv"
BOOK_MAP = RAW / "book_id_map.csv"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    return parser.parse_args()


def paths(mode):
    stem = f"observation_ladder_{mode}"
    return (
        DATA_DIR / f"{stem}.parquet",
        DATA_DIR / f"{stem}.json",
        DATA_DIR / f"{stem.upper()}_REPORT.md",
    )


def raw_sql(limit):
    limit_sql = "" if limit is None else f"LIMIT {int(limit)}"
    return f"""
        SELECT * FROM read_csv(
            '{INTERACTIONS}', header=true,
            columns={{
                user_id: 'INTEGER', book_id: 'INTEGER', is_read: 'INTEGER',
                rating: 'INTEGER', is_reviewed: 'INTEGER'
            }}
        )
        {limit_sql}
    """


def main():
    args = parse_args()
    parquet, json_path, report = paths(args.mode)
    temporary = parquet.with_suffix(".tmp.parquet")
    if temporary.exists():
        temporary.unlink()
    limit = 500_000 if args.mode == "quick" else None
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    t0 = time.time()
    con.execute(
        f"""
        COPY (
            WITH raw AS ({raw_sql(limit)}), mapped AS (
                SELECT r.user_id, btw.work_id,
                       r.is_read::BOOLEAN AS is_read,
                       r.rating::UTINYINT AS rating,
                       r.is_reviewed::BOOLEAN AS is_reviewed
                FROM raw r
                JOIN read_csv(
                    '{BOOK_MAP}', header=true,
                    columns={{book_id_csv: 'INTEGER', book_id: 'VARCHAR'}}
                ) m ON r.book_id=m.book_id_csv
                JOIN ex.book_to_work btw ON m.book_id=btw.book_id
            )
            SELECT user_id, work_id,
                   bool_or(is_read) AS is_read,
                   max(rating)::UTINYINT AS rating,
                   bool_or(is_reviewed) AS is_reviewed,
                   count(*)::USMALLINT AS edition_interactions
            FROM mapped GROUP BY user_id, work_id
        ) TO '{temporary}'
        (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
        """
    )
    temporary.replace(parquet)
    extract_seconds = time.time() - t0
    row = con.execute(
        f"""
        SELECT count(*), count(DISTINCT user_id), count(DISTINCT work_id),
               count(*) FILTER (WHERE rating>0),
               count(*) FILTER (WHERE is_read AND rating=0),
               count(*) FILTER (WHERE NOT is_read AND rating=0),
               count(*) FILTER (WHERE is_reviewed),
               count(*) FILTER (WHERE is_reviewed AND rating=0),
               sum(edition_interactions)-count(*)
        FROM read_parquet('{parquet}')
        """
    ).fetchone()
    n = int(row[0])
    result = {
        "mode": args.mode,
        "source_rows": 228_648_342 if args.mode == "full" else limit,
        "user_work_rows": n,
        "users": int(row[1]),
        "works": int(row[2]),
        "rated": int(row[3]),
        "read_unrated": int(row[4]),
        "shelved_unread": int(row[5]),
        "reviewed": int(row[6]),
        "reviewed_unrated": int(row[7]),
        "collapsed_edition_duplicates": int(row[8]),
        "read_unrated_share_of_read": float(row[4] / max(row[3] + row[4], 1)),
        "extract_seconds": extract_seconds,
        "output_bytes": parquet.stat().st_size,
        "output": str(parquet),
    }
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Goodreads observation ladder",
        "",
        "All compact interactions are mapped to canonical works and collapsed to one state "
        "per user/work. Edition duplicates use maximum rating and boolean-any read/review.",
        "",
        f"- Mode: **{args.mode}**; source rows: **{result['source_rows']:,}**; "
        f"user-work rows: **{n:,}**.",
        f"- Users: **{result['users']:,}**; works: **{result['works']:,}**; output: "
        f"**{result['output_bytes']/1024**3:.2f} GiB**.",
        f"- Rated: **{result['rated']:,}**; read but unrated: "
        f"**{result['read_unrated']:,}**; shelved/unread: **{result['shelved_unread']:,}**.",
        f"- Read-unrated share of recorded reads: "
        f"**{100*result['read_unrated_share_of_read']:.2f}%**.",
        f"- Reviewed: **{result['reviewed']:,}**; reviewed but unrated: "
        f"**{result['reviewed_unrated']:,}**.",
        f"- Edition rows collapsed: **{result['collapsed_edition_duplicates']:,}**; "
        f"extraction time: **{extract_seconds/60:.1f} min**.",
        "",
        "`is_read=false` is only weak awareness/interest evidence. The selection audit uses "
        "`is_read=true, rating=0` as the defensible known-read missing-outcome state.",
        "",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    con.close()
    print(f"Wrote {report} ({extract_seconds:.1f}s)")


if __name__ == "__main__":
    main()

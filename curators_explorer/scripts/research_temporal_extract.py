#!/usr/bin/env python3
"""Extract compact temporal rating events from the detailed Goodreads archive.

The 11.5 GB gzip is scanned directly. No decompressed JSON is materialized.
Hashed detailed-interaction users are mapped back to compact numeric user IDs,
editions are joined to the existing work map, and timestamps are stored as UTC
epoch seconds for compact downstream trajectory analysis.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb

from curators_explorer.db import DB_PATH


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = ROOT / "data" / "ucsd_goodreads" / "raw"
SOURCE = RAW_DIR / "goodreads_interactions_dedup.json.gz"
USER_MAP = RAW_DIR / "user_id_map.csv"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    return parser.parse_args()


def paths(mode):
    stem = f"temporal_rated_events_{mode}"
    return (
        DATA_DIR / f"{stem}.parquet",
        DATA_DIR / f"{stem}_summary.json",
        DATA_DIR / f"{stem.upper()}_REPORT.md",
    )


def source_sql(limit):
    limit_sql = "" if limit is None else f"LIMIT {int(limit)}"
    return f"""
        WITH raw AS (
            SELECT *
            FROM read_json(
                '{SOURCE}',
                format='newline_delimited',
                compression='gzip',
                columns={{
                    user_id: 'VARCHAR',
                    book_id: 'VARCHAR',
                    rating: 'INTEGER',
                    date_added: 'VARCHAR',
                    date_updated: 'VARCHAR',
                    read_at: 'VARCHAR',
                    started_at: 'VARCHAR'
                }}
            )
            WHERE rating > 0
            {limit_sql}
        )
        SELECT
            um.user_id_csv::INTEGER AS user_id,
            btw.work_id::VARCHAR AS work_id,
            try_cast(j.book_id AS BIGINT) AS book_id,
            j.rating::UTINYINT AS rating,
            try_cast(epoch(try_strptime(nullif(j.date_added, ''),
                '%a %b %d %H:%M:%S %z %Y')) AS BIGINT) AS added_at,
            try_cast(epoch(try_strptime(nullif(j.date_updated, ''),
                '%a %b %d %H:%M:%S %z %Y')) AS BIGINT) AS updated_at,
            try_cast(epoch(try_strptime(nullif(j.read_at, ''),
                '%a %b %d %H:%M:%S %z %Y')) AS BIGINT) AS read_at,
            try_cast(epoch(try_strptime(nullif(j.started_at, ''),
                '%a %b %d %H:%M:%S %z %Y')) AS BIGINT) AS started_at,
            (j.date_added = j.date_updated)::BOOLEAN AS added_equals_updated
        FROM raw j
        JOIN user_map um ON j.user_id = um.user_hash
        JOIN ex.book_to_work btw ON j.book_id = btw.book_id
    """


def summarize(con, parquet, mode, elapsed):
    row = con.execute(
        f"""
        SELECT
            count(*) AS n,
            count(DISTINCT user_id) AS users,
            count(DISTINCT work_id) AS works,
            count(*) FILTER (WHERE added_at IS NOT NULL) AS n_added,
            count(*) FILTER (WHERE updated_at IS NOT NULL) AS n_updated,
            count(*) FILTER (WHERE read_at IS NOT NULL) AS n_read,
            count(*) FILTER (WHERE started_at IS NOT NULL) AS n_started,
            count(*) FILTER (WHERE added_equals_updated) AS n_same,
            count(*) FILTER (WHERE updated_at < added_at) AS n_updated_before_added,
            count(*) FILTER (WHERE read_at < added_at) AS n_read_before_added,
            count(*) FILTER (WHERE started_at > read_at) AS n_started_after_read,
            min(added_at), max(added_at), min(read_at), max(read_at)
        FROM read_parquet('{parquet}')
        """
    ).fetchone()
    n = int(row[0])
    duplicates = con.execute(
        f"""
        SELECT count(*) - count(DISTINCT (user_id, work_id))
        FROM read_parquet('{parquet}')
        """
    ).fetchone()[0]
    result = {
        "mode": mode,
        "source": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "output": str(parquet),
        "output_bytes": parquet.stat().st_size,
        "elapsed_seconds": elapsed,
        "rows": n,
        "users": int(row[1]),
        "works": int(row[2]),
        "duplicate_user_work_rows": int(duplicates),
        "coverage": {
            "added_at": row[3] / n,
            "updated_at": row[4] / n,
            "read_at": row[5] / n,
            "started_at": row[6] / n,
        },
        "quality": {
            "added_equals_updated": row[7] / n,
            "updated_before_added": row[8] / n,
            "read_before_added": row[9] / max(int(row[5]), 1),
            "started_after_read": row[10] / max(
                con.execute(
                    f"SELECT count(*) FROM read_parquet('{parquet}') "
                    "WHERE started_at IS NOT NULL AND read_at IS NOT NULL"
                ).fetchone()[0],
                1,
            ),
        },
        "ranges_epoch": {
            "added_min": row[11],
            "added_max": row[12],
            "read_min": row[13],
            "read_max": row[14],
        },
    }
    return result


def write_report(result, path):
    c = result["coverage"]
    q = result["quality"]
    lines = [
        "# Detailed Goodreads temporal extraction",
        "",
        "The detailed gzip was scanned directly and joined to numeric users and canonical "
        "works. Only rated events and the four temporal fields were retained; no decompressed "
        "JSON intermediate was written.",
        "",
        f"- Mode: **{result['mode']}**; rows: **{result['rows']:,}**; users: "
        f"**{result['users']:,}**; works: **{result['works']:,}**.",
        f"- Output: **{result['output_bytes']/1024**3:.2f} GiB**; extraction time: "
        f"**{result['elapsed_seconds']/60:.1f} min**.",
        f"- Timestamp coverage — added: **{100*c['added_at']:.2f}%**, updated: "
        f"**{100*c['updated_at']:.2f}%**, read: **{100*c['read_at']:.2f}%**, started: "
        f"**{100*c['started_at']:.2f}%**.",
        f"- Added equals updated: **{100*q['added_equals_updated']:.2f}%**; updated before "
        f"added: **{100*q['updated_before_added']:.3f}%**.",
        f"- Among populated read dates, read precedes Goodreads addition in "
        f"**{100*q['read_before_added']:.2f}%** of events.",
        f"- Duplicate edition/user-work rows retained for explicit downstream collapse: "
        f"**{result['duplicate_user_work_rows']:,}**.",
        "",
        "`added_at` and `updated_at` are Goodreads activity timestamps, not guaranteed rating "
        "timestamps. `read_at` and `started_at` are user-entered and nonrandomly missing. "
        "Trajectory models must carry timestamp-definition and bulk-import sensitivity axes.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    parquet, summary_path, report_path = paths(args.mode)
    limit = 500_000 if args.mode == "quick" else None
    temporary = parquet.with_suffix(".tmp.parquet")
    if temporary.exists():
        temporary.unlink()
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute(
        f"""
        CREATE TEMP TABLE user_map AS
        SELECT user_id_csv::INTEGER AS user_id_csv, user_id::VARCHAR AS user_hash
        FROM read_csv('{USER_MAP}', header=true, columns={{
            user_id_csv: 'INTEGER', user_id: 'VARCHAR'
        }})
        """
    )
    t0 = time.time()
    con.execute(
        f"COPY ({source_sql(limit)}) TO '{temporary}' "
        "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)"
    )
    temporary.replace(parquet)
    elapsed = time.time() - t0
    result = summarize(con, parquet, args.mode, elapsed)
    summary_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(result, report_path)
    con.close()
    print(f"Wrote {report_path} ({elapsed:.1f}s extraction)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Clean BrightData Goodreads metadata and join it to UCSD work IDs.

The 8GB source contains review text that is irrelevant to this project.  This
script parses it once, retains only stable identifiers and useful catalogue
fields, then produces an all-UCSD-work metadata table.  Exact Goodreads edition
IDs are the only join key; titles are never fuzzily joined.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb

from ucsd_explorer.db import PARQUET
from curators_explorer.db import DB_PATH


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "Goodreads-Books.csv"
CLEAN_BOOKS = PARQUET / "brightdata_books.parquet"
PROJECTED_BOOKS = ROOT / ".tmp" / "brightdata_metadata" / "brightdata_books_projected.parquet"
WORK_METADATA = PARQUET / "brightdata_work_metadata.parquet"
DATA = ROOT / "curators_explorer" / "data"
OUT_JSON = DATA / "brightdata_metadata_audit.json"
OUT_REPORT = DATA / "BRIGHTDATA_METADATA_AUDIT_REPORT.md"
YEAR_MIN = 1
YEAR_MAX = 2026


def connection() -> duckdb.DuckDBPyConnection:
    temp_dir = ROOT / ".tmp" / "brightdata_metadata"
    temp_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=4")
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"PRAGMA temp_directory='{temp_dir}'")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    return con


def csv_sql() -> str:
    # Explicit all-string parsing avoids a full-file inference pass and keeps
    # rare malformed numeric fields from changing the schema.
    return f"""
        read_csv(
            '{SOURCE}',
            header=true,
            all_varchar=true,
            strict_mode=false,
            ignore_errors=true,
            max_line_size=100000000
        )
    """


def build_clean_books(con: duckdb.DuckDBPyConnection) -> None:
    print(f"Projecting useful BrightData columns from {SOURCE.name}", flush=True)
    CLEAN_BOOKS.parent.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"""
        COPY (
            WITH parsed AS (
                SELECT
                    try_cast(
                        regexp_extract(
                            coalesce(nullif(trim(url), ''), trim(id)),
                            '(?:/book/show/)?([0-9]+)', 1
                        ) AS UBIGINT
                    ) AS book_id,
                    nullif(trim(url), '') AS url,
                    nullif(trim(name), '') AS title,
                    try_cast(author AS VARCHAR[]) AS authors,
                    nullif(trim(try(json_extract_string(author, '$[0]'))), '')
                        AS primary_author,
                    try_cast(genres AS VARCHAR[]) AS genres,
                    nullif(trim(first_published), '') AS first_published_raw,
                    try_cast(num_ratings AS UBIGINT) AS num_ratings,
                    try_cast(star_rating AS DOUBLE) AS star_rating
                FROM {csv_sql()}
            ), dated AS (
                SELECT *,
                    try_cast(
                        regexp_extract(first_published_raw, '(-?[0-9]{{1,4}})\\s*$', 1)
                        AS INTEGER
                    ) AS extracted_year
                FROM parsed
                WHERE book_id IS NOT NULL
            )
            SELECT
                book_id, url, title, authors, primary_author, genres,
                first_published_raw,
                CASE WHEN extracted_year BETWEEN {YEAR_MIN} AND {YEAR_MAX}
                     THEN extracted_year END::SMALLINT AS first_published_year,
                num_ratings, star_rating
            FROM dated
        ) TO '{PROJECTED_BOOKS}' (
            FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000
        )
        """
    )
    print("Deduplicating compact edition metadata", flush=True)
    clean_tmp = CLEAN_BOOKS.with_suffix(".tmp.parquet")
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM read_parquet('{PROJECTED_BOOKS}')
            QUALIFY row_number() OVER (
                PARTITION BY book_id
                ORDER BY
                    (first_published_raw IS NOT NULL) DESC,
                    (primary_author IS NOT NULL) DESC,
                    coalesce(num_ratings, 0) DESC,
                    url
            ) = 1
        ) TO '{clean_tmp}' (
            FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000
        )
        """
    )
    clean_tmp.replace(CLEAN_BOOKS)
    PROJECTED_BOOKS.unlink(missing_ok=True)


def build_work_metadata(con: duckdb.DuckDBPyConnection) -> None:
    print("Joining exact Goodreads edition IDs and aggregating works", flush=True)
    books = PARQUET / "books.parquet"
    con.execute(
        f"""
        COPY (
            WITH ucsd_editions AS (
                SELECT
                    try_cast(book_id AS UBIGINT) AS book_id,
                    work_id::VARCHAR AS work_id,
                    try_cast(publication_year AS INTEGER) AS edition_year
                FROM read_parquet('{books}')
                WHERE work_id IS NOT NULL
            ), ucsd_years AS (
                SELECT work_id,
                    min(edition_year) FILTER (
                        WHERE edition_year BETWEEN 1500 AND 2017
                    )::SMALLINT AS ucsd_min_edition_year,
                    round(quantile_cont(edition_year, 0.10) FILTER (
                        WHERE edition_year BETWEEN 1500 AND 2017
                    ))::SMALLINT AS ucsd_q10_edition_year,
                    count(*)::INTEGER AS ucsd_editions
                FROM ucsd_editions
                GROUP BY work_id
            ), matched AS (
                SELECT
                    u.work_id, b.book_id, b.url, b.title, b.authors,
                    b.primary_author, b.genres, b.first_published_raw,
                    b.first_published_year, b.num_ratings, b.star_rating
                FROM ucsd_editions u
                JOIN read_parquet('{CLEAN_BOOKS}') b USING (book_id)
            ), bright_year_counts AS (
                SELECT work_id, first_published_year, count(*) AS year_count
                FROM matched
                WHERE first_published_year IS NOT NULL
                GROUP BY work_id, first_published_year
            ), bright_modes AS (
                SELECT work_id, first_published_year AS brightdata_mode_year
                FROM bright_year_counts
                QUALIFY row_number() OVER (
                    PARTITION BY work_id
                    ORDER BY year_count DESC, first_published_year ASC
                ) = 1
            ), bright_aggregates AS (
                SELECT
                    work_id,
                    count(*)::INTEGER AS brightdata_matched_editions,
                    count(first_published_year)::INTEGER AS brightdata_dated_editions,
                    count(DISTINCT first_published_year)::INTEGER
                        AS brightdata_distinct_years,
                    min(first_published_year)::SMALLINT AS brightdata_min_year,
                    round(quantile_cont(first_published_year, 0.10))::SMALLINT
                        AS brightdata_q10_year,
                    arg_max(book_id, struct_pack(
                        ratings := coalesce(num_ratings, 0), book_id := book_id
                    )) AS representative_book_id,
                    arg_max(url, struct_pack(
                        ratings := coalesce(num_ratings, 0), book_id := book_id
                    )) AS url,
                    arg_max(title, struct_pack(
                        ratings := coalesce(num_ratings, 0), book_id := book_id
                    )) AS title,
                    arg_max(authors, struct_pack(
                        ratings := coalesce(num_ratings, 0), book_id := book_id
                    )) AS authors,
                    arg_max(primary_author, struct_pack(
                        ratings := coalesce(num_ratings, 0), book_id := book_id
                    )) AS primary_author,
                    arg_max(genres, struct_pack(
                        ratings := coalesce(num_ratings, 0), book_id := book_id
                    )) AS genres
                FROM matched
                GROUP BY work_id
            ), bright_works AS (
                SELECT a.*, m.brightdata_mode_year
                FROM bright_aggregates a
                LEFT JOIN bright_modes m USING(work_id)
            )
            SELECT
                u.work_id,
                b.representative_book_id,
                b.url,
                b.title,
                b.authors,
                b.primary_author,
                b.genres,
                b.brightdata_matched_editions,
                b.brightdata_dated_editions,
                b.brightdata_distinct_years,
                b.brightdata_min_year,
                b.brightdata_q10_year,
                b.brightdata_mode_year,
                u.ucsd_min_edition_year,
                u.ucsd_q10_edition_year,
                CASE WHEN b.brightdata_mode_year IS NOT NULL
                          AND u.ucsd_min_edition_year IS NOT NULL
                     THEN least(b.brightdata_mode_year, u.ucsd_min_edition_year)
                     ELSE coalesce(b.brightdata_mode_year, u.ucsd_min_edition_year)
                     END::SMALLINT AS best_first_published_year,
                CASE WHEN b.brightdata_mode_year IS NOT NULL
                          AND u.ucsd_min_edition_year IS NOT NULL
                          AND b.brightdata_mode_year < u.ucsd_min_edition_year
                     THEN 'brightdata_earlier'
                     WHEN b.brightdata_mode_year IS NOT NULL
                          AND u.ucsd_min_edition_year IS NOT NULL
                          AND b.brightdata_mode_year > u.ucsd_min_edition_year
                     THEN 'ucsd_earlier'
                     WHEN b.brightdata_mode_year IS NOT NULL
                          AND u.ucsd_min_edition_year IS NOT NULL
                     THEN 'sources_agree'
                     WHEN b.brightdata_mode_year IS NOT NULL
                     THEN 'brightdata_only'
                     WHEN u.ucsd_min_edition_year IS NOT NULL
                     THEN 'ucsd_only'
                     ELSE NULL END AS year_source,
                CASE WHEN b.brightdata_mode_year IS NOT NULL
                          AND u.ucsd_min_edition_year IS NOT NULL
                     THEN least(b.brightdata_mode_year, u.ucsd_min_edition_year) < 1000
                     ELSE coalesce(b.brightdata_mode_year, u.ucsd_min_edition_year) < 1000
                     END AS ancient_year_era_uncertain,
                u.ucsd_editions
            FROM ucsd_years u
            LEFT JOIN bright_works b USING (work_id)
        ) TO '{WORK_METADATA}' (
            FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000
        )
        """
    )


def audit(con: duckdb.DuckDBPyConnection, runtime: float) -> dict:
    clean = con.execute(
        f"""
        SELECT count(*) AS books,
               count(url) AS urls,
               count(primary_author) AS authors,
               count(genres) AS genres,
               count(first_published_raw) AS raw_dates,
               count(first_published_year) AS parsed_years,
               min(first_published_year) AS min_year,
               max(first_published_year) AS max_year
        FROM read_parquet('{CLEAN_BOOKS}')
        """
    ).fetchone()
    joined = con.execute(
        f"""
        SELECT count(*) AS works,
               count(representative_book_id) AS matched_works,
               sum(brightdata_matched_editions) AS matched_editions,
               count(brightdata_mode_year) AS bright_year_works,
               count(ucsd_min_edition_year) AS ucsd_year_works,
               count(best_first_published_year) AS best_year_works,
               count(primary_author) AS author_works,
               count(genres) AS genre_works,
               count(*) FILTER (
                   WHERE brightdata_mode_year IS NOT NULL
                     AND ucsd_min_edition_year IS NOT NULL
                     AND brightdata_mode_year < ucsd_min_edition_year
               ) AS bright_earlier,
               count(*) FILTER (
                   WHERE brightdata_mode_year IS NOT NULL
                     AND ucsd_min_edition_year IS NOT NULL
                     AND brightdata_mode_year > ucsd_min_edition_year
               ) AS bright_later,
               count(*) FILTER (WHERE brightdata_distinct_years > 1) AS conflicting_year_works,
               median(abs(brightdata_mode_year - ucsd_min_edition_year)) FILTER (
                   WHERE brightdata_mode_year IS NOT NULL
                     AND ucsd_min_edition_year IS NOT NULL
               ) AS median_abs_gap,
               count(*) FILTER (WHERE ancient_year_era_uncertain) AS ancient_era_uncertain
        FROM read_parquet('{WORK_METADATA}')
        """
    ).fetchone()
    examples = con.execute(
        f"""
        SELECT title, primary_author, brightdata_mode_year, brightdata_min_year,
               ucsd_min_edition_year, best_first_published_year,
               brightdata_matched_editions, brightdata_distinct_years
        FROM read_parquet('{WORK_METADATA}')
        WHERE (lower(title), lower(primary_author)) IN (
            ('moby-dick or, the whale', 'herman melville'),
            ('ulysses', 'james joyce'),
            ('the brothers karamazov', 'fyodor dostoevsky'),
            ('the great gatsby', 'f. scott fitzgerald'),
            ('one hundred years of solitude', 'gabriel garcía márquez'),
            ('one hundred years of solitude', 'gabriel garcia marquez'),
            ('the odyssey', 'homer'),
            ('the iliad', 'homer'),
            ('don quixote', 'miguel de cervantes saavedra'),
            ('don quixote', 'miguel de cervantes')
        )
        ORDER BY title
        """
    ).fetchall()
    author_audit = con.execute(
        f"""
        SELECT count(*) FILTER (
                   WHERE w.primary_author IS NOT NULL AND s.author IS NOT NULL
               ) AS comparable,
               count(*) FILTER (
                   WHERE lower(regexp_replace(w.primary_author, '[^[:alnum:]]', '', 'g')) =
                         lower(regexp_replace(s.author, '[^[:alnum:]]', '', 'g'))
               ) AS normalized_equal,
               count(*) FILTER (
                   WHERE w.primary_author IS NOT NULL
                     AND nullif(trim(s.author), '') IS NULL
               ) AS bright_fills_blank,
               count(*) FILTER (
                   WHERE w.primary_author IS NOT NULL AND s.author IS NOT NULL
                     AND lower(regexp_replace(w.primary_author, '[^[:alnum:]]', '', 'g')) <>
                         lower(regexp_replace(s.author, '[^[:alnum:]]', '', 'g'))
               ) AS different
        FROM read_parquet('{WORK_METADATA}') w
        JOIN ex.work_scores s USING (work_id)
        """
    ).fetchone()
    return {
        "source": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "clean_books_path": str(CLEAN_BOOKS),
        "clean_books_bytes": CLEAN_BOOKS.stat().st_size,
        "work_metadata_path": str(WORK_METADATA),
        "work_metadata_bytes": WORK_METADATA.stat().st_size,
        "runtime_seconds": runtime,
        "clean_books": dict(zip(
            ["books", "urls", "authors", "genres", "raw_dates", "parsed_years", "min_year", "max_year"],
            map(lambda x: int(x) if x is not None else None, clean),
        )),
        "joined_works": dict(zip(
            [
                "works", "matched_works", "matched_editions", "bright_year_works",
                "ucsd_year_works", "best_year_works", "author_works", "genre_works",
                "bright_earlier", "bright_later", "conflicting_year_works", "median_abs_gap",
                "ancient_era_uncertain",
            ],
            [int(x) if x is not None else None for x in joined],
        )),
        "examples": [
            dict(zip(
                [
                    "title", "author", "bright_mode_year", "bright_min_year",
                    "ucsd_min_edition_year", "best_year", "matched_editions",
                    "bright_distinct_years",
                ],
                [
                    title, author,
                    *[int(x) if x is not None else None for x in values],
                ],
            ))
            for title, author, *values in examples
        ],
        "author_comparison": dict(zip(
            ["comparable", "normalized_equal", "bright_fills_blank", "different"],
            [int(x) for x in author_audit],
        )),
        "join_policy": "exact Goodreads edition book_id only; no fuzzy title matching",
        "year_policy": "earlier of modal valid BrightData first_published and minimum UCSD edition year",
    }


def write_report(result: dict) -> None:
    c = result["clean_books"]
    j = result["joined_works"]
    lines = [
        "# BrightData Goodreads metadata audit",
        "",
        "The downloaded BrightData CSV is joined to UCSD by exact Goodreads edition `book_id` "
        "extracted from `url`. No fuzzy title or author matching is used. The work-level year is "
        "the earlier of the modal valid BrightData `first_published` year across matched editions "
        "and the minimum UCSD edition year. A claimed first publication cannot logically postdate "
        "an observed edition.",
        "",
        f"Runtime: **{result['runtime_seconds']:.1f}s**. The {result['source_bytes']/2**30:.2f} GiB "
        f"CSV becomes a {result['clean_books_bytes']/2**20:.1f} MiB useful-column edition table "
        f"and a {result['work_metadata_bytes']/2**20:.1f} MiB joined work table.",
        "",
        "## Coverage",
        "",
        f"- BrightData editions: **{c['books']:,}**; parsed first-published years: "
        f"**{c['parsed_years']:,}**; authors: **{c['authors']:,}**; genre lists: "
        f"**{c['genres']:,}**.",
        f"- UCSD works: **{j['works']:,}**; exact matched works: **{j['matched_works']:,}** "
        f"from **{j['matched_editions']:,}** matched editions.",
        f"- BrightData-year works: **{j['bright_year_works']:,}**; UCSD-year works: "
        f"**{j['ucsd_year_works']:,}**; combined best-year works: **{j['best_year_works']:,}**.",
        f"- Work-level author coverage: **{j['author_works']:,}**; genre coverage: "
        f"**{j['genre_works']:,}**.",
        f"- Of **{result['author_comparison']['comparable']:,}** works with both author names, "
        f"**{result['author_comparison']['normalized_equal']:,}** agree after simple normalization "
        f"and **{result['author_comparison']['different']:,}** differ; BrightData fills "
        f"**{result['author_comparison']['bright_fills_blank']:,}** blank current names.",
        "",
        "## Date comparison",
        "",
        f"Where both exist, BrightData is earlier for **{j['bright_earlier']:,}** works and "
        f"later for **{j['bright_later']:,}**; median absolute gap is "
        f"**{j['median_abs_gap']:,} years**. **{j['conflicting_year_works']:,}** matched works "
        "have more than one BrightData first-published year across editions.",
        f"**{j['ancient_era_uncertain']:,}** works have a chosen year below 1000 and are flagged "
        "`ancient_year_era_uncertain`: the scrape does not reliably preserve BCE/CE semantics "
        "for values such as Homer's 701. This does not affect the canon oldness score because "
        "all such years are already at its capped maximum.",
        "",
        "| work | author | Bright mode | Bright min | UCSD edition min | chosen | matched editions | distinct Bright years |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["examples"]:
        lines.append(
            f"| *{row['title']}* | {row['author']} | {row['bright_mode_year']} | "
            f"{row['bright_min_year']} | {row['ucsd_min_edition_year']} | {row['best_year']} | "
            f"{row['matched_editions']} | {row['bright_distinct_years']} |"
        )
    lines += [
        "",
        "## Stored fields",
        "",
        "The compact edition table retains URL, title, parsed author list, primary author, parsed "
        "genre list, raw and parsed first-publication date, rating count, and average rating. "
        "The work table adds exact-match coverage, BrightData year diagnostics, UCSD fallback "
        "years, the chosen year with provenance, and representative URL/author/genres. The same "
        "rows are materialized as `brightdata_work_metadata` in `explorer.duckdb` for later "
        "frontend filtering without reparsing or attaching the source CSV.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize_explorer_table() -> None:
    print("Materializing explorer.brightdata_work_metadata", flush=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS brightdata_work_metadata")
    con.execute(
        f"CREATE TABLE brightdata_work_metadata AS SELECT * FROM read_parquet('{WORK_METADATA}')"
    )
    con.execute(
        "CREATE UNIQUE INDEX idx_brightdata_work_metadata "
        "ON brightdata_work_metadata(work_id)"
    )
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild-clean", action="store_true")
    args = parser.parse_args()
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}")
    t0 = time.time()
    con = connection()
    if args.rebuild_clean or not CLEAN_BOOKS.exists():
        build_clean_books(con)
    else:
        print(f"Reusing {CLEAN_BOOKS}", flush=True)
    build_work_metadata(con)
    result = audit(con, time.time() - t0)
    con.close()
    materialize_explorer_table()
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(result)
    print(f"Wrote {CLEAN_BOOKS}")
    print(f"Wrote {WORK_METADATA}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

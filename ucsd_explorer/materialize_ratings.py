#!/usr/bin/env python3
"""Materialize rating-based explorer tables from the UCSD warehouse.

Star ratings are unordered — we keep full 1–5★ distributions and per-user
pickiness so the explorer can find favorites / divisive books without fake ranks.

Corpus includes all books above ``min_book_ratings`` (Goodreads count), tagged
with ``is_sf`` from the shelf filter so the UI can toggle SF-only vs all genres.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from ucsd_explorer.db import DERIVED, EXPLORER_DB, META_PATH, PARQUET, ROOT

WAREHOUSE_DB = ROOT / "data" / "ucsd_goodreads" / "ucsd.duckdb"


def materialize(
    *,
    min_sf_core: int = 10,
    min_sf_ratio: float = 0.55,
    min_book_ratings: int = 50,
    min_user_ratings: int = 5,
) -> dict:
    import duckdb
    from ucsd_goodreads.warehouse import materialize_sf_book_ids, open_warehouse

    DERIVED.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ix_pq = PARQUET / "interactions.parquet"
    books_pq = PARQUET / "books.parquet"
    if not ix_pq.exists():
        raise SystemExit(f"Missing {ix_pq}")
    if not books_pq.exists():
        raise SystemExit(f"Missing {books_pq}")

    # Ensure SF id cache exists on warehouse (for is_sf tagging)
    wh = open_warehouse(WAREHOUSE_DB, PARQUET, read_only=False)
    try:
        n_sf = wh.execute("SELECT count(*) FROM sf_book_ids").fetchone()[0]
        print(f"sf_book_ids: {n_sf:,}", flush=True)
    except Exception:
        n_sf = materialize_sf_book_ids(
            wh,
            min_sf_core=min_sf_core,
            min_sf_ratio=min_sf_ratio,
            min_ratings=min_book_ratings,
        )
        print(f"created sf_book_ids: {n_sf:,}", flush=True)

    books_tmp = DERIVED / "_explorer_books_tmp.parquet"
    print(
        f"Exporting all books with ratings_count ≥ {min_book_ratings} "
        f"(tagging is_sf)…",
        flush=True,
    )
    wh.execute(
        f"""
        COPY (
            SELECT
                b.book_id::VARCHAR AS book_id,
                b.work_id::VARCHAR AS work_id,
                b.title,
                a.name AS author,
                b.author_id::VARCHAR AS author_id,
                b.url AS book_url,
                b.average_rating AS avg_rating,
                b.ratings_count,
                coalesce(s.sf_core, 0) AS sf_core,
                coalesce(s.sf_ratio, 0) AS sf_ratio,
                (s.book_id IS NOT NULL) AS is_sf
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            LEFT JOIN sf_book_ids s ON b.book_id = s.book_id
            WHERE b.ratings_count >= {int(min_book_ratings)}
              AND b.work_id IS NOT NULL
        ) TO '{books_tmp}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    wh.close()

    if EXPLORER_DB.exists():
        EXPLORER_DB.unlink()
    con = duckdb.connect(str(EXPLORER_DB))

    print("Loading books…", flush=True)
    con.execute(
        f"""
        CREATE TABLE books AS
        SELECT
            book_id,
            work_id,
            title,
            author,
            CASE WHEN author_id IS NULL OR author_id = '' THEN NULL
                 ELSE 'https://www.goodreads.com/author/show/' || author_id END AS author_url,
            book_url,
            avg_rating,
            ratings_count,
            sf_core,
            sf_ratio,
            is_sf
        FROM read_parquet('{books_tmp}')
        """
    )
    n_books = con.execute("SELECT count(*) FROM books").fetchone()[0]
    n_sf_books = con.execute("SELECT count(*) FROM books WHERE is_sf").fetchone()[0]
    print(f"  books: {n_books:,} ({n_sf_books:,} SF-tagged)", flush=True)

    # A work is SF if any edition is SF-tagged
    con.execute(
        """
        CREATE TABLE works AS
        SELECT
            work_id,
            arg_max(book_id, ratings_count) AS book_id,
            arg_max(title, ratings_count) AS title,
            arg_max(author, ratings_count) AS author,
            arg_max(author_url, ratings_count) AS author_url,
            arg_max(book_url, ratings_count) AS book_url,
            arg_max(avg_rating, ratings_count) AS avg_rating,
            max(ratings_count) AS ratings_count,
            bool_or(is_sf) AS is_sf,
            max(sf_core) AS sf_core,
            max(sf_ratio) AS sf_ratio
        FROM books
        GROUP BY work_id
        """
    )
    con.execute("CREATE TABLE book_to_work AS SELECT book_id, work_id FROM books")
    n_works_all = con.execute("SELECT count(*) FROM works").fetchone()[0]
    n_works_sf = con.execute("SELECT count(*) FROM works WHERE is_sf").fetchone()[0]
    print(f"  works: {n_works_all:,} ({n_works_sf:,} SF)", flush=True)

    print("User pickiness (global)…", flush=True)
    con.execute(
        f"""
        CREATE TABLE user_pickiness AS
        SELECT
            user_id,
            count(*)::BIGINT AS n_rated,
            sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n_five,
            sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::DOUBLE / count(*) AS five_rate
        FROM read_parquet('{ix_pq}')
        WHERE rating > 0
        GROUP BY user_id
        HAVING count(*) >= {int(min_user_ratings)}
        """
    )
    med = float(
        con.execute("SELECT quantile_cont(five_rate, 0.5) FROM user_pickiness").fetchone()[0]
    )
    print(
        f"  {con.execute('select count(*) from user_pickiness').fetchone()[0]:,} users; "
        f"median five_rate={med:.3f}",
        flush=True,
    )

    print("Collapsing edition ratings → works (all genres)…", flush=True)
    con.execute(
        f"""
        CREATE TABLE all_rating_events AS
        WITH rated AS (
            SELECT
                btw.work_id,
                i.user_id,
                max(i.rating) AS rating
            FROM read_parquet('{ix_pq}') i
            JOIN book_to_work btw ON i.book_id = btw.book_id
            WHERE i.rating > 0
            GROUP BY 1, 2
        )
        SELECT
            r.work_id,
            r.user_id,
            r.rating,
            u.n_rated,
            u.five_rate,
            least(20.0, greatest(0.25, {med} / nullif(u.five_rate, 0))) AS picky_weight,
            w.is_sf
        FROM rated r
        JOIN user_pickiness u ON r.user_id = u.user_id
        JOIN works w ON r.work_id = w.work_id
        """
    )

    print("Work-level stats…", flush=True)
    con.execute(
        """
        CREATE TABLE work_stats AS
        SELECT
            work_id,
            count(*)::BIGINT AS n,
            avg(rating)::DOUBLE AS mean,
            stddev_pop(rating)::DOUBLE AS std,
            sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5,
            sum(CASE WHEN rating = 4 THEN 1 ELSE 0 END)::BIGINT AS n4,
            sum(CASE WHEN rating = 3 THEN 1 ELSE 0 END)::BIGINT AS n3,
            sum(CASE WHEN rating = 2 THEN 1 ELSE 0 END)::BIGINT AS n2,
            sum(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::BIGINT AS n1,
            sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::BIGINT AS n_low,
            (sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p5,
            (sum(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p1,
            (sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p_low
        FROM all_rating_events
        GROUP BY work_id
        """
    )

    con.execute(
        """
        CREATE TABLE five_star_events AS
        SELECT work_id, user_id, n_rated, five_rate, picky_weight, is_sf
        FROM all_rating_events
        WHERE rating = 5
        """
    )
    con.execute(
        """
        CREATE TABLE work_picky AS
        SELECT
            work_id,
            count(*)::BIGINT AS n5_picky_events,
            sum(picky_weight)::DOUBLE AS picky_five_mass,
            avg(picky_weight)::DOUBLE AS mean_picky_weight
        FROM five_star_events
        GROUP BY work_id
        """
    )
    con.execute(
        """
        CREATE TABLE work_scores AS
        SELECT
            w.work_id,
            w.book_id,
            w.title,
            w.author,
            w.author_url,
            w.book_url,
            w.avg_rating,
            w.ratings_count,
            w.is_sf,
            s.n, s.mean, s.std,
            s.n5, s.n4, s.n3, s.n2, s.n1, s.n_low,
            s.p5, s.p1, s.p_low,
            (4.0 * s.p5 * s.p_low) AS polarization
        FROM works w
        JOIN work_stats s USING (work_id)
        """
    )

    global_p5_all = float(
        con.execute("SELECT sum(n5)::DOUBLE / sum(n) FROM work_stats").fetchone()[0]
    )
    global_p5_sf = float(
        con.execute(
            """
            SELECT sum(s.n5)::DOUBLE / sum(s.n)
            FROM work_stats s
            JOIN works w USING (work_id)
            WHERE w.is_sf
            """
        ).fetchone()[0]
    )
    mean_all = float(con.execute("SELECT avg(mean) FROM work_scores").fetchone()[0])
    mean_sf = float(
        con.execute("SELECT avg(mean) FROM work_scores WHERE is_sf").fetchone()[0]
    )
    con.execute(
        """
        CREATE TABLE explorer_globals AS
        SELECT
            ?::DOUBLE AS global_p5,
            ?::DOUBLE AS global_p5_sf,
            ?::DOUBLE AS global_p5_all,
            ?::DOUBLE AS global_mean,
            ?::DOUBLE AS global_mean_sf,
            ?::DOUBLE AS global_mean_all,
            ?::DOUBLE AS median_user_five_rate
        """,
        [global_p5_sf, global_p5_sf, global_p5_all, mean_sf, mean_sf, mean_all, med],
    )
    con.execute("CREATE INDEX idx_fse_work ON five_star_events(work_id)")
    con.execute("CREATE INDEX idx_are_work ON all_rating_events(work_id)")
    con.execute("CREATE INDEX idx_are_user ON all_rating_events(user_id)")
    con.execute("CREATE INDEX idx_ws_sf ON work_scores(is_sf)")
    con.execute("CREATE INDEX idx_are_sf ON all_rating_events(is_sf)")
    con.execute("CREATE INDEX idx_fse_sf ON five_star_events(is_sf)")

    n_works = con.execute("SELECT count(*) FROM work_scores").fetchone()[0]
    n_works_sf = con.execute("SELECT count(*) FROM work_scores WHERE is_sf").fetchone()[0]
    n_five = con.execute("SELECT count(*) FROM five_star_events").fetchone()[0]
    n_five_sf = con.execute(
        "SELECT count(*) FROM five_star_events WHERE is_sf"
    ).fetchone()[0]
    n_events = con.execute("SELECT count(*) FROM all_rating_events").fetchone()[0]
    n_events_sf = con.execute(
        "SELECT count(*) FROM all_rating_events WHERE is_sf"
    ).fetchone()[0]
    meta = {
        "list_id": "ucsd_ratings",
        "list_title": "UCSD Goodreads — favorites (5★)",
        "source": "warehouse parquet (unordered ratings; SF toggleable)",
        "n_works": int(n_works),
        "n_works_sf": int(n_works_sf),
        "n_rating_events": int(n_events),
        "n_rating_events_sf": int(n_events_sf),
        "n_five_star_events": int(n_five),
        "n_five_star_events_sf": int(n_five_sf),
        "n_users_pickiness": int(
            con.execute("SELECT count(*) FROM user_pickiness").fetchone()[0]
        ),
        "global_p5": global_p5_sf,
        "global_p5_sf": global_p5_sf,
        "global_p5_all": global_p5_all,
        "global_mean_sf": mean_sf,
        "global_mean_all": mean_all,
        "median_user_five_rate": med,
        "min_sf_core": min_sf_core,
        "min_sf_ratio": min_sf_ratio,
        "min_book_ratings": min_book_ratings,
        "genre_filter_available": True,
        "anti_spam_applicable": False,
        "ballot_model": "unordered_ratings",
        "built_at": time.time(),
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    con.close()
    try:
        books_tmp.unlink()
    except OSError:
        pass
    print(
        f"Wrote {EXPLORER_DB.name}: {n_works:,} works ({n_works_sf:,} SF), "
        f"{n_events:,} ratings ({n_events_sf:,} SF), "
        f"{n_five:,} five-stars in {time.time()-t0:.1f}s",
        flush=True,
    )
    try:
        from ucsd_explorer.taste import materialize_taste

        print("Materializing taste filter…", flush=True)
        taste_meta = materialize_taste()
        meta["taste"] = taste_meta
        META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"Taste materialize skipped/failed: {e}", flush=True)

    try:
        from ucsd_explorer.catalog_flags import materialize_catalog_flags

        print("Materializing catalog flags…", flush=True)
        cat_meta = materialize_catalog_flags(db_path=EXPLORER_DB)
        meta["catalog_flags"] = cat_meta
        meta["catalog_flags_available"] = True
        META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"Catalog flags skipped/failed: {e}", flush=True)

    try:
        from ucsd_explorer.genres import materialize_genres

        print("Materializing genre tags…", flush=True)
        genre_meta = materialize_genres(db_path=EXPLORER_DB)
        meta["genres"] = genre_meta
        meta["genres_available"] = True
        META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"Genre tags skipped/failed: {e}", flush=True)

    import duckdb as d2

    c = d2.connect(str(EXPLORER_DB), read_only=True)
    light = c.execute(
        """
        SELECT title, n, mean, p5, is_sf
        FROM work_scores WHERE book_id = '17735' OR title = 'Light'
        ORDER BY n DESC LIMIT 5
        """
    ).fetchall()
    print("Light-ish rows:", light, flush=True)
    c.close()
    return meta


def retarget_is_sf(
    *,
    min_sf_core: int = 10,
    min_sf_ratio: float = 0.55,
    min_book_ratings: int = 50,
) -> dict:
    """Rebuild warehouse sf_book_ids and patch is_sf on the explorer DB in place.

    Avoids a full ratings rematerialize (which drops taste / curator tables).
    """
    import duckdb
    from ucsd_goodreads.warehouse import materialize_sf_book_ids, open_warehouse

    t0 = time.time()
    wh = open_warehouse(WAREHOUSE_DB, PARQUET, read_only=False)
    try:
        n_sf = materialize_sf_book_ids(
            wh,
            min_sf_core=min_sf_core,
            min_sf_ratio=min_sf_ratio,
            min_ratings=min_book_ratings,
        )
        print(f"sf_book_ids rebuilt: {n_sf:,}", flush=True)
    finally:
        wh.close()

    if not EXPLORER_DB.exists():
        raise SystemExit(f"Missing {EXPLORER_DB}")

    con = duckdb.connect(str(EXPLORER_DB))
    con.execute(f"ATTACH '{WAREHOUSE_DB}' AS wh (READ_ONLY)")
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE _sf_books AS
        SELECT DISTINCT book_id::VARCHAR AS book_id FROM wh.sf_book_ids
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE _sf_works AS
        SELECT DISTINCT work_id::VARCHAR AS work_id
        FROM wh.sf_book_ids
        WHERE work_id IS NOT NULL
        """
    )
    before = con.execute(
        "SELECT count(*) FROM work_scores WHERE coalesce(is_sf, FALSE)"
    ).fetchone()[0]

    def _retarget(table: str, key: str, sf_table: str) -> None:
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if table not in tables:
            return
        tmp = f"_{table}_sf_new"
        con.execute(f"DROP TABLE IF EXISTS {tmp}")
        con.execute(
            f"""
            CREATE TABLE {tmp} AS
            SELECT t.* EXCLUDE (is_sf),
                   (s.{key} IS NOT NULL) AS is_sf
            FROM {table} t
            LEFT JOIN {sf_table} s USING ({key})
            """
        )
        con.execute(f"DROP TABLE {table}")
        con.execute(f"ALTER TABLE {tmp} RENAME TO {table}")

    _retarget("books", "book_id", "_sf_books")
    _retarget("works", "work_id", "_sf_works")
    _retarget("work_scores", "work_id", "_sf_works")
    _retarget("all_rating_events", "work_id", "_sf_works")
    _retarget("five_star_events", "work_id", "_sf_works")

    con.execute("CREATE INDEX IF NOT EXISTS idx_ws_sf ON work_scores(is_sf)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_ws_n ON work_scores(n)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_are_sf ON all_rating_events(is_sf)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_fse_sf ON five_star_events(is_sf)")

    con.execute("DETACH wh")
    con.close()

    # Soft literary + multi-gate prevalence (source of truth for the UI).
    # Overwrites is_sf from the sf gate after the warehouse-based patch.
    from ucsd_explorer.genre_gates import materialize_genre_gates

    gate_stats = materialize_genre_gates(db_path=EXPLORER_DB)

    import duckdb as _duck

    con2 = _duck.connect(str(EXPLORER_DB))
    after = con2.execute(
        "SELECT count(*) FROM work_scores WHERE coalesce(is_sf, FALSE)"
    ).fetchone()[0]
    wolfe = con2.execute(
        """
        SELECT title, is_sf, n FROM work_scores
        WHERE author ILIKE 'Gene Wolfe'
          AND (title ILIKE '%torturer%' OR title ILIKE '%new sun%'
               OR title ILIKE '%fifth head%' OR title ILIKE '%claw of%'
               OR title ILIKE '%sword of the lictor%' OR title ILIKE '%citadel%')
        ORDER BY n DESC
        """
    ).fetchall()
    con2.close()

    stats = {
        "sf_book_ids": n_sf,
        "work_scores_sf_before": int(before),
        "work_scores_sf_after": int(after),
        "genre_gates": gate_stats,
        "elapsed_s": round(time.time() - t0, 1),
        "wolfe_sample": [
            {"title": t, "is_sf": bool(s), "n": int(n)} for t, s, n in wolfe
        ],
    }
    print(
        f"is_sf retarget: works SF {before:,} → {after:,} in {stats['elapsed_s']}s",
        flush=True,
    )
    for row in wolfe[:10]:
        print(f"  {row}", flush=True)
    return stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--min-sf-core", type=int, default=10)
    p.add_argument("--min-sf-ratio", type=float, default=0.55)
    p.add_argument("--min-book-ratings", type=int, default=50)
    p.add_argument("--min-user-ratings", type=int, default=5)
    p.add_argument(
        "--retarget-sf-only",
        action="store_true",
        help="Only rebuild sf_book_ids and patch is_sf (keep taste/curators)",
    )
    args = p.parse_args()
    if args.retarget_sf_only:
        retarget_is_sf(
            min_sf_core=args.min_sf_core,
            min_sf_ratio=args.min_sf_ratio,
            min_book_ratings=args.min_book_ratings,
        )
        return
    materialize(
        min_sf_core=args.min_sf_core,
        min_sf_ratio=args.min_sf_ratio,
        min_book_ratings=args.min_book_ratings,
        min_user_ratings=args.min_user_ratings,
    )


if __name__ == "__main__":
    main()

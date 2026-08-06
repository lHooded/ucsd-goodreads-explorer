#!/usr/bin/env python3
"""Audit edition/language coverage and merge already-flagged duplicate work evidence."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import duckdb
import numpy as np

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo
from curators_explorer.scripts.research_fixed_mass_subsamples import aggregate, fit
from curators_explorer.scripts.research_hierarchical_read_selection import (
    ASSIGNMENTS,
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BOOKS = Path(__file__).resolve().parents[2] / "data/ucsd_goodreads/parquet/books.parquet"
BOUNDARY = DATA_DIR / "hierarchical_candidate_boundary.json"
OUT_JSON = DATA_DIR / "edition_language_fragmentation.json"
OUT_REPORT = DATA_DIR / "EDITION_LANGUAGE_FRAGMENTATION_REPORT.md"


def build_merged_events():
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute(
        f"CREATE TEMP TABLE assignments AS SELECT * FROM read_parquet('{ASSIGNMENTS}') WHERE jury_q>0"
    )
    con.execute(
        f"""
        CREATE TEMP TABLE user_balance AS
        SELECT o.user_id,
               count(*) FILTER (WHERE o.rating=5)::DOUBLE AS n_high,
               count(*) FILTER (WHERE o.rating BETWEEN 1 AND 3)::DOUBLE AS n_low,
               least(count(*) FILTER (WHERE o.rating=5),
                     count(*) FILTER (WHERE o.rating BETWEEN 1 AND 3), 12)::DOUBLE AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN assignments a USING (user_id)
        JOIN ex.work_stats s USING (work_id)
        WHERE o.rating>0 AND s.n BETWEEN 100 AND {MAX_CATALOG_N}
        GROUP BY o.user_id
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE eligible AS
        SELECT s.work_id, s.n AS catalog_n, ws.title, ws.author
        FROM ex.work_stats s JOIN ex.work_scores ws USING (work_id)
        LEFT JOIN ex.work_flags f USING (work_id)
        WHERE s.n BETWEEN 100 AND {MAX_CATALOG_N}
          AND NOT coalesce(f.is_excluded,FALSE)
          AND NOT coalesce(f.is_nonfiction,FALSE)
          AND NOT coalesce(f.is_comic,FALSE)
          AND NOT coalesce(f.is_picture_book,FALSE)
          AND NOT coalesce(f.is_derivative,FALSE)
          AND NOT coalesce(f.is_duplicate,FALSE)
          AND NOT coalesce(f.is_collection,FALSE)
        """
    )
    # Only use duplicate links that already exist in work_flags. This audit does not infer
    # new cross-language equivalences. If a user has both records, prefer a rated record and
    # then the canonical record, preventing the duplicate from counting twice.
    con.execute(
        """
        CREATE TEMP TABLE source_map AS
        SELECT f.work_id AS source_work_id,
               CASE WHEN f.is_duplicate AND f.canonical_work_id IS NOT NULL
                    THEN f.canonical_work_id ELSE f.work_id END AS target_work_id,
               f.is_duplicate
        FROM ex.work_flags f
        JOIN eligible e ON e.work_id = CASE
            WHEN f.is_duplicate AND f.canonical_work_id IS NOT NULL
            THEN f.canonical_work_id ELSE f.work_id END
        """
    )
    labels = ", ".join(f"a.{label}" for label,_k in PARTITIONS)
    con.execute(
        f"""
        CREATE TEMP TABLE mapped_raw AS
        SELECT m.target_work_id AS work_id, m.source_work_id, o.user_id,
               o.rating, o.is_read, o.edition_interactions, a.jury_q, {labels},
               b.n_high, b.n_low, b.n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN source_map m ON m.source_work_id=o.work_id
        JOIN assignments a USING (user_id)
        JOIN user_balance b USING (user_id)
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE chosen_state AS
        SELECT * EXCLUDE(choice_rank) FROM (
            SELECT *, row_number() OVER (
                PARTITION BY work_id,user_id
                ORDER BY (rating>0) DESC, (source_work_id=work_id) DESC,
                         is_read DESC, edition_interactions DESC, source_work_id
            ) AS choice_rank
            FROM mapped_raw
        ) WHERE choice_rank=1
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE work_mass AS
        SELECT work_id,
               sum(jury_q * CASE WHEN rating=5 AND n_high>0 THEN n_side/n_high
                   WHEN rating BETWEEN 1 AND 3 AND n_low>0 THEN n_side/n_low
                   ELSE 0 END) AS pair_mass
        FROM chosen_state GROUP BY work_id
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE candidates AS
        SELECT (row_number() OVER (ORDER BY e.work_id)-1)::INTEGER AS work_idx,
               e.*, m.pair_mass
        FROM eligible e JOIN work_mass m USING (work_id)
        WHERE m.pair_mass>=2
        """
    )
    rows = con.execute(
        "SELECT work_idx,work_id,title,author,catalog_n,pair_mass FROM candidates ORDER BY work_idx"
    ).fetchall()
    works = [
        {
            "work_idx": int(row[0]), "work_id": str(row[1]),
            "title": row[2], "author": row[3], "catalog_n": int(row[4]),
            "merged_sql_mass": float(row[5]),
        }
        for row in rows
    ]
    event = con.execute(
        f"""
        SELECT c.work_idx, s.rating,
               s.jury_q * CASE WHEN s.rating=5 AND s.n_high>0 THEN s.n_side/s.n_high
                   WHEN s.rating BETWEEN 1 AND 3 AND s.n_low>0 THEN s.n_side/s.n_low
                   ELSE 0 END AS value,
               {', '.join(f's.{label}' for label,_k in PARTITIONS)}
        FROM chosen_state s JOIN candidates c USING (work_id)
        WHERE s.rating=5 OR s.rating BETWEEN 1 AND 3
        """
    ).fetchnumpy()
    arrays = {
        "work_idx": event["work_idx"].astype(np.int32),
        "rating": event["rating"].astype(np.int8),
        "value": event["value"].astype(np.float64),
    }
    for label,_k in PARTITIONS:
        arrays[label] = event[label].astype(np.int16)

    duplicate_rows = con.execute(
        """
        WITH source_stats AS (
            SELECT m.target_work_id AS work_id,
                   count(*) FILTER (WHERE m.source_work_id!=m.target_work_id) AS duplicate_works,
                   coalesce(sum(s.n) FILTER (WHERE m.source_work_id!=m.target_work_id),0) AS duplicate_n
            FROM source_map m LEFT JOIN ex.work_stats s ON s.work_id=m.source_work_id
            GROUP BY m.target_work_id
        ), chosen_stats AS (
            SELECT work_id,
                   count(*) FILTER (WHERE source_work_id!=work_id
                                      AND (rating=5 OR rating BETWEEN 1 AND 3)) AS borrowed,
                   count(*) FILTER (WHERE source_work_id=work_id
                                      AND (rating=5 OR rating BETWEEN 1 AND 3)) AS canonical
            FROM chosen_state GROUP BY work_id
        )
        SELECT c.work_id, coalesce(ss.duplicate_works,0), coalesce(ss.duplicate_n,0),
               coalesce(cs.borrowed,0), coalesce(cs.canonical,0)
        FROM candidates c
        LEFT JOIN source_stats ss USING (work_id)
        LEFT JOIN chosen_stats cs USING (work_id)
        """
    ).fetchall()
    duplicate = {
        str(row[0]): {
            "duplicate_works": int(row[1]), "duplicate_catalog_ratings": int(row[2]),
            "borrowed_pair_users": int(row[3]), "canonical_pair_users": int(row[4]),
        }
        for row in duplicate_rows
    }

    con.execute("CREATE TEMP TABLE candidate_ids AS SELECT work_id FROM candidates")
    language_rows = con.execute(
        f"""
        SELECT b.work_id,
               CASE WHEN lower(coalesce(b.language_code,''))='en'
                          OR lower(coalesce(b.language_code,''))='eng'
                          OR lower(coalesce(b.language_code,'')) LIKE 'en-%'
                    THEN 'eng' ELSE lower(coalesce(b.language_code,'')) END AS language_code,
               count(*) AS editions, sum(coalesce(b.ratings_count,0)) AS metadata_ratings
        FROM read_parquet('{BOOKS}') b JOIN candidate_ids c USING (work_id)
        GROUP BY b.work_id, language_code
        """
    ).fetchall()
    con.close()
    language = defaultdict(list)
    for work_id,code,editions,ratings in language_rows:
        language[str(work_id)].append(
            {"language_code": code or None, "editions": int(editions),
             "metadata_ratings": int(ratings)}
        )
    return works, arrays, duplicate, language


def language_summary(groups):
    editions = sum(row["editions"] for row in groups)
    known = [row for row in groups if row["language_code"]]
    known_ratings = sum(row["metadata_ratings"] for row in known)
    english_ratings = sum(
        row["metadata_ratings"] for row in known
        if row["language_code"] == "eng"
    )
    dominant = max((row["metadata_ratings"] for row in known), default=0)
    return {
        "editions": editions,
        "known_language_editions": sum(row["editions"] for row in known),
        "languages": len(known),
        "metadata_ratings_known_language": known_ratings,
        "english_metadata_rating_share": None if known_ratings==0 else english_ratings/known_ratings,
        "dominant_language_rating_share": None if known_ratings==0 else dominant/known_ratings,
        "language_detail": sorted(groups,key=lambda row:-row["metadata_ratings"]),
    }


def main():
    t0 = time.time()
    baseline = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    baseline_rows = baseline["expanded_books"]
    baseline_by_id = {row["work_id"]:row for row in baseline_rows}
    baseline10 = sorted(
        (row for row in baseline_rows if row["expanded_rank_mass10"] is not None),
        key=lambda row:row["expanded_rank_mass10"],
    )
    baseline_ids = [row["work_id"] for row in baseline10]

    works, arrays, duplicate, language_groups = build_merged_events()
    metric = fit(aggregate(arrays,np.ones(len(arrays["value"])),len(works)))
    publishable = metric["pair_mass"]>=10
    order = np.flatnonzero(publishable)
    order = order[np.argsort(-metric["score"][order],kind="stable")]
    merged_ids = [works[i]["work_id"] for i in order]
    merged_rank = {work_id:rank+1 for rank,work_id in enumerate(merged_ids)}
    work_idx = {row["work_id"]:i for i,row in enumerate(works)}
    rows = []
    for i in order:
        work = works[i]
        work_id = work["work_id"]
        base = baseline_by_id.get(work_id)
        rows.append(
            {
                "merged_rank": merged_rank[work_id], "work_id":work_id,
                "title":work["title"], "author":work["author"],
                "baseline_rank": None if base is None else base["expanded_rank_mass10"],
                "baseline_pair_mass": None if base is None else base["pair_mass"],
                "merged_pair_mass": float(metric["pair_mass"][i]),
                "merged_score": float(100*metric["score"][i]),
                **duplicate.get(work_id,{}),
                **language_summary(language_groups.get(work_id,[])),
            }
        )
    merged_by_id = {row["work_id"]:row for row in rows}
    top200 = rows[:200]
    top200_ids = {row["work_id"] for row in top200}
    baseline_top200 = set(baseline_ids[:200])
    changed = [
        row for row in rows
        if row["duplicate_works"]>0 and row["baseline_rank"] is not None
    ]
    top_language = [row for row in top200 if row["known_language_editions"]>0]
    result = {
        "meta": {
            "purpose":"edition/language coverage and flagged-duplicate evidence merge",
            "runtime_seconds":time.time()-t0,
            "baseline_candidates":len(baseline_rows),
            "merged_candidates":len(works),
            "baseline_publishable":len(baseline10),
            "merged_publishable":len(rows),
            "merge_rule":"prefer rated record, then canonical record; at most one user vote per canonical work",
            "language_note":"language shares use edition metadata ratings, not the research jury",
        },
        "comparison": {
            "jaccard50":jaccard(baseline_ids,merged_ids,50),
            "jaccard200":jaccard(baseline_ids,merged_ids,200),
            "rbo":rbo(baseline_ids,merged_ids),
            "new_top200":[row for row in top200 if row["work_id"] not in baseline_top200],
            "exited_top200":[
                {**baseline_by_id[work_id],
                 "merged_rank":merged_rank.get(work_id)}
                for work_id in baseline_top200-top200_ids
            ],
        },
        "duplicate_summary": {
            "publishable_with_flagged_duplicates":len(changed),
            "top200_with_flagged_duplicates":sum(row["duplicate_works"]>0 for row in top200),
            "top200_borrowed_pair_users":sum(row["borrowed_pair_users"] for row in top200),
            "largest_publishable_mass_changes":sorted(
                changed,
                key=lambda row:row["merged_pair_mass"]-(row["baseline_pair_mass"] or 0),
                reverse=True,
            )[:40],
        },
        "language_summary": {
            "top200_median_editions":float(np.median([row["editions"] for row in top200])),
            "top200_with_multiple_known_languages":sum(row["languages"]>1 for row in top200),
            "top200_median_known_languages":float(np.median([row["languages"] for row in top200])),
            "top200_median_english_share":float(np.median([
                row["english_metadata_rating_share"] for row in top_language
                if row["english_metadata_rating_share"] is not None
            ])),
            "top200_low_english_share":[
                row for row in top200
                if row["english_metadata_rating_share"] is not None
                and row["english_metadata_rating_share"]<.25
            ],
        },
        "merged_top200":top200,
    }
    OUT_JSON.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines = [
        "# Edition and language-fragmentation audit", "", "## Result", "",
        "Goodreads already joins most editions and translations under a shared work ID. "
        "This audit additionally merges only the duplicate-work links already present in "
        "the local catalog flags, keeping at most one vote per user and preferring their "
        "canonical record when both are rated.", "",
        f"- Expanded candidates: baseline **{len(baseline_rows):,}**, duplicate-merged "
        f"**{len(works):,}**; publishable mass-10 books: **{len(baseline10):,} / {len(rows):,}**.",
        f"- Ranking similarity after the merge: J@50 **{result['comparison']['jaccard50']:.3f}**, "
        f"J@200 **{result['comparison']['jaccard200']:.3f}**, RBO **{result['comparison']['rbo']:.3f}**.",
        f"- Publishable books with flagged duplicate evidence: **{len(changed)}**; within "
        f"the merged top 200: **{result['duplicate_summary']['top200_with_flagged_duplicates']}**.",
        f"- The top 200 has a median **{result['language_summary']['top200_median_editions']:.0f}** "
        f"editions; **{result['language_summary']['top200_with_multiple_known_languages']}** "
        "have editions recorded in more than one known language.", "",
        "## Largest duplicate-evidence changes", "",
        "| merged # | book | old # | old mass | merged mass | borrowed pair users | duplicate works |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["duplicate_summary"]["largest_publishable_mass_changes"][:30]:
        old_rank = "—" if row["baseline_rank"] is None else row["baseline_rank"]
        lines.append(
            f"| {row['merged_rank']} | {row['title']} — {row['author']} | {old_rank} | "
            f"{row['baseline_pair_mass']:.1f} | {row['merged_pair_mass']:.1f} | "
            f"{row['borrowed_pair_users']} | {row['duplicate_works']} |"
        )
    lines += [
        "", "## Low-English-share books in the merged top 200", "",
        "Metadata language is missing for many editions and is not reader nationality; this "
        "table is a fragmentation diagnostic, not a cultural-quality measure.", "",
        "| # | book | editions | known languages | English metadata-rating share | dominant-language share |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in result["language_summary"]["top200_low_english_share"][:50]:
        lines.append(
            f"| {row['merged_rank']} | {row['title']} — {row['author']} | {row['editions']} | "
            f"{row['languages']} | {100*row['english_metadata_rating_share']:.0f}% | "
            f"{100*row['dominant_language_rating_share']:.0f}% |"
        )
    lines += [
        "", "This resolves only known duplicate links. Separate work IDs with translated "
        "titles cannot be safely merged from title text alone; external identifiers or manual "
        "review would be required before changing the point model.", "",
    ]
    OUT_REPORT.write_text("\n".join(lines),encoding="utf-8")
    print(f"Wrote {OUT_REPORT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

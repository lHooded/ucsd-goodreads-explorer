#!/usr/bin/env python3
"""Catalog hygiene: collections, derivatives, comics, nonfiction, near-duplicates.

Builds ``work_flags`` on the explorer DuckDB from title heuristics, Goodreads
shelf counts, and optional curated overrides in ``data/catalog_overrides.json``.

Publication years live in ``ucsd_explorer.work_years`` (separate module).

Run:
  .venv/bin/python -m ucsd_explorer.catalog_flags
  .venv/bin/python -m ucsd_explorer.catalog_flags --years-only
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from ucsd_explorer.db import DERIVED, EXPLORER_DB, META_PATH, OVERRIDES_PATH, PARQUET
from ucsd_explorer.work_years import (
    apply_original_year_overrides,
    build_work_years_table,
    materialize_work_years,
)

# Soft score multipliers when a flag is present (lowest wins; overrides can go lower).
WEIGHT_COLLECTION = 0.18
WEIGHT_DERIVATIVE = 0.12
WEIGHT_COMIC = 0.18
WEIGHT_BOTH = 0.08

COLLECTION_TITLE_RE = re.compile(
    r"(?i)"
    r"\bcomplete\s+works\b"
    r"|\bcollected\s+(stories|fictions|fiction|poems|poetry|plays|works|essays|short\s+stories)\b"
    r"|\bomnibus\b"
    r"|\banthology\b"
    r"|\banthologies\b"
    r"|\briverside\s+shakespeare\b"
    r"|\bcomplete\s+calvin\b"
    r"|\bboxed\s+set\b"
    r"|\bbox\s+set\b"
    r"|\bboxset\b"
    r"|\bcomplete\s+collection\b"
    r"|\bshort\s+stories\s+of\b"
    r"|\bthe\s+complete\s+[a-z]"
    r"|\bvolumes?\s+\d+\s*[-–—]\s*\d+"
    r"|\b(?:vol\.?|volume)\s*\d+\s*[-–—]\s*(?:vol\.?|volume)?\s*\d+"
    # Multi-volume ranges in the title (omnibus), not a single "#1"
    r"|[#]\s*\d+\s*[-–—]\s*\d+"
    r"|\bcollection\s*\([^)]*[#]\s*\d"
    r"|\b(?:complete|entire)\s+series\b"
    # Omnibus of a series — NOT bare "Trilogy #1" (that is a single volume)
    r"|\b(?:trilogy|quartet|pentalogy|tetralogy|hexalogy)\s+(?:omnibus|boxed|box\s*set|collection|set)\b"
    r"|\b(?:omnibus|boxed|box\s*set|collection)\b.{0,40}\b(?:trilogy|quartet|pentalogy)\b"
    r"|\b(?:books?|novels?)\s+\d+\s*[-–—]\s*\d+"
    r"|\ba\s+[\w'&.\s]{0,50}\bcollection\b"
    r"|\band\s+other\s+(stories|tales|writings|poems|essays)\b"
    r"|\bother\s+(stories|tales|writings)\b"
    # Explicit multi-novel packaging (Wind/Pinball: Two Novels)
    r"|\b(?:two|three|four|five)\s+novels?\b"
    r"|\b(?:two|three|four)\s+novellas?\b"
)

# Single installment of a numbered series — not an omnibus by itself.
SINGLE_VOLUME_SERIES_RE = re.compile(
    r"(?i)"
    r"[,:(]\s*[#]\s*\d+(?:\.\d+)?\s*\)?\s*$"  # ", #1)" / "(#2)" at end
    r"|[#]\s*\d+(?:\.\d+)?\s*\)\s*$"
    r"|\bpart\s+(?:one|two|three|\d+)\b"
)

# Title cues that support short-story / essay collection even without "omnibus".
COLLECTION_CUE_RE = re.compile(
    r"(?i)"
    r"\bshort\s+stories\b"
    r"|\bstories\b"
    r"|\btales\b"
    r"|\bfables\b"
    r"|\bpoems\b"
    r"|\bessays\b"
    r"|\bwritings\b"
    r"|\bnovellas\b"
    r"|\bchronicles\b"
)

DERIVATIVE_TITLE_RE = re.compile(
    r"(?i)"
    r"\bscreenplay\b"
    r"|\bfilm\s+diary\b"
    r"|\bmonarch\s+notes\b"
    r"|\bcliff'?s?\s+notes\b"
    r"|\bsparknotes\b"
    r"|\bstudy\s+guide\b"
    r"|\bcompanion\s+to\b"
    r"|\b(?:movie|film)\s+companion\b"
    r"|\billustrated\s+(?:movie\s+)?companion\b"
    r"|\bannotated\s+bibliography\b"
    r"|\b10th\s+anniversary\s+exhibit\b"
    r"|\banniversary\s+exhibit\b"
    # Movie/game art books — not "The Art of Fielding" / "Art of War"
    r"|\bthe\s+art\s+of\b.{0,60}\b(?:movie|film|cinema|animation|pixar|disney|fellowship|two\s+towers|return\s+of\s+the\s+king|star\s+wars|harry\s+potter|game\s+of\s+thrones|incredibles)\b"
    r"|\bart\s+of\s+the\s+(?:fellowship|two\s+towers|return|hobbit|incredibles)\b"
    r"|\b(?:the\s+)?making\s+of\s+the\s+(?:movie|film|picture)\b"
    r"|\b(?:the\s+)?making\s+of\b.{0,40}\b(?:movie|film)\s+trilogy\b"
    r"|\bbehind\s+the\s+scenes\s+of\b"
    r"|\breader'?s?\s+companion\b"
    r"|\billustrated\s+history\b"
    # Musical scores / sheet music editions of picture books etc.
    r"|\bfor\s+soprano\b"
    r"|\bfor\s+piano\b"
    r"|\band\s+orchestra\b"
    r"|\bsheet\s+music\b"
    r"|\bpiano\s+vocal\b"
    r"|\bvocal\s+score\b"
)

PICTURE_SHELVES = (
    "picture-books",
    "picture-book",
    "board-books",
    "board-book",
    "childrens-picture-books",
)
FICTION_SHELVES = (
    "fiction",
    "novels",
    "novel",
    "literary-fiction",
    "literature",
    "classic-fiction",
    "adult-fiction",
    "general-fiction",
    "contemporary-fiction",
)
NONFICTION_SHELVES = (
    "non-fiction",
    "nonfiction",
    "non_fiction",
    "reference",
    "biography",
    "memoir",
    "history",
    "science",
    "self-help",
    "selfhelp",
    "art",
    "photography",
    "essay",
    "essays",
    "criticism",
    "literary-criticism",
)
COLLECTION_SHELVES = (
    "short-stories",
    "short-story",
    "anthologies",
    "anthology",
    "collections",
    "collection",
    "omnibus",
    "box-set",
    "boxed-set",
)
COMIC_SHELVES = (
    "graphic-novels",
    "graphic-novel",
    "graphicnovels",
    "graphicnovel",
    "comics",
    "comic",
    "comic-books",
    "comic-book",
    "comics-graphic-novels",
    "graphic-novels-comics",
    "comics-and-graphic-novels",
    "graphic-novels-and-comics",
    "comic-graphic-novel",
    "graphic-novel-comic",
    "manga",
    "mangas",
    "comics-manga",
    "manga-comics",
    "comics-and-manga",
    "manga-and-comics",
    "manga-manhwa",
    "manhwa",
    "webtoon",
    "webtoons",
    "bd",
    "bande-dessinee",
    "dc-comics",
    "marvel-comics",
    "graphic-novels-manga",
    "manga-graphic-novels",
    "read-manga",
    "read-comics",
)
COMIC_TITLE_RE = re.compile(
    r"(?i)"
    r"\bgraphic\s+novels?\b"
    r"|\bmanga\b"
    r"|\bmanhwa\b"
    r"|\bwebtoon\b"
    r"|\bbande\s+dessin"
)


def load_overrides() -> dict[str, Any]:
    if not OVERRIDES_PATH.exists():
        return {}
    return json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))


def normalize_title(title: str) -> str:
    """Cluster key: lowercase, strip punctuation / articles / trailing #N."""
    if not title:
        return ""
    t = unicodedata.normalize("NFKC", title).lower().strip()
    t = t.replace("&", " and ")
    t = re.sub(r"\s*#\s*\d+\s*$", "", t)
    t = re.sub(r"\s*\(\s*\d+\s*\)\s*$", "", t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^(the|a|an)\s+", "", t)
    return t


def _core_title_norm(title: str) -> str:
    """Normalize with parenthetical series suffixes removed."""
    return normalize_title(re.sub(r"\([^)]*\)", " ", title or ""))


def _split_slash_parts(title: str) -> list[str]:
    """Split dual/multi-work titles on slashes; empty if not a slash combo."""
    raw = title or ""
    if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", raw):
        return []
    if re.search(r"(?i)\bpiano\s*/\s*vocal|\bvocal\s*/\s*guitar", raw):
        return []
    # Ignore slashes that only appear inside (...) series aliases
    outside = re.sub(r"\([^)]*\)", " ", raw)
    outside = re.sub(r"\s+", " ", outside).strip()
    if " / " in outside:
        parts = [p.strip() for p in re.split(r"\s*/\s*", outside) if p.strip()]
    elif re.search(r"[A-Za-z]/[A-Za-z]", outside):
        parts = [p.strip() for p in outside.split("/") if p.strip()]
    else:
        return []
    parts = [p for p in parts if len(p) >= 3 and not re.fullmatch(r"\d+([./]\d+)*", p)]
    return parts if len(parts) >= 2 else []


def _non_latin_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ord(c) > 127) / len(letters)


def _part_norms(part: str) -> list[str]:
    """Candidate norms for a slash component (full text + after-colon subtitle)."""
    out: list[str] = []
    for candidate in (part,):
        n = normalize_title(candidate)
        if n and n not in out:
            out.append(n)
    if ":" in (part or ""):
        after = part.split(":", 1)[1].strip()
        if after and len(after) >= 3:
            n = normalize_title(after)
            if n and n not in out:
                out.append(n)
    return out


def _component_matches(part_norm: str, work_title: str) -> bool:
    """True if work_title is the same work as slash component (not a shorter prefix)."""
    wn = _core_title_norm(work_title)
    if not part_norm or not wn:
        return False
    if wn == part_norm:
        return True
    # Prefix match only for longer components — short stems ("wind", "lost world"
    # adjacent titles) create huge false positives.
    if len(part_norm) < 12:
        return False
    if wn.startswith(part_norm + " ") or wn.startswith(part_norm + ":"):
        return True
    return False


def _title_flags(title: str) -> tuple[bool, bool, bool]:
    return (
        bool(COLLECTION_TITLE_RE.search(title or "")),
        bool(DERIVATIVE_TITLE_RE.search(title or "")),
        bool(COMIC_TITLE_RE.search(title or "")),
    )


def _shelf_comic(comic_n: int, fiction_n: int) -> bool:
    """Shelf-primary comics/manga/GN — same shape as nonfiction gate."""
    return comic_n >= 10 and comic_n > fiction_n * 1.15


def _shelf_collection(title: str, collection_n: int, fiction_n: int) -> bool:
    """Shelf-based collection signal, gated to avoid single-volume false positives."""
    if collection_n < 40:
        return False
    if collection_n < max(fiction_n, 1) * 0.5:
        return False
    # Numbered single installment of a series → not an omnibus
    if SINGLE_VOLUME_SERIES_RE.search(title or "") and not re.search(
        r"(?i)[#]\s*\d+\s*[-–—]\s*\d+", title or ""
    ):
        return False
    # Prefer a title cue ("stories", "tales", …) unless shelves are overwhelmingly collection
    if COLLECTION_CUE_RE.search(title or "") or COLLECTION_TITLE_RE.search(title or ""):
        return True
    return collection_n >= 120 and collection_n >= max(fiction_n, 1) * 0.9




def _pass_shelf_and_meta(con, shelves_pq: Path, books_pq: Path) -> list[tuple]:
    """Build shelf aggregates + per-work meta; return work meta rows."""
    print("Catalog flags: shelf aggregates…", flush=True)
    fiction_list = ", ".join(f"'{s}'" for s in FICTION_SHELVES)
    nonfiction_list = ", ".join(f"'{s}'" for s in NONFICTION_SHELVES)
    collection_list = ", ".join(f"'{s}'" for s in COLLECTION_SHELVES)
    comic_list = ", ".join(f"'{s}'" for s in COMIC_SHELVES)
    picture_list = ", ".join(f"'{s}'" for s in PICTURE_SHELVES)

    con.execute("DROP TABLE IF EXISTS work_flags")
    con.execute("DROP TABLE IF EXISTS _shelf_work_agg")
    con.execute(
        f"""
        CREATE TEMP TABLE _shelf_work_agg AS
        SELECT
            btw.work_id,
            sum(CASE WHEN lower(s.shelf) IN ({fiction_list})
                     THEN s.count ELSE 0 END)::BIGINT AS fiction_n,
            sum(CASE WHEN lower(s.shelf) IN ({nonfiction_list})
                     THEN s.count ELSE 0 END)::BIGINT AS nonfiction_n,
            sum(CASE WHEN lower(s.shelf) IN ({collection_list})
                     THEN s.count ELSE 0 END)::BIGINT AS collection_n,
            sum(CASE WHEN lower(s.shelf) IN ({comic_list})
                     THEN s.count ELSE 0 END)::BIGINT AS comic_n,
            sum(CASE WHEN lower(s.shelf) IN ({picture_list})
                     THEN s.count ELSE 0 END)::BIGINT AS picture_n
        FROM read_parquet('{shelves_pq}') s
        JOIN book_to_work btw ON s.book_id = btw.book_id
        WHERE NOT coalesce(s.is_status, FALSE)
          AND lower(s.shelf) IN ({fiction_list}, {nonfiction_list}, {collection_list},
                                 {comic_list}, {picture_list})
        GROUP BY btw.work_id
        """
    )
    print(
        f"  shelf-tagged works: {con.execute('SELECT count(*) FROM _shelf_work_agg').fetchone()[0]:,}",
        flush=True,
    )

    print("Catalog flags: book metadata…", flush=True)
    con.execute(
        f"""
        CREATE TEMP TABLE _book_meta AS
        SELECT
            book_id::VARCHAR AS book_id,
            work_id::VARCHAR AS work_id,
            author_id::VARCHAR AS author_id,
            lower(coalesce(language_code, '')) AS language_code,
            try_cast(num_pages AS INTEGER) AS num_pages
        FROM read_parquet('{books_pq}')
        WHERE work_id IS NOT NULL
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE _work_meta AS
        SELECT
            ws.work_id,
            ws.book_id,
            ws.title,
            ws.author,
            ws.n,
            coalesce(bm.author_id,
                regexp_extract(coalesce(ws.author_url, ''), 'author/show/(\\d+)', 1)
            ) AS author_id,
            coalesce(nullif(bm.language_code, ''), '') AS language_code,
            bm.num_pages,
            coalesce(sa.fiction_n, 0) AS fiction_n,
            coalesce(sa.nonfiction_n, 0) AS nonfiction_n,
            coalesce(sa.collection_n, 0) AS collection_n,
            coalesce(sa.comic_n, 0) AS comic_n,
            coalesce(sa.picture_n, 0) AS picture_n
        FROM work_scores ws
        LEFT JOIN _book_meta bm ON ws.book_id = bm.book_id
        LEFT JOIN _shelf_work_agg sa ON ws.work_id = sa.work_id
        """
    )
    rows = con.execute(
        """
        SELECT work_id, book_id, title, author, n, author_id, language_code,
               num_pages, fiction_n, nonfiction_n, collection_n, comic_n, picture_n
        FROM _work_meta
        """
    ).fetchall()
    print(f"  scoring {len(rows):,} works…", flush=True)
    return rows


def _pass_auto_flags(
    rows: list[tuple],
    *,
    exclude_ids: set[str],
) -> list[dict[str, Any]]:
    """Pass 1: per-work title/shelf automatic flags."""
    flagged: list[dict[str, Any]] = []
    for (
        work_id,
        book_id,
        title,
        author,
        n,
        author_id,
        language_code,
        num_pages,
        fiction_n,
        nonfiction_n,
        collection_n,
        comic_n,
        picture_n,
    ) in rows:
        wid = str(work_id)
        title_s = title or ""
        is_coll_title, is_deriv_title, is_comic_title = _title_flags(title_s)
        is_coll_shelf = _shelf_collection(
            title_s, int(collection_n or 0), int(fiction_n or 0)
        )
        is_collection = is_coll_title or is_coll_shelf
        is_derivative = is_deriv_title
        if is_derivative and SINGLE_VOLUME_SERIES_RE.search(title_s):
            if not re.search(
                r"(?i)\b(?:screenplay|study\s+guide|monarch\s+notes|cliff'?s?\s+notes|"
                r"sparknotes|movie\s+companion|film\s+companion|illustrated\s+companion|"
                r"for\s+soprano|for\s+piano|sheet\s+music|vocal\s+score)\b",
                title_s,
            ):
                is_derivative = False
        is_nonfiction = bool(nonfiction_n >= 10 and nonfiction_n > fiction_n * 1.15)
        is_comic = is_comic_title or _shelf_comic(int(comic_n or 0), int(fiction_n or 0))
        pages = int(num_pages) if num_pages is not None else None
        pic_n = int(picture_n or 0)
        # Picture books: strong picture-* shelves, or short + children's picture signal
        is_picture_book = pic_n >= 40 and (
            pic_n >= max(int(fiction_n or 0), 1) * 0.25
            or (pages is not None and pages <= 64 and pic_n >= 20)
        )
        flagged.append(
            {
                "work_id": wid,
                "book_id": str(book_id),
                "title": title_s,
                "author": author,
                "n": int(n or 0),
                "author_id": str(author_id or "") or None,
                "language_code": language_code or "",
                "title_norm": normalize_title(title_s),
                "is_collection": is_collection,
                "is_derivative": is_derivative,
                "is_nonfiction": is_nonfiction,
                "is_comic": is_comic,
                "is_picture_book": is_picture_book,
                "is_excluded": wid in exclude_ids,
                "inherit_year": None,
            }
        )
    return flagged


def _pass_slash_omnibus(
    flagged: list[dict[str, Any]],
    year_by_work: dict[str, int],
) -> int:
    """Pass 1b: slash omnibuses confirmed by ≥2 sibling component matches."""
    print("  slash-omnibus component match…", flush=True)
    by_author: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in flagged:
        aid = row["author_id"] or f"name:{normalize_title(row['author'] or '')}"
        by_author[aid].append(row)

    slash_hits = 0
    for works in by_author.values():
        for row in works:
            parts = _split_slash_parts(row["title"])
            if len(parts) < 2:
                continue
            if any(_non_latin_ratio(p) > 0.4 for p in parts):
                continue
            others = [
                x
                for x in works
                if x["work_id"] != row["work_id"] and not _split_slash_parts(x["title"])
            ]
            matches: list[dict[str, Any] | None] = []
            for part in parts:
                pnorms = _part_norms(part)
                best = None
                best_exact = False
                for o in others:
                    hit_norm = next(
                        (pn for pn in pnorms if _component_matches(pn, o["title"])),
                        None,
                    )
                    if hit_norm is None:
                        continue
                    exact = _core_title_norm(o["title"]) == hit_norm
                    if best is None or (exact and not best_exact) or (
                        exact == best_exact and o["n"] > best["n"]
                    ):
                        best = o
                        best_exact = exact
                matches.append(best)
            matched_ids = {m["work_id"] for m in matches if m}
            if len(matched_ids) < 2:
                continue
            row["is_collection"] = True
            years = [
                year_by_work[m["work_id"]]
                for m in matches
                if m and m["work_id"] in year_by_work
            ]
            if years:
                row["inherit_year"] = min(years)
            slash_hits += 1
    print(f"  slash omnibuses confirmed: {slash_hits:,}", flush=True)
    return slash_hits


def _pass_overrides_and_weights(
    flagged: list[dict[str, Any]],
    *,
    force_flags: dict[str, list[str]],
    never_collection: set[str],
    never_comic: set[str],
    deweight_map: dict[str, float],
    original_years: dict[str, int],
) -> dict[str, int]:
    """Pass 1c: curated overrides + format weights. Returns inherit_years map."""
    inherit_years: dict[str, int] = {}
    for row in flagged:
        wid = row["work_id"]
        forced = set(force_flags.get(wid) or [])
        if wid in never_collection:
            row["is_collection"] = False
            row["inherit_year"] = None
        if wid in never_comic:
            row["is_comic"] = False
        if "collection" in forced:
            row["is_collection"] = True
        if "derivative" in forced:
            row["is_derivative"] = True
        if "nonfiction" in forced:
            row["is_nonfiction"] = True
        if "fiction" in forced:
            row["is_nonfiction"] = False
        if "comic" in forced:
            row["is_comic"] = True

        weights = [1.0]
        if row["is_collection"] and row["is_derivative"]:
            weights.append(WEIGHT_BOTH)
        elif row["is_collection"]:
            weights.append(WEIGHT_COLLECTION)
        elif row["is_derivative"]:
            weights.append(WEIGHT_DERIVATIVE)
        if row["is_comic"]:
            weights.append(WEIGHT_COMIC)
        fmt = min(weights)
        if wid in deweight_map:
            fmt = min(fmt, deweight_map[wid])
        row["format_weight"] = float(fmt)

        flag_bits = []
        if row["is_collection"]:
            flag_bits.append("collection")
        if row["is_derivative"]:
            flag_bits.append("derivative")
        if row["is_nonfiction"]:
            flag_bits.append("nonfiction")
        if row["is_comic"]:
            flag_bits.append("comic")
        if row.get("is_picture_book"):
            flag_bits.append("picture_book")
        if row["is_excluded"]:
            flag_bits.append("excluded")
        row["flags"] = ",".join(flag_bits)

        if row.get("inherit_year"):
            inherit_years[wid] = int(row["inherit_year"])
        if wid in original_years:
            inherit_years[wid] = int(original_years[wid])
    return inherit_years


def _pass_duplicate_clusters(
    flagged: list[dict[str, Any]],
    canonical_map: dict[str, str],
) -> list[tuple]:
    """Pass 2: near-duplicate clusters → CSV-ready out_rows."""
    print("  flagged; clustering duplicates…", flush=True)
    clusters: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in flagged:
        aid = row["author_id"] or f"name:{normalize_title(row['author'] or '')}"
        lang = (row["language_code"] or "")[:2]
        key = (aid, row["title_norm"], lang)
        if row["title_norm"]:
            clusters[key].append(row)

    dup_of: dict[str, str] = {}
    for members in clusters.values():
        if len(members) < 2:
            continue
        coll_vals = {bool(m["is_collection"]) for m in members}
        if len(coll_vals) > 1:
            continue
        members_sorted = sorted(members, key=lambda m: (-m["n"], m["work_id"]))
        canon = members_sorted[0]["work_id"]
        for m in members_sorted[1:]:
            dup_of[m["work_id"]] = canon

    for src, dst in canonical_map.items():
        dup_of[src] = dst

    canon_book = {r["work_id"]: r["book_id"] for r in flagged}
    canon_title = {r["work_id"]: r["title"] for r in flagged}

    out_rows = []
    for row in flagged:
        wid = row["work_id"]
        canon = dup_of.get(wid)
        is_dup = canon is not None and canon != wid
        flags = row["flags"]
        if is_dup:
            flags = (flags + ",duplicate") if flags else "duplicate"
        out_rows.append(
            (
                wid,
                row["book_id"],
                row["author_id"],
                row["language_code"],
                row["title_norm"],
                row["is_collection"],
                row["is_derivative"],
                row["is_nonfiction"],
                row["is_comic"],
                row.get("is_picture_book", False),
                row["is_excluded"],
                is_dup,
                canon if is_dup else None,
                canon_book.get(canon) if is_dup else None,
                canon_title.get(canon) if is_dup else None,
                row["format_weight"],
                flags,
            )
        )
    return out_rows


def _write_work_flags_table(con, out_rows: list[tuple]) -> None:
    print(f"  writing {len(out_rows):,} flag rows…", flush=True)
    tmp_csv = DERIVED / "_work_flags_tmp.csv"
    DERIVED.mkdir(parents=True, exist_ok=True)
    with tmp_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "work_id",
                "book_id",
                "author_id",
                "language_code",
                "title_norm",
                "is_collection",
                "is_derivative",
                "is_nonfiction",
                "is_comic",
                "is_picture_book",
                "is_excluded",
                "is_duplicate",
                "canonical_work_id",
                "canonical_book_id",
                "canonical_title",
                "format_weight",
                "flags",
            ]
        )
        w.writerows(out_rows)

    con.execute("DROP TABLE IF EXISTS work_flags")
    con.execute(
        f"""
        CREATE TABLE work_flags AS
        SELECT
            work_id::VARCHAR AS work_id,
            book_id::VARCHAR AS book_id,
            nullif(author_id, '')::VARCHAR AS author_id,
            language_code::VARCHAR AS language_code,
            title_norm::VARCHAR AS title_norm,
            lower(is_collection) IN ('true', '1', 't') AS is_collection,
            lower(is_derivative) IN ('true', '1', 't') AS is_derivative,
            lower(is_nonfiction) IN ('true', '1', 't') AS is_nonfiction,
            lower(is_comic) IN ('true', '1', 't') AS is_comic,
            lower(is_picture_book) IN ('true', '1', 't') AS is_picture_book,
            lower(is_excluded) IN ('true', '1', 't') AS is_excluded,
            lower(is_duplicate) IN ('true', '1', 't') AS is_duplicate,
            nullif(canonical_work_id, '')::VARCHAR AS canonical_work_id,
            nullif(canonical_book_id, '')::VARCHAR AS canonical_book_id,
            nullif(canonical_title, '')::VARCHAR AS canonical_title,
            try_cast(format_weight AS DOUBLE) AS format_weight,
            flags::VARCHAR AS flags
        FROM read_csv('{tmp_csv}', header=true, all_varchar=true)
        """
    )
    try:
        tmp_csv.unlink()
    except OSError:
        pass
    con.execute("CREATE INDEX idx_wf_coll ON work_flags(is_collection)")
    con.execute("CREATE INDEX idx_wf_deriv ON work_flags(is_derivative)")
    con.execute("CREATE INDEX idx_wf_nf ON work_flags(is_nonfiction)")
    con.execute("CREATE INDEX idx_wf_comic ON work_flags(is_comic)")
    con.execute("CREATE INDEX idx_wf_pic ON work_flags(is_picture_book)")
    con.execute("CREATE INDEX idx_wf_dup ON work_flags(is_duplicate)")


def _apply_inherit_years(con, inherit_years: dict[str, int]) -> None:
    if not inherit_years:
        return
    print(f"  applying {len(inherit_years):,} inherited/override years…", flush=True)
    for wid, y in inherit_years.items():
        exists = con.execute(
            "SELECT 1 FROM work_years WHERE work_id = ?", [wid]
        ).fetchone()
        if exists:
            con.execute(
                "UPDATE work_years SET pub_year = ? WHERE work_id = ?", [y, wid]
            )
        else:
            con.execute("INSERT INTO work_years VALUES (?, ?)", [wid, y])


def _smoke_checks(con) -> None:
    checks = [
        ("%Complete Works%", "%Shakespeare%"),
        ("Hamlet: Screenplay%", None),
        ("Animal Farm / 1984", None),
        ("Brave New World / Brave New World Revisited", None),
        ("Dating You / Hating You", None),
        ("11/22/63", None),
        ("Collected Fictions", None),
        ("Crime and Punishment", "%Dosto%"),
        ("Watchmen", "%Moore%"),
        ("Saga, Vol. 1%", "%Vaughan%"),
        ("Coraline", "%Gaiman%"),
        ("Stoner", "%Williams%"),
    ]
    for title_pat, author_pat in checks:
        sql = """
            SELECT ws.title, ws.n, f.flags, round(f.format_weight, 2), wy.pub_year
            FROM work_scores ws
            LEFT JOIN work_flags f USING (work_id)
            LEFT JOIN work_years wy USING (work_id)
            WHERE ws.title ILIKE ?
        """
        args: list[Any] = [title_pat]
        if author_pat:
            sql += " AND ws.author ILIKE ?"
            args.append(author_pat)
        sql += " ORDER BY ws.n DESC LIMIT 1"
        print(f"  check {title_pat}: {con.execute(sql, args).fetchall()}", flush=True)


def materialize_catalog_flags(*, db_path: Path | None = None) -> dict[str, Any]:
    import duckdb

    db_path = db_path or EXPLORER_DB
    if not db_path.exists():
        raise SystemExit(f"Missing {db_path}. Run materialize_ratings first.")

    shelves_pq = PARQUET / "book_shelves.parquet"
    books_pq = PARQUET / "books.parquet"
    if not shelves_pq.exists():
        raise SystemExit(f"Missing {shelves_pq}")
    if not books_pq.exists():
        raise SystemExit(f"Missing {books_pq}")

    t0 = time.time()
    overrides = load_overrides()
    con = duckdb.connect(str(db_path))

    rows = _pass_shelf_and_meta(con, shelves_pq, books_pq)

    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "work_years" not in tables:
        build_work_years_table(con, books_pq)
        apply_original_year_overrides(con, overrides)
    year_by_work = {
        str(r[0]): int(r[1])
        for r in con.execute("SELECT work_id, pub_year FROM work_years").fetchall()
        if r[1] is not None
    }

    force_flags: dict[str, list[str]] = {
        str(k): list(v) for k, v in (overrides.get("force_flags") or {}).items()
    }
    never_collection = {str(x) for x in (overrides.get("never_collection") or [])}
    never_comic = {str(x) for x in (overrides.get("never_comic") or [])}
    deweight_map: dict[str, float] = {
        str(k): float(v) for k, v in (overrides.get("deweight_work_ids") or {}).items()
    }
    exclude_ids = {str(x) for x in (overrides.get("exclude_work_ids") or [])}
    canonical_map: dict[str, str] = {
        str(k): str(v) for k, v in (overrides.get("canonical_map") or {}).items()
    }
    original_years: dict[str, int] = {
        str(k): int(v) for k, v in (overrides.get("original_years") or {}).items()
    }

    flagged = _pass_auto_flags(rows, exclude_ids=exclude_ids)
    slash_hits = _pass_slash_omnibus(flagged, year_by_work)
    inherit_years = _pass_overrides_and_weights(
        flagged,
        force_flags=force_flags,
        never_collection=never_collection,
        never_comic=never_comic,
        deweight_map=deweight_map,
        original_years=original_years,
    )
    out_rows = _pass_duplicate_clusters(flagged, canonical_map)
    _write_work_flags_table(con, out_rows)

    stats = {
        "n_works": len(out_rows),
        "n_collection": int(
            con.execute("SELECT count(*) FROM work_flags WHERE is_collection").fetchone()[0]
        ),
        "n_derivative": int(
            con.execute("SELECT count(*) FROM work_flags WHERE is_derivative").fetchone()[0]
        ),
        "n_nonfiction": int(
            con.execute("SELECT count(*) FROM work_flags WHERE is_nonfiction").fetchone()[0]
        ),
        "n_comic": int(
            con.execute("SELECT count(*) FROM work_flags WHERE is_comic").fetchone()[0]
        ),
        "n_picture_book": int(
            con.execute(
                "SELECT count(*) FROM work_flags WHERE is_picture_book"
            ).fetchone()[0]
        ),
        "n_duplicate": int(
            con.execute("SELECT count(*) FROM work_flags WHERE is_duplicate").fetchone()[0]
        ),
        "n_excluded": int(
            con.execute("SELECT count(*) FROM work_flags WHERE is_excluded").fetchone()[0]
        ),
        "n_slash_omnibus": slash_hits,
        "n_year_overrides": len(inherit_years),
        "built_at": time.time(),
        "elapsed_s": round(time.time() - t0, 1),
    }
    print(
        f"work_flags: {stats['n_works']:,} · collections {stats['n_collection']:,} · "
        f"derivatives {stats['n_derivative']:,} · nonfiction {stats['n_nonfiction']:,} · "
        f"comics {stats['n_comic']:,} · picture {stats['n_picture_book']:,} · "
        f"duplicates {stats['n_duplicate']:,} · "
        f"slash omnibuses {slash_hits:,} in {stats['elapsed_s']}s",
        flush=True,
    )

    _apply_inherit_years(con, inherit_years)
    _smoke_checks(con)
    con.close()

    DERIVED.mkdir(parents=True, exist_ok=True)
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    else:
        meta = {}
    meta["catalog_flags"] = stats
    meta["catalog_flags_available"] = True
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return stats


def has_catalog_flags() -> bool:
    from ucsd_explorer.db import table_names

    return "work_flags" in table_names()


def parse_catalog_params(params: dict[str, Any]) -> dict[str, bool]:
    """UI defaults: fiction_only / exclude_derivatives / comics / collapse ON."""
    from ucsd_explorer.db import truthy

    def flag(key: str, default: bool) -> bool:
        if key not in params:
            return default
        return truthy(params.get(key))

    return {
        "exclude_collections": flag("exclude_collections", False),
        "exclude_comics": flag("exclude_comics", True),
        "exclude_picture_books": flag("exclude_picture_books", True),
        "fiction_only": flag("fiction_only", True),
        "exclude_derivatives": flag("exclude_derivatives", True),
        "collapse_duplicates": flag("collapse_duplicates", True),
        "apply_format_weight": flag("apply_format_weight", True),
    }


def catalog_sql_bits(
    catalog: dict[str, bool] | None,
    *,
    work_alias: str = "s",
    flags_alias: str = "cf",
    score_expr: str | None = None,
) -> tuple[str, str, str]:
    """Return (join_sql, where_sql, score_sql).

    ``score_sql`` is ``score_expr`` optionally multiplied by format_weight.
    Empty join/where when flags table missing or catalog is None.
    """
    if not catalog:
        return "", "", (score_expr or "score")
    if not has_catalog_flags():
        return "", "", (score_expr or "score")

    join = f" LEFT JOIN work_flags {flags_alias} ON {flags_alias}.work_id = {work_alias}.work_id"
    where_parts = [f" NOT coalesce({flags_alias}.is_excluded, FALSE)"]
    if catalog.get("exclude_collections"):
        where_parts.append(f" NOT coalesce({flags_alias}.is_collection, FALSE)")
    if catalog.get("exclude_comics"):
        where_parts.append(f" NOT coalesce({flags_alias}.is_comic, FALSE)")
    if catalog.get("exclude_picture_books"):
        where_parts.append(f" NOT coalesce({flags_alias}.is_picture_book, FALSE)")
    if catalog.get("fiction_only"):
        where_parts.append(f" NOT coalesce({flags_alias}.is_nonfiction, FALSE)")
    if catalog.get("exclude_derivatives"):
        where_parts.append(f" NOT coalesce({flags_alias}.is_derivative, FALSE)")
    if catalog.get("collapse_duplicates"):
        where_parts.append(f" NOT coalesce({flags_alias}.is_duplicate, FALSE)")
    where = " AND " + " AND ".join(where_parts)
    if score_expr is None:
        scored = "score"
    elif catalog.get("apply_format_weight", True):
        scored = f"(({score_expr}) * coalesce({flags_alias}.format_weight, 1.0))"
    else:
        scored = f"({score_expr})"
    return join, where, scored


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=EXPLORER_DB)
    p.add_argument(
        "--years-only",
        action="store_true",
        help="Only (re)build work_years; skip work_flags",
    )
    args = p.parse_args()
    if args.years_only:
        materialize_work_years(db_path=args.db)
    else:
        materialize_catalog_flags(db_path=args.db)


if __name__ == "__main__":
    main()

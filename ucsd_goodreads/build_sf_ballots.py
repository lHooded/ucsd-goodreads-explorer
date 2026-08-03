#!/usr/bin/env python3
"""Convert UCSD Goodreads Book Graph interactions into ranking-explorer ballots.

Pipeline
--------
1. Stream book metadata; keep works that look like science fiction via
   popular_shelves (genres file has no dedicated SF bucket).
2. Collapse editions to a canonical book_id per work_id (most ratings).
3. Stream goodreads_interactions.csv; for each user, turn high ratings of SF
   works into a ranked ballot (5★ before 4★; stable tie-break by book_id).
4. Write ranking_explorer-compatible JSON + update datasets.json.

Academic use only. Cite Wan & McAuley (UCSD Book Graph); do not redistribute.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "ucsd_goodreads" / "raw"
DEFAULT_OUT_DIR = ROOT / "data" / "ucsd_goodreads" / "derived"
EXPLORER_DATA = ROOT / "ranking_explorer" / "data"

# Strong SF shelves (prefer these over ambiguous "sci-fi" / hybrid tags).
SF_CORE_SHELVES = frozenset(
    {
        "science-fiction",
        "hard-sf",
        "hard-science-fiction",
        "space-opera",
        "cyberpunk",
        "military-science-fiction",
        "military-sf",
    }
)
# Softer SF tags — counted only alongside core (excludes bare sf/sff hybrids).
SF_SOFT_SHELVES = frozenset(
    {
        "sci-fi",
        "scifi",
        "sciencefiction",
        "speculative-fiction",
    }
)
# Competing non-SF signals used to reject pure fantasy/romance shelves.
NON_SF_SHELVES = frozenset(
    {
        "fantasy",
        "paranormal",
        "urban-fantasy",
        "high-fantasy",
        "epic-fantasy",
        "paranormal-romance",
        "romance",
        "contemporary-romance",
        "historical-romance",
        "young-adult",
        "ya",
        "horror",
        "vampires",
        "werewolves",
        "shapeshifters",
        "children",
        "childrens",
        "middle-grade",
        "magic",
        "magical",
        "harry-potter",
        "hogwarts",
        "discworld",
    }
)

# Title prefixes that are overwhelmingly not SF even when miscategorised.
NON_SF_TITLE_PREFIXES = (
    "harry potter",
    "a game of thrones",
    "a clash of kings",
    "a storm of swords",
    "a feast for crows",
    "a dance with dragons",
)

ENGLISH_LANG = frozenset({"", "eng", "en", "en-US", "en-GB", "en-CA", "en-AU"})


def open_json_gz(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def shelf_counts(book: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for s in book.get("popular_shelves") or []:
        name = (s.get("name") or "").strip().lower()
        if not name:
            continue
        try:
            out[name] = int(s.get("count") or 0)
        except (TypeError, ValueError):
            out[name] = 0
    return out


def is_science_fiction(
    book: dict[str, Any],
    *,
    min_sf_shelves: int,
    min_sf_ratio: float,
) -> bool:
    """True if popular_shelves look like science fiction, not fantasy crossover.

    Requires real ``science-fiction`` (or hard-SF / space-opera / …) mass, not
    just ``sci-fi`` / ``sci-fi-fantasy`` tags that ASOIAF and Harry Potter share.
    """
    title = (book.get("title") or book.get("title_without_series") or "").casefold()
    if any(title.startswith(p) for p in NON_SF_TITLE_PREFIXES):
        return False

    counts = shelf_counts(book)
    core = sum(counts.get(s, 0) for s in SF_CORE_SHELVES)
    soft = sum(counts.get(s, 0) for s in SF_SOFT_SHELVES)
    non = sum(counts.get(s, 0) for s in NON_SF_SHELVES)
    # Also treat unlisted *fantasy* shelves (except sci-/science- hybrids) as non-SF.
    for name, count in counts.items():
        if name in NON_SF_SHELVES or name in SF_CORE_SHELVES or name in SF_SOFT_SHELVES:
            continue
        if "fantasy" in name and "sci" not in name and "science" not in name:
            non += count
        elif name in {"potter", "witchcraft", "wizards", "wizardry"}:
            non += count
    if core < min_sf_shelves:
        return False
    # Core SF must dominate competing fantasy/romance/YA shelves.
    # Soft tags (sci-fi) can help the ratio slightly but cannot replace core.
    sf = core + 0.35 * soft
    denom = sf + non
    if denom <= 0:
        return False
    return (sf / denom) >= min_sf_ratio


def load_authors(path: Path) -> dict[str, str]:
    authors: dict[str, str] = {}
    if not path.exists():
        return authors
    for rec in open_json_gz(path):
        aid = str(rec.get("author_id") or "")
        name = (rec.get("name") or "").strip()
        if aid and name:
            authors[aid] = name
    return authors


def primary_author_id(book: dict[str, Any]) -> Optional[str]:
    authors = book.get("authors") or []
    if not authors:
        return None
    # Prefer empty role (main author) over illustrator/editor.
    for a in authors:
        if (a.get("role") or "").strip() == "":
            return str(a.get("author_id"))
    return str(authors[0].get("author_id")) if authors[0].get("author_id") else None


def pick_books_path(raw: Path, prefer_full: bool) -> Path:
    full = raw / "goodreads_books.json.gz"
    fantasy = raw / "goodreads_books_fantasy_paranormal.json.gz"
    if prefer_full and full.exists() and full.stat().st_size > 100_000_000:
        return full
    if fantasy.exists() and fantasy.stat().st_size > 1_000_000:
        return fantasy
    if full.exists() and full.stat().st_size > 1_000_000:
        return full
    raise FileNotFoundError(
        f"Need {full.name} or {fantasy.name} under {raw}. Run download.sh first."
    )


def build_sf_catalog(
    books_path: Path,
    authors: dict[str, str],
    *,
    min_sf_shelves: int,
    min_sf_ratio: float,
    min_ratings: int,
    english_only: bool,
) -> tuple[dict[str, str], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Return (book_id→canonical_id, canonical books, merge records)."""
    # work_id → list of edition records
    by_work: dict[str, list[dict[str, Any]]] = defaultdict(list)
    n_seen = 0
    n_sf = 0

    for book in open_json_gz(books_path):
        n_seen += 1
        if n_seen % 200_000 == 0:
            print(f"  … scanned {n_seen:,} books, kept {n_sf:,} SF editions", flush=True)
        if english_only:
            lang = (book.get("language_code") or "").strip()
            if lang not in ENGLISH_LANG:
                continue
        try:
            ratings = int(float(book.get("ratings_count") or 0))
        except (TypeError, ValueError):
            ratings = 0
        if ratings < min_ratings:
            continue
        if not is_science_fiction(
            book, min_sf_shelves=min_sf_shelves, min_sf_ratio=min_sf_ratio
        ):
            continue
        n_sf += 1
        work_id = str(book.get("work_id") or book.get("book_id"))
        aid = primary_author_id(book)
        by_work[work_id].append(
            {
                "book_id": str(book["book_id"]),
                "work_id": work_id,
                "title": book.get("title") or book.get("title_without_series") or "",
                "author_id": aid,
                "author": authors.get(aid or "", "") or "",
                "avg_rating": _float(book.get("average_rating")),
                "ratings_count": ratings,
                "book_url": book.get("url")
                or f"https://www.goodreads.com/book/show/{book['book_id']}",
                "author_url": (
                    f"https://www.goodreads.com/author/show/{aid}" if aid else None
                ),
                "image_url": book.get("image_url"),
                "publication_year": book.get("publication_year"),
            }
        )

    book_to_canonical: dict[str, str] = {}
    canonical: dict[str, dict[str, Any]] = {}
    merges: list[dict[str, Any]] = []

    for work_id, editions in by_work.items():
        editions.sort(key=lambda e: (-e["ratings_count"], e["book_id"]))
        canon = editions[0]
        cid = canon["book_id"]
        member_votes = {e["book_id"]: e["ratings_count"] for e in editions}
        for e in editions:
            book_to_canonical[e["book_id"]] = cid
        entry = {
            "book_id": cid,
            "work_id": work_id,
            "title": canon["title"],
            "author": canon["author"],
            "author_url": canon["author_url"],
            "book_url": canon["book_url"],
            "avg_rating": canon["avg_rating"],
            "ratings_count": sum(e["ratings_count"] for e in editions),
            "merged_from": [e["book_id"] for e in editions[1:]] or None,
            "merge_layer": "work_id" if len(editions) > 1 else None,
        }
        if entry["merged_from"] is None:
            del entry["merged_from"]
            del entry["merge_layer"]
        canonical[cid] = entry
        if len(editions) > 1:
            merges.append(
                {
                    "canonical_id": cid,
                    "merged_ids": [e["book_id"] for e in editions[1:]],
                    "title": canon["title"],
                    "author": canon["author"],
                    "member_votes": member_votes,
                    "layer": "work_id",
                }
            )

    print(
        f"Scanned {n_seen:,} books → {n_sf:,} SF editions → "
        f"{len(canonical):,} works ({len(merges):,} multi-edition merges)",
        flush=True,
    )
    return book_to_canonical, canonical, merges


def _float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_book_id_map(path: Path) -> dict[str, str]:
    """csv book_id (interactions) → Goodreads book_id."""
    mapping: dict[str, str] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            mapping[row["book_id_csv"]] = row["book_id"]
    return mapping


def stream_interactions_csv(
    path: Path,
    book_map: dict[str, str],
    book_to_canonical: dict[str, str],
    *,
    min_rating: int,
) -> tuple[dict[str, dict[str, tuple[int, str]]], dict[str, int]]:
    """Return (user → {canonical_id: (rating, book_id)}, user → n_rated)."""
    # Per user best rating per work; second value is canonical book_id (stable).
    user_ratings: dict[str, dict[str, tuple[int, str]]] = defaultdict(dict)
    user_n_rated: dict[str, int] = defaultdict(int)
    n_rows = 0
    n_kept = 0

    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            n_rows += 1
            if n_rows % 5_000_000 == 0:
                print(
                    f"  … interactions {n_rows:,} rows, "
                    f"{n_kept:,} SF ratings, {len(user_ratings):,} users",
                    flush=True,
                )
            try:
                rating = int(row["rating"])
            except (TypeError, ValueError, KeyError):
                continue
            if rating <= 0:
                continue
            uid = row["user_id"]
            user_n_rated[uid] += 1
            if rating < min_rating:
                continue
            csv_bid = row["book_id"]
            gr_bid = book_map.get(csv_bid)
            if gr_bid is None:
                continue
            cid = book_to_canonical.get(gr_bid)
            if cid is None:
                continue
            n_kept += 1
            prev = user_ratings[uid].get(cid)
            if prev is None or rating > prev[0]:
                user_ratings[uid][cid] = (rating, cid)

    print(
        f"Interactions: {n_rows:,} rows → {n_kept:,} SF ratings ≥{min_rating} "
        f"across {len(user_ratings):,} users",
        flush=True,
    )
    return user_ratings, user_n_rated


def stream_interactions_fantasy_json(
    path: Path,
    book_to_canonical: dict[str, str],
    *,
    min_rating: int,
) -> tuple[dict[str, dict[str, tuple[int, str]]], dict[str, int]]:
    """Fantasy-slice interactions use raw Goodreads book/user ids."""
    user_ratings: dict[str, dict[str, tuple[int, str]]] = defaultdict(dict)
    user_n_rated: dict[str, int] = defaultdict(int)
    n_rows = 0
    n_kept = 0

    for rec in open_json_gz(path):
        n_rows += 1
        if n_rows % 5_000_000 == 0:
            print(
                f"  … fantasy interactions {n_rows:,}, kept {n_kept:,}, "
                f"users {len(user_ratings):,}",
                flush=True,
            )
        try:
            rating = int(rec.get("rating") or 0)
        except (TypeError, ValueError):
            continue
        if rating <= 0:
            continue
        uid = str(rec.get("user_id") or "")
        if not uid:
            continue
        user_n_rated[uid] += 1
        if rating < min_rating:
            continue
        gr_bid = str(rec.get("book_id") or "")
        cid = book_to_canonical.get(gr_bid)
        if cid is None:
            continue
        n_kept += 1
        prev = user_ratings[uid].get(cid)
        if prev is None or rating > prev[0]:
            user_ratings[uid][cid] = (rating, cid)

    print(
        f"Fantasy interactions: {n_rows:,} → {n_kept:,} SF ratings ≥{min_rating}, "
        f"{len(user_ratings):,} users",
        flush=True,
    )
    return user_ratings, user_n_rated


def ballots_from_ratings(
    user_ratings: dict[str, dict[str, tuple[int, str]]],
    user_n_rated: dict[str, int],
    books: dict[str, dict[str, Any]],
    *,
    min_ballot: int,
    max_ballot: int,
    max_voters: Optional[int],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    voters: list[dict[str, Any]] = []
    vote_counts: dict[str, int] = defaultdict(int)

    # Deterministic order: users with more SF ratings first (richer ballots).
    ordered = sorted(
        user_ratings.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )
    if max_voters is not None:
        ordered = ordered[:max_voters]

    for uid, ratings in ordered:
        # Sort: higher stars first; tie-break by global popularity then id.
        items = sorted(
            ratings.items(),
            key=lambda kv: (
                -kv[1][0],
                -(books.get(kv[0], {}).get("ratings_count") or 0),
                kv[0],
            ),
        )
        if max_ballot > 0:
            items = items[:max_ballot]
        if len(items) < min_ballot:
            continue
        ballot = []
        authors: set[str] = set()
        for rank, (cid, (_rating, _)) in enumerate(items, start=1):
            meta = books.get(cid) or {"book_id": cid, "title": None, "author": None}
            author = meta.get("author")
            if author:
                authors.add(author)
            ballot.append(
                {
                    "book_id": cid,
                    "rank": rank,
                    "title": meta.get("title"),
                    "author": author,
                    "rating": _rating,
                }
            )
            vote_counts[cid] += 1
        voters.append(
            {
                "vote_id": uid,
                "user_id": uid,
                "user_name": f"user_{uid}",
                "books_read": int(user_n_rated.get(uid) or len(items)),
                # Unknown in this dump — set >0 so Listopia anti-spam friends=0
                # heuristics do not treat every UCSD user as a sockpuppet.
                "friends": 1,
                "ballot_size": len(ballot),
                "num_unique_authors": len(authors),
                "ballot": ballot,
            }
        )

    return voters, dict(vote_counts)


def trim_books(
    books: dict[str, dict[str, Any]],
    vote_counts: dict[str, int],
    *,
    min_voters: int,
) -> dict[str, dict[str, Any]]:
    kept = {}
    for bid, meta in books.items():
        n = vote_counts.get(bid, 0)
        if n < min_voters:
            continue
        row = dict(meta)
        row["list_voters"] = n
        row["list_score"] = n  # no Listopia score; use raw support
        kept[bid] = row
    # Assign list_rank by support
    ranked = sorted(kept.items(), key=lambda kv: (-kv[1]["list_voters"], kv[0]))
    for i, (bid, row) in enumerate(ranked, start=1):
        row["list_rank"] = i
    return {bid: row for bid, row in ranked}


def filter_voters_to_books(
    voters: list[dict[str, Any]],
    books: dict[str, dict[str, Any]],
    *,
    min_ballot: int,
) -> list[dict[str, Any]]:
    out = []
    for v in voters:
        ballot = [b for b in v["ballot"] if b["book_id"] in books]
        for i, b in enumerate(ballot, start=1):
            b["rank"] = i
        if len(ballot) < min_ballot:
            continue
        authors = {b.get("author") for b in ballot if b.get("author")}
        nv = dict(v)
        nv["ballot"] = ballot
        nv["ballot_size"] = len(ballot)
        nv["num_unique_authors"] = len(authors)
        out.append(nv)
    return out


def update_datasets_json(
    datasets_path: Path,
    *,
    dataset_id: str,
    file_name: str,
    title: str,
    n_voters: int,
    n_books: int,
) -> None:
    entries = []
    if datasets_path.exists():
        entries = json.loads(datasets_path.read_text(encoding="utf-8"))
    entries = [e for e in entries if e.get("id") != dataset_id]
    entries.insert(
        0,
        {
            "id": dataset_id,
            "file": f"data/{file_name}",
            "title": title,
            "voters": n_voters,
            "books": n_books,
        },
    )
    datasets_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    p.add_argument(
        "--explorer-out",
        type=Path,
        default=EXPLORER_DATA / "ucsd_sf.json",
        help="ranking_explorer JSON payload",
    )
    p.add_argument("--dataset-id", default="ucsd_sf")
    p.add_argument("--title", default="UCSD Goodreads — Science Fiction")
    p.add_argument("--min-sf-shelves", type=int, default=10)
    p.add_argument(
        "--min-sf-ratio",
        type=float,
        default=0.55,
        help="SF shelf mass / (SF + fantasy/romance/YA/horror mass)",
    )
    p.add_argument("--min-book-ratings", type=int, default=50)
    p.add_argument("--min-rating", type=int, default=4, choices=[4, 5])
    p.add_argument("--min-ballot", type=int, default=3)
    p.add_argument("--max-ballot", type=int, default=40)
    p.add_argument("--min-book-voters", type=int, default=5)
    p.add_argument("--max-voters", type=int, default=0, help="0 = no cap")
    p.add_argument("--english-only", action="store_true", default=True)
    p.add_argument("--all-languages", action="store_true")
    p.add_argument(
        "--prefer-fantasy-slice",
        action="store_true",
        help="Use fantasy/paranormal genre files even if full books exist",
    )
    p.add_argument(
        "--force-seed-ids",
        type=str,
        default="17735",
        help="Comma-separated Goodreads book_ids always kept (Light=17735)",
    )
    args = p.parse_args()
    english_only = not args.all_languages

    raw: Path = args.raw
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    authors = load_authors(raw / "goodreads_book_authors.json.gz")
    print(f"Authors loaded: {len(authors):,}", flush=True)

    prefer_full = not args.prefer_fantasy_slice
    books_path = pick_books_path(raw, prefer_full=prefer_full)
    print(f"Books source: {books_path.name}", flush=True)

    book_to_canonical, books, merges = build_sf_catalog(
        books_path,
        authors,
        min_sf_shelves=args.min_sf_shelves,
        min_sf_ratio=args.min_sf_ratio,
        min_ratings=args.min_book_ratings,
        english_only=english_only,
    )

    # Force-include seed editions (e.g. Light) even if shelves missed them.
    seed_ids = [s.strip() for s in args.force_seed_ids.split(",") if s.strip()]
    if seed_ids and books_path.exists():
        needed = [s for s in seed_ids if s not in book_to_canonical]
        if needed:
            print(f"Seeding missing book_ids from catalog scan: {needed}", flush=True)
            for book in open_json_gz(books_path):
                bid = str(book.get("book_id") or "")
                if bid not in needed:
                    continue
                aid = primary_author_id(book)
                work_id = str(book.get("work_id") or bid)
                # Map all editions of this work if we see them later — for now
                # just register this edition as its own work if absent.
                if bid in book_to_canonical:
                    continue
                # Prefer an existing canonical for same work.
                existing = next(
                    (
                        b
                        for b in books.values()
                        if b.get("work_id") == work_id
                    ),
                    None,
                )
                if existing:
                    book_to_canonical[bid] = existing["book_id"]
                else:
                    book_to_canonical[bid] = bid
                    books[bid] = {
                        "book_id": bid,
                        "work_id": work_id,
                        "title": book.get("title") or "",
                        "author": authors.get(aid or "", "") or "",
                        "author_url": (
                            f"https://www.goodreads.com/author/show/{aid}"
                            if aid
                            else None
                        ),
                        "book_url": book.get("url")
                        or f"https://www.goodreads.com/book/show/{bid}",
                        "avg_rating": _float(book.get("average_rating")),
                        "ratings_count": int(float(book.get("ratings_count") or 0)),
                    }
                needed.remove(bid)
                if not needed:
                    break
            if needed:
                print(
                    f"WARNING: seed book_ids not found in {books_path.name}: {needed}",
                    flush=True,
                )

    catalog_path = out_dir / "sf_books.jsonl"
    with catalog_path.open("w", encoding="utf-8") as fh:
        for bid, meta in books.items():
            fh.write(json.dumps(meta, ensure_ascii=False) + "\n")
    (out_dir / "book_to_canonical.json").write_text(
        json.dumps(book_to_canonical), encoding="utf-8"
    )
    print(f"Wrote {catalog_path} ({len(books):,} works)", flush=True)

    csv_path = raw / "goodreads_interactions.csv"
    fantasy_ix = raw / "goodreads_interactions_fantasy_paranormal.json.gz"
    map_path = raw / "book_id_map.csv"

    # Size floors avoid streaming partial downloads (gzip EOFError / truncated CSV).
    FULL_IX_MIN = 3_500_000_000  # ~4.0G complete
    FANTASY_IX_MIN = 2_500_000_000  # ~2.6G complete

    if csv_path.exists() and csv_path.stat().st_size >= FULL_IX_MIN:
        print("Using full interactions CSV…", flush=True)
        book_map = load_book_id_map(map_path)
        user_ratings, user_n_rated = stream_interactions_csv(
            csv_path,
            book_map,
            book_to_canonical,
            min_rating=args.min_rating,
        )
        source_note = "ucsd_goodreads/goodreads_interactions.csv"
    elif fantasy_ix.exists() and fantasy_ix.stat().st_size >= FANTASY_IX_MIN:
        print("Using fantasy/paranormal interactions JSON…", flush=True)
        try:
            user_ratings, user_n_rated = stream_interactions_fantasy_json(
                fantasy_ix,
                book_to_canonical,
                min_rating=args.min_rating,
            )
        except EOFError:
            print(
                f"ERROR: {fantasy_ix.name} looks truncated "
                f"({fantasy_ix.stat().st_size:,} bytes). Re-run download.sh.",
                file=sys.stderr,
            )
            return
        source_note = "ucsd_goodreads/goodreads_interactions_fantasy_paranormal.json.gz"
    else:
        sizes = {
            "interactions.csv": csv_path.stat().st_size if csv_path.exists() else 0,
            "fantasy_interactions.json.gz": fantasy_ix.stat().st_size
            if fantasy_ix.exists()
            else 0,
        }
        print(
            "No complete interactions file yet "
            f"(csv>={FULL_IX_MIN:,}, fantasy_gz>={FANTASY_IX_MIN:,}). "
            f"Have: {sizes}. Catalog written; re-run after download finishes.",
            file=sys.stderr,
        )
        (out_dir / "build_state.json").write_text(
            json.dumps(
                {
                    "status": "catalog_only",
                    "n_works": len(books),
                    "books_source": books_path.name,
                    "partial_sizes": sizes,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return

    max_voters = args.max_voters or None
    voters, vote_counts = ballots_from_ratings(
        user_ratings,
        user_n_rated,
        books,
        min_ballot=args.min_ballot,
        max_ballot=args.max_ballot,
        max_voters=max_voters,
    )
    books = trim_books(books, vote_counts, min_voters=args.min_book_voters)
    voters = filter_voters_to_books(voters, books, min_ballot=args.min_ballot)

    # Recompute list ranks after voter trim
    vote_counts = defaultdict(int)
    for v in voters:
        for b in v["ballot"]:
            vote_counts[b["book_id"]] += 1
    books = trim_books(dict(books), dict(vote_counts), min_voters=args.min_book_voters)
    voters = filter_voters_to_books(voters, books, min_ballot=args.min_ballot)

    payload = {
        "list_id": args.dataset_id,
        "list_title": args.title,
        "source": source_note,
        "n_voters": len(voters),
        "anti_spam_applicable": False,
        "ballot_construction": {
            "min_rating": args.min_rating,
            "min_ballot": args.min_ballot,
            "max_ballot": args.max_ballot,
            "min_sf_shelves": args.min_sf_shelves,
            "min_sf_ratio": args.min_sf_ratio,
            "edition_merge": "work_id",
            "tie_break": "rating desc, ratings_count desc, book_id",
        },
        "edition_merges": merges,
        "voters": voters,
        "books": books,
    }

    args.explorer_out.parent.mkdir(parents=True, exist_ok=True)
    args.explorer_out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(
        f"Wrote {args.explorer_out} ({len(voters):,} voters, {len(books):,} books)",
        flush=True,
    )

    # Check seed coverage
    for seed in seed_ids:
        cid = book_to_canonical.get(seed, seed)
        if cid in books:
            print(
                f"  seed {seed} → {cid} {books[cid].get('title')!r}: "
                f"{books[cid].get('list_voters')} ballots",
                flush=True,
            )
        else:
            print(f"  seed {seed} not in final books (too few voters or missing)", flush=True)

    update_datasets_json(
        EXPLORER_DATA / "datasets.json",
        dataset_id=args.dataset_id,
        file_name=args.explorer_out.name,
        title=args.title,
        n_voters=len(voters),
        n_books=len(books),
    )
    print(f"Updated {EXPLORER_DATA / 'datasets.json'}", flush=True)

    (out_dir / "build_state.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "n_voters": len(voters),
                "n_books": len(books),
                "n_merges": len(merges),
                "source": source_note,
                "explorer_out": str(args.explorer_out),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

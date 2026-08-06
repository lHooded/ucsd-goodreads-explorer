#!/usr/bin/env python3
"""Leakage-controlled direct-jury pilot for semantic seed-origin dependence.

The pilot maps the user's scraped Greatest Books source lists to Goodreads works,
constructs disjoint literary origins, adds non-literary controls, and compares
held-out rankings from direct origin-affinity juries.  Every origin work is
removed from every ranked universe, so convergence cannot be created by simply
ranking the anchors that selected the jury.
"""

from __future__ import annotations

import csv
import json
import math
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

import duckdb
import numpy as np

from curators_explorer.db import DB_PATH, execute
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo
from curators_explorer.scripts.research_external_canon_omissions import (
    build_matcher,
    catalog_rows,
)


ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parents[1] / "data"
LIST_DIR = ROOT / "lists_by_title"
GREATEST = DATA / "greatestbooks_top100_2026-08-06.tsv"
CANDIDATE_CATALOG = DATA / "distributed_canon_catalog.json"
OUT_JSON = DATA / "multi_origin_seed_pilot.json"
OUT_REPORT = DATA / "MULTI_ORIGIN_SEED_PILOT_REPORT.md"

ORIGIN_SIZE = 40
MAX_TEACHER_SIZE = 2_000
MIN_ORIGIN_HITS = 3
MIN_BOOK_MASS = 10.0
LOWER_Z = 1.2815515655446004

FRANCOPHONE_SOURCES = {
    "best_foreign_work_of_fiction_chosen_by_francophone_writers",
    "fifty_french_writers_choose_their_favorite_10_books",
    "the_25_favorite_books_of_100_francophone_writers",
    "pour_une_bibliotheque_ideale",
}
ANGLOPHONE_SOURCES = {
    "the_100_greatest_british_novels",
    "the_great_american_novels",
    "the_100_best_novels_of_all_time_in_english",
    "daily_telegraph_s_100_books_of_the_century_1900_1999",
}
EASTERN_SOURCES = {"100_books_to_read_from_eastern_europe_and_central_asia"}
LATIN_AMERICAN_SOURCE = {"100_best_novels_written_in_spanish_in_the_past_25_years"}
CHINA_SOURCE = {"100_china_books_you_have_to_read"}
ROMANIAN_SOURCE = {
    "a_canonical_list_100_romanian_books_of_prose_in_100_years_1918_2018"
}
AFRICAN_SOURCE = {"africa_s_100_best_books_of_the_20th_century"}
GREEK_SOURCE = {
    "the_100_best_books_of_two_centuries_of_modern_greek_literature_1813_2013"
}
DUTCH_SOURCE = {"the_dutch_literary_canon_in_100_works"}
CHILDRENS_SOURCE = {"100_greatest_childrens_books_of_all_time"}
ROMANCE_SOURCE = {"125_best_romance_books_of_all_time"}
LATIN_AMERICAN_COUNTRIES = {
    "argentine", "argentinian", "bolivian", "brazilian", "chilean", "colombian",
    "costa rican", "cuban", "dominican", "ecuadorian", "guatemalan", "haitian",
    "honduran", "mexican", "nicaraguan", "panamanian", "paraguayan", "peruvian",
    "puerto rican", "salvadoran", "uruguayan", "venezuelan",
}
EASTERN_LANGUAGES = {
    "russian", "polish", "hungarian", "czech", "serbo-croatian", "serbian",
    "croatian", "slovenian", "romanian", "bulgarian", "ukrainian", "georgian",
    "albanian", "lithuanian", "latvian", "estonian", "turkish",
}


def load_scraped_lists() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(LIST_DIR.glob("*.csv")):
        source = path.stem
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                try:
                    year = int(row.get("year") or 0)
                except ValueError:
                    year = 0
                try:
                    global_rank = int(row.get("rank") or 10**9)
                except ValueError:
                    global_rank = 10**9
                rows.append(
                    {
                        "source": source,
                        "title": (row.get("book") or "").strip(),
                        "author": (row.get("authors") or "").strip(),
                        "year": year,
                        "country": (row.get("country") or "").strip(),
                        "language": (row.get("language") or "").strip(),
                        "global_rank": global_rank,
                    }
                )
    return rows


def load_greatest() -> list[dict[str, Any]]:
    with GREATEST.open(encoding="utf-8", newline="") as handle:
        return [
            {
                "source": "greatestbooks_head",
                "title": row["title"],
                "author": row["author"],
                "year": 0,
                "country": "",
                "language": "",
                "global_rank": int(row["rank"]),
            }
            for row in csv.DictReader(handle, delimiter="\t")
        ]


def align_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    catalog = catalog_rows()
    matcher = build_matcher(catalog)
    source_rows = load_scraped_lists()
    aligned: list[dict[str, Any]] = []
    confidence_bins = Counter()
    for source in source_rows:
        match, confidence, kind = matcher(source)
        if match is None:
            confidence_bins[kind] += 1
            continue
        confidence_bins["matched"] += 1
        aligned.append(
            {
                **source,
                "work_id": str(match["work_id"]),
                "matched_title": match["title"],
                "matched_author": match["author"],
                "catalog_n": int(match["catalog_n"]),
                "match_confidence": confidence,
                "match_kind": kind,
                "flags": {
                    key: bool(match.get(key))
                    for key in (
                        "is_excluded", "is_nonfiction", "is_comic", "is_picture_book",
                        "is_derivative", "is_duplicate", "is_collection",
                    )
                },
            }
        )
    return aligned, {
        "source_files": len(list(LIST_DIR.glob("*.csv"))),
        "source_rows": len(source_rows),
        "aligned_rows": len(aligned),
        "unique_aligned_works": len({row["work_id"] for row in aligned}),
        "match_status": dict(confidence_bins),
    }


def work_profiles(aligned: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for row in aligned:
        if any(row["flags"].values()):
            continue
        p = profiles.setdefault(
            row["work_id"],
            {
                "work_id": row["work_id"],
                "title": row["matched_title"],
                "author": row["matched_author"],
                "catalog_n": row["catalog_n"],
                "years": [],
                "countries": Counter(),
                "languages": Counter(),
                "sources": set(),
                "best_global_rank": 10**9,
            },
        )
        if row["year"]:
            p["years"].append(row["year"])
        if row["country"]:
            p["countries"][row["country"]] += 1
        if row["language"]:
            p["languages"][row["language"]] += 1
        p["sources"].add(row["source"])
        p["best_global_rank"] = min(p["best_global_rank"], row["global_rank"])
    for p in profiles.values():
        p["year"] = int(np.median(p["years"])) if p["years"] else 0
    return profiles


def candidate_score(p: dict[str, Any], preferred_sources: set[str] | None = None) -> tuple:
    preferred = 0 if not preferred_sources else len(p["sources"] & preferred_sources)
    return (-preferred, -len(p["sources"]), p["best_global_rank"], -p["catalog_n"], p["work_id"])


def origin_role(name: str) -> str:
    if name.startswith("control_"):
        return "control"
    if name.startswith("border_"):
        return "border"
    return "literary"


def origin_min_hits(rows: list[dict[str, Any]]) -> int:
    """Relax only genuinely small anchors; one hit is too popularity-sensitive."""
    return 2 if len(rows) < 30 else MIN_ORIGIN_HITS


def literary_origins(
    aligned: list[dict[str, Any]], profiles: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    greatest_rows = load_greatest()
    matcher = build_matcher(catalog_rows())
    greatest_ids: list[str] = []
    for row in greatest_rows:
        match, _confidence, _kind = matcher(row)
        if match is not None and str(match["work_id"]) in profiles:
            greatest_ids.append(str(match["work_id"]))

    def eastern(p):
        langs = {x.casefold() for x in p["languages"]}
        return bool(p["sources"] & EASTERN_SOURCES) or bool(langs & EASTERN_LANGUAGES)

    def has_source(sources: set[str]) -> Callable[[dict[str, Any]], bool]:
        return lambda p: bool(p["sources"] & sources)

    def latin_american(p: dict[str, Any]) -> bool:
        countries = {x.casefold() for x in p["countries"]}
        return bool(p["sources"] & LATIN_AMERICAN_SOURCE) and bool(
            countries & LATIN_AMERICAN_COUNTRIES
        )

    # Give the scarcer exact regional lists first claim on overlaps. Broad period
    # pools come later. Children's literature is a separately analysed border case.
    specs: list[tuple[str, Callable[[dict[str, Any]], bool], set[str] | None]] = [
        ("latin_american_lens", latin_american, LATIN_AMERICAN_SOURCE),
        ("african_lens", has_source(AFRICAN_SOURCE), AFRICAN_SOURCE),
        ("romanian_lens", has_source(ROMANIAN_SOURCE), ROMANIAN_SOURCE),
        ("modern_greek_lens", has_source(GREEK_SOURCE), GREEK_SOURCE),
        ("dutch_lens", has_source(DUTCH_SOURCE), DUTCH_SOURCE),
        ("china_list_lens", has_source(CHINA_SOURCE), CHINA_SOURCE),
        ("greatestbooks_head", lambda p: p["work_id"] in set(greatest_ids), {"greatestbooks_head"}),
        ("border_childrens_literary", has_source(CHILDRENS_SOURCE), CHILDRENS_SOURCE),
        ("eastern_central", eastern, EASTERN_SOURCES),
        ("francophone_lens", lambda p: bool(p["sources"] & FRANCOPHONE_SOURCES), FRANCOPHONE_SOURCES),
        ("anglophone_lens", lambda p: bool(p["sources"] & ANGLOPHONE_SOURCES), ANGLOPHONE_SOURCES),
        ("contemporary_1980_2017", lambda p: 1980 <= p["year"] <= 2017, None),
        ("postwar_1946_1979", lambda p: 1946 <= p["year"] <= 1979, None),
        ("modernist_1900_1945", lambda p: 1900 <= p["year"] <= 1945, None),
        ("historical_pre1900", lambda p: 0 < p["year"] < 1900, None),
    ]
    origins: dict[str, list[dict[str, Any]]] = {}
    used: set[str] = set()
    greatest_order = {work_id: i for i, work_id in enumerate(greatest_ids)}
    for name, predicate, preferred_sources in specs:
        candidates = [p for p in profiles.values() if p["work_id"] not in used and predicate(p)]
        if name == "greatestbooks_head":
            candidates.sort(key=lambda p: greatest_order.get(p["work_id"], 10**9))
        else:
            candidates.sort(key=lambda p: candidate_score(p, preferred_sources))
        selected = candidates[:ORIGIN_SIZE]
        origins[name] = selected
        used.update(p["work_id"] for p in selected)
    return origins


def control_origins(
    used_ids: set[str], profiles: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    def fetch(where: str, args: list[Any]) -> list[dict[str, Any]]:
        rows = execute(
            f"""
            SELECT DISTINCT s.work_id, s.title, s.author, s.n
            FROM work_scores s
            LEFT JOIN work_flags f USING (work_id)
            LEFT JOIN taste_signal_works t USING (work_id)
            LEFT JOIN work_genre_gates g USING (work_id)
            WHERE s.n BETWEEN 500 AND 400000
              AND NOT coalesce(f.is_excluded,FALSE)
              AND NOT coalesce(f.is_nonfiction,FALSE)
              AND NOT coalesce(f.is_comic,FALSE)
              AND NOT coalesce(f.is_picture_book,FALSE)
              AND NOT coalesce(f.is_derivative,FALSE)
              AND NOT coalesce(f.is_duplicate,FALSE)
              AND NOT coalesce(f.is_collection,FALSE)
              AND ({where})
            ORDER BY s.n DESC, s.work_id
            """,
            args,
        ).fetchall()
        return [
            {"work_id": str(r[0]), "title": r[1], "author": r[2], "catalog_n": int(r[3]),
             "year": 0, "sources": set()}
            for r in rows if str(r[0]) not in used_ids
        ]

    romance = sorted(
        (
            p for p in profiles.values()
            if p["work_id"] not in used_ids and p["sources"] & ROMANCE_SOURCE
        ),
        key=lambda p: candidate_score(p, ROMANCE_SOURCE),
    )[:ORIGIN_SIZE]
    used_ids.update(row["work_id"] for row in romance)
    commercial = fetch(
        "t.side='non_literary' AND (s.title LIKE '%#%' OR s.n>=50000)", []
    )
    chosen_commercial = commercial[:ORIGIN_SIZE]
    used_ids.update(row["work_id"] for row in chosen_commercial)
    fantasy = fetch("g.gate='fantasy' AND g.passed AND t.side='non_literary'", [])
    chosen_fantasy = [row for row in fantasy if row["work_id"] not in used_ids][:ORIGIN_SIZE]
    return {
        "control_popular_romance": romance,
        "control_commercial_series": chosen_commercial,
        "control_popular_fantasy": chosen_fantasy,
    }


def serializable_origin(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            key: (sorted(value) if isinstance(value, set) else dict(value) if isinstance(value, Counter) else value)
            for key, value in row.items()
            if key not in {"years"}
        }
        for row in rows
    ]


def run_direct_pilot(origins: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    t0 = time.time()
    candidate_payload = json.loads(CANDIDATE_CATALOG.read_text(encoding="utf-8"))
    candidates = candidate_payload["books"]
    excluded_ids = {row["work_id"] for rows in origins.values() for row in rows}
    candidates = [row for row in candidates if row["work_id"] not in excluded_ids]

    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("CREATE TEMP TABLE origin_works(origin VARCHAR, work_id VARCHAR)")
    con.executemany(
        "INSERT INTO origin_works VALUES (?, ?)",
        [(name, row["work_id"]) for name, rows in origins.items() for row in rows],
    )
    con.execute("CREATE TEMP TABLE origin_requirements(origin VARCHAR, min_hits INTEGER)")
    con.executemany(
        "INSERT INTO origin_requirements VALUES (?, ?)",
        [(name, origin_min_hits(rows)) for name, rows in origins.items()],
    )
    con.execute(
        """
        CREATE TEMP TABLE origin_affinity AS
        SELECT o.origin, e.user_id,
               count(*)::INTEGER AS hits,
               count(*) FILTER (WHERE e.rating=5)::INTEGER AS fives,
               sum((CASE WHEN e.rating=5 THEN 1.0 ELSE 0.0 END) - e.five_rate)
                   / sqrt(count(*))
                   + 0.05*ln(1.0+count(*)) AS affinity
        FROM ex.all_rating_events e
        JOIN origin_works o USING (work_id)
        JOIN origin_requirements r USING (origin)
        WHERE e.rating>0
        GROUP BY o.origin, e.user_id
        HAVING count(*) >= max(r.min_hits)
        """
    )
    availability = {
        row[0]: int(row[1])
        for row in con.execute(
            "SELECT origin,count(*) FROM origin_affinity GROUP BY origin"
        ).fetchall()
    }
    if min(availability.values(), default=0) < 200:
        raise RuntimeError(f"Origin teacher coverage too small: {availability}")
    con.execute(
        f"""
        CREATE TEMP TABLE teachers AS
        SELECT origin,user_id,affinity,hits,fives
        FROM (
            SELECT *, row_number() OVER (
                PARTITION BY origin ORDER BY affinity DESC, hits DESC, user_id
            ) AS rn
            FROM origin_affinity
        )
        WHERE rn <= {MAX_TEACHER_SIZE}
        """
    )
    con.execute("CREATE TEMP TABLE candidates(work_id VARCHAR PRIMARY KEY)")
    con.executemany("INSERT INTO candidates VALUES (?)", [(row["work_id"],) for row in candidates])
    con.execute(
        """
        CREATE TEMP TABLE user_balance AS
        SELECT t.origin,e.user_id,
               count(*) FILTER (WHERE e.rating=5)::DOUBLE AS n_high,
               count(*) FILTER (WHERE e.rating BETWEEN 1 AND 3)::DOUBLE AS n_low,
               least(count(*) FILTER (WHERE e.rating=5),
                     count(*) FILTER (WHERE e.rating BETWEEN 1 AND 3),12)::DOUBLE AS n_side
        FROM teachers t
        JOIN ex.all_rating_events e USING (user_id)
        JOIN candidates c USING (work_id)
        WHERE e.rating=5 OR e.rating BETWEEN 1 AND 3
        GROUP BY t.origin,e.user_id
        """
    )
    rows = con.execute(
        """
        SELECT t.origin,e.work_id,
               sum(CASE WHEN e.rating=5 AND b.n_high>0 THEN b.n_side/b.n_high ELSE 0 END) AS wins,
               sum(CASE WHEN e.rating BETWEEN 1 AND 3 AND b.n_low>0 THEN b.n_side/b.n_low ELSE 0 END) AS losses,
               count(DISTINCT e.user_id) AS raters
        FROM teachers t
        JOIN user_balance b USING (origin,user_id)
        JOIN ex.all_rating_events e USING (user_id)
        JOIN candidates c USING (work_id)
        WHERE e.rating=5 OR e.rating BETWEEN 1 AND 3
        GROUP BY t.origin,e.work_id
        """
    ).fetchall()
    teacher_users = defaultdict(set)
    for origin, user_id in con.execute("SELECT origin,user_id FROM teachers").fetchall():
        teacher_users[origin].add(int(user_id))
    con.close()

    candidate_meta = {row["work_id"]: row for row in candidates}
    by_origin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for origin, work_id, wins, losses, raters in rows:
        wins, losses = float(wins or 0), float(losses or 0)
        mass = wins + losses
        if mass < MIN_BOOK_MASS:
            continue
        p = (wins + 0.5) / (mass + 1.0)
        u = math.sqrt(p * (1.0 - p) / (mass + 2.0))
        meta = candidate_meta[str(work_id)]
        by_origin[origin].append(
            {
                "work_id": str(work_id), "title": meta["title"], "author": meta["author"],
                "score": 100 * (p - LOWER_Z * u), "esteem": 100 * p,
                "u": 100 * u, "pair_mass": mass, "raters": int(raters),
            }
        )
    rankings: dict[str, list[str]] = {}
    for origin, book_rows in by_origin.items():
        book_rows.sort(key=lambda row: (-row["score"], row["work_id"]))
        for rank, row in enumerate(book_rows, 1):
            row["rank"] = rank
        rankings[origin] = [row["work_id"] for row in book_rows]

    names = list(origins)
    literary = [name for name in names if origin_role(name) == "literary"]
    controls = [name for name in names if origin_role(name) == "control"]
    pairwise = []
    for a, b in combinations(names, 2):
        ua, ub = teacher_users[a], teacher_users[b]
        pairwise.append(
            {
                "a": a, "b": b,
                "kind": (
                    "literary-literary" if a in literary and b in literary else
                    "control-control" if a in controls and b in controls else
                    "literary-control" if ((a in literary and b in controls) or
                                            (b in literary and a in controls)) else
                    "literary-border" if (a in literary or b in literary) else
                    "border-control"
                ),
                "teacher_jaccard": len(ua & ub) / max(1, len(ua | ub)),
                "book_jaccard50": jaccard(rankings.get(a, []), rankings.get(b, []), 50),
                "book_jaccard200": jaccard(rankings.get(a, []), rankings.get(b, []), 200),
                "book_rbo": rbo(rankings.get(a, []), rankings.get(b, [])),
            }
        )
    frequency = Counter(
        work_id for name in literary for work_id in rankings.get(name, [])[:200]
    )
    stable_ids = [work_id for work_id, count in frequency.items() if count >= math.ceil(0.75*len(literary))]
    stable_ids.sort(key=lambda work_id: (-frequency[work_id], candidate_meta[work_id]["consensus_rank"]))
    return {
        "teacher_size": {name: len(users) for name, users in teacher_users.items()},
        "teacher_availability": availability,
        "rankable_counts": {name: len(by_origin.get(name, [])) for name in names},
        "rankings": {name: by_origin.get(name, [])[:250] for name in names},
        "pairwise": pairwise,
        "stable_literary_top200": [
            {
                "work_id": work_id,
                "title": candidate_meta[work_id]["title"],
                "author": candidate_meta[work_id]["author"],
                "origin_top200_count": frequency[work_id],
                "current_consensus_rank": candidate_meta[work_id]["consensus_rank"],
            }
            for work_id in stable_ids
        ],
        "runtime_seconds": time.time() - t0,
    }


def mean_metric(rows: list[dict[str, Any]], kind: str, key: str) -> float:
    values = [row[key] for row in rows if row["kind"] == kind]
    return float(np.mean(values)) if values else float("nan")


def main() -> None:
    t0 = time.time()
    aligned, inventory = align_sources()
    profiles = work_profiles(aligned)
    origins = literary_origins(aligned, profiles)
    used = {row["work_id"] for rows in origins.values() for row in rows}
    origins.update(control_origins(used, profiles))
    pilot = run_direct_pilot(origins)
    result = {
        "method": {
            "purpose": "semantic seed-origin dependence pilot",
            "origin_size": ORIGIN_SIZE,
            "minimum_origin_hits": {
                name: origin_min_hits(rows) for name, rows in origins.items()
            },
            "maximum_teacher_size": MAX_TEACHER_SIZE,
            "book_universe": CANDIDATE_CATALOG.name,
            "all_origin_works_excluded_from_all_rankings": True,
            "jury": "direct centered-five-star affinity; no behavioral reconstruction yet",
            "ranker": "balanced per-user 5-star versus <=3-star lower confidence bound",
            "runtime_seconds": time.time() - t0,
        },
        "inventory": inventory,
        "origins": {name: serializable_origin(rows) for name, rows in origins.items()},
        "pilot": pilot,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pairs = pilot["pairwise"]
    literary_n = len([name for name in origins if origin_role(name) == "literary"])
    border_n = len([name for name in origins if origin_role(name) == "border"])
    control_n = len([name for name in origins if origin_role(name) == "control"])
    lines = [
        "# Multi-origin semantic-seed pilot", "", "## Design", "",
        f"Mapped {inventory['aligned_rows']:,}/{inventory['source_rows']:,} scraped list rows "
        f"to {inventory['unique_aligned_works']:,} unique Goodreads works. Built "
        f"{literary_n} disjoint core literary origins, {border_n} literary border case, and "
        f"{control_n} non-literary controls, up to {ORIGIN_SIZE} works each. The union of every "
        "origin is excluded from every ranking.", "",
        "Small origins use a two-anchor reader threshold rather than three; they remain in the "
        "audit but are explicitly lower-information tests. The children's origin is compared "
        "with both sides but excluded from the core literary convergence average.", "",
        "This is the cheap direct-affinity pilot, not the final behavioral-jury refit. It tests "
        "whether the origin construction produces literary convergence before paying for full "
        "reconstruction and hierarchical scoring.", "",
        "## Origins and coverage", "",
        "| Origin | Role | Works | min hits | eligible affinity users | selected jury | rankable held-out books |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for name, rows in origins.items():
        lines.append(
            f"| {name} | {origin_role(name)} | {len(rows)} | {origin_min_hits(rows)} | "
            f"{pilot['teacher_availability'].get(name,0):,} | "
            f"{pilot['teacher_size'].get(name,0):,} | {pilot['rankable_counts'].get(name,0):,} |"
        )
    lines += [
        "", "## Convergence", "",
        f"- Literary↔literary mean teacher Jaccard: **"
        f"{mean_metric(pairs,'literary-literary','teacher_jaccard'):.3f}**; "
        f"book Jaccard@50/200: **{mean_metric(pairs,'literary-literary','book_jaccard50'):.3f}/"
        f"{mean_metric(pairs,'literary-literary','book_jaccard200'):.3f}**.",
        f"- Literary↔control mean teacher Jaccard: **"
        f"{mean_metric(pairs,'literary-control','teacher_jaccard'):.3f}**; "
        f"book Jaccard@50/200: **{mean_metric(pairs,'literary-control','book_jaccard50'):.3f}/"
        f"{mean_metric(pairs,'literary-control','book_jaccard200'):.3f}**.",
        f"- Literary↔children's-border mean teacher Jaccard: **"
        f"{mean_metric(pairs,'literary-border','teacher_jaccard'):.3f}**; "
        f"book Jaccard@50/200: **{mean_metric(pairs,'literary-border','book_jaccard50'):.3f}/"
        f"{mean_metric(pairs,'literary-border','book_jaccard200'):.3f}**.",
        f"- Books appearing in at least 75% of literary top 200s: **"
        f"{len(pilot['stable_literary_top200'])}**.", "",
        "## Shared held-out literary head", "",
        "| Book | origins top-200 | current consensus rank |", "|---|---:|---:|",
    ]
    for row in pilot["stable_literary_top200"][:50]:
        lines.append(
            f"| *{row['title']}* — {row['author']} | {row['origin_top200_count']}/{literary_n} | "
            f"{row['current_consensus_rank']} |"
        )
    lines += ["", "## Origin heads", ""]
    for name in origins:
        lines += [f"### {name}", ""]
        for row in pilot["rankings"].get(name, [])[:15]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"({row['score']:.1f} +/-{row['u']:.1f}, mass {row['pair_mass']:.1f})"
            )
        lines.append("")
    lines += [
        "## Decision rule", "",
        "Proceed to behavioral reconstruction only if literary origins converge materially "
        "more with one another than with controls and the shared head is recognizably literary. "
        "Direct-jury convergence is not proof of seed independence; it is a prerequisite for "
        "the more expensive test.", "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

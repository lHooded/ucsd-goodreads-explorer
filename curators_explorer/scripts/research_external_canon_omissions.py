#!/usr/bin/env python3
"""Crosswalk external canons against the distributed-canon research ranking."""

from __future__ import annotations

import csv
import json
import math
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from scipy.stats import spearmanr

from curators_explorer.db import execute
from curators_explorer.ranking import rank_books


ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parents[1] / "data"
LIT_PATH = ROOT / "lit-2014-2024.txt"
GREATEST_PATH = DATA / "greatestbooks_top100_2026-08-06.tsv"
SYNTHESIS_PATH = DATA / "hierarchical_stability_synthesis.json"
BOUNDARY_PATH = DATA / "hierarchical_candidate_boundary.json"
HIERARCHICAL_PATH = DATA / "hierarchical_read_selection.json"
TEMPORAL_PATH = DATA / "temporal_trajectories.json"
OUT_JSON = DATA / "external_canon_omission_audit.json"
OUT_REPORT = DATA / "EXTERNAL_CANON_OMISSION_AUDIT.md"

MAX_CATALOG_N = 80_000

# External lists sometimes name a cycle or corpus rather than one Goodreads work.
# Those are not silently equated with a first volume.
AGGREGATE_TITLES = {
    "in search of lost time",
    "lord of rings",
    "book of new sun",
}

WORK_OVERRIDES = {
    "moby dick": "2409320",
    "moby dick or whale": "2409320",
    "great gatsby": "245494",
    "ulysses": "2368224",
    "nineteen eighty four": "153313",
    "1984": "153313",
    "don quixote": "121842",
    "blood meridian": "1065465",
    "tristram shandy": "2280279",
    "life and opinions of tristram shandy": "2280279",
    "life and opinions of tristram shandy gentleman": "2280279",
    "one thousand and one nights": "859375",
    "arabian nights": "859375",
    "bible": "6405906",
    "holy bible": "6405906",
    "essays": "1311",
    "buddenbrooks": "3458174",
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", value)
    return " ".join(re.findall(r"[a-z0-9]+", value))


def title_norm(value: str) -> str:
    value = norm(value)
    value = re.sub(r"\b(the|a|an)\b", " ", value)
    return " ".join(value.split())


def author_norm(value: str) -> str:
    value = norm(value)
    value = re.sub(r"\b(jr|sr)\b", " ", value)
    value = value.replace("fyodor dostoevsky", "fyodor dostoyevsky")
    value = value.replace("unknown", "anonymous")
    return " ".join(value.split())


def load_lit() -> list[dict[str, Any]]:
    rows = []
    for rank, line in enumerate(LIT_PATH.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        title, author = re.split(r"\s+-\s+", line, maxsplit=1)
        rows.append({"rank": rank, "title": title.strip(), "author": author.strip()})
    return rows


def load_greatest() -> list[dict[str, Any]]:
    with GREATEST_PATH.open(encoding="utf-8", newline="") as handle:
        return [
            {"rank": int(row["rank"]), "title": row["title"], "author": row["author"]}
            for row in csv.DictReader(handle, delimiter="\t")
        ]


def catalog_rows() -> list[dict[str, Any]]:
    rows = execute(
        """
        SELECT s.work_id, s.book_id, s.title, s.author, s.n, s.mean, s.p5,
               coalesce(f.is_excluded, FALSE), coalesce(f.is_nonfiction, FALSE),
               coalesce(f.is_comic, FALSE), coalesce(f.is_picture_book, FALSE),
               coalesce(f.is_derivative, FALSE), coalesce(f.is_duplicate, FALSE),
               coalesce(f.is_collection, FALSE)
        FROM work_scores s
        LEFT JOIN work_flags f USING (work_id)
        WHERE s.n >= 20
        """
    ).fetchall()
    keys = (
        "work_id", "book_id", "title", "author", "catalog_n", "global_mean",
        "global_p5", "is_excluded", "is_nonfiction", "is_comic",
        "is_picture_book", "is_derivative", "is_duplicate", "is_collection",
    )
    return [dict(zip(keys, row)) for row in rows]


def build_matcher(catalog: list[dict[str, Any]]):
    by_id = {str(row["work_id"]): row for row in catalog}
    by_author: dict[str, list[dict[str, Any]]] = {}
    by_author_last: dict[str, list[dict[str, Any]]] = {}
    by_title: dict[str, list[dict[str, Any]]] = {}
    for row in catalog:
        row["_title_norm"] = title_norm(row["title"])
        row["_author_norm"] = author_norm(row["author"])
        by_author.setdefault(row["_author_norm"], []).append(row)
        by_title.setdefault(row["_title_norm"], []).append(row)
        if row["_author_norm"]:
            by_author_last.setdefault(row["_author_norm"].split()[-1], []).append(row)

    def match(source: dict[str, Any]) -> tuple[dict[str, Any] | None, float, str]:
        source_title = title_norm(source["title"])
        source_author = author_norm(source["author"])
        if source_title in AGGREGATE_TITLES:
            return None, 1.0, "aggregate_or_cycle"
        if source_title in WORK_OVERRIDES:
            row = by_id.get(WORK_OVERRIDES[source_title])
            return row, 1.0, "manual_work_override"

        pool = by_author.get(source_author, [])
        if not pool and source_author:
            pool = by_author_last.get(source_author.split()[-1], [])
        if not pool:
            # Anonymous/Various Authors are much safer as an exact-title lookup.
            pool = by_title.get(source_title, [])
        author_candidates = [
            (
                row,
                SequenceMatcher(None, source_author, row["_author_norm"]).ratio()
                if source_author else 0.0,
            )
            for row in pool
        ]

        best = None
        for row, author_similarity in author_candidates:
            title_similarity = SequenceMatcher(
                None, source_title, row["_title_norm"]
            ).ratio()
            score = 0.82 * title_similarity + 0.18 * author_similarity
            score += min(0.01, 0.001 * max(0, len(str(row["catalog_n"])) - 2))
            candidate = (score, title_similarity, int(row["catalog_n"]), row)
            if best is None or candidate[:3] > best[:3]:
                best = candidate
        if best is None or best[0] < 0.70:
            return None, 0.0 if best is None else float(best[0]), "unmatched"
        return best[3], float(best[0]), "fuzzy_title_author"

    return match


def load_research_maps():
    synthesis = json.loads(SYNTHESIS_PATH.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    hierarchical = json.loads(HIERARCHICAL_PATH.read_text(encoding="utf-8"))
    temporal = json.loads(TEMPORAL_PATH.read_text(encoding="utf-8"))
    current = {str(row["work_id"]): row for row in synthesis["books"]}
    expanded = {str(row["work_id"]): row for row in boundary["expanded_books"]}
    old = {str(row["work_id"]): row for row in hierarchical["books"]}
    trajectories = {
        str(row["work_id"]): row for row in temporal.get("central_trajectories", [])
    }
    return synthesis, current, expanded, old, trajectories


def exclusion_reason(catalog: dict[str, Any], expanded: dict[str, Any] | None) -> str:
    if expanded is not None:
        if expanded.get("expanded_rank_mass10") is None:
            return "below_pair_mass_10"
        if int(expanded["expanded_rank_mass10"]) > 200:
            return "scored_below_top_200"
        return "current_top_200"
    if int(catalog["catalog_n"]) > MAX_CATALOG_N:
        return "above_hard_80k_catalog_ceiling"
    for flag in (
        "is_excluded", "is_nonfiction", "is_comic", "is_picture_book",
        "is_derivative", "is_duplicate", "is_collection",
    ):
        if catalog.get(flag):
            return flag
    if int(catalog["catalog_n"]) < 100:
        return "below_100_catalog_ratings"
    return "pair_mass_below_2_or_no_balanced_evidence"


def align_source(
    name: str,
    source: list[dict[str, Any]],
    match,
    current: dict[str, Any],
    expanded: dict[str, Any],
    old: dict[str, Any],
    trajectories: dict[str, Any],
    love_by_id: dict[str, Any],
) -> list[dict[str, Any]]:
    aligned = []
    for source_row in source:
        catalog, confidence, match_kind = match(source_row)
        if catalog is None:
            aligned.append({
                "source": name, "source_rank": int(source_row["rank"]),
                "source_title": source_row["title"],
                "source_author": source_row["author"], "match_kind": match_kind,
                "match_confidence": confidence, "work_id": None,
                "status": match_kind,
            })
            continue
        work_id = str(catalog["work_id"])
        model = expanded.get(work_id)
        point = old.get(work_id)
        trajectory = trajectories.get(work_id)
        love = love_by_id.get(work_id)
        row = {
            "source": name,
            "source_rank": int(source_row["rank"]),
            "source_title": source_row["title"],
            "source_author": source_row["author"],
            "match_kind": match_kind,
            "match_confidence": confidence,
            **{key: value for key, value in catalog.items() if not key.startswith("_")},
            "status": exclusion_reason(catalog, model),
            "distributed_rank": None if model is None else model.get("expanded_rank_mass10"),
            "distributed_score": None if model is None else model.get("score"),
            "distributed_u": None if model is None else model.get("u"),
            "pair_mass": None if model is None else model.get("pair_mass"),
            "coverage": None if model is None else model.get("coverage"),
            "tier": None if work_id not in current else current[work_id].get("tier"),
            "love_rank": None if love is None else love["rank"],
            "love_score": None if love is None else love["score"],
            "esteem": None if point is None else point.get("esteem"),
            "heterogeneity": None if point is None else point.get("heterogeneity"),
            "gamma_1_5_score": None if point is None else point.get("gamma_1_5_score"),
            "popularity_cap30_rank": (
                None if point is None else
                point.get("specification_trajectory", {}).get("book_cap_30", {}).get("rank")
            ),
            "temporal_delta_p5": None if trajectory is None else trajectory.get("delta_p5"),
            "temporal_delta_mean_q": (
                None if trajectory is None else trajectory.get("delta_mean_q")
            ),
        }
        aligned.append(row)
    return aligned


def source_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparable = [row for row in rows if row.get("work_id")]
    overlaps = [row for row in comparable if row["status"] == "current_top_200"]
    rankable_pairs = [
        row for row in comparable if row.get("distributed_rank") is not None
    ]
    rho = None
    if len(rankable_pairs) >= 3:
        rho = float(spearmanr(
            [row["source_rank"] for row in rankable_pairs],
            [row["distributed_rank"] for row in rankable_pairs],
        ).statistic)
    popularity_rho = None
    if len(comparable) >= 3:
        popularity_rho = float(spearmanr(
            [row["source_rank"] for row in comparable],
            [math.log1p(int(row["catalog_n"])) for row in comparable],
        ).statistic)
    top25_n = sorted(
        int(row["catalog_n"]) for row in comparable if row["source_rank"] <= 25
    )
    rest_n = sorted(
        int(row["catalog_n"]) for row in comparable if row["source_rank"] > 25
    )
    return {
        "rows": len(rows),
        "matched_works": len(comparable),
        "current_top200_overlap": len(overlaps),
        "recall": len(overlaps) / max(1, len(comparable)),
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "rank_spearman_among_rankable": rho,
        # Positive means lower-ranked books are more popular; negative means the head is.
        "source_rank_vs_log_catalog_n_spearman": popularity_rho,
        "top25_median_catalog_n": top25_n[len(top25_n)//2] if top25_n else None,
        "rank26_100_median_catalog_n": rest_n[len(rest_n)//2] if rest_n else None,
        "median_catalog_n": sorted(int(row["catalog_n"]) for row in comparable)[len(comparable)//2],
    }


def markdown_table(rows: list[dict[str, Any]], limit: int = 30) -> list[str]:
    lines = [
        "| Source rank | Book | Love | Distributed | Score | Reason | n |",
        "|---:|---|---:|---:|---:|---|---:|",
    ]
    for row in rows[:limit]:
        love = ">2000" if row.get("love_rank") is None else str(row["love_rank"])
        dist = "—" if row.get("distributed_rank") is None else str(row["distributed_rank"])
        score = "—" if row.get("distributed_score") is None else f"{row['distributed_score']:.1f}"
        lines.append(
            f"| {row['source_rank']} | *{row.get('title', row.get('source_title'))}* — "
            f"{row.get('author', row.get('source_author'))} | {love} | {dist} | {score} | "
            f"{row['status'].replace('_', ' ')} | {int(row.get('catalog_n') or 0):,} |"
        )
    return lines


def main() -> None:
    catalog = catalog_rows()
    match = build_matcher(catalog)
    synthesis, current, expanded, old, trajectories = load_research_maps()

    love_payload = rank_books({
        "metric": "love", "scale_mode": "adjusted", "deweight": 15,
        "purity": 55, "min_votes": 25, "bayesian_m": 30, "limit": 2000,
    })
    love_by_id = {str(row["work_id"]): row for row in love_payload["results"]}
    love_source = [
        {"rank": row["rank"], "title": row["title"], "author": row["author"]}
        for row in love_payload["results"][:100]
    ]

    sources = {
        "lit_2014_2024": load_lit(),
        "greatestbooks_2026": load_greatest(),
        "love_default": love_source,
    }
    aligned = {
        name: align_source(
            name, rows, match, current, expanded, old, trajectories, love_by_id
        )
        for name, rows in sources.items()
    }
    summaries = {name: source_summary(rows) for name, rows in aligned.items()}

    focus_titles = {"ulysses", "great gatsby", "moby dick or whale"}
    focus = []
    seen = set()
    for rows in aligned.values():
        for row in rows:
            if title_norm(row.get("title") or row.get("source_title") or "") not in focus_titles:
                continue
            if row.get("work_id") in seen:
                continue
            seen.add(row.get("work_id"))
            focus.append(row)

    result = {
        "method": {
            "purpose": "external-canon omission audit",
            "distributed_source": SYNTHESIS_PATH.name,
            "distributed_audited_top": len(synthesis["books"]),
            "love_params": love_payload["params"],
            "love_cohort": love_payload["cohort"],
            "catalog_ceiling": MAX_CATALOG_N,
            "greatestbooks_source": "https://thegreatestbooks.org/v/table",
            "greatestbooks_snapshot": GREATEST_PATH.name,
        },
        "summaries": summaries,
        "focus_books": focus,
        "sources": aligned,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# External-canon omission audit", "",
        "This is a diagnostic crosswalk, not a validation target. The comparison lists can "
        "contain popularity, curriculum, language, prize, and list-copying effects; disagreement "
        "is evidence to explain, not automatically an error in the distributed model.", "",
        "## Coverage", "",
    ]
    for name, summary in summaries.items():
        lines += [
            f"### {name}", "",
            f"- Matched {summary['matched_works']} of {summary['rows']}; "
            f"{summary['current_top200_overlap']} are in the distributed top 200 "
            f"({100*summary['recall']:.1f}% of matched works).",
            f"- Omission/status counts: `{summary['status_counts']}`.",
            f"- Rank correlation among works scoreable above the publication threshold: "
            f"{summary['rank_spearman_among_rankable']:.3f}.", "",
            f"- Source rank versus log Goodreads catalog count: "
            f"{summary['source_rank_vs_log_catalog_n_spearman']:.3f} (negative means the "
            f"source head is more popular). Top-25 median n="
            f"{summary['top25_median_catalog_n']:,}; ranks 26–100 median n="
            f"{summary['rank26_100_median_catalog_n']:,}.", "",
        ]

    greatest = summaries["greatestbooks_2026"]
    lit = summaries["lit_2014_2024"]
    love = summaries["love_default"]
    lines += [
        "## Popularity signal, cautiously interpreted", "",
        f"The external heads are more widely read on Goodreads: Greatest Books has source-rank "
        f"versus log-readership rho {greatest['source_rank_vs_log_catalog_n_spearman']:.3f} "
        f"and a top-25 median n of {greatest['top25_median_catalog_n']:,}, versus "
        f"{greatest['rank26_100_median_catalog_n']:,} below #25. The 2014–2024 literary list "
        f"shows the same direction (rho {lit['source_rank_vs_log_catalog_n_spearman']:.3f}). "
        f"The live Love top 100 does not (rho {love['source_rank_vs_log_catalog_n_spearman']:.3f}).", "",
        "This is consistent with exposure, curriculum, and repeated-list effects, but it does "
        "not identify a causal popularity bias: being canonical also causes people to read a "
        "book. The raised-ceiling scorer is the stronger diagnostic because it tests whether "
        "high readership alone is sufficient to create a high distributed score.", "",
    ]

    lines += ["## Highest external omissions", ""]
    for name in ("greatestbooks_2026", "lit_2014_2024", "love_default"):
        omitted = [
            row for row in aligned[name]
            if row.get("work_id") and row["status"] != "current_top_200"
        ]
        lines += [f"### {name}", ""] + markdown_table(omitted, limit=30) + [""]

    lines += [
        "## Immediate interpretation of the three motivating books", "",
        "- **Ulysses:** high live-jury love but a much lower conservative distributed score. "
        "The gap is downstream of jury selection: broad cross-community disagreement and "
        "uncertainty are the leading mechanisms, with a negative observed temporal path.",
        "- **Moby-Dick:** also liked by the live jury, but heterogeneous enough to land below "
        "the publication top 200. Its temporal path rises, so enthusiast-first decay is not "
        "the explanation.",
        "- **The Great Gatsby:** unlike the other two, it is only #824 on live Love and is "
        "then removed before distributed scoring by the hard 80,000-rating ceiling. Its "
        "absence therefore combines weak distinctive enthusiasm with an eligibility design "
        "choice; a raised-ceiling counterfactual is required before judging its model rank.", "",
        "## Next diagnostic", "",
        "Rerun the expanded-prior model with the 80,000 ceiling raised while keeping all other "
        "rules fixed. Compare newly admitted mega-read books both before and after evidence "
        "saturation. This separates a popularity *eligibility ban* from actual jury esteem and "
        "cross-community consensus; it is more informative than promoting external-list books "
        "by fiat.", "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

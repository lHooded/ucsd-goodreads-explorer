#!/usr/bin/env python3
"""Synthesize the leakage-controlled multi-origin semantic-seed audit."""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


DATA = Path(__file__).resolve().parents[1] / "data"
PILOT = DATA / "multi_origin_seed_pilot.json"
FULL = DATA / "multi_origin_behavioral_full.json"
CATALOG = DATA / "distributed_canon_catalog.json"
OUT = DATA / "MULTI_ORIGIN_SEED_AUDIT_SYNTHESIS.md"

REGIONAL = [
    "latin_american_lens",
    "african_lens",
    "romanian_lens",
    "modern_greek_lens",
    "dutch_lens",
    "china_list_lens",
]


def jaccard(a: list[str], b: list[str], k: int) -> float:
    aa, bb = set(a[:k]), set(b[:k])
    return len(aa & bb) / max(1, len(aa | bb))


def intersection_n(a: list[str], b: list[str], k: int) -> int:
    return len(set(a[:k]) & set(b[:k]))


def group_mean(rows: list[dict[str, Any]], kind: str, key: str) -> float:
    return statistics.mean(row[key] for row in rows if row["kind"] == kind)


def pair_subset_mean(
    pairwise: list[dict[str, Any]], left: list[str], right: list[str], key: str
) -> float:
    left_set, right_set = set(left), set(right)
    same = left_set == right_set
    values = []
    for row in pairwise:
        a, b = row["a"], row["b"]
        if same and a in left_set and b in left_set:
            values.append(row[key])
        elif not same and (
            (a in left_set and b in right_set) or (b in left_set and a in right_set)
        ):
            values.append(row[key])
    return statistics.mean(values)


def aggregate(
    names: list[str], rankings: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    by_origin = {
        name: {row["work_id"]: row for row in rankings[name]} for name in names
    }
    work_ids = {work_id for rows in by_origin.values() for work_id in rows}
    result = []
    for work_id in work_ids:
        rows = [by_origin[name].get(work_id) for name in names]
        observed = [row for row in rows if row is not None]
        meta = observed[0]
        ranks = [row["rank"] if row is not None else 301 for row in rows]
        result.append(
            {
                "work_id": work_id,
                "title": meta["title"],
                "author": meta["author"],
                "top50_count": sum(rank <= 50 for rank in ranks),
                "top200_count": sum(rank <= 200 for rank in ranks),
                "mean_censored_rank": statistics.mean(ranks),
                "median_censored_rank": statistics.median(ranks),
                "current_consensus_rank": meta["current_consensus_rank"],
            }
        )
    result.sort(
        key=lambda row: (
            -row["top200_count"],
            -row["top50_count"],
            row["mean_censored_rank"],
            row["work_id"],
        )
    )
    for rank, row in enumerate(result, 1):
        row["ensemble_rank"] = rank
    return result


def mean_current_overlap(
    names: list[str], rankings: dict[str, list[dict[str, Any]]], current: list[str], k: int
) -> float:
    return statistics.mean(
        jaccard(current, [row["work_id"] for row in rankings[name]], k)
        for name in names
    )


def main() -> None:
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    full = json.loads(FULL.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["books"]
    comparison = full["comparison"]
    pairwise = comparison["pairwise"]
    rankings = full["rankings"]
    literary = comparison["literary_origins"]
    controls = comparison["control_origins"]
    border = comparison["border_origins"]
    broad = [name for name in literary if name not in REGIONAL]

    excluded = {
        row["work_id"]
        for rows in pilot["origins"].values()
        for row in rows
    }
    current = [
        row["work_id"]
        for row in sorted(
            (row for row in catalog if row["work_id"] not in excluded),
            key=lambda row: row["consensus_rank"],
        )
    ]
    ensemble_rows = aggregate(literary, rankings)
    ensemble = [row["work_id"] for row in ensemble_rows]

    # Leave-one-origin-out instability measures sensitivity to the set of literary starts.
    loo50, loo200 = [], []
    loo_pair200 = []
    for omitted in literary:
        kept = [name for name in literary if name != omitted]
        loo = [row["work_id"] for row in aggregate(kept, rankings)]
        loo50.append(jaccard(ensemble, loo, 50))
        loo200.append(jaccard(ensemble, loo, 200))
        loo_pair200.append(pair_subset_mean(pairwise, kept, kept, "book_jaccard200"))

    pair_lookup = {
        frozenset((row["a"], row["b"])): row for row in pairwise
    }
    origin_diagnostics = []
    for name in literary:
        lit_rows = [
            pair_lookup[frozenset((name, other))]
            for other in literary
            if other != name
        ]
        control_rows = [pair_lookup[frozenset((name, other))] for other in controls]
        ids = [row["work_id"] for row in rankings[name]]
        origin_diagnostics.append(
            {
                "name": name,
                "teachers": full["teacher"]["selected"][name],
                "ap": full["diagnostics"][name]["average_precision"],
                "within200": statistics.mean(row["book_jaccard200"] for row in lit_rows),
                "control200": statistics.mean(row["book_jaccard200"] for row in control_rows),
                "current200": jaccard(current, ids, 200),
            }
        )

    current_i50 = intersection_n(ensemble, current, 50)
    current_i200 = intersection_n(ensemble, current, 200)
    direct_pairs = pilot["pilot"]["pairwise"]
    stable = comparison["stable_literary_top200"]

    lines = [
        "# Multi-origin semantic-seed audit: synthesis",
        "",
        "## Answer",
        "",
        "The present canon is **not reproducible from any arbitrary seed**, but it is also "
        "**not merely a copy of its original literary seed**. Independent literary starts "
        "recover a common Goodreads behavior basin and a substantial held-out book core; "
        "non-literary starts recover a sharply different basin. The initial seed still matters "
        "for exact ordering, marginal books, and which literary subtraditions are emphasized.",
        "",
        f"The seed-free multi-origin ensemble shares **{current_i50}/50** and "
        f"**{current_i200}/200** books with the current ranking. A stricter core of "
        f"**{len(stable)} books** appears in at least "
        f"{comparison['stable_threshold']}/{len(literary)} independent literary top 200s. "
        "Those figures are more informative than claiming a percentage of the ranking was "
        "'caused' by the seed, which this observational experiment cannot identify.",
        "",
        "## Main evidence",
        "",
        "| Comparison | jury Jaccard | book Jaccard@50 | book Jaccard@200 |",
        "|---|---:|---:|---:|",
        f"| Literary ↔ literary (behavioral) | {group_mean(pairwise,'literary-literary','jury_jaccard'):.3f} | "
        f"{group_mean(pairwise,'literary-literary','book_jaccard50'):.3f} | "
        f"{group_mean(pairwise,'literary-literary','book_jaccard200'):.3f} |",
        f"| Literary ↔ controls (behavioral) | {group_mean(pairwise,'literary-control','jury_jaccard'):.3f} | "
        f"{group_mean(pairwise,'literary-control','book_jaccard50'):.3f} | "
        f"{group_mean(pairwise,'literary-control','book_jaccard200'):.3f} |",
        f"| Controls ↔ controls (behavioral) | {group_mean(pairwise,'control-control','jury_jaccard'):.3f} | "
        f"{group_mean(pairwise,'control-control','book_jaccard50'):.3f} | "
        f"{group_mean(pairwise,'control-control','book_jaccard200'):.3f} |",
        f"| Literary ↔ children's border | {group_mean(pairwise,'literary-border','jury_jaccard'):.3f} | "
        f"{group_mean(pairwise,'literary-border','book_jaccard50'):.3f} | "
        f"{group_mean(pairwise,'literary-border','book_jaccard200'):.3f} |",
        "",
        f"Before behavioral reconstruction, direct literary rankings overlapped at "
        f"J@200={group_mean(direct_pairs,'literary-literary','book_jaccard200'):.3f}, versus "
        f"{group_mean(direct_pairs,'literary-control','book_jaccard200'):.3f} for controls. "
        "After replacing book identities with generic behavior features, the gap widens rather "
        "than disappearing. That is the key evidence for a distributed taste signal.",
        "",
        "## Regional stress test",
        "",
        "| Origin subset | jury Jaccard | book Jaccard@50 | book Jaccard@200 |",
        "|---|---:|---:|---:|",
        f"| Six regional origins only | {pair_subset_mean(pairwise,REGIONAL,REGIONAL,'jury_jaccard'):.3f} | "
        f"{pair_subset_mean(pairwise,REGIONAL,REGIONAL,'book_jaccard50'):.3f} | "
        f"{pair_subset_mean(pairwise,REGIONAL,REGIONAL,'book_jaccard200'):.3f} |",
        f"| Eight broad/history/list origins only | {pair_subset_mean(pairwise,broad,broad,'jury_jaccard'):.3f} | "
        f"{pair_subset_mean(pairwise,broad,broad,'book_jaccard50'):.3f} | "
        f"{pair_subset_mean(pairwise,broad,broad,'book_jaccard200'):.3f} |",
        f"| Regional ↔ broad | {pair_subset_mean(pairwise,REGIONAL,broad,'jury_jaccard'):.3f} | "
        f"{pair_subset_mean(pairwise,REGIONAL,broad,'book_jaccard50'):.3f} | "
        f"{pair_subset_mean(pairwise,REGIONAL,broad,'book_jaccard200'):.3f} |",
        "",
        "Regional starts agree less with one another than the broad starts do. This is partly "
        "real cultural variation and partly much thinner Goodreads evidence. Crucially, their "
        "cross-overlap with broad starts remains materially above literary-control overlap; the "
        "common basin is not produced solely by GreatestBooks or European historical origins.",
        "",
        "## Origin-level diagnostics",
        "",
        "`within lit` is mean top-200 overlap with the other literary starts; `vs controls` is "
        "mean overlap with romance, commercial-series, and fantasy controls.",
        "",
        "| Origin | teachers | AP | within lit | vs controls | vs current |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in origin_diagnostics:
        lines.append(
            f"| {row['name']} | {row['teachers']:,} | {row['ap']:.3f} | "
            f"{row['within200']:.3f} | {row['control200']:.3f} | {row['current200']:.3f} |"
        )
    lines += [
        "",
        "The China list and contemporary-period origin lean toward the popular/romance control "
        "basin; Dutch also has limited separation. They should be retained as adversarial "
        "diagnostics, not allowed to dominate a final ensemble. Africa, Romania, Greece, and "
        "Dutch have small teacher pools, so their individual heads are much less certain.",
        "",
        "## Stability to removing an origin",
        "",
        f"Removing each literary origin in turn changes the ensemble top 50 by a mean Jaccard "
        f"of **{statistics.mean(loo50):.3f}** (range {min(loo50):.3f}–{max(loo50):.3f}) and the "
        f"top 200 by **{statistics.mean(loo200):.3f}** "
        f"(range {min(loo200):.3f}–{max(loo200):.3f}). The mean pairwise top-200 overlap stays "
        f"between **{min(loo_pair200):.3f}** and **{max(loo_pair200):.3f}**. No single origin "
        "creates the convergence.",
        "",
        "## Current ranking alignment",
        "",
        f"Mean overlap of an individual literary-origin ranking with the current ranking is "
        f"J@50/J@200 **{mean_current_overlap(literary,rankings,current,50):.3f}/"
        f"{mean_current_overlap(literary,rankings,current,200):.3f}**. For controls it is only "
        f"**{mean_current_overlap(controls,rankings,current,50):.3f}/"
        f"{mean_current_overlap(controls,rankings,current,200):.3f}**. The independent ensemble "
        f"reaches **{jaccard(ensemble,current,50):.3f}/{jaccard(ensemble,current,200):.3f}**.",
        "",
        "## Multi-origin held-out ensemble head",
        "",
        "This ordering uses only frequency and censored rank across the 14 alternative literary "
        "juries. The current consensus rank is shown for comparison but is not a tiebreaker.",
        "",
        "| Rank | Book | top-50 origins | top-200 origins | mean rank | current rank |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in ensemble_rows[:75]:
        lines.append(
            f"| {row['ensemble_rank']} | *{row['title']}* — {row['author']} | "
            f"{row['top50_count']}/{len(literary)} | {row['top200_count']}/{len(literary)} | "
            f"{row['mean_censored_rank']:.1f} | {row['current_consensus_rank']} |"
        )
    lines += [
        "",
        "## What this does not prove",
        "",
        "- The 51-feature behavior panel and candidate universe were developed in the existing "
        "pipeline. Anchor-book identity is removed, but those structural choices are not fully "
        "seed-free.",
        "- Goodreads users, translations, editions, exposure, and list-to-Goodreads matching are "
        "uneven. The regional tests are therefore lower bounds on cultural distinctiveness, not "
        "clean samples of regional readership.",
        "- The experiment establishes a stable basin, not a unique or objective canon. A "
        "different platform or a deliberately non-Goodreads population could produce another "
        "stable basin.",
        "- Popularity is reduced by balanced per-reader scoring and evidence thresholds, but it "
        "cannot be removed from who encountered and rated a book.",
        "",
        "## Recommended use",
        "",
        "Keep the present conservative ranking as the main product for now. Use this audit as "
        "evidence that its central literary signal is natural within Goodreads, and use the "
        "multi-origin frequency/rank as a new robustness diagnostic. The next high-value model "
        "change is a seed-ensemble jury: average or shrink the well-powered literary-origin "
        "membership scores while down-weighting origins with weak reconstruction or excessive "
        "control similarity. That should reduce seed-specific ordering without pretending all "
        "origins have equal evidence.",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

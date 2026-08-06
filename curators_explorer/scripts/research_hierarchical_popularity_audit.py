#!/usr/bin/env python3
"""Audit popularity leverage using aggregate-evidence saturation trajectories."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HIERARCHICAL = DATA_DIR / "hierarchical_read_selection.json"
OUT_JSON = DATA_DIR / "hierarchical_popularity_audit.json"
OUT_REPORT = DATA_DIR / "HIERARCHICAL_POPULARITY_AUDIT_REPORT.md"
CAPS = ("book_cap_30", "book_cap_60", "book_cap_120")


def partial_spearman(x, y, z):
    xr, yr, zr = rankdata(x), rankdata(y), rankdata(z)
    rxy = np.corrcoef(xr, yr)[0, 1]
    rxz = np.corrcoef(xr, zr)[0, 1]
    ryz = np.corrcoef(yr, zr)[0, 1]
    denominator = np.sqrt(max((1-rxz**2)*(1-ryz**2), 1e-12))
    return float((rxy-rxz*ryz)/denominator)


def band_rows(rows):
    out = []
    for low, high in ((10,20),(20,50),(50,100),(100,np.inf)):
        selected = [row for row in rows if low <= row["pair_mass"] < high]
        out.append(
            {
                "low": low, "high": None if np.isinf(high) else high,
                "n": len(selected),
                "score_catalog_spearman": float(
                    spearmanr(
                        [np.log1p(row["catalog_n"]) for row in selected],
                        [row["central_score"] for row in selected],
                    ).statistic
                ),
                "median_cap30_rank_change": float(
                    np.median([
                        row["book_cap_30_rank"]-row["central_rank"]
                        for row in selected
                    ])
                ),
            }
        )
    return out


def main():
    payload = json.loads(HIERARCHICAL.read_text(encoding="utf-8"))
    rows = []
    for book in payload["books"]:
        if book["hierarchical_rank"] is None:
            continue
        trajectory = book["specification_trajectory"]
        rows.append(
            {
                "work_id": book["work_id"], "title": book["title"],
                "author": book["author"], "catalog_n": book["catalog_n"],
                "pair_mass": book["pair_mass"],
                "central_rank": book["hierarchical_rank"],
                "central_score": book["score"],
                **{
                    f"{cap}_rank": trajectory[cap]["rank"] for cap in CAPS
                },
                **{
                    f"{cap}_score": trajectory[cap]["score"] for cap in CAPS
                },
            }
        )
    score = np.asarray([row["central_score"] for row in rows])
    catalog = np.log1p([row["catalog_n"] for row in rows])
    mass = np.log1p([row["pair_mass"] for row in rows])
    top200 = [row for row in rows if row["central_rank"] <= 200]
    catalog_order = np.argsort([row["catalog_n"] for row in top200])
    quartile = np.empty(len(top200), dtype=int)
    quartile[catalog_order] = np.minimum(
        3, np.arange(len(top200)) * 4 // len(top200)
    )
    quartiles = []
    for q in range(4):
        selected = [row for row, group in zip(top200, quartile) if group == q]
        quartiles.append(
            {
                "quartile": q+1, "n": len(selected),
                "catalog_min": min(row["catalog_n"] for row in selected),
                "catalog_max": max(row["catalog_n"] for row in selected),
                "cap30_top200_survival": float(np.mean([
                    row["book_cap_30_rank"] <= 200 for row in selected
                ])),
                "median_cap30_rank_change": float(np.median([
                    row["book_cap_30_rank"]-row["central_rank"] for row in selected
                ])),
                "median_cap30_score_change": float(np.median([
                    row["book_cap_30_score"]-row["central_score"] for row in selected
                ])),
            }
        )
    cap_summaries = {
        summary["label"]: summary
        for summary in payload["specifications"] if summary["label"] in CAPS
    }
    result = {
        "meta": {
            "purpose": "popularity leverage under aggregate book-evidence saturation",
            "rankable_books": len(rows),
        },
        "associations": {
            "score_catalog_spearman": float(spearmanr(score, catalog).statistic),
            "score_pair_mass_spearman": float(spearmanr(score, mass).statistic),
            "catalog_pair_mass_spearman": float(spearmanr(catalog, mass).statistic),
            "score_catalog_partial_spearman_given_pair_mass": partial_spearman(
                score, catalog, mass
            ),
        },
        "cap_summaries": cap_summaries,
        "pair_mass_bands": band_rows(rows),
        "top200_catalog_quartiles": quartiles,
        "central_top50": top200[:50],
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    a = result["associations"]
    lines = [
        "# Hierarchical popularity-leverage audit", "", "## Result", "",
        "Aggregate book evidence is forcibly saturated at 30, 60, and 120 effective pair "
        "votes while community-cell caps, jury weights, and conditional preference events "
        "stay fixed. This removes the principal route by which a widely read book can gain "
        "extra precision without erasing genuine conditional esteem.", "",
        f"- Uncapped score versus catalog readership: rho **{a['score_catalog_spearman']:.3f}**.",
        f"- Score versus catalog readership conditional on pair mass (partial Spearman): "
        f"**{a['score_catalog_partial_spearman_given_pair_mass']:.3f}**.",
        f"- Catalog readership versus effective pair mass: rho "
        f"**{a['catalog_pair_mass_spearman']:.3f}**.", "",
        "| aggregate cap | J@50 | J@200 | RBO | score/catalog rho | median top200 u |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for cap in CAPS:
        row = cap_summaries[cap]
        lines.append(
            f"| {cap.rsplit('_',1)[1]} | {row['jaccard50_vs_central']:.3f} | "
            f"{row['jaccard200_vs_central']:.3f} | {row['rbo_vs_central']:.3f} | "
            f"{row['score_catalog_spearman']:.3f} | {row['median_top200_u']:.2f} |"
        )
    lines += ["", "## Point-head stress trajectory", "",
              "| # | book | catalog n | pair mass | cap30 | cap60 | cap120 |",
              "|---:|---|---:|---:|---:|---:|---:|"]
    for row in top200[:30]:
        lines.append(
            f"| {row['central_rank']} | {row['title']} — {row['author']} | "
            f"{row['catalog_n']:,} | {row['pair_mass']:.1f} | "
            f"{row['book_cap_30_rank']} | {row['book_cap_60_rank']} | "
            f"{row['book_cap_120_rank']} |"
        )
    lines += ["", "## Within-evidence associations", "",
              "| pair mass | books | score/catalog rho | median cap30 rank change |",
              "|---|---:|---:|---:|"]
    for row in result["pair_mass_bands"]:
        high = "∞" if row["high"] is None else str(row["high"])
        lines.append(
            f"| {row['low']}–{high} | {row['n']} | {row['score_catalog_spearman']:.3f} | "
            f"{row['median_cap30_rank_change']:+.0f} |"
        )
    lines += ["", "## Interpretation", "",
              "Survival under a low evidence cap is evidence against *precision-driven* "
              "popularity bias, not proof of a bias-free canon. Cultural familiarity can "
              "affect who reads, rates, or becomes a juror even after numerical evidence is "
              "capped; feature-family and selection trajectories remain necessary.", ""]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

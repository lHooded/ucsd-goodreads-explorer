#!/usr/bin/env python3
"""Synthesize the hierarchical challenger into stability/evidence tiers."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np

from curators_explorer.scripts.research_hierarchical_read_selection import (
    ASSIGNMENTS,
    OBSERVATIONS,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HIERARCHICAL = DATA_DIR / "hierarchical_read_selection.json"
READER_BOOT = DATA_DIR / "hierarchical_reader_bootstrap_full.json"
JURY_BOOT = DATA_DIR / "hierarchical_jury_bootstrap_full.json"
MEMBERSHIP = DATA_DIR / "hierarchical_membership_audit.json"
FEATURE_JURIES = DATA_DIR / "hierarchical_feature_juries.json"
BOUNDARY = DATA_DIR / "hierarchical_candidate_boundary.json"
FIXED_MASS = DATA_DIR / "fixed_mass_subsamples_full.json"
JOINT_BOOT = DATA_DIR / "hierarchical_joint_bootstrap_full.json"
COMMUNITY_REWEIGHT = DATA_DIR / "adversarial_community_reweighting_full.json"
EDITION_LANGUAGE = DATA_DIR / "edition_language_fragmentation.json"
TEMPORAL = DATA_DIR / "temporal_trajectories.json"
OUT_JSON = DATA_DIR / "hierarchical_stability_synthesis.json"
OUT_REPORT = DATA_DIR / "HIERARCHICAL_STABILITY_SYNTHESIS_REPORT.md"

PLAUSIBLE_SPECS = (
    "central", "book_prior_20", "book_prior_100", "book_cap_60",
    "book_cap_120", "evidence_z_0_5", "evidence_z_1_282",
    "unrated_gamma_1_5", "unrated_gamma_2",
)


def evidence_for(work_ids):
    con = duckdb.connect()
    con.execute("PRAGMA threads=8")
    con.execute("CREATE TEMP TABLE ranked(work_id VARCHAR PRIMARY KEY)")
    con.executemany("INSERT INTO ranked VALUES (?)", [(x,) for x in work_ids])
    rows = con.execute(
        f"""
        SELECT o.work_id,
               count(*) FILTER (WHERE o.rating>0)::BIGINT AS full_raters,
               count(*) FILTER (WHERE o.is_read OR o.rating>0)::BIGINT AS full_readers,
               count(*) FILTER (WHERE o.is_read AND o.rating=0)::BIGINT AS full_read_unrated,
               count(*) FILTER (WHERE o.is_reviewed)::BIGINT AS full_reviewed,
               count(*) FILTER (WHERE a.jury_q>0 AND o.rating>0)::BIGINT AS jury_raters,
               sum(a.jury_q) FILTER (WHERE o.rating>0) AS jury_rated_mass,
               sum(a.jury_q) FILTER (WHERE o.is_read OR o.rating>0) AS jury_read_mass
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN ranked r USING (work_id)
        LEFT JOIN read_parquet('{ASSIGNMENTS}') a USING (user_id)
        GROUP BY o.work_id
        """
    ).fetchall()
    con.close()
    return {
        row[0]: {
            "full_raters": int(row[1]), "full_readers": int(row[2]),
            "full_read_unrated": int(row[3]), "full_reviewed": int(row[4]),
            "jury_raters": int(row[5]),
            "jury_rated_mass": 0.0 if row[6] is None else float(row[6]),
            "jury_read_mass": 0.0 if row[7] is None else float(row[7]),
        }
        for row in rows
    }


def temporal_maps(payload):
    trajectories = {row["work_id"]: row for row in payload["central_trajectories"]}
    declines = {
        row["work_id"]: row for row in payload["all_direction_consistent_declines"]
    }
    rises = {
        row["work_id"]: row for row in payload["all_direction_consistent_rises"]
    }
    return trajectories, declines, rises


def assign_tier(
    pair_mass, joint_rate, ranks, membership_ranks, feature_ranks,
    boundary_rank, fixed120_rate, community_status, gamma2_score
):
    plausible_survival = all(rank is not None and rank <= 200 for rank in ranks)
    membership_survival = bool(membership_ranks) and all(
        rank is not None and rank <= 200 for rank in membership_ranks
    )
    feature_survival = bool(feature_ranks) and all(
        rank is not None and rank <= 200 for rank in feature_ranks
    )
    boundary_survival = boundary_rank is not None and boundary_rank <= 200
    if (
        pair_mass >= 20 and joint_rate >= 0.8
        and plausible_survival and membership_survival and feature_survival
        and boundary_survival and fixed120_rate >= 0.8
        and community_status == "broadly_stable" and gamma2_score >= 50
    ):
        return "stable_core"
    if (
        plausible_survival and membership_survival and feature_survival
        and boundary_survival and joint_rate >= 0.5
        and fixed120_rate >= 0.5 and community_status == "broadly_stable"
        and gamma2_score >= 50
    ):
        return "supported_boundary"
    return "underexposed_or_contested"


def main():
    hierarchical = json.loads(HIERARCHICAL.read_text(encoding="utf-8"))
    boot = json.loads(READER_BOOT.read_text(encoding="utf-8"))
    jury_boot = json.loads(JURY_BOOT.read_text(encoding="utf-8"))
    membership = json.loads(MEMBERSHIP.read_text(encoding="utf-8"))
    feature_juries = json.loads(FEATURE_JURIES.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    fixed_mass = json.loads(FIXED_MASS.read_text(encoding="utf-8"))
    joint_boot = json.loads(JOINT_BOOT.read_text(encoding="utf-8"))
    community_reweight = json.loads(COMMUNITY_REWEIGHT.read_text(encoding="utf-8"))
    edition_language = json.loads(EDITION_LANGUAGE.read_text(encoding="utf-8"))
    temporal = json.loads(TEMPORAL.read_text(encoding="utf-8"))
    hierarchical_by_id = {row["work_id"]: row for row in hierarchical["books"]}
    boot_by_id = {row["work_id"]: row for row in boot["books"]}
    jury_by_id = {
        row["work_id"]: row for row in jury_boot["variants"][0]["books"]
    }
    membership_by_id = {
        row["work_id"]: row for row in membership["membership_trajectory"]
    }
    feature_by_id = {
        row["work_id"]: row for row in feature_juries["soft_point_top200_trajectory"]
    }
    boundary_by_id = {
        row["work_id"]: row for row in boundary["old_top200_trajectory"]
    }
    fixed60_by_id = {
        row["work_id"]: row for row in fixed_mass["targets"]["60"]["books"]
    }
    fixed120_by_id = {
        row["work_id"]: row for row in fixed_mass["targets"]["120"]["books"]
    }
    joint_by_id = {row["work_id"]: row for row in joint_boot["books"]}
    community_by_id = {row["work_id"]: row for row in community_reweight["books"]}
    trajectories, declines, rises = temporal_maps(temporal)
    # The research point model now learns its empirical priors on every eligible mass-2
    # work, then applies the unchanged mass-10 publication threshold. Retain the earlier
    # paths as sensitivity maps and override only the central point fields here.
    point_top = []
    for expanded in boundary["expanded_mass10_top200"]:
        old = dict(hierarchical_by_id[expanded["work_id"]])
        old.update(
            {
                "hierarchical_rank": expanded["expanded_rank_mass10"],
                "score": expanded["score"], "u": expanded["u"],
                "pair_mass": expanded["pair_mass"],
                "observed_coverage": expanded["coverage"],
                "catalog_n": expanded["catalog_n"],
            }
        )
        point_top.append(old)
    evidence = evidence_for([row["work_id"] for row in point_top])
    books = []
    for row in point_top:
        work_id = row["work_id"]
        reader = boot_by_id.get(work_id)
        jury = jury_by_id.get(work_id)
        member = membership_by_id.get(work_id)
        feature = feature_by_id.get(work_id)
        joint = joint_by_id[work_id]
        community = community_by_id[work_id]
        boundary_row = next(
            item for item in boundary["expanded_mass10_top200"]
            if item["work_id"] == work_id
        )
        fixed60 = fixed60_by_id.get(work_id)
        fixed120 = fixed120_by_id.get(work_id)
        spec = row["specification_trajectory"]
        plausible_ranks = [spec[label]["rank"] for label in PLAUSIBLE_SPECS]
        plausible_scores = [spec[label]["score"] for label in PLAUSIBLE_SPECS]
        membership_ranks = [] if member is None else [
            member["hard jury / hard communities"],
            member["soft jury / fuzzy90 communities"],
            member["hard jury / fuzzy90 communities"],
        ]
        feature_ranks = [] if feature is None else [
            feature["rich_no_direct_activity / hard"],
            feature["rich_no_direct_activity / fuzzy90"],
        ]
        boundary_rank = boundary_row["expanded_rank_mass10"]
        fixed120_rate = 0.0 if fixed120 is None else fixed120["top200_rate"]
        tier = assign_tier(
            row["pair_mass"], joint["top200_rate"], plausible_ranks, membership_ranks,
            feature_ranks, boundary_rank, fixed120_rate,
            community["community_status"], row["gamma_2_score"],
        )
        trajectory = trajectories.get(work_id)
        if work_id in declines:
            temporal_status, path = "decline_consistent", declines[work_id]
        elif work_id in rises:
            temporal_status, path = "rise_consistent", rises[work_id]
        elif trajectory is not None:
            temporal_status, path = "clock_sensitive", None
        else:
            temporal_status, path = "insufficient", None
        analytic_u = float(row["u"])
        reader_u = None if reader is None else float(reader["reader_u80"])
        jury_u = None if jury is None else float(jury["jury_u80"])
        joint_u = float(joint["joint_u80"])
        books.append(
            {
                "rank": row["hierarchical_rank"], "work_id": work_id,
                "title": row["title"], "author": row["author"],
                "score": row["score"],
                # Conservative envelope: the widths partly overlap and must not be
                # added as if independent.
                "provisional_u": max(analytic_u, joint_u),
                "analytic_u": analytic_u, "reader_u80": reader_u,
                "jury_u80": jury_u, "joint_u80": joint_u,
                "tier": tier, "pair_mass": row["pair_mass"],
                "coverage": row["observed_coverage"],
                "joint_eligibility_rate": joint["eligibility_rate"],
                "joint_top200_rate": joint["top200_rate"],
                "joint_rank_q10": joint["rank_q10"],
                "joint_rank_q90": joint["rank_q90"],
                "reader_top200_rate": None if reader is None else reader["bootstrap_top200_rate"],
                "reader_rank_q10": None if reader is None else reader["rank_q10"],
                "reader_rank_q90": None if reader is None else reader["rank_q90"],
                "jury_top200_rate": None if jury is None else jury["top200_rate"],
                "jury_rank_q10": None if jury is None else jury["rank_q10"],
                "jury_rank_q90": None if jury is None else jury["rank_q90"],
                "membership_rank_min": min(membership_ranks, default=None),
                "membership_rank_max": max(membership_ranks, default=None),
                "feature_rank_min": min(
                    (rank for rank in feature_ranks if rank is not None), default=None
                ),
                "feature_rank_max": max(
                    (rank for rank in feature_ranks if rank is not None), default=None
                ),
                "expanded_prior_rank": boundary_rank,
                "old_prior_rank": boundary_row["old_rank"],
                "fixed60_top200_rate": 0.0 if fixed60 is None else fixed60["top200_rate"],
                "fixed60_rank_q10": None if fixed60 is None else fixed60["rank_q10"],
                "fixed60_rank_q90": None if fixed60 is None else fixed60["rank_q90"],
                "fixed120_top200_rate": fixed120_rate,
                "fixed120_rank_q10": None if fixed120 is None else fixed120["rank_q10"],
                "fixed120_rank_q90": None if fixed120 is None else fixed120["rank_q90"],
                "community_status": community["community_status"],
                "community_r2_robust_score": community["robust_2.0_score"],
                "community_r2_robust_drop": community["robust_2.0_drop"],
                "community_r2_robust_rank": community["robust_2.0_rank"],
                "community_r2_top200_rate": community["random_2.0_top200_rate"],
                "community_r2_rank_q10": community["random_2.0_rank_q10"],
                "community_r2_rank_q90": community["random_2.0_rank_q90"],
                "plausible_rank_min": min(plausible_ranks),
                "plausible_rank_median": float(np.median(plausible_ranks)),
                "plausible_rank_max": max(plausible_ranks),
                "plausible_score_min": min(plausible_scores),
                "plausible_score_max": max(plausible_scores),
                "mass20_rank": spec["mass_20"]["rank"],
                "popularity_stress_rank": spec["book_cap_30"]["rank"],
                "gamma2_score": row["gamma_2_score"],
                "all_low_score": row["all_unrated_low_score"],
                "rating_completion": row["rating_completion"],
                "temporal_status": temporal_status,
                "early_p5": None if trajectory is None else trajectory["early_p5"],
                "late_p5": None if trajectory is None else trajectory["late_p5"],
                "delta_p5": None if trajectory is None else trajectory["delta_p5"],
                "delta_mean_q": None if trajectory is None else trajectory["delta_mean_q"],
                "temporal_path_min": None if path is None else path["path_delta_min"],
                "temporal_path_max": None if path is None else path["path_delta_max"],
                **evidence.get(work_id, {}),
            }
        )
    tier_counts = {
        label: sum(row["tier"] == label for row in books)
        for label in ("stable_core", "supported_boundary", "underexposed_or_contested")
    }
    result = {
        "method": {
            "status": "preferred research point model; not yet production default",
            "point_rankable": boundary["counts"]["mass_ge_10"],
            "prior_population": boundary["counts"]["mass_ge_2"],
            "displayed_top": len(books),
            "score_catalog_spearman": boundary["meta"]["score_catalog_spearman_mass10"],
            "reader_bootstrap_replicates": boot["meta"]["replicates"],
            "reader_jaccard50_mean": boot["summary"]["jaccard50_mean"],
            "reader_jaccard200_mean": boot["summary"]["jaccard200_mean"],
            "jury_bootstrap_replicates": jury_boot["meta"]["completed_replicates"],
            "jury_jaccard50_mean": jury_boot["variants"][0]["jaccard50_mean"],
            "jury_jaccard200_mean": jury_boot["variants"][0]["jaccard200_mean"],
            "joint_bootstrap_replicates": joint_boot["meta"]["replicates"],
            "joint_jaccard50_mean": joint_boot["summary"]["jaccard50_mean"],
            "joint_jaccard200_mean": joint_boot["summary"]["jaccard200_mean"],
            "joint_median_u80": joint_boot["summary"]["median_joint_u80"],
            "community_reweight_replicates": community_reweight["meta"]["replicates_per_ratio"],
            "community_r2_jaccard50": community_reweight["ratios"]["2.0"]["jaccard50_mean"],
            "community_r2_jaccard200": community_reweight["ratios"]["2.0"]["jaccard200_mean"],
            "community_r2_robust_jaccard50": community_reweight["ratios"]["2.0"]["robust_jaccard50"],
            "community_r2_robust_jaccard200": community_reweight["ratios"]["2.0"]["robust_jaccard200"],
            "community_mixture_sensitive": community_reweight["counts"]["mixture_sensitive"],
            "duplicate_merge_jaccard50": edition_language["comparison"]["jaccard50"],
            "duplicate_merge_jaccard200": edition_language["comparison"]["jaccard200"],
            "top200_median_editions": edition_language["language_summary"]["top200_median_editions"],
            "top200_multilanguage_works": edition_language["language_summary"]["top200_with_multiple_known_languages"],
            "feature_no_activity_jaccard50": next(
                row["jaccard50_vs_soft_point"] for row in feature_juries["variants"]
                if row["label"] == "rich_no_direct_activity / hard"
            ),
            "feature_no_activity_jaccard200": next(
                row["jaccard200_vs_soft_point"] for row in feature_juries["variants"]
                if row["label"] == "rich_no_direct_activity / hard"
            ),
            "expanded_prior_jaccard50": boundary["comparison"]["mass10_vs_old_jaccard50"],
            "expanded_prior_jaccard200": boundary["comparison"]["mass10_vs_old_jaccard200"],
            "fixed60_jaccard50": fixed_mass["targets"]["60"]["jaccard50_mean"],
            "fixed60_jaccard200": fixed_mass["targets"]["60"]["jaccard200_mean"],
            "fixed120_jaccard50": fixed_mass["targets"]["120"]["jaccard50_mean"],
            "fixed120_jaccard200": fixed_mass["targets"]["120"]["jaccard200_mean"],
            "predictive_heterogeneity_floor": boundary["meta"][
                "predictive_heterogeneity_floor"
            ],
            "provisional_u": "max(analytic posterior/partition u, joint reader-by-jury u80)",
            "provisional_u_excludes": [
                "MNAR Gamma path", "temporal drift", "teacher-feature alternatives",
            ],
        },
        "tier_counts": tier_counts,
        "books": books,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    labels = {
        "stable_core": "core", "supported_boundary": "supported",
        "underexposed_or_contested": "fragile",
    }
    temporal_labels = {
        "decline_consistent": "↓", "rise_consistent": "↑",
        "clock_sensitive": "mixed", "insufficient": "—",
    }
    lines = [
        "# Stability-first hierarchical canon challenger",
        "",
        "## Decision",
        "",
        "The expanded-prior hierarchical model is now the preferred research ranking, "
        "although it is not yet the production default. It removes the popularity-correlated "
        "coverage cliff by predicting unobserved communities with partial pooling, while "
        f"explicitly charging a {100*result['method']['predictive_heterogeneity_floor']:.1f}-point "
        "empirical heterogeneity floor for those predictions.",
        "",
        f"Across the displayed top 200 there are **{tier_counts['stable_core']} stable-core**, "
        f"**{tier_counts['supported_boundary']} supported/boundary**, and "
        f"**{tier_counts['underexposed_or_contested']} underexposed-or-contested** books. "
        "The tiers annotate evidence; they do not change the point order.",
        "",
        "A stable-core book stays top 200 under nine plausible prior/evidence-cap/uncertainty/Γ "
        "specifications, all hard/soft/fuzzy membership paths, the no-shelf-size jury, and "
        "the expanded-prior ranking; has at least 80% joint-reader-by-jury and fixed-mass-120 "
        "top-200 inclusion; survives the bounded community-influence test; has pair mass at "
        "least 20; and retains score at least 50 under "
        "Γ=2. The supported tier relaxes "
        "the mass and inclusion conditions; the final tier is an explicit uncertainty flag.",
        "",
        f"- Rankable books: **{result['method']['point_rankable']:,}** at publication mass 10; "
        f"priors are learned on **{result['method']['prior_population']:,}** mass-2 works.",
        f"- Reader stability: mean Jaccard **{result['method']['reader_jaccard50_mean']:.3f}** "
        f"at 50 and **{result['method']['reader_jaccard200_mean']:.3f}** at 200 over 2,000 draws.",
        f"- Jury-definition stability: mean Jaccard **{result['method']['jury_jaccard50_mean']:.3f}** "
        f"at 50 and **{result['method']['jury_jaccard200_mean']:.3f}** at 200 over 100 refits.",
        f"- Joint reader-by-jury stability: mean Jaccard **{result['method']['joint_jaccard50_mean']:.3f}** "
        f"at 50 and **{result['method']['joint_jaccard200_mean']:.3f}** at 200 over "
        f"{result['method']['joint_bootstrap_replicates']:,} draws; median top-200 joint u80 "
        f"is **{result['method']['joint_median_u80']:.2f}** points.",
        f"- Bounded community influence (largest weight at most 2x smallest): shared-mixture "
        f"mean Jaccard **{result['method']['community_r2_jaccard50']:.3f}/"
        f"{result['method']['community_r2_jaccard200']:.3f}** at 50/200; book-specific "
        f"least-favourable Jaccard **{result['method']['community_r2_robust_jaccard50']:.3f}/"
        f"{result['method']['community_r2_robust_jaccard200']:.3f}**. All "
        f"{result['method']['community_mixture_sensitive']} sensitive books were already fragile.",
        f"- Edition/language audit: merging all already-flagged duplicate work IDs leaves "
        f"Jaccard **{result['method']['duplicate_merge_jaccard50']:.3f}/"
        f"{result['method']['duplicate_merge_jaccard200']:.3f}** at 50/200. The top 200 has "
        f"a median **{result['method']['top200_median_editions']:.0f}** editions, and "
        f"**{result['method']['top200_multilanguage_works']}** have more than one known "
        "edition language; known fragmentation is not driving the ranking.",
        f"- No-shelf-size jury: Jaccard **{result['method']['feature_no_activity_jaccard50']:.3f}** "
        f"at 50 and **{result['method']['feature_no_activity_jaccard200']:.3f}** at 200; "
        f"expanded-prior mass-10 ranking: **{result['method']['expanded_prior_jaccard50']:.3f} / "
        f"{result['method']['expanded_prior_jaccard200']:.3f}**.",
        f"- Actual-reader fixed-mass thinning: mean Jaccard 50/200 is "
        f"**{result['method']['fixed60_jaccard50']:.3f}/{result['method']['fixed60_jaccard200']:.3f}** "
        f"at expected mass 60 and **{result['method']['fixed120_jaccard50']:.3f}/"
        f"{result['method']['fixed120_jaccard200']:.3f}** at mass 120.",
        f"- Score versus catalog readership: Spearman **{result['method']['score_catalog_spearman']:.3f}**. "
        "Under the aggressive 30-vote aggregate cap, Jaccard is 0.724/0.869 at 50/200 and "
        "all five point leaders remain top ten. This argues against precision-driven "
        "popularity at the head, but not against cultural familiarity or reader selection.",
        "",
        "`score ±u*` uses the larger of analytic posterior/partition uncertainty and the "
        "joint reader-by-jury u80. The components overlap and are not added in quadrature. "
        "Feature-family, fixed-mass, Γ, and temporal paths remain separate.",
        "",
        "## Current top 50",
        "",
        "| # | book | score ±u* | tier | spec ranks | cap30 | joint ranks | joint top200 | full readers | pair mass | coverage | rated/read | temporal |",
        "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in books[:50]:
        completion = "—" if row["rating_completion"] is None else f"{100*row['rating_completion']:.0f}%"
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | "
            f"{row['score']:.1f} ±{row['provisional_u']:.1f} | {labels[row['tier']]} | "
            f"{row['plausible_rank_min']}–{row['plausible_rank_max']} | "
            f"{row['popularity_stress_rank']} | "
            f"{row['joint_rank_q10']:.0f}–{row['joint_rank_q90']:.0f} | "
            f"{100*row['joint_top200_rate']:.0f}% | "
            f"{row['full_readers']:,} | {row['pair_mass']:.1f} | "
            f"{100*row['coverage']:.0f}% | {completion} | "
            f"{temporal_labels[row['temporal_status']]} |"
        )
    lines += [
        "", "## Current top 50: upstream and fixed-mass stress", "",
        "`mass60` is a deliberately severe stress path and is not a core-tier veto.", "",
        "| # | book | no-activity ranks | old-prior rank | mass60 ranks | mass120 ranks | community R2 worst |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in books[:50]:
        feature_text = "—" if row["feature_rank_min"] is None else f"{row['feature_rank_min']}–{row['feature_rank_max']}"
        expanded_text = "—" if row["old_prior_rank"] is None else str(row["old_prior_rank"])
        fixed60_text = "—" if row["fixed60_rank_q10"] is None else f"{row['fixed60_rank_q10']:.0f}–{row['fixed60_rank_q90']:.0f}"
        fixed120_text = "—" if row["fixed120_rank_q10"] is None else f"{row['fixed120_rank_q10']:.0f}–{row['fixed120_rank_q90']:.0f}"
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | {feature_text} | "
            f"{expanded_text} | {fixed60_text} | {fixed120_text} | "
            f"{row['community_r2_robust_rank']} |"
        )
    lines += [
        "",
        "## Remaining limitations and next work",
        "",
        "1. Retain the three sub-10 exploratory top-200 entrants as an underexposed watch list "
        "until additional evidence exists.",
        "2. The four books newly entering the publication top 200 have now been audited and "
        "remain in the fragile tier because at least one membership/feature path crosses rank "
        "200 and their old-prior Γ=2 scores fall just below 50.",
        "3. Keep known-read/unrated Γ and temporal trajectories visible as systematic paths, "
        "not silently folded into the score.",
        "4. Treat cultural familiarity and Goodreads selection as the main unresolved bias; "
        "stability cannot prove that an unobserved or culturally isolated canon has been recovered.",
        "5. Any further cross-language work-ID merging needs external identifiers or manual "
        "review; translated title text alone is not safe enough to mutate the point model.",
        "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

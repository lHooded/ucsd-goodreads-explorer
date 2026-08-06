#!/usr/bin/env python3
"""Temporal trajectory and enthusiast-self-selection audit on the full archive."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy.stats import spearmanr

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
EVENTS = DATA_DIR / "temporal_rated_events_full.parquet"
WEIGHTS = DATA_DIR / "soft_jury_weights.parquet"
EXACT = DATA_DIR / "overnight_uncertainty_full.json"
OUT_JSON = DATA_DIR / "temporal_trajectories.json"
OUT_REPORT = DATA_DIR / "TEMPORAL_TRAJECTORIES_REPORT.md"

DEFINITIONS = {
    "added_all": ("added_at", "added_at IS NOT NULL"),
    "added_no_bulk_users": (
        "added_at",
        "added_at IS NOT NULL AND (profile_events < 20 OR peak_day_share < 0.50)",
    ),
    "added_post_onboarding": (
        "added_at",
        "added_at IS NOT NULL AND added_day > first_day + 7 AND added_day <> peak_day",
    ),
    "updated_all": ("updated_at", "updated_at IS NOT NULL"),
    "read_available": ("read_at", "read_at IS NOT NULL"),
}
CENTRAL = "added_post_onboarding"


def trajectory_query(label, timestamp, condition):
    return f"""
        WITH usable AS (
            SELECT *, {timestamp} AS event_at
            FROM candidate_events
            WHERE ({condition}) AND (rating=5 OR rating<=3) AND jury_q > 0
        ), cutoffs AS (
            SELECT work_id,
                   quantile_cont(event_at, .20) AS q20,
                   quantile_cont(event_at, .80) AS q80
            FROM usable GROUP BY work_id
        ), marked AS (
            SELECT u.*,
                   u.event_at <= c.q20 AS early,
                   u.event_at >= c.q80 AS late
            FROM usable u JOIN cutoffs c USING (work_id)
        ), agg AS (
            SELECT work_id,
                sum(jury_q) FILTER (WHERE early) AS early_mass,
                sum(jury_q * jury_q) FILTER (WHERE early) AS early_mass2,
                sum(jury_q * (rating=5)::INTEGER) FILTER (WHERE early) /
                    nullif(sum(jury_q) FILTER (WHERE early), 0) AS early_p5,
                avg(jury_q) FILTER (WHERE early) AS early_mean_q,
                count(DISTINCT user_id) FILTER (WHERE early) AS early_users,
                sum(jury_q) FILTER (WHERE late) AS late_mass,
                sum(jury_q * jury_q) FILTER (WHERE late) AS late_mass2,
                sum(jury_q * (rating=5)::INTEGER) FILTER (WHERE late) /
                    nullif(sum(jury_q) FILTER (WHERE late), 0) AS late_p5,
                avg(jury_q) FILTER (WHERE late) AS late_mean_q,
                count(DISTINCT user_id) FILTER (WHERE late) AS late_users,
                min(event_at) AS first_event,
                max(event_at) AS last_event
            FROM marked GROUP BY work_id
        )
        SELECT work_id, early_mass, late_mass, early_p5, late_p5,
               late_p5-early_p5 AS delta_p5,
               early_mean_q, late_mean_q, late_mean_q-early_mean_q AS delta_mean_q,
               early_users, late_users,
               early_mass*early_mass/nullif(early_mass2,0) AS early_kish,
               late_mass*late_mass/nullif(late_mass2,0) AS late_kish,
               first_event, last_event
        FROM agg
        WHERE early_mass >= 10 AND late_mass >= 10
        ORDER BY work_id
    """


def rows_as_dicts(cursor):
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def compare_definitions(all_rows):
    central = {r["work_id"]: r for r in all_rows[CENTRAL]}
    out = {}
    for label, rows in all_rows.items():
        other = {r["work_id"]: r for r in rows}
        common = sorted(set(central) & set(other))
        a = np.asarray([central[x]["delta_p5"] for x in common], dtype=float)
        b = np.asarray([other[x]["delta_p5"] for x in common], dtype=float)
        out[label] = {
            "n_estimable": len(rows),
            "n_common_with_central": len(common),
            "delta_spearman": None if len(common) < 2 else float(spearmanr(a, b).statistic),
            "median_absolute_delta_difference": None if not len(common) else float(np.median(np.abs(a-b))),
            "sign_agreement": None if not len(common) else float(np.mean(np.sign(a) == np.sign(b))),
        }
    return out


def era_rankings(con):
    rows = rows_as_dicts(
        con.execute(
            """
            WITH paired AS (
                SELECT *, CASE
                    WHEN added_at >= epoch(TIMESTAMP '2011-01-01')
                     AND added_at < epoch(TIMESTAMP '2014-01-01') THEN '2011_2013'
                    WHEN added_at >= epoch(TIMESTAMP '2014-01-01')
                     AND added_at < epoch(TIMESTAMP '2016-01-01') THEN '2014_2015'
                    WHEN added_at >= epoch(TIMESTAMP '2016-01-01')
                     AND added_at < epoch(TIMESTAMP '2018-01-01') THEN '2016_2017'
                END AS era
                FROM candidate_events
                WHERE (rating=5 OR rating<=3) AND jury_q>0
                  AND added_day > first_day+7 AND added_day<>peak_day
            ), agg AS (
                SELECT era, work_id, sum(jury_q) AS mass,
                       sum(jury_q*(rating=5)::INTEGER)/sum(jury_q) AS p5
                FROM paired WHERE era IS NOT NULL GROUP BY era, work_id
            )
            SELECT era, work_id, mass, p5
            FROM agg WHERE mass>=20 ORDER BY era, p5 DESC, work_id
            """
        )
    )
    rankings = {}
    scores = {}
    for row in rows:
        rankings.setdefault(row["era"], []).append(row["work_id"])
        scores.setdefault(row["era"], {})[row["work_id"]] = row["p5"]
    comparisons = []
    eras = ("2011_2013", "2014_2015", "2016_2017")
    for left, right in zip(eras, eras[1:]):
        common = sorted(set(scores.get(left, {})) & set(scores.get(right, {})))
        rho = None
        if len(common) > 1:
            rho = float(
                spearmanr(
                    [scores[left][x] for x in common],
                    [scores[right][x] for x in common],
                ).statistic
            )
        comparisons.append(
            {
                "left": left,
                "right": right,
                "left_rankable": len(rankings.get(left, [])),
                "right_rankable": len(rankings.get(right, [])),
                "common": len(common),
                "score_spearman": rho,
                "jaccard50": jaccard(rankings.get(left, []), rankings.get(right, []), 50),
                "jaccard200": jaccard(rankings.get(left, []), rankings.get(right, []), 200),
                "rbo": rbo(rankings.get(left, []), rankings.get(right, [])),
            }
        )
    return rankings, comparisons


def write_report(result):
    p = result["user_profiles"]
    lines = [
        "# Temporal trajectories and enthusiast self-selection",
        "",
        "## Scope",
        "",
        "This audit uses full-dataset detailed timestamps for the exact-estimator candidate "
        "books, weighted by continuous jury-inclusion probability. The primary clock is "
        "`date_added`, excluding a user's first account week and their largest same-day import. "
        "Early and late estimates are the first and last temporal quintiles of 5★ versus ≤3★ "
        "events. They diagnose selection trajectories; they are not replacements for the "
        "community-equalized canon score.",
        "",
        f"- Broad users profiled: **{p['users']:,}**; rating events: **{p['events']:,}**.",
        f"- Users with ≥20 events whose largest day holds ≥50%: "
        f"**{100*p['bulk_user_rate']:.1f}%**; their share of soft jury mass: "
        f"**{100*p['bulk_mass_rate']:.1f}%**.",
        f"- Candidate user-work events after edition collapse: "
        f"**{result['meta']['candidate_user_work_events']:,}**.",
        "",
        "## Timestamp-definition sensitivity",
        "",
        "| definition | estimable | common | delta ρ | median |Δ difference| | sign agreement |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, row in result["definition_comparison"].items():
        rho = "—" if row["delta_spearman"] is None else f"{row['delta_spearman']:.3f}"
        mad = "—" if row["median_absolute_delta_difference"] is None else f"{row['median_absolute_delta_difference']:.3f}"
        sign = "—" if row["sign_agreement"] is None else f"{100*row['sign_agreement']:.1f}%"
        lines.append(
            f"| {label} | {row['n_estimable']} | {row['n_common_with_central']} | "
            f"{rho} | {mad} | {sign} |"
        )
    lines += [
        "",
        "## Calendar holdout stability",
        "",
        "| eras | rankable | common | score ρ | J@50 | J@200 | RBO |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["era_comparisons"]:
        lines.append(
            f"| {row['left']} → {row['right']} | {row['left_rankable']}→{row['right_rankable']} | "
            f"{row['common']} | {row['score_spearman']:.3f} | {row['jaccard50']:.3f} | "
            f"{row['jaccard200']:.3f} | {row['rbo']:.3f} |"
        )
    for heading, key in (
        ("Direction-consistent early-to-late declines in the exact top 200", "robust_declines"),
        ("Direction-consistent early-to-late rises in the exact top 200", "robust_rises"),
    ):
        lines += ["", f"## {heading}", "", "| book | exact rank | early p5 | late p5 | central change | path range | Δ jury-q |", "|---|---:|---:|---:|---:|---:|---:|"]
        for row in result[key][:20]:
            lines.append(
                f"| {row['title']} — {row['author']} | {row['exact_rank']} | "
                f"{row['early_p5']:.3f} | {row['late_p5']:.3f} | {row['delta_p5']:+.3f} | "
                f"{row['path_delta_min']:+.3f}–{row['path_delta_max']:+.3f} | "
                f"{row['delta_mean_q']:+.3f} |"
            )
    lines += [
        "",
        "## Decision",
        "",
        "Temporal data should now be retained as a diagnostic and book-level trajectory "
        "annotation, not folded directly into the canonical score. Bulk importing is common, "
        "and early/late direction is materially sensitive to which imperfect Goodreads clock "
        "is used. Direction-consistent paths can flag plausible enthusiast-first inflation or "
        "later broadening for further sensitivity analysis; inconsistent paths should increase "
        "uncertainty rather than move a book up or down.",
    ]
    lines += [
        "",
        "## Interpretation limits",
        "",
        "- Goodreads timestamps identify recording chronology, not exposure or the original "
        "moment a rating was formed.",
        "- Calendar eras mix audience change with platform growth and cohort replacement.",
        "- `read_at` is user-entered and missing nonrandomly; agreement across timestamp paths "
        "is stronger evidence than any one path.",
        "- A decline bounds plausible enthusiast-first inflation but does not prove that absent "
        "readers would dislike the book.",
        "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    t0 = time.time()
    exact = json.loads(EXACT.read_text(encoding="utf-8"))
    candidates = {row["work_id"]: row for row in exact["books"]}
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("CREATE TEMP TABLE candidates(work_id VARCHAR PRIMARY KEY)")
    con.executemany("INSERT INTO candidates VALUES (?)", [(x,) for x in candidates])
    print("Profiling broad users and import bursts…", flush=True)
    con.execute(
        f"""
        CREATE TEMP TABLE broad_events AS
        SELECT e.*, w.jury_q, w.hard_jury,
               CASE WHEN e.added_at >= epoch(TIMESTAMP '2006-01-01')
                          AND e.added_at < epoch(TIMESTAMP '2018-01-01')
                    THEN floor(e.added_at/86400)::INTEGER END AS added_day
        FROM read_parquet('{EVENTS}') e
        JOIN read_parquet('{WEIGHTS}') w USING (user_id)
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE user_days AS
        SELECT user_id, added_day, count(*)::INTEGER AS n
        FROM broad_events WHERE added_day IS NOT NULL GROUP BY 1,2
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE profiles AS
        WITH totals AS (
            SELECT b.user_id, count(*)::INTEGER AS profile_events,
                   min(b.added_day)::INTEGER AS first_day,
                   max(b.added_day)::INTEGER AS last_day,
                   any_value(b.jury_q) AS jury_q
            FROM broad_events b GROUP BY b.user_id
        ), peaks AS (
            SELECT user_id, added_day AS peak_day, n AS peak_n,
                   row_number() OVER (PARTITION BY user_id ORDER BY n DESC, added_day) AS rn
            FROM user_days
        )
        SELECT t.*, p.peak_day, p.peak_n,
               p.peak_n::DOUBLE/t.profile_events AS peak_day_share
        FROM totals t JOIN peaks p USING (user_id) WHERE p.rn=1
        """
    )
    profile_row = con.execute(
        """
        SELECT count(*), sum(profile_events),
               avg((profile_events>=20 AND peak_day_share>=.5)::INTEGER),
               sum(jury_q*(profile_events>=20 AND peak_day_share>=.5)::INTEGER)/sum(jury_q)
        FROM profiles
        """
    ).fetchone()
    print("Collapsing candidate editions to user-work events…", flush=True)
    con.execute(
        """
        CREATE TEMP TABLE candidate_events AS
        SELECT b.user_id, b.work_id, max(b.rating)::UTINYINT AS rating,
               min(b.added_at) FILTER (WHERE b.added_day IS NOT NULL)::BIGINT AS added_at,
               max(b.updated_at) FILTER (
                   WHERE b.updated_at >= epoch(TIMESTAMP '2006-01-01')
                     AND b.updated_at < epoch(TIMESTAMP '2018-01-01')
               )::BIGINT AS updated_at,
               min(b.read_at) FILTER (
                   WHERE b.read_at >= epoch(TIMESTAMP '1800-01-01')
                     AND b.read_at < epoch(TIMESTAMP '2018-01-01')
               )::BIGINT AS read_at,
               min(b.started_at) FILTER (
                   WHERE b.started_at >= epoch(TIMESTAMP '1800-01-01')
                     AND b.started_at < epoch(TIMESTAMP '2018-01-01')
               )::BIGINT AS started_at,
               min(b.added_day)::INTEGER AS added_day,
               any_value(b.jury_q) AS jury_q,
               any_value(b.hard_jury) AS hard_jury,
               any_value(p.profile_events) AS profile_events,
               any_value(p.first_day) AS first_day,
               any_value(p.peak_day) AS peak_day,
               any_value(p.peak_day_share) AS peak_day_share
        FROM broad_events b JOIN candidates c USING (work_id)
        JOIN profiles p USING (user_id)
        GROUP BY b.user_id, b.work_id
        """
    )
    candidate_n = con.execute("SELECT count(*) FROM candidate_events").fetchone()[0]
    all_rows = {}
    for label, (timestamp, condition) in DEFINITIONS.items():
        print(f"Trajectory path {label}…", flush=True)
        all_rows[label] = rows_as_dicts(
            con.execute(trajectory_query(label, timestamp, condition))
        )
    definition_comparison = compare_definitions(all_rows)
    rankings, era_comparisons = era_rankings(con)
    central_all = []
    for row in all_rows[CENTRAL]:
        book = candidates[row["work_id"]]
        central_all.append(
            {
                **row,
                "title": book["title"],
                "author": book["author"],
                "exact_rank": book["exact_rank"],
                "exact_score": book["exact_score"],
            }
        )
    central_rows = [
        row for row in central_all
        if row["exact_rank"] is not None and row["exact_rank"] <= 200
    ]
    activity_labels = [label for label in DEFINITIONS if label != "read_available"]
    activity_maps = {
        label: {r["work_id"]: r for r in all_rows[label]}
        for label in activity_labels
    }
    robust_ids = set.intersection(*[set(x) for x in activity_maps.values()])
    declines, rises = [], []
    all_declines, all_rises = [], []
    for row in central_all:
        work_id = row["work_id"]
        if work_id not in robust_ids:
            continue
        deltas = [activity_maps[label][work_id]["delta_p5"] for label in activity_labels]
        enriched = {
            **row,
            "path_delta_min": float(min(deltas)),
            "path_delta_max": float(max(deltas)),
        }
        if all(delta < 0 for delta in deltas):
            all_declines.append(enriched)
        elif all(delta > 0 for delta in deltas):
            all_rises.append(enriched)
    declines = [
        row for row in all_declines
        if row["exact_rank"] is not None and row["exact_rank"] <= 200
    ]
    rises = [
        row for row in all_rises
        if row["exact_rank"] is not None and row["exact_rank"] <= 200
    ]
    declines.sort(key=lambda r: r["delta_p5"])
    rises.sort(key=lambda r: -r["delta_p5"])
    result = {
        "meta": {
            "purpose": "temporal trajectory and enthusiast-self-selection audit",
            "runtime_seconds": time.time() - t0,
            "candidate_books": len(candidates),
            "candidate_user_work_events": int(candidate_n),
            "central_definition": CENTRAL,
        },
        "user_profiles": {
            "users": int(profile_row[0]),
            "events": int(profile_row[1]),
            "bulk_user_rate": float(profile_row[2]),
            "bulk_mass_rate": float(profile_row[3]),
        },
        "definition_comparison": definition_comparison,
        "era_comparisons": era_comparisons,
        "era_top_work_ids": {k: v[:200] for k, v in rankings.items()},
        "central_trajectories": central_all,
        "central_top200_trajectories": central_rows,
        "all_direction_consistent_declines": all_declines,
        "all_direction_consistent_rises": all_rises,
        "robust_declines": declines,
        "robust_rises": rises,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(result)
    con.close()
    print(f"Wrote {OUT_REPORT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

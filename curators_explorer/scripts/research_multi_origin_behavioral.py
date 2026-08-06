#!/usr/bin/env python3
"""Behaviorally reconstruct disjoint seed-origin juries and compare held-out ranks.

This is the expensive second stage of the semantic seed audit.  Origin books
define teachers only.  Five-fold out-of-fold ridge models use the same generic
rating/author/series/year behavior panel as the current jury reconstruction;
book identities and list membership are not predictors.  The union of all
origin works remains excluded from all output rankings.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

import duckdb
import numpy as np

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard, rbo
from curators_explorer.scripts.research_jury_rebuild import (
    FEATURES,
    activity_bins,
    average_precision,
    materialize_behavior_features,
    materialize_model_frame,
    materialize_rich_behavior_features,
    ridge_oof,
    roc_auc,
)
from curators_explorer.scripts.research_multi_origin_seed_pilot import (
    origin_min_hits,
    origin_role,
)
from curators_explorer.scripts.research_ratings_only_canon import _con, materialize_base
from curators_explorer.scripts.research_threeway_unseeded import materialize_work_author_year


DATA = Path(__file__).resolve().parents[1] / "data"
PILOT = DATA / "multi_origin_seed_pilot.json"
CATALOG = DATA / "distributed_canon_catalog.json"
FEATURE_CACHE = DATA / "multi_origin_behavior_features.npz"
OUT_JSON = DATA / "multi_origin_behavioral_full.json"
OUT_REPORT = DATA / "MULTI_ORIGIN_BEHAVIORAL_FULL_REPORT.md"
QUICK_JSON = DATA / "multi_origin_behavioral_quick.json"
QUICK_REPORT = DATA / "MULTI_ORIGIN_BEHAVIORAL_QUICK_REPORT.md"

TEACHER_N = 2_000
JURY_N = 3_000
MIN_BOOK_MASS = 10.0
LOWER_Z = 1.2815515655446004

QUICK_ORIGINS = (
    "greatestbooks_head",
    "eastern_central",
    "contemporary_1980_2017",
    "historical_pre1900",
    "control_commercial_series",
)


def clean_array(a) -> np.ndarray:
    if np.ma.isMaskedArray(a):
        a = a.filled(np.nan)
    return np.asarray(a, dtype=np.float64)


def load_or_build_features(rebuild: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    if FEATURE_CACHE.exists() and not rebuild:
        t0 = time.time()
        with np.load(FEATURE_CACHE, allow_pickle=False) as saved:
            ids = saved["ids"].astype(np.int64)
            folds = saved["folds"].astype(np.int8)
            x = saved["x"].astype(np.float64)
        return ids, folds, x, {
            "source": FEATURE_CACHE.name,
            "users": len(ids),
            "features": x.shape[1],
            "load_seconds": time.time() - t0,
        }

    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    materialize_base(con)
    con.execute("CREATE OR REPLACE TEMP TABLE jury_teacher(user_id BIGINT, w DOUBLE)")
    materialize_work_author_year(con)
    behavior = materialize_behavior_features(con)
    rich = materialize_rich_behavior_features(con)
    frame = materialize_model_frame(con)
    columns = ", ".join(FEATURES)
    d = con.execute(
        f"SELECT user_id, (hash(user_id::VARCHAR)%5)::INTEGER AS fold, {columns} "
        "FROM jury_model_frame ORDER BY user_id"
    ).fetchnumpy()
    con.close()
    ids = np.asarray(d["user_id"], dtype=np.int64)
    folds = np.asarray(d["fold"], dtype=np.int8)
    x = np.column_stack([clean_array(d[name]) for name in FEATURES])
    np.savez_compressed(FEATURE_CACHE, ids=ids, folds=folds, x=x)
    return ids, folds, x, {
        "source": "rebuilt",
        "users": len(ids),
        "features": x.shape[1],
        "behavior": behavior,
        "rich": rich,
        "frame": frame,
        "build_seconds": time.time() - t0,
        "cache": FEATURE_CACHE.name,
    }


def origin_rows(payload: dict[str, Any], selected: tuple[str, ...] | None) -> dict[str, list[dict[str, Any]]]:
    origins = payload["origins"]
    if selected is None:
        return origins
    return {name: origins[name] for name in selected}


def direct_teachers(origins: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, list[int]], dict[str, Any]]:
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
        CREATE TEMP TABLE affinity AS
        SELECT o.origin,e.user_id,count(*)::INTEGER AS hits,
               count(*) FILTER (WHERE e.rating=5)::INTEGER AS fives,
               sum((CASE WHEN e.rating=5 THEN 1.0 ELSE 0.0 END)-e.five_rate)
                   / sqrt(count(*)) + 0.05*ln(1.0+count(*)) AS score
        FROM ex.all_rating_events e JOIN origin_works o USING(work_id)
        JOIN origin_requirements r USING(origin)
        WHERE e.rating>0
        GROUP BY o.origin,e.user_id
        HAVING count(*) >= max(r.min_hits)
        """
    )
    availability = {
        str(a): int(n)
        for a, n in con.execute("SELECT origin,count(*) FROM affinity GROUP BY origin").fetchall()
    }
    rows = con.execute(
        f"""
        SELECT origin,user_id FROM (
            SELECT *,row_number() OVER(
                PARTITION BY origin ORDER BY score DESC,hits DESC,user_id
            ) rn FROM affinity
        ) WHERE rn<={TEACHER_N}
        ORDER BY origin,rn
        """
    ).fetchall()
    con.close()
    teachers: dict[str, list[int]] = defaultdict(list)
    for origin, user_id in rows:
        teachers[str(origin)].append(int(user_id))
    selected = {name: len(teachers.get(name, [])) for name in origins}
    if min(selected.values(), default=0) < 200:
        raise RuntimeError(f"Origin teacher coverage too small: {availability}")
    return dict(teachers), {"available": availability, "selected": selected}


def fit_juries(
    ids: np.ndarray,
    folds: np.ndarray,
    x: np.ndarray,
    teachers: dict[str, list[int]],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[int]]]:
    id_to_i = {int(user_id): i for i, user_id in enumerate(ids)}
    bins = activity_bins(x)
    diagnostics: dict[str, dict[str, Any]] = {}
    juries: dict[str, list[int]] = {}
    for origin, teacher_ids in teachers.items():
        y = np.zeros(len(ids), dtype=np.int8)
        for user_id in teacher_ids:
            i = id_to_i.get(user_id)
            if i is not None:
                y[i] = 1
        teacher_w = y.astype(np.float64)
        t0 = time.time()
        score, coefficients = ridge_oof(
            x, y, teacher_w, folds, bins, FEATURES, matched=False
        )
        order = np.lexsort((ids, -score))
        selected = ids[order[:JURY_N]].astype(np.int64).tolist()
        selected_set = set(selected)
        teacher_set = set(teacher_ids)
        overlap = len(selected_set & teacher_set)
        diagnostics[origin] = {
            "teacher_covered": int(y.sum()),
            "roc_auc": roc_auc(y, score),
            "average_precision": average_precision(y, score),
            "teacher_jury_overlap": overlap,
            "teacher_jury_jaccard": overlap / max(1, len(selected_set | teacher_set)),
            "score_q99": float(np.quantile(score, 0.99)),
            "top_coefficients": sorted(
                coefficients.items(), key=lambda item: abs(item[1]), reverse=True
            )[:15],
            "fit_seconds": time.time() - t0,
        }
        juries[origin] = selected
        print(
            f"{origin}: AUC={diagnostics[origin]['roc_auc']:.3f} "
            f"AP={diagnostics[origin]['average_precision']:.3f} "
            f"teacher/jury J={diagnostics[origin]['teacher_jury_jaccard']:.3f}",
            flush=True,
        )
    return diagnostics, juries


def rank_juries(
    juries: dict[str, list[int]], excluded_ids: set[str]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    catalog_payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    candidates = [row for row in catalog_payload["books"] if row["work_id"] not in excluded_ids]
    meta = {row["work_id"]: row for row in candidates}
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("CREATE TEMP TABLE juries(origin VARCHAR,user_id BIGINT)")
    con.executemany(
        "INSERT INTO juries VALUES (?,?)",
        [(origin, user_id) for origin, users in juries.items() for user_id in users],
    )
    con.execute("CREATE TEMP TABLE candidates(work_id VARCHAR PRIMARY KEY)")
    con.executemany("INSERT INTO candidates VALUES (?)", [(row["work_id"],) for row in candidates])
    con.execute(
        """
        CREATE TEMP TABLE balances AS
        SELECT j.origin,e.user_id,
               count(*) FILTER(WHERE e.rating=5)::DOUBLE n_high,
               count(*) FILTER(WHERE e.rating BETWEEN 1 AND 3)::DOUBLE n_low,
               least(count(*) FILTER(WHERE e.rating=5),
                     count(*) FILTER(WHERE e.rating BETWEEN 1 AND 3),12)::DOUBLE n_side
        FROM juries j JOIN ex.all_rating_events e USING(user_id)
        JOIN candidates c USING(work_id)
        WHERE e.rating=5 OR e.rating BETWEEN 1 AND 3
        GROUP BY j.origin,e.user_id
        """
    )
    rows = con.execute(
        """
        SELECT j.origin,e.work_id,
               sum(CASE WHEN e.rating=5 AND b.n_high>0 THEN b.n_side/b.n_high ELSE 0 END) wins,
               sum(CASE WHEN e.rating BETWEEN 1 AND 3 AND b.n_low>0 THEN b.n_side/b.n_low ELSE 0 END) losses,
               count(DISTINCT e.user_id) raters
        FROM juries j JOIN balances b USING(origin,user_id)
        JOIN ex.all_rating_events e USING(user_id)
        JOIN candidates c USING(work_id)
        WHERE e.rating=5 OR e.rating BETWEEN 1 AND 3
        GROUP BY j.origin,e.work_id
        """
    ).fetchall()
    con.close()
    by_origin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for origin, work_id, wins, losses, raters in rows:
        wins, losses = float(wins or 0), float(losses or 0)
        mass = wins + losses
        if mass < MIN_BOOK_MASS:
            continue
        p = (wins + 0.5) / (mass + 1.0)
        u = math.sqrt(p * (1.0 - p) / (mass + 2.0))
        work = meta[str(work_id)]
        by_origin[str(origin)].append(
            {
                "work_id": str(work_id), "title": work["title"], "author": work["author"],
                "score": 100*(p-LOWER_Z*u), "esteem": 100*p, "u": 100*u,
                "pair_mass": mass, "raters": int(raters),
                "current_consensus_rank": work["consensus_rank"],
            }
        )
    for origin, rows_ in by_origin.items():
        rows_.sort(key=lambda row: (-row["score"], row["work_id"]))
        for rank, row in enumerate(rows_, 1):
            row["rank"] = rank
    return dict(by_origin), {"candidate_books": len(candidates)}


def compare(
    origins: dict[str, list[dict[str, Any]]],
    juries: dict[str, list[int]],
    rankings: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    names = list(origins)
    literary = [name for name in names if origin_role(name) == "literary"]
    controls = [name for name in names if origin_role(name) == "control"]
    borders = [name for name in names if origin_role(name) == "border"]
    rank_ids = {name: [row["work_id"] for row in rankings.get(name, [])] for name in names}
    jury_sets = {name: set(juries[name]) for name in names}
    pairwise = []
    for a, b in combinations(names, 2):
        kind = (
            "literary-literary" if a in literary and b in literary else
            "control-control" if a in controls and b in controls else
            "literary-control" if ((a in literary and b in controls) or
                                    (b in literary and a in controls)) else
            "literary-border" if (a in literary or b in literary) else
            "border-control"
        )
        pairwise.append(
            {
                "a": a, "b": b, "kind": kind,
                "jury_jaccard": len(jury_sets[a] & jury_sets[b]) / max(1, len(jury_sets[a] | jury_sets[b])),
                "book_jaccard50": jaccard(rank_ids[a], rank_ids[b], 50),
                "book_jaccard200": jaccard(rank_ids[a], rank_ids[b], 200),
                "book_rbo": rbo(rank_ids[a], rank_ids[b]),
            }
        )
    frequency = Counter(work_id for name in literary for work_id in rank_ids[name][:200])
    row_by_id = {
        row["work_id"]: row for name in literary for row in rankings.get(name, [])
    }
    threshold = math.ceil(0.75*len(literary))
    stable = [work_id for work_id, count in frequency.items() if count >= threshold]
    stable.sort(key=lambda work_id: (-frequency[work_id], row_by_id[work_id]["current_consensus_rank"]))
    return {
        "pairwise": pairwise,
        "literary_origins": literary,
        "control_origins": controls,
        "border_origins": borders,
        "stable_threshold": threshold,
        "stable_literary_top200": [
            {
                "work_id": work_id,
                "title": row_by_id[work_id]["title"],
                "author": row_by_id[work_id]["author"],
                "origin_top200_count": frequency[work_id],
                "current_consensus_rank": row_by_id[work_id]["current_consensus_rank"],
            }
            for work_id in stable
        ],
    }


def group_mean(pairwise: list[dict[str, Any]], kind: str, key: str) -> float:
    values = [row[key] for row in pairwise if row["kind"] == kind]
    return float(np.mean(values)) if values else float("nan")


def write_report(result: dict[str, Any], path: Path) -> None:
    comparison = result["comparison"]
    pairs = comparison["pairwise"]
    literary_n = len(comparison["literary_origins"])
    lines = [
        f"# Multi-origin behavioral seed audit ({result['method']['mode']})", "",
        "## Design", "",
        f"Each disjoint origin selects up to {TEACHER_N:,} direct-affinity teachers. A five-fold "
        f"out-of-fold model reconstructs them from the current {len(FEATURES)} generic behavior "
        f"features, then selects a {JURY_N:,}-reader jury. No book identity or list membership is "
        "a predictor. The union of all origin works is excluded from every ranked universe.", "",
        "This stage uses the same balanced 5-star-versus-low ranker for every reconstructed jury. "
        "It isolates seed-origin dependence before the much more expensive community refit.", "",
        "## Reconstruction", "",
        "| Origin | Role | Works | min hits | teachers | AUC | AP | teacher/jury J | fit seconds | rankable books |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in result["origins"]:
        d = result["diagnostics"][name]
        lines.append(
            f"| {name} | {origin_role(name)} | {result['origin_details'][name]['works']} | "
            f"{result['origin_details'][name]['min_hits']} | "
            f"{result['teacher']['selected'].get(name,0):,} | "
            f"{d['roc_auc']:.3f} | {d['average_precision']:.3f} | "
            f"{d['teacher_jury_jaccard']:.3f} | {d['fit_seconds']:.1f} | "
            f"{len(result['rankings'].get(name, [])):,} |"
        )
    lines += [
        "", "## Convergence", "",
        f"- Literary↔literary mean reconstructed-jury Jaccard: **"
        f"{group_mean(pairs,'literary-literary','jury_jaccard'):.3f}**; book Jaccard@50/200 "
        f"**{group_mean(pairs,'literary-literary','book_jaccard50'):.3f}/"
        f"{group_mean(pairs,'literary-literary','book_jaccard200'):.3f}**.",
        f"- Literary↔control mean reconstructed-jury Jaccard: **"
        f"{group_mean(pairs,'literary-control','jury_jaccard'):.3f}**; book Jaccard@50/200 "
        f"**{group_mean(pairs,'literary-control','book_jaccard50'):.3f}/"
        f"{group_mean(pairs,'literary-control','book_jaccard200'):.3f}**.",
        f"- Literary↔children's-border mean reconstructed-jury Jaccard: **"
        f"{group_mean(pairs,'literary-border','jury_jaccard'):.3f}**; book Jaccard@50/200 "
        f"**{group_mean(pairs,'literary-border','book_jaccard50'):.3f}/"
        f"{group_mean(pairs,'literary-border','book_jaccard200'):.3f}**.",
        f"- Held-out books present in at least {comparison['stable_threshold']}/{literary_n} "
        f"literary top 200s: **{len(comparison['stable_literary_top200'])}**.", "",
        "## Shared held-out head", "",
        "| Book | literary top-200s | current consensus rank |", "|---|---:|---:|",
    ]
    for row in comparison["stable_literary_top200"][:75]:
        lines.append(
            f"| *{row['title']}* — {row['author']} | {row['origin_top200_count']}/{literary_n} | "
            f"{row['current_consensus_rank']} |"
        )
    lines += ["", "## Origin heads", ""]
    for name in result["origins"]:
        lines += [f"### {name}", ""]
        for row in result["rankings"].get(name, [])[:15]:
            lines.append(
                f"{row['rank']}. *{row['title']}* — {row['author']} "
                f"({row['score']:.1f} +/-{row['u']:.1f}, mass {row['pair_mass']:.1f})"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--rebuild-features", action="store_true")
    args = parser.parse_args()
    t0 = time.time()
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    origins = origin_rows(pilot, QUICK_ORIGINS if args.quick else None)
    excluded_ids = {
        row["work_id"] for rows in pilot["origins"].values() for row in rows
    }
    ids, folds, x, feature_meta = load_or_build_features(args.rebuild_features)
    teachers, teacher_meta = direct_teachers(origins)
    diagnostics, juries = fit_juries(ids, folds, x, teachers)
    rankings, ranking_meta = rank_juries(juries, excluded_ids)
    comparison = compare(origins, juries, rankings)
    result = {
        "method": {
            "purpose": "behaviorally reconstructed semantic seed-origin audit",
            "mode": "quick" if args.quick else "full",
            "teacher_n": TEACHER_N,
            "jury_n": JURY_N,
            "features": FEATURES,
            "five_fold_out_of_fold": True,
            "all_origin_works_excluded_from_all_rankings": True,
            "runtime_seconds": time.time()-t0,
        },
        "feature_cache": feature_meta,
        "teacher": teacher_meta,
        "origins": list(origins),
        "origin_details": {
            name: {
                "role": origin_role(name),
                "works": len(rows),
                "min_hits": origin_min_hits(rows),
            }
            for name, rows in origins.items()
        },
        "diagnostics": diagnostics,
        "jury_user_ids": juries,
        "ranking_meta": ranking_meta,
        "rankings": {name: rows[:300] for name, rows in rankings.items()},
        "comparison": comparison,
    }
    out_json, out_report = (QUICK_JSON, QUICK_REPORT) if args.quick else (OUT_JSON, OUT_REPORT)
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    write_report(result, out_report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_report}")


if __name__ == "__main__":
    main()

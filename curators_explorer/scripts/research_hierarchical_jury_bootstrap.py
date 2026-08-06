#!/usr/bin/env python3
"""Propagate teacher-composition jury refits through the hierarchical scorer."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy import sparse

from curators_explorer.scripts.research_consensus_stability_pilot import (
    JURY_N,
    jaccard,
    materialize_pilot_users,
    reconstruct_jury,
)
from curators_explorer.scripts.research_hierarchical_read_selection import (
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
    combine,
)
from curators_explorer.scripts.research_jury_rebuild import (
    activity_bins,
    fetch_frame,
)
from curators_explorer.scripts.research_overnight_jury_bootstrap import (
    BOOT_SEED,
    ridge_oof_teacher_bootstrap,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ASSIGNMENTS = DATA_DIR / "jury_fuzzy_community_assignments.parquet"
HARD_ASSIGNMENTS = DATA_DIR / "jury_community_assignments.parquet"
CANDIDATES = DATA_DIR / "overnight_uncertainty_full.json"
LEGACY_CHECKPOINT = DATA_DIR / "overnight_jury_bootstrap_full_checkpoint.npz"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--reps", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.reps is None:
        args.reps = 2 if args.mode == "quick" else 100
    return args


def paths(mode):
    stem = f"hierarchical_jury_bootstrap_{mode}"
    return {
        "checkpoint": DATA_DIR / f"{stem}_checkpoint.npz",
        "json": DATA_DIR / f"{stem}.json",
        "report": DATA_DIR / f"{stem.upper()}_REPORT.md",
    }


def matrix_from_arrays(values, n_users, n_works, k):
    return sparse.coo_matrix(
        (
            values["value"].astype(np.float32),
            (values["user_idx"].astype(np.int32), values["cell"].astype(np.int64)),
        ),
        shape=(n_users, n_works * k),
    ).tocsr()


def query_matrix(con, label_sql, weight_sql, event_sql, k, n_users, n_works):
    values = con.execute(
        f"""
        SELECT user_idx, work_idx * {k} + ({label_sql}) AS cell,
               ({weight_sql}) * ({event_sql}) AS value
        FROM pair_events
        WHERE ({event_sql}) > 0 AND ({weight_sql}) > 0
        """
    ).fetchnumpy()
    return matrix_from_arrays(values, n_users, n_works, k)


def build_blocks(broad_ids, candidate):
    from curators_explorer.db import DB_PATH

    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("CREATE TEMP TABLE broad_order(user_id BIGINT, user_idx INTEGER)")
    con.executemany(
        "INSERT INTO broad_order VALUES (?, ?)",
        [(int(uid), i) for i, uid in enumerate(broad_ids)],
    )
    con.execute("CREATE TEMP TABLE candidates(work_idx INTEGER, work_id VARCHAR)")
    con.executemany(
        "INSERT INTO candidates VALUES (?, ?)",
        [(i, row["work_id"]) for i, row in enumerate(candidate)],
    )
    con.execute(
        f"""
        CREATE TEMP TABLE assignments AS
        SELECT b.user_idx, a.*, {', '.join(f'h.{label}' for label, _k in PARTITIONS)}
        FROM broad_order b
        JOIN read_parquet('{ASSIGNMENTS}') a USING (user_id)
        JOIN read_parquet('{HARD_ASSIGNMENTS}') h USING (user_id)
        """
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
    fuzzy_columns = ", ".join(
        f"a.{label}_a, a.{label}_wa, a.{label}_b, a.{label}_wb"
        for label, _k in PARTITIONS
    )
    hard_columns = ", ".join(f"a.{label}" for label, _k in PARTITIONS)
    con.execute(
        f"""
        CREATE TEMP TABLE pair_events AS
        SELECT c.work_idx, a.user_idx, o.rating, {hard_columns}, {fuzzy_columns},
               coalesce(b.n_high,0) AS n_high,
               coalesce(b.n_low,0) AS n_low, coalesce(b.n_side,0) AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN candidates c USING (work_id)
        JOIN assignments a USING (user_id)
        LEFT JOIN user_balance b USING (user_id)
        WHERE o.rating=5 OR o.rating BETWEEN 1 AND 3
        """
    )
    win_sql = "CASE WHEN rating=5 AND n_high>0 THEN n_side/n_high ELSE 0 END"
    loss_sql = "CASE WHEN rating BETWEEN 1 AND 3 AND n_low>0 THEN n_side/n_low ELSE 0 END"
    variants = {"hard": [], "fuzzy90": []}
    for label, k in PARTITIONS:
        print(f"Building jury blocks {label}…", flush=True)
        hard = {
            "label": label, "k": k,
            "positive": query_matrix(
                con, label, "1.0", win_sql, k, len(broad_ids), len(candidate)
            ),
            "negative": query_matrix(
                con, label, "1.0", loss_sql, k, len(broad_ids), len(candidate)
            ),
        }
        # A and B memberships are separate sparse contributions into the same cells.
        fuzzy = {"label": label, "k": k}
        for outcome, event_sql in (("positive", win_sql), ("negative", loss_sql)):
            left = query_matrix(
                con, f"{label}_a", f"{label}_wa", event_sql,
                k, len(broad_ids), len(candidate),
            )
            right = query_matrix(
                con, f"{label}_b", f"{label}_wb", event_sql,
                k, len(broad_ids), len(candidate),
            )
            fuzzy[outcome] = left + right
        variants["hard"].append(hard)
        variants["fuzzy90"].append(fuzzy)
    q_rows = con.execute("SELECT user_idx, jury_q FROM assignments ORDER BY user_idx").fetchall()
    q = np.asarray([float(row[1]) for row in q_rows], dtype=np.float64)
    con.close()
    return q, variants


def fit(blocks, weights, n_works):
    parts = []
    for block in blocks:
        k = block["k"]
        parts.append(
            {
                "label": block["label"], "k": k,
                "wins": np.asarray(weights @ block["positive"]).reshape(n_works, k),
                "losses": np.asarray(weights @ block["negative"]).reshape(n_works, k),
            }
        )
    return combine(
        parts, prior_strength=8.0, book_prior_strength=50.0,
        book_evidence_cap=math.inf, min_mass=10.0, evidence_z=1.0,
        gamma=1.0, all_low=False,
    )


def save_checkpoint(path, work_ids, arrays, jury_jaccard, packed, completed):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            candidate_work_ids=np.asarray(work_ids), completed=np.asarray(completed),
            jury_jaccard=jury_jaccard[:completed], selected_packed=packed[:completed],
            hard_scores=arrays["hard"][0][:completed],
            hard_ranks=arrays["hard"][1][:completed],
            fuzzy_scores=arrays["fuzzy90"][0][:completed],
            fuzzy_ranks=arrays["fuzzy90"][1][:completed],
        )
    temporary.replace(path)


def allocate(reps, n_works, n_users):
    arrays = {
        label: (
            np.full((reps, n_works), np.nan, dtype=np.float32),
            np.zeros((reps, n_works), dtype=np.uint16),
        )
        for label in ("hard", "fuzzy90")
    }
    return (
        arrays, np.full(reps, np.nan, dtype=np.float32),
        np.zeros((reps, math.ceil(n_users / 8)), dtype=np.uint8), 0,
    )


def load_checkpoint(path, work_ids, reps, n_users):
    arrays, jury_jaccard, packed, completed = allocate(reps, len(work_ids), n_users)
    if not path.exists():
        return arrays, jury_jaccard, packed, completed
    with np.load(path, allow_pickle=False) as saved:
        if saved["candidate_work_ids"].astype(str).tolist() != work_ids:
            raise RuntimeError("checkpoint candidate universe differs")
        completed = min(int(saved["completed"]), reps)
        jury_jaccard[:completed] = saved["jury_jaccard"][:completed]
        packed[:completed] = saved["selected_packed"][:completed]
        arrays["hard"][0][:completed] = saved["hard_scores"][:completed]
        arrays["hard"][1][:completed] = saved["hard_ranks"][:completed]
        arrays["fuzzy90"][0][:completed] = saved["fuzzy_scores"][:completed]
        arrays["fuzzy90"][1][:completed] = saved["fuzzy_ranks"][:completed]
    return arrays, jury_jaccard, packed, completed


def summarize(label, point, scores, ranks, candidate, completed):
    point_ranking = point["ranking"].tolist()
    j50, j200 = [], []
    for draw in ranks[:completed]:
        order = np.flatnonzero(draw > 0)
        order = order[np.argsort(draw[order], kind="stable")]
        j50.append(jaccard(point_ranking, order.tolist(), 50))
        j200.append(jaccard(point_ranking, order.tolist(), 200))
    books = []
    for rank, i in enumerate(point_ranking[:200], start=1):
        values = scores[:completed, i]
        finite = np.isfinite(values)
        values = values[finite]
        draw_ranks = ranks[:completed, i]
        draw_ranks = draw_ranks[draw_ranks > 0]
        books.append(
            {
                "rank": rank, "work_id": candidate[i]["work_id"],
                "title": candidate[i]["title"], "author": candidate[i]["author"],
                "score": float(100 * point["score"][i]),
                "jury_u80": float((np.quantile(values,.9)-np.quantile(values,.1))/2),
                "eligible_rate": float(finite.mean()),
                "top200_rate": float(
                    np.mean((ranks[:completed, i] > 0) & (ranks[:completed, i] <= 200))
                ),
                "rank_q10": float(np.quantile(draw_ranks, .1)),
                "rank_q90": float(np.quantile(draw_ranks, .9)),
            }
        )
    return {
        "label": label, "point_rankable": int(point["estimable"].sum()),
        "jaccard50_mean": float(np.mean(j50)), "jaccard50_q10": float(np.quantile(j50,.1)),
        "jaccard200_mean": float(np.mean(j200)), "jaccard200_q10": float(np.quantile(j200,.1)),
        "median_top200_jury_u80": float(np.median([row["jury_u80"] for row in books])),
        "median_top200_eligibility": float(np.median([row["eligible_rate"] for row in books])),
        "books": books,
    }


def main():
    args = parse_args()
    output = paths(args.mode)
    t0 = time.time()
    candidate_payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidate = sorted(candidate_payload["books"], key=lambda row: int(row["work_idx"]))
    work_ids = [row["work_id"] for row in candidate]

    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, baseline_scores, broad = reconstruct_jury(con)
    ids, folds, y, teacher_w, x = fetch_frame(con)
    bins = activity_bins(x)
    broad_ids, baseline_mask, _ = materialize_pilot_users(
        con, all_ids, baseline_scores, broad
    )
    con.close()
    broad_frame_idx = np.searchsorted(ids, broad_ids)
    if not np.array_equal(ids[broad_frame_idx], broad_ids):
        raise RuntimeError("could not map broad users into feature frame")
    q, blocks = build_blocks(broad_ids, candidate)
    points = {label: fit(part, q, len(candidate)) for label, part in blocks.items()}
    baseline_set = set(np.flatnonzero(baseline_mask).tolist())

    if args.resume:
        arrays, jury_jaccard, packed, completed = load_checkpoint(
            output["checkpoint"], work_ids, args.reps, len(broad_ids)
        )
    else:
        arrays, jury_jaccard, packed, completed = allocate(
            args.reps, len(candidate), len(broad_ids)
        )
    with np.load(LEGACY_CHECKPOINT, allow_pickle=False) as saved:
        legacy_jaccard = saved["jury_jaccard"][:args.reps].astype(np.float64)
    positive_mask = y == 1
    start_time = time.time()
    while completed < args.reps:
        rng = np.random.default_rng(BOOT_SEED + completed)
        multiplier = np.ones(len(y), dtype=np.float64)
        multiplier[positive_mask] = rng.exponential(1.0, size=int(positive_mask.sum()))
        model_score, _coef = ridge_oof_teacher_bootstrap(
            x, y, teacher_w, folds, bins, multiplier
        )
        selected = np.argsort(-model_score[broad_frame_idx], kind="stable")[:JURY_N]
        jury_mask = np.zeros(len(broad_ids), dtype=np.float32)
        jury_mask[selected] = 1.0
        intersection = len(set(selected.tolist()) & baseline_set)
        jury_jaccard[completed] = intersection / (2 * JURY_N - intersection)
        packed[completed] = np.packbits(jury_mask.astype(bool))
        for label in ("hard", "fuzzy90"):
            draw = fit(blocks[label], jury_mask, len(candidate))
            eligible = draw["estimable"]
            arrays[label][0][completed, eligible] = 100 * draw["score"][eligible]
            arrays[label][1][completed, draw["ranking"]] = np.arange(
                1, len(draw["ranking"]) + 1, dtype=np.uint16
            )
        completed += 1
        if completed % 5 == 0 or completed == args.reps:
            save_checkpoint(
                output["checkpoint"], work_ids, arrays, jury_jaccard,
                packed, completed,
            )
            elapsed = time.time() - start_time
            print(
                f"  checkpoint {completed}/{args.reps}: {elapsed/completed:.2f}s/rep, "
                f"jury J={np.median(jury_jaccard[:completed]):.3f}", flush=True,
            )
    legacy_error = float(np.max(np.abs(jury_jaccard[:completed] - legacy_jaccard[:completed])))
    if legacy_error > 1e-6:
        raise RuntimeError(f"jury refits do not reproduce legacy campaign: {legacy_error}")
    summaries = [
        summarize(label, points[label], *arrays[label], candidate, completed)
        for label in ("hard", "fuzzy90")
    ]
    result = {
        "meta": {
            "purpose": "teacher-composition jury refits propagated through hierarchical scorer",
            "mode": args.mode, "completed_replicates": completed,
            "candidate_books": len(candidate), "runtime_seconds": time.time()-t0,
            "bootstrap_seconds": time.time()-start_time,
            "legacy_jaccard_max_abs_error": legacy_error,
        },
        "jury_reconstruction": jury_meta,
        "jury_jaccard": {
            "q10": float(np.quantile(jury_jaccard[:completed],.1)),
            "median": float(np.median(jury_jaccard[:completed])),
            "q90": float(np.quantile(jury_jaccard[:completed],.9)),
        },
        "variants": summaries,
    }
    output["json"].write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hierarchical jury-definition bootstrap", "", "## Result", "",
        "Each draw Bayesian-bootstraps the positive teacher cohort, refits the five-fold "
        "behavioral jury model, selects a 4,929-person jury, and reruns the hierarchical "
        "book estimator through hard and conservative fuzzy90 communities.", "",
        f"- Replicates: **{completed}**; refit time: **{result['meta']['bootstrap_seconds']:.1f}s**.",
        f"- Jury Jaccard q10/median/q90: **{result['jury_jaccard']['q10']:.3f} / "
        f"{result['jury_jaccard']['median']:.3f} / {result['jury_jaccard']['q90']:.3f}**.",
        "", "| communities | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 | median jury u80 | median eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['label']} | {row['jaccard50_mean']:.3f} | {row['jaccard50_q10']:.3f} | "
            f"{row['jaccard200_mean']:.3f} | {row['jaccard200_q10']:.3f} | "
            f"{row['median_top200_jury_u80']:.2f} | {100*row['median_top200_eligibility']:.0f}% |"
        )
    lines += ["", "## Hard-community point head", "",
              "| # | book | score | jury u80 | top200 | jury-rank q10–q90 |",
              "|---:|---|---:|---:|---:|---:|"]
    for row in summaries[0]["books"][:40]:
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | {row['score']:.1f} | "
            f"{row['jury_u80']:.1f} | {100*row['top200_rate']:.0f}% | "
            f"{row['rank_q10']:.0f}–{row['rank_q90']:.0f} |"
        )
    lines += ["", "This isolates finite teacher-composition uncertainty. Reader resampling, "
              "teacher-definition alternatives, and missing-not-at-random Γ paths remain separate.", ""]
    output["report"].write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output['report']} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

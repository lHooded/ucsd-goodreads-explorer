#!/usr/bin/env python3
"""Reader-block bootstrap for the hierarchical community-pooling pilot."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy import sparse
from scipy.stats import spearmanr

from curators_explorer.db import DB_PATH
from curators_explorer.scripts.research_consensus_stability_pilot import jaccard
from curators_explorer.scripts.research_hierarchical_read_selection import (
    ASSIGNMENTS,
    MAX_CATALOG_N,
    OBSERVATIONS,
    PARTITIONS,
    combine,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CANDIDATES = DATA_DIR / "overnight_uncertainty_full.json"
POINT_JSON = DATA_DIR / "hierarchical_read_selection.json"
BOOT_SEED = 98_771


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--reps", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    if args.reps is None:
        args.reps = 64 if args.mode == "quick" else 2_000
    return args


def paths(mode):
    stem = f"hierarchical_reader_bootstrap_{mode}"
    return DATA_DIR / f"{stem}.json", DATA_DIR / f"{stem.upper()}_REPORT.md"


def matrix_from_query(con, value_sql, label, k, n_users, n_works):
    values = con.execute(
        f"""
        SELECT user_idx, work_idx * {k} + {label} AS cell, {value_sql} AS value
        FROM pair_events
        WHERE {value_sql} > 0
        """
    ).fetchnumpy()
    return sparse.coo_matrix(
        (
            values["value"].astype(np.float32),
            (values["user_idx"].astype(np.int32), values["cell"].astype(np.int64)),
        ),
        shape=(n_users, n_works * k),
    ).tocsr()


def build_blocks(works):
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=8")
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("CREATE TEMP TABLE candidates(work_idx INTEGER, work_id VARCHAR)")
    con.executemany(
        "INSERT INTO candidates VALUES (?, ?)",
        [(i, row["work_id"]) for i, row in enumerate(works)],
    )
    con.execute(
        f"""
        CREATE TEMP TABLE assignments AS
        SELECT row_number() OVER (ORDER BY user_id)-1 AS user_idx, *
        FROM read_parquet('{ASSIGNMENTS}') WHERE jury_q>0
        """
    )
    n_users = int(con.execute("SELECT count(*) FROM assignments").fetchone()[0])
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
    con.execute(
        f"""
        CREATE TEMP TABLE pair_events AS
        SELECT c.work_idx, a.*, o.rating,
               coalesce(b.n_high,0) AS n_high,
               coalesce(b.n_low,0) AS n_low,
               coalesce(b.n_side,0) AS n_side
        FROM read_parquet('{OBSERVATIONS}') o
        JOIN candidates c USING (work_id)
        JOIN assignments a USING (user_id)
        LEFT JOIN user_balance b USING (user_id)
        WHERE o.rating=5 OR o.rating BETWEEN 1 AND 3
        """
    )
    win_sql = "jury_q * CASE WHEN rating=5 AND n_high>0 THEN n_side/n_high ELSE 0 END"
    loss_sql = "jury_q * CASE WHEN rating BETWEEN 1 AND 3 AND n_low>0 THEN n_side/n_low ELSE 0 END"
    blocks = []
    for label, k in PARTITIONS:
        print(f"Building sparse block {label}…", flush=True)
        blocks.append(
            {
                "label": label,
                "k": k,
                "positive": matrix_from_query(
                    con, win_sql, label, k, n_users, len(works)
                ),
                "negative": matrix_from_query(
                    con, loss_sql, label, k, n_users, len(works)
                ),
            }
        )
    con.close()
    return n_users, blocks


def project(weights, block, n_works):
    k = block["k"]
    wins = np.asarray(weights @ block["positive"], dtype=np.float64).reshape(
        len(weights), n_works, k
    )
    losses = np.asarray(weights @ block["negative"], dtype=np.float64).reshape(
        len(weights), n_works, k
    )
    return wins, losses


def central_metric(parts):
    return combine(
        parts,
        prior_strength=8.0,
        book_prior_strength=50.0,
        book_evidence_cap=np.inf,
        min_mass=10.0,
        evidence_z=1.0,
        gamma=1.0,
        all_low=False,
    )


def rank_draws(blocks, n_users, n_works, reps, batch_size):
    scores = np.full((reps, n_works), np.nan, dtype=np.float32)
    ranks = np.zeros((reps, n_works), dtype=np.uint16)
    for start in range(0, reps, batch_size):
        count = min(batch_size, reps - start)
        weights = np.vstack(
            [
                np.random.default_rng(BOOT_SEED + draw).poisson(1.0, n_users)
                for draw in range(start, start + count)
            ]
        ).astype(np.float32)
        projected = [project(weights, block, n_works) for block in blocks]
        for offset in range(count):
            parts = [
                {
                    "label": block["label"],
                    "k": block["k"],
                    "wins": wins[offset],
                    "losses": losses[offset],
                }
                for block, (wins, losses) in zip(blocks, projected)
            ]
            metric = central_metric(parts)
            eligible = metric["estimable"]
            scores[start + offset, eligible] = 100 * metric["score"][eligible]
            ranks[start + offset, metric["ranking"]] = np.arange(
                1, len(metric["ranking"]) + 1, dtype=np.uint16
            )
        print(f"  completed {start + count}/{reps}", flush=True)
    return scores, ranks


def band_summary(rows, key, edges):
    result = []
    values = np.asarray([row[key] for row in rows], dtype=float)
    for low, high in zip(edges[:-1], edges[1:]):
        selected = [
            row for row, value in zip(rows, values) if value >= low and value < high
        ]
        if not selected:
            continue
        result.append(
            {
                "low": low,
                "high": None if np.isinf(high) else high,
                "n": len(selected),
                "median_u80": float(np.median([row["reader_u80"] for row in selected])),
                "median_top200_rate": float(
                    np.median([row["bootstrap_top200_rate"] for row in selected])
                ),
            }
        )
    return result


def write_report(result, path):
    meta, summary = result["meta"], result["summary"]
    lines = [
        "# Hierarchical reader-block bootstrap",
        "",
        "## Result",
        "",
        "Whole readers are Poisson-resampled while soft jury weights, community labels, and "
        "the learned jury definition remain fixed. Every draw refits book, community, and "
        "predictive-heterogeneity pooling terms before reranking.",
        "",
        f"- Mode: **{meta['mode']}**; replicates: **{meta['replicates']:,}**; "
        f"runtime: **{meta['runtime_seconds']:.1f}s**.",
        f"- Mean Jaccard@50: **{summary['jaccard50_mean']:.3f}** "
        f"(10th percentile {summary['jaccard50_q10']:.3f}).",
        f"- Mean Jaccard@200: **{summary['jaccard200_mean']:.3f}** "
        f"(10th percentile {summary['jaccard200_q10']:.3f}).",
        f"- Median top-200 reader `u80`: **{summary['median_top200_u80']:.2f}** points; "
        f"median bootstrap eligibility: **{100*summary['median_top200_eligibility']:.0f}%**.",
        f"- Top-200 reader uncertainty versus catalog popularity: Spearman "
        f"**{summary['top200_u80_catalog_spearman']:.3f}**; versus pair mass: "
        f"**{summary['top200_u80_pair_mass_spearman']:.3f}**.",
        "",
        "## Evidence trajectories within the point top 200",
        "",
        "| pair mass | books | median reader u80 | median top-200 inclusion |",
        "|---|---:|---:|---:|",
    ]
    for row in result["pair_mass_bands"]:
        high = "∞" if row["high"] is None else f"{row['high']:.0f}"
        lines.append(
            f"| {row['low']:.0f}–{high} | {row['n']} | {row['median_u80']:.2f} | "
            f"{100*row['median_top200_rate']:.0f}% |"
        )
    lines += [
        "",
        "## Point top 40",
        "",
        "| # | book | score | analytic u | reader u80 | eligibility | top-200 rate | rank q10–q90 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["books"][:40]:
        lines.append(
            f"| {row['rank']} | {row['title']} — {row['author']} | {row['score']:.1f} | "
            f"{row['analytic_u']:.1f} | {row['reader_u80']:.1f} | "
            f"{100*row['bootstrap_eligibility']:.0f}% | "
            f"{100*row['bootstrap_top200_rate']:.0f}% | "
            f"{row['rank_q10']:.0f}–{row['rank_q90']:.0f} |"
        )
    lines += [
        "",
        "`reader u80` is half the conditional 10th–90th percentile score interval. "
        "Eligibility and inclusion are reported separately so a narrow conditional interval "
        "cannot disguise unstable evidence. This bootstrap does not refit the jury definition.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    out_json, out_report = paths(args.mode)
    t0 = time.time()
    candidate = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    works = sorted(candidate["books"], key=lambda row: int(row["work_idx"]))
    point = json.loads(POINT_JSON.read_text(encoding="utf-8"))
    point_by_id = {row["work_id"]: row for row in point["books"]}
    n_users, blocks = build_blocks(works)

    # Validate that the sparse sufficient statistics reproduce the stored point fit.
    point_parts = []
    for block in blocks:
        k = block["k"]
        point_parts.append(
            {
                "label": block["label"],
                "k": k,
                "wins": np.asarray(block["positive"].sum(axis=0)).reshape(len(works), k),
                "losses": np.asarray(block["negative"].sum(axis=0)).reshape(len(works), k),
            }
        )
    reproduced = central_metric(point_parts)
    point_ranking = reproduced["ranking"].tolist()
    stored_score = np.asarray([point_by_id[row["work_id"]]["score"] for row in works])
    validation_error = float(
        np.max(np.abs(100 * reproduced["score"] - stored_score))
    )
    if validation_error > 1e-3:
        raise RuntimeError(f"point reproduction failed: max error {validation_error}")

    scores, ranks = rank_draws(
        blocks, n_users, len(works), args.reps, args.batch_size
    )
    point50, point200 = set(point_ranking[:50]), set(point_ranking[:200])
    j50, j200 = [], []
    for draw in ranks:
        order = np.flatnonzero(draw > 0)
        order = order[np.argsort(draw[order], kind="stable")]
        j50.append(jaccard(list(point50), order.tolist(), 50))
        j200.append(jaccard(list(point200), order.tolist(), 200))

    rows = []
    for rank, i in enumerate(point_ranking[:200], start=1):
        values = scores[:, i]
        finite = np.isfinite(values)
        observed = values[finite]
        observed_ranks = ranks[:, i][ranks[:, i] > 0]
        source = point_by_id[works[i]["work_id"]]
        rows.append(
            {
                "work_id": works[i]["work_id"], "title": works[i]["title"],
                "author": works[i]["author"], "catalog_n": works[i]["catalog_n"],
                "rank": rank, "score": float(100 * reproduced["score"][i]),
                "analytic_u": float(source["u"]),
                "pair_mass": float(reproduced["pair_mass"][i]),
                "reader_u80": float(
                    (np.quantile(observed, .9) - np.quantile(observed, .1)) / 2
                ),
                "bootstrap_eligibility": float(finite.mean()),
                "bootstrap_top200_rate": float(
                    np.mean((ranks[:, i] > 0) & (ranks[:, i] <= 200))
                ),
                "rank_q10": float(np.quantile(observed_ranks, .1)),
                "rank_q50": float(np.quantile(observed_ranks, .5)),
                "rank_q90": float(np.quantile(observed_ranks, .9)),
            }
        )
    u80 = np.asarray([row["reader_u80"] for row in rows])
    catalog = np.asarray([row["catalog_n"] for row in rows])
    mass = np.asarray([row["pair_mass"] for row in rows])
    summary = {
        "jaccard50_mean": float(np.mean(j50)),
        "jaccard50_q10": float(np.quantile(j50, .1)),
        "jaccard200_mean": float(np.mean(j200)),
        "jaccard200_q10": float(np.quantile(j200, .1)),
        "median_top200_u80": float(np.median(u80)),
        "median_top200_eligibility": float(
            np.median([row["bootstrap_eligibility"] for row in rows])
        ),
        "top200_u80_catalog_spearman": float(
            spearmanr(np.log1p(catalog), u80).statistic
        ),
        "top200_u80_pair_mass_spearman": float(spearmanr(mass, u80).statistic),
    }
    result = {
        "meta": {
            "purpose": "reader-block stability of hierarchical partial pooling",
            "mode": args.mode, "replicates": args.reps,
            "n_users": n_users, "n_books": len(works),
            "point_max_abs_score_error": validation_error,
            "runtime_seconds": time.time() - t0,
        },
        "summary": summary,
        "pair_mass_bands": band_summary(rows, "pair_mass", [10, 20, 50, 100, np.inf]),
        "books": rows,
    }
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_report(result, out_report)
    print(f"Wrote {out_report} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

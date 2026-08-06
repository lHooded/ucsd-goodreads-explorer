#!/usr/bin/env python3
"""Export alternative jury-feature selections with frozen community projections."""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import numpy as np

from curators_explorer.scripts.research_consensus_stability_pilot import BROAD_N
from curators_explorer.scripts.research_jury_seed_trajectories import (
    JURY_MODELS,
    build_fixed_partitions,
    build_fixed_preference_embedding,
    materialize_analysis_users,
    reconstruct_jury_models,
)
from curators_explorer.scripts.research_ratings_only_canon import _con
from curators_explorer.scripts.research_soft_membership_pilot import (
    calibrate_responsibilities,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SOFT_WEIGHTS = DATA_DIR / "soft_jury_weights.parquet"
BASE_ASSIGNMENTS = DATA_DIR / "jury_community_assignments.parquet"
BASE_FUZZY = DATA_DIR / "jury_fuzzy_community_assignments.parquet"
OUT = DATA_DIR / "jury_feature_variant_assignments.parquet"
SUMMARY = DATA_DIR / "jury_feature_variant_assignments.json"
TARGET = 0.90


def frozen_centroid_similarities(embedding, labels, k):
    centers = np.zeros((k, embedding.shape[1]), dtype=np.float64)
    np.add.at(centers, labels[:BROAD_N], embedding[:BROAD_N])
    sizes = np.bincount(labels[:BROAD_N], minlength=k).astype(float)
    centers /= np.maximum(sizes[:, None], 1.0)
    centers /= np.maximum(np.linalg.norm(centers, axis=1)[:, None], 1e-12)
    return np.asarray(embedding @ centers.T, dtype=np.float64)


def main():
    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    ids, scores, selected, jury_meta = reconstruct_jury_models(con)
    con.execute("PRAGMA threads=8")
    analysis_ids, masks, population_meta = materialize_analysis_users(
        con, ids, scores, selected
    )
    embedding, embedding_meta = build_fixed_preference_embedding(
        con, len(analysis_ids)
    )
    partitions = build_fixed_partitions(embedding, masks["rich_behavior_global"])
    con.close()

    out_con = duckdb.connect()
    q_rows = out_con.execute(
        f"SELECT user_id, jury_q FROM read_parquet('{SOFT_WEIGHTS}')"
    ).fetchall()
    q_by_id = {int(uid): float(q) for uid, q in q_rows}
    q = np.asarray([q_by_id.get(int(uid), 0.0) for uid in analysis_ids])
    calibrated = []
    calibration_meta = []
    for part in partitions:
        label, k = part["label"], int(part["k"])
        print(f"Calibrating projected {label}…", flush=True)
        # Use the already validated baseline assignment as the frozen anchor. Equivalent
        # SVD runs can differ at a handful of near-tie users, which would otherwise mix a
        # cluster-refit perturbation into the jury-feature comparison.
        hard_rows = out_con.execute(
            f"SELECT user_id, {label} FROM read_parquet('{BASE_ASSIGNMENTS}')"
        ).fetchall()
        hard_by_id = {int(uid): int(value) for uid, value in hard_rows}
        baseline_hard = np.asarray(
            [hard_by_id[int(uid)] for uid in analysis_ids[:BROAD_N]],
            dtype=np.int16,
        )
        part["labels"][:BROAD_N] = baseline_hard
        similarities = frozen_centroid_similarities(
            embedding, part["labels"], k
        )
        responsibility, meta = calibrate_responsibilities(
            similarities, q, TARGET
        )
        order = np.argsort(-responsibility, axis=1, kind="stable")[:, :2]
        rr = np.arange(len(q))[:, None]
        weight = responsibility[rr, order]
        fuzzy_rows = out_con.execute(
            f"SELECT user_id, {label}_a, {label}_wa, {label}_b, {label}_wb "
            f"FROM read_parquet('{BASE_FUZZY}')"
        ).fetchall()
        fuzzy_by_id = {
            int(uid): (int(a), float(wa), int(b), float(wb))
            for uid, a, wa, b, wb in fuzzy_rows
        }
        for idx, uid in enumerate(analysis_ids[:BROAD_N]):
            a, wa, b, wb = fuzzy_by_id[int(uid)]
            order[idx] = (a, b)
            weight[idx] = (wa, wb)
        calibrated.append(
            (label, order.astype(np.int16), weight.astype(np.float32))
        )
        calibration_meta.append(
            {
                "partition": label, "k": k, **meta,
                "argmax_fidelity_baseline": float(
                    np.mean(order[:BROAD_N, 0] == part["labels"][:BROAD_N])
                ),
            }
        )

    jury_labels = [spec["label"] for spec in JURY_MODELS]
    columns = [f"{label} BOOLEAN" for label in jury_labels]
    for label, _order, _weight in calibrated:
        columns.extend(
            [
                f"{label} SMALLINT", f"{label}_a SMALLINT", f"{label}_wa REAL",
                f"{label}_b SMALLINT", f"{label}_wb REAL",
            ]
        )
    out_con.execute(
        "CREATE TABLE assignments(user_id BIGINT, baseline_broad BOOLEAN, jury_q DOUBLE, "
        + ", ".join(columns) + ")"
    )
    rows = []
    for idx, uid in enumerate(analysis_ids):
        values = [int(uid), idx < BROAD_N, float(q[idx])]
        values.extend(bool(masks[label][idx]) for label in jury_labels)
        for pidx, (label, order, weight) in enumerate(calibrated):
            values.extend(
                [
                    int(partitions[pidx]["labels"][idx]),
                    int(order[idx, 0]), float(weight[idx, 0]),
                    int(order[idx, 1]), float(weight[idx, 1]),
                ]
            )
        rows.append(tuple(values))
    placeholders = ",".join("?" for _ in range(len(rows[0])))
    out_con.executemany(f"INSERT INTO assignments VALUES ({placeholders})", rows)
    temporary = OUT.with_suffix(".tmp.parquet")
    if temporary.exists():
        temporary.unlink()
    out_con.execute(
        f"COPY assignments TO '{temporary}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    temporary.replace(OUT)

    validation = {}
    for label, _k in [(p["label"], p["k"]) for p in partitions]:
        mismatch = out_con.execute(
            f"""
            SELECT count(*) FILTER (WHERE a.{label} != b.{label})
            FROM read_parquet('{OUT}') a
            JOIN read_parquet('{BASE_ASSIGNMENTS}') b USING (user_id)
            WHERE a.baseline_broad
            """
        ).fetchone()[0]
        fuzzy_error = out_con.execute(
            f"""
            SELECT max(greatest(
                abs(a.{label}_wa-b.{label}_wa),
                abs(a.{label}_wb-b.{label}_wb)
            ))
            FROM read_parquet('{OUT}') a
            JOIN read_parquet('{BASE_FUZZY}') b USING (user_id)
            WHERE a.baseline_broad
            """
        ).fetchone()[0]
        validation[label] = {
            "hard_label_mismatches": int(mismatch),
            "max_fuzzy_weight_error": float(fuzzy_error),
        }
    baseline_jury_mismatch = out_con.execute(
        f"""
        SELECT count(*) FILTER (WHERE a.rich_behavior_global != b.hard_jury)
        FROM read_parquet('{OUT}') a
        JOIN read_parquet('{BASE_ASSIGNMENTS}') b USING (user_id)
        WHERE a.baseline_broad
        """
    ).fetchone()[0]
    out_con.close()
    if baseline_jury_mismatch or any(
        row["hard_label_mismatches"] for row in validation.values()
    ):
        raise RuntimeError("frozen projection failed to reproduce baseline assignments")
    result = {
        "population": population_meta,
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "calibration": calibration_meta,
        "validation": {
            "baseline_jury_mismatches": int(baseline_jury_mismatch),
            "partitions": validation,
        },
        "jury_sizes": {
            label: int(masks[label].sum()) for label in jury_labels
        },
        "runtime_seconds": time.time()-t0,
        "output": str(OUT),
    }
    SUMMARY.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {OUT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

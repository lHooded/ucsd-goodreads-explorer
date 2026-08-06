#!/usr/bin/env python3
"""Export conservative mean-max-0.90 top-two community responsibilities."""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import numpy as np

from curators_explorer.scripts.research_consensus_stability_pilot import (
    build_partitions,
    build_preference_embedding,
    materialize_pilot_users,
    reconstruct_jury,
)
from curators_explorer.scripts.research_ratings_only_canon import _con
from curators_explorer.scripts.research_soft_membership_pilot import (
    calibrate_responsibilities,
    centroid_similarities,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
WEIGHTS = DATA_DIR / "soft_jury_weights.parquet"
OUT = DATA_DIR / "jury_fuzzy_community_assignments.parquet"
SUMMARY = DATA_DIR / "jury_fuzzy_community_assignments.json"
TARGET = 0.90


def main():
    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    jury_meta, all_ids, score, broad = reconstruct_jury(con)
    con.execute("PRAGMA threads=8")
    broad_ids, hard_mask, _ = materialize_pilot_users(con, all_ids, score, broad)
    embedding, embedding_meta = build_preference_embedding(con, len(broad_ids))
    partitions = build_partitions(embedding, hard_mask)
    con.close()

    out_con = duckdb.connect()
    q_rows = out_con.execute(
        f"SELECT user_id, jury_q FROM read_parquet('{WEIGHTS}')"
    ).fetchall()
    q_by_id = {int(uid): float(q) for uid, q in q_rows}
    q = np.asarray([q_by_id[int(uid)] for uid in broad_ids], dtype=np.float64)
    calibrated = []
    metadata = []
    for part in partitions:
        label, k = part["label"], int(part["k"])
        print(f"Calibrating {label}…", flush=True)
        similarity = centroid_similarities(embedding, part["labels"], k)
        responsibility, meta = calibrate_responsibilities(similarity, q, TARGET)
        order = np.argsort(-responsibility, axis=1, kind="stable")[:, :2]
        rr = np.arange(len(q))[:, None]
        weight = responsibility[rr, order]
        calibrated.append((label, order.astype(np.int16), weight.astype(np.float32)))
        metadata.append(
            {
                "partition": label, "k": k, **meta,
                "argmax_fidelity": float(
                    np.mean(order[:, 0] == part["labels"])
                ),
            }
        )

    columns = []
    for label, _order, _weight in calibrated:
        columns.extend(
            [
                f"{label}_a SMALLINT", f"{label}_wa REAL",
                f"{label}_b SMALLINT", f"{label}_wb REAL",
            ]
        )
    out_con.execute(
        "CREATE TABLE assignments(user_id BIGINT, jury_q DOUBLE, hard_jury BOOLEAN, "
        + ", ".join(columns) + ")"
    )
    rows = []
    for idx, uid in enumerate(broad_ids):
        values = [int(uid), float(q[idx]), bool(hard_mask[idx])]
        for _label, order, weight in calibrated:
            values.extend(
                [int(order[idx, 0]), float(weight[idx, 0]),
                 int(order[idx, 1]), float(weight[idx, 1])]
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
    out_con.close()
    result = {
        "users": len(rows), "target_mean_max": TARGET,
        "soft_mass": float(q.sum()), "hard_jury_users": int(hard_mask.sum()),
        "partitions": metadata, "jury_reconstruction": jury_meta,
        "embedding": embedding_meta, "runtime_seconds": time.time() - t0,
        "output": str(OUT),
    }
    SUMMARY.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {OUT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

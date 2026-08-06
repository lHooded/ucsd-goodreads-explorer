#!/usr/bin/env python3
"""Materialize the nine stable hard community assignments with jury weights."""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb

from curators_explorer.scripts.research_consensus_stability_pilot import (
    build_partitions,
    build_preference_embedding,
    materialize_pilot_users,
    reconstruct_jury,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
WEIGHTS = DATA_DIR / "soft_jury_weights.parquet"
OUT = DATA_DIR / "jury_community_assignments.parquet"
SUMMARY = DATA_DIR / "jury_community_assignments.json"


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
    labels = [part["label"] for part in partitions]
    columns = ", ".join(f"{label} SMALLINT" for label in labels)
    out_con.execute(
        f"CREATE TABLE assignments(user_id BIGINT, jury_q DOUBLE, "
        f"hard_jury BOOLEAN, {columns})"
    )
    rows = []
    for idx, uid in enumerate(broad_ids):
        rows.append(
            (
                int(uid), q_by_id[int(uid)], bool(hard_mask[idx]),
                *[int(part["labels"][idx]) for part in partitions],
            )
        )
    placeholders = ",".join("?" for _ in range(3 + len(labels)))
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
        "users": len(rows),
        "soft_mass": sum(row[1] for row in rows),
        "hard_jury_users": sum(row[2] for row in rows),
        "partitions": [
            {
                "label": part["label"],
                "k": int(part["k"]),
                "soft_mass_by_community": [
                    float(sum(q_by_id[int(broad_ids[i])] for i in range(len(broad_ids))
                              if int(part["labels"][i]) == community))
                    for community in range(int(part["k"]))
                ],
            }
            for part in partitions
        ],
        "jury_reconstruction": jury_meta,
        "embedding": embedding_meta,
        "runtime_seconds": time.time() - t0,
        "output": str(OUT),
    }
    SUMMARY.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {OUT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Materialize bootstrap jury-inclusion probabilities with stable user IDs."""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import numpy as np

from curators_explorer.scripts.research_consensus_stability_pilot import (
    JURY_N,
    reconstruct_jury,
)
from curators_explorer.scripts.research_ratings_only_canon import _con


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CHECKPOINT = DATA_DIR / "overnight_jury_bootstrap_full_checkpoint.npz"
OUT = DATA_DIR / "soft_jury_weights.parquet"
SUMMARY = DATA_DIR / "soft_jury_weights_summary.json"


def main():
    t0 = time.time()
    con = _con()
    con.execute("PRAGMA memory_limit='6GB'")
    con.execute("PRAGMA threads=1")
    _meta, all_ids, model_score, broad = reconstruct_jury(con)
    con.close()
    with np.load(CHECKPOINT, allow_pickle=False) as saved:
        completed = int(saved["completed"])
        q = saved["selected_counts"].astype(np.float64) / completed
    if len(q) != len(broad) or not np.isclose(q.sum(), JURY_N):
        raise RuntimeError("checkpoint selection counts do not match broad jury pool")
    score_by_id = {int(uid): float(score) for uid, score in zip(all_ids, model_score)}
    rows = [
        (int(uid), rank < JURY_N, float(q[rank]), rank + 1, score_by_id[int(uid)])
        for rank, uid in enumerate(broad)
    ]
    out_con = duckdb.connect()
    out_con.execute(
        "CREATE TABLE weights(user_id BIGINT, hard_jury BOOLEAN, jury_q DOUBLE, "
        "broad_rank INTEGER, behavior_score DOUBLE)"
    )
    out_con.executemany("INSERT INTO weights VALUES (?, ?, ?, ?, ?)", rows)
    temporary = OUT.with_suffix(".tmp.parquet")
    if temporary.exists():
        temporary.unlink()
    out_con.execute(
        f"COPY weights TO '{temporary}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    temporary.replace(OUT)
    out_con.close()
    summary = {
        "source_replicates": completed,
        "users": len(rows),
        "hard_jury_users": JURY_N,
        "soft_mass": float(q.sum()),
        "soft_nonzero_users": int(np.sum(q > 0)),
        "kish_effective_users": float(q.sum() ** 2 / np.sum(q * q)),
        "elapsed_seconds": time.time() - t0,
        "output": str(OUT),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()

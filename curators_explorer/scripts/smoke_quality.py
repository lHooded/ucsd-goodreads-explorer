#!/usr/bin/env python3
"""Quick quality smoke checks for curators_explorer defaults."""

from __future__ import annotations

import json
import time
from pathlib import Path

from curators_explorer.ranking import rank_books
from curators_explorer.taste_packs import reset_pack

ROOT = Path(__file__).resolve().parents[2]
TASTE = json.loads((ROOT / "ucsd_explorer/data/taste_lists.json").read_text())
ANTI = {s.get("resolved_name") or s["match"] for s in TASTE["resolved"]["non_literary"]}
POS = {s.get("resolved_name") or s["match"] for s in TASTE["resolved"]["literary_poll"]}


def main() -> None:
    reset_pack()
    cases = [
        ("everyone", dict(deweight=0, purity=0)),
        ("default", dict(deweight=15, purity=55)),
        ("browse", dict(deweight=25, purity=0)),
        ("sharp", dict(deweight=15, purity=65)),
    ]
    for name, knobs in cases:
        params = dict(
            metric="love",
            scale_mode="adjusted",
            min_votes=25,
            limit=200,
            sf_only=False,
            **knobs,
        )
        t0 = time.time()
        out = rank_books(params)
        ms = int((time.time() - t0) * 1000)
        rows = out["results"]
        pos50 = sum(1 for r in rows[:50] if r["author"] in POS)
        anti50 = sum(1 for r in rows[:50] if r["author"] in ANTI)
        print(
            f"{name:10s} {ms:5d}ms curators={out['cohort']['n_curators']:6d} "
            f"kind={out['cohort']['cohort_kind']:10s} "
            f"pos50={pos50} anti50={anti50}"
        )
        print("   top5:", ", ".join(r["title"][:40] for r in rows[:5]))


if __name__ == "__main__":
    main()

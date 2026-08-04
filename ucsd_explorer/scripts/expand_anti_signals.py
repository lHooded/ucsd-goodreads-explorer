#!/usr/bin/env python3
"""Discover hybrid non-literary anti-signal author candidates.

Sources:
  1) UCSD crowd vs deep-curator rating gap (friends-rating analogue)
  2) Post45 NYT hardcover fiction bestsellers (weeks on list, 1980+)
  3) Optional manual seed list

Does not write taste_lists.json — prints / writes candidate JSON for review.

Usage (from repo root):
  .venv/bin/python -m ucsd_explorer.scripts.expand_anti_signals
  # optional: --nyt .tmp/nyt_full.tsv --out .tmp/anti_signal_candidates.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

from ucsd_explorer.db import get_con
from ucsd_explorer.taste import fold

ROOT = Path(__file__).resolve().parents[2]
TASTE_PATH = Path(__file__).resolve().parents[1] / "data" / "taste_lists.json"

MANUAL_SEEDS = [
    "John Scalzi",
    "Orson Scott Card",
    "Brandon Sanderson",
    "Patrick Rothfuss",
    "Jim Butcher",
    "Patricia Briggs",
    "Ilona Andrews",
    "Karen Marie Moning",
    "Laurell K. Hamilton",
    "Sherrilyn Kenyon",
    "Nora Roberts",
    "Danielle Steel",
    "Nicholas Sparks",
    "Colleen Hoover",
    "Sarah J. Maas",
    "Rebecca Yarros",
    "Emily Henry",
    "Ali Hazelwood",
    "Casey McQuiston",
    "Taylor Jenkins Reid",
    "Abby Jimenez",
    "Elsie Silver",
    "Rainbow Rowell",
    "Jenny Han",
    "Holly Black",
    "Leigh Bardugo",
    "V.E. Schwab",
    "Victoria Aveyard",
    "Jay Kristoff",
    "Marie Lu",
    "Tahereh Mafi",
    "Sabaa Tahir",
    "Jennifer L. Armentrout",
    "Laura Thalassa",
    "James Patterson",
    "Lee Child",
    "John Grisham",
    "David Baldacci",
    "Dean Koontz",
    "Clive Cussler",
    "Tom Clancy",
    "Robert Ludlum",
    "E.L. James",
    "Sylvia Day",
    "R.A. Salvatore",
    "Terry Goodkind",
    "Robert Jordan",
    "Terry Brooks",
    "Piers Anthony",
    "Kevin J. Anderson",
    "Brian Herbert",
    "L. Ron Hubbard",
    "Eoin Colfer",
    "Brent Weeks",
    "Peter V. Brett",
    "Craig Alanson",
    "Matt Dinniman",
    "Travis Baldree",
    "Pirateaba",
    "Will Wight",
    "Sophie Kinsella",
    "Helen Fielding",
    "Paulo Coelho",
    "Elizabeth Gilbert",
    "Tim LaHaye",
    "Frank E. Peretti",
]

EXTRA_PROTECT = [
    "Ursula K. Le Guin",
    "Octavia E. Butler",
    "Samuel R. Delany",
    "Philip K. Dick",
    "J.R.R. Tolkien",
    "George R.R. Martin",
    "Frank Herbert",
    "Mary Shelley",
    "H.G. Wells",
    "Jules Verne",
    "Kurt Vonnegut",
    "Margaret Atwood",
    "Kazuo Ishiguro",
    "David Foster Wallace",
    "Thomas Pynchon",
    "Don DeLillo",
    "Cormac McCarthy",
    "Toni Morrison",
    "Virginia Woolf",
    "Jane Austen",
    "Charles Dickens",
    "William Faulkner",
    "Gabriel García Márquez",
    "Haruki Murakami",
    "Neil Gaiman",
    "China Miéville",
    "Ted Chiang",
    "Jeff VanderMeer",
    "Emily St. John Mandel",
    "Colson Whitehead",
    "N.K. Jemisin",
    "Ann Leckie",
    "Becky Chambers",
    "Ada Palmer",
    "Kim Stanley Robinson",
    "Iain M. Banks",
    "Gene Wolfe",
    "William Gibson",
    "Neal Stephenson",
    "Dan Simmons",
    "Connie Willis",
    "Lois McMaster Bujold",
    "Terry Pratchett",
    "Joe Abercrombie",
]


def _protect_folds(taste: dict) -> set[str]:
    protect: set[str] = set()
    for key in ("literary", "literary_sf_extras"):
        for x in taste.get(key, []):
            protect.add(fold(x["match"]))
    for x in taste.get("non_literary_audit", {}).get("removed_from_non_literary", []):
        protect.add(fold(x.get("match") or ""))
    for n in EXTRA_PROTECT:
        protect.add(fold(n))
    return protect


def ucsd_gap_candidates(con, *, existing: set[str], protect: set[str]) -> list[dict]:
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE deep_users AS
        SELECT user_id FROM user_curator_deep_weight
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE work_deep AS
        SELECT
          e.work_id,
          count(*)::BIGINT AS n_deep,
          avg(e.rating)::DOUBLE AS mean_deep,
          avg(CASE WHEN e.rating = 5 THEN 1.0 ELSE 0 END)::DOUBLE AS p5_deep
        FROM all_rating_events e
        JOIN deep_users d USING (user_id)
        GROUP BY e.work_id
        HAVING count(*) >= 20
        """
    )
    rows = con.execute(
        """
        WITH joined AS (
          SELECT
            w.author AS author,
            w.n AS n_global,
            w.mean AS mean_global,
            w.p5 AS p5_global,
            d.n_deep,
            d.mean_deep,
            d.p5_deep,
            coalesce(w.is_sf, false) AS is_sf
          FROM work_scores w
          JOIN work_deep d USING (work_id)
          WHERE w.author IS NOT NULL AND length(trim(w.author)) > 1
            AND w.n >= 200
        )
        SELECT
          author,
          count(*)::BIGINT AS n_works,
          sum(n_global)::BIGINT AS crowd_n,
          sum(n_deep)::BIGINT AS deep_n,
          sum(mean_global * n_global) / sum(n_global) AS crowd_mean,
          sum(mean_deep * n_deep) / sum(n_deep) AS deep_mean,
          sum(p5_global * n_global) / sum(n_global) AS crowd_p5,
          sum(p5_deep * n_deep) / sum(n_deep) AS deep_p5,
          bool_or(is_sf) AS any_sf
        FROM joined
        GROUP BY author
        HAVING sum(n_global) >= 2000 AND sum(n_deep) >= 80
        """
    ).fetchall()
    out: list[dict] = []
    for (
        author,
        n_works,
        crowd_n,
        deep_n,
        crowd_mean,
        deep_mean,
        crowd_p5,
        deep_p5,
        any_sf,
    ) in rows:
        f = fold(author)
        if f in protect or f in existing:
            continue
        mean_gap = float(crowd_mean) - float(deep_mean)
        p5_gap = float(crowd_p5) - float(deep_p5)
        if mean_gap < 0.12 and p5_gap < 0.04:
            continue
        score = (0.55 * mean_gap + 0.45 * (p5_gap * 5.0)) * (
            1.0 + 0.15 * math.log10(max(int(crowd_n), 10))
        )
        out.append(
            {
                "author": author,
                "source": "ucsd_gap",
                "score": round(score, 4),
                "mean_gap": round(mean_gap, 4),
                "p5_gap": round(p5_gap, 4),
                "crowd_mean": round(float(crowd_mean), 3),
                "deep_mean": round(float(deep_mean), 3),
                "crowd_p5": round(float(crowd_p5), 3),
                "deep_p5": round(float(deep_p5), 3),
                "crowd_n": int(crowd_n),
                "deep_n": int(deep_n),
                "n_works": int(n_works),
                "any_sf": bool(any_sf),
            }
        )
    out.sort(key=lambda x: -x["score"])
    return out


def nyt_candidates(
    path: Path, *, existing: set[str], protect: set[str], min_year: int = 1980
) -> list[dict]:
    weeks: Counter[str] = Counter()
    with path.open(encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            try:
                year = int(row.get("year") or 0)
            except ValueError:
                continue
            if year < min_year:
                continue
            author = (row.get("author") or "").strip()
            if not author:
                continue
            author = re.sub(r"^by\s+", "", author, flags=re.I)
            author = author.split("/")[0].split(";")[0].strip()
            if author:
                weeks[author] += 1
    out: list[dict] = []
    for author, w in weeks.most_common():
        if w < 8:
            break
        f = fold(author)
        if f in protect or f in existing:
            continue
        out.append(
            {
                "author": author,
                "source": "nyt_bestseller",
                "weeks": int(w),
                "score": float(w),
            }
        )
    return out


def merge_candidates(
    ucsd: list[dict],
    nyt: list[dict],
    *,
    existing: set[str],
    protect: set[str],
) -> list[dict]:
    merged: dict[str, dict] = {}

    def add(rec: dict) -> None:
        f = fold(rec["author"])
        if f in protect:
            return
        if f not in merged:
            merged[f] = {
                "author": rec["author"],
                "sources": set(),
                "ucsd_score": 0.0,
                "nyt_weeks": 0,
                "mean_gap": None,
                "p5_gap": None,
                "crowd_n": 0,
                "any_sf": False,
                "already": f in existing,
            }
        m = merged[f]
        m["sources"].add(rec["source"])
        if rec["source"].startswith("ucsd"):
            m["ucsd_score"] = max(m["ucsd_score"], float(rec.get("score") or 0))
            m["mean_gap"] = rec.get("mean_gap")
            m["p5_gap"] = rec.get("p5_gap")
            m["crowd_n"] = max(m["crowd_n"], int(rec.get("crowd_n") or 0))
            m["any_sf"] = m["any_sf"] or bool(rec.get("any_sf"))
            if len(rec["author"]) > len(m["author"]):
                m["author"] = rec["author"]
        if rec["source"] == "nyt_bestseller":
            m["nyt_weeks"] = max(m["nyt_weeks"], int(rec.get("weeks") or 0))
        if rec["source"] == "manual_seed":
            m["ucsd_score"] = max(m["ucsd_score"], 1.0)

    for c in ucsd:
        add(c)
    for c in nyt:
        add(c)
    for name in MANUAL_SEEDS:
        f = fold(name)
        if f in protect or f in existing:
            continue
        add({"author": name, "source": "manual_seed", "score": 50.0})

    new: list[dict] = []
    for m in merged.values():
        if m["already"]:
            continue
        sources = m["sources"]
        s = float(m["ucsd_score"])
        s += 0.02 * m["nyt_weeks"]
        if "manual_seed" in sources:
            s += 8.0
        if "ucsd_gap" in sources and "nyt_bestseller" in sources:
            s += 5.0
        if len(sources) >= 2:
            s += 3.0
        if m["ucsd_score"] <= 0 and m["nyt_weeks"] < 15 and "manual_seed" not in sources:
            continue
        new.append(
            {
                "author": m["author"],
                "sources": sorted(sources),
                "hybrid_score": round(s, 3),
                "ucsd_score": round(float(m["ucsd_score"]), 3),
                "nyt_weeks": int(m["nyt_weeks"]),
                "mean_gap": m["mean_gap"],
                "p5_gap": m["p5_gap"],
                "crowd_n": int(m["crowd_n"]),
                "any_sf": bool(m["any_sf"]),
            }
        )
    new.sort(key=lambda x: -x["hybrid_score"])
    return new


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--nyt",
        type=Path,
        default=ROOT / ".tmp" / "nyt_full.tsv",
        help="Post45 NYT bestsellers TSV",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".tmp" / "anti_signal_candidates.json",
    )
    args = ap.parse_args()

    taste = json.loads(TASTE_PATH.read_text(encoding="utf-8"))
    existing = {fold(x["match"]) for x in taste.get("non_literary", [])}
    protect = _protect_folds(taste)
    con = get_con()

    print("UCSD crowd−curator gap…", flush=True)
    ucsd = ucsd_gap_candidates(con, existing=existing, protect=protect)
    print(f"  {len(ucsd)} UCSD gap candidates", flush=True)

    nyt: list[dict] = []
    if args.nyt.exists():
        print(f"NYT bestsellers from {args.nyt}…", flush=True)
        nyt = nyt_candidates(args.nyt, existing=existing, protect=protect)
        print(f"  {len(nyt)} NYT candidates", flush=True)
    else:
        print(f"NYT file missing ({args.nyt}); skipping", flush=True)

    merged = merge_candidates(ucsd, nyt, existing=existing, protect=protect)
    payload = {
        "n_existing": len(existing),
        "n_new": len(merged),
        "new": merged,
        "ucsd_top": ucsd[:100],
        "nyt_top": nyt[:100],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} ({len(merged)} new candidates)", flush=True)
    for c in merged[:25]:
        print(
            f"  {c['hybrid_score']:7.2f}  {c['author'][:42]:42s}  "
            f"{','.join(c['sources'])}",
            flush=True,
        )


if __name__ == "__main__":
    main()

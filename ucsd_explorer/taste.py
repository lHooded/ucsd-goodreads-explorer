#!/usr/bin/env python3
"""Literary vs non-literary taste signals for the UCSD explorer.

Taste is scored from the *full* Goodreads dump (not SF-only):

* Literary hits: ★≥4 on poll (+ optional SF prestige extras) authors
* Non-literary hits: ★=5 only on the anti-signal authors (1–4★ are fine)

SF rankings then optionally keep only users who pass the taste sliders.
"""

from __future__ import annotations

import json
import math
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Optional

from ucsd_explorer.db import EXPLORER_DB, NORMIE_PATH, PARQUET, ROOT, TASTE_PATH

STATIC_TASTE_PATH = Path(__file__).resolve().parent / "static" / "data" / "taste_lists.json"
POLL_PATH = ROOT / "lit-2014-2024.txt"
WAREHOUSE_DB = ROOT / "data" / "ucsd_goodreads" / "ucsd.duckdb"

# SF extras are not on the poll chart; give a mid-high default prestige.
SF_EXTRA_PRESTIGE = 0.72
# Poll is still a top-100-of-all-time list: rank 1 → 1.0, rank N → PRESTIGE_FLOOR.
POLL_PRESTIGE_FLOOR = 0.5

# Goodreads name variants
NAME_ALIASES: dict[str, list[str]] = {
    "miguel de cervantes": ["Miguel de Cervantes Saavedra", "Miguel de Cervantes"],
    "stanisław lem": ["Stanislaw Lem", "Stanisław Lem"],
    "stanislaw lem": ["Stanislaw Lem"],
    "fyodor dostoevsky": ["Fyodor Dostoyevsky", "Fyodor Dostoevsky"],
    "fyodor dostoyevsky": ["Fyodor Dostoyevsky", "Fyodor Dostoevsky"],
    "james tiptree jr.": ["James Tiptree Jr.", "James Tiptree, Jr.", "Alice Bradley Sheldon"],
    "arkady strugatsky": [
        "Arkady Strugatsky",
        "Arkadii Strugatskii",
        "Arkady Natanovich Strugatsky",
    ],
    "china miéville": ["China Miéville", "China Mieville"],
    "gabriel garcía márquez": ["Gabriel García Márquez", "Gabriel Garcia Marquez"],
    "louis-ferdinand céline": ["Louis-Ferdinand Céline", "Louis-Ferdinand Celine"],
    "emily brontë": ["Emily Brontë", "Emily Bronte"],
    "natsume sōseki": ["Natsume Sōseki", "Natsume Soseki"],
    "j.k. rowling": ["J.K. Rowling", "J. K. Rowling"],
    "p.c. cast": ["P.C. Cast", "P. C. Cast"],
    "james s.a. corey": ["James S.A. Corey", "James S. A. Corey"],
    "kurt vonnegut": ["Kurt Vonnegut", "Kurt Vonnegut Jr.", "Kurt Vonnegut Jr"],
    "mary shelley": ["Mary Shelley", "Mary Wollstonecraft Shelley"],
    "f. scott fitzgerald": ["F. Scott Fitzgerald", "Francis Scott Fitzgerald"],
    "j.d. salinger": ["J.D. Salinger", "J. D. Salinger", "JD Salinger"],
    "natsume soseki": ["Natsume Soseki", "Natsume Sōseki"],
}


def parse_poll_chart(path: Path | None = None) -> list[dict[str, Any]]:
    """Parse lit-2014-2024.txt → [{rank, title, author}, ...] (1-indexed ranks)."""
    p = path or POLL_PATH
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # "Title - Author" (last " - " split; titles may contain dashes)
        if " - " in line:
            title, author = line.rsplit(" - ", 1)
        elif " — " in line:
            title, author = line.rsplit(" — ", 1)
        else:
            continue
        rows.append(
            {
                "rank": i,
                "title": title.strip(),
                "author": author.strip(),
            }
        )
    return rows


def author_poll_prestige(
    *,
    literary_matches: list[str],
    floor: float = POLL_PRESTIGE_FLOOR,
    poll_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Best (highest) chart prestige per literary author name (folded).

    Preferring books further up the poll, gently: rank 1 → 1.0, rank N → floor
    (default 0.5). It's still a top-100 list; the bottom shouldn't be near-zero.
    Multiple chart books → use the author's best (lowest) rank.
    """
    chart = parse_poll_chart(poll_path)
    n = max(len(chart), 1)
    best_rank: dict[str, int] = {}
    best_title: dict[str, str] = {}
    for row in chart:
        f = fold(row["author"])
        r = int(row["rank"])
        if f not in best_rank or r < best_rank[f]:
            best_rank[f] = r
            best_title[f] = row["title"]

    out: dict[str, dict[str, Any]] = {}
    for match in literary_matches:
        f = fold(match)
        # Also try aliases
        candidates = [f] + [fold(a) for a in NAME_ALIASES.get(f, [])]
        rank = None
        title = None
        for c in candidates:
            if c in best_rank:
                if rank is None or best_rank[c] < rank:
                    rank = best_rank[c]
                    title = best_title[c]
            # partial: chart author fold equals or contains
            for cf, rr in best_rank.items():
                if cf == c or (len(c) > 5 and (c in cf or cf in c)):
                    if rank is None or rr < rank:
                        rank = rr
                        title = best_title[cf]
        if rank is None:
            # Unmatched literary author — mid-pack default
            prestige = 0.5 * (1.0 + floor)
            rank = None
        else:
            # Linear: rank 1 → 1.0, rank n → floor
            t = (rank - 1) / max(n - 1, 1)
            prestige = 1.0 - (1.0 - floor) * t
        out[fold(match)] = {
            "match": match,
            "poll_rank": rank,
            "poll_title": title,
            "prestige": float(prestige),
        }
    return out


def fold(s: str) -> str:
    s = (s or "").translate(
        str.maketrans(
            {
                "ł": "l",
                "Ł": "L",
                "ø": "o",
                "Ø": "O",
                "đ": "d",
                "Đ": "D",
                "ð": "d",
                "Ð": "D",
                "þ": "th",
                "Þ": "th",
                "ß": "ss",
            }
        )
    )
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.casefold().strip(" ,.")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_taste_lists(path: Path | None = None) -> dict[str, Any]:
    p = path or TASTE_PATH
    if not p.exists():
        raise SystemExit(f"Missing {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _norm_title_key(title: str) -> str:
    t = fold(title or "")
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^(the|a|an)\s+", "", t)
    return t


def _author_candidate_keys(author: str) -> list[str]:
    """Folded author keys including NAME_ALIASES for catalog lookup."""
    f = fold(author)
    keys = [f]
    for a in NAME_ALIASES.get(f, []):
        fa = fold(a)
        if fa and fa not in keys:
            keys.append(fa)
    # Also try reverse: if catalog uses Jr. form as alias target
    for alias_key, variants in NAME_ALIASES.items():
        if f == alias_key or f in {fold(v) for v in variants}:
            if alias_key not in keys:
                keys.append(alias_key)
            for v in variants:
                fv = fold(v)
                if fv and fv not in keys:
                    keys.append(fv)
    return keys


def match_poll_works(con) -> list[dict[str, Any]]:
    """Map lit-2014-2024 chart entries → explorer work_ids (edition-collapsed).

    Popularity ``n`` is work_scores.n so rare *editions* of famous books cannot
    game rarity. Returns one row per matched poll entry.
    """
    chart = parse_poll_chart()
    prestige_by_author = author_poll_prestige(
        literary_matches=[e["author"] for e in chart]
    )
    rows = con.execute(
        """
        SELECT work_id, title, author, n
        FROM work_scores
        WHERE n >= 40
        """
    ).fetchall()
    by_author: dict[str, list[tuple[str, str, int]]] = {}
    for wid, title, author, n in rows:
        by_author.setdefault(fold(author or ""), []).append(
            (str(wid), title or "", int(n or 0))
        )

    matched: list[dict[str, Any]] = []
    seen: set[str] = set()
    for e in chart:
        pa = fold(e["author"])
        pt = _norm_title_key(e["title"])
        best = None
        cands: list[tuple[str, str, int]] = []
        for key in _author_candidate_keys(e["author"]):
            cands.extend(by_author.get(key) or [])
        # Mild fallback: author last-token match (e.g. "Jr.")
        if not cands:
            last = pa.split()[-1] if pa else ""
            if len(last) >= 5:
                for k, vs in by_author.items():
                    if k.endswith(last) or last in k.split():
                        cands.extend(vs)
        for wid, title, n in cands:
            wt = _norm_title_key(title)
            if not wt or not pt:
                continue
            if (
                wt == pt
                or wt.startswith(pt + " ")
                or pt.startswith(wt + " ")
                or (len(pt) >= 8 and pt in wt)
                or (len(wt) >= 8 and wt in pt)
            ):
                if best is None or n > best[2]:
                    best = (wid, title, n)
        if not best or best[0] in seen:
            continue
        seen.add(best[0])
        info = prestige_by_author.get(pa) or {}
        matched.append(
            {
                "work_id": best[0],
                "poll_rank": int(e["rank"]),
                "poll_title": e["title"],
                "poll_author": e["author"],
                "work_title": best[1],
                "n": best[2],
                "prestige": float(info.get("prestige") or 0.25),
            }
        )
    return matched


def _configure_duckdb(con) -> None:
    """Faster bulk builds: skip insertion-order preservation, use all cores."""
    import os

    try:
        con.execute("SET preserve_insertion_order=false")
    except Exception:
        pass
    try:
        con.execute("SET enable_progress_bar=false")
    except Exception:
        pass
    threads = max(1, min(16, os.cpu_count() or 4))
    try:
        con.execute(f"SET threads={threads}")
    except Exception:
        pass


def _ensure_are_user_index(con) -> None:
    """user_id index on ~100M rating events — critical for curator builds/joins."""
    rows = con.execute(
        """
        SELECT index_name FROM duckdb_indexes()
        WHERE table_name = 'all_rating_events'
          AND index_name = 'idx_are_user'
        """
    ).fetchall()
    if rows:
        return
    print("Creating all_rating_events(user_id) index (one-time, may take a bit)…", flush=True)
    t0 = time.time()
    con.execute("CREATE INDEX idx_are_user ON all_rating_events(user_id)")
    print(f"  idx_are_user ready in {time.time() - t0:.1f}s", flush=True)


def _materialize_user_star_hist(con) -> None:
    """One full pass over ratings → per-user star histogram + mean (shared by curators)."""
    print("User star histograms (shared curator/percentile input)…", flush=True)
    t0 = time.time()
    con.execute("DROP TABLE IF EXISTS user_star_hist")
    con.execute(
        """
        CREATE TABLE user_star_hist AS
        SELECT
            user_id,
            count(*)::BIGINT AS n_rated,
            avg(rating)::DOUBLE AS mean_rating,
            max(rating)::INTEGER AS max_star,
            count(*) FILTER (WHERE rating = 1)::BIGINT AS c1,
            count(*) FILTER (WHERE rating = 2)::BIGINT AS c2,
            count(*) FILTER (WHERE rating = 3)::BIGINT AS c3,
            count(*) FILTER (WHERE rating = 4)::BIGINT AS c4,
            count(*) FILTER (WHERE rating = 5)::BIGINT AS c5,
            count(DISTINCT rating)::BIGINT AS n_levels
        FROM all_rating_events
        GROUP BY user_id
        """
    )
    con.execute("CREATE INDEX idx_ush_user ON user_star_hist(user_id)")
    n = int(con.execute("SELECT count(*) FROM user_star_hist").fetchone()[0])
    print(f"  user_star_hist: {n:,} users in {time.time() - t0:.1f}s", flush=True)


def _materialize_curator_weights(con, poll_works: list[dict[str, Any]]) -> dict[str, Any]:
    """RYM-style curator gates → user_curator_weight.

    Gates mirror the film curation criteria:
      1. moderate five_rate + mean (not extreme pos/neg)
      2. at least one 5★
      3. depth into rarer *poll* literary works (work-level n, not editions)
      4. existing lit_weight (appreciated / chart taste)
    """
    print("Curator weights (RYM-style gates + poll-work rarity)…", flush=True)
    _ensure_are_user_index(con)
    _materialize_user_star_hist(con)

    con.execute("DROP TABLE IF EXISTS poll_works")
    con.execute(
        """
        CREATE TABLE poll_works (
            work_id VARCHAR,
            poll_rank INTEGER,
            poll_title VARCHAR,
            poll_author VARCHAR,
            work_title VARCHAR,
            n BIGINT,
            prestige DOUBLE,
            rarity DOUBLE
        )
        """
    )
    rows = []
    for p in poll_works:
        rarity = 1.0 / math.log(2.0 + float(p["n"]))
        rows.append(
            (
                p["work_id"],
                p["poll_rank"],
                p["poll_title"],
                p["poll_author"],
                p["work_title"],
                p["n"],
                p["prestige"],
                rarity,
            )
        )
    con.executemany("INSERT INTO poll_works VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.execute("CREATE INDEX idx_poll_works ON poll_works(work_id)")

    con.execute("DROP TABLE IF EXISTS user_curator_weight")
    con.execute(
        """
        CREATE TABLE user_curator_weight AS
        WITH user_poll AS (
            SELECT
                e.user_id,
                count(DISTINCT e.work_id)::BIGINT AS n_poll_works,
                sum(p.rarity * p.prestige)::DOUBLE AS rarity_mass,
                max(p.rarity)::DOUBLE AS max_rarity,
                -- "Rare" ≈ bottom half of chart by work-level popularity
                count(DISTINCT e.work_id) FILTER (
                    WHERE p.n <= (SELECT approx_quantile(n, 0.50) FROM poll_works)
                )::BIGINT AS n_rare_poll
            FROM all_rating_events e
            JOIN poll_works p USING (work_id)
            WHERE e.rating >= 4
            GROUP BY e.user_id
        ),
        base AS (
            SELECT
                w.user_id,
                w.lit_weight,
                w.lit_share,
                w.lit_hits,
                w.com_hits,
                u.five_rate,
                u.n_rated,
                m.mean_rating,
                m.c5 AS n5,
                coalesce(up.n_poll_works, 0) AS n_poll_works,
                coalesce(up.rarity_mass, 0) AS rarity_mass,
                coalesce(up.max_rarity, 0) AS max_rarity,
                coalesce(up.n_rare_poll, 0) AS n_rare_poll,
                CASE WHEN m.c5 >= 1 THEN 1.0 ELSE 0.0 END AS has_five,
                CASE
                    WHEN u.five_rate BETWEEN 0.10 AND 0.42
                         AND m.mean_rating BETWEEN 3.05 AND 4.05 THEN 1.0
                    WHEN u.five_rate BETWEEN 0.08 AND 0.50
                         AND m.mean_rating BETWEEN 2.95 AND 4.15 THEN 0.55
                    ELSE 0.0
                END AS moderate_gate,
                -- Emphasize depth into rare chart works (power > 1)
                power(ln(1.0 + coalesce(up.rarity_mass, 0) * 5.0), 1.35) AS rarity_boost
            FROM user_lit_weight w
            JOIN user_pickiness u USING (user_id)
            JOIN user_star_hist m USING (user_id)
            LEFT JOIN user_poll up USING (user_id)
            WHERE w.lit_hits >= 4
              AND w.com_hits <= greatest(3, cast(w.lit_hits * 0.35 AS BIGINT))
              AND u.n_rated >= 40
        ),
        norms AS (
            SELECT max(rarity_boost) AS max_boost FROM base WHERE has_five = 1
        ),
        scored AS (
            SELECT
                b.user_id,
                b.lit_weight,
                b.lit_share,
                b.lit_hits,
                b.com_hits,
                b.five_rate,
                b.mean_rating,
                b.n_rated,
                b.n5,
                b.n_poll_works,
                b.rarity_mass,
                b.max_rarity,
                b.n_rare_poll,
                b.has_five,
                b.moderate_gate,
                b.rarity_boost,
                (
                    b.has_five
                    * b.moderate_gate
                    * b.lit_weight
                    * (
                        0.35 + 0.65 * (
                            b.rarity_boost / nullif((SELECT max_boost FROM norms), 0)
                        )
                    )
                )::DOUBLE AS curator_weight
            FROM base b
            WHERE b.has_five = 1
              AND b.moderate_gate >= 0.55
              AND b.n_poll_works >= 5
              AND b.n_rare_poll >= 1
        )
        SELECT
            s.*,
            percent_rank() OVER (ORDER BY s.curator_weight)::DOUBLE AS weight_pctile
        FROM scored s
        """
    )
    con.execute("CREATE INDEX idx_ucw_user ON user_curator_weight(user_id)")
    n = int(con.execute("SELECT count(*) FROM user_curator_weight").fetchone()[0])
    bounds = con.execute(
        "SELECT min(curator_weight), max(curator_weight), avg(curator_weight) "
        "FROM user_curator_weight"
    ).fetchone()
    print(
        f"  poll_works: {len(poll_works):,} · curator users: {n:,} · "
        f"weight {bounds[0]:.3f}–{bounds[2]:.3f}–{bounds[1]:.3f}",
        flush=True,
    )

    pct_meta = _materialize_percentile_curators(con)
    return {
        "n_poll_works": len(poll_works),
        "n_curator_users": n,
        "curator_weight_min": float(bounds[0]) if bounds[0] is not None else None,
        "curator_weight_avg": float(bounds[2]) if bounds[2] is not None else None,
        "curator_weight_max": float(bounds[1]) if bounds[1] is not None else None,
        **pct_meta,
    }


def _materialize_percentile_curators(con) -> dict[str, Any]:
    """Criticker-style mid-bin percentiles + pct-curator cohort (no mean gate).

    Percentiles are *literary-anchored* when the user has enough poll-author
    ratings (≥20): the CDF is built only on literary_poll signal works so
    bingeing trash does not stretch the bottom of the scale. Otherwise fall
    back to the full-shelf CDF.

    Pct-curator gates drop the moderate mean/five_rate filter (harsh 1=avg
    raters stay) but keep volume, lit depth, rare poll exposure, and low
    commercial 5★ pollution.
    """
    print("Percentile maps (literary-anchored Criticker midpoints)…", flush=True)
    con.execute("DROP TABLE IF EXISTS lit_signal_works")
    # Prefer work-collapsed signal table when present (built during likes).
    has_tsw = (
        con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'taste_signal_works'"
        ).fetchone()[0]
        > 0
    )
    if has_tsw:
        con.execute(
            """
            CREATE TABLE lit_signal_works AS
            SELECT DISTINCT work_id
            FROM taste_signal_works
            WHERE side = 'literary_poll'
            """
        )
    else:
        con.execute(
            """
            CREATE TABLE lit_signal_works AS
            SELECT DISTINCT btw.work_id::VARCHAR AS work_id
            FROM taste_signal_books s
            JOIN book_to_work btw ON s.book_id = btw.book_id::VARCHAR
            WHERE s.side = 'literary_poll'
            """
        )
    con.execute("CREATE INDEX idx_lsw ON lit_signal_works(work_id)")

    con.execute("DROP TABLE IF EXISTS user_star_percentiles")
    # Midpoint of each star's cumulative mass: (F_<k + F_≤k) / 2
    # full_counts come from shared user_star_hist (no second full scan).
    con.execute(
        """
        CREATE TABLE user_star_percentiles AS
        WITH lit_counts AS (
            SELECT
                e.user_id,
                count(*)::BIGINT AS n_lit_rated,
                count(*) FILTER (WHERE e.rating = 1)::BIGINT AS c1,
                count(*) FILTER (WHERE e.rating = 2)::BIGINT AS c2,
                count(*) FILTER (WHERE e.rating = 3)::BIGINT AS c3,
                count(*) FILTER (WHERE e.rating = 4)::BIGINT AS c4,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS c5,
                count(DISTINCT e.rating)::BIGINT AS n_levels
            FROM all_rating_events e
            JOIN lit_signal_works lw USING (work_id)
            GROUP BY e.user_id
        ),
        chosen AS (
            SELECT
                f.user_id,
                f.n_rated,
                coalesce(l.n_lit_rated, 0) AS n_lit_rated,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN 'lit' ELSE 'full' END AS source,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN l.n_lit_rated ELSE f.n_rated END AS n_cdf,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN l.c1 ELSE f.c1 END AS c1,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN l.c2 ELSE f.c2 END AS c2,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN l.c3 ELSE f.c3 END AS c3,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN l.c4 ELSE f.c4 END AS c4,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN l.c5 ELSE f.c5 END AS c5,
                CASE WHEN coalesce(l.n_lit_rated, 0) >= 20 THEN l.n_levels ELSE f.n_levels END AS n_levels
            FROM user_star_hist f
            LEFT JOIN lit_counts l USING (user_id)
            WHERE f.n_rated >= 20 AND f.n_levels >= 2
        )
        SELECT
            user_id,
            n_rated,
            n_lit_rated,
            n_cdf,
            n_levels,
            source,
            ((0.0 + (c1::DOUBLE / n_cdf)) / 2.0)::DOUBLE AS pct_1,
            (
                ((c1::DOUBLE / n_cdf) + ((c1 + c2)::DOUBLE / n_cdf)) / 2.0
            )::DOUBLE AS pct_2,
            (
                (((c1 + c2)::DOUBLE / n_cdf) + ((c1 + c2 + c3)::DOUBLE / n_cdf)) / 2.0
            )::DOUBLE AS pct_3,
            (
                (((c1 + c2 + c3)::DOUBLE / n_cdf)
                 + ((c1 + c2 + c3 + c4)::DOUBLE / n_cdf)) / 2.0
            )::DOUBLE AS pct_4,
            (
                (((c1 + c2 + c3 + c4)::DOUBLE / n_cdf) + 1.0) / 2.0
            )::DOUBLE AS pct_5
        FROM chosen
        """
    )
    con.execute("CREATE INDEX idx_usp_user ON user_star_percentiles(user_id)")
    n_pct = int(con.execute("SELECT count(*) FROM user_star_percentiles").fetchone()[0])
    n_lit_src = int(
        con.execute(
            "SELECT count(*) FROM user_star_percentiles WHERE source = 'lit'"
        ).fetchone()[0]
    )
    print(
        f"  percentile users: {n_pct:,} (literary-anchored: {n_lit_src:,})",
        flush=True,
    )

    print("Pct-curator weights (no mean gate; volume + lit + rarity)…", flush=True)
    con.execute("DROP TABLE IF EXISTS user_curator_pct_weight")
    con.execute(
        """
        CREATE TABLE user_curator_pct_weight AS
        WITH user_poll AS (
            SELECT
                e.user_id,
                count(DISTINCT e.work_id)::BIGINT AS n_poll_works,
                sum(p.rarity * p.prestige)::DOUBLE AS rarity_mass,
                max(p.rarity)::DOUBLE AS max_rarity,
                count(DISTINCT e.work_id) FILTER (
                    WHERE p.n <= (SELECT approx_quantile(n, 0.50) FROM poll_works)
                )::BIGINT AS n_rare_poll,
                -- High personal love on a poll work (top star OR pct≥0.75 via lit map)
                count(DISTINCT e.work_id) FILTER (
                    WHERE e.rating = m.max_star OR e.rating >= 4
                )::BIGINT AS n_poll_loved
            FROM all_rating_events e
            JOIN poll_works p USING (work_id)
            JOIN user_star_hist m USING (user_id)
            WHERE e.rating >= 3
            GROUP BY e.user_id
        ),
        base AS (
            SELECT
                w.user_id,
                w.lit_weight,
                w.lit_share,
                w.lit_hits,
                w.com_hits,
                u.five_rate,
                u.n_rated,
                m.mean_rating,
                m.c5 AS n5,
                m.max_star,
                pct.source AS pct_source,
                pct.n_levels,
                coalesce(up.n_poll_works, 0) AS n_poll_works,
                coalesce(up.rarity_mass, 0) AS rarity_mass,
                coalesce(up.max_rarity, 0) AS max_rarity,
                coalesce(up.n_rare_poll, 0) AS n_rare_poll,
                coalesce(up.n_poll_loved, 0) AS n_poll_loved,
                power(ln(1.0 + coalesce(up.rarity_mass, 0) * 5.0), 1.35) AS rarity_boost
            FROM user_lit_weight w
            JOIN user_pickiness u USING (user_id)
            JOIN user_star_hist m USING (user_id)
            JOIN user_star_percentiles pct USING (user_id)
            LEFT JOIN user_poll up USING (user_id)
            WHERE w.lit_hits >= 2
              AND w.com_hits <= greatest(5, cast(w.lit_hits * 0.65 AS BIGINT))
              AND u.n_rated >= 25
              AND pct.n_levels >= 2
              AND coalesce(up.n_poll_works, 0) >= 2
              AND coalesce(up.n_poll_loved, 0) >= 1
        ),
        norms AS (
            SELECT max(rarity_boost) AS max_boost FROM base
        ),
        scored AS (
            SELECT
                b.*,
                (
                    b.lit_weight
                    * (
                        0.30 + 0.70 * (
                            b.rarity_boost / nullif((SELECT max_boost FROM norms), 0)
                        )
                    )
                )::DOUBLE AS curator_pct_weight
            FROM base b
        )
        SELECT
            s.*,
            percent_rank() OVER (ORDER BY s.curator_pct_weight)::DOUBLE AS weight_pctile
        FROM scored s
        WHERE s.curator_pct_weight > 0
        """
    )
    con.execute("CREATE INDEX idx_ucpw_user ON user_curator_pct_weight(user_id)")
    n = int(con.execute("SELECT count(*) FROM user_curator_pct_weight").fetchone()[0])
    bounds = con.execute(
        "SELECT min(curator_pct_weight), max(curator_pct_weight), avg(curator_pct_weight) "
        "FROM user_curator_pct_weight"
    ).fetchone()
    print(
        f"  pct-curator users: {n:,} · "
        f"weight {bounds[0]:.3f}–{bounds[2]:.3f}–{bounds[1]:.3f}",
        flush=True,
    )
    pure_meta = _materialize_pure_curators(con)
    deep_meta = _materialize_deep_curators(con)
    return {
        "n_percentile_users": n_pct,
        "n_percentile_lit_anchored": n_lit_src,
        "n_curator_pct_users": n,
        "curator_pct_weight_min": float(bounds[0]) if bounds[0] is not None else None,
        "curator_pct_weight_avg": float(bounds[2]) if bounds[2] is not None else None,
        "curator_pct_weight_max": float(bounds[1]) if bounds[1] is not None else None,
        **pure_meta,
        **deep_meta,
    }


def _materialize_pure_curators(con) -> dict[str, Any]:
    """Stricter RYM-style cohort: few non-literary ★5s + high lit lean.

    Mirrors the taste-filter framing (literary depth without gushing over
    commercial anti-signals) baked into the curator weight itself.
    """
    print("Pure curators (strict anti-commercial + lit lean)…", flush=True)

    # Soft com share penalty: lit_share^1.25 × (1 − com_share)^2
    # Hard gates: lit_share ≥ 0.55, com_hits ≤ max(1, 0.18·lit), net ≥ 0.20
    con.execute("DROP TABLE IF EXISTS user_curator_pure_weight")
    con.execute(
        """
        CREATE TABLE user_curator_pure_weight AS
        WITH scored AS (
            SELECT
                c.user_id,
                c.lit_weight,
                c.lit_share,
                c.lit_hits,
                c.com_hits,
                c.five_rate,
                c.mean_rating,
                c.n_rated,
                c.n5,
                c.n_poll_works,
                c.rarity_mass,
                c.max_rarity,
                c.n_rare_poll,
                c.has_five,
                c.moderate_gate,
                c.rarity_boost,
                (
                    c.curator_weight
                    * power(greatest(coalesce(c.lit_share, 0), 0.01), 1.25)
                    * power(greatest(
                        1.0 - coalesce(c.com_hits, 0)::DOUBLE
                            / nullif(c.lit_hits + c.com_hits, 0),
                        0.05
                    ), 2.0)
                )::DOUBLE AS curator_weight
            FROM user_curator_weight c
            WHERE c.lit_share >= 0.55
              AND c.com_hits <= greatest(1, cast(c.lit_hits * 0.18 AS BIGINT))
              AND (c.lit_hits - c.com_hits)::DOUBLE
                    / nullif(c.lit_hits + c.com_hits, 0) >= 0.20
        )
        SELECT
            s.*,
            percent_rank() OVER (ORDER BY s.curator_weight)::DOUBLE AS weight_pctile
        FROM scored s
        WHERE s.curator_weight > 0
        """
    )
    con.execute("CREATE INDEX idx_ucpure_user ON user_curator_pure_weight(user_id)")
    n_star = int(con.execute("SELECT count(*) FROM user_curator_pure_weight").fetchone()[0])

    con.execute("DROP TABLE IF EXISTS user_curator_pct_pure_weight")
    con.execute(
        """
        CREATE TABLE user_curator_pct_pure_weight AS
        WITH scored AS (
            SELECT
                c.user_id,
                c.lit_weight,
                c.lit_share,
                c.lit_hits,
                c.com_hits,
                c.five_rate,
                c.mean_rating,
                c.n_rated,
                c.n5,
                c.max_star,
                c.pct_source,
                c.n_levels,
                c.n_poll_works,
                c.rarity_mass,
                c.max_rarity,
                c.n_rare_poll,
                c.n_poll_loved,
                c.rarity_boost,
                (
                    c.curator_pct_weight
                    * power(greatest(coalesce(c.lit_share, 0), 0.01), 1.25)
                    * power(greatest(
                        1.0 - coalesce(c.com_hits, 0)::DOUBLE
                            / nullif(c.lit_hits + c.com_hits, 0),
                        0.05
                    ), 2.0)
                )::DOUBLE AS curator_pct_weight
            FROM user_curator_pct_weight c
            WHERE c.lit_share >= 0.55
              AND c.com_hits <= greatest(1, cast(c.lit_hits * 0.18 AS BIGINT))
              AND (c.lit_hits - c.com_hits)::DOUBLE
                    / nullif(c.lit_hits + c.com_hits, 0) >= 0.20
              AND c.n_poll_works >= 3
              AND c.lit_hits >= 4
        )
        SELECT
            s.*,
            percent_rank() OVER (ORDER BY s.curator_pct_weight)::DOUBLE AS weight_pctile
        FROM scored s
        WHERE s.curator_pct_weight > 0
        """
    )
    con.execute("CREATE INDEX idx_ucppure_user ON user_curator_pct_pure_weight(user_id)")
    n_pct = int(
        con.execute("SELECT count(*) FROM user_curator_pct_pure_weight").fetchone()[0]
    )
    bounds = con.execute(
        "SELECT min(curator_pct_weight), max(curator_pct_weight), avg(curator_pct_weight) "
        "FROM user_curator_pct_pure_weight"
    ).fetchone()
    print(
        f"  pure star curators: {n_star:,} · pure pct curators: {n_pct:,} · "
        f"pct weight {bounds[0]:.3f}–{bounds[2]:.3f}–{bounds[1]:.3f}",
        flush=True,
    )
    return {
        "n_curator_pure_users": n_star,
        "n_curator_pct_pure_users": n_pct,
        "curator_pct_pure_weight_min": float(bounds[0]) if bounds[0] is not None else None,
        "curator_pct_pure_weight_avg": float(bounds[2]) if bounds[2] is not None else None,
        "curator_pct_pure_weight_max": float(bounds[1]) if bounds[1] is not None else None,
    }


def _load_normie_titles() -> list[str]:
    if not NORMIE_PATH.exists():
        return []
    data = json.loads(NORMIE_PATH.read_text(encoding="utf-8"))
    titles = data.get("titles") or []
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for t in titles:
        t = (t or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _deep_curator_defaults() -> dict[str, float | int]:
    """Load tuned gates from deep_curator_params.json when present.

    Materialization uses a *loose* floor so query-time normie_strictness can
    tighten or relax. Historical tuned values (share≥0.60, n_deep≥4) are the
    query-time default at normie_strictness=0 — see ranking.normie_strictness_params.
    """
    defaults: dict[str, float | int] = {
        "min_deep": 2,
        "min_deep_rare": 1,
        "min_deep_share": 0.35,
        "deep_exp": 1.8,
        "rarity_mix": 0.90,
        # Non-literary anti-signal pollution (com_hits / (lit+com)).
        "max_com_share": 0.20,
        "com_exp": 3.0,
    }
    path = Path(__file__).resolve().parent / "data" / "deep_curator_params.json"
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for k in defaults:
                if k in raw:
                    defaults[k] = type(defaults[k])(raw[k])
        except Exception:
            pass
    return defaults


def _materialize_deep_curators(
    con,
    *,
    min_deep: int | None = None,
    min_deep_rare: int | None = None,
    min_deep_share: float | None = None,
    deep_exp: float | None = None,
    rarity_mix: float | None = None,
    max_com_share: float | None = None,
    com_exp: float | None = None,
) -> dict[str, Any]:
    """Curators who go past normie prestige into rarer poll/chart works.

    Normie canon (school staples / ubiquitous 'quality') does not mint weight by
    itself — same idea as not following RYM users who only log Kubrick/Hitchcock.

    Commercial anti-signals (non_literary ★=5 hits) also shape the cohort:
    users above max_com_share are dropped, and remaining weights are scaled by
    (1 - com_share)^com_exp so "great taste + a few trash 5★s" is downweighted.
    """
    dflt = _deep_curator_defaults()
    min_deep = int(dflt["min_deep"] if min_deep is None else min_deep)
    min_deep_rare = int(dflt["min_deep_rare"] if min_deep_rare is None else min_deep_rare)
    min_deep_share = float(
        dflt["min_deep_share"] if min_deep_share is None else min_deep_share
    )
    deep_exp = float(dflt["deep_exp"] if deep_exp is None else deep_exp)
    rarity_mix = float(dflt["rarity_mix"] if rarity_mix is None else rarity_mix)
    max_com_share = float(
        dflt["max_com_share"] if max_com_share is None else max_com_share
    )
    com_exp = float(dflt["com_exp"] if com_exp is None else com_exp)

    print("Deep curators (non-normie poll depth)…", flush=True)
    titles = _load_normie_titles()
    if not titles:
        print("  no normie_canon.json titles — skipping deep cohort", flush=True)
        return {"n_curator_deep_users": 0, "n_normie_works": 0, "n_deep_poll_works": 0}

    con.execute("DROP TABLE IF EXISTS normie_works")
    con.execute("CREATE TABLE normie_works (work_id VARCHAR, title VARCHAR)")
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for t in titles:
        hits = con.execute(
            """
            SELECT work_id, title FROM work_scores
            WHERE title = ? OR title ILIKE ? || ' (%'
            ORDER BY n DESC
            LIMIT 2
            """,
            [t, t],
        ).fetchall()
        if not hits:
            hits = con.execute(
                """
                SELECT work_id, title FROM work_scores
                WHERE title ILIKE ?
                ORDER BY n DESC
                LIMIT 1
                """,
                [t + "%"],
            ).fetchall()
        for wid, title in hits:
            if wid not in seen:
                seen.add(wid)
                rows.append((str(wid), str(title)))
    con.executemany("INSERT INTO normie_works VALUES (?, ?)", rows)
    con.execute("CREATE INDEX idx_normie_work ON normie_works(work_id)")

    con.execute("DROP TABLE IF EXISTS deep_poll_works")
    con.execute(
        """
        CREATE TABLE deep_poll_works AS
        SELECT p.*
        FROM poll_works p
        WHERE p.work_id NOT IN (SELECT work_id FROM normie_works)
        """
    )
    con.execute("CREATE INDEX idx_deep_poll ON deep_poll_works(work_id)")
    n_deep_poll = int(con.execute("SELECT count(*) FROM deep_poll_works").fetchone()[0])

    con.execute("DROP TABLE IF EXISTS user_curator_deep_weight")
    con.execute(
        f"""
        CREATE TABLE user_curator_deep_weight AS
        WITH user_deep AS (
            SELECT
                e.user_id,
                count(DISTINCT e.work_id)::BIGINT AS n_deep,
                count(DISTINCT e.work_id) FILTER (
                    WHERE d.n <= (SELECT approx_quantile(n, 0.55) FROM deep_poll_works)
                )::BIGINT AS n_deep_rare,
                sum(d.rarity * d.prestige)::DOUBLE AS deep_mass
            FROM all_rating_events e
            JOIN deep_poll_works d USING (work_id)
            WHERE e.rating >= 4
            GROUP BY e.user_id
        ),
        user_normie AS (
            SELECT
                e.user_id,
                count(DISTINCT e.work_id)::BIGINT AS n_normie
            FROM all_rating_events e
            JOIN normie_works n USING (work_id)
            WHERE e.rating >= 4
            GROUP BY e.user_id
        ),
        base AS (
            SELECT
                c.user_id,
                c.lit_weight,
                c.lit_share,
                c.lit_hits,
                c.com_hits,
                c.five_rate,
                c.mean_rating,
                c.n_rated,
                c.n5,
                c.max_star,
                c.pct_source,
                c.n_levels,
                c.n_poll_works,
                c.rarity_mass,
                c.max_rarity,
                c.n_rare_poll,
                c.n_poll_loved,
                c.curator_pct_weight AS base_w,
                d.n_deep,
                d.n_deep_rare,
                d.deep_mass,
                coalesce(n.n_normie, 0) AS n_normie,
                d.n_deep::DOUBLE
                    / nullif(d.n_deep + coalesce(n.n_normie, 0), 0) AS deep_share,
                coalesce(c.com_hits, 0)::DOUBLE
                    / nullif(
                        coalesce(c.lit_hits, 0) + coalesce(c.com_hits, 0), 0
                    ) AS com_share,
                power(ln(1.0 + d.deep_mass * 5.0), 1.35) AS deep_boost
            FROM user_curator_pct_weight c
            JOIN user_deep d USING (user_id)
            LEFT JOIN user_normie n USING (user_id)
            WHERE d.n_deep >= {int(min_deep)}
              AND d.n_deep_rare >= {int(min_deep_rare)}
              AND d.n_deep::DOUBLE
                    / nullif(d.n_deep + coalesce(n.n_normie, 0), 0)
                    >= {float(min_deep_share)}
              AND coalesce(c.com_hits, 0)::DOUBLE
                    / nullif(
                        coalesce(c.lit_hits, 0) + coalesce(c.com_hits, 0), 0
                    ) <= {float(max_com_share)}
        ),
        norms AS (
            SELECT max(deep_boost) AS mx FROM base
        ),
        scored AS (
            SELECT
                b.*,
                (
                    b.base_w
                    * power(greatest(b.deep_share, 0.05), {float(deep_exp)})
                    * (
                        {1.0 - float(rarity_mix)}
                        + {float(rarity_mix)} * b.deep_boost
                            / nullif((SELECT mx FROM norms), 0)
                    )
                    * power(
                        greatest(1.0 - coalesce(b.com_share, 0), 0.02),
                        {float(com_exp)}
                    )
                )::DOUBLE AS curator_pct_weight
            FROM base b
        )
        SELECT
            s.*,
            percent_rank() OVER (ORDER BY s.curator_pct_weight)::DOUBLE AS weight_pctile
        FROM scored s
        WHERE s.curator_pct_weight > 0
        """
    )
    con.execute("CREATE INDEX idx_ucdeep_user ON user_curator_deep_weight(user_id)")
    n = int(con.execute("SELECT count(*) FROM user_curator_deep_weight").fetchone()[0])
    bounds = con.execute(
        "SELECT min(curator_pct_weight), max(curator_pct_weight), avg(curator_pct_weight) "
        "FROM user_curator_deep_weight"
    ).fetchone()
    com_stats = con.execute(
        """
        SELECT
          avg(com_share),
          approx_quantile(com_share, 0.9),
          count(*) FILTER (WHERE com_share > 0.10)
        FROM user_curator_deep_weight
        """
    ).fetchone()
    print(
        f"  normie works: {len(rows):,} · deep poll works: {n_deep_poll:,} · "
        f"deep curators: {n:,} · weight {bounds[0]:.3f}–{bounds[2]:.3f}–{bounds[1]:.3f}",
        flush=True,
    )
    print(
        f"  com_share avg={com_stats[0]:.3f} p90={com_stats[1]:.3f} "
        f">10%={int(com_stats[2]):,} · mint max_com_share={max_com_share:.2f} "
        f"com_exp={com_exp:.1f}",
        flush=True,
    )
    return {
        "n_normie_works": len(rows),
        "n_deep_poll_works": n_deep_poll,
        "n_curator_deep_users": n,
        "deep_min_deep": min_deep,
        "deep_min_deep_rare": min_deep_rare,
        "deep_min_deep_share": min_deep_share,
        "deep_max_com_share": max_com_share,
        "deep_com_exp": com_exp,
        "curator_deep_weight_min": float(bounds[0]) if bounds[0] is not None else None,
        "curator_deep_weight_avg": float(bounds[2]) if bounds[2] is not None else None,
        "curator_deep_weight_max": float(bounds[1]) if bounds[1] is not None else None,
    }


def _author_index(con) -> dict[str, tuple[str, str, int]]:
    """fold(name) → (author_id, name, ratings_count). Prefer higher ratings_count."""
    rows = con.execute(
        "SELECT author_id, name, coalesce(ratings_count, 0) FROM authors"
    ).fetchall()
    by_fold: dict[str, tuple[str, str, int]] = {}
    for aid, name, rc in rows:
        if not name:
            continue
        f = fold(name)
        rc_i = int(rc or 0)
        if f not in by_fold or rc_i > by_fold[f][2]:
            by_fold[f] = (str(aid), name, rc_i)
    return by_fold


def resolve_author(
    name: str, by_fold: dict[str, tuple[str, str, int]]
) -> Optional[tuple[str, str]]:
    """Resolve a display name to (author_id, resolved_name).

    Tries aliases and prefers the Goodreads author with the most ratings
    (so 'Fyodor Dostoevsky' → Dostoyevsky 3137322, not the 100-rating stub).
    """
    candidates = [name] + NAME_ALIASES.get(fold(name), [])
    found: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for cand in candidates:
        f = fold(cand)
        for key in (f, re.sub(r"\s+", " ", re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", f).strip())):
            if key in by_fold and by_fold[key][0] not in seen:
                found.append(by_fold[key])
                seen.add(by_fold[key][0])
    if not found:
        f = fold(name)
        near = [
            v
            for k, v in by_fold.items()
            if k == f or k.startswith(f + " ") or f.startswith(k + " ")
        ]
        if len(near) == 1:
            found = near
        else:
            hits = [
                v
                for k, v in by_fold.items()
                if f == k or (len(f) > 6 and (f in k or k in f))
            ]
            if len(hits) == 1:
                found = hits
    if not found:
        return None
    best = max(found, key=lambda t: t[2])
    return best[0], best[1]


def _sigs(taste: dict[str, Any], key: str) -> list[dict[str, str]]:
    raw = taste.get(key)
    if key == "non_literary" and not raw:
        raw = taste.get("commercial")  # back-compat
    out = []
    for sig in raw or []:
        if sig.get("kind") != "author":
            continue
        match = (sig.get("match") or "").strip()
        if match:
            out.append({"kind": "author", "match": match})
    return out


def resolve_lists(taste: dict[str, Any] | None = None) -> dict[str, list[dict[str, str]]]:
    """Resolve signal authors to Goodreads author_ids by bucket."""
    import duckdb

    taste = taste or load_taste_lists()
    con = duckdb.connect(str(WAREHOUSE_DB), read_only=True)
    try:
        by_fold = _author_index(con)
    finally:
        con.close()

    buckets = {
        "literary_poll": _sigs(taste, "literary"),
        "literary_sf": _sigs(taste, "literary_sf_extras"),
        "non_literary": _sigs(taste, "non_literary"),
    }
    out: dict[str, list[dict[str, str]]] = {
        "literary_poll": [],
        "literary_sf": [],
        "non_literary": [],
    }
    seen: set[str] = set()
    # non_literary wins overlaps
    for side in ("non_literary", "literary_poll", "literary_sf"):
        for sig in buckets[side]:
            resolved = resolve_author(sig["match"], by_fold)
            if not resolved:
                continue
            aid, rname = resolved
            if aid in seen:
                continue
            seen.add(aid)
            out[side].append(
                {
                    "kind": "author",
                    "match": sig["match"],
                    "author_id": aid,
                    "resolved_name": rname,
                }
            )
    return out


def materialize_taste(*, min_liked: int = 4) -> dict[str, Any]:
    """Write taste tables into explorer.duckdb (does not rebuild rating tables)."""
    import duckdb

    if not EXPLORER_DB.exists():
        raise SystemExit(
            f"Missing {EXPLORER_DB}. Run:\n"
            "  .venv/bin/python -m ucsd_explorer.materialize_ratings"
        )
    ix_pq = PARQUET / "interactions.parquet"
    books_pq = PARQUET / "books.parquet"
    if not books_pq.exists():
        raise SystemExit(f"Need {books_pq}")

    t0 = time.time()
    resolved = resolve_lists()
    poll = resolved["literary_poll"]
    sf = resolved["literary_sf"]
    nonlit = resolved["non_literary"]
    if not poll and not nonlit:
        raise SystemExit("No authors resolved from taste_lists.json")

    prestige_map = author_poll_prestige(
        literary_matches=[s["match"] for s in poll],
    )
    for s in poll:
        info = prestige_map.get(fold(s["match"])) or {}
        s["poll_rank"] = info.get("poll_rank")
        s["poll_title"] = info.get("poll_title")
        s["prestige"] = float(info.get("prestige") or 0.25)
    for s in sf:
        s["poll_rank"] = None
        s["poll_title"] = None
        s["prestige"] = float(SF_EXTRA_PRESTIGE)
    for s in nonlit:
        s["poll_rank"] = None
        s["poll_title"] = None
        s["prestige"] = 0.0

    base = load_taste_lists()
    base["resolved"] = resolved
    base["poll_prestige_floor"] = POLL_PRESTIGE_FLOOR
    # keep convenience mirrors
    base["literary"] = [{"kind": "author", "match": s["match"]} for s in poll]
    base["literary_sf_extras"] = [{"kind": "author", "match": s["match"]} for s in sf]
    base["non_literary"] = [{"kind": "author", "match": s["match"]} for s in nonlit]
    base["commercial"] = base["non_literary"]  # alias
    TASTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TASTE_PATH.write_text(json.dumps(base, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    static = {
        "literary": base["literary"],
        "literary_sf_extras": base["literary_sf_extras"],
        "non_literary": base["non_literary"],
        "notes": base.get("notes"),
        "dropped_from_literary": base.get("dropped_from_literary"),
        "non_literary_audit": base.get("non_literary_audit"),
    }
    STATIC_TASTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATIC_TASTE_PATH.write_text(
        json.dumps(static, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    rows = (
        [
            (s["author_id"], "literary_poll", s["match"], s["prestige"], s.get("poll_rank"))
            for s in poll
        ]
        + [
            (s["author_id"], "literary_sf", s["match"], s["prestige"], None)
            for s in sf
        ]
        + [
            (s["author_id"], "non_literary", s["match"], 0.0, None)
            for s in nonlit
        ]
    )

    con = duckdb.connect(str(EXPLORER_DB))
    _configure_duckdb(con)
    for t in (
        "taste_authors",
        "taste_signal_books",
        "taste_signal_works",
        "user_author_likes",
        "user_taste",
        "user_lit_weight",
        "poll_works",
        "user_curator_weight",
        "user_curator_pct_weight",
        "user_curator_pure_weight",
        "user_curator_pct_pure_weight",
        "user_curator_deep_weight",
        "normie_works",
        "deep_poll_works",
        "user_star_percentiles",
        "user_star_hist",
        "lit_signal_works",
    ):
        con.execute(f"DROP TABLE IF EXISTS {t}")

    con.execute(
        """
        CREATE TABLE taste_authors (
            author_id VARCHAR,
            side VARCHAR,
            match_name VARCHAR,
            prestige DOUBLE,
            poll_rank INTEGER
        )
        """
    )
    con.executemany("INSERT INTO taste_authors VALUES (?, ?, ?, ?, ?)", rows)

    print(
        f"Taste authors: {len(poll)} poll literary, {len(sf)} SF extras, "
        f"{len(nonlit)} non-literary — mapping books…",
        flush=True,
    )
    top = sorted(poll, key=lambda s: -(s.get("prestige") or 0))[:5]
    print(
        "  top prestige: "
        + ", ".join(
            f"{s['match']}(#{s.get('poll_rank')},{s['prestige']:.2f})" for s in top
        ),
        flush=True,
    )
    con.execute(
        f"""
        CREATE TABLE taste_signal_books AS
        SELECT
            b.book_id::VARCHAR AS book_id,
            t.author_id,
            t.side,
            t.prestige,
            t.poll_rank
        FROM read_parquet('{books_pq}') b
        JOIN taste_authors t ON b.author_id::VARCHAR = t.author_id
        """
    )
    n_books = con.execute("SELECT count(*) FROM taste_signal_books").fetchone()[0]
    print(f"  signal books: {n_books:,}", flush=True)

    print("User×author likes from work-collapsed ratings…", flush=True)
    # Work-level (edition-collapsed) is faster and avoids double-counting editions.
    # Filter to signal works first so we don't touch the full interactions parquet.
    con.execute("DROP TABLE IF EXISTS taste_signal_works")
    con.execute(
        """
        CREATE TABLE taste_signal_works AS
        SELECT
            btw.work_id::VARCHAR AS work_id,
            s.author_id,
            s.side,
            max(s.prestige)::DOUBLE AS prestige
        FROM taste_signal_books s
        JOIN book_to_work btw ON s.book_id = btw.book_id::VARCHAR
        GROUP BY 1, 2, 3
        """
    )
    con.execute("CREATE INDEX idx_tsw_work ON taste_signal_works(work_id)")
    con.execute(
        f"""
        CREATE TABLE user_author_likes AS
        SELECT
            e.user_id,
            s.author_id,
            s.side,
            max(s.prestige)::DOUBLE AS prestige,
            count(*) FILTER (WHERE e.rating >= {int(min_liked)})::BIGINT AS n_liked,
            sum(CASE WHEN e.rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n_five
        FROM all_rating_events e
        JOIN taste_signal_works s USING (work_id)
        GROUP BY 1, 2, 3
        """
    )

    # Default user_taste = poll literary (≥4) vs non-literary (5★ only), SF extras off
    con.execute(
        """
        CREATE TABLE user_taste AS
        WITH agg AS (
            SELECT
                user_id,
                sum(CASE WHEN side = 'literary_poll' THEN n_liked ELSE 0 END)::BIGINT AS lit_hits,
                sum(CASE WHEN side = 'non_literary' THEN n_five ELSE 0 END)::BIGINT AS com_hits,
                sum(CASE WHEN side = 'literary_poll' THEN n_five ELSE 0 END)::BIGINT AS lit_fives,
                sum(CASE WHEN side = 'non_literary' THEN n_five ELSE 0 END)::BIGINT AS com_fives,
                sum(CASE WHEN side = 'literary_sf' THEN n_liked ELSE 0 END)::BIGINT AS lit_sf_hits,
                sum(
                    CASE WHEN side = 'literary_poll'
                         THEN coalesce(prestige, 0) * n_liked ELSE 0 END
                )::DOUBLE AS lit_mass
            FROM user_author_likes
            GROUP BY user_id
        )
        SELECT
            user_id,
            lit_hits,
            com_hits,
            lit_fives,
            com_fives,
            lit_sf_hits,
            lit_mass,
            lit_hits::DOUBLE / nullif(lit_hits + com_hits, 0) AS lit_share,
            com_hits::DOUBLE / nullif(lit_hits + com_hits, 0) AS com_share,
            (
                coalesce(lit_hits::DOUBLE / nullif(lit_hits + com_hits, 0), 0)
                - coalesce(com_hits::DOUBLE / nullif(lit_hits + com_hits, 0), 0)
            ) AS net_share
        FROM agg
        WHERE lit_hits + com_hits > 0
        """
    )
    con.execute("CREATE INDEX idx_user_taste ON user_taste(user_id)")
    con.execute("CREATE INDEX idx_ual_user ON user_author_likes(user_id)")
    con.execute("CREATE INDEX idx_ual_side ON user_author_likes(side)")

    # Literary depth weight: lit_share × ln(1 + prestige-weighted lit mass)
    # Top-of-poll likes count more than bottom-of-poll likes.
    con.execute(
        """
        CREATE TABLE user_lit_weight AS
        SELECT
            user_id,
            lit_hits,
            com_hits,
            lit_mass,
            lit_share,
            com_share,
            net_share,
            greatest(0.0, coalesce(lit_share, 0))
                * ln(1.0 + greatest(coalesce(lit_mass, 0), 0)) AS lit_weight,
            greatest(0.0, coalesce(net_share, 0))
                * ln(1.0 + greatest(coalesce(lit_mass, 0), 0)) AS lit_net_weight
        FROM user_taste
        WHERE lit_hits > 0
        """
    )
    con.execute("CREATE INDEX idx_ulw_user ON user_lit_weight(user_id)")

    poll_works = match_poll_works(con)
    print(
        f"  poll chart works matched: {len(poll_works)}/{len(parse_poll_chart())}",
        flush=True,
    )
    if poll_works:
        rare = sorted(poll_works, key=lambda p: p["n"])[:8]
        print(
            "  rarest matched: "
            + ", ".join(f"{p['poll_title']}(n={p['n']})" for p in rare),
            flush=True,
        )
    curator_meta = _materialize_curator_weights(con, poll_works)

    # Speed up similar-books (fan → co-favorites)
    try:
        con.execute("CREATE INDEX IF NOT EXISTS idx_fse_user ON five_star_events(user_id)")
    except Exception:
        pass

    n_users = con.execute("SELECT count(*) FROM user_taste").fetchone()[0]
    sample = con.execute(
        """
        SELECT
            count(*) FILTER (WHERE lit_share >= 0.5) AS lit_lean,
            count(*) FILTER (WHERE com_share >= 0.5) AS nonlit_lean
        FROM user_taste
        """
    ).fetchone()
    con.close()

    meta = {
        "n_literary_poll_authors": len(poll),
        "n_literary_sf_authors": len(sf),
        "n_non_literary_authors": len(nonlit),
        "n_signal_books": int(n_books),
        "n_users_with_taste": int(n_users),
        "min_liked_literary": min_liked,
        "non_literary_uses_fives_only": True,
        "poll_prestige_floor": POLL_PRESTIGE_FLOOR,
        "lit_lean_users": int(sample[0] or 0),
        "nonlit_lean_users": int(sample[1] or 0),
        "elapsed_s": round(time.time() - t0, 1),
        **curator_meta,
    }
    print(
        f"user_taste: {n_users:,} users (poll lit vs non-lit 5★; SF extras off by default) "
        f"lit-lean≥50%: {meta['lit_lean_users']:,}, nonlit-lean≥50%: {meta['nonlit_lean_users']:,} "
        f"in {meta['elapsed_s']}s",
        flush=True,
    )
    return meta


def main() -> None:
    import argparse

    import duckdb

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--min-liked",
        type=int,
        default=4,
        help="Min stars for a *literary* taste hit (non-literary always uses 5★ only)",
    )
    p.add_argument(
        "--deep-only",
        action="store_true",
        help="Rebuild deep (non-normie) curator tables from existing pct weights (fast)",
    )
    p.add_argument(
        "--pure-only",
        action="store_true",
        help="Rebuild pure curator tables from existing curator weights (fast)",
    )
    p.add_argument(
        "--curators-only",
        action="store_true",
        help="Rebuild curator/percentile tables from existing lit weights (skips likes)",
    )
    args = p.parse_args()
    if args.deep_only:
        con = duckdb.connect(str(EXPLORER_DB))
        _configure_duckdb(con)
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        need = {"user_curator_pct_weight", "poll_works", "work_scores", "all_rating_events"}
        missing = need - tables
        if missing:
            raise SystemExit(
                f"Missing {sorted(missing)}; run full taste materialize first."
            )
        meta = _materialize_deep_curators(con)
        con.close()
        print(json.dumps(meta, indent=2), flush=True)
        return
    if args.pure_only:
        con = duckdb.connect(str(EXPLORER_DB))
        _configure_duckdb(con)
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        need = {"user_curator_weight", "user_curator_pct_weight"}
        missing = need - tables
        if missing:
            raise SystemExit(
                f"Missing {sorted(missing)}; run full taste materialize first."
            )
        meta = _materialize_pure_curators(con)
        con.close()
        print(json.dumps(meta, indent=2), flush=True)
        return
    if args.curators_only:
        con = duckdb.connect(str(EXPLORER_DB))
        _configure_duckdb(con)
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        need = {"user_lit_weight", "user_pickiness", "all_rating_events", "taste_signal_books"}
        missing = need - tables
        if missing:
            raise SystemExit(
                f"Missing {sorted(missing)}; run full taste materialize first."
            )
        t0 = time.time()
        poll_works = match_poll_works(con)
        print(
            f"  poll chart works matched: {len(poll_works)}/{len(parse_poll_chart())}",
            flush=True,
        )
        meta = _materialize_curator_weights(con, poll_works)
        meta["elapsed_s"] = round(time.time() - t0, 1)
        con.close()
        print(json.dumps(meta, indent=2), flush=True)
        return
    materialize_taste(min_liked=args.min_liked)


if __name__ == "__main__":
    main()

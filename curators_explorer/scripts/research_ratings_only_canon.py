#!/usr/bin/env python3
"""Ratings-only literary consensus experiments.

Allowed discovery signal: (user_id, work_id, rating) only
(plus counts derived from that). No author piles, genres, titles, or
sociodemographics enter scoring.

Evaluation labels (literary_poll / non_literary / normie) are used ONLY
to score methods after the fact.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_ratings_only_canon
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from curators_explorer.db import DB_PATH, LEGACY_NORMIE_PATH, LEGACY_TASTE_PATH

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "ratings_only_canon.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "RATINGS_ONLY_CANON_REPORT.md"

MIN_WORK_N = 25
MIN_USER_N = 20
MIN_RANK_N = 100  # avoid vanity-press heads in consensus lists
TOP_N = 200
FETCH = 2000

# Paper notes (discovery still ratings-only; these guide which graph metrics we try):
# - Lizardo 2018: method of reflections on person×item bipartite taste; δ^2 =
#   2nd-order popularity; low δ^2 ≈ audiences who also choose niche forms.
# - Airoldi 2024: legitimacy is nested + relational → multi-community heads,
#   not one global axis.
# - Feldkamp et al. 2024: expert/canonical proxies often *anti*-correlate with
#   Goodreads means; genre awards align more with popular than canonical.
# - Walsh & Antoniak: Goodreads "classics" are school/industry constructions;
#   crowd tags ≠ academic canon.


def _quantile(
    con, sql_expr: str, q: float, *, table: str = "user_feat", where: str = "TRUE"
) -> float:
    """approx_quantile needs FLOAT quantile, not DOUBLE."""
    return float(
        con.execute(
            f"SELECT approx_quantile(({sql_expr})::DOUBLE, ?::FLOAT) FROM {table} WHERE {where}",
            [float(q)],
        ).fetchone()[0]
    )


def _con():
    import duckdb

    con = duckdb.connect()
    con.execute(f"ATTACH '{DB_PATH}' AS ex (READ_ONLY)")
    con.execute("USE ex")
    return con


def load_eval_sets(con) -> dict[str, Any]:
    taste = json.loads(LEGACY_TASTE_PATH.read_text(encoding="utf-8"))
    normie = json.loads(LEGACY_NORMIE_PATH.read_text(encoding="utf-8"))
    pos_aids = {str(s["author_id"]) for s in taste["resolved"]["literary_poll"]}
    anti_aids = {str(s["author_id"]) for s in taste["resolved"]["non_literary"]}

    # Map authors → works via taste_authors + book authors is hard without authors table.
    # Use title/author string match against work_scores for eval probes (eval only).
    pos_names = {
        (s.get("resolved_name") or s["match"]).lower()
        for s in taste["resolved"]["literary_poll"]
    }
    anti_names = {
        (s.get("resolved_name") or s["match"]).lower()
        for s in taste["resolved"]["non_literary"]
    }
    # Prefer work_id sets from taste signal works if present.
    pos_works: set[str] = set()
    anti_works: set[str] = set()
    try:
        rows = con.execute(
            """
            SELECT DISTINCT work_id, side
            FROM taste_signal_works
            WHERE side IN ('literary_poll', 'non_literary')
            """
        ).fetchall()
        for wid, side in rows:
            if side == "literary_poll":
                pos_works.add(str(wid))
            else:
                anti_works.add(str(wid))
    except Exception:
        pass

    # Fallback: author name match on work_scores.author
    if len(pos_works) < 20:
        rows = con.execute(
            "SELECT work_id, author FROM work_scores WHERE n >= ?",
            [MIN_WORK_N],
        ).fetchall()
        for wid, author in rows:
            a = (author or "").lower()
            if any(n in a for n in pos_names):
                pos_works.add(str(wid))
            if any(n in a for n in anti_names):
                anti_works.add(str(wid))

    # Normie fillers: canon titles that are not also positive literary
    titles = list(normie.get("titles") or [])
    normie_works: set[str] = set()
    for t in titles:
        rows = con.execute(
            """
            SELECT work_id, title, author FROM work_scores
            WHERE lower(title) = lower(?)
               OR lower(title) LIKE lower(?) || ' (%'
            ORDER BY n DESC LIMIT 3
            """,
            [t, t],
        ).fetchall()
        for wid, title, author in rows:
            normie_works.add(str(wid))

    fillers = {w for w in normie_works if w not in pos_works}
    return {
        "pos_works": pos_works,
        "anti_works": anti_works,
        "normie_works": normie_works,
        "filler_works": fillers,
        "pos_names": sorted(pos_names)[:5],
        "n_pos_works": len(pos_works),
        "n_anti_works": len(anti_works),
        "n_fillers": len(fillers),
    }


def catalog_ok_sql(alias: str = "s") -> str:
    """Fiction-ish catalog hygiene using precomputed flags when present."""
    return f"""
      AND NOT coalesce(cf.is_excluded, FALSE)
      AND NOT coalesce(cf.is_nonfiction, FALSE)
      AND NOT coalesce(cf.is_comic, FALSE)
      AND NOT coalesce(cf.is_picture_book, FALSE)
      AND NOT coalesce(cf.is_derivative, FALSE)
      AND NOT coalesce(cf.is_duplicate, FALSE)
      AND NOT coalesce(cf.is_collection, FALSE)
    """


def materialize_base(con) -> None:
    """Ratings-derived tables only (in the ephemeral duckdb, reading from ex)."""
    print("Materializing ratings-only features…", flush=True)
    t0 = time.time()
    # Work popularity / rarity from the rating matrix.
    con.execute("USE memory")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE work_pop AS
        SELECT
            e.work_id,
            count(*)::BIGINT AS n,
            count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5,
            avg(e.rating)::DOUBLE AS mean
        FROM ex.all_rating_events e
        GROUP BY e.work_id
        HAVING count(*) >= {MIN_WORK_N}
        """
    )
    # rarity in (0,1]: high for obscure books
    con.execute(
        """
        CREATE OR REPLACE TABLE work_rarity AS
        SELECT
            work_id,
            n,
            n5,
            mean,
            (1.0 / ln(1.0 + n))::DOUBLE AS rarity,
            (n5::DOUBLE / n)::DOUBLE AS p5
        FROM work_pop
        """
    )
    # User rating stats + depth = mean rarity of ★≥4 (ratings-only "taste depth")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_feat AS
        SELECT
            e.user_id,
            count(*)::BIGINT AS n_rated,
            avg(e.rating)::DOUBLE AS mean_rating,
            (count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*))::DOUBLE AS five_rate,
            avg(r.rarity) FILTER (WHERE e.rating >= 4)::DOUBLE AS depth_ge4,
            avg(r.rarity) FILTER (WHERE e.rating = 5)::DOUBLE AS depth_5,
            -- Engaged readers: also touch mid/popular books (not only obscure vanity)
            count(*) FILTER (WHERE e.rating >= 4 AND r.n >= 500)::BIGINT AS n_ge4_midpop,
            count(*) FILTER (WHERE e.rating >= 4 AND r.n >= 5000)::BIGINT AS n_ge4_popular,
            avg(ln(1.0 + r.n)) FILTER (WHERE e.rating = 5)::DOUBLE AS mean_logn_5,
            count(*) FILTER (WHERE e.rating >= 4)::BIGINT AS n_ge4,
            count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
        FROM ex.all_rating_events e
        JOIN work_rarity r USING (work_id)
        GROUP BY e.user_id
        HAVING count(*) >= {MIN_USER_N}
           AND count(*) FILTER (WHERE e.rating >= 4) >= 5
        """
    )
    n_w = con.execute("SELECT count(*) FROM work_rarity").fetchone()[0]
    n_u = con.execute("SELECT count(*) FROM user_feat").fetchone()[0]
    print(f"  works={n_w:,} users={n_u:,} ({time.time()-t0:.1f}s)", flush=True)


def rank_from_sql(con, score_sql: str, args: list[Any] | None = None) -> list[dict]:
    """score_sql must yield work_id, score, n_eff (and optionally extra)."""
    rows = con.execute(
        f"""
        SELECT
            s.work_id,
            s.book_id,
            s.title,
            s.author,
            x.score,
            x.n_eff,
            wr.n AS catalog_n,
            wr.p5,
            wr.mean
        FROM ({score_sql}) x
        JOIN ex.work_scores s USING (work_id)
        JOIN work_rarity wr USING (work_id)
        LEFT JOIN ex.work_flags cf ON cf.work_id = s.work_id
        WHERE TRUE
        {catalog_ok_sql('s')}
        ORDER BY x.score DESC NULLS LAST, x.n_eff DESC
        LIMIT {FETCH}
        """,
        args or [],
    ).fetchall()
    out = []
    for i, r in enumerate(rows, 1):
        out.append(
            {
                "rank": i,
                "work_id": str(r[0]),
                "book_id": r[1],
                "title": r[2],
                "author": r[3],
                "score": float(r[4]) if r[4] is not None else 0.0,
                "n_eff": float(r[5]) if r[5] is not None else 0.0,
                "catalog_n": int(r[6] or 0),
                "p5": float(r[7]) if r[7] is not None else None,
                "mean": float(r[8]) if r[8] is not None else None,
            }
        )
    return out


def method_baseline_bayes_p5(con) -> list[dict]:
    """Global Bayesian P(5★) — popularity-aware baseline."""
    m, p0 = 50.0, 0.35
    sql = f"""
        SELECT
            work_id,
            ((n5 + {m}*{p0}) / (n + {m}))::DOUBLE AS score,
            n::DOUBLE AS n_eff
        FROM work_rarity
        WHERE n >= {MIN_WORK_N}
    """
    return rank_from_sql(con, sql)


def method_baseline_mean(con) -> list[dict]:
    sql = f"""
        SELECT work_id, mean AS score, n::DOUBLE AS n_eff
        FROM work_rarity WHERE n >= {MIN_WORK_N}
    """
    return rank_from_sql(con, sql)


def method_rarity_depth_curators(
    con, *, depth_col: str = "depth_ge4", top_frac: float = 0.05, min_votes: int = 25
) -> list[dict]:
    """Top depth users among engaged readers → Bayesian P(5★)."""
    where = (
        f"{depth_col} IS NOT NULL AND n_rated >= 50 AND n_ge4_midpop >= 8 "
        f"AND n_ge4_popular >= 2"
    )
    thr = _quantile(con, depth_col, 1.0 - top_frac, where=where)
    m, p0 = 30.0, 0.25
    sql = f"""
        WITH cur AS (
            SELECT user_id FROM user_feat
            WHERE {where} AND {depth_col} >= ?
        ),
        agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
            FROM ex.all_rating_events e
            JOIN cur USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            ((n5 + {m}*{p0}) / (n + {m}))::DOUBLE AS score,
            n::DOUBLE AS n_eff
        FROM agg
    """
    return rank_from_sql(con, sql, [float(thr)])


def method_rarity_depth_love(
    con, *, top_frac: float = 0.05, min_votes: int = 25
) -> list[dict]:
    """Engaged depth curators + rarity-weighted 5★ rate."""
    where = (
        "depth_ge4 IS NOT NULL AND n_rated >= 50 AND n_ge4_midpop >= 8 "
        "AND n_ge4_popular >= 2"
    )
    thr = _quantile(con, "depth_ge4", 1.0 - top_frac, where=where)
    m = 30.0
    sql = f"""
        WITH cur AS (
            SELECT user_id FROM user_feat
            WHERE {where} AND depth_ge4 >= ?
        ),
        agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                sum(CASE WHEN e.rating = 5 THEN wr.rarity ELSE 0 END)::DOUBLE AS rare5
            FROM ex.all_rating_events e
            JOIN cur USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            ((rare5 + {m} * 0.02) / (n + {m}))::DOUBLE AS score,
            n::DOUBLE AS n_eff
        FROM agg
    """
    return rank_from_sql(con, sql, [float(thr)])


def method_picky_curators(con, *, top_frac: float = 0.10, min_votes: int = 25) -> list[dict]:
    """Lowest five_rate users (stingy raters) → Bayesian P(5★)."""
    where = "five_rate IS NOT NULL AND n_rated >= 40 AND n_ge4_midpop >= 5"
    thr = _quantile(con, "five_rate", top_frac, where=where)
    m, p0 = 30.0, 0.2
    sql = f"""
        WITH cur AS (
            SELECT user_id FROM user_feat
            WHERE {where} AND five_rate <= ?
        ),
        agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
            FROM ex.all_rating_events e
            JOIN cur USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            ((n5 + {m}*{p0}) / (n + {m}))::DOUBLE AS score,
            n::DOUBLE AS n_eff
        FROM agg
    """
    return rank_from_sql(con, sql, [float(thr)])


def method_contrastive_lift(con, *, top_frac: float = 0.10, min_votes: int = 40) -> list[dict]:
    """P(5★|engaged-deep) − P(5★|mass) among books with enough of both.

    Closest ratings-only analogue of 'discriminating' literary signal.
    """
    where = (
        "depth_ge4 IS NOT NULL AND n_rated >= 50 AND n_ge4_midpop >= 8 "
        "AND n_ge4_popular >= 2"
    )
    thr = _quantile(con, "depth_ge4", 1.0 - top_frac, where=where)
    sql = f"""
        WITH deep AS (
            SELECT user_id FROM user_feat
            WHERE {where} AND depth_ge4 >= ?
        ),
        mass AS (
            SELECT user_id FROM user_feat
            WHERE n_rated >= 30 AND depth_ge4 IS NOT NULL AND depth_ge4 < ?
        ),
        deep_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_d,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_d
            FROM ex.all_rating_events e
            JOIN deep USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        ),
        mass_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_m,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_m
            FROM ex.all_rating_events e
            JOIN mass USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            d.work_id,
            (d.p5_d - m.p5_m)::DOUBLE AS score,
            least(d.n_d, m.n_m)::DOUBLE AS n_eff
        FROM deep_agg d
        JOIN mass_agg m USING (work_id)
        WHERE d.n_d >= {min_votes} AND m.n_m >= {min_votes}
    """
    return rank_from_sql(con, sql, [float(thr), float(thr)])


def method_audience_depth(con, *, min_votes: int = 50) -> list[dict]:
    """Rank books by mean depth of their 5★ audience (ratings-only consecration)."""
    m = 40.0
    prior = con.execute(
        "SELECT avg(depth_ge4) FROM user_feat WHERE depth_ge4 IS NOT NULL"
    ).fetchone()[0]
    sql = f"""
        WITH agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n5,
                avg(uf.depth_ge4)::DOUBLE AS mean_depth
            FROM ex.all_rating_events e
            JOIN user_feat uf USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE e.rating = 5
              AND uf.depth_ge4 IS NOT NULL
              AND uf.n_rated >= 40
              AND uf.n_ge4_midpop >= 5
              AND wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            (
                (n5 / (n5 + {m})) * mean_depth
                + ({m} / (n5 + {m})) * {float(prior)}
            )::DOUBLE AS score,
            n5::DOUBLE AS n_eff
        FROM agg
    """
    return rank_from_sql(con, sql)


def method_hits_reflective(con, *, iters: int = 8, min_votes: int = 25) -> list[dict]:
    """HITS on 5★ edges weighted by book rarity (ratings-only).

    Edge u→i gets weight rarity_i so mass market hubs don't dominate.
    user_score ← sum_i rarity_i * book_score_i (over u's 5★)
    book_score ← sum_u user_score_u (over 5★ raters), then *= rarity again.
    """
    print("  HITS: loading rarity-weighted 5★ edges…", flush=True)
    t0 = time.time()
    edges = con.execute(
        f"""
        SELECT e.user_id, e.work_id, wr.rarity
        FROM ex.five_star_events e
        JOIN work_rarity wr USING (work_id)
        JOIN user_feat uf USING (user_id)
        WHERE wr.n >= {MIN_RANK_N}
          AND wr.n <= 150000
          AND uf.n_rated >= 40
          AND uf.n5 BETWEEN 8 AND 300
          AND uf.n_ge4_midpop >= 5
          AND uf.depth_ge4 IS NOT NULL
        """
    ).fetchall()
    print(f"  HITS: {len(edges):,} edges ({time.time()-t0:.1f}s)", flush=True)

    books_of: dict[int, list[tuple[str, float]]] = defaultdict(list)
    users_of: dict[str, list[int]] = defaultdict(list)
    rarity: dict[str, float] = {}
    for uid, wid, rar in edges:
        wid = str(wid)
        rar = float(rar)
        rarity[wid] = rar
        books_of[int(uid)].append((wid, rar))
        users_of[wid].append(int(uid))

    bscore = {w: rarity[w] for w in users_of}
    uscore = {u: 1.0 for u in books_of}

    def l2norm(d: dict) -> None:
        s = math.sqrt(sum(v * v for v in d.values())) or 1.0
        for k in d:
            d[k] /= s

    for it in range(iters):
        for u, items in books_of.items():
            uscore[u] = sum(bscore.get(w, 0.0) * rar for w, rar in items)
            uscore[u] /= math.sqrt(len(items))
        l2norm(uscore)
        for w, uids in users_of.items():
            bscore[w] = sum(uscore.get(u, 0.0) for u in uids) * rarity[w]
            bscore[w] /= math.sqrt(max(len(uids), 1))
        l2norm(bscore)
        print(f"  HITS iter {it+1}/{iters}", flush=True)

    m = 30.0
    scored = []
    for wid, sc in bscore.items():
        n = len(users_of[wid])
        if n < min_votes:
            continue
        scored.append((wid, sc * (n / (n + m)), float(n)))
    scored.sort(key=lambda t: (-t[1], -t[2]))

    con.execute("USE memory")
    con.execute(
        "CREATE OR REPLACE TABLE hits_scores (work_id VARCHAR, score DOUBLE, n_eff DOUBLE)"
    )
    con.executemany(
        "INSERT INTO hits_scores VALUES (?, ?, ?)",
        [(w, s, n) for w, s, n in scored[: FETCH * 2]],
    )
    return rank_from_sql(con, "SELECT work_id, score, n_eff FROM hits_scores")


def method_depth_weighted_all(con, *, min_votes: int = 25) -> list[dict]:
    """Engaged users only; weight = depth_ge4^2."""
    m, p0 = 30.0, 0.25
    sql = f"""
        WITH agg AS (
            SELECT
                e.work_id,
                sum(power(greatest(uf.depth_ge4, 1e-9), 2))::DOUBLE AS w_sum,
                sum(
                    CASE WHEN e.rating = 5
                         THEN power(greatest(uf.depth_ge4, 1e-9), 2)
                         ELSE 0 END
                )::DOUBLE AS w5,
                (
                    power(sum(power(greatest(uf.depth_ge4, 1e-9), 2)), 2)
                    / nullif(sum(power(power(greatest(uf.depth_ge4, 1e-9), 2), 2)), 0)
                )::DOUBLE AS n_eff
            FROM ex.all_rating_events e
            JOIN user_feat uf USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE uf.depth_ge4 IS NOT NULL
              AND uf.n_rated >= 40
              AND uf.n_ge4_midpop >= 5
              AND wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            ((w5 + {m}*{p0}) / (w_sum + {m}))::DOUBLE AS score,
            n_eff
        FROM agg
        WHERE n_eff >= {min_votes}
    """
    return rank_from_sql(con, sql)


def method_cocitation_pmi(con, *, min_votes: int = 40) -> list[dict]:
    """Eigenvector-ish prestige from 5★ co-liking among mid-popular books.

    Sparse item–item graph: edge = positive PMI of co-5★ users, books with n in
    [200, 20000]. Power iteration. Ratings-only.
    """
    print("  PMI: building mid-pop 5★ user sets…", flush=True)
    t0 = time.time()
    rows = con.execute(
        f"""
        SELECT e.work_id, e.user_id
        FROM ex.five_star_events e
        JOIN work_rarity wr USING (work_id)
        JOIN user_feat uf USING (user_id)
        WHERE wr.n BETWEEN 200 AND 20000
          AND uf.n_rated >= 30
          AND uf.n5 BETWEEN 5 AND 250
        """
    ).fetchall()
    print(f"  PMI: {len(rows):,} edges ({time.time()-t0:.1f}s)", flush=True)

    users_of: dict[str, set[int]] = defaultdict(set)
    for wid, uid in rows:
        users_of[str(wid)].add(int(uid))
    works = [w for w, us in users_of.items() if len(us) >= min_votes]
    print(f"  PMI: {len(works):,} candidate works", flush=True)

    books_of_user: dict[int, list[str]] = defaultdict(list)
    for w in works:
        for u in users_of[w]:
            books_of_user[u].append(w)

    pair_count: dict[tuple[str, str], int] = defaultdict(int)
    n_users_pairs = 0
    for _u, wlist in books_of_user.items():
        if len(wlist) < 2 or len(wlist) > 80:
            continue
        n_users_pairs += 1
        wl = wlist[:40]
        for i in range(len(wl)):
            for j in range(i + 1, len(wl)):
                a, b = (wl[i], wl[j]) if wl[i] < wl[j] else (wl[j], wl[i])
                pair_count[(a, b)] += 1

    print(f"  PMI: {len(pair_count):,} pairs from {n_users_pairs:,} users", flush=True)
    n_u = max(len(books_of_user), 1)
    adj: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (a, b), c in pair_count.items():
        if c < 5:
            continue
        pa = len(users_of[a]) / n_u
        pb = len(users_of[b]) / n_u
        pab = c / n_u
        pmi = math.log(pab / (pa * pb + 1e-18) + 1e-18)
        if pmi <= 0:
            continue
        adj[a].append((b, pmi))
        adj[b].append((a, pmi))

    score = {w: 1.0 for w in adj}
    for it in range(12):
        nxt = {}
        for w, nbrs in adj.items():
            nxt[w] = sum(score.get(v, 0.0) * wt for v, wt in nbrs) / math.sqrt(
                len(nbrs)
            )
        s = math.sqrt(sum(v * v for v in nxt.values())) or 1.0
        score = {k: v / s for k, v in nxt.items()}
        print(f"  PMI power iter {it+1}/12", flush=True)

    m = 40.0
    scored = []
    for w, sc in score.items():
        n = len(users_of[w])
        if n < min_votes:
            continue
        scored.append((w, sc * (n / (n + m)), float(n)))
    scored.sort(key=lambda t: (-t[1], -t[2]))

    con.execute("USE memory")
    con.execute(
        "CREATE OR REPLACE TABLE pmi_scores (work_id VARCHAR, score DOUBLE, n_eff DOUBLE)"
    )
    con.executemany(
        "INSERT INTO pmi_scores VALUES (?, ?, ?)",
        [(w, s, n) for w, s, n in scored[: FETCH * 2]],
    )
    return rank_from_sql(con, "SELECT work_id, score, n_eff FROM pmi_scores")


def method_anti_blockbuster_picky(con, *, min_votes: int = 30) -> list[dict]:
    """Users who rarely 5★ blockbusters but rate a lot → their Bayesian P(5★)."""
    thr_n = _quantile(con, "n", 0.995, table="work_rarity")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_resist AS
        SELECT
            e.user_id,
            count(*) FILTER (WHERE wr.n >= {float(thr_n)})::BIGINT AS n_bb,
            (
                count(*) FILTER (WHERE wr.n >= {float(thr_n)} AND e.rating = 5)::DOUBLE
                / nullif(count(*) FILTER (WHERE wr.n >= {float(thr_n)}), 0)
            ) AS p5_bb,
            uf.n_rated,
            uf.five_rate
        FROM ex.all_rating_events e
        JOIN work_rarity wr USING (work_id)
        JOIN user_feat uf USING (user_id)
        WHERE uf.n_rated >= 50
        GROUP BY e.user_id, uf.n_rated, uf.five_rate
        HAVING count(*) FILTER (WHERE wr.n >= {float(thr_n)}) >= 8
        """
    )
    resist_thr = _quantile(
        con,
        "1.0 - coalesce(p5_bb, 1.0)",
        0.85,
        table="user_resist",
        where="p5_bb IS NOT NULL",
    )
    m, p0 = 30.0, 0.25
    sql = f"""
        WITH cur AS (
            SELECT user_id FROM user_resist
            WHERE (1.0 - coalesce(p5_bb, 1.0)) >= ?
              AND five_rate <= 0.45
        ),
        agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
            FROM ex.all_rating_events e
            JOIN cur USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            ((n5 + {m}*{p0}) / (n + {m}))::DOUBLE AS score,
            n::DOUBLE AS n_eff
        FROM agg
    """
    return rank_from_sql(con, sql, [float(resist_thr)])


def _load_midpop_five_star(
    con, *, n_lo: int = 200, n_hi: int = 20000, min_votes: int = 25
) -> tuple[dict[str, list[int]], dict[int, list[str]]]:
    """Bipartite mid-pop 5★ graph (ratings-only). Cached per process/params."""
    key = (n_lo, n_hi, min_votes)
    hit = _MIDPOP_CACHE.get(key)
    if hit is not None:
        print(f"  midpop cache hit {key}", flush=True)
        return hit

    rows = con.execute(
        f"""
        SELECT e.work_id, e.user_id
        FROM ex.five_star_events e
        JOIN work_rarity wr USING (work_id)
        JOIN user_feat uf USING (user_id)
        WHERE wr.n BETWEEN {n_lo} AND {n_hi}
          AND uf.n_rated >= 30
          AND uf.n5 BETWEEN 5 AND 250
        """
    ).fetchall()
    users_of: dict[str, list[int]] = defaultdict(list)
    books_of: dict[int, list[str]] = defaultdict(list)
    for wid, uid in rows:
        wid = str(wid)
        uid = int(uid)
        users_of[wid].append(uid)
        books_of[uid].append(wid)

    def _sync(
        u_of: dict[str, list[int]], b_of: dict[int, list[str]]
    ) -> tuple[dict[str, list[int]], dict[int, list[str]]]:
        keep_w = {w for w, us in u_of.items() if len(us) >= min_votes}
        b2: dict[int, list[str]] = {}
        for u, ws in b_of.items():
            ws2 = [w for w in ws if w in keep_w]
            if 5 <= len(ws2) <= 100:
                b2[u] = ws2
        u2: dict[str, list[int]] = defaultdict(list)
        for u, ws in b2.items():
            for w in ws:
                u2[w].append(u)
        u2 = {w: us for w, us in u2.items() if len(us) >= min_votes}
        b3: dict[int, list[str]] = {}
        for u, ws in b2.items():
            ws3 = [w for w in ws if w in u2]
            if len(ws3) >= 5:
                b3[u] = ws3
        u3: dict[str, list[int]] = defaultdict(list)
        for u, ws in b3.items():
            for w in ws:
                u3[w].append(u)
        return dict(u3), b3

    out = _sync(users_of, books_of)
    _MIDPOP_CACHE[key] = out
    return out


_MIDPOP_CACHE: dict[tuple[int, int, int], tuple[dict[str, list[int]], dict[int, list[str]]]] = {}
_PMI_CACHE: dict[tuple, dict[str, list[tuple[str, float]]]] = {}
_REFLECT_CACHE: dict[tuple, tuple[dict[int, list[float]], dict[str, list[float]]]] = {}


def clear_graph_caches() -> None:
    _MIDPOP_CACHE.clear()
    _PMI_CACHE.clear()
    _REFLECT_CACHE.clear()


def _method_of_reflections(
    users_of: dict[str, list[int]],
    books_of: dict[int, list[str]],
    *,
    iters: int = 16,
) -> tuple[dict[int, list[float]], dict[str, list[float]]]:
    """Lizardo / Hidalgo–Hausmann reflections on person×book 5★ matrix.

    d_u[0] = omnivorousness (# books)
    δ_w[0] = popularity (share of users who 5★ the book)
    d_u[n] = mean_δ of books liked by u
    δ_w[n] = mean_d of users who like w
    """
    # Cache by object identity + iters (graphs are reused via midpop cache)
    key = (id(users_of), id(books_of), iters)
    hit = _REFLECT_CACHE.get(key)
    if hit is not None:
        print(f"  reflections cache hit iters={iters}", flush=True)
        return hit

    n_users = max(len(books_of), 1)
    d: dict[int, list[float]] = {
        u: [float(len(ws))] for u, ws in books_of.items()
    }
    delta: dict[str, list[float]] = {
        w: [len(us) / n_users] for w, us in users_of.items()
    }
    for n in range(1, iters + 1):
        for u, ws in books_of.items():
            d[u].append(sum(delta[w][n - 1] for w in ws) / len(ws))
        for w, us in users_of.items():
            delta[w].append(sum(d[u][n - 1] for u in us) / len(us))
        if n % 2 == 0:
            mu = sum(v[-1] for v in delta.values()) / len(delta)
            sd = math.sqrt(
                sum((v[-1] - mu) ** 2 for v in delta.values()) / len(delta)
            ) or 1.0
            for w in delta:
                delta[w][-1] = (delta[w][-1] - mu) / sd
            mu = sum(v[-1] for v in d.values()) / len(d)
            sd = math.sqrt(sum((v[-1] - mu) ** 2 for v in d.values()) / len(d)) or 1.0
            for u in d:
                d[u][-1] = (d[u][-1] - mu) / sd
        print(f"  reflections iter {n}/{iters}", flush=True)
    _REFLECT_CACHE[key] = (d, delta)
    return d, delta


def _scores_to_rank(con, scored: list[tuple[str, float, float]]) -> list[dict]:
    scored.sort(key=lambda t: (-t[1], -t[2]))
    con.execute("USE memory")
    con.execute(
        "CREATE OR REPLACE TABLE tmp_scores (work_id VARCHAR, score DOUBLE, n_eff DOUBLE)"
    )
    con.executemany(
        "INSERT INTO tmp_scores VALUES (?, ?, ?)",
        [(w, s, n) for w, s, n in scored[: FETCH * 2]],
    )
    return rank_from_sql(con, "SELECT work_id, score, n_eff FROM tmp_scores")


def method_lizardo_neg_delta2(con, *, min_votes: int = 30) -> list[dict]:
    """Rank by −δ² (2nd-order popularity): audiences who avoid popular forms.

    Lizardo Table 1: δ_k² = average popular-choice bias of the book's fans.
    Low δ² ⇒ fans also choose niche books — closest reflections analogue of
    "consecrating niche enthusiasts" without taste piles.
    """
    print("  Lizardo: loading mid-pop 5★ bipartite…", flush=True)
    t0 = time.time()
    users_of, books_of = _load_midpop_five_star(
        con, n_lo=400, n_hi=15000, min_votes=min_votes
    )
    print(
        f"  Lizardo: {len(users_of):,} works, {len(books_of):,} users "
        f"({time.time()-t0:.1f}s)",
        flush=True,
    )
    _d, delta = _method_of_reflections(users_of, books_of, iters=6)
    m = 40.0
    scored = []
    for w, us in users_of.items():
        n = float(len(us))
        if n < min_votes:
            continue
        # δ[2] is 2nd-order popularity; negate so niche-audience books rise
        sc = -float(delta[w][2])
        scored.append((w, sc * (n / (n + m)), n))
    return _scores_to_rank(con, scored)


def method_lizardo_niche_enthusiasts(con, *, min_votes: int = 30) -> list[dict]:
    """Users with low d¹ (niche culture enthusiasts) → Bayesian P(5★).

    d_u¹ = average popularity of books they 5★. Bottom quartile = niche bias.
    """
    print("  Lizardo niche enthusiasts: bipartite…", flush=True)
    users_of, books_of = _load_midpop_five_star(
        con, n_lo=400, n_hi=15000, min_votes=25
    )
    d, _delta = _method_of_reflections(users_of, books_of, iters=2)
    # d[u][1] = popular choice bias
    biases = [(u, d[u][1]) for u in books_of]
    biases.sort(key=lambda t: t[1])
    k = max(int(0.20 * len(biases)), 50)
    niche_users = {u for u, _ in biases[:k]}
    print(f"  niche enthusiasts: {len(niche_users):,} users", flush=True)

    con.execute("USE memory")
    con.execute("CREATE OR REPLACE TABLE niche_users (user_id BIGINT)")
    con.executemany(
        "INSERT INTO niche_users VALUES (?)", [(u,) for u in niche_users]
    )
    m, p0 = 30.0, 0.25
    sql = f"""
        WITH agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
            FROM ex.all_rating_events e
            JOIN niche_users nu USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            work_id,
            ((n5 + {m}*{p0}) / (n + {m}))::DOUBLE AS score,
            n::DOUBLE AS n_eff
        FROM agg
    """
    return rank_from_sql(con, sql)


def method_lizardo_high_order(con, *, min_votes: int = 30) -> list[dict]:
    """High-order even reflection (community structure after popularity drained).

    After z-scoring even iterations, δ^{16} freezes into co-choice communities
    (Lizardo §2.4). Rank by |δ^{even}| × shrink — surfaces dense local canons.
    """
    print("  Lizardo high-order: bipartite…", flush=True)
    users_of, books_of = _load_midpop_five_star(
        con, n_lo=400, n_hi=15000, min_votes=min_votes
    )
    _d, delta = _method_of_reflections(users_of, books_of, iters=14)
    m = 40.0
    scored = []
    for w, us in users_of.items():
        n = float(len(us))
        if n < min_votes:
            continue
        # absolute high-order score picks either pole of the frozen axis
        sc = abs(float(delta[w][14]))
        scored.append((w, sc * (n / (n + m)), n))
    return _scores_to_rank(con, scored)


def method_feldkamp_dual_axis(con, *, min_votes: int = 30) -> list[dict]:
    """Crowd-mean downweighted niche-audience score (Feldkamp dual quality).

    Expert/canonical proxies anti-correlate with Goodreads means; so among
    mid-pop books, reward low δ² (niche-enthusiast audience) while penalizing
    high global mean — push away popular-romance crowd darlings.
    """
    print("  Feldkamp dual: reflections + mean penalty…", flush=True)
    users_of, books_of = _load_midpop_five_star(
        con, n_lo=400, n_hi=15000, min_votes=min_votes
    )
    _d, delta = _method_of_reflections(users_of, books_of, iters=4)
    means = {
        str(r[0]): float(r[1])
        for r in con.execute(
            "SELECT work_id, mean FROM work_rarity WHERE n BETWEEN 200 AND 20000"
        ).fetchall()
    }
    mean_vals = [means[w] for w in users_of if w in means]
    mu = sum(mean_vals) / len(mean_vals)
    sd = math.sqrt(sum((x - mu) ** 2 for x in mean_vals) / len(mean_vals)) or 1.0
    m = 40.0
    scored = []
    for w, us in users_of.items():
        n = float(len(us))
        if n < min_votes or w not in means:
            continue
        z_mean = (means[w] - mu) / sd
        # niche audience (low δ2) minus crowd-mean z
        sc = (-float(delta[w][2])) - 0.75 * z_mean
        scored.append((w, sc * (n / (n + m)), n))
    return _scores_to_rank(con, scored)


def _pmi_adjacency(
    users_of: dict[str, set[int]] | dict[str, list[int]],
    *,
    min_pair: int = 8,
    min_pmi: float = 1.25,
    knn: int = 6,
) -> dict[str, list[tuple[str, float]]]:
    """Positive-PMI item graph, sparsified to kNN so communities don't fuse."""
    key = (id(users_of), min_pair, min_pmi, knn)
    hit = _PMI_CACHE.get(key)
    if hit is not None:
        print(f"  PMI cache hit knn={knn} min_pmi={min_pmi}", flush=True)
        return hit

    users_sets = {w: set(us) for w, us in users_of.items()}
    books_of_user: dict[int, list[str]] = defaultdict(list)
    for w, us in users_sets.items():
        for u in us:
            books_of_user[u].append(w)
    pair_count: dict[tuple[str, str], int] = defaultdict(int)
    for _u, wlist in books_of_user.items():
        if len(wlist) < 2 or len(wlist) > 60:
            continue
        wl = wlist[:30]
        for i in range(len(wl)):
            for j in range(i + 1, len(wl)):
                a, b = (wl[i], wl[j]) if wl[i] < wl[j] else (wl[j], wl[i])
                pair_count[(a, b)] += 1
    n_u = max(len(books_of_user), 1)
    raw: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (a, b), c in pair_count.items():
        if c < min_pair:
            continue
        pa = len(users_sets[a]) / n_u
        pb = len(users_sets[b]) / n_u
        pab = c / n_u
        pmi = math.log(pab / (pa * pb + 1e-18) + 1e-18)
        if pmi < min_pmi:
            continue
        raw[a].append((b, pmi))
        raw[b].append((a, pmi))
    adj: dict[str, list[tuple[str, float]]] = {}
    for w, nbrs in raw.items():
        nbrs.sort(key=lambda t: -t[1])
        adj[w] = nbrs[:knn]
    _PMI_CACHE[key] = adj
    return adj


def method_nested_community_portfolio(con, *, min_votes: int = 25) -> list[dict]:
    """Airoldi-style nested legitimacy: PMI communities → within-community prestige.

    1) Mid-pop 5★ PMI kNN graph → label-propagation communities (loud local canons).
    2) Within each large community, local consecration density from users dense
       in that community.
    3) Portfolio rank: interleave top books across communities (round-robin),
       so Arabic / Tamil / Anglophone clusters can all surface without one
       global eigenvector swallowing the rest.
    """
    print("  Nested communities: building PMI graph…", flush=True)
    t0 = time.time()
    # Slightly tighter band than reflections — denser language/taste clusters
    users_of_l, books_of = _load_midpop_five_star(
        con, n_lo=250, n_hi=12000, min_votes=min_votes
    )
    users_of = {w: set(us) for w, us in users_of_l.items()}
    adj = _pmi_adjacency(users_of, min_pair=8, min_pmi=1.5, knn=5)
    print(
        f"  Nested: {len(adj):,} nodes in PMI graph ({time.time()-t0:.1f}s)",
        flush=True,
    )
    if len(adj) < 50:
        return []

    # Label propagation on sparsified graph
    labels = {w: w for w in adj}
    for it in range(15):
        order = list(adj.keys())
        order = order[it:] + order[:it]
        changed = 0
        for w in order:
            votes: Counter[str] = Counter()
            for v, wt in adj[w]:
                if v in labels:
                    votes[labels[v]] += wt
            if not votes:
                continue
            best = max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
            if best != labels[w]:
                labels[w] = best
                changed += 1
        print(f"  labelprop {it+1}/15 changed={changed}", flush=True)
        if changed == 0:
            break

    communities: dict[str, list[str]] = defaultdict(list)
    for w, lab in labels.items():
        communities[lab].append(w)
    # Prefer mid-size communities (loud local canons); drop the mega-blob if any
    sized = sorted(
        ((lab, ws) for lab, ws in communities.items() if len(ws) >= 25),
        key=lambda t: -len(t[1]),
    )
    if sized and len(sized[0][1]) > 0.45 * len(adj):
        # Mega-component: keep next communities + split mega via connected
        # components on stronger edges only
        print("  Nested: mega-component detected; re-cluster at higher PMI", flush=True)
        adj2 = _pmi_adjacency(users_of, min_pair=12, min_pmi=2.2, knn=4)
        labels = {w: w for w in adj2}
        for it in range(12):
            order = list(adj2.keys())
            order = order[it:] + order[:it]
            changed = 0
            for w in order:
                votes: Counter[str] = Counter()
                for v, wt in adj2[w]:
                    if v in labels:
                        votes[labels[v]] += wt
                if not votes:
                    continue
                best = max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
                if best != labels[w]:
                    labels[w] = best
                    changed += 1
            if changed == 0:
                break
        communities = defaultdict(list)
        for w, lab in labels.items():
            communities[lab].append(w)
        sized = sorted(
            ((lab, ws) for lab, ws in communities.items() if 25 <= len(ws) <= 8000),
            key=lambda t: -len(t[1]),
        )
    large = sized[:15]
    print(
        f"  Nested: {len(large)} communities "
        f"(sizes={[len(ws) for _, ws in large]})",
        flush=True,
    )

    m, p0 = 25.0, 0.3
    community_ranks: list[list[tuple[str, float, float]]] = []
    community_meta: list[dict[str, Any]] = []
    for lab, members in large:
        member_set = set(members)
        # users with ≥3 5★ in this community
        dense_users = set()
        for u, ws in books_of.items():
            hit = sum(1 for w in ws if w in member_set)
            if hit >= 3:
                dense_users.add(u)
        if len(dense_users) < 40:
            continue
        # Bayesian P(5) within community books from dense users
        n5: dict[str, int] = defaultdict(int)
        nn: dict[str, int] = defaultdict(int)
        # Use only 5★ edges we already have for speed (presence = 5★)
        for w in members:
            for u in users_of.get(w, ()):
                if u in dense_users:
                    nn[w] += 1
                    n5[w] += 1  # all edges are 5★; use density of dense fans
        scored = []
        for w in members:
            n = float(nn.get(w, 0))
            if n < min_votes:
                continue
            # score = share of community-dense users among mid-pop 5★ audience
            # ≈ local consecration density
            sc = (n + m * p0) / (len(users_of[w]) + m)
            scored.append((w, sc, n))
        scored.sort(key=lambda t: (-t[1], -t[2]))
        if not scored:
            continue
        community_ranks.append(scored)
        # peek titles for report via duckdb later
        community_meta.append(
            {
                "label": lab,
                "size": len(members),
                "dense_users": len(dense_users),
                "top_ids": [w for w, _, _ in scored[:5]],
            }
        )

    # Round-robin portfolio across communities
    portfolio: list[tuple[str, float, float]] = []
    seen: set[str] = set()
    max_len = max((len(r) for r in community_ranks), default=0)
    for i in range(max_len):
        for ci, ranked in enumerate(community_ranks):
            if i >= len(ranked):
                continue
            w, sc, n = ranked[i]
            if w in seen:
                continue
            seen.add(w)
            # slight boost for earlier (larger) communities' heads, but
            # primarily order by round so communities interleave
            portfolio.append((w, sc + 0.01 * (len(community_ranks) - ci), n))

    # stash community meta for report
    con.execute("USE memory")
    con.execute(
        """
        CREATE OR REPLACE TABLE nested_meta (
            community_idx INTEGER, label VARCHAR, size INTEGER,
            dense_users INTEGER, top_work_id VARCHAR, top_rank INTEGER
        )
        """
    )
    meta_rows = []
    for ci, meta in enumerate(community_meta):
        for ti, wid in enumerate(meta["top_ids"]):
            meta_rows.append(
                (ci, meta["label"][:32], meta["size"], meta["dense_users"], wid, ti + 1)
            )
    if meta_rows:
        con.executemany("INSERT INTO nested_meta VALUES (?, ?, ?, ?, ?, ?)", meta_rows)

    return _scores_to_rank(con, portfolio)


def method_nested_mass_community_reflections(con, *, min_votes: int = 25) -> list[dict]:
    """Within the mid-pop community with highest median catalog-n, apply −δ².

    Ratings-only proxy for the platform's dominant (often Anglophone) cluster:
    among mid-size PMI communities, take the one whose books are most globally
    popular on average, then Lizardo −δ² inside it. Avoids language metadata
    while following Airoldi's nest: global community → within-community prestige.
    """
    print("  Mass-community reflections: PMI communities…", flush=True)
    users_of_l, books_of = _load_midpop_five_star(
        con, n_lo=250, n_hi=12000, min_votes=min_votes
    )
    users_of = {w: set(us) for w, us in users_of_l.items()}
    adj = _pmi_adjacency(users_of, min_pair=8, min_pmi=1.5, knn=5)
    labels = {w: w for w in adj}
    for it in range(12):
        order = list(adj.keys())
        order = order[it:] + order[:it]
        changed = 0
        for w in order:
            votes: Counter[str] = Counter()
            for v, wt in adj[w]:
                if v in labels:
                    votes[labels[v]] += wt
            if not votes:
                continue
            best = max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
            if best != labels[w]:
                labels[w] = best
                changed += 1
        if changed == 0:
            break
    communities: dict[str, list[str]] = defaultdict(list)
    for w, lab in labels.items():
        communities[lab].append(w)

    catalog_n = {
        str(r[0]): int(r[1])
        for r in con.execute("SELECT work_id, n FROM work_rarity").fetchall()
    }

    def median_n(ws: list[str]) -> float:
        vals = sorted(catalog_n.get(w, 0) for w in ws)
        if not vals:
            return 0.0
        return float(vals[len(vals) // 2])

    candidates = [
        (lab, ws, median_n(ws))
        for lab, ws in communities.items()
        if 40 <= len(ws) <= 2500
    ]
    if not candidates:
        candidates = [
            (lab, ws, median_n(ws))
            for lab, ws in communities.items()
            if len(ws) >= 25
        ]
    candidates.sort(key=lambda t: -t[2])
    if not candidates:
        return []
    lab, members, med = candidates[0]
    print(
        f"  Mass community: size={len(members)} median_n={med:.0f} "
        f"(of {len(candidates)} candidates)",
        flush=True,
    )
    member_set = set(members)
    # Restrict bipartite to this community for reflections
    users_sub: dict[str, list[int]] = {
        w: users_of_l[w] for w in members if w in users_of_l
    }
    books_sub: dict[int, list[str]] = {}
    for u, ws in books_of.items():
        ws2 = [w for w in ws if w in member_set]
        if len(ws2) >= 3:
            books_sub[u] = ws2
    # resync
    u2: dict[str, list[int]] = defaultdict(list)
    for u, ws in books_sub.items():
        for w in ws:
            u2[w].append(u)
    users_sub = {w: us for w, us in u2.items() if len(us) >= min_votes}
    books_sub = {
        u: [w for w in ws if w in users_sub] for u, ws in books_sub.items()
    }
    books_sub = {u: ws for u, ws in books_sub.items() if len(ws) >= 3}
    if len(users_sub) < 30:
        return []
    _d, delta = _method_of_reflections(users_sub, books_sub, iters=6)
    m = 30.0
    scored = []
    for w, us in users_sub.items():
        n = float(len(us))
        if n < min_votes:
            continue
        sc = -float(delta[w][min(2, len(delta[w]) - 1)])
        scored.append((w, sc * (n / (n + m)), n))
    return _scores_to_rank(con, scored)


def evaluate(rows: list[dict], ev: dict[str, Any]) -> dict[str, Any]:
    pos, anti, fillers = ev["pos_works"], ev["anti_works"], ev["filler_works"]

    def ranks(ids: set[str], limit: int) -> list[int]:
        out = []
        for r in rows[:limit]:
            if r["work_id"] in ids:
                out.append(r["rank"])
        return out

    def count(ids: set[str], limit: int) -> int:
        return sum(1 for r in rows[:limit] if r["work_id"] in ids)

    anti_r = ranks(anti, 1000)
    pos50 = count(pos, 50)
    anti50 = count(anti, 50)
    anti1000 = count(anti, 1000)
    fill50 = count(fillers, 50)
    med_anti = None
    if anti_r:
        anti_r_sorted = sorted(anti_r)
        med_anti = anti_r_sorted[len(anti_r_sorted) // 2]

    # crude quality: reward pos50, penalize anti head + fillers
    q = (
        3.0 * pos50
        - 4.0 * anti50
        - 0.5 * anti1000
        - 2.0 * fill50
        + (0.01 * (med_anti or 0))
    )
    # geo mean n in top 100
    ns = [max(r["n_eff"], 1.0) for r in rows[:100]]
    geo_n = math.exp(sum(math.log(n) for n in ns) / len(ns)) if ns else 0.0

    return {
        "Q": q,
        "geo_n": geo_n,
        "pos50": pos50,
        "anti50": anti50,
        "anti1000": anti1000,
        "anti_med": med_anti,
        "filler50": fill50,
        "pos_share50": pos50 / 50.0,
        "anti_share1000": anti1000 / 1000.0,
        "top20": [
            {"rank": r["rank"], "title": r["title"], "author": r["author"], "n": r["n_eff"]}
            for r in rows[:20]
        ],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Run only these method names (default: paper suite + best priors)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run every registered method including slow failures",
    )
    args = parser.parse_args(argv)

    con = _con()
    clear_graph_caches()
    ev = load_eval_sets(con)
    print(
        f"Eval sets: pos_works={ev['n_pos_works']} anti={ev['n_anti_works']} "
        f"fillers={ev['n_fillers']}",
        flush=True,
    )
    materialize_base(con)

    registry: dict[str, Callable[[], list[dict]]] = {
        "baseline_bayes_p5": lambda: method_baseline_bayes_p5(con),
        "picky_top10pct": lambda: method_picky_curators(con, top_frac=0.10),
        "depth_top5pct_p5": lambda: method_rarity_depth_curators(con, top_frac=0.05),
        "audience_depth": lambda: method_audience_depth(con),
        "contrastive_lift": lambda: method_contrastive_lift(con, top_frac=0.10),
        "anti_blockbuster_picky": lambda: method_anti_blockbuster_picky(con),
        "cocitation_pmi": lambda: method_cocitation_pmi(con),
        "hits_rarity_weighted": lambda: method_hits_reflective(con, iters=5),
        # Paper-informed (Lizardo / Airoldi / Feldkamp)
        "lizardo_neg_delta2": lambda: method_lizardo_neg_delta2(con),
        "lizardo_niche_enthusiasts": lambda: method_lizardo_niche_enthusiasts(con),
        "lizardo_high_order": lambda: method_lizardo_high_order(con),
        "feldkamp_dual_axis": lambda: method_feldkamp_dual_axis(con),
        "nested_community_portfolio": lambda: method_nested_community_portfolio(con),
        "nested_mass_community_reflections": lambda: method_nested_mass_community_reflections(
            con
        ),
    }

    default_suite = [
        "anti_blockbuster_picky",
        "cocitation_pmi",
        "lizardo_neg_delta2",
        "lizardo_niche_enthusiasts",
        "lizardo_high_order",
        "feldkamp_dual_axis",
        "nested_community_portfolio",
        "nested_mass_community_reflections",
    ]
    if args.all:
        names = list(registry.keys())
    elif args.only is not None and len(args.only) > 0:
        names = args.only
    else:
        names = default_suite

    results: dict[str, Any] = {
        "meta": {
            "allowed": "(user_id, work_id, rating) and counts derived from them",
            "min_work_n": MIN_WORK_N,
            "min_user_n": MIN_USER_N,
            "papers": [
                "Lizardo 2018 method of reflections (Poetics)",
                "Airoldi 2024 nested relational legitimacy (Poetics)",
                "Feldkamp et al. 2024 Measuring Literary Quality (JCLS)",
                "Walsh & Antoniak Goodreads Classics (JCA)",
            ],
            "eval": {
                "n_pos_works": ev["n_pos_works"],
                "n_anti_works": ev["n_anti_works"],
                "n_fillers": ev["n_fillers"],
            },
        },
        "methods": {},
    }

    # Merge prior JSON metrics for methods we skip this run
    if OUT_JSON.exists() and not args.all:
        try:
            prior = json.loads(OUT_JSON.read_text(encoding="utf-8"))
            for k, v in (prior.get("methods") or {}).items():
                if k not in names:
                    results["methods"][k] = v
        except Exception:
            pass

    for name in names:
        if name not in registry:
            print(f"Unknown method {name}; skip", flush=True)
            continue
        print(f"\n=== {name} ===", flush=True)
        t0 = time.time()
        try:
            rows = registry[name]()
            ms = int((time.time() - t0) * 1000)
            metrics = evaluate(rows, ev)
            blob: dict[str, Any] = {"elapsed_ms": ms, "metrics": metrics}
            if name == "nested_community_portfolio":
                try:
                    tops = con.execute(
                        """
                        SELECT community_idx, size, dense_users, top_rank,
                               s.title, s.author
                        FROM nested_meta nm
                        JOIN ex.work_scores s ON s.work_id = nm.top_work_id
                        ORDER BY community_idx, top_rank
                        LIMIT 60
                        """
                    ).fetchall()
                    blob["communities"] = [
                        {
                            "community": r[0],
                            "size": r[1],
                            "dense_users": r[2],
                            "rank_in_comm": r[3],
                            "title": r[4],
                            "author": r[5],
                        }
                        for r in tops
                    ]
                except Exception as exc:
                    blob["communities_error"] = str(exc)
            results["methods"][name] = blob
            print(
                f"  {ms}ms Q={metrics['Q']:.2f} pos50={metrics['pos50']} "
                f"anti50={metrics['anti50']} anti1000={metrics['anti1000']} "
                f"anti_med={metrics['anti_med']} filler50={metrics['filler50']} "
                f"geo_n={metrics['geo_n']:.0f}",
                flush=True,
            )
            for r in metrics["top20"][:8]:
                print(
                    f"    {r['rank']:2d}. {r['title'][:52]:52s} — {r['author'][:28]}",
                    flush=True,
                )
        except Exception as exc:
            results["methods"][name] = {"error": str(exc)}
            print(f"  FAILED: {exc}", flush=True)
            import traceback

            traceback.print_exc()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    _write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD}", flush=True)
    con.close()


def _write_report(results: dict[str, Any]) -> None:
    lines = [
        "# Ratings-only literary consensus — probe results",
        "",
        "Discovery uses **only** `(user_id, work_id, rating)` (and aggregates thereof).",
        "Literary_poll / non_literary / normie lists are **evaluation only**.",
        "",
        "## Papers → method choices",
        "",
        "- **Lizardo (2018), method of reflections:** person↔item recursive centralities "
        "beyond plain HITS. `δ²` = 2nd-order popularity of a book's audience; "
        "`d¹` = popular-choice bias of a reader. We rank by `−δ²` and by the "
        "Bayesian tastes of low-`d¹` (niche-enthusiast) users.",
        "- **Airoldi (2024), nested relational legitimacy:** hierarchies are nested "
        "(genre→artist→work) and comparative. Global eigenvectors collapse loud "
        "local canons; we build PMI communities and a round-robin portfolio of "
        "within-community heads.",
        "- **Feldkamp et al. (2024):** expert/canonical proxies often anti-correlate "
        "with Goodreads means; Hugo-like prestige tracks popular more than canonical. "
        "`feldkamp_dual_axis` rewards niche audiences while penalizing high crowd means.",
        "- **Walsh & Antoniak:** Goodreads “classics” are school/industry constructions — "
        "crowd tags ≠ academic canon. Eval against `literary_poll` is one Anglophone "
        "axis among many; Arabic/Tamil/Persian heads can be real canons with pos50=0.",
        "",
        "## Takeaways",
        "",
        "1. **Naive rarity-depth fails on Goodreads.** Obscure indie romance inflates "
        "“depth”; popular classics lower it → romance/vanity heads.",
        "2. **Plain HITS → YA/fantasy popularity hubs.**",
        "3. **Best Anglophone-poll overlap so far:** `anti_blockbuster_picky` "
        "(pos50≈4) — serious + multilingual classics mix, not poll literary.",
        "4. **`cocitation_pmi` recovers a coherent Arabic literary cluster** "
        "(anti50=0) — real ratings-only consensus, wrong eval axis.",
        "5. **Paper-informed follow-ups** (Lizardo / nested / Feldkamp) are below; "
        "expect multi-community canons rather than one Western poll ranking.",
        "",
        "## Method scores",
        "",
        "| method | Q | geo_n | pos50 | anti50 | anti1000 | anti_med | filler50 | ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    ok = [(n, b) for n, b in results["methods"].items() if "metrics" in b]
    err = [(n, b) for n, b in results["methods"].items() if "error" in b]
    ok.sort(key=lambda kv: -kv[1]["metrics"]["Q"])
    for name, blob in ok + err:
        if "error" in blob:
            lines.append(f"| {name} | ERR | | | | | | | |")
            continue
        m = blob["metrics"]
        lines.append(
            f"| {name} | {m['Q']:.1f} | {m['geo_n']:.0f} | {m['pos50']} | {m['anti50']} | "
            f"{m['anti1000']} | {m['anti_med']} | {m['filler50']} | {blob['elapsed_ms']} |"
        )
    lines += ["", "## Top 12 by method", ""]
    for name, blob in results["methods"].items():
        lines.append(f"### {name}")
        if "error" in blob:
            lines.append(f"Error: {blob['error']}")
            lines.append("")
            continue
        for r in blob["metrics"]["top20"][:12]:
            lines.append(
                f"- {r['rank']}. {r['title']} — {r['author']} (n≈{r['n']:.0f})"
            )
        if blob.get("communities"):
            lines.append("")
            lines.append("Within-community heads (nested portfolio):")
            cur = None
            for c in blob["communities"]:
                if c["community"] != cur:
                    cur = c["community"]
                    lines.append(
                        f"- Community {cur} (size={c['size']}, "
                        f"dense_users={c['dense_users']}):"
                    )
                lines.append(f"  - {c['rank_in_comm']}. {c['title']} — {c['author']}")
        lines.append("")
    lines += [
        "## Notes",
        "",
        "- Discovery signal remains ratings-only; catalog flags only for readable heads.",
        "- `lizardo_*`: reflections on mid-pop 5★ bipartite graph (n∈[200,20000]).",
        "- `nested_community_portfolio`: PMI label-propagation + round-robin heads.",
        "- `feldkamp_dual_axis`: `−δ² − 0.75·z(mean)`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Author-aware literary consensus experiments.

Allowed discovery: (user_id, work_id, rating, author_id) where author_id is
parsed from Goodreads author_url on work_scores. No taste piles / poll labels
enter scoring.

Motivation (Airoldi nested legitimacy; Vlegels & Lievens artist-preference
networks; arXiv:2303.05080 suggesting author-similarity over book-similarity):
book-level co-5★ graphs collapse into author islands. Lifting the bipartite
graph to person×author should recover *cross-author* taste hierarchies.

Also tests cross-author book PMI (same-author edges dropped).

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_author_level_canon
"""

from __future__ import annotations

import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_ratings_only_canon import (
    FETCH,
    MIN_RANK_N,
    _con,
    _method_of_reflections,
    _pmi_adjacency,
    _scores_to_rank,
    clear_graph_caches,
    evaluate,
    load_eval_sets,
    materialize_base,
    rank_from_sql,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "author_level_canon.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "AUTHOR_LEVEL_CANON_REPORT.md"

# Shared in-process caches (author bipartite loaded once)
_AUTHOR_GRAPH: dict[str, Any] | None = None


def materialize_authors(con) -> None:
    """work→author_id map + author aggregates (discovery-safe)."""
    print("Materializing author map…", flush=True)
    t0 = time.time()
    con.execute("USE memory")
    con.execute(
        """
        CREATE OR REPLACE TABLE work_author AS
        SELECT
            work_id,
            regexp_extract(author_url, 'author/show/([0-9]+)', 1) AS author_id,
            author AS author_name,
            n,
            mean,
            n5,
            (n5::DOUBLE / nullif(n, 0))::DOUBLE AS p5
        FROM ex.work_scores
        WHERE author_url IS NOT NULL
          AND author_url <> ''
          AND regexp_extract(author_url, 'author/show/([0-9]+)', 1) <> ''
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE author_pop AS
        SELECT
            author_id,
            any_value(author_name) AS author_name,
            count(*)::BIGINT AS n_works,
            sum(n)::BIGINT AS n_ratings,
            sum(n5)::BIGINT AS n5_ratings,
            max(n)::BIGINT AS max_work_n,
            avg(mean)::DOUBLE AS mean_rating
        FROM work_author
        GROUP BY author_id
        HAVING sum(n) >= 200
        """
    )
    n_a = con.execute("SELECT count(*) FROM author_pop").fetchone()[0]
    n_w = con.execute("SELECT count(*) FROM work_author").fetchone()[0]
    print(f"  authors={n_a:,} works_mapped={n_w:,} ({time.time()-t0:.1f}s)", flush=True)


def load_author_eval(con) -> dict[str, Any]:
    pos = {
        str(r[0])
        for r in con.execute(
            "SELECT author_id FROM ex.taste_authors WHERE side='literary_poll'"
        ).fetchall()
    }
    anti = {
        str(r[0])
        for r in con.execute(
            "SELECT author_id FROM ex.taste_authors WHERE side='non_literary'"
        ).fetchall()
    }
    names = {
        str(r[0]): r[1]
        for r in con.execute(
            "SELECT author_id, match_name FROM ex.taste_authors"
        ).fetchall()
    }
    return {
        "pos_authors": pos,
        "anti_authors": anti,
        "names": names,
        "n_pos": len(pos),
        "n_anti": len(anti),
    }


def evaluate_authors(
    ranked: list[dict[str, Any]], ev_a: dict[str, Any]
) -> dict[str, Any]:
    pos, anti = ev_a["pos_authors"], ev_a["anti_authors"]

    def count(ids: set[str], limit: int) -> int:
        return sum(1 for r in ranked[:limit] if r["author_id"] in ids)

    pos50 = count(pos, 50)
    anti50 = count(anti, 50)
    anti200 = count(anti, 200)
    q = 3.0 * pos50 - 4.0 * anti50 - 0.25 * anti200
    return {
        "Q_author": q,
        "pos50": pos50,
        "anti50": anti50,
        "anti200": anti200,
        "top20": [
            {
                "rank": r["rank"],
                "author_id": r["author_id"],
                "author": r.get("author") or ev_a["names"].get(r["author_id"], "?"),
                "score": r["score"],
                "n_eff": r.get("n_eff"),
            }
            for r in ranked[:20]
        ],
    }


def _load_user_author_five_star(con, *, min_fans: int = 40, max_authors_per_user: int = 80):
    """Cached person×author bipartite from 5★ events (any work by author)."""
    global _AUTHOR_GRAPH
    if _AUTHOR_GRAPH is not None:
        print("  author-graph cache hit", flush=True)
        return _AUTHOR_GRAPH

    print("  Loading user×author 5★ bipartite…", flush=True)
    t0 = time.time()
    # Aggregate in DuckDB then pull compact edges
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_author_5 AS
        SELECT
            e.user_id,
            wa.author_id,
            count(*)::BIGINT AS n5
        FROM ex.five_star_events e
        JOIN work_author wa USING (work_id)
        JOIN author_pop ap USING (author_id)
        JOIN user_feat uf USING (user_id)
        WHERE uf.n_rated >= 30
          AND uf.n5 BETWEEN 5 AND 250
          AND ap.n_ratings BETWEEN 500 AND 500000
        GROUP BY e.user_id, wa.author_id
        """
    )
    # Keep authors with enough distinct fans
    con.execute(
        f"""
        CREATE OR REPLACE TABLE author_keep AS
        SELECT author_id
        FROM user_author_5
        GROUP BY author_id
        HAVING count(DISTINCT user_id) >= {min_fans}
        """
    )
    rows = con.execute(
        f"""
        SELECT ua.user_id, ua.author_id
        FROM user_author_5 ua
        JOIN author_keep USING (author_id)
        """
    ).fetchall()
    users_of: dict[str, list[int]] = defaultdict(list)
    authors_of: dict[int, list[str]] = defaultdict(list)
    for uid, aid in rows:
        aid = str(aid)
        uid = int(uid)
        users_of[aid].append(uid)
        authors_of[uid].append(aid)
    # Cap hyperactive users
    authors_of = {
        u: aids[:max_authors_per_user]
        for u, aids in authors_of.items()
        if 3 <= len(aids) <= 200
    }
    users_of2: dict[str, list[int]] = defaultdict(list)
    for u, aids in authors_of.items():
        for a in aids:
            users_of2[a].append(u)
    users_of = {a: us for a, us in users_of2.items() if len(us) >= min_fans}
    authors_of = {
        u: [a for a in aids if a in users_of] for u, aids in authors_of.items()
    }
    authors_of = {u: aids for u, aids in authors_of.items() if len(aids) >= 3}
    # Final sync: every user listed under an author must appear in authors_of
    users_of3: dict[str, list[int]] = defaultdict(list)
    for u, aids in authors_of.items():
        for a in aids:
            users_of3[a].append(u)
    users_of = dict(users_of3)

    names = {
        str(r[0]): r[1]
        for r in con.execute("SELECT author_id, author_name FROM author_pop").fetchall()
    }
    _AUTHOR_GRAPH = {
        "users_of": users_of,
        "authors_of": authors_of,
        "names": names,
    }
    print(
        f"  authors={len(users_of):,} users={len(authors_of):,} "
        f"({time.time()-t0:.1f}s)",
        flush=True,
    )
    return _AUTHOR_GRAPH


def _author_rows_from_scores(
    scored: list[tuple[str, float, float]], names: dict[str, str]
) -> list[dict[str, Any]]:
    scored.sort(key=lambda t: (-t[1], -t[2]))
    out = []
    for i, (aid, sc, n) in enumerate(scored[:FETCH], 1):
        out.append(
            {
                "rank": i,
                "author_id": aid,
                "author": names.get(aid, "?"),
                "score": sc,
                "n_eff": n,
            }
        )
    return out


def _author_reflections(con, *, iters: int = 14):
    """One reflections pass on the cached author bipartite."""
    g = _load_user_author_five_star(con)
    d, delta = _method_of_reflections(g["users_of"], g["authors_of"], iters=iters)
    return g, d, delta


def method_author_neg_delta2(con) -> tuple[list[dict], list[dict]]:
    """Lizardo −δ² on person×author; expand top authors → flagship works."""
    g, _d, delta = _author_reflections(con, iters=14)
    users_of, names = g["users_of"], g["names"]
    m = 40.0
    scored = []
    for a, us in users_of.items():
        n = float(len(us))
        sc = -float(delta[a][2])
        scored.append((a, sc * (n / (n + m)), n))
    authors = _author_rows_from_scores(scored, names)
    works = _expand_authors_to_works(con, [r["author_id"] for r in authors])
    return authors, works


def method_author_high_order(con) -> tuple[list[dict], list[dict]]:
    g, _d, delta = _author_reflections(con, iters=14)
    users_of, names = g["users_of"], g["names"]
    m = 40.0
    scored = []
    for a, us in users_of.items():
        n = float(len(us))
        sc = abs(float(delta[a][14]))
        scored.append((a, sc * (n / (n + m)), n))
    authors = _author_rows_from_scores(scored, names)
    works = _expand_authors_to_works(con, [r["author_id"] for r in authors])
    return authors, works


def method_author_niche_enthusiasts(con) -> tuple[list[dict], list[dict]]:
    """Low d¹ users (niche-author seekers) → share of niche fans per author."""
    g, d, _delta = _author_reflections(con, iters=14)
    users_of, authors_of, names = g["users_of"], g["authors_of"], g["names"]
    biases = sorted(((u, d[u][1]) for u in authors_of), key=lambda t: t[1])
    k = max(int(0.20 * len(biases)), 50)
    niche = {u for u, _ in biases[:k]}
    print(f"  niche author-seekers: {len(niche):,}", flush=True)

    n5: dict[str, int] = defaultdict(int)
    nn: dict[str, int] = defaultdict(int)
    for a, us in users_of.items():
        for u in us:
            nn[a] += 1
            if u in niche:
                n5[a] += 1
    m, p0 = 30.0, 0.15
    scored = []
    for a, n in nn.items():
        if n < 40:
            continue
        sc = (n5[a] + m * p0) / (n + m)
        scored.append((a, sc, float(n)))
    authors = _author_rows_from_scores(scored, names)
    works = _expand_authors_to_works(con, [r["author_id"] for r in authors])
    return authors, works


def method_author_pmi_portfolio(con) -> tuple[list[dict], list[dict], list[dict]]:
    """Author PMI communities → round-robin portfolio of community heads."""
    g = _load_user_author_five_star(con)
    users_of, authors_of, names = g["users_of"], g["authors_of"], g["names"]
    users_sets = {a: set(us) for a, us in users_of.items()}
    adj = _pmi_adjacency(users_sets, min_pair=10, min_pmi=1.5, knn=6)
    print(f"  author PMI nodes={len(adj):,}", flush=True)
    labels = {a: a for a in adj}
    for it in range(12):
        order = list(adj.keys())
        order = order[it:] + order[:it]
        changed = 0
        for a in order:
            votes: Counter[str] = Counter()
            for v, wt in adj[a]:
                if v in labels:
                    votes[labels[v]] += wt
            if not votes:
                continue
            best = max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
            if best != labels[a]:
                labels[a] = best
                changed += 1
        if changed == 0:
            break
    communities: dict[str, list[str]] = defaultdict(list)
    for a, lab in labels.items():
        communities[lab].append(a)
    sized = sorted(
        ((lab, mems) for lab, mems in communities.items() if len(mems) >= 8),
        key=lambda t: -len(t[1]),
    )
    if sized and len(sized[0][1]) > 0.4 * max(len(adj), 1):
        adj = _pmi_adjacency(users_sets, min_pair=15, min_pmi=2.0, knn=4)
        labels = {a: a for a in adj}
        for it in range(10):
            order = list(adj.keys())
            order = order[it:] + order[:it]
            changed = 0
            for a in order:
                votes = Counter()
                for v, wt in adj[a]:
                    if v in labels:
                        votes[labels[v]] += wt
                if not votes:
                    continue
                best = max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]
                if best != labels[a]:
                    labels[a] = best
                    changed += 1
            if changed == 0:
                break
        communities = defaultdict(list)
        for a, lab in labels.items():
            communities[lab].append(a)
        sized = sorted(
            (
                (lab, mems)
                for lab, mems in communities.items()
                if 8 <= len(mems) <= 400
            ),
            key=lambda t: -len(t[1]),
        )
    large = sized[:20]
    print(f"  author communities: {len(large)} sizes={[len(m) for _, m in large[:12]]}", flush=True)

    # Within-community score = share of community-dense users among fans
    community_ranks: list[list[tuple[str, float, float]]] = []
    community_meta: list[dict[str, Any]] = []
    for lab, members in large:
        mset = set(members)
        dense = {
            u
            for u, aids in authors_of.items()
            if sum(1 for a in aids if a in mset) >= 3
        }
        if len(dense) < 30:
            continue
        scored = []
        for a in members:
            fans = users_of.get(a, [])
            n = float(len(fans))
            if n < 30:
                continue
            nd = sum(1 for u in fans if u in dense)
            sc = (nd + 8) / (n + 20)
            scored.append((a, sc, n))
        scored.sort(key=lambda t: (-t[1], -t[2]))
        if not scored:
            continue
        community_ranks.append(scored)
        community_meta.append(
            {
                "size": len(members),
                "dense_users": len(dense),
                "heads": [
                    {"author_id": a, "author": names.get(a, "?"), "score": sc}
                    for a, sc, _ in scored[:5]
                ],
            }
        )

    portfolio: list[tuple[str, float, float]] = []
    seen: set[str] = set()
    max_len = max((len(r) for r in community_ranks), default=0)
    for i in range(max_len):
        for ci, ranked in enumerate(community_ranks):
            if i >= len(ranked):
                continue
            a, sc, n = ranked[i]
            if a in seen:
                continue
            seen.add(a)
            portfolio.append((a, sc + 0.01 * (len(community_ranks) - ci), n))
    authors = _author_rows_from_scores(portfolio, names)
    works = _expand_authors_to_works(con, [r["author_id"] for r in authors])
    return authors, works, community_meta


def method_cross_author_book_pmi(con) -> list[dict]:
    """Book PMI eigenvector with same-author co-liking edges removed."""
    print("  Cross-author book PMI…", flush=True)
    t0 = time.time()
    rows = con.execute(
        f"""
        SELECT e.work_id, e.user_id, wa.author_id
        FROM ex.five_star_events e
        JOIN work_author wa USING (work_id)
        JOIN work_rarity wr USING (work_id)
        JOIN user_feat uf USING (user_id)
        WHERE wr.n BETWEEN 300 AND 15000
          AND uf.n_rated >= 30
          AND uf.n5 BETWEEN 5 AND 250
        """
    ).fetchall()
    work_author = {}
    users_of: dict[str, set[int]] = defaultdict(set)
    for wid, uid, aid in rows:
        wid, aid = str(wid), str(aid)
        work_author[wid] = aid
        users_of[wid].add(int(uid))
    users_of = {w: us for w, us in users_of.items() if len(us) >= 30}
    books_of_user: dict[int, list[str]] = defaultdict(list)
    for w, us in users_of.items():
        for u in us:
            books_of_user[u].append(w)

    pair_count: dict[tuple[str, str], int] = defaultdict(int)
    n_users_pairs = 0
    for _u, wlist in books_of_user.items():
        if len(wlist) < 2 or len(wlist) > 60:
            continue
        # Deduplicate to one work per author for this user (strongest anti-island)
        by_auth: dict[str, str] = {}
        for w in wlist:
            a = work_author.get(w)
            if a and a not in by_auth:
                by_auth[a] = w
        wl = list(by_auth.values())[:25]
        if len(wl) < 2:
            continue
        n_users_pairs += 1
        for i in range(len(wl)):
            for j in range(i + 1, len(wl)):
                a, b = (wl[i], wl[j]) if wl[i] < wl[j] else (wl[j], wl[i])
                pair_count[(a, b)] += 1
    print(
        f"  cross-author pairs={len(pair_count):,} from {n_users_pairs:,} users "
        f"({time.time()-t0:.1f}s)",
        flush=True,
    )
    n_u = max(len(books_of_user), 1)
    adj: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (a, b), c in pair_count.items():
        if c < 6:
            continue
        pa = len(users_of[a]) / n_u
        pb = len(users_of[b]) / n_u
        pab = c / n_u
        pmi = math.log(pab / (pa * pb + 1e-18) + 1e-18)
        if pmi <= 1.0:
            continue
        adj[a].append((b, pmi))
        adj[b].append((a, pmi))
    score = {w: 1.0 for w in adj}
    for it in range(12):
        nxt = {}
        for w, nbrs in adj.items():
            nxt[w] = sum(score.get(v, 0.0) * wt for v, wt in nbrs) / math.sqrt(
                max(len(nbrs), 1)
            )
        s = math.sqrt(sum(v * v for v in nxt.values())) or 1.0
        score = {k: v / s for k, v in nxt.items()}
    m = 40.0
    scored = []
    for w, sc in score.items():
        n = float(len(users_of[w]))
        scored.append((w, sc * (n / (n + m)), n))
    return _scores_to_rank(con, scored)


def _expand_authors_to_works(con, author_ids: list[str], *, per_author: int = 1) -> list[dict]:
    """Map ranked authors → their highest-n mid-pop catalog-ok work."""
    if not author_ids:
        return []
    con.execute("USE memory")
    con.execute("CREATE OR REPLACE TABLE ranked_authors (author_id VARCHAR, rnk INTEGER)")
    con.executemany(
        "INSERT INTO ranked_authors VALUES (?, ?)",
        [(a, i) for i, a in enumerate(author_ids[:800], 1)],
    )
    rows = con.execute(
        f"""
        WITH cand AS (
            SELECT
                wa.author_id,
                wa.work_id,
                wa.n,
                wa.p5,
                ra.rnk,
                row_number() OVER (
                    PARTITION BY wa.author_id ORDER BY wa.n DESC
                ) AS work_rank
            FROM work_author wa
            JOIN ranked_authors ra USING (author_id)
            JOIN ex.work_scores s USING (work_id)
            LEFT JOIN ex.work_flags cf ON cf.work_id = wa.work_id
            WHERE wa.n >= {MIN_RANK_N}
              AND NOT coalesce(cf.is_excluded, FALSE)
              AND NOT coalesce(cf.is_nonfiction, FALSE)
              AND NOT coalesce(cf.is_comic, FALSE)
              AND NOT coalesce(cf.is_picture_book, FALSE)
              AND NOT coalesce(cf.is_derivative, FALSE)
              AND NOT coalesce(cf.is_duplicate, FALSE)
              AND NOT coalesce(cf.is_collection, FALSE)
        )
        SELECT
            c.work_id, s.book_id, s.title, s.author, c.author_id,
            (1000.0 - c.rnk + coalesce(c.p5, 0))::DOUBLE AS score,
            c.n::DOUBLE AS n_eff, c.n, c.p5, s.mean
        FROM cand c
        JOIN ex.work_scores s USING (work_id)
        WHERE c.work_rank <= {per_author}
        ORDER BY c.rnk ASC, c.n DESC
        LIMIT {FETCH}
        """
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
                "author_id": str(r[4]),
                "score": float(r[5]),
                "n_eff": float(r[6]),
                "catalog_n": int(r[7] or 0),
                "p5": float(r[8]) if r[8] is not None else None,
                "mean": float(r[9]) if r[9] is not None else None,
            }
        )
    return out


def main() -> None:
    global _AUTHOR_GRAPH
    _AUTHOR_GRAPH = None
    clear_graph_caches()

    con = _con()
    ev_w = load_eval_sets(con)
    ev_a = load_author_eval(con)
    print(
        f"Eval works: pos={ev_w['n_pos_works']} anti={ev_w['n_anti_works']}; "
        f"authors: pos={ev_a['n_pos']} anti={ev_a['n_anti']}",
        flush=True,
    )
    materialize_base(con)
    materialize_authors(con)

    results: dict[str, Any] = {
        "meta": {
            "allowed": "(user_id, work_id, rating, author_id from author_url)",
            "papers": [
                "Airoldi 2024 nested relational legitimacy",
                "Lizardo 2018 reflections (person×item; here item=author)",
                "Vlegels & Lievens 2017 artist-preference networks (Poetics)",
                "arXiv:2303.05080 — prefer author-similarity over book-similarity",
            ],
            "eval_authors": {"n_pos": ev_a["n_pos"], "n_anti": ev_a["n_anti"]},
            "eval_works": {
                "n_pos": ev_w["n_pos_works"],
                "n_anti": ev_w["n_anti_works"],
            },
        },
        "methods": {},
    }

    # Author methods that share one bipartite + reflections cache
    author_methods = [
        ("author_neg_delta2", lambda: method_author_neg_delta2(con)),
        ("author_niche_enthusiasts", lambda: method_author_niche_enthusiasts(con)),
        ("author_high_order", lambda: method_author_high_order(con)),
        ("author_pmi_portfolio", lambda: method_author_pmi_portfolio(con)),
    ]

    for name, fn in author_methods:
        print(f"\n=== {name} ===", flush=True)
        t0 = time.time()
        try:
            out = fn()
            if name == "author_pmi_portfolio":
                authors, works, communities = out
            else:
                authors, works = out
                communities = None
            ms = int((time.time() - t0) * 1000)
            a_met = evaluate_authors(authors, ev_a)
            w_met = evaluate(works, ev_w)
            blob: dict[str, Any] = {
                "elapsed_ms": ms,
                "author_metrics": a_met,
                "work_metrics": w_met,
            }
            if communities is not None:
                blob["communities"] = communities[:12]
            results["methods"][name] = blob
            print(
                f"  {ms}ms authorQ={a_met['Q_author']:.1f} "
                f"apos50={a_met['pos50']} aanti50={a_met['anti50']} | "
                f"workQ={w_met['Q']:.1f} wpos50={w_met['pos50']} "
                f"wanti50={w_met['anti50']}",
                flush=True,
            )
            for r in a_met["top20"][:8]:
                print(f"    A{r['rank']:2d}. {r['author'][:50]}", flush=True)
            for r in w_met["top20"][:5]:
                print(
                    f"    W{r['rank']:2d}. {r['title'][:48]} — {r['author'][:22]}",
                    flush=True,
                )
        except Exception as exc:
            results["methods"][name] = {"error": str(exc)}
            print(f"  FAILED: {exc}", flush=True)
            import traceback

            traceback.print_exc()

    print("\n=== cross_author_book_pmi ===", flush=True)
    t0 = time.time()
    try:
        works = method_cross_author_book_pmi(con)
        ms = int((time.time() - t0) * 1000)
        w_met = evaluate(works, ev_w)
        results["methods"]["cross_author_book_pmi"] = {
            "elapsed_ms": ms,
            "work_metrics": w_met,
        }
        print(
            f"  {ms}ms workQ={w_met['Q']:.1f} pos50={w_met['pos50']} "
            f"anti50={w_met['anti50']} anti1000={w_met['anti1000']}",
            flush=True,
        )
        for r in w_met["top20"][:8]:
            print(f"    {r['rank']:2d}. {r['title'][:48]} — {r['author'][:22]}", flush=True)
    except Exception as exc:
        results["methods"]["cross_author_book_pmi"] = {"error": str(exc)}
        print(f"  FAILED: {exc}", flush=True)
        import traceback

        traceback.print_exc()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    _write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD}", flush=True)
    con.close()


def _write_report(results: dict[str, Any]) -> None:
    lines = [
        "# Author-level literary consensus — probe results",
        "",
        "Discovery uses `(user_id, work_id, rating, author_id)` with `author_id` "
        "from Goodreads `author_url`. Taste/poll labels are **evaluation only**.",
        "",
        "## Why author?",
        "",
        "Book-level co-5★ clustering produced **author islands** (Joyce↔Joyce, "
        "Pynchon↔Pynchon). Adding author is not more of the same signal: it is "
        "Airoldi’s nested level (work → artist). Person×author reflections / PMI "
        "should connect Dostoevsky↔Joyce readers without requiring book-pair "
        "co-citation. Cross-author book PMI drops same-author edges explicitly.",
        "",
        "## Method scores",
        "",
        "| method | author Q | a_pos50 | a_anti50 | work Q | w_pos50 | w_anti50 | ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, blob in results["methods"].items():
        if "error" in blob:
            lines.append(f"| {name} | ERR | | | | | | |")
            continue
        a = blob.get("author_metrics") or {}
        w = blob.get("work_metrics") or {}
        lines.append(
            f"| {name} | {a.get('Q_author', float('nan')):.1f} | {a.get('pos50', '')} | "
            f"{a.get('anti50', '')} | {w.get('Q', float('nan')):.1f} | "
            f"{w.get('pos50', '')} | {w.get('anti50', '')} | {blob['elapsed_ms']} |"
        )
    lines += ["", "## Top authors / works", ""]
    for name, blob in results["methods"].items():
        lines.append(f"### {name}")
        if "error" in blob:
            lines.append(f"Error: {blob['error']}")
            lines.append("")
            continue
        if blob.get("author_metrics"):
            lines.append("Authors:")
            for r in blob["author_metrics"]["top20"][:12]:
                lines.append(f"- {r['rank']}. {r['author']} (n≈{r.get('n_eff', 0):.0f})")
        if blob.get("work_metrics"):
            lines.append("Works (expanded / ranked):")
            for r in blob["work_metrics"]["top20"][:12]:
                lines.append(
                    f"- {r['rank']}. {r['title']} — {r['author']} (n≈{r['n']:.0f})"
                )
        if blob.get("communities"):
            lines.append("Author communities (heads):")
            for i, c in enumerate(blob["communities"][:8]):
                heads = ", ".join(h["author"] for h in c["heads"][:4])
                lines.append(
                    f"- C{i} size={c['size']} dense={c['dense_users']}: {heads}"
                )
        lines.append("")
    lines += [
        "## Scholar Labs query (copy-paste)",
        "",
        "```",
        "bipartite person-author OR person-artist taste network OR "
        '"method of reflections" OR "two-mode" cultural hierarchy OR '
        "omnivorousness ranking authors books OR Goodreads co-reading "
        "author similarity literary canon -recommendation -collaborative-filtering",
        "```",
        "",
        "Related seeds: Lizardo 2018 Poetics; Vlegels & Lievens 2017 Poetics "
        "(artist preferences); Airoldi 2024 nested legitimacy; "
        "arXiv:2303.05080 (author-similarity networks on Goodreads).",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

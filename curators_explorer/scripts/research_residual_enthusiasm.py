#!/usr/bin/env python3
"""Hierarchical residual-enthusiasm ranking (serious-reader contrastive esteem).

Keeps the careful cohort machinery (focus vs anti-like users), but replaces raw
P(5) differences with baseline-adjusted residuals + empirical-Bayes shrinkage.

Fixes vs old contrastive score:
  - No "missing anti ⇒ 0.85·p5_c" positive inventing
  - User generosity and book baseline appeal partialled out
  - Thin-support works shrunk toward 0
  - Optional author→work hierarchical blend

Also freezes probe reporting without the Q anti-median bonus, and reports an
author-disjoint poll held-out recall.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_residual_enthusiasm
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_feature_sensitivity import (
    _moments,
    build_affinity,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    load_eval_sets,
    materialize_base,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    build_user_features,
    filler_eval,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "residual_enthusiasm.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "RESIDUAL_ENTHUSIASM_REPORT.md"
WEIGHTS_CAREFUL = Path(__file__).resolve().parents[1] / "data" / "weights_careful_cotrain.json"
STABILITY_JSON = Path(__file__).resolve().parents[1] / "data" / "stability_analysis.json"

TOP_FRAC = 0.06
MAX_N = 120_000
MIN_VOTES = 30
SHRINK_K = 40.0
AUTHOR_BLEND = 0.30  # weight on author-level shrunk residual
SEED = 7


def load_weights() -> dict[str, Any]:
    if WEIGHTS_CAREFUL.exists():
        return json.loads(WEIGHTS_CAREFUL.read_text(encoding="utf-8"))
    p = Path(__file__).resolve().parents[1] / "data" / "cotrained_weights.json"
    return json.loads(p.read_text(encoding="utf-8"))


def rank_scored(con, score_sql: str) -> list[dict]:
    """Like rank_from_sql but keeps n_c / n_a when present."""
    from curators_explorer.scripts.research_ratings_only_canon import FETCH, catalog_ok_sql

    rows = con.execute(
        f"""
        SELECT
            s.work_id,
            s.book_id,
            s.title,
            s.author,
            x.score,
            x.n_eff,
            coalesce(x.n_c, x.n_eff) AS n_c,
            coalesce(x.n_a, 0) AS n_a,
            wr.n AS catalog_n
        FROM ({score_sql}) x
        JOIN ex.work_scores s USING (work_id)
        JOIN work_rarity wr USING (work_id)
        LEFT JOIN ex.work_flags cf ON cf.work_id = s.work_id
        WHERE TRUE
        {catalog_ok_sql('s')}
        ORDER BY x.score DESC NULLS LAST, x.n_eff DESC
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
                "score": float(r[4]) if r[4] is not None else 0.0,
                "n_eff": float(r[5]) if r[5] is not None else 0.0,
                "n_c": float(r[6]) if r[6] is not None else 0.0,
                "n_a": float(r[7]) if r[7] is not None else 0.0,
                "catalog_n": int(r[8]) if r[8] is not None else 0,
            }
        )
    return out


def load_sticky() -> list[str]:
    d = json.loads(STABILITY_JSON.read_text(encoding="utf-8"))
    return [
        e["work_id"]
        for e in d["sticky_baseline_top50"]
        if e.get("in_top50_rate", 0) >= 0.8
    ]


def probe_metrics(rows: list[dict], ev: dict[str, Any], sticky: set[str]) -> dict[str, Any]:
    """Probe metrics without the anti-median Q bonus."""
    pos, anti, fillers = ev["pos_works"], ev["anti_works"], ev["filler_works"]

    def count(ids: set[str], limit: int) -> int:
        return sum(1 for r in rows[:limit] if r["work_id"] in ids)

    pos50 = count(pos, 50)
    anti50 = count(anti, 50)
    anti1000 = count(anti, 1000)
    fill50 = count(fillers, 50)
    sticky50 = count(sticky, 50)
    # support among top 50
    n_c_vals = [float(r.get("n_c") or r.get("n_eff") or 0) for r in rows[:50]]
    n_a_vals = [float(r.get("n_a") or 0) for r in rows[:50]]
    q_clean = 3.0 * pos50 - 4.0 * anti50 - 0.5 * anti1000 - 2.0 * fill50
    return {
        "Q_clean": q_clean,
        "pos50": pos50,
        "anti50": anti50,
        "anti1000": anti1000,
        "filler50": fill50,
        "sticky50": sticky50,
        "top50_mean_n_c": sum(n_c_vals) / max(len(n_c_vals), 1),
        "top50_mean_n_a": sum(n_a_vals) / max(len(n_a_vals), 1),
        "top50_frac_missing_anti": sum(1 for x in n_a_vals if x < MIN_VOTES) / max(len(n_a_vals), 1),
    }


def author_disjoint_sets(con) -> dict[str, set[str]]:
    """Split poll works by author_id hash so validation authors never appear in train."""
    rows = con.execute(
        f"""
        SELECT p.work_id, wa.author_id, p.poll_rank
        FROM ex.poll_works p
        JOIN work_ax wa USING (work_id)
        WHERE p.n >= 2000 AND wa.author_id IS NOT NULL AND wa.author_id <> ''
        """
    ).fetchall()
    # authors → works
    by_auth: dict[str, list[tuple[str, int]]] = {}
    for wid, aid, pr in rows:
        by_auth.setdefault(str(aid), []).append((str(wid), int(pr or 0)))
    train_w, test_w = set(), set()
    train_a, test_a = set(), set()
    for aid, works in sorted(by_auth.items()):
        # stable split on author id
        bucket = sum(ord(c) for c in aid) % 2
        if bucket == 1:
            train_a.add(aid)
            train_w.update(w for w, _ in works)
        else:
            test_a.add(aid)
            test_w.update(w for w, _ in works)
    return {
        "train_works": train_w,
        "test_works": test_w,
        "train_authors": train_a,
        "test_authors": test_a,
    }


def heldout_recall(rows: list[dict], heldout: set[str], *, ks=(50, 100, 200, 500)) -> dict[str, Any]:
    ranks = {r["work_id"]: r["rank"] for r in rows}
    in_rank = [ranks[w] for w in heldout if w in ranks]
    out = {"n_heldout": len(heldout), "n_ranked": len(in_rank)}
    for k in ks:
        out[f"recall@{k}"] = sum(1 for r in in_rank if r <= k) / max(len(heldout), 1)
        out[f"hits@{k}"] = sum(1 for r in in_rank if r <= k)
    if in_rank:
        out["median_rank"] = float(sorted(in_rank)[len(in_rank) // 2])
    else:
        out["median_rank"] = None
    return out


def pick_cohorts(con, *, top_frac: float = TOP_FRAC) -> dict[str, int]:
    thr_c = float(
        con.execute(
            f"""
            SELECT approx_quantile(classic_affinity, {1.0 - top_frac}::FLOAT)
            FROM user_affinity_gated
            """
        ).fetchone()[0]
    )
    thr_a = float(
        con.execute(
            f"""
            SELECT approx_quantile(anti_raw, {1.0 - top_frac}::FLOAT)
            FROM user_affinity
            WHERE series_share_5 >= 0.45 OR binge_mean_5 >= 2.5
            """
        ).fetchone()[0]
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_focus_top AS
        SELECT user_id FROM user_affinity_gated WHERE classic_affinity >= {thr_c}
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE cohort_anti_top AS
        SELECT user_id FROM user_affinity
        WHERE anti_raw >= {thr_a}
          AND (series_share_5 >= 0.45 OR binge_mean_5 >= 2.5)
        """
    )
    n_f = con.execute("SELECT count(*) FROM cohort_focus_top").fetchone()[0]
    n_a = con.execute("SELECT count(*) FROM cohort_anti_top").fetchone()[0]
    return {"n_focus": int(n_f), "n_anti": int(n_a), "thr_c": thr_c, "thr_a": thr_a}


def materialize_residuals(con) -> None:
    """y=I(5★); residual = y - user_mean - book_mean + global_mean (mid-pop works)."""
    print("  computing user/book baselines + residuals…", flush=True)
    t0 = time.time()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE rate_y AS
        SELECT
            e.user_id,
            e.work_id,
            (e.rating = 5)::DOUBLE AS y
        FROM ex.all_rating_events e
        JOIN work_rarity wr ON wr.work_id = e.work_id
        WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
        """
    )
    mu = float(con.execute("SELECT avg(y) FROM rate_y").fetchone()[0])
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_base AS
        SELECT user_id, avg(y) AS u_mean, count(*)::BIGINT AS u_n
        FROM rate_y GROUP BY user_id
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE book_base AS
        SELECT work_id, avg(y) AS b_mean, count(*)::BIGINT AS b_n
        FROM rate_y GROUP BY work_id
        """
    )
    # Shrink user/book means slightly toward global (k_u=20, k_b=50)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE rate_resid AS
        SELECT
            r.user_id,
            r.work_id,
            r.y,
            (
                r.y
                - ((u.u_n * u.u_mean + 20 * {mu}) / (u.u_n + 20))
                - ((b.b_n * b.b_mean + 50 * {mu}) / (b.b_n + 50))
                + {mu}
            )::DOUBLE AS resid
        FROM rate_y r
        JOIN user_base u USING (user_id)
        JOIN book_base b USING (work_id)
        """
    )
    print(f"  residuals ready (μ={mu:.3f}, {time.time()-t0:.1f}s)", flush=True)


def rank_raw_p5_fixed(con, *, min_votes: int = MIN_VOTES) -> list[dict]:
    """p5 contrast requiring bilateral support (no missing-anti inventing)."""
    sql = f"""
        WITH c_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_c,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_c
            FROM ex.all_rating_events e
            JOIN cohort_focus_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        ),
        a_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_a,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_a
            FROM ex.all_rating_events e
            JOIN cohort_anti_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            c.work_id,
            (c.p5_c - a.p5_a)::DOUBLE AS score,
            c.n_c::DOUBLE AS n_c,
            a.n_a::DOUBLE AS n_a,
            least(c.n_c, a.n_a)::DOUBLE AS n_eff
        FROM c_agg c
        INNER JOIN a_agg a USING (work_id)
        WHERE c.n_c >= {min_votes}
    """
    return rank_scored(con, sql)


def rank_raw_p5_legacy(con, *, min_votes: int = MIN_VOTES) -> list[dict]:
    """Legacy missing-anti fallback (for side-by-side diagnosis only)."""
    sql = f"""
        WITH c_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_c,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_c
            FROM ex.all_rating_events e
            JOIN cohort_focus_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        ),
        a_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_a,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_a
            FROM ex.all_rating_events e
            JOIN cohort_anti_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            c.work_id,
            (c.p5_c - coalesce(a.p5_a, c.p5_c * 0.85))::DOUBLE AS score,
            c.n_c::DOUBLE AS n_c,
            coalesce(a.n_a, 0)::DOUBLE AS n_a,
            least(c.n_c, coalesce(a.n_a, c.n_c))::DOUBLE AS n_eff
        FROM c_agg c
        LEFT JOIN a_agg a USING (work_id)
        WHERE c.n_c >= {min_votes}
    """
    return rank_scored(con, sql)


def rank_residual(
    con,
    *,
    min_votes: int = MIN_VOTES,
    k: float = SHRINK_K,
    author_blend: float = AUTHOR_BLEND,
    require_anti: bool = False,
) -> list[dict]:
    """Shrunk focus residual − shrunk anti residual; missing anti → 0 (not a bonus)."""
    anti_filter = f"WHERE w.n_a >= {min_votes}" if require_anti else ""
    sql = f"""
        WITH c_agg AS (
            SELECT
                r.work_id,
                count(*)::BIGINT AS n_c,
                avg(r.resid)::DOUBLE AS m_c
            FROM rate_resid r
            JOIN cohort_focus_top t USING (user_id)
            GROUP BY r.work_id
            HAVING count(*) >= {min_votes}
        ),
        a_agg AS (
            SELECT
                r.work_id,
                count(*)::BIGINT AS n_a,
                avg(r.resid)::DOUBLE AS m_a
            FROM rate_resid r
            JOIN cohort_anti_top t USING (user_id)
            GROUP BY r.work_id
            HAVING count(*) >= {min_votes}
        ),
        work_scores AS (
            SELECT
                c.work_id,
                c.n_c,
                coalesce(a.n_a, 0)::BIGINT AS n_a,
                (c.n_c / (c.n_c + {k})) * c.m_c AS focus_shrunk,
                CASE
                    WHEN a.n_a IS NULL THEN 0.0
                    ELSE (a.n_a / (a.n_a + {k})) * a.m_a
                END AS anti_shrunk
            FROM c_agg c
            LEFT JOIN a_agg a USING (work_id)
        ),
        with_author AS (
            SELECT
                w.*,
                wa.author_id
            FROM work_scores w
            LEFT JOIN work_ax wa USING (work_id)
            {anti_filter}
        ),
        author_level AS (
            SELECT
                author_id,
                sum(n_c * (focus_shrunk - anti_shrunk)) / nullif(sum(n_c), 0) AS author_score
            FROM with_author
            WHERE author_id IS NOT NULL AND author_id <> ''
            GROUP BY author_id
        )
        SELECT
            w.work_id,
            (
                (1.0 - {author_blend}) * (w.focus_shrunk - w.anti_shrunk)
                + {author_blend} * coalesce(al.author_score, w.focus_shrunk - w.anti_shrunk)
            )::DOUBLE AS score,
            w.n_c::DOUBLE AS n_c,
            w.n_a::DOUBLE AS n_a,
            least(w.n_c, CASE WHEN w.n_a = 0 THEN w.n_c ELSE w.n_a END)::DOUBLE AS n_eff
        FROM with_author w
        LEFT JOIN author_level al USING (author_id)
    """
    return rank_scored(con, sql)


def top15(rows: list[dict]) -> list[dict]:
    return [
        {
            "rank": r["rank"],
            "title": r["title"],
            "author": r["author"],
            "score": r["score"],
            "n_c": r.get("n_c"),
            "n_a": r.get("n_a"),
        }
        for r in rows[:15]
    ]


def main() -> None:
    t_all = time.time()
    con = _con()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    print("Setup…", flush=True)
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    label_cohorts(con)

    w = load_weights()
    print(f"  weights source: {w.get('source', WEIGHTS_CAREFUL.name)}", flush=True)
    moments = _moments(con)
    g = w["gates"]
    build_affinity(
        con,
        moments,
        classic_terms=w["classic_terms"],
        anti_terms=w["anti_terms"],
        normie_terms=w["normie_terms"],
        lam_a=float(w.get("lambda_anti", 0.85)),
        lam_n=float(w.get("lambda_normie", 0.75)),
        series_gate=float(g["series_gate"]),
        mega_gate=float(g["mega_gate"]),
        binge_gate=float(g["binge_gate"]),
        span_gate=float(g["span_gate"]),
    )
    cohorts = pick_cohorts(con, top_frac=float(w.get("top_frac", TOP_FRAC)))
    print(f"  cohorts focus={cohorts['n_focus']:,} anti={cohorts['n_anti']:,}", flush=True)

    adj = author_disjoint_sets(con)
    print(
        f"  author-disjoint poll: train_authors={len(adj['train_authors'])} "
        f"test_authors={len(adj['test_authors'])} "
        f"train_works={len(adj['train_works'])} test_works={len(adj['test_works'])}",
        flush=True,
    )

    materialize_residuals(con)

    methods = {}
    print("\n=== legacy p5 (missing-anti bonus) ===", flush=True)
    legacy = rank_raw_p5_legacy(con)
    methods["legacy_p5"] = {
        "probe": probe_metrics(legacy, ev, sticky),
        "fill": filler_eval(legacy, con),
        "heldout_author_disjoint": heldout_recall(legacy, adj["test_works"]),
        "top15": top15(legacy),
    }
    print(
        f"  Q_clean={methods['legacy_p5']['probe']['Q_clean']:.1f} "
        f"pos50={methods['legacy_p5']['probe']['pos50']} "
        f"anti50={methods['legacy_p5']['probe']['anti50']} "
        f"fill50={methods['legacy_p5']['probe']['filler50']} "
        f"sticky50={methods['legacy_p5']['probe']['sticky50']} "
        f"missing_anti_top50={methods['legacy_p5']['probe']['top50_frac_missing_anti']:.2f}",
        flush=True,
    )

    print("\n=== fixed p5 (missing anti → 0) ===", flush=True)
    fixed = rank_raw_p5_fixed(con)
    methods["fixed_p5"] = {
        "probe": probe_metrics(fixed, ev, sticky),
        "fill": filler_eval(fixed, con),
        "heldout_author_disjoint": heldout_recall(fixed, adj["test_works"]),
        "top15": top15(fixed),
    }
    print(
        f"  Q_clean={methods['fixed_p5']['probe']['Q_clean']:.1f} "
        f"pos50={methods['fixed_p5']['probe']['pos50']} "
        f"anti50={methods['fixed_p5']['probe']['anti50']} "
        f"fill50={methods['fixed_p5']['probe']['filler50']} "
        f"sticky50={methods['fixed_p5']['probe']['sticky50']} "
        f"missing_anti_top50={methods['fixed_p5']['probe']['top50_frac_missing_anti']:.2f}",
        flush=True,
    )

    print("\n=== residual enthusiasm (shrunk + author blend) ===", flush=True)
    resid = rank_residual(con)
    methods["residual"] = {
        "probe": probe_metrics(resid, ev, sticky),
        "fill": filler_eval(resid, con),
        "heldout_author_disjoint": heldout_recall(resid, adj["test_works"]),
        "top15": top15(resid),
    }
    print(
        f"  Q_clean={methods['residual']['probe']['Q_clean']:.1f} "
        f"pos50={methods['residual']['probe']['pos50']} "
        f"anti50={methods['residual']['probe']['anti50']} "
        f"fill50={methods['residual']['probe']['filler50']} "
        f"sticky50={methods['residual']['probe']['sticky50']} "
        f"missing_anti_top50={methods['residual']['probe']['top50_frac_missing_anti']:.2f}",
        flush=True,
    )
    print(
        f"  author-disjoint held-out recall@200="
        f"{methods['residual']['heldout_author_disjoint']['recall@200']:.3f} "
        f"(legacy {methods['legacy_p5']['heldout_author_disjoint']['recall@200']:.3f})",
        flush=True,
    )

    print("\n=== residual variants ===", flush=True)
    for label, kwargs in (
        ("residual_bilateral", {"require_anti": True}),
        ("residual_no_author", {"author_blend": 0.0}),
        ("residual_bilateral_no_author", {"require_anti": True, "author_blend": 0.0}),
    ):
        rows = rank_residual(con, **kwargs)
        methods[label] = {
            "probe": probe_metrics(rows, ev, sticky),
            "fill": filler_eval(rows, con),
            "heldout_author_disjoint": heldout_recall(rows, adj["test_works"]),
            "top15": top15(rows),
        }
        p = methods[label]["probe"]
        h = methods[label]["heldout_author_disjoint"]
        print(
            f"  {label}: Q_clean={p['Q_clean']:.1f} pos50={p['pos50']} "
            f"fill50={p['filler50']} sticky50={p['sticky50']} "
            f"heldout@200={h['recall@200']:.3f}",
            flush=True,
        )

    results = {
        "meta": {
            "shrink_k": SHRINK_K,
            "author_blend": AUTHOR_BLEND,
            "min_votes": MIN_VOTES,
            "top_frac": TOP_FRAC,
            "weights": str(WEIGHTS_CAREFUL),
            "cohorts": cohorts,
            "author_disjoint": {
                "n_train_authors": len(adj["train_authors"]),
                "n_test_authors": len(adj["test_authors"]),
                "n_train_works": len(adj["train_works"]),
                "n_test_works": len(adj["test_works"]),
            },
        },
        "methods": methods,
    }
    OUT_JSON.write_text(json.dumps(results, indent=2, default=float) + "\n")

    lines = [
        "# Residual enthusiasm ranking",
        "",
        "Same careful focus/anti cohorts; book score = shrunk residual enthusiasm",
        "(focus − anti), with baselines for user generosity and book appeal removed.",
        "Missing anti evidence contributes **0**, not a positive bonus.",
        "",
        "## Probe metrics (no anti-median Q bonus)",
        "",
        "| method | Q_clean | pos50 | anti50 | filler50 | sticky50 | miss-anti@50 | heldout recall@200 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in (
        "legacy_p5",
        "fixed_p5",
        "residual",
        "residual_bilateral",
        "residual_no_author",
        "residual_bilateral_no_author",
    ):
        if name not in methods:
            continue
        p = methods[name]["probe"]
        h = methods[name]["heldout_author_disjoint"]
        lines.append(
            f"| {name} | {p['Q_clean']:.1f} | {p['pos50']} | {p['anti50']} | "
            f"{p['filler50']} | {p['sticky50']} | {p['top50_frac_missing_anti']:.2f} | "
            f"{h['recall@200']:.3f} |"
        )
    # pick best by heldout then Q_clean for display head
    best_name = max(
        [n for n in methods if n.startswith("residual")],
        key=lambda n: (
            methods[n]["heldout_author_disjoint"]["recall@200"],
            methods[n]["probe"]["Q_clean"],
            -methods[n]["probe"]["filler50"],
        ),
    )
    lines += ["", f"## Best residual variant top 15 (`{best_name}`)", ""]
    for r in methods[best_name]["top15"]:
        lines.append(
            f"- {r['rank']}. {r['title']} — {r['author']} "
            f"(n_c={r.get('n_c')}, n_a={r.get('n_a')})"
        )
    lines += ["", "## Legacy p5 top 15 (for contrast)", ""]
    for r in methods["legacy_p5"]["top15"]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    lines += [
        "",
        "## Notes",
        "",
        "- Weights: careful cotrain freeze (`weights_careful_cotrain.json`).",
        "- Iterative sparse weights kept separately as `weights_iter_sparse.json`.",
        f"- Shrinkage k={SHRINK_K}, default author blend={AUTHOR_BLEND}.",
        "- `fixed_p5` here = bilateral p5 contrast (INNER JOIN on anti support); same head-ish metrics as legacy but floods anti into ranks 51–1000 (Q_clean collapses via anti1000).",
        "- Best residual variant so far: `residual_no_author` — higher poll pos50 + slightly better author-disjoint held-out; more school-canon / filler in the head; sticky down vs legacy.",
        "- Tradeoff is real: residual improves identification metrics a bit while shifting from modernist sticky core toward syllabus/school classics.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)


if __name__ == "__main__":
    main()

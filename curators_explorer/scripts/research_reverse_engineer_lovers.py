#!/usr/bin/env python3
"""Reverse-engineer the user cohort behind literary-classic seeds.

EXPLICITLY seed-informed (confirmation-bias risk acknowledged). Goal is
insight: characterize users who love lit-2014-2024 / deep-poll works, then
test whether that cohort recovers *held-out* classics and what else they
elevate.

Discovery for ranking still uses only ratings(+author aggregates) of the
cohort; seeds define membership only.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_reverse_engineer_lovers
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_ratings_only_canon import (
    FETCH,
    MIN_RANK_N,
    _con,
    catalog_ok_sql,
    evaluate,
    load_eval_sets,
    materialize_base,
    rank_from_sql,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "reverse_engineer_lovers.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "REVERSE_ENGINEER_LOVERS_REPORT.md"

MIN_SEED_N = 2000  # higher min ratings on seed works (user request)
MIN_LOVER_SEED_HITS = 3
LOVER_N_RATED_MIN = 40


def materialize_seeds(con) -> dict[str, Any]:
    """poll / deep_poll seeds with higher min-n; train/test split by rank."""
    print("Materializing classic seeds…", flush=True)
    con.execute("USE memory")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE seed_all AS
        SELECT
            work_id,
            poll_rank,
            poll_title,
            poll_author,
            work_title,
            n,
            prestige,
            'poll' AS seed_source
        FROM ex.poll_works
        WHERE n >= {MIN_SEED_N}
        UNION
        SELECT
            work_id,
            poll_rank,
            poll_title,
            poll_author,
            work_title,
            n,
            prestige,
            'deep_poll' AS seed_source
        FROM ex.deep_poll_works
        WHERE n >= {MIN_SEED_N}
          AND work_id NOT IN (SELECT work_id FROM ex.poll_works WHERE n >= {MIN_SEED_N})
        """
    )
    # Prefer poll_works ranking for split; attach unique ranks
    con.execute(
        f"""
        CREATE OR REPLACE TABLE seed_ranked AS
        SELECT
            work_id,
            poll_rank,
            poll_title,
            poll_author,
            work_title,
            n,
            prestige,
            CASE WHEN (poll_rank % 2) = 1 THEN 'train' ELSE 'test' END AS split
        FROM ex.poll_works
        WHERE n >= {MIN_SEED_N}
        """
    )
    n_all = con.execute("SELECT count(*) FROM seed_ranked").fetchone()[0]
    n_tr = con.execute("SELECT count(*) FROM seed_ranked WHERE split='train'").fetchone()[0]
    n_te = con.execute("SELECT count(*) FROM seed_ranked WHERE split='test'").fetchone()[0]
    tops = con.execute(
        """
        SELECT poll_rank, poll_title, poll_author, n, split
        FROM seed_ranked ORDER BY poll_rank LIMIT 12
        """
    ).fetchall()
    meta = {
        "min_seed_n": MIN_SEED_N,
        "n_seeds": n_all,
        "n_train": n_tr,
        "n_test": n_te,
        "top12": [
            {
                "rank": r[0],
                "title": r[1],
                "author": r[2],
                "n": int(r[3]),
                "split": r[4],
            }
            for r in tops
        ],
    }
    print(f"  seeds={n_all} train={n_tr} test={n_te} (min n≥{MIN_SEED_N})", flush=True)
    return meta


def define_lovers(con, *, seed_split: str = "train", min_hits: int = MIN_LOVER_SEED_HITS) -> dict[str, Any]:
    """Users with ≥min_hits 5★ on seed works in the given split (+ engaged)."""
    if seed_split == "train":
        where_seed = "s.split = 'train'"
    elif seed_split == "test":
        where_seed = "s.split = 'test'"
    else:
        where_seed = "TRUE"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE lover_users AS
        WITH hits AS (
            SELECT
                e.user_id,
                count(DISTINCT e.work_id)::BIGINT AS seed_hits_5,
                count(*)::BIGINT AS seed_ratings
            FROM ex.all_rating_events e
            JOIN seed_ranked s ON s.work_id = e.work_id AND ({where_seed})
            WHERE e.rating = 5
            GROUP BY e.user_id
            HAVING count(DISTINCT e.work_id) >= {min_hits}
        )
        SELECT
            h.user_id,
            h.seed_hits_5,
            h.seed_ratings,
            uf.n_rated,
            uf.five_rate,
            uf.mean_rating,
            uf.n5,
            uf.depth_ge4,
            uf.n_ge4_midpop,
            uf.n_ge4_popular,
            uf.mean_logn_5
        FROM hits h
        JOIN user_feat uf USING (user_id)
        WHERE uf.n_rated >= {LOVER_N_RATED_MIN}
        """
    )
    n = con.execute("SELECT count(*) FROM lover_users").fetchone()[0]
    stats = con.execute(
        """
        SELECT
            avg(seed_hits_5), avg(n_rated), avg(five_rate), avg(mean_rating),
            avg(depth_ge4), avg(mean_logn_5),
            approx_quantile(seed_hits_5, 0.5::FLOAT),
            approx_quantile(n_rated, 0.5::FLOAT)
        FROM lover_users
        """
    ).fetchone()
    meta = {
        "seed_split": seed_split,
        "min_hits": min_hits,
        "n_lovers": n,
        "avg_seed_hits_5": float(stats[0] or 0),
        "avg_n_rated": float(stats[1] or 0),
        "avg_five_rate": float(stats[2] or 0),
        "avg_mean_rating": float(stats[3] or 0),
        "avg_depth_ge4": float(stats[4]) if stats[4] is not None else None,
        "avg_mean_logn_5": float(stats[5]) if stats[5] is not None else None,
        "med_seed_hits": float(stats[6] or 0),
        "med_n_rated": float(stats[7] or 0),
    }
    print(
        f"  lovers({seed_split}, hits≥{min_hits})={n:,} "
        f"avg_hits={meta['avg_seed_hits_5']:.1f} avg_n={meta['avg_n_rated']:.0f} "
        f"five_rate={meta['avg_five_rate']:.3f}",
        flush=True,
    )
    return meta


def matched_controls(con) -> dict[str, Any]:
    """Controls matched on n_rated decile, excluding lovers."""
    con.execute(
        """
        CREATE OR REPLACE TABLE control_users AS
        WITH lover_decile AS (
            SELECT
                user_id,
                ntile(10) OVER (ORDER BY n_rated) AS dec
            FROM lover_users
        ),
        feat_decile AS (
            SELECT
                user_id,
                n_rated,
                five_rate,
                mean_rating,
                n5,
                depth_ge4,
                mean_logn_5,
                ntile(10) OVER (ORDER BY n_rated) AS dec
            FROM user_feat
            WHERE n_rated >= 40
              AND user_id NOT IN (SELECT user_id FROM lover_users)
        ),
        need AS (
            SELECT dec, count(*)::BIGINT AS n
            FROM lover_decile
            GROUP BY dec
        ),
        sampled AS (
            SELECT
                f.*,
                row_number() OVER (PARTITION BY f.dec ORDER BY f.user_id) AS rn,
                n.n AS need_n
            FROM feat_decile f
            JOIN need n USING (dec)
        )
        SELECT user_id, n_rated, five_rate, mean_rating, n5, depth_ge4, mean_logn_5
        FROM sampled
        WHERE rn <= need_n
        """
    )
    n = con.execute("SELECT count(*) FROM control_users").fetchone()[0]
    print(f"  matched controls={n:,}", flush=True)
    return {"n_controls": n}


def compare_cohorts(con) -> dict[str, Any]:
    """Effect sizes: lover vs control on ratings-only features + blockbuster resist."""
    # Blockbuster / author features for both cohorts
    thr_n = float(
        con.execute(
            "SELECT approx_quantile(n, 0.995::FLOAT) FROM work_rarity"
        ).fetchone()[0]
    )
    for table, out in [("lover_users", "lover_ext"), ("control_users", "control_ext")]:
        con.execute(
            f"""
            CREATE OR REPLACE TABLE {out} AS
            SELECT
                u.user_id,
                u.n_rated,
                u.five_rate,
                u.mean_rating,
                u.n5,
                u.depth_ge4,
                u.mean_logn_5,
                (
                    count(*) FILTER (WHERE wr.n >= {thr_n} AND e.rating = 5)::DOUBLE
                    / nullif(count(*) FILTER (WHERE wr.n >= {thr_n}), 0)
                ) AS p5_blockbuster,
                count(DISTINCT wa.author_id)::BIGINT AS n_authors_5,
                (
                    count(DISTINCT wa.author_id)::DOUBLE
                    / nullif(count(*) FILTER (WHERE e.rating = 5), 0)
                ) AS author_diversity_5,
                avg(ln(1.0 + wr.n)) FILTER (WHERE e.rating = 5) AS mean_logn_5_re
            FROM {table} u
            JOIN ex.all_rating_events e USING (user_id)
            JOIN work_rarity wr USING (work_id)
            LEFT JOIN (
                SELECT
                    work_id,
                    regexp_extract(author_url, 'author/show/([0-9]+)', 1) AS author_id
                FROM ex.work_scores
                WHERE author_url IS NOT NULL
            ) wa USING (work_id)
            GROUP BY
                u.user_id, u.n_rated, u.five_rate, u.mean_rating, u.n5,
                u.depth_ge4, u.mean_logn_5
            """
        )

    def means(table: str) -> dict[str, float | None]:
        row = con.execute(
            f"""
            SELECT
                avg(n_rated), avg(five_rate), avg(mean_rating), avg(n5),
                avg(depth_ge4), avg(mean_logn_5_re), avg(p5_blockbuster),
                avg(n_authors_5), avg(author_diversity_5)
            FROM {table}
            """
        ).fetchone()
        keys = [
            "n_rated",
            "five_rate",
            "mean_rating",
            "n5",
            "depth_ge4",
            "mean_logn_5",
            "p5_blockbuster",
            "n_authors_5",
            "author_diversity_5",
        ]
        return {k: (float(v) if v is not None else None) for k, v in zip(keys, row)}

    L, C = means("lover_ext"), means("control_ext")
    effects = {}
    for k in L:
        lv, cv = L[k], C[k]
        if lv is None or cv is None:
            effects[k] = None
            continue
        ls = con.execute(f"SELECT stddev_samp({k}) FROM lover_ext").fetchone()[0]
        cs = con.execute(f"SELECT stddev_samp({k}) FROM control_ext").fetchone()[0]
        pooled = math.sqrt(((ls or 0) ** 2 + (cs or 0) ** 2) / 2) or 1.0
        effects[k] = {
            "lover_mean": lv,
            "control_mean": cv,
            "diff": lv - cv,
            "cohen_d": (lv - cv) / pooled,
        }
    print("  cohort contrasts (Cohen's d):", flush=True)
    for k, e in sorted(effects.items(), key=lambda kv: -abs((kv[1] or {}).get("cohen_d") or 0)):
        if not e:
            continue
        print(
            f"    {k:22s} d={e['cohen_d']:+.2f}  "
            f"L={e['lover_mean']:.4g} C={e['control_mean']:.4g}",
            flush=True,
        )
    return {"lover": L, "control": C, "effects": effects, "blockbuster_n_thr": thr_n}


def rank_by_lovers(con, *, min_votes: int = 25) -> list[dict]:
    """Bayesian P(5★) among lover cohort; exclude train seeds from head optionally later."""
    m, p0 = 30.0, 0.25
    sql = f"""
        WITH agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
            FROM ex.all_rating_events e
            JOIN lover_users lu USING (user_id)
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


def heldout_metrics(rows: list[dict], con, ev: dict[str, Any]) -> dict[str, Any]:
    train_ids = {
        str(r[0])
        for r in con.execute("SELECT work_id FROM seed_ranked WHERE split='train'").fetchall()
    }
    test_ids = {
        str(r[0])
        for r in con.execute("SELECT work_id FROM seed_ranked WHERE split='test'").fetchall()
    }
    # Rank excluding train seeds (so we don't just rediscover membership)
    filtered = [r for r in rows if r["work_id"] not in train_ids]
    for i, r in enumerate(filtered, 1):
        r = dict(r)
        r["rank"] = i
        filtered[i - 1] = r

    def count(ids: set[str], limit: int) -> int:
        return sum(1 for r in filtered[:limit] if r["work_id"] in ids)

    def first_rank(ids: set[str]) -> int | None:
        for r in filtered:
            if r["work_id"] in ids:
                return r["rank"]
        return None

    test_ranks = [r["rank"] for r in filtered if r["work_id"] in test_ids]
    med = sorted(test_ranks)[len(test_ranks) // 2] if test_ranks else None
    base = evaluate(filtered, ev)
    return {
        "n_ranked_ex_train": len(filtered),
        "test_in_top50": count(test_ids, 50),
        "test_in_top100": count(test_ids, 100),
        "test_in_top200": count(test_ids, 200),
        "test_in_top500": count(test_ids, 500),
        "n_test_seeds": len(test_ids),
        "test_recall_top200": count(test_ids, 200) / max(len(test_ids), 1),
        "test_median_rank": med,
        "test_first_rank": first_rank(test_ids),
        "eval_vs_literary_poll": base,
        "top30_ex_train": [
            {
                "rank": r["rank"],
                "title": r["title"],
                "author": r["author"],
                "n": r["n_eff"],
                "is_test_seed": r["work_id"] in test_ids,
                "is_pos_poll": r["work_id"] in ev["pos_works"],
            }
            for r in filtered[:30]
        ],
    }


def emergent_likes(con, *, limit: int = 40) -> list[dict]:
    """What else do lovers 5★? (excluding all seeds)."""
    rows = con.execute(
        f"""
        WITH agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n,
                count(*) FILTER (WHERE e.rating = 5)::BIGINT AS n5
            FROM ex.all_rating_events e
            JOIN lover_users lu USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
              AND e.work_id NOT IN (SELECT work_id FROM seed_ranked)
            GROUP BY e.work_id
            HAVING count(*) >= 40
        )
        SELECT
            s.title, s.author, a.n, a.n5,
            ((a.n5 + 30*0.25) / (a.n + 30))::DOUBLE AS bayes_p5,
            wr.n AS catalog_n
        FROM agg a
        JOIN ex.work_scores s USING (work_id)
        JOIN work_rarity wr USING (work_id)
        LEFT JOIN ex.work_flags cf ON cf.work_id = s.work_id
        WHERE TRUE
        {catalog_ok_sql('s')}
        ORDER BY bayes_p5 DESC, a.n DESC
        LIMIT {limit}
        """
    ).fetchall()
    return [
        {
            "title": r[0],
            "author": r[1],
            "n_lovers": int(r[2]),
            "n5": int(r[3]),
            "bayes_p5": float(r[4]),
            "catalog_n": int(r[5]),
        }
        for r in rows
    ]


def hit_threshold_sweep(con, ev: dict[str, Any]) -> list[dict]:
    """How sensitive is held-out recovery to min seed hits?"""
    out = []
    for hits in (2, 3, 4, 5, 8):
        print(f"\n--- sweep min_hits={hits} ---", flush=True)
        define_lovers(con, seed_split="train", min_hits=hits)
        n = con.execute("SELECT count(*) FROM lover_users").fetchone()[0]
        if n < 50:
            out.append({"min_hits": hits, "n_lovers": n, "skipped": True})
            continue
        rows = rank_by_lovers(con, min_votes=20)
        held = heldout_metrics(rows, con, ev)
        out.append(
            {
                "min_hits": hits,
                "n_lovers": n,
                "test_in_top50": held["test_in_top50"],
                "test_in_top200": held["test_in_top200"],
                "test_recall_top200": held["test_recall_top200"],
                "test_median_rank": held["test_median_rank"],
                "pos50": held["eval_vs_literary_poll"]["pos50"],
                "anti50": held["eval_vs_literary_poll"]["anti50"],
                "Q": held["eval_vs_literary_poll"]["Q"],
            }
        )
        print(
            f"  n={n} test@50={held['test_in_top50']} test@200={held['test_in_top200']} "
            f"med_rank={held['test_median_rank']} Q={held['eval_vs_literary_poll']['Q']:.1f}",
            flush=True,
        )
    return out


def proxy_from_features(con, ev: dict[str, Any], effects: dict[str, Any]) -> dict[str, Any]:
    """Ratings-only proxy: users matching lover signature WITHOUT seed hits.

    Uses the strongest separating features from the contrast (not seed counts).
    """
    # Typical signature from literary lovers historically: lower five_rate,
    # lower p5_blockbuster, moderate depth — take top contrasts by |d|
    ranked_feats = sorted(
        (
            (k, abs(v["cohen_d"]), v)
            for k, v in effects.items()
            if v and k not in ("n_rated", "n5")  # matched / size-like
        ),
        key=lambda t: -t[1],
    )
    top = ranked_feats[:4]
    print("  proxy features:", [(k, f"{v['cohen_d']:+.2f}") for k, _, v in top], flush=True)

    # Build a simple score: sum of z-scored features in the lover direction
    # Implement via SQL thresholds at lover-favoring quartiles
    # Direction: if lover_mean > control_mean, take high values; else low
    clauses = []
    for k, _ad, v in top:
        if k in ("p5_blockbuster", "author_diversity_5", "mean_logn_5", "mean_logn_5_re"):
            # may need lover_ext columns — compute on user_feat + join for proxy pool
            pass
    # Practical proxy using user_feat only + blockbuster resist table
    thr_n = effects.get("_thr")  # unused
    bb_thr = float(
        con.execute(
            "SELECT approx_quantile(n, 0.995::FLOAT) FROM work_rarity"
        ).fetchone()[0]
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_proxy_feat AS
        SELECT
            uf.user_id,
            uf.n_rated,
            uf.five_rate,
            uf.mean_rating,
            uf.depth_ge4,
            uf.mean_logn_5,
            (
                count(*) FILTER (WHERE wr.n >= {bb_thr} AND e.rating = 5)::DOUBLE
                / nullif(count(*) FILTER (WHERE wr.n >= {bb_thr}), 0)
            ) AS p5_blockbuster
        FROM user_feat uf
        JOIN ex.all_rating_events e USING (user_id)
        JOIN work_rarity wr USING (work_id)
        WHERE uf.n_rated >= 50
          AND uf.n_ge4_midpop >= 5
        GROUP BY uf.user_id, uf.n_rated, uf.five_rate, uf.mean_rating,
                 uf.depth_ge4, uf.mean_logn_5
        HAVING count(*) FILTER (WHERE wr.n >= {bb_thr}) >= 5
        """
    )
    # Align with lover means: typically lower five_rate, lower p5_bb, lower mean_logn?
    # Use quintiles in the lover direction from measured effects
    dirs = {}
    for k, e in effects.items():
        if not e:
            continue
        dirs[k] = 1 if e["diff"] > 0 else -1

    # Score = -z(five_rate)*I + -z(p5_bb) + ...
    fr_mu, fr_sd = con.execute(
        "SELECT avg(five_rate), stddev_samp(five_rate) FROM user_proxy_feat"
    ).fetchone()
    bb_mu, bb_sd = con.execute(
        "SELECT avg(p5_blockbuster), stddev_samp(p5_blockbuster) FROM user_proxy_feat"
    ).fetchone()
    ml_mu, ml_sd = con.execute(
        "SELECT avg(mean_logn_5), stddev_samp(mean_logn_5) FROM user_proxy_feat"
    ).fetchone()
    fr_sd = fr_sd or 1.0
    bb_sd = bb_sd or 1.0
    ml_sd = ml_sd or 1.0
    # lover direction from effects
    s_fr = -1 if dirs.get("five_rate", -1) < 0 else 1
    s_bb = -1 if dirs.get("p5_blockbuster", -1) < 0 else 1
    s_ml = -1 if dirs.get("mean_logn_5", -1) < 0 else 1

    con.execute(
        f"""
        CREATE OR REPLACE TABLE proxy_users AS
        SELECT user_id,
            (
                {s_fr} * (five_rate - {fr_mu}) / {fr_sd}
              + {s_bb} * (p5_blockbuster - {bb_mu}) / {bb_sd}
              + {s_ml} * (mean_logn_5 - {ml_mu}) / {ml_sd}
            )::DOUBLE AS proxy_score
        FROM user_proxy_feat
        WHERE five_rate IS NOT NULL AND p5_blockbuster IS NOT NULL
          AND mean_logn_5 IS NOT NULL
        """
    )
    thr = con.execute(
        "SELECT approx_quantile(proxy_score, 0.95::FLOAT) FROM proxy_users"
    ).fetchone()[0]
    con.execute(
        f"""
        CREATE OR REPLACE TABLE lover_users AS
        SELECT
            p.user_id,
            0::BIGINT AS seed_hits_5,
            0::BIGINT AS seed_ratings,
            uf.n_rated,
            uf.five_rate,
            uf.mean_rating,
            uf.n5,
            uf.depth_ge4,
            uf.n_ge4_midpop,
            uf.n_ge4_popular,
            uf.mean_logn_5
        FROM proxy_users p
        JOIN user_feat uf USING (user_id)
        WHERE p.proxy_score >= {float(thr)}
        """
    )
    n = con.execute("SELECT count(*) FROM lover_users").fetchone()[0]
    print(f"  proxy lovers (top 5% signature)={n:,}", flush=True)
    rows = rank_by_lovers(con, min_votes=25)
    # For proxy, evaluate against ALL seeds as held-out (no train membership)
    all_seed = {
        str(r[0]) for r in con.execute("SELECT work_id FROM seed_ranked").fetchall()
    }
    filtered = list(rows)
    seed_hits = {
        "seed_in_top50": sum(1 for r in filtered[:50] if r["work_id"] in all_seed),
        "seed_in_top200": sum(1 for r in filtered[:200] if r["work_id"] in all_seed),
        "seed_in_top500": sum(1 for r in filtered[:500] if r["work_id"] in all_seed),
        "n_seeds": len(all_seed),
    }
    base = evaluate(filtered, ev)
    return {
        "n_proxy_lovers": n,
        "proxy_directions": {
            "five_rate": s_fr,
            "p5_blockbuster": s_bb,
            "mean_logn_5": s_ml,
        },
        "seed_recovery": seed_hits,
        "eval": base,
        "top20": [
            {"rank": r["rank"], "title": r["title"], "author": r["author"], "n": r["n_eff"]}
            for r in filtered[:20]
        ],
    }


def main() -> None:
    t_all = time.time()
    con = _con()
    ev = load_eval_sets(con)
    print(
        f"Eval: pos={ev['n_pos_works']} anti={ev['n_anti_works']}",
        flush=True,
    )
    materialize_base(con)
    seed_meta = materialize_seeds(con)

    results: dict[str, Any] = {
        "meta": {
            "purpose": "reverse-engineer classic-lover cohort (seed-informed; bias acknowledged)",
            "min_seed_n": MIN_SEED_N,
            "seeds": seed_meta,
        },
        "sweep": [],
    }

    # Primary: train lovers hits≥3
    print("\n=== primary train lovers (hits≥3) ===", flush=True)
    lover_meta = define_lovers(con, seed_split="train", min_hits=3)
    ctrl_meta = matched_controls(con)
    contrasts = compare_cohorts(con)
    rows = rank_by_lovers(con)
    held = heldout_metrics(rows, con, ev)
    emergent = emergent_likes(con, limit=25)
    results["primary"] = {
        "lovers": lover_meta,
        "controls": ctrl_meta,
        "contrasts": contrasts,
        "heldout": held,
        "emergent_likes": emergent,
    }
    print(
        f"  held-out test seeds @50={held['test_in_top50']} @200={held['test_in_top200']} "
        f"recall200={held['test_recall_top200']:.2%} med_rank={held['test_median_rank']}",
        flush=True,
    )
    print("  emergent (non-seed) head:", flush=True)
    for i, r in enumerate(emergent[:8], 1):
        print(f"    {i}. {r['title'][:48]} — {r['author'][:24]}", flush=True)

    results["sweep"] = hit_threshold_sweep(con, ev)

    print("\n=== ratings-only proxy from lover signature ===", flush=True)
    # Restore train lovers contrasts already computed; proxy uses those effects
    results["proxy"] = proxy_from_features(con, ev, contrasts["effects"])
    print(
        f"  proxy seed@50={results['proxy']['seed_recovery']['seed_in_top50']} "
        f"@200={results['proxy']['seed_recovery']['seed_in_top200']} "
        f"Q={results['proxy']['eval']['Q']:.1f}",
        flush=True,
    )

    # Also: all-seed lovers (max insight cluster), for emergent only
    print("\n=== all-seed lovers emergent (hits≥4) ===", flush=True)
    define_lovers(con, seed_split="all", min_hits=4)
    results["all_seed_emergent"] = emergent_likes(con, limit=20)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    _write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    con.close()


def _write_report(results: dict[str, Any]) -> None:
    p = results.get("primary") or {}
    held = p.get("heldout") or {}
    contrasts = (p.get("contrasts") or {}).get("effects") or {}
    lines = [
        "# Reverse-engineering classic lovers",
        "",
        "Seed-informed analysis (confirmation bias risk is real and acknowledged).",
        f"Seeds = `poll_works` with **n ≥ {MIN_SEED_N}**, split odd/even `poll_rank` "
        "into train/test. Lovers = users with ≥k distinct **5★ train seeds**.",
        "",
        "## Seeds",
        "",
    ]
    for s in (results.get("meta") or {}).get("seeds", {}).get("top12") or []:
        lines.append(
            f"- #{s['rank']} [{s['split']}] {s['title']} — {s['author']} (n={s['n']})"
        )
    lines += ["", "## Cohort contrast (train lovers vs n_rated-matched controls)", ""]
    lines.append("| feature | lover | control | Δ | Cohen d |")
    lines.append("|---|---:|---:|---:|---:|")
    for k, e in sorted(
        contrasts.items(),
        key=lambda kv: -abs((kv[1] or {}).get("cohen_d") or 0),
    ):
        if not e:
            continue
        lines.append(
            f"| {k} | {e['lover_mean']:.4g} | {e['control_mean']:.4g} | "
            f"{e['diff']:+.4g} | {e['cohen_d']:+.2f} |"
        )
    lines += [
        "",
        "## Held-out recovery (train lovers → rank books, drop train seeds)",
        "",
        f"- test seeds in top 50 / 100 / 200 / 500: "
        f"**{held.get('test_in_top50')}** / {held.get('test_in_top100')} / "
        f"**{held.get('test_in_top200')}** / {held.get('test_in_top500')} "
        f"(of {held.get('n_test_seeds')})",
        f"- test recall@200: {held.get('test_recall_top200')}",
        f"- test median rank: {held.get('test_median_rank')}",
        f"- vs literary_poll works: pos50={held.get('eval_vs_literary_poll', {}).get('pos50')} "
        f"anti50={held.get('eval_vs_literary_poll', {}).get('anti50')} "
        f"Q={held.get('eval_vs_literary_poll', {}).get('Q')}",
        "",
        "### Top 30 excluding train seeds",
        "",
    ]
    for r in held.get("top30_ex_train") or []:
        flags = []
        if r.get("is_test_seed"):
            flags.append("TEST-SEED")
        if r.get("is_pos_poll"):
            flags.append("poll-work")
        tag = f" [{', '.join(flags)}]" if flags else ""
        lines.append(
            f"- {r['rank']}. {r['title']} — {r['author']} (n≈{r['n']:.0f}){tag}"
        )
    lines += ["", "## Emergent non-seed likes (train lovers)", ""]
    for i, r in enumerate(p.get("emergent_likes") or [], 1):
        lines.append(
            f"- {i}. {r['title']} — {r['author']} "
            f"(bayes_p5={r['bayes_p5']:.3f}, lovers_n={r['n_lovers']}, catalog_n={r['catalog_n']})"
        )
    lines += ["", "## Hit-threshold sweep", "", "| k | n_lovers | test@50 | test@200 | recall@200 | med_rank | Q |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in results.get("sweep") or []:
        if row.get("skipped"):
            lines.append(f"| {row['min_hits']} | {row['n_lovers']} | skipped | | | | |")
            continue
        lines.append(
            f"| {row['min_hits']} | {row['n_lovers']} | {row['test_in_top50']} | "
            f"{row['test_in_top200']} | {row['test_recall_top200']:.2%} | "
            f"{row['test_median_rank']} | {row['Q']:.1f} |"
        )
    prox = results.get("proxy") or {}
    lines += [
        "",
        "## Ratings-only proxy (no seed hits in membership)",
        "",
        "Top 5% users by z-scored signature copied from lover−control directions "
        f"(`five_rate`, `p5_blockbuster`, `mean_logn_5`). n={prox.get('n_proxy_lovers')}.",
        f"- all seeds in top 50/200/500: {prox.get('seed_recovery', {}).get('seed_in_top50')} / "
        f"{prox.get('seed_recovery', {}).get('seed_in_top200')} / "
        f"{prox.get('seed_recovery', {}).get('seed_in_top500')}",
        f"- literary_poll pos50/anti50/Q: {prox.get('eval', {}).get('pos50')} / "
        f"{prox.get('eval', {}).get('anti50')} / {prox.get('eval', {}).get('Q')}",
        "",
        "Proxy top 12:",
        "",
    ]
    for r in (prox.get("top20") or [])[:12]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    lines += [
        "",
        "## Takeaways",
        "",
        "See JSON for full detail. Core questions this run answers:",
        "1. What ratings-only traits separate classic-lovers from matched controls?",
        "2. Do train-seed lovers recover held-out test classics?",
        "3. Does a seed-free proxy built from those traits still surface classics?",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

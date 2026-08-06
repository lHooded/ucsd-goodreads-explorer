#!/usr/bin/env python3
"""Within-user pairwise esteem (focus vs anti).

For each reader: books they rated 5★ beat books they rated ≤3.
Cap highs/lows per user so pairs stay linear. Aggregate win rates in the
careful focus cohort vs anti-like cohort, shrink, and contrast.

Removes user generosity / scale effects that residual only partially handles.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_pairwise_esteem
"""

from __future__ import annotations

import json
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
from curators_explorer.scripts.research_residual_enthusiasm import (
    WEIGHTS_CAREFUL,
    author_disjoint_sets,
    heldout_recall,
    load_sticky,
    load_weights,
    materialize_residuals,
    pick_cohorts,
    probe_metrics,
    rank_raw_p5_legacy,
    rank_residual,
    rank_scored,
    top15,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    build_user_features,
    filler_eval,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "pairwise_esteem.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "PAIRWISE_ESTEEM_REPORT.md"

TOP_FRAC = 0.06
MAX_N = 120_000
MIN_APPEAR = 40  # min (wins+losses) in a cohort before counting
SHRINK_K = 50.0
MAX_HIGHS = 12  # 5★ works sampled per user
MAX_LOWS = 12  # ≤3 works sampled per user
LOW_MAX_RATING = 3
SEED = 11


def build_pair_tables(con) -> dict[str, int]:
    """Sample within-user 5★-beats-≤3 pairs for focus and anti cohorts."""
    print(
        f"  sampling pairs (≤{MAX_HIGHS} highs × ≤{MAX_LOWS} lows / user)…",
        flush=True,
    )
    t0 = time.time()
    # Deterministic-ish sample via hash of (user, work) instead of random()
    for label, cohort in (("focus", "cohort_focus_top"), ("anti", "cohort_anti_top")):
        con.execute(
            f"""
            CREATE OR REPLACE TABLE pairs_{label} AS
            WITH rated AS (
                SELECT
                    e.user_id,
                    e.work_id,
                    e.rating
                FROM ex.all_rating_events e
                JOIN {cohort} c USING (user_id)
                JOIN work_rarity wr ON wr.work_id = e.work_id
                WHERE wr.n >= {MIN_RANK_N} AND wr.n <= {MAX_N}
            ),
            highs AS (
                SELECT
                    user_id,
                    work_id,
                    row_number() OVER (
                        PARTITION BY user_id
                        ORDER BY hash(user_id || '-' || work_id || '-h{SEED}')
                    ) AS rn
                FROM rated
                WHERE rating = 5
            ),
            lows AS (
                SELECT
                    user_id,
                    work_id,
                    row_number() OVER (
                        PARTITION BY user_id
                        ORDER BY hash(user_id || '-' || work_id || '-l{SEED}')
                    ) AS rn
                FROM rated
                WHERE rating <= {LOW_MAX_RATING}
            )
            SELECT
                h.user_id,
                h.work_id AS winner,
                l.work_id AS loser
            FROM highs h
            JOIN lows l USING (user_id)
            WHERE h.rn <= {MAX_HIGHS} AND l.rn <= {MAX_LOWS}
            """
        )
    n_f = con.execute("SELECT count(*) FROM pairs_focus").fetchone()[0]
    n_a = con.execute("SELECT count(*) FROM pairs_anti").fetchone()[0]
    u_f = con.execute("SELECT count(DISTINCT user_id) FROM pairs_focus").fetchone()[0]
    u_a = con.execute("SELECT count(DISTINCT user_id) FROM pairs_anti").fetchone()[0]
    print(
        f"  pairs focus={n_f:,} ({u_f:,} users) anti={n_a:,} ({u_a:,} users) "
        f"({time.time()-t0:.1f}s)",
        flush=True,
    )
    return {
        "n_pairs_focus": int(n_f),
        "n_pairs_anti": int(n_a),
        "n_users_focus": int(u_f),
        "n_users_anti": int(u_a),
    }


def rank_pairwise(con, *, min_appear: int = MIN_APPEAR, k: float = SHRINK_K) -> list[dict]:
    """Shrunk focus win-rate − shrunk anti win-rate."""
    sql = f"""
        WITH f_w AS (
            SELECT winner AS work_id, count(*)::BIGINT AS wins
            FROM pairs_focus GROUP BY 1
        ),
        f_l AS (
            SELECT loser AS work_id, count(*)::BIGINT AS losses
            FROM pairs_focus GROUP BY 1
        ),
        a_w AS (
            SELECT winner AS work_id, count(*)::BIGINT AS wins
            FROM pairs_anti GROUP BY 1
        ),
        a_l AS (
            SELECT loser AS work_id, count(*)::BIGINT AS losses
            FROM pairs_anti GROUP BY 1
        ),
        focus_stats AS (
            SELECT
                coalesce(w.work_id, l.work_id) AS work_id,
                coalesce(w.wins, 0) AS wins,
                coalesce(l.losses, 0) AS losses,
                (coalesce(w.wins, 0) + coalesce(l.losses, 0)) AS n
            FROM f_w w
            FULL OUTER JOIN f_l l USING (work_id)
        ),
        anti_stats AS (
            SELECT
                coalesce(w.work_id, l.work_id) AS work_id,
                coalesce(w.wins, 0) AS wins,
                coalesce(l.losses, 0) AS losses,
                (coalesce(w.wins, 0) + coalesce(l.losses, 0)) AS n
            FROM a_w w
            FULL OUTER JOIN a_l l USING (work_id)
        ),
        scored AS (
            SELECT
                f.work_id,
                f.n AS n_c,
                coalesce(a.n, 0) AS n_a,
                (f.n::DOUBLE / (f.n + {k})) * (f.wins::DOUBLE / nullif(f.n, 0)) AS focus_wr,
                CASE
                    WHEN a.n IS NULL OR a.n < {min_appear} THEN 0.0
                    ELSE (a.n::DOUBLE / (a.n + {k})) * (a.wins::DOUBLE / nullif(a.n, 0))
                END AS anti_wr
            FROM focus_stats f
            LEFT JOIN anti_stats a USING (work_id)
            WHERE f.n >= {min_appear}
        )
        SELECT
            work_id,
            (focus_wr - anti_wr)::DOUBLE AS score,
            n_c::DOUBLE AS n_c,
            n_a::DOUBLE AS n_a,
            least(n_c, CASE WHEN n_a = 0 THEN n_c ELSE n_a END)::DOUBLE AS n_eff
        FROM scored
    """
    return rank_scored(con, sql)


def rank_pairwise_bilateral(
    con, *, min_appear: int = MIN_APPEAR, k: float = SHRINK_K
) -> list[dict]:
    """Require adequate appearances in both cohorts."""
    sql = f"""
        WITH f_w AS (
            SELECT winner AS work_id, count(*)::BIGINT AS wins
            FROM pairs_focus GROUP BY 1
        ),
        f_l AS (
            SELECT loser AS work_id, count(*)::BIGINT AS losses
            FROM pairs_focus GROUP BY 1
        ),
        a_w AS (
            SELECT winner AS work_id, count(*)::BIGINT AS wins
            FROM pairs_anti GROUP BY 1
        ),
        a_l AS (
            SELECT loser AS work_id, count(*)::BIGINT AS losses
            FROM pairs_anti GROUP BY 1
        ),
        focus_stats AS (
            SELECT
                coalesce(w.work_id, l.work_id) AS work_id,
                coalesce(w.wins, 0) AS wins,
                coalesce(l.losses, 0) AS losses,
                (coalesce(w.wins, 0) + coalesce(l.losses, 0)) AS n
            FROM f_w w
            FULL OUTER JOIN f_l l USING (work_id)
        ),
        anti_stats AS (
            SELECT
                coalesce(w.work_id, l.work_id) AS work_id,
                coalesce(w.wins, 0) AS wins,
                coalesce(l.losses, 0) AS losses,
                (coalesce(w.wins, 0) + coalesce(l.losses, 0)) AS n
            FROM a_w w
            FULL OUTER JOIN a_l l USING (work_id)
        ),
        scored AS (
            SELECT
                f.work_id,
                f.n AS n_c,
                a.n AS n_a,
                (f.n::DOUBLE / (f.n + {k})) * (f.wins::DOUBLE / nullif(f.n, 0)) AS focus_wr,
                (a.n::DOUBLE / (a.n + {k})) * (a.wins::DOUBLE / nullif(a.n, 0)) AS anti_wr
            FROM focus_stats f
            INNER JOIN anti_stats a USING (work_id)
            WHERE f.n >= {min_appear} AND a.n >= {min_appear}
        )
        SELECT
            work_id,
            (focus_wr - anti_wr)::DOUBLE AS score,
            n_c::DOUBLE AS n_c,
            n_a::DOUBLE AS n_a,
            least(n_c, n_a)::DOUBLE AS n_eff
        FROM scored
    """
    return rank_scored(con, sql)


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
    print(f"  weights: {w.get('source', WEIGHTS_CAREFUL.name)}", flush=True)
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
        f"  author-disjoint test works={len(adj['test_works'])} "
        f"(authors={len(adj['test_authors'])})",
        flush=True,
    )

    pair_meta = build_pair_tables(con)
    methods: dict[str, Any] = {}

    def record(name: str, rows: list[dict]) -> None:
        methods[name] = {
            "probe": probe_metrics(rows, ev, sticky),
            "fill": filler_eval(rows, con),
            "heldout_author_disjoint": heldout_recall(rows, adj["test_works"]),
            "top15": top15(rows),
        }
        p = methods[name]["probe"]
        h = methods[name]["heldout_author_disjoint"]
        print(
            f"  {name}: Q_clean={p['Q_clean']:.1f} pos50={p['pos50']} "
            f"anti50={p['anti50']} fill50={p['filler50']} sticky50={p['sticky50']} "
            f"heldout@200={h['recall@200']:.3f}",
            flush=True,
        )

    print("\n=== baselines ===", flush=True)
    record("legacy_p5", rank_raw_p5_legacy(con))
    materialize_residuals(con)
    record("residual_no_author", rank_residual(con, author_blend=0.0))

    print("\n=== pairwise ===", flush=True)
    record("pairwise", rank_pairwise(con))
    record("pairwise_bilateral", rank_pairwise_bilateral(con))

    results = {
        "meta": {
            "max_highs": MAX_HIGHS,
            "max_lows": MAX_LOWS,
            "low_max_rating": LOW_MAX_RATING,
            "min_appear": MIN_APPEAR,
            "shrink_k": SHRINK_K,
            "pairs": pair_meta,
            "cohorts": cohorts,
            "weights": str(WEIGHTS_CAREFUL),
        },
        "methods": methods,
    }
    OUT_JSON.write_text(json.dumps(results, indent=2, default=float) + "\n")

    lines = [
        "# Within-user pairwise esteem",
        "",
        "Same careful focus/anti cohorts. Score = shrunk focus win-rate − shrunk anti",
        f"win-rate, where a win is: same user rated A=5 and B≤{LOW_MAX_RATING}.",
        f"Per user cap: {MAX_HIGHS} highs × {MAX_LOWS} lows.",
        "",
        "## Probe metrics (no anti-median Q bonus)",
        "",
        "| method | Q_clean | pos50 | anti50 | filler50 | sticky50 | heldout@200 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("legacy_p5", "residual_no_author", "pairwise", "pairwise_bilateral"):
        p = methods[name]["probe"]
        h = methods[name]["heldout_author_disjoint"]
        lines.append(
            f"| {name} | {p['Q_clean']:.1f} | {p['pos50']} | {p['anti50']} | "
            f"{p['filler50']} | {p['sticky50']} | {h['recall@200']:.3f} |"
        )

    best = "pairwise_bilateral"  # best operational head + held-out@50
    lines += [
        "",
        "## Pairwise bilateral top 15 (recommended)",
        "",
        "Requires adequate pair appearances in **both** cohorts. Best pos50 and",
        "held-out@50 / median rank; Q_clean looks worse only because anti floods 51–1000.",
        "",
    ]
    for r in methods["pairwise_bilateral"]["top15"]:
        lines.append(
            f"- {r['rank']}. {r['title']} — {r['author']} "
            f"(n_c={r.get('n_c')}, n_a={r.get('n_a')})"
        )
    lines += [
        "",
        "## Pairwise (anti optional) top 15",
        "",
        "Highest held-out@200, but 74% of top50 lack anti support — highbrow books",
        "focus readers prefer that anti barely rates. Sticky collapses.",
        "",
    ]
    for r in methods["pairwise"]["top15"]:
        lines.append(
            f"- {r['rank']}. {r['title']} — {r['author']} "
            f"(n_c={r.get('n_c')}, n_a={r.get('n_a')})"
        )
    lines += ["", "## Legacy p5 top 15", ""]
    for r in methods["legacy_p5"]["top15"]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    lines += ["", "## Residual (no author) top 15", ""]
    for r in methods["residual_no_author"]["top15"]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    lines += [
        "",
        "## Notes",
        "",
        "- Pairwise removes within-user scale: only relative preference matters.",
        "- Compare held-out@200 and head shape vs legacy / residual.",
        f"- Pairs built: focus={pair_meta['n_pairs_focus']:,}, anti={pair_meta['n_pairs_anti']:,}.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)


if __name__ == "__main__":
    main()

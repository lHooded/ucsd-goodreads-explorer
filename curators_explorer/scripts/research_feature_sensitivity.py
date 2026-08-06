#!/usr/bin/env python3
"""Feature impact + rank-trajectory analysis for the unseeded contrastive scorer.

- Ablate each feature (zero its weight everywhere) and measure ranking shift.
- Sweep knobs (λ_anti, top_frac, series gate) and record book rank trajectories.
- Report probe metrics as *noisy* signals only — piles are fallible.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_feature_sensitivity
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    evaluate,
    load_eval_sets,
    materialize_base,
    rank_from_sql,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    FEATURE_COLS,
    build_user_features,
    filler_eval,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
    threeway_contrast,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "feature_sensitivity.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "FEATURE_SENSITIVITY_REPORT.md"

# Baseline coefficients (same as threeway scorer)
CLASSIC_TERMS = {
    "mean_pub_year_5": -1.4,
    "series_share_5": -1.5,
    "mega_catalog_share_5": -1.3,
    "mean_logn_5": -1.0,
    "depth_ge4": 0.9,
    "midpop_span_per_logn5": 1.2,
    "author_hhi_5": -0.8,
    "mid_catalog_share_5": 0.5,
    "std_logn_5": 0.4,
    "singleton_author_share_5": 0.6,
    "binge_mean_5": -0.7,
    "author_div_5": 0.5,
}
ANTI_TERMS = {
    "series_share_5": 1.6,
    "binge_mean_5": 1.2,
    "binge_max_5": 0.8,
    "author_hhi_5": 1.0,
    "mean_pub_year_5": 1.0,
    "singleton_author_share_5": -0.8,
    "author_div_5": -0.6,
}
NORMIE_TERMS = {
    "mega_catalog_share_5": 1.5,
    "mean_logn_5": 1.3,
    "p5_blockbuster": 0.8,
    "n_megastar_authors_5": 0.6,
    "midpop_span_per_logn5": -0.7,
    "depth_ge4": -0.5,
}

WATCH_TITLES = [
    "Dhalgren",
    "Moby-Dick",
    "Ulysses",
    "Lolita",
    "The Brothers Karamazov",
    "1984",
    "The Catcher in the Rye",
    "The Hate U Give",
    "Words of Radiance",
    "A Court of Mist and Fury",
    "Infinite Jest",
    "Blood Meridian",
    "Gravity's Rainbow",
    "Stoner",
    "The Book of Disquiet",
]


def _moments(con) -> dict[str, dict[str, float]]:
    out = {}
    for c in FEATURE_COLS:
        mu, sd = con.execute(
            f"SELECT avg({c}), stddev_samp({c}) FROM user_rich WHERE {c} IS NOT NULL"
        ).fetchone()
        out[c] = {"mu": float(mu or 0), "sd": float(sd or 1) or 1.0}
    return out


def _zexpr(col: str, moments: dict[str, dict[str, float]]) -> str:
    mu, sd = moments[col]["mu"], moments[col]["sd"]
    return f"((coalesce({col}, {mu}) - ({mu})) / ({sd}))"


def _sum_expr(terms: dict[str, float], moments: dict[str, dict[str, float]]) -> str:
    parts = [
        f"({w}) * {_zexpr(c, moments)}" for c, w in terms.items() if c in moments and w != 0
    ]
    return " + ".join(parts) if parts else "0"


def build_affinity(
    con,
    moments: dict[str, dict[str, float]],
    *,
    classic_terms: dict[str, float],
    anti_terms: dict[str, float],
    normie_terms: dict[str, float],
    lam_a: float = 0.85,
    lam_n: float = 0.75,
    series_gate: float = 0.40,
    mega_gate: float = 0.28,
    binge_gate: float = 2.8,
    span_gate: float = 3.0,
) -> dict[str, Any]:
    classic_raw = _sum_expr(classic_terms, moments)
    anti_raw = _sum_expr(anti_terms, moments)
    normie_raw = _sum_expr(normie_terms, moments)
    focus = f"({classic_raw}) - ({lam_a}) * ({anti_raw}) - ({lam_n}) * ({normie_raw})"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_affinity AS
        SELECT
            user_id,
            ({classic_raw})::DOUBLE AS classic_raw,
            ({anti_raw})::DOUBLE AS anti_raw,
            ({normie_raw})::DOUBLE AS normie_raw,
            ({focus})::DOUBLE AS classic_affinity,
            series_share_5,
            binge_mean_5,
            midpop_span_per_logn5,
            mega_catalog_share_5
        FROM user_rich
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE user_affinity_gated AS
        SELECT *
        FROM user_affinity
        WHERE series_share_5 <= {series_gate}
          AND mega_catalog_share_5 <= {mega_gate}
          AND binge_mean_5 <= {binge_gate}
          AND midpop_span_per_logn5 >= {span_gate}
        """
    )
    n_g = con.execute("SELECT count(*) FROM user_affinity_gated").fetchone()[0]
    return {"n_gated": n_g, "lam_a": lam_a, "lam_n": lam_n, "series_gate": series_gate}


def contrastive_rank(
    con,
    *,
    top_frac: float = 0.06,
    min_votes: int = 30,
    anti_series_floor: float = 0.45,
) -> list[dict]:
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
            WHERE series_share_5 >= {anti_series_floor} OR binge_mean_5 >= 2.5
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
          AND (series_share_5 >= {anti_series_floor} OR binge_mean_5 >= 2.5)
        """
    )
    sql = f"""
        WITH c_agg AS (
            SELECT
                e.work_id,
                count(*)::BIGINT AS n_c,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5_c
            FROM ex.all_rating_events e
            JOIN cohort_focus_top t USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= 120000
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
            WHERE wr.n >= {MIN_RANK_N} AND wr.n <= 120000
            GROUP BY e.work_id
            HAVING count(*) >= {min_votes}
        )
        SELECT
            c.work_id,
            (c.p5_c - coalesce(a.p5_a, c.p5_c * 0.85))::DOUBLE AS score,
            least(c.n_c, coalesce(a.n_a, c.n_c))::DOUBLE AS n_eff
        FROM c_agg c
        LEFT JOIN a_agg a USING (work_id)
        WHERE c.n_c >= {min_votes}
    """
    return rank_from_sql(con, sql)


def rank_maps(rows: list[dict]) -> dict[str, int]:
    return {r["work_id"]: r["rank"] for r in rows}


def top_ids(rows: list[dict], k: int = 50) -> set[str]:
    return {r["work_id"] for r in rows[:k]}


def kendall_top(a: dict[str, int], b: dict[str, int], universe: set[str]) -> float:
    """Kendall-tau-like agreement on pairwise order within universe ∩ both maps."""
    ids = [i for i in universe if i in a and i in b]
    if len(ids) < 3:
        return float("nan")
    conc = disc = 0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            x, y = ids[i], ids[j]
            sa = a[x] - a[y]
            sb = b[x] - b[y]
            if sa == 0 or sb == 0:
                continue
            if sa * sb > 0:
                conc += 1
            else:
                disc += 1
    tot = conc + disc
    return (conc - disc) / tot if tot else float("nan")


def resolve_watchlist(con) -> list[dict[str, Any]]:
    out = []
    for title in WATCH_TITLES:
        rows = con.execute(
            """
            SELECT work_id, title, author, n
            FROM ex.work_scores
            WHERE lower(title) = lower(?)
               OR lower(title) LIKE lower(?) || ' (%'
               OR lower(title) LIKE lower(?) || ' or,%'
               OR lower(title) LIKE lower(?) || ':%'
            ORDER BY n DESC
            LIMIT 1
            """,
            [title, title, title, title],
        ).fetchall()
        if rows:
            wid, t, a, n = rows[0]
            out.append(
                {
                    "query": title,
                    "work_id": str(wid),
                    "title": t,
                    "author": a,
                    "n": int(n or 0),
                }
            )
    return out


def summarize_ranking(rows: list[dict], ev, con, watch: list[dict]) -> dict[str, Any]:
    base = evaluate(rows, ev)
    extra = filler_eval(rows, con)
    ranks = rank_maps(rows)
    watch_ranks = []
    for w in watch:
        watch_ranks.append(
            {
                "query": w["query"],
                "title": w["title"],
                "author": w["author"],
                "work_id": w["work_id"],
                "rank": ranks.get(w["work_id"]),
            }
        )
    return {
        "Q": base["Q"],
        "pos50": base["pos50"],
        "anti50": base["anti50"],
        "filler50": base["filler50"],
        "classic50": extra["classic50"],
        "normie50": extra["normie50"],
        "test50": extra["test50"],
        "test200": extra["test200"],
        "top15": [
            {"rank": r["rank"], "title": r["title"], "author": r["author"]}
            for r in rows[:15]
        ],
        "watch": watch_ranks,
    }


def zero_feature(
    classic: dict[str, float],
    anti: dict[str, float],
    normie: dict[str, float],
    feat: str,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    c, a, n = dict(classic), dict(anti), dict(normie)
    if feat in c:
        c[feat] = 0.0
    if feat in a:
        a[feat] = 0.0
    if feat in n:
        n[feat] = 0.0
    return c, a, n


def all_features_used() -> list[str]:
    keys = set(CLASSIC_TERMS) | set(ANTI_TERMS) | set(NORMIE_TERMS)
    return sorted(keys)


def main() -> None:
    t_all = time.time()
    con = _con()
    ev = load_eval_sets(con)
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    label_cohorts(con)
    threeway_contrast(con)  # prints gold separators; not required for scoring
    moments = _moments(con)
    watch = resolve_watchlist(con)
    print(f"Watchlist resolved: {len(watch)}/{len(WATCH_TITLES)}", flush=True)

    results: dict[str, Any] = {
        "meta": {
            "note": "Probe metrics are noisy; piles are fallible. Prefer stability + trajectory structure.",
            "watchlist": watch,
        },
        "baseline": {},
        "ablations": {},
        "trajectories": {},
        "suggestions": [],
    }

    # --- Baseline ---
    print("\n=== baseline ===", flush=True)
    build_affinity(con, moments, classic_terms=CLASSIC_TERMS, anti_terms=ANTI_TERMS, normie_terms=NORMIE_TERMS)
    base_rows = contrastive_rank(con)
    base_sum = summarize_ranking(base_rows, ev, con, watch)
    base_map = rank_maps(base_rows)
    base_top200 = top_ids(base_rows, 200)
    results["baseline"] = base_sum
    print(
        f"  Q={base_sum['Q']:.1f} pos50={base_sum['pos50']} anti50={base_sum['anti50']} "
        f"classic50={base_sum['classic50']}",
        flush=True,
    )
    for w in base_sum["watch"]:
        if w["rank"] is not None:
            print(f"    {w['query']}: rank {w['rank']}", flush=True)

    # --- Ablations ---
    print("\n=== feature ablations ===", flush=True)
    for feat in all_features_used():
        c, a, n = zero_feature(CLASSIC_TERMS, ANTI_TERMS, NORMIE_TERMS, feat)
        # skip if feature unused after zero (always still run)
        build_affinity(con, moments, classic_terms=c, anti_terms=a, normie_terms=n)
        rows = contrastive_rank(con)
        summ = summarize_ranking(rows, ev, con, watch)
        m = rank_maps(rows)
        j50 = len(top_ids(rows, 50) & top_ids(base_rows, 50)) / 50.0
        j200 = len(top_ids(rows, 200) & base_top200) / 200.0
        # mean |Δrank| on baseline top200
        deltas = []
        for wid in base_top200:
            if wid in m:
                deltas.append(abs(m[wid] - base_map[wid]))
        mean_abs = sum(deltas) / len(deltas) if deltas else None
        # watchlist Δrank (positive = rose / improved when feature removed? 
        # rank decrease = rose. Δ = abl_rank - base_rank; negative means rose without feature)
        watch_delta = []
        for w in watch:
            br = base_map.get(w["work_id"])
            ar = m.get(w["work_id"])
            if br is not None and ar is not None:
                watch_delta.append(
                    {
                        "query": w["query"],
                        "base_rank": br,
                        "abl_rank": ar,
                        "delta": ar - br,  # negative => rose when feature removed
                    }
                )
        tau = kendall_top(base_map, m, base_top200)
        blob = {
            "feature": feat,
            "used_in": [
                s
                for s, d in [
                    ("classic", CLASSIC_TERMS),
                    ("anti", ANTI_TERMS),
                    ("normie", NORMIE_TERMS),
                ]
                if feat in d
            ],
            "baseline_coef": {
                "classic": CLASSIC_TERMS.get(feat),
                "anti": ANTI_TERMS.get(feat),
                "normie": NORMIE_TERMS.get(feat),
            },
            "metrics": summ,
            "delta_Q": summ["Q"] - base_sum["Q"],
            "delta_pos50": summ["pos50"] - base_sum["pos50"],
            "delta_anti50": summ["anti50"] - base_sum["anti50"],
            "jaccard_top50": j50,
            "jaccard_top200": j200,
            "mean_abs_delta_rank_top200": mean_abs,
            "kendall_top200": tau,
            "watch_delta": watch_delta,
            "top8": summ["top15"][:8],
        }
        results["ablations"][feat] = blob
        print(
            f"  drop {feat:28s} ΔQ={blob['delta_Q']:+.1f} Δpos50={blob['delta_pos50']:+d} "
            f"J50={j50:.2f} mean|Δr|={mean_abs:.1f} τ={tau:.3f}",
            flush=True,
        )

    # --- Trajectories ---
    print("\n=== trajectories ===", flush=True)
    traj: dict[str, Any] = {}

    # Sweep λ_anti
    lam_path = []
    for lam_a in [0.0, 0.3, 0.55, 0.85, 1.15, 1.5, 2.0]:
        build_affinity(
            con,
            moments,
            classic_terms=CLASSIC_TERMS,
            anti_terms=ANTI_TERMS,
            normie_terms=NORMIE_TERMS,
            lam_a=lam_a,
            lam_n=0.75,
        )
        rows = contrastive_rank(con)
        summ = summarize_ranking(rows, ev, con, watch)
        lam_path.append(
            {
                "lam_anti": lam_a,
                "Q": summ["Q"],
                "pos50": summ["pos50"],
                "anti50": summ["anti50"],
                "watch": {w["query"]: w["rank"] for w in summ["watch"]},
                "top5": [r["title"] for r in summ["top15"][:5]],
            }
        )
        print(f"  λ_anti={lam_a:.2f} Q={summ['Q']:.1f} pos50={summ['pos50']}", flush=True)
    traj["lambda_anti"] = lam_path

    # Sweep top_frac (strictness of focus cohort)
    frac_path = []
    build_affinity(
        con, moments, classic_terms=CLASSIC_TERMS, anti_terms=ANTI_TERMS, normie_terms=NORMIE_TERMS
    )
    for frac in [0.12, 0.08, 0.06, 0.04, 0.025, 0.015]:
        rows = contrastive_rank(con, top_frac=frac)
        summ = summarize_ranking(rows, ev, con, watch)
        frac_path.append(
            {
                "top_frac": frac,
                "Q": summ["Q"],
                "pos50": summ["pos50"],
                "anti50": summ["anti50"],
                "watch": {w["query"]: w["rank"] for w in summ["watch"]},
                "top5": [r["title"] for r in summ["top15"][:5]],
            }
        )
        print(f"  top_frac={frac:.3f} Q={summ['Q']:.1f} pos50={summ['pos50']}", flush=True)
    traj["top_frac"] = frac_path

    # Sweep series gate
    series_path = []
    for sg in [0.55, 0.45, 0.40, 0.32, 0.25, 0.18]:
        build_affinity(
            con,
            moments,
            classic_terms=CLASSIC_TERMS,
            anti_terms=ANTI_TERMS,
            normie_terms=NORMIE_TERMS,
            series_gate=sg,
        )
        rows = contrastive_rank(con)
        summ = summarize_ranking(rows, ev, con, watch)
        series_path.append(
            {
                "series_gate": sg,
                "n_gated": con.execute(
                    "SELECT count(*) FROM user_affinity_gated"
                ).fetchone()[0],
                "Q": summ["Q"],
                "pos50": summ["pos50"],
                "anti50": summ["anti50"],
                "watch": {w["query"]: w["rank"] for w in summ["watch"]},
                "top5": [r["title"] for r in summ["top15"][:5]],
            }
        )
        print(
            f"  series_gate={sg:.2f} gated={series_path[-1]['n_gated']:,} "
            f"Q={summ['Q']:.1f}",
            flush=True,
        )
    traj["series_gate"] = series_path
    results["trajectories"] = traj

    # Trajectory archetypes: books that monotonically rise/fall with λ_anti
    archetypes = classify_trajectories(traj["lambda_anti"], watch)
    results["trajectory_archetypes_lambda_anti"] = archetypes

    results["suggestions"] = SUGGESTIONS
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    _write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    con.close()


def classify_trajectories(path: list[dict], watch: list[dict]) -> dict[str, Any]:
    """Label watch books by how rank moves as λ_anti increases."""
    out = {"rising": [], "falling": [], "u_shaped": [], "flat_or_noisy": [], "missing": []}
    for w in watch:
        q = w["query"]
        ranks = []
        for step in path:
            r = step["watch"].get(q)
            ranks.append(r)
        known = [(i, r) for i, r in enumerate(ranks) if r is not None]
        if len(known) < 3:
            out["missing"].append({"query": q, "ranks": ranks})
            continue
        # use early vs late
        early = known[0][1]
        late = known[-1][1]
        mid = known[len(known) // 2][1]
        deltas = [ranks[i + 1] - ranks[i] for i in range(len(ranks) - 1)
                  if ranks[i] is not None and ranks[i + 1] is not None]
        rise = sum(1 for d in deltas if d < 0)  # rank number decreases
        fall = sum(1 for d in deltas if d > 0)
        entry = {"query": q, "ranks": ranks, "early": early, "late": late, "delta": late - early}
        if late <= early - 8 and rise >= fall:
            out["rising"].append(entry)  # improves under stronger anti penalty
        elif late >= early + 8 and fall >= rise:
            out["falling"].append(entry)
        elif mid < early - 5 and mid < late - 5:
            out["u_shaped"].append(entry)  # best in middle
        else:
            out["flat_or_noisy"].append(entry)
    return out


SUGGESTIONS = [
    {
        "name": "Multi-proxy Pareto, not single Q",
        "detail": (
            "Treat literary_poll / anti / normie as noisy voters. Prefer parameter "
            "regions that jointly: (a) keep anti50 near 0, (b) don't collapse to "
            "only mega-syllabus fillers, (c) stay stable under feature ablation, "
            "(d) surface multilingual consecrated works without romance heads."
        ),
    },
    {
        "name": "Internal consistency / stability as accuracy proxy",
        "detail": (
            "Bootstrap users, re-fit or re-rank, measure Jaccard@50 and Kendall on "
            "top200. A 'more accurate' metric should be stabler under resampling than "
            "a brittle one that overfits pile quirks."
        ),
    },
    {
        "name": "Trajectory archetypes (your Dhalgren idea)",
        "detail": (
            "Sweep a knob (λ_anti, series gate, top_frac). Cluster books by rank path: "
            "anti-sensitive risers, syllabus-stable, romance-crashers, mid-peak "
            "experimental. Use archetype purity (do risers cohere?) as a structural "
            "signal without trusting any single title list."
        ),
    },
    {
        "name": "Held-out community recovery",
        "detail": (
            "From PMI/reflections, freeze non-English literary communities (Arabic, "
            "Turkish, …) as unlabeled targets. Metrics that recover them without "
            "language labels are discovering real consecration structure."
        ),
    },
    {
        "name": "Iterative co-training",
        "detail": (
            "1) Rank with current metric. 2) Take head ∩ high-stability books as a "
            "soft positive expansion (and romance/series head as soft negative). "
            "3) Re-estimate only user-feature weights / gates. 4) Require the next "
            "head to improve stability + anti rejection, else reject the step. "
            "Stops runaway confirmation if expansion is tiny and audited."
        ),
    },
    {
        "name": "Human-in-the-loop on trajectories, not on piles",
        "detail": (
            "Instead of enlarging lit-2014-2024, label a few trajectory archetypes "
            "('this rising path feels right / wrong'). That supervises the geometry "
            "of the metric with less canon politics."
        ),
    },
]


def _write_report(results: dict[str, Any]) -> None:
    b = results["baseline"]
    lines = [
        "# Feature sensitivity & rank trajectories",
        "",
        "Probe piles are **fallible** — Q/pos50 are reference signals, not truth. "
        "Impact is judged by ranking geometry change (Jaccard, Kendall, watchlist Δrank) "
        "as much as by probe scores.",
        "",
        "## Baseline (contrastive unseeded)",
        "",
        f"- Q={b['Q']:.1f} pos50={b['pos50']} anti50={b['anti50']} "
        f"classic50={b['classic50']} normie50={b['normie50']}",
        "",
        "Watchlist ranks:",
        "",
    ]
    for w in b["watch"]:
        lines.append(f"- {w['query']}: **{w['rank']}** ({w['title']} — {w['author']})")

    # Ablation table sorted by mean abs delta rank
    ab = list(results["ablations"].values())
    ab.sort(key=lambda x: -(x["mean_abs_delta_rank_top200"] or 0))
    lines += [
        "",
        "## Feature ablation (zero weight in classic+anti+normie terms)",
        "",
        "Larger `mean|Δrank|` / smaller Jaccard ⇒ feature more load-bearing for the ranking.",
        "",
        "| feature | in | ΔQ | Δpos50 | J@50 | mean\\|Δr\\|@200 | τ@200 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for x in ab:
        lines.append(
            f"| {x['feature']} | {','.join(x['used_in'])} | {x['delta_Q']:+.1f} | "
            f"{x['delta_pos50']:+d} | {x['jaccard_top50']:.2f} | "
            f"{x['mean_abs_delta_rank_top200']:.1f} | {x['kendall_top200']:.3f} |"
        )

    lines += ["", "### Watchlist moves when feature dropped (Δrank; − = rose)", ""]
    for x in ab[:8]:
        lines.append(f"**drop `{x['feature']}`** (ΔQ={x['delta_Q']:+.1f})")
        for w in x["watch_delta"]:
            if abs(w["delta"]) >= 5:
                lines.append(
                    f"- {w['query']}: {w['base_rank']} → {w['abl_rank']} (Δ {w['delta']:+d})"
                )
        lines.append("")

    lines += ["", "## Trajectories", ""]
    for name, path in results["trajectories"].items():
        lines.append(f"### Sweep `{name}`")
        if name == "lambda_anti":
            lines.append("| λ_anti | Q | pos50 | anti50 | Dhalgren | Ulysses | Hate U Give | ACOTAR |")
            lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
            for s in path:
                w = s["watch"]
                lines.append(
                    f"| {s['lam_anti']:.2f} | {s['Q']:.1f} | {s['pos50']} | {s['anti50']} | "
                    f"{w.get('Dhalgren')} | {w.get('Ulysses')} | {w.get('The Hate U Give')} | "
                    f"{w.get('A Court of Mist and Fury')} |"
                )
        elif name == "top_frac":
            lines.append("| top_frac | Q | pos50 | Dhalgren | Moby-Dick | 1984 | Words of Radiance |")
            lines.append("|---:|---:|---:|---:|---:|---:|---:|")
            for s in path:
                w = s["watch"]
                lines.append(
                    f"| {s['top_frac']:.3f} | {s['Q']:.1f} | {s['pos50']} | "
                    f"{w.get('Dhalgren')} | {w.get('Moby-Dick')} | {w.get('1984')} | "
                    f"{w.get('Words of Radiance')} |"
                )
        else:
            lines.append("| series_gate | n_gated | Q | pos50 | Dhalgren | Lolita | ACOTAR |")
            lines.append("|---:|---:|---:|---:|---:|---:|---:|")
            for s in path:
                w = s["watch"]
                lines.append(
                    f"| {s['series_gate']:.2f} | {s['n_gated']} | {s['Q']:.1f} | {s['pos50']} | "
                    f"{w.get('Dhalgren')} | {w.get('Lolita')} | "
                    f"{w.get('A Court of Mist and Fury')} |"
                )
        lines.append("")

    arch = results.get("trajectory_archetypes_lambda_anti") or {}
    lines += ["## λ_anti trajectory archetypes (watchlist)", ""]
    for kind in ("rising", "falling", "u_shaped", "flat_or_noisy", "missing"):
        items = arch.get(kind) or []
        lines.append(f"### {kind} ({len(items)})")
        for e in items:
            lines.append(f"- {e['query']}: {e.get('ranks')}")
        lines.append("")

    lines += ["## Improving accuracy without a trusted canon", ""]
    for s in results["suggestions"]:
        lines.append(f"### {s['name']}")
        lines.append(s["detail"])
        lines.append("")

    lines += [
        "## Practical next data to gather",
        "",
        "1. Full trajectory matrices for top~500 baseline books across λ_anti / series_gate / top_frac.",
        "2. Bootstrap stability curves (Jaccard@50 vs resample).",
        "3. Soft labels on a few dozen *paths* (not titles): experimental-riser vs syllabus-flat vs junk-crasher.",
        "4. Multilingual community recovery scores as an external structural check.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

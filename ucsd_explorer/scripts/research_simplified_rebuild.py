#!/usr/bin/env python3
"""Research: sliders-at-zero, normie ablations, Pareto, percentile anchoring.

Writes:
  ucsd_explorer/data/simplified_rebuild_research.json
  ucsd_explorer/data/SIMPLIFIED_REBUILD_REPORT.md
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from ucsd_explorer.db import NORMIE_PATH, ROOT, execute, get_con
from ucsd_explorer.ranking import (
    _curator_user_weight_sql,
    deep_com_share_cap,
    normie_depth_params,
    normie_purity_params,
    rank_books,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "simplified_rebuild_research.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "SIMPLIFIED_REBUILD_REPORT.md"

GOOD = [
    "The Left Hand of Darkness",
    "The Dispossessed",
    "Solaris",
    "Ubik",
    "Kindred",
    "Neuromancer",
    "Blindsight",
    "A Canticle for Leibowitz",
    "The Stars My Destination",
    "Dhalgren",
    "Hyperion",
    "The Three-Body Problem",
    "Roadside Picnic",
    "The Book of the New Sun",
    "Shadow of the Torturer",
    "Permutation City",
]
BAD = [
    "Ready Player One",
    "The Martian",
    "Ender's Game",
    "Speaker for the Dead",
    "Red Rising",
    "Old Man's War",
    "The Hunger Games",
    "Divergent",
    "The Name of the Wind",
    "The Way of Kings",
    "Wool",
    "Dark Matter",
    "Artemis",
]


def _base_params(**kw: Any) -> dict[str, Any]:
    p = {
        "method": "curator_deep_pct_love",
        "min_votes": 25,
        "max_n": 0,
        "bayesian_m": 30,
        "limit": 400,
        "curator_strictness": 0,
        "curator_strictness_mode": "deweight",
        "normie_depth": 0,
        "normie_purity": 0,
        "coverage_weight": 0.0,
        "genre_gates": ["sf"],
        "fiction_only": True,
        "exclude_comics": True,
        "exclude_picture_books": True,
        "exclude_derivatives": True,
        "exclude_collections": True,
        "collapse_duplicates": True,
    }
    p.update(kw)
    return p


def _title_ranks(results: list[dict]) -> dict[str, int | None]:
    out: dict[str, int | None] = {t: None for t in GOOD + BAD}
    for r in results:
        title = r.get("title") or ""
        for t in out:
            if out[t] is None and t.lower() in title.lower():
                out[t] = int(r["rank"])
    return out


def _quality(ranks: dict[str, int | None]) -> dict[str, Any]:
    def stats(keys: list[str]) -> dict[str, Any]:
        vals = [ranks[k] for k in keys if ranks.get(k) is not None]
        miss = [k for k in keys if ranks.get(k) is None]
        if not vals:
            return {
                "n_found": 0,
                "median": None,
                "mean": None,
                "top50": 0,
                "top100": 0,
                "top200": 0,
                "missing": miss,
            }
        vals_s = sorted(vals)
        mid = vals_s[len(vals_s) // 2]
        return {
            "n_found": len(vals),
            "median": mid,
            "mean": sum(vals) / len(vals),
            "top50": sum(1 for v in vals if v <= 50),
            "top100": sum(1 for v in vals if v <= 100),
            "top200": sum(1 for v in vals if v <= 200),
            "missing": miss,
        }

    g = stats(GOOD)
    b = stats(BAD)
    # Higher better: good early, bad late / missing.
    # Missing bad counts as rank 999.
    bad_vals = [ranks[k] if ranks.get(k) is not None else 999 for k in BAD]
    good_vals = [ranks[k] for k in GOOD if ranks.get(k) is not None]
    q = 0.0
    if good_vals:
        q += 2.0 * sum(1 for v in good_vals if v <= 50)
        q += 1.0 * sum(1 for v in good_vals if 50 < v <= 100)
        q -= 3.0 * sum(1 for v in bad_vals if v <= 50)
        q -= 2.0 * sum(1 for v in bad_vals if 50 < v <= 100)
        q -= 0.5 * sum(1 for v in bad_vals if 100 < v <= 200)
        q += (sorted(bad_vals)[len(bad_vals) // 2]) / 80.0
        q -= (sorted(good_vals)[len(good_vals) // 2]) / 100.0
    return {"score": q, "good": g, "bad": b}


def _voter_mass(results: list[dict], *, top_k: int = 100) -> dict[str, float]:
    rows = results[:top_k]
    if not rows:
        return {"median_n": 0.0, "mean_n": 0.0, "geo_n": 0.0}
    ns = [max(1.0, float(r.get("n") or 1)) for r in rows]
    ns_s = sorted(ns)
    geo = math.exp(sum(math.log(x) for x in ns) / len(ns))
    return {
        "median_n": ns_s[len(ns_s) // 2],
        "mean_n": sum(ns) / len(ns),
        "geo_n": geo,
    }


def _run(label: str, **kw: Any) -> dict[str, Any]:
    t0 = time.time()
    params = _base_params(**kw)
    data = rank_books(params)
    results = data.get("results") or []
    ranks = _title_ranks(results)
    qual = _quality(ranks)
    mass = _voter_mass(results)
    # Approximate eligible curator count via gate (best-effort)
    return {
        "label": label,
        "params": {
            k: params[k]
            for k in (
                "curator_strictness",
                "normie_depth",
                "normie_purity",
                "coverage_weight",
                "bayesian_m",
                "min_votes",
            )
        },
        "n_results": len(results),
        "quality": qual,
        "voter_mass": mass,
        "ranks": ranks,
        "top15": [
            {"rank": r["rank"], "n": r["n"], "title": r["title"], "score": r.get("score")}
            for r in results[:15]
        ],
        "elapsed_s": round(time.time() - t0, 2),
        "meta": {
            "deep_com_share_cap": data.get("deep_com_share_cap"),
            "normie_gates": data.get("normie_gates"),
        },
    }


def cohort_diagnostics() -> dict[str, Any]:
    """Explain why sliders-at-0 still look curated."""
    con = get_con()
    n_deep = int(con.execute("SELECT count(*) FROM user_curator_deep_weight").fetchone()[0])
    n_pct = int(con.execute("SELECT count(*) FROM user_curator_pct_weight").fetchone()[0])
    mint = con.execute(
        """
        SELECT
          avg(deep_share), approx_quantile(deep_share, 0.1),
          avg(com_share), approx_quantile(com_share, 0.9),
          avg(n_deep), avg(n_normie)
        FROM user_curator_deep_weight
        """
    ).fetchone()

    sizes = {}
    for label, depth, purity, strict, force_com in [
        ("mint_only_no_query_com", 0, 0, 0, None),  # can't disable com in API; measure SQL
        ("sliders_0_default_com", 0, 0, 0, "default"),
        ("depth40_pur55", 40, 55, 0, "default"),
        ("depth40_pur0", 40, 0, 0, "default"),
        ("depth0_pur55", 0, 55, 0, "default"),
        ("strict50_d40_p55", 40, 55, 50, "default"),
        ("strict100_d40_p55", 40, 55, 100, "default"),
    ]:
        we, gate, args, et = _curator_user_weight_sql(
            pct=True,
            mode="deweight",
            strictness=strict,
            deep=True,
            normie_depth=depth,
            normie_purity=purity,
        )
        # Patch: measure with com_cap at purity 0 as if truly off (cap=1.0)
        if force_com is None:
            # strip com share lines by rebuilding gate without default com
            we2, gate2, args2, _ = _curator_user_weight_sql(
                pct=True,
                mode="deweight",
                strictness=strict,
                deep=False,  # no deep gates
            )
            # manually apply only mint table + depth/purity without com
            from ucsd_explorer.ranking import _normie_gate_sql

            nsql, nargs = _normie_gate_sql(depth, purity)
            gate_m = nsql
            args_m = list(nargs)
            n = int(
                con.execute(
                    f"SELECT count(*) FROM user_curator_deep_weight c WHERE TRUE {gate_m}",
                    args_m,
                ).fetchone()[0]
            )
            sizes[label] = {
                "n": n,
                "note": "depth/purity only; NO query com_share cap",
                "com_cap": None,
            }
            continue

        n = int(
            con.execute(
                f"SELECT count(*) FROM user_curator_deep_weight c WHERE TRUE {gate}",
                args,
            ).fetchone()[0]
        )
        pur_for = purity if purity > 0 else 55.0
        sizes[label] = {
            "n": n,
            "com_cap": deep_com_share_cap(pur_for),
            "depth_params": normie_depth_params(depth),
            "purity_params": normie_purity_params(purity),
        }

    # True everyone = pct curators (not deep mint)
    sizes["all_pct_curators"] = {"n": n_pct}
    sizes["deep_mint_table"] = {"n": n_deep}

    return {
        "n_deep_mint": n_deep,
        "n_pct_curators": n_pct,
        "mint_stats": {
            "avg_deep_share": mint[0],
            "p10_deep_share": mint[1],
            "avg_com_share": mint[2],
            "p90_com_share": mint[3],
            "avg_n_deep": mint[4],
            "avg_n_normie": mint[5],
        },
        "cohort_sizes": sizes,
        "explanation": [
            "Materialization already keeps only users with n_deep≥2, deep_share≥0.35, com_share≤0.20 (~20k).",
            "Query-time purity=0 still applies com_share cap as if purity=55 (~0.111) — so 'all zero' is NOT inactive.",
            "depth=0/purity=0 still leave that mint floor + com cap; ranking looks 'curated' because the table is pre-curated.",
            "curator_strictness=0 correctly keeps all passers (no top-K shrink).",
        ],
    }


def inferred_normie() -> dict[str, Any]:
    """Can we recover school-canon-like titles from discrimination stats?"""
    con = get_con()
    hand = []
    if NORMIE_PATH.exists():
        hand = json.loads(NORMIE_PATH.read_text())["titles"]

    # Discrimination on poll works: like★≥4 rate in deep mint vs all active users
    rows = con.execute(
        """
        WITH active AS (
          SELECT user_id FROM user_star_hist WHERE n_rated >= 30
        ),
        deep AS (
          SELECT user_id FROM user_curator_deep_weight
        ),
        poll AS (
          SELECT work_id, poll_title, work_title AS title, n, rarity, prestige
          FROM poll_works
        ),
        likes AS (
          SELECT e.work_id, e.user_id
          FROM all_rating_events e
          JOIN poll USING (work_id)
          WHERE e.rating >= 4
        ),
        stats AS (
          SELECT
            p.work_id,
            p.poll_title,
            p.title,
            p.n AS catalog_n,
            p.rarity,
            p.prestige,
            (SELECT count(*) FROM active) AS n_active,
            (SELECT count(*) FROM deep) AS n_deep,
            count(DISTINCT l.user_id) FILTER (
              WHERE l.user_id IN (SELECT user_id FROM active)
            )::DOUBLE AS n_liked_active,
            count(DISTINCT l.user_id) FILTER (
              WHERE l.user_id IN (SELECT user_id FROM deep)
            )::DOUBLE AS n_liked_deep
          FROM poll p
          LEFT JOIN likes l USING (work_id)
          GROUP BY 1,2,3,4,5,6
        )
        SELECT
          poll_title,
          title,
          catalog_n,
          rarity,
          prestige,
          n_liked_active / nullif(n_active, 0) AS p_all,
          n_liked_deep / nullif(n_deep, 0) AS p_deep,
          (n_liked_deep / nullif(n_deep, 0))
            / nullif(n_liked_active / nullif(n_active, 0), 0) AS lift
        FROM stats
        ORDER BY catalog_n DESC
        """
    ).fetchall()

    items = []
    for poll_title, title, n, rarity, prestige, p_all, p_deep, lift in rows:
        items.append(
            {
                "poll_title": poll_title,
                "title": title,
                "n": int(n or 0),
                "rarity": float(rarity or 0),
                "prestige": float(prestige or 0),
                "p_all": float(p_all or 0),
                "p_deep": float(p_deep or 0),
                "lift": float(lift or 0) if lift is not None else None,
                "in_hand_normie": any(
                    (poll_title or "").lower() == h.lower()
                    or (title or "").lower().startswith(h.lower())
                    for h in hand
                ),
            }
        )

    # Inferred normie: high popularity + low lift (deep likes them ~as often as everyone)
    # Deep signals: high lift
    scored = [x for x in items if x["lift"] is not None and x["p_all"] > 0]
    by_normie_score = sorted(
        scored,
        key=lambda x: (x["n"] * (1.0 / max(x["lift"], 0.5)), x["n"]),
        reverse=True,
    )
    inferred_top = by_normie_score[:25]
    by_lift = sorted(scored, key=lambda x: x["lift"], reverse=True)[:15]

    # Also: most popular poll works regardless (popularity proxy)
    by_n = sorted(items, key=lambda x: x["n"], reverse=True)[:25]

    hand_matched = [x for x in items if x["in_hand_normie"]]
    # Overlap: hand titles that appear in inferred top-25 by normie score
    inferred_titles = {x["poll_title"] for x in inferred_top}
    hand_in_inferred = sum(1 for x in hand_matched if x["poll_title"] in inferred_titles)

    return {
        "n_poll_works": len(items),
        "hand_normie_on_poll": hand_matched,
        "inferred_normie_top25": inferred_top,
        "high_lift_deep_signals_top15": by_lift,
        "most_popular_poll_top25": by_n,
        "overlap_hand_in_inferred_top25": hand_in_inferred,
        "notes": [
            "lift = P(★≥4|deep) / P(★≥4|active). lift≈1 → everyone likes it (school/ubiquitous).",
            "lift≫1 → deep curators disproportionately like it (useful positive signal).",
            "Popularity×(1/lift) ranks ubiquitous chart books that don't discriminate — a data-driven normie proxy.",
            "Hand list also includes non-poll school books (Gatsby, Mockingbird) that affect deep_share only.",
        ],
    }


def percentile_ablation() -> dict[str, Any]:
    """Lit-anchored pct vs full-shelf pct vs raw 5★ rate on same deep cohort."""
    con = get_con()
    # Build scores for SF works among deep users with depth40/purity55 gates
    we, gate, args, _ = _curator_user_weight_sql(
        pct=True,
        mode="deweight",
        strictness=0,
        deep=True,
        normie_depth=40,
        normie_purity=55,
    )

    # Precompute full-shelf midpoints from user_star_hist
    sql = f"""
    WITH cur AS (
      SELECT c.user_id, ({we})::DOUBLE AS w
      FROM user_curator_deep_weight c
      WHERE TRUE
      {gate}
    ),
    full_pct AS (
      SELECT
        user_id,
        (((c1+c2+c3+c4)::DOUBLE / n_rated) + 1.0) / 2.0 AS pct5_full,
        (((c1+c2+c3)::DOUBLE / n_rated)
          + ((c1+c2+c3+c4)::DOUBLE / n_rated)) / 2.0 AS pct4_full
      FROM user_star_hist
      WHERE n_rated >= 20
    ),
    ev AS (
      SELECT
        e.work_id,
        e.rating,
        c.w,
        p.pct_5 AS pct5_adj,
        p.source AS pct_source,
        f.pct5_full,
        CASE WHEN e.rating = 5 THEN 1.0 ELSE 0.0 END AS is5
      FROM all_rating_events e
      JOIN cur c USING (user_id)
      JOIN work_genre_gates g
        ON g.work_id = e.work_id AND g.gate = 'sf' AND g.passed
      LEFT JOIN user_star_percentiles p USING (user_id)
      LEFT JOIN full_pct f USING (user_id)
      WHERE e.rating >= 1
    ),
    agg AS (
      SELECT
        work_id,
        sum(w)::DOUBLE AS w_sum,
        count(*)::BIGINT AS n_raw,
        sum(w * power(greatest(coalesce(pct5_adj, pct5_full, 0.5), 1e-6), 2.5))
          FILTER (WHERE rating = 5)::DOUBLE AS love_adj,
        sum(w * power(greatest(coalesce(pct5_full, 0.5), 1e-6), 2.5))
          FILTER (WHERE rating = 5)::DOUBLE AS love_full,
        sum(w * is5)::DOUBLE AS w5,
        sum(w * CASE WHEN pct_source = 'lit' THEN 1 ELSE 0 END)::DOUBLE AS w_lit_src
      FROM ev
      GROUP BY work_id
    )
    SELECT
      s.work_id, s.title, s.author, s.n AS catalog_n,
      a.n_raw,
      a.w_sum,
      a.love_adj / nullif(a.w_sum, 0) AS score_adj,
      a.love_full / nullif(a.w_sum, 0) AS score_full,
      a.w5 / nullif(a.w_sum, 0) AS p5_raw,
      a.w_lit_src / nullif(a.w_sum, 0) AS frac_lit_anchored
    FROM agg a
    JOIN work_scores s USING (work_id)
    JOIN work_flags f USING (work_id)
    WHERE a.n_raw >= 25
      AND NOT coalesce(f.is_nonfiction, false)
      AND NOT coalesce(f.is_comic, false)
      AND NOT coalesce(f.is_picture_book, false)
      AND NOT coalesce(f.is_collection, false)
      AND NOT coalesce(f.is_derivative, false)
    """
    rows = con.execute(sql, args).fetchall()
    cols = [
        "work_id",
        "title",
        "author",
        "catalog_n",
        "n_raw",
        "w_sum",
        "score_adj",
        "score_full",
        "p5_raw",
        "frac_lit_anchored",
    ]
    books = [dict(zip(cols, r)) for r in rows]

    def rank_by(key: str) -> dict[str, int]:
        ordered = sorted(books, key=lambda b: (-(b[key] or 0), -b["n_raw"]))
        return {b["work_id"]: i + 1 for i, b in enumerate(ordered)}

    r_adj = rank_by("score_adj")
    r_full = rank_by("score_full")
    r_p5 = rank_by("p5_raw")

    def find_ranks(substr: str) -> dict[str, Any]:
        hits = [b for b in books if substr.lower() in (b["title"] or "").lower()]
        hits = sorted(hits, key=lambda b: -b["catalog_n"])[:3]
        out = []
        for b in hits:
            wid = b["work_id"]
            out.append(
                {
                    "title": b["title"],
                    "catalog_n": b["catalog_n"],
                    "n_raw": b["n_raw"],
                    "rank_adj": r_adj[wid],
                    "rank_full": r_full[wid],
                    "rank_p5": r_p5[wid],
                    "delta_full_minus_adj": r_full[wid] - r_adj[wid],
                    "delta_p5_minus_adj": r_p5[wid] - r_adj[wid],
                    "frac_lit_anchored": b["frac_lit_anchored"],
                }
            )
        return out

    probes = {}
    for t in GOOD + BAD + ["I Love Dick", "Nova Swing", "Light", "Blindsight", "Dhalgren"]:
        probes[t] = find_ranks(t)

    # Obscure vs popular bands: mean rank delta (full - adj); positive => adj ranks obscure higher
    obscure = [b for b in books if b["catalog_n"] < 500]
    popular = [b for b in books if b["catalog_n"] >= 5000]

    def band_delta(band: list[dict]) -> dict[str, float]:
        if not band:
            return {}
        d_full = [r_full[b["work_id"]] - r_adj[b["work_id"]] for b in band]
        d_p5 = [r_p5[b["work_id"]] - r_adj[b["work_id"]] for b in band]
        # Among GOOD titles in band
        return {
            "n": len(band),
            "mean_rank_delta_full_vs_adj": sum(d_full) / len(d_full),
            "mean_rank_delta_p5_vs_adj": sum(d_p5) / len(d_p5),
            "pct_adj_better_than_full": sum(1 for d in d_full if d > 0) / len(d_full),
            "pct_adj_better_than_p5": sum(1 for d in d_p5 if d > 0) / len(d_p5),
        }

    # Literary obscure: in GOOD list and catalog_n < 2000
    lit_obscure = []
    for b in books:
        for g in GOOD:
            if g.lower() in (b["title"] or "").lower() and b["catalog_n"] < 3000:
                lit_obscure.append(b)
                break

    return {
        "n_books_scored": len(books),
        "band_obscure_n_lt_500": band_delta(obscure),
        "band_popular_n_ge_5000": band_delta(popular),
        "literary_probe_obscure": band_delta(lit_obscure),
        "probes": probes,
        "interpretation_hint": (
            "delta_full_minus_adj > 0 means adjusted (lit-anchored) ranks the book BETTER "
            "(lower rank number) than full-shelf percentiles."
        ),
    }


def pareto_sweep() -> dict[str, Any]:
    """Sweep depth/purity/strictness; maximize literary quality vs voter mass."""
    grid = []
    depths = [0, 40, 60]
    purities = [0, 55, 75]
    stricts = [0, 40, 80]
    for d in depths:
        for p in purities:
            for s in stricts:
                # skip some redundant corners to save time? full 4*4*3=48 — a bit heavy
                # do all but it's ok if each is ~2-5s
                label = f"d{d}_p{p}_s{s}"
                print(f"  pareto {label}…", flush=True)
                try:
                    run = _run(label, normie_depth=d, normie_purity=p, curator_strictness=s)
                except Exception as e:
                    grid.append({"label": label, "error": str(e)})
                    continue
                q = run["quality"]["score"]
                v = run["voter_mass"]["geo_n"]
                grid.append(
                    {
                        "label": label,
                        "depth": d,
                        "purity": p,
                        "strictness": s,
                        "quality": q,
                        "geo_n": v,
                        "median_n": run["voter_mass"]["median_n"],
                        "good_med": run["quality"]["good"]["median"],
                        "bad_med": run["quality"]["bad"]["median"],
                        "good_top50": run["quality"]["good"]["top50"],
                        "bad_top100": run["quality"]["bad"]["top100"],
                        "com_cap": run["meta"].get("deep_com_share_cap"),
                    }
                )

    valid = [g for g in grid if "quality" in g]
    if not valid:
        return {"grid": grid}

    # Normalize to [0,1] and find utopia / knee
    qs = [g["quality"] for g in valid]
    vs = [math.log(max(g["geo_n"], 1)) for g in valid]
    qmin, qmax = min(qs), max(qs)
    vmin, vmax = min(vs), max(vs)

    def norm_q(q: float) -> float:
        return (q - qmin) / (qmax - qmin + 1e-9)

    def norm_v(v: float) -> float:
        lv = math.log(max(v, 1))
        return (lv - vmin) / (vmax - vmin + 1e-9)

    for g in valid:
        g["q_norm"] = norm_q(g["quality"])
        g["v_norm"] = norm_v(g["geo_n"])
        # distance to utopia (1,1)
        g["dist_utopia"] = math.hypot(1 - g["q_norm"], 1 - g["v_norm"])
        # product (balanced)
        g["qv_product"] = g["q_norm"] * g["v_norm"]
        # weighted: prefer quality slightly
        g["qv_quality_lean"] = 0.65 * g["q_norm"] + 0.35 * g["v_norm"]

    # Pareto front: not dominated
    front = []
    for g in valid:
        dominated = False
        for h in valid:
            if h is g:
                continue
            if (h["quality"] >= g["quality"] and h["geo_n"] >= g["geo_n"]) and (
                h["quality"] > g["quality"] or h["geo_n"] > g["geo_n"]
            ):
                dominated = True
                break
        if not dominated:
            front.append(g["label"])

    best_utopia = min(valid, key=lambda g: g["dist_utopia"])
    best_prod = max(valid, key=lambda g: g["qv_product"])
    best_qlean = max(valid, key=lambda g: g["qv_quality_lean"])
    best_q = max(valid, key=lambda g: g["quality"])
    best_v = max(valid, key=lambda g: g["geo_n"])

    return {
        "n_runs": len(valid),
        "pareto_front_labels": front,
        "best_utopia_knee": best_utopia,
        "best_product": best_prod,
        "best_quality_lean": best_qlean,
        "best_quality": best_q,
        "best_voter_mass": best_v,
        "grid": valid,
    }


def normie_ablation_runs() -> dict[str, Any]:
    """Compare current vs depth-only vs purity-only vs zeros."""
    runs = []
    configs = [
        ("baseline_d40_p55", {"normie_depth": 40, "normie_purity": 55}),
        ("depth_only_d40", {"normie_depth": 40, "normie_purity": 0}),
        ("purity_only_p55", {"normie_depth": 0, "normie_purity": 55}),
        ("sliders_zero", {"normie_depth": 0, "normie_purity": 0}),
        ("strict_mint_sim_d60_p75", {"normie_depth": 60, "normie_purity": 75}),
        ("loose_d25_p35", {"normie_depth": 25, "normie_purity": 35}),
    ]
    for label, kw in configs:
        print(f"  ablation {label}…", flush=True)
        runs.append(_run(label, **kw))

    # Top-100 overlap vs baseline
    base = next(r for r in runs if r["label"] == "baseline_d40_p55")
    base_titles = [t["title"] for t in base["top15"]]
    # fuller overlap from ranks of shared probes
    overlaps = {}
    for r in runs:
        if r["label"] == base["label"]:
            continue
        # Spearman-ish on shared found ranks
        pairs = []
        for t in GOOD + BAD:
            a, b = base["ranks"].get(t), r["ranks"].get(t)
            if a and b:
                pairs.append((a, b))
        if pairs:
            # mean abs rank delta
            mad = sum(abs(a - b) for a, b in pairs) / len(pairs)
        else:
            mad = None
        overlaps[r["label"]] = {
            "mean_abs_rank_delta_vs_baseline": mad,
            "quality_delta": r["quality"]["score"] - base["quality"]["score"],
            "geo_n_ratio": r["voter_mass"]["geo_n"] / max(base["voter_mass"]["geo_n"], 1),
        }

    return {"runs": runs, "vs_baseline": overlaps}


def write_report(payload: dict[str, Any]) -> None:
    diag = payload["slider_zero_diagnosis"]
    abl = payload["normie_ablation"]
    inf = payload["inferred_normie"]
    pct = payload["percentile_ablation"]
    par = payload["pareto"]

    lines: list[str] = []
    lines.append("# Simplified rebuild — research report\n")
    lines.append(f"_Generated from live `explorer.duckdb` experiments._\n")

    lines.append("## 1. Why “all sliders at zero” still looks good\n")
    for e in diag["explanation"]:
        lines.append(f"- {e}")
    lines.append("")
    lines.append(f"- Deep mint table size: **{diag['n_deep_mint']:,}**")
    lines.append(f"- Broader pct-curator table: **{diag['n_pct_curators']:,}**")
    lines.append(
        f"- Mint averages: deep_share≈{diag['mint_stats']['avg_deep_share']:.2f}, "
        f"com_share≈{diag['mint_stats']['avg_com_share']:.3f}, "
        f"n_deep≈{diag['mint_stats']['avg_n_deep']:.1f}, "
        f"n_normie≈{diag['mint_stats']['avg_n_normie']:.1f}"
    )
    lines.append("")
    lines.append("| Setting | Cohort n | com_cap |")
    lines.append("|---|---:|---:|")
    for k, v in diag["cohort_sizes"].items():
        lines.append(f"| {k} | {v.get('n', '')} | {v.get('com_cap', '')} |")
    lines.append("")
    lines.append(
        "**Implication for redesign:** “Inactive sliders” must mean *no mint floors and no "
        "hidden com cap* if you want “everyone.” Prefer explicit mint recipe + query gates, "
        "and if purity=0 then com_cap should be off or separately controlled.\n"
    )

    lines.append("## 2. Normie canon — keep, drop, or infer?\n")
    lines.append("### Ablation vs baseline (depth40 / purity55 / cov0 / SF)\n")
    lines.append("| Config | quality | geo_n (top100) | good median rank | bad median | MAD vs baseline |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in abl["runs"]:
        vs = abl["vs_baseline"].get(r["label"], {})
        mad = vs.get("mean_abs_rank_delta_vs_baseline")
        mad_s = "—" if mad is None else f"{mad:.1f}"
        lines.append(
            f"| {r['label']} | {r['quality']['score']:.2f} | "
            f"{r['voter_mass']['geo_n']:.0f} | {r['quality']['good']['median']} | "
            f"{r['quality']['bad']['median']} | {mad_s} |"
        )
    lines.append("")
    lines.append(
        "**Depth-only** (purity 0) ≈ removing school-share tracking while keeping min deep hits. "
        "**Sliders zero** still has mint floors + hidden com cap.\n"
    )

    lines.append("### Data-inferred normie proxy\n")
    lines.append(
        "For each poll work: `lift = P(★≥4|deep) / P(★≥4|active)`. "
        "Low lift + high n ≈ ubiquitous / school-like; high lift ≈ deep signal.\n"
    )
    lines.append(
        f"Hand-normie titles that fall on the poll and also in inferred-top25: "
        f"**{inf['overlap_hand_in_inferred_top25']}** "
        f"(hand-on-poll count={len(inf['hand_normie_on_poll'])}).\n"
    )
    lines.append("Inferred normie-like (top 12 by popularity×1/lift):\n")
    for x in inf["inferred_normie_top25"][:12]:
        lines.append(
            f"- {x['poll_title']} (n={x['n']}, lift={x['lift']:.2f}, "
            f"hand={x['in_hand_normie']})"
        )
    lines.append("\nHighest-lift poll works (deep discriminators):\n")
    for x in inf["high_lift_deep_signals_top15"][:10]:
        lines.append(f"- {x['poll_title']} (lift={x['lift']:.2f}, n={x['n']})")
    lines.append("")
    lines.append(
        "**Verdict:** You can *approximate* school-canon with a popularity×low-lift rule on the "
        "positive pile, but the hand list also covers **non-poll** syllabus books that only "
        "affect `n_normie`. Pure deletion from the positive pile loses that purity axis. "
        "**Recommendation for v1:** keep an explicit school/neutral list (hand or "
        "data-seeded + editable), used only for share gating — not for positive weight.\n"
    )

    lines.append("## 3. Slider Pareto — literary quality vs voter mass\n")
    lines.append(
        "Competing objectives: **quality** (good-list early / bad-list late) vs "
        "**geo mean curator votes in top 100** (obscure books need mass).\n"
    )
    lines.append(
        "Technique: grid sweep → normalize both axes → "
        "(a) Pareto front, (b) minimize distance to utopia (1,1), "
        "(c) maximize q_norm×v_norm, (d) quality-lean weighted sum.\n"
    )
    if par.get("best_utopia_knee"):
        for name, key in [
            ("Utopia knee", "best_utopia_knee"),
            ("Product max", "best_product"),
            ("Quality-lean", "best_quality_lean"),
            ("Best quality", "best_quality"),
            ("Best mass", "best_voter_mass"),
        ]:
            g = par[key]
            lines.append(
                f"- **{name}:** `{g['label']}` — Q={g['quality']:.2f}, "
                f"geo_n={g['geo_n']:.0f}, good_med={g.get('good_med')}, "
                f"bad_top100={g.get('bad_top100')}"
            )
        lines.append(f"\nPareto front ({len(par['pareto_front_labels'])} points): "
                     + ", ".join(f"`{x}`" for x in par["pareto_front_labels"][:20]))
        if len(par["pareto_front_labels"]) > 20:
            lines.append(f" … +{len(par['pareto_front_labels'])-20} more")
    lines.append("")
    lines.append(
        "**On re-running for new signal piles:** yes — treat (quality probes, voter mass) as "
        "fixed evaluators; swap positive/negative/school packs; re-grid mint+query knobs; "
        "pick knee. Same machinery supports per-user presets later "
        "(cache Pareto or fit a simple response surface).\n"
    )
    lines.append(
        "**Coverage:** keep fixed at 0 (among-raters) for v1; slider optional later.\n"
    )

    lines.append("## 4. Adjusted vs raw percentiles\n")
    lines.append(pct.get("interpretation_hint", ""))
    lines.append("")
    bo = pct.get("band_obscure_n_lt_500") or {}
    bp = pct.get("band_popular_n_ge_5000") or {}
    bl = pct.get("literary_probe_obscure") or {}
    lines.append("| Band | n | mean Δ rank (full−adj) | mean Δ (p5−adj) | % adj better than full |")
    lines.append("|---|---:|---:|---:|---:|")
    for name, b in [
        ("obscure catalog_n<500", bo),
        ("popular catalog_n≥5000", bp),
        ("literary probes (obscure-ish)", bl),
    ]:
        if not b:
            continue
        lines.append(
            f"| {name} | {b.get('n')} | {b.get('mean_rank_delta_full_vs_adj', 0):.1f} | "
            f"{b.get('mean_rank_delta_p5_vs_adj', 0):.1f} | "
            f"{100*b.get('pct_adj_better_than_full', 0):.0f}% |"
        )
    lines.append("\nSelected probes (rank adj / full / raw p5):\n")
    for t in [
        "Blindsight",
        "Dhalgren",
        "I Love Dick",
        "Left Hand of Darkness",
        "Ready Player One",
        "The Martian",
        "Hyperion",
    ]:
        # fuzzy key
        hit = None
        for k, v in pct.get("probes", {}).items():
            if t.lower() in k.lower() and v:
                hit = v[0]
                break
        if not hit:
            continue
        lines.append(
            f"- **{hit['title'][:48]}** (n_cat={hit['catalog_n']}): "
            f"adj=#{hit['rank_adj']}, full=#{hit['rank_full']}, p5=#{hit['rank_p5']} "
            f"(Δfull={hit['delta_full_minus_adj']:+d})"
        )
    lines.append("")

    lines.append("## 5. Recommendations for the simplified rebuild\n")
    lines.append("1. **Curators = today’s deep mint**, renamed; one weight table.")
    lines.append("2. **Keep school/neutral list** for share gating (hand preset + optional data-seeded suggestions); do not only delete from positives.")
    lines.append("3. **Fix “zero means off”** — no hidden purity=55 com_cap; expose com_cap or tie it only to an explicit control.")
    lines.append("4. **Default coverage = 0** (among-raters).")
    lines.append("5. **Minimal knobs:** taste floor (depth + optional purity), com pollution, strictness (make aggressive), min votes, Bayesian m when relevant.")
    lines.append("6. **Scale modes:** keep adjusted percentiles as default if obscure literary probes benefit; offer full-shelf pct and raw stars as alternatives (same cohort).")
    lines.append("7. **Preset packs** (positive / negative / school) editable in UI via `user_author_likes` query-time aggregation; Reset → committed preset.")
    lines.append("8. **Eval harness:** good/bad probes + voter mass + utopia knee — rerun when piles change.")
    lines.append("9. SF toggle + catalog flags only; no similarity in v1; curator vs global histograms yes.")
    lines.append("")
    lines.append("See `simplified_rebuild_research.json` for full grids and probe tables.\n")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    get_con()  # warm
    print("1) slider-zero diagnosis…", flush=True)
    diag = cohort_diagnostics()
    print("2) normie ablation rankings…", flush=True)
    abl = normie_ablation_runs()
    print("3) inferred normie…", flush=True)
    inf = inferred_normie()
    print("4) percentile ablation…", flush=True)
    pct = percentile_ablation()
    print("5) Pareto sweep…", flush=True)
    par = pareto_sweep()

    payload = {
        "slider_zero_diagnosis": diag,
        "normie_ablation": {
            "vs_baseline": abl["vs_baseline"],
            "runs": [
                {
                    k: r[k]
                    for k in (
                        "label",
                        "params",
                        "quality",
                        "voter_mass",
                        "ranks",
                        "top15",
                        "elapsed_s",
                        "meta",
                    )
                }
                for r in abl["runs"]
            ],
        },
        "inferred_normie": inf,
        "percentile_ablation": pct,
        "pareto": par,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    write_report(payload)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

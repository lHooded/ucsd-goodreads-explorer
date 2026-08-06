#!/usr/bin/env python3
"""Cautious co-training on sticky positives (stability veto).

1) Soft positives = books sticky in ≥80% of stability boots (baseline top50).
2) Soft negatives = high series-share / binge head among anti-like users' favorites.
3) Nudge feature weights toward separating sticky-lovers vs binge users (small step).
4) Re-rank; run a short bootstrap; KEEP only if veto passes.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_cotraining
"""

from __future__ import annotations

import json
import math
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from curators_explorer.scripts.research_feature_sensitivity import (
    ANTI_TERMS,
    CLASSIC_TERMS,
    NORMIE_TERMS,
    _moments,
    build_affinity,
    contrastive_rank,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    evaluate,
    load_eval_sets,
    materialize_base,
    rank_from_sql,
)
from curators_explorer.scripts.research_stability import (
    bootstrap_pools,
    contrastive_rank_from_user_lists,
    jaccard,
    load_pools,
    pick_top_frac,
    top_ids,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    FEATURE_COLS,
    build_user_features,
    filler_eval,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "cotraining.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "COTRAINING_REPORT.md"
STABILITY_JSON = Path(__file__).resolve().parents[1] / "data" / "stability_analysis.json"

STEP = 0.35  # blend toward newly estimated weights
TOP_FRAC = 0.06
N_BOOT = 12  # shorter veto check than full stability
SEED = 7
STICKY_RATE = 0.80


def load_sticky_ids() -> list[str]:
    d = json.loads(STABILITY_JSON.read_text(encoding="utf-8"))
    return [
        e["work_id"]
        for e in d["sticky_baseline_top50"]
        if e.get("in_top50_rate", 0) >= STICKY_RATE
    ]


def soft_negative_works(con, *, limit: int = 40) -> list[str]:
    """Books loved by series-binge users (anti-like), excluding sticky IDs."""
    sticky = set(load_sticky_ids())
    rows = con.execute(
        f"""
        WITH binge_users AS (
            SELECT user_id
            FROM user_affinity
            WHERE series_share_5 >= 0.55 AND binge_mean_5 >= 2.2
            ORDER BY anti_raw DESC
            LIMIT 8000
        ),
        agg AS (
            SELECT
                e.work_id,
                count(*) FILTER (WHERE e.rating = 5)::DOUBLE / count(*) AS p5,
                count(*)::BIGINT AS n
            FROM ex.all_rating_events e
            JOIN binge_users b USING (user_id)
            JOIN work_rarity wr ON wr.work_id = e.work_id
            JOIN work_ax wa ON wa.work_id = e.work_id
            WHERE wr.n >= {MIN_RANK_N}
              AND wa.is_seriesish
            GROUP BY e.work_id
            HAVING count(*) >= 40
        )
        SELECT work_id FROM agg
        ORDER BY p5 DESC, n DESC
        LIMIT {limit * 3}
        """
    ).fetchall()
    out = []
    for (wid,) in rows:
        wid = str(wid)
        if wid in sticky:
            continue
        out.append(wid)
        if len(out) >= limit:
            break
    return out


def label_soft_users(con, sticky_ids: list[str], neg_ids: list[str]) -> dict[str, Any]:
    """Users who multi-5★ sticky vs multi-5★ soft-neg series books."""
    con.execute("CREATE OR REPLACE TABLE soft_pos_works (work_id VARCHAR)")
    con.execute("CREATE OR REPLACE TABLE soft_neg_works (work_id VARCHAR)")
    con.executemany("INSERT INTO soft_pos_works VALUES (?)", [(w,) for w in sticky_ids])
    con.executemany("INSERT INTO soft_neg_works VALUES (?)", [(w,) for w in neg_ids])

    con.execute(
        """
        CREATE OR REPLACE TABLE soft_pos_users AS
        SELECT e.user_id, count(DISTINCT e.work_id)::BIGINT AS hits
        FROM ex.all_rating_events e
        JOIN soft_pos_works s USING (work_id)
        JOIN user_rich ur USING (user_id)
        WHERE e.rating = 5
        GROUP BY e.user_id
        HAVING count(DISTINCT e.work_id) >= 4
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE soft_neg_users AS
        SELECT e.user_id, count(DISTINCT e.work_id)::BIGINT AS hits
        FROM ex.all_rating_events e
        JOIN soft_neg_works s USING (work_id)
        JOIN user_rich ur USING (user_id)
        WHERE e.rating = 5
        GROUP BY e.user_id
        HAVING count(DISTINCT e.work_id) >= 6
        """
    )
    # exclusive-ish
    con.execute(
        """
        CREATE OR REPLACE TABLE soft_pos_excl AS
        SELECT p.user_id FROM soft_pos_users p
        WHERE p.user_id NOT IN (SELECT user_id FROM soft_neg_users)
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE soft_neg_excl AS
        SELECT n.user_id FROM soft_neg_users n
        WHERE n.user_id NOT IN (SELECT user_id FROM soft_pos_users)
        """
    )
    np_ = con.execute("SELECT count(*) FROM soft_pos_excl").fetchone()[0]
    nn = con.execute("SELECT count(*) FROM soft_neg_excl").fetchone()[0]
    print(f"  soft users pos_excl={np_:,} neg_excl={nn:,}", flush=True)
    return {"n_pos": np_, "n_neg": nn}


def feature_effects(con) -> dict[str, dict[str, float]]:
    """Cohen-ish d: soft_pos - soft_neg on user_rich features."""
    effects = {}
    for c in FEATURE_COLS:
        row = con.execute(
            f"""
            SELECT
                avg(CASE WHEN p.user_id IS NOT NULL THEN ur.{c} END),
                avg(CASE WHEN n.user_id IS NOT NULL THEN ur.{c} END),
                stddev_samp(ur.{c})
            FROM user_rich ur
            LEFT JOIN soft_pos_excl p USING (user_id)
            LEFT JOIN soft_neg_excl n USING (user_id)
            WHERE p.user_id IS NOT NULL OR n.user_id IS NOT NULL
            """
        ).fetchone()
        mp, mn, sd = row
        if mp is None or mn is None or not sd:
            continue
        effects[c] = {
            "pos_mean": float(mp),
            "neg_mean": float(mn),
            "d": (float(mp) - float(mn)) / float(sd),
        }
    return effects


def nudge_weights(
    effects: dict[str, dict[str, float]],
    *,
    step: float = STEP,
) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, Any]]:
    """Blend current terms toward effect-aligned directions (small step)."""
    classic = dict(CLASSIC_TERMS)
    anti = dict(ANTI_TERMS)
    normie = dict(NORMIE_TERMS)
    audit = {"updates": []}

    # Map: if pos>neg on feature, classic should weight positive; anti opposite for binge/series
    for feat, classic_coef in list(CLASSIC_TERMS.items()):
        if feat not in effects:
            continue
        d = effects[feat]["d"]
        # target classic coef sign matches d, magnitude soft-capped
        target = max(min(d * 1.2, 2.0), -2.0)
        new = (1 - step) * classic_coef + step * target
        classic[feat] = new
        audit["updates"].append(
            {
                "block": "classic",
                "feature": feat,
                "old": classic_coef,
                "target_from_d": target,
                "d": d,
                "new": new,
            }
        )

    for feat, anti_coef in list(ANTI_TERMS.items()):
        if feat not in effects:
            continue
        d = effects[feat]["d"]
        # anti score should be HIGH for binge users = low for sticky lovers → opposite of d
        target = max(min(-d * 1.2, 2.0), -2.0)
        new = (1 - step) * anti_coef + step * target
        anti[feat] = new
        audit["updates"].append(
            {
                "block": "anti",
                "feature": feat,
                "old": anti_coef,
                "target_from_d": target,
                "d": d,
                "new": new,
            }
        )

    # Normie block: nudge mega/logn using effects if sticky lovers lower than binge
    # Keep milder — binge negs aren't pure normie
    for feat, coef in list(NORMIE_TERMS.items()):
        if feat not in effects:
            continue
        d = effects[feat]["d"]
        # only gently adjust features already in normie block
        target = max(min(-d * 0.8, 1.8), -1.8)
        new = (1 - step * 0.6) * coef + (step * 0.6) * target
        normie[feat] = new
        audit["updates"].append(
            {
                "block": "normie",
                "feature": feat,
                "old": coef,
                "target_from_d": target,
                "d": d,
                "new": new,
            }
        )

    return classic, anti, normie, audit


def gate_nudge(con) -> dict[str, float]:
    """Slightly tighten gates toward soft-pos percentiles (cautious)."""
    row = con.execute(
        """
        SELECT
            approx_quantile(series_share_5, 0.85::FLOAT),
            approx_quantile(mega_catalog_share_5, 0.85::FLOAT),
            approx_quantile(binge_mean_5, 0.85::FLOAT),
            approx_quantile(midpop_span_per_logn5, 0.20::FLOAT)
        FROM user_rich ur
        JOIN soft_pos_excl p USING (user_id)
        """
    ).fetchone()
    # Blend current gates with pos percentiles
    cur = {"series": 0.40, "mega": 0.28, "binge": 2.8, "span": 3.0}
    sug = {
        "series": float(row[0] or cur["series"]),
        "mega": float(row[1] or cur["mega"]),
        "binge": float(row[2] or cur["binge"]),
        "span": float(row[3] or cur["span"]),
    }
    # only tighten (series/mega/binge down, span up), small step
    out = {
        "series_gate": min(cur["series"], (1 - STEP) * cur["series"] + STEP * sug["series"]),
        "mega_gate": min(cur["mega"], (1 - STEP) * cur["mega"] + STEP * sug["mega"]),
        "binge_gate": min(cur["binge"], (1 - STEP) * cur["binge"] + STEP * sug["binge"]),
        "span_gate": max(cur["span"], (1 - STEP) * cur["span"] + STEP * sug["span"]),
    }
    return {"current": cur, "soft_pos_pct": sug, "applied": out}


def short_stability_ev(
    con,
    ev,
    gated: list[tuple[int, float]],
    anti: list[tuple[int, float]],
    base_top50: set[str],
    base_top200: set[str],
    sticky_ids: set[str],
    *,
    n_boot: int = N_BOOT,
) -> dict[str, Any]:
    rng = random.Random(SEED)
    j50s, j200s = [], []
    presence50: Counter[str] = Counter()
    metrics = []
    sticky_rates = []
    for _b in range(n_boot):
        focus_u, anti_u = bootstrap_pools(gated, anti, rng=rng, frac=TOP_FRAC)
        rows = contrastive_rank_from_user_lists(con, focus_u, anti_u)
        t50, t200 = top_ids(rows, 50), top_ids(rows, 200)
        j50s.append(jaccard(base_top50, t50))
        j200s.append(jaccard(base_top200, t200))
        for wid in t50:
            presence50[wid] += 1
        met = evaluate(rows, ev)
        metrics.append(met)
        sticky_in = sum(1 for w in sticky_ids if w in t50)
        sticky_rates.append(sticky_in / max(len(sticky_ids), 1))

    def mean_sd(xs: list[float]) -> tuple[float, float]:
        mu = sum(xs) / len(xs)
        sd = (sum((x - mu) ** 2 for x in xs) / max(len(xs) - 1, 1)) ** 0.5
        return mu, sd

    j50_mu, j50_sd = mean_sd(j50s)
    j200_mu, j200_sd = mean_sd(j200s)
    q_mu, q_sd = mean_sd([m["Q"] for m in metrics])
    anti_mu, anti_sd = mean_sd([float(m["anti50"]) for m in metrics])
    sticky_mu, sticky_sd = mean_sd(sticky_rates)
    sticky_still = []
    for wid in sticky_ids:
        sticky_still.append({"work_id": wid, "top50_rate": presence50[wid] / n_boot})
    n_sticky_ok = sum(1 for s in sticky_still if s["top50_rate"] >= 0.7)
    return {
        "j50_mean": j50_mu,
        "j50_sd": j50_sd,
        "j200_mean": j200_mu,
        "j200_sd": j200_sd,
        "Q_mean": q_mu,
        "Q_sd": q_sd,
        "anti50_mean": anti_mu,
        "anti50_sd": anti_sd,
        "sticky_fraction_in_top50_mean": sticky_mu,
        "sticky_fraction_in_top50_sd": sticky_sd,
        "n_sticky_still_ge_70pct": n_sticky_ok,
        "n_sticky": len(sticky_ids),
    }


def veto(
    before: dict[str, Any],
    after: dict[str, Any],
    before_eval: dict[str, Any],
    after_eval: dict[str, Any],
) -> dict[str, Any]:
    """Accept only if junk stays out and stability doesn't worsen much."""
    reasons = []
    ok = True
    if after_eval["anti50"] > 1:
        ok = False
        reasons.append(f"anti50 rose to {after_eval['anti50']}")
    if after["anti50_mean"] > 0.5:
        ok = False
        reasons.append(f"boot anti50_mean={after['anti50_mean']:.2f}")
    if after["j50_mean"] < before["j50_mean"] - 0.04:
        ok = False
        reasons.append(
            f"J50 stability dropped {before['j50_mean']:.2f} → {after['j50_mean']:.2f}"
        )
    if after["n_sticky_still_ge_70pct"] < before["n_sticky_still_ge_70pct"] - 2:
        ok = False
        reasons.append(
            f"sticky retention {before['n_sticky_still_ge_70pct']} → "
            f"{after['n_sticky_still_ge_70pct']}"
        )
    # soft preference: don't require Q up (piles fallible)
    if ok:
        reasons.append("passed: anti controlled + stability not worsened materially")
    return {"accepted": ok, "reasons": reasons}


def main() -> None:
    t_all = time.time()

    def lap(label: str, t0: float) -> float:
        dt = time.time() - t0
        print(f"  [timing] {label}: {dt:.1f}s (total {time.time()-t_all:.1f}s)", flush=True)
        return time.time()

    con = _con()
    ev = load_eval_sets(con)
    print("Preparing base tables…", flush=True)
    t = time.time()
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    label_cohorts(con)
    moments = _moments(con)
    t = lap("setup/materialize", t)

    sticky_ids = load_sticky_ids()
    print(f"Sticky positives: {len(sticky_ids)}", flush=True)

    # --- Baseline affinity + rank + short stability ---
    print("\n=== baseline ===", flush=True)
    build_affinity(
        con,
        moments,
        classic_terms=CLASSIC_TERMS,
        anti_terms=ANTI_TERMS,
        normie_terms=NORMIE_TERMS,
    )
    neg_ids = soft_negative_works(con)
    print(f"Soft negatives (series binge favorites): {len(neg_ids)}", flush=True)
    # titles for report
    neg_titles = []
    for wid in neg_ids[:12]:
        row = con.execute(
            "SELECT title, author FROM ex.work_scores WHERE work_id=?", [wid]
        ).fetchone()
        if row:
            neg_titles.append({"work_id": wid, "title": row[0], "author": row[1]})

    sticky_titles = []
    for wid in sticky_ids:
        row = con.execute(
            "SELECT title, author FROM ex.work_scores WHERE work_id=?", [wid]
        ).fetchone()
        if row:
            sticky_titles.append({"work_id": wid, "title": row[0], "author": row[1]})

    soft_counts = label_soft_users(con, sticky_ids, neg_ids)
    effects = feature_effects(con)
    print("  top effects (pos - neg):", flush=True)
    for feat, e in sorted(effects.items(), key=lambda kv: -abs(kv[1]["d"]))[:10]:
        print(f"    {feat:28s} d={e['d']:+.2f}", flush=True)

    gated0, anti0 = load_pools(con)
    focus0 = pick_top_frac(gated0, TOP_FRAC)
    anti_u0 = pick_top_frac(anti0, TOP_FRAC)
    base_rows = contrastive_rank_from_user_lists(con, focus0, anti_u0)
    base_eval = evaluate(base_rows, ev)
    base_fill = filler_eval(base_rows, con)
    base_top50 = top_ids(base_rows, 50)
    base_top200 = top_ids(base_rows, 200)
    print(
        f"  baseline Q={base_eval['Q']:.1f} pos50={base_eval['pos50']} "
        f"anti50={base_eval['anti50']}",
        flush=True,
    )
    t = lap("baseline rank + soft labels", t)
    print("  short stability (baseline)…", flush=True)
    base_stab = short_stability_ev(
        con, ev, gated0, anti0, base_top50, base_top200, set(sticky_ids)
    )
    print(
        f"  J50={base_stab['j50_mean']:.2f} sticky70={base_stab['n_sticky_still_ge_70pct']}/"
        f"{base_stab['n_sticky']} anti_boot={base_stab['anti50_mean']:.2f}",
        flush=True,
    )
    t = lap(f"baseline stability ({N_BOOT} boots)", t)

    # --- Nudge ---
    print("\n=== co-training nudge ===", flush=True)
    classic_n, anti_n, normie_n, audit = nudge_weights(effects, step=STEP)
    gates = gate_nudge(con)
    print(f"  gates applied: {gates['applied']}", flush=True)
    build_affinity(
        con,
        moments,
        classic_terms=classic_n,
        anti_terms=anti_n,
        normie_terms=normie_n,
        series_gate=gates["applied"]["series_gate"],
        mega_gate=gates["applied"]["mega_gate"],
        binge_gate=gates["applied"]["binge_gate"],
        span_gate=gates["applied"]["span_gate"],
    )
    gated1, anti1 = load_pools(con)
    focus1 = pick_top_frac(gated1, TOP_FRAC)
    anti_u1 = pick_top_frac(anti1, TOP_FRAC)
    new_rows = contrastive_rank_from_user_lists(con, focus1, anti_u1)
    new_eval = evaluate(new_rows, ev)
    new_fill = filler_eval(new_rows, con)
    new_top50 = top_ids(new_rows, 50)
    print(
        f"  cotrained Q={new_eval['Q']:.1f} pos50={new_eval['pos50']} "
        f"anti50={new_eval['anti50']} overlap50={jaccard(base_top50, new_top50):.2f}",
        flush=True,
    )
    t = lap("nudge + re-rank", t)
    print("  short stability (cotrained)…", flush=True)
    # Stability vs *cotrained* baseline top (geometry of new method)
    new_stab = short_stability_ev(
        con, ev, gated1, anti1, new_top50, top_ids(new_rows, 200), set(sticky_ids)
    )
    print(
        f"  J50={new_stab['j50_mean']:.2f} sticky70={new_stab['n_sticky_still_ge_70pct']}/"
        f"{new_stab['n_sticky']} anti_boot={new_stab['anti50_mean']:.2f}",
        flush=True,
    )
    t = lap(f"cotrained stability ({N_BOOT} boots)", t)

    decision = veto(base_stab, new_stab, base_eval, new_eval)
    # Also compare cotrained stability to baseline stability (fair veto)
    # Recompute: is new method's self-J50 at least almost as good as old self-J50?
    print(f"  veto accepted={decision['accepted']}: {decision['reasons']}", flush=True)

    results = {
        "meta": {
            "step": STEP,
            "sticky_n": len(sticky_ids),
            "soft_neg_n": len(neg_ids),
            "n_boot_veto": N_BOOT,
        },
        "sticky_titles": sticky_titles,
        "soft_neg_titles": neg_titles,
        "soft_user_counts": soft_counts,
        "feature_effects_pos_minus_neg": effects,
        "weight_audit": audit,
        "gates": gates,
        "baseline": {
            "eval": base_eval,
            "fill": base_fill,
            "stability": base_stab,
            "top15": [
                {"rank": r["rank"], "title": r["title"], "author": r["author"]}
                for r in base_rows[:15]
            ],
        },
        "cotrained": {
            "eval": new_eval,
            "fill": new_fill,
            "stability": new_stab,
            "overlap_top50_with_baseline": jaccard(base_top50, new_top50),
            "classic_terms": classic_n,
            "anti_terms": anti_n,
            "normie_terms": normie_n,
            "top15": [
                {"rank": r["rank"], "title": r["title"], "author": r["author"]}
                for r in new_rows[:15]
            ],
        },
        "veto": decision,
        "adopted_weights": decision["accepted"],
    }

    # If accepted, write adopted weights file for later use
    if decision["accepted"]:
        adopt_path = Path(__file__).resolve().parents[1] / "data" / "cotrained_weights.json"
        adopt_path.write_text(
            json.dumps(
                {
                    "classic_terms": classic_n,
                    "anti_terms": anti_n,
                    "normie_terms": normie_n,
                    "gates": gates["applied"],
                    "lambda_anti": 0.85,
                    "lambda_normie": 0.75,
                    "top_frac": TOP_FRAC,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        results["adopted_weights_path"] = str(adopt_path)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    _write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    con.close()


def _write_report(results: dict[str, Any]) -> None:
    v = results["veto"]
    b, c = results["baseline"], results["cotrained"]
    lines = [
        "# Cautious co-training report",
        "",
        "## Plan (plain English)",
        "",
        "1. Soft positives = **sticky** books from stability (≥80% of boots in top 50).",
        "2. Soft negatives = favorites of heavy **series-binge** users.",
        "3. Slightly nudge feature weights so sticky-lovers score higher / binge users lower.",
        "4. Slightly tighten gates toward sticky-lover habits.",
        "5. **Veto:** keep the new recipe only if junk stays out and stability doesn’t get worse.",
        "",
        f"## Veto: **{'ACCEPTED' if v['accepted'] else 'REJECTED'}**",
        "",
    ]
    for r in v["reasons"]:
        lines.append(f"- {r}")

    lines += [
        "",
        "## Soft labels used",
        "",
        f"Sticky positives ({len(results['sticky_titles'])}):",
        "",
    ]
    for t in results["sticky_titles"][:15]:
        lines.append(f"- {t['title']} — {t['author']}")
    if len(results["sticky_titles"]) > 15:
        lines.append(f"- … +{len(results['sticky_titles'])-15} more")
    lines += ["", "Soft-negative examples (series binge favorites):", ""]
    for t in results["soft_neg_titles"][:10]:
        lines.append(f"- {t['title']} — {t['author']}")

    lines += [
        "",
        "## Before vs after",
        "",
        "| | baseline | co-trained |",
        "|---|---:|---:|",
        f"| Q | {b['eval']['Q']:.1f} | {c['eval']['Q']:.1f} |",
        f"| pos50 | {b['eval']['pos50']} | {c['eval']['pos50']} |",
        f"| anti50 | {b['eval']['anti50']} | {c['eval']['anti50']} |",
        f"| classic50 | {b['fill']['classic50']} | {c['fill']['classic50']} |",
        f"| boot J50 | {b['stability']['j50_mean']:.2f} | {c['stability']['j50_mean']:.2f} |",
        f"| sticky still ≥70% boots | {b['stability']['n_sticky_still_ge_70pct']}/{b['stability']['n_sticky']} | {c['stability']['n_sticky_still_ge_70pct']}/{c['stability']['n_sticky']} |",
        f"| boot anti50 | {b['stability']['anti50_mean']:.2f} | {c['stability']['anti50_mean']:.2f} |",
        f"| overlap top50 | 1.00 | {c['overlap_top50_with_baseline']:.2f} |",
        "",
        "### Baseline top 10",
        "",
    ]
    for r in b["top15"][:10]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")
    lines += ["", "### Co-trained top 10", ""]
    for r in c["top15"][:10]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")

    lines += [
        "",
        "## Biggest weight nudges",
        "",
    ]
    ups = sorted(
        results["weight_audit"]["updates"],
        key=lambda u: -abs(u["new"] - u["old"]),
    )
    for u in ups[:12]:
        lines.append(
            f"- `{u['block']}.{u['feature']}`: {u['old']:+.2f} → {u['new']:+.2f} "
            f"(effect d={u['d']:+.2f})"
        )

    lines += [
        "",
        f"Gates: {results['gates']['applied']}",
        "",
        "## What this means next",
        "",
    ]
    if v["accepted"]:
        lines.append(
            "Adopted weights saved to `cotrained_weights.json`. "
            "Next: optional second tiny step, or candidate-feature search if we plateau."
        )
    else:
        lines.append(
            "Kept the **baseline** recipe. Co-training signal wasn’t clean enough "
            "under the veto — try smaller STEP, stricter soft labels, or new features."
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

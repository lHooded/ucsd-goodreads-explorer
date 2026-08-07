#!/usr/bin/env python3
"""Accurate Pareto after com-cap-at-zero fix; sweep relevant affectors.

Writes/updates:
  ucsd_explorer/data/pareto_post_fix.json
  ucsd_explorer/data/PARETO_POST_FIX_REPORT.md
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from ucsd_explorer.db import get_con
from ucsd_explorer.ranking import (
    _curator_user_weight_sql,
    rank_books,
    resolve_deep_com_share_cap,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "pareto_post_fix.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "PARETO_POST_FIX_REPORT.md"

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


def _base(**kw: Any) -> dict[str, Any]:
    p = {
        "method": "curator_deep_pct_love",
        "min_votes": 25,
        "max_n": 0,
        "bayesian_m": 30,
        "limit": 400,
        "curator_strictness": 0,
        "curator_strictness_mode": "deweight",
        "curator_deweight": 25,
        "normie_depth": 40,
        "normie_purity": 55,
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


def _ranks(results: list[dict]) -> dict[str, int | None]:
    out: dict[str, int | None] = {t: None for t in GOOD + BAD}
    for r in results:
        title = (r.get("title") or "").lower()
        for t in out:
            if out[t] is None and t.lower() in title:
                out[t] = int(r["rank"])
    return out


def _quality(ranks: dict[str, int | None]) -> dict[str, Any]:
    def band(keys: list[str]) -> dict[str, Any]:
        vals = [ranks[k] for k in keys if ranks.get(k) is not None]
        if not vals:
            return {"n_found": 0, "median": None, "top50": 0, "top100": 0, "top200": 0}
        vals_s = sorted(vals)
        return {
            "n_found": len(vals),
            "median": vals_s[len(vals_s) // 2],
            "top50": sum(1 for v in vals if v <= 50),
            "top100": sum(1 for v in vals if v <= 100),
            "top200": sum(1 for v in vals if v <= 200),
        }

    g, b = band(GOOD), band(BAD)
    bad_vals = [ranks[k] if ranks.get(k) is not None else 999 for k in BAD]
    good_vals = [ranks[k] for k in GOOD if ranks.get(k) is not None]
    q = 0.0
    if good_vals:
        q += 2.0 * sum(1 for v in good_vals if v <= 50)
        q += 1.0 * sum(1 for v in good_vals if 50 < v <= 100)
        q -= 3.0 * sum(1 for v in bad_vals if v <= 50)
        q -= 2.0 * sum(1 for v in bad_vals if 50 < v <= 100)
        q -= 0.5 * sum(1 for v in bad_vals if 100 < v <= 200)
        q += sorted(bad_vals)[len(bad_vals) // 2] / 80.0
        q -= sorted(good_vals)[len(good_vals) // 2] / 100.0
    return {"score": q, "good": g, "bad": b}


def _mass(results: list[dict], top_k: int = 100) -> dict[str, float]:
    rows = results[:top_k]
    if not rows:
        return {"median_n": 0.0, "mean_n": 0.0, "geo_n": 0.0}
    ns = [max(1.0, float(r.get("n") or 1)) for r in rows]
    ns_s = sorted(ns)
    return {
        "median_n": float(ns_s[len(ns_s) // 2]),
        "mean_n": sum(ns) / len(ns),
        "geo_n": math.exp(sum(math.log(x) for x in ns) / len(ns)),
    }


def run(label: str, **kw: Any) -> dict[str, Any]:
    t0 = time.time()
    params = _base(**kw)
    data = rank_books(params)
    results = data.get("results") or []
    ranks = _ranks(results)
    return {
        "label": label,
        "params": {
            k: params.get(k)
            for k in (
                "normie_depth",
                "normie_purity",
                "curator_strictness",
                "curator_deweight",
                "coverage_weight",
                "min_votes",
                "max_n",
                "bayesian_m",
                "com_share_cap",
            )
        },
        "quality": _quality(ranks),
        "voter_mass": _mass(results),
        "ranks": ranks,
        "top10": [
            {"rank": r["rank"], "n": r["n"], "title": (r["title"] or "")[:50]}
            for r in results[:10]
        ],
        "deep_com_share_cap": data.get("deep_com_share_cap"),
        "elapsed_s": round(time.time() - t0, 2),
    }


def verify_zero_fix() -> dict[str, Any]:
    con = get_con()
    cases = []
    for label, depth, purity, com_cap in [
        ("all_query_zero", 0, 0, None),
        ("purity55", 0, 55, None),
        ("explicit_com_0.11", 0, 0, 0.11),
        ("d40_p55", 40, 55, None),
        ("d40_p0", 40, 0, None),
    ]:
        we, gate, args, _ = _curator_user_weight_sql(
            pct=True,
            mode="deweight",
            strictness=0,
            deep=True,
            normie_depth=depth,
            normie_purity=purity,
            com_share_cap=com_cap,
        )
        n = int(
            con.execute(
                f"SELECT count(*) FROM user_curator_deep_weight c WHERE TRUE {gate}",
                args,
            ).fetchone()[0]
        )
        resolved = resolve_deep_com_share_cap(
            normie_purity=purity, com_share_cap=com_cap
        )
        cases.append(
            {
                "label": label,
                "n": n,
                "resolved_com_cap": resolved,
                "gate_has_com": "com_hits" in gate and "<=" in gate,
            }
        )
    n_mint = int(con.execute("SELECT count(*) FROM user_curator_deep_weight").fetchone()[0])
    n_pct = int(con.execute("SELECT count(*) FROM user_star_percentiles").fetchone()[0])
    return {
        "n_mint": n_mint,
        "n_percentile_users": n_pct,
        "cases": cases,
        "note": (
            "all_query_zero: no taste gates / com_cap (resolved_com_cap=None). "
            "Ranking uses equal weight over all percentile users (~n_percentile_users); "
            "mint gate count above is only the mint table size for comparison. "
            "Raising depth/purity/deweight switches to mint_deep scoring."
        ),
    }


def annotate_pareto(runs: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in runs if "quality" in r and "voter_mass" in r]
    qs = [r["quality"]["score"] for r in valid]
    vs = [math.log(max(r["voter_mass"]["geo_n"], 1)) for r in valid]
    qmin, qmax = min(qs), max(qs)
    vmin, vmax = min(vs), max(vs)

    def nq(q: float) -> float:
        return (q - qmin) / (qmax - qmin + 1e-9)

    def nv(geo: float) -> float:
        return (math.log(max(geo, 1)) - vmin) / (vmax - vmin + 1e-9)

    for r in valid:
        r["q_norm"] = nq(r["quality"]["score"])
        r["v_norm"] = nv(r["voter_mass"]["geo_n"])
        r["dist_utopia"] = math.hypot(1 - r["q_norm"], 1 - r["v_norm"])
        r["qv_product"] = r["q_norm"] * r["v_norm"]
        r["qv_quality_lean"] = 0.65 * r["q_norm"] + 0.35 * r["v_norm"]

    front = []
    for g in valid:
        dominated = any(
            (h["quality"]["score"] >= g["quality"]["score"]
             and h["voter_mass"]["geo_n"] >= g["voter_mass"]["geo_n"])
            and (
                h["quality"]["score"] > g["quality"]["score"]
                or h["voter_mass"]["geo_n"] > g["voter_mass"]["geo_n"]
            )
            for h in valid
            if h is not g
        )
        if not dominated:
            front.append(g["label"])

    def pick(key: str, reverse: bool = False) -> dict[str, Any]:
        return (max if reverse else min)(valid, key=lambda r: r[key])

    return {
        "n": len(valid),
        "pareto_front": front,
        "best_utopia": pick("dist_utopia"),
        "best_product": pick("qv_product", reverse=True),
        "best_quality_lean": pick("qv_quality_lean", reverse=True),
        "best_quality": max(valid, key=lambda r: r["quality"]["score"]),
        "best_mass": max(valid, key=lambda r: r["voter_mass"]["geo_n"]),
        "runs": valid,
    }


def main() -> None:
    get_con()
    print("Verify zero-fix…", flush=True)
    zero = verify_zero_fix()
    for c in zero["cases"]:
        print(f"  {c['label']}: n={c['n']} com_cap={c['resolved_com_cap']}", flush=True)

    runs: list[dict[str, Any]] = []

    print("Core depth×purity×strictness (deweight=25)…", flush=True)
    for d in (0, 25, 40, 60):
        for p in (0, 35, 55, 75):
            for s in (0, 40, 80):
                label = f"core_d{d}_p{p}_s{s}"
                print(f"  {label}", flush=True)
                runs.append(
                    run(
                        label,
                        normie_depth=d,
                        normie_purity=p,
                        curator_strictness=s,
                        curator_deweight=25,
                    )
                )

    base = {
        "normie_depth": 40,
        "normie_purity": 55,
        "curator_strictness": 0,
        "curator_deweight": 25,
        "coverage_weight": 0.0,
        "min_votes": 25,
        "max_n": 0,
        "bayesian_m": 30,
    }

    print("Axis: curator_deweight (d40/p55/s0)…", flush=True)
    for dw in (0, 15, 25, 40, 60, 80, 100):
        runs.append(run(f"dew_{dw}", **{**base, "curator_deweight": dw}))

    print("Axis: deweight at all taste-zero…", flush=True)
    for dw in (0, 25, 50, 100):
        runs.append(
            run(
                f"zerotaste_dew_{dw}",
                normie_depth=0,
                normie_purity=0,
                curator_strictness=0,
                curator_deweight=dw,
            )
        )

    print("Axis: min_votes…", flush=True)
    for mv in (15, 25, 40, 60, 100):
        runs.append(run(f"minv_{mv}", **{**base, "min_votes": mv}))

    print("Axis: max_n (popularity ceiling)…", flush=True)
    for mx in (0, 1500, 3000, 5000, 8000, 12000, 20000):
        runs.append(run(f"maxn_{mx}", **{**base, "max_n": mx}))

    print("Axis: bayesian_m…", flush=True)
    for m in (5, 15, 30, 50, 80, 120):
        runs.append(run(f"m_{m}", **{**base, "bayesian_m": m}))

    print("Axis: coverage…", flush=True)
    for cov in (0.0, 0.25, 0.5, 0.75, 1.0):
        runs.append(run(f"cov_{int(cov*100)}", **{**base, "coverage_weight": cov}))

    print("Axis: explicit com_share_cap (purity=0 so only explicit)…", flush=True)
    for cap in (None, 0.08, 0.11, 0.15, 0.20):
        kw = {**base, "normie_purity": 0, "normie_depth": 40}
        if cap is None:
            runs.append(run("com_off_d40", **kw))
        else:
            runs.append(run(f"com_{cap}", **{**kw, "com_share_cap": cap}))

    print("Axis: purity with depth fixed 40, strict 0…", flush=True)
    for p in (0, 20, 35, 45, 55, 65, 75, 90):
        runs.append(
            run(
                f"pur_axis_{p}",
                normie_depth=40,
                normie_purity=p,
                curator_strictness=0,
                curator_deweight=25,
            )
        )

    print("Annotate Pareto…", flush=True)
    # Separate analyses
    core = annotate_pareto([r for r in runs if r["label"].startswith("core_")])
    all_ann = annotate_pareto(runs)
    maxn_ann = annotate_pareto([r for r in runs if r["label"].startswith("maxn_")])
    minv_ann = annotate_pareto([r for r in runs if r["label"].startswith("minv_")])
    m_ann = annotate_pareto([r for r in runs if r["label"].startswith("m_")])
    cov_ann = annotate_pareto([r for r in runs if r["label"].startswith("cov_")])
    com_ann = annotate_pareto(
        [r for r in runs if r["label"].startswith("com_") or r["label"] == "com_off_d40"]
    )
    pur_ann = annotate_pareto([r for r in runs if r["label"].startswith("pur_axis_")])
    dew_ann = annotate_pareto([r for r in runs if r["label"].startswith("dew_")])
    dew0_ann = annotate_pareto([r for r in runs if r["label"].startswith("zerotaste_dew_")])

    payload = {
        "zero_fix_verification": zero,
        "notes": [
            "max_n=0 means no ceiling (keep). Nonzero max_n caps Kish n_eff / votes.",
            "Sliders at 0 → equal weight over all percentile users (not mint-only).",
            "curator_deweight preferred over gate/equal-elite; core grid uses deweight=25 (expo=1).",
            "Early SF/catalog work filter keeps all-zero rankings ~1s.",
            "Keep max_n in simplified rebuild as a first-class control.",
        ],
        "core_pareto": _slim(core),
        "all_runs_pareto": _slim(all_ann),
        "axis_max_n": _slim(maxn_ann),
        "axis_min_votes": _slim(minv_ann),
        "axis_bayesian_m": _slim(m_ann),
        "axis_coverage": _slim(cov_ann),
        "axis_com_cap": _slim(com_ann),
        "axis_purity": _slim(pur_ann),
        "axis_deweight": _slim(dew_ann),
        "axis_deweight_taste_zero": _slim(dew0_ann),
        "runs": runs,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    write_md(payload)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")


def _slim(block: dict[str, Any]) -> dict[str, Any]:
    def brief(r: dict[str, Any] | None) -> dict[str, Any] | None:
        if not r:
            return None
        return {
            "label": r["label"],
            "quality": r["quality"]["score"],
            "geo_n": r["voter_mass"]["geo_n"],
            "median_n": r["voter_mass"]["median_n"],
            "good_med": r["quality"]["good"]["median"],
            "bad_med": r["quality"]["bad"]["median"],
            "good_top50": r["quality"]["good"]["top50"],
            "bad_top100": r["quality"]["bad"]["top100"],
            "params": r.get("params"),
            "dist_utopia": r.get("dist_utopia"),
            "qv_product": r.get("qv_product"),
        }

    return {
        "n": block["n"],
        "pareto_front": block["pareto_front"],
        "best_utopia": brief(block["best_utopia"]),
        "best_product": brief(block["best_product"]),
        "best_quality_lean": brief(block["best_quality_lean"]),
        "best_quality": brief(block["best_quality"]),
        "best_mass": brief(block["best_mass"]),
        "runs_brief": [brief(r) for r in block["runs"]],
    }


def write_md(payload: dict[str, Any]) -> None:
    z = payload["zero_fix_verification"]
    lines = [
        "# Pareto after slider zero-fix\n",
        "## Zero-fix verification\n",
        z["note"],
        "",
        "| Case | cohort n | resolved com_cap | gate has com |",
        "|---|---:|---:|---|",
    ]
    for c in z["cases"]:
        lines.append(
            f"| {c['label']} | {c['n']} | {c['resolved_com_cap']} | {c['gate_has_com']} |"
        )
    lines.append(f"\nMint table size: **{z['n_mint']:,}**")
    if z.get("n_percentile_users") is not None:
        lines.append(
            f"\nPercentile users (all-zero cohort): **{z['n_percentile_users']:,}**\n"
        )
    else:
        lines.append("")

    def section(title: str, key: str) -> None:
        b = payload[key]
        lines.append(f"## {title}\n")
        lines.append(
            f"Runs: {b['n']}. Pareto front: "
            + ", ".join(f"`{x}`" for x in b["pareto_front"][:24])
        )
        if len(b["pareto_front"]) > 24:
            lines.append(f" … +{len(b['pareto_front'])-24} more")
        lines.append("")
        for name, k in [
            ("Utopia knee", "best_utopia"),
            ("Product", "best_product"),
            ("Quality-lean", "best_quality_lean"),
            ("Best quality", "best_quality"),
            ("Best mass", "best_mass"),
        ]:
            r = b[k]
            lines.append(
                f"- **{name}:** `{r['label']}` Q={r['quality']:.2f} geo_n={r['geo_n']:.0f} "
                f"good_med={r['good_med']} bad_med={r['bad_med']} "
                f"params={r['params']}"
            )
        lines.append("")
        lines.append("| label | Q | geo_n | med_n | good_med | bad_med |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for r in sorted(b["runs_brief"], key=lambda x: -x["quality"])[:20]:
            lines.append(
                f"| {r['label']} | {r['quality']:.2f} | {r['geo_n']:.0f} | "
                f"{r['median_n']:.0f} | {r['good_med']} | {r['bad_med']} |"
            )
        lines.append("")

    section("Core grid (depth × purity × strictness, deweight=25)", "core_pareto")
    section("curator_deweight axis (d40/p55/s0)", "axis_deweight")
    section("deweight at taste-zero (d0/p0/s0)", "axis_deweight_taste_zero")
    section("max_n axis (from d40/p55/s0/cov0)", "axis_max_n")
    section("min_votes axis", "axis_min_votes")
    section("bayesian_m axis", "axis_bayesian_m")
    section("coverage axis", "axis_coverage")
    section("explicit com_cap axis (depth40, purity0)", "axis_com_cap")
    section("purity axis (depth40)", "axis_purity")

    lines.append("## Implications for simplified rebuild\n")
    lines.append(
        "- **Keep `max_n`** (max ratings / Kish ceiling): it is a strong obscure-vs-popular lever; "
        "`0` = off."
    )
    lines.append(
        "- Query **purity=0 ⇒ com cap off** (fixed). Sliders at 0 ⇒ equal weight over all "
        "percentile users (not mint-only)."
    )
    lines.append(
        "- Prefer **weighted curator scores** (`curator_deweight`) over equal-elite gate mode; "
        "core defaults use deweight=25 (expo=1)."
    )
    lines.append(
        "- Prefer utopia/quality-lean picks from core grid as UI defaults; expose max_n + min_votes + m + deweight."
    )
    lines.append(
        "- Coverage=0 remains preferred for obscure literary discovery unless mass metrics demand otherwise."
    )
    lines.append("")
    lines.append("Full data: `pareto_post_fix.json`.\n")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

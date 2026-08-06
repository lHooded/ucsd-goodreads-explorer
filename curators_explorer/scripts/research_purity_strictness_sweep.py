#!/usr/bin/env python3
"""Sweep purity × curator-strictness for quality vs quantity on the deep pool.

Purity: deep_share floor + com_share cap (same mapping as curators_explorer.cohort).
Strictness: elite top-K keep among purity passers (legacy curator_strictness /
log-linear keep toward ~100 at 100).

Quantity = Kish n_eff (stored weights) + raw n_jury.
Quality = within-jury pairwise probes (poll-contaminated — interpret cautiously)
         + Q_clean / anti / filler / sticky.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_purity_strictness_sweep
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from curators_explorer.cohort import com_share_cap, purity_gate_sql, purity_min_share
from curators_explorer.scripts.research_deep_size_sweep import build_pairs, rank_pairwise
from curators_explorer.scripts.research_ratings_only_canon import (
    _con,
    load_eval_sets,
    materialize_base,
)
from curators_explorer.scripts.research_residual_enthusiasm import (
    author_disjoint_sets,
    heldout_recall,
    load_sticky,
    probe_metrics,
    top15,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "purity_strictness_sweep.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "PURITY_STRICTNESS_SWEEP_REPORT.md"

ELITE_FLOOR = 100.0
PURITIES = [0, 35, 45, 55, 65, 75, 90]
STRICTNESSES = [0, 15, 25, 40, 55, 70, 85]


def elite_keep_sql(strictness: float, n_pass_expr: str = "n_pass") -> str:
    t = max(0.0, min(100.0, float(strictness))) / 100.0
    if t <= 1e-12:
        return n_pass_expr
    return (
        f"CAST(ceil(power(greatest({n_pass_expr}, 1)::DOUBLE, {1.0 - t}) "
        f"* power(least({ELITE_FLOOR}::DOUBLE, "
        f"greatest({n_pass_expr}, 1)::DOUBLE), {t})) AS BIGINT)"
    )


def gate_readout(purity: float, strictness: float) -> dict[str, Any]:
    return {
        "purity": purity,
        "strictness": strictness,
        "min_deep_share": purity_min_share(purity),
        "com_share_cap": com_share_cap(purity),
    }


def make_jury(con, *, purity: float, strictness: float, name: str = "jury_ps") -> dict[str, Any]:
    gate_sql, gate_args = purity_gate_sql(purity, alias="c")
    keep = elite_keep_sql(strictness, "n_pass")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {name} AS
        WITH passers AS (
            SELECT
                c.user_id,
                c.curator_pct_weight AS w,
                c.deep_share,
                c.com_share,
                c.n_deep,
                row_number() OVER (ORDER BY c.curator_pct_weight DESC) AS elite_rank,
                count(*) OVER () AS n_pass
            FROM ex.user_curator_deep_weight c
            WHERE TRUE
            {gate_sql}
        )
        SELECT user_id, w, deep_share, com_share, n_deep, n_pass, elite_rank
        FROM passers
        WHERE elite_rank <= {keep}
        """,
        gate_args,
    )
    row = con.execute(
        f"""
        SELECT
            count(*)::BIGINT,
            coalesce(sum(w), 0)::DOUBLE,
            (sum(w)*sum(w))/nullif(sum(w*w), 0)::DOUBLE,
            avg(deep_share), avg(com_share), avg(n_deep),
            max(n_pass)
        FROM {name}
        """
    ).fetchone()
    return {
        "n_jury": int(row[0]),
        "sum_w": float(row[1] or 0),
        "kish_n_eff": float(row[2] or 0),
        "mean_deep_share": float(row[3] or 0),
        "mean_com_share": float(row[4] or 0),
        "mean_n_deep": float(row[5] or 0),
        "n_pass_purity": int(row[6] or 0),
    }


def pareto_annotate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in runs if r.get("ok")]
    if not valid:
        return {"n_runs": 0, "grid": runs}

    qs = [r["quality"] for r in valid]
    vs = [math.log(max(r["quantity"], 1.0)) for r in valid]
    qmin, qmax = min(qs), max(qs)
    vmin, vmax = min(vs), max(vs)

    def nq(q: float) -> float:
        return (q - qmin) / (qmax - qmin + 1e-9)

    def nv(v: float) -> float:
        lv = math.log(max(v, 1.0))
        return (lv - vmin) / (vmax - vmin + 1e-9)

    for r in valid:
        r["q_norm"] = nq(r["quality"])
        r["v_norm"] = nv(r["quantity"])
        r["dist_utopia"] = math.hypot(1 - r["q_norm"], 1 - r["v_norm"])
        r["qv_product"] = r["q_norm"] * r["v_norm"]
        r["qv_quality_lean"] = 0.65 * r["q_norm"] + 0.35 * r["v_norm"]
        r["qv_balanced"] = 0.5 * r["q_norm"] + 0.5 * r["v_norm"]

    front = []
    for g in valid:
        dominated = False
        for h in valid:
            if h is g:
                continue
            if (h["quality"] >= g["quality"] and h["quantity"] >= g["quantity"]) and (
                h["quality"] > g["quality"] or h["quantity"] > g["quantity"]
            ):
                dominated = True
                break
        if not dominated:
            front.append(g["label"])

    def pick(key: str, *, reverse: bool = False):
        return (max if reverse else min)(valid, key=lambda r: r[key])

    return {
        "n_runs": len(valid),
        "pareto_front_labels": front,
        "best_utopia_knee": pick("dist_utopia"),
        "best_product": pick("qv_product", reverse=True),
        "best_quality_lean": pick("qv_quality_lean", reverse=True),
        "best_balanced": pick("qv_balanced", reverse=True),
        "best_quality": pick("quality", reverse=True),
        "best_quantity": pick("quantity", reverse=True),
    }


def _slim(r: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "label",
        "purity",
        "strictness",
        "n_jury",
        "kish_n_eff",
        "n_pass_purity",
        "quality",
        "quantity",
        "q_norm",
        "v_norm",
        "dist_utopia",
        "qv_product",
        "qv_quality_lean",
        "probe",
        "heldout",
        "gates",
        "top8",
    ]
    return {k: r[k] for k in keys if k in r}


def write_report(results: dict[str, Any]) -> None:
    runs = [r for r in results["runs"] if r.get("ok")]
    pareto = results["pareto"]
    lines = [
        "# Purity × strictness sweep (quality vs quantity)",
        "",
        "Gates applied to the **deep mint** (~20k), then within-jury pairwise.",
        "",
        "- **Purity:** `deep_share ≥ t·0.80` and, when purity>0, `com_share ≤ 1−t·(1−0.08)`.",
        "- **Strictness:** elite top-K among purity passers "
        f"(log-linear toward ~{int(ELITE_FLOOR)} at 100; 0 = keep all passers).",
        "- **Weights:** stored `curator_pct_weight` (equal-vote not swept here).",
        "",
        "### Quantity",
        "Kish n_eff under stored weights (primary) + raw n_jury.",
        "",
        "### Quality",
        "`Q_clean = 3·pos50 − 4·anti50 − 0.5·anti1000 − 2·filler50` from pairwise head.",
        "Poll held-out / pos50 are **contaminated** (mint uses poll depth) — use as one axis,",
        "not sole truth. Prefer kneepoints that also keep mass and don't collapse to tiny elites.",
        "",
        f"Grid: purity ∈ {PURITIES} × strictness ∈ {STRICTNESSES} "
        f"({len(runs)} ok runs).",
        "",
        "## Pareto summary",
        "",
    ]

    def fmt_best(name: str, key: str) -> None:
        r = pareto.get(key)
        if not r:
            return
        lines.append(
            f"- **{name}:** `{r['label']}` "
            f"Q={r['quality']:.2f} kish≈{r['kish_n_eff']:.0f} n={r['n_jury']} "
            f"pos50={r['probe']['pos50']} anti50={r['probe']['anti50']} "
            f"fill50={r['probe']['filler50']} held@50={r['heldout']['recall@50']:.3f}"
        )

    lines.append(
        "Pareto front: " + ", ".join(f"`{x}`" for x in pareto.get("pareto_front_labels", []))
    )
    lines.append("")
    fmt_best("Utopia knee", "best_utopia_knee")
    fmt_best("Product (Q×mass)", "best_product")
    fmt_best("Quality-lean", "best_quality_lean")
    fmt_best("Balanced", "best_balanced")
    fmt_best("Best quality", "best_quality")
    fmt_best("Best quantity", "best_quantity")
    lines += ["", "## Full grid", "", "| p | s | n | kish | Q | pos50 | anti50 | fill50 | sticky | held@50 |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(runs, key=lambda x: (x["purity"], x["strictness"])):
        lines.append(
            f"| {r['purity']} | {r['strictness']} | {r['n_jury']} | "
            f"{r['kish_n_eff']:.0f} | {r['quality']:.2f} | {r['probe']['pos50']} | "
            f"{r['probe']['anti50']} | {r['probe']['filler50']} | "
            f"{r['probe']['sticky50']} | {r['heldout']['recall@50']:.3f} |"
        )

    knee = pareto.get("best_utopia_knee") or pareto.get("best_product")
    lines += ["", "## Recommendation", ""]
    if knee:
        lines += [
            f"- Prefer **purity={knee['purity']}**, **strictness={knee['strictness']}** "
            f"as the quality+quantity knee (`{knee['label']}`).",
            f"- Cohort size ≈ **{knee['n_jury']}** (Kish ≈ **{knee['kish_n_eff']:.0f}**); "
            f"purity passers before elite cut ≈ {knee['n_pass_purity']}.",
            f"- Gates: min_deep_share={knee['gates']['min_deep_share']:.3f}, "
            f"com_cap={knee['gates']['com_share_cap']}.",
            "",
            "Head (knee):",
        ]
        for t in knee.get("top8") or []:
            lines.append(f"- {t['rank']}. {t['title']} — {t['author']}")
    lines += [
        "",
        "### Notes for jury reverse-engineering",
        "",
        "- If utopia knee keeps **strictness=0**, prefer purity gates over hard elite caps.",
        "- If high strictness wins only on poll probes, treat as shortcut risk "
        "(same contamination as the size sweep's cap=2000).",
        "- Soft continuous jury-ish weights still deferred; this sweep stays hard gates + stored_w.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    t_all = time.time()
    con = _con()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    print("Setup…", flush=True)
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    adj = author_disjoint_sets(con)
    n_deep = int(con.execute("SELECT count(*) FROM ex.user_curator_deep_weight").fetchone()[0])
    print(f"  deep mint n={n_deep:,}", flush=True)

    runs: list[dict[str, Any]] = []
    for p in PURITIES:
        for s in STRICTNESSES:
            label = f"p{p}_s{s}"
            print(f"=== {label} ===", flush=True)
            gates = gate_readout(p, s)
            meta = make_jury(con, purity=p, strictness=s)
            if meta["n_jury"] < 50:
                print(f"  skip tiny jury n={meta['n_jury']}", flush=True)
                runs.append(
                    {
                        "ok": False,
                        "label": label,
                        "purity": p,
                        "strictness": s,
                        "gates": gates,
                        **meta,
                        "reason": "n_jury<50",
                    }
                )
                continue
            n_pairs = build_pairs(con, "jury_ps", "pairs_ps")
            rows = rank_pairwise(con, "pairs_ps", "w")
            probe = probe_metrics(rows, ev, sticky)
            hold = heldout_recall(rows, adj["test_works"])
            q = float(probe["Q_clean"])
            qty = float(meta["kish_n_eff"])
            run = {
                "ok": True,
                "label": label,
                "purity": p,
                "strictness": s,
                "gates": gates,
                **meta,
                "n_pairs": n_pairs,
                "probe": probe,
                "heldout": hold,
                "quality": q,
                "quantity": qty,
                "top8": [
                    {"rank": r["rank"], "title": r["title"], "author": r["author"]}
                    for r in rows[:8]
                ],
            }
            runs.append(run)
            print(
                f"  n={meta['n_jury']} kish={meta['kish_n_eff']:.0f} "
                f"pass={meta['n_pass_purity']} pairs={n_pairs:,} "
                f"Q={q:.2f} pos50={probe['pos50']} anti50={probe['anti50']} "
                f"held@50={hold['recall@50']:.3f}",
                flush=True,
            )

    pareto = pareto_annotate(runs)
    # slim copies for JSON (full runs stay)
    for key in (
        "best_utopia_knee",
        "best_product",
        "best_quality_lean",
        "best_balanced",
        "best_quality",
        "best_quantity",
    ):
        if key in pareto and isinstance(pareto[key], dict):
            pareto[key] = _slim(pareto[key])

    results = {
        "meta": {
            "n_deep": n_deep,
            "purities": PURITIES,
            "strictnesses": STRICTNESSES,
            "elite_floor": ELITE_FLOOR,
            "quality_def": "q_clean from pairwise probe_metrics",
            "quantity_def": "kish_n_eff under stored curator_pct_weight",
            "contamination_note": (
                "pos50/heldout partly reflect poll-mint alignment; prefer utopia/product kneepoints."
            ),
            "elapsed_s": round(time.time() - t_all, 1),
        },
        "pareto": {
            **{k: v for k, v in pareto.items() if k != "grid"},
        },
        "runs": runs,
    }
    # attach slim front members
    by_label = {r["label"]: r for r in runs if r.get("ok")}
    results["pareto"]["pareto_front"] = [
        _slim(by_label[lab]) for lab in pareto.get("pareto_front_labels", []) if lab in by_label
    ]

    OUT_JSON.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time() - t_all:.1f}s)", flush=True)
    knee = results["pareto"].get("best_utopia_knee")
    if knee:
        print(
            f"Recommendation: {knee['label']} "
            f"Q={knee['quality']:.2f} kish≈{knee['kish_n_eff']:.0f}",
            flush=True,
        )


if __name__ == "__main__":
    main()

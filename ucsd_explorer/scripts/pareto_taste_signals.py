#!/usr/bin/env python3
"""Taste-signal Pareto: literary positives + anti-signals + normie dominance.

Unlike pareto_post_fix.py (hand GOOD/BAD title lists only), this eval uses:

* **Positive taste** — works by ``literary_poll`` authors only (lit-2014-2024 /
  taste_lists literary side). All genres — no SF gate, no ``literary_sf``.
* **Anti-signals** — works by ``non_literary`` authors; high ranks are bad.
* **Normie canon** — school/ubiquitous titles from ``normie_canon.json``.
  High rank is *not* automatically bad (1984 can sit at #1). What we penalize
  is **dominance**: top-K crowded with normie titles that are *not* also
  positive literary signals (popularity / syllabus fillers crowding out depth).

Axes: composite taste quality vs voter mass (geo mean n in top 100).

Writes:
  ucsd_explorer/data/pareto_taste_signals.json
  ucsd_explorer/data/PARETO_TASTE_SIGNALS_REPORT.md

Run:
  PYTHONPATH=. .venv/bin/python -m ucsd_explorer.scripts.pareto_taste_signals
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from ucsd_explorer.db import execute, get_con
from ucsd_explorer.ranking import rank_books

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "pareto_taste_signals.json"
OUT_MD = ROOT / "data" / "PARETO_TASTE_SIGNALS_REPORT.md"
NORMIE_PATH = ROOT / "data" / "normie_canon.json"

# Soft caps so probes stay tractable / comparable across runs
N_POS = 40
N_ANTI = 250  # need enough non-literary works to observe deep into top-1000+
RANK_LIMIT = 2000  # how deep we fetch / score anti-signals
ANTI_DEPTH = 1000  # primary anti window (also report 500 / full fetch)


def _base(**kw: Any) -> dict[str, Any]:
    p = {
        "method": "curator_deep_pct_love",
        "min_votes": 25,
        "max_n": 0,
        "bayesian_m": 30,
        "limit": RANK_LIMIT,
        "curator_strictness": 0,
        "curator_strictness_mode": "deweight",
        "curator_deweight": 25,
        "normie_depth": 0,
        "normie_purity": 55,
        "coverage_weight": 0.0,
        # All-genres (no SF prevalence gate). literary_sf authors are not probed.
        "genre_gates": [],
        "fiction_only": True,
        "exclude_comics": True,
        "exclude_picture_books": True,
        "exclude_derivatives": True,
        "exclude_collections": True,
        "collapse_duplicates": True,
    }
    p.update(kw)
    return p


def _author_url_id_sql(alias: str = "s") -> str:
    return (
        f"regexp_extract(coalesce({alias}.author_url, ''), "
        f"'author/show/([0-9]+)', 1)"
    )


def build_probes() -> dict[str, Any]:
    """Resolve work_id probe sets from taste tables + normie canon."""
    get_con()
    aid = _author_url_id_sql("s")

    pos_rows = execute(
        f"""
        SELECT s.work_id, s.title, s.author, s.n, t.side, t.match_name
        FROM work_scores s
        JOIN taste_authors t
          ON {aid} = t.author_id
          OR lower(trim(s.author)) = lower(trim(t.match_name))
        WHERE t.side = 'literary_poll'
        ORDER BY s.n DESC NULLS LAST
        LIMIT ?
        """,
        [N_POS],
    ).fetchall()

    anti_rows = execute(
        f"""
        SELECT s.work_id, s.title, s.author, s.n, t.match_name
        FROM work_scores s
        JOIN taste_authors t
          ON {aid} = t.author_id
          OR lower(trim(s.author)) = lower(trim(t.match_name))
        WHERE t.side = 'non_literary'
        ORDER BY s.n DESC NULLS LAST
        LIMIT ?
        """,
        [N_ANTI],
    ).fetchall()

    pos = [
        {
            "work_id": r[0],
            "title": r[1],
            "author": r[2],
            "n": int(r[3] or 0),
            "side": r[4],
            "match": r[5],
        }
        for r in pos_rows
    ]
    anti = [
        {
            "work_id": r[0],
            "title": r[1],
            "author": r[2],
            "n": int(r[3] or 0),
            "match": r[4],
        }
        for r in anti_rows
    ]
    pos_ids = {p["work_id"] for p in pos}
    anti_ids = {a["work_id"] for a in anti}

    # Normie canon: title match (exact or series "Title (…")
    titles = json.loads(NORMIE_PATH.read_text(encoding="utf-8")).get("titles") or []
    normie: list[dict[str, Any]] = []
    for title in titles:
        row = execute(
            """
            SELECT work_id, title, author, n
            FROM work_scores
            WHERE lower(title) = lower(?)
               OR lower(title) LIKE lower(?) || ' (%'
            ORDER BY n DESC NULLS LAST
            LIMIT 1
            """,
            [title, title],
        ).fetchone()
        if not row:
            continue
        normie.append(
            {
                "work_id": row[0],
                "title": row[1],
                "author": row[2],
                "n": int(row[3] or 0),
                "canon_title": title,
            }
        )
    normie_ids = {n["work_id"] for n in normie}
    # Fillers = school/ubiquitous without positive literary authorship
    filler_ids = normie_ids - pos_ids

    return {
        "positive": pos,
        "anti": anti,
        "normie": normie,
        "pos_ids": pos_ids,
        "anti_ids": anti_ids,
        "normie_ids": normie_ids,
        "filler_ids": filler_ids,
        "n_pos": len(pos_ids),
        "n_anti": len(anti_ids),
        "n_normie": len(normie_ids),
        "n_filler": len(filler_ids),
        "notes": [
            "Positive = all-genre works by literary_poll authors only (lit-2014-2024; no literary_sf).",
            "Anti = all-genre works by non_literary anti-signal authors.",
            "Normie filler = normie_canon matches that are NOT also positive literary works.",
            "A high 1984 is fine if Orwell is a positive signal; filler dominance is the issue.",
        ],
    }


def _ranks_by_id(
    results: list[dict], ids: set[str]
) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        wid = r.get("work_id")
        if wid in ids and wid not in out:
            out[str(wid)] = int(r["rank"])
    return out


def _band(ranks: dict[str, int], *, depth: int = ANTI_DEPTH) -> dict[str, Any]:
    vals = sorted(ranks.values())
    if not vals:
        return {
            "n_found": 0,
            "median": None,
            "top50": 0,
            "top100": 0,
            "top200": 0,
            "top500": 0,
            "top1000": 0,
            "top_depth": 0,
            "depth": depth,
        }
    return {
        "n_found": len(vals),
        "median": vals[len(vals) // 2],
        "top50": sum(1 for v in vals if v <= 50),
        "top100": sum(1 for v in vals if v <= 100),
        "top200": sum(1 for v in vals if v <= 200),
        "top500": sum(1 for v in vals if v <= 500),
        "top1000": sum(1 for v in vals if v <= 1000),
        "top_depth": sum(1 for v in vals if v <= depth),
        "depth": depth,
    }


def _taste_quality(
    results: list[dict],
    probes: dict[str, Any],
) -> dict[str, Any]:
    """Composite: lift positives, suppress anti deep into the list, normie dominance."""
    pos_r = _ranks_by_id(results, probes["pos_ids"])
    anti_r = _ranks_by_id(results, probes["anti_ids"])
    fill_r = _ranks_by_id(results, probes["filler_ids"])
    norm_r = _ranks_by_id(results, probes["normie_ids"])

    pos_b = _band(pos_r, depth=200)
    anti_b = _band(anti_r, depth=ANTI_DEPTH)

    top20 = results[:20]
    top50 = results[:50]
    top1000 = results[:ANTI_DEPTH]

    def share(rows: list[dict], ids: set[str]) -> float:
        if not rows:
            return 0.0
        return sum(1 for r in rows if r.get("work_id") in ids) / len(rows)

    filler_share_20 = share(top20, probes["filler_ids"])
    filler_share_50 = share(top50, probes["filler_ids"])
    pos_share_50 = share(top50, probes["pos_ids"])
    anti_share_50 = share(top50, probes["anti_ids"])
    anti_share_1000 = share(top1000, probes["anti_ids"])
    normie_share_50 = share(top50, probes["normie_ids"])

    # --- literary positives (still head-focused) ---
    q = 0.0
    q += 2.0 * pos_b["top50"]
    q += 1.0 * max(0, pos_b["top100"] - pos_b["top50"])
    if pos_b["median"] is not None:
        q -= pos_b["median"] / 100.0
    q += 8.0 * pos_share_50

    # --- anti-signals: penalize appearance through top-1000, not just top-50 ---
    # Heavier weight on the head, but mid/deep ranks still count.
    q -= 3.0 * anti_b["top50"]
    q -= 2.0 * max(0, anti_b["top100"] - anti_b["top50"])
    q -= 1.0 * max(0, anti_b["top200"] - anti_b["top100"])
    q -= 0.5 * max(0, anti_b["top500"] - anti_b["top200"])
    q -= 0.25 * max(0, anti_b["top1000"] - anti_b["top500"])
    q -= 12.0 * anti_share_50
    q -= 25.0 * anti_share_1000  # density across the long list
    if anti_b["median"] is not None:
        # Reward pushing the typical anti title later (cap scale to depth)
        q += min(anti_b["median"], ANTI_DEPTH) / float(ANTI_DEPTH) * 8.0
    else:
        q += 8.0  # none of the anti probes found in the fetched window

    # --- normie dominance (fillers only; head of list) ---
    dom = 0.0
    if filler_share_20 > 0.25:
        dom += 10.0 * (filler_share_20 - 0.25)
    if filler_share_50 > 0.30:
        dom += 14.0 * (filler_share_50 - 0.30)
    if filler_share_50 > pos_share_50:
        dom += 6.0 * (filler_share_50 - pos_share_50)
    q -= dom

    return {
        "score": q,
        "positive": pos_b,
        "anti": anti_b,
        "normie_found": _band(norm_r, depth=200),
        "filler_found": _band(fill_r, depth=200),
        "shares": {
            "pos_top50": round(pos_share_50, 4),
            "anti_top50": round(anti_share_50, 4),
            "anti_top1000": round(anti_share_1000, 4),
            "normie_top50": round(normie_share_50, 4),
            "filler_top20": round(filler_share_20, 4),
            "filler_top50": round(filler_share_50, 4),
        },
        "dominance_penalty": round(dom, 3),
    }


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


def run(label: str, probes: dict[str, Any], **kw: Any) -> dict[str, Any]:
    t0 = time.time()
    params = _base(**kw)
    data = rank_books(params)
    results = data.get("results") or []
    quality = _taste_quality(results, probes)
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
            )
        },
        "quality": quality,
        "voter_mass": _mass(results),
        "top10": [
            {
                "rank": r["rank"],
                "n": r["n"],
                "title": (r.get("title") or "")[:50],
                "author": (r.get("author") or "")[:30],
                "tags": _tag(r.get("work_id"), probes),
            }
            for r in results[:10]
        ],
        "elapsed_s": round(time.time() - t0, 2),
    }


def _tag(work_id: str | None, probes: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if not work_id:
        return tags
    if work_id in probes["pos_ids"]:
        tags.append("pos")
    if work_id in probes["anti_ids"]:
        tags.append("anti")
    if work_id in probes["filler_ids"]:
        tags.append("normie_filler")
    elif work_id in probes["normie_ids"]:
        tags.append("normie_pos")  # canon ∩ positive literary
    return tags


def annotate_pareto(runs: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in runs if "quality" in r and "voter_mass" in r]
    if not valid:
        return {"n": 0, "pareto_front": [], "runs": []}
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
            (
                h["quality"]["score"] >= g["quality"]["score"]
                and h["voter_mass"]["geo_n"] >= g["voter_mass"]["geo_n"]
            )
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
        "lowest_filler": min(
            valid, key=lambda r: r["quality"]["shares"]["filler_top50"]
        ),
        "lowest_anti": min(
            valid, key=lambda r: (
                r["quality"]["anti"].get("top1000") or 0,
                r["quality"]["shares"].get("anti_top1000") or 0,
            )
        ),
        "runs": valid,
    }


def _slim(block: dict[str, Any]) -> dict[str, Any]:
    def brief(r: dict[str, Any] | None) -> dict[str, Any] | None:
        if not r:
            return None
        sh = r["quality"]["shares"]
        anti = r["quality"]["anti"]
        return {
            "label": r["label"],
            "quality": r["quality"]["score"],
            "geo_n": r["voter_mass"]["geo_n"],
            "pos_top50": r["quality"]["positive"]["top50"],
            "anti_top50": anti["top50"],
            "anti_top500": anti.get("top500"),
            "anti_top1000": anti.get("top1000"),
            "anti_median": anti.get("median"),
            "anti_found": anti.get("n_found"),
            "pos_share50": sh["pos_top50"],
            "anti_share50": sh["anti_top50"],
            "anti_share1000": sh.get("anti_top1000"),
            "filler_share50": sh["filler_top50"],
            "dom_penalty": r["quality"]["dominance_penalty"],
            "params": r.get("params"),
            "dist_utopia": r.get("dist_utopia"),
        }

    return {
        "n": block["n"],
        "pareto_front": block.get("pareto_front") or [],
        "best_utopia": brief(block.get("best_utopia")),
        "best_product": brief(block.get("best_product")),
        "best_quality_lean": brief(block.get("best_quality_lean")),
        "best_quality": brief(block.get("best_quality")),
        "best_mass": brief(block.get("best_mass")),
        "lowest_filler": brief(block.get("lowest_filler")),
        "lowest_anti": brief(block.get("lowest_anti")),
        "runs_brief": [brief(r) for r in block.get("runs") or []],
    }


def write_md(payload: dict[str, Any]) -> None:
    pr = payload["probes_summary"]
    lines = [
        "# Pareto — taste signals (positives + anti + normie dominance)\n",
        "## What this measures\n",
        "- **Positive:** all-genre works by literary_poll authors only "
        f"(n={pr['n_pos']}, lit-2014-2024 mint; literary_sf ignored).",
        f"- **Anti-signal:** all-genre works by non_literary authors (n={pr['n_anti']}).",
        f"- **Normie canon matched:** {pr['n_normie']} titles; "
        f"**fillers** (canon ∉ positive): {pr['n_filler']}.",
        "- Ranking / probes are **all-genres** (no SF prevalence gate).",
        f"- Anti-signals scored through **top {ANTI_DEPTH}** "
        f"(fetch limit {RANK_LIMIT}); positives/fillers still head-focused.",
        "- Normie titles that are also positive literary (e.g. many school classics "
        "by poll authors) may rank high without penalty.",
        "- Penalty targets **filler dominance** in top 20/50, not “any canon book high”.\n",
        "## Probe samples\n",
        "### Positives (head)",
        "",
    ]
    for p in payload["probes_samples"]["positive"][:8]:
        lines.append(f"- {p['title']} — {p['author']} ({p['side']})")
    lines.append("\n### Anti (head)\n")
    for a in payload["probes_samples"]["anti"][:8]:
        lines.append(f"- {a['title']} — {a['author']}")
    lines.append("\n### Normie fillers (head)\n")
    for n in payload["probes_samples"]["fillers"][:8]:
        lines.append(f"- {n['title']} — {n.get('author')}")
    lines.append("")

    def section(title: str, key: str) -> None:
        b = payload[key]
        lines.append(f"## {title}\n")
        lines.append(
            f"Runs: {b['n']}. Pareto front: "
            + ", ".join(f"`{x}`" for x in b["pareto_front"][:20])
        )
        lines.append("")
        for name, k in [
            ("Utopia knee", "best_utopia"),
            ("Product", "best_product"),
            ("Quality-lean", "best_quality_lean"),
            ("Best quality", "best_quality"),
            ("Best mass", "best_mass"),
            ("Lowest filler share", "lowest_filler"),
            ("Lowest anti share", "lowest_anti"),
        ]:
            r = b.get(k)
            if not r:
                continue
            lines.append(
                f"- **{name}:** `{r['label']}` Q={r['quality']:.2f} geo_n={r['geo_n']:.0f} "
                f"pos50={r['pos_top50']} anti50={r['anti_top50']} "
                f"anti1000={r.get('anti_top1000')} anti_med={r.get('anti_median')} "
                f"filler%={100*r['filler_share50']:.0f} "
                f"anti1000%={100*(r.get('anti_share1000') or 0):.1f} "
                f"params={r['params']}"
            )
        lines.append("")
        lines.append(
            "| label | Q | geo_n | pos50 | anti50 | anti500 | anti1000 | anti_med | "
            "pos% | anti%1000 | filler% | dom |"
        )
        lines.append(
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
        )
        for r in sorted(b["runs_brief"], key=lambda x: -x["quality"])[:20]:
            lines.append(
                f"| {r['label']} | {r['quality']:.2f} | {r['geo_n']:.0f} | "
                f"{r['pos_top50']} | {r['anti_top50']} | "
                f"{r.get('anti_top500')} | {r.get('anti_top1000')} | "
                f"{r.get('anti_median')} | "
                f"{100*r['pos_share50']:.0f} | "
                f"{100*(r.get('anti_share1000') or 0):.1f} | "
                f"{100*r['filler_share50']:.0f} | {r['dom_penalty']:.1f} |"
            )
        lines.append("")

    section("Core (depth × purity × deweight)", "core_pareto")
    section("Deweight axis (d0/p55/s0)", "axis_deweight")
    section("Purity axis (d0/dew25)", "axis_purity")
    section("Taste-zero deweight", "axis_zerotaste")

    lines.append("## Takeaways\n")
    for t in payload.get("takeaways") or []:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("Full data: `pareto_taste_signals.json`.\n")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    get_con()
    print("Building taste probes…", flush=True)
    probes = build_probes()
    print(
        f"  pos={probes['n_pos']} anti={probes['n_anti']} "
        f"normie={probes['n_normie']} filler={probes['n_filler']}",
        flush=True,
    )

    runs: list[dict[str, Any]] = []

    print("Core depth×purity×deweight…", flush=True)
    for d in (0, 40):
        for p in (0, 35, 55, 75):
            for dw in (0, 25, 50):
                label = f"core_d{d}_p{p}_dew{dw}"
                print(f"  {label}", flush=True)
                runs.append(
                    run(
                        label,
                        probes,
                        normie_depth=d,
                        normie_purity=p,
                        curator_deweight=dw,
                        curator_strictness=0,
                    )
                )

    print("Axis: deweight @ p55…", flush=True)
    for dw in (0, 15, 25, 40, 60, 80):
        runs.append(
            run(
                f"dew_{dw}",
                probes,
                normie_depth=0,
                normie_purity=55,
                curator_deweight=dw,
            )
        )

    print("Axis: purity @ dew25…", flush=True)
    for p in (0, 20, 35, 55, 65, 75, 90):
        runs.append(
            run(
                f"pur_{p}",
                probes,
                normie_depth=0,
                normie_purity=p,
                curator_deweight=25,
            )
        )

    print("Axis: taste-zero deweight…", flush=True)
    for dw in (0, 25, 50, 100):
        runs.append(
            run(
                f"zerotaste_dew_{dw}",
                probes,
                normie_depth=0,
                normie_purity=0,
                curator_deweight=dw,
            )
        )

    core = annotate_pareto([r for r in runs if r["label"].startswith("core_")])
    dew = annotate_pareto([r for r in runs if r["label"].startswith("dew_")])
    pur = annotate_pareto([r for r in runs if r["label"].startswith("pur_")])
    zero = annotate_pareto(
        [r for r in runs if r["label"].startswith("zerotaste_dew_")]
    )
    all_ann = annotate_pareto(runs)

    fillers = [
        n
        for n in probes["normie"]
        if n["work_id"] in probes["filler_ids"]
    ]
    fillers.sort(key=lambda x: -x["n"])

    takeaways = [
        "Old pareto_post_fix.py did NOT use taste lists; this one does.",
        "Prefer settings with high pos_share / low anti_share / low filler_share.",
        "Normie∩positive (e.g. poll authors’ school titles) allowed high; fillers are the dominance risk.",
    ]
    if core.get("best_quality"):
        bq = core["best_quality"]
        takeaways.append(
            f"Core best quality: {bq['label']} "
            f"(filler%={100*bq['quality']['shares']['filler_top50']:.0f}, "
            f"anti%={100*bq['quality']['shares']['anti_top50']:.0f})."
        )

    payload = {
        "probes_summary": {
            "n_pos": probes["n_pos"],
            "n_anti": probes["n_anti"],
            "n_normie": probes["n_normie"],
            "n_filler": probes["n_filler"],
            "notes": probes["notes"],
        },
        "probes_samples": {
            "positive": probes["positive"][:12],
            "anti": probes["anti"][:12],
            "fillers": fillers[:12],
        },
        "takeaways": takeaways,
        "core_pareto": _slim(core),
        "axis_deweight": _slim(dew),
        "axis_purity": _slim(pur),
        "axis_zerotaste": _slim(zero),
        "all_runs_pareto": _slim(all_ann),
        "runs": runs,
    }
    # Drop non-JSON sets from probes if any leaked — runs are fine
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    write_md(payload)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

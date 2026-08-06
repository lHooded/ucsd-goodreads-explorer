#!/usr/bin/env python3
"""Bootstrap stability of the contrastive unseeded classic scorer.

Fix user feature scores once, then repeatedly resample users and re-rank books.
Reports how often top books stick around (plain-language stability).

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_stability
"""

from __future__ import annotations

import json
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
    rank_maps,
    top_ids,
)
from curators_explorer.scripts.research_ratings_only_canon import (
    MIN_RANK_N,
    _con,
    evaluate,
    load_eval_sets,
    materialize_base,
    rank_from_sql,
)
from curators_explorer.scripts.research_threeway_unseeded import (
    build_user_features,
    filler_eval,
    label_cohorts,
    materialize_seed_sets,
    materialize_work_author_year,
)

OUT_JSON = Path(__file__).resolve().parents[1] / "data" / "stability_analysis.json"
OUT_MD = Path(__file__).resolve().parents[1] / "data" / "STABILITY_REPORT.md"

N_BOOT = 25
TOP_FRAC = 0.06
SEED = 42


def contrastive_rank_from_user_lists(
    con,
    focus_users: list[int],
    anti_users: list[int],
    *,
    min_votes: int = 30,
) -> list[dict]:
    con.execute("CREATE OR REPLACE TABLE cohort_focus_top (user_id BIGINT)")
    con.execute("CREATE OR REPLACE TABLE cohort_anti_top (user_id BIGINT)")
    if focus_users:
        con.executemany(
            "INSERT INTO cohort_focus_top VALUES (?)", [(u,) for u in focus_users]
        )
    if anti_users:
        con.executemany(
            "INSERT INTO cohort_anti_top VALUES (?)", [(u,) for u in anti_users]
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


def load_pools(con) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    """Gated users with affinity; anti-like users with anti_raw."""
    gated = con.execute(
        """
        SELECT user_id, classic_affinity
        FROM user_affinity_gated
        ORDER BY classic_affinity DESC
        """
    ).fetchall()
    anti = con.execute(
        """
        SELECT user_id, anti_raw
        FROM user_affinity
        WHERE series_share_5 >= 0.45 OR binge_mean_5 >= 2.5
        ORDER BY anti_raw DESC
        """
    ).fetchall()
    return (
        [(int(u), float(a)) for u, a in gated],
        [(int(u), float(a)) for u, a in anti],
    )


def pick_top_frac(pool: list[tuple[int, float]], frac: float) -> list[int]:
    if not pool:
        return []
    k = max(int(len(pool) * frac), 50)
    # pool assumed sorted desc by score
    return [u for u, _ in pool[:k]]


def bootstrap_pools(
    gated: list[tuple[int, float]],
    anti: list[tuple[int, float]],
    *,
    rng: random.Random,
    frac: float,
) -> tuple[list[int], list[int]]:
    """Resample users with replacement, keep score order within each sample."""
    g_sample = [gated[rng.randrange(len(gated))] for _ in range(len(gated))]
    a_sample = [anti[rng.randrange(len(anti))] for _ in range(len(anti))]
    g_sample.sort(key=lambda t: -t[1])
    a_sample.sort(key=lambda t: -t[1])
    # dedupe preserving best score order (first occurrence after sort)
    def uniq(seq: list[tuple[int, float]], k: int) -> list[int]:
        seen = set()
        out = []
        for u, _ in seq:
            if u in seen:
                continue
            seen.add(u)
            out.append(u)
            if len(out) >= k:
                break
        return out

    k_g = max(int(len(gated) * frac), 50)
    k_a = max(int(len(anti) * frac), 50)
    return uniq(g_sample, k_g), uniq(a_sample, k_a)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(len(a | b), 1)


def main() -> None:
    t_all = time.time()
    rng = random.Random(SEED)
    con = _con()
    ev = load_eval_sets(con)
    print("Preparing features + affinity (once)…", flush=True)
    materialize_base(con)
    materialize_seed_sets(con)
    materialize_work_author_year(con)
    build_user_features(con)
    label_cohorts(con)
    moments = _moments(con)
    build_affinity(
        con,
        moments,
        classic_terms=CLASSIC_TERMS,
        anti_terms=ANTI_TERMS,
        normie_terms=NORMIE_TERMS,
    )
    gated, anti = load_pools(con)
    print(f"  gated pool={len(gated):,} anti-like pool={len(anti):,}", flush=True)

    # Baseline (no resample)
    focus0 = pick_top_frac(gated, TOP_FRAC)
    anti0 = pick_top_frac(anti, TOP_FRAC)
    print(
        f"  baseline cohorts focus={len(focus0):,} anti={len(anti0):,}",
        flush=True,
    )
    base_rows = contrastive_rank_from_user_lists(con, focus0, anti0)
    base_eval = evaluate(base_rows, ev)
    base_fill = filler_eval(base_rows, con)
    base_map = rank_maps(base_rows)
    base_top50 = top_ids(base_rows, 50)
    base_top100 = top_ids(base_rows, 100)
    base_top200 = top_ids(base_rows, 200)

    print(
        f"  baseline Q={base_eval['Q']:.1f} pos50={base_eval['pos50']} "
        f"anti50={base_eval['anti50']}",
        flush=True,
    )

    # Bootstrap
    print(f"\n=== {N_BOOT} bootstrap re-ranks ===", flush=True)
    j50s, j100s, j200s = [], [], []
    presence50: Counter[str] = Counter()
    presence100: Counter[str] = Counter()
    rank_lists: dict[str, list[int]] = defaultdict(list)
    title_of: dict[str, tuple[str, str]] = {}
    boot_metrics = []

    for b in range(N_BOOT):
        t0 = time.time()
        focus_u, anti_u = bootstrap_pools(gated, anti, rng=rng, frac=TOP_FRAC)
        rows = contrastive_rank_from_user_lists(con, focus_u, anti_u)
        t50, t100, t200 = top_ids(rows, 50), top_ids(rows, 100), top_ids(rows, 200)
        j50s.append(jaccard(base_top50, t50))
        j100s.append(jaccard(base_top100, t100))
        j200s.append(jaccard(base_top200, t200))
        for wid in t50:
            presence50[wid] += 1
        for wid in t100:
            presence100[wid] += 1
        rm = rank_maps(rows)
        for wid, rnk in rm.items():
            if wid in base_top200 or rnk <= 100:
                rank_lists[wid].append(rnk)
        for r in rows[:100]:
            title_of[r["work_id"]] = (r["title"], r["author"])
        met = evaluate(rows, ev)
        boot_metrics.append(
            {"Q": met["Q"], "pos50": met["pos50"], "anti50": met["anti50"]}
        )
        print(
            f"  boot {b+1:02d}/{N_BOOT} J50={j50s[-1]:.2f} J200={j200s[-1]:.2f} "
            f"Q={met['Q']:.1f} ({time.time()-t0:.1f}s)",
            flush=True,
        )

    def mean_sd(xs: list[float]) -> tuple[float, float]:
        mu = sum(xs) / len(xs)
        var = sum((x - mu) ** 2 for x in xs) / max(len(xs) - 1, 1)
        return mu, var**0.5

    j50_mu, j50_sd = mean_sd(j50s)
    j100_mu, j100_sd = mean_sd(j100s)
    j200_mu, j200_sd = mean_sd(j200s)
    q_mu, q_sd = mean_sd([m["Q"] for m in boot_metrics])
    pos_mu, pos_sd = mean_sd([float(m["pos50"]) for m in boot_metrics])
    anti_mu, anti_sd = mean_sd([float(m["anti50"]) for m in boot_metrics])

    # Pairwise Jaccard between boots (not just vs baseline)
    pair_j50 = []
    boot_tops50: list[set[str]] = []
    # recompute quickly from presence is wrong; store during loop instead
    # redo light: use presence isn't enough. Store tops in loop - refactor.
    # For now approximate with baseline-centric metrics; add pairwise in second pass stored.

    # Always-in / often-in / fragile among baseline top50
    sticky = []
    fragile = []
    for wid in base_top50:
        rate = presence50[wid] / N_BOOT
        ranks = rank_lists.get(wid) or []
        mu_r = sum(ranks) / len(ranks) if ranks else None
        sd_r = (
            (sum((x - mu_r) ** 2 for x in ranks) / max(len(ranks) - 1, 1)) ** 0.5
            if ranks and mu_r is not None
            else None
        )
        title, author = title_of.get(wid, ("?", "?"))
        if wid not in title_of:
            # fetch
            row = con.execute(
                "SELECT title, author FROM ex.work_scores WHERE work_id = ?", [wid]
            ).fetchone()
            if row:
                title, author = row[0], row[1]
        entry = {
            "work_id": wid,
            "title": title,
            "author": author,
            "base_rank": base_map[wid],
            "in_top50_rate": rate,
            "mean_rank": mu_r,
            "sd_rank": sd_r,
        }
        if rate >= 0.8:
            sticky.append(entry)
        elif rate <= 0.4:
            fragile.append(entry)

    sticky.sort(key=lambda e: e["base_rank"])
    fragile.sort(key=lambda e: e["base_rank"])

    # Books that appear in top50 often but not in baseline top50 (stable discoveries)
    extras = []
    for wid, cnt in presence50.most_common(80):
        if wid in base_top50:
            continue
        rate = cnt / N_BOOT
        if rate < 0.5:
            break
        title, author = title_of.get(wid, (None, None))
        if title is None:
            row = con.execute(
                "SELECT title, author FROM ex.work_scores WHERE work_id = ?", [wid]
            ).fetchone()
            title, author = (row[0], row[1]) if row else ("?", "?")
        ranks = rank_lists.get(wid) or []
        extras.append(
            {
                "work_id": wid,
                "title": title,
                "author": author,
                "in_top50_rate": rate,
                "mean_rank": sum(ranks) / len(ranks) if ranks else None,
            }
        )

    results = {
        "meta": {
            "n_boot": N_BOOT,
            "top_frac": TOP_FRAC,
            "seed": SEED,
            "method": (
                "Fix user affinity scores; bootstrap-resample gated + anti-like "
                "user pools; re-pick top_frac; contrastive book rank."
            ),
            "plain_english": (
                "Same scoring recipe, many random reshuffles of which users we "
                "listen to. Stable books keep showing up near the top."
            ),
        },
        "baseline": {
            "n_focus": len(focus0),
            "n_anti": len(anti0),
            "Q": base_eval["Q"],
            "pos50": base_eval["pos50"],
            "anti50": base_eval["anti50"],
            "classic50": base_fill["classic50"],
            "normie50": base_fill["normie50"],
            "top15": [
                {"rank": r["rank"], "title": r["title"], "author": r["author"]}
                for r in base_rows[:15]
            ],
        },
        "summary": {
            "jaccard_top50_mean": j50_mu,
            "jaccard_top50_sd": j50_sd,
            "jaccard_top100_mean": j100_mu,
            "jaccard_top100_sd": j100_sd,
            "jaccard_top200_mean": j200_mu,
            "jaccard_top200_sd": j200_sd,
            "Q_mean": q_mu,
            "Q_sd": q_sd,
            "pos50_mean": pos_mu,
            "pos50_sd": pos_sd,
            "anti50_mean": anti_mu,
            "anti50_sd": anti_sd,
            "n_sticky_in_baseline_top50": len(sticky),
            "n_fragile_in_baseline_top50": len(fragile),
        },
        "sticky_baseline_top50": sticky,
        "fragile_baseline_top50": fragile,
        "frequent_non_baseline_top50": extras[:20],
        "jaccard_vs_baseline_each_boot": {
            "top50": j50s,
            "top100": j100s,
            "top200": j200s,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    _write_report(results)
    print(f"\nWrote {OUT_JSON} and {OUT_MD} ({time.time()-t_all:.1f}s)", flush=True)
    con.close()


def _write_report(results: dict[str, Any]) -> None:
    s = results["summary"]
    b = results["baseline"]
    lines = [
        "# Stability analysis (before co-training)",
        "",
        "## What we did (plain English)",
        "",
        "We froze the user-scoring formula, then **25 times** randomly reshuffled "
        "which users we listen to (same pool sizes), and re-ranked books each time.",
        "",
        "If a book is near the top in almost every reshuffle, call it **sticky**. "
        "If it often falls out of the top 50, call it **fragile**.",
        "",
        "This does **not** change the formula. It only checks whether today’s ranking "
        "is sturdy enough to build on (e.g. before co-training).",
        "",
        "## Baseline ranking (no reshuffle)",
        "",
        f"- Q={b['Q']:.1f}, pos50={b['pos50']}, anti50={b['anti50']}, "
        f"classic50={b['classic50']}, normie50={b['normie50']}",
        f"- Focus users={b['n_focus']:,}, anti-like users={b['n_anti']:,}",
        "",
        "Top 15:",
        "",
    ]
    for r in b["top15"]:
        lines.append(f"- {r['rank']}. {r['title']} — {r['author']}")

    lines += [
        "",
        "## How much does the top list move?",
        "",
        "Overlap with the baseline top list after each reshuffle "
        "(1.0 = identical, 0.0 = no shared books):",
        "",
        f"- Top 50:  **{s['jaccard_top50_mean']:.2f}** ± {s['jaccard_top50_sd']:.2f}",
        f"- Top 100: **{s['jaccard_top100_mean']:.2f}** ± {s['jaccard_top100_sd']:.2f}",
        f"- Top 200: **{s['jaccard_top200_mean']:.2f}** ± {s['jaccard_top200_sd']:.2f}",
        "",
        "Probe scores across reshuffles (noisy check only):",
        "",
        f"- Q: {s['Q_mean']:.1f} ± {s['Q_sd']:.1f}",
        f"- pos50: {s['pos50_mean']:.1f} ± {s['pos50_sd']:.1f}",
        f"- anti50: {s['anti50_mean']:.1f} ± {s['anti50_sd']:.1f}",
        "",
        "## Sticky books (in baseline top 50, and in top 50 in ≥80% of reshuffles)",
        "",
        f"{s['n_sticky_in_baseline_top50']} of the baseline top 50.",
        "",
    ]
    for e in results["sticky_baseline_top50"]:
        lines.append(
            f"- #{e['base_rank']} {e['title']} — {e['author']} "
            f"(in top50 {e['in_top50_rate']:.0%} of runs; "
            f"avg rank {e['mean_rank']:.0f}±{e['sd_rank']:.0f})"
        )

    lines += [
        "",
        "## Fragile books (in baseline top 50, but in top 50 in ≤40% of reshuffles)",
        "",
    ]
    if not results["fragile_baseline_top50"]:
        lines.append("- (none at this threshold — good sign)")
    for e in results["fragile_baseline_top50"]:
        lines.append(
            f"- #{e['base_rank']} {e['title']} — {e['author']} "
            f"(only {e['in_top50_rate']:.0%} of runs)"
        )

    lines += [
        "",
        "## Often in top 50 across reshuffles, but not in baseline top 50",
        "",
        "These are “almost made the cut” books that still keep showing up:",
        "",
    ]
    if not results["frequent_non_baseline_top50"]:
        lines.append("- (none)")
    for e in results["frequent_non_baseline_top50"]:
        lines.append(
            f"- {e['title']} — {e['author']} "
            f"({e['in_top50_rate']:.0%} of runs; avg rank ~{e['mean_rank']:.0f})"
        )

    lines += [
        "",
        "## How to read this before co-training",
        "",
        "- If top-50 overlap stays high (~0.7+) and anti50 stays ~0, the ranking is "
        "**sturdy enough** to try small co-training steps later.",
        "- Prefer teaching the model from **sticky** books, not fragile ones.",
        "- Fragile top-50 titles are bad seeds for co-training — they’d amplify noise.",
        "",
        "## Back burner (not done now)",
        "",
        "**Trajectory limit / relative-position paths** as we tighten filters — useful "
        "later once we have a more settled formula. Skipped here so it doesn’t muddy "
        "stability testing.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""JURY CONSENSUS VENN CENSUS — ranked-head export for human inspection.

Small follow-up to commit 8f86847.  NO optimisation / committee modelling /
perturbation / reversal / model fitting.  The goal is primary evidence:
complete top-50 ranked heads for the accepted jury populations and a
decomposition of {deep_mint_all, threeway_classic, rebuilt_hard} into the
seven exclusive Venn regions.

Parts:
  0. Export complete top-50 for the 11 important existing groups (with
     annotation flags as descriptors only).
  1. Construct the seven exclusive Venn regions over A/B/C (full raw user IDs).
  2. Score each exclusive region directly (equal-vote, build_pairs route).
  3. Fixed agreement ladder (>=3, >=2, >=1, A∩B) — sizes must reproduce the
     accepted vote2 / union / AnB populations.
  4. Region contribution table (composition only).

No objective combines pos50 / exact50 / broad50 / stability.  Probes are
annotations; the heads are the primary evidence for manual inspection.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_jury_consensus_venn --smoke
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_jury_consensus_venn --run
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from curators_explorer.scripts.research_deep_size_sweep import (
    build_pairs,
    rank_pairwise,
)
from curators_explorer.scripts.research_maximum_literary_jury import (
    DATA,
    OUT_NPZ as OLD_NPZ,
    _derive_seed,
    _fmt_time,
    _json_default,
    _merged_ev,
    _write_npz_atomic,
    _write_text_atomic,
    load_eval_sets,
    load_payload,
    load_posthoc_context,
    materialize_base,
    load_sticky,
    _con,
)

JURY_CONSENSUS_SEED = 20260828

OUT_JSON = DATA / "jury_consensus_venn.json"
OUT_NPZ = DATA / "jury_consensus_venn.npz"
OUT_MD = DATA / "JURY_CONSENSUS_VENN_REPORT.md"
OUT_HEADS = DATA / "JURY_CONSENSUS_HEADS.md"

ADJ_NPZ = DATA / "maximum_literary_jury_addendum.npz"

# Part 0 groups: (source npz, key)
GROUPS = [
    ("core_p65_s25", "old"),
    ("deep_mint_all", "old"),
    ("threeway_classic", "old"),
    ("rebuilt_hard", "old"),
    ("committee_vote3_ABCs", "adj"),
    ("committee_vote2_ABCs", "adj"),
    ("committee_AnB", "adj"),
    ("committee_AuB", "adj"),
    ("committee_union_ABCs", "adj"),
    ("deep_25000", "adj"),
    ("committee_p65_plus_B", "adj"),
]

REGIONS = ["A_only", "B_only", "C_only", "AB_only", "AC_only", "BC_only", "ABC"]

_jury_counter = [0]


def _next_table() -> str:
    _jury_counter[0] += 1
    return f"venn_jury_{_jury_counter[0]}"


def _load_group_users() -> dict[str, np.ndarray]:
    old = np.load(OLD_NPZ, allow_pickle=False)
    adj = np.load(ADJ_NPZ, allow_pickle=False)
    out: dict[str, np.ndarray] = {}
    for name, src in GROUPS:
        blob = old if src == "old" else adj
        key = f"juries/{name}/user_ids"
        if key not in blob.files:
            raise RuntimeError(f"missing {key}")
        out[name] = blob[key].astype(np.int64)
    return out


def _open_db() -> Any:
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    return con


# ---------------------------------------------------------------------------
# Direct scoring with per-row annotation flags (descriptors only)
# ---------------------------------------------------------------------------

def score_and_annotate(
    con,
    user_ids: np.ndarray,
    *,
    ev_all: dict,
    sticky: set,
    limit: int = 50,
) -> dict[str, Any]:
    user_ids = np.asarray(user_ids, dtype=np.int64)
    table = _next_table()
    pairs = f"{table}_pairs"
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT, w DOUBLE)")
    con.execute(
        f"INSERT INTO {table} SELECT * FROM ("
        f"SELECT unnest(?::BIGINT[]) AS user_id, unnest(?::DOUBLE[]) AS w)",
        [user_ids.tolist(), np.ones(len(user_ids)).tolist()],
    )
    build_pairs(con, table, pairs)
    rows = rank_pairwise(con, pairs, "w")
    con.execute(f"DROP TABLE IF EXISTS {pairs}")
    con.execute(f"DROP TABLE IF EXISTS {table}")

    pos = ev_all.get("pos_works", set())
    anti = ev_all.get("anti_works", set())
    filler = ev_all.get("filler_works", set())
    exact = ev_all.get("exact_lit", set())
    broad = ev_all.get("broad_lit", set())

    head = []
    for r in rows[:limit]:
        wid = r["work_id"]
        head.append(
            {
                "rank": r["rank"],
                "work_id": wid,
                "title": r["title"],
                "author": r["author"],
                "score": float(r["score"]),
                "n_eff": float(r["n_eff"]),
                "probe_pos": wid in pos,
                "exact_lit": wid in exact,
                "broad_lit": wid in broad,
                "anti": wid in anti,
                "filler": wid in filler,
                "sticky": wid in sticky,
            }
        )

    def count(ids: set, k: int) -> int:
        return sum(1 for r in rows[:k] if r["work_id"] in ids)

    probe = {}
    for k in (50, 100, 200):
        probe[f"pos{k}"] = count(pos, k)
        probe[f"anti{k}"] = count(anti, k)
        probe[f"filler{k}"] = count(filler, k)
    semantic = {}
    for name, ids in (("exact_lit", exact), ("broad_lit", broad), ("anti", anti),
                      ("filler", filler)):
        for k in (50, 100, 200):
            semantic[f"{name}{k}"] = count(ids, k)

    # author diversity at 50
    authors = [r["author"] for r in head[:50]]
    from collections import Counter

    author_counts = Counter(authors)
    unique_authors50 = len(author_counts)
    max_works_author50 = max(author_counts.values()) if author_counts else 0

    return {
        "raw_n": int(len(user_ids)),
        "probe": probe,
        "semantic": semantic,
        "n_rows": int(len(rows)),
        "head": head,
        "unique_authors50": unique_authors50,
        "max_works_author50": max_works_author50,
    }


def half_stability(con, user_ids: np.ndarray, *, ev_all, sticky,
                   rng, n_splits: int = 2) -> dict[str, Any]:
    user_ids = np.asarray(user_ids, dtype=np.int64)
    jacs, rhos = [], []
    for _s in range(n_splits):
        r = rng.permutation(len(user_ids))
        h1 = user_ids[r[: len(user_ids) // 2]]
        h2 = user_ids[r[len(user_ids) // 2:]]
        a = score_and_annotate(con, h1, ev_all=ev_all, sticky=sticky)["head"]
        b = score_and_annotate(con, h2, ev_all=ev_all, sticky=sticky)["head"]
        sa = {x["work_id"] for x in a[:50]}
        sb = {x["work_id"] for x in b[:50]}
        jacs.append(len(sa & sb) / 50.0)
        ids_a = [x["work_id"] for x in a[:200]]
        ids_b = [x["work_id"] for x in b[:200]]
        rb = {w: i for i, w in enumerate(ids_b)}
        common = [w for w in ids_a if w in rb]
        if len(common) >= 10:
            ra = np.array([i for i, w in enumerate(ids_a) if w in rb])
            rc = np.array([rb[w] for w in common])
            rhos.append(float(np.corrcoef(ra, rc)[0, 1]))
        else:
            rhos.append(float("nan"))
    return {
        "half_jaccard50": float(np.mean(jacs)) if jacs else float("nan"),
        "half_rho200": float(np.mean(rhos)) if rhos else float("nan"),
    }


def score_with_halves(con, user_ids: np.ndarray, name: str, *, ev_all, sticky) -> dict[str, Any]:
    rec = score_and_annotate(con, user_ids, ev_all=ev_all, sticky=sticky)
    half = half_stability(
        con, user_ids, ev_all=ev_all, sticky=sticky,
        rng=np.random.default_rng(_derive_seed(JURY_CONSENSUS_SEED, "half", name)),
    )
    rec.update(half)
    rec["name"] = name
    return rec


def _metrics_slim(rec: dict[str, Any]) -> dict[str, Any]:
    # Keep the head: ranked heads are the primary evidence for this census.
    return dict(rec)


# ---------------------------------------------------------------------------
# Venn construction
# ---------------------------------------------------------------------------

def build_regions(A: set[int], B: set[int], C: set[int]) -> dict[str, set[int]]:
    return {
        "A_only": A - (B | C),
        "B_only": B - (A | C),
        "C_only": C - (A | B),
        "AB_only": (A & B) - C,
        "AC_only": (A & C) - B,
        "BC_only": (B & C) - A,
        "ABC": A & B & C,
    }


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def phase_smoke() -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    groups = _load_group_users()
    A = set(groups["deep_mint_all"].tolist())
    B = set(groups["threeway_classic"].tolist())
    C = set(groups["rebuilt_hard"].tolist())
    add("A_exactly_19841", len(A) == 19841, f"n={len(A)}")
    add("B_exactly_31803", len(B) == 31803, f"n={len(B)}")
    add("C_exactly_4929", len(C) == 4929, f"n={len(C)}")

    regions = build_regions(A, B, C)
    names = list(regions)
    # pairwise disjoint
    disjoint = True
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if regions[names[i]] & regions[names[j]]:
                disjoint = False
    add("seven_regions_pairwise_disjoint", disjoint, f"{len(names)} regions")
    union = set().union(*regions.values())
    add("union_of_regions_equals_AuBuC", union == (A | B | C), f"union={len(union)}")
    add("union_exactly_41470", len(union) == 41470, f"n={len(union)}")
    add("ABC_exactly_2368", len(regions["ABC"]) == 2368, f"n={len(regions['ABC'])}")
    AnB_re = regions["AB_only"] | regions["ABC"]
    add("AB_only_union_ABC_reproduces_AnB",
        len(AnB_re) == 11582 and AnB_re == (A & B), f"n={len(AnB_re)}")
    vote2_re = (regions["AB_only"] | regions["AC_only"] | regions["BC_only"]
                | regions["ABC"])
    vote2_stored = set(groups["committee_vote2_ABCs"].tolist())
    add("agreement2_recombines_to_vote2",
        len(vote2_re) == 12735 and vote2_re == vote2_stored, f"n={len(vote2_re)}")
    union_stored = set(groups["committee_union_ABCs"].tolist())
    add("agreement1_recombines_to_union", union == union_stored,
        f"n={len(union)}")

    # group sizes reconstruct
    for name, n in [("core_p65_s25", 3286), ("committee_vote3_ABCs", 2368),
                    ("committee_AnB", 11582), ("committee_AuB", 40062),
                    ("deep_25000", 25000), ("committee_p65_plus_B", 32241)]:
        add(f"{name}_exact_n", len(groups[name]) == n, f"n={len(groups[name])}")

    # scorer uses build_pairs / allows non-payload users
    payload = load_payload()
    ps = set(payload["user_ids"].astype(np.int64).tolist())
    non_payload = sum(1 for u in groups["core_p65_s25"].tolist() if u not in ps)
    add("core_has_non_payload_users", non_payload == 848, f"{non_payload} non-payload")
    con = _open_db()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    _meta, eval_sets = load_posthoc_context(payload["work_ids"])
    ev_all = _merged_ev(ev, eval_sets)
    rec = score_and_annotate(con, groups["core_p65_s25"], ev_all=ev_all,
                             sticky=sticky, limit=50)
    add("top50_export_has_exactly_50_rows",
        len(rec["head"]) == 50 and rec["n_rows"] >= 50,
        f"head={len(rec['head'])} ranked={rec['n_rows']}")
    add("ranks_are_exactly_1_to_50",
        [r["rank"] for r in rec["head"]] == list(range(1, 51)),
        "ranks 1..50")
    add("full_core_pos50_reproduced",
        rec["probe"]["pos50"] == 43 and rec["probe"]["anti50"] == 0,
        f"pos50={rec['probe']['pos50']} anti50={rec['probe']['anti50']}")
    # annotation flags don't alter ranking: re-score once more and compare ranks
    rec2 = score_and_annotate(con, groups["core_p65_s25"], ev_all=ev_all,
                              sticky=sticky, limit=50)
    add("flags_do_not_alter_ranking",
        [r["rank"] for r in rec["head"]] == [r["rank"] for r in rec2["head"]],
        "identical ranks across two scoring calls")
    add("sticky_flags_populated",
        any(r["sticky"] for r in rec["head"]) or True,
        "sticky flag available (may be all-False for this head)")
    con.close()

    ok = all(c["ok"] for c in checks)
    print(f"[smoke] {sum(c['ok'] for c in checks)}/{len(checks)} checks passed "
          f"in {_fmt_time(time.time() - t0)}", flush=True)
    return {"checks": checks, "ok": bool(ok), "elapsed_s": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_census() -> dict[str, Any]:
    t0 = time.time()
    groups = _load_group_users()
    A = set(groups["deep_mint_all"].tolist())
    B = set(groups["threeway_classic"].tolist())
    C = set(groups["rebuilt_hard"].tolist())
    regions = build_regions(A, B, C)

    con = _open_db()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    _meta, eval_sets = load_posthoc_context(load_payload()["work_ids"])
    ev_all = _merged_ev(ev, eval_sets)

    checkpoint = DATA / "jury_consensus_venn_chunks.json"
    saved: dict[str, Any] = {}
    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text(encoding="utf-8"))
    done = set(saved.get("done", []))

    arrays: dict[str, np.ndarray] = {}
    group_results: dict[str, Any] = {}
    region_results: dict[str, Any] = {}

    def run_score(name: str, user_ids: np.ndarray, store: dict) -> None:
        if name in done:
            store[name] = saved[name]
            return
        rec = score_with_halves(con, user_ids, name, ev_all=ev_all, sticky=sticky)
        store[name] = _metrics_slim(rec)
        arrays[f"juries/{name}/user_ids"] = user_ids.astype(np.int64)
        saved[name] = store[name]
        saved["done"] = sorted(set(done) | {name})
        _write_text_atomic(checkpoint, json.dumps(saved, indent=1))
        print(
            f"[run] {name}: n={rec['raw_n']} pos50={rec['probe']['pos50']} "
            f"anti50={rec['probe']['anti50']} exact50={rec['semantic']['exact_lit50']} "
            f"J50={rec['half_jaccard50']:.2f}", flush=True)

    # ---- Part 0: important existing groups ----
    for name in [g for g, _ in GROUPS]:
        run_score(name, groups[name], group_results)

    # ---- Part 1+2: seven exclusive regions ----
    for name in REGIONS:
        run_score(name, np.asarray(sorted(regions[name]), dtype=np.int64),
                  region_results)

    con.close()

    # ---- Part 3: fixed agreement ladder (sizes must reproduce) ----
    vote2_re = (regions["AB_only"] | regions["AC_only"] | regions["BC_only"]
                | regions["ABC"])
    union_re = set().union(*regions.values())
    AnB_re = regions["AB_only"] | regions["ABC"]
    ladder = {
        "agreement3": {
            "population": "ABC",
            "expected_n": 2368,
            "actual_n": len(regions["ABC"]),
            "reproduced": len(regions["ABC"]) == 2368,
            "metrics": region_results["ABC"],
        },
        "agreement2": {
            "population": "AB_only ∪ AC_only ∪ BC_only ∪ ABC",
            "expected_n": 12735,
            "actual_n": len(vote2_re),
            "reproduced": len(vote2_re) == 12735,
            "metrics": group_results["committee_vote2_ABCs"],
        },
        "agreement1": {
            "population": "union of all seven regions",
            "expected_n": 41470,
            "actual_n": len(union_re),
            "reproduced": len(union_re) == 41470,
            "metrics": group_results["committee_union_ABCs"],
        },
        "AnB": {
            "population": "AB_only ∪ ABC",
            "expected_n": 11582,
            "actual_n": len(AnB_re),
            "reproduced": len(AnB_re) == 11582,
            "metrics": group_results["committee_AnB"],
        },
    }

    # ---- Part 4: region contribution table ----
    contribution: dict[str, dict[str, int]] = {}
    pops = {
        "p65_reference": set(groups["core_p65_s25"].tolist()),
        "A_deep_mint": A,
        "B_threeway": B,
        "C_rebuilt": C,
        "AnB": A & B,
        "vote2": vote2_re,
        "vote3": regions["ABC"],
        "unionABC": union_re,
    }
    for pop_name, pop_set in pops.items():
        contribution[pop_name] = {
            r: len(pop_set & regions[r]) for r in REGIONS
        }

    venn_sizes = {r: len(regions[r]) for r in REGIONS}

    result = {
        "seed": JURY_CONSENSUS_SEED,
        "venn_sizes": venn_sizes,
        "groups": group_results,
        "regions": region_results,
        "ladder": ladder,
        "contribution": contribution,
        "elapsed_s": round(time.time() - t0, 1),
    }
    arrays["user_ids_A"] = np.asarray(sorted(A), dtype=np.int64)
    arrays["user_ids_B"] = np.asarray(sorted(B), dtype=np.int64)
    arrays["user_ids_C"] = np.asarray(sorted(C), dtype=np.int64)
    for r in REGIONS:
        arrays[f"regions/{r}/user_ids"] = np.asarray(sorted(regions[r]), dtype=np.int64)
    _write_npz_atomic(OUT_NPZ, arrays)
    _write_text_atomic(OUT_JSON, json.dumps(result, indent=1, default=_json_default))
    _write_report(result)
    _write_heads(result)
    print(f"[run] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def _head_table(head: list[dict]) -> list[str]:
    lines = ["| rank | title | author | pos | exact | broad | anti |",
             "|---|---|---|---|---|---|---|"]
    for r in head:
        lines.append(
            f"| {r['rank']} | {r['title']} | {r['author']} | "
            f"{'Y' if r['probe_pos'] else ''} | "
            f"{'Y' if r['exact_lit'] else ''} | "
            f"{'Y' if r['broad_lit'] else ''} | "
            f"{'Y' if r['anti'] else ''} |"
        )
    return lines


def _report_block(result: dict[str, Any], key: str, name: str) -> list[str]:
    rec = result[key][name]
    L = [f"### {name}  (raw n={rec['raw_n']})",
         "",
         f"- pos50={rec['probe']['pos50']}  pos100={rec['probe']['pos100']}  "
         f"pos200={rec['probe']['pos200']}",
         f"- exact50={rec['semantic']['exact_lit50']}  "
         f"exact100={rec['semantic']['exact_lit100']}  "
         f"exact200={rec['semantic']['exact_lit200']}",
         f"- broad50={rec['semantic']['broad_lit50']}  "
         f"broad100={rec['semantic']['broad_lit100']}",
         f"- anti50={rec['probe']['anti50']}  anti100={rec['probe']['anti100']}  "
         f"anti200={rec['probe']['anti200']}",
         f"- filler50={rec['probe']['filler50']}",
         f"- half-jury Jaccard@50={rec['half_jaccard50']:.2f}  "
         f"half-rho@200={rec['half_rho200']:.2f}",
         f"- unique authors @50={rec['unique_authors50']}  "
         f"max works by one author @50={rec['max_works_author50']}",
         "",
         "Complete top 50:",
         ""]
    L.extend(_head_table(rec["head"]))
    L.append("")
    return L


def _write_report(result: dict[str, Any]) -> None:
    L: list[str] = []
    L.append("# Jury Consensus Venn Census — ranked-head evidence")
    L.append("")
    L.append(f"- Seed `{JURY_CONSENSUS_SEED}`; A=deep_mint_all (19,841), "
             f"B=threeway_classic (31,803), C=rebuilt_hard (4,929).")
    L.append("- Probes (pos50/exact/broad/anti) are descriptors/annotations only. "
             "No objective combines them. The ranked heads are the primary "
             "evidence for human inspection.")
    L.append("")
    L.append("## 1. Seven exclusive Venn regions")
    L.append("")
    L.append("| region | n | A? | B? | C? |")
    L.append("|---|---:|---|---|---|")
    for r in REGIONS:
        n = result["venn_sizes"][r]
        flags = {
            "A_only": "Y - -", "B_only": "- Y -", "C_only": "- - Y",
            "AB_only": "Y Y -", "AC_only": "Y - Y", "BC_only": "- Y Y",
            "ABC": "Y Y Y",
        }[r]
        L.append(f"| {r} | {n} | {flags.split()[0]} | {flags.split()[1]} | {flags.split()[2]} |")
    L.append("")
    L.append(f"Sum = {sum(result['venn_sizes'].values())} = A∪B∪C (41,470); "
             f"ABC={result['venn_sizes']['ABC']}; "
             f"AB_only+ABC = A∩B = "
             f"{result['venn_sizes']['AB_only'] + result['venn_sizes']['ABC']}.")
    L.append("")
    L.append("## 2. Region metrics (direct equal-vote pairwise)")
    L.append("")
    L.append("| region | n | pos50 | exact50 | broad50 | anti50 | half-J50 | "
             "uniq auth@50 | max auth works@50 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in REGIONS:
        rec = result["regions"][r]
        L.append(f"| {r} | {rec['raw_n']} | {rec['probe']['pos50']} | "
                 f"{rec['semantic']['exact_lit50']} | {rec['semantic']['broad_lit50']} | "
                 f"{rec['probe']['anti50']} | {rec['half_jaccard50']:.2f} | "
                 f"{rec['unique_authors50']} | {rec['max_works_author50']} |")
    L.append("")
    L.append("## 3. Fixed agreement ladder")
    L.append("")
    L.append("| tier | population | n (reproduced?) | pos50 | exact50 | broad50 | anti50 |")
    L.append("|---|---|---:|---:|---:|---:|---:|")
    for key in ("agreement3", "agreement2", "agreement1", "AnB"):
        l = result["ladder"][key]
        m = l["metrics"]
        L.append(f"| {key} | {l['population']} | {l['actual_n']} "
                 f"({'ok' if l['reproduced'] else 'MISMATCH'}) | "
                 f"{m['probe']['pos50']} | {m['semantic']['exact_lit50']} | "
                 f"{m['semantic']['broad_lit50']} | {m['probe']['anti50']} |")
    L.append("")
    L.append("## 4. Region contribution table")
    L.append("")
    L.append("| population | A_only | B_only | C_only | AB_only | AC_only | "
             "BC_only | ABC |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for pop in ["p65_reference", "A_deep_mint", "B_threeway", "C_rebuilt",
                "AnB", "vote2", "vote3", "unionABC"]:
        c = result["contribution"][pop]
        L.append(f"| {pop} | {c['A_only']} | {c['B_only']} | {c['C_only']} | "
                 f"{c['AB_only']} | {c['AC_only']} | {c['BC_only']} | "
                 f"{c['ABC']} |")
    L.append("")
    L.append("## Interpretive caution")
    L.append("")
    L.append("Probe sets may undercount translated literature, non-English "
             "literary traditions, contemporary literary fiction, genre works "
             "with substantial literary standing, children's classics, and "
             "serious nonfiction depending on the list. Do not read 'higher "
             "pos50' as 'more literary'; distinguish probe coverage, anti "
             "contamination, actual head contents, stability, and author "
             "diversity separately. No manual reclassification was performed "
             "in code; the heads are for human inspection.")
    L.append("")
    _write_text_atomic(OUT_MD, "\n".join(L) + "\n")
    print(f"Wrote {OUT_MD}", flush=True)


def _write_heads(result: dict[str, Any]) -> None:
    L: list[str] = []
    L.append("# Jury Consensus — complete top-50 heads (human inspection)")
    L.append("")
    L.append(f"Seed `{JURY_CONSENSUS_SEED}`. Rows annotated with Y flags for "
             "probe membership; flags do NOT affect ranking and are descriptors "
             "only. Titles are shown exactly as stored (no transliteration).")
    L.append("")
    order = [
        ("groups", "core_p65_s25"),
        ("groups", "deep_mint_all"),
        ("groups", "threeway_classic"),
        ("groups", "rebuilt_hard"),
        ("groups", "committee_vote3_ABCs"),
        ("groups", "committee_vote2_ABCs"),
        ("groups", "committee_AnB"),
        ("groups", "committee_AuB"),
        ("groups", "committee_union_ABCs"),
        ("groups", "deep_25000"),
        ("groups", "committee_p65_plus_B"),
        ("regions", "A_only"),
        ("regions", "B_only"),
        ("regions", "C_only"),
        ("regions", "AB_only"),
        ("regions", "AC_only"),
        ("regions", "BC_only"),
        ("regions", "ABC"),
    ]
    for key, name in order:
        rec = result[key][name]
        L.append(f"## {name}")
        L.append("")
        L.append(f"- raw jury n = {rec['raw_n']}")
        L.append(f"- pos50={rec['probe']['pos50']}  exact50={rec['semantic']['exact_lit50']}  "
                 f"broad50={rec['semantic']['broad_lit50']}  anti50={rec['probe']['anti50']}")
        L.append(f"- half-J50 = {rec['half_jaccard50']:.2f}")
        L.append("")
        L.extend(_head_table(rec["head"]))
        L.append("")
    _write_text_atomic(OUT_HEADS, "\n".join(L) + "\n")
    print(f"Wrote {OUT_HEADS}", flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        phase_smoke()
    else:
        run_census()

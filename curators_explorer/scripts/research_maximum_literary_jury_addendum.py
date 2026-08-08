#!/usr/bin/env python3
"""MAXIMUM LITERARY JURY — correction + triage addendum (audit follow-up).

Focused corrections to the previous campaign (commit 4cc0bb9):

A. TRUE core-preserving frontier.  The old corepres_* frontier silently
   restricted the p65_s25 core to the 2,438 spectral-payload members.  Here we
   preserve ALL 3,286 original p65_s25 users (raw user IDs) and add model-ranked
   halo users from the payload.

B. Random-halo controls at 10k/20k/30k (5 deterministic replicates each).

C. Expansion of the already-large historical populations:
   - deep_mint_all (19,841) -> 25k/30k/40k/50k/60k
   - threeway_classic (31,803) -> 35k/40k/50k/60k/80k

D. Six fixed simple committee candidates over {deep_mint_all, threeway_classic,
   rebuilt_hard} (+ p65 UNION threeway_classic reference).

E. Optional one-step committee expansion ONLY if a committee candidate meets
   raw n >= 20,000, pos50 >= 18, anti50 <= 2.

Critical fix: the direct pairwise scorer ALWAYS uses the original build_pairs
route here (no payload-only pair cache), so non-payload historical users
contribute their pairs.  A smoke check re-scores the full 3,286 p65 core and
must reproduce pos50=42 / anti50=0 (the 2,438-payload-only result is ~39).

The existing behaviour-only elastic-net score (scores/binary_elasticnet) is
used ONLY as one provisional ordering of payload halo users.  No retraining.

Run:
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_maximum_literary_jury_addendum --smoke
  PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.research_maximum_literary_jury_addendum --run
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
    probe_metrics,
    load_sticky,
    _con,
)

MAX_JURY_ADDENDUM_SEED = 20260827

OUT_JSON = DATA / "maximum_literary_jury_addendum.json"
OUT_NPZ = DATA / "maximum_literary_jury_addendum.npz"
OUT_MD = DATA / "MAXIMUM_LITERARY_JURY_ADDENDUM_REPORT.md"

FULL_CORE_SIZES = [3286, 5000, 8000, 10000, 15000, 20000, 30000, 40000, 60000]
RANDOM_HALO_REPS = 5
RANDOM_HALO_SIZES = [10000, 20000, 30000]
DEEP_MINT_SIZES = [19841, 25000, 30000, 40000, 50000, 60000]
THREEWAY_SIZES = [31803, 35000, 40000, 50000, 60000, 80000]
COMMITTEE_EXPANSION_SIZES = [40000, 60000, 80000]

# ---------------------------------------------------------------------------
# Data / context loading
# ---------------------------------------------------------------------------

def load_old_arrays() -> dict[str, np.ndarray]:
    with np.load(OLD_NPZ, allow_pickle=False) as blob:
        return {k: blob[k] for k in blob.files}


def _open_db() -> Any:
    con = _con()
    con.execute("PRAGMA memory_limit='7GB'")
    con.execute("PRAGMA threads=8")
    return con


# ---------------------------------------------------------------------------
# Direct scoring (build_pairs route ONLY — never the payload-only cache)
# ---------------------------------------------------------------------------

_jury_counter = [0]


def _next_table() -> str:
    _jury_counter[0] += 1
    return f"adj_jury_{_jury_counter[0]}"


def score_jury_direct(
    con,
    user_ids: np.ndarray,
    *,
    weights: np.ndarray | None,
    ev_all: dict,
    sticky: set,
    limit: int = 200,
) -> dict[str, Any]:
    """Pairwise esteem via the original build_pairs route (arbitrary users)."""
    user_ids = np.asarray(user_ids, dtype=np.int64)
    if weights is None:
        weights = np.ones(len(user_ids), dtype=np.float64)
    table = _next_table()
    pairs = f"{table}_pairs"
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table}(user_id BIGINT, w DOUBLE)")
    con.execute(
        f"INSERT INTO {table} SELECT * FROM ("
        f"SELECT unnest(?::BIGINT[]) AS user_id, unnest(?::DOUBLE[]) AS w)",
        [user_ids.tolist(), weights.tolist()],
    )
    build_pairs(con, table, pairs)
    rows = rank_pairwise(con, pairs, "w")
    con.execute(f"DROP TABLE IF EXISTS {pairs}")
    con.execute(f"DROP TABLE IF EXISTS {table}")

    probe = probe_metrics(rows, ev_all, sticky)
    sem = {}
    for name in ("exact_lit", "broad_lit", "anti", "filler"):
        ids = ev_all.get(name, set())
        for k in (50, 100, 200):
            sem[f"{name}{k}"] = sum(r["work_id"] in ids for r in rows[:k])
    return {
        "raw_n": int(len(user_ids)),
        "probe": probe,
        "semantic": sem,
        "n_rows": int(len(rows)),
        "head": [
            {
                "rank": r["rank"], "work_id": r["work_id"], "title": r["title"],
                "author": r["author"], "score": float(r["score"]),
                "n_eff": float(r["n_eff"]),
            }
            for r in rows[:limit]
        ],
    }


def half_jaccard_direct(con, user_ids: np.ndarray, *, ev_all, sticky,
                        rng, n_splits: int = 2) -> dict[str, Any]:
    user_ids = np.asarray(user_ids, dtype=np.int64)
    jacs, rhos = [], []
    for _s in range(n_splits):
        r = rng.permutation(len(user_ids))
        h1 = user_ids[r[: len(user_ids) // 2]]
        h2 = user_ids[r[len(user_ids) // 2:]]
        a = score_jury_direct(con, h1, weights=None, ev_all=ev_all, sticky=sticky)["head"]
        b = score_jury_direct(con, h2, weights=None, ev_all=ev_all, sticky=sticky)["head"]
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
        "half_jaccard50_splits": n_splits,
        "half_rho200": float(np.mean(rhos)) if rhos else float("nan"),
    }


def score_and_halves(con, user_ids: np.ndarray, name: str, *, ev_all, sticky) -> dict[str, Any]:
    rec = score_jury_direct(con, user_ids, weights=None, ev_all=ev_all, sticky=sticky)
    half = half_jaccard_direct(
        con, user_ids, ev_all=ev_all, sticky=sticky,
        rng=np.random.default_rng(_derive_seed(MAX_JURY_ADDENDUM_SEED, "half", name)),
    )
    rec.update(half)
    rec["name"] = name
    return rec


def _rec_slim(rec: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in rec.items() if k != "head"}
    out["head_top30"] = rec["head"][:30]
    return out


# ---------------------------------------------------------------------------
# Halo ordering helpers (payload model-ranked, excluding a source set)
# ---------------------------------------------------------------------------

def halo_ordering(payload_ids: np.ndarray, scores: np.ndarray,
                  exclude: set[int]) -> np.ndarray:
    """Payload users not in `exclude`, sorted by score desc, user-id tiebreak."""
    ex = np.isin(payload_ids, np.fromiter(exclude, dtype=np.int64))
    idx = np.flatnonzero(~ex)
    ids = payload_ids[idx]
    sc = scores[idx]
    order = np.lexsort((ids, -sc))
    return ids[order]


def expand_jury(source: np.ndarray, halo: np.ndarray, target: int) -> np.ndarray:
    src = np.unique(np.asarray(source, dtype=np.int64))
    k = target - len(src)
    assert k >= 0, f"target {target} below source size {len(src)}"
    add = halo[:k]
    assert len(set(src) & set(add.tolist())) == 0, "halo overlap with source"
    return np.concatenate([src, add])


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------

def phase_smoke() -> dict[str, Any]:
    t0 = time.time()
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    old = load_old_arrays()
    payload = load_payload()
    payload_ids = payload["user_ids"].astype(np.int64)
    full_core = old["juries/core_p65_s25/user_ids"].astype(np.int64)
    add("full_p65_core_exactly_3286", len(full_core) == 3286,
        f"n={len(full_core)}")
    payload_set = set(payload_ids.tolist())
    non_payload = [u for u in full_core.tolist() if u not in payload_set]
    add("full_core_has_non_payload_members", len(non_payload) > 0,
        f"{len(non_payload)} of {len(full_core)} outside spectral payload")

    deep = old["juries/deep_mint_all/user_ids"].astype(np.int64)
    tc = old["juries/threeway_classic/user_ids"].astype(np.int64)
    add("deep_mint_exactly_19841", len(deep) == 19841, f"n={len(deep)}")
    add("threeway_classic_exactly_31803", len(tc) == 31803, f"n={len(tc)}")

    scores = old["scores/binary_elasticnet"].astype(np.float64)
    assert len(scores) == len(payload_ids)

    # committee logic on a synthetic example
    A = {1, 2, 3, 4}
    B = {3, 4, 5, 6}
    C = {4, 6, 7, 8}
    inter = A & B
    union = A | B
    vote2 = (A & B) | (A & C) | (B & C)
    vote3 = A & B & C
    add("committee_intersection_correct", inter == {3, 4}, f"{sorted(inter)}")
    add("committee_union_correct", union == {1, 2, 3, 4, 5, 6}, f"{sorted(union)}")
    add("committee_vote2_correct", vote2 == {3, 4, 6}, f"{sorted(vote2)}")
    add("committee_vote3_correct", vote3 == {4}, f"{sorted(vote3)}")
    add("vote2_counts_distinct_families",
        all(len([S for S in (A, B, C) if u in S]) >= 2 for u in vote2),
        "vote2 users appear in >=2 distinct source families")

    # deterministic random controls
    rng1 = np.random.default_rng(7)
    rng2 = np.random.default_rng(7)
    add("random_controls_deterministic",
        bool(np.array_equal(rng1.choice(10000, 500, replace=False),
                            rng2.choice(10000, 500, replace=False))),
        "same seed -> same draw")

    # random halo never samples core members
    core_set = set(full_core.tolist())
    halo = halo_ordering(payload_ids, scores, core_set)
    rng = np.random.default_rng(_derive_seed(MAX_JURY_ADDENDUM_SEED, "smoke_randhalo"))
    sample = rng.choice(halo, 500, replace=False)
    add("random_halo_disjoint_from_core",
        not (set(sample.tolist()) & core_set), "sample has zero core members")

    # core-preserving juries contain all 3286
    for size in [3286, 10000, 20000]:
        jury = expand_jury(full_core, halo, size)
        add(f"fullcore_{size}_contains_all_core",
            len(jury) == size and core_set <= set(jury.tolist()),
            f"n={len(jury)}, core subset ok")

    # direct scoring of full p65 reproduces historical result (non-payload users
    # must contribute their pairs via the build_pairs route)
    con = _open_db()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    _meta, eval_sets = load_posthoc_context(payload["work_ids"])
    ev_all = _merged_ev(ev, eval_sets)
    # historical full-core result uses the stored curator_pct weights
    core_w = old["juries/core_p65_s25/weights"].astype(np.float64)
    rec_w = score_jury_direct(con, full_core, weights=core_w, ev_all=ev_all,
                              sticky=sticky)
    add("full_p65_direct_reproduces_42_0",
        rec_w["probe"]["pos50"] == 42 and rec_w["probe"]["anti50"] == 0,
        f"weighted pos50={rec_w['probe']['pos50']} anti50={rec_w['probe']['anti50']} "
        f"Q={rec_w['probe']['Q_clean']}")
    # prove non-payload users actually contribute: payload-only core is weaker
    core_payload_only = np.asarray([u for u in full_core.tolist() if u in payload_set],
                                   dtype=np.int64)
    rec_eq = score_jury_direct(con, full_core, weights=None, ev_all=ev_all,
                               sticky=sticky)
    rec2 = score_jury_direct(con, core_payload_only, weights=None, ev_all=ev_all,
                             sticky=sticky)
    add("non_payload_users_matter",
        rec2["probe"]["pos50"] <= rec_eq["probe"]["pos50"] - 2,
        f"payload-only core pos50={rec2['probe']['pos50']} vs full-equal pos50={rec_eq['probe']['pos50']}")
    con.close()

    ok = all(c["ok"] for c in checks)
    print(f"[smoke] {sum(c['ok'] for c in checks)}/{len(checks)} checks passed "
          f"in {_fmt_time(time.time() - t0)}", flush=True)
    return {"checks": checks, "ok": bool(ok), "elapsed_s": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_addendum() -> dict[str, Any]:
    t0 = time.time()
    old = load_old_arrays()
    payload = load_payload()
    payload_ids = payload["user_ids"].astype(np.int64)
    scores = old["scores/binary_elasticnet"].astype(np.float64)
    assert len(scores) == len(payload_ids)

    full_core = old["juries/core_p65_s25/user_ids"].astype(np.int64)
    deep = old["juries/deep_mint_all/user_ids"].astype(np.int64)
    tc = old["juries/threeway_classic/user_ids"].astype(np.int64)
    rebuilt = old["juries/rebuilt_hard/user_ids"].astype(np.int64)
    assert len(full_core) == 3286 and len(deep) == 19841 and len(tc) == 31803

    con = _open_db()
    ev = load_eval_sets(con)
    sticky = set(load_sticky())
    materialize_base(con)
    _meta, eval_sets = load_posthoc_context(payload["work_ids"])
    ev_all = _merged_ev(ev, eval_sets)

    core_set = set(full_core.tolist())
    halo_from_core = halo_ordering(payload_ids, scores, core_set)

    juries: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {}
    checkpoint = DATA / "maximum_literary_jury_addendum_chunks.json"
    done: set[str] = set()
    if checkpoint.exists():
        blob = json.loads(checkpoint.read_text(encoding="utf-8"))
        juries = blob["juries"]
        done = {j["name"] for j in juries}

    def score_named(name: str, user_ids: np.ndarray, *, store: bool = True) -> dict[str, Any]:
        nonlocal juries
        if name in done:
            return next(j for j in juries if j["name"] == name)
        rec = score_and_halves(con, user_ids, name, ev_all=ev_all, sticky=sticky)
        if store:
            juries.append(_rec_slim(rec))
            arrays[f"juries/{name}/user_ids"] = user_ids.astype(np.int64)
            _write_text_atomic(checkpoint, json.dumps({"juries": juries}, indent=1))
            print(f"[run] {name}: n={rec['raw_n']} pos50={rec['probe']['pos50']} "
                  f"anti50={rec['probe']['anti50']} "
                  f"exact50={rec['semantic']['exact_lit50']} "
                  f"J50={rec['half_jaccard50']:.2f}", flush=True)
        return rec

    # ---- Part A: corrected full-core frontier ----
    for size in FULL_CORE_SIZES:
        jury = expand_jury(full_core, halo_from_core, size)
        assert core_set <= set(jury.tolist()), f"fullcore_{size} missing core"
        score_named(f"fullcore_{size}", jury)

    # ---- Part B: random-halo controls ----
    for size in RANDOM_HALO_SIZES:
        k = size - len(full_core)
        for rep in range(RANDOM_HALO_REPS):
            rng = np.random.default_rng(
                _derive_seed(MAX_JURY_ADDENDUM_SEED, "randhalo", size, rep))
            sel = rng.choice(halo_from_core, k, replace=False)
            assert not (set(sel.tolist()) & core_set), "random halo touched core"
            jury = np.concatenate([full_core, sel])
            score_named(f"randhalo_{size}_{rep}", jury)

    # ---- Part C: expansion of large historical juries ----
    deep_set = set(deep.tolist())
    halo_from_deep = halo_ordering(payload_ids, scores, deep_set)
    for size in DEEP_MINT_SIZES:
        jury = expand_jury(deep, halo_from_deep, size)
        assert deep_set <= set(jury.tolist()), f"deep_{size} missing source"
        score_named(f"deep_{size}", jury)

    tc_set = set(tc.tolist())
    halo_from_tc = halo_ordering(payload_ids, scores, tc_set)
    for size in THREEWAY_SIZES:
        jury = expand_jury(tc, halo_from_tc, size)
        assert tc_set <= set(jury.tolist()), f"threeway_{size} missing source"
        score_named(f"threeway_{size}", jury)

    # ---- Part D: six fixed committee candidates ----
    A = deep_set
    B = tc_set
    C = set(rebuilt.tolist())
    committees = {
        "committee_AnB": sorted(A & B),
        "committee_AuB": sorted(A | B),
        "committee_vote2_ABCs": sorted((A & B) | (A & C) | (B & C)),
        "committee_vote3_ABCs": sorted(A & B & C),
        "committee_union_ABCs": sorted(A | B | C),
        "committee_p65_plus_B": sorted(core_set | B),
    }
    committee_meta = {
        name: {
            "raw_n": len(users),
            "n_A": len(set(users) & A),
            "n_B": len(set(users) & B),
            "n_C": len(set(users) & C),
        }
        for name, users in committees.items()
    }
    for name in sorted(committees):
        score_named(name, np.asarray(committees[name], dtype=np.int64))

    # ---- Part E: optional committee expansion ----
    gate_candidates = [
        r for r in juries
        if r["name"] in committees
        and r["raw_n"] >= 20000 and r["probe"]["pos50"] >= 18
        and r["probe"]["anti50"] <= 2
    ]
    part_e: dict[str, Any] = {"performed": False, "gate_candidates": [
        {"name": r["name"], "raw_n": r["raw_n"], "pos50": r["probe"]["pos50"],
         "anti50": r["probe"]["anti50"], "half_jaccard50": r["half_jaccard50"]}
        for r in gate_candidates
    ]}
    if gate_candidates:
        best = max(gate_candidates, key=lambda r: (r["probe"]["pos50"],
                                                   r["raw_n"],
                                                   r["half_jaccard50"]))
        base_name = best["name"]
        base_users = np.asarray(committees[base_name], dtype=np.int64)
        base_set = set(base_users.tolist())
        halo_from_base = halo_ordering(payload_ids, scores, base_set)
        expansions = [s for s in COMMITTEE_EXPANSION_SIZES if s > len(base_users)]
        part_e["performed"] = True
        part_e["committee_base"] = base_name
        part_e["committee_base_n"] = int(len(base_users))
        part_e["expansion_sizes"] = expansions
        for size in expansions:
            jury = expand_jury(base_users, halo_from_base, size)
            assert base_set <= set(jury.tolist()), f"{base_name}_{size} missing base"
            score_named(f"{base_name}_{size}", jury)

    # ---- finalize ----
    con.close()
    result = {
        "seed": MAX_JURY_ADDENDUM_SEED,
        "full_core_n": len(full_core),
        "full_core_payload_overlap": len(core_set & set(payload_ids.tolist())),
        "juries": juries,
        "committee_meta": committee_meta,
        "part_e": part_e,
        "elapsed_s": round(time.time() - t0, 1),
    }
    arrays["user_ids"] = payload_ids
    arrays["full_core"] = full_core
    _write_npz_atomic(OUT_NPZ, arrays)
    _write_text_atomic(OUT_JSON, json.dumps(result, indent=1, default=_json_default))
    _write_report(result)
    print(f"[run] done in {_fmt_time(time.time() - t0)}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _head_str(head: list[dict], n: int = 30) -> list[str]:
    return [f"{r['rank']}. {r['title']} — {r['author']}" for r in head[:n]]


def _frontier_rows(juries, prefix: str, order=None) -> list[dict]:
    rows = [r for r in juries if r["name"].startswith(prefix)]
    return sorted(rows, key=lambda r: r["name"])


def _write_report(result: dict[str, Any]) -> None:
    juries = result["juries"]
    by_name = {r["name"]: r for r in juries}
    L: list[str] = []
    L.append("# Maximum Literary Jury — Correction & Triage Addendum")
    L.append("")
    L.append(f"- Seed `{MAX_JURY_ADDENDUM_SEED}`; full p65 core n={result['full_core_n']} "
             f"(payload overlap {result['full_core_payload_overlap']}); "
             f"old artifacts untouched.")
    L.append("")
    L.append("## Audit correction being tested")
    L.append("")
    L.append("The old corepres_* frontier dropped 848 trusted p65_s25 members "
             "(only the 2,438 spectral-payload members were kept). This addendum "
             "preserves ALL 3,286 raw core users and adds model-ranked halo users "
             "from the payload. The pairwise scorer always uses the original "
             "build_pairs route, so non-payload users contribute their pairs.")
    L.append("")
    L.append("## Correct full-p65 frontier (all juries contain all 3,286 core users)")
    L.append("")
    L.append("| jury | n | pos50 | exact50 | broad50 | anti50 | half-J50 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in _frontier_rows(juries, "fullcore_"):
        L.append(f"| {r['name']} | {r['raw_n']} | {r['probe']['pos50']} | "
                 f"{r['semantic']['exact_lit50']} | {r['semantic']['broad_lit50']} | "
                 f"{r['probe']['anti50']} | {r['half_jaccard50']:.2f} |")
    L.append("")
    L.append("## Full-core model-halo vs random-halo controls")
    L.append("")
    L.append("| size | halo type | pos50 mean (min-max) | anti50 mean (min-max) | half-J50 mean |")
    L.append("|---|---:|---:|---:|---:|")
    for size in RANDOM_HALO_SIZES:
        model = by_name.get(f"fullcore_{size}")
        rand = [by_name[f"randhalo_{size}_{rep}"] for rep in range(RANDOM_HALO_REPS)]
        m_pos = model["probe"]["pos50"] if model else float("nan")
        r_pos = [r["probe"]["pos50"] for r in rand]
        r_anti = [r["probe"]["anti50"] for r in rand]
        r_j = [r["half_jaccard50"] for r in rand]
        L.append(
            f"| {size} | model-halo | {m_pos:.0f} | "
            f"{model['probe']['anti50'] if model else float('nan'):.0f} | "
            f"{model['half_jaccard50'] if model else float('nan'):.2f} |")
        L.append(
            f"| {size} | random-halo | {np.mean(r_pos):.1f} "
            f"({min(r_pos)}-{max(r_pos)}) | {np.mean(r_anti):.1f} "
            f"({min(r_anti)}-{max(r_anti)}) | {np.mean(r_j):.2f} |")
    L.append("")
    L.append("## Deep-mint expansion frontier (all juries contain all 19,841 source users)")
    L.append("")
    L.append("| jury | n | pos50 | exact50 | broad50 | anti50 | half-J50 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in _frontier_rows(juries, "deep_"):
        L.append(f"| {r['name']} | {r['raw_n']} | {r['probe']['pos50']} | "
                 f"{r['semantic']['exact_lit50']} | {r['semantic']['broad_lit50']} | "
                 f"{r['probe']['anti50']} | {r['half_jaccard50']:.2f} |")
    L.append("")
    L.append("## Threeway-classic expansion frontier (all juries contain all 31,803 source users)")
    L.append("")
    L.append("| jury | n | pos50 | exact50 | broad50 | anti50 | half-J50 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in _frontier_rows(juries, "threeway_"):
        L.append(f"| {r['name']} | {r['raw_n']} | {r['probe']['pos50']} | "
                 f"{r['semantic']['exact_lit50']} | {r['semantic']['broad_lit50']} | "
                 f"{r['probe']['anti50']} | {r['half_jaccard50']:.2f} |")
    L.append("")
    L.append("## Simple committee populations")
    L.append("")
    L.append("| candidate | n | A count | B count | C count | pos50 | exact50 | anti50 | half-J50 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for name in sorted(committees := result["committee_meta"]):
        r = by_name.get(name)
        if not r:
            continue
        m = committees[name]
        L.append(f"| {name} | {r['raw_n']} | {m['n_A']} | {m['n_B']} | {m['n_C']} | "
                 f"{r['probe']['pos50']} | {r['semantic']['exact_lit50']} | "
                 f"{r['probe']['anti50']} | {r['half_jaccard50']:.2f} |")
    L.append("")
    L.append("## Optional committee expansion")
    L.append("")
    pe = result["part_e"]
    if pe["performed"]:
        L.append(f"- Gate passed: committee base `{pe['committee_base']}` "
                 f"(n={pe['committee_base_n']}); expansions {pe['expansion_sizes']}.")
        L.append("")
        L.append("| jury | n | pos50 | anti50 | half-J50 |")
        L.append("|---|---:|---:|---:|---:|")
        for r in _frontier_rows(juries, f"{pe['committee_base']}_"):
            L.append(f"| {r['name']} | {r['raw_n']} | {r['probe']['pos50']} | "
                     f"{r['probe']['anti50']} | {r['half_jaccard50']:.2f} |")
    else:
        L.append("- Gate NOT met (no committee candidate with raw n>=20,000, "
                 "pos50>=18, anti50<=2); no expansion performed.")
    L.append("")
    L.append("## Triage conclusion")
    L.append("")
    L.append("### A. Did preserving the missing 848 p65 users materially improve the "
             "previous 10k/20k frontier?")
    old10 = next((r for r in juries if r["name"] == "fullcore_10000"), None)
    old20 = next((r for r in juries if r["name"] == "fullcore_20000"), None)
    L.append(f"- fullcore_10000 pos50={old10['probe']['pos50'] if old10 else '?'} "
             f"(old payload-only corepres_10000 was 19). "
             f"fullcore_20000 pos50={old20['probe']['pos50'] if old20 else '?'} "
             f"(old payload-only corepres_20000 was 11).")
    L.append("")
    L.append("### B. Can the 19,841 deep-mint population be expanded past 20k?")
    for r in _frontier_rows(juries, "deep_"):
        if r["raw_n"] in (25000, 30000, 40000):
            L.append(f"- deep_{r['raw_n']}: pos50={r['probe']['pos50']}, "
                     f"anti50={r['probe']['anti50']}")
    L.append("")
    L.append("### C. Can the 31,803 threeway-classic population be expanded beyond ~32k?")
    for r in _frontier_rows(juries, "threeway_"):
        if r["raw_n"] >= 35000:
            L.append(f"- threeway_{r['raw_n']}: pos50={r['probe']['pos50']}, "
                     f"anti50={r['probe']['anti50']}")
    L.append("")
    L.append("### D. Do simple intersections/unions/votes beat their sources?")
    for name in sorted(result["committee_meta"]):
        r = by_name.get(name)
        if r:
            L.append(f"- {name}: n={r['raw_n']}, pos50={r['probe']['pos50']}, "
                     f"anti50={r['probe']['anti50']}")
    L.append("")
    L.append("### E. Largest observed jury under the candidates tested here")
    L.append("")
    L.append("| threshold | largest observed jury | n | pos50 | anti50 |")
    L.append("|---|---|---:|---:|---:|")
    for pos_thr in (20, 15, 10):
        cands = [r for r in juries
                 if r["probe"]["pos50"] >= pos_thr and r["probe"]["anti50"] <= 2]
        if cands:
            best = max(cands, key=lambda r: r["raw_n"])
            L.append(f"| pos50>={pos_thr} & anti50<=2 | {best['name']} | {best['raw_n']} | "
                     f"{best['probe']['pos50']} | {best['probe']['anti50']} |")
        else:
            L.append(f"| pos50>={pos_thr} & anti50<=2 | none | - | - | - |")
    L.append("")
    L.append("These are largest *observed* under the candidates tested in this "
             "addendum, not universal maxima.")
    L.append("")
    _write_text_atomic(OUT_MD, "\n".join(L) + "\n")
    print(f"Wrote {OUT_MD}", flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        phase_smoke()
    else:
        run_addendum()

"""Trench-coat test: are large-jury literary endpoints (80k/110k) superpositions
of several taste schools?

Theory (user): an 80k jury is a mixture of multiple literary canons; the whole
cannot fit in a single small basin, so its endpoint mixes basins (Karamazov +
C&P + HP + Maus in one head).  Splitting the SAME user set into smaller groups
and re-running the reversal should make groups resolve into PURER, possibly
DISTINCT basins.

Random splits are the baseline; the interesting splits are DETERMINISTIC
(label-free) ways of separating taste schools inside the jury:
  mode2    - sign of the 2nd left singular vector of the parent submatrix
             (the classic "two taste schools" decomposition)
  mode2q3  - 3 quantile groups on the 2nd mode loading
  affinity - median split by each user's cos with the parent endpoint pref
             (agreed-with-compromise vs dissented)
Random splits are included for comparison.

Replay trick: the sweep's only rng consumption is make_jury_seed's
rng.choice(...) (iterate_map and remove_fraction gain/hard are rng-free), so
the exact user set of every stored jury can be recovered by replaying the same
choice calls in the same order -- no matrix work.  Verified bit-for-bit.

Phases:
  verify  -- re-run a jury on its recovered users; must reproduce the stored
             endpoint exactly.
  split   -- recover user sets, split literary/control parents by method,
             run the standard reversal on each subgroup, store endpoints.
  analyze -- per-method inheritance vs the 20k baseline (29% >= 3), purity,
             basin resolution, and the "reveal" test (do deterministic
             splits find literary schools inside control juries?).

Same machinery as the drift exploit: run_jury (retained_target 1.01,
evidence floor), preference_head scoring, greedy direction clustering.
Honesty: parents are selected with eval-set labels; subgroup dynamics and
final scoring are label-free until the very last step.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import svds

from curators_explorer.scripts import (
    research_attractor_pruning as pruning,
)
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year
from curators_explorer.scripts.research_jury_ensemble_reversal import (
    preference_head,
    run_jury,
)
from curators_explorer.scripts.research_reversal_drift_exploit import POLE_KEY

DATA = Path(__file__).resolve().parents[1] / "data"
MAIN_TAG = "main"
MAIN_SEED = 20260811
MAIN_SIZES = [20000, 30000, 45000, 60000, 80000, 110000]
MAIN_JURIES = 120
RETAINED_TARGET = 1.01

METHODS = ["random", "mode2", "mode2q3", "affinity"]
METHOD_BASE = {"random": 0, "mode2": 10, "mode2q3": 20, "affinity": 30}


def replay_jury_users(
    payload: dict[str, np.ndarray], seed: int, sizes: list[int], juries: int
) -> dict[tuple[int, int], np.ndarray]:
    """Recover the exact user set of every jury from the main sweep (rng replay)."""
    n_users = len(payload["user_ids"])
    rng = np.random.default_rng(seed)
    out: dict[tuple[int, int], np.ndarray] = {}
    for size in sizes:
        for j in range(juries):
            selected = np.sort(rng.choice(n_users, size=min(size, n_users), replace=False))
            out[(size, j)] = selected
    return out


def build_subgroup_start(
    payload: dict[str, np.ndarray], users: np.ndarray
) -> np.ndarray:
    """Same seed construction as make_jury_seed, restricted to a user subset."""
    n_users = len(payload["user_ids"])
    start = np.full(n_users, 0.4, dtype=np.float32)
    start[users] = 20.0
    start /= start.mean()
    return start


def parent_submatrix(payload: dict[str, np.ndarray], users: np.ndarray):
    """Normalized user x book matrix restricted to `users`, plus the local
    indices of users with both positive and negative ratings."""
    sub = pruning.subset_payload(payload, users)
    row, col, side = sub["row"], sub["col"], sub["side"]
    n_users, n_books = len(sub["user_ids"]), len(sub["work_ids"])
    pos = np.bincount(row[side > 0], minlength=n_users).astype(np.float32)
    neg = np.bincount(row[side < 0], minlength=n_users).astype(np.float32)
    valid = (pos > 0) & (neg > 0)
    edge_keep = valid[row]
    lrow, lcol, lside = row[edge_keep], col[edge_keep], side[edge_keep]
    values = np.where(
        lside > 0, 0.5 / pos[lrow], -0.5 / neg[lrow]
    ).astype(np.float32)
    M = coo_matrix((values, (lrow, lcol)), shape=(n_users, n_books)).tocsr()
    return M, valid


def split_by_method(
    payload: dict[str, np.ndarray],
    users: np.ndarray,
    method: str,
    rng: np.random.Generator,
    pref: np.ndarray,
    n_groups: int,
) -> list[tuple[str, int, np.ndarray]]:
    """Return (method, group_index, user_subset) groups."""
    if method == "random":
        perm = rng.permutation(users)
        n = len(perm)
        sizes = [n // n_groups + (1 if i < n % n_groups else 0) for i in range(n_groups)]
        out = []
        at = 0
        for s in sizes:
            out.append(np.sort(perm[at : at + s]))
            at += s
        return [("random", i, g) for i, g in enumerate(out)]

    M, valid = parent_submatrix(payload, users)
    loc_valid = np.flatnonzero(valid)
    v_users = users[loc_valid]
    if method == "affinity":
        rows = M[loc_valid]
        pn = pref / max(np.linalg.norm(pref), 1e-12)
        Apn = np.asarray(rows @ pn).ravel()
        sq = np.asarray(rows.multiply(rows).sum(axis=1)).ravel()
        norm = np.sqrt(np.maximum(sq, 1e-12))
        c = Apn / norm
        med = float(np.median(c))
        return [
            ("affinity", 0, np.sort(v_users[c >= med])),
            ("affinity", 1, np.sort(v_users[c < med])),
        ]

    try:
        u, s, _ = svds(M, k=2, v0=np.ones(M.shape[1], dtype=np.float32))
    except TypeError:
        u, s, _ = svds(M, k=2)
    v = u[:, 1][loc_valid]
    if method == "mode2":
        return [
            ("mode2", 0, np.sort(v_users[v > 0])),
            ("mode2", 1, np.sort(v_users[v < 0])),
        ]
    q1, q2 = np.quantile(v, [1.0 / 3, 2.0 / 3])
    return [
        ("mode2q3", 0, np.sort(v_users[v < q1])),
        ("mode2q3", 1, np.sort(v_users[(v >= q1) & (v < q2)])),
        ("mode2q3", 2, np.sort(v_users[v >= q2])),
    ]


def load_main_analysis() -> dict[str, Any]:
    return json.loads(
        (DATA / "drift_exploit_main_all_analysis.json").read_text(encoding="utf-8")
    )


def phase_split(args) -> None:
    payload, matrix, _ = year.load_matrix()
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])

    methods = METHODS if args.split_method == "all" else [args.split_method]

    users_by_key = replay_jury_users(payload, MAIN_SEED, MAIN_SIZES, MAIN_JURIES)
    recs = json.loads(
        (DATA / "drift_exploit_main.json").read_text(encoding="utf-8")
    )["records"]

    if args.parents:
        parents = [int(x) for x in args.parents.split(",")]
        parent_recs = [dict(recs[i], idx=i, role="manual") for i in parents]
    else:
        analysis = load_main_analysis()
        lit: list[dict[str, Any]] = []
        for d in analysis["amplified"]:
            if d["kind"] != "drifter":
                continue
            if d.get("source_exact50", 0) < 3:
                continue
            idx = int(d["seed"].split(":")[1])
            size = recs[idx]["size"]
            if size not in (80000, 110000):
                continue
            lit.append(dict(recs[idx], idx=idx, src_exact=d.get("source_exact50", 0)))
        lit.sort(key=lambda r: -r["src_exact"])
        for r in lit:
            r.pop("src_exact", None)
        if len(lit) > args.max_lit:
            lit = lit[: args.max_lit]
        # controls: exact-0 juries at 80k/110k, scored from the stored prefs
        npz_blob = np.load(DATA / f"drift_exploit_{MAIN_TAG}.npz")
        ctrl_cand: list[dict[str, Any]] = []
        for i, r in enumerate(recs):
            if r["size"] not in (80000, 110000):
                continue
            _, m = preference_head(
                npz_blob["prefs"][i], payload, meta, eval_sets, limit=50
            )
            if m["exact_lit50"] == 0:
                ctrl_cand.append(dict(r, idx=i))
        if len(ctrl_cand) > args.max_ctrl:
            rng = np.random.default_rng(args.seed)
            ctrl_cand = list(rng.choice(ctrl_cand, size=args.max_ctrl, replace=False))
        parent_recs = [dict(r, role="literary") for r in lit] + [
            dict(r, role="control") for r in ctrl_cand
        ]
    print(
        f"parents: {[(r['idx'], r['size'], r['role']) for r in parent_recs]}",
        flush=True,
    )

    pole = np.load(DATA / "canon_breeding_overnight_directions.npz", allow_pickle=True)[
        POLE_KEY
    ].astype(np.float64)

    directions: list[np.ndarray] = []
    prefs: list[np.ndarray] = []
    stage0_prefs: list[np.ndarray] = []
    records: list[dict[str, Any]] = []

    def run_group(
        parent: dict[str, Any], method: str, group: int, users: np.ndarray
    ) -> None:
        rng = np.random.default_rng(
            args.seed + 1000 * parent["idx"] + METHOD_BASE[method] + group
        )
        start = build_subgroup_start(payload, users)
        run = run_jury(payload, matrix, start, rng, RETAINED_TARGET)
        deep = run["stages"][-1]
        head, m = preference_head(run["final_pref"], payload, meta, eval_sets, limit=200)
        direction = deep["direction"].astype(np.float64)
        cos_pole = float(
            np.sum(direction * pole)
            / (np.linalg.norm(direction) * np.linalg.norm(pole) + 1e-20)
        )
        pd = parent["direction"].astype(np.float64)
        cos_parent = float(
            np.sum(direction * pd)
            / (np.linalg.norm(direction) * np.linalg.norm(pd) + 1e-20)
        )
        directions.append(direction.astype(np.float32))
        prefs.append(run["final_pref"])
        stage0_prefs.append(run["stage0_pref"])
        records.append(
            {
                "parent_idx": parent["idx"],
                "parent_size": parent["size"],
                "parent_role": parent["role"],
                "method": method,
                "group": group,
                "group_size": int(len(users)),
                "stop_reason": run["stop_reason"],
                "n_stages": len(run["stages"]),
                "remaining_users": deep["remaining_users"],
                "cos_pole": cos_pole,
                "cos_parent": cos_parent,
                "exact50": m["exact_lit50"],
                "broad50": m["broad_lit50"],
                "anti50": m["anti50"],
                "exact200": m["exact_lit200"],
                "head": [h["title"] for h in head[:12]],
            }
        )

    npz_blob = np.load(DATA / f"drift_exploit_{MAIN_TAG}.npz")
    parent_prefs = npz_blob["prefs"]
    total = 0
    t0 = time.time()
    for parent in parent_recs:
        idx, size = parent["idx"], parent["size"]
        j = idx - MAIN_SIZES.index(size) * MAIN_JURIES
        users = users_by_key[(size, j)]
        rng = np.random.default_rng(args.seed + idx)
        _, m = preference_head(parent_prefs[idx], payload, meta, eval_sets, limit=50)
        parent["exact50"] = m["exact_lit50"]
        parent["anti50"] = m["anti50"]
        if parent["role"] == "manual":
            parent["role"] = "literary" if m["exact_lit50"] >= 3 else "control"
        head, _ = preference_head(parent_prefs[idx], payload, meta, eval_sets, limit=12)
        parent["head"] = [h["title"] for h in head]
        parent["direction"] = npz_blob["directions"][idx]
        n_groups = 5 if size >= 110000 else 4
        for method in methods:
            for mth, g, part in split_by_method(
                payload, users, method, rng, parent_prefs[idx], n_groups
            ):
                run_group(parent, mth, g, part)
                total += 1
        if args.ladder and idx in [int(x) for x in args.ladder.split(",")]:
            rng2 = np.random.default_rng(args.seed + idx + 200_000)
            for n_groups, base in ((2, 200), (8, 300)):
                for mth, g, part in split_by_method(
                    payload, users, "random", rng2, parent_prefs[idx], n_groups
                ):
                    run_group(parent, mth, base + g, part)
                    total += 1
        print(
            f"parent {idx} ({size}, {parent['role']}): {total} subgroups done, "
            f"elapsed {time.time() - t0:.0f}s", flush=True,
        )

    npz_out = DATA / f"split_{args.tag}.npz"
    json_out = DATA / f"split_{args.tag}.json"
    np.savez_compressed(
        npz_out,
        directions=np.asarray(directions),
        prefs=np.asarray(prefs),
        stage0_prefs=np.asarray(stage0_prefs),
    )
    json_out.write_text(
        json.dumps(
            {
                "records": records,
                "parents": [
                    {k: p[k] for k in ("idx", "size", "role", "exact50", "anti50", "head")}
                    for p in parent_recs
                ],
                "partial": False,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {npz_out} ({len(directions)} subgroup runs)", flush=True)
    print(f"Wrote {json_out}", flush=True)


def phase_verify(args) -> None:
    """Bit-for-bit check that recovered user sets reproduce the stored endpoints."""
    payload, matrix, _ = year.load_matrix()
    users_by_key = replay_jury_users(payload, MAIN_SEED, MAIN_SIZES, MAIN_JURIES)
    npz_blob = np.load(DATA / f"drift_exploit_{MAIN_TAG}.npz")
    for key in args.verify:
        size, j = int(key.split(":")[0]), int(key.split(":")[1])
        users = users_by_key[(size, j)]
        start = build_subgroup_start(payload, users)
        rng = np.random.default_rng(MAIN_SEED)  # rng is never consumed by run_jury
        run = run_jury(payload, matrix, start, rng, RETAINED_TARGET)
        stored = npz_blob["prefs"][MAIN_SIZES.index(size) * MAIN_JURIES + j]
        same = np.array_equal(run["final_pref"], stored)
        maxdiff = float(np.max(np.abs(run["final_pref"] - stored)))
        print(f"verify {key}: identical={same} maxdiff={maxdiff:.3e}", flush=True)


def phase_analyze(args) -> None:
    blob = json.loads((DATA / f"split_{args.tag}.json").read_text(encoding="utf-8"))
    records, parents = blob["records"], blob["parents"]
    baseline_ge3 = 0.2916667  # 35/120 at 20k in the main sweep

    result: dict[str, Any] = {"baseline_20k_frac_ge3": baseline_ge3}
    parents_by_idx = {p["idx"]: p for p in parents}

    def stats(sub: list[dict[str, Any]]) -> dict[str, Any]:
        if not sub:
            return {"n": 0}
        ex = np.asarray([r["exact50"] for r in sub], dtype=np.float64)
        return {
            "n": len(sub),
            "frac_exact_ge3": float(np.mean(ex >= 3)),
            "frac_exact_ge1": float(np.mean(ex >= 1)),
            "mean_exact": float(ex.mean()),
            "max_exact": int(ex.max()),
            "mean_cos_pole": float(np.mean([r["cos_pole"] for r in sub])),
        }

    # per-method inheritance, by parent role
    by_method: dict[str, dict[str, Any]] = {}
    for method in METHODS:
        by_method[method] = {
            role: stats(
                [r for r in records if r["method"] == method and r["parent_role"] == role]
            )
            for role in ("literary", "control")
        }
    for method, d in by_method.items():
        for role, s in d.items():
            if s.get("n"):
                s["enrichment_vs_baseline"] = s["frac_exact_ge3"] / baseline_ge3
    result["by_method"] = by_method

    # reveal test: per-method per-parent detail for controls
    reveal: list[dict[str, Any]] = []
    for method in METHODS:
        for r in [r for r in records if r["method"] == method and r["parent_role"] == "control"]:
            if r["exact50"] >= 1:
                reveal.append(
                    {
                        "parent_idx": r["parent_idx"],
                        "parent_head": parents_by_idx[r["parent_idx"]]["head"][:4],
                        "method": method,
                        "exact": r["exact50"],
                        "anti": r["anti50"],
                        "cos_pole": round(r["cos_pole"], 3),
                        "head": r["head"][:6],
                    }
                )
    result["reveal_controls"] = reveal

    # purity + resolution per literary parent per method
    purity: list[dict[str, Any]] = []
    for pidx in sorted(parents_by_idx):
        if parents_by_idx[pidx]["role"] != "literary":
            continue
        for method in METHODS:
            subs = [
                r for r in records
                if r["parent_idx"] == pidx and r["method"] == method and r["group"] < 200
            ]
            if len(subs) < 2:
                continue
            purity.append(
                {
                    "parent_idx": pidx,
                    "method": method,
                    "n_groups": len(subs),
                    "subgroup_exact": [r["exact50"] for r in subs],
                    "subgroup_anti": [r["anti50"] for r in subs],
                    "cos_parent": [round(r["cos_parent"], 3) for r in subs],
                    "heads": [r["head"][:5] for r in subs],
                }
            )
    result["purity_by_parent_method"] = purity

    out = DATA / f"split_{args.tag}_analysis.json"
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"Wrote {out}", flush=True)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("purity_by_parent_method", "reveal_controls")},
            indent=1,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["split", "analyze", "verify"], required=True)
    parser.add_argument("--tag", default="main")
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--parents", type=str, default="")
    parser.add_argument("--split-method", choices=METHODS + ["all"], default="all")
    parser.add_argument("--max-lit", type=int, default=12)
    parser.add_argument("--max-ctrl", type=int, default=6)
    parser.add_argument("--ladder", default="")
    parser.add_argument("--cluster-threshold", type=float, default=0.5)
    parser.add_argument("--verify", nargs="+", default=["80000:0"])
    args = parser.parse_args()
    if args.phase == "verify":
        phase_verify(args)
    elif args.phase == "split":
        phase_split(args)
    else:
        phase_analyze(args)


if __name__ == "__main__":
    main()

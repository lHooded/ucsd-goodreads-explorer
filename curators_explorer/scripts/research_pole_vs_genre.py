"""Dawn experiment: cross the literary pole (T.s5xT.s3::dm) against the genre
dominant basin (pairwise_bilateral::s4) and the contrastive literary basin.

Pole parent = the canonical readers of the 17/23/12 child (its deepest survivor
set, weight 20 / 0.4) plus its deepest direction; genre parents rebuilt by
re-running their deterministic paths.
"""
import json, sys
import numpy as np
sys.path.insert(0, "/home/ifrankling/unsw/novels")
from curators_explorer.scripts import research_attractor_pruning as pruning
from curators_explorer.scripts import research_attractor_pruning_audit as audit
from curators_explorer.scripts import research_attractor_pruning_preexisting as preexisting
from curators_explorer.scripts import research_seedless_attractor_census as attractor
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts import research_year_aware_canon as year
from curators_explorer.scripts.research_canon_breeding import (
    run_path, jury_mix_start, direction_mix_start, classify, make_parent_starts,
)
from collections import Counter

DATA = "/home/ifrankling/unsw/novels/curators_explorer/data"
TAG = "pole_vs_genre"
SEED = 20260809
REPS = 30

payload, matrix, matrix_meta = year.load_matrix()
n_users = len(payload["user_ids"])
meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])
rng = np.random.default_rng(SEED)

npz = np.load(f"{DATA}/canon_breeding_overnight_directions.npz", allow_pickle=True)

def pole_parent():
    # rebuild the pole child's deterministic start (direction_mix of the
    # teacher parents) and re-run its path with converged weights saved
    starts = make_parent_starts(payload)
    teacher_runs = {}
    for name in ("teacher_p65_s25",):
        teacher_runs[name] = run_path(payload, matrix, starts[name][0], rng, store_weights=True)
    t = teacher_runs["teacher_p65_s25"]
    s5 = len(t["stages"]) - 1
    s3 = max(i for i, st in enumerate(t["stages"]) if st["stage"] == 3)
    pool_s = {
        "s5": {"canon_direction": t["directions"][s5]},
        "s3": {"canon_direction": t["directions"][s3]},
    }
    start = direction_mix_start(payload, pool_s, "s5", "s3")
    run = run_path(payload, matrix, start, rng, store_weights=True)
    deepest = len(run["stages"]) - 1
    keep = run["surviving"][deepest]
    d = run["directions"][deepest].astype(np.float64)
    w = run["weights_store"][deepest].astype(np.float64)
    print(f"pole rebuilt: stages={len(run['stages'])} survivors={keep.size} "
          f"selfcorr={np.sum(run['directions'][deepest]*run['directions'][deepest-1]):.4f}")
    return {"canon_direction": d, "weights": w, "surviving": keep, "name": "pole"}

def path_parent(name, start):
    run = run_path(payload, matrix, start, rng, store_weights=True)
    deepest = len(run["stages"]) - 1
    return {
        "canon_direction": run["directions"][deepest],
        "weights": run["weights_store"][deepest],
        "surviving": run["surviving"][deepest], "name": name,
    }

titles_p = json.load(open(f"{DATA}/pairwise_esteem.json"))["methods"]["pairwise_bilateral"]["top15"]
pairwise_start, _ = preexisting.start_from_book_titles(
    payload, [r["title"] for r in titles_p], meta
)
p4 = path_parent("pairwise_bilateral::s4", pairwise_start)

print(f"pole survivors {pole_parent()['surviving'].size}; p4 survivors {p4['surviving'].size}")

parents = {"pole": pole_parent(), "pairwise_bilateral::s4": p4}
print("pole x p4 corr:", round(float(np.sum(parents['pole']['canon_direction'] * parents['pairwise_bilateral::s4']['canon_direction'])), 3))

def fake_entry(p):
    keep = p["surviving"]
    w = p["weights"][keep] if p["weights"].size == len(payload["user_ids"]) else p["weights"]
    return {"run": {"surviving": np.array([keep]), "weights_store": {0: w}}, "canon_stage": 0}

children = []
def record(name, a, b, mode, rep, start):
    run = run_path(payload, matrix, start, rng, store_pref=True)
    deepest = len(run["stages"]) - 1
    cos = {p: float(np.sum(run["directions"][deepest] * parents[p]["canon_direction"])) for p in parents}
    pref = run["pref_store"][deepest]
    head, m = attractor.posthoc_head(pref, payload["work_ids"], meta, eval_sets, limit=200)
    c = classify({p: [cos[p]] for p in parents}, 0)
    children.append({
        "name": name, "a": a, "b": b, "mode": mode, "rep": rep,
        "stages": len(run["stages"]), "stop": run["stop_reason"],
        "cos": cos, "class": c,
        "exact50": m["exact_lit50"], "broad50": m["broad_lit50"], "anti50": m["anti50"],
        "survivors": int(run["surviving"][deepest].size),
        "head": [h["title"] for h in head[:10]],
    })
    print(f"{name}: class={c} cos={ {k: round(v,3) for k,v in cos.items()} } exact={m['exact_lit50']} broad={m['broad_lit50']} anti={m['anti50']} surv={run['surviving'][deepest].size}", flush=True)

pairs = [("pole", "pairwise_bilateral::s4"), ("pole", "contrastive_careful::s4")]
titles_c = json.load(open(f"{DATA}/threeway_unseeded.json"))["rankings"]["unseeded_contrastive"]["top25"]
contrastive_start, _ = preexisting.start_from_book_titles(
    payload, [r["title"] for r in titles_c], meta
)
c4 = path_parent("contrastive_careful::s4", contrastive_start)
parents["contrastive_careful::s4"] = c4
print("pole x c4 corr:", round(float(np.sum(parents['pole']['canon_direction'] * parents['contrastive_careful::s4']['canon_direction'])), 3))

for (a, b) in pairs:
    for rep in range(REPS):
        record(f"{a}x{b}::jm::r{rep}", a, b, "jury_mix", rep,
               jury_mix_start(payload, {n: fake_entry(parents[n]) for n in (a, b)}, a, b, rng))
    record(f"{a}x{b}::dm", a, b, "direction_mix", 0,
           direction_mix_start(payload, parents, a, b))
for rep in range(REPS):
    record(f"polexpole::jm::r{rep}", "pole", "pole", "self", rep,
           jury_mix_start(payload, {"pole": fake_entry(parents["pole"])}, "pole", "pole", rng))

summary = {
    "tag": TAG, "seed": SEED, "reps": REPS,
    "corr_pole_p4": float(np.sum(parents["pole"]["canon_direction"] * parents["pairwise_bilateral::s4"]["canon_direction"])),
    "corr_pole_c4": float(np.sum(parents["pole"]["canon_direction"] * parents["contrastive_careful::s4"]["canon_direction"])),
    "children": children,
}
json.dump(summary, open(f"{DATA}/pole_vs_genre.json", "w"), indent=1)

for mode in ("jury_mix", "direction_mix", "self"):
    sub = [c for c in children if c["mode"] == mode]
    if not sub:
        continue
    print(f"\n{mode} (n={len(sub)}):")
    for k, v in Counter(c["class"] for c in sub).most_common():
        print(f"  {k}: {v}")
    for c in sub[:3]:
        print(f"   {c['name']}: {c['class']} exact={c['exact50']} broad={c['broad50']} anti={c['anti50']} head={c['head'][:5]}")

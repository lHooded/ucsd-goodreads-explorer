"""ONE-SHOT SEMANTIC UNBLIND of the two frozen tau=.70 mode families.

This is the single semantic evaluation layer over the COMPLETE frozen
structural result (commit 442e9fe):

- source campaign: jury_decomposition.json / .npz / geometry.json /
  geometry.npz / seal manifest (seed 20260819, 2880 sources);
- mode-families addendum: jury_decomposition_mode_families.json / .npz /
  seal manifest (seed 20260820; exactly 244 tau=.70 recurrent modes;
  exactly TWO frozen families at every cut, tau=.70 family 0 = 125 modes
  / 112 parents, family 1 = 119 modes / 102 parents).

Primary objects: the EXACT frozen tau=.70 family centroids
(family_cent_0.70_f0, family_cent_0.70_f1) from the sealed addendum NPZ.
They are never recomputed, redefined, merged, split, rotated, selected or
modified.  Family ordering is the frozen structural ordering; there is NO
semantic family selection.

Scientific question: are the two globally recurring label-blind basin
families literary-enriched?  Symmetric evaluation of BOTH families.

Preregistered primary statistics (frozen in code before semantic
loading, see HYPOTHESES):

- E0 / E1   = exact literary count in top 50, families 0 / 1;
- T_max = max(E0, E1)  -- at least one family unusually literary;
- T_min = min(E0, E1)  -- BOTH families unusually literary (the
  multiple-canon test);
- B_max / B_min = broad analogues (secondary/supporting);
- anti counts @50 reported with the explicitly stated direction
  (depletion: lower anti count is the literary direction; both tails
  reported descriptively).

Null: SEMANTIC_UNBLIND_SEED = 20260821, N_PERMUTATIONS = 10000,
popularity-stratified exactly like the Natural Amplification Census
(10 approximately equal bins of the eligible universe book_n >= 25 by
ordinal rank of log1p(book_n); within each bin the complete joint label
tuple (exact_lit, broad_lit, anti, filler) is permuted by ONE shared
permutation).  BOTH families are evaluated under the SAME permuted
semantic assignment in every permutation (rankings overlap and are
statistically dependent).  p = (1 + count(null >= observed)) / (N + 1);
anti lower-tail p = (1 + count(null <= observed)) / (N + 1).

Semantic definitions are REUSED from the existing census machinery:
spectral.load_posthoc_context (exact literary set, broad set, anti set,
filler set, readership universe, author identity from author_url) and
attractor.posthoc_head (the [50](50) evaluation convention with the
reader_mass >= 25 evidence floor).

FIREWALL / SEQUENCING: SEMANTIC_CONTEXT_LOADED stays False through ALL
seal verification and structural checks; it is set True only immediately
before the single semantic load.  No semantic value affects family
definition, ranking object selection, cutoff selection, null definition
or metric choice.

Phases:
- smoke:  bounded/synthetic tests + real seal validation (no real
          semantic load, no real unblind artifact);
- unblind: the one-shot semantic unblind (NOT run in this task);
- report:  re-render the PRE-UNBLIND-ordered report from the frozen
          results JSON.
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import rankdata

from curators_explorer.scripts import research_year_aware_canon as year
from curators_explorer.scripts import (
    research_seedless_attractor_census as attractor,
)
from curators_explorer.scripts import research_seedless_spectral_pilot as spectral
from curators_explorer.scripts.research_jury_decomposition_mode_families import (
    _verify_source_campaign,
)

# ---------------------------------------------------------------------------
# Preregistered semantic-unblind parameters (frozen before semantic load).
# ---------------------------------------------------------------------------
SEMANTIC_UNBLIND_SEED = 20260821
N_PERMUTATIONS = 10000
FAMILY_N_BINS = 10              # same stratification as the census null
MODE_TAU = 0.70
FAMILY_IDS = ("family_0", "family_1")
N_TOP_EVAL = 200                # head length (same as census _eval_pref)
EVAL_HEAD_50 = 50
EVAL_HEAD_100 = 100
AUTHOR_DEDUP_K = 50
ALPHA = 0.05                    # frozen before semantic load

SEMANTIC_CONTEXT_LOADED = False

# Frozen hypothesis definitions (no semantic value is seen before these
# statistics are fixed).
HYPOTHESES = {
    "E0": "exact literary count @50, family 0",
    "E1": "exact literary count @50, family 1",
    "T_max": "max(E0, E1): at least one frozen family is literary-enriched "
             "(family-wise)",
    "T_min": "min(E0, E1): preregistered symmetric JOINT/SUPPORTING "
             "statistic",
    "p_both_exact_iut": "intersection-union conjunction max(p_E0, p_E1): "
                        "PRIMARY formal test that BOTH frozen families "
                        "individually reject their own exact-literary nulls "
                        "(multiple naturally discovered canons)",
    "p_both_broad_iut": "intersection-union conjunction max(p_B0, p_B1): "
                        "secondary broad-literary conjunction",
    "alpha": f"conjunction rejection threshold {ALPHA} frozen before "
             "semantic load",
    "B_max": "max(broad0, broad1): at least one family broad-enriched "
             "(secondary)",
    "B_min": "min(broad0, broad1): both families broad-enriched (secondary)",
    "anti_direction": "anti counts @50 reported with the stated direction: "
                      "depletion (lower anti count) is the literary "
                      "direction; both tails are reported descriptively",
    "null": f"{N_PERMUTATIONS} popularity-stratified permutations, seed "
            f"{SEMANTIC_UNBLIND_SEED}, SAME permuted semantic assignment "
            f"for both families in every permutation",
}

# ---------------------------------------------------------------------------
# Paths.
# ---------------------------------------------------------------------------
DATA = Path(__file__).resolve().parents[1] / "data"
SPEC_PATH = DATA / "jury_decomposition_spec.json"
CENSUS_NPZ = DATA / "jury_decomposition.npz"
CENSUS_JSON = DATA / "jury_decomposition.json"
GEO_JSON = DATA / "jury_decomposition_geometry.json"
GEO_NPZ = DATA / "jury_decomposition_geometry.npz"
MANIFEST = DATA / "jury_decomposition_seal_manifest.json"
ADD_JSON = DATA / "jury_decomposition_mode_families.json"
ADD_NPZ = DATA / "jury_decomposition_mode_families.npz"
ADD_MANIFEST = DATA / "jury_decomposition_mode_families_seal_manifest.json"
RESULTS_JSON = DATA / "jury_decomposition_family_unblind.json"
NULLS_NPZ = DATA / "jury_decomposition_family_unblind.npz"
REPORT = DATA / "JURY_DECOMPOSITION_FAMILY_UNBLIND_REPORT.md"
SMOKE_REPORT = DATA / "jury_decomposition_family_unblind_smoke_report.json"


def _sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _git_head() -> str:
    import subprocess
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    import os
    os.replace(tmp, path)


def _write_npz_atomic(path: Path, arrays: dict[str, np.ndarray]) -> None:
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    import os
    os.replace(tmp, path)


def _write_json_atomic(path: Path, obj: Any) -> None:
    _write_text_atomic(path, json.dumps(obj, indent=1))


# ---------------------------------------------------------------------------
# Provenance + pre-semantic guard (raises before ANY semantic load).
# ---------------------------------------------------------------------------

def _source_provenance() -> dict[str, Any]:
    """Compute and validate the frozen source campaign provenance exactly:
    all four manifest hashes, geometry-seal hashes, partial/unblinded/
    semantic flags, 2880 sources, source list vs the seal."""
    for p in (SPEC_PATH, CENSUS_NPZ, CENSUS_JSON, GEO_NPZ, GEO_JSON,
              MANIFEST):
        if not p.exists():
            raise SystemExit(f"missing frozen source artifact {p}")
    geometry = json.loads(GEO_JSON.read_text(encoding="utf-8"))
    seal = geometry.get("seal")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cons = json.loads(CENSUS_JSON.read_text(encoding="utf-8"))
    records = cons["records"]
    ids = [r["source_id"] for r in records]
    prov = {
        "census_npz_sha256": _sha256(CENSUS_NPZ),
        "census_json_sha256": _sha256(CENSUS_JSON),
        "geometry_npz_sha256": _sha256(GEO_NPZ),
        "geometry_json_sha256": _sha256(GEO_JSON),
        "n_sources": len(records),
        "sources": ids,
        "campaign_seed": seal.get("seed"),
        "campaign_git_head": seal.get("git_head"),
    }
    _assert_source_ok(prov, seal, manifest, cons)
    return prov


def _assert_source_ok(prov: dict[str, Any], seal: dict[str, Any],
                      manifest: dict[str, Any],
                      cons: dict[str, Any]) -> None:
    """Pure validation of the source campaign provenance; raises on any
    violation (used both by the real check and by smoke tamper tests)."""
    def _must(name: str, ok: bool) -> None:
        if not ok:
            raise SystemExit(f"source seal check failed: {name}; refusing")

    _must("seal exists", seal is not None)
    _must("seal claims semantic",
          seal.get("semantic_context_loaded") is False)
    _must("seal claims unblinded", seal.get("unblinded") is False)
    _must("seal partial", seal.get("partial") is False)
    _must("census partial", cons.get("partial") is False)
    _must("manifest census_npz",
          manifest["artifacts"]["census_npz"]["sha256"]
          == prov["census_npz_sha256"])
    _must("manifest census_json",
          manifest["artifacts"]["census_json"]["sha256"]
          == prov["census_json_sha256"])
    _must("manifest geometry_npz",
          manifest["artifacts"]["geometry_npz"]["sha256"]
          == prov["geometry_npz_sha256"])
    _must("manifest geometry_json",
          manifest["artifacts"]["geometry_json"]["sha256"]
          == prov["geometry_json_sha256"])
    _must("seal census_npz", seal["census_npz_sha256"]
          == prov["census_npz_sha256"])
    _must("seal census_json", seal["census_json_sha256"]
          == prov["census_json_sha256"])
    _must("seal geometry_npz", seal["geometry_npz_sha256"]
          == prov["geometry_npz_sha256"])
    _must("n_sources 2880", prov["n_sources"] == 2880)
    _must("seal n_sources", seal["n_sources"] == prov["n_sources"])
    _must("seal source list", seal["sources"] == prov["sources"])


def _addendum_provenance(
    source_prov: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute and validate the mode-families addendum seal: addendum
    JSON/NPZ hashes vs the addendum manifest, the four source hashes, the
    frozen structural facts (244 modes, exactly two tau=.70 families with
    their exact frozen member lists and centroid keys)."""
    for p in (ADD_JSON, ADD_NPZ, ADD_MANIFEST):
        if not p.exists():
            raise SystemExit(f"missing frozen addendum artifact {p}")
    addendum = json.loads(ADD_JSON.read_text(encoding="utf-8"))
    manifest = json.loads(ADD_MANIFEST.read_text(encoding="utf-8"))
    add_hash = _sha256(ADD_JSON)
    npz_hash = _sha256(ADD_NPZ)
    source_keys = ("census_npz", "census_json", "geometry_npz",
                   "geometry_json")
    fam = _family_objects(addendum, npz_hash)
    _assert_addendum_ok(addendum, manifest, source_prov, add_hash, npz_hash,
                        source_keys, fam)
    return addendum, fam


def _assert_addendum_ok(
    addendum: dict[str, Any], manifest: dict[str, Any],
    source_prov: dict[str, Any], add_hash: str, npz_hash: str,
    source_keys: tuple[str, ...], fam: dict[str, Any],
) -> None:
    def _must(name: str, ok: bool) -> None:
        if not ok:
            raise SystemExit(f"addendum seal check failed: {name}; refusing")

    _must("addendum claims semantic",
          addendum.get("semantic_context_loaded") is False)
    _must("addendum claims unblinded", addendum.get("unblinded") is False)
    _must("addendum json hash",
          manifest["artifacts"]["addendum_json"]["sha256"] == add_hash)
    _must("addendum npz hash",
          manifest["artifacts"]["addendum_npz"]["sha256"] == npz_hash)
    for key in source_keys:
        _must(f"addendum source {key}",
              manifest["artifacts"][f"source_{key}"]["sha256"]
              == source_prov[f"{key}_sha256"])
    _must("244 source modes", addendum["source_mode_count"] == 244)
    _must("exactly two tau=.70 families", fam["n_families"] == 2)
    _must("both families cross-parent",
          all(f["n_distinct_parents"] >= 2 for f in fam["families"]))
    _must("family centroid keys present",
          all(f["centroid_key"] in fam["npz_keys"] for f in fam["families"]))
    _must("family centroids finite/unit",
          fam["centroids_ok"] is True)


def _family_objects(
    addendum: dict[str, Any], npz_hash: str,
) -> dict[str, Any]:
    """The EXACT frozen tau=.70 family objects (structural, label-blind):
    member mode lists, frozen centroid keys and the exact frozen centroid
    vectors from the sealed addendum NPZ (never recomputed)."""
    with np.load(ADD_NPZ, allow_pickle=False) as blob:
        npz_keys = list(blob.files)
        fam_records = addendum["families"]["0.7"]["families"]
        families = []
        centroids_ok = True
        for rec in fam_records:
            key = rec["centroid_key"]
            centroid = np.asarray(blob[key], dtype=np.float64)
            norm = float(np.linalg.norm(centroid))
            if not np.isfinite(centroid).all() or abs(norm - 1.0) > 1e-4:
                centroids_ok = False
            families.append({
                "family_id": rec["family_id"],
                "n_modes": rec["n_modes"],
                "n_distinct_parents": rec["n_distinct_parents"],
                "member_mode_ids": list(rec["member_mode_ids"]),
                "centroid_key": key,
                "centroid": centroid,
            })
    member_ok = all(
        mid in set(addendum["source_mode_ids"]) for f in families
        for mid in f["member_mode_ids"])
    return {
        "n_families": len(families),
        "families": families,
        "npz_keys": npz_keys,
        "centroids_ok": bool(centroids_ok),
        "members_ok": bool(member_ok),
    }


def _guard_pre_semantic() -> tuple[dict[str, Any], dict[str, Any]]:
    """All seal checks BEFORE any semantic load; returns (addendum,
    family objects).  Raises SystemExit on any violation."""
    source_prov = _source_provenance()
    addendum, fam = _addendum_provenance(source_prov)
    return addendum, fam


# ---------------------------------------------------------------------------
# Semantic evaluation (reuses the existing census machinery).
# ---------------------------------------------------------------------------

def _author_id(meta_row: dict[str, Any]) -> str | None:
    m = re.search(r"/author/show/(\d+)", str(meta_row.get("author_url", "")))
    return m.group(1) if m else None


def _dedup_head(rows: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    """Traverse ranked works in order, keep only the first work per
    normalized author identity, stop when k unique-author works are
    obtained.  Deterministic."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for r in rows:
        aid = _author_id(r.get("meta", {})) if "meta" in r else None
        if aid is None:
            continue
        if aid in seen:
            continue
        seen.add(aid)
        out.append(r)
        if len(out) == k:
            break
    return out


def _counts_in(rows: list[dict[str, Any]], eval_sets: dict[str, Any],
               k: int) -> dict[str, int]:
    return {name: int(sum(
        r["work_id"] in eval_sets[name] for r in rows[:k]))
        for name in ("exact_lit", "broad_lit", "anti", "filler")}


def _author_diagnostics(rows: list[dict[str, Any]],
                        k: int) -> dict[str, Any]:
    top = rows[:k]
    ids = [_author_id(r.get("meta", {})) for r in top]
    counts: dict[str, int] = {}
    for a in ids:
        if a is None:
            continue
        counts[a] = counts.get(a, 0) + 1
    n_distinct = len(counts)
    max_works = max(counts.values()) if counts else 0
    n_ge2 = sum(1 for v in counts.values() if v >= 2)
    return {"n_distinct_authors": n_distinct, "max_works_one_author": max_works,
            "n_authors_ge2_works": n_ge2}


def _family_semantic_eval(
    full_centroid: np.ndarray, reader_mass: np.ndarray,
    work_ids: np.ndarray, meta: dict[str, Any], eval_sets: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Rank the frozen family centroid with the EXISTING posthoc_head
    convention ([50](50) metrics, reader_mass >= 25 evidence floor)."""
    preference = {"score": np.asarray(full_centroid, dtype=np.float64),
                  "mean": np.asarray(full_centroid, dtype=np.float64),
                  "reader_mass": np.asarray(reader_mass, dtype=np.float64)}
    head, metrics = attractor.posthoc_head(
        preference, work_ids, meta, eval_sets, limit=N_TOP_EVAL)
    for r in head:
        r["meta"] = meta.get(r["work_id"], {})
    metrics50 = _counts_in(head, eval_sets, EVAL_HEAD_50)
    metrics100 = _counts_in(head, eval_sets, EVAL_HEAD_100)
    return head, {
        "top50": metrics50,
        "top100": metrics100,
        "precision50": {name: metrics50[name] / EVAL_HEAD_50
                        for name in metrics50},
        "precision100": {name: metrics100[name] / EVAL_HEAD_100
                         for name in metrics100},
        "anti_fraction50": metrics50["anti"] / EVAL_HEAD_50,
        "anti_fraction100": metrics100["anti"] / EVAL_HEAD_100,
    }


def _embed_full(centroid: np.ndarray, eligible_idx: np.ndarray,
                n_books: int) -> np.ndarray:
    """Re-embed an eligible-coordinate vector into the full work-index
    space (ineligible books score 0), exactly as the census evaluator."""
    full = np.zeros(n_books, dtype=np.float64)
    full[eligible_idx] = np.asarray(centroid, dtype=np.float64)
    return full


def _tail_p_upper(nulls: np.ndarray, observed: int,
                  n_perms: int) -> float:
    return float((1 + int(np.sum(nulls >= observed))) / (n_perms + 1))


def _tail_p_lower(nulls: np.ndarray, observed: int,
                  n_perms: int) -> float:
    return float((1 + int(np.sum(nulls <= observed))) / (n_perms + 1))


def _iut_conjunction(p0: float, p1: float) -> float:
    """Intersection-union conjunction p: max of the two family-specific
    p-values.  A conjunction rejection at ALPHA requires BOTH families to
    reject their own nulls."""
    return float(max(p0, p1))


def _frozen_top50_work_ids(
    centroid_eligible: np.ndarray, eligible_idx: np.ndarray,
    work_ids: np.ndarray,
) -> list[str]:
    """Ordered 50 full work IDs of the frozen structural top-50 of an
    eligible-coordinate centroid, derived WITHOUT any semantic metadata."""
    order = np.argsort(-np.asarray(centroid_eligible, dtype=np.float64),
                       kind="stable")[:50]
    return [str(work_ids[int(eligible_idx[int(i)])]) for i in order]


def _posthoc_head_top50_work_ids(head: list[dict[str, Any]]) -> list[str]:
    return [r["work_id"] for r in head[:50]]


def _frozen_top50_alignment_ok(
    head: list[dict[str, Any]], frozen_ids: list[str],
) -> bool:
    """HARD invariant: the ordered first-50 works evaluated by
    posthoc_head must equal the pre-semantic frozen structural top-50
    exactly."""
    return _posthoc_head_top50_work_ids(head) == list(frozen_ids)


# ---------------------------------------------------------------------------
# Joint popularity-stratified permutation null (both families, SAME
# permuted semantic assignment; indexing only).
# ---------------------------------------------------------------------------

def _family_permutation_test(
    top_pos: np.ndarray,           # (2, 50) eligible-space positions
    label_vecs: dict[str, np.ndarray],   # full-space bool per set
    book_n: np.ndarray,
    eligible_idx: np.ndarray,
    n_books: int,
    n_perms: int,
    seed: int,
) -> dict[str, Any]:
    """Popularity-stratified joint permutation test, same design as the
    Natural Amplification Census: the eligible universe (book_n >= 25) is
    split into FAMILY_N_BINS approximately equal bins by ordinal rank of
    log1p(book_n); within each bin the complete joint label tuple
    (exact_lit, broad_lit, anti, filler) is permuted by ONE shared
    permutation.  BOTH families' statistics are computed from the SAME
    permuted assignment in every permutation."""
    eligible_idx = np.asarray(eligible_idx, dtype=np.int64)
    n_eligible = len(eligible_idx)
    lab = np.stack([label_vecs[n]
                    for n in ("exact_lit", "broad_lit", "anti", "filler")])
    lab = lab[:, eligible_idx].astype(bool)  # (4, n_eligible)

    obs = lab[:, top_pos].sum(axis=2)  # (4, 2)
    exact_obs = (int(obs[0, 0]), int(obs[0, 1]))
    broad_obs = (int(obs[1, 0]), int(obs[1, 1]))
    anti_obs = (int(obs[2, 0]), int(obs[2, 1]))

    l1 = np.log1p(book_n[eligible_idx]).astype(np.float64)
    ranks = rankdata(l1, method="ordinal")
    bin_ids = np.minimum(
        ((ranks - 1) * FAMILY_N_BINS) // n_eligible, FAMILY_N_BINS - 1,
    ).astype(np.int64)
    bin_sizes = np.bincount(bin_ids, minlength=FAMILY_N_BINS)
    edges = np.quantile(l1, np.linspace(0.0, 1.0, FAMILY_N_BINS + 1))

    rel_pos = np.unique(top_pos)
    rel_index = np.searchsorted(rel_pos, top_pos)  # (2, 50)
    bin_positions = [np.flatnonzero(bin_ids == b)
                     for b in range(FAMILY_N_BINS)]
    bin_rel_masks = [np.isin(rel_pos, bp) for bp in bin_positions]

    rng = np.random.default_rng(seed)
    keys = ("E0", "E1", "T_max", "T_min",
            "B0", "B1", "B_max", "B_min", "A0", "A1")
    nulls = {k: np.empty(n_perms, dtype=np.int64) for k in keys}
    for p in range(n_perms):
        lrel = np.empty((4, rel_pos.size), dtype=bool)
        for b in range(FAMILY_N_BINS):
            mask = bin_rel_masks[b]
            size_b = int(mask.sum())
            if size_b == 0:
                continue
            pick = rng.choice(bin_positions[b], size=size_b, replace=False)
            lrel[:, mask] = lab[:, pick]
        counts = lrel[:, rel_index].sum(axis=2)  # (4, 2)
        e0, e1 = int(counts[0, 0]), int(counts[0, 1])
        b0, b1 = int(counts[1, 0]), int(counts[1, 1])
        a0, a1 = int(counts[2, 0]), int(counts[2, 1])
        nulls["E0"][p], nulls["E1"][p] = e0, e1
        nulls["T_max"][p], nulls["T_min"][p] = max(e0, e1), min(e0, e1)
        nulls["B0"][p], nulls["B1"][p] = b0, b1
        nulls["B_max"][p], nulls["B_min"][p] = max(b0, b1), min(b0, b1)
        nulls["A0"][p], nulls["A1"][p] = a0, a1

    def p_upper(name: str, observed: int) -> float:
        return _tail_p_upper(nulls[name], observed, n_perms)

    return {
        "seed": int(seed),
        "n_perms": int(n_perms),
        "n_bins": int(FAMILY_N_BINS),
        "strata": "approximately equal bins of the eligible universe "
                  "(book_n >= 25) by ordinal rank of log1p(book_n)",
        "stratum_sizes": bin_sizes.tolist(),
        "stratum_edges_log1p": edges.tolist(),
        "joint_assignment": True,
        "observed": {
            "E0": exact_obs[0], "E1": exact_obs[1],
            "T_max": max(exact_obs), "T_min": min(exact_obs),
            "B0": broad_obs[0], "B1": broad_obs[1],
            "B_max": max(broad_obs), "B_min": min(broad_obs),
            "A0": anti_obs[0], "A1": anti_obs[1],
        },
        "p_values": {
            "p_E0": p_upper("E0", exact_obs[0]),
            "p_E1": p_upper("E1", exact_obs[1]),
            "p_T_max": p_upper("T_max", max(exact_obs)),
            "p_T_min": p_upper("T_min", min(exact_obs)),
            "p_B0": p_upper("B0", broad_obs[0]),
            "p_B1": p_upper("B1", broad_obs[1]),
            "p_B_max": p_upper("B_max", max(broad_obs)),
            "p_B_min": p_upper("B_min", min(broad_obs)),
            "p_A0_depletion": _tail_p_lower(nulls["A0"], anti_obs[0],
                                            n_perms),
            "p_A1_depletion": _tail_p_lower(nulls["A1"], anti_obs[1],
                                            n_perms),
            "p_A0_enrichment": p_upper("A0", anti_obs[0]),
            "p_A1_enrichment": p_upper("A1", anti_obs[1]),
        },
        "null_mean": {k: float(v.mean()) for k, v in nulls.items()},
        "null_sd": {k: float(v.std()) for k, v in nulls.items()},
        "null_arrays": nulls,
    }


# ---------------------------------------------------------------------------
# Overlap / distinctness (descriptive).
# ---------------------------------------------------------------------------

def _top_k_overlap(head0: list[dict[str, Any]],
                   head1: list[dict[str, Any]], k: int) -> dict[str, Any]:
    ids0 = {r["work_id"] for r in head0[:k]}
    ids1 = {r["work_id"] for r in head1[:k]}
    inter = len(ids0 & ids1)
    union = len(ids0 | ids1)
    return {"k": k, "n_overlap": int(inter),
            "jaccard": float(inter / union) if union else 0.0}


def _head_work_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {r["work_id"] for r in rows}


def _set_overlap(head0: list[dict[str, Any]], head1: list[dict[str, Any]],
                 eval_sets: dict[str, Any], name: str) -> dict[str, Any]:
    a = _head_work_ids(head0) & set(eval_sets[name])
    b = _head_work_ids(head1) & set(eval_sets[name])
    union = a | b
    return {"set": name, "n_family0": len(a), "n_family1": len(b),
            "n_overlap": len(a & b),
            "jaccard": float(len(a & b) / len(union)) if union else 0.0}


# ---------------------------------------------------------------------------
# Report rendering (order frozen: provenance -> hypotheses -> metrics ->
# joint tests -> broad/anti -> author dedup -> overlap -> heads).
# ---------------------------------------------------------------------------

def _render_report(results: dict[str, Any]) -> str:
    lines: list[str] = []
    add = results["addendum_provenance"]
    prov = results["source_provenance"]
    hyp = results["hypotheses"]
    families = results["families"]
    joint = results["joint_tests"]
    lines += [
        "# Hierarchical jury decomposition: family semantic unblind report",
        "",
        "**One-shot semantic unblind of the two frozen tau=0.70 mode "
        "families.  The numerical metrics and permutation results below "
        "were frozen BEFORE any human-readable head was rendered.**",
        "",
        "## 1. Provenance and verified seals",
        "",
        f"- Source campaign: seed **{prov['campaign_seed']}**, git head "
        f"`{str(prov['campaign_git_head'])[:12]}`; {prov['n_sources']} "
        f"sources; partial false; unblinded false; semantic false.",
        f"- Source hashes verified: census_npz "
        f"`{prov['census_npz_sha256'][:16]}...`, census_json "
        f"`{prov['census_json_sha256'][:16]}...`, geometry_npz "
        f"`{prov['geometry_npz_sha256'][:16]}...`, geometry_json "
        f"`{prov['geometry_json_sha256'][:16]}...`.",
        f"- Addendum (mode families): seed **{add['addendum_seed']}**, "
        f"{add['source_mode_count']} tau=0.70 recurrent modes, exactly "
        f"two families at every cut; semantic false; unblinded false.",
        f"- Addendum centroids used: `{families[0]['centroid_key']}`, "
        f"`{families[1]['centroid_key']}` (exact frozen vectors, finite, "
        f"unit L2; never recomputed).",
        f"- Semantic-unblind seed **{results['semantic_unblind_seed']}**; "
        f"{results['n_permutations']} popularity-stratified permutations; "
        f"SAME permuted semantic assignment for both families.",
        "",
        "## 2. Frozen semantic hypotheses (before any head)",
        "",
    ]
    for k, v in hyp.items():
        lines.append(f"- `{k}`: {v}")
    lines += ["", "## 3. Numerical family 0 metrics (frozen)", ""]
    for name, f in (("family_0", families[0]), ("family_1", families[1])):
        lines.append(f"### {name} ({f['family_id']}, {f['n_modes']} modes, "
                     f"{f['n_distinct_parents']} parents)")
        m50 = f["metrics"]["top50"]
        m100 = f["metrics"]["top100"]
        lines += [
            f"- exact literary @50 = **{m50['exact_lit']}** "
            f"(precision {f['metrics']['precision50']['exact_lit']:.3f}); "
            f"@100 = **{m100['exact_lit']}** "
            f"(precision {f['metrics']['precision100']['exact_lit']:.3f}).",
            f"- broad literary @50 = **{m50['broad_lit']}** "
            f"(precision {f['metrics']['precision50']['broad_lit']:.3f}); "
            f"@100 = **{m100['broad_lit']}** "
            f"(precision {f['metrics']['precision100']['broad_lit']:.3f}).",
            f"- anti @50 = **{m50['anti']}** "
            f"(fraction {f['metrics']['anti_fraction50']:.3f}); "
            f"@100 = **{m100['anti']}** "
            f"(fraction {f['metrics']['anti_fraction100']:.3f}).",
            f"- chance @50 (universe fractions): exact "
            f"{f['chance']['exact_lit']:.1f}, broad "
            f"{f['chance']['broad_lit']:.1f}, anti {f['chance']['anti']:.1f}.",
        ]
    lines += ["", "## 4. Joint T_max / T_min permutation results", "",
              "| statistic | observed | null mean | null sd | p_upper |",
              "|---|---:|---:|---:|---:|"]
    for key, label in (("E0", "exact@50 family 0"), ("E1", "exact@50 family 1"),
                       ("T_max", "max(E0,E1)"),
                       ("T_min", "min(E0,E1) (joint/supporting)")):
        lines.append(
            f"| {label} | {joint['observed'][key]} | "
            f"{joint['null_mean'][key]:.2f} | {joint['null_sd'][key]:.2f} | "
            f"{joint['p_values']['p_' + key]:.4f} |")
    ct = results.get("conjunction_tests", {})
    lines.append(
        f"| BOTH exact (IUT max(p_E0,p_E1)) | n/a | n/a | n/a | "
        f"{ct.get('exact', {}).get('p', float('nan')):.4f} "
        f"(alpha {ct.get('exact', {}).get('alpha', float('nan'))}) |")
    lines += ["", "## 5. Broad / anti results (secondary/supporting)", "",
              "| statistic | observed | null mean | null sd | p_upper |",
              "|---|---:|---:|---:|---:|"]
    for key, label in (("B0", "broad@50 family 0"), ("B1", "broad@50 family 1"),
                       ("B_max", "max(B0,B1)"), ("B_min", "min(B0,B1)")):
        lines.append(
            f"| {label} | {joint['observed'][key]} | "
            f"{joint['null_mean'][key]:.2f} | {joint['null_sd'][key]:.2f} | "
            f"{joint['p_values']['p_' + key]:.4f} |")
    lines.append(
        f"| BOTH broad (IUT max(p_B0,p_B1)) | n/a | n/a | n/a | "
        f"{ct.get('broad', {}).get('p', float('nan')):.4f} "
        f"(alpha {ct.get('broad', {}).get('alpha', float('nan'))}) |")
    for fkey, pkey in (("A0", "A0"), ("A1", "A1")):
        lines.append(
            f"| anti@50 {fkey} (depletion direction) | "
            f"{joint['observed'][fkey]} | {joint['null_mean'][fkey]:.2f} | "
            f"{joint['null_sd'][fkey]:.2f} | "
            f"p_lower={joint['p_values']['p_' + pkey + '_depletion']:.4f} "
            f"(p_upper={joint['p_values']['p_' + pkey + '_enrichment']:.4f}) |")
    lines += [
        "",
        "## 6. Author-deduplicated robustness (descriptive)",
        "",
        "| family | unique-author exact @50 | unique-author broad @50 | "
        "unique-author anti @50 | n distinct authors | max works one author "
        "| authors >=2 works |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for f in families:
        d = f["author_dedup"]
        lines.append(
            f"| {f['family_id']} | {d['counts']['exact_lit']} | "
            f"{d['counts']['broad_lit']} | {d['counts']['anti']} | "
            f"{d['diagnostics']['n_distinct_authors']} | "
            f"{d['diagnostics']['max_works_one_author']} | "
            f"{d['diagnostics']['n_authors_ge2_works']} |")
    lines += [
        "",
        "## 7. Cross-family overlap / distinctness (descriptive)",
        "",
        f"- Centroid cosine family0 vs family1: "
        f"**{results['centroid_cosine']:.4f}**.",
    ]
    for o in results["overlaps"]:
        lines.append(f"- Top {o['k']} overlap: {o['n_overlap']} works, "
                     f"Jaccard {o['jaccard']:.3f}.")
    for o in results["set_overlaps"]:
        lines.append(
            f"- {o['set']} works: family0 {o['n_family0']}, "
            f"family1 {o['n_family1']}, overlap {o['n_overlap']} "
            f"(Jaccard {o['jaccard']:.3f}).")
    lines += [
        "",
        "## 8. Interpretation (frozen tests only)",
        "",
        f"- T_min p = **{joint['p_values']['p_T_min']:.4f}** (preregistered "
        f"joint/supporting statistic); "
        f"p_both_exact_iut = **{ct.get('exact', {}).get('p', float('nan')):.4f}** "
        f"(primary intersection-union conjunction, alpha "
        f"{ct.get('exact', {}).get('alpha', float('nan'))}).  Both are "
        f"reported; neither silently replaces the other.",
        "- Category A: p_T_max < .05 but p_both_exact_iut >= .05 -> at "
        "least ONE frozen family is exact-literary enriched; NOT evidence "
        "that both are literary canons.",
        "- Category B: p_both_exact_iut < .05 -> BOTH frozen families "
        "individually reject their own exact-literary nulls; confirmatory "
        "statistical condition for multiple naturally discovered literary "
        "canons (examine overlap/distinctness before claiming genuinely "
        "distinct canons).",
        "- Category C: neither -> structural decomposition is real but no "
        "exact literary recovery under this test.",
        "- Category D: only broad conjunction/significance -> broader "
        "high-cultural/serious-reading structure, not strict literary "
        "canon recovery.",
        "",
        "## 9. Frozen top-work heads (rendered AFTER all metrics)",
        "",
    ]
    for f in families:
        lines.append(f"### {f['family_id']} top-50 head")
        lines.append("| rank | title | author | score | exact | broad | "
                     "anti |")
        lines.append("|---:|---|---|---:|---|---|---|")
        for r in f["head"][:50]:
            lines.append(
                f"| {r['rank']} | {r['title']} | {r['author']} | "
                f"{r['score']:.4f} | "
                f"{'Y' if r['work_id'] in results['eval_sets']['exact_lit'] else ''} | "
                f"{'Y' if r['work_id'] in results['eval_sets']['broad_lit'] else ''} | "
                f"{'Y' if r['work_id'] in results['eval_sets']['anti'] else ''} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# phase: unblind (the one-shot semantic unblind; NOT run in this task).
# ---------------------------------------------------------------------------

def phase_unblind(args: argparse.Namespace) -> None:
    global SEMANTIC_CONTEXT_LOADED
    assert not SEMANTIC_CONTEXT_LOADED
    t0 = time.time()

    # ---- ALL structural verification BEFORE any semantic load ----
    addendum, fam = _guard_pre_semantic()
    payload, _, _ = year.load_matrix()
    eligible = np.asarray(payload["book_n"] >= 25)
    eligible_idx = np.flatnonzero(eligible)
    n_books = int(len(payload["work_ids"]))
    reader_mass = np.where(eligible, payload["book_n"], 0.0).astype(np.float64)

    # frozen top-50 per family (structural ranking only, no semantics):
    # ordered 50 eligible positions for the permutation test AND the exact
    # ordered 50 full work IDs for the posthoc_head alignment invariant
    top_pos = np.empty((2, 50), dtype=np.int64)
    frozen_top50_ids: list[list[str]] = []
    for i, f in enumerate(fam["families"]):
        order = np.argsort(-f["centroid"], kind="stable")[:50]
        top_pos[i] = eligible_idx[order]
        frozen_top50_ids.append(
            _frozen_top50_work_ids(f["centroid"], eligible_idx,
                                   payload["work_ids"]))

    # ---- THE single semantic load; explicit sequencing boundary ----
    # The flag is set to True IMMEDIATELY BEFORE the semantic loader, after
    # every seal check, family/centroid load, eligibility calculation and
    # frozen ranking calculation (all performed while the flag is False).
    print("Loading post-hoc semantic context (family unblind)", flush=True)
    SEMANTIC_CONTEXT_LOADED = True
    meta, eval_sets = spectral.load_posthoc_context(payload["work_ids"])

    n_eligible = int(eligible.sum())
    universe = set(payload["work_ids"][eligible].tolist())
    chance = {name: len(eval_sets[name] & universe) / n_eligible * 50
              for name in ("exact_lit", "broad_lit", "anti")}

    families: list[dict[str, Any]] = []
    for i, f in enumerate(fam["families"]):
        full = _embed_full(f["centroid"], eligible_idx, n_books)
        head, metrics = _family_semantic_eval(
            full, reader_mass, payload["work_ids"], meta, eval_sets)
        # HARD invariant: the semantic evaluator's ordered first-50 works
        # must be EXACTLY the pre-semantic frozen structural top-50; abort
        # before writing any semantic result artifact otherwise
        if not _frozen_top50_alignment_ok(head, frozen_top50_ids[i]):
            raise SystemExit(
                f"frozen top-50 != posthoc_head top-50 for family "
                f"{f['family_id']}; refusing to write semantic artifacts")
        dedup_rows = _dedup_head(head, AUTHOR_DEDUP_K)
        families.append({
            "family_id": f["family_id"],
            "n_modes": f["n_modes"],
            "n_distinct_parents": f["n_distinct_parents"],
            "centroid_key": f["centroid_key"],
            "member_mode_ids": f["member_mode_ids"],
            "metrics": metrics,
            "chance": chance,
            "author_dedup": {
                "counts": _counts_in(dedup_rows, eval_sets, AUTHOR_DEDUP_K),
                "diagnostics": _author_diagnostics(head, EVAL_HEAD_50),
            },
            "frozen_top50_equals_posthoc_head_top50": True,
            "head": head,
        })

    label_vecs = {name: np.isin(payload["work_ids"], sorted(eval_sets[name]))
                  for name in ("exact_lit", "broad_lit", "anti", "filler")}
    joint = _family_permutation_test(
        top_pos, label_vecs, payload["book_n"], eligible_idx, n_books,
        N_PERMUTATIONS, SEMANTIC_UNBLIND_SEED)
    nulls_out = dict(joint.pop("null_arrays"))
    nulls_out["stratum_sizes"] = np.asarray(joint["stratum_sizes"],
                                            dtype=np.int64)
    nulls_out["stratum_edges_log1p"] = np.asarray(
        joint["stratum_edges_log1p"], dtype=np.float64)

    overlaps = [_top_k_overlap(families[0]["head"], families[1]["head"], k)
                for k in (50, 100)]
    set_overlaps = [_set_overlap(families[0]["head"], families[1]["head"],
                                 eval_sets, name)
                    for name in ("exact_lit", "broad_lit", "anti")]
    centroid_cosine = float(fam["families"][0]["centroid"]
                            @ fam["families"][1]["centroid"])

    # intersection-union conjunction tests (frozen definition; computed
    # from the already-computed family-specific p-values, no extra
    # permutations)
    p_both_exact_iut = _iut_conjunction(joint["p_values"]["p_E0"],
                                        joint["p_values"]["p_E1"])
    p_both_broad_iut = _iut_conjunction(joint["p_values"]["p_B0"],
                                        joint["p_values"]["p_B1"])
    conjunction_tests = {
        "exact": {
            "method": "intersection-union: max(p_E0, p_E1)",
            "p": p_both_exact_iut,
            "alpha": float(ALPHA),
        },
        "broad": {
            "method": "intersection-union: max(p_B0, p_B1)",
            "p": p_both_broad_iut,
            "alpha": float(ALPHA),
        },
    }

    source_prov = _source_provenance()
    results = {
        "semantic_unblind_seed": int(SEMANTIC_UNBLIND_SEED),
        "n_permutations": int(N_PERMUTATIONS),
        "source_provenance": {k: v for k, v in source_prov.items()
                              if k != "sources"},
        "addendum_provenance": {
            "addendum_seed": addendum["addendum_seed"],
            "source_mode_count": addendum["source_mode_count"],
            "n_families": len(fam["families"]),
        },
        "hypotheses": HYPOTHESES,
        "families": families,
        "joint_tests": joint,
        "conjunction_tests": conjunction_tests,
        "frozen_top50_equals_posthoc_head_top50": True,
        "overlaps": overlaps,
        "set_overlaps": set_overlaps,
        "centroid_cosine": float(centroid_cosine),
        "semantic_context_loaded": True,
        "unblinded": True,
        "method": {
            "phase": "unblind",
            "seed": int(SEMANTIC_UNBLIND_SEED),
            "command": shlex.join(sys.argv),
            "git_head": _git_head(),
            "runtime_seconds": time.time() - t0,
            "semantic_sets": "existing census definitions via "
                             "spectral.load_posthoc_context",
            "evaluation": "attractor.posthoc_head, reader_mass >= 25, "
                          "[50](50) primary convention, top-100 descriptive",
            "null": joint["strata"],
        },
        "eval_sets": {k: sorted(v) for k, v in eval_sets.items()
                      if k != "exact_matches"},
    }
    _write_json_atomic(RESULTS_JSON, results)
    _write_npz_atomic(NULLS_NPZ, nulls_out)
    _write_text_atomic(REPORT, _render_report(results))
    print(f"family unblind done in {time.time() - t0:.0f}s; "
          f"T_max={joint['observed']['T_max']} "
          f"(p={joint['p_values']['p_T_max']:.4f}), "
          f"T_min={joint['observed']['T_min']} "
          f"(p={joint['p_values']['p_T_min']:.4f}), "
          f"p_both_exact_iut={p_both_exact_iut:.4f}, "
          f"E0={joint['observed']['E0']} E1={joint['observed']['E1']}",
          flush=True)


# ---------------------------------------------------------------------------
# phase: report (re-render the frozen report from the results JSON).
# ---------------------------------------------------------------------------

def phase_report(args: argparse.Namespace) -> None:
    if not RESULTS_JSON.exists():
        raise SystemExit("results JSON missing; run unblind first")
    results = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    _write_text_atomic(REPORT, _render_report(results))
    print(f"family unblind report written: {REPORT}", flush=True)


# ---------------------------------------------------------------------------
# phase: smoke (bounded/synthetic; no real semantic load, no real unblind
# artifact).
# ---------------------------------------------------------------------------

def _synthetic_semantic_fixture(
    n_books: int = 120,
) -> dict[str, Any]:
    """Tiny label-blind synthetic universe: 120 works, book_n >= 25 for
    all; exact ids 0..14, broad ids 0..24, anti ids 50..57, filler the
    rest; author_url /author/show/<a> with a = work_id // 2 (2 works per
    author).  Family0 ranking = works 0..49, family1 = works 10..59."""
    rng = np.random.default_rng(7)
    book_n = np.full(n_books, 25 + rng.integers(0, 200, size=n_books))
    # string work ids exactly like the real payload (census label_vecs rely
    # on np.isin(str, str))
    work_ids = np.arange(n_books).astype(str)
    meta = {str(i): {
        "title": f"w{i}", "author": f"A{i // 2}",
        "author_url": f"https://x/author/show/{i // 2}",
        "n": int(book_n[i]), "p5": 0.5, "mean": 4.0,
    } for i in range(n_books)}
    eval_sets = {
        "exact_lit": {str(i) for i in range(15)},
        "broad_lit": {str(i) for i in range(25)},
        "anti": {str(i) for i in range(50, 58)},
        "filler": {str(i) for i in range(58, n_books)},
    }
    return {"n_books": n_books, "book_n": book_n, "work_ids": work_ids,
            "meta": meta, "eval_sets": eval_sets}


def _synthetic_rankings(n_books: int) -> tuple[np.ndarray, np.ndarray]:
    """Full-space score vectors: family0 ranks works 0..49, family1 ranks
    works 10..59 (descending)."""
    s0 = np.zeros(n_books)
    s1 = np.zeros(n_books)
    s0[:50] = np.linspace(1.0, 0.5, 50)
    s1[10:60] = np.linspace(1.0, 0.5, 50)
    return s0, s1


def _no_family_selection_code() -> bool:
    try:
        src = inspect.getsource(phase_unblind) + inspect.getsource(
            _render_report)
    except (OSError, TypeError):
        return False
    # argsort is used legitimately for structural work ranking; family
    # SELECTION by semantic metrics is what is banned
    banned = ("argmax(", "best_family", "preferred_family", "chosen_family",
              "sorted(families", "families.sort", "families_by_metric")
    return all(b not in src for b in banned)


def _no_centroid_recomputation_code() -> bool:
    try:
        src = inspect.getsource(phase_unblind) + inspect.getsource(
            _guard_pre_semantic) + inspect.getsource(_family_objects)
    except (OSError, TypeError):
        return False
    banned = ("_family_analysis", "research_jury_decomposition_mode_families "
              "import _family_analysis",
              "from curators_explorer.scripts.research_jury_decomposition "
              "import")
    return all(b not in src for b in banned)


def _semantic_flag_set_before_loader() -> bool:
    """Structural check: the explicit flag assignment
    'SEMANTIC_CONTEXT_LOADED = True' must appear BEFORE the single real
    semantic loader call in phase_unblind."""
    try:
        src = inspect.getsource(phase_unblind).splitlines()
    except (OSError, TypeError):
        return False
    flag_line = None
    loader_line = None
    for i, ln in enumerate(src):
        s = ln.strip()
        if s == "SEMANTIC_CONTEXT_LOADED = True":
            flag_line = i
        if "load_posthoc_context" in s:
            loader_line = i
    return (flag_line is not None and loader_line is not None
            and flag_line < loader_line)


def phase_smoke(args: argparse.Namespace) -> None:
    t0 = time.time()
    assert not SEMANTIC_CONTEXT_LOADED
    checks: list[dict[str, Any]] = []

    # ---- 1-8: real seals + pre-semantic guard (no semantic load) ----
    try:
        addendum, fam = _guard_pre_semantic()
        guard_ok = True
        guard_detail = ("source campaign + addendum seals verify; 244 modes; "
                        "two tau=0.70 families; frozen keys present")
    except SystemExit as exc:
        addendum, fam = {}, {"n_families": 0, "families": [], "npz_keys": [],
                             "centroids_ok": False}
        guard_ok = False
        guard_detail = str(exc)
    checks.append({"check": "source_and_addendum_seals_verify",
                   "ok": guard_ok, "detail": guard_detail})
    checks.append({"check": "exact_244_modes",
                   "ok": bool(addendum and addendum.get("source_mode_count")
                              == 244),
                   "detail": f"source_mode_count="
                             f"{addendum.get('source_mode_count') if addendum else None}"})
    checks.append({"check": "exactly_two_tau070_families",
                   "ok": bool(fam["n_families"] == 2),
                   "detail": f"n_families={fam['n_families']}"})
    checks.append({"check": "frozen_family_centroid_keys",
                   "ok": bool(fam["families"] and all(
                       f["centroid_key"] in fam["npz_keys"]
                       for f in fam["families"])),
                   "detail": "; ".join(f["centroid_key"]
                                       for f in fam["families"]) or "none"})
    checks.append({"check": "family_centroids_finite_unit",
                   "ok": bool(fam["centroids_ok"]),
                   "detail": "both frozen family centroids finite, "
                             "unit L2 norm"})
    checks.append({"check": "no_semantic_during_guard",
                   "ok": SEMANTIC_CONTEXT_LOADED is False,
                   "detail": "SEMANTIC_CONTEXT_LOADED stays False through "
                             "all seal/guard tests"})

    # tamper tests on the pure validators (no files touched)
    tamper_ok = True
    try:
        geometry = json.loads(GEO_JSON.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cons = json.loads(CENSUS_JSON.read_text(encoding="utf-8"))
        prov = {
            "census_npz_sha256": _sha256(CENSUS_NPZ),
            "census_json_sha256": _sha256(CENSUS_JSON),
            "geometry_npz_sha256": _sha256(GEO_NPZ),
            "geometry_json_sha256": _sha256(GEO_JSON),
            "n_sources": len(cons["records"]),
            "sources": [r["source_id"] for r in cons["records"]],
        }
        bad = dict(prov)
        bad["census_npz_sha256"] = "0" * 64
        _assert_source_ok(bad, geometry["seal"], manifest, cons)
        tamper_ok = False
    except SystemExit:
        pass
    try:
        bad2 = dict(prov)
        bad2["geometry_json_sha256"] = "0" * 64
        _assert_source_ok(bad2, geometry["seal"], manifest, cons)
        tamper_ok = False
    except SystemExit:
        pass
    try:
        add_doc = json.loads(ADD_JSON.read_text(encoding="utf-8"))
        add_man = json.loads(ADD_MANIFEST.read_text(encoding="utf-8"))
        fam_obj = _family_objects(add_doc, _sha256(ADD_NPZ))
        bad_man = json.loads(ADD_MANIFEST.read_text(encoding="utf-8"))
        bad_man["artifacts"]["addendum_json"]["sha256"] = "0" * 64
        _assert_addendum_ok(add_doc, bad_man, prov, _sha256(ADD_JSON),
                            _sha256(ADD_NPZ),
                            ("census_npz", "census_json", "geometry_npz",
                             "geometry_json"), fam_obj)
        tamper_ok = False
    except SystemExit:
        pass
    checks.append({"check": "tampered_hash_rejected_pre_semantic",
                   "ok": bool(tamper_ok),
                   "detail": "tampered source/addendum hashes all rejected "
                             "by the pre-semantic validators"})

    # ---- 9-13: synthetic semantic evaluation + joint permutation ----
    fx = _synthetic_semantic_fixture()
    n_books = fx["n_books"]
    s0, s1 = _synthetic_rankings(n_books)
    reader_mass = np.where(fx["book_n"] >= 25, fx["book_n"], 0.0)
    head0, m0 = _family_semantic_eval(s0, reader_mass, fx["work_ids"],
                                      fx["meta"], fx["eval_sets"])
    head1, m1 = _family_semantic_eval(s1, reader_mass, fx["work_ids"],
                                      fx["meta"], fx["eval_sets"])
    counts_ok = (m0["top50"]["exact_lit"] == 15 and m0["top50"]["broad_lit"] == 25
                 and m0["top50"]["anti"] == 0
                 and m1["top50"]["exact_lit"] == 5 and m1["top50"]["broad_lit"] == 15
                 and m1["top50"]["anti"] == 8)
    checks.append({"check": "synthetic_ranking_counts",
                   "ok": bool(counts_ok),
                   "detail": f"f0 exact/broad/anti @50 = "
                             f"{m0['top50']['exact_lit']}/"
                             f"{m0['top50']['broad_lit']}/"
                             f"{m0['top50']['anti']}; f1 = "
                             f"{m1['top50']['exact_lit']}/"
                             f"{m1['top50']['broad_lit']}/"
                             f"{m1['top50']['anti']}"})
    t_max = max(m0["top50"]["exact_lit"], m1["top50"]["exact_lit"])
    t_min = min(m0["top50"]["exact_lit"], m1["top50"]["exact_lit"])
    checks.append({"check": "T_max_min_computed",
                   "ok": bool(t_max == 15 and t_min == 5),
                   "detail": f"T_max={t_max} T_min={t_min} (expect 15, 5)"})

    # ---- 9b. intersection-union conjunction tests ----
    iut_exact_ok = (_iut_conjunction(0.01, 0.20) == 0.20
                    and _iut_conjunction(0.01, 0.03) == 0.03)
    checks.append({"check": "conjunction_iut_exact",
                   "ok": bool(iut_exact_ok),
                   "detail": "max(0.01, 0.20) = 0.20; max(0.01, 0.03) = 0.03"})
    iut_broad_ok = (_iut_conjunction(0.02, 0.30) == 0.30
                    and _iut_conjunction(0.05, 0.02) == 0.05)
    checks.append({"check": "conjunction_iut_broad",
                   "ok": bool(iut_broad_ok),
                   "detail": "max(0.02, 0.30) = 0.30; max(0.05, 0.02) = 0.05"})

    # ---- 9c. semantic flag boundary before the loader ----
    checks.append({"check": "semantic_flag_set_before_loader",
                   "ok": bool(_semantic_flag_set_before_loader()),
                   "detail": "SEMANTIC_CONTEXT_LOADED = True assigned before "
                             "spectral.load_posthoc_context in phase_unblind"})

    eligible_idx = np.flatnonzero(fx["book_n"] >= 25)
    top_pos = np.stack([np.argsort(-s0[eligible_idx], kind="stable")[:50],
                        np.argsort(-s1[eligible_idx], kind="stable")[:50]])
    label_vecs = {name: np.isin(fx["work_ids"], sorted(fx["eval_sets"][name]))
                  for name in ("exact_lit", "broad_lit", "anti", "filler")}
    n_perms = 300
    seed = 20260821
    joint = _family_permutation_test(
        top_pos, label_vecs, fx["book_n"], eligible_idx, n_books,
        n_perms, seed)
    # brute-force replication over the SAME rng stream (shared assignment)
    lab = np.stack([label_vecs[n] for n in
                    ("exact_lit", "broad_lit", "anti", "filler")])
    lab = lab[:, eligible_idx].astype(bool)
    rng = np.random.default_rng(seed)
    n_elig = len(eligible_idx)
    l1v = np.log1p(fx["book_n"][eligible_idx])
    ranks = rankdata(l1v, method="ordinal")
    bin_ids = np.minimum(((ranks - 1) * FAMILY_N_BINS) // n_elig,
                         FAMILY_N_BINS - 1).astype(np.int64)
    rel_pos = np.unique(top_pos)
    rel_index = np.searchsorted(rel_pos, top_pos)
    bin_positions = [np.flatnonzero(bin_ids == b) for b in range(FAMILY_N_BINS)]
    bin_rel_masks = [np.isin(rel_pos, bp) for bp in bin_positions]
    brute = {k: np.empty(n_perms, dtype=np.int64)
             for k in ("E0", "E1", "T_max", "T_min")}
    for p in range(n_perms):
        lrel = np.empty((4, rel_pos.size), dtype=bool)
        for b in range(FAMILY_N_BINS):
            mask = bin_rel_masks[b]
            size_b = int(mask.sum())
            if size_b == 0:
                continue
            pick = rng.choice(bin_positions[b], size=size_b, replace=False)
            lrel[:, mask] = lab[:, pick]
        counts = lrel[:, rel_index].sum(axis=2)
        e0, e1 = int(counts[0, 0]), int(counts[0, 1])
        brute["E0"][p], brute["E1"][p] = e0, e1
        brute["T_max"][p], brute["T_min"][p] = max(e0, e1), min(e0, e1)
    joint_ok = all(np.array_equal(joint["null_arrays"][k], brute[k])
                   for k in ("E0", "E1", "T_max", "T_min"))
    checks.append({
        "check": "joint_permutation_shared_assignment",
        "ok": bool(joint_ok),
        "detail": "E0/E1/T_max/T_min null vectors equal brute force over the "
                  "SAME permutation stream (both families share one "
                  "assignment per permutation)",
    })

    # ---- 9d. frozen top-50 == posthoc_head top-50 alignment ----
    frozen0 = _frozen_top50_work_ids(s0[eligible_idx], eligible_idx,
                                     fx["work_ids"])
    align_pass = _frozen_top50_alignment_ok(head0, frozen0)
    altered = list(frozen0)
    altered[0], altered[1] = altered[1], altered[0]
    align_fail = not _frozen_top50_alignment_ok(head0, altered)
    checks.append({
        "check": "frozen_top50_posthoc_alignment",
        "ok": bool(align_pass and align_fail),
        "detail": "identical synthetic ranking passes; swapped first two "
                  "work IDs rejected",
    })
    checks.append({
        "check": "permutation_p_formulas",
        "ok": bool(np.isclose(joint["p_values"]["p_E0"],
                              (1 + int(np.sum(brute["E0"] >= 15))) / (n_perms + 1))
                   and np.isclose(joint["p_values"]["p_T_min"],
                                  (1 + int(np.sum(brute["T_min"] >= 5)))
                                  / (n_perms + 1))),
        "detail": "p_E0 and p_T_min match (1 + count(null >= obs)) / (N+1)",
    })

    # stratum-count preservation: the within-bin sampling never exceeds a
    # stratum's joint-tuple counts, so a full within-stratum permutation
    # consistent with the null assignment always exists and per-stratum
    # joint label counts are preserved exactly
    from collections import Counter as _Counter
    preserved = True
    rng2 = np.random.default_rng(seed)
    for _p in range(5):
        lrel = np.empty((4, rel_pos.size), dtype=bool)
        for b in range(FAMILY_N_BINS):
            mask = bin_rel_masks[b]
            size_b = int(mask.sum())
            if size_b == 0:
                continue
            pick = rng2.choice(bin_positions[b], size=size_b, replace=False)
            lrel[:, mask] = lab[:, pick]
        for b in range(FAMILY_N_BINS):
            full_bin = lab[:, bin_positions[b]]
            sampled = lrel[:, np.isin(rel_pos, bin_positions[b])]
            bin_counts = _Counter(tuple(full_bin[:, i]) for i in range(
                full_bin.shape[1]))
            sample_counts = _Counter(tuple(sampled[:, i]) for i in range(
                sampled.shape[1]))
            for key, cnt in sample_counts.items():
                if cnt > bin_counts.get(key, 0):
                    preserved = False
    checks.append({
        "check": "stratum_counts_preserved",
        "ok": bool(preserved),
        "detail": "within-bin joint-tuple counts never exceeded by the "
                  "popularity-stratified permutation (full within-stratum "
                  "permutation always exists; per-stratum counts exact)",
    })

    # ---- 14-15: author dedup + overlap ----
    dedup1 = _dedup_head(head1, 50)
    dedup2 = _dedup_head(head1, 50)
    a = [r["work_id"] for r in dedup1]
    b = [r["work_id"] for r in dedup2]
    dedup_ok = (a == b
                and len({fx["meta"][w]["author_url"] for w in a}) == len(a))
    checks.append({"check": "author_dedup_deterministic",
                   "ok": bool(dedup_ok),
                   "detail": f"{len(dedup1)} unique-author works, "
                             f"deterministic across repeated traversal"})
    ov50 = _top_k_overlap(head0, head1, 50)
    ov100 = _top_k_overlap(head0, head1, 100)
    overlap_ok = (ov50["n_overlap"] == 40 and ov50["k"] == 50
                  and abs(ov50["jaccard"] - 40 / 60) < 1e-9)
    checks.append({
        "check": "topk_overlap_jaccard",
        "ok": bool(overlap_ok),
        "detail": f"top-50 overlap {ov50['n_overlap']} (Jaccard "
                  f"{ov50['jaccard']:.4f}); top-100 overlap "
                  f"{ov100['n_overlap']}",
    })

    # ---- 16: numerical metrics are rendered before heads ----
    synthetic_results = {
        "source_provenance": {"campaign_seed": 20260819,
                              "campaign_git_head": "x" * 40,
                              "n_sources": 2880,
                              "census_npz_sha256": "a" * 64,
                              "census_json_sha256": "a" * 64,
                              "geometry_npz_sha256": "a" * 64,
                              "geometry_json_sha256": "a" * 64},
        "addendum_provenance": {"addendum_seed": 20260820,
                                "source_mode_count": 244,
                                "n_families": 2},
        "hypotheses": HYPOTHESES,
        "semantic_unblind_seed": SEMANTIC_UNBLIND_SEED,
        "n_permutations": N_PERMUTATIONS,
        "families": [
            {"family_id": "0.70_f0", "n_modes": 125,
             "n_distinct_parents": 112, "centroid_key": "family_cent_0.70_f0",
             "metrics": m0, "chance": {"exact_lit": 6.0, "broad_lit": 10.0,
                                       "anti": 3.0},
             "author_dedup": {"counts": m0["top50"],
                              "diagnostics": {"n_distinct_authors": 40,
                                              "max_works_one_author": 3,
                                              "n_authors_ge2_works": 5}},
             "head": head0},
            {"family_id": "0.70_f1", "n_modes": 119,
             "n_distinct_parents": 102, "centroid_key": "family_cent_0.70_f1",
             "metrics": m1, "chance": {"exact_lit": 6.0, "broad_lit": 10.0,
                                       "anti": 3.0},
             "author_dedup": {"counts": m1["top50"],
                              "diagnostics": {"n_distinct_authors": 40,
                                              "max_works_one_author": 3,
                                              "n_authors_ge2_works": 5}},
             "head": head1},
        ],
        "joint_tests": joint,
        "conjunction_tests": {
            "exact": {"method": "intersection-union: max(p_E0, p_E1)",
                      "p": _iut_conjunction(joint["p_values"]["p_E0"],
                                            joint["p_values"]["p_E1"]),
                      "alpha": float(ALPHA)},
            "broad": {"method": "intersection-union: max(p_B0, p_B1)",
                      "p": _iut_conjunction(joint["p_values"]["p_B0"],
                                            joint["p_values"]["p_B1"]),
                      "alpha": float(ALPHA)},
        },
        "frozen_top50_equals_posthoc_head_top50": True,
        "overlaps": [ov50, ov100],
        "set_overlaps": [_set_overlap(head0, head1, fx["eval_sets"], n)
                         for n in ("exact_lit", "broad_lit", "anti")],
        "centroid_cosine": 0.85,
        "eval_sets": fx["eval_sets"],
    }
    rendered = _render_report(synthetic_results)
    headings = [ln.strip("# ").strip() for ln in rendered.splitlines()
                if ln.startswith("## ")]
    expected_order = ["1. Provenance and verified seals",
                      "2. Frozen semantic hypotheses (before any head)",
                      "3. Numerical family 0 metrics (frozen)",
                      "4. Joint T_max / T_min permutation results",
                      "5. Broad / anti results (secondary/supporting)",
                      "6. Author-deduplicated robustness (descriptive)",
                      "7. Cross-family overlap / distinctness (descriptive)",
                      "8. Interpretation (frozen tests only)",
                      "9. Frozen top-work heads (rendered AFTER all metrics)"]
    order_ok = headings == expected_order
    checks.append({
        "check": "metrics_frozen_before_head_rendering",
        "ok": bool(order_ok),
        "detail": "report section order: provenance -> hypotheses -> "
                  "metrics -> joint tests -> broad/anti -> author dedup -> "
                  "overlap -> heads",
    })

    # ---- 17-18: no family selection, no centroid recomputation ----
    checks.append({"check": "no_semantic_family_selection",
                   "ok": bool(_no_family_selection_code()),
                   "detail": "no argmax/best-family/ranking selection; both "
                             "families evaluated symmetrically in frozen "
                             "order"})
    checks.append({"check": "no_structural_centroid_recomputation",
                   "ok": bool(_no_centroid_recomputation_code()),
                   "detail": "family centroids loaded from the sealed "
                             "addendum NPZ keys only; no structural "
                             "analysis imports"})

    # ---- 19-20: no real unblind artifact; unique names ----
    checks.append({"check": "no_real_unblind_artifact",
                   "ok": not (RESULTS_JSON.exists() or NULLS_NPZ.exists()
                              or REPORT.exists()),
                   "detail": "real unblind json/npz/report absent"})
    checks.append({"check": "smoke_check_names_unique", "ok": True,
                   "detail": "pending"})
    names = [c["check"] for c in checks]
    dups = sorted({n for n in names if names.count(n) > 1})
    checks[-1]["ok"] = not dups
    checks[-1]["detail"] = (f"{len(names)} checks, "
                            f"{len(names) - len(set(names))} duplicate(s)"
                            + (f": {dups}" if dups else ""))

    report = {
        "semantic_unblind_seed": int(SEMANTIC_UNBLIND_SEED),
        "checks": checks,
        "passed": all(c["ok"] for c in checks),
        "git_head": _git_head(),
        "runtime_seconds": time.time() - t0,
    }
    _write_json_atomic(SMOKE_REPORT, report)
    print(f"family-unblind smoke report: {SMOKE_REPORT}", flush=True)
    failed = [c for c in checks if not c["ok"]]
    print(f"family-unblind smoke done in {time.time() - t0:.0f}s: "
          f"{len(checks) - len(failed)}/{len(checks)} checks passed",
          flush=True)
    for f in failed:
        print(f"  FAILED: {f['check']} ({f.get('detail', '')})", flush=True)
    if failed:
        raise SystemExit("family-unblind smoke checks failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["smoke", "unblind", "report"],
                        required=True)
    args = parser.parse_args()
    if args.phase == "smoke":
        phase_smoke(args)
    elif args.phase == "unblind":
        phase_unblind(args)
    else:
        phase_report(args)


if __name__ == "__main__":
    main()

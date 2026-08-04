#!/usr/bin/env python3
"""Ranking methods over unordered SF star ratings."""

from __future__ import annotations

import math
from typing import Any

from ucsd_explorer.catalog_flags import catalog_sql_bits, parse_catalog_params
from ucsd_explorer.db import GLOBALS, execute
from ucsd_explorer.genres import (
    SF_PRESET_INCLUDE,
    genre_sql_bits,
    has_genre_tables,
    parse_genre_params,
)
from ucsd_explorer.taste_query import (
    has_curator_deep_weights,
    has_curator_pct_pure_weights,
    has_curator_pct_weights,
    has_curator_pure_weights,
    has_curator_weights,
    has_lit_weights,
    has_taste_tables,
    parse_taste_params,
    taste_eligible_cte,
)
from ucsd_explorer.work_years import year_sql_bits

METHODS = [
    {
        "id": "curator_pct_love",
        "name": "Curator‰ love (power)",
        "blurb": "Literary-anchored percentiles^ρ as love *mass over the whole curator cohort* (unrated→0). Soft-deweight + coverage; fan-only YA/picture spikes cannot beat widely rated classics. Table 5★ column = literal Goodreads 5★s among curators (score uses personal top-shelf percentiles).",
    },
    {
        "id": "curator_pure_pct_love",
        "name": "Pure Curator‰ love",
        "blurb": "Same coverage love score on a stricter cohort: high lit_share, few commercial 5★s, weight penalized by com_share. Taste-filter framing baked into curator selection.",
    },
    {
        "id": "curator_deep_pct_love",
        "name": "Deep Curator‰ love",
        "blurb": "Love among curators who go past normie prestige (school-canon / ubiquitous 'quality') into rarer poll-chart works. RYM analogy: Kubrick-only users don't mint follows.",
    },
    {
        "id": "curator_deep_pct_geom",
        "name": "Deep Curator‰ top-half geom",
        "blurb": "Only ★≥3 ratings in each curator’s top-half shelf (pct≥0.5). Contribution = geometric(★)·pct^x — ratio slider sets 5:4:3 = q²:q:1; power slider sharpens loves. Coverage over the deep cohort.",
    },
    {
        "id": "curator_pct_asymm",
        "name": "Curator‰ love − hate",
        "blurb": "Asymmetric love−hate mass / cohort W (unrated→0). Soft-deweight + coverage against fan-only samples.",
    },
    {
        "id": "curator_pct_tilt",
        "name": "Curator‰ love−tilt (soft hate)",
        "blurb": "Like love−hate but with a much weaker hate term — middle ground when full love−hate floors school canon too hard.",
    },
    {
        "id": "curator_deep_pct_tilt",
        "name": "Deep Curator‰ love−tilt",
        "blurb": "Soft love−tilt on the deep (non-normie) curator cohort.",
    },
    {
        "id": "curator_pure_pct_asymm",
        "name": "Pure Curator‰ love − hate",
        "blurb": "Asymmetric love−hate on the pure (low non-literary 5★) curator cohort.",
    },
    {
        "id": "curator_pct_gap",
        "name": "Curator‰ top−upper-mid gap",
        "blurb": "Top−upper-mid mass / cohort W. 5★-vs-4★ analogue with coverage so only-fans books shrink.",
    },
    {
        "id": "curator_pure_pct_gap",
        "name": "Pure Curator‰ top−mid gap",
        "blurb": "Top−upper-mid gap on the pure anti-commercial curator cohort.",
    },
    {
        "id": "curator_pct_top",
        "name": "Curator‰ top-shelf rate",
        "blurb": "Top-shelf mass / cohort W (not among raters only). Closest to cohort-wide Bayesian favorite rate.",
    },
    {
        "id": "curator_pure_pct_top",
        "name": "Pure Curator‰ top-shelf",
        "blurb": "Top-shelf rate on the pure (few commercial 5★s) curator cohort.",
    },
    {
        "id": "curator_pct_gem",
        "name": "Curator‰ hidden gem",
        "blurb": "Coverage top-rate × log(rater mass), soft-cap Kish n. Rare literary/SF gems among percentile curators.",
    },
    {
        "id": "curator_pure_pct_gem",
        "name": "Pure Curator‰ hidden gem",
        "blurb": "Hidden-gem score on pure curators — literary lean without gushing over commercial anti-signals.",
    },
    {
        "id": "curator_pct_mean",
        "name": "Curator‰ Bayesian mean",
        "blurb": "Cohort mean percentile with unrated imputed at prior. Gentler than love; still coverage-aware.",
    },
    {
        "id": "curator_pure_pct_mean",
        "name": "Pure Curator‰ Bayesian mean",
        "blurb": "Coverage mean percentile on the pure anti-commercial curator cohort.",
    },
    {
        "id": "curator_five_rate",
        "name": "Curator 5★ rate (RYM)",
        "blurb": "Original star-based RYM gates (moderate mean/five-rate). Bayesian 5★ rate among those curators. Kept for posterity.",
    },
    {
        "id": "curator_pure_five_rate",
        "name": "Pure Curator 5★ rate",
        "blurb": "Star RYM curators further gated for high lit_share / low commercial 5★ pollution.",
    },
    {
        "id": "curator_mean",
        "name": "Curator Bayesian mean (RYM)",
        "blurb": "Original star-based curator cohort. IMDb-style mean. Kept for posterity.",
    },
    {
        "id": "curator_pure_mean",
        "name": "Pure Curator Bayesian mean",
        "blurb": "IMDb-style mean on the pure (anti-commercial) star curator cohort.",
    },
    {
        "id": "curator_gem",
        "name": "Curator hidden gem (RYM)",
        "blurb": "Original star-based curator 5★ rate × log(weight). Kept for posterity.",
    },
    {
        "id": "curator_pure_gem",
        "name": "Pure Curator hidden gem",
        "blurb": "Hidden gem on pure star curators (strict non-literary 5★ gate).",
    },
    {
        "id": "curator_liked",
        "name": "Curator strong-like (RYM)",
        "blurb": "Original star-based curator ≥4★ share. Kept for posterity.",
    },
    {
        "id": "curator_pure_liked",
        "name": "Pure Curator strong-like",
        "blurb": "≥4★ share on the pure anti-commercial star curator cohort.",
    },
    {
        "id": "combo_five_rate",
        "name": "Combo: lit×picky 5★ rate",
        "blurb": "P(5★) with user weight = poll-prestige lit_weight × picky^α. Literary taste + stingy 5★s. Divisive OK.",
    },
    {
        "id": "picky_five_rate",
        "name": "Picky 5★ rate (among stingy users)",
        "blurb": "5★ rate using only users below median five-star rate.",
    },
    {
        "id": "combo_mean",
        "name": "Combo: lit×picky Bayesian mean",
        "blurb": "IMDb-style mean with lit×picky weights. Rewards sustained quality (solid 4★s), not only gushing 5★ rates — fills the gap when combo 5★ rate overfits finales & tiny prestige samples.",
    },
    {
        "id": "combo_liked",
        "name": "Combo: lit×picky strong-like (≥4★)",
        "blurb": "Share of lit×picky weight on ratings ≥4. Literary picky readers often reserve 5★s; this keeps books they firmly like without requiring a favorite stamp.",
    },
    {
        "id": "picky_gem",
        "name": "Picky hidden gem",
        "blurb": "Stingy-user 5★ rate × log(n), soft-cap mega-hits. Same signal as picky 5★ rate, less ACOTAR/Stormlight/omnibus dominance.",
    },
    {
        "id": "cross_five",
        "name": "Cross: lit×picky ∩ stingy 5★",
        "blurb": "Geometric mean of lit×picky 5★ rate and stingy-only 5★ rate. Books both literary prestige readers and general stingy users crown — cuts language bubbles and romance-only spikes.",
    },
    {
        "id": "combo_gem",
        "name": "Combo hidden gem",
        "blurb": "Combo 5★ rate × log(weight mass), soft-cap mega-hits. Best default for literary SF gems.",
    },
    {
        "id": "combo_five_mass",
        "name": "Combo 5★ mass",
        "blurb": "Sum of lit×picky weights on 5★ only. Favours books beloved by literary picky readers.",
    },
    {
        "id": "combo_power",
        "name": "Combo power-mean (5★ focus)",
        "blurb": "Lit×picky weighted mean with (rating/5)^3.5 so 5★ dominate; 1–3★ barely count. Fine with love/hate splits.",
    },
    {
        "id": "combo_wilson",
        "name": "Combo Wilson 5★",
        "blurb": "Wilson lower bound on lit×picky 5★ rate — confident favorites among literary picky raters.",
    },
    {
        "id": "combo_love",
        "name": "Combo love density",
        "blurb": "Lit×picky 5★ mass / soft√n. Surfaces cult love (divisive OK) without needing a high overall 5★ rate.",
    },
    {
        "id": "five_rate_bayes",
        "name": "Bayesian 5★ rate",
        "blurb": "Share of ratings that are 5★, shrunk toward the global rate.",
    },
    {
        "id": "imdb_bayes",
        "name": "IMDb/RYM-style Bayesian mean",
        "blurb": "Classic WR = (v/(v+m))·R + (m/(v+m))·C on (optionally taste-filtered) ratings. Good all-purpose quality score.",
    },
    {
        "id": "five_count",
        "name": "5★ count",
        "blurb": "How many people called this a favorite (raw 5★). Popular books dominate.",
    },
    {
        "id": "lit_weighted_mean",
        "name": "Literary-weighted mean",
        "blurb": "Each rating weighted by lit_share × ln(1+prestige-mass). Heavy literary readers count more.",
    },
    {
        "id": "lit_weighted_five",
        "name": "Literary-weighted 5★ mass",
        "blurb": "Sum of literary weights on 5★ events. Favours books beloved by deep literary readers.",
    },
    {
        "id": "lit_weighted_five_rate",
        "name": "Literary-weighted Bayesian 5★ rate",
        "blurb": "Weighted P(5★) among literary-weighted raters, Bayesian-shrunk.",
    },
    {
        "id": "lit_gem",
        "name": "Literary hidden gem",
        "blurb": "Literary-weighted Bayesian 5★ rate × log(effective n), soft-penalize mega-hits.",
    },
    {
        "id": "picky_five",
        "name": "Picky-weighted 5★",
        "blurb": "Each 5★ weighted by how rarely that user gives 5★.",
    },
    {
        "id": "polarization",
        "name": "Polarization (love × dislike)",
        "blurb": "4·P(5★)·P(≤2★). Divisive titles.",
    },
    {
        "id": "stddev",
        "name": "Rating spread (σ)",
        "blurb": "Population stddev of stars.",
    },
    {
        "id": "hidden_gem",
        "name": "Hidden gem (generic)",
        "blurb": "Bayesian 5★ rate × log10(n), soft-cap mega-hits. Not literary-specific.",
    },
    {
        "id": "mean",
        "name": "Mean rating",
        "blurb": "Simple Bayesian-shrunk average.",
    },
]

LIT_METHODS = {
    "lit_weighted_mean",
    "lit_weighted_five",
    "lit_weighted_five_rate",
    "lit_gem",
}

# lit×picky(+rating emphasis) methods — always need dynamic re-aggregation
COMBO_METHODS = {
    "combo_five_rate",
    "combo_gem",
    "combo_five_mass",
    "combo_power",
    "combo_wilson",
    "combo_love",
    "combo_mean",
    "combo_liked",
}

# Needs both lit×picky and stingy-only rates in one aggregation
CROSS_METHODS = {
    "cross_five",
}

# Original star-gated RYM curator cohort
CURATOR_STAR_METHODS = {
    "curator_five_rate",
    "curator_mean",
    "curator_gem",
    "curator_liked",
}

# Star cohort + strict anti-commercial / high lit lean (taste-filter framing)
CURATOR_PURE_STAR_METHODS = {
    "curator_pure_five_rate",
    "curator_pure_mean",
    "curator_pure_gem",
    "curator_pure_liked",
}

# Percentile curator cohort (no moderate mean gate; Criticker midpoints)
CURATOR_PCT_METHODS = {
    "curator_pct_love",
    "curator_pct_asymm",
    "curator_pct_gap",
    "curator_pct_top",
    "curator_pct_gem",
    "curator_pct_mean",
}

# Percentile + strict anti-commercial / high lit lean
CURATOR_PURE_PCT_METHODS = {
    "curator_pure_pct_love",
    "curator_pure_pct_asymm",
    "curator_pure_pct_gap",
    "curator_pure_pct_top",
    "curator_pure_pct_gem",
    "curator_pure_pct_mean",
}

# Non-normie poll depth cohort (school-canon alone does not mint curators)
CURATOR_DEEP_PCT_METHODS = {
    "curator_deep_pct_love",
    "curator_deep_pct_tilt",
    "curator_deep_pct_geom",
}

# Soft hate tilt on the standard pct cohort
CURATOR_TILT_METHODS = {
    "curator_pct_tilt",
}

CURATOR_METHODS = (
    CURATOR_STAR_METHODS
    | CURATOR_PURE_STAR_METHODS
    | CURATOR_PCT_METHODS
    | CURATOR_PURE_PCT_METHODS
    | CURATOR_DEEP_PCT_METHODS
    | CURATOR_TILT_METHODS
)

# Methods that use percentile tables / coverage scores
CURATOR_PCT_FAMILY = (
    CURATOR_PCT_METHODS
    | CURATOR_PURE_PCT_METHODS
    | CURATOR_DEEP_PCT_METHODS
    | CURATOR_TILT_METHODS
)
CURATOR_STAR_FAMILY = CURATOR_STAR_METHODS | CURATOR_PURE_STAR_METHODS

PICKY_RATE_METHODS = {
    "picky_five_rate",
    "picky_gem",
}

WEIGHTED_METHODS = LIT_METHODS | COMBO_METHODS | CROSS_METHODS | CURATOR_METHODS

# Tunables for combo scorers (adjusted against SF literary smoke tests)
PICKY_EXP = 0.9
RATING_POWER = 3.5
COMBO_SOFT = 10000.0
CURATOR_SOFT = 8000.0
PICKY_GEM_SOFT = 8000.0
WILSON_Z = 1.645  # ~90% one-sided
COMBO_SMALL_M = 20.0  # shrink tiny weight-mass samples in gem/wilson
CURATOR_SMALL_M = 12.0
# Criticker percentile love: power > 1 deweights mid-shelf ratings
PCT_LOVE_POWER = 3.2
PCT_HATE_POWER = 2.2
PCT_HATE_LAMBDA = 1.35  # how hard bottom-shelf ratings pull down asymm score
PCT_TILT_HATE_LAMBDA = 0.45  # soft middle ground between love and love−hate
PCT_GAP_MID_COEF = 0.55  # subtract this × upper-mid mass from top mass
PCT_TOP_THRESH = 0.88
PCT_MID_LO = 0.70
PCT_BOTTOM_THRESH = 0.25
PCT_PRIOR = 0.50  # Bayesian prior for mean percentile
PCT_TOP_PRIOR = 0.15
# Deep geom: only top-half shelf + ★∈{3,4,5}; weights 5:4:3 = q²:q:1
PCT_GEOM_TOP_HALF = 0.50
PCT_GEOM_RATIO_DEFAULT = 2.0
PCT_GEOM_POWER_DEFAULT = 2.5
# Coverage blend for ‰ mass scores.
# Slider u∈[0,1] linearly interpolates the among-raters score and the
# full-cohort score (unread→0). Denominator blending made almost all
# perceptible change pile up near u≈0; score blending is linear by design.
PCT_COVERAGE_DEFAULT = 1.0


def _pct_coverage_score(mass_expr: str, m: float, coverage: float) -> str:
    """SQL: (1−u)·(mass/(w_sum+m)) + u·(mass/(W+m))."""
    u = max(0.0, min(1.0, float(coverage)))
    among = (
        f"(({mass_expr}) / (coalesce(agg.w_sum, 0) + ({m})::DOUBLE))"
    )
    full = (
        f"(({mass_expr}) / ((SELECT W FROM curator_cohort) + ({m})::DOUBLE))"
    )
    return (
        f"((1.0 - ({u})::DOUBLE) * {among} + ({u})::DOUBLE * {full})"
    )


def _book_filter_sql(q: str, alias: str = "w") -> tuple[str, list[Any]]:
    if not q:
        return "", []
    like = f"%{q}%"
    return (
        f" AND ({alias}.title ILIKE ? OR {alias}.author ILIKE ? OR {alias}.book_id = ? OR {alias}.work_id = ?)",
        [like, like, q, q],
    )


def _rows_to_results(rows: list) -> list[dict[str, Any]]:
    results = []
    for i, row in enumerate(rows, start=1):
        (
            work_id,
            book_id,
            title,
            author,
            book_url,
            n,
            mean,
            std,
            n5,
            n1,
            n_low,
            p5,
            p_low,
            pol,
            score,
        ) = row
        results.append(
            {
                "rank": i,
                "work_id": work_id,
                "book_id": book_id,
                "title": title,
                "author": author,
                "book_url": book_url,
                "n": int(n),
                "n5": int(n5),
                "n1": int(n1 or 0),
                "mean": float(mean) if mean is not None else None,
                "std": float(std) if std is not None else None,
                "p5": float(p5) if p5 is not None else None,
                "p_low": float(p_low) if p_low is not None else None,
                "polarization": float(pol) if pol is not None else None,
                "score": float(score) if score is not None else 0.0,
                "votes": int(n),
            }
        )
    return results


def _int_param(params: dict[str, Any], *keys: str, default: int) -> int:
    """Read an int without treating 0 as missing (unlike `x or default`)."""
    for key in keys:
        if key not in params:
            continue
        val = params[key]
        if val is None or val == "":
            continue
        return int(val)
    return default


def _float_param(params: dict[str, Any], *keys: str, default: float) -> float:
    for key in keys:
        if key not in params:
            continue
        val = params[key]
        if val is None or val == "":
            continue
        return float(val)
    return default


def _curator_score_method(method: str) -> str:
    """Map pure/deep curator method ids onto the shared score formula keys."""
    if method.startswith("curator_deep_pct_"):
        rest = method[len("curator_deep_pct_") :]
        if rest == "tilt":
            return "curator_pct_asymm"  # soft λ applied when building pct_asymm
        if rest == "geom":
            return "curator_pct_geom"
        return "curator_pct_" + rest
    if method == "curator_pct_tilt":
        return "curator_pct_asymm"
    if method.startswith("curator_pure_pct_"):
        return "curator_pct_" + method[len("curator_pure_pct_") :]
    if method.startswith("curator_pure_"):
        return "curator_" + method[len("curator_pure_") :]
    return method


CURATOR_ELITE_FLOOR = 100  # curator strictness=100 → keep ~this many users
NORMIE_MAX_DEEP = 20  # normie strictness=100 → min non-normie poll ★≥4


def _clamp_strictness(strictness: float) -> float:
    """Curator / normie sliders: 0 (off) … 100 (max)."""
    return max(0.0, min(100.0, float(strictness)))


def _strictness_t(strictness: float) -> float:
    return _clamp_strictness(strictness) / 100.0


def _log_lerp(a: float, b: float, t: float) -> float:
    """Log-linear interpolation — equal slider steps ≈ equal multiplicative change."""
    a = max(a, 1e-9)
    b = max(b, 1e-9)
    return math.exp(math.log(a) + t * (math.log(b) - math.log(a)))


def curator_elite_keep_expr(strictness: float, n_pass_expr: str = "n_pass") -> str:
    """SQL expression: how many top-weighted curators to keep.

    t=0 → all passers (disabled). t=1 → ~100 (or all if fewer pass).
    Log-linear in cohort size so the slider feels roughly even.
    """
    t = _strictness_t(strictness)
    if t <= 1e-12:
        return n_pass_expr
    # K = n_pass^(1-t) * min(FLOOR, n_pass)^t
    return (
        f"CAST(ceil(power(greatest({n_pass_expr}, 1)::DOUBLE, {1.0 - t}) "
        f"* power(least({float(CURATOR_ELITE_FLOOR)}::DOUBLE, "
        f"greatest({n_pass_expr}, 1)::DOUBLE), {t})) AS BIGINT)"
    )


def curator_strictness_gates(strictness: float, *, pct: bool) -> dict[str, float | int]:
    """Legacy volume floors for gate mode / readout.

    Primary curator shrink is top-K elite keep (see curator_elite_keep_expr).
    At strictness 0 these floors are minimal (effectively off).
    """
    t = _strictness_t(strictness)
    if pct:
        return {
            "min_n_rated": int(round(0 + t * 100)),  # 0..100 (0 = off)
            "min_poll_works": int(round(0 + t * 8)),  # 0..8
            "min_rare_poll": int(round(0 + t * 3)),  # 0..3
            "min_lit_hits": int(round(0 + t * 8)),  # 0..8
            "max_com_ratio": 0.90 - t * 0.55,  # 0.90..0.35
            "min_weight_pctile": 0.0,  # elite keep handles ranking cut
        }
    return {
        "min_n_rated": int(round(0 + t * 120)),
        "min_poll_works": int(round(0 + t * 10)),
        "min_rare_poll": int(round(0 + t * 4)),
        "min_lit_hits": int(round(0 + t * 10)),
        "max_com_ratio": 0.75 - t * 0.50,
        "min_weight_pctile": 0.0,
    }


def curator_deweight_alpha(strictness: float) -> float:
    """Mild within-elite soft deweight. 0 at slider 0 (fully off)."""
    t = _strictness_t(strictness)
    return 3.0 * t  # was up to 14; elite keep is the real shrink now


def normie_depth_params(depth: float) -> dict[str, float | int | bool]:
    """Map 0–100 → min non-normie poll depth (and a mild rare-poll floor).

    0 = off. 100 ≈ min_deep 20 (enough that popular books land near ≤50 votes
    when purity is also high). Rare floor scales with depth so "only chart-top
    deep books" is not enough at high settings.
    """
    t = _strictness_t(depth)
    if t <= 1e-12:
        return {"enabled": False, "min_deep": 0, "min_deep_rare": 0}
    min_deep = int(round(_log_lerp(2.0, float(NORMIE_MAX_DEEP), t)))
    # Milder than the old combined slider — purity owns anti-school now.
    min_deep_rare = max(0, int(round(min_deep * (0.20 + 0.20 * t))))
    return {"enabled": True, "min_deep": min_deep, "min_deep_rare": min_deep_rare}


def normie_purity_params(purity: float) -> dict[str, float | int | bool]:
    """Map 0–100 → deep_share floor (non-normie / (non-normie + normie) among ★≥4).

    0 = off (no share gate). 100 ≈ share ≥ 0.80. This is the Kubrick-only /
    school-canon filter, independent of how many deep books someone has.
    """
    t = _strictness_t(purity)
    if t <= 1e-12:
        return {"enabled": False, "min_deep_share": 0.0}
    # Soft start at 0.35 so low purity still admits dual-canon readers.
    return {"enabled": True, "min_deep_share": 0.35 + t * 0.45}


def deep_com_share_cap(purity: float) -> float:
    """Query-time max non-literary anti-signal share for deep curators.

    Independent of school-canon purity, but tightens gently with it:
    purity 0 → 0.15, purity 100 → 0.08. Materialization already uses a
    wider floor (≈0.20) and (1−com_share)^com_exp in stored weights.
    """
    t = _strictness_t(purity)
    return 0.15 - t * 0.07


def normie_gate_params(
    depth: float = 0.0,
    purity: float = 0.0,
    *,
    # Back-compat: old single slider applied the same value to both axes.
    strictness: float | None = None,
) -> dict[str, float | int | bool]:
    if strictness is not None and _clamp_strictness(depth) <= 0 and _clamp_strictness(purity) <= 0:
        depth = purity = float(strictness)
    d = normie_depth_params(depth)
    p = normie_purity_params(purity)
    enabled = bool(d.get("enabled") or p.get("enabled"))
    return {
        "enabled": enabled,
        "min_deep": int(d["min_deep"]),
        "min_deep_rare": int(d["min_deep_rare"]),
        "min_deep_share": float(p["min_deep_share"]),
        "depth": _clamp_strictness(depth),
        "purity": _clamp_strictness(purity),
        "share_power": 0.0,
    }


def normie_strictness_params(strictness: float) -> dict[str, float | int | bool]:
    """Back-compat wrapper: old combined slider → depth=purity=strictness."""
    return normie_gate_params(strictness=strictness)


def _normie_gate_sql(
    depth: float = 0.0,
    purity: float = 0.0,
    *,
    strictness: float | None = None,
    alias: str = "c",
) -> tuple[str, list[Any]]:
    p = normie_gate_params(depth, purity, strictness=strictness)
    if not p.get("enabled"):
        return "", []
    a = alias
    clauses: list[str] = []
    args: list[Any] = []
    if int(p["min_deep"]) > 0:
        clauses.append(f"AND {a}.n_deep >= ?")
        args.append(int(p["min_deep"]))
    if int(p["min_deep_rare"]) > 0:
        clauses.append(f"AND {a}.n_deep_rare >= ?")
        args.append(int(p["min_deep_rare"]))
    if float(p["min_deep_share"]) > 1e-12:
        clauses.append(f"AND {a}.deep_share >= ?")
        args.append(float(p["min_deep_share"]))
    if not clauses:
        return "", []
    return "\n        " + "\n        ".join(clauses) + "\n    ", args


def curator_deweight_exponent(strictness: float) -> float:
    """Back-compat alias: report α as the UI 'exp' readout."""
    return curator_deweight_alpha(strictness)


def _curator_gate_sql(gates: dict[str, float | int], alias: str = "c") -> tuple[str, list[Any]]:
    """SQL fragment + args filtering a curator weight table alias."""
    a = alias
    sql = f"""
        AND {a}.n_rated >= ?
        AND {a}.n_poll_works >= ?
        AND {a}.n_rare_poll >= ?
        AND {a}.lit_hits >= ?
        AND {a}.com_hits::DOUBLE <= greatest(
            2.0,
            {a}.lit_hits::DOUBLE * ?
        )
        AND coalesce({a}.weight_pctile, 0) >= ?
    """
    args: list[Any] = [
        int(gates["min_n_rated"]),
        int(gates["min_poll_works"]),
        int(gates["min_rare_poll"]),
        int(gates["min_lit_hits"]),
        float(gates["max_com_ratio"]),
        float(gates["min_weight_pctile"]),
    ]
    return sql, args


def _curator_user_weight_sql(
    *,
    pct: bool,
    mode: str,
    strictness: float,
    alias: str = "c",
    deep: bool = False,
    normie_depth: float = 0.0,
    normie_purity: float = 0.0,
    normie_strictness: float | None = None,
) -> tuple[str, str, list[Any], float]:
    """Return (weight_expr, pre_elite_gate_sql, gate_args, elite_t).

    Cohort shrink is log-linear top-K by curator weight (elite_t from strictness).
    pre_elite_gate_sql applies volume (+ optional normie depth/purity) floors.

    mode=deweight: keep base curator weights among elites (mild α).
    mode=gate: equal weight 1.0 among elites (pure top-K vote).
    """
    a = alias
    base_w = f"{a}.curator_pct_weight" if pct else f"{a}.curator_weight"
    mode = (mode or "deweight").strip().lower()
    if mode not in ("deweight", "gate"):
        mode = "deweight"

    elite_t = _strictness_t(strictness)
    # Volume floors stay minimal at 0 so "off" really means off.
    gate_sql, gate_args = _curator_gate_sql(
        curator_strictness_gates(strictness, pct=pct), alias=a
    )

    if mode == "gate":
        # Equal votes among elites, but deep cohort still soft-penalizes
        # commercial anti-signal share so gate mode cannot re-inflate junk.
        if deep:
            com = (
                f"(coalesce({a}.com_hits,0)::DOUBLE"
                f" / nullif(coalesce({a}.lit_hits,0)+coalesce({a}.com_hits,0),0))"
            )
            weight_expr = (
                f"(power(greatest(1.0 - coalesce({com}, 0), 0.02), 3.0))"
            )
        else:
            weight_expr = "1.0"
    else:
        alpha = curator_deweight_alpha(strictness)
        if alpha <= 1e-12:
            weight_expr = f"({base_w})"
        else:
            weight_expr = (
                f"({base_w} * exp(-({alpha}) * (1.0 - coalesce({a}.weight_pctile, 0))))"
            )

    if deep:
        n_sql, n_args = _normie_gate_sql(
            normie_depth,
            normie_purity,
            strictness=normie_strictness,
            alias=a,
        )
        gate_sql = gate_sql + n_sql
        gate_args = list(gate_args) + n_args
        # Always apply a query-time commercial cap for deep methods.
        # Use purity when set; otherwise the mid default (purity≈55 → ~0.11).
        pur_for_com = (
            float(normie_purity)
            if _clamp_strictness(normie_purity) > 0
            else (
                float(normie_strictness)
                if normie_strictness is not None
                and _clamp_strictness(float(normie_strictness)) > 0
                else 55.0
            )
        )
        com_cap = deep_com_share_cap(pur_for_com)
        com = (
            f"(coalesce({a}.com_hits,0)::DOUBLE"
            f" / nullif(coalesce({a}.lit_hits,0)+coalesce({a}.com_hits,0),0))"
        )
        gate_sql = (
            gate_sql
            + f"\n        AND coalesce({com}, 0) <= {float(com_cap)}\n    "
        )

    return weight_expr, gate_sql, gate_args, elite_t


def parse_sf_only(params: dict[str, Any]) -> bool:
    """True when the active filter is the SF any-of preset (or legacy sf_only).

    Prefer ``parse_genre_params`` / genre SQL for filtering. This flag only
    selects SF vs all-genre Bayesian priors and legacy ``is_sf`` fallbacks.
    """
    genres = parse_genre_params(params)
    if genres.get("require") or genres.get("exclude"):
        return False
    inc = set(genres.get("include") or [])
    if not inc:
        return False
    return inc <= set(SF_PRESET_INCLUDE)


def scope_globals(sf_only: bool) -> tuple[float, float]:
    """Return (global_p5, global_mean) for the active genre scope."""
    if sf_only:
        p0 = float(GLOBALS.get("global_p5_sf", GLOBALS.get("global_p5", 0.4)))
        c0 = float(GLOBALS.get("global_mean_sf", GLOBALS.get("global_mean", 3.8)))
    else:
        p0 = float(GLOBALS.get("global_p5_all", GLOBALS.get("global_p5", 0.4)))
        c0 = float(GLOBALS.get("global_mean_all", GLOBALS.get("global_mean", 3.8)))
    return p0, c0


def _event_sf_pred(sf_only: bool, alias: str = "e") -> str:
    """Legacy event.is_sf filter when genre tables are unavailable."""
    if not (sf_only and not has_genre_tables()):
        return ""
    col = f"{alias}.is_sf" if alias else "is_sf"
    return f" AND {col}"


def _rank_filter_bits(
    *,
    catalog: dict[str, bool] | None,
    year_min: int | None,
    year_max: int | None,
    q: str,
    genres: dict[str, list[str]] | None,
    work_alias: str,
    score_expr: str | None = None,
    sf_only: bool = False,
) -> tuple[str, str, str, list[Any]]:
    """Shared catalog + year + search + genre wiring for rank SQL paths.

    Returns ``(joins, where_suffix, scored_expr, extra_args)`` where
    ``extra_args`` is book ILIKE args + year-range args + genre args.
    """
    book_filter, book_args = _book_filter_sql(q, work_alias)
    genre_where, genre_args = genre_sql_bits(genres, work_alias=work_alias)
    sf_fallback = ""
    if not has_genre_tables() and sf_only:
        sf_fallback = f" AND {work_alias}.is_sf"
    cat_join, cat_where, scored = catalog_sql_bits(
        catalog, work_alias=work_alias, flags_alias="cf", score_expr=score_expr
    )
    year_join, year_where, year_args = year_sql_bits(
        year_min, year_max, work_alias=work_alias
    )
    joins = f"{cat_join}{year_join}"
    where_suffix = f"{sf_fallback}{genre_where}{book_filter}{cat_where}{year_where}"
    # Placeholder order must match where_suffix: genre → book → year
    return joins, where_suffix, scored, genre_args + book_args + year_args


def rank_books(params: dict[str, Any]) -> dict[str, Any]:
    method = params.get("method") or "five_rate_bayes"
    # Default 1 (not 30): HTML min is 1; the old `x or 30` treated 0/"" as 30 and
    # looked like a hard floor whenever the field was cleared.
    min_n = max(0, _int_param(params, "min_votes", "min_n", default=1))
    max_n = max(0, _int_param(params, "max_n", default=0))
    bayesian_m = max(0.0, _float_param(params, "bayesian_m", default=50.0))
    limit = min(max(1, _int_param(params, "limit", default=200)), 1000)
    q = (params.get("q") or "").strip()
    genres = parse_genre_params(params)
    sf_only = parse_sf_only(params)
    picky_max = params.get("picky_max_five_rate")
    if picky_max is None or picky_max == "":
        picky_max = GLOBALS["median_user_five_rate"]
    else:
        picky_max = float(picky_max)

    taste = parse_taste_params(params)
    catalog = parse_catalog_params(params)
    year_min = _int_param(params, "year_min", default=0) or None
    year_max = _int_param(params, "year_max", default=0) or None
    if year_min is not None and year_min <= 0:
        year_min = None
    if year_max is not None and year_max <= 0:
        year_max = None
    if taste and not has_taste_tables():
        raise ValueError(
            "Taste tables missing. Run: .venv/bin/python -m ucsd_explorer.taste"
        )
    if method in WEIGHTED_METHODS and not has_lit_weights() and method not in CURATOR_METHODS:
        raise ValueError(
            "Literary weights missing. Run: .venv/bin/python -m ucsd_explorer.taste"
        )
    if method in CURATOR_STAR_METHODS and not has_curator_weights():
        raise ValueError(
            "Curator weights missing. Run: .venv/bin/python -m ucsd_explorer.taste"
        )
    if method in CURATOR_PCT_METHODS | CURATOR_TILT_METHODS and not has_curator_pct_weights():
        raise ValueError(
            "Percentile curator tables missing. Run: .venv/bin/python -m ucsd_explorer.taste"
        )
    if method in CURATOR_PURE_STAR_METHODS and not has_curator_pure_weights():
        raise ValueError(
            "Pure curator weights missing. Run: .venv/bin/python -m ucsd_explorer.taste --pure-only"
        )
    if method in CURATOR_PURE_PCT_METHODS and not has_curator_pct_pure_weights():
        raise ValueError(
            "Pure percentile curator tables missing. "
            "Run: .venv/bin/python -m ucsd_explorer.taste --pure-only"
        )
    if method in CURATOR_DEEP_PCT_METHODS and not has_curator_deep_weights():
        raise ValueError(
            "Deep curator tables missing. "
            "Run: .venv/bin/python -m ucsd_explorer.taste --deep-only"
        )

    curator_strictness = _clamp_strictness(
        _float_param(params, "curator_strictness", default=0.0)
    )
    curator_strictness_mode = str(
        params.get("curator_strictness_mode") or "deweight"
    ).strip().lower()
    if curator_strictness_mode not in ("deweight", "gate"):
        curator_strictness_mode = "deweight"
    # Deep methods only. Prefer depth/purity; fall back to legacy normie_strictness.
    legacy_normie = _clamp_strictness(
        _float_param(params, "normie_strictness", default=0.0)
    )
    has_split = ("normie_depth" in params) or ("normie_purity" in params)
    if has_split:
        normie_depth = _clamp_strictness(
            _float_param(params, "normie_depth", default=0.0)
        )
        normie_purity = _clamp_strictness(
            _float_param(params, "normie_purity", default=0.0)
        )
        legacy_for_gates: float | None = None
    else:
        normie_depth = 0.0
        normie_purity = 0.0
        legacy_for_gates = legacy_normie if legacy_normie > 0 else None

    geom_ratio = max(
        1.0,
        min(8.0, _float_param(params, "geom_ratio", default=PCT_GEOM_RATIO_DEFAULT)),
    )
    pct_power = max(
        1.0,
        min(8.0, _float_param(params, "pct_power", default=PCT_GEOM_POWER_DEFAULT)),
    )
    coverage_weight = max(
        0.0,
        min(1.0, _float_param(params, "coverage_weight", default=PCT_COVERAGE_DEFAULT)),
    )

    p0, c0 = scope_globals(sf_only)
    m = float(bayesian_m)

    needs_dynamic = bool(taste) or method in WEIGHTED_METHODS

    if needs_dynamic:
        rows, n_eligible = _rank_dynamic(
            method=method,
            min_n=min_n,
            max_n=max_n,
            bayesian_m=m,
            p0=p0,
            c0=c0,
            picky_max=picky_max,
            q=q,
            limit=limit,
            taste=taste,
            sf_only=sf_only,
            genres=genres,
            catalog=catalog,
            year_min=year_min,
            year_max=year_max,
            curator_strictness=curator_strictness,
            curator_strictness_mode=curator_strictness_mode,
            normie_depth=normie_depth,
            normie_purity=normie_purity,
            normie_strictness=legacy_for_gates,
            geom_ratio=geom_ratio,
            pct_power=pct_power,
            coverage_weight=coverage_weight,
        )
    elif method in PICKY_RATE_METHODS:
        rows = _picky_rate_rows(
            method=method,
            min_n=min_n,
            max_n=max_n,
            picky_max=picky_max,
            bayesian_m=bayesian_m,
            p0=p0,
            q=q,
            limit=limit,
            sf_only=sf_only,
            genres=genres,
            catalog=catalog,
            year_min=year_min,
            year_max=year_max,
        )
        n_eligible = None
    else:
        rows = _rank_precomputed(
            method=method,
            min_n=min_n,
            max_n=max_n,
            bayesian_m=m,
            p0=p0,
            c0=c0,
            q=q,
            limit=limit,
            sf_only=sf_only,
            genres=genres,
            catalog=catalog,
            year_min=year_min,
            year_max=year_max,
        )
        n_eligible = None

    out: dict[str, Any] = {
        "method": method,
        "min_votes": min_n,
        "max_n": max_n,
        "bayesian_m": bayesian_m,
        "limit": limit,
        "sf_only": sf_only,
        "genres": genres,
        "catalog": catalog,
        "year_min": year_min,
        "year_max": year_max,
        "n_results": len(rows),
        "globals": {
            **GLOBALS,
            "global_p5": p0,
            "global_mean": c0,
        },
        "results": _rows_to_results(rows),
        "taste_enabled": bool(taste),
    }
    if method in CURATOR_METHODS:
        out["curator_strictness"] = curator_strictness
        out["curator_strictness_mode"] = curator_strictness_mode
        out["curator_gates"] = curator_strictness_gates(
            curator_strictness,
            pct=method in CURATOR_PCT_FAMILY,
        )
        out["curator_elite_floor"] = CURATOR_ELITE_FLOOR
        if curator_strictness_mode == "deweight":
            out["curator_deweight_exp"] = curator_deweight_exponent(curator_strictness)
        if method in CURATOR_DEEP_PCT_METHODS:
            out["normie_depth"] = normie_depth
            out["normie_purity"] = normie_purity
            out["normie_gates"] = normie_gate_params(
                normie_depth, normie_purity, strictness=legacy_for_gates
            )
            out["deep_com_share_cap"] = deep_com_share_cap(
                normie_purity
                if normie_purity > 0
                else (legacy_for_gates if legacy_for_gates else 55.0)
            )
            out["curator_cohort"] = "deep"
            if method == "curator_deep_pct_geom":
                out["geom_ratio"] = geom_ratio
                out["pct_power"] = pct_power
                out["geom_weights"] = {
                    "5": geom_ratio * geom_ratio,
                    "4": geom_ratio,
                    "3": 1.0,
                }
        elif method in CURATOR_PURE_STAR_METHODS | CURATOR_PURE_PCT_METHODS:
            out["curator_cohort"] = "pure"
        elif method in CURATOR_PCT_METHODS | CURATOR_TILT_METHODS:
            out["curator_cohort"] = "pct"
        else:
            out["curator_cohort"] = "rym"
        if method in CURATOR_PCT_FAMILY:
            out["coverage_weight"] = coverage_weight
    if taste:
        out["taste"] = taste
        out["n_eligible_users"] = n_eligible
    return out


def _rank_precomputed(
    *,
    method,
    min_n,
    max_n,
    bayesian_m,
    p0,
    c0,
    q,
    limit,
    sf_only=True,
    genres=None,
    catalog=None,
    year_min=None,
    year_max=None,
):
    where = ["s.n >= ?"]
    args: list[Any] = [min_n]
    if max_n > 0:
        where.append("s.n <= ?")
        args.append(max_n)

    m = bayesian_m
    if method == "five_count":
        raw_score = "s.n5::DOUBLE"
    elif method == "five_rate_bayes":
        raw_score = f"((s.n5::DOUBLE + ({m})::DOUBLE * ({p0})::DOUBLE) / (s.n::DOUBLE + ({m})::DOUBLE))"
    elif method == "imdb_bayes":
        raw_score = (
            f"((s.n::DOUBLE / (s.n::DOUBLE + ({m})::DOUBLE)) * s.mean::DOUBLE"
            f" + (({m})::DOUBLE / (s.n::DOUBLE + ({m})::DOUBLE)) * ({c0})::DOUBLE)"
        )
    elif method == "picky_five":
        raw_score = "coalesce(p.picky_five_mass, 0)::DOUBLE"
    elif method == "polarization":
        raw_score = "s.polarization::DOUBLE"
    elif method == "stddev":
        raw_score = "s.std::DOUBLE"
    elif method == "hidden_gem":
        soft = 20000.0
        raw_score = (
            f"((s.n5::DOUBLE + ({m})::DOUBLE * ({p0})::DOUBLE) / (s.n::DOUBLE + ({m})::DOUBLE))"
            f" * ln(s.n::DOUBLE + 1) / ln(10)"
            f" / (1.0 + s.n::DOUBLE / ({soft})::DOUBLE)"
        )
    elif method == "mean":
        raw_score = f"((s.mean::DOUBLE * s.n::DOUBLE + ({m})::DOUBLE * ({c0})::DOUBLE) / (s.n::DOUBLE + ({m})::DOUBLE))"
    else:
        raise ValueError(f"unknown method {method}")

    joins, where_suffix, score, extra_args = _rank_filter_bits(
        catalog=catalog,
        year_min=year_min,
        year_max=year_max,
        q=q,
        genres=genres,
        sf_only=sf_only,
        work_alias="s",
        score_expr=raw_score,
    )

    sql = f"""
        SELECT
            s.work_id, s.book_id, s.title, s.author, s.book_url,
            s.n, s.mean, s.std, s.n5, s.n1, s.n_low, s.p5, s.p_low, s.polarization,
            {score} AS score
        FROM work_scores s
        LEFT JOIN work_picky p USING (work_id)
        {joins}
        WHERE {' AND '.join(where)}{where_suffix}
        ORDER BY score DESC, s.n DESC
        LIMIT ?
    """
    return execute(sql, args + extra_args + [limit]).fetchall()


def _rank_dynamic(
    *,
    method,
    min_n,
    max_n,
    bayesian_m,
    p0,
    c0,
    picky_max,
    q,
    limit,
    taste,
    sf_only=True,
    genres=None,
    catalog=None,
    year_min=None,
    year_max=None,
    curator_strictness=0.0,
    curator_strictness_mode="deweight",
    normie_depth=0.0,
    normie_purity=0.0,
    normie_strictness=None,
    geom_ratio=PCT_GEOM_RATIO_DEFAULT,
    pct_power=PCT_GEOM_POWER_DEFAULT,
    coverage_weight=PCT_COVERAGE_DEFAULT,
):
    """Re-aggregate from rating events with optional taste filter + lit/combo weights."""
    use_lit = method in LIT_METHODS
    use_combo = method in COMBO_METHODS
    use_cross = method in CROSS_METHODS
    use_curator_star = method in CURATOR_STAR_FAMILY
    use_curator_pct = method in CURATOR_PCT_FAMILY
    use_curator = use_curator_star or use_curator_pct
    use_weights = use_lit or use_combo or use_cross or use_curator
    use_deep = method in CURATOR_DEEP_PCT_METHODS
    use_geom = method == "curator_deep_pct_geom" or method.endswith("_pct_geom")
    coverage_weight = max(0.0, min(1.0, float(coverage_weight)))
    if use_deep:
        curator_table = "user_curator_deep_weight"
    elif method in CURATOR_PURE_PCT_METHODS:
        curator_table = "user_curator_pct_pure_weight"
    elif method in CURATOR_PCT_METHODS | CURATOR_TILT_METHODS:
        curator_table = "user_curator_pct_weight"
    elif method in CURATOR_PURE_STAR_METHODS:
        curator_table = "user_curator_pure_weight"
    else:
        curator_table = "user_curator_weight"
    score_method = _curator_score_method(method)
    max_clause = "AND agg.n <= ?" if max_n > 0 else ""
    max_args: list[Any] = [max_n] if max_n > 0 else []

    geom_ratio = max(1.0, min(8.0, float(geom_ratio)))
    pct_power = max(1.0, min(8.0, float(pct_power)))

    ctes: list[str] = []
    args: list[Any] = []
    n_eligible = None

    if taste:
        taste_cte, taste_args = taste_eligible_cte(taste)
        ctes.append(taste_cte)
        args.extend(taste_args)
        n_eligible = int(
            execute(f"WITH {taste_cte} SELECT count(*) FROM eligible", taste_args).fetchone()[0]
        )

    if use_curator:
        sf_pred = _event_sf_pred(sf_only)
        weight_expr, gate_sql, gate_args, elite_t = _curator_user_weight_sql(
            pct=use_curator_pct,
            mode=curator_strictness_mode,
            strictness=curator_strictness,
            alias="c",
            deep=use_deep,
            normie_depth=normie_depth if use_deep else 0.0,
            normie_purity=normie_purity if use_deep else 0.0,
            normie_strictness=normie_strictness if use_deep else None,
        )
        keep_expr = curator_elite_keep_expr(curator_strictness, "n_pass")
        # Rank passers by stored weight, then keep top-K (log-linear in strictness).
        ctes.append(
            f"""
            curator_pool AS (
                SELECT
                    c.*,
                    row_number() OVER (
                        ORDER BY c.{"curator_pct_weight" if use_curator_pct else "curator_weight"} DESC
                    ) AS elite_rank,
                    count(*) OVER () AS n_pass
                FROM {curator_table} c
                WHERE TRUE
                {gate_sql}
            )
            """
        )
        args.extend(gate_args)
        ctes.append(
            f"""
            curator_active AS (
                SELECT *
                FROM curator_pool
                WHERE elite_rank <= {keep_expr}
            )
            """
        )
        # Rewire weight_expr to alias `c` on curator_active (same column names).
        # Curator cohort already encodes taste; taste sliders further intersect if on.
        taste_join = "JOIN eligible el USING (user_id)" if taste else ""
        if use_curator_pct:
            # Total deweighted curator mass — unrated curators count as 0 love
            # so fan-only books (high mean among few raters) cannot beat widely
            # rated classics. Soft-deweight made this bias worse without coverage.
            ctes.append(
                f"""
                curator_cohort AS (
                    SELECT coalesce(sum(({weight_expr})), 0)::DOUBLE AS W
                    FROM curator_active c
                )
                """
            )
            rp = PCT_LOVE_POWER
            hp = PCT_HATE_POWER
            # Soft tilt methods use a gentler hate coefficient in pct_asymm.
            if method in CURATOR_TILT_METHODS or (
                method in CURATOR_DEEP_PCT_METHODS and method.endswith("_tilt")
            ):
                hl = PCT_TILT_HATE_LAMBDA
            else:
                hl = PCT_HATE_LAMBDA
            pct_case = """
                    CASE e.rating
                        WHEN 1 THEN p.pct_1
                        WHEN 2 THEN p.pct_2
                        WHEN 3 THEN p.pct_3
                        WHEN 4 THEN p.pct_4
                        WHEN 5 THEN p.pct_5
                        ELSE 0.5
                    END
            """
            if use_geom:
                # ★∈{3,4,5} ∩ top-half shelf; mass = geom(★)·pct^x
                # geometric: 5:4:3 = q² : q : 1
                qg = float(geom_ratio)
                xp = float(pct_power)
                half = float(PCT_GEOM_TOP_HALF)
                pct_love_expr = f"""
                    CASE
                        WHEN e.rating IN (3, 4, 5)
                             AND ({pct_case}) >= {half}
                        THEN (
                            CASE e.rating
                                WHEN 5 THEN ({qg} * {qg})
                                WHEN 4 THEN ({qg})
                                ELSE 1.0
                            END
                        ) * power(({pct_case}), {xp})
                        ELSE 0.0
                    END
                """
            else:
                pct_love_expr = f"""
                    power(
                        {pct_case},
                        {rp}
                    )
                """
            filtered = f"""
            filtered AS (
                SELECT
                    e.*,
                    ({weight_expr})::DOUBLE AS lit_weight,
                    ({weight_expr})::DOUBLE AS curator_weight,
                    ({pct_case})::DOUBLE AS pct,
                    ({pct_love_expr})::DOUBLE AS pct_love,
                    (
                        power(
                            {pct_case},
                            {rp}
                        )
                        - ({hl}) * power(
                            1.0 - ({pct_case}),
                            {hp}
                        )
                    )::DOUBLE AS pct_asymm
                FROM all_rating_events e
                JOIN curator_active c USING (user_id)
                JOIN user_star_percentiles p USING (user_id)
                {taste_join}
                WHERE TRUE{sf_pred}
            )
            """
        else:
            filtered = f"""
            filtered AS (
                SELECT
                    e.*,
                    ({weight_expr})::DOUBLE AS lit_weight,
                    ({weight_expr})::DOUBLE AS curator_weight,
                    0.0::DOUBLE AS pct,
                    0.0::DOUBLE AS pct_love,
                    0.0::DOUBLE AS pct_asymm
                FROM all_rating_events e
                JOIN curator_active c USING (user_id)
                {taste_join}
                WHERE TRUE{sf_pred}
            )
            """
        # gate_args already consumed when building curator_pool
    elif taste:
        # Live lit_weight from eligible (respects SF-extras / ★4 / poll prestige)
        sf_pred = _event_sf_pred(sf_only)
        filtered = f"""
            filtered AS (
                SELECT
                    e.*,
                    coalesce(el.lit_weight, 0)::DOUBLE AS lit_weight,
                    0.0::DOUBLE AS pct,
                    0.0::DOUBLE AS pct_love
                FROM all_rating_events e
                JOIN eligible el USING (user_id)
                WHERE TRUE{sf_pred}
            )
        """
    elif use_weights:
        sf_pred = _event_sf_pred(sf_only)
        filtered = f"""
            filtered AS (
                SELECT
                    e.*,
                    coalesce(w.lit_weight, 0)::DOUBLE AS lit_weight,
                    0.0::DOUBLE AS pct,
                    0.0::DOUBLE AS pct_love
                FROM all_rating_events e
                LEFT JOIN user_lit_weight w USING (user_id)
                WHERE TRUE{sf_pred}
            )
        """
    else:
        sf_pred = _event_sf_pred(sf_only)
        filtered = f"""
            filtered AS (
                SELECT
                    e.*,
                    0.0::DOUBLE AS lit_weight,
                    0.0::DOUBLE AS pct,
                    0.0::DOUBLE AS pct_love
                FROM all_rating_events e
                WHERE TRUE{sf_pred}
            )
        """
    ctes.append(filtered)

    # Aggregation
    if method in PICKY_RATE_METHODS:
        sf_pred = _event_sf_pred(sf_only)
        if taste:
            ctes[-1] = f"""
                filtered AS (
                    SELECT e.*, coalesce(el.lit_weight, 0)::DOUBLE AS lit_weight
                    FROM all_rating_events e
                    JOIN eligible el USING (user_id)
                    WHERE e.five_rate <= ?{sf_pred}
                )
            """
            args.append(picky_max)
        else:
            ctes[-1] = f"""
                filtered AS (
                    SELECT e.*, 0.0::DOUBLE AS lit_weight
                    FROM all_rating_events e
                    WHERE e.five_rate <= ?{sf_pred}
                )
            """
            args.append(picky_max)

    # User weight for combo: lit × picky^α ; rating power for combo_power
    pe = PICKY_EXP
    rp = RATING_POWER
    if use_curator_pct:
        top_t = PCT_TOP_THRESH
        mid_lo = PCT_MID_LO
        bot_t = PCT_BOTTOM_THRESH
        # Kish n_eff = (Σw)²/Σw² so soft-deweight flows into N, soft-caps, min-n
        agg = f"""
            agg AS (
                SELECT
                    work_id,
                    count(*)::BIGINT AS n_raw,
                    sum(curator_weight)::DOUBLE AS w_sum,
                    sum(curator_weight * curator_weight)::DOUBLE AS w_sq,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                    )::DOUBLE AS n,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                    )::DOUBLE AS n_eff,
                    sum(curator_weight * pct)::DOUBLE AS w_rating_sum,
                    sum(CASE WHEN pct >= {top_t} THEN curator_weight ELSE 0 END)::DOUBLE AS w_five,
                    sum(CASE WHEN pct >= 0.60 THEN curator_weight ELSE 0 END)::DOUBLE AS w_high,
                    sum(curator_weight * pct_love)::DOUBLE AS w_power,
                    sum(curator_weight * pct_asymm)::DOUBLE AS w_power_rating,
                    sum(
                        CASE WHEN pct >= {mid_lo} AND pct < {top_t}
                             THEN curator_weight ELSE 0 END
                    )::DOUBLE AS w_mid,
                    sum(
                        CASE WHEN pct <= {bot_t} THEN curator_weight ELSE 0 END
                    )::DOUBLE AS w_bottom,
                    0::BIGINT AS n_stingy,
                    0::BIGINT AS n5_stingy,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(CASE WHEN pct >= {top_t} THEN curator_weight ELSE 0 END)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n5,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(CASE WHEN rating = 1 THEN curator_weight ELSE 0 END)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n1,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(CASE WHEN pct <= {bot_t} THEN curator_weight ELSE 0 END)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n_low,
                    (
                        sum(curator_weight * pct) / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS mean,
                    stddev_pop(pct)::DOUBLE AS std,
                    (
                        sum(CASE WHEN pct >= {top_t} THEN curator_weight ELSE 0 END)
                        / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS p5,
                    (
                        sum(CASE WHEN pct <= {bot_t} THEN curator_weight ELSE 0 END)
                        / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS p_low,
                    sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5_star,
                    sum(CASE WHEN rating = 5 THEN picky_weight ELSE 0 END)::DOUBLE AS picky_five_mass
                FROM filtered
                WHERE curator_weight > 0
                GROUP BY work_id
            )
        """
    elif use_curator:
        # Kish n_eff + weighted stars so soft-deweight flows into N / p5 / soft-caps
        agg = """
            agg AS (
                SELECT
                    work_id,
                    count(*)::BIGINT AS n_raw,
                    sum(curator_weight)::DOUBLE AS w_sum,
                    sum(curator_weight * curator_weight)::DOUBLE AS w_sq,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                    )::DOUBLE AS n,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                    )::DOUBLE AS n_eff,
                    sum(curator_weight * rating)::DOUBLE AS w_rating_sum,
                    sum(CASE WHEN rating = 5 THEN curator_weight ELSE 0 END)::DOUBLE AS w_five,
                    sum(CASE WHEN rating >= 4 THEN curator_weight ELSE 0 END)::DOUBLE AS w_high,
                    0.0::DOUBLE AS w_power,
                    0.0::DOUBLE AS w_power_rating,
                    0.0::DOUBLE AS w_mid,
                    sum(CASE WHEN rating <= 2 THEN curator_weight ELSE 0 END)::DOUBLE AS w_bottom,
                    0::BIGINT AS n_stingy,
                    0::BIGINT AS n5_stingy,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(CASE WHEN rating = 5 THEN curator_weight ELSE 0 END)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n5,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(CASE WHEN rating = 1 THEN curator_weight ELSE 0 END)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n1,
                    (
                        power(sum(curator_weight), 2)
                        / nullif(sum(curator_weight * curator_weight), 0)
                        * (
                            sum(CASE WHEN rating <= 2 THEN curator_weight ELSE 0 END)
                            / nullif(sum(curator_weight), 0)
                        )
                    )::DOUBLE AS n_low,
                    (
                        sum(curator_weight * rating) / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS mean,
                    stddev_pop(rating)::DOUBLE AS std,
                    (
                        sum(CASE WHEN rating = 5 THEN curator_weight ELSE 0 END)
                        / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS p5,
                    (
                        sum(CASE WHEN rating <= 2 THEN curator_weight ELSE 0 END)
                        / nullif(sum(curator_weight), 0)
                    )::DOUBLE AS p_low,
                    sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5_star,
                    sum(CASE WHEN rating = 5 THEN picky_weight ELSE 0 END)::DOUBLE AS picky_five_mass
                FROM filtered
                WHERE curator_weight > 0
                GROUP BY work_id
            )
        """
    elif use_cross:
        # Dual signal: lit×picky weighted 5★ rate ∩ stingy-only unweighted 5★ rate
        agg = f"""
            agg AS (
                SELECT
                    work_id,
                    count(*)::BIGINT AS n,
                    sum(
                        CASE WHEN lit_weight > 0
                             THEN lit_weight * power(picky_weight, {pe})
                             ELSE 0 END
                    )::DOUBLE AS w_sum,
                    sum(
                        CASE WHEN lit_weight > 0
                             THEN lit_weight * power(picky_weight, {pe}) * rating
                             ELSE 0 END
                    )::DOUBLE AS w_rating_sum,
                    sum(
                        CASE WHEN lit_weight > 0 AND rating = 5
                             THEN lit_weight * power(picky_weight, {pe})
                             ELSE 0 END
                    )::DOUBLE AS w_five,
                    sum(
                        CASE WHEN lit_weight > 0 AND rating >= 4
                             THEN lit_weight * power(picky_weight, {pe})
                             ELSE 0 END
                    )::DOUBLE AS w_high,
                    0.0::DOUBLE AS w_power,
                    0.0::DOUBLE AS w_power_rating,
                    sum(CASE WHEN five_rate <= {float(picky_max)} THEN 1 ELSE 0 END)::BIGINT AS n_stingy,
                    sum(CASE WHEN five_rate <= {float(picky_max)} AND rating = 5
                             THEN 1 ELSE 0 END)::BIGINT AS n5_stingy,
                    sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5,
                    sum(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::BIGINT AS n1,
                    sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::BIGINT AS n_low,
                    avg(rating)::DOUBLE AS mean,
                    stddev_pop(rating)::DOUBLE AS std,
                    (sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p5,
                    (sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p_low,
                    sum(CASE WHEN rating = 5 THEN picky_weight ELSE 0 END)::DOUBLE AS picky_five_mass
                FROM filtered
                GROUP BY work_id
            )
        """
    elif use_combo:
        # uw = lit_weight * picky^α ; pw = uw * (rating/5)^ρ
        agg = f"""
            agg AS (
                SELECT
                    work_id,
                    count(*)::BIGINT AS n,
                    sum(lit_weight * power(picky_weight, {pe}))::DOUBLE AS w_sum,
                    sum(
                        lit_weight * power(picky_weight, {pe}) * rating
                    )::DOUBLE AS w_rating_sum,
                    sum(
                        CASE WHEN rating = 5
                             THEN lit_weight * power(picky_weight, {pe})
                             ELSE 0 END
                    )::DOUBLE AS w_five,
                    sum(
                        CASE WHEN rating >= 4
                             THEN lit_weight * power(picky_weight, {pe})
                             ELSE 0 END
                    )::DOUBLE AS w_high,
                    sum(
                        lit_weight * power(picky_weight, {pe})
                        * power(rating / 5.0, {rp})
                    )::DOUBLE AS w_power,
                    sum(
                        lit_weight * power(picky_weight, {pe})
                        * power(rating / 5.0, {rp}) * rating
                    )::DOUBLE AS w_power_rating,
                    0::BIGINT AS n_stingy,
                    0::BIGINT AS n5_stingy,
                    sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5,
                    sum(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::BIGINT AS n1,
                    sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::BIGINT AS n_low,
                    avg(rating)::DOUBLE AS mean,
                    stddev_pop(rating)::DOUBLE AS std,
                    (sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p5,
                    (sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p_low,
                    sum(CASE WHEN rating = 5 THEN picky_weight ELSE 0 END)::DOUBLE AS picky_five_mass
                FROM filtered
                WHERE lit_weight > 0
                GROUP BY work_id
            )
        """
    elif use_lit:
        agg = """
            agg AS (
                SELECT
                    work_id,
                    count(*)::BIGINT AS n,
                    sum(lit_weight)::DOUBLE AS w_sum,
                    sum(lit_weight * rating)::DOUBLE AS w_rating_sum,
                    sum(CASE WHEN rating = 5 THEN lit_weight ELSE 0 END)::DOUBLE AS w_five,
                    sum(CASE WHEN rating >= 4 THEN lit_weight ELSE 0 END)::DOUBLE AS w_high,
                    0.0::DOUBLE AS w_power,
                    0.0::DOUBLE AS w_power_rating,
                    0::BIGINT AS n_stingy,
                    0::BIGINT AS n5_stingy,
                    sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5,
                    sum(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::BIGINT AS n1,
                    sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::BIGINT AS n_low,
                    avg(rating)::DOUBLE AS mean,
                    stddev_pop(rating)::DOUBLE AS std,
                    (sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p5,
                    (sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p_low,
                    sum(CASE WHEN rating = 5 THEN picky_weight ELSE 0 END)::DOUBLE AS picky_five_mass
                FROM filtered
                WHERE lit_weight > 0
                GROUP BY work_id
            )
        """
    else:
        agg = """
            agg AS (
                SELECT
                    work_id,
                    count(*)::BIGINT AS n,
                    count(*)::DOUBLE AS w_sum,
                    sum(rating)::DOUBLE AS w_rating_sum,
                    sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::DOUBLE AS w_five,
                    sum(CASE WHEN rating >= 4 THEN 1 ELSE 0 END)::DOUBLE AS w_high,
                    0.0::DOUBLE AS w_power,
                    0.0::DOUBLE AS w_power_rating,
                    0::BIGINT AS n_stingy,
                    0::BIGINT AS n5_stingy,
                    sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5,
                    sum(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::BIGINT AS n1,
                    sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::BIGINT AS n_low,
                    avg(rating)::DOUBLE AS mean,
                    stddev_pop(rating)::DOUBLE AS std,
                    (sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p5,
                    (sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END)::DOUBLE / count(*)) AS p_low,
                    sum(CASE WHEN rating = 5 THEN picky_weight ELSE 0 END)::DOUBLE AS picky_five_mass
                FROM filtered
                GROUP BY work_id
            )
        """
    ctes.append(agg)

    m = bayesian_m
    soft = 20000.0
    soft_c = COMBO_SOFT
    z = WILSON_Z
    if method == "five_count":
        score = "agg.n5::DOUBLE"
    elif method == "five_rate_bayes":
        score = f"((agg.n5::DOUBLE + ({m})::DOUBLE * ({p0})::DOUBLE) / (agg.n::DOUBLE + ({m})::DOUBLE))"
    elif method == "imdb_bayes":
        score = (
            f"((agg.n::DOUBLE / (agg.n::DOUBLE + ({m})::DOUBLE)) * agg.mean::DOUBLE"
            f" + (({m})::DOUBLE / (agg.n::DOUBLE + ({m})::DOUBLE)) * ({c0})::DOUBLE)"
        )
    elif method == "lit_weighted_mean":
        score = (
            f"((agg.w_sum / (agg.w_sum + ({m})::DOUBLE))"
            f" * (agg.w_rating_sum / nullif(agg.w_sum, 0))"
            f" + (({m})::DOUBLE / (agg.w_sum + ({m})::DOUBLE)) * ({c0})::DOUBLE)"
        )
    elif method == "lit_weighted_five":
        score = "coalesce(agg.w_five, 0)::DOUBLE"
    elif method == "lit_weighted_five_rate":
        score = (
            f"((agg.w_five + ({m})::DOUBLE * ({p0})::DOUBLE)"
            f" / (agg.w_sum + ({m})::DOUBLE))"
        )
    elif method == "lit_gem":
        score = (
            f"((agg.w_five + ({m})::DOUBLE * ({p0})::DOUBLE) / (agg.w_sum + ({m})::DOUBLE))"
            f" * ln(agg.w_sum + 1) / ln(10)"
            f" / (1.0 + agg.n::DOUBLE / ({soft})::DOUBLE)"
        )
    elif method == "combo_five_rate":
        score = (
            f"((agg.w_five + ({m})::DOUBLE * ({p0})::DOUBLE)"
            f" / (agg.w_sum + ({m})::DOUBLE))"
        )
    elif score_method == "curator_five_rate":
        score = (
            f"((agg.w_five + ({m})::DOUBLE * ({p0})::DOUBLE)"
            f" / (agg.w_sum + ({m})::DOUBLE))"
        )
    elif score_method == "curator_mean":
        score = (
            f"((agg.w_sum / (agg.w_sum + ({m})::DOUBLE))"
            f" * (agg.w_rating_sum / nullif(agg.w_sum, 0))"
            f" + (({m})::DOUBLE / (agg.w_sum + ({m})::DOUBLE)) * ({c0})::DOUBLE)"
        )
    elif score_method == "curator_liked":
        score = (
            f"((agg.w_high + ({m})::DOUBLE * ({p0})::DOUBLE)"
            f" / (agg.w_sum + ({m})::DOUBLE))"
        )
    elif score_method == "curator_gem":
        sm = CURATOR_SMALL_M
        soft_u = CURATOR_SOFT
        # Soft-cap on Kish n_eff (alias agg.n), not raw headcount
        score = (
            f"((agg.w_five + ({m})::DOUBLE * ({p0})::DOUBLE) / (agg.w_sum + ({m})::DOUBLE))"
            f" * ln(agg.w_sum + 1) / ln(10)"
            f" / (1.0 + agg.n::DOUBLE / ({soft_u})::DOUBLE)"
            f" * (agg.w_sum / (agg.w_sum + ({sm})::DOUBLE))"
        )
    elif score_method == "curator_pct_mean":
        # Linear blend of among-raters mean vs full-cohort (unread@prior).
        prior = PCT_PRIOR
        u = max(0.0, min(1.0, float(coverage_weight)))
        among = (
            f"((agg.w_rating_sum + ({m})::DOUBLE * ({prior})::DOUBLE)"
            f" / (coalesce(agg.w_sum, 0) + ({m})::DOUBLE))"
        )
        full = (
            f"((agg.w_rating_sum"
            f" + greatest((SELECT W FROM curator_cohort) - agg.w_sum, 0)"
            f" * ({prior})::DOUBLE"
            f" + ({m})::DOUBLE * ({prior})::DOUBLE)"
            f" / ((SELECT W FROM curator_cohort) + ({m})::DOUBLE))"
        )
        score = f"((1.0 - ({u})::DOUBLE) * {among} + ({u})::DOUBLE * {full})"
    elif score_method == "curator_pct_love":
        # Love mass: linear blend among-raters ↔ full cohort (unread→0).
        prior = PCT_PRIOR
        rp = PCT_LOVE_POWER
        mass = f"(agg.w_power + ({m})::DOUBLE * power(({prior})::DOUBLE, {rp}))"
        score = _pct_coverage_score(mass, m, coverage_weight)
    elif score_method == "curator_pct_geom":
        # Top-half ★≥3 geom·pct^x mass; linear coverage blend.
        # Prior: 3★ weight (=1) at the half-shelf boundary.
        half = PCT_GEOM_TOP_HALF
        xp = float(pct_power)
        prior_mass = f"power(({half})::DOUBLE, {xp})"
        mass = f"(agg.w_power + ({m})::DOUBLE * ({prior_mass}))"
        score = _pct_coverage_score(mass, m, coverage_weight)
    elif score_method == "curator_pct_asymm":
        prior = PCT_PRIOR
        rp = PCT_LOVE_POWER
        hp = PCT_HATE_POWER
        hl = PCT_HATE_LAMBDA
        prior_asymm = f"(power(({prior})::DOUBLE, {rp}) - ({hl}) * power(1.0 - ({prior})::DOUBLE, {hp}))"
        mass = f"(agg.w_power_rating + ({m})::DOUBLE * {prior_asymm})"
        score = _pct_coverage_score(mass, m, coverage_weight)
    elif score_method == "curator_pct_gap":
        coef = PCT_GAP_MID_COEF
        prior = PCT_TOP_PRIOR
        mass = (
            f"(agg.w_five - ({coef})::DOUBLE * agg.w_mid"
            f" + ({m})::DOUBLE * ({prior})::DOUBLE)"
        )
        score = _pct_coverage_score(mass, m, coverage_weight)
    elif score_method == "curator_pct_top":
        prior = PCT_TOP_PRIOR
        mass = f"(agg.w_five + ({m})::DOUBLE * ({prior})::DOUBLE)"
        score = _pct_coverage_score(mass, m, coverage_weight)
    elif score_method == "curator_pct_gem":
        sm = CURATOR_SMALL_M
        soft_u = CURATOR_SOFT
        prior = PCT_TOP_PRIOR
        mass = f"(agg.w_five + ({m})::DOUBLE * ({prior})::DOUBLE)"
        base = _pct_coverage_score(mass, m, coverage_weight)
        # Coverage top-rate × log(rater mass); soft-cap on Kish n_eff
        score = (
            f"({base})"
            f" * ln(agg.w_sum + 1) / ln(10)"
            f" / (1.0 + agg.n::DOUBLE / ({soft_u})::DOUBLE)"
            f" * (agg.w_sum / (agg.w_sum + ({sm})::DOUBLE))"
        )
    elif method == "combo_mean":
        score = (
            f"((agg.w_sum / (agg.w_sum + ({m})::DOUBLE))"
            f" * (agg.w_rating_sum / nullif(agg.w_sum, 0))"
            f" + (({m})::DOUBLE / (agg.w_sum + ({m})::DOUBLE)) * ({c0})::DOUBLE)"
        )
    elif method == "combo_liked":
        score = (
            f"((agg.w_high + ({m})::DOUBLE * ({p0})::DOUBLE)"
            f" / (agg.w_sum + ({m})::DOUBLE))"
        )
    elif method == "cross_five":
        # Geometric mean of lit×picky Bayesian 5★ rate and stingy-only Bayesian 5★ rate
        score = f"""(
            sqrt(
                greatest(
                    ((agg.w_five + ({m})::DOUBLE * ({p0})::DOUBLE)
                     / (agg.w_sum + ({m})::DOUBLE)),
                    0
                )
                * greatest(
                    ((agg.n5_stingy::DOUBLE + ({m})::DOUBLE * ({p0})::DOUBLE)
                     / (agg.n_stingy::DOUBLE + ({m})::DOUBLE)),
                    0
                )
            )
        )"""
    elif method == "combo_gem":
        sm = COMBO_SMALL_M
        score = (
            f"((agg.w_five + ({m})::DOUBLE * ({p0})::DOUBLE) / (agg.w_sum + ({m})::DOUBLE))"
            f" * ln(agg.w_sum + 1) / ln(10)"
            f" / (1.0 + agg.n::DOUBLE / ({soft_c})::DOUBLE)"
            f" * (agg.w_sum / (agg.w_sum + ({sm})::DOUBLE))"
        )
    elif method == "combo_five_mass":
        score = "coalesce(agg.w_five, 0)::DOUBLE"
    elif method == "combo_love":
        # Literary-picky 5★ density — good for cult / divisive books
        score = (
            f"coalesce(agg.w_five, 0) / power(1.0 + agg.n::DOUBLE / 400.0, 0.55)"
        )
    elif method == "combo_power":
        # Bayesian shrink of power-weighted mean toward global mean
        score = (
            f"((agg.w_power / (agg.w_power + ({m})::DOUBLE))"
            f" * (agg.w_power_rating / nullif(agg.w_power, 0))"
            f" + (({m})::DOUBLE / (agg.w_power + ({m})::DOUBLE)) * ({c0})::DOUBLE)"
        )
    elif method == "combo_wilson":
        # Wilson lower bound on weighted five-rate; n_eff = w_sum
        sm = COMBO_SMALL_M
        score = f"""(
            CASE WHEN agg.w_sum <= 0 THEN 0 ELSE
            (
                (
                    ((agg.w_five / agg.w_sum) + ({z})*({z})/(2*agg.w_sum)
                     - ({z}) * sqrt(
                        greatest(
                            (agg.w_five / agg.w_sum) * (1 - agg.w_five / agg.w_sum) / agg.w_sum
                            + ({z})*({z})/(4*agg.w_sum*agg.w_sum),
                            0
                        )
                     )
                    ) / (1 + ({z})*({z})/agg.w_sum)
                ) * (agg.w_sum / (agg.w_sum + ({sm})::DOUBLE))
            ) END
        )"""
    elif method == "picky_five":
        score = "coalesce(agg.picky_five_mass, 0)::DOUBLE"
    elif method == "picky_five_rate":
        score = f"((agg.n5::DOUBLE + ({m})::DOUBLE * ({p0})::DOUBLE) / (agg.n::DOUBLE + ({m})::DOUBLE))"
    elif method == "picky_gem":
        soft_p = PICKY_GEM_SOFT
        score = (
            f"((agg.n5::DOUBLE + ({m})::DOUBLE * ({p0})::DOUBLE) / (agg.n::DOUBLE + ({m})::DOUBLE))"
            f" * ln(agg.n::DOUBLE + 1) / ln(10)"
            f" / (1.0 + agg.n::DOUBLE / ({soft_p})::DOUBLE)"
        )
    elif method == "polarization":
        score = "(4.0 * agg.p5 * agg.p_low)"
    elif method == "stddev":
        score = "agg.std::DOUBLE"
    elif method == "hidden_gem":
        score = (
            f"((agg.n5::DOUBLE + ({m})::DOUBLE * ({p0})::DOUBLE) / (agg.n::DOUBLE + ({m})::DOUBLE))"
            f" * ln(agg.n::DOUBLE + 1) / ln(10)"
            f" / (1.0 + agg.n::DOUBLE / ({soft})::DOUBLE)"
        )
    elif method == "mean":
        score = f"((agg.mean::DOUBLE * agg.n::DOUBLE + ({m})::DOUBLE * ({c0})::DOUBLE) / (agg.n::DOUBLE + ({m})::DOUBLE))"
    else:
        raise ValueError(f"unknown method {method}")

    # Weighted methods need some weight mass as well as support n.
    # Curator paths set agg.n = Kish n_eff so min/max votes & soft-caps
    # already respect soft-deweight (raw headcount alone cannot inflate N).
    min_clause = "agg.n >= ?"
    if use_weights:
        min_clause += " AND agg.w_sum >= 1"
    if use_cross:
        min_clause += " AND agg.n_stingy >= 20"

    joins, where_suffix, scored, extra_args = _rank_filter_bits(
        catalog=catalog,
        year_min=year_min,
        year_max=year_max,
        q=q,
        genres=genres,
        sf_only=False,  # SF already applied when building agg / events
        work_alias="w",
        score_expr=score,
    )

    with_sql = ",\n".join(ctes)
    # Curator scores use Kish n_eff for min_votes; show raw rater / literal 5★ counts.
    if use_curator:
        n_disp = "agg.n_raw"
        n5_disp = "agg.n5_star"
    else:
        n_disp = "cast(round(agg.n) AS BIGINT)"
        n5_disp = "cast(round(agg.n5) AS BIGINT)"
    sql = f"""
        WITH {with_sql}
        SELECT
            w.work_id, w.book_id, w.title, w.author, w.book_url,
            {n_disp} AS n,
            agg.mean, agg.std,
            {n5_disp} AS n5,
            cast(round(agg.n1) AS BIGINT) AS n1,
            cast(round(agg.n_low) AS BIGINT) AS n_low,
            agg.p5, agg.p_low,
            (4.0 * agg.p5 * agg.p_low) AS polarization,
            {scored} AS score
        FROM agg
        JOIN works w USING (work_id)
        {joins}
        WHERE {min_clause} {max_clause}{where_suffix}
        ORDER BY score DESC, agg.n DESC
        LIMIT ?
    """
    args = args + [min_n] + max_args + extra_args + [limit]
    rows = execute(sql, args).fetchall()
    return rows, n_eligible


def _picky_rate_rows(
    *,
    method,
    min_n,
    max_n,
    picky_max,
    bayesian_m,
    p0,
    q,
    limit,
    sf_only=True,
    genres=None,
    catalog=None,
    year_min=None,
    year_max=None,
):
    where = ["s.n >= ?"]
    args: list[Any] = [min_n]
    if max_n > 0:
        where.append("s.n <= ?")
        args.append(max_n)
    sf_ev = _event_sf_pred(sf_only, alias="")
    m = float(bayesian_m)
    soft_p = PICKY_GEM_SOFT
    if method == "picky_gem":
        rate = (
            f"(coalesce(n.n5_stingy, 0)::DOUBLE + {m}::DOUBLE * {p0}::DOUBLE)"
            f" / (coalesce(d.n_stingy, 0)::DOUBLE + {m}::DOUBLE)"
        )
        raw = (
            f"({rate})"
            f" * (ln(coalesce(d.n_stingy, 0)::DOUBLE + 1.0) / ln(10.0))"
            f" / (1.0 + coalesce(d.n_stingy, 0)::DOUBLE / {soft_p}::DOUBLE)"
        )
        score_params: list[Any] = []
        where.append("coalesce(d.n_stingy, 0) >= 20")
    else:
        raw = (
            "(coalesce(n.n5_stingy, 0)::DOUBLE + ?::DOUBLE * ?::DOUBLE)"
            " / (coalesce(d.n_stingy, 0)::DOUBLE + ?::DOUBLE)"
        )
        score_params = [bayesian_m, p0, bayesian_m]

    joins, where_suffix, scored, extra_args = _rank_filter_bits(
        catalog=catalog,
        year_min=year_min,
        year_max=year_max,
        q=q,
        genres=genres,
        sf_only=sf_only,
        work_alias="s",
        score_expr=raw,
    )

    return execute(
        f"""
        WITH denom AS (
            SELECT work_id, count(*)::BIGINT AS n_stingy
            FROM all_rating_events
            WHERE five_rate <= ?{sf_ev}
            GROUP BY work_id
        ),
        numer AS (
            SELECT work_id, count(*)::BIGINT AS n5_stingy
            FROM five_star_events
            WHERE five_rate <= ?{sf_ev}
            GROUP BY work_id
        )
        SELECT
            s.work_id, s.book_id, s.title, s.author, s.book_url,
            s.n, s.mean, s.std, s.n5, s.n1, s.n_low, s.p5, s.p_low, s.polarization,
            {scored} AS score
        FROM work_scores s
        LEFT JOIN denom d USING (work_id)
        LEFT JOIN numer n USING (work_id)
        {joins}
        WHERE {' AND '.join(where)}{where_suffix}
        ORDER BY score DESC, s.n DESC
        LIMIT ?
        """,
        [picky_max, picky_max]
        + score_params
        + args
        + extra_args
        + [limit],
    ).fetchall()


def work_relevant_hist(work_id: str, params: dict[str, Any]) -> dict[str, Any] | None:
    """Star (+ optional percentile) hist among users who feed the current ranking.

    Matches taste intersection and/or curator elite cohort used by rank_books.
    When curator weights apply, star buckets and means are weight-sums (not
    unweighted headcounts) so soft-deweight / unequal elite weights show up.
    """
    method = str(params.get("method") or "")
    taste = parse_taste_params(params)
    use_curator = method in CURATOR_METHODS
    if not use_curator and not taste:
        return None

    use_curator_pct = method in CURATOR_PCT_FAMILY
    use_deep = method in CURATOR_DEEP_PCT_METHODS
    sf_only = parse_sf_only(params)

    curator_strictness = _clamp_strictness(
        _float_param(params, "curator_strictness", default=0.0)
    )
    curator_strictness_mode = str(
        params.get("curator_strictness_mode") or "deweight"
    ).strip().lower()
    if curator_strictness_mode not in ("deweight", "gate"):
        curator_strictness_mode = "deweight"

    legacy_normie = _clamp_strictness(
        _float_param(params, "normie_strictness", default=0.0)
    )
    has_split = ("normie_depth" in params) or ("normie_purity" in params)
    if has_split:
        normie_depth = _clamp_strictness(
            _float_param(params, "normie_depth", default=0.0)
        )
        normie_purity = _clamp_strictness(
            _float_param(params, "normie_purity", default=0.0)
        )
        legacy_for_gates: float | None = None
    else:
        normie_depth = 0.0
        normie_purity = 0.0
        legacy_for_gates = legacy_normie if legacy_normie > 0 else None

    if use_deep:
        curator_table = "user_curator_deep_weight"
    elif method in CURATOR_PURE_PCT_METHODS:
        curator_table = "user_curator_pct_pure_weight"
    elif method in CURATOR_PCT_METHODS | CURATOR_TILT_METHODS:
        curator_table = "user_curator_pct_weight"
    elif method in CURATOR_PURE_STAR_METHODS:
        curator_table = "user_curator_pure_weight"
    else:
        curator_table = "user_curator_weight"

    ctes: list[str] = []
    args: list[Any] = []
    label_bits: list[str] = []

    if taste:
        if not has_taste_tables():
            return {"error": "taste tables missing", "n": 0, "stars": {}, "weighted": False}
        taste_cte, taste_args = taste_eligible_cte(taste)
        ctes.append(taste_cte)
        args.extend(taste_args)
        label_bits.append("taste-eligible")

    weight_expr = "1.0"
    user_from = ""
    if use_curator:
        if use_deep and not has_curator_deep_weights():
            return {"error": "deep curator tables missing", "n": 0, "stars": {}, "weighted": False}
        if method in CURATOR_PCT_METHODS | CURATOR_TILT_METHODS and not has_curator_pct_weights():
            return {"error": "curator pct tables missing", "n": 0, "stars": {}, "weighted": False}
        weight_expr, gate_sql, gate_args, _elite_t = _curator_user_weight_sql(
            pct=use_curator_pct or use_deep or method in CURATOR_PURE_PCT_METHODS,
            mode=curator_strictness_mode,
            strictness=curator_strictness,
            alias="c",
            deep=use_deep,
            normie_depth=normie_depth if use_deep else 0.0,
            normie_purity=normie_purity if use_deep else 0.0,
            normie_strictness=legacy_for_gates if use_deep else None,
        )
        wcol = "curator_pct_weight" if (
            use_curator_pct or use_deep or method in CURATOR_PURE_PCT_METHODS
        ) else "curator_weight"
        keep_expr = curator_elite_keep_expr(curator_strictness, "n_pass")
        taste_join = "JOIN eligible el USING (user_id)" if taste else ""
        ctes.append(
            f"""
            curator_pool AS (
                SELECT
                    c.*,
                    row_number() OVER (ORDER BY c.{wcol} DESC) AS elite_rank,
                    count(*) OVER () AS n_pass
                FROM {curator_table} c
                {taste_join}
                WHERE TRUE
                {gate_sql}
            )
            """
        )
        args.extend(gate_args)
        ctes.append(
            f"""
            curator_active AS (
                SELECT * FROM curator_pool
                WHERE elite_rank <= {keep_expr}
            )
            """
        )
        user_from = "curator_active c"
        label_bits.append("ranking curators")
        if use_deep:
            label_bits.append(
                f"depth {int(normie_depth) if has_split else int(legacy_normie)}"
                f"/purity {int(normie_purity) if has_split else int(legacy_normie)}"
            )
        label_bits.append(f"curator {int(curator_strictness)}")
    elif taste:
        user_from = "eligible c"
        weight_expr = "coalesce(c.lit_weight, 1.0)"

    sf_pred = _event_sf_pred(sf_only)
    # Personal percentile of this star on the user's shelf (when available).
    pct_join = ""
    pct_expr = "NULL::DOUBLE"
    if has_curator_pct_weights() or has_curator_deep_weights():
        pct_join = "LEFT JOIN user_star_percentiles p USING (user_id)"
        pct_expr = """
            CASE e.rating
                WHEN 1 THEN p.pct_1
                WHEN 2 THEN p.pct_2
                WHEN 3 THEN p.pct_3
                WHEN 4 THEN p.pct_4
                WHEN 5 THEN p.pct_5
                ELSE NULL
            END
        """

    with_sql = ",\n".join(ctes)
    row = execute(
        f"""
        WITH {with_sql},
        ev AS (
            SELECT
                e.rating,
                ({weight_expr})::DOUBLE AS w,
                ({pct_expr})::DOUBLE AS pct
            FROM all_rating_events e
            JOIN {user_from} USING (user_id)
            {pct_join}
            WHERE e.work_id = ?{sf_pred}
              AND e.rating BETWEEN 1 AND 5
              AND ({weight_expr}) > 0
        )
        SELECT
            count(*)::BIGINT AS n_raw,
            coalesce(sum(w), 0)::DOUBLE AS w_sum,
            coalesce(sum(CASE WHEN rating = 5 THEN w ELSE 0 END), 0)::DOUBLE AS w5,
            coalesce(sum(CASE WHEN rating = 4 THEN w ELSE 0 END), 0)::DOUBLE AS w4,
            coalesce(sum(CASE WHEN rating = 3 THEN w ELSE 0 END), 0)::DOUBLE AS w3,
            coalesce(sum(CASE WHEN rating = 2 THEN w ELSE 0 END), 0)::DOUBLE AS w2,
            coalesce(sum(CASE WHEN rating = 1 THEN w ELSE 0 END), 0)::DOUBLE AS w1,
            sum(w * rating) / nullif(sum(w), 0) AS w_mean,
            sum(w * pct) / nullif(sum(CASE WHEN pct IS NOT NULL THEN w ELSE 0 END), 0) AS w_pct_mean,
            approx_quantile(pct, 0.5) AS pct_med,
            count(*) FILTER (WHERE pct IS NOT NULL)::BIGINT AS n_pct
        FROM ev
        """,
        args + [work_id],
    ).fetchone()

    if not row:
        return {
            "n": 0,
            "n_raw": 0,
            "weighted": use_curator or bool(taste),
            "stars": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
            "label": " · ".join(label_bits) or "relevant raters",
        }

    n_raw = int(row[0] or 0)
    w_sum = float(row[1] or 0.0)
    stars_w = {
        "5": float(row[2] or 0.0),
        "4": float(row[3] or 0.0),
        "3": float(row[4] or 0.0),
        "2": float(row[5] or 0.0),
        "1": float(row[6] or 0.0),
    }
    # Display counts: round weighted mass for the bar chart; keep raw n separately.
    stars_disp = {k: int(round(v)) for k, v in stars_w.items()}
    p5 = (stars_w["5"] / w_sum) if w_sum else None
    return {
        "n": int(round(w_sum)) if w_sum else 0,
        "n_raw": n_raw,
        "w_sum": w_sum,
        "weighted": True,
        "mean": float(row[7]) if row[7] is not None else None,
        "p5": p5,
        "stars": stars_disp,
        "stars_weighted": stars_w,
        "pct_mean": float(row[8]) if row[8] is not None else None,
        "pct_median": float(row[9]) if row[9] is not None else None,
        "n_pct": int(row[10] or 0),
        "label": " · ".join(label_bits) or "relevant raters",
        "method": method,
    }

"""Curator cohort: continuous purity gates + deweight; mint only as a safe fast path.

Contract
--------
* deweight=0, purity=0 → every percentile user, weight 1.0 (true off).
* purity 0→100 → continuous deep_share floor (0→0.80) and, when >0, com_share
  cap (1.0→0.08). No forced mint-time floors.
* deweight 0→100 → weight = coalesce(curator_score, 1e-4)^expo (expo 0→4).
  Does not remove users from the cohort; tiny weights vanish from scores.

The ~20k ``user_curator_deep_weight`` table is a *cached* elite universe
(mint floors baked in). We only scan it when query-time purity is already at
least as strict as those floors (safe subset). Otherwise we score the wide
percentile pool with LEFT JOINed taste features.
"""

from __future__ import annotations

from typing import Any

from curators_explorer.taste_packs import pack_author_ids, pack_uses_mint

DEWEIGHT_EXPO_MAX = 4.0
DEWEIGHT_ALPHA_MAX = 8.0
PURITY_SHARE_MAX = 0.80
COM_SHARE_FLOOR = 0.08

# Mint-time floors — used ONLY to decide the safe mint fast path, never as
# forced query gates when purity is softer.
MINT_MIN_DEEP_SHARE = 0.35
MINT_MAX_COM_SHARE = 0.20
MINT_DEEP_EXP = 1.8
MINT_COM_EXP = 3.0

# Non-mint missing taste weight. Must stay tiny in *aggregate* across ~600k
# users: at dew=15 (expo=0.6), 1e-4^0.6≈4e-3 → ~2k total mass if used as
# pct fallback was removed; 1e-8^0.6≈1.6e-5 → ~10 total mass (negligible vs
# deep mint Σw≈5k). Do NOT coalesce to pct-curator weights — that pool is
# ~10× the deep mass and made purity 0→1 look like a deweight bug.
MISSING_WEIGHT = 1e-8


def clamp01_100(x: float) -> float:
    return max(0.0, min(100.0, float(x)))


def t01(x: float) -> float:
    return clamp01_100(x) / 100.0


def deweight_exponent(deweight: float) -> float:
    return DEWEIGHT_EXPO_MAX * t01(deweight)


def deweight_alpha(deweight: float) -> float:
    return DEWEIGHT_ALPHA_MAX * t01(deweight)


def purity_min_share(purity: float) -> float:
    t = t01(purity)
    if t <= 1e-12:
        return 0.0
    return t * PURITY_SHARE_MAX


def com_share_cap(purity: float) -> float | None:
    """Query-time max com_share when purity > 0; None when off."""
    t = t01(purity)
    if t <= 1e-12:
        return None
    return 1.0 - t * (1.0 - COM_SHARE_FLOOR)


def mint_fast_path_ok(*, purity: float, use_mint_pack: bool) -> bool:
    """True when scanning the mint table cannot exclude anyone purity would keep.

    Mint baked deep_share≥0.35 and com_share≤0.20. If query purity already
    requires share ≥ that floor *and* a com cap ≤ 0.20, mint is a safe subset.
    Deweight-only (purity=0) is never a mint fast path — deweight must not
    shrink membership.
    """
    if not use_mint_pack:
        return False
    min_share = purity_min_share(purity)
    cap = com_share_cap(purity)
    if min_share + 1e-12 < MINT_MIN_DEEP_SHARE:
        return False
    if cap is None or cap + 1e-12 > MINT_MAX_COM_SHARE:
        return False
    return True


def weight_expr_sql(
    deweight: float,
    *,
    alias: str = "c",
    weight_col: str = "curator_pct_weight",
) -> str:
    """SQL weight from stored curator scores. expo=0 → flat 1.0."""
    expo = deweight_exponent(deweight)
    a = alias
    if expo <= 1e-12:
        return "1.0"
    base = f"(power(greatest(({a}.{weight_col}), 1e-9), {float(expo)}))"
    alpha = deweight_alpha(deweight)
    if alpha <= 1e-12:
        return base
    return (
        f"({base} * exp(-({alpha}) * (1.0 - coalesce({a}.weight_pctile, 0))))"
    )


def purity_gate_sql(purity: float, *, alias: str = "c") -> tuple[str, list[Any]]:
    """Continuous purity gates only — nothing at purity=0."""
    a = alias
    clauses: list[str] = []
    args: list[Any] = []
    min_share = purity_min_share(purity)
    if min_share > 1e-12:
        clauses.append(f"AND coalesce({a}.deep_share, 0) >= ?")
        args.append(float(min_share))
    cap = com_share_cap(purity)
    if cap is not None:
        clauses.append(f"AND coalesce({a}.com_share, 0) <= ?")
        args.append(float(cap))
    if not clauses:
        return "", []
    return "\n        " + "\n        ".join(clauses) + "\n    ", args


def _id_list(ids: list[str]) -> str:
    safe = []
    for i in ids:
        s = str(i)
        if not s or any(c not in "0123456789" for c in s):
            continue
        safe.append(f"'{s}'")
    return ", ".join(safe) if safe else "'__none__'"


def _neutral_works_cte(neutral_titles: list[str]) -> str:
    neutrals = [t for t in (neutral_titles or []) if t]
    if not neutrals:
        return """
            pack_neutral_works AS (
                SELECT work_id FROM works WHERE FALSE
            )
        """
    title_vals = ", ".join(
        "('" + t.replace("'", "''") + "')" for t in neutrals[:200]
    )
    return f"""
            pack_neutral_works AS (
                SELECT DISTINCT w.work_id
                FROM works w
                JOIN (VALUES {title_vals}) AS t(title)
                  ON lower(w.title) = lower(t.title)
                     OR lower(w.title) LIKE lower(t.title) || ' (%'
            )
    """


def all_equal_cte() -> str:
    return """
            curator_active AS (
                SELECT
                    user_id,
                    1.0::DOUBLE AS curator_pct_weight,
                    0.0::DOUBLE AS weight_pctile,
                    0.0::DOUBLE AS deep_share,
                    0.0::DOUBLE AS com_share,
                    1.0::DOUBLE AS w
                FROM user_star_percentiles
            )
    """


def mint_fast_ctes(deweight: float, purity: float) -> tuple[list[str], list[Any]]:
    """Safe subset scan of the mint table (purity already ≥ mint floors)."""
    gate_sql, gate_args = purity_gate_sql(purity, alias="c")
    w_expr = weight_expr_sql(deweight, alias="c")
    ctes = [
        f"""
            curator_pool AS (
                SELECT c.*
                FROM user_curator_deep_weight c
                WHERE TRUE
                {gate_sql}
            )
        """,
        f"""
            curator_active AS (
                SELECT
                    user_id,
                    curator_pct_weight,
                    weight_pctile,
                    deep_share,
                    com_share,
                    ({w_expr})::DOUBLE AS w
                FROM curator_pool c
            )
        """,
    ]
    return ctes, list(gate_args)


def wide_mint_ctes(deweight: float, purity: float) -> tuple[list[str], list[Any]]:
    """Wide percentile universe + LEFT JOIN deep-mint taste features.

    Continuity:
      * purity=0 → no gates; all percentile users remain.
      * deweight=0 → weight 1.0 for all.
      * deweight>0 → w = coalesce(deep_mint_score, MISSING)^expo.
        Uses *deep* mint weights only (not the wider pct-curator table), so
        bad-taste mass is negligible without needing a purity gate.
      * purity>0 → soft share/com gates on coalesced deep features (0 if absent).
    """
    gate_sql, gate_args = purity_gate_sql(purity, alias="u")
    expo = deweight_exponent(deweight)
    alpha = deweight_alpha(deweight)
    if expo <= 1e-12:
        w_sql = "1.0"
    else:
        w_sql = (
            f"(power(greatest(u.curator_pct_weight, 1e-9), {float(expo)}))"
        )
        if alpha > 1e-12:
            w_sql = (
                f"({w_sql} * exp(-({alpha}) * "
                f"(1.0 - coalesce(u.weight_pctile, 0))))"
            )

    ctes = [
        f"""
            curator_universe AS (
                SELECT
                    p.user_id,
                    -- Deep mint score only. pct_weight is a softer, larger pool
                    -- and must not dominate when purity=0.
                    coalesce(d.curator_pct_weight, {MISSING_WEIGHT})
                        ::DOUBLE AS curator_pct_weight,
                    coalesce(d.weight_pctile, 0.0)::DOUBLE AS weight_pctile,
                    coalesce(d.deep_share, 0.0)::DOUBLE AS deep_share,
                    coalesce(d.com_share, 0.0)::DOUBLE AS com_share,
                    coalesce(d.n_deep, 0)::BIGINT AS n_deep
                FROM user_star_percentiles p
                LEFT JOIN user_curator_deep_weight d USING (user_id)
            )
        """,
        f"""
            curator_active AS (
                SELECT
                    u.user_id,
                    u.curator_pct_weight,
                    u.weight_pctile,
                    u.deep_share,
                    u.com_share,
                    ({w_sql})::DOUBLE AS w
                FROM curator_universe u
                WHERE TRUE
                {gate_sql}
            )
        """,
    ]
    return ctes, list(gate_args)


def wide_live_ctes(
    *,
    deweight: float,
    purity: float,
    positive_ids: set[str],
    negative_ids: set[str],
    neutral_titles: list[str],
) -> tuple[list[str], list[Any]]:
    """Wide universe with live pack features — no mint floors."""
    pos = sorted(positive_ids)
    neg = sorted(negative_ids)
    if not pos and not neg:
        return [all_equal_cte()], []

    pos_sql = _id_list(pos)
    neg_sql = _id_list(neg)
    gate_sql, gate_args = purity_gate_sql(purity, alias="u")

    deep_exp = MINT_DEEP_EXP
    com_exp = MINT_COM_EXP
    # Soft base from pack features when no deep-mint row; never fall back to
    # the wide pct-curator table (same mass bug as wide_mint_ctes).
    soft_w = f"""
        (
            ln(1.0 + coalesce(feat.n_deep, 0)::DOUBLE)
            * power(greatest(coalesce(feat.deep_share, 0.05), 0.05), {deep_exp})
            * power(greatest(1.0 - coalesce(feat.com_share, 0), 0.02), {com_exp})
        )
    """
    weight_col = f"""
        coalesce(d.curator_pct_weight, ({soft_w}), {MISSING_WEIGHT})
    """

    expo = deweight_exponent(deweight)
    alpha = deweight_alpha(deweight)
    if expo <= 1e-12:
        w_sql = "1.0"
    else:
        w_sql = f"(power(greatest(u.curator_pct_weight, 1e-9), {float(expo)}))"
        if alpha > 1e-12:
            w_sql = (
                f"({w_sql} * exp(-({alpha}) * "
                f"(1.0 - coalesce(u.weight_pctile, 0))))"
            )

    ctes = [
        _neutral_works_cte(neutral_titles),
        f"""
            pack_pos AS (
                SELECT user_id,
                       sum(n_liked)::BIGINT AS n_deep,
                       sum(n_five)::BIGINT AS n_pos_five
                FROM user_author_likes
                WHERE author_id IN ({pos_sql})
                GROUP BY user_id
            )
        """,
        f"""
            pack_neg AS (
                SELECT user_id,
                       sum(n_five)::BIGINT AS n_neg_five
                FROM user_author_likes
                WHERE author_id IN ({neg_sql})
                GROUP BY user_id
            )
        """,
        """
            pack_neutral_hits AS (
                SELECT e.user_id, count(DISTINCT e.work_id)::BIGINT AS n_normie
                FROM all_rating_events e
                JOIN pack_neutral_works nw USING (work_id)
                WHERE e.rating >= 4
                GROUP BY e.user_id
            )
        """,
        f"""
            curator_universe AS (
                SELECT
                    p.user_id,
                    ({weight_col})::DOUBLE AS curator_pct_weight,
                    coalesce(d.weight_pctile, 0.0)::DOUBLE AS weight_pctile,
                    coalesce(feat.deep_share, 0.0)::DOUBLE AS deep_share,
                    coalesce(feat.com_share, 0.0)::DOUBLE AS com_share,
                    coalesce(feat.n_deep, 0)::BIGINT AS n_deep
                FROM user_star_percentiles p
                LEFT JOIN user_curator_deep_weight d USING (user_id)
                LEFT JOIN (
                    SELECT
                        coalesce(po.user_id, n.user_id, h.user_id) AS user_id,
                        coalesce(po.n_deep, 0)::BIGINT AS n_deep,
                        coalesce(po.n_pos_five, 0)::BIGINT AS n_pos_five,
                        coalesce(n.n_neg_five, 0)::BIGINT AS n_neg_five,
                        coalesce(h.n_normie, 0)::BIGINT AS n_normie,
                        (
                            coalesce(po.n_deep, 0)::DOUBLE
                            / nullif(
                                coalesce(po.n_deep, 0) + coalesce(h.n_normie, 0), 0
                            )
                        )::DOUBLE AS deep_share,
                        (
                            coalesce(n.n_neg_five, 0)::DOUBLE
                            / nullif(
                                coalesce(po.n_pos_five, 0)
                                + coalesce(n.n_neg_five, 0), 0
                            )
                        )::DOUBLE AS com_share
                    FROM pack_pos po
                    FULL OUTER JOIN pack_neg n USING (user_id)
                    FULL OUTER JOIN pack_neutral_hits h USING (user_id)
                ) feat USING (user_id)
            )
        """,
        f"""
            curator_active AS (
                SELECT
                    u.user_id,
                    u.curator_pct_weight,
                    u.weight_pctile,
                    u.deep_share,
                    u.com_share,
                    ({w_sql})::DOUBLE AS w
                FROM curator_universe u
                WHERE TRUE
                {gate_sql}
            )
        """,
    ]
    return ctes, list(gate_args)


def build_cohort_ctes(
    *,
    deweight: float,
    purity: float,
    pack: dict[str, Any] | None = None,
) -> tuple[list[str], list[Any], dict[str, Any]]:
    """Return (cte_sql_list, args, meta)."""
    dew = clamp01_100(deweight)
    pur = clamp01_100(purity)
    min_share = purity_min_share(pur)
    cap = com_share_cap(pur)
    use_mint_pack = pack is None or pack_uses_mint(pack)

    meta: dict[str, Any] = {
        "deweight": dew,
        "purity": pur,
        "min_deep_share": min_share,
        "com_share_cap": cap,
        "use_mint_pack": use_mint_pack,
    }

    # True off — no taste attention.
    if t01(dew) <= 1e-12 and t01(pur) <= 1e-12:
        meta["cohort_kind"] = "all_equal"
        meta["source"] = "user_star_percentiles"
        meta["fast_path"] = False
        return [all_equal_cte()], [], meta

    # Safe mint fast path only when purity already implies mint floors.
    if mint_fast_path_ok(purity=pur, use_mint_pack=use_mint_pack):
        meta["cohort_kind"] = "taste"
        meta["source"] = "user_curator_deep_weight"
        meta["fast_path"] = True
        ctes, args = mint_fast_ctes(dew, pur)
        return ctes, args, meta

    meta["fast_path"] = False
    meta["cohort_kind"] = "taste"
    if use_mint_pack:
        meta["source"] = "wide_percentile+mint_features"
        ctes, args = wide_mint_ctes(dew, pur)
        return ctes, args, meta

    pos, neg = pack_author_ids(pack)
    neutrals = list((pack or {}).get("neutral_titles") or [])
    meta["source"] = "wide_percentile+live_pack"
    meta["n_positive_authors"] = len(pos)
    meta["n_negative_authors"] = len(neg)
    meta["n_neutral_titles"] = len(neutrals)
    ctes, args = wide_live_ctes(
        deweight=dew,
        purity=pur,
        positive_ids=pos,
        negative_ids=neg,
        neutral_titles=neutrals,
    )
    return ctes, args, meta

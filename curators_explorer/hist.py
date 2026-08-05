"""Curator-cohort vs global star histograms for a single work."""

from __future__ import annotations

from typing import Any

from curators_explorer.catalog import parse_sf_only
from curators_explorer.cohort import build_cohort_ctes, clamp01_100
from curators_explorer.db import execute
from curators_explorer.ranking import WEIGHT_EVENT_EPS, _float_param
from curators_explorer.taste_packs import get_active_pack


def global_hist(work_id: str) -> dict[str, Any] | None:
    row = execute(
        """
        SELECT n, mean, std, n5, n4, n3, n2, n1, p5
        FROM work_scores
        WHERE work_id = ?
        """,
        [work_id],
    ).fetchone()
    if not row:
        return None
    n = int(row[0] or 0)
    stars = {
        "5": int(row[3] or 0),
        "4": int(row[4] or 0),
        "3": int(row[5] or 0),
        "2": int(row[6] or 0),
        "1": int(row[7] or 0),
    }
    return {
        "label": "Global (all Goodreads raters in catalog)",
        "n": n,
        "mean": float(row[1]) if row[1] is not None else None,
        "std": float(row[2]) if row[2] is not None else None,
        "p5": float(row[8]) if row[8] is not None else None,
        "stars": stars,
        "weighted": False,
    }


def curator_hist(work_id: str, params: dict[str, Any]) -> dict[str, Any]:
    deweight = clamp01_100(
        _float_param(params, "deweight", "curator_deweight", default=15.0)
    )
    purity = clamp01_100(
        _float_param(params, "purity", "normie_purity", default=55.0)
    )
    pack = params.get("pack")
    if not isinstance(pack, dict):
        pack = get_active_pack()

    ctes, args, meta = build_cohort_ctes(deweight=deweight, purity=purity, pack=pack)
    with_sql = ",\n".join(ctes)
    row = execute(
        f"""
        WITH {with_sql},
        ev AS (
            SELECT
                e.rating,
                c.w AS w
            FROM all_rating_events e
            JOIN curator_active c USING (user_id)
            WHERE e.work_id = ?
              AND e.rating BETWEEN 1 AND 5
              AND c.w > {WEIGHT_EVENT_EPS}
        )
        SELECT
            count(*)::BIGINT AS n_raw,
            coalesce(sum(w), 0)::DOUBLE AS w_sum,
            coalesce(sum(CASE WHEN rating = 5 THEN w ELSE 0 END), 0)::DOUBLE AS w5,
            coalesce(sum(CASE WHEN rating = 4 THEN w ELSE 0 END), 0)::DOUBLE AS w4,
            coalesce(sum(CASE WHEN rating = 3 THEN w ELSE 0 END), 0)::DOUBLE AS w3,
            coalesce(sum(CASE WHEN rating = 2 THEN w ELSE 0 END), 0)::DOUBLE AS w2,
            coalesce(sum(CASE WHEN rating = 1 THEN w ELSE 0 END), 0)::DOUBLE AS w1,
            (sum(w * rating) / nullif(sum(w), 0))::DOUBLE AS mean,
            stddev_pop(rating)::DOUBLE AS std
        FROM ev
        """,
        list(args) + [work_id],
    ).fetchone()

    if not row:
        return {
            "label": "Active curator cohort",
            "n": 0,
            "stars": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
            "weighted": deweight > 0,
            "cohort": meta,
        }

    w_sum = float(row[1] or 0)
    stars = {
        "5": float(row[2] or 0),
        "4": float(row[3] or 0),
        "3": float(row[4] or 0),
        "2": float(row[5] or 0),
        "1": float(row[6] or 0),
    }
    p5 = (stars["5"] / w_sum) if w_sum else None
    kind = meta.get("cohort_kind", "?")
    src = meta.get("source", "?")
    return {
        "label": (
            f"Curators ({kind}, {src}; deweight={int(deweight)}, "
            f"purity={int(purity)}; {'weighted' if deweight > 0 else 'equal weights'})"
        ),
        "n": int(row[0] or 0),
        "w_sum": w_sum,
        "mean": float(row[7]) if row[7] is not None else None,
        "std": float(row[8]) if row[8] is not None else None,
        "p5": p5,
        "stars": stars,
        "weighted": deweight > 0,
        "cohort": meta,
    }


def book_hists(work_id: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "global": global_hist(work_id),
        "curators": curator_hist(work_id, params),
        "sf_only": parse_sf_only(params),
    }

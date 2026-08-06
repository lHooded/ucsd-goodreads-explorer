"""Serve the fixed distributed-consensus and community-esteem rankings."""

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from typing import Any

from curators_explorer.db import DATA, execute, truthy

DISTRIBUTED_CANON_METRIC = "distributed_canon"
DISTRIBUTED_ESTEEM_METRIC = "distributed_esteem"
DISTRIBUTED_METRICS = {DISTRIBUTED_CANON_METRIC, DISTRIBUTED_ESTEEM_METRIC}
CATALOG_PATH = DATA / "distributed_canon_catalog.json"
JURY_SUMMARY_PATH = DATA / "soft_jury_weights_summary.json"


def _int_param(params: dict[str, Any], key: str, default: int) -> int:
    value = params.get(key)
    if value is None or value == "":
        return default
    return int(value)


def _metadata(work_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch display metadata in chunks to keep the parameter list modest."""
    out: dict[str, dict[str, Any]] = {}
    for start in range(0, len(work_ids), 750):
        chunk = work_ids[start : start + 750]
        placeholders = ",".join("?" for _ in chunk)
        rows = execute(
            f"""
            SELECT work_id, book_id, book_url, author_url, n, mean, std, p5,
                   p_low, polarization, is_sf
            FROM work_scores
            WHERE work_id IN ({placeholders})
            """,
            chunk,
        ).fetchall()
        for row in rows:
            out[str(row[0])] = {
                "book_id": row[1],
                "book_url": row[2],
                "author_url": row[3],
                "catalog_ratings": int(row[4] or 0),
                "mean": float(row[5]) if row[5] is not None else None,
                "std": float(row[6]) if row[6] is not None else None,
                "p5": float(row[7]) if row[7] is not None else None,
                "p_low": float(row[8]) if row[8] is not None else None,
                "polarization": float(row[9]) if row[9] is not None else None,
                "is_sf": bool(row[10]),
            }
    return out


@lru_cache(maxsize=1)
def _artifact() -> dict[str, Any]:
    """Load the raised-ceiling mass-2 catalogue once per server process."""
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Missing distributed-canon artifact: {CATALOG_PATH}")

    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    books = payload.get("books") or []
    work_ids = [str(row["work_id"]) for row in books]
    metadata = _metadata(work_ids)

    enriched: list[dict[str, Any]] = []
    for source in books:
        row = dict(source)
        row.update(metadata.get(str(row["work_id"]), {}))
        row.update(
            {
                "catalog_n": int(row.get("catalog_n") or row.get("catalog_ratings") or 0),
                "n": int(row.get("catalog_n") or row.get("catalog_ratings") or 0),
                "readers": int(row.get("catalog_n") or row.get("catalog_ratings") or 0),
                "votes": int(row.get("catalog_n") or row.get("catalog_ratings") or 0),
                "fixed_metric": True,
            }
        )
        enriched.append(row)

    jury = {}
    if JURY_SUMMARY_PATH.exists():
        jury = json.loads(JURY_SUMMARY_PATH.read_text(encoding="utf-8"))

    return {
        "method": payload.get("method") or {},
        "books": enriched,
        "by_work_id": {str(row["work_id"]): row for row in enriched},
        "jury": jury,
        "evidence_counts": dict(Counter(row["evidence_status"] for row in enriched)),
        "community_counts": dict(Counter(row["community_status"] for row in enriched)),
    }


def _metric_view(source: dict[str, Any], metric: str) -> dict[str, Any]:
    row = dict(source)
    if metric == DISTRIBUTED_ESTEEM_METRIC:
        row.update(
            {
                "rank": int(row["esteem_rank"]),
                "score": float(row["esteem"]),
                "uncertainty": float(row["esteem_uncertainty"]),
                "score_kind": "esteem",
            }
        )
    else:
        row.update(
            {
                "rank": int(row["consensus_rank"]),
                "score": float(row["consensus_score"]),
                "uncertainty": float(row["consensus_uncertainty"]),
                "score_kind": "consensus",
            }
        )
    row["uncertainty_kind"] = "analytic_sampling_plus_partition"
    return row


def distributed_canon_detail(
    work_id: str, metric: str = DISTRIBUTED_CANON_METRIC
) -> dict[str, Any] | None:
    """Return both fixed scores and the selected metric view for one work."""
    source = _artifact()["by_work_id"].get(str(work_id))
    return _metric_view(source, metric) if source else None


def rank_distributed_canon(params: dict[str, Any]) -> dict[str, Any]:
    """Filter either fixed ranking without recomputing its jury or scores."""
    artifact = _artifact()
    metric = str(params.get("metric") or DISTRIBUTED_CANON_METRIC).strip().lower()
    if metric not in DISTRIBUTED_METRICS:
        metric = DISTRIBUTED_CANON_METRIC
    limit = max(1, min(5000, _int_param(params, "limit", 200)))
    q = str(params.get("q") or "").strip().casefold()
    sf_only = truthy(params.get("sf_only"))

    rows = artifact["books"]
    if sf_only:
        rows = [row for row in rows if row.get("is_sf")]
    if q:
        rows = [
            row
            for row in rows
            if q in str(row.get("title") or "").casefold()
            or q in str(row.get("author") or "").casefold()
            or q == str(row.get("work_id") or "").casefold()
            or q == str(row.get("book_id") or "").casefold()
        ]
    rank_key = "esteem_rank" if metric == DISTRIBUTED_ESTEEM_METRIC else "consensus_rank"
    rows = sorted(rows, key=lambda row: int(row[rank_key]))
    results = [_metric_view(row, metric) for row in rows[:limit]]

    jury = artifact["jury"]
    method = artifact["method"]
    return {
        "results": results,
        "n_results": len(results),
        "params": {
            "metric": metric,
            "scale_mode": "fixed model",
            "fixed_model": True,
            "limit": limit,
            "q": q,
            "sf_only": sf_only,
            "audited_top": int(method.get("ranked_books") or len(artifact["books"])),
            "point_rankable": len(artifact["books"]),
            "publication_pair_mass": method.get("publication_pair_mass"),
            "minimum_pair_mass": method.get("minimum_pair_mass"),
        },
        "cohort": {
            "n_curators": int(jury.get("soft_nonzero_users") or 0),
            "effective_curators": float(jury.get("kish_effective_users") or 0),
            "jury_mass": float(jury.get("soft_mass") or 0),
            "cohort_kind": "soft distributed jury",
            "source": "raised-ceiling cap-120 model",
        },
        "research": {
            "book_evidence_cap": method.get("book_evidence_cap"),
            "cell_evidence_cap": method.get("cell_evidence_cap"),
            "evidence_counts": artifact["evidence_counts"],
            "community_counts": artifact["community_counts"],
            "uncertainty": method.get("uncertainty_kind"),
        },
    }

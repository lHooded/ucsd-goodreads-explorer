"""Editable taste packs: positive / negative authors + school-neutral titles."""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from typing import Any

from curators_explorer.db import (
    DEFAULT_PRESET_PATH,
    LEGACY_NORMIE_PATH,
    LEGACY_TASTE_PATH,
    PRESETS_PATH,
    WAREHOUSE_DB,
    execute,
)

_LOCK = threading.RLock()
# Session pack state (process-local). Reset restores shipped preset.
_ACTIVE: dict[str, Any] | None = None
_DEFAULT: dict[str, Any] | None = None


def _author_entry(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "author_id": str(raw["author_id"]),
        "name": str(raw.get("name") or raw.get("resolved_name") or raw.get("match") or ""),
        "match": str(raw.get("match") or raw.get("name") or ""),
        **{
            k: raw[k]
            for k in ("prestige", "poll_rank")
            if k in raw and raw[k] is not None
        },
    }


def load_shipped_preset() -> dict[str, Any]:
    global _DEFAULT
    with _LOCK:
        if _DEFAULT is not None:
            return copy.deepcopy(_DEFAULT)
        if DEFAULT_PRESET_PATH.exists():
            data = json.loads(DEFAULT_PRESET_PATH.read_text(encoding="utf-8"))
        else:
            # Fallback: build from legacy files if preset missing.
            taste = json.loads(LEGACY_TASTE_PATH.read_text(encoding="utf-8"))
            normie = json.loads(LEGACY_NORMIE_PATH.read_text(encoding="utf-8"))
            data = {
                "id": "default_literary",
                "label": "Default literary",
                "sliders": {
                    "deweight": 15,
                    "purity": 55,
                    "min_votes": 25,
                    "bayesian_m": 30,
                    "scale_mode": "adjusted",
                    "metric": "love",
                    "sf_only": False,
                    "limit": 200,
                },
                "positive_authors": [
                    _author_entry(s) for s in taste["resolved"]["literary_poll"]
                ],
                "negative_authors": [
                    _author_entry(s) for s in taste["resolved"]["non_literary"]
                ],
                "neutral_titles": list(normie.get("titles") or []),
            }
        _DEFAULT = data
        return copy.deepcopy(data)


def load_slider_presets() -> dict[str, Any]:
    if PRESETS_PATH.exists():
        return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
    return {}


def get_active_pack() -> dict[str, Any]:
    global _ACTIVE
    with _LOCK:
        if _ACTIVE is None:
            _ACTIVE = load_shipped_preset()
        return copy.deepcopy(_ACTIVE)


def reset_pack() -> dict[str, Any]:
    global _ACTIVE
    with _LOCK:
        _ACTIVE = load_shipped_preset()
        return copy.deepcopy(_ACTIVE)


def update_pack(patch: dict[str, Any]) -> dict[str, Any]:
    """Replace or patch positive/negative author lists and/or neutral titles."""
    global _ACTIVE
    with _LOCK:
        cur = get_active_pack() if _ACTIVE is None else copy.deepcopy(_ACTIVE)
        if "positive_authors" in patch:
            cur["positive_authors"] = [
                _author_entry(a) for a in (patch["positive_authors"] or []) if a.get("author_id")
            ]
        if "negative_authors" in patch:
            cur["negative_authors"] = [
                _author_entry(a) for a in (patch["negative_authors"] or []) if a.get("author_id")
            ]
        if "neutral_titles" in patch:
            cur["neutral_titles"] = [
                str(t).strip() for t in (patch["neutral_titles"] or []) if str(t).strip()
            ]
        _ACTIVE = cur
        return copy.deepcopy(_ACTIVE)


def pack_author_ids(pack: dict[str, Any] | None = None) -> tuple[set[str], set[str]]:
    pack = pack or get_active_pack()
    pos = {str(a["author_id"]) for a in pack.get("positive_authors") or [] if a.get("author_id")}
    neg = {str(a["author_id"]) for a in pack.get("negative_authors") or [] if a.get("author_id")}
    return pos, neg


def pack_uses_mint(pack: dict[str, Any] | None = None) -> bool:
    """Use the deep mint table when packs are the default set or a safe subset.

    Exact match → mint features are authoritative.
    Positive ⊆ literary_poll and negative == non_literary → still mint
    (removing positives only; mint gates remain valid / slightly conservative).
    """
    pack = pack or get_active_pack()
    pos, neg = pack_author_ids(pack)
    try:
        rows = execute(
            "SELECT author_id, side FROM taste_authors WHERE side IN ('literary_poll', 'non_literary')"
        ).fetchall()
    except Exception:
        return False
    mint_pos = {str(r[0]) for r in rows if r[1] == "literary_poll"}
    mint_neg = {str(r[0]) for r in rows if r[1] == "non_literary"}
    if not mint_pos:
        return False
    if pos == mint_pos and neg == mint_neg:
        return True
    # Safe subset: same anti-signal pile, positives only removed (not replaced).
    if neg == mint_neg and pos and pos.issubset(mint_pos):
        return True
    return False


def pack_matches_mint(pack: dict[str, Any] | None = None) -> bool:
    """True when packs exactly match the literary_poll / non_literary mint sides."""
    pack = pack or get_active_pack()
    pos, neg = pack_author_ids(pack)
    try:
        rows = execute(
            "SELECT author_id, side FROM taste_authors WHERE side IN ('literary_poll', 'non_literary')"
        ).fetchall()
    except Exception:
        return False
    mint_pos = {str(r[0]) for r in rows if r[1] == "literary_poll"}
    mint_neg = {str(r[0]) for r in rows if r[1] == "non_literary"}
    return pos == mint_pos and neg == mint_neg


def pack_hash(pack: dict[str, Any] | None = None) -> str:
    pack = pack or get_active_pack()
    pos, neg = pack_author_ids(pack)
    neutrals = sorted(str(t) for t in (pack.get("neutral_titles") or []))
    payload = {
        "pos": sorted(pos),
        "neg": sorted(neg),
        "neutral": neutrals,
    }
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def search_authors(q: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """Resolve author names for the pack editor."""
    q = (q or "").strip()
    if not q:
        return []
    limit = max(1, min(50, int(limit)))
    like = f"%{q}%"
    # Prefer taste_authors (already in explorer DB), then warehouse authors.
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        rows = execute(
            """
            SELECT author_id, match_name, side, prestige
            FROM taste_authors
            WHERE match_name ILIKE ?
            ORDER BY coalesce(prestige, 0) DESC, match_name
            LIMIT ?
            """,
            [like, limit],
        ).fetchall()
        for aid, name, side, prestige in rows:
            aid = str(aid)
            if aid in seen:
                continue
            seen.add(aid)
            out.append(
                {
                    "author_id": aid,
                    "name": name,
                    "match": name,
                    "side": side,
                    "prestige": float(prestige) if prestige is not None else 0.0,
                }
            )
    except Exception:
        pass

    if len(out) >= limit or not WAREHOUSE_DB.exists():
        return out[:limit]

    try:
        import duckdb

        con = duckdb.connect(str(WAREHOUSE_DB), read_only=True)
        try:
            rows = con.execute(
                """
                SELECT author_id, name, coalesce(ratings_count, 0)
                FROM authors
                WHERE name ILIKE ?
                ORDER BY coalesce(ratings_count, 0) DESC
                LIMIT ?
                """,
                [like, limit],
            ).fetchall()
        finally:
            con.close()
        for aid, name, rc in rows:
            aid = str(aid)
            if aid in seen:
                continue
            seen.add(aid)
            out.append(
                {
                    "author_id": aid,
                    "name": name,
                    "match": name,
                    "ratings_count": int(rc or 0),
                }
            )
            if len(out) >= limit:
                break
    except Exception:
        pass
    return out[:limit]


def pack_payload() -> dict[str, Any]:
    pack = get_active_pack()
    return {
        "pack": pack,
        "pack_hash": pack_hash(pack),
        "matches_mint": pack_matches_mint(pack),
        "uses_mint": pack_uses_mint(pack),
        "presets": load_slider_presets(),
        "shipped_sliders": (load_shipped_preset().get("sliders") or {}),
    }

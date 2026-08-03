#!/usr/bin/env python3
"""Shared DuckDB connection helpers for the UCSD explorer."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
PARQUET = ROOT / "data" / "ucsd_goodreads" / "parquet"
DERIVED = ROOT / "data" / "ucsd_goodreads" / "derived"
DB_PATH = ROOT / "data" / "ucsd_goodreads" / "explorer.duckdb"
EXPLORER_DB = DB_PATH  # alias used by materializers
META_PATH = DERIVED / "explorer_meta.json"
TASTE_PATH = Path(__file__).resolve().parent / "data" / "taste_lists.json"
NORMIE_PATH = Path(__file__).resolve().parent / "data" / "normie_canon.json"
OVERRIDES_PATH = Path(__file__).resolve().parent / "data" / "catalog_overrides.json"

_LOCK = threading.RLock()
_CON = None
META: dict[str, Any] = {}
GLOBALS: dict[str, float] = {"global_p5": 0.4, "median_user_five_rate": 0.37, "global_mean": 3.8}


def ensure_db():
    import duckdb

    if not DB_PATH.exists():
        raise SystemExit(
            f"Missing {DB_PATH}. Run:\n"
            "  .venv/bin/python -m ucsd_explorer.materialize_ratings"
        )
    con = duckdb.connect(str(DB_PATH), read_only=True)
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "work_scores" not in tables:
        con.close()
        raise SystemExit(
            "Explorer DB is the old ballot schema. Rebuild with:\n"
            "  .venv/bin/python -m ucsd_explorer.materialize_ratings"
        )
    return con


def get_con():
    global _CON, META, GLOBALS
    with _LOCK:
        if _CON is None:
            _CON = ensure_db()
            if META_PATH.exists():
                data = json.loads(META_PATH.read_text(encoding="utf-8"))
                META.clear()
                META.update(data)
            try:
                cols = {r[0] for r in _CON.execute("DESCRIBE explorer_globals").fetchall()}
                if "global_p5_sf" in cols:
                    g = _CON.execute(
                        """
                        SELECT global_p5, global_p5_sf, global_p5_all,
                               global_mean_sf, global_mean_all, median_user_five_rate
                        FROM explorer_globals
                        """
                    ).fetchone()
                    GLOBALS["global_p5"] = float(g[0])
                    GLOBALS["global_p5_sf"] = float(g[1])
                    GLOBALS["global_p5_all"] = float(g[2])
                    GLOBALS["global_mean_sf"] = float(g[3])
                    GLOBALS["global_mean_all"] = float(g[4])
                    GLOBALS["global_mean"] = float(g[3])
                    GLOBALS["median_user_five_rate"] = float(g[5])
                else:
                    g = _CON.execute(
                        "SELECT global_p5, median_user_five_rate FROM explorer_globals"
                    ).fetchone()
                    GLOBALS["global_p5"] = float(g[0])
                    GLOBALS["median_user_five_rate"] = float(g[1])
            except Exception:
                pass
            try:
                # Prefer SF mean as default display mean
                gm = _CON.execute(
                    "SELECT avg(mean) FROM work_scores WHERE coalesce(is_sf, TRUE)"
                ).fetchone()[0]
                if gm is not None:
                    GLOBALS.setdefault("global_mean", float(gm))
            except Exception:
                try:
                    gm = _CON.execute("SELECT avg(mean) FROM work_scores").fetchone()[0]
                    if gm is not None:
                        GLOBALS["global_mean"] = float(gm)
                except Exception:
                    pass
            try:
                # Detect whether genre toggle is available
                ws_cols = {r[0] for r in _CON.execute("DESCRIBE work_scores").fetchall()}
                META["genre_filter_available"] = "is_sf" in ws_cols
            except Exception:
                META["genre_filter_available"] = False
        return _CON


def execute(sql: str, args: list[Any] | None = None):
    """Thread-safe query; returns a result handle that already fetched under the lock.

    DuckDB connections are not safe to interleave execute/fetch across threads, so
    callers should use fetchall()/fetchone() on the returned _Result (data already
    materialized).
    """
    con = get_con()
    with _LOCK:
        cur = con.execute(sql) if args is None else con.execute(sql, args)
        rows = cur.fetchall()
        description = cur.description
    return _Result(rows, description)


class _Result:
    """Minimal stand-in for a DuckDB result so existing .fetchall/.fetchone call sites work."""

    __slots__ = ("_rows", "description")

    def __init__(self, rows: list, description):
        self._rows = rows
        self.description = description

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


def table_names() -> set[str]:
    rows = execute("SHOW TABLES").fetchall()
    return {r[0] for r in rows}


def truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def resolve_work_id(book_or_work_id: str) -> tuple[str, str] | None:
    """Map a Goodreads book_id or work_id to (work_id, book_id).

    Prefer an exact book_id hit. Many book_ids collide with unrelated work_ids
    (e.g. Brothers Karamazov book_id 4934 vs work_id 4934 = a different book),
    so ``WHERE book_id=? OR work_id=?`` + fetchone() is unsafe.
    """
    key = str(book_or_work_id)
    row = execute(
        """
        SELECT work_id, book_id
        FROM work_scores
        WHERE book_id = ? OR work_id = ?
        ORDER BY CASE WHEN book_id = ? THEN 0 ELSE 1 END
        LIMIT 1
        """,
        [key, key, key],
    ).fetchone()
    if not row:
        return None
    return str(row[0]), str(row[1])

"""Read-only DuckDB access to the shared explorer warehouse."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PKG = Path(__file__).resolve().parent
STATIC = PKG / "static"
DATA = PKG / "data"
DB_PATH = ROOT / "data" / "ucsd_goodreads" / "explorer.duckdb"
WAREHOUSE_DB = ROOT / "data" / "ucsd_goodreads" / "ucsd.duckdb"
META_PATH = ROOT / "data" / "ucsd_goodreads" / "derived" / "explorer_meta.json"
DEFAULT_PRESET_PATH = DATA / "default_preset.json"
PRESETS_PATH = DATA / "presets.json"
LEGACY_TASTE_PATH = ROOT / "ucsd_explorer" / "data" / "taste_lists.json"
LEGACY_NORMIE_PATH = ROOT / "ucsd_explorer" / "data" / "normie_canon.json"

_LOCK = threading.RLock()
_CON = None
META: dict[str, Any] = {}
GLOBALS: dict[str, float] = {
    "global_p5": 0.4,
    "median_user_five_rate": 0.37,
    "global_mean": 3.8,
}


def ensure_db():
    import duckdb

    if not DB_PATH.exists():
        raise SystemExit(
            f"Missing {DB_PATH}. Materialize with:\n"
            "  .venv/bin/python -m ucsd_explorer.materialize_ratings"
        )
    con = duckdb.connect(str(DB_PATH), read_only=True)
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    required = {
        "work_scores",
        "all_rating_events",
        "user_star_percentiles",
        "user_curator_deep_weight",
    }
    missing = required - tables
    if missing:
        con.close()
        raise SystemExit(f"Explorer DB missing tables: {sorted(missing)}")
    return con


def get_con():
    global _CON, META, GLOBALS
    with _LOCK:
        if _CON is None:
            _CON = ensure_db()
            if META_PATH.exists():
                META.clear()
                META.update(json.loads(META_PATH.read_text(encoding="utf-8")))
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
                    GLOBALS.update(
                        {
                            "global_p5": float(g[0]),
                            "global_p5_sf": float(g[1]),
                            "global_p5_all": float(g[2]),
                            "global_mean_sf": float(g[3]),
                            "global_mean_all": float(g[4]),
                            "global_mean": float(g[3]),
                            "median_user_five_rate": float(g[5]),
                        }
                    )
                else:
                    g = _CON.execute(
                        "SELECT global_p5, median_user_five_rate FROM explorer_globals"
                    ).fetchone()
                    GLOBALS["global_p5"] = float(g[0])
                    GLOBALS["median_user_five_rate"] = float(g[1])
            except Exception:
                pass
            try:
                tables = {r[0] for r in _CON.execute("SHOW TABLES").fetchall()}
                META["has_genre_gates"] = "work_genre_gates" in tables
                META["has_catalog_flags"] = "work_flags" in tables
                META["has_user_star_hist"] = "user_star_hist" in tables
                META["has_user_author_likes"] = "user_author_likes" in tables
                META["has_normie_works"] = "normie_works" in tables
            except Exception:
                pass
        return _CON


def execute(sql: str, args: list[Any] | None = None):
    """Thread-safe query; materialize rows under the lock (DuckDB is not MT-safe)."""
    con = get_con()
    with _LOCK:
        cur = con.execute(sql) if args is None else con.execute(sql, args)
        rows = cur.fetchall()
        description = cur.description
    return _Result(rows, description)


class _Result:
    __slots__ = ("_rows", "description")

    def __init__(self, rows: list, description):
        self._rows = rows
        self.description = description

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


def table_names() -> set[str]:
    return {r[0] for r in execute("SHOW TABLES").fetchall()}


def truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def resolve_work_id(book_or_work_id: str) -> tuple[str, str] | None:
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

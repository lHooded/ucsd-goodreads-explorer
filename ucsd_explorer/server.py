#!/usr/bin/env python3
"""HTTP front-end for the UCSD favorites explorer."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ucsd_explorer.db import GLOBALS, META, STATIC, TASTE_PATH, execute, get_con, resolve_work_id
from ucsd_explorer.ranking import METHODS, rank_books, work_relevant_hist
from ucsd_explorer.similarity import SIM_METHODS, similar_books
from ucsd_explorer.catalog_flags import has_catalog_flags
from ucsd_explorer.genre_gates import GATE_DEFS, GATE_IDS, has_genre_gates
from ucsd_explorer.genres import SF_PRESET_INCLUDE, has_genre_tables, search_genres
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


def _filtered_star_hist(work_id: str, taste: dict[str, Any] | None) -> dict[str, Any] | None:
    """Star histogram for a work, optionally restricted to taste-eligible users."""
    if not taste:
        return None
    if not has_taste_tables():
        return {"error": "taste tables missing", "n": 0, "stars": {}}
    taste_cte, taste_args = taste_eligible_cte(taste)
    row = execute(
        f"""
        WITH {taste_cte},
        ev AS (
            SELECT e.rating
            FROM all_rating_events e
            JOIN eligible USING (user_id)
            WHERE e.work_id = ?
        )
        SELECT
            count(*)::BIGINT AS n,
            sum(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::BIGINT AS n5,
            sum(CASE WHEN rating = 4 THEN 1 ELSE 0 END)::BIGINT AS n4,
            sum(CASE WHEN rating = 3 THEN 1 ELSE 0 END)::BIGINT AS n3,
            sum(CASE WHEN rating = 2 THEN 1 ELSE 0 END)::BIGINT AS n2,
            sum(CASE WHEN rating = 1 THEN 1 ELSE 0 END)::BIGINT AS n1,
            avg(rating)::DOUBLE AS mean,
            stddev_pop(rating)::DOUBLE AS std
        FROM ev
        """,
        taste_args + [work_id],
    ).fetchone()
    if not row:
        return {"n": 0, "stars": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}}
    n = int(row[0] or 0)
    n5 = int(row[1] or 0)
    stars = {
        "5": n5,
        "4": int(row[2] or 0),
        "3": int(row[3] or 0),
        "2": int(row[4] or 0),
        "1": int(row[5] or 0),
    }
    p5 = (n5 / n) if n else None
    return {
        "n": n,
        "mean": float(row[6]) if row[6] is not None else None,
        "std": float(row[7]) if row[7] is not None else None,
        "p5": p5,
        "stars": stars,
        "taste": taste,
    }


def book_detail(book_id: str, params: dict[str, Any]) -> dict[str, Any]:
    raw_limit = params.get("limit")
    limit = min(max(1, int(raw_limit) if raw_limit not in (None, "") else 40), 100)
    raw_sim_limit = params.get("sim_limit")
    sim_limit = min(max(1, int(raw_sim_limit) if raw_sim_limit not in (None, "") else 20), 50)
    raw_min_both = params.get("min_both")
    min_both = max(1, int(raw_min_both) if raw_min_both not in (None, "") else 3)
    taste = parse_taste_params(params)
    resolved = resolve_work_id(book_id)
    if not resolved:
        return {"error": "not found"}
    work_id, _canonical_book_id = resolved
    row = execute(
        """
        SELECT
            s.work_id, s.book_id, s.title, s.author, s.book_url, s.author_url,
            s.n, s.mean, s.std, s.n5, s.n4, s.n3, s.n2, s.n1, s.n_low,
            s.p5, s.p1, s.p_low, s.polarization,
            p.picky_five_mass, p.n5_picky_events
        FROM work_scores s
        LEFT JOIN work_picky p USING (work_id)
        WHERE s.work_id = ?
        """,
        [work_id],
    ).fetchone()
    if not row:
        return {"error": "not found"}
    if has_taste_tables():
        supporters = execute(
            """
            SELECT f.user_id, f.n_rated, f.five_rate, f.picky_weight,
                   t.lit_share, t.com_share, t.net_share, t.lit_hits, t.com_hits,
                   w.lit_weight
            FROM five_star_events f
            LEFT JOIN user_taste t ON f.user_id = t.user_id
            LEFT JOIN user_lit_weight w ON f.user_id = w.user_id
            WHERE f.work_id = ?
            ORDER BY coalesce(w.lit_weight, 0) DESC, f.picky_weight DESC
            LIMIT ?
            """,
            [work_id, limit],
        ).fetchall()
    else:
        supporters = execute(
            """
            SELECT user_id, n_rated, five_rate, picky_weight,
                   NULL, NULL, NULL, NULL, NULL, NULL
            FROM five_star_events
            WHERE work_id = ?
            ORDER BY picky_weight DESC, n_rated DESC
            LIMIT ?
            """,
            [work_id, limit],
        ).fetchall()

    p0 = GLOBALS["global_p5"]
    n, n5 = int(row[6]), int(row[9])
    m = 50.0
    bayes_p5 = (n5 + m * p0) / (n + m)

    out = {
        "book": {
            "work_id": row[0],
            "book_id": row[1],
            "title": row[2],
            "author": row[3],
            "book_url": row[4],
            "author_url": row[5],
            "n": n,
            "mean": row[7],
            "std": row[8],
            "n5": n5,
            "n4": row[10],
            "n3": row[11],
            "n2": row[12],
            "n1": row[13],
            "n_low": row[14],
            "p5": row[15],
            "p1": row[16],
            "p_low": row[17],
            "polarization": row[18],
            "picky_five_mass": row[19],
            "bayesian_p5": bayes_p5,
            "stars": {
                "5": n5,
                "4": int(row[10] or 0),
                "3": int(row[11] or 0),
                "2": int(row[12] or 0),
                "1": int(row[13] or 0),
            },
        },
        "n_supporters": n5,
        "supporters": [
            {
                "user_id": str(s[0]),
                "user_name": f"user_{s[0]}",
                "books_read": int(s[1]),
                "five_rate": float(s[2]),
                "picky_weight": float(s[3]),
                "lit_share": float(s[4]) if s[4] is not None else None,
                "com_share": float(s[5]) if s[5] is not None else None,
                "net_share": float(s[6]) if s[6] is not None else None,
                "lit_hits": int(s[7]) if s[7] is not None else 0,
                "com_hits": int(s[8]) if s[8] is not None else 0,
                "lit_weight": float(s[9]) if s[9] is not None else None,
            }
            for s in supporters
        ],
        "sim_methods": SIM_METHODS,
    }

    # Point at a more-rated same-title edition when this one is a stub / adaptation
    if n < 200:
        better = execute(
            """
            SELECT book_id, title, author, n
            FROM work_scores
            WHERE title = ?
              AND work_id != ?
              AND n >= greatest(? * 5, 200)
            ORDER BY n DESC
            LIMIT 1
            """,
            [row[2], work_id, n],
        ).fetchone()
        if better:
            out["better_edition"] = {
                "book_id": better[0],
                "title": better[1],
                "author": better[2],
                "n": int(better[3]),
            }

    filtered = _filtered_star_hist(work_id, taste)
    if filtered is not None:
        out["filtered_hist"] = filtered

    try:
        relevant = work_relevant_hist(work_id, params)
    except Exception as e:
        relevant = {"error": str(e), "n": 0, "stars": {}}
    if relevant is not None:
        out["relevant_hist"] = relevant
        bits = []
        if relevant.get("weighted"):
            bits.append("weighted by ranking cohort weights")
        if relevant.get("label"):
            bits.append(str(relevant["label"]))
        out["hist_note"] = (
            "Relevant histogram: "
            + (" · ".join(bits) if bits else "users who contribute to the current ranking.")
        )
    elif taste:
        out["hist_note"] = "Filtered histogram uses the current taste sliders."
    else:
        out["hist_note"] = (
            "Select a curator method and/or enable taste filter to see a "
            "ranking-cohort histogram (with weights when applicable)."
        )
    try:
        from ucsd_explorer.catalog_flags import has_catalog_flags

        if has_catalog_flags():
            fl = execute(
                """
                SELECT is_collection, is_derivative, is_nonfiction, is_excluded,
                       is_duplicate, canonical_work_id, canonical_book_id,
                       canonical_title, format_weight, flags, is_comic
                FROM work_flags WHERE work_id = ?
                """,
                [work_id],
            ).fetchone()
            if fl:
                out["catalog"] = {
                    "is_collection": bool(fl[0]),
                    "is_derivative": bool(fl[1]),
                    "is_nonfiction": bool(fl[2]),
                    "is_excluded": bool(fl[3]),
                    "is_duplicate": bool(fl[4]),
                    "canonical_work_id": fl[5],
                    "canonical_book_id": fl[6],
                    "canonical_title": fl[7],
                    "format_weight": float(fl[8]) if fl[8] is not None else 1.0,
                    "flags": fl[9] or "",
                    "is_comic": bool(fl[10]),
                }
    except Exception:
        pass

    if str(params.get("similar") or "1").lower() not in ("0", "false", "no"):
        try:
            sim_params = dict(params)
            sim_params["sim_method"] = params.get("sim_method") or "cosine"
            sim_params["sim_limit"] = sim_limit
            sim_params["limit"] = sim_limit
            sim_params["min_both"] = min_both
            out["similar"] = similar_books(book_id, sim_params)
        except Exception as e:
            out["similar"] = {"error": str(e), "results": []}
    return out


def taste_payload() -> dict[str, Any]:
    get_con()
    if TASTE_PATH.exists():
        data = json.loads(TASTE_PATH.read_text(encoding="utf-8"))
    else:
        static = STATIC / "data" / "taste_lists.json"
        data = json.loads(static.read_text(encoding="utf-8")) if static.exists() else {}
    resolved = data.get("resolved") or {}
    literary = (
        [{"kind": "author", "match": s["match"]} for s in resolved.get("literary_poll") or []]
        or data.get("literary")
        or []
    )
    literary_sf = (
        [{"kind": "author", "match": s["match"]} for s in resolved.get("literary_sf") or []]
        or data.get("literary_sf_extras")
        or []
    )
    non_literary = (
        [{"kind": "author", "match": s["match"]} for s in resolved.get("non_literary") or []]
        or data.get("non_literary")
        or data.get("commercial")
        or []
    )
    stats = {}
    if has_taste_tables():
        try:
            row = execute(
                """
                SELECT count(*),
                       count(*) FILTER (WHERE lit_share >= 0.5),
                       count(*) FILTER (WHERE com_share >= 0.5)
                FROM user_taste
                """
            ).fetchone()
            stats = {
                "n_users_with_taste": int(row[0]),
                "n_lit_lean": int(row[1] or 0),
                "n_nonlit_lean": int(row[2] or 0),
            }
        except Exception:
            stats = {}
    return {
        "literary": literary,
        "literary_sf_extras": literary_sf,
        "non_literary": non_literary,
        "commercial": non_literary,
        "notes": data.get("notes"),
        "dropped_from_literary": data.get("dropped_from_literary"),
        "non_literary_audit": data.get("non_literary_audit"),
        "stats": stats,
        "lit_weights_available": has_lit_weights(),
        "curator_weights_available": has_curator_weights(),
        "curator_pct_weights_available": has_curator_pct_weights(),
        "curator_pure_weights_available": has_curator_pure_weights(),
        "curator_pct_pure_weights_available": has_curator_pct_pure_weights(),
        "curator_deep_weights_available": has_curator_deep_weights(),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[ucsd_explorer] {self.address_string()} {fmt % args}", flush=True)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if path.suffix in {".js", ".css", ".html"}:
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        if path in ("/", "/index.html"):
            return self._file(STATIC / "index.html", "text/html; charset=utf-8")
        if path == "/app.js":
            return self._file(STATIC / "app.js", "application/javascript; charset=utf-8")
        if path == "/styles.css":
            return self._file(STATIC / "styles.css", "text/css; charset=utf-8")
        if path.startswith("/data/"):
            rel = path[len("/data/") :]
            fp = STATIC / "data" / rel
            if fp.exists() and fp.is_file():
                ctype = (
                    "application/json"
                    if fp.suffix == ".json"
                    else "application/octet-stream"
                )
                return self._file(fp, ctype)
            return self._json(404, {"error": "not found"})
        if path == "/api/meta":
            get_con()
            return self._json(
                200,
                {
                    **META,
                    "methods": METHODS,
                    "sim_methods": SIM_METHODS,
                    "globals": GLOBALS,
                    "taste_available": has_taste_tables(),
                    "lit_weights_available": has_lit_weights(),
                    "curator_weights_available": has_curator_weights(),
                    "curator_pct_weights_available": has_curator_pct_weights(),
                    "curator_pure_weights_available": has_curator_pure_weights(),
                    "curator_pct_pure_weights_available": has_curator_pct_pure_weights(),
                    "curator_deep_weights_available": has_curator_deep_weights(),
                    "catalog_flags_available": has_catalog_flags(),
                    "genres_available": has_genre_tables(),
                    "genre_gates_available": has_genre_gates(),
                    "genre_gate_presets": [
                        {"id": gid, "label": GATE_DEFS[gid]["label"]}
                        for gid in GATE_IDS
                    ],
                    "sf_preset_include": list(SF_PRESET_INCLUDE),
                    "note": "Unordered 5★ / literary-weighted / similar-books explorer.",
                },
            )
        if path == "/api/genres":
            try:
                q = qs.get("q") or ""
                limit = int(qs.get("limit") or 40)
                return self._json(200, {"genres": search_genres(q, limit=limit)})
            except Exception as e:
                return self._json(400, {"error": str(e)})
        if path == "/api/taste":
            try:
                return self._json(200, taste_payload())
            except Exception as e:
                return self._json(400, {"error": str(e)})
        if path == "/api/rank":
            try:
                return self._json(200, rank_books(qs))
            except Exception as e:
                return self._json(400, {"error": str(e)})
        m = re.match(r"^/api/book/([^/]+)/similar$", path)
        if m:
            try:
                return self._json(200, similar_books(m.group(1), qs))
            except Exception as e:
                return self._json(400, {"error": str(e)})
        m = re.match(r"^/api/book/([^/]+)$", path)
        if m:
            try:
                return self._json(200, book_detail(m.group(1), qs))
            except Exception as e:
                return self._json(400, {"error": str(e)})
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid JSON"})
        if parsed.path == "/api/rank":
            try:
                return self._json(200, rank_books(body))
            except Exception as e:
                return self._json(400, {"error": str(e)})
        m = re.match(r"^/api/book/([^/]+)/similar$", parsed.path)
        if m:
            try:
                return self._json(200, similar_books(m.group(1), body))
            except Exception as e:
                return self._json(400, {"error": str(e)})
        m = re.match(r"^/api/book/([^/]+)$", parsed.path)
        if m:
            try:
                return self._json(200, book_detail(m.group(1), body))
            except Exception as e:
                return self._json(400, {"error": str(e)})
        self._json(404, {"error": "not found"})


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8766)
    args = p.parse_args()
    get_con()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"UCSD explorer → http://{args.host}:{args.port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()

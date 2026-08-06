"""HTTP front-end for the curators explorer."""

from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from curators_explorer.db import GLOBALS, META, STATIC, execute, get_con, resolve_work_id
from curators_explorer.distributed_canon import (
    DISTRIBUTED_METRICS,
    distributed_canon_detail,
)
from curators_explorer.hist import book_hists
from curators_explorer.ranking import METRICS, SCALE_MODES, rank_books
from curators_explorer.taste_packs import (
    get_active_pack,
    pack_payload,
    reset_pack,
    search_authors,
    update_pack,
)

HOST = "127.0.0.1"
PORT = 8767


def _qs(params: dict[str, list[str]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, vals in params.items():
        if not vals:
            continue
        out[k] = vals[0] if len(vals) == 1 else vals
    return out


def book_detail(book_id: str, params: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_work_id(book_id)
    if not resolved:
        return {"error": "not found"}
    work_id, _ = resolved
    row = execute(
        """
        SELECT
            s.work_id, s.book_id, s.title, s.author, s.book_url, s.author_url,
            s.n, s.mean, s.std, s.n5, s.n4, s.n3, s.n2, s.n1,
            s.p5, s.p1, s.p_low, s.polarization
        FROM work_scores s
        WHERE s.work_id = ?
        """,
        [work_id],
    ).fetchone()
    if not row:
        return {"error": "not found"}
    metric = str(params.get("metric") or params.get("method") or "").strip().lower()
    metric_detail = (
        distributed_canon_detail(work_id, metric)
        if metric in DISTRIBUTED_METRICS
        else None
    )
    hists = book_hists(work_id, params)
    if metric_detail:
        # The live taste-pack curator histogram is a different jury from the
        # fixed research model, so do not imply that it generated this score.
        hists.pop("curators", None)
    return {
        "book": {
            "work_id": row[0],
            "book_id": row[1],
            "title": row[2],
            "author": row[3],
            "book_url": row[4],
            "author_url": row[5],
            "n": int(row[6] or 0),
            "mean": float(row[7]) if row[7] is not None else None,
            "std": float(row[8]) if row[8] is not None else None,
            "stars": {
                "5": int(row[9] or 0),
                "4": int(row[10] or 0),
                "3": int(row[11] or 0),
                "2": int(row[12] or 0),
                "1": int(row[13] or 0),
            },
            "p5": float(row[14]) if row[14] is not None else None,
            "p1": float(row[15]) if row[15] is not None else None,
            "p_low": float(row[16]) if row[16] is not None else None,
            "polarization": float(row[17]) if row[17] is not None else None,
        },
        "histograms": hists,
        "metric_detail": metric_detail,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "CuratorsExplorer/0.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {args[0]}", flush=True)

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _read_json(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _static(self, rel: str) -> None:
        path = (STATIC / rel).resolve()
        if not str(path).startswith(str(STATIC.resolve())) or not path.is_file():
            self._send(404, b"not found", "text/plain")
            return
        data = path.read_bytes()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
        }.get(path.suffix.lower(), "application/octet-stream")
        self._send(200, data, ctype)

    def do_GET(self) -> None:  # noqa: N802
        get_con()
        parsed = urlparse(self.path)
        path = parsed.path
        qs = _qs(parse_qs(parsed.query))

        if path in ("/", "/index.html"):
            self._static("index.html")
            return
        if path in ("/app.js", "/styles.css"):
            self._static(path.lstrip("/"))
            return
        if path.startswith("/static/"):
            self._static(path[len("/static/") :])
            return

        if path == "/api/meta":
            pack = get_active_pack()
            self._json(
                200,
                {
                    "metrics": METRICS,
                    "scale_modes": SCALE_MODES,
                    "globals": GLOBALS,
                    "meta": META,
                    "defaults": pack.get("sliders") or {},
                    "catalog_defaults": pack.get("catalog_defaults") or {},
                    "note": "Python does not hot-reload; restart the server after code changes.",
                },
            )
            return

        if path == "/api/taste":
            self._json(200, pack_payload())
            return

        if path == "/api/authors":
            self._json(
                200,
                {"results": search_authors(str(qs.get("q") or ""), limit=int(qs.get("limit") or 20))},
            )
            return

        if path == "/api/rank":
            t0 = time.time()
            try:
                out = rank_books(qs)
                out["elapsed_ms"] = int((time.time() - t0) * 1000)
                self._json(200, out)
            except Exception as exc:
                self._json(500, {"error": str(exc)})
            return

        if path.startswith("/api/book/"):
            book_id = path[len("/api/book/") :].strip("/")
            self._json(200, book_detail(book_id, qs))
            return

        if path.startswith("/api/hist/"):
            book_id = path[len("/api/hist/") :].strip("/")
            resolved = resolve_work_id(book_id)
            if not resolved:
                self._json(404, {"error": "not found"})
                return
            self._json(200, book_hists(resolved[0], qs))
            return

        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        get_con()
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json()

        if path == "/api/rank":
            t0 = time.time()
            try:
                out = rank_books(body)
                out["elapsed_ms"] = int((time.time() - t0) * 1000)
                self._json(200, out)
            except Exception as exc:
                self._json(500, {"error": str(exc)})
            return

        if path.startswith("/api/book/"):
            book_id = path[len("/api/book/") :].strip("/")
            self._json(200, book_detail(book_id, body))
            return

        if path == "/api/taste":
            action = str(body.get("action") or "get").lower()
            if action == "reset":
                reset_pack()
                self._json(200, pack_payload())
                return
            if action in ("update", "set"):
                update_pack(body)
                self._json(200, pack_payload())
                return
            self._json(200, pack_payload())
            return

        self._send(404, b"not found", "text/plain")


def main() -> None:
    get_con()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Curators explorer → http://{HOST}:{PORT}/", flush=True)
    print("Hard-refresh the browser after UI changes; restart after Python changes.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye", flush=True)


if __name__ == "__main__":
    main()

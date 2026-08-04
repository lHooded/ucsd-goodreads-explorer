#!/usr/bin/env python3
"""Prevalence genre gates (SF, fantasy, coming-of-age, LGBTQ, western).

Each gate scores Goodreads shelves on a work and decides pass/fail via either:

* **ratio** — core(+soft) vs competing genre mass (SF / fantasy), with a soft
  literary penalty that only applies when literary shelving is strong *and*
  the book is popular enough (obscure books keep the pre-literary ratio).
* **theme** — absolute core mass plus a floor vs ``fiction`` so sparse
  cross-tags do not count (coming-of-age / LGBTQ / western).

Gates are stored on ``work_genre_gates`` and can be intersected
(``genre_gates=["sf","fantasy"]`` → science-fantasy).

Run:
  .venv/bin/python -m ucsd_explorer.genre_gates
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from ucsd_explorer.db import EXPLORER_DB, META_PATH, PARQUET

# ---------------------------------------------------------------------------
# Gate definitions
# ---------------------------------------------------------------------------

GATE_DEFS: dict[str, dict[str, Any]] = {
    "sf": {
        "label": "Science fiction",
        "mode": "ratio",
        "core": (
            "science-fiction",
            "hard-sf",
            "hard-science-fiction",
            "space-opera",
            "cyberpunk",
            "military-science-fiction",
            "military-sf",
        ),
        "soft": ("sci-fi", "scifi", "sciencefiction", "sf"),
        "soft_weight": 0.35,
        "compete": (
            # fantasy / adjacent
            "fantasy",
            "high-fantasy",
            "epic-fantasy",
            "urban-fantasy",
            "paranormal",
            "paranormal-romance",
            "magic",
            "discworld",
            "comic-fantasy",
            # romance / YA / horror
            "romance",
            "contemporary-romance",
            "young-adult",
            "ya",
            "teen",
            "horror",
            "vampires",
            # humor / faith shelves that pick up sparse SF tags (Discworld, Left Behind)
            "humor",
            "humour",
            "comedy",
            "christian",
            "christian-fiction",
            "religion",
            "religious",
        ),
        "literary": (
            "classics",
            "classic",
            "literature",
            "literary-fiction",
            "literary",
            "classic-literature",
            "magical-realism",
        ),
        "literary_weight": 0.5,
        # Soft literary: popular books always get the half-weight literary
        # denom (keeps Dan Brown / Kafka out). Obscure books skip it so a
        # few classic shelves do not wipe sparse-but-real SF.
        "literary_min_n": 250,
        "literary_always_if_popular": True,
        "literary_vs_sf": 1.5,
        "literary_floor": 80,
        "min_core": 10,
        "min_core_obscure": 10,
        "obscure_n": 200,
        "min_ratio": 0.55,
        # Science-fantasy escapes (New Sun / some Bas-Lag) — high abs core
        "escape_abs_core": 800,
        "escape_ratio": 0.27,
        "escape_soft_core": 80,
        "escape_soft_ratio": 0.35,
        # Block YA-primary dystopia from SF escapes (Hunger Games etc.)
        "escape_require_ya_lt_core": True,
        "escape_soft_max_ya": 50,
    },
    "fantasy": {
        "label": "Fantasy",
        "mode": "ratio",
        "core": (
            "fantasy",
            "high-fantasy",
            "epic-fantasy",
            "urban-fantasy",
        ),
        "soft": ("magic", "magical", "paranormal", "dark-fantasy", "fantasy-sci-fi", "sci-fi-fantasy"),
        "soft_weight": 0.35,
        # YA is *not* a hard competitor: much fantasy is YA (Earthsea, Sabriel).
        # Soft-weight so YA-only dystopias still lose to YA mass, without
        # killing classics that pick up school/YA shelves on volume 1.
        "compete": (
            "science-fiction",
            "sci-fi",
            "scifi",
            "sf",
            "cyberpunk",
            "romance",
            "contemporary-romance",
            "mystery",
            "thriller",
            "horror",
        ),
        "compete_soft": ("young-adult", "ya", "teen"),
        "compete_soft_weight": 0.25,
        "literary": (
            "classics",
            "classic",
            "literature",
            "literary-fiction",
            "magical-realism",
        ),
        "literary_weight": 0.35,
        "literary_min_n": 250,
        "literary_always_if_popular": True,
        "literary_vs_sf": 1.5,
        "literary_floor": 80,
        "min_core": 15,
        "min_core_obscure": 15,
        "obscure_n": 200,
        "min_ratio": 0.50,
        "escape_abs_core": 200,
        "escape_ratio": 0.30,
        "escape_soft_core": 40,
        "escape_soft_ratio": 0.35,
        "escape_require_ya_lt_core": False,
        "escape_soft_max_ya": None,
    },
    "coming_of_age": {
        "label": "Coming of age",
        "mode": "theme",
        "core": ("coming-of-age", "bildungsroman"),
        "soft": ("ya-coming-of-age", "growing-up"),
        "soft_weight": 0.5,
        "min_core": 40,
        "min_core_obscure": 15,
        "obscure_n": 200,
        # vs fiction: Catcher ~0.085, Mockingbird ~0.78, Perks ~0.23
        "min_vs_fiction": 0.06,
        "min_vs_fiction_obscure": 0.04,
    },
    "lgbtq": {
        "label": "LGBTQ / identity",
        "mode": "theme",
        "core": (
            "lgbt",
            "lgbtq",
            "lgbtqia",
            "queer",
            "gay",
            "lesbian",
            "bisexual",
            "transgender",
            "glbt",
        ),
        "soft": (
            "gay-fiction",
            "lesbian-fiction",
            "queer-lit",
            "lgbtqa",
            "mm-romance",
            "m-m",
        ),
        "soft_weight": 0.45,
        "min_core": 25,
        "min_core_obscure": 10,
        "obscure_n": 200,
        # Giovanni ~0.46+, CMBYN >1, Orlando ~0.19
        "min_vs_fiction": 0.08,
        "min_vs_fiction_obscure": 0.05,
    },
    "western": {
        "label": "Western",
        "mode": "theme",
        "core": ("western", "westerns", "wild-west"),
        "soft": ("cowboy", "cowboys"),
        "soft_weight": 0.4,
        # Keep romance-westerns from dominating pure western lists via fiction floor
        "min_core": 30,
        "min_core_obscure": 12,
        "obscure_n": 200,
        # Lonesome Dove ~0.98, Blood Meridian ~0.32, Sisters Brothers ~0.37
        "min_vs_fiction": 0.12,
        "min_vs_fiction_obscure": 0.08,
    },
}

GATE_IDS = tuple(GATE_DEFS.keys())


def has_genre_gates() -> bool:
    from ucsd_explorer.db import get_con

    try:
        tables = {r[0] for r in get_con().execute("SHOW TABLES").fetchall()}
        return "work_genre_gates" in tables
    except Exception:
        return False


_GATE_ALIASES = {
    "science_fiction": "sf",
    "sci_fi": "sf",
    "coa": "coming_of_age",
    "comingofage": "coming_of_age",
    "lgbt": "lgbtq",
    "lgbtqia": "lgbtq",
    "queer": "lgbtq",
    "identity": "lgbtq",
}


def parse_genre_gates(params: dict[str, Any]) -> list[str]:
    """Parse active prevalence gates (AND / intersection).

    Empty / missing ``genre_gates`` falls back to the legacy SF include-tag
    preset → ``["sf"]`` so older clients keep SF-scoped rankings.
    Explicit ``genre_gates=[]`` / ``genre_gates=`` means no prevalence gate.
    """
    explicit = "genre_gates" in params or "gates" in params
    raw = params.get("genre_gates", params.get("gates"))

    if raw is None or raw == "":
        if explicit:
            return []
        # Legacy: SF any-of include tags or default sf_only → sf gate
        from ucsd_explorer.genres import SF_PRESET_INCLUDE, parse_genre_params

        g = parse_genre_params(params)
        inc = set(g.get("include") or [])
        if inc and inc <= set(SF_PRESET_INCLUDE):
            return ["sf"]
        return []

    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("["):
            try:
                raw = json.loads(s)
            except json.JSONDecodeError:
                raw = [x.strip() for x in s.split(",") if x.strip()]
        elif not s:
            return []
        else:
            raw = [x.strip() for x in s.split(",") if x.strip()]
    if not isinstance(raw, (list, tuple)):
        raw = [raw]

    out: list[str] = []
    seen: set[str] = set()
    for x in raw:
        gid = str(x).strip().lower().replace("-", "_").replace(" ", "_")
        gid = _GATE_ALIASES.get(gid, gid)
        if gid not in GATE_DEFS or gid in seen:
            continue
        seen.add(gid)
        out.append(gid)
    return out


def gate_sql_bits(
    gates: list[str] | None,
    *,
    work_alias: str = "w",
) -> tuple[str, list[Any]]:
    """AND of prevalence gates (intersection)."""
    if not gates:
        return "", []
    if not has_genre_gates():
        # Fall back: SF only via is_sf
        if gates == ["sf"]:
            return f" AND coalesce({work_alias}.is_sf, FALSE)", []
        return "", []
    parts = []
    args: list[Any] = []
    for gid in gates:
        parts.append(
            f""" EXISTS (
              SELECT 1 FROM work_genre_gates gg
              WHERE gg.work_id = {work_alias}.work_id
                AND gg.gate = ?
                AND gg.passed
            )"""
        )
        args.append(gid)
    return " AND " + " AND ".join(parts), args


def _sum_shelves(shelf_counts: dict[str, int], names: tuple[str, ...] | list[str]) -> float:
    return float(sum(shelf_counts.get(s, 0) for s in names))


def score_gate(gate_id: str, shelf_counts: dict[str, int], *, n_ratings: int) -> dict[str, Any]:
    """Evaluate one gate for a work. Returns dict with passed/score/ratio."""
    g = GATE_DEFS[gate_id]
    core = _sum_shelves(shelf_counts, g["core"])
    soft = _sum_shelves(shelf_counts, g.get("soft") or ())
    score = core + float(g.get("soft_weight", 0.35)) * soft
    fiction = float(shelf_counts.get("fiction", 0))
    obscure = n_ratings < int(g.get("obscure_n", 200))
    min_core = float(g["min_core_obscure"] if obscure else g["min_core"])

    if g["mode"] == "theme":
        vs = float(g["min_vs_fiction_obscure"] if obscure else g["min_vs_fiction"])
        # Avoid div0: require absolute core and relative to fiction when fiction exists
        if fiction > 0:
            ratio = score / fiction
        else:
            ratio = 1.0 if score >= min_core else 0.0
        passed = score >= min_core and ratio >= vs
        return {
            "gate": gate_id,
            "passed": bool(passed),
            "score": round(score, 2),
            "ratio": round(ratio, 4) if ratio is not None else None,
            "core": core,
            "mode": "theme",
        }

    # ratio mode
    compete = _sum_shelves(shelf_counts, g.get("compete") or ())
    compete += float(g.get("compete_soft_weight", 0.0)) * _sum_shelves(
        shelf_counts, g.get("compete_soft") or ()
    )
    literary = _sum_shelves(shelf_counts, g.get("literary") or ())
    lit_w = float(g.get("literary_weight", 0.5))
    if g.get("literary_always_if_popular", False):
        apply_lit = n_ratings >= int(g.get("literary_min_n", 250))
    else:
        apply_lit = (
            n_ratings >= int(g.get("literary_min_n", 250))
            and literary
            >= max(float(g.get("literary_floor", 80)), float(g.get("literary_vs_sf", 1.5)) * score)
        )
    denom = score + compete + (lit_w * literary if apply_lit else 0.0)
    ratio = (score / denom) if denom > 0 else None
    min_ratio = float(g["min_ratio"])
    ya = _sum_shelves(shelf_counts, ("young-adult", "ya", "teen"))
    passed = False
    if score >= min_core and ratio is not None:
        if ratio >= min_ratio:
            passed = True
        elif core >= float(g.get("escape_abs_core", 1e9)) and ratio >= float(
            g.get("escape_ratio", 1.0)
        ):
            if g.get("escape_require_ya_lt_core"):
                if ya < core:
                    passed = True
            else:
                passed = True
        elif (
            core >= float(g.get("escape_soft_core", 1e9))
            and ratio >= float(g.get("escape_soft_ratio", 1.0))
            and compete > 0
        ):
            max_ya = g.get("escape_soft_max_ya")
            if max_ya is None or ya < float(max_ya):
                passed = True
    # Obscure: allow slightly lower core if ratio is strong
    if not passed and obscure and core >= min_core and ratio is not None and ratio >= min_ratio:
        passed = True

    return {
        "gate": gate_id,
        "passed": bool(passed),
        "score": round(score, 2),
        "ratio": round(ratio, 4) if ratio is not None else None,
        "core": core,
        "apply_lit": apply_lit,
        "mode": "ratio",
    }


def _sql_str_list(names: tuple[str, ...] | list[str] | set[str]) -> str:
    return ", ".join("'" + str(s).replace("'", "''") + "'" for s in names)


def _sql_shelf_sum(shelves: tuple[str, ...] | list[str] | set[str]) -> str:
    if not shelves:
        return "0::DOUBLE"
    return (
        f"sum(CASE WHEN shelf IN ({_sql_str_list(shelves)}) "
        f"THEN count ELSE 0 END)::DOUBLE"
    )


def _ratio_gate_select_sql(gid: str, g: dict[str, Any]) -> str:
    """One SELECT arm for a ratio-mode gate over ``_gate_pivot``."""
    soft_w = float(g.get("soft_weight", 0.35))
    lit_w = float(g.get("literary_weight", 0.5))
    lit_min_n = int(g.get("literary_min_n", 250))
    lit_vs = float(g.get("literary_vs_sf", 1.5))
    lit_floor = float(g.get("literary_floor", 80))
    always_pop = bool(g.get("literary_always_if_popular", False))
    min_core = float(g["min_core"])
    min_core_obscure = float(g.get("min_core_obscure", min_core))
    obscure_n = int(g.get("obscure_n", 200))
    min_ratio = float(g["min_ratio"])
    esc_abs = float(g.get("escape_abs_core", 1e9))
    esc_ratio = float(g.get("escape_ratio", 1.0))
    esc_soft = float(g.get("escape_soft_core", 1e9))
    esc_soft_ratio = float(g.get("escape_soft_ratio", 1.0))
    ya_lt_core = bool(g.get("escape_require_ya_lt_core", False))
    soft_max_ya = g.get("escape_soft_max_ya")
    csw = float(g.get("compete_soft_weight", 0.0))
    c, s, k, lit = f"{gid}_core", f"{gid}_soft", f"{gid}_compete", f"{gid}_literary"
    ks = f"{gid}_compete_soft"
    compete_expr = f"({k} + {csw} * {ks})" if csw else k
    if always_pop:
        lit_case = f"""
                    CASE
                        WHEN n >= {lit_min_n} THEN {lit_w} * {lit}
                        ELSE 0
                    END"""
    else:
        lit_case = f"""
                    CASE
                        WHEN n >= {lit_min_n}
                         AND {lit} >= greatest({lit_floor}, {lit_vs} * ({c} + {soft_w} * {s}))
                        THEN {lit_w} * {lit}
                        ELSE 0
                    END"""
    abs_ya = f"AND ya < core" if ya_lt_core else ""
    if soft_max_ya is None:
        soft_ya = ""
    else:
        soft_ya = f"AND ya < {float(soft_max_ya)}"
    return f"""
        SELECT
            work_id,
            '{gid}' AS gate,
            TRUE AS passed,
            round(score, 2) AS score,
            round(ratio, 4) AS ratio
        FROM (
            SELECT
                work_id,
                {c} AS core,
                ({c} + {soft_w} * {s}) AS score,
                {compete_expr} AS compete,
                ya,
                {lit_case} AS lit_pen,
                CASE
                    WHEN n < {obscure_n} THEN {min_core_obscure}
                    ELSE {min_core}
                END AS min_core_eff,
                CASE
                    WHEN ({c} + {soft_w} * {s} + {compete_expr} + ({lit_case})) > 0
                    THEN ({c} + {soft_w} * {s})
                         / ({c} + {soft_w} * {s} + {compete_expr} + ({lit_case}))
                    ELSE NULL
                END AS ratio
            FROM _gate_pivot
        ) t
        WHERE score >= min_core_eff
          AND ratio IS NOT NULL
          AND (
            ratio >= {min_ratio}
            OR (
              core >= {esc_abs}
              AND ratio >= {esc_ratio}
              {abs_ya}
            )
            OR (
              core >= {esc_soft}
              AND ratio >= {esc_soft_ratio}
              AND compete > 0
              {soft_ya}
            )
          )
    """


def _theme_gate_select_sql(gid: str, g: dict[str, Any]) -> str:
    soft_w = float(g.get("soft_weight", 0.5))
    min_core = float(g["min_core"])
    min_core_obscure = float(g.get("min_core_obscure", min_core))
    obscure_n = int(g.get("obscure_n", 200))
    min_vs = float(g["min_vs_fiction"])
    min_vs_obscure = float(g.get("min_vs_fiction_obscure", min_vs))
    c, s = f"{gid}_core", f"{gid}_soft"
    return f"""
        SELECT
            work_id,
            '{gid}' AS gate,
            TRUE AS passed,
            round(score, 2) AS score,
            round(ratio, 4) AS ratio
        FROM (
            SELECT
                work_id,
                ({c} + {soft_w} * {s}) AS score,
                CASE
                    WHEN n < {obscure_n} THEN {min_core_obscure}
                    ELSE {min_core}
                END AS min_core_eff,
                CASE
                    WHEN n < {obscure_n} THEN {min_vs_obscure}
                    ELSE {min_vs}
                END AS min_vs_eff,
                CASE
                    WHEN fiction > 0 THEN ({c} + {soft_w} * {s}) / fiction
                    WHEN ({c} + {soft_w} * {s}) >= CASE
                        WHEN n < {obscure_n} THEN {min_core_obscure}
                        ELSE {min_core}
                    END THEN 1.0
                    ELSE 0.0
                END AS ratio
            FROM _gate_pivot
        ) t
        WHERE score >= min_core_eff AND ratio >= min_vs_eff
    """


def _inherit_series_gates(con) -> int:
    """Promote early volumes when later volumes clearly pass a ratio gate.

    Famous first books (Earthsea #1, Oz #1) often pick up school/YA/classic
    shelves that sequels avoid. If ≥2 later volumes pass and the candidate
    has real core shelf mass, inherit the gate.
    """
    import re

    # Only inherit for ratio genres where series coherence is meaningful
    inherit_gates = ("fantasy", "sf", "western")
    pat = re.compile(r"^(.*?)\s*\(([^)]+),\s*#(\d+(?:\.\d+)?)\)\s*$")
    rows = con.execute(
        """
        SELECT w.work_id, w.title, w.author, w.n,
               g.gate,
               EXISTS(
                 SELECT 1 FROM work_genre_gates x
                 WHERE x.work_id = w.work_id AND x.gate = g.gate AND x.passed
               ) AS passed
        FROM work_scores w
        CROSS JOIN (SELECT UNNEST(?::VARCHAR[]) AS gate) g
        WHERE w.n >= 200 AND w.title LIKE '%#%'
        """,
        [list(inherit_gates)],
    ).fetchall()

    from collections import defaultdict

    by_series: dict[tuple, list] = defaultdict(list)
    for wid, title, author, n, gate, passed in rows:
        m = pat.match(title or "")
        if not m:
            continue
        key = ((author or "").strip().lower(), m.group(2).strip().lower(), gate)
        by_series[key].append(
            {
                "work_id": str(wid),
                "num": float(m.group(3)),
                "n": int(n),
                "passed": bool(passed),
                "title": title,
            }
        )

    inserts: list[tuple] = []
    for (_author, _sname, gate), vols in by_series.items():
        if len(vols) < 2:
            continue
        vols = sorted(vols, key=lambda v: v["num"])
        later_pass = [v for v in vols if v["num"] >= 2.0 and v["passed"]]
        if len(later_pass) < 2:
            continue
        gdef = GATE_DEFS[gate]
        min_core = float(gdef.get("min_core", 15))
        for v in vols:
            if v["passed"] or v["num"] >= 2.0:
                continue
            # Require some core mass so we don't inherit onto unrelated #0.5 shorts
            core = con.execute(
                f"""
                SELECT {_sql_shelf_sum(gdef.get("core") or ())}
                FROM work_genres WHERE work_id = ?
                """,
                [v["work_id"]],
            ).fetchone()[0]
            if float(core or 0) < min_core:
                continue
            # Score/ratio placeholders — marked as inherited
            inserts.append((v["work_id"], gate, True, float(core or 0), None))

    if not inserts:
        print("  series inherit: 0", flush=True)
        return 0

    # Dedupe
    seen: set[tuple[str, str]] = set()
    uniq: list[tuple] = []
    for row in inserts:
        k = (row[0], row[1])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(row)

    con.executemany(
        "INSERT INTO work_genre_gates VALUES (?, ?, ?, ?, ?)",
        uniq,
    )
    print(f"  series inherit: {len(uniq):,} volume promotions", flush=True)
    return len(uniq)


def materialize_genre_gates(*, db_path: Path | None = None) -> dict[str, Any]:
    """Build work_genre_gates via SQL pivot + CTAS (fast; passed rows only)."""
    import duckdb

    db_path = db_path or EXPLORER_DB
    if not db_path.exists():
        raise SystemExit(f"Missing {db_path}")

    t0 = time.time()
    con = duckdb.connect(str(db_path))
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "work_genres" not in tables:
        raise SystemExit("work_genres missing — run: python -m ucsd_explorer.genres")

    needed: set[str] = {"fiction", "young-adult", "ya", "teen"}
    agg_exprs: list[str] = []
    col_names: list[str] = []
    for gid, g in GATE_DEFS.items():
        core = tuple(g.get("core") or ())
        soft = tuple(g.get("soft") or ())
        needed.update(core)
        needed.update(soft)
        for suffix, shelves in (
            ("core", core),
            ("soft", soft),
        ):
            name = f"{gid}_{suffix}"
            agg_exprs.append(f"{_sql_shelf_sum(shelves)} AS {name}")
            col_names.append(name)
        if g["mode"] == "ratio":
            compete = tuple(g.get("compete") or ())
            compete_soft = tuple(g.get("compete_soft") or ())
            literary = tuple(g.get("literary") or ())
            needed.update(compete)
            needed.update(compete_soft)
            needed.update(literary)
            for suffix, shelves in (
                ("compete", compete),
                ("compete_soft", compete_soft),
                ("literary", literary),
            ):
                name = f"{gid}_{suffix}"
                agg_exprs.append(f"{_sql_shelf_sum(shelves)} AS {name}")
                col_names.append(name)
    for name, shelves in (
        ("fiction", ("fiction",)),
        ("ya", ("young-adult", "ya", "teen")),
    ):
        agg_exprs.append(f"{_sql_shelf_sum(shelves)} AS {name}")
        col_names.append(name)

    coalesce_cols = ", ".join(
        f"coalesce(x.{c}, 0) AS {c}" for c in col_names
    )

    print("Genre gates: SQL pivot…", flush=True)
    con.execute("DROP TABLE IF EXISTS _gate_pivot")
    con.execute(
        f"""
        CREATE TEMP TABLE _gate_pivot AS
        SELECT
            ws.work_id,
            ws.n::BIGINT AS n,
            {coalesce_cols}
        FROM work_scores ws
        LEFT JOIN (
            SELECT
                work_id,
                {", ".join(agg_exprs)}
            FROM work_genres
            WHERE shelf IN ({_sql_str_list(needed)})
            GROUP BY work_id
        ) x USING (work_id)
        """
    )
    n_works = con.execute("SELECT count(*) FROM _gate_pivot").fetchone()[0]
    print(f"  pivoted {n_works:,} works · scoring gates in SQL…", flush=True)

    arms: list[str] = []
    for gid, g in GATE_DEFS.items():
        if g["mode"] == "ratio":
            arms.append(_ratio_gate_select_sql(gid, g))
        else:
            arms.append(_theme_gate_select_sql(gid, g))

    con.execute("DROP TABLE IF EXISTS work_genre_gates")
    con.execute(
        f"""
        CREATE TABLE work_genre_gates AS
        {" UNION ALL ".join(arms)}
        """
    )
    n_inherited = _inherit_series_gates(con)
    con.execute("CREATE INDEX idx_wgg_work ON work_genre_gates(work_id)")
    con.execute("CREATE INDEX idx_wgg_gate ON work_genre_gates(gate, passed)")
    con.execute(
        "CREATE INDEX idx_wgg_work_gate ON work_genre_gates(work_id, gate, passed)"
    )

    pass_counts = {
        gid: int(
            con.execute(
                "SELECT count(*) FROM work_genre_gates WHERE gate = ?", [gid]
            ).fetchone()[0]
        )
        for gid in GATE_IDS
    }
    n_rows = int(con.execute("SELECT count(*) FROM work_genre_gates").fetchone()[0])

    # Sync work_scores.is_sf only (skip rewriting multi-GB event tables —
    # ranking uses work_genre_gates / work_scores; event is_sf is legacy).
    if "work_scores" in tables:
        print("  syncing work_scores.is_sf from sf gate…", flush=True)
        con.execute("DROP TABLE IF EXISTS _ws_sf_sync")
        con.execute(
            """
            CREATE TABLE _ws_sf_sync AS
            SELECT w.* EXCLUDE (is_sf),
                   (s.work_id IS NOT NULL) AS is_sf
            FROM work_scores w
            LEFT JOIN (
                SELECT DISTINCT work_id FROM work_genre_gates
                WHERE gate = 'sf' AND passed
            ) s USING (work_id)
            """
        )
        con.execute("DROP TABLE work_scores")
        con.execute("ALTER TABLE _ws_sf_sync RENAME TO work_scores")
        con.execute("CREATE INDEX IF NOT EXISTS idx_ws_sf ON work_scores(is_sf)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_ws_n ON work_scores(n)")

    con.execute("DROP TABLE IF EXISTS _gate_pivot")
    stats = {
        "n_rows": n_rows,
        "n_works": int(n_works),
        "n_series_inherited": n_inherited,
        "passed": pass_counts,
        "gates": {gid: GATE_DEFS[gid]["label"] for gid in GATE_IDS},
        "elapsed_s": round(time.time() - t0, 1),
        "built_at": time.time(),
        "store": "passed_only",
    }
    print(
        "work_genre_gates: "
        + ", ".join(f"{k}={v:,}" for k, v in pass_counts.items())
        + f" in {stats['elapsed_s']}s",
        flush=True,
    )
    con.close()
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        meta["genre_gates"] = stats
        meta["genre_gates_available"] = True
        META_PATH.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return stats


def validate_gates() -> None:
    """Print pass/fail for known anchors."""
    from ucsd_explorer.db import get_con

    con = get_con()
    anchors = [
        ("sf", "The Left Hand of Darkness", True),
        ("sf", "The Shadow of the Torturer%", True),
        ("sf", "The Last Question", True),
        ("sf", "Neuromancer%", True),
        ("sf", "The Trial", False),
        ("sf", "Infinite Jest", False),
        ("sf", "The Wind-Up Bird Chronicle", False),
        ("fantasy", "The Name of the Wind%", True),
        ("fantasy", "The Hobbit%", True),
        ("fantasy", "A Wizard of Earthsea%", True),
        ("fantasy", "Sabriel%", True),
        ("fantasy", "The Wonderful Wizard of Oz%", True),
        ("fantasy", "Neuromancer%", False),
        ("fantasy", "The Martian", False),
        ("fantasy", "The Hunger Games%", False),
        ("fantasy", "1984", False),
        ("coming_of_age", "The Catcher in the Rye", True),
        ("coming_of_age", "The Perks of Being a Wallflower", True),
        ("coming_of_age", "To Kill a Mockingbird", True),
        ("coming_of_age", "Pride and Prejudice", False),
        ("lgbtq", "Giovanni's Room", True),
        ("lgbtq", "Call Me by Your Name", True),
        ("lgbtq", "The Hobbit%", False),
        ("western", "Lonesome Dove", True),
        ("western", "Blood Meridian%", True),
        ("western", "True Grit", True),
        ("western", "Gone Girl", False),
    ]
    print("Gate validation:")
    for gate, title, expect in anchors:
        row = con.execute(
            """
            SELECT w.title, g.passed, g.score, g.ratio
            FROM work_scores w
            LEFT JOIN work_genre_gates g
              ON g.work_id = w.work_id AND g.gate = ?
            WHERE w.title ILIKE ?
            ORDER BY w.n DESC LIMIT 1
            """,
            [gate, title],
        ).fetchone()
        if not row:
            print(f"  MISS {gate} {title}")
            continue
        ok = bool(row[1]) == expect
        mark = "OK" if ok else "FAIL"
        print(
            f"  {mark}: {gate:15s} expect={expect} got={row[1]} "
            f"score={row[2]} ratio={row[3]} | {row[0][:45]}"
        )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--validate", action="store_true")
    args = p.parse_args()
    materialize_genre_gates()
    if args.validate:
        validate_gates()


if __name__ == "__main__":
    main()

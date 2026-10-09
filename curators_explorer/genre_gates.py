"""Named genre prevalence gates for the curators explorer.

The first five definitions are copied from the UCSD explorer and continue to
use its materialized ``work_genre_gates`` rows when those rows are present.
The additional gates are evaluated from Goodreads shelf mass at query time.
That keeps the curators app usable with the existing shared warehouse while
also covering legitimate low-volume shelves which the original materializer
did not retain.

``score_gate`` and ``validate_gates`` intentionally mirror the UCSD assertion
style: genre policy is data-driven, and known books are only validation
anchors, never classification exceptions.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from curators_explorer.db import execute, table_names

try:
    # Keep the already-tuned UCSD definitions byte-for-byte in spirit, while
    # adding the curators-only gates below.  The curators app still owns all
    # query/materialization behavior in this module.
    from ucsd_explorer.genre_gates import GATE_DEFS as _UCSD_GATE_DEFS
except Exception:  # pragma: no cover - only relevant to a partial checkout
    _UCSD_GATE_DEFS = {}


GATE_DEFS: dict[str, dict[str, Any]] = {
    key: dict(value) for key, value in _UCSD_GATE_DEFS.items()
}


# ``mode=theme`` is deliberately permissive unless marked strict.  The
# fiction floor prevents one stray shelf from making a huge unrelated book a
# genre match, while the low floors retain literary works whose Goodreads
# shelving is sparse.  Strict gates use higher absolute and relative floors.
GATE_DEFS.update(
    {
        "children": {
            "label": "Children's",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "children",
                "childrens",
                "children-s",
                "children-books",
                "childrens-books",
                "children-s-books",
                "children-s-literature",
                "childrens-literature",
                "children-s-lit",
                "childrens-lit",
                "children-s-fiction",
                "childrens-fiction",
                "juvenile",
                "juvenile-fiction",
                "kid-lit",
            ),
            "soft": (
                "childhood",
                "childhood-books",
                "children-young-adult",
                "children-ya",
                "childrens-classics",
                "children-s-classics",
                "kids",
                "child",
            ),
            "soft_weight": 0.2,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.005,
            "min_vs_fiction_obscure": 0.002,
        },
        "religion": {
            "label": "Religion / spirituality",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "religion",
                "religious",
                "religious-fiction",
                "religious-studies",
                "religion-spirituality",
                "religion-and-spirituality",
                "christian",
                "christianity",
                "christian-fiction",
                "theology",
                "faith",
                "spirituality",
                "spiritual",
                "spiritual-growth",
                "spiritual-formation",
            ),
            "soft": ("philosophy-religion", "religion-philosophy"),
            "soft_weight": 0.5,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.005,
            "min_vs_fiction_obscure": 0.002,
        },
        "philosophy": {
            "label": "Philosophy",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "philosophy",
                "philosophical",
                "philosophie",
                "existentialism",
                "existential",
                "philosophy-religion",
                "religion-philosophy",
                "political-philosophy",
                "eastern-philosophy",
                "ethics",
                "metaphysics",
                "ontology",
                "absurdism",
                "philosophical-fiction",
            ),
            "soft": ("philosophy-psychology", "psychology-philosophy"),
            "soft_weight": 0.45,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.005,
            "min_vs_fiction_obscure": 0.002,
        },
        "magical_realism": {
            "label": "Magical realism",
            "mode": "theme",
            "strictness": "loose",
            "core": ("magical-realism", "magic-realism"),
            "soft": ("magical", "surrealism", "surreal"),
            "soft_weight": 0.25,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.003,
            "min_vs_fiction_obscure": 0.001,
        },
        "weird": {
            "label": "Weird fiction",
            "mode": "theme",
            "strictness": "strict",
            "core": ("weird", "weird-fiction", "new-weird"),
            "soft": (
                "surrealism",
                "surreal",
                "slipstream",
                "bizarro-fiction",
                "experimental-fiction",
            ),
            "soft_weight": 0.2,
            "require_core": True,
            "min_core": 15,
            "min_core_obscure": 5,
            "obscure_n": 400,
            "min_vs_fiction": 0.01,
            "min_vs_fiction_obscure": 0.005,
        },
        "satire": {
            "label": "Satire",
            "mode": "theme",
            "strictness": "strict",
            "core": ("satire", "satirical", "satire-fiction"),
            "soft": ("political-satire", "social-satire"),
            "soft_weight": 0.25,
            "require_core": True,
            "min_core": 15,
            "min_core_obscure": 5,
            "obscure_n": 400,
            "min_vs_fiction": 0.014,
            "min_vs_fiction_obscure": 0.008,
        },
        "dystopian": {
            "label": "Dystopian",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "dystopian",
                "dystopia",
                "dystopian-fiction",
                "dystopias",
                "dystopia-utopia",
                "utopia-dystopia",
                "dystopian-post-apocalyptic",
                "ya-dystopian",
                "ya-dystopia",
            ),
            "soft": ("post-apocalyptic", "post-apocalypse"),
            "soft_weight": 0.25,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.005,
            "min_vs_fiction_obscure": 0.002,
        },
        "short_story": {
            "label": "Short story",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "short-stories",
                "short-story",
                "short-fiction",
                "short-story-collections",
                "short-story-collection",
                "shortstories",
                "short-stories-essays",
                "short-stories-novellas",
                "shorts",
            ),
            "soft": ("short",),
            "soft_weight": 0.2,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.005,
            "min_vs_fiction_obscure": 0.002,
        },
        "comedy": {
            "label": "Comedy / humor",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "comedy",
                "comedies",
                "comedic",
                "humor",
                "humour",
                "humorous",
                "romantic-comedy",
                "dark-humor",
            ),
            "soft": ("fantasy-humor", "fantasy-humour"),
            "soft_weight": 0.2,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.003,
            "min_vs_fiction_obscure": 0.001,
        },
        "low_fantasy": {
            "label": "Low fantasy",
            "mode": "tag",
            "strictness": "loose",
            "core": (
                "low-fantasy",
                "low-fantasy-fiction",
                "grounded-fantasy",
                "gritty-fantasy",
                "modern-fantasy",
                "contemporary-fantasy",
                "urban-fantasy",
                "dark-fantasy",
                "historical-fantasy",
                "fantasy-of-manners",
                "flintlock-fantasy",
                "grimdark-fantasy",
            ),
            "soft": (),
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
        },
        "poetry": {
            "label": "Poetry",
            "mode": "tag",
            "strictness": "loose",
            "core": (
                "poetry",
                "poems",
                "poetry-and-plays",
                "poetry-plays",
                "verse",
                "novels-in-verse",
                "novel-in-verse",
            ),
            "soft": (),
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
        },
        "graphic_novel": {
            "label": "Graphic novel",
            "mode": "tag",
            "strictness": "loose",
            "core": (
                "graphic-novels",
                "graphic-novel",
                "graphicnovels",
                "graphicnovel",
                "graphic",
                "comics-graphic-novels",
                "graphic-novels-comics",
                "comics-and-graphic-novels",
                "graphic-novels-and-comics",
                "comic-graphic-novel",
                "graphic-novel-comic",
                "graphic-novel-comics",
                "manga-graphic-novels",
                "graphic-novels-manga",
                "comics",
                "comic",
                "comic-books",
                "comic-book",
                "manga",
            ),
            "soft": (),
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
        },
        "horror": {
            "label": "Horror",
            "mode": "theme",
            "strictness": "strict",
            "core": (
                "horror",
                "gothic-horror",
                "horror-thriller",
                "horror-suspense",
                "thriller-horror",
                "mystery-thriller-horror",
                "fiction-horror",
                "horror-fiction",
                "horror-supernatural",
                "psychological-horror",
                "psychological-horror-thrillers",
            ),
            "soft": ("dark-fantasy", "fantasy-horror", "horror-fantasy"),
            "soft_weight": 0.15,
            "require_core": True,
            "compete": (
                "fantasy",
                "science-fiction",
                "sci-fi",
                "young-adult",
                "ya",
                "teen",
                "romance",
                "paranormal",
                "thriller",
                "mystery",
            ),
            "ratio_include_compete": True,
            "require_fiction": True,
            "min_core": 20,
            "min_core_obscure": 5,
            "obscure_n": 400,
            "min_vs_fiction": 0.08,
            "min_vs_fiction_obscure": 0.04,
        },
        "apocalyptic": {
            "label": "Apocalyptic / post-apocalyptic",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "post-apocalyptic",
                "apocalyptic",
                "apocalypse",
                "post-apocalypse",
                "dystopian-post-apocalyptic",
                "apocalyptic-fiction",
                "end-of-the-world",
                "end-of-world",
                "world-ending",
                "nuclear-apocalypse",
                "zombie-apocalypse",
            ),
            "soft": ("dystopian", "dystopia"),
            "soft_weight": 0.15,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.005,
            "min_vs_fiction_obscure": 0.002,
        },
        "hard_sf": {
            "label": "Hard science fiction",
            "mode": "tag",
            "strictness": "loose",
            "core": (
                "hard-sci-fi",
                "hard-sf",
                "hard-science-fiction",
                "hard-scifi",
                "hard-science",
                "science-hard",
            ),
            "soft": (),
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
        },
        "psychology": {
            "label": "Psychological depth",
            "mode": "theme",
            "strictness": "loose",
            "core": (
                "psychology",
                "psychological",
                "psychological-fiction",
                "psychological-novel",
                "psychological-thriller",
                "psychological-thrillers",
                "psychological-suspense",
                "psychological-mystery",
                "psychological-drama",
                "psychology-sociology",
                "psychoanalysis",
                "depth-psychology",
                "mental-health",
                "mental-illness",
                "character-study",
                "character-studies",
                "character-driven",
                "character-development",
                "well-developed-characters",
                "introspective",
                "introspection",
                "interior-monologue",
                "trauma",
                "human-nature",
                "psyche",
                "philosophy-psychology",
                "psychology-philosophy",
            ),
            "soft": ("existentialism", "philosophy", "philosophical", "human-condition"),
            "soft_weight": 0.15,
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
            "min_vs_fiction": 0.003,
            "min_vs_fiction_obscure": 0.001,
        },
        "road_novel": {
            "label": "Road novel",
            "mode": "tag",
            "strictness": "loose",
            "core": (
                "road-trip",
                "roadtrip",
                "road-trips",
                "on-the-road",
                "road-novel",
                "road-novels",
                "road-narratives",
                "road-travel",
                "travel-adventure",
            ),
            "soft": (),
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
        },
        "slice_of_life": {
            "label": "Slice of life",
            "mode": "tag",
            "strictness": "loose",
            "core": (
                "slice-of-life",
                "slice-o-life",
                "sliceoflife",
                "slices-of-life",
                "slice-of-life-novels",
                "realistic-slice-of-life",
                "contemporary-slice-of-life",
                "manga-slice-of-life",
                "slice-of-life-manga",
                "manga-sliceoflife",
                "sliceoflife",
            ),
            "soft": (),
            "min_core": 5,
            "min_core_obscure": 3,
            "obscure_n": 400,
        },
        "ya": {
            "label": "Young adult (YA)",
            "mode": "theme",
            "strictness": "strict",
            # Generic young-adult / ya shelves are noisy on classics and
            # children's books.  The explicit fiction/literature shelves form
            # the strict core; generic labels provide only a small lift.
            "core": (
                "young-adult-fiction",
                "ya-fiction",
                "young-adult-lit",
                "ya-lit",
                "young-adult-literature",
                "teen-fiction",
                "ya-books",
                "young-adult-books",
            ),
            "soft": (
                "young-adult",
                "ya",
                "teen",
                "ya-fantasy",
                "ya-dystopian",
                "ya-dystopia",
                "children-young-adult",
                "children-ya",
            ),
            "soft_weight": 0.15,
            "require_core": True,
            "min_core": 20,
            "min_core_obscure": 5,
            "obscure_n": 400,
            "min_vs_fiction": 0.10,
            "min_vs_fiction_obscure": 0.05,
        },
    }
)


GATE_IDS = tuple(GATE_DEFS)
MATERIALIZED_GATE_IDS = frozenset({"sf", "fantasy", "coming_of_age", "lgbtq", "western"})

_GATE_ALIASES = {
    "science_fiction": "sf",
    "sci_fi": "sf",
    "coa": "coming_of_age",
    "comingofage": "coming_of_age",
    "lgbt": "lgbtq",
    "lgbtqia": "lgbtq",
    "queer": "lgbtq",
    "identity": "lgbtq",
    "childrens": "children",
    "children_s": "children",
    "magical-realism": "magical_realism",
    "magicalrealism": "magical_realism",
    "short-story": "short_story",
    "shortstory": "short_story",
    "graphic-novel": "graphic_novel",
    "graphicnovel": "graphic_novel",
    "hard-sci-fi": "hard_sf",
    "hard-scifi": "hard_sf",
    "hard-sf": "hard_sf",
    "hard_sci_fi": "hard_sf",
    "hard_scifi": "hard_sf",
    "hard_sf": "hard_sf",
    "road-novel": "road_novel",
    "slice-of-life": "slice_of_life",
    "sliceoflife": "slice_of_life",
    "young-adult": "ya",
}


def has_genre_gates() -> bool:
    try:
        return "work_genre_gates" in table_names()
    except Exception:
        return False


def parse_genre_gates(params: dict[str, Any]) -> list[str]:
    """Parse active named gates; gates are intersected (AND)."""

    explicit = "genre_gates" in params or "gates" in params
    raw = params.get("genre_gates", params.get("gates"))
    if raw is None or raw == "":
        return [] if explicit else []
    if isinstance(raw, str):
        value = raw.strip()
        if value.startswith("["):
            try:
                raw = json.loads(value)
            except json.JSONDecodeError:
                raw = [x.strip() for x in value.split(",") if x.strip()]
        else:
            raw = [x.strip() for x in value.split(",") if x.strip()]
    if not isinstance(raw, (list, tuple)):
        raw = [raw]

    out: list[str] = []
    seen: set[str] = set()
    for value in raw:
        gid = str(value).strip().lower().replace(" ", "_")
        candidates = (gid, gid.replace("_", "-"), gid.replace("-", "_"))
        gid = next((candidate for candidate in candidates if candidate in _GATE_ALIASES), gid)
        gid = _GATE_ALIASES.get(gid, gid.replace("-", "_"))
        if gid not in GATE_DEFS or gid in seen:
            continue
        seen.add(gid)
        out.append(gid)
    return out


def _sql_str_list(names: tuple[str, ...] | list[str] | set[str]) -> str:
    return ", ".join("'" + str(s).replace("'", "''") + "'" for s in names)


def _sum_expr(
    rows_sql: str,
    shelves: tuple[str, ...] | list[str] | set[str],
    *,
    work_alias: str,
) -> str:
    if not shelves:
        return "0.0"
    return f"""coalesce((
        SELECT sum(CASE WHEN gr.shelf IN ({_sql_str_list(shelves)})
                        THEN gr.count ELSE 0 END)::DOUBLE
        FROM {rows_sql} gr
        WHERE gr.work_id = {work_alias}.work_id
    ), 0.0)"""


def _dynamic_gate_sql(gid: str, definition: dict[str, Any], *, work_alias: str) -> str:
    # Imported lazily so genres.py can discover gate shelves without a module
    # import cycle.
    from curators_explorer.genres import ensure_extra_genres, genre_rows_sql

    shelves: set[str] = set()
    for key in ("core", "soft", "compete", "compete_soft", "literary"):
        shelves.update(str(x) for x in (definition.get(key) or ()))
    shelves.add("fiction")
    ensure_extra_genres(shelves)
    rows_sql = genre_rows_sql()
    core = _sum_expr(rows_sql, definition.get("core") or (), work_alias=work_alias)
    soft = _sum_expr(rows_sql, definition.get("soft") or (), work_alias=work_alias)
    soft_weight = float(definition.get("soft_weight", 0.35))
    score = f"(({core}) + {soft_weight} * ({soft}))"
    n = f"coalesce({work_alias}.n, 0)"
    min_core = float(definition.get("min_core", 5))
    min_obscure = float(definition.get("min_core_obscure", min_core))
    obscure_n = int(definition.get("obscure_n", 400))
    min_core_expr = f"CASE WHEN {n} < {obscure_n} THEN {min_obscure} ELSE {min_core} END"
    minimum_expr = f"({core})" if definition.get("require_core") else f"({score})"

    if definition.get("mode") == "tag":
        return f"({minimum_expr}) >= ({min_core_expr})"

    if definition.get("mode") == "theme":
        fiction = _sum_expr(rows_sql, ("fiction",), work_alias=work_alias)
        compete = _sum_expr(
            rows_sql, definition.get("compete") or (), work_alias=work_alias
        )
        ratio_base = (
            f"(({fiction}) + ({compete}))"
            if definition.get("ratio_include_compete")
            else f"({fiction})"
        )
        min_vs = float(definition.get("min_vs_fiction", 0.005))
        min_vs_obscure = float(
            definition.get("min_vs_fiction_obscure", min_vs)
        )
        min_vs_expr = (
            f"CASE WHEN {n} < {obscure_n} THEN {min_vs_obscure} ELSE {min_vs} END"
        )
        ratio = (
            f"CASE WHEN ({ratio_base}) > 0 THEN ({score}) / ({ratio_base}) "
            f"WHEN ({minimum_expr}) >= ({min_core_expr}) THEN 1.0 ELSE 0.0 END"
        )
        fiction_requirement = f" AND ({fiction}) > 0" if definition.get("require_fiction") else ""
        return (
            f"(({minimum_expr}) >= ({min_core_expr}) AND ({ratio}) >= ({min_vs_expr})"
            f"{fiction_requirement})"
        )

    # Ratio-mode fallback for the five older gates if the warehouse does not
    # contain their materialized rows.
    compete = _sum_expr(rows_sql, definition.get("compete") or (), work_alias=work_alias)
    compete_soft = _sum_expr(
        rows_sql, definition.get("compete_soft") or (), work_alias=work_alias
    )
    compete_expr = f"(({compete}) + {float(definition.get('compete_soft_weight', 0.0))} * ({compete_soft}))"
    literary = _sum_expr(rows_sql, definition.get("literary") or (), work_alias=work_alias)
    lit_weight = float(definition.get("literary_weight", 0.5))
    lit_min_n = int(definition.get("literary_min_n", 250))
    if definition.get("literary_always_if_popular", False):
        lit_term = f"CASE WHEN {n} >= {lit_min_n} THEN {lit_weight} * ({literary}) ELSE 0 END"
    else:
        lit_floor = float(definition.get("literary_floor", 80))
        lit_vs = float(definition.get("literary_vs_sf", 1.5))
        lit_term = (
            f"CASE WHEN {n} >= {lit_min_n} AND ({literary}) >= "
            f"greatest({lit_floor}, {lit_vs} * ({score})) "
            f"THEN {lit_weight} * ({literary}) ELSE 0 END"
        )
    ratio = f"({score}) / nullif(({score}) + ({compete_expr}) + ({lit_term}), 0)"
    min_ratio = float(definition.get("min_ratio", 0.5))
    standard = f"({score}) >= ({min_core_expr}) AND ({ratio}) >= {min_ratio}"

    ya = _sum_expr(rows_sql, ("young-adult", "ya", "teen"), work_alias=work_alias)
    core_abs = _sum_expr(rows_sql, definition.get("core") or (), work_alias=work_alias)
    escape_abs = float(definition.get("escape_abs_core", 1e9))
    escape_ratio = float(definition.get("escape_ratio", 1.0))
    escape = f"({core_abs}) >= {escape_abs} AND ({ratio}) >= {escape_ratio}"
    if definition.get("escape_require_ya_lt_core"):
        escape += f" AND ({ya}) < ({core_abs})"
    escape_soft_core = float(definition.get("escape_soft_core", 1e9))
    escape_soft_ratio = float(definition.get("escape_soft_ratio", 1.0))
    escape_soft = (
        f"({core_abs}) >= {escape_soft_core} AND ({ratio}) >= {escape_soft_ratio} "
        f"AND ({compete_expr}) > 0"
    )
    max_ya = definition.get("escape_soft_max_ya")
    if max_ya is not None:
        escape_soft += f" AND ({ya}) < {float(max_ya)}"
    return f"(({standard}) OR ({escape}) OR ({escape_soft}))"


def gate_sql_bits(
    gates: list[str] | None,
    *,
    work_alias: str = "w",
) -> tuple[str, list[Any]]:
    """Return an ANDed SQL suffix for named prevalence gates."""

    if not gates:
        return "", []
    parts: list[str] = []
    args: list[Any] = []
    materialized = has_genre_gates()
    for gid in gates:
        definition = GATE_DEFS.get(gid)
        if definition is None:
            continue
        if materialized and gid in MATERIALIZED_GATE_IDS:
            parts.append(
                f"""EXISTS (
                    SELECT 1 FROM work_genre_gates gg
                    WHERE gg.work_id = {work_alias}.work_id
                      AND gg.gate = ?
                      AND gg.passed
                )"""
            )
            args.append(gid)
        else:
            parts.append(_dynamic_gate_sql(gid, definition, work_alias=work_alias))
    return (" AND " + " AND ".join(parts), args) if parts else ("", [])


def _sum_shelves(shelf_counts: dict[str, int], names: tuple[str, ...] | list[str]) -> float:
    return float(sum(shelf_counts.get(s, 0) for s in names))


def score_gate(
    gate_id: str,
    shelf_counts: dict[str, int],
    *,
    n_ratings: int,
) -> dict[str, Any]:
    """Evaluate a gate in Python for validation and diagnostics."""

    definition = GATE_DEFS[gate_id]
    core = _sum_shelves(shelf_counts, definition.get("core") or ())
    soft = _sum_shelves(shelf_counts, definition.get("soft") or ())
    score = core + float(definition.get("soft_weight", 0.35)) * soft
    obscure = n_ratings < int(definition.get("obscure_n", 400))
    min_core = float(
        definition.get("min_core_obscure", definition.get("min_core", 5))
        if obscure
        else definition.get("min_core", 5)
    )

    if definition.get("mode") == "tag":
        passed = (core if definition.get("require_core") else score) >= min_core
        return {
            "gate": gate_id,
            "passed": bool(passed),
            "score": round(score, 2),
            "ratio": None,
            "core": core,
            "mode": "tag",
        }

    fiction = float(shelf_counts.get("fiction", 0))
    if definition.get("mode") == "theme":
        compete = _sum_shelves(shelf_counts, definition.get("compete") or ())
        ratio_base = fiction + compete if definition.get("ratio_include_compete") else fiction
        minimum_score = core if definition.get("require_core") else score
        ratio = (
            score / ratio_base
            if ratio_base > 0
            else (1.0 if minimum_score >= min_core else 0.0)
        )
        min_vs = float(
            definition.get("min_vs_fiction_obscure", definition.get("min_vs_fiction", 0.005))
            if obscure
            else definition.get("min_vs_fiction", 0.005)
        )
        passed = (
            (core if definition.get("require_core") else score) >= min_core
            and ratio >= min_vs
            and (not definition.get("require_fiction") or fiction > 0)
        )
        return {
            "gate": gate_id,
            "passed": bool(passed),
            "score": round(score, 2),
            "ratio": round(ratio, 4),
            "core": core,
            "mode": "theme",
        }

    compete = _sum_shelves(shelf_counts, definition.get("compete") or ())
    compete += float(definition.get("compete_soft_weight", 0.0)) * _sum_shelves(
        shelf_counts, definition.get("compete_soft") or ()
    )
    literary = _sum_shelves(shelf_counts, definition.get("literary") or ())
    lit_weight = float(definition.get("literary_weight", 0.5))
    if definition.get("literary_always_if_popular", False):
        apply_lit = n_ratings >= int(definition.get("literary_min_n", 250))
    else:
        apply_lit = (
            n_ratings >= int(definition.get("literary_min_n", 250))
            and literary
            >= max(
                float(definition.get("literary_floor", 80)),
                float(definition.get("literary_vs_sf", 1.5)) * score,
            )
        )
    denom = score + compete + (lit_weight * literary if apply_lit else 0.0)
    ratio = score / denom if denom > 0 else None
    passed = bool(
        score >= min_core
        and ratio is not None
        and (
            ratio >= float(definition.get("min_ratio", 0.5))
            or (
                core >= float(definition.get("escape_abs_core", 1e9))
                and ratio >= float(definition.get("escape_ratio", 1.0))
                and (
                    not definition.get("escape_require_ya_lt_core")
                    or _sum_shelves(shelf_counts, ("young-adult", "ya", "teen")) < core
                )
            )
            or (
                core >= float(definition.get("escape_soft_core", 1e9))
                and ratio >= float(definition.get("escape_soft_ratio", 1.0))
                and compete > 0
                and (
                    definition.get("escape_soft_max_ya") is None
                    or _sum_shelves(shelf_counts, ("young-adult", "ya", "teen"))
                    < float(definition["escape_soft_max_ya"])
                )
            )
        )
    )
    return {
        "gate": gate_id,
        "passed": passed,
        "score": round(score, 2),
        "ratio": round(ratio, 4) if ratio is not None else None,
        "core": core,
        "mode": "ratio",
    }


def _anchor_result(gate_id: str, title_pattern: str) -> tuple[str, bool | None, float | None, float | None] | None:
    row = execute(
        """
        SELECT work_id, title, n
        FROM work_scores
        WHERE title ILIKE ?
        ORDER BY n DESC
        LIMIT 1
        """,
        [title_pattern],
    ).fetchone()
    if not row:
        return None
    work_id, title, n = str(row[0]), str(row[1]), int(row[2] or 0)
    if gate_id in MATERIALIZED_GATE_IDS and has_genre_gates():
        gate = execute(
            """
            SELECT passed, score, ratio
            FROM work_genre_gates
            WHERE work_id = ? AND gate = ?
            """,
            [work_id, gate_id],
        ).fetchone()
        return title, bool(gate[0]) if gate else False, gate[1] if gate else None, gate[2] if gate else None

    from curators_explorer.genres import ensure_extra_genres, genre_rows_sql

    ensure_extra_genres(set().union(*(_shelf_set(d) for d in GATE_DEFS.values())))
    counts = {
        str(shelf): int(count or 0)
        for shelf, count in execute(
            f"SELECT shelf, sum(count)::BIGINT FROM {genre_rows_sql()} WHERE work_id = ? GROUP BY shelf",
            [work_id],
        ).fetchall()
    }
    result = score_gate(gate_id, counts, n_ratings=n)
    return title, bool(result["passed"]), result.get("score"), result.get("ratio")


def _shelf_set(definition: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for key in ("core", "soft", "compete", "compete_soft", "literary"):
        out.update(str(x) for x in (definition.get(key) or ()))
    out.add("fiction")
    return out


# These are smoke anchors, not classification rules.  The title patterns are
# intentionally broad enough to select the popular canonical work edition.
GENRE_ASSERTIONS: tuple[tuple[str, str, bool], ...] = (
    # Copied UCSD anchors.
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
    ("coming_of_age", "Great Expectations", True),
    ("coming_of_age", "The Ice Palace", True),
    ("coming_of_age", "The Fellowship of the Ring%", False),
    ("coming_of_age", "The Hobbit%", False),
    ("coming_of_age", "The Hitchhiker's Guide to the Galaxy%", False),
    ("coming_of_age", "The Brothers K", False),
    ("coming_of_age", "Pride and Prejudice", False),
    ("lgbtq", "Giovanni's Room", True),
    ("lgbtq", "Call Me by Your Name", True),
    ("lgbtq", "The Hobbit%", False),
    ("western", "Lonesome Dove", True),
    ("western", "Blood Meridian%", True),
    ("western", "True Grit", True),
    ("western", "Gone Girl", False),
    # New loose / strict genre anchors.
    ("children", "Charlotte's Web", True),
    ("children", "The Little Prince", True),
    ("children", "The Hobbit%", True),
    ("children", "The Trial", False),
    ("religion", "The Brothers Karamazov", True),
    ("religion", "The Handmaid's Tale", True),
    ("religion", "The Trial", False),
    ("philosophy", "The Brothers Karamazov", True),
    ("philosophy", "Crime and Punishment", True),
    ("philosophy", "The Stranger", True),
    ("philosophy", "The Trial", True),
    ("philosophy", "The Hobbit%", False),
    ("magical_realism", "One Hundred Years of Solitude", True),
    ("magical_realism", "The House of the Spirits", True),
    ("magical_realism", "Beloved", True),
    ("magical_realism", "The Trial", False),
    ("weird", "House of Leaves", True),
    ("weird", "The Metamorphosis", True),
    ("weird", "The Third Policeman", True),
    ("weird", "The Wind-Up Bird Chronicle", True),
    ("weird", "The Stranger", False),
    ("satire", "Catch-22%", True),
    ("satire", "Animal Farm", True),
    ("satire", "Candide", True),
    ("satire", "The Hitchhiker's Guide%", True),
    ("satire", "Slaughterhouse-Five", True),
    ("satire", "The Trial", False),
    ("dystopian", "1984", True),
    ("dystopian", "Brave New World", True),
    ("dystopian", "The Handmaid's Tale", True),
    ("dystopian", "Pride and Prejudice", False),
    ("short_story", "Dubliners", True),
    ("short_story", "Nine Stories", True),
    ("short_story", "The Metamorphosis", True),
    ("short_story", "The Brothers Karamazov", False),
    ("comedy", "Candide", True),
    ("comedy", "Don Quixote", True),
    ("comedy", "A Confederacy of Dunces", True),
    ("comedy", "The Trial", False),
    ("low_fantasy", "The Last Unicorn", True),
    ("low_fantasy", "The Trial", False),
    ("poetry", "Leaves of Grass", True),
    ("poetry", "The Waste Land", True),
    ("poetry", "The Brothers Karamazov", False),
    ("graphic_novel", "Watchmen", True),
    ("graphic_novel", "The Metamorphosis", False),
    ("graphic_novel", "The Great Gatsby", False),
    ("horror", "Dracula", True),
    ("horror", "Frankenstein", True),
    ("horror", "The Haunting of Hill House", True),
    ("horror", "The Shining", True),
    ("horror", "The Exorcist", True),
    ("horror", "The Trial", False),
    ("apocalyptic", "The Road", True),
    ("apocalyptic", "Seveneves", True),
    ("apocalyptic", "Pride and Prejudice", False),
    ("hard_sf", "Contact", True),
    ("hard_sf", "Seveneves", True),
    ("hard_sf", "The Trial", False),
    ("psychology", "The Brothers Karamazov", True),
    ("psychology", "Crime and Punishment", True),
    ("psychology", "The Stranger", True),
    ("psychology", "The Hobbit%", False),
    ("road_novel", "On the Road", True),
    ("road_novel", "Fear and Loathing in Las Vegas", True),
    ("road_novel", "Paper Towns", True),
    ("road_novel", "Pride and Prejudice", False),
    ("slice_of_life", "Ghost World", True),
    ("slice_of_life", "The Trial", False),
    ("slice_of_life", "Pride and Prejudice", False),
    ("ya", "The Hunger Games%", True),
    ("ya", "Harry Potter and the Sorcerer's Stone%", True),
    ("ya", "The Fault in Our Stars", True),
    ("ya", "The Perks of Being a Wallflower", True),
    ("ya", "The Book Thief", True),
    ("ya", "The Hobbit%", False),
)


def validate_gates() -> None:
    """Print and assert the known genre anchor classifications."""

    failures: list[str] = []
    for gate, title_pattern, expected in GENRE_ASSERTIONS:
        result = _anchor_result(gate, title_pattern)
        if result is None:
            message = f"MISS {gate} {title_pattern}"
            print("  " + message)
            failures.append(message)
            continue
        title, actual, score, ratio = result
        ok = actual == expected
        mark = "OK" if ok else "FAIL"
        print(
            f"  {mark}: {gate:16s} expect={expected} got={actual} "
            f"score={score} ratio={ratio} | {title[:55]}"
        )
        if not ok:
            failures.append(f"{gate} {title_pattern}: expected {expected}, got {actual}")
    assert not failures, "Genre validation failures:\n" + "\n".join(failures)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    print("Curators genre gates:")
    for gid in GATE_IDS:
        definition = GATE_DEFS[gid]
        print(
            f"  {gid:16s} {definition.get('label', gid)} "
            f"({definition.get('strictness', 'copied')})"
        )
    if args.validate:
        print("\nGate validation:")
        validate_gates()


if __name__ == "__main__":
    main()

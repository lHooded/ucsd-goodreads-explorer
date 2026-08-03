# UCSD Goodreads ranking explorer

Explore **unordered** star ratings from the
[UCSD Goodreads Book Graph](https://mengtingwan.github.io/data/goodreads)
(Wan & McAuley) with RYM-style **curator** scoring — literary-anchored percentiles,
deep-curator cohorts, coverage controls, and live similar-book lookup.

Built for local research use. The raw UCSD dumps are **academic use only** and
are **not** redistributed here.

## What’s in this repo

| Path | Role |
|---|---|
| `ucsd_goodreads/` | Download helpers + DuckDB/parquet warehouse |
| `ucsd_explorer/` | Ranking UI + scoring methods (server on `:8766`) |
| `lit-2014-2024.txt` | Literary poll used to mint deep curators / taste signals |

Legacy Goodreads **Listopia** scrapers and static ranking pages are intentionally
out of scope (ignored if present locally).

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1) Download UCSD dumps (large; see ucsd_goodreads/README.md)
./ucsd_goodreads/download.sh

# 2) Build warehouse parquet + DuckDB views
.venv/bin/python -m ucsd_goodreads.warehouse build-all

# 3) Materialize explorer rating / taste / curator tables
.venv/bin/python -m ucsd_explorer.materialize_ratings

# 4) Run the UI
.venv/bin/python -m ucsd_explorer.server
# → http://127.0.0.1:8766
```

Rebuild taste / deep-curator tables after editing
`ucsd_explorer/data/taste_lists.json` or `normie_canon.json`:

```bash
.venv/bin/python -m ucsd_explorer.taste
# or deep cohort only:
.venv/bin/python -m ucsd_explorer.taste --deep-only
```

## Scoring (high level)

- **Curator‰** methods use literary-anchored personal percentiles (harsh vs
  trashy raters land on a comparable shelf scale).
- **Deep Curator** cohorts are readers with depth on the lit poll beyond a
  school/normie canon (canon is selection-only — never a book-level penalty).
- **Deep Curator‰ top-half geom** keeps ★3–5 in each curator’s top half-shelf,
  weights stars as a geometric sequence `q² : q : 1`, and raises percentiles to
  a power `x`.
- **Coverage** blends among-raters score (0) with full-cohort score (100,
  unread → 0), linearly in score space.

See `ucsd_explorer/README.md` for methods and UI details.

## Data layout (local, gitignored)

```
data/ucsd_goodreads/
  raw/          # original dumps
  parquet/      # columnar extracts
  ucsd.duckdb   # warehouse views
  explorer.duckdb
```

## Cite the source data

Mengting Wan, Julian McAuley, *Item Recommendation on Monotonic Behavior Chains*, RecSys 2018.

Mengting Wan et al., *Fine-Grained Spoiler Detection from Large-Scale Review Corpora*, ACL 2019.

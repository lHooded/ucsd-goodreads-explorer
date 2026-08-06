# Curators Explorer

Simplified rebuild of the UCSD Goodreads ranking explorer.

## Run

```bash
cd /path/to/novels
PYTHONPATH=. .venv/bin/python -m curators_explorer
# → http://127.0.0.1:8767/
```

Uses the existing DuckDB warehouse at `data/ucsd_goodreads/explorer.duckdb` (read-only). Leave `ucsd_explorer/` in place.

**Hard-refresh** the browser after UI changes. **Restart** the server after Python changes (no hot reload).

## What it does

- One filtering philosophy: **Curators** (taste gates + weights)
- Metrics: fixed distributed consensus, fixed community esteem, love, Bayesian mean, raw mean, % top, curator reads
- Scale modes: adjusted percentiles (default), raw full-shelf percentiles, raw stars
- Knobs: **deweight**, **purity**, min ratings, Bayesian m, SF toggle, catalog filters
- Fixed: coverage = among-raters (0); strictness/depth hidden at 0
- Editable positive/negative author packs + school-neutral titles (Reset restores shipped preset)
- Dual histograms: curator cohort vs global

The two fixed research metrics serve all 4,781 mass-2 eligible works from
`data/distributed_canon_catalog.json`. **Distributed canon** retains the conservative
score (mean community esteem minus disagreement and evidence penalties), while
**Community esteem** ranks the same works before those penalties. Both display
analytic `±u`, jury evidence, coverage, a community-disagreement status, and a
separate evidence status. Search, Limit, and SF-only filter these views; the live
curator and catalog controls deliberately do not recompute them. Selecting either
fixed metric raises the display limit to 5,000 so the full exploratory tail is visible.

## Defaults (from taste-signal Pareto)

| Preset | dew | purity |
|---|---:|---:|
| Default literary | 15 | 55 |
| Browse / mass | 25 | 0 |
| Sharp | 15 | 65 |
| Everyone (debug) | 0 | 0 |

See `ucsd_explorer/data/SIMPLIFIED_REBUILD_REPORT.md` and `PARETO_TASTE_SIGNALS_REPORT.md`.

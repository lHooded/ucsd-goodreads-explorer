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
- Metrics: love, Bayesian mean, raw mean, % top, curator reads
- Scale modes: adjusted percentiles (default), raw full-shelf percentiles, raw stars
- Knobs: **deweight**, **purity**, min ratings, Bayesian m, SF toggle, catalog filters
- Fixed: coverage = among-raters (0); strictness/depth hidden at 0
- Editable positive/negative author packs + school-neutral titles (Reset restores shipped preset)
- Dual histograms: curator cohort vs global

## Defaults (from taste-signal Pareto)

| Preset | dew | purity |
|---|---:|---:|
| Default literary | 15 | 55 |
| Browse / mass | 25 | 0 |
| Sharp | 15 | 65 |
| Everyone (debug) | 0 | 0 |

See `ucsd_explorer/data/SIMPLIFIED_REBUILD_REPORT.md` and `PARETO_TASTE_SIGNALS_REPORT.md`.

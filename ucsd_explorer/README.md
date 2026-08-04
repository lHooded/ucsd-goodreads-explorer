# UCSD Ranking Explorer

Server-side explorer for **unordered** UCSD Goodreads star ratings.

Rankings stay in DuckDB/SQL; the browser only gets the result table
(http://127.0.0.1:8766 by default).

## Build / run

From the repo root (after the warehouse exists — see the root README):

```bash
.venv/bin/python -m ucsd_explorer.materialize_ratings
.venv/bin/python -m ucsd_explorer.taste          # taste + curator tables
.venv/bin/python -m ucsd_explorer.server
```

Useful rebuilds:

```bash
.venv/bin/python -m ucsd_explorer.taste --deep-only
.venv/bin/python -m ucsd_explorer.taste --pure-only
```

## Config data (committed)

| File | Role |
|---|---|
| `data/taste_lists.json` | Literary / commercial author & book signals |
| `data/normie_canon.json` | School/canon titles excluded when minting *deep* curators |
| `data/deep_curator_params.json` | Materialization floors for the deep cohort |
| `data/catalog_overrides.json` | Manual catalog / year / format fixes |
| `../lit-2014-2024.txt` | 2014–2024 literary poll chart |

## Curator scoring

Literary-anchored **percentiles** map each user’s star to a personal shelf
position. Curator cohorts soft-deweight (or gate) by elite weight; deep methods
add **depth** / **purity** sliders over the non-normie poll, and bake
**non-literary anti-signal** pollution into weights (`(1−com_share)^3` plus a
purity-tightened com_share cap) so commercial SF fans are suppressed without
the separate taste filter.

Notable methods:

| Method | Idea |
|---|---|
| Curator‰ love | `pct^ρ` love mass / cohort (unread → 0 at full coverage) |
| Deep Curator‰ love / tilt | Same on the deep cohort |
| Deep Curator‰ top-half geom | ★∈{3,4,5} ∩ pct≥0.5; mass = geom(★)·pct^x |
| Curator‰ love−hate / tilt | Asymmetric love minus bottom-shelf mass |
| Bayesian 5★ / picky / gem | Simpler baselines on all or picky raters |

**Coverage** (‰ methods): slider `u` mixes  
`(1−u)·(mass / raters) + u·(mass / full cohort)`.

**Geom sliders:** star ratio `q` (weights `q²:q:1` for ★5/4/3) and percentile
power `x`.

## Similar books

Open a row → drawer with co-favorite similarity (cosine / Jaccard / lift / PMI /
conditional / association) from `five_star_events`, plus a ranking-cohort
weighted star histogram.

## Catalog filters

Fiction-only, SF-only, year band, exclude comics / picture books / derivatives,
collapse duplicate works, deweight omnibus/collections.

# Ensemble Reversal — Overnight Campaign Runbook

**Service:** `novels-ensemble-reversal.service` (systemd user unit, linger on)
**Launched:** Fri 2026-08-07 01:12 AEST (seed 20260808, `--hours 7` cap)
**Script:** `curators_explorer/scripts/research_jury_ensemble_reversal.py`

## Purpose

Test the hypothesis "if a literary center exists, reversed random juries should
drift toward it". Each of 300 random juries per size (2000 / 5000 / 10000 /
20000) is collapsed to the Goodreads center (stage 0) and then pushed to a
non-center basin via gain-hard pruning (members weight 20, non-members 0.4,
hard renormalization after each gain-hard step, 6 stages, evidence floor).
The ensemble of reversed endpoints is then combined by several label-free
"processed averages" (plain mean, coordinate median, agreement-weighted
consensus, mean displacement) and a basin census (clustering endpoint
preference scores at correlation threshold 0.3).

Pilot evidence so far (25 juries, size 2000): reversed juries land in genre
basins, NOT literary — dominant basin Harry Potter / ACOTAR / Sanderson /
Martin (23/25 juries at size 2000), second small eclectic basin (Quran, Maus,
Calvin & Hobbes). All processed averages: exact_lit 0 @50 (chance 0.10),
anti 5–44 (chance 6.17). The overnight run raises statistics to 300 juries ×
4 sizes to confirm or overturn this.

## Monitoring

- `systemctl --user status novels-ensemble-reversal` — running / done / failed
- `tail -f curators_explorer/data/ensemble_reversal_overnight.log` — per-jury lines
- `curators_explorer/data/jury_ensemble_reversal_overnight_status.json` — checkpoint every 10 juries
- Progress estimate: ~3.4 s/jury, 1200 juries ≈ 70 min wall (well under the 7 h cap)

## Stop / restart

- `systemctl --user stop novels-ensemble-reversal` — halts cleanly (current jury finishes; per-jury try/except; data before the stop remains valid)
- Restart re-runs from scratch (no `--resume`; run is short by design so this is acceptable). `Restart=on-failure` handles crashes automatically.

## Outputs (land in `curators_explorer/data/`)

- `jury_ensemble_reversal_overnight.json` — full per-jury records (stage-0 + deepest directions and preference scores, per-stage retained scalars, verdicts) + aggregates + clusters
- `JURY_ENSEMBLE_REVERSAL_OVERNIGHT_REPORT.md` — rendered report
- `ensemble_reversal_overnight.log` — stdout/stderr

## Memory budget (safe by design)

~1200 juries × 4 vectors × 26,418 float32 ≈ 500 MB held at peak; machine had
only ~6.1 GB available (15 GB total, swap already partly in use), so the
campaign is deliberately bounded rather than an 8-hour unbounded run. Do not
raise `--juries` far without checking `free -h`.

## Interpretation

- Exact-literary @50 per aggregate vs chance 0.10; broad @50 vs chance 0.80; anti vs chance 6.17.
- If all aggregates and basins stay at chance/non-literary: reversal does NOT point at a literary center (genre-attractor outcome).
- If a basin or aggregate exceeds chance substantially: that basin/aggregate is a candidate literary center to drill into next.

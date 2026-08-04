# Deep taste signals (personal power + comedy cap) — shelved

Experiment status: **parked**. The live `main` deep-curator path
(normie depth/purity + commercial com_share) is cleaner and already does
most of what this was aiming at. These toggles did not feel worth the
extra list-curation surface.

## What this branch adds

Query-time toggles on deep curator methods only (off by default):

1. **Personal power** — require ≥1 ★=5 on `personal_power_signals.json`
   (Tarkovsky/Tarr-class intensity: intimate, personal-epic, or
   philosophical fiction — not society-satire / ideology alone).
2. **Comedy cap** — treat acclaimed comedy ★≥4 like school-canon on the
   purity axis, and allow at most 2 comedy ★=5s (`comedy_signals.json`).

Materialization (`taste --deep-only`) builds `comedy_works` /
`personal_power_works` and stores `n_comedy`, `n_comedy_fives`,
`n_personal_fives` on `user_curator_deep_weight`.

UI: checkboxes under Normie depth/purity when a deep method is selected.

## Why shelve

- Cohort impact at typical settings (depth 40 / purity 55) was modest once
  the personal list grew (most deep curators already had ≥1 list ★=5).
- Comedy rarely dominated deep top ranks; Hitchhiker omnibus spikes were
  the main case, and existing com/normie machinery already dampens a lot.
- Maintaining hand lists + author_hints is ongoing cost for little ranking
  signal vs depth/purity/com_share.

## If reviving

1. Merge/cherry-pick this branch.
2. Review `personal_power_signals.json` / `comedy_signals.json` (include vs
   borderline vs excluded; popularity deferrals; foundational Homer/Milton
   excluded on purpose).
3. `PYTHONPATH=. .venv/bin/python -m ucsd_explorer.taste --deep-only`
4. Restart the explorer; enable toggles under deep methods.

## Related RYM analogy (user intent)

- Don’t follow users who 5★ many acclaimed comedies.
- Satire / society / ideology alone isn’t enough; want at least one
  powerful/personal 5★ (not only Strangelove-class).

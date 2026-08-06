# Purity × strictness sweep (quality vs quantity)

Gates applied to the **deep mint** (~20k), then within-jury pairwise.

- **Purity:** `deep_share ≥ t·0.80` and, when purity>0, `com_share ≤ 1−t·(1−0.08)`.
- **Strictness:** elite top-K among purity passers (log-linear toward ~100 at 100; 0 = keep all passers).
- **Weights:** stored `curator_pct_weight` (equal-vote not swept here).

### Quantity
Kish n_eff under stored weights (primary) + raw n_jury.

### Quality
`Q_clean = 3·pos50 − 4·anti50 − 0.5·anti1000 − 2·filler50` from pairwise head.
Poll held-out / pos50 are **contaminated** (mint uses poll depth) — use as one axis,
not sole truth. Prefer kneepoints that also keep mass and don't collapse to tiny elites.

Grid: purity ∈ [0, 35, 45, 55, 65, 75, 90] × strictness ∈ [0, 15, 25, 40, 55, 70, 85] (49 ok runs).

**Mint note:** on the pre-minted deep table, purity 0 and 35 are identical — mint floors
(`deep_share≥0.35`, `com_share≤0.20`) already dominate soft purity. Purity starts to bite at ~45+.

## Pareto summary

Pareto front: `p0_s0`, `p0_s15`, `p0_s25`, `p35_s0`, `p35_s15`, `p35_s25`, `p45_s15`, `p45_s40`, `p55_s0`, `p55_s15`, `p55_s25`, `p55_s40`, `p65_s25`, `p75_s40`

- **Utopia knee:** `p65_s25` Q=126.00 kish≈2678 n=3286 pos50=42 anti50=0 fill50=0 held@50=0.419
- **Product (Q×mass):** `p65_s25` Q=126.00 kish≈2678 n=3286 pos50=42 anti50=0 fill50=0 held@50=0.419
- **Quality-lean:** `p75_s40` Q=137.50 kish≈1102 n=1262 pos50=47 anti50=0 fill50=0 held@50=0.442
- **Balanced:** `p45_s40` Q=131.00 kish≈2015 n=2354 pos50=44 anti50=0 fill50=0 held@50=0.442
- **Best quality:** `p75_s40` Q=137.50 kish≈1102 n=1262 pos50=47 anti50=0 fill50=0 held@50=0.442
- **Best quantity:** `p0_s0` Q=71.50 kish≈9401 n=19841 pos50=24 anti50=0 fill50=0 held@50=0.163

## Full grid

| p | s | n | kish | Q | pos50 | anti50 | fill50 | sticky | held@50 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 19841 | 9401 | 71.50 | 24 | 0 | 0 | 4 | 0.163 |
| 0 | 15 | 8973 | 6191 | 93.00 | 31 | 0 | 0 | 7 | 0.233 |
| 0 | 25 | 5287 | 4094 | 111.00 | 37 | 0 | 0 | 8 | 0.302 |
| 0 | 40 | 2391 | 2044 | 125.00 | 42 | 0 | 0 | 11 | 0.442 |
| 0 | 55 | 1082 | 976 | 134.50 | 47 | 0 | 0 | 11 | 0.512 |
| 0 | 70 | 489 | 455 | 130.50 | 46 | 0 | 0 | 11 | 0.512 |
| 0 | 85 | 222 | 211 | 126.00 | 43 | 0 | 0 | 8 | 0.442 |
| 35 | 0 | 19841 | 9401 | 71.50 | 24 | 0 | 0 | 4 | 0.163 |
| 35 | 15 | 8973 | 6191 | 93.00 | 31 | 0 | 0 | 7 | 0.233 |
| 35 | 25 | 5287 | 4094 | 111.00 | 37 | 0 | 0 | 8 | 0.302 |
| 35 | 40 | 2391 | 2044 | 125.00 | 42 | 0 | 0 | 11 | 0.442 |
| 35 | 55 | 1082 | 976 | 134.50 | 47 | 0 | 0 | 11 | 0.512 |
| 35 | 70 | 489 | 455 | 130.50 | 46 | 0 | 0 | 11 | 0.512 |
| 35 | 85 | 222 | 211 | 126.00 | 43 | 0 | 0 | 8 | 0.442 |
| 45 | 0 | 19333 | 9255 | 71.50 | 24 | 0 | 0 | 4 | 0.163 |
| 45 | 15 | 8778 | 6092 | 96.00 | 32 | 0 | 0 | 7 | 0.256 |
| 45 | 25 | 5185 | 4028 | 111.00 | 37 | 0 | 0 | 9 | 0.279 |
| 45 | 40 | 2354 | 2015 | 131.00 | 44 | 0 | 0 | 11 | 0.442 |
| 45 | 55 | 1069 | 965 | 133.00 | 47 | 0 | 0 | 11 | 0.512 |
| 45 | 70 | 486 | 453 | 133.50 | 47 | 0 | 0 | 12 | 0.535 |
| 45 | 85 | 221 | 210 | 126.00 | 43 | 0 | 0 | 8 | 0.465 |
| 55 | 0 | 14960 | 7795 | 75.00 | 25 | 0 | 0 | 3 | 0.140 |
| 55 | 15 | 7059 | 5126 | 105.00 | 35 | 0 | 0 | 8 | 0.302 |
| 55 | 25 | 4278 | 3417 | 120.00 | 40 | 0 | 0 | 9 | 0.349 |
| 55 | 40 | 2019 | 1749 | 132.00 | 44 | 0 | 0 | 11 | 0.442 |
| 55 | 55 | 953 | 865 | 122.00 | 46 | 0 | 0 | 11 | 0.488 |
| 55 | 70 | 450 | 420 | 130.50 | 46 | 0 | 0 | 11 | 0.512 |
| 55 | 85 | 212 | 201 | 129.00 | 44 | 0 | 0 | 9 | 0.488 |
| 65 | 0 | 10525 | 5827 | 89.50 | 30 | 0 | 0 | 5 | 0.186 |
| 65 | 15 | 5235 | 3910 | 108.00 | 36 | 0 | 0 | 9 | 0.326 |
| 65 | 25 | 3286 | 2678 | 126.00 | 42 | 0 | 0 | 10 | 0.419 |
| 65 | 40 | 1635 | 1434 | 131.00 | 44 | 0 | 0 | 11 | 0.465 |
| 65 | 55 | 813 | 743 | 121.50 | 46 | 0 | 0 | 11 | 0.488 |
| 65 | 70 | 405 | 379 | 135.00 | 47 | 0 | 0 | 12 | 0.512 |
| 65 | 85 | 202 | 192 | 121.00 | 42 | 0 | 1 | 9 | 0.442 |
| 75 | 0 | 6833 | 3723 | 95.50 | 32 | 0 | 0 | 6 | 0.233 |
| 75 | 15 | 3626 | 2663 | 120.00 | 40 | 0 | 0 | 8 | 0.326 |
| 75 | 25 | 2377 | 1917 | 121.50 | 41 | 0 | 0 | 9 | 0.349 |
| 75 | 40 | 1262 | 1102 | 137.50 | 47 | 0 | 0 | 12 | 0.442 |
| 75 | 55 | 670 | 613 | 126.50 | 46 | 0 | 0 | 11 | 0.465 |
| 75 | 70 | 356 | 333 | 130.50 | 45 | 0 | 0 | 12 | 0.465 |
| 75 | 85 | 189 | 180 | 121.50 | 42 | 0 | 1 | 8 | 0.419 |
| 90 | 0 | 3395 | 1806 | 113.50 | 38 | 0 | 0 | 8 | 0.302 |
| 90 | 15 | 2001 | 1386 | 123.00 | 42 | 0 | 0 | 9 | 0.372 |
| 90 | 25 | 1407 | 1072 | 126.00 | 44 | 0 | 0 | 9 | 0.372 |
| 90 | 40 | 829 | 690 | 125.00 | 46 | 0 | 0 | 10 | 0.442 |
| 90 | 55 | 489 | 431 | 133.00 | 46 | 0 | 0 | 11 | 0.442 |
| 90 | 70 | 288 | 263 | 136.00 | 46 | 0 | 0 | 11 | 0.442 |
| 90 | 85 | 170 | 159 | 132.00 | 44 | 0 | 0 | 8 | 0.442 |

## Recommendation

- Prefer **purity=65**, **strictness=25** as the quality+quantity knee (`p65_s25`).
- Cohort size ≈ **3286** (Kish ≈ **2678**); purity passers before elite cut ≈ 10525.
- Gates: min_deep_share=0.520, com_cap=0.4019999999999999.

Head (knee):
- 1. Crime and Punishment — Fyodor Dostoyevsky
- 2. The Brothers Karamazov — Fyodor Dostoyevsky
- 3. Gravity's Rainbow — Thomas Pynchon
- 4. 2666 — Roberto Bolano
- 5. Stoner — John  Williams
- 6. War and Peace — Leo Tolstoy
- 7. Infinite Jest — David Foster Wallace
- 8. The Divine Comedy — Dante Alighieri

### Notes for jury reverse-engineering

- If utopia knee keeps **strictness=0**, prefer purity gates over hard elite caps.
- If high strictness wins only on poll probes, treat as shortcut risk (same contamination as the size sweep's cap=2000).
- Soft continuous jury-ish weights still deferred; this sweep stays hard gates + stored_w.


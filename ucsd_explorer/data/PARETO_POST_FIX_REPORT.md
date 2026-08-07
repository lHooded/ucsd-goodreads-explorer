# Pareto after slider zero-fix

## Zero-fix verification

all_query_zero: no taste gates / com_cap (resolved_com_cap=None). Ranking uses equal weight over all percentile users (~n_percentile_users); mint gate count above is only the mint table size for comparison. Raising depth/purity/deweight switches to mint_deep scoring.

| Case | cohort n | resolved com_cap | gate has com |
|---|---:|---:|---|
| all_query_zero | 19841 | None | False |
| purity55 | 14960 | 0.4939999999999999 | True |
| explicit_com_0.11 | 16347 | 0.11 | True |
| d40_p55 | 12627 | 0.4939999999999999 | True |
| d40_p0 | 16645 | None | False |

Mint table size: **19,841**

Percentile users (all-zero cohort): **625,573**

## Core grid (depth × purity × strictness, deweight=25)

Runs: 48. Pareto front: `core_d0_p0_s0`, `core_d0_p35_s0`, `core_d0_p75_s0`, `core_d25_p0_s0`, `core_d25_p35_s0`, `core_d25_p75_s0`

- **Utopia knee:** `core_d0_p0_s0` Q=32.15 geo_n=569 good_med=34 bad_med=200 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `core_d0_p0_s0` Q=32.15 geo_n=569 good_med=34 bad_med=200 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `core_d0_p0_s0` Q=32.15 geo_n=569 good_med=34 bad_med=200 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `core_d0_p75_s0` Q=35.67 geo_n=210 good_med=32 bad_med=202 params={'normie_depth': 0, 'normie_purity': 75, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `core_d0_p0_s0` Q=32.15 geo_n=569 good_med=34 bad_med=200 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| core_d0_p75_s0 | 35.67 | 210 | 223 | 32 | 202 |
| core_d25_p75_s0 | 35.67 | 210 | 223 | 32 | 202 |
| core_d60_p0_s40 | 34.17 | 109 | 103 | 32 | 153 |
| core_d60_p35_s40 | 34.17 | 109 | 103 | 32 | 153 |
| core_d60_p55_s40 | 34.17 | 103 | 95 | 32 | 155 |
| core_d40_p0_s40 | 34.15 | 144 | 158 | 34 | 170 |
| core_d40_p35_s40 | 34.15 | 144 | 158 | 34 | 170 |
| core_d0_p0_s40 | 34.14 | 152 | 169 | 35 | 178 |
| core_d0_p35_s40 | 34.14 | 152 | 169 | 35 | 178 |
| core_d25_p0_s40 | 34.14 | 152 | 169 | 35 | 178 |
| core_d25_p35_s40 | 34.14 | 152 | 169 | 35 | 178 |
| core_d40_p75_s0 | 33.67 | 193 | 214 | 32 | 200 |
| core_d40_p55_s40 | 33.18 | 131 | 129 | 31 | 163 |
| core_d0_p55_s40 | 33.16 | 137 | 145 | 33 | 167 |
| core_d25_p55_s40 | 33.16 | 137 | 145 | 33 | 167 |
| core_d0_p0_s0 | 32.15 | 569 | 528 | 34 | 200 |
| core_d0_p35_s0 | 32.15 | 569 | 528 | 34 | 200 |
| core_d0_p55_s0 | 32.15 | 420 | 389 | 34 | 232 |
| core_d25_p0_s0 | 32.15 | 569 | 528 | 34 | 200 |
| core_d25_p35_s0 | 32.15 | 569 | 528 | 34 | 200 |

## curator_deweight axis (d40/p55/s0)

Runs: 7. Pareto front: `dew_25`, `dew_60`, `dew_80`, `dew_100`

- **Utopia knee:** `dew_80` Q=23.28 geo_n=1039 good_med=21 bad_med=57 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 80, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `dew_80` Q=23.28 geo_n=1039 good_med=21 bad_med=57 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 80, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `dew_60` Q=31.27 geo_n=710 good_med=22 bad_med=105 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 60, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `dew_25` Q=32.15 geo_n=391 good_med=34 bad_med=230 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `dew_100` Q=0.00 geo_n=2150 good_med=None bad_med=None params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| dew_25 | 32.15 | 391 | 356 | 34 | 230 |
| dew_60 | 31.27 | 710 | 599 | 22 | 105 |
| dew_0 | 30.65 | 309 | 295 | 34 | 223 |
| dew_15 | 30.65 | 368 | 337 | 34 | 257 |
| dew_40 | 23.67 | 487 | 501 | 35 | 200 |
| dew_80 | 23.28 | 1039 | 994 | 21 | 57 |
| dew_100 | 0.00 | 2150 | 1994 | None | None |

## deweight at taste-zero (d0/p0/s0)

Runs: 4. Pareto front: `zerotaste_dew_25`, `zerotaste_dew_50`, `zerotaste_dew_100`

- **Utopia knee:** `zerotaste_dew_100` Q=0.00 geo_n=3209 good_med=None bad_med=None params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `zerotaste_dew_100` Q=0.00 geo_n=3209 good_med=None bad_med=None params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `zerotaste_dew_50` Q=31.75 geo_n=859 good_med=24 bad_med=156 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 50, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `zerotaste_dew_25` Q=32.15 geo_n=569 good_med=34 bad_med=200 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `zerotaste_dew_100` Q=0.00 geo_n=3209 good_med=None bad_med=None params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| zerotaste_dew_25 | 32.15 | 569 | 528 | 34 | 200 |
| zerotaste_dew_50 | 31.75 | 859 | 721 | 24 | 156 |
| zerotaste_dew_100 | 0.00 | 3209 | 2992 | None | None |
| zerotaste_dew_0 | -11.97 | 607 | 384 | 135 | 40 |

## max_n axis (from d40/p55/s0/cov0)

Runs: 7. Pareto front: `maxn_0`, `maxn_1500`, `maxn_3000`, `maxn_5000`, `maxn_8000`, `maxn_12000`, `maxn_20000`

- **Utopia knee:** `maxn_0` Q=32.15 geo_n=391 good_med=34 bad_med=230 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `maxn_0` Q=32.15 geo_n=391 good_med=34 bad_med=230 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `maxn_1500` Q=32.17 geo_n=359 good_med=32 bad_med=226 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 1500, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `maxn_1500` Q=32.17 geo_n=359 good_med=32 bad_med=226 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 1500, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `maxn_0` Q=32.15 geo_n=391 good_med=34 bad_med=230 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| maxn_1500 | 32.17 | 359 | 346 | 32 | 226 |
| maxn_0 | 32.15 | 391 | 356 | 34 | 230 |
| maxn_3000 | 32.15 | 391 | 356 | 34 | 230 |
| maxn_5000 | 32.15 | 391 | 356 | 34 | 230 |
| maxn_8000 | 32.15 | 391 | 356 | 34 | 230 |
| maxn_12000 | 32.15 | 391 | 356 | 34 | 230 |
| maxn_20000 | 32.15 | 391 | 356 | 34 | 230 |

## min_votes axis

Runs: 5. Pareto front: `minv_60`, `minv_100`

- **Utopia knee:** `minv_100` Q=30.26 geo_n=716 good_med=23 bad_med=96 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 100, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `minv_100` Q=30.26 geo_n=716 good_med=23 bad_med=96 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 100, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `minv_60` Q=33.21 geo_n=572 good_med=28 bad_med=142 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 60, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `minv_60` Q=33.21 geo_n=572 good_med=28 bad_med=142 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 60, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `minv_100` Q=30.26 geo_n=716 good_med=23 bad_med=96 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 100, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| minv_60 | 33.21 | 572 | 542 | 28 | 142 |
| minv_25 | 32.15 | 391 | 356 | 34 | 230 |
| minv_15 | 32.14 | 351 | 337 | 35 | 246 |
| minv_100 | 30.26 | 716 | 593 | 23 | 96 |
| minv_40 | 23.38 | 482 | 501 | 32 | 243 |

## bayesian_m axis

Runs: 6. Pareto front: `m_15`, `m_50`, `m_80`, `m_120`

- **Utopia knee:** `m_50` Q=32.19 geo_n=471 good_med=30 bad_med=218 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 50, 'com_share_cap': None}
- **Product:** `m_50` Q=32.19 geo_n=471 good_med=30 bad_med=218 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 50, 'com_share_cap': None}
- **Quality-lean:** `m_50` Q=32.19 geo_n=471 good_med=30 bad_med=218 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 50, 'com_share_cap': None}
- **Best quality:** `m_15` Q=33.12 geo_n=346 good_med=37 bad_med=253 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 15, 'com_share_cap': None}
- **Best mass:** `m_120` Q=25.13 geo_n=518 good_med=32 bad_med=184 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 120, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| m_15 | 33.12 | 346 | 295 | 37 | 253 |
| m_5 | 33.09 | 304 | 260 | 40 | 265 |
| m_50 | 32.19 | 471 | 509 | 30 | 218 |
| m_30 | 32.15 | 391 | 356 | 34 | 230 |
| m_80 | 25.71 | 502 | 542 | 29 | 202 |
| m_120 | 25.13 | 518 | 542 | 32 | 184 |

## coverage axis

Runs: 5. Pareto front: `cov_25`, `cov_50`, `cov_75`, `cov_100`

- **Utopia knee:** `cov_75` Q=29.62 geo_n=554 good_med=37 bad_med=146 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.75, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `cov_75` Q=29.62 geo_n=554 good_med=37 bad_med=146 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.75, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `cov_75` Q=29.62 geo_n=554 good_med=37 bad_med=146 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.75, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `cov_0` Q=32.15 geo_n=391 good_med=34 bad_med=230 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `cov_100` Q=14.73 geo_n=820 good_med=51 bad_med=95 params={'normie_depth': 40, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 1.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| cov_0 | 32.15 | 391 | 356 | 34 | 230 |
| cov_25 | 32.15 | 432 | 449 | 34 | 218 |
| cov_50 | 30.62 | 507 | 542 | 37 | 195 |
| cov_75 | 29.62 | 554 | 587 | 37 | 146 |
| cov_100 | 14.73 | 820 | 711 | 51 | 95 |

## explicit com_cap axis (depth40, purity0)

Runs: 5. Pareto front: `com_off_d40`, `com_0.2`

- **Utopia knee:** `com_off_d40` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `com_off_d40` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `com_off_d40` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `com_off_d40` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `com_off_d40` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| com_off_d40 | 32.14 | 534 | 478 | 35 | 198 |
| com_0.2 | 32.14 | 534 | 478 | 35 | 198 |
| com_0.11 | 31.64 | 427 | 427 | 35 | 304 |
| com_0.15 | 31.62 | 473 | 417 | 37 | 206 |
| com_0.08 | 30.65 | 384 | 326 | 34 | 273 |

## purity axis (depth40)

Runs: 8. Pareto front: `pur_axis_0`, `pur_axis_20`, `pur_axis_35`, `pur_axis_55`, `pur_axis_75`

- **Utopia knee:** `pur_axis_0` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Product:** `pur_axis_0` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Quality-lean:** `pur_axis_0` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best quality:** `pur_axis_75` Q=33.67 geo_n=193 good_med=32 bad_med=200 params={'normie_depth': 40, 'normie_purity': 75, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}
- **Best mass:** `pur_axis_0` Q=32.14 geo_n=534 good_med=35 bad_med=198 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30, 'com_share_cap': None}

| label | Q | geo_n | med_n | good_med | bad_med |
|---|---:|---:|---:|---:|---:|
| pur_axis_75 | 33.67 | 193 | 214 | 32 | 200 |
| pur_axis_55 | 32.15 | 391 | 356 | 34 | 230 |
| pur_axis_0 | 32.14 | 534 | 478 | 35 | 198 |
| pur_axis_20 | 32.14 | 534 | 478 | 35 | 198 |
| pur_axis_35 | 32.14 | 534 | 478 | 35 | 198 |
| pur_axis_45 | 32.14 | 518 | 465 | 35 | 198 |
| pur_axis_90 | 28.70 | 100 | 90 | 29 | 93 |
| pur_axis_65 | 26.36 | 272 | 288 | 34 | 221 |

## Implications for simplified rebuild

- **Keep `max_n`** (max ratings / Kish ceiling): it is a strong obscure-vs-popular lever; `0` = off.
- Query **purity=0 ⇒ com cap off** (fixed). Sliders at 0 ⇒ equal weight over all percentile users (not mint-only).
- Prefer **weighted curator scores** (`curator_deweight`) over equal-elite gate mode; core defaults use deweight=25 (expo=1).
- Prefer utopia/quality-lean picks from core grid as UI defaults; expose max_n + min_votes + m + deweight.
- Coverage=0 remains preferred for obscure literary discovery unless mass metrics demand otherwise.

Full data: `pareto_post_fix.json`.


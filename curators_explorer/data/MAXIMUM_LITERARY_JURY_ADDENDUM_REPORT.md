# Maximum Literary Jury — Correction & Triage Addendum

- Seed `20260827`; full p65 core n=3286 (payload overlap 2438); old artifacts untouched.

## Audit correction being tested

The old corepres_* frontier dropped 848 trusted p65_s25 members (only the 2,438 spectral-payload members were kept). This addendum preserves ALL 3,286 raw core users and adds model-ranked halo users from the payload. The pairwise scorer always uses the original build_pairs route, so non-payload users contribute their pairs.

## Correct full-p65 frontier (all juries contain all 3,286 core users)

| jury | n | pos50 | exact50 | broad50 | anti50 | half-J50 |
|---|---:|---:|---:|---:|---:|---:|
| fullcore_10000 | 10000 | 22 | 14 | 22 | 1 | 0.49 |
| fullcore_15000 | 15000 | 16 | 11 | 16 | 0 | 0.57 |
| fullcore_20000 | 20000 | 14 | 9 | 14 | 0 | 0.57 |
| fullcore_30000 | 30000 | 8 | 6 | 8 | 1 | 0.46 |
| fullcore_3286 | 3286 | 43 | 23 | 43 | 0 | 0.69 |
| fullcore_40000 | 40000 | 5 | 3 | 5 | 2 | 0.53 |
| fullcore_5000 | 5000 | 40 | 21 | 40 | 0 | 0.70 |
| fullcore_60000 | 60000 | 3 | 2 | 3 | 3 | 0.50 |
| fullcore_8000 | 8000 | 26 | 15 | 26 | 1 | 0.50 |

## Full-core model-halo vs random-halo controls

| size | halo type | pos50 mean (min-max) | anti50 mean (min-max) | half-J50 mean |
|---|---:|---:|---:|---:|
| 10000 | model-halo | 22 | 1 | 0.49 |
| 10000 | random-halo | 19.2 (18-21) | 17.6 (15-20) | 0.56 |
| 20000 | model-halo | 14 | 0 | 0.57 |
| 20000 | random-halo | 10.6 (10-12) | 22.8 (19-27) | 0.59 |
| 30000 | model-halo | 8 | 1 | 0.46 |
| 30000 | random-halo | 4.4 (3-6) | 25.6 (21-29) | 0.61 |

## Deep-mint expansion frontier (all juries contain all 19,841 source users)

| jury | n | pos50 | exact50 | broad50 | anti50 | half-J50 |
|---|---:|---:|---:|---:|---:|---:|
| deep_19841 | 19841 | 26 | 12 | 26 | 0 | 0.64 |
| deep_25000 | 25000 | 20 | 11 | 20 | 0 | 0.59 |
| deep_30000 | 30000 | 16 | 10 | 16 | 0 | 0.58 |
| deep_40000 | 40000 | 12 | 9 | 12 | 0 | 0.54 |
| deep_50000 | 50000 | 9 | 7 | 9 | 0 | 0.46 |
| deep_60000 | 60000 | 8 | 6 | 8 | 1 | 0.56 |

## Threeway-classic expansion frontier (all juries contain all 31,803 source users)

| jury | n | pos50 | exact50 | broad50 | anti50 | half-J50 |
|---|---:|---:|---:|---:|---:|---:|
| threeway_31803 | 31803 | 19 | 9 | 19 | 0 | 0.68 |
| threeway_35000 | 35000 | 14 | 8 | 14 | 0 | 0.60 |
| threeway_40000 | 40000 | 10 | 7 | 10 | 0 | 0.54 |
| threeway_50000 | 50000 | 6 | 3 | 6 | 0 | 0.58 |
| threeway_60000 | 60000 | 5 | 3 | 5 | 0 | 0.51 |
| threeway_80000 | 80000 | 5 | 3 | 5 | 2 | 0.54 |

## Simple committee populations

| candidate | n | A count | B count | C count | pos50 | exact50 | anti50 | half-J50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| committee_AnB | 11582 | 11582 | 11582 | 2368 | 30 | 14 | 0 | 0.61 |
| committee_AuB | 40062 | 19841 | 31803 | 3521 | 16 | 10 | 0 | 0.62 |
| committee_p65_plus_B | 32241 | 12020 | 31803 | 3192 | 18 | 10 | 0 | 0.61 |
| committee_union_ABCs | 41470 | 19841 | 31803 | 4929 | 13 | 8 | 0 | 0.58 |
| committee_vote2_ABCs | 12735 | 12016 | 12301 | 3521 | 30 | 12 | 0 | 0.59 |
| committee_vote3_ABCs | 2368 | 2368 | 2368 | 2368 | 44 | 22 | 0 | 0.71 |

## Optional committee expansion

- Gate passed: committee base `committee_p65_plus_B` (n=32241); expansions [40000, 60000, 80000].

| jury | n | pos50 | anti50 | half-J50 |
|---|---:|---:|---:|---:|
| committee_p65_plus_B_40000 | 40000 | 11 | 0 | 0.58 |
| committee_p65_plus_B_60000 | 60000 | 5 | 0 | 0.53 |
| committee_p65_plus_B_80000 | 80000 | 6 | 1 | 0.55 |

## Triage conclusion

### A. Did preserving the missing 848 p65 users materially improve the previous 10k/20k frontier?
- fullcore_10000 pos50=22 (old payload-only corepres_10000 was 19). fullcore_20000 pos50=14 (old payload-only corepres_20000 was 11).

### B. Can the 19,841 deep-mint population be expanded past 20k?
- deep_25000: pos50=20, anti50=0
- deep_30000: pos50=16, anti50=0
- deep_40000: pos50=12, anti50=0

### C. Can the 31,803 threeway-classic population be expanded beyond ~32k?
- threeway_35000: pos50=14, anti50=0
- threeway_40000: pos50=10, anti50=0
- threeway_50000: pos50=6, anti50=0
- threeway_60000: pos50=5, anti50=0
- threeway_80000: pos50=5, anti50=2

### D. Do simple intersections/unions/votes beat their sources?
- committee_AnB: n=11582, pos50=30, anti50=0
- committee_AuB: n=40062, pos50=16, anti50=0
- committee_p65_plus_B: n=32241, pos50=18, anti50=0
- committee_union_ABCs: n=41470, pos50=13, anti50=0
- committee_vote2_ABCs: n=12735, pos50=30, anti50=0
- committee_vote3_ABCs: n=2368, pos50=44, anti50=0

### E. Largest observed jury under the candidates tested here

| threshold | largest observed jury | n | pos50 | anti50 |
|---|---|---:|---:|---:|
| pos50>=20 & anti50<=2 | deep_25000 | 25000 | 20 | 0 |
| pos50>=15 & anti50<=2 | committee_AuB | 40062 | 16 | 0 |
| pos50>=10 & anti50<=2 | committee_union_ABCs | 41470 | 13 | 0 |

These are largest *observed* under the candidates tested in this addendum, not universal maxima.


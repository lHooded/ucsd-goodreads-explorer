# Jury Consensus Venn Census — ranked-head evidence

- Seed `20260828`; A=deep_mint_all (19,841), B=threeway_classic (31,803), C=rebuilt_hard (4,929).
- Probes (pos50/exact/broad/anti) are descriptors/annotations only. No objective combines them. The ranked heads are the primary evidence for human inspection.

## 1. Seven exclusive Venn regions

| region | n | A? | B? | C? |
|---|---:|---|---|---|
| A_only | 7825 | Y | - | - |
| B_only | 19502 | - | Y | - |
| C_only | 1408 | - | - | Y |
| AB_only | 9214 | Y | Y | - |
| AC_only | 434 | Y | - | Y |
| BC_only | 719 | - | Y | Y |
| ABC | 2368 | Y | Y | Y |

Sum = 41470 = A∪B∪C (41,470); ABC=2368; AB_only+ABC = A∩B = 11582.

## 2. Region metrics (direct equal-vote pairwise)

| region | n | pos50 | exact50 | broad50 | anti50 | half-J50 | uniq auth@50 | max auth works@50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A_only | 7825 | 21 | 15 | 21 | 0 | 0.59 | 42 | 3 |
| B_only | 19502 | 13 | 6 | 13 | 1 | 0.62 | 37 | 4 |
| C_only | 1408 | 19 | 8 | 19 | 0 | 0.61 | 31 | 7 |
| AB_only | 9214 | 26 | 14 | 26 | 0 | 0.62 | 38 | 5 |
| AC_only | 434 | 38 | 23 | 38 | 0 | 0.48 | 42 | 5 |
| BC_only | 719 | 34 | 14 | 34 | 0 | 0.55 | 31 | 11 |
| ABC | 2368 | 44 | 22 | 44 | 0 | 0.66 | 33 | 6 |

## 3. Fixed agreement ladder

| tier | population | n (reproduced?) | pos50 | exact50 | broad50 | anti50 |
|---|---|---:|---:|---:|---:|---:|
| agreement3 | ABC | 2368 (ok) | 44 | 22 | 44 | 0 |
| agreement2 | AB_only ∪ AC_only ∪ BC_only ∪ ABC | 12735 (ok) | 30 | 12 | 30 | 0 |
| agreement1 | union of all seven regions | 41470 (ok) | 13 | 8 | 13 | 0 |
| AnB | AB_only ∪ ABC | 11582 (ok) | 30 | 14 | 30 | 0 |

## 4. Region contribution table

| population | A_only | B_only | C_only | AB_only | AC_only | BC_only | ABC |
|---|---:|---:|---:|---:|---:|---:|---:|
| p65_reference | 333 | 0 | 0 | 1576 | 105 | 0 | 1272 |
| A_deep_mint | 7825 | 0 | 0 | 9214 | 434 | 0 | 2368 |
| B_threeway | 0 | 19502 | 0 | 9214 | 0 | 719 | 2368 |
| C_rebuilt | 0 | 0 | 1408 | 0 | 434 | 719 | 2368 |
| AnB | 0 | 0 | 0 | 9214 | 0 | 0 | 2368 |
| vote2 | 0 | 0 | 0 | 9214 | 434 | 719 | 2368 |
| vote3 | 0 | 0 | 0 | 0 | 0 | 0 | 2368 |
| unionABC | 7825 | 19502 | 1408 | 9214 | 434 | 719 | 2368 |

## Interpretive caution

Probe sets may undercount translated literature, non-English literary traditions, contemporary literary fiction, genre works with substantial literary standing, children's classics, and serious nonfiction depending on the list. Do not read 'higher pos50' as 'more literary'; distinguish probe coverage, anti contamination, actual head contents, stability, and author diversity separately. No manual reclassification was performed in code; the heads are for human inspection.


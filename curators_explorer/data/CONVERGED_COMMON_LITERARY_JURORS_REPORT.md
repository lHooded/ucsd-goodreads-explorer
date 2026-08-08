# Converged Common Literary Jurors — report

- Seed `20260831`. Established convergence reused: research_jury_ensemble_reversal.run_jury (BETA=2.5, MAX_STAGES=8, ITERATIONS=20, gain-hard LADDER_RATE=0.05, MIN_REMAINING_FRACTION=0.05, retained target 1.01).

## Popular-book benchmark

- Rule: global rating count in [500, 120000]; deterministic support-stratified cap to 20000 (20 equal support strata, 1000 each). No literary labels or reference scores used.
- Candidates: 26393; selected: 20000; support min/median/max 500/1020/119871

## Corrected known-group common-L (benchmark universe)

| group | n_scoreable | median | p10 | p25 | p75 | frac>=.6 | med hi | med lo | med testable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ABC | 2202 | 0.710 | 0.591 | 0.652 | 0.768 | 0.883 | 41 | 33 | 400 |
| p65 | 2909 | 0.708 | 0.589 | 0.645 | 0.765 | 0.878 | 30 | 27 | 400 |
| AnB | 10097 | 0.690 | 0.564 | 0.626 | 0.750 | 0.824 | 30 | 21 | 400 |
| vote2 | 10711 | 0.689 | 0.562 | 0.625 | 0.750 | 0.821 | 30 | 22 | 400 |
| A_only | 2158 | 0.653 | 0.520 | 0.583 | 0.717 | 0.701 | 17 | 27 | 400 |
| B_only | 10677 | 0.658 | 0.531 | 0.591 | 0.723 | 0.723 | 34 | 27 | 400 |
| AB_only | 7895 | 0.684 | 0.557 | 0.618 | 0.745 | 0.807 | 28 | 19 | 400 |
| AuB | 23546 | 0.673 | 0.541 | 0.605 | 0.736 | 0.765 | 30 | 25 | 400 |
| fandom_anti10k | 3737 | 0.551 | 0.403 | 0.476 | 0.629 | 0.342 | 21 | 15 | 320 |
| random10k | 7325 | 0.589 | 0.431 | 0.502 | 0.666 | 0.465 | 20 | 17 | 325 |

| pair | n | pearson | spearman |
|---|---:|---:|---:|
| R1_ABC_vs_R2_p65 | 152517 | 0.839 | 0.829 |
| R1_ABC_vs_R3_AnB | 153666 | 0.722 | 0.714 |
| R2_p65_vs_R3_AnB | 159206 | 0.777 | 0.773 |

## Seed juries (corrected common score)

| seed | n | median L | p10 | frac>=.6 | noneABC |
|---|---:|---:|---:|---:|---:|
| Seed_L5000 | 5000 | 0.811 | 0.790 | 1.000 | 0.486 |
| Seed_L10000 | 10000 | 0.785 | 0.758 | 1.000 | 0.538 |
| Seed_L20000 | 20000 | 0.753 | 0.718 | 1.000 | 0.598 |

## Convergence outcomes (established dynamics)

| endpoint | stop | stages | raw support | Kish | w-top1% | weighted median L | weighted p10 | frac weight L>=.6 | frac weight L<.55 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Conv_L5000 | evidence_floor | 6 | 16350 | 10026 | 0.022 | 0.801 | 0.470 | 0.790 | 0.173 |
| Conv_L10000 | evidence_floor | 7 | 13581 | 9555 | 0.017 | 0.786 | 0.758 | 0.997 | 0.003 |
| Conv_L20000 | evidence_floor | 6 | 15696 | 11156 | 0.017 | 0.748 | 0.717 | 0.998 | 0.002 |

## 90%-seed convergence stability

| endpoint | rep | book J50 | book J200 | book rho200 | weighted median L |
|---|---:|---:|---:|---:|---:|
| Conv_L5000 | rep0 | 0.50 | 0.78 | 0.764 | 0.644 |
| Conv_L5000 | rep1 | 0.70 | 0.89 | 0.786 | 0.637 |
| Conv_L5000 | rep2 | 0.64 | 0.61 | 0.803 | 0.638 |
| Conv_L10000 | rep0 | 0.92 | 0.95 | 0.967 | 0.781 |
| Conv_L10000 | rep1 | 0.92 | 0.95 | 0.959 | 0.781 |
| Conv_L10000 | rep2 | 0.96 | 0.94 | 0.963 | 0.781 |
| Conv_L20000 | rep0 | 0.76 | 0.90 | 0.800 | 0.749 |
| Conv_L20000 | rep1 | 0.76 | 0.88 | 0.784 | 0.750 |
| Conv_L20000 | rep2 | 0.78 | 0.89 | 0.794 | 0.749 |

## Obscure-book coverage (converged endpoints)

| endpoint | band 20-49 raw>=1 | >=3 | qm>=0.5 | qm>=1 | band 100-249 raw>=1 | qm>=1 |
|---|---:|---:|---:|---:|---:|---:|
| Conv_L5000 | 0.75 | 0.26 | 0.02 | 0.01 | 0.99 | 0.05 |
| Conv_L10000 | 0.72 | 0.22 | 0.05 | 0.01 | 0.99 | 0.05 |
| Conv_L20000 | 0.66 | 0.15 | 0.04 | 0.00 | 0.98 | 0.04 |

## Seed vs converged

| size | seed median L | conv weighted median L | seed head pos50 | conv head pos50 | conv Kish | 20-49 raw>=1 | 20-49 qm>=1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5000 | 0.811 | 0.801 | 34 | 10 | 10026 | 0.75 | 0.01 |
| 10000 | 0.785 | 0.786 | 28 | 16 | 9555 | 0.72 | 0.01 |
| 20000 | 0.753 | 0.748 | 23 | 10 | 11156 | 0.66 | 0.00 |

## Interpretation

Do convergence and the common-L endpoint preserve literary character? See converged heads in CONVERGED_COMMON_LITERARY_JUROR_HEADS.md and the weighted-L distributions above. No convergence parameters were tuned by size.


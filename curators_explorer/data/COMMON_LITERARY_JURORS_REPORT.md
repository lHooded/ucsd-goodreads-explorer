# Common Literary Juror Discovery — report

- Seed `20260830`. Reverse-engineered common-reference scoring; no semantic optimisation.

## References

- R1_ABC: n=2368 ranked works=2000
- R2_p65: n=3286 ranked works=2000
- R3_AnB: n=11582 ranked works=2000

## Cross-reference agreement about users

| pair | n | pearson | spearman | median abs diff |
|---|---:|---:|---:|---:|
| R1_ABC_vs_R2_p65 | 130874 | 0.645 | 0.629 | 0.067 |
| R1_ABC_vs_R3_AnB | 121083 | 0.494 | 0.480 | 0.080 |
| R2_p65_vs_R3_AnB | 119790 | 0.684 | 0.667 | 0.059 |

## Common-score distributions for known groups

| group | n_in_universe | median | p10 | p25 | p75 | frac>=.6 |
|---|---:|---:|---:|---:|---:|---:|
| ABC | 2368 | 0.680 | 0.559 | 0.618 | 0.739 | 0.811 |
| p65 | 3286 | 0.681 | 0.563 | 0.620 | 0.740 | 0.821 |
| AnB | 11582 | 0.653 | 0.526 | 0.588 | 0.714 | 0.713 |
| vote2 | 12226 | 0.652 | 0.525 | 0.586 | 0.713 | 0.708 |
| A_only | 2304 | 0.607 | 0.484 | 0.541 | 0.669 | 0.530 |
| B_only | 10861 | 0.603 | 0.485 | 0.543 | 0.666 | 0.520 |
| AB_only | 9214 | 0.645 | 0.518 | 0.580 | 0.707 | 0.686 |
| AuB | 25391 | 0.626 | 0.500 | 0.560 | 0.691 | 0.610 |
| fandom_anti10k | 5493 | 0.505 | 0.384 | 0.439 | 0.572 | 0.167 |
| random10k | 10000 | 0.536 | 0.404 | 0.465 | 0.609 | 0.279 |

## Nested candidate frontier

| jury | n | median L | p10 | p75 | frac>=.6 | median ev | none-of-ABC frac | pos50 | anti50 | exact50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| L2500 | 2500 | 0.783 | 0.761 | 0.805 | 1.000 | 370 | 0.222 | 39 | 0 | 24 |
| L5000 | 5000 | 0.757 | 0.731 | 0.783 | 1.000 | 360 | 0.292 | 37 | 0 | 23 |
| L10000 | 10000 | 0.725 | 0.696 | 0.757 | 1.000 | 345 | 0.381 | 35 | 0 | 20 |
| L15000 | 15000 | 0.706 | 0.672 | 0.740 | 1.000 | 324 | 0.443 | 31 | 1 | 18 |
| L20000 | 20000 | 0.690 | 0.654 | 0.725 | 1.000 | 320 | 0.487 | 25 | 2 | 14 |
| L30000 | 30000 | 0.666 | 0.625 | 0.706 | 1.000 | 308 | 0.554 | 21 | 2 | 12 |
| L40000 | 40000 | 0.646 | 0.600 | 0.690 | 0.912 | 300 | 0.606 | 17 | 3 | 10 |

## Stability (5 half splits)

| jury | half-J50 mean | half-J200 mean | rho200 mean |
|---|---:|---:|---:|
| L2500 | 0.76 | 0.76 | 0.712 |
| L5000 | 0.76 | 0.76 | 0.686 |
| L10000 | 0.74 | 0.74 | 0.734 |
| L20000 | 0.60 | 0.73 | 0.648 |
| L40000 | 0.70 | 0.69 | 0.627 |

## Self-convergence trajectories (label-free T_N)

| jury | transition | retention | book J50 | book J200 | book rho200 | median L | frac L>=.6 |
|---|---|---:|---:|---:|---:|---:|---:|
| L5000 | J0->J1 | 0.451 | 0.68 | 0.71 | 0.708 | 0.723 | 0.853 |
| L5000 | J1->J2 | 0.337 | 0.74 | 0.76 | 0.696 | 0.701 | 0.740 |
| L5000 | J2->J3 | 0.228 | 0.68 | 0.81 | 0.663 | 0.673 | 0.611 |
| L10000 | J0->J1 | 0.441 | 0.58 | 0.72 | 0.602 | 0.687 | 0.779 |
| L10000 | J1->J2 | 0.339 | 0.66 | 0.77 | 0.676 | 0.668 | 0.657 |
| L10000 | J2->J3 | 0.215 | 0.78 | 0.78 | 0.737 | 0.633 | 0.493 |
| L20000 | J0->J1 | 0.455 | 0.56 | 0.69 | 0.525 | 0.648 | 0.632 |
| L20000 | J1->J2 | 0.357 | 0.74 | 0.74 | 0.723 | 0.629 | 0.523 |
| L20000 | J2->J3 | 0.268 | 0.82 | 0.79 | 0.812 | 0.604 | 0.416 |

## Perturbation / basin test (L10000, 10% random replacement)

| rep | P2∩L10 | P2∩J1 | P2∩J2 | book J50 vs J2 | book J200 vs J2 | median L |
|---|---:|---:|---:|---:|---:|---:|
| pert0 | 0.308 | 0.405 | 0.498 | 0.76 | 0.81 | 0.666 |
| pert1 | 0.288 | 0.377 | 0.488 | 0.76 | 0.78 | 0.662 |
| pert2 | 0.282 | 0.379 | 0.468 | 0.68 | 0.77 | 0.662 |

## Fandom self-convergence control

- retention F0→F2: 0.037; book J50: 0.70; book J200: 0.66; median common-L at F2: 0.519

## Obscure-book coverage (by validated jurors)

| jury | band 20-49 >=1 | >=3 | >=5 | median | band 100-249 >=1 | >=3 |
|---|---:|---:|---:|---:|---:|---:|
| L2500 | 0.21 | 0.02 | 0.00 | 0.0 | 0.48 | 0.17 |
| L5000 | 0.33 | 0.06 | 0.01 | 0.0 | 0.64 | 0.32 |
| L10000 | 0.50 | 0.15 | 0.05 | 0.0 | 0.81 | 0.54 |
| L15000 | 0.61 | 0.25 | 0.10 | 1.0 | 0.89 | 0.68 |
| L20000 | 0.69 | 0.33 | 0.16 | 1.0 | 0.93 | 0.76 |
| L30000 | 0.79 | 0.47 | 0.28 | 2.0 | 0.97 | 0.86 |
| L40000 | 0.85 | 0.58 | 0.39 | 3.0 | 0.98 | 0.91 |
| J3_5000 | 0.30 | 0.01 | 0.00 | 0.0 | 0.77 | 0.35 |
| J3_10000 | 0.53 | 0.08 | 0.01 | 1.0 | 0.94 | 0.71 |
| J3_20000 | 0.74 | 0.28 | 0.07 | 1.0 | 0.98 | 0.90 |

## Key naturality table

| jury | n | median L | half-J50 | self-ret J0→J1 | J1→J2 | J2→J3 | book J50 J2→J3 | 20-49 >=1 | 20-49 >=3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| L5000 | 5000 | 0.757 | 0.76 | 0.451 | 0.337 | 0.228 | 0.68 | 0.33 | 0.06 |
| L10000 | 10000 | 0.725 | 0.74 | 0.441 | 0.339 | 0.215 | 0.78 | 0.50 | 0.15 |
| L20000 | 20000 | 0.690 | 0.60 | 0.455 | 0.357 | 0.268 | 0.82 | 0.69 | 0.33 |

## Answers

1. Common reader direction: see cross-reference table.
2. Rediscovery outside A/B/C: see 'none-of-ABC frac' in the frontier table.
3. Individual quality vs size: see median L / frac>=.6 across the frontier.
4. Actual literary rankings: see COMMON_LITERARY_JUROR_HEADS.md (full top-50).
5. Stability: see stability table.
6-7. Self-consistency/convergence: see trajectory table.
8. Basin attraction: see perturbation table.
9. Control: fandom self-converges too; self-convergence is generic to coherent taste communities, not proof of literariness.
10. Coverage: see coverage table.
11. Descriptive candidates: see key naturality table.


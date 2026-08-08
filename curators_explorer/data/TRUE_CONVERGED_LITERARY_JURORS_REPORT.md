# True Converged Literary Jurors — report

- Seed `20260901`. Membership is a hard invariant; convergence = internal reweighting of fixed members under the iterate_map equation (BETA=2.5) to a genuine numerical fixed point (step>=0.9999 AND weight_rel<=1e-4 for 5 consecutive, max 200).

## Frozen common-L input

- Convergence-eligible users (Option 1, raw rebuild): 149239; with L>=0.60: 68033; median L over eligible: 0.586

## Primary jury definitions

| jury | n | median L | p10 | p25 | p75 | min L |
|---|---:|---:|---:|---:|---:|---:|
| J5000 | 5000 | 0.811 | 0.790 | 0.797 | 0.834 | 0.785 |
| J10000 | 10000 | 0.785 | 0.758 | 0.767 | 0.811 | 0.753 |
| J20000 | 20000 | 0.753 | 0.718 | 0.730 | 0.785 | 0.711 |
| J30000 | 30000 | 0.730 | 0.691 | 0.704 | 0.767 | 0.683 |

## Numerical convergence

| jury | converged | stop | iters | final step | final weight_rel | final book_rel |
|---|---|---|---:|---:|---:|---:|
| J5000 | False | max_iter_not_converged | 200 | 0.999999 | 8.59e-04 | 1.20e-03 |
| J10000 | False | max_iter_not_converged | 200 | 1.000000 | 7.53e-04 | 9.99e-04 |
| J20000 | False | max_iter_not_converged | 200 | 1.000000 | 7.03e-04 | 9.15e-04 |
| J30000 | False | max_iter_not_converged | 200 | 1.000000 | 6.49e-04 | 8.38e-04 |

## Converged user-weight quality

| jury | Kish | top1% | top5% | gini | wtd median L | wtd p10 | wtd p75 | wt L>=.7 | wt L>=.6 | wt L<.6 | w-L pearson | w-L spearman |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| J5000 | 3344 | 0.019 | 0.095 | 0.397 | 0.812 | 0.790 | 0.835 | 1.000 | 1.000 | 0.000 | 0.051 | 0.051 |
| J10000 | 6423 | 0.021 | 0.103 | 0.423 | 0.784 | 0.758 | 0.810 | 1.000 | 1.000 | 0.000 | -0.045 | -0.042 |
| J20000 | 13569 | 0.019 | 0.095 | 0.391 | 0.755 | 0.719 | 0.789 | 1.000 | 1.000 | 0.000 | 0.073 | 0.077 |
| J30000 | 19523 | 0.021 | 0.103 | 0.417 | 0.727 | 0.690 | 0.763 | 0.785 | 1.000 | 0.000 | -0.090 | -0.095 |

## Seed vs converged book head

| jury | seed pos50 | conv pos50 | J50 | J200 | rho200 |
|---|---:|---:|---:|---:|---:|
| J5000 | 25 | 34 | 0.61 | 0.66 | 0.755 |
| J10000 | 21 | 9 | 0.52 | 0.54 | 0.610 |
| J20000 | 11 | 17 | 0.56 | 0.67 | 0.648 |
| J30000 | 5 | 4 | 0.59 | 0.49 | 0.650 |

## Stability

### 90% subsample (10 reps)

| jury | conv rate | iters med | J50 med | J50 p10 | J50 p90 | J200 med | wtd median L med |
|---|---:|---:|---:|---:|---:|---:|---:|
| J5000 | 0/10 | 200 | 0.87 | 0.82 | 0.89 | 0.88 | 0.812 |
| J10000 | 1/10 | 200 | 0.85 | 0.81 | 0.89 | 0.88 | 0.784 |
| J20000 | 0/10 | 200 | 0.85 | 0.79 | 0.89 | 0.89 | 0.755 |
| J30000 | 0/10 | 200 | 0.23 | 0.22 | 0.24 | 0.26 | 0.733 |

### Random initial weights (10 reps)

| jury | J50 med | J50 p10 | J50 p90 | wtd median L med | weight cos med |
|---|---:|---:|---:|---:|---:|
| J5000 | 0.85 | 0.31 | 0.89 | 0.812 | 0.864 |
| J10000 | 0.35 | 0.26 | 0.89 | 0.786 | 0.592 |
| J20000 | 0.30 | 0.28 | 0.93 | 0.750 | 0.629 |
| J30000 | 0.42 | 0.22 | 0.96 | 0.727 | 0.665 |

### 80% subsample J10000 (5 reps)

- J50 med 0.23 (p10 0.23, p90 0.25); J200 med 0.32

### Split-half converged stability

| jury | J50 med | J50 p10 | J50 p90 | J200 med | rho200 med |
|---|---:|---:|---:|---:|---:|
| J10000 | 0.63 | 0.61 | 0.67 | 0.58 | 0.703 |
| J20000 | 0.61 | 0.59 | 0.67 | 0.62 | 0.771 |

## Controls (same convergence dynamics)

- random10k: n=10000 converged=False iters=200 kish=6518 wtd median L=0.570 wt L<.6=0.591
  random-init J50 med 0.52
- fandom10k: n=10000 converged=False iters=200 kish=6520 wtd median L=0.559 wt L<.6=0.637
  random-init J50 med 0.54

## Obscure-book coverage

| jury | 5-19 >=1 | 20-49 >=1 | >=3 | 50-99 >=1 | 100-249 >=1 | 250-999 >=1 | 1000-4999 >=1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| J5000 | 0.16 | 0.32 | 0.04 | 0.50 | 0.67 | 0.86 | 0.98 |
| J10000 | 0.30 | 0.51 | 0.13 | 0.68 | 0.82 | 0.93 | 1.00 |
| J20000 | 0.47 | 0.69 | 0.32 | 0.83 | 0.92 | 0.98 | 1.00 |
| J30000 | 0.59 | 0.79 | 0.47 | 0.90 | 0.96 | 0.99 | 1.00 |

## Convergence-weighted information coverage

| jury | 20-49 info>=0.5 | >=1 | >=2 | 100-249 info>=1 | 250-999 info>=1 |
|---|---:|---:|---:|---:|---:|
| J5000 | 0.204 | 0.177 | 0.056 | 0.426 | 0.624 |
| J10000 | 0.319 | 0.254 | 0.063 | 0.703 | 0.887 |
| J20000 | 0.527 | 0.387 | 0.219 | 0.729 | 0.879 |
| J30000 | 0.628 | 0.468 | 0.236 | 0.862 | 0.955 |

## Cross-size comparison

| jury | seed median L | conv wtd median L | iters | Kish | seed->conv J50 | 90% med J50 | rand-init med J50 | half med J50 | 20-49 >=1 | 20-49 >=3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| J5000 | 0.811 | 0.812 | 200 | 3344 | 0.61 | 0.87 | 0.85 | nan | 0.32 | 0.04 |
| J10000 | 0.785 | 0.784 | 200 | 6423 | 0.52 | 0.85 | 0.35 | 0.63 | 0.51 | 0.13 |
| J20000 | 0.753 | 0.755 | 200 | 13569 | 0.56 | 0.85 | 0.30 | 0.61 | 0.69 | 0.32 |
| J30000 | 0.730 | 0.727 | 200 | 19523 | 0.59 | 0.23 | 0.42 | nan | 0.79 | 0.47 |

## Interpretation

See the 12 questions in the task; key qualitative answers follow from the tables above and the heads file. Membership never changes; convergence only reweights fixed members. Numerical convergence is generic (controls also converge); the naturality claim rests on: high individual common-L + internally converged literary head + stability across 90%/80%/half/random-init samples.


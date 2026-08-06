# Target-excluded enthusiast-selection calibration

## Outcome

This audit removes the target interaction from the reader embedding and predicts recorded interaction out of fold. Rating values remain hidden until after propensity scores are fixed.

The model calibrated **90** books and achieved median held-out interaction AUC **0.814**. AUC measures whether co-reading features distinguish recorded readers from jury members with no recorded interaction; it is not a causal exposure validation.

## Calibration comparison

| retained | method | Γ q50 | Γ q75 | Γ q90 | Γ q95 | mean esteem inflation |
|---:|---|---:|---:|---:|---:|---:|
| 25% | old centroid | 1.21 | 1.52 | 2.04 | 2.42 | 3.2 pp |
| 25% | target-excluded cross-fit | 1.80 | 2.05 | 2.52 | 2.90 | 9.4 pp |
| 50% | old centroid | 1.10 | 1.25 | 1.40 | 1.45 | 1.2 pp |
| 50% | target-excluded cross-fit | 1.34 | 1.53 | 1.95 | 2.10 | 5.7 pp |
| 75% | old centroid | 1.05 | 1.13 | 1.18 | 1.23 | 0.5 pp |
| 75% | target-excluded cross-fit | 1.16 | 1.28 | 1.44 | 1.48 | 3.2 pp |

## Sampling-noise reference

Random subsets of the same size were drawn 100 times per book. These one-sided Γ quantiles show how much apparent sensitivity arises from smaller samples alone.

| retained | observed Γ q50/q75/q90 | random-subset Γ q50/q75/q90 |
|---:|---:|---:|
| 25% | 1.80/2.05/2.52 | 1.01/1.21/1.47 |
| 50% | 1.34/1.53/1.95 | 1.00/1.12/1.25 |
| 75% | 1.16/1.28/1.44 | 1.00/1.07/1.14 |

## Interpretation

The 25% retention scenario is deliberately harsh: Γ=1.5 is below its median, while Γ=2 is near q75=2.05. Under 50% retention, Γ=1.5 is near q75=1.53 and Γ=2 is near q90=1.95. This supports using 1.5 as a moderate and 2 as a strong stress test, not as estimated truth. The random-subset row must be consulted before attributing the whole tail to enthusiast selection.

This improves leakage control but does not make selection identifiable. Absence of a Goodreads rating is not observed exposure, and the high-propensity subset is a stress-test analogue rather than a reconstruction of a rare book's missing readers.

## Recommendation

Retain Γ=1.5 as the primary moderate sensitivity bound and Γ=2 as the strong bound while q75/q90 under 25% retention are 2.05/2.52. Keep Γ sensitivity separate from ±u. Next test jury feature families and pair sampling seeds; revisit these thresholds only if those axes materially alter the calibration population.

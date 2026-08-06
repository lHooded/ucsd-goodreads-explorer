# Soft-jury reader-block bootstrap

## Design

The hard 4,929-person jury and the equal-mass bootstrap-inclusion jury are each resampled in whole-reader Poisson blocks through the same nine hard community partitions and exact expected-inclusion pair events.

- Mode: **full**; replicates: **2,000**.
- Candidate books: **1,157**.

| jury | rankable | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 | med top200 u80 | med eligibility | eligibility <80% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hard jury | 297 | 0.598 | 0.538 | 0.765 | 0.739 | 4.62 | 100% | 29 |
| soft jury q | 300 | 0.599 | 0.538 | 0.769 | 0.739 | 4.47 | 100% | 30 |

The soft jury improves mean Jaccard@200 by 0.0035 and lowers median top-200 `u80` by 0.15 points. These are modest gains: they support soft weights as the preferred point estimator, not a claim that the jury has been fundamentally redefined. The hard jury remains a required sensitivity path.

Conditional score widths must be interpreted with eligibility. This comparison tests reader-sample stability only; it does not re-bootstrap the soft weights or identify missing exposure.

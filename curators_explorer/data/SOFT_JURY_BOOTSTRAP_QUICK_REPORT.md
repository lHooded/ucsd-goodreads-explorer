# Soft-jury reader-block bootstrap

## Design

The hard 4,929-person jury and the equal-mass bootstrap-inclusion jury are each resampled in whole-reader Poisson blocks through the same nine hard community partitions and exact expected-inclusion pair events.

- Mode: **quick**; replicates: **16**.
- Candidate books: **1,157**.

| jury | rankable | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 | med top200 u80 | med eligibility | eligibility <80% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hard jury | 297 | 0.576 | 0.493 | 0.761 | 0.735 | 4.12 | 100% | 28 |
| soft jury q | 300 | 0.586 | 0.515 | 0.755 | 0.724 | 3.99 | 100% | 34 |

Conditional score widths must be interpreted with eligibility. This comparison tests reader-sample stability only; it does not re-bootstrap the soft weights or identify missing exposure.

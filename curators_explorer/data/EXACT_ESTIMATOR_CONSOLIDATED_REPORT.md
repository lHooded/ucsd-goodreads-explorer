# Consolidated exact estimator and uncertainty decision

## Decision

The exact expected-inclusion estimator replaces the arbitrary 12×12 hash sample. For a reader with H eligible 5-star and L eligible ≤3-star ratings, M=min(H,L,12), so each positive event receives M/H and each negative event M/L.

Report reader-block `u80` as the primary conditional `±u`, jury-composition `u80` as a second uncertainty component, and both eligibility probabilities separately. Do not yet collapse the two widths into one number: the campaigns were not a joint nested bootstrap.

## Completed evidence

- Reader-block replicates: **5,000**; jury-composition replicates: **5,000**.
- Exact rankable books: **297** from **1,146** tracked near-evidence candidates.
- Within the exact top 200, median reader `u80` is **4.62** points and median jury `u80` is **0.86** points.
- Median jury/reader width ratio is **0.205**. Reader sampling/evidence is therefore the larger uncertainty axis at present.
- Top-200 books below 80% eligibility: **29** under reader resampling and **5** under jury refits.

## Soft-jury implication

Bootstrap inclusion probabilities preserve exactly **4929** juror equivalents across 20,000 candidates. **3,963** users are selected in at least 99% of refits, **13,951** in at most 1%, and only **1,160** occupy the 10–90% boundary band. This supports a controlled soft-boundary ablation rather than a wholesale latent-jury rewrite.

## Interpretation

Eligibility is part of uncertainty, not a nuisance to hide. A high conditional score with low eligibility remains an underexposed candidate. Γ sensitivity for unobserved enthusiast selection remains a separate systematic-bias trajectory and is not included in either `u80`.

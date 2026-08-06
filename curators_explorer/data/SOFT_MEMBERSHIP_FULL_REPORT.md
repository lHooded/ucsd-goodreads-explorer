# Soft jury and community membership pilot

## Design

The hard jury is compared with bootstrap inclusion weights `q_u`. These weights sum to exactly 4,929 juror equivalents and remain bounded by one. Community alternatives use top-two cosine-centroid responsibilities summing to one per user; truncating at two prevents infinitesimal memberships from fabricating universal exposure.

- Mode: **full**; community partitions: **9**.
- Soft-jury nonzero users: **6,826**; Kish effective users: **5199.3**; total mass: **4929.0**.
- Exact hard baseline: **297** rankable books.

## Ablation results

| variant | rankable | gain/loss | J@50 | J@200 | RBO | score ρ | pop ρ | med partition u | med heterogeneity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hard jury / hard communities | 297 | +0/-0 | 1.000 | 1.000 | 1.000 | 1.000 | -0.536 | 1.94 | 0.00 |
| soft jury q / hard communities | 300 | +6/-3 | 0.923 | 0.942 | 0.935 | 0.999 | -0.542 | 1.75 | 0.00 |
| hard jury / top2 communities mean-max 0.90 | 301 | +9/-5 | 0.887 | 0.942 | 0.948 | 0.998 | -0.533 | 1.52 | 0.00 |
| soft jury q / top2 communities mean-max 0.90 | 303 | +10/-4 | 0.887 | 0.932 | 0.938 | 0.997 | -0.531 | 1.58 | 0.00 |
| hard jury / top2 communities mean-max 0.75 | 311 | +18/-4 | 0.887 | 0.869 | 0.891 | 0.991 | -0.524 | 1.42 | 0.00 |
| soft jury q / top2 communities mean-max 0.75 | 313 | +21/-5 | 0.786 | 0.852 | 0.878 | 0.990 | -0.543 | 1.43 | 0.00 |
| hard jury / top2 communities mean-max 0.60 | 323 | +30/-4 | 0.667 | 0.786 | 0.806 | 0.982 | -0.522 | 1.27 | 0.00 |
| soft jury q / top2 communities mean-max 0.60 | 320 | +27/-4 | 0.695 | 0.786 | 0.812 | 0.980 | -0.521 | 1.27 | 0.00 |

## Decision

Use bootstrap jury-inclusion probability as the preferred continuous jury weight, while retaining the hard 4,929-person cut as a sensitivity axis. The soft jury preserves exactly the same total mass and produces only modest head movement.

Do not make fuzzy community membership the default. The 0.90 mean-primary top-two version is useful as a conservative audit, but the 0.75 and 0.60 paths change eligibility and the ranking substantially while mechanically shrinking partition sensitivity. That is smoothing, not demonstrated discovery of a truer consensus.

## Guardrails

- A fall in estimated heterogeneity under fuzzy communities is partly mechanical; it is not by itself evidence of a truer consensus.
- Soft jury mass tests uncertainty at the existing jury boundary. It does not discover a new estimand or repair missing exposure.
- Community weights remain an audit/aggregation layer. They do not nominate books.
- Rankability gains are evidence gains, not automatic evidence of canonical status.

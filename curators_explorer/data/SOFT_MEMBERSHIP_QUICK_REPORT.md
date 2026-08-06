# Soft jury and community membership pilot

## Design

The hard jury is compared with bootstrap inclusion weights `q_u`. These weights sum to exactly 4,929 juror equivalents and remain bounded by one. Community alternatives use top-two cosine-centroid responsibilities summing to one per user; truncating at two prevents infinitesimal memberships from fabricating universal exposure.

- Mode: **quick**; community partitions: **9**.
- Soft-jury nonzero users: **6,826**; Kish effective users: **5199.3**; total mass: **4929.0**.
- Exact hard baseline: **297** rankable books.

## Ablation results

| variant | rankable | gain/loss | J@50 | J@200 | RBO | score ρ | pop ρ | med partition u | med heterogeneity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hard jury / hard communities | 297 | +0/-0 | 1.000 | 1.000 | 1.000 | 1.000 | -0.536 | 1.94 | 0.00 |
| soft jury q / hard communities | 300 | +6/-3 | 0.923 | 0.942 | 0.935 | 0.999 | -0.542 | 1.75 | 0.00 |
| hard jury / top2 communities mean-max 0.90 | 301 | +9/-5 | 0.887 | 0.942 | 0.948 | 0.998 | -0.533 | 1.52 | 0.00 |
| soft jury q / top2 communities mean-max 0.90 | 303 | +10/-4 | 0.887 | 0.932 | 0.938 | 0.997 | -0.531 | 1.58 | 0.00 |

## Guardrails

- A fall in estimated heterogeneity under fuzzy communities is partly mechanical; it is not by itself evidence of a truer consensus.
- Soft jury mass tests uncertainty at the existing jury boundary. It does not discover a new estimand or repair missing exposure.
- Community weights remain an audit/aggregation layer. They do not nominate books.
- Rankability gains are evidence gains, not automatic evidence of canonical status.

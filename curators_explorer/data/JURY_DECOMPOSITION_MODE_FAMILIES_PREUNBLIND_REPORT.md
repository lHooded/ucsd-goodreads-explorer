# Hierarchical jury decomposition: mode-families addendum (PRE-UNBLIND structural summary)

**Generated from the sealed main census + geometry only. No semantic context (titles, authors, literary sets, known pole, genres, publication year) was loaded to produce this document.**

- Addendum seed: **20260820**; 10000 label-blind permutations (indexing only).
- Source campaign: seed **20260819**, git head `4ad7287b4624`; 244 recurrent random modes at tau=0.7.
- Addendum code git commit: `9367bd34019f8e5fab988562609d7f020fea5c35`

## Source seal

- census_npz b333150fef91a96e... (verified)
- census_json 8f54a02224f021df... (verified)
- geometry_npz 24a90fa35cdaf6de... (verified)
- geometry_json c47e1ecb75be2d23... (verified)
- addendum_json 6a2894978f6ded6e... (verified)
- addendum_npz eb09e80480a65553... (verified)

## PART A -- cross-parent mode families (tau=0.70 recurrent modes)

| family tau | n families | n cross-parent | >=3 parents | >=5 parents | largest n_modes | largest n_parents | median parents (cross) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 2 | 2 | 2 | 2 | 0.30_f0 | 0.30_f0 | 107.0 |
| 0.50 | 2 | 2 | 2 | 2 | 0.50_f0 | 0.50_f0 | 107.0 |
| 0.70 | 2 | 2 | 2 | 2 | 0.70_f0 | 0.70_f0 | 107.0 |

## PART B -- ratings-only spectral recovery of random modes

| statistic | observed | null mean | null sd | p_upper |
|---|---:|---:|---:|---:|
| mean best cosine (own parent) | 0.5827 | 0.5592 | 0.0005 | 0.0001 |
| median best cosine | 0.5703 | n/a | n/a | 0.0001 |
| mean per-parent mode coverage | 0.9347 | 0.9414 | 0.0044 | 0.9369 |
| fraction mutual-best among siblings | 0.4458 | n/a | n/a | n/a |

## PART C -- parent specificity (absolute distance/cosine)

| statistic | observed | null mean | null sd | p |
|---|---:|---:|---:|---:|
| best-single: mean own-parent cosine | 0.5473 | 0.4899 | 0.0082 | 0.0001 (upper) |
| hull: mean own-parent error | 0.8943 | 0.9463 | 0.0073 | 0.0001 (lower) |
| best-single-error: mean own-parent error | 0.9466 | 1.0018 | n/a | 0.0001 (lower) |

## Prior relative convex-mixture result (kept as-is)

- mixture_rel_0.70 observed relative improvement **0.0536**, empirical upper-tail p **0.9850** (null / non-significant; NOT reinterpreted by this addendum).

## Invariant checks

- family_partition_tau_0.30: ok
- family_centroid_reconstruction_tau_0.30: ok
- family_partition_tau_0.50: ok
- family_centroid_reconstruction_tau_0.50: ok
- family_partition_tau_0.70: ok
- family_centroid_reconstruction_tau_0.70: ok
- mode_sim_symmetric_diagonal: ok
- spectral_table_consistent: ok
- hull_table_consistent: ok

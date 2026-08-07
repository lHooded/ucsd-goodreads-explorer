# Attractor pruning: removing the proponents of contraction to the Goodreads center

Each path starts from a year-derived literary jury, iterates the standard nonlinear ratings-geometry map for 20 steps, identifies the strongest proponents of the converged direction, removes them, rebuilds the operator on the survivors, and restarts from the same literary seed. Ladder paths remove 5% of survivors per stage up to eight stages; hard paths remove the full converged jury (converged weight >= 1.25 x mean) at once. Random controls remove the same number of users at random, so any difference from the criterion paths is attributable to who was removed rather than how much evidence was removed.

Paths: **9**; runtime: **113.3s**.

## Summary

| path | beta | criterion | mode | stop reason | stages | final users | final step corr | final retained vs reference | max retained across stages | final overlap J@200 |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| best_preference_delta_q10 | 2.5 | top_weight | ladder | max_stages | 9 | 154755 | 0.99875 | 0.1914 | 0.4753 (stage 1) | 0.000 |
| best_preference_delta_q10 | 2.5 | gain | ladder | max_stages | 9 | 154755 | 0.99975 | 0.5505 | 0.5545 (stage 7) | 0.003 |
| best_preference_delta_q10 | 2.5 | random | ladder | max_stages | 9 | 154755 | 0.99985 | 0.4583 | 0.4644 (stage 1) | 0.003 |
| best_preference_q10 | 2.5 | top_weight | ladder | max_stages | 9 | 154755 | 0.99934 | 0.3750 | 0.5430 (stage 1) | 0.000 |
| best_preference_delta_q10 | 1.5 | top_weight | ladder | max_stages | 9 | 154755 | 0.99840 | 0.2306 | 0.4651 (stage 1) | 0.000 |
| best_preference_delta_q10 | 2.5 | top_weight | hard | evidence_floor | 6 | 13760 | 0.99945 | 0.0471 | 0.4631 (stage 0) | 0.000 |
| best_preference_delta_q10 | 2.5 | gain | hard | retained_literary_direction | 3 | 76329 | 0.99893 | 0.7017 | 0.7017 (stage 2) | 0.023 |
| best_preference_delta_q10 | 2.5 | random | hard | evidence_floor | 6 | 13178 | 0.99976 | 0.3678 | 0.4631 (stage 0) | 0.044 |
| best_preference_delta_q10 | 2.5 | gain | hard | evidence_floor | 6 | 15395 | 1.00000 | 0.6260 | 0.7238 (stage 4) | 0.250 |

## Stage detail

### best_preference_delta_q10 · beta=2.5 · top_weight · ladder (stop: max_stages)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 11664 | 0.000 | 0.99987 | 0.4631 | 0.4631 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 221607 | 11081 | 0.050 | 0.99995 | 0.4753 | 0.4480 | 0.698 | 0.000 | 0.000 | 0/0 | 0/3 | 2/18 |
| 2 | 210526 | 10527 | 0.098 | 0.99863 | 0.3752 | 0.3355 | 0.699 | 0.000 | 0.003 | 0/0 | 0/2 | 6/29 |
| 3 | 199999 | 10000 | 0.143 | 0.99961 | 0.4608 | 0.4130 | 0.703 | 0.000 | 0.003 | 0/1 | 0/4 | 6/27 |
| 4 | 189999 | 9500 | 0.186 | 0.99970 | 0.4150 | 0.3776 | 0.704 | 0.000 | 0.000 | 0/0 | 0/2 | 12/24 |
| 5 | 180499 | 9025 | 0.226 | 0.99959 | 0.3959 | 0.3354 | 0.698 | 0.000 | 0.000 | 0/0 | 0/2 | 14/52 |
| 6 | 171474 | 8574 | 0.265 | 0.99955 | 0.4333 | 0.3751 | 0.705 | 0.000 | 0.000 | 0/0 | 0/2 | 12/40 |
| 7 | 162900 | 8145 | 0.302 | 0.99922 | 0.4558 | 0.4089 | 0.700 | 0.000 | 0.000 | 0/1 | 0/2 | 16/48 |
| 8 | 154755 | 0 | 0.337 | 0.99875 | 0.1914 | 0.1886 | 0.702 | 0.000 | 0.000 | 0/0 | 0/1 | 28/74 |

### best_preference_delta_q10 · beta=2.5 · gain · ladder (stop: max_stages)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 11664 | 0.000 | 0.99987 | 0.4631 | 0.4631 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 221607 | 11081 | 0.050 | 0.99995 | 0.4871 | 0.5368 | 0.699 | 0.000 | 0.003 | 0/0 | 0/4 | 2/18 |
| 2 | 210526 | 10527 | 0.098 | 0.99884 | 0.4403 | 0.5214 | 0.703 | 0.000 | 0.003 | 0/1 | 0/4 | 5/25 |
| 3 | 199999 | 10000 | 0.143 | 0.99984 | 0.5003 | 0.5975 | 0.700 | 0.000 | 0.003 | 0/1 | 0/5 | 7/25 |
| 4 | 189999 | 9500 | 0.186 | 0.99984 | 0.4994 | 0.6314 | 0.701 | 0.000 | 0.003 | 0/1 | 0/4 | 8/29 |
| 5 | 180499 | 9025 | 0.226 | 0.99985 | 0.5229 | 0.6591 | 0.701 | 0.000 | 0.003 | 0/1 | 0/4 | 12/34 |
| 6 | 171474 | 8574 | 0.265 | 0.99763 | 0.4776 | 0.6334 | 0.703 | 0.000 | 0.003 | 0/1 | 0/3 | 14/43 |
| 7 | 162900 | 8145 | 0.302 | 0.99989 | 0.5545 | 0.7130 | 0.702 | 0.000 | 0.003 | 0/1 | 0/5 | 13/41 |
| 8 | 154755 | 0 | 0.337 | 0.99975 | 0.5505 | 0.7248 | 0.700 | 0.000 | 0.003 | 0/1 | 0/4 | 15/43 |

### best_preference_delta_q10 · beta=2.5 · random · ladder (stop: max_stages)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 11664 | 0.000 | 0.99987 | 0.4631 | 0.4631 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 221607 | 11081 | 0.050 | 0.99987 | 0.4644 | 0.4624 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/18 |
| 2 | 210526 | 10527 | 0.098 | 0.99987 | 0.4630 | 0.4612 | 0.692 | 0.000 | 0.003 | 0/1 | 0/6 | 2/18 |
| 3 | 199999 | 10000 | 0.143 | 0.99987 | 0.4616 | 0.4574 | 0.692 | 0.000 | 0.003 | 0/1 | 0/6 | 2/18 |
| 4 | 189999 | 9500 | 0.186 | 0.99987 | 0.4600 | 0.4557 | 0.691 | 0.000 | 0.003 | 0/1 | 0/6 | 2/17 |
| 5 | 180499 | 9025 | 0.226 | 0.99986 | 0.4591 | 0.4517 | 0.691 | 0.000 | 0.003 | 0/1 | 0/6 | 2/16 |
| 6 | 171474 | 8574 | 0.265 | 0.99986 | 0.4588 | 0.4501 | 0.691 | 0.000 | 0.003 | 0/1 | 0/6 | 2/16 |
| 7 | 162900 | 8145 | 0.302 | 0.99987 | 0.4598 | 0.4485 | 0.691 | 0.000 | 0.003 | 0/1 | 0/6 | 2/16 |
| 8 | 154755 | 0 | 0.337 | 0.99985 | 0.4583 | 0.4438 | 0.691 | 0.000 | 0.003 | 0/1 | 0/6 | 2/15 |

### best_preference_q10 · beta=2.5 · top_weight · ladder (stop: max_stages)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 11664 | 0.000 | 0.99988 | 0.5231 | 0.5231 | 0.694 | 0.000 | 0.000 | 0/1 | 0/5 | 4/25 |
| 1 | 221607 | 11081 | 0.050 | 0.99997 | 0.5430 | 0.5187 | 0.700 | 0.000 | 0.000 | 0/1 | 0/5 | 2/18 |
| 2 | 210526 | 10527 | 0.098 | 0.99955 | 0.4767 | 0.4413 | 0.697 | 0.000 | 0.000 | 0/0 | 0/3 | 7/33 |
| 3 | 199999 | 10000 | 0.143 | 0.99992 | 0.5158 | 0.4622 | 0.701 | 0.000 | 0.000 | 0/1 | 0/4 | 7/25 |
| 4 | 189999 | 9500 | 0.186 | 0.99978 | 0.4777 | 0.4276 | 0.700 | 0.000 | 0.000 | 0/0 | 0/2 | 6/29 |
| 5 | 180499 | 9025 | 0.226 | 0.99976 | 0.5037 | 0.4391 | 0.700 | 0.000 | 0.000 | 0/0 | 0/1 | 13/46 |
| 6 | 171474 | 8574 | 0.265 | 0.99918 | 0.4180 | 0.3617 | 0.705 | 0.000 | 0.000 | 0/0 | 0/1 | 19/50 |
| 7 | 162900 | 8145 | 0.302 | 0.99962 | 0.4814 | 0.4061 | 0.697 | 0.000 | 0.000 | 0/0 | 0/1 | 12/53 |
| 8 | 154755 | 0 | 0.337 | 0.99934 | 0.3750 | 0.3111 | 0.707 | 0.000 | 0.000 | 0/0 | 0/1 | 16/56 |

### best_preference_delta_q10 · beta=1.5 · top_weight · ladder (stop: max_stages)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 11664 | 0.000 | 0.99985 | 0.4540 | 0.4540 | 0.784 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 221607 | 11081 | 0.050 | 0.99994 | 0.4651 | 0.4400 | 0.787 | 0.000 | 0.000 | 0/0 | 0/2 | 5/20 |
| 2 | 210526 | 10527 | 0.098 | 0.99876 | 0.3545 | 0.3195 | 0.788 | 0.000 | 0.000 | 0/0 | 0/2 | 8/33 |
| 3 | 199999 | 10000 | 0.143 | 0.99970 | 0.4475 | 0.4087 | 0.790 | 0.000 | 0.003 | 0/0 | 0/3 | 11/30 |
| 4 | 189999 | 9500 | 0.186 | 0.99960 | 0.3899 | 0.3584 | 0.794 | 0.000 | 0.000 | 0/0 | 0/1 | 14/32 |
| 5 | 180499 | 9025 | 0.226 | 0.99953 | 0.3881 | 0.3339 | 0.788 | 0.000 | 0.000 | 0/0 | 0/1 | 16/64 |
| 6 | 171474 | 8574 | 0.265 | 0.99963 | 0.4175 | 0.3674 | 0.792 | 0.000 | 0.000 | 0/0 | 0/1 | 15/58 |
| 7 | 162900 | 8145 | 0.302 | 0.99878 | 0.3930 | 0.3550 | 0.790 | 0.000 | 0.000 | 0/0 | 0/1 | 18/59 |
| 8 | 154755 | 0 | 0.337 | 0.99840 | 0.2306 | 0.2130 | 0.796 | 0.000 | 0.000 | 0/0 | 0/1 | 27/80 |

### best_preference_delta_q10 · beta=2.5 · top_weight · hard (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 101474 | 0.000 | 0.99987 | 0.4631 | 0.4631 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 131797 | 56679 | 0.435 | 0.99983 | 0.1197 | 0.1852 | 0.697 | 0.000 | 0.000 | 0/0 | 0/0 | 28/70 |
| 2 | 75118 | 31574 | 0.678 | 0.99969 | 0.1699 | 0.2439 | 0.683 | 0.000 | 0.000 | 0/0 | 0/0 | 34/109 |
| 3 | 43544 | 19184 | 0.813 | 0.99964 | 0.0561 | 0.1008 | 0.685 | 0.000 | 0.000 | 0/0 | 0/0 | 28/80 |
| 4 | 24360 | 10600 | 0.896 | 0.99981 | 0.0960 | 0.1728 | 0.681 | 0.000 | 0.000 | 0/0 | 0/0 | 28/64 |
| 5 | 13760 | 0 | 0.941 | 0.99945 | 0.0471 | 0.2436 | 0.698 | 0.000 | 0.000 | 0/0 | 0/0 | 32/101 |

### best_preference_delta_q10 · beta=2.5 · gain · hard (stop: retained_literary_direction)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 101474 | 0.000 | 0.99987 | 0.4631 | 0.4631 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 131797 | 55468 | 0.435 | 0.99918 | 0.5382 | 0.6126 | 0.698 | 0.000 | 0.000 | 0/0 | 0/1 | 15/47 |
| 2 | 76329 | 0 | 0.673 | 0.99893 | 0.7017 | 0.8791 | 0.653 | 0.000 | 0.023 | 0/3 | 3/12 | 14/50 |

### best_preference_delta_q10 · beta=2.5 · random · hard (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 101474 | 0.000 | 0.99987 | 0.4631 | 0.4631 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 131797 | 57544 | 0.435 | 0.99985 | 0.4597 | 0.4408 | 0.690 | 0.000 | 0.003 | 0/1 | 0/4 | 2/18 |
| 2 | 74253 | 32435 | 0.682 | 0.99986 | 0.4510 | 0.4095 | 0.686 | 0.000 | 0.003 | 0/1 | 0/3 | 4/21 |
| 3 | 41818 | 18320 | 0.821 | 0.99985 | 0.4447 | 0.3833 | 0.680 | 0.000 | 0.015 | 0/3 | 0/6 | 8/22 |
| 4 | 23498 | 10320 | 0.899 | 0.99975 | 0.4173 | 0.3715 | 0.675 | 0.000 | 0.036 | 1/4 | 1/9 | 7/21 |
| 5 | 13178 | 0 | 0.944 | 0.99976 | 0.3678 | 0.3896 | 0.669 | 0.000 | 0.044 | 1/5 | 1/15 | 10/27 |

### best_preference_delta_q10 · beta=2.5 · gain · hard (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | J@50 | J@200 | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 101474 | 0.000 | 0.99987 | 0.4631 | 0.4631 | 0.692 | 0.000 | 0.003 | 0/1 | 0/7 | 2/19 |
| 1 | 131797 | 55468 | 0.435 | 0.99918 | 0.5382 | 0.6126 | 0.698 | 0.000 | 0.000 | 0/0 | 0/1 | 15/47 |
| 2 | 76329 | 29041 | 0.673 | 0.99893 | 0.7017 | 0.8791 | 0.653 | 0.000 | 0.023 | 0/3 | 3/12 | 14/50 |
| 3 | 47288 | 20488 | 0.797 | 1.00000 | 0.7192 | 0.9670 | 0.617 | 0.010 | 0.096 | 3/6 | 7/27 | 4/13 |
| 4 | 26800 | 11405 | 0.885 | 1.00000 | 0.7238 | 0.9766 | 0.618 | 0.042 | 0.149 | 3/9 | 7/29 | 9/25 |
| 5 | 15395 | 0 | 0.934 | 1.00000 | 0.6260 | 0.9567 | 0.671 | 0.099 | 0.250 | 5/14 | 12/38 | 3/10 |

## Removed-user profile

Average year-jury features of removed vs retained users at each removal stage: old_love_share (mean oldness of five-star ratings), preference (old-minus-new rating correlation), rated_n (ratings), five_rate.

| path | stage | removed users | removed old_love | retained old_love | removed pref | retained pref | removed rated_n | retained rated_n | removed five_rate | retained five_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| best_preference_delta_q10 top_weight/ladder | 0 | 11664 | 0.150 | 0.103 | 0.077 | -0.004 | 198 | 149 | 0.329 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 1 | 11081 | 0.134 | 0.101 | 0.065 | -0.008 | 206 | 146 | 0.321 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 2 | 10527 | 0.117 | 0.100 | 0.023 | -0.010 | 198 | 143 | 0.316 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 3 | 10000 | 0.135 | 0.098 | 0.049 | -0.013 | 206 | 140 | 0.326 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 4 | 9500 | 0.126 | 0.097 | 0.018 | -0.014 | 203 | 136 | 0.318 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 5 | 9025 | 0.101 | 0.097 | 0.027 | -0.016 | 187 | 134 | 0.318 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 6 | 8574 | 0.122 | 0.095 | 0.025 | -0.019 | 194 | 131 | 0.316 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 7 | 8145 | 0.128 | 0.094 | 0.031 | -0.021 | 182 | 128 | 0.321 | 0.321 |
| best_preference_delta_q10 gain/ladder | 0 | 11664 | 0.131 | 0.104 | 0.043 | -0.003 | 175 | 150 | 0.348 | 0.320 |
| best_preference_delta_q10 gain/ladder | 1 | 11081 | 0.123 | 0.103 | 0.038 | -0.005 | 175 | 149 | 0.353 | 0.318 |
| best_preference_delta_q10 gain/ladder | 2 | 10527 | 0.115 | 0.102 | 0.008 | -0.005 | 173 | 147 | 0.347 | 0.316 |
| best_preference_delta_q10 gain/ladder | 3 | 10000 | 0.111 | 0.102 | 0.019 | -0.007 | 162 | 147 | 0.348 | 0.315 |
| best_preference_delta_q10 gain/ladder | 4 | 9500 | 0.129 | 0.100 | 0.011 | -0.007 | 151 | 146 | 0.350 | 0.313 |
| best_preference_delta_q10 gain/ladder | 5 | 9025 | 0.111 | 0.100 | 0.013 | -0.009 | 149 | 146 | 0.352 | 0.311 |
| best_preference_delta_q10 gain/ladder | 6 | 8574 | 0.112 | 0.099 | -0.008 | -0.009 | 146 | 146 | 0.352 | 0.309 |
| best_preference_delta_q10 gain/ladder | 7 | 8145 | 0.117 | 0.098 | 0.001 | -0.009 | 138 | 147 | 0.350 | 0.306 |
| best_preference_delta_q10 random/ladder | 0 | 11664 | 0.106 | 0.105 | -0.001 | -0.000 | 153 | 151 | 0.322 | 0.321 |
| best_preference_delta_q10 random/ladder | 1 | 11081 | 0.105 | 0.105 | -0.001 | -0.000 | 153 | 151 | 0.325 | 0.321 |
| best_preference_delta_q10 random/ladder | 2 | 10527 | 0.105 | 0.105 | 0.001 | -0.000 | 151 | 151 | 0.320 | 0.321 |
| best_preference_delta_q10 random/ladder | 3 | 10000 | 0.104 | 0.105 | -0.002 | -0.000 | 150 | 151 | 0.320 | 0.321 |
| best_preference_delta_q10 random/ladder | 4 | 9500 | 0.104 | 0.105 | 0.003 | -0.000 | 153 | 151 | 0.321 | 0.321 |
| best_preference_delta_q10 random/ladder | 5 | 9025 | 0.105 | 0.105 | -0.001 | -0.000 | 151 | 151 | 0.323 | 0.321 |
| best_preference_delta_q10 random/ladder | 6 | 8574 | 0.103 | 0.105 | -0.002 | -0.000 | 151 | 151 | 0.321 | 0.321 |
| best_preference_delta_q10 random/ladder | 7 | 8145 | 0.105 | 0.105 | -0.000 | -0.000 | 150 | 151 | 0.320 | 0.321 |
| best_preference_q10 top_weight/ladder | 0 | 11664 | 0.129 | 0.104 | 0.064 | -0.004 | 196 | 149 | 0.328 | 0.321 |
| best_preference_q10 top_weight/ladder | 1 | 11081 | 0.132 | 0.102 | 0.071 | -0.008 | 202 | 146 | 0.323 | 0.320 |
| best_preference_q10 top_weight/ladder | 2 | 10527 | 0.138 | 0.100 | 0.022 | -0.009 | 194 | 144 | 0.318 | 0.321 |
| best_preference_q10 top_weight/ladder | 3 | 10000 | 0.115 | 0.100 | 0.046 | -0.012 | 203 | 141 | 0.323 | 0.320 |
| best_preference_q10 top_weight/ladder | 4 | 9500 | 0.136 | 0.098 | 0.023 | -0.014 | 199 | 138 | 0.315 | 0.321 |
| best_preference_q10 top_weight/ladder | 5 | 9025 | 0.123 | 0.096 | 0.040 | -0.017 | 191 | 135 | 0.322 | 0.321 |
| best_preference_q10 top_weight/ladder | 6 | 8574 | 0.112 | 0.096 | 0.005 | -0.018 | 193 | 132 | 0.318 | 0.321 |
| best_preference_q10 top_weight/ladder | 7 | 8145 | 0.124 | 0.094 | 0.026 | -0.020 | 180 | 129 | 0.324 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 0 | 11664 | 0.149 | 0.103 | 0.073 | -0.004 | 200 | 149 | 0.330 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 1 | 11081 | 0.129 | 0.101 | 0.064 | -0.008 | 210 | 146 | 0.323 | 0.320 |
| best_preference_delta_q10 top_weight/ladder | 2 | 10527 | 0.112 | 0.101 | 0.016 | -0.009 | 198 | 143 | 0.314 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 3 | 10000 | 0.138 | 0.099 | 0.049 | -0.012 | 208 | 139 | 0.327 | 0.320 |
| best_preference_delta_q10 top_weight/ladder | 4 | 9500 | 0.123 | 0.098 | 0.008 | -0.013 | 210 | 136 | 0.320 | 0.320 |
| best_preference_delta_q10 top_weight/ladder | 5 | 9025 | 0.099 | 0.098 | 0.026 | -0.015 | 190 | 133 | 0.323 | 0.320 |
| best_preference_delta_q10 top_weight/ladder | 6 | 8574 | 0.120 | 0.096 | 0.031 | -0.018 | 195 | 130 | 0.316 | 0.321 |
| best_preference_delta_q10 top_weight/ladder | 7 | 8145 | 0.123 | 0.095 | 0.009 | -0.019 | 184 | 127 | 0.323 | 0.320 |
| best_preference_delta_q10 top_weight/hard | 0 | 101474 | 0.144 | 0.075 | 0.047 | -0.036 | 156 | 148 | 0.319 | 0.323 |
| best_preference_delta_q10 top_weight/hard | 1 | 56679 | 0.073 | 0.077 | -0.029 | -0.042 | 150 | 146 | 0.323 | 0.323 |
| best_preference_delta_q10 top_weight/hard | 2 | 31574 | 0.085 | 0.070 | -0.014 | -0.062 | 154 | 140 | 0.324 | 0.322 |
| best_preference_delta_q10 top_weight/hard | 3 | 19184 | 0.050 | 0.086 | -0.049 | -0.073 | 153 | 129 | 0.322 | 0.322 |
| best_preference_delta_q10 top_weight/hard | 4 | 10600 | 0.081 | 0.090 | -0.047 | -0.093 | 135 | 125 | 0.317 | 0.325 |
| best_preference_delta_q10 gain/hard | 0 | 101474 | 0.125 | 0.090 | 0.013 | -0.010 | 143 | 158 | 0.335 | 0.311 |
| best_preference_delta_q10 gain/hard | 1 | 55468 | 0.076 | 0.099 | -0.039 | 0.011 | 131 | 178 | 0.344 | 0.286 |
| best_preference_delta_q10 random/hard | 0 | 101474 | 0.105 | 0.105 | -0.001 | -0.000 | 151 | 152 | 0.321 | 0.321 |
| best_preference_delta_q10 random/hard | 1 | 57544 | 0.105 | 0.105 | -0.000 | 0.000 | 152 | 151 | 0.322 | 0.321 |
| best_preference_delta_q10 random/hard | 2 | 32435 | 0.105 | 0.105 | -0.001 | 0.001 | 150 | 152 | 0.320 | 0.321 |
| best_preference_delta_q10 random/hard | 3 | 18320 | 0.104 | 0.106 | 0.002 | 0.001 | 151 | 153 | 0.321 | 0.320 |
| best_preference_delta_q10 random/hard | 4 | 10320 | 0.106 | 0.106 | -0.001 | 0.002 | 154 | 153 | 0.322 | 0.319 |
| best_preference_delta_q10 gain/hard | 0 | 101474 | 0.125 | 0.090 | 0.013 | -0.010 | 143 | 158 | 0.335 | 0.311 |
| best_preference_delta_q10 gain/hard | 1 | 55468 | 0.076 | 0.099 | -0.039 | 0.011 | 131 | 178 | 0.344 | 0.286 |
| best_preference_delta_q10 gain/hard | 2 | 29041 | 0.059 | 0.124 | -0.068 | 0.059 | 136 | 203 | 0.347 | 0.248 |
| best_preference_delta_q10 gain/hard | 3 | 20488 | 0.135 | 0.116 | 0.050 | 0.065 | 167 | 230 | 0.283 | 0.222 |
| best_preference_delta_q10 gain/hard | 4 | 11405 | 0.060 | 0.159 | -0.023 | 0.131 | 178 | 269 | 0.254 | 0.198 |

## Converged heads at the stop stage

### best_preference_delta_q10 · beta=2.5 · top_weight · ladder (stage 8, stop max_stages)

Exact literary @50/200: **0/0**; broad: **0/1**; anti: **28/74**.

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.936)
2. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.893)
3. *The Hate U Give* — Angie Thomas (0.889)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.883)
5. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.882)
6. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.881)
7. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.872)
8. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.870)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.850)
10. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.847)
11. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.847)
12. *The Harry Potter Collection 1-4 (Harry Potter, #1-4)* — J.K. Rowling (0.845)
13. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.840)
14. *Humans of New York: Stories* — Brandon Stanton (0.837)
15. *Dear Ijeawele, or a Feminist Manifesto in Fifteen Suggestions* — Chimamanda Ngozi Adichie (0.836)

### best_preference_delta_q10 · beta=2.5 · gain · ladder (stage 8, stop max_stages)

Exact literary @50/200: **0/1**; broad: **0/4**; anti: **15/43**.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.894)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.884)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.870)
4. *Calvin and Hobbes* — Bill Watterson (0.844)
5. *Jesus the Christ* — James E. Talmage (0.837)
6. *The Hate U Give* — Angie Thomas (0.836)
7. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.832)
8. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.830)
9. *March: Book Two (March, #2)* — John             Lewis (0.828)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.825)
11. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.823)
12. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.814)
13. *Toda Mafalda* — Quino (0.811)
14. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.806)
15. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.806)

### best_preference_delta_q10 · beta=2.5 · random · ladder (stage 8, stop max_stages)

Exact literary @50/200: **0/1**; broad: **0/6**; anti: **2/15**.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.946)
2. *Calvin and Hobbes* — Bill Watterson (0.911)
3. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.899)
4. *March: Book Two (March, #2)* — John             Lewis (0.897)
5. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.894)
6. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.891)
7. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.880)
8. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.878)
9. *March: Book Three (March, #3)* — John             Lewis (0.877)
10. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.874)
11. *The Absolute Sandman, Volume One* — Neil Gaiman (0.872)
12. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.871)
13. *The Hate U Give* — Angie Thomas (0.867)
14. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.864)
15. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.863)

### best_preference_q10 · beta=2.5 · top_weight · ladder (stage 8, stop max_stages)

Exact literary @50/200: **0/0**; broad: **0/1**; anti: **16/56**.

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.920)
2. *The Hate U Give* — Angie Thomas (0.896)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.881)
4. *The Harry Potter Collection 1-4 (Harry Potter, #1-4)* — J.K. Rowling (0.880)
5. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.863)
6. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.863)
7. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.857)
8. *The Complete Calvin and Hobbes* — Bill Watterson (0.855)
9. *Humans of New York: Stories* — Brandon Stanton (0.853)
10. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.853)
11. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.847)
12. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.836)
13. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.830)
14. *Toda Mafalda* — Quino (0.826)
15. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.825)

### best_preference_delta_q10 · beta=1.5 · top_weight · ladder (stage 8, stop max_stages)

Exact literary @50/200: **0/0**; broad: **0/1**; anti: **27/80**.

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.925)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.906)
3. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.891)
4. *The Hate U Give* — Angie Thomas (0.887)
5. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.879)
6. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.872)
7. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.865)
8. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.850)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.838)
10. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.837)
11. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.834)
12. *Humans of New York: Stories* — Brandon Stanton (0.830)
13. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.829)
14. *A Voice in the Wind (Mark of the Lion, #1)* — Francine Rivers (0.827)
15. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.824)

### best_preference_delta_q10 · beta=2.5 · top_weight · hard (stage 5, stop evidence_floor)

Exact literary @50/200: **0/0**; broad: **0/0**; anti: **32/101**.

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.883)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.861)
3. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.854)
4. *The Nightingale* — Kristin Hannah (0.846)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.827)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.815)
7. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.804)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.791)
9. *Small Great Things* — Jodi Picoult (0.783)
10. *The Hero of Ages (Mistborn, #3)* — Brandon Sanderson (0.767)
11. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.766)
12. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (0.766)
13. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.763)
14. *The Martian* — Andy Weir (0.748)
15. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.744)

### best_preference_delta_q10 · beta=2.5 · gain · hard (stage 2, stop retained_literary_direction)

Exact literary @50/200: **0/3**; broad: **3/12**; anti: **14/50**.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.920)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.846)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.844)
4. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.839)
5. *Changes (The Dresden Files, #12)* — Jim Butcher (0.830)
6. *Calvin and Hobbes* — Bill Watterson (0.824)
7. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.823)
8. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.822)
9. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.814)
10. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.810)
11. *Fool's Quest  (The Fitz and The Fool, #2)* — Robin Hobb (0.810)
12. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.807)
13. *Jesus the Christ* — James E. Talmage (0.799)
14. *The Monster at the End of this Book* — Jon Stone (0.794)
15. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.792)

### best_preference_delta_q10 · beta=2.5 · random · hard (stage 5, stop evidence_floor)

Exact literary @50/200: **1/5**; broad: **1/15**; anti: **10/27**.

1. *Unbroken: A World War II Story of Survival, Resilience, and Redemption* — Laura Hillenbrand (0.781)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.763)
3. *The Nightingale* — Kristin Hannah (0.754)
4. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.736)
5. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.725)
6. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.725)
7. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.724)
8. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.724)
9. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.712)
10. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.712)
11. *ثلاثية غرناطة* — Radwa Ashour (0.703)
12. *J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings* — J.R.R. Tolkien (0.703)
13. *Calvin and Hobbes* — Bill Watterson (0.688)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.684)
15. *Homegoing* — Yaa Gyasi (0.684)

### best_preference_delta_q10 · beta=2.5 · gain · hard (stage 5, stop evidence_floor)

Exact literary @50/200: **5/14**; broad: **12/38**; anti: **3/10**.

1. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.844)
2. *Pride and Prejudice* — Jane Austen (0.840)
3. *The Complete Stories and Poems* — Edgar Allan Poe (0.823)
4. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.823)
5. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.813)
6. *To Kill a Mockingbird* — Harper Lee (0.809)
7. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.794)
8. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.790)
9. *Jane Eyre* — Charlotte Bronte (0.786)
10. *J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings* — J.R.R. Tolkien (0.780)
11. *Hamlet* — William Shakespeare (0.776)
12. *The Monster at the End of this Book* — Jon Stone (0.769)
13. *The Complete Grimm's Fairy Tales* — Jacob Grimm (0.769)
14. *Persuasion* — Jane Austen (0.768)
15. *The Complete Works* — William Shakespeare (0.767)

## Findings

- The unpruned baseline reproduces the known collapse: the converged head is the Goodreads love center (exact literary 0/1 at @50, anti 2/19), with only 0.463 of the original literary direction retained.
- **Gradual pruning (5% per stage) barely moves the basin.** Gain-pruning nudges retained direction from 0.463 to 0.55 over eight stages; top-weight pruning degrades it to 0.19-0.37 and lets anti books into the head; the random control is flat at ~0.46. None approach the 0.70 retention threshold.
- **The qualitative change appears only when the co-opted users are removed at once.** Removing the top-43%-by-weight-gain (users whose weights rose most during iteration) lifts retained direction 0.463 -> 0.538 -> 0.702 (stage 2), with 0.879 of the stage-start direction preserved.
- **Continuing toward 0.85 exposes an enclosed literary valley.** Step correlation reaches exactly 1.00000 while 0.967-0.977 of the stage-start direction is preserved; retained vs the full-matrix reference plateaus at ~0.724 before degrading to 0.626 as evidence runs out (stage 5, 15,395 of 233,271 users, 93.4% removed).
- **The deep-pruned head is canonical**: *The Brothers Karamazov* #1, *Pride and Prejudice* #2, Poe, *Hamlet*, *Persuasion*, *The Divine Comedy*, *The Count of Monte Cristo*. Exact literary @50 rises 0 -> 3 -> 5; anti @50 collapses from 14-19 to 3. The random control at comparable or smaller remaining mass never exceeds 0.46 retained and keeps anti >= 7/21, so the effect is specific to who is removed, not how much evidence is removed.
- **The proponents of contraction are old-book-loving omnivores.** Removed users have higher old-love share (0.144 vs 0.075 at the first hard removal) and positive old-vs-new preference. The pull back to the Goodreads center is not a separate genre population: it is carried by readers who love old books AND the popular center. Removing exactly them exposes a stricter old-book core.
- **Caveats.** The valley is not unsupervised: the year-preference direction must be supplied and the year-jury members are retained by construction (their weight gain is negative). The fixed point plateaus around 0.72 against the full-matrix reference and degrades past ~94% removal. The head remains edition-coarse (boxed sets) and school-canon-leaning with residual children's entries. This validates old-over-new preference as a genuine anchored signal and locates the collapse mechanism, but it does not overturn the identifiability boundary: the literary ordering is confirmed by the geometry, not discovered by it.

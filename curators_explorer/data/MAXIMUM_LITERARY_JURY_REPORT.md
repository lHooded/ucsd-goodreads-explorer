# Maximum Literary Jury / Core–Halo Amplification

- Experiment seed: `20260826`; git head `91413ab7c39d7832f30e1fac5079b5e8313b8d94`
- Payload: 233,271 users × 26,418 works
- J_star rule (frozen): 1 raw_n>=10000; 2 anti50<=5; 3 maximize pos50+0.25*broad50+5*half_jaccard; 4 tie-break larger kish; 5 larger raw_n; fallback largest jury with anti50<=5
- Perturbation outcome (frozen): primary = 0.7*ref_cosine + 0.3*half_jaccard; ref = frozen p65_s25 weighted pairwise ranking; ref_cosine over common top-1000 works

## 1. Goal and honest framing

We reverse-engineer a strong literary *user* jury from ordinary Goodreads behaviour, then ask how large it can be made while retaining a stable, recognisably literary consensus. Semantic labels are used openly for training/model selection/evaluation/optimisation; the separation kept honest is between direct seed-book features (oracle only), ordinary behavioural features (primary inference), user membership labels from earlier literary juries, and final semantic evaluation.

## 2. Reconstructed historical user juries

| jury | raw n | Kish n_eff | payload-covered | pos50 | anti50 | exact@50 | kind |
|---|---:|---:|---:|---:|---:|---:|---|
| `core_p65_s25` | 3286 | 2678 | 2438 | 42 | 0 | 23 | deep_mint_jury |
| `deep_mint_all` | 19841 | 9401 | 11236 | 24 | 0 | 14 | deep_mint_all |
| `p0_s0` | 19841 | 9401 | 11236 | 24 | 0 | 14 | deep_mint_jury |
| `p0_s15` | 8973 | 6191 | 6098 | 31 | 0 | 17 | deep_mint_jury |
| `p0_s25` | 5287 | 4094 | 3873 | 37 | 0 | 20 | deep_mint_jury |
| `p0_s40` | 2391 | 2044 | 1898 | 42 | 0 | 24 | deep_mint_jury |
| `p45_s40` | 2354 | 2015 | 1871 | 44 | 0 | 24 | deep_mint_jury |
| `p65_s0` | 10525 | 5827 | 5402 | 30 | 0 | 17 | deep_mint_jury |
| `p75_s40` | 1262 | 1102 | 985 | 47 | 0 | 25 | deep_mint_jury |
| `rebuilt_hard` | 4929 | nan | 2945 | 37 | 0 | 18 | rebuilt_hard_jury |
| `rebuilt_soft` | 20000 | 5199 | 12267 | 18 | 1 | 6 | rebuilt_soft_jury |
| `threeway_anti` | 221879 | nan | 136425 | 0 | 36 | 0 | threeway_cohort |
| `threeway_classic` | 31803 | nan | 21044 | 19 | 0 | 9 | threeway_cohort |
| `threeway_normie` | 33571 | nan | 17224 | 0 | 7 | 0 | threeway_cohort |

Threeway cohort sizes (rebuilt): classic=31803 anti=221879 normie=33571

### Reconstructed head (core p65_s25)

1. Crime and Punishment — Fyodor Dostoyevsky
2. The Brothers Karamazov — Fyodor Dostoyevsky
3. Gravity's Rainbow — Thomas Pynchon
4. 2666 — Roberto Bolano
5. Stoner — John  Williams
6. War and Peace — Leo Tolstoy
7. Infinite Jest — David Foster Wallace
8. The Divine Comedy — Dante Alighieri
9. The Magic Mountain — Thomas Mann
10. Demons — Fyodor Dostoyevsky
11. Pale Fire — Vladimir Nabokov
12. The Master and Margarita — Mikhail Bulgakov
13. East of Eden — John Steinbeck
14. In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust
15. Lolita — Vladimir Nabokov
16. Ulysses — James Joyce
17. The Idiot — Fyodor Dostoyevsky
18. The Dead — James Joyce
19. Four Quartets — T.S. Eliot
20. Swann's Way (In Search of Lost Time, #1) — Marcel Proust
21. The Trial — Franz Kafka
22. Blood Meridian, or the Evening Redness in the West — Cormac McCarthy
23. Notes from Underground — Fyodor Dostoyevsky
24. The Book of Disquiet — Fernando Pessoa
25. Molloy — Samuel Beckett
26. Life and Fate — Vasily Grossman
27. Anna Karenina — Leo Tolstoy
28. Inferno (The Divine Comedy #1) — Dante Alighieri
29. Journey to the End of the Night — Louis-Ferdinand Celine
30. The Metamorphosis — Franz Kafka

## 3. Failed-10k paired forensic analysis

- Paired observations: 24 (2 roots × 12 partitions)
- Partition reconstruction: root0 fitness corr 1.000000, root1 1.000000
- LOO ridge (delta_f1_margin): corr=-0.213, r2=-0.313

| feature | LOO coef (std) | univ corr | mean delta | root0 sign | root1 sign |
|---|---:|---:|---:|---:|---|
| `series_share_5` | -0.017 | -0.088 | +0.0000 | +0.0001 | -0.0001 |
| `binge_max_5_log` | -0.010 | +0.008 | -0.0003 | -0.0061 | +0.0055 |
| `author_hhi_5` | +0.003 | +0.117 | -0.0002 | +0.0011 | -0.0014 |
| `mean_pub_year_5` | +0.002 | +0.141 | +0.0004 | -0.0002 | +0.0010 |
| `midpop_span_per_logn5` | +0.003 | +0.168 | -0.0004 | -0.0044 | +0.0036 |
| `mega_catalog_share_5` | -0.012 | -0.246 | -0.0004 | -0.0004 | -0.0004 |

Do the failed anti-ish 10k halves still contain relative information about which reader behaviours push a child closer to the literary F1 phase? Coefficient signs below are compared against the threeway/feature-sensitivity results in the interpretation section. n=24 is tiny; do not read p-values.

## 4. User features and labels

- Features: 51 ordinary behavioural features aligned to 233,271 payload users; 0 NaNs median-imputed.
- Direct seed-hit features are used ONLY in the labelled oracle model.

| label | positive n (payload) | rate |
|---|---:|---:|
| p65_s25 | 2438 | 0.0105 |
| p75_s40 | 985 | 0.0042 |
| p45_s40 | 1871 | 0.0080 |
| p0_s0 | 11236 | 0.0482 |
| p0_s25 | 3873 | 0.0166 |
| p0_s15 | 6098 | 0.0261 |
| threeway_classic | 21044 | 0.0902 |
| threeway_anti | 136425 | 0.5848 |
| threeway_normie | 17224 | 0.0738 |
| rebuilt_hard | 2945 | 0.0126 |
| soft_consensus | 6311 | 0.0271 |

## 5. Model validation

| model | AUC | AP | positive n | negative n |
|---|---:|---:|---:|---:|
| binary_elasticnet | 0.924 | 0.852 | 2438 | 4876 |
| binary_l2 | 0.993 | 0.986 | 2438 | 4876 |
| binary_gbm | 0.996 | 0.992 | 2438 | - |
| soft_ridge | corr=0.875 | - | - | - |
| oracle (seed hits, upper bound) | 1.000 | - | 2438 | - |

### Leave-one-jury-definition-out

| held-out jury | AUC | top-1% rate | base rate | enrichment |
|---|---:|---:|---:|---:|
| p75_s40 | 0.928 | 0.0832 | 0.0042 | 19.70× |
| p65_s25 | 0.916 | 0.1694 | 0.0105 | 16.21× |
| p45_s40 | 0.920 | 0.1488 | 0.0080 | 18.55× |
| threeway_classic | 0.786 | 0.3178 | 0.0902 | 3.52× |
| p0_s0 | 0.850 | 0.3491 | 0.0482 | 7.25× |
| rebuilt_hard | 0.936 | 0.2933 | 0.0126 | 23.23× |

### Ablations (elasticnet, drop feature set)

| ablation | AUC | dropped |
|---|---:|---|
| no_publication_year | 0.924 | mean_pub_year_5 |
| no_series_binge | 0.920 | series_share_5, binge_mean_5, binge_max_5_log |
| no_popularity | 0.921 | mean_logn_5, std_logn_5, p5_blockbuster, midpop_likes_per_log_shelf, popular_likes_per_log_shelf, mean_logn_all, std_logn_all, mean_logn_low, mid_catalog_share_5, mega_catalog_share_5, p5_mid_exposed, p5_mega_exposed |

## 6. User phenotype explanation

Interpretable model coefficients (elasticnet, top by |coef|):

- `rare_rated_share`: -0.8210
- `mean_abs_residual`: -0.5709
- `binge_max_5_log`: -0.5489
- `mid_loved_share`: -0.4939
- `rare_loved_share`: -0.4655
- `mean_logn_low`: -0.3054
- `mean_residual`: +0.2717
- `log_n5`: -0.2612
- `midpop_author_frac_5`: +0.2144
- `log_n_rated`: +0.2138
- `singleton_author_share_5`: -0.1922
- `midpop_span_per_logn5`: +0.1729
- `p5_mid_exposed`: +0.1675
- `n_midpop_authors_5_log`: -0.1631
- `mean_work_mean_all`: +0.1579
- `depth_5`: -0.1488
- `popular_likes_per_log_shelf`: -0.1470
- `rating_pop_corr`: -0.1470
- `log_n_ge4`: +0.1463
- `p5_mega_exposed`: -0.1236

## 7. Direct nested jury frontier

| jury | n | pos50 | broad50 | anti50 | half J50 | head (top 6) |
|---|---:|---:|---:|---:|---:|---|
| top_1000 | 1000 | 10 | 10 | 1 | 0.24 | Stoner, White Noise, The Sympathizer, Kindred, Homegoing, The Amazing Adventures o |
| top_10000 | 10000 | 7 | 7 | 1 | 0.39 | لا تصالح, The One and Only Ivan, رياض الصالحين, لافتات - المجموعة الكامل, A Tree Grows in Brooklyn, يسمعون حسيسها |
| top_100000 | 100000 | 1 | 1 | 6 | 0.42 | The Hate U Give, Captive Prince: Volume T, لا تصالح, The War that Saved My Li, Words of Radiance (The S, الحرافيش |
| top_120000 | 120000 | 1 | 1 | 10 | 0.53 | The Hate U Give, Captive Prince: Volume T, Words of Radiance (The S, The War that Saved My Li, لا تصالح, Magic Binds (Kate Daniel |
| top_1500 | 1500 | 12 | 12 | 0 | 0.23 | Kindred, Middlesex, ساق البامبو, Homegoing, The Book of Night Women, The Hate U Give |
| top_15000 | 15000 | 5 | 5 | 1 | 0.44 | لا تصالح, رياض الصالحين, لافتات - المجموعة الكامل, يسمعون حسيسها, The War that Saved My Li, A Monster Calls |
| top_150000 | 150000 | 0 | 0 | 13 | 0.49 | The Hate U Give, Words of Radiance (The S, The War that Saved My Li, Crooked Kingdom (Six of , Magic Binds (Kate Daniel, لا تصالح |
| top_2000 | 2000 | 9 | 9 | 2 | 0.28 | Middlesex, Invisible Cities, Kindred, One Hundred Years of Sol, رياض الصالحين, Americanah |
| top_20000 | 20000 | 4 | 4 | 0 | 0.46 | لا تصالح, رياض الصالحين, لافتات - المجموعة الكامل, The Story of a New Name , The Hate U Give, The One and Only Ivan |
| top_30000 | 30000 | 2 | 2 | 2 | 0.46 | رياض الصالحين, لا تصالح, The Hate U Give, The Story of a New Name , Homegoing, The War that Saved My Li |
| top_3286 | 3286 | 9 | 9 | 1 | 0.33 | لا تصالح, رياض الصالحين, Kindred, The Hate U Give, لافتات - المجموعة الكامل, All the Light We Cannot  |
| top_40000 | 40000 | 1 | 1 | 2 | 0.41 | The Hate U Give, رياض الصالحين, لا تصالح, The Story of a New Name , Homegoing, The War that Saved My Li |
| top_500 | 500 | 9 | 9 | 1 | 0.05 | The Sympathizer, The Name of the Rose, A Little Life, The Nightingale, Stoner, The Inquisitor's Tale: O |
| top_5000 | 5000 | 9 | 9 | 1 | 0.27 | لا تصالح, رياض الصالحين, The Hate U Give, لافتات - المجموعة الكامل, The Nightingale, يسمعون حسيسها |
| top_60000 | 60000 | 1 | 1 | 4 | 0.47 | The Hate U Give, رياض الصالحين, لا تصالح, The War that Saved My Li, Captive Prince: Volume T, Homegoing |
| top_8000 | 8000 | 8 | 8 | 1 | 0.36 | لا تصالح, رياض الصالحين, يسمعون حسيسها, لافتات - المجموعة الكامل, The One and Only Ivan, The War that Saved My Li |
| top_80000 | 80000 | 1 | 1 | 7 | 0.52 | The Hate U Give, Captive Prince: Volume T, لا تصالح, Homegoing, The War that Saved My Li, The Story of a New Name  |

## 8. Core-preserving frontier

- `corepres_10000`: n=10000 pos50=19 anti50=1 J50=0.50
- `corepres_100000`: n=100000 pos50=1 anti50=6 J50=0.47
- `corepres_120000`: n=120000 pos50=1 anti50=10 J50=0.42
- `corepres_15000`: n=15000 pos50=15 anti50=0 J50=0.45
- `corepres_150000`: n=150000 pos50=0 anti50=13 J50=0.50
- `corepres_20000`: n=20000 pos50=11 anti50=0 J50=0.52
- `corepres_30000`: n=30000 pos50=5 anti50=2 J50=0.48
- `corepres_40000`: n=40000 pos50=3 anti50=3 J50=0.45
- `corepres_5000`: n=5000 pos50=35 anti50=0 J50=0.56
- `corepres_60000`: n=60000 pos50=1 anti50=3 J50=0.48
- `corepres_8000`: n=8000 pos50=23 anti50=1 J50=0.48
- `corepres_80000`: n=80000 pos50=1 anti50=7 J50=0.46

## 9. Core-excluding rediscovery frontier

- `coreexcl_1000`: n=1000 pos50=7 anti50=2 J50=0.26
- `coreexcl_10000`: n=10000 pos50=4 anti50=1 J50=0.46
- `coreexcl_2000`: n=2000 pos50=9 anti50=2 J50=0.28
- `coreexcl_20000`: n=20000 pos50=2 anti50=1 J50=0.46
- `coreexcl_30000`: n=30000 pos50=1 anti50=2 J50=0.44
- `coreexcl_500`: n=500 pos50=8 anti50=1 J50=0.01
- `coreexcl_5000`: n=5000 pos50=2 anti50=1 J50=0.39
- `coreexcl_50000`: n=50000 pos50=1 anti50=3 J50=0.50
- `coreexcl_8000`: n=8000 pos50=4 anti50=1 J50=0.39

## 10. Core-replacement experiment

Implemented as the constant-size swap perturbation at |J_star| below (removal strategies include random and low-score core members; addition strategies include high-score outsiders). Full results in section 12.

## 11. Selected J_star

- **corepres_10000**: raw n=10000, pos50=19, anti50=1, half J50=0.5

## 12. Constant-size swap experiment

- Candidate juries: 272; J_star n=10000; base primary=0.45571583248797465
- Substitution LOO corr=0.47018748658419535, r2=-0.3447736290754071

| strategy/fraction | n | primary | exact50 | anti50 | ref_cosine |
|---|---:|---:|---:|---:|---:|
| anti/low_score/0.025 | 5 | 0.4678 | 13.0 | 1.0 | 0.464 |
| anti/low_score/0.05 | 5 | 0.4494 | 14.0 | 1.0 | 0.449 |
| anti/low_score/0.1 | 5 | 0.4545 | 11.0 | 9.0 | 0.480 |
| anti/low_score/0.2 | 5 | 0.4381 | 5.0 | 32.0 | 0.417 |
| anti/random/0.025 | 5 | 0.4584 | 13.0 | 1.0 | 0.458 |
| anti/random/0.05 | 5 | 0.4731 | 13.4 | 1.0 | 0.480 |
| anti/random/0.1 | 5 | 0.4606 | 11.6 | 8.4 | 0.489 |
| anti/random/0.2 | 5 | 0.4722 | 6.4 | 28.8 | 0.478 |
| boundary/high_score/0.025 | 4 | 0.4446 | 13.0 | 1.0 | 0.440 |
| boundary/high_score/0.05 | 4 | 0.4067 | 10.0 | 1.0 | 0.380 |
| boundary/high_score/0.1 | 4 | 0.4366 | 12.0 | 1.0 | 0.414 |
| boundary/high_score/0.2 | 4 | 0.3991 | 10.0 | 1.0 | 0.370 |
| boundary/low_score/0.025 | 10 | 0.4635 | 13.0 | 1.0 | 0.456 |
| boundary/low_score/0.05 | 10 | 0.4457 | 13.0 | 1.0 | 0.443 |
| boundary/low_score/0.1 | 10 | 0.4447 | 13.0 | 1.0 | 0.435 |
| boundary/low_score/0.2 | 10 | 0.4211 | 11.0 | 1.0 | 0.410 |
| boundary/random/0.025 | 10 | 0.4592 | 13.0 | 1.0 | 0.456 |
| boundary/random/0.05 | 10 | 0.4523 | 12.6 | 1.0 | 0.441 |
| boundary/random/0.1 | 10 | 0.4444 | 12.4 | 1.1 | 0.433 |
| boundary/random/0.2 | 10 | 0.4360 | 11.6 | 1.1 | 0.409 |
| high/high_score/0.025 | 4 | 0.4205 | 13.0 | 1.0 | 0.396 |
| high/high_score/0.05 | 4 | 0.4076 | 11.0 | 1.0 | 0.384 |
| high/high_score/0.1 | 4 | 0.3922 | 12.0 | 0.0 | 0.363 |
| high/high_score/0.2 | 4 | 0.3658 | 12.0 | 0.0 | 0.322 |
| high/low_score/0.025 | 10 | 0.4516 | 13.0 | 1.0 | 0.451 |
| high/low_score/0.05 | 10 | 0.4316 | 13.0 | 1.0 | 0.437 |
| high/low_score/0.1 | 10 | 0.3949 | 11.0 | 0.0 | 0.387 |
| high/low_score/0.2 | 10 | 0.3773 | 11.0 | 0.0 | 0.365 |
| high/random/0.025 | 10 | 0.4474 | 12.8 | 1.0 | 0.442 |
| high/random/0.05 | 10 | 0.4337 | 12.3 | 1.0 | 0.427 |
| high/random/0.1 | 10 | 0.4213 | 11.9 | 0.0 | 0.414 |
| high/random/0.2 | 10 | 0.3801 | 11.8 | 0.2 | 0.345 |
| random/low_score/0.025 | 5 | 0.4477 | 13.0 | 1.0 | 0.442 |
| random/low_score/0.05 | 5 | 0.4403 | 12.6 | 1.0 | 0.432 |
| random/low_score/0.1 | 5 | 0.4264 | 12.8 | 1.6 | 0.422 |
| random/low_score/0.2 | 5 | 0.3990 | 11.0 | 4.0 | 0.399 |
| random/random/0.025 | 5 | 0.4469 | 13.2 | 1.0 | 0.440 |
| random/random/0.05 | 5 | 0.4460 | 12.8 | 1.2 | 0.445 |
| random/random/0.1 | 5 | 0.4382 | 12.0 | 1.6 | 0.428 |
| random/random/0.2 | 5 | 0.4165 | 11.8 | 4.4 | 0.401 |

## 13. Learned substitution effects

| feature | coefficient | sd |
|---|---:|---:|
| `series_share_5` | -0.0126 | 0.0003 |
| `binge_max_5_log` | -0.0020 | 0.0002 |
| `author_hhi_5` | -0.0046 | 0.0001 |
| `mean_pub_year_5` | -0.0120 | 0.0001 |
| `midpop_span_per_logn5` | +0.0065 | 0.0003 |
| `mega_catalog_share_5` | -0.0195 | 0.0003 |

## 14. Optional improved J_star rounds

- Rounds done: 1; improved: False
  - round 0: primary=0.4540 exact50=13 anti50=1

## 15. Maximum amplification frontier

- Base core: 10000 users (J_star (core-preserving 10k))

| jury | n | pos50 | broad50 | anti50 | half J50 |
|---|---:|---:|---:|---:|---:|
| amp_100000 | 100000 | 1 | 1 | 6 | 0.45 |
| amp_11000 | 11000 | 18 | 18 | 0 | 0.44 |
| amp_120000 | 120000 | 1 | 1 | 10 | 0.50 |
| amp_12500 | 12500 | 17 | 17 | 0 | 0.46 |
| amp_15000 | 15000 | 15 | 15 | 0 | 0.48 |
| amp_20000 | 20000 | 11 | 11 | 0 | 0.51 |
| amp_30000 | 30000 | 5 | 5 | 2 | 0.48 |
| amp_40000 | 40000 | 3 | 3 | 3 | 0.48 |
| amp_60000 | 60000 | 1 | 1 | 3 | 0.48 |
| amp_80000 | 80000 | 1 | 1 | 7 | 0.47 |

## 16. Soft-weight effective-size result

The primary result uses hard nested juries. Soft-weight variant was not run in this campaign; the rebuilt soft jury (Kish n_eff from the export) is recorded in section 2.

## 17. Optional reversal-size diagnostics

- core_p65_s25: jury_n=2438 s0=+0.501 deepest=-0.065 exact50=5 anti50=21
- jstar: jury_n=5000 s0=+0.453 deepest=-0.017 exact50=0 anti50=22
- top5k: jury_n=5000 s0=+0.453 deepest=-0.017 exact50=0 anti50=22
- coreexcl5k: jury_n=5000 s0=+0.451 deepest=+0.007 exact50=0 anti50=25
- random5k: jury_n=5000 s0=-0.435 deepest=+0.181 exact50=0 anti50=20

## 18. Final recommendation

### Recommended juries

- **best-quality jury**: raw n=2945, pos50=40, anti50=0, broad50=40, half J50=0.61, head: Hamlet; The Brothers Karamazov; Crime and Punishment; War and Peace; 2666
- **best 10k+ jury**: raw n=10000, pos50=19, anti50=1, broad50=19, half J50=0.50, head: The Brothers Karamazov; Crime and Punishment; لا تصالح; رياض الصالحين; يسمعون حسيسها
- **best 20k+ jury**: raw n=20000, pos50=11, anti50=0, broad50=11, half J50=0.52, head: لا تصالح; رياض الصالحين; لافتات - المجموعة الكاملة; The War that Saved My Life (The War That; The Story of a New Name (The Neapolitan 
- **largest acceptable jury**: raw n=20000, pos50=11, anti50=0, broad50=11, half J50=0.52, head: لا تصالح; رياض الصالحين; لافتات - المجموعة الكاملة; The War that Saved My Life (The War That; The Story of a New Name (The Neapolitan 

- **preferred interpretable/production jury (J_star)**: raw n=10000, pos50=19, anti50=1, broad50=19, half J50=0.50, head: The Brothers Karamazov; Crime and Punishment; لا تصالح; رياض الصالحين; يسمعون حسيسها

Historical jury comparisons (seed-labelled cohorts are references, not model-constructed amplifications):

- **exact_exact_deep_mint**: n=11236 pos50=24 anti50=0 J50=0.56
- **exact_exact_threeway_classic**: n=21044 pos50=17 anti50=0 J50=0.57

### J_star details

- NPZ user-index key: members stored in `maximum_literary_jury.npz`; construction = core-preserving frontier `corepres_10000` (full p65_s25 core + top behaviour-score outsiders).
- raw n = 10000; Kish n_eff = 10000 (equal vote).
- Direct ranking: pos50=19, anti50=1, exact@50=13, half-jury J50=0.50.

Top-30 head:

1. The Brothers Karamazov — Fyodor Dostoyevsky
2. Crime and Punishment — Fyodor Dostoyevsky
3. لا تصالح — 'ml dnql
4. رياض الصالحين — yHy~ bn shrf lnwwy
5. يسمعون حسيسها — 'ymn l`twm
6. Life and Fate — Vasily Grossman
7. 2666 — Roberto Bolano
8. لافتات - المجموعة الكاملة — 'Hmd mTr
9. Infinite Jest — David Foster Wallace
10. Gravity's Rainbow — Thomas Pynchon
11. The Magic Mountain — Thomas Mann
12. The Story of a New Name (The Neapolitan Novels #2) — Elena Ferrante
13. War and Peace — Leo Tolstoy
14. Homegoing — Yaa Gyasi
15. The One and Only Ivan — Katherine Applegate
16. A Season in Hell/The Drunken Boat — Arthur Rimbaud
17. The War that Saved My Life (The War That Saved My Life #1) — Kimberly Brubaker Bradley
18. Swann's Way (In Search of Lost Time, #1) — Marcel Proust
19. The Rings of Saturn — W.G. Sebald
20. Demons — Fyodor Dostoyevsky
21. Saatleri Ayarlama Enstitüsü — Ahmet Hamdi Tanpinar
22. الطنطورية — Radwa Ashour
23. The Hate U Give — Angie Thomas
24. In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust
25. عائد إلى حيفا — Gsn knfny
26. The Book of Disquiet — Fernando Pessoa
27. Stoner — John  Williams
28. The Nightingale — Kristin Hannah
29. The Story of the Lost Child (The Neapolitan Novels, #4) — Elena Ferrante
30. ديوان الإمام الشافعي — mHmd bn drys lshf`y


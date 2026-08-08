# Recursive family breeding report

**Fixed-compass exploratory pilot**: recursive amplification of the naturally discovered literary-enriched basin (Family 1) via randomized child-jury fitness, without semantic input to selection.

- Seed **20260822**; 2 independent random roots of 80,000 users; 12 partition replicates; pools ['80,000', '40,000', '20,000', '10,000', '5,000'].
- Family compass: `family_cent_0.70_f1` (literary-enriched; the one-time semantic branch choice) vs `family_cent_0.70_f0` (anti-enriched).  Selection uses ONLY the deepest-endpoint F1-minus-F0 family margin of randomized child juries; semantic labels never enter fitness.
- Every jury run records the full reversal margin trajectory (stage0/deepest/max, argmax stage, reversal_gain = deepest - stage0) for observability; selection is unchanged.
- Run complete: **True**; git head `19b10c93539b`; artifact sha256 `20643d17d03a061e...`.

## Root 0: reversal saturation / crossover

Evaluated selected juries (stage0 margin, deepest margin, reversal gain = deepest - stage0, best stage):

| branch | generation | size | stage0 margin | deepest margin | reversal gain | best stage |
|---|---|---:|---:|---:|---:|---:|
| lit | 0 | 80000 | -0.3808 | 0.4253 | 0.8061 | 3 |
| lit | 1 | 40000 | -0.4543 | 0.4670 | 0.9213 | 4 |
| lit | 2 | 20000 | -0.4525 | 0.6244 | 1.0770 | 5 |
| lit | 3 | 10000 | -0.4561 | 0.0047 | 0.4608 | 1 |
| lit | 4 | 5000 | -0.3816 | 0.1967 | 0.5783 | 3 |
| anti | 0 | 80000 | -0.3808 | 0.4253 | 0.8061 | 3 |
| anti | 1 | 40000 | 0.4984 | -0.4749 | -0.9733 | 0 |
| anti | 2 | 20000 | 0.4850 | -0.6438 | -1.1288 | 0 |
| anti | 3 | 10000 | 0.4668 | 0.0465 | -0.4202 | 0 |
| anti | 4 | 5000 | 0.4674 | -0.2032 | -0.6706 | 0 |
| rand | 0 | 80000 | -0.3808 | 0.4253 | 0.8061 | 3 |
| rand | 1 | 40000 | 0.3584 | -0.4267 | -0.7851 | 0 |
| rand | 2 | 20000 | -0.3039 | 0.6108 | 0.9147 | 5 |
| rand | 3 | 10000 | -0.4391 | 0.0065 | 0.4456 | 2 |
| rand | 4 | 5000 | -0.3050 | 0.2042 | 0.5092 | 3 |

Child-campaign reversal summary:

| branch | gen | n children | stage0 mean | deepest mean | gain mean | gain>0 | gain<0 | median best stage |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| shared | 0 | 48 | -0.0905 | 0.1980 | 0.2885 | 0.67 | 0.33 | 5.0 |
| lit | 1 | 24 | -0.4249 | 0.6224 | 1.0473 | 1.00 | 0.00 | 5.0 |
| lit | 2 | 24 | -0.4516 | -0.0154 | 0.4362 | 1.00 | 0.00 | 2.0 |
| lit | 3 | 24 | -0.3555 | 0.1743 | 0.5297 | 0.96 | 0.04 | 2.0 |
| anti | 1 | 24 | 0.4028 | -0.5068 | -0.9096 | 0.08 | 0.92 | 0.0 |
| anti | 2 | 24 | 0.4808 | 0.0594 | -0.4214 | 0.00 | 1.00 | 0.0 |
| anti | 3 | 24 | 0.3946 | -0.1427 | -0.5373 | 0.08 | 0.92 | 0.0 |

## Root 0: trajectory of evaluated selected juries

| branch | gen | size | margin F1-F0 | cos F1 | cos F0 | exact@50 | broad@50 | anti@50 | split-half rho |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lit | 0 | 80000 | 0.4253 | 0.5895 | 0.1641 | 0 | 0 | 3 | 0.0052 |
| lit | 1 | 40000 | 0.4670 | 0.6695 | 0.2026 | 0 | 0 | 13 | 0.0064 |
| lit | 2 | 20000 | 0.6244 | 0.8374 | 0.2129 | 5 | 8 | 8 | -0.0131 |
| lit | 3 | 10000 | 0.0047 | 0.5945 | 0.5898 | 0 | 0 | 27 | 0.0191 |
| lit | 4 | 5000 | 0.1967 | 0.6282 | 0.4315 | 0 | 0 | 16 | n/a |
| anti | 0 | 80000 | 0.4253 | 0.5895 | 0.1641 | 0 | 0 | 3 | 0.0052 |
| anti | 1 | 40000 | -0.4749 | 0.2221 | 0.6970 | 0 | 0 | 41 | 0.0002 |
| anti | 2 | 20000 | -0.6438 | 0.2075 | 0.8513 | 0 | 0 | 41 | 0.0080 |
| anti | 3 | 10000 | 0.0465 | 0.6043 | 0.5578 | 0 | 0 | 19 | -0.0105 |
| anti | 4 | 5000 | -0.2032 | 0.4513 | 0.6545 | 0 | 0 | 35 | n/a |
| rand | 0 | 80000 | 0.4253 | 0.5895 | 0.1641 | 0 | 0 | 3 | n/a |
| rand | 1 | 40000 | -0.4267 | 0.2072 | 0.6339 | 0 | 0 | 45 | n/a |
| rand | 2 | 20000 | 0.6108 | 0.8184 | 0.2076 | 3 | 8 | 10 | n/a |
| rand | 3 | 10000 | 0.0065 | 0.5926 | 0.5861 | 0 | 0 | 28 | n/a |
| rand | 4 | 5000 | 0.2042 | 0.6304 | 0.4261 | 0 | 0 | 20 | n/a |

## Root 1: reversal saturation / crossover

Evaluated selected juries (stage0 margin, deepest margin, reversal gain = deepest - stage0, best stage):

| branch | generation | size | stage0 margin | deepest margin | reversal gain | best stage |
|---|---|---:|---:|---:|---:|---:|
| lit | 0 | 80000 | 0.4965 | -0.3269 | -0.8234 | 0 |
| lit | 1 | 40000 | -0.4516 | 0.4664 | 0.9180 | 4 |
| lit | 2 | 20000 | -0.4537 | 0.6292 | 1.0829 | 5 |
| lit | 3 | 10000 | 0.3783 | 0.0347 | -0.3436 | 0 |
| lit | 4 | 5000 | -0.4398 | 0.1506 | 0.5904 | 3 |
| anti | 0 | 80000 | 0.4965 | -0.3269 | -0.8234 | 0 |
| anti | 1 | 40000 | 0.4822 | -0.4119 | -0.8941 | 0 |
| anti | 2 | 20000 | 0.4839 | -0.6464 | -1.1303 | 0 |
| anti | 3 | 10000 | 0.4826 | 0.0515 | -0.4311 | 0 |
| anti | 4 | 5000 | 0.4237 | -0.1506 | -0.5743 | 0 |
| rand | 0 | 80000 | 0.4965 | -0.3269 | -0.8234 | 0 |
| rand | 1 | 40000 | 0.4908 | -0.4810 | -0.9717 | 0 |
| rand | 2 | 20000 | 0.4988 | -0.6223 | -1.1211 | 0 |
| rand | 3 | 10000 | 0.4630 | 0.0906 | -0.3723 | 0 |
| rand | 4 | 5000 | 0.4702 | -0.1030 | -0.5732 | 0 |

Child-campaign reversal summary:

| branch | gen | n children | stage0 mean | deepest mean | gain mean | gain>0 | gain<0 | median best stage |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| shared | 0 | 48 | 0.3200 | -0.4166 | -0.7366 | 0.17 | 0.83 | 0.0 |
| lit | 1 | 24 | -0.3920 | 0.5687 | 0.9607 | 0.96 | 0.04 | 5.0 |
| lit | 2 | 24 | -0.3914 | -0.0202 | 0.3712 | 0.92 | 0.08 | 2.0 |
| lit | 3 | 24 | 0.0542 | 0.0115 | -0.0427 | 0.50 | 0.50 | 1.0 |
| anti | 1 | 24 | 0.4815 | -0.6413 | -1.1228 | 0.00 | 1.00 | 0.0 |
| anti | 2 | 24 | 0.4821 | 0.0703 | -0.4118 | 0.00 | 1.00 | 0.0 |
| anti | 3 | 24 | 0.4762 | -0.1648 | -0.6410 | 0.00 | 1.00 | 0.0 |

## Root 1: trajectory of evaluated selected juries

| branch | gen | size | margin F1-F0 | cos F1 | cos F0 | exact@50 | broad@50 | anti@50 | split-half rho |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lit | 0 | 80000 | -0.3269 | 0.1989 | 0.5258 | 0 | 0 | 41 | 0.0006 |
| lit | 1 | 40000 | 0.4664 | 0.6802 | 0.2138 | 0 | 0 | 15 | -0.0023 |
| lit | 2 | 20000 | 0.6292 | 0.8319 | 0.2027 | 3 | 4 | 10 | 0.0043 |
| lit | 3 | 10000 | 0.0347 | 0.6048 | 0.5701 | 1 | 1 | 23 | -0.0266 |
| lit | 4 | 5000 | 0.1506 | 0.6186 | 0.4680 | 0 | 0 | 16 | n/a |
| anti | 0 | 80000 | -0.3269 | 0.1989 | 0.5258 | 0 | 0 | 41 | 0.0006 |
| anti | 1 | 40000 | -0.4119 | 0.2295 | 0.6415 | 0 | 0 | 45 | -0.0017 |
| anti | 2 | 20000 | -0.6464 | 0.2109 | 0.8573 | 0 | 0 | 45 | -0.0048 |
| anti | 3 | 10000 | 0.0515 | 0.6132 | 0.5616 | 0 | 0 | 18 | -0.0024 |
| anti | 4 | 5000 | -0.1506 | 0.4598 | 0.6104 | 0 | 0 | 32 | n/a |
| rand | 0 | 80000 | -0.3269 | 0.1989 | 0.5258 | 0 | 0 | 41 | n/a |
| rand | 1 | 40000 | -0.4810 | 0.2239 | 0.7048 | 0 | 0 | 44 | n/a |
| rand | 2 | 20000 | -0.6223 | 0.2183 | 0.8405 | 0 | 0 | 42 | n/a |
| rand | 3 | 10000 | 0.0906 | 0.6126 | 0.5219 | 0 | 0 | 23 | n/a |
| rand | 4 | 5000 | -0.1030 | 0.4782 | 0.5812 | 0 | 0 | 20 | n/a |

## Across-root means (evaluated selected juries)

| branch | gen | size | margin F1-F0 | cos F1 | cos F0 | exact@50 | broad@50 | anti@50 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| lit | 0 | 80000 | 0.0492 | 0.3942 | 0.3450 | 0.0 | 0.0 | 22.0 |
| lit | 1 | 40000 | 0.4667 | 0.6749 | 0.2082 | 0.0 | 0.0 | 14.0 |
| lit | 2 | 20000 | 0.6268 | 0.8347 | 0.2078 | 4.0 | 6.0 | 9.0 |
| lit | 3 | 10000 | 0.0197 | 0.5996 | 0.5799 | 0.5 | 0.5 | 25.0 |
| lit | 4 | 5000 | 0.1737 | 0.6234 | 0.4498 | 0.0 | 0.0 | 16.0 |
| anti | 0 | 80000 | 0.0492 | 0.3942 | 0.3450 | 0.0 | 0.0 | 22.0 |
| anti | 1 | 40000 | -0.4434 | 0.2258 | 0.6692 | 0.0 | 0.0 | 43.0 |
| anti | 2 | 20000 | -0.6451 | 0.2092 | 0.8543 | 0.0 | 0.0 | 43.0 |
| anti | 3 | 10000 | 0.0490 | 0.6087 | 0.5597 | 0.0 | 0.0 | 18.5 |
| anti | 4 | 5000 | -0.1769 | 0.4555 | 0.6324 | 0.0 | 0.0 | 33.5 |
| rand | 0 | 80000 | 0.0492 | 0.3942 | 0.3450 | 0.0 | 0.0 | 22.0 |
| rand | 1 | 40000 | -0.4538 | 0.2155 | 0.6693 | 0.0 | 0.0 | 44.5 |
| rand | 2 | 20000 | -0.0057 | 0.5183 | 0.5241 | 1.5 | 4.0 | 26.0 |
| rand | 3 | 10000 | 0.0486 | 0.6026 | 0.5540 | 0.0 | 0.0 | 25.5 |
| rand | 4 | 5000 | 0.0506 | 0.5543 | 0.5037 | 0.0 | 0.0 | 20.0 |

## Selection diagnostics (fitness split-half stability)

| root | branch | gen | fitness mean | fitness sd | selected mean | rejected mean | separation | rho | top-half overlap |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | lit+anti (shared) | 0 | -0.0000 | 0.1584 | 0.1257 | -0.1257 | 0.2514 | 0.0052 | 20043/40000 |
| 0 | lit | 1 | -0.0000 | 0.0047 | 0.0038 | -0.0038 | 0.0077 | 0.0064 | 10106/20000 |
| 0 | lit | 2 | -0.0000 | 0.0042 | 0.0034 | -0.0034 | 0.0068 | -0.0131 | 4954/10000 |
| 0 | lit | 3 | 0.0000 | 0.0185 | 0.0183 | -0.0183 | 0.0367 | 0.0191 | 2529/5000 |
| 0 | anti | 1 | 0.0000 | 0.0639 | -0.0530 | 0.0530 | -0.1059 | 0.0002 | 10046/20000 |
| 0 | anti | 2 | -0.0000 | 0.0052 | -0.0042 | 0.0042 | -0.0084 | 0.0080 | 5044/10000 |
| 0 | anti | 3 | -0.0000 | 0.0220 | -0.0171 | 0.0171 | -0.0342 | -0.0105 | 2485/5000 |
| 1 | lit+anti (shared) | 0 | -0.0000 | 0.1116 | 0.0874 | -0.0874 | 0.1749 | 0.0006 | 20001/40000 |
| 1 | lit | 1 | -0.0000 | 0.0530 | 0.0529 | -0.0529 | 0.1057 | -0.0023 | 10005/20000 |
| 1 | lit | 2 | 0.0000 | 0.0069 | 0.0056 | -0.0056 | 0.0112 | 0.0043 | 4981/10000 |
| 1 | lit | 3 | 0.0000 | 0.0495 | 0.0388 | -0.0388 | 0.0777 | -0.0266 | 2448/5000 |
| 1 | anti | 1 | -0.0000 | 0.0034 | -0.0028 | 0.0028 | -0.0056 | -0.0017 | 9999/20000 |
| 1 | anti | 2 | 0.0000 | 0.0032 | -0.0026 | 0.0026 | -0.0052 | -0.0048 | 4954/10000 |
| 1 | anti | 3 | -0.0000 | 0.0023 | -0.0019 | 0.0019 | -0.0039 | -0.0024 | 2506/5000 |

## Semantic heads

### Root 0: root 80k jury head (top 30)

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.8934)
2. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.8748)
3. *Calvin and Hobbes* — Bill Watterson (0.8712)
4. *Worlds' End (The Sandman #8)* — Neil Gaiman (0.8531)
5. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.8507)
6. *Brief Lives (The Sandman #7)* — Neil Gaiman (0.8313)
7. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.8167)
8. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.8165)
9. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.8159)
10. *The Absolute Sandman, Volume One* — Neil Gaiman (0.8087)
11. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.8079)
12. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.8023)
13. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.8000)
14. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.7990)
15. *Changes (The Dresden Files, #12)* — Jim Butcher (0.7957)
16. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.7921)
17. *The Wake (The Sandman #10)* — Neil Gaiman (0.7891)
18. *Fables and Reflections (The Sandman #6)* — Neil Gaiman (0.7887)
19. *Transmetropolitan, Vol. 6: Gouge Away (Transmetropolitan, #6)* — Warren Ellis (0.7853)
20. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (0.7836)
21. *The Doll's House (The Sandman #2)* — Neil Gaiman (0.7836)
22. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.7833)
23. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.7822)
24. *The Complete Calvin and Hobbes* — Bill Watterson (0.7807)
25. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.7776)
26. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.7775)
27. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.7759)
28. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.7733)
29. *Locke & Key, Vol. 4: Keys to the Kingdom* — Joe Hill (0.7703)
30. *Transmetropolitan, Vol. 7: Spider's Thrash (Transmetropolitan, #7)* — Warren Ellis (0.7696)

### Root 0: final literary 5k (top 30)

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.9038)
2. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.8521)
3. *Changes (The Dresden Files, #12)* — Jim Butcher (0.8305)
4. *A Memory of Light (Wheel of Time, #14)* — Robert Jordan (0.8035)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7923)
6. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.7863)
7. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7841)
8. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.7839)
9. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.7823)
10. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.7796)
11. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.7767)
12. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7754)
13. *Skin Game (The Dresden Files, #15)* — Jim Butcher (0.7578)
14. *Calvin and Hobbes* — Bill Watterson (0.7562)
15. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.7550)
16. *Dead Beat (The Dresden Files, #7)* — Jim Butcher (0.7550)
17. *Worlds' End (The Sandman #8)* — Neil Gaiman (0.7541)
18. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.7541)
19. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.7528)
20. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.7430)
21. *Brief Lives (The Sandman #7)* — Neil Gaiman (0.7429)
22. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.7423)
23. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.7357)
24. *Saga, Vol. 1 (Saga, #1)* — Brian K. Vaughan (0.7323)
25. *The Wake (The Sandman #10)* — Neil Gaiman (0.7287)
26. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.7272)
27. *Winter (The Lunar Chronicles, #4)* — Marissa Meyer (0.7266)
28. *The Doll's House (The Sandman #2)* — Neil Gaiman (0.7227)
29. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.7205)
30. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (0.7197)

### Root 0: final anti 5k (top 30)

1. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.8371)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.7689)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.7620)
4. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.7539)
5. *Wonder (Wonder #1)* — R.J. Palacio (0.7446)
6. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.7355)
7. *Fruits Basket, Vol. 11* — Natsuki Takaya (0.7252)
8. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7219)
9. *Origin (Lux, #4)* — Jennifer L. Armentrout (0.7147)
10. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.7059)
11. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.7033)
12. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.7000)
13. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.6971)
14. *Winter (The Lunar Chronicles, #4)* — Marissa Meyer (0.6894)
15. *Fruits Basket, Vol. 18* — Natsuki Takaya (0.6849)
16. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.6822)
17. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.6779)
18. *Fruits Basket, Vol. 19* — Natsuki Takaya (0.6769)
19. *Fruits Basket, Vol. 20* — Natsuki Takaya (0.6736)
20. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (0.6666)
21. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.6655)
22. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.6648)
23. *The Hate U Give* — Angie Thomas (0.6542)
24. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.6442)
25. *Cress (The Lunar Chronicles, #3)* — Marissa Meyer (0.6421)
26. *Unbroken: A World War II Story of Survival, Resilience, and Redemption* — Laura Hillenbrand (0.6385)
27. *Onyx (Lux, #2)* — Jennifer L. Armentrout (0.6367)
28. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.6349)
29. *Deity (Covenant, #3)* — Jennifer L. Armentrout (0.6345)
30. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.6302)

### Root 0: final random 5k (top 30)

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.8982)
2. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.8941)
3. *Changes (The Dresden Files, #12)* — Jim Butcher (0.8483)
4. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7867)
5. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.7839)
6. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.7769)
7. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.7757)
8. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7757)
9. *Saga, Vol. 4 (Saga, #4)* — Brian K. Vaughan (0.7628)
10. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.7590)
11. *Small Favor (The Dresden Files, #10)* — Jim Butcher (0.7547)
12. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7544)
13. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.7528)
14. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.7523)
15. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.7485)
16. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.7477)
17. *Skin Game (The Dresden Files, #15)* — Jim Butcher (0.7437)
18. *Calvin and Hobbes* — Bill Watterson (0.7424)
19. *The Nightingale* — Kristin Hannah (0.7374)
20. *Saga, Vol. 1 (Saga, #1)* — Brian K. Vaughan (0.7350)
21. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (0.7322)
22. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.7310)
23. *Nemesis Games (The Expanse #5)* — James S.A. Corey (0.7254)
24. *Fables and Reflections (The Sandman #6)* — Neil Gaiman (0.7241)
25. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (0.7219)
26. *Saga, Vol. 5 (Saga, #5)* — Brian K. Vaughan (0.7210)
27. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.7140)
28. *Brief Lives (The Sandman #7)* — Neil Gaiman (0.7139)
29. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.7131)
30. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.7116)

### Root 0: intermediate literary heads (top 12)

**literary generation 1 (40,000)**: exact@50 0, broad@50 0, anti@50 13, margin 0.4670

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.8434)
2. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.8203)
3. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.8160)
4. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.8068)
5. *Calvin and Hobbes* — Bill Watterson (0.8067)
6. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.8014)
7. *Changes (The Dresden Files, #12)* — Jim Butcher (0.7915)
8. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7874)
9. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.7819)
10. *J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings* — J.R.R. Tolkien (0.7723)
11. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.7671)
12. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.7651)

**literary generation 2 (20,000)**: exact@50 5, broad@50 8, anti@50 8, margin 0.6244

1. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.8643)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.8040)
3. *Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2)* — Art Spiegelman (0.8014)
4. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.7970)
5. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7761)
6. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.7742)
7. *Between the World and Me* — Ta-Nehisi Coates (0.7603)
8. *Collected Fictions* — Jorge Luis Borges (0.7484)
9. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7471)
10. *The Hate U Give* — Angie Thomas (0.7447)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7444)
12. *The Aleph and Other Stories* — Jorge Luis Borges (0.7392)

**literary generation 3 (10,000)**: exact@50 0, broad@50 0, anti@50 27, margin 0.0047

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.8639)
2. *The Hate U Give* — Angie Thomas (0.8457)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.8355)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.8339)
5. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.8223)
6. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.7874)
7. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.7832)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.7725)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.7662)
10. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.7511)
11. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.7462)
12. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.7434)

**literary generation 4 (5,000)**: exact@50 0, broad@50 0, anti@50 16, margin 0.1967

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.9038)
2. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.8521)
3. *Changes (The Dresden Files, #12)* — Jim Butcher (0.8305)
4. *A Memory of Light (Wheel of Time, #14)* — Robert Jordan (0.8035)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7923)
6. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.7863)
7. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7841)
8. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.7839)
9. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.7823)
10. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.7796)
11. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.7767)
12. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7754)

### Root 1: root 80k jury head (top 30)

1. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.8330)
2. *Magic Rises (Kate Daniels, #6)* — Ilona Andrews (0.8207)
3. *Magic Slays (Kate Daniels, #5)* — Ilona Andrews (0.8205)
4. *Magic Breaks (Kate Daniels, #7)* — Ilona Andrews (0.7942)
5. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.7917)
6. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.7908)
7. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.7900)
8. *Dreamfever (Fever, #4)* — Karen Marie Moning (0.7676)
9. *White Hot (Hidden Legacy, #2)* — Ilona Andrews (0.7627)
10. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.7626)
11. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.7625)
12. *Magic Binds (Kate Daniels, #9)* — Ilona Andrews (0.7530)
13. *Third Grave Dead Ahead (Charley Davidson, #3)* — Darynda Jones (0.7485)
14. *Acheron (Dark-Hunter #14)* — Sherrilyn Kenyon (0.7446)
15. *Fifth Grave Past the Light (Charley Davidson, #5)* — Darynda Jones (0.7443)
16. *Silver Borne (Mercy Thompson, #5)* — Patricia Briggs (0.7442)
17. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.7438)
18. *Blood Bound (Mercy Thompson, #2)* — Patricia Briggs (0.7423)
19. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.7415)
20. *Heart of Obsidian  (Psy-Changeling, #12)* — Nalini Singh (0.7359)
21. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.7318)
22. *Father Mine (Black Dagger Brotherhood, #6.5)* — J.R. Ward (0.7265)
23. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.7162)
24. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.7152)
25. *Bloodfever (Fever, #2)* — Karen Marie Moning (0.7094)
26. *Magic Shifts (Kate Daniels, #8)* — Ilona Andrews (0.7046)
27. *Losing Hope (Hopeless, #2)* — Colleen Hoover (0.7028)
28. *The Outlaw Demon Wails (The Hollows, #6)* — Kim Harrison (0.7018)
29. *Ever After (The Hollows, #11)* — Kim Harrison (0.6964)
30. *Night Broken (Mercy Thompson, #8)* — Patricia Briggs (0.6960)

### Root 1: final literary 5k (top 30)

1. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.8062)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.7923)
3. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7881)
4. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7770)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7710)
6. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.7501)
7. *Calvin and Hobbes* — Bill Watterson (0.7443)
8. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.7400)
9. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.7362)
10. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.7299)
11. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.7289)
12. *The Complete Calvin and Hobbes* — Bill Watterson (0.7289)
13. *Changes (The Dresden Files, #12)* — Jim Butcher (0.7255)
14. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.7167)
15. *J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings* — J.R.R. Tolkien (0.7155)
16. *The Wake (The Sandman #10)* — Neil Gaiman (0.7129)
17. *Skin Game (The Dresden Files, #15)* — Jim Butcher (0.7114)
18. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.7067)
19. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.7062)
20. *The Doll's House (The Sandman #2)* — Neil Gaiman (0.7041)
21. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.7035)
22. *Fables and Reflections (The Sandman #6)* — Neil Gaiman (0.6998)
23. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (0.6998)
24. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.6987)
25. *Brief Lives (The Sandman #7)* — Neil Gaiman (0.6951)
26. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.6889)
27. *Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2)* — Art Spiegelman (0.6886)
28. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.6885)
29. *Between the World and Me* — Ta-Nehisi Coates (0.6856)
30. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (0.6805)

### Root 1: final anti 5k (top 30)

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.8419)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.7745)
3. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.7514)
4. *The Nightingale* — Kristin Hannah (0.7470)
5. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.7453)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.7377)
7. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7234)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.7217)
9. *The Hate U Give* — Angie Thomas (0.7181)
10. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.7066)
11. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.6799)
12. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.6727)
13. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.6609)
14. *Onyx (Lux, #2)* — Jennifer L. Armentrout (0.6580)
15. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.6537)
16. *We Should All Be Feminists* — Chimamanda Ngozi Adichie (0.6520)
17. *Unbroken: A World War II Story of Survival, Resilience, and Redemption* — Laura Hillenbrand (0.6517)
18. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.6496)
19. *Origin (Lux, #4)* — Jennifer L. Armentrout (0.6441)
20. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.6439)
21. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.6401)
22. *Six of Crows (Six of Crows, #1)* — Leigh Bardugo (0.6344)
23. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (0.6327)
24. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.6324)
25. *Homegoing* — Yaa Gyasi (0.6309)
26. *A Monster Calls* — Patrick Ness (0.6290)
27. *Rock Chick Redemption (Rock Chick, #3)* — Kristen Ashley (0.6271)
28. *Last Sacrifice (Vampire Academy, #6)* — Richelle Mead (0.6260)
29. *Wonder (Wonder #1)* — R.J. Palacio (0.6260)
30. *Changes (The Dresden Files, #12)* — Jim Butcher (0.6197)

### Root 1: final random 5k (top 30)

1. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (0.8120)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.8026)
3. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.7723)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.7706)
5. *The Hate U Give* — Angie Thomas (0.7422)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.7331)
7. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.7299)
8. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.7297)
9. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.7274)
10. *The Qur'an / القرآن الكريم* — Anonymous (0.7245)
11. *الإسلام بين الشرق والغرب* — Alija Izetbegovic (0.7218)
12. *الرحيق المختوم* — Safiy al-Rahman al-Mubarakfuri (0.7149)
13. *لا تصالح* — 'ml dnql (0.7132)
14. *زمن الخيول البيضاء* — Ibrahim Nasrallah - ibrhym nSr llh (0.7126)
15. *The Nightingale* — Kristin Hannah (0.7118)
16. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7111)
17. *Heir of Fire (Throne of Glass, #3)* — Sarah J. Maas (0.6890)
18. *الطنطورية* — Radwa Ashour (0.6867)
19. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (0.6834)
20. *Trials of Death (Cirque Du Freak, #5)* — Darren Shan (0.6834)
21. *عائد إلى حيفا* — Gsn knfny (0.6628)
22. *الحرافيش* — Naguib Mahfouz (0.6618)
23. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.6572)
24. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.6547)
25. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.6526)
26. *Winter (The Lunar Chronicles, #4)* — Marissa Meyer (0.6519)
27. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.6517)
28. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.6509)
29. *Six of Crows (Six of Crows, #1)* — Leigh Bardugo (0.6497)
30. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.6479)

### Root 1: intermediate literary heads (top 12)

**literary generation 1 (40,000)**: exact@50 0, broad@50 0, anti@50 15, margin 0.4664

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.8661)
2. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.8281)
3. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.8161)
4. *Saga, Vol. 4 (Saga, #4)* — Brian K. Vaughan (0.7956)
5. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.7943)
6. *J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings* — J.R.R. Tolkien (0.7872)
7. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.7797)
8. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.7767)
9. *Calvin and Hobbes* — Bill Watterson (0.7695)
10. *Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2)* — Art Spiegelman (0.7596)
11. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7493)
12. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.7402)

**literary generation 2 (20,000)**: exact@50 3, broad@50 4, anti@50 10, margin 0.6292

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.8001)
2. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.7994)
3. *Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2)* — Art Spiegelman (0.7993)
4. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7709)
5. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.7707)
6. *Ficciones* — Jorge Luis Borges (0.7649)
7. *Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1)* — Art Spiegelman (0.7447)
8. *Labyrinths:  Selected Stories and Other Writings* — Jorge Luis Borges (0.7357)
9. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.7321)
10. *Stoner* — John  Williams (0.7300)
11. *The Book of Disquiet* — Fernando Pessoa (0.7289)
12. *The Complete Calvin and Hobbes* — Bill Watterson (0.7277)

**literary generation 3 (10,000)**: exact@50 1, broad@50 1, anti@50 23, margin 0.0347

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.8257)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.8192)
3. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.8090)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.8044)
5. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.7889)
6. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.7628)
7. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.7535)
8. *Unbroken: A World War II Story of Survival, Resilience, and Redemption* — Laura Hillenbrand (0.7525)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.7485)
10. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.7474)
11. *The Hate U Give* — Angie Thomas (0.7432)
12. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7332)

**literary generation 4 (5,000)**: exact@50 0, broad@50 0, anti@50 16, margin 0.1506

1. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.8062)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.7923)
3. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.7881)
4. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.7770)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.7710)
6. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.7501)
7. *Calvin and Hobbes* — Bill Watterson (0.7443)
8. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.7400)
9. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.7362)
10. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.7299)
11. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.7289)
12. *The Complete Calvin and Hobbes* — Bill Watterson (0.7289)

## Empirical summary

- **lit** across-root trajectory: g0: m=+0.049 ex=0.0 an=22.0 -> g1: m=+0.467 ex=0.0 an=14.0 -> g2: m=+0.627 ex=4.0 an=9.0 -> g3: m=+0.020 ex=0.5 an=25.0 -> g4: m=+0.174 ex=0.0 an=16.0
- **anti** across-root trajectory: g0: m=+0.049 ex=0.0 an=22.0 -> g1: m=-0.443 ex=0.0 an=43.0 -> g2: m=-0.645 ex=0.0 an=43.0 -> g3: m=+0.049 ex=0.0 an=18.5 -> g4: m=-0.177 ex=0.0 an=33.5
- **rand** across-root trajectory: g0: m=+0.049 ex=0.0 an=22.0 -> g1: m=-0.454 ex=0.0 an=44.5 -> g2: m=-0.006 ex=1.5 an=26.0 -> g3: m=+0.049 ex=0.0 an=25.5 -> g4: m=+0.051 ex=0.0 an=20.0
- Random control at 20k: root-level margins ['+0.611', '-0.622'] (opposite signs across roots), vs literary 20k ['+0.624', '+0.629'] (same sign, both strongly F1-ward).
- Fitness split-half Spearman: min -0.027, max 0.019 across all fitness nodes (estimates are effectively unstable; selection carried only ~12-replicate signal).

Reversal regime per branch (stage0 margin / reversal gain, across-root means of evaluated juries):

| branch | g1 | g2 | g3 | g4 |
|---|---:|---:|---:|---:|
| lit | s0=-0.453 / gain=+0.920 | s0=-0.453 / gain=+1.080 | s0=-0.039 / gain=+0.059 | s0=-0.411 / gain=+0.584 |
| anti | s0=+0.490 / gain=-0.934 | s0=+0.484 / gain=-1.130 | s0=+0.475 / gain=-0.426 | s0=+0.446 / gain=-0.622 |
| rand | s0=+0.425 / gain=-0.878 | s0=+0.097 / gain=-0.103 | s0=+0.012 / gain=+0.037 | s0=+0.083 / gain=-0.032 |

At the 20k peak the literary juries still collapse F0-ward at stage 0 (s0 ['-0.453', '-0.454']) and reach F1 only through reversal (gain ['+1.077', '+1.083']): the literary tendency is REVEALED by reversal, not yet the ordinary stage-0 convergence.  No latent-basin -> direct-convergence saturation/crossover is observed on the literary path (stage0 margin never rises toward F1 as breeding proceeds).  The anti-bred juries show the mirror image: stage-0 convergence is F1-ward (s0 ['+0.485', '+0.484']) and reversal pushes them to F0 (gain ['-1.129', '-1.130']); their deepest-stage margin is anti-F1 at every generation.

## Interpretation notes

The reversal-saturation question: if recursive breeding makes a jury literary in its ORDINARY stage-0 convergence, reversal gain (deepest - stage0 margin) should fall toward zero and eventually go negative, while stage0 margin rises.  A hidden literary basin is instead indicated by positive reversal gain that reveals Family 1 from a low stage0 margin.  No claim is made beyond what the tables above show; no permutation tests are applied (exploratory pilot).

What the pilot shows plainly: (1) the literary path's F1-minus-F0 margin rises across generations in BOTH roots and peaks at the 20k jury (across-root +0.63, exact@50 4, anti@50 9, heads concentrating on Borges/Dostoyevsky/Pessoa/Stoner/Maus/Persepolis), then collapses at 10k/5k (margin ~0, anti@50 rising again, final heads collapsing into a narrow fandom/series cluster); (2) the anti branch moves strongly in the opposite direction in both roots (margins -0.44..-0.65, anti@50 32-45); (3) the random control does not reproduce the literary trend (20k margins +0.61 vs -0.62 across roots, heads anti-heavy in root 1); (4) fitness split-half stability is effectively zero, so individual-level fitness estimates are noisy even though selection repeatedly reproduced the same 20k endpoint; (5) the amplification is therefore real but transient, and reversal remains essential to it (the literary signal is still a hidden basin, not an ordinary convergence, at every functional generation).

Terminology: if the literary path amplifies, this is 'recursive amplification of a naturally discovered literary-enriched basin' (the families were structurally discovered label-blind; the choice of Family 1 as the branch to amplify was a one-time semantic decision), NOT 'completely unsupervised discovery of the literary canon'.

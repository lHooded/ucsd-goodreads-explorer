# Seedless signed spectral pilot

## Design

Discovery used only `(user_id, work_id, rating)`. Each reader contributes equal total positive (5-star) and negative (1–3-star) mass. Ratings-derived book popularity, mean, five-star tendency, user activity, and generosity are projected out. Titles, authors, flags, and semantic lists are loaded only after all full/half/null decompositions finish.

Matrix: **233,271 users × 6,583 works**, **7,039,295 signed edges**. Runtime: **26.0s**; matrix cache: **15.5 MiB**.

The two half-sample fits use disjoint readers. The shuffled null preserves each reader's positive/negative counts and the global positive/negative book frequencies while destroying reader-level co-preference.

## Spectrum and stability

### Stable-subspace test

Unlike individual-vector correlation, this test allows tied or nearly tied modes to rotate within the same shared subspace.

| leading modes | full↔half mean sq. corr | full↔half weakest | half↔half mean sq. corr | half↔half weakest |
|---:|---:|---:|---:|---:|
| 1 | 0.987 | 0.994 | 0.950 | 0.975 |
| 2 | 0.971 | 0.977 | 0.905 | 0.926 |
| 3 | 0.937 | 0.919 | 0.799 | 0.727 |
| 4 | 0.774 | 0.406 | 0.793 | 0.694 |
| 6 | 0.940 | 0.911 | 0.837 | 0.748 |
| 8 | 0.936 | 0.906 | 0.857 | 0.844 |
| 12 | 0.853 | 0.389 | 0.740 | 0.062 |
| 16 | 0.827 | 0.385 | 0.711 | 0.078 |
| 24 | 0.770 | 0.050 | 0.663 | 0.005 |

### Individual modes

`eff. books` is the inverse concentration of squared loadings: larger means broader; `top50 mass` is the fraction of a mode carried by its 50 most extreme books.

| mode | singular | null | excess | residual | half corr | half pole J@100 | eff. books | top50 mass | exact lit +/− @50 | broad lit +/− @50 | anti +/− @50 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1.6466 | 0.9089 | 1.81 | 5.16e-03 | 0.994 | 0.914 | 357 | 0.309 | 1/0 | 1/0 | 31/50 |
| 2 | 1.5276 | 0.9075 | 1.68 | 1.23e-02 | 0.977 | 0.763 | 117 | 0.507 | 0/0 | 0/0 | 41/49 |
| 3 | 1.4835 | 0.9073 | 1.63 | 2.27e-02 | 0.911 | 0.640 | 187 | 0.456 | 0/0 | 0/0 | 50/41 |
| 4 | 1.4530 | 0.9069 | 1.60 | 2.48e-02 | 0.729 | 0.459 | 39 | 0.730 | 0/0 | 0/0 | 50/49 |
| 5 | 1.4507 | 0.9060 | 1.60 | 3.41e-02 | 0.836 | 0.561 | 111 | 0.594 | 0/0 | 0/0 | 40/50 |
| 6 | 1.4359 | 0.9053 | 1.59 | 3.44e-02 | 0.822 | 0.485 | 161 | 0.444 | 0/0 | 0/0 | 50/34 |
| 7 | 1.4144 | 0.9051 | 1.56 | 2.88e-02 | 0.871 | 0.567 | 96 | 0.628 | 0/0 | 0/0 | 12/48 |
| 8 | 1.4132 | 0.9048 | 1.56 | 2.42e-02 | 0.859 | 0.341 | 11 | 0.908 | 0/0 | 0/0 | 44/23 |
| 9 | 1.4032 | 0.9044 | 1.55 | 4.35e-02 | 0.887 | 0.445 | 18 | 0.872 | 0/0 | 0/0 | 40/19 |
| 10 | 1.3682 | 0.9036 | 1.51 | 4.29e-02 | 0.674 | 0.317 | 184 | 0.438 | 0/0 | 0/0 | 40/25 |
| 11 | 1.3600 | 0.9031 | 1.51 | 5.01e-02 | 0.658 | 0.409 | 210 | 0.408 | 0/0 | 0/1 | 23/36 |
| 12 | 1.3556 | 0.9026 | 1.50 | 4.29e-02 | 0.558 | 0.292 | 200 | 0.395 | 0/0 | 0/0 | 36/40 |
| 13 | 1.3479 | 0.9022 | 1.49 | 5.11e-02 | 0.420 | 0.182 | 44 | 0.768 | 0/0 | 0/1 | 16/15 |
| 14 | 1.3422 | 0.9019 | 1.49 | 3.98e-02 | 0.479 | 0.177 | 30 | 0.804 | 0/0 | 0/0 | 7/27 |
| 15 | 1.3371 | 0.9012 | 1.48 | 5.74e-02 | 0.619 | 0.283 | 111 | 0.533 | 0/0 | 0/0 | 21/34 |
| 16 | 1.3314 | 0.9008 | 1.48 | 4.87e-02 | 0.522 | 0.250 | 211 | 0.395 | 0/0 | 0/0 | 33/30 |
| 17 | 1.3224 | 0.9002 | 1.47 | 6.24e-02 | 0.532 | 0.269 | 136 | 0.494 | 0/0 | 0/0 | 12/33 |
| 18 | 1.3128 | 0.8998 | 1.46 | 5.79e-02 | 0.495 | 0.230 | 153 | 0.427 | 0/0 | 0/0 | 24/10 |
| 19 | 1.3115 | 0.8995 | 1.46 | 6.27e-02 | 0.511 | 0.208 | 232 | 0.411 | 0/0 | 1/0 | 37/21 |
| 20 | 1.2951 | 0.8991 | 1.44 | 6.41e-02 | 0.335 | 0.197 | 76 | 0.584 | 0/0 | 0/0 | 7/16 |
| 21 | 1.2915 | 0.8988 | 1.44 | 6.40e-02 | 0.415 | 0.245 | 268 | 0.351 | 0/0 | 0/0 | 28/46 |
| 22 | 1.2898 | 0.8983 | 1.44 | 6.35e-02 | 0.428 | 0.194 | 249 | 0.358 | 0/0 | 0/0 | 31/22 |
| 23 | 1.2813 | 0.8978 | 1.43 | 7.85e-02 | 0.301 | 0.165 | 161 | 0.445 | 0/0 | 0/0 | 23/15 |
| 24 | 1.2617 | 0.8970 | 1.41 | 7.52e-02 | 0.289 | 0.148 | 259 | 0.366 | 0/0 | 0/0 | 28/22 |

## Mode poles

### Mode 1 positive

1. *Chosen (House of Night, #3)* — P.C. Cast (loading 0.07687, n=21,124)
2. *Evermore (The Immortals, #1)* — Alyson Noel (loading 0.07633, n=24,321)
3. *Marked (House of Night, #1)* — P.C. Cast (loading 0.07595, n=37,472)
4. *Betrayed (House of Night, #2)* — P.C. Cast (loading 0.07583, n=23,424)
5. *Fallen (Fallen, #1)* — Lauren Kate (loading 0.07484, n=39,502)
6. *Hunted (House of Night, #5)* — P.C. Cast (loading 0.07320, n=17,669)
7. *Untamed (House of Night, #4)* — P.C. Cast (loading 0.07116, n=21,097)
8. *Tempted (House of Night, #6)* — P.C. Cast (loading 0.07051, n=16,108)
9. *Blue Moon (The Immortals, #2)* — Alyson Noel (loading 0.06809, n=10,482)
10. *Matched (Matched, #1)* — Ally Condie (loading 0.06588, n=47,728)
11. *Crossed (Matched, #2)* — Ally Condie (loading 0.06546, n=21,446)
12. *Shadowland (The Immortals, #3)* — Alyson Noel (loading 0.06441, n=8,529)

### Mode 1 negative

1. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (loading 0.11620, n=32,297)
2. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (loading 0.10580, n=23,734)
3. *Clockwork Prince (The Infernal Devices, #2)* — Cassandra Clare (loading 0.10394, n=38,779)
4. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (loading 0.10387, n=30,591)
5. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (loading 0.10044, n=20,041)
6. *Heir of Fire (Throne of Glass, #3)* — Sarah J. Maas (loading 0.09346, n=24,457)
7. *City of Glass (The Mortal Instruments, #3)* — Cassandra Clare (loading 0.09253, n=67,752)
8. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (loading 0.09002, n=190,342)
9. *City of Heavenly Fire (The Mortal Instruments, #6)* — Cassandra Clare (loading 0.08993, n=28,473)
10. *The Last Olympian (Percy Jackson and the Olympians, #5)* — Rick Riordan (loading 0.08430, n=44,223)
11. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (loading 0.08385, n=177,929)
12. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.08341, n=183,770)

### Mode 2 positive

1. *Proven Guilty (The Dresden Files, #8)* — Jim Butcher (loading 0.16891, n=10,347)
2. *White Night (The Dresden Files, #9)* — Jim Butcher (loading 0.16610, n=10,169)
3. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (loading 0.16543, n=9,264)
4. *Dead Beat (The Dresden Files, #7)* — Jim Butcher (loading 0.16384, n=10,861)
5. *Changes (The Dresden Files, #12)* — Jim Butcher (loading 0.16262, n=9,238)
6. *Blood Rites (The Dresden Files, #6)* — Jim Butcher (loading 0.15102, n=11,186)
7. *Death Masks (The Dresden Files, #5)* — Jim Butcher (loading 0.15021, n=11,894)
8. *Small Favor (The Dresden Files, #10)* — Jim Butcher (loading 0.14702, n=9,701)
9. *Summer Knight (The Dresden Files, #4)* — Jim Butcher (loading 0.13749, n=13,026)
10. *Cold Days (The Dresden Files, #14)* — Jim Butcher (loading 0.13362, n=8,201)
11. *Skin Game (The Dresden Files, #15)* — Jim Butcher (loading 0.11989, n=6,710)
12. *Grave Peril (The Dresden Files, #3)* — Jim Butcher (loading 0.11330, n=14,398)

### Mode 2 negative

1. *Cerulean Sins (Anita Blake, Vampire Hunter, #11)* — Laurell K. Hamilton (loading 0.11392, n=7,162)
2. *Incubus Dreams (Anita Blake, Vampire Hunter, #12)* — Laurell K. Hamilton (loading 0.11344, n=6,847)
3. *Danse Macabre (Anita Blake, Vampire Hunter, #14)* — Laurell K. Hamilton (loading 0.11337, n=6,397)
4. *Micah (Anita Blake, Vampire Hunter, #13)* — Laurell K. Hamilton (loading 0.10719, n=6,328)
5. *Blood Noir (Anita Blake, Vampire Hunter #16)* — Laurell K. Hamilton (loading 0.09897, n=5,520)
6. *Narcissus in Chains (Anita Blake, Vampire Hunter, #10)* — Laurell K. Hamilton (loading 0.09792, n=7,909)
7. *The Harlequin (Anita Blake, Vampire Hunter #15)* — Laurell K. Hamilton (loading 0.09311, n=6,131)
8. *Skin Trade (Anita Blake, Vampire Hunter #17)* — Laurell K. Hamilton (loading 0.08459, n=5,095)
9. *Flirt (Anita Blake, Vampire Hunter #18)* — Laurell K. Hamilton (loading 0.07658, n=4,648)
10. *Burnt Offerings (Anita Blake, Vampire Hunter, #7)* — Laurell K. Hamilton (loading 0.07381, n=8,954)
11. *Bullet (Anita Blake, Vampire Hunter #19)* — Laurell K. Hamilton (loading 0.07298, n=4,403)
12. *Blue Moon (Anita Blake, Vampire Hunter, #8)* — Laurell K. Hamilton (loading 0.06972, n=8,575)

### Mode 3 positive

1. *Portrait in Death (In Death, #16)* — J.D. Robb (loading 0.13476, n=3,196)
2. *Vengeance in Death (In Death, #6)* — J.D. Robb (loading 0.13144, n=3,896)
3. *Loyalty in Death (In Death, #9)* — J.D. Robb (loading 0.11585, n=3,184)
4. *Betrayal in Death (In Death, #12)* — J.D. Robb (loading 0.11466, n=3,000)
5. *Witness in Death (In Death, #10)* — J.D. Robb (loading 0.11337, n=3,173)
6. *Holiday in Death (In Death, #7)* — J.D. Robb (loading 0.11199, n=3,625)
7. *Imitation in Death (In Death, #17)* — J.D. Robb (loading 0.11012, n=2,679)
8. *Conspiracy in Death (In Death, #8)* — J.D. Robb (loading 0.10988, n=3,500)
9. *Reunion in Death (In Death, #14)* — J.D. Robb (loading 0.10968, n=2,740)
10. *Rapture in Death (In Death, #4)* — J.D. Robb (loading 0.10954, n=4,335)
11. *Judgment in Death (In Death, #11)* — J.D. Robb (loading 0.10825, n=3,194)
12. *Divided in Death (In Death, #18)* — J.D. Robb (loading 0.10703, n=2,704)

### Mode 3 negative

1. *Danse Macabre (Anita Blake, Vampire Hunter, #14)* — Laurell K. Hamilton (loading 0.11222, n=6,397)
2. *Micah (Anita Blake, Vampire Hunter, #13)* — Laurell K. Hamilton (loading 0.10993, n=6,328)
3. *Incubus Dreams (Anita Blake, Vampire Hunter, #12)* — Laurell K. Hamilton (loading 0.10779, n=6,847)
4. *Cerulean Sins (Anita Blake, Vampire Hunter, #11)* — Laurell K. Hamilton (loading 0.10258, n=7,162)
5. *Blood Noir (Anita Blake, Vampire Hunter #16)* — Laurell K. Hamilton (loading 0.09823, n=5,520)
6. *The Harlequin (Anita Blake, Vampire Hunter #15)* — Laurell K. Hamilton (loading 0.09049, n=6,131)
7. *Skin Trade (Anita Blake, Vampire Hunter #17)* — Laurell K. Hamilton (loading 0.08873, n=5,095)
8. *Narcissus in Chains (Anita Blake, Vampire Hunter, #10)* — Laurell K. Hamilton (loading 0.08745, n=7,909)
9. *Flirt (Anita Blake, Vampire Hunter #18)* — Laurell K. Hamilton (loading 0.08323, n=4,648)
10. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (loading 0.08267, n=192,417)
11. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.08132, n=183,770)
12. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (loading 0.07871, n=174,713)

### Mode 4 positive

1. *To the Nines (Stephanie Plum, #9)* — Janet Evanovich (loading 0.22033, n=9,421)
2. *Hard Eight (Stephanie Plum, #8)* — Janet Evanovich (loading 0.21984, n=9,777)
3. *Seven Up (Stephanie Plum, #7)* — Janet Evanovich (loading 0.21975, n=10,095)
4. *Hot Six (Stephanie Plum, #6)* — Janet Evanovich (loading 0.21869, n=10,512)
5. *Eleven on Top (Stephanie Plum, #11)* — Janet Evanovich (loading 0.21569, n=8,954)
6. *High Five (Stephanie Plum, #5)* — Janet Evanovich (loading 0.21107, n=10,420)
7. *Three to Get Deadly (Stephanie Plum, #3)* — Janet Evanovich (loading 0.21078, n=12,221)
8. *Ten Big Ones (Stephanie Plum, #10)* — Janet Evanovich (loading 0.20695, n=8,651)
9. *Twelve Sharp (Stephanie Plum, #12)* — Janet Evanovich (loading 0.20436, n=8,383)
10. *Four to Score (Stephanie Plum, #4)* — Janet Evanovich (loading 0.20361, n=11,390)
11. *Lean Mean Thirteen (Stephanie Plum, #13)* — Janet Evanovich (loading 0.20206, n=8,332)
12. *Two for the Dough (Stephanie Plum, #2)* — Janet Evanovich (loading 0.18171, n=13,494)

### Mode 4 negative

1. *Sorceress of Darshiva (The Malloreon, #4)* — David Eddings (loading 0.04436, n=3,851)
2. *Guardians of the West (The Malloreon, #1)* — David Eddings (loading 0.04182, n=4,462)
3. *King of the Murgos (The Malloreon, #2)* — David Eddings (loading 0.04155, n=4,328)
4. *The Seeress of Kell (The Malloreon, #5)* — David Eddings (loading 0.04037, n=3,770)
5. *Demon Lord of Karanda (The Malloreon, #3)* — David Eddings (loading 0.03858, n=3,676)
6. *Magician's Gambit (The Belgariad, #3)* — David Eddings (loading 0.03663, n=7,347)
7. *Pawn of Prophecy (The Belgariad, #1)* — David Eddings (loading 0.03632, n=7,877)
8. *Castle of Wizardry (The Belgariad, #4)* — David Eddings (loading 0.03560, n=6,254)
9. *Enchanters' End Game (The Belgariad, #5)* — David Eddings (loading 0.03505, n=7,092)
10. *Queen of Sorcery (The Belgariad, #2)* — David Eddings (loading 0.03364, n=6,166)
11. *The Help* — Kathryn Stockett (loading 0.03225, n=98,134)
12. *Fool Moon (The Dresden Files, #2)* — Jim Butcher (loading 0.03059, n=16,766)

### Mode 5 positive

1. *High Five (Stephanie Plum, #5)* — Janet Evanovich (loading 0.06659, n=10,420)
2. *Eclipse (Twilight, #3)* — Stephenie Meyer (loading 0.06562, n=116,643)
3. *Hot Six (Stephanie Plum, #6)* — Janet Evanovich (loading 0.06560, n=10,512)
4. *Breaking Dawn (Twilight, #4)* — Stephenie Meyer (loading 0.06534, n=112,600)
5. *Lean Mean Thirteen (Stephanie Plum, #13)* — Janet Evanovich (loading 0.06514, n=8,332)
6. *Hard Eight (Stephanie Plum, #8)* — Janet Evanovich (loading 0.06505, n=9,777)
7. *Ten Big Ones (Stephanie Plum, #10)* — Janet Evanovich (loading 0.06399, n=8,651)
8. *Seven Up (Stephanie Plum, #7)* — Janet Evanovich (loading 0.06215, n=10,095)
9. *Three to Get Deadly (Stephanie Plum, #3)* — Janet Evanovich (loading 0.06196, n=12,221)
10. *To the Nines (Stephanie Plum, #9)* — Janet Evanovich (loading 0.06153, n=9,421)
11. *Twelve Sharp (Stephanie Plum, #12)* — Janet Evanovich (loading 0.06085, n=8,383)
12. *Eleven on Top (Stephanie Plum, #11)* — Janet Evanovich (loading 0.06002, n=8,954)

### Mode 5 negative

1. *Portrait in Death (In Death, #16)* — J.D. Robb (loading 0.15983, n=3,196)
2. *Vengeance in Death (In Death, #6)* — J.D. Robb (loading 0.14882, n=3,896)
3. *Loyalty in Death (In Death, #9)* — J.D. Robb (loading 0.13666, n=3,184)
4. *Betrayal in Death (In Death, #12)* — J.D. Robb (loading 0.13642, n=3,000)
5. *Holiday in Death (In Death, #7)* — J.D. Robb (loading 0.13350, n=3,625)
6. *Divided in Death (In Death, #18)* — J.D. Robb (loading 0.13182, n=2,704)
7. *Imitation in Death (In Death, #17)* — J.D. Robb (loading 0.13151, n=2,679)
8. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.13148, n=183,770)
9. *Judgment in Death (In Death, #11)* — J.D. Robb (loading 0.13060, n=3,194)
10. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (loading 0.12957, n=192,417)
11. *Witness in Death (In Death, #10)* — J.D. Robb (loading 0.12895, n=3,173)
12. *Conspiracy in Death (In Death, #8)* — J.D. Robb (loading 0.12850, n=3,500)

### Mode 6 positive

1. *Hard Eight (Stephanie Plum, #8)* — Janet Evanovich (loading 0.14359, n=9,777)
2. *Hot Six (Stephanie Plum, #6)* — Janet Evanovich (loading 0.14309, n=10,512)
3. *High Five (Stephanie Plum, #5)* — Janet Evanovich (loading 0.13984, n=10,420)
4. *Seven Up (Stephanie Plum, #7)* — Janet Evanovich (loading 0.13974, n=10,095)
5. *Three to Get Deadly (Stephanie Plum, #3)* — Janet Evanovich (loading 0.13556, n=12,221)
6. *To the Nines (Stephanie Plum, #9)* — Janet Evanovich (loading 0.13466, n=9,421)
7. *Four to Score (Stephanie Plum, #4)* — Janet Evanovich (loading 0.13458, n=11,390)
8. *Eleven on Top (Stephanie Plum, #11)* — Janet Evanovich (loading 0.13297, n=8,954)
9. *Ten Big Ones (Stephanie Plum, #10)* — Janet Evanovich (loading 0.12942, n=8,651)
10. *Lean Mean Thirteen (Stephanie Plum, #13)* — Janet Evanovich (loading 0.12517, n=8,332)
11. *Twelve Sharp (Stephanie Plum, #12)* — Janet Evanovich (loading 0.12151, n=8,383)
12. *Two for the Dough (Stephanie Plum, #2)* — Janet Evanovich (loading 0.11217, n=13,494)

### Mode 6 negative

1. *Danse Macabre (Anita Blake, Vampire Hunter, #14)* — Laurell K. Hamilton (loading 0.10235, n=6,397)
2. *Incubus Dreams (Anita Blake, Vampire Hunter, #12)* — Laurell K. Hamilton (loading 0.10044, n=6,847)
3. *Cerulean Sins (Anita Blake, Vampire Hunter, #11)* — Laurell K. Hamilton (loading 0.09845, n=7,162)
4. *Micah (Anita Blake, Vampire Hunter, #13)* — Laurell K. Hamilton (loading 0.08495, n=6,328)
5. *Narcissus in Chains (Anita Blake, Vampire Hunter, #10)* — Laurell K. Hamilton (loading 0.08458, n=7,909)
6. *Blood Noir (Anita Blake, Vampire Hunter #16)* — Laurell K. Hamilton (loading 0.08448, n=5,520)
7. *The Harlequin (Anita Blake, Vampire Hunter #15)* — Laurell K. Hamilton (loading 0.08190, n=6,131)
8. *Skin Trade (Anita Blake, Vampire Hunter #17)* — Laurell K. Hamilton (loading 0.07584, n=5,095)
9. *The Killing Dance (Anita Blake, Vampire Hunter, #6)* — Laurell K. Hamilton (loading 0.07543, n=9,342)
10. *Burnt Offerings (Anita Blake, Vampire Hunter, #7)* — Laurell K. Hamilton (loading 0.06826, n=8,954)
11. *Bloody Bones (Anita Blake, Vampire Hunter #5)* — Laurell K. Hamilton (loading 0.06647, n=9,708)
12. *Blue Moon (Anita Blake, Vampire Hunter, #8)* — Laurell K. Hamilton (loading 0.06643, n=8,575)

### Mode 7 positive

1. *Season of Mists (The Sandman #4)* — Neil Gaiman (loading 0.11267, n=6,862)
2. *Brief Lives (The Sandman #7)* — Neil Gaiman (loading 0.11102, n=5,161)
3. *The Doll's House (The Sandman #2)* — Neil Gaiman (loading 0.10595, n=8,833)
4. *Worlds' End (The Sandman #8)* — Neil Gaiman (loading 0.10516, n=4,738)
5. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (loading 0.10317, n=4,713)
6. *Fables and Reflections (The Sandman #6)* — Neil Gaiman (loading 0.10107, n=5,294)
7. *A Game of You (The Sandman #5)* — Neil Gaiman (loading 0.10038, n=5,769)
8. *The Wake (The Sandman #10)* — Neil Gaiman (loading 0.09987, n=4,401)
9. *Dream Country (The Sandman #3)* — Neil Gaiman (loading 0.09423, n=8,018)
10. *Preludes & Nocturnes (The Sandman #1)* — Neil Gaiman (loading 0.08630, n=15,084)
11. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (loading 0.06138, n=192,417)
12. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.05638, n=183,770)

### Mode 7 negative

1. *Proven Guilty (The Dresden Files, #8)* — Jim Butcher (loading 0.16963, n=10,347)
2. *White Night (The Dresden Files, #9)* — Jim Butcher (loading 0.16421, n=10,169)
3. *Dead Beat (The Dresden Files, #7)* — Jim Butcher (loading 0.16117, n=10,861)
4. *Blood Rites (The Dresden Files, #6)* — Jim Butcher (loading 0.15924, n=11,186)
5. *Death Masks (The Dresden Files, #5)* — Jim Butcher (loading 0.15739, n=11,894)
6. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (loading 0.15514, n=9,264)
7. *Small Favor (The Dresden Files, #10)* — Jim Butcher (loading 0.14646, n=9,701)
8. *Summer Knight (The Dresden Files, #4)* — Jim Butcher (loading 0.14359, n=13,026)
9. *Grave Peril (The Dresden Files, #3)* — Jim Butcher (loading 0.14277, n=14,398)
10. *Danse Macabre (Anita Blake, Vampire Hunter, #14)* — Laurell K. Hamilton (loading 0.13251, n=6,397)
11. *Changes (The Dresden Files, #12)* — Jim Butcher (loading 0.13159, n=9,238)
12. *Incubus Dreams (Anita Blake, Vampire Hunter, #12)* — Laurell K. Hamilton (loading 0.12835, n=6,847)

### Mode 8 positive

1. *Death Masks (The Dresden Files, #5)* — Jim Butcher (loading 0.04068, n=11,894)
2. *A Voice in the Wind (Mark of the Lion, #1)* — Francine Rivers (loading 0.04025, n=3,425)
3. *Proven Guilty (The Dresden Files, #8)* — Jim Butcher (loading 0.03944, n=10,347)
4. *Blood Rites (The Dresden Files, #6)* — Jim Butcher (loading 0.03840, n=11,186)
5. *White Night (The Dresden Files, #9)* — Jim Butcher (loading 0.03720, n=10,169)
6. *Grave Peril (The Dresden Files, #3)* — Jim Butcher (loading 0.03650, n=14,398)
7. *Summer Knight (The Dresden Files, #4)* — Jim Butcher (loading 0.03605, n=13,026)
8. *Dead Beat (The Dresden Files, #7)* — Jim Butcher (loading 0.03593, n=10,861)
9. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (loading 0.03569, n=9,264)
10. *Small Favor (The Dresden Files, #10)* — Jim Butcher (loading 0.03458, n=9,701)
11. *90 Minutes in Heaven: A True Story of Death and Life* — Don Piper (loading 0.03127, n=3,148)
12. *Redeeming Love* — Francine Rivers (loading 0.03054, n=9,292)

### Mode 8 negative

1. *Apollyon (Left Behind, #5)* — Tim LaHaye (loading 0.34325, n=2,496)
2. *The Mark (Left Behind, #8)* — Tim LaHaye (loading 0.34229, n=2,227)
3. *Soul Harvest: The World Takes Sides (Left Behind, #4)* — Tim LaHaye (loading 0.33610, n=2,725)
4. *Assassins (Left Behind, #6)* — Tim LaHaye (loading 0.33042, n=2,371)
5. *Desecration (Left Behind, #9)* — Tim LaHaye (loading 0.32353, n=2,019)
6. *Nicolae (Left Behind, #3)* — Tim LaHaye (loading 0.31889, n=3,066)
7. *The Indwelling (Left Behind, #7)* — Tim LaHaye (loading 0.31734, n=2,279)
8. *Tribulation Force (Left Behind, #2)* — Tim LaHaye (loading 0.29218, n=3,360)
9. *Left Behind (Left Behind, #1)* — Tim LaHaye (loading 0.13327, n=10,047)
10. *Worlds' End (The Sandman #8)* — Neil Gaiman (loading 0.03709, n=4,738)
11. *Season of Mists (The Sandman #4)* — Neil Gaiman (loading 0.03638, n=6,862)
12. *The Doll's House (The Sandman #2)* — Neil Gaiman (loading 0.03582, n=8,833)

### Mode 9 positive

1. *Dead as a Doornail (Sookie Stackhouse, #5)* — Charlaine Harris (loading 0.04874, n=24,809)
2. *Club Dead (Sookie Stackhouse, #3)* — Charlaine Harris (loading 0.04753, n=27,777)
3. *Definitely Dead (Sookie Stackhouse, #6)* — Charlaine Harris (loading 0.04667, n=24,065)
4. *From Dead to Worse (Sookie Stackhouse, #8)* — Charlaine Harris (loading 0.04617, n=22,347)
5. *Breaking Dawn (Twilight, #4)* — Stephenie Meyer (loading 0.04561, n=112,600)
6. *All Together Dead (Sookie Stackhouse, #7)* — Charlaine Harris (loading 0.04525, n=23,374)
7. *Dead and Gone (Sookie Stackhouse, #9)* — Charlaine Harris (loading 0.04315, n=21,666)
8. *Living Dead in Dallas (Sookie Stackhouse, #2)* — Charlaine Harris (loading 0.04295, n=29,643)
9. *Eclipse (Twilight, #3)* — Stephenie Meyer (loading 0.04286, n=116,643)
10. *New Moon (Twilight, #2)* — Stephenie Meyer (loading 0.04217, n=120,318)
11. *Dead to the World (Sookie Stackhouse, #4)* — Charlaine Harris (loading 0.04161, n=27,397)
12. *Twilight (Twilight, #1)* — Stephenie Meyer (loading 0.04141, n=235,067)

### Mode 9 negative

1. *The Vile Village (A Series of Unfortunate Events, #7)* — Lemony Snicket (loading 0.28032, n=10,924)
2. *The Carnivorous Carnival (A Series of Unfortunate Events, #9)* — Lemony Snicket (loading 0.27763, n=9,975)
3. *The Austere Academy (A Series of Unfortunate Events, #5)* — Lemony Snicket (loading 0.27450, n=12,358)
4. *The Miserable Mill (A Series of Unfortunate Events, #4)* — Lemony Snicket (loading 0.27440, n=13,482)
5. *The Slippery Slope (A Series of Unfortunate Events, #10)* — Lemony Snicket (loading 0.27351, n=9,516)
6. *The Hostile Hospital (A Series of Unfortunate Events, #8)* — Lemony Snicket (loading 0.27028, n=9,099)
7. *The Ersatz Elevator (A Series of Unfortunate Events, #6)* — Lemony Snicket (loading 0.26968, n=11,509)
8. *The Wide Window (A Series of Unfortunate Events, #3)* — Lemony Snicket (loading 0.25725, n=15,323)
9. *The Grim Grotto (A Series of Unfortunate Events, #11)* — Lemony Snicket (loading 0.25318, n=8,823)
10. *The Penultimate Peril (A Series of Unfortunate Events, #12)* — Lemony Snicket (loading 0.23293, n=8,337)
11. *The Reptile Room (A Series of Unfortunate Events, #2)* — Lemony Snicket (loading 0.22806, n=17,604)
12. *The End (A Series of Unfortunate Events, #13)* — Lemony Snicket (loading 0.18507, n=8,334)

### Mode 10 positive

1. *Sorceress of Darshiva (The Malloreon, #4)* — David Eddings (loading 0.14196, n=3,851)
2. *Guardians of the West (The Malloreon, #1)* — David Eddings (loading 0.13332, n=4,462)
3. *The Seeress of Kell (The Malloreon, #5)* — David Eddings (loading 0.12993, n=3,770)
4. *King of the Murgos (The Malloreon, #2)* — David Eddings (loading 0.12815, n=4,328)
5. *Demon Lord of Karanda (The Malloreon, #3)* — David Eddings (loading 0.12559, n=3,676)
6. *Brief Lives (The Sandman #7)* — Neil Gaiman (loading 0.11990, n=5,161)
7. *Castle of Wizardry (The Belgariad, #4)* — David Eddings (loading 0.11889, n=6,254)
8. *Season of Mists (The Sandman #4)* — Neil Gaiman (loading 0.11874, n=6,862)
9. *Enchanters' End Game (The Belgariad, #5)* — David Eddings (loading 0.11593, n=7,092)
10. *Worlds' End (The Sandman #8)* — Neil Gaiman (loading 0.11516, n=4,738)
11. *Fables and Reflections (The Sandman #6)* — Neil Gaiman (loading 0.11499, n=5,294)
12. *Pawn of Prophecy (The Belgariad, #1)* — David Eddings (loading 0.11420, n=7,877)

### Mode 10 negative

1. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (loading 0.05502, n=19,224)
2. *Deadhouse Gates (The Malazan Book of the Fallen, #2)* — Steven Erikson (loading 0.05262, n=4,221)
3. *The Bonehunters (Malazan Book of the Fallen, #6)* — Steven Erikson (loading 0.05253, n=2,414)
4. *Memories of Ice (The Malazan Book of the Fallen, #3)* — Steven Erikson (loading 0.05215, n=3,527)
5. *Lover Eternal (Black Dagger Brotherhood, #2)* — J.R. Ward (loading 0.05082, n=19,584)
6. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (loading 0.04941, n=64,658)
7. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (loading 0.04890, n=114,688)
8. *Fool's Errand (Tawny Man, #1)* — Robin Hobb (loading 0.04697, n=6,192)
9. *House of Chains (The Malazan Book of the Fallen, #4)* — Steven Erikson (loading 0.04611, n=2,966)
10. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (loading 0.04571, n=53,880)
11. *The Gathering Storm (Wheel of Time, #12)* — Robert Jordan (loading 0.04563, n=8,913)
12. *Fool's Fate (Tawny Man, #3)* — Robin Hobb (loading 0.04558, n=5,403)

### Mode 11 positive

1. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.13235, n=3,689)
2. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.12791, n=3,307)
3. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (loading 0.12649, n=4,220)
4. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.12484, n=2,812)
5. *The Walking Dead, Vol. 02: Miles Behind Us* — Robert Kirkman (loading 0.11976, n=4,875)
6. *The Walking Dead, Vol. 06: This Sorrowful Life* — Robert Kirkman (loading 0.11823, n=3,073)
7. *The Walking Dead, Vol. 10: What We Become* — Robert Kirkman (loading 0.11458, n=2,489)
8. *The Walking Dead, Vol. 09: Here We Remain* — Robert Kirkman (loading 0.10509, n=2,570)
9. *The Walking Dead, Vol. 11: Fear the Hunters* — Robert Kirkman (loading 0.10441, n=2,374)
10. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (loading 0.10357, n=3,061)
11. *The Walking Dead, Vol. 12: Life Among Them* — Robert Kirkman (loading 0.10101, n=2,432)
12. *Sorceress of Darshiva (The Malloreon, #4)* — David Eddings (loading 0.09601, n=3,851)

### Mode 11 negative

1. *ثلاثية غرناطة* — Radwa Ashour (loading 0.12728, n=6,061)
2. *الطنطورية* — Radwa Ashour (loading 0.11696, n=3,142)
3. *ساق البامبو* — s`wd lsn`wsy (loading 0.09011, n=7,228)
4. *Hunted (House of Night, #5)* — P.C. Cast (loading 0.08383, n=17,669)
5. *Tempted (House of Night, #6)* — P.C. Cast (loading 0.08128, n=16,108)
6. *Chosen (House of Night, #3)* — P.C. Cast (loading 0.08110, n=21,124)
7. *رباعيات صلاح جاهين* — SlH jhyn (loading 0.07981, n=2,045)
8. *Untamed (House of Night, #4)* — P.C. Cast (loading 0.07931, n=21,097)
9. *Betrayed (House of Night, #2)* — P.C. Cast (loading 0.07791, n=23,424)
10. *الحرافيش* — Naguib Mahfouz (loading 0.07666, n=2,008)
11. *Burned (House of Night, #7)* — P.C. Cast (loading 0.07123, n=14,324)
12. *عزازيل* — ywsf zydn (loading 0.07102, n=7,420)

### Mode 12 positive

1. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.14056, n=3,689)
2. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.13751, n=3,307)
3. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.13212, n=2,812)
4. *The Walking Dead, Vol. 02: Miles Behind Us* — Robert Kirkman (loading 0.12964, n=4,875)
5. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (loading 0.12817, n=4,220)
6. *The Walking Dead, Vol. 06: This Sorrowful Life* — Robert Kirkman (loading 0.12698, n=3,073)
7. *The Walking Dead, Vol. 10: What We Become* — Robert Kirkman (loading 0.11936, n=2,489)
8. *The Walking Dead, Vol. 09: Here We Remain* — Robert Kirkman (loading 0.11320, n=2,570)
9. *The Walking Dead, Vol. 11: Fear the Hunters* — Robert Kirkman (loading 0.10756, n=2,374)
10. *The Walking Dead, Vol. 12: Life Among Them* — Robert Kirkman (loading 0.10637, n=2,432)
11. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (loading 0.10277, n=3,061)
12. *The Walking Dead, Vol. 13: Too Far Gone* — Robert Kirkman (loading 0.09206, n=2,093)

### Mode 12 negative

1. *Sorceress of Darshiva (The Malloreon, #4)* — David Eddings (loading 0.08152, n=3,851)
2. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (loading 0.07737, n=192,417)
3. *King of the Murgos (The Malloreon, #2)* — David Eddings (loading 0.07606, n=4,328)
4. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (loading 0.07505, n=174,713)
5. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.07496, n=183,770)
6. *Pawn of Prophecy (The Belgariad, #1)* — David Eddings (loading 0.07496, n=7,877)
7. *Castle of Wizardry (The Belgariad, #4)* — David Eddings (loading 0.07477, n=6,254)
8. *Enchanters' End Game (The Belgariad, #5)* — David Eddings (loading 0.07459, n=7,092)
9. *The Seeress of Kell (The Malloreon, #5)* — David Eddings (loading 0.07402, n=3,770)
10. *Guardians of the West (The Malloreon, #1)* — David Eddings (loading 0.07358, n=4,462)
11. *Demon Lord of Karanda (The Malloreon, #3)* — David Eddings (loading 0.07304, n=3,676)
12. *Burnt Offerings (Anita Blake, Vampire Hunter, #7)* — Laurell K. Hamilton (loading 0.07207, n=8,954)

### Mode 13 positive

1. *Dead as a Doornail (Sookie Stackhouse, #5)* — Charlaine Harris (loading 0.22768, n=24,809)
2. *All Together Dead (Sookie Stackhouse, #7)* — Charlaine Harris (loading 0.22032, n=23,374)
3. *Definitely Dead (Sookie Stackhouse, #6)* — Charlaine Harris (loading 0.22026, n=24,065)
4. *From Dead to Worse (Sookie Stackhouse, #8)* — Charlaine Harris (loading 0.21888, n=22,347)
5. *Club Dead (Sookie Stackhouse, #3)* — Charlaine Harris (loading 0.21070, n=27,777)
6. *Dead and Gone (Sookie Stackhouse, #9)* — Charlaine Harris (loading 0.19773, n=21,666)
7. *Dead to the World (Sookie Stackhouse, #4)* — Charlaine Harris (loading 0.19257, n=27,397)
8. *Living Dead in Dallas (Sookie Stackhouse, #2)* — Charlaine Harris (loading 0.19129, n=29,643)
9. *Perfect (Pretty Little Liars, #3)* — Sara Shepard (loading 0.16144, n=6,650)
10. *Wicked (Pretty Little Liars, #5)* — Sara Shepard (loading 0.15758, n=4,919)
11. *Heartless (Pretty Little Liars, #7)* — Sara Shepard (loading 0.15584, n=4,090)
12. *Killer (Pretty Little Liars, #6)* — Sara Shepard (loading 0.15380, n=4,702)

### Mode 13 negative

1. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.11608, n=3,689)
2. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.11577, n=3,307)
3. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.10770, n=2,812)
4. *The Walking Dead, Vol. 02: Miles Behind Us* — Robert Kirkman (loading 0.10538, n=4,875)
5. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (loading 0.10426, n=4,220)
6. *The Walking Dead, Vol. 06: This Sorrowful Life* — Robert Kirkman (loading 0.10348, n=3,073)
7. *The Walking Dead, Vol. 10: What We Become* — Robert Kirkman (loading 0.09733, n=2,489)
8. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (loading 0.09137, n=3,061)
9. *The Walking Dead, Vol. 09: Here We Remain* — Robert Kirkman (loading 0.09039, n=2,570)
10. *The Walking Dead, Vol. 11: Fear the Hunters* — Robert Kirkman (loading 0.09036, n=2,374)
11. *The Walking Dead, Vol. 12: Life Among Them* — Robert Kirkman (loading 0.08886, n=2,432)
12. *The Walking Dead, Vol. 13: Too Far Gone* — Robert Kirkman (loading 0.07132, n=2,093)

### Mode 14 positive

1. *Wicked (Pretty Little Liars, #5)* — Sara Shepard (loading 0.26249, n=4,919)
2. *Perfect (Pretty Little Liars, #3)* — Sara Shepard (loading 0.26163, n=6,650)
3. *Heartless (Pretty Little Liars, #7)* — Sara Shepard (loading 0.25331, n=4,090)
4. *Killer (Pretty Little Liars, #6)* — Sara Shepard (loading 0.25227, n=4,702)
5. *Flawless (Pretty Little Liars, #2)* — Sara Shepard (loading 0.24814, n=7,941)
6. *Unbelievable (Pretty Little Liars, #4)* — Sara Shepard (loading 0.24302, n=5,914)
7. *Wanted (Pretty Little Liars, #8)* — Sara Shepard (loading 0.22645, n=4,163)
8. *Twisted (Pretty Little Liars, #9)* — Sara Shepard (loading 0.16959, n=2,936)
9. *Pretty Little Liars (Pretty Little Liars, #1)* — Sara Shepard (loading 0.15901, n=15,861)
10. *Ruthless (Pretty Little Liars, #10)* — Sara Shepard (loading 0.14646, n=2,291)
11. *Brief Lives (The Sandman #7)* — Neil Gaiman (loading 0.06554, n=5,161)
12. *Winter's Heart (Wheel of Time, #9)* — Robert Jordan (loading 0.06313, n=8,189)

### Mode 14 negative

1. *All Together Dead (Sookie Stackhouse, #7)* — Charlaine Harris (loading 0.15417, n=23,374)
2. *Dead as a Doornail (Sookie Stackhouse, #5)* — Charlaine Harris (loading 0.15313, n=24,809)
3. *Definitely Dead (Sookie Stackhouse, #6)* — Charlaine Harris (loading 0.15245, n=24,065)
4. *From Dead to Worse (Sookie Stackhouse, #8)* — Charlaine Harris (loading 0.15195, n=22,347)
5. *Club Dead (Sookie Stackhouse, #3)* — Charlaine Harris (loading 0.14612, n=27,777)
6. *Dead and Gone (Sookie Stackhouse, #9)* — Charlaine Harris (loading 0.13595, n=21,666)
7. *Dead to the World (Sookie Stackhouse, #4)* — Charlaine Harris (loading 0.13388, n=27,397)
8. *Living Dead in Dallas (Sookie Stackhouse, #2)* — Charlaine Harris (loading 0.13311, n=29,643)
9. *Dead in the Family (Sookie Stackhouse, #10)* — Charlaine Harris (loading 0.10528, n=19,346)
10. *Dead Until Dark (Sookie Stackhouse, #1)* — Charlaine Harris (loading 0.09407, n=48,925)
11. *Dead Reckoning (Sookie Stackhouse, #11)* — Charlaine Harris (loading 0.06658, n=15,337)
12. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.06384, n=2,104)

### Mode 15 positive

1. *الفيل الأزرق* — 'Hmd mrd (loading 0.09632, n=7,149)
2. *The 3 Mistakes of My Life* — Chetan Bhagat (loading 0.09560, n=5,706)
3. *28 حرف* — 'Hmd Hlmy (loading 0.09117, n=2,862)
4. *One Night at the Call Center* — Chetan Bhagat (loading 0.08995, n=4,995)
5. *ظل الأفعى* — ywsf zydn (loading 0.08887, n=2,383)
6. *محال* — ywsf zydn (loading 0.08885, n=2,062)
7. *Revolution 2020: Love, Corruption, Ambition* — Chetan Bhagat (loading 0.08445, n=4,283)
8. *2 States: The Story of My Marriage* — Chetan Bhagat (loading 0.08292, n=7,006)
9. *الأسود يليق بك* — 'Hlm mstGnmy (loading 0.08251, n=7,204)
10. *في ديسمبر تنتهي كل الأحلام* — 'thyr `bdllh lnshmy (loading 0.08222, n=2,807)
11. *أحببتك أكثر مما ينبغي* — 'thyr `bdllh lnshmy (loading 0.08084, n=5,546)
12. *شيكاجو* — Alaa Al Aswany (loading 0.07972, n=3,195)

### Mode 15 negative

1. *A Crown of Swords (Wheel of Time, #7)* — Robert Jordan (loading 0.17906, n=9,473)
2. *Lord of Chaos (Wheel of Time, #6)* — Robert Jordan (loading 0.17393, n=10,180)
3. *The Fires of Heaven (Wheel of Time, #5)* — Robert Jordan (loading 0.16327, n=10,695)
4. *The Path of Daggers (Wheel of Time, #8)* — Robert Jordan (loading 0.15731, n=8,700)
5. *Winter's Heart (Wheel of Time, #9)* — Robert Jordan (loading 0.15272, n=8,189)
6. *The Shadow Rising (Wheel of Time, #4)* — Robert Jordan (loading 0.15247, n=12,786)
7. *ثلاثية غرناطة* — Radwa Ashour (loading 0.15064, n=6,061)
8. *Knife of Dreams (Wheel of Time, #11)* — Robert Jordan (loading 0.14412, n=7,460)
9. *The Dragon Reborn (Wheel of Time, #3)* — Robert Jordan (loading 0.13951, n=15,289)
10. *الطنطورية* — Radwa Ashour (loading 0.13798, n=3,142)
11. *The Great Hunt (Wheel of Time, #2)* — Robert Jordan (loading 0.13437, n=16,452)
12. *The Gathering Storm (Wheel of Time, #12)* — Robert Jordan (loading 0.12739, n=8,913)

### Mode 16 positive

1. *Sorceress of Darshiva (The Malloreon, #4)* — David Eddings (loading 0.13221, n=3,851)
2. *The Seeress of Kell (The Malloreon, #5)* — David Eddings (loading 0.12792, n=3,770)
3. *Guardians of the West (The Malloreon, #1)* — David Eddings (loading 0.12479, n=4,462)
4. *King of the Murgos (The Malloreon, #2)* — David Eddings (loading 0.12137, n=4,328)
5. *Demon Lord of Karanda (The Malloreon, #3)* — David Eddings (loading 0.11937, n=3,676)
6. *Enchanters' End Game (The Belgariad, #5)* — David Eddings (loading 0.11695, n=7,092)
7. *Castle of Wizardry (The Belgariad, #4)* — David Eddings (loading 0.11679, n=6,254)
8. *Pawn of Prophecy (The Belgariad, #1)* — David Eddings (loading 0.11111, n=7,877)
9. *Magician's Gambit (The Belgariad, #3)* — David Eddings (loading 0.10782, n=7,347)
10. *Queen of Sorcery (The Belgariad, #2)* — David Eddings (loading 0.10642, n=6,166)
11. *The Shining Ones (The Tamuli, #2)* — David Eddings (loading 0.07957, n=2,087)
12. *Wicked (Pretty Little Liars, #5)* — Sara Shepard (loading 0.07695, n=4,919)

### Mode 16 negative

1. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (loading 0.10570, n=8,363)
2. *Magic Rises (Kate Daniels, #6)* — Ilona Andrews (loading 0.09823, n=5,526)
3. *Magic Burns (Kate Daniels, #2)* — Ilona Andrews (loading 0.09296, n=8,813)
4. *Magic Breaks (Kate Daniels, #7)* — Ilona Andrews (loading 0.09231, n=4,480)
5. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (loading 0.09040, n=8,631)
6. *Magic Slays (Kate Daniels, #5)* — Ilona Andrews (loading 0.09015, n=7,527)
7. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.08810, n=3,689)
8. *Iron Kissed (Mercy Thompson, #3)* — Patricia Briggs (loading 0.08733, n=13,137)
9. *Bone Crossed (Mercy Thompson, #4)* — Patricia Briggs (loading 0.08560, n=11,855)
10. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.08189, n=3,307)
11. *Burnt Offerings (Anita Blake, Vampire Hunter, #7)* — Laurell K. Hamilton (loading 0.08163, n=8,954)
12. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.08117, n=2,812)

### Mode 17 positive

1. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.12398, n=3,689)
2. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.12335, n=3,307)
3. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.11460, n=2,812)
4. *The Walking Dead, Vol. 06: This Sorrowful Life* — Robert Kirkman (loading 0.11410, n=3,073)
5. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (loading 0.11298, n=4,220)
6. *The Walking Dead, Vol. 02: Miles Behind Us* — Robert Kirkman (loading 0.10892, n=4,875)
7. *The Walking Dead, Vol. 10: What We Become* — Robert Kirkman (loading 0.10354, n=2,489)
8. *The Walking Dead, Vol. 09: Here We Remain* — Robert Kirkman (loading 0.09858, n=2,570)
9. *The Walking Dead, Vol. 11: Fear the Hunters* — Robert Kirkman (loading 0.09340, n=2,374)
10. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (loading 0.09252, n=3,061)
11. *The Walking Dead, Vol. 12: Life Among Them* — Robert Kirkman (loading 0.09046, n=2,432)
12. *The Walking Dead, Vol. 13: Too Far Gone* — Robert Kirkman (loading 0.08017, n=2,093)

### Mode 17 negative

1. *A Crown of Swords (Wheel of Time, #7)* — Robert Jordan (loading 0.16496, n=9,473)
2. *Lord of Chaos (Wheel of Time, #6)* — Robert Jordan (loading 0.16398, n=10,180)
3. *The Fires of Heaven (Wheel of Time, #5)* — Robert Jordan (loading 0.15052, n=10,695)
4. *The Shadow Rising (Wheel of Time, #4)* — Robert Jordan (loading 0.14186, n=12,786)
5. *The Path of Daggers (Wheel of Time, #8)* — Robert Jordan (loading 0.13889, n=8,700)
6. *Winter's Heart (Wheel of Time, #9)* — Robert Jordan (loading 0.13556, n=8,189)
7. *Knife of Dreams (Wheel of Time, #11)* — Robert Jordan (loading 0.13346, n=7,460)
8. *The Dragon Reborn (Wheel of Time, #3)* — Robert Jordan (loading 0.13054, n=15,289)
9. *The Great Hunt (Wheel of Time, #2)* — Robert Jordan (loading 0.12352, n=16,452)
10. *The Gathering Storm (Wheel of Time, #12)* — Robert Jordan (loading 0.12255, n=8,913)
11. *Crossroads of Twilight (Wheel of Time, #10)* — Robert Jordan (loading 0.10702, n=7,393)
12. *Towers of Midnight (Wheel of Time, #13)* — Robert Jordan (loading 0.10498, n=8,222)

### Mode 18 positive

1. *Brief Lives (The Sandman #7)* — Neil Gaiman (loading 0.10374, n=5,161)
2. *Season of Mists (The Sandman #4)* — Neil Gaiman (loading 0.10109, n=6,862)
3. *Worlds' End (The Sandman #8)* — Neil Gaiman (loading 0.09914, n=4,738)
4. *Fables and Reflections (The Sandman #6)* — Neil Gaiman (loading 0.09735, n=5,294)
5. *The Wake (The Sandman #10)* — Neil Gaiman (loading 0.09615, n=4,401)
6. *A Game of You (The Sandman #5)* — Neil Gaiman (loading 0.09604, n=5,769)
7. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (loading 0.09526, n=4,713)
8. *The Doll's House (The Sandman #2)* — Neil Gaiman (loading 0.09420, n=8,833)
9. *Dream Country (The Sandman #3)* — Neil Gaiman (loading 0.09020, n=8,018)
10. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (loading 0.07588, n=19,224)
11. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.07066, n=183,770)
12. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (loading 0.07064, n=177,929)

### Mode 18 negative

1. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.15901, n=2,171)
2. *Vampire Mountain (Cirque Du Freak, #4)* — Darren Shan (loading 0.15852, n=2,715)
3. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.15663, n=2,104)
4. *Trials of Death (Cirque Du Freak, #5)* — Darren Shan (loading 0.15193, n=2,494)
5. *The Vampire's Assistant* — Darren Shan (loading 0.15171, n=3,665)
6. *The Vampire Prince (Cirque Du Freak, #6)* — Darren Shan (loading 0.15029, n=2,389)
7. *Tunnels of Blood* — Darren Shan (loading 0.14269, n=3,043)
8. *Killers of the Dawn (Cirque Du Freak, #9)* — Darren Shan (loading 0.13996, n=2,061)
9. *A Living Nightmare (Cirque Du Freak, #1)* — Darren Shan (loading 0.12671, n=4,872)
10. *Wicked (Pretty Little Liars, #5)* — Sara Shepard (loading 0.08087, n=4,919)
11. *Perfect (Pretty Little Liars, #3)* — Sara Shepard (loading 0.08034, n=6,650)
12. *Heartless (Pretty Little Liars, #7)* — Sara Shepard (loading 0.07793, n=4,090)

### Mode 19 positive

1. *A Crown of Swords (Wheel of Time, #7)* — Robert Jordan (loading 0.11014, n=9,473)
2. *The Path of Daggers (Wheel of Time, #8)* — Robert Jordan (loading 0.10143, n=8,700)
3. *Winter's Heart (Wheel of Time, #9)* — Robert Jordan (loading 0.10097, n=8,189)
4. *Lord of Chaos (Wheel of Time, #6)* — Robert Jordan (loading 0.09974, n=10,180)
5. *The Fires of Heaven (Wheel of Time, #5)* — Robert Jordan (loading 0.09117, n=10,695)
6. *Knife of Dreams (Wheel of Time, #11)* — Robert Jordan (loading 0.08538, n=7,460)
7. *Crossroads of Twilight (Wheel of Time, #10)* — Robert Jordan (loading 0.08266, n=7,393)
8. *The Shadow Rising (Wheel of Time, #4)* — Robert Jordan (loading 0.08009, n=12,786)
9. *The Dragon Reborn (Wheel of Time, #3)* — Robert Jordan (loading 0.06958, n=15,289)
10. *Y: The Last Man, Vol. 7: Paper Dolls (Y: The Last Man, #7)* — Brian K. Vaughan (loading 0.06913, n=2,860)
11. *Y: The Last Man, Vol. 4: Safeword (Y: The Last Man, #4)* — Brian K. Vaughan (loading 0.06660, n=3,144)
12. *Y: The Last Man, Vol. 5: Ring of Truth (Y: The Last Man, #5)* — Brian K. Vaughan (loading 0.06593, n=3,201)

### Mode 19 negative

1. *Hunted (House of Night, #5)* — P.C. Cast (loading 0.11859, n=17,669)
2. *Chosen (House of Night, #3)* — P.C. Cast (loading 0.11703, n=21,124)
3. *Tempted (House of Night, #6)* — P.C. Cast (loading 0.11531, n=16,108)
4. *Untamed (House of Night, #4)* — P.C. Cast (loading 0.11441, n=21,097)
5. *Betrayed (House of Night, #2)* — P.C. Cast (loading 0.11063, n=23,424)
6. *Beyond the Grave (The 39 Clues #4)* — Jude Watson (loading 0.11009, n=2,479)
7. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.10983, n=2,629)
8. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.10797, n=2,253)
9. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.10762, n=2,236)
10. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.10640, n=2,179)
11. *Burned (House of Night, #7)* — P.C. Cast (loading 0.10376, n=14,324)
12. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.10172, n=2,171)

### Mode 20 positive

1. *Fables and Reflections (The Sandman #6)* — Neil Gaiman (loading 0.08208, n=5,294)
2. *A Game of You (The Sandman #5)* — Neil Gaiman (loading 0.07746, n=5,769)
3. *Worlds' End (The Sandman #8)* — Neil Gaiman (loading 0.07589, n=4,738)
4. *Brief Lives (The Sandman #7)* — Neil Gaiman (loading 0.07557, n=5,161)
5. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (loading 0.07350, n=4,713)
6. *Season of Mists (The Sandman #4)* — Neil Gaiman (loading 0.07301, n=6,862)
7. *The Wake (The Sandman #10)* — Neil Gaiman (loading 0.07268, n=4,401)
8. *The Doll's House (The Sandman #2)* — Neil Gaiman (loading 0.06940, n=8,833)
9. *Dream Country (The Sandman #3)* — Neil Gaiman (loading 0.06542, n=8,018)
10. *The Vampire's Assistant* — Darren Shan (loading 0.06451, n=3,665)
11. *Vampire Mountain (Cirque Du Freak, #4)* — Darren Shan (loading 0.06403, n=2,715)
12. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.06336, n=3,689)

### Mode 20 negative

1. *Y: The Last Man, Vol. 7: Paper Dolls (Y: The Last Man, #7)* — Brian K. Vaughan (loading 0.20303, n=2,860)
2. *Y: The Last Man, Vol. 5: Ring of Truth (Y: The Last Man, #5)* — Brian K. Vaughan (loading 0.19129, n=3,201)
3. *Y: The Last Man, Vol. 3: One Small Step (Y: The Last Man, #3)* — Brian K. Vaughan (loading 0.19030, n=3,457)
4. *Y: The Last Man, Vol. 4: Safeword (Y: The Last Man, #4)* — Brian K. Vaughan (loading 0.18976, n=3,144)
5. *Y: The Last Man, Vol. 9: Motherland (Y: The Last Man, #9)* — Brian K. Vaughan (loading 0.18920, n=2,683)
6. *Y: The Last Man, Vol. 8: Kimono Dragons (Y: The Last Man, #8)* — Brian K. Vaughan (loading 0.18641, n=2,841)
7. *Y: The Last Man, Vol. 6: Girl on Girl (Y: The Last Man, #6)* — Brian K. Vaughan (loading 0.17588, n=2,758)
8. *Y: The Last Man, Vol. 2: Cycles (Y: The Last Man, #2)* — Brian K. Vaughan (loading 0.17322, n=4,155)
9. *Y: The Last Man, Vol. 10: Whys and Wherefores (Y: The Last Man, #10)* — Brian K. Vaughan (loading 0.15079, n=2,640)
10. *Y: The Last Man, Vol. 1: Unmanned* — Brian K. Vaughan (loading 0.12738, n=8,665)
11. *Beyond the Grave (The 39 Clues #4)* — Jude Watson (loading 0.10333, n=2,479)
12. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.10028, n=2,629)

### Mode 21 positive

1. *Thinner* — Richard Bachman (loading 0.10849, n=12,621)
2. *Gerald's Game* — Stephen King (loading 0.10695, n=11,167)
3. *The Tommyknockers* — Stephen King (loading 0.10377, n=10,935)
4. *Dreamcatcher* — Stephen King (loading 0.10176, n=12,202)
5. *Cujo* — Stephen King (loading 0.09977, n=16,907)
6. *From a Buick 8* — Stephen King (loading 0.08851, n=5,758)
7. *The Dark Half* — Stephen King (loading 0.08775, n=10,571)
8. *Christine* — Stephen King (loading 0.08000, n=15,432)
9. *Rose Madder* — Stephen King (loading 0.07913, n=8,465)
10. *Cell* — Stephen King (loading 0.07535, n=14,917)
11. *The Girl Who Loved Tom Gordon* — Stephen King (loading 0.07474, n=11,696)
12. *Sorceress of Darshiva (The Malloreon, #4)* — David Eddings (loading 0.07438, n=3,851)

### Mode 21 negative

1. *Hunted (House of Night, #5)* — P.C. Cast (loading 0.11490, n=17,669)
2. *Chosen (House of Night, #3)* — P.C. Cast (loading 0.11193, n=21,124)
3. *Untamed (House of Night, #4)* — P.C. Cast (loading 0.11175, n=21,097)
4. *Tempted (House of Night, #6)* — P.C. Cast (loading 0.11172, n=16,108)
5. *Betrayed (House of Night, #2)* — P.C. Cast (loading 0.10414, n=23,424)
6. *Burned (House of Night, #7)* — P.C. Cast (loading 0.10340, n=14,324)
7. *Chainfire (Sword of Truth, #9)* — Terry Goodkind (loading 0.09775, n=4,026)
8. *Naked Empire (Sword of Truth, #8)* — Terry Goodkind (loading 0.09242, n=4,314)
9. *Phantom (Sword of Truth, #10)* — Terry Goodkind (loading 0.09117, n=3,723)
10. *Awakened (House of Night, #8)* — P.C. Cast (loading 0.08591, n=11,827)
11. *Soul of the Fire (Sword of Truth, #5)* — Terry Goodkind (loading 0.08570, n=5,391)
12. *Temple of the Winds (Sword of Truth, #4)* — Terry Goodkind (loading 0.08473, n=6,341)

### Mode 22 positive

1. *Vampire Mountain (Cirque Du Freak, #4)* — Darren Shan (loading 0.12961, n=2,715)
2. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.12869, n=2,171)
3. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.12480, n=2,104)
4. *Trials of Death (Cirque Du Freak, #5)* — Darren Shan (loading 0.12400, n=2,494)
5. *The Vampire Prince (Cirque Du Freak, #6)* — Darren Shan (loading 0.12307, n=2,389)
6. *The Vampire's Assistant* — Darren Shan (loading 0.12245, n=3,665)
7. *Tunnels of Blood* — Darren Shan (loading 0.11434, n=3,043)
8. *Killers of the Dawn (Cirque Du Freak, #9)* — Darren Shan (loading 0.11149, n=2,061)
9. *A Living Nightmare (Cirque Du Freak, #1)* — Darren Shan (loading 0.10438, n=4,872)
10. *Death Note, Vol. 3: Hard Run (Death Note, #3)* — Tsugumi Ohba (loading 0.09188, n=3,103)
11. *Death Note, Vol. 4: Love (Death Note, #4)* — Tsugumi Ohba (loading 0.09099, n=2,846)
12. *Death Note, Vol. 2: Confluence (Death Note, #2)* — Tsugumi Ohba (loading 0.09004, n=3,608)

### Mode 22 negative

1. *The 3 Mistakes of My Life* — Chetan Bhagat (loading 0.09665, n=5,706)
2. *One Night at the Call Center* — Chetan Bhagat (loading 0.09477, n=4,995)
3. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.08672, n=2,179)
4. *2 States: The Story of My Marriage* — Chetan Bhagat (loading 0.08624, n=7,006)
5. *Revolution 2020: Love, Corruption, Ambition* — Chetan Bhagat (loading 0.08560, n=4,283)
6. *Beyond the Grave (The 39 Clues #4)* — Jude Watson (loading 0.08468, n=2,479)
7. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.08393, n=2,629)
8. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.08085, n=2,253)
9. *Five Point Someone* — Chetan Bhagat (loading 0.07897, n=7,107)
10. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.07858, n=2,236)
11. *ثلاثية غرناطة* — Radwa Ashour (loading 0.07718, n=6,061)
12. *The Sword Thief (The 39 Clues, #3)* — Peter Lerangis (loading 0.07596, n=2,811)

### Mode 23 positive

1. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.14860, n=2,236)
2. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.14774, n=2,629)
3. *Beyond the Grave (The 39 Clues #4)* — Jude Watson (loading 0.14668, n=2,479)
4. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.14568, n=2,179)
5. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.14396, n=2,253)
6. *The Sword Thief (The 39 Clues, #3)* — Peter Lerangis (loading 0.13410, n=2,811)
7. *Into the Gauntlet (The 39 Clues, #10)* — Margaret Peterson Haddix (loading 0.12246, n=2,489)
8. *One False Note (The 39 Clues, #2)* — Gordon Korman (loading 0.12193, n=3,070)
9. *Vampire Mountain (Cirque Du Freak, #4)* — Darren Shan (loading 0.12135, n=2,715)
10. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.11966, n=2,171)
11. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.11754, n=2,104)
12. *Trials of Death (Cirque Du Freak, #5)* — Darren Shan (loading 0.11591, n=2,494)

### Mode 23 negative

1. *Emperor Mage (Immortals, #3)* — Tamora Pierce (loading 0.08068, n=5,418)
2. *Lioness Rampant (Song of the Lioness, #4)* — Tamora Pierce (loading 0.07804, n=7,696)
3. *In the Hand of the Goddess (Song of the Lioness, #2)* — Tamora Pierce (loading 0.07688, n=8,348)
4. *Wild Magic (Immortals, #1)* — Tamora Pierce (loading 0.07610, n=6,693)
5. *The Woman Who Rides Like a Man (Song of the Lioness, #3)* — Tamora Pierce (loading 0.07496, n=7,396)
6. *Alanna: The First Adventure (Song of the Lioness, #1)* — Tamora Pierce (loading 0.07437, n=11,006)
7. *The Realms of the Gods (Immortals, #4)* — Tamora Pierce (loading 0.06914, n=5,140)
8. *Page (Protector of the Small, #2)* — Tamora Pierce (loading 0.06822, n=4,655)
9. *Lady Knight (Protector of the Small, #4)* — Tamora Pierce (loading 0.06512, n=4,848)
10. *First Test (Protector of the Small, #1)* — Tamora Pierce (loading 0.06508, n=5,349)
11. *The Last Straw (Diary of a Wimpy Kid, #3)* — Jeff Kinney (loading 0.06424, n=4,906)
12. *Wolf-Speaker (Immortals, #2)* — Tamora Pierce (loading 0.06367, n=5,126)

### Mode 24 positive

1. *Chainfire (Sword of Truth, #9)* — Terry Goodkind (loading 0.09121, n=4,026)
2. *Phantom (Sword of Truth, #10)* — Terry Goodkind (loading 0.08719, n=3,723)
3. *Lover Eternal (Black Dagger Brotherhood, #2)* — J.R. Ward (loading 0.08519, n=19,584)
4. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (loading 0.08393, n=19,224)
5. *Lover Revealed (Black Dagger Brotherhood, #4)* — J.R. Ward (loading 0.07959, n=15,969)
6. *Naked Empire (Sword of Truth, #8)* — Terry Goodkind (loading 0.07842, n=4,314)
7. *Lover Unbound (Black Dagger Brotherhood, #5)* — J.R. Ward (loading 0.07811, n=15,621)
8. *Temple of the Winds (Sword of Truth, #4)* — Terry Goodkind (loading 0.07590, n=6,341)
9. *Blood of the Fold (Sword of Truth, #3)* — Terry Goodkind (loading 0.07371, n=6,926)
10. *Faith of the Fallen (Sword of Truth, #6)* — Terry Goodkind (loading 0.07275, n=5,531)
11. *Confessor (Sword of Truth, #11)* — Terry Goodkind (loading 0.07260, n=3,747)
12. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.07256, n=2,171)

### Mode 24 negative

1. *Death Note, Vol. 4: Love (Death Note, #4)* — Tsugumi Ohba (loading 0.11388, n=2,846)
2. *Death Note, Vol. 2: Confluence (Death Note, #2)* — Tsugumi Ohba (loading 0.11305, n=3,608)
3. *Every Which Way But Dead (The Hollows, #3)* — Kim Harrison (loading 0.11256, n=8,469)
4. *For a Few Demons More (The Hollows, #5)* — Kim Harrison (loading 0.10960, n=7,067)
5. *Death Note, Vol. 3: Hard Run (Death Note, #3)* — Tsugumi Ohba (loading 0.10764, n=3,103)
6. *The Outlaw Demon Wails (The Hollows, #6)* — Kim Harrison (loading 0.10724, n=6,748)
7. *The Good, the Bad, and the Undead (The Hollows, #2)* — Kim Harrison (loading 0.10667, n=8,197)
8. *Death Note, Vol. 6: Give-and-Take (Death Note, #6)* — Tsugumi Ohba (loading 0.10283, n=2,338)
9. *Death Note, Vol. 5: Whiteout (Death Note, #5)* — Tsugumi Ohba (loading 0.10165, n=2,573)
10. *A Fistful of Charms (The Hollows, #4)* — Kim Harrison (loading 0.09917, n=7,036)
11. *Death Note, Vol. 7: Zero (Death Note, #7)* — Tsugumi Ohba (loading 0.09901, n=2,189)
12. *Black Magic Sanction (The Hollows, #8)* — Kim Harrison (loading 0.09808, n=5,750)

## Interpretation rule

A mode is structurally credible only if it exceeds the shuffled spectrum and aligns across both disjoint-reader halves. Literary overlap is descriptive post-hoc evidence, not part of mode fitting, orientation, ordering, or acceptance. If literary books appear only in unstable or null-sized modes, the ratings matrix does not support a naturally identifiable single literary axis under this operator.

# Seedless signed spectral pilot

## Design

Discovery used only `(user_id, work_id, rating)`. Each reader contributes equal total positive (5-star) and negative (1–3-star) mass. Ratings-derived book popularity, mean, five-star tendency, user activity, and generosity are projected out. Titles, authors, flags, and semantic lists are loaded only after all full/half/null decompositions finish.

Matrix: **233,271 users × 26,418 works**, **7,340,284 signed edges**. Runtime: **36.8s**; matrix cache: **18.3 MiB**.

The two half-sample fits use disjoint readers. The shuffled null preserves each reader's positive/negative counts and the global positive/negative book frequencies while destroying reader-level co-preference.

## Spectrum and stability

### Stable-subspace test

Unlike individual-vector correlation, this test allows tied or nearly tied modes to rotate within the same shared subspace.

| leading modes | full↔half mean sq. corr | full↔half weakest | half↔half mean sq. corr | half↔half weakest |
|---:|---:|---:|---:|---:|
| 1 | 0.965 | 0.983 | 0.870 | 0.933 |
| 2 | 0.956 | 0.972 | 0.851 | 0.912 |
| 3 | 0.823 | 0.719 | 0.587 | 0.219 |
| 4 | 0.876 | 0.807 | 0.655 | 0.401 |
| 6 | 0.845 | 0.531 | 0.658 | 0.194 |
| 8 | 0.899 | 0.851 | 0.718 | 0.651 |
| 12 | 0.773 | 0.373 | 0.567 | 0.004 |
| 16 | 0.727 | 0.274 | 0.509 | 0.091 |
| 24 | 0.673 | 0.116 | 0.457 | 0.007 |
| 32 | 0.595 | 0.005 | 0.400 | 0.001 |

### Individual modes

`eff. books` is the inverse concentration of squared loadings: larger means broader; `top50 mass` is the fraction of a mode carried by its 50 most extreme books.

| mode | singular | null | excess | residual | half corr | half pole J@100 | eff. books | top50 mass | exact lit +/− @50 | broad lit +/− @50 | anti +/− @50 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.7475 | 0.4680 | 1.60 | 6.17e-03 | 0.983 | 0.815 | 148 | 0.460 | 0/0 | 2/0 | 0/0 |
| 2 | 0.7178 | 0.4609 | 1.56 | 1.03e-02 | 0.972 | 0.844 | 1031 | 0.162 | 0/1 | 0/1 | 50/26 |
| 3 | 0.6963 | 0.4210 | 1.65 | 1.88e-02 | 0.852 | 0.403 | 97 | 0.663 | 0/0 | 0/0 | 5/0 |
| 4 | 0.6864 | 0.4197 | 1.64 | 1.87e-02 | 0.713 | 0.531 | 112 | 0.600 | 0/0 | 0/0 | 0/21 |
| 5 | 0.6703 | 0.4194 | 1.60 | 3.15e-02 | 0.729 | 0.375 | 104 | 0.641 | 0/0 | 0/0 | 10/23 |
| 6 | 0.6637 | 0.4190 | 1.58 | 2.91e-02 | 0.757 | 0.460 | 677 | 0.204 | 0/0 | 0/0 | 23/35 |
| 7 | 0.6599 | 0.4187 | 1.58 | 3.23e-02 | 0.770 | 0.420 | 276 | 0.343 | 0/0 | 0/0 | 28/38 |
| 8 | 0.6382 | 0.4185 | 1.52 | 4.05e-02 | 0.852 | 0.443 | 209 | 0.419 | 0/0 | 0/0 | 43/47 |
| 9 | 0.6259 | 0.4182 | 1.50 | 4.15e-02 | 0.628 | 0.397 | 55 | 0.678 | 0/0 | 0/0 | 50/0 |
| 10 | 0.6226 | 0.4180 | 1.49 | 4.34e-02 | 0.483 | 0.142 | 38 | 0.641 | 0/0 | 0/0 | 27/15 |
| 11 | 0.6195 | 0.4178 | 1.48 | 4.99e-02 | 0.480 | 0.309 | 161 | 0.507 | 0/0 | 0/0 | 6/11 |
| 12 | 0.6183 | 0.4177 | 1.48 | 5.04e-02 | 0.487 | 0.254 | 163 | 0.465 | 0/0 | 0/0 | 8/0 |
| 13 | 0.6163 | 0.4175 | 1.48 | 6.06e-02 | 0.498 | 0.330 | 308 | 0.351 | 0/0 | 0/0 | 26/35 |
| 14 | 0.6113 | 0.4170 | 1.47 | 5.68e-02 | 0.584 | 0.315 | 98 | 0.542 | 0/0 | 0/0 | 0/14 |
| 15 | 0.6102 | 0.4168 | 1.46 | 5.52e-02 | 0.488 | 0.293 | 96 | 0.574 | 0/0 | 0/0 | 3/4 |
| 16 | 0.6065 | 0.4166 | 1.46 | 5.93e-02 | 0.338 | 0.187 | 178 | 0.441 | 0/0 | 0/0 | 0/19 |
| 17 | 0.6040 | 0.4164 | 1.45 | 6.85e-02 | 0.406 | 0.185 | 57 | 0.561 | 0/0 | 0/0 | 1/18 |
| 18 | 0.6023 | 0.4163 | 1.45 | 6.67e-02 | 0.382 | 0.099 | 107 | 0.431 | 0/0 | 0/0 | 1/14 |
| 19 | 0.5995 | 0.4163 | 1.44 | 6.29e-02 | 0.413 | 0.125 | 167 | 0.420 | 0/0 | 0/0 | 1/0 |
| 20 | 0.5969 | 0.4160 | 1.43 | 6.17e-02 | 0.299 | 0.254 | 230 | 0.395 | 0/0 | 0/0 | 21/11 |
| 21 | 0.5904 | 0.4158 | 1.42 | 7.85e-02 | 0.337 | 0.248 | 193 | 0.362 | 0/0 | 0/0 | 13/1 |
| 22 | 0.5888 | 0.4158 | 1.42 | 8.30e-02 | 0.283 | 0.138 | 213 | 0.434 | 0/0 | 0/0 | 0/3 |
| 23 | 0.5863 | 0.4156 | 1.41 | 7.98e-02 | 0.214 | 0.118 | 161 | 0.479 | 0/0 | 0/0 | 2/22 |
| 24 | 0.5830 | 0.4154 | 1.40 | 7.57e-02 | 0.358 | 0.207 | 212 | 0.400 | 0/0 | 0/0 | 20/15 |
| 25 | 0.5803 | 0.4152 | 1.40 | 6.63e-02 | 0.267 | 0.078 | 309 | 0.304 | 0/0 | 0/0 | 0/16 |
| 26 | 0.5754 | 0.4152 | 1.39 | 8.22e-02 | 0.151 | 0.104 | 296 | 0.341 | 0/0 | 0/0 | 19/47 |
| 27 | 0.5750 | 0.4148 | 1.39 | 9.13e-02 | 0.203 | 0.139 | 289 | 0.320 | 0/0 | 0/0 | 11/1 |
| 28 | 0.5715 | 0.4147 | 1.38 | 7.32e-02 | 0.204 | 0.110 | 342 | 0.304 | 0/0 | 0/0 | 25/6 |
| 29 | 0.5683 | 0.4146 | 1.37 | 8.14e-02 | 0.200 | 0.081 | 393 | 0.305 | 0/0 | 0/0 | 7/0 |
| 30 | 0.5665 | 0.4146 | 1.37 | 8.43e-02 | 0.168 | 0.154 | 578 | 0.221 | 0/0 | 0/0 | 7/21 |
| 31 | 0.5649 | 0.4143 | 1.36 | 9.00e-02 | 0.167 | 0.092 | 795 | 0.168 | 0/0 | 0/0 | 11/10 |
| 32 | 0.5640 | 0.4141 | 1.36 | 8.19e-02 | 0.244 | 0.149 | 462 | 0.252 | 0/0 | 0/0 | 23/8 |

## Mode poles

### Mode 1 positive

1. *ثلاثية غرناطة* — Radwa Ashour (loading 0.18167, n=6,061)
2. *الطنطورية* — Radwa Ashour (loading 0.16063, n=3,142)
3. *ساق البامبو* — s`wd lsn`wsy (loading 0.13213, n=7,228)
4. *الحرافيش* — Naguib Mahfouz (loading 0.12812, n=2,008)
5. *رباعيات صلاح جاهين* — SlH jhyn (loading 0.12539, n=2,045)
6. *لا تصالح* — 'ml dnql (loading 0.12099, n=898)
7. *عزازيل* — ywsf zydn (loading 0.10828, n=7,420)
8. *زمن الخيول البيضاء* — Ibrahim Nasrallah - ibrhym nSr llh (loading 0.10429, n=1,322)
9. *المانيفستو* — mSTf~ brhym (loading 0.10323, n=1,472)
10. *الإسلام بين الشرق والغرب* — Alija Izetbegovic (loading 0.10221, n=1,500)
11. *عائد إلى حيفا* — Gsn knfny (loading 0.10160, n=2,520)
12. *ويسترن يونيون فرع الهرم: ديوان بالعامية المصرية* — mSTf~ brhym (loading 0.09716, n=1,047)

### Mode 1 negative

1. *28 حرف* — 'Hmd Hlmy (loading 0.13033, n=2,862)
2. *نيكروفيليا* — shyryn hny'y (loading 0.11983, n=1,581)
3. *السنجة* — 'Hmd khld twfyq (loading 0.10648, n=1,991)
4. *ليتها تقرأ* — khld lbtly (loading 0.10448, n=1,995)
5. *ظل الأفعى* — ywsf zydn (loading 0.10295, n=2,383)
6. *شيكاجو* — Alaa Al Aswany (loading 0.09353, n=3,195)
7. *الفيل الأزرق* — 'Hmd mrd (loading 0.09341, n=7,149)
8. *محال* — ywsf zydn (loading 0.09243, n=2,062)
9. *النبطي* — ywsf zydn (loading 0.08679, n=2,578)
10. *نادي السيارات* — Alaa Al Aswany (loading 0.08487, n=1,821)
11. *الرجال من بولاق والنساء من أول فيصل* — yhb m`wD (loading 0.08398, n=1,103)
12. *أحببتك أكثر مما ينبغي* — 'thyr `bdllh lnshmy (loading 0.08301, n=5,546)

### Mode 2 positive

1. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (loading 0.08713, n=32,297)
2. *Clockwork Prince (The Infernal Devices, #2)* — Cassandra Clare (loading 0.07825, n=38,779)
3. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (loading 0.07797, n=23,734)
4. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (loading 0.07603, n=30,591)
5. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (loading 0.07161, n=20,041)
6. *City of Glass (The Mortal Instruments, #3)* — Cassandra Clare (loading 0.07138, n=67,752)
7. *Divergent (Divergent, #1)* — Veronica Roth (loading 0.06846, n=161,403)
8. *City of Heavenly Fire (The Mortal Instruments, #6)* — Cassandra Clare (loading 0.06788, n=28,473)
9. *Catching Fire (The Hunger Games, #2)* — Suzanne Collins (loading 0.06657, n=182,350)
10. *The Hunger Games (The Hunger Games, #1)* — Suzanne Collins (loading 0.06607, n=288,704)
11. *Heir of Fire (Throne of Glass, #3)* — Sarah J. Maas (loading 0.06605, n=24,457)
12. *Clockwork Angel (The Infernal Devices, #1)* — Cassandra Clare (loading 0.06210, n=54,188)

### Mode 2 negative

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (loading 0.05871, n=10,709)
2. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (loading 0.05821, n=15,510)
3. *Fallen (Fallen, #1)* — Lauren Kate (loading 0.05497, n=39,502)
4. *Evermore (The Immortals, #1)* — Alyson Noel (loading 0.05446, n=24,321)
5. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (loading 0.05216, n=42,646)
6. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (loading 0.05084, n=49,797)
7. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (loading 0.05060, n=53,880)
8. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (loading 0.04980, n=119,871)
9. *Changes (The Dresden Files, #12)* — Jim Butcher (loading 0.04777, n=9,238)
10. *Matched (Matched, #1)* — Ally Condie (loading 0.04770, n=47,728)
11. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (loading 0.04759, n=27,968)
12. *Blue Moon (The Immortals, #2)* — Alyson Noel (loading 0.04707, n=10,482)

### Mode 3 positive

1. *حياة في الإدارة* — Gzy `bd lrHmn lqSyby (loading 0.03184, n=1,367)
2. *Otomen, Vol. 1 (Otomen, #1)* — Aya Kanno (loading 0.01921, n=777)
3. *Stay Out of the Basement  (Goosebumps, #2)* — R.L. Stine (loading 0.01829, n=1,611)
4. *Black Bird, Vol. 01 (Black Bird, #1)* — Kanoko Sakurakouji (loading 0.01793, n=2,153)
5. *Chobits, Vol. 4* — CLAMP (loading 0.01656, n=733)
6. *Vampire Knight, Vol. 1 (Vampire Knight, #1)* — Matsuri Hino (loading 0.01651, n=5,872)
7. *Monster Blood (Goosebumps, #3)* — R.L. Stine (loading 0.01639, n=1,071)
8. *D.Gray-man, Vol. #2 (D.Gray-man, #2)* — Katsura Hoshino (loading 0.01636, n=511)
9. *Be Careful What You Wish For... (Goosebumps, #12)* — R.L. Stine (loading 0.01635, n=1,080)
10. *Chobits, Vol. 2* — CLAMP (loading 0.01607, n=781)
11. *Chobits, Vol. 6* — CLAMP (loading 0.01593, n=653)
12. *Absolute Boyfriend, Vol. 6* — Yuu Watase (loading 0.01574, n=652)

### Mode 3 negative

1. *Naruto, Vol. 07: Orochimaru's Curse (Naruto, #7)* — Masashi Kishimoto (loading 0.14700, n=939)
2. *Naruto, Vol. 10: A Splendid Ninja (Naruto, #10)* — Masashi Kishimoto (loading 0.14487, n=829)
3. *Naruto, Vol. 21: Pursuit (Naruto, #21)* — Masashi Kishimoto (loading 0.14037, n=686)
4. *Naruto, Vol. 16: Eulogy (Naruto, #16)* — Masashi Kishimoto (loading 0.13178, n=711)
5. *Naruto, Vol. 05: Exam Hell (Naruto, #5)* — Masashi Kishimoto (loading 0.13009, n=1,129)
6. *Naruto, Vol. 19: Successor (Naruto, #19)* — Masashi Kishimoto (loading 0.12940, n=720)
7. *Fullmetal Alchemist, Vol. 20 (Fullmetal Alchemist, #20)* — Hiromu Arakawa (loading 0.12924, n=707)
8. *Fullmetal Alchemist, Vol. 11 (Fullmetal Alchemist, #11)* — Hiromu Arakawa (loading 0.12539, n=879)
9. *Fullmetal Alchemist, Vol. 21 (Fullmetal Alchemist, #21)* — Hiromu Arakawa (loading 0.12481, n=667)
10. *Fullmetal Alchemist, Vol. 22 (Fullmetal Alchemist, #22)* — Hiromu Arakawa (loading 0.12481, n=678)
11. *Naruto, Vol. 15: Naruto's Ninja Handbook! (Naruto, #15)* — Masashi Kishimoto (loading 0.12333, n=742)
12. *Fullmetal Alchemist, Vol. 10 (Fullmetal Alchemist, #10)* — Hiromu Arakawa (loading 0.12204, n=902)

### Mode 4 positive

1. *Naruto, Vol. 21: Pursuit (Naruto, #21)* — Masashi Kishimoto (loading 0.12572, n=686)
2. *Naruto, Vol. 07: Orochimaru's Curse (Naruto, #7)* — Masashi Kishimoto (loading 0.12214, n=939)
3. *Naruto, Vol. 10: A Splendid Ninja (Naruto, #10)* — Masashi Kishimoto (loading 0.12149, n=829)
4. *Naruto, Vol. 12: The Great Flight (Naruto, #12)* — Masashi Kishimoto (loading 0.11799, n=807)
5. *Naruto, Vol. 05: Exam Hell (Naruto, #5)* — Masashi Kishimoto (loading 0.11461, n=1,129)
6. *Naruto, Vol. 31: Final Battle (Naruto, #31)* — Masashi Kishimoto (loading 0.11094, n=646)
7. *Naruto, Vol. 03: Bridge of Courage (Naruto, #3)* — Masashi Kishimoto (loading 0.11090, n=1,132)
8. *Naruto, Vol. 17: Itachi's Power (Naruto, #17)* — Masashi Kishimoto (loading 0.10875, n=725)
9. *Naruto, Vol. 09: Turning the Tables (Naruto, #9)* — Masashi Kishimoto (loading 0.10756, n=886)
10. *Naruto, Vol. 19: Successor (Naruto, #19)* — Masashi Kishimoto (loading 0.10711, n=720)
11. *Naruto, Vol. 15: Naruto's Ninja Handbook! (Naruto, #15)* — Masashi Kishimoto (loading 0.10611, n=742)
12. *Naruto, Vol. 26: Awakening (Naruto, #26)* — Masashi Kishimoto (loading 0.10562, n=680)

### Mode 4 negative

1. *Fullmetal Alchemist, Vol. 20 (Fullmetal Alchemist, #20)* — Hiromu Arakawa (loading 0.14471, n=707)
2. *Fullmetal Alchemist, Vol. 11 (Fullmetal Alchemist, #11)* — Hiromu Arakawa (loading 0.13508, n=879)
3. *Fullmetal Alchemist, Vol. 16 (Fullmetal Alchemist, #16)* — Hiromu Arakawa (loading 0.13341, n=757)
4. *Fullmetal Alchemist, Vol. 3 (Fullmetal Alchemist, #3)* — Hiromu Arakawa (loading 0.12850, n=1,391)
5. *Fullmetal Alchemist, Vol. 25 (Fullmetal Alchemist, #25)* — Hiromu Arakawa (loading 0.12713, n=590)
6. *Fullmetal Alchemist, Vol. 10 (Fullmetal Alchemist, #10)* — Hiromu Arakawa (loading 0.12695, n=902)
7. *Fullmetal Alchemist, Vol. 22 (Fullmetal Alchemist, #22)* — Hiromu Arakawa (loading 0.12399, n=678)
8. *Fullmetal Alchemist, Vol. 9 (Fullmetal Alchemist, #9)* — Hiromu Arakawa (loading 0.12053, n=978)
9. *Fullmetal Alchemist, Vol. 6 (Fullmetal Alchemist, #6)* — Hiromu Arakawa (loading 0.11910, n=1,088)
10. *Fullmetal Alchemist, Vol. 23 (Fullmetal Alchemist, #23)* — Hiromu Arakawa (loading 0.11863, n=695)
11. *Fullmetal Alchemist, Vol. 21 (Fullmetal Alchemist, #21)* — Hiromu Arakawa (loading 0.11642, n=667)
12. *Fullmetal Alchemist, Vol. 5 (Fullmetal Alchemist, #5)* — Hiromu Arakawa (loading 0.11441, n=1,216)

### Mode 5 positive

1. *Fullmetal Alchemist, Vol. 20 (Fullmetal Alchemist, #20)* — Hiromu Arakawa (loading 0.13514, n=707)
2. *Fullmetal Alchemist, Vol. 11 (Fullmetal Alchemist, #11)* — Hiromu Arakawa (loading 0.12920, n=879)
3. *Fullmetal Alchemist, Vol. 16 (Fullmetal Alchemist, #16)* — Hiromu Arakawa (loading 0.12527, n=757)
4. *Fullmetal Alchemist, Vol. 22 (Fullmetal Alchemist, #22)* — Hiromu Arakawa (loading 0.11843, n=678)
5. *Fullmetal Alchemist, Vol. 10 (Fullmetal Alchemist, #10)* — Hiromu Arakawa (loading 0.11697, n=902)
6. *Fullmetal Alchemist, Vol. 3 (Fullmetal Alchemist, #3)* — Hiromu Arakawa (loading 0.11343, n=1,391)
7. *Fullmetal Alchemist, Vol. 21 (Fullmetal Alchemist, #21)* — Hiromu Arakawa (loading 0.10878, n=667)
8. *Fullmetal Alchemist, Vol. 25 (Fullmetal Alchemist, #25)* — Hiromu Arakawa (loading 0.10796, n=590)
9. *Fullmetal Alchemist, Vol. 8 (Fullmetal Alchemist, #8)* — Hiromu Arakawa (loading 0.10773, n=985)
10. *Fullmetal Alchemist, Vol. 9 (Fullmetal Alchemist, #9)* — Hiromu Arakawa (loading 0.10716, n=978)
11. *Fullmetal Alchemist, Vol. 23 (Fullmetal Alchemist, #23)* — Hiromu Arakawa (loading 0.10518, n=695)
12. *Fullmetal Alchemist, Vol. 13 (Fullmetal Alchemist, #13)* — Hiromu Arakawa (loading 0.10340, n=838)

### Mode 5 negative

1. *Fruits Basket, Vol. 11* — Natsuki Takaya (loading 0.15454, n=1,612)
2. *Fruits Basket, Vol. 18* — Natsuki Takaya (loading 0.14557, n=1,394)
3. *Fruits Basket, Vol. 4* — Natsuki Takaya (loading 0.14426, n=2,093)
4. *Fruits Basket, Vol. 5* — Natsuki Takaya (loading 0.14387, n=1,922)
5. *Fruits Basket, Vol. 9* — Natsuki Takaya (loading 0.14082, n=1,666)
6. *Fruits Basket, Vol. 7* — Natsuki Takaya (loading 0.13743, n=1,965)
7. *Fruits Basket, Vol. 6* — Natsuki Takaya (loading 0.13697, n=1,829)
8. *Fruits Basket, Vol. 12* — Natsuki Takaya (loading 0.13662, n=1,550)
9. *Fruits Basket, Vol. 8* — Natsuki Takaya (loading 0.13516, n=1,779)
10. *Fruits Basket, Vol. 13* — Natsuki Takaya (loading 0.13350, n=1,566)
11. *Fruits Basket, Vol. 19* — Natsuki Takaya (loading 0.13335, n=1,364)
12. *Fruits Basket, Vol. 16* — Natsuki Takaya (loading 0.12948, n=1,455)

### Mode 6 positive

1. *To Kill a Mockingbird* — Harper Lee (loading 0.06311, n=206,684)
2. *The Help* — Kathryn Stockett (loading 0.05350, n=98,134)
3. *The Crystal Star* — Vonda N. McIntyre (loading 0.05317, n=798)
4. *The Nightingale* — Kristin Hannah (loading 0.05298, n=24,326)
5. *Assault at Selonia (Star Wars: The Corellian Trilogy, #2)* — Roger MacBride Allen (loading 0.05289, n=737)
6. *Micah (Anita Blake, Vampire Hunter, #13)* — Laurell K. Hamilton (loading 0.05206, n=6,328)
7. *The Pillars of Creation (Sword of Truth, #7)* — Terry Goodkind (loading 0.04980, n=4,795)
8. *Tyrant's Test (Star Wars: The Black Fleet Crisis, #3)* — Michael P. Kube-McDowell (loading 0.04886, n=551)
9. *Cerulean Sins (Anita Blake, Vampire Hunter, #11)* — Laurell K. Hamilton (loading 0.04839, n=7,162)
10. *Before the Storm (Star Wars: The Black Fleet Crisis, #1)* — Michael P. Kube-McDowell (loading 0.04786, n=631)
11. *Incubus Dreams (Anita Blake, Vampire Hunter, #12)* — Laurell K. Hamilton (loading 0.04782, n=6,847)
12. *Jedi Eclipse (Agents of Chaos, #2) (Star Wars: The New Jedi Order, #5)* — James Luceno (loading 0.04776, n=629)

### Mode 6 negative

1. *Changes (The Dresden Files, #12)* — Jim Butcher (loading 0.09734, n=9,238)
2. *Small Favor (The Dresden Files, #10)* — Jim Butcher (loading 0.09681, n=9,701)
3. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (loading 0.09666, n=9,264)
4. *White Night (The Dresden Files, #9)* — Jim Butcher (loading 0.09571, n=10,169)
5. *Proven Guilty (The Dresden Files, #8)* — Jim Butcher (loading 0.09231, n=10,347)
6. *Dead Beat (The Dresden Files, #7)* — Jim Butcher (loading 0.09126, n=10,861)
7. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (loading 0.08811, n=15,510)
8. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (loading 0.08756, n=10,709)
9. *Cold Days (The Dresden Files, #14)* — Jim Butcher (loading 0.08565, n=8,201)
10. *Blood Rites (The Dresden Files, #6)* — Jim Butcher (loading 0.08472, n=11,186)
11. *Death Masks (The Dresden Files, #5)* — Jim Butcher (loading 0.08011, n=11,894)
12. *Skin Game (The Dresden Files, #15)* — Jim Butcher (loading 0.07922, n=6,710)

### Mode 7 positive

1. *Fruits Basket, Vol. 11* — Natsuki Takaya (loading 0.12952, n=1,612)
2. *Fruits Basket, Vol. 4* — Natsuki Takaya (loading 0.12149, n=2,093)
3. *Fruits Basket, Vol. 18* — Natsuki Takaya (loading 0.11949, n=1,394)
4. *Fruits Basket, Vol. 9* — Natsuki Takaya (loading 0.11864, n=1,666)
5. *Fruits Basket, Vol. 5* — Natsuki Takaya (loading 0.11768, n=1,922)
6. *Fruits Basket, Vol. 12* — Natsuki Takaya (loading 0.11761, n=1,550)
7. *Fruits Basket, Vol. 7* — Natsuki Takaya (loading 0.11587, n=1,965)
8. *Fruits Basket, Vol. 6* — Natsuki Takaya (loading 0.11446, n=1,829)
9. *Fruits Basket, Vol. 8* — Natsuki Takaya (loading 0.11309, n=1,779)
10. *Fruits Basket, Vol. 19* — Natsuki Takaya (loading 0.11060, n=1,364)
11. *Fruits Basket, Vol. 16* — Natsuki Takaya (loading 0.10810, n=1,455)
12. *Fruits Basket, Vol. 17* — Natsuki Takaya (loading 0.10747, n=1,426)

### Mode 7 negative

1. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (loading 0.06997, n=23,734)
2. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (loading 0.06937, n=20,041)
3. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (loading 0.06926, n=32,297)
4. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (loading 0.06763, n=30,591)
5. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (loading 0.06471, n=192,417)
6. *Heir of Fire (Throne of Glass, #3)* — Sarah J. Maas (loading 0.06318, n=24,457)
7. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.06275, n=183,770)
8. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (loading 0.06147, n=174,713)
9. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (loading 0.06102, n=178,374)
10. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (loading 0.05991, n=177,929)
11. *Clockwork Prince (The Infernal Devices, #2)* — Cassandra Clare (loading 0.05830, n=38,779)
12. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (loading 0.05794, n=190,342)

### Mode 8 positive

1. *Micah (Anita Blake, Vampire Hunter, #13)* — Laurell K. Hamilton (loading 0.06337, n=6,328)
2. *Danse Macabre (Anita Blake, Vampire Hunter, #14)* — Laurell K. Hamilton (loading 0.05821, n=6,397)
3. *Cerulean Sins (Anita Blake, Vampire Hunter, #11)* — Laurell K. Hamilton (loading 0.05678, n=7,162)
4. *Incubus Dreams (Anita Blake, Vampire Hunter, #12)* — Laurell K. Hamilton (loading 0.05610, n=6,847)
5. *Blood Noir (Anita Blake, Vampire Hunter #16)* — Laurell K. Hamilton (loading 0.05089, n=5,520)
6. *The Harlequin (Anita Blake, Vampire Hunter #15)* — Laurell K. Hamilton (loading 0.04829, n=6,131)
7. *Narcissus in Chains (Anita Blake, Vampire Hunter, #10)* — Laurell K. Hamilton (loading 0.04635, n=7,909)
8. *Flirt (Anita Blake, Vampire Hunter #18)* — Laurell K. Hamilton (loading 0.04632, n=4,648)
9. *Skin Trade (Anita Blake, Vampire Hunter #17)* — Laurell K. Hamilton (loading 0.04515, n=5,095)
10. *Bullet (Anita Blake, Vampire Hunter #19)* — Laurell K. Hamilton (loading 0.04289, n=4,403)
11. *Kiss the Dead (Anita Blake, Vampire Hunter #21)* — Laurell K. Hamilton (loading 0.03453, n=3,140)
12. *A Stroke of Midnight (Merry Gentry, #4)* — Laurell K. Hamilton (loading 0.03327, n=4,804)

### Mode 8 negative

1. *Portrait in Death (In Death, #16)* — J.D. Robb (loading 0.13174, n=3,196)
2. *Vengeance in Death (In Death, #6)* — J.D. Robb (loading 0.12463, n=3,896)
3. *Reunion in Death (In Death, #14)* — J.D. Robb (loading 0.12327, n=2,740)
4. *Loyalty in Death (In Death, #9)* — J.D. Robb (loading 0.12105, n=3,184)
5. *Creation in Death (In Death, #25)* — J.D. Robb (loading 0.11942, n=2,472)
6. *Betrayal in Death (In Death, #12)* — J.D. Robb (loading 0.11772, n=3,000)
7. *Conspiracy in Death (In Death, #8)* — J.D. Robb (loading 0.11759, n=3,500)
8. *Imitation in Death (In Death, #17)* — J.D. Robb (loading 0.11560, n=2,679)
9. *Survivor In Death (In Death, #20)* — J.D. Robb (loading 0.11546, n=2,724)
10. *Holiday in Death (In Death, #7)* — J.D. Robb (loading 0.11525, n=3,625)
11. *Divided in Death (In Death, #18)* — J.D. Robb (loading 0.11511, n=2,704)
12. *Seduction in Death (In Death, #13)* — J.D. Robb (loading 0.11345, n=2,881)

### Mode 9 positive

1. *Fruits Basket, Vol. 11* — Natsuki Takaya (loading 0.07476, n=1,612)
2. *Fruits Basket, Vol. 5* — Natsuki Takaya (loading 0.07385, n=1,922)
3. *Fruits Basket, Vol. 12* — Natsuki Takaya (loading 0.07364, n=1,550)
4. *Fruits Basket, Vol. 9* — Natsuki Takaya (loading 0.07271, n=1,666)
5. *Fruits Basket, Vol. 8* — Natsuki Takaya (loading 0.07046, n=1,779)
6. *Fruits Basket, Vol. 17* — Natsuki Takaya (loading 0.06982, n=1,426)
7. *Fruits Basket, Vol. 7* — Natsuki Takaya (loading 0.06529, n=1,965)
8. *Fruits Basket, Vol. 18* — Natsuki Takaya (loading 0.06219, n=1,394)
9. *Fruits Basket, Vol. 10* — Natsuki Takaya (loading 0.06154, n=1,688)
10. *Fruits Basket, Vol. 13* — Natsuki Takaya (loading 0.06125, n=1,566)
11. *Fruits Basket, Vol. 16* — Natsuki Takaya (loading 0.06018, n=1,455)
12. *Fruits Basket, Vol. 4* — Natsuki Takaya (loading 0.05973, n=2,093)

### Mode 9 negative

1. *Skip Beat!, Vol. 06* — Yoshiki Nakamura (loading 0.20399, n=666)
2. *Skip Beat!, Vol. 13* — Yoshiki Nakamura (loading 0.20091, n=610)
3. *Skip Beat!, Vol. 12* — Yoshiki Nakamura (loading 0.19857, n=681)
4. *Skip Beat!, Vol. 16* — Yoshiki Nakamura (loading 0.19795, n=575)
5. *Skip Beat!, Vol. 14* — Yoshiki Nakamura (loading 0.19207, n=604)
6. *Skip Beat!, Vol. 03* — Yoshiki Nakamura (loading 0.18692, n=720)
7. *Skip Beat!, Vol. 02* — Yoshiki Nakamura (loading 0.18551, n=889)
8. *Skip Beat!, Vol. 05* — Yoshiki Nakamura (loading 0.17725, n=679)
9. *Skip Beat!, Vol. 08* — Yoshiki Nakamura (loading 0.17537, n=635)
10. *Skip Beat!, Vol. 10* — Yoshiki Nakamura (loading 0.17434, n=638)
11. *Skip Beat!, Vol. 09* — Yoshiki Nakamura (loading 0.17141, n=620)
12. *Skip Beat!, Vol. 17* — Yoshiki Nakamura (loading 0.15669, n=567)

### Mode 10 positive

1. *Portrait in Death (In Death, #16)* — J.D. Robb (loading 0.06211, n=3,196)
2. *Loyalty in Death (In Death, #9)* — J.D. Robb (loading 0.06159, n=3,184)
3. *Betrayal in Death (In Death, #12)* — J.D. Robb (loading 0.06006, n=3,000)
4. *Asterix and Caesar's Gift (Astérix #21)* — Rene Goscinny (loading 0.06006, n=785)
5. *Asterix and Cleopatra (Asterix, #6)* — Rene Goscinny (loading 0.05912, n=1,245)
6. *Reunion in Death (In Death, #14)* — J.D. Robb (loading 0.05818, n=2,740)
7. *Vengeance in Death (In Death, #6)* — J.D. Robb (loading 0.05765, n=3,896)
8. *Asterix the Legionary (Asterix, #10)* — Rene Goscinny (loading 0.05759, n=898)
9. *Asterix and the Golden Sickle (Asterix, #2)* — Rene Goscinny (loading 0.05725, n=1,036)
10. *Divided in Death (In Death, #18)* — J.D. Robb (loading 0.05715, n=2,704)
11. *Creation in Death (In Death, #25)* — J.D. Robb (loading 0.05656, n=2,472)
12. *Imitation in Death (In Death, #17)* — J.D. Robb (loading 0.05629, n=2,679)

### Mode 10 negative

1. *The Mark (Left Behind, #8)* — Tim LaHaye (loading 0.23952, n=2,227)
2. *Apollyon (Left Behind, #5)* — Tim LaHaye (loading 0.23647, n=2,496)
3. *The Indwelling (Left Behind, #7)* — Tim LaHaye (loading 0.23557, n=2,279)
4. *Soul Harvest: The World Takes Sides (Left Behind, #4)* — Tim LaHaye (loading 0.23303, n=2,725)
5. *Assassins (Left Behind, #6)* — Tim LaHaye (loading 0.22827, n=2,371)
6. *Desecration (Left Behind, #9)* — Tim LaHaye (loading 0.22313, n=2,019)
7. *The Remnant (Left Behind, #10)* — Tim LaHaye (loading 0.22224, n=1,911)
8. *Tribulation Force (Left Behind, #2)* — Tim LaHaye (loading 0.21298, n=3,360)
9. *Nicolae (Left Behind, #3)* — Tim LaHaye (loading 0.20258, n=3,066)
10. *Armageddon: The Cosmic Battle of the Ages (Left Behind, #11)* — Tim LaHaye (loading 0.18110, n=1,576)
11. *Glorious Appearing: The End of Days (Left Behind, #12)* — Tim LaHaye (loading 0.14490, n=1,286)
12. *Left Behind (Left Behind, #1)* — Tim LaHaye (loading 0.08367, n=10,047)

### Mode 11 positive

1. *Stay Out of the Basement  (Goosebumps, #2)* — R.L. Stine (loading 0.14894, n=1,611)
2. *Welcome to Camp Nightmare  (Goosebumps, #9)* — R.L. Stine (loading 0.13230, n=1,383)
3. *How I Got My Shrunken Head (Goosebumps, #39)* — R.L. Stine (loading 0.12901, n=772)
4. *It Came from Beneath the Sink! (Goosebumps, #30)* — R.L. Stine (loading 0.12405, n=835)
5. *Night of the Living Dummy (Goosebumps, #7)* — R.L. Stine (loading 0.11748, n=2,076)
6. *Return of the Mummy (Goosebumps, #23)* — R.L. Stine (loading 0.11670, n=610)
7. *The Haunted Mask (Goosebumps, #11)* — R.L. Stine (loading 0.11658, n=1,777)
8. *Night of the Living Dummy II (Goosebumps, #31)* — R.L. Stine (loading 0.11571, n=760)
9. *One Day at Horrorland (Goosebumps, #16)* — R.L. Stine (loading 0.11515, n=1,453)
10. *You Can't Scare Me! (Goosebumps #15)* — R.L. Stine (loading 0.11410, n=583)
11. *The Scarecrow Walks at Midnight (Goosebumps, #20)* — R.L. Stine (loading 0.11264, n=995)
12. *The Horror at Camp Jellyjam  (Goosebumps, #33)* — R.L. Stine (loading 0.11254, n=768)

### Mode 11 negative

1. *Asterix and Caesar's Gift (Astérix #21)* — Rene Goscinny (loading 0.10045, n=785)
2. *Asterix and Cleopatra (Asterix, #6)* — Rene Goscinny (loading 0.09804, n=1,245)
3. *Asterix the Legionary (Asterix, #10)* — Rene Goscinny (loading 0.09555, n=898)
4. *Asterix and the Golden Sickle (Asterix, #2)* — Rene Goscinny (loading 0.09238, n=1,036)
5. *Asterix at the Olympic Games (Asterix, #12)* — Rene Goscinny (loading 0.08447, n=919)
6. *Asterix in Belgium (Asterix, #24)* — Rene Goscinny (loading 0.08417, n=697)
7. *Asterix and the Cauldron (Asterix, #13)* — Rene Goscinny (loading 0.08394, n=711)
8. *Asterix and the Normans (Asterix, #9)* — Rene Goscinny (loading 0.08268, n=811)
9. *Asterix in Spain (Asterix, #14)* — Rene Goscinny (loading 0.08062, n=706)
10. *Obelix and Co. (Asterix, #23)* — Rene Goscinny (loading 0.07808, n=614)
11. *Asterix in Britain (Asterix, #8)* — Rene Goscinny (loading 0.07676, n=1,051)
12. *Asterix and the Laurel Wreath (Asterix, #18)* — Rene Goscinny (loading 0.07546, n=615)

### Mode 12 positive

1. *Asterix and Cleopatra (Asterix, #6)* — Rene Goscinny (loading 0.14708, n=1,245)
2. *Asterix and the Golden Sickle (Asterix, #2)* — Rene Goscinny (loading 0.14557, n=1,036)
3. *Asterix and Caesar's Gift (Astérix #21)* — Rene Goscinny (loading 0.14527, n=785)
4. *Asterix the Legionary (Asterix, #10)* — Rene Goscinny (loading 0.14367, n=898)
5. *Asterix at the Olympic Games (Asterix, #12)* — Rene Goscinny (loading 0.12051, n=919)
6. *Asterix and the Normans (Asterix, #9)* — Rene Goscinny (loading 0.12049, n=811)
7. *The Crab with the Golden Claws (Tintin, #9)* — Herge (loading 0.12008, n=1,397)
8. *Asterix and the Cauldron (Asterix, #13)* — Rene Goscinny (loading 0.11999, n=711)
9. *Asterix in Belgium (Asterix, #24)* — Rene Goscinny (loading 0.11885, n=697)
10. *Asterix in Spain (Asterix, #14)* — Rene Goscinny (loading 0.11737, n=706)
11. *Asterix in Britain (Asterix, #8)* — Rene Goscinny (loading 0.11135, n=1,051)
12. *Obelix and Co. (Asterix, #23)* — Rene Goscinny (loading 0.10917, n=614)

### Mode 12 negative

1. *Because I Said So (Because You Are Mine, #1.5)* — Beth Kery (loading 0.05636, n=651)
2. *The Letter of Marque (Aubrey/Maturin, #12)* — Patrick O'Brian (loading 0.05543, n=709)
3. *The Nutmeg of Consolation (Aubrey/Maturin, #14)* — Patrick O'Brian (loading 0.05502, n=597)
4. *Because I Could Not Resist (Because You Are Mine, #1.2)* — Beth Kery (loading 0.05477, n=727)
5. *Because You Must Learn (Because You Are Mine, #1.4)* — Beth Kery (loading 0.05348, n=701)
6. *Because You Haunt Me (Because You Are Mine, #1.3)* — Beth Kery (loading 0.05241, n=688)
7. *Because You Torment Me (Because You Are Mine, #1.6)* — Beth Kery (loading 0.05239, n=640)
8. *Post Captain (Aubrey/Maturin, #2)* — Patrick O'Brian (loading 0.05233, n=1,363)
9. *Because I Need To (Because You Are Mine, #1.7)* — Beth Kery (loading 0.05095, n=614)
10. *The Fortune of War* — Patrick O'Brian (loading 0.05078, n=897)
11. *Because I Am Yours (Because You Are Mine, #1.8)* — Beth Kery (loading 0.05017, n=609)
12. *The Far Side of the World* — Patrick O'Brian (loading 0.04967, n=777)

### Mode 13 positive

1. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (loading 0.04846, n=8,631)
2. *Proven Guilty (The Dresden Files, #8)* — Jim Butcher (loading 0.04732, n=10,347)
3. *Small Favor (The Dresden Files, #10)* — Jim Butcher (loading 0.04676, n=9,701)
4. *Asterix and the Golden Sickle (Asterix, #2)* — Rene Goscinny (loading 0.04645, n=1,036)
5. *White Night (The Dresden Files, #9)* — Jim Butcher (loading 0.04636, n=10,169)
6. *Asterix and Caesar's Gift (Astérix #21)* — Rene Goscinny (loading 0.04562, n=785)
7. *Stay Out of the Basement  (Goosebumps, #2)* — R.L. Stine (loading 0.04559, n=1,611)
8. *Asterix and Cleopatra (Asterix, #6)* — Rene Goscinny (loading 0.04527, n=1,245)
9. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (loading 0.04457, n=8,363)
10. *Asterix the Legionary (Asterix, #10)* — Rene Goscinny (loading 0.04404, n=898)
11. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (loading 0.04388, n=9,264)
12. *Magic Rises (Kate Daniels, #6)* — Ilona Andrews (loading 0.04321, n=5,526)

### Mode 13 negative

1. *Soul Harvest: The World Takes Sides (Left Behind, #4)* — Tim LaHaye (loading 0.11084, n=2,725)
2. *The Mark (Left Behind, #8)* — Tim LaHaye (loading 0.11042, n=2,227)
3. *Assassins (Left Behind, #6)* — Tim LaHaye (loading 0.10832, n=2,371)
4. *Apollyon (Left Behind, #5)* — Tim LaHaye (loading 0.10795, n=2,496)
5. *The Indwelling (Left Behind, #7)* — Tim LaHaye (loading 0.10643, n=2,279)
6. *Desecration (Left Behind, #9)* — Tim LaHaye (loading 0.10424, n=2,019)
7. *The Remnant (Left Behind, #10)* — Tim LaHaye (loading 0.10422, n=1,911)
8. *Tribulation Force (Left Behind, #2)* — Tim LaHaye (loading 0.09996, n=3,360)
9. *Nicolae (Left Behind, #3)* — Tim LaHaye (loading 0.09531, n=3,066)
10. *Skip Beat!, Vol. 06* — Yoshiki Nakamura (loading 0.09212, n=666)
11. *Portrait in Death (In Death, #16)* — J.D. Robb (loading 0.09131, n=3,196)
12. *Skip Beat!, Vol. 13* — Yoshiki Nakamura (loading 0.09108, n=610)

### Mode 14 positive

1. *The Letter of Marque (Aubrey/Maturin, #12)* — Patrick O'Brian (loading 0.18061, n=709)
2. *Post Captain (Aubrey/Maturin, #2)* — Patrick O'Brian (loading 0.17026, n=1,363)
3. *The Nutmeg of Consolation (Aubrey/Maturin, #14)* — Patrick O'Brian (loading 0.16835, n=597)
4. *The Fortune of War* — Patrick O'Brian (loading 0.16613, n=897)
5. *The Far Side of the World* — Patrick O'Brian (loading 0.16254, n=777)
6. *Treason's Harbour (Aubrey/Maturin, #9)* — Patrick O'Brian (loading 0.15773, n=739)
7. *The Surgeon's Mate* — Patrick O'Brian (loading 0.15354, n=811)
8. *The Reverse of the Medal (Aubrey/Maturin, #11)* — Patrick O'Brian (loading 0.15010, n=665)
9. *The Mauritius Command* — Patrick O'Brian (loading 0.14885, n=1,014)
10. *Blue at the Mizzen (Aubrey/Maturin, #20)* — Patrick O'Brian (loading 0.14087, n=526)
11. *Desolation Island* — Patrick O'Brian (loading 0.14052, n=941)
12. *H.M.S. Surprise* — Patrick O'Brian (loading 0.14017, n=1,185)

### Mode 14 negative

1. *The Last Command (Star Wars: The Thrawn Trilogy, #3)* — Timothy Zahn (loading 0.04280, n=4,164)
2. *Heir to the Empire (Star Wars: The Thrawn Trilogy #1)* — Timothy Zahn (loading 0.04134, n=6,148)
3. *Bumi Manusia* — Pramoedya Ananta Toer (loading 0.03423, n=2,052)
4. *Dark Force Rising (Star Wars: The Thrawn Trilogy, #2)* — Timothy Zahn (loading 0.03372, n=4,542)
5. *Found (Firstborn, #3)* — Karen Kingsbury (loading 0.02996, n=628)
6. *Jejak Langkah* — Pramoedya Ananta Toer (loading 0.02954, n=863)
7. *Forgiven (Firstborn, #2)* — Karen Kingsbury (loading 0.02947, n=646)
8. *Family (Firstborn, #4)* — Karen Kingsbury (loading 0.02893, n=570)
9. *Forever (Firstborn, #5)* — Karen Kingsbury (loading 0.02831, n=563)
10. *Asterix and Caesar's Gift (Astérix #21)* — Rene Goscinny (loading 0.02762, n=785)
11. *Return (Redemption, #3)* — Karen Kingsbury (loading 0.02706, n=877)
12. *Child of All Nations* — Pramoedya Ananta Toer (loading 0.02700, n=998)

### Mode 15 positive

1. *Five Go to Mystery Moor (Famous Five, #13)* — Enid Blyton (loading 0.17933, n=1,090)
2. *Five Go Adventuring Again (Famous Five, #2)* — Enid Blyton (loading 0.17225, n=1,623)
3. *Five Get Into Trouble (Famous Five, #8)* — Enid Blyton (loading 0.16492, n=1,238)
4. *Five Go Off to Camp (Famous Five, #7)* — Enid Blyton (loading 0.16091, n=1,146)
5. *Five Go to Billycock Hill (Famous Five, #16)* — Enid Blyton (loading 0.15277, n=878)
6. *Five on a Secret Trail (Famous Five, #15)* — Enid Blyton (loading 0.15272, n=941)
7. *Five on Kirrin Island Again (Famous Five, #6)* — Enid Blyton (loading 0.15106, n=1,504)
8. *Five Go Off in a Caravan (Famous Five, #5)* — Enid Blyton (loading 0.15088, n=1,445)
9. *Five Go to Smuggler's Top (Famous Five, #4)* — Enid Blyton (loading 0.14247, n=1,703)
10. *Five Go to Demon's Rocks (Famous Five, #19)* — Enid Blyton (loading 0.14121, n=1,002)
11. *Five Get into a Fix (Famous Five, #17)* — Enid Blyton (loading 0.13995, n=843)
12. *Five Are Together Again (Famous Five, #21)* — Enid Blyton (loading 0.13848, n=1,047)

### Mode 15 negative

1. *Assault at Selonia (Star Wars: The Corellian Trilogy, #2)* — Roger MacBride Allen (loading 0.08599, n=737)
2. *The Crystal Star* — Vonda N. McIntyre (loading 0.07997, n=798)
3. *Jedi Eclipse (Agents of Chaos, #2) (Star Wars: The New Jedi Order, #5)* — James Luceno (loading 0.07208, n=629)
4. *Hero's Trial (Star Wars: The New Jedi Order, #4)* — James Luceno (loading 0.07199, n=717)
5. *Tyrant's Test (Star Wars: The Black Fleet Crisis, #3)* — Michael P. Kube-McDowell (loading 0.07056, n=551)
6. *Dark Journey (Star Wars: The New Jedi Order, #10)* — Elaine Cunningham (loading 0.06785, n=700)
7. *Conquest (Edge of Victory, #1) (Star Wars: The New Jedi Order, #7)* — Greg Keyes (loading 0.06721, n=690)
8. *Children of the Jedi* — Barbara Hambly (loading 0.06719, n=869)
9. *Before the Storm (Star Wars: The Black Fleet Crisis, #1)* — Michael P. Kube-McDowell (loading 0.06666, n=631)
10. *Remnant (Force Heretic, #1) (Star Wars: The New Jedi Order, #15)* — Sean Williams (loading 0.06605, n=576)
11. *The New Rebellion* — Kristine Kathryn Rusch (loading 0.06562, n=645)
12. *Onslaught (Dark Tide, #1) (Star Wars: The New Jedi Order, #2)* — Michael A. Stackpole (loading 0.06534, n=923)

### Mode 16 positive

1. *Because I Said So (Because You Are Mine, #1.5)* — Beth Kery (loading 0.11427, n=651)
2. *Because I Could Not Resist (Because You Are Mine, #1.2)* — Beth Kery (loading 0.11074, n=727)
3. *Because You Must Learn (Because You Are Mine, #1.4)* — Beth Kery (loading 0.10814, n=701)
4. *Because You Torment Me (Because You Are Mine, #1.6)* — Beth Kery (loading 0.10426, n=640)
5. *Because I Need To (Because You Are Mine, #1.7)* — Beth Kery (loading 0.10381, n=614)
6. *Because You Haunt Me (Because You Are Mine, #1.3)* — Beth Kery (loading 0.10313, n=688)
7. *Because I Am Yours (Because You Are Mine, #1.8)* — Beth Kery (loading 0.09976, n=609)
8. *Because You Tempt Me (Because You Are Mine, #1.1)* — Beth Kery (loading 0.08987, n=1,030)
9. *Tarnished Gold (Landry, #5)* — V.C. Andrews (loading 0.07997, n=953)
10. *Midnight Whispers (Cutler #4)* — V.C. Andrews (loading 0.07355, n=1,112)
11. *Pearl in the Mist (Landry, #2)* — V.C. Andrews (loading 0.07301, n=1,289)
12. *Hidden Jewel (Landry, #4)* — V.C. Andrews (loading 0.07134, n=1,015)

### Mode 16 negative

1. *The Letter of Marque (Aubrey/Maturin, #12)* — Patrick O'Brian (loading 0.14274, n=709)
2. *The Nutmeg of Consolation (Aubrey/Maturin, #14)* — Patrick O'Brian (loading 0.13607, n=597)
3. *Post Captain (Aubrey/Maturin, #2)* — Patrick O'Brian (loading 0.13600, n=1,363)
4. *The Fortune of War* — Patrick O'Brian (loading 0.13109, n=897)
5. *The Far Side of the World* — Patrick O'Brian (loading 0.12807, n=777)
6. *Treason's Harbour (Aubrey/Maturin, #9)* — Patrick O'Brian (loading 0.12615, n=739)
7. *The Surgeon's Mate* — Patrick O'Brian (loading 0.12219, n=811)
8. *The Reverse of the Medal (Aubrey/Maturin, #11)* — Patrick O'Brian (loading 0.11837, n=665)
9. *The Mauritius Command* — Patrick O'Brian (loading 0.11726, n=1,014)
10. *Blue at the Mizzen (Aubrey/Maturin, #20)* — Patrick O'Brian (loading 0.11381, n=526)
11. *The Truelove* — Patrick O'Brian (loading 0.11138, n=562)
12. *The Commodore (Aubrey/Maturin, #17)* — Patrick O'Brian (loading 0.11088, n=567)

### Mode 17 positive

1. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.08336, n=2,629)
2. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.08292, n=2,236)
3. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.07978, n=2,179)
4. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.07391, n=2,253)
5. *The Sword Thief (The 39 Clues, #3)* — Peter Lerangis (loading 0.07303, n=2,811)
6. *Beyond the Grave (The 39 Clues #4)* — Jude Watson (loading 0.07157, n=2,479)
7. *In Too Deep (The 39 Clues, #6)* — Jude Watson (loading 0.07030, n=2,302)
8. *A King's Ransom (The 39 Clues: Cahills vs. Vespers, #2)* — Jude Watson (loading 0.06821, n=1,097)
9. *Into the Gauntlet (The 39 Clues, #10)* — Margaret Peterson Haddix (loading 0.06559, n=2,489)
10. *Vespers Rising (The 39 Clues, #11)* — Rick Riordan (loading 0.06318, n=1,700)
11. *One False Note (The 39 Clues, #2)* — Gordon Korman (loading 0.05901, n=3,070)
12. *Shatterproof (The 39 Clues: Cahills vs. Vespers, #4)* — Roland Smith (loading 0.05894, n=947)

### Mode 17 negative

1. *Dial L for Loser (The Clique, #6)* — Lisi Harrison (loading 0.22560, n=1,062)
2. *Best Friends for Never (The Clique, #2)* — Lisi Harrison (loading 0.21793, n=1,436)
3. *Invasion of the Boy Snatchers (The Clique, #4)* — Lisi Harrison (loading 0.21626, n=1,221)
4. *The Pretty Committee Strikes Back (The Clique, #5)* — Lisi Harrison (loading 0.21085, n=1,126)
5. *Sealed with a Diss (The Clique, #8)* — Lisi Harrison (loading 0.20351, n=958)
6. *Revenge of the Wannabes (The Clique, #3)* — Lisi Harrison (loading 0.20053, n=1,284)
7. *It's Not Easy Being Mean (The Clique, #7)* — Lisi Harrison (loading 0.19122, n=969)
8. *Bratfest at Tiffany's (The Clique, #9)* — Lisi Harrison (loading 0.18849, n=919)
9. *Boys "R" Us (The Clique, #11)* — Lisi Harrison (loading 0.16179, n=597)
10. *P.S. I Loathe You (The Clique, #10)* — Lisi Harrison (loading 0.15674, n=664)
11. *The Clique (The Clique, #1)* — Lisi Harrison (loading 0.15206, n=2,839)
12. *Massie (Clique Summer Collection, #1)* — Lisi Harrison (loading 0.08016, n=556)

### Mode 18 positive

1. *Dial L for Loser (The Clique, #6)* — Lisi Harrison (loading 0.09241, n=1,062)
2. *Best Friends for Never (The Clique, #2)* — Lisi Harrison (loading 0.08984, n=1,436)
3. *Invasion of the Boy Snatchers (The Clique, #4)* — Lisi Harrison (loading 0.08857, n=1,221)
4. *The Pretty Committee Strikes Back (The Clique, #5)* — Lisi Harrison (loading 0.08591, n=1,126)
5. *Revenge of the Wannabes (The Clique, #3)* — Lisi Harrison (loading 0.08529, n=1,284)
6. *Sealed with a Diss (The Clique, #8)* — Lisi Harrison (loading 0.08404, n=958)
7. *Tarnished Gold (Landry, #5)* — V.C. Andrews (loading 0.07986, n=953)
8. *It's Not Easy Being Mean (The Clique, #7)* — Lisi Harrison (loading 0.07835, n=969)
9. *Bratfest at Tiffany's (The Clique, #9)* — Lisi Harrison (loading 0.07679, n=919)
10. *Midnight Whispers (Cutler #4)* — V.C. Andrews (loading 0.07332, n=1,112)
11. *Pearl in the Mist (Landry, #2)* — V.C. Andrews (loading 0.07281, n=1,289)
12. *All That Glitters (Landry, #3)* — V.C. Andrews (loading 0.07255, n=1,210)

### Mode 18 negative

1. *Because I Said So (Because You Are Mine, #1.5)* — Beth Kery (loading 0.18998, n=651)
2. *Because I Could Not Resist (Because You Are Mine, #1.2)* — Beth Kery (loading 0.18612, n=727)
3. *Because You Haunt Me (Because You Are Mine, #1.3)* — Beth Kery (loading 0.18416, n=688)
4. *Because You Must Learn (Because You Are Mine, #1.4)* — Beth Kery (loading 0.18351, n=701)
5. *Because You Torment Me (Because You Are Mine, #1.6)* — Beth Kery (loading 0.17911, n=640)
6. *Because I Need To (Because You Are Mine, #1.7)* — Beth Kery (loading 0.17542, n=614)
7. *Because I Am Yours (Because You Are Mine, #1.8)* — Beth Kery (loading 0.16744, n=609)
8. *Because You Tempt Me (Because You Are Mine, #1.1)* — Beth Kery (loading 0.15415, n=1,030)
9. *Hot Six (Stephanie Plum, #6)* — Janet Evanovich (loading 0.05010, n=10,512)
10. *Hard Eight (Stephanie Plum, #8)* — Janet Evanovich (loading 0.04945, n=9,777)
11. *Eleven on Top (Stephanie Plum, #11)* — Janet Evanovich (loading 0.04900, n=8,954)
12. *Seven Up (Stephanie Plum, #7)* — Janet Evanovich (loading 0.04830, n=10,095)

### Mode 19 positive

1. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.05657, n=2,236)
2. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.05504, n=2,629)
3. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.05205, n=2,179)
4. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.04737, n=2,253)
5. *In Too Deep (The 39 Clues, #6)* — Jude Watson (loading 0.04632, n=2,302)
6. *A King's Ransom (The 39 Clues: Cahills vs. Vespers, #2)* — Jude Watson (loading 0.04529, n=1,097)
7. *The Sword Thief (The 39 Clues, #3)* — Peter Lerangis (loading 0.04479, n=2,811)
8. *Beyond the Grave (The 39 Clues #4)* — Jude Watson (loading 0.04442, n=2,479)
9. *Vespers Rising (The 39 Clues, #11)* — Rick Riordan (loading 0.04220, n=1,700)
10. *Five Go Adventuring Again (Famous Five, #2)* — Enid Blyton (loading 0.04198, n=1,623)
11. *Into the Gauntlet (The 39 Clues, #10)* — Margaret Peterson Haddix (loading 0.04143, n=2,489)
12. *Tarnished Gold (Landry, #5)* — V.C. Andrews (loading 0.04061, n=953)

### Mode 19 negative

1. *Because I Said So (Because You Are Mine, #1.5)* — Beth Kery (loading 0.16370, n=651)
2. *Because I Could Not Resist (Because You Are Mine, #1.2)* — Beth Kery (loading 0.15932, n=727)
3. *Because You Must Learn (Because You Are Mine, #1.4)* — Beth Kery (loading 0.15642, n=701)
4. *Because You Haunt Me (Because You Are Mine, #1.3)* — Beth Kery (loading 0.15290, n=688)
5. *Because You Torment Me (Because You Are Mine, #1.6)* — Beth Kery (loading 0.14940, n=640)
6. *Because I Need To (Because You Are Mine, #1.7)* — Beth Kery (loading 0.14817, n=614)
7. *Because I Am Yours (Because You Are Mine, #1.8)* — Beth Kery (loading 0.14249, n=609)
8. *Because You Tempt Me (Because You Are Mine, #1.1)* — Beth Kery (loading 0.12893, n=1,030)
9. *The Mystery at Lilac Inn (Nancy Drew, #4)* — Carolyn Keene (loading 0.09834, n=1,829)
10. *The Clue of the Broken Locket (Nancy Drew Mystery Stories, #11)* — Carolyn Keene (loading 0.09494, n=1,298)
11. *The Clue in the Diary (Nancy Drew, #7)* — Carolyn Keene (loading 0.09379, n=1,346)
12. *The Whispering Statue (Nancy Drew Mystery Stories, #14)* — Carolyn Keene (loading 0.09318, n=1,038)

### Mode 20 positive

1. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.12624, n=2,629)
2. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.12343, n=2,236)
3. *Hard Eight (Stephanie Plum, #8)* — Janet Evanovich (loading 0.11821, n=9,777)
4. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.11701, n=2,179)
5. *Eleven on Top (Stephanie Plum, #11)* — Janet Evanovich (loading 0.11602, n=8,954)
6. *To the Nines (Stephanie Plum, #9)* — Janet Evanovich (loading 0.11564, n=9,421)
7. *Seven Up (Stephanie Plum, #7)* — Janet Evanovich (loading 0.11459, n=10,095)
8. *High Five (Stephanie Plum, #5)* — Janet Evanovich (loading 0.11452, n=10,420)
9. *Hot Six (Stephanie Plum, #6)* — Janet Evanovich (loading 0.11372, n=10,512)
10. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.11006, n=2,253)
11. *Three to Get Deadly (Stephanie Plum, #3)* — Janet Evanovich (loading 0.10702, n=12,221)
12. *Ten Big Ones (Stephanie Plum, #10)* — Janet Evanovich (loading 0.10623, n=8,651)

### Mode 20 negative

1. *The Clue in the Diary (Nancy Drew, #7)* — Carolyn Keene (loading 0.05994, n=1,346)
2. *The Mystery at Lilac Inn (Nancy Drew, #4)* — Carolyn Keene (loading 0.05861, n=1,829)
3. *Password to Larkspur Lane (Nancy Drew, #10)* — Carolyn Keene (loading 0.05860, n=1,187)
4. *Nancy's Mysterious Letter (Nancy Drew, #8)* — Carolyn Keene (loading 0.05733, n=1,104)
5. *The Sign of the Twisted Candles (Nancy Drew, #9)* — Carolyn Keene (loading 0.05707, n=1,371)
6. *The Clue of the Broken Locket (Nancy Drew Mystery Stories, #11)* — Carolyn Keene (loading 0.05600, n=1,298)
7. *The Whispering Statue (Nancy Drew Mystery Stories, #14)* — Carolyn Keene (loading 0.05566, n=1,038)
8. *Mystery of the Ivory Charm (Nancy Drew Mystery Stories, #13)* — Carolyn Keene (loading 0.05414, n=824)
9. *The Clue in the Old Album (Nancy Drew Mystery Stories, #24)* — Carolyn Keene (loading 0.05332, n=652)
10. *The Invisible Intruder (Nancy Drew Mystery Stories, #46)* — Carolyn Keene (loading 0.05256, n=506)
11. *The Secret of Shadow Ranch (Nancy Drew, #5)* — Carolyn Keene (loading 0.05181, n=1,778)
12. *The Secret in the Old Attic (Nancy Drew, #21)* — Carolyn Keene (loading 0.05154, n=1,193)

### Mode 21 positive

1. *Because I Said So (Because You Are Mine, #1.5)* — Beth Kery (loading 0.06770, n=651)
2. *Because I Could Not Resist (Because You Are Mine, #1.2)* — Beth Kery (loading 0.06526, n=727)
3. *Because You Must Learn (Because You Are Mine, #1.4)* — Beth Kery (loading 0.06395, n=701)
4. *The Indwelling (Left Behind, #7)* — Tim LaHaye (loading 0.06189, n=2,279)
5. *Because I Need To (Because You Are Mine, #1.7)* — Beth Kery (loading 0.06164, n=614)
6. *Because You Torment Me (Because You Are Mine, #1.6)* — Beth Kery (loading 0.06053, n=640)
7. *The Remnant (Left Behind, #10)* — Tim LaHaye (loading 0.05961, n=1,911)
8. *The Mark (Left Behind, #8)* — Tim LaHaye (loading 0.05938, n=2,227)
9. *Apollyon (Left Behind, #5)* — Tim LaHaye (loading 0.05936, n=2,496)
10. *Desecration (Left Behind, #9)* — Tim LaHaye (loading 0.05913, n=2,019)
11. *Because You Haunt Me (Because You Are Mine, #1.3)* — Beth Kery (loading 0.05874, n=688)
12. *Because I Am Yours (Because You Are Mine, #1.8)* — Beth Kery (loading 0.05849, n=609)

### Mode 21 negative

1. *Found (Firstborn, #3)* — Karen Kingsbury (loading 0.16452, n=628)
2. *Forever (Firstborn, #5)* — Karen Kingsbury (loading 0.15949, n=563)
3. *Forgiven (Firstborn, #2)* — Karen Kingsbury (loading 0.15748, n=646)
4. *Family (Firstborn, #4)* — Karen Kingsbury (loading 0.14469, n=570)
5. *Return (Redemption, #3)* — Karen Kingsbury (loading 0.13850, n=877)
6. *Fame (Firstborn, #1)* — Karen Kingsbury (loading 0.13726, n=723)
7. *Rejoice (Redemption, #4)* — Karen Kingsbury (loading 0.13287, n=820)
8. *Reunion (Redemption, #5)* — Karen Kingsbury (loading 0.11429, n=816)
9. *Sunrise (Sunrise, #1)* — Karen Kingsbury (loading 0.10287, n=543)
10. *Redemption (Redemption, #1)* — Karen Kingsbury (loading 0.08675, n=1,442)
11. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.08132, n=2,629)
12. *Dial L for Loser (The Clique, #6)* — Lisi Harrison (loading 0.07817, n=1,062)

### Mode 22 positive

1. *Tarnished Gold (Landry, #5)* — V.C. Andrews (loading 0.13506, n=953)
2. *Pearl in the Mist (Landry, #2)* — V.C. Andrews (loading 0.12499, n=1,289)
3. *Midnight Whispers (Cutler #4)* — V.C. Andrews (loading 0.12226, n=1,112)
4. *Hidden Jewel (Landry, #4)* — V.C. Andrews (loading 0.12144, n=1,015)
5. *All That Glitters (Landry, #3)* — V.C. Andrews (loading 0.11995, n=1,210)
6. *Twilight's Child (Cutler #3)* — V.C. Andrews (loading 0.11782, n=1,218)
7. *Melody (Logan, #1)* — V.C. Andrews (loading 0.11554, n=1,137)
8. *Heart Song (Logan, #2)* — V.C. Andrews (loading 0.10540, n=900)
9. *Found (Firstborn, #3)* — Karen Kingsbury (loading 0.10408, n=628)
10. *Unfinished Symphony (Logan, #3)* — V.C. Andrews (loading 0.10351, n=884)
11. *Forgiven (Firstborn, #2)* — Karen Kingsbury (loading 0.10228, n=646)
12. *Raven (Orphans, #4)* — V.C. Andrews (loading 0.10170, n=689)

### Mode 22 negative

1. *One Night at the Call Center* — Chetan Bhagat (loading 0.05727, n=4,995)
2. *The 3 Mistakes of My Life* — Chetan Bhagat (loading 0.05625, n=5,706)
3. *Revolution 2020: Love, Corruption, Ambition* — Chetan Bhagat (loading 0.05352, n=4,283)
4. *2 States: The Story of My Marriage* — Chetan Bhagat (loading 0.04776, n=7,006)
5. *Five Point Someone* — Chetan Bhagat (loading 0.04423, n=7,107)
6. *Half Girlfriend* — Chetan Bhagat (loading 0.04102, n=2,279)
7. *Cinta Brontosaurus* — Raditya Dika (loading 0.03753, n=971)
8. *The Carnivorous Carnival (A Series of Unfortunate Events, #9)* — Lemony Snicket (loading 0.03701, n=9,975)
9. *The Miserable Mill (A Series of Unfortunate Events, #4)* — Lemony Snicket (loading 0.03694, n=13,482)
10. *The Austere Academy (A Series of Unfortunate Events, #5)* — Lemony Snicket (loading 0.03637, n=12,358)
11. *The Vile Village (A Series of Unfortunate Events, #7)* — Lemony Snicket (loading 0.03628, n=10,924)
12. *The Slippery Slope (A Series of Unfortunate Events, #10)* — Lemony Snicket (loading 0.03500, n=9,516)

### Mode 23 positive

1. *Found (Firstborn, #3)* — Karen Kingsbury (loading 0.14385, n=628)
2. *Forgiven (Firstborn, #2)* — Karen Kingsbury (loading 0.13809, n=646)
3. *Forever (Firstborn, #5)* — Karen Kingsbury (loading 0.13803, n=563)
4. *Family (Firstborn, #4)* — Karen Kingsbury (loading 0.13153, n=570)
5. *Return (Redemption, #3)* — Karen Kingsbury (loading 0.12485, n=877)
6. *Fame (Firstborn, #1)* — Karen Kingsbury (loading 0.11843, n=723)
7. *Rejoice (Redemption, #4)* — Karen Kingsbury (loading 0.11768, n=820)
8. *Reunion (Redemption, #5)* — Karen Kingsbury (loading 0.10573, n=816)
9. *Sunrise (Sunrise, #1)* — Karen Kingsbury (loading 0.09214, n=543)
10. *Redemption (Redemption, #1)* — Karen Kingsbury (loading 0.07604, n=1,442)
11. *Even Now (Lost Love, #1)* — Karen Kingsbury (loading 0.07336, n=1,120)
12. *Remember (Redemption, #2)* — Karen Kingsbury (loading 0.06661, n=1,096)

### Mode 23 negative

1. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.13588, n=2,629)
2. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.12934, n=2,179)
3. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.12916, n=2,236)
4. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.12127, n=2,253)
5. *In Too Deep (The 39 Clues, #6)* — Jude Watson (loading 0.11936, n=2,302)
6. *Beyond the Grave (The 39 Clues #4)* — Jude Watson (loading 0.11736, n=2,479)
7. *The Sword Thief (The 39 Clues, #3)* — Peter Lerangis (loading 0.11680, n=2,811)
8. *A King's Ransom (The 39 Clues: Cahills vs. Vespers, #2)* — Jude Watson (loading 0.10580, n=1,097)
9. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.10281, n=2,104)
10. *The Vampire Prince (Cirque Du Freak, #6)* — Darren Shan (loading 0.10215, n=2,389)
11. *Vespers Rising (The 39 Clues, #11)* — Rick Riordan (loading 0.10103, n=1,700)
12. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.10060, n=2,171)

### Mode 24 positive

1. *Hard Eight (Stephanie Plum, #8)* — Janet Evanovich (loading 0.13069, n=9,777)
2. *Seven Up (Stephanie Plum, #7)* — Janet Evanovich (loading 0.12768, n=10,095)
3. *To the Nines (Stephanie Plum, #9)* — Janet Evanovich (loading 0.12766, n=9,421)
4. *Eleven on Top (Stephanie Plum, #11)* — Janet Evanovich (loading 0.12735, n=8,954)
5. *High Five (Stephanie Plum, #5)* — Janet Evanovich (loading 0.12590, n=10,420)
6. *Hot Six (Stephanie Plum, #6)* — Janet Evanovich (loading 0.12484, n=10,512)
7. *Three to Get Deadly (Stephanie Plum, #3)* — Janet Evanovich (loading 0.12052, n=12,221)
8. *Ten Big Ones (Stephanie Plum, #10)* — Janet Evanovich (loading 0.11856, n=8,651)
9. *Four to Score (Stephanie Plum, #4)* — Janet Evanovich (loading 0.11627, n=11,390)
10. *Lean Mean Thirteen (Stephanie Plum, #13)* — Janet Evanovich (loading 0.11284, n=8,332)
11. *Twelve Sharp (Stephanie Plum, #12)* — Janet Evanovich (loading 0.11220, n=8,383)
12. *Two for the Dough (Stephanie Plum, #2)* — Janet Evanovich (loading 0.09777, n=13,494)

### Mode 24 negative

1. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.11053, n=2,104)
2. *The Vampire Prince (Cirque Du Freak, #6)* — Darren Shan (loading 0.10848, n=2,389)
3. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.10798, n=2,171)
4. *Killers of the Dawn (Cirque Du Freak, #9)* — Darren Shan (loading 0.10392, n=2,061)
5. *Trials of Death (Cirque Du Freak, #5)* — Darren Shan (loading 0.10329, n=2,494)
6. *Sons of Destiny (Cirque Du Freak, #12)* — Darren Shan (loading 0.10176, n=1,835)
7. *Vampire Mountain (Cirque Du Freak, #4)* — Darren Shan (loading 0.10131, n=2,715)
8. *Lord of the Shadows (Cirque Du Freak, #11)* — Darren Shan (loading 0.09872, n=1,894)
9. *The Vampire's Assistant* — Darren Shan (loading 0.09407, n=3,665)
10. *The Lake of Souls* — Darren Shan (loading 0.08628, n=1,962)
11. *Tunnels of Blood* — Darren Shan (loading 0.08587, n=3,043)
12. *A Living Nightmare (Cirque Du Freak, #1)* — Darren Shan (loading 0.07569, n=4,872)

### Mode 25 positive

1. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.12773, n=3,689)
2. *The Walking Dead, Vol. 06: This Sorrowful Life* — Robert Kirkman (loading 0.12689, n=3,073)
3. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.12670, n=3,307)
4. *The Walking Dead, Vol. 09: Here We Remain* — Robert Kirkman (loading 0.11902, n=2,570)
5. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (loading 0.11831, n=4,220)
6. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.11699, n=2,812)
7. *The Walking Dead, Vol. 12: Life Among Them* — Robert Kirkman (loading 0.11376, n=2,432)
8. *The Walking Dead, Vol. 10: What We Become* — Robert Kirkman (loading 0.11255, n=2,489)
9. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (loading 0.10871, n=3,061)
10. *The Walking Dead, Vol. 11: Fear the Hunters* — Robert Kirkman (loading 0.10869, n=2,374)
11. *The Walking Dead, Vol. 13: Too Far Gone* — Robert Kirkman (loading 0.10419, n=2,093)
12. *The Walking Dead, Vol. 02: Miles Behind Us* — Robert Kirkman (loading 0.10217, n=4,875)

### Mode 25 negative

1. *Sons of Destiny (Cirque Du Freak, #12)* — Darren Shan (loading 0.04524, n=1,835)
2. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.04458, n=2,104)
3. *Lord of the Shadows (Cirque Du Freak, #11)* — Darren Shan (loading 0.04435, n=1,894)
4. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.04425, n=2,171)
5. *Killers of the Dawn (Cirque Du Freak, #9)* — Darren Shan (loading 0.04371, n=2,061)
6. *Trials of Death (Cirque Du Freak, #5)* — Darren Shan (loading 0.04357, n=2,494)
7. *The Vampire Prince (Cirque Du Freak, #6)* — Darren Shan (loading 0.04341, n=2,389)
8. *Gerald's Game* — Stephen King (loading 0.04200, n=11,167)
9. *Bumi Manusia* — Pramoedya Ananta Toer (loading 0.04010, n=2,052)
10. *Dreamcatcher* — Stephen King (loading 0.03998, n=12,202)
11. *Vampire Mountain (Cirque Du Freak, #4)* — Darren Shan (loading 0.03957, n=2,715)
12. *The Predator (Animorphs, #5)* — Katherine Applegate (loading 0.03898, n=669)

### Mode 26 positive

1. *進撃の巨人 7 [Shingeki no Kyojin 7] (Attack on Titan, #7)* — Hajime Isayama (loading 0.08947, n=1,058)
2. *Attack on Titan, Vol. 11 (Attack on Titan, #11)* — Hajime Isayama (loading 0.08899, n=963)
3. *進撃の巨人 8 [Shingeki no Kyojin 8] (Attack on Titan, #8)* — Hajime Isayama (loading 0.08849, n=1,047)
4. *進撃の巨人 10 [Shingeki no Kyojin 10] (Attack on Titan, #10)* — Hajime Isayama (loading 0.08637, n=1,015)
5. *Attack on Titan, Vol. 6 (Attack on Titan, #6)* — Hajime Isayama (loading 0.08623, n=1,158)
6. *進撃の巨人 9 [Shingeki no Kyojin 9] (Attack on Titan, #9)* — Hajime Isayama (loading 0.08550, n=1,024)
7. *Golem in the Gears (Xanth, #9)* — Piers Anthony (loading 0.08092, n=1,431)
8. *Attack on Titan, Vol. 5 (Attack on Titan, #5)* — Hajime Isayama (loading 0.07818, n=1,248)
9. *Attack on Titan, Vol. 3 (Attack on Titan, #3)* — Hajime Isayama (loading 0.07754, n=1,557)
10. *Dragon on a Pedestal (Xanth, #7)* — Piers Anthony (loading 0.07428, n=1,527)
11. *Heaven Cent (Xanth #11)* — Piers Anthony (loading 0.07270, n=1,176)
12. *Night Mare (Xanth, #6)* — Piers Anthony (loading 0.07112, n=2,047)

### Mode 26 negative

1. *Sea of Swords (Forgotten Realms: Paths of Darkness, #4; Legend of Drizzt, #13)* — R.A. Salvatore (loading 0.13431, n=1,292)
2. *Passage to Dawn (Forgotten Realms: Legacy of the Drow, #4; Legend of Drizzt, #10)* — R.A. Salvatore (loading 0.12290, n=1,617)
3. *Siege of Darkness (Forgotten Realms: Legacy of the Drow, #3; Legend of Drizzt, #9)* — R.A. Salvatore (loading 0.11086, n=1,882)
4. *The Silent Blade (Forgotten Realms: Paths of Darkness, #1; Legend of Drizzt, #11)* — R.A. Salvatore (loading 0.10898, n=1,498)
5. *The Legacy (Forgotten Realms: Legacy of the Drow, #1; Legend of Drizzt, #7)* — R.A. Salvatore (loading 0.10581, n=2,191)
6. *The Lone Drow (Forgotten Realms: Hunter's Blades, #2; Legend of Drizzt, #15)* — R.A. Salvatore (loading 0.10304, n=1,354)
7. *Starless Night (Forgotten Realms: Legacy of the Drow, #2; Legend of Drizzt, #8)* — R.A. Salvatore (loading 0.10290, n=2,004)
8. *The Spine of the World (Forgotten Realms: Paths of Darkness, #2; Legend of Drizzt, #12)* — R.A. Salvatore (loading 0.10279, n=1,336)
9. *The Two Swords (Forgotten Realms: Hunter's Blades, #3; Legend of Drizzt, #16)* — R.A. Salvatore (loading 0.10204, n=1,259)
10. *Streams of Silver (Forgotten Realms: Icewind Dale, #2; Legend of Drizzt, #5)* — R.A. Salvatore (loading 0.09837, n=3,088)
11. *The Thousand Orcs (Forgotten Realms: Hunter's Blades, #1; Legend of Drizzt, #14)* — R.A. Salvatore (loading 0.08854, n=1,540)
12. *Canticle (Forgotten Realms: The Cleric Quintet, #1)* — R.A. Salvatore (loading 0.08741, n=873)

### Mode 27 positive

1. *Allies of the Night (Cirque du Freak, #8)* — Darren Shan (loading 0.13155, n=2,104)
2. *Hunters of the Dusk (Cirque Du Freak, #7)* — Darren Shan (loading 0.13114, n=2,171)
3. *The Vampire Prince (Cirque Du Freak, #6)* — Darren Shan (loading 0.13067, n=2,389)
4. *Sons of Destiny (Cirque Du Freak, #12)* — Darren Shan (loading 0.12461, n=1,835)
5. *Killers of the Dawn (Cirque Du Freak, #9)* — Darren Shan (loading 0.12432, n=2,061)
6. *Trials of Death (Cirque Du Freak, #5)* — Darren Shan (loading 0.11871, n=2,494)
7. *Lord of the Shadows (Cirque Du Freak, #11)* — Darren Shan (loading 0.11684, n=1,894)
8. *Vampire Mountain (Cirque Du Freak, #4)* — Darren Shan (loading 0.11561, n=2,715)
9. *The Vampire's Assistant* — Darren Shan (loading 0.11197, n=3,665)
10. *The Lake of Souls* — Darren Shan (loading 0.10079, n=1,962)
11. *Tunnels of Blood* — Darren Shan (loading 0.09959, n=3,043)
12. *A Living Nightmare (Cirque Du Freak, #1)* — Darren Shan (loading 0.08256, n=4,872)

### Mode 27 negative

1. *Bleach, Volume 25* — Tite Kubo (loading 0.07838, n=530)
2. *Bleach, Volume 17* — Tite Kubo (loading 0.07601, n=672)
3. *Bleach, Volume 05* — Tite Kubo (loading 0.07522, n=934)
4. *The Black Circle (The 39 Clues, #5)* — Patrick Carman (loading 0.07340, n=2,629)
5. *The Emperor's Code (The 39 Clues, #8)* — Gordon Korman (loading 0.07262, n=2,179)
6. *Bleach, Volume 02* — Tite Kubo (loading 0.07140, n=1,330)
7. *Storm Warning (The 39 Clues, #9)* — Linda Sue Park (loading 0.06981, n=2,236)
8. *Bleach, Volume 22* — Tite Kubo (loading 0.06946, n=616)
9. *Bleach, Volume 14* — Tite Kubo (loading 0.06942, n=815)
10. *The Viper's Nest (39 Clues, #7)* — Peter Lerangis (loading 0.06823, n=2,253)
11. *Perfect (Pretty Little Liars, #3)* — Sara Shepard (loading 0.06737, n=6,650)
12. *Bleach, Volume 07* — Tite Kubo (loading 0.06647, n=924)

### Mode 28 positive

1. *Bumi Manusia* — Pramoedya Ananta Toer (loading 0.07092, n=2,052)
2. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (loading 0.05760, n=183,770)
3. *The Color of Her Panties (Xanth #15)* — Piers Anthony (loading 0.05756, n=887)
4. *Golem in the Gears (Xanth, #9)* — Piers Anthony (loading 0.05672, n=1,431)
5. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (loading 0.05417, n=174,713)
6. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (loading 0.05404, n=192,417)
7. *Heaven Cent (Xanth #11)* — Piers Anthony (loading 0.05400, n=1,176)
8. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (loading 0.05283, n=178,374)
9. *Jejak Langkah* — Pramoedya Ananta Toer (loading 0.05266, n=863)
10. *Night Mare (Xanth, #6)* — Piers Anthony (loading 0.05237, n=2,047)
11. *Child of All Nations* — Pramoedya Ananta Toer (loading 0.05213, n=998)
12. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (loading 0.05090, n=177,929)

### Mode 28 negative

1. *I Like It Like That (Gossip Girl, #5)* — Cecily von Ziegesar (loading 0.11890, n=1,725)
2. *Because I'm Worth It (Gossip Girl, #4)* — Cecily von Ziegesar (loading 0.11561, n=2,014)
3. *Nobody Does it Better (Gossip Girl, #7)* — Cecily von Ziegesar (loading 0.11410, n=1,454)
4. *You're the One That I Want (Gossip Girl, #6)* — Cecily von Ziegesar (loading 0.11398, n=1,948)
5. *All I Want is Everything (Gossip Girl, #3)* — Cecily von Ziegesar (loading 0.11249, n=2,315)
6. *Only in Your Dreams (Gossip Girl, #9)* — Cecily von Ziegesar (loading 0.10510, n=1,172)
7. *Nothing Can Keep Us Together (Gossip Girl, #8)* — Cecily von Ziegesar (loading 0.10465, n=1,299)
8. *進撃の巨人 7 [Shingeki no Kyojin 7] (Attack on Titan, #7)* — Hajime Isayama (loading 0.09643, n=1,058)
9. *You Know You Love Me (Gossip Girl, #2)* — Cecily von Ziegesar (loading 0.09468, n=2,864)
10. *Would I Lie to You (Gossip Girl, #10)* — Cecily von Ziegesar (loading 0.09310, n=1,060)
11. *進撃の巨人 9 [Shingeki no Kyojin 9] (Attack on Titan, #9)* — Hajime Isayama (loading 0.09291, n=1,024)
12. *Don't You Forget About Me (Gossip Girl, #11)* — Cecily von Ziegesar (loading 0.09262, n=990)

### Mode 29 positive

1. *Agatha Raisin and the Wellspring of Death (Agatha Raisin, #7)* — M.C. Beaton (loading 0.08680, n=706)
2. *Agatha Raisin and the Wizard of Evesham (Agatha Raisin, #8)* — M.C. Beaton (loading 0.08325, n=737)
3. *The Ersatz Elevator (A Series of Unfortunate Events, #6)* — Lemony Snicket (loading 0.07629, n=11,509)
4. *The Austere Academy (A Series of Unfortunate Events, #5)* — Lemony Snicket (loading 0.07606, n=12,358)
5. *Agatha Raisin and the Murderous Marriage (Agatha Raisin, #5)* — M.C. Beaton (loading 0.07542, n=901)
6. *The Slippery Slope (A Series of Unfortunate Events, #10)* — Lemony Snicket (loading 0.07525, n=9,516)
7. *Agatha Raisin and the Walkers of Dembley (Agatha Raisin, #4)* — M.C. Beaton (loading 0.07308, n=949)
8. *The Vile Village (A Series of Unfortunate Events, #7)* — Lemony Snicket (loading 0.07305, n=10,924)
9. *The Hostile Hospital (A Series of Unfortunate Events, #8)* — Lemony Snicket (loading 0.07289, n=9,099)
10. *Agatha Raisin and the Case of the Curious Curate (Agatha Raisin, #13)* — M.C. Beaton (loading 0.07240, n=591)
11. *The Miserable Mill (A Series of Unfortunate Events, #4)* — Lemony Snicket (loading 0.07229, n=13,482)
12. *Agatha Raisin and the Fairies of Fryfam (Agatha Raisin, #10)* — M.C. Beaton (loading 0.07174, n=701)

### Mode 29 negative

1. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (loading 0.10249, n=1,439)
2. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (loading 0.10230, n=1,672)
3. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (loading 0.10109, n=1,656)
4. *Weirdos from Another Planet!: A Calvin and Hobbes Collection* — Bill Watterson (loading 0.10087, n=1,195)
5. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (loading 0.10065, n=1,335)
6. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (loading 0.09954, n=1,184)
7. *Yukon Ho!* — Bill Watterson (loading 0.09764, n=1,178)
8. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (loading 0.09738, n=1,986)
9. *The Revenge of the Baby-Sat* — Bill Watterson (loading 0.09341, n=1,290)
10. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (loading 0.08905, n=1,241)
11. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (loading 0.08809, n=1,902)
12. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (loading 0.08208, n=1,667)

### Mode 30 positive

1. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.06888, n=3,307)
2. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.06867, n=3,689)
3. *The Walking Dead, Vol. 06: This Sorrowful Life* — Robert Kirkman (loading 0.06638, n=3,073)
4. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (loading 0.06454, n=4,220)
5. *Agatha Raisin and the Wellspring of Death (Agatha Raisin, #7)* — M.C. Beaton (loading 0.06215, n=706)
6. *Agatha Raisin and the Wizard of Evesham (Agatha Raisin, #8)* — M.C. Beaton (loading 0.05991, n=737)
7. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.05798, n=2,812)
8. *Agatha Raisin and the Walkers of Dembley (Agatha Raisin, #4)* — M.C. Beaton (loading 0.05573, n=949)
9. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (loading 0.05431, n=3,061)
10. *Agatha Raisin and the Fairies of Fryfam (Agatha Raisin, #10)* — M.C. Beaton (loading 0.05372, n=701)
11. *Best Friends* — Jacqueline Wilson (loading 0.05362, n=648)
12. *The Walking Dead, Vol. 09: Here We Remain* — Robert Kirkman (loading 0.05212, n=2,570)

### Mode 30 negative

1. *Cerulean Sins (Anita Blake, Vampire Hunter, #11)* — Laurell K. Hamilton (loading 0.09017, n=7,162)
2. *Incubus Dreams (Anita Blake, Vampire Hunter, #12)* — Laurell K. Hamilton (loading 0.08914, n=6,847)
3. *Danse Macabre (Anita Blake, Vampire Hunter, #14)* — Laurell K. Hamilton (loading 0.08809, n=6,397)
4. *The Harlequin (Anita Blake, Vampire Hunter #15)* — Laurell K. Hamilton (loading 0.08315, n=6,131)
5. *One Piece, Volume 07: The Crap-Geezer (One Piece, #7)* — Eiichiro Oda (loading 0.07995, n=595)
6. *Blood Noir (Anita Blake, Vampire Hunter #16)* — Laurell K. Hamilton (loading 0.07946, n=5,520)
7. *Burnt Offerings (Anita Blake, Vampire Hunter, #7)* — Laurell K. Hamilton (loading 0.07811, n=8,954)
8. *One Piece, Volume 04: The Black Cat Pirates (One Piece, #4)* — Eiichiro Oda (loading 0.07753, n=692)
9. *Narcissus in Chains (Anita Blake, Vampire Hunter, #10)* — Laurell K. Hamilton (loading 0.07376, n=7,909)
10. *The Killing Dance (Anita Blake, Vampire Hunter, #6)* — Laurell K. Hamilton (loading 0.07364, n=9,342)
11. *Micah (Anita Blake, Vampire Hunter, #13)* — Laurell K. Hamilton (loading 0.07161, n=6,328)
12. *Skin Trade (Anita Blake, Vampire Hunter #17)* — Laurell K. Hamilton (loading 0.07126, n=5,095)

### Mode 31 positive

1. *Death Note, Vol. 8: Target (Death Note, #8)* — Tsugumi Ohba (loading 0.07151, n=2,090)
2. *Bumi Manusia* — Pramoedya Ananta Toer (loading 0.07075, n=2,052)
3. *Death Note, Vol. 4: Love (Death Note, #4)* — Tsugumi Ohba (loading 0.06792, n=2,846)
4. *Death Note, Vol. 9: Contact (Death Note, #9)* — Tsugumi Ohba (loading 0.06634, n=1,844)
5. *Death Note, Vol. 5: Whiteout (Death Note, #5)* — Tsugumi Ohba (loading 0.06608, n=2,573)
6. *Death Note, Vol. 7: Zero (Death Note, #7)* — Tsugumi Ohba (loading 0.06359, n=2,189)
7. *The Carnivorous Carnival (A Series of Unfortunate Events, #9)* — Lemony Snicket (loading 0.06308, n=9,975)
8. *The Austere Academy (A Series of Unfortunate Events, #5)* — Lemony Snicket (loading 0.06179, n=12,358)
9. *The Miserable Mill (A Series of Unfortunate Events, #4)* — Lemony Snicket (loading 0.06163, n=13,482)
10. *Death Note, Vol. 10: Deletion (Death Note, #10)* — Tsugumi Ohba (loading 0.06154, n=1,726)
11. *Death Note, Vol. 11: Kindred Spirits (Death Note, #11)* — Tsugumi Ohba (loading 0.06123, n=1,674)
12. *The Slippery Slope (A Series of Unfortunate Events, #10)* — Lemony Snicket (loading 0.06086, n=9,516)

### Mode 31 negative

1. *Black Butler, Vol. 5 (Black Butler, #5)* — Yana Toboso (loading 0.06484, n=915)
2. *Black Butler, Vol. 3 (Black Butler, #3)* — Yana Toboso (loading 0.06394, n=1,371)
3. *Black Butler, Vol. 6 (Black Butler, #6)* — Yana Toboso (loading 0.06193, n=867)
4. *Black Butler, Vol. 7 (Black Butler, #7)* — Yana Toboso (loading 0.05792, n=782)
5. *Black Butler, Vol. 10 (Black Butler, #10)* — Yana Toboso (loading 0.05709, n=613)
6. *Black Butler, Vol. 8 (Black Butler, #8)* — Yana Toboso (loading 0.05651, n=696)
7. *Black Butler, Vol. 2 (Black Butler, #2)* — Yana Toboso (loading 0.05639, n=1,467)
8. *Bleach, Volume 17* — Tite Kubo (loading 0.05545, n=672)
9. *Bleach, Volume 25* — Tite Kubo (loading 0.05420, n=530)
10. *Cinta Brontosaurus* — Raditya Dika (loading 0.05265, n=971)
11. *Eleven on Top (Stephanie Plum, #11)* — Janet Evanovich (loading 0.05256, n=8,954)
12. *Black Butler, Vol. 12 (Black Butler, #12)* — Yana Toboso (loading 0.05213, n=579)

### Mode 32 positive

1. *The Walking Dead, Vol. 04: The Heart's Desire* — Robert Kirkman (loading 0.10539, n=3,689)
2. *The Walking Dead, Vol. 05: The Best Defense* — Robert Kirkman (loading 0.10483, n=3,307)
3. *The Walking Dead, Vol. 06: This Sorrowful Life* — Robert Kirkman (loading 0.10075, n=3,073)
4. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (loading 0.09539, n=4,220)
5. *The Walking Dead, Vol. 09: Here We Remain* — Robert Kirkman (loading 0.09360, n=2,570)
6. *The Walking Dead, Vol. 07: The Calm Before* — Robert Kirkman (loading 0.09328, n=2,812)
7. *The Walking Dead, Vol. 12: Life Among Them* — Robert Kirkman (loading 0.08920, n=2,432)
8. *The Walking Dead, Vol. 10: What We Become* — Robert Kirkman (loading 0.08901, n=2,489)
9. *The Walking Dead, Vol. 08: Made to Suffer* — Robert Kirkman (loading 0.08673, n=3,061)
10. *The Walking Dead, Vol. 11: Fear the Hunters* — Robert Kirkman (loading 0.08506, n=2,374)
11. *The Walking Dead, Vol. 13: Too Far Gone* — Robert Kirkman (loading 0.08483, n=2,093)
12. *The Walking Dead, Vol. 02: Miles Behind Us* — Robert Kirkman (loading 0.08045, n=4,875)

### Mode 32 negative

1. *Bumi Manusia* — Pramoedya Ananta Toer (loading 0.10694, n=2,052)
2. *Child of All Nations* — Pramoedya Ananta Toer (loading 0.08616, n=998)
3. *Jejak Langkah* — Pramoedya Ananta Toer (loading 0.08552, n=863)
4. *Agatha Raisin and the Wellspring of Death (Agatha Raisin, #7)* — M.C. Beaton (loading 0.07774, n=706)
5. *Agatha Raisin and the Wizard of Evesham (Agatha Raisin, #8)* — M.C. Beaton (loading 0.07325, n=737)
6. *Agatha Raisin and the Murderous Marriage (Agatha Raisin, #5)* — M.C. Beaton (loading 0.06951, n=901)
7. *Agatha Raisin and the Walkers of Dembley (Agatha Raisin, #4)* — M.C. Beaton (loading 0.06620, n=949)
8. *Agatha Raisin and the Fairies of Fryfam (Agatha Raisin, #10)* — M.C. Beaton (loading 0.06587, n=701)
9. *Agatha Raisin and the Case of the Curious Curate (Agatha Raisin, #13)* — M.C. Beaton (loading 0.06335, n=591)
10. *Agatha Raisin and the Potted Gardener (Agatha Raisin, #3)* — M.C. Beaton (loading 0.06327, n=1,087)
11. *The Green Mile, Part 4: The Bad Death of Eduard Delacroix* — Stephen King (loading 0.06090, n=1,625)
12. *Agatha Raisin and the Witch of Wyckhadden (Agatha Raisin, #9)* — M.C. Beaton (loading 0.06028, n=684)

## Interpretation rule

A mode is structurally credible only if it exceeds the shuffled spectrum and aligns across both disjoint-reader halves. Literary overlap is descriptive post-hoc evidence, not part of mode fitting, orientation, ordering, or acceptance. If literary books appear only in unstable or null-sized modes, the ratings matrix does not support a naturally identifiable single literary axis under this operator.

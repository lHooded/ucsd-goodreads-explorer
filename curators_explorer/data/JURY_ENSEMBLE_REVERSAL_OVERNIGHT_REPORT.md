# Ensemble convergence-reversal of random juries

Each random jury is iterated through the standard map (stage 0 collapses to the Goodreads center), then gain-hard convergence reversal prunes the strongest proponents of the converged direction and restarts from the same jury seed. This report asks whether the reversed endpoints of many random juries, taken together, point at a literary center. Literary scoring is done in preference space after all directions, preferences, aggregates, and clusters are frozen; endpoint directions feed only the pairwise-agreement statistic, and the basin census clusters preference scores.

Sizes: **[2000, 5000, 10000, 20000]**; juries per size: **300**; runtime: **3864.2s**. Chance @50: exact 0.10, broad 0.80, anti 6.17.

## Jury size 2,000 (300 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.087, median 0.092 (min 0.008, max 0.145). Stop reasons: {'evidence_floor': 300}; median deepest users 14,061.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 14/14 |
| plain_mean | 0/0 | 0/0 | 27/27 |
| coordinate_median | 0/0 | 0/0 | 28/28 |
| agreement_consensus | 0/0 | 0/0 | 25/25 |
| mean_displacement | 0/0 | 0/0 | 5/5 |
| big_jury_control (n=116,635) | 0/0 | 0/0 | 10/10 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 0.11, median 0, max 2; broad_lit: mean 0.76, max 6; anti: mean 19.26. 0/300 juries reach exact_lit50 >= 3; 6/300 reach broad_lit50 >= 5.

### Basin census (clustered endpoint preference scores)

Preference-correlation threshold 0.3; 2 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 268 | 0 | 0 | 25 |
| 2 | 32 | 0 | 0 | 31 |

#### Basin 1 (268 juries) head

1. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.707)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.691)
3. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.691)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.688)
5. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.661)
6. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.651)
7. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.649)
8. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.636)
9. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.634)
10. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.631)

#### Basin 2 (32 juries) head

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.766)
2. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.734)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.732)
4. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.711)
5. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.708)
6. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.705)
7. *Rock Chick Regret (Rock Chick, #7)* — Kristen Ashley (0.693)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.685)
9. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.680)
10. *The Golden Dynasty (Fantasyland, #2)* — Kristen Ashley (0.661)

### Aggregate heads

#### center_stage0

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.907)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.894)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.892)
4. *March: Book Two (March, #2)* — John             Lewis (0.892)
5. *The Hate U Give* — Angie Thomas (0.888)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.851)
7. *March: Book Three (March, #3)* — John             Lewis (0.849)
8. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.844)
9. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.839)
10. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.837)
11. *Calvin and Hobbes* — Bill Watterson (0.830)
12. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.829)

#### agreement_consensus

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (18.202)
2. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (18.084)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (17.967)
4. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (17.241)
5. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (16.770)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (16.719)
7. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (16.552)
8. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (16.523)
9. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (16.248)
10. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (16.225)
11. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (16.027)
12. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (16.008)

#### plain_mean

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.699)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.693)
3. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.691)
4. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.673)
5. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.646)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.644)
7. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.639)
8. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.635)
9. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.631)
10. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.622)
11. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.622)
12. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.619)

#### mean_displacement

1. *Emma (The Austen Project, #3)* — Alexander McCall Smith (0.691)
2. *Primates of Park Avenue* — Wednesday Martin (0.680)
3. *The Three Weissmanns of Westport* — Cathleen Schine (0.679)
4. *Among the Ten Thousand Things* — Julia Pierpont (0.675)
5. *After Alice* — Gregory Maguire (0.675)
6. *Palo Alto* — James Franco (0.674)
7. *Citizen Girl* — Emma McLaughlin (0.652)
8. *The Red House* — Mark Haddon (0.648)
9. *Sweet Valley Confidential: Ten Years Later* — Francine Pascal (0.644)
10. *Shopaholic on Honeymoon (Shopaholic #3.5)* — Sophie Kinsella (0.642)
11. *It's Not Okay: Turning Heartbreak Into Happily Never After* — Andi Dorfman (0.639)
12. *Oroonoko* — Aphra Behn (0.639)

## Jury size 5,000 (300 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.164, median 0.161 (min 0.020, max 0.218). Stop reasons: {'evidence_floor': 300}; median deepest users 15,136.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 14/14 |
| plain_mean | 0/0 | 0/0 | 26/26 |
| coordinate_median | 0/0 | 0/0 | 25/25 |
| agreement_consensus | 0/0 | 0/0 | 26/26 |
| mean_displacement | 0/0 | 0/0 | 8/8 |
| big_jury_control (n=116,635) | 0/0 | 0/0 | 26/26 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 0.13, median 0, max 4; broad_lit: mean 0.22, max 9; anti: mean 24.10. 5/300 juries reach exact_lit50 >= 3; 2/300 reach broad_lit50 >= 5.

### Basin census (clustered endpoint preference scores)

Preference-correlation threshold 0.3; 1 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 300 | 0 | 0 | 26 |

#### Basin 1 (300 juries) head

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.772)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.759)
3. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.745)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.732)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.724)
6. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.709)
7. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.705)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.697)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.694)
10. *The Hate U Give* — Angie Thomas (0.686)

### Aggregate heads

#### center_stage0

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.908)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.892)
3. *March: Book Two (March, #2)* — John             Lewis (0.891)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.888)
5. *The Hate U Give* — Angie Thomas (0.886)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.858)
7. *March: Book Three (March, #3)* — John             Lewis (0.850)
8. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.844)
9. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.835)
10. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.830)
11. *Calvin and Hobbes* — Bill Watterson (0.827)
12. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.825)

#### agreement_consensus

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (37.737)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (37.562)
3. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (36.931)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (36.240)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (35.463)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (34.983)
7. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (34.592)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (34.572)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (34.434)
10. *The Hate U Give* — Angie Thomas (33.902)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (33.191)
12. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (33.069)

#### plain_mean

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.772)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.759)
3. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.745)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.732)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.724)
6. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.709)
7. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.705)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.697)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.694)
10. *The Hate U Give* — Angie Thomas (0.686)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.678)
12. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.675)

#### mean_displacement

1. *The Three Weissmanns of Westport* — Cathleen Schine (0.605)
2. *One Indian Girl* — Chetan Bhagat (0.596)
3. *Emma (The Austen Project, #3)* — Alexander McCall Smith (0.596)
4. *The Front (Winston Garano, #2)* — Patricia Cornwell (0.588)
5. *Primates of Park Avenue* — Wednesday Martin (0.585)
6. *Citizen Girl* — Emma McLaughlin (0.583)
7. *This One is Mine* — Maria Semple (0.578)
8. *Among the Ten Thousand Things* — Julia Pierpont (0.577)
9. *Season of the Machete* — James Patterson (0.577)
10. *Nanny Returns (Nanny, #2)* — Emma McLaughlin (0.572)
11. *The Birthing House* — Christopher Ransom (0.571)
12. *Shopaholic on Honeymoon (Shopaholic #3.5)* — Sophie Kinsella (0.569)

## Jury size 10,000 (300 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.199, median 0.214 (min -0.038, max 0.296). Stop reasons: {'evidence_floor': 300}; median deepest users 17,518.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 14/14 |
| plain_mean | 0/0 | 0/0 | 25/25 |
| coordinate_median | 0/0 | 0/0 | 24/24 |
| agreement_consensus | 0/0 | 0/0 | 23/23 |
| mean_displacement | 0/0 | 0/0 | 9/9 |
| big_jury_control (n=116,635) | 0/0 | 0/0 | 23/23 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 0.14, median 0, max 1; broad_lit: mean 0.14, max 1; anti: mean 23.77. 0/300 juries reach exact_lit50 >= 3; 0/300 reach broad_lit50 >= 5.

### Basin census (clustered endpoint preference scores)

Preference-correlation threshold 0.3; 1 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 300 | 0 | 0 | 25 |

#### Basin 1 (300 juries) head

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.810)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.802)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.786)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.779)
5. *The Hate U Give* — Angie Thomas (0.771)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.767)
7. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.766)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.765)
9. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.745)
10. *The Nightingale* — Kristin Hannah (0.725)

### Aggregate heads

#### center_stage0

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.909)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.892)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.889)
4. *March: Book Two (March, #2)* — John             Lewis (0.887)
5. *The Hate U Give* — Angie Thomas (0.885)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.848)
7. *March: Book Three (March, #3)* — John             Lewis (0.843)
8. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.841)
9. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.835)
10. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.831)
11. *Calvin and Hobbes* — Bill Watterson (0.825)
12. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.825)

#### agreement_consensus

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (48.339)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (47.880)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (46.966)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (46.303)
5. *The Hate U Give* — Angie Thomas (46.028)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (45.806)
7. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (45.735)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (45.707)
9. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (44.601)
10. *The Nightingale* — Kristin Hannah (43.304)
11. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (42.518)
12. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (42.490)

#### plain_mean

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.810)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.802)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.786)
4. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.779)
5. *The Hate U Give* — Angie Thomas (0.771)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.767)
7. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.766)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.765)
9. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.745)
10. *The Nightingale* — Kristin Hannah (0.725)
11. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.714)
12. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.711)

#### mean_displacement

1. *One Indian Girl* — Chetan Bhagat (0.558)
2. *The Juliette Society (The Juliette Society, #1)* — Sasha Grey (0.532)
3. *Season of the Machete* — James Patterson (0.532)
4. *The Birthing House* — Christopher Ransom (0.531)
5. *The Front (Winston Garano, #2)* — Patricia Cornwell (0.526)
6. *Shopaholic on Honeymoon (Shopaholic #3.5)* — Sophie Kinsella (0.520)
7. *Steamed* — Katie MacAlister (0.517)
8. *Citizen Girl* — Emma McLaughlin (0.512)
9. *If I Did It: Confessions of the Killer* — O.J. Simpson (0.509)
10. *DEAD[ish] (DEAD[ish] #1)* — Naomi Kramer (0.508)
11. *The Three Weissmanns of Westport* — Cathleen Schine (0.506)
12. *A Desirable Residence* — Madeleine Wickham (0.506)

## Jury size 20,000 (300 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.268, median 0.290 (min -0.062, max 0.345). Stop reasons: {'evidence_floor': 300}; median deepest users 16,109.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 14/14 |
| plain_mean | 0/0 | 0/0 | 27/27 |
| coordinate_median | 0/0 | 0/0 | 33/33 |
| agreement_consensus | 0/0 | 0/0 | 28/28 |
| mean_displacement | 0/0 | 0/0 | 8/8 |
| big_jury_control (n=116,635) | 0/0 | 0/0 | 7/7 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 1.56, median 0, max 9; broad_lit: mean 2.33, max 15; anti: mean 26.39. 98/300 juries reach exact_lit50 >= 3; 86/300 reach broad_lit50 >= 5.

### Basin census (clustered endpoint preference scores)

Preference-correlation threshold 0.3; 1 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 300 | 0 | 0 | 27 |

#### Basin 1 (300 juries) head

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.792)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.783)
3. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.742)
4. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.742)
5. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.738)
6. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.716)
7. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.714)
8. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.678)
9. *The Hate U Give* — Angie Thomas (0.671)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.661)

### Aggregate heads

#### center_stage0

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.912)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.892)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.890)
4. *March: Book Two (March, #2)* — John             Lewis (0.886)
5. *The Hate U Give* — Angie Thomas (0.886)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.845)
7. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.842)
8. *March: Book Three (March, #3)* — John             Lewis (0.841)
9. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.837)
10. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.833)
11. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.827)
12. *Calvin and Hobbes* — Bill Watterson (0.827)

#### agreement_consensus

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (63.855)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (63.346)
3. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (59.987)
4. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (59.836)
5. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (59.601)
6. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (58.333)
7. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (57.479)
8. *The Hate U Give* — Angie Thomas (53.972)
9. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (53.898)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (52.976)
11. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (52.755)
12. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (52.232)

#### plain_mean

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.792)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.783)
3. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.742)
4. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.742)
5. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.738)
6. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.716)
7. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.714)
8. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.678)
9. *The Hate U Give* — Angie Thomas (0.671)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.661)
11. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.652)
12. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.645)

#### mean_displacement

1. *Among the Ten Thousand Things* — Julia Pierpont (0.655)
2. *The Three Weissmanns of Westport* — Cathleen Schine (0.643)
3. *Rich and Pretty* — Rumaan Alam (0.624)
4. *Emma (The Austen Project, #3)* — Alexander McCall Smith (0.611)
5. *Primates of Park Avenue* — Wednesday Martin (0.608)
6. *All the Summer Girls* — Meg Donohue (0.600)
7. *This One is Mine* — Maria Semple (0.597)
8. *A Wedding in December* — Anita Shreve (0.596)
9. *Nanny Returns (Nanny, #2)* — Emma McLaughlin (0.594)
10. *Citizen Girl* — Emma McLaughlin (0.593)
11. *The Girls of August* — Anne Rivers Siddons (0.584)
12. *Girls in Trucks* — Katie Crouch (0.580)

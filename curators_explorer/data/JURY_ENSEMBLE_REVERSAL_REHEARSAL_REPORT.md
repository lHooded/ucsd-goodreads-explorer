# Ensemble convergence-reversal of random juries

Each random jury is iterated through the standard map (stage 0 collapses to the Goodreads center), then gain-hard convergence reversal prunes the strongest proponents of the converged direction and restarts from the same jury seed. This report asks whether the reversed endpoints of many random juries, taken together, point at a literary center. Literary scoring is done in preference space after all directions, preferences, aggregates, and clusters are frozen; endpoint directions are used only to cluster the basins.

Sizes: **[2000, 5000]**; juries per size: **25**; runtime: **145.0s**. Chance @50: exact 0.10, broad 0.80, anti 6.17.

## Jury size 2,000 (25 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.074, median 0.075 (min 0.005, max 0.127). Stop reasons: {'evidence_floor': 25}; median deepest users 14,015.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 10/10 |
| plain_mean | 0/0 | 0/0 | 32/32 |
| coordinate_median | 0/0 | 0/0 | 33/33 |
| agreement_consensus | 0/0 | 0/0 | 32/32 |
| mean_displacement | 0/0 | 0/0 | 5/5 |
| big_jury_control (n=50,000) | 0/0 | 0/0 | 44/44 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 0.12, median 0, max 1; broad_lit: mean 0.68, max 4; anti: mean 20.20. 0/25 juries reach exact_lit50 >= 3; 0/25 reach broad_lit50 >= 5.

### Basin census (clustered endpoint directions)

Correlation threshold 0.5; 25 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 1 | 0 | 0 | 23 |
| 2 | 1 | 0 | 0 | 43 |
| 3 | 1 | 0 | 0 | 45 |
| 4 | 1 | 0 | 0 | 24 |
| 5 | 1 | 0 | 0 | 25 |
| 6 | 1 | 0 | 0 | 45 |
| 7 | 1 | 0 | 0 | 23 |
| 8 | 1 | 0 | 0 | 12 |
| 9 | 1 | 0 | 0 | 23 |
| 10 | 1 | 1 | 1 | 8 |
| 11 | 1 | 0 | 0 | 2 |
| 12 | 1 | 0 | 2 | 6 |
| 13 | 1 | 0 | 2 | 8 |
| 14 | 1 | 0 | 0 | 25 |
| 15 | 1 | 1 | 4 | 7 |
| 16 | 1 | 0 | 0 | 36 |
| 17 | 1 | 0 | 2 | 13 |
| 18 | 1 | 0 | 0 | 23 |
| 19 | 1 | 0 | 0 | 43 |
| 20 | 1 | 1 | 3 | 7 |
| 21 | 1 | 0 | 3 | 7 |
| 22 | 1 | 0 | 0 | 23 |
| 23 | 1 | 0 | 0 | 11 |
| 24 | 1 | 0 | 0 | 11 |
| 25 | 1 | 0 | 0 | 12 |

#### Basin 1 (1 juries) head

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.815)
2. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.812)
3. *Fullmetal Alchemist, Vol. 3 (Fullmetal Alchemist, #3)* — Hiromu Arakawa (0.801)
4. *Magic Slays (Kate Daniels, #5)* — Ilona Andrews (0.800)
5. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.797)
6. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.797)
7. *Fruits Basket, Vol. 16* — Natsuki Takaya (0.796)
8. *Fruits Basket, Vol. 11* — Natsuki Takaya (0.796)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.793)
10. *Fullmetal Alchemist, Vol. 10 (Fullmetal Alchemist, #10)* — Hiromu Arakawa (0.787)

#### Basin 2 (1 juries) head

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.864)
2. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.856)
3. *The Last Olympian (Percy Jackson and the Olympians, #5)* — Rick Riordan (0.846)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.838)
5. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.837)
6. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.827)
7. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.819)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.807)
9. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.782)
10. *City of Heavenly Fire (The Mortal Instruments, #6)* — Cassandra Clare (0.778)

#### Basin 3 (1 juries) head

1. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.890)
2. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.865)
3. *Third Grave Dead Ahead (Charley Davidson, #3)* — Darynda Jones (0.865)
4. *Magic Slays (Kate Daniels, #5)* — Ilona Andrews (0.855)
5. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.853)
6. *Dreamfever (Fever, #4)* — Karen Marie Moning (0.837)
7. *Magic Rises (Kate Daniels, #6)* — Ilona Andrews (0.824)
8. *Fifth Grave Past the Light (Charley Davidson, #5)* — Darynda Jones (0.817)
9. *Kiss of Snow (Psy-Changeling #10)* — Nalini Singh (0.817)
10. *Acheron (Dark-Hunter #14)* — Sherrilyn Kenyon (0.813)

### Aggregate heads

#### center_stage0

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.908)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.903)
3. *March: Book Two (March, #2)* — John             Lewis (0.901)
4. *The Hate U Give* — Angie Thomas (0.887)
5. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.885)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.868)
7. *March: Book Three (March, #3)* — John             Lewis (0.864)
8. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.856)
9. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.852)
10. *Calvin and Hobbes* — Bill Watterson (0.844)
11. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.842)
12. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.842)

#### agreement_consensus

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (1.355)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (1.339)
3. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (1.249)
4. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (1.240)
5. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (1.227)
6. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (1.197)
7. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (1.192)
8. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (1.169)
9. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (1.147)
10. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (1.119)
11. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (1.079)
12. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (1.077)

#### plain_mean

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.721)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.712)
3. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.665)
4. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.657)
5. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.653)
6. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.653)
7. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.652)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.637)
9. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.630)
10. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.610)
11. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.598)
12. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.593)

#### mean_displacement

1. *Among the Ten Thousand Things* — Julia Pierpont (0.720)
2. *Emma (The Austen Project, #3)* — Alexander McCall Smith (0.711)
3. *The Three Weissmanns of Westport* — Cathleen Schine (0.703)
4. *After Alice* — Gregory Maguire (0.693)
5. *A Wedding in December* — Anita Shreve (0.691)
6. *Primates of Park Avenue* — Wednesday Martin (0.689)
7. *The Red House* — Mark Haddon (0.675)
8. *Oroonoko* — Aphra Behn (0.673)
9. *Rich and Pretty* — Rumaan Alam (0.664)
10. *The Witches: Salem, 1692* — Stacy Schiff (0.662)
11. *This One is Mine* — Maria Semple (0.661)
12. *The Front (Winston Garano, #2)* — Patricia Cornwell (0.656)

## Jury size 5,000 (25 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.139, median 0.133 (min 0.070, max 0.189). Stop reasons: {'evidence_floor': 25}; median deepest users 15,167.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 14/14 |
| plain_mean | 0/0 | 0/0 | 25/25 |
| coordinate_median | 0/0 | 0/0 | 25/25 |
| agreement_consensus | 0/0 | 0/0 | 23/23 |
| mean_displacement | 0/0 | 0/0 | 7/7 |
| big_jury_control (n=116,635) | 0/0 | 0/0 | 42/42 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 0.16, median 0, max 1; broad_lit: mean 0.20, max 2; anti: mean 24.68. 0/25 juries reach exact_lit50 >= 3; 0/25 reach broad_lit50 >= 5.

### Basin census (clustered endpoint directions)

Correlation threshold 0.5; 24 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 2 | 0 | 0 | 31 |
| 2 | 1 | 0 | 0 | 30 |
| 3 | 1 | 0 | 0 | 38 |
| 4 | 1 | 0 | 0 | 21 |
| 5 | 1 | 0 | 0 | 35 |
| 6 | 1 | 0 | 0 | 21 |
| 7 | 1 | 0 | 0 | 27 |
| 8 | 1 | 0 | 0 | 24 |
| 9 | 1 | 0 | 0 | 34 |
| 10 | 1 | 1 | 1 | 19 |
| 11 | 1 | 0 | 0 | 27 |
| 12 | 1 | 0 | 0 | 38 |
| 13 | 1 | 1 | 2 | 11 |
| 14 | 1 | 0 | 0 | 15 |
| 15 | 1 | 0 | 0 | 23 |
| 16 | 1 | 0 | 0 | 33 |
| 17 | 1 | 0 | 0 | 34 |
| 18 | 1 | 0 | 0 | 20 |
| 19 | 1 | 0 | 0 | 20 |
| 20 | 1 | 1 | 1 | 13 |
| 21 | 1 | 1 | 1 | 13 |
| 22 | 1 | 0 | 0 | 16 |
| 23 | 1 | 0 | 0 | 23 |
| 24 | 1 | 0 | 0 | 18 |

#### Basin 1 (2 juries) head

1. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.777)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.771)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.762)
4. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.743)
5. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.728)
6. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.713)
7. *The Nightingale* — Kristin Hannah (0.703)
8. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.702)
9. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.699)
10. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.698)

#### Basin 2 (1 juries) head

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.841)
2. *Changes (The Dresden Files, #12)* — Jim Butcher (0.821)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.809)
4. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.778)
5. *White Night (The Dresden Files, #9)* — Jim Butcher (0.769)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.767)
7. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.762)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.752)
9. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.750)
10. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (0.744)

#### Basin 3 (1 juries) head

1. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.830)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.822)
3. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.778)
4. *Magic Rises (Kate Daniels, #6)* — Ilona Andrews (0.771)
5. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.769)
6. *Magic Slays (Kate Daniels, #5)* — Ilona Andrews (0.765)
7. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.765)
8. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.759)
9. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.753)
10. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.752)

### Aggregate heads

#### center_stage0

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.906)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.895)
3. *The Hate U Give* — Angie Thomas (0.886)
4. *The Complete Calvin and Hobbes* — Bill Watterson (0.881)
5. *March: Book Two (March, #2)* — John             Lewis (0.869)
6. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.837)
7. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.835)
8. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.827)
9. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.825)
10. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.825)
11. *Humans of New York: Stories* — Brandon Stanton (0.823)
12. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.818)

#### agreement_consensus

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (2.818)
2. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (2.639)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (2.623)
4. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (2.601)
5. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (2.533)
6. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (2.533)
7. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (2.498)
8. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (2.484)
9. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (2.457)
10. *Changes (The Dresden Files, #12)* — Jim Butcher (2.418)
11. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (2.407)
12. *The Hate U Give* — Angie Thomas (2.370)

#### plain_mean

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.787)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.760)
3. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.740)
4. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.736)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.734)
6. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.734)
7. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.704)
8. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.701)
9. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.700)
10. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.696)
11. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.688)
12. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.687)

#### mean_displacement

1. *One Indian Girl* — Chetan Bhagat (0.603)
2. *The Bling Ring: How a Gang of Fame-Obsessed Teens Ripped Off Hollywood and Shocked the World* — Nancy Jo Sales (0.601)
3. *The Three Weissmanns of Westport* — Cathleen Schine (0.590)
4. *Sweet Valley Confidential: Ten Years Later* — Francine Pascal (0.582)
5. *Emma (The Austen Project, #3)* — Alexander McCall Smith (0.581)
6. *Nanny Returns (Nanny, #2)* — Emma McLaughlin (0.579)
7. *Diary Of An Oxygen Thief (The Oxygen Thief Diaries #1)* — Anonymous (0.571)
8. *Trapped* — Michael Northrop (0.571)
9. *It's Not Okay: Turning Heartbreak Into Happily Never After* — Andi Dorfman (0.569)
10. *Shopaholic on Honeymoon (Shopaholic #3.5)* — Sophie Kinsella (0.566)
11. *Oroonoko* — Aphra Behn (0.565)
12. *A Desirable Residence* — Madeleine Wickham (0.563)

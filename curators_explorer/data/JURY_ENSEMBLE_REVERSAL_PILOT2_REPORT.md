# Ensemble convergence-reversal of random juries

Each random jury is iterated through the standard map (stage 0 collapses to the Goodreads center), then gain-hard convergence reversal prunes the strongest proponents of the converged direction and restarts from the same jury seed. This report asks whether the reversed endpoints of many random juries, taken together, point at a literary center. Literary scoring is done in preference space after all directions, preferences, aggregates, and clusters are frozen; endpoint directions are used only to cluster the basins.

Sizes: **[1500, 3000]**; juries per size: **4**; runtime: **30.8s**. Chance @50: exact 0.10, broad 0.80, anti 6.17.

## Jury size 1,500 (4 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.028, median 0.030 (min 0.014, max 0.037). Stop reasons: {'evidence_floor': 4}; median deepest users 14,199.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 8/8 |
| plain_mean | 0/0 | 0/0 | 24/24 |
| coordinate_median | 0/0 | 0/0 | 19/19 |
| agreement_consensus | 0/0 | 0/0 | 26/26 |
| mean_displacement | 0/0 | 1/1 | 7/7 |
| big_jury_control (n=6,000) | 0/0 | 0/0 | 16/16 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 0.25, median 0, max 1; broad_lit: mean 0.75, max 3; anti: mean 16.25. 0/4 juries reach exact_lit50 >= 3; 0/4 reach broad_lit50 >= 5.

### Basin census (clustered endpoint directions)

Correlation threshold 0.5; 4 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 3 | 4 |
| 2 | 1 | 0 | 0 | 28 |
| 3 | 1 | 0 | 0 | 5 |
| 4 | 1 | 0 | 0 | 28 |

#### Basin 1 (1 juries) head

1. *The Qur'an / القرآن الكريم* — Anonymous (0.923)
2. *رياض الصالحين* — yHy~ bn shrf lnwwy (0.823)
3. *لا تصالح* — 'ml dnql (0.819)
4. *الرحيق المختوم* — Safiy al-Rahman al-Mubarakfuri (0.819)
5. *الإسلام بين الشرق والغرب* — Alija Izetbegovic (0.812)
6. *لافتات - المجموعة الكاملة* — 'Hmd mTr (0.784)
7. *الحرافيش* — Naguib Mahfouz (0.777)
8. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.776)
9. *الجريمة والعقاب # 2* — Fyodor Dostoyevsky (0.774)
10. *Mornings in Jenin* — Susan Abulhawa (0.769)

#### Basin 2 (1 juries) head

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.843)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.828)
3. *Fruits Basket, Vol. 4* — Natsuki Takaya (0.816)
4. *Fruits Basket, Vol. 16* — Natsuki Takaya (0.806)
5. *The Last Olympian (Percy Jackson and the Olympians, #5)* — Rick Riordan (0.800)
6. *Fruits Basket, Vol. 5* — Natsuki Takaya (0.799)
7. *Armed & Dangerous (Cut & Run, #5)* — Abigail Roux (0.794)
8. *Fruits Basket, Vol. 7* — Natsuki Takaya (0.793)
9. *Fruits Basket, Vol. 9* — Natsuki Takaya (0.792)
10. *Fish & Chips (Cut & Run, #3)* — Abigail Roux (0.792)

#### Basin 3 (1 juries) head

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.873)
2. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.857)
3. *Calvin and Hobbes* — Bill Watterson (0.839)
4. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (0.826)
5. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.821)
6. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.819)
7. *The Complete Calvin and Hobbes* — Bill Watterson (0.803)
8. *Transmetropolitan, Vol. 7: Spider's Thrash (Transmetropolitan, #7)* — Warren Ellis (0.803)
9. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.796)
10. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.795)

### Aggregate heads

#### center_stage0

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.908)
2. *March: Book Two (March, #2)* — John             Lewis (0.899)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.899)
4. *The Hate U Give* — Angie Thomas (0.888)
5. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.883)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.870)
7. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.867)
8. *March: Book Three (March, #3)* — John             Lewis (0.861)
9. *Calvin and Hobbes* — Bill Watterson (0.852)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.852)
11. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.848)
12. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.846)

#### agreement_consensus

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.082)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.080)
3. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.078)
4. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.075)
5. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.074)
6. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.073)
7. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.072)
8. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.070)
9. *Fullmetal Alchemist, Vol. 1 (Fullmetal Alchemist, #1)* — Hiromu Arakawa (0.069)
10. *The Godfather* — Mario Puzo (0.068)
11. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.068)
12. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.067)

#### plain_mean

1. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.717)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.711)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.707)
4. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.704)
5. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.662)
6. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.657)
7. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.644)
8. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.644)
9. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.632)
10. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.630)
11. *Changes (The Dresden Files, #12)* — Jim Butcher (0.625)
12. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.624)

#### mean_displacement

1. *Oroonoko* — Aphra Behn (0.753)
2. *Palo Alto* — James Franco (0.748)
3. *Pamela; or, Virtue Rewarded* — Samuel Richardson (0.737)
4. *Primates of Park Avenue* — Wednesday Martin (0.724)
5. *Blue Shoe* — Anne Lamott (0.720)
6. *The Three Weissmanns of Westport* — Cathleen Schine (0.719)
7. *Sweet Valley Confidential: Ten Years Later* — Francine Pascal (0.710)
8. *Among the Ten Thousand Things* — Julia Pierpont (0.707)
9. *The Red House* — Mark Haddon (0.705)
10. *After Alice* — Gregory Maguire (0.704)
11. *The Bling Ring: How a Gang of Fame-Obsessed Teens Ripped Off Hollywood and Shocked the World* — Nancy Jo Sales (0.702)
12. *Bellman & Black* — Diane Setterfield (0.701)

## Jury size 3,000 (4 juries)

Endpoint agreement (mean pairwise direction correlation): mean 0.061, median 0.069 (min 0.021, max 0.085). Stop reasons: {'evidence_floor': 4}; median deepest users 14,566.

### Processed averages (preference space)

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| center_stage0 | 0/0 | 0/0 | 12/12 |
| plain_mean | 0/0 | 0/0 | 21/21 |
| coordinate_median | 0/0 | 0/0 | 20/20 |
| agreement_consensus | 0/0 | 0/0 | 25/25 |
| mean_displacement | 0/0 | 0/0 | 7/7 |
| big_jury_control (n=12,000) | 0/0 | 0/0 | 29/29 |

### Per-jury endpoint distribution (@50)

exact_lit: mean 0.00, median 0, max 0; broad_lit: mean 0.50, max 2; anti: mean 19.75. 0/4 juries reach exact_lit50 >= 3; 0/4 reach broad_lit50 >= 5.

### Basin census (clustered endpoint directions)

Correlation threshold 0.5; 4 basins. Literary metrics are each basin's mean member preference head.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 1 | 0 | 0 | 28 |
| 2 | 1 | 0 | 0 | 38 |
| 3 | 1 | 0 | 0 | 6 |
| 4 | 1 | 0 | 2 | 7 |

#### Basin 1 (1 juries) head

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.947)
2. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.895)
3. *Skin Game (The Dresden Files, #15)* — Jim Butcher (0.889)
4. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.883)
5. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (0.876)
6. *Changes (The Dresden Files, #12)* — Jim Butcher (0.876)
7. *A Memory of Light (Wheel of Time, #14)* — Robert Jordan (0.862)
8. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.857)
9. *Small Favor (The Dresden Files, #10)* — Jim Butcher (0.843)
10. *Fool's Quest  (The Fitz and The Fool, #2)* — Robin Hobb (0.840)

#### Basin 2 (1 juries) head

1. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.811)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.806)
3. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.786)
4. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.760)
5. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.747)
6. *Dreamfever (Fever, #4)* — Karen Marie Moning (0.741)
7. *Father Mine (Black Dagger Brotherhood, #6.5)* — J.R. Ward (0.726)
8. *The Nightingale* — Kristin Hannah (0.721)
9. *Demon from the Dark (Immortals After Dark #10)* — Kresley Cole (0.718)
10. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.713)

#### Basin 3 (1 juries) head

1. *Calvin and Hobbes* — Bill Watterson (0.871)
2. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.849)
3. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.846)
4. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.844)
5. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.839)
6. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.836)
7. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.830)
8. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.829)
9. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.827)
10. *Brief Lives (The Sandman #7)* — Neil Gaiman (0.816)

### Aggregate heads

#### center_stage0

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.896)
2. *The Hate U Give* — Angie Thomas (0.891)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.889)
4. *March: Book Two (March, #2)* — John             Lewis (0.880)
5. *The Complete Calvin and Hobbes* — Bill Watterson (0.877)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.850)
7. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.849)
8. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.839)
9. *Humans of New York: Stories* — Brandon Stanton (0.836)
10. *March: Book Three (March, #3)* — John             Lewis (0.831)
11. *Dear Ijeawele, or a Feminist Manifesto in Fifteen Suggestions* — Chimamanda Ngozi Adichie (0.822)
12. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.817)

#### agreement_consensus

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.181)
2. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.178)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.176)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.172)
5. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.166)
6. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.165)
7. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.165)
8. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.162)
9. *The Nightingale* — Kristin Hannah (0.155)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.154)
11. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.154)
12. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.153)

#### plain_mean

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.747)
2. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.741)
3. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.728)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.706)
5. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.705)
6. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.687)
7. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.663)
8. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.662)
9. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.657)
10. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.657)
11. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.651)
12. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.643)

#### mean_displacement

1. *The Girls of August* — Anne Rivers Siddons (0.740)
2. *Palo Alto* — James Franco (0.740)
3. *Stella Bain* — Anita Shreve (0.715)
4. *Emma (The Austen Project, #3)* — Alexander McCall Smith (0.706)
5. *The Three Weissmanns of Westport* — Cathleen Schine (0.704)
6. *All the Summer Girls* — Meg Donohue (0.702)
7. *How to Be Single* — Liz Tuccillo (0.697)
8. *A Desirable Residence* — Madeleine Wickham (0.695)
9. *Her* — Harriet Lane (0.694)
10. *Blue Shoe* — Anne Lamott (0.686)
11. *Rich and Pretty* — Rumaan Alam (0.685)
12. *One Indian Girl* — Chetan Bhagat (0.680)

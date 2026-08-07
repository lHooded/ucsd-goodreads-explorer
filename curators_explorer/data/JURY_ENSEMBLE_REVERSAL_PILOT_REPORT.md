# Ensemble convergence-reversal of random juries

Each random jury is iterated through the standard map (stage 0 collapses to the Goodreads center), then gain-hard convergence reversal prunes the strongest proponents of the converged direction and restarts from the same jury seed. This report asks whether the reversed endpoints of many random juries, taken together, point at a literary center. All averages are label-free; literary metrics are applied only after every direction, aggregate, and cluster is frozen.

Sizes: **[1500, 3000]**; juries per size: **3**; runtime: **24.9s**. Chance @50: exact 0.10, broad 0.80, anti 6.17.

## Jury size 1,500 (3 juries)

Endpoint agreement (mean pairwise correlation): mean 0.042, median 0.037 (min 0.035, max 0.053). Stop reasons: {'evidence_floor': 3}.

### Processed averages of endpoint directions

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| ensemble_center | 10/10 | 13/13 | 3/3 |
| plain_mean | 1/1 | 2/2 | 6/6 |
| coordinate_median | 1/1 | 1/1 | 5/5 |
| agreement_consensus | 1/1 | 2/2 | 2/2 |
| mean_displacement | 0/0 | 0/0 | 48/48 |
| big_jury_control (n=4,500) | 0/0 | 0/0 | 36/36 |

### Basin census (clustered endpoint directions)

Correlation threshold 0.5; 3 basins.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 4 | 1 |
| 2 | 1 | 0 | 0 | 36 |
| 3 | 1 | 0 | 0 | 10 |

#### Basin 1 (1 juries) head

1. *ثلاثية غرناطة* — Radwa Ashour (0.062)
2. *الطنطورية* — Radwa Ashour (0.053)
3. *ساق البامبو* — s`wd lsn`wsy (0.053)
4. *Animal Farm* — George Orwell (0.049)
5. *الحرافيش* — Naguib Mahfouz (0.048)
6. *1984* — George Orwell (0.047)
7. *لا تصالح* — 'ml dnql (0.043)
8. *الإسلام بين الشرق والغرب* — Alija Izetbegovic (0.041)
9. *The Forty Rules of Love* — Elif Shafak (0.041)
10. *عزازيل* — ywsf zydn (0.040)

#### Basin 2 (1 juries) head

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.043)
2. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.039)
3. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.038)
4. *The Last Olympian (Percy Jackson and the Olympians, #5)* — Rick Riordan (0.038)
5. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.038)
6. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.036)
7. *Fruits Basket, Vol. 4* — Natsuki Takaya (0.035)
8. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (0.033)
9. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.033)
10. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.032)

#### Basin 3 (1 juries) head

1. *The Stand* — Stephen King (0.039)
2. *Watchmen* — Alan Moore (0.032)
3. *The Walking Dead, Vol. 03: Safety Behind Bars* — Robert Kirkman (0.031)
4. *Batman: The Dark Knight Returns (The Dark Knight Saga, #1)* — Frank Miller (0.029)
5. *The Walking Dead, Vol. 01: Days Gone Bye* — Robert Kirkman (0.028)
6. *The Waste Lands* — Stephen King (0.027)
7. *11/22/63* — Stephen King (0.027)
8. *Explorers on the Moon (Tintin, #17)* — Herge (0.026)
9. *Transmetropolitan, Vol. 3: Year of the Bastard (Transmetropolitan, #3)* — Warren Ellis (0.026)
10. *It* — Stephen King (0.025)

### Aggregate heads

#### ensemble_center

1. *1984* — George Orwell (0.054)
2. *Between the World and Me* — Ta-Nehisi Coates (0.045)
3. *Crime and Punishment* — Fyodor Dostoyevsky (0.044)
4. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (0.040)
5. *The Handmaid's Tale* — Margaret Atwood (0.039)
6. *To Kill a Mockingbird* — Harper Lee (0.038)
7. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.038)
8. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.037)
9. *Slaughterhouse-Five* — Kurt Vonnegut Jr. (0.037)
10. *Watchmen* — Alan Moore (0.037)
11. *Hamlet* — William Shakespeare (0.036)
12. *Animal Farm* — George Orwell (0.035)

#### agreement_consensus

1. *ثلاثية غرناطة* — Radwa Ashour (0.046)
2. *الطنطورية* — Radwa Ashour (0.045)
3. *1984* — George Orwell (0.042)
4. *Animal Farm* — George Orwell (0.040)
5. *زمن الخيول البيضاء* — Ibrahim Nasrallah - ibrhym nSr llh (0.036)
6. *الحرافيش* — Naguib Mahfouz (0.035)
7. *لا تصالح* — 'ml dnql (0.030)
8. *رأيت رام الله* — Mourid Barghouti (0.030)
9. *Mornings in Jenin* — Susan Abulhawa (0.030)
10. *Because I Said So (Because You Are Mine, #1.5)* — Beth Kery (0.029)
11. *رجال في الشمس* — Gsn knfny (0.028)
12. *Because I Could Not Resist (Because You Are Mine, #1.2)* — Beth Kery (0.027)

#### plain_mean

1. *الطنطورية* — Radwa Ashour (0.039)
2. *ثلاثية غرناطة* — Radwa Ashour (0.039)
3. *1984* — George Orwell (0.037)
4. *Animal Farm* — George Orwell (0.035)
5. *زمن الخيول البيضاء* — Ibrahim Nasrallah - ibrhym nSr llh (0.032)
6. *Because I Said So (Because You Are Mine, #1.5)* — Beth Kery (0.030)
7. *الحرافيش* — Naguib Mahfouz (0.029)
8. *Because I Could Not Resist (Because You Are Mine, #1.2)* — Beth Kery (0.028)
9. *The Doll's House (The Sandman #2)* — Neil Gaiman (0.027)
10. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.027)
11. *Mornings in Jenin* — Susan Abulhawa (0.027)
12. *Because You Must Learn (Because You Are Mine, #1.4)* — Beth Kery (0.027)

#### mean_displacement

1. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.043)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.043)
3. *Divergent (Divergent, #1)* — Veronica Roth (0.041)
4. *The Hunger Games (The Hunger Games, #1)* — Suzanne Collins (0.041)
5. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (0.041)
6. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.040)
7. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.040)
8. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.040)
9. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (0.039)
10. *Catching Fire (The Hunger Games, #2)* — Suzanne Collins (0.038)
11. *The Last Olympian (Percy Jackson and the Olympians, #5)* — Rick Riordan (0.037)
12. *The Da Vinci Code (Robert Langdon, #2)* — Dan Brown (0.036)

## Jury size 3,000 (3 juries)

Endpoint agreement (mean pairwise correlation): mean 0.063, median 0.106 (min -0.031, max 0.113). Stop reasons: {'evidence_floor': 3}.

### Processed averages of endpoint directions

| aggregate | exact @50/200 | broad @50/200 | anti @50/200 |
|---|---|---|---|
| ensemble_center | 1/1 | 1/1 | 9/9 |
| plain_mean | 0/0 | 0/0 | 22/22 |
| coordinate_median | 0/0 | 0/0 | 16/16 |
| agreement_consensus | 0/0 | 0/0 | 18/18 |
| mean_displacement | 0/0 | 0/0 | 32/32 |
| big_jury_control (n=9,000) | 0/0 | 0/0 | 43/43 |

### Basin census (clustered endpoint directions)

Correlation threshold 0.5; 3 basins.

| basin | juries | exact @50 | broad @50 | anti @50 |
|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 1 | 8 |
| 2 | 1 | 0 | 0 | 26 |
| 3 | 1 | 0 | 0 | 14 |

#### Basin 1 (1 juries) head

1. *The Lies of Locke Lamora (Gentleman Bastard, #1)* — Scott Lynch (0.026)
2. *Memories of Ice (The Malazan Book of the Fallen, #3)* — Steven Erikson (0.025)
3. *Deadhouse Gates (The Malazan Book of the Fallen, #2)* — Steven Erikson (0.024)
4. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.024)
5. *House of Chains (The Malazan Book of the Fallen, #4)* — Steven Erikson (0.024)
6. *Blood Song (Raven's Shadow, #1)* — Anthony  Ryan (0.023)
7. *The Bonehunters (Malazan Book of the Fallen, #6)* — Steven Erikson (0.023)
8. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (0.023)
9. *Onslaught (Dark Tide, #1) (Star Wars: The New Jedi Order, #2)* — Michael A. Stackpole (0.023)
10. *The Crippled God (The Malazan Book of the Fallen, #10)* — Steven Erikson (0.023)

#### Basin 2 (1 juries) head

1. *Fruits Basket, Vol. 18* — Natsuki Takaya (0.034)
2. *Fruits Basket, Vol. 4* — Natsuki Takaya (0.033)
3. *Fruits Basket, Vol. 11* — Natsuki Takaya (0.033)
4. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.033)
5. *Fruits Basket, Vol. 5* — Natsuki Takaya (0.032)
6. *Fruits Basket, Vol. 12* — Natsuki Takaya (0.031)
7. *Fruits Basket, Vol. 19* — Natsuki Takaya (0.031)
8. *Fullmetal Alchemist, Vol. 2 (Fullmetal Alchemist, #2)* — Hiromu Arakawa (0.031)
9. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.031)
10. *Fruits Basket, Vol. 2* — Natsuki Takaya (0.031)

#### Basin 3 (1 juries) head

1. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.039)
2. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.037)
3. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (0.036)
4. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.036)
5. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.035)
6. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.035)
7. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.031)
8. *The Book Thief* — Markus Zusak (0.030)
9. *The Last Boyfriend (Forever Love, #1)* — J.S. Cooper (0.028)
10. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.027)

### Aggregate heads

#### ensemble_center

1. *To Kill a Mockingbird* — Harper Lee (0.061)
2. *The Nightingale* — Kristin Hannah (0.046)
3. *All the Light We Cannot See* — Anthony Doerr (0.045)
4. *The Help* — Kathryn Stockett (0.043)
5. *Unbroken: A World War II Story of Survival, Resilience, and Redemption* — Laura Hillenbrand (0.042)
6. *The Kite Runner* — Khaled Hosseini (0.039)
7. *The Diary of a Young Girl* — Anne Frank (0.039)
8. *A Man Called Ove* — Fredrik Backman (0.039)
9. *A Thousand Splendid Suns* — Khaled Hosseini (0.038)
10. *Between the World and Me* — Ta-Nehisi Coates (0.037)
11. *A Tree Grows in Brooklyn* — Betty  Smith (0.037)
12. *Charlotte's Web* — E.B. White (0.036)

#### agreement_consensus

1. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.044)
2. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.043)
3. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.042)
4. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.041)
5. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.041)
6. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (0.039)
7. *The Book Thief* — Markus Zusak (0.034)
8. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.033)
9. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.031)
10. *To Kill a Mockingbird* — Harper Lee (0.031)
11. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.030)
12. *Skip Beat!, Vol. 07* — Yoshiki Nakamura (0.029)

#### plain_mean

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.045)
2. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.045)
3. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.042)
4. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.041)
5. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.040)
6. *The Book Thief* — Markus Zusak (0.040)
7. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (0.037)
8. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.035)
9. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.034)
10. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.033)
11. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.033)
12. *To Kill a Mockingbird* — Harper Lee (0.031)

#### mean_displacement

1. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.060)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.058)
3. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.053)
4. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.050)
5. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (0.049)
6. *The Hero of Ages (Mistborn, #3)* — Brandon Sanderson (0.047)
7. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.044)
8. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.043)
9. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.043)
10. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.042)
11. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.042)
12. *The Lies of Locke Lamora (Gentleman Bastard, #1)* — Scott Lynch (0.040)

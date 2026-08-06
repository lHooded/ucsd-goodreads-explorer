# Seedless nonlinear jury-attractor census

Discovery used only `(user_id, work_id, rating)`. Random reader cohorts were iteratively reweighted by agreement with degree-corrected signed book support. Titles, authors, and evaluation lists were loaded only after convergence, basin clustering, and scoring.

Starts: **16**; iterations: **30**; beta: **1.5**; basins at correlation ≥0.92: **4**; runtime: **12.9s**.

## Contraction trajectory

| iteration | mean step corr | q10 | q90 | effective user share |
|---:|---:|---:|---:|---:|
| 1 | nan | nan | nan | 0.630 |
| 2 | 0.9465 | 0.9146 | 0.9779 | 0.755 |
| 3 | 0.9700 | 0.9670 | 0.9729 | 0.788 |
| 4 | 0.9743 | 0.9703 | 0.9783 | 0.793 |
| 5 | 0.9755 | 0.9688 | 0.9815 | 0.794 |
| 6 | 0.9767 | 0.9694 | 0.9847 | 0.794 |
| 7 | 0.9804 | 0.9747 | 0.9859 | 0.793 |
| 8 | 0.9853 | 0.9817 | 0.9888 | 0.791 |
| 9 | 0.9893 | 0.9856 | 0.9924 | 0.790 |
| 10 | 0.9922 | 0.9882 | 0.9956 | 0.788 |
| 11 | 0.9945 | 0.9914 | 0.9973 | 0.786 |
| 12 | 0.9961 | 0.9935 | 0.9983 | 0.785 |
| 13 | 0.9972 | 0.9953 | 0.9989 | 0.784 |
| 14 | 0.9978 | 0.9962 | 0.9991 | 0.783 |
| 15 | 0.9982 | 0.9966 | 0.9993 | 0.782 |
| 16 | 0.9985 | 0.9969 | 0.9995 | 0.782 |
| 17 | 0.9988 | 0.9973 | 0.9996 | 0.781 |
| 18 | 0.9990 | 0.9978 | 0.9997 | 0.780 |
| 19 | 0.9992 | 0.9983 | 0.9998 | 0.780 |
| 20 | 0.9994 | 0.9987 | 0.9998 | 0.780 |
| 21 | 0.9995 | 0.9990 | 0.9998 | 0.779 |
| 22 | 0.9996 | 0.9992 | 0.9999 | 0.779 |
| 23 | 0.9996 | 0.9993 | 0.9999 | 0.779 |
| 24 | 0.9997 | 0.9994 | 0.9999 | 0.779 |
| 25 | 0.9997 | 0.9994 | 0.9999 | 0.779 |
| 26 | 0.9998 | 0.9995 | 1.0000 | 0.779 |
| 27 | 0.9998 | 0.9996 | 1.0000 | 0.778 |
| 28 | 0.9998 | 0.9996 | 1.0000 | 0.778 |
| 29 | 0.9999 | 0.9997 | 1.0000 | 0.778 |
| 30 | 0.9999 | 0.9997 | 1.0000 | 0.778 |

## Equal-basin center candidates

### equal_basin_mean

Exact literary @50/200: **0/1**; broad literary: **0/2**; anti: **14/48**.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.915; minimum basin reader mass=990)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.901; minimum basin reader mass=284)
3. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.891; minimum basin reader mass=2705)
4. *The Hate U Give* — Angie Thomas (0.885; minimum basin reader mass=1561)
5. *March: Book Two (March, #2)* — John             Lewis (0.884; minimum basin reader mass=190)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.853; minimum basin reader mass=366)
7. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.842; minimum basin reader mass=160)
8. *March: Book Three (March, #3)* — John             Lewis (0.840; minimum basin reader mass=160)
9. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.839; minimum basin reader mass=810)
10. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.834; minimum basin reader mass=596)
11. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.832; minimum basin reader mass=551)
12. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.830; minimum basin reader mass=1853)
13. *Calvin and Hobbes* — Bill Watterson (0.829; minimum basin reader mass=659)
14. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.825; minimum basin reader mass=127)
15. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.825; minimum basin reader mass=960)
16. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.823; minimum basin reader mass=193)
17. *Humans of New York: Stories* — Brandon Stanton (0.821; minimum basin reader mass=239)
18. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.820; minimum basin reader mass=1099)
19. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.819; minimum basin reader mass=140)
20. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.813; minimum basin reader mass=405)
21. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.809; minimum basin reader mass=1359)
22. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.807; minimum basin reader mass=23021)
23. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.807; minimum basin reader mass=699)
24. *Dear Ijeawele, or a Feminist Manifesto in Fifteen Suggestions* — Chimamanda Ngozi Adichie (0.807; minimum basin reader mass=436)
25. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.805; minimum basin reader mass=1220)
26. *Toda Mafalda* — Quino (0.804; minimum basin reader mass=112)
27. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.799; minimum basin reader mass=141)
28. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.796; minimum basin reader mass=1319)
29. *The Harry Potter Collection 1-4 (Harry Potter, #1-4)* — J.K. Rowling (0.793; minimum basin reader mass=331)
30. *March: Book One (March, #1)* — John             Lewis (0.793; minimum basin reader mass=328)

### equal_basin_q10

Exact literary @50/200: **0/0**; broad literary: **0/1**; anti: **14/42**.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.895; minimum basin reader mass=990)
2. *The Hate U Give* — Angie Thomas (0.879; minimum basin reader mass=1561)
3. *The Complete Calvin and Hobbes* — Bill Watterson (0.856; minimum basin reader mass=284)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.853; minimum basin reader mass=2705)
5. *March: Book Two (March, #2)* — John             Lewis (0.849; minimum basin reader mass=190)
6. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.827; minimum basin reader mass=810)
7. *Humans of New York: Stories* — Brandon Stanton (0.808; minimum basin reader mass=239)
8. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.801; minimum basin reader mass=366)
9. *Dear Ijeawele, or a Feminist Manifesto in Fifteen Suggestions* — Chimamanda Ngozi Adichie (0.801; minimum basin reader mass=436)
10. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.789; minimum basin reader mass=1099)
11. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.787; minimum basin reader mass=596)
12. *March: Book Three (March, #3)* — John             Lewis (0.778; minimum basin reader mass=160)
13. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.778; minimum basin reader mass=1853)
14. *Toda Mafalda* — Quino (0.775; minimum basin reader mass=112)
15. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.774; minimum basin reader mass=699)
16. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.773; minimum basin reader mass=405)
17. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.772; minimum basin reader mass=160)
18. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.770; minimum basin reader mass=551)
19. *We Should All Be Feminists* — Chimamanda Ngozi Adichie (0.770; minimum basin reader mass=1858)
20. *Humans of New York* — Brandon Stanton (0.770; minimum basin reader mass=215)
21. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.769; minimum basin reader mass=1319)
22. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.768; minimum basin reader mass=960)
23. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.767; minimum basin reader mass=1359)
24. *Calvin and Hobbes* — Bill Watterson (0.764; minimum basin reader mass=659)
25. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.764; minimum basin reader mass=193)
26. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.760; minimum basin reader mass=1220)
27. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.754; minimum basin reader mass=23021)
28. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.753; minimum basin reader mass=5547)
29. *March: Book One (March, #1)* — John             Lewis (0.749; minimum basin reader mass=328)
30. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.749; minimum basin reader mass=140)

### equal_basin_mean_minus_sd

Exact literary @50/200: **0/1**; broad literary: **0/2**; anti: **14/42**.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.895; minimum basin reader mass=990)
2. *The Hate U Give* — Angie Thomas (0.879; minimum basin reader mass=1561)
3. *The Complete Calvin and Hobbes* — Bill Watterson (0.857; minimum basin reader mass=284)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.854; minimum basin reader mass=2705)
5. *March: Book Two (March, #2)* — John             Lewis (0.850; minimum basin reader mass=190)
6. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.828; minimum basin reader mass=810)
7. *Humans of New York: Stories* — Brandon Stanton (0.809; minimum basin reader mass=239)
8. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.804; minimum basin reader mass=366)
9. *Dear Ijeawele, or a Feminist Manifesto in Fifteen Suggestions* — Chimamanda Ngozi Adichie (0.801; minimum basin reader mass=436)
10. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.790; minimum basin reader mass=596)
11. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.790; minimum basin reader mass=1099)
12. *March: Book Three (March, #3)* — John             Lewis (0.780; minimum basin reader mass=160)
13. *Toda Mafalda* — Quino (0.778; minimum basin reader mass=112)
14. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.778; minimum basin reader mass=1853)
15. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.775; minimum basin reader mass=405)
16. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.774; minimum basin reader mass=699)
17. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.773; minimum basin reader mass=160)
18. *We Should All Be Feminists* — Chimamanda Ngozi Adichie (0.771; minimum basin reader mass=1858)
19. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.771; minimum basin reader mass=551)
20. *Humans of New York* — Brandon Stanton (0.770; minimum basin reader mass=215)
21. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.769; minimum basin reader mass=1319)
22. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.769; minimum basin reader mass=960)
23. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.767; minimum basin reader mass=1359)
24. *Calvin and Hobbes* — Bill Watterson (0.765; minimum basin reader mass=659)
25. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.764; minimum basin reader mass=193)
26. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.760; minimum basin reader mass=1220)
27. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.755; minimum basin reader mass=23021)
28. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.753; minimum basin reader mass=5547)
29. *March: Book One (March, #1)* — John             Lewis (0.751; minimum basin reader mass=328)
30. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.750; minimum basin reader mass=140)

## Basins

### Basin 1 (7 starts)

Within-basin direction correlation: **0.940**; effective reader share: **0.785**; exact literary @50/200: **0/0**; broad literary: **0/0**; anti: **28/80**.

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.929; reader mass=3344)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.896; reader mass=990)
3. *The Hate U Give* — Angie Thomas (0.891; reader mass=2151)
4. *White Hot (Hidden Legacy, #2)* — Ilona Andrews (0.884; reader mass=338)
5. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.882; reader mass=336)
6. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.881; reader mass=4966)
7. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.880; reader mass=2262)
8. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.879; reader mass=658)
9. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.861; reader mass=27977)
10. *A Voice in the Wind (Mark of the Lion, #1)* — Francine Rivers (0.860; reader mass=582)
11. *The Complete Calvin and Hobbes* — Bill Watterson (0.855; reader mass=284)
12. *March: Book Two (March, #2)* — John             Lewis (0.853; reader mass=199)
13. *The Harry Potter Collection 1-4 (Harry Potter, #1-4)* — J.K. Rowling (0.853; reader mass=497)
14. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.849; reader mass=1006)
15. *Humans of New York: Stories* — Brandon Stanton (0.834; reader mass=282)
16. *Harry Potter Boxed Set, Books 1-5 (Harry Potter, #1-5)* — J.K. Rowling (0.833; reader mass=344)
17. *An Echo in the Darkness (Mark of the Lion, #2)* — Francine Rivers (0.831; reader mass=415)
18. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.831; reader mass=883)
19. *Standing for Something: 10 Neglected Virtues That Will Heal Our Hearts and Homes* — Gordon B. Hinckley (0.831; reader mass=178)
20. *The Nightingale* — Kristin Hannah (0.829; reader mass=3654)

### Basin 2 (6 starts)

Within-basin direction correlation: **0.954**; effective reader share: **0.791**; exact literary @50/200: **0/1**; broad literary: **0/6**; anti: **6/30**.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.944; reader mass=711)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.935; reader mass=2343)
3. *March: Book Two (March, #2)* — John             Lewis (0.916; reader mass=368)
4. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.911; reader mass=476)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.909; reader mass=352)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.899; reader mass=719)
7. *March: Book Three (March, #3)* — John             Lewis (0.898; reader mass=330)
8. *Calvin and Hobbes* — Bill Watterson (0.893; reader mass=1309)
9. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.893; reader mass=1263)
10. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.892; reader mass=396)
11. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.887; reader mass=421)
12. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.886; reader mass=332)
13. *The Hate U Give* — Angie Thomas (0.877; reader mass=1561)
14. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.877; reader mass=293)
15. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.875; reader mass=278)
16. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.875; reader mass=241)
17. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.872; reader mass=323)
18. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.863; reader mass=491)
19. *The Revenge of the Baby-Sat* — Bill Watterson (0.863; reader mass=285)
20. *Yukon Ho!* — Bill Watterson (0.860; reader mass=250)

### Basin 3 (2 starts)

Within-basin direction correlation: **0.988**; effective reader share: **0.788**; exact literary @50/200: **0/1**; broad literary: **0/4**; anti: **6/30**.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.944; reader mass=706)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.936; reader mass=2338)
3. *March: Book Two (March, #2)* — John             Lewis (0.921; reader mass=391)
4. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.910; reader mass=474)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.910; reader mass=351)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.904; reader mass=768)
7. *March: Book Three (March, #3)* — John             Lewis (0.903; reader mass=348)
8. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.894; reader mass=1259)
9. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.893; reader mass=395)
10. *Calvin and Hobbes* — Bill Watterson (0.892; reader mass=1308)
11. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=418)
12. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.886; reader mass=331)
13. *The Hate U Give* — Angie Thomas (0.882; reader mass=1702)
14. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.877; reader mass=293)
15. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.877; reader mass=277)
16. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.871; reader mass=323)
17. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.871; reader mass=239)
18. *The Revenge of the Baby-Sat* — Bill Watterson (0.866; reader mass=283)
19. *The Absolute Sandman, Volume One* — Neil Gaiman (0.864; reader mass=401)
20. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.862; reader mass=489)

### Basin 4 (1 starts)

Within-basin direction correlation: **1.000**; effective reader share: **0.772**; exact literary @50/200: **0/0**; broad literary: **0/1**; anti: **28/81**.

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.926; reader mass=3335)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.894; reader mass=996)
3. *The Hate U Give* — Angie Thomas (0.891; reader mass=2070)
4. *White Hot (Hidden Legacy, #2)* — Ilona Andrews (0.886; reader mass=343)
5. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.881; reader mass=337)
6. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.881; reader mass=4969)
7. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.881; reader mass=2268)
8. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.875; reader mass=629)
9. *A Voice in the Wind (Mark of the Lion, #1)* — Francine Rivers (0.862; reader mass=569)
10. *The Complete Calvin and Hobbes* — Bill Watterson (0.859; reader mass=292)
11. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.858; reader mass=27804)
12. *The Harry Potter Collection 1-4 (Harry Potter, #1-4)* — J.K. Rowling (0.853; reader mass=500)
13. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.852; reader mass=1021)
14. *March: Book Two (March, #2)* — John             Lewis (0.847; reader mass=190)
15. *رياض الصالحين* — yHy~ bn shrf lnwwy (0.845; reader mass=205)
16. *An Echo in the Darkness (Mark of the Lion, #2)* — Francine Rivers (0.832; reader mass=402)
17. *Harry Potter Boxed Set, Books 1-5 (Harry Potter, #1-5)* — J.K. Rowling (0.832; reader mass=348)
18. *Humans of New York: Stories* — Brandon Stanton (0.831; reader mass=268)
19. *Wildfire (Hidden Legacy, #3)* — Ilona Andrews (0.831; reader mass=291)
20. *لا تصالح* — 'ml dnql (0.830; reader mass=421)

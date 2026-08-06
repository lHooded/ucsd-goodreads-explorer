# Year-jury nonlinear attractor trajectories

Each year-derived jury starts the same nuisance-projected nonlinear ratings iteration used in the seedless attractor census. A reader selected in both book-parity folds gets full initial weight; a one-fold selection gets half weight. Titles and evaluation lists are loaded only after every path has finished.

Paths: **12**; iterations: **20**; runtime: **10.9s**.

## Summary

| seed | beta | final step corr | direction from start | user weights from start | effective user share | projected rank J@50 | J@200 | projected exact lit @50/200 | broad @50/200 | anti @50/200 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| best_linear_q10 | 1.5 | 0.99998 | 0.530 | 0.249 | 0.782 | 0.111 | 0.081 | 5/11 | 8/20 | 21/56 |
| best_linear_q10 | 2.5 | 0.99998 | 0.546 | 0.257 | 0.687 | 0.111 | 0.090 | 6/13 | 10/22 | 20/54 |
| best_linear_q10 | 3.5 | 0.99998 | 0.552 | 0.259 | 0.637 | 0.111 | 0.105 | 6/14 | 11/27 | 20/52 |
| best_linear_mass_q10 | 1.5 | 0.99999 | 0.618 | 0.260 | 0.782 | 0.111 | 0.093 | 5/11 | 8/20 | 21/56 |
| best_linear_mass_q10 | 2.5 | 0.99998 | 0.626 | 0.263 | 0.687 | 0.111 | 0.105 | 6/13 | 10/23 | 20/54 |
| best_linear_mass_q10 | 3.5 | 0.99998 | 0.630 | 0.261 | 0.637 | 0.111 | 0.117 | 6/14 | 11/26 | 20/54 |
| best_preference_q10 | 1.5 | 0.99993 | 0.506 | 0.215 | 0.785 | 0.075 | 0.090 | 3/11 | 6/18 | 22/52 |
| best_preference_q10 | 2.5 | 0.99989 | 0.523 | 0.218 | 0.694 | 0.099 | 0.105 | 5/12 | 8/20 | 22/54 |
| best_preference_q10 | 3.5 | 0.99986 | 0.532 | 0.217 | 0.648 | 0.124 | 0.120 | 5/14 | 10/23 | 20/50 |
| best_preference_delta_q10 | 1.5 | 0.99986 | 0.454 | 0.149 | 0.784 | 0.111 | 0.099 | 6/11 | 11/22 | 20/50 |
| best_preference_delta_q10 | 2.5 | 0.99988 | 0.463 | 0.149 | 0.692 | 0.111 | 0.111 | 6/13 | 11/24 | 21/50 |
| best_preference_delta_q10 | 3.5 | 0.99988 | 0.467 | 0.148 | 0.644 | 0.111 | 0.124 | 6/14 | 11/26 | 21/50 |

## Findings

- Every path genuinely contracts: final step correlations exceed 0.9998. This proves numerical convergence, not literary validity.
- Share- and mass-based old-love starts collapse to effectively one basin (final direction correlation 0.993–1.000). The old-over-new preference paths retain a nearby distinct basin: cross-basin correlations are 0.896–0.920.
- Only 45.4%–63.0% of the initial directional correlation remains. Initial-to-final projected top-200 Jaccard is only 0.081–0.124.
- The final projected heads mix a few classics with YA/paranormal and fantasy-series axes; ordinary approval collapses further to Calvin and Hobbes, Sanderson, comics, and popular nonfiction. The unconstrained stability iteration therefore washes out the literary year signal rather than refining it.
- Publication-year preference should remain an explicit anchored criterion. A future fixed-point experiment would need an anchor penalty and should be judged by retained literary direction as well as contraction speed.

## Contraction trajectories

### best_linear_q10 · beta=1.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.96624 | 0.9662 | 0.9509 | 0.497 |
| 2 | 0.96950 | 0.8754 | 0.7484 | 0.709 |
| 3 | 0.98556 | 0.7874 | 0.5383 | 0.765 |
| 4 | 0.99361 | 0.7244 | 0.4203 | 0.778 |
| 5 | 0.99666 | 0.6807 | 0.3607 | 0.781 |
| 6 | 0.99796 | 0.6493 | 0.3283 | 0.781 |
| 7 | 0.99862 | 0.6256 | 0.3085 | 0.782 |
| 8 | 0.99899 | 0.6070 | 0.2950 | 0.782 |
| 9 | 0.99920 | 0.5919 | 0.2849 | 0.782 |
| 10 | 0.99936 | 0.5793 | 0.2771 | 0.782 |
| 11 | 0.99950 | 0.5688 | 0.2708 | 0.782 |
| 12 | 0.99961 | 0.5601 | 0.2658 | 0.782 |
| 13 | 0.99970 | 0.5528 | 0.2616 | 0.782 |
| 14 | 0.99978 | 0.5469 | 0.2583 | 0.782 |
| 15 | 0.99985 | 0.5421 | 0.2557 | 0.782 |
| 16 | 0.99990 | 0.5384 | 0.2537 | 0.782 |
| 17 | 0.99994 | 0.5355 | 0.2521 | 0.782 |
| 18 | 0.99996 | 0.5333 | 0.2509 | 0.782 |
| 19 | 0.99997 | 0.5316 | 0.2500 | 0.782 |
| 20 | 0.99998 | 0.5303 | 0.2493 | 0.782 |

Final projected-direction head:

1. *1984* — George Orwell (direction=0.04537)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04105)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04034)
4. *Crossed (Matched, #2)* — Ally Condie (direction=0.03508)
5. *Matched (Matched, #1)* — Ally Condie (direction=0.03506)
6. *Watchmen* — Alan Moore (direction=0.03459)
7. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03447)
8. *Animal Farm* — George Orwell (direction=0.03415)
9. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03408)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03391)
11. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03251)
12. *To Kill a Mockingbird* — Harper Lee (direction=0.03241)
13. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03237)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03229)
15. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03178)
16. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03130)
17. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (direction=0.03061)
18. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.03048)
19. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (direction=0.02994)
20. *The Hobbit* — J.R.R. Tolkien (direction=0.02961)
21. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02924)
22. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02887)
23. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02873)
24. *ثلاثية غرناطة* — Radwa Ashour (direction=0.02849)
25. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02819)
26. *Hamlet* — William Shakespeare (direction=0.02806)
27. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02775)
28. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (direction=0.02762)
29. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02758)
30. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02753)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.945; reader mass=710)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.934; reader mass=2325)
3. *March: Book Two (March, #2)* — John             Lewis (0.918; reader mass=375)
4. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.911; reader mass=477)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.910; reader mass=355)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.902; reader mass=729)
7. *March: Book Three (March, #3)* — John             Lewis (0.899; reader mass=336)
8. *Calvin and Hobbes* — Bill Watterson (0.893; reader mass=1312)
9. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.893; reader mass=398)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.892; reader mass=1265)
11. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.886; reader mass=423)
12. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.883; reader mass=335)
13. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.880; reader mass=279)
14. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.877; reader mass=296)
15. *The Hate U Give* — Angie Thomas (0.877; reader mass=1558)
16. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.876; reader mass=241)
17. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.872; reader mass=323)
18. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.864; reader mass=491)
19. *Yukon Ho!* — Bill Watterson (0.863; reader mass=250)
20. *The Revenge of the Baby-Sat* — Bill Watterson (0.861; reader mass=286)
21. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.861; reader mass=593)
22. *The Absolute Sandman, Volume One* — Neil Gaiman (0.859; reader mass=406)
23. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.857; reader mass=305)
24. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.853; reader mass=955)
25. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.851; reader mass=2702)
26. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.850; reader mass=1980)
27. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.850; reader mass=2261)
28. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.850; reader mass=835)
29. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.849; reader mass=337)
30. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.848; reader mass=1215)

### best_linear_q10 · beta=2.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.95441 | 0.9544 | 0.9233 | 0.464 |
| 2 | 0.97016 | 0.8565 | 0.6855 | 0.632 |
| 3 | 0.98756 | 0.7736 | 0.4934 | 0.673 |
| 4 | 0.99445 | 0.7168 | 0.3958 | 0.683 |
| 5 | 0.99702 | 0.6779 | 0.3479 | 0.685 |
| 6 | 0.99815 | 0.6502 | 0.3220 | 0.686 |
| 7 | 0.99875 | 0.6295 | 0.3062 | 0.687 |
| 8 | 0.99909 | 0.6134 | 0.2954 | 0.687 |
| 9 | 0.99925 | 0.6004 | 0.2873 | 0.687 |
| 10 | 0.99937 | 0.5894 | 0.2808 | 0.687 |
| 11 | 0.99949 | 0.5802 | 0.2756 | 0.687 |
| 12 | 0.99961 | 0.5724 | 0.2714 | 0.687 |
| 13 | 0.99970 | 0.5660 | 0.2679 | 0.687 |
| 14 | 0.99978 | 0.5607 | 0.2651 | 0.687 |
| 15 | 0.99984 | 0.5564 | 0.2629 | 0.687 |
| 16 | 0.99989 | 0.5530 | 0.2611 | 0.687 |
| 17 | 0.99993 | 0.5503 | 0.2597 | 0.687 |
| 18 | 0.99996 | 0.5483 | 0.2587 | 0.687 |
| 19 | 0.99997 | 0.5468 | 0.2579 | 0.687 |
| 20 | 0.99998 | 0.5456 | 0.2573 | 0.687 |

Final projected-direction head:

1. *1984* — George Orwell (direction=0.04820)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04167)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04083)
4. *Crossed (Matched, #2)* — Ally Condie (direction=0.03645)
5. *Matched (Matched, #1)* — Ally Condie (direction=0.03628)
6. *Animal Farm* — George Orwell (direction=0.03601)
7. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03549)
8. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03548)
9. *Watchmen* — Alan Moore (direction=0.03491)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03486)
11. *To Kill a Mockingbird* — Harper Lee (direction=0.03478)
12. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03370)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03364)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03343)
15. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03295)
16. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.03148)
17. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03133)
18. *The Hobbit* — J.R.R. Tolkien (direction=0.03060)
19. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (direction=0.02997)
20. *Hamlet* — William Shakespeare (direction=0.02997)
21. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02955)
22. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (direction=0.02949)
23. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02940)
24. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02875)
25. *The Brothers Karamazov* — Fyodor Dostoyevsky (direction=0.02874)
26. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02859)
27. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02841)
28. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (direction=0.02815)
29. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02801)
30. *Macbeth* — William Shakespeare (direction=0.02776)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.950; reader mass=762)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.935; reader mass=2471)
3. *March: Book Two (March, #2)* — John             Lewis (0.921; reader mass=395)
4. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.917; reader mass=376)
5. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.914; reader mass=509)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.912; reader mass=783)
7. *March: Book Three (March, #3)* — John             Lewis (0.906; reader mass=355)
8. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.900; reader mass=423)
9. *Calvin and Hobbes* — Bill Watterson (0.900; reader mass=1390)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.899; reader mass=1351)
11. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=354)
12. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=452)
13. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.887; reader mass=293)
14. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.884; reader mass=313)
15. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.884; reader mass=254)
16. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.880; reader mass=343)
17. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.876; reader mass=521)
18. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.875; reader mass=626)
19. *The Hate U Give* — Angie Thomas (0.874; reader mass=1447)
20. *Yukon Ho!* — Bill Watterson (0.873; reader mass=264)
21. *The Absolute Sandman, Volume One* — Neil Gaiman (0.864; reader mass=437)
22. *The Revenge of the Baby-Sat* — Bill Watterson (0.864; reader mass=302)
23. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.860; reader mass=324)
24. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.857; reader mass=2408)
25. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.857; reader mass=2042)
26. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.856; reader mass=357)
27. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.856; reader mass=210)
28. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.856; reader mass=1026)
29. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.852; reader mass=899)
30. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.852; reader mass=1655)

### best_linear_q10 · beta=3.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.94851 | 0.9485 | 0.9052 | 0.445 |
| 2 | 0.97082 | 0.8485 | 0.6526 | 0.589 |
| 3 | 0.98829 | 0.7681 | 0.4707 | 0.623 |
| 4 | 0.99472 | 0.7139 | 0.3823 | 0.632 |
| 5 | 0.99713 | 0.6772 | 0.3397 | 0.635 |
| 6 | 0.99820 | 0.6511 | 0.3168 | 0.636 |
| 7 | 0.99878 | 0.6318 | 0.3029 | 0.637 |
| 8 | 0.99911 | 0.6168 | 0.2934 | 0.637 |
| 9 | 0.99928 | 0.6047 | 0.2862 | 0.638 |
| 10 | 0.99937 | 0.5944 | 0.2805 | 0.638 |
| 11 | 0.99949 | 0.5857 | 0.2758 | 0.638 |
| 12 | 0.99959 | 0.5784 | 0.2719 | 0.638 |
| 13 | 0.99968 | 0.5723 | 0.2688 | 0.638 |
| 14 | 0.99976 | 0.5672 | 0.2662 | 0.638 |
| 15 | 0.99982 | 0.5630 | 0.2641 | 0.638 |
| 16 | 0.99987 | 0.5597 | 0.2624 | 0.638 |
| 17 | 0.99992 | 0.5571 | 0.2611 | 0.638 |
| 18 | 0.99995 | 0.5551 | 0.2601 | 0.637 |
| 19 | 0.99996 | 0.5535 | 0.2594 | 0.637 |
| 20 | 0.99998 | 0.5523 | 0.2587 | 0.637 |

Final projected-direction head:

1. *1984* — George Orwell (direction=0.04977)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04184)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04100)
4. *Crossed (Matched, #2)* — Ally Condie (direction=0.03707)
5. *Animal Farm* — George Orwell (direction=0.03700)
6. *Matched (Matched, #1)* — Ally Condie (direction=0.03680)
7. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03637)
8. *To Kill a Mockingbird* — Harper Lee (direction=0.03617)
9. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03599)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03542)
11. *Watchmen* — Alan Moore (direction=0.03510)
12. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03466)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03427)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03401)
15. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03328)
16. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.03213)
17. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03121)
18. *The Hobbit* — J.R.R. Tolkien (direction=0.03118)
19. *Hamlet* — William Shakespeare (direction=0.03099)
20. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02982)
21. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (direction=0.02947)
22. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02943)
23. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02938)
24. *The Brothers Karamazov* — Fyodor Dostoyevsky (direction=0.02938)
25. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (direction=0.02918)
26. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (direction=0.02906)
27. *Macbeth* — William Shakespeare (direction=0.02882)
28. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02846)
29. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02841)
30. *Between the World and Me* — Ta-Nehisi Coates (direction=0.02812)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.952; reader mass=785)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.934; reader mass=2533)
3. *March: Book Two (March, #2)* — John             Lewis (0.923; reader mass=404)
4. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.920; reader mass=383)
5. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.917; reader mass=811)
6. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.913; reader mass=522)
7. *March: Book Three (March, #3)* — John             Lewis (0.909; reader mass=364)
8. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.903; reader mass=434)
9. *Calvin and Hobbes* — Bill Watterson (0.902; reader mass=1427)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.901; reader mass=1390)
11. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.889; reader mass=362)
12. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.889; reader mass=299)
13. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=259)
14. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=463)
15. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.887; reader mass=319)
16. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.884; reader mass=351)
17. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.881; reader mass=533)
18. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.881; reader mass=638)
19. *Yukon Ho!* — Bill Watterson (0.877; reader mass=268)
20. *The Hate U Give* — Angie Thomas (0.873; reader mass=1390)
21. *The Absolute Sandman, Volume One* — Neil Gaiman (0.865; reader mass=450)
22. *The Revenge of the Baby-Sat* — Bill Watterson (0.863; reader mass=309)
23. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.861; reader mass=331)
24. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.861; reader mass=2478)
25. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.860; reader mass=2065)
26. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.859; reader mass=214)
27. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.859; reader mass=365)
28. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.856; reader mass=1055)
29. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.853; reader mass=1287)
30. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.853; reader mass=1674)

### best_linear_mass_q10 · beta=1.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.96972 | 0.9697 | 0.9513 | 0.496 |
| 2 | 0.97710 | 0.8969 | 0.7431 | 0.714 |
| 3 | 0.98953 | 0.8284 | 0.5265 | 0.769 |
| 4 | 0.99524 | 0.7784 | 0.4087 | 0.780 |
| 5 | 0.99745 | 0.7429 | 0.3522 | 0.783 |
| 6 | 0.99842 | 0.7169 | 0.3231 | 0.783 |
| 7 | 0.99890 | 0.6969 | 0.3060 | 0.783 |
| 8 | 0.99917 | 0.6810 | 0.2948 | 0.783 |
| 9 | 0.99937 | 0.6681 | 0.2867 | 0.782 |
| 10 | 0.99952 | 0.6575 | 0.2806 | 0.782 |
| 11 | 0.99963 | 0.6487 | 0.2758 | 0.782 |
| 12 | 0.99971 | 0.6414 | 0.2720 | 0.782 |
| 13 | 0.99979 | 0.6355 | 0.2690 | 0.782 |
| 14 | 0.99985 | 0.6307 | 0.2666 | 0.782 |
| 15 | 0.99990 | 0.6269 | 0.2647 | 0.782 |
| 16 | 0.99994 | 0.6240 | 0.2633 | 0.782 |
| 17 | 0.99996 | 0.6217 | 0.2622 | 0.782 |
| 18 | 0.99997 | 0.6200 | 0.2613 | 0.782 |
| 19 | 0.99998 | 0.6186 | 0.2607 | 0.782 |
| 20 | 0.99999 | 0.6176 | 0.2601 | 0.782 |

Final projected-direction head:

1. *1984* — George Orwell (direction=0.04515)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04116)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04044)
4. *Crossed (Matched, #2)* — Ally Condie (direction=0.03515)
5. *Matched (Matched, #1)* — Ally Condie (direction=0.03510)
6. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03449)
7. *Watchmen* — Alan Moore (direction=0.03441)
8. *Animal Farm* — George Orwell (direction=0.03413)
9. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03397)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03376)
11. *To Kill a Mockingbird* — Harper Lee (direction=0.03252)
12. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03241)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03237)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03217)
15. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03160)
16. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03135)
17. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (direction=0.03073)
18. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.03038)
19. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (direction=0.03002)
20. *The Hobbit* — J.R.R. Tolkien (direction=0.02954)
21. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02934)
22. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02890)
23. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02878)
24. *ثلاثية غرناطة* — Radwa Ashour (direction=0.02844)
25. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02812)
26. *Hamlet* — William Shakespeare (direction=0.02797)
27. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02773)
28. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (direction=0.02768)
29. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02763)
30. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02753)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.945; reader mass=709)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.934; reader mass=2327)
3. *March: Book Two (March, #2)* — John             Lewis (0.917; reader mass=374)
4. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.911; reader mass=476)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.910; reader mass=354)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.902; reader mass=730)
7. *March: Book Three (March, #3)* — John             Lewis (0.899; reader mass=335)
8. *Calvin and Hobbes* — Bill Watterson (0.893; reader mass=1310)
9. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.893; reader mass=397)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.892; reader mass=1263)
11. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.886; reader mass=423)
12. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.883; reader mass=334)
13. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.880; reader mass=278)
14. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.877; reader mass=295)
15. *The Hate U Give* — Angie Thomas (0.877; reader mass=1557)
16. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.875; reader mass=241)
17. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.872; reader mass=323)
18. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.864; reader mass=491)
19. *Yukon Ho!* — Bill Watterson (0.863; reader mass=250)
20. *The Revenge of the Baby-Sat* — Bill Watterson (0.861; reader mass=285)
21. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.861; reader mass=593)
22. *The Absolute Sandman, Volume One* — Neil Gaiman (0.859; reader mass=406)
23. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.856; reader mass=305)
24. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.853; reader mass=954)
25. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.852; reader mass=2701)
26. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.850; reader mass=2257)
27. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.850; reader mass=834)
28. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.850; reader mass=1977)
29. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.849; reader mass=337)
30. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.848; reader mass=1216)

### best_linear_mass_q10 · beta=2.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.96034 | 0.9603 | 0.9259 | 0.466 |
| 2 | 0.97733 | 0.8817 | 0.6817 | 0.641 |
| 3 | 0.99070 | 0.8160 | 0.4821 | 0.680 |
| 4 | 0.99579 | 0.7701 | 0.3839 | 0.688 |
| 5 | 0.99771 | 0.7381 | 0.3381 | 0.689 |
| 6 | 0.99858 | 0.7150 | 0.3147 | 0.689 |
| 7 | 0.99901 | 0.6975 | 0.3009 | 0.689 |
| 8 | 0.99923 | 0.6837 | 0.2918 | 0.688 |
| 9 | 0.99939 | 0.6724 | 0.2852 | 0.688 |
| 10 | 0.99953 | 0.6630 | 0.2802 | 0.688 |
| 11 | 0.99963 | 0.6552 | 0.2762 | 0.688 |
| 12 | 0.99971 | 0.6487 | 0.2731 | 0.688 |
| 13 | 0.99977 | 0.6434 | 0.2705 | 0.688 |
| 14 | 0.99984 | 0.6390 | 0.2685 | 0.688 |
| 15 | 0.99989 | 0.6354 | 0.2669 | 0.688 |
| 16 | 0.99993 | 0.6326 | 0.2656 | 0.687 |
| 17 | 0.99995 | 0.6304 | 0.2647 | 0.687 |
| 18 | 0.99997 | 0.6288 | 0.2639 | 0.687 |
| 19 | 0.99998 | 0.6274 | 0.2633 | 0.687 |
| 20 | 0.99998 | 0.6264 | 0.2628 | 0.687 |

Final projected-direction head:

1. *1984* — George Orwell (direction=0.04800)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04181)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04091)
4. *Crossed (Matched, #2)* — Ally Condie (direction=0.03651)
5. *Matched (Matched, #1)* — Ally Condie (direction=0.03632)
6. *Animal Farm* — George Orwell (direction=0.03604)
7. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03550)
8. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03539)
9. *To Kill a Mockingbird* — Harper Lee (direction=0.03489)
10. *Watchmen* — Alan Moore (direction=0.03475)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03472)
12. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03357)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03350)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03331)
15. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03301)
16. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.03139)
17. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03136)
18. *The Hobbit* — J.R.R. Tolkien (direction=0.03053)
19. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (direction=0.03008)
20. *Hamlet* — William Shakespeare (direction=0.02992)
21. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02958)
22. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (direction=0.02957)
23. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02951)
24. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02883)
25. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02864)
26. *The Brothers Karamazov* — Fyodor Dostoyevsky (direction=0.02862)
27. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02836)
28. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (direction=0.02802)
29. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02798)
30. *Macbeth* — William Shakespeare (direction=0.02776)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.949; reader mass=760)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.935; reader mass=2474)
3. *March: Book Two (March, #2)* — John             Lewis (0.921; reader mass=394)
4. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.917; reader mass=375)
5. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.914; reader mass=508)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.912; reader mass=784)
7. *March: Book Three (March, #3)* — John             Lewis (0.906; reader mass=354)
8. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.901; reader mass=422)
9. *Calvin and Hobbes* — Bill Watterson (0.900; reader mass=1387)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.899; reader mass=1349)
11. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.889; reader mass=354)
12. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=451)
13. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.887; reader mass=293)
14. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.884; reader mass=312)
15. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.883; reader mass=254)
16. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.880; reader mass=343)
17. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.876; reader mass=521)
18. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.875; reader mass=625)
19. *The Hate U Give* — Angie Thomas (0.874; reader mass=1445)
20. *Yukon Ho!* — Bill Watterson (0.872; reader mass=263)
21. *The Revenge of the Baby-Sat* — Bill Watterson (0.864; reader mass=302)
22. *The Absolute Sandman, Volume One* — Neil Gaiman (0.864; reader mass=436)
23. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.860; reader mass=324)
24. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.857; reader mass=2404)
25. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.857; reader mass=2037)
26. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.856; reader mass=357)
27. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.856; reader mass=209)
28. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.856; reader mass=1024)
29. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.852; reader mass=899)
30. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.852; reader mass=1653)

### best_linear_mass_q10 · beta=3.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.95540 | 0.9554 | 0.9095 | 0.450 |
| 2 | 0.97753 | 0.8745 | 0.6491 | 0.601 |
| 3 | 0.99114 | 0.8100 | 0.4591 | 0.633 |
| 4 | 0.99600 | 0.7660 | 0.3697 | 0.638 |
| 5 | 0.99782 | 0.7358 | 0.3286 | 0.639 |
| 6 | 0.99864 | 0.7141 | 0.3077 | 0.639 |
| 7 | 0.99906 | 0.6979 | 0.2956 | 0.639 |
| 8 | 0.99926 | 0.6850 | 0.2875 | 0.639 |
| 9 | 0.99939 | 0.6745 | 0.2816 | 0.639 |
| 10 | 0.99952 | 0.6656 | 0.2770 | 0.639 |
| 11 | 0.99962 | 0.6583 | 0.2735 | 0.639 |
| 12 | 0.99970 | 0.6521 | 0.2706 | 0.639 |
| 13 | 0.99977 | 0.6470 | 0.2683 | 0.639 |
| 14 | 0.99982 | 0.6427 | 0.2664 | 0.638 |
| 15 | 0.99988 | 0.6392 | 0.2649 | 0.638 |
| 16 | 0.99992 | 0.6364 | 0.2637 | 0.638 |
| 17 | 0.99995 | 0.6342 | 0.2628 | 0.638 |
| 18 | 0.99996 | 0.6324 | 0.2620 | 0.638 |
| 19 | 0.99997 | 0.6311 | 0.2614 | 0.637 |
| 20 | 0.99998 | 0.6300 | 0.2610 | 0.637 |

Final projected-direction head:

1. *1984* — George Orwell (direction=0.04957)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04199)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04108)
4. *Crossed (Matched, #2)* — Ally Condie (direction=0.03712)
5. *Animal Farm* — George Orwell (direction=0.03704)
6. *Matched (Matched, #1)* — Ally Condie (direction=0.03683)
7. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03629)
8. *To Kill a Mockingbird* — Harper Lee (direction=0.03626)
9. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03600)
10. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03531)
11. *Watchmen* — Alan Moore (direction=0.03495)
12. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03456)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03414)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03390)
15. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03336)
16. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.03205)
17. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03124)
18. *The Hobbit* — J.R.R. Tolkien (direction=0.03112)
19. *Hamlet* — William Shakespeare (direction=0.03095)
20. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02983)
21. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (direction=0.02960)
22. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02952)
23. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02948)
24. *The Brothers Karamazov* — Fyodor Dostoyevsky (direction=0.02927)
25. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (direction=0.02927)
26. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (direction=0.02896)
27. *Macbeth* — William Shakespeare (direction=0.02884)
28. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02845)
29. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02842)
30. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02804)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.951; reader mass=784)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.935; reader mass=2536)
3. *March: Book Two (March, #2)* — John             Lewis (0.922; reader mass=402)
4. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.920; reader mass=382)
5. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.917; reader mass=812)
6. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.914; reader mass=521)
7. *March: Book Three (March, #3)* — John             Lewis (0.909; reader mass=363)
8. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.903; reader mass=433)
9. *Calvin and Hobbes* — Bill Watterson (0.902; reader mass=1424)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.901; reader mass=1388)
11. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.890; reader mass=362)
12. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.889; reader mass=298)
13. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=463)
14. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=259)
15. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.887; reader mass=319)
16. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.883; reader mass=351)
17. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.882; reader mass=533)
18. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.881; reader mass=637)
19. *Yukon Ho!* — Bill Watterson (0.876; reader mass=267)
20. *The Hate U Give* — Angie Thomas (0.873; reader mass=1388)
21. *The Absolute Sandman, Volume One* — Neil Gaiman (0.865; reader mass=450)
22. *The Revenge of the Baby-Sat* — Bill Watterson (0.864; reader mass=308)
23. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.861; reader mass=2474)
24. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.860; reader mass=331)
25. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.860; reader mass=2060)
26. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.859; reader mass=214)
27. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.858; reader mass=364)
28. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.856; reader mass=1053)
29. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.853; reader mass=1288)
30. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.853; reader mass=1673)

### best_preference_q10 · beta=1.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.96721 | 0.9672 | 0.9507 | 0.492 |
| 2 | 0.96953 | 0.8771 | 0.7414 | 0.710 |
| 3 | 0.98498 | 0.7866 | 0.5201 | 0.767 |
| 4 | 0.99323 | 0.7200 | 0.3955 | 0.779 |
| 5 | 0.99648 | 0.6729 | 0.3328 | 0.782 |
| 6 | 0.99794 | 0.6387 | 0.2987 | 0.783 |
| 7 | 0.99870 | 0.6132 | 0.2779 | 0.784 |
| 8 | 0.99911 | 0.5937 | 0.2639 | 0.784 |
| 9 | 0.99933 | 0.5783 | 0.2539 | 0.784 |
| 10 | 0.99944 | 0.5657 | 0.2462 | 0.785 |
| 11 | 0.99951 | 0.5551 | 0.2401 | 0.785 |
| 12 | 0.99956 | 0.5459 | 0.2351 | 0.785 |
| 13 | 0.99960 | 0.5380 | 0.2310 | 0.785 |
| 14 | 0.99966 | 0.5310 | 0.2275 | 0.785 |
| 15 | 0.99972 | 0.5249 | 0.2245 | 0.785 |
| 16 | 0.99977 | 0.5196 | 0.2220 | 0.785 |
| 17 | 0.99982 | 0.5151 | 0.2199 | 0.785 |
| 18 | 0.99986 | 0.5113 | 0.2181 | 0.785 |
| 19 | 0.99990 | 0.5081 | 0.2167 | 0.785 |
| 20 | 0.99993 | 0.5056 | 0.2155 | 0.785 |

Final projected-direction head:

1. *To Kill a Mockingbird* — Harper Lee (direction=0.04072)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04069)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04019)
4. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03406)
5. *1984* — George Orwell (direction=0.03393)
6. *Matched (Matched, #1)* — Ally Condie (direction=0.03341)
7. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03296)
8. *Crossed (Matched, #2)* — Ally Condie (direction=0.03288)
9. *Watchmen* — Alan Moore (direction=0.03261)
10. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03243)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03174)
12. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03126)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03084)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03074)
15. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02938)
16. *The Hobbit* — J.R.R. Tolkien (direction=0.02935)
17. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02864)
18. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.02853)
19. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02783)
20. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (direction=0.02779)
21. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (direction=0.02762)
22. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02750)
23. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02750)
24. *Between the World and Me* — Ta-Nehisi Coates (direction=0.02732)
25. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (direction=0.02698)
26. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02666)
27. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.02659)
28. *The Stand* — Stephen King (direction=0.02651)
29. *Passion (Fallen, #3)* — Lauren Kate (direction=0.02639)
30. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (direction=0.02609)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.944; reader mass=693)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.933; reader mass=2258)
3. *March: Book Two (March, #2)* — John             Lewis (0.920; reader mass=389)
4. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.911; reader mass=468)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.907; reader mass=346)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.904; reader mass=774)
7. *March: Book Three (March, #3)* — John             Lewis (0.901; reader mass=349)
8. *Calvin and Hobbes* — Bill Watterson (0.893; reader mass=1292)
9. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.892; reader mass=390)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.892; reader mass=1249)
11. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.885; reader mass=414)
12. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.882; reader mass=329)
13. *The Hate U Give* — Angie Thomas (0.881; reader mass=1707)
14. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.880; reader mass=273)
15. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.875; reader mass=289)
16. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.874; reader mass=317)
17. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.870; reader mass=234)
18. *The Absolute Sandman, Volume One* — Neil Gaiman (0.863; reader mass=398)
19. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.863; reader mass=485)
20. *The Revenge of the Baby-Sat* — Bill Watterson (0.860; reader mass=280)
21. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.860; reader mass=586)
22. *Yukon Ho!* — Bill Watterson (0.859; reader mass=245)
23. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.856; reader mass=2723)
24. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.856; reader mass=298)
25. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.853; reader mass=935)
26. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.852; reader mass=853)
27. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.850; reader mass=1303)
28. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.850; reader mass=2241)
29. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.849; reader mass=1960)
30. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.848; reader mass=332)

### best_preference_q10 · beta=2.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.95703 | 0.9570 | 0.9234 | 0.461 |
| 2 | 0.96990 | 0.8601 | 0.6752 | 0.636 |
| 3 | 0.98686 | 0.7737 | 0.4698 | 0.678 |
| 4 | 0.99415 | 0.7126 | 0.3651 | 0.688 |
| 5 | 0.99697 | 0.6700 | 0.3137 | 0.690 |
| 6 | 0.99825 | 0.6396 | 0.2859 | 0.692 |
| 7 | 0.99890 | 0.6171 | 0.2690 | 0.693 |
| 8 | 0.99925 | 0.6001 | 0.2577 | 0.693 |
| 9 | 0.99944 | 0.5868 | 0.2495 | 0.693 |
| 10 | 0.99954 | 0.5761 | 0.2434 | 0.694 |
| 11 | 0.99961 | 0.5673 | 0.2386 | 0.694 |
| 12 | 0.99964 | 0.5597 | 0.2347 | 0.694 |
| 13 | 0.99966 | 0.5531 | 0.2314 | 0.694 |
| 14 | 0.99967 | 0.5471 | 0.2286 | 0.695 |
| 15 | 0.99970 | 0.5418 | 0.2263 | 0.695 |
| 16 | 0.99975 | 0.5371 | 0.2242 | 0.695 |
| 17 | 0.99979 | 0.5329 | 0.2224 | 0.695 |
| 18 | 0.99982 | 0.5292 | 0.2209 | 0.695 |
| 19 | 0.99985 | 0.5259 | 0.2196 | 0.695 |
| 20 | 0.99989 | 0.5231 | 0.2184 | 0.694 |

Final projected-direction head:

1. *To Kill a Mockingbird* — Harper Lee (direction=0.04406)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04202)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04119)
4. *1984* — George Orwell (direction=0.03697)
5. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03569)
6. *Matched (Matched, #1)* — Ally Condie (direction=0.03502)
7. *Crossed (Matched, #2)* — Ally Condie (direction=0.03449)
8. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03360)
9. *Watchmen* — Alan Moore (direction=0.03262)
10. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03226)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03176)
12. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03160)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03131)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03120)
15. *Torment (Fallen, #2)* — Lauren Kate (direction=0.02994)
16. *The Hobbit* — J.R.R. Tolkien (direction=0.02959)
17. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02874)
18. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.02871)
19. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.02859)
20. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02854)
21. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02850)
22. *Between the World and Me* — Ta-Nehisi Coates (direction=0.02850)
23. *East of Eden* — John Steinbeck (direction=0.02800)
24. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02786)
25. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (direction=0.02740)
26. *All the Light We Cannot See* — Anthony Doerr (direction=0.02733)
27. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02720)
28. *Hamlet* — William Shakespeare (direction=0.02717)
29. *The Stand* — Stephen King (direction=0.02693)
30. *Dune (Dune Chronicles #1)* — Frank Herbert (direction=0.02677)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.950; reader mass=735)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.933; reader mass=2335)
3. *March: Book Two (March, #2)* — John             Lewis (0.924; reader mass=411)
4. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.914; reader mass=495)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.914; reader mass=362)
6. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.912; reader mass=835)
7. *March: Book Three (March, #3)* — John             Lewis (0.908; reader mass=370)
8. *Calvin and Hobbes* — Bill Watterson (0.900; reader mass=1355)
9. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.900; reader mass=410)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.898; reader mass=1321)
11. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=286)
12. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=438)
13. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.887; reader mass=344)
14. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.883; reader mass=334)
15. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.881; reader mass=302)
16. *The Hate U Give* — Angie Thomas (0.879; reader mass=1641)
17. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.875; reader mass=244)
18. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.875; reader mass=510)
19. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.872; reader mass=613)
20. *The Absolute Sandman, Volume One* — Neil Gaiman (0.870; reader mass=424)
21. *Yukon Ho!* — Bill Watterson (0.866; reader mass=256)
22. *The Revenge of the Baby-Sat* — Bill Watterson (0.863; reader mass=293)
23. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.861; reader mass=311)
24. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.857; reader mass=2370)
25. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.856; reader mass=996)
26. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.855; reader mass=921)
27. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.855; reader mass=1996)
28. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.855; reader mass=347)
29. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.854; reader mass=204)
30. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.852; reader mass=1609)

### best_preference_q10 · beta=3.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.95198 | 0.9520 | 0.9058 | 0.444 |
| 2 | 0.97036 | 0.8528 | 0.6407 | 0.596 |
| 3 | 0.98760 | 0.7686 | 0.4442 | 0.631 |
| 4 | 0.99451 | 0.7099 | 0.3482 | 0.639 |
| 5 | 0.99715 | 0.6694 | 0.3017 | 0.642 |
| 6 | 0.99835 | 0.6405 | 0.2767 | 0.644 |
| 7 | 0.99896 | 0.6193 | 0.2616 | 0.645 |
| 8 | 0.99929 | 0.6033 | 0.2515 | 0.646 |
| 9 | 0.99947 | 0.5909 | 0.2443 | 0.646 |
| 10 | 0.99958 | 0.5810 | 0.2388 | 0.647 |
| 11 | 0.99964 | 0.5728 | 0.2346 | 0.647 |
| 12 | 0.99969 | 0.5659 | 0.2311 | 0.647 |
| 13 | 0.99971 | 0.5599 | 0.2283 | 0.648 |
| 14 | 0.99971 | 0.5546 | 0.2259 | 0.648 |
| 15 | 0.99971 | 0.5497 | 0.2238 | 0.648 |
| 16 | 0.99974 | 0.5453 | 0.2220 | 0.648 |
| 17 | 0.99977 | 0.5413 | 0.2204 | 0.648 |
| 18 | 0.99980 | 0.5377 | 0.2190 | 0.648 |
| 19 | 0.99983 | 0.5345 | 0.2178 | 0.648 |
| 20 | 0.99986 | 0.5316 | 0.2167 | 0.648 |

Final projected-direction head:

1. *To Kill a Mockingbird* — Harper Lee (direction=0.04616)
2. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04263)
3. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04161)
4. *1984* — George Orwell (direction=0.03866)
5. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03652)
6. *Matched (Matched, #1)* — Ally Condie (direction=0.03573)
7. *Crossed (Matched, #2)* — Ally Condie (direction=0.03519)
8. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (direction=0.03402)
9. *Watchmen* — Alan Moore (direction=0.03268)
10. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (direction=0.03215)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (direction=0.03181)
12. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03169)
13. *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams (direction=0.03151)
14. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (direction=0.03141)
15. *Torment (Fallen, #2)* — Lauren Kate (direction=0.03018)
16. *The Hobbit* — J.R.R. Tolkien (direction=0.02973)
17. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.02959)
18. *East of Eden* — John Steinbeck (direction=0.02911)
19. *Between the World and Me* — Ta-Nehisi Coates (direction=0.02903)
20. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02894)
21. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (direction=0.02887)
22. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02878)
23. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02872)
24. *All the Light We Cannot See* — Anthony Doerr (direction=0.02854)
25. *Hamlet* — William Shakespeare (direction=0.02834)
26. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02796)
27. *Macbeth* — William Shakespeare (direction=0.02795)
28. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02792)
29. *Of Mice and Men* — John Steinbeck (direction=0.02732)
30. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (direction=0.02722)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.952; reader mass=753)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.932; reader mass=2340)
3. *March: Book Two (March, #2)* — John             Lewis (0.926; reader mass=419)
4. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.917; reader mass=366)
5. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.915; reader mass=865)
6. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.915; reader mass=503)
7. *March: Book Three (March, #3)* — John             Lewis (0.910; reader mass=378)
8. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.903; reader mass=417)
9. *Calvin and Hobbes* — Bill Watterson (0.902; reader mass=1383)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.900; reader mass=1350)
11. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.892; reader mass=289)
12. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=349)
13. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=447)
14. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.886; reader mass=339)
15. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.883; reader mass=306)
16. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.879; reader mass=519)
17. *The Hate U Give* — Angie Thomas (0.878; reader mass=1610)
18. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.878; reader mass=621)
19. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.877; reader mass=246)
20. *The Absolute Sandman, Volume One* — Neil Gaiman (0.872; reader mass=434)
21. *Yukon Ho!* — Bill Watterson (0.869; reader mass=259)
22. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.864; reader mass=314)
23. *The Revenge of the Baby-Sat* — Bill Watterson (0.862; reader mass=296)
24. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.861; reader mass=2429)
25. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.857; reader mass=2004)
26. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.857; reader mass=1019)
27. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.857; reader mass=207)
28. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.856; reader mass=351)
29. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.856; reader mass=956)
30. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.853; reader mass=1614)

### best_preference_delta_q10 · beta=1.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.96042 | 0.9604 | 0.9491 | 0.489 |
| 2 | 0.96443 | 0.8557 | 0.7180 | 0.717 |
| 3 | 0.98246 | 0.7528 | 0.4678 | 0.772 |
| 4 | 0.99221 | 0.6779 | 0.3294 | 0.782 |
| 5 | 0.99613 | 0.6258 | 0.2618 | 0.784 |
| 6 | 0.99784 | 0.5888 | 0.2264 | 0.784 |
| 7 | 0.99868 | 0.5618 | 0.2057 | 0.784 |
| 8 | 0.99912 | 0.5414 | 0.1923 | 0.783 |
| 9 | 0.99935 | 0.5255 | 0.1830 | 0.783 |
| 10 | 0.99949 | 0.5128 | 0.1760 | 0.783 |
| 11 | 0.99959 | 0.5023 | 0.1706 | 0.783 |
| 12 | 0.99966 | 0.4936 | 0.1663 | 0.783 |
| 13 | 0.99971 | 0.4861 | 0.1628 | 0.783 |
| 14 | 0.99975 | 0.4797 | 0.1599 | 0.784 |
| 15 | 0.99979 | 0.4742 | 0.1574 | 0.784 |
| 16 | 0.99982 | 0.4693 | 0.1553 | 0.784 |
| 17 | 0.99983 | 0.4649 | 0.1535 | 0.784 |
| 18 | 0.99984 | 0.4610 | 0.1519 | 0.784 |
| 19 | 0.99985 | 0.4573 | 0.1505 | 0.784 |
| 20 | 0.99986 | 0.4540 | 0.1492 | 0.784 |

Final projected-direction head:

1. *To Kill a Mockingbird* — Harper Lee (direction=0.04453)
2. *1984* — George Orwell (direction=0.04418)
3. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04289)
4. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04192)
5. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03683)
6. *Matched (Matched, #1)* — Ally Condie (direction=0.03477)
7. *Animal Farm* — George Orwell (direction=0.03443)
8. *Crossed (Matched, #2)* — Ally Condie (direction=0.03404)
9. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03228)
10. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03212)
11. *Torment (Fallen, #2)* — Lauren Kate (direction=0.03078)
12. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.02998)
13. *Watchmen* — Alan Moore (direction=0.02983)
14. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02957)
15. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02933)
16. *ثلاثية غرناطة* — Radwa Ashour (direction=0.02909)
17. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02886)
18. *Between the World and Me* — Ta-Nehisi Coates (direction=0.02869)
19. *Hamlet* — William Shakespeare (direction=0.02839)
20. *East of Eden* — John Steinbeck (direction=0.02739)
21. *Passion (Fallen, #3)* — Lauren Kate (direction=0.02723)
22. *Of Mice and Men* — John Steinbeck (direction=0.02710)
23. *Tempted (House of Night, #6)* — P.C. Cast (direction=0.02707)
24. *All the Light We Cannot See* — Anthony Doerr (direction=0.02702)
25. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02698)
26. *Macbeth* — William Shakespeare (direction=0.02685)
27. *The Brothers Karamazov* — Fyodor Dostoyevsky (direction=0.02665)
28. *Hunted (House of Night, #5)* — P.C. Cast (direction=0.02654)
29. *Untamed (House of Night, #4)* — P.C. Cast (direction=0.02641)
30. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (direction=0.02638)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.944; reader mass=665)
2. *March: Book Two (March, #2)* — John             Lewis (0.920; reader mass=398)
3. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.913; reader mass=454)
4. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.904; reader mass=789)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.903; reader mass=343)
6. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.901; reader mass=1468)
7. *March: Book Three (March, #3)* — John             Lewis (0.900; reader mass=358)
8. *Calvin and Hobbes* — Bill Watterson (0.893; reader mass=1263)
9. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.891; reader mass=1203)
10. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.891; reader mass=384)
11. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.888; reader mass=412)
12. *The Hate U Give* — Angie Thomas (0.882; reader mass=1736)
13. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.880; reader mass=265)
14. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.878; reader mass=322)
15. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.876; reader mass=311)
16. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.874; reader mass=284)
17. *Yukon Ho!* — Bill Watterson (0.863; reader mass=244)
18. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.861; reader mass=232)
19. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.857; reader mass=2693)
20. *The Absolute Sandman, Volume One* — Neil Gaiman (0.856; reader mass=388)
21. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.855; reader mass=899)
22. *The Revenge of the Baby-Sat* — Bill Watterson (0.855; reader mass=273)
23. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.855; reader mass=470)
24. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.851; reader mass=566)
25. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.851; reader mass=2241)
26. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.851; reader mass=860)
27. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.848; reader mass=322)
28. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.847; reader mass=1310)
29. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.842; reader mass=1149)
30. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.841; reader mass=1843)

### best_preference_delta_q10 · beta=2.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.94992 | 0.9499 | 0.9219 | 0.460 |
| 2 | 0.96467 | 0.8386 | 0.6497 | 0.644 |
| 3 | 0.98433 | 0.7401 | 0.4191 | 0.683 |
| 4 | 0.99309 | 0.6706 | 0.3029 | 0.690 |
| 5 | 0.99649 | 0.6225 | 0.2468 | 0.690 |
| 6 | 0.99802 | 0.5884 | 0.2170 | 0.690 |
| 7 | 0.99878 | 0.5635 | 0.1994 | 0.690 |
| 8 | 0.99917 | 0.5446 | 0.1878 | 0.690 |
| 9 | 0.99938 | 0.5298 | 0.1796 | 0.691 |
| 10 | 0.99952 | 0.5179 | 0.1734 | 0.691 |
| 11 | 0.99961 | 0.5082 | 0.1687 | 0.691 |
| 12 | 0.99966 | 0.5000 | 0.1648 | 0.691 |
| 13 | 0.99971 | 0.4930 | 0.1617 | 0.691 |
| 14 | 0.99976 | 0.4870 | 0.1590 | 0.691 |
| 15 | 0.99979 | 0.4817 | 0.1568 | 0.692 |
| 16 | 0.99982 | 0.4772 | 0.1549 | 0.692 |
| 17 | 0.99984 | 0.4731 | 0.1533 | 0.692 |
| 18 | 0.99985 | 0.4695 | 0.1519 | 0.692 |
| 19 | 0.99987 | 0.4662 | 0.1506 | 0.692 |
| 20 | 0.99988 | 0.4631 | 0.1495 | 0.692 |

Final projected-direction head:

1. *To Kill a Mockingbird* — Harper Lee (direction=0.04767)
2. *1984* — George Orwell (direction=0.04628)
3. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04374)
4. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04244)
5. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03799)
6. *Animal Farm* — George Orwell (direction=0.03600)
7. *Matched (Matched, #1)* — Ally Condie (direction=0.03589)
8. *Crossed (Matched, #2)* — Ally Condie (direction=0.03519)
9. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03366)
10. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03241)
11. *Torment (Fallen, #2)* — Lauren Kate (direction=0.03111)
12. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.03067)
13. *Hamlet* — William Shakespeare (direction=0.03017)
14. *Watchmen* — Alan Moore (direction=0.02994)
15. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02971)
16. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02946)
17. *Between the World and Me* — Ta-Nehisi Coates (direction=0.02940)
18. *Of Mice and Men* — John Steinbeck (direction=0.02913)
19. *East of Eden* — John Steinbeck (direction=0.02908)
20. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02895)
21. *All the Light We Cannot See* — Anthony Doerr (direction=0.02883)
22. *Macbeth* — William Shakespeare (direction=0.02870)
23. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02810)
24. *New Moon (Twilight, #2)* — Stephenie Meyer (direction=0.02802)
25. *The Brothers Karamazov* — Fyodor Dostoyevsky (direction=0.02785)
26. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (direction=0.02768)
27. *The Diary of a Young Girl* — Anne Frank (direction=0.02766)
28. *Tempted (House of Night, #6)* — P.C. Cast (direction=0.02731)
29. *Passion (Fallen, #3)* — Lauren Kate (direction=0.02721)
30. *Untamed (House of Night, #4)* — P.C. Cast (direction=0.02695)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.950; reader mass=700)
2. *March: Book Two (March, #2)* — John             Lewis (0.924; reader mass=422)
3. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.916; reader mass=480)
4. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.911; reader mass=851)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.909; reader mass=360)
6. *March: Book Three (March, #3)* — John             Lewis (0.906; reader mass=382)
7. *Calvin and Hobbes* — Bill Watterson (0.900; reader mass=1324)
8. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.899; reader mass=407)
9. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.897; reader mass=1268)
10. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.893; reader mass=437)
11. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.887; reader mass=277)
12. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.887; reader mass=1332)
13. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.885; reader mass=328)
14. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.883; reader mass=339)
15. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.882; reader mass=297)
16. *The Hate U Give* — Angie Thomas (0.879; reader mass=1679)
17. *Yukon Ho!* — Bill Watterson (0.873; reader mass=255)
18. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.867; reader mass=242)
19. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.865; reader mass=490)
20. *The Absolute Sandman, Volume One* — Neil Gaiman (0.863; reader mass=415)
21. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.862; reader mass=592)
22. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.861; reader mass=956)
23. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.859; reader mass=2366)
24. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.858; reader mass=338)
25. *The Revenge of the Baby-Sat* — Bill Watterson (0.857; reader mass=286)
26. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.853; reader mass=928)
27. *March: Book One (March, #1)* — John             Lewis (0.848; reader mass=664)
28. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.848; reader mass=196)
29. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.848; reader mass=1223)
30. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.847; reader mass=1386)

### best_preference_delta_q10 · beta=3.5

| iteration | step corr | direction from start | user weights from start | effective user share |
|---:|---:|---:|---:|---:|
| 1 | 0.94468 | 0.9447 | 0.9046 | 0.445 |
| 2 | 0.96503 | 0.8311 | 0.6150 | 0.604 |
| 3 | 0.98510 | 0.7349 | 0.3955 | 0.636 |
| 4 | 0.99342 | 0.6679 | 0.2889 | 0.640 |
| 5 | 0.99662 | 0.6217 | 0.2378 | 0.641 |
| 6 | 0.99808 | 0.5889 | 0.2106 | 0.641 |
| 7 | 0.99881 | 0.5648 | 0.1944 | 0.641 |
| 8 | 0.99918 | 0.5466 | 0.1836 | 0.642 |
| 9 | 0.99938 | 0.5323 | 0.1760 | 0.642 |
| 10 | 0.99951 | 0.5208 | 0.1703 | 0.643 |
| 11 | 0.99960 | 0.5113 | 0.1658 | 0.643 |
| 12 | 0.99966 | 0.5034 | 0.1622 | 0.643 |
| 13 | 0.99971 | 0.4965 | 0.1592 | 0.643 |
| 14 | 0.99975 | 0.4907 | 0.1567 | 0.644 |
| 15 | 0.99978 | 0.4856 | 0.1546 | 0.644 |
| 16 | 0.99982 | 0.4811 | 0.1529 | 0.644 |
| 17 | 0.99984 | 0.4772 | 0.1513 | 0.644 |
| 18 | 0.99987 | 0.4737 | 0.1500 | 0.644 |
| 19 | 0.99987 | 0.4705 | 0.1488 | 0.644 |
| 20 | 0.99988 | 0.4675 | 0.1477 | 0.644 |

Final projected-direction head:

1. *To Kill a Mockingbird* — Harper Lee (direction=0.04946)
2. *1984* — George Orwell (direction=0.04747)
3. *Fallen (Fallen, #1)* — Lauren Kate (direction=0.04405)
4. *Evermore (The Immortals, #1)* — Alyson Noel (direction=0.04260)
5. *Marked (House of Night, #1)* — P.C. Cast (direction=0.03858)
6. *Animal Farm* — George Orwell (direction=0.03685)
7. *Matched (Matched, #1)* — Ally Condie (direction=0.03637)
8. *Crossed (Matched, #2)* — Ally Condie (direction=0.03571)
9. *Crime and Punishment* — Fyodor Dostoyevsky (direction=0.03444)
10. *Blue Moon (The Immortals, #2)* — Alyson Noel (direction=0.03240)
11. *Torment (Fallen, #2)* — Lauren Kate (direction=0.03124)
12. *Hamlet* — William Shakespeare (direction=0.03123)
13. *Beautiful Creatures (Caster Chronicles, #1)* — Kami Garcia (direction=0.03092)
14. *Of Mice and Men* — John Steinbeck (direction=0.03028)
15. *Watchmen* — Alan Moore (direction=0.03001)
16. *East of Eden* — John Steinbeck (direction=0.02996)
17. *Betrayed (House of Night, #2)* — P.C. Cast (direction=0.02985)
18. *All the Light We Cannot See* — Anthony Doerr (direction=0.02980)
19. *Macbeth* — William Shakespeare (direction=0.02975)
20. *Between the World and Me* — Ta-Nehisi Coates (direction=0.02970)
21. *Shadowland (The Immortals, #3)* — Alyson Noel (direction=0.02933)
22. *Chosen (House of Night, #3)* — P.C. Cast (direction=0.02889)
23. *New Moon (Twilight, #2)* — Stephenie Meyer (direction=0.02877)
24. *The Diary of a Young Girl* — Anne Frank (direction=0.02876)
25. *The Short Second Life of Bree Tanner (Twilight, #3.5)* — Stephenie Meyer (direction=0.02867)
26. *The Brothers Karamazov* — Fyodor Dostoyevsky (direction=0.02845)
27. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (direction=0.02836)
28. *Charlotte's Web* — E.B. White (direction=0.02775)
29. *The Handmaid's Tale* — Margaret Atwood (direction=0.02739)
30. *Unbroken: A World War II Story of Survival, Resilience, and Redemption* — Laura Hillenbrand (direction=0.02739)

Final ordinary-approval head:

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.952; reader mass=716)
2. *March: Book Two (March, #2)* — John             Lewis (0.925; reader mass=431)
3. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.916; reader mass=491)
4. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.914; reader mass=880)
5. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.912; reader mass=366)
6. *March: Book Three (March, #3)* — John             Lewis (0.908; reader mass=392)
7. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.902; reader mass=416)
8. *Calvin and Hobbes* — Bill Watterson (0.902; reader mass=1353)
9. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.899; reader mass=1296)
10. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.894; reader mass=446)
11. *Scientific Progress Goes "Boink": A Calvin and Hobbes Collection* — Bill Watterson (0.890; reader mass=281)
12. *There's Treasure Everywhere: A Calvin and Hobbes Collection* — Bill Watterson (0.889; reader mass=334)
13. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.885; reader mass=301)
14. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.883; reader mass=346)
15. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.878; reader mass=1258)
16. *The Hate U Give* — Angie Thomas (0.877; reader mass=1649)
17. *Yukon Ho!* — Bill Watterson (0.877; reader mass=259)
18. *Something Under the Bed is Drooling: A Calvin and Hobbes Collection* — Bill Watterson (0.871; reader mass=244)
19. *Locke & Key, Vol. 5: Clockworks* — Joe Hill (0.869; reader mass=496)
20. *The Calvin and Hobbes Tenth Anniversary Book* — Bill Watterson (0.867; reader mass=601)
21. *The Absolute Sandman, Volume One* — Neil Gaiman (0.867; reader mass=426)
22. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.863; reader mass=2424)
23. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.863; reader mass=979)
24. *The Calvin and Hobbes Lazy Sunday Book* — Bill Watterson (0.862; reader mass=343)
25. *The Revenge of the Baby-Sat* — Bill Watterson (0.857; reader mass=290)
26. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.854; reader mass=962)
27. *March: Book One (March, #1)* — John             Lewis (0.853; reader mass=679)
28. *The Absolute Sandman, Volume Two* — Neil Gaiman (0.852; reader mass=199)
29. *Brief Lives (The Sandman #7)* — Neil Gaiman (0.850; reader mass=1013)
30. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.850; reader mass=1255)

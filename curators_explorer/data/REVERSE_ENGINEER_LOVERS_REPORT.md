# Reverse-engineering classic lovers

Seed-informed analysis (confirmation bias risk is real and acknowledged).
Seeds = `poll_works` with **n ≥ 2000**, split odd/even `poll_rank` into train/test. Lovers = users with ≥k distinct **5★ train seeds**.

## Seeds

- #1 [train] Moby-Dick — Herman Melville (n=31475)
- #2 [test] The Brothers Karamazov — Fyodor Dostoevsky (n=15001)
- #3 [train] Lolita — Vladimir Nabokov (n=47579)
- #4 [test] Crime and Punishment — Fyodor Dostoevsky (n=37267)
- #5 [train] Ulysses — James Joyce (n=8443)
- #6 [test] Infinite Jest — David Foster Wallace (n=4598)
- #7 [train] Don Quixote — Miguel de Cervantes (n=15298)
- #8 [test] Blood Meridian — Cormac McCarthy (n=6348)
- #9 [train] Gravity's Rainbow — Thomas Pynchon (n=2385)
- #11 [train] Stoner — John Williams (n=6637)
- #12 [test] The Stranger — Albert Camus (n=43833)
- #13 [train] The Divine Comedy — Dante Alighieri (n=10670)

## Cohort contrast (train lovers vs n_rated-matched controls)

| feature | lover | control | Δ | Cohen d |
|---|---:|---:|---:|---:|
| n_authors_5 | 159.9 | 95.6 | +64.28 | +0.46 |
| n5 | 108.4 | 59.25 | +49.14 | +0.37 |
| n_rated | 286.4 | 182.7 | +103.7 | +0.35 |
| five_rate | 0.4352 | 0.3682 | +0.06696 | +0.32 |
| p5_blockbuster | 0.475 | 0.4084 | +0.06657 | +0.31 |
| mean_rating | 4.108 | 4.002 | +0.1065 | +0.26 |
| author_diversity_5 | 1.881 | 2.858 | -0.9766 | -0.21 |
| depth_ge4 | 0.1298 | 0.1322 | -0.002442 | -0.12 |
| mean_logn_5 | 8.663 | 8.532 | +0.1305 | +0.11 |

## Held-out recovery (train lovers → rank books, drop train seeds)

- test seeds in top 50 / 100 / 200 / 500: **1** / 4 / **8** / 13 (of 39)
- test recall@200: 0.20512820512820512
- test median rank: 517
- vs literary_poll works: pos50=5 anti50=9 Q=-68.06

### Top 30 excluding train seeds

- 1. Words of Radiance (The Stormlight Archive, #2) — Brandon Sanderson (n≈1041)
- 2. Tutunamayanlar — Oguz Atay (n≈322)
- 3. The Return of the King (The Lord of the Rings, #3) — J.R.R. Tolkien (n≈10850)
- 4. Tehlikeli Oyunlar — Oguz Atay (n≈181)
- 5. Le Monogramme — Odysseus Elytis (n≈103)
- 6. The Knight in the Panther's Skin — Shota Rustaveli (n≈108)
- 7. The Fellowship of the Ring (The Lord of the Rings, #1) — J.R.R. Tolkien (n≈20420) [TEST-SEED]
- 8. The Hate U Give — Angie Thomas (n≈807)
- 9. Мастер и Маргарита. Собачье сердце — Mikhail Bulgakov (n≈71) [poll-work]
- 10. The Essential Neruda: Selected Poems — Pablo Neruda (n≈203)
- 11. Двенадцать стульев / Золотой телёнок — Ilya Ilf (n≈110)
- 12. The Two Towers (The Lord of the Rings, #2) — J.R.R. Tolkien (n≈11149)
- 13. Checkmate (The Lymond Chronicles, #6) — Dorothy Dunnett (n≈97)
- 14. The Last Question — Isaac Asimov (n≈363)
- 15. Puslu Kıtalar Atlası — Ihsan Oktay Anar (n≈433)
- 16. A Game of Thrones: The Book of Ice and Fire RPG rulebook — Simone Cooper (n≈63)
- 17. Ježeva kućica — Branko Copic (n≈111)
- 18. Harry Potter and the Order of the Phoenix (Harry Potter, #5, Part 1) — J.K. Rowling (n≈126)
- 19. The Hitchhiker's Guide to the Galaxy: A Trilogy in Four Parts — Douglas Adams (n≈539)
- 20. The Green Mile, Part 6: Coffey on the Mile — Stephen King (n≈285)
- 21. Cuentos completos 1 — Julio Cortazar (n≈155)
- 22. Rita Hayworth and Shawshank Redemption: A Story from Different Seasons — Stephen King (n≈372)
- 23. The Fortress — Mesa Selimovic (n≈108)
- 24. The Moonlight Sonata — Yiannis Ritsos (n≈75)
- 25. Assassin's Fate (The Fitz and the Fool, #3) — Robin Hobb (n≈143)
- 26. The Poetry of Pablo Neruda — Pablo Neruda (n≈500)
- 27. The Essential Rumi — Jalaluddin Mevlana Rumi (n≈730)
- 28. The Way of Kings (The Stormlight Archive, #1) — Brandon Sanderson (n≈1607)
- 29. Time Regained (In Search of Lost Time, #7) — Marcel Proust (n≈258) [poll-work]
- 30. The Dark Tower Series Collection: The Gunslinger, The Drawing of the Three, The Waste Lands, Wizard and Glass, Wolves of the Calla, Song of Susannah, The Dark Tower — Stephen King (n≈138)

## Emergent non-seed likes (train lovers)

- 1. Words of Radiance (The Stormlight Archive, #2) — Brandon Sanderson (bayes_p5=0.735, lovers_n=1041, catalog_n=10709)
- 2. Tutunamayanlar — Oguz Atay (bayes_p5=0.734, lovers_n=322, catalog_n=965)
- 3. The Return of the King (The Lord of the Rings, #3) — J.R.R. Tolkien (bayes_p5=0.732, lovers_n=10850, catalog_n=49797)
- 4. Tehlikeli Oyunlar — Oguz Atay (bayes_p5=0.727, lovers_n=181, catalog_n=491)
- 5. Le Monogramme — Odysseus Elytis (bayes_p5=0.718, lovers_n=103, catalog_n=295)
- 6. The Knight in the Panther's Skin — Shota Rustaveli (bayes_p5=0.714, lovers_n=108, catalog_n=191)
- 7. The Hate U Give — Angie Thomas (bayes_p5=0.702, lovers_n=807, catalog_n=11481)
- 8. Мастер и Маргарита. Собачье сердце — Mikhail Bulgakov (bayes_p5=0.698, lovers_n=71, catalog_n=141)
- 9. The Essential Neruda: Selected Poems — Pablo Neruda (bayes_p5=0.680, lovers_n=203, catalog_n=551)
- 10. Двенадцать стульев / Золотой телёнок — Ilya Ilf (bayes_p5=0.675, lovers_n=110, catalog_n=231)
- 11. The Two Towers (The Lord of the Rings, #2) — J.R.R. Tolkien (bayes_p5=0.674, lovers_n=11149, catalog_n=52144)
- 12. Checkmate (The Lymond Chronicles, #6) — Dorothy Dunnett (bayes_p5=0.673, lovers_n=97, catalog_n=362)
- 13. The Last Question — Isaac Asimov (bayes_p5=0.673, lovers_n=363, catalog_n=1568)
- 14. Puslu Kıtalar Atlası — Ihsan Oktay Anar (bayes_p5=0.673, lovers_n=433, catalog_n=1568)
- 15. A Game of Thrones: The Book of Ice and Fire RPG rulebook — Simone Cooper (bayes_p5=0.672, lovers_n=63, catalog_n=440)
- 16. Ježeva kućica — Branko Copic (bayes_p5=0.670, lovers_n=111, catalog_n=254)
- 17. Harry Potter and the Order of the Phoenix (Harry Potter, #5, Part 1) — J.K. Rowling (bayes_p5=0.670, lovers_n=126, catalog_n=1653)
- 18. The Hitchhiker's Guide to the Galaxy: A Trilogy in Four Parts — Douglas Adams (bayes_p5=0.669, lovers_n=539, catalog_n=2031)
- 19. The Green Mile, Part 6: Coffey on the Mile — Stephen King (bayes_p5=0.668, lovers_n=285, catalog_n=1569)
- 20. Cuentos completos 1 — Julio Cortazar (bayes_p5=0.668, lovers_n=155, catalog_n=399)
- 21. Rita Hayworth and Shawshank Redemption: A Story from Different Seasons — Stephen King (bayes_p5=0.665, lovers_n=372, catalog_n=1766)
- 22. The Fortress — Mesa Selimovic (bayes_p5=0.663, lovers_n=108, catalog_n=264)
- 23. The Moonlight Sonata — Yiannis Ritsos (bayes_p5=0.662, lovers_n=75, catalog_n=181)
- 24. Assassin's Fate (The Fitz and the Fool, #3) — Robin Hobb (bayes_p5=0.662, lovers_n=143, catalog_n=1299)
- 25. The Poetry of Pablo Neruda — Pablo Neruda (bayes_p5=0.661, lovers_n=500, catalog_n=1362)

## Hit-threshold sweep

| k | n_lovers | test@50 | test@200 | recall@200 | med_rank | Q |
|---|---:|---:|---:|---:|---:|---:|
| 2 | 83391 | 1 | 4 | 10.26% | 724 | -88.6 |
| 3 | 43490 | 1 | 8 | 20.51% | 517 | -68.1 |
| 4 | 24118 | 5 | 10 | 25.64% | 391 | -27.5 |
| 5 | 14112 | 5 | 15 | 38.46% | 242 | -12.7 |
| 8 | 3420 | 9 | 28 | 71.79% | 80 | 26.1 |

## Ratings-only proxy (no seed hits in membership)

Top 5% users by z-scored signature copied from lover−control directions (`five_rate`, `p5_blockbuster`, `mean_logn_5`). n=20390.
- all seeds in top 50/200/500: 0 / 1 / 4
- literary_poll pos50/anti50/Q: 0 / 47 / -460.18

Proxy top 12:

- 1. Harry Potter and the Deathly Hallows (Harry Potter, #7) — J.K. Rowling
- 2. Harry Potter and the Half-Blood Prince (Harry Potter, #6) — J.K. Rowling
- 3. Harry Potter and the Goblet of Fire (Harry Potter, #4) — J.K. Rowling
- 4. Harry Potter and the Prisoner of Azkaban (Harry Potter, #3) — J.K. Rowling
- 5. A Court of Mist and Fury (A Court of Thorns and Roses, #2) — Sarah J. Maas
- 6. Harry Potter and the Order of the Phoenix (Harry Potter, #5) — J.K. Rowling
- 7. The Last Olympian (Percy Jackson and the Olympians, #5) — Rick Riordan
- 8. Lover Awakened (Black Dagger Brotherhood, #3) — J.R. Ward
- 9. Harry Potter and the Chamber of Secrets (Harry Potter, #2) — J.K. Rowling
- 10. Clockwork Princess (The Infernal Devices, #3) — Cassandra Clare
- 11. Harry Potter and the Sorcerer's Stone (Harry Potter, #1) — J.K. Rowling
- 12. Queen of Shadows (Throne of Glass, #4) — Sarah J. Maas

## Takeaways

1. **Strict classic-lovers are real and recoverable — soft ones are not.**  
   Users with ≥8 distinct 5★ on *train* poll seeds (n=3,420) put **28/39 test seeds in top 200** (recall 72%, median rank 80), and score **pos50=17, anti50=0, Q≈26** on literary_poll works — far above any ratings-only method so far. At ≥3 hits the same recipe is weak (1 test seed @50).

2. **Their ratings-only “personality” is not picky-niche.** vs n_rated-matched controls they have *higher* five_rate (d≈+0.32), *higher* blockbuster 5★ rate (d≈+0.31), more authors touched, slightly *lower* rarity-depth. They look like **enthusiastic omnivores who also hammer the classics**, not anti-blockbuster snobs. That explains why `anti_blockbuster_picky` only weakly overlapped the poll.

3. **Confirmation bias check (seed-free proxy) fails hard.** Copying the lover−control signature (high five_rate / high blockbuster / …) into a top-5% proxy with **no seed hits** yields Potter/Maas heads and essentially **zero** seed recovery. The discriminative bit is *engagement with the classics themselves*, not the generic correlates.

4. **Emergent cluster around hard lovers** mixes high fantasy (Sanderson, Tolkien), Turkish/Greek/Georgian/Persian consecrated works (Atay, Elytis, Rustaveli, Shahnameh), Bulgakov, Dunnett — a “serious + multilingual + epic” neighborhood, not romance islands.

5. **Practical implication for identifying the cohort:**  
   - Seed- or pack-conditioned membership (deep curator / lit hits) is doing real work; pure behavioral proxies of “picky” or “deep” fight the actual signature.  
   - If avoiding full lit piles: require **multi-hit** on a *small* held-in classic core (or deep-poll), then rank — odd/even split shows this generalizes to held-out classics.  
   - Do not expect reflections/PMI alone to find these users; they are not a dense co-liking island in the mid-pop graph the way romance is.

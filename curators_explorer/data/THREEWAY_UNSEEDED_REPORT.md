# Three-way cohorts + unseeded classic-focus scorer

Seeds label cohorts for contrast/fitting only. Book ranking at inference uses **unseeded** user features from `(user, rating, work, author[, year])`.

## Takeaways

1. **Three-way split is sharp.** Classics vs anti is mostly **anti-series / anti-binge / older books**. Classics vs normie is mostly **less mega-blockbuster mass + more mid-pop author span**. Those are the levers.
2. **Simple affinity ranking still leaks romance** until you gate (series/mega/binge) and subtract anti/normie raw scores.
3. **Best unseeded metric so far:** contrastive `P(5|classic_focus_top) − P(5|anti_like_top)` → **Q≈72, pos50=22, anti50=0**, head = Ulysses / Moby-Dick / Paradise Lost / Hamlet / Mrs Dalloway / Lolita / C&P. Beats the seeded exclusive-cohort oracle (Q≈50) on the literary_poll probe.
4. Feature weights were fit using seed-labeled cohorts; inference user scores use **no seed hit counts**. Treat as a complex working metric to simplify later.

## Cohorts (exclusive primary)

- classic: 31,803 (≥6 classic 5★, classic≥anti, classic≥normie)
- anti: 221,879 (≥10 anti 5★, anti>classic)
- normie: 33,571 (≥4 normie 5★, normie>classic, anti low)

## Feature means & classic vs anti / normie

| feature | classic | anti | normie | d_anti | d_normie | both? |
|---|---:|---:|---:|---:|---:|---|
| mean_pub_year_5 | 1969 | 1999 | 1975 | -1.853 | -0.3944 | YES |
| series_share_5 | 0.1707 | 0.6077 | 0.2799 | -1.549 | -0.3873 | YES |
| mega_catalog_share_5 | 0.1626 | 0.2173 | 0.315 | -0.342 | -0.9521 | YES |
| mean_logn_5 | 8.476 | 8.888 | 9.245 | -0.3369 | -0.6292 | YES |
| depth_ge4 | 0.1327 | 0.1256 | 0.1218 | 0.3252 | 0.5031 | YES |
| midpop_span_per_logn5 | 6.771 | 5.688 | 4.635 | 0.3139 | 0.6194 | YES |
| author_hhi_5 | 0.04327 | 0.07425 | 0.05955 | -0.4363 | -0.2294 | YES |
| n_midpop_authors_5 | 29.67 | 25.97 | 17.81 | 0.1839 | 0.5899 | YES |
| n_authors_5 | 53.2 | 46.7 | 33.08 | 0.1338 | 0.4143 | YES |
| singleton_author_share_5 | 0.7903 | 0.6685 | 0.8408 | 0.7401 | -0.307 |  |
| author_div_5 | 0.7502 | 0.557 | 0.8026 | 0.9189 | -0.2491 |  |
| n5 | 75.26 | 92.38 | 43.12 | -0.1776 | 0.3333 |  |
| binge_max_5 | 6.352 | 11.05 | 4.798 | -0.5265 | 0.174 |  |
| mean_rating | 4.049 | 4.141 | 3.986 | -0.2245 | 0.1553 |  |
| five_rate | 0.3977 | 0.4464 | 0.3674 | -0.2315 | 0.1439 |  |
| p5_blockbuster | 0.4339 | 0.4968 | 0.4041 | -0.2887 | 0.1371 |  |
| binge_mean_5 | 1.431 | 2.108 | 1.327 | -0.6888 | 0.106 |  |
| n_rated | 230.2 | 245 | 148.1 | -0.0594 | 0.3289 |  |
| mid_catalog_share_5 | 0.4401 | 0.4489 | 0.3501 | -0.05272 | 0.5381 |  |
| std_logn_5 | 2.056 | 1.889 | 2.037 | 0.377 | 0.04197 |  |
| n_megastar_authors_5 | 9.475 | 9.545 | 9.787 | -0.01196 | -0.05321 |  |
| midpop_author_frac_5 | 0.5844 | 0.5857 | 0.5357 | -0.008041 | 0.301 |  |

## Unseeded affinity (classic_raw − λ·anti_raw − λ·normie_raw)

- classic: focus=+10.727 classic_raw=+6.061 anti_raw=-4.805 normie_raw=-0.775
- anti: focus=-4.764 classic_raw=-2.166 anti_raw=+2.354 normie_raw=+0.796
- normie: focus=+3.810 classic_raw=+1.779 anti_raw=-4.223 normie_raw=+2.078

Classic terms:

- `series_share_5`: -1.50
- `mean_pub_year_5`: -1.40
- `mega_catalog_share_5`: -1.30
- `midpop_span_per_logn5`: +1.20
- `mean_logn_5`: -1.00
- `depth_ge4`: +0.90
- `author_hhi_5`: -0.80
- `binge_mean_5`: -0.70
- `singleton_author_share_5`: +0.60
- `mid_catalog_share_5`: +0.50
- `author_div_5`: +0.50
- `std_logn_5`: +0.40

Anti terms:

- `series_share_5`: +1.60
- `binge_mean_5`: +1.20
- `author_hhi_5`: +1.00
- `mean_pub_year_5`: +1.00
- `binge_max_5`: +0.80
- `singleton_author_share_5`: -0.80
- `author_div_5`: -0.60

Normie terms:

- `mega_catalog_share_5`: +1.50
- `mean_logn_5`: +1.30
- `p5_blockbuster`: +0.80
- `midpop_span_per_logn5`: -0.70
- `n_megastar_authors_5`: +0.60
- `depth_ge4`: -0.50

λ_anti=0.85 λ_normie=0.75

Gated top ~8% overlap: classic recall=13.09%, anti recall=0.42%, normie recall=1.35% (frac of top classic=46.34%)

## Book ranking results

| method | Q | pos50 | anti50 | classic50 | normie50 | test50 | test200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| unseeded_gated_weighted | 21.7 | 8 | 0 | 2 | 1 | 2 | 8 |
| unseeded_gated_top8_hard | 29.5 | 10 | 0 | 7 | 2 | 4 | 16 |
| unseeded_gated_top4 | 27.1 | 11 | 0 | 7 | 2 | 4 | 12 |
| unseeded_contrastive | 71.8 | 22 | 0 | 22 | 6 | 7 | 13 |
| seeded_classic_oracle | 50.4 | 15 | 0 | 11 | 3 | 8 | 17 |

## Top 15 by method

### unseeded_gated_weighted
- 1. The Hate U Give — Angie Thomas (n≈226)
- 2. Duino Elegies and The Sonnets to Orpheus — Rainer Maria Rilke (n≈34)
- 3. The Book of Disquiet — Fernando Pessoa (n≈237)
- 4. Refugee — Alan Gratz (n≈29)
- 5. The War that Saved My Life (The War That Saved My Life #1) — Kimberly Brubaker Bradley (n≈173)
- 6. Geography III — Elizabeth Bishop (n≈58)
- 7. Life and Fate — Vasily Grossman (n≈130)
- 8. The Selected Poetry of Rainer Maria Rilke — Rainer Maria Rilke (n≈218)
- 9. The Selected Poems — Osip Mandelstam (n≈37)
- 10. Residence on Earth — Pablo Neruda (n≈42)
- 11. The Essential Neruda: Selected Poems — Pablo Neruda (n≈77)
- 12. Poems of Paul Celan — Paul Celan (n≈116)
- 13. A Monster Calls — Patrick Ness (n≈220)
- 14. الساعة الخامسة والعشرون — Constantin Virgil Gheorghiu (n≈34)
- 15. Complete Poems and Selected Letters — John Keats (n≈55)

### unseeded_gated_top8_hard
- 1. The Hate U Give — Angie Thomas (n≈365)
- 2. The Book of Disquiet — Fernando Pessoa (n≈402)
- 3. The Selected Poetry of Rainer Maria Rilke — Rainer Maria Rilke (n≈308)
- 4. The War that Saved My Life (The War That Saved My Life #1) — Kimberly Brubaker Bradley (n≈254)
- 5. Life and Fate — Vasily Grossman (n≈158)
- 6. The Brothers Karamazov — Fyodor Dostoyevsky (n≈1861)
- 7. Hamlet — William Shakespeare (n≈2549)
- 8. A Monster Calls — Patrick Ness (n≈424)
- 9. A Season in Hell/The Drunken Boat — Arthur Rimbaud (n≈235)
- 10. In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust (n≈227)
- 11. Complete Poems and Selected Letters — John Keats (n≈71)
- 12. Crime and Punishment — Fyodor Dostoyevsky (n≈2781)
- 13. Four Quartets — T.S. Eliot (n≈392)
- 14. The Essential Rumi — Jalaluddin Mevlana Rumi (n≈374)
- 15. Poems of Paul Celan — Paul Celan (n≈150)

### unseeded_gated_top4
- 1. The Hate U Give — Angie Thomas (n≈109)
- 2. The War that Saved My Life (The War That Saved My Life #1) — Kimberly Brubaker Bradley (n≈93)
- 3. The Book of Disquiet — Fernando Pessoa (n≈133)
- 4. Geography III — Elizabeth Bishop (n≈41)
- 5. A Monster Calls — Patrick Ness (n≈101)
- 6. The Selected Poetry of Rainer Maria Rilke — Rainer Maria Rilke (n≈137)
- 7. Complete Poems, 1904-1962 — E.E. Cummings (n≈64)
- 8. Peter Pan (A Little Golden Book) — Eugene Bradley Coco (n≈59)
- 9. The Essential Rumi — Jalaluddin Mevlana Rumi (n≈101)
- 10. Hamlet — William Shakespeare (n≈966)
- 11. Paradise Lost and Paradise Regained — John Milton (n≈50)
- 12. Four Quartets — T.S. Eliot (n≈193)
- 13. Life and Fate — Vasily Grossman (n≈94)
- 14. Poems of Paul Celan — Paul Celan (n≈86)
- 15. The Man Without Qualities — Robert Musil (n≈41)

### unseeded_contrastive
- 1. Ulysses — James Joyce (n≈37)
- 2. Moby-Dick or, The Whale — Herman Melville (n≈300)
- 3. Paradise Lost — John Milton (n≈43)
- 4. Hamlet — William Shakespeare (n≈427)
- 5. Mrs. Dalloway — Virginia Woolf (n≈40)
- 6. Lolita — Vladimir Nabokov (n≈138)
- 7. Crime and Punishment — Fyodor Dostoyevsky (n≈123)
- 8. Macbeth — William Shakespeare (n≈373)
- 9. A Streetcar Named Desire — Tennessee Williams (n≈63)
- 10. The Trial — Franz Kafka (n≈31)
- 11. The Poisonwood Bible — Barbara Kingsolver (n≈105)
- 12. Invisible Man — Ralph Ellison (n≈30)
- 13. Life After Life — Kate Atkinson (n≈30)
- 14. King Lear — William Shakespeare (n≈116)
- 15. Heart of Darkness — Joseph Conrad (n≈88)

### seeded_classic_oracle
- 1. Tutunamayanlar — Oguz Atay (n≈386)
- 2. Tehlikeli Oyunlar — Oguz Atay (n≈218)
- 3. Le Monogramme — Odysseus Elytis (n≈102)
- 4. The Moonlight Sonata — Yiannis Ritsos (n≈68)
- 5. The Knight in the Panther's Skin — Shota Rustaveli (n≈98)
- 6. Мастер и Маргарита. Собачье сердце — Mikhail Bulgakov (n≈59)
- 7. The Brothers Karamazov — Fyodor Dostoyevsky (n≈6761)
- 8. Crime and Punishment — Fyodor Dostoyevsky (n≈11729)
- 9. The Return of the King (The Lord of the Rings, #3) — J.R.R. Tolkien (n≈6256)
- 10. Shahnameh: The Persian Book of Kings — Abolqasem Ferdowsi (n≈129)
- 11. Cuentos completos 1 — Julio Cortazar (n≈161)
- 12. The Fortress — Mesa Selimovic (n≈113)
- 13. The Book of Disquiet — Fernando Pessoa (n≈779)
- 14. The Fellowship of the Ring (The Lord of the Rings, #1) — J.R.R. Tolkien (n≈11735)
- 15. The Last Question — Isaac Asimov (n≈297)

## Notes

- Gold features = same-sign effect vs anti **and** vs normie with min|d|≥0.12.
- **Differentiation summary:**
  - vs **anti**: classics rate far fewer series (`series_share` 0.17 vs 0.61), older books, lower author HHI / binge.
  - vs **normie**: classics put less mass on mega-catalog blockbusters (`mega_share` 0.16 vs 0.32), span more mid-pop authors, slightly deeper rarity.
- Unseeded inference: `classic_focus = classic_raw − λ_a·anti_raw − λ_n·normie_raw`, hard gates on series/mega/binge/midpop-span, then either weighted P(5) or **contrastive** P(5|focus)−P(5|anti-like).
- Contrastive unseeded beat the seeded oracle on literary_poll Q here (still evaluate cautiously — feature weights were fit using seed-labeled cohorts).
- Seeded oracle remains a membership upper bound for the exclusive classic cohort itself.

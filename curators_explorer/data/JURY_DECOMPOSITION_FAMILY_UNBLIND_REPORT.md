# Hierarchical jury decomposition: family semantic unblind report

**One-shot semantic unblind of the two frozen tau=0.70 mode families.  The numerical metrics and permutation results below were frozen BEFORE any human-readable head was rendered.**

## 1. Provenance and verified seals

- Source campaign: seed **20260819**, git head `4ad7287b4624`; 2880 sources; partial false; unblinded false; semantic false.
- Source hashes verified: census_npz `b333150fef91a96e...`, census_json `8f54a02224f021df...`, geometry_npz `24a90fa35cdaf6de...`, geometry_json `c47e1ecb75be2d23...`.
- Addendum (mode families): seed **20260820**, 244 tau=0.70 recurrent modes, exactly two families at every cut; semantic false; unblinded false.
- Addendum centroids used: `family_cent_0.70_f0`, `family_cent_0.70_f1` (exact frozen vectors, finite, unit L2; never recomputed).
- Semantic-unblind seed **20260821**; 10000 popularity-stratified permutations; SAME permuted semantic assignment for both families.

## 2. Frozen semantic hypotheses (before any head)

- `E0`: exact literary count @50, family 0
- `E1`: exact literary count @50, family 1
- `T_max`: max(E0, E1): at least one frozen family is literary-enriched (family-wise)
- `T_min`: min(E0, E1): preregistered symmetric JOINT/SUPPORTING statistic
- `p_both_exact_iut`: intersection-union conjunction max(p_E0, p_E1): PRIMARY formal test that BOTH frozen families individually reject their own exact-literary nulls (multiple naturally discovered canons)
- `p_both_broad_iut`: intersection-union conjunction max(p_B0, p_B1): secondary broad-literary conjunction
- `alpha`: conjunction rejection threshold 0.05 frozen before semantic load
- `B_max`: max(broad0, broad1): at least one family broad-enriched (secondary)
- `B_min`: min(broad0, broad1): both families broad-enriched (secondary)
- `anti_direction`: anti counts @50 reported with the stated direction: depletion (lower anti count) is the literary direction; both tails are reported descriptively
- `null`: 10000 popularity-stratified permutations, seed 20260821, SAME permuted semantic assignment for both families in every permutation

## 3. Numerical family 0 metrics (frozen)

### family_0 (0.70_f0, 125 modes, 112 parents)
- exact literary @50 = **0** (precision 0.000); @100 = **0** (precision 0.000).
- broad literary @50 = **0** (precision 0.000); @100 = **0** (precision 0.000).
- anti @50 = **47** (fraction 0.940); @100 = **81** (fraction 0.810).
- chance @50 (universe fractions): exact 0.1, broad 0.8, anti 6.2.
### family_1 (0.70_f1, 119 modes, 102 parents)
- exact literary @50 = **4** (precision 0.080); @100 = **9** (precision 0.090).
- broad literary @50 = **6** (precision 0.120); @100 = **13** (precision 0.130).
- anti @50 = **8** (fraction 0.160); @100 = **14** (fraction 0.140).
- chance @50 (universe fractions): exact 0.1, broad 0.8, anti 6.2.

## 4. Joint T_max / T_min permutation results

| statistic | observed | null mean | null sd | p_upper |
|---|---:|---:|---:|---:|
| exact@50 family 0 | 0 | 0.66 | 0.80 | 1.0000 |
| exact@50 family 1 | 4 | 0.53 | 0.73 | 0.0020 |
| max(E0,E1) | 4 | 0.94 | 0.84 | 0.0060 |
| min(E0,E1) (joint/supporting) | 0 | 0.25 | 0.48 | 1.0000 |
| BOTH exact (IUT max(p_E0,p_E1)) | n/a | n/a | n/a | 1.0000 (alpha 0.05) |

## 5. Broad / anti results (secondary/supporting)

| statistic | observed | null mean | null sd | p_upper |
|---|---:|---:|---:|---:|
| broad@50 family 0 | 0 | 2.00 | 1.37 | 1.0000 |
| broad@50 family 1 | 6 | 1.76 | 1.29 | 0.0074 |
| max(B0,B1) | 6 | 2.57 | 1.29 | 0.0212 |
| min(B0,B1) | 0 | 1.19 | 0.99 | 1.0000 |
| BOTH broad (IUT max(p_B0,p_B1)) | n/a | n/a | n/a | 1.0000 (alpha 0.05) |
| anti@50 A0 (depletion direction) | 47 | 16.59 | 3.31 | p_lower=1.0000 (p_upper=0.0001) |
| anti@50 A1 (depletion direction) | 8 | 15.00 | 3.21 | p_lower=0.0169 (p_upper=0.9937) |

## 6. Author-deduplicated robustness (descriptive)

| family | unique-author exact @50 | unique-author broad @50 | unique-author anti @50 | n distinct authors | max works one author | authors >=2 works |
|---|---:|---:|---:|---:|---:|---:|
| 0.70_f0 | 0 | 0 | 30 | 19 | 8 | 10 |
| 0.70_f1 | 8 | 10 | 4 | 27 | 5 | 11 |

## 7. Cross-family overlap / distinctness (descriptive)

- Centroid cosine family0 vs family1: **0.2516**.
- Top 50 overlap: 6 works, Jaccard 0.064.
- Top 100 overlap: 15 works, Jaccard 0.081.
- exact_lit works: family0 0, family1 14, overlap 0 (Jaccard 0.000).
- broad_lit works: family0 0, family1 31, overlap 0 (Jaccard 0.000).
- anti works: family0 141, family1 22, overlap 14 (Jaccard 0.094).

## 8. Interpretation (frozen tests only)

- T_min p = **1.0000** (preregistered joint/supporting statistic); p_both_exact_iut = **1.0000** (primary intersection-union conjunction, alpha 0.05).  Both are reported; neither silently replaces the other.
- Category A: p_T_max < .05 but p_both_exact_iut >= .05 -> at least ONE frozen family is exact-literary enriched; NOT evidence that both are literary canons.
- Category B: p_both_exact_iut < .05 -> BOTH frozen families individually reject their own exact-literary nulls; confirmatory statistical condition for multiple naturally discovered literary canons (examine overlap/distinctness before claiming genuinely distinct canons).
- Category C: neither -> structural decomposition is real but no exact literary recovery under this test.
- Category D: only broad conjunction/significance -> broader high-cultural/serious-reading structure, not strict literary canon recovery.

## 9. Frozen top-work heads (rendered AFTER all metrics)

### 0.70_f0 top-50 head
| rank | title | author | score | exact | broad | anti |
|---:|---|---|---:|---|---|---|
| 1 | A Court of Mist and Fury (A Court of Thorns and Roses, #2) | Sarah J. Maas | 0.0374 |  |  | Y |
| 2 | Harry Potter and the Deathly Hallows (Harry Potter, #7) | J.K. Rowling | 0.0370 |  |  | Y |
| 3 | Clockwork Princess (The Infernal Devices, #3) | Cassandra Clare | 0.0360 |  |  | Y |
| 4 | Harry Potter Boxset (Harry Potter, #1-7) | J.K. Rowling | 0.0358 |  |  | Y |
| 5 | Crooked Kingdom (Six of Crows, #2) | Leigh Bardugo | 0.0355 |  |  | Y |
| 6 | Harry Potter and the Half-Blood Prince (Harry Potter, #6) | J.K. Rowling | 0.0351 |  |  | Y |
| 7 | Queen of Shadows (Throne of Glass, #4) | Sarah J. Maas | 0.0351 |  |  | Y |
| 8 | Winter (The Lunar Chronicles, #4) | Marissa Meyer | 0.0350 |  |  | Y |
| 9 | Cress (The Lunar Chronicles, #3) | Marissa Meyer | 0.0349 |  |  | Y |
| 10 | Harry Potter and the Goblet of Fire (Harry Potter, #4) | J.K. Rowling | 0.0348 |  |  | Y |
| 11 | Harry Potter and the Prisoner of Azkaban (Harry Potter, #3) | J.K. Rowling | 0.0346 |  |  | Y |
| 12 | The Last Olympian (Percy Jackson and the Olympians, #5) | Rick Riordan | 0.0344 |  |  | Y |
| 13 | Crown of Midnight (Throne of Glass, #2) | Sarah J. Maas | 0.0342 |  |  | Y |
| 14 | The House of Hades (The Heroes of Olympus, #4) | Rick Riordan | 0.0339 |  |  | Y |
| 15 | Six of Crows (Six of Crows, #1) | Leigh Bardugo | 0.0331 |  |  | Y |
| 16 | The Mark of Athena (The Heroes of Olympus, #3) | Rick Riordan | 0.0327 |  |  | Y |
| 17 | Empire of Storms (Throne of Glass, #5) | Sarah J. Maas | 0.0326 |  |  | Y |
| 18 | Heir of Fire (Throne of Glass, #3) | Sarah J. Maas | 0.0326 |  |  | Y |
| 19 | Harry Potter and the Order of the Phoenix (Harry Potter, #5) | J.K. Rowling | 0.0324 |  |  | Y |
| 20 | Clockwork Prince (The Infernal Devices, #2) | Cassandra Clare | 0.0324 |  |  | Y |
| 21 | Harry Potter and the Sorcerer's Stone (Harry Potter, #1) | J.K. Rowling | 0.0322 |  |  | Y |
| 22 | Lady Midnight (The Dark Artifices, #1) | Cassandra Clare | 0.0321 |  |  | Y |
| 23 | A Court of Wings and Ruin (A Court of Thorns and Roses, #3) | Sarah J. Maas | 0.0315 |  |  | Y |
| 24 | The Hate U Give | Angie Thomas | 0.0313 |  |  |  |
| 25 | City of Heavenly Fire (The Mortal Instruments, #6) | Cassandra Clare | 0.0310 |  |  | Y |
| 26 | The Nightingale | Kristin Hannah | 0.0299 |  |  | Y |
| 27 | Shadowfever (Fever, #5) | Karen Marie Moning | 0.0298 |  |  | Y |
| 28 | A Storm of Swords (A Song of Ice and Fire, #3) | George R.R. Martin | 0.0296 |  |  |  |
| 29 | The Hunger Games (The Hunger Games, #1) | Suzanne Collins | 0.0295 |  |  | Y |
| 30 | The Son of Neptune (The Heroes of Olympus, #2) | Rick Riordan | 0.0294 |  |  | Y |
| 31 | Ignite Me (Shatter Me, #3) | Tahereh Mafi | 0.0294 |  |  | Y |
| 32 | The Assassin's Blade (Throne of Glass, #0.1-0.5) | Sarah J. Maas | 0.0294 |  |  | Y |
| 33 | Last Sacrifice (Vampire Academy, #6) | Richelle Mead | 0.0292 |  |  | Y |
| 34 | Origin (Lux, #4) | Jennifer L. Armentrout | 0.0292 |  |  | Y |
| 35 | Harry Potter and the Chamber of Secrets (Harry Potter, #2) | J.K. Rowling | 0.0291 |  |  | Y |
| 36 | Gemina (The Illuminae Files, #2) | Amie Kaufman | 0.0291 |  |  |  |
| 37 | Sentinel (Covenant, #5) | Jennifer L. Armentrout | 0.0290 |  |  | Y |
| 38 | The Battle of the Labyrinth (Percy Jackson and the Olympians, #4) | Rick Riordan | 0.0286 |  |  | Y |
| 39 | The Indigo Spell (Bloodlines, #3) | Richelle Mead | 0.0284 |  |  | Y |
| 40 | Lord of Shadows (The Dark Artifices, #2) | Cassandra Clare | 0.0284 |  |  | Y |
| 41 | Magic Strikes (Kate Daniels, #3) | Ilona Andrews | 0.0284 |  |  | Y |
| 42 | An Ember in the Ashes (An Ember in the Ashes, #1) | Sabaa Tahir | 0.0283 |  |  | Y |
| 43 | The Hunger Games Trilogy Boxset (The Hunger Games, #1-3) | Suzanne Collins | 0.0282 |  |  | Y |
| 44 | Magic Bleeds (Kate Daniels, #4) | Ilona Andrews | 0.0280 |  |  | Y |
| 45 | The Final Empire (Mistborn, #1) | Brandon Sanderson | 0.0279 |  |  | Y |
| 46 | Magic Rises (Kate Daniels, #6) | Ilona Andrews | 0.0278 |  |  | Y |
| 47 | Shadow Kiss (Vampire Academy, #3) | Richelle Mead | 0.0278 |  |  | Y |
| 48 | Deity (Covenant, #3) | Jennifer L. Armentrout | 0.0277 |  |  | Y |
| 49 | Nothing but Shadows (Tales from Shadowhunter Academy, #4) | Cassandra Clare | 0.0274 |  |  | Y |
| 50 | The Help | Kathryn Stockett | 0.0274 |  |  | Y |
### 0.70_f1 top-50 head
| rank | title | author | score | exact | broad | anti |
|---:|---|---|---:|---|---|---|
| 1 | The Complete Maus (Maus, #1-2) | Art Spiegelman | 0.0355 |  |  |  |
| 2 | Words of Radiance (The Stormlight Archive, #2) | Brandon Sanderson | 0.0344 |  |  | Y |
| 3 | The Complete Sherlock Holmes | Arthur Conan Doyle | 0.0333 |  |  |  |
| 4 | The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury | Bill Watterson | 0.0333 |  |  |  |
| 5 | Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2) | Art Spiegelman | 0.0332 |  |  |  |
| 6 | A Storm of Swords (A Song of Ice and Fire, #3) | George R.R. Martin | 0.0331 |  |  |  |
| 7 | Harry Potter Boxset (Harry Potter, #1-7) | J.K. Rowling | 0.0326 |  |  | Y |
| 8 | Saga, Vol. 2 (Saga, #2) | Brian K. Vaughan | 0.0324 |  |  |  |
| 9 | Ficciones | Jorge Luis Borges | 0.0324 |  |  |  |
| 10 | The Return of the King (The Lord of the Rings, #3) | J.R.R. Tolkien | 0.0320 |  |  |  |
| 11 | Saga, Vol. 3 (Saga, #3) | Brian K. Vaughan | 0.0319 |  |  |  |
| 12 | Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1) | Art Spiegelman | 0.0319 |  |  |  |
| 13 | Labyrinths:  Selected Stories and Other Writings | Jorge Luis Borges | 0.0318 |  |  |  |
| 14 | Calvin and Hobbes | Bill Watterson | 0.0318 |  |  |  |
| 15 | The Complete Calvin and Hobbes | Bill Watterson | 0.0313 |  |  |  |
| 16 | The Complete Persepolis | Marjane Satrapi | 0.0312 |  |  |  |
| 17 | The Brothers Karamazov | Fyodor Dostoyevsky | 0.0308 | Y | Y |  |
| 18 | The Lord of the Rings (The Lord of the Rings, #1-3) | J.R.R. Tolkien | 0.0308 |  |  |  |
| 19 | Between the World and Me | Ta-Nehisi Coates | 0.0308 |  |  |  |
| 20 | The Way of Kings (The Stormlight Archive, #1) | Brandon Sanderson | 0.0306 |  |  | Y |
| 21 | Harry Potter and the Deathly Hallows (Harry Potter, #7) | J.K. Rowling | 0.0306 |  |  | Y |
| 22 | Collected Fictions | Jorge Luis Borges | 0.0303 |  |  |  |
| 23 | Season of Mists (The Sandman #4) | Neil Gaiman | 0.0300 |  |  |  |
| 24 | Saga, Vol. 1 (Saga, #1) | Brian K. Vaughan | 0.0300 |  |  |  |
| 25 | Harry Potter and the Prisoner of Azkaban (Harry Potter, #3) | J.K. Rowling | 0.0293 |  |  | Y |
| 26 | The Book of Disquiet | Fernando Pessoa | 0.0292 | Y | Y |  |
| 27 | The Name of the Wind (The Kingkiller Chronicle, #1) | Patrick Rothfuss | 0.0291 |  |  |  |
| 28 | Cosmos | Carl Sagan | 0.0291 |  |  |  |
| 29 | The Kindly Ones (The Sandman #9) | Neil Gaiman | 0.0291 |  |  |  |
| 30 | The Aleph and Other Stories | Jorge Luis Borges | 0.0290 |  |  |  |
| 31 | A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2) | George R.R. Martin | 0.0290 |  |  |  |
| 32 | Stoner | John  Williams | 0.0289 | Y | Y |  |
| 33 | Harry Potter and the Half-Blood Prince (Harry Potter, #6) | J.K. Rowling | 0.0288 |  |  | Y |
| 34 | Nothing to Envy: Ordinary Lives in North Korea | Barbara Demick | 0.0288 |  |  |  |
| 35 | A Game of Thrones (A Song of Ice and Fire, #1) | George R.R. Martin | 0.0287 |  |  |  |
| 36 | Harry Potter and the Goblet of Fire (Harry Potter, #4) | J.K. Rowling | 0.0286 |  |  | Y |
| 37 | Crime and Punishment | Fyodor Dostoyevsky | 0.0285 |  | Y |  |
| 38 | The Arrival | Shaun Tan | 0.0284 |  |  |  |
| 39 | J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings | J.R.R. Tolkien | 0.0284 |  |  |  |
| 40 | The Wise Man's Fear (The Kingkiller Chronicle, #2) | Patrick Rothfuss | 0.0284 |  |  |  |
| 41 | Saga, Vol. 4 (Saga, #4) | Brian K. Vaughan | 0.0284 |  |  |  |
| 42 | The Two Towers (The Lord of the Rings, #2) | J.R.R. Tolkien | 0.0282 |  |  |  |
| 43 | Changes (The Dresden Files, #12) | Jim Butcher | 0.0282 |  |  | Y |
| 44 | Voices from Chernobyl: The Oral History of a Nuclear Disaster | Svetlana Alexievich | 0.0280 |  |  |  |
| 45 | The Complete Stories | Flannery O'Connor | 0.0278 |  |  |  |
| 46 | If This Is a Man / The Truce | Primo Levi | 0.0277 |  |  |  |
| 47 | This Is Water: Some Thoughts, Delivered on a Significant Occasion, about Living a Compassionate Life | David Foster Wallace | 0.0275 |  | Y |  |
| 48 | Lonesome Dove | Larry McMurtry | 0.0275 |  |  |  |
| 49 | Swann's Way (In Search of Lost Time, #1) | Marcel Proust | 0.0275 | Y | Y |  |
| 50 | Sapiens: A Brief History of Humankind | Yuval Noah Harari | 0.0275 |  |  |  |

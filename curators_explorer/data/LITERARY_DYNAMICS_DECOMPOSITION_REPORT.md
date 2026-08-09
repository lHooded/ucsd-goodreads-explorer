# Literary dynamics decomposition

- Deterministic seed: `20260902`.
- Membership is the frozen common-L selection from `237cb37`; the map only reweights fixed members.
- `BETA=2.5`, long maximum `2000`, random-init sigma `0.2`.
- Full top-1000 checkpoint arrays (IDs, implicit ranks, scores, reader mass, and checkpoint weights) are in the NPZ. This report and the heads file show complete top-50 metadata for human inspection.

## Audit and smoke status

- Overall audit: **PASS** (23/23 checks).
- The four independent inherited t=200 reproductions matched the committed endpoint diagnostics, seed heads, and t=200 head metrics within stored numerical precision before the long run.

| check | status | detail |
|---|---|---|
| starting_commit_or_descendant | PASS | HEAD=237cb3783b66c020ca034aab39a78af46899640f |
| frozen_score_hash_present | PASS | f6d536d0e37345359344ba3cd94094d1be579067a8c1ff0c7420e9f92a60d49c |
| beta_exactly_2_5 | PASS | BETA=2.5 |
| long_cap_exactly_2000 | PASS | LONG_MAX_ITER=2000 |
| random_sigma_exactly_0p20 | PASS | sigma=0.2 |
| strict_rule_frozen | PASS | step>=0.9999, wrel<=0.0001, consecutive=5 |
| equal_init_exact_ones | PASS | all initial weights are exactly one after mean normalization |
| historical_iterate_map_equation_audited | PASS | historical source contains the frozen tanh/sigmoid/damped equation |
| no_pruning_or_reversal_in_long_runner | PASS | trajectory code changes no IDs and contains no pruning/reversal path |
| t200_reproduction_J5000 | PASS | step=0.999999285 wrel=8.589e-04 Kish=3344.373 J50=0.612903 |
| t200_reproduction_J10000 | PASS | step=0.999999583 wrel=7.527e-04 Kish=6422.643 J50=0.515152 |
| t200_reproduction_J20000 | PASS | step=0.999999642 wrel=7.035e-04 Kish=13568.648 J50=0.562500 |
| t200_reproduction_J30000 | PASS | step=0.999999642 wrel=6.491e-04 Kish=19523.110 J50=0.587302 |
| nested_J5_J10 | PASS | intersection=5000 |
| nested_J10_J20 | PASS | intersection=10000 |
| nested_J20_J30 | PASS | intersection=20000 |
| shells_pairwise_disjoint | PASS | sizes=[5000, 5000, 10000, 10000] |
| shell_union_J30000 | PASS | union=30000 |
| old_artifacts_present | PASS | 237cb37 JSON/report/heads still exist |
| persisted_old_80_subsets | PASS | five exact payloads found |
| absent_rank_unit | PASS | missing top-500 book gets fixed rank 501 |
| jaccard_overlap_are_distinct | PASS | Jaccard and overlap fraction use separate formulas |
| lag_history_uses_t_minus_2 | PASS | lag-2 distances compare the actual t-2 vector |

## Fixed memberships and shells

The exact nestedness checks are `|J5 ∩ J10|=5000`, `|J10 ∩ J20|=10000`, and `|J20 ∩ J30|=20000`. The disjoint shells are S0=J5, S1=J10−J5, S2=J20−J10, S3=J30−J20; their union is J30. Shell reports are direct equal-vote rankings.

| shell | n | mean L | median L | p10 | p25 | p75 | min | outside ABC |
|---|---|---|---|---|---|---|---|---|
| S0 | 5000 | 0.819 | 0.811 | 0.790 | 0.797 | 0.834 | 0.785 | 0.486 |
| S1 | 5000 | 0.768 | 0.767 | 0.756 | 0.760 | 0.775 | 0.753 | 0.590 |
| S2 | 10000 | 0.731 | 0.730 | 0.715 | 0.720 | 0.741 | 0.711 | 0.657 |
| S3 | 10000 | 0.697 | 0.697 | 0.686 | 0.690 | 0.704 | 0.683 | 0.719 |

| shell | ABC | p65 | A∩B | vote2 | A only | B only | AB only | none ABC |
|---|---|---|---|---|---|---|---|---|
| S0 | 0.081 | 0.104 | 0.278 | 0.291 | 0.032 | 0.189 | 0.197 | 0.486 |
| S1 | 0.057 | 0.068 | 0.212 | 0.220 | 0.028 | 0.160 | 0.155 | 0.590 |
| S2 | 0.040 | 0.054 | 0.166 | 0.175 | 0.029 | 0.137 | 0.126 | 0.657 |
| S3 | 0.030 | 0.038 | 0.127 | 0.134 | 0.025 | 0.120 | 0.097 | 0.719 |

See `LITERARY_SIZE_SHELL_HEADS.md` for complete direct top-50 heads and a human-readable shell taste summary. Series descriptors are not available from a clean project table; author and reliable flag concentration are reported instead.

## Primary size-decomposition table

The literary-assessment cells are post-hoc descriptions of the actual heads, not selection criteria. Probe counts remain annotations only.

| jury | n | median L | direct literary assessment | final dynamic literary assessment | direct pos/exact/broad/anti | final pos/exact/broad/anti | direct→final J50 | direct authors/max | final authors/max | 20–49 >=1 | 20–49 >=3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J5000 | 5000 | 0.811 | direct head: pos/exact/broad/anti=25/19/25/0; unique authors=36, max same author=5; top five=Crime and Punishment; The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); Hamlet | final dynamic head: pos/exact/broad/anti=34/25/34/0; unique authors=36, max same author=4; top five=Crime and Punishment; Hamlet; The Brothers Karamazov; The Return of the King (The Lord of the Rings, #3); The Trial | 25/19/25/0 | 34/25/34/0 | 0.613 | 36/5 | 36/4 | 0.32 | 0.04 |
| J10000 | 10000 | 0.785 | direct head: pos/exact/broad/anti=21/16/21/1; unique authors=36, max same author=5; top five=Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3) | final dynamic head: pos/exact/broad/anti=9/6/9/1; unique authors=29, max same author=9; top five=The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3) | 21/16/21/1 | 9/6/9/1 | 0.515 | 36/5 | 29/9 | 0.51 | 0.13 |
| J20000 | 20000 | 0.753 | direct head: pos/exact/broad/anti=11/8/11/1; unique authors=29, max same author=7; top five=The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3) | final dynamic head: pos/exact/broad/anti=17/11/17/0; unique authors=37, max same author=4; top five=Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov | 11/8/11/1 | 17/11/17/0 | 0.562 | 29/7 | 37/4 | 0.69 | 0.32 |
| J30000 | 30000 | 0.730 | direct head: pos/exact/broad/anti=5/3/5/1; unique authors=26, max same author=8; top five=The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Between the World and Me; The Complete Maus (Maus, #1-2); The Two Towers (The Lord of the Rings, #2) | final dynamic head: pos/exact/broad/anti=4/2/4/3; unique authors=19, max same author=9; top five=The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); A Storm of Swords (A Song of Ice and Fire, #3); J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings | 5/3/5/1 | 4/2/4/3 | 0.562 | 26/8 | 19/9 | 0.79 | 0.47 |

## Direct size trajectory

Jaccard and overlap fraction are reported separately. Direct size movement uses top-500 union ranks with absent rank fixed at 501.

### J5000_to_J10000

| comparison | J50 | overlap/50 | J200 | overlap/200 | rho common top200 | score Pearson |
|---|---|---|---|---|---|---|
| direct | 0.639 | 0.780 | 0.717 | 0.835 | 0.783 | 0.934 |

### Top 30 direct risers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| The Calvin and Hobbes Tenth Anniversary Book | Bill Watterson | 501 | 165 | 336 |
| The Last Question | Isaac Asimov | 501 | 174 | 327 |
| Born a Crime: Stories From a South African Childhood | Trevor Noah | 501 | 177 | 324 |
| Voices from Chernobyl: The Oral History of a Nuclear Disaster | Svetlana Alexievich | 501 | 180 | 321 |
| The Hate U Give | Angie Thomas | 501 | 189 | 312 |
| In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) | Marcel Proust | 501 | 190 | 311 |
| Changes (The Dresden Files, #12) | Jim Butcher | 501 | 194 | 307 |
| Just Mercy: A Story of Justice and Redemption | Bryan Stevenson | 501 | 204 | 297 |
| John Adams | David McCullough | 501 | 207 | 294 |
| A Gentleman in Moscow | Amor Towles | 501 | 231 | 270 |
| The Monster at the End of this Book | Jon Stone | 501 | 234 | 267 |
| The Love Song of J. Alfred Prufrock and Other Poems | T.S. Eliot | 501 | 237 | 264 |
| A Storm of Swords: Steel and Snow (A Song of Ice and Fire, #3: Part 1 of 2) | George R.R. Martin | 501 | 243 | 258 |
| Meditations | Marcus Aurelius | 501 | 246 | 255 |
| The Warmth of Other Suns: The Epic Story of America's Great Migration | Isabel Wilkerson | 501 | 248 | 253 |
| Everything That Rises Must Converge: Stories | Flannery O'Connor | 501 | 254 | 247 |
| Beyond Good and Evil | Friedrich Nietzsche | 501 | 255 | 246 |
| Night Watch (Discworld, #29; City Watch, #6) | Terry Pratchett | 501 | 256 | 245 |
| Four Quartets | T.S. Eliot | 501 | 259 | 242 |
| It's a Magical World: A Calvin and Hobbes Collection | Bill Watterson | 501 | 262 | 239 |
| Evicted: Poverty and Profit in the American City | Matthew Desmond | 501 | 263 | 238 |
| The New Jim Crow: Mass Incarceration in the Age of Colorblindness | Michelle Alexander | 501 | 268 | 233 |
| A Constellation of Vital Phenomena | Anthony Marra | 501 | 279 | 222 |
| Discipline and Punish: The Birth of the Prison | Michel Foucault | 501 | 280 | 221 |
| Will You Please Be Quiet, Please? | Raymond Carver | 501 | 282 | 219 |
| Midnight Tides (The Malazan Book of the Fallen, #5) | Steven Erikson | 501 | 284 | 217 |
| The Indispensable Calvin and Hobbes | Bill Watterson | 501 | 291 | 210 |
| Tutunamayanlar | Oguz Atay | 501 | 292 | 209 |
| Team of Rivals: The Political Genius of Abraham Lincoln | Doris Kearns Goodwin | 501 | 295 | 206 |
| The Importance of Being Earnest and Other Plays | Oscar Wilde | 501 | 297 | 204 |

### Top 30 direct fallers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Disgrace | J.M. Coetzee | 195 | 450 | -255 |
| Raise High the Roof Beam, Carpenters & Seymour: An Introduction | J.D. Salinger | 277 | 501 | -224 |
| Wuthering Heights | Emily Bronte | 242 | 458 | -216 |
| A Portrait of the Artist as a Young Man | James Joyce | 275 | 489 | -214 |
| Twelfth Night | William Shakespeare | 288 | 501 | -213 |
| Brave New World | Aldous Huxley | 295 | 501 | -206 |
| Zorba the Greek | Nikos Kazantzakis | 299 | 501 | -202 |
| The Old Man and the Sea | Ernest Hemingway | 302 | 501 | -199 |
| If on a Winter's Night a Traveler | Italo Calvino | 122 | 315 | -193 |
| The Diary of a Young Girl | Anne Frank | 308 | 501 | -193 |
| V for Vendetta | Alan Moore | 200 | 390 | -190 |
| Persuasion | Jane Austen | 294 | 482 | -188 |
| My Name is Red | Orhan Pamuk | 313 | 501 | -188 |
| Their Eyes Were Watching God | Zora Neale Hurston | 187 | 374 | -187 |
| Middlesex | Jeffrey Eugenides | 300 | 486 | -186 |
| Animal Farm | George Orwell | 279 | 462 | -183 |
| Of Mice and Men | John Steinbeck | 273 | 452 | -179 |
| The Once and Future King (The Once and Future King #1-4) | T.H. White | 314 | 492 | -178 |
| The Cat in the Hat | Dr. Seuss | 250 | 427 | -177 |
| 2001: A Space Odyssey (Space Odyssey, #1) | Arthur C. Clarke | 270 | 447 | -177 |
| House of Leaves | Mark Z. Danielewski | 326 | 501 | -175 |
| Gone with the Wind | Margaret Mitchell | 327 | 501 | -174 |
| Foundation (Foundation #1) | Isaac Asimov | 328 | 501 | -173 |
| Foucault's Pendulum | Umberto Eco | 329 | 501 | -172 |
| The Amber Spyglass (His Dark Materials, #3) | Philip Pullman | 338 | 501 | -163 |
| The Metamorphosis | Franz Kafka | 159 | 317 | -158 |
| Franny and Zooey | J.D. Salinger | 281 | 439 | -158 |
| Madame Bovary | Gustave Flaubert | 214 | 369 | -155 |
| The Stand | Stephen King | 346 | 501 | -155 |
| The Three Musketeers (The D'Artagnan Romances, #1) | Alexandre Dumas | 317 | 469 | -152 |

Post-hoc author summary: risers Bill Watterson (1), Isaac Asimov (1), Trevor Noah (1), Svetlana Alexievich (1), Angie Thomas (1), Marcel Proust (1), Jim Butcher (1), Bryan Stevenson (1); fallers J.M. Coetzee (1), J.D. Salinger (1), Emily Bronte (1), James Joyce (1), William Shakespeare (1), Aldous Huxley (1), Nikos Kazantzakis (1), Ernest Hemingway (1).

### J10000_to_J20000

| comparison | J50 | overlap/50 | J200 | overlap/200 | rho common top200 | score Pearson |
|---|---|---|---|---|---|---|
| direct | 0.515 | 0.680 | 0.702 | 0.825 | 0.725 | 0.938 |

### Top 30 direct risers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Dear Ijeawele, or a Feminist Manifesto in Fifteen Suggestions | Chimamanda Ngozi Adichie | 501 | 162 | 339 |
| Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection | Bill Watterson | 501 | 186 | 315 |
| March: Book Two (March, #2) | John             Lewis | 501 | 187 | 314 |
| The Revenge of the Baby-Sat | Bill Watterson | 501 | 217 | 284 |
| March: Book Three (March, #3) | John             Lewis | 501 | 222 | 279 |
| The Calvin and Hobbes Lazy Sunday Book | Bill Watterson | 501 | 240 | 261 |
| The Rings of Saturn | W.G. Sebald | 501 | 246 | 255 |
| In Search of Lost Time  (À la recherche du temps perdu #1-7) | Marcel Proust | 501 | 254 | 247 |
| There's Treasure Everywhere: A Calvin and Hobbes Collection | Bill Watterson | 501 | 270 | 231 |
| Amphigorey (Amphigorey, #1) | Edward Gorey | 501 | 278 | 223 |
| Yukon Ho! | Bill Watterson | 501 | 281 | 220 |
| Citizen: An American Lyric | Claudia Rankine | 501 | 291 | 210 |
| A Manual for Cleaning Women: Selected Stories | Lucia Berlin | 501 | 292 | 209 |
| Toda Mafalda | Quino | 501 | 293 | 208 |
| The Absolute Sandman, Volume One | Neil Gaiman | 312 | 105 | 207 |
| Building Stories | Chris Ware | 501 | 295 | 206 |
| Every Man Dies Alone | Hans Fallada | 501 | 296 | 205 |
| March: Book One (March, #1) | John             Lewis | 341 | 142 | 199 |
| My Family and Other Animals (Corfu Trilogy, #1) | Gerald Durrell | 501 | 309 | 192 |
| The Complete Tales and Poems | Edgar Allan Poe | 501 | 313 | 188 |
| Kindred | Octavia E. Butler | 501 | 315 | 186 |
| Locke & Key, Vol. 5: Clockworks | Joe Hill | 376 | 195 | 181 |
| Long Walk to Freedom | Nelson Mandela | 501 | 321 | 180 |
| The Gashlycrumb Tinies (The Vinegar Works, #1) | Edward Gorey | 429 | 252 | 177 |
| Evicted: Poverty and Profit in the American City | Matthew Desmond | 263 | 88 | 175 |
| A Song of Ice and Fire (A Song of Ice and Fire, #1-4) | George R.R. Martin | 501 | 330 | 171 |
| The New Jim Crow: Mass Incarceration in the Age of Colorblindness | Michelle Alexander | 268 | 104 | 164 |
| The Complete Tales and Poems of Winnie-the-Pooh (Winnie-the-Pooh, #1-4) | A.A. Milne | 501 | 338 | 163 |
| The Overcoat | Nikolai Gogol | 338 | 176 | 162 |
| Cutting for Stone | Abraham Verghese | 498 | 336 | 162 |

### Top 30 direct fallers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| A Clockwork Orange | Anthony Burgess | 170 | 437 | -267 |
| The Castle | Franz Kafka | 236 | 501 | -265 |
| Beyond Good and Evil | Friedrich Nietzsche | 255 | 501 | -246 |
| Nine Stories | J.D. Salinger | 137 | 381 | -244 |
| White Noise | Don DeLillo | 265 | 501 | -236 |
| Faust: First Part | Johann Wolfgang von Goethe | 205 | 439 | -234 |
| Dead Souls | Nikolai Gogol | 276 | 501 | -225 |
| Fahrenheit 451 | Ray Bradbury | 275 | 499 | -224 |
| What We Talk About When We Talk About Love | Raymond Carver | 149 | 370 | -221 |
| Invisible Man | Ralph Ellison | 283 | 501 | -218 |
| Oedipus Rex  (The Theban Plays, #1) | Sophocles | 286 | 501 | -215 |
| Ham on Rye | Charles Bukowski | 288 | 501 | -213 |
| Wolf Hall (Thomas Cromwell, #1) | Hilary Mantel | 289 | 498 | -209 |
| Moby-Dick or, The Whale | Herman Melville | 154 | 359 | -205 |
| The Martian Chronicles | Ray Bradbury | 152 | 351 | -199 |
| David Copperfield | Charles Dickens | 302 | 501 | -199 |
| The Lies of Locke Lamora (Gentleman Bastard, #1) | Scott Lynch | 278 | 476 | -198 |
| Love in the Time of Cholera | Gabriel Garcia Marquez | 227 | 418 | -191 |
| A Confederacy of Dunces | John Kennedy Toole | 198 | 387 | -189 |
| Catch-22 (Catch-22, #1) | Joseph Heller | 224 | 408 | -184 |
| The Metamorphosis | Franz Kafka | 317 | 501 | -184 |
| The Myth of Sisyphus and Other Essays | Albert Camus | 191 | 374 | -183 |
| Kürk Mantolu Madonna | Sabahattin Ali | 319 | 501 | -182 |
| Mother Night | Kurt Vonnegut Jr. | 92 | 273 | -181 |
| The Fall | Albert Camus | 331 | 501 | -170 |
| The Unbearable Lightness of Being | Milan Kundera | 111 | 276 | -165 |
| Song of Solomon | Toni Morrison | 146 | 310 | -164 |
| To the Lighthouse | Virginia Woolf | 110 | 272 | -162 |
| Revolutionary Road | Richard Yates | 250 | 412 | -162 |
| The Walking Dead, Compendium 1 | Robert Kirkman | 339 | 501 | -162 |

Post-hoc author summary: risers Bill Watterson (5), John             Lewis (2), Chimamanda Ngozi Adichie (1), W.G. Sebald (1), Marcel Proust (1), Edward Gorey (1), Claudia Rankine (1), Lucia Berlin (1); fallers Ray Bradbury (2), Anthony Burgess (1), Franz Kafka (1), Friedrich Nietzsche (1), J.D. Salinger (1), Don DeLillo (1), Johann Wolfgang von Goethe (1), Nikolai Gogol (1).

### J20000_to_J30000

| comparison | J50 | overlap/50 | J200 | overlap/200 | rho common top200 | score Pearson |
|---|---|---|---|---|---|---|
| direct | 0.724 | 0.840 | 0.770 | 0.870 | 0.793 | 0.967 |

### Top 30 direct risers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Rita Hayworth and Shawshank Redemption: A Story from Different Seasons | Stephen King | 496 | 263 | 233 |
| The Brothers Lionheart | Astrid Lindgren | 447 | 230 | 217 |
| Something Under the Bed is Drooling: A Calvin and Hobbes Collection | Bill Watterson | 417 | 204 | 213 |
| Cancer Ward | Aleksandr Solzhenitsyn | 501 | 297 | 204 |
| Crooked Kingdom (Six of Crows, #2) | Leigh Bardugo | 349 | 158 | 191 |
| Angle of Repose | Wallace Stegner | 434 | 243 | 191 |
| Can't We Talk about Something More Pleasant? | Roz Chast | 501 | 312 | 189 |
| Death's End (Remembrance of Earth’s Past, #3) | Liu Cixin | 490 | 307 | 183 |
| Columbine | Dave Cullen | 471 | 291 | 180 |
| And the Band Played On: Politics, People, and the AIDS Epidemic | Randy Shilts | 445 | 266 | 179 |
| Locke & Key, Vol. 4: Keys to the Kingdom | Joe Hill | 427 | 257 | 170 |
| The Nightingale | Kristin Hannah | 501 | 332 | 169 |
| The Declaration of Independence and The Constitution of the United States | Founding Fathers | 407 | 242 | 165 |
| A Song of Ice and Fire (A Song of Ice and Fire, #1-5) | George R.R. Martin | 467 | 304 | 163 |
| Weirdos from Another Planet!: A Calvin and Hobbes Collection | Bill Watterson | 452 | 290 | 162 |
| Beartown | Fredrik Backman | 468 | 308 | 160 |
| Saga, Vol. 7 (Saga, #7) | Brian K. Vaughan | 304 | 145 | 159 |
| Collected Poems, 1909-1962 | T.S. Eliot | 390 | 234 | 156 |
| The Absolute Sandman, Volume Two | Neil Gaiman | 362 | 210 | 152 |
| The Story of Ferdinand | Munro Leaf | 428 | 276 | 152 |
| Essential Tales and Poems | Edgar Allan Poe | 353 | 202 | 151 |
| The Gay Science | Friedrich Nietzsche | 501 | 353 | 148 |
| The Constitution of the United States of America | Founding Fathers | 501 | 355 | 146 |
| Locke & Key, Vol. 6: Alpha & Omega | Joe Hill | 347 | 205 | 142 |
| Attack of the Deranged Mutant Killer Monster Snow Goons | Bill Watterson | 401 | 262 | 139 |
| Assassin's Fate (The Fitz and the Fool, #3) | Robin Hobb | 501 | 363 | 138 |
| The World of Winnie-the-Pooh (Winnie-the-Pooh, #1-2) | A.A. Milne | 409 | 272 | 137 |
| Die Herren von Winterfell (Das Lied von Eis und Feuer, #1) | George R.R. Martin | 451 | 315 | 136 |
| The Guns of August | Barbara W. Tuchman | 444 | 309 | 135 |
| The Unabridged Journals of Sylvia Plath | Sylvia Plath | 486 | 351 | 135 |

### Top 30 direct fallers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Mrs. Dalloway | Virginia Woolf | 271 | 501 | -230 |
| To the Lighthouse | Virginia Woolf | 272 | 501 | -229 |
| Bone: The Complete Edition | Jeff Smith | 277 | 501 | -224 |
| Steppenwolf | Hermann Hesse | 283 | 501 | -218 |
| The Road | Cormac McCarthy | 258 | 474 | -216 |
| Alice in Wonderland | Jane Carruth | 185 | 397 | -212 |
| Bury My Heart at Wounded Knee: An Indian History of the American West | Dee Brown | 247 | 458 | -211 |
| Consider the Lobster and Other Essays | David Foster Wallace | 230 | 414 | -184 |
| The Argonauts | Maggie Nelson | 323 | 501 | -178 |
| Richard III | William Shakespeare | 325 | 501 | -176 |
| Batman: The Killing Joke | Alan Moore | 305 | 479 | -174 |
| The Thousand Autumns of Jacob de Zoet | David Mitchell | 327 | 501 | -174 |
| The Death of Ivan Ilych | Leo Tolstoy | 329 | 501 | -172 |
| The Rings of Saturn | W.G. Sebald | 246 | 416 | -170 |
| Alice's Adventures in Wonderland & Through the Looking-Glass | Lewis Carroll | 331 | 501 | -170 |
| The Grapes of Wrath | John Steinbeck | 333 | 501 | -168 |
| Farewell, My Lovely (Philip Marlowe, #2) | Raymond Chandler | 340 | 501 | -161 |
| Gilead (Gilead, #1) | Marilynne Robinson | 341 | 501 | -160 |
| The Unbearable Lightness of Being | Milan Kundera | 276 | 435 | -159 |
| All the Pretty Horses (The Border Trilogy, #1) | Cormac McCarthy | 342 | 501 | -159 |
| The Iliad | Homer | 213 | 365 | -152 |
| Waiting for Godot | Samuel Beckett | 221 | 372 | -151 |
| From Hell | Alan Moore | 314 | 464 | -150 |
| The Godfather | Mario Puzo | 306 | 452 | -146 |
| Jimmy Corrigan, the Smartest Kid on Earth | Chris Ware | 357 | 501 | -144 |
| Moby-Dick or, The Whale | Herman Melville | 359 | 501 | -142 |
| Jane Eyre | Charlotte Bronte | 299 | 437 | -138 |
| Charlotte's Web | E.B. White | 363 | 501 | -138 |
| Alice's Adventures in Wonderland | Lewis Carroll | 365 | 501 | -136 |
| Daytripper | Fabio Moon | 268 | 402 | -134 |

Post-hoc author summary: risers Bill Watterson (2), Stephen King (1), Astrid Lindgren (1), Aleksandr Solzhenitsyn (1), Leigh Bardugo (1), Wallace Stegner (1), Roz Chast (1), Liu Cixin (1); fallers Virginia Woolf (2), Jeff Smith (1), Hermann Hesse (1), Cormac McCarthy (1), Jane Carruth (1), Dee Brown (1), David Foster Wallace (1), Maggie Nelson (1).

## Primary long-run dynamics

Strict convergence means step ≥ .9999 and weight_rel ≤ 1e−4 for five consecutive iterations. A candidate hit is followed by +50 verification iterations; if that window is not stable, the trajectory continues to its full cap. `practical_head_stability` is a separate descriptive rule: the first saved checkpoint whose later saved heads all have at least 0.90 top-50 overlap fraction with final.

| jury | strict candidate t | strict +50 stable? | iterations | wrel t200 | wrel t500/final avail | wrel t1000/final avail | wrel final | lag2 rel final | t200→final J50 | t200→final overlap/50 | practical stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J5000 | 381 | True | 431 | 8.59e-04 | 4.52e-06 | 4.52e-06 | 4.52e-06 | 9.14e-06 | 1.000 | 1.000 | 1 |
| J10000 | 333 | True | 383 | 7.53e-04 | 5.20e-06 | 5.20e-06 | 5.20e-06 | 1.06e-05 | 1.000 | 1.000 | 10 |
| J20000 | 419 | True | 469 | 7.03e-04 | 2.62e-05 | 2.62e-05 | 2.62e-05 | 5.21e-05 | 1.000 | 1.000 | 20 |
| J30000 | 439 | True | 489 | 6.49e-04 | 7.13e-05 | 7.13e-05 | 7.13e-05 | 1.43e-04 | 0.961 | 0.980 | 10 |

Window summaries show median [minimum, maximum] over each available iteration window; absent late windows reflect genuine early strict convergence plus the required 50-iteration verification run.

| jury | window | weight_rel_1 median [min,max] | weight_rel_2 median [min,max] | book_rel_1 median [min,max] | step median [min,max] |
|---|---|---|---|---|---|
| J5000 | 1–50 | 9.03e-03 [4.71e-03, 4.38e-01] | 1.79e-02 [9.40e-03, 5.65e-01] | 1.32e-02 [6.74e-03, 1.54e+04] | 1.00e+00 [2.75e-01, 1.00e+00] |
| J5000 | 51–100 | 3.38e-03 [1.97e-03, 7.11e-03] | 6.76e-03 [4.51e-03, 1.39e-02] | 4.77e-03 [2.88e-03, 1.10e-02] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J5000 | 101–200 | 1.32e-03 [5.62e-04, 4.44e-03] | 2.69e-03 [1.13e-03, 8.35e-03] | 1.84e-03 [7.67e-04, 7.80e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J5000 | 201–500 | 3.90e-04 [4.52e-06, 2.40e-03] | 7.99e-04 [9.14e-06, 4.74e-03] | 5.35e-04 [5.65e-06, 3.52e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J10000 | 1–50 | 1.15e-02 [4.72e-03, 4.48e-01] | 2.29e-02 [9.35e-03, 5.92e-01] | 1.61e-02 [6.34e-03, 5.34e+03] | 1.00e+00 [3.61e-01, 1.00e+00] |
| J10000 | 51–100 | 2.78e-03 [1.35e-03, 5.98e-03] | 5.52e-03 [2.75e-03, 1.15e-02] | 3.70e-03 [1.78e-03, 8.98e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J10000 | 101–200 | 7.09e-04 [2.29e-04, 2.85e-03] | 1.42e-03 [4.57e-04, 5.59e-03] | 9.09e-04 [2.84e-04, 4.17e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J10000 | 201–500 | 2.22e-04 [5.20e-06, 3.10e-03] | 4.59e-04 [1.06e-05, 5.83e-03] | 2.92e-04 [6.33e-06, 5.24e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J20000 | 1–50 | 1.09e-02 [5.68e-03, 4.41e-01] | 2.17e-02 [1.13e-02, 5.65e-01] | 1.49e-02 [8.20e-03, 2.48e+03] | 1.00e+00 [4.65e-01, 1.00e+00] |
| J20000 | 51–100 | 2.95e-03 [1.94e-03, 5.82e-03] | 5.96e-03 [3.90e-03, 1.14e-02] | 4.24e-03 [2.68e-03, 8.90e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J20000 | 101–200 | 9.82e-04 [4.42e-04, 2.81e-03] | 1.96e-03 [8.83e-04, 5.33e-03] | 1.31e-03 [5.93e-04, 4.55e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J20000 | 201–500 | 1.50e-04 [2.42e-05, 1.01e-03] | 3.04e-04 [4.85e-05, 2.01e-03] | 1.98e-04 [3.19e-05, 1.42e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J30000 | 1–50 | 1.48e-02 [4.70e-03, 4.43e-01] | 2.94e-02 [9.41e-03, 5.72e-01] | 1.95e-02 [6.32e-03, 8.28e+03] | 1.00e+00 [5.32e-01, 1.00e+00] |
| J30000 | 51–100 | 3.89e-03 [1.86e-03, 5.17e-03] | 7.75e-03 [3.73e-03, 1.02e-02] | 5.23e-03 [2.42e-03, 7.41e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J30000 | 101–200 | 1.09e-03 [4.20e-04, 3.36e-03] | 2.19e-03 [8.39e-04, 6.75e-03] | 1.39e-03 [5.22e-04, 4.96e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |
| J30000 | 201–500 | 3.44e-04 [5.83e-05, 1.44e-03] | 6.90e-04 [1.17e-04, 2.76e-03] | 4.21e-04 [7.22e-05, 2.07e-03] | 1.00e+00 [1.00e+00, 1.00e+00] |

| jury | log(wrel) window | n | slope | R² | p-value |
|---|---|---|---|---|---|
| J5000 | 200_1000 | 232 | -2.48e-02 | 0.753 | 0.000 |
| J5000 | 1000_2000 | 0 | — | — | — |
| J10000 | 200_1000 | 184 | -2.21e-02 | 0.558 | 0.000 |
| J10000 | 1000_2000 | 0 | — | — | — |
| J20000 | 200_1000 | 270 | -7.49e-03 | 0.331 | 0.000 |
| J20000 | 1000_2000 | 0 | — | — | — |
| J30000 | 200_1000 | 290 | -7.30e-03 | 0.463 | 0.000 |
| J30000 | 1000_2000 | 0 | — | — | — |

Lag-2/lag-3/lag-4 diagnostics and all saved-checkpoint comparisons are also stored in JSON. The lag-cycle flag is intentionally heuristic and is not treated as proof of a mathematical cycle.

### Saved-checkpoint head stability

Each row compares the checkpoint with its previous saved checkpoint, with t=200, and with the final available checkpoint. `ov50` is overlap/50; J50 is Jaccard.

| jury | checkpoint | vs previous J50/ov50 | vs t200 J50/ov50 | vs final J50/ov50 |
|---|---|---|---|---|
| J5000 | requested 0 (actual 0) | — | J0.61/0.76 | J0.61/0.76 |
| J5000 | requested 20 (actual 20) | J0.96/0.98 | J0.92/0.96 | J0.92/0.96 |
| J5000 | requested 100 (actual 100) | J1.00/1.00 | J0.96/0.98 | J0.96/0.98 |
| J5000 | requested 200 (actual 200) | J0.96/0.98 | J1.00/1.00 | J1.00/1.00 |
| J5000 | requested 500 (actual 431) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J5000 | requested 1000 (actual 431) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J5000 | requested 2000 (actual 431) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J10000 | requested 0 (actual 0) | — | J0.52/0.68 | J0.52/0.68 |
| J10000 | requested 20 (actual 20) | J0.85/0.92 | J0.92/0.96 | J0.92/0.96 |
| J10000 | requested 100 (actual 100) | J0.96/0.98 | J1.00/1.00 | J1.00/1.00 |
| J10000 | requested 200 (actual 200) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J10000 | requested 500 (actual 383) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J10000 | requested 1000 (actual 383) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J10000 | requested 2000 (actual 383) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J20000 | requested 0 (actual 0) | — | J0.56/0.72 | J0.56/0.72 |
| J20000 | requested 20 (actual 20) | J0.92/0.96 | J0.85/0.92 | J0.85/0.92 |
| J20000 | requested 100 (actual 100) | J0.92/0.96 | J1.00/1.00 | J1.00/1.00 |
| J20000 | requested 200 (actual 200) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J20000 | requested 500 (actual 469) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J20000 | requested 1000 (actual 469) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J20000 | requested 2000 (actual 469) | J1.00/1.00 | J1.00/1.00 | J1.00/1.00 |
| J30000 | requested 0 (actual 0) | — | J0.59/0.74 | J0.56/0.72 |
| J30000 | requested 20 (actual 20) | J0.92/0.96 | J0.92/0.96 | J0.92/0.96 |
| J30000 | requested 100 (actual 100) | J0.96/0.98 | J0.96/0.98 | J1.00/1.00 |
| J30000 | requested 200 (actual 200) | J0.96/0.98 | J1.00/1.00 | J0.96/0.98 |
| J30000 | requested 500 (actual 489) | J0.96/0.98 | J0.96/0.98 | J1.00/1.00 |
| J30000 | requested 1000 (actual 489) | J0.96/0.98 | J0.96/0.98 | J1.00/1.00 |
| J30000 | requested 2000 (actual 489) | J0.96/0.98 | J0.96/0.98 | J1.00/1.00 |

## Direct → t200 → final movement

### J5000

### Direct → final risers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Will You Please Be Quiet, Please? | Raymond Carver | 501 | 140 | 361 |
| Austerlitz | W.G. Sebald | 501 | 151 | 350 |
| The Symposium | Plato | 501 | 152 | 349 |
| Beyond Good and Evil | Friedrich Nietzsche | 501 | 168 | 333 |
| رباعيات خيام | Omar Khayyam | 501 | 169 | 332 |
| The Love Song of J. Alfred Prufrock and Other Poems | T.S. Eliot | 501 | 173 | 328 |
| In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) | Marcel Proust | 501 | 174 | 327 |
| The Glass Bead Game | Hermann Hesse | 501 | 177 | 324 |
| Four Quartets | T.S. Eliot | 501 | 195 | 306 |
| Just Mercy: A Story of Justice and Redemption | Bryan Stevenson | 501 | 197 | 304 |
| Suttree | Cormac McCarthy | 501 | 204 | 297 |
| Tutunamayanlar | Oguz Atay | 501 | 205 | 296 |
| Discipline and Punish: The Birth of the Prison | Michel Foucault | 501 | 207 | 294 |
| The Tartar Steppe | Dino Buzzati | 501 | 210 | 291 |
| Everything That Rises Must Converge: Stories | Flannery O'Connor | 501 | 217 | 284 |

### Direct → final fallers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Words of Radiance (The Stormlight Archive, #2) | Brandon Sanderson | 100 | 501 | -401 |
| The Tale of Peter Rabbit | Beatrix Potter | 178 | 501 | -323 |
| The Hero of Ages (Mistborn, #3) | Brandon Sanderson | 186 | 501 | -315 |
| The Name of the Wind (The Kingkiller Chronicle, #1) | Patrick Rothfuss | 144 | 448 | -304 |
| The Complete Works | William Shakespeare | 202 | 501 | -299 |
| A Little Princess | Frances Hodgson Burnett | 232 | 501 | -269 |
| Oh, The Places You'll Go! | Dr. Seuss | 147 | 404 | -257 |
| The Cat in the Hat | Dr. Seuss | 250 | 501 | -251 |
| The Killer Angels (The Civil War Trilogy, #2) | Michael Shaara | 252 | 501 | -249 |
| A Game of You (The Sandman #5) | Neil Gaiman | 163 | 408 | -245 |
| Saga, Vol. 3 (Saga, #3) | Brian K. Vaughan | 116 | 355 | -239 |
| Saga, Vol. 5 (Saga, #5) | Brian K. Vaughan | 267 | 501 | -234 |
| On Writing: A Memoir of the Craft | Stephen King | 168 | 397 | -229 |
| The Adventures of Sherlock Holmes | Arthur Conan Doyle | 141 | 363 | -222 |
| The Wake (The Sandman #10) | Neil Gaiman | 204 | 426 | -222 |

The complete top-30 direct→t200, direct→final, and t200→final movement lists are in JSON; the two headline lists above are top 15.

### J10000

### Direct → final risers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Boy's Life | Robert McCammon | 501 | 183 | 318 |
| Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection | Bill Watterson | 501 | 195 | 306 |
| Lamb: The Gospel According to Biff, Christ's Childhood Pal | Christopher Moore | 479 | 176 | 303 |
| Murder on the Orient Express (Hercule Poirot, #10) | Agatha Christie | 499 | 201 | 298 |
| I, Robot (Robot #0.1) | Isaac Asimov | 501 | 205 | 296 |
| The Return of Sherlock Holmes | Arthur Conan Doyle | 501 | 207 | 294 |
| The Revenge of the Baby-Sat | Bill Watterson | 501 | 210 | 291 |
| Foundation (Foundation #1) | Isaac Asimov | 501 | 212 | 289 |
| Gone with the Wind | Margaret Mitchell | 501 | 218 | 283 |
| There's Treasure Everywhere: A Calvin and Hobbes Collection | Bill Watterson | 501 | 225 | 276 |
| The Good Earth (House of Earth, #1) | Pearl S. Buck | 501 | 228 | 273 |
| Corduroy | Don Freeman | 501 | 229 | 272 |
| Falling Up | Shel Silverstein | 433 | 162 | 271 |
| The Three Musketeers (The D'Artagnan Romances, #1) | Alexandre Dumas | 469 | 202 | 267 |
| Something Under the Bed is Drooling: A Calvin and Hobbes Collection | Bill Watterson | 501 | 237 | 264 |

### Direct → final fallers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Collected Fictions | Jorge Luis Borges | 75 | 501 | -426 |
| The Complete Stories | Flannery O'Connor | 107 | 501 | -394 |
| Selected Stories | Anton Chekhov | 112 | 501 | -389 |
| Cathedral | Raymond Carver | 121 | 501 | -380 |
| Where I'm Calling From: New and Selected Stories | Raymond Carver | 132 | 501 | -369 |
| The Waste Land | T.S. Eliot | 148 | 501 | -353 |
| The Fire Next Time | James     Baldwin | 164 | 499 | -335 |
| What We Talk About When We Talk About Love | Raymond Carver | 149 | 480 | -331 |
| Journey to the End of the Night | Louis-Ferdinand Celine | 50 | 372 | -322 |
| Blood Meridian, or the Evening Redness in the West | Cormac McCarthy | 136 | 458 | -322 |
| Voices from Chernobyl: The Oral History of a Nuclear Disaster | Svetlana Alexievich | 180 | 501 | -321 |
| Memoirs of Hadrian | Marguerite Yourcenar | 181 | 501 | -320 |
| Midnight's Children | Salman Rushdie | 102 | 421 | -319 |
| 2666 | Roberto Bolano | 40 | 357 | -317 |
| Swann's Way (In Search of Lost Time, #1) | Marcel Proust | 184 | 501 | -317 |

The complete top-30 direct→t200, direct→final, and t200→final movement lists are in JSON; the two headline lists above are top 15.

### J20000

### Direct → final risers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Long Day's Journey Into Night | Eugene O'Neill | 501 | 227 | 274 |
| Death on the Installment Plan | Louis-Ferdinand Celine | 484 | 222 | 262 |
| The World of Yesterday | Stefan Zweig | 497 | 269 | 228 |
| The Complete Poems 1927-1979 | Elizabeth Bishop | 492 | 265 | 227 |
| Master of the Senate (The Years of Lyndon Johnson, #3) | Robert A. Caro | 501 | 274 | 227 |
| The Unabridged Journals of Sylvia Plath | Sylvia Plath | 486 | 261 | 225 |
| The Path to Power (The Years of Lyndon Johnson, #1) | Robert A. Caro | 400 | 181 | 219 |
| Wild Swans: Three Daughters of China | Jung Chang | 478 | 259 | 219 |
| The Complete Essays | Michel de Montaigne | 420 | 205 | 215 |
| Apology | Plato | 501 | 288 | 213 |
| Can't We Talk about Something More Pleasant? | Roz Chast | 501 | 292 | 209 |
| Death and the Dervish | Mesa Selimovic | 449 | 251 | 198 |
| The Metamorphosis, In the Penal Colony, and Other Stories: The Great Short Works of Franz Kafka | Franz Kafka | 472 | 276 | 196 |
| The Summer Book | Tove Jansson | 501 | 305 | 196 |
| Savage Inequalities: Children in America's Schools | Jonathan Kozol | 501 | 307 | 194 |

### Direct → final fallers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| The Way of Kings (The Stormlight Archive, #1) | Brandon Sanderson | 99 | 501 | -402 |
| Dream Country (The Sandman #3) | Neil Gaiman | 131 | 501 | -370 |
| Changes (The Dresden Files, #12) | Jim Butcher | 136 | 501 | -365 |
| The Name of the Wind (The Kingkiller Chronicle, #1) | Patrick Rothfuss | 139 | 501 | -362 |
| A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2) | George R.R. Martin | 83 | 434 | -351 |
| The Wise Man's Fear (The Kingkiller Chronicle, #2) | Patrick Rothfuss | 159 | 501 | -342 |
| A Game of You (The Sandman #5) | Neil Gaiman | 111 | 445 | -334 |
| Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection | Bill Watterson | 186 | 501 | -315 |
| Saga, Vol. 5 (Saga, #5) | Brian K. Vaughan | 189 | 501 | -312 |
| It's a Magical World: A Calvin and Hobbes Collection | Bill Watterson | 193 | 501 | -308 |
| Locke & Key, Vol. 5: Clockworks | Joe Hill | 195 | 500 | -305 |
| Scientific Progress Goes "Boink": A Calvin and Hobbes Collection | Bill Watterson | 205 | 501 | -296 |
| The Days Are Just Packed: A Calvin and Hobbes Collection | Bill Watterson | 214 | 501 | -287 |
| A Little Princess | Frances Hodgson Burnett | 201 | 487 | -286 |
| The Revenge of the Baby-Sat | Bill Watterson | 217 | 501 | -284 |

The complete top-30 direct→t200, direct→final, and t200→final movement lists are in JSON; the two headline lists above are top 15.

### J30000

### Direct → final risers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Gates of Fire: An Epic Novel of the Battle of Thermopylae | Steven Pressfield | 501 | 149 | 352 |
| The Return of Sherlock Holmes | Arthur Conan Doyle | 501 | 157 | 344 |
| Daughter of the Forest  (Sevenwaters, #1) | Juliet Marillier | 501 | 172 | 329 |
| The Obelisk Gate (The Broken Earth, #2) | N.K. Jemisin | 488 | 160 | 328 |
| Transmetropolitan, Vol. 7: Spider's Thrash (Transmetropolitan, #7) | Warren Ellis | 501 | 174 | 327 |
| Strange the Dreamer (Strange the Dreamer, #1) | Laini Taylor | 494 | 169 | 325 |
| Blood Song (Raven's Shadow, #1) | Anthony  Ryan | 477 | 153 | 324 |
| Death: The High Cost of Living Collected | Neil Gaiman | 501 | 177 | 324 |
| The Walking Dead, Vol. 08: Made to Suffer | Robert Kirkman | 471 | 155 | 316 |
| Transmetropolitan, Vol. 3: Year of the Bastard (Transmetropolitan, #3) | Warren Ellis | 501 | 190 | 311 |
| V for Vendetta | Alan Moore | 501 | 191 | 310 |
| The Green Mile, Part 1: The Two Dead Girls | Stephen King | 501 | 199 | 302 |
| Magic Strikes (Kate Daniels, #3) | Ilona Andrews | 482 | 182 | 300 |
| A Thousand Splendid Suns | Khaled Hosseini | 501 | 201 | 300 |
| And Then There Were None | Agatha Christie | 491 | 202 | 289 |

### Direct → final fallers

| title | author | old_rank | new_rank | delta |
|---|---|---|---|---|
| Selected Stories | Anton Chekhov | 57 | 501 | -444 |
| The Complete Stories | Flannery O'Connor | 64 | 501 | -437 |
| Four Quartets | T.S. Eliot | 111 | 501 | -390 |
| March: Book Three (March, #3) | John             Lewis | 113 | 501 | -388 |
| A Constellation of Vital Phenomena | Anthony Marra | 121 | 501 | -380 |
| In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) | Marcel Proust | 122 | 501 | -379 |
| Where I'm Calling From: New and Selected Stories | Raymond Carver | 134 | 501 | -367 |
| Voices from Chernobyl: The Oral History of a Nuclear Disaster | Svetlana Alexievich | 138 | 501 | -363 |
| The Book of Disquiet | Fernando Pessoa | 139 | 501 | -362 |
| The Fire Next Time | James     Baldwin | 124 | 481 | -357 |
| 2666 | Roberto Bolano | 55 | 410 | -355 |
| Middlemarch | George Eliot | 147 | 501 | -354 |
| Everything That Rises Must Converge: Stories | Flannery O'Connor | 152 | 501 | -349 |
| The Essential Rumi | Jalaluddin Mevlana Rumi | 153 | 501 | -348 |
| If This Is a Man / The Truce | Primo Levi | 141 | 479 | -338 |

The complete top-30 direct→t200, direct→final, and t200→final movement lists are in JSON; the two headline lists above are top 15.

## Size versus convergence: descriptive decomposition

For N=10k/20k/30k, D5 is J5000 direct, DN is that size's direct ranking, and CN(final) is its long-run equal-init ranking. These are multiple frozen descriptive distances, not a formal causal decomposition. The interaction can depend on N.

| N | D5→DN 1−J50 | DN→CN 1−J50 | D5→CN 1−J50 | D5→DN 1−J200 | DN→CN 1−J200 | D5→CN 1−J200 | D5→DN rho | DN→CN rho | D5→CN rho | pref RMS D5→DN | pref RMS DN→CN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10000 | 0.361 | 0.485 | 0.571 | 0.283 | 0.456 | 0.502 | 0.783 | 0.610 | 0.515 | 0.492 | 0.449 |
| 20000 | 0.684 | 0.438 | 0.718 | 0.462 | 0.333 | 0.540 | 0.499 | 0.646 | 0.322 | 0.883 | 0.449 |
| 30000 | 0.750 | 0.438 | 0.734 | 0.556 | 0.524 | 0.697 | 0.328 | 0.659 | 0.407 | 1.130 | 0.448 |

## Semantic annotations and structural concentration

Probe counts are annotations only. Actual heads, authors, and titles are in `LITERARY_DYNAMICS_TRAJECTORY_HEADS.md`.

| jury | direct pos/exact/broad/anti | t20 | t100 | t200 | t500 | final |
|---|---|---|---|---|---|---|
| J5000 | 25/19/25/0 | 36/26/36/0 | 35/25/35/0 | 34/25/34/0 | 34/25/34/0 | 34/25/34/0 |
| J10000 | 21/16/21/1 | 8/5/8/1 | 9/6/9/1 | 9/6/9/1 | 9/6/9/1 | 9/6/9/1 |
| J20000 | 11/8/11/1 | 20/13/20/0 | 17/11/17/0 | 17/11/17/0 | 17/11/17/0 | 17/11/17/0 |
| J30000 | 5/3/5/1 | 4/2/4/3 | 4/2/4/3 | 4/2/4/3 | 4/2/4/3 | 4/2/4/3 |

| jury | checkpoint | unique authors@50 | max same author | collections | duplicates | comics |
|---|---|---|---|---|---|---|
| J5000 | 0 | 36 | 5 | 5 | 0 | 7 |
| J5000 | 1 | 36 | 5 | 5 | 0 | 5 |
| J5000 | 2 | 35 | 5 | 5 | 0 | 5 |
| J5000 | 5 | 35 | 4 | 5 | 0 | 4 |
| J5000 | 10 | 35 | 4 | 5 | 0 | 4 |
| J5000 | 20 | 36 | 4 | 4 | 0 | 4 |
| J5000 | 50 | 36 | 4 | 4 | 0 | 4 |
| J5000 | 100 | 36 | 4 | 4 | 0 | 4 |
| J5000 | 200 | 36 | 4 | 5 | 0 | 4 |
| J5000 | 300 | 36 | 4 | 5 | 0 | 4 |
| J5000 | 431 | 36 | 4 | 5 | 0 | 4 |
| J10000 | 0 | 36 | 5 | 7 | 0 | 10 |
| J10000 | 1 | 33 | 6 | 6 | 0 | 12 |
| J10000 | 2 | 33 | 6 | 5 | 0 | 13 |
| J10000 | 5 | 33 | 7 | 4 | 0 | 15 |
| J10000 | 10 | 31 | 7 | 4 | 0 | 14 |
| J10000 | 20 | 28 | 9 | 4 | 0 | 15 |
| J10000 | 50 | 29 | 9 | 4 | 0 | 15 |
| J10000 | 100 | 29 | 9 | 4 | 0 | 15 |
| J10000 | 200 | 29 | 9 | 4 | 0 | 15 |
| J10000 | 300 | 29 | 9 | 4 | 0 | 15 |
| J10000 | 383 | 29 | 9 | 4 | 0 | 15 |
| J20000 | 0 | 29 | 7 | 10 | 0 | 18 |
| J20000 | 1 | 34 | 5 | 13 | 0 | 12 |
| J20000 | 2 | 35 | 5 | 13 | 0 | 9 |
| J20000 | 5 | 36 | 5 | 14 | 0 | 9 |
| J20000 | 10 | 35 | 4 | 12 | 0 | 10 |
| J20000 | 20 | 35 | 4 | 11 | 0 | 10 |
| J20000 | 50 | 36 | 4 | 11 | 0 | 10 |
| J20000 | 100 | 37 | 4 | 11 | 0 | 9 |
| J20000 | 200 | 37 | 4 | 11 | 0 | 9 |
| J20000 | 300 | 37 | 4 | 11 | 0 | 9 |
| J20000 | 469 | 37 | 4 | 11 | 0 | 9 |
| J30000 | 0 | 26 | 8 | 11 | 0 | 21 |
| J30000 | 1 | 27 | 8 | 11 | 0 | 22 |
| J30000 | 2 | 27 | 9 | 9 | 0 | 24 |
| J30000 | 5 | 23 | 9 | 6 | 0 | 25 |
| J30000 | 10 | 21 | 9 | 5 | 0 | 24 |
| J30000 | 20 | 19 | 9 | 6 | 0 | 25 |
| J30000 | 50 | 20 | 9 | 7 | 0 | 25 |
| J30000 | 100 | 19 | 9 | 7 | 0 | 25 |
| J30000 | 200 | 20 | 9 | 7 | 0 | 24 |
| J30000 | 300 | 20 | 9 | 7 | 0 | 24 |
| J30000 | 489 | 19 | 9 | 7 | 0 | 25 |

## Random initialization

Each primary has five sigma=.20 lognormal starts, except J30000 with three. Comparisons are to the equal-init trajectory at the same saved horizon. The classification is descriptive: transient sensitivity, persistent basin multiplicity, stable ranking/unstable weights, or unresolved.

| jury | final J50 overlap median | p10 | p90 | final J200 overlap median | final weight cosine median | pairwise final J50 overlap | classification |
|---|---|---|---|---|---|---|---|
| J5000 | 0.940 | 0.908 | 0.940 | 0.896 | 0.913 | 0.930 | stable ranking / unstable weights |
| J10000 | 0.400 | 0.400 | 0.756 | 0.311 | 0.359 | 0.860 | persistent basin multiplicity (mixed endpoints) |
| J20000 | 0.740 | 0.548 | 0.884 | 0.569 | 0.738 | 0.730 | persistent basin multiplicity |
| J30000 | 0.680 | 0.680 | 0.904 | 0.361 | 0.657 | 0.680 | persistent basin multiplicity |

## J10000 80% forensic check

The old five exact subsets were reused. Long-horizon medians below test whether the old t=200 anomaly persists rather than treating it as a basin label.

| horizon | n | J50 median | overlap/50 median | J200 median | overlap/200 median | score Pearson median |
|---|---|---|---|---|---|---|
| 200 | 10 | 0.250 | 0.400 | 0.327 | 0.492 | 0.659 |
| 500 | 10 | 0.250 | 0.400 | 0.327 | 0.492 | 0.660 |
| 1000 | 10 | 0.250 | 0.400 | 0.327 | 0.492 | 0.660 |
| 2000 | 10 | 0.250 | 0.400 | 0.327 | 0.492 | 0.660 |

t200 overlap50 median=0.400; t500 overlap50 median=0.400; t1000 overlap50 median=0.400; t2000 overlap50 median=0.400

## Coverage context

These are the correct raw obscure-book coverage values persisted by the inherited experiment; no obscure-book accuracy validation was performed here.

| jury | 20–49 >=1 | 20–49 >=3 | 5–19 >=1 | 50–99 >=1 | 100–249 >=1 | 250–999 >=1 |
|---|---|---|---|---|---|---|
| J5000 | 0.32 | 0.04 | 0.16 | 0.50 | 0.67 | 0.86 |
| J10000 | 0.51 | 0.13 | 0.30 | 0.68 | 0.82 | 0.93 |
| J20000 | 0.69 | 0.32 | 0.47 | 0.83 | 0.92 | 0.98 |
| J30000 | 0.79 | 0.47 | 0.59 | 0.90 | 0.96 | 0.99 |

## Explicit answers

### What do S1/S2/S3 prefer?

The answer is in the complete shell heads file and its interpretive section. The report deliberately uses actual top-book titles, repeated authors, and reliable collection/comic flags rather than a new genre classifier.

### Is t=200 asymptotic?

Use the t200→final J50/J200 rows and practical-head-stability iterations above. A high head overlap can coexist with non-negligible continuing weight movement; the report does not equate head stability with a weight fixed point.

### Does the user vector converge or cycle?

The primary cycle diagnostics report actual lag-1 through lag-4 relative distances. A 2-cycle would require lag-1 to remain positive while lag-2 collapses; the stored heuristic is only evidence, not a proof. Windowed log trends show whether movement is declining.

### What causes the larger-jury slide?

The answer must be size-specific. Compare the direct shell heads and direct J5→J10→J20→J30 movement with each fixed-size direct→final head. If a fandom/graphic/series-heavy head is already in DN, that is membership composition; if it appears or is amplified only in CN, that is convergence; the data allow both and interaction.

### Practical jury assessment

J5000, J10000, J20000, and J30000 should not be reduced to a single optimized scalar. The final assessment weighs direct-head naturality, individual common-L quality, dynamic behavior, initialization sensitivity, and the preserved coverage tradeoff. In particular, a large direct jury can remain a defensible trustworthy readership even if this internal-consensus operator amplifies a different axis.

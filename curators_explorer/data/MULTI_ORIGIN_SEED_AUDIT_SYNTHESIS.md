# Multi-origin semantic-seed audit: synthesis

## Answer

The present canon is **not reproducible from any arbitrary seed**, but it is also **not merely a copy of its original literary seed**. Independent literary starts recover a common Goodreads behavior basin and a substantial held-out book core; non-literary starts recover a sharply different basin. The initial seed still matters for exact ordering, marginal books, and which literary subtraditions are emphasized.

The seed-free multi-origin ensemble shares **27/50** and **111/200** books with the current ranking. A stricter core of **72 books** appears in at least 11/14 independent literary top 200s. Those figures are more informative than claiming a percentage of the ranking was 'caused' by the seed, which this observational experiment cannot identify.

## Main evidence

| Comparison | jury Jaccard | book Jaccard@50 | book Jaccard@200 |
|---|---:|---:|---:|
| Literary ↔ literary (behavioral) | 0.184 | 0.254 | 0.363 |
| Literary ↔ controls (behavioral) | 0.022 | 0.106 | 0.164 |
| Controls ↔ controls (behavioral) | 0.176 | 0.463 | 0.530 |
| Literary ↔ children's border | 0.128 | 0.222 | 0.318 |

Before behavioral reconstruction, direct literary rankings overlapped at J@200=0.237, versus 0.172 for controls. After replacing book identities with generic behavior features, the gap widens rather than disappearing. That is the key evidence for a distributed taste signal.

## Regional stress test

| Origin subset | jury Jaccard | book Jaccard@50 | book Jaccard@200 |
|---|---:|---:|---:|
| Six regional origins only | 0.103 | 0.158 | 0.275 |
| Eight broad/history/list origins only | 0.301 | 0.356 | 0.458 |
| Regional ↔ broad | 0.142 | 0.226 | 0.336 |

Regional starts agree less with one another than the broad starts do. This is partly real cultural variation and partly much thinner Goodreads evidence. Crucially, their cross-overlap with broad starts remains materially above literary-control overlap; the common basin is not produced solely by GreatestBooks or European historical origins.

## Origin-level diagnostics

`within lit` is mean top-200 overlap with the other literary starts; `vs controls` is mean overlap with romance, commercial-series, and fantasy controls.

| Origin | teachers | AP | within lit | vs controls | vs current |
|---|---:|---:|---:|---:|---:|
| latin_american_lens | 2,000 | 0.036 | 0.320 | 0.040 | 0.600 |
| african_lens | 784 | 0.028 | 0.379 | 0.111 | 0.365 |
| romanian_lens | 1,007 | 0.012 | 0.275 | 0.112 | 0.303 |
| modern_greek_lens | 328 | 0.015 | 0.270 | 0.071 | 0.404 |
| dutch_lens | 321 | 0.012 | 0.297 | 0.229 | 0.190 |
| china_list_lens | 2,000 | 0.061 | 0.334 | 0.344 | 0.120 |
| greatestbooks_head | 2,000 | 0.148 | 0.456 | 0.179 | 0.311 |
| eastern_central | 2,000 | 0.079 | 0.350 | 0.053 | 0.533 |
| francophone_lens | 2,000 | 0.084 | 0.423 | 0.091 | 0.460 |
| anglophone_lens | 2,000 | 0.057 | 0.424 | 0.241 | 0.250 |
| contemporary_1980_2017 | 2,000 | 0.065 | 0.282 | 0.320 | 0.096 |
| postwar_1946_1979 | 2,000 | 0.046 | 0.414 | 0.245 | 0.227 |
| modernist_1900_1945 | 2,000 | 0.061 | 0.444 | 0.117 | 0.379 |
| historical_pre1900 | 2,000 | 0.101 | 0.418 | 0.146 | 0.351 |

The China list and contemporary-period origin lean toward the popular/romance control basin; Dutch also has limited separation. They should be retained as adversarial diagnostics, not allowed to dominate a final ensemble. Africa, Romania, Greece, and Dutch have small teacher pools, so their individual heads are much less certain.

## Stability to removing an origin

Removing each literary origin in turn changes the ensemble top 50 by a mean Jaccard of **0.882** (range 0.786–1.000) and the top 200 by **0.923** (range 0.896–0.951). The mean pairwise top-200 overlap stays between **0.348** and **0.379**. No single origin creates the convergence.

## Current ranking alignment

Mean overlap of an individual literary-origin ranking with the current ranking is J@50/J@200 **0.234/0.328**. For controls it is only **0.007/0.035**. The independent ensemble reaches **0.370/0.384**.

## Multi-origin held-out ensemble head

This ordering uses only frequency and censored rank across the 14 alternative literary juries. The current consensus rank is shown for comparison but is not a tiebreaker.

| Rank | Book | top-50 origins | top-200 origins | mean rank | current rank |
|---:|---|---:|---:|---:|---:|
| 1 | *East of Eden* — John Steinbeck | 13/14 | 14/14 | 17.5 | 30 |
| 2 | *Stoner* — John  Williams | 13/14 | 14/14 | 31.6 | 23 |
| 3 | *The Importance of Being Earnest* — Oscar Wilde | 11/14 | 14/14 | 29.1 | 42 |
| 4 | *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne | 11/14 | 14/14 | 33.9 | 238 |
| 5 | *The Raven* — Edgar Allan Poe | 10/14 | 14/14 | 31.9 | 64 |
| 6 | *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien | 10/14 | 14/14 | 36.9 | 407 |
| 7 | *Twenty Love Poems and a Song of Despair* — Pablo Neruda | 10/14 | 14/14 | 55.4 | 66 |
| 8 | *The Adventures of Sherlock Holmes* — Arthur Conan Doyle | 9/14 | 14/14 | 49.3 | 15 |
| 9 | *Alice's Adventures in Wonderland & Through the Looking-Glass* — Lewis Carroll | 8/14 | 14/14 | 61.9 | 25 |
| 10 | *The Things They Carried* — Tim O'Brien | 7/14 | 14/14 | 63.2 | 242 |
| 11 | *A Midsummer Night's Dream* — William Shakespeare | 7/14 | 14/14 | 68.6 | 307 |
| 12 | *A Streetcar Named Desire* — Tennessee Williams | 6/14 | 14/14 | 53.3 | 33 |
| 13 | *Infinite Jest* — David Foster Wallace | 6/14 | 14/14 | 78.1 | 28 |
| 14 | *Ariel* — Sylvia Plath | 3/14 | 14/14 | 70.4 | 108 |
| 15 | *I, Claudius (Claudius, #1)* — Robert Graves | 2/14 | 14/14 | 92.9 | 152 |
| 16 | *Shakespeare's Sonnets* — William Shakespeare | 12/14 | 13/14 | 26.1 | 13 |
| 17 | *Othello* — William Shakespeare | 10/14 | 13/14 | 56.9 | 47 |
| 18 | *Inferno (The Divine Comedy #1)* — Dante Alighieri | 9/14 | 13/14 | 59.6 | 9 |
| 19 | *The Yellow Wall-Paper* — Charlotte Perkins Gilman | 8/14 | 13/14 | 63.5 | 77 |
| 20 | *Romeo and Juliet* — William Shakespeare | 8/14 | 13/14 | 65.1 | 129 |
| 21 | *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien | 8/14 | 13/14 | 76.8 | 3505 |
| 22 | *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien | 7/14 | 13/14 | 70.5 | 3699 |
| 23 | *Songs of Innocence and of Experience* — William Blake | 7/14 | 13/14 | 71.7 | 63 |
| 24 | *A Little Princess* — Frances Hodgson Burnett | 7/14 | 13/14 | 91.1 | 750 |
| 25 | *A Christmas Carol* — Charles Dickens | 5/14 | 13/14 | 84.6 | 416 |
| 26 | *The Importance of Being Earnest and Other Plays* — Oscar Wilde | 4/14 | 13/14 | 84.1 | 237 |
| 27 | *Much Ado About Nothing* — William Shakespeare | 4/14 | 13/14 | 89.0 | 156 |
| 28 | *Cyrano de Bergerac* — Edmond Rostand | 1/14 | 13/14 | 110.6 | 115 |
| 29 | *Of Human Bondage* — W. Somerset Maugham | 0/14 | 13/14 | 137.0 | 104 |
| 30 | *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust | 11/14 | 12/14 | 59.3 | 27 |
| 31 | *Les Fleurs du Mal* — Charles Baudelaire | 11/14 | 12/14 | 60.6 | 8 |
| 32 | *Lonesome Dove* — Larry McMurtry | 9/14 | 12/14 | 80.4 | 325 |
| 33 | *Four Quartets* — T.S. Eliot | 9/14 | 12/14 | 83.7 | 75 |
| 34 | *The Essential Rumi* — Jalaluddin Mevlana Rumi | 8/14 | 12/14 | 69.1 | 204 |
| 35 | *Roots: The Saga of an American Family* — Alex Haley | 8/14 | 12/14 | 84.9 | 604 |
| 36 | *Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead* — Fyodor Dostoyevsky | 8/14 | 12/14 | 86.0 | 17 |
| 37 | *The Death of Ivan Ilych* — Leo Tolstoy | 7/14 | 12/14 | 96.1 | 11 |
| 38 | *The Overcoat* — Nikolai Gogol | 6/14 | 12/14 | 87.4 | 40 |
| 39 | *From the Mixed-Up Files of Mrs. Basil E. Frankweiler* — E.L. Konigsburg | 6/14 | 12/14 | 89.2 | 437 |
| 40 | *Bring Up the Bodies (Thomas Cromwell, #2)* — Hilary Mantel | 6/14 | 12/14 | 100.7 | 524 |
| 41 | *Germinal (Les Rougon-Macquart, #13)* — Emile Zola | 5/14 | 12/14 | 112.7 | 99 |
| 42 | *Richard III* — William Shakespeare | 4/14 | 12/14 | 104.3 | 50 |
| 43 | *Chess Story* — Stefan Zweig | 4/14 | 12/14 | 107.4 | 72 |
| 44 | *Alice in Wonderland* — Jane Carruth | 1/14 | 12/14 | 123.6 | 141 |
| 45 | *The Tell-Tale Heart* — Edgar Allan Poe | 1/14 | 12/14 | 123.6 | 119 |
| 46 | *The Name of the Rose* — Umberto Eco | 1/14 | 12/14 | 141.4 | 58 |
| 47 | *On the Banks of Plum Creek  (Little House, #4)* — Laura Ingalls Wilder | 1/14 | 12/14 | 150.1 | 1287 |
| 48 | *Johnny Got His Gun* — Dalton Trumbo | 0/14 | 12/14 | 123.1 | 323 |
| 49 | *We Have Always Lived in the Castle* — Shirley Jackson | 0/14 | 12/14 | 134.5 | 241 |
| 50 | *The Wind-Up Bird Chronicle* — Haruki Murakami | 0/14 | 12/14 | 139.6 | 109 |
| 51 | *Twelfth Night* — William Shakespeare | 0/14 | 12/14 | 140.6 | 169 |
| 52 | *If on a Winter's Night a Traveler* — Italo Calvino | 0/14 | 12/14 | 144.1 | 43 |
| 53 | *Rosencrantz and Guildenstern Are Dead* — Tom Stoppard | 0/14 | 12/14 | 151.5 | 452 |
| 54 | *A Monster Calls* — Patrick Ness | 9/14 | 11/14 | 84.1 | 3653 |
| 55 | *100 Love Sonnets* — Pablo Neruda | 9/14 | 11/14 | 86.0 | 295 |
| 56 | *A Tree Grows in Brooklyn* — Betty  Smith | 7/14 | 11/14 | 91.3 | 559 |
| 57 | *Notes from Underground* — Fyodor Dostoyevsky | 7/14 | 11/14 | 103.9 | 24 |
| 58 | *Wonder (Wonder #1)* — R.J. Palacio | 7/14 | 11/14 | 108.2 | 3891 |
| 59 | *The Lottery* — Shirley Jackson | 6/14 | 11/14 | 103.7 | 286 |
| 60 | *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie | 5/14 | 11/14 | 112.7 | 1452 |
| 61 | *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante | 4/14 | 11/14 | 125.6 | 442 |
| 62 | *The Ultimate Hitchhiker's Guide to the Galaxy* — Douglas Adams | 3/14 | 11/14 | 131.6 | 647 |
| 63 | *The Memoirs of Sherlock Holmes* — Arthur Conan Doyle | 3/14 | 11/14 | 144.7 | 145 |
| 64 | *Complete Poems, 1904-1962* — E.E. Cummings | 3/14 | 11/14 | 146.9 | 215 |
| 65 | *The Return of Sherlock Holmes* — Arthur Conan Doyle | 2/14 | 11/14 | 139.9 | 65 |
| 66 | *Bartleby the Scrivener* — Herman Melville | 2/14 | 11/14 | 154.1 | 38 |
| 67 | *Blindness* — Jose Saramago | 1/14 | 11/14 | 146.7 | 136 |
| 68 | *Anne of Avonlea (Anne of Green Gables, #2)* — L.M. Montgomery | 1/14 | 11/14 | 155.1 | 777 |
| 69 | *I Capture the Castle* — Dodie Smith | 1/14 | 11/14 | 159.9 | 692 |
| 70 | *Cat on a Hot Tin Roof* — Tennessee Williams | 0/14 | 11/14 | 145.1 | 472 |
| 71 | *Who's Afraid of Virginia Woolf?* — Edward Albee | 0/14 | 11/14 | 150.9 | 162 |
| 72 | *Flowers for Algernon* — Daniel Keyes | 0/14 | 11/14 | 153.9 | 582 |
| 73 | *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust | 8/14 | 10/14 | 105.6 | 49 |
| 74 | *The Annotated Alice: The Definitive Edition* — Lewis Carroll | 8/14 | 10/14 | 112.1 | 266 |
| 75 | *Gone with the Wind* — Margaret Mitchell | 7/14 | 10/14 | 114.5 | 3916 |

## What this does not prove

- The 51-feature behavior panel and candidate universe were developed in the existing pipeline. Anchor-book identity is removed, but those structural choices are not fully seed-free.
- Goodreads users, translations, editions, exposure, and list-to-Goodreads matching are uneven. The regional tests are therefore lower bounds on cultural distinctiveness, not clean samples of regional readership.
- The experiment establishes a stable basin, not a unique or objective canon. A different platform or a deliberately non-Goodreads population could produce another stable basin.
- Popularity is reduced by balanced per-reader scoring and evidence thresholds, but it cannot be removed from who encountered and rated a book.

## Recommended use

Keep the present conservative ranking as the main product for now. Use this audit as evidence that its central literary signal is natural within Goodreads, and use the multi-origin frequency/rank as a new robustness diagnostic. The next high-value model change is a seed-ensemble jury: average or shrink the well-powered literary-origin membership scores while down-weighting origins with weak reconstruction or excessive control similarity. That should reduce seed-specific ordering without pretending all origins have equal evidence.

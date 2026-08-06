# External-canon omission audit

This is a diagnostic crosswalk, not a validation target. The comparison lists can contain popularity, curriculum, language, prize, and list-copying effects; disagreement is evidence to explain, not automatically an error in the distributed model.

## Coverage

### lit_2014_2024

- Matched 97 of 100; 50 are in the distributed top 200 (51.5% of matched works).
- Omission/status counts: `{'scored_below_top_200': 24, 'current_top_200': 50, 'is_nonfiction': 11, 'aggregate_or_cycle': 3, 'above_hard_80k_catalog_ceiling': 7, 'below_pair_mass_10': 4, 'is_collection': 1}`.
- Rank correlation among works scoreable above the publication threshold: 0.392.

- Source rank versus log Goodreads catalog count: -0.365 (negative means the source head is more popular). Top-25 median n=15,298; ranks 26–100 median n=6,243.

### greatestbooks_2026

- Matched 98 of 100; 51 are in the distributed top 200 (52.0% of matched works).
- Omission/status counts: `{'scored_below_top_200': 32, 'aggregate_or_cycle': 2, 'above_hard_80k_catalog_ceiling': 12, 'current_top_200': 51, 'is_nonfiction': 2, 'is_collection': 1}`.
- Rank correlation among works scoreable above the publication threshold: 0.143.

- Source rank versus log Goodreads catalog count: -0.338 (negative means the source head is more popular). Top-25 median n=37,267; ranks 26–100 median n=16,866.

### love_default

- Matched 100 of 100; 69 are in the distributed top 200 (69.0% of matched works).
- Omission/status counts: `{'current_top_200': 69, 'scored_below_top_200': 12, 'below_pair_mass_10': 17, 'above_hard_80k_catalog_ceiling': 2}`.
- Rank correlation among works scoreable above the publication threshold: 0.210.

- Source rank versus log Goodreads catalog count: -0.030 (negative means the source head is more popular). Top-25 median n=2,820; ranks 26–100 median n=2,478.

## Popularity signal, cautiously interpreted

The external heads are more widely read on Goodreads: Greatest Books has source-rank versus log-readership rho -0.338 and a top-25 median n of 37,267, versus 16,866 below #25. The 2014–2024 literary list shows the same direction (rho -0.365). The live Love top 100 does not (rho -0.030).

This is consistent with exposure, curriculum, and repeated-list effects, but it does not identify a causal popularity bias: being canonical also causes people to read a book. The raised-ceiling scorer is the stronger diagnostic because it tests whether high readership alone is sufficient to create a high distributed score.

## Highest external omissions

### greatestbooks_2026

| Source rank | Book | Love | Distributed | Score | Reason | n |
|---:|---|---:|---:|---:|---|---:|
| 1 | *Ulysses* — James Joyce | 18 | 295 | 47.1 | scored below top 200 | 8,443 |
| 3 | *The Great Gatsby* — F. Scott Fitzgerald | 824 | — | — | above hard 80k catalog ceiling | 180,225 |
| 5 | *The Catcher in the Rye* — J.D. Salinger | 1109 | — | — | above hard 80k catalog ceiling | 146,781 |
| 6 | *Moby-Dick or, The Whale* — Herman Melville | 72 | 273 | 47.7 | scored below top 200 | 31,475 |
| 7 | *1984* — George Orwell | 67 | — | — | above hard 80k catalog ceiling | 152,321 |
| 11 | *Lolita* — Vladimir Nabokov | 29 | 263 | 48.0 | scored below top 200 | 47,579 |
| 14 | *Wuthering Heights* — Emily Bronte | 1320 | — | — | above hard 80k catalog ceiling | 85,493 |
| 15 | *Pride and Prejudice* — Jane Austen | 968 | — | — | above hard 80k catalog ceiling | 162,658 |
| 16 | *To Kill a Mockingbird* — Harper Lee | 216 | — | — | above hard 80k catalog ceiling | 206,684 |
| 19 | *Madame Bovary* — Gustave Flaubert | 570 | 606 | 40.2 | scored below top 200 | 20,475 |
| 21 | *Holy Bible: King James Version* — Anonymous | >2000 | — | — | is nonfiction | 10,909 |
| 22 | *The Adventures of Huckleberry Finn* — Mark Twain | 587 | 510 | 42.2 | scored below top 200 | 76,095 |
| 30 | *Jane Eyre* — Charlotte Bronte | 743 | — | — | above hard 80k catalog ceiling | 105,901 |
| 31 | *Heart of Darkness* — Joseph Conrad | 623 | 764 | 36.5 | scored below top 200 | 28,886 |
| 35 | *Catch-22 (Catch-22, #1)* — Joseph Heller | 121 | 248 | 48.4 | scored below top 200 | 37,916 |
| 38 | *Great Expectations* — Charles Dickens | 1174 | 264 | 47.9 | scored below top 200 | 45,015 |
| 39 | *Frankenstein* — Mary Wollstonecraft Shelley | >2000 | 460 | 43.2 | scored below top 200 | 78,386 |
| 41 | *On the Road* — Jack Kerouac | >2000 | 956 | 32.2 | scored below top 200 | 25,650 |
| 44 | *The Little Prince* — Antoine de Saint-Exupery | 128 | — | — | above hard 80k catalog ceiling | 80,094 |
| 47 | *Ficciones* — Jorge Luis Borges | >2000 | — | — | is collection | 3,709 |
| 50 | *Brave New World* — Aldous Huxley | 1147 | — | — | above hard 80k catalog ceiling | 81,565 |
| 51 | *Lord of the Flies* — William Golding | >2000 | — | — | above hard 80k catalog ceiling | 120,254 |
| 52 | *The Old Man and the Sea* — Ernest Hemingway | 1529 | 959 | 32.1 | scored below top 200 | 50,776 |
| 53 | *Animal Farm* — George Orwell | 786 | — | — | above hard 80k catalog ceiling | 148,699 |
| 55 | *Rebecca* — Daphne du Maurier | 883 | 355 | 45.5 | scored below top 200 | 31,368 |
| 56 | *Dracula* — Bram Stoker | >2000 | 1063 | 27.2 | scored below top 200 | 60,999 |
| 57 | *The Sun Also Rises* — Ernest Hemingway | 1324 | 789 | 36.0 | scored below top 200 | 24,249 |
| 60 | *Things Fall Apart (The African Trilogy, #1)* — Chinua Achebe | 1916 | 862 | 34.6 | scored below top 200 | 21,326 |
| 62 | *Under the Volcano* — Malcolm Lowry | 334 | 307 | 46.9 | scored below top 200 | 1,408 |
| 63 | *The Golden Notebook* — Doris Lessing | 887 | 420 | 44.0 | scored below top 200 | 1,802 |

### lit_2014_2024

| Source rank | Book | Love | Distributed | Score | Reason | n |
|---:|---|---:|---:|---:|---|---:|
| 1 | *Moby-Dick or, The Whale* — Herman Melville | 72 | 273 | 47.7 | scored below top 200 | 31,475 |
| 3 | *Lolita* — Vladimir Nabokov | 29 | 263 | 48.0 | scored below top 200 | 47,579 |
| 5 | *Ulysses* — James Joyce | 18 | 295 | 47.1 | scored below top 200 | 8,443 |
| 10 | *Holy Bible: King James Version* — Anonymous | >2000 | — | — | is nonfiction | 10,909 |
| 22 | *1984* — George Orwell | 67 | — | — | above hard 80k catalog ceiling | 152,321 |
| 27 | *Dubliners* — James Joyce | 347 | 243 | 48.5 | scored below top 200 | 9,967 |
| 28 | *Catch-22 (Catch-22, #1)* — Joseph Heller | 121 | 248 | 48.4 | scored below top 200 | 37,916 |
| 30 | *The Catcher in the Rye* — J.D. Salinger | 1109 | — | — | above hard 80k catalog ceiling | 146,781 |
| 36 | *A Portrait of the Artist as a Young Man* — James Joyce | 641 | 394 | 44.6 | scored below top 200 | 10,695 |
| 37 | *Thus Spoke Zarathustra* — Friedrich Nietzsche | >2000 | — | — | is nonfiction | 6,727 |
| 41 | *Mason & Dixon* — Thomas Pynchon | 156 | 240 | 48.6 | scored below top 200 | 644 |
| 46 | *Siddhartha* — Hermann Hesse | 1160 | 329 | 46.1 | scored below top 200 | 33,775 |
| 49 | *Heart of Darkness* — Joseph Conrad | 623 | 764 | 36.5 | scored below top 200 | 28,886 |
| 50 | *No Longer Human* — Osamu Dazai | 742 | — | 44.4 | below pair mass 10 | 905 |
| 51 | *Brave New World* — Aldous Huxley | 1147 | — | — | above hard 80k catalog ceiling | 81,565 |
| 52 | *Dune (Dune Chronicles #1)* — Frank Herbert | 151 | 228 | 49.1 | scored below top 200 | 42,545 |
| 55 | *American Psycho* — Bret Easton Ellis | >2000 | 1011 | 30.3 | scored below top 200 | 15,548 |
| 57 | *The Republic* — Plato | >2000 | — | — | is nonfiction | 9,642 |
| 58 | *The Recognitions* — William Gaddis | 35 | 235 | 48.8 | scored below top 200 | 341 |
| 59 | *V.* — Thomas Pynchon | 523 | 218 | 49.6 | scored below top 200 | 1,324 |
| 60 | *Slaughterhouse-Five* — Kurt Vonnegut Jr. | 164 | 538 | 41.5 | scored below top 200 | 63,568 |
| 61 | *The Sailor Who Fell from Grace with the Sea* — Yukio Mishima | 1164 | 478 | 42.8 | scored below top 200 | 1,387 |
| 62 | *The Great Gatsby* — F. Scott Fitzgerald | 824 | — | — | above hard 80k catalog ceiling | 180,225 |
| 63 | *Wuthering Heights* — Emily Bronte | 1320 | — | — | above hard 80k catalog ceiling | 85,493 |
| 65 | *Meditations* — Marcus Aurelius | >2000 | — | — | is nonfiction | 4,015 |
| 68 | *Confessions* — Augustine of Hippo | >2000 | — | — | is nonfiction | 2,630 |
| 69 | *The Old Man and the Sea* — Ernest Hemingway | 1529 | 959 | 32.1 | scored below top 200 | 50,776 |
| 71 | *The Hobbit* — J.R.R. Tolkien | 608 | — | — | above hard 80k catalog ceiling | 154,068 |
| 72 | *Finnegans Wake* — James Joyce | 962 | 399 | 44.5 | scored below top 200 | 1,014 |
| 73 | *The Crying of Lot 49* — Thomas Pynchon | 886 | 527 | 41.8 | scored below top 200 | 5,257 |

### love_default

| Source rank | Book | Love | Distributed | Score | Reason | n |
|---:|---|---:|---:|---:|---|---:|
| 18 | *Ulysses* — James Joyce | 18 | 295 | 47.1 | scored below top 200 | 8,443 |
| 22 | *The Last Question* — Isaac Asimov | 22 | — | 48.4 | below pair mass 10 | 1,568 |
| 24 | *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante | 24 | 350 | 45.6 | scored below top 200 | 5,464 |
| 29 | *Lolita* — Vladimir Nabokov | 29 | 263 | 48.0 | scored below top 200 | 47,579 |
| 32 | *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien | 32 | 402 | 44.4 | scored below top 200 | 49,797 |
| 34 | *Tehlikeli Oyunlar* — Oguz Atay | 34 | — | 50.4 | below pair mass 10 | 491 |
| 35 | *The Recognitions* — William Gaddis | 35 | 235 | 48.8 | scored below top 200 | 341 |
| 45 | *The Annotated Alice: The Definitive Edition* — Lewis Carroll | 45 | — | 48.4 | below pair mass 10 | 1,054 |
| 51 | *The Story of the Lost Child (The Neapolitan Novels, #4)* — Elena Ferrante | 51 | — | 44.1 | below pair mass 10 | 3,443 |
| 52 | *Lonesome Dove* — Larry McMurtry | 52 | 284 | 47.3 | scored below top 200 | 7,691 |
| 54 | *Min kamp 2 (Min kamp #2)* — Karl Ove Knausgard | 54 | — | 47.9 | below pair mass 10 | 918 |
| 57 | *Those Who Leave and Those Who Stay (The Neapolitan Novels #3)* — Elena Ferrante | 57 | — | 43.7 | below pair mass 10 | 4,162 |
| 60 | *The Man Without Qualities: Vol. 1* — Robert Musil | 60 | — | 48.2 | below pair mass 10 | 187 |
| 62 | *Death and the Dervish* — Mesa Selimovic | 62 | — | 49.7 | below pair mass 10 | 573 |
| 65 | *The Ultimate Hitchhiker's Guide to the Galaxy* — Douglas Adams | 65 | 428 | 43.9 | scored below top 200 | 19,406 |
| 67 | *1984* — George Orwell | 67 | — | — | above hard 80k catalog ceiling | 152,321 |
| 69 | *Austerlitz* — W.G. Sebald | 69 | 246 | 48.5 | scored below top 200 | 1,043 |
| 72 | *Moby-Dick or, The Whale* — Herman Melville | 72 | 273 | 47.7 | scored below top 200 | 31,475 |
| 75 | *Cuentos completos 1* — Julio Cortazar | 75 | — | 46.5 | below pair mass 10 | 399 |
| 76 | *Remembrance of Things Past: Volume I - Swann's Way & Within a Budding Grove* — Marcel Proust | 76 | — | 51.1 | below pair mass 10 | 358 |
| 80 | *Warlock (Legends West, #1)* — Oakley Hall | 80 | — | 45.1 | below pair mass 10 | 177 |
| 81 | *Conversation in the Cathedral* — Mario Vargas Llosa | 81 | — | 49.1 | below pair mass 10 | 485 |
| 82 | *Little, Big* — John Crowley | 82 | — | 44.8 | below pair mass 10 | 1,087 |
| 83 | *Gormenghast (Gormenghast, #2)* — Mervyn Peake | 83 | — | 45.7 | below pair mass 10 | 1,056 |
| 84 | *The Bridge on the Drina* — Ivo Andric | 84 | 201 | 50.1 | scored below top 200 | 1,229 |
| 88 | *Housekeeping* — Marilynne Robinson | 88 | 252 | 48.4 | scored below top 200 | 3,315 |
| 89 | *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien | 89 | — | — | above hard 80k catalog ceiling | 119,871 |
| 94 | *A Brief History of Seven Killings* — Marlon James | 94 | — | 41.8 | below pair mass 10 | 2,063 |
| 96 | *The Last Samurai* — Helen DeWitt | 96 | — | 45.1 | below pair mass 10 | 391 |
| 97 | *Butcher's Crossing* — John  Williams | 97 | — | 46.1 | below pair mass 10 | 686 |

## Immediate interpretation of the three motivating books

- **Ulysses:** high live-jury love but a much lower conservative distributed score. The gap is downstream of jury selection: broad cross-community disagreement and uncertainty are the leading mechanisms, with a negative observed temporal path.
- **Moby-Dick:** also liked by the live jury, but heterogeneous enough to land below the publication top 200. Its temporal path rises, so enthusiast-first decay is not the explanation.
- **The Great Gatsby:** unlike the other two, it is only #824 on live Love and is then removed before distributed scoring by the hard 80,000-rating ceiling. Its absence therefore combines weak distinctive enthusiasm with an eligibility design choice; a raised-ceiling counterfactual is required before judging its model rank.

## Next diagnostic

Rerun the expanded-prior model with the 80,000 ceiling raised while keeping all other rules fixed. Compare newly admitted mega-read books both before and after evidence saturation. This separates a popularity *eligibility ban* from actual jury esteem and cross-community consensus; it is more informative than promoting external-list books by fiat.

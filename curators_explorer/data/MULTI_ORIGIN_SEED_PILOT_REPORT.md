# Multi-origin semantic-seed pilot

## Design

Mapped 2,209/3,057 scraped list rows to 1,295 unique Goodreads works. Built 14 disjoint core literary origins, 1 literary border case, and 3 non-literary controls, up to 40 works each. The union of every origin is excluded from every ranking.

Small origins use a two-anchor reader threshold rather than three; they remain in the audit but are explicitly lower-information tests. The children's origin is compared with both sides but excluded from the core literary convergence average.

This is the cheap direct-affinity pilot, not the final behavioral-jury refit. It tests whether the origin construction produces literary convergence before paying for full reconstruction and hierarchical scoring.

## Origins and coverage

| Origin | Role | Works | min hits | eligible affinity users | selected jury | rankable held-out books |
|---|---|---:|---:|---:|---:|---:|
| latin_american_lens | literary | 22 | 2 | 7,753 | 2,000 | 855 |
| african_lens | literary | 33 | 3 | 784 | 784 | 291 |
| romanian_lens | literary | 19 | 2 | 1,007 | 1,007 | 292 |
| modern_greek_lens | literary | 34 | 3 | 328 | 328 | 83 |
| dutch_lens | literary | 32 | 3 | 321 | 321 | 57 |
| china_list_lens | literary | 13 | 2 | 3,290 | 2,000 | 832 |
| greatestbooks_head | literary | 40 | 3 | 250,112 | 2,000 | 1,060 |
| border_childrens_literary | border | 40 | 3 | 204,250 | 2,000 | 890 |
| eastern_central | literary | 40 | 3 | 6,680 | 2,000 | 968 |
| francophone_lens | literary | 40 | 3 | 30,317 | 2,000 | 1,087 |
| anglophone_lens | literary | 40 | 3 | 84,210 | 2,000 | 1,024 |
| contemporary_1980_2017 | literary | 40 | 3 | 46,488 | 2,000 | 933 |
| postwar_1946_1979 | literary | 40 | 3 | 100,679 | 2,000 | 930 |
| modernist_1900_1945 | literary | 40 | 3 | 44,782 | 2,000 | 1,033 |
| historical_pre1900 | literary | 40 | 3 | 82,906 | 2,000 | 985 |
| control_popular_romance | control | 40 | 3 | 107,025 | 2,000 | 637 |
| control_commercial_series | control | 40 | 3 | 449,503 | 2,000 | 555 |
| control_popular_fantasy | control | 40 | 3 | 170,164 | 2,000 | 348 |

## Convergence

- Literary↔literary mean teacher Jaccard: **0.015**; book Jaccard@50/200: **0.173/0.237**.
- Literary↔control mean teacher Jaccard: **0.002**; book Jaccard@50/200: **0.128/0.172**.
- Literary↔children's-border mean teacher Jaccard: **0.011**; book Jaccard@50/200: **0.167/0.227**.
- Books appearing in at least 75% of literary top 200s: **35**.

## Shared held-out literary head

| Book | origins top-200 | current consensus rank |
|---|---:|---:|
| *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien | 14/14 | 407 |
| *Middlesex* — Jeffrey Eugenides | 14/14 | 1112 |
| *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien | 14/14 | 3505 |
| *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien | 14/14 | 3699 |
| *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin | 14/14 | 4626 |
| *East of Eden* — John Steinbeck | 13/14 | 30 |
| *The Name of the Rose* — Umberto Eco | 13/14 | 58 |
| *The Wind-Up Bird Chronicle* — Haruki Murakami | 13/14 | 109 |
| *Blindness* — Jose Saramago | 13/14 | 136 |
| *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin | 13/14 | 2901 |
| *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin | 13/14 | 4593 |
| *Stoner* — John  Williams | 12/14 | 23 |
| *Alice's Adventures in Wonderland & Through the Looking-Glass* — Lewis Carroll | 12/14 | 25 |
| *The Importance of Being Earnest* — Oscar Wilde | 12/14 | 42 |
| *Alice in Wonderland* — Jane Carruth | 12/14 | 141 |
| *A Tree Grows in Brooklyn* — Betty  Smith | 12/14 | 559 |
| *Flowers for Algernon* — Daniel Keyes | 12/14 | 582 |
| *The Ultimate Hitchhiker's Guide to the Galaxy* — Douglas Adams | 12/14 | 647 |
| *A Monster Calls* — Patrick Ness | 12/14 | 3653 |
| *Wonder (Wonder #1)* — R.J. Palacio | 12/14 | 3891 |
| *Gone with the Wind* — Margaret Mitchell | 12/14 | 3916 |
| *The Shadow of the Wind (The Cemetery of Forgotten Books,  #1)* — Carlos Ruiz Zafon | 12/14 | 4431 |
| *Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead* — Fyodor Dostoyevsky | 11/14 | 17 |
| *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust | 11/14 | 27 |
| *Othello* — William Shakespeare | 11/14 | 47 |
| *The Things They Carried* — Tim O'Brien | 11/14 | 242 |
| *Cat's Cradle* — Kurt Vonnegut Jr. | 11/14 | 281 |
| *The Godfather* — Mario Puzo | 11/14 | 297 |
| *A Midsummer Night's Dream* — William Shakespeare | 11/14 | 307 |
| *Cloud Atlas* — David Mitchell | 11/14 | 374 |
| *A Christmas Carol* — Charles Dickens | 11/14 | 416 |
| *A Prayer for Owen Meany* — John Irving | 11/14 | 436 |
| *Homegoing* — Yaa Gyasi | 11/14 | 1035 |
| *A Little Life* — Hanya Yanagihara | 11/14 | 1503 |
| *Ender's Game (Ender's Saga, #1)* — Orson Scott Card | 11/14 | 4685 |

## Origin heads

### latin_american_lens

1. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (87.7 +/-3.2, mass 71.5)
2. *The Poetry of Pablo Neruda* — Pablo Neruda (86.6 +/-6.1, mass 12.0)
3. *الطنطورية* — Radwa Ashour (86.2 +/-6.3, mass 11.8)
4. *Conversation in the Cathedral* — Mario Vargas Llosa (86.2 +/-5.2, mass 23.2)
5. *Infinite Jest* — David Foster Wallace (85.7 +/-3.4, mass 73.1)
6. *Stoner* — John  Williams (85.7 +/-3.9, mass 53.5)
7. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (84.9 +/-3.4, mass 82.5)
8. *Chess Story* — Stefan Zweig (83.6 +/-5.5, mass 26.6)
9. *East of Eden* — John Steinbeck (83.5 +/-3.5, mass 82.1)
10. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (83.1 +/-6.9, mass 13.8)
11. *The Rings of Saturn* — W.G. Sebald (81.5 +/-7.2, mass 14.3)
12. *A Constellation of Vital Phenomena* — Anthony Marra (81.0 +/-6.7, mass 18.9)
13. *The War of the End of the World* — Mario Vargas Llosa (80.6 +/-5.7, mass 31.0)
14. *100 Love Sonnets* — Pablo Neruda (80.3 +/-7.5, mass 14.4)
15. *The Recognitions* — William Gaddis (80.1 +/-8.1, mass 11.1)

### african_lens

1. *Homegoing* — Yaa Gyasi (80.5 +/-5.8, mass 29.7)
2. *East of Eden* — John Steinbeck (80.0 +/-5.4, mass 36.8)
3. *Twenty Love Poems and a Song of Despair* — Pablo Neruda (78.8 +/-7.5, mass 16.2)
4. *Bring Up the Bodies (Thomas Cromwell, #2)* — Hilary Mantel (77.1 +/-8.6, mass 12.1)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (75.6 +/-7.2, mass 23.2)
6. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (75.4 +/-6.9, mass 25.8)
7. *A Monster Calls* — Patrick Ness (74.0 +/-9.0, mass 13.3)
8. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (72.8 +/-7.6, mass 22.9)
9. *The Orphan Master's Son* — Adam Johnson (72.7 +/-9.9, mass 10.8)
10. *Wizard of the Crow* — Ngugi wa Thiong'o (72.4 +/-9.2, mass 13.9)
11. *The Left Hand of Darkness* — Ursula K. Le Guin (70.8 +/-8.9, mass 16.5)
12. *Roots: The Saga of an American Family* — Alex Haley (70.8 +/-9.7, mass 13.0)
13. *The Importance of Being Earnest* — Oscar Wilde (70.5 +/-6.8, mass 34.2)
14. *The Blind Assassin* — Margaret Atwood (70.2 +/-7.4, mass 27.8)
15. *for colored girls who have considered suicide/when the rainbow is enuf* — Ntozake Shange (68.8 +/-9.9, mass 13.2)

### romanian_lens

1. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (86.4 +/-4.2, mass 41.1)
2. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (85.0 +/-3.9, mass 56.9)
3. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (84.5 +/-3.2, mass 94.4)
4. *Shōgun (Asian Saga, #1)* — James Clavell (81.0 +/-4.7, mass 49.2)
5. *Oscar et la dame rose* — Eric-Emmanuel Schmitt (80.2 +/-4.4, mass 62.3)
6. *Flowers for Algernon* — Daniel Keyes (79.9 +/-4.9, mass 48.8)
7. *Gone with the Wind* — Margaret Mitchell (79.7 +/-3.5, mass 105.5)
8. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (79.5 +/-5.3, mass 40.7)
9. *A Monster Calls* — Patrick Ness (79.0 +/-7.5, mass 16.2)
10. *Middlesex* — Jeffrey Eugenides (77.9 +/-7.4, mass 18.3)
11. *Gog* — Giovanni Papini (77.6 +/-8.8, mass 10.5)
12. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (77.2 +/-8.0, mass 15.1)
13. *Quo Vadis* — Henryk Sienkiewicz (77.0 +/-5.0, mass 54.0)
14. *Blindness* — Jose Saramago (77.0 +/-5.8, mass 37.4)
15. *Extremely Loud and Incredibly Close* — Jonathan Safran Foer (76.9 +/-5.9, mass 36.3)

### modern_greek_lens

1. *Antigone (The Theban Plays, #3)* — Sophocles (91.4 +/-3.8, mass 23.1)
2. *Le Monogramme* — Odysseus Elytis (89.9 +/-3.4, mass 45.4)
3. *Report to Greco* — Nikos Kazantzakis (86.0 +/-5.2, mass 23.4)
4. *The Last Temptation of Christ* — Nikos Kazantzakis (83.9 +/-4.5, mass 44.8)
5. *A Christmas Carol* — Charles Dickens (80.8 +/-7.6, mass 12.8)
6. *Η φόνισσα* — Alexandros Papadiamantis (80.4 +/-4.8, mass 49.3)
7. *What a Carve Up!* — Jonathan Coe (79.5 +/-7.4, mass 15.8)
8. *The Name of the Rose* — Umberto Eco (78.9 +/-5.4, mass 39.5)
9. *Burial Rites* — Hannah Kent (78.3 +/-7.2, mass 19.1)
10. *The Shadow of the Wind (The Cemetery of Forgotten Books,  #1)* — Carlos Ruiz Zafon (75.8 +/-7.7, mass 18.4)
11. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (75.7 +/-8.0, mass 16.9)
12. *Γκιακ* — Demosthenes Papamarkos (74.1 +/-7.6, mass 21.5)
13. *Murder on the Orient Express (Hercule Poirot, #10)* — Agatha Christie (72.2 +/-8.8, mass 15.8)
14. *Το λάθος* — Antonis Samarakis (68.9 +/-7.3, mass 30.3)
15. *Middlesex* — Jeffrey Eugenides (65.4 +/-8.6, mass 22.6)

### dutch_lens

1. *The Brothers Lionheart* — Astrid Lindgren (85.8 +/-6.2, mass 12.9)
2. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (78.1 +/-8.8, mass 10.3)
3. *Middlesex* — Jeffrey Eugenides (75.2 +/-9.5, mass 10.1)
4. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (75.2 +/-7.7, mass 19.5)
5. *The Wind-Up Bird Chronicle* — Haruki Murakami (75.0 +/-7.7, mass 19.3)
6. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (74.4 +/-7.0, mass 25.9)
7. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (72.3 +/-8.2, mass 18.9)
8. *Alice's Adventures in Wonderland & Through the Looking-Glass* — Lewis Carroll (71.9 +/-7.6, mass 24.2)
9. *The Thousand Autumns of Jacob de Zoet* — David Mitchell (70.8 +/-10.5, mass 10.2)
10. *Blindness* — Jose Saramago (69.6 +/-9.6, mass 14.2)
11. *Extremely Loud and Incredibly Close* — Jonathan Safran Foer (68.4 +/-6.7, mass 37.3)
12. *The New York Trilogy* — Paul Auster (67.4 +/-9.4, mass 16.3)
13. *The Name of the Rose* — Umberto Eco (67.0 +/-8.0, mass 25.2)
14. *The Witches* — Roald Dahl (66.8 +/-9.7, mass 15.6)
15. *Cloud Atlas* — David Mitchell (66.5 +/-9.5, mass 16.6)

### china_list_lens

1. *The Nightingale* — Kristin Hannah (86.9 +/-2.3, mass 169.5)
2. *A Tree Grows in Brooklyn* — Betty  Smith (86.2 +/-2.1, mass 228.3)
3. *Wonder (Wonder #1)* — R.J. Palacio (84.6 +/-3.1, mass 102.5)
4. *Roots: The Saga of an American Family* — Alex Haley (84.1 +/-3.6, mass 74.9)
5. *Different Seasons* — Stephen King (82.5 +/-5.8, mass 25.1)
6. *Homegoing* — Yaa Gyasi (82.1 +/-5.0, mass 38.0)
7. *East of Eden* — John Steinbeck (82.0 +/-2.6, mass 185.9)
8. *A Gentleman in Moscow* — Amor Towles (81.8 +/-5.1, mass 38.3)
9. *Gone with the Wind* — Margaret Mitchell (81.6 +/-2.2, mass 265.1)
10. *Someone Knows My Name* — Lawrence Hill (81.5 +/-4.9, mass 42.9)
11. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (80.6 +/-4.1, mass 68.6)
12. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (79.5 +/-4.4, mass 63.1)
13. *Exodus* — Leon Uris (79.4 +/-5.6, mass 34.7)
14. *The Green Mile* — Stephen King (78.6 +/-5.5, mass 38.1)
15. *A Monster Calls* — Patrick Ness (77.9 +/-6.2, mass 29.0)

### greatestbooks_head

1. *East of Eden* — John Steinbeck (89.6 +/-2.2, mass 138.7)
2. *Les Fleurs du Mal* — Charles Baudelaire (88.6 +/-4.7, mass 20.3)
3. *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust (88.3 +/-3.5, mass 54.1)
4. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (86.4 +/-2.8, mass 116.7)
5. *The Things They Carried* — Tim O'Brien (85.0 +/-3.9, mass 58.3)
6. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (84.8 +/-3.2, mass 93.9)
7. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (84.7 +/-2.3, mass 206.5)
8. *The Overcoat* — Nikolai Gogol (84.4 +/-6.8, mass 11.8)
9. *Chess Story* — Stefan Zweig (84.3 +/-6.6, mass 13.5)
10. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (84.2 +/-3.1, mass 106.1)
11. *The Story of the Lost Child (The Neapolitan Novels, #4)* — Elena Ferrante (83.1 +/-5.6, mass 26.7)
12. *Of Human Bondage* — W. Somerset Maugham (82.9 +/-5.4, mass 29.0)
13. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (82.4 +/-7.0, mass 14.0)
14. *Romeo and Juliet* — William Shakespeare (81.9 +/-2.2, mass 268.4)
15. *Othello* — William Shakespeare (81.8 +/-3.5, mass 93.4)

### border_childrens_literary

1. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (91.4 +/-1.8, mass 184.9)
2. *From the Mixed-Up Files of Mrs. Basil E. Frankweiler* — E.L. Konigsburg (90.2 +/-2.5, mass 92.8)
3. *The Witches* — Roald Dahl (89.9 +/-2.2, mass 144.2)
4. *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne (89.2 +/-3.7, mass 38.5)
5. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (88.7 +/-2.1, mass 176.2)
6. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (88.4 +/-1.6, mass 333.8)
7. *Little House on the Prairie (Little House, #2)* — Laura Ingalls Wilder (87.3 +/-2.6, mass 119.7)
8. *A Little Princess* — Frances Hodgson Burnett (87.2 +/-2.4, mass 151.3)
9. *The Lion, the Witch, and the Wardrobe (Chronicles of Narnia, #1)* — C.S. Lewis (87.1 +/-1.7, mass 309.6)
10. *The Brothers Lionheart* — Astrid Lindgren (87.0 +/-5.5, mass 16.9)
11. *The Nightingale* — Kristin Hannah (86.1 +/-3.2, mass 84.1)
12. *Mrs. Frisby and the Rats of NIMH (Rats of NIMH, #1)* — Robert C. O'Brien (85.7 +/-3.5, mass 68.6)
13. *Anne of the Island (Anne of Green Gables, #3)* — L.M. Montgomery (85.7 +/-3.2, mass 84.8)
14. *Anne of Avonlea (Anne of Green Gables, #2)* — L.M. Montgomery (85.6 +/-3.0, mass 105.2)
15. *A Man Called Ove* — Fredrik Backman (85.3 +/-3.4, mass 79.3)

### eastern_central

1. *Besnilo* — Borislav Pekic (88.1 +/-5.4, mass 14.1)
2. *The Fortress* — Mesa Selimovic (87.8 +/-4.9, mass 22.0)
3. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (85.4 +/-6.1, mass 14.8)
4. *Ježeva kućica* — Branko Copic (85.1 +/-6.4, mass 13.4)
5. *The Grand Inquisitor* — Fyodor Dostoyevsky (83.3 +/-7.4, mass 10.3)
6. *Stoner* — John  Williams (83.2 +/-4.2, mass 56.4)
7. *East of Eden* — John Steinbeck (82.8 +/-3.3, mass 98.9)
8. *Tutunamayanlar* — Oguz Atay (81.5 +/-6.5, mass 19.3)
9. *Selected Poems* — Marina Tsvetaeva (80.4 +/-7.2, mass 16.3)
10. *Cancer Ward* — Aleksandr Solzhenitsyn (80.2 +/-5.2, mass 39.7)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (80.0 +/-3.5, mass 104.3)
12. *Martin Eden* — Jack London (79.6 +/-5.7, mass 33.1)
13. *One, None, and One Hundred Thousand* — Luigi Pirandello (79.3 +/-8.1, mass 12.2)
14. *Tales of Belkin and Other Prose Writings* — Alexander Pushkin (78.9 +/-7.1, mass 19.1)
15. *Illuminations* — Arthur Rimbaud (78.7 +/-7.7, mass 15.3)

### francophone_lens

1. *Johnny Got His Gun* — Dalton Trumbo (88.8 +/-4.9, mass 17.9)
2. *Les Fleurs du Mal* — Charles Baudelaire (87.4 +/-4.0, mass 41.3)
3. *Time Regained (In Search of Lost Time, #7)* — Marcel Proust (86.7 +/-6.1, mass 12.3)
4. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (82.9 +/-6.5, mass 17.2)
5. *The Things They Carried* — Tim O'Brien (81.6 +/-4.5, mass 52.6)
6. *Hopscotch* — Julio Cortazar (81.3 +/-5.5, mass 32.8)
7. *Bring Up the Bodies (Thomas Cromwell, #2)* — Hilary Mantel (81.3 +/-6.0, mass 25.2)
8. *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante (81.1 +/-5.9, mass 27.2)
9. *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust (80.6 +/-4.6, mass 54.0)
10. *Ariel* — Sylvia Plath (80.3 +/-6.0, mass 27.7)
11. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (80.1 +/-3.7, mass 93.3)
12. *Stoner* — John  Williams (79.3 +/-4.5, mass 61.6)
13. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (79.1 +/-4.0, mass 79.4)
14. *The Guermantes Way  (In Search of Lost Time, #3)* — Marcel Proust (78.7 +/-8.1, mass 12.8)
15. *Infinite Jest* — David Foster Wallace (78.3 +/-4.7, mass 57.0)

### anglophone_lens

1. *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante (93.9 +/-2.2, mass 64.7)
2. *Bring Up the Bodies (Thomas Cromwell, #2)* — Hilary Mantel (91.3 +/-2.6, mass 70.8)
3. *Homegoing* — Yaa Gyasi (87.9 +/-3.7, mass 47.6)
4. *Those Who Leave and Those Who Stay (The Neapolitan Novels #3)* — Elena Ferrante (87.6 +/-3.8, mass 45.7)
5. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (86.5 +/-2.8, mass 110.2)
6. *The Story of the Lost Child (The Neapolitan Novels, #4)* — Elena Ferrante (86.1 +/-4.2, mass 42.6)
7. *A Monster Calls* — Patrick Ness (83.9 +/-3.9, mass 61.5)
8. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (83.7 +/-3.2, mass 103.4)
9. *Stoner* — John  Williams (83.1 +/-5.0, mass 35.8)
10. *Arcadia* — Tom Stoppard (82.8 +/-7.4, mass 11.0)
11. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (82.2 +/-3.4, mass 101.0)
12. *East of Eden* — John Steinbeck (81.7 +/-3.6, mass 87.5)
13. *A Tree Grows in Brooklyn* — Betty  Smith (80.5 +/-3.6, mass 92.8)
14. *A Gentleman in Moscow* — Amor Towles (79.2 +/-6.5, mass 23.4)
15. *Middlesex* — Jeffrey Eugenides (78.7 +/-3.1, mass 145.9)

### contemporary_1980_2017

1. *Homegoing* — Yaa Gyasi (94.8 +/-1.6, mass 126.1)
2. *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante (92.0 +/-2.9, mass 48.6)
3. *The Orphan Master's Son* — Adam Johnson (89.1 +/-3.1, mass 63.5)
4. *A Monster Calls* — Patrick Ness (86.9 +/-3.6, mass 58.5)
5. *A Gentleman in Moscow* — Amor Towles (85.9 +/-4.2, mass 42.2)
6. *Bring Up the Bodies (Thomas Cromwell, #2)* — Hilary Mantel (85.5 +/-3.9, mass 53.5)
7. *Those Who Leave and Those Who Stay (The Neapolitan Novels #3)* — Elena Ferrante (84.8 +/-4.6, mass 38.4)
8. *The Story of the Lost Child (The Neapolitan Novels, #4)* — Elena Ferrante (84.6 +/-4.6, mass 38.9)
9. *East of Eden* — John Steinbeck (83.7 +/-3.0, mass 116.8)
10. *A Little Life* — Hanya Yanagihara (82.4 +/-3.0, mass 134.1)
11. *A Tree Grows in Brooklyn* — Betty  Smith (82.4 +/-3.2, mass 110.8)
12. *Stoner* — John  Williams (82.3 +/-5.1, mass 37.1)
13. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (82.1 +/-3.7, mass 80.0)
14. *A Constellation of Vital Phenomena* — Anthony Marra (81.5 +/-4.6, mass 50.6)
15. *Cutting for Stone* — Abraham Verghese (81.1 +/-3.4, mass 102.2)

### postwar_1946_1979

1. *The Ultimate Hitchhiker's Guide to the Galaxy* — Douglas Adams (92.9 +/-1.8, mass 133.3)
2. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (85.7 +/-2.5, mass 149.4)
3. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (85.1 +/-2.6, mass 153.3)
4. *The Things They Carried* — Tim O'Brien (84.9 +/-4.2, mass 47.7)
5. *The Hitchhiker's Guide to the Galaxy: A Trilogy in Four Parts* — Douglas Adams (84.4 +/-6.5, mass 14.2)
6. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (83.2 +/-1.9, mass 344.0)
7. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (82.4 +/-2.2, mass 254.1)
8. *East of Eden* — John Steinbeck (81.6 +/-3.9, mass 76.3)
9. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (81.5 +/-2.9, mass 143.9)
10. *Lonesome Dove* — Larry McMurtry (81.4 +/-5.5, mass 31.7)
11. *The Restaurant at the End of the Universe (Hitchhiker's Guide, #2)* — Douglas Adams (80.9 +/-3.3, mass 116.3)
12. *If on a Winter's Night a Traveler* — Italo Calvino (80.7 +/-5.8, mass 28.8)
13. *Cat's Cradle* — Kurt Vonnegut Jr. (80.2 +/-3.1, mass 133.9)
14. *Kurt Vonnegut's Cat's Cradle* — Harold Bloom (80.1 +/-7.1, mass 17.0)
15. *Flowers for Algernon* — Daniel Keyes (79.8 +/-3.4, mass 114.4)

### modernist_1900_1945

1. *East of Eden* — John Steinbeck (90.1 +/-2.0, mass 167.4)
2. *Homegoing* — Yaa Gyasi (86.6 +/-5.3, mass 19.6)
3. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (86.1 +/-2.8, mass 117.7)
4. *The Violent Bear It Away* — Flannery O'Connor (82.4 +/-7.4, mass 11.4)
5. *Songs of Innocence and of Experience* — William Blake (82.0 +/-6.4, mass 19.2)
6. *L.A. Confidential (L.A. Quartet, #3)* — James Ellroy (81.9 +/-7.6, mass 11.2)
7. *Lonesome Dove* — Larry McMurtry (81.5 +/-5.2, mass 36.6)
8. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (81.1 +/-3.3, mass 115.3)
9. *I, Claudius (Claudius, #1)* — Robert Graves (80.8 +/-6.2, mass 23.8)
10. *The Things They Carried* — Tim O'Brien (80.3 +/-4.0, mass 77.6)
11. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (79.6 +/-3.7, mass 92.1)
12. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (77.5 +/-2.6, mass 235.4)
13. *The Long Goodbye (Philip Marlowe, #6)* — Raymond Chandler (77.4 +/-6.6, mass 25.7)
14. *Four Quartets* — T.S. Eliot (77.4 +/-8.6, mass 11.7)
15. *Shakespeare's Sonnets* — William Shakespeare (77.1 +/-7.6, mass 18.0)

### historical_pre1900

1. *Othello* — William Shakespeare (87.0 +/-2.2, mass 180.5)
2. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (85.5 +/-2.1, mass 245.7)
3. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (84.7 +/-2.8, mass 135.0)
4. *The Adventures of Sherlock Holmes* — Arthur Conan Doyle (84.2 +/-3.9, mass 62.2)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (83.7 +/-3.4, mass 89.2)
6. *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante (82.9 +/-6.7, mass 14.9)
7. *Much Ado About Nothing* — William Shakespeare (82.1 +/-3.2, mass 115.2)
8. *Shakespeare's Sonnets* — William Shakespeare (81.9 +/-4.9, mass 42.6)
9. *Night Watch (Discworld, #29; City Watch, #6)* — Terry Pratchett (81.9 +/-7.2, mass 13.4)
10. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (81.8 +/-3.1, mass 129.6)
11. *A Midsummer Night's Dream* — William Shakespeare (81.1 +/-2.6, mass 187.8)
12. *The Yellow Wall-Paper* — Charlotte Perkins Gilman (79.8 +/-6.3, mass 24.7)
13. *The Importance of Being Earnest* — Oscar Wilde (79.4 +/-3.6, mass 102.7)
14. *The Raven* — Edgar Allan Poe (79.4 +/-6.2, mass 26.3)
15. *Twelfth Night* — William Shakespeare (78.7 +/-3.8, mass 94.9)

### control_popular_romance

1. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (92.1 +/-3.1, mass 36.3)
2. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (91.8 +/-2.2, mass 99.4)
3. *Wonder (Wonder #1)* — R.J. Palacio (91.4 +/-1.7, mass 199.6)
4. *The Nightingale* — Kristin Hannah (90.8 +/-1.8, mass 205.5)
5. *A Monster Calls* — Patrick Ness (86.9 +/-2.6, mass 127.5)
6. *Ready Player One* — Ernest Cline (86.1 +/-2.6, mass 141.9)
7. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (85.6 +/-2.3, mass 190.4)
8. *Still Alice* — Lisa Genova (85.1 +/-3.0, mass 109.0)
9. *A Man Called Ove* — Fredrik Backman (84.7 +/-2.7, mass 141.4)
10. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (84.7 +/-4.0, mass 54.6)
11. *Dragonfly in Amber (Outlander, #2)* — Diana Gabaldon (84.6 +/-2.4, mass 182.6)
12. *The Martian* — Andy Weir (84.5 +/-2.6, mass 160.5)
13. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (83.6 +/-3.9, mass 66.1)
14. *A Little Life* — Hanya Yanagihara (82.9 +/-4.5, mass 46.9)
15. *Homegoing* — Yaa Gyasi (82.8 +/-4.8, mass 41.1)

### control_commercial_series

1. *The Nightingale* — Kristin Hannah (91.7 +/-2.3, mass 89.3)
2. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (89.9 +/-3.4, mass 46.3)
3. *Wonder (Wonder #1)* — R.J. Palacio (89.0 +/-2.7, mass 96.8)
4. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (88.3 +/-4.2, mass 31.0)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (85.7 +/-3.2, mass 88.2)
6. *The Girl Who Played with Fire (Millennium, #2)* — Stieg Larsson (83.6 +/-2.5, mass 176.7)
7. *Ready Player One* — Ernest Cline (83.6 +/-3.4, mass 89.4)
8. *Someone Knows My Name* — Lawrence Hill (83.4 +/-7.2, mass 10.9)
9. *The Girl Who Kicked the Hornet's Nest (Millennium, #3)* — Stieg Larsson (83.0 +/-2.9, mass 138.0)
10. *A Man Called Ove* — Fredrik Backman (82.5 +/-4.3, mass 54.6)
11. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (81.5 +/-2.7, mass 172.3)
12. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (81.4 +/-3.4, mass 101.1)
13. *11/22/63* — Stephen King (81.1 +/-4.6, mass 50.2)
14. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (80.7 +/-3.7, mass 89.6)
15. *Gone with the Wind* — Margaret Mitchell (80.7 +/-3.2, mass 125.5)

### control_popular_fantasy

1. *Dead to the World (Sookie Stackhouse, #4)* — Charlaine Harris (91.0 +/-2.2, mass 122.3)
2. *The Nightingale* — Kristin Hannah (89.4 +/-4.2, mass 25.6)
3. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (88.6 +/-2.9, mass 80.0)
4. *Dead as a Doornail (Sookie Stackhouse, #5)* — Charlaine Harris (86.9 +/-2.8, mass 108.3)
5. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (86.5 +/-3.3, mass 73.3)
6. *All Together Dead (Sookie Stackhouse, #7)* — Charlaine Harris (86.0 +/-2.9, mass 104.3)
7. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (85.2 +/-2.4, mass 180.4)
8. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (84.8 +/-3.1, mass 99.9)
9. *Anna and the French Kiss (Anna and the French Kiss, #1)* — Stephanie Perkins (84.6 +/-1.8, mass 341.0)
10. *Definitely Dead (Sookie Stackhouse, #6)* — Charlaine Harris (84.5 +/-3.1, mass 102.6)
11. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (83.1 +/-5.4, mass 28.9)
12. *A Man Called Ove* — Fredrik Backman (82.9 +/-6.9, mass 14.1)
13. *The Martian* — Andy Weir (82.8 +/-3.6, mass 84.0)
14. *A Monster Calls* — Patrick Ness (82.7 +/-3.3, mass 103.3)
15. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (82.6 +/-4.2, mass 57.4)

## Decision rule

Proceed to behavioral reconstruction only if literary origins converge materially more with one another than with controls and the shared head is recognizably literary. Direct-jury convergence is not proof of seed independence; it is a prerequisite for the more expensive test.

# Multi-origin behavioral seed audit (full)

## Design

Each disjoint origin selects up to 2,000 direct-affinity teachers. A five-fold out-of-fold model reconstructs them from the current 51 generic behavior features, then selects a 3,000-reader jury. No book identity or list membership is a predictor. The union of all origin works is excluded from every ranked universe.

This stage uses the same balanced 5-star-versus-low ranker for every reconstructed jury. It isolates seed-origin dependence before the much more expensive community refit.

## Reconstruction

| Origin | Role | Works | min hits | teachers | AUC | AP | teacher/jury J | fit seconds | rankable books |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| latin_american_lens | literary | 22 | 2 | 2,000 | 0.896 | 0.036 | 0.043 | 5.7 | 300 |
| african_lens | literary | 33 | 3 | 784 | 0.905 | 0.028 | 0.036 | 6.0 | 300 |
| romanian_lens | literary | 19 | 2 | 1,007 | 0.869 | 0.012 | 0.016 | 5.6 | 300 |
| modern_greek_lens | literary | 34 | 3 | 328 | 0.959 | 0.015 | 0.023 | 5.6 | 300 |
| dutch_lens | literary | 32 | 3 | 321 | 0.929 | 0.012 | 0.018 | 6.1 | 300 |
| china_list_lens | literary | 13 | 2 | 2,000 | 0.920 | 0.061 | 0.068 | 5.6 | 300 |
| greatestbooks_head | literary | 40 | 3 | 2,000 | 0.974 | 0.148 | 0.138 | 5.7 | 300 |
| border_childrens_literary | border | 40 | 3 | 2,000 | 0.962 | 0.124 | 0.109 | 5.5 | 300 |
| eastern_central | literary | 40 | 3 | 2,000 | 0.958 | 0.079 | 0.082 | 6.5 | 300 |
| francophone_lens | literary | 40 | 3 | 2,000 | 0.954 | 0.084 | 0.087 | 5.8 | 300 |
| anglophone_lens | literary | 40 | 3 | 2,000 | 0.931 | 0.057 | 0.061 | 6.2 | 300 |
| contemporary_1980_2017 | literary | 40 | 3 | 2,000 | 0.942 | 0.065 | 0.068 | 5.6 | 300 |
| postwar_1946_1979 | literary | 40 | 3 | 2,000 | 0.925 | 0.046 | 0.051 | 5.7 | 300 |
| modernist_1900_1945 | literary | 40 | 3 | 2,000 | 0.945 | 0.061 | 0.067 | 5.6 | 300 |
| historical_pre1900 | literary | 40 | 3 | 2,000 | 0.965 | 0.101 | 0.100 | 5.7 | 300 |
| control_popular_romance | control | 40 | 3 | 2,000 | 0.949 | 0.075 | 0.076 | 5.8 | 300 |
| control_commercial_series | control | 40 | 3 | 2,000 | 0.991 | 0.304 | 0.234 | 5.8 | 300 |
| control_popular_fantasy | control | 40 | 3 | 2,000 | 0.980 | 0.202 | 0.168 | 5.5 | 300 |

## Convergence

- Literary↔literary mean reconstructed-jury Jaccard: **0.184**; book Jaccard@50/200 **0.254/0.363**.
- Literary↔control mean reconstructed-jury Jaccard: **0.022**; book Jaccard@50/200 **0.106/0.164**.
- Literary↔children's-border mean reconstructed-jury Jaccard: **0.128**; book Jaccard@50/200 **0.222/0.318**.
- Held-out books present in at least 11/14 literary top 200s: **72**.

## Shared held-out head

| Book | literary top-200s | current consensus rank |
|---|---:|---:|
| *The Adventures of Sherlock Holmes* — Arthur Conan Doyle | 14/14 | 15 |
| *Stoner* — John  Williams | 14/14 | 23 |
| *Alice's Adventures in Wonderland & Through the Looking-Glass* — Lewis Carroll | 14/14 | 25 |
| *Infinite Jest* — David Foster Wallace | 14/14 | 28 |
| *East of Eden* — John Steinbeck | 14/14 | 30 |
| *A Streetcar Named Desire* — Tennessee Williams | 14/14 | 33 |
| *The Importance of Being Earnest* — Oscar Wilde | 14/14 | 42 |
| *The Raven* — Edgar Allan Poe | 14/14 | 64 |
| *Twenty Love Poems and a Song of Despair* — Pablo Neruda | 14/14 | 66 |
| *Ariel* — Sylvia Plath | 14/14 | 108 |
| *I, Claudius (Claudius, #1)* — Robert Graves | 14/14 | 152 |
| *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne | 14/14 | 238 |
| *The Things They Carried* — Tim O'Brien | 14/14 | 242 |
| *A Midsummer Night's Dream* — William Shakespeare | 14/14 | 307 |
| *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien | 14/14 | 407 |
| *Inferno (The Divine Comedy #1)* — Dante Alighieri | 13/14 | 9 |
| *Shakespeare's Sonnets* — William Shakespeare | 13/14 | 13 |
| *Othello* — William Shakespeare | 13/14 | 47 |
| *Songs of Innocence and of Experience* — William Blake | 13/14 | 63 |
| *The Yellow Wall-Paper* — Charlotte Perkins Gilman | 13/14 | 77 |
| *Of Human Bondage* — W. Somerset Maugham | 13/14 | 104 |
| *Cyrano de Bergerac* — Edmond Rostand | 13/14 | 115 |
| *Romeo and Juliet* — William Shakespeare | 13/14 | 129 |
| *Much Ado About Nothing* — William Shakespeare | 13/14 | 156 |
| *The Importance of Being Earnest and Other Plays* — Oscar Wilde | 13/14 | 237 |
| *A Christmas Carol* — Charles Dickens | 13/14 | 416 |
| *A Little Princess* — Frances Hodgson Burnett | 13/14 | 750 |
| *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien | 13/14 | 3505 |
| *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien | 13/14 | 3699 |
| *Les Fleurs du Mal* — Charles Baudelaire | 12/14 | 8 |
| *The Death of Ivan Ilych* — Leo Tolstoy | 12/14 | 11 |
| *Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead* — Fyodor Dostoyevsky | 12/14 | 17 |
| *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust | 12/14 | 27 |
| *The Overcoat* — Nikolai Gogol | 12/14 | 40 |
| *If on a Winter's Night a Traveler* — Italo Calvino | 12/14 | 43 |
| *Richard III* — William Shakespeare | 12/14 | 50 |
| *The Name of the Rose* — Umberto Eco | 12/14 | 58 |
| *Chess Story* — Stefan Zweig | 12/14 | 72 |
| *Four Quartets* — T.S. Eliot | 12/14 | 75 |
| *Germinal (Les Rougon-Macquart, #13)* — Emile Zola | 12/14 | 99 |
| *The Wind-Up Bird Chronicle* — Haruki Murakami | 12/14 | 109 |
| *The Tell-Tale Heart* — Edgar Allan Poe | 12/14 | 119 |
| *Alice in Wonderland* — Jane Carruth | 12/14 | 141 |
| *Twelfth Night* — William Shakespeare | 12/14 | 169 |
| *The Essential Rumi* — Jalaluddin Mevlana Rumi | 12/14 | 204 |
| *We Have Always Lived in the Castle* — Shirley Jackson | 12/14 | 241 |
| *Johnny Got His Gun* — Dalton Trumbo | 12/14 | 323 |
| *Lonesome Dove* — Larry McMurtry | 12/14 | 325 |
| *From the Mixed-Up Files of Mrs. Basil E. Frankweiler* — E.L. Konigsburg | 12/14 | 437 |
| *Rosencrantz and Guildenstern Are Dead* — Tom Stoppard | 12/14 | 452 |
| *Bring Up the Bodies (Thomas Cromwell, #2)* — Hilary Mantel | 12/14 | 524 |
| *Roots: The Saga of an American Family* — Alex Haley | 12/14 | 604 |
| *On the Banks of Plum Creek  (Little House, #4)* — Laura Ingalls Wilder | 12/14 | 1287 |
| *Notes from Underground* — Fyodor Dostoyevsky | 11/14 | 24 |
| *Bartleby the Scrivener* — Herman Melville | 11/14 | 38 |
| *The Return of Sherlock Holmes* — Arthur Conan Doyle | 11/14 | 65 |
| *Blindness* — Jose Saramago | 11/14 | 136 |
| *The Memoirs of Sherlock Holmes* — Arthur Conan Doyle | 11/14 | 145 |
| *Who's Afraid of Virginia Woolf?* — Edward Albee | 11/14 | 162 |
| *Complete Poems, 1904-1962* — E.E. Cummings | 11/14 | 215 |
| *The Lottery* — Shirley Jackson | 11/14 | 286 |
| *100 Love Sonnets* — Pablo Neruda | 11/14 | 295 |
| *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante | 11/14 | 442 |
| *Cat on a Hot Tin Roof* — Tennessee Williams | 11/14 | 472 |
| *A Tree Grows in Brooklyn* — Betty  Smith | 11/14 | 559 |
| *Flowers for Algernon* — Daniel Keyes | 11/14 | 582 |
| *The Ultimate Hitchhiker's Guide to the Galaxy* — Douglas Adams | 11/14 | 647 |
| *I Capture the Castle* — Dodie Smith | 11/14 | 692 |
| *Anne of Avonlea (Anne of Green Gables, #2)* — L.M. Montgomery | 11/14 | 777 |
| *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie | 11/14 | 1452 |
| *A Monster Calls* — Patrick Ness | 11/14 | 3653 |
| *Wonder (Wonder #1)* — R.J. Palacio | 11/14 | 3891 |

## Origin heads

### latin_american_lens

1. *Tutunamayanlar* — Oguz Atay (89.5 +/-5.2, mass 11.9)
2. *The Grand Inquisitor* — Fyodor Dostoyevsky (88.2 +/-5.1, mass 17.8)
3. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (86.8 +/-4.4, mass 34.9)
4. *Time Regained (In Search of Lost Time, #7)* — Marcel Proust (86.7 +/-5.6, mass 16.4)
5. *Shakespeare's Sonnets* — William Shakespeare (86.0 +/-3.2, mass 86.0)
6. *East of Eden* — John Steinbeck (83.3 +/-2.5, mass 181.9)
7. *The Selected Poetry of Rainer Maria Rilke* — Rainer Maria Rilke (82.9 +/-5.3, mass 31.1)
8. *The Essential Rumi* — Jalaluddin Mevlana Rumi (82.8 +/-6.3, mass 18.4)
9. *Sodom and Gomorrah (In Search of Lost Time, #4)* — Marcel Proust (82.8 +/-6.6, mass 16.2)
10. *Les Fleurs du Mal* — Charles Baudelaire (82.4 +/-3.8, mass 74.8)
11. *Stoner* — John  Williams (81.7 +/-3.9, mass 74.6)
12. *The Marriage of Heaven and Hell* — William Blake (81.7 +/-6.2, mass 22.2)
13. *Notes from Underground* — Fyodor Dostoyevsky (81.5 +/-3.9, mass 72.5)
14. *Othello* — William Shakespeare (81.2 +/-2.4, mass 232.4)
15. *The Library of Babel* — Jorge Luis Borges (81.2 +/-6.8, mass 17.6)

### african_lens

1. *A Monster Calls* — Patrick Ness (84.4 +/-4.1, mass 53.9)
2. *Time Regained (In Search of Lost Time, #7)* — Marcel Proust (84.0 +/-7.2, mass 10.4)
3. *100 Love Sonnets* — Pablo Neruda (83.9 +/-5.8, mass 21.5)
4. *Shakespeare's Sonnets* — William Shakespeare (83.1 +/-3.9, mass 67.7)
5. *The Compleat Works of Wllm Shkspr* — Reduced Shakespeare Company (82.5 +/-7.5, mass 11.2)
6. *Angels in America, Part One: Millennium Approaches* — Tony Kushner (81.9 +/-5.9, mass 24.6)
7. *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante (81.8 +/-5.6, mass 28.8)
8. *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust (81.1 +/-3.8, mass 83.4)
9. *Stoner* — John  Williams (81.1 +/-3.9, mass 78.4)
10. *The Selected Poetry of Rainer Maria Rilke* — Rainer Maria Rilke (80.8 +/-6.0, mass 26.5)
11. *The Tartar Steppe* — Dino Buzzati (80.8 +/-7.3, mass 14.4)
12. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (80.4 +/-6.2, mass 24.6)
13. *Four Quartets* — T.S. Eliot (79.8 +/-5.5, mass 35.8)
14. *Wonder (Wonder #1)* — R.J. Palacio (79.2 +/-4.0, mass 79.4)
15. *The Dead* — James Joyce (79.2 +/-6.0, mass 29.2)

### romanian_lens

1. *Shahnameh: The Persian Book of Kings* — Abolqasem Ferdowsi (88.1 +/-4.8, mass 22.1)
2. *The Adventures of Sherlock Holmes* — Arthur Conan Doyle (86.3 +/-2.8, mass 115.8)
3. *Romeo and Juliet* — William Shakespeare (85.5 +/-1.2, mass 799.6)
4. *East of Eden* — John Steinbeck (84.0 +/-3.3, mass 93.5)
5. *قصه‌های من و بابام - کتاب دوم - شوخی‌ها و مهربانی‌ها* — Erich Ohser Plauen (83.9 +/-6.8, mass 13.0)
6. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (83.5 +/-2.8, mass 140.5)
7. *گلستان سعدی* — Saadi (82.4 +/-7.6, mass 10.5)
8. *Shakespeare's Sonnets* — William Shakespeare (82.0 +/-3.9, mass 70.4)
9. *رباعيات صلاح جاهين* — SlH jhyn (81.4 +/-7.2, mass 14.1)
10. *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust (81.4 +/-4.9, mass 44.0)
11. *The Nightingale and the Rose* — Oscar Wilde (81.2 +/-7.6, mass 12.2)
12. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (79.6 +/-3.2, mass 133.4)
13. *Purgatorio (The Divine Comedy, #2)* — Dante Alighieri (77.0 +/-7.8, mass 16.5)
14. *مثنوی معنوی* — Jalaluddin Mevlana Rumi (77.0 +/-8.5, mass 12.6)
15. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (76.8 +/-2.4, mass 267.8)

### modern_greek_lens

1. *Shahnameh: The Persian Book of Kings* — Abolqasem Ferdowsi (91.0 +/-3.4, mass 35.3)
2. *مثنوی معنوی* — Jalaluddin Mevlana Rumi (90.9 +/-3.5, mass 32.9)
3. *The Knight in the Panther's Skin* — Shota Rustaveli (90.6 +/-4.5, mass 15.9)
4. *The Grand Inquisitor* — Fyodor Dostoyevsky (87.5 +/-5.4, mass 16.4)
5. *Shakespeare's Sonnets* — William Shakespeare (87.4 +/-3.6, mass 56.3)
6. *Le Monogramme* — Odysseus Elytis (87.1 +/-5.0, mass 22.0)
7. *گلستان سعدی* — Saadi (86.7 +/-5.1, mass 22.9)
8. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (85.2 +/-5.7, mass 19.1)
9. *غزلیات سعدی* — Saadi (85.1 +/-5.9, mass 17.4)
10. *Time Regained (In Search of Lost Time, #7)* — Marcel Proust (85.0 +/-6.5, mass 12.6)
11. *The Adventures of Sherlock Holmes* — Arthur Conan Doyle (84.8 +/-3.1, mass 99.9)
12. *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust (84.6 +/-3.9, mass 59.6)
13. *رباعيات خيام* — Omar Khayyam (83.6 +/-4.2, mass 52.6)
14. *بوستان سعدی* — Saadi (83.1 +/-5.7, mass 24.6)
15. *The Selected Poetry of Rainer Maria Rilke* — Rainer Maria Rilke (83.0 +/-5.7, mass 24.8)

### dutch_lens

1. *الحرافيش* — Naguib Mahfouz (90.0 +/-3.4, mass 43.5)
2. *ثلاثية غرناطة* — Radwa Ashour (87.0 +/-3.5, mass 60.6)
3. *Three Comrades* — Erich Maria Remarque (86.6 +/-5.9, mass 14.0)
4. *A Monster Calls* — Patrick Ness (85.2 +/-4.0, mass 51.6)
5. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (85.2 +/-2.5, mass 166.6)
6. *گلستان سعدی* — Saadi (83.6 +/-7.1, mass 11.1)
7. *Infinite Jest* — David Foster Wallace (83.4 +/-5.9, mass 21.1)
8. *Bumi Manusia* — Pramoedya Ananta Toer (82.6 +/-5.1, mass 36.0)
9. *Wonder (Wonder #1)* — R.J. Palacio (82.2 +/-3.9, mass 70.0)
10. *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust (80.4 +/-5.4, mass 35.3)
11. *The Brothers Lionheart* — Astrid Lindgren (79.5 +/-6.7, mass 21.5)
12. *الطنطورية* — Radwa Ashour (79.5 +/-5.6, mass 35.0)
13. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (79.3 +/-3.1, mass 138.0)
14. *Stoner* — John  Williams (79.1 +/-5.3, mass 40.9)
15. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (79.1 +/-4.1, mass 78.3)

### china_list_lens

1. *A Monster Calls* — Patrick Ness (88.7 +/-2.5, mass 116.8)
2. *Homegoing* — Yaa Gyasi (88.2 +/-2.8, mass 94.7)
3. *Wonder (Wonder #1)* — R.J. Palacio (87.2 +/-2.2, mass 192.7)
4. *East of Eden* — John Steinbeck (85.4 +/-2.2, mass 211.2)
5. *The Compleat Works of Wllm Shkspr* — Reduced Shakespeare Company (85.3 +/-6.7, mass 11.1)
6. *A Tree Grows in Brooklyn* — Betty  Smith (84.3 +/-2.1, mass 256.2)
7. *100 Love Sonnets* — Pablo Neruda (83.3 +/-6.7, mass 14.3)
8. *A Man Called Ove* — Fredrik Backman (83.0 +/-2.6, mass 176.7)
9. *A Gentleman in Moscow* — Amor Towles (82.4 +/-3.9, mass 71.3)
10. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (81.7 +/-2.7, mass 174.7)
11. *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante (81.4 +/-5.5, mass 31.0)
12. *Twenty Love Poems and a Song of Despair* — Pablo Neruda (80.6 +/-6.1, mass 25.5)
13. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (80.5 +/-4.0, mass 74.4)
14. *The Martian* — Andy Weir (80.3 +/-2.6, mass 203.1)
15. *Cutting for Stone* — Abraham Verghese (79.7 +/-3.0, mass 154.0)

### greatestbooks_head

1. *Romeo and Juliet* — William Shakespeare (88.0 +/-1.2, mass 673.8)
2. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (87.7 +/-2.2, mass 174.4)
3. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (87.2 +/-1.8, mass 303.5)
4. *East of Eden* — John Steinbeck (86.0 +/-2.3, mass 191.0)
5. *Shakespeare's Sonnets* — William Shakespeare (85.6 +/-3.6, mass 65.1)
6. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (83.6 +/-2.7, mass 152.6)
7. *100 Love Sonnets* — Pablo Neruda (83.4 +/-7.0, mass 12.3)
8. *The Raven* — Edgar Allan Poe (83.2 +/-4.6, mass 43.8)
9. *The Importance of Being Earnest* — Oscar Wilde (82.4 +/-2.6, mass 184.9)
10. *A Monster Calls* — Patrick Ness (82.1 +/-5.2, mass 34.0)
11. *Othello* — William Shakespeare (81.7 +/-2.5, mass 206.7)
12. *Les Fleurs du Mal* — Charles Baudelaire (81.0 +/-5.5, mass 32.9)
13. *The Adventures of Sherlock Holmes* — Arthur Conan Doyle (80.8 +/-3.6, mass 91.6)
14. *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne (80.7 +/-4.7, mass 49.3)
15. *Inferno (The Divine Comedy #1)* — Dante Alighieri (80.1 +/-3.6, mass 97.9)

### border_childrens_literary

1. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (91.8 +/-1.4, mass 320.1)
2. *A Monster Calls* — Patrick Ness (90.7 +/-2.2, mass 125.6)
3. *Wonder (Wonder #1)* — R.J. Palacio (89.4 +/-2.3, mass 139.1)
4. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (88.4 +/-1.7, mass 302.4)
5. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (87.7 +/-2.1, mass 201.0)
6. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (87.6 +/-1.4, mass 451.3)
7. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (87.0 +/-2.5, mass 139.8)
8. *A Man Called Ove* — Fredrik Backman (86.0 +/-2.9, mass 108.8)
9. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (85.0 +/-1.9, mass 317.7)
10. *Gone with the Wind* — Margaret Mitchell (84.1 +/-1.8, mass 339.5)
11. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (83.7 +/-3.7, mass 75.2)
12. *A Little Princess* — Frances Hodgson Burnett (83.4 +/-2.7, mass 158.3)
13. *The Compleat Works of Wllm Shkspr* — Reduced Shakespeare Company (82.9 +/-7.5, mass 10.3)
14. *The Lion, the Witch, and the Wardrobe (Chronicles of Narnia, #1)* — C.S. Lewis (82.6 +/-1.8, mass 374.9)
15. *The Importance of Being Earnest* — Oscar Wilde (82.4 +/-2.8, mass 157.6)

### eastern_central

1. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (88.0 +/-4.0, mass 38.6)
2. *Shakespeare's Sonnets* — William Shakespeare (86.8 +/-2.8, mass 109.2)
3. *The Grand Inquisitor* — Fyodor Dostoyevsky (86.4 +/-5.9, mass 14.0)
4. *Notes from Underground* — Fyodor Dostoyevsky (85.3 +/-3.8, mass 57.7)
5. *Les Fleurs du Mal* — Charles Baudelaire (84.9 +/-3.4, mass 78.0)
6. *Sodom and Gomorrah (In Search of Lost Time, #4)* — Marcel Proust (84.8 +/-5.9, mass 18.2)
7. *A Season in Hell/The Drunken Boat* — Arthur Rimbaud (83.3 +/-5.9, mass 21.8)
8. *Romeo and Juliet* — William Shakespeare (82.8 +/-1.4, mass 634.9)
9. *The Overcoat* — Nikolai Gogol (81.9 +/-4.8, mass 43.2)
10. *The Library of Babel* — Jorge Luis Borges (81.7 +/-7.4, mass 12.8)
11. *The Book of Sand and Shakespeare's Memory* — Jorge Luis Borges (81.7 +/-7.4, mass 13.0)
12. *The Essential Rumi* — Jalaluddin Mevlana Rumi (81.5 +/-6.3, mass 21.9)
13. *Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead* — Fyodor Dostoyevsky (80.7 +/-3.1, mass 133.8)
14. *The Selected Poetry of Rainer Maria Rilke* — Rainer Maria Rilke (80.5 +/-5.8, mass 29.5)
15. *Four Quartets* — T.S. Eliot (80.2 +/-4.7, mass 51.5)

### francophone_lens

1. *Shakespeare's Sonnets* — William Shakespeare (91.6 +/-2.3, mass 91.5)
2. *The Grand Inquisitor* — Fyodor Dostoyevsky (86.4 +/-6.2, mass 12.0)
3. *The Essential Rumi* — Jalaluddin Mevlana Rumi (85.3 +/-5.6, mass 20.7)
4. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (85.1 +/-4.9, mass 31.6)
5. *Les Fleurs du Mal* — Charles Baudelaire (84.6 +/-3.9, mass 61.2)
6. *Romeo and Juliet* — William Shakespeare (83.3 +/-1.5, mass 550.2)
7. *100 Love Sonnets* — Pablo Neruda (83.2 +/-6.6, mass 15.3)
8. *Othello* — William Shakespeare (82.0 +/-2.2, mass 259.9)
9. *The Raven* — Edgar Allan Poe (81.5 +/-4.4, mass 57.4)
10. *The Selected Poetry of Rainer Maria Rilke* — Rainer Maria Rilke (81.0 +/-6.3, mass 22.9)
11. *East of Eden* — John Steinbeck (80.8 +/-2.6, mass 188.2)
12. *The Dead* — James Joyce (80.7 +/-5.6, mass 31.6)
13. *Sodom and Gomorrah (In Search of Lost Time, #4)* — Marcel Proust (80.3 +/-7.7, mass 12.8)
14. *The Compleat Works of Wllm Shkspr* — Reduced Shakespeare Company (80.1 +/-7.9, mass 12.0)
15. *The Tartar Steppe* — Dino Buzzati (79.4 +/-7.6, mass 14.8)

### anglophone_lens

1. *A Monster Calls* — Patrick Ness (88.0 +/-3.2, mass 70.5)
2. *East of Eden* — John Steinbeck (86.3 +/-2.1, mass 228.5)
3. *The Raven* — Edgar Allan Poe (86.2 +/-4.1, mass 44.7)
4. *Wonder (Wonder #1)* — R.J. Palacio (84.1 +/-2.9, mass 120.9)
5. *100 Love Sonnets* — Pablo Neruda (83.6 +/-6.5, mass 15.8)
6. *Homegoing* — Yaa Gyasi (83.3 +/-4.2, mass 55.4)
7. *Shakespeare's Sonnets* — William Shakespeare (83.0 +/-4.3, mass 52.6)
8. *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante (82.4 +/-5.3, mass 31.5)
9. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (82.0 +/-2.8, mass 154.8)
10. *The Essential Rumi* — Jalaluddin Mevlana Rumi (81.5 +/-6.8, mass 16.8)
11. *A Tree Grows in Brooklyn* — Betty  Smith (81.2 +/-2.6, mass 191.8)
12. *The Importance of Being Earnest* — Oscar Wilde (80.9 +/-2.8, mass 169.3)
13. *Angels in America* — Tony Kushner (80.6 +/-7.6, mass 13.3)
14. *Twenty Love Poems and a Song of Despair* — Pablo Neruda (80.6 +/-6.0, mass 26.6)
15. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (80.5 +/-3.3, mass 113.1)

### contemporary_1980_2017

1. *Homegoing* — Yaa Gyasi (89.8 +/-1.9, mass 186.9)
2. *Wonder (Wonder #1)* — R.J. Palacio (89.4 +/-1.6, mass 287.9)
3. *A Monster Calls* — Patrick Ness (88.0 +/-2.4, mass 144.2)
4. *East of Eden* — John Steinbeck (87.2 +/-2.1, mass 197.3)
5. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (85.9 +/-2.1, mass 224.8)
6. *A Tree Grows in Brooklyn* — Betty  Smith (84.4 +/-2.1, mass 254.3)
7. *Roots: The Saga of an American Family* — Alex Haley (82.7 +/-3.9, mass 67.9)
8. *Cutting for Stone* — Abraham Verghese (82.6 +/-2.2, mass 251.7)
9. *A Man Called Ove* — Fredrik Backman (82.1 +/-2.2, mass 270.6)
10. *Lonesome Dove* — Larry McMurtry (82.0 +/-3.9, mass 74.4)
11. *A Little Life* — Hanya Yanagihara (81.5 +/-2.5, mass 202.2)
12. *100 Love Sonnets* — Pablo Neruda (81.3 +/-7.6, mass 12.1)
13. *The Story of the Lost Child (The Neapolitan Novels, #4)* — Elena Ferrante (81.2 +/-5.1, mass 38.7)
14. *Angels in America* — Tony Kushner (80.8 +/-8.1, mass 10.5)
15. *The Nightingale* — Kristin Hannah (80.6 +/-2.3, mass 268.9)

### postwar_1946_1979

1. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (89.4 +/-1.7, mass 262.4)
2. *A Monster Calls* — Patrick Ness (88.5 +/-3.4, mass 54.9)
3. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (87.0 +/-1.6, mass 387.3)
4. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (86.2 +/-2.0, mass 237.9)
5. *Shakespeare's Sonnets* — William Shakespeare (85.8 +/-3.6, mass 64.9)
6. *The Importance of Being Earnest* — Oscar Wilde (85.2 +/-2.3, mass 201.0)
7. *The Raven* — Edgar Allan Poe (84.7 +/-4.2, mass 50.0)
8. *East of Eden* — John Steinbeck (83.4 +/-2.3, mass 217.2)
9. *Romeo and Juliet* — William Shakespeare (82.2 +/-1.5, mass 571.8)
10. *A Gentleman in Moscow* — Amor Towles (82.0 +/-6.1, mass 22.8)
11. *Wonder (Wonder #1)* — R.J. Palacio (81.0 +/-3.9, mass 75.8)
12. *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne (80.2 +/-4.3, mass 65.0)
13. *Gone with the Wind* — Margaret Mitchell (79.6 +/-2.0, mass 352.3)
14. *The Compleat Works of Wllm Shkspr* — Reduced Shakespeare Company (79.5 +/-8.1, mass 12.0)
15. *A Christmas Carol* — Charles Dickens (79.2 +/-2.3, mass 286.7)

### modernist_1900_1945

1. *Shakespeare's Sonnets* — William Shakespeare (90.3 +/-2.6, mass 84.2)
2. *Romeo and Juliet* — William Shakespeare (87.2 +/-1.2, mass 695.5)
3. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (85.2 +/-2.5, mass 155.3)
4. *Othello* — William Shakespeare (83.5 +/-2.1, mass 268.1)
5. *The Essential Rumi* — Jalaluddin Mevlana Rumi (83.1 +/-6.4, mass 17.9)
6. *East of Eden* — John Steinbeck (82.6 +/-2.3, mass 222.5)
7. *The Importance of Being Earnest* — Oscar Wilde (81.6 +/-2.4, mass 216.3)
8. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (80.9 +/-2.2, mass 272.7)
9. *Les Fleurs du Mal* — Charles Baudelaire (80.5 +/-5.0, mass 43.7)
10. *Inferno (The Divine Comedy #1)* — Dante Alighieri (80.2 +/-3.2, mass 126.0)
11. *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne (79.9 +/-5.0, mass 45.6)
12. *100 Love Sonnets* — Pablo Neruda (79.6 +/-8.0, mass 12.3)
13. *The Overcoat* — Nikolai Gogol (79.1 +/-7.0, mass 19.3)
14. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (78.6 +/-7.2, mass 18.6)
15. *A Gentleman in Moscow* — Amor Towles (78.2 +/-7.6, mass 16.4)

### historical_pre1900

1. *Romeo and Juliet* — William Shakespeare (90.2 +/-1.0, mass 795.8)
2. *Shakespeare's Sonnets* — William Shakespeare (88.9 +/-2.8, mass 88.2)
3. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (87.5 +/-2.2, mass 186.5)
4. *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien (84.0 +/-1.9, mass 314.3)
5. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (82.8 +/-2.6, mass 170.6)
6. *Othello* — William Shakespeare (82.0 +/-2.2, mass 262.8)
7. *Inferno (The Divine Comedy #1)* — Dante Alighieri (81.1 +/-3.3, mass 109.2)
8. *Les Fleurs du Mal* — Charles Baudelaire (81.1 +/-5.4, mass 34.5)
9. *The Adventures of Sherlock Holmes* — Arthur Conan Doyle (80.6 +/-3.5, mass 103.4)
10. *The Importance of Being Earnest* — Oscar Wilde (79.7 +/-2.7, mass 195.9)
11. *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust (79.6 +/-7.2, mass 16.9)
12. *A Midsummer Night's Dream* — William Shakespeare (79.0 +/-2.3, mass 272.0)
13. *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne (78.8 +/-5.1, mass 46.1)
14. *East of Eden* — John Steinbeck (78.8 +/-3.0, mass 160.0)
15. *A Christmas Carol* — Charles Dickens (78.3 +/-2.3, mass 283.0)

### control_popular_romance

1. *The Nightingale* — Kristin Hannah (91.6 +/-1.3, mass 351.8)
2. *Wonder (Wonder #1)* — R.J. Palacio (91.0 +/-1.4, mass 359.7)
3. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (90.7 +/-1.8, mass 211.4)
4. *A Man Called Ove* — Fredrik Backman (89.8 +/-1.6, mass 272.1)
5. *A Monster Calls* — Patrick Ness (89.6 +/-1.8, mass 240.6)
6. *The Martian* — Andy Weir (88.6 +/-1.4, mass 412.9)
7. *Ready Player One* — Ernest Cline (88.3 +/-1.6, mass 345.2)
8. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (88.2 +/-1.6, mass 366.2)
9. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (87.9 +/-2.3, mass 148.2)
10. *Still Alice* — Lisa Genova (86.2 +/-2.2, mass 196.2)
11. *Homegoing* — Yaa Gyasi (85.4 +/-3.0, mass 103.3)
12. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (84.8 +/-3.4, mass 80.3)
13. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (84.6 +/-3.4, mass 80.3)
14. *A Little Life* — Hanya Yanagihara (84.4 +/-3.3, mass 92.5)
15. *Gone with the Wind* — Margaret Mitchell (84.2 +/-2.0, mass 290.3)

### control_commercial_series

1. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (92.2 +/-1.5, mass 234.9)
2. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (90.2 +/-2.2, mass 134.0)
3. *The Martian* — Andy Weir (89.6 +/-2.1, mass 152.6)
4. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (88.5 +/-2.0, mass 210.9)
5. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (87.8 +/-2.9, mass 88.6)
6. *The Nightingale* — Kristin Hannah (87.6 +/-2.9, mass 95.4)
7. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (86.9 +/-1.6, mass 366.2)
8. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (86.6 +/-2.0, mass 231.5)
9. *Wonder (Wonder #1)* — R.J. Palacio (86.4 +/-2.7, mass 119.5)
10. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (86.0 +/-2.1, mass 220.2)
11. *Ready Player One* — Ernest Cline (85.8 +/-2.4, mass 163.7)
12. *Gone with the Wind* — Margaret Mitchell (83.8 +/-2.4, mass 191.2)
13. *Night Watch (Discworld, #29; City Watch, #6)* — Terry Pratchett (83.7 +/-6.3, mass 16.8)
14. *A Man Called Ove* — Fredrik Backman (83.5 +/-4.0, mass 62.5)
15. *The Girl Who Played with Fire (Millennium, #2)* — Stieg Larsson (82.9 +/-2.4, mass 215.2)

### control_popular_fantasy

1. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (92.0 +/-1.6, mass 228.1)
2. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (91.5 +/-1.6, mass 234.5)
3. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (91.5 +/-2.0, mass 131.0)
4. *The Nightingale* — Kristin Hannah (90.7 +/-2.9, mass 61.4)
5. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (88.0 +/-2.1, mass 196.1)
6. *Wonder (Wonder #1)* — R.J. Palacio (87.2 +/-2.5, mass 130.4)
7. *A Monster Calls* — Patrick Ness (86.2 +/-2.5, mass 154.2)
8. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (85.7 +/-2.0, mass 261.6)
9. *The Martian* — Andy Weir (85.0 +/-2.5, mass 158.5)
10. *A Man Called Ove* — Fredrik Backman (84.8 +/-4.5, mass 39.2)
11. *Ready Player One* — Ernest Cline (84.4 +/-2.3, mass 210.7)
12. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (84.1 +/-2.5, mass 183.6)
13. *The Green Mile* — Stephen King (83.8 +/-4.2, mass 51.5)
14. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (83.0 +/-1.7, mass 415.5)
15. *Dead to the World (Sookie Stackhouse, #4)* — Charlaine Harris (82.0 +/-1.9, mass 356.3)

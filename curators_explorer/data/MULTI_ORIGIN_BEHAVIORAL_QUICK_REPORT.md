# Multi-origin behavioral seed audit (quick)

## Design

Each disjoint origin selects up to 2,000 direct-affinity teachers. A five-fold out-of-fold model reconstructs them from the current 51 generic behavior features, then selects a 3,000-reader jury. No book identity or list membership is a predictor. The union of all origin works is excluded from every ranked universe.

This stage uses the same balanced 5-star-versus-low ranker for every reconstructed jury. It isolates seed-origin dependence before the much more expensive community refit.

## Reconstruction

| Origin | Role | Works | min hits | teachers | AUC | AP | teacher/jury J | fit seconds | rankable books |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| greatestbooks_head | literary | 40 | 3 | 2,000 | 0.974 | 0.148 | 0.138 | 5.6 | 300 |
| eastern_central | literary | 40 | 3 | 2,000 | 0.958 | 0.079 | 0.082 | 5.6 | 300 |
| contemporary_1980_2017 | literary | 40 | 3 | 2,000 | 0.942 | 0.065 | 0.068 | 6.5 | 300 |
| historical_pre1900 | literary | 40 | 3 | 2,000 | 0.965 | 0.101 | 0.100 | 6.0 | 300 |
| control_commercial_series | control | 40 | 3 | 2,000 | 0.991 | 0.304 | 0.234 | 5.7 | 300 |

## Convergence

- Literary↔literary mean reconstructed-jury Jaccard: **0.215**; book Jaccard@50/200 **0.247/0.357**.
- Literary↔control mean reconstructed-jury Jaccard: **0.017**; book Jaccard@50/200 **0.098/0.169**.
- Literary↔children's-border mean reconstructed-jury Jaccard: **nan**; book Jaccard@50/200 **nan/nan**.
- Held-out books present in at least 3/4 literary top 200s: **138**.

## Shared held-out head

| Book | literary top-200s | current consensus rank |
|---|---:|---:|
| *The Adventures of Sherlock Holmes* — Arthur Conan Doyle | 4/4 | 15 |
| *Stoner* — John  Williams | 4/4 | 23 |
| *Alice's Adventures in Wonderland & Through the Looking-Glass* — Lewis Carroll | 4/4 | 25 |
| *Infinite Jest* — David Foster Wallace | 4/4 | 28 |
| *East of Eden* — John Steinbeck | 4/4 | 30 |
| *A Streetcar Named Desire* — Tennessee Williams | 4/4 | 33 |
| *The Importance of Being Earnest* — Oscar Wilde | 4/4 | 42 |
| *If on a Winter's Night a Traveler* — Italo Calvino | 4/4 | 43 |
| *The Raven* — Edgar Allan Poe | 4/4 | 64 |
| *Twenty Love Poems and a Song of Despair* — Pablo Neruda | 4/4 | 66 |
| *The Yellow Wall-Paper* — Charlotte Perkins Gilman | 4/4 | 77 |
| *Of Human Bondage* — W. Somerset Maugham | 4/4 | 104 |
| *Ariel* — Sylvia Plath | 4/4 | 108 |
| *Cyrano de Bergerac* — Edmond Rostand | 4/4 | 115 |
| *Alice in Wonderland* — Jane Carruth | 4/4 | 141 |
| *I, Claudius (Claudius, #1)* — Robert Graves | 4/4 | 152 |
| *Much Ado About Nothing* — William Shakespeare | 4/4 | 156 |
| *The Essential Rumi* — Jalaluddin Mevlana Rumi | 4/4 | 204 |
| *The Importance of Being Earnest and Other Plays* — Oscar Wilde | 4/4 | 237 |
| *The House at Pooh Corner (Winnie-the-Pooh, #2)* — A.A. Milne | 4/4 | 238 |
| *We Have Always Lived in the Castle* — Shirley Jackson | 4/4 | 241 |
| *The Things They Carried* — Tim O'Brien | 4/4 | 242 |
| *The Lottery* — Shirley Jackson | 4/4 | 286 |
| *100 Love Sonnets* — Pablo Neruda | 4/4 | 295 |
| *A Midsummer Night's Dream* — William Shakespeare | 4/4 | 307 |
| *Johnny Got His Gun* — Dalton Trumbo | 4/4 | 323 |
| *Lonesome Dove* — Larry McMurtry | 4/4 | 325 |
| *Through the Looking-Glass, and What Alice Found There* — Lewis Carroll | 4/4 | 332 |
| *100 Selected Poems* — E.E. Cummings | 4/4 | 357 |
| *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien | 4/4 | 407 |
| *A Christmas Carol* — Charles Dickens | 4/4 | 416 |
| *From the Mixed-Up Files of Mrs. Basil E. Frankweiler* — E.L. Konigsburg | 4/4 | 437 |
| *The Story of a New Name (The Neapolitan Novels #2)* — Elena Ferrante | 4/4 | 442 |
| *Bring Up the Bodies (Thomas Cromwell, #2)* — Hilary Mantel | 4/4 | 524 |
| *Roots: The Saga of an American Family* — Alex Haley | 4/4 | 604 |
| *A Little Princess* — Frances Hodgson Burnett | 4/4 | 750 |
| *Anne of Avonlea (Anne of Green Gables, #2)* — L.M. Montgomery | 4/4 | 777 |
| *On the Banks of Plum Creek  (Little House, #4)* — Laura Ingalls Wilder | 4/4 | 1287 |
| *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien | 4/4 | 3505 |
| *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien | 4/4 | 3699 |
| *Les Fleurs du Mal* — Charles Baudelaire | 3/4 | 8 |
| *Inferno (The Divine Comedy #1)* — Dante Alighieri | 3/4 | 9 |
| *The Death of Ivan Ilych* — Leo Tolstoy | 3/4 | 11 |
| *Shakespeare's Sonnets* — William Shakespeare | 3/4 | 13 |
| *Faust: First Part* — Johann Wolfgang von Goethe | 3/4 | 16 |
| *Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead* — Fyodor Dostoyevsky | 3/4 | 17 |
| *Notes from Underground* — Fyodor Dostoyevsky | 3/4 | 24 |
| *Swann's Way (In Search of Lost Time, #1)* — Marcel Proust | 3/4 | 27 |
| *Bartleby the Scrivener* — Herman Melville | 3/4 | 38 |
| *The Overcoat* — Nikolai Gogol | 3/4 | 40 |
| *Eugene Onegin* — Alexander Pushkin | 3/4 | 46 |
| *Othello* — William Shakespeare | 3/4 | 47 |
| *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* — Marcel Proust | 3/4 | 49 |
| *Richard III* — William Shakespeare | 3/4 | 50 |
| *The Name of the Rose* — Umberto Eco | 3/4 | 58 |
| *Songs of Innocence and of Experience* — William Blake | 3/4 | 63 |
| *The Return of Sherlock Holmes* — Arthur Conan Doyle | 3/4 | 65 |
| *Chess Story* — Stefan Zweig | 3/4 | 72 |
| *Four Quartets* — T.S. Eliot | 3/4 | 75 |
| *رباعيات خيام* — Omar Khayyam | 3/4 | 81 |
| *Julius Caesar* — William Shakespeare | 3/4 | 82 |
| *The Selected Poetry of Rainer Maria Rilke* — Rainer Maria Rilke | 3/4 | 89 |
| *The Hunchback of Notre-Dame* — Victor Hugo | 3/4 | 95 |
| *Purgatorio (The Divine Comedy, #2)* — Dante Alighieri | 3/4 | 98 |
| *Germinal (Les Rougon-Macquart, #13)* — Emile Zola | 3/4 | 99 |
| *The Marriage of Heaven and Hell* — William Blake | 3/4 | 102 |
| *The Rime of the Ancient Mariner* — Samuel Taylor Coleridge | 3/4 | 106 |
| *The Wind-Up Bird Chronicle* — Haruki Murakami | 3/4 | 109 |
| *The Dead* — James Joyce | 3/4 | 110 |
| *The Tell-Tale Heart* — Edgar Allan Poe | 3/4 | 119 |
| *The Merchant of Venice* — William Shakespeare | 3/4 | 125 |
| *Romeo and Juliet* — William Shakespeare | 3/4 | 129 |
| *Narcissus and Goldmund* — Hermann Hesse | 3/4 | 130 |
| *Medea* — Euripides | 3/4 | 132 |
| *Antigone (The Theban Plays, #3)* — Sophocles | 3/4 | 133 |

## Origin heads

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

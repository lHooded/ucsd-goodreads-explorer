# Expanded-prior joint reader-by-jury bootstrap

## Result

Each draw takes one saved teacher-composition jury refit and independently Poisson-resamples whole Goodreads users within it. Global, book, community, and predictive-heterogeneity terms are then relearned on the expanded mass-2 prior population; the publication threshold remains pair mass 10.

- Replicates: **20** across **100** saved jury refits; expanded works: **4,920**.
- Mean Jaccard@50/200: **0.693 / 0.729** (10th percentiles 0.639 / 0.701).
- Median point-top-200 joint `u80`: **3.65** points; median eligibility: **100%**; median top-200 inclusion: **90%**.
- Recomputed soft point matches the stored expanded ranking at J@50/200 **1.000/1.000** with maximum top-200 score error **0.0000**.

## Expanded-prior point head

| # | book | score | analytic u | joint u80 | eligibility | top200 | joint rank q10-q90 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 83.5 | 3.5 | 2.5 | 100% | 100% | 1-2 |
| 2 | Hamlet — William Shakespeare | 83.0 | 3.2 | 3.2 | 100% | 100% | 1-2 |
| 3 | Les Misérables — Victor Hugo | 75.6 | 4.5 | 2.6 | 100% | 100% | 3-7 |
| 4 | Crime and Punishment — Fyodor Dostoyevsky | 75.3 | 7.0 | 3.2 | 100% | 100% | 3-6 |
| 5 | Macbeth — William Shakespeare | 75.2 | 4.1 | 5.1 | 100% | 100% | 2-12 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 74.0 | 4.2 | 4.6 | 100% | 100% | 3-15 |
| 7 | Demons — Fyodor Dostoyevsky | 73.7 | 5.1 | 2.8 | 100% | 100% | 4-12 |
| 8 | The Idiot — Fyodor Dostoyevsky | 71.2 | 6.7 | 3.3 | 100% | 100% | 6-16 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 71.1 | 5.8 | 3.8 | 100% | 100% | 9-25 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 70.2 | 6.1 | 4.3 | 100% | 100% | 9-28 |
| 11 | Paradise Lost — John Milton | 69.9 | 5.9 | 5.7 | 100% | 100% | 7-35 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 69.4 | 5.7 | 5.7 | 100% | 100% | 5-34 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 69.3 | 5.5 | 3.1 | 100% | 100% | 8-18 |
| 14 | The Divine Comedy — Dante Alighieri | 69.0 | 5.4 | 4.0 | 100% | 100% | 7-23 |
| 15 | War and Peace — Leo Tolstoy | 68.7 | 6.0 | 4.9 | 100% | 100% | 7-22 |
| 16 | Anna Karenina — Leo Tolstoy | 68.5 | 4.1 | 3.2 | 100% | 100% | 8-21 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 67.9 | 4.9 | 4.0 | 100% | 100% | 12-28 |
| 18 | King Lear — William Shakespeare | 67.3 | 5.2 | 4.2 | 100% | 100% | 10-34 |
| 19 | The Magic Mountain — Thomas Mann | 67.2 | 5.6 | 3.6 | 100% | 100% | 12-38 |
| 20 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 66.8 | 5.9 | 3.9 | 100% | 100% | 10-35 |
| 21 | Faust: First Part — Johann Wolfgang von Goethe | 66.5 | 5.9 | 3.0 | 100% | 100% | 14-37 |
| 22 | Leaves of Grass — Walt Whitman | 66.1 | 5.8 | 4.6 | 100% | 100% | 12-45 |
| 23 | Stoner — John  Williams | 65.7 | 6.7 | 3.0 | 100% | 100% | 15-37 |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 65.5 | 6.2 | 2.9 | 100% | 100% | 17-41 |
| 25 | Infinite Jest — David Foster Wallace | 65.0 | 6.2 | 3.4 | 100% | 95% | 19-48 |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 65.0 | 5.9 | 4.5 | 100% | 100% | 18-70 |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 64.8 | 6.2 | 4.6 | 100% | 100% | 22-72 |
| 28 | The Iliad — Homer | 64.1 | 7.3 | 3.4 | 100% | 100% | 17-45 |
| 29 | The Waves — Virginia Woolf | 64.0 | 6.3 | 4.6 | 100% | 100% | 15-65 |
| 30 | The Count of Monte Cristo — Alexandre Dumas | 63.5 | 4.6 | 4.1 | 100% | 100% | 13-52 |
| 31 | The Waste Land — T.S. Eliot | 63.4 | 6.4 | 4.6 | 100% | 100% | 27-95 |
| 32 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 63.3 | 5.2 | 3.8 | 100% | 100% | 22-63 |
| 33 | 2666 — Roberto Bolano | 63.1 | 6.8 | 3.6 | 100% | 100% | 25-60 |
| 34 | A Streetcar Named Desire — Tennessee Williams | 63.1 | 5.9 | 3.1 | 100% | 100% | 21-53 |
| 35 | The Book of Disquiet — Fernando Pessoa | 63.0 | 6.9 | 2.7 | 100% | 100% | 28-59 |
| 36 | East of Eden — John Steinbeck | 62.9 | 6.4 | 3.7 | 100% | 100% | 24-66 |
| 37 | Bartleby the Scrivener — Herman Melville | 62.6 | 6.5 | 3.5 | 100% | 100% | 26-65 |
| 38 | The Overcoat — Nikolai Gogol | 62.2 | 6.7 | 4.3 | 100% | 100% | 28-85 |
| 39 | Dead Souls — Nikolai Gogol | 61.8 | 5.9 | 3.0 | 100% | 100% | 32-60 |
| 40 | One Hundred Years of Solitude — Gabriel Garcia Marquez | 61.7 | 5.8 | 3.1 | 100% | 100% | 25-63 |
| 41 | Hunger — Knut Hamsun | 61.6 | 6.2 | 3.4 | 100% | 100% | 28-60 |
| 42 | The Sound and the Fury — William Faulkner | 61.0 | 6.7 | 4.7 | 100% | 100% | 26-89 |
| 43 | The Arabian Nights — Anonymous | 60.9 | 7.2 | 2.3 | 100% | 100% | 29-62 |
| 44 | Richard III — William Shakespeare | 60.8 | 6.6 | 3.6 | 100% | 100% | 32-85 |
| 45 | In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust | 60.7 | 7.3 | 5.4 | 100% | 100% | 21-103 |
| 46 | If on a Winter's Night a Traveler — Italo Calvino | 60.6 | 6.2 | 2.8 | 100% | 100% | 44-74 |
| 47 | Othello — William Shakespeare | 60.5 | 6.3 | 4.8 | 100% | 100% | 24-78 |
| 48 | Eugene Onegin — Alexander Pushkin | 60.5 | 6.4 | 5.3 | 100% | 100% | 28-113 |
| 49 | The Importance of Being Earnest — Oscar Wilde | 60.3 | 6.4 | 3.3 | 100% | 100% | 32-80 |
| 50 | Blood Meridian, or the Evening Redness in the West — Cormac McCarthy | 60.2 | 6.2 | 3.9 | 100% | 100% | 38-93 |

`joint u80` is half the conditional 10th-90th percentile score interval. Use max(analytic u, joint u80) as the provisional display envelope: the analytic and bootstrap widths overlap, so quadrature would double count. Feature-family, Gamma, fixed-mass, and temporal trajectories remain separate systematic paths.

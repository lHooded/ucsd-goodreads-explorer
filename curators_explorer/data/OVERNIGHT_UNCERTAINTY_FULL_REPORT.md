# Exact-pair user-block uncertainty campaign

## Design

The random 12×12 pair sample is integrated out analytically. Each user-book event receives its exact probability of inclusion in a balanced sample, retaining equal expected high/low mass per reader and a maximum contribution of one.

Whole readers are then resampled with Poisson(1) weights through all nine community partitions. Score intervals are conditional on bootstrap eligibility; eligibility and top-k probabilities are reported separately.

- Mode: **full**; completed bootstrap replicates: **5,000**.
- Exact-pair events: **862,392**; expected mass per side: **48801.0**.
- Near-evidence/bootstrap candidates: **1,146**; exact rankable books: **297**.

## Exact estimator versus sampled seeds

| comparison | J@50 | J@200 | RBO |
|---|---:|---:|---:|
| prior central seed11 | 0.587 | 0.653 | 0.662 |
| sample seed 11 | 0.587 | 0.653 | 0.666 |
| sample seed 23 | 0.515 | 0.633 | 0.552 |
| sample seed 47 | 0.613 | 0.613 | 0.739 |
| sample seed 89 | 0.562 | 0.626 | 0.691 |
| sample seed 131 | 0.493 | 0.646 | 0.641 |

## Uncertainty calibration

Among exact top-200 books with defined intervals, median bootstrap-u80 / analytic-u = **0.762**. This is diagnostic, not a coverage claim; conditional tail probabilities must still be read alongside bootstrap eligibility.

## Exact top books with bootstrap diagnostics

| book | exact | analytic u | boot q10–q90 | boot u80 | eligible | top200 |
|---|---:|---:|---:|---:|---:|---:|
| Hamlet — William Shakespeare | 1 (79.7) | 4.9 | 75.2–82.0 | 3.4 | 100% | 100% |
| The Brothers Karamazov — Fyodor Dostoyevsky | 2 (76.8) | 4.4 | 70.3–79.7 | 4.7 | 100% | 100% |
| Les Fleurs du Mal — Charles Baudelaire | 3 (76.0) | 5.2 | 67.5–77.7 | 5.1 | 100% | 100% |
| Demons — Fyodor Dostoyevsky | 4 (75.9) | 5.7 | 70.5–77.3 | 3.4 | 81% | 81% |
| Macbeth — William Shakespeare | 5 (73.5) | 4.7 | 66.5–75.7 | 4.6 | 100% | 100% |
| Notes from Underground — Fyodor Dostoyevsky | 6 (73.2) | 6.1 | 67.7–75.0 | 3.6 | 67% | 67% |
| Shakespeare's Sonnets — William Shakespeare | 7 (73.2) | 5.2 | 63.8–74.9 | 5.6 | 100% | 100% |
| Les Misérables — Victor Hugo | 8 (72.0) | 5.2 | 65.7–74.8 | 4.5 | 100% | 100% |
| The Master and Margarita — Mikhail Bulgakov | 9 (71.7) | 4.0 | 62.4–73.9 | 5.8 | 100% | 100% |
| Journey to the End of the Night — Louis-Ferdinand Celine | 10 (71.6) | 5.6 | 60.4–74.2 | 6.9 | 83% | 83% |
| The Death of Ivan Ilych — Leo Tolstoy | 11 (70.8) | 4.6 | 68.2–73.1 | 2.5 | 100% | 100% |
| The Waves — Virginia Woolf | 12 (70.7) | 7.0 | 54.9–74.0 | 9.6 | 71% | 70% |
| Bartleby the Scrivener — Herman Melville | 13 (69.8) | 6.5 | 63.9–72.7 | 4.4 | 49% | 49% |
| Faust: First Part — Johann Wolfgang von Goethe | 14 (69.1) | 5.1 | 61.6–72.1 | 5.3 | 100% | 100% |
| The Overcoat — Nikolai Gogol | 15 (69.1) | 7.6 | 54.4–72.2 | 8.9 | 48% | 48% |
| Inferno (The Divine Comedy #1) — Dante Alighieri | 16 (68.9) | 4.9 | 64.3–71.5 | 3.6 | 100% | 100% |
| The Magic Mountain — Thomas Mann | 17 (68.8) | 5.7 | 59.8–72.1 | 6.2 | 100% | 100% |
| The Adventures of Sherlock Holmes — Arthur Conan Doyle | 18 (68.7) | 5.0 | 60.9–70.9 | 5.0 | 100% | 100% |
| Infinite Jest — David Foster Wallace | 19 (68.7) | 5.8 | 62.1–72.0 | 5.0 | 86% | 86% |
| Faust — Johann Wolfgang von Goethe | 20 (68.1) | 6.9 | 56.5–70.7 | 7.1 | 48% | 48% |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 21 (68.1) | 4.4 | 61.1–70.3 | 4.6 | 100% | 100% |
| The Divine Comedy — Dante Alighieri | 22 (67.9) | 5.5 | 63.0–71.2 | 4.1 | 100% | 100% |
| Crime and Punishment — Fyodor Dostoyevsky | 23 (67.9) | 7.7 | 63.0–71.5 | 4.3 | 100% | 100% |
| Leaves of Grass — Walt Whitman | 24 (67.6) | 4.8 | 61.8–70.1 | 4.1 | 100% | 100% |
| Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 25 (66.9) | 4.0 | 59.9–68.5 | 4.3 | 100% | 100% |
| Paradise Lost — John Milton | 26 (66.8) | 6.1 | 59.2–71.1 | 6.0 | 100% | 100% |
| Hunger — Knut Hamsun | 27 (66.7) | 6.5 | 57.4–70.0 | 6.3 | 87% | 87% |
| Hopscotch — Julio Cortazar | 28 (66.7) | 6.1 | 57.3–70.2 | 6.4 | 69% | 69% |
| The Waste Land — T.S. Eliot | 29 (66.7) | 5.6 | 60.8–69.2 | 4.2 | 100% | 100% |
| The Arabian Nights — Anonymous | 30 (66.2) | 6.9 | 63.5–69.2 | 2.8 | 96% | 96% |
| King Lear — William Shakespeare | 31 (66.1) | 5.0 | 57.9–67.9 | 5.0 | 100% | 100% |
| East of Eden — John Steinbeck | 32 (66.0) | 4.8 | 60.9–68.3 | 3.7 | 100% | 100% |
| Songs of Innocence and of Experience — William Blake | 33 (65.5) | 6.6 | 59.8–68.3 | 4.2 | 90% | 90% |
| The Idiot — Fyodor Dostoyevsky | 34 (65.4) | 9.6 | 57.3–68.9 | 5.8 | 100% | 100% |
| Anna Karenina — Leo Tolstoy | 35 (64.9) | 4.0 | 59.0–68.1 | 4.5 | 100% | 100% |
| Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 36 (64.9) | 6.0 | 56.5–69.7 | 6.6 | 100% | 100% |
| Invisible Man — Ralph Ellison | 37 (64.8) | 5.6 | 58.0–67.8 | 4.9 | 100% | 100% |
| War and Peace — Leo Tolstoy | 38 (64.6) | 9.0 | 56.9–68.2 | 5.7 | 100% | 100% |
| Dead Souls — Nikolai Gogol | 39 (64.5) | 5.0 | 60.7–67.5 | 3.4 | 100% | 100% |
| A Streetcar Named Desire — Tennessee Williams | 40 (64.5) | 5.1 | 61.3–67.4 | 3.1 | 100% | 100% |
| If on a Winter's Night a Traveler — Italo Calvino | 41 (64.3) | 5.5 | 59.5–67.7 | 4.1 | 99% | 99% |
| The Raven — Edgar Allan Poe | 42 (64.2) | 7.0 | 58.3–68.5 | 5.1 | 74% | 74% |
| The Rime of the Ancient Mariner — Samuel Taylor Coleridge | 43 (63.9) | 6.5 | 54.6–66.7 | 6.1 | 83% | 83% |
| Metamorphoses — Ovid | 44 (63.4) | 6.2 | 57.6–66.8 | 4.6 | 96% | 96% |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 45 (62.9) | 5.9 | 57.5–66.7 | 4.6 | 100% | 100% |
| The Importance of Being Earnest — Oscar Wilde | 46 (62.7) | 4.6 | 58.4–65.6 | 3.6 | 100% | 100% |
| Eugene Onegin — Alexander Pushkin | 47 (62.6) | 5.6 | 55.7–66.3 | 5.3 | 100% | 100% |
| The Heart is a Lonely Hunter — Carson McCullers | 48 (62.6) | 6.5 | 48.3–66.5 | 9.1 | 46% | 45% |
| Germinal (Les Rougon-Macquart, #13) — Emile Zola | 49 (62.5) | 7.0 | 53.9–65.6 | 5.9 | 73% | 73% |
| A Hero of Our Time — Mikhail Lermontov | 50 (62.4) | 6.3 | 54.6–65.7 | 5.5 | 79% | 78% |
| The Count of Monte Cristo — Alexandre Dumas | 51 (61.9) | 4.8 | 56.2–64.2 | 4.0 | 100% | 100% |
| To the Lighthouse — Virginia Woolf | 52 (61.8) | 4.5 | 54.4–63.6 | 4.6 | 100% | 100% |
| Light in August — William Faulkner | 53 (61.8) | 6.5 | 53.2–65.2 | 6.0 | 69% | 69% |
| Mrs. Dalloway — Virginia Woolf | 54 (61.6) | 7.6 | 52.6–63.6 | 5.5 | 100% | 100% |
| Blindness — Jose Saramago | 55 (61.6) | 5.7 | 50.3–64.0 | 6.8 | 92% | 91% |
| All Quiet on the Western Front — Erich Maria Remarque | 56 (61.6) | 4.4 | 57.5–64.2 | 3.3 | 100% | 100% |
| Bleak House — Charles Dickens | 57 (61.5) | 5.4 | 57.4–64.6 | 3.6 | 100% | 100% |
| The Remains of the Day — Kazuo Ishiguro | 58 (61.2) | 6.1 | 57.4–64.3 | 3.4 | 98% | 98% |
| And Then There Were None — Agatha Christie | 59 (61.1) | 6.9 | 54.3–64.1 | 4.9 | 100% | 100% |
| The Name of the Rose — Umberto Eco | 60 (61.1) | 4.5 | 57.8–63.5 | 2.8 | 100% | 100% |

## Caveats

- Poisson bootstrap weights resample users, but jury membership and learned community assignments remain fixed. It calibrates ranking uncertainty conditional on the current jury reconstruction.
- Fractional expected-inclusion votes remove hash-seed noise; they do not create new readers or solve missing exposure.
- Conditional score intervals must be read alongside eligibility probability. A book with a high conditional score and low eligibility remains underexposed.

# Teacher-composition jury bootstrap

## Design

Each replicate Bayesian-bootstraps the positive teacher users, refits the five-fold rich behavioral jury model, selects a new 4,929-person jury within the fixed broad 20,000, and reranks books using exact expected-inclusion pair votes.

- Mode: **full**; completed replicates: **5,000**.
- Books tracked: **1,146**; baseline exact rankable: **297**.
- Jury Jaccard q10/median/q90: **0.916 / 0.929 / 0.940**.

## Baseline top books under jury reconstruction uncertainty

| book | baseline | jury q10–q90 | jury u80 | eligible | top200 |
|---|---:|---:|---:|---:|---:|
| Hamlet — William Shakespeare | 1 (79.7) | 77.5–80.1 | 1.3 | 100% | 100% |
| The Brothers Karamazov — Fyodor Dostoyevsky | 2 (76.8) | 75.7–77.7 | 1.0 | 100% | 100% |
| Les Fleurs du Mal — Charles Baudelaire | 3 (76.0) | 74.3–76.6 | 1.1 | 100% | 100% |
| Demons — Fyodor Dostoyevsky | 4 (75.9) | 74.9–76.2 | 0.7 | 89% | 89% |
| Macbeth — William Shakespeare | 5 (73.5) | 69.8–73.6 | 1.9 | 100% | 100% |
| Notes from Underground — Fyodor Dostoyevsky | 6 (73.2) | 73.1–74.0 | 0.4 | 38% | 38% |
| Shakespeare's Sonnets — William Shakespeare | 7 (73.2) | 72.2–73.3 | 0.5 | 100% | 100% |
| Les Misérables — Victor Hugo | 8 (72.0) | 70.2–72.6 | 1.2 | 100% | 100% |
| The Master and Margarita — Mikhail Bulgakov | 9 (71.7) | 71.1–72.4 | 0.6 | 100% | 100% |
| Journey to the End of the Night — Louis-Ferdinand Celine | 10 (71.6) | 71.3–72.4 | 0.5 | 100% | 100% |
| The Death of Ivan Ilych — Leo Tolstoy | 11 (70.8) | 69.4–71.0 | 0.8 | 100% | 100% |
| The Waves — Virginia Woolf | 12 (70.7) | 69.8–72.7 | 1.4 | 100% | 100% |
| Bartleby the Scrivener — Herman Melville | 13 (69.8) | 69.5–70.9 | 0.7 | 80% | 80% |
| Faust: First Part — Johann Wolfgang von Goethe | 14 (69.1) | 67.9–69.3 | 0.7 | 100% | 100% |
| The Overcoat — Nikolai Gogol | 15 (69.1) | 69.0–69.9 | 0.5 | 86% | 86% |
| Inferno (The Divine Comedy #1) — Dante Alighieri | 16 (68.9) | 68.8–70.3 | 0.7 | 100% | 100% |
| The Magic Mountain — Thomas Mann | 17 (68.8) | 68.2–69.7 | 0.7 | 100% | 100% |
| The Adventures of Sherlock Holmes — Arthur Conan Doyle | 18 (68.7) | 66.9–69.4 | 1.3 | 100% | 100% |
| Infinite Jest — David Foster Wallace | 19 (68.7) | 68.2–69.3 | 0.5 | 100% | 100% |
| Faust — Johann Wolfgang von Goethe | 20 (68.1) | 67.7–68.9 | 0.6 | 99% | 99% |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 21 (68.1) | 67.5–68.4 | 0.5 | 100% | 100% |
| The Divine Comedy — Dante Alighieri | 22 (67.9) | 66.8–68.7 | 0.9 | 100% | 100% |
| Crime and Punishment — Fyodor Dostoyevsky | 23 (67.9) | 66.6–68.8 | 1.1 | 100% | 100% |
| Leaves of Grass — Walt Whitman | 24 (67.6) | 66.6–67.8 | 0.6 | 100% | 100% |
| Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 25 (66.9) | 65.7–67.1 | 0.7 | 100% | 100% |
| Paradise Lost — John Milton | 26 (66.8) | 65.2–68.0 | 1.4 | 100% | 100% |
| Hunger — Knut Hamsun | 27 (66.7) | 66.6–67.6 | 0.5 | 100% | 100% |
| Hopscotch — Julio Cortazar | 28 (66.7) | 66.0–67.7 | 0.9 | 98% | 98% |
| The Waste Land — T.S. Eliot | 29 (66.7) | 66.5–67.5 | 0.5 | 100% | 100% |
| The Arabian Nights — Anonymous | 30 (66.2) | 66.0–66.9 | 0.4 | 100% | 100% |
| King Lear — William Shakespeare | 31 (66.1) | 65.6–67.4 | 0.9 | 100% | 100% |
| East of Eden — John Steinbeck | 32 (66.0) | 64.5–66.3 | 0.9 | 100% | 100% |
| Songs of Innocence and of Experience — William Blake | 33 (65.5) | 63.3–66.6 | 1.6 | 100% | 100% |
| The Idiot — Fyodor Dostoyevsky | 34 (65.4) | 63.8–66.5 | 1.4 | 100% | 100% |
| Anna Karenina — Leo Tolstoy | 35 (64.9) | 64.2–66.6 | 1.2 | 100% | 100% |
| Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 36 (64.9) | 63.9–65.4 | 0.8 | 100% | 100% |
| Invisible Man — Ralph Ellison | 37 (64.8) | 63.8–65.4 | 0.8 | 100% | 100% |
| War and Peace — Leo Tolstoy | 38 (64.6) | 60.7–64.6 | 1.9 | 100% | 100% |
| Dead Souls — Nikolai Gogol | 39 (64.5) | 63.1–65.1 | 1.0 | 100% | 100% |
| A Streetcar Named Desire — Tennessee Williams | 40 (64.5) | 63.6–64.7 | 0.5 | 100% | 100% |
| If on a Winter's Night a Traveler — Italo Calvino | 41 (64.3) | 63.6–64.6 | 0.5 | 100% | 100% |
| The Raven — Edgar Allan Poe | 42 (64.2) | 63.7–66.4 | 1.3 | 100% | 100% |
| The Rime of the Ancient Mariner — Samuel Taylor Coleridge | 43 (63.9) | 62.3–64.0 | 0.8 | 100% | 100% |
| Metamorphoses — Ovid | 44 (63.4) | 63.0–64.5 | 0.7 | 100% | 100% |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 45 (62.9) | 61.9–63.8 | 0.9 | 100% | 100% |
| The Importance of Being Earnest — Oscar Wilde | 46 (62.7) | 61.3–63.4 | 1.0 | 100% | 100% |
| Eugene Onegin — Alexander Pushkin | 47 (62.6) | 62.5–63.4 | 0.5 | 100% | 100% |
| The Heart is a Lonely Hunter — Carson McCullers | 48 (62.6) | 61.9–63.2 | 0.7 | 98% | 98% |
| Germinal (Les Rougon-Macquart, #13) — Emile Zola | 49 (62.5) | 60.2–63.7 | 1.7 | 100% | 100% |
| A Hero of Our Time — Mikhail Lermontov | 50 (62.4) | 61.7–63.0 | 0.6 | 100% | 100% |
| The Count of Monte Cristo — Alexandre Dumas | 51 (61.9) | 60.4–62.8 | 1.2 | 100% | 100% |
| To the Lighthouse — Virginia Woolf | 52 (61.8) | 60.5–62.3 | 0.9 | 100% | 100% |
| Light in August — William Faulkner | 53 (61.8) | 61.1–62.5 | 0.7 | 95% | 95% |
| Mrs. Dalloway — Virginia Woolf | 54 (61.6) | 60.5–62.1 | 0.8 | 100% | 100% |
| Blindness — Jose Saramago | 55 (61.6) | 59.8–61.8 | 1.0 | 100% | 100% |
| All Quiet on the Western Front — Erich Maria Remarque | 56 (61.6) | 60.5–62.1 | 0.8 | 100% | 100% |
| Bleak House — Charles Dickens | 57 (61.5) | 60.8–62.0 | 0.6 | 100% | 100% |
| The Remains of the Day — Kazuo Ishiguro | 58 (61.2) | 60.2–61.9 | 0.8 | 100% | 100% |
| And Then There Were None — Agatha Christie | 59 (61.1) | 59.2–60.9 | 0.8 | 100% | 100% |
| The Name of the Rose — Umberto Eco | 60 (61.1) | 60.9–62.0 | 0.6 | 100% | 100% |
| Cyrano de Bergerac — Edmond Rostand | 61 (60.6) | 60.0–61.2 | 0.6 | 93% | 93% |
| Orlando — Virginia Woolf | 62 (60.4) | 59.6–60.9 | 0.6 | 100% | 100% |
| Midnight's Children — Salman Rushdie | 63 (60.4) | 59.8–61.0 | 0.6 | 100% | 100% |
| The Wind in the Willows — Kenneth Grahame | 64 (60.3) | 59.3–61.2 | 1.0 | 94% | 94% |
| Doctor Zhivago — Boris Pasternak | 65 (60.1) | 59.3–61.3 | 1.0 | 100% | 100% |
| The Wind-Up Bird Chronicle — Haruki Murakami | 66 (60.1) | 59.6–61.3 | 0.9 | 100% | 100% |
| Antigone (The Theban Plays, #3) — Sophocles | 67 (60.0) | 59.2–61.0 | 0.9 | 100% | 100% |
| David Copperfield — Charles Dickens | 68 (59.9) | 59.1–60.5 | 0.7 | 100% | 100% |
| Anne of Green Gables (Anne of Green Gables, #1) — L.M. Montgomery | 69 (59.8) | 58.6–61.0 | 1.2 | 100% | 100% |
| One Hundred Years of Solitude — Gabriel Garcia Marquez | 70 (59.7) | 58.9–61.4 | 1.3 | 100% | 100% |
| Brideshead Revisited: The Sacred and Profane Memories of Captain Charles Ryder — Evelyn Waugh | 71 (59.7) | 58.7–60.4 | 0.8 | 100% | 100% |
| Julius Caesar — William Shakespeare | 72 (59.6) | 58.5–60.0 | 0.8 | 100% | 100% |
| One Flew Over the Cuckoo's Nest — Ken Kesey | 73 (59.6) | 58.0–60.8 | 1.4 | 100% | 100% |
| Othello — William Shakespeare | 74 (59.5) | 58.4–60.6 | 1.1 | 100% | 100% |
| The Iliad — Homer | 75 (59.5) | 58.5–62.2 | 1.9 | 100% | 100% |
| The Tin Drum — Gunter Grass | 76 (59.1) | 59.1–60.1 | 0.5 | 100% | 100% |
| The Castle — Franz Kafka | 77 (59.0) | 57.9–60.5 | 1.3 | 100% | 100% |
| The Fall — Albert Camus | 78 (58.9) | 58.7–60.9 | 1.1 | 100% | 100% |
| The Hunchback of Notre-Dame — Victor Hugo | 79 (58.7) | 57.4–59.1 | 0.9 | 100% | 100% |
| Les Liaisons dangereuses — Pierre-Ambroise Choderlos de Laclos | 80 (58.5) | 57.9–59.2 | 0.7 | 98% | 98% |

## Interpretation limits

- This isolates finite-teacher composition uncertainty. It does not bootstrap the choice of teacher definition, the broad 20,000-person pool, community learning, or missing exposure.
- A book's interval is conditional on passing evidence gates; eligibility probability is reported separately.
- Combine this component with the user-block campaign only after checking their dependence; do not automatically add interval widths.

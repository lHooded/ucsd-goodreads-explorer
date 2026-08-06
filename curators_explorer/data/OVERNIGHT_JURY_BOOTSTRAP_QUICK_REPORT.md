# Teacher-composition jury bootstrap

## Design

Each replicate Bayesian-bootstraps the positive teacher users, refits the five-fold rich behavioral jury model, selects a new 4,929-person jury within the fixed broad 20,000, and reranks books using exact expected-inclusion pair votes.

- Mode: **quick**; completed replicates: **2**.
- Books tracked: **1,146**; baseline exact rankable: **297**.
- Jury Jaccard q10/median/q90: **0.909 / 0.920 / 0.931**.

## Baseline top books under jury reconstruction uncertainty

| book | baseline | jury q10–q90 | jury u80 | eligible | top200 |
|---|---:|---:|---:|---:|---:|
| Hamlet — William Shakespeare | 1 (79.7) | 78.6–79.5 | 0.4 | 100% | 100% |
| The Brothers Karamazov — Fyodor Dostoyevsky | 2 (76.8) | 74.9–76.6 | 0.8 | 100% | 100% |
| Les Fleurs du Mal — Charles Baudelaire | 3 (76.0) | 76.1–76.4 | 0.2 | 100% | 100% |
| Demons — Fyodor Dostoyevsky | 4 (75.9) | 75.7–75.8 | 0.1 | 100% | 100% |
| Macbeth — William Shakespeare | 5 (73.5) | 72.9–73.7 | 0.4 | 100% | 100% |
| Notes from Underground — Fyodor Dostoyevsky | 6 (73.2) | — | — | 0% | 0% |
| Shakespeare's Sonnets — William Shakespeare | 7 (73.2) | 72.3–72.3 | 0.0 | 100% | 100% |
| Les Misérables — Victor Hugo | 8 (72.0) | 72.3–72.3 | 0.0 | 100% | 100% |
| The Master and Margarita — Mikhail Bulgakov | 9 (71.7) | 71.5–71.6 | 0.1 | 100% | 100% |
| Journey to the End of the Night — Louis-Ferdinand Celine | 10 (71.6) | 71.7–71.9 | 0.1 | 100% | 100% |
| The Death of Ivan Ilych — Leo Tolstoy | 11 (70.8) | 69.1–71.0 | 0.9 | 100% | 100% |
| The Waves — Virginia Woolf | 12 (70.7) | 71.5–72.5 | 0.5 | 100% | 100% |
| Bartleby the Scrivener — Herman Melville | 13 (69.8) | — | — | 0% | 0% |
| Faust: First Part — Johann Wolfgang von Goethe | 14 (69.1) | 68.9–69.2 | 0.1 | 100% | 100% |
| The Overcoat — Nikolai Gogol | 15 (69.1) | 70.1–70.1 | 0.0 | 50% | 50% |
| Inferno (The Divine Comedy #1) — Dante Alighieri | 16 (68.9) | 68.9–69.3 | 0.2 | 100% | 100% |
| The Magic Mountain — Thomas Mann | 17 (68.8) | 69.1–69.9 | 0.4 | 100% | 100% |
| The Adventures of Sherlock Holmes — Arthur Conan Doyle | 18 (68.7) | 67.8–69.5 | 0.8 | 100% | 100% |
| Infinite Jest — David Foster Wallace | 19 (68.7) | 68.4–69.1 | 0.4 | 100% | 100% |
| Faust — Johann Wolfgang von Goethe | 20 (68.1) | 67.9–68.6 | 0.4 | 100% | 100% |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 21 (68.1) | 68.3–68.4 | 0.1 | 100% | 100% |
| The Divine Comedy — Dante Alighieri | 22 (67.9) | 67.5–68.4 | 0.5 | 100% | 100% |
| Crime and Punishment — Fyodor Dostoyevsky | 23 (67.9) | 68.1–68.3 | 0.1 | 100% | 100% |
| Leaves of Grass — Walt Whitman | 24 (67.6) | 67.3–67.5 | 0.1 | 100% | 100% |
| Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 25 (66.9) | 66.1–66.9 | 0.4 | 100% | 100% |
| Paradise Lost — John Milton | 26 (66.8) | 66.2–66.3 | 0.0 | 100% | 100% |
| Hunger — Knut Hamsun | 27 (66.7) | 67.0–67.2 | 0.1 | 100% | 100% |
| Hopscotch — Julio Cortazar | 28 (66.7) | 66.5–67.7 | 0.6 | 100% | 100% |
| The Waste Land — T.S. Eliot | 29 (66.7) | 66.4–66.9 | 0.3 | 100% | 100% |
| The Arabian Nights — Anonymous | 30 (66.2) | 66.2–66.4 | 0.1 | 100% | 100% |
| King Lear — William Shakespeare | 31 (66.1) | 66.1–66.1 | 0.0 | 100% | 100% |
| East of Eden — John Steinbeck | 32 (66.0) | 65.5–65.6 | 0.1 | 100% | 100% |
| Songs of Innocence and of Experience — William Blake | 33 (65.5) | 63.6–65.4 | 0.9 | 100% | 100% |
| The Idiot — Fyodor Dostoyevsky | 34 (65.4) | 64.8–66.1 | 0.7 | 100% | 100% |
| Anna Karenina — Leo Tolstoy | 35 (64.9) | 65.3–65.4 | 0.1 | 100% | 100% |
| Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 36 (64.9) | 64.6–65.3 | 0.3 | 100% | 100% |
| Invisible Man — Ralph Ellison | 37 (64.8) | 64.0–64.1 | 0.0 | 100% | 100% |
| War and Peace — Leo Tolstoy | 38 (64.6) | 60.8–62.1 | 0.7 | 100% | 100% |
| Dead Souls — Nikolai Gogol | 39 (64.5) | 62.9–64.3 | 0.7 | 100% | 100% |
| A Streetcar Named Desire — Tennessee Williams | 40 (64.5) | 64.2–64.5 | 0.2 | 100% | 100% |
| If on a Winter's Night a Traveler — Italo Calvino | 41 (64.3) | 63.8–64.4 | 0.3 | 100% | 100% |
| The Raven — Edgar Allan Poe | 42 (64.2) | 63.6–65.4 | 0.9 | 100% | 100% |
| The Rime of the Ancient Mariner — Samuel Taylor Coleridge | 43 (63.9) | 63.6–63.7 | 0.1 | 100% | 100% |
| Metamorphoses — Ovid | 44 (63.4) | 63.5–64.5 | 0.5 | 100% | 100% |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 45 (62.9) | 63.1–63.2 | 0.1 | 100% | 100% |
| The Importance of Being Earnest — Oscar Wilde | 46 (62.7) | 62.3–63.3 | 0.5 | 100% | 100% |
| Eugene Onegin — Alexander Pushkin | 47 (62.6) | 62.4–62.9 | 0.2 | 100% | 100% |
| The Heart is a Lonely Hunter — Carson McCullers | 48 (62.6) | 61.7–62.7 | 0.5 | 100% | 100% |
| Germinal (Les Rougon-Macquart, #13) — Emile Zola | 49 (62.5) | 61.2–62.8 | 0.8 | 100% | 100% |
| A Hero of Our Time — Mikhail Lermontov | 50 (62.4) | 62.2–62.3 | 0.1 | 100% | 100% |
| The Count of Monte Cristo — Alexandre Dumas | 51 (61.9) | 62.0–62.0 | 0.0 | 100% | 100% |
| To the Lighthouse — Virginia Woolf | 52 (61.8) | 59.7–62.1 | 1.2 | 100% | 100% |
| Light in August — William Faulkner | 53 (61.8) | 62.3–62.8 | 0.3 | 100% | 100% |
| Mrs. Dalloway — Virginia Woolf | 54 (61.6) | 61.0–61.6 | 0.3 | 100% | 100% |
| Blindness — Jose Saramago | 55 (61.6) | 60.2–61.0 | 0.4 | 100% | 100% |
| All Quiet on the Western Front — Erich Maria Remarque | 56 (61.6) | 61.4–62.4 | 0.5 | 100% | 100% |
| Bleak House — Charles Dickens | 57 (61.5) | 61.5–61.6 | 0.1 | 100% | 100% |
| The Remains of the Day — Kazuo Ishiguro | 58 (61.2) | 60.5–61.6 | 0.6 | 100% | 100% |
| And Then There Were None — Agatha Christie | 59 (61.1) | 59.7–61.0 | 0.7 | 100% | 100% |
| The Name of the Rose — Umberto Eco | 60 (61.1) | 61.7–61.9 | 0.1 | 100% | 100% |
| Cyrano de Bergerac — Edmond Rostand | 61 (60.6) | 60.0–60.0 | 0.0 | 50% | 50% |
| Orlando — Virginia Woolf | 62 (60.4) | 60.5–61.2 | 0.3 | 100% | 100% |
| Midnight's Children — Salman Rushdie | 63 (60.4) | 60.6–61.3 | 0.4 | 100% | 100% |
| The Wind in the Willows — Kenneth Grahame | 64 (60.3) | 60.3–60.4 | 0.1 | 100% | 100% |
| Doctor Zhivago — Boris Pasternak | 65 (60.1) | 59.7–60.4 | 0.4 | 100% | 100% |
| The Wind-Up Bird Chronicle — Haruki Murakami | 66 (60.1) | 60.0–60.8 | 0.4 | 100% | 100% |
| Antigone (The Theban Plays, #3) — Sophocles | 67 (60.0) | 58.9–60.3 | 0.7 | 100% | 100% |
| David Copperfield — Charles Dickens | 68 (59.9) | 59.2–60.3 | 0.5 | 100% | 100% |
| Anne of Green Gables (Anne of Green Gables, #1) — L.M. Montgomery | 69 (59.8) | 59.2–60.9 | 0.9 | 100% | 100% |
| One Hundred Years of Solitude — Gabriel Garcia Marquez | 70 (59.7) | 60.3–60.6 | 0.1 | 100% | 100% |
| Brideshead Revisited: The Sacred and Profane Memories of Captain Charles Ryder — Evelyn Waugh | 71 (59.7) | 59.8–59.9 | 0.1 | 100% | 100% |
| Julius Caesar — William Shakespeare | 72 (59.6) | 59.2–59.7 | 0.3 | 100% | 100% |
| One Flew Over the Cuckoo's Nest — Ken Kesey | 73 (59.6) | 57.7–57.8 | 0.1 | 100% | 100% |
| Othello — William Shakespeare | 74 (59.5) | 58.7–59.3 | 0.3 | 100% | 100% |
| The Iliad — Homer | 75 (59.5) | 58.7–58.8 | 0.0 | 100% | 100% |
| The Tin Drum — Gunter Grass | 76 (59.1) | 59.1–59.6 | 0.3 | 100% | 100% |
| The Castle — Franz Kafka | 77 (59.0) | 58.5–58.9 | 0.2 | 100% | 100% |
| The Fall — Albert Camus | 78 (58.9) | 59.8–61.5 | 0.8 | 100% | 100% |
| The Hunchback of Notre-Dame — Victor Hugo | 79 (58.7) | 57.5–58.4 | 0.5 | 100% | 100% |
| Les Liaisons dangereuses — Pierre-Ambroise Choderlos de Laclos | 80 (58.5) | 58.2–58.3 | 0.0 | 100% | 100% |

## Interpretation limits

- This isolates finite-teacher composition uncertainty. It does not bootstrap the choice of teacher definition, the broad 20,000-person pool, community learning, or missing exposure.
- A book's interval is conditional on passing evidence gates; eligibility probability is reported separately.
- Combine this component with the user-block campaign only after checking their dependence; do not automatically add interval widths.

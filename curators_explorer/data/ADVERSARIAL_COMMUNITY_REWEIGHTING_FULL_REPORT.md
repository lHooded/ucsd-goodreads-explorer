# Adversarial community-influence audit

## Design

Communities start with equal influence. The shared-mixture path repeatedly changes those influences for the entire catalog while limiting the largest community weight to R times the smallest. The least-favourable path gives each individual book the most adverse mixture allowed by the same bound. The latter is intentionally severe and remains a sensitivity bound, not the point score.

- Mode: **full**; shared mixtures per bound: **1,000**.
- Point validation: formula error **2.2e-16**; stored top-200 Jaccard **1.000**.

| max community ratio | shared mean J@50 | shared q10 J@50 | shared mean J@200 | shared q10 J@200 | least-favourable J@50 | least-favourable J@200 |
|---:|---:|---:|---:|---:|---:|---:|
| 1.5 | 0.988 | 0.961 | 0.994 | 0.990 | 0.961 | 0.980 |
| 2.0 | 0.976 | 0.923 | 0.990 | 0.980 | 0.961 | 0.951 |

Within the point top 200, **193** books are broadly stable and **7** are mixture-sensitive under the preregistered R=2 rule.

## Point head trajectories

| # | book | point | R1.5 worst score/rank | R2 worst score/rank | R2 shared ranks | R2 top200 | status |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 83.5 | 82.5/1 | 81.8/1 | 1-1 | 100% | broadly_stable |
| 2 | Hamlet — William Shakespeare | 83.0 | 82.1/2 | 81.4/2 | 2-2 | 100% | broadly_stable |
| 3 | Les Misérables — Victor Hugo | 75.6 | 74.5/3 | 73.7/3 | 3-3 | 100% | broadly_stable |
| 4 | Crime and Punishment — Fyodor Dostoyevsky | 75.3 | 73.7/5 | 72.6/5 | 4-5 | 100% | broadly_stable |
| 5 | Macbeth — William Shakespeare | 75.2 | 74.0/4 | 73.2/4 | 4-5 | 100% | broadly_stable |
| 6 | The Master and Margarita — Mikhail Bulgakov | 74.0 | 73.1/6 | 72.5/7 | 6-6 | 100% | broadly_stable |
| 7 | Demons — Fyodor Dostoyevsky | 73.7 | 73.0/7 | 72.5/6 | 7-7 | 100% | broadly_stable |
| 8 | The Idiot — Fyodor Dostoyevsky | 71.2 | 70.0/9 | 69.1/9 | 8-9 | 100% | broadly_stable |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 71.1 | 70.2/8 | 69.5/8 | 8-9 | 100% | broadly_stable |
| 10 | Shakespeare's Sonnets — William Shakespeare | 70.2 | 69.2/10 | 68.5/10 | 10-10 | 100% | broadly_stable |
| 11 | Paradise Lost — John Milton | 69.9 | 68.7/12 | 67.8/13 | 11-11 | 100% | broadly_stable |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 69.4 | 68.5/13 | 67.8/12 | 12-13 | 100% | broadly_stable |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 69.3 | 68.8/11 | 68.4/11 | 12-13 | 100% | broadly_stable |
| 14 | The Divine Comedy — Dante Alighieri | 69.0 | 67.9/14 | 67.2/14 | 14-14 | 100% | broadly_stable |
| 15 | War and Peace — Leo Tolstoy | 68.7 | 67.2/15 | 66.0/16 | 15-16 | 100% | broadly_stable |
| 16 | Anna Karenina — Leo Tolstoy | 68.5 | 67.0/17 | 65.9/17 | 15-16 | 100% | broadly_stable |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 67.9 | 67.0/16 | 66.4/15 | 17-17 | 100% | broadly_stable |
| 18 | King Lear — William Shakespeare | 67.3 | 66.1/19 | 65.3/19 | 18-19 | 100% | broadly_stable |
| 19 | The Magic Mountain — Thomas Mann | 67.2 | 66.1/18 | 65.4/18 | 18-19 | 100% | broadly_stable |
| 20 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 66.8 | 65.7/20 | 64.9/20 | 19-21 | 100% | broadly_stable |
| 21 | Faust: First Part — Johann Wolfgang von Goethe | 66.5 | 65.4/21 | 64.6/21 | 20-21 | 100% | broadly_stable |
| 22 | Leaves of Grass — Walt Whitman | 66.1 | 65.2/22 | 64.6/22 | 22-22 | 100% | broadly_stable |
| 23 | Stoner — John  Williams | 65.7 | 64.9/23 | 64.4/23 | 23-23 | 100% | broadly_stable |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 65.5 | 64.6/24 | 64.0/24 | 24-24 | 100% | broadly_stable |
| 25 | Infinite Jest — David Foster Wallace | 65.0 | 64.2/25 | 63.6/25 | 25-26 | 100% | broadly_stable |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 65.0 | 63.9/26 | 63.2/26 | 25-27 | 100% | broadly_stable |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 64.8 | 63.7/27 | 62.9/27 | 26-27 | 100% | broadly_stable |
| 28 | The Iliad — Homer | 64.1 | 62.7/29 | 61.6/31 | 28-29 | 100% | broadly_stable |
| 29 | The Waves — Virginia Woolf | 64.0 | 62.9/28 | 62.1/28 | 28-29 | 100% | broadly_stable |
| 30 | The Count of Monte Cristo — Alexandre Dumas | 63.5 | 62.0/35 | 60.9/37 | 30-32 | 100% | broadly_stable |
| 31 | The Waste Land — T.S. Eliot | 63.4 | 62.4/30 | 61.8/29 | 30-32 | 100% | broadly_stable |
| 32 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 63.3 | 62.1/34 | 61.2/35 | 31-34 | 100% | broadly_stable |
| 33 | 2666 — Roberto Bolano | 63.1 | 62.2/32 | 61.6/32 | 32-35 | 100% | broadly_stable |
| 34 | A Streetcar Named Desire — Tennessee Williams | 63.1 | 62.3/31 | 61.7/30 | 33-35 | 100% | broadly_stable |
| 35 | The Book of Disquiet — Fernando Pessoa | 63.0 | 62.1/33 | 61.5/33 | 33-36 | 100% | broadly_stable |
| 36 | East of Eden — John Steinbeck | 62.9 | 61.9/36 | 61.2/34 | 34-36 | 100% | broadly_stable |
| 37 | Bartleby the Scrivener — Herman Melville | 62.6 | 61.6/37 | 61.0/36 | 37-37 | 100% | broadly_stable |
| 38 | The Overcoat — Nikolai Gogol | 62.2 | 61.3/38 | 60.7/38 | 38-38 | 100% | broadly_stable |
| 39 | Dead Souls — Nikolai Gogol | 61.8 | 61.0/39 | 60.5/39 | 39-40 | 100% | broadly_stable |
| 40 | One Hundred Years of Solitude — Gabriel Garcia Marquez | 61.7 | 60.1/42 | 59.1/44 | 39-41 | 100% | broadly_stable |
| 41 | Hunger — Knut Hamsun | 61.6 | 60.8/40 | 60.2/40 | 40-41 | 100% | broadly_stable |
| 42 | The Sound and the Fury — William Faulkner | 61.0 | 59.6/46 | 58.7/47 | 42-44 | 100% | broadly_stable |
| 43 | The Arabian Nights — Anonymous | 60.9 | 60.1/43 | 59.5/42 | 42-45 | 100% | broadly_stable |
| 44 | Richard III — William Shakespeare | 60.8 | 60.2/41 | 59.7/41 | 43-45 | 100% | broadly_stable |
| 45 | In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust | 60.7 | 59.7/45 | 58.9/45 | 43-46 | 100% | broadly_stable |
| 46 | If on a Winter's Night a Traveler — Italo Calvino | 60.6 | 59.8/44 | 59.2/43 | 45-47 | 100% | broadly_stable |
| 47 | Othello — William Shakespeare | 60.5 | 59.0/52 | 57.9/56 | 46-49 | 100% | broadly_stable |
| 48 | Eugene Onegin — Alexander Pushkin | 60.5 | 59.5/47 | 58.7/46 | 46-49 | 100% | broadly_stable |
| 49 | The Importance of Being Earnest — Oscar Wilde | 60.3 | 59.2/50 | 58.4/50 | 47-52 | 100% | broadly_stable |
| 50 | Blood Meridian, or the Evening Redness in the West — Cormac McCarthy | 60.2 | 59.3/48 | 58.6/49 | 49-52 | 100% | broadly_stable |
| 51 | Don Quixote — Miguel de Cervantes Saavedra | 60.1 | 58.7/54 | 57.6/59 | 49-53 | 100% | broadly_stable |
| 52 | Faust — Johann Wolfgang von Goethe | 60.1 | 59.2/49 | 58.7/48 | 50-54 | 100% | broadly_stable |
| 53 | Pedro Páramo — Juan Rulfo | 60.0 | 59.0/51 | 58.3/51 | 51-54 | 100% | broadly_stable |
| 54 | To the Lighthouse — Virginia Woolf | 59.9 | 58.8/53 | 58.0/53 | 52-55 | 100% | broadly_stable |
| 55 | The Odyssey — Homer | 59.7 | 57.9/61 | 56.5/67 | 54-58 | 100% | broadly_stable |
| 56 | Twenty Love Poems and a Song of Despair — Pablo Neruda | 59.6 | 58.7/55 | 58.0/54 | 55-57 | 100% | broadly_stable |
| 57 | Invisible Man — Ralph Ellison | 59.5 | 58.6/57 | 57.9/55 | 56-59 | 100% | broadly_stable |
| 58 | Hopscotch — Julio Cortazar | 59.4 | 58.5/58 | 57.8/57 | 56-60 | 100% | broadly_stable |
| 59 | The Raven — Edgar Allan Poe | 59.3 | 58.6/56 | 58.1/52 | 58-60 | 100% | broadly_stable |
| 60 | Songs of Innocence and of Experience — William Blake | 59.3 | 58.3/59 | 57.7/58 | 57-61 | 100% | broadly_stable |

The least-favourable path compounds the central model's existing disagreement penalty, so it should flag dependence rather than replace the main ranking. Shared mixtures are the cleaner test of whether a common change in community influence destabilizes the catalog.

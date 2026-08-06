# Hierarchical jury-feature-family audit

## Result

The baseline rich-behavior jury, the plausible no-direct-activity jury, and the generic-only adversarial ablation are propagated through hard and conservative fuzzy90 communities. Communities remain frozen to the baseline 20,000-user space.

| jury / communities | role | rankable | J@50 hard | J@200 hard | RBO hard | J@50 soft | J@200 soft | score rho | pop rho | med u |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rich_behavior_global / hard | plausible baseline | 1146 | 1.000 | 1.000 | 1.000 | 0.961 | 0.951 | 1.000 | -0.312 | 6.99 |
| rich_behavior_global / fuzzy90 | plausible baseline | 1146 | 0.923 | 0.970 | 0.954 | 0.961 | 0.942 | 1.000 | -0.309 | 7.05 |
| rich_no_direct_activity / hard | plausible shelf-size ablation | 1112 | 0.887 | 0.878 | 0.880 | 0.887 | 0.887 | 0.991 | -0.312 | 7.07 |
| rich_no_direct_activity / fuzzy90 | plausible shelf-size ablation | 1112 | 0.852 | 0.869 | 0.873 | 0.887 | 0.887 | 0.990 | -0.313 | 7.04 |
| generic_behavior_only / hard | adversarial estimand ablation | 281 | 0.064 | 0.105 | 0.166 | 0.064 | 0.105 | 0.459 | -0.309 | 8.23 |
| generic_behavior_only / fuzzy90 | adversarial estimand ablation | 281 | 0.064 | 0.105 | 0.162 | 0.064 | 0.105 | 0.461 | -0.304 | 8.22 |

## Soft-point head trajectories

| # | book | baseline hard | no-activity hard | no-activity fuzzy | generic hard |
|---:|---|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 2 | 1 | 1 | 2 |
| 2 | Hamlet — William Shakespeare | 1 | 2 | 2 | 238 |
| 3 | Crime and Punishment — Fyodor Dostoyevsky | 5 | 4 | 4 | 16 |
| 4 | Les Misérables — Victor Hugo | 4 | 3 | 3 | 101 |
| 5 | Macbeth — William Shakespeare | 3 | 8 | 8 | 224 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 6 | 6 | 7 | 13 |
| 7 | Demons — Fyodor Dostoyevsky | 7 | 5 | 5 | None |
| 8 | The Idiot — Fyodor Dostoyevsky | 9 | 11 | 10 | None |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 8 | 9 | 9 | None |
| 10 | Shakespeare's Sonnets — William Shakespeare | 10 | 27 | 27 | None |
| 11 | Paradise Lost — John Milton | 13 | 7 | 6 | None |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 15 | 10 | 11 | None |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 11 | 16 | 18 | None |
| 14 | The Divine Comedy — Dante Alighieri | 14 | 12 | 12 | None |
| 15 | Anna Karenina — Leo Tolstoy | 17 | 14 | 14 | 62 |
| 16 | War and Peace — Leo Tolstoy | 12 | 13 | 13 | 30 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 16 | 17 | 17 | None |
| 18 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 18 | 19 | 20 | 22 |
| 19 | The Magic Mountain — Thomas Mann | 19 | 20 | 21 | None |
| 20 | King Lear — William Shakespeare | 22 | 15 | 16 | 128 |
| 21 | Leaves of Grass — Walt Whitman | 21 | 23 | 23 | None |
| 22 | Faust: First Part — Johann Wolfgang von Goethe | 20 | 18 | 15 | None |
| 23 | Stoner — John  Williams | 23 | 24 | 25 | None |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 24 | 21 | 19 | None |
| 25 | Infinite Jest — David Foster Wallace | 25 | 50 | 48 | None |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 26 | 25 | 24 | None |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 27 | 31 | 30 | None |
| 28 | The Waves — Virginia Woolf | 29 | 22 | 22 | None |
| 29 | The Iliad — Homer | 36 | 33 | 33 | 171 |
| 30 | The Waste Land — T.S. Eliot | 35 | 26 | 26 | None |
| 31 | The Count of Monte Cristo — Alexandre Dumas | 30 | 34 | 34 | 61 |
| 32 | 2666 — Roberto Bolano | 31 | 32 | 31 | None |
| 33 | A Streetcar Named Desire — Tennessee Williams | 28 | 29 | 32 | None |
| 34 | The Book of Disquiet — Fernando Pessoa | 33 | 35 | 35 | None |
| 35 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 32 | 40 | 37 | 64 |
| 36 | Bartleby the Scrivener — Herman Melville | 37 | 39 | 39 | None |
| 37 | The Overcoat — Nikolai Gogol | 34 | 28 | 28 | None |
| 38 | Dead Souls — Nikolai Gogol | 39 | 43 | 44 | None |
| 39 | East of Eden — John Steinbeck | 38 | 56 | 62 | 34 |
| 40 | Hunger — Knut Hamsun | 40 | 30 | 29 | None |
| 41 | In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust | 45 | 38 | 36 | None |
| 42 | The Arabian Nights — Anonymous | 41 | 51 | 50 | None |
| 43 | One Hundred Years of Solitude — Gabriel Garcia Marquez | 42 | 45 | 51 | 63 |
| 44 | Richard III — William Shakespeare | 46 | 52 | 52 | None |
| 45 | If on a Winter's Night a Traveler — Italo Calvino | 43 | 46 | 45 | None |
| 46 | The Sound and the Fury — William Faulkner | 55 | 37 | 40 | 163 |
| 47 | The Importance of Being Earnest — Oscar Wilde | 44 | 42 | 42 | 51 |
| 48 | Othello — William Shakespeare | 47 | 49 | 47 | 164 |
| 49 | Faust — Johann Wolfgang von Goethe | 48 | 44 | 43 | None |
| 50 | Eugene Onegin — Alexander Pushkin | 50 | 41 | 41 | None |

The no-activity path is a plausible constituency perturbation. The generic-only path removes the feature family that defines the literary estimand and is therefore a falsification diagnostic, not an equal-vote veto.

# Jury-feature and pair-seed trajectories

## Design

Two plausible rich-behavior jury reconstructions and one generic-only adversarial ablation are crossed with five deterministic balanced pair samples. Jury size, 5★ versus ≤3★ semantics, and the exposure-adjusted score are fixed. The latent space and communities are fitted only on the original rich-model top 20,000; alternative-jury outsiders are projected into that frozen space.

- Universes: **15**.
- Analysis users: **23,867**; alternative juries add **3,867** people outside the rich-model top 20,000.
- Previous-central versus new-central Jaccard@200: **0.990**.

## Jury reconstruction overlap

| jury | role | features | overlap with baseline | Jaccard |
|---|---|---:|---:|---:|
| rich_behavior_global | plausible | 51 | 4,929 | 1.000 |
| rich_no_direct_activity | plausible | 47 | 4,421 | 0.813 |
| generic_behavior_only | adversarial_ablation | 37 | 375 | 0.040 |

## One-factor stability

| universe | rankable | J@50 | J@200 | RBO |
|---|---:|---:|---:|---:|
| rich_behavior_global__seed11 | 353 | 1.000 | 1.000 | 1.000 |
| rich_no_direct_activity__seed11 | 354 | 0.667 | 0.826 | 0.805 |
| generic_behavior_only__seed11 | 22 | 0.029 | 0.018 | 0.027 |
| rich_behavior_global__seed23 | 348 | 0.389 | 0.594 | 0.485 |
| rich_behavior_global__seed47 | 348 | 0.471 | 0.562 | 0.552 |
| rich_behavior_global__seed89 | 355 | 0.429 | 0.594 | 0.544 |
| rich_behavior_global__seed131 | 356 | 0.351 | 0.594 | 0.500 |

## Result

- **58** central books pass the new feature/seed axes.
- **47** of the prior 50 jointly robust books also pass; this is the current cumulative core.
- Plausible feature family: **12** semantic and **7** evidence-sensitive central books.
- The generic-only ablation can rank only **4** central books. Its 4% jury overlap and evidence collapse make it a useful falsification test, not an equal-vote veto on the literary estimand.
- Pair seed: **26** semantic and **55** evidence-sensitive central books.

A sampling-seed failure means the book's estimate depends on which finite set of each reader's high/low ratings was sampled. It should be addressed by repeated-sample aggregation or by using all bounded per-user votes, not interpreted as constituency disagreement.

## Cumulative robust core

| book | base | score ± u | Γ1.5 | jury | seeds | crossed |
|---|---:|---:|---:|---:|---:|---:|
| The Brothers Karamazov — Fyodor Dostoyevsky | 1 | 82.3 ± 3.1 | 75.9 | 100%/100% | 100%/100% | 100% |
| Hamlet — William Shakespeare | 2 | 76.9 ± 4.0 | 69.8 | 100%/100% | 100%/100% | 100% |
| The Magic Mountain — Thomas Mann | 3 | 75.8 ± 6.4 | 67.0 | 100%/100% | 100%/100% | 100% |
| Shakespeare's Sonnets — William Shakespeare | 4 | 75.1 ± 5.3 | 67.1 | 100%/100% | 100%/100% | 100% |
| Stoner — John  Williams | 5 | 74.5 ± 5.9 | 66.5 | 100%/100% | 80%/80% | 80% |
| Notes from Underground — Fyodor Dostoyevsky | 6 | 73.1 ± 6.0 | 64.8 | 100%/100% | 100%/100% | 100% |
| Invisible Man — Ralph Ellison | 7 | 71.7 ± 5.7 | 63.4 | 100%/100% | 100%/100% | 100% |
| Journey to the End of the Night — Louis-Ferdinand Celine | 8 | 71.5 ± 6.5 | 62.5 | 100%/100% | 100%/100% | 100% |
| Les Fleurs du Mal — Charles Baudelaire | 9 | 71.4 ± 5.1 | 62.9 | 100%/100% | 100%/100% | 100% |
| Faust: First Part — Johann Wolfgang von Goethe | 10 | 71.3 ± 5.7 | 62.5 | 100%/100% | 100%/100% | 100% |
| Songs of Innocence and of Experience — William Blake | 11 | 71.3 ± 6.3 | 62.9 | 100%/100% | 80%/80% | 80% |
| Les Misérables — Victor Hugo | 13 | 71.1 ± 5.0 | 61.8 | 100%/100% | 100%/100% | 100% |
| Macbeth — William Shakespeare | 15 | 70.7 ± 5.5 | 61.3 | 100%/100% | 100%/100% | 100% |
| The Rime of the Ancient Mariner — Samuel Taylor Coleridge | 16 | 70.5 ± 6.3 | 61.8 | 100%/100% | 100%/100% | 100% |
| Inferno (The Divine Comedy #1) — Dante Alighieri | 17 | 70.1 ± 4.7 | 61.3 | 100%/100% | 100%/100% | 100% |
| The Waves — Virginia Woolf | 18 | 70.0 ± 6.9 | 61.1 | 100%/100% | 80%/80% | 80% |
| Metamorphoses — Ovid | 20 | 69.2 ± 5.9 | 60.3 | 100%/100% | 100%/100% | 100% |
| Hunger — Knut Hamsun | 21 | 68.7 ± 7.5 | 60.0 | 100%/100% | 100%/100% | 100% |
| Infinite Jest — David Foster Wallace | 22 | 68.5 ± 5.9 | 59.6 | 100%/100% | 80%/80% | 80% |
| The Adventures of Sherlock Holmes — Arthur Conan Doyle | 23 | 68.3 ± 5.6 | 59.6 | 100%/100% | 100%/100% | 100% |
| Leaves of Grass — Walt Whitman | 25 | 67.4 ± 5.9 | 58.9 | 100%/100% | 100%/100% | 100% |
| Dead Souls — Nikolai Gogol | 27 | 66.1 ± 6.5 | 57.6 | 100%/100% | 100%/100% | 100% |
| The Death of Ivan Ilych — Leo Tolstoy | 29 | 65.5 ± 4.8 | 56.0 | 100%/100% | 100%/100% | 100% |
| East of Eden — John Steinbeck | 31 | 65.3 ± 5.6 | 56.4 | 100%/100% | 100%/100% | 100% |
| War and Peace — Leo Tolstoy | 32 | 65.3 ± 5.7 | 56.5 | 100%/100% | 100%/100% | 100% |
| King Lear — William Shakespeare | 35 | 64.1 ± 5.9 | 53.4 | 100%/100% | 100%/100% | 100% |
| The Tin Drum — Gunter Grass | 39 | 63.5 ± 6.2 | 54.2 | 100%/100% | 80%/80% | 90% |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 40 | 63.2 ± 5.8 | 53.7 | 100%/100% | 100%/100% | 100% |
| The Idiot — Fyodor Dostoyevsky | 41 | 63.2 ± 8.0 | 53.6 | 100%/100% | 100%/100% | 100% |
| Medea — Euripides | 42 | 63.1 ± 6.0 | 53.7 | 100%/100% | 100%/100% | 100% |
| As I Lay Dying — William Faulkner | 43 | 63.0 ± 5.9 | 53.1 | 100%/100% | 100%/100% | 100% |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 44 | 62.9 ± 6.8 | 53.7 | 100%/100% | 100%/100% | 100% |
| The Master and Margarita — Mikhail Bulgakov | 45 | 62.7 ± 7.2 | 53.1 | 100%/100% | 100%/100% | 100% |
| Paradise Lost — John Milton | 47 | 62.2 ± 8.8 | 53.2 | 100%/100% | 100%/100% | 100% |
| A Streetcar Named Desire — Tennessee Williams | 48 | 62.1 ± 6.8 | 52.9 | 100%/100% | 100%/100% | 100% |
| Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 50 | 62.0 ± 5.7 | 53.1 | 100%/100% | 100%/100% | 100% |
| If on a Winter's Night a Traveler — Italo Calvino | 52 | 61.8 ± 7.9 | 52.3 | 100%/100% | 100%/100% | 100% |
| Blindness — Jose Saramago | 53 | 61.8 ± 7.0 | 52.2 | 100%/100% | 100%/100% | 100% |
| The Divine Comedy — Dante Alighieri | 54 | 61.7 ± 10.1 | 52.1 | 100%/100% | 100%/100% | 100% |
| Crime and Punishment — Fyodor Dostoyevsky | 55 | 61.6 ± 10.5 | 53.2 | 100%/100% | 100%/100% | 100% |
| The Name of the Rose — Umberto Eco | 56 | 61.6 ± 4.6 | 52.0 | 100%/100% | 100%/100% | 100% |
| All Quiet on the Western Front — Erich Maria Remarque | 58 | 61.1 ± 4.6 | 51.4 | 100%/100% | 100%/100% | 100% |
| Narcissus and Goldmund — Hermann Hesse | 60 | 60.8 ± 7.1 | 51.7 | 100%/100% | 100%/100% | 100% |
| Richard III — William Shakespeare | 61 | 60.5 ± 8.8 | 50.9 | 100%/100% | 80%/80% | 80% |
| The Wind in the Willows — Kenneth Grahame | 63 | 60.3 ± 8.5 | 51.1 | 100%/100% | 100%/100% | 100% |
| The Merchant of Venice — William Shakespeare | 66 | 59.9 ± 8.3 | 50.3 | 100%/100% | 80%/100% | 80% |
| Eugene Onegin — Alexander Pushkin | 68 | 59.6 ± 6.5 | 50.1 | 100%/100% | 100%/100% | 100% |

## Plausible feature-family-sensitive books

| book | base | score ± u | Γ1.5 | jury | seeds | crossed |
|---|---:|---:|---:|---:|---:|---:|
| The Phantom of the Opera — Gaston Leroux | 195 | 45.6 ± 11.5 | 36.8 | 50%/100% | 40%/100% | 20% |
| Norwegian Wood — Haruki Murakami | 165 | 47.6 ± 5.2 | 38.0 | 50%/100% | 60%/100% | 30% |
| The Metamorphosis — Franz Kafka | 168 | 47.4 ± 7.1 | 37.1 | 50%/100% | 40%/100% | 30% |
| Don Quixote — Miguel de Cervantes Saavedra | 159 | 48.3 ± 9.1 | 38.8 | 50%/100% | 80%/100% | 60% |
| Cannery Row — John Steinbeck | 162 | 48.1 ± 7.8 | 37.5 | 50%/100% | 60%/80% | 40% |
| Candide — Voltaire | 178 | 46.6 ± 7.7 | 36.1 | 50%/100% | 80%/100% | 70% |
| Tropic of Cancer — Henry Miller | 170 | 47.0 ± 9.4 | 37.6 | 50%/100% | 80%/100% | 80% |
| Dubliners — James Joyce | 174 | 46.8 ± 9.4 | 37.5 | 50%/100% | 80%/100% | 50% |
| The House of the Spirits — Isabel Allende | 194 | 45.7 ± 6.1 | 36.5 | 50%/100% | 60%/100% | 40% |
| Hard Times — Charles Dickens | 199 | 45.0 ± 7.7 | 35.9 | 50%/100% | 20%/100% | 10% |
| The Stranger — Albert Camus | 198 | 45.3 ± 6.5 | 35.0 | 50%/100% | 60%/100% | 40% |
| The Picture of Dorian Gray — Oscar Wilde | 200 | 45.0 ± 6.2 | 36.6 | 50%/100% | 100%/100% | 80% |

## Pair-sampling-seed-sensitive books

| book | base | score ± u | Γ1.5 | jury | seeds | crossed |
|---|---:|---:|---:|---:|---:|---:|
| Nausea — Jean-Paul Sartre | 147 | 49.4 ± 5.6 | 39.8 | 100%/100% | 40%/100% | 30% |
| Far from the Madding Crowd — Thomas Hardy | 82 | 57.5 ± 6.4 | 48.1 | 100%/100% | 60%/100% | 70% |
| Tess of the D'Urbervilles — Thomas Hardy | 124 | 51.6 ± 8.8 | 42.0 | 100%/100% | 60%/100% | 60% |
| A Wrinkle in Time (A Wrinkle in Time Quintet, #1) — Madeleine L'Engle | 179 | 46.6 ± 6.7 | 37.1 | 100%/100% | 40%/100% | 40% |
| The Road — Cormac McCarthy | 132 | 50.5 ± 5.3 | 40.1 | 100%/100% | 40%/100% | 50% |
| Middlesex — Jeffrey Eugenides | 163 | 47.9 ± 8.7 | 38.6 | 100%/100% | 60%/100% | 60% |
| Middlemarch — George Eliot | 190 | 45.8 ± 9.3 | 35.5 | 100%/100% | 60%/100% | 70% |
| The Phantom of the Opera — Gaston Leroux | 195 | 45.6 ± 11.5 | 36.8 | 50%/100% | 40%/100% | 20% |
| Fight Club — Chuck Palahniuk | 164 | 47.8 ± 5.3 | 38.3 | 100%/100% | 20%/100% | 20% |
| Sons and Lovers — D.H. Lawrence | 191 | 45.7 ± 6.5 | 36.3 | 100%/100% | 40%/100% | 40% |
| The God of Small Things — Arundhati Roy | 176 | 46.7 ± 7.7 | 37.4 | 100%/100% | 60%/100% | 60% |
| The Awakening — Kate Chopin | 137 | 50.3 ± 6.1 | 40.7 | 100%/100% | 40%/100% | 50% |
| Black Beauty — Anna Sewell | 166 | 47.6 ± 9.1 | 38.7 | 100%/100% | 20%/100% | 20% |
| The Metamorphosis — Franz Kafka | 168 | 47.4 ± 7.1 | 37.1 | 50%/100% | 40%/100% | 30% |
| A Tale of Two Cities — Charles Dickens | 182 | 46.3 ± 6.8 | 36.4 | 100%/100% | 20%/100% | 20% |
| Ivanhoe — Walter Scott | 167 | 47.5 ± 7.8 | 38.3 | 100%/100% | 20%/100% | 20% |
| Treasure Island — Robert Louis Stevenson | 171 | 46.9 ± 5.8 | 37.9 | 100%/100% | 60%/100% | 60% |
| The Stranger — Albert Camus | 198 | 45.3 ± 6.5 | 35.0 | 50%/100% | 60%/100% | 40% |
| Catch-22 (Catch-22, #1) — Joseph Heller | 136 | 50.3 ± 8.5 | 40.8 | 100%/100% | 60%/100% | 60% |
| Silas Marner — George Eliot | 192 | 45.7 ± 6.7 | 36.3 | 100%/100% | 60%/100% | 50% |
| Siddhartha — Hermann Hesse | 151 | 49.2 ± 6.6 | 40.2 | 100%/100% | 20%/100% | 40% |
| Hard Times — Charles Dickens | 199 | 45.0 ± 7.7 | 35.9 | 50%/100% | 20%/100% | 10% |
| Norwegian Wood — Haruki Murakami | 165 | 47.6 ± 5.2 | 38.0 | 50%/100% | 60%/100% | 30% |
| A Farewell to Arms — Ernest Hemingway | 196 | 45.6 ± 4.4 | 36.0 | 100%/100% | 40%/100% | 50% |
| Slaughterhouse-Five — Kurt Vonnegut Jr. | 173 | 46.8 ± 6.8 | 36.8 | 100%/100% | 60%/100% | 60% |
| The House of the Spirits — Isabel Allende | 194 | 45.7 ± 6.1 | 36.5 | 50%/100% | 60%/100% | 40% |

## Recommendation

Use the cumulative survivors as the strongest current tier, while retaining all axis rates rather than converting survival into a new opaque score. Replace the single pair sample with repeated-seed aggregation before product use. Next calibrate ±u with user-block resampling. Keep the generic-only jury as an adversarial audit rather than part of the literary estimand: removing all author/series/year behavior destroys the jury reconstruction instead of providing a nearby specification.

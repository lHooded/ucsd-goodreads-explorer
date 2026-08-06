# Joint consensus multiverse: jury, pair definition, and self-selection

## Why combine the axes

A book can survive jury changes and pair-definition changes separately yet fail when both move together, especially after allowing enthusiast self-selection. This pilot therefore reports interpretable one-factor trajectories and a compact crossed grid.

## Design

- Jury sizes: [3286, 4929, 7500] from the same behavioral score.
- Pair definitions: ['5★ versus ≤3★', '5★ versus ≤2★', '≥4★ versus ≤2★'].
- The ≤2★ variants use proportionally lower evidence floors (2 readers/community and 20 globally versus 3/30) because those outcomes are intrinsically sparser. Coverage remains a separate reported axis.
- Selection bounds Γ: [1.0, 1.25, 1.5, 2.0, 3.0]; Γ=1 is no unmeasured selection, while larger Γ allows positive-outcome readers to be more likely to become observed raters.
- Full crossed universes: **45**; fixed community partitions: **9**.
- Distributed eligibility retains the earlier saturating 50% community-coverage gate.

## One-factor trajectories

| universe | rankable | J@50 | J@200 | RBO |
|---|---:|---:|---:|---:|
| strict_3286__five_vs_le3__gamma1p0 | 204 | 0.408 | 0.413 | 0.560 |
| central_4929__five_vs_le3__gamma1p0 | 353 | 1.000 | 1.000 | 1.000 |
| central_4929__five_vs_le3__gamma1p25 | 353 | 0.961 | 0.990 | 0.983 |
| central_4929__five_vs_le3__gamma1p5 | 353 | 0.961 | 0.980 | 0.966 |
| central_4929__five_vs_le3__gamma2p0 | 353 | 0.887 | 0.942 | 0.950 |
| central_4929__five_vs_le3__gamma3p0 | 353 | 0.852 | 0.914 | 0.921 |
| broad_7500__five_vs_le3__gamma1p0 | 527 | 0.493 | 0.481 | 0.624 |
| central_4929__five_vs_le2__gamma1p0 | 386 | 0.408 | 0.538 | 0.506 |
| central_4929__ge4_vs_le2__gamma1p0 | 391 | 0.282 | 0.476 | 0.347 |

## Crossed stability

Across 44 non-baseline universes, mean/worst J@50 is **0.382/0.149**, mean/worst J@200 is **0.485/0.361**, and mean RBO is **0.495**.

## Data-informed Γ calibration by pseudo-obscuring

Broadly observed books were made artificially obscure by retaining only readers nearest the book's observed-reader binary co-reading centroid. Selection uses outcome-blind exposure affinity—the embedding never sees rating values. Γ is the resulting positive-odds inflation relative to the full observed readership.

| readers retained | books | subset higher | mean esteem inflation | Γ q50 | Γ q75 | Γ q90 | raw MAE | corrected MAE |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 25% | 90 | 67% | 3.2 pp | 1.21 | 1.52 | 2.04 | 0.064 | 0.060 |
| 50% | 90 | 63% | 1.2 pp | 1.10 | 1.25 | 1.40 | 0.034 | 0.033 |
| 75% | 90 | 63% | 0.5 pp | 1.05 | 1.13 | 1.18 | 0.022 | 0.021 |

This calibrates plausible sensitivity scenarios, not the actual Γ of a rare book. The broad comparison group is still selected, and the binary embedding includes the fact of the target interaction; treat the estimates as lower-resolution bounds.

## Jointly robust provisional tier

Central top-200 books with score≥50, top-200 survival in at least two-thirds of jury variants, pair variants, and all crossed universes, and a Γ=1.5 conservative score still at least 50.

| book | base | score ± u | Γ floor | jury top200/evid | pair top200/evid | crossed top200 |
|---|---:|---:|---:|---:|---:|---:|
| The Brothers Karamazov — Fyodor Dostoyevsky | 1 | 82.2 ± 3.1 | >3 | 100%/100% | 100%/100% | 91% |
| Hamlet — William Shakespeare | 2 | 76.9 ± 4.0 | >3 | 100%/100% | 100%/100% | 100% |
| The Magic Mountain — Thomas Mann | 3 | 75.6 ± 6.7 | >3 | 100%/100% | 100%/100% | 89% |
| Shakespeare's Sonnets — William Shakespeare | 4 | 75.1 ± 5.3 | >3 | 100%/100% | 100%/100% | 89% |
| Stoner — John  Williams | 5 | 74.5 ± 5.9 | >3 | 67%/67% | 67%/67% | 67% |
| Notes from Underground — Fyodor Dostoyevsky | 6 | 73.0 ± 6.0 | 3.0 | 67%/67% | 67%/67% | 67% |
| Invisible Man — Ralph Ellison | 7 | 71.7 ± 5.7 | 3.0 | 100%/100% | 100%/100% | 89% |
| Journey to the End of the Night — Louis-Ferdinand Celine | 8 | 71.6 ± 6.5 | 3.0 | 100%/100% | 67%/100% | 67% |
| Les Fleurs du Mal — Charles Baudelaire | 9 | 71.3 ± 5.1 | 3.0 | 100%/100% | 100%/100% | 100% |
| Songs of Innocence and of Experience — William Blake | 10 | 71.3 ± 6.3 | 3.0 | 67%/67% | 100%/100% | 78% |
| Faust: First Part — Johann Wolfgang von Goethe | 11 | 71.3 ± 5.7 | 3.0 | 100%/100% | 100%/100% | 100% |
| Macbeth — William Shakespeare | 13 | 70.7 ± 5.5 | 3.0 | 100%/100% | 100%/100% | 100% |
| The Rime of the Ancient Mariner — Samuel Taylor Coleridge | 15 | 70.5 ± 6.3 | 3.0 | 67%/67% | 100%/100% | 78% |
| Les Misérables — Victor Hugo | 16 | 70.3 ± 4.6 | 3.0 | 100%/100% | 100%/100% | 100% |
| Inferno (The Divine Comedy #1) — Dante Alighieri | 17 | 70.3 ± 4.7 | 3.0 | 100%/100% | 100%/100% | 100% |
| Metamorphoses — Ovid | 18 | 70.1 ± 5.7 | 3.0 | 100%/100% | 100%/100% | 80% |
| The Waves — Virginia Woolf | 19 | 70.0 ± 6.9 | 3.0 | 67%/67% | 67%/67% | 67% |
| Hunger — Knut Hamsun | 21 | 68.7 ± 7.5 | 3.0 | 100%/100% | 100%/100% | 89% |
| Infinite Jest — David Foster Wallace | 22 | 68.5 ± 5.9 | 3.0 | 67%/67% | 100%/100% | 67% |
| The Adventures of Sherlock Holmes — Arthur Conan Doyle | 23 | 68.1 ± 5.7 | 3.0 | 100%/100% | 100%/100% | 100% |
| Leaves of Grass — Walt Whitman | 25 | 67.3 ± 5.9 | 3.0 | 100%/100% | 100%/100% | 89% |
| Ariel — Sylvia Plath | 26 | 66.3 ± 7.1 | 3.0 | 67%/67% | 100%/100% | 67% |
| Dead Souls — Nikolai Gogol | 27 | 66.1 ± 6.5 | 3.0 | 100%/100% | 100%/100% | 100% |
| The Death of Ivan Ilych — Leo Tolstoy | 29 | 65.5 ± 4.8 | 2.0 | 100%/100% | 100%/100% | 89% |
| East of Eden — John Steinbeck | 31 | 65.3 ± 5.6 | 3.0 | 100%/100% | 100%/100% | 100% |
| War and Peace — Leo Tolstoy | 32 | 65.3 ± 5.7 | 3.0 | 100%/100% | 100%/100% | 98% |
| Bartleby the Scrivener — Herman Melville | 34 | 65.0 ± 7.4 | 2.0 | 67%/67% | 100%/100% | 67% |
| King Lear — William Shakespeare | 35 | 64.1 ± 5.9 | 2.0 | 100%/100% | 100%/100% | 100% |
| The Tin Drum — Gunter Grass | 38 | 63.5 ± 6.2 | 2.0 | 67%/67% | 100%/100% | 73% |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 40 | 63.2 ± 5.8 | 2.0 | 67%/67% | 100%/100% | 67% |
| The Idiot — Fyodor Dostoyevsky | 41 | 63.2 ± 8.0 | 2.0 | 100%/100% | 100%/100% | 100% |
| Medea — Euripides | 42 | 63.1 ± 6.0 | 2.0 | 100%/100% | 100%/100% | 78% |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 43 | 63.1 ± 6.8 | 2.0 | 100%/100% | 100%/100% | 100% |
| As I Lay Dying — William Faulkner | 44 | 63.0 ± 5.9 | 2.0 | 100%/100% | 100%/100% | 76% |
| The Master and Margarita — Mikhail Bulgakov | 45 | 62.7 ± 7.2 | 2.0 | 100%/100% | 100%/100% | 89% |

## Selection-sensitive central books

The lower-tail consensus score falls below 50 by Γ≤1.5. This is a sensitivity statement, not proof that selection of that strength exists.

| book | base | score ± u | Γ floor | jury top200/evid | pair top200/evid | crossed top200 |
|---|---:|---:|---:|---:|---:|---:|
| Franny and Zooey — J.D. Salinger | 99 | 55.1 ± 6.1 | 1.25 | 67%/67% | 67%/100% | 56% |
| The Age of Innocence — Edith Wharton | 101 | 54.9 ± 7.4 | 1.25 | 33%/67% | 100%/100% | 44% |
| Gravity's Rainbow — Thomas Pynchon | 102 | 54.7 ± 12.3 | 1.25 | 67%/67% | 67%/100% | 31% |
| One Day in the Life of Ivan Denisovich — Aleksandr Solzhenitsyn | 103 | 54.6 ± 5.9 | 1.25 | 100%/100% | 100%/100% | 89% |
| Oedipus Rex  (The Theban Plays, #1) — Sophocles | 104 | 54.5 ± 7.3 | 1.25 | 100%/100% | 100%/100% | 100% |
| The Wind-Up Bird Chronicle — Haruki Murakami | 105 | 54.4 ± 8.5 | 1.25 | 67%/67% | 100%/100% | 73% |
| The Hunchback of Notre-Dame — Victor Hugo | 107 | 54.3 ± 8.1 | 1.25 | 100%/100% | 100%/100% | 100% |
| Pygmalion — George Bernard Shaw | 108 | 54.2 ± 6.0 | 1.25 | 100%/100% | 67%/67% | 67% |
| As You Like It — William Shakespeare | 109 | 54.2 ± 6.2 | 1.25 | 100%/100% | 100%/100% | 84% |
| Rosencrantz and Guildenstern Are Dead — Tom Stoppard | 110 | 53.9 ± 6.9 | 1.25 | 67%/67% | 67%/67% | 56% |
| Jude the Obscure — Thomas Hardy | 111 | 53.9 ± 10.2 | 1.25 | 67%/67% | 67%/100% | 33% |
| The Magus — John Fowles | 112 | 53.7 ± 6.8 | 1.25 | 67%/67% | 67%/100% | 33% |
| Mrs. Dalloway — Virginia Woolf | 113 | 53.5 ± 5.7 | 1.25 | 100%/100% | 100%/100% | 96% |
| The Murder of Roger Ackroyd (Hercule Poirot, #4) — Agatha Christie | 114 | 53.5 ± 8.3 | 1.25 | 67%/67% | 33%/33% | 33% |
| Dune (Dune Chronicles #1) — Frank Herbert | 115 | 53.4 ± 5.1 | 1.25 | 100%/100% | 67%/100% | 67% |
| The Red and the Black — Stendhal | 116 | 53.1 ± 6.0 | 1.25 | 67%/100% | 100%/100% | 67% |
| The Color Purple — Alice Walker | 117 | 53.0 ± 7.0 | 1.25 | 67%/67% | 100%/100% | 64% |
| A Confederacy of Dunces — John Kennedy Toole | 118 | 52.4 ± 6.4 | 1.25 | 100%/100% | 100%/100% | 69% |
| Their Eyes Were Watching God — Zora Neale Hurston | 119 | 52.1 ± 6.7 | 1.25 | 67%/67% | 100%/100% | 58% |
| Oblomov — Ivan Goncharov | 120 | 52.1 ± 7.7 | 1.25 | 33%/67% | 67%/67% | 44% |
| The Satanic Verses — Salman Rushdie | 121 | 52.0 ± 6.9 | 1.25 | 33%/67% | 33%/67% | 16% |
| The Three Musketeers (The D'Artagnan Romances, #1) — Alexandre Dumas | 122 | 51.8 ± 8.7 | 1.25 | 67%/100% | 100%/100% | 67% |
| Kim — Rudyard Kipling | 123 | 51.8 ± 6.9 | 1.25 | 33%/67% | 67%/67% | 33% |
| Tess of the D'Urbervilles — Thomas Hardy | 124 | 51.6 ± 8.8 | 1.25 | 67%/100% | 67%/100% | 56% |
| Fear and Loathing in Las Vegas — Hunter S. Thompson | 125 | 51.3 ± 6.2 | 1.25 | 67%/100% | 100%/100% | 80% |
| The Sorrows of Young Werther — Johann Wolfgang von Goethe | 126 | 51.3 ± 5.1 | 1.25 | 100%/100% | 67%/100% | 67% |
| Julius Caesar — William Shakespeare | 127 | 51.2 ± 6.9 | 1.25 | 67%/100% | 100%/100% | 89% |
| To the Lighthouse — Virginia Woolf | 128 | 51.2 ± 8.9 | 1.25 | 100%/100% | 67%/100% | 76% |
| The Heart is a Lonely Hunter — Carson McCullers | 129 | 51.1 ± 7.0 | 1.25 | 67%/67% | 67%/67% | 56% |
| Peter Pan — J.M. Barrie | 130 | 51.0 ± 6.5 | 1.25 | 67%/67% | 100%/100% | 78% |

## Jury-sensitive central books

None among books rankable under all three jury sizes. Observed jury-size failures were evidence/coverage failures rather than top-200 preference shifts.

## Jury-evidence-sensitive central books

| book | base | score ± u | Γ floor | jury top200/evid | pair top200/evid | crossed top200 |
|---|---:|---:|---:|---:|---:|---:|
| Notes from Underground — Fyodor Dostoyevsky | 6 | 73.0 ± 6.0 | 3.0 | 67%/67% | 67%/67% | 67% |
| Stoner — John  Williams | 5 | 74.5 ± 5.9 | >3 | 67%/67% | 67%/67% | 67% |
| Infinite Jest — David Foster Wallace | 22 | 68.5 ± 5.9 | 3.0 | 67%/67% | 100%/100% | 67% |
| Songs of Innocence and of Experience — William Blake | 10 | 71.3 ± 6.3 | 3.0 | 67%/67% | 100%/100% | 78% |
| The Waves — Virginia Woolf | 19 | 70.0 ± 6.9 | 3.0 | 67%/67% | 67%/67% | 67% |
| The Arabian Nights — Anonymous | 12 | 71.1 ± 6.7 | 3.0 | 67%/67% | 67%/67% | 56% |
| The Overcoat — Nikolai Gogol | 14 | 70.7 ± 6.9 | 3.0 | 67%/67% | 67%/67% | 56% |
| The Rime of the Ancient Mariner — Samuel Taylor Coleridge | 15 | 70.5 ± 6.3 | 3.0 | 67%/67% | 100%/100% | 78% |
| Demons — Fyodor Dostoyevsky | 20 | 69.3 ± 9.4 | 3.0 | 67%/67% | 67%/67% | 42% |
| Bartleby the Scrivener — Herman Melville | 34 | 65.0 ± 7.4 | 2.0 | 67%/67% | 100%/100% | 67% |
| Pedro Páramo — Juan Rulfo | 24 | 67.7 ± 6.3 | 3.0 | 67%/67% | 67%/67% | 56% |
| The Tin Drum — Gunter Grass | 38 | 63.5 ± 6.2 | 2.0 | 67%/67% | 100%/100% | 73% |
| Ariel — Sylvia Plath | 26 | 66.3 ± 7.1 | 3.0 | 67%/67% | 100%/100% | 67% |
| Midnight's Children — Salman Rushdie | 33 | 65.2 ± 5.9 | 2.0 | 67%/67% | 67%/100% | 56% |
| Quo Vadis — Henryk Sienkiewicz | 28 | 65.8 ± 7.4 | 2.0 | 67%/67% | 33%/33% | 22% |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 40 | 63.2 ± 5.8 | 2.0 | 67%/67% | 100%/100% | 67% |
| The Seagull — Anton Chekhov | 30 | 65.5 ± 7.0 | 2.0 | 67%/67% | 33%/33% | 22% |
| Heart of a Dog — Mikhail Bulgakov | 36 | 64.0 ± 6.7 | 2.0 | 67%/67% | 33%/33% | 33% |
| Of Human Bondage — W. Somerset Maugham | 57 | 61.2 ± 6.7 | 2.0 | 67%/67% | 33%/33% | 44% |
| Doctor Zhivago — Boris Pasternak | 39 | 63.4 ± 6.3 | 2.0 | 67%/67% | 100%/100% | 44% |
| Faust — Johann Wolfgang von Goethe | 50 | 62.0 ± 6.8 | 2.0 | 67%/67% | 33%/33% | 44% |
| The Fall — Albert Camus | 53 | 61.7 ± 5.9 | 2.0 | 67%/67% | 100%/100% | 78% |
| Native Son — Richard Wright | 78 | 58.0 ± 12.8 | 2.0 | 67%/67% | 67%/67% | 44% |
| Blindness — Jose Saramago | 56 | 61.4 ± 7.7 | 2.0 | 67%/67% | 100%/100% | 78% |
| The Waste Land — T.S. Eliot | 74 | 58.3 ± 5.6 | 1.5 | 67%/67% | 100%/100% | 78% |
| Richard III — William Shakespeare | 61 | 60.5 ± 8.8 | 2.0 | 67%/67% | 67%/67% | 67% |
| Cyrano de Bergerac — Edmond Rostand | 59 | 61.0 ± 7.6 | 2.0 | 67%/67% | 33%/33% | 33% |
| Narcissus and Goldmund — Hermann Hesse | 60 | 60.8 ± 7.1 | 2.0 | 67%/67% | 100%/100% | 78% |
| The Woman in White — Wilkie Collins | 62 | 60.4 ± 6.4 | 2.0 | 67%/67% | 67%/67% | 56% |
| My Ántonia — Willa Cather | 64 | 60.2 ± 8.7 | 2.0 | 67%/67% | 67%/67% | 36% |

## Pair-definition-sensitive central books

| book | base | score ± u | Γ floor | jury top200/evid | pair top200/evid | crossed top200 |
|---|---:|---:|---:|---:|---:|---:|
| The Prophet — Kahlil Gibran | 81 | 57.5 ± 6.2 | 1.5 | 67%/100% | 33%/100% | 53% |
| Fight Club — Chuck Palahniuk | 164 | 47.8 ± 5.3 | 1.0 | 67%/100% | 33%/100% | 38% |
| Foucault's Pendulum — Umberto Eco | 95 | 55.5 ± 6.5 | 1.5 | 67%/100% | 33%/100% | 27% |
| The Road — Cormac McCarthy | 139 | 50.2 ± 5.6 | 1.25 | 67%/100% | 33%/100% | 44% |
| Norwegian Wood — Haruki Murakami | 165 | 47.6 ± 5.2 | 1.0 | 67%/100% | 33%/100% | 33% |
| The Phantom of the Opera — Gaston Leroux | 195 | 45.6 ± 11.5 | 1.0 | 33%/67% | 33%/100% | 11% |
| Slaughterhouse-Five — Kurt Vonnegut Jr. | 171 | 47.0 ± 6.8 | 1.0 | 67%/100% | 33%/100% | 42% |
| The God of Small Things — Arundhati Roy | 175 | 46.7 ± 7.7 | 1.0 | 100%/100% | 33%/100% | 49% |
| The Awakening — Kate Chopin | 135 | 50.3 ± 6.1 | 1.25 | 33%/67% | 33%/100% | 22% |
| The Poisonwood Bible — Barbara Kingsolver | 169 | 47.1 ± 8.2 | 1.0 | 67%/100% | 33%/100% | 22% |
| The House of the Spirits — Isabel Allende | 194 | 45.7 ± 6.1 | 1.0 | 67%/100% | 33%/100% | 33% |
| Ivanhoe — Walter Scott | 168 | 47.5 ± 7.8 | 1.0 | 67%/100% | 33%/100% | 44% |
| The Grapes of Wrath — John Steinbeck | 172 | 46.9 ± 6.1 | 1.0 | 67%/100% | 33%/100% | 53% |
| Middlesex — Jeffrey Eugenides | 163 | 47.9 ± 8.7 | 1.0 | 67%/67% | 33%/100% | 53% |
| The Handmaid's Tale — Margaret Atwood | 155 | 48.8 ± 6.7 | 1.0 | 67%/100% | 33%/100% | 49% |
| Silas Marner — George Eliot | 192 | 45.7 ± 6.7 | 1.0 | 33%/67% | 33%/100% | 22% |

## Pair-evidence-sensitive central books

| book | base | score ± u | Γ floor | jury top200/evid | pair top200/evid | crossed top200 |
|---|---:|---:|---:|---:|---:|---:|
| Quo Vadis — Henryk Sienkiewicz | 28 | 65.8 ± 7.4 | 2.0 | 67%/67% | 33%/33% | 22% |
| The Seagull — Anton Chekhov | 30 | 65.5 ± 7.0 | 2.0 | 67%/67% | 33%/33% | 22% |
| Heart of a Dog — Mikhail Bulgakov | 36 | 64.0 ± 6.7 | 2.0 | 67%/67% | 33%/33% | 33% |
| Faust — Johann Wolfgang von Goethe | 50 | 62.0 ± 6.8 | 2.0 | 67%/67% | 33%/33% | 44% |
| Of Human Bondage — W. Somerset Maugham | 57 | 61.2 ± 6.7 | 2.0 | 67%/67% | 33%/33% | 44% |
| Cyrano de Bergerac — Edmond Rostand | 59 | 61.0 ± 7.6 | 2.0 | 67%/67% | 33%/33% | 33% |
| The Raven — Edgar Allan Poe | 73 | 58.6 ± 7.8 | 1.5 | 67%/67% | 33%/33% | 33% |
| Howards End — E.M. Forster | 79 | 57.9 ± 6.7 | 1.5 | 67%/67% | 33%/33% | 33% |
| The House of Mirth — Edith Wharton | 89 | 56.6 ± 9.7 | 1.5 | 67%/67% | 33%/33% | 33% |
| Franz Kafka's The Castle — David Fishelson | 90 | 56.4 ± 10.0 | 1.5 | 67%/67% | 33%/33% | 44% |
| The Sign of Four — Arthur Conan Doyle | 93 | 55.8 ± 10.1 | 1.5 | 67%/100% | 33%/33% | 22% |
| The Murder of Roger Ackroyd (Hercule Poirot, #4) — Agatha Christie | 114 | 53.5 ± 8.3 | 1.25 | 67%/67% | 33%/33% | 33% |
| The Importance of Being Earnest and Other Plays — Oscar Wilde | 179 | 46.5 ± 13.3 | 1.0 | 33%/67% | 33%/33% | 36% |
| A Christmas Carol, The Chimes and The Cricket on the Hearth — Charles Dickens | 184 | 46.3 ± 9.6 | 1.0 | 67%/67% | 33%/33% | 22% |
| Of Love and Other Demons — Gabriel Garcia Marquez | 197 | 45.5 ± 7.3 | 1.0 | 33%/67% | 33%/33% | 7% |
| Stoner — John  Williams | 5 | 74.5 ± 5.9 | >3 | 67%/67% | 67%/67% | 67% |
| Notes from Underground — Fyodor Dostoyevsky | 6 | 73.0 ± 6.0 | 3.0 | 67%/67% | 67%/67% | 67% |
| The Arabian Nights — Anonymous | 12 | 71.1 ± 6.7 | 3.0 | 67%/67% | 67%/67% | 56% |
| The Overcoat — Nikolai Gogol | 14 | 70.7 ± 6.9 | 3.0 | 67%/67% | 67%/67% | 56% |
| The Waves — Virginia Woolf | 19 | 70.0 ± 6.9 | 3.0 | 67%/67% | 67%/67% | 67% |
| Demons — Fyodor Dostoyevsky | 20 | 69.3 ± 9.4 | 3.0 | 67%/67% | 67%/67% | 42% |
| Pedro Páramo — Juan Rulfo | 24 | 67.7 ± 6.3 | 3.0 | 67%/67% | 67%/67% | 56% |
| Richard III — William Shakespeare | 61 | 60.5 ± 8.8 | 2.0 | 67%/67% | 67%/67% | 67% |
| The Mayor of Casterbridge — Thomas Hardy | 140 | 49.9 ± 6.0 | 1.0 | 67%/100% | 67%/67% | 44% |
| A Hero of Our Time — Mikhail Lermontov | 84 | 57.4 ± 5.9 | 1.5 | 100%/100% | 67%/67% | 67% |
| The Heart is a Lonely Hunter — Carson McCullers | 129 | 51.1 ± 7.0 | 1.25 | 67%/67% | 67%/67% | 56% |
| Rosencrantz and Guildenstern Are Dead — Tom Stoppard | 110 | 53.9 ± 6.9 | 1.25 | 67%/67% | 67%/67% | 56% |
| Pygmalion — George Bernard Shaw | 108 | 54.2 ± 6.0 | 1.25 | 100%/100% | 67%/67% | 67% |
| Death in Venice — Thomas Mann | 158 | 48.4 ± 8.3 | 1.0 | 67%/67% | 67%/67% | 40% |
| Who's Afraid of Virginia Woolf? — Edward Albee | 65 | 60.1 ± 8.3 | 2.0 | 33%/67% | 67%/67% | 33% |

## Interpretation

- Γ trajectories bound unmeasured enthusiast selection; pseudo-obscuring provides a rough empirical scale, not a book-specific estimate of actual selection strength.
- `±u` remains sampling/partition uncertainty. Γ sensitivity is systematic bias and must remain a separate field or trajectory.
- Jury variants currently change strictness along the chosen rich-behavior score. Feature-family and soft-weight juries remain future axes.
- Pair definitions test rating-threshold semantics, not every possible pair sampler. Repeated sampling seeds remain a useful later variance check.
- A book missing from a strict universe because evidence falls below the coverage gate is evidence-sensitive, not necessarily disliked.

## Recommendation

Treat the jointly robust books as the current strongest candidates, not a locked canon. Next cross-fit a target-excluded exposure propensity model to validate the pseudo-obscuring Γ scale, then add behavioral feature-family and pair-sampling-seed trajectories.

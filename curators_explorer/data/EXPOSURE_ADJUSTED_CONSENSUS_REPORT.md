# Exposure-adjusted distributed literary consensus pilot

## What changed

The earlier pilot mixed taste with exposure: rare books often vanished from a community ranking because they lacked enough readers. This revision estimates esteem conditional on observed readership and keeps exposure breadth separate.

- Every juror contributes balanced sampled 5★ and ≤3★ observations.
- Reader communities are equal-weighted; unobserved communities are unknown, not negative.
- Evidence is capped at 30 readers per book/community in the central specification.
- Distributed-rank eligibility requires at least 50% observed community coverage. This is a pass/fail evidence condition, never a score bonus.
- The score is the estimated 10th percentile of preference in a new observed community: mean conditional esteem minus 1.282 × noise-corrected heterogeneity.
- Sampling and partition sensitivity are reported separately as the provisional ±u.

## Data and specification multiverse

- Jury: **4,929**; broad clustering pool: **20,000**.
- Balanced vote users: **4,822**; user-book votes: **97,602**.
- Community partitions: **9**; exposure/estimation specifications: **9**.

## Residual popularity audit

Popularity is not expected to have literally zero association with canonical esteem. The important design constraint is that readership is absent from the point-score formula and stops reducing uncertainty after the evidence cap.
A large negative correlation is also a warning: it can reflect genuine jury taste, but also self-selection whereby obscure books are rated mainly by enthusiasts. This dataset cannot identify those explanations without an exposure model or additional interaction data.

| relationship | n | Spearman ρ |
|---|---:|---:|
| score vs catalog readership, all rankable | 353 | -0.517 |
| score vs catalog readership, central top 200 | 200 | -0.326 |
| uncertainty vs catalog readership | 353 | -0.090 |
| exposure coverage vs catalog readership | 353 | 0.521 |
| previous pilot: community-top200 vs catalog readership | 200 | 0.830 |

## Specification stability

Each row changes one evidence rule from the central specification.

| specification | rankable | J@50 | J@200 | RBO |
|---|---:|---:|---:|---:|
| central | 353 | 1.000 | 1.000 | 1.000 |
| community_min_2 | 401 | 0.695 | 0.709 | 0.797 |
| community_min_5 | 184 | 0.316 | 0.362 | 0.467 |
| evidence_cap_15 | 353 | 0.887 | 0.970 | 0.929 |
| evidence_cap_60 | 353 | 0.923 | 0.980 | 0.983 |
| prior_strength_2 | 353 | 0.852 | 0.932 | 0.903 |
| prior_strength_8 | 353 | 0.852 | 0.887 | 0.893 |
| global_min_20 | 370 | 0.961 | 0.905 | 0.985 |
| global_min_50 | 214 | 0.471 | 0.434 | 0.699 |

## Provisional robust distributed tier

Central top-200 books with a lower-tail score ≥50 that remain top-200 in at least 80% of evidence specifications, with noise-corrected heterogeneity ≤0.08 and provisional uncertainty ≤6 score points. These are audit thresholds, not a claim of ground truth.

| book | rank | score ± u | esteem | heterog. | coverage | jury votes | spec top200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| The Brothers Karamazov — Fyodor Dostoyevsky | 1 | 82.2 ± 3.1 | 0.824 | 0.002 | 99% | 390 | 100% |
| Hamlet — William Shakespeare | 2 | 76.9 ± 4.0 | 0.843 | 0.058 | 100% | 623 | 100% |
| Shakespeare's Sonnets — William Shakespeare | 4 | 75.1 ± 5.3 | 0.751 | 0.000 | 70% | 60 | 89% |
| Invisible Man — Ralph Ellison | 7 | 71.7 ± 5.7 | 0.717 | 0.000 | 70% | 65 | 89% |
| Les Fleurs du Mal — Charles Baudelaire | 9 | 71.3 ± 5.1 | 0.717 | 0.003 | 79% | 63 | 100% |
| Faust: First Part — Johann Wolfgang von Goethe | 11 | 71.3 ± 5.7 | 0.728 | 0.012 | 79% | 74 | 89% |
| Macbeth — William Shakespeare | 13 | 70.7 ± 5.5 | 0.753 | 0.036 | 98% | 323 | 100% |
| Les Misérables — Victor Hugo | 16 | 70.3 ± 4.6 | 0.765 | 0.048 | 99% | 287 | 100% |
| Inferno (The Divine Comedy #1) — Dante Alighieri | 17 | 70.3 ± 4.7 | 0.703 | 0.000 | 79% | 85 | 100% |
| Metamorphoses — Ovid | 18 | 70.1 ± 5.7 | 0.706 | 0.004 | 68% | 48 | 89% |
| Infinite Jest — David Foster Wallace | 22 | 68.5 ± 5.9 | 0.685 | 0.000 | 67% | 66 | 89% |
| The Adventures of Sherlock Holmes — Arthur Conan Doyle | 23 | 68.1 ± 5.7 | 0.726 | 0.034 | 90% | 93 | 100% |
| Leaves of Grass — Walt Whitman | 25 | 67.3 ± 5.9 | 0.685 | 0.010 | 88% | 78 | 100% |
| The Death of Ivan Ilych — Leo Tolstoy | 29 | 65.5 ± 4.8 | 0.659 | 0.003 | 82% | 111 | 100% |
| East of Eden — John Steinbeck | 31 | 65.3 ± 5.6 | 0.667 | 0.011 | 88% | 81 | 100% |
| War and Peace — Leo Tolstoy | 32 | 65.3 ± 5.7 | 0.755 | 0.080 | 99% | 222 | 100% |
| King Lear — William Shakespeare | 35 | 64.1 ± 5.9 | 0.701 | 0.047 | 97% | 163 | 100% |
| One Hundred Years of Solitude — Gabriel Garcia Marquez | 37 | 63.6 ± 5.5 | 0.715 | 0.062 | 100% | 305 | 100% |
| As I Lay Dying — William Faulkner | 44 | 63.0 ± 5.9 | 0.651 | 0.016 | 75% | 99 | 100% |
| Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 49 | 62.0 ± 5.7 | 0.670 | 0.039 | 99% | 131 | 100% |
| The Fall — Albert Camus | 53 | 61.7 ± 5.9 | 0.626 | 0.007 | 72% | 78 | 89% |
| The Name of the Rose — Umberto Eco | 55 | 61.6 ± 4.6 | 0.616 | 0.000 | 83% | 103 | 100% |
| All Quiet on the Western Front — Erich Maria Remarque | 58 | 61.1 ± 4.6 | 0.611 | 0.000 | 86% | 104 | 100% |
| The Plague — Albert Camus | 72 | 58.6 ± 5.2 | 0.600 | 0.010 | 74% | 142 | 100% |
| The Waste Land — T.S. Eliot | 74 | 58.3 ± 5.6 | 0.587 | 0.003 | 79% | 56 | 89% |
| David Copperfield — Charles Dickens | 75 | 58.3 ± 4.7 | 0.588 | 0.004 | 94% | 118 | 100% |
| Murder on the Orient Express (Hercule Poirot, #10) — Agatha Christie | 77 | 58.2 ± 5.6 | 0.586 | 0.004 | 80% | 50 | 100% |
| A Hero of Our Time — Mikhail Lermontov | 84 | 57.4 ± 5.9 | 0.578 | 0.003 | 71% | 52 | 89% |
| One Day in the Life of Ivan Denisovich — Aleksandr Solzhenitsyn | 103 | 54.6 ± 5.9 | 0.546 | 0.000 | 70% | 51 | 100% |
| Dune (Dune Chronicles #1) — Frank Herbert | 115 | 53.4 ± 5.1 | 0.534 | 0.000 | 82% | 82 | 100% |
| The Red and the Black — Stendhal | 116 | 53.1 ± 6.0 | 0.539 | 0.006 | 81% | 75 | 100% |
| The Sorrows of Young Werther — Johann Wolfgang von Goethe | 126 | 51.3 ± 5.1 | 0.513 | 0.000 | 86% | 95 | 100% |
| The Little Prince — Antoine de Saint-Exupery | 132 | 50.5 ± 5.4 | 0.563 | 0.045 | 100% | 216 | 100% |
| The Road — Cormac McCarthy | 139 | 50.2 ± 5.6 | 0.514 | 0.009 | 86% | 96 | 100% |

## Contested despite high average esteem

Central top-200 books with estimated between-community heterogeneity above 0.08.

| book | rank | score ± u | esteem | heterog. | coverage | jury votes | spec top200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Crime and Punishment — Fyodor Dostoyevsky | 54 | 61.6 ± 10.5 | 0.792 | 0.137 | 100% | 498 | 100% |
| Don Quixote — Miguel de Cervantes Saavedra | 157 | 48.4 ± 9.1 | 0.654 | 0.132 | 98% | 173 | 89% |
| The Picture of Dorian Gray — Oscar Wilde | 200 | 45.1 ± 6.2 | 0.618 | 0.130 | 100% | 253 | 56% |
| The Metamorphosis — Franz Kafka | 167 | 47.5 ± 7.0 | 0.638 | 0.127 | 100% | 327 | 89% |
| The Stranger — Albert Camus | 199 | 45.3 ± 6.5 | 0.612 | 0.125 | 99% | 316 | 56% |
| The Grapes of Wrath — John Steinbeck | 172 | 46.9 ± 6.1 | 0.625 | 0.122 | 97% | 174 | 89% |
| Steppenwolf — Hermann Hesse | 159 | 48.3 ± 7.0 | 0.634 | 0.117 | 89% | 173 | 100% |
| Great Expectations — Charles Dickens | 185 | 46.2 ± 7.8 | 0.612 | 0.117 | 97% | 213 | 78% |
| Anna Karenina — Leo Tolstoy | 85 | 57.2 ± 5.7 | 0.713 | 0.110 | 100% | 368 | 100% |
| Waiting for Godot — Samuel Beckett | 147 | 49.3 ± 8.4 | 0.632 | 0.109 | 94% | 146 | 100% |
| The Odyssey — Homer | 92 | 55.9 ± 6.8 | 0.697 | 0.108 | 100% | 234 | 100% |
| A Tale of Two Cities — Charles Dickens | 183 | 46.3 ± 6.7 | 0.601 | 0.107 | 99% | 195 | 89% |
| Gravity's Rainbow — Thomas Pynchon | 102 | 54.7 ± 12.3 | 0.682 | 0.105 | 51% | 52 | 89% |
| Dubliners — James Joyce | 173 | 46.8 ± 9.4 | 0.592 | 0.097 | 83% | 116 | 89% |
| One Flew Over the Cuckoo's Nest — Ken Kesey | 136 | 50.3 ± 6.4 | 0.622 | 0.093 | 97% | 129 | 100% |
| The Importance of Being Earnest — Oscar Wilde | 138 | 50.2 ± 8.5 | 0.619 | 0.091 | 96% | 112 | 100% |
| Anne of Green Gables (Anne of Green Gables, #1) — L.M. Montgomery | 146 | 49.4 ± 11.3 | 0.610 | 0.091 | 76% | 64 | 89% |
| The Iliad — Homer | 86 | 56.9 ± 6.5 | 0.681 | 0.087 | 100% | 168 | 100% |
| The Importance of Being Earnest and Other Plays — Oscar Wilde | 179 | 46.5 ± 13.3 | 0.574 | 0.085 | 65% | 37 | 67% |
| The Count of Monte Cristo — Alexandre Dumas | 67 | 59.9 ± 5.2 | 0.707 | 0.085 | 97% | 271 | 100% |
| Mrs. Dalloway — Virginia Woolf | 113 | 53.5 ± 5.7 | 0.644 | 0.085 | 99% | 138 | 100% |
| Middlemarch — George Eliot | 190 | 45.9 ± 9.3 | 0.566 | 0.084 | 84% | 85 | 89% |
| Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 76 | 58.3 ± 10.7 | 0.689 | 0.083 | 69% | 90 | 100% |

## Evidence/specification-sensitive central books

| book | rank | score ± u | esteem | heterog. | coverage | jury votes | spec top200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| The Phantom of the Opera — Gaston Leroux | 195 | 45.6 ± 11.5 | 0.501 | 0.035 | 73% | 42 | 33% |
| Of Love and Other Demons — Gabriel Garcia Marquez | 197 | 45.5 ± 7.3 | 0.455 | 0.000 | 56% | 31 | 33% |
| The Jungle — Upton Sinclair | 193 | 45.7 ± 12.4 | 0.544 | 0.068 | 60% | 39 | 44% |
| The Goldfinch — Donna Tartt | 198 | 45.3 ± 12.4 | 0.552 | 0.077 | 53% | 40 | 44% |
| Silas Marner — George Eliot | 192 | 45.7 ± 6.7 | 0.457 | 0.000 | 64% | 38 | 44% |
| Sons and Lovers — D.H. Lawrence | 191 | 45.7 ± 6.5 | 0.457 | 0.000 | 67% | 42 | 44% |
| A Wrinkle in Time (A Wrinkle in Time Quintet, #1) — Madeleine L'Engle | 177 | 46.6 ± 6.7 | 0.466 | 0.000 | 60% | 36 | 56% |
| The Stranger — Albert Camus | 199 | 45.3 ± 6.5 | 0.612 | 0.125 | 99% | 316 | 56% |
| The Picture of Dorian Gray — Oscar Wilde | 200 | 45.1 ± 6.2 | 0.618 | 0.130 | 100% | 253 | 56% |
| The Importance of Being Earnest and Other Plays — Oscar Wilde | 179 | 46.5 ± 13.3 | 0.574 | 0.085 | 65% | 37 | 67% |
| A Christmas Carol, The Chimes and The Cricket on the Hearth — Charles Dickens | 184 | 46.3 ± 9.6 | 0.503 | 0.031 | 56% | 34 | 67% |
| Black Beauty — Anna Sewell | 166 | 47.6 ± 9.1 | 0.499 | 0.017 | 56% | 34 | 67% |
| The Virgin Suicides — Jeffrey Eugenides | 186 | 46.1 ± 8.9 | 0.506 | 0.035 | 50% | 37 | 67% |
| Middlesex — Jeffrey Eugenides | 163 | 47.9 ± 8.7 | 0.510 | 0.025 | 86% | 47 | 67% |
| Cannery Row — John Steinbeck | 162 | 48.1 ± 7.8 | 0.491 | 0.008 | 67% | 38 | 67% |
| Lord Jim — Joseph Conrad | 141 | 49.7 ± 6.3 | 0.497 | 0.000 | 64% | 42 | 67% |
| The House of the Spirits — Isabel Allende | 194 | 45.7 ± 6.1 | 0.473 | 0.013 | 84% | 60 | 67% |
| Vanity Fair — William Makepeace Thackeray | 176 | 46.6 ± 5.8 | 0.466 | 0.000 | 76% | 59 | 67% |
| A Farewell to Arms — Ernest Hemingway | 196 | 45.6 ± 4.4 | 0.463 | 0.005 | 99% | 125 | 67% |
| Twenty Love Poems and a Song of Despair — Pablo Neruda | 83 | 57.4 ± 14.1 | 0.635 | 0.047 | 53% | 35 | 78% |
| Native Son — Richard Wright | 78 | 58.0 ± 12.8 | 0.652 | 0.056 | 53% | 31 | 78% |
| Light in August — William Faulkner | 188 | 46.1 ± 11.3 | 0.560 | 0.077 | 71% | 46 | 78% |
| We — Yevgeny Zamyatin | 148 | 49.2 ± 10.4 | 0.564 | 0.056 | 52% | 36 | 78% |
| Hopscotch — Julio Cortazar | 70 | 59.0 ± 10.3 | 0.661 | 0.055 | 54% | 38 | 78% |
| Jude the Obscure — Thomas Hardy | 111 | 53.9 ± 10.2 | 0.589 | 0.039 | 58% | 34 | 78% |
| The Sign of Four — Arthur Conan Doyle | 93 | 55.8 ± 10.1 | 0.603 | 0.035 | 66% | 42 | 78% |
| Brideshead Revisited: The Sacred and Profane Memories of Captain Charles Ryder — Evelyn Waugh | 98 | 55.3 ± 10.0 | 0.595 | 0.033 | 74% | 44 | 78% |
| Franz Kafka's The Castle — David Fishelson | 90 | 56.4 ± 10.0 | 0.592 | 0.022 | 51% | 37 | 78% |
| Bleak House — Charles Dickens | 100 | 55.1 ± 9.8 | 0.597 | 0.036 | 66% | 44 | 78% |
| The House of Mirth — Edith Wharton | 89 | 56.6 ± 9.7 | 0.610 | 0.034 | 60% | 42 | 78% |

## Underexposed candidates

Books entering a top 200 under at least one lenient evidence specification but missing the central global-reader floor. They are unresolved rather than rejected.

| book | rank | score ± u | esteem | heterog. | coverage | jury votes | spec top200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| The Nose — Nikolai Gogol | — | 57.1 ± 7.9 | 0.571 | 0.000 | 48% | 33 | 11% |
| My Name is Red — Orhan Pamuk | — | 61.3 ± 7.7 | 0.614 | 0.001 | 43% | 32 | 11% |
| North and South — Elizabeth Gaskell | — | 55.3 ± 12.3 | 0.619 | 0.051 | 43% | 32 | 11% |
| White Nights — Fyodor Dostoyevsky | — | 57.9 ± 7.1 | 0.579 | 0.000 | 48% | 54 | 11% |
| Invisible Cities — Italo Calvino | — | 59.1 ± 7.7 | 0.625 | 0.027 | 50% | 60 | 11% |
| A Little Princess — Frances Hodgson Burnett | — | 59.3 ± 7.5 | 0.593 | 0.000 | 50% | 27 | 11% |
| Zorba the Greek — Nikos Kazantzakis | — | 64.3 ± 7.4 | 0.643 | 0.000 | 45% | 32 | 11% |
| Under the Volcano — Malcolm Lowry | — | 52.5 ± 8.1 | 0.556 | 0.024 | 48% | 32 | 11% |
| Cat on a Hot Tin Roof — Tennessee Williams | — | 48.7 ± 7.7 | 0.487 | 0.000 | 54% | 29 | 11% |
| The Jungle Books — Rudyard Kipling | — | 52.1 ± 8.6 | 0.536 | 0.012 | 64% | 29 | 11% |
| Blood Meridian, or the Evening Redness in the West — Cormac McCarthy | — | 64.0 ± 10.1 | 0.665 | 0.020 | 48% | 60 | 11% |
| The Secret History — Donna Tartt | — | 43.8 ± 10.7 | 0.523 | 0.066 | 36% | 30 | 11% |
| Alice's Adventures in Wonderland — Lewis Carroll | — | 58.0 ± 7.9 | 0.580 | 0.000 | 51% | 25 | 11% |
| The Corrections — Jonathan Franzen | — | 48.8 ± 11.3 | 0.530 | 0.033 | 47% | 31 | 11% |
| The History of Tom Jones, a Foundling — Henry Fielding | — | 48.1 ± 11.1 | 0.579 | 0.076 | 47% | 34 | 11% |
| Chess Story — Stefan Zweig | — | 66.7 ± 6.7 | 0.667 | 0.000 | 49% | 34 | 11% |
| The End of the Affair — Graham Greene | — | 54.1 ± 7.8 | 0.541 | 0.000 | 47% | 30 | 11% |
| The Life and Opinions of Tristram Shandy, Gentleman — Laurence Sterne | — | 52.1 ± 15.0 | 0.631 | 0.086 | 45% | 42 | 11% |
| The Charterhouse of Parma — Stendhal | — | 53.7 ± 7.9 | 0.537 | 0.000 | 51% | 27 | 11% |
| 2666 — Roberto Bolano | — | 76.9 ± 7.0 | 0.785 | 0.013 | 43% | 40 | 11% |
| Women in Love (Brangwen Family, #2) — D.H. Lawrence | — | 48.5 ± 10.8 | 0.528 | 0.033 | 49% | 30 | 11% |
| The Tenant of Wildfell Hall — Anne Bronte | — | 46.8 ± 7.6 | 0.468 | 0.000 | 46% | 37 | 11% |
| The Book of Disquiet — Fernando Pessoa | — | 74.0 ± 7.0 | 0.740 | 0.000 | 42% | 32 | 11% |
| The Remains of the Day — Kazuo Ishiguro | — | 60.8 ± 9.5 | 0.631 | 0.018 | 41% | 37 | 11% |
| Solaris — Stanislaw Lem | — | 64.2 ± 8.1 | 0.642 | 0.000 | 50% | 28 | 11% |
| The Neverending Story — Michael Ende | — | 53.5 ± 7.3 | 0.535 | 0.000 | 56% | 25 | 11% |
| The Princess Bride — William Goldman | — | 50.6 ± 8.2 | 0.515 | 0.007 | 56% | 29 | 11% |
| Buddenbrooks: The Decline of a Family — Thomas Mann | — | 71.2 ± 8.3 | 0.720 | 0.007 | 45% | 45 | 11% |
| A Passage to India — E.M. Forster | — | 47.6 ± 7.8 | 0.476 | 0.000 | 46% | 32 | 11% |
| Rabbit, Run (Rabbit Angstrom #1) — John Updike | — | 49.0 ± 8.0 | 0.490 | 0.000 | 45% | 30 | 11% |

## Russian-author diagnostic example

This is retained only to compare with the motivating example; author nationality does not enter any score.

| book | rank | score ± u | esteem | heterog. | coverage | jury votes | spec top200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| The Brothers Karamazov — Fyodor Dostoyevsky | 1 | 82.2 ± 3.1 | 0.824 | 0.002 | 99% | 390 | 100% |
| Notes from Underground — Fyodor Dostoyevsky | 6 | 73.0 ± 6.0 | 0.730 | 0.000 | 64% | 54 | 89% |
| The Overcoat — Nikolai Gogol | 14 | 70.7 ± 6.9 | 0.713 | 0.005 | 55% | 35 | 78% |
| Demons — Fyodor Dostoyevsky | 20 | 69.3 ± 9.4 | 0.724 | 0.024 | 58% | 106 | 89% |
| Dead Souls — Nikolai Gogol | 27 | 66.1 ± 6.5 | 0.671 | 0.008 | 73% | 96 | 100% |
| The Death of Ivan Ilych — Leo Tolstoy | 29 | 65.5 ± 4.8 | 0.659 | 0.003 | 82% | 111 | 100% |
| The Seagull — Anton Chekhov | 30 | 65.5 ± 7.0 | 0.655 | 0.000 | 55% | 30 | 78% |
| War and Peace — Leo Tolstoy | 32 | 65.3 ± 5.7 | 0.755 | 0.080 | 99% | 222 | 100% |
| Heart of a Dog — Mikhail Bulgakov | 36 | 64.0 ± 6.7 | 0.640 | 0.000 | 57% | 47 | 78% |
| Doctor Zhivago — Boris Pasternak | 39 | 63.4 ± 6.3 | 0.634 | 0.000 | 71% | 46 | 78% |
| The Idiot — Fyodor Dostoyevsky | 41 | 63.2 ± 8.0 | 0.718 | 0.067 | 92% | 187 | 100% |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 43 | 63.1 ± 6.8 | 0.668 | 0.030 | 93% | 146 | 100% |
| The Master and Margarita — Mikhail Bulgakov | 45 | 62.7 ± 7.2 | 0.714 | 0.068 | 89% | 171 | 100% |
| Crime and Punishment — Fyodor Dostoyevsky | 54 | 61.6 ± 10.5 | 0.792 | 0.137 | 100% | 498 | 100% |
| Eugene Onegin — Alexander Pushkin | 68 | 59.6 ± 6.5 | 0.614 | 0.014 | 76% | 73 | 100% |
| A Hero of Our Time — Mikhail Lermontov | 84 | 57.4 ± 5.9 | 0.578 | 0.003 | 71% | 52 | 89% |
| Anna Karenina — Leo Tolstoy | 85 | 57.2 ± 5.7 | 0.713 | 0.110 | 100% | 368 | 100% |
| Fathers and Sons — Ivan Turgenev | 91 | 56.1 ± 6.1 | 0.570 | 0.007 | 82% | 90 | 100% |
| One Day in the Life of Ivan Denisovich — Aleksandr Solzhenitsyn | 103 | 54.6 ± 5.9 | 0.546 | 0.000 | 70% | 51 | 100% |
| We — Yevgeny Zamyatin | 148 | 49.2 ± 10.4 | 0.564 | 0.056 | 52% | 36 | 78% |
| The Cherry Orchard — Anton Chekhov | 152 | 49.0 ± 6.9 | 0.495 | 0.004 | 53% | 35 | 78% |
| The Gambler — Fyodor Dostoyevsky | 213 | 44.2 ± 6.0 | 0.442 | 0.000 | 64% | 60 | 22% |
| Lolita — Vladimir Nabokov | 221 | 43.3 ± 6.6 | 0.601 | 0.131 | 100% | 279 | 44% |
| The Nose — Nikolai Gogol | — | 57.1 ± 7.9 | 0.571 | 0.000 | 48% | 33 | 11% |
| White Nights — Fyodor Dostoyevsky | — | 57.9 ± 7.1 | 0.579 | 0.000 | 48% | 54 | 11% |
| The Kreutzer Sonata — Leo Tolstoy | — | 44.8 ± 7.3 | 0.448 | 0.000 | 47% | 39 | 0% |
| Pale Fire — Vladimir Nabokov | — | 42.8 ± 11.1 | 0.629 | 0.156 | 47% | 50 | 0% |
| Resurrection — Leo Tolstoy | — | 56.4 ± 14.0 | 0.634 | 0.054 | 46% | 37 | 11% |

## Limits and interpretation

- Conditional-on-rating esteem is not the same as the preference of everyone who might have been exposed. Goodreads ratings are missing-not-at-random.
- A rare book can receive a high point estimate and wide uncertainty. It cannot be called distributed until several communities provide evidence, but it is not treated as disliked merely because other communities have no observations.
- ±u is a provisional combination of within-community posterior uncertainty and partition sensitivity. The communities reuse readers, so it is not yet a calibrated frequentist confidence interval.
- The score intentionally penalizes genuine taste heterogeneity. Exposure coverage is displayed beside it rather than hidden inside it.
- The next multiverse should vary jury construction and pair definitions; this pilot only varies exposure/evidence estimation around the fixed rebuilt jury.

## Recommendation

The exposure-adjusted pilot supports a nontrivial provisional distributed tier. Proceed to jury/pair-definition trajectories, retaining conditional esteem, heterogeneity, exposure breadth, and uncertainty as separate outputs.

# Hierarchical community pooling and read-selection pilot

## Design

Exact expected-inclusion positive/negative mass is retained. Every book×community cell receives a logistic empirical-Bayes prior combining the book-wide and community-wide rate; the book-wide component is first shrunk by 50 units toward the global rate. Observed evidence is capped at 30 and updates that prior. Missing communities therefore remain uncertain predictions rather than causing a binary coverage failure. Their heterogeneity is assigned a data-estimated predictive floor learned from well-observed books. Shared book-level uncertainty is carried once rather than divided across predicted communities. The point ranking is a conservative posterior estimate: mean community esteem minus lower-tail penalties for genuine heterogeneity and shared book uncertainty.

Known-read/unrated interactions are not imputed in the central score. Separate Γ paths assign them a lower positive propensity than observed raters using capped marginal pair weights; the all-low path is an extreme bound.

- Candidate books: **1,146**; candidate states: **794,388** from **6,808** users.
- Rated candidate states: **590,232**; known-read/unrated: **11,516**.
- Central rankable: **1,143**; current hard-gate ranking: 300.
- Cross-community predictive heterogeneity floor: **4.8 score points**.

## Specification trajectories

| specification | rankable | J@50 current | J@200 current | RBO current | J@50 central | J@200 central | RBO central | pop ρ | med top200 u | med observed coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| central | 1143 | 0.639 | 0.365 | 0.680 | 1.000 | 1.000 | 1.000 | -0.311 | 7.01 | 53% |
| book_prior_20 | 1143 | 0.613 | 0.342 | 0.682 | 0.852 | 0.932 | 0.921 | -0.280 | 7.56 | 52% |
| book_prior_100 | 1143 | 0.639 | 0.375 | 0.697 | 0.961 | 0.980 | 0.943 | -0.329 | 6.56 | 53% |
| book_cap_30 | 1143 | 0.639 | 0.307 | 0.705 | 0.724 | 0.869 | 0.820 | -0.335 | 7.48 | 46% |
| book_cap_60 | 1143 | 0.724 | 0.347 | 0.762 | 0.786 | 0.951 | 0.851 | -0.323 | 7.14 | 52% |
| book_cap_120 | 1143 | 0.639 | 0.356 | 0.710 | 0.887 | 0.980 | 0.936 | -0.314 | 7.04 | 53% |
| evidence_z_0_5 | 1143 | 0.639 | 0.342 | 0.682 | 0.923 | 0.942 | 0.970 | -0.331 | 7.05 | 52% |
| evidence_z_1_282 | 1143 | 0.613 | 0.379 | 0.678 | 0.961 | 0.970 | 0.987 | -0.299 | 6.97 | 53% |
| mass_20 | 587 | 0.639 | 0.429 | 0.689 | 1.000 | 0.674 | 0.980 | -0.392 | 6.94 | 58% |
| unrated_gamma_1_5 | 1143 | 0.613 | 0.351 | 0.713 | 0.887 | 0.942 | 0.932 | -0.310 | 6.99 | 54% |
| unrated_gamma_2 | 1143 | 0.613 | 0.356 | 0.711 | 0.887 | 0.942 | 0.927 | -0.308 | 6.98 | 55% |
| unrated_all_low | 1143 | 0.695 | 0.370 | 0.683 | 0.754 | 0.878 | 0.855 | -0.296 | 6.99 | 57% |

## Known-read/unrated sensitivity

These are score changes among the central top 200, holding the observed ratings fixed.

| path | median drop | 90th-percentile drop | drop >3 | drop >5 |
|---|---:|---:|---:|---:|
| gamma_1_5 | 0.19 | 1.11 | 0 | 0 |
| gamma_2 | 0.55 | 1.66 | 2 | 0 |
| all_low | 3.07 | 6.09 | 102 | 40 |

## Central top 40

| # | book | score ±u | old # | pair mass | observed coverage | rated/read | Γ1.5 | Γ2 | all-low |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 83.4 ±3.5 | 2 | 383.2 | 100% | 97% | 82.8 | 82.2 | 75.9 |
| 2 | Hamlet — William Shakespeare | 82.8 ±3.2 | 1 | 644.0 | 100% | 99% | 82.9 | 82.9 | 82.4 |
| 3 | Crime and Punishment — Fyodor Dostoyevsky | 75.0 ±7.0 | 21 | 519.7 | 100% | 99% | 74.7 | 74.6 | 72.9 |
| 4 | Les Misérables — Victor Hugo | 74.9 ±4.5 | 9 | 296.9 | 98% | 97% | 73.0 | 72.4 | 67.8 |
| 5 | Macbeth — William Shakespeare | 74.5 ±4.1 | 6 | 304.1 | 100% | 99% | 74.1 | 73.9 | 72.7 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 73.8 ±4.2 | 8 | 177.8 | 94% | 97% | 73.3 | 72.7 | 68.2 |
| 7 | Demons — Fyodor Dostoyevsky | 73.2 ±5.1 | 4 | 100.6 | 53% | 96% | 73.8 | 73.3 | 65.2 |
| 8 | The Idiot — Fyodor Dostoyevsky | 70.7 ±6.6 | 32 | 194.9 | 94% | 97% | 69.7 | 69.2 | 65.8 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 70.6 ±5.8 | 3 | 66.7 | 65% | 97% | 69.2 | 68.8 | 64.9 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 69.8 ±6.1 | 5 | 65.7 | 72% | 98% | 69.3 | 68.9 | 65.8 |
| 11 | Paradise Lost — John Milton | 69.6 ±6.1 | 26 | 141.3 | 100% | 98% | 68.7 | 68.3 | 65.1 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 69.1 ±5.8 | 14 | 85.7 | 90% | 98% | 69.1 | 68.9 | 66.5 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 69.0 ±5.7 | 12 | 106.5 | 79% | 99% | 68.9 | 68.7 | 67.1 |
| 14 | The Divine Comedy — Dante Alighieri | 68.2 ±5.4 | 22 | 112.4 | 92% | 97% | 67.4 | 66.8 | 62.5 |
| 15 | Anna Karenina — Leo Tolstoy | 68.0 ±4.1 | 33 | 347.5 | 100% | 97% | 67.1 | 66.5 | 62.3 |
| 16 | War and Peace — Leo Tolstoy | 67.9 ±5.9 | 45 | 249.2 | 97% | 96% | 66.8 | 66.2 | 62.0 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 67.6 ±5.0 | 20 | 144.8 | 87% | 99% | 67.6 | 67.3 | 65.4 |
| 18 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 67.2 ±6.0 | 17 | 86.7 | 89% | 99% | 66.2 | 65.9 | 63.6 |
| 19 | The Magic Mountain — Thomas Mann | 67.0 ±5.6 | 16 | 81.3 | 71% | 96% | 67.1 | 66.6 | 61.2 |
| 20 | King Lear — William Shakespeare | 66.7 ±5.2 | 29 | 162.0 | 96% | 99% | 65.9 | 65.6 | 63.8 |
| 21 | Leaves of Grass — Walt Whitman | 66.2 ±5.9 | 23 | 79.3 | 89% | 98% | 65.6 | 65.1 | 61.5 |
| 22 | Faust: First Part — Johann Wolfgang von Goethe | 66.0 ±5.9 | 15 | 81.3 | 85% | 98% | 65.3 | 64.9 | 61.5 |
| 23 | Stoner — John  Williams | 65.4 ±6.8 | — | 47.5 | 51% | 97% | 65.7 | 65.3 | 62.1 |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 65.1 ±6.3 | — | 58.6 | 46% | 97% | 65.0 | 64.6 | 60.1 |
| 25 | Infinite Jest — David Foster Wallace | 64.6 ±6.3 | 18 | 64.9 | 63% | 88% | 66.3 | 65.3 | 56.8 |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 64.5 ±5.9 | 7 | 74.6 | 53% | 96% | 64.2 | 63.8 | 59.7 |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 64.1 ±6.3 | 39 | 93.2 | 77% | 92% | 63.4 | 62.2 | 51.8 |
| 28 | The Waves — Virginia Woolf | 64.1 ±6.4 | 10 | 49.8 | 54% | 95% | 63.7 | 63.0 | 57.3 |
| 29 | The Iliad — Homer | 63.6 ±7.6 | 72 | 175.2 | 100% | 98% | 62.8 | 62.5 | 60.6 |
| 30 | The Waste Land — T.S. Eliot | 63.2 ±6.5 | 24 | 59.7 | 75% | 99% | 62.0 | 61.7 | 59.4 |
| 31 | The Count of Monte Cristo — Alexandre Dumas | 63.2 ±4.7 | 54 | 280.7 | 98% | 99% | 62.1 | 61.7 | 59.2 |
| 32 | 2666 — Roberto Bolano | 63.0 ±6.8 | — | 38.4 | 25% | 90% | 63.2 | 62.4 | 54.9 |
| 33 | A Streetcar Named Desire — Tennessee Williams | 62.9 ±6.1 | 40 | 77.8 | 89% | 99% | 62.4 | 62.1 | 60.2 |
| 34 | The Book of Disquiet — Fernando Pessoa | 62.9 ±6.9 | — | 38.0 | 38% | 91% | 63.7 | 62.8 | 54.5 |
| 35 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 62.8 ±5.3 | 31 | 130.2 | 99% | 100% | 62.7 | 62.7 | 62.6 |
| 36 | Bartleby the Scrivener — Herman Melville | 62.3 ±6.6 | 11 | 48.9 | 52% | 99% | 62.7 | 62.4 | 60.0 |
| 37 | The Overcoat — Nikolai Gogol | 62.3 ±6.7 | 13 | 44.2 | 52% | 99% | 62.0 | 61.8 | 60.3 |
| 38 | Dead Souls — Nikolai Gogol | 61.6 ±6.0 | 42 | 98.6 | 82% | 97% | 60.7 | 60.1 | 55.5 |
| 39 | East of Eden — John Steinbeck | 61.5 ±6.9 | 34 | 92.9 | 92% | 99% | 61.4 | 61.1 | 59.1 |
| 40 | Hunger — Knut Hamsun | 61.4 ±6.2 | 25 | 62.9 | 58% | 99% | 61.1 | 60.8 | 58.1 |

## Interpretation limits

- This is an empirical-Bayes pilot, not a fully fitted generative multilevel model. Book-wide evidence contributes to every community prior, so uncertainty is still understated when whole communities are unobserved.
- Read-unrated Γ paths approximate the marginal pair contribution the missing event would have had. They bound rating selection among recorded readers, not unrecorded exposure.
- Removing a gate can admit weakly identified books. Pair mass, posterior uncertainty, and selection paths must remain visible; do not publish the central order alone.

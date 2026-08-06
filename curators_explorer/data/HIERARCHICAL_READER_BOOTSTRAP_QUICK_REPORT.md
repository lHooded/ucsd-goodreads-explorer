# Hierarchical reader-block bootstrap

## Result

Whole readers are Poisson-resampled while soft jury weights, community labels, and the learned jury definition remain fixed. Every draw refits book, community, and predictive-heterogeneity pooling terms before reranking.

- Mode: **quick**; replicates: **64**; runtime: **5.5s**.
- Mean Jaccard@50: **0.701** (10th percentile 0.648).
- Mean Jaccard@200: **0.731** (10th percentile 0.702).
- Median top-200 reader `u80`: **3.72** points; median bootstrap eligibility: **100%**.
- Top-200 reader uncertainty versus catalog popularity: Spearman **0.436**; versus pair mass: **0.491**.

## Evidence trajectories within the point top 200

| pair mass | books | median reader u80 | median top-200 inclusion |
|---|---:|---:|---:|
| 10–20 | 39 | 2.87 | 69% |
| 20–50 | 71 | 3.72 | 94% |
| 50–100 | 50 | 4.09 | 95% |
| 100–∞ | 40 | 4.09 | 100% |

## Point top 40

| # | book | score | analytic u | reader u80 | eligibility | top-200 rate | rank q10–q90 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 83.4 | 3.5 | 3.6 | 100% | 100% | 1–2 |
| 2 | Hamlet — William Shakespeare | 82.8 | 3.2 | 2.6 | 100% | 100% | 1–2 |
| 3 | Crime and Punishment — Fyodor Dostoyevsky | 75.0 | 7.0 | 4.0 | 100% | 100% | 3–8 |
| 4 | Les Misérables — Victor Hugo | 74.9 | 4.5 | 3.0 | 100% | 100% | 3–8 |
| 5 | Macbeth — William Shakespeare | 74.5 | 4.1 | 3.7 | 100% | 100% | 3–10 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 73.8 | 4.2 | 4.1 | 100% | 100% | 4–14 |
| 7 | Demons — Fyodor Dostoyevsky | 73.2 | 5.1 | 2.9 | 100% | 100% | 5–11 |
| 8 | The Idiot — Fyodor Dostoyevsky | 70.7 | 6.6 | 4.2 | 100% | 100% | 5–20 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 70.6 | 5.8 | 3.2 | 100% | 100% | 6–19 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 69.8 | 6.1 | 3.2 | 100% | 100% | 8–23 |
| 11 | Paradise Lost — John Milton | 69.6 | 6.1 | 5.1 | 100% | 100% | 6–29 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 69.1 | 5.8 | 3.9 | 100% | 100% | 8–29 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 69.0 | 5.7 | 2.8 | 100% | 100% | 8–20 |
| 14 | The Divine Comedy — Dante Alighieri | 68.2 | 5.4 | 4.2 | 100% | 100% | 9–27 |
| 15 | Anna Karenina — Leo Tolstoy | 68.0 | 4.1 | 3.4 | 100% | 100% | 7–24 |
| 16 | War and Peace — Leo Tolstoy | 67.9 | 5.9 | 3.5 | 100% | 100% | 8–25 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 67.6 | 5.0 | 4.0 | 100% | 100% | 13–43 |
| 18 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 67.2 | 6.0 | 3.7 | 100% | 100% | 12–37 |
| 19 | The Magic Mountain — Thomas Mann | 67.0 | 5.6 | 3.0 | 100% | 100% | 14–32 |
| 20 | King Lear — William Shakespeare | 66.7 | 5.2 | 4.6 | 100% | 100% | 11–41 |
| 21 | Leaves of Grass — Walt Whitman | 66.2 | 5.9 | 4.3 | 100% | 100% | 11–37 |
| 22 | Faust: First Part — Johann Wolfgang von Goethe | 66.0 | 5.9 | 4.4 | 100% | 100% | 12–45 |
| 23 | Stoner — John  Williams | 65.4 | 6.8 | 2.6 | 100% | 100% | 16–33 |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 65.1 | 6.3 | 3.1 | 100% | 100% | 18–43 |
| 25 | Infinite Jest — David Foster Wallace | 64.6 | 6.3 | 4.1 | 100% | 100% | 18–57 |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 64.5 | 5.9 | 3.9 | 100% | 100% | 18–52 |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 64.1 | 6.3 | 4.4 | 100% | 100% | 20–63 |
| 28 | The Waves — Virginia Woolf | 64.1 | 6.4 | 3.7 | 100% | 100% | 20–52 |
| 29 | The Iliad — Homer | 63.6 | 7.6 | 3.9 | 100% | 100% | 18–58 |
| 30 | The Waste Land — T.S. Eliot | 63.2 | 6.5 | 4.7 | 100% | 100% | 19–70 |
| 31 | The Count of Monte Cristo — Alexandre Dumas | 63.2 | 4.7 | 4.2 | 100% | 100% | 16–51 |
| 32 | 2666 — Roberto Bolano | 63.0 | 6.8 | 2.7 | 100% | 100% | 25–52 |
| 33 | A Streetcar Named Desire — Tennessee Williams | 62.9 | 6.1 | 3.8 | 100% | 100% | 23–63 |
| 34 | The Book of Disquiet — Fernando Pessoa | 62.9 | 6.9 | 2.7 | 100% | 100% | 25–48 |
| 35 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 62.8 | 5.3 | 5.4 | 100% | 100% | 14–61 |
| 36 | Bartleby the Scrivener — Herman Melville | 62.3 | 6.6 | 3.8 | 100% | 100% | 25–71 |
| 37 | The Overcoat — Nikolai Gogol | 62.3 | 6.7 | 4.3 | 100% | 98% | 22–67 |
| 38 | Dead Souls — Nikolai Gogol | 61.6 | 6.0 | 2.9 | 100% | 100% | 28–67 |
| 39 | East of Eden — John Steinbeck | 61.5 | 6.9 | 3.8 | 100% | 100% | 20–67 |
| 40 | Hunger — Knut Hamsun | 61.4 | 6.2 | 3.6 | 100% | 100% | 28–77 |

`reader u80` is half the conditional 10th–90th percentile score interval. Eligibility and inclusion are reported separately so a narrow conditional interval cannot disguise unstable evidence. This bootstrap does not refit the jury definition.

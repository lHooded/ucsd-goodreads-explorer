# Hierarchical popularity-leverage audit

## Result

Aggregate book evidence is forcibly saturated at 30, 60, and 120 effective pair votes while community-cell caps, jury weights, and conditional preference events stay fixed. This removes the principal route by which a widely read book can gain extra precision without erasing genuine conditional esteem.

- Uncapped score versus catalog readership: rho **-0.311**.
- Score versus catalog readership conditional on pair mass (partial Spearman): **-0.507**.
- Catalog readership versus effective pair mass: rho **0.552**.

| aggregate cap | J@50 | J@200 | RBO | score/catalog rho | median top200 u |
|---:|---:|---:|---:|---:|---:|
| 30 | 0.724 | 0.869 | 0.820 | -0.335 | 7.48 |
| 60 | 0.786 | 0.951 | 0.851 | -0.323 | 7.14 |
| 120 | 0.887 | 0.980 | 0.936 | -0.314 | 7.04 |

## Point-head stress trajectory

| # | book | catalog n | pair mass | cap30 | cap60 | cap120 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 15,001 | 383.2 | 2 | 2 | 1 |
| 2 | Hamlet — William Shakespeare | 56,520 | 644.0 | 1 | 1 | 2 |
| 3 | Crime and Punishment — Fyodor Dostoyevsky | 37,267 | 519.7 | 9 | 10 | 8 |
| 4 | Les Misérables — Victor Hugo | 42,472 | 296.9 | 6 | 8 | 5 |
| 5 | Macbeth — William Shakespeare | 51,265 | 304.1 | 5 | 7 | 6 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 14,883 | 177.8 | 3 | 5 | 4 |
| 7 | Demons — Fyodor Dostoyevsky | 2,315 | 100.6 | 8 | 4 | 3 |
| 8 | The Idiot — Fyodor Dostoyevsky | 8,723 | 194.9 | 25 | 19 | 13 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 3,574 | 66.7 | 4 | 3 | 7 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 6,147 | 65.7 | 10 | 6 | 9 |
| 11 | Paradise Lost — John Milton | 10,385 | 141.3 | 17 | 12 | 12 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 10,670 | 85.7 | 7 | 9 | 10 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 6,062 | 106.5 | 11 | 11 | 11 |
| 14 | The Divine Comedy — Dante Alighieri | 9,441 | 112.4 | 14 | 15 | 14 |
| 15 | Anna Karenina — Leo Tolstoy | 40,447 | 347.5 | 29 | 28 | 24 |
| 16 | War and Peace — Leo Tolstoy | 16,463 | 249.2 | 38 | 33 | 22 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 6,178 | 144.8 | 16 | 20 | 16 |
| 18 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 19,415 | 86.7 | 18 | 16 | 15 |
| 19 | The Magic Mountain — Thomas Mann | 2,610 | 81.3 | 15 | 14 | 17 |
| 20 | King Lear — William Shakespeare | 16,693 | 162.0 | 37 | 31 | 20 |
| 21 | Leaves of Grass — Walt Whitman | 6,922 | 79.3 | 13 | 18 | 18 |
| 22 | Faust: First Part — Johann Wolfgang von Goethe | 5,138 | 81.3 | 23 | 21 | 19 |
| 23 | Stoner — John  Williams | 6,637 | 47.5 | 12 | 13 | 21 |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 3,984 | 58.6 | 20 | 17 | 23 |
| 25 | Infinite Jest — David Foster Wallace | 4,598 | 64.9 | 26 | 22 | 25 |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 2,216 | 74.6 | 30 | 24 | 26 |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 3,419 | 93.2 | 42 | 34 | 27 |
| 28 | The Waves — Virginia Woolf | 2,478 | 49.8 | 24 | 23 | 28 |
| 29 | The Iliad — Homer | 25,162 | 175.2 | 70 | 51 | 35 |
| 30 | The Waste Land — T.S. Eliot | 3,979 | 59.7 | 33 | 25 | 29 |

## Within-evidence associations

| pair mass | books | score/catalog rho | median cap30 rank change |
|---|---:|---:|---:|
| 10–20 | 556 | -0.500 | -1 |
| 20–50 | 368 | -0.566 | -8 |
| 50–100 | 124 | -0.555 | +0 |
| 100–∞ | 95 | -0.488 | +34 |

## Interpretation

Survival under a low evidence cap is evidence against *precision-driven* popularity bias, not proof of a bias-free canon. Cultural familiarity can affect who reads, rates, or becomes a juror even after numerical evidence is capped; feature-family and selection trajectories remain necessary.

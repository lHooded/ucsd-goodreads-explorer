# Hierarchical jury/community membership audit

## Result

The corrected hierarchical estimator is crossed with equal-weight hard versus bootstrap-probability soft juries and hard versus conservative mean-max-0.90 top-two community memberships. Every user's fuzzy memberships sum to one.

| variant | rankable | J@50 | J@200 | RBO | score rho | pop rho | med top200 u |
|---|---:|---:|---:|---:|---:|---:|---:|
| soft jury / hard communities | 1143 | 1.000 | 1.000 | 1.000 | 1.000 | -0.311 | 7.01 |
| hard jury / hard communities | 1146 | 0.961 | 0.951 | 0.940 | 0.999 | -0.312 | 6.99 |
| soft jury / fuzzy90 communities | 1143 | 0.961 | 0.970 | 0.983 | 1.000 | -0.312 | 7.00 |
| hard jury / fuzzy90 communities | 1146 | 0.961 | 0.942 | 0.962 | 0.999 | -0.309 | 7.05 |

## Baseline-head rank trajectories

| baseline | book | hard jury | soft fuzzy90 | hard fuzzy90 |
|---:|---|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 2 | 1 | 1 |
| 2 | Hamlet — William Shakespeare | 1 | 2 | 2 |
| 3 | Crime and Punishment — Fyodor Dostoyevsky | 5 | 3 | 4 |
| 4 | Les Misérables — Victor Hugo | 4 | 4 | 5 |
| 5 | Macbeth — William Shakespeare | 3 | 5 | 3 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 6 | 6 | 6 |
| 7 | Demons — Fyodor Dostoyevsky | 7 | 7 | 7 |
| 8 | The Idiot — Fyodor Dostoyevsky | 9 | 8 | 8 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 8 | 9 | 9 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 10 | 11 | 11 |
| 11 | Paradise Lost — John Milton | 13 | 10 | 10 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 15 | 12 | 15 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 11 | 13 | 13 |
| 14 | The Divine Comedy — Dante Alighieri | 14 | 15 | 14 |
| 15 | Anna Karenina — Leo Tolstoy | 17 | 14 | 16 |
| 16 | War and Peace — Leo Tolstoy | 12 | 16 | 12 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 16 | 18 | 18 |
| 18 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 18 | 17 | 17 |
| 19 | The Magic Mountain — Thomas Mann | 19 | 20 | 21 |
| 20 | King Lear — William Shakespeare | 22 | 22 | 22 |

Fuzzy-community movement is an audit, not automatic improvement: smoothing mechanically reduces apparent community disagreement. The hard-jury path tests the existing jury boundary but does not refit that boundary.

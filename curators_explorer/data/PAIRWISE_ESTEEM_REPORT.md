# Within-user pairwise esteem

Same careful focus/anti cohorts. Score = shrunk focus win-rate − shrunk anti
win-rate, where a win is: same user rated A=5 and B≤3.
Per user cap: 12 highs × 12 lows.

## Probe metrics (no anti-median Q bonus)

| method | Q_clean | pos50 | anti50 | filler50 | sticky50 | heldout@200 | heldout@50 | median heldout |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| legacy_p5 | 66.5 | 24 | 0 | 2 | 25 | 0.395 | — | — |
| residual_no_author | 61.5 | 28 | 0 | 6 | 22 | 0.395 | — | — |
| pairwise (anti optional) | 43.5 | 15 | 0 | 0 | 4 | **0.535** | 0.140 | 150 |
| **pairwise_bilateral** | -59.5* | **29** | 0 | 2 | 20 | 0.442 | **0.349** | **26** |

\*Q_clean collapses from anti1000=285 (anti in ranks 51–1000), not from anti50.

## Pairwise bilateral top 15 (recommended)

Requires pair appearances in both cohorts.

- 1. Middlemarch — George Eliot
- 2. Hamlet — William Shakespeare
- 3. Les Misérables — Victor Hugo
- 4. Invisible Man — Ralph Ellison
- 5. The Things They Carried — Tim O'Brien
- 6. The Metamorphosis — Franz Kafka
- 7. Inferno (The Divine Comedy #1) — Dante Alighieri
- 8. Paradise Lost — John Milton
- 9. A Raisin in the Sun — Lorraine Hansberry
- 10. East of Eden — John Steinbeck
- 11. Lolita — Vladimir Nabokov
- 12. Madame Bovary — Gustave Flaubert
- 13. To the Lighthouse — Virginia Woolf
- 14. Mrs. Dalloway — Virginia Woolf
- 15. The Importance of Being Earnest — Oscar Wilde

## Pairwise (anti optional) top 15

High held-out@200, but often no anti support — “books focus loves that binge readers barely touch.”

- 1. The Brothers Karamazov — Fyodor Dostoyevsky
- 2. Les Fleurs du Mal — Charles Baudelaire
- 3. Four Quartets — T.S. Eliot
- 4. Leaves of Grass — Walt Whitman
- 5. Stoner — John Williams
- 6. Journey to the End of the Night — Louis-Ferdinand Celine
- 7. Gravity's Rainbow — Thomas Pynchon
- …

## Takeaway

Pairwise bilateral is the most interesting result so far: strongest poll pos50, best held-out median rank (~26), literary head that mixes syllabus and serious fiction without children’s filler. Anti still out of top 50. Worth treating as a primary candidate scorer (or combining with residual/legacy as a second axis).

Pairs built: focus≈621k, anti≈1.3M.

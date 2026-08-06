# Stability analysis (before co-training)

## What we did (plain English)

We froze the user-scoring formula, then **25 times** randomly reshuffled which users we listen to (same pool sizes), and re-ranked books each time.

If a book is near the top in almost every reshuffle, call it **sticky**. If it often falls out of the top 50, call it **fragile**.

This does **not** change the formula. It only checks whether today’s ranking is sturdy enough to build on (e.g. before co-training).

## Baseline ranking (no reshuffle)

- Q=72.0, pos50=22, anti50=0, classic50=22, normie50=6
- Focus users=6,739, anti-like users=13,684

Top 15:

- 1. Ulysses — James Joyce
- 2. Moby-Dick or, The Whale — Herman Melville
- 3. Paradise Lost — John Milton
- 4. Hamlet — William Shakespeare
- 5. Mrs. Dalloway — Virginia Woolf
- 6. Lolita — Vladimir Nabokov
- 7. Crime and Punishment — Fyodor Dostoyevsky
- 8. A Streetcar Named Desire — Tennessee Williams
- 9. Macbeth — William Shakespeare
- 10. The Trial — Franz Kafka
- 11. The Poisonwood Bible — Barbara Kingsolver
- 12. Invisible Man — Ralph Ellison
- 13. King Lear — William Shakespeare
- 14. Life After Life — Kate Atkinson
- 15. Heart of Darkness — Joseph Conrad

## How much does the top list move?

Overlap with the baseline top list after each reshuffle (1.0 = identical, 0.0 = no shared books):

- Top 50:  **0.58** ± 0.04
- Top 100: **0.57** ± 0.03
- Top 200: **0.56** ± 0.02

Probe scores across reshuffles (noisy check only):

- Q: 66.5 ± 4.5
- pos50: 22.0 ± 1.4
- anti50: 0.0 ± 0.2

## Sticky books (in baseline top 50, and in top 50 in ≥80% of reshuffles)

25 of the baseline top 50.

- #1 Ulysses — James Joyce (in top50 84% of runs; avg rank 67±138)
- #2 Moby-Dick or, The Whale — Herman Melville (in top50 100% of runs; avg rank 2±1)
- #3 Paradise Lost — John Milton (in top50 100% of runs; avg rank 7±4)
- #4 Hamlet — William Shakespeare (in top50 100% of runs; avg rank 3±1)
- #5 Mrs. Dalloway — Virginia Woolf (in top50 96% of runs; avg rank 63±263)
- #6 Lolita — Vladimir Nabokov (in top50 100% of runs; avg rank 10±3)
- #7 Crime and Punishment — Fyodor Dostoyevsky (in top50 100% of runs; avg rank 9±5)
- #8 A Streetcar Named Desire — Tennessee Williams (in top50 100% of runs; avg rank 12±8)
- #9 Macbeth — William Shakespeare (in top50 100% of runs; avg rank 14±4)
- #11 The Poisonwood Bible — Barbara Kingsolver (in top50 100% of runs; avg rank 24±7)
- #13 King Lear — William Shakespeare (in top50 88% of runs; avg rank 27±11)
- #14 Life After Life — Kate Atkinson (in top50 80% of runs; avg rank 162±455)
- #15 Heart of Darkness — Joseph Conrad (in top50 100% of runs; avg rank 12±5)
- #17 Their Eyes Were Watching God — Zora Neale Hurston (in top50 100% of runs; avg rank 15±6)
- #18 The Odyssey — Homer (in top50 100% of runs; avg rank 29±6)
- #19 Don Quixote — Miguel de Cervantes Saavedra (in top50 100% of runs; avg rank 8±5)
- #22 The Arabian Nights — Anonymous (in top50 84% of runs; avg rank 33±20)
- #25 The Grapes of Wrath — John Steinbeck (in top50 100% of runs; avg rank 26±9)
- #26 Beloved — Toni Morrison (in top50 100% of runs; avg rank 24±9)
- #29 The Things They Carried — Tim O'Brien (in top50 96% of runs; avg rank 21±12)
- #30 War and Peace — Leo Tolstoy (in top50 80% of runs; avg rank 38±16)
- #33 The Metamorphosis — Franz Kafka (in top50 100% of runs; avg rank 25±8)
- #36 Madame Bovary — Gustave Flaubert (in top50 96% of runs; avg rank 20±11)
- #38 Vanity Fair — William Makepeace Thackeray (in top50 92% of runs; avg rank 26±14)
- #42 One Hundred Years of Solitude — Gabriel Garcia Marquez (in top50 96% of runs; avg rank 28±10)

## Fragile books (in baseline top 50, but in top 50 in ≤40% of reshuffles)

- #20 Death of a Salesman — Arthur Miller (only 40% of runs)
- #24 Middlesex — Jeffrey Eugenides (only 20% of runs)
- #31 The Haunting of Hill House — Shirley Jackson (only 36% of runs)
- #41 The Virgin Suicides — Jeffrey Eugenides (only 24% of runs)
- #44 Le Morte d'Arthur: King Arthur and the Legends of the Round Table — Thomas Malory (only 8% of runs)
- #46 Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll (only 24% of runs)
- #47 Things Fall Apart (The African Trilogy, #1) — Chinua Achebe (only 12% of runs)
- #49 Candide — Voltaire (only 12% of runs)

## Often in top 50 across reshuffles, but not in baseline top 50

These are “almost made the cut” books that still keep showing up:

- Anna Karenina — Leo Tolstoy (96% of runs; avg rank ~33)
- Out of the Dust — Karen Hesse (68% of runs; avg rank ~4)
- The Tale of Despereaux — Kate DiCamillo (64% of runs; avg rank ~43)
- Charlotte's Web — E.B. White (60% of runs; avg rank ~47)
- Frindle — Andrew Clements (52% of runs; avg rank ~91)

## How to read this before co-training

- Top-50 overlap ≈ **0.58** is **middling**: the core holds, but nearly half the top-50 slots churn across reshuffles. Not fragile chaos, not rock-solid either.
- **anti50 stays ~0** across boots — junk rejection is stable even when the exact classic mix wobbles.
- **Co-training should only teach from sticky books** (the ≥80% list). Fragile top-50 titles would amplify noise.
- A few children’s/YA titles (Despereaux, Charlotte’s Web, Frindle, Out of the Dust) often enter top-50 under reshuffles though they aren’t in the baseline top-50 — watch that bleed if we co-train later.
- Verdict: **safe to plan co-training on the sticky core**; don’t treat the whole baseline top-50 as gospel yet.

## Back burner (not done now)

**Trajectory limit / relative-position paths** as we tighten filters — useful later once we have a more settled formula. Skipped here so it doesn’t muddy stability testing.

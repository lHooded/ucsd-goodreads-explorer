# Cautious co-training report

## Plan (plain English)

1. Soft positives = **sticky** books from stability (≥80% of boots in top 50).
2. Soft negatives = favorites of heavy **series-binge** users.
3. Slightly nudge feature weights so sticky-lovers score higher / binge users lower.
4. Slightly tighten gates toward sticky-lover habits.
5. **Veto:** keep the new recipe only if junk stays out and stability doesn’t get worse.

## Veto: **ACCEPTED**

- passed: anti controlled + stability not worsened materially

## Soft labels used

Sticky positives (25):

- Ulysses — James Joyce
- Moby-Dick or, The Whale — Herman Melville
- Paradise Lost — John Milton
- Hamlet — William Shakespeare
- Mrs. Dalloway — Virginia Woolf
- Lolita — Vladimir Nabokov
- Crime and Punishment — Fyodor Dostoyevsky
- A Streetcar Named Desire — Tennessee Williams
- Macbeth — William Shakespeare
- The Poisonwood Bible — Barbara Kingsolver
- King Lear — William Shakespeare
- Life After Life — Kate Atkinson
- Heart of Darkness — Joseph Conrad
- Their Eyes Were Watching God — Zora Neale Hurston
- The Odyssey — Homer
- … +10 more

Soft-negative examples (series binge favorites):

- Sunrise (Sunrise, #1) — Karen Kingsbury
- J.D. Robb In Death: The First Cases (In Death #1 & 2) — J.D. Robb
- The Proposition 5: The Ferro Family (The Proposition, #5) — H.M. Ward
- The Kindly Ones (The Sandman #9) — Neil Gaiman
- Fame (Firstborn, #1) — Karen Kingsbury
- Found (Firstborn, #3) — Karen Kingsbury
- J. R. Ward Collection: Black Dagger #1,3,5,6 & Fallen Angels #1 — J.R. Ward
- The Last Hope (Warriors: Omen of the Stars, #6) — Erin Hunter
- Fatal Frenzy (Fatal, #9) — Marie Force
- Black Dagger Brotherhood, #1-9 — J.R. Ward

## Before vs after

| | baseline | co-trained |
|---|---:|---:|
| Q | 71.7 | 71.5 |
| pos50 | 22 | 24 |
| anti50 | 0 | 0 |
| classic50 | 22 | 24 |
| boot J50 | 0.55 | 0.57 |
| sticky still ≥70% boots | 24/25 | 24/25 |
| boot anti50 | 0.08 | 0.00 |
| overlap top50 | 1.00 | 0.69 |

### Baseline top 10

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

### Co-trained top 10

- 1. Hamlet — William Shakespeare
- 2. Paradise Lost — John Milton
- 3. A Streetcar Named Desire — Tennessee Williams
- 4. Moby-Dick or, The Whale — Herman Melville
- 5. Mrs. Dalloway — Virginia Woolf
- 6. Ulysses — James Joyce
- 7. Lolita — Vladimir Nabokov
- 8. Crime and Punishment — Fyodor Dostoyevsky
- 9. The Poisonwood Bible — Barbara Kingsolver
- 10. Macbeth — William Shakespeare

## Biggest weight nudges

- `classic.mean_logn_5`: -1.00 → -0.05 (effect d=+1.42)
- `classic.depth_ge4`: +0.90 → +0.07 (effect d=-1.23)
- `classic.mega_catalog_share_5`: -1.30 → -0.54 (effect d=+0.73)
- `classic.author_div_5`: +0.50 → +1.02 (effect d=+2.41)
- `normie.mean_logn_5`: +1.30 → +0.79 (effect d=+1.42)
- `classic.singleton_author_share_5`: +0.60 → +1.09 (effect d=+1.81)
- `anti.author_div_5`: -0.60 → -1.09 (effect d=+2.41)
- `classic.binge_mean_5`: -0.70 → -1.15 (effect d=-3.59)
- `normie.mega_catalog_share_5`: +1.50 → +1.06 (effect d=+0.73)
- `classic.author_hhi_5`: -0.80 → -1.22 (effect d=-3.22)
- `anti.binge_max_5`: +0.80 → +1.22 (effect d=-2.11)
- `anti.singleton_author_share_5`: -0.80 → -1.22 (effect d=+1.81)

Gates: {'series_gate': 0.3832207300696273, 'mega_gate': 0.26934249416516093, 'binge_gate': 2.457462648079794, 'span_gate': 4.058637974381011}

## What this means next

Adopted weights saved to `cotrained_weights.json`. Next: optional second tiny step, or candidate-feature search if we plateau.

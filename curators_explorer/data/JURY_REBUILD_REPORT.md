# Jury rebuild: behavioral reconstruction of p65/s25

## Outcome

The preliminary jury uses **rich_behavior_global** and contains **4,929** users. Its honest five-fold out-of-fold overlap with the teacher is **1,377** (Jaccard **0.201**), capturing **50.9%** of stored teacher weight.

This is a reconstruction diagnostic, not a locked production cohort.

## Guardrails

- Teacher: deep mint with purity=65 and strictness=25, weighted by stored `curator_pct_weight`.
- Selected predictors: generic rating aggregates plus author breadth/concentration, series behavior, and publication-era behavior. No poll/taste membership or mint columns enter model fitting.
- The co-reading profile explicitly removes **9,617** known poll, deep-poll, taste-signal, and evaluation works before learning.
- Evaluation is out-of-fold: each user is scored by a model that did not see that user's teacher label.
- Direct-activity removal is an explicit ablation. It preserves nearly all of the rich model's recovery, while the activity-only baseline is weak; activity is not the main shortcut.
- Poll and school/normie piles remain diagnostics, never model loss terms.

## Teacher and candidate pool

- Teacher n: **3,286**, Kish ≈ **2678**, stored mass=2318.7.
- Behavioral candidates: **626,152**; teacher coverage: **3,286/3,286**.
- Restaged old focus: **4,743** users (historical exact n=4,774); old-focus↔teacher Jaccard **0.077**.
- Preliminary↔teacher Jaccard at the broader size knee is **0.201**; preliminary↔old-focus Jaccard is **0.122**.

## Honest reconstruction

| model | predictors | AUC | AP | overlap@teacher-n | Jaccard | teacher weight |
|---|---:|---:|---:|---:|---:|---:|
| activity_baseline | 11 | 0.769 | 0.014 | 59 | 0.009 | 2.9% |
| generic_behavior_global | 37 | 0.879 | 0.031 | 104 | 0.016 | 4.8% |
| rich_behavior_global | 51 | 0.981 | 0.237 | 1042 | 0.188 | 40.6% |
| rich_behavior_no_direct_activity | 47 | 0.980 | 0.222 | 1006 | 0.181 | 39.1% |
| rich_behavior_activity_matched | 47 | 0.974 | 0.149 | 673 | 0.114 | 24.3% |
| behavior_binned_matched | 30 | 0.958 | 0.217 | 956 | 0.170 | 33.7% |
| profile_mean | 1 | 0.977 | 0.166 | 744 | 0.128 | 27.0% |
| profile_evidence | 1 | 0.988 | 0.429 | 1465 | 0.287 | 54.3% |
| profile_love | 1 | 0.977 | 0.168 | 752 | 0.129 | 27.3% |
| profile_half0 | 1 | 0.973 | 0.143 | 640 | 0.108 | 23.2% |
| profile_half1 | 1 | 0.973 | 0.133 | 612 | 0.103 | 22.5% |
| profile_love_plus_behavior | 31 | 0.982 | 0.211 | 909 | 0.161 | 32.8% |

Random precision is the teacher prevalence in the candidate pool; the activity baseline shows how much of reconstruction is just shelf size and star usage.

### Preferred-model size sweep

| jury n | overlap | precision | teacher recall | Jaccard | teacher weight |
|---:|---:|---:|---:|---:|---:|
| 1643 | 592 | 0.360 | 0.180 | 0.136 | 24.9% |
| 2464 | 853 | 0.346 | 0.260 | 0.174 | 34.2% |
| 3286 | 1042 | 0.317 | 0.317 | 0.188 | 40.6% |
| 4108 | 1230 | 0.299 | 0.374 | 0.200 | 46.6% |
| 4929 | 1377 | 0.279 | 0.419 | 0.201 | 50.9% |
| 6572 | 1641 | 0.250 | 0.499 | 0.200 | 58.6% |
| 9858 | 2053 | 0.208 | 0.625 | 0.185 | 69.9% |

### What the behavioral reconstruction learned

- `mean_pub_year_5`: -0.170
- `series_share_5`: -0.145
- `n_megastar_authors_5_log`: -0.112
- `n_midpop_authors_5_log`: +0.110
- `log_n_ge4`: +0.079
- `log_n_rated`: +0.076
- `n_authors_5_log`: +0.058
- `singleton_author_share_5`: -0.058
- `popular_likes_per_log_shelf`: -0.052
- `author_div_5`: -0.045
- `p5_mid_exposed`: -0.043
- `binge_max_5_log`: -0.041
- `midpop_span_per_logn5`: +0.040
- `midpop_likes_per_log_shelf`: -0.031
- `author_hhi_5`: +0.029
- `mean_logn_all`: +0.028

### Co-reading fallback audit (not the selected jury)

Top positive non-signal anchors are shown to make the item-identity shortcut visible:
- ABC of Reading — Ezra Pound (coef=+3.00, teacher readers≈46)
- A Naked Singularity — Sergio de la Pava (coef=+3.00, teacher readers≈54)
- Pricksongs and Descants — Robert Coover (coef=+3.00, teacher readers≈38)
- 1919 (U.S.A., #2) — John dos Passos (coef=+3.00, teacher readers≈39)
- The Golem — Gustav Meyrink (coef=+3.00, teacher readers≈80)
- Woodcutters — Thomas Bernhard (coef=+3.00, teacher readers≈65)
- USA: The 42nd Parallel / 1919 / The Big Money — John dos Passos (coef=+3.00, teacher readers≈61)
- The Cantos — Ezra Pound (coef=+3.00, teacher readers≈92)
- Pornografia — Witold Gombrowicz (coef=+3.00, teacher readers≈42)
- Duino Elegies — Rainer Maria Rilke (coef=+3.00, teacher readers≈107)
- The Rings of Saturn — W.G. Sebald (coef=+3.00, teacher readers≈180)
- Mr. Sammler's Planet — Saul Bellow (coef=+3.00, teacher readers≈42)
- The Street of Crocodiles — Bruno Schulz (coef=+3.00, teacher readers≈160)
- Maldoror and the Complete Works — Comte de Lautreamont (coef=+3.00, teacher readers≈83)
- Either/Or: A Fragment of Life — Soren Kierkegaard (coef=+3.00, teacher readers≈104)
- Cosmos — Witold Gombrowicz (coef=+3.00, teacher readers≈48)

### Book-half stability

- Hash-half 0 vs hash-half 1 jury Jaccard: **0.337**.
- Half 0 vs full-profile jury: **0.601**; half 1 vs full: **0.547**.

The two disjoint book halves are a shortcut check: low agreement means the co-reading fallback is still relying on narrow reading islands rather than a stable reader trait. It was not selected.

## Pairwise head comparison

- **preliminary:** pos50=37, anti50=0, filler50=0, sticky50=10, heldout@50=0.349, heldout@200=0.628.
- **old_focus_approx:** pos50=21, anti50=0, filler50=0, sticky50=9, heldout@50=0.209, heldout@200=0.605.
- **teacher:** pos50=43, anti50=0, filler50=0, sticky50=9, heldout@50=0.442, heldout@200=0.674.
- Pairwise top-50 Jaccard preliminary↔teacher: **0.408**.
- Historical old-focus comparison (from `JURY_DIAGNOSIS_REPORT.md`): pos50=19, anti50=0, filler50=0, sticky50=6, heldout@50=0.209, heldout@200=0.605.

### Preliminary top 15

- 1. Hamlet — William Shakespeare
- 2. The Brothers Karamazov — Fyodor Dostoyevsky
- 3. Crime and Punishment — Fyodor Dostoyevsky
- 4. 2666 — Roberto Bolano
- 5. Shakespeare's Sonnets — William Shakespeare
- 6. War and Peace — Leo Tolstoy
- 7. Notes from Underground — Fyodor Dostoyevsky
- 8. Les Misérables — Victor Hugo
- 9. Demons — Fyodor Dostoyevsky
- 10. The Magic Mountain — Thomas Mann
- 11. Macbeth — William Shakespeare
- 12. Stoner — John  Williams
- 13. The Idiot — Fyodor Dostoyevsky
- 14. Invisible Man — Ralph Ellison
- 15. Anna Karenina — Leo Tolstoy

### Old_Focus_Approx top 15

- 1. The Brothers Karamazov — Fyodor Dostoyevsky
- 2. Crime and Punishment — Fyodor Dostoyevsky
- 3. Les Fleurs du Mal — Charles Baudelaire
- 4. Hamlet — William Shakespeare
- 5. Rebecca — Daphne du Maurier
- 6. Les Misérables — Victor Hugo
- 7. The Things They Carried — Tim O'Brien
- 8. Leaves of Grass — Walt Whitman
- 9. Stoner — John  Williams
- 10. Anna Karenina — Leo Tolstoy
- 11. War and Peace — Leo Tolstoy
- 12. Journey to the End of the Night — Louis-Ferdinand Celine
- 13. Revolutionary Road — Richard Yates
- 14. A Tree Grows in Brooklyn — Betty  Smith
- 15. The Count of Monte Cristo — Alexandre Dumas

### Teacher top 15

- 1. Crime and Punishment — Fyodor Dostoyevsky
- 2. The Brothers Karamazov — Fyodor Dostoyevsky
- 3. The Divine Comedy — Dante Alighieri
- 4. Gravity's Rainbow — Thomas Pynchon
- 5. Infinite Jest — David Foster Wallace
- 6. 2666 — Roberto Bolano
- 7. Stoner — John  Williams
- 8. War and Peace — Leo Tolstoy
- 9. The Magic Mountain — Thomas Mann
- 10. Demons — Fyodor Dostoyevsky
- 11. Swann's Way (In Search of Lost Time, #1) — Marcel Proust
- 12. East of Eden — John Steinbeck
- 13. The Master and Margarita — Mikhail Bulgakov
- 14. Pale Fire — Vladimir Nabokov
- 15. The Trial — Franz Kafka

## Set differences

| group | n | mean shelf | five rate | rare-loved share | mega-loved share |
|---|---:|---:|---:|---:|---:|
| teacher − jury | 1909 | 190 | 0.320 | 0.257 | 0.070 |
| jury − teacher | 3552 | 151 | 0.319 | 0.208 | 0.149 |

- Of jury−teacher, **1,424/3,552** (40.1%) are elsewhere in the deep mint. Their minted mean deep_share=0.517, com_share=0.026, n_deep=12.1.
- Missed teachers have mean stored weight=0.596, deep_share=0.706, n_deep=14.7; **45** have ≥1,000 ratings.

### Common 5★ books in the differences

**Jury − teacher:**
- Hamlet — William Shakespeare (1444 users)
- Crime and Punishment — Fyodor Dostoyevsky (944 users)
- Macbeth — William Shakespeare (843 users)
- Jane Eyre — Charlotte Bronte (703 users)
- Anna Karenina — Leo Tolstoy (699 users)
- The Brothers Karamazov — Fyodor Dostoyevsky (648 users)
- Les Misérables — Victor Hugo (641 users)
- The Stranger — Albert Camus (588 users)
- The Count of Monte Cristo — Alexandre Dumas (574 users)
- The Odyssey — Homer (570 users)

**Teacher − jury:**
- Crime and Punishment — Fyodor Dostoyevsky (766 users)
- One Hundred Years of Solitude — Gabriel Garcia Marquez (625 users)
- The Brothers Karamazov — Fyodor Dostoyevsky (623 users)
- Lolita — Vladimir Nabokov (596 users)
- The Stranger — Albert Camus (499 users)
- The Master and Margarita — Mikhail Bulgakov (416 users)
- The Metamorphosis — Franz Kafka (402 users)
- The Trial — Franz Kafka (382 users)
- Slaughterhouse-Five — Kurt Vonnegut Jr. (378 users)
- Anna Karenina — Leo Tolstoy (361 users)

## Decision

Use **rich_behavior_global at n=4,929** as the current preliminary behavioral jury. This is the overlap/mass knee rather than a copied teacher-size cut, and its pairwise head materially beats the old focus while approaching the teacher. Do not adopt the higher-overlap co-reading evidence model: its explicit literary-title anchors and only moderate disjoint-book stability make it a shortcut.

This remains a preliminary hard jury. Continuous jury weights are still deferred, as agreed in the handoff.

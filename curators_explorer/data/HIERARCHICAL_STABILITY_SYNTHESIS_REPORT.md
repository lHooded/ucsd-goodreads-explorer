# Stability-first hierarchical canon challenger

## Decision

The expanded-prior hierarchical model is now the preferred research ranking, although it is not yet the production default. It removes the popularity-correlated coverage cliff by predicting unobserved communities with partial pooling, while explicitly charging a 3.7-point empirical heterogeneity floor for those predictions.

Across the displayed top 200 there are **117 stable-core**, **51 supported/boundary**, and **32 underexposed-or-contested** books. The tiers annotate evidence; they do not change the point order.

A stable-core book stays top 200 under nine plausible prior/evidence-cap/uncertainty/Γ specifications, all hard/soft/fuzzy membership paths, the no-shelf-size jury, and the expanded-prior ranking; has at least 80% joint-reader-by-jury and fixed-mass-120 top-200 inclusion; survives the bounded community-influence test; has pair mass at least 20; and retains score at least 50 under Γ=2. The supported tier relaxes the mass and inclusion conditions; the final tier is an explicit uncertainty flag.

- Rankable books: **1,139** at publication mass 10; priors are learned on **4,920** mass-2 works.
- Reader stability: mean Jaccard **0.707** at 50 and **0.733** at 200 over 2,000 draws.
- Jury-definition stability: mean Jaccard **0.887** at 50 and **0.931** at 200 over 100 refits.
- Joint reader-by-jury stability: mean Jaccard **0.701** at 50 and **0.726** at 200 over 1,000 draws; median top-200 joint u80 is **4.17** points.
- Bounded community influence (largest weight at most 2x smallest): shared-mixture mean Jaccard **0.976/0.990** at 50/200; book-specific least-favourable Jaccard **0.961/0.951**. All 7 sensitive books were already fragile.
- Edition/language audit: merging all already-flagged duplicate work IDs leaves Jaccard **1.000/1.000** at 50/200. The top 200 has a median **52** editions, and **195** have more than one known edition language; known fragmentation is not driving the ranking.
- No-shelf-size jury: Jaccard **0.887** at 50 and **0.887** at 200; expanded-prior mass-10 ranking: **0.961 / 0.961**.
- Actual-reader fixed-mass thinning: mean Jaccard 50/200 is **0.732/0.935** at expected mass 60 and **0.886/0.981** at mass 120.
- Score versus catalog readership: Spearman **-0.244**. Under the aggressive 30-vote aggregate cap, Jaccard is 0.724/0.869 at 50/200 and all five point leaders remain top ten. This argues against precision-driven popularity at the head, but not against cultural familiarity or reader selection.

`score ±u*` uses the larger of analytic posterior/partition uncertainty and the joint reader-by-jury u80. The components overlap and are not added in quadrature. Feature-family, fixed-mass, Γ, and temporal paths remain separate.

## Current top 50

| # | book | score ±u* | tier | spec ranks | cap30 | joint ranks | joint top200 | full readers | pair mass | coverage | rated/read | temporal |
|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 83.5 ±4.0 | core | 1–2 | 2 | 1–2 | 100% | 17,481 | 383.2 | 100% | 97% | ↑ |
| 2 | Hamlet — William Shakespeare | 83.0 ±3.2 | core | 1–2 | 1 | 1–2 | 100% | 58,851 | 644.0 | 100% | 99% | mixed |
| 3 | Les Misérables — Victor Hugo | 75.6 ±4.5 | core | 3–8 | 6 | 3–9 | 100% | 47,886 | 296.9 | 98% | 97% | ↑ |
| 4 | Crime and Punishment — Fyodor Dostoyevsky | 75.3 ±7.0 | core | 3–10 | 9 | 3–7 | 100% | 40,702 | 519.7 | 100% | 99% | ↑ |
| 5 | Macbeth — William Shakespeare | 75.2 ±4.2 | core | 4–7 | 5 | 3–10 | 100% | 53,103 | 304.1 | 100% | 99% | mixed |
| 6 | The Master and Margarita — Mikhail Bulgakov | 74.0 ±4.4 | core | 4–7 | 3 | 4–16 | 100% | 16,472 | 177.8 | 94% | 97% | mixed |
| 7 | Demons — Fyodor Dostoyevsky | 73.7 ±5.1 | core | 3–7 | 8 | 4–12 | 100% | 2,628 | 100.6 | 53% | 96% | mixed |
| 8 | The Idiot — Fyodor Dostoyevsky | 71.2 ±6.7 | core | 8–19 | 25 | 5–22 | 100% | 10,037 | 194.9 | 94% | 97% | ↑ |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 71.1 ±5.8 | core | 3–11 | 4 | 6–24 | 100% | 3,863 | 66.7 | 65% | 97% | ↑ |
| 10 | Shakespeare's Sonnets — William Shakespeare | 70.2 ±6.1 | core | 6–16 | 10 | 7–28 | 100% | 6,427 | 65.7 | 72% | 98% | mixed |
| 11 | Paradise Lost — John Milton | 69.9 ±5.9 | core | 10–13 | 17 | 5–27 | 100% | 11,357 | 141.3 | 100% | 98% | mixed |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 69.4 ±5.7 | core | 9–12 | 7 | 9–30 | 100% | 11,619 | 85.7 | 90% | 98% | ↓ |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 69.3 ±5.5 | core | 11–13 | 11 | 8–22 | 100% | 6,415 | 106.5 | 79% | 99% | ↓ |
| 14 | The Divine Comedy — Dante Alighieri | 69.0 ±5.4 | core | 14–17 | 14 | 8–29 | 100% | 10,793 | 112.4 | 92% | 97% | mixed |
| 15 | War and Peace — Leo Tolstoy | 68.7 ±6.0 | core | 15–33 | 38 | 6–25 | 100% | 19,756 | 249.2 | 97% | 96% | mixed |
| 16 | Anna Karenina — Leo Tolstoy | 68.5 ±4.1 | core | 13–28 | 29 | 7–25 | 100% | 46,974 | 347.5 | 100% | 97% | mixed |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 67.9 ±4.9 | core | 14–20 | 16 | 10–40 | 100% | 6,557 | 144.8 | 87% | 99% | ↑ |
| 18 | King Lear — William Shakespeare | 67.3 ±5.2 | core | 18–31 | 37 | 10–36 | 100% | 17,424 | 162.0 | 96% | 99% | mixed |
| 19 | The Magic Mountain — Thomas Mann | 67.2 ±5.6 | core | 14–20 | 15 | 13–37 | 100% | 3,016 | 81.3 | 71% | 96% | mixed |
| 20 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 66.8 ±5.9 | core | 15–20 | 18 | 11–40 | 100% | 21,160 | 86.7 | 89% | 99% | mixed |
| 21 | Faust: First Part — Johann Wolfgang von Goethe | 66.5 ±5.9 | core | 19–24 | 23 | 12–46 | 100% | 5,376 | 81.3 | 85% | 98% | ↓ |
| 22 | Leaves of Grass — Walt Whitman | 66.1 ±5.8 | core | 18–26 | 13 | 13–45 | 100% | 7,505 | 79.3 | 89% | 98% | ↓ |
| 23 | Stoner — John  Williams | 65.7 ±6.7 | core | 13–23 | 12 | 16–40 | 100% | 7,200 | 47.5 | 51% | 97% | ↓ |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 65.5 ±6.2 | core | 17–25 | 20 | 17–43 | 100% | 4,597 | 58.6 | 46% | 97% | mixed |
| 25 | Infinite Jest — David Foster Wallace | 65.0 ±6.2 | core | 19–29 | 26 | 18–55 | 100% | 7,470 | 64.9 | 63% | 88% | ↓ |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 65.0 ±5.9 | core | 24–29 | 30 | 18–58 | 100% | 2,541 | 74.6 | 53% | 96% | mixed |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 64.8 ±6.2 | core | 27–34 | 42 | 15–65 | 100% | 4,552 | 93.2 | 77% | 92% | ↓ |
| 28 | The Iliad — Homer | 64.1 ±7.3 | core | 28–51 | 70 | 16–61 | 100% | 26,538 | 175.2 | 100% | 98% | mixed |
| 29 | The Waves — Virginia Woolf | 64.0 ±6.3 | core | 23–32 | 24 | 17–67 | 100% | 3,012 | 49.8 | 54% | 95% | ↑ |
| 30 | The Count of Monte Cristo — Alexandre Dumas | 63.5 ±4.6 | core | 25–54 | 60 | 17–50 | 100% | 49,532 | 280.7 | 98% | 99% | ↑ |
| 31 | The Waste Land — T.S. Eliot | 63.4 ±6.4 | core | 25–37 | 33 | 21–70 | 100% | 4,166 | 59.7 | 75% | 99% | ↓ |
| 32 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 63.3 ±5.2 | core | 27–40 | 35 | 17–70 | 100% | 41,549 | 130.2 | 99% | 100% | ↓ |
| 33 | 2666 — Roberto Bolano | 63.1 ±6.8 | core | 25–40 | 22 | 25–58 | 100% | 2,876 | 38.4 | 25% | 90% | mixed |
| 34 | A Streetcar Named Desire — Tennessee Williams | 63.1 ±5.9 | core | 30–36 | 31 | 21–70 | 100% | 17,717 | 77.8 | 89% | 99% | ↓ |
| 35 | The Book of Disquiet — Fernando Pessoa | 63.0 ±6.9 | core | 27–36 | 19 | 25–54 | 100% | 2,282 | 38.0 | 38% | 91% | mixed |
| 36 | East of Eden — John Steinbeck | 62.9 ±6.4 | core | 35–46 | 48 | 21–69 | 100% | 26,096 | 92.9 | 92% | 99% | ↑ |
| 37 | Bartleby the Scrivener — Herman Melville | 62.6 ±6.5 | core | 29–37 | 32 | 24–66 | 100% | 4,123 | 48.9 | 52% | 99% | mixed |
| 38 | The Overcoat — Nikolai Gogol | 62.2 ±6.7 | core | 30–39 | 27 | 24–88 | 99% | 2,791 | 44.2 | 52% | 99% | ↓ |
| 39 | Dead Souls — Nikolai Gogol | 61.8 ±5.9 | core | 34–47 | 46 | 26–74 | 100% | 4,948 | 98.6 | 82% | 97% | mixed |
| 40 | One Hundred Years of Solitude — Gabriel Garcia Marquez | 61.7 ±5.8 | core | 38–76 | 92 | 21–63 | 100% | 54,239 | 304.9 | 100% | 98% | mixed |
| 41 | Hunger — Knut Hamsun | 61.6 ±6.2 | core | 35–43 | 49 | 28–80 | 100% | 3,841 | 62.9 | 58% | 99% | mixed |
| 42 | The Sound and the Fury — William Faulkner | 61.0 ±6.7 | core | 44–74 | 111 | 24–86 | 100% | 13,016 | 149.1 | 97% | 98% | mixed |
| 43 | The Arabian Nights — Anonymous | 60.9 ±7.2 | core | 37–43 | 28 | 29–74 | 100% | 5,931 | 38.2 | 62% | 97% | ↓ |
| 44 | Richard III — William Shakespeare | 60.8 ±6.6 | core | 39–47 | 43 | 30–76 | 100% | 4,892 | 48.7 | 46% | 99% | mixed |
| 45 | In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust | 60.7 ±7.3 | core | 30–59 | 21 | 28–103 | 99% | 929 | 29.6 | 32% | 93% | mixed |
| 46 | If on a Winter's Night a Traveler — Italo Calvino | 60.6 ±6.2 | core | 42–48 | 53 | 33–91 | 100% | 7,435 | 70.0 | 70% | 97% | mixed |
| 47 | Othello — William Shakespeare | 60.5 ±6.3 | core | 45–79 | 100 | 25–80 | 100% | 27,647 | 186.7 | 97% | 99% | mixed |
| 48 | Eugene Onegin — Alexander Pushkin | 60.5 ±6.4 | core | 46–57 | 59 | 30–117 | 98% | 3,505 | 66.6 | 72% | 98% | mixed |
| 49 | The Importance of Being Earnest — Oscar Wilde | 60.3 ±6.4 | core | 41–66 | 58 | 27–96 | 100% | 24,794 | 113.1 | 96% | 100% | ↓ |
| 50 | Blood Meridian, or the Evening Redness in the West — Cormac McCarthy | 60.2 ±6.2 | core | 42–63 | 75 | 31–93 | 100% | 7,287 | 63.7 | 50% | 96% | ↓ |

## Current top 50: upstream and fixed-mass stress

`mass60` is a deliberately severe stress path and is not a core-tier veto.

| # | book | no-activity ranks | old-prior rank | mass60 ranks | mass120 ranks | community R2 worst |
|---:|---|---:|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 1–1 | 1 | 1–8 | 1–3 | 1 |
| 2 | Hamlet — William Shakespeare | 2–2 | 2 | 1–5 | 1–3 | 2 |
| 3 | Les Misérables — Victor Hugo | 3–3 | 4 | 3–20 | 3–10 | 3 |
| 4 | Crime and Punishment — Fyodor Dostoyevsky | 4–4 | 3 | 1–10 | 2–6 | 5 |
| 5 | Macbeth — William Shakespeare | 8–8 | 5 | 3–28 | 3–13 | 4 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 6–7 | 6 | 7–36 | 6–13 | 7 |
| 7 | Demons — Fyodor Dostoyevsky | 5–5 | 7 | 4–15 | 4–6 | 6 |
| 8 | The Idiot — Fyodor Dostoyevsky | 10–11 | 8 | 7–35 | 6–17 | 9 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 9–9 | 9 | 2–5 | 6–9 | 8 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 27–27 | 10 | 4–9 | 8–11 | 10 |
| 11 | Paradise Lost — John Milton | 6–7 | 11 | 6–30 | 7–16 | 13 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 10–11 | 12 | 9–23 | 12–15 | 12 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 16–18 | 13 | 11–31 | 10–13 | 11 |
| 14 | The Divine Comedy — Dante Alighieri | 12–12 | 14 | 8–29 | 12–15 | 14 |
| 15 | War and Peace — Leo Tolstoy | 13–13 | 16 | 4–28 | 6–20 | 16 |
| 16 | Anna Karenina — Leo Tolstoy | 14–14 | 15 | 7–45 | 7–31 | 17 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 17–17 | 17 | 20–64 | 16–26 | 15 |
| 18 | King Lear — William Shakespeare | 15–16 | 20 | 15–63 | 16–31 | 19 |
| 19 | The Magic Mountain — Thomas Mann | 20–21 | 19 | 11–28 | 15–18 | 18 |
| 20 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 19–20 | 18 | 13–34 | 19–22 | 20 |
| 21 | Faust: First Part — Johann Wolfgang von Goethe | 15–18 | 22 | 10–26 | 17–19 | 21 |
| 22 | Leaves of Grass — Walt Whitman | 23–23 | 21 | 15–35 | 20–23 | 22 |
| 23 | Stoner — John  Williams | 24–25 | 23 | 11–16 | 22–25 | 23 |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 19–21 | 24 | 9–14 | 20–24 | 24 |
| 25 | Infinite Jest — David Foster Wallace | 48–50 | 25 | 15–25 | 25–28 | 25 |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 24–25 | 26 | 15–30 | 24–27 | 26 |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 30–31 | 27 | 17–65 | 26–29 | 27 |
| 28 | The Iliad — Homer | 33–33 | 29 | 15–57 | 20–42 | 31 |
| 29 | The Waves — Virginia Woolf | 22–22 | 28 | 21–27 | 28–31 | 28 |
| 30 | The Count of Monte Cristo — Alexandre Dumas | 34–34 | 31 | 16–96 | 19–66 | 37 |
| 31 | The Waste Land — T.S. Eliot | 26–26 | 30 | 27–32 | 31–35 | 29 |
| 32 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 37–40 | 35 | 27–76 | 27–42 | 35 |
| 33 | 2666 — Roberto Bolano | 31–32 | 32 | 22–28 | 31–35 | 32 |
| 34 | A Streetcar Named Desire — Tennessee Williams | 29–32 | 33 | 33–58 | 34–37 | 30 |
| 35 | The Book of Disquiet — Fernando Pessoa | 35–35 | 34 | 21–27 | 31–35 | 33 |
| 36 | East of Eden — John Steinbeck | 56–62 | 39 | 31–65 | 31–36 | 34 |
| 37 | Bartleby the Scrivener — Herman Melville | 39–39 | 36 | 27–32 | 36–38 | 36 |
| 38 | The Overcoat — Nikolai Gogol | 28–28 | 37 | 30–35 | 37–40 | 38 |
| 39 | Dead Souls — Nikolai Gogol | 43–44 | 38 | 41–78 | 38–42 | 39 |
| 40 | One Hundred Years of Solitude — Gabriel Garcia Marquez | 45–51 | 43 | 20–91 | 20–67 | 44 |
| 41 | Hunger — Knut Hamsun | 29–30 | 40 | 32–39 | 40–43 | 40 |
| 42 | The Sound and the Fury — William Faulkner | 37–40 | 46 | 41–128 | 39–62 | 47 |
| 43 | The Arabian Nights — Anonymous | 50–51 | 42 | 37–42 | 43–46 | 42 |
| 44 | Richard III — William Shakespeare | 52–52 | 44 | 34–39 | 42–45 | 41 |
| 45 | In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust | 36–38 | 41 | 47–53 | 48–52 | 45 |
| 46 | If on a Winter's Night a Traveler — Italo Calvino | 45–46 | 45 | 38–59 | 44–47 | 43 |
| 47 | Othello — William Shakespeare | 47–49 | 48 | 34–111 | 29–68 | 56 |
| 48 | Eugene Onegin — Alexander Pushkin | 41–41 | 50 | 37–60 | 45–48 | 46 |
| 49 | The Importance of Being Earnest — Oscar Wilde | 42–42 | 47 | 48–111 | 48–53 | 50 |
| 50 | Blood Meridian, or the Evening Redness in the West — Cormac McCarthy | 55–56 | 52 | 46–70 | 54–58 | 49 |

## Remaining limitations and next work

1. Retain the three sub-10 exploratory top-200 entrants as an underexposed watch list until additional evidence exists.
2. The four books newly entering the publication top 200 have now been audited and remain in the fragile tier because at least one membership/feature path crosses rank 200 and their old-prior Γ=2 scores fall just below 50.
3. Keep known-read/unrated Γ and temporal trajectories visible as systematic paths, not silently folded into the score.
4. Treat cultural familiarity and Goodreads selection as the main unresolved bias; stability cannot prove that an unobserved or culturally isolated canon has been recovered.
5. Any further cross-language work-ID merging needs external identifiers or manual review; translated title text alone is not safe enough to mutate the point model.

# Hierarchical jury-definition bootstrap

## Result

Each draw Bayesian-bootstraps the positive teacher cohort, refits the five-fold behavioral jury model, selects a 4,929-person jury, and reruns the hierarchical book estimator through hard and conservative fuzzy90 communities.

- Replicates: **100**; refit time: **659.3s**.
- Jury Jaccard q10/median/q90: **0.919 / 0.930 / 0.939**.

| communities | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 | median jury u80 | median eligibility |
|---|---:|---:|---:|---:|---:|---:|
| hard | 0.887 | 0.852 | 0.931 | 0.914 | 0.85 | 100% |
| fuzzy90 | 0.897 | 0.852 | 0.935 | 0.922 | 0.81 | 100% |

## Hard-community point head

| # | book | score | jury u80 | top200 | jury-rank q10–q90 |
|---:|---|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 83.4 | 0.9 | 100% | 1–2 |
| 2 | Hamlet — William Shakespeare | 82.8 | 1.0 | 100% | 1–2 |
| 3 | Crime and Punishment — Fyodor Dostoyevsky | 75.0 | 0.9 | 100% | 3–5 |
| 4 | Les Misérables — Victor Hugo | 74.9 | 1.0 | 100% | 3–5 |
| 5 | Macbeth — William Shakespeare | 74.5 | 1.3 | 100% | 3–7 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 73.8 | 0.5 | 100% | 5–7 |
| 7 | Demons — Fyodor Dostoyevsky | 73.2 | 0.5 | 100% | 6–7 |
| 8 | The Idiot — Fyodor Dostoyevsky | 70.7 | 1.5 | 100% | 8–12 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 70.6 | 0.7 | 100% | 8–11 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 69.8 | 0.7 | 100% | 9–13 |
| 11 | Paradise Lost — John Milton | 69.6 | 1.3 | 100% | 9–14 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 69.1 | 0.9 | 100% | 11–15 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 69.0 | 0.9 | 100% | 10–14 |
| 14 | The Divine Comedy — Dante Alighieri | 68.2 | 1.1 | 100% | 11–18 |
| 15 | Anna Karenina — Leo Tolstoy | 68.0 | 0.7 | 100% | 14–18 |
| 16 | War and Peace — Leo Tolstoy | 67.9 | 1.5 | 100% | 11–20 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 67.6 | 0.6 | 100% | 15–19 |
| 18 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 67.2 | 1.3 | 100% | 15–22 |
| 19 | The Magic Mountain — Thomas Mann | 67.0 | 0.7 | 100% | 16–21 |
| 20 | King Lear — William Shakespeare | 66.7 | 0.9 | 100% | 17–22 |
| 21 | Leaves of Grass — Walt Whitman | 66.2 | 0.5 | 100% | 19–23 |
| 22 | Faust: First Part — Johann Wolfgang von Goethe | 66.0 | 0.7 | 100% | 18–22 |
| 23 | Stoner — John  Williams | 65.4 | 0.6 | 100% | 22–25 |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 65.1 | 0.8 | 100% | 22–26 |
| 25 | Infinite Jest — David Foster Wallace | 64.6 | 0.7 | 100% | 24–29 |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 64.5 | 0.6 | 100% | 24–28 |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 64.1 | 0.9 | 100% | 26–30 |
| 28 | The Waves — Virginia Woolf | 64.1 | 1.2 | 100% | 25–32 |
| 29 | The Iliad — Homer | 63.6 | 1.6 | 100% | 25–39 |
| 30 | The Waste Land — T.S. Eliot | 63.2 | 0.6 | 100% | 29–36 |
| 31 | The Count of Monte Cristo — Alexandre Dumas | 63.2 | 1.0 | 100% | 27–36 |
| 32 | 2666 — Roberto Bolano | 63.0 | 0.7 | 100% | 29–37 |
| 33 | A Streetcar Named Desire — Tennessee Williams | 62.9 | 1.0 | 100% | 28–37 |
| 34 | The Book of Disquiet — Fernando Pessoa | 62.9 | 0.4 | 100% | 30–35 |
| 35 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 62.8 | 0.9 | 100% | 28–37 |
| 36 | Bartleby the Scrivener — Herman Melville | 62.3 | 0.7 | 100% | 32–39 |
| 37 | The Overcoat — Nikolai Gogol | 62.3 | 0.7 | 100% | 32–40 |
| 38 | Dead Souls — Nikolai Gogol | 61.6 | 0.9 | 100% | 36–44 |
| 39 | East of Eden — John Steinbeck | 61.5 | 1.2 | 100% | 35–46 |
| 40 | Hunger — Knut Hamsun | 61.4 | 0.7 | 100% | 38–46 |

This isolates finite teacher-composition uncertainty. Reader resampling, teacher-definition alternatives, and missing-not-at-random Γ paths remain separate.

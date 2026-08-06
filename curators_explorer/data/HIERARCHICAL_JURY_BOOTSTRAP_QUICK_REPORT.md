# Hierarchical jury-definition bootstrap

## Result

Each draw Bayesian-bootstraps the positive teacher cohort, refits the five-fold behavioral jury model, selects a 4,929-person jury, and reruns the hierarchical book estimator through hard and conservative fuzzy90 communities.

- Replicates: **2**; refit time: **24.3s**.
- Jury Jaccard q10/median/q90: **0.909 / 0.920 / 0.931**.

| communities | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 | median jury u80 | median eligibility |
|---|---:|---:|---:|---:|---:|---:|
| hard | 0.887 | 0.887 | 0.951 | 0.951 | 0.29 | 100% |
| fuzzy90 | 0.923 | 0.923 | 0.966 | 0.962 | 0.26 | 100% |

## Hard-community point head

| # | book | score | jury u80 | top200 | jury-rank q10–q90 |
|---:|---|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 83.4 | 0.3 | 100% | 2–2 |
| 2 | Hamlet — William Shakespeare | 82.8 | 0.3 | 100% | 1–1 |
| 3 | Crime and Punishment — Fyodor Dostoyevsky | 75.0 | 0.2 | 100% | 4–5 |
| 4 | Les Misérables — Victor Hugo | 74.9 | 0.1 | 100% | 3–4 |
| 5 | Macbeth — William Shakespeare | 74.5 | 0.4 | 100% | 3–5 |
| 6 | The Master and Margarita — Mikhail Bulgakov | 73.8 | 0.4 | 100% | 6–7 |
| 7 | Demons — Fyodor Dostoyevsky | 73.2 | 0.2 | 100% | 6–7 |
| 8 | The Idiot — Fyodor Dostoyevsky | 70.7 | 0.4 | 100% | 8–8 |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 70.6 | 0.4 | 100% | 9–9 |
| 10 | Shakespeare's Sonnets — William Shakespeare | 69.8 | 0.1 | 100% | 10–13 |
| 11 | Paradise Lost — John Milton | 69.6 | 0.3 | 100% | 11–12 |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 69.1 | 0.3 | 100% | 11–14 |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 69.0 | 1.1 | 100% | 11–16 |
| 14 | The Divine Comedy — Dante Alighieri | 68.2 | 0.7 | 100% | 12–14 |
| 15 | Anna Karenina — Leo Tolstoy | 68.0 | 0.2 | 100% | 15–16 |
| 16 | War and Peace — Leo Tolstoy | 67.9 | 0.0 | 100% | 19–19 |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 67.6 | 0.1 | 100% | 13–17 |
| 18 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 67.2 | 0.7 | 100% | 16–20 |
| 19 | The Magic Mountain — Thomas Mann | 67.0 | 0.1 | 100% | 16–18 |
| 20 | King Lear — William Shakespeare | 66.7 | 0.0 | 100% | 21–21 |
| 21 | Leaves of Grass — Walt Whitman | 66.2 | 0.1 | 100% | 20–22 |
| 22 | Faust: First Part — Johann Wolfgang von Goethe | 66.0 | 0.4 | 100% | 18–22 |
| 23 | Stoner — John  Williams | 65.4 | 0.2 | 100% | 23–23 |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 65.1 | 0.0 | 100% | 24–24 |
| 25 | Infinite Jest — David Foster Wallace | 64.6 | 0.4 | 100% | 25–28 |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 64.5 | 0.0 | 100% | 26–28 |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 64.1 | 0.1 | 100% | 27–29 |
| 28 | The Waves — Virginia Woolf | 64.1 | 0.0 | 100% | 25–26 |
| 29 | The Iliad — Homer | 63.6 | 0.3 | 100% | 36–40 |
| 30 | The Waste Land — T.S. Eliot | 63.2 | 0.2 | 100% | 32–34 |
| 31 | The Count of Monte Cristo — Alexandre Dumas | 63.2 | 0.1 | 100% | 29–30 |
| 32 | 2666 — Roberto Bolano | 63.0 | 0.4 | 100% | 30–34 |
| 33 | A Streetcar Named Desire — Tennessee Williams | 62.9 | 0.3 | 100% | 27–31 |
| 34 | The Book of Disquiet — Fernando Pessoa | 62.9 | 0.3 | 100% | 32–36 |
| 35 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 62.8 | 0.5 | 100% | 32–36 |
| 36 | Bartleby the Scrivener — Herman Melville | 62.3 | 0.2 | 100% | 37–38 |
| 37 | The Overcoat — Nikolai Gogol | 62.3 | 0.2 | 100% | 33–33 |
| 38 | Dead Souls — Nikolai Gogol | 61.6 | 0.6 | 100% | 39–43 |
| 39 | East of Eden — John Steinbeck | 61.5 | 0.2 | 100% | 36–39 |
| 40 | Hunger — Knut Hamsun | 61.4 | 0.2 | 100% | 40–40 |

This isolates finite teacher-composition uncertainty. Reader resampling, teacher-definition alternatives, and missing-not-at-random Γ paths remain separate.

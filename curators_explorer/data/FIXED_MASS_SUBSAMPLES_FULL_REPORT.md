# Fixed-mass reader-subsample audit

## Design

For every book above the target, each observed jury user×book pair event is independently retained with probability target/full-mass. Thus popular books are reranked from actual reader subsets with the same expected effective evidence, rather than retaining their full-sample rate and merely inflating its uncertainty.

- Mode: **full**; draws per target: **300**; pair events: **557,502**.

| target | books thinned | mean J@50 | q10 J@50 | mean J@200 | q10 J@200 |
|---:|---:|---:|---:|---:|---:|
| 60 | 160 | 0.732 | 0.695 | 0.935 | 0.914 |
| 120 | 63 | 0.886 | 0.852 | 0.981 | 0.970 |

## Baseline head

| # | book | full mass | target60 rank q10–q90 | top200 | target120 rank q10–q90 | top200 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | The Brothers Karamazov — Fyodor Dostoyevsky | 383.2 | 1–8 | 100% | 1–3 | 100% |
| 2 | Hamlet — William Shakespeare | 644.0 | 1–5 | 100% | 1–3 | 100% |
| 3 | Les Misérables — Victor Hugo | 296.9 | 3–20 | 100% | 3–10 | 100% |
| 4 | Crime and Punishment — Fyodor Dostoyevsky | 519.7 | 1–10 | 100% | 2–6 | 100% |
| 5 | Macbeth — William Shakespeare | 304.1 | 3–28 | 100% | 3–13 | 100% |
| 6 | The Master and Margarita — Mikhail Bulgakov | 177.8 | 7–36 | 100% | 6–13 | 100% |
| 7 | Demons — Fyodor Dostoyevsky | 100.6 | 4–15 | 100% | 4–6 | 100% |
| 8 | The Idiot — Fyodor Dostoyevsky | 194.9 | 7–35 | 100% | 6–17 | 100% |
| 9 | Les Fleurs du Mal — Charles Baudelaire | 66.7 | 2–5 | 100% | 6–9 | 100% |
| 10 | Shakespeare's Sonnets — William Shakespeare | 65.7 | 4–9 | 100% | 8–11 | 100% |
| 11 | Paradise Lost — John Milton | 141.3 | 6–30 | 100% | 7–16 | 100% |
| 12 | Inferno (The Divine Comedy #1) — Dante Alighieri | 85.7 | 9–23 | 100% | 12–15 | 100% |
| 13 | The Death of Ivan Ilych — Leo Tolstoy | 106.5 | 11–31 | 100% | 10–13 | 100% |
| 14 | The Divine Comedy — Dante Alighieri | 112.4 | 8–29 | 100% | 12–15 | 100% |
| 15 | War and Peace — Leo Tolstoy | 249.2 | 4–28 | 100% | 6–20 | 100% |
| 16 | Anna Karenina — Leo Tolstoy | 347.5 | 7–45 | 100% | 7–31 | 100% |
| 17 | Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 144.8 | 20–64 | 100% | 16–26 | 100% |
| 18 | King Lear — William Shakespeare | 162.0 | 15–63 | 100% | 16–31 | 100% |
| 19 | The Magic Mountain — Thomas Mann | 81.3 | 11–28 | 100% | 15–18 | 100% |
| 20 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 86.7 | 13–34 | 100% | 19–22 | 100% |
| 21 | Faust: First Part — Johann Wolfgang von Goethe | 81.3 | 10–26 | 100% | 17–19 | 100% |
| 22 | Leaves of Grass — Walt Whitman | 79.3 | 15–35 | 100% | 20–23 | 100% |
| 23 | Stoner — John  Williams | 47.5 | 11–16 | 100% | 22–25 | 100% |
| 24 | Notes from Underground — Fyodor Dostoyevsky | 58.6 | 9–14 | 100% | 20–24 | 100% |
| 25 | Infinite Jest — David Foster Wallace | 64.9 | 15–25 | 100% | 25–28 | 100% |
| 26 | Journey to the End of the Night — Louis-Ferdinand Celine | 74.6 | 15–30 | 100% | 24–27 | 100% |
| 27 | Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 93.2 | 17–65 | 100% | 26–29 | 100% |
| 28 | The Iliad — Homer | 175.2 | 15–57 | 100% | 20–42 | 100% |
| 29 | The Waves — Virginia Woolf | 49.8 | 21–27 | 100% | 28–31 | 100% |
| 30 | The Count of Monte Cristo — Alexandre Dumas | 280.7 | 16–96 | 100% | 19–66 | 100% |
| 31 | The Waste Land — T.S. Eliot | 59.7 | 27–32 | 100% | 31–35 | 100% |
| 32 | Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 130.2 | 27–76 | 100% | 27–42 | 100% |
| 33 | 2666 — Roberto Bolano | 38.4 | 22–28 | 100% | 31–35 | 100% |
| 34 | A Streetcar Named Desire — Tennessee Williams | 77.8 | 33–58 | 100% | 34–37 | 100% |
| 35 | The Book of Disquiet — Fernando Pessoa | 38.0 | 21–27 | 100% | 31–35 | 100% |
| 36 | East of Eden — John Steinbeck | 92.9 | 31–65 | 100% | 31–36 | 100% |
| 37 | Bartleby the Scrivener — Herman Melville | 48.9 | 27–32 | 100% | 36–38 | 100% |
| 38 | The Overcoat — Nikolai Gogol | 44.2 | 30–35 | 100% | 37–40 | 100% |
| 39 | Dead Souls — Nikolai Gogol | 98.6 | 41–78 | 100% | 38–42 | 100% |
| 40 | One Hundred Years of Solitude — Gabriel Garcia Marquez | 304.9 | 20–91 | 100% | 20–67 | 100% |
| 41 | Hunger — Knut Hamsun | 62.9 | 32–39 | 100% | 40–43 | 100% |
| 42 | The Sound and the Fury — William Faulkner | 149.1 | 41–128 | 99% | 39–62 | 100% |
| 43 | The Arabian Nights — Anonymous | 38.2 | 37–42 | 100% | 43–46 | 100% |
| 44 | Richard III — William Shakespeare | 48.7 | 34–39 | 100% | 42–45 | 100% |
| 45 | In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust | 29.6 | 47–53 | 100% | 48–52 | 100% |
| 46 | If on a Winter's Night a Traveler — Italo Calvino | 70.0 | 38–59 | 100% | 44–47 | 100% |
| 47 | Othello — William Shakespeare | 186.7 | 34–111 | 99% | 29–68 | 100% |
| 48 | Eugene Onegin — Alexander Pushkin | 66.6 | 37–60 | 100% | 45–48 | 100% |
| 49 | The Importance of Being Earnest — Oscar Wilde | 113.1 | 48–111 | 100% | 48–53 | 100% |
| 50 | Blood Meridian, or the Evening Redness in the West — Cormac McCarthy | 63.7 | 46–70 | 100% | 54–58 | 100% |

This is deliberately more destructive than deterministic evidence capping: it asks what would happen if the extra readers had never been observed. It is a popularity-leverage stress test, not the preferred point estimator and not a calibrated confidence interval.

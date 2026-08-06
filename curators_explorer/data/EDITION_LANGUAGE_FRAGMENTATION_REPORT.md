# Edition and language-fragmentation audit

## Result

Goodreads already joins most editions and translations under a shared work ID. This audit additionally merges only the duplicate-work links already present in the local catalog flags, keeping at most one vote per user and preferring their canonical record when both are rated.

- Expanded candidates: baseline **4,920**, duplicate-merged **4,920**; publishable mass-10 books: **1,139 / 1,139**.
- Ranking similarity after the merge: J@50 **1.000**, J@200 **1.000**, RBO **1.000**.
- Publishable books with flagged duplicate evidence: **13**; within the merged top 200: **5**.
- The top 200 has a median **52** editions; **195** have editions recorded in more than one known language.

## Largest duplicate-evidence changes

| merged # | book | old # | old mass | merged mass | borrowed pair users | duplicate works |
|---:|---|---:|---:|---:|---:|---:|
| 1087 | 'Salem's Lot — Stephen King | 1081 | 26.3 | 27.5 | 16 | 1 |
| 3 | Les Misérables — Victor Hugo | 3 | 296.9 | 298.0 | 11 | 2 |
| 4 | Crime and Punishment — Fyodor Dostoyevsky | 4 | 519.7 | 520.8 | 4 | 2 |
| 67 | The Yellow Wall-Paper — Charlotte Perkins Gilman | 72 | 30.5 | 31.4 | 4 | 1 |
| 420 | The Sorrows of Young Werther — Johann Wolfgang von Goethe | 419 | 96.8 | 97.5 | 8 | 1 |
| 843 | The Strange Case of Dr. Jekyll and Mr. Hyde — Robert Louis Stevenson | 867 | 111.1 | 111.6 | 4 | 1 |
| 1103 | The Outsiders — S.E. Hinton | 1103 | 38.5 | 38.5 | 1 | 2 |
| 326 | The Tale of Genji — Murasaki Shikibu | 325 | 10.4 | 10.4 | 3 | 1 |
| 20 | The Adventures of Sherlock Holmes — Arthur Conan Doyle | 20 | 86.7 | 86.7 | 1 | 1 |
| 458 | Flowers for Algernon — Daniel Keyes | 458 | 48.3 | 48.3 | 1 | 1 |
| 752 | The Turn of the Screw — Henry James | 752 | 54.4 | 54.4 | 0 | 1 |
| 61 | The Return of Sherlock Holmes — Arthur Conan Doyle | 61 | 27.2 | 27.2 | 0 | 1 |
| 815 | Charlotte's Web — E.B. White | 815 | 59.6 | 59.6 | 0 | 1 |

## Low-English-share books in the merged top 200

Metadata language is missing for many editions and is not reader nationality; this table is a fragmentation diagnostic, not a cultural-quality measure.

| # | book | editions | known languages | English metadata-rating share | dominant-language share |
|---:|---|---:|---:|---:|---:|
| 38 | The Overcoat — Nikolai Gogol | 35 | 15 | 6% | 46% |
| 82 | The Selected Poetry of Rainer Maria Rilke — Rainer Maria Rilke | 3 | 1 | 0% | 100% |
| 93 | Purgatorio (The Divine Comedy, #2) — Dante Alighieri | 36 | 9 | 11% | 88% |
| 94 | Death on the Installment Plan — Louis-Ferdinand Celine | 10 | 5 | 0% | 52% |
| 115 | The Grand Inquisitor — Fyodor Dostoyevsky | 6 | 2 | 0% | 62% |
| 124 | A Hunger Artist — Franz Kafka | 9 | 5 | 7% | 47% |
| 130 | Sobre héroes y tumbas — Ernesto Sabato | 19 | 10 | 0% | 96% |
| 132 | The Insulted and Humiliated — Fyodor Dostoyevsky | 28 | 12 | 0% | 69% |
| 133 | Ubik — Philip K. Dick | 63 | 15 | 10% | 87% |
| 153 | Tutunamayanlar — Oguz Atay | 2 | 2 | 0% | 100% |

This resolves only known duplicate links. Separate work IDs with translated titles cannot be safely merged from title text alone; external identifiers or manual review would be required before changing the point model.

# Temporal trajectories and enthusiast self-selection

## Scope

This audit uses full-dataset detailed timestamps for the exact-estimator candidate books, weighted by continuous jury-inclusion probability. The primary clock is `date_added`, excluding a user's first account week and their largest same-day import. Early and late estimates are the first and last temporal quintiles of 5★ versus ≤3★ events. They diagnose selection trajectories; they are not replacements for the community-equalized canon score.

- Broad users profiled: **20,000**; rating events: **6,672,078**.
- Users with ≥20 events whose largest day holds ≥50%: **37.9%**; their share of soft jury mass: **40.1%**.
- Candidate user-work events after edition collapse: **1,466,226**.

## Timestamp-definition sensitivity

| definition | estimable | common | delta ρ | median |Δ difference| | sign agreement |
|---|---:|---:|---:|---:|---:|
| added_all | 1133 | 875 | 0.660 | 0.070 | 74.3% |
| added_no_bulk_users | 1085 | 875 | 0.678 | 0.074 | 73.5% |
| added_post_onboarding | 875 | 875 | 1.000 | 0.000 | 100.0% |
| updated_all | 1132 | 875 | 0.599 | 0.074 | 72.1% |
| read_available | 361 | 361 | 0.373 | 0.101 | 63.4% |

## Calendar holdout stability

| eras | rankable | common | score ρ | J@50 | J@200 | RBO |
|---|---:|---:|---:|---:|---:|---:|
| 2011_2013 → 2014_2015 | 872→584 | 559 | 0.839 | 0.266 | 0.476 | 0.396 |
| 2014_2015 → 2016_2017 | 584→329 | 313 | 0.771 | 0.282 | 0.418 | 0.392 |

## Direction-consistent early-to-late declines in the exact top 200

| book | exact rank | early p5 | late p5 | central change | path range | Δ jury-q |
|---|---:|---:|---:|---:|---:|---:|
| Cyrano de Bergerac — Edmond Rostand | 61 | 0.951 | 0.505 | -0.446 | -0.446–-0.340 | -0.068 |
| Nausea — Jean-Paul Sartre | 193 | 0.497 | 0.300 | -0.196 | -0.196–-0.050 | -0.062 |
| Candide — Voltaire | 158 | 0.671 | 0.495 | -0.175 | -0.175–-0.066 | +0.123 |
| Rosencrantz and Guildenstern Are Dead — Tom Stoppard | 125 | 0.813 | 0.638 | -0.174 | -0.236–-0.174 | -0.036 |
| Dubliners — James Joyce | 132 | 0.698 | 0.540 | -0.158 | -0.158–-0.045 | -0.041 |
| To the Lighthouse — Virginia Woolf | 52 | 0.800 | 0.642 | -0.158 | -0.158–-0.049 | +0.034 |
| Twelfth Night — William Shakespeare | 107 | 0.667 | 0.522 | -0.145 | -0.158–-0.074 | -0.038 |
| Infinite Jest — David Foster Wallace | 19 | 0.820 | 0.677 | -0.143 | -0.143–-0.022 | +0.052 |
| Cat's Cradle — Kurt Vonnegut Jr. | 122 | 0.538 | 0.396 | -0.142 | -0.142–-0.127 | +0.014 |
| A Streetcar Named Desire — Tennessee Williams | 40 | 0.817 | 0.677 | -0.140 | -0.140–-0.024 | -0.003 |
| The Sense of an Ending — Julian Barnes | 178 | 0.363 | 0.229 | -0.134 | -0.159–-0.090 | +0.086 |
| Swann's Way (In Search of Lost Time, #1) — Marcel Proust | 36 | 0.879 | 0.751 | -0.128 | -0.128–-0.034 | -0.014 |
| The Decameron — Giovanni Boccaccio | 94 | 0.712 | 0.586 | -0.126 | -0.209–-0.124 | +0.044 |
| The Gambler — Fyodor Dostoyevsky | 165 | 0.420 | 0.297 | -0.122 | -0.179–-0.122 | -0.214 |
| The English Patient — Michael Ondaatje | 175 | 0.412 | 0.295 | -0.118 | -0.118–-0.058 | +0.051 |
| Songs of Innocence and of Experience — William Blake | 33 | 0.911 | 0.797 | -0.114 | -0.162–-0.098 | -0.095 |
| Peter Pan — J.M. Barrie | 98 | 0.570 | 0.465 | -0.105 | -0.136–-0.048 | +0.073 |
| The Death of Ivan Ilych — Leo Tolstoy | 11 | 0.771 | 0.666 | -0.104 | -0.104–-0.023 | +0.025 |
| Waiting for Godot — Samuel Beckett | 105 | 0.683 | 0.583 | -0.100 | -0.100–-0.021 | +0.081 |
| Kafka on the Shore — Haruki Murakami | 183 | 0.512 | 0.416 | -0.096 | -0.154–-0.025 | +0.042 |

## Direction-consistent early-to-late rises in the exact top 200

| book | exact rank | early p5 | late p5 | central change | path range | Δ jury-q |
|---|---:|---:|---:|---:|---:|---:|
| The God of Small Things — Arundhati Roy | 150 | 0.302 | 0.668 | +0.365 | +0.113–+0.365 | +0.109 |
| White Fang — Jack London | 154 | 0.178 | 0.541 | +0.364 | +0.328–+0.364 | -0.001 |
| The Hound of the Baskervilles — Arthur Conan Doyle | 109 | 0.304 | 0.603 | +0.299 | +0.168–+0.307 | +0.046 |
| The Poisonwood Bible — Barbara Kingsolver | 172 | 0.322 | 0.603 | +0.281 | +0.133–+0.281 | +0.115 |
| For Whom the Bell Tolls — Ernest Hemingway | 126 | 0.203 | 0.480 | +0.276 | +0.073–+0.276 | +0.033 |
| The Phantom of the Opera — Gaston Leroux | 164 | 0.020 | 0.292 | +0.272 | +0.101–+0.272 | +0.008 |
| The House of the Spirits — Isabel Allende | 176 | 0.281 | 0.548 | +0.267 | +0.108–+0.267 | +0.197 |
| Chronicle of a Death Foretold — Gabriel Garcia Marquez | 119 | 0.359 | 0.611 | +0.252 | +0.032–+0.252 | -0.019 |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 45 | 0.615 | 0.854 | +0.239 | +0.118–+0.239 | +0.115 |
| Flowers for Algernon — Daniel Keyes | 139 | 0.314 | 0.549 | +0.234 | +0.143–+0.234 | +0.044 |
| The Portrait of a Lady — Henry James | 134 | 0.409 | 0.640 | +0.232 | +0.040–+0.232 | +0.181 |
| The Count of Monte Cristo — Alexandre Dumas | 51 | 0.601 | 0.815 | +0.214 | +0.183–+0.214 | -0.001 |
| Dune (Dune Chronicles #1) — Frank Herbert | 106 | 0.318 | 0.528 | +0.210 | +0.048–+0.210 | -0.062 |
| The Picture of Dorian Gray — Oscar Wilde | 127 | 0.426 | 0.629 | +0.202 | +0.008–+0.202 | -0.090 |
| Around the World in Eighty Days (Extraordinary Voyages, #11) — Jules Verne | 195 | 0.337 | 0.534 | +0.197 | +0.086–+0.197 | +0.105 |
| The Prophet — Kahlil Gibran | 129 | 0.326 | 0.520 | +0.194 | +0.078–+0.194 | -0.092 |
| All Quiet on the Western Front — Erich Maria Remarque | 56 | 0.510 | 0.696 | +0.186 | +0.185–+0.233 | -0.118 |
| Blindness — Jose Saramago | 55 | 0.435 | 0.616 | +0.181 | +0.173–+0.238 | -0.008 |
| The Jungle — Upton Sinclair | 156 | 0.305 | 0.484 | +0.179 | +0.165–+0.210 | -0.093 |
| The Call of the Wild — Jack London | 194 | 0.274 | 0.447 | +0.173 | +0.152–+0.173 | +0.129 |

## Decision

Temporal data should now be retained as a diagnostic and book-level trajectory annotation, not folded directly into the canonical score. Bulk importing is common, and early/late direction is materially sensitive to which imperfect Goodreads clock is used. Direction-consistent paths can flag plausible enthusiast-first inflation or later broadening for further sensitivity analysis; inconsistent paths should increase uncertainty rather than move a book up or down.

## Interpretation limits

- Goodreads timestamps identify recording chronology, not exposure or the original moment a rating was formed.
- Calendar eras mix audience change with platform growth and cohort replacement.
- `read_at` is user-entered and missing nonrandomly; agreement across timestamp paths is stronger evidence than any one path.
- A decline bounds plausible enthusiast-first inflation but does not prove that absent readers would dislike the book.

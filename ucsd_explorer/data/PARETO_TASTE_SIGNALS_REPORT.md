# Pareto — taste signals (positives + anti + normie dominance)

## What this measures

- **Positive:** all-genre works by literary_poll authors only (n=40, lit-2014-2024 mint; literary_sf ignored).
- **Anti-signal:** all-genre works by non_literary authors (n=250).
- **Normie canon matched:** 49 titles; **fillers** (canon ∉ positive): 31.
- Ranking / probes are **all-genres** (no SF prevalence gate).
- Anti-signals scored through **top 1000** (fetch limit 2000); positives/fillers still head-focused.
- Normie titles that are also positive literary (e.g. many school classics by poll authors) may rank high without penalty.
- Penalty targets **filler dominance** in top 20/50, not “any canon book high”.

## Probe samples

### Positives (head)

- The Great Gatsby — F. Scott Fitzgerald (literary_poll)
- 1984 — George Orwell (literary_poll)
- Animal Farm — George Orwell (literary_poll)
- The Catcher in the Rye — J.D. Salinger (literary_poll)
- Romeo and Juliet — William Shakespeare (literary_poll)
- Of Mice and Men — John Steinbeck (literary_poll)
- Wuthering Heights — Emily Bronte (literary_poll)
- Brave New World — Aldous Huxley (literary_poll)

### Anti (head)

- Harry Potter and the Sorcerer's Stone (Harry Potter, #1) — J.K. Rowling
- The Hunger Games (The Hunger Games, #1) — Suzanne Collins
- Twilight (Twilight, #1) — Stephenie Meyer
- Harry Potter and the Prisoner of Azkaban (Harry Potter, #3) — J.K. Rowling
- Harry Potter and the Chamber of Secrets (Harry Potter, #2) — J.K. Rowling
- Harry Potter and the Goblet of Fire (Harry Potter, #4) — J.K. Rowling
- Catching Fire (The Hunger Games, #2) — Suzanne Collins
- Harry Potter and the Deathly Hallows (Harry Potter, #7) — J.K. Rowling

### Normie fillers (head)

- Harry Potter and the Sorcerer's Stone (Harry Potter, #1) — J.K. Rowling
- The Hunger Games (The Hunger Games, #1) — Suzanne Collins
- To Kill a Mockingbird — Harper Lee
- Pride and Prejudice — Jane Austen
- The Hobbit — J.R.R. Tolkien
- The Da Vinci Code (Robert Langdon, #2) — Dan Brown
- Lord of the Flies — William Golding
- The Alchemist — Paulo Coelho

## Core (depth × purity × deweight)

Runs: 24. Pareto front: `core_d0_p0_dew25`, `core_d0_p0_dew50`, `core_d0_p35_dew0`, `core_d0_p35_dew25`, `core_d0_p35_dew50`, `core_d40_p0_dew0`, `core_d40_p35_dew0`

- **Utopia knee:** `core_d0_p0_dew25` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Product:** `core_d0_p0_dew25` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Quality-lean:** `core_d40_p0_dew0` Q=15.07 geo_n=337 pos50=4 anti50=0 anti1000=3 anti_med=1249 filler%=2 anti1000%=0.3 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 0, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best quality:** `core_d40_p0_dew0` Q=15.07 geo_n=337 pos50=4 anti50=0 anti1000=3 anti_med=1249 filler%=2 anti1000%=0.3 params={'normie_depth': 40, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 0, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best mass:** `core_d0_p0_dew50` Q=5.24 geo_n=862 pos50=4 anti50=0 anti1000=9 anti_med=228 filler%=2 anti1000%=3.9 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 50, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest filler share:** `core_d0_p0_dew0` Q=-7.46 geo_n=563 pos50=0 anti50=2 anti1000=3 anti_med=1181 filler%=0 anti1000%=0.3 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 0, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest anti share:** `core_d0_p0_dew0` Q=-7.46 geo_n=563 pos50=0 anti50=2 anti1000=3 anti_med=1181 filler%=0 anti1000%=0.3 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 0, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}

| label | Q | geo_n | pos50 | anti50 | anti500 | anti1000 | anti_med | pos% | anti%1000 | filler% | dom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| core_d40_p0_dew0 | 15.07 | 337 | 4 | 0 | 3 | 3 | 1249 | 8 | 0.3 | 2 | 0.0 |
| core_d40_p35_dew0 | 15.07 | 337 | 4 | 0 | 3 | 3 | 1249 | 8 | 0.3 | 2 | 0.0 |
| core_d0_p35_dew0 | 13.36 | 351 | 3 | 0 | 3 | 3 | 1320 | 6 | 0.3 | 2 | 0.0 |
| core_d40_p55_dew0 | 12.04 | 309 | 4 | 0 | 3 | 9 | 950 | 8 | 0.9 | 2 | 0.0 |
| core_d0_p55_dew0 | 12.00 | 304 | 3 | 0 | 3 | 6 | 993 | 6 | 0.6 | 2 | 0.0 |
| core_d0_p0_dew25 | 10.09 | 569 | 4 | 0 | 3 | 10 | 609 | 8 | 1.6 | 0 | 0.0 |
| core_d0_p35_dew25 | 10.09 | 569 | 4 | 0 | 3 | 10 | 609 | 8 | 1.6 | 0 | 0.0 |
| core_d40_p0_dew25 | 10.03 | 534 | 4 | 0 | 3 | 10 | 602 | 8 | 1.6 | 0 | 0.0 |
| core_d40_p35_dew25 | 10.03 | 534 | 4 | 0 | 3 | 10 | 602 | 8 | 1.6 | 0 | 0.0 |
| core_d0_p55_dew25 | 9.62 | 420 | 4 | 0 | 3 | 10 | 558 | 8 | 1.8 | 0 | 0.0 |
| core_d40_p55_dew25 | 9.61 | 391 | 4 | 0 | 3 | 10 | 556 | 8 | 1.8 | 0 | 0.0 |
| core_d0_p0_dew50 | 5.24 | 862 | 4 | 0 | 9 | 9 | 228 | 8 | 3.9 | 2 | 0.0 |
| core_d0_p35_dew50 | 5.24 | 862 | 4 | 0 | 9 | 9 | 228 | 8 | 3.9 | 2 | 0.0 |
| core_d40_p0_dew50 | 5.24 | 795 | 4 | 0 | 9 | 9 | 228 | 8 | 3.9 | 2 | 0.0 |
| core_d40_p35_dew50 | 5.24 | 795 | 4 | 0 | 9 | 9 | 228 | 8 | 3.9 | 2 | 0.0 |
| core_d0_p55_dew50 | 5.20 | 634 | 4 | 0 | 9 | 9 | 224 | 8 | 4.0 | 0 | 0.0 |
| core_d40_p55_dew50 | 5.20 | 594 | 4 | 0 | 9 | 9 | 224 | 8 | 4.0 | 0 | 0.0 |
| core_d0_p75_dew25 | 5.11 | 211 | 4 | 0 | 9 | 9 | 258 | 8 | 3.4 | 0 | 0.0 |
| core_d0_p75_dew0 | 4.82 | 160 | 4 | 0 | 10 | 10 | 451 | 8 | 2.1 | 0 | 0.0 |
| core_d40_p75_dew0 | 4.60 | 154 | 4 | 0 | 10 | 10 | 419 | 8 | 2.3 | 0 | 0.0 |

## Deweight axis (d0/p55/s0)

Runs: 6. Pareto front: `dew_0`, `dew_15`, `dew_25`, `dew_40`, `dew_80`

- **Utopia knee:** `dew_15` Q=11.91 geo_n=401 pos50=4 anti50=0 anti1000=10 anti_med=771 filler%=0 anti1000%=1.3 params={'normie_depth': 0, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 15, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Product:** `dew_15` Q=11.91 geo_n=401 pos50=4 anti50=0 anti1000=10 anti_med=771 filler%=0 anti1000%=1.3 params={'normie_depth': 0, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 15, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Quality-lean:** `dew_15` Q=11.91 geo_n=401 pos50=4 anti50=0 anti1000=10 anti_med=771 filler%=0 anti1000%=1.3 params={'normie_depth': 0, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 15, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best quality:** `dew_0` Q=12.00 geo_n=304 pos50=3 anti50=0 anti1000=6 anti_med=993 filler%=2 anti1000%=0.6 params={'normie_depth': 0, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 0, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best mass:** `dew_80` Q=4.86 geo_n=1093 pos50=6 anti50=0 anti1000=4 anti_med=67 filler%=4 anti1000%=5.8 params={'normie_depth': 0, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 80, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest filler share:** `dew_15` Q=11.91 geo_n=401 pos50=4 anti50=0 anti1000=10 anti_med=771 filler%=0 anti1000%=1.3 params={'normie_depth': 0, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 15, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest anti share:** `dew_80` Q=4.86 geo_n=1093 pos50=6 anti50=0 anti1000=4 anti_med=67 filler%=4 anti1000%=5.8 params={'normie_depth': 0, 'normie_purity': 55, 'curator_strictness': 0, 'curator_deweight': 80, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}

| label | Q | geo_n | pos50 | anti50 | anti500 | anti1000 | anti_med | pos% | anti%1000 | filler% | dom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dew_0 | 12.00 | 304 | 3 | 0 | 3 | 6 | 993 | 6 | 0.6 | 2 | 0.0 |
| dew_15 | 11.91 | 401 | 4 | 0 | 3 | 10 | 771 | 8 | 1.3 | 0 | 0.0 |
| dew_25 | 9.62 | 420 | 4 | 0 | 3 | 10 | 558 | 8 | 1.8 | 0 | 0.0 |
| dew_40 | 6.23 | 527 | 4 | 0 | 10 | 10 | 328 | 8 | 3.0 | 0 | 0.0 |
| dew_80 | 4.86 | 1093 | 6 | 0 | 4 | 4 | 67 | 12 | 5.8 | 4 | 0.0 |
| dew_60 | 4.37 | 754 | 5 | 0 | 8 | 8 | 146 | 10 | 5.3 | 2 | 0.0 |

## Purity axis (d0/dew25)

Runs: 7. Pareto front: `pur_0`, `pur_20`, `pur_35`

- **Utopia knee:** `pur_0` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Product:** `pur_0` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Quality-lean:** `pur_0` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best quality:** `pur_0` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best mass:** `pur_0` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest filler share:** `pur_0` Q=10.09 geo_n=569 pos50=4 anti50=0 anti1000=10 anti_med=609 filler%=0 anti1000%=1.6 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest anti share:** `pur_90` Q=5.32 geo_n=116 pos50=4 anti50=0 anti1000=4 anti_med=104 filler%=2 anti1000%=3.7 params={'normie_depth': 0, 'normie_purity': 90, 'curator_strictness': 0, 'curator_deweight': 25, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}

| label | Q | geo_n | pos50 | anti50 | anti500 | anti1000 | anti_med | pos% | anti%1000 | filler% | dom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pur_0 | 10.09 | 569 | 4 | 0 | 3 | 10 | 609 | 8 | 1.6 | 0 | 0.0 |
| pur_20 | 10.09 | 569 | 4 | 0 | 3 | 10 | 609 | 8 | 1.6 | 0 | 0.0 |
| pur_35 | 10.09 | 569 | 4 | 0 | 3 | 10 | 609 | 8 | 1.6 | 0 | 0.0 |
| pur_55 | 9.62 | 420 | 4 | 0 | 3 | 10 | 558 | 8 | 1.8 | 0 | 0.0 |
| pur_65 | 7.36 | 295 | 4 | 0 | 10 | 10 | 443 | 8 | 2.2 | 0 | 0.0 |
| pur_90 | 5.32 | 116 | 4 | 0 | 4 | 4 | 104 | 8 | 3.7 | 2 | 0.0 |
| pur_75 | 5.11 | 211 | 4 | 0 | 9 | 9 | 258 | 8 | 3.4 | 0 | 0.0 |

## Taste-zero deweight

Runs: 4. Pareto front: `zerotaste_dew_100`

- **Utopia knee:** `zerotaste_dew_100` Q=24.56 geo_n=3059 pos50=7 anti50=0 anti1000=0 anti_med=None filler%=10 anti1000%=0.0 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Product:** `zerotaste_dew_100` Q=24.56 geo_n=3059 pos50=7 anti50=0 anti1000=0 anti_med=None filler%=10 anti1000%=0.0 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Quality-lean:** `zerotaste_dew_100` Q=24.56 geo_n=3059 pos50=7 anti50=0 anti1000=0 anti_med=None filler%=10 anti1000%=0.0 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best quality:** `zerotaste_dew_100` Q=24.56 geo_n=3059 pos50=7 anti50=0 anti1000=0 anti_med=None filler%=10 anti1000%=0.0 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Best mass:** `zerotaste_dew_100` Q=24.56 geo_n=3059 pos50=7 anti50=0 anti1000=0 anti_med=None filler%=10 anti1000%=0.0 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest filler share:** `zerotaste_dew_0` Q=-7.46 geo_n=563 pos50=0 anti50=2 anti1000=3 anti_med=1181 filler%=0 anti1000%=0.3 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 0, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}
- **Lowest anti share:** `zerotaste_dew_100` Q=24.56 geo_n=3059 pos50=7 anti50=0 anti1000=0 anti_med=None filler%=10 anti1000%=0.0 params={'normie_depth': 0, 'normie_purity': 0, 'curator_strictness': 0, 'curator_deweight': 100, 'coverage_weight': 0.0, 'min_votes': 25, 'max_n': 0, 'bayesian_m': 30}

| label | Q | geo_n | pos50 | anti50 | anti500 | anti1000 | anti_med | pos% | anti%1000 | filler% | dom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zerotaste_dew_100 | 24.56 | 3059 | 7 | 0 | 0 | 0 | None | 33 | 0.0 | 10 | 0.0 |
| zerotaste_dew_25 | 10.09 | 569 | 4 | 0 | 3 | 10 | 609 | 8 | 1.6 | 0 | 0.0 |
| zerotaste_dew_50 | 5.24 | 862 | 4 | 0 | 9 | 9 | 228 | 8 | 3.9 | 2 | 0.0 |
| zerotaste_dew_0 | -7.46 | 563 | 0 | 2 | 3 | 3 | 1181 | 0 | 0.3 | 0 | 0.0 |

## Takeaways

- Old pareto_post_fix.py did NOT use taste lists; this one does.
- Prefer settings with high pos_share / low anti_share / low filler_share.
- Normie∩positive (e.g. poll authors’ school titles) allowed high; fillers are the dominance risk.
- Core best quality: core_d40_p0_dew0 (filler%=2, anti%=0).

Full data: `pareto_taste_signals.json`.


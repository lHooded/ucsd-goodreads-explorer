# Deep curator size × weight sweep (pivotal)

Before reverse-engineering a new jury: does capping deep curators to ~focus size,
or turning weights into equal votes, hurt pairwise quality?

## Weight mass (caution)

- Deep pool: **19,841** users; stored weight sum ≈ 4985
- Cumulative mass of top-k:

- top   500: **13.4%** of stored mass
- top  1000: **22.1%** of stored mass
- top  2000: **35.0%** of stored mass
- top  3000: **45.0%** of stored mass
- top  4774: **58.4%** of stored mass
- top  6000: **65.8%** of stored mass
- top  8000: **75.4%** of stored mass
- top 10000: **82.8%** of stored mass
- top 15000: **94.9%** of stored mass
- top 19841: **100.0%** of stored mass

Kish n_eff if we power-weight stored scores:

- expo=0.0: n_eff ≈ **19841**
- expo=0.6: n_eff ≈ **14759**
- expo=1.0: n_eff ≈ **9401**
- expo=2.0: n_eff ≈ **2122**
- expo=4.0: n_eff ≈ **106**

App guidance historically: prefer **weighted** over equal-elite; deweight≈15–25
corresponds to soft power emphasis (expo ~0.6–1), not a hard top-4.8k gate.

## Weird pockets in the mint (deep ≠ perfect)

- com_share ≥ 0.15: **1,881** users (mean n_deep=8.5)
- deep_share ≤ 0.40 (near floor): **3,099**
- n_rated ≥ 2000: **103** (p99≈1501)
- top500 vs bottom-half of deep: deep_share 0.75 vs 0.52, n_deep 27.2 vs 5.3

## Pairwise sweep

| cap | mode | pos50 | sticky50 | fill50 | held@50 | held@200 | J50 vs full+w |
|---|---|---:|---:|---:|---:|---:|---:|
| 2000 | equal | 42 | 12 | 0 | 0.465 | 0.721 | 0.333 |
| 2000 | stored_w | 44 | 11 | 0 | 0.442 | 0.744 | 0.351 |
| 2000 | pow2 | 45 | 11 | 0 | 0.419 | 0.721 | 0.333 |
| 3000 | equal | 41 | 12 | 0 | 0.419 | 0.674 | 0.389 |
| 3000 | stored_w | 43 | 11 | 0 | 0.419 | 0.698 | 0.389 |
| 3000 | pow2 | 43 | 11 | 0 | 0.372 | 0.698 | 0.389 |
| 4774 | equal | 38 | 9 | 0 | 0.326 | 0.651 | 0.449 |
| 4774 | stored_w | 38 | 9 | 0 | 0.326 | 0.651 | 0.493 |
| 4774 | pow2 | 39 | 8 | 0 | 0.326 | 0.628 | 0.429 |
| 6000 | equal | 37 | 7 | 0 | 0.302 | 0.628 | 0.515 |
| 6000 | stored_w | 34 | 8 | 0 | 0.279 | 0.628 | 0.562 |
| 6000 | pow2 | 38 | 8 | 0 | 0.302 | 0.605 | 0.471 |
| 8000 | equal | 33 | 6 | 0 | 0.256 | 0.628 | 0.587 |
| 8000 | stored_w | 32 | 7 | 0 | 0.233 | 0.605 | 0.613 |
| 8000 | pow2 | 33 | 5 | 0 | 0.233 | 0.605 | 0.538 |
| 10000 | equal | 32 | 5 | 0 | 0.256 | 0.605 | 0.587 |
| 10000 | stored_w | 31 | 7 | 0 | 0.233 | 0.605 | 0.639 |
| 10000 | pow2 | 28 | 4 | 0 | 0.116 | 0.558 | 0.538 |
| 15000 | equal | 27 | 5 | 0 | 0.209 | 0.535 | 0.613 |
| 15000 | stored_w | 26 | 4 | 0 | 0.163 | 0.535 | 0.852 |
| 15000 | pow2 | 23 | 2 | 0 | 0.093 | 0.535 | 0.667 |
| all | equal | 26 | 4 | 0 | 0.140 | 0.465 | 0.538 |
| all | stored_w | 24 | 4 | 0 | 0.163 | 0.512 | 1.000 |
| all | pow2 | 21 | 2 | 0 | 0.093 | 0.442 | 0.613 |

## Reference head (all deep, stored weight)

- 1. Crime and Punishment — Fyodor Dostoyevsky
- 2. The Brothers Karamazov — Fyodor Dostoyevsky
- 3. Four Quartets — T.S. Eliot
- 4. 2666 — Roberto Bolano
- 5. Tutunamayanlar — Oguz Atay
- 6. Giovanni's Room — James     Baldwin
- 7. Death and the Dervish — Mesa Selimovic
- 8. Stoner — John  Williams
- 9. Tehlikeli Oyunlar — Oguz Atay
- 10. The Book of Disquiet — Fernando Pessoa
- 11. Infinite Jest — David Foster Wallace
- 12. War and Peace — Leo Tolstoy

## Recommendation (for reverse-engineering target)

- Best overall in sweep: **cap=2000 / equal** (held@50=0.465, pos50=42)
- Best among full-pool weighted: **stored_w** (held@50=0.163, pos50=24)
- Best equal-vote cap: **2000** (held@50=0.465, pos50=42)

### Critical caution (do not skip)

1. **Poll held-out / pos50 are contaminated teachers.** Deep curators are minted from poll-depth signals. Smaller elites will look better on those probes partly because they are the densest poll-aligned core.
2. **Wider deep pools dilute pairwise and admit local canons** (full+weighted head includes Turkish literary islands) — mint imperfection to flag.
3. **App deweight ≠ top-4.8k hard gate.** Soft weighting keeps many users at low mass (Kish n_eff ~9–15k). Hard-capping to focus size threw away ~40%+ of mass.
4. **For reverse-engineering:** prefer teacher ≈ top **3–8k** by weight (before dilution) *or* filtered full deep + soft weights; score candidate juries on overlap with deep + head sanity, not only poll probes. Watch shortcuts that recreate mint score ranking.

Interpret cautiously: if full+weighted matches or beats small equal caps, **do not**
reverse-engineer only a tiny equal elite — use the fuller weighted deep pool as the
teacher signal (or a mass-matched soft target), and watch for shortcuts that only
recover the top few thousand heaviest mint scores.

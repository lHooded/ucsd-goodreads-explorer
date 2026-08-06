# Feature sensitivity & rank trajectories

Probe piles are **fallible** — Q/pos50 are reference signals, not truth.
Impact is judged by ranking geometry change (Jaccard, Kendall, watchlist Δrank)
as much as by probe scores.

## Headline findings

1. **Most load-bearing for ranking geometry** (drop → largest reshuffle of top200):
   `midpop_span_per_logn5`, `binge_max_5`, `author_hhi_5`, `series_share_5`, `mean_pub_year_5`.
2. **Most load-bearing for noisy poll Q** (drop → biggest Q drop):
   `mean_pub_year_5` (−39), `binge_max_5` (−21), `series_share_5` (−12), `n_megastar_authors_5` (−11).
3. **Geometry ≠ poll:** dropping `midpop_span` reshuffles ranks hard (mean|Δr|≈218, τ≈0.45) but Q slightly *rises*. Don’t optimize Q alone.
4. **Your projectile intuition works:** as `λ_anti` ↑, experimental/modernist watch titles **rise** (Dhalgren 1759→1169, Infinite Jest 536→274, Gravity’s Rainbow 844→498, Stoner 430→202) while syllabus anchors stay flat (Ulysses/Moby-Dick/Lolita ~1–7). Hate U Give is **u-shaped** (best mid-λ, worse at extremes).
5. **Stricter focus cohort (`top_frac` ↓)** also lifts Dhalgren (1524→678) and Gravity’s Rainbow — until the cohort gets too small and Q collapses (`top_frac=0.015`).

## Baseline (contrastive unseeded)

- Q=72.0 pos50=22 anti50=0 classic50=22 normie50=6

Watchlist ranks:

- Dhalgren: **1524** (Dhalgren — Samuel R. Delany)
- Moby-Dick: **2** (Moby-Dick or, The Whale — Herman Melville)
- Ulysses: **1** (Ulysses — James Joyce)
- Lolita: **6** (Lolita — Vladimir Nabokov)
- The Brothers Karamazov: **34** (The Brothers Karamazov — Fyodor Dostoyevsky)
- 1984: **None** (1984 — George Orwell)
- The Catcher in the Rye: **None** (The Catcher in the Rye — J.D. Salinger)
- The Hate U Give: **126** (The Hate U Give — Angie Thomas)
- Words of Radiance: **None** (Words of Radiance (The Stormlight Archive, #2) — Brandon Sanderson)
- A Court of Mist and Fury: **None** (A Court of Mist and Fury (A Court of Thorns and Roses, #2) — Sarah J. Maas)
- Infinite Jest: **409** (Infinite Jest — David Foster Wallace)
- Gravity's Rainbow: **632** (Gravity's Rainbow — Thomas Pynchon)
- Stoner: **267** (Stoner — John  Williams)
- The Book of Disquiet: **145** (The Book of Disquiet — Fernando Pessoa)

## Feature ablation (zero weight in classic+anti+normie terms)

Larger `mean|Δrank|` / smaller Jaccard ⇒ feature more load-bearing for the ranking.

| feature | in | ΔQ | Δpos50 | J@50 | mean\|Δr\|@200 | τ@200 |
|---|---|---:|---:|---:|---:|---:|
| midpop_span_per_logn5 | classic,normie | +2.7 | +1 | 0.82 | 217.9 | 0.448 |
| binge_max_5 | anti | -21.0 | -2 | 0.68 | 157.1 | 0.459 |
| author_hhi_5 | classic,anti | +1.9 | +1 | 0.70 | 106.8 | 0.591 |
| series_share_5 | classic,anti | -11.5 | -2 | 0.66 | 94.1 | 0.558 |
| mean_pub_year_5 | classic,anti | -38.6 | -8 | 0.70 | 91.1 | 0.556 |
| binge_mean_5 | classic,anti | -1.6 | +3 | 0.84 | 65.3 | 0.667 |
| singleton_author_share_5 | classic,anti | -5.9 | +1 | 0.80 | 50.0 | 0.712 |
| mean_logn_5 | classic,normie | +1.8 | +1 | 0.94 | 36.2 | 0.778 |
| author_div_5 | classic,anti | -1.9 | +2 | 0.90 | 31.7 | 0.791 |
| depth_ge4 | classic,normie | -0.7 | +1 | 0.94 | 28.4 | 0.787 |
| p5_blockbuster | normie | -5.7 | +1 | 0.96 | 25.1 | 0.848 |
| n_megastar_authors_5 | normie | -11.1 | +0 | 0.94 | 20.9 | 0.838 |
| mega_catalog_share_5 | classic,normie | -7.1 | +0 | 0.96 | 17.7 | 0.823 |
| mid_catalog_share_5 | classic | +0.2 | +0 | 0.98 | 11.2 | 0.889 |
| std_logn_5 | classic | -0.5 | +0 | 1.00 | 7.4 | 0.906 |

### Watchlist moves when feature dropped (Δrank; − = rose)

**drop `midpop_span_per_logn5`** (ΔQ=+2.7)
- Dhalgren: 1524 → 642 (Δ -882)
- The Brothers Karamazov: 34 → 12 (Δ -22)
- The Hate U Give: 126 → 97 (Δ -29)
- Infinite Jest: 409 → 113 (Δ -296)
- Gravity's Rainbow: 632 → 243 (Δ -389)
- Stoner: 267 → 154 (Δ -113)
- The Book of Disquiet: 145 → 66 (Δ -79)

**drop `binge_max_5`** (ΔQ=-21.0)
- Dhalgren: 1524 → 1542 (Δ +18)
- Ulysses: 1 → 468 (Δ +467)
- The Brothers Karamazov: 34 → 288 (Δ +254)
- The Hate U Give: 126 → 209 (Δ +83)
- Infinite Jest: 409 → 535 (Δ +126)
- Gravity's Rainbow: 632 → 765 (Δ +133)
- Stoner: 267 → 364 (Δ +97)
- The Book of Disquiet: 145 → 224 (Δ +79)

**drop `author_hhi_5`** (ΔQ=+1.9)
- Dhalgren: 1524 → 1162 (Δ -362)
- Ulysses: 1 → 12 (Δ +11)
- The Brothers Karamazov: 34 → 94 (Δ +60)
- Infinite Jest: 409 → 357 (Δ -52)
- Gravity's Rainbow: 632 → 544 (Δ -88)
- Stoner: 267 → 208 (Δ -59)
- The Book of Disquiet: 145 → 114 (Δ -31)

**drop `series_share_5`** (ΔQ=-11.5)
- The Brothers Karamazov: 34 → 64 (Δ +30)
- The Hate U Give: 126 → 426 (Δ +300)
- Infinite Jest: 409 → 465 (Δ +56)
- Gravity's Rainbow: 632 → 830 (Δ +198)
- The Book of Disquiet: 145 → 138 (Δ -7)

**drop `mean_pub_year_5`** (ΔQ=-38.6)
- Dhalgren: 1524 → 1673 (Δ +149)
- Lolita: 6 → 11 (Δ +5)
- The Brothers Karamazov: 34 → 61 (Δ +27)
- The Hate U Give: 126 → 121 (Δ -5)
- Infinite Jest: 409 → 418 (Δ +9)
- Gravity's Rainbow: 632 → 587 (Δ -45)
- Stoner: 267 → 220 (Δ -47)

**drop `binge_mean_5`** (ΔQ=-1.6)
- Dhalgren: 1524 → 1478 (Δ -46)
- Ulysses: 1 → 13 (Δ +12)
- The Brothers Karamazov: 34 → 15 (Δ -19)
- The Hate U Give: 126 → 622 (Δ +496)
- Infinite Jest: 409 → 473 (Δ +64)
- Gravity's Rainbow: 632 → 687 (Δ +55)
- Stoner: 267 → 332 (Δ +65)
- The Book of Disquiet: 145 → 185 (Δ +40)

**drop `singleton_author_share_5`** (ΔQ=-5.9)
- Dhalgren: 1524 → 1361 (Δ -163)
- The Brothers Karamazov: 34 → 23 (Δ -11)
- The Hate U Give: 126 → 783 (Δ +657)
- Infinite Jest: 409 → 492 (Δ +83)
- Gravity's Rainbow: 632 → 732 (Δ +100)
- Stoner: 267 → 352 (Δ +85)
- The Book of Disquiet: 145 → 182 (Δ +37)

**drop `mean_logn_5`** (ΔQ=+1.8)
- Dhalgren: 1524 → 1549 (Δ +25)
- The Brothers Karamazov: 34 → 41 (Δ +7)
- The Hate U Give: 126 → 146 (Δ +20)
- Infinite Jest: 409 → 360 (Δ -49)
- Gravity's Rainbow: 632 → 701 (Δ +69)
- Stoner: 267 → 245 (Δ -22)
- The Book of Disquiet: 145 → 132 (Δ -13)


## Trajectories

### Sweep `lambda_anti`
| λ_anti | Q | pos50 | anti50 | Dhalgren | Ulysses | Hate U Give | ACOTAR |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 58.0 | 21 | 0 | 1759 | 1 | 151 | None |
| 0.30 | 58.0 | 21 | 0 | 1547 | 1 | 146 | None |
| 0.55 | 59.0 | 21 | 0 | 1683 | 2 | 140 | None |
| 0.85 | 72.0 | 22 | 0 | 1524 | 1 | 126 | None |
| 1.15 | 75.2 | 24 | 0 | 1172 | 2 | 124 | None |
| 1.50 | 77.0 | 25 | 0 | 1169 | 3 | 130 | None |
| 2.00 | 75.6 | 24 | 0 | 1169 | 3 | 152 | None |

### Sweep `top_frac`
| top_frac | Q | pos50 | Dhalgren | Moby-Dick | 1984 | Words of Radiance |
|---:|---:|---:|---:|---:|---:|---:|
| 0.120 | 71.8 | 24 | None | 2 | None | None |
| 0.080 | 80.5 | 25 | 1845 | 2 | None | None |
| 0.060 | 72.0 | 22 | 1524 | 2 | None | None |
| 0.040 | 50.7 | 20 | 883 | 1 | None | None |
| 0.025 | 55.6 | 23 | 797 | 1 | None | None |
| 0.015 | 17.4 | 19 | 678 | 2 | None | None |

### Sweep `series_gate`
| series_gate | n_gated | Q | pos50 | Dhalgren | Lolita | ACOTAR |
|---:|---:|---:|---:|---:|---:|---:|
| 0.55 | 144200 | 72.0 | 23 | 1937 | 6 | None |
| 0.45 | 123197 | 73.5 | 23 | 1789 | 6 | None |
| 0.40 | 112327 | 72.0 | 22 | 1524 | 6 | None |
| 0.32 | 92312 | 72.8 | 23 | 987 | 6 | None |
| 0.25 | 73809 | 72.3 | 23 | 805 | 6 | None |
| 0.18 | 52296 | 71.4 | 23 | 632 | 6 | None |

## λ_anti trajectory archetypes (watchlist)

### rising (6)
- Dhalgren: [1759, 1547, 1683, 1524, 1172, 1169, 1169]
- The Brothers Karamazov: [41, 37, 34, 34, 33, 33, 33]
- Infinite Jest: [536, 454, 460, 409, 423, 418, 274]
- Gravity's Rainbow: [844, 819, 729, 632, 628, 559, 498]
- Stoner: [430, 345, 305, 267, 250, 224, 202]
- The Book of Disquiet: [189, 164, 161, 145, 132, 124, 110]

### falling (0)

### u_shaped (1)
- The Hate U Give: [151, 146, 140, 126, 124, 130, 152]

### flat_or_noisy (3)
- Moby-Dick: [2, 2, 1, 2, 3, 2, 2]
- Ulysses: [1, 1, 2, 1, 2, 3, 3]
- Lolita: [6, 6, 6, 6, 6, 7, 7]

### missing (4)
- 1984: [None, None, None, None, None, None, None]
- The Catcher in the Rye: [None, None, None, None, None, None, None]
- Words of Radiance: [None, None, None, None, None, None, None]
- A Court of Mist and Fury: [None, None, None, None, None, None, None]

## Improving accuracy without a trusted canon

### Multi-proxy Pareto, not single Q
Treat literary_poll / anti / normie as noisy voters. Prefer parameter regions that jointly: (a) keep anti50 near 0, (b) don't collapse to only mega-syllabus fillers, (c) stay stable under feature ablation, (d) surface multilingual consecrated works without romance heads.

### Internal consistency / stability as accuracy proxy
Bootstrap users, re-fit or re-rank, measure Jaccard@50 and Kendall on top200. A 'more accurate' metric should be stabler under resampling than a brittle one that overfits pile quirks.

### Trajectory archetypes (your Dhalgren idea)
Sweep a knob (λ_anti, series gate, top_frac). Cluster books by rank path: anti-sensitive risers, syllabus-stable, romance-crashers, mid-peak experimental. Use archetype purity (do risers cohere?) as a structural signal without trusting any single title list.

### Held-out community recovery
From PMI/reflections, freeze non-English literary communities (Arabic, Turkish, …) as unlabeled targets. Metrics that recover them without language labels are discovering real consecration structure.

### Iterative co-training
1) Rank with current metric. 2) Take head ∩ high-stability books as a soft positive expansion (and romance/series head as soft negative). 3) Re-estimate only user-feature weights / gates. 4) Require the next head to improve stability + anti rejection, else reject the step. Stops runaway confirmation if expansion is tiny and audited.

### Human-in-the-loop on trajectories, not on piles
Instead of enlarging lit-2014-2024, label a few trajectory archetypes ('this rising path feels right / wrong'). That supervises the geometry of the metric with less canon politics.

## Practical next data to gather

1. Full trajectory matrices for top~500 baseline books across λ_anti / series_gate / top_frac.
2. Bootstrap stability curves (Jaccard@50 vs resample).
3. Soft labels on a few dozen *paths* (not titles): experimental-riser vs syllabus-flat vs junk-crasher.
4. Multilingual community recovery scores as an external structural check.

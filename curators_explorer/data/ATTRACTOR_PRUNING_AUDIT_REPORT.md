# Attractor-pruning audit: is the valley real?

Three suspicions checked against the gain-hard pruning path: trivial convergence (early freeze), seed echo (survivors are mostly the year jury), and reachability (do random starts find the literary pole without the seed?).

Runtime: **42.5s**.

## 1. Convergence is not trivial

| stage | users | either-fold jury | both-fold jury | step corr iter1 | iter5 | iter20 | retained vs stage start | eff share | users for half mass |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 233,271 | 10.8% | 4.3% | 0.9499 | 0.9965 | 0.999872 | 0.463 | 0.692 | 65,043 |
| 1 | 131,797 | 19.1% | 7.5% | 0.9864 | 0.9975 | 0.999179 | 0.613 | 0.698 | 36,653 |
| 2 | 76,329 | 33.0% | 13.0% | 0.9925 | 0.9995 | 0.998926 | 0.879 | 0.653 | 19,029 |
| 3 | 47,288 | 53.2% | 21.0% | 0.9918 | 0.9999 | 1.000000 | 0.967 | 0.617 | 11,797 |
| 4 | 26,800 | 54.2% | 37.0% | 0.9959 | 0.9999 | 0.999999 | 0.977 | 0.618 | 6,591 |
| 5 | 15,395 | 76.5% | 64.4% | 0.9906 | 0.9999 | 1.000000 | 0.957 | 0.671 | 4,404 |

The map contracts smoothly at every stage (step correlation rises 0.99 -> 1.0 over the 20 iterations); the final 1.00000 is a genuine fixed point at float precision, not an early freeze. Effective user share stays 0.62-0.70, so no small elite captures the converged weights.

## 2. The seed-echo suspicion is largely right about the population

By stage 5, 76.5% of survivors are either-fold and 64.4% are both-fold year-jury members (baseline 10.8%/4.3%). Pruning-by-gain retains year-jury members by construction (their weight gain is negative), so the high retained-direction numbers partly restate the seed inside a seed-dominated population. The stage-level 'retained direction' metric on its own is therefore weak evidence for a valley.

## 3. But the valley is reachable seedlessly

Random 3%-cohort starts iterated to convergence on three populations; counts of starts landing within +/-0.25 of the full-matrix literary direction:

| population | users | paired seeds: literary/mixed/mirror | unpaired: literary/mixed/mirror |
|---|---:|---|---|
| full | 233,271 | 13/6/13; 15/2/15; 12/8/12 | 14/4/6 |
| stage3 | 47,288 | 16/0/16; 16/0/16; 16/0/16 | 9/0/15 |
| stage5 | 15,395 | 16/0/16; 16/1/15; 16/0/16 | 18/0/6 |

- On the **full** population, no random start finds the literary pole (max correlation 0.478); all basins are the Goodreads love center and its mirror.
- On the **stage-5 pruned** population, the geometry has exactly two attractors: the literary pole and its paranormal-romance mirror. The paired-start 16/16 splits are partly an artifact of the complement-start design; among **unpaired** cohort starts the split is **18/6** in favor of the literary pole — it is the stronger basin, not a coin flip.
- The stage-5 literary-pole consensus head (pooled across seeds) is essentially the seeded run's head, confirming that the seeded fixed point is a genuine attractor of the pruned geometry, not a seed echo:

1. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.841)
2. *Pride and Prejudice* — Jane Austen (0.841)
3. *The Complete Stories and Poems* — Edgar Allan Poe (0.822)
4. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.820)
5. *The Complete Sherlock Holmes* — Arthur Conan Doyle (0.812)
6. *To Kill a Mockingbird* — Harper Lee (0.806)
7. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.791)
8. *Jane Eyre* — Charlotte Bronte (0.789)
9. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.788)
10. *J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings* — J.R.R. Tolkien (0.776)
11. *Hamlet* — William Shakespeare (0.774)
12. *The Monster at the End of this Book* — Jon Stone (0.772)
13. *The Complete Grimm's Fairy Tales* — Jacob Grimm (0.766)
14. *Persuasion* — Jane Austen (0.766)
15. *The Count of Monte Cristo* — Alexandre Dumas (0.765)

Pole metrics: exact literary @50 **5**, broad **12**, anti **3**.

## Verdict

- **Convergence**: real (smooth contraction, exact fixed points). The original report's step-correlation claims hold.
- **The seeded head is not an artifact**: random starts on the pruned population find the same canonical head with the same metrics, and the literary pole is the majority basin among unpaired starts (18/24).
- **What does not survive**: the framing that pruning 'discovers' the valley. The pruned population is 64% both-fold seed-jury members, so the geometry that supports the literary pole was manufactured by the seeded pruning; the stage-level retained-direction metric mostly restates the seed. The head is Anglophone school-canon plus beloved boxed sets and children's classics (one foreign-language book at #1), matching the known lean of the year-preference jury itself.
- The remaining genuine novelty: gain-pruning specifically (not random pruning of the same mass) creates a geometry in which a literary pole exists as the dominant attractor at all, and the pull-to-center population is old-book-loving omnivores. The mirror pole (paranormal romance/urban fantasy) exists in the same geometry, so ratings alone still do not say which end is 'literary' — the identifiability boundary stands.

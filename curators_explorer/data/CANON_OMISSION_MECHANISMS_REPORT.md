# Why high-canon books are absent

## Reading the decomposition

The live Love ranking asks whether the selected raters express strong relative love. The distributed score asks a harder question: after balancing each juror's high and low ratings, does esteem recur across many independently reclustered communities, with enough evidence to survive lower-tail penalties? A book can therefore have high Love and high average esteem yet miss because the enthusiasm is uneven.

The raised-ceiling top-200 score cutoff is **49.8**.

| Book | Love | Raised / cap120 | Score | Esteem | Heterog. penalty | Community pair-rate q10–q90 | P(top200), mass60/120 |
|---|---:|---:|---:|---:|---:|---:|---:|
| *Moby-Dick or, The Whale* | 72 | 227 / 278 | 48.7 | 64.7 | 13.2 | 42–83% | 43/35% |
| *Ulysses* | 18 | 238 / 262 | 48.4 | 64.8 | 13.2 | 35–88% | 33/16% |
| *The Great Gatsby* | 824 | 1046 / 1059 | 25.9 | 46.4 | 18.2 | 18–70% | — |
| *The Brothers Karamazov* | 1 | 1 / 2 | 83.7 | 88.9 | 3.7 | 75–95% | 100/100% |
| *Crime and Punishment* | 3 | 4 / 7 | 76.4 | 87.2 | 9.4 | 66–97% | 100/100% |
| *Lolita* | 29 | 209 / 271 | 49.3 | 65.3 | 13.4 | 42–91% | 47/48% |
| *The Catcher in the Rye* | 1109 | 1064 / 1069 | 24.4 | 37.0 | 10.2 | 21–55% | — |
| *1984* | 67 | 169 / 216 | 51.2 | 67.4 | 13.9 | 45–84% | — |
| *Hamlet* | 11 | 2 / 1 | 83.6 | 90.3 | 5.5 | 78–97% | 100/100% |
| *Wuthering Heights* | 1320 | 625 / 694 | 38.8 | 56.7 | 15.2 | 37–83% | — |
| *Pride and Prejudice* | 968 | 597 / 696 | 39.7 | 62.1 | 20.4 | 33–87% | — |
| *To Kill a Mockingbird* | 216 | 439 / 497 | 43.2 | 59.9 | 14.0 | 39–78% | — |
| *Madame Bovary* | 570 | 520 / 550 | 41.3 | 55.1 | 10.6 | 33–66% | 2/0% |
| *The Adventures of Huckleberry Finn* | 587 | 421 / 469 | 43.5 | 60.6 | 14.1 | 39–81% | 11/0% |
| *The Last Question* | 22 | — / — | 47.1 | 58.9 | 5.2 | — | — |
| *The Story of a New Name (The Neapolitan Novels #2)* | 24 | 365 / 368 | 44.7 | 55.9 | 4.9 | 68–77% | 0/0% |
| *Dubliners* | 347 | 221 / 218 | 48.9 | 61.6 | 8.9 | 41–85% | 13/0% |
| *Catch-22 (Catch-22, #1)* | 121 | 210 / 206 | 49.3 | 59.7 | 6.7 | 37–76% | 38/11% |
| *Jane Eyre* | 743 | 829 / 893 | 34.3 | 58.4 | 21.6 | 27–84% | — |
| *Les Misérables* | 77 | 3 / — | 76.9 | 83.0 | 4.0 | 67–92% | 100/100% |
| *Macbeth* | 49 | 5 / — | 75.8 | 81.9 | 4.1 | 63–93% | 100/100% |

## Three motivating books

### Ulysses

Its Love rank shows strong enthusiasm among the live literary cohort. The distributed model also estimates high mean esteem, but enthusiasm varies markedly across community definitions and its uncertainty is high. It sits only a few score points below the top-200 cutoff and enters the top 200 in 16–33% of fixed-evidence resamples; this is a heterogeneity/robustness boundary, not a confident rejection or popularity exclusion. Its early-to-late paired 5-star rate falls 5.3 percentage points, but later readers have slightly *higher* mean jury-likeness; that is not the clean enthusiast-self-selection signature of simultaneous rating decline and declining jury-q.

### Moby-Dick

The mechanism is similar but better observed: high esteem and full community coverage, offset by a large heterogeneity penalty. Its positive temporal trajectory argues against enthusiast-first decay: its paired 5-star rate rises 2.7 percentage points. It enters the top 200 in 35–43% of fixed-evidence resamples. It is a plausible boundary disagreement with external canons, not a data-scarcity failure.

### The Great Gatsby

The old 80k ceiling hid the answer, but the counterfactual is decisive: after admission it ranks near the bottom, and remains there under evidence capping. Its mean balanced esteem is below the top-200 cutoff even before the very large cross-community penalty. Its external prominence is therefore not supported by this Goodreads literary jury; curriculum, cultural familiarity, and list tradition are more plausible explanations than a precision/popularity artifact inside our scorer.

## Model implication

Remove the hard 80k eligibility ceiling in the next candidate model, because it prevents the model from distinguishing *popular but broadly supported* (The Little Prince) from *popular but weakly supported* (Gatsby). Replace it with a moderate total-evidence cap around 120 and retain uncapped, 60, and 30 paths as trajectories. Cap 120 preserves 99% of the raised-ceiling top 200 while preventing unlimited precision leverage. 1984 is a useful boundary case: #169 uncapped but #216 at cap 120.

Do not automatically add Ulysses or Moby-Dick from external ranks. Instead, expose a second 'high esteem, community-contested' view or report their average esteem alongside the conservative score. That makes the philosophical choice—consensus versus intense minority esteem—visible rather than burying it in one rank.

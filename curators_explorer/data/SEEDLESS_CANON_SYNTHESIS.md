# Seedless canon search: synthesis

## Question

Can a literary canonical consensus be recovered using only the structure of
`(user_id, work_id, rating)` tuples, without titles, authors, publication years,
genres, shelves, demographics, or literary seeds?

All discovery choices below were frozen before titles and the existing literary/
anti sets were loaded. Those sets are evaluation probes only.

## What the new pass tested

| Principle | Ratings-only implementation | Structural result | Post-hoc result |
|---|---|---|---|
| Signed taste modes | Degree-corrected signed spectral operator; activity, generosity, popularity, mean rating and p5 projected out | Strongly non-null spectrum, but low-evidence modes are unstable/localized | Arabic/Bengali literary communities, manga, romance and series islands; no global literary pole |
| Evidence/stability | Repeat at minimum 100, 500 and 2,000 readers; disjoint-reader principal-angle tests | Leading-8 half-sample subspace agreement rises from 0.105 to 0.718 to 0.857 | Stability removes sampling noise, but the stable objects are still genre/series ecosystems |
| Distributed readers | Rotation-invariant dispersion of each reader's five-star books through the stable taste subspace | Bridge-book scores replicate across halves (Spearman 0.936–0.941) | Cross-fantasy readers, not literary generalists; exact literary overlap @50 is zero |
| Exposure among bridge readers | Popularity-adjusted cohort enrichment rather than star esteem | Replicates across halves (Spearman about 0.86) | A stable Arabic reading community, not a global literary center |
| Random-origin reconstruction | 32 random juries repeatedly reweighted by agreement with degree-corrected signed book support | Successive directions contract from 0.939 to 0.9994 correlation, but do not all choose the same basin | Local attractors and a Goodreads-wide love center, not a literary center |
| Equal-attractor center | Give each discovered basin equal mass; use mean, q10, or mean-minus-SD esteem | Top-200 overlap under new seeds/nonlinearity is about 0.67–0.72 | Sanderson, Calvin and Hobbes, Harry Potter, recent social nonfiction; no exact literary seed in the q10 top 200 |
| Cultural nestedness contribution | Excess audience containment over a bipartite degree expectation, using full natural collection sizes for 120,000 users | Highly reproducible across anchor panels (Spearman 0.971–0.980) | Romance/urban-fantasy cores; exact and broad literary overlap are both zero through rank 500 |

## The main finding

There **is** natural, reproducible structure in Goodreads ratings. There is also a
natural center under several defensible definitions. But the naturally selected
objects are:

1. local cultural/fandom canons;
2. stable series and genre ecosystems; and
3. a platform-wide “strongly loved on Goodreads” center.

None of the tested symmetry breakers identifies a global *literary* hierarchy.
The result is no longer well explained by a poor clusterer, insufficient numerical
convergence, one arbitrary seed, low book evidence, popularity alone, or the loss of
natural collection size. Each of those explanations was tested separately.

This is an identifiability boundary. The tuple matrix can say that two cultural
regions differ, which regions are stable, which readers bridge them, and which books
are central or nested. It contains no label saying why the stable Mercy Thompson or
Arabic-literary hierarchy should count as less or more “literary” than another.
An unsupervised method can privilege an observable asymmetry—size, rarity,
stinginess, breadth, nestedness, stability—but the experiments show that none of
those asymmetries uniquely corresponds to literary prestige on Goodreads.

## Why the nestedness result matters

The final full-incidence test was a faithful version of Morin and Sobchuk's
[shortlist effect](https://www.cambridge.org/core/journals/evolutionary-human-sciences/article/shortlist-effect-nestedness-contributions-as-a-tool-to-explain-cultural-success/E404AE0BFD5D51ABBF6CD26C1B37FEEE):
it retained naturally short and long user collections rather than the balanced
spectral sample. Its stability became excellent, but it selected romance and urban
fantasy. This is consistent with the warning from
[in-block nestedness](https://arxiv.org/abs/1801.05620): modular and nested structure
can coexist, and global nestedness can describe a highly organized local block.
Optimizing in-block nestedness would improve recovery of those blocks and their
internal ladders; it would not, by itself, supply a reason to call one block the
literary center.

## What remains useful

- The rank-500 signed matrix cache makes deeper decompositions a roughly one-minute
  experiment, without repeating the 98.7-million-event extraction.
- The evidence trajectory demonstrates why 100-reader books generate impressive but
  non-replicating modes. Five hundred readers is a much better discovery floor;
  evidence is then capped/shrunk in final estimation rather than used as esteem.
- The nonlinear reconstruction really does contract. The earlier concern that it
  might wander or move in a consistently wrong numerical direction is resolved:
  individual paths slow smoothly, but multiple basins remain.
- Equal-basin aggregation is a principled ratings-only **Goodreads consensus** metric.
  It should not be mislabeled a literary canon.
- Local canons are genuine outputs, not nuisances. The Arabic literary pole is both
  structurally strong and stable once evidence is adequate.

## Recommended next decision

Do not spend a long run on another seedless clusterer or a full in-block nestedness
optimizer. The likely gain is a cleaner atlas of local canons, not identification of
the missing literary ordering.

If the goal remains specifically literary, introduce one minimal, explicit ordering
principle and audit it rather than hiding it inside “unsupervised” machinery. The
least prescriptive next candidate is **durability**: use rating timestamps only to
reward esteem that replicates across independent account cohorts and time windows,
while treating Goodreads bulk imports as a sensitivity path. This still will not
make “literary” identifiable by theorem, but it tests a canon-relevant asymmetry
(persistence) rather than a named literary seed. Publication year would strengthen
that test but would be a second metadata concession.

Alternatively, retain the current seeded distributed-consensus ranking and describe
the seed honestly as choosing which of the naturally present Goodreads taste basins
is interpreted as literary. The extensive seed-origin robustness work already
measures how strongly that choice affects the result.

## Reproducible artifacts

- `research_seedless_spectral_pilot.py`
- `research_seedless_bridge_canon.py`
- `research_seedless_attractor_census.py`
- `research_seedless_nestedness_contribution.py`
- `SEEDLESS_SPECTRAL_PILOT_REPORT_b500.md`
- `SEEDLESS_BRIDGE_CANON_PILOT_REPORT.md`
- `SEEDLESS_ATTRACTOR_CENSUS_FULL_REPORT.md`
- `SEEDLESS_NESTEDNESS_CONTRIBUTION_FULL_INCIDENCE_REPORT.md`

Large sparse matrix caches are local generated artifacts and should not be committed.

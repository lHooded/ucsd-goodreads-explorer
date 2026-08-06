# Handoff: rebuilding the literary jury

**Audience:** another agent picking up this research thread.  
**Repo:** `/home/ifrankling/unsw/novels`  
**Working package:** `curators_explorer/` (research scripts + reports). Leave `ucsd_explorer/` intact unless changing shared mint/ranking.  
**Machine constraint:** ~16GB RAM / 16 cores — avoid ProcessPool copies of huge matrices (swap thrash).

---

## Latest update: external-canon omission and popularity-ceiling audit (2026-08-06)

The fixed distributed ranking is now available on the Curators Explorer frontend as
`Distributed canon (research)`, including score +/-u, stability tier, reader/evidence counts,
and book-level trajectory details. Backend integration is in `distributed_canon.py`.

The next diagnostic compares the distributed top 200 with `lit-2014-2024.txt`, the default
frontend Love top 100, and a 2026-08-06 snapshot of the top 100 at
`https://thegreatestbooks.org/v/table`. See `EXTERNAL_CANON_OMISSION_AUDIT.md` /
`external_canon_omission_audit.json` and `research_external_canon_omissions.py`.

- 50/97 matched literary-list works and 51/98 matched Greatest Books works are in the
  distributed top 200; 69/100 Love-head works are.
- External-list heads are more widely read on Goodreads (source rank vs log catalog n rho
  -0.365 literary, -0.338 Greatest Books), while the Love head is essentially flat (-0.030).
  This is consistent with exposure/list feedback but is not causal proof of popularity bias.
- Omission mechanisms differ: external high books may be excluded by catalog type, blocked by
  the hard n<=80,000 ceiling, below pair-mass publication support, or fully scored below #200.

`POPULARITY_CEILING_COUNTERFACTUAL_REPORT.md` /
`popularity_ceiling_counterfactual.json` raise the ceiling to 400,000 while keeping the jury,
balanced-pair construction, and publication mass threshold fixed. All 54 mega-read candidates
are judged, with total-book evidence caps inf/120/60/30.

- Only 3 mega books enter the uncapped top 200; 2 survive caps 120/60 and 1 survives cap 30.
- Raised ceiling vs baseline J@50/200 is 0.923/0.961; common-rank rho is 0.998.
- Cap 120 vs uncapped raised ranking is J@50/200 0.923/0.990, making it the natural moderate
  saturation point. Cap 30 is deliberately harsh (0.724/0.887).
- *The Great Gatsby* is #1046 uncapped and #1059 at cap 120: its absence is not a precision
  artifact after admission. *1984* is #169 uncapped but #216 at cap 120, so it is a useful
  evidence-sensitive boundary. *The Little Prince* survives every cap.

`CANON_OMISSION_MECHANISMS_REPORT.md` / `canon_omission_mechanisms.json` decompose balanced
soft-jury esteem and community dispersion:

- *Ulysses*: Love #18, raised #238, esteem 64.8, heterogeneity penalty 13.2, raw supported-cell
  pair-rate q10-q90 35-88%, fixed-mass P(top200) 33%/16% at mass 60/120. Its paired 5-star
  trajectory falls 5.3pp but mean jury-q rises, so this is not clean enthusiast-first decay.
- *Moby-Dick*: Love #72, raised #227, esteem 64.7, heterogeneity penalty 13.2, q10-q90 42-83%,
  fixed-mass P(top200) 43%/35%; paired 5-star trajectory rises 2.7pp.
- *Gatsby*: Love #824, raised #1046, esteem 46.4, heterogeneity penalty 18.2, q10-q90 18-70%.
  Curriculum/cultural/list tradition is more plausible than direct scorer-popularity leverage.

**Decision direction:** remove the hard 80k eligibility ceiling in the next preferred model,
replace it with moderate total-evidence saturation around 120, and retain uncapped/60/30 as
trajectories. Do not auto-promote external-list books. Add mean esteem or a separate
"high-esteem, community-contested" view so books like *Ulysses* and *Moby-Dick* are visibly
boundary/estimand disagreements rather than silently treated as noncanonical.

### Frontend continuation: full catalogue + esteem view

That direction is now implemented in the explorer. Rerunning
`research_popularity_ceiling_counterfactual.py` writes `distributed_canon_catalog.json`, which
contains all **4,781** raised-ceiling candidates with pair mass at least 2 under the cap-120
model. The fixed frontend metrics are:

- `Distributed canon (research)`: conservative score, ranked across the full mass-2 catalogue.
- `Community esteem (research)`: mean posterior community esteem before subtracting
  heterogeneity and evidence penalties.

Both include analytic sampling/partition `+/-u`. Community disagreement is classified
separately as broad/mixed/contested/unclear; evidence is supported/exploratory/sparse. The
contested label is driven by the cross-community heterogeneity penalty but requires enough
pair mass and coverage; weak evidence is never called disagreement. Selecting either fixed
metric sets the view limit to 5,000, so the entire exploratory tail is accessible. Backend
serving is in `distributed_canon.py`; UI changes are in `static/app.js`, `index.html`, and
`styles.css`.

---

## 0. Latest update: observation ladder + hierarchical pooling challenger (2026-08-06)

The full detailed archive is now collapsed to one row per mapped user×work in
`observation_ladder_full.parquet` (1.09 GiB). See `OBSERVATION_LADDER_FULL_REPORT.md` and
`observation_ladder_full.json`.

- 228,648,342 raw interactions collapse to 210,633,872 user×work states across 870,607 users
  and 523,869 works.
- 98,854,143 states are rated; 7,008,040 are known-read/unrated; 104,771,689 are
  shelved/unread. Known-read/unrated is 6.62% of recorded reads.
- 13,630,476 states are reviewed, including 440,527 reviewed but unrated.
- `research_observation_ladder_extract.py` reproduces the artifact. The extraction took ~102s.

The soft jury and its nine hard community assignments are materialized in
`jury_community_assignments.parquet` by `research_export_jury_communities.py`: 20,000 broad
users, 6,808 with nonzero bootstrap jury weight, total jury mass 4,929.

### Hierarchical partial-pooling pilot

`research_hierarchical_read_selection.py` / `HIERARCHICAL_READ_SELECTION_REPORT.md` replace
the old 50%-community-coverage cliff with empirical-Bayes prediction for unobserved
book×community cells. The central fit:

- retains exact expected-inclusion pair mass and caps each observed cell at 30;
- shrinks each book rate by 50 global-prior units and each cell by 8 prior units;
- carries book-level uncertainty once (it is shared across predicted communities);
- estimates a 4.8-score-point out-of-sample community-heterogeneity floor from well-observed
  books, so missing communities are unknown rather than artificial confirmations;
- ranks by conservative mean esteem minus heterogeneity and evidence penalties;
- makes 1,143 of 1,146 near-evidence candidates estimable at pair mass ≥10.

The first implementation incorrectly reused a sparse book's own high rate as independent
confirmation in every missing community; it flooded the head with low-mass books and was
discarded. The corrected shared-uncertainty/shrinkage fit does not exhibit that failure.

Reasonable book-prior and evidence-penalty variants are locally stable versus the corrected
central fit: Jaccard@50 0.852–0.961 and Jaccard@200 0.932–0.980. Central score versus catalog
readership is rho=-0.311: popularity is not rewarded, although it still controls how much can
be known. Γ=1.5/2 known-read-unrated paths have median top-200 score drops 0.19/0.55 points;
the deliberately extreme all-unrated-low path drops the median 3.07 points and remains a
separate systematic bound.

### Reader bootstrap and stability synthesis

`research_hierarchical_reader_bootstrap.py` passed a 64-draw bug test and completed 2,000
whole-reader Poisson draws in 27s. See `HIERARCHICAL_READER_BOOTSTRAP_FULL_REPORT.md`.

- mean Jaccard@50 = 0.707 (q10 0.639); mean Jaccard@200 = 0.733 (q10 0.702);
- median top-200 reader u80 = 3.95 points; median eligibility = 100%;
- point-top-200 books at pair mass 10–20 have median top-200 survival 67%, versus 94–100%
  above mass 20. Sparse books can have narrow conditional bootstrap widths because pooling
  pins them to the prior, so analytic posterior uncertainty and eligibility must stay visible.

The jury/community continuation is complete:

- `jury_fuzzy_community_assignments.parquet` materializes the conservative top-two,
  q-weighted mean-max-0.90 responsibilities; every user's memberships sum to one.
- `HIERARCHICAL_MEMBERSHIP_AUDIT_REPORT.md` crosses hard/soft juries and hard/fuzzy90
  communities. Hard-jury J@50/200 is 0.961/0.951; soft-fuzzy90 is 0.961/0.970; hard-fuzzy90
  is 0.961/0.942. The point top seven remain the same set.
- `research_hierarchical_jury_bootstrap.py` refit 100 teacher-composition juries and propagated
  each through both hard and fuzzy90 hierarchical scorers. Its first draws reproduce the
  legacy 5,000-refit jury Jaccards exactly. See `HIERARCHICAL_JURY_BOOTSTRAP_FULL_REPORT.md`.
  Median top-200 jury u80 is 0.85, much smaller than reader uncertainty; hard-community mean
  J@50/200 is 0.887/0.931. The top five are always top seven and have 100% top-200 inclusion.
  Packed selected-jury masks are retained in the checkpoint for reuse without another refit.

The numerical-popularity audit is `HIERARCHICAL_POPULARITY_AUDIT_REPORT.md`. Aggregate
book-level evidence is saturated at 30/60/120 effective pair votes, in addition to the
existing per-cell cap. Under the aggressive cap 30, J@50/200 is 0.724/0.869 and the point top
five remain ranks 1, 2, 5, 6, and 9. Catalog readership and pair mass correlate rho=0.552,
but score/catalog partial rho conditional on pair mass is -0.507. This is evidence against
*precision-driven* popularity holding up the head; it does not rule out cultural familiarity,
reader selection, or jury-definition bias upstream of the scorer.

Three additional upstream/popularity audits are now complete.

- `HIERARCHICAL_FEATURE_JURIES_REPORT.md` propagates alternative jury-feature families through
  the hierarchical scorer. Removing direct activity/shelf-size features changes 12% of the
  top 200 (J@50/200 0.887/0.878 for hard communities; 0.852/0.869 for fuzzy90), while common-book
  scores remain rho=0.991. The same five books remain the head set. A generic-only jury has
  user Jaccard 0.040, only 281 rankable books, and J@200 0.105; it is an adversarial estimand
  ablation, not a plausible veto. `jury_feature_variant_assignments.*` exactly reproduce all
  existing baseline jurors, hard labels, and fuzzy weights before projecting outsider jurors.
- `HIERARCHICAL_CANDIDATE_BOUNDARY_REPORT.md` expands the prior-learning population from 1,146
  candidates to 4,920 fiction works at pair mass >=2, then reapplies mass >=10 for publication.
  The relearned-prior ranking has J@50/200 0.961/0.961 and the same head. Three sub-10 books
  enter its top 200: *Remembrance of Things Past: Volume I* (#178, mass 9.3), *Don Quijote de
  la Mancha I* (#188, 9.2), and *Tehlikeli Oyunlar* (#199, 7.7). They are an underexposed
  watch list with roughly +/-8.3-point uncertainty, not promotion candidates yet.
- `FIXED_MASS_SUBSAMPLES_FULL_REPORT.md` removes actual observed user-book pair events rather
  than merely rescaling book counts. Across 300 draws, equalizing high-evidence books to
  expected mass 120 yields mean J@50/200 0.886/0.981; the deliberately severe mass-60 path
  yields 0.732/0.935. Every head-five book remains top 200 in every draw. At mass 60 their
  10th-90th percentile rank bands are 1-8, 1-5, 3-20, 1-10, and 3-28 in expanded-prior order.

`research_hierarchical_joint_bootstrap.py` then crosses the 100 saved teacher-composition jury
refits with ten independent whole-reader Poisson resamples apiece. It relearns every pooling
term on the expanded population in each of 1,000 draws. See
`HIERARCHICAL_JOINT_BOOTSTRAP_FULL_REPORT.md`.

- Mean joint J@50/200 is 0.701/0.726; median point-top-200 joint u80 is 4.17 points.
- Reader-only u80 was 3.95 and jury-only u80 was 0.85, so reader evidence remains dominant,
  but the interaction is now measured directly.
- The expanded-prior head five have 100% top-200 inclusion and joint q10-q90 rank bands 1-2,
  1-2, 3-9, 3-7, and 3-10.
- The recomputed soft point exactly reproduces the stored expanded ranking (J@50/200 1/1;
  maximum top-200 score error 0.000003 points).

The updated synthesis is `HIERARCHICAL_STABILITY_SYNTHESIS_REPORT.md` /
`hierarchical_stability_synthesis.json`. The **expanded mass-2 prior population with a mass-10
publication threshold is now the preferred research point model**, though not yet the product
default. It labels **117 stable-core, 51 supported/boundary, and 32
underexposed-or-contested** books. Display `u*` is now max(analytic u, joint reader-by-jury
u80); the overlapping components are not added in quadrature. The four books newly entering
the expanded-prior publication top 200 were also added to the feature audit and remain fragile
for substantive trajectory/Gamma reasons rather than an old reporting cutoff.

**Decision:** direct numerical popularity is increasingly unlikely to explain the head, but
cultural familiarity and Goodreads reader selection are not identified away. Retain the three
sub-10 exploratory entrants as a separate watch list. Keep feature-family, fixed-mass, Gamma,
and temporal paths separate from `+/-u`; stability is evidence for a distributed consensus,
not proof that culturally isolated or unobserved canons have been recovered.

### Community influence and edition/language continuation

`research_adversarial_community_reweighting.py` / `ADVERSARIAL_COMMUNITY_REWEIGHTING_FULL_REPORT.md`
now tests whether the equal-community point is a narrow convenient balance. Across 1,000
shared mixtures where no community can have more than twice another's influence, mean
J@50/200 is 0.976/0.990. A deliberately harsher book-specific least-favourable mixture has
J@50/200 0.961/0.951. Only seven point-top-200 books are mixture-sensitive; all are rank 147+
and all were already in the fragile tier. Do not replace the point score with the worst-case
score because the central model already penalizes disagreement; retain this as a trajectory.

`research_edition_language_fragmentation.py` / `EDITION_LANGUAGE_FRAGMENTATION_REPORT.md`
merges the 2,434 duplicate-work links already known to the catalog while capping each user at
one canonical vote. For the expanded research universe this changes neither candidate count
(4,920), publishable count (1,139), top 50, nor top 200: J@50/200 and RBO are all 1.000. The
top 200 has a median 52 Goodreads editions and 195 have editions in multiple known languages,
so the archive already consolidates most translations. Thirteen publishable books borrow any
flagged-duplicate evidence; the largest visible top movement is *The Yellow Wall-Paper* 72->67.
Unknown cross-language work-ID failures still require external identifiers or manual review;
translated title similarity alone is not safe enough to merge.

The synthesis includes both audits. Tier counts remain 117/51/32, which is itself evidence
that the fragile tier is detecting the same boundary under genuinely new tests.

---

## Prior update: leakage-controlled selection + feature/seed trajectories (2026-08-05)

### Morning continuation: exact estimator, soft participation, and time

The overnight campaign completed successfully: 5,000 exact-pair user-block replicates and
5,000 teacher-composition jury refits. Consolidated decision/report/results:
`EXACT_ESTIMATOR_CONSOLIDATED_REPORT.md` and `exact_estimator_consolidated.json`.

- The exact expected-inclusion estimator replaces hash-seeded 12×12 pair sampling.
- Across the exact top 200, median reader-block `u80` is 4.62 points versus 0.86 for jury
  composition; reader/evidence uncertainty is currently much larger.
- Keep reader `u80`, jury `u80`, and their eligibility probabilities separate until a joint
  nested bootstrap is calibrated. Γ remains a separate systematic-bias trajectory.

Soft participation is now tested in `SOFT_MEMBERSHIP_FULL_REPORT.md` and
`SOFT_JURY_BOOTSTRAP_FULL_REPORT.md`. Bootstrap jury-inclusion probabilities sum to exactly
4,929 juror equivalents, touch 6,826 users, and have Kish n=5,199. In 2,000 reader-block
replicates the soft jury modestly improves mean J@200 (0.769 vs 0.765) and median `u80`
(4.47 vs 4.62). Use it as the preferred point estimator, with the hard jury retained as a
sensitivity path. Do **not** adopt general fuzzy community membership: only the conservative
top-two/mean-max-0.90 version is useful as an audit; stronger smoothing mechanically reduces
partition variance and changes the ranking substantially.

The full detailed Goodreads interaction archive was downloaded and gzip-validated at
`data/ucsd_goodreads/raw/goodreads_interactions_dedup.json.gz` (11,492,470,942 bytes). The
official `user_id_map.csv` was also re-downloaded after the local copy proved truncated; the
old file is preserved as `user_id_map.csv.corrupt-20260806`. `research_temporal_extract.py`
produced `temporal_rated_events_full.parquet`: 99,282,051 mapped rated events, 811,050 users,
523,822 works, 1.46 GiB. See `TEMPORAL_RATED_EVENTS_FULL_REPORT.md`.

The first trajectory audit is complete in `TEMPORAL_TRAJECTORIES_REPORT.md` and
`temporal_trajectories.json`. Across the 20,000 broad users, 37.9% put at least half their
ratings on one day; they carry 40.1% of soft jury mass. Early/late trajectory direction agrees
with the onboarding-filtered primary clock only ~72–74% under alternative Goodreads activity
clocks (63% for available `read_at`). Calendar raw-esteem top-200 Jaccard is only 0.42–0.48
despite common-book score rho 0.77–0.84. **Decision:** retain time as a diagnostic and
book-level uncertainty/trajectory annotation, not a direct score correction. Direction-
consistent decline plus falling mean jury-q is the clearest current enthusiast-first flag;
clock disagreement should widen uncertainty rather than move rank.

The original overnight runbook is `curators_explorer/data/OVERNIGHT_CAMPAIGN_RUNBOOK.md`.

The two deferred robustness audits are implemented:

- Target-excluded selection script/report/results:
  `research_target_excluded_selection.py`, `TARGET_EXCLUDED_SELECTION_REPORT.md`,
  `target_excluded_selection.json`.
- Jury-feature/pair-seed script/report/results:
  `research_jury_seed_trajectories.py`, `JURY_SEED_TRAJECTORIES_REPORT.md`,
  `jury_seed_trajectories.json`.

### Target-excluded Γ calibration

The old co-reading-centroid calibration was outcome-blind but still included the target
interaction and scored readers against a centroid they helped define. The replacement splits
90 calibration books into five item folds, removes each entire target fold from the reader
embedding, and predicts recorded target interaction for held-out user folds. The balanced
ridge propensity model sees binary interaction labels but never rating values. Median held-out
interaction AUC is **0.814**.

The effect is stronger than the old proxy and far above random-subset noise. When the highest-
propensity 25% of observed pair voters are retained, esteem is higher for **90%** of books,
mean inflation is **9.4 points**, and Γ q50/q75/q90 is **1.80/2.05/2.52**. Matched random
subsets give **1.01/1.21/1.47**. At 50% retention the observed quantiles are
**1.34/1.53/1.95** versus random **1.00/1.12/1.25**.

This supports retaining Γ=1.5 as the moderate bound and Γ=2 as the strong bound. It still does
not identify actual missing exposure: no Goodreads rating conflates not exposed, not read, and
not recorded, while the high-propensity subset represents the typical audience rather than a
randomized counterfactual readership.

### Jury feature families and pair-sampling seeds

Three 4,929-person jury reconstructions were crossed with five balanced-pair seeds (15
universes). To prevent the alternative juries changing the baseline latent space, communities
are fit on the original rich-model top 20,000 and 3,867 outsider jurors are projected into that
frozen space. The prior central ranking is reproduced at Jaccard@50 **1.000**, Jaccard@200
**0.990**.

- Removing direct shelf-size variables leaves a nearby plausible jury (user Jaccard **0.813**)
  and a fairly stable ranking (Jaccard@200 **0.826**).
- Removing all author/series/publication-era behavior produces a different population (user
  Jaccard **0.040**) with only 22 rankable books, four from the central top 200. Treat this as
  an adversarial ablation showing those features define the literary estimand—not as an equal
  plausible jury allowed to veto every candidate.
- Pair sampling is a major nuisance axis: alternative-seed Jaccard@200 is **0.563–0.594**.
  There are 26 semantic and 55 evidence-sensitive central books across seeds.
- **47 of the prior 50** jointly robust books also pass both plausible jury-feature models,
  at least four of five seeds, at least 80% of their ten plausible crossed universes, and the
  Γ=1.5 score floor. The three excluded books are *Ariel*, *Bartleby the Scrivener*, and *The
  Fall*; all fail through seed-dependent evidence, not a demonstrated preference reversal.

An inherited truncation was also fixed: `aggregate_spec` now retains every eligible rank,
rather than counting all eligible books but saving only 500. The original 45-universe
multiverse was rerun; its headline counts are unchanged (50 joint robust, 70 selection-
sensitive, 16 pair-semantic), while full presence/evidence diagnostics are now safe for future
broader universes.

**Decision:** the current strongest stability tier is 47 books, but do not treat the three
sampling-evidence failures as disproven canon. Replace the arbitrary single pair sample with
repeated-seed expected counts or all capped per-user votes, then calibrate `±u` using user-block
resampling. Keep Γ systematic-bias sensitivity separate from `±u`.

---

## 0A. Prior update: joint consensus multiverse (2026-08-05)

The jury-size, pair-definition, and enthusiast-self-selection trajectories are now implemented
together as a compact structured multiverse:

- Script: `curators_explorer/scripts/research_consensus_multiverse.py`
- Report: `curators_explorer/data/CONSENSUS_MULTIVERSE_REPORT.md`
- Results: `curators_explorer/data/consensus_multiverse.json`

The run crosses three nested rich-behavior juries (3,286 / 4,929 / 7,500), three rating-pair
definitions (5★ vs ≤3★, 5★ vs ≤2★, and ≥4★ vs ≤2★), and five selection-bias bounds
(Γ=1 / 1.25 / 1.5 / 2 / 3): **45 universes** over the same nine community partitions.
One-factor paths are retained alongside the crossed grid so each kind of instability remains
interpretable.

Γ bounds how much more likely a positive-outcome reader may be to appear among observed raters.
A separate outcome-blind calibration pseudo-obscures 90 broadly observed books by selecting
readers from a binary co-reading embedding that never sees rating values. Retaining only the
nearest 25% gives Γ quantiles 1.21 / 1.52 / 2.04 at p50 / p75 / p90. Thus Γ=1.5 is a defensible
moderately conservative scenario and Γ=2 is strong, but neither is a book-specific estimate:
the broad comparator is itself selected, and the embedding still knows the target interaction
occurred.

Main results:

- Selection bounds alone preserve the head well: at Γ=1.5, Jaccard@200 is **0.980** and RBO
  is **0.966**; at Γ=2 they are **0.942 / 0.950**.
- Jury size and rating semantics matter much more. Across all 44 non-baseline universes,
  mean/worst Jaccard@200 is **0.485 / 0.361** and mean RBO is **0.495**.
- **50** books form a provisional jointly robust tier: central top-200 and score≥50, ≥2/3
  top-200 survival along the jury, pair, and full crossed paths, and Γ=1.5 score still ≥50.
- **70** central positive-score books fall below 50 by Γ≤1.5 and are explicitly marked
  selection-sensitive. This is a robustness warning, not evidence that the bias exists.
- There are **0** jury-semantic failures among books rankable under all three jury sizes, but
  **83** jury-evidence failures. Current jury-size instability is overwhelmingly insufficient
  coverage in the strict jury, not a demonstrated taste reversal.
- Pair semantics produce **16** genuine top-200 trajectory shifts among fully rankable books;
  another **51** are pair-evidence-sensitive because ≤2★ outcomes are sparse.
- `±u` remains sampling/partition uncertainty. Γ sensitivity is systematic missing-not-at-
  random bias and must be displayed separately, not folded into `u`.

**Decision:** doing the axes together was useful: separate paths identify the mechanism, while
the crossed grid catches interactions that one-at-a-time tests miss. Treat the 50 as strongest
current candidates, not a locked canon. Next validate Γ using a cross-fitted, target-excluded
exposure propensity; then add jury feature-family and pair-sampling-seed axes before calibrating
`±u` with user-block resampling.

---

## 0B. Prior update: exposure-adjusted consensus pilot (2026-08-05)

The popularity/exposure correction requested after the first community pilot is implemented:

- Script: `curators_explorer/scripts/research_exposure_adjusted_consensus.py`
- Report: `curators_explorer/data/EXPOSURE_ADJUSTED_CONSENSUS_REPORT.md`
- Results: `curators_explorer/data/exposure_adjusted_consensus.json`

The old audit could not distinguish “this community dislikes the book” from “too few people in
this community rated it.” That was a large confound: within the old baseline top 200, catalog
readership correlated **ρ=0.830** with community-top200 rate.

The revised pilot separates:

1. conditional esteem among jurors who rated the book;
2. noise-corrected between-community taste heterogeneity;
3. observed exposure breadth;
4. provisional epistemic uncertainty (`score ± u`).

Implementation details:

- 4,822 jurors contribute 97,602 balanced user-book votes (equal sampled 5★ and ≤3★ sides).
- Communities are equal-weighted; an unobserved community is unknown, not negative.
- Evidence is capped at 30 readers per book/community, so popularity cannot add unlimited
  precision or leverage.
- At least 50% observed-community coverage is a **saturating eligibility condition**: crossing
  it permits entry to the distributed ranking, but 100% coverage scores no higher than 50%.
- Point score = mean conditional esteem − 1.282 × estimated genuine community heterogeneity,
  interpretable as a rough lower-tail preference in a new observed community.
- `±u` combines posterior sampling uncertainty and sensitivity to alternative partitions. It
  is useful now but not yet a calibrated confidence interval because partitions reuse users.

Results:

- 353 books clear the central evidence/coverage rules.
- 34 form a provisional robust distributed tier: score≥50, top-200 in ≥80% of nine evidence
  specifications, heterogeneity≤0.08, and u≤6 points.
- High-estimate books below the evidence/coverage floor are retained as **underexposed
  candidates**, not treated as disliked or noncanonical.
- Evidence caps and prior-strength changes are fairly stable; minimum-reader/community rules
  remain the largest source of head movement.

The direct positive popularity reward is gone, but this does **not** solve selection bias. Among
rankable books, score now correlates **ρ=−0.517** with catalog readership. That may partly be
real serious-reader taste, but it can also mean obscure books are rated mainly by enthusiasts.
With ratings alone those mechanisms are not identifiable. Do not optimize this correlation to
zero or celebrate it as “debiasing”; use an exposure-propensity/sensitivity model or additional
interaction data to bound the effect.

**Decision:** carry conditional esteem, heterogeneity, coverage, and uncertainty as separate
outputs. Next expand trajectories across jury and pair definitions, then add a sensitivity
analysis for enthusiast self-selection. The likely product shape remains a distributed core,
contested tier, and underexposed-candidate tier—not one falsely precise universal list.

---

## 0C. Prior update: focused consensus-stability pilot (2026-08-05)

The focused community-robustness pilot is implemented and reported:

- Script: `curators_explorer/scripts/research_consensus_stability_pilot.py`
- Report: `curators_explorer/data/CONSENSUS_STABILITY_PILOT_REPORT.md`
- Results: `curators_explorer/data/consensus_stability_pilot.json`

This is deliberately **not another clustering-based canon generator**. It first constructs a
plausible within-jury pairwise ranking, then uses ratings-derived user communities only as
adversarial perturbations: equal-community weighting, leave-one-community-out, bounded random
reweighting, and community-only rankings. Nine alternative partitions (k=6/10/16 × three
seeds) produce 159 mixture universes and 96 community-only diagnostics.

Main result:

- Mean leave-one-community-out stability is strong: Jaccard@200 **0.842**, RBO **0.887**.
- **157** books remain top-200 in at least 80% of mixture perturbations.
- Only **34** also pass the stricter distributed-support definition: ≥50% community-only
  top-200 rate, normalized per-capita support concentration ≤0.25, and worst LOO drop ≤100.
- The remaining **123** are mixture-stable but have at least one community-dependence warning.

This supports a **small shared core followed by contested tiers**, not a single defensible total
order deep into the list. The Russian-literature concern splits rather than disappears:
*Brothers Karamazov*, *Crime and Punishment*, *War and Peace*, *Anna Karenina*, and several
others have genuinely broad support; *Pale Fire*, *Resurrection*, *The Insulted and
Humiliated*, and similar entries are much more community-dependent. This is evidence for
annotating/stratifying the result, not mechanically deleting Russian books.

Important implementation detail: support concentration uses **per-capita** positive support
and a k-normalized HHI, so community size is not mistaken for concentration. Jury
reconstruction is pinned to one DuckDB thread for deterministic floating-point aggregation;
parallelism resumes for the matrix stage.

**Decision:** the audit approach succeeds where prior ratings-only clustering failed because
clusters stress-test candidates instead of nominating them. Proceed to a jury/specification
multiverse while retaining three outputs: distributed core, community-dependent stable tier,
and fragile tier. Rank trajectories across those controlled specifications are the natural
next diagnostic; cluster book trajectories/archetypes, not readers/books as a canon-discovery
objective.

---

## 0D. Prior update: behavioral jury rebuild (2026-08-05)

The behavioral teacher reconstruction is now implemented and reported:

- Script: `curators_explorer/scripts/research_jury_rebuild.py`
- Report: `curators_explorer/data/JURY_REBUILD_REPORT.md`
- Results: `curators_explorer/data/jury_rebuild.json`

Current preliminary jury:

- **Model:** `rich_behavior_global` — five-fold out-of-fold linear reconstruction from
  generic ratings plus author breadth/concentration, series behavior, and publication era.
- **No inference leakage:** poll/taste membership and mint columns are labels/evaluation only,
  never predictors. A decontaminated co-reading model was audited and rejected as a shortcut.
- **Size:** **4,929**, chosen at the overlap/mass plateau rather than copying teacher n=3,286.
- **Teacher overlap:** 1,377 users; Jaccard **0.201**; **50.9%** of stored teacher weight.
- **Old-focus comparison:** restaged old focus Jaccard with teacher **0.077**.
- **Pairwise:** preliminary pos50 **37**, old focus **21**, teacher **43**;
  preliminary↔teacher top-50 Jaccard **0.408**.

Main learned directions reproduce and sharpen the original jury story: older 5★ publication
year, lower series share, fewer megastar authors, broader mid-popularity author span. Removing
direct shelf-size variables barely changes recovery (Jaccard 0.189→0.181 at teacher-sized k),
while activity-only is near-useless (0.009), so activity is not the main shortcut.

Set differences were inspected. Jury−teacher is more school/classical-canon and mega-popular
than teacher (Hamlet/Macbeth/Jane Eyre), but not a romance/commercial pocket; 40% is elsewhere
in the deep mint. Teacher−jury is deeper in Nabokov/Kafka/Bulgakov-style modernist reading.

**Decision:** use the 4,929-person rich behavioral cohort as the current preliminary hard jury.
Continuous soft jury weights remain deferred. The next ranking step can use within-jury
pairwise plus exposure framing; do not revive the co-reading evidence model merely because its
teacher overlap is higher.

---

## 1. Objectives (read this first)

### Primary goal
Build a **literary / “classics” ranking** from Goodreads ratings that reflects serious-reader taste — **without treating evaluation piles as ground truth**.

Piles (`literary_poll`, `non_literary`, school/normie from `lit-2014-2024.txt` / `normie_canon`) are **noisy probes**, not optimization targets.

### Immediate goal (where we are now)
Treat the expanded-prior hierarchical ranking as the research default and decide how to
present or productize it without erasing its limits. Preserve esteem, heterogeneity, exposure,
joint uncertainty, feature-family/fixed-mass paths, and systematic Gamma/time sensitivity as
separate outputs rather than one magic score.

The jury rebuild itself is complete. Diagnosis still matters: **who we listen to matters more
than how we order books**, and the new pilot shows that community composition remains visible
even inside the rebuilt jury.

### Planned sequence (do in this order)

1. ~~Choose a **teacher subset** of deep curators~~ → done.
2. ~~Reverse-engineer the teacher from behavioral features~~ → done.
3. ~~Compare new jury vs old focus vs teacher and inspect set diffs~~ → done.
4. ~~Run within-jury pairwise and a focused community-stability audit~~ → done.
5. ~~Separate conditional esteem, exposure breadth, heterogeneity, and uncertainty~~ → done
   for the fixed-jury exposure/evidence pilot.
6. ~~Build a compact **jury-size / rating-threshold / selection-bound multiverse** and add
   jury-feature / pair-sampling-seed axes~~ → done.
7. ~~Analyze **book rank trajectories** across those controlled axes~~ → done for the current
   axes; jury-evidence, pair-evidence, pair-semantic, and selection-sensitive paths separated.
8. ~~Add sensitivity bounds for enthusiast self-selection / missing-not-at-random exposure~~
   → Γ trajectories and target-excluded cross-fitted calibration done.
9. ~~Propagate plausible jury-feature alternatives, expand the candidate/prior boundary, and
   run actual-reader fixed-mass tests~~ -> done.
10. ~~Decide the research point model and calibrate a joint reader-by-jury interval~~ ->
    expanded-prior mass-2 learning / mass-10 publication chosen; 1,000 joint draws done.
11. Decide presentation/productization: compact distributed core plus supported/contested
    tiers, visible uncertainty and systematic paths, and a separate low-mass watch list.

### Design principles (do not violate)

- Probes ≠ loss function. Prefer structural / overlap / head-sanity signals alongside poll metrics.
- **Poll held-out and pos50 are contaminated** for anything minted from poll depth — smaller elites look “better” by construction.
- Deep curators are a strong teacher, **not infallible** (commercial-share pockets, floor passers, language islands, hyper-raters).
- Prefer **weighted** soft mass over hard equal-elite cuts.
- Keep reports plain-language; write findings to `curators_explorer/data/*_REPORT.md`.

---

## 2. Order of discovery (chronological arc)

What we learned, in the order we learned it — earlier steps explain why later ones exist.

### Phase A — Ratings-only canons fail as Anglophone lit heads
**Scripts/reports:** `research_ratings_only_canon.py` → `RATINGS_ONLY_CANON_REPORT.md`

Rarity / HITS / PMI / reflections on ratings alone → **local canons**, not the literary ranking we want. Author-level nesting helps theory (`AUTHOR_LEVEL_CANON_REPORT.md`) but heads still collapse into romance islands.

### Phase B — Reverse-engineer “classic lovers” (seed-conditioned)
**Scripts/reports:** `research_reverse_engineer_lovers.py` → `REVERSE_ENGINEER_LOVERS_REPORT.md`

Tried to find users who love classics from behavior. Result: lovers are often **omnivores**; seed-free correlates drift to Potter/Maas. Seeded reverse-engineering is fragile.

### Phase C — Three-way unseeded contrastive scorer (best careful baseline)
**Scripts/reports:** `research_threeway_unseeded.py` → `THREEWAY_UNSEEDED_REPORT.md`  
**Weights:** `weights_careful_cotrain.json` (canonical)

Classic vs anti vs normie cohorts; fit feature terms carefully in DuckDB; inference unseeded:

`classic_focus − λ·anti − λ·normie` + gates → strong probe numbers (Q≈72, pos50≈22, anti50=0).

**Stability** (`STABILITY_REPORT.md`): sticky books identified.  
**Careful cotrain** (`COTRAINING_*`): accepted → careful weights.  
**Iterative sparse cotrain** (`COTRAINING_ITER_*`): accepted then **drifted** (sign flips, children’s books) → frozen as `weights_iter_sparse.json`; **canonical restored to careful**.

### Phase D — Residual enthusiasm & pairwise esteem
**Scripts/reports:** `RESIDUAL_ENTHUSIASM_REPORT.md`, `PAIRWISE_ESTEEM_REPORT.md`

Residual enthusiasm: modest gains, more school-canon head.  
**Within-user pairwise** (same user: 5★ beats ≤3):

- Anti-optional: highbrow feel, but many books lack anti readers.
- Bilateral: strong shared canon, but depends on binge readers who never read true classics.

User OK with school canon prominence; dropped “contrastive vs binge” as primary framing. Liked **within-focus pairwise** + exposure/enthusiasm.

### Phase E — Diagnosis: jury selection is the bottleneck
**Scripts/reports:** `research_jury_diagnosis.py` → `JURY_DIAGNOSIS_REPORT.md`

Critical finding:

| Jury | Size | Notes |
|---|---:|---|
| Behavioral “focus” (top ~6% affinity) | ~4,774 | Equal-vote hard cutoff |
| Deep curators (mint) | ~19,841 | Seed-informed + weighted |
| Jaccard focus ↔ equal-size top deep | **~0.10** | Almost different people |
| Same pairwise on focus vs deep-capped | pos50 **19** vs **38** | Deep wins hard |

Original research focus was reverse-engineered from **taste signals**, then used as an equal-vote jury — **not** the app’s deep curator system (`ex.user_curator_deep_weight`, purity/deweight in `curators_explorer/cohort.py`).

**Conclusion:** fix **who is on the jury** before more book-ordering tricks.

### Phase F — Rebuild plan; first gate size/weight (pivotal)
**Scripts/reports:** `research_deep_size_sweep.py` → `DEEP_SIZE_SWEEP_REPORT.md`

Question: how many deep curators, equal vs weighted?

Findings:

- Top **4774** holds only **~58%** of stored weight mass.
- Soft deweight Kish n_eff ≈ **9–15k** (expo 0.6–1), not a hard 4.8k gate.
- Naive “best” on poll probes: **cap=2000 equal** — **trap** (contaminated).
- Full deep + weight dilutes; local canons (e.g. Turkish literary islands) appear in pairwise head.
- Weird mint pockets: ~1.8k high com_share, ~3.1k floor deep_share, ~103 hyper-raters.

**Caution recorded:** do not reverse-engineer only a tiny equal elite; prefer mid-pool / filtered weighted teacher; score on overlap + head sanity, not poll alone.

### Phase G — Purity × strictness for quality vs quantity
**Scripts/reports:** `research_purity_strictness_sweep.py` → `PURITY_STRICTNESS_SWEEP_REPORT.md`

On deep mint, sweep purity (share/com gates) × strictness (elite top-K keep).

| Kneepoint | Setting | n / Kish | Role |
|---|---|---|---|
| **Utopia / product** | **p65 / s25** | **3286 / ~2678** | **Chosen teacher** |
| Quality-lean | p75 / s40 | 1262 / ~1102 | Too small / shortcut risk |
| Max mass | p0 / s0 | 19841 / ~9401 | Diluted |

Note: on mint, **p0 ≡ p35** (mint floors already bind); purity bites from ~45+.

---

## 3. Current decision (teacher for training judges)

**Agreed teacher subset of deep curators:**

- Start from `ex.user_curator_deep_weight` (~19,841).
- Apply **purity ≈ 65** (`deep_share` floor + `com_share` cap per `curators_explorer/cohort.py`).
- Apply **strictness ≈ 25** (elite keep among purity passers) → ~**3.3k** users, Kish ≈ **2.7k**.
- Supervise with **stored weights** (`curator_pct_weight`), not equal 0/1 only.
- Soft continuous jury-ish weights: **later**.

**Reject as teacher:** full 20k equal; old focus ~4.8k equal; p75/s40 or top-1–2k “best probe” elites.

**Rationale in one line:** quality×mass knee that cleans mint pockets without collapsing into a poll-aligned shortcut elite.

---

## 4. Next work (do this next)

1. Retain the three sub-10 exploratory top-200 entrants as an underexposed watch list. Do not publish their
   precise ranks until more evidence exists; their current uncertainty is about 8.3 points.
2. Decide presentation: 117-book strict core, 51 supported/boundary books, and 32 explicitly
   underexposed-or-contested books. Tiers annotate evidence and should not silently rerank.
3. Keep conditional esteem, heterogeneity, coverage, joint `+/-u`, fixed-mass trajectories, no-activity-jury
   trajectories, Gamma sensitivity, and time visible even if product display derives one
   headline score. Cultural familiarity/reader selection remains the main unresolved bias.
4. If continuing bias research before productization, focus on adversarial community
   reweighting and edition/language fragmentation rather than more random hyperparameter
   sweeps; both internal audits are now complete. Further progress on the cultural-observation
   boundary needs external identifiers/manual review or an independent corpus.

Reuse patterns from:

- `research_consensus_stability_pilot.py` (current fixed-stat perturbation engine)
- `research_exposure_adjusted_consensus.py` (current conditional-estimation engine)
- `research_feature_sensitivity.py` (book trajectory/archetype reporting)
- `research_jury_rebuild.py` (behavioral jury variants)
- `research_target_excluded_selection.py` (leakage-controlled Γ calibration)
- `research_jury_seed_trajectories.py` (feature/seed trajectories and frozen projections)
- `research_hierarchical_feature_juries.py` (plausible feature-family propagation)
- `research_hierarchical_candidate_boundary.py` (expanded candidate/prior population)
- `research_fixed_mass_subsamples.py` (actual-reader popularity-leverage stress)
- `research_hierarchical_stability_synthesis.py` (current unified tiers and trajectories)
- `research_hierarchical_joint_bootstrap.py` (joint whole-reader x teacher-jury calibration)
- `research_adversarial_community_reweighting.py` (bounded shared and least-favourable mixtures)
- `research_edition_language_fragmentation.py` (known duplicate merge and language coverage)
- `research_deep_size_sweep.py` / `research_purity_strictness_sweep.py` (jury gates)

---

## 5. Key paths

| What | Where |
|---|---|
| Research scripts | `curators_explorer/scripts/research_*.py` |
| Reports / JSON | `curators_explorer/data/` |
| Canonical contrastive weights | `curators_explorer/data/weights_careful_cotrain.json` |
| Drifted iter weights (frozen, not default) | `curators_explorer/data/weights_iter_sparse.json` |
| Deep mint table | `user_curator_deep_weight` in `data/ucsd_goodreads/explorer.duckdb` |
| Cohort gates (purity / deweight) | `curators_explorer/cohort.py` |
| App ranking | `curators_explorer/ranking.py` |
| Older Pareto / rebuild notes (purity defaults) | `ucsd_explorer/data/SIMPLIFIED_REBUILD_REPORT.md`, `PARETO_TASTE_SIGNALS_REPORT.md` |
| Parked idea | `TODO` — trajectory-limit analysis after scoring formula settles |

## Seedless ratings-only center search (2026-08-06)

The renewed strict `(user_id, work_id, rating)` search is complete. See
`SEEDLESS_CANON_SYNTHESIS.md` for the consolidated result and exact artifact map.

The pass added a nuisance-projected signed spectral census, evidence-floor and
disjoint-reader subspace trajectories, rotation-invariant bridge readers, nonlinear
random-start jury attractors, equal-basin centers, and full-incidence cultural
nestedness contributions. The numerical/structural signals are real and often highly
stable, but they identify local canons, series/genre ecosystems, or a Goodreads-wide
love center—not a unique global literary hierarchy. In particular:

- leading-8 half-sample subspace agreement improves from 0.105 at `n>=100` to 0.718
  at `n>=500` and 0.857 at `n>=2000`;
- nonlinear paths genuinely contract (mean step correlation 0.939 -> 0.9994), but
  retain multiple basins;
- equal-basin center top-200 overlap is about 0.67–0.72 under seed/nonlinearity
  changes, but its head is Sanderson/Calvin and Hobbes/Harry Potter/social nonfiction;
- the faithful 120,000-user full-collection nestedness score is extremely stable
  across anchor panels (Spearman 0.971–0.980) but selects romance/urban fantasy and
  has zero exact or broad literary overlap through rank 500.

Do not rerun extraction for rank/power changes: the keyed local sparse caches are
reusable. Do not commit the `seedless_*_matrix*.npz` files. The next defensible
ratings-adjacent experiment, if desired, is a seedless durability criterion across
timestamp/account cohorts. Another clusterer or exact in-block nestedness optimizer
is expected to refine local canons without solving the literary identifiability
problem.

### Run pattern

```bash
cd /home/ifrankling/unsw/novels
PYTHONPATH=. .venv/bin/python -m curators_explorer.scripts.<script_module>
```

DB access for research usually via `_con()` in `research_ratings_only_canon.py` (attaches explorer DB as `ex`).

---

## 6. Vocabulary cheat sheet

| Term | Meaning here |
|---|---|
| **Deep curators** | Minted elite users in `user_curator_deep_weight` (poll-depth informed, weighted) |
| **Focus** | Old research jury: top affinity slice (~4.8k), equal vote |
| **Purity** | Query gate: min `deep_share`, max `com_share` |
| **Strictness** | Elite top-K keep among passers (legacy curator_strictness) |
| **Deweight** | Soft power on stored weights (not membership cut) |
| **Pairwise** | Within-user: 5★ preferred over ≤3★; aggregate win rates |
| **Probes** | literary_poll / anti / normie lists — diagnostics only |
| **Teacher** | Deep subset we reverse-engineer a behavioral jury to match |

---

## 7. What “done” looks like for the jury rebuild

- A **behavioral** jury that substantially overlaps the p65/s25 deep teacher (much better than focus’s Jaccard ~0.10).
- Set-diff iteration that **stops** when gains shrink or we’re only recovering mint score order.
- Weird deep pockets **flagged**, not silently trusted.
- Pairwise head that looks literary without needing bilateral binge contrast as the main story.
- Clear note in a report: what shortcut was avoided and why this jury beats old focus.

# Goodreads "Canon" Research — Master Report for Sol High

Prepared from the complete research record in `curators_explorer/data/` (all `.md` reports
read oldest-created-first, JSONs consulted as needed), plus the canonical orientation in
`JURY_REBUILD_HANDOFF.md`. Companion notes live in `ucsd_explorer/data/SIMPLIFIED_REBUILD_REPORT.md`
and `PARETO_TASTE_SIGNALS_REPORT.md`.

Scope: eight days of experiments (2026-08-01 … 2026-08-07) that turned the question "is there a
distributed, data-recoverable literary canon on Goodreads?" into a sharp, testable claim with a
well-characterized *identifiability boundary*, one clean *anchored* criterion (publication year),
a reproducible *latent literary basin* recoverable by a seed+prune cascade, and a null result for
any *unsupervised* natural literary center.

---

## 0. Bottom line

1. **There is no unsupervised literary canon.** Ratings tuples contain reproducible structure
   (local/fandom canons, series and genre ecosystems, a platform-wide "loved" center), but **no
   symmetry breaker recovers a *literary* ordering**: spectral, bridge-reader, attractor-census,
   nestedness, and ensemble-reversal all select genre/series/fandom objects, with **zero** exact
   literary overlap at @50 in the clean unsupervised conditions. This is an identifiability boundary,
   not a clustering failure (each alternative explanation was tested separately).

2. **A literary canon exists only as an explicit, seeded preference, and it is real when the seed
   is an anchored *reader* signal.** The cleanest anchored criterion tested — **publication year**
   (oldness = earlier of modal BrightData `first_published` and minimum UCSD edition year, capped) —
   produces a recognizably canonical head (Moby-Dick #1, Crime and Punishment, Wuthering Heights,
   1984, Pride and Prejudice, Middlemarch, …) with strong stability (fold-jury Jaccard 0.539,
   half-score rho 0.948).

3. **The map + prune cascade turns a latent literary direction into a *true basin* of a carved
   graph.** Iterated weight-gain pruning (remove at once the strongest proponents of the converged
   direction) exposes a literary valley: Brothers Karamazov / Pride and Prejudice head, exact 5 @50,
   anti collapsed 14-19 → 3, and random starts on the survivor graph land in the literary pole as the
   dominant basin (18-24/24). Caveat: the valley geometry is partly manufactured by the seed
   (64% of survivors are seed-jury members by construction), so the *geometry* is real but the
   *framing* that pruning "discovers" the valley does not survive audit.

4. **Random reversal is null; drift is real but size-tuned and lives in the preference head, not the
   direction head.** 1,200 reversed juries across 4 sizes: every processed average has exact 0 @50;
   juries converge onto the HP/ACOTAR/Sanderson genre basin. At exactly 20k-jury size a drift window
   opens (mean exact50 1.54, 29.2% ≥3, 14.2% ≥5) that collapses at 30-60k and reopens at 80k.

5. **Breeding reveals a basin hierarchy, and one genuinely new, strongest literary canon.** 404
   children across 6 parents: convergence ~always (86%), but breeding true is rare (19%); two
   basins dominate (`pairwise_bilateral::s4`, `contrastive_careful::s4`). Seeding a child jury from
   the **top-25 books of summed teacher directions** (book-mediated, not jury-mediated) yields the
   strongest literary aggregate found anywhere: **exact/broad/anti @50 = 17/23/12** (chance
   0.10/0.80/6.17), head = One Hundred Years of Solitude, Crime and Punishment, Lolita, Anna
   Karenina, War and Peace, The Master and Margarita, Brothers Karamazov, 1984, … It self-reproduces
   30/30, survives a cross against the dominant genre basin (never absorbed), but is a basin only of
   its carved survivor graph (13,249 of 233,271 users) — not of the full population.

---

## 1. Data

| artifact | value |
|---|---|
| Candidate works | 26,418 |
| Users | 233,271 |
| (user, work) edges | 7.34M |
| Rating events (rated) | 98,854,143 of 210,633,872 observation-ladder rows |
| Temporal rated events | 99,282,051 rows (95% read in full; 427,908 duplicate edition rows) |
| `is_read=true` / `rating=0` | the defensible "missing-outcome" state |
| Chance @50 (exact/broad/anti) | 0.10 / 0.80 / 6.17 |
| BrightData editions (CSV 7.72 GiB) | 6,354,752; parsed first-published years 6,121,957 |
| UCSD works | 1,521,963 |
| Exact book_id-matched works | 1,255,255 (from 1,256,941 editions) |
| Combined best-year works | 1,423,253 |
| Deep mint | `user_curator_deep_weight` in `data/ucsd_goodreads/explorer.duckdb` |

Machine constraint honored throughout: ~16 GB RAM / 16 cores; heavy matrix work is done
single-process or chunked (no `ProcessPool` copies of the 233k×26k preference/direction matrices).

---

## 2. Jury reconstruction lineage (Aug 5)

The core problem: define *readers* (a "jury") whose five-star behavior measures literary esteem, then
rank books by jury agreement. All early variants are seed-conditioned (titles/author lists loaded
late, as evaluation only).

- **Reverse-engineer lovers** (`REVERSE_ENGINEER_LOVERS_REPORT.md`): seed = poll works (ratings ≥
  2,000), train/test split by poll-rank parity. Lovers are five-star-heavy omnivores
  (reading d ≈ 0.46). Held-out recall@200 = 0.205.
- **Cotraining** (`COTRAINING_FAST` **VETOED**: J@50 0.42→0.38; `COTRAINING` **ACCEPTED**:
  sticky positives × series-binge soft negatives; `COTRAINING_ITER` **ACCEPTED**: Q 54→66.2,
  sticky50 12→14, J@50 0.59→0.62; head Hamlet / Lolita / Poisonwood Bible). Weights:
  `weights_careful_cotrain.json` (default), `weights_iter_sparse.json` (frozen drifted artifact,
  not default).
- **Pairwise esteem** (`PAIRWISE_ESTEEM_REPORT.md`): pairwise_bilateral heldout@50 0.349,
  anti-optional heldout@200 0.535.
- **Jury diagnosis** (`JURY_DIAGNOSIS_REPORT.md`): focus jury 4,774 vs deep jury 19,841; overlap
  41.0%; deep-capped Jaccard 0.100.
- **Deep size sweep** (`DEEP_SIZE_SWEEP_REPORT.md`): top-500 = 13.4% of rating mass; deweight
  ≈15–25 ≡ expo ~0.6–1.
- **Jury rebuild** (`JURY_REBUILD_REPORT.md`, → `JURY_REBUILD_HANDOFF.md`): rich_behavior_global
  jury of **4,929**; OOF Jaccard 0.201, 50.9% of weight.
- **Consensus stability** (`CONSENSUS_STABILITY_PILOT_REPORT.md`): 9 partitions; 157
  mixture-stable, 34 strict.
- **Exposure-adjusted consensus** (`EXPOSURE_ADJUSTED_CONSENSUS_REPORT.md`): 10th-percentile
  estimator; ≥50% community coverage gate.
- **Jury seed trajectories** (`JURY_SEED_TRAJECTORIES_REPORT.md`): 15 universes; 58 central;
  47/50 cumulative core.
- **Consensus multiverse** (`CONSENSUS_MULTIVERSE_REPORT.md`): 45 crossed configurations;
  strict_3286 J@50 0.408, broad_7500 0.493, Γ3 0.852.
- **Target-excluded selection** (`TARGET_EXCLUDED_SELECTION_REPORT.md`): Γ q50 1.80 at 25%
  retention.
- **Stability report** (`STABILITY_REPORT.md`): 25 reshuffles; top-50 overlap 0.58±0.04; 25
  sticky books.
- **Ratings-only canon** (`RATINGS_ONLY_CANON_REPORT.md`): Lizardo/Airoldi/Feldkamp framing;
  naive rarity and depth **fail** (romance/vanity heads); naive HITS **fails** (YA/fantasy hubs);
  `lizardo_high_order` is the best new method with anti50 = 0.
- **Threeway unseeded** (`THREEWAY_UNSEEDED_REPORT.md`): classic 31,803 / anti 221,879 / normie
  33,571; contrastive Q≈72, pos50=22, anti50=0; head Ulysses / Moby-Dick / Paradise Lost / Hamlet /
  Mrs Dalloway / Lolita / Crime and Punishment.
- **Author-level canon** (`AUTHOR_LEVEL_CANON_REPORT.md`): author-level fails the Anglophone poll
  (MC-romance); cross-author PMI recovers **Arabic canons**.
- **Purity/strictness sweep** (`PURITY_STRICTNESS_SWEEP_REPORT.md`): utopia p65_s25 Q=126,
  kish≈2,678, n=3,286, pos50=42; 14-point Pareto front.
- **Feature sensitivity** (`FEATURE_SENSITIVITY_REPORT.md`): load-bearing features
  `midpop_span_per_logn5`, `binge_max_5`, `author_hhi_5`, `series_share_5`, `mean_pub_year_5`.
- **Residual enthusiasm** (`RESIDUAL_ENTHUSIASM_REPORT.md`): best residual_no_author Q=61.5,
  pos50=28, recall@200 0.419.

Idiosyncratic negative results carried forward: generic-only jury collapses (rankable 281,
J@50 ≈ 0.064); seed ensemble shares 27/50 and 111/200 with the final ranking, with a 72-book core
present in ≥11/14 literary top-200s; the rich no-direct-activity jury overlaps the activity jury
at Jaccard 0.813.

---

## 3. Scoring, uncertainty, and the hierarchical model (Aug 6, morning)

These lock the *quantitative* semantics of "is book x canon":

- **Exact expected-inclusion pair estimator** (`EXACT_ESTIMATOR_CONSOLIDATED_REPORT.md`,
  **decision**): M = min(H, L, 12); positive event weight M/H, negative M/L. Median reader
  half-width (u80) **4.62** vs jury bootstrap 0.86 — reader uncertainty dominates.
- **Soft membership / soft jury bootstrap** (`SOFT_MEMBERSHIP_*`, `SOFT_JURY_BOOTSTRAP_*`,
  **decision**): soft jury = bootstrap inclusion q (sums to 4,929 juror-equivalents) preferred over
  hard; soft gains are modest (+0.0035 J@200, −0.15 u80) but reported separately as the primary
  path, hard kept as sensitivity.
- **Temporal**: `TEMPORAL_RATED_EVENTS_*` (read 39.95% of 99.28M rows; 427,908 duplicate edition
  rows); `TEMPORAL_TRAJECTORIES_REPORT.md` calendar holdout J@50 0.266/0.282.
- **Observation ladder** (`OBSERVATION_LADDER_*`): `is_read=true` with `rating=0` is the
  defensible missing-outcome state; 210.6M rows.
- **Current best ranking** (`CURRENT_BEST_RANKING_OVERVIEW.md`): 300 rankable books; mean J@200
  0.769.
- **Hierarchical series** (`HIERARCHICAL_READ_SELECTION_REPORT.md`): read-selection ρ **−0.311**
  vs catalog; popularity audit caps 30/60/120 give partial ρ −0.507; fixed-mass subsamples
  target60 J@50 0.732 / target120 0.886; joint bootstrap u80 4.17 / expanded prior 4,920.
- **Expanded-prior hierarchical model (preferred research ranking, not production default)**:
  empirical Bayes per book×community cell, cap 30/cell, 3.7–4.8 heterogeneity floor; score vs
  catalog readership ρ ≈ −0.311 (hierarchical) / −0.542 (exact-pair).
- **Adversarial community reweighting** (`ADVERSARIAL_COMMUNITY_REWEIGHTING_*`): shared J@50
  0.976, 193 stable / 7 sensitive.
- **Candidate boundary** (`HIERARCHICAL_CANDIDATE_BOUNDARY_REPORT.md`): 4,920; J@50 0.961.
- **Edition/language fragmentation** (`EDITION_LANGUAGE_FRAGMENTATION_REPORT.md`): duplicate-merge
  J = 1.000 (non-issue).
- **Stability synthesis + tiers** (`HIERARCHICAL_STABILITY_SYNTHESIS_REPORT.md`): stable-core tier
  = top-200 robust under all prior/cap/uncertainty/Γ/hard-soft-fuzzy/no-shelf paths, ≥80% joint
  inclusion, survives bounded-community influence, pair mass ≥20, score ≥50 at Γ=2; raised-ceiling
  top-200 cutoff ≈ 49.8.
- **Omission diagnostics** (`EXTERNAL_CANON_OMISSION_AUDIT.md`, `CANON_OMISSION_MECHANISMS_REPORT.md`):
  love_default hits 69/100 of an external top-100; ρ 0.210/0.392/0.143 across metric families.
- **Popularity ceiling counterfactual** (`POPULARITY_CEILING_COUNTERFACTUAL_REPORT.md`): 54
  mega-read books, **0** reach the top-50.
- **Multi-origin seed pilot + audit** (`MULTI_ORIGIN_SEED_PILOT_REPORT.md`,
  `MULTI_ORIGIN_SEED_AUDIT_SYNTHESIS.md`): 9+ origins, behavioral full/quick variants; measures how
  strongly seed choice shapes the result (the honest framing adopted throughout: the seed picks
  *which* of the naturally present taste basins is interpreted as literary).

---

## 4. The seed question: seedless search → identifiability boundary (Aug 6, evening)

Discovery choices frozen **before** titles/authors/years/genres/literary sets were loaded.

| Principle | Implementation | Structural result | Post-hoc result |
|---|---|---|---|
| Signed taste modes | Degree-corrected signed spectral; activity/generosity/popularity/mean/p5 projected out | Strongly non-null, low-evidence modes unstable/localized | Arabic/Bengali literary communities, manga, romance/series islands; **no global literary pole** |
| Evidence/stability | Min readers 100/500/2,000; disjoint-reader principal angles | Leading-8 half-sample agreement 0.105 → 0.718 → 0.857 | Stable objects are still genre/series ecosystems |
| Distributed readers | Rotation-invariant dispersion of 5★ books in stable subspace | Bridge scores replicate (Spearman 0.936–0.941) | Cross-fantasy readers, not literary generalists; exact @50 = 0 |
| Exposure among bridges | Popularity-adjusted cohort enrichment | Replicates (Spearman ≈0.86) | Stable Arabic reading community |
| Random-origin reconstruction | 32 random juries reweighted by agreement | Correlations 0.939 → 0.9994 | Local attractors + Goodreads love center |
| Equal-attractor center | All basins equal mass; mean/q10/mean−SD | Top-200 overlap 0.67–0.72 | Sanderson, Calvin & Hobbes, HP, social nonfiction; 0 exact literary in q10 top-200 |
| Cultural nestedness | Excess audience containment, full natural collection sizes, 120k users | Spearman 0.971–0.980 | Romance/urban-fantasy cores; 0 exact AND 0 broad through rank 500 |

**Verdict (`SEEDLESS_CANON_SYNTHESIS.md`):** an identifiability boundary. The tuple matrix
describes cultural regions, stability, bridging, and centrality — it does not label why one stable
hierarchy is more "literary" than another. Every plausible symmetry (size, rarity, stinginess,
breadth, nestedness, stability) was tested and none uniquely encodes literary prestige. The
recommended next step was explicitly **not** another unsupervised clusterer but one *minimal
explicit ordering principle* (durability / year) — which is exactly the year-aware path taken next.

---

## 5. Year-aware canon and the metadata audit (Aug 6, evening)

### 5.1 BrightData metadata (`BRIGHTDATA_METADATA_AUDIT_REPORT.md`)

- Work year = earlier of modal BrightData `first_published` (across matched editions) and minimum
  UCSD edition year; a claimed first publication cannot postdate an observed edition.
- BD earlier for 186,119 works, later for 8,160; median absolute gap 0; 877 flagged
  `ancient_year_era_uncertain` (BCE/CE not reliable, e.g. Homer 701) — irrelevant because all are
  already at the oldness cap.
- Clean dates: Moby-Dick 1851/1851/1923; Brothers Karamazov 1880; Gatsby 1925; Ulysses 1922;
  100 Years of Solitude 1967. 72 works have >1 BD year; 441,914/478,278 author names agree.

### 5.2 Year-aware pilot (`YEAR_AWARE_CANON_PILOT_REPORT.md`)

Design: oldness = 0 at 2000 → 1 at 1850; four-star neutral; reader score deducts uncertainty;
balanced top/bottom-10% cohorts; **cross-fit by work-ID parity** (a book's year never enters its own
score). Coverage 26,403/26,418 works (24,990 exact-joined BD years); runtime 84.2s.

Primary `best_linear_q10` (old-jury minus contemporary-jury): exact/broad/anti @50 = **11/21/0**
(anti 0), head: Macbeth, 1984, Hamlet, LOTR Fellowship/Two Towers, Sense and Sensibility, Animal
Farm, Othello, The Odyssey, Alice, One Flew Over the Cuckoo's Nest, Huckleberry Finn, Brave New
World …

Stability (fold-jury Jaccard / half-score rho): 0.539 / 0.948; half J@50 0.729, J@100 0.717,
J@200 0.702, J@500 0.658.

**Old/new cohort contrast** (the cleanest "who" result): classics (Austen, Dickens, Shakespeare,
Carroll, Kafka, Steinbeck, Homer, etc.) score high via *old* readers and negative via *new* readers
(e.g. Huckleberry Finn old +0.076 / new −0.913; Othello +0.328 / −0.882); Tolkien/children's
classics score via both; Pynchon/Vonnegut/20c-modern via new.

Definition sensitivity vs primary contrast ranking (J@50/J@200): `best_linear1800_q10` 0.923/0.887
(endpoint 1800); `best_linear1900_q10` 0.923/0.887; `ucsd_linear_q10` 0.639/0.569 (how much the
repaired dates matter); `bright_linear_q10` 0.370/0.303; `best_preference_q10` 0.205/0.208 (within-
reader old-vs-new jury, rho 0.952, **zero anti through rank 500**, recovers Moby-Dick #22,
Middlemarch #29, Don Quixote #44, Ulysses #126, Gatsby #174); `best_linear_q10_all` 0.075/0.090
(matched low-old contrast is **essential**). All-time stable head is covered in §0.

### 5.3 Year-jury attractor trajectories (`YEAR_JURY_ATTRACTOR_REPORT.md`)

12 paths (4 juries × 3 betas): all genuinely contract (final step corr ≥ 0.9998), but retain only
45–63% of the initial direction and collapse projected top-200 Jaccard to 0.081–0.124; heads mix
classics with YA/paranormal/fantasy. "The unconstrained stability iteration washes out the literary
year signal rather than refining it" — which motivates the *pruning* idea.

---

## 6. Attractor pruning: collapse, valley, and the audit (Aug 6, evening)

### 6.1 The main run (`ATTRACTOR_PRUNING_REPORT.md`, 9 paths, 113.3s)

- **Unpruned baseline**: collapses to the Goodreads love center (exact 0/1 @50, anti 2/19), only
  0.463 of the literary direction retained.
- **Gradual pruning (5%/stage) barely moves the basin** (gain-pruning 0.463→0.55; top-weight
  degrades to 0.19–0.37 with anti leakage; random flat ~0.46). None hit the 0.70 threshold.
- **The qualitative change needs simultaneous removal of co-opted users**: removing the top-43%
  by weight-gain at once lifts retained 0.463 → 0.538 → 0.702 (stage 2).
- **Continuing to 0.85 exposes an enclosed literary valley**: step correlation reaches exactly
  1.00000; retained vs full-matrix plateaus ~0.724 before degrading to 0.626 at evidence floor
  (stage 5, 15,395 of 233,271 users, 93.4% removed).
- **Deep-pruned head is canonical**: Brothers Karamazov #1, Pride and Prejudice #2, Poe, Hamlet,
  Persuasion, Divine Comedy, Count of Monte Cristo; exact 0 → 3 → 5 @50; anti collapses 14–19 → 3.
  Random control at comparable/lower mass never exceeds 0.46 retained and keeps anti ≥ 7/21 — the
  effect is **who** is removed, not how much.
- **Proponents of contraction are old-book-loving omnivores** (old-love share 0.144 vs 0.075;
  positive old-vs-new preference).

### 6.2 Pre-year reversal (`ATTRACTOR_PRUNING_PREYEAR_REPORT.md`, 5 candidates, 52.1s)

- **Every pre-year literary construction collapses under the unpruned map** (retained vs start
  0.27–0.44, exact 0/1 @50, heads mixing classics with YA/paranormal). The pre-year failures were
  never observed only because the map was never started from them.
- **Gain-hard reversal splits by candidate kind**: the three *user-jury* candidates
  (teacher_p65_s25, rebuilt hard/soft) rise to 0.53–0.66 retained but end in paranormal-romance
  heads (anti 17–28 @50; rebuilt_soft pooled pole = Shadowfever/Kate Daniels).
- **The two *book-space* candidates reach a dominant literary valley**: contrastive_careful stage 4
  (unpaired census 21/1) and pairwise_bilateral stage 5 (22/0) — **more literary than the year
  jury's 18/6** — pooled consensus heads exact/broad/anti @50 = 10/17/7 (contrastive: C&P,
  Poisonwood Bible, Middlesex, Hamlet) and 9/14/11 (pairwise: East of Eden, Hamlet, Importance of
  Being Earnest, Lolita).
- **What years still do**: keep the gain-hard path *inside* the valley at its deepest point
  (retained 0.70, census 18/6); pre-year book candidates are literary only below the 0.70 retained
  threshold (0.50/0.43). Years do not create the basin — pre-year starts reach a deeper one — but
  they make it enclosing from the start.

### 6.3 The audit (`ATTRACTOR_PRUNING_AUDIT_REPORT.md`, 42.5s)

Three suspicions checked against the gain-hard path:

1. **Convergence is not trivial**: step corr 0.9499 → 0.999872 → 1.000000 (float-exact fixed
   point); effective user share 0.62–0.70 throughout (no small elite captures the weights).
2. **Seed echo is largely right about the population**: stage-5 survivors are 76.5% either-fold /
   64.4% both-fold year-jury members (baseline 10.8%/4.3%) — pruning-by-gain retains the seed by
   construction, so stage-level "retained direction" is weak valley evidence on its own.
3. **But the valley is reachable seedlessly on the carved graph**: random 3%-cohort starts on the
   full population find no literary pole (max corr 0.478; basins = love center + mirror); on the
   stage-5 population the geometry has exactly two attractors — literary pole vs paranormal-romance
   mirror — and among *unpaired* starts the literary pole wins 18/6. The pooled literary-pole head
   is essentially the seeded head (same metrics: exact 5, broad 12, anti 3).

**Verdict:** convergence real; seeded head not an artifact *of the carved geometry*; but the
valley framing ("pruning discovers the valley") does not survive — the geometry was manufactured by
the seeded pruning. The genuine novelty: gain-pruning specifically (not random pruning of the same
mass) creates a geometry with a literary pole as the dominant attractor; the mirror pole (paranormal
romance / urban fantasy) exists in the same geometry, so **ratings alone still do not say which end
is 'literary'** — the identifiability boundary stands.

---

## 7. Ensemble reversal: is there a *natural* literary center? (Aug 7)

Random juries → stage-0 collapse → gain-hard reversal. All averages/aggregates frozen before
literary scoring. **Negative result**, consistently:

| run | config | endpoint agreement (mean pairwise dir corr) | processed averages exact @50 | per-jury exact ≥3 |
|---|---|---|---|---|
| Pilot | 3×1500/3000 | 0.042 | 0 | — |
| Pilot2 | 4×1500/3000 | 0.028 | 0 | — |
| Rehearsal + 2 | 25×2000/5000 | 0.074 | 0 | 0/25 (median deepest 14,015) |
| **Overnight** | **300 × 2000/5000/10000/20000** | 0.087 → 0.199 → 0.268 | 0/0 @50/@200 (all aggregates) | see below |

Overnight per-size endpoint distribution (@50) and endpoint agreement — the drift window:

| size | endpoint corr (mean) | exact mean / med / max | anti mean | frac exact ≥3 | frac broad ≥5 | basin census |
|---|---:|---:|---:|---:|---:|---|
| 2,000 | 0.087 | 0.11 / 0 / 2 | 19.3 | 0/300 | 6/300 | 2 basins (268/32), genre+romance heads |
| 5,000 | 0.164 | 0.13 / 0 / 4 | 24.1 | 5/300 | 2/300 | 1 basin, genre head |
| 10,000 | 0.199 | 0.14 / 0 / 1 | 23.8 | 0/300 | 0/300 | 1 basin, genre head |
| **20,000** | 0.268 | **1.56 / 0 / 9** | 26.4 | **98/300** | **86/300** | 1 basin, genre head |

Every processed average (center_stage0, plain_mean, coordinate_median, agreement_consensus,
mean_displacement, big_jury_control) has **exact = 0 @50 and @200**; the aggregate heads are
HP / ACOTAR / Sanderson / Martin / The Hate U Give, with the *center* head dominated by Calvin &
Hobbes, March, and social nonfiction. Endpoint agreement *rises* with jury size (0.087→0.268) —
reversed juries converge onto the genre basin, not a literary one. Only size 20k produces
individual literary-leaning juries, and ensembles wash them to zero. Run via
`scripts/research_jury_ensemble_reversal.py` (seed 20260808, 3864.2s, service
`novels-ensemble-reversal.service`), checkpointed every 10 juries.

### 7.1 Drift exploit (`DRIFT_EXPLOIT_REPORT.md`, tag=main, seed 20260811)

The size-20k window is a real, reproducible phenomenon:

- Sweep 120 juries × 6 sizes: mean exact50 **1.54 @20k (29.2% ≥3, 14.2% ≥5)**, collapses at 30k
  (0.31) / 45k (0.09) / 60k (0.13), secondary bump @80k (0.43, 6.7%).
- **Drift lives in the preference head** (top-25 mass ≥25 books; users 0.4 + 19.6×frac5), **not**
  the direction head (hub domination). `split_smoke.*` (Aug 7, no report): the 80k literary drifter
  (parent d561, exact 8, anti 0) carries its signal in a **subgroup** — 4 subgroups exact
  0/7/1/4 (anti 46/6/3/7); 4 control subgroups exact 0; enrichment 1.71 vs 0.0.
- Amplification (52 drifters + 6 controls + 3 clusters + 4 ensembles = 65 runs): 6 deep literary
  canons (exact ≥3 AND cos(pole) ≥ 0.5): d561, d567, d713 (80–110k, anti 0), d564, d9 (20k, exact
  4/5/5 both smokes and main), d480 — heads mix Russian classics (C&P, Karamazov) with graphic
  literature (Maus, Persepolis, Watchmen, Arrival), Sherlock Holmes, Coates' Between the World and
  Me. Size matters: 80k = 4/8 deep; 110k 1/4; 20k 1/35 (abundant, noisy). Controls never succeed
  (6/6 genre heads). Ensembles blur (majority of drifters lean genre).
- **Honesty note**: drifters are selected with eval labels; amplification itself is label-free.
  Single clean drifters beat every aggregation.

---

## 8. Breeding: basin hierarchy and the 17/23/12 pole (Aug 7)

Parents = converged directions of gain-hard paths (6 canons, 21 pairs, 404 children; 1338s seed
20260807; B-run seed 20260808 ~1100s).

Parent direction correlations: teacher s3 is nearly orthogonal to everything (0.02–0.12); the
`contrastive_careful`/`pairwise_bilateral` cluster is tight (0.53–0.88); teacher s5 is a weak
bridge (0.33–0.45).

**Convergence**: jury_mix converges 275/321 (86%, another 5 stop already-converged), but breeds
**true 62, ties 2, lean 105, NEW 152 (47%)**.

**Attraction matrix (reproduced 18/21 identical across seeds)**:
- `pairwise_bilateral::s4` **dominant**: absorbs own s5 (21/21 true), contrastive s4 (19 true),
  contrastive s5 (18 true), teacher s5 (3 true + 18 lean).
- `contrastive_careful::s4` second: absorbs teacher s5 (21/21 lean), wins pairwise s5 (1 true + 20
  lean).
- `teacher_p65_s25::s3`, `contrastive::s5`, `pairwise::s5` **never win** — source canons.
- **Breeding any two source canons → 21/21 new basins**, all non-literary (Colleen-Hoover romance,
  Calvin & Hobbes eclectic, HP/fantasy).
- Polyamory (3 parents) is deterministic, all lean to contrastive_careful::s4 (cos 0.39/0.71).
- Controls: self-breeding *drifts* for 4/6 canons (cos to self 0.14–0.70); half-random controls all
  land non-literary (exact 0). Increment size is irrelevant to convergence (all ≥0.9995) but larger
  increments are *worse* for literaryness (hard_mult 2.0 overshoots); hard_mult 1.25 is the
  operating point.

### 8.1 The night's discovery: a new literary pole via direction-mix

Breeding the two teacher canons (s5 × s3, corr 0.38) through the **book-mediated channel**
(seed the child jury from the top-25 books of the summed parent directions):

- **exact/broad/anti @50 = 17/23/12** — the strongest literary aggregate anywhere in the project
  (prior best: contrastive s4 at 9/16/6).
- Head (top 16 all literary): One Hundred Years of Solitude, Crime and Punishment, Lolita, Anna
  Karenina, The Stranger, The Metamorphosis, The Brothers Karamazov, 1984, War and Peace, The
  Master and Margarita, Moby-Dick, To Kill a Mockingbird, The Sound and the Fury, Stoner, The
  Trial, Don Quixote (then Infinite Jest, The Idiot, Ficciones, Hamlet, Ulysses, Blood Meridian).
- Trajectory: stage 0 exact 0 → stage 2: 5/9/14 → stage 4: 16/24/1 → stage 5: 17/23/12; oscillates
  past parents (cos 0.38→0.51→0.38) — a genuinely **new basin**. 94.3% of users pruned (13,249 of
  233,271 survivors).
- Valley audit: 19/24 random starts on its survivor graph land in the literary pole.
- Deterministic → identical in seed-20260808 rerun and as generation-3 of the tournament collapse.
  The *same* parents via jury-half mixing land in the Colleen-Hoover romance basin (exact 0).
- **Books mediate the pole; juries do not.** The literary consensus lives in *what readers jointly
  hold*, not in who the readers are.

### 8.2 Dawn addendum: does the pole survive the dominant genre basin? (`pole_vs_genre.json`)

- **pole × pole (self): 30/30 identical, exact 17/23/13**, single head (C&P, 100 Years of Solitude,
  Anna Karenina, War and Peace, Master and Margarita) — a stable, self-reproducing canon.
- **pole × pairwise-s4 (genre-dominant): 60 children, all "new" — the genre basin does NOT absorb
  the pole.** Hybrid basin (cos 0.30/0.29) exact 9–13 @50, head led by Lolita, The Metamorphosis,
  East of Eden, 100 Years of Solitude, C&P — more literary than the genre parent, never pure genre.
- **pole × contrastive-s4: genuinely new basin** (cos ≈ 0.02 to all parents), exact 9/13/11 — two
  0.52-correlated literary canons still yield literary offspring.
- A flat "20/0.4 jury of the pole's readers" does **not** map back into the pole on the full graph
  (converges to the mirror basin) — the pole is a basin only of the carved survivor graph.
- `pole_vs_true_genre.json`: pole × genre via jury_mix → new, exact 3/broad 5/anti 36 — jury-mix
  again degrades literaryness.

### 8.3 Seedless census at scale (`SEEDLESS_ATTRACTOR_CENSUS_BREEDNIGHT_B25/B15/B40_REPORT.md`)

1000 starts @2.5 → **194 basins** (top two: 198 and 195 starts, HP/Sanderson/Calvin-and-Hobbes
zones); 512 @4.0 → 137; 512 @1.5 → 130. **No basin at any beta has a literary head** (exact @50 =
0 across all basins; broad ≤1; anti 2–30). Random dynamics in the full graph: dozens of
genre/fandom valleys, **zero literary basin volume**. Equal-basin center = Sanderson / Calvin &
Hobbes / HP / recent social nonfiction.

---

## 9. Synthesis: what is, and is not, identified

1. **Not an attractor of raw dynamics.** 1,000 random starts, 1,200 reversed juries, 3 betas, and
   the spectral/nestedness/bridge searches: zero literary basins, zero exact overlap. Any account
   of a "natural distributed literary canon" on Goodreads is falsified by the unsupervised record.
2. **Latent and carvable.** Literary seeds + iterative gain-hard pruning find real canons
   (contrastive s4 9/16/6; pairwise s4 9/13/4), and the map+prune cascade turns a latent literary
   direction into a *true basin* of the survivor graph (valley audits 18–24/24), reproducible
   across seeds. The strongest pole (17/23/12) is produced by book-mediated (not jury-mediated)
   breeding.
3. **The honest framing is a chosen preference.** Publication year is the least prescriptive
   *anchored* criterion that works; it is stable (fold-jury 0.539, rho 0.948), canonical in content,
   and its "who" is a coherent population (old-book-loving omnivores are *not* a separate literary
   population — they are the pull-to-center carriers). But ratings alone cannot label which of two
   mirror poles (literary vs paranormal romance) is "literary": the identifiability boundary is
   intrinsic.
4. **Readership ≠ canon.** Score vs catalog readership ρ ≈ −0.311; popularity ceilings and
   read-rate adjustments matter; mega-read books never crack the top-50.
5. **Reader uncertainty dominates jury uncertainty** (u80 4.62 vs 0.86); the hierarchical
   expanded-prior model is the preferred research ranking.

---

## 10. Open threads (as of last run)

- **Label-free selection** for drifters: can literary vs genre lean be read without eval sets
  (cosine to known genre basin vs pole; Maus/Borges head signature)?
- **Iterated amplification** of produced canons (2 rounds) toward cos(pole) ≥ 0.8.
- **80k-jury window**: cleanest per-jury yield; ~3× cost of 20k.
- **Weight-classes for ELO comparisons** (from the review) — untested.
- **Subgroup structure** of the 80k drifter (`split_smoke.*`, no report): the literary signal
  concentrates in a user subgroup (0/7/1/4 across 4 subgroups) — needs a full report and a
  mechanism.
- **Promote the 17/23/12 pole**: full 200-head analysis, larger valley census, self-iteration
  through books.
- **Direction-mix on more sibling pairs** (contrastive s4×s5 already Borges-leaning 7/13/19) — is
  the pole unique to the teacher family?
- **Full 200-head + valley census of the year-aware primary** (`best_linear_q10`), and whether
  year-aware + pole-prune compose.
- **Seedless durability** (timestamps-only persistence) as the next minimal explicit principle, per
  `SEEDLESS_CANON_SYNTHESIS.md`.

---

## 11. Artifact inventory (key)

- **Reports**: `data/*.md` (all listed in §2–§8); orientation `JURY_REBUILD_HANDOFF.md`.
- **Weights**: `data/weights_careful_cotrain.json` (default), `data/weights_iter_sparse.json`
  (frozen, non-default).
- **Mint**: `user_curator_deep_weight` in `data/ucsd_goodreads/explorer.duckdb`; plus
  `brightdata_work_metadata` table.
- **Campaign artifacts**: `ensemble_reversal_overnight.log` + status JSON; `canon_breeding_overnight
  {,_b}.json` + directions `.npz`; `breednight_census_{b25,b15,b40}.log`; `drift_exploit_main*
  {,.npz,.json}`; `split_smoke.{json,npz}`; `pole_vs_genre.json`, `pole_vs_true_genre.json`.
- **Large caches** (spectral/nestedness/temporal/observation matrices, `.npz`/`.parquet`) are local
  generated artifacts and should not be committed.

---

*Sources: 60+ research reports in `curators_explorer/data/`, read in full; the four overnight
campaigns; and the year/attractor/drift/breeding JSON evidence files. All literary/anti sets were
evaluation probes loaded only after the relevant discovery choices were frozen.*

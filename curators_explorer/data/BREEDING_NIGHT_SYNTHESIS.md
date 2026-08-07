# Breeding Night — Synthesis (2026-08-07)

Four experiments ran overnight, all against the same 26,418-book / 233,271-user
Goodreads graph (7.34M edges; chance @50 = exact 0.10, broad 0.80, anti 6.17):

| experiment | scale | runtime | output |
|---|---|---|---|
| canon breeding (seed 20260807) | 6 canons, 21 pairs, 404 children | 1338s | `canon_breeding_overnight.json` / `CANNON_BREEDING_OVERNIGHT_REPORT.md` |
| canon breeding (seed 20260808, reproducibility) | same design | ~1100s | `canon_breeding_overnight_b.*` |
| seedless census | 1000 starts @2.5; 512 @1.5; 512 @4.0 | 334+175+173s | `SEEDLESS_ATTRACTOR_CENSUS_BREEDNIGHT_B25/B15/B40_REPORT.md` |
| ensemble reversal | 300 juries × 4 sizes | 3864s | `JURY_ENSEMBLE_REVERSAL_OVERNIGHT_REPORT.md` |

## 1. Does breeding converge? To which parent? Or to a new canon?

Jury-half mixes (`jury_mix`) converge almost always — 275/321 (86%) reach
final-step correlation ≥ 0.999 (another 5 stop at stage 0 already converged).
But they rarely breed true: **62 true, 2 ties, 105 lean, 152 new (47%)**.

The attraction matrix (n=21 children per pair, 20 jitter reps + base) shows a
clear basin hierarchy, reproduced almost exactly with a second seed (18/21
pairs identical; the other 3 differ by one child at a classification boundary):

- `pairwise_bilateral::s4` is the dominant basin: absorbs its own sibling s5
  (21/21 true), contrastive s4 (19 true), contrastive s5 (18 true), teacher s5
  (3 true + 18 lean).
- `contrastive_careful::s4` is second: absorbs teacher s5 (21/21 lean), wins
  pairwise s5 (1 true + 20 lean).
- `teacher_p65_s25::s3`, `contrastive::s5`, `pairwise::s5` never win a child
  from another family — they are source canons.
- Breeding any two source canons yields **21/21 new basins**, all non-literary
  (Colleen-Hoover romance, Calvin & Hobbes eclectic basin, HP/fantasy).
- Polyamory (3 parents, 3 reps): deterministic — all lean to
  `contrastive_careful::s4` (cos 0.39/0.71).
- Controls: self-breeding *drifts* for 4/6 canons (`self:drifted`, cos to self
  0.14–0.70); half-random controls all land non-literary (exact 0).

## 2. The increment question: does a larger pruning step converge more strongly?

No. All eight variants (hard_mult 0.75/1.0/1.5/2.0, ladder 0.10/0.20, beta
3.5/5.0) reach final-step correlations ≥ 0.9995 — convergence strength is
already saturated. Larger increments are instead *worse for literaryness*:
hard_mult 2.0 overshoots (stage-1 `nothing_removed`, exact 0 @50). The standard
hard_mult 1.25 cascade is the right operating point.

## 3. The night's main discovery: a new, strong literary pole via direction-mix

Breeding the two *teacher* canons (s5 × s3, only 0.38-correlated) through the
**book-mediated channel** (seed the child jury from the top-25 books of the
summed parent directions) produces a genuine **new literary canon**:

- exact/broad/anti @50 = **17 / 23 / 12** (chance 0.1 / 0.8 / 6.2) — the
  strongest literary aggregate found anywhere in this project (best prior
  canon: contrastive s4 at 9/16/6).
- Head (top 16 ALL literary): One Hundred Years of Solitude, Crime and
  Punishment, Lolita, Anna Karenina, The Stranger, The Metamorphosis, The
  Brothers Karamazov, 1984, War and Peace, The Master and Margarita, Moby-Dick,
  To Kill a Mockingbird, The Sound and the Fury, Stoner, The Trial, Don Quixote
  (then Infinite Jest, The Idiot, Ficciones, Hamlet, Ulysses, Blood Meridian).
- Trajectory: stage 0 exact 0 → stage 2: 5/9/14 → **stage 4: 16/24/1** →
  stage 5 (final): 17/23/12. The child oscillates past its parents
  (cos 0.38→0.51→0.38) before settling — it is a *new basin*, not a parent
  basin. 94.3% of users pruned away (13,249 of 233,271 survivors).
- Valley audit: 19/24 random starts on the survivor graph land in the literary
  pole (24-start census) — the carved graph makes the pole a true basin.
- Deterministic (no rng) → identical result in the seed-20260808 rerun, and
  again as generation-3 of the tournament collapse. The *same* parents bred via
  jury-half mixing instead land in the Colleen Hoover romance basin (exact 0).

The generation tournament (direction-mix of the closest pair each round,
parents removed — 5 rounds to a single canon) shows every generation child is
"new": breeding compounds away from parents. The literary pole appears exactly
when a pair of teacher-family canons is combined through books, and the final
collapsed canon is a mixture that no longer has a literary head.

## 4. Seedless census at scale: how many stability zones?

1000 random starts @ beta 2.5 → **194 basins** (top two: 198 and 195 starts —
HP/Sanderson/Calvin-and-Hobbes genre zones); 512 @ beta 4.0 → 137 basins; 512
@ beta 1.5 → 130 basins. **No basin at any beta has a literary head**
(exact @50 = 0 across all basins; broad ≤ 1; anti 2–30). Random dynamics in
the full graph have dozens of genre/fandom valleys and **zero literary basin
volume**.

## 5. Ensemble reversal at scale: is there a natural literary center?

300 juries × sizes 2000/5000/10000/20000: every processed average (plain mean,
coordinate median, agreement consensus, mean displacement, center) has
**exact = 0 @50 and @200**; the basin census of reversed endpoints is
non-literary (HP/romance/Sanderson); endpoint agreement *rises* with jury size
(0.087 → 0.268) — reversed juries converge onto the genre basin, not a literary
one. Only at size 20,000 do 98/300 individual juries reach exact ≥ 3, but the
ensemble still washes to zero.

## 6. What this says about a "natural distributed literary canon"

1. **It is not an attractor of the raw dynamics.** Nothing random finds it:
   1000 starts, 1200 reversed juries, 3 betas — zero literary basins.
2. **It is latent and carvable.** Literary seeds + iterative pruning find
   canons (contrastive s4: 9/16/6; pairwise s4: 9/13/4), and the map+prune
   cascade converts the latent literary direction into a *true basin* of the
   survivor graph (19–24/24 valley audits).
3. **Books mediate the pole; juries do not.** Mixing literary juries
   (jury halves) falls into romance/eclectic basins; seeding from the top-25
   books of summed literary directions finds the strongest pole yet
   (17/23/12). The literary consensus lives in *what readers jointly hold*,
   not in who the readers are.
4. **Convergence is saturated.** Increment size does not change final
   convergence; bigger steps overshoot.

## 7. Dawn addendum: does the literary pole survive the dominant genre basin?

The decisive test: cross the 17/23/12 pole (rebuilt with its true converged
weights; pole × pairwise s4 direction correlation 0.754) against the strongest
genre valley, pairwise s4 (30 jitter reps), and against the contrastive
literary canon (0.519 corr), plus pole self-breeding (30 reps)
(`research_pole_vs_genre.py` → `pole_vs_genre.json`):

- **pole × pole (self): 30/30 identical, exact 17/23/13, single head**
  (Crime and Punishment, 100 Years of Solitude, Anna Karenina, War and Peace,
  The Master and Margarita). The pole is a stable, self-reproducing canon in
  content.
- **pole × pairwise-s4 (genre-dominant): 60 children, all "new" — the genre
  basin does NOT absorb the pole.** Children land in a hybrid basin
  (cos 0.30/0.29 to the parents) with exact 9–13 @50, head led by Lolita,
  The Metamorphosis, East of Eden, 100 Years of Solitude, Crime and
  Punishment — more literary than the genre parent, never pure genre.
- **pole × contrastive-s4: a genuinely new basin** (cos ≈ 0.02 to all
  parents), exact 9/13/11 — breeding two literary canons that are only 0.52
  correlated still yields literary offspring.
- A flat "20/0.4 jury of the pole's readers" does NOT map back into the pole
  on the full graph (it converges to the mirror basin) — the pole is a basin
  only of the carved survivor graph, not of the full population.

## 8. Next steps (dawn experiment)

- Promote the 17/23/12 pole: full 200-head analysis, larger valley census on
  its survivor graph, and self-iteration (it is now a basin, so breeding it
  with itself through books should be stable).
- Direction-mix on more sibling pairs (contrastive s4×s5 already shows a
  Borges-leaning 7/13/19 head) — is the literary pole unique to the teacher
  family?
- Cross the teacher literary pole with the pairwise s4 genre-dominant basin:
  does the genre basin win (as reversal suggests) or the literary pole?

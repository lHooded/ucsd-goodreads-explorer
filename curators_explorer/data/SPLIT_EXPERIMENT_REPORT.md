# Jury-Splitting ("Trench Coat") Experiment Report (tag=main, seed=20260813)

## Question
80k/110k reversed juries with *mixed* literary heads (Karamazov + C&P + HP +
Maus in one head) look like several taste schools in a trench coat: the whole
jury cannot fit into one small literary basin.  Hypothesis: splitting the
**same user set** into smaller juries should resolve the components into
purer, distinct basins.

## Method
- Recovered the exact user set of every stored 80k/110k jury by replaying the
  sweep's RNG stream (the only random draws per jury are `rng.choice` in
  `make_jury_seed`; `iterate_map` and `remove_fraction` gain/hard are
  rng-free).  **Verified bit-for-bit**: re-running juries on recovered users
  reproduces the stored endpoints exactly (maxdiff 0).
- Parents: 12 literary drifters (exact50 >= 3 at 80k/110k) + 6 control juries
  (exact 0 at 80k/110k).  205 subgroup runs + 65 ladder runs, all under
  systemd memory/CPU caps (MemoryMax=4G, CPUQuota=200%, Nice=15).
- Split methods:
  - `random` (baseline): 80k -> 4x20k, 110k -> 5x22k
  - `mode2`: sign of the 2nd left singular vector of the parent submatrix
    (the "two schools" decomposition)
  - `mode2q3`: 3 quantiles of the 2nd mode loading
  - `affinity`: median split by cos(user row, parent endpoint pref)
  - `ladder`: random 2x40k/2x55k and 8x10k/8x13.75k on three parents
- Subgroups run through the identical reversal (retained 1.01, evidence
  floor) and scored with the same eval sets.
- Honesty: parents are label-selected; subgroup dynamics and scoring are
  label-free until the final step.

## Results

### 1. The trench coat is real — and universal
Random 20k subgroups of **control juries** (genre-headed at 80k/110k) drift
literary at **48%** (13/27, mean exact 1.89) — *above* the 29% baseline for
fresh random 20k juries.  Literary-parent subgroups: 36.5%.  One control
(d623, Stormlight-headed) produced 4/5 literary subgroups at 22k.  Every big
jury mixes literary + genre + graphic schools; the endpoint only reflects the
dominant school.  The 80k endpoint lean does NOT predict the subgroup lean.

### 2. The 20k resonance (size dependence within the same users)
Ladder on d561 (literary), d713 (literary), d623 (control):
- ~20-22k subgroups: literary drift appears (2/4, 1/5, 4/5)
- 40-55k subgroups: dead zone (exact 0-1) — confirmed *inside the same user
  set*, not just across jury sizes
- 10-14k subgroups: exact 0 (too small), but several show cos_pole 0.4-0.6
  with genre heads (unstable direction near the pole region, no eval overlap)

### 3. Deterministic splits separate the big schools, not the literary one
- `mode2` on d561: subgroup A -> HP; subgroup B -> Calvin & Hobbes / Maus /
  Stormlight.  The 2nd singular mode resolves HP vs graphic — the two largest
  schools — but the literary school is a minority component below the top
  modes.  frac_ge3: 4% (literary parents), 8% (controls); mean cos_pole
  0.18 vs 0.04 random — mode2 does push directions closer to the pole.
- `mode2q3`: 0% everywhere — over-segmentation destroys the signal.
- `affinity`: 0% ge3 (splits agreement-with-the-compromise; both halves land
  genre).  High anti (17-23) throughout.
- **Conclusion: the literary school cannot be isolated by the dominant-mode
  decomposition; random splitting finds it more often (36-48%).**

### 4. Two flavors of literary drift at 20k
- "dirty" (endpoint anti 3-12): abundant, present in every jury's subgroups,
  exact 3-5, cos_pole ~0.02 (far from the pole basin).
- "clean" (endpoint anti <= 2): rare, only the 80k/110k drifters; these are
  the ones that amplify forward to cos_pole 0.6-0.73 (drift-exploit results).
- Drift endpoints as a whole sit at cos_pole ~0.03 (same as all endpoints) —
  the drift basin is a *vestibule* of the pole basin, reachable by forward
  amplification but not by direction cosine.

## Interpretation
The user's theory is confirmed: large juries are superpositions; small
juries resolve them.  But the resolution is probabilistic: ~40% of any 20k
slice of an 80k jury drifts literary, because the literary school is
*ubiquitous* at the 20k scale (~a third of random 20k juries drift anyway).
The dead zone 30-60k is the mixed-coat regime where no single school
dominates.  Deterministic mode-based splitting is the wrong tool for the
literary school specifically (it is not a top-2 mode); random splitting is
the better detector, and clean (anti<=2) endpoints remain the best
amplification seeds.

## Artifacts
- split_main.npz/json/_analysis.json (205 subgroup runs, 18 parents x 4
  methods)
- split_ladder.npz/json/_analysis.json (65 runs: 2x40k + 8x10k on 561/713/623)
- split_smoke / split_memtest: validation runs (mode2 path, 110k parent)
- research_jury_split_experiment.py: replay/verify/split/analyze phases

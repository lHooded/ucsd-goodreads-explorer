# Recursive descendant families report

**Fragmentation test**: does the old 20k literary basin fragment into recurrent 10k descendant families, and can a rolling descendant-family compass (G10) be followed at 10k?

- Descendant seed **20260824**; follow replicates **24**; 5k descendant replicates **24**; breeding seed 20260822.
- Part A uses ONLY the 48 already-saved 10k literary child endpoints; the natural geometric partition is frozen BEFORE any semantic context is loaded.  G10 choice is an explicit one-time SEMANTIC BRANCH CHOICE among cross-root recurrent families.
- Part C uses NEW independent partitions and NEW reversal runs; user selection uses only deepest-endpoint cos(child, G10) inside randomized child juries.  No semantic labels, no old F1/F0, no direct user-to-G10 affinity in selection.
- Run complete: **True**; git head `3b4fb12d24f8`; artifact sha256 `e68ecd627eddd8d8...`.

## 1. Previous 20k lineage being followed

- Root 0 literary 20k: margin +0.6244, exact@50 5, broad@50 8, anti@50 8; its 10k descendants under the OLD fixed-F1 compass: margin +0.0047, exact@50 0, anti@50 27 (the collapse this experiment re-examines).
- Root 1 literary 20k: margin +0.6292, exact@50 3, broad@50 4, anti@50 10; its 10k descendants under the OLD fixed-F1 compass: margin +0.0347, exact@50 1, anti@50 23 (the collapse this experiment re-examines).

## 2. Saved 48-endpoint 10k descendant geometry

Pooled pairwise cosine: mean 0.7245, q25 0.6517, median 0.6630, q75 0.8092, min 0.6189, max 0.8231.

Natural geometric cut: k = **2** (average silhouette 0.4260); silhouettes by k: k=2: 0.4260, k=3: 0.2732, k=4: 0.2578, k=5: 0.2521, k=6: 0.0718, k=7: 0.0533, k=8: 0.0307.

Fixed cosine cuts (descriptive robustness only):

| tau | n clusters | sizes |
|---|---:|---|
| 0.30 | 1 | [48] |
| 0.50 | 1 | [48] |
| 0.70 | 2 | [24, 24] |

## 3. Natural 10k families

| family | n | root0 reps | root1 reps | within cos (mean/med) | cross-root centroid cos | cos old F1 | cos old F0 | recurrent | strong |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| 0 | 24 | 12 | 0 | 0.8038/0.8108 | n/a | 0.6414 | 0.6585 |  |  |
| 1 | 24 | 0 | 12 | 0.7967/0.8070 | n/a | 0.6411 | 0.6636 |  |  |

## 4. Semantic inspection of frozen 10k families

| family | exact@50/100 | broad@50/100 | anti@50/100 | head (top 8) |
|---|---:|---:|---:|---|
| 0 | 0/1 | 0/1 | 27/50 | Harry Potter Boxset (Harry Potter, #1-7), The Hate U Give, Words of Radiance (The Stormlight Archive, #2), A Court of Mist and Fury (A Court of Thorns and Roses, #2), Harry Potter and the Deathly Hallows (Harry Potter, #7), Harry Potter and the Half-Blood Prince (Harry Potter, #6), Harry Potter and the Goblet of Fire (Harry Potter, #4), Harry Potter and the Prisoner of Azkaban (Harry Potter, #3) |
| 1 | 0/2 | 0/2 | 28/46 | Harry Potter and the Deathly Hallows (Harry Potter, #7), Harry Potter Boxset (Harry Potter, #1-7), Words of Radiance (The Stormlight Archive, #2), Harry Potter and the Goblet of Fire (Harry Potter, #4), Harry Potter and the Prisoner of Azkaban (Harry Potter, #3), Harry Potter and the Half-Blood Prince (Harry Potter, #6), A Storm of Swords (A Song of Ice and Fire, #3), A Court of Mist and Fury (A Court of Thorns and Roses, #2) |

## Stopped at Part A/B

20k F1 descendants did not resolve into a cross-root recurrent 10k family under the fixed natural geometric partition.

The natural geometric partition produced families that are entirely root-specific: no family recurs across BOTH independent 20k parent lineages under the fixed cross-root recurrence rule (both roots represented; >= 2 distinct partition replicates per root; size >= 6).  The fixed tau=0.70 cosine cut produces EXACTLY the same two-cluster root-segregated split, so the structure is not an artifact of the silhouette choice.  Per the fixed procedure, no follow experiment was run and NO 5k descendant census was computed.  The experiment is NOT rescued with an alternate threshold.

# Breeding literary canons

Each parent is a converged direction of a gain-hard pruning path, together with its converged reader weights and survivor set. Children are bred by mixing half the jurors of one parent with half of the other (jury_mix) or by seeding from the top-25 books of the summed parent directions (direction_mix), then pushed through the same pruning machinery. A child breeds true if its deepest direction is within 0.85 correlation of a parent (and not within 0.05 of both); it leans at 0.60; otherwise it is a new canon.

Runtime: **77s**. Semantic context loaded only after every direction was frozen.

## Parent pool

| canon | canon stage | exact @50 | broad @50 | anti @50 | survivors |
|---|---:|---:|---:|---:|---:|
| teacher_p65_s25 | 5 | 4 | 8 | 17 | 14,662 |
| contrastive_careful | 4 | 9 | 16 | 6 | 24,923 |
| pairwise_bilateral | 5 | 9 | 14 | 10 | 15,284 |

Parent direction correlations:

| | teacher_p65_s25 | contrastive_careful | pairwise_bilateral |
|---|---|---|---|
| teacher_p65_s25 | 1.00 | 0.36 | 0.38 |
| contrastive_careful | 0.36 | 1.00 | 0.82 |
| pairwise_bilateral | 0.38 | 0.82 | 1.00 |

## Does breeding converge?

### jury_mix (4 children)

- Converged (final step corr >= 0.999): **4/4**.
- Breeds true to one parent: **0**.
- Ties (within 0.05 of both): **0**.
- Leans to a parent: **2**.
- New canon (below 0.60 to both): **2**.

| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |
|---|---:|---:|---|---:|---:|---:|
| contrastive_careful x love_center | 0.732 | 0.002 | lean:contrastive_careful | 0 | 0 | 6 |
| teacher_p65_s25 x contrastive_careful | 0.436 | 0.680 | lean:contrastive_careful | 5 | 9 | 15 |
| teacher_p65_s25 x love_center | 0.368 | 0.003 | new | 0 | 0 | 6 |
| teacher_p65_s25 x pairwise_bilateral | 0.460 | 0.545 | new | 4 | 8 | 24 |

### direction_mix (2 children)

- Converged (final step corr >= 0.999): **2/2**.
- Breeds true to one parent: **0**.
- Ties (within 0.05 of both): **0**.
- Leans to a parent: **2**.
- New canon (below 0.60 to both): **0**.

| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |
|---|---:|---:|---|---:|---:|---:|
| teacher_p65_s25 x contrastive_careful | 0.446 | 0.753 | lean:contrastive_careful | 4 | 6 | 3 |
| teacher_p65_s25 x pairwise_bilateral | 0.472 | 0.749 | lean:pairwise_bilateral | 6 | 10 | 5 |

## Attraction matrix (jury_mix; entry = breed-true/new over children of the pair)

| A \ B | teacher_p65_s25 | contrastive_careful | pairwise_bilateral |
|---|---|---|---|---|---|
| teacher_p65_s25 | - | 0:0:0:0 | 0:0:0:1 |
| contrastive_careful | 0:0:0:0 | - | - |
| pairwise_bilateral | 0:0:0:1 | - | - |

## Controls (self-breeding, random-mix, generations)

| child | mode | class | cos to A @deepest | exact @50 | anti @50 |
|---|---:|---:|---:|---:|---:|
| teacher_p65_s25xteacher_p65_s25::jm | self | self:drifted | 0.34943991899490356 | 5 | 15 |
| teacher_p65_s25xrandom::jm | control | control | 0.17280349135398865 | 0 | 25 |
| contrastive_carefulxcontrastive_careful::jm | self | self:stable | 0.8500638008117676 | 9 | 14 |
| contrastive_carefulxrandom::jm | control | control | 0.5927085876464844 | 0 | 25 |
| pairwise_bilateralxpairwise_bilateral::jm | self | self:drifted | 0.6978515386581421 | 9 | 9 |
| pairwise_bilateralxrandom::jm | control | control | 0.5858609676361084 | 0 | 26 |

## Valley audits (unpaired 24-start census on the canon stage)

| object | literary pole | mixed | mirror pole |
|---|---:|---:|---:|
| teacher_p65_s25 | 20 | 2 | 2 |
| contrastive_careful | 21 | 1 | 2 |
| pairwise_bilateral | 24 | 0 | 0 |
| teacher_p65_s25xpairwise_bilateral::jm | 5 | 9 | 10 |
| teacher_p65_s25xlove_center::jm | 13 | 2 | 9 |

## New-canon heads (deepest stage)

### teacher_p65_s25xpairwise_bilateral::jm

exact/broad/anti @50 4/8/24.

1. *East of Eden* — John Steinbeck (0.909)
2. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.890)
3. *The Things They Carried* — Tim O'Brien (0.886)
4. *The Importance of Being Earnest* — Oscar Wilde (0.877)
5. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.854)
6. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.834)
7. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.827)
8. *Hamlet* — William Shakespeare (0.821)
9. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.820)
10. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.815)

### teacher_p65_s25xlove_center::jm

exact/broad/anti @50 0/0/6.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.950)
2. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.937)
3. *March: Book Two (March, #2)* — John             Lewis (0.924)
4. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.919)
5. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.913)
6. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.912)
7. *March: Book Three (March, #3)* — John             Lewis (0.909)
8. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.903)
9. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.899)
10. *Calvin and Hobbes* — Bill Watterson (0.897)

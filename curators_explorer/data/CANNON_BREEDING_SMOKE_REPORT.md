# Breeding literary canons

Each parent is a converged direction of a gain-hard pruning path, together with its converged reader weights and survivor set. Children are bred by mixing half the jurors of one parent with half of the other (jury_mix) or by seeding from the top-25 books of the summed parent directions (direction_mix), then pushed through the same pruning machinery. A child breeds true if its deepest direction is within 0.85 correlation of a parent (and not within 0.05 of both); it leans at 0.60; otherwise it is a new canon.

Runtime: **220s**. Semantic context loaded only after every direction was frozen.

## Parent pool

| canon | parent path | canon stage | exact @50 | broad @50 | anti @50 | survivors |
|---|---|---:|---:|---:|---:|---:|
| teacher_p65_s25::s5 | teacher_p65_s25 | 5 | 4 | 8 | 17 | 14,662 |
| teacher_p65_s25::s3 | teacher_p65_s25 | 3 | 3 | 4 | 21 | 43,753 |
| contrastive_careful::s4 | contrastive_careful | 4 | 9 | 16 | 6 | 24,923 |
| contrastive_careful::s5 | contrastive_careful | 5 | 8 | 14 | 18 | 12,073 |
| pairwise_bilateral::s5 | pairwise_bilateral | 5 | 9 | 14 | 10 | 15,284 |
| pairwise_bilateral::s4 | pairwise_bilateral | 4 | 8 | 13 | 4 | 29,760 |

Parent direction correlations:

| | teacher_p65_s25::s5 | teacher_p65_s25::s3 | contrastive_careful::s4 | contrastive_careful::s5 | pairwise_bilateral::s5 | pairwise_bilateral::s4 |
|---|---|---|---|---|---|---|
| teacher_p65_s25::s5 | 1.00 | 0.38 | 0.36 | 0.33 | 0.38 | 0.45 |
| teacher_p65_s25::s3 | 0.38 | 1.00 | 0.02 | -0.07 | 0.05 | 0.12 |
| contrastive_careful::s4 | 0.36 | 0.02 | 1.00 | 0.70 | 0.82 | 0.79 |
| contrastive_careful::s5 | 0.33 | -0.07 | 0.70 | 1.00 | 0.61 | 0.53 |
| pairwise_bilateral::s5 | 0.38 | 0.05 | 0.82 | 0.61 | 1.00 | 0.88 |
| pairwise_bilateral::s4 | 0.45 | 0.12 | 0.79 | 0.53 | 0.88 | 1.00 |

## Does breeding converge?

### jury_mix (6 children)

- Converged (final step corr >= 0.999): **6/6**.
- Breeds true to one parent: **0**.
- Ties (within 0.05 of both; breeds true to the family): **0**.
- Leans to a parent: **2**.
- New canon (below 0.60 to both): **4**.
- Stopped at stage 0 (already an attractor; no pruning happened): **1**.

| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |
|---|---:|---:|---|---:|---:|---:|
| teacher_p65_s25::s3 x love_center | 0.446 | 0.048 | new | 0 | 0 | 14 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.436 | 0.680 | lean:contrastive_careful::s4 | 5 | 9 | 15 |
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.401 | 0.635 | lean:contrastive_careful::s4 | 6 | 10 | 20 |
| teacher_p65_s25::s5 x love_center | 0.368 | 0.003 | new | 0 | 0 | 6 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.125 | 0.397 | new | 0 | 2 | 4 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.006 | 0.345 | new | 0 | 1 | 15 |

### direction_mix (2 children)

- Converged (final step corr >= 0.999): **2/2**.
- Breeds true to one parent: **0**.
- Ties (within 0.05 of both; breeds true to the family): **0**.
- Leans to a parent: **1**.
- New canon (below 0.60 to both): **1**.
- Stopped at stage 0 (already an attractor; no pruning happened): **0**.

| pair | cos A | cos B | class | exact @50 | broad @50 | anti @50 |
|---|---:|---:|---|---:|---:|---:|
| teacher_p65_s25::s5 x contrastive_careful::s4 | 0.446 | 0.753 | lean:contrastive_careful::s4 | 4 | 6 | 3 |
| teacher_p65_s25::s5 x teacher_p65_s25::s3 | 0.377 | 0.157 | new | 17 | 23 | 12 |

## Attraction matrix (jury_mix; entry = true:A : true:B : ties : new over children of the pair)

| A \ B | teacher_p65_s25::s5 | teacher_p65_s25::s3 | contrastive_careful::s4 | contrastive_careful::s5 | pairwise_bilateral::s5 | pairwise_bilateral::s4 |
|---|---|---|---|---|---|---|
| teacher_p65_s25::s5 | - | 0:0:0:2 | 0:0:0:0 | - | - | - |
| teacher_p65_s25::s3 | 0:0:0:2 | - | - | - | - | - |
| contrastive_careful::s4 | 0:0:0:0 | - | - | - | - | - |
| contrastive_careful::s5 | - | - | - | - | - | - |
| pairwise_bilateral::s5 | - | - | - | - | - | - |
| pairwise_bilateral::s4 | - | - | - | - | - | - |

## Controls (self-breeding, random-mix, generations)

| child | mode | class | cos to A @deepest | exact @50 | anti @50 |
|---|---:|---:|---:|---:|---:|
| teacher_p65_s25::s5xteacher_p65_s25::s5::jm | self | self:drifted | 0.34943991899490356 | 5 | 15 |
| teacher_p65_s25::s5xrandom::jm | control | control | 0.17280349135398865 | 0 | 25 |
| teacher_p65_s25::s3xteacher_p65_s25::s3::jm | self | self:drifted | 0.4125729203224182 | 0 | 17 |
| teacher_p65_s25::s3xrandom::jm | control | control | 0.06039881333708763 | 0 | 25 |
| contrastive_careful::s4xcontrastive_careful::s4::jm | self | self:stable | 0.8500638008117676 | 9 | 14 |
| contrastive_careful::s4xrandom::jm | control | control | 0.5927085876464844 | 0 | 25 |
| contrastive_careful::s5xcontrastive_careful::s5::jm | self | self:drifted | 0.14006005227565765 | 6 | 18 |
| contrastive_careful::s5xrandom::jm | control | control | 0.46828728914260864 | 0 | 26 |
| pairwise_bilateral::s5xpairwise_bilateral::s5::jm | self | self:drifted | 0.6978515386581421 | 9 | 9 |
| pairwise_bilateral::s5xrandom::jm | control | control | 0.5858609676361084 | 0 | 26 |
| pairwise_bilateral::s4xpairwise_bilateral::s4::jm | self | self:stable | 0.9572464227676392 | 7 | 12 |
| pairwise_bilateral::s4xrandom::jm | control | control | 0.5371364951133728 | 0 | 25 |
| gen0::pairwise_bilateral::s5xpairwise_bilateral::s4 | generation | new | 0.37152814865112305 | 7 | 31 |
| gen1::contrastive_careful::s4xcontrastive_careful::s5 | generation | new | 0.5171910524368286 | 7 | 19 |
| gen2::gen0::pairwise_bilateral::s5xpairwise_bilateral::s4xgen1::contrastive_careful::s4xcontrastive_careful::s5 | generation | new | 0.20971256494522095 | 3 | 27 |
| gen3::teacher_p65_s25::s5xteacher_p65_s25::s3 | generation | new | 0.3771601915359497 | 17 | 12 |
| gen4::gen2::gen0::pairwise_bilateral::s5xpairwise_bilateral::s4xgen1::contrastive_careful::s4xcontrastive_careful::s5xgen3::teacher_p65_s25::s5xteacher_p65_s25::s3 | generation | new | 0.4716247320175171 | 3 | 18 |

## Increment size: does a larger increment converge more strongly?

| variant | children | mean final step corr | breed-true rate | new-canons | mean exact @50 |
|---|---:|---:|---:|---:|---:|
| hard_mult_0.75 | 2 | 0.99967 | 0.00 | 2 | 2.0 |
| hard_mult_1.0 | 2 | 0.99991 | 0.00 | 1 | 3.0 |
| hard_mult_1.5 | 2 | 0.99998 | 0.00 | 1 | 1.0 |
| hard_mult_2.0 | 2 | 0.99920 | 0.00 | 1 | 0.0 |
| ladder_0.10 | 2 | 0.99933 | 0.00 | 1 | 0.0 |
| ladder_0.20 | 2 | 0.99996 | 0.00 | 1 | 0.0 |
| beta_3.5 | 2 | 0.99931 | 0.00 | 2 | 1.5 |
| beta_5.0 | 2 | 0.99984 | 0.00 | 2 | 4.0 |

## Polyamorous breeding (three parents)

- poly::teacher_p65_s25::s5+contrastive_careful::s4+pairwise_bilateral::s5::r0: class lean:contrastive_careful::s4, cos A/B 0.390/0.710, exact @50 9.
- poly::teacher_p65_s25::s5+contrastive_careful::s4+pairwise_bilateral::s5::r1: class lean:contrastive_careful::s4, cos A/B 0.390/0.710, exact @50 9.
- poly::teacher_p65_s25::s5+contrastive_careful::s4+pairwise_bilateral::s5::r2: class lean:contrastive_careful::s4, cos A/B 0.390/0.710, exact @50 9.

## Valley audits (unpaired 24-start census on the canon stage)

| object | literary pole | mixed | mirror pole |
|---|---:|---:|---:|
| teacher_p65_s25::s5 | 20 | 2 | 2 |
| teacher_p65_s25::s3 | 22 | 0 | 2 |
| contrastive_careful::s4 | 21 | 1 | 2 |
| contrastive_careful::s5 | 4 | 18 | 2 |
| pairwise_bilateral::s5 | 24 | 0 | 0 |
| pairwise_bilateral::s4 | 15 | 0 | 9 |
| teacher_p65_s25::s5xteacher_p65_s25::s3::jm | 2 | 11 | 11 |
| teacher_p65_s25::s5xteacher_p65_s25::s3::dm | 19 | 4 | 1 |
| teacher_p65_s25::s5xlove_center::jm | 13 | 2 | 9 |
| teacher_p65_s25::s3xlove_center::jm | 8 | 3 | 13 |
| teacher_p65_s25::s5xteacher_p65_s25::s3::jm::r1 | 8 | 3 | 13 |
| teacher_p65_s25::s5xteacher_p65_s25::s3::jm::hard_mult_0.75 | 3 | 10 | 11 |

## New-canon heads (deepest stage)

### teacher_p65_s25::s5xteacher_p65_s25::s3::jm

exact/broad/anti @50 0/2/4.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.910)
2. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.885)
3. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.866)
4. *Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2)* — Art Spiegelman (0.856)
5. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.856)
6. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.855)
7. *If This Is a Man / The Truce* — Primo Levi (0.851)
8. *March: Book Two (March, #2)* — John             Lewis (0.837)
9. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.832)
10. *Between the World and Me* — Ta-Nehisi Coates (0.829)

### teacher_p65_s25::s5xteacher_p65_s25::s3::dm

exact/broad/anti @50 17/23/12.

1. *Crime and Punishment* — Fyodor Dostoyevsky (0.971)
2. *One Hundred Years of Solitude* — Gabriel Garcia Marquez (0.969)
3. *Anna Karenina* — Leo Tolstoy (0.957)
4. *Lolita* — Vladimir Nabokov (0.948)
5. *War and Peace* — Leo Tolstoy (0.947)
6. *The Master and Margarita* — Mikhail Bulgakov (0.945)
7. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.935)
8. *The Stranger* — Albert Camus (0.933)
9. *Stoner* — John  Williams (0.926)
10. *The Metamorphosis* — Franz Kafka (0.911)

### teacher_p65_s25::s5xlove_center::jm

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

### teacher_p65_s25::s3xlove_center::jm

exact/broad/anti @50 0/0/14.

1. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.909)
2. *The Nightingale* — Kristin Hannah (0.880)
3. *The Mark (Left Behind, #8)* — Tim LaHaye (0.848)
4. *An Echo in the Darkness (Mark of the Lion, #2)* — Francine Rivers (0.838)
5. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.827)
6. *A Voice in the Wind (Mark of the Lion, #1)* — Francine Rivers (0.823)
7. *The Hate U Give* — Angie Thomas (0.817)
8. *Beard Science (Winston Brothers, #3)* — Penny Reid (0.816)
9. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.814)
10. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.811)

### teacher_p65_s25::s5xteacher_p65_s25::s3::jm::r1

exact/broad/anti @50 0/1/15.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.893)
2. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.887)
3. *لا تصالح* — 'ml dnql (0.858)
4. *رياض الصالحين* — yHy~ bn shrf lnwwy (0.851)
5. *The Qur'an / القرآن الكريم* — Anonymous (0.851)
6. *الإسلام بين الشرق والغرب* — Alija Izetbegovic (0.840)
7. *الرحيق المختوم* — Safiy al-Rahman al-Mubarakfuri (0.826)
8. *The Nightingale* — Kristin Hannah (0.826)
9. *الجريمة والعقاب # 2* — Fyodor Dostoyevsky (0.821)
10. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.818)

### teacher_p65_s25::s5xteacher_p65_s25::s3::jm::hard_mult_0.75

exact/broad/anti @50 0/1/3.

1. *The Complete Calvin and Hobbes* — Bill Watterson (0.878)
2. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.871)
3. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.866)
4. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.862)
5. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.861)
6. *The New Jim Crow: Mass Incarceration in the Age of Colorblindness* — Michelle Alexander (0.851)
7. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.848)
8. *Calvin and Hobbes* — Bill Watterson (0.846)
9. *Maus II: A Survivor's Tale: And Here My Troubles Began (Maus, #2)* — Art Spiegelman (0.844)
10. *Between the World and Me* — Ta-Nehisi Coates (0.842)

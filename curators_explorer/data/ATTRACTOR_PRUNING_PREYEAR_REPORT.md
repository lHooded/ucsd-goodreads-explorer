# Convergence reversal on pre-year literary candidates

Before publication year entered the dataset, the nonlinear attractor map had only ever been started from random cohorts. The literary-leaning constructions of that era — the teacher jury, the rebuilt juries, the contrastive ranking, and the bilateral pairwise esteem head — were never run through the map. This experiment starts each of them, watches the collapse to the Goodreads center, then applies the gain-hard pruning (remove the strongest proponents of the converged direction at once, rebuild, restart from the same candidate seed).

Candidates: **5**; runtime: **52.1s**.

## Collapse baseline (stage 0)

| candidate | kind | users | retained vs start | step corr | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---|---|---:|---:|---:|---|---|---|
| teacher_p65_s25 | users | 233,271 | 0.274 | 0.99994 | 0/1 | 0/7 | 5/24 |
| rebuilt_hard_4929 | users | 233,271 | 0.320 | 0.99994 | 0/1 | 0/7 | 5/24 |
| rebuilt_soft | users | 233,271 | 0.322 | 0.99994 | 0/1 | 0/7 | 5/24 |
| contrastive_careful | books | 233,271 | 0.439 | 0.99981 | 0/1 | 0/5 | 3/24 |
| pairwise_bilateral | books | 233,271 | 0.352 | 0.99982 | 0/1 | 0/7 | 3/22 |

## Reversal outcome

- **teacher_p65_s25** (users): stop **evidence_floor** at stage 5 (14,662 users, 93.7% removed); retained 0.535 (from 0.274); exact/broad/anti @50 = 4/8/17.
- **rebuilt_hard_4929** (users): stop **evidence_floor** at stage 5 (14,515 users, 93.8% removed); retained 0.636 (from 0.320); exact/broad/anti @50 = 1/2/26.
- **rebuilt_soft** (users): stop **evidence_floor** at stage 5 (14,754 users, 93.7% removed); retained 0.661 (from 0.322); exact/broad/anti @50 = 1/6/28. **Valley audit:** unpaired starts 21/0/3 (literary/mixed/mirror); pooled pole exact/broad/anti @50 = 1/2/37; random control reaches 0.198 retained.
- **contrastive_careful** (books): stop **evidence_floor** at stage 5 (12,073 users, 94.8% removed); retained 0.373 (from 0.439); exact/broad/anti @50 = 8/14/18. **Valley audit:** unpaired starts 11/0/13 (literary/mixed/mirror); pooled pole exact/broad/anti @50 = 0/2/24; random control reaches 0.291 retained. Census at most-literary stage 4: 21/1.
- **pairwise_bilateral** (books): stop **evidence_floor** at stage 5 (15,284 users, 93.4% removed); retained 0.430 (from 0.352); exact/broad/anti @50 = 9/14/10. **Valley audit:** unpaired starts 11/0/13 (literary/mixed/mirror); pooled pole exact/broad/anti @50 = 4/7/30; random control reaches 0.249 retained. Census at most-literary stage 5: 22/0.

## Stage detail

### teacher_p65_s25 · users (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 99629 | 0.000 | 0.99994 | 0.2739 | 0.2739 | 0.685 | 0/1 | 0/7 | 5/24 |
| 1 | 133642 | 56029 | 0.427 | 0.99986 | 0.1484 | 0.1677 | 0.686 | 0/0 | 0/1 | 17/49 |
| 2 | 77613 | 33860 | 0.667 | 0.99944 | 0.2092 | 0.2354 | 0.688 | 0/2 | 0/3 | 32/91 |
| 3 | 43753 | 18759 | 0.812 | 0.99976 | 0.3269 | 0.3449 | 0.680 | 3/6 | 4/10 | 21/60 |
| 4 | 24994 | 10332 | 0.893 | 0.99942 | 0.4547 | 0.5452 | 0.672 | 1/7 | 1/11 | 32/105 |
| 5 | 14662 | 0 | 0.937 | 0.99914 | 0.5353 | 0.6835 | 0.649 | 4/13 | 8/23 | 17/57 |

### rebuilt_hard_4929 · users (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 100199 | 0.000 | 0.99994 | 0.3199 | 0.3199 | 0.687 | 0/1 | 0/7 | 5/24 |
| 1 | 133072 | 55678 | 0.430 | 0.99985 | 0.1713 | 0.1948 | 0.686 | 0/0 | 0/1 | 19/50 |
| 2 | 77394 | 33796 | 0.668 | 0.99938 | 0.2184 | 0.2510 | 0.687 | 0/1 | 0/2 | 32/87 |
| 3 | 43598 | 18924 | 0.813 | 0.99937 | 0.3633 | 0.3732 | 0.683 | 1/2 | 1/6 | 23/58 |
| 4 | 24674 | 10159 | 0.894 | 0.99945 | 0.5081 | 0.6072 | 0.670 | 1/2 | 1/6 | 32/116 |
| 5 | 14515 | 0 | 0.938 | 0.99953 | 0.6361 | 0.8166 | 0.648 | 1/12 | 2/25 | 26/90 |

### rebuilt_soft · users (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 100190 | 0.000 | 0.99994 | 0.3224 | 0.3224 | 0.687 | 0/1 | 0/7 | 5/24 |
| 1 | 133081 | 55717 | 0.430 | 0.99988 | 0.1881 | 0.2131 | 0.686 | 0/0 | 0/1 | 19/51 |
| 2 | 77364 | 33700 | 0.668 | 0.99937 | 0.2295 | 0.2643 | 0.687 | 0/1 | 0/2 | 31/82 |
| 3 | 43664 | 18854 | 0.813 | 0.99828 | 0.3915 | 0.4096 | 0.684 | 1/2 | 2/6 | 22/57 |
| 4 | 24810 | 10056 | 0.894 | 0.99956 | 0.5138 | 0.6203 | 0.664 | 1/2 | 1/6 | 33/117 |
| 5 | 14754 | 0 | 0.937 | 0.99978 | 0.6608 | 0.8446 | 0.645 | 1/13 | 6/27 | 28/87 |

### contrastive_careful · books (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 101856 | 0.000 | 0.99981 | 0.4393 | 0.4393 | 0.694 | 0/1 | 0/5 | 3/24 |
| 1 | 131415 | 54699 | 0.437 | 0.99983 | 0.5310 | 0.6830 | 0.688 | 0/2 | 0/6 | 13/39 |
| 2 | 76716 | 29286 | 0.671 | 1.00000 | 0.6920 | 0.9692 | 0.630 | 2/5 | 4/16 | 9/39 |
| 3 | 47430 | 22507 | 0.797 | 1.00000 | 0.6593 | 0.9907 | 0.626 | 7/15 | 13/29 | 4/21 |
| 4 | 24923 | 12850 | 0.893 | 1.00000 | 0.4965 | 0.9795 | 0.703 | 9/16 | 16/30 | 6/29 |
| 5 | 12073 | 0 | 0.948 | 0.99950 | 0.3733 | 0.8636 | 0.670 | 8/15 | 14/23 | 18/67 |

### pairwise_bilateral · books (stop: evidence_floor)

| stage | users | removed | cum removed | step corr | retained ref | retained stage | eff share | exact lit @50/200 | broad @50/200 | anti @50/200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0 | 233271 | 100615 | 0.000 | 0.99982 | 0.3518 | 0.3518 | 0.689 | 0/1 | 0/7 | 3/22 |
| 1 | 132656 | 56259 | 0.431 | 0.99974 | 0.3517 | 0.4483 | 0.692 | 1/2 | 1/3 | 13/35 |
| 2 | 76397 | 29353 | 0.672 | 0.99942 | 0.6005 | 0.8432 | 0.656 | 3/8 | 5/16 | 27/74 |
| 3 | 47044 | 17284 | 0.798 | 1.00000 | 0.6430 | 0.9750 | 0.623 | 4/10 | 7/21 | 18/68 |
| 4 | 29760 | 14476 | 0.872 | 1.00000 | 0.5841 | 0.9905 | 0.623 | 8/14 | 13/32 | 4/18 |
| 5 | 15284 | 0 | 0.934 | 1.00000 | 0.4305 | 0.9760 | 0.700 | 9/14 | 14/27 | 10/32 |

## Converged heads at the stop stage

### teacher_p65_s25 · stage 5 · stop evidence_floor

Exact literary @50/200: **4/13**; broad: **8/23**; anti: **17/57**.

1. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.844)
2. *Labyrinths:  Selected Stories and Other Writings* — Jorge Luis Borges (0.833)
3. *Fullmetal Alchemist, Vol. 3 (Fullmetal Alchemist, #3)* — Hiromu Arakawa (0.808)
4. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.805)
5. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.803)
6. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.792)
7. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.789)
8. *Ficciones* — Jorge Luis Borges (0.787)
9. *Dreamfever (Fever, #4)* — Karen Marie Moning (0.783)
10. *Collected Fictions* — Jorge Luis Borges (0.770)
11. *Fullmetal Alchemist, Vol. 10 (Fullmetal Alchemist, #10)* — Hiromu Arakawa (0.764)
12. *Fullmetal Alchemist, Vol. 2 (Fullmetal Alchemist, #2)* — Hiromu Arakawa (0.751)
13. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.743)
14. *Fullmetal Alchemist, Vol. 9 (Fullmetal Alchemist, #9)* — Hiromu Arakawa (0.741)
15. *Fullmetal Alchemist, Vol. 22 (Fullmetal Alchemist, #22)* — Hiromu Arakawa (0.740)

### rebuilt_hard_4929 · stage 5 · stop evidence_floor

Exact literary @50/200: **1/12**; broad: **2/25**; anti: **26/90**.

1. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.860)
2. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.831)
3. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.803)
4. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.796)
5. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.783)
6. *Dreamfever (Fever, #4)* — Karen Marie Moning (0.766)
7. *Heir of Fire (Throne of Glass, #3)* — Sarah J. Maas (0.760)
8. *Fullmetal Alchemist, Vol. 10 (Fullmetal Alchemist, #10)* — Hiromu Arakawa (0.750)
9. *Collected Fictions* — Jorge Luis Borges (0.741)
10. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.740)
11. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.729)
12. *Fifth Grave Past the Light (Charley Davidson, #5)* — Darynda Jones (0.727)
13. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.726)
14. *Fullmetal Alchemist, Vol. 11 (Fullmetal Alchemist, #11)* — Hiromu Arakawa (0.725)
15. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.722)

### rebuilt_soft · stage 5 · stop evidence_floor

Exact literary @50/200: **1/13**; broad: **6/27**; anti: **28/87**.

1. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.856)
2. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.836)
3. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.797)
4. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.788)
5. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.772)
6. *Dreamfever (Fever, #4)* — Karen Marie Moning (0.770)
7. *Collected Fictions* — Jorge Luis Borges (0.758)
8. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.755)
9. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.751)
10. *Magic Slays (Kate Daniels, #5)* — Ilona Andrews (0.750)
11. *Armed & Dangerous (Cut & Run, #5)* — Abigail Roux (0.744)
12. *Ficciones* — Jorge Luis Borges (0.735)
13. *Fifth Grave Past the Light (Charley Davidson, #5)* — Darynda Jones (0.729)
14. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.728)
15. *The Last Olympian (Percy Jackson and the Olympians, #5)* — Rick Riordan (0.721)
Unpaired random-start census on the final population: **21** literary / **3** mirror / 0 mixed (of 24).
Pooled literary-pole consensus head:

1. *Shadowfever (Fever, #5)* — Karen Marie Moning (0.882)
2. *Magic Bleeds (Kate Daniels, #4)* — Ilona Andrews (0.870)
3. *Magic Strikes (Kate Daniels, #3)* — Ilona Andrews (0.842)
4. *Fifth Grave Past the Light (Charley Davidson, #5)* — Darynda Jones (0.819)
5. *Magic Slays (Kate Daniels, #5)* — Ilona Andrews (0.815)
6. *Dreamfever (Fever, #4)* — Karen Marie Moning (0.802)
7. *The Brothers Karamazov* — Fyodor Dostoyevsky (0.791)
8. *Lover Awakened (Black Dagger Brotherhood, #3)* — J.R. Ward (0.787)
9. *Magic Rises (Kate Daniels, #6)* — Ilona Andrews (0.783)
10. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.778)

### contrastive_careful · stage 5 · stop evidence_floor

Exact literary @50/200: **8/15**; broad: **14/23**; anti: **18/67**.

1. *Crime and Punishment* — Fyodor Dostoyevsky (0.963)
2. *The Poisonwood Bible* — Barbara Kingsolver (0.953)
3. *Middlesex* — Jeffrey Eugenides (0.951)
4. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (0.947)
5. *Hamlet* — William Shakespeare (0.938)
6. *The Grapes of Wrath* — John Steinbeck (0.934)
7. *Lolita* — Vladimir Nabokov (0.932)
8. *Macbeth* — William Shakespeare (0.906)
9. *The Odyssey* — Homer (0.890)
10. *Their Eyes Were Watching God* — Zora Neale Hurston (0.888)
11. *Waiting for Godot* — Samuel Beckett (0.888)
12. *The Trial* — Franz Kafka (0.885)
13. *Life After Life* — Kate Atkinson (0.865)
14. *A Streetcar Named Desire* — Tennessee Williams (0.856)
15. *Mrs. Dalloway* — Virginia Woolf (0.850)

Unpaired random-start census at the most-literary stage (stage 4, best exact+broad @50): **21** literary / **1** mirror / 2 mixed (of 24).
Pooled literary-pole consensus head at that stage:

1. *Middlesex* — Jeffrey Eugenides (0.975)
2. *The Poisonwood Bible* — Barbara Kingsolver (0.973)
3. *Crime and Punishment* — Fyodor Dostoyevsky (0.973)
4. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (0.965)
5. *Hamlet* — William Shakespeare (0.962)
6. *Lolita* — Vladimir Nabokov (0.960)
7. *Life After Life* — Kate Atkinson (0.956)
8. *The Grapes of Wrath* — John Steinbeck (0.950)
9. *Macbeth* — William Shakespeare (0.944)
10. *Their Eyes Were Watching God* — Zora Neale Hurston (0.942)

Unpaired random-start census on the final population: **11** literary / **13** mirror / 0 mixed (of 24).
Pooled literary-pole consensus head:

1. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.872)
2. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.868)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.851)
4. *The Complete Calvin and Hobbes* — Bill Watterson (0.843)
5. *The Absolutely True Diary of a Part-Time Indian* — Sherman Alexie (0.843)
6. *The Hate U Give* — Angie Thomas (0.837)
7. *Calvin and Hobbes* — Bill Watterson (0.834)
8. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.818)
9. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.815)
10. *Crime and Punishment* — Fyodor Dostoyevsky (0.813)

### pairwise_bilateral · stage 5 · stop evidence_floor

Exact literary @50/200: **9/14**; broad: **14/27**; anti: **10/32**.

1. *East of Eden* — John Steinbeck (0.987)
2. *Hamlet* — William Shakespeare (0.982)
3. *Lolita* — Vladimir Nabokov (0.978)
4. *The Importance of Being Earnest* — Oscar Wilde (0.977)
5. *The Metamorphosis* — Franz Kafka (0.971)
6. *The Things They Carried* — Tim O'Brien (0.968)
7. *Mrs. Dalloway* — Virginia Woolf (0.946)
8. *Inferno (The Divine Comedy #1)* — Dante Alighieri (0.936)
9. *Middlemarch* — George Eliot (0.936)
10. *Invisible Man* — Ralph Ellison (0.931)
11. *Paradise Lost* — John Milton (0.927)
12. *To the Lighthouse* — Virginia Woolf (0.922)
13. *Madame Bovary* — Gustave Flaubert (0.921)
14. *A Raisin in the Sun* — Lorraine Hansberry (0.857)
15. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.742)

Unpaired random-start census at the most-literary stage (stage 5, best exact+broad @50): **22** literary / **0** mirror / 2 mixed (of 24).
Pooled literary-pole consensus head at that stage:

1. *East of Eden* — John Steinbeck (0.987)
2. *Hamlet* — William Shakespeare (0.980)
3. *The Importance of Being Earnest* — Oscar Wilde (0.976)
4. *Lolita* — Vladimir Nabokov (0.975)
5. *The Metamorphosis* — Franz Kafka (0.969)
6. *The Things They Carried* — Tim O'Brien (0.967)
7. *Mrs. Dalloway* — Virginia Woolf (0.944)
8. *Middlemarch* — George Eliot (0.934)
9. *Inferno (The Divine Comedy #1)* — Dante Alighieri (0.929)
10. *Paradise Lost* — John Milton (0.926)

Unpaired random-start census on the final population: **11** literary / **13** mirror / 0 mixed (of 24).
Pooled literary-pole consensus head:

1. *East of Eden* — John Steinbeck (0.937)
2. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.884)
3. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.863)
4. *The Importance of Being Earnest* — Oscar Wilde (0.860)
5. *The Things They Carried* — Tim O'Brien (0.845)
6. *Hamlet* — William Shakespeare (0.843)
7. *The Hate U Give* — Angie Thomas (0.833)
8. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.821)
9. *Lady Midnight (The Dark Artifices, #1)* — Cassandra Clare (0.820)
10. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.813)

## Findings

- The stage-0 baseline answers the motivating question: **every pre-year literary candidate collapses under the unpruned map** exactly like the year juries did (retained vs start 0.27-0.44, exact literary 0/1, heads mixing classics with YA/paranormal series). The pre-year failures were never observed because the map was never started from them; this run shows they fail too.
- **Gain-hard reversal gives partial rescue, and the outcome splits by candidate kind.** The three user-jury candidates (teacher, rebuilt hard, rebuilt soft) rise to 0.53-0.66 retained but end in paranormal-romance-dominated heads (anti 17-28 @50, exact <=4). Their pruned geometry has a single strong pole and it is the romance basin: rebuilt_soft's census is 21/3 but its pooled pole head is Shadowfever/Kate Daniels. None of the user juries produces a literary valley.
- **The two book-space candidates do reach a dominant literary valley.** Their gain-hard paths produce genuinely literary heads (contrastive: Crime and Punishment #1, Poisonwood Bible, Middlesex, Hamlet; pairwise: East of Eden #1, Hamlet #2, Lolita #3; exact 8-9 @50, broad 13-16 @50, anti 4-10 @50 at stages 3-4), and at the most-literary stages the pruned geometry is **more literary than the year jury's**: unpaired census 21/1 (contrastive stage 4) and 22/0 (pairwise stage 5) vs the year jury's 18/6, with pooled consensus heads at exact/broad/anti @50 = 10/17/7 (contrastive) and 9/14/11 (pairwise) vs the year jury's 5/12/3 — purely canonical (Middlesex, Poisonwood Bible, Crime and Punishment, Hamlet, Lolita; East of Eden, Hamlet, The Importance of Being Earnest, Lolita). The 11/13 coin flip seen at the peak-retained stages (2-3) resolves as pruning deepens.
- **What publication year still does: it keeps the gain-hard path inside the valley.** For the book candidates the literary basin dominates only where retained has already fallen below the 0.70 threshold (0.50 @ contrastive stage 4, 0.43 @ pairwise stage 5), and contrastive's deepest stage (5) re-splits (11/13) with anti climbing to 18/67. The year jury is the only start whose pruned path sits in the deep literary valley at its deepest point (retained 0.70, census 18/6). Years do not create the literary basin — pre-year starts reach a deeper one — but they make it enclosing from the start.
- The effect remains specific to who is removed: the random-removal controls never approach the retained-direction levels of the gain-hard paths (0.20-0.29).

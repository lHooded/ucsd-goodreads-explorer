# Ratings-only literary consensus — probe results

Discovery uses **only** `(user_id, work_id, rating)` (and aggregates thereof).
Literary_poll / non_literary / normie lists are **evaluation only**.

## Papers → method choices

- **Lizardo (2018), method of reflections:** person↔item recursive centralities beyond plain HITS. `δ²` = 2nd-order popularity of a book's audience; `d¹` = popular-choice bias of a reader. We rank by `−δ²` and by the Bayesian tastes of low-`d¹` (niche-enthusiast) users.
- **Airoldi (2024), nested relational legitimacy:** hierarchies are nested (genre→artist→work) and comparative. Global eigenvectors collapse loud local canons; we build PMI communities and a round-robin portfolio of within-community heads.
- **Feldkamp et al. (2024):** expert/canonical proxies often anti-correlate with Goodreads means; Hugo-like prestige tracks popular more than canonical. `feldkamp_dual_axis` rewards niche audiences while penalizing high crowd means.
- **Walsh & Antoniak:** Goodreads “classics” are school/industry constructions — crowd tags ≠ academic canon. Eval against `literary_poll` is one Anglophone axis among many; Arabic/Tamil/Persian heads can be real canons with pos50=0.

## Takeaways

1. **Naive rarity-depth fails on Goodreads.** Obscure indie romance inflates “depth”; popular classics lower it → romance/vanity heads.

2. **Plain HITS → YA/fantasy popularity hubs.** Eigenvector prestige without reflections collapses to omnivore×popular (Lizardo’s warning).

3. **Best Anglophone-poll overlap remains** `anti_blockbuster_picky` (pos50=4) — serious + multilingual classics mix, not poll literary.

4. **Lizardo reflections recover loud non-Anglophone canons, not the English lit poll:**
   - `lizardo_high_order` (best Q among new methods, anti50=0): Arabic literary cluster (Towfik, Mourad, …) — same structure `cocitation_pmi` found, now grounded in reflections theory.
   - `lizardo_neg_delta2` (anti50=0): Indonesian Tere Liye constellation — another dense local consecration.
   - `lizardo_niche_enthusiasts`: Arabic religious/devotional + Tutunamayanlar + Rumi mixed with fantasy — “niche bias” ≠ literary.

5. **Airoldi nested portfolio works:** sparsified PMI → ~15 mid-size communities (Arabic Towfik, Wordsworth, Christie, YA, comics, business, …). Round-robin heads stay anti50=0. Global one-axis ranking is the wrong object.

6. **“Mass” community ≠ literary canon.** Highest median-`n` mid-size community + within-community `−δ²` → Discworld/Pratchett cluster. Platform-dominant co-choice blocks are genre canons, not syllabi.

7. **Feldkamp dual-axis** (penalize high Goodreads mean) surfaces Arabic midbrow + Chetan Bhagat — confirms crowd-mean is a bad expert proxy, but subtracting it alone doesn’t yield literary_poll.

8. **Walsh implication:** treating Goodreads as one classics axis is wrong; ratings recover *many* school/industry/community canons. Eval against `literary_poll` undersells real consensus elsewhere.

9. **Research conclusion (ratings-only):** the recoverable signal is **multi-community nested prestige**, not a single Western literary ranking. Product path: surface community heads (incl. loud non-English canons) + optional within-community curator ranking — seeds remain for Anglophone poll targeting if desired.

10. **Author-level follow-up** (`AUTHOR_LEVEL_CANON_REPORT.md`): adding `author_id` (from `author_url`) is the right nested move (Airoldi / Vlegels), and cross-author book PMI still finds Arabic literary — but person×author reflections/PMI promote **dense romance islands**, not `lit-2014-2024` (poll authors remain mid/low rank). Author is better as a de-islanding / multi-canon tool than as a global literary ranker on Goodreads.



## Method scores

| method | Q | geo_n | pos50 | anti50 | anti1000 | anti_med | filler50 | ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lizardo_high_order | 8.7 | 299 | 0 | 0 | 1 | 922 | 0 | 177254 |
| lizardo_neg_delta2 | 6.7 | 144 | 0 | 0 | 5 | 923 | 0 | 99757 |
| contrastive_lift | 5.0 | 55 | 0 | 0 | 1 | 551 | 0 | 4078 |
| nested_community_portfolio | 2.9 | 120 | 0 | 0 | 5 | 538 | 0 | 106617 |
| audience_depth | 0.0 | 111 | 0 | 0 | 0 | None | 0 | 1114 |
| nested_mass_community_reflections | 0.0 | 801 | 0 | 0 | 0 | None | 0 | 92060 |
| cocitation_pmi | -3.4 | 395 | 0 | 0 | 24 | 858 | 0 | 144258 |
| anti_blockbuster_picky | -26.4 | 133 | 4 | 5 | 43 | 313 | 0 | 4523 |
| lizardo_niche_enthusiasts | -30.9 | 226 | 0 | 3 | 51 | 663 | 0 | 106093 |
| depth_top5pct_p5 | -36.9 | 133 | 0 | 3 | 61 | 564 | 0 | 1255 |
| feldkamp_dual_axis | -44.4 | 111 | 0 | 0 | 102 | 657 | 0 | 76658 |
| picky_top10pct | -76.1 | 193 | 3 | 12 | 81 | 339 | 0 | 1500 |
| baseline_bayes_p5 | -97.0 | 332 | 0 | 12 | 106 | 399 | 0 | 162 |
| hits_rarity_weighted | -385.7 | 20976 | 1 | 36 | 478 | 429 | 5 | 144730 |

## Top 12 by method

### baseline_bayes_p5
- 1. The Way of Kings, Part 2 (The Stormlight Archive #1.2) — Brandon Sanderson (n≈893)
- 2. A Court of Mist and Fury (A Court of Thorns and Roses, #2) — Sarah J. Maas (n≈23734)
- 3. Words of Radiance (The Stormlight Archive, #2) — Brandon Sanderson (n≈10709)
- 4. பொன்னியின் செல்வன் [Ponniyin Selvan] — Kalki (n≈438)
- 5. Words of Radiance, Part 2 (The Stormlight Archive #2.2) — Brandon Sanderson (n≈241)
- 6. Still (Grip, #2) — Kennedy Ryan (n≈206)
- 7. Mark of the Lion Trilogy — Francine Rivers (n≈647)
- 8. Beyond the World of Man (Dwellers of Ahwahnee, #3) — Sheryl Seal (n≈88)
- 9. Beyond Oria Falls (Dwellers of Ahwahnee, #2) — Sheryl Seal (n≈89)
- 10. A Court of Thorns and Roses Coloring Book — Sarah J. Maas (n≈129)
- 11. Percy Jackson Collection: Percy Jackson and the Lightning Thief, the Last Olympian, the Titans Curse, the Sea of Monsters, the Battle of the Labyrinth, the Demigod Files and the Red Pyramid — Rick Riordan (n≈262)
- 12. Cornered Coyote (Coyote #3) — Dianne Harman (n≈105)

### picky_top10pct
- 1. Words of Radiance (The Stormlight Archive, #2) — Brandon Sanderson (n≈1128)
- 2. பொன்னியின் செல்வன் [Ponniyin Selvan] — Kalki (n≈49)
- 3. Special Forces - Soldiers (Special Forces, #1) — Aleksandr Voinov (n≈48)
- 4. A Court of Mist and Fury (A Court of Thorns and Roses, #2) — Sarah J. Maas (n≈1389)
- 5. The Hate U Give — Angie Thomas (n≈1107)
- 6. The Way of Kings, Part 2 (The Stormlight Archive #1.2) — Brandon Sanderson (n≈73)
- 7. Shahnameh: The Persian Book of Kings — Abolqasem Ferdowsi (n≈54)
- 8. The Way of Kings (The Stormlight Archive, #1) — Brandon Sanderson (n≈1628)
- 9. A Little Life — Hanya Yanagihara (n≈1337)
- 10. Worm — Wildbow (n≈58)
- 11. Assassin's Fate (The Fitz and the Fool, #3) — Robin Hobb (n≈180)
- 12. The Heart's Invisible Furies — John Boyne (n≈89)

### depth_top5pct_p5
- 1. Ends Here (Road to Nowhere, #2) — M.  Robinson (n≈133)
- 2. Crashed (Driven, #3) — K. Bromberg (n≈324)
- 3. Cornered Coyote (Coyote #3) — Dianne Harman (n≈71)
- 4. Preppy: The Life & Death of Samuel Clearwater, Part One (King, #5) — T.M. Frazier (n≈156)
- 5. Preppy: The Life & Death of Samuel Clearwater, Part Three (King, #7) — T.M. Frazier (n≈121)
- 6. Fueled (Driven, #2) — K. Bromberg (n≈348)
- 7. Among the Shrouded — Amalie Jahn (n≈68)
- 8. Road to Nowhere (Road to Nowhere, #1) — M.  Robinson (n≈149)
- 9. Beyond Bridalveil Fall  (Dwellers of Awahnee, #1) — Sheryl Seal (n≈66)
- 10. Ride Steady (Chaos, #3) — Kristen Ashley (n≈243)
- 11. Blue Coyote Motel (Coyote #1) — Dianne Harman (n≈87)
- 12. Spellbound in His Arms (The Greek Isles Series, #1) — Angel Sefer (n≈71)

### audience_depth
- 1. Moth to a Flame — Ashley Antoinette (n≈137)
- 2. Dog Days of Summer (Rolling Thunder #1) — P.J. Fiala (n≈97)
- 3. Tagged: The Apocalypse — Joseph M. Chiron (n≈79)
- 4. The Riding School (Pony Tales, #1) — C.P. Mandara (n≈110)
- 5. The Dopeman's Wife (The Dopeman, #1) — JaQuavis Coleman (n≈100)
- 6. Tale of the Murda Mamas (The Cartel, #2) — Ashley Antoinette (n≈152)
- 7. Out of the Box Awakening (Out of the Box, #1) — Jennifer Theriot (n≈105)
- 8. Bitch (Bitch, #1) — Deja King (n≈130)
- 9. Cornered Coyote (Coyote #3) — Dianne Harman (n≈87)
- 10. Out of the Box Regifted (Out of the Box, #2) — Jennifer Theriot (n≈90)
- 11. Daddy Morebucks (Daddy's Girl, #1) — Normandie Alleman (n≈100)
- 12. The Last Chapter (The Cartel, #3) — Ashley Antoinette (n≈166)

### contrastive_lift
- 1. A House Without Windows — Stevie Turner (n≈44)
- 2. The Clay Lion (The Clay Lion, #1) — Amalie Jahn (n≈74)
- 3. Among the Shrouded — Amalie Jahn (n≈41)
- 4. The Gordonston Ladies Dog Walking Club — Duncan Whitehead (n≈93)
- 5. The Branches of Time — Luca  Rossi (n≈84)
- 6. Baby (Species Intervention #6609, #1) — J.K. Accinni (n≈74)
- 7. Lone Wolf Rising (The Winters Family Saga, #1) — Jami Brumfield (n≈66)
- 8. Pompeii: City on Fire (Seven Wonders, #6) — T.L. Higley (n≈48)
- 9. Demigods and Monsters (Sphinx, #2) — Raye Wagner (n≈46)
- 10. The Reluctant Duchess (Ladies of the Manor, #2) — Roseanna M. White (n≈44)
- 11. Sexy Motherpucker (Bad Motherpuckers, #2) — Lili Valente (n≈62)
- 12. Tempted (Bad Boy Next Door, #2) — Lauren Landish (n≈41)

### anti_blockbuster_picky
- 1. لا تصالح — 'ml dnql (n≈136)
- 2. Words of Radiance (The Stormlight Archive, #2) — Brandon Sanderson (n≈1495)
- 3. Shahnameh: The Persian Book of Kings — Abolqasem Ferdowsi (n≈97)
- 4. The Way of Kings, Part 2 (The Stormlight Archive #1.2) — Brandon Sanderson (n≈104)
- 5. Mrityunjaya — Shivaji Sawant (n≈53)
- 6. பொன்னியின் செல்வன் [Ponniyin Selvan] — Kalki (n≈51)
- 7. زمن الخيول البيضاء — Ibrahim Nasrallah - ibrhym nSr llh (n≈199)
- 8. حصن المسلم: من أذكار الكتاب والسنة — s`yd bn `ly bn whf lqHTny (n≈50)
- 9. Assassin's Fate (The Fitz and the Fool, #3) — Robin Hobb (n≈244)
- 10. Checkmate (The Lymond Chronicles, #6) — Dorothy Dunnett (n≈85)
- 11. Tutunamayanlar — Oguz Atay (n≈92)
- 12. مثنوی معنوی — Jalaluddin Mevlana Rumi (n≈74)

### cocitation_pmi
- 1. يوتوبيا — Ahmed Khaled Towfik (n≈1107)
- 2. رباعيات صلاح جاهين — SlH jhyn (n≈929)
- 3. تراب الماس — 'Hmd mrd (n≈1297)
- 4. الطنطورية — Radwa Ashour (n≈1429)
- 5. الفيل الأزرق — 'Hmd mrd (n≈954)
- 6. ثلاثية غرناطة — Radwa Ashour (n≈2416)
- 7. ڤيرتيجو — 'Hmd mrd (n≈485)
- 8. الأسود يليق بك — 'Hlm mstGnmy (n≈1020)
- 9. عزازيل — ywsf zydn (n≈2224)
- 10. المانيفستو — mSTf~ brhym (n≈561)
- 11. هيبتا — mHmd Sdq (n≈910)
- 12. الحرافيش — Naguib Mahfouz (n≈939)

### hits_rarity_weighted
- 1. A Game of Thrones (A Song of Ice and Fire, #1) — George R.R. Martin (n≈54100)
- 2. The Book Thief — Markus Zusak (n≈51369)
- 3. City of Glass (The Mortal Instruments, #3) — Cassandra Clare (n≈29904)
- 4. The Fellowship of the Ring (The Lord of the Rings, #1) — J.R.R. Tolkien (n≈53247)
- 5. City of Bones (The Mortal Instruments, #1) — Cassandra Clare (n≈34575)
- 6. Clockwork Angel (The Infernal Devices, #1) — Cassandra Clare (n≈23340)
- 7. City of Ashes (The Mortal Instruments, #2) — Cassandra Clare (n≈24425)
- 8. Clockwork Princess (The Infernal Devices, #3) — Cassandra Clare (n≈20147)
- 9. The Lightning Thief (Percy Jackson and the Olympians, #1) — Rick Riordan (n≈31261)
- 10. The Lion, the Witch, and the Wardrobe (Chronicles of Narnia, #1) — C.S. Lewis (n≈38306)
- 11. Clockwork Prince (The Infernal Devices, #2) — Cassandra Clare (n≈20192)
- 12. The Help — Kathryn Stockett (n≈45156)

### lizardo_neg_delta2
- 1. Daun Yang Jatuh Tak Pernah Membenci Angin — Tere Liye (n≈173)
- 2. Sunset Bersama Rosie — Tere Liye (n≈115)
- 3. Rembulan Tenggelam Di Wajahmu — Tere Liye (n≈254)
- 4. Ayahku (Bukan) Pembohong — Tere Liye (n≈135)
- 5. Bidadari Bidadari Surga — Tere Liye (n≈234)
- 6. Fierce (Storm MC, #2) — Nina  Levine (n≈129)
- 7. Storm (Storm MC, #1) — Nina  Levine (n≈146)
- 8. Hafalan Shalat Delisa — Tere Liye (n≈306)
- 9. Ketika Cinta Bertasbih — Habiburrahman El-Shirazy (n≈159)
- 10. Bulletproof (A Matter of Time #5) — Mary Calmes (n≈112)
- 11. أسطورة بعد منتصف الليل — 'Hmd khld twfyq (n≈254)
- 12. حلقة الرعب — 'Hmd khld twfyq (n≈242)

### lizardo_niche_enthusiasts
- 1. رياض الصالحين — yHy~ bn shrf lnwwy (n≈368)
- 2. حصن المسلم: من أذكار الكتاب والسنة — s`yd bn `ly bn whf lqHTny (n≈135)
- 3. Tutunamayanlar — Oguz Atay (n≈233)
- 4. لا تصالح — 'ml dnql (n≈534)
- 5. A Court of Mist and Fury (A Court of Thorns and Roses, #2) — Sarah J. Maas (n≈608)
- 6. Bluestar's Prophecy (Warriors Super Edition, #2) — Erin Hunter (n≈136)
- 7. The Last Hope (Warriors: Omen of the Stars, #6) — Erin Hunter (n≈114)
- 8. مثنوی معنوی — Jalaluddin Mevlana Rumi (n≈143)
- 9. ديوان الإمام الشافعي — mHmd bn drys lshf`y (n≈344)
- 10. The Coldest Winter Ever — Sister Souljah (n≈586)
- 11. The Lightning-Struck Heart (Tales From Verania, #1) — T.J. Klune (n≈164)
- 12. The Darkest Hour (Warriors, #6) — Erin Hunter (n≈335)

### lizardo_high_order
- 1. تراب الماس — 'Hmd mrd (n≈1241)
- 2. في قلبي أنثى عبرية — khwl@ Hmdy (n≈997)
- 3. يوتوبيا — Ahmed Khaled Towfik (n≈1043)
- 4. الجزار — Hsn ljndy (n≈375)
- 5. الفيل الأزرق — 'Hmd mrd (n≈914)
- 6. هيبتا — mHmd Sdq (n≈866)
- 7. 1/4 جرام — Essam Youssef (n≈610)
- 8. ڤيرتيجو — 'Hmd mrd (n≈475)
- 9. ترنيمة سلام — 'Hmd `bd lmjyd (n≈358)
- 10. المانيفستو — mSTf~ brhym (n≈536)
- 11. رغم الفراق — nwr `bdlmjyd (n≈273)
- 12. أنت لي — mn~ lmrshwd (n≈538)

### feldkamp_dual_axis
- 1. ليتها تقرأ — khld lbtly (n≈154)
- 2. One Night at the Call Center — Chetan Bhagat (n≈90)
- 3. نيكروفيليا — shyryn hny'y (n≈90)
- 4. حبيبتي بكماء — mHmd lslm (n≈62)
- 5. ظل الأفعى — ywsf zydn (n≈248)
- 6. The 3 Mistakes of My Life — Chetan Bhagat (n≈194)
- 7. Revolution 2020: Love, Corruption, Ambition — Chetan Bhagat (n≈169)
- 8. السنجة — 'Hmd khld twfyq (n≈146)
- 9. في ديسمبر تنتهي كل الأحلام — 'thyr `bdllh lnshmy (n≈267)
- 10. فلتغفري — 'thyr `bdllh lnshmy (n≈325)
- 11. الرجال من بولاق والنساء من أول فيصل — yhb m`wD (n≈66)
- 12. "حكايات فرغلي المستكاوي "حكايتى مع كفر السحلاوية — Hsn ljndy (n≈203)

### nested_community_portfolio
- 1. حكايات التاروت — 'Hmd khld twfyq (n≈154)
- 2. أسطورة آخر الليل — 'Hmd khld twfyq (n≈140)
- 3. The Major Works — William Wordsworth (n≈135)
- 4. اغتصاب ولكن تحت سقف واحد — d` `bd lrHmn (n≈142)
- 5. قطة في عرين الأسد — mn~ slm@ (n≈114)
- 6. اكتشفت زوجى فى الأتوبيس — msh`r Gly@ (n≈129)
- 7. أسطورة المواجهة — 'Hmd khld twfyq (n≈93)
- 8. أسطورة إيجور — 'Hmd khld twfyq (n≈144)
- 9. أسطورة النافاراي — 'Hmd khld twfyq (n≈87)
- 10. Poetry and Prose — Percy Bysshe Shelley (n≈89)
- 11. أسطورة رفعت — 'Hmd khld twfyq (n≈88)
- 12. أسطورتنا — 'Hmd khld twfyq (n≈100)

Within-community heads (nested portfolio):
- Community 0 (size=100, dense_users=3133):
  - 1. An Autobiography — Angela Y. Davis
  - 2. This Bridge Called My Back: Writings by Radical Women of Color — Cherrie L. Moraga
  - 3. The Mis-Education of the Negro — Carter G. Woodson
  - 4. Soul on Ice — Eldridge Cleaver
  - 5. Race Matters — Cornel West
- Community 1 (size=98, dense_users=1961):
  - 1. The Hard Thing About Hard Things: Building a Business When There Are No Easy Answers — Ben Horowitz
  - 2. Smartcuts: How Hackers, Innovators, and Icons Accelerate Success — Shane Snow
  - 3. The Inevitable: Understanding the 12 Technological Forces That Will Shape Our Future — Kevin Kelly
  - 4. The Start-Up of You: Adapt to the Future, Invest in Yourself, and Transform Your Career — Reid Hoffman
  - 5. Hooked: How to Build Habit-Forming Products — Nir Eyal
- Community 2 (size=91, dense_users=1721):
  - 1. The Missing — C.L. Taylor
  - 2. Between You and Me — Lisa     Hall
  - 3. The Lie — C.L. Taylor
  - 4. The Secret (DS Imogen Grey, #2) — Katerina Diamond
  - 5. Lying in Wait — Liz Nugent
- Community 3 (size=74, dense_users=3083):
  - 1. The Major Works — William Wordsworth
  - 2. The Complete Poems — William Blake
  - 3. The Complete Poems — Samuel Taylor Coleridge
  - 4. The Complete Poems — Percy Bysshe Shelley
  - 5. Poetry and Prose — Percy Bysshe Shelley
- Community 4 (size=72, dense_users=1726):
  - 1. West Side Story — Irving Shulman
  - 2. Fiddler on the Roof — Joseph Stein
  - 3. Sweeney Todd: The Demon Barber of Fleet Street — Stephen Sondheim
  - 4. The Odd Couple — Neil Simon
  - 5. Crimes of the Heart — Beth Henley
- Community 5 (size=69, dense_users=1961):
  - 1. Sacred Contracts: Awakening Your Divine Potential — Caroline Myss
  - 2. Why People Don't Heal and How They Can: A Practical Programme for Healing Body, Mind and Spirit — Caroline Myss
  - 3. Heal Your Body: The Mental Causes for Physical Illness and the Metaphysical Way to Overcome Them — Louise L. Hay
  - 4. Soul Stories — Gary Zukav
  - 5. A Course in Miracles — Foundation for Inner Peace
- Community 6 (size=67, dense_users=1472):
  - 1. The Seventh Wish — Kate Messner
  - 2. A Handful of Stars — Cynthia Lord
  - 3. Ms. Bixby's Last Day — John David  Anderson
  - 4. All Rise for the Honorable Perry T. Cook — Leslie Connor
  - 5. Some Kind of Courage — Dan Gemeinhart
- Community 7 (size=67, dense_users=1421):
  - 1. اغتصاب ولكن تحت سقف واحد — d` `bd lrHmn
  - 2. قطة في عرين الأسد — mn~ slm@
  - 3. اكتشفت زوجى فى الأتوبيس — msh`r Gly@
  - 4. أماريتا — `mrw `bd lHmyd
  - 5. مزرعة الدموع — mn~ slm@
- Community 8 (size=66, dense_users=2305):
  - 1. Batman: Knightfall, Vol. 1: Broken Bat — Doug Moench
  - 2. Batman: Knightfall, Vol. 3: Knightsend — Doug Moench
  - 3. Batman: Dark Victory — Jeph Loeb
  - 4. Batman: A Death in the Family — Jim Starlin
  - 5. Batman: No Man's Land, Vol. 1 — Bob Gale
- Community 9 (size=66, dense_users=2120):
  - 1. They Both Die at the End — Adam Silvera
  - 2. Ramona Blue — Julie   Murphy
  - 3. History Is All You Left Me — Adam Silvera
  - 4. Dear Martin — Nic Stone
  - 5. True Letters from a Fictional Life — Kenneth Logan
- Community 10 (size=66, dense_users=501):
  - 1. حكايات التاروت — 'Hmd khld twfyq
  - 2. أسطورة آخر الليل — 'Hmd khld twfyq
  - 3. أسطورة المواجهة — 'Hmd khld twfyq
  - 4. أسطورة إيجور — 'Hmd khld twfyq
  - 5. أسطورة النافاراي — 'Hmd khld twfyq
- Community 11 (size=61, dense_users=2463):
  - 1. Mrs. McGinty's Dead (Hercule Poirot, #28) — Agatha Christie
  - 2. Third Girl (Hercule Poirot, #35) — Agatha Christie
  - 3. After the Funeral (Hercule Poirot, #29) — Agatha Christie
  - 4. Appointment with Death (Hercule Poirot, #19) — Agatha Christie
  - 5. The Clocks (Hercule Poirot, #34) — Agatha Christie

### nested_mass_community_reflections
- 1. The Unadulterated Cat — Terry Pratchett (n≈92)
- 2. The Dark Side of the Sun — Terry Pratchett (n≈65)
- 3. The First Discworld Novels the Colour of Magic and the Light Fantastic — Terry Pratchett (n≈132)
- 4. The Wit and Wisdom of Discworld — Terry Pratchett (n≈47)
- 5. The Discworld Mapp: Being the Onlie True and Mostlie Accurate Mappe of the Fantastyk and Magical Dyscworlde — Terry Pratchett (n≈64)
- 6. Eric (Discworld, #9; Rincewind #4) — Terry Pratchett (n≈629)
- 7. The Amazing Maurice and His Educated Rodents (Discworld, #28) — Terry Pratchett (n≈625)
- 8. The Last Hero (Discworld, #27; Rincewind #7) — Terry Pratchett (n≈677)
- 9. The Last Continent (Discworld, #22; Rincewind #6) — Terry Pratchett (n≈812)
- 10. Unseen Academicals (Discworld, #37; Rincewind #8) — Terry Pratchett (n≈692)
- 11. Nation — Terry Pratchett (n≈544)
- 12. The Hollow Chocolate Bunnies of the Apocalypse — Robert Rankin (n≈44)

## Notes

- Discovery signal remains ratings-only; catalog flags only for readable heads.
- `lizardo_*`: reflections on mid-pop 5★ bipartite graph (n∈[200,20000]).
- `nested_community_portfolio`: PMI label-propagation + round-robin heads.
- `feldkamp_dual_axis`: `−δ² − 0.75·z(mean)`.

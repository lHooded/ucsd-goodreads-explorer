# Seedless bridge-reader canon pilot

## Design

Discovery used only `(user_id, work_id, rating)`. A reader's bridge score is the directional dispersion of their sampled five-star books inside the leading stable ratings-only taste subspace, multiplied by structural signal strength. It is invariant to rotations of tied spectral modes. The top 10% form the bridge cohort; the top 10% by directional concentration form the specialist cohort.

Matrix: **233,271 readers × 26,418 works**; bridge readers: **23,289**; specialist readers: **23,289**; runtime: **14.5s**.

Titles, authors, and literary/anti lists were loaded only after cohort membership, book scores, and half-sample stability were frozen.

## Ranking stability

| ranking | half | score Spearman | J@50 | J@100 | J@200 | J@500 | common books |
|---|---:|---:|---:|---:|---:|---:|---:|
| bridge | 0 | 0.941 | 0.667 | 0.709 | 0.639 | 0.675 | 4,283 |
| bridge | 1 | 0.936 | 0.754 | 0.770 | 0.633 | 0.675 | 4,306 |
| specialist | 0 | 0.967 | 0.786 | 0.600 | 0.646 | 0.736 | 4,330 |
| specialist | 1 | 0.968 | 0.754 | 0.626 | 0.626 | 0.721 | 4,319 |
| all_eligible | 0 | 0.970 | 0.613 | 0.653 | 0.724 | 0.704 | 26,352 |
| all_eligible | 1 | 0.971 | 0.613 | 0.724 | 0.702 | 0.667 | 26,365 |
| bridge_exposure | 0 | 0.860 | 0.639 | 0.802 | 0.835 | 0.773 | 26,352 |
| bridge_exposure | 1 | 0.863 | 0.538 | 0.681 | 0.810 | 0.751 | 26,365 |
| specialist_exposure | 0 | 0.873 | 0.538 | 0.575 | 0.575 | 0.701 | 26,352 |
| specialist_exposure | 1 | 0.862 | 0.562 | 0.613 | 0.702 | 0.684 | 26,365 |
| bridge_minus_specialist | 0 | 0.830 | 0.613 | 0.587 | 0.562 | 0.488 | 3,413 |
| bridge_minus_specialist | 1 | 0.827 | 0.538 | 0.587 | 0.509 | 0.490 | 3,407 |

## Post-hoc evaluation

### bridge

Exact literary seed overlap @50/200/500: **0 / 2 / 4**. Broad literary overlap: **0 / 2 / 5**. Anti overlap: **26 / 93 / 207**.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.893 ± 0.015; sample readers=339)
2. *The Return of the King (The Lord of the Rings, #3)* — J.R.R. Tolkien (0.888 ± 0.010; sample readers=1,760)
3. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.887 ± 0.007; sample readers=4,368)
4. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.887 ± 0.010; sample readers=1,758)
5. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.871 ± 0.019; sample readers=418)
6. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.863 ± 0.008; sample readers=3,858)
7. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.862 ± 0.020; sample readers=445)
8. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.858 ± 0.008; sample readers=4,040)
9. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.854 ± 0.008; sample readers=4,233)
10. *The Name of the Wind (The Kingkiller Chronicle, #1)* — Patrick Rothfuss (0.850 ± 0.014; sample readers=1,377)
11. *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin (0.834 ± 0.010; sample readers=3,016)
12. *The Lord of the Rings (The Lord of the Rings, #1-3)* — J.R.R. Tolkien (0.826 ± 0.016; sample readers=1,072)
13. *The Hero of Ages (Mistborn, #3)* — Brandon Sanderson (0.821 ± 0.024; sample readers=404)
14. *Towers of Midnight (Wheel of Time, #13)* — Robert Jordan (0.807 ± 0.030; sample readers=187)
15. *The Two Towers (The Lord of the Rings, #2)* — J.R.R. Tolkien (0.804 ± 0.015; sample readers=1,551)
16. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.802 ± 0.008; sample readers=5,624)
17. *The Qur'an / القرآن الكريم* — Anonymous (0.802 ± 0.030; sample readers=216)
18. *The Wise Man's Fear (The Kingkiller Chronicle, #2)* — Patrick Rothfuss (0.797 ± 0.019; sample readers=904)
19. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.795 ± 0.030; sample readers=146)
20. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.791 ± 0.026; sample readers=429)
21. *A Clash of Kings  (A Song of Ice and Fire, #2)* — George R.R. Martin (0.789 ± 0.015; sample readers=1,640)
22. *The Final Empire (Mistborn, #1)* — Brandon Sanderson (0.782 ± 0.023; sample readers=614)
23. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.775 ± 0.010; sample readers=3,722)
24. *A Memory of Light (Wheel of Time, #14)* — Robert Jordan (0.766 ± 0.036; sample readers=176)
25. *Season of Mists (The Sandman #4)* — Neil Gaiman (0.760 ± 0.033; sample readers=104)
26. *The Hunger Games (The Hunger Games, #1)* — Suzanne Collins (0.753 ± 0.009; sample readers=4,881)
27. *J.R.R. Tolkien 4-Book Boxed Set: The Hobbit and The Lord of the Rings* — J.R.R. Tolkien (0.753 ± 0.038; sample readers=181)
28. *The Nightingale* — Kristin Hannah (0.743 ± 0.035; sample readers=276)
29. *رباعيات صلاح جاهين* — SlH jhyn (0.739 ± 0.041; sample readers=150)
30. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.737 ± 0.042; sample readers=139)

### specialist

Exact literary seed overlap @50/200/500: **0 / 0 / 1**. Broad literary overlap: **0 / 1 / 3**. Anti overlap: **38 / 117 / 213**.

1. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.952 ± 0.004; sample readers=6,876)
2. *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling (0.939 ± 0.004; sample readers=6,640)
3. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.939 ± 0.009; sample readers=642)
4. *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling (0.938 ± 0.004; sample readers=6,843)
5. *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling (0.931 ± 0.004; sample readers=6,942)
6. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.922 ± 0.011; sample readers=499)
7. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.910 ± 0.010; sample readers=1,557)
8. *The Way of Kings (The Stormlight Archive, #1)* — Brandon Sanderson (0.908 ± 0.013; sample readers=704)
9. *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling (0.904 ± 0.005; sample readers=6,362)
10. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.896 ± 0.014; sample readers=722)
11. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (0.893 ± 0.010; sample readers=1,778)
12. *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling (0.886 ± 0.005; sample readers=7,461)
13. *Changes (The Dresden Files, #12)* — Jim Butcher (0.879 ± 0.018; sample readers=399)
14. *The Hate U Give* — Angie Thomas (0.869 ± 0.019; sample readers=363)
15. *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling (0.863 ± 0.006; sample readers=6,489)
16. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (0.860 ± 0.013; sample readers=1,281)
17. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (0.851 ± 0.013; sample readers=1,549)
18. *Cress (The Lunar Chronicles, #3)* — Marissa Meyer (0.849 ± 0.015; sample readers=1,130)
19. *Winter (The Lunar Chronicles, #4)* — Marissa Meyer (0.842 ± 0.016; sample readers=950)
20. *Turn Coat (The Dresden Files, #11)* — Jim Butcher (0.841 ± 0.023; sample readers=335)
21. *We Should All Be Feminists* — Chimamanda Ngozi Adichie (0.832 ± 0.025; sample readers=255)
22. *The Last Olympian (Percy Jackson and the Olympians, #5)* — Rick Riordan (0.832 ± 0.014; sample readers=1,550)
23. *The Qur'an / القرآن الكريم* — Anonymous (0.827 ± 0.021; sample readers=147)
24. *The House of Hades (The Heroes of Olympus, #4)* — Rick Riordan (0.827 ± 0.018; sample readers=806)
25. *Six of Crows (Six of Crows, #1)* — Leigh Bardugo (0.823 ± 0.017; sample readers=942)
26. *A Storm of Swords (A Song of Ice and Fire, #3)* — George R.R. Martin (0.818 ± 0.018; sample readers=911)
27. *Small Favor (The Dresden Files, #10)* — Jim Butcher (0.817 ± 0.026; sample readers=331)
28. *Skin Game (The Dresden Files, #15)* — Jim Butcher (0.816 ± 0.027; sample readers=276)
29. *Cold Days (The Dresden Files, #14)* — Jim Butcher (0.814 ± 0.027; sample readers=315)
30. *Heir of Fire (Throne of Glass, #3)* — Sarah J. Maas (0.813 ± 0.016; sample readers=1,293)

### all_eligible

Exact literary seed overlap @50/200/500: **0 / 0 / 2**. Broad literary overlap: **0 / 1 / 7**. Anti overlap: **11 / 54 / 112**.

1. *Words of Radiance (The Stormlight Archive, #2)* — Brandon Sanderson (0.924 ± 0.009; sample readers=1,675)
2. *The Complete Calvin and Hobbes* — Bill Watterson (0.918 ± 0.012; sample readers=500)
3. *March: Book Two (March, #2)* — John             Lewis (0.895 ± 0.014; sample readers=288)
4. *Harry Potter Boxset (Harry Potter, #1-7)* — J.K. Rowling (0.894 ± 0.008; sample readers=3,027)
5. *The Hate U Give* — Angie Thomas (0.886 ± 0.010; sample readers=1,872)
6. *The Authoritative Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.874 ± 0.019; sample readers=320)
7. *Just Mercy: A Story of Justice and Redemption* — Bryan Stevenson (0.869 ± 0.018; sample readers=573)
8. *The Indispensable Calvin and Hobbes* — Bill Watterson (0.861 ± 0.020; sample readers=241)
9. *March: Book Three (March, #3)* — John             Lewis (0.860 ± 0.021; sample readers=252)
10. *The Essential Calvin and Hobbes: A Calvin and Hobbes Treasury* — Bill Watterson (0.856 ± 0.016; sample readers=912)
11. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (0.852 ± 0.009; sample readers=3,399)
12. *The Days Are Just Packed: A Calvin and Hobbes Collection* — Bill Watterson (0.850 ± 0.023; sample readers=282)
13. *Calvin and Hobbes* — Bill Watterson (0.850 ± 0.016; sample readers=989)
14. *Crooked Kingdom (Six of Crows, #2)* — Leigh Bardugo (0.846 ± 0.013; sample readers=1,608)
15. *It's a Magical World: A Calvin and Hobbes Collection* — Bill Watterson (0.841 ± 0.024; sample readers=270)
16. *Born a Crime: Stories From a South African Childhood* — Trevor Noah (0.841 ± 0.016; sample readers=1,060)
17. *Harry Potter Collection (Harry Potter, #1-6)* — J.K. Rowling (0.837 ± 0.025; sample readers=264)
18. *Hamilton: The Revolution* — Lin-Manuel Miranda (0.834 ± 0.020; sample readers=634)
19. *Nothing to Envy: Ordinary Lives in North Korea* — Barbara Demick (0.826 ± 0.020; sample readers=632)
20. *Saga, Vol. 3 (Saga, #3)* — Brian K. Vaughan (0.826 ± 0.015; sample readers=1,360)
21. *The Kindly Ones (The Sandman #9)* — Neil Gaiman (0.823 ± 0.021; sample readers=628)
22. *Homicidal Psycho Jungle Cat: A Calvin and Hobbes Collection* — Bill Watterson (0.823 ± 0.027; sample readers=226)
23. *The Revenge of the Baby-Sat* — Bill Watterson (0.822 ± 0.027; sample readers=186)
24. *Humans of New York: Stories* — Brandon Stanton (0.822 ± 0.027; sample readers=263)
25. *Attack of the Deranged Mutant Killer Monster Snow Goons* — Bill Watterson (0.821 ± 0.027; sample readers=196)
26. *The Complete Maus (Maus, #1-2)* — Art Spiegelman (0.818 ± 0.013; sample readers=1,746)
27. *Saga, Vol. 2 (Saga, #2)* — Brian K. Vaughan (0.816 ± 0.014; sample readers=1,678)
28. *A Storm of Swords: Blood and Gold (A Song of Ice and Fire, #3: Part 2 of 2)* — George R.R. Martin (0.816 ± 0.018; sample readers=942)
29. *Assassin's Fate (The Fitz and the Fool, #3)* — Robin Hobb (0.812 ± 0.029; sample readers=204)
30. *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling (0.812 ± 0.004; sample readers=25,528)

### bridge_exposure

Exact literary seed overlap @50/200/500: **0 / 0 / 0**. Broad literary overlap: **0 / 0 / 1**. Anti overlap: **0 / 0 / 65**.

1. *ڤيرتيجو* — 'Hmd mrd (2.541 ± 0.101; sample readers=357)
2. *1919* — 'Hmd mrd (2.478 ± 0.107; sample readers=303)
3. *1/4 جرام* — Essam Youssef (2.434 ± 0.105; sample readers=317)
4. *مالك* — mHmwd bkry (2.402 ± 0.140; sample readers=157)
5. *الفيل الأزرق* — 'Hmd mrd (2.369 ± 0.072; sample readers=717)
6. *شاب كشك في رحلة البحث عن الجادون* — `mrw slm@ (2.369 ± 0.124; sample readers=210)
7. *فلتغفري* — 'thyr `bdllh lnshmy (2.360 ± 0.098; sample readers=372)
8. *المرحوم* — Hsn kml (2.354 ± 0.128; sample readers=195)
9. *هيبتا* — mHmd Sdq (2.353 ± 0.077; sample readers=628)
10. *E.S.P.* — 'Hmd khld twfyq (2.343 ± 0.144; sample readers=144)
11. *أنا عشقت* — mHmd lmnsy qndyl (2.321 ± 0.124; sample readers=212)
12. *بضع ساعات في يوم ما* — mHmd Sdq (2.304 ± 0.145; sample readers=140)
13. *زوجي مازال حبيبي* — sr@ drwysh (2.296 ± 0.140; sample readers=156)
14. *ليست عذراء* — dyn `md (2.289 ± 0.161; sample readers=105)
15. *قصاصات قابلة للحرق* — 'Hmd khld twfyq (2.289 ± 0.122; sample readers=218)
16. *أرض الإله* — 'Hmd mrd (2.277 ± 0.140; sample readers=154)
17. *صندوق الدمى* — shyryn hny'y (2.254 ± 0.136; sample readers=166)
18. *رغم الفراق* — nwr `bdlmjyd (2.241 ± 0.144; sample readers=142)
19. *عناق عند جسر بروكلين* — Ezzedine C. Fishere (2.236 ± 0.122; sample readers=219)
20. *قهوة وشيكولاتة* — `mr Thr (2.236 ± 0.157; sample readers=113)
21. *أحببتك أكثر مما ينبغي* — 'thyr `bdllh lnshmy (2.235 ± 0.078; sample readers=608)
22. *نيكروفيليا* — shyryn hny'y (2.224 ± 0.112; sample readers=270)
23. *الليلة الثالثة والعشرون* — tmr brhym (2.222 ± 0.152; sample readers=124)
24. *"حكايات فرغلي المستكاوي "حكايتى مع كفر السحلاوية* — Hsn ljndy (2.220 ± 0.118; sample readers=235)
25. *9 ملي* — Amr Algendy - `mrw ljndy (2.213 ± 0.171; sample readers=87)
26. *الجزار* — Hsn ljndy (2.208 ± 0.133; sample readers=175)
27. *نادي السيارات* — Alaa Al Aswany (2.205 ± 0.114; sample readers=259)
28. *في ديسمبر تنتهي كل الأحلام* — 'thyr `bdllh lnshmy (2.204 ± 0.098; sample readers=363)
29. *28 حرف* — 'Hmd Hlmy (2.203 ± 0.095; sample readers=393)
30. *انستا_حياة#* — mHmd Sdq (2.199 ± 0.147; sample readers=136)

### specialist_exposure

Exact literary seed overlap @50/200/500: **0 / 0 / 0**. Broad literary overlap: **0 / 2 / 2**. Anti overlap: **26 / 88 / 209**.

1. *الإسلام بين الشرق والغرب* — Alija Izetbegovic (2.350 ± 0.108; sample readers=296)
2. *Lord of Shadows (The Dark Artifices, #2)* — Cassandra Clare (2.310 ± 0.077; sample readers=634)
3. *Queen of Shadows (Throne of Glass, #4)* — Sarah J. Maas (2.240 ± 0.040; sample readers=2,470)
4. *Fruits Basket, Vol. 19* — Natsuki Takaya (2.199 ± 0.160; sample readers=106)
5. *Fullmetal Alchemist, Vol. 16 (Fullmetal Alchemist, #16)* — Hiromu Arakawa (2.165 ± 0.183; sample readers=70)
6. *The Assassin's Blade (Throne of Glass, #0.1-0.5)* — Sarah J. Maas (2.152 ± 0.057; sample readers=1,187)
7. *Fullmetal Alchemist, Vol. 11 (Fullmetal Alchemist, #11)* — Hiromu Arakawa (2.148 ± 0.183; sample readers=69)
8. *Lady Midnight (The Dark Artifices, #1)* — Cassandra Clare (2.141 ± 0.051; sample readers=1,476)
9. *Fruits Basket, Vol. 17* — Natsuki Takaya (2.133 ± 0.162; sample readers=103)
10. *أمير الظل: مهندس على الطريق* — `bd llh Glb lbrGwthy (2.127 ± 0.134; sample readers=172)
11. *Fruits Basket, Vol. 11* — Natsuki Takaya (2.124 ± 0.146; sample readers=137)
12. *Fullmetal Alchemist, Vol. 20 (Fullmetal Alchemist, #20)* — Hiromu Arakawa (2.117 ± 0.180; sample readers=73)
13. *Fruits Basket, Vol. 16* — Natsuki Takaya (2.116 ± 0.154; sample readers=119)
14. *طبائع الاستبداد ومصارع الاستعباد* — `bd lrHmn lkwkby (2.103 ± 0.110; sample readers=284)
15. *Heir of Fire (Throne of Glass, #3)* — Sarah J. Maas (2.081 ± 0.038; sample readers=2,709)
16. *الطنطورية* — Radwa Ashour (2.072 ± 0.083; sample readers=535)
17. *Empire of Storms (Throne of Glass, #5)* — Sarah J. Maas (2.070 ± 0.048; sample readers=1,684)
18. *Tales from the Shadowhunter Academy* — Cassandra Clare (2.065 ± 0.108; sample readers=293)
19. *Fruits Basket, Vol. 18* — Natsuki Takaya (2.054 ± 0.156; sample readers=116)
20. *Fullmetal Alchemist, Vol. 17 (Fullmetal Alchemist, #17)* — Hiromu Arakawa (2.042 ± 0.199; sample readers=52)
21. *Crown of Midnight (Throne of Glass, #2)* — Sarah J. Maas (2.026 ± 0.034; sample readers=3,351)
22. *Fruits Basket, Vol. 4* — Natsuki Takaya (2.024 ± 0.129; sample readers=191)
23. *Fullmetal Alchemist, Vol. 25 (Fullmetal Alchemist, #25)* — Hiromu Arakawa (2.023 ± 0.188; sample readers=64)
24. *Fruits Basket, Vol. 12* — Natsuki Takaya (2.017 ± 0.156; sample readers=115)
25. *Fruits Basket, Vol. 5* — Natsuki Takaya (2.015 ± 0.140; sample readers=157)
26. *A Court of Mist and Fury (A Court of Thorns and Roses, #2)* — Sarah J. Maas (2.010 ± 0.034; sample readers=3,399)
27. *Fullmetal Alchemist, Vol. 10 (Fullmetal Alchemist, #10)* — Hiromu Arakawa (2.008 ± 0.172; sample readers=87)
28. *أفراح الروح* — Sayed Qutb (2.000 ± 0.124; sample readers=212)
29. *Clockwork Princess (The Infernal Devices, #3)* — Cassandra Clare (1.993 ± 0.032; sample readers=3,924)
30. *أيام من حياتى* — zynb lGzly (1.988 ± 0.168; sample readers=93)

### bridge_minus_specialist

Exact literary seed overlap @50/200/500: **0 / 3 / 4**. Broad literary overlap: **0 / 6 / 11**. Anti overlap: **39 / 116 / 195**.

1. *The Path of Daggers (Wheel of Time, #8)* — Robert Jordan (1.075 ± 0.069; sample readers=154)
2. *Winter's Heart (Wheel of Time, #9)* — Robert Jordan (1.016 ± 0.081; sample readers=158)
3. *Matched (Matched, #1)* — Ally Condie (0.870 ± 0.031; sample readers=958)
4. *A Crown of Swords (Wheel of Time, #7)* — Robert Jordan (0.854 ± 0.084; sample readers=166)
5. *Crossroads of Twilight (Wheel of Time, #10)* — Robert Jordan (0.852 ± 0.080; sample readers=154)
6. *Eclipse (Twilight, #3)* — Stephenie Meyer (0.834 ± 0.021; sample readers=2,023)
7. *Breaking Dawn (Twilight, #4)* — Stephenie Meyer (0.834 ± 0.023; sample readers=1,982)
8. *Crescendo (Hush, Hush, #2)* — Becca Fitzpatrick (0.833 ± 0.049; sample readers=437)
9. *Wicked (Pretty Little Liars, #5)* — Sara Shepard (0.830 ± 0.104; sample readers=80)
10. *Untamed (House of Night, #4)* — P.C. Cast (0.809 ± 0.052; sample readers=240)
11. *Heartless (Pretty Little Liars, #7)* — Sara Shepard (0.807 ± 0.126; sample readers=64)
12. *Fallen (Fallen, #1)* — Lauren Kate (0.799 ± 0.032; sample readers=706)
13. *The Elite (The Selection, #2)* — Kiera Cass (0.797 ± 0.043; sample readers=772)
14. *The Heir (The Selection, #4)* — Kiera Cass (0.784 ± 0.056; sample readers=398)
15. *Silence (Hush, Hush, #3)* — Becca Fitzpatrick (0.780 ± 0.062; sample readers=317)
16. *Temple of the Winds (Sword of Truth, #4)* — Terry Goodkind (0.774 ± 0.104; sample readers=87)
17. *Twilight (Twilight, #1)* — Stephenie Meyer (0.769 ± 0.017; sample readers=3,461)
18. *Chosen (House of Night, #3)* — P.C. Cast (0.769 ± 0.049; sample readers=261)
19. *Hunted (House of Night, #5)* — P.C. Cast (0.760 ± 0.053; sample readers=224)
20. *New Moon (Twilight, #2)* — Stephenie Meyer (0.757 ± 0.019; sample readers=2,224)
21. *Hush, Hush (Hush, Hush, #1)* — Becca Fitzpatrick (0.751 ± 0.039; sample readers=741)
22. *Faith of the Fallen (Sword of Truth, #6)* — Terry Goodkind (0.742 ± 0.123; sample readers=79)
23. *Stone of Tears (Sword of Truth, #2)* — Terry Goodkind (0.729 ± 0.106; sample readers=109)
24. *The Crown (The Selection, #5)* — Kiera Cass (0.725 ± 0.068; sample readers=259)
25. *Pretty Little Liars (Pretty Little Liars, #1)* — Sara Shepard (0.725 ± 0.057; sample readers=301)
26. *Betrayed (House of Night, #2)* — P.C. Cast (0.722 ± 0.048; sample readers=269)
27. *Tempted (House of Night, #6)* — P.C. Cast (0.713 ± 0.055; sample readers=188)
28. *Blood of the Fold (Sword of Truth, #3)* — Terry Goodkind (0.712 ± 0.106; sample readers=96)
29. *Confessor (Sword of Truth, #11)* — Terry Goodkind (0.711 ± 0.143; sample readers=47)
30. *Marked (House of Night, #1)* — P.C. Cast (0.710 ± 0.035; sample readers=576)

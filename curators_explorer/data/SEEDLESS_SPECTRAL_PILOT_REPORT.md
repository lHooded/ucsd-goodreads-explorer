# Seedless signed spectral pilot

## Design

Discovery used only `(user_id, work_id, rating)`. Each reader contributes equal total positive (5-star) and negative (1–3-star) mass. Ratings-derived book popularity, mean, five-star tendency, user activity, and generosity are projected out. Titles, authors, flags, and semantic lists are loaded only after all full/half/null decompositions finish.

Matrix: **233,271 users × 104,872 works**, **7,447,233 signed edges**. Runtime: **57.5s**; matrix cache: **20.7 MiB**.

The two half-sample fits use disjoint readers. The shuffled null preserves each reader's positive/negative counts and the global positive/negative book frequencies while destroying reader-level co-preference.

## Spectrum and stability

### Stable-subspace test

Unlike individual-vector correlation, this test allows tied or nearly tied modes to rotate within the same shared subspace.

| leading modes | full↔half mean sq. corr | full↔half weakest | half↔half mean sq. corr | half↔half weakest |
|---:|---:|---:|---:|---:|
| 1 | 0.002 | 0.035 | 0.055 | 0.234 |
| 2 | 0.197 | 0.029 | 0.045 | 0.018 |
| 3 | 0.269 | 0.013 | 0.039 | 0.006 |
| 4 | 0.393 | 0.034 | 0.085 | 0.003 |
| 6 | 0.339 | 0.004 | 0.132 | 0.002 |
| 8 | 0.307 | 0.022 | 0.105 | 0.001 |
| 12 | 0.251 | 0.015 | 0.075 | 0.004 |
| 16 | 0.236 | 0.009 | 0.061 | 0.000 |
| 24 | 0.227 | 0.007 | 0.048 | 0.001 |
| 32 | 0.215 | 0.006 | 0.039 | 0.002 |
| 40 | 0.206 | 0.006 | 0.034 | 0.002 |

### Individual modes

`eff. books` is the inverse concentration of squared loadings: larger means broader; `top50 mass` is the fraction of a mode carried by its 50 most extreme books.

| mode | singular | null | excess | residual | half corr | half pole J@100 | eff. books | top50 mass | exact lit +/− @50 | broad lit +/− @50 | anti +/− @50 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.3515 | 0.2116 | 1.66 | 2.36e-02 | 0.788 | 0.376 | 35 | 0.718 | 0/0 | 0/0 | 0/0 |
| 2 | 0.3502 | 0.2111 | 1.66 | 2.16e-02 | 0.713 | 0.517 | 112 | 0.574 | 0/0 | 0/0 | 0/0 |
| 3 | 0.3414 | 0.2110 | 1.62 | 3.21e-02 | 0.391 | 0.062 | 442 | 0.245 | 0/0 | 2/0 | 0/0 |
| 4 | 0.3346 | 0.2109 | 1.59 | 3.86e-02 | 0.623 | 0.269 | 670 | 0.186 | 0/0 | 0/0 | 0/0 |
| 5 | 0.3232 | 0.2109 | 1.53 | 6.43e-02 | 0.406 | 0.209 | 84 | 0.681 | 0/0 | 0/0 | 0/0 |
| 6 | 0.3178 | 0.2108 | 1.51 | 6.67e-02 | 0.210 | 0.003 | 5218 | 0.050 | 0/0 | 0/0 | 2/11 |
| 7 | 0.3165 | 0.2107 | 1.50 | 6.89e-02 | 0.422 | 0.106 | 27 | 0.809 | 0/0 | 0/0 | 0/0 |
| 8 | 0.3100 | 0.2107 | 1.47 | 7.07e-02 | 0.161 | 0.006 | 323 | 0.325 | 0/0 | 0/0 | 0/0 |
| 9 | 0.3052 | 0.2106 | 1.45 | 8.11e-02 | 0.193 | 0.070 | 377 | 0.308 | 0/0 | 0/0 | 0/0 |
| 10 | 0.3039 | 0.2106 | 1.44 | 7.84e-02 | 0.100 | 0.001 | 116 | 0.524 | 0/0 | 0/0 | 0/1 |
| 11 | 0.2998 | 0.2105 | 1.42 | 7.62e-02 | 0.094 | 0.010 | 934 | 0.175 | 0/0 | 0/0 | 0/0 |
| 12 | 0.2990 | 0.2104 | 1.42 | 8.51e-02 | 0.223 | 0.069 | 513 | 0.235 | 0/0 | 0/0 | 0/0 |
| 13 | 0.2968 | 0.2104 | 1.41 | 8.86e-02 | 0.116 | 0.057 | 1148 | 0.149 | 0/0 | 0/0 | 0/0 |
| 14 | 0.2960 | 0.2103 | 1.41 | 8.69e-02 | 0.139 | 0.022 | 1462 | 0.120 | 0/0 | 0/0 | 0/0 |
| 15 | 0.2957 | 0.2103 | 1.41 | 9.19e-02 | 0.143 | 0.057 | 353 | 0.233 | 0/0 | 0/0 | 0/0 |
| 16 | 0.2926 | 0.2103 | 1.39 | 9.11e-02 | 0.173 | 0.068 | 1027 | 0.161 | 0/0 | 0/0 | 0/0 |
| 17 | 0.2918 | 0.2102 | 1.39 | 9.36e-02 | 0.146 | 0.066 | 1399 | 0.134 | 0/0 | 0/0 | 0/0 |
| 18 | 0.2917 | 0.2101 | 1.39 | 9.40e-02 | 0.119 | 0.033 | 950 | 0.171 | 0/0 | 0/0 | 0/0 |
| 19 | 0.2910 | 0.2101 | 1.38 | 8.82e-02 | 0.192 | 0.045 | 1106 | 0.149 | 0/0 | 0/0 | 0/0 |
| 20 | 0.2894 | 0.2100 | 1.38 | 8.99e-02 | 0.181 | 0.067 | 1013 | 0.159 | 0/0 | 0/0 | 0/0 |
| 21 | 0.2891 | 0.2100 | 1.38 | 9.59e-02 | 0.205 | 0.060 | 681 | 0.217 | 0/0 | 0/0 | 0/0 |
| 22 | 0.2880 | 0.2100 | 1.37 | 9.97e-02 | 0.149 | 0.060 | 1244 | 0.147 | 0/0 | 0/0 | 0/0 |
| 23 | 0.2871 | 0.2100 | 1.37 | 9.08e-02 | 0.191 | 0.098 | 1937 | 0.102 | 0/0 | 0/0 | 0/0 |
| 24 | 0.2866 | 0.2099 | 1.37 | 9.03e-02 | 0.109 | 0.034 | 1962 | 0.101 | 0/0 | 0/0 | 0/0 |
| 25 | 0.2861 | 0.2098 | 1.36 | 9.22e-02 | 0.126 | 0.045 | 1429 | 0.127 | 0/0 | 0/0 | 0/0 |
| 26 | 0.2849 | 0.2098 | 1.36 | 8.96e-02 | 0.162 | 0.056 | 1506 | 0.122 | 0/0 | 0/0 | 0/0 |
| 27 | 0.2845 | 0.2097 | 1.36 | 8.98e-02 | 0.186 | 0.062 | 1355 | 0.140 | 0/0 | 0/0 | 0/0 |
| 28 | 0.2841 | 0.2097 | 1.35 | 8.44e-02 | 0.146 | 0.036 | 1643 | 0.121 | 0/0 | 0/0 | 0/0 |
| 29 | 0.2827 | 0.2097 | 1.35 | 9.40e-02 | 0.073 | 0.070 | 1782 | 0.113 | 0/0 | 0/0 | 0/0 |
| 30 | 0.2823 | 0.2096 | 1.35 | 8.92e-02 | 0.105 | 0.037 | 1981 | 0.102 | 0/0 | 0/0 | 0/0 |
| 31 | 0.2820 | 0.2096 | 1.35 | 9.63e-02 | 0.102 | 0.027 | 3187 | 0.075 | 0/0 | 0/0 | 0/0 |
| 32 | 0.2814 | 0.2095 | 1.34 | 9.22e-02 | 0.148 | 0.042 | 2850 | 0.072 | 0/0 | 0/0 | 0/0 |
| 33 | 0.2807 | 0.2095 | 1.34 | 9.28e-02 | 0.106 | 0.037 | 3046 | 0.074 | 0/0 | 0/0 | 0/6 |
| 34 | 0.2801 | 0.2094 | 1.34 | 9.11e-02 | 0.085 | 0.023 | 3284 | 0.069 | 0/0 | 0/0 | 0/0 |
| 35 | 0.2796 | 0.2094 | 1.34 | 9.54e-02 | 0.141 | 0.045 | 3214 | 0.071 | 0/0 | 0/0 | 0/0 |
| 36 | 0.2792 | 0.2093 | 1.33 | 9.08e-02 | 0.126 | 0.040 | 3536 | 0.067 | 0/0 | 0/0 | 0/0 |
| 37 | 0.2789 | 0.2093 | 1.33 | 9.12e-02 | 0.109 | 0.034 | 2786 | 0.079 | 0/0 | 0/0 | 0/0 |
| 38 | 0.2784 | 0.2093 | 1.33 | 9.30e-02 | 0.108 | 0.047 | 2971 | 0.076 | 0/0 | 0/0 | 9/0 |
| 39 | 0.2780 | 0.2092 | 1.33 | 9.23e-02 | 0.059 | 0.037 | 2952 | 0.081 | 0/0 | 0/0 | 0/0 |
| 40 | 0.2774 | 0.2091 | 1.33 | 9.19e-02 | 0.097 | 0.046 | 2936 | 0.076 | 0/0 | 0/0 | 0/0 |

## Mode poles

### Mode 1 positive

1. *Hai Miiko! 3* — Ono Eriko (loading 0.24287, n=134)
2. *Hai Miiko! 6* — Ono Eriko (loading 0.23734, n=132)
3. *Hai Miiko! 4* — Ono Eriko (loading 0.23029, n=133)
4. *Hai, Miiko! Vol. 2* — Ono Eriko (loading 0.22883, n=131)
5. *Hai Miiko! 18* — Ono Eriko (loading 0.22652, n=114)
6. *Hai, Miiko! 15* — Ono Eriko (loading 0.21506, n=112)
7. *Hai, Miiko! 14* — Ono Eriko (loading 0.21374, n=106)
8. *Hai Miiko! 7* — Ono Eriko (loading 0.21179, n=119)
9. *Hai, Miiko! 12* — Ono Eriko (loading 0.21045, n=132)
10. *Hai, Miiko! 16* — Ono Eriko (loading 0.18686, n=130)
11. *Hai Miiko! 5* — Ono Eriko (loading 0.18464, n=126)
12. *Hai, Miiko! Vol. 20* — Ono Eriko (loading 0.17487, n=100)

### Mode 1 negative

1. *Shit Happens: Gue yang Ogah Kawin, Kok Lo yang Rese?!* — Christian Simamora (loading 0.06093, n=204)
2. *Tangkaplah Daku, Kau Kujitak!* — Hilman Hariwijaya (loading 0.06060, n=589)
3. *Miss Cupid* — Mia Arsjad (loading 0.06015, n=123)
4. *Perhaps You: Hanya Cinta yang Bisa* — Stephanie Zen (loading 0.05673, n=171)
5. *Big Brother Complex* — Primadonna Angela (loading 0.05648, n=149)
6. *Kintaholic (Belanglicious #2)* — Primadonna Angela (loading 0.05478, n=103)
7. *Three Days Cinderella* — Agnes Jessica (loading 0.05230, n=211)
8. *Fairish* — Esti Kinasih (loading 0.05207, n=813)
9. *Poconggg Juga Pocong* — @poconggg (loading 0.04883, n=369)
10. *Cinta Brontosaurus* — Raditya Dika (loading 0.04868, n=971)
11. *Beautiful Mistake* — Sefryana Khairil (loading 0.04849, n=145)
12. *Beauty and The Best* — Luna Torashyngu (loading 0.04594, n=209)

### Mode 2 positive

1. *দীপু নাম্বার টু* — Muhammed Zafar Iqbal (loading 0.13328, n=356)
2. *একাত্তরের দিনগুলি* — Jahanara Imam (loading 0.12294, n=198)
3. *শঙ্কু সমগ্র* — Satyajit Ray (loading 0.11759, n=294)
4. *আগুনের পরশমণি* — Humayun Ahmed (loading 0.10144, n=183)
5. *জোছনা ও জননীর গল্প* — Humayun Ahmed (loading 0.10083, n=304)
6. *রূপালী মাকড়সা (তিন গোয়েন্দা, #৩)* — Rakib Hassan (loading 0.09793, n=136)
7. *Rashed, My Friend* — Muhammed Zafar Iqbal (loading 0.09427, n=254)
8. *Pather panchali: Song of the road* — Bibhutibhushan Bandyopadhyay (loading 0.09301, n=440)
9. *হাজার বছর ধরে* — Zahir Raihan (loading 0.09196, n=294)
10. *The Complete Adventures of Feluda, Vol. 1* — Satyajit Ray (loading 0.09096, n=530)
11. *শঙ্খনীল কারাগার* — Humayun Ahmed (loading 0.08893, n=320)
12. *প্রথম আলো ১* — Sunil Gangopadhyay (loading 0.08846, n=212)

### Mode 2 negative

1. *হিমু এবং হার্ভার্ড Ph.D. বল্টু ভাই (হিমু, #21)* — Humayun Ahmed (loading 0.15756, n=156)
2. *হিমু এবং একটি রাশিয়ান পরী (হিমু, #20)* — Humayun Ahmed (loading 0.15040, n=138)
3. *হলুদ হিমু কালো র‍্যাব (হিমু, #14)* — Humayun Ahmed (loading 0.14381, n=273)
4. *আঙ্গুল কাটা জগলু (হিমু, #13)* — Humayun Ahmed (loading 0.13384, n=176)
5. *আজ হিমুর বিয়ে (হিমু, #15)* — Humayun Ahmed (loading 0.13284, n=272)
6. *বিপদ (মিসির আলি, #7)* — Humayun Ahmed (loading 0.13049, n=117)
7. *এবং হিমু ... (হিমু, #5)* — Humayun Ahmed (loading 0.12767, n=176)
8. *হিমুর আছে জল (হিমু, #19)* — Humayun Ahmed (loading 0.12740, n=126)
9. *একজন হিমু কয়েকটি ঝিঁ ঝিঁ পোকা (হিমু, #9)* — Humayun Ahmed (loading 0.12731, n=190)
10. *হিমু রিমান্ডে (হিমু, #16)* — Humayun Ahmed (loading 0.12518, n=216)
11. *আজ চিত্রার বিয়ে* — Humayun Ahmed (loading 0.12208, n=145)
12. *লিলুয়া বাতাস* — Humayun Ahmed (loading 0.11977, n=149)

### Mode 3 positive

1. *ثلاثية غرناطة* — Radwa Ashour (loading 0.13983, n=6,061)
2. *الطنطورية* — Radwa Ashour (loading 0.12019, n=3,142)
3. *ساق البامبو* — s`wd lsn`wsy (loading 0.10339, n=7,228)
4. *رباعيات صلاح جاهين* — SlH jhyn (loading 0.09246, n=2,045)
5. *لا تصالح* — 'ml dnql (loading 0.09119, n=898)
6. *الحرافيش* — Naguib Mahfouz (loading 0.08629, n=2,008)
7. *الرحيق المختوم* — Safiy al-Rahman al-Mubarakfuri (loading 0.08232, n=2,335)
8. *عزازيل* — ywsf zydn (loading 0.08208, n=7,420)
9. *الإسلام بين الشرق والغرب* — Alija Izetbegovic (loading 0.08067, n=1,500)
10. *عائد إلى حيفا* — Gsn knfny (loading 0.07756, n=2,520)
11. *ويسترن يونيون فرع الهرم: ديوان بالعامية المصرية* — mSTf~ brhym (loading 0.07609, n=1,047)
12. *زمن الخيول البيضاء* — Ibrahim Nasrallah - ibrhym nSr llh (loading 0.07575, n=1,322)

### Mode 3 negative

1. *28 حرف* — 'Hmd Hlmy (loading 0.08503, n=2,862)
2. *نيكروفيليا* — shyryn hny'y (loading 0.08182, n=1,581)
3. *ليتها تقرأ* — khld lbtly (loading 0.07504, n=1,995)
4. *السنجة* — 'Hmd khld twfyq (loading 0.06889, n=1,991)
5. *ظل الأفعى* — ywsf zydn (loading 0.06730, n=2,383)
6. *شيكاجو* — Alaa Al Aswany (loading 0.06052, n=3,195)
7. *الرجال من بولاق والنساء من أول فيصل* — yhb m`wD (loading 0.06004, n=1,103)
8. *نادي السيارات* — Alaa Al Aswany (loading 0.05919, n=1,821)
9. *مالك* — mHmwd bkry (loading 0.05826, n=910)
10. *في ديسمبر تنتهي كل الأحلام* — 'thyr `bdllh lnshmy (loading 0.05370, n=2,807)
11. *علشان السناره تغمز: كلام لازم كل البنات تعرفه* — 'ml mHmwd (loading 0.05241, n=503)
12. *The Mask of Gold* — Alan A. McLean (loading 0.05139, n=429)

### Mode 4 positive

1. *Neil's Guardian Angel (Cattle Valley, #17)* — Carol Lynne (loading 0.08514, n=135)
2. *Physical Therapy (Cattle Valley, #5)* — Carol Lynne (loading 0.08276, n=201)
3. *Cattle Valley Mistletoe (Cattle Valley, #2)* — Carol Lynne (loading 0.07795, n=210)
4. *Tater's Bear (Brac Pack #22)* — Lynn Hagen (loading 0.07527, n=166)
5. *By the Light of the Moon (Moonlight Breed #2)* — Gabrielle Evans (loading 0.07337, n=131)
6. *Bent - Not Broken (Cattle Valley, #13)* — Carol Lynne (loading 0.07171, n=132)
7. *Forbidden Desires (Tri-Omega Mates #2)* — Stormy Glenn (loading 0.06938, n=186)
8. *Broken Pottery (Campus Cravings, #6)* — Carol Lynne (loading 0.06908, n=150)
9. *Secret Desires (Tri-Omega Mates #1)* — Stormy Glenn (loading 0.06744, n=226)
10. *Coach (Campus Cravings, #1)* — Carol Lynne (loading 0.06648, n=233)
11. *The Sound of White  (Cattle Valley, #8)* — Carol Lynne (loading 0.06632, n=176)
12. *Cowboy Easy (Blaecleah Brothers #1)* — Stormy Glenn (loading 0.06533, n=182)

### Mode 4 negative

1. *Midnight (Dance with the Devil, #3)* — Megan Derr (loading 0.06238, n=149)
2. *Dance in the Dark (Dance with the Devil, #2)* — Megan Derr (loading 0.05927, n=213)
3. *Bloodlines (Infected, #2)* — Andrea Speed (loading 0.05859, n=166)
4. *Houseboat on the Nile (Spy vs. Spook, #1)* — Tinnean (loading 0.05318, n=179)
5. *I'll Be Your Drill, Soldier* — Crystal Rose (loading 0.05146, n=558)
6. *Conquest (Conquest, #1)* — S.J. Frost (loading 0.05133, n=265)
7. *American Love Songs* — Ashlyn Kane (loading 0.05118, n=418)
8. *Life in Fusion (Summit City, #2)* — Ethan Day (loading 0.05022, n=184)
9. *Tigers and Devils (Tigers and Devils #1)* — Sean Kennedy (loading 0.04999, n=841)
10. *Clear Water* — Amy Lane (loading 0.04884, n=519)
11. *Bareback (Bareback, #1)* — Chris Owen (loading 0.04867, n=516)
12. *Who We Are (Bear, Otter, and the Kid, #2)* — T.J. Klune (loading 0.04853, n=659)

### Mode 5 positive

1. *Hai, Miiko! Vol. 20* — Ono Eriko (loading 0.08653, n=100)
2. *Hai Miiko! 1* — Ono Eriko (loading 0.08587, n=203)
3. *Hai, Miiko! 14* — Ono Eriko (loading 0.07768, n=106)
4. *Hai Miiko! 3* — Ono Eriko (loading 0.07553, n=134)
5. *Hai Miiko! 18* — Ono Eriko (loading 0.06748, n=114)
6. *Hai, Miiko! 15* — Ono Eriko (loading 0.06713, n=112)
7. *Hai Miiko! 6* — Ono Eriko (loading 0.06674, n=132)
8. *Hai Miiko! 4* — Ono Eriko (loading 0.06260, n=133)
9. *Hai, Miiko! 12* — Ono Eriko (loading 0.06213, n=132)
10. *Hai Miiko! 7* — Ono Eriko (loading 0.06167, n=119)
11. *Hai, Miiko! Vol. 2* — Ono Eriko (loading 0.05716, n=131)
12. *Hai Miiko! 5* — Ono Eriko (loading 0.05547, n=126)

### Mode 5 negative

1. *名探偵コナン 29 (Detective Conan #29)* — Gosho Aoyama (loading 0.18955, n=223)
2. *名探偵コナン 46 (Detective Conan #46)* — Gosho Aoyama (loading 0.15798, n=130)
3. *Detektif Conan Vol. 49* — Gosho Aoyama (loading 0.15743, n=130)
4. *名探偵コナン 27 (Detective Conan #27)* — Gosho Aoyama (loading 0.15422, n=220)
5. *名探偵コナン 21 (Detective Conan #21)* — Gosho Aoyama (loading 0.15169, n=251)
6. *Case Closed, Vol. 10* — Gosho Aoyama (loading 0.14931, n=296)
7. *Case Closed, Vol. 14* — Gosho Aoyama (loading 0.14616, n=197)
8. *Case Closed, Vol. 12* — Gosho Aoyama (loading 0.14329, n=176)
9. *Case Closed, Vol. 8* — Gosho Aoyama (loading 0.14159, n=326)
10. *名探偵コナン 24 (Detective Conan #24)* — Gosho Aoyama (loading 0.14149, n=226)
11. *Case Closed, Vol. 18* — Gosho Aoyama (loading 0.13997, n=228)
12. *Detektif Conan Vol. 53* — Gosho Aoyama (loading 0.13709, n=104)

### Mode 6 positive

1. *Coach (Breeding, #1)* — Alexa Riley (loading 0.03300, n=1,113)
2. *Mechanic (Breeding, #2)* — Alexa Riley (loading 0.03289, n=1,245)
3. *X/1999, Volume 18: Inversion* — CLAMP (loading 0.03236, n=121)
4. *X/1999, Volume 08: Crescendo* — CLAMP (loading 0.03227, n=140)
5. *The Last Boyfriend (Forever Love, #1)* — J.S. Cooper (loading 0.03148, n=1,788)
6. *X/1999, Volume 04: Intermezzo* — CLAMP (loading 0.03122, n=166)
7. *Storm (Storm MC, #1)* — Nina  Levine (loading 0.03116, n=1,949)
8. *X/1999, Volume 14: Concerto* — CLAMP (loading 0.03090, n=125)
9. *X/1999, Volume 06: Duet* — CLAMP (loading 0.03044, n=153)
10. *Honor Student (Honor, #1)* — Teresa Mummert (loading 0.03030, n=2,021)
11. *One Night Stand (One Night Stand, #1)* — J.S. Cooper (loading 0.03000, n=1,233)
12. *X/1999, Volume 07: Rhapsody* — CLAMP (loading 0.02861, n=152)

### Mode 6 negative

1. *Angelic Layer, Vol. 4 (Angelic Layer, #4)* — CLAMP (loading 0.04709, n=135)
2. *Angelic Layer, Vol. 3 (Angelic Layer, #3)* — CLAMP (loading 0.04679, n=137)
3. *Angelic Layer, Vol. 2 (Angelic Layer, #2)* — CLAMP (loading 0.04511, n=148)
4. *Angelic Layer, Vol. 5 (Angelic Layer, #5)* — CLAMP (loading 0.04105, n=134)
5. *Angelic Layer, Vol. 1 (Angelic Layer, #1)* — CLAMP (loading 0.03898, n=279)
6. *Hopeless (Hopeless, #1)* — Colleen Hoover (loading 0.03771, n=24,016)
7. *Archer's Voice* — Mia Sheridan (loading 0.03687, n=8,304)
8. *Crashed (Driven, #3)* — K. Bromberg (loading 0.03408, n=4,081)
9. *Fueled (Driven, #2)* — K. Bromberg (loading 0.03314, n=4,567)
10. *Motorcycle Man (Dream Man, #4)* — Kristen Ashley (loading 0.03196, n=6,027)
11. *Rock Chick Regret (Rock Chick, #7)* — Kristen Ashley (loading 0.03191, n=3,552)
12. *Sweet Dreams (Colorado Mountain, #2)* — Kristen Ashley (loading 0.03152, n=4,923)

### Mode 7 positive

1. *X/1999, Volume 08: Crescendo* — CLAMP (loading 0.21204, n=140)
2. *X/1999, Volume 18: Inversion* — CLAMP (loading 0.20960, n=121)
3. *X/1999, Volume 04: Intermezzo* — CLAMP (loading 0.19929, n=166)
4. *X/1999, Volume 06: Duet* — CLAMP (loading 0.19706, n=153)
5. *X/1999, Volume 14: Concerto* — CLAMP (loading 0.19147, n=125)
6. *X/1999, Volume 07: Rhapsody* — CLAMP (loading 0.18347, n=152)
7. *X/1999, Volume 17: Suite* — CLAMP (loading 0.18344, n=118)
8. *X/1999, Volume 03: Sonata* — CLAMP (loading 0.16282, n=183)
9. *Natsume's Book of Friends, Vol. 3* — Yuki Midorikawa (loading 0.13674, n=134)
10. *The Tyrant Falls in Love, Volume 5* — Hinako Takanaga (loading 0.13403, n=108)
11. *A Drunken Dream and Other Stories* — Moto Hagio (loading 0.12331, n=115)
12. *Verliebter Tyrann 4* — Hinako Takanaga (loading 0.12097, n=108)

### Mode 7 negative

1. *Angelic Layer, Vol. 4 (Angelic Layer, #4)* — CLAMP (loading 0.28510, n=135)
2. *Angelic Layer, Vol. 3 (Angelic Layer, #3)* — CLAMP (loading 0.27984, n=137)
3. *Angelic Layer, Vol. 2 (Angelic Layer, #2)* — CLAMP (loading 0.26482, n=148)
4. *Angelic Layer, Vol. 5 (Angelic Layer, #5)* — CLAMP (loading 0.23721, n=134)
5. *Angelic Layer, Vol. 1 (Angelic Layer, #1)* — CLAMP (loading 0.23550, n=279)
6. *Nodame Cantabile, Vol. 3 (Nodame Cantabile, #3)* — Tomoko Ninomiya (loading 0.04749, n=122)
7. *Mahadewa Mahadewi* — Nova Riyanti Yusuf (loading 0.04730, n=109)
8. *Nodame Cantabile, Vol. 4 (Nodame Cantabile, #4)* — Tomoko Ninomiya (loading 0.04384, n=131)
9. *Suki: A like story, Vol. 01 (Suki, #1)* — CLAMP (loading 0.02811, n=131)
10. *Ai Yori Aoshi, Vol. 1* — Kou Fumizuki (loading 0.02798, n=151)
11. *Jangan Main-Main* — Djenar Maesa Ayu (loading 0.02714, n=360)
12. *Five Have a Wonderful Time (Famous Five, #11)* — Enid Blyton (loading 0.02028, n=953)

### Mode 8 positive

1. *Dengeki Daisy, Vol. 08 (Dengeki Daisy, #8)* — Kyousuke Motomi (loading 0.04585, n=481)
2. *Inferno (Play to Live #4)* — D. Rus (loading 0.04363, n=226)
3. *달빛 조각사 2 (The Legendary Moonlight Sculptor, #2)* — Heesung Nam (loading 0.04347, n=106)
4. *Boys Over Flowers: Hana Yori Dango, Vol. 23 (Boys Over Flowers, #23)* — Yoko Kamio (loading 0.03980, n=167)
5. *Berjuta Rasanya* — Tere Liye (loading 0.03800, n=638)
6. *Boys Over Flowers: Hana Yori Dango, Vol. 26 (Boys Over Flowers, #26)* — Yoko Kamio (loading 0.03360, n=170)
7. *Boys Over Flowers: Hana Yori Dango, Vol. 21 (Boys Over Flowers, #21)* — Yoko Kamio (loading 0.03333, n=176)
8. *Bleach―ブリーチ― 65 [Burīchi 65] (Bleach, #65)* — Tite Kubo (loading 0.03255, n=130)
9. *InuYasha: A Question of Time (InuYasha, #37)* — Rumiko Takahashi (loading 0.03007, n=174)
10. *InuYasha: A Mountain That Lives (InuYasha, #34)* — Rumiko Takahashi (loading 0.02849, n=174)
11. *花より男子 34 [Hana Yori Dango] (Boys Over Flowers, #34)* — Yoko Kamio (loading 0.02801, n=145)
12. *Bleach―ブリーチ― 62 [Burīchi 62] (Bleach, #62)* — Tite Kubo (loading 0.02740, n=166)

### Mode 8 negative

1. *Naruto, Vol. 07: Orochimaru's Curse (Naruto, #7)* — Masashi Kishimoto (loading 0.11324, n=939)
2. *Naruto, Vol. 21: Pursuit (Naruto, #21)* — Masashi Kishimoto (loading 0.10809, n=686)
3. *Naruto, Vol. 26: Awakening (Naruto, #26)* — Masashi Kishimoto (loading 0.10360, n=680)
4. *Naruto, Vol. 15: Naruto's Ninja Handbook! (Naruto, #15)* — Masashi Kishimoto (loading 0.09241, n=742)
5. *Naruto, Vol. 10: A Splendid Ninja (Naruto, #10)* — Masashi Kishimoto (loading 0.09240, n=829)
6. *Naruto, Vol. 12: The Great Flight (Naruto, #12)* — Masashi Kishimoto (loading 0.09111, n=807)
7. *Naruto, Vol. 08: Life-and-Death Battles (Naruto, #8)* — Masashi Kishimoto (loading 0.09009, n=865)
8. *Naruto, Vol. 05: Exam Hell (Naruto, #5)* — Masashi Kishimoto (loading 0.08950, n=1,129)
9. *Naruto, Vol. 30: Puppet Masters (Naruto, #30)* — Masashi Kishimoto (loading 0.08888, n=629)
10. *One Piece, Volume 17: Hiriluk's Cherry Blossoms (One Piece, #17)* — Eiichiro Oda (loading 0.08777, n=444)
11. *Naruto, Vol. 34: The Reunion (Naruto, #34)* — Masashi Kishimoto (loading 0.08756, n=570)
12. *Träume (One Piece, #24)* — Eiichiro Oda (loading 0.08688, n=339)

### Mode 9 positive

1. *20th Century Boys, Band 12 (20th Century Boys, #12)* — Naoki Urasawa (loading 0.11109, n=216)
2. *20th Century Boys, Band 14 (20th Century Boys, #14)* — Naoki Urasawa (loading 0.10332, n=210)
3. *20th Century Boys, Band 11 (20th Century Boys, #11)* — Naoki Urasawa (loading 0.10184, n=213)
4. *20th Century Boys, Band 15 (20th Century Boys, #15)* — Naoki Urasawa (loading 0.10134, n=206)
5. *20th Century Boys, Band 2 (20th Century Boys, #2)* — Naoki Urasawa (loading 0.09659, n=351)
6. *20th Century Boys, Band 10 (20th Century Boys, #10)* — Naoki Urasawa (loading 0.09316, n=241)
7. *20th Century Boys, Band 9 (20th Century Boys, #9)* — Naoki Urasawa (loading 0.09086, n=227)
8. *20th Century Boys, Band 18 (20th Century Boys, #18)* — Naoki Urasawa (loading 0.08971, n=190)
9. *20th Century Boys, Band 5 (20th Century Boys, #5)* — Naoki Urasawa (loading 0.08939, n=273)
10. *20th Century Boys, 19 (20th Century Boys, #19)* — Naoki Urasawa (loading 0.08605, n=202)
11. *20th Century Boys, Band 7 (20th Century Boys, #7)* — Naoki Urasawa (loading 0.08300, n=245)
12. *20th Century Boys, Band 13 (20th Century Boys, #13)* — Naoki Urasawa (loading 0.07960, n=215)

### Mode 9 negative

1. *Dragon Ball, Vol. 15: The Titanic Tournament (Dragon Ball, #15)* — Akira Toriyama (loading 0.08404, n=179)
2. *Is og ild (Sagaen om Isfolket, #28)* — Margit Sandemo (loading 0.08065, n=114)
3. *Dragon Ball Z, Vol. 13: The Red Ribbon Androids (Dragon Ball Z, #13)* — Akira Toriyama (loading 0.08063, n=124)
4. *Dragon Ball, Vol. 13: Piccolo Conquers the World (Dragon Ball, #13)* — Akira Toriyama (loading 0.08046, n=184)
5. *Djevlekløften (Sagaen om Isfolket, #21)* — Margit Sandemo (loading 0.07991, n=119)
6. *Den onde arven (Sagaen om Isfolket, #6)* — Margit Sandemo (loading 0.07578, n=187)
7. *Dragon Ball, Vol. 12: The Demon King Piccolo (Dragon Ball, #12)* — Akira Toriyama (loading 0.07577, n=190)
8. *Dragon Ball, Vol. 16: Goku vs. Piccolo (Dragon Ball, #16)* — Akira Toriyama (loading 0.07547, n=188)
9. *Vinden fra øst (Sagaen om Isfolket, #15)* — Margit Sandemo (loading 0.07476, n=130)
10. *Kvinnen på stranden (Sagaen om Isfolket, #34)* — Margit Sandemo (loading 0.07440, n=103)
11. *Dragon Ball, Vol. 14: Heaven and Earth (Dragon Ball, #14)* — Akira Toriyama (loading 0.07315, n=183)
12. *Skandalen (Sagaen om Isfolket, #27)* — Margit Sandemo (loading 0.07301, n=111)

### Mode 10 positive

1. *Is og ild (Sagaen om Isfolket, #28)* — Margit Sandemo (loading 0.16548, n=114)
2. *Djevlekløften (Sagaen om Isfolket, #21)* — Margit Sandemo (loading 0.16469, n=119)
3. *Den onde arven (Sagaen om Isfolket, #6)* — Margit Sandemo (loading 0.15545, n=187)
4. *Vinden fra øst (Sagaen om Isfolket, #15)* — Margit Sandemo (loading 0.15210, n=130)
5. *Kvinnen på stranden (Sagaen om Isfolket, #34)* — Margit Sandemo (loading 0.15106, n=103)
6. *Skandalen (Sagaen om Isfolket, #27)* — Margit Sandemo (loading 0.14907, n=111)
7. *Den ensomme (Sagaen om Isfolket, #9)* — Margit Sandemo (loading 0.14444, n=145)
8. *Spøkelsesslottet (Sagaen om Isfolket, #7)* — Margit Sandemo (loading 0.14154, n=180)
9. *Det svarte vannet (Sagaen om Isfolket, #46)* — Margit Sandemo (loading 0.13909, n=101)
10. *Engel med svarte vinger (Sagaen om Isfolket, #25)* — Margit Sandemo (loading 0.13746, n=117)
11. *Fergemannen (Sagaen om Isfolket, #31)* — Margit Sandemo (loading 0.13328, n=111)
12. *Nattens demon (Sagaen om Isfolket, #33)* — Margit Sandemo (loading 0.13064, n=125)

### Mode 10 negative

1. *Broken Fortress (Rifter #6)* — Ginn Hale (loading 0.05259, n=117)
2. *Enemies & Shadows (Rifter #7)* — Ginn Hale (loading 0.05035, n=114)
3. *Witches' Blood (Rifter #4)* — Ginn Hale (loading 0.04997, n=128)
4. *Chobits, Vol. 7* — CLAMP (loading 0.04171, n=651)
5. *Chobits, Vol. 4* — CLAMP (loading 0.03935, n=733)
6. *The Iron Temple (Rifter, #9)* — Ginn Hale (loading 0.03476, n=105)
7. *Volley Balls  (Balls to the Wall #1)* — Tara Lain (loading 0.03444, n=133)
8. *Boży bojownicy (Trylogia husycka, #2)* — Andrzej Sapkowski (loading 0.03363, n=266)
9. *The Divan* — Hafez (loading 0.03352, n=867)
10. *A Day Makes (The Vault, #1)* — Mary Calmes (loading 0.03334, n=114)
11. *When the Dust Settles (Timing, #3)* — Mary Calmes (loading 0.03307, n=127)
12. *Bodyguard To A Sex God (Bodyguards Inc. #1)* — R.J. Scott (loading 0.03103, n=154)

### Mode 11 positive

1. *Naruto, Vol. 07: Orochimaru's Curse (Naruto, #7)* — Masashi Kishimoto (loading 0.06652, n=939)
2. *Naruto, Vol. 09: Turning the Tables (Naruto, #9)* — Masashi Kishimoto (loading 0.05786, n=886)
3. *Naruto, Vol. 21: Pursuit (Naruto, #21)* — Masashi Kishimoto (loading 0.05679, n=686)
4. *Naruto, Vol. 10: A Splendid Ninja (Naruto, #10)* — Masashi Kishimoto (loading 0.05354, n=829)
5. *Naruto, Vol. 05: Exam Hell (Naruto, #5)* — Masashi Kishimoto (loading 0.05177, n=1,129)
6. *Naruto, Vol. 15: Naruto's Ninja Handbook! (Naruto, #15)* — Masashi Kishimoto (loading 0.05135, n=742)
7. *Never Trust a Pirate (Playful Brides, #7)* — Valerie Bowman (loading 0.05131, n=100)
8. *Naruto, Vol. 17: Itachi's Power (Naruto, #17)* — Masashi Kishimoto (loading 0.05117, n=725)
9. *Naruto, Vol. 28: Homecoming (Naruto, #28)* — Masashi Kishimoto (loading 0.04748, n=667)
10. *Naruto, Vol. 12: The Great Flight (Naruto, #12)* — Masashi Kishimoto (loading 0.04707, n=807)
11. *Naruto, Vol. 26: Awakening (Naruto, #26)* — Masashi Kishimoto (loading 0.04696, n=680)
12. *Naruto, Vol. 24: Unorthodox (Naruto, #24)* — Masashi Kishimoto (loading 0.04607, n=653)

### Mode 11 negative

1. *Nana, Vol. 11 (Nana, #11)* — Ai Yazawa (loading 0.09213, n=386)
2. *Nana, Vol. 9 (Nana, #9)* — Ai Yazawa (loading 0.08582, n=407)
3. *Nana, Vol. 14 (Nana, #14)* — Ai Yazawa (loading 0.08381, n=357)
4. *Nana, Vol. 5 (Nana, #5)* — Ai Yazawa (loading 0.08213, n=538)
5. *Nana, Vol. 20 (Nana, #20)* — Ai Yazawa (loading 0.08156, n=278)
6. *Nana, Vol. 6 (Nana, #6)* — Ai Yazawa (loading 0.08137, n=496)
7. *Nana, Vol. 13 (Nana, #13)* — Ai Yazawa (loading 0.07841, n=359)
8. *Nana 16 (Nana, #16)* — Ai Yazawa (loading 0.07461, n=333)
9. *Nana, Vol. 10 (Nana, #10)* — Ai Yazawa (loading 0.07431, n=395)
10. *Nana, Vol. 19 (Nana, #19)* — Ai Yazawa (loading 0.07402, n=295)
11. *Nana, Vol. 18 (Nana, #18)* — Ai Yazawa (loading 0.07344, n=316)
12. *Nana 15* — Ai Yazawa (loading 0.06813, n=327)

### Mode 12 positive

1. *Nothing Special (Nothing Special, #1)* — A.E. Via (loading 0.07044, n=377)
2. *Bitter Kind of Love (Prairie Devils MC #5)* — Nicole Snow (loading 0.06940, n=117)
3. *His Imperfect Mate (Brac Pack #26)* — Lynn Hagen (loading 0.06749, n=153)
4. *Faking It (Metropolis, #1)* — Riley Hart (loading 0.06424, n=206)
5. *Lessons Learned (Assassin/Shifter, #19)* — Sandrine Gasq-Dion (loading 0.06165, n=129)
6. *After the Fire (Through Hell and Back, #2)* — Felice Stevens (loading 0.06148, n=106)
7. *Not a Game (Friends, #1)* — Cardeno C. (loading 0.06008, n=133)
8. *Love Means... Family (Farm, #5)* — Andrew  Grey (loading 0.05853, n=132)
9. *The Best Revenge (Bottled Up, #2)* — Andrew  Grey (loading 0.05762, n=109)
10. *The Weight of It All* — N.R. Walker (loading 0.05614, n=370)
11. *A Serving of Love (Of Love, #2)* — Andrew  Grey (loading 0.05608, n=145)
12. *Unspoken* — Brenda Rothert (loading 0.05587, n=142)

### Mode 12 negative

1. *When the Dust Settles (Timing, #3)* — Mary Calmes (loading 0.11721, n=127)
2. *Bodyguard To A Sex God (Bodyguards Inc. #1)* — R.J. Scott (loading 0.11597, n=154)
3. *Volley Balls  (Balls to the Wall #1)* — Tara Lain (loading 0.11062, n=133)
4. *A Day Makes (The Vault, #1)* — Mary Calmes (loading 0.11058, n=114)
5. *The Sound of White  (Cattle Valley, #8)* — Carol Lynne (loading 0.10545, n=176)
6. *Eye of the Beholder (Cattle Valley, #11)* — Carol Lynne (loading 0.08957, n=161)
7. *Physical Therapy (Cattle Valley, #5)* — Carol Lynne (loading 0.08901, n=201)
8. *Neil's Guardian Angel (Cattle Valley, #17)* — Carol Lynne (loading 0.08763, n=135)
9. *Cattle Valley Mistletoe (Cattle Valley, #2)* — Carol Lynne (loading 0.08654, n=210)
10. *Rough Ride (Cattle Valley, #4)* — Carol Lynne (loading 0.08229, n=215)
11. *All Play and No Work (Cattle Valley, #1)* — Carol Lynne (loading 0.07948, n=278)
12. *To Service and Protect (Cattle Valley, #20)* — Carol Lynne (loading 0.07715, n=128)

### Mode 13 positive

1. *Dragon Ball Z, Vol. 13: The Red Ribbon Androids (Dragon Ball Z, #13)* — Akira Toriyama (loading 0.08626, n=124)
2. *Dragon Ball Z, Vol. 7: The Ginyu Force (Dragon Ball Z, #7)* — Akira Toriyama (loading 0.07370, n=129)
3. *Dragon Ball Z, Vol. 23: Boo Unleashed! (Dragon Ball Z, #23)* — Akira Toriyama (loading 0.07197, n=116)
4. *20th Century Boys, Band 12 (20th Century Boys, #12)* — Naoki Urasawa (loading 0.06820, n=216)
5. *Dragon Ball Z, Vol. 24: Hercule to the Rescue (Dragon Ball Z, #24)* — Akira Toriyama (loading 0.06510, n=123)
6. *Dragon Ball Z, Vol. 17: The Cell Game (Dragon Ball Z, #17)* — Akira Toriyama (loading 0.06465, n=129)
7. *Dragon Ball, Vol. 15: The Titanic Tournament (Dragon Ball, #15)* — Akira Toriyama (loading 0.06455, n=179)
8. *20th Century Boys, Band 11 (20th Century Boys, #11)* — Naoki Urasawa (loading 0.06435, n=213)
9. *Dragon Ball, Vol. 10: Return to the Tournament (Dragon Ball, #10)* — Akira Toriyama (loading 0.06264, n=192)
10. *20th Century Boys, Band 14 (20th Century Boys, #14)* — Naoki Urasawa (loading 0.05879, n=210)
11. *20th Century Boys, Band 15 (20th Century Boys, #15)* — Naoki Urasawa (loading 0.05838, n=206)
12. *Naoki Urasawa Präsentiert: Monster, Band 17: Bin wieder da (Naoki Urasawa's Monster, #17)* — Naoki Urasawa (loading 0.05721, n=235)

### Mode 13 negative

1. *The Sound of White  (Cattle Valley, #8)* — Carol Lynne (loading 0.04702, n=176)
2. *Träume (One Piece, #24)* — Eiichiro Oda (loading 0.04694, n=339)
3. *Fergemannen (Sagaen om Isfolket, #31)* — Margit Sandemo (loading 0.04464, n=111)
4. *在這裡 (One Piece, #31)* — Eiichiro Oda (loading 0.04262, n=324)
5. *Rough Ride (Cattle Valley, #4)* — Carol Lynne (loading 0.04148, n=215)
6. *One Piece, Volume 18: Ace Arrives (One Piece, #18)* — Eiichiro Oda (loading 0.04132, n=411)
7. *Eye of the Beholder (Cattle Valley, #11)* — Carol Lynne (loading 0.03975, n=161)
8. *Neil's Guardian Angel (Cattle Valley, #17)* — Carol Lynne (loading 0.03962, n=135)
9. *Bent - Not Broken (Cattle Valley, #13)* — Carol Lynne (loading 0.03928, n=132)
10. *Super Sock Man (Johnnies, #0.5, Granby Knitting, #1.5)* — Amy Lane (loading 0.03915, n=230)
11. *Sassy in Diapers (Sassy Mates, #4.3)* — Milly Taiden (loading 0.03886, n=156)
12. *The Duty of a Beta (Pack Discipline #3)* — Kim Dare (loading 0.03877, n=176)

### Mode 14 positive

1. *Volley Balls  (Balls to the Wall #1)* — Tara Lain (loading 0.07459, n=133)
2. *A Day Makes (The Vault, #1)* — Mary Calmes (loading 0.07210, n=114)
3. *Bodyguard To A Sex God (Bodyguards Inc. #1)* — R.J. Scott (loading 0.07052, n=154)
4. *When the Dust Settles (Timing, #3)* — Mary Calmes (loading 0.07019, n=127)
5. *The Divan* — Hafez (loading 0.05938, n=867)
6. *Secret Desires (Tri-Omega Mates #1)* — Stormy Glenn (loading 0.05770, n=226)
7. *Is og ild (Sagaen om Isfolket, #28)* — Margit Sandemo (loading 0.05714, n=114)
8. *Djevlekløften (Sagaen om Isfolket, #21)* — Margit Sandemo (loading 0.05685, n=119)
9. *Never Trust a Pirate (Playful Brides, #7)* — Valerie Bowman (loading 0.05380, n=100)
10. *Vinden fra øst (Sagaen om Isfolket, #15)* — Margit Sandemo (loading 0.05234, n=130)
11. *Kvinnen på stranden (Sagaen om Isfolket, #34)* — Margit Sandemo (loading 0.05221, n=103)
12. *Skandalen (Sagaen om Isfolket, #27)* — Margit Sandemo (loading 0.05102, n=111)

### Mode 14 negative

1. *بامداد خمار* — ftnh Hj sydjwdy (loading 0.04984, n=615)
2. *Bagaikan Puteri (Bagaikan Puteri, #1)* — Ramlee Awang Murshid (loading 0.04634, n=226)
3. *Claymore, Vol. 15: Genesis of War (Claymore, #15)* — Norihiro Yagi (loading 0.04612, n=210)
4. *Some Like It Scot (Scandalous Highlanders, #4)* — Suzanne Enoch (loading 0.04526, n=171)
5. *Not a Game (Friends, #1)* — Cardeno C. (loading 0.04517, n=133)
6. *Faking It (Metropolis, #1)* — Riley Hart (loading 0.04492, n=206)
7. *Bitter Kind of Love (Prairie Devils MC #5)* — Nicole Snow (loading 0.04477, n=117)
8. *Luca (Ruin & Revenge, #2)* — Sarah Castille (loading 0.04474, n=127)
9. *Claymore, Vol. 11: Kindred of Paradise (Claymore, #11)* — Norihiro Yagi (loading 0.04289, n=253)
10. *Claymore, Vol. 19: Phantoms in the Heart (Claymore, #19)* — Norihiro Yagi (loading 0.04225, n=175)
11. *Claymore, Vol. 7: Fit for Battle (Claymore, #7)* — Norihiro Yagi (loading 0.04222, n=290)
12. *Rescued (Rescued Hearts, #1)* — Felice Stevens (loading 0.03970, n=226)

### Mode 15 positive

1. *Bodyguard To A Sex God (Bodyguards Inc. #1)* — R.J. Scott (loading 0.15543, n=154)
2. *A Day Makes (The Vault, #1)* — Mary Calmes (loading 0.15423, n=114)
3. *When the Dust Settles (Timing, #3)* — Mary Calmes (loading 0.14631, n=127)
4. *Volley Balls  (Balls to the Wall #1)* — Tara Lain (loading 0.14105, n=133)
5. *Tater's Bear (Brac Pack #22)* — Lynn Hagen (loading 0.06444, n=166)
6. *Murphy's Madness (Brac Pack #15)* — Lynn Hagen (loading 0.05600, n=196)
7. *Claymore, Vol. 15: Genesis of War (Claymore, #15)* — Norihiro Yagi (loading 0.05484, n=210)
8. *Memphis (Zeus's Pack #8)* — Lynn Hagen (loading 0.05237, n=106)
9. *クレイモア 24 [Kureimoa 24] (Claymore, #24)* — Norihiro Yagi (loading 0.05114, n=118)
10. *Claymore, Vol. 19: Phantoms in the Heart (Claymore, #19)* — Norihiro Yagi (loading 0.05038, n=175)
11. *Claymore, Vol. 7: Fit for Battle (Claymore, #7)* — Norihiro Yagi (loading 0.05005, n=290)
12. *Avanti (Zeus's Pack #2)* — Lynn Hagen (loading 0.04926, n=152)

### Mode 15 negative

1. *Bitter Kind of Love (Prairie Devils MC #5)* — Nicole Snow (loading 0.09046, n=117)
2. *Not a Game (Friends, #1)* — Cardeno C. (loading 0.08850, n=133)
3. *After the Fire (Through Hell and Back, #2)* — Felice Stevens (loading 0.08145, n=106)
4. *The Sound of White  (Cattle Valley, #8)* — Carol Lynne (loading 0.07734, n=176)
5. *Unspoken* — Brenda Rothert (loading 0.07245, n=142)
6. *Neil's Guardian Angel (Cattle Valley, #17)* — Carol Lynne (loading 0.06945, n=135)
7. *Release (Fire on Ice, #5)* — Brenda Rothert (loading 0.06888, n=156)
8. *Faking It (Metropolis, #1)* — Riley Hart (loading 0.06594, n=206)
9. *Suspiciously Obedient (Obedient, #2)* — Julia Kent (loading 0.06240, n=116)
10. *Never Kiss an Outlaw (Deadly Pistols MC, #2)* — Nicole Snow (loading 0.06041, n=198)
11. *Rescued (Rescued Hearts, #1)* — Felice Stevens (loading 0.05882, n=226)
12. *Her Billionaires: The Complete Collection (Her Billionaires, #1-4)* — Julia Kent (loading 0.05317, n=240)

### Mode 16 positive

1. *Never Trust a Pirate (Playful Brides, #7)* — Valerie Bowman (loading 0.08566, n=100)
2. *When the Dust Settles (Timing, #3)* — Mary Calmes (loading 0.08122, n=127)
3. *Bodyguard To A Sex God (Bodyguards Inc. #1)* — R.J. Scott (loading 0.07722, n=154)
4. *A Day Makes (The Vault, #1)* — Mary Calmes (loading 0.07616, n=114)
5. *Volley Balls  (Balls to the Wall #1)* — Tara Lain (loading 0.07434, n=133)
6. *Sassy in Diapers (Sassy Mates, #4.3)* — Milly Taiden (loading 0.07371, n=156)
7. *Reese's Cowboy Kiss: Witness Protection - Rancher Style: Blake's Story (Sweet Montana Bride #1)* — Kimberly Krey (loading 0.06783, n=123)
8. *Hunted by Darkness (Darkness #4)* — Katie Reus (loading 0.05780, n=113)
9. *Fire at Twilight (The Firefighters of Darling Bay, #1)* — Lila Ashe (loading 0.05725, n=258)
10. *Beauty and the Highland Beast (A Highland Fairy Tale, #1)* — Lecia Cornwall (loading 0.05529, n=122)
11. *Hot on Her Trail (Hell Yeah!, #2)* — Sable Hunter (loading 0.05251, n=474)
12. *Delayed Penalty (Pilots Hockey, #1)* — Sophia Henry (loading 0.04827, n=221)

### Mode 16 negative

1. *Dragon Ball Z, Vol. 13: The Red Ribbon Androids (Dragon Ball Z, #13)* — Akira Toriyama (loading 0.07498, n=124)
2. *Luca (Ruin & Revenge, #2)* — Sarah Castille (loading 0.07247, n=127)
3. *Dragon Ball Z, Vol. 7: The Ginyu Force (Dragon Ball Z, #7)* — Akira Toriyama (loading 0.06590, n=129)
4. *Dragon Ball Z, Vol. 23: Boo Unleashed! (Dragon Ball Z, #23)* — Akira Toriyama (loading 0.06418, n=116)
5. *Hunter (Zeus's Pack #5)* — Lynn Hagen (loading 0.05859, n=139)
6. *Loco's Love (Brac Pack #9)* — Lynn Hagen (loading 0.05735, n=219)
7. *The Weight of It All* — N.R. Walker (loading 0.05646, n=370)
8. *Dragon Ball Z, Vol. 17: The Cell Game (Dragon Ball Z, #17)* — Akira Toriyama (loading 0.05404, n=129)
9. *Dragon Ball Z, Vol. 24: Hercule to the Rescue (Dragon Ball Z, #24)* — Akira Toriyama (loading 0.05401, n=123)
10. *Dragon Ball, Vol. 15: The Titanic Tournament (Dragon Ball, #15)* — Akira Toriyama (loading 0.05316, n=179)
11. *Claymore, Vol. 15: Genesis of War (Claymore, #15)* — Norihiro Yagi (loading 0.05264, n=210)
12. *Boarlander Bash Bear (Boarlander Bears, #2)* — T.S. Joyce (loading 0.05251, n=220)

### Mode 17 positive

1. *Designs of Desire (Desires Entwined, #1)* — Tempeste O'Riley (loading 0.07509, n=134)
2. *Served Hot (Portland Heat, #1)* — Annabeth Albert (loading 0.05936, n=250)
3. *Knave of Broken Hearts (Love in Laguna, #2)* — Tara Lain (loading 0.05807, n=161)
4. *Way Off Plan (Firsts and Forever, #1)* — Alexa Land (loading 0.05052, n=206)
5. *Bound for Keeps (Men of Honor, #5)* — S.E. Jakes (loading 0.04769, n=220)
6. *Brier's Bargain (Bodyguards in Love, #1)* — Carol Lynne (loading 0.04769, n=200)
7. *Finding Forgiveness (Finding, #4)* — Sloane Kennedy (loading 0.04312, n=108)
8. *Vengeance (The Protectors, #5)* — Sloane Kennedy (loading 0.04252, n=137)
9. *Complete Faith (Morning Report, #2)* — Sue  Brown (loading 0.04247, n=109)
10. *Fullmetal Alchemist, Vol. 20 (Fullmetal Alchemist, #20)* — Hiromu Arakawa (loading 0.04242, n=707)
11. *Someone to Keep Me (Collars and Cuffs, #3)* — K.C. Wells (loading 0.04226, n=206)
12. *Rurouni Kenshin, Volume 10* — Nobuhiro Watsuki (loading 0.04196, n=306)

### Mode 17 negative

1. *Dragon Ball, Vol. 13: Piccolo Conquers the World (Dragon Ball, #13)* — Akira Toriyama (loading 0.07049, n=184)
2. *Dragon Ball, Vol. 12: The Demon King Piccolo (Dragon Ball, #12)* — Akira Toriyama (loading 0.06515, n=190)
3. *Dragon Ball, Vol. 15: The Titanic Tournament (Dragon Ball, #15)* — Akira Toriyama (loading 0.06510, n=179)
4. *Bodyguard To A Sex God (Bodyguards Inc. #1)* — R.J. Scott (loading 0.06495, n=154)
5. *Dragon Ball Z, Vol. 13: The Red Ribbon Androids (Dragon Ball Z, #13)* — Akira Toriyama (loading 0.06456, n=124)
6. *Dragon Ball, Vol. 11: The Eyes of Tenshinhan (Dragon Ball, #11)* — Akira Toriyama (loading 0.06241, n=184)
7. *Dragon Ball, Vol. 16: Goku vs. Piccolo (Dragon Ball, #16)* — Akira Toriyama (loading 0.06195, n=188)
8. *A Day Makes (The Vault, #1)* — Mary Calmes (loading 0.06075, n=114)
9. *Dragon Ball, Vol. 14: Heaven and Earth (Dragon Ball, #14)* — Akira Toriyama (loading 0.06074, n=183)
10. *Dragon Ball, Vol. 3: The Training of Kame-Sen'nin (Dragon Ball, #3)* — Akira Toriyama (loading 0.06020, n=287)
11. *When the Dust Settles (Timing, #3)* — Mary Calmes (loading 0.05978, n=127)
12. *Dragon Ball, Vol. 6: Bulma Returns! (Dragon Ball, #6)* — Akira Toriyama (loading 0.05944, n=247)

### Mode 18 positive

1. *Desired by Dragons (Dragons of New York, #2)* — Terry Bolryder (loading 0.08914, n=128)
2. *Iron (Rent-a-Dragon #2)* — Terry Bolryder (loading 0.08783, n=126)
3. *Destined Dragons (Dragons of New York, #3)* — Terry Bolryder (loading 0.08723, n=112)
4. *The Divan* — Hafez (loading 0.07482, n=867)
5. *Taken by Night (Night and Day Ink, #4)* — Milly Taiden (loading 0.06321, n=101)
6. *Super Sock Man (Johnnies, #0.5, Granby Knitting, #1.5)* — Amy Lane (loading 0.06140, n=230)
7. *Bodyguard Bear (Protection, Inc., #1)* — Zoe Chant (loading 0.05839, n=118)
8. *Bear-ever Yours (Polar Heat, #1)* — Terry Bolryder (loading 0.05607, n=108)
9. *دیوان كلیات شمس تبریزی* — Jalaluddin Mevlana Rumi (loading 0.05566, n=276)
10. *Steel (Rent-a-Dragon #1)* — Terry Bolryder (loading 0.05452, n=192)
11. *Bayou Dreams (Rougaroux Social Club #1)* — Lynn Lorenz (loading 0.05402, n=235)
12. *A Tiger's Bounty (Tiger Protectors, #1)* — Terry Bolryder (loading 0.05321, n=134)

### Mode 18 negative

1. *Reflash (Assassin/Shifter, #10)* — Sandrine Gasq-Dion (loading 0.07689, n=150)
2. *Best Laid Plans (Assassin/Shifter, #5)* — Sandrine Gasq-Dion (loading 0.07370, n=173)
3. *An Ignited Passion (Assassin/Shifter, #9)* — Sandrine Gasq-Dion (loading 0.07209, n=163)
4. *Betrayed (Assassin/Shifter, #14)* — Sandrine Gasq-Dion (loading 0.07063, n=140)
5. *Perfectly Paired (Topped, #3; Masters and Mercenaries, #12.5)* — Lexi Blake (loading 0.07040, n=108)
6. *A Mate for Lance (The Program, #5)* — Charlene Hartnady (loading 0.06398, n=112)
7. *بامداد خمار* — ftnh Hj sydjwdy (loading 0.06391, n=615)
8. *Curtis (Coyote Ridge, #1)* — Nicole Edwards (loading 0.06028, n=160)
9. *Fugitive of Magic (Dragon's Gift: The Protector #1)* — Linsey Hall (loading 0.05790, n=113)
10. *A Mate for Lazarus (The Program #3)* — Charlene Hartnady (loading 0.05753, n=134)
11. *For the Love of Caden  (Assassin/Shifter, #6)* — Sandrine Gasq-Dion (loading 0.05635, n=175)
12. *Anchor Me (Stark Trilogy, #4)* — J. Kenner (loading 0.05464, n=170)

### Mode 19 positive

1. *Best Laid Plans (Assassin/Shifter, #5)* — Sandrine Gasq-Dion (loading 0.10768, n=173)
2. *Reflash (Assassin/Shifter, #10)* — Sandrine Gasq-Dion (loading 0.09040, n=150)
3. *An Ignited Passion (Assassin/Shifter, #9)* — Sandrine Gasq-Dion (loading 0.08735, n=163)
4. *For the Love of Caden  (Assassin/Shifter, #6)* — Sandrine Gasq-Dion (loading 0.07246, n=175)
5. *Half Moon Rising (Assassin/Shifter, #4)* — Sandrine Gasq-Dion (loading 0.07073, n=189)
6. *Devil and the Deep (Deep Six, #2)* — Julie Ann Walker (loading 0.06280, n=155)
7. *Russian Prey (Assassin/Shifter, #8)* — Sandrine Gasq-Dion (loading 0.06178, n=168)
8. *The Red Zone (Assassin/Shifter, #11)* — Sandrine Gasq-Dion (loading 0.06106, n=149)
9. *A Starstruck Kiss (Caught Up in Love, #3.5)* — Lauren Blakely (loading 0.06065, n=137)
10. *Stars in Their Eyes (Caught Up in Love, #4)* — Lauren Blakely (loading 0.06052, n=152)
11. *Too Hard to Forget (Romancing the Clarksons, #3)* — Tessa Bailey (loading 0.05780, n=148)
12. *Hers to Command (Verdantia, #1)* — Patricia A. Knight (loading 0.05693, n=178)

### Mode 19 negative

1. *Car Wash (Car Wash #1)* — Shawn Lane (loading 0.06511, n=134)
2. *Edric (Resistant Omegas #3)* — Joyee Flynn (loading 0.06429, n=123)
3. *Blood Signs (Blood, Moon and Sun #1)* — Amber Kell (loading 0.05324, n=180)
4. *Nothing To Do With Pride (Supernatural Mates #4)* — Amber Kell (loading 0.05008, n=143)
5. *Stormy Eyes (Brac Pack #5)* — Lynn Hagen (loading 0.04949, n=246)
6. *Gemini* — Chris Owen (loading 0.04846, n=246)
7. *What Chris Wants (Men Who Walk the Edge of Honor, #4.5)* — Lori Foster (loading 0.04757, n=341)
8. *Nothing Special (Nothing Special, #1)* — A.E. Via (loading 0.04566, n=377)
9. *My Little Kitty (Purrfect Mates #2)* — Joyee Flynn (loading 0.04531, n=130)
10. *Becoming Dragon (Dragon Point, #1)* — Eve Langlais (loading 0.04395, n=104)
11. *Harder than Words (Montgomery Ink, #3)* — Carrie Ann Ryan (loading 0.04246, n=195)
12. *A Brac Pack Crazy Family Christmas (Brac Pack #24)* — Lynn Hagen (loading 0.04245, n=124)

### Mode 20 positive

1. *Alpha's Prerogative (Wolves of Stone Ridge #2)* — Charlie Richards (loading 0.09742, n=181)
2. *Bayou Dreams (Rougaroux Social Club #1)* — Lynn Lorenz (loading 0.09263, n=235)
3. *Boarlander Boss Bear (Boarlander Bears, #1)* — T.S. Joyce (loading 0.07461, n=251)
4. *Boarlander Bash Bear (Boarlander Bears, #2)* — T.S. Joyce (loading 0.06277, n=220)
5. *Boarlander Cursed Bear (Boarlander Bears, #5)* — T.S. Joyce (loading 0.05479, n=193)
6. *Air Ryder (Harper's Mountains, #3)* — T.S. Joyce (loading 0.05241, n=201)
7. *Persuasion (Sons of Odin MC, #1)* — Violetta Rand (loading 0.05190, n=113)
8. *Dylan's Redemption (The McBrides, #3)* — Jennifer Ryan (loading 0.05069, n=124)
9. *Kristin (Hope Valley BBW Online Dating App Romance, #2)* — Ariana Hawkes (loading 0.04987, n=106)
10. *The Red Zone (Assassin/Shifter, #11)* — Sandrine Gasq-Dion (loading 0.04904, n=149)
11. *Commanded (Club Sin, #6)* — Stacey Kennedy (loading 0.04656, n=146)
12. *Raw and Dirty (Bad Boys MC Trilogy, #1)* — Violet Blaze (loading 0.04543, n=112)

### Mode 20 negative

1. *Sassy in Diapers (Sassy Mates, #4.3)* — Milly Taiden (loading 0.08544, n=156)
2. *Reese's Cowboy Kiss: Witness Protection - Rancher Style: Blake's Story (Sweet Montana Bride #1)* — Kimberly Krey (loading 0.08233, n=123)
3. *Owning It (Metropolis, #3)* — Riley Hart (loading 0.07785, n=133)
4. *Vengeance (The Protectors, #5)* — Sloane Kennedy (loading 0.07018, n=137)
5. *Fire at Twilight (The Firefighters of Darling Bay, #1)* — Lila Ashe (loading 0.06725, n=258)
6. *Hot on Her Trail (Hell Yeah!, #2)* — Sable Hunter (loading 0.06540, n=474)
7. *Shatter (Unbreakable Bonds #2)* — Jocelynn Drake (loading 0.06434, n=138)
8. *Finding Forgiveness (Finding, #4)* — Sloane Kennedy (loading 0.06331, n=108)
9. *Logan's Need (The Escort, #3)* — Sloane Kennedy (loading 0.06093, n=122)
10. *Salvation (Firsts and Forever, #5)* — Alexa Land (loading 0.05894, n=136)
11. *Jumping Jude (Made Marian, #3)* — Lucy Lennox (loading 0.05758, n=194)
12. *Hunted by Darkness (Darkness #4)* — Katie Reus (loading 0.05334, n=113)

### Mode 21 positive

1. *Never Trust a Pirate (Playful Brides, #7)* — Valerie Bowman (loading 0.11802, n=100)
2. *Hunted by Darkness (Darkness #4)* — Katie Reus (loading 0.09130, n=113)
3. *Burn Down the Night (Everything I Left Unsaid, #3)* — Molly O'Keefe (loading 0.08563, n=205)
4. *Beauty and the Highland Beast (A Highland Fairy Tale, #1)* — Lecia Cornwall (loading 0.08551, n=122)
5. *Claymore, Vol. 15: Genesis of War (Claymore, #15)* — Norihiro Yagi (loading 0.07947, n=210)
6. *Don't Read in the Closet: Volume Two* — Blaine D. Arden (loading 0.07223, n=102)
7. *Delayed Penalty (Pilots Hockey, #1)* — Sophia Henry (loading 0.07211, n=221)
8. *Claymore, Vol. 11: Kindred of Paradise (Claymore, #11)* — Norihiro Yagi (loading 0.07071, n=253)
9. *Tremaine's True Love (True Gentlemen, #1)* — Grace Burrowes (loading 0.07016, n=221)
10. *Alpha Trine (The Valespian Pact #1)* — Lexi Ander (loading 0.06957, n=172)
11. *Claymore, Vol. 19: Phantoms in the Heart (Claymore, #19)* — Norihiro Yagi (loading 0.06896, n=175)
12. *Up to Date (Better Date than Never, #8)* — Susan Hatler (loading 0.06633, n=116)

### Mode 21 negative

1. *Luca (Ruin & Revenge, #2)* — Sarah Castille (loading 0.09961, n=127)
2. *Commanded (Club Sin, #6)* — Stacey Kennedy (loading 0.07797, n=146)
3. *Nico (Ruin & Revenge, #1)* — Sarah Castille (loading 0.07470, n=261)
4. *The Duty of a Beta (Pack Discipline #3)* — Kim Dare (loading 0.07226, n=176)
5. *Vampires Never Cry Wolf (Dead in the City, #3)* — Sara  Humphreys (loading 0.07038, n=123)
6. *Some Like It Scot (Scandalous Highlanders, #4)* — Suzanne Enoch (loading 0.06513, n=171)
7. *The Major's Faux Fiancee (The Dukes of War, #4)* — Erica Ridley (loading 0.06377, n=109)
8. *Charming the Beast (Purgatory, #3)* — Cynthia Eden (loading 0.06008, n=195)
9. *Super Sock Man (Johnnies, #0.5, Granby Knitting, #1.5)* — Amy Lane (loading 0.05970, n=230)
10. *Ecstasy Claimed (Guardians of the Realms, #2)* — Setta Jay (loading 0.05852, n=141)
11. *Play Me Hard (Play Me, #3)* — Tracy Wolff (loading 0.05742, n=150)
12. *An Oral Fixation* — Piper Vaughn (loading 0.05633, n=143)

### Mode 22 positive

1. *Luca (Ruin & Revenge, #2)* — Sarah Castille (loading 0.08506, n=127)
2. *Commanded (Club Sin, #6)* — Stacey Kennedy (loading 0.06731, n=146)
3. *Nico (Ruin & Revenge, #1)* — Sarah Castille (loading 0.06204, n=261)
4. *Vampires Never Cry Wolf (Dead in the City, #3)* — Sara  Humphreys (loading 0.06178, n=123)
5. *Sweet Treats (Sweet Perfection, #1)* — Stormy Glenn (loading 0.06017, n=116)
6. *The Major's Faux Fiancee (The Dukes of War, #4)* — Erica Ridley (loading 0.05656, n=109)
7. *Angel and the Assassin (Angel and the Assassin, #1)* — Fyn Alexander (loading 0.05533, n=167)
8. *Play Me Hard (Play Me, #3)* — Tracy Wolff (loading 0.05354, n=150)
9. *Stirring Up Trouble (Stir, #1)* — Z.A. Maxfield (loading 0.05353, n=151)
10. *Charming the Beast (Purgatory, #3)* — Cynthia Eden (loading 0.05352, n=195)
11. *A Day Makes (The Vault, #1)* — Mary Calmes (loading 0.05308, n=114)
12. *When the Dust Settles (Timing, #3)* — Mary Calmes (loading 0.04988, n=127)

### Mode 22 negative

1. *Never Trust a Pirate (Playful Brides, #7)* — Valerie Bowman (loading 0.09537, n=100)
2. *Hunted by Darkness (Darkness #4)* — Katie Reus (loading 0.07790, n=113)
3. *Beauty and the Highland Beast (A Highland Fairy Tale, #1)* — Lecia Cornwall (loading 0.07628, n=122)
4. *Burn Down the Night (Everything I Left Unsaid, #3)* — Molly O'Keefe (loading 0.07020, n=205)
5. *Delayed Penalty (Pilots Hockey, #1)* — Sophia Henry (loading 0.06743, n=221)
6. *Up to Date (Better Date than Never, #8)* — Susan Hatler (loading 0.06052, n=116)
7. *Tremaine's True Love (True Gentlemen, #1)* — Grace Burrowes (loading 0.05906, n=221)
8. *Darkness Falls (Reveler #1)* — Erin Kellison (loading 0.05592, n=219)
9. *The Missing Butterfly (Missing Butterfly, #1)* — Megan Derr (loading 0.05546, n=307)
10. *Out of the Shadow (Cattle Valley, #6)* — Carol Lynne (loading 0.05162, n=182)
11. *Just For You* — Jet Mykles (loading 0.05013, n=314)
12. *The Girl from Summer Hill* — Jude Deveraux (loading 0.04943, n=331)

### Mode 23 positive

1. *Iron (Rent-a-Dragon #2)* — Terry Bolryder (loading 0.06424, n=126)
2. *Destined Dragons (Dragons of New York, #3)* — Terry Bolryder (loading 0.06108, n=112)
3. *Desired by Dragons (Dragons of New York, #2)* — Terry Bolryder (loading 0.06048, n=128)
4. *A Subtle Breeze (Southern Spirits, #1)* — Bailey Bradford (loading 0.05832, n=104)
5. *Secret Desires (Tri-Omega Mates #1)* — Stormy Glenn (loading 0.05477, n=226)
6. *Keeping House (Truth or Dare #1)* — Lee Brazil (loading 0.05211, n=143)
7. *Bent - Not Broken (Cattle Valley, #13)* — Carol Lynne (loading 0.05205, n=132)
8. *The Dom with a Safeword (Badass Brats, #1)* — Sorcha Black (loading 0.05162, n=131)
9. *Cirque de Minuit (Cirque Masters, #1)* — Annabel Joseph (loading 0.04912, n=146)
10. *Titanium (Rent-A-Dragon #3)* — Terry Bolryder (loading 0.04619, n=111)
11. *What Remains* — Garrett Leigh (loading 0.04596, n=159)
12. *His Sub's Submissive (Club Esoteria, #1)* — Cooper McKenzie (loading 0.04561, n=100)

### Mode 23 negative

1. *Stormy Eyes (Brac Pack #5)* — Lynn Hagen (loading 0.06328, n=246)
2. *Mark's Not Gay (Brac Pack #11)* — Lynn Hagen (loading 0.05074, n=212)
3. *Fret (The Rock Series, #1)* — Sandrine Gasq-Dion (loading 0.04543, n=160)
4. *Knave of Broken Hearts (Love in Laguna, #2)* — Tara Lain (loading 0.04432, n=161)
5. *A Rose is a Rose* — Jet Mykles (loading 0.04413, n=133)
6. *A Mate for Lazarus (The Program #3)* — Charlene Hartnady (loading 0.04360, n=134)
7. *Hard to Serve (Hard Ink #4.7; Blasphemy 0.5; 1001 Dark Nights #43)* — Laura Kaye (loading 0.04324, n=173)
8. *Perfectly Paired (Topped, #3; Masters and Mercenaries, #12.5)* — Lexi Blake (loading 0.04297, n=108)
9. *Montana's Vamp (Brac Pack #16)* — Lynn Hagen (loading 0.04273, n=223)
10. *Mastering Her Senses (Blasphemy, #2)* — Laura Kaye (loading 0.04225, n=157)
11. *Dagon's Ride (Brac Pack #19)* — Lynn Hagen (loading 0.04158, n=183)
12. *Obsession (Cordova Empire, #1)* — Ann Mayburn (loading 0.04141, n=104)

### Mode 24 positive

1. *Running Hot (EMS Heat, #1)* — Stephani Hecht (loading 0.05381, n=178)
2. *Iron (Rent-a-Dragon #2)* — Terry Bolryder (loading 0.05367, n=126)
3. *Destined Dragons (Dragons of New York, #3)* — Terry Bolryder (loading 0.05199, n=112)
4. *Desired by Dragons (Dragons of New York, #2)* — Terry Bolryder (loading 0.05120, n=128)
5. *Bound Forever (Bound, #3)* — Ava March (loading 0.05095, n=107)
6. *Bound by Deception (Bound, #1)* — Ava March (loading 0.04914, n=323)
7. *Don't Read in the Closet: Volume Two* — Blaine D. Arden (loading 0.04895, n=102)
8. *His Client (His Client, #1)* — Ava March (loading 0.04778, n=214)
9. *Mark's Not Gay (Brac Pack #11)* — Lynn Hagen (loading 0.04731, n=212)
10. *Baiting Ben (Moon Pack, #2)* — Amber Kell (loading 0.04605, n=229)
11. *Boarlander Boss Bear (Boarlander Bears, #1)* — T.S. Joyce (loading 0.04575, n=251)
12. *Nana, Vol. 11 (Nana, #11)* — Ai Yazawa (loading 0.04548, n=386)

### Mode 24 negative

1. *Sassy in Diapers (Sassy Mates, #4.3)* — Milly Taiden (loading 0.06736, n=156)
2. *Reese's Cowboy Kiss: Witness Protection - Rancher Style: Blake's Story (Sweet Montana Bride #1)* — Kimberly Krey (loading 0.06565, n=123)
3. *Fire at Twilight (The Firefighters of Darling Bay, #1)* — Lila Ashe (loading 0.06031, n=258)
4. *Hot on Her Trail (Hell Yeah!, #2)* — Sable Hunter (loading 0.05229, n=474)
5. *The Divan* — Hafez (loading 0.04863, n=867)
6. *An Oral Fixation* — Piper Vaughn (loading 0.04630, n=143)
7. *Texas Winter (Texas, #2)* — R.J. Scott (loading 0.04291, n=275)
8. *A Subtle Breeze (Southern Spirits, #1)* — Bailey Bradford (loading 0.04015, n=104)
9. *A Troubled Range (Range, #2)* — Andrew  Grey (loading 0.03935, n=206)
10. *Grey's Awakening (Cabin Fever, #2)* — Cameron Dane (loading 0.03897, n=378)
11. *The Duty of a Beta (Pack Discipline #3)* — Kim Dare (loading 0.03751, n=176)
12. *Honor Bound (Viking Lore #1)* — Stormy Glenn (loading 0.03691, n=161)

### Mode 25 positive

1. *Secret Desires (Tri-Omega Mates #1)* — Stormy Glenn (loading 0.06549, n=226)
2. *Perfectly Paired (Topped, #3; Masters and Mercenaries, #12.5)* — Lexi Blake (loading 0.06097, n=108)
3. *A Mate for Lazarus (The Program #3)* — Charlene Hartnady (loading 0.05883, n=134)
4. *Curtis (Coyote Ridge, #1)* — Nicole Edwards (loading 0.05704, n=160)
5. *A Mate for Lance (The Program, #5)* — Charlene Hartnady (loading 0.05703, n=112)
6. *Bent - Not Broken (Cattle Valley, #13)* — Carol Lynne (loading 0.05300, n=132)
7. *Fugitive of Magic (Dragon's Gift: The Protector #1)* — Linsey Hall (loading 0.05055, n=113)
8. *Nana, Vol. 11 (Nana, #11)* — Ai Yazawa (loading 0.05017, n=386)
9. *Magic Undying (Dragon's Gift: The Seeker #1)* — Linsey Hall (loading 0.04912, n=136)
10. *Sweetest Taboo (S.I.N., #3)* — J. Kenner (loading 0.04823, n=173)
11. *A Caleb Footlong (The O'Hagan Way #2)* — Joyee Flynn (loading 0.04796, n=126)
12. *Anchor Me (Stark Trilogy, #4)* — J. Kenner (loading 0.04595, n=170)

### Mode 25 negative

1. *Destined Dragons (Dragons of New York, #3)* — Terry Bolryder (loading 0.08030, n=112)
2. *Iron (Rent-a-Dragon #2)* — Terry Bolryder (loading 0.07314, n=126)
3. *Midnight (Dance with the Devil, #3)* — Megan Derr (loading 0.07283, n=149)
4. *Desired by Dragons (Dragons of New York, #2)* — Terry Bolryder (loading 0.07150, n=128)
5. *Alpha Trine (The Valespian Pact #1)* — Lexi Ander (loading 0.05891, n=172)
6. *Bear-ever Yours (Polar Heat, #1)* — Terry Bolryder (loading 0.05568, n=108)
7. *Taken by Night (Night and Day Ink, #4)* — Milly Taiden (loading 0.05562, n=101)
8. *Murphy's Madness (Brac Pack #15)* — Lynn Hagen (loading 0.04933, n=196)
9. *Carter's Tryck (Brac Pack #17)* — Lynn Hagen (loading 0.04849, n=202)
10. *Reese's Cowboy Kiss: Witness Protection - Rancher Style: Blake's Story (Sweet Montana Bride #1)* — Kimberly Krey (loading 0.04736, n=123)
11. *A Tiger's Bounty (Tiger Protectors, #1)* — Terry Bolryder (loading 0.04666, n=134)
12. *Mark's Not Gay (Brac Pack #11)* — Lynn Hagen (loading 0.04634, n=212)

### Mode 26 positive

1. *Winning Streak (The Beasts of Baseball #4)* — Alice Ward (loading 0.07633, n=138)
2. *Dark Devotion (Fatefully Yours #1)* — Gabrielle Evans (loading 0.05397, n=101)
3. *Secret Desires (Tri-Omega Mates #1)* — Stormy Glenn (loading 0.05006, n=226)
4. *A Caleb Footlong (The O'Hagan Way #2)* — Joyee Flynn (loading 0.04955, n=126)
5. *Billionaire Unknown: Blake* — J.S. Scott (loading 0.04911, n=159)
6. *Sold (Highest Bidder, #2)* — Lauren Landish (loading 0.04823, n=170)
7. *Falling for the Babysitter* — Penny Wylder (loading 0.04754, n=294)
8. *Twisted Twosome* — Meghan Quinn (loading 0.04712, n=261)
9. *Russian Prey (Assassin/Shifter, #8)* — Sandrine Gasq-Dion (loading 0.04688, n=168)
10. *The Target* — Gerri Hill (loading 0.04660, n=138)
11. *The Dom with a Safeword (Badass Brats, #1)* — Sorcha Black (loading 0.04657, n=131)
12. *Real Deal (Single Dads Club #1)* — Piper Rayne (loading 0.04627, n=173)

### Mode 26 negative

1. *The Reaper's Mate* — Celia Aaron (loading 0.08473, n=120)
2. *Dangerous Kiss: A Rock Star Romance (Dangerous Noise Book 1)* — Crystal Kaswell (loading 0.08274, n=178)
3. *Duty* — Lauren Landish (loading 0.08144, n=156)
4. *Knocked Up* — Nikki Chase (loading 0.07347, n=107)
5. *All I Want is You (Forever and Ever, #1)* — E.L. Todd (loading 0.07163, n=243)
6. *Her Dad's Friend* — Penny Wylder (loading 0.05704, n=408)
7. *Just A Taste Of Me (Wolf Creek Pack #2)* — Stormy Glenn (loading 0.04792, n=230)
8. *Chance of a Lifetime (Anderson Brothers, #3)* — Marissa Clarke (loading 0.04676, n=103)
9. *Pretend It's Love (Behind the Bar, #2)* — Stefanie London (loading 0.04570, n=112)
10. *Dare to Dream (Maxwell, #2)* — S.B. Alexander (loading 0.04447, n=106)
11. *The Perfect Bargain* — Jessa McAdams (loading 0.04297, n=111)
12. *Over the Top (Maverick Montana, #4)* — Rebecca Zanetti (loading 0.04217, n=142)

### Mode 27 positive

1. *Devil and the Deep (Deep Six, #2)* — Julie Ann Walker (loading 0.08335, n=155)
2. *Serial Love (Saints Protection & Investigation #1)* — Maryann Jordan (loading 0.07784, n=127)
3. *Own Me* — Penny Wylder (loading 0.07709, n=125)
4. *Rockstar Daddy (Wilder Rock, #1)* — Taryn Quinn (loading 0.07598, n=134)
5. *Searching For Harmony (Boston Love #1)* — Kelly Elliott (loading 0.07402, n=181)
6. *The List (The List, #1)* — Tawna Fenske (loading 0.07367, n=119)
7. *Now That It's You* — Tawna Fenske (loading 0.06178, n=116)
8. *Nothing Special (Nothing Special, #1)* — A.E. Via (loading 0.05563, n=377)
9. *The Unrequited* — Saffron A. Kent (loading 0.05174, n=434)
10. *The Rule Maker  (The Rule Breakers, #2)* — Jennifer Blackwood (loading 0.05133, n=178)
11. *Mr. and Mr. Smith (Tough Love, #1)* — HelenKay Dimon (loading 0.04909, n=129)
12. *Kick Start (Dangerous Ground, #5)* — Josh Lanyon (loading 0.04843, n=141)

### Mode 27 negative

1. *Emergency Engagement (Love Emergency, #1)* — Samanthe Beck (loading 0.07020, n=148)
2. *Fighting Fate (Redwood Pack, #6)* — Carrie Ann Ryan (loading 0.06125, n=101)
3. *Broken Fortress (Rifter #6)* — Ginn Hale (loading 0.06121, n=117)
4. *Ghost Riders (Ghost Riders MC #1-5)* — Alexa Riley (loading 0.06078, n=120)
5. *The Iron Temple (Rifter, #9)* — Ginn Hale (loading 0.05477, n=105)
6. *Fool Me Once (Foolproof Love, #2)* — Katee Robert (loading 0.05417, n=144)
7. *The Boss: Book One (The Boss, #1)* — Cari Quinn (loading 0.05393, n=130)
8. *Thug Matrimony (Thug #3)* — Wahida Clark (loading 0.05332, n=271)
9. *Every Thug Needs a Lady (Thug #2)* — Wahida Clark (loading 0.05219, n=269)
10. *Enemies & Shadows (Rifter #7)* — Ginn Hale (loading 0.05114, n=114)
11. *An Indecent Proposal (The O'Malleys, #3)* — Katee Robert (loading 0.05113, n=166)
12. *Run to Ground (Rocky Mountain K9 Unit, #1)* — Katie Ruggle (loading 0.05004, n=123)

### Mode 28 positive

1. *Falling Down* — Eli Easton (loading 0.06115, n=141)
2. *Obsession (Cordova Empire, #1)* — Ann Mayburn (loading 0.05180, n=104)
3. *Don't Read in the Closet: Volume Two* — Blaine D. Arden (loading 0.05029, n=102)
4. *Delivered Fast (Portland Heat, #3)* — Annabeth Albert (loading 0.04911, n=148)
5. *Connection Error (#gaymers, #3)* — Annabeth Albert (loading 0.04862, n=231)
6. *The Medicine and the Mob (Santorno, #1)* — Sandrine Gasq-Dion (loading 0.04620, n=101)
7. *Boarlander Boss Bear (Boarlander Bears, #1)* — T.S. Joyce (loading 0.04530, n=251)
8. *Mastering Her Senses (Blasphemy, #2)* — Laura Kaye (loading 0.04507, n=157)
9. *Up All Night in Bliss (Nights in Bliss, Colorado, #6.5)* — Sophie Oak (loading 0.04480, n=100)
10. *Playing with Temptation (The Players Club, #1)* — Erika Wilde (loading 0.04350, n=137)
11. *Siren Enslaved (Texas Sirens, #3)* — Sophie Oak (loading 0.04332, n=237)
12. *Midsummer Baker (Midsummer #4)* — Megan Derr (loading 0.04325, n=116)

### Mode 28 negative

1. *Curve Ball (Homeruns #2)* — Sloan  Johnson (loading 0.06937, n=112)
2. *The Dom with a Safeword (Badass Brats, #1)* — Sorcha Black (loading 0.06381, n=131)
3. *Cirque de Minuit (Cirque Masters, #1)* — Annabel Joseph (loading 0.06179, n=146)
4. *Branded Sanctuary (Nature of Desire, #7)* — Joey W. Hill (loading 0.05782, n=133)
5. *His Sub's Submissive (Club Esoteria, #1)* — Cooper McKenzie (loading 0.05746, n=100)
6. *Enemies like You  (Enemies with Benefits #1)* — Joanna Chambers (loading 0.05723, n=100)
7. *Sassy in Diapers (Sassy Mates, #4.3)* — Milly Taiden (loading 0.05664, n=156)
8. *Reese's Cowboy Kiss: Witness Protection - Rancher Style: Blake's Story (Sweet Montana Bride #1)* — Kimberly Krey (loading 0.05650, n=123)
9. *Cronin's Key II (Cronin's Key, #2)* — N.R. Walker (loading 0.05474, n=182)
10. *Loving Storm (Ashes & Embers, #5)* — Carian Cole (loading 0.05472, n=121)
11. *Guns n' Boys: Book 1, Part 1 (Guns n' Boys, #1)* — K.A. Merikan (loading 0.05272, n=138)
12. *Eater of Lives (Spectr, #4)* — Jordan L. Hawk (loading 0.05211, n=142)

### Mode 29 positive

1. *The Target* — Gerri Hill (loading 0.06831, n=138)
2. *Artist's Dream* — Gerri Hill (loading 0.06515, n=138)
3. *Behind the Pine Curtain* — Gerri Hill (loading 0.06335, n=189)
4. *Creature Feature (Creature Feature #1)* — Poppy Dennison (loading 0.05513, n=117)
5. *No Strings* — Gerri Hill (loading 0.05292, n=126)
6. *Softly Spoken Lies (Moonlight Breed #4)* — Gabrielle Evans (loading 0.05285, n=110)
7. *Alpha Trine (The Valespian Pact #1)* — Lexi Ander (loading 0.05119, n=172)
8. *学園アリス 19 [Gakuen Alice 19]* — Tachibana Higuchi (loading 0.04720, n=104)
9. *Keeping House (Truth or Dare #1)* — Lee Brazil (loading 0.04631, n=143)
10. *Black Magic (Black Magic #1)* — Megan Derr (loading 0.04591, n=131)
11. *Kick Start (Dangerous Ground, #5)* — Josh Lanyon (loading 0.04449, n=141)
12. *Mr. and Mr. Smith (Tough Love, #1)* — HelenKay Dimon (loading 0.04406, n=129)

### Mode 29 negative

1. *Too Hard to Forget (Romancing the Clarksons, #3)* — Tessa Bailey (loading 0.05841, n=148)
2. *Blood Hunt (Midnight Hunters #2)* — L.L. Raand (loading 0.05671, n=147)
3. *Hers to Command (Verdantia, #1)* — Patricia A. Knight (loading 0.05509, n=178)
4. *Stars in Their Eyes (Caught Up in Love, #4)* — Lauren Blakely (loading 0.05408, n=152)
5. *Broken Fortress (Rifter #6)* — Ginn Hale (loading 0.05343, n=117)
6. *Almost Matched (Almost Bad Boys, #1)* — A.O. Peart (loading 0.05335, n=155)
7. *The Midnight Hunt (Midnight Hunters, #1)* — L.L. Raand (loading 0.05233, n=214)
8. *A Starstruck Kiss (Caught Up in Love, #3.5)* — Lauren Blakely (loading 0.05159, n=137)
9. *All Play and No Work (Cattle Valley, #1)* — Carol Lynne (loading 0.04872, n=278)
10. *Unearthing Cole (Discovering Me, #1)* — A.M. Arthur (loading 0.04754, n=133)
11. *The Iron Temple (Rifter, #9)* — Ginn Hale (loading 0.04732, n=105)
12. *Enemies & Shadows (Rifter #7)* — Ginn Hale (loading 0.04678, n=114)

### Mode 30 positive

1. *Home Run (The Boys of Summer, #2)* — Heidi McLaughlin (loading 0.08315, n=121)
2. *Blown Away* — Brenda Rothert (loading 0.06414, n=101)
3. *Pitch Please (There's No Crying in Baseball #1)* — Lani Lynn Vale (loading 0.06113, n=218)
4. *Turbulent Waters (Billionaire Aviators #3)* — Melody Anne (loading 0.05735, n=126)
5. *Butterfly Dreams* — A. Meredith Walters (loading 0.05714, n=178)
6. *Hottest Mess (S.I.N., #2)* — J. Kenner (loading 0.05526, n=181)
7. *Unexpectedly Hers (Sterling Canyon, #3)* — Jamie Beck (loading 0.05256, n=109)
8. *Forged in Smoke (Red-Hot SEALs, #3)* — Trish McCallan (loading 0.05055, n=128)
9. *Finding Our Forever (Silver Springs, #1)* — Brenda Novak (loading 0.04674, n=211)
10. *Vengeance (The Protectors, #5)* — Sloane Kennedy (loading 0.04595, n=137)
11. *Wrong Question, Right Answer (The Bourbon Street Boys #3)* — Elle Casey (loading 0.04494, n=360)
12. *Wrong Turn, Right Direction (The Bourbon Street Boys, #4)* — Elle Casey (loading 0.04388, n=213)

### Mode 30 negative

1. *His to Cherish (Fireside, #3)* — Stacey  Lynn (loading 0.07283, n=116)
2. *Bayou Dreams (Rougaroux Social Club #1)* — Lynn Lorenz (loading 0.05712, n=235)
3. *Alpha's Prerogative (Wolves of Stone Ridge #2)* — Charlie Richards (loading 0.05488, n=181)
4. *Porter (Lovibond, #3)* — Georgia Cates (loading 0.05249, n=150)
5. *Emergency Engagement (Love Emergency, #1)* — Samanthe Beck (loading 0.04450, n=148)
6. *Tap (Lovibond, #1)* — Georgia Cates (loading 0.04227, n=339)
7. *From the Wreckage* — Melissa  Collins (loading 0.04199, n=104)
8. *Two Fangs And A Hoof (Midnight Matings #4)* — Joyee Flynn (loading 0.04197, n=164)
9. *Anchored (Belonging, #1)* — Rachel Haimowitz (loading 0.04163, n=136)
10. *Deja Vu* — Sosie Frost (loading 0.04049, n=109)
11. *Second Chance Bite (Wolf Harem, #1)* — Joyee Flynn (loading 0.04007, n=104)
12. *Feathers and Filth (Midnight Matings #16)* — Joyee Flynn (loading 0.03956, n=104)

### Mode 31 positive

1. *The General's Lover (Assassin/Shifter, #7)* — Sandrine Gasq-Dion (loading 0.05817, n=171)
2. *Sassy in Diapers (Sassy Mates, #4.3)* — Milly Taiden (loading 0.05395, n=156)
3. *Reese's Cowboy Kiss: Witness Protection - Rancher Style: Blake's Story (Sweet Montana Bride #1)* — Kimberly Krey (loading 0.05260, n=123)
4. *Fire at Twilight (The Firefighters of Darling Bay, #1)* — Lila Ashe (loading 0.04581, n=258)
5. *Hot on Her Trail (Hell Yeah!, #2)* — Sable Hunter (loading 0.04427, n=474)
6. *Stormy Eyes (Brac Pack #5)* — Lynn Hagen (loading 0.04426, n=246)
7. *Riley's Downfall (Brac Pack #29)* — Lynn Hagen (loading 0.04145, n=124)
8. *Dragon Ball Z, Vol. 13: The Red Ribbon Androids (Dragon Ball Z, #13)* — Akira Toriyama (loading 0.04122, n=124)
9. *Puslu Kıtalar Atlası* — Ihsan Oktay Anar (loading 0.04111, n=1,568)
10. *The Medicine and the Mob (Santorno, #1)* — Sandrine Gasq-Dion (loading 0.03932, n=101)
11. *Tutunamayanlar* — Oguz Atay (loading 0.03907, n=965)
12. *The Slayer's Apprentice* — Zathyn Priest (loading 0.03893, n=111)

### Mode 31 negative

1. *Boarlander Boss Bear (Boarlander Bears, #1)* — T.S. Joyce (loading 0.05003, n=251)
2. *Boarlander Cursed Bear (Boarlander Bears, #5)* — T.S. Joyce (loading 0.04645, n=193)
3. *حلفاء الشر* — nbyl frwq (loading 0.04407, n=121)
4. *One Night with Her Bachelor (Montana Born Bachelor Auction #6; Wild Montana Nights, #1)* — Kat Latham (loading 0.04062, n=109)
5. *Hidden Desires (Tri-Omega Mates #3)* — Stormy Glenn (loading 0.04010, n=158)
6. *Like the Taste of Summer* — Kaje Harper (loading 0.03987, n=157)
7. *Air Ryder (Harper's Mountains, #3)* — T.S. Joyce (loading 0.03735, n=201)
8. *Cowboy Easy (Blaecleah Brothers #1)* — Stormy Glenn (loading 0.03705, n=182)
9. *How to Walk Like a Man (Howl At The Moon #2)* — Eli Easton (loading 0.03602, n=319)
10. *Quinn's Hart* — Cassandra Gold (loading 0.03578, n=135)
11. *My Fair Princess (The Improper Princesses #1)* — Vanessa Kelly (loading 0.03541, n=138)
12. *Sold to the Hitman (Hitman #2)* — Alexis Abbott (loading 0.03517, n=285)

### Mode 32 positive

1. *Keata's Promise (Brac Pack #7)* — Lynn Hagen (loading 0.04821, n=235)
2. *There's Something About Ari (Bluewater Bay, #2)* — L.B. Gregg (loading 0.04642, n=177)
3. *The Midnight Hunt (Midnight Hunters, #1)* — L.L. Raand (loading 0.04351, n=214)
4. *The Holy Road (Rifter #5)* — Ginn Hale (loading 0.04103, n=121)
5. *Blood Hunt (Midnight Hunters #2)* — L.L. Raand (loading 0.04079, n=147)
6. *Kincade's Rose (The Megalodon Team, #1)* — Aliyah Burke (loading 0.03979, n=134)
7. *Skip Beat!, Vol. 28* — Yoshiki Nakamura (loading 0.03898, n=458)
8. *Winning Streak (The Beasts of Baseball #4)* — Alice Ward (loading 0.03868, n=138)
9. *The Dopeman's Wife (The Dopeman, #1)* — JaQuavis Coleman (loading 0.03840, n=221)
10. *Broken Fortress (Rifter #6)* — Ginn Hale (loading 0.03725, n=117)
11. *حلفاء الشر* — nbyl frwq (loading 0.03597, n=121)
12. *The Prada Plan (The Prada Plan, #1)* — Ashley Antoinette (loading 0.03586, n=279)

### Mode 32 negative

1. *Shiver (Unbreakable Bonds #1)* — Jocelynn Drake (loading 0.05545, n=174)
2. *The Target* — Gerri Hill (loading 0.04560, n=138)
3. *Artist's Dream* — Gerri Hill (loading 0.04321, n=138)
4. *Two Fangs And A Hoof (Midnight Matings #4)* — Joyee Flynn (loading 0.04087, n=164)
5. *Behind the Pine Curtain* — Gerri Hill (loading 0.03982, n=189)
6. *Bewitched by Bella's Brother* — Amy Lane (loading 0.03952, n=304)
7. *Don't Read in the Closet: Volume Two* — Blaine D. Arden (loading 0.03942, n=102)
8. *Consorting With Dragons* — Sera Trevor (loading 0.03916, n=129)
9. *Bet Me* — Lila Monroe (loading 0.03814, n=350)
10. *Feathers and Filth (Midnight Matings #16)* — Joyee Flynn (loading 0.03809, n=104)
11. *Chance of a Lifetime (Anderson Brothers, #3)* — Marissa Clarke (loading 0.03765, n=103)
12. *Midsummer Baker (Midsummer #4)* — Megan Derr (loading 0.03713, n=116)

### Mode 33 positive

1. *Don't Read in the Closet: Volume Two* — Blaine D. Arden (loading 0.05502, n=102)
2. *Midsummer Baker (Midsummer #4)* — Megan Derr (loading 0.05055, n=116)
3. *Stuff My Stocking: M/M Romance Stories that are Nice and… Naughty* — M.J. O'Shea (loading 0.04965, n=137)
4. *حلفاء الشر* — nbyl frwq (loading 0.04537, n=121)
5. *Broken Fortress (Rifter #6)* — Ginn Hale (loading 0.04295, n=117)
6. *Yours* — Kim Alan (loading 0.04268, n=109)
7. *Alpha Trine (The Valespian Pact #1)* — Lexi Ander (loading 0.04090, n=172)
8. *Bagaikan Puteri (Bagaikan Puteri, #1)* — Ramlee Awang Murshid (loading 0.03925, n=226)
9. *Black Blades (Rifter #3)* — Ginn Hale (loading 0.03809, n=138)
10. *The Iron Temple (Rifter, #9)* — Ginn Hale (loading 0.03802, n=105)
11. *Enemies & Shadows (Rifter #7)* — Ginn Hale (loading 0.03657, n=114)
12. *مهنتي القتل* — nbyl frwq (loading 0.03565, n=108)

### Mode 33 negative

1. *The Millionaire Makeover (Bachelor Auction, #2)* — Naima Simone (loading 0.04930, n=104)
2. *Vendetta (The Nikki Boyd Files #1)* — Lisa Harris (loading 0.04912, n=125)
3. *Hidden Agenda (Southern Crimes, #3)* — Lisa Harris (loading 0.04912, n=101)
4. *Marketing Beef* — Rick Bettencourt (loading 0.04632, n=107)
5. *Super Sock Man (Johnnies, #0.5, Granby Knitting, #1.5)* — Amy Lane (loading 0.04443, n=230)
6. *An Oral Fixation* — Piper Vaughn (loading 0.03859, n=143)
7. *You Are the Reason (The Tav #2)* — Renae Kaye (loading 0.03850, n=158)
8. *For Every Season (Amish Vines and Orchards, #3)* — Cindy Woodsmall (loading 0.03763, n=101)
9. *Winter Chill* — Aria Grace (loading 0.03743, n=139)
10. *Chance of a Lifetime (Anderson Brothers, #3)* — Marissa Clarke (loading 0.03642, n=103)
11. *Over the Top (Maverick Montana, #4)* — Rebecca Zanetti (loading 0.03604, n=142)
12. *Lockdown (Saint Squad, #2)* — Traci Hunter Abramson (loading 0.03582, n=180)

### Mode 34 positive

1. *Too Hard to Forget (Romancing the Clarksons, #3)* — Tessa Bailey (loading 0.05414, n=148)
2. *Stars in Their Eyes (Caught Up in Love, #4)* — Lauren Blakely (loading 0.05064, n=152)
3. *Hers to Command (Verdantia, #1)* — Patricia A. Knight (loading 0.05034, n=178)
4. *A Starstruck Kiss (Caught Up in Love, #3.5)* — Lauren Blakely (loading 0.04910, n=137)
5. *He Completes Me (Home #2)* — Cardeno C. (loading 0.04907, n=323)
6. *Almost Matched (Almost Bad Boys, #1)* — A.O. Peart (loading 0.04782, n=155)
7. *Hidden Desires (Tri-Omega Mates #3)* — Stormy Glenn (loading 0.04652, n=158)
8. *Home Run (The Boys of Summer, #2)* — Heidi McLaughlin (loading 0.04480, n=121)
9. *Sassy in Diapers (Sassy Mates, #4.3)* — Milly Taiden (loading 0.04143, n=156)
10. *At Long Last (Scott and Preston, #1)* — Shawn Lane (loading 0.03994, n=110)
11. *学園アリス 19 [Gakuen Alice 19]* — Tachibana Higuchi (loading 0.03893, n=104)
12. *Forever (From Thirty Days to Forever, #2)* — Shayla Kersten (loading 0.03864, n=113)

### Mode 34 negative

1. *Animal Instincts* — Kim Alan (loading 0.03874, n=124)
2. *Always Watching (Elite Guardians, #1)* — Lynette Eason (loading 0.03784, n=230)
3. *Up in Arms* — Kindle Alexander (loading 0.03740, n=199)
4. *More Than Everything (Family, #3)* — Cardeno C. (loading 0.03719, n=260)
5. *Hidden Agenda (Southern Crimes, #3)* — Lisa Harris (loading 0.03685, n=101)
6. *Sweet Treats (Sweet Perfection, #1)* — Stormy Glenn (loading 0.03605, n=116)
7. *Silver & Black (Silver & Black, #1)* — Tyler May (loading 0.03598, n=168)
8. *Spook Squad (PsyCop, #7)* — Jordan Castillo Price (loading 0.03581, n=311)
9. *Face Value (Sanctuary, #3)* — R.J. Scott (loading 0.03577, n=102)
10. *Full House (Poker Night #5)* — Carol Lynne (loading 0.03517, n=115)
11. *Home of His Own (Home, #2)* — T.A. Chase (loading 0.03482, n=194)
12. *Country Mouse (Country Mouse, #1)* — Amy Lane (loading 0.03389, n=354)

### Mode 35 positive

1. *Sweet Treats (Sweet Perfection, #1)* — Stormy Glenn (loading 0.04596, n=116)
2. *Unearthing Cole (Discovering Me, #1)* — A.M. Arthur (loading 0.04294, n=133)
3. *Kincade's Rose (The Megalodon Team, #1)* — Aliyah Burke (loading 0.04037, n=134)
4. *Unexpected Turn* — Ella Frank (loading 0.03828, n=117)
5. *Curve Ball (Homeruns #2)* — Sloan  Johnson (loading 0.03759, n=112)
6. *Eternally Yours* — Brenda Jackson (loading 0.03702, n=168)
7. *Still* — Mary Calmes (loading 0.03699, n=208)
8. *Seduction, Westmoreland Style (The Westmorelands, #10)* — Brenda Jackson (loading 0.03683, n=184)
9. *Seagrass Pier (Hope Beach, #3)* — Colleen Coble (loading 0.03579, n=150)
10. *Thirty Days (From Thirty Days to Forever, #1)* — Shayla Kersten (loading 0.03545, n=153)
11. *All Play and No Work (Cattle Valley, #1)* — Carol Lynne (loading 0.03527, n=278)
12. *Beyond Temptation (Forged of Steele #3)* — Brenda Jackson (loading 0.03506, n=132)

### Mode 35 negative

1. *At Long Last (Scott and Preston, #1)* — Shawn Lane (loading 0.05250, n=110)
2. *Just For You* — Jet Mykles (loading 0.05013, n=314)
3. *Hidden Desires (Tri-Omega Mates #3)* — Stormy Glenn (loading 0.04758, n=158)
4. *Hope Harbor (Hope Harbor, #1)* — Irene Hannon (loading 0.04755, n=127)
5. *Among the Fair Magnolias: Four Southern Love Stories* — Tamera Alexander (loading 0.04495, n=118)
6. *Forbidden Desires (Tri-Omega Mates #2)* — Stormy Glenn (loading 0.04389, n=186)
7. *The Things We Knew* — Catherine   West (loading 0.04377, n=125)
8. *The Bachelor Girl's Guide to Murder (Herringford and Watts, #1)* — Rachel McMillan (loading 0.04089, n=162)
9. *Hidden Agenda (Southern Crimes, #3)* — Lisa Harris (loading 0.03872, n=101)
10. *Aidan and Ethan (Seeking Redemption, #1)* — Cameron Dane (loading 0.03815, n=330)
11. *Call Me Sir (Sir, #1)* — Stormy Glenn (loading 0.03812, n=142)
12. *A Bride at Last (Unexpected Brides, #3)* — Melissa Jagears (loading 0.03793, n=103)

### Mode 36 positive

1. *JJS: Jalan-Jalan Seram! (Lupus Kecil, #3)* — Hilman Hariwijaya (loading 0.04655, n=297)
2. *Sunatan Masal (Lupus Kecil, #2)* — Hilman Hariwijaya (loading 0.04559, n=297)
3. *Fraternization Rule (Risqué Contracts, #3)* — Fiona Davenport (loading 0.04280, n=119)
4. *Hung: A Billionaire Bad Boy Romance* — Simone Sowood (loading 0.04246, n=106)
5. *A SEAL's Oath (The SEALs of Chance Creek, #1)* — Cora Seton (loading 0.04112, n=148)
6. *Always His (Crazed Devotion #1)* — C.A. Harms (loading 0.04050, n=149)
7. *Lupus Kecil (Lupus Kecil, #1)* — Hilman Hariwijaya (loading 0.04016, n=338)
8. *Turbulent Waters (Billionaire Aviators #3)* — Melody Anne (loading 0.03984, n=126)
9. *Topi-topi Centil* — Hilman Hariwijaya (loading 0.03872, n=317)
10. *Forged in Smoke (Red-Hot SEALs, #3)* — Trish McCallan (loading 0.03859, n=128)
11. *Rurouni Kenshin, Volume 08* — Nobuhiro Watsuki (loading 0.03854, n=348)
12. *Rurouni Kenshin, Volume 10* — Nobuhiro Watsuki (loading 0.03758, n=306)

### Mode 36 negative

1. *Stripped Bare (Vegas Billionaire, #1)* — Heidi McLaughlin (loading 0.03968, n=189)
2. *The Tuscan's Revenge Wedding (Italian Billionaires, #1)* — Jennifer Blake (loading 0.03945, n=143)
3. *Anaconda* — Lauren Landish (loading 0.03903, n=244)
4. *SEAL Under Covers (SEAL Brotherhood #3)* — Sharon Hamilton (loading 0.03531, n=111)
5. *His to Cherish (Fireside, #3)* — Stacey  Lynn (loading 0.03479, n=116)
6. *Anchor (First to Fight Book 1)* — Nicole Blanchard (loading 0.03426, n=144)
7. *Jesse's Diner (Hope, #2)* — Cardeno C. (loading 0.03402, n=172)
8. *Hadley (The Club Girl Diaries #3)* — Addison Jane (loading 0.03378, n=210)
9. *Intimate Deception* — Laura Landon (loading 0.03279, n=276)
10. *Country Kisses (3:AM Kisses, #8)* — Addison Moore (loading 0.03187, n=102)
11. *Hammer (Regulators MC, #2)* — Chelsea Camaron (loading 0.03089, n=136)
12. *Tequila Mockingbird (Sinners #3)* — Rhys Ford (loading 0.03087, n=275)

### Mode 37 positive

1. *Own Me* — Penny Wylder (loading 0.05012, n=125)
2. *A Past Revenge* — Carole Mortimer (loading 0.04422, n=105)
3. *Big Red Lollipop* — Rukhsana Khan (loading 0.04320, n=258)
4. *Somebody Nice!* — Raine O'Tierney (loading 0.04313, n=151)
5. *A Savage Betrayal* — Lynne Graham (loading 0.04242, n=183)
6. *Unearthing Cole (Discovering Me, #1)* — A.M. Arthur (loading 0.03910, n=133)
7. *At Long Last (Scott and Preston, #1)* — Shawn Lane (loading 0.03904, n=110)
8. *Call of the Dragon (Return to Avalore, #1)* — Elianne Adams (loading 0.03878, n=136)
9. *Anatoly Medlov: Complete Reign (The Medlov Crime Family, #3)* — Latrivia S. Nelson (loading 0.03788, n=176)
10. *Darkness Unchained (Sky Brooks, #2)* — McKenzie Hunter (loading 0.03724, n=118)
11. *Infernal Magic (Demons of Fire and Night, #1)* — C.N. Crawford (loading 0.03695, n=138)
12. *Moon Tortured (Sky Brooks, #1)* — McKenzie Hunter (loading 0.03665, n=253)

### Mode 37 negative

1. *A Fool For You (Foolproof Love, #3)* — Katee Robert (loading 0.04728, n=109)
2. *Bagaikan Puteri (Bagaikan Puteri, #1)* — Ramlee Awang Murshid (loading 0.04682, n=226)
3. *Hijab Sang Pencinta (Bagaikan Puteri, #3)* — Ramlee Awang Murshid (loading 0.04640, n=183)
4. *Micah (Marius Brothers #1)* — Joyee Flynn (loading 0.04583, n=200)
5. *Fractured Love* — Ella James (loading 0.04532, n=339)
6. *Mikhail* — Ramlee Awang Murshid (loading 0.04500, n=140)
7. *Home Run (The Boys of Summer, #2)* — Heidi McLaughlin (loading 0.04468, n=121)
8. *Nerds Are Freaks Too* — Koko Brown (loading 0.04363, n=147)
9. *Fiksyen 302* — Ramlee Awang Murshid (loading 0.04237, n=108)
10. *Breathless* — Beverly Jenkins (loading 0.04232, n=105)
11. *The Boy Next Door (Off-Limits Romance #2)* — Ella James (loading 0.04217, n=506)
12. *Something So Perfect (Something So, #2)* — Natasha Madison (loading 0.04212, n=189)

### Mode 38 positive

1. *Unearthing Cole (Discovering Me, #1)* — A.M. Arthur (loading 0.06170, n=133)
2. *My Hero* — Max Vos (loading 0.04506, n=113)
3. *Halley's Bible Handbook: An Abbreviated Bible Commentary* — Henry H. Halley (loading 0.04437, n=112)
4. *Prince Claimed (Thresl Chronicles #2)* — Amber Kell (loading 0.04433, n=116)
5. *Designs of Desire (Desires Entwined, #1)* — Tempeste O'Riley (loading 0.04388, n=134)
6. *Served Hot (Portland Heat, #1)* — Annabeth Albert (loading 0.04222, n=250)
7. *Curve Ball (Homeruns #2)* — Sloan  Johnson (loading 0.04174, n=112)
8. *The Attributes of God* — Arthur W. Pink (loading 0.04079, n=135)
9. *The Challenge of Jesus: Rediscovering Who Jesus Was and Is* — N.T. Wright (loading 0.03974, n=127)
10. *Slave: The Hidden Truth About Your Identity in Christ* — John F. MacArthur Jr. (loading 0.03913, n=126)
11. *Undercover Boyfriend (One Fine Day, #1)* — Jacob Z. Flores (loading 0.03892, n=103)
12. *The Wedding Planner* — G.A. Hauser (loading 0.03841, n=153)

### Mode 38 negative

1. *Dirty Heart (Cole McGinnis, #6)* — Rhys Ford (loading 0.05121, n=105)
2. *The Memory Weaver* — Jane Kirkpatrick (loading 0.04728, n=103)
3. *A Fool For You (Foolproof Love, #3)* — Katee Robert (loading 0.04686, n=109)
4. *A Savage Betrayal* — Lynne Graham (loading 0.04604, n=183)
5. *The Cross of Christ* — John R.W. Stott (loading 0.04435, n=286)
6. *A Matter of Time, Vol. 1 (A Matter of Time #1-2)* — Mary Calmes (loading 0.04372, n=472)
7. *Systematic Theology: An Introduction to Biblical Doctrine* — Wayne A. Grudem (loading 0.04302, n=527)
8. *A Past Revenge* — Carole Mortimer (loading 0.04127, n=105)
9. *Fractured Love* — Ella James (loading 0.03954, n=339)
10. *Breathless* — Beverly Jenkins (loading 0.03921, n=105)
11. *Big Red Lollipop* — Rukhsana Khan (loading 0.03685, n=258)
12. *Heart in Hand (Warder #3)* — Mary Calmes (loading 0.03422, n=273)

### Mode 39 positive

1. *Hung: A Billionaire Bad Boy Romance* — Simone Sowood (loading 0.05318, n=106)
2. *Dragon Mine (North American Dragon #1)* — Joyee Flynn (loading 0.05078, n=162)
3. *Always His (Crazed Devotion #1)* — C.A. Harms (loading 0.04957, n=149)
4. *Just My Type (The Bradfords, #3)* — Erin Nicholas (loading 0.04632, n=146)
5. *A Promise of Hope (Kauffman Amish Bakery, #2)* — Amy Clipston (loading 0.04548, n=225)
6. *An Oral Fixation* — Piper Vaughn (loading 0.04491, n=143)
7. *Breaking Away (Assassins, #5)* — Toni Aleo (loading 0.04435, n=746)
8. *His* — Brenda Rothert (loading 0.04394, n=291)
9. *One Night with Her Bachelor (Montana Born Bachelor Auction #6; Wild Montana Nights, #1)* — Kat Latham (loading 0.04390, n=109)
10. *The Target* — Gerri Hill (loading 0.04350, n=138)
11. *Behind the Pine Curtain* — Gerri Hill (loading 0.04233, n=189)
12. *Artist's Dream* — Gerri Hill (loading 0.04216, n=138)

### Mode 39 negative

1. *Rough Riders* — Jordan Silver (loading 0.05302, n=149)
2. *Don't Read in the Closet: Volume Two* — Blaine D. Arden (loading 0.04415, n=102)
3. *Tryst* — Jordan Silver (loading 0.04340, n=135)
4. *The Billionaire's Virgin* — Penny Wylder (loading 0.04246, n=226)
5. *Every Thug Needs a Lady (Thug #2)* — Wahida Clark (loading 0.04205, n=269)
6. *Duke (Aces MC Series Book 2)* — Aimee-Louise Foster (loading 0.04193, n=118)
7. *Justify My Thug (Thug #5)* — Wahida Clark (loading 0.04101, n=195)
8. *The Dopeman's Wife (The Dopeman, #1)* — JaQuavis Coleman (loading 0.04091, n=221)
9. *Midsummer Baker (Midsummer #4)* — Megan Derr (loading 0.04030, n=116)
10. *Lockdown (Saint Squad, #2)* — Traci Hunter Abramson (loading 0.03964, n=180)
11. *Thug Matrimony (Thug #3)* — Wahida Clark (loading 0.03921, n=271)
12. *What Can Be* — Mary Calmes (loading 0.03898, n=255)

### Mode 40 positive

1. *Guns n' Boys: Book 1, Part 1 (Guns n' Boys, #1)* — K.A. Merikan (loading 0.05058, n=138)
2. *Loving Storm (Ashes & Embers, #5)* — Carian Cole (loading 0.04819, n=121)
3. *Worked Up (Made in Jersey, #3)* — Tessa Bailey (loading 0.04806, n=289)
4. *Sunatan Masal (Lupus Kecil, #2)* — Hilman Hariwijaya (loading 0.04781, n=297)
5. *JJS: Jalan-Jalan Seram! (Lupus Kecil, #3)* — Hilman Hariwijaya (loading 0.04732, n=297)
6. *Lupus Kecil (Lupus Kecil, #1)* — Hilman Hariwijaya (loading 0.04601, n=338)
7. *Stripped Bare (Vegas Billionaire, #1)* — Heidi McLaughlin (loading 0.04486, n=189)
8. *Inked (Bad Boys Next Door, #1)* — Lauren Landish (loading 0.04422, n=198)
9. *Unforgiven* — Ruth Clampett (loading 0.04239, n=132)
10. *Baby Fever Bride* — Nicole Snow (loading 0.04061, n=214)
11. *Intimate Deception* — Laura Landon (loading 0.04026, n=276)
12. *Always His (Crazed Devotion #1)* — C.A. Harms (loading 0.04014, n=149)

### Mode 40 negative

1. *The Degan Incident (Galactic Conspiracies #1)* — Rob Colton (loading 0.04540, n=229)
2. *Red Havoc Bad Bear (Red Havoc Panthers, #5)* — T.S. Joyce (loading 0.04409, n=111)
3. *Red Havoc Rebel (Red Havoc Panthers, #2)* — T.S. Joyce (loading 0.04348, n=160)
4. *Broken Fortress (Rifter #6)* — Ginn Hale (loading 0.04105, n=117)
5. *Red Dirt Christmas (Red Dirt, #3.5)* — N.R. Walker (loading 0.04104, n=110)
6. *You and a Billion Blue Tiles* — Missy Welsh (loading 0.03913, n=121)
7. *Fang And Fur (Midnight Matings #6)* — Stormy Glenn (loading 0.03731, n=196)
8. *Don't Read in the Closet: Volume Two* — Blaine D. Arden (loading 0.03721, n=102)
9. *学園アリス 19 [Gakuen Alice 19]* — Tachibana Higuchi (loading 0.03669, n=104)
10. *Blood Guard (Mission, #1)* — Megan Erickson (loading 0.03589, n=112)
11. *The Iron Temple (Rifter, #9)* — Ginn Hale (loading 0.03539, n=105)
12. *Rough (Biker MC Romance, #2)* — Scott Hildreth (loading 0.03522, n=168)

## Interpretation rule

A mode is structurally credible only if it exceeds the shuffled spectrum and aligns across both disjoint-reader halves. Literary overlap is descriptive post-hoc evidence, not part of mode fitting, orientation, ordering, or acceptance. If literary books appear only in unstable or null-sized modes, the ratings matrix does not support a naturally identifiable single literary axis under this operator.

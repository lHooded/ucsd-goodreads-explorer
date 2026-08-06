# Popularity-ceiling counterfactual

## Design

The catalog ceiling is raised from 80,000 to 400,000 ratings. Everything else remains structurally the same: the jury is fixed, community priors are relearned, publication still requires pair mass 10, and each observed community is capped at 30 evidence units. Total book-evidence caps of 120, 60, and 30 test progressively stronger saturation, preventing mega-read books from buying arbitrarily high precision.

## Result

- Newly admitted mega-read candidates: **54**; central top-50: **0**; central top-200: **3**; cap-30 top-200: **1**. Moderate cap-60/cap-120 top-200 counts are **2** and **2**.
- Raised ceiling versus baseline: Jaccard@50 **0.923**, Jaccard@200 **0.961**, common-rank rho **0.998**.
- Within raised ceiling, uncapped versus total-evidence-cap-30: Jaccard@50 **0.724**, Jaccard@200 **0.887**.

- Moderate cap 60: Jaccard@50/200 **0.786/0.951**; cap 120: **0.923/0.990**.

## Newly admitted mega-read works

| Central | Cap 120 | Cap 60 | Cap 30 | Book | n | Score | Esteem | Heterog. penalty |
|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 83 | 129 | 169 | 201 | *Romeo and Juliet* — William Shakespeare | 125,639 | 56.1 | 73.5 | 15.6 |
| 111 | 123 | 139 | 141 | *The Little Prince* — Antoine de Saint-Exupery | 80,094 | 54.1 | 58.0 | 0.9 |
| 169 | 216 | 261 | 308 | *1984* — George Orwell | 152,321 | 51.2 | 67.4 | 13.9 |
| 439 | 497 | 543 | 578 | *To Kill a Mockingbird* — Harper Lee | 206,684 | 43.2 | 59.9 | 14.0 |
| 597 | 696 | 757 | 822 | *Pride and Prejudice* — Jane Austen | 162,658 | 39.7 | 62.1 | 20.4 |
| 625 | 694 | 743 | 802 | *Wuthering Heights* — Emily Bronte | 85,493 | 38.8 | 56.7 | 15.2 |
| 722 | 772 | 819 | 850 | *Animal Farm* — George Orwell | 148,699 | 36.8 | 54.4 | 15.0 |
| 744 | 745 | 792 | 821 | *The Fellowship of the Ring (The Lord of the Rings, #1)* — J.R.R. Tolkien | 119,871 | 36.2 | 53.4 | 13.6 |
| 829 | 893 | 944 | 976 | *Jane Eyre* — Charlotte Bronte | 105,901 | 34.3 | 58.4 | 21.6 |
| 868 | 885 | 900 | 912 | *Brave New World* — Aldous Huxley | 81,565 | 33.2 | 47.5 | 11.2 |
| 914 | 914 | 912 | 894 | *The Book Thief* — Markus Zusak | 104,480 | 32.1 | 41.7 | 4.2 |
| 935 | 938 | 942 | 940 | *Fahrenheit 451* — Ray Bradbury | 94,041 | 31.5 | 43.9 | 9.0 |
| 940 | 937 | 927 | 916 | *The Hitchhiker's Guide to the Galaxy (Hitchhiker's Guide to the Galaxy, #1)* — Douglas Adams | 82,286 | 31.3 | 42.5 | 7.0 |
| 944 | 960 | 968 | 971 | *Of Mice and Men* — John Steinbeck | 106,388 | 31.2 | 46.7 | 12.5 |
| 989 | 988 | 986 | 970 | *A Game of Thrones (A Song of Ice and Fire, #1)* — George R.R. Martin | 114,688 | 29.1 | 37.2 | 3.2 |
| 1005 | 1008 | 1012 | 1018 | *The Hobbit* — J.R.R. Tolkien | 154,068 | 28.2 | 45.4 | 13.8 |
| 1036 | 1036 | 1036 | 1041 | *Insurgent (Divergent, #2)* — Veronica Roth | 99,234 | 26.6 | 38.0 | 5.1 |
| 1043 | 1043 | 1042 | 1042 | *The Help* — Kathryn Stockett | 98,134 | 26.2 | 35.9 | 4.2 |
| 1046 | 1059 | 1064 | 1075 | *The Great Gatsby* — F. Scott Fitzgerald | 180,225 | 25.9 | 46.4 | 18.2 |
| 1064 | 1069 | 1070 | 1072 | *The Catcher in the Rye* — J.D. Salinger | 146,781 | 24.4 | 37.0 | 10.2 |
| 1065 | 1064 | 1057 | 1049 | *The Lion, the Witch, and the Wardrobe (Chronicles of Narnia, #1)* — C.S. Lewis | 110,663 | 24.3 | 35.7 | 7.1 |
| 1067 | 1065 | 1065 | 1070 | *The Perks of Being a Wallflower* — Stephen Chbosky | 91,852 | 24.1 | 33.1 | 3.5 |
| 1068 | 1066 | 1066 | 1073 | *The Lightning Thief (Percy Jackson and the Olympians, #1)* — Rick Riordan | 97,530 | 24.1 | 35.2 | 5.0 |
| 1083 | 1083 | 1082 | 1077 | *The Fault in Our Stars* — John Green | 174,858 | 22.4 | 30.8 | 3.4 |
| 1085 | 1085 | 1085 | 1071 | *Harry Potter and the Deathly Hallows (Harry Potter, #7)* — J.K. Rowling | 178,374 | 22.2 | 31.0 | 4.2 |
| 1088 | 1088 | 1089 | 1078 | *The Giver (The Giver, #1)* — Lois Lowry | 98,482 | 21.9 | 29.9 | 3.1 |
| 1090 | 1090 | 1091 | 1091 | *Lord of the Flies* — William Golding | 120,254 | 21.7 | 34.8 | 10.2 |
| 1095 | 1095 | 1094 | 1094 | *Gone Girl* — Gillian Flynn | 108,871 | 21.1 | 30.3 | 3.9 |
| 1096 | 1096 | 1096 | 1102 | *New Moon (Twilight, #2)* — Stephenie Meyer | 120,318 | 20.5 | 30.7 | 4.6 |
| 1097 | 1097 | 1099 | 1105 | *Breaking Dawn (Twilight, #4)* — Stephenie Meyer | 112,600 | 19.7 | 30.8 | 5.4 |
| 1098 | 1100 | 1101 | 1107 | *Eclipse (Twilight, #3)* — Stephenie Meyer | 116,643 | 19.4 | 29.8 | 4.8 |
| 1099 | 1099 | 1100 | 1092 | *Harry Potter and the Goblet of Fire (Harry Potter, #4)* — J.K. Rowling | 183,770 | 19.4 | 26.1 | 2.2 |
| 1104 | 1102 | 1102 | 1097 | *The Time Traveler's Wife* — Audrey Niffenegger | 85,620 | 19.3 | 27.7 | 3.5 |
| 1105 | 1105 | 1106 | 1112 | *Divergent (Divergent, #1)* — Veronica Roth | 161,403 | 19.2 | 29.6 | 4.6 |
| 1107 | 1106 | 1098 | 1098 | *The Kite Runner* — Khaled Hosseini | 110,575 | 19.1 | 33.0 | 9.9 |
| 1110 | 1110 | 1110 | 1111 | *Catching Fire (The Hunger Games, #2)* — Suzanne Collins | 182,350 | 18.4 | 27.1 | 3.5 |
| 1112 | 1112 | 1112 | 1101 | *Harry Potter and the Half-Blood Prince (Harry Potter, #6)* — J.K. Rowling | 174,713 | 17.8 | 25.1 | 2.8 |
| 1114 | 1114 | 1115 | 1118 | *Mockingjay (The Hunger Games, #3)* — Suzanne Collins | 172,277 | 17.2 | 26.0 | 3.7 |
| 1115 | 1115 | 1116 | 1119 | *Little Women (Little Women, #1)* — Louisa May Alcott | 96,001 | 17.1 | 36.9 | 16.5 |
| 1116 | 1116 | 1114 | 1103 | *The Girl with the Dragon Tattoo (Millennium, #1)* — Stieg Larsson | 111,028 | 16.9 | 22.7 | 1.7 |
| 1118 | 1118 | 1117 | 1113 | *Harry Potter and the Prisoner of Azkaban (Harry Potter, #3)* — J.K. Rowling | 192,417 | 16.5 | 25.8 | 4.9 |
| 1122 | 1121 | 1120 | 1114 | *Harry Potter and the Order of the Phoenix (Harry Potter, #5)* — J.K. Rowling | 177,929 | 15.9 | 22.8 | 2.5 |
| 1124 | 1124 | 1125 | 1126 | *Fifty Shades of Grey (Fifty Shades, #1)* — E.L. James | 99,559 | 13.8 | 22.0 | 3.4 |
| 1125 | 1125 | 1126 | 1130 | *The Girl on the Train* — Paula Hawkins | 96,296 | 13.8 | 22.4 | 3.6 |
| 1126 | 1126 | 1124 | 1129 | *Harry Potter and the Sorcerer's Stone (Harry Potter, #1)* — J.K. Rowling | 305,142 | 13.5 | 22.7 | 6.0 |
| 1127 | 1127 | 1129 | 1127 | *Harry Potter and the Chamber of Secrets (Harry Potter, #2)* — J.K. Rowling | 190,342 | 12.4 | 20.1 | 3.7 |
| 1128 | 1128 | 1127 | 1128 | *Memoirs of a Geisha* — Arthur Golden | 93,755 | 12.0 | 22.1 | 6.4 |
| 1129 | 1129 | 1130 | 1125 | *The Lovely Bones* — Alice Sebold | 102,035 | 12.0 | 18.0 | 1.8 |
| 1130 | 1130 | 1128 | 1123 | *The Hunger Games (The Hunger Games, #1)* — Suzanne Collins | 288,704 | 11.9 | 17.0 | 1.2 |
| 1131 | 1132 | 1132 | 1131 | *Twilight (Twilight, #1)* — Stephenie Meyer | 235,067 | 7.8 | 15.2 | 4.0 |
| 1132 | 1131 | 1131 | 1133 | *The Alchemist* — Paulo Coelho | 113,184 | 7.5 | 20.3 | 10.7 |
| 1133 | 1133 | 1133 | 1132 | *Angels & Demons  (Robert Langdon, #1)* — Dan Brown | 117,318 | 6.9 | 11.4 | 1.6 |
| 1134 | 1134 | 1134 | 1134 | *The Da Vinci Code (Robert Langdon, #2)* — Dan Brown | 132,203 | 4.8 | 8.2 | 1.2 |
| — | — | — | — | *City of Bones (The Mortal Instruments, #1)* — Cassandra Clare | 110,137 | 31.0 | 42.8 | 5.2 |

## External top-30 and motivating books

| Book | External ranks | Baseline | Raised | Cap 120 | Cap 60 | Cap 30 | Score ±u |
|---|---|---:|---:|---:|---:|---:|---:|
| *Ulysses* | lit_2014_2024:5, greatestbooks_2026:1, love_default:18 | 295 | 238 | 262 | 356 | 478 | 48.4 ±9.0 |
| *The Brothers Karamazov* | lit_2014_2024:2, greatestbooks_2026:18, love_default:1 | 1 | 1 | 2 | 2 | 2 | 83.7 ±3.6 |
| *Moby-Dick or, The Whale* | lit_2014_2024:1, greatestbooks_2026:6, love_default:72 | 273 | 227 | 278 | 345 | 428 | 48.7 ±6.8 |
| *Infinite Jest* | lit_2014_2024:6, love_default:2 | 25 | 30 | 28 | 22 | 29 | 64.2 ±6.4 |
| *Crime and Punishment* | lit_2014_2024:4, greatestbooks_2026:13, love_default:3 | 4 | 4 | 7 | 9 | 6 | 76.4 ±6.9 |
| *The Great Gatsby* | lit_2014_2024:62, greatestbooks_2026:3 | — | 1046 | 1059 | 1064 | 1075 | 25.9 ±6.3 |
| *Lolita* | lit_2014_2024:3, greatestbooks_2026:11, love_default:29 | 263 | 209 | 271 | 337 | 417 | 49.3 ±8.3 |
| *One Hundred Years of Solitude* | lit_2014_2024:21, greatestbooks_2026:4, love_default:16 | 40 | 34 | 44 | 60 | 70 | 63.0 ±5.8 |
| *2666* | lit_2014_2024:24, love_default:4 | 33 | 36 | 34 | 30 | 25 | 62.5 ±6.8 |
| *Blood Meridian, or the Evening Redness in the West* | lit_2014_2024:8, love_default:5 | 50 | 56 | 55 | 50 | 80 | 59.3 ±6.4 |
| *The Catcher in the Rye* | lit_2014_2024:30, greatestbooks_2026:5 | — | 1064 | 1069 | 1070 | 1072 | 24.4 ±5.9 |
| *Stoner* | lit_2014_2024:11, love_default:6 | 23 | 23 | 23 | 18 | 15 | 65.0 ±6.8 |
| *1984* | lit_2014_2024:22, greatestbooks_2026:7, love_default:67 | — | 169 | 216 | 261 | 308 | 51.2 ±6.8 |
| *Life and Fate* | love_default:7 | 182 | 193 | 191 | 186 | 173 | 50.0 ±8.1 |
| *Don Quixote* | lit_2014_2024:7, greatestbooks_2026:8, love_default:44 | 51 | 46 | 54 | 75 | 100 | 60.4 ±6.1 |
| *In the Shadow of Young Girls in Flower (In Search of Lost Time, #2)* | love_default:8 | 45 | 51 | 49 | 43 | 26 | 59.8 ±7.4 |
| *The Book of Disquiet* | lit_2014_2024:31, love_default:9 | 35 | 37 | 36 | 31 | 21 | 62.4 ±7.0 |
| *The Sound and the Fury* | lit_2014_2024:32, greatestbooks_2026:9, love_default:55 | 42 | 38 | 41 | 63 | 89 | 62.0 ±6.5 |
| *Gravity's Rainbow* | lit_2014_2024:9, love_default:21 | 128 | 127 | 127 | 118 | 171 | 53.1 ±7.6 |
| *Anna Karenina* | lit_2014_2024:14, greatestbooks_2026:10, love_default:48 | 16 | 13 | 21 | 23 | 20 | 69.4 ±4.1 |
| *Time Regained (In Search of Lost Time, #7)* | love_default:10 | 97 | 108 | 105 | 101 | 84 | 54.3 ±7.9 |
| *Hamlet* | lit_2014_2024:20, greatestbooks_2026:75, love_default:11 | 2 | 2 | 1 | 1 | 1 | 83.6 ±3.0 |
| *The Stranger* | lit_2014_2024:12, greatestbooks_2026:23 | 147 | 130 | 184 | 233 | 303 | 52.9 ±6.5 |
| *War and Peace* | lit_2014_2024:16, greatestbooks_2026:12, love_default:12 | 15 | 10 | 19 | 26 | 27 | 69.7 ±6.3 |
| *The Divine Comedy* | lit_2014_2024:13, greatestbooks_2026:28, love_default:42 | 14 | 16 | 14 | 13 | 12 | 69.0 ±5.3 |
| *Tutunamayanlar* | love_default:13 | 153 | 175 | 172 | 167 | 149 | 50.9 ±8.2 |
| *Wuthering Heights* | lit_2014_2024:63, greatestbooks_2026:14 | — | 625 | 694 | 743 | 802 | 38.8 ±6.9 |
| *The Library of Babel* | love_default:14 | 140 | 158 | 155 | 154 | 134 | 51.6 ±8.3 |
| *Swann's Way (In Search of Lost Time, #1)* | love_default:15 | 27 | 29 | 27 | 32 | 40 | 64.5 ±6.1 |
| *Pride and Prejudice* | greatestbooks_2026:15 | — | 597 | 696 | 757 | 822 | 39.7 ±7.7 |
| *The Iliad* | lit_2014_2024:15, greatestbooks_2026:37, love_default:95 | 28 | 24 | 29 | 38 | 44 | 64.8 ±7.2 |
| *To Kill a Mockingbird* | greatestbooks_2026:16 | — | 439 | 497 | 543 | 578 | 43.2 ±5.7 |
| *The Odyssey* | lit_2014_2024:17, greatestbooks_2026:26, love_default:70 | 55 | 44 | 62 | 77 | 97 | 60.9 ±6.7 |
| *Journey to the End of the Night* | lit_2014_2024:29, greatestbooks_2026:49, love_default:17 | 26 | 28 | 26 | 24 | 31 | 64.7 ±5.9 |
| *The Trial* | lit_2014_2024:18, greatestbooks_2026:20 | 110 | 96 | 120 | 185 | 269 | 55.4 ±7.6 |
| *The Master and Margarita* | lit_2014_2024:33, greatestbooks_2026:34, love_default:19 | 6 | 6 | 5 | 7 | 5 | 74.4 ±4.2 |
| *Madame Bovary* | lit_2014_2024:74, greatestbooks_2026:19 | 606 | 520 | 550 | 607 | 651 | 41.3 ±7.7 |
| *The Marriage of Heaven and Hell* | love_default:20 | 92 | 104 | 102 | 97 | 78 | 54.7 ±7.9 |
| *The Last Question* | love_default:22 | — | — | — | — | — | 47.1 ±8.6 |
| *The Adventures of Huckleberry Finn* | greatestbooks_2026:22 | 510 | 421 | 469 | 522 | 564 | 43.5 ±6.3 |
| *Life A User's Manual* | love_default:23 | 178 | 191 | 189 | 183 | 167 | 50.2 ±8.1 |
| *Notes from Underground* | lit_2014_2024:23 | 24 | 25 | 24 | 20 | 24 | 64.8 ±6.3 |
| *The Story of a New Name (The Neapolitan Novels #2)* | love_default:24 | 350 | 365 | 368 | 360 | 349 | 44.7 ±8.2 |
| *Middlemarch* | greatestbooks_2026:24 | 141 | 140 | 137 | 156 | 206 | 52.6 ±6.6 |
| *To the Lighthouse* | lit_2014_2024:56, greatestbooks_2026:25 | 54 | 52 | 48 | 66 | 77 | 59.8 ±5.9 |
| *Pale Fire* | lit_2014_2024:42, greatestbooks_2026:70, love_default:25 | 76 | 78 | 79 | 74 | 119 | 56.4 ±6.8 |
| *Faust* | lit_2014_2024:25, greatestbooks_2026:94 | 52 | 55 | 53 | 48 | 39 | 59.4 ±7.0 |
| *East of Eden* | lit_2014_2024:40, love_default:26 | 36 | 31 | 30 | 35 | 37 | 63.1 ±6.4 |
| *Dubliners* | lit_2014_2024:27 | 243 | 221 | 218 | 269 | 334 | 48.9 ±7.4 |
| *The Grapes of Wrath* | lit_2014_2024:80, greatestbooks_2026:27 | 117 | 106 | 111 | 142 | 172 | 54.5 ±7.6 |
| *Four Quartets* | love_default:27 | 77 | 75 | 75 | 70 | 54 | 56.7 ±7.5 |
| *Catch-22 (Catch-22, #1)* | lit_2014_2024:28, greatestbooks_2026:35 | 248 | 210 | 206 | 246 | 289 | 49.3 ±6.1 |
| *Suttree* | love_default:28 | 138 | 153 | 150 | 146 | 126 | 51.9 ±8.0 |
| *The Magic Mountain* | lit_2014_2024:48, greatestbooks_2026:29, love_default:50 | 19 | 21 | 20 | 16 | 19 | 66.8 ±5.7 |
| *The Waste Land* | love_default:30 | 31 | 32 | 31 | 27 | 32 | 63.1 ±6.5 |
| *Jane Eyre* | greatestbooks_2026:30 | — | 829 | 893 | 944 | 976 | 34.3 ±8.1 |

## Interpretation

A newly admitted book that remains high under cap 30 has broad jury esteem, not merely a precision advantage. A book that ranks low in both paths is absent for substantive rating/community reasons. A large uncapped-to-capped fall is the signature of evidence-volume leverage.

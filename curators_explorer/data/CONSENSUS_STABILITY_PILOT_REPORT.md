# Focused pilot: community-robust literary consensus

## Question

Does the rebuilt jury contain a shared canonical core, or does its head depend on particular latent reader communities? Clusters are used only to perturb and audit the ranking—not to nominate books.

## Design

- Current rich behavioral jury: **4,929** users; embedding pool: **20,000**.
- User embedding: centered rating residuals over **32,578** books, truncated to 24 dimensions.
- Partitions: k=[6, 10, 16] × seeds=[11, 29, 47] = **9** alternatives.
- Universes: **159** balanced/leave-one-out/random reweightings plus **96** community-only diagnostics.
- Ranking: fixed within-user 5★ versus ≤3★ pair samples; user reweighting changes only precomputed sufficient statistics.

## Perturbation stability

| perturbation | n | mean J@50 | worst J@50 | mean J@200 | worst J@200 | mean RBO |
|---|---:|---:|---:|---:|---:|---:|
| equal_community | 9 | 0.749 | 0.695 | 0.753 | 0.739 | 0.852 |
| leave_one_out | 96 | 0.809 | 0.515 | 0.842 | 0.606 | 0.887 |
| random_reweight | 54 | 0.779 | 0.613 | 0.810 | 0.695 | 0.867 |

## Pilot result

- **157** books are mixture-stable: they remain top-200 in at least 80% of perturbations.
- **34** of those meet all stricter cross-community tests.
- The other **123** are stable for the current jury mixture but retain a detectable taste-community dependency.
- This supports a compact shared core followed by contested tiers, rather than a single defensible total order extending far down the list.

## Distributed robust core

A deliberately stricter tier: top-200 in at least 80% of mixture perturbations, top-200 in at least 50% of community-only rankings, normalized support concentration no more than 0.25, and worst observed leave-one-community-out drop no more than 100 places. These thresholds are descriptive and were not optimized against a probe list.

| book | base | median | top200 | community top200 | norm. concentration | worst LOO drop* |
|---|---:|---:|---:|---:|---:|---:|
| Hamlet — William Shakespeare | 1 | 2 | 100% | 100% | 0.066 | 3.0 |
| The Brothers Karamazov — Fyodor Dostoyevsky | 2 | 2 | 100% | 96% | 0.086 | 2.0 |
| Crime and Punishment — Fyodor Dostoyevsky | 3 | 3 | 100% | 100% | 0.076 | 5.0 |
| War and Peace — Leo Tolstoy | 6 | 6 | 100% | 94% | 0.055 | 12.0 |
| Shakespeare's Sonnets — William Shakespeare | 5 | 6 | 100% | 51% | 0.066 | 15.0 |
| Les Misérables — Victor Hugo | 8 | 8 | 100% | 98% | 0.060 | 24.0 |
| Macbeth — William Shakespeare | 10 | 9 | 100% | 96% | 0.084 | 63.0 |
| The Magic Mountain — Thomas Mann | 9 | 10 | 100% | 51% | 0.072 | 10.0 |
| The Idiot — Fyodor Dostoyevsky | 13 | 14 | 100% | 86% | 0.130 | 42.0 |
| Anna Karenina — Leo Tolstoy | 15 | 16 | 100% | 100% | 0.042 | 22.0 |
| Faust: First Part — Johann Wolfgang von Goethe | 16 | 16 | 100% | 55% | 0.084 | 27.0 |
| The Master and Margarita — Mikhail Bulgakov | 17 | 17 | 100% | 79% | 0.083 | 58.0 |
| The Adventures of Sherlock Holmes — Arthur Conan Doyle | 20 | 21 | 100% | 66% | 0.090 | 77.0 |
| Paradise Lost — John Milton | 22 | 24 | 100% | 99% | 0.026 | 30.0 |
| The Count of Monte Cristo — Alexandre Dumas | 26 | 24 | 100% | 91% | 0.076 | 77.0 |
| King Lear — William Shakespeare | 27 | 26 | 100% | 94% | 0.043 | 56.0 |
| Les Fleurs du Mal — Charles Baudelaire | 28 | 30 | 100% | 61% | 0.032 | 21.0 |
| One Hundred Years of Solitude — Gabriel Garcia Marquez | 31 | 32 | 100% | 100% | 0.028 | 24.0 |
| The Divine Comedy — Dante Alighieri | 32 | 34 | 100% | 83% | 0.028 | 66.0 |
| The Odyssey — Homer | 33 | 35 | 100% | 98% | 0.027 | 49.0 |
| Inferno (The Divine Comedy #1) — Dante Alighieri | 34 | 37 | 100% | 68% | 0.040 | 27.0 |
| Don Quixote — Miguel de Cervantes Saavedra | 44 | 45 | 100% | 90% | 0.035 | 44.0 |
| Leaves of Grass — Walt Whitman | 47 | 48 | 100% | 71% | 0.030 | 40.0 |
| The Iliad — Homer | 49 | 51 | 100% | 94% | 0.019 | 62.0 |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 54 | 59 | 100% | 79% | 0.083 | 96.0 |
| Waiting for Godot — Samuel Beckett | 67 | 70 | 100% | 68% | 0.057 | 28.0 |
| The Death of Ivan Ilych — Leo Tolstoy | 74 | 76 | 100% | 67% | 0.075 | 98.0 |
| East of Eden — John Steinbeck | 81 | 78 | 100% | 74% | 0.022 | 42.0 |
| If on a Winter's Night a Traveler — Italo Calvino | 82 | 84 | 100% | 54% | 0.094 | 63.0 |
| Alice's Adventures in Wonderland & Through the Looking-Glass — Lewis Carroll | 88 | 92 | 100% | 92% | 0.009 | 44.0 |
| Dead Souls — Nikolai Gogol | 91 | 93 | 100% | 59% | 0.079 | 34.0 |
| A Streetcar Named Desire — Tennessee Williams | 105 | 108 | 100% | 72% | 0.035 | 93.0 |
| The Name of the Rose — Umberto Eco | 137 | 146 | 100% | 61% | 0.043 | 60.0 |
| All Quiet on the Western Front — Erich Maria Remarque | 165 | 169 | 91% | 71% | 0.036 | 57.0 |

## Mixture-stable but community-dependent

These books survive at least 80% of mixture perturbations but fail one or more distributed-core tests. They are the main candidates for taste-community bias, not books to delete automatically.

| book | base | median | top200 | community top200 | norm. concentration | worst LOO drop* |
|---|---:|---:|---:|---:|---:|---:|
| Tehlikeli Oyunlar — Oguz Atay | 38 | 37 | 95% | 10% | 0.326 | 463.0 |
| Pale Fire — Vladimir Nabokov | 58 | 59 | 95% | 20% | 0.214 | 443.0 |
| Giovanni's Room — James     Baldwin | 41 | 43 | 99% | 11% | 0.201 | 439.0 |
| Heart of Darkness and The Secret Sharer — Joseph Conrad | 64 | 61 | 99% | 12% | 0.254 | 437.0 |
| In the Shadow of Young Girls in Flower (In Search of Lost Time, #2) — Marcel Proust | 76 | 78 | 92% | 14% | 0.199 | 425.0 |
| Resurrection — Leo Tolstoy | 87 | 86 | 95% | 18% | 0.237 | 414.0 |
| Ulysses — James Joyce | 73 | 73 | 94% | 77% | 0.094 | 405.0 |
| The Insulted and Humiliated — Fyodor Dostoyevsky | 101 | 104 | 92% | 22% | 0.183 | 400.0 |
| North and South — Elizabeth Gaskell | 116 | 115 | 89% | 19% | 0.252 | 385.0 |
| The Life and Opinions of Tristram Shandy, Gentleman — Laurence Sterne | 125 | 133 | 87% | 22% | 0.159 | 376.0 |
| The Castle — Franz Kafka | 90 | 91 | 94% | 32% | 0.180 | 367.0 |
| Endgame & Act Without Words — Samuel Beckett | 136 | 136 | 86% | 16% | 0.159 | 365.0 |
| Blood Meridian, or the Evening Redness in the West — Cormac McCarthy | 52 | 57 | 96% | 24% | 0.233 | 364.0 |
| Suttree — Cormac McCarthy | 139 | 140 | 84% | 5% | 0.146 | 362.0 |
| The Tin Drum — Gunter Grass | 144 | 143 | 84% | 29% | 0.113 | 357.0 |
| The Street of Crocodiles — Bruno Schulz | 147 | 146 | 82% | 9% | 0.255 | 354.0 |
| Jane Eyre — Charlotte Bronte | 148 | 149 | 83% | 82% | 0.151 | 353.0 |
| The Moon and Sixpence — W. Somerset Maugham | 150 | 148 | 84% | 7% | 0.086 | 346.0 |
| The Glass Bead Game — Hermann Hesse | 158 | 163 | 86% | 30% | 0.141 | 343.0 |
| The Good Soldier Švejk — Jaroslav Hasek | 141 | 141 | 85% | 12% | 0.175 | 333.0 |
| A Tale of Two Cities — Charles Dickens | 169 | 168 | 84% | 84% | 0.082 | 332.0 |
| Absalom, Absalom! — William Faulkner | 69 | 72 | 96% | 23% | 0.125 | 331.0 |
| All the Pretty Horses (The Border Trilogy, #1) — Cormac McCarthy | 134 | 145 | 85% | 14% | 0.104 | 327.0 |
| To the Lighthouse — Virginia Woolf | 157 | 164 | 84% | 60% | 0.048 | 323.0 |
| Gravity's Rainbow — Thomas Pynchon | 18 | 19 | 99% | 28% | 0.177 | 319.0 |
| Lost Illusions — Honore de Balzac | 128 | 132 | 91% | 10% | 0.084 | 319.0 |
| Selected Poetry — John Keats | 107 | 111 | 94% | 2% | 0.154 | 316.0 |
| The Dead — James Joyce | 45 | 44 | 98% | 21% | 0.169 | 312.0 |
| Lolita — Vladimir Nabokov | 85 | 84 | 95% | 100% | 0.056 | 303.0 |
| The Rings of Saturn — W.G. Sebald | 89 | 88 | 96% | 9% | 0.171 | 298.0 |
| Os Maias — Eca de Queiros | 109 | 111 | 99% | 1% | 0.098 | 283.0 |
| Blindness — Jose Saramago | 126 | 133 | 90% | 29% | 0.138 | 272.0 |
| Othello — William Shakespeare | 72 | 74 | 97% | 94% | 0.100 | 261.0 |
| Autobiography of Red — Anne Carson | 94 | 96 | 94% | 7% | 0.123 | 255.0 |
| Doctor Faustus — Thomas Mann | 138 | 137 | 84% | 14% | 0.163 | 252.0 |

## Fragile books from the baseline top 200

| book | base | top200 | median | q90 | community top200 | max LOO drop |
|---|---:|---:|---:|---:|---:|---:|
| The Remains of the Day — Kazuo Ishiguro | 198 | 50% | 201 | 270 | 18% | 303 |
| King Henry IV, Part 1 (Wars of the Roses, #2) — William Shakespeare | 200 | 50% | 201 | 265 | 16% | 264 |
| Narcissus and Goldmund — Hermann Hesse | 193 | 52% | 199 | 239 | 40% | 94 |
| The Tell-Tale Heart — Edgar Allan Poe | 192 | 54% | 195 | 242 | 7% | 128 |
| Cry, the Beloved Country — Alan Paton | 195 | 55% | 193 | 264 | 8% | 199 |
| The Seagull — Anton Chekhov | 190 | 57% | 193 | 265 | 27% | 119 |
| A Midsummer Night's Dream — William Shakespeare | 197 | 58% | 193 | 267 | 79% | 304 |
| Germinal (Les Rougon-Macquart, #13) — Emile Zola | 191 | 58% | 191 | 253 | 29% | 184 |
| Persuasion — Jane Austen | 199 | 59% | 188 | 394 | 46% | 302 |
| Jakob von Gunten — Robert Walser | 189 | 60% | 182 | 241 | 2% | 312 |
| Tlön, Uqbar, Orbis Tertius — Jorge Luis Borges | 196 | 61% | 180 | 318 | 2% | 305 |
| The Cask of Amontillado — Edgar Allan Poe | 194 | 61% | 182 | 277 | 10% | 198 |
| Beware of Pity — Stefan Zweig | 177 | 62% | 176 | 276 | 1% | 237 |
| Paris Spleen — Charles Baudelaire | 182 | 64% | 181 | 263 | 14% | 312 |
| The Heart of the Matter — Graham Greene | 186 | 67% | 187 | 256 | 20% | 115 |
| White Noise — Don DeLillo | 187 | 67% | 187 | 308 | 19% | 314 |
| The Waste Land — T.S. Eliot | 188 | 67% | 189 | 253 | 35% | 151 |
| Middlemarch — George Eliot | 181 | 67% | 183 | 266 | 51% | 147 |
| The Memoirs of Sherlock Holmes — Arthur Conan Doyle | 185 | 68% | 177 | 266 | 17% | 316 |
| A Suitable Boy (A Suitable Boy, #1) — Vikram Seth | 179 | 69% | 175 | 261 | 3% | 204 |
| Martin Eden — Jack London | 180 | 70% | 177 | 281 | 19% | 152 |
| The Marriage of Heaven and Hell — William Blake | 170 | 71% | 166 | 281 | 8% | 331 |
| Wuthering Heights — Emily Bronte | 184 | 71% | 178 | 248 | 92% | 317 |
| Life and Fate — Vasily Grossman | 154 | 73% | 157 | 285 | 10% | 347 |
| Faust — Johann Wolfgang von Goethe | 176 | 74% | 178 | 240 | 22% | 117 |
| And Then There Were None — Agatha Christie | 173 | 74% | 179 | 226 | 66% | 113 |
| The Valley of Fear — Arthur Conan Doyle | 151 | 75% | 145 | 265 | 10% | 350 |
| Winnie-the-Pooh (Winnie-the-Pooh, #1) — A.A. Milne | 172 | 75% | 173 | 225 | 34% | 78 |
| The Tempest — William Shakespeare | 156 | 76% | 162 | 238 | 56% | 251 |
| Oedipus Rex  (The Theban Plays, #1) — Sophocles | 174 | 76% | 177 | 249 | 57% | 234 |
| The Twelve Chairs — Ilya Ilf | 167 | 76% | 157 | 251 | 0% | 166 |
| The Betrothed — Alessandro Manzoni | 168 | 76% | 163 | 244 | 4% | 164 |
| A Modest Proposal and Other Satirical Works — Jonathan Swift | 160 | 77% | 174 | 239 | 7% | 180 |
| Of Human Bondage — W. Somerset Maugham | 183 | 77% | 181 | 216 | 17% | 104 |
| The War of the End of the World — Mario Vargas Llosa | 153 | 77% | 138 | 326 | 7% | 348 |

## Russian-literature dependence check

Author-name diagnostic only; it never enters ranking or clustering.

| book | base | median | top200 | community top200 | norm. concentration | worst LOO drop* |
|---|---:|---:|---:|---:|---:|---:|
| The Brothers Karamazov — Fyodor Dostoyevsky | 2 | 2 | 100% | 96% | 0.086 | 2 |
| Crime and Punishment — Fyodor Dostoyevsky | 3 | 3 | 100% | 100% | 0.076 | 5 |
| War and Peace — Leo Tolstoy | 6 | 6 | 100% | 94% | 0.055 | 12 |
| Demons — Fyodor Dostoyevsky | 7 | 8 | 100% | 42% | 0.266 | 121 |
| Notes from Underground — Fyodor Dostoyevsky | 11 | 11 | 100% | 34% | 0.136 | 31 |
| The Idiot — Fyodor Dostoyevsky | 13 | 14 | 100% | 86% | 0.130 | 42 |
| Anna Karenina — Leo Tolstoy | 15 | 16 | 100% | 100% | 0.042 | 22 |
| The Master and Margarita — Mikhail Bulgakov | 17 | 17 | 100% | 79% | 0.083 | 58 |
| The Overcoat — Nikolai Gogol | 40 | 42 | 100% | 29% | 0.096 | 58 |
| The Grand Inquisitor — Fyodor Dostoyevsky | 46 | 43 | 96% | 9% | 0.171 | 210 |
| Notes from Underground, White Nights, The Dream of a Ridiculous Man, and Selections from The House of the Dead — Fyodor Dostoyevsky | 54 | 59 | 100% | 79% | 0.083 | 96 |
| Pale Fire — Vladimir Nabokov | 58 | 59 | 95% | 20% | 0.214 | 443 |
| The House of the Dead — Fyodor Dostoyevsky | 71 | 72 | 100% | 14% | 0.222 | 34 |
| The Death of Ivan Ilych — Leo Tolstoy | 74 | 76 | 100% | 67% | 0.075 | 98 |
| Lolita — Vladimir Nabokov | 85 | 84 | 95% | 100% | 0.056 | 303 |
| Resurrection — Leo Tolstoy | 87 | 86 | 95% | 18% | 0.237 | 414 |
| Dead Souls — Nikolai Gogol | 91 | 93 | 100% | 59% | 0.079 | 34 |
| The Insulted and Humiliated — Fyodor Dostoyevsky | 101 | 104 | 92% | 22% | 0.183 | 400 |
| Cancer Ward — Aleksandr Solzhenitsyn | 104 | 109 | 100% | 8% | 0.103 | 96 |
| Heart of a Dog — Mikhail Bulgakov | 113 | 117 | 94% | 26% | 0.132 | 193 |
| Doctor Zhivago — Boris Pasternak | 115 | 119 | 98% | 35% | 0.033 | 99 |
| Eugene Onegin — Alexander Pushkin | 117 | 120 | 96% | 58% | 0.049 | 125 |
| Life and Fate — Vasily Grossman | 154 | 157 | 73% | 10% | 0.109 | 347 |
| The Seagull — Anton Chekhov | 190 | 193 | 57% | 27% | 0.086 | 119 |
| A Hero of Our Time — Mikhail Lermontov | 266 | 278 | 4% | 38% | 0.092 | 179 |
| Fathers and Sons — Ivan Turgenev | 292 | 293 | 0% | 56% | 0.067 | 65 |
| Despair — Vladimir Nabokov | 310 | 302 | 1% | 1% | 0.169 | 191 |
| The Little Tragedies — Alexander Pushkin | 318 | 302 | 8% | 5% | 0.264 | 183 |
| The Gift — Vladimir Nabokov | 335 | 336 | 1% | 0% | 0.122 | 166 |
| White Nights — Fyodor Dostoyevsky | 344 | 350 | 1% | 26% | 0.173 | 157 |
| The Nose — Nikolai Gogol | 353 | 355 | 0% | 12% | 0.108 | 148 |
| The Inspector General — Nikolai Gogol | 376 | 365 | 1% | 8% | 0.199 | 125 |
| Tales of Belkin and Other Prose Writings — Alexander Pushkin | 410 | 407 | 3% | 3% | 0.181 | 91 |
| One Day in the Life of Ivan Denisovich — Aleksandr Solzhenitsyn | 441 | 446 | 0% | 30% | 0.043 | 60 |
| We — Yevgeny Zamyatin | 487 | 483 | 0% | 18% | 0.112 | 14 |
| Village Evenings Near Dikanka and Mirgorod — Nikolai Gogol | 496 | 484 | 1% | 12% | 0.327 | 5 |

## Example community heads

One seed at each resolution is shown to interpret—not endorse—the partitions.

### k6_s11

- C0 (current n=491): Crime and Punishment — Fyodor Dostoyevsky; Hamlet — William Shakespeare; The Brothers Karamazov — Fyodor Dostoyevsky
- C1 (current n=664): Hamlet — William Shakespeare; The Count of Monte Cristo — Alexandre Dumas; The Adventures of Sherlock Holmes — Arthur Conan Doyle
- C2 (current n=448): Anne of Green Gables (Anne of Green Gables, #1) — L.M. Montgomery; The Count of Monte Cristo — Alexandre Dumas; Hamlet — William Shakespeare
- C3 (current n=1315): Lolita — Vladimir Nabokov; Moby-Dick or, The Whale — Herman Melville; Ulysses — James Joyce
- C4 (current n=940): Hamlet — William Shakespeare; Jane Eyre — Charlotte Bronte; Macbeth — William Shakespeare
- C5 (current n=1071): Crime and Punishment — Fyodor Dostoyevsky; The Brothers Karamazov — Fyodor Dostoyevsky; War and Peace — Leo Tolstoy

### k10_s11

- C0 (current n=409): Crime and Punishment — Fyodor Dostoyevsky; The Brothers Karamazov — Fyodor Dostoyevsky; Hamlet — William Shakespeare
- C1 (current n=935): Lolita — Vladimir Nabokov; Ulysses — James Joyce; Moby-Dick or, The Whale — Herman Melville
- C2 (current n=333): The Brothers Karamazov — Fyodor Dostoyevsky; The Count of Monte Cristo — Alexandre Dumas; The Master and Margarita — Mikhail Bulgakov
- C3 (current n=302): Hamlet — William Shakespeare; The Brothers Karamazov — Fyodor Dostoyevsky; Macbeth — William Shakespeare
- C4 (current n=500): Jane Eyre — Charlotte Bronte; Les Misérables — Victor Hugo; Anna Karenina — Leo Tolstoy
- C5 (current n=471): The Count of Monte Cristo — Alexandre Dumas; The Adventures of Sherlock Holmes — Arthur Conan Doyle; Hamlet — William Shakespeare
- C6 (current n=277): Hamlet — William Shakespeare; Crime and Punishment — Fyodor Dostoyevsky; Jane Eyre — Charlotte Bronte
- C7 (current n=621): Hamlet — William Shakespeare; Macbeth — William Shakespeare; Othello — William Shakespeare
- C8 (current n=273): Anne of Green Gables (Anne of Green Gables, #1) — L.M. Montgomery; A Christmas Carol — Charles Dickens; Hamlet — William Shakespeare
- C9 (current n=808): Crime and Punishment — Fyodor Dostoyevsky; The Brothers Karamazov — Fyodor Dostoyevsky; War and Peace — Leo Tolstoy

### k16_s11

- C0 (current n=332): Crime and Punishment — Fyodor Dostoyevsky; Hamlet — William Shakespeare; The Brothers Karamazov — Fyodor Dostoyevsky
- C1 (current n=749): Lolita — Vladimir Nabokov; Ulysses — James Joyce; The Sound and the Fury — William Faulkner
- C2 (current n=254): Hamlet — William Shakespeare; The Brothers Karamazov — Fyodor Dostoyevsky; Mrs. Dalloway — Virginia Woolf
- C3 (current n=274): Hamlet — William Shakespeare; The Brothers Karamazov — Fyodor Dostoyevsky; Macbeth — William Shakespeare
- C4 (current n=288): Jane Eyre — Charlotte Bronte; Sense and Sensibility — Jane Austen; Persuasion — Jane Austen
- C5 (current n=340): The Metamorphosis — Franz Kafka; The Stranger — Albert Camus; One Hundred Years of Solitude — Gabriel Garcia Marquez
- C6 (current n=131): Hamlet — William Shakespeare; The Picture of Dorian Gray — Oscar Wilde; Les Misérables — Victor Hugo
- C7 (current n=479): Hamlet — William Shakespeare; Macbeth — William Shakespeare; King Lear — William Shakespeare
- C8 (current n=206): Jane Eyre — Charlotte Bronte; Anne of Green Gables (Anne of Green Gables, #1) — L.M. Montgomery; A Christmas Carol — Charles Dickens
- C9 (current n=549): The Brothers Karamazov — Fyodor Dostoyevsky; Crime and Punishment — Fyodor Dostoyevsky; War and Peace — Leo Tolstoy
- C10 (current n=154): Hamlet — William Shakespeare; The Idiot — Fyodor Dostoyevsky; The Stranger — Albert Camus
- C11 (current n=310): The Count of Monte Cristo — Alexandre Dumas; Les Misérables — Victor Hugo; A Tale of Two Cities — Charles Dickens
- C12 (current n=125): Hamlet — William Shakespeare; Crime and Punishment — Fyodor Dostoyevsky; The Odyssey — Homer
- C13 (current n=309): Crime and Punishment — Fyodor Dostoyevsky; Hamlet — William Shakespeare; The Brothers Karamazov — Fyodor Dostoyevsky
- C14 (current n=289): Hamlet — William Shakespeare; The Two Towers (The Lord of the Rings, #2) — J.R.R. Tolkien; The Fellowship of the Ring (The Lord of the Rings, #1) — J.R.R. Tolkien
- C15 (current n=140): Hamlet — William Shakespeare; The Brothers Karamazov — Fyodor Dostoyevsky; Crime and Punishment — Fyodor Dostoyevsky

## Interpretation guardrails

- Normalized concentration uses per-capita positive support: 0 means perfectly even community support and 1 means support confined to one community. Normalization makes different k values comparable.
- *Rankings retain only their top 500. A worst LOO drop ending at rank 501 therefore means the book fell outside the saved ranking; the reported drop is a censored lower bound, not its exact final rank.
- Random resampling tests variance; community perturbations test mixture dependence. Neither proves objective literary value.
- A dense local canon can be perfectly stable inside one community. It belongs in the global core only if support is distributed and leave-one-out movement is small.
- Goodreads exposure is still missing-not-at-random. Cross-community rank stability cannot repair books that communities never jointly encounter.
- The honest result may be a small shared core followed by contested tiers rather than one precise total order.

## Recommendation

The pilot supports a small cross-community core, but not one broad total consensus. Proceed to the larger jury/specification multiverse while preserving the distinction between robust-core and community-dependent/contested tiers.

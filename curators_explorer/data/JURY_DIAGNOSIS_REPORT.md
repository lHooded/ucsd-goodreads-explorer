# Jury diagnosis: focus vs deep curators

Question: is the messy pairwise list about **who we listen to**, or **how we order books**?

## Overlap

- Behavioral focus (top affinity slice): **4,774** users
- Deep curators (all): **19,841**
- Deep capped to same size: **4,774** (highest curator weights)
- Focus ∩ deep(all): **1,957** (41.0% of focus)
- Focus ∩ deep(capped): **871** (Jaccard **0.100**)
- Mean classic_affinity: focus=20.53, deep_capped=15.30
- Mean series_share: focus=0.093, deep_capped=0.100

## Most common 5★ books (same jury size)

Top-25 Jaccard focus vs deep-equal: **0.389**; vs deep-weighted: **0.282**

### Focus jury

- 1. Jane Eyre — Charlotte Bronte (users=1360, exposure=28.5%)
- 2. Hamlet — William Shakespeare (users=1268, exposure=26.6%)
- 3. Crime and Punishment — Fyodor Dostoyevsky (users=1217, exposure=25.5%)
- 4. Lolita — Vladimir Nabokov (users=1069, exposure=22.4%)
- 5. Anna Karenina — Leo Tolstoy (users=1057, exposure=22.1%)
- 6. One Hundred Years of Solitude — Gabriel Garcia Marquez (users=1049, exposure=22.0%)
- 7. Wuthering Heights — Emily Bronte (users=1023, exposure=21.4%)
- 8. The Adventures of Huckleberry Finn — Mark Twain (users=981, exposure=20.5%)
- 9. The Little Prince — Antoine de Saint-Exupery (users=974, exposure=20.4%)
- 10. The Picture of Dorian Gray — Oscar Wilde (users=923, exposure=19.3%)
- 11. The Grapes of Wrath — John Steinbeck (users=900, exposure=18.9%)
- 12. The Stranger — Albert Camus (users=887, exposure=18.6%)
- 13. Frankenstein — Mary Wollstonecraft Shelley (users=886, exposure=18.6%)
- 14. Of Mice and Men — John Steinbeck (users=871, exposure=18.2%)
- 15. The Odyssey — Homer (users=829, exposure=17.4%)

### Deep capped (equal count)

- 1. Crime and Punishment — Fyodor Dostoyevsky (users=2116, exposure=44.3%)
- 2. The Brothers Karamazov — Fyodor Dostoyevsky (users=1741, exposure=36.5%)
- 3. One Hundred Years of Solitude — Gabriel Garcia Marquez (users=1524, exposure=31.9%)
- 4. Lolita — Vladimir Nabokov (users=1514, exposure=31.7%)
- 5. The Stranger — Albert Camus (users=1410, exposure=29.5%)
- 6. The Metamorphosis — Franz Kafka (users=1254, exposure=26.3%)
- 7. The Trial — Franz Kafka (users=1148, exposure=24.0%)
- 8. Anna Karenina — Leo Tolstoy (users=1124, exposure=23.5%)
- 9. Hamlet — William Shakespeare (users=1091, exposure=22.9%)
- 10. The Master and Margarita — Mikhail Bulgakov (users=1084, exposure=22.7%)
- 11. Moby-Dick or, The Whale — Herman Melville (users=1018, exposure=21.3%)
- 12. Slaughterhouse-Five — Kurt Vonnegut Jr. (users=1005, exposure=21.1%)
- 13. War and Peace — Leo Tolstoy (users=994, exposure=20.8%)
- 14. Ulysses — James Joyce (users=960, exposure=20.1%)
- 15. The Odyssey — Homer (users=923, exposure=19.3%)

### Deep capped (weight-summed 5★s)

- 1. Crime and Punishment — Fyodor Dostoyevsky (users=2116, exposure=44.3%)
- 2. The Brothers Karamazov — Fyodor Dostoyevsky (users=1741, exposure=36.5%)
- 3. Lolita — Vladimir Nabokov (users=1514, exposure=31.7%)
- 4. One Hundred Years of Solitude — Gabriel Garcia Marquez (users=1524, exposure=31.9%)
- 5. The Stranger — Albert Camus (users=1410, exposure=29.5%)
- 6. The Metamorphosis — Franz Kafka (users=1254, exposure=26.3%)
- 7. The Trial — Franz Kafka (users=1148, exposure=24.0%)
- 8. Ulysses — James Joyce (users=960, exposure=20.1%)
- 9. Anna Karenina — Leo Tolstoy (users=1124, exposure=23.5%)
- 10. The Master and Margarita — Mikhail Bulgakov (users=1084, exposure=22.7%)
- 11. Moby-Dick or, The Whale — Herman Melville (users=1018, exposure=21.3%)
- 12. Hamlet — William Shakespeare (users=1091, exposure=22.9%)
- 13. War and Peace — Leo Tolstoy (users=994, exposure=20.8%)
- 14. The Sound and the Fury — William Faulkner (users=893, exposure=18.7%)
- 15. Slaughterhouse-Five — Kurt Vonnegut Jr. (users=1005, exposure=21.1%)

## Within-jury pairwise (no anti contrast)

| method | pos50 | anti50 | filler50 | sticky50 | heldout@50 | heldout@200 |
|---|---:|---:|---:|---:|---:|---:|
| pairwise_focus_equal | 19 | 0 | 0 | 6 | 0.209 | 0.605 |
| pairwise_deep_capped_equal | 38 | 0 | 0 | 9 | 0.326 | 0.651 |
| pairwise_deep_capped_weighted | 38 | 0 | 0 | 9 | 0.326 | 0.651 |

Pairwise top50 Jaccard focus↔deep_eq=**0.235**, focus↔deep_w=**0.235**

### Pairwise — focus equal

- 1. The Brothers Karamazov — Fyodor Dostoyevsky (pair_n=1772.0, exposure_5=14.8%)
- 2. Crime and Punishment — Fyodor Dostoyevsky (pair_n=3466.0, exposure_5=25.5%)
- 3. Hamlet — William Shakespeare (pair_n=3158.0, exposure_5=26.6%)
- 4. Les Fleurs du Mal — Charles Baudelaire (pair_n=561.0, exposure_5=4.7%)
- 5. Four Quartets — T.S. Eliot (pair_n=235.0, exposure_5=2.5%)
- 6. Leaves of Grass — Walt Whitman (pair_n=842.0, exposure_5=8.9%)
- 7. Stoner — John  Williams (pair_n=705.0, exposure_5=5.3%)
- 8. The Things They Carried — Tim O'Brien (pair_n=763.0, exposure_5=7.2%)
- 9. Les Misérables — Victor Hugo (pair_n=2182.0, exposure_5=17.2%)
- 10. Rebecca — Daphne du Maurier (pair_n=1273.0, exposure_5=12.3%)
- 11. Anna Karenina — Leo Tolstoy (pair_n=2783.0, exposure_5=22.1%)
- 12. War and Peace — Leo Tolstoy (pair_n=1433.0, exposure_5=13.8%)
- 13. Journey to the End of the Night — Louis-Ferdinand Celine (pair_n=470.0, exposure_5=3.3%)
- 14. Gravity's Rainbow — Thomas Pynchon (pair_n=304.0, exposure_5=2.4%)
- 15. Anne of Green Gables (Anne of Green Gables, #1) — L.M. Montgomery (pair_n=1305.0, exposure_5=10.8%)

### Pairwise — deep capped equal

- 1. Crime and Punishment — Fyodor Dostoyevsky (pair_n=6412.0, exposure_5=44.3%)
- 2. The Brothers Karamazov — Fyodor Dostoyevsky (pair_n=5694.0, exposure_5=36.5%)
- 3. Stoner — John  Williams (pair_n=1229.0, exposure_5=8.6%)
- 4. War and Peace — Leo Tolstoy (pair_n=2570.0, exposure_5=20.8%)
- 5. Gravity's Rainbow — Thomas Pynchon (pair_n=1654.0, exposure_5=10.1%)
- 6. 2666 — Roberto Bolano (pair_n=1260.0, exposure_5=10.1%)
- 7. East of Eden — John Steinbeck (pair_n=1524.0, exposure_5=12.0%)
- 8. The Dead — James Joyce (pair_n=326.0, exposure_5=2.8%)
- 9. Infinite Jest — David Foster Wallace (pair_n=2342.0, exposure_5=13.5%)
- 10. Swann's Way (In Search of Lost Time, #1) — Marcel Proust (pair_n=1955.0, exposure_5=12.8%)
- 11. The Trial — Franz Kafka (pair_n=2832.0, exposure_5=24.0%)
- 12. Les Fleurs du Mal — Charles Baudelaire (pair_n=718.0, exposure_5=7.5%)
- 13. The Magic Mountain — Thomas Mann (pair_n=1415.0, exposure_5=11.0%)
- 14. Four Quartets — T.S. Eliot (pair_n=342.0, exposure_5=3.6%)
- 15. Demons — Fyodor Dostoyevsky (pair_n=1758.0, exposure_5=10.5%)

### Pairwise — deep capped weighted

- 1. Crime and Punishment — Fyodor Dostoyevsky (pair_n=6412.0, exposure_5=44.3%)
- 2. The Brothers Karamazov — Fyodor Dostoyevsky (pair_n=5694.0, exposure_5=36.5%)
- 3. Gravity's Rainbow — Thomas Pynchon (pair_n=1654.0, exposure_5=10.1%)
- 4. Stoner — John  Williams (pair_n=1229.0, exposure_5=8.6%)
- 5. 2666 — Roberto Bolano (pair_n=1260.0, exposure_5=10.1%)
- 6. War and Peace — Leo Tolstoy (pair_n=2570.0, exposure_5=20.8%)
- 7. The Magic Mountain — Thomas Mann (pair_n=1415.0, exposure_5=11.0%)
- 8. Infinite Jest — David Foster Wallace (pair_n=2342.0, exposure_5=13.5%)
- 9. The Dead — James Joyce (pair_n=326.0, exposure_5=2.8%)
- 10. East of Eden — John Steinbeck (pair_n=1524.0, exposure_5=12.0%)
- 11. Demons — Fyodor Dostoyevsky (pair_n=1758.0, exposure_5=10.5%)
- 12. The Divine Comedy — Dante Alighieri (pair_n=1037.0, exposure_5=9.9%)
- 13. Four Quartets — T.S. Eliot (pair_n=342.0, exposure_5=3.6%)
- 14. Pale Fire — Vladimir Nabokov (pair_n=1255.0, exposure_5=10.5%)
- 15. The Master and Margarita — Mikhail Bulgakov (pair_n=3376.0, exposure_5=22.7%)

## How to read this

- **Low overlap + different common books** → we have been listening to a different crowd than deep curators.
- **Deep pairwise looks good / focus pairwise messy** → jury selection is the main issue.
- **Both pairwise lists look alike (good or bad)** → ordering method (or shared data limits) dominates.

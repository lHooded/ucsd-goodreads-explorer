# Fast co-training (16GB-safe)

Single process, capped user/edge pools — no multi-process matrix copies.

## Veto: **REJECTED**

- J50 stability dropped

- start J50=0.42, best J50=0.38
- start anti≈9.90, best anti≈0.10

## Rounds

- round 1: proxy=-40.15 improved=True sticky50=3 anti50=6 (3.5s)
- round 2: proxy=-7.59 improved=True sticky50=1 anti50=2 (3.5s)
- round 3: proxy=-4.42 improved=True sticky50=1 anti50=2 (3.5s)
- round 4: proxy=6.67 improved=True sticky50=0 anti50=0 (3.6s)
- round 5: proxy=10.89 improved=True sticky50=1 anti50=0 (3.5s)
- round 6: proxy=21.96 improved=True sticky50=3 anti50=0 (3.5s)
- round 7: proxy=21.96 improved=False sticky50=3 anti50=0 (3.5s)
- round 8: proxy=25.18 improved=True sticky50=4 anti50=0 (3.5s)
- round 9: proxy=27.99 improved=True sticky50=5 anti50=0 (3.5s)
- round 10: proxy=27.99 improved=False sticky50=5 anti50=0 (3.5s)

## Top 15

- 1. A Tale of Two Cities — Charles Dickens
- 2. Where the Sidewalk Ends — Shel Silverstein
- 3. Charlotte's Web — E.B. White
- 4. Frankenstein — Mary Wollstonecraft Shelley
- 5. The Adventures of Huckleberry Finn — Mark Twain
- 6. Gone with the Wind — Margaret Mitchell
- 7. Holes (Holes, #1) — Louis Sachar
- 8. Thirteen Reasons Why — Jay Asher
- 9. The Odyssey — Homer
- 10. Charlie and the Chocolate Factory (Charlie Bucket, #1) — Roald Dahl
- 11. Inkheart (Inkworld, #1) — Cornelia Funke
- 12. A Wrinkle in Time (A Wrinkle in Time Quintet, #1) — Madeleine L'Engle
- 13. Hamlet — William Shakespeare
- 14. The Golden Compass (His Dark Materials, #1) — Philip Pullman
- 15. Macbeth — William Shakespeare
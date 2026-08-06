# Residual enthusiasm ranking

Same careful focus/anti cohorts; book score = shrunk residual enthusiasm
(focus − anti), with baselines for user generosity and book appeal removed.
Missing anti evidence contributes **0**, not a positive bonus.

## Probe metrics (no anti-median Q bonus)

| method | Q_clean | pos50 | anti50 | filler50 | sticky50 | miss-anti@50 | heldout recall@200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy_p5 | 66.5 | 24 | 0 | 2 | 25 | 0.00 | 0.395 |
| fixed_p5 | -40.5 | 24 | 0 | 2 | 25 | 0.00 | 0.395 |
| residual | 59.0 | 26 | 0 | 6 | 20 | 0.00 | 0.419 |
| residual_bilateral | -31.0 | 27 | 0 | 6 | 21 | 0.00 | 0.395 |
| residual_no_author | 61.5 | 28 | 0 | 6 | 21 | 0.00 | 0.419 |
| residual_bilateral_no_author | -36.0 | 28 | 0 | 6 | 21 | 0.00 | 0.395 |

## Best residual variant top 15 (`residual_no_author`)

- 1. Hamlet — William Shakespeare (n_c=1886.0, n_a=462.0)
- 2. Moby-Dick or, The Whale — Herman Melville (n_c=1504.0, n_a=324.0)
- 3. Lolita — Vladimir Nabokov (n_c=2061.0, n_a=154.0)
- 4. Macbeth — William Shakespeare (n_c=1529.0, n_a=411.0)
- 5. Crime and Punishment — Fyodor Dostoyevsky (n_c=1926.0, n_a=134.0)
- 6. The Odyssey — Homer (n_c=1663.0, n_a=627.0)
- 7. Les Misérables — Victor Hugo (n_c=1303.0, n_a=349.0)
- 8. The Grapes of Wrath — John Steinbeck (n_c=1678.0, n_a=225.0)
- 9. The Poisonwood Bible — Barbara Kingsolver (n_c=1086.0, n_a=111.0)
- 10. The Adventures of Huckleberry Finn — Mark Twain (n_c=2152.0, n_a=865.0)
- 11. Anna Karenina — Leo Tolstoy (n_c=1834.0, n_a=189.0)
- 12. Charlotte's Web — E.B. White (n_c=1387.0, n_a=719.0)
- 13. Paradise Lost — John Milton (n_c=761.0, n_a=52.0)
- 14. King Lear — William Shakespeare (n_c=903.0, n_a=131.0)
- 15. One Hundred Years of Solitude — Gabriel Garcia Marquez (n_c=1844.0, n_a=170.0)

## Legacy p5 top 15 (for contrast)

- 1. Hamlet — William Shakespeare
- 2. Paradise Lost — John Milton
- 3. A Streetcar Named Desire — Tennessee Williams
- 4. Moby-Dick or, The Whale — Herman Melville
- 5. Mrs. Dalloway — Virginia Woolf
- 6. Crime and Punishment — Fyodor Dostoyevsky
- 7. Lolita — Vladimir Nabokov
- 8. Ulysses — James Joyce
- 9. The Poisonwood Bible — Barbara Kingsolver
- 10. Macbeth — William Shakespeare
- 11. The Arabian Nights — Anonymous
- 12. The Trial — Franz Kafka
- 13. Peter Pan (A Little Golden Book) — Eugene Bradley Coco
- 14. Heart of Darkness — Joseph Conrad
- 15. The Grapes of Wrath — John Steinbeck

## Notes

- Weights: careful cotrain freeze (`weights_careful_cotrain.json`).
- Iterative sparse weights kept separately as `weights_iter_sparse.json`.
- Shrinkage k=40.0, default author blend=0.3.
- `fixed_p5` here = bilateral p5 contrast (requires anti support). Head metrics match legacy, but anti floods ranks 51–1000 so Q_clean collapses.
- Best residual variant: `residual_no_author` — pos50 28, held-out@200 0.419 (legacy 0.395); more school-canon/filler; sticky 21 vs 25.
- Real tradeoff: better identification vs modernist sticky core.

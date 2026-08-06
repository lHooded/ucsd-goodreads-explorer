# Author-level literary consensus — probe results

Discovery uses `(user_id, work_id, rating, author_id)` with `author_id` from
Goodreads `author_url`. Taste/poll labels are **evaluation only**.

## Why author?

Book-level co-5★ clustering produced **author islands** (Joyce↔Joyce,
Pynchon↔Pynchon). Adding author is not “more of the same”: it is Airoldi’s
nested level (work → artist). Person×author reflections / PMI should connect
Dostoevsky↔Joyce readers without requiring book-pair co-citation.
Cross-author book PMI drops same-author edges explicitly.

Literature that motivates this:

- Lizardo 2018 — reflections on person×cultural-item (item can be artist)
- Vlegels & Lievens 2017 (*Poetics*) — ground-up clustering of **artist** preferences
- Airoldi 2024 — nested legitimacy (genre → artist → work)
- arXiv:2303.05080 — explicitly suggests author-similarity networks over book ones on Goodreads

## Verdict

**Author helps the theory and the multi-canon story; it does not unlock the Anglophone lit poll.**

| method | author Q | a_pos50 | a_anti50 | work Q | w_pos50 | w_anti50 | head |
|---|---:|---:|---:|---:|---:|---:|---|
| author_neg_delta2 | 0.0 | 0 | 0 | 0.0 | 0 | 0 | MC romance (Nina Levine, Ryan Michele, …) |
| author_niche_enthusiasts | 0.0 | 0 | 0 | 7.3 | 0 | 0 | same MC-romance block |
| author_high_order | 0.0 | 0 | 0 | 6.8 | 0 | 0 | same |
| author_pmi_portfolio | -4.2 | 0 | 1 | -2.9 | 0 | 1 | M/M romance communities |
| cross_author_book_pmi | — | — | — | -2.6 | 0 | 0 | Arabic literary (Ashour, Towfik, Barghouti, …) |

### Diagnostics (61/62 poll authors in the author graph)

- Under `−δ²`, poll authors sit around **mean rank ~12.6k / 14.8k** (worst half).
- Mid-pop filter (`max_work_n ∈ [3k,100k]`, 1670 authors): poll mean rank still **~1221 / 1670**.
- Heads of `−δ²` / niche metrics = tightly co-liked **romance** authors; high `δ¹` heads = **children’s picture-book** authors (omnivore-parent audiences).

Interpretation: literary-poll authors are **diffuse prestige hubs** (many casual 5★s from omnivores). Romance MC / MM authors form **dense local islands**. Reflections and PMI amplify density, so they promote genre canons, not syllabus canons — consistent with Feldkamp (crowd structure ≠ expert canonicity) and Walsh (Goodreads “classics” ≠ academic canon).

`cross_author_book_pmi` still surfaces the Arabic literary cluster after removing same-author edges — author IDs help *de-island* the book graph for multilingual canons, without recovering `lit-2014-2024`.

## Caching / runtime

- Mid-pop book graph, PMI adjacency, and reflections are **process-cached** in
  `research_ratings_only_canon.py` (`clear_graph_caches()` at run start).
- Author bipartite loaded **once**; reflections(iters=14) reused across
  `neg_delta2` / `niche` / `high_order` (~208s first, then ~0.4–4s).
- Full author suite ≈ 7 minutes wall (dominated by one reflections + one PMI + cross-author pairs).

## Scholar Labs query

```
bipartite person-author OR person-artist taste network OR
"method of reflections" OR "two-mode" cultural hierarchy OR
omnivorousness ranking authors books OR Goodreads co-reading
author similarity literary canon prestige -recommendation
-collaborative-filtering
```

Secondary:

```
"artist preferences" network clustering omnivore Poetics
OR nested cultural legitimacy genre artist work digital traces
OR Goodreads author co-occurrence canon vs popular
```

Seeds: Lizardo 2018; Vlegels & Lievens 2017; Airoldi 2024; Hidalgo–Hausmann reflections; arXiv:2303.05080; Feldkamp et al. 2024 JCLS.

## Implied next moves (if continuing)

1. Treat author as a **nesting/debias** tool (cross-author edges, author-community portfolio UI) — not as a global prestige ranker for Anglophone lit.
2. For Anglophone poll specifically: ratings(+author) still look underdetermined without a seed/taste prior (back to curator packs) **or** an external proxy (syllabi, prizes, translation graphs).
3. Product: multi-canon explorer (Arabic / Indonesian / romance-dense / … community heads) rather than one Western classics leaderboard.

# Chat History

## User
You are picking up where another agent left off. This task is data-sciency and fuzzy. Please continue their work.
[JURY_REBUILD_HANDOFF.md](curators_explorer/data/JURY_REBUILD_HANDOFF.md)

## User
Before you keep going I want to make sure we're on the same page. What's the main goal here? What are we trying to achieve?

## User
Ok, sounds like we are on the same page. Can I just quickly ask what features you used when trying to filter the jurors?

## User
Just for your reference, here's the original jury filtering system:
The winning metric has two layers: **score users**, then **score books from two user cohorts**.

### 1. Per-user features (unseeded)
From each user’s ratings + book + author (+ year), e.g.:

- `series_share_5` — fraction of their 5★ titles that look like series (`#` in title)
- `binge_mean_5` — average number of 5★s per author
- `mega_catalog_share_5` — fraction of 5★s on ultra-popular books
- `mean_logn_5` — how popular their 5★ books are on average
- `midpop_span_per_logn5` — how many mid-popularity authors they 5★, scaled by activity
- `mean_pub_year_5`, `depth_ge4`, author HHI, etc.

Each feature \(x\) is turned into a z-score vs all users:

\[
z(x) = \frac{x - \mu_x}{\sigma_x}
\]

### 2. Three raw “likeness” scores
Linear combinations of those z-scores (coefficients from the three-way contrast):

\[
\begin{aligned}
\text{classic\_raw}
&= -1.5\,z(\text{series}) - 1.4\,z(\text{year}) - 1.3\,z(\text{mega}) \\
&\quad + 1.2\,z(\text{midpop span}) - 1.0\,z(\text{mean log }n) + \cdots \\[0.5em]
\text{anti\_raw}
&= +1.6\,z(\text{series}) + 1.2\,z(\text{binge}) + 1.0\,z(\text{HHI}) + \cdots \\[0.5em]
\text{normie\_raw}
&= +1.5\,z(\text{mega}) + 1.3\,z(\text{mean log }n) + 0.8\,z(\text{p5 blockbuster}) + \cdots
\end{aligned}
\]

Intuition: **classic_raw** rewards older, non-series, mid-pop-author-spanning tastes; **anti_raw** rewards series binge; **normie_raw** rewards school-blockbuster concentration.

### 3. Net classic focus
\[
\text{classic\_focus}
= \text{classic\_raw}
- 0.85\,\text{anti\_raw}
- 0.75\,\text{normie\_raw}
\]

Then hard gates (must pass all):

- `series_share_5 ≤ 0.40`
- `mega_catalog_share_5 ≤ 0.28`
- `binge_mean_5 ≤ 2.8`
- `midpop_span_per_logn5 ≥ 3`

### 4. Contrastive book score (the one with Q≈72)
Among gated users, take the top ~6% by `classic_focus` → cohort \(C\).  
Separately, take high-`anti_raw` series/binge users → cohort \(A\).

For each book:

\[
\text{score}(b) = P(5^\star \mid C) - P(5^\star \mid A)
\]

(with a fallback if \(A\) has too few ratings on \(b\)). Books need enough ratings in \(C\) (and ideally \(A\)).

So a book rises only if **classic-focus users love it more than anti-like users do** — not merely if classic-focus users like it in absolute terms (that weaker version still let some contemporary favorites through).

Seeds were used only to *learn* which features/coefficients separate the three groups; at scoring time a user’s `classic_focus` does not count hits on the lit/anti/normie lists.



You can take inspiration from it if needed.

Ok, as you were.

## User
This looks promising. It appears we've copied the russian-lit leaning from the original poll. There are also definitely other biases. To me this feels like an impossible question, but is there a way to help find and remove biases? To try and find the 'canonical literary consensus' (of those who have goodreads accounts)? I think using stability as a metric is the most obvious path. To me it feels intuitive, that if there does exist some 'canonical literary consensus' then it would be the most stable - removing sets of jurors / changing weights / etc would result in the least amount of change. To me this sounds like a problem of finding and comparing local maximums of stability - issue is we would need some efficient way to measure stability. I also have a tiny inkling that analysing the trajectory (search workspace for that term to get an idea of what I mean if you don't know) of different books may somehow help. Not too sure though, just throwing ideas at the wall.

I've outlined my rudimentary ideas for a solution to this possibly impossible problem. If you have any other approaches that might work, please suggest them.

## User
Sorry to interrupt you, but if you ever need me to download any papers for you, just ask.

As you were.

## User
Hmm I do like this idea and am happy to go ahead with it. However, I did try some clustering approaches before originally reverse engineering the jury from the taste signals (see [RATINGS_ONLY_CANON_REPORT.md](curators_explorer/data/RATINGS_ONLY_CANON_REPORT.md) and [AUTHOR_LEVEL_CANON_REPORT.md](curators_explorer/data/AUTHOR_LEVEL_CANON_REPORT.md) ) but didn't have much luck. Do you think your approach will be more successful, and why?

## User
Ok, the focused pilot sounds good. Go ahead with it.

## User
I actually don't mind Russian literature being near the top, I was just using it as an example. But the goal of this task is still to find some distributed 'literary canonical consensus'. Also, wouldn't some books not appear in certain communities just because they aren't popular enough? You mentioned that some Russian classics are community dependent, is this just because they are rarer? How do we account for this? I understand that popularity comes into play when talking about canons, but I should specify further - I want to find some notion of a less popularity dependent literary distributed canon. Obviously to have enough data at least some number of readers must have read a book, but in general I want to minimise the role of popularity. Is this even possible and what does this change in our approach?

## User
Just had a quick thought (very inspired by you) for the end result. Because there's going to be uncertainty in the score assigned to each novel, we can display the uncertainty to the right of the score (± u). Not that this matters right now.

Anyway, yeah the proposed changes look good. Go ahead.

## User
What do you mean by enthusiast self-selection, and how do you intend to bound it?

## User
Ok that sounds good. You mentioned in your previous message that "run jury/pair-definition trajectories" should also be included in the next work - does it make sense to do them together? If so, go ahead, otherwise just continue with bounding enthusiast self-selection.

## User
Good stuff. Continue in your suggested direction.

## User
You seem to be doing well so far and I am happy to continue to follow your direction.

I am going to go to bed soon and can leave my computer on overnight, but I want to be careful with token usage - I don't want unnecessary usage overnight. Are there some ~8 hour extensive tests you can design that will further our goal? We would need to run a trimmed version first to bugtest.

## User
Just correcting a slight typo, what can be run overnight shouldn't just be restricted to tests. They could be anything that is useful.

## User
Ok I'm up. I had a couple of thoughts I had overnight:
- Cluster/canon participation isn't a black and white thing. Is it time we assign multiple weights to each user detailing how much they are in each group. I'd imagine this would lead to better results, but it could muddy/slow down the research. Is this the right time to do it? Or should we wait? Or even never? I'm open to suggestions.
- I realised that having a timestamp that a user rated a book would be useful for analysing self-selection bias. Firstly, does the dataset (https://cseweb.ucsd.edu/~jmcauley/datasets/goodreads.html) even have this data? And if so, do you think it's worth it?

## User
Ok that sounds mostly good. Alternatively you could start the 11GB download now, do your step 1, skip step 2, do step 3 and once it's downloaded, either do step 4 directly or a pilot (which doesn't have to be just the fantasy subset, since we've just downloaded the full file) depending on the results from previous steps. Does this order offer any disadvantages to your proposed order? Maybe step 3 was waiting on step 2 somehow? If neither, go with my suggestion.

## User
Just a checkup.

## User
Are there any other potentially useful columns within the extended 11GB archive we downloaded? Can you give me an overview of the current best ranking with stats (trajectories, uncertainty, number of readers, etc). What do you think the best direction from here would be?

## User
Plan sounds good. Continue.

## User
Hmm, intuitively that top five does feel better but it definitely could be due to popularity bias - hard to say.

Continue as planned.

## User
Good stuff. I agree with your proposed direction. Continue.

## User
More good stuff. Before moving on, can you give me an overview of where we're at and how much further you think we can push this? In this explanation, try to minimise jargon.

## User
Ok, sounds good - continue.

## User
Ok, incorporate the current ranking onto the existing webpage as a new scoring metric. I will peruse it and have a think about potential next steps.

## User
Hmm I think the next step is analysing why certain books which appear at the top of other canons (Ulysses, The Great Gatsby, Moby-Dick etc) and not on ours. Of course it is likely that these other lists are heavily affected by popularity bias.

Best other canon lists to refer to are: ( [lit-2014-2024.txt](lit-2014-2024.txt) , the love ranking on the FE and https://thegreatestbooks.org/v/table). Let me know if you need help accessing/reading the last one.

## User
I do like both your suggested changes. For the evidence cap, why should it exist? And why does increasing it increase the esteem and not just change uncertainty? This isn't necessarily a request for you to change action, I just want to understand why a evidence cap is good, and why you are suggesting 120,000.

For your second suggestion I do like the existing conservative distributed consensus score. For your second suggestion, is your “community-contested” indicator referring to just the Heterog. penalty or a range of relating factors? Either way, I support a secondary esteem-based ranking. Please add that to the FE.

And I would like the FE to show as many books as possible, even if their positions become less and less accurate.

## User
Hmm, thanks for all the work.

How much do you think these results are caused by the initial seed? Do you think we'd get similar results with any old seed? I guess I'm asking how 'natural'/'canonical' (that is, natural/canonical according to the biases already present in the goodreads data) this list is?

## User
Yeah, I was thinking this, but thought it would take a long time to run. Very likely worth it though. I compiled a list of candidate literary origins from the highest weighted lists on TheGreatestBooks and scraped them into csv files ( [lists_by_title](lists_by_title) ). You don't need to use all of them (use your best judgement), but you should should be able to use them (and the already scraped TheGreatestBooks 'canon') to create disjoint historical origins, regional/language-based origins and contemporary origins (though the dataset is from 2017, so some books may not be in the dataset). I'll let you create the non-literary controls yourself though.

## User
I added 7 more literary starts after realising the lists were still quite euro-centric.

## User
Sorry to interrupt you there, I had no idea how long the program was going to take. Also I added 7 more literary lists from TheGreatestBooks which had wider regional coverage - only use them if you think it will be worth it. South America still underrepresented.

## User
It looks like my computer ran out of space during your last operation. I've cleared some space up (deleted the large gzip, and removed .cache and .gradle). You are welcome to clear up unneeded space within the `novels` directory, just make sure its not a file that will need to be redownloaded, and that work is saved and pushed to github, but ask to delete anything else.

Also, repeating my last message in case you didn't get it: "Sorry to interrupt you there, I had no idea how long the program was going to take. Also I added 7 more literary lists from TheGreatestBooks which had wider regional coverage - only use them if you think it will be worth it. South America still underrepresented."

Continue following the plan, just be careful of harddrive space limitations and memory.

## User
Sorry to interrupt you again! Just thought I'd mentioned I added a literary-esque children's books list from TheGreatestBooks - I thought that one might serve as interesting too.

## User
Hmm, a few things.
1. How do we know that the reconstruction/convergence process always 'goes' in the same direction? Do we actually end up becoming more stable/slowing down/almost converging?
2. Are the literary origins more or less similar after attempted convergence?
3. If they do end up being more similar, it makes sense that there would be some 'literary center' to goodreads. Kinda something like the average of all the literary origins that somewhat converge. If this exists, I'd like to know the feasibility of searching for it.
4. If not, then maybe the literary origins were too close to start with, or the reconstruction/convergence process (as posed in point 1) was going in the wrong direction. TBH, I'm not sure about this case, it goes against intuition.

## User
I'm interested in the contraction trajectory test; but worried about how long it would take, but first let's discuss the robust center search.

Your plan for searching for the robust center relies too heavily on the choice for literary origins. The original model was found based on a literary seed ([lit-2014-2024.txt](lit-2014-2024.txt)). If we went your way we would be doing a similar thing, just for a group of literary origins. Even if we found a center, it still wasn't found naturally.
I'm looking for a more novel, perhaps more mathematical solution that relies less on supposed literary origins. Frankly this seem like an impossible task, but a very interesting one. Do you have any ideas?

## User
If you need any papers downloaded, let me know. As you were.

## User
Actually this was the original goal of this project (it started with a thought I had two nights ago). I was attempting with Grok 4.5, but decided to try reverse-engineering, but we never came out of that rabbit hole. I am absolutely willing for you to give it another crack. Your ideas all sound promising. Persue as you see fit.


Here's the relevant conversation history:

"""
I had an interesting thought last night. I was wondering whether it was possible to determine this literary canon we found by just analysing rating patterns (with no additional information). That is, without any taste signals or piles whatsoever. I could imagine one such approach being based on grouping users/books into clusters.



Could you give this question some thought, look for existing literature/research on this topic and/or design a query for google scholar labs (a google scholar LLM-assisted search)?




Short answer: **clustering alone finds taste communities, not “the canon.”** Recovering a literary hierarchy from ratings with **no** hand piles is a real research question — and partly doable — but you need an **ordering principle** on top of clusters (or instead of them). Your curator setup is already close to one classic unsupervised idea, just with external seeds.

### Why pure clustering isn’t enough

User–book ratings are a bipartite graph. Co-clustering / spectral methods / HLTA will happily find “romance readers,” “epic fantasy,” “literary fiction,” “YA,” etc. (SCUT even does this on the UCSD Goodreads matrix and recovers genre-ish book trees from interactions alone.)

That answers *who hangs with whom*, not *which hangout is consecrated*. Nothing in “cluster A vs B” says Karamazov outranks Harry Potter. Hierarchy needs a second ingredient: nestedness, rarity, pickiness, reflective prestige, etc.

### What “no piles” can still use

These are all functions of the rating matrix only:

| Idea | Intuition | Link to your system |
|---|---|---|
| **Nestedness / rarity nesting** | High-taste users’ loves ⊂∪ rare items; mass users mostly like ubiquitous books | Your `deep_share` / anti-normie logic, without naming the books |
| **Reflective two-mode prestige** | A book is prestigious if prestigious users love it; a user is prestigious if they love prestigious books — iterate | Soft version of curator weights with no seed authors ([Lizardo-style reflective centralities](https://www.sciencedirect.com/science/article/abs/pii/S0304422X17301857)) |
| **Lift / discriminativeness** | Books where picky/rare-taste users ★≥4 much more than mass | Your research `lift = P(★≥4\\|deep)/P(★≥4\\|active)` — “deep” defined unsupervised |
| **Correspondence analysis / SVD axes** | First latent axes of the user×item matrix often mix genre + legitimacy | Bourdieu used MCA with *social* covariates; here the axis is purely behavioral |
| **Taste groups then rank groups** | HLTA/conformative filtering finds groups; score groups by mean rarity, rating stinginess, entropy | Clusters + a prestige scoring rule |

Important caveat: unsupervised methods recover **a** cultural axis. Whether it matches *literary* canon vs “obscure snobbery,” non-English literary scenes, theory-bro shelves, etc. is an empirical question. Evaluation against polls/school lists sneaks labels back in for *validation*, even if discovery used none.

### Closest existing literature

- **Taste hierarchies from digital traces:** Airoldi, *The nested relationality of perceived legitimacy* (*Poetics*, 2024) — nested legitimacy from YouTube music evaluations.
- **Person–culture networks / omnivore as special case of reflective metrics:** “The mutual specification of genres and audiences” (*Poetics*) — prestige of genres from who consumes them and vice versa.
- **Ground-up clustering of taste (no preset genres):** Roose et al., network clustering of artist preferences (*Poetics*).
- **Unsupervised taste groups for CF:** HLTA / conformative filtering (Chen et al.).
- **Bipartite spectral structure on Goodreads-scale data:** SCUT (OpenReview) — hierarchical co-clustering of the UCSD user–book matrix.
- **Sociology background (usually *with* education/class labels):** Bourdieu *Distinction*; UK Cultural Capital projects; omnivore debates — useful theory, weaker as “ratings-only” recipes.
- **Goodreads + canon:** mostly studies how platforms *reproduce* institutional canons (Post45 “Goodreads Classics,” school-canon impact studies) — not unsupervised discovery of canon from stars alone. That gap is interesting.

### Google Scholar Labs query

Scholar Labs works best as a **research question**, not a boolean dump. Paste something like:

```text
Can literary or cultural prestige / canon hierarchy be recovered from
user–item rating or consumption data alone, without curated seed lists,
genre labels, or sociodemographic covariates?

I'm especially interested in:
- unsupervised or weakly supervised methods (co-clustering, spectral
  bipartite clustering, hierarchical latent tree / taste groups,
  nestedness of cultural consumption, reflective two-mode centrality,
  correspondence analysis / SVD of rating matrices)
- empirical work on books, music, or film that maps taste hierarchies
  or legitimacy from digital traces (Goodreads, YouTube, streaming)
- how these methods distinguish “highbrow / consecrated” structure from
  mere community detection or popularity

Please prioritize sociology of culture (Poetics, Bourdieu/omnivore
debates), computational social science, and recommender-systems papers
that discover latent taste hierarchies rather than only optimize accuracy.
```

Optional follow-ups once Labs returns seeds:

```text
Papers citing Lizardo reflective two-mode centrality OR nestedness
cultural taste OR "taste hierarchies" digital traces
```

```text
Recovering cultural legitimacy from collaborative filtering matrices
without side information
```

### If you ever prototype it on your DB

A clean experiment: define user prestige by iterative rarity-weighted love (no author piles), rank books by weighted love among high-prestige users, compare overlap@50/200 to your literary_poll ranking and anti-signal suppression. That directly tests whether the “canon you found” is already latent in the rating geometry.

I can turn that into a small research script against `explorer.duckdb` if you want to poke it empirically next.





A lot of this response is good. I think you slightly misunderstood me when I meant rating patterns. To be more clear I want some kind of algorithm that given tuples of (book_id, rating, user_id), can determine some kind of literary consensus, using any and all possible tools (things you listed in What “no piles” can still use). Of course the data doesn't actually need to be served as a list of tuples, I'm just getting at what data is allowed. Optionally we could expand the allowed data in the future if we don't get results, but I would want to keep it as generaliseable as possible.

First commit the current changes so we have a record of the simpler implementation.

Then experiment with the most promising approaches, see what results you end up with. And if you want me to access any research papers for you, or run a scholar lab query, I'm happy to help.




### Commit
`curators_explorer` is on `main` as **`c496b76`** (“Add curators_explorer: simplified continuous curator ranking app”). Legacy `ucsd_explorer` edits were left unstaged.

### Experiments (ratings-only)
Script: `curators_explorer/scripts/research_ratings_only_canon.py`  
Report: `curators_explorer/data/RATINGS_ONLY_CANON_REPORT.md`

Allowed signal: `(user_id, work_id, rating)` only. Poll/anti lists used **only for scoring**.

| Approach | What happened |
|---|---|
| Global Bayes P(5★) | Popular fantasy / romance |
| Rarity-depth curators | **Fails:** indie romance / vanity (obscure ★≥4 inflates “depth”; classics *hurt* it) |
| Plain / rarity HITS | YA–fantasy hubs (Potter, Clare, Martin) |
| Picky raters | Slight poll overlap (pos50=3); still Sanderson-heavy |
| **Anti-blockbuster + picky** | **Best poll overlap (pos50=4)** — Shahnameh, Tutunamayanlar, Arabic/Tamil epics + epic fantasy |
| **Mid-pop 5★ PMI co-citation** | **Most interesting:** coherent **Arabic literary** head (Towfik, Radwa Ashour, …), anti50=0 — a real literary consensus, not the English poll |

### Reading
Ratings alone seem to recover **dense consecrated communities**, not one global Anglophone “lit poll” axis. Seeded curators are doing something rarity-depth can’t: tying prestige to a specific cultural neighborhood.

### If you run Scholar Labs
This prompt fits the empirical result well:

```text
How can multiple cultural legitimacy hierarchies or literary canons
be recovered from bipartite user–item rating data alone, without seed
lists or metadata? I'm interested in co-citation / PMI item graphs,
nestedness within communities, multilingual canon formation on
Goodreads-like platforms, and why rarity-based "cultural capital"
proxies fail when popular classics coexist with obscure genre niches.
```

Papers I’d most like PDFs/HTML for if you can grab them: Airoldi 2024 (*Poetics*, nested legitimacy); Lizardo reflective two-mode centrality; anything on **Goodreads co-reading graphs and non-English canons**.

I can next try **within-community** ranking (run PMI, then prestige inside the English-dense component) if you want another pass.



## User
Ok, I downloaded the first two papers you asked four as html files, and two others that looked relevant from the Google Scholar results. I didn't look for information on non-English canons; but some cultures tend to be very loud about the love for their classics (as they deserve to be).

Use the info from the downloaded papers to best perform your research; and continue.



Your “loud cultures love their classics” intuition is exactly what the ratings graph shows.

### Papers → what we ran
- **Lizardo:** method of reflections (`−δ²`, niche enthusiasts, high-order) instead of plain HITS  
- **Airoldi:** nested multi-community portfolio (PMI → label-prop → round-robin heads)  
- **Feldkamp:** dual axis that penalizes high Goodreads means  
- **Walsh:** treat crowd “classics” as one construction among many — so `literary_poll` is eval only

### What came out
| Signal | Head | vs poll |
|---|---|---|
| `lizardo_high_order` (best new Q, anti50=0) | Arabic literary (Towfik, Mourad, …) | pos50=0 |
| `lizardo_neg_delta2` (anti50=0) | Indonesian Tere Liye constellation | pos50=0 |
| `nested_community_portfolio` (~15 communities) | Towfik, Wordsworth, Christie, YA, comics, … interleaved | anti50=0 |
| `nested_mass_community_reflections` | Discworld/Pratchett (platform-dense “mass” cluster) | not literary |
| Still best poll overlap | `anti_blockbuster_picky` (pos50=4) | weak |

### Verdict
Ratings-only does **not** recover one Anglophone literary axis. It recovers **nested local canons** — Arabic, Indonesian, Discworld, etc. — which matches Airoldi and explains why Feldkamp’s Goodreads-vs-expert split shows up here. Full write-up: `curators_explorer/data/RATINGS_ONLY_CANON_REPORT.md`.

Natural next product move: multi-canon explorer (community heads + within-community ranking), with seeds only if you still want the English lit-poll target.



## User
Was there any cluster found (through any method) that contained many of the literary classics flagged in [lit-2014-2024.txt](lit-2014-2024.txt) ?





**No** — nothing like a broad `lit-2014-2024` classics cluster showed up.

Against the **100 titles** in that file (183 matched work_ids):
- Only ~76 even enter the mid-pop PMI graph (n∈[250,12000]). The biggest school-canon titles are missing because they’re *too* popular: Gatsby, 1984, Catcher, Lolita, One Hundred Years of Solitude, etc.
- Best communities held **4–5** lit works, and they’re mostly **same-author** clumps (Joyce quartet; Pynchon + Gaddis), not a cross-canon classics block.
- At most ~5–7% of graph-lit works sit in any single community.

Against the wider **literary_poll** work set (all works by those authors), there *are* dense micro-clusters — Vonnegut (~23/25), García Márquez, Dostoevsky, Nabokov, Hesse, Woolf, Wolfe, Shakespeare plays — but each is an author/family island. No community holds more than ~5% of poll works in the graph.

So: ratings co-liking recovers **author neighborhoods**, not one literary-classics community. Global method heads never concentrated the list either (`anti_blockbuster_picky` still best at pos50=4).




## User
You mention how ratings analysis is turning up author islands. What if we expand the information used to (user, rating, book, author)? Would that allow for further progress? Do you want to search for relevant research papers / give me a scholar labs query?

Also the research python scripts are taking a lot of time, if this can't be helped leave it; just make sure they're optimised and you're not repeating work.

Continue your research.




**Yes, expand to author — but as a nesting/debias layer, not a magic literary ranker.**

### Would `(user, rating, book, author)` help?
Theoretically yes (Airoldi’s artist level; Vlegels & Lievens artist-preference nets; arXiv:2303.05080 argues for author-similarity over book-similarity). Empirically on Goodreads:

- **Person×author reflections/PMI** → dense **MC / M/M romance** islands (0 poll authors in top 50). Poll authors are *in* the graph (61/62) but sit mid/low under `−δ²` even with a mid-pop filter.
- **Cross-author book PMI** (drop same-author edges) → still the **Arabic literary** cluster — author helps de-island multilingual canons, not `lit-2014-2024`.

Literary authors behave like diffuse prestige hubs; romance authors like tight taste islands. Density-seeking graph metrics prefer the latter.

### Scholar Labs query
```
bipartite person-author OR person-artist taste network OR
"method of reflections" OR "two-mode" cultural hierarchy OR
omnivorousness ranking authors books OR Goodreads co-reading
author similarity literary canon prestige -recommendation
-collaborative-filtering
```

### Scripts
Cached mid-pop / PMI / reflections in the ratings script; author bipartite + reflections(14) loaded once and reused (~208s → ~0.4s). Full author suite ~7 min. Reports: `AUTHOR_LEVEL_CANON_REPORT.md`, updated takeaway in `RATINGS_ONLY_CANON_REPORT.md`.

**Bottom line:** author is worth keeping for multi-canon / de-islanding; Anglophone poll still looks underdetermined without seeds or an external prestige proxy.

## User
For now let's just include publication year. Remember that you will need to find the oldest publication year among editions to get accurate data (check the dataset to double check my info). My intuition tells me that users rating a lot of old books highly are much more likely to be literary. Even if this is a bias, it at least is a very simple and explainable bias, and doesn't pretend to be hidden.

## User
Before doing that, let's improve the quality of our data let's join this parsed and cleaned Goodreads dataset (https://huggingface.co/datasets/BrightData/Goodreads-Books) with our current one. I downloaded it, search for `Goodreads-Books.csv`.

The useful columns are:
- url
- author (might be more accurate than ours)
- genres (might be helpful for FE filtering, but we'll ignore them for literary canon research exercise
- first_published (this is most important!)

If you see any other improvements you can make, go for it.

Once you've cleaned up our data redo the experiments. I've forgotten if you did this (you probably did) but also test preferring users who rate old books higher than new ones. I'd also be interested in what the chosen jurors converge to on our 'stability maximisation approach' (I know it wasn't just stability; that is shorthand). Good luck.

# Simplified rebuild — implementation plan

**Audience:** a new agent implementing the redesign **without prior chat history**.  
**Status:** research complete on the legacy app (`ucsd_explorer/`); build the new app in a **new directory**, leave old code in place.  
**Supersession:** findings from Aug 2026 Pareto / taste-signal work **override** earlier slider defaults in this doc where they conflict.

Related artifacts (legacy tree):

| File | Role |
|---|---|
| `ucsd_explorer/` | Current explorer to copy patterns from, not to gut |
| `lit-2014-2024.txt` | Literary poll → default **positive** author pack |
| `ucsd_explorer/data/taste_lists.json` | Positive + **non_literary** anti-signal authors |
| `ucsd_explorer/data/normie_canon.json` | School/neutral titles for **share gate only** |
| `ucsd_explorer/data/PARETO_TASTE_SIGNALS_REPORT.md` | Latest taste-aware Pareto (all-genres, anti through top 1000) |
| `ucsd_explorer/data/pareto_taste_signals.json` | Full run data |
| `ucsd_explorer/data/PARETO_POST_FIX_REPORT.md` | Earlier hand-probe / mass Pareto (SF-oriented) |
| `ucsd_explorer/scripts/pareto_taste_signals.py` | Re-runnable evaluator for new piles |

---

## 0. Product goal

Rebuild the UCSD Goodreads ranking explorer as a **simpler, more customisable** app:

- One filtering philosophy: **Curators** (today’s “deep curator” idea, renamed).
- Minimal sliders that actually bite; fixed coverage = among-raters (0).
- Editable **taste packs** (positive / negative (+ school-neutral for purity)).
- Clear sort metrics + a global **scale mode**.
- SF toggle + existing catalog hygiene; **no** similarity in v1.
- Curator vs global rating histograms.
- Clean code in a **new directory**; keep `ucsd_explorer/` as reference.

---

## 1. Original feature requirements (user)

### Architecture
- New directory; keep old code.
- Clean, maintainable code.

### Curators
- Deep-curator-style filtering only; rename **Deep → Curators**.

### Sort metrics
1. **Love** (existing percentile love mass) with simplified sliders; coverage slider **removed** (fixed at 0). Make remaining knobs change things more drastically; keep slider count minimal.
2. **Scale mode** for all relevant metrics: **raw percentiles** vs **adjusted percentiles** vs **raw star ratings**.
3. RYM/IMDb-style **Bayesian** rating estimate.
4. **Raw mean** and **raw % of 5★** (or percentile equivalent).
5. **Number of curator reads** (popularity among the active curator cohort).

### Taste signals
- Keep only:
  - **Positive** pile (seeded from `lit-2014-2024.txt` / literary poll authors).
  - **Negative** anti-signal pile (non-literary authors).
- **Do not** drop school/normie tracking by only deleting titles from positives — that loses **purity** (see §3). Keep a lightweight **school/neutral** list used **only** for share gating (`deep_share`-style), not as positive weight.
- Drop the separate SF-only positive pile (`literary_sf`); all-genres literary poll is the default positive pack.
- Keep current preset as default; **Reset** restores it.
- Prefer **frontend-editable packs** (author-level) if architecture allows; prepare for public user presets later.

### Genre / catalog / out of scope
- **SF toggle only** for genres in v1 (legacy genre UI is too finicky).
- Copy existing catalog filters (omnibus/collections, comics, picture books, derivatives, fiction-only, collapse duplicates, etc.) even if messy — isolate in one module.
- **No book similarity** in v1.
- **Do** implement curator histograms vs global histograms.
- Implement any **non-minor** optimisations discovered (early work filters, avoid wide 625k joins when mint gates apply, single score template, etc.).

### Coverage
- Fixed at **0** (among-raters only). Slider later if needed.

---

## 2. Locked design decisions

| Topic | Decision |
|---|---|
| School / normie | **Keep** as neutral list for **purity/share gate only**. Not positive weight. Deletion-only ≠ purity (ablation: depth-only MAD≈28 vs baseline; purity-only ≈ baseline). |
| Infer normie from data? | Popularity×low-lift on poll approximates many hand titles but misses non-poll syllabus books. **v1: keep hand `normie_canon.json`** (optionally data-seed suggestions later). |
| Coverage | **Fixed 0**. |
| SF-extras pile | **Drop** from v1 positives. |
| Live pack editing | **Author packs** in v1 if feasible (query-time from like tables). Title-level editing later. Reset → committed preset JSON. |
| Equal-vote / gate mode | **Do not expose** on FE; weighted curator scores only. |
| Strictness (elite top-K) | **Hide / fix at 0** for v1 defaults. |
| Depth floor | **Hide / fix at 0**; purity + deweight carry pickiness. |
| Love variants | **One** love score in v1 (no geom/tilt forks until love is solid). |
| Similarity | Deferred. |

---

## 3. Why “all sliders at zero” looked curated (legacy bug / lesson)

Historically, UI zeros still looked literary because:

1. Rankings used the **pre-minted deep table** (~20k users), not all Goodreads users.
2. A query bug could invent a **com_share cap** even at purity=0 (fixed on current build).

**Contract for the new app:**

- **All pickiness knobs at 0** → pay **no** attention to taste lists for gating/weighting → cohort ≈ everyone who can score (percentile users), **equal weights**.
- Raising knobs continuously increases attention to taste (gates + stored curator weights).
- Never silently apply mint floors or com caps when the UI says off.

Legacy fix reference: wide cohort at zeros; `resolve_deep_com_share_cap`; early SF/catalog work filter for speed.

---

## 4. Research summary (do not re-litigate unless piles change)

### 4.1 Normie / purity
- Tracking school titles in the denominator of share **matters**.
- Data-inferred low-lift×popularity ≈ hand list on-poll, incomplete off-poll.
- **Keep explicit school/neutral list.**

### 4.2 Competing goals → Pareto
Two (later three) axes:

1. **Literary / taste quality** — positives high; non-literary antis low (**measure through top 1000**, not only top 50).
2. **Voter mass** — geo-mean curator `n` in top ~100 (obscure books need votes).
3. Diagnostic: **normie-filler dominance** in the head (canon ∉ positive). High 1984 is fine if it’s a positive signal; HP-style fillers crowding top 20/50 is not.

Technique: grid sweep → Pareto front → utopia / product / quality-lean kneepoints.  
Re-run `pareto_taste_signals.py` (or successor) when default piles change.

### 4.3 Hand-probe vs taste-signal Pareto
- `PARETO_POST_FIX_REPORT.md`: older SF + hand GOOD/BAD lists; suggested higher dew/purity for “literary SF probes.”
- `PARETO_TASTE_SIGNALS_REPORT.md`: **authoritative for v1 defaults** — all-genres, literary_poll positives, non_literary antis through **top 1000**.

### 4.4 Deep anti-signal finding (critical)
Top-50 anti counts are almost always 0 once weighting is on — **misleading**.

At purity≈55, raising **deweight**:

| dew | anti in top 1000 | anti median rank | Effect |
|---:|---:|---:|---|
| 0 | ~6 | ~993 | Fewest/late antis; weak without other gates |
| 15 | ~10 | ~771 | Best mid-list push among weighted settings |
| 25 | ~10 | ~558 | Still good |
| 40 | ~10 | ~328 | Same count, clustered higher |
| 60–80 | ~4–8 | ~67–146 | Antis invade top ~200 |

Raising **purity** at dew=25: anti count flat until high purity; then median **worsens** (antis move up) while mass collapses. p90 is too harsh.

**Do not default deweight to 40+** if mid-list anti-suppression matters.

### 4.5 Adjusted percentiles
Not a clear win for obscure titles; mainly recalibrates generous raters. **Expose all three scale modes**; default adjusted for continuity; let eval/presets choose.

### 4.6 Optimisations already proven useful
- Push genre/catalog work filters **into** event aggregation (don’t scan ~100M ratings then filter).
- When taste gates/deweight on → score from mint curator table (~20k), not 625k wide join.
- When all pickiness off → equal-weight percentile users + early work filter (~1s vs ~11s).
- Single aggregation template; swap score expression.
- Cap `limit` high enough for eval (2000+) but UI default ~200–400.

---

## 5. v1 product specification

### 5.1 Directory / stack
- New package dir next to `ucsd_explorer/` (name e.g. `curators_explorer/` — pick one and stick to it).
- Same DuckDB warehouse / ratings materialization is fine; new mint + API + static UI.
- Python HTTP server + static JS/HTML is fine (match legacy) unless there’s a strong reason to switch.

### 5.2 Taste packs (data model)
Three sets in a preset JSON:

1. **positive_authors** — from literary poll (`lit-2014-2024.txt` → author IDs).
2. **negative_authors** — from current `non_literary` anti-signals.
3. **neutral_titles` or works** — from `normie_canon.json` (school/ubiquitous), **share gate only**.

UI: edit author packs (+ show neutral list); **Reset** reloads shipped preset.  
Query-time cohort from per-user like aggregates (legacy has `user_author_likes`-style data — reuse or rematerialize once).

### 5.3 Curator cohort
At query time (conceptually):

- Start from users who can score (have shelf percentiles or star hist).
- **Taste floor / purity:** require enough positive hits; optionally  
  `share = pos / (pos + neutral)` ≥ threshold; optionally cap negative 5★ pollution (`com_share`).
- **Deweight:** `weight = stored_curator_score ^ expo(deweight)` with expo=0 → all ones. Prefer this over equal elite votes.
- **Strictness:** omit from FE (fixed off) unless advanced panel.
- **Depth:** omit from FE (fixed off).

Mint may precompute base curator scores for the **default** preset for speed; live pack edits recompute weights from likes for the active pack key (cache by pack hash).

### 5.4 Sort metrics
| Metric | Notes |
|---|---|
| Love | `f(scale)^ρ` mass among raters (coverage=0). One variant. |
| Bayesian | `(n/(n+m))R + (m/(n+m))C`; `C` = curator-scope prior; `n` = Kish n_eff if weighted |
| Mean | Of active scale |
| % top | 5★ rate or top-shelf pct rate per scale mode |
| Curator reads | Count / weight-sum of cohort raters |

**Scale mode** (global): raw stars | raw full-shelf percentiles | adjusted (anchor on positive-signal books — define once in code comments + UI blurb).

### 5.5 FE controls (minimal)

**Expose**

| Control | Default | Role |
|---|---:|---|
| **Deweight** | **15–25** | How hard curator weights pull. Primary knob. |
| **Purity** (taste floor / share) | **0–55** | Pos share vs neutral + soft com cap when &gt;0. Mass/obscurity dial; weak on deep antis alone. |
| **Min ratings** | **25** | Always |
| **Bayesian m** | **30–50** | When Bayesian sort selected |
| **Scale mode** | adjusted | Applies to relevant metrics |
| **Sort metric** | love | |
| **SF toggle** | off or on per preset | Prevalence SF gate only |
| Catalog checkboxes | copy legacy defaults | Isolate module |
| Taste pack editor + Reset | default preset | Author packs |

**Fixed / hidden**

- Coverage = 0  
- Strictness = 0  
- Depth = 0  
- No gate/equal-votes mode  
- No geom/tilt/coverage sliders  
- No similarity  

**Presets (ship these)**

| Preset | dew | purity | Notes |
|---|---:|---:|---|
| **Default literary** | **15** (or 25) | **55** | Best everyday: clean head, antis later in list (med ~550–770 @ dew15), filler ~0 |
| **Browse / mass** | **25** | **0** | Same deep-anti count as low purity @ dew25; more voter mass |
| **Sharp** | **15** | **65** | Smaller mass; avoid 75–90 if mid-list antis matter |
| **Everyone (debug)** | **0** | **0** | True off — not a literary mode |
| **Elite (optional)** | **100** | **0** | Can zero antis in top 1000 but filler creep — not default |

**Avoid shipping as default:** dew ≥ 40–60 (mid-list anti concentration), dew=0+purity=0, purity ≥ 90.

### 5.6 Histograms
- Per opened book: star (and optional pct) hist among **active curator cohort** (weighted if deweight &gt; 0) vs **global**.
- Label clearly which cohort/weights apply.

### 5.7 Catalog / genre
- Copy legacy flag logic into one module (`catalog_flags` / filters).
- SF: single prevalence gate toggle (legacy `work_genre_gates` / `sf`).
- No full genre tag UI in v1.

---

## 6. Implementation sketch (for the building agent)

1. Scaffold new dir: db access (read-only DuckDB), config paths, server, static UI.
2. Materialize or reuse: rating events, works, flags, percentiles, author-like hits, default preset JSON.
3. Cohort SQL builder: packs → gates → weights → active users.
4. One `rank_books` template; metric + scale mode → score expression.
5. Early `eligible_works` CTE for SF + catalog (performance).
6. API: `/api/meta`, `/api/rank`, `/api/book`, `/api/hist`, `/api/taste` (get/reset/update packs).
7. UI: metric, scale, dew, purity, min n, m, SF, catalog, results table, drawer with dual hist, pack editor + Reset + presets.
8. Port/adapt `pareto_taste_signals.py` into the new tree; run once against defaults; adjust preset if needed.
9. Do **not** port similarity, geom love, multi-curator method zoo, or finicky multi-genre UI.

---

## 7. Eval checklist before calling v1 done

- [ ] All knobs 0 → broad equal cohort (not mint-only theater).
- [ ] Default preset: poll positives high; anti-signals rare in top 50; anti median in top 1000 not collapsed to &lt;200.
- [ ] Neutral list affects share gate; removing it widens school-heavy curators (spot-check).
- [ ] Coverage fixed among-raters; obscure books can surface with enough curator n.
- [ ] Scale modes all wired; Bayesian/mean/love/%top/reads work.
- [ ] SF toggle + catalog filters behave like legacy copies.
- [ ] Pack Reset restores shipped preset; edit authors changes ranking without full DB remint (or document cache invalidation).
- [ ] Histograms: curator vs global.
- [ ] Hard-refresh / server restart documented (Python does not hot-reload).

---

## 8. Reproduce research (legacy tree)

```bash
# Earlier simplified-rebuild probes
PYTHONPATH=. .venv/bin/python -m ucsd_explorer.scripts.research_simplified_rebuild

# Hand-probe mass Pareto
PYTHONPATH=. .venv/bin/python -m ucsd_explorer.scripts.pareto_post_fix

# Taste-signal Pareto (all-genres, anti through top 1000) — prefer this for defaults
PYTHONPATH=. .venv/bin/python -m ucsd_explorer.scripts.pareto_taste_signals
```

---

## 9. Bottom line for the implementer

Build a **new, smaller app** around: **Curators + positive/negative author packs + school-neutral share gate + deweight + purity + fixed coverage 0 + scale mode + a short metric menu + SF/catalog + dual histograms + editable packs with Reset.**

Defaults: **deweight ≈ 15–25, purity ≈ 55 (or 0 for browse), everything else off/fixed.**  
Re-validate with the taste-signal Pareto when piles change.  
Ignore legacy method proliferation and similarity until this core feels right.

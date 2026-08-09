# Literary basin refinement report

Campaign seed: `20260903`. Starting frozen commit: `bff6d6d9b91410daac1c302382f9e5a02892d02e`.
Campaign wall-clock runtime estimate: `1846.0` seconds (resumable phases included).

This is a bounded two-stage refinement experiment. Basin discovery, cluster-count selection, J5-like-basin selection, and expansion membership construction were label-free; semantic probes are post-hoc annotations only.

## Audit and invariants

Smoke checks: **26/26 passed**.

|check|status|detail|
|---|:---:|---|
|starting_commit_exact|PASS|HEAD=bff6d6d9b91410daac1c302382f9e5a02892d02e|
|prior_artifacts_present|PASS|/home/ifrankling/unsw/novels/curators_explorer/data/literary_dynamics_decomposition.json, /home/ifrankling/unsw/novels/curators_explorer/data/literary_dynamics_decomposition.npz, /home/ifrankling/unsw/novels/curators_explorer/scripts/research_literary_dynamics_decomposition.py|
|frozen_score_hash_matches|PASS|f6d536d0e37345359344ba3cd94094d1be579067a8c1ff0c7420e9f92a60d49c|
|frozen_universe_hash_matches|PASS|2cb504f7284a19d6afb1263471b7d9f43457b167a8f79db6987d773c26a592e4|
|payload_membership_J5000_exact|PASS|payload=5000 requested=5000|
|selection_hash_J5000_matches|PASS|f946c68688d46695940527482e4e4bd70b6060b1eb534b288004c50750c4ecac|
|payload_membership_J10000_exact|PASS|payload=10000 requested=10000|
|selection_hash_J10000_matches|PASS|50eefa930b10f04f50d90a25e6d281cf6418a61f3c07e2af2b2bad19a425493f|
|payload_membership_J20000_exact|PASS|payload=20000 requested=20000|
|selection_hash_J20000_matches|PASS|c038c928564da50a3ec596338b134eebd2ed94f6a3f1ef9cd5cf6e0d28468fad|
|payload_membership_J30000_exact|PASS|payload=30000 requested=30000|
|selection_hash_J30000_matches|PASS|6a7f4b3397d5d3ecbbd6d83d5b0d04e6ccd6979c0b7fa2e8132d2c1f301b7b8f|
|nested_memberships|PASS|J5/J10/J20/J30 nested intersections exact|
|fixed_beta|PASS|BETA=2.5|
|fixed_random_sigma|PASS|sigma=0.2|
|basin_cap|PASS|cap=1000|
|expansion_cap|PASS|cap=700|
|exact_historical_equation_audited|PASS|damped tanh/sigmoid equation and historical iterate_map inspected|
|no_pruning_reversal_outsiders|PASS|runner only reweights fixed local payload users|
|cluster_method_label_free|PASS|cluster code consumes only endpoint book vectors before metadata/probes|
|cluster_k_search_frozen|PASS|k=[2, 3, 4, 5, 6, 7, 8]|
|cluster_tie_rule_frozen|PASS|tol=0.01|
|frozen_j5_endpoint_reproduced|PASS|t=431 score_hash=35ea99556c06a2d60d7a2aa889b446fc9afc2202c293d6cf3f04fe99ba8316fb|
|frozen_j5_endpoint_hash_present|PASS|35ea99556c06a2d60d7a2aa889b446fc9afc2202c293d6cf3f04fe99ba8316fb|
|frozen_j5_work_universe_common|PASS|works=26418|
|endpoint_weights_mean_one|PASS|mean=1.000000000|

Frozen J5 endpoint iteration: `431`; endpoint float32 hash: `35ea99556c06a2d60d7a2aa889b446fc9afc2202c293d6cf3f04fe99ba8316fb`.

## Basin census

Clustering representation: centered, L2-normalized final full book-preference vectors; distance `1 - cosine`; agglomerative average linkage; k search exactly 2..8.

|population|k|basin|runs|frequency|silhouette(k)|within median|nearest between|J5 cosine|equal assignment|qualitative head|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
|J10000|4|1|29|0.453|0.786|0.973|0.945|0.897|no|Crime and Punishment; Hamlet; Between the World and Me; The Brothers Karamazov; The Return of the King (The Lord of the Rings, #3); leading authors: J.R.R. Tolkien (3), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2)|
|J10000|4|2|14|0.219|0.786|0.976|0.945|0.863|no|Crime and Punishment; Hamlet; The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Brothers Karamazov; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2)|
|J10000|4|3|13|0.203|0.786|0.973|0.912|0.657|yes|The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); The Lord of the Rings (The Lord of the Rings, #1-3); A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (5), George R.R. Martin (2), Fyodor Dostoyevsky (2), Neil Gaiman (2)|
|J10000|4|4|8|0.125|0.786|0.976|0.912|0.706|no|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Between the World and Me; The Two Towers (The Lord of the Rings, #2); A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (4), Fyodor Dostoyevsky (2), Art Spiegelman (2), Ta-Nehisi Coates (1)|
|J20000|4|1|18|0.281|0.916|0.983|0.845|0.807|yes|Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Fyodor Dostoyevsky (3), Art Spiegelman (3), J.R.R. Tolkien (2)|
|J20000|4|2|17|0.266|0.916|0.987|0.845|0.776|no|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Brothers Karamazov; The Two Towers (The Lord of the Rings, #2); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2)|
|J20000|4|3|15|0.234|0.916|0.988|0.846|0.619|no|The Return of the King (The Lord of the Rings, #3); Between the World and Me; Crime and Punishment; A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Brian K. Vaughan (3), Ta-Nehisi Coates (1)|
|J20000|4|4|14|0.219|0.916|0.984|0.846|0.589|no|The Return of the King (The Lord of the Rings, #3); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); leading authors: J.R.R. Tolkien (5), Neil Gaiman (5), Art Spiegelman (2), George R.R. Martin (1)|

### Cluster robustness

**J10000** silhouette by k: 2=0.718, 3=0.707, 4=0.786, 5=0.679, 6=0.558, 7=0.533, 8=0.273
; bootstrap median ARI=1.000 (p10=1.000, p90=1.000).
**J20000** silhouette by k: 2=0.648, 3=0.734, 4=0.916, 5=0.700, 6=0.684, 7=0.684, 8=0.505
; bootstrap median ARI=1.000 (p10=1.000, p90=1.000).

J5-like basin is selected only by maximum centered preference cosine to frozen J5. The best-minus-second margin is J10000=0.034; J20000=0.031.

## Basin dynamics

|population|strict runs/64|median final step|median final weight_rel_1|median final book_rel_1|median recent lag2/lag1|2-cycle heuristic count|practical head stability median|
|---|---:|---:|---:|---:|---:|---:|---:|
|J10000|63/64|1.000|2.40e-05|3.06e-05|2.045|0|20|
|J20000|63/64|1.000|1.99e-05|2.53e-05|2.045|0|20|

Interpretation of lag diagnostics is descriptive: a genuine 2-cycle would require lag-1 weight movement to remain nonzero while lag-2 collapses. The report does not assume a cycle from nonzero lag-1 alone.

## J5 agreement and specificity

Outer candidate pool: `J20000\J5000`, n=15000; eligible frozen-J5 works=1235 split A/B=579/656.

|comparison|n|Pearson|Spearman|
|---|---:|---:|---:|
|A_vs_B|14857|0.210|0.216|
|A_vs_basin_margin|14915|0.005|0.003|
|B_vs_basin_margin|14940|0.078|0.078|
|full_vs_basin_margin|14998|-0.026|-0.031|
|A_vs_common_L|14915|0.162|0.161|
|basin_margin_vs_common_L|20000|0.063|0.071|

Top-set overlap between ORDER_J5's fold-A signal and basin specificity:

|k|overlap|Jaccard|
|---:|---:|---:|
|1000|66|0.034|
|2500|485|0.107|
|5000|1778|0.216|
|10000|6784|0.513|

### Matched-L profiles

The high/low specificity groups were formed within each frozen common-L decile, then pooled.

|group|n|L median|L p10|L p90|specificity median|top head|
|---|---:|---:|---:|---:|---:|---|
|high_specificity_matched_L|6660|0.753|0.718|0.785|0.102|Crime and Punishment; Hamlet; The Brothers Karamazov; Between the World and Me; Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1); leading authors: Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (2), Leo Tolstoy (2)|
|low_specificity_matched_L|6660|0.753|0.718|0.786|-1.823|The Return of the King (The Lord of the Rings, #3); The Fellowship of the Ring (The Lord of the Rings, #1); A Storm of Swords (A Song of Ice and Fire, #3); The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), Neil Gaiman (4), George R.R. Martin (3), Brandon Sanderson (2)|

Specificity-band profiles are exported in `LITERARY_BASIN_HEADS.md`; the matched-L heads are the direct equal-vote heads of those pooled users, not converged selections.

## Refined expansion results

|ordering|n|median L|p10 L|heldout B median|direct→final J50|final→J5 J50|final→J5 J200|random median J50 vs equal|strict?|iterations|20–49 ≥1|20–49 ≥3|direct head|final head|
|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|---:|---:|---:|---|---|
|L|7500|0.797|0.772|0.750|0.587|0.724|0.786|0.980|yes|349|0.424|0.081|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); The Fellowship of the Ring (The Lord of the Rings, #1); leading authors: J.R.R. Tolkien (4), Fyodor Dostoyevsky (3), Art Spiegelman (2), William Shakespeare (1)|Crime and Punishment; Hamlet; The Brothers Karamazov; Between the World and Me; The Trial; leading authors: J.R.R. Tolkien (4), Fyodor Dostoyevsky (3), Jorge Luis Borges (2), William Shakespeare (1)|
|L|10000|0.785|0.758|0.748|0.515|0.250|0.303|0.660|yes|383|0.506|0.134|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1)|The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), George R.R. Martin (2), Fyodor Dostoyevsky (2), Neil Gaiman (2)|
|L|12500|0.775|0.747|0.742|0.493|0.587|0.606|0.720|yes|566|0.563|0.182|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; Between the World and Me; The Two Towers (The Lord of the Rings, #2); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1)|Crime and Punishment; Hamlet; Between the World and Me; Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Art Spiegelman (3), J.R.R. Tolkien (3), Fyodor Dostoyevsky (2)|
|L|15000|0.767|0.736|0.738|0.471|0.190|0.286|0.560|yes|510|0.611|0.228|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Two Towers (The Lord of the Rings, #2); Between the World and Me; leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1)|The Return of the King (The Lord of the Rings, #3); The Fellowship of the Ring (The Lord of the Rings, #1); A Storm of Swords (A Song of Ice and Fire, #3); The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), Neil Gaiman (3), George R.R. Martin (2), Art Spiegelman (2)|
|L|17500|0.760|0.727|0.734|0.538|0.389|0.527|0.680|yes|499|0.653|0.274|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Between the World and Me; Hamlet; The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Neil Gaiman (2)|Crime and Punishment; Hamlet; Between the World and Me; Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1); The Return of the King (The Lord of the Rings, #3); leading authors: Art Spiegelman (3), J.R.R. Tolkien (3), Jorge Luis Borges (3), Fyodor Dostoyevsky (2)|
|L|20000|0.753|0.718|0.729|0.562|0.333|0.509|0.960|yes|469|0.686|0.318|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2)|Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), J.R.R. Tolkien (2)|
|J5|7500|0.797|0.728|0.734|0.515|0.667|0.732|0.420|yes|449|0.429|0.082|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Fyodor Dostoyevsky (2), Art Spiegelman (2), William Shakespeare (1)|Crime and Punishment; Hamlet; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; Between the World and Me; leading authors: J.R.R. Tolkien (4), Fyodor Dostoyevsky (2), Jorge Luis Borges (2), Art Spiegelman (2)|
|J5|10000|0.785|0.723|0.728|0.471|0.220|0.299|0.500|yes|700|0.503|0.131|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; The Two Towers (The Lord of the Rings, #2); Hamlet; The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1)|The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); The Lord of the Rings (The Lord of the Rings, #1-3); A Storm of Swords (A Song of Ice and Fire, #3); leading authors: Neil Gaiman (5), J.R.R. Tolkien (4), George R.R. Martin (2), Brian K. Vaughan (2)|
|J5|12500|0.767|0.720|0.728|0.429|0.562|0.613|0.720|yes|454|0.571|0.184|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); Hamlet; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1)|Crime and Punishment; Hamlet; The Return of the King (The Lord of the Rings, #3); Ficciones; Between the World and Me; leading authors: J.R.R. Tolkien (4), Jorge Luis Borges (3), Art Spiegelman (3), Fyodor Dostoyevsky (2)|
|J5|15000|0.760|0.720|0.730|0.449|0.163|0.262|0.540|yes|323|0.619|0.233|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2)|The Return of the King (The Lord of the Rings, #3); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); leading authors: J.R.R. Tolkien (5), Neil Gaiman (5), Art Spiegelman (2), George R.R. Martin (1)|
|J5|17500|0.756|0.719|0.730|0.471|0.389|0.521|0.360|yes|689|0.659|0.281|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1)|Crime and Punishment; Hamlet; The Return of the King (The Lord of the Rings, #3); Between the World and Me; Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1); leading authors: J.R.R. Tolkien (3), Art Spiegelman (3), Jorge Luis Borges (3), Fyodor Dostoyevsky (2)|
|J5|20000|0.753|0.718|0.729|0.562|0.333|0.509|0.720|yes|469|0.686|0.318|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2)|Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), J.R.R. Tolkien (2)|
|BASIN|7500|0.797|0.730|0.740|0.667|0.562|0.681|0.440|yes|418|0.408|0.093|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); leading authors: J.R.R. Tolkien (4), Fyodor Dostoyevsky (2), Art Spiegelman (2), William Shakespeare (1)|Crime and Punishment; Hamlet; The Brothers Karamazov; Between the World and Me; Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1); leading authors: Fyodor Dostoyevsky (2), Art Spiegelman (2), Leo Tolstoy (2), Jorge Luis Borges (2)|
|BASIN|10000|0.785|0.723|0.734|0.351|0.333|0.423|0.320|yes|547|0.507|0.157|Crime and Punishment; Hamlet; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; Between the World and Me; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1)|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; The Two Towers (The Lord of the Rings, #2); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Brian K. Vaughan (2)|
|BASIN|12500|0.768|0.720|0.734|0.667|0.538|0.533|0.980|yes|534|0.549|0.198|Crime and Punishment; Hamlet; The Return of the King (The Lord of the Rings, #3); Between the World and Me; The Brothers Karamazov; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2)|Crime and Punishment; Hamlet; The Brothers Karamazov; The Return of the King (The Lord of the Rings, #3); Ficciones; leading authors: Jorge Luis Borges (4), Fyodor Dostoyevsky (3), Art Spiegelman (3), J.R.R. Tolkien (2)|
|BASIN|15000|0.760|0.720|0.735|0.333|0.205|0.329|0.320|yes|414|0.584|0.230|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; Between the World and Me; The Brothers Karamazov; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2)|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); Hamlet; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Brian K. Vaughan (2)|
|BASIN|17500|0.756|0.719|0.732|0.667|0.333|0.487|0.360|yes|377|0.620|0.269|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; Between the World and Me; The Complete Maus (Maus, #1-2); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2)|Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Brothers Karamazov; Maus I: A Survivor's Tale: My Father Bleeds History (Maus, #1); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2)|
|BASIN|20000|0.753|0.718|0.729|0.562|0.333|0.509|0.720|yes|469|0.686|0.318|The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2)|Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), J.R.R. Tolkien (2)|

### Cross-method rediscovery

The expansion members are compared over the outer J20\J5 users at each tested size.

|n|pair|overlap|Jaccard|
|---:|---|---:|---:|
|7500|L_vs_J5|446|0.098|
|7500|L_vs_BASIN|475|0.105|
|7500|J5_vs_BASIN|431|0.094|
|10000|L_vs_J5|1701|0.205|
|10000|L_vs_BASIN|1822|0.223|
|10000|J5_vs_BASIN|1702|0.205|
|12500|L_vs_J5|3722|0.330|
|12500|L_vs_BASIN|3862|0.347|
|12500|J5_vs_BASIN|3710|0.329|
|15000|L_vs_J5|6714|0.505|
|15000|L_vs_BASIN|6753|0.510|
|15000|J5_vs_BASIN|6629|0.496|
|17500|L_vs_J5|10417|0.714|
|17500|L_vs_BASIN|10464|0.720|
|17500|J5_vs_BASIN|10421|0.715|
|20000|L_vs_J5|15000|1.000|
|20000|L_vs_BASIN|15000|1.000|
|20000|J5_vs_BASIN|15000|1.000|

### Direct → converged head movement

The full top-50 heads, including every title and author, are in `LITERARY_REFINED_EXPANSION_HEADS.md`. For J10/J20-sized expansions the concise movement view is:

**L_10000** direct→final top50 overlap=34/50; direct: Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1); final: The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), George R.R. Martin (2), Fyodor Dostoyevsky (2), Neil Gaiman (2)
**J5_10000** direct→final top50 overlap=32/50; direct: The Return of the King (The Lord of the Rings, #3); Crime and Punishment; The Two Towers (The Lord of the Rings, #2); Hamlet; The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1); final: The Return of the King (The Lord of the Rings, #3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); The Lord of the Rings (The Lord of the Rings, #1-3); A Storm of Swords (A Song of Ice and Fire, #3); leading authors: Neil Gaiman (5), J.R.R. Tolkien (4), George R.R. Martin (2), Brian K. Vaughan (2)
**BASIN_10000** direct→final top50 overlap=26/50; direct: Crime and Punishment; Hamlet; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; Between the World and Me; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1); final: The Return of the King (The Lord of the Rings, #3); Crime and Punishment; The Two Towers (The Lord of the Rings, #2); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Brian K. Vaughan (2)
**L_15000** direct→final top50 overlap=32/50; direct: Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; The Two Towers (The Lord of the Rings, #2); Between the World and Me; leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), William Shakespeare (1); final: The Return of the King (The Lord of the Rings, #3); The Fellowship of the Ring (The Lord of the Rings, #1); A Storm of Swords (A Song of Ice and Fire, #3); The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (5), Neil Gaiman (3), George R.R. Martin (2), Art Spiegelman (2)
**J5_15000** direct→final top50 overlap=31/50; direct: The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; The Two Towers (The Lord of the Rings, #2); The Lord of the Rings (The Lord of the Rings, #1-3); leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2); final: The Return of the King (The Lord of the Rings, #3); A Storm of Swords (A Song of Ice and Fire, #3); The Lord of the Rings (The Lord of the Rings, #1-3); The Two Towers (The Lord of the Rings, #2); The Fellowship of the Ring (The Lord of the Rings, #1); leading authors: J.R.R. Tolkien (5), Neil Gaiman (5), Art Spiegelman (2), George R.R. Martin (1)
**BASIN_15000** direct→final top50 overlap=25/50; direct: Crime and Punishment; The Return of the King (The Lord of the Rings, #3); Hamlet; Between the World and Me; The Brothers Karamazov; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Jorge Luis Borges (2); final: The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); Hamlet; leading authors: J.R.R. Tolkien (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), Brian K. Vaughan (2)
**L_20000** direct→final top50 overlap=36/50; direct: The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2); final: Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), J.R.R. Tolkien (2)
**J5_20000** direct→final top50 overlap=36/50; direct: The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2); final: Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), J.R.R. Tolkien (2)
**BASIN_20000** direct→final top50 overlap=36/50; direct: The Return of the King (The Lord of the Rings, #3); Crime and Punishment; Hamlet; Between the World and Me; A Storm of Swords (A Song of Ice and Fire, #3); leading authors: J.R.R. Tolkien (5), Art Spiegelman (3), Fyodor Dostoyevsky (2), Bill Watterson (2); final: Crime and Punishment; Hamlet; Between the World and Me; The Return of the King (The Lord of the Rings, #3); The Brothers Karamazov; leading authors: Jorge Luis Borges (4), Art Spiegelman (3), Fyodor Dostoyevsky (2), J.R.R. Tolkien (2)

## Coverage

Coverage global work-count source: `/home/ifrankling/unsw/novels/curators_explorer/data/juror_coherence_tail_state/global_work_stats.npz`; global works=523815.

Coverage is reported for raw reader presence; no obscure-book accuracy validation was performed.

Frozen primary context from the prior persisted coverage artifact:

|jury|20–49 ≥1|20–49 ≥3|
|---|---:|---:|
|J5000|0.319|0.038|
|J10000|0.506|0.134|
|J20000|0.686|0.318|
|J30000|0.785|0.465|


## Scientific interpretation

### Does the larger-jury slide come from membership, dynamics, or both?

For ORDER_L at 10k, direct→J5 top-50 Jaccard is `0.538` and final→J5 is `0.250`; at 20k the corresponding values are `0.282` and `0.333`.

The descriptive result supports an interaction: the added membership changes the direct head, and nonlinear reweighting further redirects at least one larger size away from the frozen J5 mode. The size-specific heads must be read together because the sign can differ by N.

### Practical reading

J5 remains the frozen narrow literary core. J10/J20 are not rejected merely because an internal map can amplify a different coherent axis: the direct heads, basin frequencies, individual L profiles, and coverage must be considered separately. J30 and any maximal-jury claim are outside this campaign.

A later adaptive/binary boundary search is scientifically justified only if one ordering shows an approximately monotone size trajectory in actual heads, held-out J5 agreement, and random-init stability. This report does not perform that search or declare a maximum.

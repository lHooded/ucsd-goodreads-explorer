# Literary user-basin affiliation report

Campaign seed: `20260904`. Starting commit: `577698fde5465c0e37b838c1626e58f521f3b134`.
Wall-clock estimate including resumable phases: `57.3` seconds.

This diagnostic preserves all four local basins. No semantic label, J5-agreement score, fitted combined score, or jury-size optimization enters affiliation, matching, or context mapping.

## A. Frozen inherited facts

Frozen-state audit: **40/40 passed**.

|item|value|
|---|---|
|common-L hash|`f6d536d0e37345359344ba3cd94094d1be579067a8c1ff0c7420e9f92a60d49c`|
|universe hash|`2cb504f7284a19d6afb1263471b7d9f43457b167a8f79db6987d773c26a592e4`|
|J10/J20 runs|64 / 64|
|selected k|4 / 4|
|J5-like basin|J10 B1; J20 B1|
|strict-valid runs|J10 63/64; J20 63/64|

## B. User-affiliation reproducibility

|population|basin|Pearson|Spearman|percentile rho|top10|MAE|median |Δ||
|---|---|---|---|---|---|---|---|
|J10000|B1|0.944|0.937|0.937|890/1000|0.072|0.018|
|J10000|B2|0.933|0.924|0.924|877/1000|0.077|0.020|
|J10000|B3|0.931|0.920|0.920|852/1000|0.094|0.024|
|J10000|B4|0.945|0.940|0.940|855/1000|0.096|0.028|
|J20000|B1|0.970|0.966|0.966|1847/2000|0.044|0.013|
|J20000|B2|0.975|0.971|0.971|1880/2000|0.038|0.010|
|J20000|B3|0.978|0.975|0.975|1872/2000|0.038|0.011|
|J20000|B4|0.966|0.961|0.961|1839/2000|0.051|0.014|

Per-shell support reproducibility:
|population|basin|shell|Pearson|Spearman|percentile rho|top10|
|---|---|---|---|---|---|---|
|J10000|B1|S0|0.952|0.946|0.946|457/500|
|J10000|B1|S1|0.937|0.928|0.928|440/500|
|J10000|B2|S0|0.940|0.933|0.933|439/500|
|J10000|B2|S1|0.925|0.915|0.915|438/500|
|J10000|B3|S0|0.943|0.933|0.933|433/500|
|J10000|B3|S1|0.918|0.906|0.906|423/500|
|J10000|B4|S0|0.947|0.944|0.944|438/500|
|J10000|B4|S1|0.942|0.937|0.937|434/500|
|J20000|B1|S0|0.976|0.973|0.973|468/500|
|J20000|B1|S1|0.974|0.972|0.972|464/500|
|J20000|B1|S2|0.964|0.960|0.960|921/1000|
|J20000|B2|S0|0.980|0.977|0.977|475/500|
|J20000|B2|S1|0.978|0.975|0.975|476/500|
|J20000|B2|S2|0.970|0.965|0.965|925/1000|
|J20000|B3|S0|0.984|0.983|0.983|475/500|
|J20000|B3|S1|0.980|0.978|0.978|469/500|
|J20000|B3|S2|0.974|0.970|0.970|923/1000|
|J20000|B4|S0|0.980|0.978|0.978|464/500|
|J20000|B4|S1|0.969|0.966|0.966|464/500|
|J20000|B4|S2|0.957|0.950|0.950|915/1000|

Affinity-vector reproducibility (median split):
- J10000: cosine median `0.999`, Pearson/Spearman flattened `0.938/0.932`.
- J20000: cosine median `1.000`, Pearson/Spearman flattened `0.972/0.969`.

### Raw argmax A/B stability

|population|agreement|κ|A counts|B counts|confusion|bottom10 margin|top25 margin|
|---|---|---|---|---|---|---|---|
|J10000|0.902|0.869|[2451, 2140, 2589, 2820]|[2564, 2045, 2552, 2839]|[[2297, 79, 10, 65], [165, 1863, 95, 17], [5, 85, 2300, 199], [97, 18, 147, 2558]]|0.702|0.935|
|J20000|0.948|0.930|[4774, 4277, 5426, 5523]|[4805, 4180, 5480, 5535]|[[4565, 86, 111, 12], [163, 3995, 6, 113], [68, 7, 5166, 185], [9, 92, 197, 5225]]|0.753|0.980|

- J10000 shell agreement: S0=0.905; S1=0.898
- J20000 shell agreement: S0=0.953; S1=0.951; S2=0.943

## C. Are raw basin weights commensurate?

|population|basin|mean|std|p10|median|p90|skew|user Kish/n|run Kish median|run weight std|
|---|---|---|---|---|---|---|---|---|---|---|
|J10000|B1|0.989|0.693|0.063|1.103|1.832|-0.125|0.671|6740.627|0.695|
|J10000|B2|0.997|0.683|0.066|1.112|1.825|-0.153|0.681|6771.510|0.690|
|J10000|B3|1.007|0.741|0.102|0.890|1.998|0.125|0.649|6436.499|0.744|
|J10000|B4|1.001|0.732|0.108|0.890|1.999|0.147|0.652|6462.927|0.740|
|J20000|B1|0.995|0.687|0.062|1.096|1.839|-0.132|0.677|13560.997|0.689|
|J20000|B2|0.998|0.690|0.065|1.085|1.850|-0.115|0.676|13545.037|0.690|
|J20000|B3|1.001|0.729|0.099|0.908|1.986|0.115|0.653|13046.456|0.730|
|J20000|B4|1.003|0.734|0.103|0.898|2.001|0.134|0.651|12954.808|0.737|

Mean-one trajectory normalization does not make the four support distributions identical; scale and concentration differences are retained rather than corrected away.

## D. Three affiliation representations

|population|method|full counts|A/B agreement|κ|A margin median|low-margin fractions|
|---|---|---|---|---|---|---|
|J10000|raw|[2507, 2087, 2553, 2853]|0.902|0.869|0.175|{"margin_le_0.01": 0.0526, "margin_le_0.05": 0.204}|
|J10000|percentile|[2648, 2471, 2246, 2635]|0.902|0.869|0.091|{"margin_le_0.01": 0.081, "margin_le_0.05": 0.3294}|
|J10000|soft_share|[2507, 2087, 2553, 2853]|0.902|0.869|0.043|{"margin_le_0.01": 0.1728, "margin_le_0.05": 0.5649}|
|J20000|raw|[4775, 4237, 5472, 5516]|0.948|0.930|0.188|{"margin_le_0.01": 0.0401, "margin_le_0.05": 0.1729}|
|J20000|percentile|[5469, 4816, 5185, 4530]|0.945|0.926|0.097|{"margin_le_0.01": 0.07205, "margin_le_0.05": 0.29775}|
|J20000|soft_share|[4775, 4237, 5472, 5516]|0.948|0.930|0.047|{"margin_le_0.01": 0.14485, "margin_le_0.05": 0.5217}|

The normalized soft-share argmax is mathematically identical to the raw-support argmax because the denominator is common across basins for each user. It remains useful as a soft representation, especially through entropy and maximum-share summaries.

- J10000 soft-share max thresholds: max_ge_0.4=0.776; max_ge_0.5=0.102; max_ge_0.6=0.022; max_ge_0.75=0.011
- J20000 soft-share max thresholds: max_ge_0.4=0.800; max_ge_0.5=0.099; max_ge_0.6=0.008; max_ge_0.75=0.004

## E. Tight matched-common-L validation outside J5

Matching rule frozen before head inspection: sort by common-L and user ID, use consecutive bins of 200, and take the upper/lower 25% specificity tails within every bin. The J20 B1-vs-others margin is the only signal.

|population|high n|low n|high L med|low L med|KS|Wasserstein|max |Δ quantile||head cosine|top50|top200|
|---|---|---|---|---|---|---|---|---|---|---|
|J20_outer|3750|3750|0.741|0.740|0.006|0.000|0.000|0.272|0/50|0/200|
|S1|1250|1250|0.767|0.767|0.013|0.000|0.001|0.283|0/50|0/200|
|S2|2500|2500|0.730|0.730|0.010|0.000|0.000|0.269|0/50|0/200|
- J20_outer: high/low direct heads have centered book cosine `0.272` and common-top-200 Spearman `—`.
- S1: high/low direct heads have centered book cosine `0.283` and common-top-200 Spearman `—`.
- S2: high/low direct heads have centered book cosine `0.269` and common-top-200 Spearman `—`.

Complete direct top-100 heads and post-hoc descriptors are in `LITERARY_USER_AFFILIATION_HEADS.md`.

## F. J10 versus J20 context dependence

### Centroid similarity

|J10\J20|B1|B2|B3|B4|
|---|---|---|---|---|
|B1|0.918|0.819|0.729|0.638|
|B2|0.817|0.921|0.625|0.728|
|B3|0.698|0.781|0.801|0.896|
|B4|0.803|0.685|0.896|0.782|

Book-space Hungarian mapping (secondary summary): J10→J20 `[1, 2, 4, 3]`; similarities `[0.918, 0.921, 0.896, 0.896]`.
Row-best margins: `[0.098, 0.104, 0.094, 0.093]`; column-best margins: `[0.101, 0.101, 0.095, 0.114]`.

|method|mapped argmax agreement|κ|confusion|by J10 shell|
|---|---|---|---|---|
|raw|0.764|0.685|[[1959, 409, 26, 113], [242, 1601, 219, 25], [45, 258, 2004, 246], [390, 47, 338, 2078]]|S0=0.767; S1=0.761|
|percentile|0.761|0.680|[[2092, 270, 35, 251], [324, 1789, 309, 49], [38, 229, 1666, 313], [295, 32, 249, 2059]]|S0=0.765; S1=0.756|
|soft_share|0.764|0.685|[[1959, 409, 26, 113], [242, 1601, 219, 25], [45, 258, 2004, 246], [390, 47, 338, 2078]]|S0=0.767; S1=0.761|

Mapped-basin support correlations for shared users:
|J10 shell|matched basin|raw Pearson|raw Spearman|percentile Pearson|top10|
|---|---|---|---|---|---|
|S0|B1|0.891|0.895|0.895|362/500|
|S0|B2|0.870|0.871|0.872|365/500|
|S0|B3|0.854|0.853|0.854|349/500|
|S0|B4|0.883|0.880|0.881|376/500|
|S1|B1|0.840|0.839|0.838|355/500|
|S1|B2|0.859|0.862|0.860|353/500|
|S1|B3|0.808|0.809|0.808|344/500|
|S1|B4|0.860|0.862|0.861|365/500|

Relational context diagnostics: exact basin-order agreement `0.553`; rank-vector Pearson/Spearman `0.821/0.821`; entropy correlation `0.805`.

Affiliations are compared through the book-centroid mapping only; no semantic or user-weight mapping was used. The context-specific user tables are in the JSON/NPZ for basin-by-basin and shell-level inspection.

## G. Sensitivity checks

- J10000 mean-vs-median full raw assignment agreement: `0.950`; mean A/B raw agreement: `0.908`.
- J20000 mean-vs-median full raw assignment agreement: `0.974`; mean A/B raw agreement: `0.950`.
- J10000 excluding unresolved trajectories: all-vs-valid raw assignment agreement `0.992`; valid-run counts `[29, 14, 12, 8]`.
- J20000 excluding unresolved trajectories: all-vs-valid raw assignment agreement `0.998`; valid-run counts `[17, 17, 15, 14]`.
  Valid-run matched-L specificity differences (high minus low): J20_outer=2.107; S1=2.123; S2=2.099
- J10000 across 10 deterministic half-splits: raw agreement median/p10/p90 `0.896/0.892/0.903`; percentile median/p10/p90 `0.898/0.895/0.903`.
- J20000 across 10 deterministic half-splits: raw agreement median/p10/p90 `0.948/0.945/0.949`; percentile median/p10/p90 `0.945/0.941/0.946`.

## H. Descriptive hard partitions

Raw and percentile argmax partitions are descriptive only; no partition is called the final jury and B2 remains independent rather than being coded as good or bad.
|method|group|n|shells|L median|margin median|
|---|---|---|---|---|---|
|raw|raw_B1|4775|{"S0": 1374, "S1": 1262, "S2": 2139}|0.759|0.197|
|raw|raw_B2|4237|{"S0": 1275, "S1": 1040, "S2": 1922}|0.758|0.175|
|raw|raw_B3|5472|{"S0": 1094, "S1": 1368, "S2": 3010}|0.748|0.213|
|raw|raw_B4|5516|{"S0": 1257, "S1": 1330, "S2": 2929}|0.750|0.167|
|percentile|percentile_B1|5469|{"S0": 1559, "S1": 1445, "S2": 2465}|0.758|0.158|
|percentile|percentile_B2|4816|{"S0": 1416, "S1": 1212, "S2": 2188}|0.758|0.140|
|percentile|percentile_B3|5185|{"S0": 1008, "S1": 1283, "S2": 2894}|0.747|0.229|
|percentile|percentile_B4|4530|{"S0": 1017, "S1": 1060, "S2": 2453}|0.749|0.216|

## Interpretation and stop condition

- Split-run support reproducibility is reported separately from population-context stability.
- Raw basin weights are not automatically commensurate; their spread and Kish diagnostics are retained.
- Percentile and raw partitions are compared rather than selecting one by semantic head quality.
- The matched-L groups exclude J5 and separately test S1 and S2; direct book-space separation is the primary validation.
- B2 is preserved as an independent mode. No union, threshold, production jury, maximum-size search, or obscure-book experiment was run.

Post-hoc descriptive partition coverage was computed from the global work-count artifact; it is included in JSON and is not used for any assignment.

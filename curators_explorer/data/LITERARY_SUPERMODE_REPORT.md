# Literary B1+B2 super-mode report

Campaign seed: `20260905`. Starting commit: `b3371b5bec39ecca9e3372ad8b3dac8f7b85a248`.
Wall-clock runtime: `8.5` seconds. Basin trajectories were not rerun.

This is a bounded diagnostic. B1 and B2 remain separate throughout; the semantic-free hypothesis tested here is local `{B1,B2}` versus `{B3,B4}`. No final jury, threshold, maximum search, fitted score, or obscure-book validation was performed.

## A. Correction note

The inherited affiliation campaign was corrected before this experiment:

- The matched-head comparison now passes each group’s actual reader-mass array to the top-200 eligibility filter; no basin trajectory was rerun.
- The percentile hard-partition report now uses `percentile_margin`, not `raw_margin`.
- The previous tautological git-hash comparison was replaced with an actual working-tree-byte versus HEAD-byte comparison, with the intentional correction manifest recorded in the inherited JSON.

Corrected previous matched-head metrics:
|group|top50 overlap|top200 overlap|common top200|Spearman|
|---|---|---|---|---|
|J20_outer|9|43|43|0.099|
|S1|10|62|62|0.297|
|S2|9|54|54|-0.082|

Frozen source audit: **28/28 passed**.
Common-L hash `f6d536d0e37345359344ba3cd94094d1be579067a8c1ff0c7420e9f92a60d49c`; universe hash `2cb504f7284a19d6afb1263471b7d9f43457b167a8f79db6987d773c26a592e4`.

## B. Candidate definitions

All candidates were computed from the frozen four-basin supports before metadata loading:

|candidate|definition|role|
|---|---|---|
|LITSHARE|P(B1)+P(B2)|primary|
|LITCONTRAST|2·LITSHARE−1|descriptive transform|
|RAWSUM|w(B1)+w(B2)|scale sensitivity|
|PCTSUM|within-basin percentile(B1)+percentile(B2)|scale sensitivity|
|B1_SUPPORT|w(B1)|comparator|
|B1_SOFT_SHARE|P(B1)|comparator|
|B1_SPECIFICITY|w(B1)−max(w(B2),w(B3),w(B4))|old comparator|

No free coefficient was fitted and no semantic label entered score construction.

## C. Split-run reproducibility

|population|score|Pearson|Spearman|top10|MAE|median |Δ||
|---|---|---|---|---|---|---|
|J10000|LITSHARE|0.967|0.971|897/1000|0.028|0.010|
|J10000|LITCONTRAST|0.967|0.971|897/1000|0.057|0.020|
|J10000|RAWSUM|0.955|0.962|918/1000|0.120|0.037|
|J10000|PCTSUM|0.949|0.963|913/1000|0.052|0.021|
|J10000|B1_SUPPORT|0.944|0.937|890/1000|0.072|0.018|
|J10000|B1_SOFT_SHARE|0.940|0.948|799/1000|0.020|0.006|
|J10000|B1_SPECIFICITY|0.946|0.957|828/1000|0.100|0.034|
|J20000|LITSHARE|0.981|0.985|1907/2000|0.014|0.005|
|J20000|LITCONTRAST|0.981|0.985|1907/2000|0.029|0.009|
|J20000|RAWSUM|0.975|0.981|1890/2000|0.068|0.022|
|J20000|PCTSUM|0.971|0.981|1898/2000|0.030|0.011|
|J20000|B1_SUPPORT|0.970|0.966|1847/2000|0.044|0.013|
|J20000|B1_SOFT_SHARE|0.970|0.976|1784/2000|0.011|0.003|
|J20000|B1_SPECIFICITY|0.972|0.979|1843/2000|0.058|0.020|

### J10000 shell split checks
|score|shell|Pearson|Spearman|top10|
|---|---|---|---|---|
|LITSHARE|S0|0.972|0.976|451/500|
|LITSHARE|S1|0.961|0.966|439/500|
|LITCONTRAST|S0|0.972|0.976|451/500|
|LITCONTRAST|S1|0.961|0.966|439/500|
|RAWSUM|S0|0.959|0.965|456/500|
|RAWSUM|S1|0.951|0.958|451/500|
|PCTSUM|S0|0.954|0.966|453/500|
|PCTSUM|S1|0.945|0.959|451/500|
|B1_SUPPORT|S0|0.952|0.946|457/500|
|B1_SUPPORT|S1|0.937|0.928|440/500|
|B1_SOFT_SHARE|S0|0.952|0.956|400/500|
|B1_SOFT_SHARE|S1|0.928|0.939|402/500|
|B1_SPECIFICITY|S0|0.954|0.963|419/500|
|B1_SPECIFICITY|S1|0.938|0.951|401/500|

Additional deterministic split repetitions, median/p10/p90:
|score|Pearson med/p10/p90; Spearman med/p10/p90; top10 med/p10/p90|
|---|---|
|LITSHARE|0.964/0.962/0.967/0.968/0.966/0.971/901.500/888.000/905.100|
|LITCONTRAST|0.964/0.962/0.967/0.968/0.966/0.971/901.500/888.000/905.100|
|RAWSUM|0.952/0.948/0.958/0.959/0.955/0.964/906.500/894.500/914.400|
|PCTSUM|0.947/0.940/0.952/0.960/0.956/0.965/904.500/887.500/913.000|
|B1_SUPPORT|0.948/0.946/0.952/0.940/0.937/0.943/902.500/893.600/906.200|
|B1_SOFT_SHARE|0.942/0.940/0.948/0.951/0.948/0.953/799.500/776.900/818.100|
|B1_SPECIFICITY|0.948/0.947/0.953/0.959/0.957/0.962/826.500/809.700/836.900|
Inherited four-basin B1 support split check: Pearson `0.944`, Spearman `0.937`.

### J20000 shell split checks
|score|shell|Pearson|Spearman|top10|
|---|---|---|---|---|
|LITSHARE|S0|0.987|0.990|481/500|
|LITSHARE|S1|0.981|0.987|477/500|
|LITSHARE|S2|0.978|0.982|943/1000|
|LITCONTRAST|S0|0.987|0.990|481/500|
|LITCONTRAST|S1|0.981|0.987|477/500|
|LITCONTRAST|S2|0.978|0.982|943/1000|
|RAWSUM|S0|0.981|0.985|478/500|
|RAWSUM|S1|0.979|0.985|483/500|
|RAWSUM|S2|0.970|0.976|936/1000|
|PCTSUM|S0|0.978|0.986|479/500|
|PCTSUM|S1|0.976|0.986|479/500|
|PCTSUM|S2|0.965|0.976|936/1000|
|B1_SUPPORT|S0|0.976|0.973|468/500|
|B1_SUPPORT|S1|0.974|0.972|464/500|
|B1_SUPPORT|S2|0.964|0.960|921/1000|
|B1_SOFT_SHARE|S0|0.976|0.980|449/500|
|B1_SOFT_SHARE|S1|0.973|0.980|445/500|
|B1_SOFT_SHARE|S2|0.966|0.971|888/1000|
|B1_SPECIFICITY|S0|0.978|0.984|465/500|
|B1_SPECIFICITY|S1|0.974|0.982|461/500|
|B1_SPECIFICITY|S2|0.968|0.974|914/1000|

Additional deterministic split repetitions, median/p10/p90:
|score|Pearson med/p10/p90; Spearman med/p10/p90; top10 med/p10/p90|
|---|---|
|LITSHARE|0.981/0.979/0.982/0.985/0.983/0.985/1905.500/1890.800/1913.800|
|LITCONTRAST|0.981/0.979/0.982/0.985/0.983/0.985/1905.500/1890.800/1913.800|
|RAWSUM|0.976/0.975/0.977/0.981/0.980/0.983/1892.500/1886.900/1903.400|
|PCTSUM|0.973/0.971/0.974/0.982/0.981/0.983/1895.500/1891.900/1903.100|
|B1_SUPPORT|0.970/0.966/0.972/0.967/0.963/0.969/1851.000/1835.400/1861.500|
|B1_SOFT_SHARE|0.969/0.965/0.972/0.975/0.972/0.977/1775.500/1751.500/1786.100|
|B1_SPECIFICITY|0.972/0.968/0.975/0.979/0.976/0.981/1836.500/1829.800/1844.400|
Inherited four-basin B1 support split check: Pearson `0.970`, Spearman `0.966`.

## D. J10↔J20 context stability

The J10→J20 basin correspondence is frozen from book-centroid space; the local B1+B2 sum uses B1/B2 in both contexts. Raw MAE is followed by z-score MAE where raw support scales are not directly comparable.

|score|Pearson|Spearman|top10|median |Δ||z-MAE|
|---|---|---|---|---|---|
|LITSHARE|0.877|0.886|733/1000|0.046|0.307|
|LITCONTRAST|0.877|0.886|733/1000|0.091|0.307|
|RAWSUM|0.877|0.888|741/1000|0.169|0.304|
|PCTSUM|0.876|0.887|746/1000|0.088|0.306|
|B1_SUPPORT|0.866|0.867|713/1000|0.078|0.273|
|B1_SOFT_SHARE|0.855|0.868|657/1000|0.024|0.289|
|B1_SPECIFICITY|0.863|0.871|580/1000|0.132|0.308|

- LITSHARE: S0 rho=0.894, top10=366/500; S1 rho=0.859, top10=354/500
- LITCONTRAST: S0 rho=0.894, top10=366/500; S1 rho=0.859, top10=354/500
- RAWSUM: S0 rho=0.898, top10=372/500; S1 rho=0.855, top10=354/500
- PCTSUM: S0 rho=0.899, top10=373/500; S1 rho=0.851, top10=354/500
- B1_SUPPORT: S0 rho=0.891, top10=362/500; S1 rho=0.840, top10=355/500
- B1_SOFT_SHARE: S0 rho=0.879, top10=324/500; S1 rho=0.829, top10=324/500
- B1_SPECIFICITY: S0 rho=0.883, top10=296/500; S1 rho=0.842, top10=278/500
- LITSHARE absolute context shift: mean_abs=0.084; p50_abs=0.046; p90_abs=0.209; p95_abs=0.315; fraction_abs_gt_0.05=0.474; fraction_abs_gt_0.10=0.261; fraction_abs_gt_0.20=0.107
- Previous four-basin context reference: mapped raw argmax agreement `0.764`, exact basin-order agreement `0.553`.

## E. Numerical B1-specific, B2-specific, joint, and OTHER groups

The frozen rule is applied separately within J20 outer, S1, and S2: B1-specific = B1 soft share ≥ within-scope 75th percentile and B2 below median; B2-specific is symmetric; joint = both B1 and B2 at/above their medians; OTHER = LITSHARE at/below its 25th percentile after removing overlapping categories. These are numerical diagnostic groups, not jury selections.

|scope|group|n|L median|LITSHARE median|
|---|---|---|---|---|
|J20_outer|B1_specific|1668|0.740|0.501|
|J20_outer|B2_specific|1827|0.743|0.494|
|J20_outer|joint|4055|0.744|0.808|
|J20_outer|OTHER|3750|0.739|0.124|
|S1|B1_specific|535|0.767|0.505|
|S1|B2_specific|630|0.768|0.497|
|S1|joint|1335|0.768|0.834|
|S1|OTHER|1250|0.767|0.149|
|S2|B1_specific|1125|0.729|0.497|
|S2|B2_specific|1211|0.730|0.494|
|S2|joint|2714|0.732|0.790|
|S2|OTHER|2500|0.730|0.112|

### J20_outer matched pairwise heads
|comparison|n/side|KS|Wasserstein|cosine|top50|top200|rank rho|Δpos/exact/broad/anti|
|---|---|---|---|---|---|---|---|---|
|B1_specific vs B2_specific|1545|0.007|0.000|0.231|7/50|66/200|0.240|+3/+1/+3/-1|
|B1_specific vs OTHER|1668|0.008|0.000|0.450|18/50|101/200|0.463|+7/+3/+7/-7|
|B2_specific vs OTHER|1827|0.009|0.000|0.415|14/50|87/200|0.388|+2/+1/+2/-6|
|joint vs OTHER|3292|0.009|0.000|0.283|8/50|46/200|0.192|+31/+21/+31/-12|
- characterization_pair_J20_outer_B1_specific_vs_B2_specific L balance: means `0.743/0.743`, std `0.021/0.021`, p10/p25/median/p75/p90 A/B `0.717/0.725/0.741/0.761/0.774` / `0.717/0.725/0.741/0.761/0.774`, KS `0.007`, Wasserstein `0.000`, max quantile Δ `0.000`.
- characterization_pair_J20_outer_B1_specific_vs_OTHER L balance: means `0.743/0.743`, std `0.021/0.021`, p10/p25/median/p75/p90 A/B `0.716/0.724/0.740/0.760/0.774` / `0.717/0.724/0.740/0.760/0.774`, KS `0.008`, Wasserstein `0.000`, max quantile Δ `0.000`.
- characterization_pair_J20_outer_B2_specific_vs_OTHER L balance: means `0.745/0.745`, std `0.021/0.021`, p10/p25/median/p75/p90 A/B `0.717/0.726/0.743/0.762/0.774` / `0.717/0.725/0.743/0.762/0.775`, KS `0.009`, Wasserstein `0.000`, max quantile Δ `0.001`.
- characterization_pair_J20_outer_joint_vs_OTHER L balance: means `0.743/0.743`, std `0.020/0.020`, p10/p25/median/p75/p90 A/B `0.717/0.725/0.741/0.759/0.773` / `0.717/0.725/0.741/0.759/0.773`, KS `0.009`, Wasserstein `0.000`, max quantile Δ `0.000`.

### S1 matched pairwise heads
|comparison|n/side|KS|Wasserstein|cosine|top50|top200|rank rho|Δpos/exact/broad/anti|
|---|---|---|---|---|---|---|---|---|
|B1_specific vs B2_specific|508|0.020|0.000|0.228|8/50|8/200|0.381|+2/+2/+2/-3|
|B1_specific vs OTHER|535|0.026|0.000|0.446|18/50|23/200|0.814|-1/+1/-1/+1|
|B2_specific vs OTHER|630|0.025|0.000|0.395|26/50|38/200|0.709|+0/+0/+0/-3|
|joint vs OTHER|1118|0.024|0.000|0.281|12/50|73/200|0.344|+32/+19/+32/-9|
- characterization_pair_S1_B1_specific_vs_B2_specific L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.760/0.767/0.776/0.782` / `0.756/0.760/0.767/0.776/0.782`, KS `0.020`, Wasserstein `0.000`, max quantile Δ `0.000`.
- characterization_pair_S1_B1_specific_vs_OTHER L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.759/0.767/0.776/0.782` / `0.756/0.760/0.767/0.776/0.782`, KS `0.026`, Wasserstein `0.000`, max quantile Δ `0.000`.
- characterization_pair_S1_B2_specific_vs_OTHER L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.761/0.768/0.776/0.782` / `0.756/0.761/0.768/0.775/0.782`, KS `0.025`, Wasserstein `0.000`, max quantile Δ `0.001`.
- characterization_pair_S1_joint_vs_OTHER L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.760/0.768/0.776/0.782` / `0.756/0.760/0.768/0.776/0.781`, KS `0.024`, Wasserstein `0.000`, max quantile Δ `0.001`.

### S2 matched pairwise heads
|comparison|n/side|KS|Wasserstein|cosine|top50|top200|rank rho|Δpos/exact/broad/anti|
|---|---|---|---|---|---|---|---|---|
|B1_specific vs B2_specific|1031|0.010|0.000|0.211|3/50|43/200|0.482|+4/+2/+4/-1|
|B1_specific vs OTHER|1125|0.013|0.000|0.422|18/50|98/200|0.785|+5/+2/+5/-9|
|B2_specific vs OTHER|1211|0.013|0.000|0.394|16/50|79/200|0.715|+6/+3/+6/-7|
|joint vs OTHER|2230|0.012|0.000|0.283|10/50|64/200|0.087|+30/+21/+30/-14|
- characterization_pair_S2_B1_specific_vs_B2_specific L balance: means `0.730/0.730`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.730/0.740/0.748` / `0.715/0.720/0.730/0.740/0.748`, KS `0.010`, Wasserstein `0.000`, max quantile Δ `0.000`.
- characterization_pair_S2_B1_specific_vs_OTHER L balance: means `0.730/0.730`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.729/0.740/0.747` / `0.715/0.720/0.729/0.740/0.748`, KS `0.013`, Wasserstein `0.000`, max quantile Δ `0.001`.
- characterization_pair_S2_B2_specific_vs_OTHER L balance: means `0.731/0.731`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.730/0.741/0.748` / `0.715/0.721/0.730/0.741/0.748`, KS `0.013`, Wasserstein `0.000`, max quantile Δ `0.000`.
- characterization_pair_S2_joint_vs_OTHER L balance: means `0.731/0.731`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.731/0.741/0.748` / `0.715/0.720/0.730/0.741/0.748`, KS `0.012`, Wasserstein `0.000`, max quantile Δ `0.001`.

## F. Candidate high/low matched-common-L comparisons

For every scope and signal, the same consecutive 200-user L bins and 25% high/low tails are used. Grouping is frozen before semantic annotation. The complete top-100 heads are in `LITERARY_SUPERMODE_HEADS.md`.

|scope|signal|n/side|high L med|low L med|KS|cosine|top50|top200|rank rho|Δpos/exact/broad/anti|
|---|---|---|---|---|---|---|---|---|---|---|
|J20_outer|LITSHARE|3750|0.741|0.740|0.007|0.272|8/50|43/200|0.206|+29/+16/+29/-11|
|J20_outer|PCTSUM|3750|0.741|0.740|0.007|0.272|8/50|42/200|0.216|+30/+19/+30/-12|
|J20_outer|B1_SOFT_SHARE|3750|0.741|0.740|0.006|0.270|8/50|38/200|-0.055|+22/+16/+22/-11|
|J20_outer|B1_SPECIFICITY|3750|0.741|0.740|0.006|0.272|9/50|43/200|0.094|+28/+17/+28/-11|
|S1|LITSHARE|1250|0.767|0.767|0.014|0.283|11/50|74/200|0.158|+31/+17/+31/-9|
|S1|PCTSUM|1250|0.767|0.767|0.014|0.284|11/50|72/200|0.190|+28/+14/+28/-9|
|S1|B1_SOFT_SHARE|1250|0.767|0.767|0.012|0.279|8/50|71/200|0.680|+26/+15/+26/-10|
|S1|B1_SPECIFICITY|1250|0.767|0.767|0.013|0.283|10/50|61/200|0.301|+29/+17/+29/-11|
|S2|LITSHARE|2500|0.730|0.730|0.010|0.269|8/50|51/200|0.029|+31/+20/+31/-13|
|S2|PCTSUM|2500|0.730|0.730|0.010|0.270|8/50|53/200|-0.061|+31/+19/+31/-13|
|S2|B1_SOFT_SHARE|2500|0.730|0.730|0.009|0.267|7/50|55/200|-0.213|+24/+15/+24/-14|
|S2|B1_SPECIFICITY|2500|0.730|0.730|0.010|0.269|9/50|54/200|-0.082|+27/+16/+27/-14|
- J20_outer/LITSHARE L balance: means `0.743/0.743`, std `0.021/0.021`, p10/p25/median/p75/p90 A/B `0.717/0.725/0.741/0.760/0.774` / `0.717/0.725/0.740/0.760/0.774`, KS `0.007`, Wasserstein `0.000`, max quantile Δ `0.001`.
- J20_outer/PCTSUM L balance: means `0.743/0.743`, std `0.021/0.021`, p10/p25/median/p75/p90 A/B `0.717/0.725/0.741/0.760/0.774` / `0.717/0.725/0.740/0.760/0.774`, KS `0.007`, Wasserstein `0.000`, max quantile Δ `0.001`.
- J20_outer/B1_SOFT_SHARE L balance: means `0.743/0.743`, std `0.021/0.021`, p10/p25/median/p75/p90 A/B `0.717/0.725/0.741/0.760/0.774` / `0.717/0.725/0.740/0.760/0.774`, KS `0.006`, Wasserstein `0.000`, max quantile Δ `0.000`.
- J20_outer/B1_SPECIFICITY L balance: means `0.743/0.743`, std `0.021/0.021`, p10/p25/median/p75/p90 A/B `0.717/0.725/0.741/0.760/0.774` / `0.717/0.725/0.740/0.760/0.774`, KS `0.006`, Wasserstein `0.000`, max quantile Δ `0.000`.
- S1/LITSHARE L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.760/0.767/0.775/0.782` / `0.756/0.760/0.767/0.775/0.781`, KS `0.014`, Wasserstein `0.000`, max quantile Δ `0.000`.
- S1/PCTSUM L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.760/0.767/0.775/0.782` / `0.756/0.760/0.767/0.775/0.781`, KS `0.014`, Wasserstein `0.000`, max quantile Δ `0.001`.
- S1/B1_SOFT_SHARE L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.760/0.767/0.775/0.782` / `0.756/0.760/0.767/0.775/0.781`, KS `0.012`, Wasserstein `0.000`, max quantile Δ `0.001`.
- S1/B1_SPECIFICITY L balance: means `0.768/0.768`, std `0.009/0.009`, p10/p25/median/p75/p90 A/B `0.756/0.760/0.767/0.775/0.782` / `0.756/0.760/0.767/0.775/0.781`, KS `0.013`, Wasserstein `0.000`, max quantile Δ `0.001`.
- S2/LITSHARE L balance: means `0.731/0.731`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.730/0.741/0.748` / `0.715/0.720/0.730/0.740/0.748`, KS `0.010`, Wasserstein `0.000`, max quantile Δ `0.001`.
- S2/PCTSUM L balance: means `0.731/0.731`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.730/0.741/0.748` / `0.715/0.720/0.730/0.740/0.748`, KS `0.010`, Wasserstein `0.000`, max quantile Δ `0.001`.
- S2/B1_SOFT_SHARE L balance: means `0.731/0.731`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.730/0.741/0.748` / `0.715/0.720/0.730/0.740/0.748`, KS `0.009`, Wasserstein `0.000`, max quantile Δ `0.000`.
- S2/B1_SPECIFICITY L balance: means `0.731/0.731`, std `0.012/0.012`, p10/p25/median/p75/p90 A/B `0.715/0.720/0.730/0.741/0.748` / `0.715/0.720/0.730/0.740/0.748`, KS `0.010`, Wasserstein `0.000`, max quantile Δ `0.000`.

## G. Direct B1 versus B2 semantic descriptors

These descriptors are post-hoc annotations of the already-frozen direct heads. They are not selection criteria.

|scope|group|top-50 descriptors|
|---|---|---|
|J20_outer|B1_specific|pos/exact/broad/anti=10/5/10/3; comics=3; authors=42; max-author=3|
|J20_outer|B2_specific|pos/exact/broad/anti=5/3/5/3; comics=17; authors=29; max-author=10|
|J20_outer|joint|pos/exact/broad/anti=32/19/32/0; comics=4; authors=33; max-author=5|
|J20_outer|OTHER|pos/exact/broad/anti=3/1/3/12; comics=3; authors=33; max-author=7|
|S1|B1_specific|pos/exact/broad/anti=7/6/7/17; comics=0; authors=40; max-author=3|
|S1|B2_specific|pos/exact/broad/anti=7/5/7/11; comics=3; authors=33; max-author=5|
|S1|joint|pos/exact/broad/anti=34/22/34/0; comics=2; authors=36; max-author=4|
|S1|OTHER|pos/exact/broad/anti=5/4/5/10; comics=1; authors=35; max-author=7|
|S2|B1_specific|pos/exact/broad/anti=7/4/7/5; comics=1; authors=44; max-author=4|
|S2|B2_specific|pos/exact/broad/anti=7/4/7/5; comics=13; authors=29; max-author=11|
|S2|joint|pos/exact/broad/anti=31/20/31/0; comics=5; authors=35; max-author=5|
|S2|OTHER|pos/exact/broad/anti=3/1/3/14; comics=3; authors=31; max-author=8|

- J20_outer pairwise qualitative contrasts: characterization_pair_J20_outer_B1_specific_vs_B2_specific: Δpos/exact/broad/anti=+3/+1/+3/-1; characterization_pair_J20_outer_B1_specific_vs_OTHER: Δpos/exact/broad/anti=+7/+3/+7/-7; characterization_pair_J20_outer_B2_specific_vs_OTHER: Δpos/exact/broad/anti=+2/+1/+2/-6; characterization_pair_J20_outer_joint_vs_OTHER: Δpos/exact/broad/anti=+31/+21/+31/-12
- S1 pairwise qualitative contrasts: characterization_pair_S1_B1_specific_vs_B2_specific: Δpos/exact/broad/anti=+2/+2/+2/-3; characterization_pair_S1_B1_specific_vs_OTHER: Δpos/exact/broad/anti=-1/+1/-1/+1; characterization_pair_S1_B2_specific_vs_OTHER: Δpos/exact/broad/anti=+0/+0/+0/-3; characterization_pair_S1_joint_vs_OTHER: Δpos/exact/broad/anti=+32/+19/+32/-9
- S2 pairwise qualitative contrasts: characterization_pair_S2_B1_specific_vs_B2_specific: Δpos/exact/broad/anti=+4/+2/+4/-1; characterization_pair_S2_B1_specific_vs_OTHER: Δpos/exact/broad/anti=+5/+2/+5/-9; characterization_pair_S2_B2_specific_vs_OTHER: Δpos/exact/broad/anti=+6/+3/+6/-7; characterization_pair_S2_joint_vs_OTHER: Δpos/exact/broad/anti=+30/+21/+30/-14

### Explicit evidence assessment

B2 is not equivalent to B1 in the frozen outer-user heads. It remains numerically and label-free distinct from OTHER, but its semantic profile is mixed rather than a second copy of the joint literary head:
- J20_outer B2-specific: pos/exact/broad/anti=5/3/5/3; comics=17; authors=29; max-author=10; OTHER: pos/exact/broad/anti=3/1/3/12; comics=3; authors=33; max-author=7; matched-L head cosine `0.415`, top200 `87/200`.
- S1 B2-specific: pos/exact/broad/anti=7/5/7/11; comics=3; authors=33; max-author=5; OTHER: pos/exact/broad/anti=5/4/5/10; comics=1; authors=35; max-author=7; matched-L head cosine `0.395`, top200 `38/200`.
- S2 B2-specific: pos/exact/broad/anti=7/4/7/5; comics=13; authors=29; max-author=11; OTHER: pos/exact/broad/anti=3/1/3/14; comics=3; authors=31; max-author=8; matched-L head cosine `0.394`, top200 `79/200`.
The strongest positive evidence for including B2 in a broader super-mode is therefore conditional: B2-specific users do not collapse into OTHER, especially in S2, but they are less literary-looking and more graphic/prestige-geek concentrated than the joint B1+B2 group. The simple union hypothesis is supported as a diagnostic axis, not as proof that every B2-specific reader belongs to the same literary mode as B1.

LITSHARE is more context-stable than the B1-only soft share and the old B1-specificity signal in the shared-user ranking diagnostics, while preserving matched-L high/low head separation in J20 outer, S1, and S2. This supports retaining B1+B2 as a portable super-mode candidate, with B1/B2 kept separately for the next validation.

## H. Interpretation

### Does B2 look independently literary?

The answer is judged by the B2-specific versus OTHER and B2-specific versus B1-specific matched comparisons, not by a single title list. Inspect the head file together with the label-free cosine/overlap rows and the probe contrasts. A B2-specific group that remains separated from OTHER at matched L and retains broad/exact literary representation supports B2 as an independent literary-compatible submode; similarity to B1 is not required.

### Does the simple B1+B2 super-mode improve portability?

LITSHARE J10↔J20 Pearson `0.877` and Spearman `0.886` are compared against the inherited four-way and B1-only context diagnostics above. A high correlation would support a portable super-mode, while strong matched-L separation is needed to show that portability is not merely loss of discrimination.

### Relation to the old three-pile intuition

The post-hoc heads allow the data to be compared with a literary / cultured-mainstream / fandom interpretation resembling B1+B2 / B3 / B4. This is an interpretation, not a coded rule. B2 remains an independent mode in all arrays and tables.

## I. Stop condition and next experiment

This campaign stops here. It did not construct a final jury, fit a combined score, choose a threshold, search a maximum, validate obscure-book recommendations, or run binary/adaptive jury-size search.

The next scientifically warranted experiment, conditional on the matched B2 results, is a predeclared soft-affiliation jury construction that retains B1 and B2 as separate diagnostic dimensions and tests out-of-sample stability before any population-size boundary search. If B2-specific separation collapses, the next step should instead improve the user-affinity estimator rather than merge B1 and B2.

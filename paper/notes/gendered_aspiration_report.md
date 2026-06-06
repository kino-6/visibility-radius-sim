# Gendered Aspirational Selectivity Follow-Up

This follow-up adds an abstract binary gender label to pair formation.
It does not add sex-specific reproductive biology. Pairs are constrained
to be A-B pairs, and one side can be assigned stronger aspirational
selectivity by requiring candidates to clear a relative score quantile
inside the perceived comparison pool.
The baseline reproductive window is 18-45. Additional sensitivity
conditions restrict reproduction to ages 20-39 to represent a tighter
time limit for delayed learning and pair formation.

The loaded term `high standards` is represented here only as a model
mechanism: candidates are ignored unless they rank high enough relative
to the perceived candidate pool. It is not a moral claim about either
gender.

## Output Files

- `outputs/gendered_aspiration/gendered_aspiration_raw.csv`
- `outputs/gendered_aspiration/gendered_aspiration_run_summary.csv`
- `outputs/gendered_aspiration/gendered_aspiration_summary.csv`
- `outputs/gendered_aspiration/gendered_aspiration_summary.png`

## Summary

| label | aspiration_profile | aspiration_quantile | reproductive_window | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_unmatched_a_mean | late_unmatched_b_mean | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Symmetric, reserve 25% | none | 0.000 | 18-45 | 3 | 0.758 | 0.672 | 0.868 | 0.329 | 0.268 | 0.035 | 0.122 | 0.878 |
| B income floor 500+ proxy | fixed 0.55 | 0.550 | 18-45 | 3 | 0.635 | 0.616 | 0.646 | 0.310 | 0.250 | 0.039 | 0.118 | 0.882 |
| B income floor 700+ proxy | fixed 0.80 | 0.800 | 18-45 | 3 | 0.086 | 0.065 | 0.112 | 0.468 | 0.550 | 0.027 | 0.042 | 0.958 |
| B mixed: 500+ base, light compound tail | mix 55/25/15/5 at 0.55/0.75/0.87/0.90 | 0.666 | 18-45 | 3 | 0.438 | 0.336 | 0.518 | 0.339 | 0.273 | 0.037 | 0.086 | 0.913 |
| B mixed: compound-heavy tail | mix 25/25/35/15 at 0.55/0.75/0.87/0.90 | 0.766 | 18-45 | 3 | 0.222 | 0.176 | 0.293 | 0.416 | 0.391 | 0.035 | 0.065 | 0.935 |
| B compound-heavy, reserve 50% | mix 25/25/35/15 at 0.55/0.75/0.87/0.90 | 0.766 | 18-45 | 3 | 0.265 | 0.200 | 0.392 | 0.391 | 0.426 | 0.036 | 0.080 | 0.920 |
| B compound-heavy, no reserve | mix 25/25/35/15 at 0.55/0.75/0.87/0.90 | 0.766 | 18-45 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Symmetric, reserve 25%, repro 20-39 | none | 0.000 | 20-39 | 3 | 0.141 | 0.112 | 0.167 | 0.372 | 0.315 | 0.043 | 0.038 | 0.950 |
| B income floor 500+ proxy, repro 20-39 | fixed 0.55 | 0.550 | 20-39 | 3 | 0.065 | 0.053 | 0.080 | 0.454 | 0.487 | 0.032 | 0.019 | 0.958 |
| B mixed: light compound tail, repro 20-39 | mix 55/25/15/5 at 0.55/0.75/0.87/0.90 | 0.666 | 20-39 | 3 | 0.044 | 0.031 | 0.059 | 0.469 | 0.504 | 0.027 | 0.018 | 0.838 |
| B mixed: compound-heavy tail, repro 20-39 | mix 25/25/35/15 at 0.55/0.75/0.87/0.90 | 0.766 | 20-39 | 3 | 0.011 | 0.002 | 0.019 | 0.393 | 0.470 | 0.010 | 0.004 | 0.261 |

## Interpretation

This run tests relative aspiration rather than reduced attention count.
The aspirational side keeps the same top-k capacity. In fixed scenarios,
candidates below the configured perceived-pool score quantile are not selected.
In mixed scenarios, aspirational agents carry heterogeneous thresholds, with
a 500+ income-floor proxy as the lower-demand case and compound-condition tails
near the top 13% to top 10% range.
The 20-39 sensitivity rows test whether the same selection pressure
becomes more damaging when the model has less time to recover from
delayed matching.

The failure mode is not simply that the aspirational side remains
unmatched. Because pair formation requires mutual selection, stricter
selection on one side can reduce realized pairs for both sides. The model
mainly amplifies the bounded-attention bottleneck rather than producing
large reproductive concentration, because agents cannot hold multiple
simultaneous reproductive pairs.

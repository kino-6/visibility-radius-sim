# Extinction Driver Analysis

Branch: `analysis/extinction-drivers`

This is an exploratory ablation of the current `sns-2000s` scenario. It compares the default run against variants that remove or relax one mechanism at a time.

## Summary

The main driver of the population collapse is not the candidate-pool multiplier by itself. In the current implementation, `candidate_pool_multiplier` is recorded as perceived comparison pressure, but it does not change which candidates agents evaluate. The behavioral shock comes from this combination:

1. `visibility_radius` expands to near-global.
2. `action_radius` remains local.
3. Agents use bounded `top-k` selection over the expanded visible pool.

After the visibility shock, most selected top candidates are outside action range. Mutual selection therefore becomes much less likely to produce active pairs, which lowers births per eligible agent.

## Seed 42 Ablation

Key outcomes from `../../outputs/factor_analysis/factor_analysis_seed42.csv`:

- Current SNS scenario: final population ratio `0.491`.
- Fixed local visibility: final population ratio `0.834`.
- Radius shock without candidate multiplier: final population ratio `0.491`.
- Global action radius: final population ratio `0.678`.
- `top_k=64`: final population ratio `0.940`.
- Percentile selection: final population ratio `0.722`.

This indicates that candidate multiplier is not yet causal in the model. The strongest rescue comes from loosening bounded attention (`top_k=64`) or removing the visibility/action mismatch.

## Multi-Seed Average

Key outcomes from `../../outputs/factor_analysis/factor_analysis_multiseed_summary.csv`:

- Current SNS scenario: mean final population ratio `0.554`.
- Fixed local visibility: mean final population ratio `0.936`.
- Global action radius: mean final population ratio `0.723`.
- `action_radius=0.50`: mean final population ratio `0.694`.
- Percentile selection: mean final population ratio `0.838`.
- `top_k=64`: mean final population ratio `1.003`.

The late-period unmatched rate is highest in the current SNS scenario (`0.838`) and falls sharply when top-k attention is relaxed (`0.279`) or the model uses percentile selection (`0.410`).

## Interpretation

The current model says:

- Local visibility is viable or only mildly declining.
- Rapid global visibility with local action range causes selected candidates to become mostly non-actionable.
- Bounded top-k attention makes this worse because agents spend their limited selection slots on globally visible candidates.
- Increasing candidate volume from `30x` to `300x` does not change behavior yet because candidate multiplier is only a metric, not part of the selection algorithm.

## Phantom Candidate Follow-Up

The branch now implements sampled phantom candidates. In this mode, `candidate_pool_multiplier` creates non-pairable comparison candidates that can enter the top-k competition. Phantom candidates have sampled trait vectors and can consume selection slots, but they cannot form pairs.

Key seed-42 comparison from `../../outputs/phantom_candidates/phantom_candidate_comparison_seed42.csv`:

- Old behavior with `phantom_candidate_mode=none`: final population ratio `0.491`.
- Default sampled phantom mode, cap `512`: final population ratio `0.415`.
- Phantom cap `64`: final population ratio `0.438`.
- Phantom cap `1024`: final population ratio `0.414`.

In the default sampled phantom run, late-period `mean_phantom_selection_share` is about `0.850`, meaning roughly 85% of top-k slots are taken by non-pairable comparison candidates in the late period. This makes candidate-pool expansion causal rather than only diagnostic.

## Extinction Avoidance Follow-Up

The branch now includes `actionable_selection_reserve_fraction`, an intervention knob that reserves part of the top-k selection quota for real candidates inside action radius before phantom/global comparison candidates can consume the remaining slots.

Seed-42 results from `../../outputs/extinction_avoidance/extinction_avoidance_reserve_seed42.csv`:

- Current phantom scenario, no reserve: final population ratio `0.415`.
- Reserve `0.25`: final population ratio `0.811`.
- Reserve `0.50`: final population ratio `0.945`.
- Reserve `0.75`: final population ratio `0.941`.
- Reserve `1.00`: final population ratio `0.959`.

Five-seed averages from `../../outputs/extinction_avoidance/extinction_avoidance_reserve_multiseed_summary.csv`:

- Current phantom scenario, no reserve: mean final ratio `0.471`.
- Reserve `0.25`: mean final ratio `0.886`.
- Reserve `0.50`: mean final ratio `1.030`.
- Reserve `0.75`: mean final ratio `1.064`.

This suggests a plausible avoidance mechanism inside the model: do not remove broad visibility entirely, but protect a minimum share of attention for actionable local candidates. In simulation terms, this keeps enough real mutual pair formation alive that the population trajectory avoids collapse.

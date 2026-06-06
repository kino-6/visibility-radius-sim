# Appendix Follow-Up Plan

This document tracks the seven follow-up experiments proposed after the first
working-paper results. The original intuition was that radius expansion itself
would suppress population viability. The current model suggests a sharper
mechanism:

```text
visibility expansion matters most when it creates an actionability gap
and non-actionable candidates consume bounded top-k attention.
```

The appendix experiments below test that revised interpretation.

## Shared Setup

All experiments use the `sns-2000s` scenario as the base unless noted.

- Horizon: 180 simulated years
- Initial population: 1200
- Seeds: 0, 1, 2 for most sweeps
- Detailed outputs: written under `outputs/appendix_followups/`
- Main measures:
  - final population ratio
  - minimum population ratio
  - late births per eligible
  - late unmatched rate
  - selected actionable share
  - phantom selection share
  - visibility/action gap
  - candidate-pool multiplier

This is a compact follow-up suite, not a publication-grade full parameter
search. The goal is to check whether the core mechanism survives several
obvious alternative explanations.

## A. Radius Alone

Question:

> Does radius expansion alone suppress viability, or does it require an
> actionability gap and phantom comparison?

Comparison:

- local visibility and local action
- global visibility and global action
- global visibility with local action, no phantom candidates
- full SNS shock with phantom candidates

Expected interpretation:

If radius alone is weak, then global visibility should not be catastrophic when
all visible candidates remain actionable. Collapse should concentrate in the
action-gap plus phantom condition.

## B. Top-k vs Percentile Selection

Question:

> Is bounded top-k attention more fragile than percentile-style selection?

Comparison:

- top-k with several `top_k` values
- percentile selection with low and default selectivity

Expected interpretation:

If the mechanism is about bounded attention, top-k selection should be more
vulnerable to phantom displacement than percentile selection that expands its
quota with the visible pool.

## C. Candidate-Pool Multiplier Sweep

Question:

> Is the SNS-like effect better represented by candidate count expansion than
> by spatial radius?

Comparison:

`max_candidate_pool_multiplier` sweep:

```text
1x, 10x, 30x, 100x, 300x, 1000x
```

Expected interpretation:

If phantom comparison is causal, final population should decline as perceived
candidate-pool multiplier rises, especially when action radius stays local.

## D. Visibility/Action Gap

Question:

> Does the gap between visible candidates and actionable candidates explain the
> collapse better than radius alone?

Comparison:

Sweep `action_radius` while visibility expands globally.

Expected interpretation:

Small action radius should produce high visibility/action gap, low selected
actionable share, and lower final population. Larger action radius should
reduce the gap and improve viability.

## E. Reserve Threshold Robustness

Question:

> Does the protected-slot threshold survive different top-k capacities?

Comparison:

`top_k` values:

```text
8, 16, 32, 64
```

Protected actionable slots:

```text
0, 1, 2, 4, 8, 16, 32
```

Invalid slot counts above `top_k` are skipped.

Expected interpretation:

The threshold should scale with slot count rather than with reserve fraction
alone. The relevant unit is expected to be protected actionable slots inside
bounded attention.

## F. Cultural Overconstraint

Question:

> Can actionable-reserve culture become too restrictive?

Comparison:

Reserve fractions:

```text
0.00, 0.0625, 0.125, 0.25, 0.50, 0.75, 0.90, 1.00
```

Expected interpretation:

The earlier result suggested survival above a threshold. This test checks
whether extreme reserve reduces search quality or whether the main effect is
only threshold-like survival.

## G. Institutional Learning

Question:

> Can regions adapt their reserve culture after observing demographic decline?

Comparison:

- no learning
- slow learning
- fast learning
- preadapted reserve reference

Implementation note:

This follow-up uses a runner-local subclass of `Simulation` with mutable
region-level reserve values. Every decade, regions that decline relative to the
previous decade increase their actionable reserve fraction. This keeps the core
simulation code unchanged while testing the institutional-learning mechanism.

Expected interpretation:

If learning is early and strong enough, the system should avoid deeper
bottlenecks. If learning is too late, late birth recovery may not rescue final
population ratio.

## Outputs

Expected output files:

- `outputs/appendix_followups/appendix_followups_raw.csv`
- `outputs/appendix_followups/appendix_followups_summary.csv`
- `outputs/appendix_followups/appendix_followups_report.md`
- `outputs/appendix_followups/appendix_followups_overview.png`
- one PNG per experiment section

The final report is also summarized in `docs/appendix_followups_results.md`
and copied into the paper bundle as an appendix note.

## Execution Status

Completed on 2026-06-06.

Canonical generated outputs:

- `docs/appendix_followups_results.md`
- `paper/notes/appendix_followups_report.md`
- `paper/appendix_followups/appendix_followups_report.md`
- `outputs/appendix_followups/appendix_followups_summary.csv`
- `outputs/appendix_followups/appendix_followups_overview.png`

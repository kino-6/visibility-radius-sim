# Actionable Reserve Threshold Report

This report checks whether the survival effect is continuous or threshold-like.

## Setup

- Scenario base: `sns-2000s`
- Horizon: 240 years, 1980-2219
- Selection mode: `top-k`
- `top_k`: 16
- Phantom candidates: enabled
- Cross-region pairing: allowed

Two sweeps were generated:

- `reserve_threshold_seed42_summary.csv`: dense reserve-fraction sweep for seed 42.
- `reserve_threshold_slots_multiseed_summary.csv`: protected top-k slot sweep across seeds 0, 1, and 2.

## Key Finding

The effect is threshold-like, but the threshold is discrete because `top_k=16`.

`actionable_selection_reserve_fraction` becomes an integer number of protected top-k slots. For example:

- `0.0000`: 0 protected slots
- `0.0625`: 1 protected slot
- `0.1250`: 2 protected slots
- `0.2500`: 4 protected slots
- `0.5000`: 8 protected slots

So weak/medium/strong cultures can look similar once they are above the minimum viable range.

## Multi-Seed Slot Results

From `reserve_threshold_slots_multiseed_summary.csv`:

| Protected slots | Reserve fraction | Mean final ratio |
|---:|---:|---:|
| 0 | 0.0000 | 0.001 |
| 1 | 0.0625 | 0.094 |
| 2 | 0.1250 | 0.390 |
| 3 | 0.1875 | 0.613 |
| 4 | 0.2500 | 0.735 |
| 5 | 0.3125 | 0.842 |
| 6 | 0.3750 | 0.890 |
| 8 | 0.5000 | 0.983 |

This suggests the model has a survival gradient rather than a single exact cliff, but the major transition happens between 0 and roughly 4-6 protected slots.

## Interpretation

The key distinction is not simply whether late-period birth rate recovers. With one protected slot, late births per eligible agent rises again, but final population remains low because the system has already passed through a deep demographic bottleneck.

The more meaningful survival condition is:

```text
enough actionable slots early enough to prevent a deep bottleneck
```

In this setup, 1-2 protected slots are too weak. Four slots begin to stabilize the system, and eight slots nearly preserve the starting population.

## Hypothesis Update

The cultural trait does not need to be perfect. It only needs to keep enough actionable candidates in attention long enough for the reproduction loop to avoid collapse.

That supports the intuition:

```text
Weak to strong virtual-world-resilient cultures may all survive,
while cultures with no virtual-world correction are selected out.
```

Differences above the survival threshold affect population share and recovery depth more than the binary survival outcome.

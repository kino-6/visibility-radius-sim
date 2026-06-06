# Gendered Aspiration Robustness Sweep

This exploratory sweep checks whether the gendered aspiration result depends on one convenient
calibration. It varies fertility, initial pair stock, pair duration, perceived SNS pool size,
top-k capacity, actionable reserve, and reproductive age window.

This is not a demographic calibration. It is a mechanism robustness check over the existing
`sns-2000s` toy scenario.

## Outputs

- `outputs/gendered_robustness/gendered_robustness_raw.csv`
- `outputs/gendered_robustness/gendered_robustness_run_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_heatmap.png`

## Compact Summary

| calibration_label | symmetric | income_500_floor | mixed_light | mixed_heavy | heavy_delta | heavy_retained |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline calibration | 0.758 | 0.635 | 0.438 | 0.222 | -0.537 | 0.292 |
| Lower birth probability | 0.231 | 0.115 | 0.089 | 0.051 | -0.180 | 0.221 |
| Higher birth probability | 1.813 | 1.745 | 1.472 | 1.259 | -0.554 | 0.695 |
| Lower initial pair stock | 0.813 | 0.560 | 0.443 | 0.193 | -0.621 | 0.237 |
| Higher initial pair stock | 0.758 | 0.635 | 0.438 | 0.222 | -0.537 | 0.292 |
| Shorter pair duration | 0.915 | 0.672 | 0.483 | 0.297 | -0.618 | 0.324 |
| Longer pair duration | 0.849 | 0.521 | 0.406 | 0.169 | -0.680 | 0.199 |
| Lower SNS pool multiplier | 0.793 | 0.646 | 0.414 | 0.225 | -0.567 | 0.284 |
| Higher SNS pool multiplier | 0.786 | 0.653 | 0.419 | 0.206 | -0.580 | 0.262 |
| Larger top-k capacity | 0.832 | 0.648 | 0.524 | 0.265 | -0.567 | 0.318 |
| Reserve 50% | 0.832 | 0.648 | 0.524 | 0.265 | -0.567 | 0.318 |
| Reproductive window 20-44 | 0.515 | 0.315 | 0.219 | 0.094 | -0.422 | 0.182 |
| Reproductive window 20-39 | 0.141 | 0.065 | 0.044 | 0.011 | -0.130 | 0.080 |

## Interpretation

The sign of the aspiration penalty is stable across the tested calibrations: compound-heavy
aspiration is below the symmetric condition in every row. The magnitude is not stable.
Birth probability, reproductive age window, and reserve/top-k parameters change whether the
system looks like decline, collapse, or partial survival.

# Appendix Follow-Up Results

Japanese translation: `appendix_followups_report_ja.md`

This report summarizes seven follow-up experiments that test whether the
working-paper mechanism is better described as radius expansion itself, or
as an actionability gap interacting with bounded attention.

## Output Files

- `outputs/appendix_followups/appendix_followups_raw.csv`
- `outputs/appendix_followups/appendix_followups_run_summary.csv`
- `outputs/appendix_followups/appendix_followups_summary.csv`
- `outputs/appendix_followups/appendix_followups_overview.png`

## Key Findings

1. **Radius alone is not the main collapse mechanism.**

   Local visibility/local action remained viable (`final_ratio_mean=1.055`).
   Global visibility/global action also remained viable enough
   (`final_ratio_mean=0.760`). The severe drop appears when global visibility
   is combined with local action (`0.314`) and becomes total collapse under
   the full phantom-comparison SNS shock (`0.000`).

2. **Candidate-pool multiplier is harsher than spatial radius.**

   With no phantom multiplier (`1x`), the model survived at a reduced level
   (`0.381`). At `10x` and above, the compact follow-up suite collapsed under
   no-reserve top-k attention. This supports the revised interpretation that
   SNS-like expansion is better modeled as perceived candidate-count expansion
   than as distance alone.

3. **Top-k bounded attention is fragile, but percentile selection is not a full rescue.**

   Top-k variants collapsed without reserve. Percentile selection improved
   slightly only at higher selectivity (`0.18 -> 0.055`), but remained far below
   viability. In this parameterization, expanding the quota helps, but does not
   solve phantom displacement by itself.

4. **Action radius alone does not rescue the system when phantom competition is extreme.**

   The action-radius sweep still collapsed even at global action radius. That
   means the actionability gap is necessary but not sufficient as an explanation:
   extreme phantom comparison can dominate top-k attention even when action
   radius is widened, unless attention slots are protected.

5. **Protected actionable slots are robust across top-k sizes.**

   Across `top_k=8,16,32,64`, zero protected slots collapsed or nearly
   collapsed. Two slots often moved the system into partial survival, and four
   slots usually approached or exceeded viability. This reinforces the
   protected-slot interpretation over reserve fraction alone.

6. **No overconstraint penalty appeared in this version.**

   Reserve fractions above the threshold did not reduce viability. In this
   model, high actionable reserve is not yet costly enough. A future version
   needs search-quality, preference mismatch, or opportunity-cost penalties to
   test whether strong culture can become too restrictive.

7. **Institutional learning can work if it is early and strong enough.**

   No learning collapsed. Slow learning recovered to `0.667`; fast learning
   recovered to `0.945`, close to the preadapted reserve reference (`0.996`).
   This supports the idea that individuals do not all need conscious insight if
   regions/institutions adapt reserve norms quickly enough.

## Caution

Several late-period rates are `0.000` in collapsed scenarios. These are not
evidence of stable low-unmatched conditions; they are denominator artifacts
after eligible population collapse. For collapsed runs, read final population
ratio and minimum population ratio first.

## a_radius_alone

| label | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean | late_visibility_action_gap_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local visibility, local action | 3 | 1.055 | 0.983 | 1.147 | 0.034 | 0.960 | 0.000 | 0.000 |
| Global visibility, global action | 3 | 0.760 | 0.740 | 0.796 | 0.035 | 1.000 | 0.000 | 0.000 |
| Global visibility, local action, no phantom | 3 | 0.314 | 0.231 | 0.415 | 0.031 | 0.132 | 0.000 | 0.820 |
| Full SNS shock with phantom | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Figure: `outputs/appendix_followups/a_radius_alone_summary.png`

## b_selection_mode

| label | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean | late_visibility_action_gap_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Top-k 8 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Top-k 16 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Top-k 32 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Percentile 0.02 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Percentile 0.08 | 3 | 0.003 | 0.001 | 0.007 | 0.002 | 0.003 | 0.226 | 0.089 |
| Percentile 0.18 | 3 | 0.055 | 0.027 | 0.107 | 0.019 | 0.009 | 0.960 | 0.541 |

Figure: `outputs/appendix_followups/b_selection_mode_summary.png`

## c_candidate_multiplier

| label | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean | late_visibility_action_gap_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1x perceived pool | 3 | 0.381 | 0.356 | 0.428 | 0.038 | 0.142 | 0.000 | 0.824 |
| 10x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 30x perceived pool | 3 | 0.000 | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 |
| 100x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 300x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1000x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Figure: `outputs/appendix_followups/c_candidate_multiplier_summary.png`

## d_actionability_gap

| label | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean | late_visibility_action_gap_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Global visibility, action radius 0.03 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.06 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.12 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.24 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.48 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius global | 3 | 0.000 | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 |

Figure: `outputs/appendix_followups/d_actionability_gap_summary.png`

## e_reserve_threshold_robustness

| label | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean | late_visibility_action_gap_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top-k 8, protected slots 0 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| top-k 8, protected slots 1 | 3 | 0.087 | 0.076 | 0.094 | 0.042 | 0.065 | 0.935 | 0.832 |
| top-k 8, protected slots 2 | 3 | 0.716 | 0.703 | 0.736 | 0.035 | 0.244 | 0.756 | 0.853 |
| top-k 8, protected slots 4 | 3 | 0.965 | 0.920 | 0.992 | 0.033 | 0.443 | 0.557 | 0.848 |
| top-k 8, protected slots 8 | 3 | 1.057 | 0.993 | 1.134 | 0.035 | 0.579 | 0.421 | 0.873 |
| top-k 16, protected slots 0 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| top-k 16, protected slots 1 | 3 | 0.224 | 0.182 | 0.257 | 0.035 | 0.058 | 0.942 | 0.669 |
| top-k 16, protected slots 2 | 3 | 0.681 | 0.677 | 0.687 | 0.032 | 0.122 | 0.878 | 0.842 |
| top-k 16, protected slots 4 | 3 | 0.996 | 0.974 | 1.023 | 0.034 | 0.222 | 0.778 | 0.853 |
| top-k 16, protected slots 8 | 3 | 1.040 | 1.015 | 1.085 | 0.035 | 0.275 | 0.725 | 0.874 |
| top-k 16, protected slots 16 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.294 | 0.706 | 0.874 |
| top-k 32, protected slots 0 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| top-k 32, protected slots 1 | 3 | 0.153 | 0.133 | 0.188 | 0.040 | 0.026 | 0.962 | 0.738 |
| top-k 32, protected slots 2 | 3 | 0.705 | 0.664 | 0.761 | 0.036 | 0.060 | 0.940 | 0.866 |
| top-k 32, protected slots 4 | 3 | 0.993 | 0.943 | 1.050 | 0.035 | 0.107 | 0.893 | 0.868 |
| top-k 32, protected slots 8 | 3 | 1.072 | 1.021 | 1.123 | 0.035 | 0.147 | 0.853 | 0.868 |
| top-k 32, protected slots 16 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.147 | 0.853 | 0.874 |
| top-k 32, protected slots 32 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.147 | 0.853 | 0.874 |
| top-k 64, protected slots 0 | 3 | 0.025 | 0.017 | 0.041 | 0.031 | 0.011 | 0.674 | 0.158 |
| top-k 64, protected slots 1 | 3 | 0.199 | 0.138 | 0.279 | 0.040 | 0.013 | 0.981 | 0.789 |
| top-k 64, protected slots 2 | 3 | 0.705 | 0.690 | 0.734 | 0.037 | 0.030 | 0.969 | 0.861 |
| top-k 64, protected slots 4 | 3 | 0.988 | 0.951 | 1.027 | 0.035 | 0.054 | 0.945 | 0.865 |
| top-k 64, protected slots 8 | 3 | 1.064 | 1.021 | 1.100 | 0.035 | 0.073 | 0.927 | 0.871 |
| top-k 64, protected slots 16 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.073 | 0.926 | 0.874 |
| top-k 64, protected slots 32 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.073 | 0.926 | 0.874 |

Figure: `outputs/appendix_followups/e_reserve_threshold_robustness_summary.png`

## f_cultural_overconstraint

| label | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean | late_visibility_action_gap_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reserve fraction 0.0000 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Reserve fraction 0.0625 | 3 | 0.224 | 0.182 | 0.257 | 0.035 | 0.058 | 0.942 | 0.669 |
| Reserve fraction 0.1250 | 3 | 0.681 | 0.677 | 0.687 | 0.032 | 0.122 | 0.878 | 0.842 |
| Reserve fraction 0.2500 | 3 | 0.996 | 0.974 | 1.023 | 0.034 | 0.222 | 0.778 | 0.853 |
| Reserve fraction 0.5000 | 3 | 1.040 | 1.015 | 1.085 | 0.035 | 0.275 | 0.725 | 0.874 |
| Reserve fraction 0.7500 | 3 | 1.050 | 1.031 | 1.078 | 0.034 | 0.309 | 0.691 | 0.867 |
| Reserve fraction 0.9000 | 3 | 1.048 | 0.998 | 1.118 | 0.034 | 0.295 | 0.705 | 0.874 |
| Reserve fraction 1.0000 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.294 | 0.706 | 0.874 |

Figure: `outputs/appendix_followups/f_cultural_overconstraint_summary.png`

## g_institutional_learning

| label | seed_count | final_ratio_mean | final_ratio_min | final_ratio_max | late_births_per_eligible_mean | late_selected_actionable_mean | late_phantom_share_mean | late_visibility_action_gap_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No learning | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Slow regional learning | 3 | 0.667 | 0.512 | 0.790 | 0.042 | 0.189 | 0.811 | 0.865 |
| Fast regional learning | 3 | 0.945 | 0.864 | 1.016 | 0.039 | 0.244 | 0.756 | 0.865 |
| Preadapted reserve 0.25 | 3 | 0.996 | 0.974 | 1.023 | 0.034 | 0.222 | 0.778 | 0.853 |

Figure: `outputs/appendix_followups/g_institutional_learning_summary.png`

## Short Interpretation

These follow-ups should be read as robustness checks rather than final
estimates. The key question is whether the qualitative pattern survives
changes in selection mode, candidate-pool multiplier, action radius,
top-k capacity, reserve strength, and region-level learning.

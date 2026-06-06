# Reproducibility Archive

This appendix records the archived simulation conditions used by the working
paper bundle. It is intended to make the paper readable as an artifact: each
major figure or table should point to a data file, a script when available,
the seed policy, and the main parameter family.

This is still a working-paper archive, not a publication-grade reproduction
capsule. Some early exploratory outputs were generated during interactive
analysis before all scenario scripts were promoted into versioned files. Those
cases are explicitly marked as archived exploratory outputs.

## Environment

- Repository: `visibility-radius-sim`
- Base commit before the latest gendered follow-up work: `4339897`
- Package manager: `uv`
- Python: `>=3.11`
- Core dependencies: `numpy`, `pandas`, `matplotlib`
- Test dependency: `pytest`
- Lockfile: `uv.lock`

Representative verification command:

```bash
uv run pytest
```

At the time this archive was added, the test suite passed with `22 passed`.

## Core Model Files

- `src/visibility_radius_sim/agent.py`
- `src/visibility_radius_sim/config.py`
- `src/visibility_radius_sim/simulation.py`
- `src/visibility_radius_sim/metrics.py`
- `src/visibility_radius_sim/plotting.py`
- `src/visibility_radius_sim/cli.py`

## Baseline Scenario Parameters

The stylized SNS-era baseline is defined by:

```python
SimulationConfig.for_scenario("sns-2000s")
```

The archived parameter snapshot is:

- `outputs/sns_2000s/sns_2000s.params.json`

Key baseline values:

| Parameter | Value |
|---|---:|
| `start_calendar_year` | `1980` |
| `years` | `80` |
| `initial_population` | `2500` |
| `seed` | `42` |
| `initial_age_distribution` | `japan-1980-stylized` |
| `location_model` | `clustered` |
| `location_cluster_count` | `12` |
| `initial_radius` | `0.02` |
| `max_radius` | `sqrt(2)` |
| `action_radius` | `0.12` |
| `radius_schedule` | `shock` |
| `visibility_expansion_mid_year` | `2007` |
| `visibility_expansion_duration_years` | `7.0` |
| `selection_mode` | `top-k` |
| `top_k` | `16` |
| `initial_candidate_pool_multiplier` | `1.0` |
| `max_candidate_pool_multiplier` | `300.0` |
| `phantom_candidate_mode` | `sampled` |
| `phantom_candidate_sample_cap` | `512` |
| `initial_pair_fraction` | `0.55` |
| `pair_duration_mean` | `18.0` |
| `birth_probability` | `0.12` |
| `carrying_capacity` | `9000` |

The baseline figure is archived as:

- `paper/figures/sns_2000s_simple.png`
- `outputs/sns_2000s/sns_2000s.csv`
- `outputs/sns_2000s/sns_2000s_simple.png`

## Main Paper Experiments

### Phantom Candidates and Actionable Reserve

Paper figure:

- `paper/figures/actionable_attention_comparison.png`

Paper data:

- `paper/data/actionable_attention_comparison_summary.csv`
- `outputs/actionable_attention/actionable_attention_comparison_summary.csv`

Seed policy:

- Archived summary table only; individual seed rows are not included in
  `paper/data`.
- The visible output names indicate the comparison was produced from an
  exploratory scenario family rather than the current scripted appendix runner.

Conditions:

- current sampled phantom behavior
- old behavior without phantom candidates
- actionable reserve at `0.50`
- actionable reserve at `0.75`

Archive status:

- Archived exploratory output.
- Publication-grade rerun should promote this scenario family into a dedicated
  versioned script or CLI subcommand.

### Protected Actionable-Slot Threshold

Paper figure:

- `paper/figures/reserve_threshold_slots_multiseed.png`

Paper data:

- `paper/data/reserve_threshold_slots_multiseed_summary.csv`
- `outputs/reserve_threshold/reserve_threshold_slots_multiseed_summary.csv`
- `outputs/reserve_threshold/reserve_threshold_slots_multiseed_raw.csv`

Seed policy:

- Multi-seed sweep.
- The summary contains min/mean/max over seeds.

Conditions:

- baseline SNS-like shock with sampled phantom candidates
- `top_k=16`
- protected actionable slots: `0,1,2,3,4,5,6,8`
- reserve fraction equals `protected_slots / top_k`

Archive status:

- Archived exploratory output with raw output retained.
- The exact generating script is not currently preserved as a standalone file.

### Long-Run Cultural Adaptation

Paper figure:

- `paper/figures/civilizational_adaptation_longrun.png`

Paper data:

- `paper/data/civilizational_adaptation_longrun_summary.csv`
- `outputs/civilizational_adaptation/`

Seed policy:

- Archived summary appears to be a fixed-seed long-run comparison.

Conditions:

- no virtual filter
- weak actionable culture
- balanced actionable culture
- strong actionable culture
- local-only reference

Core interpretation:

- Region-held reserve culture can preserve actionable attention when the
  virtual candidate pool expands.

Archive status:

- Archived exploratory output.

### Region Boundary and Cross-Region Pairing

Paper figures:

- `paper/figures/regional_culture_crossing_comparison.png`
- `paper/figures/regional_culture_trajectories_by_culture.png`

Paper data:

- `paper/data/regional_culture_crossing_summary.csv`
- `outputs/regional_culture/`

Seed policy:

- Archived fixed-seed or small-run comparison; raw trajectory CSVs are retained.

Conditions:

- cross-region pairing allowed
- cross-region pairing blocked
- region-held reserve cultures compared by final culture share and trajectory

Archive status:

- Archived exploratory output.

### Behavioral Action Interventions

Paper figure:

- `paper/figures/behavioral_action_interventions.png`

Paper data:

- `paper/data/behavioral_action_interventions_summary.csv`
- `paper/data/behavioral_action_interventions_seed42_summary.csv`
- `outputs/behavioral_interventions/`

Seed policy:

- Multi-seed summary plus seed `42` summary are both archived.

Conditions:

- raw SNS / no discipline
- contact before scroll
- 48h move to reality
- full behavior bundle
- distance filter first
- weekly fixed local venue
- do not replay phantom candidates

Archive status:

- Archived exploratory output with summary and raw CSVs retained.

## Appendix Follow-Ups A-G

Script:

- `scripts/run_appendix_followups.py`

Paper appendix:

- `paper/appendix_followups/appendix_followups_report.md`
- `paper/appendix_followups/appendix_followups_report_ja.md`
- `paper/appendix_followups/data/appendix_followups_summary.csv`
- `paper/appendix_followups/data/appendix_followups_run_summary.csv`
- `paper/appendix_followups/figures/`

Output archive:

- `outputs/appendix_followups/appendix_followups_raw.csv`
- `outputs/appendix_followups/appendix_followups_run_summary.csv`
- `outputs/appendix_followups/appendix_followups_summary.csv`
- `outputs/appendix_followups/*.png`

Seed policy:

- `SEEDS = (0, 1, 2)`

Shared base configuration:

- `SimulationConfig.for_scenario("sns-2000s")`
- `years = 180`
- `initial_population = 1200`
- `carrying_capacity = 4500`
- `worker_count = None`
- `max_auto_workers = 8`
- `parallel_threshold = 200`
- `metrics_precision = 6`

Experiments:

| Experiment | Main Question |
|---|---|
| `a_radius_alone` | Is radius expansion alone enough, or is the actionability gap required? |
| `b_selection_mode` | Does top-k versus percentile selection change the failure mode? |
| `c_candidate_multiplier` | Does perceived candidate-pool multiplier drive collapse? |
| `d_actionability_gap` | Does widening action radius rescue viability? |
| `e_reserve_threshold_robustness` | Do protected actionable-slot thresholds persist across `top_k`? |
| `f_cultural_overconstraint` | Does very high reserve become costly in the current model? |
| `g_institutional_learning` | Can region-level learning recover after observed decline? |

Representative rerun command:

```bash
.venv/bin/python scripts/run_appendix_followups.py
```

## Gendered Aspirational Selectivity Follow-Up

Script:

- `scripts/run_gendered_aspiration.py`

Paper notes:

- `paper/notes/gendered_aspiration_report.md`
- `paper/notes/gendered_aspiration_report_ja.md`

Output archive:

- `outputs/gendered_aspiration/gendered_aspiration_raw.csv`
- `outputs/gendered_aspiration/gendered_aspiration_run_summary.csv`
- `outputs/gendered_aspiration/gendered_aspiration_summary.csv`
- `outputs/gendered_aspiration/gendered_aspiration_summary.png`

Seed policy:

- `SEEDS = (0, 1, 2)`

Shared base configuration:

- `SimulationConfig.for_scenario("sns-2000s")`
- `years = 180`
- `initial_population = 1200`
- `carrying_capacity = 4500`
- `gender_mode = "binary-balanced"`
- `selection_mode = "top-k"`
- `top_k = 16`
- `actionable_selection_reserve_fraction = 0.25`
- Baseline reproductive window: `18-45`
- `aspirational_min_score_quantile` varies by condition
- `aspirational_min_score_quantile_distribution` is used in the mixed individual-threshold conditions

Conditions:

| Variant | Meaning |
|---|---|
| `symmetric_reserve_025` | A/B symmetric choice, no relative aspiration threshold, reserve `0.25` |
| `b_income_500_floor` | B side uses an income-floor proxy interpreted as 500+ with no upper cap, approximated as `quantile=0.55` |
| `b_income_700_floor` | B side uses a stricter single-condition reference, approximated as `quantile=0.80` |
| `b_mixed_income_plus_light` | B side has individual thresholds: weights `55/25/15/5` at quantiles `0.55/0.75/0.87/0.90` |
| `b_mixed_income_plus_heavy` | B side has more compound-condition weight: `25/25/35/15` at quantiles `0.55/0.75/0.87/0.90` |
| `b_mixed_income_plus_heavy_reserve_050` | Same compound-heavy threshold distribution, reserve `0.50` |
| `b_mixed_income_plus_heavy_no_reserve` | Same compound-heavy threshold distribution, reserve `0.00` |
| `symmetric_reserve_025_repro_20_39` | Symmetric reference with reproduction restricted to ages `20-39` |
| `b_income_500_floor_repro_20_39` | 500+ income-floor proxy with reproduction restricted to ages `20-39` |
| `b_mixed_income_plus_light_repro_20_39` | Light mixed aspiration profile with reproduction restricted to ages `20-39` |
| `b_mixed_income_plus_heavy_repro_20_39` | Compound-heavy aspiration profile with reproduction restricted to ages `20-39` |

Interpretation constraint:

- The A/B labels are abstract. They are not a claim about sex-specific
  reproductive biology.
- The loaded phrase "high standards" is implemented as a relative score
  threshold inside the perceived comparison pool, not as a smaller top-k
  attention budget.
- The income thresholds are heuristic model proxies. They are not calibrated
  income equations; the point is to compare single lower-bound requirements
  with heterogeneous compound requirements.
- The `20-39` reproductive-window rows are sensitivity checks. Because the
  birth probability is not age-specific inside the window, they should be read
  as a time-limit stress test, not a demographic fertility calibration.

Representative rerun command:

```bash
.venv/bin/python scripts/run_gendered_aspiration.py
```

## Gendered Aspiration Calibration Robustness Sweep

Script:

- `scripts/run_gendered_robustness.py`

Paper notes:

- `paper/notes/gendered_robustness_report.md`
- `paper/notes/gendered_robustness_report_ja.md`

Output archive:

- `outputs/gendered_robustness/gendered_robustness_raw.csv`
- `outputs/gendered_robustness/gendered_robustness_run_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_heatmap.png`

Seed policy:

- `SEEDS = (0, 1, 2)`

Shared base configuration:

- `SimulationConfig.for_scenario("sns-2000s")`
- `years = 180`
- `initial_population = 1200`
- `carrying_capacity = 4500`
- `gender_mode = "binary-balanced"`
- `selection_mode = "top-k"`
- `top_k = 16`
- `actionable_selection_reserve_fraction = 0.25`

Calibration axes varied one-at-a-time:

- `birth_probability = 0.09, 0.18`
- `initial_pair_fraction = 0.35, 0.70`
- `pair_duration_mean = 10.0, 26.0`
- `max_candidate_pool_multiplier = 100.0, 500.0`
- `top_k = 32`
- `actionable_selection_reserve_fraction = 0.50`
- reproductive window `20-44` and `20-39`

Aspiration profiles:

- `symmetric`
- `income_500_floor`
- `mixed_light`
- `mixed_heavy`

Interpretation constraint:

- This is a robustness sweep, not a demographic calibration. It tests whether
  the sign and scale of the aspiration penalty survive plausible parameter
  perturbations in the toy model.

Representative rerun command:

```bash
.venv/bin/python scripts/run_gendered_robustness.py
```

## Reality-grounded Japan-like Calibration

Script:

- `scripts/run_reality_grounded_calibration.py`

Named scenario added:

- `SimulationConfig.for_scenario("japan-2070")`
- CLI: `uv run python -m visibility_radius_sim.cli run --scenario japan-2070 --output outputs/japan_2070.csv`

Paper note:

- `paper/notes/reality_grounded_calibration_report_ja.md`

Output archive:

- `outputs/reality_grounded_calibration/base_candidate_summary.csv`
- `outputs/reality_grounded_calibration/profile_raw.csv`
- `outputs/reality_grounded_calibration/profile_summary.csv`
- `outputs/reality_grounded_calibration/profile_comparison.png`
- `outputs/reality_grounded_calibration/reality_overlay.png`

Seed policy:

- `SEEDS = (0, 1, 2)`

Calibration target:

- 91 simulated years, 1980-2070 inclusive.
- Symmetric condition target band: final population ratio `0.65-0.85`, center `0.74`.
- This target is a toy-model index target motivated by Japanese fertility decline and
  the IPSS 2023 national population projection, not a full demographic calibration.
- `reality_overlay.png` normalizes the 1980-2020 census anchors and the 2070 IPSS
  projection anchor into a population index, linearly interpolates the reference
  line, and overlays selected simulation trajectories.
- Candidate selection now evaluates not only the 2070 endpoint but also
  population-index RMSE at 1980/1990/2000/2010/2020/2070.
- The `japan-tfr-stylized` birth probability schedule multiplies
  `birth_probability` by higher 1980-era and lower post-2000-era factors.

Selected named-scenario parameters:

- `years = 91`
- `start_calendar_year = 1980`
- `initial_population = 1200`
- `reproductive_min_age = 20`
- `reproductive_max_age = 44`
- `fertility_age_profile = "japan-stylized"`
- `birth_probability = 0.22`
- `birth_probability_schedule = "japan-tfr-stylized"`
- `pair_duration_mean = 18.0`
- `initial_pair_fraction = 0.55`
- `carrying_capacity = 6000`
- `lifespan_mean = 78.0`
- `selection_mode = "top-k"`
- `top_k = 16`
- `actionable_selection_reserve_fraction = 0.25`

Representative rerun command:

```bash
.venv/bin/python scripts/run_reality_grounded_calibration.py
```

## Reproducibility Gaps

The following gaps remain before this can be treated as a publication-grade
reproduction package:

1. Promote all archived exploratory scenario families into scripts or CLI
   subcommands.
2. Store per-run parameter JSON files for every paper figure, not only the
   baseline demo/SNS runs.
3. Store raw per-seed outputs beside every summary table.
4. Record the exact git commit after each paper-generation run.
5. Add a single `make paper` or `uv run ...` command that regenerates all paper
   figures and tables from scratch.
6. Add environment metadata to paper outputs, such as Python version and package
   versions.

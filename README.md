# visibility-radius-sim

`visibility-radius-sim` is a small Python agent-based simulation for exploring how a rapidly expanding observable candidate pool can change selection dynamics, unmatched rates, reproductive concentration, fertility proxies, and trait diversity.

The core research question is:

> Can a local "top candidate selection" heuristic remain adaptive when the observable candidate pool rapidly expands from local to near-global?

The motivating scenario is the 2000s: search, SNS, recommendation systems, and online platforms rapidly increased the number of visible candidates and comparison targets. This project asks whether a selection heuristic that may be adaptive in a local environment can become maladaptive when the visibility radius expands much faster than the heuristic changes.

This is an abstract model. It is not a model of real human behavior, a demographic forecast, a causal claim about fertility decline, or a claim about any particular society, platform, or group. The goal is to make a simple simulation surface where assumptions are explicit and easy to change.

## What It Simulates

Each agent has:

- an age, lifespan, location, and alive/dead state
- a numeric trait vector: attractiveness, resources, intelligence, kindness, and stability
- preference weights over those traits
- a selection rule that keeps either a top percentile or a fixed top-k set of candidates

Each simulated year:

1. Living agents age and agents past lifespan are removed.
2. The visibility radius is updated.
3. Existing pairs remain active until death or pair-duration expiry.
4. Unpaired reproductive-age agents evaluate visible candidates.
5. Candidate scores are computed from preference weights and traits.
6. Agents keep either their top selection percentile or their fixed top-k candidates.
7. New pairs form only when selection is mutual and both agents are within action radius.
8. Active reproductive-age pairs may produce children.
9. Children inherit the average of parent traits plus mutation noise.
10. Yearly metrics are recorded.

## Radius Schedules

The CLI supports five visibility schedules:

- `fixed`: constant local radius
- `linear`: radius expands linearly from initial to maximum
- `sigmoid`: radius expands slowly at first, quickly near the middle, then levels off
- `shock`: radius expands rapidly around a specified calendar year
- `global`: radius is set to the maximum from the beginning

## Install

Install dependencies with `uv`:

```bash
uv sync
```

## Run A Simulation

For the 2000s SNS-style rapid visibility expansion scenario:

```bash
uv run python -m visibility_radius_sim.cli run \
  --scenario sns-2000s \
  --seed 42 \
  --output outputs/sns_2000s.csv
```

Then plot it:

```bash
uv run python -m visibility_radius_sim.cli plot \
  --input outputs/sns_2000s.csv \
  --output outputs/sns_2000s.png
```

For a simpler first-pass view:

```bash
uv run python -m visibility_radius_sim.cli plot-simple \
  --input outputs/sns_2000s.csv \
  --output outputs/sns_2000s_simple.png
```

The `sns-2000s` scenario starts in 1980 and uses a `shock` radius schedule centered around 2007. It is not calibrated to historical demographic data and should not be read as a Japan forecast. It is heuristically tuned so the pre-expansion period is viable: in the default seed, the model is roughly stable to mildly growing before the visibility shock, then the shock changes matching and fertility proxies.

In this scenario, `radius` and candidate volume are separated:

- `visibility_radius`: which in-simulation agents are spatially/socially visible
- `action_radius`: which visible agents are close enough for an actual pair to form
- `candidate_pool_multiplier`: perceived candidate-pool expansion from feeds, search, profiles, and recommendations
- `selection_mode=top-k`: a bounded attention model where agents keep only a fixed number of top candidates even when perceived candidate volume grows hundreds of times
- `phantom_candidate_mode=sampled`: extra perceived candidates can consume top-k selection slots while remaining unavailable for pair formation
- `actionable_selection_reserve_fraction`: optional selection-slot reserve for real candidates within action radius
- `initial_pair_fraction`: an initial stock of existing pairs, so the model does not start in 1980 as if every adult were unpaired

This means the model can represent a key SNS-era asymmetry: visibility can become near-global while practical action remains local or regional. Agents may spend their fixed top-k attention on highly visible but non-actionable candidates, leaving fewer local candidates available for mutual selection. In sampled phantom mode, the perceived candidate multiplier becomes causal: synthetic comparison candidates can enter the top-k competition, but they cannot form pairs.

The actionable reserve parameter is a simple intervention knob. For example, `--actionable-selection-reserve-fraction 0.5` means half of the selection slots are filled from real candidates inside action radius before global/phantom comparison candidates can consume the remaining slots.

```bash
uv run python -m visibility_radius_sim.cli run \
  --years 250 \
  --population 1000 \
  --radius-schedule sigmoid \
  --output outputs/run_sigmoid.csv
```

This writes:

- `outputs/run_sigmoid.csv`: yearly metrics
- `outputs/run_sigmoid.params.json`: the parameter values used for the run

For a quick demo:

```bash
uv run python -m visibility_radius_sim.cli run --years 250 --population 1000 --seed 42 --output outputs/demo.csv
```

Useful parameters to vary:

```bash
uv run python -m visibility_radius_sim.cli run \
  --years 250 \
  --start-year 1980 \
  --population 1000 \
  --radius-schedule shock \
  --expansion-mid-year 2007 \
  --expansion-duration-years 7 \
  --location-model clustered \
  --location-cluster-count 12 \
  --location-cluster-std 0.035 \
  --action-radius 0.18 \
  --selection-mode top-k \
  --top-k 8 \
  --initial-pair-fraction 0.55 \
  --pair-duration-mean 18 \
  --pair-duration-std 8 \
  --max-candidate-pool-multiplier 300 \
  --phantom-candidate-mode sampled \
  --phantom-candidate-sample-cap 512 \
  --actionable-selection-reserve-fraction 0.5 \
  --birth-probability 0.25 \
  --selectivity 0.15 \
  --mutation-std 0.05 \
  --initial-max-age 90 \
  --carrying-capacity 5000 \
  --workers 1 \
  --seed 42 \
  --output outputs/linear_selective.csv
```

Candidate selection can run in parallel:

```bash
uv run python -m visibility_radius_sim.cli run \
  --years 250 \
  --population 1000 \
  --radius-schedule sigmoid \
  --workers 0 \
  --output outputs/auto_workers.csv
```

Omit `--workers` for automatic worker selection. Auto mode uses available CPU information, leaves one logical CPU free when possible, caps worker count with `--max-auto-workers`, and stays single-threaded below `--parallel-threshold` eligible agents. Use `--workers 1` for a deterministic single-thread baseline. The simulation records the resolved worker count in `selection_worker_count`.

## Visualize Population And Analysis

Simple view:

```bash
uv run python -m visibility_radius_sim.cli plot-simple \
  --input outputs/demo.csv \
  --output outputs/demo_simple.png
```

The simple plot focuses on:

- population index
- births per eligible agent and unmatched rate, shown as 5-year averages
- visible share: the average share of eligible candidates visible to an eligible agent
- actionable share: the average share of eligible candidates both visible and within action radius
- selected-actionable share: the share of selected top candidates that are actually actionable
- accepted share: the selected top-k quota divided by perceived candidate count
- a short text summary

Detailed view:

```bash
uv run python -m visibility_radius_sim.cli plot \
  --input outputs/demo.csv \
  --output outputs/demo.png
```

The detailed plot command creates a larger analysis dashboard with:

- population trajectory over time
- visibility radius overlaid on population
- births, deaths, and net yearly population flow
- matched pairs and unmatched rate
- observed candidate-pool coverage and mean visible candidates
- perceived candidate count after candidate-pool multiplier
- actionable candidate count within action radius
- visibility-action gap and selected-actionable share
- accepted share of the perceived candidate pool
- fertility proxies such as births per eligible agent
- trait mean and diversity
- reproductive concentration and effective parent count
- normalized response curves using radius coverage as the x-axis
- density-adjusted effective birth probability when carrying capacity is enabled
- run parameters from the `.params.json` sidecar file
- final-year and full-run summary statistics

## Metrics

The simulation writes one CSV row per year with:

- `year`
- `calendar_year`
- `population_size`
- `birth_count`
- `births_per_population`
- `births_per_eligible`
- `births_per_matched_pair`
- `death_count`
- `matched_pair_count`
- `new_pair_count`
- `active_pair_count`
- `unmatched_rate`
- `mean_visible_candidate_count`
- `median_visible_candidate_count`
- `mean_perceived_candidate_count`
- `median_perceived_candidate_count`
- `mean_actionable_candidate_count`
- `action_coverage_rate`
- `visibility_action_gap`
- `mean_selected_actionable_share`
- `mean_selection_quota`
- `mean_selection_acceptance_share`
- `mean_phantom_candidate_count`
- `mean_sampled_phantom_candidate_count`
- `mean_selected_phantom_count`
- `mean_phantom_selection_share`
- `candidate_pool_multiplier`
- `action_radius`
- `blocked_mutual_pair_count`
- `visibility_coverage_rate`
- `theoretical_area_coverage`
- `effective_birth_probability`
- `selection_worker_count`
- `trait_mean`
- `trait_variance`
- `trait_diversity`
- `reproductive_concentration`
- `effective_parent_count`
- `visibility_radius`

`reproductive_concentration` is implemented as a simple Gini coefficient over yearly offspring counts among living agents. Higher values mean births are more concentrated among fewer parents in that year.

`matched_pair_count` is the number of active reproductive-age pairs in that year. `new_pair_count` is the number of new pairs formed that year. `active_pair_count` is all ongoing pairs, including pairs outside reproductive age.

`effective_parent_count` is the inverse Simpson concentration of agents who had offspring in that year. Higher values mean reproduction was distributed across more parents.

`visibility_coverage_rate` is the observed share of eligible candidates visible to the average eligible agent in that year. This is usually more useful than radius alone because the same radius can cover very different candidate shares depending on population density and age structure.

`mean_perceived_candidate_count` multiplies the in-simulation visible candidates by `candidate_pool_multiplier`. This is meant to represent SNS-style comparison pressure where the number of visible profiles, feeds, or recommendation targets can grow far faster than the local agent population.

`mean_selection_acceptance_share` is the selected quota divided by perceived candidate count. In `top-k` mode this share can collapse as perceived candidate volume grows, even if the absolute number of candidates an agent can seriously consider stays fixed.

`mean_phantom_candidate_count` is the average number of non-pairable comparison candidates implied by the candidate multiplier. `mean_sampled_phantom_candidate_count` is how many of those were sampled into the top-k competition for performance. `mean_phantom_selection_share` is the share of top-k slots taken by phantom candidates. Higher values mean more attention is spent on candidates who cannot become pairs in the simulation.

`visibility_action_gap` is the share of eligible agents who are visible but outside action radius. `mean_selected_actionable_share` is the share of selected top candidates who are actually close enough for pair formation. These are useful when studying SNS-like settings where visibility expands much faster than practical action range.

`effective_birth_probability` is the birth probability after optional carrying-capacity suppression. This keeps long runs readable by preventing population growth from overwhelming the radius experiment. Set `--carrying-capacity 0` to disable it.

## Tests

```bash
uv run pytest
```

Tests are included as a sanity check for the simulation mechanics, but the main workflow is running scenarios and inspecting the generated CSV and dashboard PNG.

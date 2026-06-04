import numpy as np

from visibility_radius_sim.agent import Agent, create_child
from visibility_radius_sim.config import (
    SimulationConfig,
    candidate_pool_multiplier_for_year,
    resolve_worker_count,
    visibility_radius_for_year,
)
from visibility_radius_sim.simulation import Simulation


def test_agents_age_and_die() -> None:
    agent = Agent(
        id=1,
        age=2,
        lifespan=3,
        location=np.array([0.0, 0.0]),
        traits=np.ones(5),
        preference_weights=np.ones(5),
        selectivity=0.2,
    )

    assert agent.age_one_year() is False
    assert agent.age == 3

    assert agent.age_one_year() is True
    assert agent.age == 4
    assert agent.alive is False


def test_child_trait_inheritance_without_mutation() -> None:
    rng = np.random.default_rng(7)
    parent_a = Agent(
        id=1,
        age=25,
        lifespan=80,
        location=np.array([0.2, 0.2]),
        traits=np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
        preference_weights=np.ones(5),
        selectivity=0.2,
    )
    parent_b = Agent(
        id=2,
        age=25,
        lifespan=80,
        location=np.array([0.6, 0.6]),
        traits=np.array([5.0, 4.0, 3.0, 2.0, 1.0]),
        preference_weights=np.ones(5),
        selectivity=0.2,
    )

    child = create_child(
        child_id=3,
        parent_a=parent_a,
        parent_b=parent_b,
        rng=rng,
        mutation_std=0.0,
        lifespan_mean=80,
        lifespan_std=0.0,
        location_noise_std=0.0,
    )

    assert np.allclose(child.traits, np.array([3.0, 3.0, 3.0, 3.0, 3.0]))
    assert np.allclose(child.location, np.array([0.4, 0.4]))
    assert child.age == 0
    assert child.alive is True


def test_radius_schedule_behavior() -> None:
    fixed = SimulationConfig(radius_schedule="fixed", initial_radius=0.2, max_radius=1.0)
    linear = SimulationConfig(radius_schedule="linear", initial_radius=0.2, max_radius=1.0, years=10)
    sigmoid = SimulationConfig(radius_schedule="sigmoid", initial_radius=0.2, max_radius=1.0, years=10)
    shock = SimulationConfig(
        radius_schedule="shock",
        initial_radius=0.2,
        max_radius=1.0,
        start_calendar_year=1980,
        visibility_expansion_mid_year=2005,
        visibility_expansion_duration_years=6,
    )
    global_config = SimulationConfig(radius_schedule="global", initial_radius=0.2, max_radius=1.0)

    assert visibility_radius_for_year(fixed, 5) == 0.2
    assert visibility_radius_for_year(global_config, 0) == 1.0
    assert visibility_radius_for_year(linear, 0) == 0.2
    assert visibility_radius_for_year(linear, 10) == 1.0
    assert 0.2 <= visibility_radius_for_year(sigmoid, 0) < visibility_radius_for_year(sigmoid, 5)
    assert visibility_radius_for_year(sigmoid, 5) < visibility_radius_for_year(sigmoid, 10) <= 1.0
    assert visibility_radius_for_year(shock, 5) < visibility_radius_for_year(shock, 25)
    assert visibility_radius_for_year(shock, 25) < visibility_radius_for_year(shock, 45)


def test_simulation_produces_metrics_for_each_year() -> None:
    config = SimulationConfig(
        years=8,
        initial_population=80,
        seed=42,
        radius_schedule="linear",
        initial_radius=0.15,
        max_radius=1.0,
    )

    metrics = Simulation(config).run()

    assert len(metrics) == 8
    assert list(metrics["year"]) == list(range(1, 9))
    assert set(
        [
            "population_size",
            "calendar_year",
            "birth_count",
            "births_per_population",
            "births_per_eligible",
            "births_per_matched_pair",
            "death_count",
            "matched_pair_count",
            "new_pair_count",
            "active_pair_count",
            "unmatched_rate",
            "mean_visible_candidate_count",
            "median_visible_candidate_count",
            "mean_perceived_candidate_count",
            "median_perceived_candidate_count",
            "mean_actionable_candidate_count",
            "action_coverage_rate",
            "visibility_action_gap",
            "mean_selected_actionable_share",
            "mean_selection_quota",
            "mean_selection_acceptance_share",
            "mean_phantom_candidate_count",
            "mean_sampled_phantom_candidate_count",
            "mean_selected_phantom_count",
            "mean_phantom_selection_share",
            "candidate_pool_multiplier",
            "action_radius",
            "blocked_mutual_pair_count",
            "visibility_coverage_rate",
            "theoretical_area_coverage",
            "effective_birth_probability",
            "trait_diversity",
            "reproductive_concentration",
            "effective_parent_count",
            "visibility_radius",
        ]
    ).issubset(metrics.columns)


def test_default_population_does_not_crash_immediately() -> None:
    config = SimulationConfig(years=20, initial_population=120, seed=123)

    metrics = Simulation(config).run()

    assert len(metrics) == 20
    assert metrics["population_size"].iloc[-1] > 0
    assert metrics["population_size"].min() > 0


def test_visibility_coverage_increases_with_radius() -> None:
    local_config = SimulationConfig(
        years=1,
        initial_population=120,
        seed=123,
        radius_schedule="fixed",
        initial_radius=0.05,
    )
    global_config = SimulationConfig(
        years=1,
        initial_population=120,
        seed=123,
        radius_schedule="global",
    )

    local_metrics = Simulation(local_config).run()
    global_metrics = Simulation(global_config).run()

    assert local_metrics["visibility_coverage_rate"].iloc[0] < global_metrics["visibility_coverage_rate"].iloc[0]
    assert local_metrics["mean_visible_candidate_count"].iloc[0] < global_metrics["mean_visible_candidate_count"].iloc[0]


def test_effective_birth_probability_respects_carrying_capacity() -> None:
    config = SimulationConfig(
        years=1,
        initial_population=120,
        seed=123,
        carrying_capacity=120,
        birth_probability=0.5,
        initial_min_age=0,
        initial_max_age=0,
    )

    metrics = Simulation(config).run()

    assert metrics["effective_birth_probability"].iloc[0] == 0.0


def test_auto_worker_count_uses_more_workers_for_large_runs() -> None:
    config = SimulationConfig(worker_count=None, parallel_threshold=10, max_auto_workers=4)

    worker_count = resolve_worker_count(config, workload_size=100)

    assert 1 <= worker_count <= 4


def test_parallel_candidate_selection_matches_single_worker_results() -> None:
    base_config = dict(
        years=5,
        initial_population=180,
        seed=99,
        radius_schedule="linear",
        initial_radius=0.1,
        max_radius=1.0,
        parallel_threshold=1,
    )

    single_worker_metrics = Simulation(SimulationConfig(**base_config, worker_count=1)).run()
    parallel_metrics = Simulation(SimulationConfig(**base_config, worker_count=2)).run()

    comparable_columns = [column for column in single_worker_metrics.columns if column != "selection_worker_count"]
    assert single_worker_metrics[comparable_columns].equals(parallel_metrics[comparable_columns])
    assert set(single_worker_metrics["selection_worker_count"]) == {1}
    assert set(parallel_metrics["selection_worker_count"]) == {2}


def test_sns_2000s_scenario_has_rapid_radius_expansion() -> None:
    config = SimulationConfig.for_scenario("sns-2000s")

    assert config.start_calendar_year == 1980
    assert config.radius_schedule == "shock"
    assert config.selection_mode == "top-k"
    assert visibility_radius_for_year(config, 20) < visibility_radius_for_year(config, 30)
    assert visibility_radius_for_year(config, 35) > 0.8 * config.max_radius
    assert candidate_pool_multiplier_for_year(config, 20) < candidate_pool_multiplier_for_year(config, 35)


def test_sns_2000s_presns_baseline_is_viable() -> None:
    config = SimulationConfig.for_scenario("sns-2000s").with_overrides(years=25, seed=42, worker_count=1)

    metrics = Simulation(config).run()

    initial_population = metrics["population_size"].iloc[0]
    assert metrics["population_size"].min() >= initial_population
    assert metrics["population_size"].iloc[-1] > initial_population
    assert metrics.loc[metrics["calendar_year"] == 1990, "population_size"].iloc[0] >= initial_population


def test_top_k_selection_caps_selection_quota() -> None:
    config = SimulationConfig(
        years=1,
        initial_population=200,
        seed=123,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=5,
        initial_candidate_pool_multiplier=10.0,
        max_candidate_pool_multiplier=10.0,
    )

    metrics = Simulation(config).run()

    assert metrics["mean_selection_quota"].iloc[0] <= 5
    assert metrics["mean_perceived_candidate_count"].iloc[0] > metrics["mean_visible_candidate_count"].iloc[0]
    assert metrics["mean_selection_acceptance_share"].iloc[0] < 0.1


def test_sampled_phantom_candidates_consume_selection_slots() -> None:
    base_config = dict(
        years=1,
        initial_population=220,
        seed=123,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=8,
        action_radius=0.08,
        initial_candidate_pool_multiplier=50.0,
        max_candidate_pool_multiplier=50.0,
        worker_count=1,
    )

    without_phantom = Simulation(SimulationConfig(**base_config, phantom_candidate_mode="none")).run()
    with_phantom = Simulation(
        SimulationConfig(
            **base_config,
            phantom_candidate_mode="sampled",
            phantom_candidate_sample_cap=256,
        )
    ).run()

    assert with_phantom["mean_phantom_candidate_count"].iloc[0] > 0
    assert with_phantom["mean_selected_phantom_count"].iloc[0] > 0
    assert with_phantom["mean_phantom_selection_share"].iloc[0] > 0
    assert with_phantom["mean_selected_actionable_share"].iloc[0] < without_phantom[
        "mean_selected_actionable_share"
    ].iloc[0]


def test_sampled_phantom_selection_is_parallel_deterministic() -> None:
    base_config = dict(
        years=3,
        initial_population=180,
        seed=404,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=8,
        initial_candidate_pool_multiplier=25.0,
        max_candidate_pool_multiplier=25.0,
        phantom_candidate_mode="sampled",
        phantom_candidate_sample_cap=128,
        parallel_threshold=1,
    )

    single_worker_metrics = Simulation(SimulationConfig(**base_config, worker_count=1)).run()
    parallel_metrics = Simulation(SimulationConfig(**base_config, worker_count=2)).run()

    comparable_columns = [column for column in single_worker_metrics.columns if column != "selection_worker_count"]
    assert single_worker_metrics[comparable_columns].equals(parallel_metrics[comparable_columns])


def test_actionable_reserve_protects_real_selection_slots() -> None:
    base_config = dict(
        years=1,
        initial_population=220,
        seed=909,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=12,
        action_radius=0.08,
        initial_candidate_pool_multiplier=80.0,
        max_candidate_pool_multiplier=80.0,
        phantom_candidate_mode="sampled",
        phantom_candidate_sample_cap=256,
        worker_count=1,
    )

    no_reserve = Simulation(
        SimulationConfig(**base_config, actionable_selection_reserve_fraction=0.0)
    ).run()
    with_reserve = Simulation(
        SimulationConfig(**base_config, actionable_selection_reserve_fraction=0.5)
    ).run()

    assert with_reserve["mean_selected_actionable_share"].iloc[0] > no_reserve[
        "mean_selected_actionable_share"
    ].iloc[0]
    assert with_reserve["mean_phantom_selection_share"].iloc[0] < no_reserve[
        "mean_phantom_selection_share"
    ].iloc[0]


def test_action_radius_can_block_visible_mutual_choices() -> None:
    config = SimulationConfig(
        years=1,
        initial_population=180,
        seed=321,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=8,
        action_radius=0.03,
        initial_candidate_pool_multiplier=1.0,
        max_candidate_pool_multiplier=1.0,
    )

    metrics = Simulation(config).run()

    assert metrics["visibility_action_gap"].iloc[0] > 0
    assert metrics["mean_selected_actionable_share"].iloc[0] < 1
    assert metrics["blocked_mutual_pair_count"].iloc[0] >= 0


def test_clustered_initial_locations_reduce_action_gap() -> None:
    base_config = dict(
        years=1,
        initial_population=240,
        seed=555,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=8,
        action_radius=0.08,
    )

    uniform_metrics = Simulation(SimulationConfig(**base_config, location_model="uniform")).run()
    clustered_metrics = Simulation(
        SimulationConfig(
            **base_config,
            location_model="clustered",
            location_cluster_count=6,
            location_cluster_std=0.015,
        )
    ).run()

    assert clustered_metrics["mean_actionable_candidate_count"].iloc[0] > uniform_metrics[
        "mean_actionable_candidate_count"
    ].iloc[0]


def test_cross_region_pairing_policy_changes_actionable_pool() -> None:
    base_config = dict(
        years=1,
        initial_population=260,
        seed=808,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=12,
        action_radius=1.0,
        location_model="clustered",
        location_cluster_count=8,
        location_cluster_std=0.02,
        initial_candidate_pool_multiplier=1.0,
        max_candidate_pool_multiplier=1.0,
        worker_count=1,
    )

    allowed = Simulation(SimulationConfig(**base_config, allow_cross_region_pairing=True)).run()
    blocked = Simulation(SimulationConfig(**base_config, allow_cross_region_pairing=False)).run()

    assert blocked["mean_visible_candidate_count"].iloc[0] == allowed["mean_visible_candidate_count"].iloc[0]
    assert blocked["mean_actionable_candidate_count"].iloc[0] < allowed["mean_actionable_candidate_count"].iloc[0]
    assert blocked["visibility_action_gap"].iloc[0] > allowed["visibility_action_gap"].iloc[0]


def test_region_culture_can_provide_actionable_reserve() -> None:
    base_config = dict(
        years=1,
        initial_population=240,
        seed=818,
        radius_schedule="global",
        selection_mode="top-k",
        top_k=12,
        action_radius=0.08,
        location_model="clustered",
        location_cluster_count=6,
        location_cluster_std=0.02,
        initial_candidate_pool_multiplier=80.0,
        max_candidate_pool_multiplier=80.0,
        phantom_candidate_mode="sampled",
        phantom_candidate_sample_cap=256,
        actionable_selection_reserve_fraction=0.0,
        worker_count=1,
    )

    no_region_culture = Simulation(SimulationConfig(**base_config)).run()
    with_region_culture = Simulation(
        SimulationConfig(
            **base_config,
            regional_actionable_reserve_fractions=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
        )
    ).run()

    assert with_region_culture["mean_selected_actionable_share"].iloc[0] > no_region_culture[
        "mean_selected_actionable_share"
    ].iloc[0]
    assert with_region_culture["mean_phantom_selection_share"].iloc[0] < no_region_culture[
        "mean_phantom_selection_share"
    ].iloc[0]


def test_initial_pair_stock_lowers_unmatched_rate() -> None:
    base_config = dict(
        years=1,
        initial_population=240,
        seed=777,
        radius_schedule="fixed",
        initial_radius=0.08,
        action_radius=0.08,
        location_model="clustered",
        location_cluster_count=4,
        location_cluster_std=0.02,
        birth_probability=0.0,
    )

    unpaired_metrics = Simulation(SimulationConfig(**base_config, initial_pair_fraction=0.0)).run()
    paired_metrics = Simulation(SimulationConfig(**base_config, initial_pair_fraction=0.5)).run()

    assert paired_metrics["active_pair_count"].iloc[0] > 0
    assert paired_metrics["unmatched_rate"].iloc[0] < unpaired_metrics["unmatched_rate"].iloc[0]

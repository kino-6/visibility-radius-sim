from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from visibility_radius_sim.agent import Agent


def gini(values: Sequence[int] | np.ndarray) -> float:
    """Return a simple Gini coefficient for non-negative offspring counts."""

    array = np.asarray(values, dtype=float)
    if array.size == 0 or np.all(array == 0.0):
        return 0.0
    if np.any(array < 0.0):
        raise ValueError("Gini values must be non-negative")

    sorted_values = np.sort(array)
    n = sorted_values.size
    index = np.arange(1, n + 1, dtype=float)
    return float((2.0 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1.0) / n)


def effective_parent_count(offspring_counts: dict[int, int]) -> float:
    counts = np.asarray([count for count in offspring_counts.values() if count > 0], dtype=float)
    if counts.size == 0:
        return 0.0
    shares = counts / counts.sum()
    return float(1.0 / np.sum(shares**2))


def trait_summary(agents: Sequence[Agent]) -> tuple[float, float, float]:
    living_traits = np.asarray([agent.traits for agent in agents if agent.alive], dtype=float)
    if living_traits.size == 0:
        return 0.0, 0.0, 0.0
    variance_by_trait = np.var(living_traits, axis=0)
    return (
        float(np.mean(living_traits)),
        float(np.mean(variance_by_trait)),
        float(np.sqrt(np.sum(variance_by_trait))),
    )


def yearly_metrics(
    *,
    year: int,
    calendar_year: int,
    agents: Sequence[Agent],
    birth_count: int,
    death_count: int,
    matched_pair_count: int,
    new_pair_count: int,
    active_pair_count: int,
    eligible_count: int,
    matched_agent_count: int,
    mean_visible_candidate_count: float,
    median_visible_candidate_count: float,
    mean_perceived_candidate_count: float,
    median_perceived_candidate_count: float,
    mean_actionable_candidate_count: float,
    action_coverage_rate: float,
    visibility_action_gap: float,
    mean_selected_actionable_share: float,
    mean_selection_quota: float,
    mean_selection_acceptance_share: float,
    candidate_pool_multiplier: float,
    visibility_coverage_rate: float,
    theoretical_area_coverage: float,
    effective_birth_probability: float,
    selection_worker_count: int,
    action_radius: float,
    blocked_mutual_pair_count: int,
    offspring_counts: dict[int, int],
    visibility_radius: float,
    precision: int,
) -> dict[str, float | int]:
    living_count = sum(1 for agent in agents if agent.alive)
    trait_mean, trait_variance, trait_diversity = trait_summary(agents)
    unmatched_rate = 0.0
    if eligible_count > 0:
        unmatched_rate = 1.0 - matched_agent_count / eligible_count
    births_per_population = 0.0 if living_count == 0 else birth_count / living_count
    births_per_eligible = 0.0 if eligible_count == 0 else birth_count / eligible_count
    births_per_matched_pair = 0.0 if matched_pair_count == 0 else birth_count / matched_pair_count

    all_parent_counts = [offspring_counts.get(agent.id, 0) for agent in agents if agent.alive]
    reproductive_concentration = gini(all_parent_counts)

    return {
        "year": year,
        "calendar_year": calendar_year,
        "population_size": living_count,
        "birth_count": birth_count,
        "births_per_population": round(float(births_per_population), precision),
        "births_per_eligible": round(float(births_per_eligible), precision),
        "births_per_matched_pair": round(float(births_per_matched_pair), precision),
        "death_count": death_count,
        "matched_pair_count": matched_pair_count,
        "new_pair_count": new_pair_count,
        "active_pair_count": active_pair_count,
        "unmatched_rate": round(float(unmatched_rate), precision),
        "mean_visible_candidate_count": round(float(mean_visible_candidate_count), precision),
        "median_visible_candidate_count": round(float(median_visible_candidate_count), precision),
        "mean_perceived_candidate_count": round(float(mean_perceived_candidate_count), precision),
        "median_perceived_candidate_count": round(float(median_perceived_candidate_count), precision),
        "mean_actionable_candidate_count": round(float(mean_actionable_candidate_count), precision),
        "action_coverage_rate": round(float(action_coverage_rate), precision),
        "visibility_action_gap": round(float(visibility_action_gap), precision),
        "mean_selected_actionable_share": round(float(mean_selected_actionable_share), precision),
        "mean_selection_quota": round(float(mean_selection_quota), precision),
        "mean_selection_acceptance_share": round(float(mean_selection_acceptance_share), precision),
        "candidate_pool_multiplier": round(float(candidate_pool_multiplier), precision),
        "visibility_coverage_rate": round(float(visibility_coverage_rate), precision),
        "theoretical_area_coverage": round(float(theoretical_area_coverage), precision),
        "effective_birth_probability": round(float(effective_birth_probability), precision),
        "selection_worker_count": selection_worker_count,
        "action_radius": round(float(action_radius), precision),
        "blocked_mutual_pair_count": blocked_mutual_pair_count,
        "trait_mean": round(trait_mean, precision),
        "trait_variance": round(trait_variance, precision),
        "trait_diversity": round(trait_diversity, precision),
        "reproductive_concentration": round(reproductive_concentration, precision),
        "effective_parent_count": round(effective_parent_count(offspring_counts), precision),
        "visibility_radius": round(float(visibility_radius), precision),
    }

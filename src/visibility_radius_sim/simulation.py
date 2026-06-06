from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd

from visibility_radius_sim.agent import Agent, create_child, create_random_agent
from visibility_radius_sim.config import (
    SimulationConfig,
    candidate_pool_multiplier_for_year,
    resolve_worker_count,
    visibility_radius_for_year,
)
from visibility_radius_sim.metrics import yearly_metrics


@dataclass(frozen=True)
class Pair:
    agent_a_id: int
    agent_b_id: int
    end_year: int


class Simulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.next_agent_id = 0
        self.location_cluster_centers = self._create_location_cluster_centers()
        self.agents = self._create_initial_population()
        self.active_pairs = self._create_initial_pairs()

    def run(self) -> pd.DataFrame:
        rows = [self.step(year) for year in range(1, self.config.years + 1)]
        return pd.DataFrame(rows)

    def step(self, year: int) -> dict[str, float | int]:
        death_count = self._age_and_remove_dead()
        self._prune_active_pairs(year)
        visibility_radius = visibility_radius_for_year(self.config, year)
        action_radius = self._action_radius()
        candidate_pool_multiplier = candidate_pool_multiplier_for_year(self.config, year)
        eligible = self._eligible_agents()
        matchable_eligible = self._eligible_agents(exclude_paired=True)
        selections, visibility_stats = self._select_candidates(
            matchable_eligible,
            visibility_radius,
            action_radius,
            candidate_pool_multiplier,
        )
        new_pairs, blocked_mutual_pair_count = self._form_pairs(matchable_eligible, selections, action_radius)
        self._activate_pairs(new_pairs, year)
        reproductive_pairs = self._active_reproductive_pairs()
        offspring_counts: dict[int, int] = defaultdict(int)
        children: list[Agent] = []
        effective_birth_probability = self._effective_birth_probability(year)

        for parent_a, parent_b in reproductive_pairs:
            child_count = self._draw_child_count(
                self._pair_birth_probability(parent_a, parent_b, effective_birth_probability)
            )
            for _ in range(child_count):
                child = create_child(
                    child_id=self._next_id(),
                    parent_a=parent_a,
                    parent_b=parent_b,
                    rng=self.rng,
                    mutation_std=self.config.mutation_std,
                    lifespan_mean=self.config.lifespan_mean,
                    lifespan_std=self.config.lifespan_std,
                    preference_alpha=self.config.preference_alpha,
                    world_size=self.config.world_size,
                )
                child.region_id = self._region_for_location(child.location)
                child.aspiration_quantile = self._child_aspiration_quantile(child.gender, parent_a, parent_b)
                children.append(child)
                offspring_counts[parent_a.id] += 1
                offspring_counts[parent_b.id] += 1

        self.agents.extend(children)
        matched_agent_ids = {agent.id for pair in reproductive_pairs for agent in pair}
        matched_agent_count = len(matched_agent_ids)

        row = yearly_metrics(
            year=year,
            calendar_year=self.config.start_calendar_year + year - 1,
            agents=self.agents,
            birth_count=len(children),
            death_count=death_count,
            matched_pair_count=len(reproductive_pairs),
            new_pair_count=len(new_pairs),
            active_pair_count=len(self.active_pairs),
            eligible_count=len(eligible),
            matched_agent_count=matched_agent_count,
            mean_visible_candidate_count=visibility_stats["mean_visible_candidate_count"],
            median_visible_candidate_count=visibility_stats["median_visible_candidate_count"],
            mean_perceived_candidate_count=visibility_stats["mean_perceived_candidate_count"],
            median_perceived_candidate_count=visibility_stats["median_perceived_candidate_count"],
            mean_actionable_candidate_count=visibility_stats["mean_actionable_candidate_count"],
            action_coverage_rate=visibility_stats["action_coverage_rate"],
            visibility_action_gap=visibility_stats["visibility_action_gap"],
            mean_selected_actionable_share=visibility_stats["mean_selected_actionable_share"],
            mean_selection_quota=visibility_stats["mean_selection_quota"],
            mean_selection_acceptance_share=visibility_stats["mean_selection_acceptance_share"],
            mean_phantom_candidate_count=visibility_stats["mean_phantom_candidate_count"],
            mean_sampled_phantom_candidate_count=visibility_stats["mean_sampled_phantom_candidate_count"],
            mean_selected_phantom_count=visibility_stats["mean_selected_phantom_count"],
            mean_phantom_selection_share=visibility_stats["mean_phantom_selection_share"],
            candidate_pool_multiplier=candidate_pool_multiplier,
            visibility_coverage_rate=visibility_stats["visibility_coverage_rate"],
            theoretical_area_coverage=self._theoretical_area_coverage(visibility_radius),
            effective_birth_probability=effective_birth_probability,
            selection_worker_count=int(visibility_stats["selection_worker_count"]),
            action_radius=action_radius,
            blocked_mutual_pair_count=blocked_mutual_pair_count,
            offspring_counts=dict(offspring_counts),
            visibility_radius=visibility_radius,
            precision=self.config.metrics_precision,
        )
        row.update(self._gender_metrics(eligible, matched_agent_ids))
        return row

    def _create_initial_population(self) -> list[Agent]:
        agents: list[Agent] = []
        for _ in range(self.config.initial_population):
            age = self._sample_initial_age()
            location, region_id = self._sample_initial_location_and_region()
            gender = self._sample_initial_gender()
            aspiration_quantile = self._sample_initial_aspiration_quantile(gender)
            agents.append(
                create_random_agent(
                    agent_id=self._next_id(),
                    rng=self.rng,
                    trait_count=self.config.trait_count,
                    world_size=self.config.world_size,
                    min_age=age,
                    max_age=age,
                    lifespan_mean=self.config.lifespan_mean,
                    lifespan_std=self.config.lifespan_std,
                    trait_mean=self.config.trait_mean,
                    trait_std=self.config.trait_std,
                    preference_alpha=self.config.preference_alpha,
                    selectivity_mean=self.config.selectivity_mean,
                    selectivity_std=self.config.selectivity_std,
                    location=location,
                    region_id=region_id,
                    gender=gender,
                    aspiration_quantile=aspiration_quantile,
                )
            )
        return agents

    def _sample_initial_gender(self) -> str | None:
        if self.config.gender_mode == "none":
            return None
        if self.config.gender_mode == "binary-balanced":
            return "A" if self.next_agent_id % 2 == 0 else "B"
        raise ValueError(f"Unknown gender mode: {self.config.gender_mode}")

    def _sample_initial_aspiration_quantile(self, gender: str | None) -> float | None:
        if not self._gender_is_aspirational(gender):
            return None

        values = self.config.aspirational_min_score_quantile_distribution
        if values is None or len(values) == 0:
            return float(np.clip(self.config.aspirational_min_score_quantile, 0.0, 1.0))

        probabilities: np.ndarray | None = None
        weights = self.config.aspirational_min_score_quantile_weights
        if weights is not None:
            if len(weights) != len(values):
                raise ValueError("aspirational_min_score_quantile_weights must match distribution length")
            weights_array = np.asarray(weights, dtype=float)
            if np.any(weights_array < 0.0) or float(weights_array.sum()) <= 0.0:
                raise ValueError("aspirational_min_score_quantile_weights must be non-negative and non-zero")
            probabilities = weights_array / float(weights_array.sum())

        index = int(self.rng.choice(len(values), p=probabilities))
        return float(np.clip(values[index], 0.0, 1.0))

    def _sample_initial_age(self) -> int:
        if self.config.initial_age_distribution == "uniform":
            return int(self.rng.integers(self.config.initial_min_age, self.config.initial_max_age + 1))
        if self.config.initial_age_distribution == "japan-1980-stylized":
            bins = ((0, 14), (15, 24), (25, 44), (45, 64), (65, 90))
            weights = np.asarray([0.23, 0.15, 0.30, 0.23, 0.09], dtype=float)
            bin_index = int(self.rng.choice(len(bins), p=weights / weights.sum()))
            low, high = bins[bin_index]
            low = max(low, self.config.initial_min_age)
            high = min(high, self.config.initial_max_age)
            if low > high:
                return int(self.rng.integers(self.config.initial_min_age, self.config.initial_max_age + 1))
            return int(self.rng.integers(low, high + 1))
        raise ValueError(f"Unknown initial age distribution: {self.config.initial_age_distribution}")

    def _create_location_cluster_centers(self) -> np.ndarray:
        if self.config.location_model != "clustered":
            return np.empty((0, 2), dtype=np.float64)
        count = max(1, self.config.location_cluster_count)
        return self.rng.uniform(0.0, self.config.world_size, size=(count, 2)).astype(np.float64)

    def _sample_initial_location_and_region(self) -> tuple[np.ndarray | None, int | None]:
        if self.config.location_model == "uniform":
            return None, None
        if self.config.location_model != "clustered":
            raise ValueError(f"Unknown location model: {self.config.location_model}")
        region_id = int(self.rng.integers(0, len(self.location_cluster_centers)))
        center = self.location_cluster_centers[region_id]
        location = center + self.rng.normal(0.0, self.config.location_cluster_std, size=2)
        return np.clip(location, 0.0, self.config.world_size).astype(np.float64), region_id

    def _region_for_location(self, location: np.ndarray) -> int | None:
        if self.config.location_model != "clustered" or self.location_cluster_centers.size == 0:
            return None
        distances = np.linalg.norm(self.location_cluster_centers - location, axis=1)
        return int(np.argmin(distances))

    def _next_id(self) -> int:
        agent_id = self.next_agent_id
        self.next_agent_id += 1
        return agent_id

    def _age_and_remove_dead(self) -> int:
        death_count = 0
        for agent in self.agents:
            if agent.age_one_year():
                death_count += 1
        self.agents = [agent for agent in self.agents if agent.alive]
        return death_count

    def _eligible_agents(self, *, exclude_paired: bool = False) -> list[Agent]:
        paired_ids = self._active_pair_ids() if exclude_paired else set()
        return [
            agent
            for agent in self.agents
            if agent.id not in paired_ids
            and agent.is_reproductive_age(self.config.reproductive_min_age, self.config.reproductive_max_age)
        ]

    def _create_initial_pairs(self) -> list[Pair]:
        target_pair_count = int((self.config.initial_population * self.config.initial_pair_fraction) // 2)
        if target_pair_count <= 0:
            return []

        eligible = self._eligible_agents()
        action_radius = self._action_radius()
        pairs: list[tuple[Agent, Agent]] = []
        available_indexes = set(range(len(eligible)))
        locations = np.asarray([agent.location for agent in eligible])
        for index in self.rng.permutation(len(eligible)):
            if len(pairs) >= target_pair_count:
                break
            if index not in available_indexes:
                continue
            available_indexes.remove(index)
            agent = eligible[index]
            candidate_indexes = np.asarray(sorted(available_indexes), dtype=int)
            candidate_indexes = np.asarray(
                [
                    candidate_index
                    for candidate_index in candidate_indexes
                    if self._genders_compatible(agent, eligible[int(candidate_index)])
                ],
                dtype=int,
            )
            if not self.config.allow_cross_region_pairing:
                candidate_indexes = np.asarray(
                    [
                        candidate_index
                        for candidate_index in candidate_indexes
                        if self._regions_compatible(agent, eligible[int(candidate_index)])
                    ],
                    dtype=int,
                )
            if candidate_indexes.size == 0:
                break
            distances = np.linalg.norm(locations[candidate_indexes] - agent.location, axis=1)
            within_radius_indexes = candidate_indexes[distances <= action_radius]
            if within_radius_indexes.size == 0:
                continue
            scored_candidates = [
                (
                    agent.score_candidate(eligible[candidate_index])
                    + eligible[candidate_index].score_candidate(agent),
                    candidate_index,
                )
                for candidate_index in within_radius_indexes
            ]
            _, candidate_index = max(scored_candidates, key=lambda item: item[0])
            available_indexes.remove(candidate_index)
            pairs.append((agent, eligible[candidate_index]))
        return [
            Pair(
                agent_a_id=agent_a.id,
                agent_b_id=agent_b.id,
                end_year=self._draw_initial_pair_end_year(),
            )
            for agent_a, agent_b in pairs[:target_pair_count]
        ]

    def _draw_initial_pair_end_year(self) -> int:
        duration = max(1, self._draw_pair_duration())
        return int(self.rng.integers(1, duration + 1))

    def _draw_pair_duration(self) -> int:
        duration = self.rng.normal(self.config.pair_duration_mean, self.config.pair_duration_std)
        return max(1, int(round(duration)))

    def _activate_pairs(self, pairs: list[tuple[Agent, Agent]], year: int) -> None:
        for agent_a, agent_b in pairs:
            self.active_pairs.append(
                Pair(
                    agent_a_id=agent_a.id,
                    agent_b_id=agent_b.id,
                    end_year=year + self._draw_pair_duration(),
                )
            )

    def _prune_active_pairs(self, year: int) -> None:
        living_ids = {agent.id for agent in self.agents if agent.alive}
        self.active_pairs = [
            pair
            for pair in self.active_pairs
            if pair.end_year >= year and pair.agent_a_id in living_ids and pair.agent_b_id in living_ids
        ]

    def _active_pair_ids(self) -> set[int]:
        return {agent_id for pair in self.active_pairs for agent_id in (pair.agent_a_id, pair.agent_b_id)}

    def _active_reproductive_pairs(self) -> list[tuple[Agent, Agent]]:
        by_id = {agent.id: agent for agent in self.agents if agent.alive}
        pairs: list[tuple[Agent, Agent]] = []
        for pair in self.active_pairs:
            agent_a = by_id.get(pair.agent_a_id)
            agent_b = by_id.get(pair.agent_b_id)
            if agent_a is None or agent_b is None:
                continue
            if agent_a.is_reproductive_age(self.config.reproductive_min_age, self.config.reproductive_max_age) and (
                agent_b.is_reproductive_age(self.config.reproductive_min_age, self.config.reproductive_max_age)
            ):
                pairs.append((agent_a, agent_b))
        return pairs

    def _gender_metrics(self, eligible: list[Agent], matched_agent_ids: set[int]) -> dict[str, float | int]:
        if self.config.gender_mode == "none":
            return {}

        living_a = [agent for agent in self.agents if agent.alive and agent.gender == "A"]
        living_b = [agent for agent in self.agents if agent.alive and agent.gender == "B"]
        eligible_a = [agent for agent in eligible if agent.gender == "A"]
        eligible_b = [agent for agent in eligible if agent.gender == "B"]
        matched_a = sum(1 for agent in eligible_a if agent.id in matched_agent_ids)
        matched_b = sum(1 for agent in eligible_b if agent.id in matched_agent_ids)
        return {
            "population_gender_a": len(living_a),
            "population_gender_b": len(living_b),
            "eligible_gender_a": len(eligible_a),
            "eligible_gender_b": len(eligible_b),
            "unmatched_rate_gender_a": self._unmatched_rate_for_group(len(eligible_a), matched_a),
            "unmatched_rate_gender_b": self._unmatched_rate_for_group(len(eligible_b), matched_b),
        }

    @staticmethod
    def _unmatched_rate_for_group(eligible_count: int, matched_count: int) -> float:
        if eligible_count <= 0:
            return 0.0
        return float(1.0 - matched_count / eligible_count)

    def _select_candidates(
        self,
        eligible: list[Agent],
        radius: float,
        action_radius: float,
        candidate_pool_multiplier: float,
    ) -> tuple[dict[int, set[int]], dict[str, float]]:
        selections: dict[int, set[int]] = {}
        if len(eligible) < 2:
            return selections, {
                "mean_visible_candidate_count": 0.0,
                "median_visible_candidate_count": 0.0,
                "mean_perceived_candidate_count": 0.0,
                "median_perceived_candidate_count": 0.0,
                "mean_actionable_candidate_count": 0.0,
                "action_coverage_rate": 0.0,
                "visibility_action_gap": 0.0,
                "mean_selected_actionable_share": 0.0,
                "mean_selection_quota": 0.0,
                "mean_selection_acceptance_share": 0.0,
                "mean_phantom_candidate_count": 0.0,
                "mean_sampled_phantom_candidate_count": 0.0,
                "mean_selected_phantom_count": 0.0,
                "mean_phantom_selection_share": 0.0,
                "visibility_coverage_rate": 0.0,
                "selection_worker_count": 1.0,
            }

        locations = np.asarray([agent.location for agent in eligible])
        traits = np.asarray([agent.traits for agent in eligible])
        ids = np.asarray([agent.id for agent in eligible])
        regions = np.asarray(
            [-1 if agent.region_id is None else int(agent.region_id) for agent in eligible],
            dtype=int,
        )
        genders = np.asarray(["" if agent.gender is None else agent.gender for agent in eligible], dtype=object)
        worker_count = resolve_worker_count(self.config, len(eligible))

        if worker_count == 1:
            results = [
                self._select_candidates_for_agent(
                    index,
                    agent,
                    locations,
                    traits,
                    ids,
                    regions,
                    genders,
                    radius,
                    action_radius,
                    candidate_pool_multiplier,
                )
                for index, agent in enumerate(eligible)
            ]
        else:
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                results = list(
                    executor.map(
                        lambda item: self._select_candidates_for_agent(
                            item[0],
                            item[1],
                            locations,
                            traits,
                            ids,
                            regions,
                            genders,
                            radius,
                            action_radius,
                            candidate_pool_multiplier,
                        ),
                        enumerate(eligible),
                    )
                )

        visible_counts: list[int] = []
        actionable_counts: list[int] = []
        selection_quotas: list[int] = []
        perceived_counts: list[float] = []
        acceptance_shares: list[float] = []
        selected_actionable_shares: list[float] = []
        phantom_counts: list[int] = []
        sampled_phantom_counts: list[int] = []
        selected_phantom_counts: list[int] = []
        phantom_selection_shares: list[float] = []
        for (
            agent_id,
            selected_ids,
            visible_count,
            actionable_count,
            selection_quota,
            selected_actionable_count,
            perceived_count,
            phantom_count,
            sampled_phantom_count,
            selected_phantom_count,
        ) in results:
            selections[agent_id] = selected_ids
            visible_counts.append(visible_count)
            actionable_counts.append(actionable_count)
            selection_quotas.append(selection_quota)
            perceived_counts.append(perceived_count)
            acceptance_shares.append(0.0 if perceived_count <= 0.0 else selection_quota / perceived_count)
            selected_actionable_shares.append(
                0.0 if selection_quota <= 0 else selected_actionable_count / selection_quota
            )
            phantom_counts.append(phantom_count)
            sampled_phantom_counts.append(sampled_phantom_count)
            selected_phantom_counts.append(selected_phantom_count)
            phantom_selection_shares.append(0.0 if selection_quota <= 0 else selected_phantom_count / selection_quota)

        coverage_denominator = max(len(eligible) - 1, 1)
        visible_counts_array = np.asarray(visible_counts)
        actionable_counts_array = np.asarray(actionable_counts)
        stats = {
            "mean_visible_candidate_count": float(np.mean(visible_counts)),
            "median_visible_candidate_count": float(np.median(visible_counts)),
            "mean_perceived_candidate_count": float(np.mean(perceived_counts)),
            "median_perceived_candidate_count": float(np.median(perceived_counts)),
            "mean_actionable_candidate_count": float(np.mean(actionable_counts)),
            "action_coverage_rate": float(np.mean(actionable_counts_array / coverage_denominator)),
            "visibility_action_gap": float(
                np.mean((visible_counts_array - actionable_counts_array) / coverage_denominator)
            ),
            "mean_selected_actionable_share": float(np.mean(selected_actionable_shares)),
            "mean_selection_quota": float(np.mean(selection_quotas)),
            "mean_selection_acceptance_share": float(np.mean(acceptance_shares)),
            "mean_phantom_candidate_count": float(np.mean(phantom_counts)),
            "mean_sampled_phantom_candidate_count": float(np.mean(sampled_phantom_counts)),
            "mean_selected_phantom_count": float(np.mean(selected_phantom_counts)),
            "mean_phantom_selection_share": float(np.mean(phantom_selection_shares)),
            "visibility_coverage_rate": float(np.mean(np.asarray(visible_counts) / coverage_denominator)),
            "selection_worker_count": float(worker_count),
        }
        return selections, stats

    def _select_candidates_for_agent(
        self,
        index: int,
        agent: Agent,
        locations: np.ndarray,
        traits: np.ndarray,
        ids: np.ndarray,
        regions: np.ndarray,
        genders: np.ndarray,
        radius: float,
        action_radius: float,
        candidate_pool_multiplier: float,
    ) -> tuple[int, set[int], int, int, int, int, float, int, int, int]:
        distances = np.linalg.norm(locations - agent.location, axis=1)
        candidate_indexes = np.where((distances <= radius) & (np.arange(len(locations)) != index))[0]
        actionable_visibility_radius = min(radius, action_radius)
        region_compatible = self._region_compatibility_mask(index, regions)
        actionable_indexes = np.where(
            (distances <= actionable_visibility_radius)
            & (np.arange(len(locations)) != index)
            & region_compatible
        )[0]
        if self.config.gender_mode != "none":
            candidate_indexes = np.asarray(
                [
                    candidate_index
                    for candidate_index in candidate_indexes
                    if self._gender_values_compatible(agent.gender, str(genders[candidate_index]) or None)
                ],
                dtype=int,
            )
            actionable_indexes = np.asarray(
                [
                    actionable_index
                    for actionable_index in actionable_indexes
                    if self._gender_values_compatible(agent.gender, str(genders[actionable_index]) or None)
                ],
                dtype=int,
            )
        visible_count = int(candidate_indexes.size)
        actionable_count = int(actionable_indexes.size)
        phantom_count = self._phantom_candidate_count(visible_count, candidate_pool_multiplier)
        sampled_phantom_count = min(phantom_count, max(0, self.config.phantom_candidate_sample_cap))
        perceived_count = visible_count * candidate_pool_multiplier
        if visible_count == 0:
            return agent.id, set(), visible_count, actionable_count, 0, 0, perceived_count, 0, 0, 0

        real_scores = traits[candidate_indexes] @ agent.preference_weights
        competition_scores = real_scores
        competition_real_indexes = np.arange(visible_count, dtype=int)
        if sampled_phantom_count > 0:
            phantom_scores = self._sample_phantom_scores(
                agent=agent,
                visible_count=visible_count,
                phantom_count=phantom_count,
                sampled_phantom_count=sampled_phantom_count,
            )
            competition_scores = np.concatenate([real_scores, phantom_scores])
            competition_real_indexes = np.concatenate(
                [competition_real_indexes, np.full(sampled_phantom_count, -1, dtype=int)]
            )

        keep_count = self._selection_quota(agent, int(competition_scores.size))
        minimum_score = self._minimum_selection_score(agent, competition_scores)
        reserved_real_indexes = self._reserved_actionable_candidate_indexes(
            agent=agent,
            real_scores=real_scores,
            candidate_indexes=candidate_indexes,
            actionable_indexes=actionable_indexes,
            keep_count=keep_count,
            minimum_score=minimum_score,
        )
        reserved_real_index_set = set(reserved_real_indexes)
        fill_count = keep_count - len(reserved_real_indexes)
        selectable_mask = np.asarray(
            [
                real_index < 0 or int(real_index) not in reserved_real_index_set
                for real_index in competition_real_indexes
            ],
            dtype=bool,
        )
        score_mask = competition_scores >= minimum_score
        fill_competition_indexes = np.where(selectable_mask & score_mask)[0]
        if fill_count > 0 and fill_competition_indexes.size > 0:
            fill_count = min(fill_count, int(fill_competition_indexes.size))
            fill_scores = competition_scores[fill_competition_indexes]
            top_fill_indexes = fill_competition_indexes[np.argsort(fill_scores)[-fill_count:]]
        else:
            top_fill_indexes = np.empty(0, dtype=int)
        selected_real_indexes = list(reserved_real_indexes) + [
            int(competition_real_indexes[top_index])
            for top_index in top_fill_indexes
            if competition_real_indexes[top_index] >= 0
        ]
        selected_phantom_count = int(np.sum(competition_real_indexes[top_fill_indexes] < 0))
        selected_ids = {int(ids[candidate_indexes[real_index]]) for real_index in selected_real_indexes}
        actionable_ids = {int(ids[actionable_index]) for actionable_index in actionable_indexes}
        selected_actionable_count = len(selected_ids & actionable_ids)
        return (
            agent.id,
            selected_ids,
            visible_count,
            actionable_count,
            keep_count,
            selected_actionable_count,
            perceived_count,
            phantom_count,
            sampled_phantom_count,
            selected_phantom_count,
        )

    def _reserved_actionable_candidate_indexes(
        self,
        *,
        agent: Agent,
        real_scores: np.ndarray,
        candidate_indexes: np.ndarray,
        actionable_indexes: np.ndarray,
        keep_count: int,
        minimum_score: float,
    ) -> list[int]:
        reserve_fraction = self._actionable_reserve_fraction_for_agent(agent)
        reserve_count = min(keep_count, int(np.ceil(keep_count * reserve_fraction)))
        if reserve_count <= 0 or actionable_indexes.size == 0:
            return []

        actionable_index_set = set(int(index) for index in actionable_indexes)
        actionable_real_positions = [
            position
            for position, candidate_index in enumerate(candidate_indexes)
            if int(candidate_index) in actionable_index_set and real_scores[position] >= minimum_score
        ]
        if not actionable_real_positions:
            return []

        reserve_count = min(reserve_count, len(actionable_real_positions))
        actionable_scores = real_scores[actionable_real_positions]
        top_positions = np.argsort(actionable_scores)[-reserve_count:]
        return [int(actionable_real_positions[position]) for position in top_positions]

    def _actionable_reserve_fraction_for_agent(self, agent: Agent | None) -> float:
        if (
            agent is not None
            and agent.region_id is not None
            and self.config.regional_actionable_reserve_fractions is not None
        ):
            fractions = self.config.regional_actionable_reserve_fractions
            if 0 <= agent.region_id < len(fractions):
                return float(np.clip(fractions[agent.region_id], 0.0, 1.0))
        return float(np.clip(self.config.actionable_selection_reserve_fraction, 0.0, 1.0))

    def _phantom_candidate_count(self, visible_count: int, candidate_pool_multiplier: float) -> int:
        if self.config.phantom_candidate_mode == "none" or visible_count <= 0:
            return 0
        if self.config.phantom_candidate_mode != "sampled":
            raise ValueError(f"Unknown phantom candidate mode: {self.config.phantom_candidate_mode}")
        return max(0, int(round(visible_count * max(candidate_pool_multiplier - 1.0, 0.0))))

    def _sample_phantom_scores(
        self,
        *,
        agent: Agent,
        visible_count: int,
        phantom_count: int,
        sampled_phantom_count: int,
    ) -> np.ndarray:
        rng = np.random.default_rng(self._phantom_seed(agent.id, visible_count, phantom_count))
        phantom_traits = rng.normal(
            self.config.trait_mean,
            self.config.trait_std,
            size=(sampled_phantom_count, self.config.trait_count),
        )
        return phantom_traits @ agent.preference_weights

    def _phantom_seed(self, agent_id: int, visible_count: int, phantom_count: int) -> int:
        base_seed = 0 if self.config.seed is None else int(self.config.seed)
        return (
            base_seed * 1_000_003
            + agent_id * 97_003
            + visible_count * 1_009
            + phantom_count * 9_176
        ) % (2**63 - 1)

    def _selection_quota(self, agent: Agent, visible_count: int) -> int:
        if visible_count <= 0:
            return 0
        if self.config.selection_mode == "top-k":
            return min(visible_count, self._effective_top_k(agent))
        if self.config.selection_mode == "percentile":
            return max(1, int(np.ceil(visible_count * self._effective_selectivity(agent))))
        raise ValueError(f"Unknown selection mode: {self.config.selection_mode}")

    def _effective_top_k(self, agent: Agent) -> int:
        top_k = max(1, self.config.top_k)
        if self._is_aspirational_agent(agent):
            top_k = max(1, int(np.floor(top_k * self.config.aspirational_top_k_multiplier)))
        return top_k

    def _effective_selectivity(self, agent: Agent) -> float:
        selectivity = agent.selectivity
        if self._is_aspirational_agent(agent):
            selectivity *= self.config.aspirational_selectivity_multiplier
        return float(np.clip(selectivity, 0.01, 1.0))

    def _minimum_selection_score(self, agent: Agent, competition_scores: np.ndarray) -> float:
        if competition_scores.size == 0 or not self._is_aspirational_agent(agent):
            return float("-inf")
        quantile = self._aspiration_quantile_for_agent(agent)
        if quantile <= 0.0:
            return float("-inf")
        return float(np.quantile(competition_scores, quantile))

    def _aspiration_quantile_for_agent(self, agent: Agent) -> float:
        if agent.aspiration_quantile is not None:
            return float(np.clip(agent.aspiration_quantile, 0.0, 1.0))
        return float(np.clip(self.config.aspirational_min_score_quantile, 0.0, 1.0))

    def _child_aspiration_quantile(
        self,
        child_gender: str | None,
        parent_a: Agent,
        parent_b: Agent,
    ) -> float | None:
        if not self._gender_is_aspirational(child_gender):
            return None
        inherited = [
            parent.aspiration_quantile
            for parent in (parent_a, parent_b)
            if parent.aspiration_quantile is not None
        ]
        if not inherited:
            return self._sample_initial_aspiration_quantile(child_gender)
        quantile = float(np.mean(inherited))
        quantile += float(self.rng.normal(0.0, self.config.aspirational_quantile_mutation_std))
        return float(np.clip(quantile, 0.0, 1.0))

    def _is_aspirational_agent(self, agent: Agent) -> bool:
        return self._gender_is_aspirational(agent.gender)

    def _gender_is_aspirational(self, gender: str | None) -> bool:
        target = self.config.aspirational_gender
        if target == "none" or gender is None:
            return False
        return target == "both" or gender == target

    def _form_pairs(
        self,
        eligible: list[Agent],
        selections: dict[int, set[int]],
        action_radius: float,
    ) -> tuple[list[tuple[Agent, Agent]], int]:
        by_id = {agent.id: agent for agent in eligible}
        mutual_pairs: list[tuple[float, Agent, Agent]] = []
        blocked_mutual_pair_count = 0

        for agent in eligible:
            for candidate_id in sorted(selections.get(agent.id, set())):
                if agent.id >= candidate_id:
                    continue
                if agent.id in selections.get(candidate_id, set()):
                    candidate = by_id[candidate_id]
                    if not self._genders_compatible(agent, candidate):
                        blocked_mutual_pair_count += 1
                        continue
                    if not self._regions_compatible(agent, candidate):
                        blocked_mutual_pair_count += 1
                        continue
                    if np.linalg.norm(agent.location - candidate.location) > action_radius:
                        blocked_mutual_pair_count += 1
                        continue
                    pair_score = agent.score_candidate(candidate) + candidate.score_candidate(agent)
                    mutual_pairs.append((pair_score, agent, candidate))

        mutual_pairs.sort(key=lambda item: (-item[0], item[1].id, item[2].id))
        paired_ids: set[int] = set()
        pairs: list[tuple[Agent, Agent]] = []
        for _, agent, candidate in mutual_pairs:
            if agent.id in paired_ids or candidate.id in paired_ids:
                continue
            paired_ids.add(agent.id)
            paired_ids.add(candidate.id)
            pairs.append((agent, candidate))

        return pairs, blocked_mutual_pair_count

    def _region_compatibility_mask(self, index: int, regions: np.ndarray) -> np.ndarray:
        if self.config.allow_cross_region_pairing:
            return np.ones(len(regions), dtype=bool)
        own_region = int(regions[index])
        return regions == own_region

    def _regions_compatible(self, agent: Agent, candidate: Agent) -> bool:
        if self.config.allow_cross_region_pairing:
            return True
        return agent.region_id == candidate.region_id

    def _genders_compatible(self, agent: Agent, candidate: Agent) -> bool:
        return self._gender_values_compatible(agent.gender, candidate.gender)

    def _gender_values_compatible(self, gender: str | None, candidate_gender: str | None) -> bool:
        if self.config.gender_mode == "none":
            return True
        if self.config.gender_mode == "binary-balanced":
            return gender is not None and candidate_gender is not None and gender != candidate_gender
        raise ValueError(f"Unknown gender mode: {self.config.gender_mode}")

    def _draw_child_count(self, effective_birth_probability: float) -> int:
        if self.rng.random() > effective_birth_probability:
            return 0

        child_count = 1
        while (
            child_count < self.config.max_children_per_pair
            and self.rng.random() < self.config.additional_child_probability
        ):
            child_count += 1
        return child_count

    def _pair_birth_probability(
        self,
        parent_a: Agent,
        parent_b: Agent,
        base_birth_probability: float,
    ) -> float:
        if self.config.fertility_age_profile == "flat":
            return base_birth_probability
        if self.config.fertility_age_profile == "japan-stylized":
            age_weight = float(
                np.sqrt(
                    self._fertility_age_weight(parent_a.age)
                    * self._fertility_age_weight(parent_b.age)
                )
            )
            return float(np.clip(base_birth_probability * age_weight, 0.0, 1.0))
        raise ValueError(f"Unknown fertility age profile: {self.config.fertility_age_profile}")

    @staticmethod
    def _fertility_age_weight(age: int) -> float:
        if age < 20:
            return 0.05
        if age < 25:
            return 0.35
        if age < 30:
            return 0.85
        if age < 35:
            return 1.0
        if age < 40:
            return 0.65
        if age < 45:
            return 0.20
        return 0.03

    def _theoretical_area_coverage(self, radius: float) -> float:
        world_area = self.config.world_size**2
        if world_area <= 0.0:
            return 0.0
        circle_area = np.pi * radius**2
        return float(np.clip(circle_area / world_area, 0.0, 1.0))

    def _scheduled_birth_probability(self, year: int) -> float:
        if self.config.birth_probability_schedule == "fixed":
            return self.config.birth_probability
        if self.config.birth_probability_schedule == "japan-tfr-stylized":
            calendar_year = self.config.start_calendar_year + year - 1
            anchors = np.asarray(
                [
                    (1980.0, 1.28),
                    (1990.0, 1.12),
                    (2000.0, 1.00),
                    (2005.0, 0.93),
                    (2010.0, 0.98),
                    (2015.0, 0.94),
                    (2020.0, 0.91),
                    (2024.0, 0.80),
                    (2070.0, 0.72),
                ],
                dtype=float,
            )
            multiplier = float(np.interp(calendar_year, anchors[:, 0], anchors[:, 1]))
            return float(np.clip(self.config.birth_probability * multiplier, 0.0, 1.0))
        raise ValueError(f"Unknown birth probability schedule: {self.config.birth_probability_schedule}")

    def _effective_birth_probability(self, year: int) -> float:
        scheduled_birth_probability = self._scheduled_birth_probability(year)
        if self.config.carrying_capacity is None or self.config.carrying_capacity <= 0:
            return scheduled_birth_probability
        living_population = sum(1 for agent in self.agents if agent.alive)
        capacity_factor = 1.0 - living_population / self.config.carrying_capacity
        return float(np.clip(scheduled_birth_probability * capacity_factor, 0.0, scheduled_birth_probability))

    def _action_radius(self) -> float:
        if self.config.action_radius is None:
            return self.config.max_radius
        return self.config.action_radius

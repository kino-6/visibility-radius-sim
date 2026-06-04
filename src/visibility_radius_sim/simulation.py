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
        effective_birth_probability = self._effective_birth_probability()

        for parent_a, parent_b in reproductive_pairs:
            child_count = self._draw_child_count(effective_birth_probability)
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
                children.append(child)
                offspring_counts[parent_a.id] += 1
                offspring_counts[parent_b.id] += 1

        self.agents.extend(children)
        matched_agent_count = len({agent.id for pair in reproductive_pairs for agent in pair})

        return yearly_metrics(
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

    def _create_initial_population(self) -> list[Agent]:
        agents: list[Agent] = []
        for _ in range(self.config.initial_population):
            age = self._sample_initial_age()
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
                    location=self._sample_initial_location(),
                )
            )
        return agents

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

    def _sample_initial_location(self) -> np.ndarray | None:
        if self.config.location_model == "uniform":
            return None
        if self.config.location_model != "clustered":
            raise ValueError(f"Unknown location model: {self.config.location_model}")
        center = self.location_cluster_centers[int(self.rng.integers(0, len(self.location_cluster_centers)))]
        location = center + self.rng.normal(0.0, self.config.location_cluster_std, size=2)
        return np.clip(location, 0.0, self.config.world_size).astype(np.float64)

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
                "visibility_coverage_rate": 0.0,
                "selection_worker_count": 1.0,
            }

        locations = np.asarray([agent.location for agent in eligible])
        traits = np.asarray([agent.traits for agent in eligible])
        ids = np.asarray([agent.id for agent in eligible])
        worker_count = resolve_worker_count(self.config, len(eligible))

        if worker_count == 1:
            results = [
                self._select_candidates_for_agent(
                    index,
                    agent,
                    locations,
                    traits,
                    ids,
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
        for (
            agent_id,
            selected_ids,
            visible_count,
            actionable_count,
            selection_quota,
            selected_actionable_count,
            perceived_count,
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
        radius: float,
        action_radius: float,
        candidate_pool_multiplier: float,
    ) -> tuple[int, set[int], int, int, int, int, float]:
        distances = np.linalg.norm(locations - agent.location, axis=1)
        candidate_indexes = np.where((distances <= radius) & (np.arange(len(locations)) != index))[0]
        actionable_visibility_radius = min(radius, action_radius)
        actionable_indexes = np.where(
            (distances <= actionable_visibility_radius) & (np.arange(len(locations)) != index)
        )[0]
        visible_count = int(candidate_indexes.size)
        actionable_count = int(actionable_indexes.size)
        perceived_count = visible_count * candidate_pool_multiplier
        if visible_count == 0:
            return agent.id, set(), visible_count, actionable_count, 0, 0, perceived_count

        scores = traits[candidate_indexes] @ agent.preference_weights
        keep_count = self._selection_quota(agent, visible_count)
        top_indexes = np.argsort(scores)[-keep_count:]
        selected_ids = {int(ids[candidate_indexes[top_index]]) for top_index in top_indexes}
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
        )

    def _selection_quota(self, agent: Agent, visible_count: int) -> int:
        if visible_count <= 0:
            return 0
        if self.config.selection_mode == "top-k":
            return min(visible_count, max(1, self.config.top_k))
        if self.config.selection_mode == "percentile":
            return max(1, int(np.ceil(visible_count * agent.selectivity)))
        raise ValueError(f"Unknown selection mode: {self.config.selection_mode}")

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

    def _theoretical_area_coverage(self, radius: float) -> float:
        world_area = self.config.world_size**2
        if world_area <= 0.0:
            return 0.0
        circle_area = np.pi * radius**2
        return float(np.clip(circle_area / world_area, 0.0, 1.0))

    def _effective_birth_probability(self) -> float:
        if self.config.carrying_capacity is None or self.config.carrying_capacity <= 0:
            return self.config.birth_probability
        living_population = sum(1 for agent in self.agents if agent.alive)
        capacity_factor = 1.0 - living_population / self.config.carrying_capacity
        return float(np.clip(self.config.birth_probability * capacity_factor, 0.0, self.config.birth_probability))

    def _action_radius(self) -> float:
        if self.config.action_radius is None:
            return self.config.max_radius
        return self.config.action_radius

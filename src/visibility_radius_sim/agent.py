from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


@dataclass
class Agent:
    id: int
    age: int
    lifespan: int
    location: FloatArray
    traits: FloatArray
    preference_weights: FloatArray
    selectivity: float
    alive: bool = True

    def age_one_year(self) -> bool:
        """Age the agent and return True when this step caused death."""

        if not self.alive:
            return False
        self.age += 1
        if self.age > self.lifespan:
            self.alive = False
            return True
        return False

    def score_candidate(self, candidate: "Agent") -> float:
        return float(np.dot(self.preference_weights, candidate.traits))

    def is_reproductive_age(self, min_age: int, max_age: int) -> bool:
        return self.alive and min_age <= self.age <= max_age


def random_preference_weights(trait_count: int, rng: np.random.Generator, alpha: float) -> FloatArray:
    weights = rng.dirichlet(np.full(trait_count, alpha, dtype=float))
    return weights.astype(np.float64)


def create_random_agent(
    agent_id: int,
    rng: np.random.Generator,
    trait_count: int,
    world_size: float,
    min_age: int,
    max_age: int,
    lifespan_mean: float,
    lifespan_std: float,
    trait_mean: float,
    trait_std: float,
    preference_alpha: float,
    selectivity_mean: float,
    selectivity_std: float,
    location: FloatArray | None = None,
) -> Agent:
    age = int(rng.integers(min_age, max_age + 1))
    lifespan = _sample_lifespan_conditioned_on_age(age, lifespan_mean, lifespan_std, rng)
    selectivity = float(np.clip(rng.normal(selectivity_mean, selectivity_std), 0.01, 1.0))
    return Agent(
        id=agent_id,
        age=age,
        lifespan=lifespan,
        location=(
            rng.uniform(0.0, world_size, size=2).astype(np.float64)
            if location is None
            else location.astype(np.float64)
        ),
        traits=rng.normal(trait_mean, trait_std, size=trait_count).astype(np.float64),
        preference_weights=random_preference_weights(trait_count, rng, preference_alpha),
        selectivity=selectivity,
    )


def _sample_lifespan_conditioned_on_age(
    age: int,
    lifespan_mean: float,
    lifespan_std: float,
    rng: np.random.Generator,
) -> int:
    """Sample an age-at-death for someone alive at the given initial age."""

    for _ in range(20):
        lifespan = max(1, int(round(rng.normal(lifespan_mean, lifespan_std))))
        if lifespan > age:
            return lifespan

    remaining_years = int(rng.integers(1, max(2, round(lifespan_std) + 1)))
    return age + remaining_years


def create_child(
    child_id: int,
    parent_a: Agent,
    parent_b: Agent,
    rng: np.random.Generator,
    mutation_std: float,
    lifespan_mean: float,
    lifespan_std: float,
    preference_alpha: float = 2.0,
    location_noise_std: float = 0.025,
    world_size: float = 1.0,
) -> Agent:
    trait_count = len(parent_a.traits)
    midpoint = 0.5 * parent_a.traits + 0.5 * parent_b.traits
    mutation = rng.normal(0.0, mutation_std, size=trait_count)
    location_midpoint = 0.5 * parent_a.location + 0.5 * parent_b.location
    location_noise = rng.normal(0.0, location_noise_std, size=2)
    lifespan = max(1, int(round(rng.normal(lifespan_mean, lifespan_std))))

    return Agent(
        id=child_id,
        age=0,
        lifespan=lifespan,
        location=np.clip(location_midpoint + location_noise, 0.0, world_size).astype(np.float64),
        traits=(midpoint + mutation).astype(np.float64),
        preference_weights=random_preference_weights(trait_count, rng, preference_alpha),
        selectivity=float(np.clip(np.mean([parent_a.selectivity, parent_b.selectivity]), 0.01, 1.0)),
    )

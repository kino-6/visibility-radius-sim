from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import os
from typing import Any, Literal

import numpy as np

RadiusSchedule = Literal["fixed", "linear", "sigmoid", "shock", "global"]
ScenarioName = Literal["baseline", "sns-2000s", "japan-2070"]
SelectionMode = Literal["percentile", "top-k"]
LocationModel = Literal["uniform", "clustered"]
InitialAgeDistribution = Literal["uniform", "japan-1980-stylized"]
PhantomCandidateMode = Literal["none", "sampled"]
GenderMode = Literal["none", "binary-balanced"]
AspirationalGender = Literal["none", "A", "B", "both"]
FertilityAgeProfile = Literal["flat", "japan-stylized"]
BirthProbabilitySchedule = Literal["fixed", "japan-tfr-stylized"]


@dataclass(frozen=True)
class SimulationConfig:
    years: int = 250
    start_calendar_year: int = 1
    initial_population: int = 1000
    seed: int | None = None
    trait_names: tuple[str, ...] = (
        "attractiveness",
        "resources",
        "intelligence",
        "kindness",
        "stability",
    )
    world_size: float = 1.0
    location_model: LocationModel = "uniform"
    location_cluster_count: int = 6
    location_cluster_std: float = 0.06
    allow_cross_region_pairing: bool = True
    initial_radius: float = 0.18
    max_radius: float = float(np.sqrt(2.0))
    action_radius: float | None = None
    radius_schedule: RadiusSchedule = "sigmoid"
    visibility_expansion_mid_year: int | None = None
    visibility_expansion_duration_years: float = 25.0
    reproductive_min_age: int = 18
    reproductive_max_age: int = 45
    initial_min_age: int = 0
    initial_max_age: int = 90
    initial_age_distribution: InitialAgeDistribution = "uniform"
    lifespan_mean: float = 78.0
    lifespan_std: float = 8.0
    selectivity_mean: float = 0.2
    selectivity_std: float = 0.04
    selection_mode: SelectionMode = "percentile"
    top_k: int = 10
    initial_candidate_pool_multiplier: float = 1.0
    max_candidate_pool_multiplier: float = 1.0
    phantom_candidate_mode: PhantomCandidateMode = "none"
    phantom_candidate_sample_cap: int = 512
    actionable_selection_reserve_fraction: float = 0.0
    regional_actionable_reserve_fractions: tuple[float, ...] | None = None
    gender_mode: GenderMode = "none"
    aspirational_gender: AspirationalGender = "none"
    aspirational_top_k_multiplier: float = 1.0
    aspirational_selectivity_multiplier: float = 1.0
    aspirational_min_score_quantile: float = 0.0
    aspirational_min_score_quantile_distribution: tuple[float, ...] | None = None
    aspirational_min_score_quantile_weights: tuple[float, ...] | None = None
    aspirational_quantile_mutation_std: float = 0.02
    trait_mean: float = 0.0
    trait_std: float = 1.0
    preference_alpha: float = 2.0
    mutation_std: float = 0.08
    birth_probability: float = 0.25
    birth_probability_schedule: BirthProbabilitySchedule = "fixed"
    additional_child_probability: float = 0.05
    max_children_per_pair: int = 2
    fertility_age_profile: FertilityAgeProfile = "flat"
    initial_pair_fraction: float = 0.0
    pair_duration_mean: float = 12.0
    pair_duration_std: float = 4.0
    carrying_capacity: int | None = 5000
    worker_count: int | None = None
    max_auto_workers: int = 8
    parallel_threshold: int = 300
    metrics_precision: int = 6
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def trait_count(self) -> int:
        return len(self.trait_names)

    def to_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values["trait_names"] = list(self.trait_names)
        return values

    @classmethod
    def for_scenario(cls, scenario: ScenarioName | None) -> "SimulationConfig":
        if scenario in (None, "baseline"):
            return cls()
        if scenario == "sns-2000s":
            return cls(
                years=80,
                start_calendar_year=1980,
                initial_population=2500,
                initial_age_distribution="japan-1980-stylized",
                location_model="clustered",
                location_cluster_count=12,
                location_cluster_std=0.035,
                initial_radius=0.02,
                max_radius=float(np.sqrt(2.0)),
                action_radius=0.12,
                radius_schedule="shock",
                visibility_expansion_mid_year=2007,
                visibility_expansion_duration_years=7.0,
                birth_probability=0.12,
                carrying_capacity=9000,
                selection_mode="top-k",
                top_k=16,
                selectivity_mean=0.18,
                initial_pair_fraction=0.55,
                pair_duration_mean=18.0,
                pair_duration_std=8.0,
                initial_candidate_pool_multiplier=1.0,
                max_candidate_pool_multiplier=300.0,
                phantom_candidate_mode="sampled",
                phantom_candidate_sample_cap=512,
                metadata={
                    "scenario": "sns-2000s",
                    "interpretation": (
                        "Abstract rapid visibility expansion inspired by search, social networks, "
                        "and recommendation systems in the 2000s. Heuristically tuned so the "
                        "pre-expansion period is viable before the visibility shock is applied."
                    ),
                },
            )
        if scenario == "japan-2070":
            return cls(
                years=91,
                start_calendar_year=1980,
                initial_population=1200,
                initial_age_distribution="japan-1980-stylized",
                location_model="clustered",
                location_cluster_count=12,
                location_cluster_std=0.035,
                initial_radius=0.02,
                max_radius=float(np.sqrt(2.0)),
                action_radius=0.12,
                radius_schedule="shock",
                visibility_expansion_mid_year=2007,
                visibility_expansion_duration_years=7.0,
                reproductive_min_age=20,
                reproductive_max_age=44,
                lifespan_mean=78.0,
                fertility_age_profile="japan-stylized",
                birth_probability=0.22,
                birth_probability_schedule="japan-tfr-stylized",
                carrying_capacity=6000,
                selection_mode="top-k",
                top_k=16,
                selectivity_mean=0.18,
                initial_pair_fraction=0.55,
                pair_duration_mean=18.0,
                pair_duration_std=8.0,
                initial_candidate_pool_multiplier=1.0,
                max_candidate_pool_multiplier=300.0,
                phantom_candidate_mode="sampled",
                phantom_candidate_sample_cap=512,
                actionable_selection_reserve_fraction=0.25,
                metadata={
                    "scenario": "japan-2070",
                    "interpretation": (
                        "Reality-grounded toy calibration for a 1980-2070 Japan-like horizon. "
                        "The symmetric condition is tuned against a population-index shape "
                        "from 1980-2070 before adding aspiration profiles."
                    ),
                },
            )
        raise ValueError(f"Unknown scenario: {scenario}")

    def with_overrides(self, **overrides: Any) -> "SimulationConfig":
        clean_overrides = {key: value for key, value in overrides.items() if value is not None}
        return replace(self, **clean_overrides)


def visibility_radius_for_year(config: SimulationConfig, year: int) -> float:
    """Return the visibility radius for a zero-or-one-based simulation year.

    Schedules are intentionally simple: fixed stays local, global jumps to the
    maximum radius, linear interpolates directly, and sigmoid interpolates with
    an S-shaped transition normalized to hit the configured endpoints.
    """

    schedule = config.radius_schedule
    if schedule == "fixed":
        return float(config.initial_radius)
    if schedule == "global":
        return float(config.max_radius)

    duration = max(config.years, 1)
    progress = float(np.clip(year / duration, 0.0, 1.0))
    span = config.max_radius - config.initial_radius

    if schedule == "linear":
        return float(config.initial_radius + span * progress)

    if schedule == "sigmoid":
        steepness = 10.0
        raw = 1.0 / (1.0 + np.exp(-steepness * (progress - 0.5)))
        low = 1.0 / (1.0 + np.exp(steepness * 0.5))
        high = 1.0 / (1.0 + np.exp(-steepness * 0.5))
        normalized = (raw - low) / (high - low)
        return float(config.initial_radius + span * normalized)

    if schedule == "shock":
        calendar_year = config.start_calendar_year + year - 1
        midpoint = config.visibility_expansion_mid_year
        if midpoint is None:
            midpoint = config.start_calendar_year + config.years // 2
        duration = max(config.visibility_expansion_duration_years, 1.0)
        steepness = 8.0 / duration
        raw = 1.0 / (1.0 + np.exp(-steepness * (calendar_year - midpoint)))
        return float(config.initial_radius + span * raw)

    raise ValueError(f"Unknown radius schedule: {schedule}")


def candidate_pool_multiplier_for_year(config: SimulationConfig, year: int) -> float:
    """Return the perceived candidate-pool multiplier for a year.

    The spatial radius controls which in-simulation agents are visible. This
    multiplier represents extra comparison pressure from feeds, profiles,
    search, and recommendation surfaces where the perceived candidate pool can
    grow much faster than local geography alone.
    """

    start = max(config.initial_candidate_pool_multiplier, 1e-9)
    end = max(config.max_candidate_pool_multiplier, 1e-9)
    if np.isclose(start, end):
        return float(end)

    radius_span = config.max_radius - config.initial_radius
    if np.isclose(radius_span, 0.0):
        progress = 1.0
    else:
        radius = visibility_radius_for_year(config, year)
        progress = float(np.clip((radius - config.initial_radius) / radius_span, 0.0, 1.0))

    return float(start * ((end / start) ** progress))


def resolve_worker_count(config: SimulationConfig, workload_size: int) -> int:
    """Return the worker count for candidate selection.

    `worker_count=None` means auto: use available CPU information, leave one
    logical CPU free when possible, cap the count to avoid thread overhead, and
    stay single-threaded for small eligible pools.
    """

    if config.worker_count is not None and config.worker_count > 0:
        return max(1, int(config.worker_count))
    if workload_size < config.parallel_threshold:
        return 1

    available_cpus = _available_cpu_count()
    if available_cpus <= 2:
        return 1
    return max(1, min(available_cpus - 1, config.max_auto_workers, workload_size))


def _available_cpu_count() -> int:
    if hasattr(os, "sched_getaffinity"):
        try:
            return max(1, len(os.sched_getaffinity(0)))
        except OSError:
            pass
    return max(1, os.cpu_count() or 1)

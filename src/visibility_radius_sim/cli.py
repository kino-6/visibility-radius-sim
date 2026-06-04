from __future__ import annotations

import argparse
import json
from pathlib import Path

from visibility_radius_sim.config import SimulationConfig
from visibility_radius_sim.plotting import plot_metrics, plot_simple_metrics
from visibility_radius_sim.simulation import Simulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="visibility-radius-sim",
        description="Run and plot an abstract visibility-radius agent-based simulation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a simulation and write CSV metrics.")
    run_parser.add_argument(
        "--scenario",
        choices=["baseline", "sns-2000s"],
        default="baseline",
        help="Named scenario preset. CLI parameters override preset values.",
    )
    run_parser.add_argument("--years", type=int, default=None)
    run_parser.add_argument("--start-year", type=int, default=None)
    run_parser.add_argument("--population", type=int, default=None)
    run_parser.add_argument(
        "--location-model",
        choices=["uniform", "clustered"],
        default=None,
        help="Initial spatial distribution.",
    )
    run_parser.add_argument("--location-cluster-count", type=int, default=None)
    run_parser.add_argument("--location-cluster-std", type=float, default=None)
    run_parser.add_argument(
        "--cross-region-pairing",
        choices=["allow", "block"],
        default=None,
        help="Whether agents can form pairs across clustered regions.",
    )
    run_parser.add_argument(
        "--radius-schedule",
        choices=["fixed", "linear", "sigmoid", "shock", "global"],
        default=None,
    )
    run_parser.add_argument("--initial-radius", type=float, default=None)
    run_parser.add_argument("--max-radius", type=float, default=None)
    run_parser.add_argument(
        "--action-radius",
        type=float,
        default=None,
        help="Range in which mutually selected agents can actually form pairs.",
    )
    run_parser.add_argument("--expansion-mid-year", type=int, default=None)
    run_parser.add_argument("--expansion-duration-years", type=float, default=None)
    run_parser.add_argument("--birth-probability", type=float, default=None)
    run_parser.add_argument(
        "--initial-pair-fraction",
        type=float,
        default=None,
        help="Initial share of agents already in persistent pairs.",
    )
    run_parser.add_argument("--pair-duration-mean", type=float, default=None)
    run_parser.add_argument("--pair-duration-std", type=float, default=None)
    run_parser.add_argument("--selectivity", type=float, default=None)
    run_parser.add_argument(
        "--selection-mode",
        choices=["percentile", "top-k"],
        default=None,
        help="Selection rule: percentile keeps a share of visible candidates; top-k keeps a fixed count.",
    )
    run_parser.add_argument("--top-k", type=int, default=None)
    run_parser.add_argument("--initial-candidate-pool-multiplier", type=float, default=None)
    run_parser.add_argument("--max-candidate-pool-multiplier", type=float, default=None)
    run_parser.add_argument(
        "--phantom-candidate-mode",
        choices=["none", "sampled"],
        default=None,
        help="Whether perceived extra candidates can consume selection slots without being pairable.",
    )
    run_parser.add_argument("--phantom-candidate-sample-cap", type=int, default=None)
    run_parser.add_argument(
        "--actionable-selection-reserve-fraction",
        type=float,
        default=None,
        help="Fraction of selection slots reserved for real candidates within action radius.",
    )
    run_parser.add_argument("--mutation-std", type=float, default=None)
    run_parser.add_argument("--lifespan-mean", type=float, default=None)
    run_parser.add_argument("--initial-min-age", type=int, default=None)
    run_parser.add_argument("--initial-max-age", type=int, default=None)
    run_parser.add_argument(
        "--initial-age-distribution",
        choices=["uniform", "japan-1980-stylized"],
        default=None,
        help="Initial age sampler. Scenario presets may use a stylized demographic age pyramid.",
    )
    run_parser.add_argument(
        "--carrying-capacity",
        type=int,
        default=None,
        help="Optional soft population cap for density-dependent birth suppression. Use 0 to disable.",
    )
    run_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Candidate-selection worker count. Omit or use 0 for auto, use 1 for single-threaded.",
    )
    run_parser.add_argument(
        "--max-auto-workers",
        type=int,
        default=None,
        help="Upper bound used by auto worker selection.",
    )
    run_parser.add_argument(
        "--parallel-threshold",
        type=int,
        default=None,
        help="Eligible-agent count below which candidate selection stays single-threaded.",
    )
    run_parser.add_argument("--seed", type=int, default=None)
    run_parser.add_argument("--output", type=Path, default=Path("outputs/run.csv"))
    run_parser.add_argument(
        "--params-output",
        type=Path,
        default=None,
        help="Optional JSON path for the run parameters. Defaults to <output>.params.json.",
    )

    plot_parser = subparsers.add_parser("plot", help="Plot a metrics CSV.")
    plot_parser.add_argument("--input", type=Path, required=True)
    plot_parser.add_argument("--output", type=Path, required=True)
    plot_parser.add_argument(
        "--params",
        type=Path,
        default=None,
        help="Optional parameters JSON. Defaults to <input>.params.json when present.",
    )

    simple_plot_parser = subparsers.add_parser("plot-simple", help="Plot a compact summary dashboard.")
    simple_plot_parser.add_argument("--input", type=Path, required=True)
    simple_plot_parser.add_argument("--output", type=Path, required=True)
    simple_plot_parser.add_argument(
        "--params",
        type=Path,
        default=None,
        help="Optional parameters JSON. Defaults to <input>.params.json when present.",
    )

    return parser


def run_command(args: argparse.Namespace) -> None:
    config = SimulationConfig.for_scenario(args.scenario).with_overrides(
        years=args.years,
        start_calendar_year=args.start_year,
        initial_population=args.population,
        location_model=args.location_model,
        location_cluster_count=args.location_cluster_count,
        location_cluster_std=args.location_cluster_std,
        allow_cross_region_pairing=_normalize_cross_region_pairing(args.cross_region_pairing),
        radius_schedule=args.radius_schedule,
        initial_radius=args.initial_radius,
        max_radius=args.max_radius,
        action_radius=args.action_radius,
        visibility_expansion_mid_year=args.expansion_mid_year,
        visibility_expansion_duration_years=args.expansion_duration_years,
        birth_probability=args.birth_probability,
        initial_pair_fraction=args.initial_pair_fraction,
        pair_duration_mean=args.pair_duration_mean,
        pair_duration_std=args.pair_duration_std,
        selectivity_mean=args.selectivity,
        selection_mode=args.selection_mode,
        top_k=args.top_k,
        initial_candidate_pool_multiplier=args.initial_candidate_pool_multiplier,
        max_candidate_pool_multiplier=args.max_candidate_pool_multiplier,
        phantom_candidate_mode=args.phantom_candidate_mode,
        phantom_candidate_sample_cap=args.phantom_candidate_sample_cap,
        actionable_selection_reserve_fraction=args.actionable_selection_reserve_fraction,
        mutation_std=args.mutation_std,
        lifespan_mean=args.lifespan_mean,
        initial_min_age=args.initial_min_age,
        initial_max_age=args.initial_max_age,
        initial_age_distribution=args.initial_age_distribution,
        carrying_capacity=_normalize_carrying_capacity(args.carrying_capacity),
        worker_count=args.workers,
        max_auto_workers=args.max_auto_workers,
        parallel_threshold=args.parallel_threshold,
        seed=args.seed,
    )
    metrics = Simulation(config).run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.output, index=False)
    params_output = args.params_output or args.output.with_suffix(".params.json")
    params_output.parent.mkdir(parents=True, exist_ok=True)
    params_output.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    print(f"Wrote {len(metrics)} yearly rows to {args.output}")
    print(f"Wrote run parameters to {params_output}")


def plot_command(args: argparse.Namespace) -> None:
    plot_metrics(args.input, args.output, params_path=args.params)
    print(f"Wrote plot to {args.output}")


def plot_simple_command(args: argparse.Namespace) -> None:
    plot_simple_metrics(args.input, args.output, params_path=args.params)
    print(f"Wrote simple plot to {args.output}")


def _normalize_carrying_capacity(value: int | None) -> int | None:
    if value is None:
        return None
    if value <= 0:
        return 0
    return value


def _normalize_cross_region_pairing(value: str | None) -> bool | None:
    if value is None:
        return None
    return value == "allow"


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        run_command(args)
    elif args.command == "plot":
        plot_command(args)
    elif args.command == "plot-simple":
        plot_simple_command(args)
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()

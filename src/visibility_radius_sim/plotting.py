from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


def plot_metrics(
    input_path: str | Path,
    output_path: str | Path,
    params_path: str | Path | None = None,
) -> None:
    input_file = Path(input_path)
    data = pd.read_csv(input_file)
    params = _load_params(input_file, params_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 14), constrained_layout=True)
    grid = fig.add_gridspec(4, 3)

    population_axis = fig.add_subplot(grid[0, :2])
    parameter_axis = fig.add_subplot(grid[0, 2])
    flow_axis = fig.add_subplot(grid[1, 0])
    matching_axis = fig.add_subplot(grid[1, 1])
    coverage_axis = fig.add_subplot(grid[1, 2])
    trait_axis = fig.add_subplot(grid[2, 0])
    concentration_axis = fig.add_subplot(grid[2, 1])
    radius_response_axis = fig.add_subplot(grid[2, 2])
    analysis_axis = fig.add_subplot(grid[3, :2])
    snapshot_axis = fig.add_subplot(grid[3, 2])

    _plot_population(population_axis, data)
    _plot_birth_death_flow(flow_axis, data)
    _plot_matching(matching_axis, data)
    _plot_visibility_coverage(coverage_axis, data)
    _plot_traits(trait_axis, data)
    _plot_concentration(concentration_axis, data)
    _plot_radius_response(radius_response_axis, data)
    _write_parameter_panel(parameter_axis, params, data)
    _write_analysis_panel(analysis_axis, data)
    _write_snapshot_panel(snapshot_axis, data)

    fig.suptitle("Visibility Radius Simulation: Population And Selection Dynamics", fontsize=16)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_simple_metrics(
    input_path: str | Path,
    output_path: str | Path,
    params_path: str | Path | None = None,
) -> None:
    input_file = Path(input_path)
    data = pd.read_csv(input_file)
    params = _load_params(input_file, params_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    _plot_simple_population(axes[0, 0], data)
    _plot_simple_reproduction(axes[0, 1], data)
    _plot_simple_visibility_action(axes[1, 0], data)
    _write_simple_summary(axes[1, 1], data, params)

    title = "Visibility Radius Simulation: Simple View"
    if params.get("metadata", {}).get("scenario"):
        title = f"{title} ({params['metadata']['scenario']})"
    fig.suptitle(title, fontsize=15)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _load_params(input_file: Path, params_path: str | Path | None) -> dict[str, Any]:
    candidates = []
    if params_path is not None:
        candidates.append(Path(params_path))
    candidates.append(input_file.with_suffix(".params.json"))

    for candidate in candidates:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return {}


def _plot_population(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    axis.plot(x, data["population_size"], color="#1f77b4", linewidth=2.4)
    axis.fill_between(x, data["population_size"], color="#1f77b4", alpha=0.12)
    axis.set_title("Population trajectory")
    axis.set_ylabel("Agents alive")
    axis.grid(alpha=0.25)

    radius_axis = axis.twinx()
    radius_axis.plot(
        x,
        data["visibility_radius"],
        color="#9467bd",
        linewidth=1.8,
        linestyle="--",
    )
    radius_axis.set_ylabel("Visibility radius")


def _plot_birth_death_flow(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    axis.plot(x, data["birth_count"], label="Births", color="#2ca02c", linewidth=1.9)
    axis.plot(x, data["death_count"], label="Deaths", color="#d62728", linewidth=1.9)
    axis.bar(
        x,
        data["birth_count"] - data["death_count"],
        label="Births - deaths",
        color="#7f7f7f",
        alpha=0.25,
    )
    axis.set_title("Population flow")
    axis.set_ylabel("Agents per year")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False, fontsize=8)


def _plot_matching(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    axis.plot(
        x,
        data["matched_pair_count"],
        label="Matched pairs",
        color="#ff7f0e",
        linewidth=1.9,
    )
    unmatched_axis = axis.twinx()
    unmatched_axis.plot(
        x,
        data["unmatched_rate"],
        label="Unmatched rate",
        color="#17becf",
        linewidth=1.9,
    )
    axis.set_title("Pair formation pressure")
    axis.set_ylabel("Pairs")
    unmatched_axis.set_ylabel("Unmatched rate")
    axis.grid(alpha=0.25)
    axis.legend(loc="upper left", frameon=False, fontsize=8)
    unmatched_axis.legend(loc="upper right", frameon=False, fontsize=8)


def _plot_visibility_coverage(axis: plt.Axes, data: pd.DataFrame) -> None:
    if "visibility_coverage_rate" not in data:
        axis.axis("off")
        axis.text(0.02, 0.98, "Visibility coverage\nnot available in CSV", va="top", ha="left")
        return

    x = _time_axis(data)
    axis.plot(
        x,
        data["visibility_coverage_rate"],
        label="Observed candidate coverage",
        color="#9467bd",
        linewidth=1.9,
    )
    axis.plot(
        x,
        data["theoretical_area_coverage"],
        label="Area coverage approx.",
        color="#7f7f7f",
        linewidth=1.4,
        linestyle="--",
    )
    candidate_axis = axis.twinx()
    candidate_axis.plot(
        x,
        data["mean_visible_candidate_count"],
        label="Visible candidates",
        color="#2ca02c",
        linewidth=1.7,
        alpha=0.85,
    )
    if "mean_perceived_candidate_count" in data:
        candidate_axis.plot(
            x,
            data["mean_perceived_candidate_count"],
            label="Perceived candidates",
            color="#d62728",
            linewidth=1.5,
            alpha=0.75,
        )
    if "mean_actionable_candidate_count" in data:
        candidate_axis.plot(
            x,
            data["mean_actionable_candidate_count"],
            label="Actionable candidates",
            color="#ff7f0e",
            linewidth=1.5,
            alpha=0.9,
        )
    axis.set_title("Visibility coverage")
    axis.set_ylabel("Coverage share")
    candidate_axis.set_ylabel("Visible candidates")
    axis.grid(alpha=0.25)
    axis.legend(loc="upper left", frameon=False, fontsize=8)
    candidate_axis.legend(loc="lower right", frameon=False, fontsize=8)


def _plot_traits(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    axis.plot(x, data["trait_mean"], label="Trait mean", color="#8c564b", linewidth=1.8)
    axis.plot(
        x,
        data["trait_diversity"],
        label="Trait diversity",
        color="#e377c2",
        linewidth=1.8,
    )
    axis.set_title("Trait distribution")
    axis.set_xlabel(_time_axis_label(data))
    axis.grid(alpha=0.25)
    axis.legend(frameon=False, fontsize=8)


def _plot_concentration(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    axis.plot(
        x,
        data["reproductive_concentration"],
        label="Reproductive concentration",
        color="#bcbd22",
        linewidth=1.8,
    )
    parent_axis = axis.twinx()
    parent_axis.plot(
        x,
        data["effective_parent_count"],
        label="Effective parent count",
        color="#1f77b4",
        linewidth=1.8,
        alpha=0.8,
    )
    axis.set_title("Reproductive concentration")
    axis.set_xlabel(_time_axis_label(data))
    axis.set_ylabel("Gini")
    parent_axis.set_ylabel("Effective parents")
    axis.grid(alpha=0.25)
    axis.legend(loc="upper left", frameon=False, fontsize=8)
    parent_axis.legend(loc="upper right", frameon=False, fontsize=8)


def _plot_radius_response(axis: plt.Axes, data: pd.DataFrame) -> None:
    x_column = "visibility_coverage_rate" if "visibility_coverage_rate" in data else "visibility_radius"
    x_label = "Observed candidate coverage" if x_column == "visibility_coverage_rate" else "Visibility radius"
    series = [
        ("population_size", "Population", "#1f77b4"),
        ("births_per_eligible", "Births/eligible", "#2ca02c"),
        ("mean_selection_acceptance_share", "Accepted share", "#d62728"),
        ("mean_selected_actionable_share", "Selected actionable", "#ff7f0e"),
        ("mean_phantom_selection_share", "Selected phantom", "#9467bd"),
        ("unmatched_rate", "Unmatched", "#17becf"),
        ("reproductive_concentration", "Concentration", "#bcbd22"),
        ("trait_diversity", "Trait diversity", "#e377c2"),
    ]
    for column, label, color in series:
        if column in data:
            axis.plot(data[x_column], _normalize(data[column]), label=label, color=color, linewidth=1.7)
    axis.set_title("Response by radius coverage")
    axis.set_xlabel(x_label)
    axis.set_ylabel("Normalized metric")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False, fontsize=8)


def _plot_simple_population(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    start_population = data["population_size"].iloc[0]
    population_index = data["population_size"] / start_population
    axis.plot(x, population_index, color="#1f77b4", linewidth=2.4, label="Population")
    axis.axhline(0.5, color="#7f7f7f", linewidth=1.0, linestyle=":", label="Half")
    axis.set_title("Population")
    axis.set_ylabel("Index, start = 1.0")
    axis.grid(alpha=0.25)

    if "visibility_coverage_rate" in data:
        radius_axis = axis.twinx()
        radius_axis.plot(
            x,
            _smooth(data["visibility_coverage_rate"]),
            color="#9467bd",
            linestyle="--",
            linewidth=2.0,
            label="Visible share",
        )
        radius_axis.set_ylabel("Visible share")
        radius_axis.set_ylim(-0.02, 1.02)
        axis.legend(loc="upper left", frameon=False, fontsize=8)
        radius_axis.legend(loc="upper right", frameon=False, fontsize=8)
    else:
        axis.legend(frameon=False, fontsize=8)


def _plot_simple_reproduction(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    if "births_per_eligible" in data:
        axis.plot(x, data["births_per_eligible"], color="#2ca02c", linewidth=1.0, alpha=0.25)
        axis.plot(
            x,
            _smooth(data["births_per_eligible"]),
            color="#2ca02c",
            linewidth=2.4,
            label="Births / eligible, 5y avg",
        )
        axis.set_ylabel("Births / eligible")
    else:
        axis.plot(x, data["birth_count"], color="#2ca02c", linewidth=1.0, alpha=0.25)
        axis.plot(x, _smooth(data["birth_count"]), color="#2ca02c", linewidth=2.4, label="Births, 5y avg")
        axis.set_ylabel("Births")
    axis.set_title("Reproduction And Matching")
    axis.grid(alpha=0.25)

    if "unmatched_rate" in data:
        unmatched_axis = axis.twinx()
        unmatched_axis.plot(x, data["unmatched_rate"], color="#17becf", linewidth=1.0, alpha=0.22)
        unmatched_axis.plot(
            x,
            _smooth(data["unmatched_rate"]),
            color="#17becf",
            linewidth=2.1,
            label="Unmatched, 5y avg",
        )
        unmatched_axis.set_ylabel("Unmatched rate")
        unmatched_axis.set_ylim(-0.02, 1.02)
        axis.legend(loc="upper left", frameon=False, fontsize=8)
        unmatched_axis.legend(loc="upper right", frameon=False, fontsize=8)
    else:
        axis.legend(frameon=False, fontsize=8)


def _plot_simple_visibility_action(axis: plt.Axes, data: pd.DataFrame) -> None:
    x = _time_axis(data)
    if "visibility_coverage_rate" in data:
        axis.plot(x, _smooth(data["visibility_coverage_rate"]), color="#9467bd", linewidth=2.2, label="Visible share")
    if "action_coverage_rate" in data:
        axis.plot(x, _smooth(data["action_coverage_rate"]), color="#ff7f0e", linewidth=2.2, label="Actionable share")
    if "mean_selected_actionable_share" in data:
        axis.plot(
            x,
            _smooth(data["mean_selected_actionable_share"]),
            color="#d62728",
            linewidth=2.2,
            label="Selected actionable",
        )
    if "mean_selection_acceptance_share" in data:
        axis.plot(
            x,
            _smooth(data["mean_selection_acceptance_share"]),
            color="#8c564b",
            linewidth=1.8,
            linestyle="--",
            label="Accepted share",
        )
    if "mean_phantom_selection_share" in data:
        axis.plot(
            x,
            _smooth(data["mean_phantom_selection_share"]),
            color="#bcbd22",
            linewidth=2.0,
            linestyle="-.",
            label="Selected phantom",
        )
    axis.set_title("Visibility vs Action")
    axis.set_ylabel("Share")
    axis.set_xlabel(_time_axis_label(data))
    axis.set_ylim(-0.02, 1.02)
    axis.grid(alpha=0.25)
    axis.legend(frameon=False, fontsize=8)


def _write_simple_summary(axis: plt.Axes, data: pd.DataFrame, params: dict[str, Any]) -> None:
    axis.axis("off")
    first = data.iloc[0]
    last = data.iloc[-1]
    peak = data.loc[data["population_size"].idxmax()]
    half_year = _first_half_population_year(data)
    scenario = params.get("metadata", {}).get("scenario", "custom")
    lines = [
        "Summary",
        f"scenario: {scenario}",
        f"start year: {int(first.get('calendar_year', first['year']))}",
        f"final year: {int(last.get('calendar_year', last['year']))}",
        f"start population: {int(first['population_size'])}",
        f"final population: {int(last['population_size'])}",
        f"relative change: {(last['population_size'] / first['population_size'] - 1):+.1%}",
        f"peak population: {int(peak['population_size'])}",
        f"half-pop year: {half_year}",
    ]
    if "births_per_eligible" in data:
        lines.extend(
            [
                f"start births/eligible: {first['births_per_eligible']:.3f}",
                f"final births/eligible: {last['births_per_eligible']:.3f}",
                f"avg births/eligible: {data['births_per_eligible'].mean():.3f}",
            ]
        )
    if "unmatched_rate" in data:
        lines.append(f"avg unmatched: {data['unmatched_rate'].mean():.1%}")
    if "visibility_action_gap" in data:
        lines.extend(
            [
                f"final visibility-action gap: {last['visibility_action_gap']:.1%}",
                f"final selected actionable: {last['mean_selected_actionable_share']:.1%}",
            ]
        )
    if "mean_phantom_selection_share" in data:
        lines.extend(
            [
                f"final selected phantom: {last['mean_phantom_selection_share']:.1%}",
                f"avg selected phantom: {data['mean_phantom_selection_share'].mean():.1%}",
            ]
        )
    if "candidate_pool_multiplier" in data:
        lines.append(f"final candidate multiplier: {last['candidate_pool_multiplier']:.1f}x")
    axis.text(0.02, 0.98, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=11)


def _write_parameter_panel(axis: plt.Axes, params: dict[str, Any], data: pd.DataFrame) -> None:
    axis.axis("off")
    lines = ["Run parameters"]
    if params:
        keys = [
            "metadata",
            "years",
            "start_calendar_year",
            "initial_population",
            "location_model",
            "location_cluster_count",
            "location_cluster_std",
            "radius_schedule",
            "visibility_expansion_mid_year",
            "visibility_expansion_duration_years",
            "initial_radius",
            "max_radius",
            "action_radius",
            "birth_probability",
            "carrying_capacity",
            "selection_mode",
            "top_k",
            "initial_candidate_pool_multiplier",
            "max_candidate_pool_multiplier",
            "phantom_candidate_mode",
            "phantom_candidate_sample_cap",
            "actionable_selection_reserve_fraction",
            "selectivity_mean",
            "mutation_std",
            "lifespan_mean",
            "initial_min_age",
            "initial_max_age",
            "worker_count",
            "max_auto_workers",
            "parallel_threshold",
            "seed",
        ]
        for key in keys:
            if key in params:
                lines.append(f"{key}: {_format_value(params[key])}")
    else:
        lines.extend(
            [
                f"years: {int(data['year'].max())}",
                "parameter JSON not found",
                "run again to generate <output>.params.json",
            ]
        )
    axis.text(0.02, 0.98, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=10)


def _write_analysis_panel(axis: plt.Axes, data: pd.DataFrame) -> None:
    axis.axis("off")
    first = data.iloc[0]
    last = data.iloc[-1]
    peak = data.loc[data["population_size"].idxmax()]
    trough = data.loc[data["population_size"].idxmin()]
    total_births = int(data["birth_count"].sum())
    total_deaths = int(data["death_count"].sum())
    net = total_births - total_deaths
    growth = _safe_ratio(last["population_size"] - first["population_size"], first["population_size"])

    lines = [
        "Trajectory analysis",
        f"start year: {int(first.get('calendar_year', first['year']))}",
        f"final year: {int(last.get('calendar_year', last['year']))}",
        f"start population: {int(first['population_size'])}",
        f"final population: {int(last['population_size'])}",
        f"net change after year 1: {last['population_size'] - first['population_size']:+.0f}",
        f"relative change: {growth:+.1%}",
        f"peak: {int(peak['population_size'])} at year {int(peak['year'])}",
        f"trough: {int(trough['population_size'])} at year {int(trough['year'])}",
        f"total births: {total_births}",
        f"total deaths: {total_deaths}",
        f"births - deaths: {net:+d}",
        f"avg unmatched rate: {data['unmatched_rate'].mean():.2%}",
        f"avg concentration: {data['reproductive_concentration'].mean():.3f}",
    ]
    if "births_per_eligible" in data:
        lines.extend(
            [
                f"start births/eligible: {first['births_per_eligible']:.3f}",
                f"final births/eligible: {last['births_per_eligible']:.3f}",
                f"avg births/eligible: {data['births_per_eligible'].mean():.3f}",
            ]
        )
    if "visibility_coverage_rate" in data:
        lines.extend(
            [
                f"start coverage: {data['visibility_coverage_rate'].iloc[0]:.2%}",
                f"final coverage: {data['visibility_coverage_rate'].iloc[-1]:.2%}",
                f"avg visible candidates: {data['mean_visible_candidate_count'].mean():.1f}",
            ]
        )
    if "mean_perceived_candidate_count" in data:
        lines.extend(
            [
                f"avg perceived candidates: {data['mean_perceived_candidate_count'].mean():.1f}",
                f"avg accepted share: {data['mean_selection_acceptance_share'].mean():.4f}",
            ]
        )
    if "mean_actionable_candidate_count" in data:
        lines.extend(
            [
                f"avg actionable candidates: {data['mean_actionable_candidate_count'].mean():.1f}",
                f"avg visibility-action gap: {data['visibility_action_gap'].mean():.2%}",
                f"avg selected actionable: {data['mean_selected_actionable_share'].mean():.2%}",
            ]
        )
    if "mean_phantom_selection_share" in data:
        lines.extend(
            [
                f"avg phantom candidates: {data['mean_phantom_candidate_count'].mean():.1f}",
                f"avg sampled phantom: {data['mean_sampled_phantom_candidate_count'].mean():.1f}",
                f"avg selected phantom: {data['mean_phantom_selection_share'].mean():.2%}",
            ]
        )
    if "effective_birth_probability" in data:
        lines.append(f"avg effective birth p: {data['effective_birth_probability'].mean():.3f}")
    if "selection_worker_count" in data:
        lines.append(f"worker count range: {data['selection_worker_count'].min():.0f}-{data['selection_worker_count'].max():.0f}")
    axis.text(0.02, 0.98, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=10)


def _write_snapshot_panel(axis: plt.Axes, data: pd.DataFrame) -> None:
    axis.axis("off")
    last = data.iloc[-1]
    lines = [
        "Final-year snapshot",
        f"year: {int(last['year'])}",
        f"calendar year: {int(last.get('calendar_year', last['year']))}",
        f"population: {int(last['population_size'])}",
        f"births: {int(last['birth_count'])}",
        f"births/eligible: {last.get('births_per_eligible', 0.0):.3f}",
        f"births/population: {last.get('births_per_population', 0.0):.3f}",
        f"deaths: {int(last['death_count'])}",
        f"matched pairs: {int(last['matched_pair_count'])}",
        f"unmatched rate: {last['unmatched_rate']:.2%}",
        f"trait mean: {last['trait_mean']:.3f}",
        f"trait variance: {last['trait_variance']:.3f}",
        f"trait diversity: {last['trait_diversity']:.3f}",
        f"concentration: {last['reproductive_concentration']:.3f}",
        f"effective parents: {last['effective_parent_count']:.1f}",
        f"visibility radius: {last['visibility_radius']:.3f}",
    ]
    if "visibility_coverage_rate" in data:
        lines.extend(
            [
                f"coverage rate: {last['visibility_coverage_rate']:.2%}",
                f"visible candidates: {last['mean_visible_candidate_count']:.1f}",
            ]
        )
    if "mean_perceived_candidate_count" in data:
        lines.extend(
            [
                f"perceived candidates: {last['mean_perceived_candidate_count']:.1f}",
                f"selection quota: {last['mean_selection_quota']:.1f}",
                f"accepted share: {last['mean_selection_acceptance_share']:.4f}",
                f"candidate multiplier: {last['candidate_pool_multiplier']:.1f}",
            ]
        )
    if "mean_actionable_candidate_count" in data:
        lines.extend(
            [
                f"actionable candidates: {last['mean_actionable_candidate_count']:.1f}",
                f"visibility-action gap: {last['visibility_action_gap']:.2%}",
                f"selected actionable: {last['mean_selected_actionable_share']:.2%}",
                f"blocked mutual pairs: {last['blocked_mutual_pair_count']:.0f}",
                f"action radius: {last['action_radius']:.3f}",
            ]
        )
    if "mean_phantom_selection_share" in data:
        lines.extend(
            [
                f"phantom candidates: {last['mean_phantom_candidate_count']:.1f}",
                f"sampled phantom: {last['mean_sampled_phantom_candidate_count']:.1f}",
                f"selected phantom: {last['mean_phantom_selection_share']:.2%}",
            ]
        )
    if "effective_birth_probability" in data:
        lines.append(f"effective birth p: {last['effective_birth_probability']:.3f}")
    if "selection_worker_count" in data:
        lines.append(f"selection workers: {last['selection_worker_count']:.0f}")
    axis.text(0.02, 0.98, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=10)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, dict):
        return value.get("scenario", "present")
    return str(value)


def _normalize(series: pd.Series) -> pd.Series:
    minimum = series.min()
    span = series.max() - minimum
    if span == 0:
        return series * 0.0
    return (series - minimum) / span


def _smooth(series: pd.Series, window: int = 5) -> pd.Series:
    return series.rolling(window=window, center=True, min_periods=1).mean()


def _first_half_population_year(data: pd.DataFrame) -> str:
    half_population = data["population_size"].iloc[0] / 2
    matches = data[data["population_size"] <= half_population]
    if matches.empty:
        return "not reached"
    row = matches.iloc[0]
    year = row.get("calendar_year", row["year"])
    return str(int(year))


def _time_axis(data: pd.DataFrame) -> pd.Series:
    if "calendar_year" in data:
        return data["calendar_year"]
    return data["year"]


def _time_axis_label(data: pd.DataFrame) -> str:
    if "calendar_year" in data:
        return "Calendar year"
    return "Year"

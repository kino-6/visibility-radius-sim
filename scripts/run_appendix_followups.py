from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from visibility_radius_sim.config import SimulationConfig
from visibility_radius_sim.simulation import Simulation


OUTPUT_DIR = Path("outputs/appendix_followups")
DOCS_RESULT_PATH = Path("docs/appendix_followups_results.md")
PAPER_NOTE_PATH = Path("paper/notes/appendix_followups_report.md")

YEARS = 180
POPULATION = 1200
SEEDS = (0, 1, 2)
LATE_WINDOW = 30


@dataclass(frozen=True)
class Scenario:
    experiment: str
    variant: str
    label: str
    overrides: dict[str, Any]
    metadata: dict[str, Any]
    seeds: tuple[int, ...] = SEEDS
    adaptive: dict[str, Any] | None = None


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAPER_NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)

    scenarios = build_scenarios()
    raw_frames: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []

    for index, scenario in enumerate(scenarios, start=1):
        print(f"[{index:03d}/{len(scenarios):03d}] {scenario.experiment}: {scenario.label}", flush=True)
        for seed in scenario.seeds:
            config = base_config(seed).with_overrides(**scenario.overrides)
            if scenario.adaptive is None:
                frame = Simulation(config).run()
            else:
                frame = run_adaptive_simulation(config, scenario.adaptive)
            frame = annotate_frame(frame, scenario, seed)
            raw_frames.append(frame)
            summaries.append(summarize_run(frame, scenario, seed))

    raw = pd.concat(raw_frames, ignore_index=True)
    summary = pd.DataFrame(summaries)
    grouped = summarize_groups(summary)

    raw_path = OUTPUT_DIR / "appendix_followups_raw.csv"
    run_summary_path = OUTPUT_DIR / "appendix_followups_run_summary.csv"
    grouped_path = OUTPUT_DIR / "appendix_followups_summary.csv"
    raw.to_csv(raw_path, index=False)
    summary.to_csv(run_summary_path, index=False)
    grouped.to_csv(grouped_path, index=False)

    plot_overview(grouped, OUTPUT_DIR / "appendix_followups_overview.png")
    for experiment in grouped["experiment"].drop_duplicates():
        plot_experiment(raw, grouped, experiment, OUTPUT_DIR / f"{experiment}_summary.png")

    report = build_report(grouped)
    report_path = OUTPUT_DIR / "appendix_followups_report.md"
    report_path.write_text(report, encoding="utf-8")
    DOCS_RESULT_PATH.write_text(report, encoding="utf-8")
    PAPER_NOTE_PATH.write_text(report, encoding="utf-8")

    print(f"wrote {raw_path}")
    print(f"wrote {grouped_path}")
    print(f"wrote {report_path}")
    print(f"wrote {DOCS_RESULT_PATH}")
    print(f"wrote {PAPER_NOTE_PATH}")


def base_config(seed: int) -> SimulationConfig:
    return SimulationConfig.for_scenario("sns-2000s").with_overrides(
        years=YEARS,
        initial_population=POPULATION,
        carrying_capacity=4500,
        seed=seed,
        worker_count=None,
        max_auto_workers=8,
        parallel_threshold=200,
        metrics_precision=6,
    )


def build_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    scenarios.extend(radius_alone_scenarios())
    scenarios.extend(selection_mode_scenarios())
    scenarios.extend(candidate_multiplier_scenarios())
    scenarios.extend(action_gap_scenarios())
    scenarios.extend(reserve_threshold_robustness_scenarios())
    scenarios.extend(cultural_overconstraint_scenarios())
    scenarios.extend(institutional_learning_scenarios())
    return scenarios


def radius_alone_scenarios() -> list[Scenario]:
    return [
        Scenario(
            "a_radius_alone",
            "local_visible_local_action",
            "Local visibility, local action",
            {
                "radius_schedule": "fixed",
                "initial_radius": 0.12,
                "max_radius": 0.12,
                "action_radius": 0.12,
                "max_candidate_pool_multiplier": 1.0,
                "phantom_candidate_mode": "none",
                "selection_mode": "top-k",
                "top_k": 16,
            },
            {"condition": "radius_aligned"},
        ),
        Scenario(
            "a_radius_alone",
            "global_visible_global_action",
            "Global visibility, global action",
            {
                "radius_schedule": "global",
                "action_radius": float(np.sqrt(2.0)),
                "max_candidate_pool_multiplier": 1.0,
                "phantom_candidate_mode": "none",
                "selection_mode": "top-k",
                "top_k": 16,
            },
            {"condition": "radius_aligned_global"},
        ),
        Scenario(
            "a_radius_alone",
            "global_visible_local_action_no_phantom",
            "Global visibility, local action, no phantom",
            {
                "radius_schedule": "global",
                "action_radius": 0.12,
                "max_candidate_pool_multiplier": 1.0,
                "phantom_candidate_mode": "none",
                "selection_mode": "top-k",
                "top_k": 16,
            },
            {"condition": "action_gap_only"},
        ),
        Scenario(
            "a_radius_alone",
            "full_sns_phantom",
            "Full SNS shock with phantom",
            {},
            {"condition": "full_mechanism"},
        ),
    ]


def selection_mode_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    for top_k in (8, 16, 32):
        scenarios.append(
            Scenario(
                "b_selection_mode",
                f"top_k_{top_k}",
                f"Top-k {top_k}",
                {"selection_mode": "top-k", "top_k": top_k},
                {"selection_mode": "top-k", "top_k": top_k},
            )
        )
    for selectivity in (0.02, 0.08, 0.18):
        scenarios.append(
            Scenario(
                "b_selection_mode",
                f"percentile_{selectivity:.2f}".replace(".", "_"),
                f"Percentile {selectivity:.2f}",
                {
                    "selection_mode": "percentile",
                    "selectivity_mean": selectivity,
                    "selectivity_std": min(0.02, selectivity / 2),
                },
                {"selection_mode": "percentile", "selectivity_mean": selectivity},
            )
        )
    return scenarios


def candidate_multiplier_scenarios() -> list[Scenario]:
    return [
        Scenario(
            "c_candidate_multiplier",
            f"multiplier_{multiplier:g}x".replace(".", "_"),
            f"{multiplier:g}x perceived pool",
            {
                "max_candidate_pool_multiplier": float(multiplier),
                "phantom_candidate_mode": "none" if multiplier == 1 else "sampled",
                "phantom_candidate_sample_cap": 512,
            },
            {"max_candidate_pool_multiplier": multiplier},
        )
        for multiplier in (1, 10, 30, 100, 300, 1000)
    ]


def action_gap_scenarios() -> list[Scenario]:
    radii = (0.03, 0.06, 0.12, 0.24, 0.48, float(np.sqrt(2.0)))
    return [
        Scenario(
            "d_actionability_gap",
            f"action_radius_{radius:.3f}".replace(".", "_"),
            "Global visibility, action radius " + ("global" if radius > 1 else f"{radius:.2f}"),
            {"action_radius": radius},
            {"action_radius": radius},
        )
        for radius in radii
    ]


def reserve_threshold_robustness_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    slot_options = (0, 1, 2, 4, 8, 16, 32)
    for top_k in (8, 16, 32, 64):
        for slots in slot_options:
            if slots > top_k:
                continue
            reserve_fraction = 0.0 if top_k <= 0 else slots / top_k
            scenarios.append(
                Scenario(
                    "e_reserve_threshold_robustness",
                    f"topk_{top_k}_slots_{slots}",
                    f"top-k {top_k}, protected slots {slots}",
                    {
                        "selection_mode": "top-k",
                        "top_k": top_k,
                        "actionable_selection_reserve_fraction": reserve_fraction,
                    },
                    {"top_k": top_k, "protected_slots": slots, "reserve_fraction": reserve_fraction},
                    seeds=SEEDS,
                )
            )
    return scenarios


def cultural_overconstraint_scenarios() -> list[Scenario]:
    fractions = (0.0, 0.0625, 0.125, 0.25, 0.5, 0.75, 0.9, 1.0)
    return [
        Scenario(
            "f_cultural_overconstraint",
            f"reserve_{fraction:.4f}".replace(".", "_"),
            f"Reserve fraction {fraction:.4f}",
            {"actionable_selection_reserve_fraction": fraction},
            {"reserve_fraction": fraction},
        )
        for fraction in fractions
    ]


def institutional_learning_scenarios() -> list[Scenario]:
    return [
        Scenario(
            "g_institutional_learning",
            "no_learning",
            "No learning",
            {"actionable_selection_reserve_fraction": 0.0},
            {"learning": "none"},
        ),
        Scenario(
            "g_institutional_learning",
            "slow_learning",
            "Slow regional learning",
            {"actionable_selection_reserve_fraction": 0.0},
            {"learning": "slow"},
            adaptive={"learning_rate": 0.0625, "decline_threshold": 0.03, "interval": 10, "max_reserve": 0.5},
        ),
        Scenario(
            "g_institutional_learning",
            "fast_learning",
            "Fast regional learning",
            {"actionable_selection_reserve_fraction": 0.0},
            {"learning": "fast"},
            adaptive={"learning_rate": 0.125, "decline_threshold": 0.02, "interval": 10, "max_reserve": 0.75},
        ),
        Scenario(
            "g_institutional_learning",
            "preadapted_025",
            "Preadapted reserve 0.25",
            {"actionable_selection_reserve_fraction": 0.25},
            {"learning": "preadapted", "reserve_fraction": 0.25},
        ),
    ]


class AdaptiveReserveSimulation(Simulation):
    def __init__(self, config: SimulationConfig, *, start_reserve: float, max_reserve: float):
        super().__init__(config)
        region_count = max(1, config.location_cluster_count)
        self.region_reserves = np.full(region_count, start_reserve, dtype=float)
        self.max_reserve = max_reserve

    def _actionable_reserve_fraction_for_agent(self, agent):  # type: ignore[override]
        if agent is not None and agent.region_id is not None:
            region_id = int(agent.region_id)
            if 0 <= region_id < len(self.region_reserves):
                return float(np.clip(self.region_reserves[region_id], 0.0, self.max_reserve))
        return 0.0

    def region_population_counts(self) -> np.ndarray:
        counts = np.zeros_like(self.region_reserves, dtype=float)
        for agent in self.agents:
            if not agent.alive or agent.region_id is None:
                continue
            region_id = int(agent.region_id)
            if 0 <= region_id < len(counts):
                counts[region_id] += 1
        return counts

    def adapt(self, previous_counts: np.ndarray, current_counts: np.ndarray, *, learning_rate: float, decline_threshold: float) -> None:
        decline_cutoff = previous_counts * (1.0 - decline_threshold)
        declining = current_counts < decline_cutoff
        self.region_reserves[declining] = np.minimum(
            self.max_reserve,
            self.region_reserves[declining] + learning_rate,
        )


def run_adaptive_simulation(config: SimulationConfig, adaptive: dict[str, Any]) -> pd.DataFrame:
    sim = AdaptiveReserveSimulation(
        config,
        start_reserve=float(adaptive.get("start_reserve", 0.0)),
        max_reserve=float(adaptive.get("max_reserve", 0.75)),
    )
    interval = int(adaptive.get("interval", 10))
    learning_rate = float(adaptive.get("learning_rate", 0.0625))
    decline_threshold = float(adaptive.get("decline_threshold", 0.03))
    previous_counts = sim.region_population_counts()
    rows: list[dict[str, Any]] = []
    for year in range(1, config.years + 1):
        row = sim.step(year)
        row["mean_region_reserve"] = round(float(np.mean(sim.region_reserves)), config.metrics_precision)
        row["max_region_reserve"] = round(float(np.max(sim.region_reserves)), config.metrics_precision)
        row["min_region_reserve"] = round(float(np.min(sim.region_reserves)), config.metrics_precision)
        rows.append(row)
        if year % interval == 0:
            current_counts = sim.region_population_counts()
            sim.adapt(
                previous_counts,
                current_counts,
                learning_rate=learning_rate,
                decline_threshold=decline_threshold,
            )
            previous_counts = current_counts
    return pd.DataFrame(rows)


def annotate_frame(frame: pd.DataFrame, scenario: Scenario, seed: int) -> pd.DataFrame:
    annotated = frame.copy()
    annotated.insert(0, "experiment", scenario.experiment)
    annotated.insert(1, "variant", scenario.variant)
    annotated.insert(2, "label", scenario.label)
    annotated.insert(3, "seed", seed)
    for key, value in scenario.metadata.items():
        annotated[key] = value
    return annotated


def summarize_run(frame: pd.DataFrame, scenario: Scenario, seed: int) -> dict[str, Any]:
    late = frame.tail(min(LATE_WINDOW, len(frame)))
    start_population = float(frame["population_size"].iloc[0])
    final_population = float(frame["population_size"].iloc[-1])
    below_half = frame.loc[frame["population_size"] <= 0.5 * start_population, "calendar_year"]
    row: dict[str, Any] = {
        "experiment": scenario.experiment,
        "variant": scenario.variant,
        "label": scenario.label,
        "seed": seed,
        "start_population": start_population,
        "peak_population": float(frame["population_size"].max()),
        "peak_year": int(frame.loc[frame["population_size"].idxmax(), "calendar_year"]),
        "final_population": final_population,
        "final_ratio": safe_div(final_population, start_population),
        "min_ratio": safe_div(float(frame["population_size"].min()), start_population),
        "half_population_year": None if below_half.empty else int(below_half.iloc[0]),
        "late_unmatched_mean": float(late["unmatched_rate"].mean()),
        "late_births_per_eligible_mean": float(late["births_per_eligible"].mean()),
        "late_selected_actionable_mean": float(late["mean_selected_actionable_share"].mean()),
        "late_phantom_share_mean": float(late["mean_phantom_selection_share"].mean()),
        "late_visibility_action_gap_mean": float(late["visibility_action_gap"].mean()),
        "late_action_coverage_mean": float(late["action_coverage_rate"].mean()),
        "late_candidate_pool_multiplier_mean": float(late["candidate_pool_multiplier"].mean()),
        "late_mean_selection_quota": float(late["mean_selection_quota"].mean()),
    }
    for key, value in scenario.metadata.items():
        row[key] = value
    if "mean_region_reserve" in frame.columns:
        row["final_mean_region_reserve"] = float(frame["mean_region_reserve"].iloc[-1])
        row["final_max_region_reserve"] = float(frame["max_region_reserve"].iloc[-1])
    return row


def summarize_groups(summary: pd.DataFrame) -> pd.DataFrame:
    meta_columns = [
        column
        for column in summary.columns
        if column
        not in {
            "seed",
            "start_population",
            "peak_population",
            "peak_year",
            "final_population",
            "final_ratio",
            "min_ratio",
            "half_population_year",
            "late_unmatched_mean",
            "late_births_per_eligible_mean",
            "late_selected_actionable_mean",
            "late_phantom_share_mean",
            "late_visibility_action_gap_mean",
            "late_action_coverage_mean",
            "late_candidate_pool_multiplier_mean",
            "late_mean_selection_quota",
            "final_mean_region_reserve",
            "final_max_region_reserve",
        }
    ]
    rows: list[dict[str, Any]] = []
    for keys, group in summary.groupby(meta_columns, dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(meta_columns, keys, strict=True))
        row.update(
            {
                "seed_count": int(group["seed"].nunique()),
                "final_ratio_mean": float(group["final_ratio"].mean()),
                "final_ratio_min": float(group["final_ratio"].min()),
                "final_ratio_max": float(group["final_ratio"].max()),
                "min_ratio_mean": float(group["min_ratio"].mean()),
                "late_unmatched_mean": float(group["late_unmatched_mean"].mean()),
                "late_births_per_eligible_mean": float(group["late_births_per_eligible_mean"].mean()),
                "late_selected_actionable_mean": float(group["late_selected_actionable_mean"].mean()),
                "late_phantom_share_mean": float(group["late_phantom_share_mean"].mean()),
                "late_visibility_action_gap_mean": float(group["late_visibility_action_gap_mean"].mean()),
                "late_action_coverage_mean": float(group["late_action_coverage_mean"].mean()),
                "late_candidate_pool_multiplier_mean": float(group["late_candidate_pool_multiplier_mean"].mean()),
                "late_mean_selection_quota": float(group["late_mean_selection_quota"].mean()),
            }
        )
        if "final_mean_region_reserve" in group:
            row["final_mean_region_reserve"] = float(group["final_mean_region_reserve"].dropna().mean())
            row["final_max_region_reserve"] = float(group["final_max_region_reserve"].dropna().mean())
        rows.append(row)
    return pd.DataFrame(rows)


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0.0:
        return 0.0
    return float(numerator / denominator)


def plot_overview(summary: pd.DataFrame, output_path: Path) -> None:
    experiments = list(summary["experiment"].drop_duplicates())
    fig, axes = plt.subplots(4, 2, figsize=(18, 22), constrained_layout=True)
    axes_flat = axes.ravel()
    for axis, experiment in zip(axes_flat, experiments, strict=False):
        subset = summary[summary["experiment"] == experiment].copy()
        axis.bar(range(len(subset)), subset["final_ratio_mean"], color="#1f77b4", alpha=0.85)
        axis.errorbar(
            range(len(subset)),
            subset["final_ratio_mean"],
            yerr=[
                subset["final_ratio_mean"] - subset["final_ratio_min"],
                subset["final_ratio_max"] - subset["final_ratio_mean"],
            ],
            fmt="none",
            ecolor="#333333",
            alpha=0.7,
            capsize=2,
        )
        axis.axhline(0.5, color="#777777", linewidth=1, linestyle=":")
        axis.set_title(experiment)
        axis.set_ylabel("Final population ratio")
        axis.set_xticks(range(len(subset)))
        axis.set_xticklabels(subset["label"], rotation=60, ha="right", fontsize=8)
        axis.grid(axis="y", alpha=0.25)
    for axis in axes_flat[len(experiments) :]:
        axis.axis("off")
    fig.suptitle("Appendix Follow-Up Experiments", fontsize=18)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_experiment(raw: pd.DataFrame, summary: pd.DataFrame, experiment: str, output_path: Path) -> None:
    raw_subset = raw[raw["experiment"] == experiment]
    summary_subset = summary[summary["experiment"] == experiment].copy()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)

    axes[0, 0].bar(range(len(summary_subset)), summary_subset["final_ratio_mean"], color="#1f77b4")
    axes[0, 0].axhline(0.5, color="#777777", linestyle=":", linewidth=1)
    axes[0, 0].set_title("Final population ratio")
    axes[0, 0].set_xticks(range(len(summary_subset)))
    axes[0, 0].set_xticklabels(summary_subset["label"], rotation=60, ha="right", fontsize=8)
    axes[0, 0].grid(axis="y", alpha=0.25)

    for label, group in raw_subset.groupby("label", sort=False):
        by_year = group.groupby("calendar_year", as_index=False)["population_size"].mean()
        start = by_year["population_size"].iloc[0]
        axes[0, 1].plot(by_year["calendar_year"], by_year["population_size"] / start, label=label, linewidth=1.8)
    axes[0, 1].axhline(0.5, color="#777777", linestyle=":", linewidth=1)
    axes[0, 1].set_title("Mean population trajectory")
    axes[0, 1].set_ylabel("Index")
    axes[0, 1].grid(alpha=0.25)
    axes[0, 1].legend(fontsize=7, frameon=False)

    x = range(len(summary_subset))
    axes[1, 0].plot(x, summary_subset["late_selected_actionable_mean"], marker="o", label="Selected actionable")
    axes[1, 0].plot(x, summary_subset["late_phantom_share_mean"], marker="o", label="Selected phantom")
    axes[1, 0].set_title("Late attention composition")
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(summary_subset["label"], rotation=60, ha="right", fontsize=8)
    axes[1, 0].grid(alpha=0.25)
    axes[1, 0].legend(frameon=False)

    axes[1, 1].scatter(
        summary_subset["late_visibility_action_gap_mean"],
        summary_subset["final_ratio_mean"],
        color="#d62728",
        s=60,
    )
    for _, row in summary_subset.iterrows():
        axes[1, 1].annotate(str(row["variant"]), (row["late_visibility_action_gap_mean"], row["final_ratio_mean"]), fontsize=7)
    axes[1, 1].set_title("Final ratio vs visibility/action gap")
    axes[1, 1].set_xlabel("Late visibility/action gap")
    axes[1, 1].set_ylabel("Final population ratio")
    axes[1, 1].grid(alpha=0.25)

    fig.suptitle(experiment, fontsize=16)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def build_report(summary: pd.DataFrame) -> str:
    lines = [
        "# Appendix Follow-Up Results",
        "",
        "This report summarizes seven follow-up experiments that test whether the",
        "working-paper mechanism is better described as radius expansion itself, or",
        "as an actionability gap interacting with bounded attention.",
        "",
        "## Output Files",
        "",
        "- `outputs/appendix_followups/appendix_followups_raw.csv`",
        "- `outputs/appendix_followups/appendix_followups_run_summary.csv`",
        "- `outputs/appendix_followups/appendix_followups_summary.csv`",
        "- `outputs/appendix_followups/appendix_followups_overview.png`",
        "",
    ]
    for experiment in summary["experiment"].drop_duplicates():
        subset = summary[summary["experiment"] == experiment].copy()
        display = subset[
            [
                "label",
                "seed_count",
                "final_ratio_mean",
                "final_ratio_min",
                "final_ratio_max",
                "late_births_per_eligible_mean",
                "late_selected_actionable_mean",
                "late_phantom_share_mean",
                "late_visibility_action_gap_mean",
            ]
        ].copy()
        for column in display.columns:
            if column not in {"label", "seed_count"}:
                display[column] = display[column].map(lambda value: f"{float(value):.3f}")
        lines.extend(
            [
                f"## {experiment}",
                "",
                dataframe_to_markdown(display),
                "",
                f"Figure: `outputs/appendix_followups/{experiment}_summary.png`",
                "",
            ]
        )
    lines.extend(
        [
            "## Short Interpretation",
            "",
            "These follow-ups should be read as robustness checks rather than final",
            "estimates. The key question is whether the qualitative pattern survives",
            "changes in selection mode, candidate-pool multiplier, action radius,",
            "top-k capacity, reserve strength, and region-level learning.",
            "",
        ]
    )
    return "\n".join(lines)


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    rows = [
        "| " + " | ".join(str(column) for column in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(rows)


if __name__ == "__main__":
    main()

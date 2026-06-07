from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


OUTPUT_DIR = Path("outputs/cross_country_calibration")
RAW_PATH = OUTPUT_DIR / "hypothesis_raw.csv"
OBSERVED_PATH = OUTPUT_DIR / "observed_population_fertility.csv"
TRAJECTORY_FIGURE = OUTPUT_DIR / "cross_country_scenario_trajectories.png"
MECHANISM_FIGURE = OUTPUT_DIR / "cross_country_mechanism_metrics.png"


REGION_ORDER = ("usa", "gbr", "ssf")
REGION_LABELS = {
    "usa": "United States",
    "gbr": "United Kingdom",
    "ssf": "Sub-Saharan Africa",
}
SCENARIOS = (
    ("local_actionable", "symmetric", "Calibrated local base", "#1f2937", "-"),
    ("sns_expansion", "symmetric", "SNS-like, symmetric", "#2563eb", "-"),
    ("sns_expansion", "b_heavy_mixed", "SNS-like, compound-heavy", "#dc2626", "-"),
    ("global_from_start", "b_heavy_mixed", "Global, compound-heavy", "#7c3aed", "--"),
)


def main() -> None:
    raw = pd.read_csv(RAW_PATH)
    observed = pd.read_csv(OBSERVED_PATH)
    plot_trajectories(raw, observed, TRAJECTORY_FIGURE)
    plot_mechanisms(raw, MECHANISM_FIGURE)
    print(f"wrote {TRAJECTORY_FIGURE}")
    print(f"wrote {MECHANISM_FIGURE}")


def plot_trajectories(raw: pd.DataFrame, observed: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), sharey=False)
    for axis, region in zip(axes, REGION_ORDER, strict=True):
        observed_region = observed.loc[observed["region"] == region]
        axis.plot(
            observed_region["calendar_year"],
            observed_region["actual_population_index"],
            color="black",
            linewidth=2.6,
            label="Observed",
        )
        for visibility, aspiration, label, color, linestyle in SCENARIOS:
            scenario = raw.loc[
                (raw["region"] == region)
                & (raw["visibility_condition"] == visibility)
                & (raw["aspiration_profile"] == aspiration)
            ]
            mean_line = scenario.groupby("calendar_year", as_index=False)["population_index"].mean()
            axis.plot(
                mean_line["calendar_year"],
                mean_line["population_index"],
                color=color,
                linestyle=linestyle,
                linewidth=2.0,
                label=label,
            )
        axis.set_title(REGION_LABELS[region])
        axis.set_xlabel("Year")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Population index, 1980=1.0")
    axes[0].legend(loc="best", fontsize=8)
    fig.suptitle("Observed line, calibrated base, and visibility x aspiration scenarios")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_mechanisms(raw: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), sharex=True)
    selected = (
        ("local_actionable", "symmetric", "Local symmetric", "#1f2937", "-"),
        ("sns_expansion", "symmetric", "SNS symmetric", "#2563eb", "-"),
        ("sns_expansion", "b_heavy_mixed", "SNS compound-heavy", "#dc2626", "-"),
        ("global_from_start", "b_heavy_mixed", "Global compound-heavy", "#7c3aed", "--"),
    )
    for row, region in enumerate(REGION_ORDER):
        for visibility, aspiration, label, color, linestyle in selected:
            scenario = raw.loc[
                (raw["region"] == region)
                & (raw["visibility_condition"] == visibility)
                & (raw["aspiration_profile"] == aspiration)
            ]
            mean_line = scenario.groupby("calendar_year", as_index=False).agg(
                births_per_population=("births_per_population", "mean"),
                unmatched_rate=("unmatched_rate", "mean"),
            )
            axes[row, 0].plot(
                mean_line["calendar_year"],
                mean_line["births_per_population"],
                color=color,
                linestyle=linestyle,
                linewidth=1.8,
                label=label,
            )
            axes[row, 1].plot(
                mean_line["calendar_year"],
                mean_line["unmatched_rate"],
                color=color,
                linestyle=linestyle,
                linewidth=1.8,
                label=label,
            )
        axes[row, 0].set_ylabel(REGION_LABELS[region])
        axes[row, 0].grid(alpha=0.25)
        axes[row, 1].grid(alpha=0.25)
    axes[0, 0].set_title("Births per population")
    axes[0, 1].set_title("Unmatched rate")
    axes[-1, 0].set_xlabel("Year")
    axes[-1, 1].set_xlabel("Year")
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle("Mechanism view: birth pressure and unmatched rate")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()

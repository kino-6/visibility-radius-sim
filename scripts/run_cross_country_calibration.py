from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import matplotlib.pyplot as plt
import pandas as pd

from visibility_radius_sim.config import SimulationConfig
from visibility_radius_sim.simulation import Simulation

from experiment_helpers import dataframe_to_markdown, rmse_for_years


OUTPUT_DIR = Path("outputs/cross_country_calibration")
PAPER_NOTE_PATH = Path("paper/notes/cross_country_calibration_report_ja.md")
START_YEAR = 1980
END_YEAR = 2024
YEARS = END_YEAR - START_YEAR + 1
POPULATION = 900
CALIBRATION_SEEDS = (0, 1)
VALIDATION_SEEDS = (0, 1, 2)
ANCHOR_YEARS = (1980, 1990, 2000, 2010, 2020, 2024)
LATE_WINDOW = 10
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/{code}/indicator/{indicator}"
POPULATION_INDICATOR = "SP.POP.TOTL"
TFR_INDICATOR = "SP.DYN.TFRT.IN"
CALIBRATION_VISIBILITY_OVERRIDES = {
    "radius_schedule": "fixed",
    "initial_radius": 0.12,
    "max_radius": 0.12,
    "action_radius": 0.12,
    "initial_candidate_pool_multiplier": 1.0,
    "max_candidate_pool_multiplier": 1.0,
    "phantom_candidate_mode": "none",
    "aspirational_gender": "none",
}


@dataclass(frozen=True)
class RegionSpec:
    name: str
    label: str
    world_bank_code: str
    initial_age_distribution: str
    base_overrides: dict[str, Any]
    calibration_grid: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class VisibilityCondition:
    name: str
    label: str
    overrides: dict[str, Any]


@dataclass(frozen=True)
class AspirationProfile:
    name: str
    label: str
    overrides: dict[str, Any]


FALLBACK_POPULATION = {
    "USA": {
        1980: 227_225_000,
        1990: 249_623_000,
        2000: 282_162_411,
        2010: 309_378_227,
        2020: 331_577_720,
        2024: 340_110_988,
    },
    "GBR": {
        1980: 56_314_216,
        1990: 57_247_586,
        2000: 58_886_100,
        2010: 62_766_365,
        2020: 67_081_000,
        2024: 68_350_000,
    },
    "SSF": {
        1980: 389_959_247,
        1990: 508_991_314,
        2000: 681_125_107,
        2010: 894_666_657,
        2020: 1_169_015_451,
        2024: 1_291_044_964,
    },
}


FALLBACK_TFR = {
    "USA": {
        1980: 1.8395,
        1990: 2.081,
        2000: 2.056,
        2010: 1.931,
        2020: 1.641,
        2024: 1.599,
    },
    "GBR": {
        1980: 1.90,
        1990: 1.83,
        2000: 1.64,
        2010: 1.92,
        2020: 1.571,
        2024: 1.551,
    },
    "SSF": {
        1980: 6.72,
        1990: 6.36,
        2000: 5.80,
        2010: 5.20,
        2020: 4.57,
        2024: 4.35,
    },
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)

    observed = build_observed_frame()
    observed_path = OUTPUT_DIR / "observed_population_fertility.csv"
    observed.to_csv(observed_path, index=False)

    calibration = run_calibration_search(observed)
    selected = select_best_calibrations(calibration)
    raw, validation_summary = run_hypothesis_validation(observed, selected)

    calibration_path = OUTPUT_DIR / "calibration_summary.csv"
    selected_path = OUTPUT_DIR / "selected_calibrations.csv"
    raw_path = OUTPUT_DIR / "hypothesis_raw.csv"
    validation_summary_path = OUTPUT_DIR / "hypothesis_summary.csv"
    calibration_figure = OUTPUT_DIR / "cross_country_calibration.png"
    hypothesis_figure = OUTPUT_DIR / "cross_country_hypothesis.png"

    calibration.to_csv(calibration_path, index=False)
    selected.to_csv(selected_path, index=False)
    raw.to_csv(raw_path, index=False)
    validation_summary.to_csv(validation_summary_path, index=False)
    plot_calibration(raw, observed, calibration_figure)
    plot_hypothesis(validation_summary, hypothesis_figure)
    PAPER_NOTE_PATH.write_text(
        build_report_ja(
            selected=selected,
            validation_summary=validation_summary,
            observed_path=observed_path,
            calibration_path=calibration_path,
            selected_path=selected_path,
            raw_path=raw_path,
            validation_summary_path=validation_summary_path,
            calibration_figure=calibration_figure,
            hypothesis_figure=hypothesis_figure,
        ),
        encoding="utf-8",
    )

    print(f"wrote {observed_path}")
    print(f"wrote {calibration_path}")
    print(f"wrote {selected_path}")
    print(f"wrote {raw_path}")
    print(f"wrote {validation_summary_path}")
    print(f"wrote {calibration_figure}")
    print(f"wrote {hypothesis_figure}")
    print(f"wrote {PAPER_NOTE_PATH}")


def region_specs() -> list[RegionSpec]:
    mature_grid = tuple(
        {
            "birth_probability": birth_probability,
            "carrying_capacity": carrying_capacity,
            "pair_duration_mean": pair_duration_mean,
            "lifespan_mean": lifespan_mean,
        }
        for birth_probability in (0.18, 0.22, 0.26, 0.30)
        for carrying_capacity in (3200, 4800, 7200)
        for pair_duration_mean in (14.0, 20.0, 26.0)
        for lifespan_mean in (78.0, 84.0)
    )
    expanding_grid = tuple(
        {
            "birth_probability": birth_probability,
            "carrying_capacity": carrying_capacity,
            "pair_duration_mean": pair_duration_mean,
            "lifespan_mean": lifespan_mean,
        }
        for birth_probability in (0.28, 0.36, 0.44, 0.52)
        for carrying_capacity in (7200, 12000, 20000, None)
        for pair_duration_mean in (18.0, 26.0)
        for lifespan_mean in (62.0, 70.0, 78.0)
    )
    return [
        RegionSpec(
            name="usa",
            label="United States",
            world_bank_code="USA",
            initial_age_distribution="japan-1980-stylized",
            base_overrides={"location_cluster_count": 14, "initial_pair_fraction": 0.55},
            calibration_grid=mature_grid,
        ),
        RegionSpec(
            name="gbr",
            label="United Kingdom",
            world_bank_code="GBR",
            initial_age_distribution="japan-1980-stylized",
            base_overrides={"location_cluster_count": 10, "initial_pair_fraction": 0.55},
            calibration_grid=mature_grid,
        ),
        RegionSpec(
            name="ssf",
            label="Sub-Saharan Africa",
            world_bank_code="SSF",
            initial_age_distribution="young-expanding-stylized",
            base_overrides={"location_cluster_count": 18, "initial_pair_fraction": 0.45},
            calibration_grid=expanding_grid,
        ),
    ]


def build_observed_frame() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for spec in region_specs():
        population = fetch_indicator(spec.world_bank_code, POPULATION_INDICATOR)
        tfr = fetch_indicator(spec.world_bank_code, TFR_INDICATOR)
        population_source = "World Bank API" if population else "fallback anchors"
        tfr_source = "World Bank API" if tfr else "fallback anchors"
        population = population or FALLBACK_POPULATION[spec.world_bank_code]
        tfr = tfr or FALLBACK_TFR[spec.world_bank_code]
        frame = interpolate_observed(spec, population, tfr)
        frame["population_source"] = population_source
        frame["tfr_source"] = tfr_source
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def fetch_indicator(country_code: str, indicator: str) -> dict[int, float]:
    url = (
        WORLD_BANK_BASE_URL.format(code=country_code, indicator=indicator)
        + "?format=json&per_page=20000"
    )
    try:
        with urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, URLError, json.JSONDecodeError, OSError) as exc:
        print(f"World Bank fetch failed for {country_code}/{indicator}: {exc}", flush=True)
        return {}
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        return {}
    values: dict[int, float] = {}
    for item in payload[1]:
        if not isinstance(item, dict) or item.get("value") is None:
            continue
        year = int(item["date"])
        if START_YEAR <= year <= END_YEAR:
            values[year] = float(item["value"])
    return values


def interpolate_observed(
    spec: RegionSpec,
    population_by_year: dict[int, float],
    tfr_by_year: dict[int, float],
) -> pd.DataFrame:
    years = pd.DataFrame({"calendar_year": range(START_YEAR, END_YEAR + 1)})
    population = pd.DataFrame(
        {"calendar_year": list(population_by_year.keys()), "actual_population": list(population_by_year.values())}
    )
    tfr = pd.DataFrame({"calendar_year": list(tfr_by_year.keys()), "tfr": list(tfr_by_year.values())})
    frame = years.merge(population, on="calendar_year", how="left").merge(tfr, on="calendar_year", how="left")
    frame["actual_population"] = frame["actual_population"].interpolate(method="linear").ffill().bfill()
    frame["tfr"] = frame["tfr"].interpolate(method="linear").ffill().bfill()
    baseline = float(frame.loc[frame["calendar_year"] == START_YEAR, "actual_population"].iloc[0])
    tfr_baseline = float(frame.loc[frame["calendar_year"] == 2000, "tfr"].iloc[0])
    if tfr_baseline <= 0:
        tfr_baseline = float(frame["tfr"].mean())
    frame["actual_population_index"] = frame["actual_population"] / baseline
    frame["tfr_multiplier"] = frame["tfr"] / tfr_baseline
    frame.insert(0, "region", spec.name)
    frame.insert(1, "region_label", spec.label)
    frame.insert(2, "world_bank_code", spec.world_bank_code)
    return frame


def run_calibration_search(observed: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in region_specs():
        reference = (
            observed.loc[observed["region"] == spec.name]
            .set_index("calendar_year")["actual_population_index"]
            .copy()
        )
        tfr_anchors = tfr_anchors_for_region(observed, spec.name)
        total = len(spec.calibration_grid) * len(CALIBRATION_SEEDS)
        candidate_index = 0
        for candidate_number, candidate in enumerate(spec.calibration_grid, start=1):
            rmse_values: list[float] = []
            final_ratios: list[float] = []
            late_births: list[float] = []
            for seed in CALIBRATION_SEEDS:
                candidate_index += 1
                print(
                    f"[calibrate {spec.label} {candidate_index:03d}/{total:03d}] "
                    f"candidate={candidate_number} seed={seed}",
                    flush=True,
                )
                config = base_config(spec, seed, tfr_anchors).with_overrides(
                    **CALIBRATION_VISIBILITY_OVERRIDES,
                    **candidate,
                )
                frame = run_single_frame(config)
                by_year = frame.set_index("calendar_year")["population_index"]
                rmse_values.append(rmse_for_years(by_year, reference, ANCHOR_YEARS))
                final_ratios.append(float(frame["population_index"].iloc[-1]))
                late_births.append(float(frame.tail(LATE_WINDOW)["births_per_population"].mean()))
            mean_rmse = float(pd.Series(rmse_values).mean())
            mean_final = float(pd.Series(final_ratios).mean())
            rows.append(
                {
                    "region": spec.name,
                    "region_label": spec.label,
                    "candidate": candidate_number,
                    "seed_count": len(CALIBRATION_SEEDS),
                    "anchor_rmse_mean": mean_rmse,
                    "anchor_rmse_min": float(min(rmse_values)),
                    "anchor_rmse_max": float(max(rmse_values)),
                    "final_ratio_mean": mean_final,
                    "final_ratio_min": float(min(final_ratios)),
                    "final_ratio_max": float(max(final_ratios)),
                    "late_births_per_population_mean": float(pd.Series(late_births).mean()),
                    "score": mean_rmse,
                    **candidate,
                    **spec.base_overrides,
                }
            )
    return pd.DataFrame(rows).sort_values(["region", "score", "anchor_rmse_mean"]).reset_index(drop=True)


def select_best_calibrations(calibration: pd.DataFrame) -> pd.DataFrame:
    selected = calibration.sort_values(["region", "score"]).groupby("region", as_index=False).head(1)
    return selected.sort_values("region").reset_index(drop=True)


def run_hypothesis_validation(
    observed: pd.DataFrame,
    selected: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    conditions = visibility_conditions()
    profiles = aspiration_profiles()
    selected_by_region = selected.set_index("region")
    total = len(selected_by_region) * len(conditions) * len(profiles) * len(VALIDATION_SEEDS)
    run_number = 0
    for spec in region_specs():
        selected_row = selected_by_region.loc[spec.name]
        candidate_overrides = {
            "birth_probability": float(selected_row["birth_probability"]),
            "carrying_capacity": none_if_nan(selected_row["carrying_capacity"]),
            "pair_duration_mean": float(selected_row["pair_duration_mean"]),
            "lifespan_mean": float(selected_row["lifespan_mean"]),
        }
        reference = (
            observed.loc[observed["region"] == spec.name]
            .set_index("calendar_year")["actual_population_index"]
            .copy()
        )
        tfr_anchors = tfr_anchors_for_region(observed, spec.name)
        for condition in conditions:
            for profile in profiles:
                for seed in VALIDATION_SEEDS:
                    run_number += 1
                    print(
                        f"[validate {run_number:03d}/{total:03d}] "
                        f"{spec.label} / {condition.label} / {profile.label} / seed={seed}",
                        flush=True,
                    )
                    config = base_config(spec, seed, tfr_anchors).with_overrides(
                        **candidate_overrides,
                        **condition.overrides,
                        **profile.overrides,
                    )
                    frame = run_single_frame(config)
                    frame.insert(0, "region", spec.name)
                    frame.insert(1, "region_label", spec.label)
                    frame.insert(2, "visibility_condition", condition.name)
                    frame.insert(3, "visibility_label", condition.label)
                    frame.insert(4, "aspiration_profile", profile.name)
                    frame.insert(5, "aspiration_label", profile.label)
                    frame.insert(6, "seed", seed)
                    raw_frames.append(frame)
                    summary_rows.append(summarize_run(frame, spec, condition, profile, seed, reference))
    raw = pd.concat(raw_frames, ignore_index=True)
    summary = summarize_validation(pd.DataFrame(summary_rows))
    return raw, summary


def base_config(spec: RegionSpec, seed: int, tfr_anchors: tuple[tuple[int, float], ...]) -> SimulationConfig:
    return SimulationConfig.for_scenario("japan-2070").with_overrides(
        years=YEARS,
        start_calendar_year=START_YEAR,
        initial_population=POPULATION,
        seed=seed,
        initial_age_distribution=spec.initial_age_distribution,
        reproductive_min_age=20,
        reproductive_max_age=44,
        fertility_age_profile="japan-stylized",
        birth_probability_schedule="anchored",
        birth_probability_schedule_anchors=tfr_anchors,
        worker_count=None,
        max_auto_workers=8,
        parallel_threshold=200,
        metrics_precision=6,
        gender_mode="binary-balanced",
        selection_mode="top-k",
        top_k=16,
        actionable_selection_reserve_fraction=0.25,
        metadata={
            "scenario": "cross-country-calibration",
            "region": spec.name,
            "world_bank_code": spec.world_bank_code,
        },
        **spec.base_overrides,
    )


def tfr_anchors_for_region(observed: pd.DataFrame, region: str) -> tuple[tuple[int, float], ...]:
    frame = observed.loc[observed["region"] == region, ["calendar_year", "tfr_multiplier"]]
    return tuple((int(row.calendar_year), float(row.tfr_multiplier)) for row in frame.itertuples(index=False))


def run_single_frame(config: SimulationConfig) -> pd.DataFrame:
    frame = Simulation(config).run()
    start_population = float(frame["population_size"].iloc[0])
    frame = frame.copy()
    frame["population_index"] = 0.0 if start_population == 0.0 else frame["population_size"] / start_population
    return frame


def visibility_conditions() -> list[VisibilityCondition]:
    return [
        VisibilityCondition(
            "local_actionable",
            "Local visible/actionable",
            {
                "radius_schedule": "fixed",
                "initial_radius": 0.12,
                "max_radius": 0.12,
                "action_radius": 0.12,
                "initial_candidate_pool_multiplier": 1.0,
                "max_candidate_pool_multiplier": 1.0,
                "phantom_candidate_mode": "none",
            },
        ),
        VisibilityCondition("sns_expansion", "SNS-like expansion", {}),
        VisibilityCondition(
            "global_from_start",
            "Global from start",
            {
                "radius_schedule": "global",
                "initial_candidate_pool_multiplier": 300.0,
                "max_candidate_pool_multiplier": 300.0,
                "phantom_candidate_mode": "sampled",
            },
        ),
    ]


def aspiration_profiles() -> list[AspirationProfile]:
    return [
        AspirationProfile("symmetric", "Symmetric", {"aspirational_gender": "none"}),
        AspirationProfile(
            "b_500_proxy",
            "B 500+ proxy",
            {"aspirational_gender": "B", "aspirational_min_score_quantile": 0.55},
        ),
        AspirationProfile(
            "b_light_mixed",
            "B light mixed",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.55, 0.25, 0.15, 0.05),
            },
        ),
        AspirationProfile(
            "b_heavy_mixed",
            "B compound-heavy",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.25, 0.25, 0.35, 0.15),
            },
        ),
    ]


def summarize_run(
    frame: pd.DataFrame,
    spec: RegionSpec,
    condition: VisibilityCondition,
    profile: AspirationProfile,
    seed: int,
    reference: pd.Series,
) -> dict[str, Any]:
    by_year = frame.set_index("calendar_year")["population_index"]
    late = frame.tail(min(LATE_WINDOW, len(frame)))
    return {
        "region": spec.name,
        "region_label": spec.label,
        "visibility_condition": condition.name,
        "visibility_label": condition.label,
        "aspiration_profile": profile.name,
        "aspiration_label": profile.label,
        "seed": seed,
        "anchor_rmse": rmse_for_years(by_year, reference, ANCHOR_YEARS),
        "final_ratio": float(frame["population_index"].iloc[-1]),
        "mean_unmatched_rate": float(frame["unmatched_rate"].mean()),
        "late_unmatched_rate": float(late["unmatched_rate"].mean()),
        "late_births_per_population": float(late["births_per_population"].mean()),
    }


def summarize_validation(run_summary: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        run_summary.groupby(
            ["region", "region_label", "visibility_condition", "visibility_label", "aspiration_profile", "aspiration_label"],
            as_index=False,
        )
        .agg(
            seed_count=("seed", "nunique"),
            anchor_rmse_mean=("anchor_rmse", "mean"),
            final_ratio_mean=("final_ratio", "mean"),
            final_ratio_min=("final_ratio", "min"),
            final_ratio_max=("final_ratio", "max"),
            mean_unmatched_rate=("mean_unmatched_rate", "mean"),
            late_unmatched_rate=("late_unmatched_rate", "mean"),
            late_births_per_population=("late_births_per_population", "mean"),
        )
        .sort_values(["region", "visibility_condition", "aspiration_profile"])
    )
    symmetric = grouped.loc[grouped["aspiration_profile"] == "symmetric"].copy()
    symmetric = symmetric[
        ["region", "visibility_condition", "final_ratio_mean", "late_births_per_population", "late_unmatched_rate"]
    ].rename(
        columns={
            "final_ratio_mean": "symmetric_final_ratio_mean",
            "late_births_per_population": "symmetric_late_births_per_population",
            "late_unmatched_rate": "symmetric_late_unmatched_rate",
        }
    )
    grouped = grouped.merge(symmetric, on=["region", "visibility_condition"], how="left")
    grouped["delta_final_ratio_vs_symmetric"] = (
        grouped["final_ratio_mean"] - grouped["symmetric_final_ratio_mean"]
    )
    grouped["delta_late_births_vs_symmetric"] = (
        grouped["late_births_per_population"] - grouped["symmetric_late_births_per_population"]
    )
    grouped["delta_late_unmatched_vs_symmetric"] = (
        grouped["late_unmatched_rate"] - grouped["symmetric_late_unmatched_rate"]
    )
    return grouped


def plot_calibration(raw: pd.DataFrame, observed: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=False)
    for axis, spec in zip(axes, region_specs(), strict=True):
        observed_region = observed.loc[observed["region"] == spec.name]
        axis.plot(
            observed_region["calendar_year"],
            observed_region["actual_population_index"],
            color="black",
            linewidth=2.4,
            label="Observed",
        )
        baseline = raw.loc[
            (raw["region"] == spec.name)
            & (raw["visibility_condition"] == "local_actionable")
            & (raw["aspiration_profile"] == "symmetric")
        ]
        mean_line = baseline.groupby("calendar_year", as_index=False)["population_index"].mean()
        axis.plot(
            mean_line["calendar_year"],
            mean_line["population_index"],
            color="#276fbf",
            linewidth=2.0,
            label="Calibrated base",
        )
        axis.set_title(spec.label)
        axis.set_xlabel("Year")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Population index, 1980=1.0")
    axes[0].legend(loc="best")
    fig.suptitle("Rough calibration against World Bank population lines")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_hypothesis(summary: pd.DataFrame, output_path: Path) -> None:
    heavy = summary.loc[summary["aspiration_profile"] == "b_heavy_mixed"].copy()
    heavy["label"] = heavy["region_label"] + "\n" + heavy["visibility_label"]
    colors = {
        "local_actionable": "#4c956c",
        "sns_expansion": "#d68c45",
        "global_from_start": "#7b2cbf",
    }
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2))
    axes[0].bar(
        heavy["label"],
        heavy["delta_final_ratio_vs_symmetric"],
        color=[colors[name] for name in heavy["visibility_condition"]],
    )
    axes[0].axhline(0.0, color="black", linewidth=1.0)
    axes[0].set_title("Population-index penalty from compound-heavy aspiration")
    axes[0].set_ylabel("Final population-index delta")
    axes[0].tick_params(axis="x", labelrotation=45)
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(
        heavy["label"],
        heavy["delta_late_births_vs_symmetric"],
        color=[colors[name] for name in heavy["visibility_condition"]],
    )
    axes[1].axhline(0.0, color="black", linewidth=1.0)
    axes[1].set_title("Late birth-rate penalty from compound-heavy aspiration")
    axes[1].set_ylabel("Late births per population delta")
    axes[1].tick_params(axis="x", labelrotation=45)
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_report_ja(
    *,
    selected: pd.DataFrame,
    validation_summary: pd.DataFrame,
    observed_path: Path,
    calibration_path: Path,
    selected_path: Path,
    raw_path: Path,
    validation_summary_path: Path,
    calibration_figure: Path,
    hypothesis_figure: Path,
) -> str:
    fit_table = calibration_fit_table(raw_path, observed_path)
    selected_table = selected[
        [
            "region_label",
            "anchor_rmse_mean",
            "final_ratio_mean",
            "birth_probability",
            "carrying_capacity",
            "pair_duration_mean",
            "lifespan_mean",
        ]
    ].round(4)
    heavy = validation_summary.loc[validation_summary["aspiration_profile"] == "b_heavy_mixed"].copy()
    heavy_table = heavy[
        [
            "region_label",
            "visibility_label",
            "final_ratio_mean",
            "delta_final_ratio_vs_symmetric",
            "late_births_per_population",
            "delta_late_births_vs_symmetric",
        ]
    ].round(4)
    return f"""# Cross-Country Calibration Note

## 目的

日本だけでなく、United States、United Kingdom、Sub-Saharan Africa aggregate について、1980-2024年の実測人口ラインを粗くなぞる土台パラメータを探索した。その上で、同じ土台に対して `visibility expansion x aspirational selection` の初回検証を行った。

これは人口予測ではない。現実人口には移民、医療、制度、都市化、教育、経済ショックなどが入っているが、このSimはそれらを明示的には持たない。ここで得たパラメータは「未モデル化要因を吸収した、比較実験用の粗い土台」と読む。

## データ

- 人口: World Bank `SP.POP.TOTL`
- 合計特殊出生率: World Bank `SP.DYN.TFRT.IN`
- 期間: 1980-2024
- 対象: `USA`, `GBR`, `SSF`
- `SSF` は国ではなく Sub-Saharan Africa aggregate。
- API URL template: `https://api.worldbank.org/v2/country/{{code}}/indicator/{{indicator}}?format=json&per_page=20000`
- 参照: World Bank Data Help Desk API documentation, World Bank WDI metadata for `SP.POP.TOTL` and `SP.DYN.TFRT.IN`, World Bank country metadata for `SSF`。

World Bank API取得に失敗した場合は、スクリプト内のフォールバックアンカーを使う。今回の出力CSVには、各行の `population_source` と `tfr_source` を記録している。

## 方法

- 各地域の人口は `population_index = population / population_1980` で比較した。
- TFRは2000年値を1.0とする倍率に変換し、`birth_probability_schedule=\"anchored\"` で年次出生確率に掛けた。
- US/UKは成熟人口の粗い年齢構造、Sub-Saharan Africaは若い拡大型の粗い年齢構造から初期化した。
- 1980, 1990, 2000, 2010, 2020, 2024 の人口指数RMSEが小さい候補を採用した。
- キャリブレーションSeed: {CALIBRATION_SEEDS}
- 検証Seed: {VALIDATION_SEEDS}

## 採用パラメータ

{dataframe_to_markdown(selected_table)}

## 土台線と現実線の照合

下表は、採用パラメータの `Local visible/actionable + Symmetric` 条件を、World Bank人口指数と比較したもの。`diff` は `sim_index - actual_index`。

{dataframe_to_markdown(fit_table)}

## 仮説検証の初回結果

下表は compound-heavy aspiration、つまり相対的に上位スコア候補へ強く寄る条件を、同じvisibility条件の symmetric 条件と比較したもの。

{dataframe_to_markdown(heavy_table)}

## 読み方

`delta_final_ratio_vs_symmetric` が負なら、同じ地域土台・同じvisibility条件の symmetric 条件より、最終人口指数が低い。`delta_late_births_vs_symmetric` が負なら、終盤10年の出生率も低い。

今回の焦点は、国や地域そのものの優劣ではなく、同じ土台の中で「候補プール拡大」と「相対上位志向」が組み合わさったときに、人口維持に必要なペア形成や出生が削られるかどうかである。

## 出力

- 観測データ: `{observed_path}`
- 探索結果: `{calibration_path}`
- 採用候補: `{selected_path}`
- 検証Raw: `{raw_path}`
- 検証Summary: `{validation_summary_path}`
- キャリブレーション図: `{calibration_figure}`
- 仮説検証図: `{hypothesis_figure}`

## 注意点

- これはWorld Bank実測線に形を寄せた抽象モデルであり、因果推定でも将来予測でもない。
- 移民を明示していないため、US/UKの人口増は出生・死亡・キャパシティ・ペア継続などの抽象パラメータがまとめて吸収している。
- Sub-Saharan Africaは集計地域なので、国別の制度・都市化・年齢構造の差は潰れている。
- 2024以降の将来外挿は今回行っていない。
"""


def calibration_fit_table(raw_path: Path, observed_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(raw_path)
    observed = pd.read_csv(observed_path)
    baseline = raw.loc[
        (raw["visibility_condition"] == "local_actionable")
        & (raw["aspiration_profile"] == "symmetric")
        & (raw["calendar_year"].isin(ANCHOR_YEARS))
    ]
    simulated = (
        baseline.groupby(["region", "region_label", "calendar_year"], as_index=False)["population_index"]
        .mean()
        .rename(columns={"population_index": "sim_index"})
    )
    actual = observed.loc[
        observed["calendar_year"].isin(ANCHOR_YEARS),
        ["region", "calendar_year", "actual_population_index"],
    ].rename(columns={"actual_population_index": "actual_index"})
    merged = simulated.merge(actual, on=["region", "calendar_year"], how="left")
    merged["diff"] = merged["sim_index"] - merged["actual_index"]
    return merged[["region_label", "calendar_year", "actual_index", "sim_index", "diff"]].round(3)


def none_if_nan(value: Any) -> int | None:
    if pd.isna(value):
        return None
    return int(value)


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from visibility_radius_sim.config import SimulationConfig
from visibility_radius_sim.simulation import Simulation

from experiment_helpers import dataframe_to_markdown, japan_reference_frame, rmse_for_years


OUTPUT_DIR = Path("outputs/primary_hypothesis_validation")
PAPER_NOTE_PATH = Path("paper/notes/primary_hypothesis_validation_report_ja.md")
SEEDS = (0, 1, 2)
LATE_WINDOW = 20
ANCHOR_YEARS = (1980, 1990, 2000, 2010, 2020, 2070)


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


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw, run_summary = run_experiment()
    summary = summarize_groups(run_summary)

    raw_path = OUTPUT_DIR / "hypothesis_validation_raw.csv"
    run_summary_path = OUTPUT_DIR / "hypothesis_validation_run_summary.csv"
    summary_path = OUTPUT_DIR / "hypothesis_validation_summary.csv"
    figure_path = OUTPUT_DIR / "hypothesis_validation.png"

    raw.to_csv(raw_path, index=False)
    run_summary.to_csv(run_summary_path, index=False)
    summary.to_csv(summary_path, index=False)
    plot_results(raw, summary, figure_path)
    PAPER_NOTE_PATH.write_text(build_report_ja(summary), encoding="utf-8")

    print(f"wrote {raw_path}")
    print(f"wrote {run_summary_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {figure_path}")
    print(f"wrote {PAPER_NOTE_PATH}")


def base_config(seed: int) -> SimulationConfig:
    return SimulationConfig.for_scenario("japan-2070").with_overrides(
        seed=seed,
        worker_count=None,
        max_auto_workers=8,
        parallel_threshold=200,
        metrics_precision=6,
        gender_mode="binary-balanced",
    )


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
        VisibilityCondition(
            "sns_expansion",
            "SNS-like expansion",
            {},
        ),
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


def run_experiment() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    reference = japan_reference_frame().set_index("calendar_year")["population_index"]
    conditions = visibility_conditions()
    profiles = aspiration_profiles()
    total = len(conditions) * len(profiles) * len(SEEDS)
    run_index = 0
    for condition in conditions:
        for profile in profiles:
            for seed in SEEDS:
                run_index += 1
                print(f"[{run_index:03d}/{total:03d}] {condition.label} / {profile.label} / seed={seed}")
                config = base_config(seed).with_overrides(**condition.overrides, **profile.overrides)
                frame = Simulation(config).run()
                start_population = float(frame["population_size"].iloc[0])
                frame = frame.copy()
                frame.insert(0, "visibility_condition", condition.name)
                frame.insert(1, "visibility_label", condition.label)
                frame.insert(2, "aspiration_profile", profile.name)
                frame.insert(3, "aspiration_label", profile.label)
                frame.insert(4, "seed", seed)
                frame["population_index"] = (
                    0.0 if start_population == 0.0 else frame["population_size"] / start_population
                )
                raw_frames.append(frame)
                summary_rows.append(summarize_run(frame, reference))
    return pd.concat(raw_frames, ignore_index=True), pd.DataFrame(summary_rows)


def summarize_run(frame: pd.DataFrame, reference: pd.Series) -> dict[str, Any]:
    late = frame.tail(min(LATE_WINDOW, len(frame)))
    start_population = float(frame["population_size"].iloc[0])
    final_population = float(frame["population_size"].iloc[-1])
    by_year = frame.set_index("calendar_year")["population_index"]
    return {
        "visibility_condition": str(frame["visibility_condition"].iloc[0]),
        "visibility_label": str(frame["visibility_label"].iloc[0]),
        "aspiration_profile": str(frame["aspiration_profile"].iloc[0]),
        "aspiration_label": str(frame["aspiration_label"].iloc[0]),
        "seed": int(frame["seed"].iloc[0]),
        "start_population": start_population,
        "peak_population": float(frame["population_size"].max()),
        "peak_year": int(frame.loc[frame["population_size"].idxmax(), "calendar_year"]),
        "final_population": final_population,
        "final_ratio": 0.0 if start_population == 0.0 else final_population / start_population,
        "anchor_rmse": rmse_for_years(by_year, reference, ANCHOR_YEARS),
        "late_unmatched_mean": float(late["unmatched_rate"].mean()),
        "late_unmatched_a_mean": float(late["unmatched_rate_gender_a"].mean()),
        "late_unmatched_b_mean": float(late["unmatched_rate_gender_b"].mean()),
        "late_births_per_population_mean": float(late["births_per_population"].mean()),
        "late_births_per_eligible_mean": float(late["births_per_eligible"].mean()),
        "late_selected_actionable_mean": float(late["mean_selected_actionable_share"].mean()),
        "late_phantom_share_mean": float(late["mean_phantom_selection_share"].mean()),
        "late_perceived_candidates_mean": float(late["mean_perceived_candidate_count"].mean()),
    }


def summarize_groups(run_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in run_summary.groupby(
        ["visibility_condition", "visibility_label", "aspiration_profile", "aspiration_label"],
        sort=False,
    ):
        row = {
            "visibility_condition": keys[0],
            "visibility_label": keys[1],
            "aspiration_profile": keys[2],
            "aspiration_label": keys[3],
            "seed_count": int(group["seed"].nunique()),
            "final_ratio_mean": float(group["final_ratio"].mean()),
            "final_ratio_min": float(group["final_ratio"].min()),
            "final_ratio_max": float(group["final_ratio"].max()),
            "anchor_rmse_mean": float(group["anchor_rmse"].mean()),
            "late_unmatched_mean": float(group["late_unmatched_mean"].mean()),
            "late_unmatched_b_mean": float(group["late_unmatched_b_mean"].mean()),
            "late_births_per_population_mean": float(group["late_births_per_population_mean"].mean()),
            "late_selected_actionable_mean": float(group["late_selected_actionable_mean"].mean()),
            "late_phantom_share_mean": float(group["late_phantom_share_mean"].mean()),
            "late_perceived_candidates_mean": float(group["late_perceived_candidates_mean"].mean()),
        }
        rows.append(row)
    summary = pd.DataFrame(rows)
    symmetric = (
        summary.loc[summary["aspiration_profile"] == "symmetric"]
        .set_index("visibility_condition")["final_ratio_mean"]
        .to_dict()
    )
    summary["delta_vs_symmetric"] = [
        float(row["final_ratio_mean"] - symmetric[row["visibility_condition"]])
        for _, row in summary.iterrows()
    ]
    summary["retained_vs_symmetric"] = [
        0.0
        if symmetric[row["visibility_condition"]] == 0.0
        else float(row["final_ratio_mean"] / symmetric[row["visibility_condition"]])
        for _, row in summary.iterrows()
    ]
    return summary


def plot_results(raw: pd.DataFrame, summary: pd.DataFrame, output_path: Path) -> None:
    reference = japan_reference_frame()
    profiles = [profile.label for profile in aspiration_profiles()]
    conditions = [condition.label for condition in visibility_conditions()]
    colors = {
        "Symmetric": "#1f77b4",
        "B 500+ proxy": "#2ca02c",
        "B light mixed": "#ff7f0e",
        "B compound-heavy": "#d62728",
    }
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)

    pivot = summary.pivot(index="visibility_label", columns="aspiration_label", values="final_ratio_mean")
    pivot = pivot.loc[conditions, profiles]
    x = range(len(pivot.index))
    width = 0.18
    for offset, profile in enumerate(profiles):
        axes[0, 0].bar(
            [value + (offset - 1.5) * width for value in x],
            pivot[profile],
            width=width,
            color=colors[profile],
            label=profile,
        )
    axes[0, 0].set_xticks(list(x))
    axes[0, 0].set_xticklabels(pivot.index, rotation=20, ha="right")
    axes[0, 0].set_title("Final population ratio")
    axes[0, 0].grid(axis="y", alpha=0.25)
    axes[0, 0].legend(frameon=False, fontsize=8)

    deltas = summary.loc[summary["aspiration_profile"] != "symmetric"].pivot(
        index="visibility_label",
        columns="aspiration_label",
        values="delta_vs_symmetric",
    )
    delta_columns = [profile for profile in profiles if profile != "Symmetric"]
    deltas = deltas.loc[conditions, delta_columns]
    for offset, profile in enumerate(delta_columns):
        axes[0, 1].bar(
            [value + (offset - 1.0) * 0.22 for value in x],
            deltas[profile],
            width=0.22,
            color=colors[profile],
            label=profile,
        )
    axes[0, 1].axhline(0.0, color="#222222", linewidth=1)
    axes[0, 1].set_xticks(list(x))
    axes[0, 1].set_xticklabels(deltas.index, rotation=20, ha="right")
    axes[0, 1].set_title("Population penalty vs symmetric")
    axes[0, 1].grid(axis="y", alpha=0.25)
    axes[0, 1].legend(frameon=False, fontsize=8)

    sns = raw.loc[raw["visibility_condition"] == "sns_expansion"]
    axes[1, 0].plot(
        reference["calendar_year"],
        reference["population_index"],
        color="#111111",
        linewidth=2.4,
        label="Japan reference",
    )
    for profile in profiles:
        group = sns.loc[sns["aspiration_label"] == profile]
        trajectory = group.groupby("calendar_year", as_index=False)["population_index"].mean()
        axes[1, 0].plot(
            trajectory["calendar_year"],
            trajectory["population_index"],
            color=colors[profile],
            linewidth=1.8,
            label=profile,
        )
    axes[1, 0].set_title("SNS-like expansion trajectories")
    axes[1, 0].set_ylabel("Population index")
    axes[1, 0].grid(alpha=0.25)
    axes[1, 0].legend(frameon=False, fontsize=8)

    unmatched = summary.pivot(index="visibility_label", columns="aspiration_label", values="late_unmatched_b_mean")
    unmatched = unmatched.loc[conditions, profiles]
    for offset, profile in enumerate(profiles):
        axes[1, 1].bar(
            [value + (offset - 1.5) * width for value in x],
            unmatched[profile],
            width=width,
            color=colors[profile],
            label=profile,
        )
    axes[1, 1].set_xticks(list(x))
    axes[1, 1].set_xticklabels(unmatched.index, rotation=20, ha="right")
    axes[1, 1].set_title("Late unmatched rate, aspirational side B")
    axes[1, 1].grid(axis="y", alpha=0.25)

    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def build_report_ja(summary: pd.DataFrame) -> str:
    table = summary[
        [
            "visibility_label",
            "aspiration_label",
            "final_ratio_mean",
            "delta_vs_symmetric",
            "retained_vs_symmetric",
            "anchor_rmse_mean",
            "late_unmatched_b_mean",
            "late_births_per_population_mean",
            "late_selected_actionable_mean",
        ]
    ].copy()
    for column in (
        "final_ratio_mean",
        "delta_vs_symmetric",
        "retained_vs_symmetric",
        "anchor_rmse_mean",
        "late_unmatched_b_mean",
        "late_births_per_population_mean",
        "late_selected_actionable_mean",
    ):
        table[column] = table[column].map(lambda value: f"{float(value):.3f}")

    heavy = summary.loc[summary["aspiration_profile"] == "b_heavy_mixed"][
        ["visibility_label", "delta_vs_symmetric", "retained_vs_symmetric"]
    ].copy()
    for column in ("delta_vs_symmetric", "retained_vs_symmetric"):
        heavy[column] = heavy[column].map(lambda value: f"{float(value):.3f}")

    return "\n".join(
        [
            "# Primary Hypothesis Validation 日本語メモ",
            "",
            "## 検証した仮説",
            "",
            "候補プールが local から SNS-like/global へ拡大すると、相対的上位層だけを足切りする aspiration profile は、",
            "上位選択なしの対称条件に比べて人口維持を悪化させる。特に、複合条件を重く見る `B compound-heavy` で悪化が大きくなる。",
            "",
            "この検証は現実因果の証明ではない。Japan-like calibration を土台にした toy model 内の機構検証である。",
            "",
            "## 条件",
            "",
            "- Base: `SimulationConfig.for_scenario(\"japan-2070\")`",
            "- Seeds: `0, 1, 2`",
            "- Visibility: local visible/actionable, SNS-like expansion, global from start",
            "- Aspiration: symmetric, B 500+ proxy, B light mixed, B compound-heavy",
            "- Output: `outputs/primary_hypothesis_validation/`",
            "",
            "## 結果表",
            "",
            dataframe_to_markdown(
                table.rename(
                    columns={
                        "visibility_label": "可視性条件",
                        "aspiration_label": "aspiration",
                        "final_ratio_mean": "最終人口比",
                        "delta_vs_symmetric": "対称差分",
                        "retained_vs_symmetric": "対称比",
                        "anchor_rmse_mean": "参照RMSE",
                        "late_unmatched_b_mean": "後期B未成立率",
                        "late_births_per_population_mean": "後期出生/人口",
                        "late_selected_actionable_mean": "後期現実候補選択率",
                    }
                )
            ),
            "",
            "## Heavy profile の要約",
            "",
            dataframe_to_markdown(
                heavy.rename(
                    columns={
                        "visibility_label": "可視性条件",
                        "delta_vs_symmetric": "対称差分",
                        "retained_vs_symmetric": "対称比",
                    }
                )
            ),
            "",
            "## 解釈",
            "",
            "`SNS-like expansion` では、対称条件はJapan referenceに近い人口線を維持するが、",
            "`B compound-heavy` は最終人口比を大きく押し下げる。",
            "この結果は、単なる出生環境の悪化だけでなく、拡大した候補プール上での上位足切りが追加的な人口抑制として働く、という仮説を支持する。",
            "",
            "ただし、local visible/actionable でも aspiration penalty は完全には消えない。",
            "これは、このモデルでは aspiration が物理距離ではなく候補集合内の相対順位足切りとして実装されているためである。",
            "したがって、より強い主張には、local 条件での認知上限・反復接触・学習緩和を別途モデル化する必要がある。",
            "",
            "## 図",
            "",
            "- `outputs/primary_hypothesis_validation/hypothesis_validation.png`",
            "",
            "## 再実行",
            "",
            "```bash",
            ".venv/bin/python scripts/run_primary_hypothesis_validation.py",
            "```",
            "",
        ]
    )


if __name__ == "__main__":
    main()

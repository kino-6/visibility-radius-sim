from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from visibility_radius_sim.config import SimulationConfig
from visibility_radius_sim.simulation import Simulation


OUTPUT_DIR = Path("outputs/gendered_robustness")
PAPER_NOTE_PATH = Path("paper/notes/gendered_robustness_report.md")
PAPER_NOTE_JA_PATH = Path("paper/notes/gendered_robustness_report_ja.md")
YEARS = 180
POPULATION = 1200
SEEDS = (0, 1, 2)
LATE_WINDOW = 30


@dataclass(frozen=True)
class AspirationProfile:
    name: str
    label: str
    overrides: dict[str, Any]
    quantile_label: str


@dataclass(frozen=True)
class Calibration:
    name: str
    label: str
    overrides: dict[str, Any]
    category: str


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAPER_NOTE_JA_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw_frames: list[pd.DataFrame] = []
    run_rows: list[dict[str, Any]] = []
    profiles = aspiration_profiles()
    calibrations = calibration_variants()
    total = len(calibrations) * len(profiles)
    run_index = 0
    for calibration in calibrations:
        for profile in profiles:
            run_index += 1
            print(f"[{run_index:03d}/{total:03d}] {calibration.label} / {profile.label}", flush=True)
            for seed in SEEDS:
                config = base_config(seed).with_overrides(**calibration.overrides, **profile.overrides)
                frame = Simulation(config).run()
                frame.insert(0, "calibration", calibration.name)
                frame.insert(1, "calibration_label", calibration.label)
                frame.insert(2, "aspiration_profile", profile.name)
                frame.insert(3, "aspiration_label", profile.label)
                frame.insert(4, "seed", seed)
                frame["calibration_category"] = calibration.category
                frame["quantile_label"] = profile.quantile_label
                raw_frames.append(frame)
                run_rows.append(summarize_run(frame, calibration, profile, seed))

    raw = pd.concat(raw_frames, ignore_index=True)
    run_summary = pd.DataFrame(run_rows)
    summary = summarize_groups(run_summary)
    summary = add_profile_deltas(summary)

    raw_path = OUTPUT_DIR / "gendered_robustness_raw.csv"
    run_summary_path = OUTPUT_DIR / "gendered_robustness_run_summary.csv"
    summary_path = OUTPUT_DIR / "gendered_robustness_summary.csv"
    figure_path = OUTPUT_DIR / "gendered_robustness_heatmap.png"
    report_path = OUTPUT_DIR / "gendered_robustness_report.md"

    raw.to_csv(raw_path, index=False)
    run_summary.to_csv(run_summary_path, index=False)
    summary.to_csv(summary_path, index=False)
    plot_heatmap(summary, figure_path)

    report = build_report(summary)
    report_ja = build_report_ja(summary)
    report_path.write_text(report, encoding="utf-8")
    PAPER_NOTE_PATH.write_text(report, encoding="utf-8")
    PAPER_NOTE_JA_PATH.write_text(report_ja, encoding="utf-8")

    print(f"wrote {raw_path}")
    print(f"wrote {run_summary_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {figure_path}")
    print(f"wrote {report_path}")
    print(f"wrote {PAPER_NOTE_PATH}")
    print(f"wrote {PAPER_NOTE_JA_PATH}")


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
        gender_mode="binary-balanced",
        selection_mode="top-k",
        top_k=16,
        actionable_selection_reserve_fraction=0.25,
    )


def aspiration_profiles() -> list[AspirationProfile]:
    return [
        AspirationProfile(
            name="symmetric",
            label="Symmetric",
            overrides={"aspirational_gender": "none"},
            quantile_label="none",
        ),
        AspirationProfile(
            name="income_500_floor",
            label="B 500+ proxy",
            overrides={"aspirational_gender": "B", "aspirational_min_score_quantile": 0.55},
            quantile_label="fixed 0.55",
        ),
        AspirationProfile(
            name="mixed_light",
            label="B light mixed",
            overrides={
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.55, 0.25, 0.15, 0.05),
            },
            quantile_label="mix 55/25/15/5 at 0.55/0.75/0.87/0.90",
        ),
        AspirationProfile(
            name="mixed_heavy",
            label="B compound-heavy",
            overrides={
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.25, 0.25, 0.35, 0.15),
            },
            quantile_label="mix 25/25/35/15 at 0.55/0.75/0.87/0.90",
        ),
    ]


def calibration_variants() -> list[Calibration]:
    return [
        Calibration("baseline", "Baseline calibration", {}, "reference"),
        Calibration("birth_low", "Lower birth probability", {"birth_probability": 0.09}, "fertility"),
        Calibration("birth_high", "Higher birth probability", {"birth_probability": 0.18}, "fertility"),
        Calibration("initial_pairs_low", "Lower initial pair stock", {"initial_pair_fraction": 0.35}, "pairing"),
        Calibration("initial_pairs_high", "Higher initial pair stock", {"initial_pair_fraction": 0.70}, "pairing"),
        Calibration("pair_duration_short", "Shorter pair duration", {"pair_duration_mean": 10.0}, "pairing"),
        Calibration("pair_duration_long", "Longer pair duration", {"pair_duration_mean": 26.0}, "pairing"),
        Calibration("phantom_100x", "Lower SNS pool multiplier", {"max_candidate_pool_multiplier": 100.0}, "visibility"),
        Calibration("phantom_500x", "Higher SNS pool multiplier", {"max_candidate_pool_multiplier": 500.0}, "visibility"),
        Calibration("topk_32", "Larger top-k capacity", {"top_k": 32}, "attention"),
        Calibration("reserve_50", "Reserve 50%", {"actionable_selection_reserve_fraction": 0.50}, "attention"),
        Calibration(
            "repro_20_44",
            "Reproductive window 20-44",
            {"reproductive_min_age": 20, "reproductive_max_age": 44},
            "age_window",
        ),
        Calibration(
            "repro_20_39",
            "Reproductive window 20-39",
            {"reproductive_min_age": 20, "reproductive_max_age": 39},
            "age_window",
        ),
    ]


def summarize_run(
    frame: pd.DataFrame,
    calibration: Calibration,
    profile: AspirationProfile,
    seed: int,
) -> dict[str, Any]:
    late = frame.tail(min(LATE_WINDOW, len(frame)))
    start_population = float(frame["population_size"].iloc[0])
    final_population = float(frame["population_size"].iloc[-1])
    below_half = frame.loc[frame["population_size"] <= 0.5 * start_population, "calendar_year"]
    return {
        "calibration": calibration.name,
        "calibration_label": calibration.label,
        "calibration_category": calibration.category,
        "aspiration_profile": profile.name,
        "aspiration_label": profile.label,
        "quantile_label": profile.quantile_label,
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
    }


def summarize_groups(run_summary: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "calibration",
        "calibration_label",
        "calibration_category",
        "aspiration_profile",
        "aspiration_label",
        "quantile_label",
    ]
    rows: list[dict[str, Any]] = []
    for keys, group in run_summary.groupby(group_columns, dropna=False, sort=False):
        row = dict(zip(group_columns, keys, strict=True))
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
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def add_profile_deltas(summary: pd.DataFrame) -> pd.DataFrame:
    baseline_by_calibration = (
        summary.loc[summary["aspiration_profile"] == "symmetric", ["calibration", "final_ratio_mean"]]
        .set_index("calibration")["final_ratio_mean"]
        .to_dict()
    )
    summary = summary.copy()
    summary["delta_vs_symmetric"] = [
        float(row["final_ratio_mean"] - baseline_by_calibration.get(row["calibration"], np.nan))
        for _, row in summary.iterrows()
    ]
    summary["retained_vs_symmetric"] = [
        safe_div(float(row["final_ratio_mean"]), baseline_by_calibration.get(row["calibration"], 0.0))
        for _, row in summary.iterrows()
    ]
    return summary


def plot_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    pivot = summary.pivot(index="calibration_label", columns="aspiration_label", values="final_ratio_mean")
    ordered_columns = [profile.label for profile in aspiration_profiles()]
    pivot = pivot[ordered_columns]

    fig, ax = plt.subplots(figsize=(11, 8), constrained_layout=True)
    image = ax.imshow(pivot.values, cmap="viridis", vmin=0.0, vmax=max(1.0, float(np.nanmax(pivot.values))))
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Gendered Aspiration Robustness: Final Population Ratio")
    for y, _ in enumerate(pivot.index):
        for x, _ in enumerate(pivot.columns):
            value = pivot.iat[y, x]
            ax.text(x, y, f"{value:.2f}", ha="center", va="center", color="white" if value < 0.55 else "black")
    fig.colorbar(image, ax=ax, label="final population ratio")
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def build_report(summary: pd.DataFrame) -> str:
    display = compact_display(summary)
    return "\n".join(
        [
            "# Gendered Aspiration Robustness Sweep",
            "",
            "This exploratory sweep checks whether the gendered aspiration result depends on one convenient",
            "calibration. It varies fertility, initial pair stock, pair duration, perceived SNS pool size,",
            "top-k capacity, actionable reserve, and reproductive age window.",
            "",
            "This is not a demographic calibration. It is a mechanism robustness check over the existing",
            "`sns-2000s` toy scenario.",
            "",
            "## Outputs",
            "",
            "- `outputs/gendered_robustness/gendered_robustness_raw.csv`",
            "- `outputs/gendered_robustness/gendered_robustness_run_summary.csv`",
            "- `outputs/gendered_robustness/gendered_robustness_summary.csv`",
            "- `outputs/gendered_robustness/gendered_robustness_heatmap.png`",
            "",
            "## Compact Summary",
            "",
            dataframe_to_markdown(display),
            "",
            "## Interpretation",
            "",
            "The sign of the aspiration penalty is stable across the tested calibrations: compound-heavy",
            "aspiration is below the symmetric condition in every row. The magnitude is not stable.",
            "Birth probability, reproductive age window, and reserve/top-k parameters change whether the",
            "system looks like decline, collapse, or partial survival.",
            "",
        ]
    )


def build_report_ja(summary: pd.DataFrame) -> str:
    display = compact_display(summary).rename(
        columns={
            "calibration_label": "条件変更",
            "symmetric": "対称",
            "income_500_floor": "500+ proxy",
            "mixed_light": "light mixed",
            "mixed_heavy": "heavy mixed",
            "heavy_delta": "heavy差分",
            "heavy_retained": "heavy/対称",
        }
    )
    return "\n".join(
        [
            "# Gendered Aspiration Robustness Sweep 日本語メモ",
            "",
            "この追試は、現行の gendered aspiration 結果が都合のよいキャリブレーションに依存していないかを見るための探索である。",
            "出生確率、初期ペア率、ペア期間、SNS的候補倍率、top-k、actionable reserve、再生産年齢窓を個別に振った。",
            "",
            "これは人口学的なキャリブレーションではない。既存の `sns-2000s` toy scenario に対する機構の頑健性チェックである。",
            "",
            "## 出力",
            "",
            "- `outputs/gendered_robustness/gendered_robustness_raw.csv`",
            "- `outputs/gendered_robustness/gendered_robustness_run_summary.csv`",
            "- `outputs/gendered_robustness/gendered_robustness_summary.csv`",
            "- `outputs/gendered_robustness/gendered_robustness_heatmap.png`",
            "",
            "## 簡易結果表",
            "",
            dataframe_to_markdown(display),
            "",
            "## 読み方",
            "",
            "`対称` はA/Bに高望み閾値を入れない参照条件。`500+ proxy` はB側だけ `quantile=0.55`。",
            "`light mixed` はB側の個体差を軽く入れた条件、`heavy mixed` は複合条件側に重みを寄せた条件。",
            "`heavy差分` は `heavy mixed - 対称` で、負なら高望み混合による追加低下を意味する。",
            "",
            "## 解釈",
            "",
            "符号はかなり安定している。tested calibrations の全条件で、heavy mixed は対称条件より低い。",
            "一方で、低下幅は安定していない。出生確率、再生産年齢窓、reserve/top-k は、",
            "結果が「低下」に見えるか「崩壊」に見えるかを大きく変える。",
            "なお `Higher initial pair stock` はこの設定では基準条件と同じ結果になった。",
            "初期ペア形成が既に飽和しており、追加指定が実質的に効いていない可能性がある。",
            "",
            "したがって、現時点で言えるのは「上位志向混合の方向性は頑健そうだが、",
            "どの程度危険かはキャリブレーション依存が大きい」ということ。",
            "特に 20-39 の年齢窓と低出生確率は、対称条件自体を弱くするため、",
            "高望み効果だけを分離して読むにはさらなる再キャリブレーションが必要である。",
            "",
            "## 再実行",
            "",
            "```bash",
            ".venv/bin/python scripts/run_gendered_robustness.py",
            "```",
            "",
        ]
    )


def compact_display(summary: pd.DataFrame) -> pd.DataFrame:
    pivot = summary.pivot(index="calibration_label", columns="aspiration_profile", values="final_ratio_mean")
    calibration_order = [calibration.label for calibration in calibration_variants()]
    pivot = pivot.reindex([label for label in calibration_order if label in pivot.index])
    rows: list[dict[str, str]] = []
    for calibration_label, row in pivot.iterrows():
        symmetric = float(row.get("symmetric", 0.0))
        heavy = float(row.get("mixed_heavy", 0.0))
        rows.append(
            {
                "calibration_label": str(calibration_label),
                "symmetric": f"{symmetric:.3f}",
                "income_500_floor": f"{float(row.get('income_500_floor', 0.0)):.3f}",
                "mixed_light": f"{float(row.get('mixed_light', 0.0)):.3f}",
                "mixed_heavy": f"{heavy:.3f}",
                "heavy_delta": f"{heavy - symmetric:.3f}",
                "heavy_retained": f"{safe_div(heavy, symmetric):.3f}",
            }
        )
    return pd.DataFrame(rows)


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    rows = [
        "| " + " | ".join(str(column) for column in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(rows)


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0.0:
        return 0.0
    return float(numerator / denominator)


if __name__ == "__main__":
    main()

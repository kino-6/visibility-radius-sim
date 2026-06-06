from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from visibility_radius_sim.config import SimulationConfig
from visibility_radius_sim.simulation import Simulation


OUTPUT_DIR = Path("outputs/gendered_aspiration")
PAPER_NOTE_PATH = Path("paper/notes/gendered_aspiration_report.md")
PAPER_NOTE_JA_PATH = Path("paper/notes/gendered_aspiration_report_ja.md")
YEARS = 180
POPULATION = 1200
SEEDS = (0, 1, 2)
LATE_WINDOW = 30


@dataclass(frozen=True)
class Scenario:
    variant: str
    label: str
    overrides: dict[str, Any]
    metadata: dict[str, Any]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAPER_NOTE_JA_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw_frames: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []
    scenarios = build_scenarios()
    for index, scenario in enumerate(scenarios, start=1):
        print(f"[{index:02d}/{len(scenarios):02d}] {scenario.label}", flush=True)
        for seed in SEEDS:
            config = base_config(seed).with_overrides(**scenario.overrides)
            frame = Simulation(config).run()
            frame.insert(0, "variant", scenario.variant)
            frame.insert(1, "label", scenario.label)
            frame.insert(2, "seed", seed)
            for key, value in scenario.metadata.items():
                frame[key] = value
            raw_frames.append(frame)
            summaries.append(summarize_run(frame, scenario, seed))

    raw = pd.concat(raw_frames, ignore_index=True)
    run_summary = pd.DataFrame(summaries)
    summary = summarize_groups(run_summary)

    raw_path = OUTPUT_DIR / "gendered_aspiration_raw.csv"
    run_summary_path = OUTPUT_DIR / "gendered_aspiration_run_summary.csv"
    summary_path = OUTPUT_DIR / "gendered_aspiration_summary.csv"
    figure_path = OUTPUT_DIR / "gendered_aspiration_summary.png"
    report_path = OUTPUT_DIR / "gendered_aspiration_report.md"

    raw.to_csv(raw_path, index=False)
    run_summary.to_csv(run_summary_path, index=False)
    summary.to_csv(summary_path, index=False)
    plot_results(raw, summary, figure_path)

    report = build_report(summary)
    report_ja = build_report_ja(summary)
    report_path.write_text(report, encoding="utf-8")
    PAPER_NOTE_PATH.write_text(report, encoding="utf-8")
    PAPER_NOTE_JA_PATH.write_text(report_ja, encoding="utf-8")

    print(f"wrote {raw_path}")
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


def build_scenarios() -> list[Scenario]:
    return [
        Scenario(
            "symmetric_reserve_025",
            "Symmetric, reserve 25%",
            {},
            {
                "aspirational_gender": "none",
                "aspiration_quantile": 0.0,
                "aspiration_profile": "none",
                "reserve_fraction": 0.25,
            },
        ),
        Scenario(
            "b_income_500_floor",
            "B income floor 500+ proxy",
            {"aspirational_gender": "B", "aspirational_min_score_quantile": 0.55},
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.55,
                "aspiration_profile": "fixed 0.55",
                "reserve_fraction": 0.25,
            },
        ),
        Scenario(
            "b_income_700_floor",
            "B income floor 700+ proxy",
            {"aspirational_gender": "B", "aspirational_min_score_quantile": 0.80},
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.80,
                "aspiration_profile": "fixed 0.80",
                "reserve_fraction": 0.25,
            },
        ),
        Scenario(
            "b_mixed_income_plus_light",
            "B mixed: 500+ base, light compound tail",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.55, 0.25, 0.15, 0.05),
            },
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.666,
                "aspiration_profile": "mix 55/25/15/5 at 0.55/0.75/0.87/0.90",
                "reserve_fraction": 0.25,
            },
        ),
        Scenario(
            "b_mixed_income_plus_heavy",
            "B mixed: compound-heavy tail",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.25, 0.25, 0.35, 0.15),
            },
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.766,
                "aspiration_profile": "mix 25/25/35/15 at 0.55/0.75/0.87/0.90",
                "reserve_fraction": 0.25,
            },
        ),
        Scenario(
            "b_mixed_income_plus_heavy_reserve_050",
            "B compound-heavy, reserve 50%",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.25, 0.25, 0.35, 0.15),
                "actionable_selection_reserve_fraction": 0.5,
            },
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.766,
                "aspiration_profile": "mix 25/25/35/15 at 0.55/0.75/0.87/0.90",
                "reserve_fraction": 0.5,
            },
        ),
        Scenario(
            "b_mixed_income_plus_heavy_no_reserve",
            "B compound-heavy, no reserve",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.25, 0.25, 0.35, 0.15),
                "actionable_selection_reserve_fraction": 0.0,
            },
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.766,
                "aspiration_profile": "mix 25/25/35/15 at 0.55/0.75/0.87/0.90",
                "reserve_fraction": 0.0,
            },
        ),
        Scenario(
            "symmetric_reserve_025_repro_20_39",
            "Symmetric, reserve 25%, repro 20-39",
            {
                "reproductive_min_age": 20,
                "reproductive_max_age": 39,
            },
            {
                "aspirational_gender": "none",
                "aspiration_quantile": 0.0,
                "aspiration_profile": "none",
                "reserve_fraction": 0.25,
                "reproductive_window": "20-39",
            },
        ),
        Scenario(
            "b_income_500_floor_repro_20_39",
            "B income floor 500+ proxy, repro 20-39",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile": 0.55,
                "reproductive_min_age": 20,
                "reproductive_max_age": 39,
            },
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.55,
                "aspiration_profile": "fixed 0.55",
                "reserve_fraction": 0.25,
                "reproductive_window": "20-39",
            },
        ),
        Scenario(
            "b_mixed_income_plus_light_repro_20_39",
            "B mixed: light compound tail, repro 20-39",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.55, 0.25, 0.15, 0.05),
                "reproductive_min_age": 20,
                "reproductive_max_age": 39,
            },
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.666,
                "aspiration_profile": "mix 55/25/15/5 at 0.55/0.75/0.87/0.90",
                "reserve_fraction": 0.25,
                "reproductive_window": "20-39",
            },
        ),
        Scenario(
            "b_mixed_income_plus_heavy_repro_20_39",
            "B mixed: compound-heavy tail, repro 20-39",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.25, 0.25, 0.35, 0.15),
                "reproductive_min_age": 20,
                "reproductive_max_age": 39,
            },
            {
                "aspirational_gender": "B",
                "aspiration_quantile": 0.766,
                "aspiration_profile": "mix 25/25/35/15 at 0.55/0.75/0.87/0.90",
                "reserve_fraction": 0.25,
                "reproductive_window": "20-39",
            },
        ),
    ]


def summarize_run(frame: pd.DataFrame, scenario: Scenario, seed: int) -> dict[str, Any]:
    late = frame.tail(min(LATE_WINDOW, len(frame)))
    start_population = float(frame["population_size"].iloc[0])
    final_population = float(frame["population_size"].iloc[-1])
    below_half = frame.loc[frame["population_size"] <= 0.5 * start_population, "calendar_year"]
    row: dict[str, Any] = {
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
        "late_unmatched_a_mean": float(late["unmatched_rate_gender_a"].mean()),
        "late_unmatched_b_mean": float(late["unmatched_rate_gender_b"].mean()),
        "late_births_per_eligible_mean": float(late["births_per_eligible"].mean()),
        "late_selected_actionable_mean": float(late["mean_selected_actionable_share"].mean()),
        "late_phantom_share_mean": float(late["mean_phantom_selection_share"].mean()),
        "late_selection_quota_mean": float(late["mean_selection_quota"].mean()),
        "reproductive_window": scenario.metadata.get("reproductive_window", "18-45"),
    }
    for key, value in scenario.metadata.items():
        row[key] = value
    return row


def summarize_groups(run_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    meta_columns = [
        "variant",
        "label",
        "aspirational_gender",
        "aspiration_quantile",
        "aspiration_profile",
        "reserve_fraction",
        "reproductive_window",
    ]
    for keys, group in run_summary.groupby(meta_columns, dropna=False, sort=False):
        row = dict(zip(meta_columns, keys, strict=True))
        row.update(
            {
                "seed_count": int(group["seed"].nunique()),
                "final_ratio_mean": float(group["final_ratio"].mean()),
                "final_ratio_min": float(group["final_ratio"].min()),
                "final_ratio_max": float(group["final_ratio"].max()),
                "min_ratio_mean": float(group["min_ratio"].mean()),
                "late_unmatched_mean": float(group["late_unmatched_mean"].mean()),
                "late_unmatched_a_mean": float(group["late_unmatched_a_mean"].mean()),
                "late_unmatched_b_mean": float(group["late_unmatched_b_mean"].mean()),
                "late_births_per_eligible_mean": float(group["late_births_per_eligible_mean"].mean()),
                "late_selected_actionable_mean": float(group["late_selected_actionable_mean"].mean()),
                "late_phantom_share_mean": float(group["late_phantom_share_mean"].mean()),
                "late_selection_quota_mean": float(group["late_selection_quota_mean"].mean()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def plot_results(raw: pd.DataFrame, summary: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    x = range(len(summary))

    axes[0, 0].bar(x, summary["final_ratio_mean"], color="#1f77b4")
    axes[0, 0].errorbar(
        x,
        summary["final_ratio_mean"],
        yerr=[
            summary["final_ratio_mean"] - summary["final_ratio_min"],
            summary["final_ratio_max"] - summary["final_ratio_mean"],
        ],
        fmt="none",
        ecolor="#333333",
        capsize=2,
    )
    axes[0, 0].axhline(0.5, color="#777777", linestyle=":", linewidth=1)
    axes[0, 0].set_title("Final population ratio")
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(summary["label"], rotation=45, ha="right", fontsize=8)
    axes[0, 0].grid(axis="y", alpha=0.25)

    for label, group in raw.groupby("label", sort=False):
        by_year = group.groupby("calendar_year", as_index=False)["population_size"].mean()
        start = by_year["population_size"].iloc[0]
        axes[0, 1].plot(by_year["calendar_year"], by_year["population_size"] / start, label=label, linewidth=1.8)
    axes[0, 1].axhline(0.5, color="#777777", linestyle=":", linewidth=1)
    axes[0, 1].set_title("Mean population trajectory")
    axes[0, 1].set_ylabel("Index")
    axes[0, 1].grid(alpha=0.25)
    axes[0, 1].legend(fontsize=7, frameon=False)

    axes[1, 0].plot(x, summary["late_unmatched_a_mean"], marker="o", label="Gender A")
    axes[1, 0].plot(x, summary["late_unmatched_b_mean"], marker="o", label="Gender B")
    axes[1, 0].set_title("Late unmatched rate by gender")
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(summary["label"], rotation=45, ha="right", fontsize=8)
    axes[1, 0].grid(alpha=0.25)
    axes[1, 0].legend(frameon=False)

    axes[1, 1].plot(x, summary["late_selected_actionable_mean"], marker="o", label="Selected actionable")
    axes[1, 1].plot(x, summary["late_phantom_share_mean"], marker="o", label="Selected phantom")
    axes[1, 1].set_title("Late attention composition")
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(summary["label"], rotation=45, ha="right", fontsize=8)
    axes[1, 1].grid(alpha=0.25)
    axes[1, 1].legend(frameon=False)

    fig.suptitle("Gendered Aspirational Selectivity Follow-Up", fontsize=16)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def build_report(summary: pd.DataFrame) -> str:
    display = summary[
        [
            "label",
            "aspiration_profile",
            "aspiration_quantile",
            "reproductive_window",
            "seed_count",
            "final_ratio_mean",
            "final_ratio_min",
            "final_ratio_max",
            "late_unmatched_a_mean",
            "late_unmatched_b_mean",
            "late_births_per_eligible_mean",
            "late_selected_actionable_mean",
            "late_phantom_share_mean",
        ]
    ].copy()
    for column in display.columns:
        if column not in {"label", "aspiration_profile", "reproductive_window", "seed_count"}:
            display[column] = display[column].map(lambda value: f"{float(value):.3f}")

    return "\n".join(
        [
            "# Gendered Aspirational Selectivity Follow-Up",
            "",
            "This follow-up adds an abstract binary gender label to pair formation.",
            "It does not add sex-specific reproductive biology. Pairs are constrained",
            "to be A-B pairs, and one side can be assigned stronger aspirational",
            "selectivity by requiring candidates to clear a relative score quantile",
            "inside the perceived comparison pool.",
            "The baseline reproductive window is 18-45. Additional sensitivity",
            "conditions restrict reproduction to ages 20-39 to represent a tighter",
            "time limit for delayed learning and pair formation.",
            "",
            "The loaded term `high standards` is represented here only as a model",
            "mechanism: candidates are ignored unless they rank high enough relative",
            "to the perceived candidate pool. It is not a moral claim about either",
            "gender.",
            "",
            "## Output Files",
            "",
            "- `outputs/gendered_aspiration/gendered_aspiration_raw.csv`",
            "- `outputs/gendered_aspiration/gendered_aspiration_run_summary.csv`",
            "- `outputs/gendered_aspiration/gendered_aspiration_summary.csv`",
            "- `outputs/gendered_aspiration/gendered_aspiration_summary.png`",
            "",
            "## Summary",
            "",
            dataframe_to_markdown(display),
            "",
            "## Interpretation",
            "",
            "This run tests relative aspiration rather than reduced attention count.",
            "The aspirational side keeps the same top-k capacity. In fixed scenarios,",
            "candidates below the configured perceived-pool score quantile are not selected.",
            "In mixed scenarios, aspirational agents carry heterogeneous thresholds, with",
            "a 500+ income-floor proxy as the lower-demand case and compound-condition tails",
            "near the top 13% to top 10% range.",
            "The 20-39 sensitivity rows test whether the same selection pressure",
            "becomes more damaging when the model has less time to recover from",
            "delayed matching.",
            "",
            "The failure mode is not simply that the aspirational side remains",
            "unmatched. Because pair formation requires mutual selection, stricter",
            "selection on one side can reduce realized pairs for both sides. The model",
            "mainly amplifies the bounded-attention bottleneck rather than producing",
            "large reproductive concentration, because agents cannot hold multiple",
            "simultaneous reproductive pairs.",
            "",
        ]
    )


def build_report_ja(summary: pd.DataFrame) -> str:
    display = summary[
        [
            "label",
            "aspiration_profile",
            "aspiration_quantile",
            "reproductive_window",
            "seed_count",
            "final_ratio_mean",
            "final_ratio_min",
            "final_ratio_max",
            "late_unmatched_a_mean",
            "late_unmatched_b_mean",
            "late_births_per_eligible_mean",
            "late_selected_actionable_mean",
            "late_phantom_share_mean",
        ]
    ].copy()
    display = display.rename(
        columns={
            "label": "条件",
            "aspiration_profile": "閾値プロファイル",
            "aspiration_quantile": "相対閾値quantile",
            "reproductive_window": "再生産年齢",
            "seed_count": "seed数",
            "final_ratio_mean": "最終人口比_平均",
            "final_ratio_min": "最終人口比_最小",
            "final_ratio_max": "最終人口比_最大",
            "late_unmatched_a_mean": "後期未成立率_A",
            "late_unmatched_b_mean": "後期未成立率_B",
            "late_births_per_eligible_mean": "後期出生数_eligible比",
            "late_selected_actionable_mean": "後期選択中_実行可能候補比",
            "late_phantom_share_mean": "後期選択中_仮想候補比",
        }
    )
    for column in display.columns:
        if column not in {"条件", "閾値プロファイル", "再生産年齢", "seed数"}:
            display[column] = display[column].map(lambda value: f"{float(value):.3f}")

    return "\n".join(
        [
            "# Gendered Aspirational Selectivity Follow-Up 日本語メモ",
            "",
            "この追試では、現行モデルに抽象的な A/B gender ラベルを加えた。",
            "ただし、性別ごとの生殖生物学は入れていない。ペア形成を A-B のみに制約し、",
            "B 側だけ perceived/global comparison pool 内の相対スコア閾値を持つことで、片側の",
            "「上位層希望」または aspirational selectivity を表現した。",
            "今回の版では、固定閾値だけでなく、個体ごとに異なる閾値を持つ混合分布も入れている。",
            "基準の再生産年齢は18〜45歳である。追加の感度分析として、学習やペア形成の遅れが",
            "より致命的になりやすい 20〜39歳のみの条件も入れた。",
            "",
            "ここでいう「高望み」は価値判断ではなく、モデル上の操作である。",
            "意味は、候補数を減らすことではなく、比較プール内で相対的に上位に入らない候補を",
            "選択対象から外す、ということに限定している。",
            "",
            "## 出力",
            "",
            "- `outputs/gendered_aspiration/gendered_aspiration_raw.csv`",
            "- `outputs/gendered_aspiration/gendered_aspiration_run_summary.csv`",
            "- `outputs/gendered_aspiration/gendered_aspiration_summary.csv`",
            "- `outputs/gendered_aspiration/gendered_aspiration_summary.png`",
            "",
            "## 結果表",
            "",
            dataframe_to_markdown(display),
            "",
            "## 読み方",
            "",
            "`B income floor 500+ proxy` は、年収500万円以上を上限なしの下限条件として読み、",
            "候補分布の上位約45%を残す近似として `quantile=0.55` を使った条件。",
            "`B income floor 700+ proxy` は、より高い単一条件の参照として上位約20%を残す `quantile=0.80`。",
            "`mixed` 条件は、500万円以上相当の緩い下限を持つ個体と、複数条件が重なって",
            "上位13%から上位10%付近まで厳しくなる個体が混在する条件。",
            "`repro 20-39` は、同じ選択条件のまま再生産可能年齢だけを20〜39歳に狭めた感度分析。",
            "",
            "## 解釈",
            "",
            "この追試では、候補枠を小さくするのではなく、相対的な上位閾値を導入した。",
            "さらに、現実の条件設定は全員一様ではないと見なし、閾値を個体ごとにばらけさせた。",
            "現行モデルは全年齢で生産可能ではないが、基準の18〜45歳はまだ広い。",
            "20〜39歳条件では、フィードバックによる条件調整が遅れた場合の回復余地が小さくなる。",
            "これにより、actionable reserve があっても、ローカル候補が各個体の perceived/global comparison pool の",
            "閾値に届かなければ選択されない。",
            "",
            "これは「何人まで候補を見るか」ではなく、「比較基準に届かない候補を実行可能でも拒む」モデルである。",
            "したがって、前回よりも高望み仮説に近い操作になっている。",
            "",
            "また、A/B の後期未成立率は片側だけが極端に悪化するというより、相互選択の条件によって両側に波及する。",
            "これはペア形成が mutual selection だからである。片側が厳しく選ぶと、選ばれない側だけでなく、",
            "選ぶ側自身も成立可能な相手を失う。",
            "",
            "現時点の重要な留保として、モデルは一人が同時に複数の生殖ペアを持てないため、",
            "上位個体への繁殖集中は強く出にくい。ここで主に見えているのは、上位層への集中というより、",
            "相互選択の成立数が減るボトルネックである。",
            "",
        ]
    )


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

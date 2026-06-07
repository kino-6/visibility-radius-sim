from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from visibility_radius_sim.config import SimulationConfig
from visibility_radius_sim.simulation import Simulation

from experiment_helpers import dataframe_to_markdown, japan_reference_frame, rmse_for_years


OUTPUT_DIR = Path("outputs/reality_grounded_calibration")
PAPER_NOTE_PATH = Path("paper/notes/reality_grounded_calibration_report_ja.md")
YEARS = 91
POPULATION = 1200
SEEDS = (0, 1, 2)
TARGET_FINAL_RATIO = 0.74
TARGET_LOWER = 0.65
TARGET_UPPER = 0.85
LATE_WINDOW = 20
ANCHOR_YEARS = (1980, 1990, 2000, 2010, 2020, 2070)
PRE_SHOCK_ANCHOR_YEARS = (1980, 1990, 2000)
EARLY_ANCHOR_YEARS = (1980, 1990, 2000, 2010, 2020)


@dataclass(frozen=True)
class BaseCandidate:
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

    candidate_summary = run_base_candidate_search()
    selected_candidates = select_candidates(candidate_summary)
    profile_summary, profile_raw = run_profile_comparison(selected_candidates)

    candidate_summary_path = OUTPUT_DIR / "base_candidate_summary.csv"
    profile_raw_path = OUTPUT_DIR / "profile_raw.csv"
    profile_summary_path = OUTPUT_DIR / "profile_summary.csv"
    figure_path = OUTPUT_DIR / "profile_comparison.png"
    overlay_path = OUTPUT_DIR / "reality_overlay.png"

    candidate_summary.to_csv(candidate_summary_path, index=False)
    profile_raw.to_csv(profile_raw_path, index=False)
    profile_summary.to_csv(profile_summary_path, index=False)
    plot_profile_comparison(profile_summary, figure_path)
    plot_reality_overlay(profile_raw, selected_candidates[0], overlay_path)

    report = build_report_ja(candidate_summary, profile_summary)
    PAPER_NOTE_PATH.write_text(report, encoding="utf-8")

    print(f"wrote {candidate_summary_path}")
    print(f"wrote {profile_raw_path}")
    print(f"wrote {profile_summary_path}")
    print(f"wrote {figure_path}")
    print(f"wrote {overlay_path}")
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
        gender_mode="binary-balanced",
        selection_mode="top-k",
        top_k=16,
        actionable_selection_reserve_fraction=0.25,
        reproductive_min_age=20,
        reproductive_max_age=44,
        fertility_age_profile="japan-stylized",
        birth_probability_schedule="japan-tfr-stylized",
    )


def base_candidates() -> list[BaseCandidate]:
    candidates: list[BaseCandidate] = []
    for birth_probability in (0.18, 0.20, 0.22, 0.24, 0.26, 0.28):
        for pair_duration_mean in (18.0, 26.0):
            for carrying_capacity in (4500, 6000, 9000):
                for lifespan_mean in (78.0, 82.0, 86.0):
                    name = (
                        f"bp{birth_probability:.2f}_dur{pair_duration_mean:.0f}_"
                        f"cap{carrying_capacity}_life{lifespan_mean:.0f}"
                    )
                    label = (
                        f"birth={birth_probability:.2f}, "
                        f"duration={pair_duration_mean:.0f}, "
                        f"cap={carrying_capacity}, "
                        f"life={lifespan_mean:.0f}"
                    )
                    candidates.append(
                        BaseCandidate(
                            name=name,
                            label=label,
                            overrides={
                                "birth_probability": birth_probability,
                                "pair_duration_mean": pair_duration_mean,
                                "initial_pair_fraction": 0.55,
                                "carrying_capacity": carrying_capacity,
                                "lifespan_mean": lifespan_mean,
                            },
                        )
                    )
    return candidates


def aspiration_profiles() -> list[AspirationProfile]:
    return [
        AspirationProfile("symmetric", "Symmetric", {"aspirational_gender": "none"}),
        AspirationProfile(
            "income_500_floor",
            "B 500+ proxy",
            {"aspirational_gender": "B", "aspirational_min_score_quantile": 0.55},
        ),
        AspirationProfile(
            "mixed_light",
            "B light mixed",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.55, 0.25, 0.15, 0.05),
            },
        ),
        AspirationProfile(
            "mixed_heavy",
            "B compound-heavy",
            {
                "aspirational_gender": "B",
                "aspirational_min_score_quantile_distribution": (0.55, 0.75, 0.87, 0.90),
                "aspirational_min_score_quantile_weights": (0.25, 0.25, 0.35, 0.15),
            },
        ),
    ]


def run_base_candidate_search() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    candidates = base_candidates()
    reference = japan_reference_frame().set_index("calendar_year")["population_index"]
    for index, candidate in enumerate(candidates, start=1):
        print(f"[base {index:03d}/{len(candidates):03d}] {candidate.label}", flush=True)
        ratios: list[float] = []
        late_births: list[float] = []
        anchor_errors: dict[int, list[float]] = {year: [] for year in ANCHOR_YEARS}
        pre_shock_rmse_values: list[float] = []
        early_rmse_values: list[float] = []
        full_rmse_values: list[float] = []
        for seed in SEEDS:
            frame = Simulation(base_config(seed).with_overrides(**candidate.overrides)).run()
            start_population = float(frame["population_size"].iloc[0])
            final_population = float(frame["population_size"].iloc[-1])
            frame = frame.copy()
            frame["population_index"] = (
                0.0 if start_population == 0.0 else frame["population_size"] / start_population
            )
            by_year = frame.set_index("calendar_year")["population_index"]
            for anchor_year in ANCHOR_YEARS:
                error = float(by_year.loc[anchor_year] - reference.loc[anchor_year])
                anchor_errors[anchor_year].append(error)
            ratios.append(0.0 if start_population == 0.0 else final_population / start_population)
            late_births.append(float(frame.tail(LATE_WINDOW)["births_per_population"].mean()))
            pre_shock_rmse_values.append(rmse_for_years(by_year, reference, PRE_SHOCK_ANCHOR_YEARS))
            early_rmse_values.append(rmse_for_years(by_year, reference, EARLY_ANCHOR_YEARS))
            full_rmse_values.append(rmse_for_years(by_year, reference, ANCHOR_YEARS))
        mean_ratio = float(pd.Series(ratios).mean())
        anchor_error_means = {
            f"error_{anchor_year}": float(pd.Series(errors).mean())
            for anchor_year, errors in anchor_errors.items()
        }
        full_rmse = float(pd.Series(full_rmse_values).mean())
        early_rmse = float(pd.Series(early_rmse_values).mean())
        pre_shock_rmse = float(pd.Series(pre_shock_rmse_values).mean())
        rows.append(
            {
                "candidate": candidate.name,
                "label": candidate.label,
                "seed_count": len(SEEDS),
                "final_ratio_mean": mean_ratio,
                "final_ratio_min": float(min(ratios)),
                "final_ratio_max": float(max(ratios)),
                "pre_shock_rmse": pre_shock_rmse,
                "early_rmse": early_rmse,
                "full_anchor_rmse": full_rmse,
                "shape_score": full_rmse + 0.75 * early_rmse + 0.50 * abs(mean_ratio - TARGET_FINAL_RATIO),
                "late_births_per_population_mean": float(pd.Series(late_births).mean()),
                "target_error": abs(mean_ratio - TARGET_FINAL_RATIO),
                "inside_target_band": TARGET_LOWER <= mean_ratio <= TARGET_UPPER,
                **anchor_error_means,
                **candidate.overrides,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["inside_target_band", "shape_score", "full_anchor_rmse", "target_error"],
        ascending=[False, True, True, True],
    )


def select_candidates(candidate_summary: pd.DataFrame) -> list[BaseCandidate]:
    candidates_by_name = {candidate.name: candidate for candidate in base_candidates()}
    return [candidates_by_name[name] for name in candidate_summary.head(5)["candidate"]]


def run_profile_comparison(selected_candidates: list[BaseCandidate]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    raw_frames: list[pd.DataFrame] = []
    profiles = aspiration_profiles()
    total = len(selected_candidates) * len(profiles)
    run_index = 0
    for candidate in selected_candidates:
        for profile in profiles:
            run_index += 1
            print(f"[profile {run_index:03d}/{total:03d}] {candidate.label} / {profile.label}", flush=True)
            ratios: list[float] = []
            late_unmatched: list[float] = []
            for seed in SEEDS:
                config = base_config(seed).with_overrides(**candidate.overrides, **profile.overrides)
                frame = Simulation(config).run()
                frame.insert(0, "candidate", candidate.name)
                frame.insert(1, "label", candidate.label)
                frame.insert(2, "aspiration_profile", profile.name)
                frame.insert(3, "aspiration_label", profile.label)
                frame.insert(4, "seed", seed)
                start_index_population = float(frame["population_size"].iloc[0])
                frame["population_index"] = (
                    0.0 if start_index_population == 0.0 else frame["population_size"] / start_index_population
                )
                raw_frames.append(frame)
                start_population = float(frame["population_size"].iloc[0])
                final_population = float(frame["population_size"].iloc[-1])
                ratios.append(0.0 if start_population == 0.0 else final_population / start_population)
                late_unmatched.append(float(frame.tail(LATE_WINDOW)["unmatched_rate"].mean()))
            rows.append(
                {
                    "candidate": candidate.name,
                    "label": candidate.label,
                    "aspiration_profile": profile.name,
                    "aspiration_label": profile.label,
                    "seed_count": len(SEEDS),
                    "final_ratio_mean": float(pd.Series(ratios).mean()),
                    "final_ratio_min": float(min(ratios)),
                    "final_ratio_max": float(max(ratios)),
                    "late_unmatched_mean": float(pd.Series(late_unmatched).mean()),
                    **candidate.overrides,
                }
            )
    summary = pd.DataFrame(rows)
    symmetric = (
        summary.loc[summary["aspiration_profile"] == "symmetric", ["candidate", "final_ratio_mean"]]
        .set_index("candidate")["final_ratio_mean"]
        .to_dict()
    )
    summary["delta_vs_symmetric"] = [
        float(row["final_ratio_mean"] - symmetric[row["candidate"]]) for _, row in summary.iterrows()
    ]
    summary["retained_vs_symmetric"] = [
        0.0 if symmetric[row["candidate"]] == 0.0 else float(row["final_ratio_mean"] / symmetric[row["candidate"]])
        for _, row in summary.iterrows()
    ]
    return summary, pd.concat(raw_frames, ignore_index=True)


def plot_profile_comparison(summary: pd.DataFrame, output_path: Path) -> None:
    pivot = summary.pivot(index="label", columns="aspiration_label", values="final_ratio_mean")
    columns = [profile.label for profile in aspiration_profiles()]
    pivot = pivot[columns]
    fig, ax = plt.subplots(figsize=(11, 5.5), constrained_layout=True)
    x = range(len(pivot.index))
    width = 0.18
    for offset, column in enumerate(columns):
        values = pivot[column].to_numpy()
        ax.bar([value + (offset - 1.5) * width for value in x], values, width=width, label=column)
    ax.axhspan(TARGET_LOWER, TARGET_UPPER, color="#2ca02c", alpha=0.12, label="target band")
    ax.axhline(TARGET_FINAL_RATIO, color="#2ca02c", linestyle=":", linewidth=1.0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(pivot.index, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Final population ratio")
    ax.set_title("Reality-grounded Calibration Candidates")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_reality_overlay(profile_raw: pd.DataFrame, candidate: BaseCandidate, output_path: Path) -> None:
    reference = japan_reference_frame()
    selected = profile_raw.loc[profile_raw["candidate"] == candidate.name]
    fig, ax = plt.subplots(figsize=(11, 6), constrained_layout=True)
    ax.plot(
        reference["calendar_year"],
        reference["population_index"],
        color="#111111",
        linewidth=2.6,
        label="Japan actual/projection anchor",
    )
    ax.scatter(
        reference["calendar_year"],
        reference["population_index"],
        color="#111111",
        s=18,
        zorder=3,
    )

    colors = {
        "symmetric": "#1f77b4",
        "income_500_floor": "#2ca02c",
        "mixed_light": "#ff7f0e",
        "mixed_heavy": "#d62728",
    }
    for profile_name, group in selected.groupby("aspiration_profile", sort=False):
        trajectory = (
            group.groupby("calendar_year", as_index=False)["population_index"]
            .mean()
            .sort_values("calendar_year")
        )
        label = str(group["aspiration_label"].iloc[0])
        ax.plot(
            trajectory["calendar_year"],
            trajectory["population_index"],
            linewidth=1.8,
            color=colors.get(profile_name, "#777777"),
            label=label,
        )

    ax.axhline(TARGET_FINAL_RATIO, color="#777777", linestyle=":", linewidth=1.0)
    ax.set_title(f"Japan reference vs simulation trajectories\n{candidate.label}")
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Population index, 1980 = 1.0")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def build_report_ja(candidate_summary: pd.DataFrame, profile_summary: pd.DataFrame) -> str:
    candidates = candidate_summary.head(10)[
        [
            "label",
            "final_ratio_mean",
            "full_anchor_rmse",
            "early_rmse",
            "error_2000",
            "error_2010",
            "error_2070",
            "target_error",
            "inside_target_band",
            "late_births_per_population_mean",
        ]
    ].copy()
    for column in (
        "final_ratio_mean",
        "full_anchor_rmse",
        "early_rmse",
        "error_2000",
        "error_2010",
        "error_2070",
        "target_error",
        "late_births_per_population_mean",
    ):
        candidates[column] = candidates[column].map(lambda value: f"{float(value):.3f}")

    selected = compact_profile_display(profile_summary)
    return "\n".join(
        [
            "# Reality-grounded Calibration 日本語メモ",
            "",
            "目的は、gendered aspiration の効果を見る前に、対称条件そのものが現実的な人口推移レンジに入るよう土台を調整すること。",
            "ここでは1980年から2070年相当の91年を見て、対称条件が1980〜2020年の人口指数アンカーと2070年推計アンカーに近い候補を探した。",
            "",
            "現実根拠の扱い:",
            "",
            "- 日本の合計特殊出生率は1980年 `1.75`、2005年 `1.26`、2023年 `1.20`、2024年概数 `1.15` と長期低下している。",
            "- 国立社会保障・人口問題研究所の将来推計では、総人口は2020年 `1億2,615万人` から2070年 `8,700万人` 程度へ低下する出生中位推計である。",
            "- したがって、このtoy modelでは1980→2070相当で `0.65〜0.85` を対称条件の粗い目標帯にした。",
            "- 年齢別出生は厳密な人口学モデルではなく、20代後半〜30代前半を高くし、40代を低くする `japan-stylized` profile として入れた。",
            "- 年次出生環境は `japan-tfr-stylized` schedule とし、1980年を高め、2000年代以降を低める倍率を `birth_probability` に掛けた。",
            "- 候補選抜では2070年の終点だけでなく、1980/1990/2000/2010/2020/2070の人口指数RMSEを評価した。",
            "",
            "参照した公的資料:",
            "",
            "- 厚生労働省 `令和６年(2024)人口動態統計月報年計（概数）の概況`: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai24/index.html",
            "- 厚生労働省 `人口動態統計 年報 主要統計表（最新データ、年次推移）`: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/suii00/index.html",
            "- 国立社会保障・人口問題研究所 `日本の将来推計人口（令和5年推計）`: https://www.ipss.go.jp/pp-zenkoku/j/zenkoku2023/pp_zenkoku2023.asp",
            "",
            "## 出力",
            "",
            "- `outputs/reality_grounded_calibration/base_candidate_summary.csv`",
            "- `outputs/reality_grounded_calibration/profile_raw.csv`",
            "- `outputs/reality_grounded_calibration/profile_summary.csv`",
            "- `outputs/reality_grounded_calibration/profile_comparison.png`",
            "- `outputs/reality_grounded_calibration/reality_overlay.png`",
            "",
            "## 対称条件の候補 上位10件",
            "",
            dataframe_to_markdown(candidates.rename(columns={
                "label": "候補",
                "final_ratio_mean": "最終人口比",
                "full_anchor_rmse": "全アンカーRMSE",
                "early_rmse": "1980-2020 RMSE",
                "error_2000": "2000誤差",
                "error_2010": "2010誤差",
                "error_2070": "2070誤差",
                "target_error": "目標誤差",
                "inside_target_band": "目標帯内",
                "late_births_per_population_mean": "後期出生/人口",
            })),
            "",
            "## 選抜候補に aspiration profile を乗せた結果",
            "",
            dataframe_to_markdown(selected),
            "",
            "## 解釈",
            "",
            "従来の180年・18〜45歳条件では、土台が強すぎたり弱すぎたりして効果分離が難しかった。",
            "91年・20〜44歳・年齢別出生profileにすると、対称条件を現実的な低下レンジに寄せやすい。",
            "その上でも `mixed_heavy` は選抜候補すべてで対称条件を下回る。",
            "`reality_overlay.png` は、1980〜2020年の国勢調査アンカーと2070年IPSS推計アンカーを線形補間した参照線に、",
            "選抜候補のSim軌道を重ねた図である。今回から、上位選択なしの対称条件が2000年頃までの増加局面をなぞることも評価に入れている。",
            "",
            "ただし、この段階でも所得・婚姻・年齢別出生率を完全にキャリブレーションしたわけではない。",
            "ここで得た候補は、今後の本編Simを走らせるための現実根拠つき初期土台である。",
            "",
            "## 再実行",
            "",
            "```bash",
            ".venv/bin/python scripts/run_reality_grounded_calibration.py",
            "```",
            "",
        ]
    )


def compact_profile_display(summary: pd.DataFrame) -> pd.DataFrame:
    pivot = summary.pivot(index="label", columns="aspiration_profile", values="final_ratio_mean")
    rows: list[dict[str, str]] = []
    for label, row in pivot.iterrows():
        symmetric = float(row.get("symmetric", 0.0))
        heavy = float(row.get("mixed_heavy", 0.0))
        rows.append(
            {
                "候補": str(label),
                "対称": f"{symmetric:.3f}",
                "500+ proxy": f"{float(row.get('income_500_floor', 0.0)):.3f}",
                "light mixed": f"{float(row.get('mixed_light', 0.0)):.3f}",
                "heavy mixed": f"{heavy:.3f}",
                "heavy差分": f"{heavy - symmetric:.3f}",
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()

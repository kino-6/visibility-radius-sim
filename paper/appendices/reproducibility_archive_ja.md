# 再現性アーカイブ

この補遺は、working paper bundle で使ったシミュレーション条件を記録するための台帳である。目的は、本文の各図表について、利用データ、利用可能なスクリプト、seed 方針、主要パラメータを追えるようにすることである。

ただし、これはまだ working paper 用のアーカイブであり、出版品質の完全再現パッケージではない。初期探索の一部は、すべての scenario script が versioned file に昇格する前の作業セッション中に生成された。そのため、該当箇所は「探索出力アーカイブ」として明記する。

## 実行環境

- Repository: `visibility-radius-sim`
- 最新 gendered follow-up 作業前の基準 commit: `4339897`
- Package manager: `uv`
- Python: `>=3.11`
- Core dependencies: `numpy`, `pandas`, `matplotlib`
- Test dependency: `pytest`
- Lockfile: `uv.lock`

代表的な検証コマンド:

```bash
uv run pytest
```

このアーカイブ追加時点で、test suite は `22 passed` で通過している。

## 中核モデルファイル

- `src/visibility_radius_sim/agent.py`
- `src/visibility_radius_sim/config.py`
- `src/visibility_radius_sim/simulation.py`
- `src/visibility_radius_sim/metrics.py`
- `src/visibility_radius_sim/plotting.py`
- `src/visibility_radius_sim/cli.py`

## Baseline Scenario Parameters

SNS era の stylized baseline は次で定義される。

```python
SimulationConfig.for_scenario("sns-2000s")
```

保存済み parameter snapshot:

- `outputs/sns_2000s/sns_2000s.params.json`

主要 baseline 値:

| Parameter | Value |
|---|---:|
| `start_calendar_year` | `1980` |
| `years` | `80` |
| `initial_population` | `2500` |
| `seed` | `42` |
| `initial_age_distribution` | `japan-1980-stylized` |
| `location_model` | `clustered` |
| `location_cluster_count` | `12` |
| `initial_radius` | `0.02` |
| `max_radius` | `sqrt(2)` |
| `action_radius` | `0.12` |
| `radius_schedule` | `shock` |
| `visibility_expansion_mid_year` | `2007` |
| `visibility_expansion_duration_years` | `7.0` |
| `selection_mode` | `top-k` |
| `top_k` | `16` |
| `initial_candidate_pool_multiplier` | `1.0` |
| `max_candidate_pool_multiplier` | `300.0` |
| `phantom_candidate_mode` | `sampled` |
| `phantom_candidate_sample_cap` | `512` |
| `initial_pair_fraction` | `0.55` |
| `pair_duration_mean` | `18.0` |
| `birth_probability` | `0.12` |
| `carrying_capacity` | `9000` |

Baseline figure:

- `paper/figures/sns_2000s_simple.png`
- `outputs/sns_2000s/sns_2000s.csv`
- `outputs/sns_2000s/sns_2000s_simple.png`

## Main Paper Experiments

### Phantom Candidates and Actionable Reserve

Paper figure:

- `paper/figures/actionable_attention_comparison.png`

Paper data:

- `paper/data/actionable_attention_comparison_summary.csv`
- `outputs/actionable_attention/actionable_attention_comparison_summary.csv`

Seed 方針:

- paper/data には summary table のみ保存されている。
- 個別 seed 行はこの summary には含まれていない。
- 現在の保存状態では、探索的 scenario family として扱う。

条件:

- current sampled phantom behavior
- old behavior without phantom candidates
- actionable reserve `0.50`
- actionable reserve `0.75`

Archive status:

- 探索出力アーカイブ。
- 出版品質の再実行には、専用 script または CLI subcommand への昇格が必要。

### Protected Actionable-Slot Threshold

Paper figure:

- `paper/figures/reserve_threshold_slots_multiseed.png`

Paper data:

- `paper/data/reserve_threshold_slots_multiseed_summary.csv`
- `outputs/reserve_threshold/reserve_threshold_slots_multiseed_summary.csv`
- `outputs/reserve_threshold/reserve_threshold_slots_multiseed_raw.csv`

Seed 方針:

- multi-seed sweep。
- summary には seed 間の min/mean/max が含まれる。

条件:

- baseline SNS-like shock with sampled phantom candidates
- `top_k=16`
- protected actionable slots: `0,1,2,3,4,5,6,8`
- reserve fraction は `protected_slots / top_k`

Archive status:

- raw output は保存されているが、生成 script は単独ファイルとしては未保存。

### Long-Run Cultural Adaptation

Paper figure:

- `paper/figures/civilizational_adaptation_longrun.png`

Paper data:

- `paper/data/civilizational_adaptation_longrun_summary.csv`
- `outputs/civilizational_adaptation/`

Seed 方針:

- 保存済み summary は fixed-seed long-run comparison として扱う。

条件:

- no virtual filter
- weak actionable culture
- balanced actionable culture
- strong actionable culture
- local-only reference

Archive status:

- 探索出力アーカイブ。

### Region Boundary and Cross-Region Pairing

Paper figures:

- `paper/figures/regional_culture_crossing_comparison.png`
- `paper/figures/regional_culture_trajectories_by_culture.png`

Paper data:

- `paper/data/regional_culture_crossing_summary.csv`
- `outputs/regional_culture/`

Seed 方針:

- fixed-seed または small-run comparison として保存されている。
- raw trajectory CSV は保存されている。

条件:

- cross-region pairing allowed
- cross-region pairing blocked
- region-held reserve cultures compared by final culture share and trajectory

Archive status:

- 探索出力アーカイブ。

### Behavioral Action Interventions

Paper figure:

- `paper/figures/behavioral_action_interventions.png`

Paper data:

- `paper/data/behavioral_action_interventions_summary.csv`
- `paper/data/behavioral_action_interventions_seed42_summary.csv`
- `outputs/behavioral_interventions/`

Seed 方針:

- multi-seed summary と seed `42` summary の両方を保存。

条件:

- raw SNS / no discipline
- contact before scroll
- 48h move to reality
- full behavior bundle
- distance filter first
- weekly fixed local venue
- do not replay phantom candidates

Archive status:

- summary と raw CSV を保持した探索出力アーカイブ。

## Appendix Follow-Ups A-G

Script:

- `scripts/run_appendix_followups.py`

Paper appendix:

- `paper/appendix_followups/appendix_followups_report.md`
- `paper/appendix_followups/appendix_followups_report_ja.md`
- `paper/appendix_followups/data/appendix_followups_summary.csv`
- `paper/appendix_followups/data/appendix_followups_run_summary.csv`
- `paper/appendix_followups/figures/`

Output archive:

- `outputs/appendix_followups/appendix_followups_raw.csv`
- `outputs/appendix_followups/appendix_followups_run_summary.csv`
- `outputs/appendix_followups/appendix_followups_summary.csv`
- `outputs/appendix_followups/*.png`

Seed 方針:

- `SEEDS = (0, 1, 2)`

共通 base configuration:

- `SimulationConfig.for_scenario("sns-2000s")`
- `years = 180`
- `initial_population = 1200`
- `carrying_capacity = 4500`
- `worker_count = None`
- `max_auto_workers = 8`
- `parallel_threshold = 200`
- `metrics_precision = 6`

実験:

| Experiment | Main Question |
|---|---|
| `a_radius_alone` | radius expansion alone と actionability gap の切り分け |
| `b_selection_mode` | top-k と percentile selection の比較 |
| `c_candidate_multiplier` | perceived candidate-pool multiplier の影響 |
| `d_actionability_gap` | action radius 拡大で救済されるか |
| `e_reserve_threshold_robustness` | protected actionable-slot threshold が `top_k` を跨いで残るか |
| `f_cultural_overconstraint` | 現行モデルで reserve が強すぎるペナルティが出るか |
| `g_institutional_learning` | region-level learning が人口低下後に回復を起こせるか |

代表的な再実行コマンド:

```bash
.venv/bin/python scripts/run_appendix_followups.py
```

## Gendered Aspirational Selectivity Follow-Up

Script:

- `scripts/run_gendered_aspiration.py`

Paper notes:

- `paper/notes/gendered_aspiration_report.md`
- `paper/notes/gendered_aspiration_report_ja.md`

Output archive:

- `outputs/gendered_aspiration/gendered_aspiration_raw.csv`
- `outputs/gendered_aspiration/gendered_aspiration_run_summary.csv`
- `outputs/gendered_aspiration/gendered_aspiration_summary.csv`
- `outputs/gendered_aspiration/gendered_aspiration_summary.png`

Seed 方針:

- `SEEDS = (0, 1, 2)`

共通 base configuration:

- `SimulationConfig.for_scenario("sns-2000s")`
- `years = 180`
- `initial_population = 1200`
- `carrying_capacity = 4500`
- `gender_mode = "binary-balanced"`
- `selection_mode = "top-k"`
- `top_k = 16`
- `actionable_selection_reserve_fraction = 0.25`
- 基準の再生産年齢: `18-45`
- `aspirational_min_score_quantile` は条件ごとに変更
- mixed 条件では `aspirational_min_score_quantile_distribution` により個体ごとの閾値を設定

条件:

| Variant | Meaning |
|---|---|
| `symmetric_reserve_025` | A/B symmetric choice、相対上位閾値なし、reserve `0.25` |
| `b_income_500_floor` | B側は年収500万円以上を上限なしの下限条件として読み、`quantile=0.55` で近似 |
| `b_income_700_floor` | より高い単一条件の参照として `quantile=0.80` で近似 |
| `b_mixed_income_plus_light` | B側の個体閾値を `0.55/0.75/0.87/0.90` に分け、重み `55/25/15/5` |
| `b_mixed_income_plus_heavy` | 複合条件寄りとして同じ閾値に重み `25/25/35/15` |
| `b_mixed_income_plus_heavy_reserve_050` | compound-heavy 分布のまま reserve `0.50` |
| `b_mixed_income_plus_heavy_no_reserve` | compound-heavy 分布のまま reserve `0.00` |
| `symmetric_reserve_025_repro_20_39` | 対称条件のまま再生産年齢を `20-39` に制限 |
| `b_income_500_floor_repro_20_39` | 500万円以上 proxy のまま再生産年齢を `20-39` に制限 |
| `b_mixed_income_plus_light_repro_20_39` | light mixed profile のまま再生産年齢を `20-39` に制限 |
| `b_mixed_income_plus_heavy_repro_20_39` | compound-heavy profile のまま再生産年齢を `20-39` に制限 |

解釈上の制約:

- A/B labels は抽象ラベルであり、sex-specific reproductive biology を意味しない。
- 「高望み」は、候補枠を小さくする操作ではなく、perceived comparison pool 内の
  相対スコア閾値として実装している。
- 年収閾値はヒューリスティックな proxy であり、所得方程式としてキャリブレーションしたものではない。
  ここでの目的は、単一の下限条件と、個体差のある複合条件を比較することである。
- `20-39` の再生産年齢条件は感度分析である。年齢窓内の出生確率は年齢別に変えていないため、
  人口学的な出生率キャリブレーションではなく、タイムリミットのストレステストとして読む。

代表的な再実行コマンド:

```bash
.venv/bin/python scripts/run_gendered_aspiration.py
```

## Gendered Aspiration Calibration Robustness Sweep

Script:

- `scripts/run_gendered_robustness.py`

Paper notes:

- `paper/notes/gendered_robustness_report.md`
- `paper/notes/gendered_robustness_report_ja.md`

Output archive:

- `outputs/gendered_robustness/gendered_robustness_raw.csv`
- `outputs/gendered_robustness/gendered_robustness_run_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_heatmap.png`

Seed 方針:

- `SEEDS = (0, 1, 2)`

共通 base configuration:

- `SimulationConfig.for_scenario("sns-2000s")`
- `years = 180`
- `initial_population = 1200`
- `carrying_capacity = 4500`
- `gender_mode = "binary-balanced"`
- `selection_mode = "top-k"`
- `top_k = 16`
- `actionable_selection_reserve_fraction = 0.25`

一度に1軸ずつ変更した calibration axes:

- `birth_probability = 0.09, 0.18`
- `initial_pair_fraction = 0.35, 0.70`
- `pair_duration_mean = 10.0, 26.0`
- `max_candidate_pool_multiplier = 100.0, 500.0`
- `top_k = 32`
- `actionable_selection_reserve_fraction = 0.50`
- reproductive window `20-44` and `20-39`

Aspiration profiles:

- `symmetric`
- `income_500_floor`
- `mixed_light`
- `mixed_heavy`

解釈上の制約:

- これは demographic calibration ではなく robustness sweep である。
  toy model 内で、aspiration penalty の符号と規模がパラメータ摂動に耐えるかを見る。

代表的な再実行コマンド:

```bash
.venv/bin/python scripts/run_gendered_robustness.py
```

## Reality-grounded Japan-like Calibration

Script:

- `scripts/run_reality_grounded_calibration.py`
- shared helper: `scripts/experiment_helpers.py`

追加した named scenario:

- `SimulationConfig.for_scenario("japan-2070")`
- CLI: `uv run python -m visibility_radius_sim.cli run --scenario japan-2070 --output outputs/japan_2070.csv`

Paper note:

- `paper/notes/reality_grounded_calibration_report_ja.md`

Output archive:

- `outputs/reality_grounded_calibration/base_candidate_summary.csv`
- `outputs/reality_grounded_calibration/profile_raw.csv`
- `outputs/reality_grounded_calibration/profile_summary.csv`
- `outputs/reality_grounded_calibration/profile_comparison.png`
- `outputs/reality_grounded_calibration/reality_overlay.png`

Seed 方針:

- `SEEDS = (0, 1, 2)`

Calibration target:

- 91 simulated years, 1980-2070 inclusive.
- 対称条件の目標帯: final population ratio `0.65-0.85`, center `0.74`.
- これは日本の出生率低下とIPSS 2023全国将来人口推計を参照した toy-model index target であり、
  完全な人口学的キャリブレーションではない。
- `reality_overlay.png` は1980-2020年の国勢調査アンカーと2070年IPSS推計アンカーを人口指数化し、線形補間した参照線にSim軌道を重ねる。
- 現在の candidate selection は、2070年付近の終点だけでなく、1980/1990/2000/2010/2020/2070 の人口指数RMSEも評価する。
- `japan-tfr-stylized` birth probability schedule は、1980年を高め、2000年代以降を低める倍率を `birth_probability` に掛ける。

選抜した named-scenario parameters:

- `years = 91`
- `start_calendar_year = 1980`
- `initial_population = 1200`
- `reproductive_min_age = 20`
- `reproductive_max_age = 44`
- `fertility_age_profile = "japan-stylized"`
- `birth_probability = 0.22`
- `birth_probability_schedule = "japan-tfr-stylized"`
- `pair_duration_mean = 18.0`
- `initial_pair_fraction = 0.55`
- `carrying_capacity = 6000`
- `lifespan_mean = 78.0`
- `selection_mode = "top-k"`
- `top_k = 16`
- `actionable_selection_reserve_fraction = 0.25`

代表的な再実行コマンド:

```bash
.venv/bin/python scripts/run_reality_grounded_calibration.py
```

## Primary Hypothesis Validation

Script:

- `scripts/run_primary_hypothesis_validation.py`
- shared helper: `scripts/experiment_helpers.py`

Paper note:

- `paper/notes/primary_hypothesis_validation_report_ja.md`

Output archive:

- `outputs/primary_hypothesis_validation/hypothesis_validation_raw.csv`
- `outputs/primary_hypothesis_validation/hypothesis_validation_run_summary.csv`
- `outputs/primary_hypothesis_validation/hypothesis_validation_summary.csv`
- `outputs/primary_hypothesis_validation/hypothesis_validation.png`

Seed 方針:

- `SEEDS = (0, 1, 2)`

検証した仮説:

- Japan-like calibration を土台に、候補プールが local から SNS-like/global へ拡大すると、
  相対的上位層だけを足切りする aspiration profile の人口維持ペナルティが大きくなるかを見る。

条件:

- Base: `SimulationConfig.for_scenario("japan-2070")`
- Visibility: local visible/actionable, SNS-like expansion, global from start
- Aspiration: symmetric, B 500+ proxy, B light mixed, B compound-heavy

代表的な再実行コマンド:

```bash
.venv/bin/python scripts/run_primary_hypothesis_validation.py
```

## 残る再現性ギャップ

出版品質の reproduction package にするには、次が必要である。

1. すべての探索 scenario family を script または CLI subcommand に昇格する。
2. baseline だけでなく、すべての paper figure に per-run parameter JSON を保存する。
3. すべての summary table の横に raw per-seed outputs を保存する。
4. paper generation run ごとに exact git commit を記録する。
5. 全図表を一括再生成する `make paper` または `uv run ...` command を追加する。
6. Python version と package versions などの environment metadata を paper outputs に保存する。

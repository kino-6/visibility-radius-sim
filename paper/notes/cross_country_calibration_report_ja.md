# Cross-Country Calibration Note

## 目的

日本だけでなく、United States、United Kingdom、Sub-Saharan Africa aggregate について、1980-2024年の実測人口ラインを粗くなぞる土台パラメータを探索した。その上で、同じ土台に対して `visibility expansion x aspirational selection` の初回検証を行った。

これは人口予測ではない。現実人口には移民、医療、制度、都市化、教育、経済ショックなどが入っているが、このSimはそれらを明示的には持たない。ここで得たパラメータは「未モデル化要因を吸収した、比較実験用の粗い土台」と読む。

## データ

- 人口: World Bank `SP.POP.TOTL`
- 合計特殊出生率: World Bank `SP.DYN.TFRT.IN`
- 期間: 1980-2024
- 対象: `USA`, `GBR`, `SSF`
- `SSF` は国ではなく Sub-Saharan Africa aggregate。
- API URL template: `https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=20000`
- 参照: World Bank Data Help Desk API documentation, World Bank WDI metadata for `SP.POP.TOTL` and `SP.DYN.TFRT.IN`, World Bank country metadata for `SSF`。

World Bank API取得に失敗した場合は、スクリプト内のフォールバックアンカーを使う。今回の出力CSVには、各行の `population_source` と `tfr_source` を記録している。

## 方法

- 各地域の人口は `population_index = population / population_1980` で比較した。
- TFRは2000年値を1.0とする倍率に変換し、`birth_probability_schedule="anchored"` で年次出生確率に掛けた。
- US/UKは成熟人口の粗い年齢構造、Sub-Saharan Africaは若い拡大型の粗い年齢構造から初期化した。
- 1980, 1990, 2000, 2010, 2020, 2024 の人口指数RMSEが小さい候補を採用した。
- キャリブレーションSeed: (0, 1)
- 検証Seed: (0, 1, 2)

## 採用パラメータ

| region_label | anchor_rmse_mean | final_ratio_mean | birth_probability | carrying_capacity | pair_duration_mean | lifespan_mean |
| --- | --- | --- | --- | --- | --- | --- |
| United Kingdom | 0.045 | 1.1512 | 0.22 | 3200.0 | 26.0 | 78.0 |
| Sub-Saharan Africa | 0.068 | 3.2535 | 0.44 | 12000.0 | 26.0 | 62.0 |
| United States | 0.0199 | 1.4703 | 0.3 | 4800.0 | 20.0 | 84.0 |

## 土台線と現実線の照合

下表は、採用パラメータの `Local visible/actionable + Symmetric` 条件を、World Bank人口指数と比較したもの。`diff` は `sim_index - actual_index`。

| region_label | calendar_year | actual_index | sim_index | diff |
| --- | --- | --- | --- | --- |
| United Kingdom | 1980 | 1.0 | 1.0 | 0.0 |
| United Kingdom | 1990 | 1.017 | 1.056 | 0.039 |
| United Kingdom | 2000 | 1.046 | 1.099 | 0.054 |
| United Kingdom | 2010 | 1.115 | 1.149 | 0.035 |
| United Kingdom | 2020 | 1.185 | 1.158 | -0.027 |
| United Kingdom | 2024 | 1.229 | 1.148 | -0.081 |
| Sub-Saharan Africa | 1980 | 1.0 | 1.0 | 0.0 |
| Sub-Saharan Africa | 1990 | 1.337 | 1.342 | 0.006 |
| Sub-Saharan Africa | 2000 | 1.747 | 1.781 | 0.034 |
| Sub-Saharan Africa | 2010 | 2.294 | 2.382 | 0.088 |
| Sub-Saharan Africa | 2020 | 2.998 | 3.04 | 0.042 |
| Sub-Saharan Africa | 2024 | 3.311 | 3.294 | -0.016 |
| United States | 1980 | 1.0 | 1.0 | 0.0 |
| United States | 1990 | 1.099 | 1.107 | 0.008 |
| United States | 2000 | 1.242 | 1.262 | 0.02 |
| United States | 2010 | 1.362 | 1.376 | 0.015 |
| United States | 2020 | 1.459 | 1.433 | -0.026 |
| United States | 2024 | 1.497 | 1.464 | -0.033 |

## 仮説検証の初回結果

下表は compound-heavy aspiration、つまり相対的に上位スコア候補へ強く寄る条件を、同じvisibility条件の symmetric 条件と比較したもの。

| region_label | visibility_label | final_ratio_mean | delta_final_ratio_vs_symmetric | late_births_per_population | delta_late_births_vs_symmetric |
| --- | --- | --- | --- | --- | --- |
| United Kingdom | Global from start | 0.9094 | -0.2135 | 0.0053 | -0.0048 |
| United Kingdom | Local visible/actionable | 1.1095 | -0.0385 | 0.011 | -0.0001 |
| United Kingdom | SNS-like expansion | 0.9451 | -0.0636 | 0.0044 | -0.0045 |
| Sub-Saharan Africa | Global from start | 2.0597 | -1.2599 | 0.0187 | -0.0091 |
| Sub-Saharan Africa | Local visible/actionable | 3.2559 | -0.0383 | 0.0269 | 0.0 |
| Sub-Saharan Africa | SNS-like expansion | 2.2189 | -0.3062 | 0.0143 | -0.0103 |
| United States | Global from start | 1.0558 | -0.4047 | 0.0076 | -0.006 |
| United States | Local visible/actionable | 1.4176 | -0.0466 | 0.0129 | -0.0008 |
| United States | SNS-like expansion | 1.1329 | -0.0732 | 0.0067 | -0.0037 |

## 追加可視化

- `cross_country_scenario_trajectories.png`: World Bank実測線、Local土台線、SNS-like条件、Global条件の人口指数推移を地域別に重ねた図。
- `cross_country_mechanism_metrics.png`: 同じ条件について、出生率 proxy と未マッチ率の推移を並べた図。

この検証は、採用パラメータを土台としてすでに実行済みである。比較軸は次の通り。

- `Calibrated local base`: 現実人口指数をなぞるための土台条件。Local visible/actionable かつ symmetric。
- `SNS-like, symmetric`: 候補プールは拡大するが、片側の相対上位志向を追加しない条件。
- `SNS-like, compound-heavy`: 候補プール拡大に、相対上位志向が強い個体分布を組み合わせた条件。
- `Global, compound-heavy`: 初期からグローバル比較がある強いストレス条件。

## 読み方

`delta_final_ratio_vs_symmetric` が負なら、同じ地域土台・同じvisibility条件の symmetric 条件より、最終人口指数が低い。`delta_late_births_vs_symmetric` が負なら、終盤10年の出生率も低い。

今回の焦点は、国や地域そのものの優劣ではなく、同じ土台の中で「候補プール拡大」と「相対上位志向」が組み合わさったときに、人口維持に必要なペア形成や出生が削られるかどうかである。

## 人類側の含意

文明退化なしに人口維持を狙うなら、SNS、検索、推薦、グローバル可視性を捨てるより、仮想世界の比較能力を現実世界の行動可能性へ接続し直す方が自然である。

このSimの言葉では、対策の中心は `actionable_selection_reserve` の社会実装になる。非行動可能な上位比較対象が全ての注意枠を奪わないようにし、実際に会える、生活圏が重なる、相互関心がある、時間制約内で関係が進む候補を選択枠に残す。

詳細は `paper/notes/human_population_maintenance_strategy_ja.md` に分けた。

## 出力

- 観測データ: `outputs/cross_country_calibration/observed_population_fertility.csv`
- 探索結果: `outputs/cross_country_calibration/calibration_summary.csv`
- 採用候補: `outputs/cross_country_calibration/selected_calibrations.csv`
- 検証Raw: `outputs/cross_country_calibration/hypothesis_raw.csv`
- 検証Summary: `outputs/cross_country_calibration/hypothesis_summary.csv`
- キャリブレーション図: `outputs/cross_country_calibration/cross_country_calibration.png`
- 仮説検証図: `outputs/cross_country_calibration/cross_country_hypothesis.png`
- 推移比較図: `outputs/cross_country_calibration/cross_country_scenario_trajectories.png`
- メカニズム図: `outputs/cross_country_calibration/cross_country_mechanism_metrics.png`
- 人類側の結論ノート: `paper/notes/human_population_maintenance_strategy_ja.md`

## 注意点

- これはWorld Bank実測線に形を寄せた抽象モデルであり、因果推定でも将来予測でもない。
- 移民を明示していないため、US/UKの人口増は出生・死亡・キャパシティ・ペア継続などの抽象パラメータがまとめて吸収している。
- Sub-Saharan Africaは集計地域なので、国別の制度・都市化・年齢構造の差は潰れている。
- 2024以降の将来外挿は今回行っていない。

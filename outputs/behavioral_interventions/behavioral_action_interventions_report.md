# Behavioral Action Interventions Report

## Question

このレポートは、これまでのシミュレーションから出てきた行動教訓が、モデル上で本当に効くのかを確認するための比較です。

検証した問いは次です。

> SNS 的な候補プール拡大が起きても、具体的な行動ルールによって「実際に会える候補」への選択圧を残せば、人口崩壊を避けられるのか？

これは現実の人間行動を直接説明するものではなく、抽象モデル上の介入比較です。

## Setup

- ベースシナリオ: `sns-2000s`
- 期間: 240 年
- 比較 seed: `0, 1, 2`
- 詳細軌跡: `seed=42`
- 人口指標: 1980 年時点を `1.0` とする population index
- 主な観察指標:
  - `final_ratio`: 最終人口 / 初期人口
  - `late_unmatched_mean`: 終盤の unmatched rate
  - `late_births_per_eligible_mean`: 終盤の eligible agent あたり出生数
  - `late_selected_actionable_mean`: top-k 候補スロットのうち、実際に到達可能な候補の割合
  - `late_phantom_share_mean`: top-k 候補スロットのうち、phantom candidate の割合

## Tested Actions

| Variant | 行動教訓としての意味 | モデル上の近似 |
|---|---|---|
| Raw SNS / no discipline | 何もしない | SNS 候補拡大をそのまま受ける |
| Contact before scroll | スクロール前に現実接触枠を確保する | top-k の一部を actionable candidates に予約 |
| Distance filter first | 評価前に距離で絞る | visibility radius を local に固定 |
| Do not replay phantom candidates | 会えない候補を脳内で反復しない | phantom sample cap を制限 |
| Weekly fixed local venue | 毎週同じ地域的な場に出る | action radius と actionable reserve を増やす |
| 48h move to reality | オンライン候補を短時間で現実接触へ移す | actionable reserve + phantom cap |
| Full behavior bundle | 上記をまとめた行動束 | reserve, phantom cap, action radius を同時に変更 |

## Multi-Seed Results

| Variant | Final ratio mean | Final ratio range | Late unmatched | Births / eligible | Actionable selected | Phantom share |
|---|---:|---:|---:|---:|---:|---:|
| Contact before scroll | 0.735 | 0.723-0.743 | 0.295 | 0.0356 | 0.245 | 0.754 |
| 48h move to reality | 0.710 | 0.672-0.743 | 0.299 | 0.0353 | 0.246 | 0.642 |
| Full behavior bundle | 0.705 | 0.675-0.721 | 0.300 | 0.0351 | 0.496 | 0.468 |
| Distance filter first | 0.515 | 0.469-0.563 | 0.308 | 0.0378 | 0.202 | 0.791 |
| Weekly fixed local venue | 0.432 | 0.387-0.494 | 0.356 | 0.0350 | 0.250 | 0.750 |
| Do not replay phantom candidates | 0.067 | 0.061-0.073 | 0.381 | 0.0379 | 0.081 | 0.664 |
| Raw SNS / no discipline | 0.001 | 0.000-0.004 | 0.235 | 0.0106 | 0.003 | 0.188 |

## Reading

### 1. The core lesson mostly survives the test

Raw SNS はほぼ崩壊しました。  
一方で、現実接触枠を残す介入は最終人口を大きく改善しました。

特に `Contact before scroll` は平均 final ratio が `0.735` で最も高く、`48h move to reality` と `Full behavior bundle` も `0.70` 前後で崩壊を回避しました。

このモデルでは、「SNS を見る時間そのもの」よりも、候補評価の前に actionable な候補を残すことが重要です。

### 2. Phantom を減らすだけでは足りない

`Do not replay phantom candidates` は、raw SNS よりは改善しますが、final ratio は `0.067` に留まりました。

つまり、会えない候補の反復を減らすだけでは弱いです。  
重要なのは、top-k 選択の中に「実際に会える候補」が入る構造を先に作ることです。

### 3. Local filter alone is partially effective

`Distance filter first` は final ratio `0.515` まで改善しました。  
ただし、`Contact before scroll` より弱いです。

これは、近場に絞るだけでは「候補評価のスロット」がまだ phantom や過剰比較に食われるためです。  
距離フィルタは効くが、actionable reserve ほど直接ではありません。

### 4. Full bundle is not best in this parameterization

`Full behavior bundle` は崩壊を防ぎますが、`Contact before scroll` を上回りませんでした。

これは少し面白い結果です。  
現行モデルでは、制約を重ねすぎると候補探索が狭くなり、出生率の上振れも削る可能性があります。

したがって、このモデル上の最適教訓は「全部を厳しく制限する」ではなく、

> 候補評価の中に、必ず現実到達可能な枠を確保する

に近いです。

### 5. Unmatched rate alone is misleading

Raw SNS の終盤 unmatched rate は低く見えますが、これは改善ではありません。  
人口がほぼ消えて、eligible population が崩れた後の指標だからです。

この比較では unmatched rate よりも、

- population index
- births per eligible
- selected actionable share

を合わせて読む必要があります。

## Conclusion

今回の Sim では、行動教訓は概ね支持されました。

最も強い教訓は次です。

> 仮想候補を完全に遮断するより、評価スロットの中に「現実に接触できる候補」を先に確保するほうが効く。

人間向けに言い換えるなら、「SNS は一日何分まで」ではなく、

- 候補を見る前に現実接触の予定を入れる
- 近場・紹介・定期的な場を先に通す
- オンラインで気になった候補は短期間で現実接触へ移す
- 会えない候補を評価基準として保存し続けない

という方向です。

ただし、このレポートは抽象モデルの結果です。  
現実の出生率には経済、住宅、労働、教育、制度、価値観、避妊、結婚制度など多数の要因が入ります。ここで確認できたのは、あくまで「候補プール拡大による top-k 選択の歪み」に対する行動介入のモデル内効果です。

## Outputs

- `outputs/behavioral_interventions/behavioral_action_interventions_summary.csv`
- `outputs/behavioral_interventions/behavioral_action_interventions_seed42_summary.csv`
- `outputs/behavioral_interventions/behavioral_action_interventions_raw.csv`
- `outputs/behavioral_interventions/behavioral_action_interventions.png`

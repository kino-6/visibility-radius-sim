# Gendered Aspiration Robustness Sweep 日本語メモ

この追試は、現行の gendered aspiration 結果が都合のよいキャリブレーションに依存していないかを見るための探索である。
出生確率、初期ペア率、ペア期間、SNS的候補倍率、top-k、actionable reserve、再生産年齢窓を個別に振った。

これは人口学的なキャリブレーションではない。既存の `sns-2000s` toy scenario に対する機構の頑健性チェックである。

## 出力

- `outputs/gendered_robustness/gendered_robustness_raw.csv`
- `outputs/gendered_robustness/gendered_robustness_run_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_summary.csv`
- `outputs/gendered_robustness/gendered_robustness_heatmap.png`

## 簡易結果表

| 条件変更 | 対称 | 500+ proxy | light mixed | heavy mixed | heavy差分 | heavy/対称 |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline calibration | 0.758 | 0.635 | 0.438 | 0.222 | -0.537 | 0.292 |
| Lower birth probability | 0.231 | 0.115 | 0.089 | 0.051 | -0.180 | 0.221 |
| Higher birth probability | 1.813 | 1.745 | 1.472 | 1.259 | -0.554 | 0.695 |
| Lower initial pair stock | 0.813 | 0.560 | 0.443 | 0.193 | -0.621 | 0.237 |
| Higher initial pair stock | 0.758 | 0.635 | 0.438 | 0.222 | -0.537 | 0.292 |
| Shorter pair duration | 0.915 | 0.672 | 0.483 | 0.297 | -0.618 | 0.324 |
| Longer pair duration | 0.849 | 0.521 | 0.406 | 0.169 | -0.680 | 0.199 |
| Lower SNS pool multiplier | 0.793 | 0.646 | 0.414 | 0.225 | -0.567 | 0.284 |
| Higher SNS pool multiplier | 0.786 | 0.653 | 0.419 | 0.206 | -0.580 | 0.262 |
| Larger top-k capacity | 0.832 | 0.648 | 0.524 | 0.265 | -0.567 | 0.318 |
| Reserve 50% | 0.832 | 0.648 | 0.524 | 0.265 | -0.567 | 0.318 |
| Reproductive window 20-44 | 0.515 | 0.315 | 0.219 | 0.094 | -0.422 | 0.182 |
| Reproductive window 20-39 | 0.141 | 0.065 | 0.044 | 0.011 | -0.130 | 0.080 |

## 読み方

`対称` はA/Bに高望み閾値を入れない参照条件。`500+ proxy` はB側だけ `quantile=0.55`。
`light mixed` はB側の個体差を軽く入れた条件、`heavy mixed` は複合条件側に重みを寄せた条件。
`heavy差分` は `heavy mixed - 対称` で、負なら高望み混合による追加低下を意味する。

## 解釈

符号はかなり安定している。tested calibrations の全条件で、heavy mixed は対称条件より低い。
一方で、低下幅は安定していない。出生確率、再生産年齢窓、reserve/top-k は、
結果が「低下」に見えるか「崩壊」に見えるかを大きく変える。
なお `Higher initial pair stock` はこの設定では基準条件と同じ結果になった。
初期ペア形成が既に飽和しており、追加指定が実質的に効いていない可能性がある。

したがって、現時点で言えるのは「上位志向混合の方向性は頑健そうだが、
どの程度危険かはキャリブレーション依存が大きい」ということ。
特に 20-39 の年齢窓と低出生確率は、対称条件自体を弱くするため、
高望み効果だけを分離して読むにはさらなる再キャリブレーションが必要である。

## 再実行

```bash
.venv/bin/python scripts/run_gendered_robustness.py
```

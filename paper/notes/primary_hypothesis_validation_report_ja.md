# Primary Hypothesis Validation 日本語メモ

## 検証した仮説

候補プールが local から SNS-like/global へ拡大すると、相対的上位層だけを足切りする aspiration profile は、
上位選択なしの対称条件に比べて人口維持を悪化させる。特に、複合条件を重く見る `B compound-heavy` で悪化が大きくなる。

この検証は現実因果の証明ではない。Japan-like calibration を土台にした toy model 内の機構検証である。

## 条件

- Base: `SimulationConfig.for_scenario("japan-2070")`
- Seeds: `0, 1, 2`
- Visibility: local visible/actionable, SNS-like expansion, global from start
- Aspiration: symmetric, B 500+ proxy, B light mixed, B compound-heavy
- Output: `outputs/primary_hypothesis_validation/`

## 結果表

| 可視性条件 | aspiration | 最終人口比 | 対称差分 | 対称比 | 参照RMSE | 後期B未成立率 | 後期出生/人口 | 後期現実候補選択率 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local visible/actionable | Symmetric | 0.945 | 0.000 | 1.000 | 0.126 | 0.329 | 0.008 | 0.757 |
| Local visible/actionable | B 500+ proxy | 0.925 | -0.020 | 0.978 | 0.110 | 0.332 | 0.008 | 0.650 |
| Local visible/actionable | B light mixed | 0.907 | -0.038 | 0.959 | 0.084 | 0.297 | 0.008 | 0.667 |
| Local visible/actionable | B compound-heavy | 0.899 | -0.046 | 0.952 | 0.088 | 0.302 | 0.008 | 0.637 |
| SNS-like expansion | Symmetric | 0.740 | 0.000 | 1.000 | 0.020 | 0.324 | 0.009 | 0.094 |
| SNS-like expansion | B 500+ proxy | 0.632 | -0.108 | 0.854 | 0.051 | 0.358 | 0.007 | 0.096 |
| SNS-like expansion | B light mixed | 0.584 | -0.157 | 0.789 | 0.070 | 0.400 | 0.006 | 0.096 |
| SNS-like expansion | B compound-heavy | 0.449 | -0.291 | 0.607 | 0.124 | 0.522 | 0.004 | 0.087 |
| Global from start | Symmetric | 0.942 | 0.000 | 1.000 | 0.120 | 0.310 | 0.008 | 0.116 |
| Global from start | B 500+ proxy | 0.725 | -0.217 | 0.770 | 0.029 | 0.349 | 0.008 | 0.103 |
| Global from start | B light mixed | 0.651 | -0.291 | 0.691 | 0.042 | 0.369 | 0.007 | 0.104 |
| Global from start | B compound-heavy | 0.509 | -0.433 | 0.540 | 0.103 | 0.474 | 0.006 | 0.100 |

## Heavy profile の要約

| 可視性条件 | 対称差分 | 対称比 |
| --- | --- | --- |
| Local visible/actionable | -0.046 | 0.952 |
| SNS-like expansion | -0.291 | 0.607 |
| Global from start | -0.433 | 0.540 |

## 解釈

`SNS-like expansion` では、対称条件はJapan referenceに近い人口線を維持するが、
`B compound-heavy` は最終人口比を大きく押し下げる。
この結果は、単なる出生環境の悪化だけでなく、拡大した候補プール上での上位足切りが追加的な人口抑制として働く、という仮説を支持する。

ただし、local visible/actionable でも aspiration penalty は完全には消えない。
これは、このモデルでは aspiration が物理距離ではなく候補集合内の相対順位足切りとして実装されているためである。
したがって、より強い主張には、local 条件での認知上限・反復接触・学習緩和を別途モデル化する必要がある。

## 図

- `outputs/primary_hypothesis_validation/hypothesis_validation.png`

## 再実行

```bash
.venv/bin/python scripts/run_primary_hypothesis_validation.py
```

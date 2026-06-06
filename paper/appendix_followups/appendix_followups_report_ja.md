# 補遺追試 結果レポート

このレポートは、working paper の中心メカニズムが「Radius 拡大そのもの」なのか、それとも「actionability gap と bounded attention の相互作用」なのかを確認するために実施した七つの追試をまとめる。

## 出力ファイル

- `outputs/appendix_followups/appendix_followups_raw.csv`
- `outputs/appendix_followups/appendix_followups_run_summary.csv`
- `outputs/appendix_followups/appendix_followups_summary.csv`
- `outputs/appendix_followups/appendix_followups_overview.png`

## この文書の読み方

この補遺は、モデル内の専門用語が多い。先に用語を押さえると読みやすい。

大きな問いは次である。

```text
候補がたくさん見えるようになること自体が悪いのか。
それとも、見える候補の多くが実際には行動不能で、
その候補が限られた注意枠を奪うことが悪いのか。
```

今回の追試は、後者を支持する。

## 用語注釈

**Radius / 可視半径**  
エージェントが候補として「見える」範囲。現実の距離そのものというより、観察・比較できる範囲の抽象表現である。SNS では物理的距離よりも、タイムライン、検索、推薦、プロフィール閲覧によって可視範囲が広がる。

**Visibility / 可視性**  
候補を見られること。見えるだけで、実際に会える・関係を進められるとは限らない。

**Action radius / 行動半径**  
実際に接触・調整・ペア形成できる範囲。現実では、距離、時間、信頼、紹介、生活圏、予定調整、文化的近さなどをまとめた概念に近い。

**Actionability / 実行可能性**  
候補が「現実に関係を進められる候補」かどうか。単に魅力的に見える候補ではなく、会える、相互に選べる、関係を進められる候補を指す。

**Actionability gap / 実行可能性ギャップ**  
見える候補と、実際に行動可能な候補の差。例えば、世界中の候補が見えるが、実際に会えるのは近場の少数だけ、という状態。

**Phantom candidate / 仮想候補・非実行可能候補**  
見える、比較できる、魅力的に感じるかもしれないが、実際にはペア形成できない候補。モデルでは、SNS や推薦システムによって増える「比較対象だが実行不能な候補」を表す。

**Phantom comparison / 仮想比較**  
phantom candidate と現実候補を同じ評価枠で比較してしまうこと。これが起きると、実際に会える候補が上位評価枠から押し出される。

**Bounded attention / 有限注意**  
人間やエージェントが同時に真剣に評価できる候補数には限界がある、という仮定。無限に候補を見られても、意思決定に使える上位枠は限られる。

**Top-k attention / 上位k件注意**  
候補全体のうち、上位 `k` 件だけを真剣な候補として扱う選択方式。例えば `top_k=16` なら、どれだけ候補が増えても上位16件だけが注意枠に残る。

**Percentile selection / パーセンタイル選択**  
候補の上位何%かを選ぶ方式。候補数が増えると選択枠も増える。top-k よりは注意枠が広がるが、今回の追試ではそれだけでは救済にならなかった。

**Reserve / 予約枠**  
top-k のうち一部を、実際に行動可能な候補のために確保する仕組み。例えば `top_k=16` で protected slots が 4 なら、上位16枠のうち4枠は actionable candidates 用に保護される。

**Protected actionable slots / 保護された実行可能候補枠**  
phantom candidate に奪われないように守られた、現実候補用の注意枠。この補遺で最も重要な変数の一つ。

**Reserve fraction / 予約比率**  
top-k の何割を actionable candidates 用に守るか。例えば `top_k=16` で `reserve_fraction=0.25` なら、おおむね4枠が保護される。

**Candidate-pool multiplier / 候補プール倍率**  
実際の近場候補数に対して、知覚される候補数が何倍に増えるか。SNS では距離が少し広がるというより、候補数が何十倍・何百倍に増えることが重要かもしれない、という問題意識から入っている。

**Final population ratio / 最終人口比**  
シミュレーション開始時に対して、終了時の人口が何倍か。`1.0` なら維持、`0.5` なら半減、`0.0` なら実質崩壊である。

**Late births/eligible / 終盤の生殖可能個体あたり出生数**  
終盤に、eligible agents に対してどれくらい出生が起きているか。人口がほぼ消えた後は分母が小さくなり、解釈が不安定になる。

**Selected actionable / 選ばれた候補のうち実行可能だった割合**  
上位注意枠に残った候補のうち、実際に行動可能な候補の割合。高いほど、注意が現実候補に残っている。

**Phantom share / phantom が注意枠を占めた割合**  
上位注意枠のうち、phantom candidates が占めた割合。高いほど、現実に会える候補が仮想比較に押し出されている。

**Institutional learning / 制度的学習**  
個人ではなく、地域や制度が人口低下を観察して行動ルールを調整すること。このモデルでは、地域ごとの reserve culture が時間とともに強くなる仕組みとして近似した。

**Preadapted culture / 事前適応済み文化**  
可視性ショックが起きる前から、actionable candidates を保護する文化・制度を持っている状態。追試Gでは、制度学習の比較対象として使っている。

## 表の読み方

各表は、複数 seed の平均結果である。

- `seed数`: 何種類の乱数 seed で試したか。
- `最終人口比 平均`: 終了時人口 / 開始時人口の平均。最重要指標。
- `最小` / `最大`: seed 間の結果の幅。
- `終盤 births/eligible`: 終盤の出生力の目安。ただし崩壊後は解釈に注意。
- `終盤 selected actionable`: 注意枠に残った実行可能候補の割合。
- `終盤 phantom share`: 注意枠を phantom candidates が占めた割合。
- `終盤 visibility/action gap`: 見える候補と行動可能候補の差。

まず `最終人口比 平均` を見て、その後に `selected actionable` と `phantom share` を見るとよい。`unmatched` や出生率だけを見ると、崩壊後の分母アーティファクトで誤読しやすい。

## 主要知見

1. **Radius 単独は主な崩壊メカニズムではない。**

   Local visibility/local action は維持された (`final_ratio_mean=1.055`)。Global visibility/global action も一定の生存性を保った (`0.760`)。大きな低下は global visibility と local action が組み合わさった場合 (`0.314`) に現れ、phantom comparison を含む full SNS shock では完全崩壊した (`0.000`)。

2. **Candidate-pool multiplier は空間的 radius より強い。**

   phantom multiplier なしの `1x` では、低下しつつも生存した (`0.381`)。一方、`10x` 以上では no-reserve top-k attention のもとで崩壊した。SNS 的な圧力は、距離そのものよりも「知覚される候補数の倍率」として表す方が強く出る。

3. **top-k bounded attention は脆いが、percentile selection だけでは救済にならない。**

   top-k variants は reserve なしでは崩壊した。percentile selection は selectivity が高い場合に少し改善した (`0.18 -> 0.055`) が、生存水準には届かなかった。このパラメータでは、選択枠を広げるだけでは phantom displacement を解けない。

4. **phantom competition が極端な場合、action radius を広げるだけでは救済にならない。**

   action-radius sweep は、global action radius でも崩壊した。したがって actionability gap は重要だが、それだけでは説明として不十分である。phantom comparison が top-k attention を占有するなら、action radius を広げても、attention slots を保護しない限り崩壊しうる。

5. **protected actionable slots は top-k サイズを変えても頑健に効く。**

   `top_k=8,16,32,64` のいずれでも、protected slots が 0 の条件は崩壊またはほぼ崩壊した。2 slots で部分的生存に入り、4 slots で多くの場合ほぼ生存水準に達した。これは reserve fraction よりも protected slots 数が重要であることを支持する。

6. **現行モデルでは overconstraint penalty は出ていない。**

   threshold を超えた reserve fraction は、viability を下げなかった。つまり現行モデルでは、強い actionable reserve culture に十分なコストがまだ入っていない。将来的には search quality、preference mismatch、opportunity cost などを導入して、強すぎる文化が逆効果になるかを検証する必要がある。

7. **制度的・地域的 learning は、十分早く強ければ効く。**

   no learning は崩壊した。slow learning は `0.667` まで回復し、fast learning は `0.945` まで回復した。これは preadapted reserve reference (`0.996`) に近い。個人全員が意識的に仮想世界ミスマッチを理解しなくても、地域・制度が早期に reserve norms を調整できれば崩壊を大きく緩和できる。

## 注意

崩壊シナリオでは、終盤の rate が `0.000` になるものが多い。これは安定状態を意味しない。eligible population が崩壊した後の分母アーティファクトである。崩壊条件では、まず final population ratio と minimum population ratio を読むべきである。

## A. Radius 単独効果

| 条件 | seed数 | 最終人口比 平均 | 最小 | 最大 | 終盤 births/eligible | 終盤 selected actionable | 終盤 phantom share | 終盤 visibility/action gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local visibility, local action | 3 | 1.055 | 0.983 | 1.147 | 0.034 | 0.960 | 0.000 | 0.000 |
| Global visibility, global action | 3 | 0.760 | 0.740 | 0.796 | 0.035 | 1.000 | 0.000 | 0.000 |
| Global visibility, local action, no phantom | 3 | 0.314 | 0.231 | 0.415 | 0.031 | 0.132 | 0.000 | 0.820 |
| Full SNS shock with phantom | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

図: `figures/a_radius_alone_summary.png`

解釈: Radius 拡大だけでは崩壊しない。Global visibility でも action が global なら一定の生存性がある。崩壊は、global に見えるが local にしか行動できない状態で始まり、phantom comparison が加わると極端化する。

## B. Top-k vs Percentile Selection

| 条件 | seed数 | 最終人口比 平均 | 最小 | 最大 | 終盤 births/eligible | 終盤 selected actionable | 終盤 phantom share | 終盤 visibility/action gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Top-k 8 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Top-k 16 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Top-k 32 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Percentile 0.02 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Percentile 0.08 | 3 | 0.003 | 0.001 | 0.007 | 0.002 | 0.003 | 0.226 | 0.089 |
| Percentile 0.18 | 3 | 0.055 | 0.027 | 0.107 | 0.019 | 0.009 | 0.960 | 0.541 |

図: `figures/b_selection_mode_summary.png`

解釈: top-k は非常に脆い。ただし percentile selection にしても、phantom comparison が強い場合は十分な救済にならない。これは「選択枠を広げる」だけでなく、「actionable slots を保護する」必要があることを示す。

## C. Candidate-Pool Multiplier Sweep

| 条件 | seed数 | 最終人口比 平均 | 最小 | 最大 | 終盤 births/eligible | 終盤 selected actionable | 終盤 phantom share | 終盤 visibility/action gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1x perceived pool | 3 | 0.381 | 0.356 | 0.428 | 0.038 | 0.142 | 0.000 | 0.824 |
| 10x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 30x perceived pool | 3 | 0.000 | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 |
| 100x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 300x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1000x perceived pool | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

図: `figures/c_candidate_multiplier_summary.png`

解釈: 候補数倍率は非常に強い。compact suite では `10x` の時点で no-reserve top-k attention が崩壊する。現実の SNS では候補数が数十倍・数百倍に増えうるため、この軸は本編より重要かもしれない。

## D. Visibility/Action Gap

| 条件 | seed数 | 最終人口比 平均 | 最小 | 最大 | 終盤 births/eligible | 終盤 selected actionable | 終盤 phantom share | 終盤 visibility/action gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Global visibility, action radius 0.03 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.06 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.12 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.24 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius 0.48 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Global visibility, action radius global | 3 | 0.000 | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 |

図: `figures/d_actionability_gap_summary.png`

解釈: この追試は直感と少し違う。action radius を広げても崩壊した。これは actionability gap が無関係という意味ではなく、phantom competition が強すぎると、action radius を広げても top-k attention の占有が残るという意味である。

## E. Reserve Threshold Robustness

| 条件 | seed数 | 最終人口比 平均 | 最小 | 最大 | 終盤 births/eligible | 終盤 selected actionable | 終盤 phantom share | 終盤 visibility/action gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top-k 8, protected slots 0 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| top-k 8, protected slots 1 | 3 | 0.087 | 0.076 | 0.094 | 0.042 | 0.065 | 0.935 | 0.832 |
| top-k 8, protected slots 2 | 3 | 0.716 | 0.703 | 0.736 | 0.035 | 0.244 | 0.756 | 0.853 |
| top-k 8, protected slots 4 | 3 | 0.965 | 0.920 | 0.992 | 0.033 | 0.443 | 0.557 | 0.848 |
| top-k 8, protected slots 8 | 3 | 1.057 | 0.993 | 1.134 | 0.035 | 0.579 | 0.421 | 0.873 |
| top-k 16, protected slots 0 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| top-k 16, protected slots 1 | 3 | 0.224 | 0.182 | 0.257 | 0.035 | 0.058 | 0.942 | 0.669 |
| top-k 16, protected slots 2 | 3 | 0.681 | 0.677 | 0.687 | 0.032 | 0.122 | 0.878 | 0.842 |
| top-k 16, protected slots 4 | 3 | 0.996 | 0.974 | 1.023 | 0.034 | 0.222 | 0.778 | 0.853 |
| top-k 16, protected slots 8 | 3 | 1.040 | 1.015 | 1.085 | 0.035 | 0.275 | 0.725 | 0.874 |
| top-k 16, protected slots 16 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.294 | 0.706 | 0.874 |
| top-k 32, protected slots 0 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| top-k 32, protected slots 1 | 3 | 0.153 | 0.133 | 0.188 | 0.040 | 0.026 | 0.962 | 0.738 |
| top-k 32, protected slots 2 | 3 | 0.705 | 0.664 | 0.761 | 0.036 | 0.060 | 0.940 | 0.866 |
| top-k 32, protected slots 4 | 3 | 0.993 | 0.943 | 1.050 | 0.035 | 0.107 | 0.893 | 0.868 |
| top-k 32, protected slots 8 | 3 | 1.072 | 1.021 | 1.123 | 0.035 | 0.147 | 0.853 | 0.868 |
| top-k 32, protected slots 16 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.147 | 0.853 | 0.874 |
| top-k 32, protected slots 32 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.147 | 0.853 | 0.874 |
| top-k 64, protected slots 0 | 3 | 0.025 | 0.017 | 0.041 | 0.031 | 0.011 | 0.674 | 0.158 |
| top-k 64, protected slots 1 | 3 | 0.199 | 0.138 | 0.279 | 0.040 | 0.013 | 0.981 | 0.789 |
| top-k 64, protected slots 2 | 3 | 0.705 | 0.690 | 0.734 | 0.037 | 0.030 | 0.969 | 0.861 |
| top-k 64, protected slots 4 | 3 | 0.988 | 0.951 | 1.027 | 0.035 | 0.054 | 0.945 | 0.865 |
| top-k 64, protected slots 8 | 3 | 1.064 | 1.021 | 1.100 | 0.035 | 0.073 | 0.927 | 0.871 |
| top-k 64, protected slots 16 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.073 | 0.926 | 0.874 |
| top-k 64, protected slots 32 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.073 | 0.926 | 0.874 |

図: `figures/e_reserve_threshold_robustness_summary.png`

解釈: top-k サイズを変えても、protected slots の閾値構造は残る。おおむね 2 slots で部分生存、4 slots で生存域に入る。これは reserve fraction ではなく、bounded attention 内の保護スロット数が重要であることを示す。

## F. Cultural Overconstraint

| 条件 | seed数 | 最終人口比 平均 | 最小 | 最大 | 終盤 births/eligible | 終盤 selected actionable | 終盤 phantom share | 終盤 visibility/action gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reserve fraction 0.0000 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Reserve fraction 0.0625 | 3 | 0.224 | 0.182 | 0.257 | 0.035 | 0.058 | 0.942 | 0.669 |
| Reserve fraction 0.1250 | 3 | 0.681 | 0.677 | 0.687 | 0.032 | 0.122 | 0.878 | 0.842 |
| Reserve fraction 0.2500 | 3 | 0.996 | 0.974 | 1.023 | 0.034 | 0.222 | 0.778 | 0.853 |
| Reserve fraction 0.5000 | 3 | 1.040 | 1.015 | 1.085 | 0.035 | 0.275 | 0.725 | 0.874 |
| Reserve fraction 0.7500 | 3 | 1.050 | 1.031 | 1.078 | 0.034 | 0.309 | 0.691 | 0.867 |
| Reserve fraction 0.9000 | 3 | 1.048 | 0.998 | 1.118 | 0.034 | 0.295 | 0.705 | 0.874 |
| Reserve fraction 1.0000 | 3 | 1.047 | 0.998 | 1.118 | 0.034 | 0.294 | 0.706 | 0.874 |

図: `figures/f_cultural_overconstraint_summary.png`

解釈: 現行モデルでは過剰制約ペナルティが出ていない。閾値を超えると強い reserve は概ね安定する。これは「強い文化が常に良い」という結論ではなく、モデル側に強制的な local/actionable bias の機会費用がまだ不足しているという意味で読むべきである。

## G. Institutional Learning

| 条件 | seed数 | 最終人口比 平均 | 最小 | 最大 | 終盤 births/eligible | 終盤 selected actionable | 終盤 phantom share | 終盤 visibility/action gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No learning | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Slow regional learning | 3 | 0.667 | 0.512 | 0.790 | 0.042 | 0.189 | 0.811 | 0.865 |
| Fast regional learning | 3 | 0.945 | 0.864 | 1.016 | 0.039 | 0.244 | 0.756 | 0.865 |
| Preadapted reserve 0.25 | 3 | 0.996 | 0.974 | 1.023 | 0.034 | 0.222 | 0.778 | 0.853 |

図: `figures/g_institutional_learning_summary.png`

解釈: 制度学習は強い。slow learning でも崩壊を避け、fast learning は preadapted culture に近い。これは「全個人が理性的に近場を見る必要がある」というより、「地域・制度が失敗を観測して attention rule を調整できるか」が重要であることを示す。

## まとめ

追試A-Gは、最初の素朴な仮説を修正する。

修正前:

```text
Radius 拡大が出生・ペア形成を壊す。
```

修正後:

```text
可視性拡大そのものではなく、
非実行可能な候補比較が bounded attention を占有し、
actionable な相互選択を押し出すことが問題である。
```

対抗条件は二つある。

1. 個人または文化が、top-k 内に十分な actionable slots を保護する。
2. 地域・制度が人口低下を観測して、十分早く reserve culture を学習する。

この補遺は、本編の主張を「SNS/Radius が悪い」から、「仮想比較を現実行動に変換する attention/institution design が必要である」へ絞り込む。

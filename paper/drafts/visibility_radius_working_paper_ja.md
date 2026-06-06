# 可視半径の拡大、有限注意、そして実行可能な配偶選択

## Visibility Radius Simulation による Working Paper

Version: 0.1  
Date: 2026-06-05  
Repository: `visibility-radius-sim`

## 要旨

本稿は、可視半径が急速に拡大する環境において、局所的な「上位候補選択」戦略が適応的であり続けるかを検討する抽象エージェント・ベース・モデルである。モデル内のエージェントは、有限の top-k 注意によって候補を評価する。候補には、実際に接触・交配可能な actionable candidates と、見えるが実行不可能な phantom candidates が存在する。

中心仮説は、可視候補プールの急拡大が、実行可能な候補への注意を押し出すことで、相互選択、ペア形成、出生を低下させる可能性がある、というものである。探索的シミュレーションでは、グローバル可視性とローカル行動半径が組み合わさると、人口ボトルネックまたは絶滅的な推移が発生した。一方、top-k 注意の一部を実行可能候補に予約する介入は、崩壊を大きく緩和した。

結果は、単純な「SNS を減らす」よりも、「仮想比較が始まる前に現実接触可能な候補枠を確保する」ことが重要であることを示唆する。地域文化実験では、場所に保持された actionable reserve culture がある地域は生存し、補正のない地域は淘汰されやすかった。

本稿は現実の人口予測ではなく、出生率低下の単一原因を主張するものでもない。貢献はより限定的である。すなわち、候補プール拡大、有限注意、行動可能性制約が相互作用するメカニズムを検討するための、再現可能な抽象モデルを提示することである。

## キーワード

エージェント・ベース・モデル、可視半径、配偶選択、有限注意、phantom candidates、actionable attention、文化適応、地域文化

## 1. 問題設定

人間の配偶選択は、長い期間、強い局所性のもとで行われてきた。候補は、居住地、学校、職場、親族、地域共同体、紹介、反復的な対面接触によって制限されていた。

現代のネットワーク環境では、この制限が大きく変わる。個人は、自分が実際に会い、信頼を形成し、関係を調整できる範囲をはるかに超える候補を観察・比較できる。

本研究の問いは次である。

> 観察可能な候補プールがローカルからグローバルへ拡大したとき、ローカル環境で有効だった上位候補選択戦略は、なお適応的であり続けるのか。

この問いは、人間が数値最適化で配偶者を選ぶという主張ではない。また、現実の出生率低下を SNS だけで説明するものでもない。ここで扱うのは、次の三つの量の不一致である。

- 可視半径: 誰が見えるか、誰と比較できるか
- 行動半径: 誰と実際に会い、信頼を形成し、関係を進められるか
- 注意容量: 何人の候補が上位評価枠を占められるか

モデルは、可視半径が行動半径よりも急速に拡大した場合に何が起きるかを調べる。

## 2. 概念仮説

作業仮説は次である。

> 可視候補の急拡大は、注意が top-k 型であり、行動半径が局所的なままである場合、適応不全を引き起こしうる。

想定される失敗経路は次である。

```text
グローバル可視性 + ローカル行動半径 + 有限 top-k 注意
-> phantom candidates が上位注意枠を消費
-> actionable な相互選択が低下
-> ペア形成が低下
-> 出生が低下
-> 人口維持が困難になる
```

対抗仮説は、情報遮断そのものではない。重要なのは、評価プロセスの中に十分な実行可能候補を残すことである。

実践的には、次のように言える。

> 仮想世界を消す必要はない。ただし、非実行可能な比較が、実行可能な出会いをすべて押し出さない構造が必要である。

## 3. モデル概要

各エージェントは次を持つ。

- 年齢
- 寿命
- 位置
- traits
- preference weights
- selectivity
- alive/dead 状態
- 任意の region identity

traits は、魅力、資源、知性、親切さ、安定性などを表す数値ベクトルである。preference weights は同次元の選好ベクトルである。

各年の処理は次である。

1. 生存エージェントが加齢する。
2. 寿命を超えたエージェントが死亡する。
3. visibility radius が更新される。
4. 生殖年齢のエージェントが候補を評価する。
5. 候補は preference weights によってスコアリングされる。
6. percentile または top-k によって選択される。
7. 相互選択が成立した場合のみペアが形成される。
8. ペアは確率的に子を産む。
9. 子は両親の traits を平均し、 mutation noise を加えて継承する。
10. 年次メトリクスを記録する。

後続実験では、次の抽象概念を追加した。

- `phantom_candidate_mode`: 見えるがペア形成できない候補が比較に入る。
- `action_radius`: この半径内の候補のみが実行可能である。
- `actionable_selection_reserve_fraction`: top-k 注意枠の一部を実行可能候補に予約する。
- regional cultures: 地域ごとに異なる reserve fraction を持つ。

## 4. メトリクス

主な出力は次である。

- population size
- population index
- births per eligible agent
- matched pair count
- unmatched rate
- trait mean / variance
- trait diversity
- reproductive concentration
- effective parent count
- selected actionable share
- selected phantom share
- visibility radius
- candidate-pool expansion

注意点として、unmatched rate は崩壊後に誤読されやすい。eligible population が極端に小さくなると、低い unmatched rate が改善ではなく分母の崩壊を反映する場合がある。人口維持を見るには、population index と births per eligible を併せて読む必要がある。

## 5. 実験結果

### 5.1 Phantom candidates によって可視半径が因果的になる

初期モデルでは、候補プール拡大だけでは結果が大きく変わらない場合があった。理由は、スコアリングされる候補が全てペア形成可能だったためである。

sampled phantom candidates を追加すると、可視半径の拡大が因果的になった。見えるが実行不可能な候補が top-k 注意枠を奪うためである。

Actionability comparison の結果は次である。

| Scenario | Final ratio | Late selected actionable | Late selected phantom |
|---|---:|---:|---:|
| Current phantom | 0.415 | 0.018 | 0.850 |
| Old behavior, no phantom | 0.491 | 0.106 | 0.000 |
| Actionable reserve 50% | 0.945 | 0.412 | 0.574 |
| Actionable reserve 75% | 0.941 | 0.455 | 0.535 |

重要なのは、phantom candidates が道徳的に悪いということではない。実行不可能な比較対象であっても、希少な意思決定注意を消費しうるという点である。

### 5.2 崩壊メカニズムは attention displacement である

重い失敗モードは、グローバル可視性とローカル行動半径が同時に存在する場合に現れる。エージェントは多数の候補を見るが、その大半とは実際にペア形成できない。選択が top-k 型である場合、高スコアの phantom candidates が実在するローカル候補を押し出す。

ここで、次の二つが分離する。

- preference formation: 比較プール内で誰が高く評価されるか
- pair formation: 実際に誰と相互選択・調整できるか

この分離が大きくなりすぎると、出生が崩れる。

### 5.3 Actionable reserve は閾値的に効く

Actionable reserve は、top-k 注意枠の一部を action radius 内の実行可能候補に予約する仕組みである。`top_k=16` の場合、reserve fraction は整数個の保護スロットに変換される。

Multi-seed slot sweep の結果は次である。

| Protected actionable slots | Reserve fraction | Mean final ratio |
|---:|---:|---:|
| 0 | 0.0000 | 0.001 |
| 1 | 0.0625 | 0.094 |
| 2 | 0.1250 | 0.390 |
| 3 | 0.1875 | 0.613 |
| 4 | 0.2500 | 0.735 |
| 5 | 0.3125 | 0.842 |
| 6 | 0.3750 | 0.890 |
| 8 | 0.5000 | 0.983 |

これは、文化的強度が連続的に良くなるというより、工学的な閾値を持つことを示唆する。

```text
十分な actionable slots を、十分早期に確保し、深い人口ボトルネックを避ける
```

この条件を満たすと、weak, balanced, strong の文化差は、絶滅か生存かよりも、回復の深さや人口シェアに影響する。

### 5.4 地域に保持された文化は actionable attention を守る

地域文化実験では、文化を親子だけで継承される性質ではなく、場所に保持される性質として扱った。これは、制度、反復的な地域接触、言語、法、社会的期待などが文化を保持するという見方に対応する。

Long-run fixed-culture comparison は次である。

| Scenario | Final ratio | Late births / eligible | Late selected actionable |
|---|---:|---:|---:|
| No virtual filter | 0.000 | 0.0000 | 0.001 |
| Weak actionable culture | 0.696 | 0.0361 | 0.241 |
| Balanced actionable culture | 0.921 | 0.0357 | 0.410 |
| Strong actionable culture | 0.963 | 0.0362 | 0.443 |
| Local-only reference | 0.353 | 0.0301 | 0.214 |

結果は、次の解釈を支持する。

> 仮想世界への耐性を持つ文化は可視半径拡大後も生存しやすく、補正のない文化は淘汰されやすい。

ただし、最大制約が常に最適という意味ではない。閾値を超えた後の違いは、生存そのものよりも、人口シェアや回復深度に現れる。

### 5.5 Region 境界と cross-region pairing は文化シェアを変える

Region を跨ぐ交配を許可するかどうかは、文化の混合の仕方を変える。

現在の regional comparison は次である。

| Cross-region pairing | Final ratio | No-reserve share | Weak share | Balanced share | Strong share |
|---|---:|---:|---:|---:|---:|
| Allowed | 0.754 | 0.002 | 0.307 | 0.337 | 0.354 |
| Blocked | 0.774 | 0.009 | 0.335 | 0.367 | 0.290 |

この結果だけで境界政策を評価することはできない。しかし、境界は総人口だけでなく文化シェアにも影響することが分かる。最適な文化強度は、移動、交配ルール、文化拡散速度に依存する可能性が高い。

### 5.6 行動介入は何を支持するか

最後に、モデル上のメカニズムを個人行動に近い形へ翻訳した。

| Variant | 行動としての意味 | Final ratio mean |
|---|---|---:|
| Raw SNS / no discipline | 介入なし | 0.001 |
| Contact before scroll | 仮想比較前に現実接触枠を確保 | 0.735 |
| 48h move to reality | オンライン関心を短時間で現実接触へ移す | 0.710 |
| Full behavior bundle | reserve, phantom cap, action radius を同時に変更 | 0.705 |
| Distance filter first | 評価前に距離で絞る | 0.515 |
| Weekly fixed local venue | 反復的な地域接触を増やす | 0.432 |
| Do not replay phantom candidates | 非実行可能候補の反復だけを減らす | 0.067 |

最も強い結果は次である。

> 有効なのは、SNS 使用時間を減らすこと自体ではなく、仮想比較が注意を消費する前に現実接触可能な候補枠を確保することである。

従って、人間向けの行動教訓は次に近い。

- スクロールや候補閲覧の前に、現実接触の予定を入れる。
- 候補評価の前に、近距離・紹介・実際に会えることを条件にする。
- オンラインで関心を持った候補は、短期間で現実接触へ移す。
- 会えない候補を、長期的な比較基準として保存し続けない。
- 反復的な地域コミュニティに参加し、信頼と調整可能性を蓄積する。

## 6. 解釈

本モデルが示すのは、可視性そのものが問題なのではないということである。可視性は有益にもなりうる。問題は、可視性が拡大しても、行動可能性が拡大しない場合である。

高可視性環境では比較対象が増える。しかし、生殖、信頼、ペア形成、長期調整には依然として制約がある。

- 物理的・時間的近接性
- 反復的接触
- 共通期待
- 相互 availability
- タイミング
- 社会的検証
- 実際に関係を進める経路

これらが不足すると、「より多く見えること」が「より多く結びつくこと」につながらない。

要約すると次である。

```text
適応単位は「多く見ること」ではない。
適応単位は「注意を十分に actionable な相互選択へ変換すること」である。
```

## 7. 実践的含意

### 7.1 個人

モデルは、曖昧な自制よりも、具体的な順序設計を支持する。

有効そうな行動は次である。

- 比較を広げる前に現実接触を作る。
- locality を後付けではなく、事前フィルタにする。
- オンライン関心を現実接触に変換するか、早めに捨てる。
- 到達不能な候補を基準値として保持しない。
- 同時に扱う真剣な候補数を小さく保つ。

これは道徳論でも懐古主義でもない。有限注意の中に actionability を残すための設計である。

### 7.2 プラットフォーム

もしプラットフォームが無限比較ではなくペア形成を支援するなら、最適化対象は engagement ではなく actionable transition になる。

設計例は次である。

- local-first ranking
- 相互 availability filter
- event-based matching
- 小さな active candidate queue
- 古い候補や到達不能候補の自然減衰
- 成立可能な mutual match 後の無限閲覧への摩擦

モデルは、エンゲージメントだけに最適化された設計は attention displacement を悪化させうる一方、現実接触への遷移を支援する設計は改善しうると予測する。

### 7.3 地域・制度

共同体は actionable candidate pool を維持する仕組みとして解釈できる。

- 学校
- 職場
- 地域
- クラブ
- 紹介
- 反復イベント
- 共有儀礼
- commitment と availability に関する地域規範

モデル上では、これは place-held culture である。個人が単独で仮想比較問題を解く必要を減らす。

### 7.4 政策・都市設計

このメカニズムが正しいなら、出生支援は補助金だけの問題ではない。経済制約は重要だが、社会的インフラも重要である。

探索すべき方向は次である。

- 若年層が安定した地域共同体の近くに住める住宅設計
- third place と定期的な地域イベント
- 紹介が低リスクで自然に行われる制度
- 調整コストを下げる交通・時間設計
- actionable matching を促すプラットフォーム設計

このモデルは、これらの政策が現実に効くことを証明しない。ただし、どこを見るべきかを示す。

## 8. 本稿が主張しないこと

本モデルは次を主張しない。

- 出生率低下の原因は SNS だけである。
- 現実の人間は数値ベクトルで配偶者を選ぶ。
- 特定の文化が道徳的に優れている。
- ローカル社会だけが理想である。
- 情報制限は常に良い。
- 日本や特定国を直接シミュレートしている。

より安全な主張は次である。

> 有限注意の選択システムでは、急速に拡大した非実行可能比較が、実際の相互ペア形成を抑制しうる。ただし、注意または制度が actionability を保存すれば、その崩壊は緩和されうる。

## 9. 限界

現在のモデルは意図的に単純である。

主な限界は次である。

- 経済がない。
- 住宅・労働市場制約がない。
- sex/gender-specific な生殖制約がない。
- 避妊・家族計画がない。
- 結婚制度がない。
- 育児コストがない。
- 固定文化以外の明示的学習が弱い。
- 位置と region 以外のネットワーク構造がない。
- プラットフォーム設計が内生化されていない。
- 現実人口データへの経験的キャリブレーションがない。

従って、本モデルは予測器ではなく、メカニズム探索器として読むべきである。

## 10. 今後の研究

次に有用な拡張は次である。

1. Region レベルの文化学習を追加する。
2. migration と cross-region pairing を分離する。
3. engagement 最適化型と actionability 最適化型の platform design を比較する。
4. trust と repeated interaction を直接モデル化する。
5. 経済制約を独立した bottleneck として追加する。
6. メカニズムが安定してから、現実の人口系列へ stylized calibration する。
7. `top_k`, action radius, reserve fraction, candidate-pool multiplier を大きく sweep する。

特に重要な次実験は、制度的学習である。

```text
地域は人口低下を観察した後、自ら actionable reserve culture を調整できるか。
```

これは、全個人が意識的に仮想世界とのミスマッチを理解しなくても、文明が回復できるかを検証する。

## 11. 結論

本シミュレーションは、控えめだが有用な命題を支持する。

> 可視性が急拡大した環境では、情報を抑圧することよりも、注意から行動へ至る経路を保存することが重要である。

モデル上の最も強い実践教訓は次である。

> 非実行可能な比較対象に、上位注意枠をすべて占有させてはいけない。

個人にとっては、仮想比較より先に、現実接触、近接性、相互 availability を配置することを意味する。プラットフォームにとっては、無限閲覧ではなく actionable transition を設計目標にすることを意味する。共同体にとっては、個人が世界規模の比較問題を一人で解かなくてもよいように、反復的な地域制度を保つことを意味する。

このメカニズムが一般化するなら、仮想世界に適応した文化とは、仮想世界を拒否する文化ではない。それは、仮想世界が欲望、注意、現実調整の橋を壊さないように設計された文化である。

## 再現性メモ

主に参照した出力は次である。

- `outputs/actionable_attention/actionable_attention_comparison_summary.csv`
- `outputs/civilizational_adaptation/civilizational_adaptation_longrun_summary.csv`
- `outputs/regional_culture/regional_culture_crossing_summary.csv`
- `outputs/reserve_threshold/reserve_threshold_report.md`
- `outputs/behavioral_interventions/behavioral_action_interventions_summary.csv`
- `outputs/behavioral_interventions/behavioral_action_interventions_report.md`

代表的な実行コマンドは次である。

```bash
uv run python -m visibility_radius_sim.cli run --years 50 --population 300 --output outputs/demo.csv
uv run python -m visibility_radius_sim.cli plot --input outputs/demo.csv --output outputs/demo.png
uv run pytest
```

一部の探索出力は作業セッション中の ad hoc script で生成されている。出版品質の再現性を目指す場合、それらを CLI サブコマンドまたは notebook として versioned artifact に昇格させる必要がある。

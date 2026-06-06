# Reality-grounded Calibration 日本語メモ

目的は、gendered aspiration の効果を見る前に、対称条件そのものが現実的な人口推移レンジに入るよう土台を調整すること。
ここでは1980年から2070年相当の91年を見て、対称条件が1980〜2020年の人口指数アンカーと2070年推計アンカーに近い候補を探した。

現実根拠の扱い:

- 日本の合計特殊出生率は1980年 `1.75`、2005年 `1.26`、2023年 `1.20`、2024年概数 `1.15` と長期低下している。
- 国立社会保障・人口問題研究所の将来推計では、総人口は2020年 `1億2,615万人` から2070年 `8,700万人` 程度へ低下する出生中位推計である。
- したがって、このtoy modelでは1980→2070相当で `0.65〜0.85` を対称条件の粗い目標帯にした。
- 年齢別出生は厳密な人口学モデルではなく、20代後半〜30代前半を高くし、40代を低くする `japan-stylized` profile として入れた。
- 年次出生環境は `japan-tfr-stylized` schedule とし、1980年を高め、2000年代以降を低める倍率を `birth_probability` に掛けた。
- 候補選抜では2070年の終点だけでなく、1980/1990/2000/2010/2020/2070の人口指数RMSEを評価した。

参照した公的資料:

- 厚生労働省 `令和６年(2024)人口動態統計月報年計（概数）の概況`: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai24/index.html
- 厚生労働省 `人口動態統計 年報 主要統計表（最新データ、年次推移）`: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/suii00/index.html
- 国立社会保障・人口問題研究所 `日本の将来推計人口（令和5年推計）`: https://www.ipss.go.jp/pp-zenkoku/j/zenkoku2023/pp_zenkoku2023.asp

## 出力

- `outputs/reality_grounded_calibration/base_candidate_summary.csv`
- `outputs/reality_grounded_calibration/profile_raw.csv`
- `outputs/reality_grounded_calibration/profile_summary.csv`
- `outputs/reality_grounded_calibration/profile_comparison.png`
- `outputs/reality_grounded_calibration/reality_overlay.png`

## 対称条件の候補 上位10件

| 候補 | 最終人口比 | 全アンカーRMSE | 1980-2020 RMSE | 2000誤差 | 2010誤差 | 2070誤差 | 目標誤差 | 目標帯内 | 後期出生/人口 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| birth=0.22, duration=18, cap=6000, life=78 | 0.740 | 0.020 | 0.021 | -0.013 | -0.003 | -0.003 | 0.000 | True | 0.009 |
| birth=0.20, duration=18, cap=9000, life=78 | 0.728 | 0.030 | 0.028 | -0.008 | 0.003 | -0.015 | 0.012 | True | 0.008 |
| birth=0.18, duration=26, cap=9000, life=82 | 0.687 | 0.025 | 0.010 | 0.009 | 0.008 | -0.056 | 0.053 | True | 0.007 |
| birth=0.22, duration=26, cap=4500, life=86 | 0.735 | 0.036 | 0.033 | 0.031 | 0.050 | -0.009 | 0.005 | True | 0.007 |
| birth=0.20, duration=26, cap=9000, life=78 | 0.777 | 0.028 | 0.022 | -0.010 | -0.000 | 0.034 | 0.037 | True | 0.009 |
| birth=0.24, duration=18, cap=4500, life=78 | 0.763 | 0.030 | 0.030 | -0.006 | 0.004 | 0.020 | 0.023 | True | 0.009 |
| birth=0.20, duration=26, cap=6000, life=82 | 0.706 | 0.030 | 0.023 | 0.023 | 0.021 | -0.037 | 0.034 | True | 0.007 |
| birth=0.18, duration=18, cap=9000, life=82 | 0.682 | 0.029 | 0.014 | 0.014 | 0.006 | -0.061 | 0.058 | True | 0.006 |
| birth=0.22, duration=26, cap=4500, life=82 | 0.705 | 0.039 | 0.023 | 0.022 | 0.025 | -0.038 | 0.035 | True | 0.007 |
| birth=0.24, duration=26, cap=4500, life=78 | 0.797 | 0.031 | 0.022 | -0.012 | -0.002 | 0.054 | 0.057 | True | 0.009 |

## 選抜候補に aspiration profile を乗せた結果

| 候補 | 対称 | 500+ proxy | light mixed | heavy mixed | heavy差分 |
| --- | --- | --- | --- | --- | --- |
| birth=0.18, duration=26, cap=9000, life=82 | 0.687 | 0.574 | 0.498 | 0.447 | -0.240 |
| birth=0.20, duration=18, cap=9000, life=78 | 0.728 | 0.642 | 0.553 | 0.439 | -0.289 |
| birth=0.20, duration=26, cap=9000, life=78 | 0.777 | 0.614 | 0.603 | 0.488 | -0.289 |
| birth=0.22, duration=18, cap=6000, life=78 | 0.740 | 0.632 | 0.584 | 0.449 | -0.291 |
| birth=0.22, duration=26, cap=4500, life=86 | 0.735 | 0.663 | 0.589 | 0.502 | -0.233 |

## 解釈

従来の180年・18〜45歳条件では、土台が強すぎたり弱すぎたりして効果分離が難しかった。
91年・20〜44歳・年齢別出生profileにすると、対称条件を現実的な低下レンジに寄せやすい。
その上でも `mixed_heavy` は選抜候補すべてで対称条件を下回る。
`reality_overlay.png` は、1980〜2020年の国勢調査アンカーと2070年IPSS推計アンカーを線形補間した参照線に、
選抜候補のSim軌道を重ねた図である。今回から、上位選択なしの対称条件が2000年頃までの増加局面をなぞることも評価に入れている。

ただし、この段階でも所得・婚姻・年齢別出生率を完全にキャリブレーションしたわけではない。
ここで得た候補は、今後の本編Simを走らせるための現実根拠つき初期土台である。

## 再実行

```bash
.venv/bin/python scripts/run_reality_grounded_calibration.py
```

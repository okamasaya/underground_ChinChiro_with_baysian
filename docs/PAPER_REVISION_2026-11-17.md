# Letter・Full paperの説明と図の改訂 — 2026年11月17日

## 改訂の理由

Zenn連載の第3回の図について、「常に456賽なら2は出ないのに、なぜ線が0へ下がるのか」という読み違いが生じた。実際の賽の使用割合と、同じ記録から評価した固定戦略仮説の事後確率を区別する説明を、論文側にも反映した。

第7回で整理した「状態の推定」「次回の観測予測」「将来のモデル比較」の違いも、図で読み分けられるようにした。

作業開始時の`main`は`4f9d045e569dc62b9da17151761d4af9ab14ade3`。作業ブランチは`docs/paper-clarity-2026-11-17`。本記録の作成時点では、今回の論文改訂はローカルの作業変更であり、コミット・Push・マージはまだ行っていない。

## 更新した図

### A06：同じ記録に対する純粋仮説と混合仮説

- [PDF](../figures/A06/kaiji_a06_mixed_single_die.pdf)／[PNG](../figures/A06/kaiji_a06_mixed_single_die.png)／[再生成コード](../figures/A06/kaiji_a06_mixed_single_die.py)
- 論文側の既存の保存系列「Hi 2回、Lo 1回、Hi 17回」を維持した。Zenn第3回の11観測の例とは別の系列である。
- 同じ保存系列を、純粋仮説と使用率0.900の混合仮説の両方で評価する曲線にした。どちらも通常賽のみとの別々の2仮説比較。
- 純粋仮説はLoで尤度が0となり、以後も過去のLoが残るので事後確率が復活しないことを明記。
- 混合仮説のLo直前の水準を水平点線で表示し、その意味を注記。
- 元の混合仮説の数値、オッズ倍率1.900／0.100、Hi 4回で低下前を上回る計算を維持。
- 実際の使用割合を描く図ではないこと、最終値1.000は丸め表示であることを図中に記載。
- 掲載幅160 mm、図中の通常文字は9 pt以上を維持。高さは205 mmへ調整。

### A22：状態推定・次回予測・将来モデル比較

- [PDF](../figures/A22/kaiji_a22_bkt_ambiguity_future.pdf)／[PNG](../figures/A22/kaiji_a22_bkt_ambiguity_future.png)／[再生成コード](../analysis/bkt_validation_figures.py)
- 上段の状態確率と下段の将来到達率に加え、中段に次回正答予測を追加。
- 同じ8回答後の状態確率は基準0.984／別解0.369、次回正答予測は0.891／0.623。
- 上2段は固定候補の比較であり、信用区間ではないことを明記。
- 下段には保存済みの各20万系列を使い、模擬実験は再実行していない。帯は到達率のモンテカルロ計算に対する点ごとのWilson区間。
- 掲載幅160 mm、通常文字9 ptの方針を維持し、高さを250 mmへ調整。
- 作図コードに`--figure A22`／`--figure A23`を追加。指定なしでは従来どおり両方を生成する。

## 本文・PDF・案内の更新

- [Letter](../kaiji_bayes_letter_20261105.pdf)：使用率と仮説確率、観測済み記録の評価、途中の閾値到達、状態確率と理解度の得点の違いを補足。
- [Full paper](../kaiji_ungr_456dice.pdf)：第3〜4節の説明、A06/A22のキャプション、図一覧を更新。
- Letter 4ページ、Full paper 68ページを維持。図番号24件と本文の印字ページも維持した。
- 改訂日は2026年11月17日へ更新。既存のリンクを保つため、TeXとPDFのファイル名は変更していない。
- README、CHANGELOG、図版対応表、再現手順を更新。

## 再生成・ビルド

仮想環境の準備は[HANDOFF_2026-11-17.md](HANDOFF_2026-11-17.md)を参照。リポジトリのルートで実行する。

```bash
set -euo pipefail
export XDG_CACHE_HOME="$PWD/build/cache"
export MPLCONFIGDIR="$PWD/build/matplotlib"
mkdir -p "$XDG_CACHE_HOME" "$MPLCONFIGDIR"

.venv/bin/python figures/A06/kaiji_a06_mixed_single_die.py
.venv/bin/python analysis/bkt_validation_figures.py --figure A22
latexmk -xelatex -interaction=nonstopmode -halt-on-error kaiji_bayes_letter_20261105.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error kaiji_ungr_456dice.tex
```

これらのコマンドは対応する図とPDFを更新する。表示確認だけを行う場合は、引き継ぎ資料にある検証用コピーで実行する。

## 確認したこと

- A06：混合仮説の逐次ベイズ更新・オッズ更新・閉形式の一致、純粋仮説の20接頭列、Lo後の0、回復までの4回を確認。
- BKT：2候補×8接頭列について尤度と状態確率を独立列挙と比較し、32条件が厳密一致。次回予測も保存済み分数値と一致。
- Letterの経験CDF座標802点を保存済みNPZと照合。TeXに埋め込まれたCDF座標は改訂前後で同一。
- 既存の計算用JSON・NPZ・CSVのSHA-256は作業前後で一致。
- 両PDFが正常にビルドされ、最終LaTeXログに警告・未定義参照・はみ出し・欠字の報告がないことを確認。
- PDFの全72ページを描画し、全体の縮小一覧と変更ページを表示確認。本文・図・キャプションの配置を確認。
- Type 3フォント0件、抽出テキストのページ外へのはみ出し0件。図番号と掲載ページの24件が対応表と一致。
- 元からあったCSV5件の差分表示は、そのまま保持した。

機械可読の記録は[revision_validation_20261117.json](../analysis/revision_validation_20261117.json)を参照。

## 著者確認と次の再開点

改訂版のLetterとFull paperは著者確認済み。その後、著者の依頼により[HANDOFF_2026-11-17.md](HANDOFF_2026-11-17.md)を、論文改訂まで含む当日のまとめ・再開点へ更新した。

1. 再開時に、今回の改訂と資料更新がGitHubへ反映済みかを確認する。
2. 未反映なら、今回の変更ファイルだけを明示してステージし、指示に従ってcommit・push・mergeする。既存のCSV5件を含めない。
3. 反映済みなら、論文の作成や著者確認を繰り返さず、連載全体の最終確認と公開準備へ進む。

今後の追加修正で図を見直す場合は、Full paperの図7（A06、本文14ページ）と図21（A22、本文52ページ）を起点に、作図コードとTeXの対応を確認する。

モデルの変更、新しい大規模模擬実験、実データによる理解度・介入効果の検証、Zennへの公開は今回の改訂には含めていない。

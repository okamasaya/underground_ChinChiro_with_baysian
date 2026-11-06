# PDF・計算・図版の再現方法

以下のコマンドは、このプロジェクトを配置したルートディレクトリで実行する。保存済みPDFと図版を読む場合は、計算やビルドの実行は不要。

## 1. PDFのビルド

TeX Live等のXeLaTeX環境、Noto Sans CJK JP、Noto Serif CJK JPを使用する。amsmath、booktabs、longtable、hyperref等のほか、Letterではpgfplotsを使用する。フォントはTeXから認識できる状態にする。

```bash
latexmk -xelatex kaiji_ungr_456dice.tex
latexmk -xelatex kaiji_bayes_letter_20261105.tex
```

`latexmk`を使わない場合は、各文書についてXeLaTeXを2回以上実行し、目次と参照を収束させる。

Letterは図の座標をTeX内に持つ。Full paperは`figures/`のPDF・画像を読み込む。ルートのTeXと`figures/`・`analysis/`・`fonts/`の位置関係を保持する。

## 2. Pythonの準備

```bash
python -m pip install -r requirements.txt
```

依存関係はMatplotlib、NumPy、fontToolsの最低バージョン指定であり、環境を完全固定するロックファイルではない。基礎ノートブックを対話的に開く場合はJupyter等の実行環境を別途用意する。

同梱の`fonts/ArticleJPSans-Regular.ttf`と`ArticleJPSans-Bold.ttf`は図版用。本文のNotoフォントとは用途が異なる。図用フォントの再構築は通常不要で、必要時のみ`analysis/build_article_font.py`と`fonts/provenance.json`を参照する。

## 3. 保存済み結果を読む

| 対象 | ファイル |
| --- | --- |
| 基礎モデル | [ノートブック](../Bayesian_updating_456dice.ipynb) |
| 賽の逐次判定と使用率の感度 | [sequential_performance.json](../analysis/sequential_performance.json)、[frequency_sensitivity.csv](../analysis/frequency_sensitivity.csv) |
| BKTの説明用感度比較 | [bkt_sensitivity.json](../analysis/bkt_sensitivity.json)、[CSV](../analysis/bkt_sensitivity.csv) |
| BKTの有限標本の曖昧さ・将来比較・予測監視 | [bkt_sequential_validation.json](../analysis/bkt_sequential_validation.json)、[CSV](../analysis/bkt_future_first_passage.csv)、[NPZ](../analysis/bkt_future_first_passage.npz) |
| 現行版との照合記録 | [revision_validation_20261106.json](../analysis/revision_validation_20261106.json) |

ノートブックは導入用の基礎モデルであり、Full paperの全結果を一括で再現するものではない。詳しい計算条件は[analysis/README.md](../analysis/README.md)にまとめている。

## 4. 計算を再実行する

目的に応じて実行する。これらのプログラムは、対応する保存データや図版を同じパスへ出力する。

```bash
python analysis/chinchiro_model.py
python analysis/sequential_performance.py
python analysis/make_extension_figures.py
```

将来BKT比較を含む計算は次を実行する。各生成モデル20万系列、最大400問を用い、保存済みの将来比較データを再生成する。

```bash
python analysis/bkt_sequential_validation.py
```

基準と別解それぞれの過去8回答後の丸め前の`q9`から再開し、各候補のパラメータを将来にも固定する。NumPy PCG64、seed `2026110302`の`SeedSequence.spawn(2)`を使用し、経験分位点は`inverted_cdf`で定義する。

## 5. 図を再生成する

A01〜A15は各図のフォルダにあるPythonを使用する。例：

```bash
python figures/A01/kaiji_a01_observation_units.py
```

追加図の作図入口は次の通り。

```bash
python analysis/discussion_figures.py
python analysis/make_extension_figures.py
python analysis/bkt_validation_figures.py
```

同じ役割の個別入口がA16〜A23にもある。A22/A23の作図は保存済みの計算結果を参照する。扉絵B01と参考写真P01は、数値計算から再生成する図ではない。

## 6. 数値の読み方

表示は原則として小数点以下3桁・ROUND_HALF_UP、回数は整数。計算用の分数やデータを表示桁で丸めない。到達率のMCSEはパーセントポイント、打切り平均のMCSEは問題数の単位で示す。

将来BKT比較は独立系列のモンテカルロ計算であり、MCMCではない。一定予測の較正監視例は整数再帰で計算している。モデル下の観測予測の保証と、現実の理解度や介入効果の実証を区別する。

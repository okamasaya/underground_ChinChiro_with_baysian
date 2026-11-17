"""Generate the Zenn episode 7 BKT state-and-prediction comparison.

Run from the repository root:
    XDG_CACHE_HOME="$PWD/build/cache" MPLCONFIGDIR="$PWD/build/matplotlib" .venv/bin/python articles/assets/plot_chinchiro_validation.py

Uses the existing eight-answer finite-sample example. Parameters are fixed;
the alternative was selected for a near-equal likelihood on this one sequence.
These are illustrative models, not fitted student data or credible intervals.
Only exact filtering and hidden-state enumeration run here: no large future
simulation is executed and no existing numerical result files are modified.
"""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
from pathlib import Path
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from bkt_sequential_validation import OBS, PARAMS, exact_filter, hidden_enumeration
from figure_fonts import configure

DESTINATION = ROOT / "images/chinchiro-bayes-07-validation/state-and-prediction.png"
NAVY, AMBER = "#2e4a88", "#ae6b22"
GRAY, INK = "#607485", "#172b3a"


def decimal(value, places=1, percentage=False):
    factor = 100 if percentage else 1
    number = Decimal(value.numerator * factor) / Decimal(value.denominator)
    return str(number.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def exact_data():
    assert OBS == (1, 1, 0, 1, 0, 1, 1, 1)
    curves = {key: exact_filter(p, OBS) for key, p in PARAMS.items()}
    saved = json.loads((ROOT / "analysis/bkt_sequential_validation.json").read_text())
    checks = 0
    for key, params in PARAMS.items():
        assert {n: str(v) for n, v in params.items()} == saved["parameters"][key]
        for n, row in enumerate(curves[key], 1):
            likelihood, posterior = hidden_enumeration(params, OBS[:n])
            assert likelihood == row["likelihood"]
            assert posterior == row["posterior"]
            checks += 2
            old = saved["exact_eight_answer_rows"][key][n - 1]
            for field in ("posterior", "q_next", "predict_next", "likelihood"):
                assert row[field] == F(old[field])
            # Learning moves state probability before the next observation.
            q = posterior + (1 - posterior) * params["T"]
            assert row["q_next"] == q
            assert row["predict_next"] == (1 - params["S"]) * q + params["G"] * (1 - q)
    assert checks == 32
    baseline, alternative = curves["baseline"][-1], curves["alternative"][-1]
    ratio = alternative["likelihood"] / baseline["likelihood"]
    assert ratio == F(saved["alternative_over_baseline_likelihood_ratio"])
    assert decimal(ratio, places=6) == "1.000044"
    assert [decimal(curves[k][-1]["posterior"], percentage=True) for k in PARAMS] == [
        "98.4", "36.9",
    ]
    assert [decimal(curves[k][-1]["predict_next"], percentage=True) for k in PARAMS] == [
        "89.1", "62.3",
    ]
    assert baseline["likelihood"] != alternative["likelihood"]
    assert baseline["predict_next"] != alternative["predict_next"]
    return curves, ratio


def make_figure(curves, ratio):
    configure()
    plt.rcParams.update({
        "font.size": 12,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": GRAY,
        "ytick.color": GRAY,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 9.8), dpi=160, sharex=True)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=.14, right=.97, bottom=.19, top=.76, hspace=.62)
    fig.text(.14, .95, "記録への当てはまりが近くても、状態の推定は分かれる",
             fontsize=20, fontweight="bold", ha="left")
    answers = " → ".join("正" if y else "誤" for y in OBS)
    fig.text(.14, .895, f"同じ8回答：{answers}", fontsize=12, color=GRAY)
    xs = list(range(1, len(OBS) + 1))
    for ax in axes:
        ax.set_xlim(.8, 8.3)
        ax.set_ylim(-.025, 1.14)
        ax.set_xticks(xs)
        ax.set_yticks([0, .25, .5, .75, 1])
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.tick_params(axis="x", length=0, pad=8)
        ax.grid(axis="y", color="#e1e7ed", linewidth=.8)
        ax.set_axisbelow(True)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#b5c1cc")
    for key, label, color, marker, style in (
        ("baseline", "基準候補", NAVY, "o", "-"),
        ("alternative", "別の候補", AMBER, "s", "--"),
    ):
        for ax, field in zip(axes, ("posterior", "predict_next")):
            values = [row[field] for row in curves[key]]
            ax.plot(xs, [float(v) for v in values], color=color, marker=marker,
                    linestyle=style, linewidth=2.5, markersize=5, label=label)
            ax.annotate(f"{decimal(values[-1], percentage=True)}%",
                        (8, float(values[-1])), xytext=(-8, 10),
                        textcoords="offset points", ha="right", color=color,
                        fontsize=12, fontweight="bold")
    axes[0].set_title("① 各回答の直後：モデル内の習得状態に置く確率",
                      loc="left", fontsize=12, pad=15)
    axes[0].set_ylabel("習得状態の確率", labelpad=12)
    axes[1].set_title("② その後の学習遷移も入れた、次の1問の正答予測",
                      loc="left", fontsize=12, pad=15)
    axes[1].set_ylabel("次回正答の予測確率", labelpad=12)
    axes[1].set_xlabel("観測を終えた回答数（下段はその次の問題の予測）", labelpad=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(.13, .86),
               ncol=2, frameon=False, fontsize=12, handlelength=2.6)
    fig.text(.14, .09,
             f"過去8回答全体の尤度比（別の候補／基準候補）＝ {decimal(ratio, places=6)}",
             fontsize=11, color=GRAY)
    fig.text(.14, .045, "固定パラメータの説明例。2本の線は仮定を変えた比較で、信用区間ではありません。",
             fontsize=10, color=GRAY)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DESTINATION, dpi=160, facecolor="white")
    plt.close(fig)


def main():
    curves, ratio = exact_data()
    make_figure(curves, ratio)
    print(f"Saved: {DESTINATION.relative_to(ROOT)}")
    print("32 exact likelihood/posterior checks against independent hidden paths passed.")
    print(f"Alternative/baseline likelihood ratio: {decimal(ratio, places=6)}")
    for key, rows in curves.items():
        row = rows[-1]
        print(f"{key}: state {decimal(row['posterior'], percentage=True)}%; "
              f"next correct {decimal(row['predict_next'], percentage=True)}%")


if __name__ == "__main__":
    main()

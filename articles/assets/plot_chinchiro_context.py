"""Generate the Zenn episode 5 context-comparison figure.

Run from the repository root:
    XDG_CACHE_HOME="$PWD/build/cache" MPLCONFIGDIR="$PWD/build/matplotlib" .venv/bin/python articles/assets/plot_chinchiro_context.py

Uses CTX20-v1, the existing illustrative sequence. Contexts precede outcomes;
the opponent seed was selected to include a high-stakes loss. This is neither
original manga data nor a sample used to estimate detection performance.
Inference uses only observed throws and pre-announced context, not latent type.
"""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from chinchiro_model import (
    ETA_CONSTANT, ETA_HIGH, HIGH_TURNS, PRIOR, bayes_factor, context_records, verify,
)
from figure_fonts import configure

DESTINATION = ROOT / "images/chinchiro-bayes-05-context/context-comparison.png"
PURPLE, NAVY, AMBER = "#82519b", "#2e4a88", "#b97621"
GRAY, INK = "#6a7b89", "#172b3a"


def percent(value):
    number = Decimal(value.numerator * 100) / Decimal(value.denominator)
    return f"{number.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%"


def exact_data():
    verify()
    rows = context_records()
    assert len(rows) == 20
    assert ETA_CONSTANT == F(9, 40)
    context, constant = [PRIOR], [PRIOR]
    odds_context = odds_constant = PRIOR / (1 - PRIOR)
    all_high_turns = []
    for row in rows:
        high_stakes = row["turn"] in HIGH_TURNS
        assert row["high_stakes"] == high_stakes
        assert row["stake"] == (10 if high_stakes else 1)
        eta = ETA_HIGH if high_stakes else F(0)
        # Observation is first-throw classification, never generated latent type.
        all_high = min(row["suspect_history"][0]) >= 4
        if all_high:
            all_high_turns.append(row["turn"])
        bf_context = 1 + 7 * eta if all_high else 1 - eta
        bf_constant = 1 + 7 * ETA_CONSTANT if all_high else 1 - ETA_CONSTANT
        # Independently compare the compressed observation with full histories.
        assert bf_context == bayes_factor(row["suspect_history"], eta)
        assert bf_constant == bayes_factor(row["suspect_history"], ETA_CONSTANT)
        assert bf_context == F(row["bf_context"])
        assert bf_constant == F(row["bf_constant"])
        odds_context *= bf_context
        odds_constant *= bf_constant
        context.append(odds_context / (1 + odds_context))
        constant.append(odds_constant / (1 + odds_constant))
        assert abs(float(context[-1]) - row["posterior_context"]) < 1e-15
        assert abs(float(constant[-1]) - row["posterior_constant"]) < 1e-15
        if not high_stakes:
            assert context[-1] == context[-2]
    assert all_high_turns == [4, 8, 11, 12, 16, 18, 20]
    assert sum(r["high_stakes"] for r in rows) == 5
    assert all(t in all_high_turns for t in HIGH_TURNS)
    bf = F(73, 10) ** 5
    assert context[-1] == bf / (9 + bf) < 1
    bf = F(103, 40) ** 7 * F(31, 40) ** 13
    assert constant[-1] == bf / (9 + bf)
    assert [percent(context[n]) for n in HIGH_TURNS] == [
        "44.79%", "85.55%", "97.74%", "99.68%", "99.96%",
    ]
    assert [percent(constant[n]) for n in HIGH_TURNS] == [
        "11.75%", "13.77%", "38.87%", "43.25%", "75.22%",
    ]
    eighth = rows[7]
    assert eighth["suspect_history"] == [(4, 6, 5)]
    assert eighth["opponent_history"] == [(5, 3, 2), (4, 4, 4)]
    assert eighth["result"] == "loss" and context[8] > context[7]
    return rows, context, constant


def make_figure(rows, context, constant):
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
    fig, axes = plt.subplots(
        3, 1, figsize=(12, 10.6), dpi=160, sharex=True,
        gridspec_kw={"height_ratios": [1, 1, 2]},
    )
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=.17, right=.975, bottom=.16, top=.83, hspace=.64)
    fig.text(.17, .95, "同じ出目列でも、局面を含む仮説では推移が変わる",
             fontsize=20, fontweight="bold", ha="left")
    fig.text(.17, .905, "色の付いた手番が、出目の前に決めた勝負どころ。",
             fontsize=12, color=GRAY, ha="left")
    xs = [row["turn"] for row in rows]
    for ax in axes:
        for turn in HIGH_TURNS:
            ax.axvspan(turn - .36, turn + .36, color="#f4e6cf", zorder=0)
        ax.set_xlim(0, 20.75)
        ax.set_xticks(range(0, 21, 2))
        ax.tick_params(axis="x", length=0, pad=8)
        ax.grid(axis="y", color="#e1e7ed", linewidth=.8)
        ax.set_axisbelow(True)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#b5c1cc")
    axes[0].bar(xs, [row["stake"] for row in rows], width=.52,
                color=[AMBER if r["high_stakes"] else "#9cabb9" for r in rows],
                zorder=3)
    axes[0].set_yticks([1, 10])
    axes[0].set_ylim(0, 12)
    axes[0].set_ylabel("賭け金\n（相対単位）", labelpad=14)
    axes[0].set_title("① 4・8・12・16・20手番目だけ、賭け金を10単位にする",
                      loc="left", fontsize=12, pad=14)
    for all_high, marker, color in ((True, "o", NAVY), (False, "s", "#9cabb9")):
        turns = [r["turn"] for r in rows
                 if (min(r["suspect_history"][0]) >= 4) == all_high]
        axes[1].scatter(turns, [int(all_high)] * len(turns), marker=marker,
                        color=color, s=44, zorder=3)
    axes[1].set_yticks([0, 1], ["1〜3を含む", "3個とも4〜6"])
    axes[1].set_ylim(-.55, 1.6)
    axes[1].set_title("② 本人の第1投を、二つに分類して対応させる",
                      loc="left", fontsize=12, pad=14)
    axes[2].plot([0] + xs, [float(p) for p in context], color=PURPLE,
                 marker="o", markersize=4, linewidth=2.6,
                 label="通常時0%・勝負どころ90%", zorder=4)
    axes[2].plot([0] + xs, [float(p) for p in constant], color=NAVY,
                 marker="s", markersize=3.5, linestyle="--", linewidth=2,
                 label="毎手番22.5%", zorder=3)
    axes[2].set_ylim(-.025, 1.12)
    axes[2].set_yticks([0, .25, .5, .75, 1])
    axes[2].yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    axes[2].set_ylabel("戦略仮説に置く確率", labelpad=14)
    axes[2].set_xlabel("観測を終えた手番数（0は観測前）", labelpad=12)
    axes[2].set_title("③ 通常賽のみと、それぞれ比較する（共通の事前確率10%）",
                      loc="left", fontsize=12, pad=14)
    axes[2].legend(loc="upper left", bbox_to_anchor=(0, -.26), ncol=2,
                   frameon=False, fontsize=11, handlelength=2.6)
    axes[2].annotate(percent(context[-1]), xy=(20, float(context[-1])),
                     xytext=(-4, 8), textcoords="offset points", ha="right",
                     color=PURPLE, fontweight="bold")
    axes[2].annotate(percent(constant[-1]), xy=(20, float(constant[-1])),
                     xytext=(-4, 12), textcoords="offset points", ha="right",
                     color=NAVY, fontweight="bold")
    fig.text(.17, .035, "説明用の仮想系列 CTX20-v1。原作の対局記録・検知性能の推定ではありません。",
             fontsize=10, color=GRAY)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DESTINATION, dpi=160, facecolor="white")
    plt.close(fig)


def main():
    rows, context, constant = exact_data()
    make_figure(rows, context, constant)
    print(f"Saved: {DESTINATION.relative_to(ROOT)}")
    print("turn | context strategy | constant-use strategy")
    for n in HIGH_TURNS:
        print(f"{n} | {percent(context[n])} | {percent(constant[n])}")


if __name__ == "__main__":
    main()

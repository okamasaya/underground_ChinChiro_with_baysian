"""Generate the Zenn episode 3 mixture and evidence-recovery figures.

Run from the repository root:
    XDG_CACHE_HOME="$PWD/build/cache" MPLCONFIGDIR="$PWD/build/matplotlib" .venv/bin/python articles/assets/plot_chinchiro_mixture.py

This is an illustrative sequence, not original manga data or a simulation
of detection performance. One die is independently selected per observation.
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
from figure_fonts import configure

OBSERVATIONS = (4, 6, 5, 4, 6, 5, 2, 4, 5, 6, 4)
PRIOR = F(1, 10)
ETA = F(9, 10)
DESTINATION = ROOT / "images/chinchiro-bayes-03-mixture"


def update(prior, high, eta=ETA):
    likelihood = (1 + eta) / 2 if high else (1 - eta) / 2
    weight_strategy = prior * likelihood
    weight_fair = (1 - prior) * F(1, 2)
    return weight_strategy / (weight_strategy + weight_fair)


def posterior_series(eta, observations=OBSERVATIONS):
    values = [PRIOR]
    cumulative_bf = F(1)
    for die in observations:
        high = die >= 4
        posterior = update(values[-1], high, eta)
        cumulative_bf *= (1 + eta) if high else (1 - eta)
        expected = PRIOR * cumulative_bf / (1 - PRIOR + PRIOR * cumulative_bf)
        assert posterior == expected
        values.append(posterior)
    return values


def decimal(value, places=1, percentage=False):
    factor = 100 if percentage else 1
    value = Decimal(value.numerator * factor) / Decimal(value.denominator)
    return str(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def exact_data():
    mixed = posterior_series(ETA)
    pure = posterior_series(F(1))
    assert [decimal(mixed[n], percentage=True) for n in range(6, 12)] == [
        "83.9", "34.3", "49.8", "65.4", "78.2", "87.2",
    ]
    assert decimal(mixed[1], percentage=True) == "17.4"
    assert decimal(pure[6], percentage=True) == "87.7"
    assert all(p == 0 for p in pure[7:])
    assert all(p == PRIOR for p in posterior_series(F(0)))
    recovery = [F(1, 10) * F(19, 10)**n for n in range(5)]
    assert recovery[3] < 1 < recovery[4]
    assert mixed[10] < mixed[6] < mixed[11]
    # The recovery multiplier applies to odds, not to posterior probability.
    reference_odds = mixed[6] / (1 - mixed[6])
    for n, multiplier in enumerate(recovery):
        odds = mixed[7 + n] / (1 - mixed[7 + n])
        assert odds / reference_odds == multiplier
    return mixed, pure, recovery


def setup():
    configure()
    plt.rcParams.update({
        "font.size": 12,
        "text.color": "#172b3a",
        "axes.labelcolor": "#172b3a",
        "xtick.color": "#435563",
        "ytick.color": "#435563",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def style(ax):
    ax.grid(axis="y", color="#e1e7ed", linewidth=.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0, pad=10)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#b5c1cc")


def comparison_figure(mixed, pure):
    fig, ax = plt.subplots(figsize=(11, 6.7), dpi=160)
    fig.subplots_adjust(left=.10, right=.97, bottom=.20, top=.72)
    fig.patch.set_facecolor("white")
    fig.text(.10, .93, "1〜3が出ても、混合戦略への疑いは残る", fontsize=21,
             fontweight="bold", ha="left")
    fig.text(.10, .865, "通常賽のみと比較。どちらの戦略仮説も事前確率10%。",
             fontsize=12, color="#526577", ha="left")
    ax.axvspan(6.75, 7.25, color="#fff0df", zorder=0)
    ax.plot(range(12), [float(p) for p in pure], color="#7e8a98",
            linestyle="--", marker="s", markersize=4.5, linewidth=1.8,
            label="常に456賽", zorder=2)
    ax.plot(range(12), [float(p) for p in mixed], color="#2e4a88",
            marker="o", markersize=5, linewidth=2.8,
            label="毎回90%の確率で456賽を選ぶ", zorder=3)
    ax.hlines(float(mixed[6]), 6, 11, color="#a3adb9", linewidth=1,
              linestyle=(0, (3, 3)), zorder=1)
    ax.set_xlim(-.15, 11.2)
    ax.set_ylim(-.025, 1.03)
    ax.set_xticks(range(12), ["観測前"] + [str(d) for d in OBSERVATIONS])
    ax.get_xticklabels()[7].set_color("#b05c00")
    ax.get_xticklabels()[7].set_fontweight("bold")
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xlabel("観測した出目（左から順番）", labelpad=14)
    ax.set_ylabel("比較する戦略仮説に置く確率", labelpad=12)
    ax.legend(loc="lower left", bbox_to_anchor=(-.01, 1.05), ncol=2,
              frameon=False, fontsize=11, handlelength=2.6)
    ax.annotate("34.3%", xy=(7, float(mixed[7])), xytext=(-10, -12),
                textcoords="offset points", ha="right", color="#2e4a88")
    ax.annotate("83.9%", xy=(6, float(mixed[6])), xytext=(-8, -24),
                textcoords="offset points", ha="right", color="#2e4a88")
    ax.annotate("4〜6が4回続き\n低下直前を上回る", xy=(11, float(mixed[11])),
                xytext=(8.6, .42), color="#2e4a88", fontsize=11,
                arrowprops={"arrowstyle": "->", "color": "#2e4a88", "lw": 1.2},
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 3})
    style(ax)
    fig.text(.10, .055, "説明用の出目列。各曲線は通常賽のみとの別々の2仮説比較。",
             fontsize=10, color="#526577")
    fig.savefig(DESTINATION / "mixture-comparison.png", dpi=160, facecolor="white")
    plt.close(fig)


def recovery_figure(recovery):
    fig, ax = plt.subplots(figsize=(10, 6.4), dpi=160)
    fig.subplots_adjust(left=.12, right=.97, bottom=.22, top=.73)
    fig.patch.set_facecolor("white")
    fig.text(.12, .93, "低下を戻すには、4〜6が4回必要", fontsize=21,
             fontweight="bold", ha="left")
    fig.text(.12, .85, "1〜3でオッズは0.1倍。その後、4〜6ごとに1.9倍。",
             fontsize=12, color="#526577", ha="left")
    ax.bar(range(5), [float(v) for v in recovery], width=.55,
           color=["#a7b5c5"] * 4 + ["#2e4a88"], zorder=3)
    ax.axhline(1, color="#65717d", linestyle=(0, (4, 3)), linewidth=1.2)
    ax.text(-.35, 1.04, "低下直前の水準", fontsize=11, color="#526577")
    for n, value in enumerate(recovery):
        ax.text(n, float(value) + .045, decimal(value, places=3),
                ha="center", va="bottom", fontsize=12, color="#172b3a")
    ax.set_ylim(0, 1.55)
    ax.set_yticks([0, .5, 1, 1.5])
    ax.set_ylabel("低下直前を1としたオッズ", labelpad=12)
    ax.set_xticks(range(5), ["1〜3の直後", "4〜6が\n1回", "4〜6が\n2回",
                             "4〜6が\n3回", "4〜6が\n4回"])
    style(ax)
    fig.text(.12, .055, "毎回90%の確率で456賽を選ぶ戦略を、通常賽のみと比較。",
             fontsize=10, color="#526577")
    fig.savefig(DESTINATION / "evidence-recovery.png", dpi=160, facecolor="white")
    plt.close(fig)


def main():
    mixed, pure, recovery = exact_data()
    setup()
    DESTINATION.mkdir(parents=True, exist_ok=True)
    comparison_figure(mixed, pure)
    recovery_figure(recovery)
    print(f"Saved two figures in: {DESTINATION.relative_to(ROOT)}")
    print("Mixture posteriors, observations 6..11:",
          [decimal(p, percentage=True) for p in mixed[6:]])
    print("Relative odds after Low then 0..4 High:", [str(v) for v in recovery])


if __name__ == "__main__":
    main()

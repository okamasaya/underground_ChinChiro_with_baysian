"""Generate the Zenn episode 2 prior-comparison chart.

Run from the repository root:
    XDG_CACHE_HOME="$PWD/build/cache" MPLCONFIGDIR="$PWD/build/matplotlib" .venv/bin/python articles/assets/plot_chinchiro_priors.py

This is a conditional illustration: every observation is High (4, 5, or 6).
It is not a simulated detection-time distribution or original manga data.
"""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
from figure_fonts import configure

PRIORS = (Fraction(1, 100), Fraction(1, 10), Fraction(1, 5), Fraction(1, 2))
N_MAX = 14
THRESHOLD = Fraction(99, 100)
DESTINATION = ROOT / "images/chinchiro-bayes-02-priors/prior-comparison.png"


def update(prior, high):
    """Compare always-fair and always-456 using one binary observation."""
    likelihood_456 = Fraction(int(high))
    likelihood_fair = Fraction(1, 2)
    weight_456 = prior * likelihood_456
    weight_fair = (1 - prior) * likelihood_fair
    return weight_456 / (weight_456 + weight_fair)


def high_series(prior):
    values = [prior]
    for n in range(1, N_MAX + 1):
        posterior = update(values[-1], high=True)
        closed_form = prior * 2**n / (1 - prior + prior * 2**n)
        assert posterior == closed_form
        values.append(posterior)
    return values


def percent(value):
    decimal = Decimal(value.numerator * 100) / Decimal(value.denominator)
    return f"{decimal.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"


def exact_data():
    series = [high_series(prior) for prior in PRIORS]
    crossings = [next(n for n, p in enumerate(values) if p >= THRESHOLD)
                 for values in series]
    assert crossings == [14, 10, 9, 7]
    assert [percent(values[7]) for values in series] == [
        "56.4%", "93.4%", "97.0%", "99.2%",
    ]
    assert series[1][7] == Fraction(128, 137)
    assert [percent(series[1][n]) for n in (0, 1, 2, 3, 4, 7, 10)] == [
        "10.0%", "18.2%", "30.8%", "47.1%", "64.0%", "93.4%", "99.1%",
    ]
    assert update(series[1][7], high=False) == 0
    assert update(Fraction(0), high=True) == 0
    for n in range(N_MAX + 1):
        assert all(series[i][n] < series[i + 1][n] for i in range(3))
    return series, crossings


def main():
    series, crossings = exact_data()
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
    fig, ax = plt.subplots(figsize=(11, 6.7), dpi=160)
    fig.subplots_adjust(left=.10, right=.97, bottom=.20, top=.72)
    fig.patch.set_facecolor("white")
    fig.text(.10, .93, "同じ出目でも、出発点で曲線は変わる", fontsize=21,
             fontweight="bold", ha="left")
    fig.text(.10, .865, "すべて4〜6を観測した場合：通常賽のみ vs 常に456賽",
             fontsize=12, color="#526577", ha="left")

    ax.axvline(7, color="#a3adb9", linestyle=(0, (3, 3)), linewidth=1.2,
               zorder=1)
    for prior, values, color, marker, style in zip(
        PRIORS, series, ("#087f8c", "#2e4a88", "#9258a0", "#b16927"),
        ("s", "o", "^", "D"), ("--", "-", "-.", ":"),
    ):
        ax.plot(range(N_MAX + 1), [float(p) for p in values],
                color=color, marker=marker, linestyle=style,
                linewidth=2.7 if prior == PRIORS[1] else 1.9,
                markersize=4.5, label=f"事前確率 {int(prior * 100)}%", zorder=3)

    ax.set_xlim(-.15, N_MAX + .2)
    ax.set_ylim(-.015, 1.03)
    ax.set_xticks([0, 2, 4, 6, 7, 8, 10, 12, 14])
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_xlabel("4〜6が連続した回数（0は観測前）", labelpad=14)
    ax.set_ylabel("常に456賽を使う仮説に置く確率", labelpad=12)
    ax.grid(axis="y", color="#e1e7ed", linewidth=.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0, pad=10)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#b5c1cc")
    ax.legend(loc="lower left", bbox_to_anchor=(-.01, 1.05), ncol=4,
              frameon=False, fontsize=11, handlelength=2.6)
    ax.annotate("7回の時点を比較", xy=(7, .46), xytext=(8.3, .38),
                fontsize=11, color="#526577",
                arrowprops={"arrowstyle": "->", "color": "#526577", "lw": 1.2},
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 3})
    fig.text(.10, .055, "サイコロ1個の二値観測。原作の対局記録ではありません。",
             fontsize=10, color="#526577")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DESTINATION, dpi=160, facecolor="white")
    plt.close(fig)
    print(f"Saved: {DESTINATION.relative_to(ROOT)}")
    print("prior | posterior after 7 High observations | first n at 99%")
    for prior, values, crossing in zip(PRIORS, series, crossings):
        print(f"{percent(prior)} | {percent(values[7])} | {crossing}")


if __name__ == "__main__":
    main()

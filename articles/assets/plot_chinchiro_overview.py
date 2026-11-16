"""Generate the Zenn episode 0 chart without changing existing paper figures.

Run from the repository root:
    XDG_CACHE_HOME="$PWD/build/cache" MPLCONFIGDIR="$PWD/build/matplotlib" .venv/bin/python articles/assets/plot_chinchiro_overview.py

The displayed observations are an illustrative, deliberately chosen sequence,
not original manga records or a random sample used to estimate performance.
"""

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

OBSERVATIONS = (4, 6, 5, 4, 6, 5, 2, 4, 5, 6)
PRIORS = (Fraction(1, 100), Fraction(1, 10), Fraction(1, 2))
ETA = Fraction(9, 10)
DESTINATION = ROOT / "images/chinchiro-bayes-00-overview/posterior.png"


def posterior_series(prior):
    """Update exactly and cross-check against the cumulative odds formula."""
    posterior = prior
    cumulative_bf = Fraction(1)
    values = [prior]
    for value in OBSERVATIONS:
        likelihood_0 = Fraction(1, 2)
        likelihood_1 = (1 + ETA) / 2 if value >= 4 else (1 - ETA) / 2
        posterior = likelihood_1 * posterior / (
            likelihood_1 * posterior + likelihood_0 * (1 - posterior)
        )
        cumulative_bf *= likelihood_1 / likelihood_0
        expected = prior * cumulative_bf / (1 - prior + prior * cumulative_bf)
        assert posterior == expected
        values.append(posterior)
    return values


def main():
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
    series = [posterior_series(prior) for prior in PRIORS]
    reference = series[1]
    assert all(reference[i] > reference[i - 1] for i in range(1, 7))
    assert reference[7] < reference[6]
    assert round(100 * float(reference[6]), 1) == 83.9
    assert round(100 * float(reference[7]), 1) == 34.3

    fig, ax = plt.subplots(figsize=(11, 6.7), dpi=160)
    fig.subplots_adjust(left=.10, right=.97, bottom=.20, top=.72)
    fig.patch.set_facecolor("white")
    fig.text(.10, .93, "同じ記録でも、疑いの推移は変わる", fontsize=21,
             fontweight="bold", ha="left")
    fig.text(.10, .865, "通常賽のみ vs 毎回90%の確率で456賽を選ぶ戦略",
             fontsize=12, color="#526577", ha="left")

    ax.axvspan(6.75, 7.25, color="#fff0df", zorder=0)
    for prior, values, color, marker, style in zip(
        PRIORS, series, ("#087f8c", "#2e4a88", "#ab527b"),
        ("s", "o", "^"), ("--", "-", "-."),
    ):
        ax.plot(range(len(values)), [float(p) for p in values],
                color=color, marker=marker, linestyle=style,
                linewidth=2.8 if prior == PRIORS[1] else 1.8,
                markersize=5, label=f"最初の確率 {int(prior * 100)}%", zorder=3)

    ax.set_xlim(-.15, 10.2)
    ax.set_ylim(-.015, 1.03)
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.set_ylabel("456賽を混ぜる戦略に置く確率", labelpad=12)
    ax.set_xticks(range(11), ["観測前"] + [str(n) for n in OBSERVATIONS])
    ax.set_xlabel("観測した出目（左から順番）", labelpad=14)
    ax.tick_params(axis="x", length=0, pad=10)
    ax.get_xticklabels()[7].set_color("#b05c00")
    ax.get_xticklabels()[7].set_fontweight("bold")
    ax.grid(axis="y", color="#e1e7ed", linewidth=.8)
    ax.set_axisbelow(True)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#b5c1cc")
    ax.legend(loc="lower left", bbox_to_anchor=(-.01, 1.05), ncol=3,
              frameon=False, fontsize=11, handlelength=2.6)
    ax.annotate("1〜3の出目で\n疑いが下がる", xy=(7, float(reference[7])),
                xytext=(7.4, .12), fontsize=12, color="#a55400",
                arrowprops={"arrowstyle": "->", "color": "#a55400", "lw": 1.3},
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 3})
    ax.annotate("83.9%", xy=(6, float(reference[6])), xytext=(-8, -23),
                textcoords="offset points", ha="right", fontsize=11,
                color="#2e4a88")
    ax.annotate("34.3%", xy=(7, float(reference[7])), xytext=(-10, -7),
                textcoords="offset points", ha="right", fontsize=11,
                color="#2e4a88")
    fig.text(.10, .055, "説明用の出目列。原作の対局記録ではありません。",
             fontsize=10, color="#526577")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DESTINATION, dpi=160, facecolor="white")
    plt.close(fig)
    print(f"Saved: {DESTINATION.relative_to(ROOT)}")
    print("Prior 10%: after six High observations "
          f"{float(reference[6]):.6%}; after Low {float(reference[7]):.6%}")


if __name__ == "__main__":
    main()

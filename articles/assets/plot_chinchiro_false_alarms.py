"""Generate the Zenn episode 6 false-alarm/first-passage figure.

Run from the repository root:
    XDG_CACHE_HOME="$PWD/build/cache" MPLCONFIGDIR="$PWD/build/matplotlib" .venv/bin/python articles/assets/plot_chinchiro_false_alarms.py

The detector compares always-fair with constant 90% 456-set use, using all
observations from a fixed start, prior 10%, and a posterior threshold of 99%.
The curves are integer-recursion results, not Monte Carlo estimates, posterior
credible intervals, or original manga data. Existing result files are not changed.
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
from figure_fonts import configure
from sequential_performance import (
    BF_THRESHOLD, PRIOR, THRESHOLD, exact_bruteforce, first_passage,
    known_boundaries, q_eta,
)

DESTINATION = ROOT / "images/chinchiro-bayes-06-false-alarms/first-passage.png"
ETA = F(9, 10)
N_MAX = 20
NAVY, GREEN, AMBER = "#2e4a88", "#167b73", "#ad7020"
GRAY, INK = "#607485", "#172b3a"


def percent(value):
    number = Decimal(str(value)) * 100
    return f"{number.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)}%"


def exact_data():
    assert PRIOR == F(1, 10) and THRESHOLD == F(99, 100)
    assert BF_THRESHOLD == 891
    assert F(1, 8) * (1 + 7 * ETA) + F(7, 8) * (1 - ETA) == 1
    boundaries = known_boundaries(ETA, N_MAX)
    for n in range(N_MAX + 1):
        for k in range(n + 1):
            factor = (1 + 7 * ETA)**k * (1 - ETA)**(n - k)
            assert (factor >= BF_THRESHOLD) == (k >= boundaries[n])
    h0 = first_passage(F(1, 8), boundaries)
    h1 = first_passage(q_eta(ETA), boundaries)
    saved = json.loads((ROOT / "analysis/sequential_performance.json").read_text())
    for key, computed in (("h0", h0), ("h1", h1)):
        for row in computed:
            old = saved[key][row["n"] - 1]
            for field in ("detection", "survival", "first_hit", "mean_min"):
                assert row[field] == old[field]
    for q, curve in ((F(1, 8), h0), (q_eta(ETA), h1)):
        # Enumerate all 2^10 paths, retaining whether they ever crossed.
        assert abs(float(exact_bruteforce(q, boundaries, 10)) - curve[9]["detection"]) < 1e-15
        assert all(a["detection"] <= b["detection"]
                   for a, b in zip(curve, curve[1:]))
    assert all(row["detection"] <= float(1 / BF_THRESHOLD) for row in h0)
    assert h0[3]["detection"] == float(F(1, 8) ** 4)
    assert h1[3]["detection"] == float(F(73, 80) ** 4)
    assert all(row["detection"] == 0 for row in h0[:3] + h1[:3])
    assert [percent(h0[n - 1]["detection"]) for n in (4, 10, 20)] == [
        "0.024%", "0.041%", "0.041%",
    ]
    assert [percent(h1[n - 1]["detection"]) for n in (4, 10, 20)] == [
        "69.332%", "99.356%", "99.994%",
    ]
    assert h0[9]["detection"] < h0[19]["detection"]
    assert percent(h1[-1]["survival"]) == "0.006%"
    # The threshold may have been crossed even when the final posterior is low.
    for bf, expected in ((F(73, 10)**3, "97.739%"),
                         (F(73, 10)**4, "99.684%"),
                         (F(73, 10)**4 / 10, "96.928%")):
        assert percent(float(bf / (9 + bf))) == expected
    for prior, threshold, upper in (
        (F(1, 100), 9801, "0.010%"),
        (F(1, 10), 891, "0.112%"),
        (F(1, 2), 99, "1.010%"),
    ):
        value = THRESHOLD / (1 - THRESHOLD) * (1 - prior) / prior
        assert value == threshold
        assert percent(float(1 / value)) == upper
    return h0, h1


def make_figure(h0, h1):
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
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 9.4), dpi=160, sharex=True)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=.14, right=.97, bottom=.16, top=.79, hspace=.57)
    fig.text(.14, .95, "一度でも99%へ到達する確率を、系列全体で調べる",
             fontsize=20, fontweight="bold", ha="left")
    fig.text(.14, .895, "事前確率10% ／ 判定閾値99% ／ 累積ベイズ因子の境界891",
             fontsize=12, color=GRAY)
    fig.text(.14, .855, "同じ判定規則を使い、相手の実際の戦略を変えて計算。",
             fontsize=11, color=GRAY)
    xs = list(range(N_MAX + 1))
    for ax in axes:
        ax.set_xlim(0, N_MAX + .25)
        ax.set_xticks(range(0, N_MAX + 1, 2))
        ax.tick_params(axis="x", length=0, pad=8)
        ax.grid(axis="y", color="#e1e7ed", linewidth=.8)
        ax.set_axisbelow(True)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#b5c1cc")
    error = [0] + [row["detection"] for row in h0]
    axes[0].step(xs, error, where="post", color=NAVY, linewidth=2.5)
    axes[0].axhline(float(1 / BF_THRESHOLD), color=AMBER,
                    linestyle=(0, (4, 3)), linewidth=1.6)
    axes[0].text(.6, float(1 / BF_THRESHOLD) + .000035,
                 "全期間の上界 1/891 ≈ 0.112%", color=AMBER, fontsize=11)
    axes[0].set_ylim(-.000025, .0014)
    axes[0].set_yticks([0, .0004, .0008, .0012])
    axes[0].yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=3))
    axes[0].set_ylabel("累積誤警報率", labelpad=12)
    axes[0].set_title("① 相手が通常賽だけ：誤って警報を出す確率",
                      loc="left", fontsize=12, pad=15)
    axes[0].scatter([20], [error[-1]], color=NAVY, s=26, zorder=3)
    axes[0].annotate(f"20手番以内 {percent(error[-1])}", (20, error[-1]),
                     xytext=(-8, 10), textcoords="offset points", ha="right",
                     color=NAVY, fontsize=11)
    detection = [0] + [row["detection"] for row in h1]
    axes[1].step(xs, detection, where="post", color=GREEN, linewidth=2.5)
    axes[1].set_ylim(-.025, 1.14)
    axes[1].set_yticks([0, .25, .5, .75, 1])
    axes[1].yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    axes[1].set_ylabel("累積検知率", labelpad=12)
    axes[1].set_xlabel("観測の上限 N（手番）", labelpad=12)
    axes[1].set_title("② 相手が毎手番90%で456賽を選ぶ：警報を出せる確率",
                      loc="left", fontsize=12, pad=15)
    axes[1].scatter([4, 20], [detection[4], detection[20]],
                    color=GREEN, s=26, zorder=3)
    axes[1].annotate(f"4手番以内 {percent(detection[4])}", (4, detection[4]),
                     xytext=(18, -38), textcoords="offset points", color=GREEN,
                     fontsize=11, arrowprops={"arrowstyle": "-", "color": GREEN})
    axes[1].annotate(f"20手番以内 {percent(detection[-1])}", (20, detection[-1]),
                     xytext=(-8, 10), textcoords="offset points", ha="right",
                     color=GREEN, fontsize=11)
    fig.text(.14, .075, "上下の縦軸は尺度が異なります。終点だけでなく、途中の到達も数えています。",
             fontsize=10, color=GRAY)
    fig.text(.14, .04, "整数再帰によるモデルの計算値。原作の実測値や、人間の気付き率ではありません。",
             fontsize=10, color=GRAY)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DESTINATION, dpi=160, facecolor="white")
    plt.close(fig)


def main():
    h0, h1 = exact_data()
    make_figure(h0, h1)
    print(f"Saved: {DESTINATION.relative_to(ROOT)}")
    print("horizon | false alarm | detection")
    for n in (4, 10, 20):
        print(f"{n} | {percent(h0[n - 1]['detection'])} | {percent(h1[n - 1]['detection'])}")
    print(f"All-time false-alarm upper bound: {percent(float(1 / BF_THRESHOLD))}")


if __name__ == "__main__":
    main()

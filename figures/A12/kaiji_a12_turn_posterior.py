#!/usr/bin/env python3
'A12: sequential strategy inference from saved, fully observed turns.\n\nRequirements: Python 3 and Matplotlib. Recreates PNG and vector PDF beside\nthis complete source; no notebook, random sample or external data needed.\nFinal size: 160 x 230 mm; PNG 400 dpi; ordinary labels at least 9 pt.\n\nOne set is selected per turn and retained for any no-role rerolls. H0 is\nalways fair. H1 selects a 456 set with eta=0.900, otherwise a fair set.\nThe posterior concerns H1, not the latent type used in the latest turn.\nAll saved turns end on throw one, but likelihoods use a complete-turn\nimplementation that also handles valid histories with up to three throws.\nLog odds are accumulated from log Bayes factors, never from rounded p.\n'

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from fractions import Fraction
from pathlib import Path
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, StrMethodFormatter, FormatStrFormatter

WIDTH_MM, HEIGHT_MM, DPI = 160, 230, 400
BASENAME = "kaiji_a12_turn_posterior"
OUT = Path(__file__).resolve().parent
INK, GRAY, GRID = "#17212B", "#6B7280", "#E2E6EB"
PURPLE, RED = "#6F4A8E", "#C4474B"
PRIOR, ETA = Fraction(1, 10), Fraction(9, 10)
THRESHOLD = Fraction(99, 100)
TURNS = [
    [[4, 4, 4]], [[6, 4, 4]], [[6, 6, 6]], [[4, 4, 5]],
    [[5, 6, 6]], [[5, 5, 6]], [[5, 4, 4]], [[4, 4, 5]],
    [[5, 4, 4]], [[4, 4, 5]], [[4, 6, 5]], [[1, 5, 1]],
    [[5, 4, 5]], [[6, 6, 5]], [[4, 4, 6]], [[5, 4, 6]],
    [[6, 5, 6]], [[6, 5, 4]], [[4, 4, 6]], [[5, 5, 6]],
]

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": GRAY, "ytick.color": GRAY,
    "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "dejavusans",
})


def no_role(x):
    return len(set(x)) == 3 and tuple(sorted(x)) not in ((1, 2, 3), (4, 5, 6))


def turn_likelihoods(turn):
    if not 1 <= len(turn) <= 3:
        raise ValueError("A complete turn contains one to three throws")
    for x in turn:
        if len(x) != 3 or any(type(face) is not int or face not in range(1, 7) for face in x):
            raise ValueError("Each throw must be an ordered triple on faces 1..6")
    if any(not no_role(x) for x in turn[:-1]):
        raise ValueError("A turn must stop immediately after a completed role")
    if len(turn) < 3 and no_role(turn[-1]):
        raise ValueError("A complete turn may stop at no role only on throw three")
    lf = Fraction(1)
    l456 = Fraction(1)
    for x in turn:
        lf *= Fraction(1, 216)
        l456 *= Fraction(1, 27) if min(x) >= 4 else Fraction(0)
    l1 = ETA * l456 + (1 - ETA) * lf
    return lf, l456, l1


def exact_data():
    if len(TURNS) != 20 or TURNS[11] != [[1, 5, 1]]:
        raise ValueError("Use the stipulated saved sequence of 20 turns")
    probs, odds, bfs = [PRIOR], [PRIOR / (1 - PRIOR)], []
    logs = [math.log10(float(odds[0]))]
    high_count = low_count = 0
    for n, turn in enumerate(TURNS, 1):
        lf, l456, l1 = turn_likelihoods(turn)
        bf = l1 / lf
        expected_bf = Fraction(1, 10) if n == 12 else Fraction(73, 10)
        if len(turn) != 1 or bf != expected_bf:
            raise ValueError("Saved turns must stop at throw one with the specified Bayes factors")
        high_count += bf == Fraction(73, 10)
        low_count += bf == Fraction(1, 10)
        previous = probs[-1]
        p = l1 * previous / (l1 * previous + lf * (1 - previous))
        o = odds[-1] * bf
        closed_o = PRIOR / (1 - PRIOR) * Fraction(73, 10) ** high_count * Fraction(1, 10) ** low_count
        if o != closed_o or p != o / (1 + o):
            raise ValueError("Bayes, odds updates and prefix-count formula disagree")
        log_o = logs[-1] + math.log10(float(bf))
        exact_log_check = math.log10(o.numerator) - math.log10(o.denominator)
        if not math.isclose(log_o, exact_log_check, abs_tol=2e-13):
            raise ValueError("Direct accumulated log odds disagree with exact odds")
        probs.append(p)
        odds.append(o)
        bfs.append(bf)
        logs.append(log_o)
    first_four = [f'{_fmt_number(float(p))}' for p in probs[1:5]]
    if first_four != ['0.448', '0.856', '0.977', '0.997']:
        raise ValueError("First four posteriors do not match the supplied checks")
    first_crossing = next(n for n, p in enumerate(probs) if p >= THRESHOLD)
    if first_crossing != 4 or not probs[3] < THRESHOLD <= probs[4]:
        raise ValueError("Incorrect first threshold crossing in this saved sequence")
    if odds[12] != odds[11] / 10 or not math.isclose(logs[12] - logs[11], -1, abs_tol=1e-13):
        raise ValueError("Turn 12 must reduce the odds tenfold and log10 odds by one")
    if not all(0 < p < 1 for p in probs) or not probs[12] < probs[11]:
        raise ValueError("Posteriors remain strictly below one and decline at turn 12")
    return probs, odds, logs, bfs, first_four


def create_figure():
    probs, odds, logs, bfs, first_four = exact_data()
    ns = list(range(21))
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    texts = []

    def text(x, y, s, **kwargs):
        kwargs.setdefault("ha", "center")
        kwargs.setdefault("va", "center")
        kwargs.setdefault("fontsize", 9)
        item = fig.text(x, y, s, **kwargs)
        texts.append(item)
        return item

    text(0.5, 0.968, "Strategy inference from full turns", fontsize=13.5, fontweight="bold")
    text(0.5, 0.934, '$p_0=0.100$   |   $H_0$: fair   |   $H_1$: 90.000% 456 + 10.000% fair', color=GRAY)
    text(0.5, 0.907, "Complete ordered throw histories retained.", color=GRAY)
    text(0.5, 0.882, "One set per turn; no-role rerolls only; at most three throws.", color=GRAY)
    text(0.13, 0.844, "A   Strategy posterior", ha="left", fontsize=10, fontweight="bold")
    text(0.13, 0.484, "B   Log10 posterior odds", ha="left", fontsize=10, fontweight="bold")
    ax1 = fig.add_axes([0.13, 0.590, 0.83, 0.230])
    ax2 = fig.add_axes([0.13, 0.230, 0.83, 0.230], sharex=ax1)
    line1, = ax1.plot(ns, [float(p) for p in probs], color=PURPLE, linewidth=1.6,
                      marker="o", markersize=3, clip_on=False, zorder=3)
    line2, = ax2.plot(ns, logs, color=PURPLE, linewidth=1.6,
                      marker="o", markersize=3, clip_on=False, zorder=3)
    ax1.axhline(float(THRESHOLD), color=GRAY, linewidth=0.8, linestyle=(0, (5, 4)), zorder=1)
    texts.append(ax1.text(15.6, 0.915, 'Threshold 0.990', fontsize=9, color=GRAY, va="center"))
    ax1.set_ylim(-0.02, 1.045)
    ax1.yaxis.set_major_locator(FixedLocator([0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    ax1.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax1.set_ylabel("Posterior probability of H1", labelpad=6)
    ax2.set_ylim(-1.6, 15.3)
    ax2.yaxis.set_major_locator(FixedLocator([0, 3, 6, 9, 12, 15]))
    ax2.yaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax2.set_ylabel("Log10 posterior odds", labelpad=6)
    for ax, values in ((ax1, [float(p) for p in probs]), (ax2, logs)):
        ax.axvline(12, color=RED, alpha=0.6, linewidth=0.8, linestyle=(0, (3, 3)))
        ax.plot([12], [values[12]], marker="o", markersize=5, color=RED, zorder=5)
        ax.set_xlim(0, 20)
        ax.xaxis.set_major_locator(FixedLocator(list(range(0, 21, 2))))
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
        ax.set_xlabel("Number of fully observed turns", labelpad=4)
        ax.tick_params(length=3, pad=3)
        ax.set_axisbelow(True)
        ax.grid(color=GRID, linewidth=0.65)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#9AA5B1")
    ax2.plot([11, 12], [logs[11], logs[12]], color=RED, linewidth=1.8, zorder=4)
    annotation_box = {"facecolor": "white", "edgecolor": "none", "pad": 1.5}
    texts.append(ax1.annotate('First p ≥ 0.990\nat turn 4', xy=(4, float(probs[4])),
                              xytext=(1.8, 0.60), fontsize=9, color=GRAY, ha="left", va="center",
                              bbox=annotation_box,
                              arrowprops={"arrowstyle": "-", "color": GRAY, "lw": 0.8}))
    texts.append(ax1.annotate('Turn 12: (1, 5, 1)\nBayes factor = 0.100',
                              xy=(12, float(probs[12])), xytext=(10.4, 0.66),
                              fontsize=9, color=RED, ha="left", va="center", bbox=annotation_box,
                              arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.8}))
    texts.append(ax1.text(7.2, 0.08,
                          "First four p values (rounded):\n" + ", ".join(first_four[:2]) + ",\n" + ", ".join(first_four[2:]),
                          fontsize=9, ha="left", va="bottom", bbox=annotation_box))
    texts.append(ax2.annotate('Odds × 0.100\nΔ log10 odds = -1', xy=(12, logs[12]),
                              xytext=(13.5, 4.6), fontsize=9, color=RED, ha="left", va="center",
                              bbox=annotation_box,
                              arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.8}))
    # Format the small complement, not a rounded posterior equal to 1.000000.
    complement = 1 - probs[-1]
    mantissa, exponent = f'{_fmt_scientific(float(complement))}'.split("e")
    text(0.5, 0.521,
         f'At turn 20: $1-p_{{20}}\\approx{mantissa}\\times10^{{{int(exponent)}}}$, so $p_{{20}}<1$.',
         fontsize=9.5, color=PURPLE)
    text(0.5, 0.146,
         r"$\log_{10}O_n=\log_{10}\!\left(\frac{p_0}{1-p_0}\right)+\sum_{t=1}^{n}\log_{10}\!\left(\frac{L_1(T_t)}{L_F(T_t)}\right)$",
         fontsize=10.5)
    text(0.5, 0.092, "All saved turns stop on throw 1; n = 0 is the prior.", color=GRAY)
    text(0.5, 0.060, "One illustrative sequence; not an error-rate or detection-delay estimate.", color=GRAY)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax in (ax1, ax2):
        texts += ax.get_xticklabels() + ax.get_yticklabels() + [ax.xaxis.label, ax.yaxis.label]
    for item in texts:
        b = item.get_window_extent(renderer)
        if item.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {item.get_text()}')
        if b.x0 < 0 or b.y0 < 0 or b.x1 > fig.bbox.width or b.y1 > fig.bbox.height:
            raise ValueError(f'Clipped text: {item.get_text()}')
    for i, a in enumerate(texts):
        ba = a.get_window_extent(renderer)
        for b in texts[i+1:]:
            bb = b.get_window_extent(renderer)
            if (min(ba.x1, bb.x1) - max(ba.x0, bb.x0) > 0.5
                    and min(ba.y1, bb.y1) - max(ba.y0, bb.y0) > 0.5):
                raise ValueError(f'Text collision: {a.get_text()} / {b.get_text()}')
    for ax in (ax1, ax2):
        if list(ax.get_xticks()) != list(range(0, 21, 2)) or any(not t.get_text().isdigit() for t in ax.get_xticklabels()):
            raise ValueError("Both turn-count axes must use integer ticks and labels")
    for curve, values in ((line1, [float(p) for p in probs]), (line2, logs)):
        if list(curve.get_xdata()) != ns or any(not math.isclose(a, b) for a, b in zip(curve.get_ydata(), values)):
            raise ValueError("Plotted values disagree with computed posteriors or direct log odds")
    return fig, probs, logs, first_four, len(texts)


def main():
    fig, probs, logs, first_four, text_count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A12 - Strategy posterior from fully observed turns",
        "Subject": "Exact strategy updates and directly accumulated log odds; saved full-turn histories",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "saved_turns": TURNS, "first_four_posteriors": first_four,
        "turn_12_log10_odds_change": logs[12] - logs[11],
        "final_posterior_complement": float(1 - probs[-1]), "final_log10_odds": logs[-1],
        "first_99_percent_crossing_in_saved_sequence": 4,
        "exact_likelihoods_bayes_odds_and_prefix_formula_agree": True,
        "direct_log_odds_and_exact_odds_agree": True, "points_per_panel": 21,
        "both_integer_turn_axes_checked": True, "text_elements_checked": text_count,
        "text_bounds_and_collisions_checked": True,
    }))


if __name__ == "__main__":
    main()

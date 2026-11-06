#!/usr/bin/env python3
'A06: asymmetric evidence in an independently selected single-die mixture.\n\nRequirements: Python 3 and Matplotlib. No notebook or external data needed.\nRun this source to recreate the PNG and vector PDF beside it.\nFinal width 160 mm; height 195 mm; PNG 400 dpi; ordinary labels >= 9 pt.\n\nH0 always uses a fair die. Under H1, select a 456 die with probability 0.900\nand a fair die with probability 0.100, independently for EVERY observation.\nThis is not the shared dice-set/turn model. The plotted posterior is P(H1|data),\nnot the probability that the most recent observation used a 456 die.\n'

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
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FixedLocator, StrMethodFormatter, FormatStrFormatter

WIDTH_MM, HEIGHT_MM, DPI = 160, 195, 400
BASENAME = "kaiji_a06_mixed_single_die"
OUT = Path(__file__).resolve().parent
INK, GRAY, GRID = "#17212B", "#6B7280", "#E2E6EB"
PURPLE, AMBER, RED = "#6F4A8E", "#D98C3F", "#C4474B"
SEQUENCE = "HHLHHHHHHHHHHHHHHHHH"
PRIOR, ETA = Fraction(1, 10), Fraction(9, 10)
LIKELIHOOD_0 = {"H": Fraction(1, 2), "L": Fraction(1, 2)}
LIKELIHOOD_1 = {"H": ETA + (1 - ETA) / 2, "L": (1 - ETA) / 2}
BF = {key: LIKELIHOOD_1[key] / LIKELIHOOD_0[key] for key in ("H", "L")}

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": GRAY, "ytick.color": GRAY,
    "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "dejavusans",
})


def exact_data():
    if len(SEQUENCE) != 20 or SEQUENCE != "HH" + "L" + "H" * 17:
        raise ValueError("Use the stipulated, saved 20-outcome sequence")
    if BF != {"H": Fraction(19, 10), "L": Fraction(1, 10)}:
        raise ValueError("Incorrect likelihood ratios")
    ns = list(range(len(SEQUENCE) + 1))
    probs, odds = [PRIOR], [PRIOR / (1 - PRIOR)]
    h = low = 0
    for outcome in SEQUENCE:
        h += outcome == "H"
        low += outcome == "L"
        p = probs[-1]
        numerator = LIKELIHOOD_1[outcome] * p
        p_next = numerator / (numerator + LIKELIHOOD_0[outcome] * (1 - p))
        o_next = odds[-1] * BF[outcome]
        o_closed = PRIOR / (1 - PRIOR) * BF["H"] ** h * BF["L"] ** low
        if o_next != o_closed or p_next != o_closed / (1 + o_closed):
            raise ValueError("Bayes, odds updates and closed form disagree")
        probs.append(p_next)
        odds.append(o_next)
    if probs[2] != Fraction(361, 1261) or probs[3] != Fraction(361, 9361):
        raise ValueError("Incorrect probabilities immediately before or after Low")
    recovery = next(m for m in range(21) if BF["L"] * BF["H"] ** m >= 1)
    if recovery != 4 or not odds[6] < odds[2] <= odds[7]:
        raise ValueError("Four consecutive High observations are required for recovery")
    if BF["L"] * BF["H"] ** 3 != Fraction(6859, 10000):
        raise ValueError("Incorrect three-High recovery factor")
    if BF["L"] * BF["H"] ** 4 != Fraction(130321, 100000):
        raise ValueError("Incorrect four-High recovery factor")
    if not 0 < probs[3] < probs[2] or probs[3] == probs[2] / 10:
        raise ValueError("A tenfold odds decrease is not a tenfold probability decrease")
    if f'{_fmt_number(float(probs[-1]))}' != '1.000':
        raise ValueError("Unexpected final posterior")
    return ns, probs, odds, recovery


def create_figure():
    ns, probs, odds, recovery = exact_data()
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

    text(0.5, 0.953, "Asymmetric evidence in a\nsingle-die mixture",
         fontsize=13.5, fontweight="bold", linespacing=1.3)
    text(0.5, 0.897, '$p_0=0.100$   |   $H_0$: fair   |   $H_1$: 90.000% 456 + 10.000% fair',
         color=GRAY)
    text(0.5, 0.870, "Select the die type independently for each observation.", color=GRAY)

    text(0.12, 0.831, "A   Posterior along the saved sequence",
         ha="left", fontsize=9.5, fontweight="bold")
    text(0.12, 0.803, "Data", ha="right", color=GRAY)
    # Outcome ribbon aligned to the same integer observation positions as the plot.
    for n, outcome in enumerate(SEQUENCE, 1):
        text(0.12 + 0.84 * n / 20, 0.803, outcome,
             color=RED if outcome == "L" else GRAY,
             fontweight="bold" if outcome == "L" else "normal")

    ax = fig.add_axes([0.12, 0.510, 0.84, 0.273])
    curve, = ax.plot(ns, [float(v) for v in probs], color=PURPLE,
                     linewidth=1.6, marker="o", markersize=3.1,
                     clip_on=False, zorder=3)
    ax.axvline(3, color=RED, linewidth=0.9, linestyle=(0, (3, 3)), alpha=0.7)
    low_point, = ax.plot([3], [float(probs[3])], marker="o", markersize=5,
                         color=RED, zorder=5)
    recovered, = ax.plot([7], [float(probs[7])], marker="o", markersize=5,
                         markerfacecolor="white", markeredgecolor=PURPLE,
                         markeredgewidth=1.3, zorder=5)
    annotations = [
        ax.annotate(f'Before Low: {_fmt_number(float(probs[2]))}',
                    xy=(2, float(probs[2])), xytext=(0.8, 0.56),
                    fontsize=9, color=INK, ha="left", va="center",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5},
                    arrowprops={"arrowstyle": "-", "color": GRAY, "lw": 0.8}),
        ax.annotate(f'Low at n = 3\np = {_fmt_number(float(probs[3]))}',
                    xy=(3, float(probs[3])), xytext=(11.4, 0.08),
                    fontsize=9, color=RED, ha="left", va="bottom",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5},
                    arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.8}),
        ax.annotate("4 High after Low\nexceed the pre-Low level",
                    xy=(7, float(probs[7])), xytext=(9.8, 0.39),
                    fontsize=9, color=PURPLE, ha="left", va="center",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5},
                    arrowprops={"arrowstyle": "-", "color": PURPLE, "lw": 0.8}),
    ]
    ax.set_xlim(0, 20)
    ax.set_ylim(-0.02, 1.045)
    ax.xaxis.set_major_locator(FixedLocator(list(range(0, 21, 2))))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax.yaxis.set_major_locator(FixedLocator([0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.set_xlabel("Number of observed die outcomes", labelpad=5)
    ax.set_ylabel("Posterior probability of H1", labelpad=6)
    ax.set_axisbelow(True)
    ax.grid(color=GRID, linewidth=0.65)
    ax.tick_params(length=3, pad=3)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#9AA5B1")

    text(0.5, 0.442,
         f'Final posterior: $p_{{20}}={_fmt_number(float(probs[-1]))}$   |   n = 0 is the prior.')
    text(0.08, 0.400, r"B   Evidence multipliers for odds $O_n=p_n/(1-p_n)$",
         ha="left", fontsize=9.5, fontweight="bold")

    cards = []
    for left, outcome, heading, color in (
            (0.08, "H", "High (4, 5, 6)", AMBER),
            (0.54, "L", "Low (1, 2, 3)", RED)):
        card = FancyBboxPatch((left, 0.240), 0.42, 0.139,
                              transform=fig.transFigure,
                              boxstyle="round,pad=0.005,rounding_size=0.008",
                              facecolor="#FFFAF2" if outcome == "H" else "#FFF5F5",
                              edgecolor=color, linewidth=0.7, zorder=0)
        fig.add_artist(card)
        cards.append(card)
        center = left + 0.21
        text(center, 0.357, heading, color=color, fontsize=10, fontweight="bold")
        text(center, 0.324, f'$P({outcome}\\mid H_1)={_fmt_number(float(LIKELIHOOD_1[outcome]))}$')
        text(center, 0.295, f'$P({outcome}\\mid H_0)={_fmt_number(float(LIKELIHOOD_0[outcome]))}$')
        text(center, 0.262, f'{heading.split()[0]}: odds ×{_fmt_number(float(BF[outcome]))}',
             color=color, fontsize=10, fontweight="bold")

    text(0.5, 0.208, "Recovering the odds immediately before the Low", fontweight="bold")
    text(0.5, 0.169,
         '$0.100\\,(1.900)^m\\geq1\\quad\\Longrightarrow\\quad m\\geq4$ (integer)',
         fontsize=11)
    text(0.5, 0.130,
         '$0.100\\,(1.900)^3\\approx0.686<1$;   $0.100\\,(1.900)^4\\approx1.303\\geq1$')
    text(0.5, 0.080,
         "Multipliers act on odds, not directly on probabilities.", color=GRAY)
    text(0.5, 0.050,
         "One illustrative sequence; not an average detection time.", color=GRAY)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts += annotations + [ax.xaxis.label, ax.yaxis.label]
    texts += ax.get_xticklabels() + ax.get_yticklabels()
    for item in texts:
        if item.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {item.get_text()}')
        b = item.get_window_extent(renderer)
        if b.x0 < 0 or b.y0 < 0 or b.x1 > fig.bbox.width or b.y1 > fig.bbox.height:
            raise ValueError(f'Clipped text: {item.get_text()}')
    if list(ax.get_xticks()) != list(range(0, 21, 2)):
        raise ValueError("Count ticks must be integers 0,2,...,20")
    if any(not item.get_text().isdigit() for item in ax.get_xticklabels()):
        raise ValueError("Count tick labels must be integers")
    if list(curve.get_xdata()) != ns or any(
            not math.isclose(y, float(p)) for y, p in zip(curve.get_ydata(), probs)):
        raise ValueError("Plotted points disagree with exact computed values")
    if list(low_point.get_xdata()) != [3] or list(recovered.get_xdata()) != [7]:
        raise ValueError("Incorrect Low or recovery marker position")
    return fig, probs, odds, recovery


def main():
    fig, probs, odds, recovery = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A06 - Asymmetric evidence in the single-die mixture",
        "Subject": "Bayesian strategy posterior; independent die-type selection per observation",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "saved_sequence": SEQUENCE, "points": len(probs),
        "posterior_before_low": float(probs[2]), "posterior_after_low": float(probs[3]),
        "posterior_after_four_high": float(probs[7]),
        "final_posterior": float(probs[-1]), "recovery_high_count": recovery,
        "exact_bayes_odds_closed_form_agree": True, "integer_ticks_checked": True,
        "text_bounds_checked": True,
    }))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
'A03: one Bayesian update as likelihood weighting and normalization.\n\nRequirements: Python 3 and Matplotlib.\nExecute this source to recreate its PNG and vector PDF in the same folder.\nThe figure is 160 x 238 mm, with ordinary text at least 9 pt.\nThis is the PURE single-die model, not the 90.000% mixture model.\n'

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from pathlib import Path
from fractions import Fraction
from itertools import combinations
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

WIDTH_MM, HEIGHT_MM, DPI = 160, 238, 400
BASENAME = "kaiji_a03_bayes_update"
OUT = Path(__file__).resolve().parent
INK = "#17212B"
NAVY = "#2B5D7E"
AMBER = "#D98C3F"
GRAY = "#6B7280"
LINE = "#CBD3DC"
PALE_BLUE = "#F0F5F8"
PALE_AMBER = "#FCF4E9"
PALE_GRAY = "#F6F7F9"

plt.rcParams.update({
    "font.family": "Article JP Sans",
    "font.size": 9,
    "text.color": INK,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "mathtext.fontset": "dejavusans",
})


def exact_update():
    prior1, prior0 = Fraction(1, 10), Fraction(9, 10)
    likelihood1, likelihood0 = Fraction(1), Fraction(1, 2)
    weight1, weight0 = prior1 * likelihood1, prior0 * likelihood0
    evidence = weight1 + weight0
    posterior1, posterior0 = weight1 / evidence, weight0 / evidence
    prior_odds = prior1 / prior0
    bayes_factor = likelihood1 / likelihood0
    posterior_odds = posterior1 / posterior0
    assert prior1 + prior0 == posterior1 + posterior0 == 1
    assert evidence == Fraction(11, 20)
    assert (posterior1, posterior0) == (Fraction(2, 11), Fraction(9, 11))
    assert prior_odds * bayes_factor == posterior_odds == Fraction(2, 9)
    return {
        "prior1": prior1, "prior0": prior0,
        "weight1": weight1, "weight0": weight0, "evidence": evidence,
        "posterior1": posterior1, "posterior0": posterior0,
    }


def create_figure():
    values = exact_update()
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH_MM)
    ax.set_ylim(HEIGHT_MM, 0)
    ax.set_axis_off()
    texts = []
    stack_widths = []

    def text(x, y, label, size=9, color=INK, weight="normal", ha="left"):
        artist = ax.text(
            x, y, label, fontsize=size, color=color, fontweight=weight,
            ha=ha, va="center", linespacing=1.15, zorder=5,
        )
        texts.append(artist)
        return artist

    def box(x, y, w, h, face="white", edge=LINE, radius=1.2):
        patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f'round,pad=0,rounding_size={radius}',
            facecolor=face, edgecolor=edge, linewidth=0.8, zorder=1,
        )
        ax.add_patch(patch)

    def arrow(y1, y2):
        ax.add_patch(FancyArrowPatch(
            (80, y1), (80, y2), arrowstyle="-|>", mutation_scale=8,
            color=GRAY, linewidth=0.9, shrinkA=0, shrinkB=0, zorder=2,
        ))

    def stage(top, height, number, title):
        box(2, top, 156, height, radius=1.6)
        box(6, top + 4, 7, 7, face=INK, edge=INK, radius=1)
        text(9.5, top + 7.5, str(number), color="white", weight="bold", ha="center")
        text(17, top + 7.5, title, size=11, weight="bold")

    def probability_bar(y, p1, p0, label1, label0):
        x, width, height = 10, 140, 7
        w1, w0 = float(p1 * width), float(p0 * width)
        ax.add_patch(Rectangle((x, y), w1, height, facecolor=AMBER,
                               edgecolor="none", zorder=2))
        ax.add_patch(Rectangle((x + w1, y), w0, height, facecolor=NAVY,
                               edgecolor="none", zorder=2))
        text(x + w1 / 2, y + height / 2, label1,
             color="white", weight="bold", ha="center")
        text(x + w1 + w0 / 2, y + height / 2, label0,
             color="white", weight="bold", ha="center")
        stack_widths.append((w1 / width, w0 / width))

    text(80, 7, "One Bayesian update", size=13.5, weight="bold", ha="center")
    text(80, 14.5, "Pure single-die model: observe one High outcome",
         color=GRAY, ha="center")
    text(42, 23, r"$H_1$: always 456", size=9.5, color=AMBER,
         weight="bold", ha="center")
    text(118, 23, r"$H_0$: always fair", size=9.5, color=NAVY,
         weight="bold", ha="center")

    # Stage 1: probabilities before the new observation.
    stage(30, 29, 1, "Prior probabilities")
    text(42, 45.2, '$P(H_1)=0.100$', size=10, color=AMBER, ha="center")
    text(118, 45.2, '$P(H_0)=0.900$', size=10, color=NAVY, ha="center")
    probability_bar(50.5, values["prior1"], values["prior0"], '10.000%', '90.000%')
    arrow(59.6, 63.5)

    # Stage 2: weights are not yet normalized probabilities.
    stage(65, 65, 2, "Multiply by the likelihood")
    box(43, 78.5, 74, 7, face=PALE_GRAY, edge=LINE, radius=1)
    text(80, 82, "Observed: High = {4, 5, 6}", ha="center")
    box(8, 90, 68, 18, face=PALE_AMBER, edge=AMBER)
    box(84, 90, 68, 18, face=PALE_BLUE, edge=NAVY)
    text(42, 95, '$P(\\mathrm{High}\\mid H_1)=1.000$',
         size=9.5, color=AMBER, ha="center")
    text(118, 95, '$P(\\mathrm{High}\\mid H_0)=0.500$',
         size=9.5, color=NAVY, ha="center")
    text(42, 103, '$w_1=0.100\\times1.000=0.100$',
         size=10, color=AMBER, ha="center")
    text(118, 103, '$w_0=0.900\\times0.500=0.450$',
         size=10, color=NAVY, ha="center")
    text(80, 111.8, "Unnormalized weights", color=GRAY, ha="center")
    text(80, 117.5, "Predictive probability / normalization",
         color=GRAY, ha="center")
    text(80, 126, '$P(\\mathrm{High})=w_1+w_0=0.100+0.450=0.550$',
         size=10, ha="center")
    arrow(130.6, 134.5)

    # Stage 3: divide both weights by the same predictive probability.
    stage(136, 43, 3, "Normalize to posterior probabilities")
    text(42, 154,
         '$P(H_1\\mid\\mathrm{High})=\\frac{0.100}{0.550}=\\frac{2}{11}$',
         size=9.5, color=AMBER, ha="center")
    text(118, 154,
         '$P(H_0\\mid\\mathrm{High})=\\frac{0.450}{0.550}=\\frac{9}{11}$',
         size=9.5, color=NAVY, ha="center")
    text(42, 162, '$\\approx0.182$', size=10, color=AMBER, ha="center")
    text(118, 162, '$\\approx0.818$', size=10, color=NAVY, ha="center")
    probability_bar(169, values["posterior1"], values["posterior0"],
                    '18.182%', '81.818%')

    # General sequential update: posterior from the previous step becomes prior.
    text(80, 187, "Sequential update: use the previous posterior as the next prior",
         size=9, color=GRAY, ha="center")
    text(80, 199,
         r"$p_t=\frac{\ell_1(D_t)\,p_{t-1}}"
         r"{\ell_1(D_t)\,p_{t-1}+\ell_0(D_t)(1-p_{t-1})}$",
         size=11.5, ha="center")
    text(45, 208, r"$p_t=P(H_1\mid D_{1:t})$",
         size=9.5, color=GRAY, ha="center")
    text(117, 208, r"$\ell_i(D_t)=P(D_t\mid H_i)$",
         size=9.5, color=GRAY, ha="center")

    # An independent check in odds, not another posterior percentage.
    box(2, 214, 156, 20, face=PALE_GRAY, edge=LINE, radius=1.5)
    text(9, 220, "Odds check", weight="bold")
    text(9, 228, r"$H_1:H_0$", color=GRAY)
    text(51, 219.5, "Prior odds", color=GRAY, ha="center")
    text(91, 219.5, "Likelihood ratio", color=GRAY, ha="center")
    text(133, 219.5, "Posterior odds", color=GRAY, ha="center")
    text(51, 228, "1/9", size=11, ha="center")
    text(70, 228, "×", size=11, color=GRAY, ha="center")
    text(91, 228, "2", size=11, ha="center")
    text(111, 228, "=", size=11, color=GRAY, ha="center")
    text(133, 228, "2/9", size=11, ha="center")

    # Validation: exact math, proportional stacked bars and readable labels.
    expected = [
        (float(values["prior1"]), float(values["prior0"])),
        (float(values["posterior1"]), float(values["posterior0"])),
    ]
    for actual, correct in zip(stack_widths, expected):
        if any(abs(a - b) > 1e-12 for a, b in zip(actual, correct)):
            raise ValueError("Probability bar proportions differ from exact values")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bboxes = [t.get_window_extent(renderer) for t in texts]
    for t, extent in zip(texts, bboxes):
        if t.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {t.get_text()}')
        if (extent.x0 < 0 or extent.y0 < 0 or
                extent.x1 > fig.bbox.width or extent.y1 > fig.bbox.height):
            raise ValueError(f'Clipped text: {t.get_text()}')
    for (i, a), (j, b) in combinations(enumerate(bboxes), 2):
        if a.overlaps(b):
            raise ValueError(f'Overlapping text: {texts[i].get_text()} / {texts[j].get_text()}')
    return fig, len(texts)


def main():
    fig, count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A03 - Bayesian update as normalization of two weights",
        "Subject": 'Pure single-die model, one observed High, prior 10.000%',
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)],
        "size_mm": [WIDTH_MM, HEIGHT_MM],
        "posterior_h1": "2/11", "posterior_h0": "9/11",
        "predictive_probability": "11/20",
        "prior_odds": "1/9", "bayes_factor": 2, "posterior_odds": "2/9",
        "proportions_checked": True, "text_labels_checked": count,
        "label_overlaps": 0,
    }))


if __name__ == "__main__":
    main()

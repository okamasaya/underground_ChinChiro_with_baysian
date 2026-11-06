#!/usr/bin/env python3
"""A02: exact single-die probability distributions and outcome means.

Requirements: Python 3, Matplotlib.
Run this source to recreate the PNG and vector PDF in the same directory.
Final size: 160 x 119 mm, 400-dpi PNG, ordinary text at least 9 pt.
"""

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
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, StrMethodFormatter, FormatStrFormatter

WIDTH_MM, HEIGHT_MM, DPI = 160, 119, 400
BASENAME = "kaiji_a02_die_distributions"
OUT = Path(__file__).resolve().parent
INK, NAVY, AMBER = "#17212B", "#2B5D7E", "#D98C3F"
GRAY, GRID = "#6B7280", "#E2E6EB"

FACES = tuple(range(1, 7))
FAIR = (Fraction(1, 6),) * 6
RIGGED = (Fraction(0),) * 3 + (Fraction(1, 3),) * 3

plt.rcParams.update({
    "font.family": "Article JP Sans",
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": GRAY,
    "ytick.color": GRAY,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "mathtext.fontset": "dejavusans",
})


def validate_distributions():
    for probabilities in (FAIR, RIGGED):
        if sum(probabilities) != 1:
            raise ValueError("A probability distribution is not normalized")
        if any(p < 0 for p in probabilities):
            raise ValueError("A probability is negative")
    fair_mean = sum(k * p for k, p in zip(FACES, FAIR))
    rigged_mean = sum(k * p for k, p in zip(FACES, RIGGED))
    if fair_mean != Fraction(7, 2) or rigged_mean != 5:
        raise ValueError("Unexpected outcome mean")
    return fair_mean, rigged_mean


def create_figure():
    means = validate_distributions()
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.956, "Single-die distributions",
             ha="center", va="center", fontsize=13.5, fontweight="bold")
    fig.text(0.5, 0.899, "Pure distributions before any mixing",
             ha="center", va="center", fontsize=9, color=GRAY)

    left = fig.add_axes([0.105, 0.33, 0.39, 0.48])
    right = fig.add_axes([0.58, 0.33, 0.39, 0.48], sharey=left)
    axes = (left, right)
    annotations = []

    for ax, probabilities, title, color, mean in zip(
        axes, (FAIR, RIGGED), ("Fair die", "456 die"),
        (NAVY, AMBER), means
    ):
        heights = [float(p) for p in probabilities]
        ax.bar(FACES, heights, width=0.64, color=color,
               edgecolor=color, linewidth=0.8, zorder=3)
        ax.set_xlim(0.5, 6.5)
        ax.set_ylim(0, 0.4)
        ax.xaxis.set_major_locator(FixedLocator(FACES))
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
        ax.yaxis.set_major_locator(FixedLocator([0, 0.1, 0.2, 0.3, 0.4]))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=GRID, linewidth=0.65)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#9AA5B1")
        ax.spines["bottom"].set_color("#9AA5B1")
        ax.tick_params(axis="both", length=3, pad=3)
        ax.set_xlabel("Face value", labelpad=5)
        ax.set_title(title, fontsize=11, fontweight="bold", color=color, pad=13)
        ax.axvline(float(mean), color=GRAY, linestyle=(0, (3, 2)),
                   linewidth=1.0, zorder=2)
        annotations.append(ax.text(
            float(mean), 0.385, f'Mean {_fmt_number(float(mean))}',
            ha="center", va="center", fontsize=9, color=GRAY,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0},
            zorder=5,
        ))
        for face, p in zip(FACES, probabilities):
            if p > 0:
                label = f'{p.numerator}/{p.denominator}'
                annotations.append(ax.text(
                    face, float(p) + 0.013, label, fontsize=9,
                    ha="center", va="bottom", color=INK,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6},
                    zorder=5,
                ))
            else:
                ax.plot(face, 0, "o", markerfacecolor="white",
                        markeredgecolor=GRAY, markersize=4.3,
                        markeredgewidth=0.9, clip_on=False, zorder=5)
                annotations.append(ax.text(
                    face, 0.019, "0", fontsize=9, ha="center",
                    va="bottom", color=GRAY, zorder=5,
                ))
    left.set_ylabel("Probability", labelpad=5)
    right.tick_params(axis="y", labelleft=False)

    annotations.append(fig.text(
        0.30, 0.178,
        '$E[X_F]=\\frac{1+2+3+4+5+6}{6}=3.500$',
        fontsize=10, color=NAVY, ha="center", va="center",
    ))
    annotations.append(fig.text(
        0.775, 0.178,
        '$E[X_{456}]=\\frac{4+5+6}{3}=5.000$',
        fontsize=10, color=AMBER, ha="center", va="center",
    ))
    annotations.append(fig.text(
        0.5, 0.054, "Mean die outcome; not expected game profit.",
        fontsize=9, color=GRAY, ha="center", va="center",
    ))

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = list(fig.texts)
    for ax in axes:
        texts.extend(ax.texts)
        texts.extend([ax.title, ax.xaxis.label, ax.yaxis.label])
        texts.extend(ax.get_xticklabels())
        texts.extend(ax.get_yticklabels())
    texts = [t for t in texts if t.get_visible() and t.get_text()]
    for text in texts:
        extent = text.get_window_extent(renderer)
        if text.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {text.get_text()}')
        if (extent.x0 < 0 or extent.y0 < 0 or
                extent.x1 > fig.bbox.width or extent.y1 > fig.bbox.height):
            raise ValueError(f'Clipped text: {text.get_text()}')
    for a, b in combinations(annotations, 2):
        if a.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)):
            raise ValueError(f'Overlapping annotations: {a.get_text()}, {b.get_text()}')
    for ax, expected in zip(axes, (FAIR, RIGGED)):
        if any(not math.isclose(bar.get_height(), float(p))
               for bar, p in zip(ax.patches, expected)):
            raise ValueError("Bar heights differ from exact probabilities")
        if list(ax.get_xticks()) != list(FACES):
            raise ValueError("Non-integer face ticks")
        if any(not label.get_text().isdigit() for label in ax.get_xticklabels()):
            raise ValueError("Face tick labels must be integers")
    if left.get_ylim() != right.get_ylim():
        raise ValueError("Probability axes do not match")
    return fig


def main():
    fig = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A02 - Single-die distributions and outcome means",
        "Subject": "Fair die and pure 456 die probability distributions",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)],
        "size_mm": [WIDTH_MM, HEIGHT_MM],
        "fair_mean": 3.5, "rigged_mean": 5.0,
        "normalization_checked": True,
        "integer_face_ticks_checked": True,
        "bar_heights_checked": True,
        "annotation_overlaps": 0,
    }))


if __name__ == "__main__":
    main()

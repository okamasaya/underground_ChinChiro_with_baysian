#!/usr/bin/env python3
"""A04: pure-456 hypothesis posterior after consecutive High outcomes.

Requirements: Python 3 and Matplotlib.
Run this source to recreate the PNG and vector PDF in the same folder.
Size: 160 x 134 mm; 400-dpi PNG; ordinary labels at least 9 pt.
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

WIDTH_MM, HEIGHT_MM, DPI = 160, 134, 400
BASENAME = "kaiji_a04_pure_posterior"
OUT = Path(__file__).resolve().parent
INK, PURPLE = "#17212B", "#6F4A8E"
NAVY, AMBER = "#2B5D7E", "#D98C3F"
GRAY, GRID = "#6B7280", "#E2E6EB"
PRIOR = Fraction(1, 10)
THRESHOLD = Fraction(99, 100)
N_MAX = 20

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


def exact_series():
    ns = list(range(N_MAX + 1))
    ps = [PRIOR * 2**n / (1 - PRIOR + PRIOR * 2**n) for n in ns]
    q = PRIOR
    for n, expected in zip(ns, ps):
        if n:
            q = q / (q + Fraction(1, 2) * (1 - q))
        if q != expected:
            raise ValueError("Sequential and closed-form posteriors disagree")
    if ps[7] != Fraction(128, 137) or ps[10] != Fraction(1024, 1033):
        raise ValueError("Unexpected annotated fractions")
    first = next(n for n, p in zip(ns, ps) if p >= THRESHOLD)
    if first != 10 or not ps[9] < THRESHOLD <= ps[10]:
        raise ValueError("Wrong first posterior-threshold crossing")
    if not all(a < b for a, b in zip(ps[:-1], ps[1:])):
        raise ValueError("Posterior must increase under consecutive High outcomes")
    return ns, ps, first


def create_figure():
    ns, exact, first = exact_series()
    ps = [float(p) for p in exact]
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.958, "Pure 456 hypothesis: consecutive High outcomes",
             ha="center", va="center", fontsize=12, fontweight="bold")
    fig.text(0.5, 0.905, 'All observations are High; prior = 10.000%',
             ha="center", va="center", fontsize=9.5, color=GRAY)
    fig.text(0.5, 0.856, r"$H_1$: always 456   |   $H_0$: always fair",
             ha="center", va="center", fontsize=9, color=GRAY)

    ax = fig.add_axes([0.12, 0.305, 0.84, 0.49])
    threshold_line = ax.axhline(
        float(THRESHOLD), color=GRAY, linewidth=1.1, linestyle=(0, (4, 3)),
        label='Posterior threshold = 0.990', zorder=2,
    )
    posterior_line, = ax.plot(
        ns, ps, marker="o", markersize=3.5, linewidth=1.75,
        color=PURPLE, label="Posterior of pure H1", zorder=3,
        clip_on=False,
    )
    for n, color in [(7, NAVY), (10, AMBER)]:
        ax.scatter([n], [ps[n]], s=40, facecolors="white",
                   edgecolors=color, linewidths=1.6, zorder=5)
    ax.set_xlim(0, N_MAX)
    ax.set_ylim(-0.02, 1.04)
    ax.xaxis.set_major_locator(FixedLocator(list(range(0, N_MAX + 1, 2))))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax.yaxis.set_major_locator(FixedLocator([0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.set_xlabel("Number of observed die outcomes", labelpad=6)
    ax.set_ylabel("Posterior probability of H1", labelpad=6)
    ax.set_axisbelow(True)
    ax.grid(color=GRID, linewidth=0.65)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color("#9AA5B1")
    ax.tick_params(length=3, pad=3)

    annotation7 = ax.annotate(
        r"$n=7$" + "\n" + '$128/137\\approx0.934$',
        xy=(7, ps[7]), xytext=(6.9, 0.63),
        ha="left", va="center", fontsize=9, color=NAVY,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": GRID},
        arrowprops={"arrowstyle": "-|>", "color": NAVY, "lw": 0.85,
                    "shrinkA": 4, "shrinkB": 5},
        zorder=6,
    )
    annotation10 = ax.annotate(
        'First ≥ 99.000%: n = 10\n' + '$1024/1033\\approx0.991$',
        xy=(10, ps[10]), xytext=(12.9, 0.63),
        ha="left", va="center", fontsize=9, color=INK,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": GRID},
        arrowprops={"arrowstyle": "-|>", "color": AMBER, "lw": 0.95,
                    "shrinkA": 4, "shrinkB": 5},
        zorder=6,
    )
    prior_note = ax.annotate(
        'n = 0: prior = 10.000%', xy=(0, ps[0]), xytext=(1.6, 0.075),
        ha="left", va="center", fontsize=9, color=GRAY,
        arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 0.8,
                    "shrinkA": 3, "shrinkB": 4},
        zorder=5,
    )
    legend = ax.legend(
        handles=[posterior_line, threshold_line], loc="lower right",
        fontsize=9, frameon=True, facecolor="white", edgecolor=GRID,
        framealpha=1, borderpad=0.5, handlelength=2.5,
    )
    fig.text(
        0.5, 0.163,
        '$p_n=\\frac{p_0\\,2^n}{1-p_0+p_0\\,2^n},\\qquad p_0=0.100$',
        ha="center", va="center", fontsize=11,
    )
    fig.text(
        0.5, 0.058, "Zero marks the prior, before any observed outcome.",
        ha="center", va="center", fontsize=9, color=GRAY,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = list(fig.texts) + list(ax.texts)
    texts += [ax.xaxis.label, ax.yaxis.label]
    texts += ax.get_xticklabels() + ax.get_yticklabels()
    texts += legend.get_texts()
    for t in texts:
        if not t.get_visible() or not t.get_text():
            continue
        if t.get_fontsize() < 9:
            raise ValueError("A label is below 9 pt")
        box = t.get_window_extent(renderer)
        if (box.x0 < 0 or box.y0 < 0 or
                box.x1 > fig.bbox.width or box.y1 > fig.bbox.height):
            raise ValueError(f'Clipped text: {t.get_text()}')
    # Annotation extents include arrows; compare their text boxes separately.
    boxes = [a.get_bbox_patch().get_window_extent(renderer)
             for a in (annotation7, annotation10)]
    if boxes[0].overlaps(boxes[1]):
        raise ValueError("Numeric callouts overlap")
    if any(b.overlaps(legend.get_window_extent(renderer)) for b in boxes):
        raise ValueError("A numeric callout overlaps the legend")
    if list(ax.get_xticks()) != list(range(0, 21, 2)):
        raise ValueError("Count ticks must be 0,2,...,20")
    if any(not t.get_text().isdigit() for t in ax.get_xticklabels()):
        raise ValueError("Count tick labels must be integers")
    if len(posterior_line.get_xdata()) != 21:
        raise ValueError("Every integer observation, including zero, needs a marker")
    if not all(math.isclose(a, float(b)) for a, b in zip(posterior_line.get_ydata(), exact)):
        raise ValueError("Plotted values differ from exact posteriors")
    return fig, first


def main():
    fig, first = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A04 - Posterior growth after consecutive High outcomes",
        "Subject": 'Pure single-die 456 hypothesis, prior 10.000%, posterior threshold 99.000%',
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "posterior_n7": "128/137", "posterior_n10": "1024/1033",
        "first_n_at_99_percent": first, "markers": 21,
        "exact_and_sequential_updates_agree": True, "integer_ticks_checked": True,
    }))


if __name__ == "__main__":
    main()

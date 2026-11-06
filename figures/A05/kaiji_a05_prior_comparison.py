#!/usr/bin/env python3
"""A05: posterior comparison for four priors under consecutive High.

Requirements: Python 3 and Matplotlib.
Running this file recreates the PNG and vector PDF beside the source.
Final size: 160 x 172 mm; 400-dpi PNG; ordinary labels at least 9 pt.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from pathlib import Path
from fractions import Fraction
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, StrMethodFormatter, FormatStrFormatter

WIDTH_MM, HEIGHT_MM, DPI = 160, 172, 400
BASENAME = "kaiji_a05_prior_comparison"
OUT = Path(__file__).resolve().parent
INK, GRAY, GRID = "#17212B", "#6B7280", "#E2E6EB"
PRIORS = (Fraction(1, 100), Fraction(1, 10), Fraction(1, 5), Fraction(1, 2))
COLORS = ("#2B5D7E", "#6F4A8E", "#268472", "#D98C3F")
STYLES = ("-", "--", ":", "-.")
MARKERS = ("o", "s", "^", "D")
N_MAX, THRESHOLD = 20, Fraction(99, 100)

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": GRAY, "ytick.color": GRAY,
    "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "dejavusans",
})


def exact_data():
    ns = list(range(N_MAX + 1))
    series, summary = [], []
    for prior in PRIORS:
        values = [prior * 2**n / (1 - prior + prior * 2**n) for n in ns]
        q = prior
        for n, expected in zip(ns, values):
            if n:
                q = q / (q + Fraction(1, 2) * (1 - q))
            if q != expected:
                raise ValueError("Sequential and closed-form updates disagree")
        first = next(n for n, p in zip(ns, values) if p >= THRESHOLD)
        if not values[first - 1] < THRESHOLD <= values[first]:
            raise ValueError("Threshold crossing is not minimal")
        series.append(values)
        summary.append([f'{_fmt_number(float(prior), percent=True)}', f'{_fmt_number(float(values[7]), percent=True)}', str(first)])
    expected = [
        ['1.000%', '56.388%', "14"],
        ['10.000%', '93.431%', "10"],
        ['20.000%', '96.970%', "9"],
        ['50.000%', '99.225%', "7"],
    ]
    if summary != expected:
        raise ValueError(f'Unexpected summary values: {summary}')
    if any(not all(series[i][n] < series[i + 1][n] for i in range(3)) for n in ns):
        raise ValueError("Posterior order must follow the order of the priors")
    return ns, series, summary


def create_figure():
    ns, exact, summary = exact_data()
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.967, "The effect of different priors",
             ha="center", va="center", fontsize=13.5, fontweight="bold")
    fig.text(0.5, 0.925, "Same observations; different prior odds",
             ha="center", va="center", fontsize=9.5, color=GRAY)
    fig.text(0.5, 0.885,
             r"All outcomes High   |   $H_1$: always 456   |   $H_0$: always fair",
             ha="center", va="center", fontsize=9, color=GRAY)

    ax = fig.add_axes([0.12, 0.485, 0.84, 0.35])
    curves = []
    for prior, values, color, style, marker in zip(PRIORS, exact, COLORS, STYLES, MARKERS):
        curve, = ax.plot(
            ns, [float(v) for v in values], color=color, linestyle=style,
            marker=marker, markersize=3.0, linewidth=1.6,
            label=f'Prior {_fmt_number(float(prior), percent=True)}', clip_on=False, zorder=3,
        )
        curves.append(curve)
    threshold = ax.axhline(
        float(THRESHOLD), color=GRAY, linewidth=0.9, linestyle=(0, (5, 4)),
        label='Posterior threshold 0.990', zorder=2,
    )
    ax.set_xlim(0, N_MAX)
    ax.set_ylim(-0.02, 1.035)
    ax.xaxis.set_major_locator(FixedLocator(list(range(0, N_MAX + 1, 2))))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax.yaxis.set_major_locator(FixedLocator([0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.set_xlabel("Number of consecutive High outcomes", labelpad=5)
    ax.set_ylabel("Posterior probability of H1", labelpad=6)
    ax.set_axisbelow(True)
    ax.grid(color=GRID, linewidth=0.65)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color("#9AA5B1")
    ax.tick_params(length=3, pad=3)
    legend = ax.legend(
        handles=curves + [threshold], loc="lower right", ncol=2, fontsize=9,
        frameon=True, facecolor="white", edgecolor=GRID, framealpha=1,
        handlelength=2.5, borderpad=0.5, columnspacing=1.0, handletextpad=0.6,
    )

    fig.text(0.52, 0.406, "Summary for consecutive High observations",
             ha="center", va="center", fontsize=9.5, fontweight="bold")
    tax = fig.add_axes([0.08, 0.145, 0.88, 0.245])
    tax.set_axis_off()
    table = tax.table(
        cellText=summary,
        colLabels=["Prior", "Posterior after\n7 High outcomes",
                   'First n with\nposterior ≥ 99.000%'],
        colWidths=[0.22, 0.43, 0.35],
        loc="center", cellLoc="center", colLoc="center", bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#D4DBE3")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor("#EEF2F6")
            cell.get_text().set_fontsize(9)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor("white" if row % 2 else "#F8FAFC")
            if col == 0:
                cell.get_text().set_color(COLORS[row - 1])
                cell.get_text().set_fontweight("bold")
            if col == 2:
                cell.get_text().set_fontweight("bold")

    fig.text(
        0.5, 0.089,
        r"$p_n=\frac{p_0\,2^n}{1-p_0+p_0\,2^n}$",
        ha="center", va="center", fontsize=11,
    )
    fig.text(
        0.5, 0.032, "n = 0 is the prior, before any observed outcome.",
        ha="center", va="center", fontsize=9, color=GRAY,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = list(fig.texts) + [ax.xaxis.label, ax.yaxis.label]
    texts += ax.get_xticklabels() + ax.get_yticklabels() + legend.get_texts()
    texts += [cell.get_text() for cell in table.get_celld().values()]
    for t in texts:
        if not t.get_visible() or not t.get_text():
            continue
        if t.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {t.get_text()}')
        extent = t.get_window_extent(renderer)
        if (extent.x0 < 0 or extent.y0 < 0 or
                extent.x1 > fig.bbox.width or extent.y1 > fig.bbox.height):
            raise ValueError(f'Clipped text: {t.get_text()}')
    for cell in table.get_celld().values():
        outer = cell.get_window_extent(renderer)
        inner = cell.get_text().get_window_extent(renderer)
        if (inner.x0 < outer.x0 or inner.x1 > outer.x1 or
                inner.y0 < outer.y0 or inner.y1 > outer.y1):
            raise ValueError("Table text overflows its cell")
    if list(ax.get_xticks()) != list(range(0, 21, 2)):
        raise ValueError("Count ticks must be integers 0,2,...,20")
    if any(not t.get_text().isdigit() for t in ax.get_xticklabels()):
        raise ValueError("Count labels must be integers")
    for curve, exact_values in zip(curves, exact):
        if len(curve.get_xdata()) != 21:
            raise ValueError("All integer observations need markers")
        if any(not math.isclose(a, float(b)) for a, b in zip(curve.get_ydata(), exact_values)):
            raise ValueError("Plotted posteriors do not match exact data")
    return fig, summary


def main():
    fig, summary = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A05 - The effect of different priors",
        "Subject": 'Pure single-die Bayesian inference; priors 1.000%, 10.000%, 20.000%, 50.000%',
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "summary": summary, "curves": 4, "points_per_curve": 21,
        "sequential_and_closed_form_agree": True, "integer_ticks_checked": True,
        "table_cell_bounds_checked": True,
    }))


if __name__ == "__main__":
    main()

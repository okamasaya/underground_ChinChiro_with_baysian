#!/usr/bin/env python3
"""A09: exact one-throw role counts, from ordered three-die outcomes.

Requirements: Python 3 and Matplotlib. Recreates PNG and vector PDF beside
this complete source; no notebook, random sample or external data needed.
Final size: 160 x 250 mm; PNG 400 dpi; ordinary labels at least 9 pt.

All three dice in a throw have the same fixed type: fair faces 1..6 or
idealized 456 faces 4..6. The panels are conditional on that fixed type,
not a mixed-strategy posterior. Counts use ordered outcomes, so all 216
or all 27 elementary outcomes within each sample space are equally likely.
The figure concerns one throw only. No payoffs or triple rankings are assumed.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from collections import Counter
from fractions import Fraction
from itertools import product
from math import comb, factorial, isclose
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FormatStrFormatter

WIDTH_MM, HEIGHT_MM, DPI = 160, 250, 400
BASENAME = "kaiji_a09_role_combinatorics"
OUT = Path(__file__).resolve().parent
INK, GRAY, GRID = "#17212B", "#6B7280", "#E2E6EB"
NAVY, AMBER = "#2B5D7E", "#D98C3F"
CATEGORIES = ["Pin triple", "Other triples", "456", "Points 4-6 combined",
              "Points 1-3 combined", "No role", "123"]
LABELS = ["Pin triple (1,1,1)", "Other triples", "456 role", "Points 4-6 combined",
          "Points 1-3 combined", "No role", "123 role"]
EXPECTED = {"fair": [1, 5, 6, 45, 45, 108, 6], "456": [0, 3, 6, 18, 0, 0, 0]}

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": GRAY, "ytick.color": INK,
    "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "dejavusans",
})


def classify(x):
    counts = Counter(x)
    if len(counts) == 1:
        return "Pin triple" if x[0] == 1 else "Other triples"
    if tuple(sorted(x)) == (4, 5, 6):
        return "456"
    if tuple(sorted(x)) == (1, 2, 3):
        return "123"
    if len(counts) == 2:
        k = next(face for face, count in counts.items() if count == 1)
        return "Points 4-6 combined" if k >= 4 else "Points 1-3 combined"
    return "No role"


def exact_data():
    results = {}
    for name, faces, denominator in (("fair", range(1, 7), 216), ("456", range(4, 7), 27)):
        triples = list(product(faces, repeat=3))
        if len(triples) != denominator or len(set(triples)) != denominator:
            raise ValueError("Sample space must consist of unique ordered triples")
        counts = Counter(classify(x) for x in triples)
        values = [counts[category] for category in CATEGORIES]
        if values != EXPECTED[name] or sum(values) != denominator:
            raise ValueError(f'Incorrect category totals for {name}: {values}')
        probabilities = [Fraction(n, denominator) for n in values]
        if sum(probabilities) != 1:
            raise ValueError("Probabilities must sum to one")
        for k in faces:
            # The singleton k is the point; the repeated face must differ from k.
            direct_count = sum(len(set(x)) == 2 and x.count(k) == 1 for x in triples)
            if direct_count != (len(faces) - 1) * 3:
                raise ValueError(f'Incorrect count for Point {k} with {name} dice')
        if counts["456"] != factorial(3):
            raise ValueError("The 456 role has six ordered permutations in both spaces")
        if name == "fair" and counts["No role"] != comb(6, 3) * factorial(3) - 2 * factorial(3):
            raise ValueError("Incorrect no-role combinatorial derivation")
        results[name] = {"counts": values, "total": denominator, "probabilities": probabilities}
    return results


def create_figure():
    data = exact_data()
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    texts, axes, rectangles, exact_labels = [], [], [], []

    def text(x, y, s, **kwargs):
        kwargs.setdefault("ha", "center")
        kwargs.setdefault("va", "center")
        kwargs.setdefault("fontsize", 9)
        item = fig.text(x, y, s, **kwargs)
        texts.append(item)
        return item

    text(0.5, 0.970, "One-throw role counts", fontsize=13.5, fontweight="bold")
    text(0.5, 0.944, "216 ordered outcomes versus 27", fontsize=10.5, color=GRAY)
    text(0.5, 0.921, "One throw; three dice of the same fixed type.", color=GRAY)

    for name, bottom, title_y, color, title in (
            ("fair", 0.630, 0.884, NAVY, r"A   Fair dice: $6^3=216$ equally likely outcomes"),
            ("456", 0.323, 0.577, AMBER, r"B   456 dice: $3^3=27$ equally likely outcomes")):
        info = data[name]
        height = 0.212
        text(0.06, title_y, title, ha="left", fontsize=10.5, fontweight="bold", color=color)
        text(0.887, bottom + height + 0.014, "Count / total", fontsize=9, fontweight="bold", color=GRAY)
        ax = fig.add_axes([0.36, bottom, 0.43, height])
        values = [float(p) for p in info["probabilities"]]
        bars = ax.barh(range(7), values, height=0.55, color=color, edgecolor="none", zorder=3)
        rectangles.append((bars, info["probabilities"]))
        # Explicit markers retain zero-probability categories in the second panel.
        for i, value in enumerate(values):
            if value == 0:
                ax.plot([0], [i], marker="o", markersize=3.8, markerfacecolor="white",
                        markeredgewidth=1, markeredgecolor=color, clip_on=False, zorder=4)
        ax.set_yticks(list(range(7)), LABELS)
        ax.set_ylim(6.6, -0.6)
        ax.set_xlim(0, 0.70)
        ax.xaxis.set_major_locator(FixedLocator([0, 0.2, 0.4, 0.6]))
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        ax.set_xlabel("Probability", labelpad=4)
        ax.tick_params(axis="y", length=0, pad=7)
        ax.tick_params(axis="x", length=3, pad=3)
        ax.set_axisbelow(True)
        ax.grid(axis="x", color=GRID, linewidth=0.65)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#9AA5B1")
        for i, count in enumerate(info["counts"]):
            y = bottom + height * (6.6 - i) / 7.2
            item = text(0.887, y, f"{count}/{info['total']}", fontsize=9.5, color=color)
            exact_labels.append((item, count, info["total"]))
        axes.append(ax)

    text(0.06, 0.257, "Counting the ordered outcomes", ha="left", fontsize=10.5, fontweight="bold")
    text(0.5, 0.229, r"Fair Point $k$: $(6-1)\times3=15$ each", fontsize=10)
    text(0.5, 0.201, r"456 Point $k$: $(3-1)\times3=6$ each ($k=4,5,6$)", fontsize=10)
    text(0.5, 0.173, r"456 role: $3!=6$ in either sample space", fontsize=10)
    text(0.5, 0.145, r"Fair no role: $\binom{6}{3}\,3!-2\times3!=108$", fontsize=10)
    text(0.5, 0.089, "456 role: one each of 4, 5, 6, in any order.", color=GRAY)
    text(0.5, 0.066, "456 dice: each die is uniform on the faces 4, 5, 6.", color=GRAY)
    text(0.5, 0.030, "All bars use the same probability scale; fractions give exact probabilities.", color=GRAY)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax in axes:
        texts += ax.get_xticklabels() + ax.get_yticklabels() + [ax.xaxis.label]
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
    for bars, probs in rectangles:
        if any(not isclose(bar.get_width(), float(p)) for bar, p in zip(bars, probs)):
            raise ValueError("Bars must represent normalized probabilities, not raw counts")
    if axes[0].get_xlim() != axes[1].get_xlim() or axes[0].get_ylim() != axes[1].get_ylim():
        raise ValueError("Both panels must use the same probability scale and row order")
    for item, count, total in exact_labels:
        if item.get_text() != f'{count}/{total}':
            raise ValueError("Incorrect exact probability label")
    return fig, data, len(texts)


def main():
    fig, data, text_count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A09 - Exact one-throw role counts: 216 versus 27 outcomes",
        "Subject": "Ordered dice outcomes; exact category counts and normalized probabilities",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "categories": CATEGORIES,
        "fair_counts": data["fair"]["counts"], "fair_total": data["fair"]["total"],
        "456_counts": data["456"]["counts"], "456_total": data["456"]["total"],
        "exact_normalization_and_counting_derivations_checked": True,
        "common_probability_scale_checked": True,
        "text_elements_checked": text_count, "text_bounds_and_collisions_checked": True,
    }))


if __name__ == "__main__":
    main()

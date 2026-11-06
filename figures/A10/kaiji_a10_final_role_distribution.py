#!/usr/bin/env python3
"""A10: one-throw probabilities and final-turn probabilities, eleven roles.

Requirements: Python 3 and Matplotlib. Recreates PNG and vector PDF beside
this complete source; no notebook, random sample or external data needed.
Final size: 160 x 264 mm; PNG 400 dpi; ordinary labels at least 9 pt.

A turn uses a fixed dice-set type, rerolls only after no role and ends by
throw three. The figure compares distributions conditional on fair or 456
dice, not a mixed-strategy posterior. All triples are ordered outcomes.
Different non-111 triples are grouped for probability accounting only;
their payout ranking is not specified here. There are no payoff assumptions.
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
from math import isclose
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedLocator, FormatStrFormatter

WIDTH_MM, HEIGHT_MM, DPI = 160, 264, 400
BASENAME = "kaiji_a10_final_role_distribution"
OUT = Path(__file__).resolve().parent
INK, GRAY, GRID = "#17212B", "#6B7280", "#E2E6EB"
NAVY, LIGHT_NAVY, AMBER = "#2B5D7E", "#B6C9D8", "#D98C3F"
CATEGORIES = ["Pin triple", "Other triples", "456", "Point 6", "Point 5", "Point 4",
              "Point 3", "Point 2", "Point 1", "No role", "123"]
LABELS = ["Pin triple (111)", "Other triples", "456 role", "Point 6", "Point 5", "Point 4",
          "Point 3", "Point 2", "Point 1", "No role", "123 role"]
EXPECTED_COUNTS = {"fair": [1, 5, 6, 15, 15, 15, 15, 15, 15, 108, 6],
                   "456": [0, 3, 6, 6, 6, 6, 0, 0, 0, 0, 0]}
EXPECTED_FINAL = {"fair": [7, 35, 42, 105, 105, 105, 105, 105, 105, 108, 42],
                  "456": [0, 3, 6, 6, 6, 6, 0, 0, 0, 0, 0]}

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": GRAY, "ytick.color": INK,
    "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "dejavusans",
    "hatch.linewidth": 0.5,
})


def classify(x):
    counts = Counter(x)
    if len(counts) == 1:
        return "Pin triple" if x[0] == 1 else "Other triples"
    ordered = tuple(sorted(x))
    if ordered == (4, 5, 6):
        return "456"
    if ordered == (1, 2, 3):
        return "123"
    if len(counts) == 2:
        k = next(face for face, count in counts.items() if count == 1)
        return f'Point {k}'
    return "No role"


def enumerate_final(one):
    """Enumerate all 11^3 role sequences, marginalizing unused future draws."""
    result = {r: Fraction(0) for r in CATEGORIES}
    for roles in product(CATEGORIES, repeat=3):
        prob = Fraction(1)
        for r in roles:
            prob *= one[r]
        end = next((r for r in roles if r != "No role"), "No role")
        result[end] += prob
    return result


def exact_data():
    data = {}
    for name, faces, total, turn_denom in (
            ("fair", range(1, 7), 216, 864), ("456", range(4, 7), 27, 27)):
        triples = list(product(faces, repeat=3))
        counts = Counter(classify(x) for x in triples)
        actual_counts = [counts[r] for r in CATEGORIES]
        if len(triples) != total or actual_counts != EXPECTED_COUNTS[name]:
            raise ValueError(f'Incorrect one-throw counts for {name}')
        one = {r: Fraction(counts[r], total) for r in CATEGORIES}
        q = one["No role"]
        factor = 1 + q + q**2
        final = {r: (q**3 if r == "No role" else one[r] * factor) for r in CATEGORIES}
        if sum(one.values()) != 1 or sum(final.values()) != 1:
            raise ValueError("Every full distribution must sum to one")
        if final != enumerate_final(one):
            raise ValueError("Stopping formula disagrees with role-sequence enumeration")
        final_nums = [final[r] * turn_denom for r in CATEGORIES]
        if final_nums != EXPECTED_FINAL[name]:
            raise ValueError(f'Incorrect final-turn probabilities for {name}')
        if name == "fair" and (q, factor, final["No role"]) != (
                Fraction(1, 2), Fraction(7, 4), Fraction(1, 8)):
            raise ValueError("Incorrect fair-dice transformation")
        if name == "456" and (q != 0 or one != final):
            raise ValueError("456 dice must end with a completed role on throw one")
        data[name] = {
            "one": [one[r] for r in CATEGORIES], "final": [final[r] for r in CATEGORIES],
            "one_labels": [f'{counts[r]}/{total}' for r in CATEGORIES],
            "final_labels": [f'{int(n)}/{turn_denom}' for n in final_nums],
        }
    return data


def create_figure():
    data = exact_data()
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    texts, axes, bar_data, fraction_data = [], [], [], []

    def text(x, y, s, **kwargs):
        kwargs.setdefault("ha", "center")
        kwargs.setdefault("va", "center")
        kwargs.setdefault("fontsize", 9)
        item = fig.text(x, y, s, **kwargs)
        texts.append(item)
        return item

    def key(x, y, label, fill, edge, hatch=None):
        fig.add_artist(Rectangle((x, y - 0.0045), 0.028, 0.009,
                                 transform=fig.transFigure, facecolor=fill,
                                 edgecolor=edge, hatch=hatch, linewidth=0.6))
        text(x + 0.038, y, label, ha="left")

    text(0.5, 0.972, "From one throw to the final role", fontsize=13.5, fontweight="bold")
    text(0.5, 0.946, "At most three throws; reroll only after no role.", fontsize=9.5, color=GRAY)
    text(0.5, 0.923, "Keep the same selected dice type throughout a turn.", color=GRAY)

    configs = [
        {"bottom": 0.575, "title_y": 0.892, "key_y": 0.858,
         "title": "A   Fair dice: one throw versus final turn",
         "first": data["fair"]["one"], "second": data["fair"]["final"],
         "labels_first": data["fair"]["one_labels"], "labels_second": data["fair"]["final_labels"],
         "colors": (LIGHT_NAVY, NAVY), "edges": (NAVY, NAVY),
         "hatch": "////", "keys": ("One throw", "Final turn"), "heads": ("1 throw", "Final")},
        {"bottom": 0.147, "title_y": 0.454, "key_y": 0.426,
         "title": "B   Final-turn roles: fair versus 456 dice",
         "first": data["fair"]["final"], "second": data["456"]["final"],
         "labels_first": data["fair"]["final_labels"], "labels_second": data["456"]["final_labels"],
         "colors": (NAVY, AMBER), "edges": (NAVY, AMBER),
         "hatch": None, "keys": ("Fair dice", "456 dice"), "heads": ("Fair", "456")},
    ]
    for cfg in configs:
        bottom, height = cfg["bottom"], 0.252
        text(0.06, cfg["title_y"], cfg["title"], ha="left", fontsize=10.5, fontweight="bold")
        key(0.06, cfg["key_y"], cfg["keys"][0], cfg["colors"][0], cfg["edges"][0], cfg["hatch"])
        key(0.34, cfg["key_y"], cfg["keys"][1], cfg["colors"][1], cfg["edges"][1])
        for x, label, color in zip((0.78, 0.92), cfg["heads"], cfg["edges"]):
            text(x, cfg["key_y"], label, fontweight="bold", color=color)
        ax = fig.add_axes([0.28, bottom, 0.39, height])
        for series, offset, fill, edge, hatch, labels, col in (
                (cfg["first"], -0.18, cfg["colors"][0], cfg["edges"][0], cfg["hatch"], cfg["labels_first"], 0.78),
                (cfg["second"], 0.18, cfg["colors"][1], cfg["edges"][1], None, cfg["labels_second"], 0.92)):
            bars = ax.barh([i + offset for i in range(11)], [float(p) for p in series],
                           height=0.30, color=fill, edgecolor=edge,
                           hatch=hatch, linewidth=0.45 if hatch else 0, zorder=3)
            bar_data.append((bars, series))
            for i, p in enumerate(series):
                if p == 0:
                    ax.plot([0], [i + offset], marker="o", markersize=3.6,
                            markerfacecolor="white", markeredgecolor=edge,
                            markeredgewidth=1, clip_on=False, zorder=4)
                y = bottom + height * (10.65 - i) / 11.3
                item = text(col, y, labels[i], color=edge, fontsize=9)
                fraction_data.append((item, p))
        ax.set_yticks(range(11), LABELS)
        ax.set_ylim(10.65, -0.65)
        ax.set_xlim(0, 0.54)
        ax.xaxis.set_major_locator(FixedLocator([0, 0.1, 0.2, 0.3, 0.4, 0.5]))
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        ax.set_xlabel("Probability", labelpad=4)
        ax.tick_params(axis="y", length=0, pad=6)
        ax.tick_params(axis="x", length=3, pad=3)
        ax.set_axisbelow(True)
        ax.grid(axis="x", color=GRID, linewidth=0.65)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#9AA5B1")
        axes.append(ax)

    text(0.5, 0.513,
         r"Fair: $q_F=1/2$; completed roles multiply by $1+q_F+q_F^2=7/4$.", fontsize=9.5)
    text(0.5, 0.490, r"Final no role: $q_F^3=1/8$ instead of $q_F=1/2$.", fontsize=9.5)
    text(0.5, 0.074, r"456 dice: $q=0$; one-throw and final-turn distributions coincide.", fontsize=9.5, color=AMBER)
    text(0.5, 0.049, "Each distribution sums to 1; right-hand columns give exact probabilities.", color=GRAY)
    text(0.5, 0.024, "Other triples combine 222 through 666; category order is for listing.", color=GRAY)

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
    for bars, probs in bar_data:
        if len(bars) != 11 or any(not isclose(bar.get_width(), float(p)) for bar, p in zip(bars, probs)):
            raise ValueError("Bars disagree with exact probabilities")
    for item, p in fraction_data:
        if Fraction(item.get_text()) != p:
            raise ValueError("Exact fraction label disagrees with data")
    if axes[0].get_xlim() != axes[1].get_xlim() or axes[0].get_ylim() != axes[1].get_ylim():
        raise ValueError("Both panels must share the probability scale and category order")
    return fig, data, len(texts)


def main():
    fig, data, text_count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A10 - One-throw and final-turn role distributions",
        "Subject": "Exact role distributions; fixed dice type; at most three throws",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "categories": CATEGORIES,
        "fair_one_throw": data["fair"]["one_labels"], "fair_final_turn": data["fair"]["final_labels"],
        "456_final_turn": data["456"]["final_labels"],
        "role_sequences_checked": 2 * 11**3, "one_throw_outcomes_checked": 216 + 27,
        "all_four_distributions_normalized": True,
        "exact_transformation_and_sequence_enumeration_agree": True,
        "bars_and_fraction_labels_checked": 44, "common_probability_scale_checked": True,
        "text_elements_checked": text_count, "text_bounds_and_collisions_checked": True,
    }))


if __name__ == "__main__":
    main()

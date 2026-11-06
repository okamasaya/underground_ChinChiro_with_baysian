#!/usr/bin/env python3
"""Render A01: four observation units for the idealized Chinchiro model.

Requirements: Python 3 and Matplotlib.
Run this file to recreate the PNG and the vector PDF beside this source.
Final physical figure size: 160 x 192 mm. All text is at least 9 pt.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from pathlib import Path
from itertools import combinations
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

WIDTH_MM, HEIGHT_MM = 160.0, 192.0
DPI = 400
BASENAME = "kaiji_a01_observation_units"
OUTPUT_DIR = Path(__file__).resolve().parent

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
    "svg.fonttype": "none",
    "mathtext.fontset": "dejavusans",
})


def create_figure():
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH_MM)
    ax.set_ylim(HEIGHT_MM, 0)
    ax.set_axis_off()
    texts = []

    def text(x, y, value, size=9, color=INK, weight="normal",
             ha="left", va="center", zorder=4):
        artist = ax.text(x, y, value, fontsize=size, color=color,
                         fontweight=weight, ha=ha, va=va,
                         linespacing=1.15, zorder=zorder)
        texts.append(artist)
        return artist

    def box(x, y, width, height, face="white", edge=LINE, radius=1.2,
            linewidth=0.8, zorder=1):
        patch = FancyBboxPatch(
            (x, y), width, height,
            boxstyle=f'round,pad=0,rounding_size={radius}',
            facecolor=face, edgecolor=edge, linewidth=linewidth,
            mutation_aspect=1, zorder=zorder,
        )
        ax.add_patch(patch)
        return patch

    def line(x1, y1, x2, y2, color=GRAY, width=0.8):
        ax.add_line(Line2D([x1, x2], [y1, y2], color=color,
                          linewidth=width, zorder=2))

    def arrow(x1, y1, x2, y2, color=GRAY):
        patch = FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=7,
            linewidth=0.85, color=color, shrinkA=0, shrinkB=0, zorder=2,
        )
        ax.add_patch(patch)

    def card(x, y, width, height, number, title, subtitle):
        box(x, y, width, height, edge=LINE, radius=1.6)
        box(x + 4, y + 4, 7, 7, face=NAVY, edge=NAVY, radius=1)
        text(x + 7.5, y + 7.5, number, size=9, color="white",
             weight="bold", ha="center")
        text(x + 14, y + 7.5, title, size=11, weight="bold")
        text(x + 4, y + 16, subtitle, color=GRAY)

    # Figure heading. The figure number can be set independently in the article.
    text(80, 7, "Observation units", size=13.5, weight="bold", ha="center")
    text(80, 14.5, "Four distinct units for dice, inference, and payoff",
         size=9, color=GRAY, ha="center")

    # 01: one die outcome.
    card(1.5, 22, 76, 64, "01", "One die outcome",
         "Introductory observation unit")
    box(13, 44, 15, 15, face=PALE_GRAY, edge=GRAY, radius=2)
    text(20.5, 51.5, r"$k$", size=19, ha="center")
    text(49, 51.5, "One observed\nface value", ha="center")

    box(6.5, 65.5, 30, 12, face=PALE_GRAY, edge=LINE, radius=1)
    text(21.5, 68.9, "Low", weight="bold", ha="center")
    text(21.5, 74, "{1, 2, 3}", ha="center")
    box(41.5, 65.5, 30, 12, face=PALE_AMBER, edge=AMBER, radius=1)
    text(56.5, 68.9, "High", weight="bold", ha="center")
    text(56.5, 74, "{4, 5, 6}", ha="center")
    text(39.5, 82, "Single-die classification", color=GRAY, ha="center")

    # 02: one throw. A common Z is the only dice-type selector.
    card(82.5, 22, 76, 64, "02", "One throw",
         "Three dice; one selected type")
    box(87.5, 44.5, 66, 29.5, face=PALE_BLUE, edge=NAVY, radius=1.3)
    box(109, 47, 23, 6.2, face=NAVY, edge=NAVY, radius=0.8)
    text(120.5, 50.1, "Shared Z", color="white", ha="center")
    line(120.5, 53.2, 120.5, 56.5, color=NAVY)
    line(99.5, 56.5, 141.5, 56.5, color=NAVY)
    for i, center in enumerate((99.5, 120.5, 141.5), 1):
        line(center, 56.5, center, 59, color=NAVY)
        box(center - 6, 59, 12, 11, edge=NAVY, radius=1.4)
        text(center, 64.5, f'$X_{i}$', size=13, ha="center")
    text(120.5, 78.8, "One common type", color=GRAY, ha="center")
    text(107.5, 83.4, "Fair", color=NAVY, weight="bold", ha="center")
    text(120.5, 83.4, "or", color=GRAY, ha="center")
    text(133.5, 83.4, "456", color=AMBER, weight="bold", ha="center")

    # 03: one turn. Role results terminate; only "no role" continues.
    card(1.5, 92, 76, 96, "03", "One turn",
         "Keep the same set during rerolls")
    for i, y in enumerate((115, 132.5, 150), 1):
        box(7.5, y, 31, 9, face=PALE_BLUE, edge=NAVY, radius=1)
        text(23, y + 4.5, f'Throw {i}', weight="bold", ha="center")
        arrow(38.5, y + 4.5, 58, y + 4.5)
        box(59, y + 0.5, 14, 8, face=PALE_GRAY, edge=GRAY, radius=1)
        text(66, y + 4.5, "Stop", ha="center")
        if i < 3:
            text(48.2, y + 0.2, "Role", color=GRAY, ha="center")
            arrow(23, y + 9, 23, y + 17.5)
            text(27, y + 13.25, "No role", color=GRAY)
        else:
            text(48.2, y - 0.7, "Any result", color=GRAY, ha="center")
    text(39.5, 164.2, "Stop no later than throw 3.", ha="center")
    text(7.5, 171.5, "Valid example (fair set)", weight="bold")
    text(7.5, 178, "1: (1, 4, 6) → no role")
    text(7.5, 184, "2: (5, 5, 6) → Point 6; stop")

    # 04: a match compares completed turns, not individual throws.
    card(82.5, 92, 76, 96, "04", "One match",
         "Parent vs one child")
    box(87.5, 115, 30, 16, face=PALE_BLUE, edge=NAVY, radius=1)
    box(123.5, 115, 30, 16, face=PALE_BLUE, edge=NAVY, radius=1)
    text(102.5, 120, "Parent turn", weight="bold", ha="center")
    text(102.5, 126, r"Final role $r$", ha="center")
    text(138.5, 120, "Child turn", weight="bold", ha="center")
    text(138.5, 126, r"Final role $s$", ha="center")
    line(102.5, 131, 102.5, 137.5)
    line(138.5, 131, 138.5, 137.5)
    line(102.5, 137.5, 138.5, 137.5)
    arrow(120.5, 137.5, 120.5, 142.5)
    box(87.5, 143.5, 66, 15, face=PALE_GRAY, edge=GRAY, radius=1)
    text(120.5, 151, "Compare final roles\n+ apply payoff table", ha="center")
    arrow(120.5, 158.5, 120.5, 164)
    box(87.5, 165, 66, 14, face=PALE_AMBER, edge=AMBER, radius=1)
    text(120.5, 169.5, "Net gain per unit stake", ha="center")
    text(120.5, 175, r"$G=g(r,s)$", size=10, ha="center")
    text(120.5, 184, "Payoff values: to be defined.", color=GRAY, ha="center")

    # Validate text geometry at the actual figure size before saving.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [artist.get_window_extent(renderer) for artist in texts]
    for artist, extent in zip(texts, boxes):
        if artist.get_fontsize() < 9:
            raise ValueError("Text is smaller than 9 pt")
        if (extent.x0 < 0 or extent.y0 < 0 or
                extent.x1 > fig.bbox.width or extent.y1 > fig.bbox.height):
            raise ValueError(f'Clipped text: {artist.get_text()!r}')
    collisions = []
    for (i, left), (j, right) in combinations(enumerate(boxes), 2):
        if left.overlaps(right):
            collisions.append((texts[i].get_text(), texts[j].get_text()))
    if collisions:
        raise ValueError(f'Overlapping labels: {collisions}')
    return fig, len(texts)


def check_example():
    """Check the example against the stipulated role classifier."""
    def classify(values):
        a, b, c = sorted(values)
        if a == c:
            return "triple"
        if (a, b, c) in ((1, 2, 3), (4, 5, 6)):
            return "special"
        if a == b:
            return f'Point {c}'
        if b == c:
            return f'Point {a}'
        return "no role"
    if classify((1, 4, 6)) != "no role":
        raise ValueError("Invalid first throw in example")
    if classify((5, 5, 6)) != "Point 6":
        raise ValueError("Invalid second throw in example")


def main():
    check_example()
    fig, text_count = create_figure()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUTPUT_DIR / f'{BASENAME}.png'
    pdf = OUTPUT_DIR / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A01 - Observation units and model boundaries",
        "Subject": "Four distinct units: die outcome, throw, turn, match",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)],
        "physical_size_mm": [WIDTH_MM, HEIGHT_MM],
        "minimum_text_pt": 9,
        "text_labels_checked": text_count,
        "label_overlaps": 0,
        "example_checked": True,
    }))


if __name__ == "__main__":
    main()

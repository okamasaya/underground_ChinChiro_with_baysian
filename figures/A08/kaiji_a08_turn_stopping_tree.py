#!/usr/bin/env python3
"""A08: a fixed-type turn ends by throw three; reroll only after no role.

Requirements: Python 3 and Matplotlib. Recreates PNG and vector PDF beside
this source; no notebook, random sample or external data required.
Final size: 160 x 250 mm; PNG 400 dpi; ordinary labels at least 9 pt.

The selected dice-set type Z is fixed throughout a turn. q and a_r are
conditional on that type. For a mixed strategy, compute each type's turn
distribution first, then mix; do not average q before using powers of q.
Dice leaving the bowl and payoff rules are outside this stopping model.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from fractions import Fraction
from itertools import product
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

WIDTH_MM, HEIGHT_MM, DPI = 160, 250, 400
BASENAME = "kaiji_a08_turn_stopping_tree"
OUT = Path(__file__).resolve().parent
INK, GRAY, LINE = "#17212B", "#6B7280", "#D4DBE3"
NAVY, AMBER = "#2B5D7E", "#D98C3F"

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "text.color": INK, "pdf.fonttype": 42, "ps.fonttype": 42,
    "mathtext.fontset": "dejavusans",
})


def role(x):
    """Classify only what this figure needs; no rankings or payoff assumptions."""
    if len(set(x)) == 1:
        return "triple"
    if len(set(x)) == 2:
        return "point6" if x.count(6) == 1 else "other_point"
    if tuple(sorted(x)) in ((1, 2, 3), (4, 5, 6)):
        return "123_or_456"
    return "none"


def stopping_probabilities(q):
    completed = [(1 - q) * q**j for j in range(3)]
    no_role = q**3
    p_m = {1: 1 - q, 2: q * (1 - q), 3: q**2}
    mean = sum(m * p for m, p in p_m.items())
    if sum(completed) + no_role != 1 or sum(p_m.values()) != 1:
        raise ValueError("Terminal probabilities do not sum to one")
    if p_m[3] != completed[2] + no_role or mean != 1 + q + q**2:
        raise ValueError("Incorrect third-throw probability or mean")
    # Independently enumerate pre-generated binary role/no-role sequences.
    # Outcomes after a stopping event are unobserved and summed out.
    counts = {1: Fraction(0), 2: Fraction(0), 3: Fraction(0)}
    endings = [Fraction(0)] * 4
    for outcomes in product((True, False), repeat=3):
        prob = Fraction(1)
        for success in outcomes:
            prob *= (1 - q) if success else q
        first = next((i for i, success in enumerate(outcomes, 1) if success), None)
        counts[first if first else 3] += prob
        endings[first - 1 if first else 3] += prob
    if counts != p_m or endings != completed + [no_role]:
        raise ValueError("Enumeration disagrees with the stopping tree")
    return completed, no_role, p_m, mean


def exact_data():
    q_values = {}
    for label, faces, expected_q in (
            ("fair", range(1, 7), Fraction(1, 2)),
            ("456", range(4, 7), Fraction(0))):
        triples = list(product(faces, repeat=3))
        labels = [role(x) for x in triples]
        q = Fraction(labels.count("none"), len(triples))
        if q != expected_q:
            raise ValueError(f'Incorrect no-role probability for {label} dice')
        q_values[label] = q
        # Check one particular completed role using its enumerated one-throw count.
        ar = Fraction(labels.count("point6"), len(triples))
        predicted = ar * (1 + q + q**2)
        total_r = Fraction(0)
        probs = {"r": ar, "other": 1 - q - ar, "none": q}
        for outcomes in product(probs, repeat=3):
            prob = Fraction(1)
            for outcome in outcomes:
                prob *= probs[outcome]
            first = next((outcome for outcome in outcomes if outcome != "none"), "none")
            if first == "r":
                total_r += prob
        if predicted != total_r:
            raise ValueError("Particular-role path sum disagrees with enumeration")
    for q in (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1)):
        stopping_probabilities(q)
    completed, no_role, p_m, mean = stopping_probabilities(q_values["fair"])
    if completed != [Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)]:
        raise ValueError("Unexpected fair-dice completion probabilities")
    if no_role != Fraction(1, 8) or p_m != {1: Fraction(1, 2), 2: Fraction(1, 4), 3: Fraction(1, 4)}:
        raise ValueError("Unexpected fair-dice terminal probabilities")
    if mean != Fraction(7, 4) or stopping_probabilities(q_values["456"])[3] != 1:
        raise ValueError("Incorrect mean number of throws")
    return completed, no_role, p_m, mean


def create_figure():
    completed, no_role, p_m, mean = exact_data()
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    texts, boxes = [], []

    def text(x, y, s, **kwargs):
        kwargs.setdefault("ha", "center")
        kwargs.setdefault("va", "center")
        kwargs.setdefault("fontsize", 9)
        item = fig.text(x, y, s, **kwargs)
        texts.append(item)
        return item

    def box(left, bottom, width, height, fill="white", edge=LINE, pad=0.004):
        patch = FancyBboxPatch((left, bottom), width, height,
                               transform=fig.transFigure,
                               boxstyle=f'round,pad={pad},rounding_size=0.006',
                               facecolor=fill, edgecolor=edge, linewidth=0.8, zorder=0)
        fig.add_artist(patch)
        return patch

    def arrow(x1, y1, x2, y2):
        fig.add_artist(FancyArrowPatch((x1, y1), (x2, y2), transform=fig.transFigure,
                                      arrowstyle="-|>", mutation_scale=10,
                                      color=GRAY, linewidth=0.9, shrinkA=0, shrinkB=0, zorder=1))

    text(0.5, 0.969, "A turn stops by the third throw", fontsize=13.5, fontweight="bold")
    text(0.5, 0.942, "Fixed dice type; reroll only after no role.", fontsize=9.5, color=GRAY)
    text(0.5, 0.918, r"$q=P(\mathrm{no\ role})$;   $a_r=P(\mathrm{particular\ completed\ role}\ r)$", fontsize=9.5)
    text(0.5, 0.895, r"Both are per-throw probabilities for the fixed type $Z$.", color=GRAY)
    text(0.08, 0.871, "A   General stopping tree", ha="left", fontsize=10.5, fontweight="bold")

    stage_ys = [0.807, 0.696, 0.585]
    any_paths = [r"1-q", r"q(1-q)", r"q^2(1-q)"]
    role_paths = [r"a_r", r"q\,a_r", r"q^2a_r"]
    for i, (y, any_path, role_path) in enumerate(zip(stage_ys, any_paths, role_paths), 1):
        stage = box(0.10, y - 0.037, 0.27, 0.074, fill="#F8FAFC", edge=GRAY)
        label = text(0.235, y + 0.016, f'Throw {i}', fontsize=10.5, fontweight="bold")
        boxes.append((label, stage))
        badge = box(0.16, y - 0.029, 0.15, 0.023, fill="#EEF2F6", edge=GRAY, pad=0.001)
        badge_text = text(0.235, y - 0.0175, r"SET $Z$", color=GRAY)
        boxes.append((badge_text, badge))
        arrow(0.374, y, 0.606, y)
        text(0.49, y + 0.017, r"$1-q$", color=GRAY)
        terminal = box(0.61, y - 0.044, 0.33, 0.088, fill="#F8FAFC")
        terminal_texts = [
            text(0.775, y + 0.027, "STOP: completed role", fontweight="bold"),
            text(0.775, y + 0.001, f'Total path: ${any_path}$', fontsize=10),
            text(0.775, y - 0.026, f'Role $r$ path: ${role_path}$', fontsize=10),
        ]
        boxes.extend((item, terminal) for item in terminal_texts)
        if i < 3:
            next_y = stage_ys[i]
            arrow(0.235, y - 0.041, 0.235, next_y + 0.041)
            text(0.28, (y + next_y) / 2, r"No role: $q$", ha="left", color=GRAY)
    # The third no-role branch terminates; it never leads to a fourth throw.
    arrow(0.235, stage_ys[-1] - 0.041, 0.235, 0.526)
    text(0.28, 0.535, r"No role: $q$", ha="left", color=GRAY)
    terminal_none = box(0.10, 0.456, 0.27, 0.066, fill="#EEF2F6", edge=GRAY)
    boxes.append((text(0.235, 0.502, "STOP: no role", fontweight="bold"), terminal_none))
    boxes.append((text(0.235, 0.475, r"Total path: $q^3$", fontsize=10), terminal_none))
    text(0.665, 0.516, "One particular completed role:", fontweight="bold")
    text(0.665, 0.485,
         r"$P_{\mathrm{turn}}(r)=a_r(1+q+q^2)$", fontsize=10.5)

    text(0.08, 0.425, r"B   Fair-dice check: $q=1/2$", ha="left", fontsize=10.5,
         fontweight="bold", color=NAVY)
    tax = fig.add_axes([0.08, 0.274, 0.84, 0.132])
    tax.set_axis_off()
    rows = [[f'Role at throw {i}', str(p), str(i)] for i, p in enumerate(completed, 1)]
    rows.append(["No role after throw 3", str(no_role), "3"])
    table = tax.table(cellText=rows, colLabels=["How the turn ends", "Probability", "Throws M"],
                      colWidths=[0.53, 0.24, 0.23], bbox=[0, 0, 1, 1],
                      cellLoc="center", colLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(LINE)
        cell.set_linewidth(0.6)
        cell.set_facecolor("#EAF0F5" if row == 0 else ("white" if row % 2 else "#F8FAFC"))
        if row == 0:
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_color(NAVY)
        texts.append(cell.get_text())
        boxes.append((cell.get_text(), cell))
    for x, m in zip((0.22, 0.5, 0.78), (1, 2, 3)):
        frac = p_m[m]
        text(x, 0.250, f'$P(M={m})={frac.numerator}/{frac.denominator}$', fontsize=10, color=NAVY)
    text(0.5, 0.224, "M = 3 includes both completed role and no role at throw 3.", color=GRAY)
    text(0.5, 0.189,
         f'$E[M]=1+q+q^2={mean.numerator}/{mean.denominator}={_fmt_number(float(mean))}$',
         fontsize=11, color=NAVY)

    box(0.08, 0.093, 0.84, 0.065, fill="#FFFAF2", edge=AMBER)
    text(0.5, 0.144, r"456 dice: $q=0$;   $P(M=1)=1$;   $E[M]=1$",
         fontsize=10, color=AMBER, fontweight="bold")
    text(0.5, 0.114, "The first throw always completes a role.", color=GRAY)
    text(0.5, 0.055, "For a mixture: apply the tree to each fixed type, then average.", color=GRAY)
    text(0.5, 0.031, "Keep the same selected set Z throughout the turn.", color=GRAY)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for item in texts:
        b = item.get_window_extent(renderer)
        if item.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {item.get_text()}')
        if b.x0 < 0 or b.y0 < 0 or b.x1 > fig.bbox.width or b.y1 > fig.bbox.height:
            raise ValueError(f'Clipped text: {item.get_text()}')
    for item, patch in boxes:
        b, outer = item.get_window_extent(renderer), patch.get_window_extent(renderer)
        if b.x0 < outer.x0 or b.x1 > outer.x1 or b.y0 < outer.y0 or b.y1 > outer.y1:
            raise ValueError(f'Text overflows its container: {item.get_text()}')
    for i, a in enumerate(texts):
        ba = a.get_window_extent(renderer)
        for b in texts[i+1:]:
            bb = b.get_window_extent(renderer)
            if (min(ba.x1, bb.x1) - max(ba.x0, bb.x0) > 0.5
                    and min(ba.y1, bb.y1) - max(ba.y0, bb.y0) > 0.5):
                raise ValueError(f'Text collision: {a.get_text()} / {b.get_text()}')
    return fig, p_m, mean, len(texts)


def main():
    fig, p_m, mean, text_count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A08 - The stopping tree for a turn with at most three throws",
        "Subject": "Fixed dice type; no-role rerolls; exact terminal and throw-count probabilities",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "fair_throw_count_distribution": {str(m): str(p) for m, p in p_m.items()},
        "fair_mean_throws": str(mean), "456_mean_throws": "1",
        "no_role_counts_checked": {"fair": "108/216", "456": "0/27"},
        "binary_sequence_enumerations_checked": 5 * 8,
        "particular_role_sequence_enumerations_checked": 2 * 27,
        "terminal_normalization_and_mean_checked": True,
        "text_elements_checked": text_count, "text_bounds_and_collisions_checked": True,
        "container_bounds_checked": True,
    }))


if __name__ == "__main__":
    main()

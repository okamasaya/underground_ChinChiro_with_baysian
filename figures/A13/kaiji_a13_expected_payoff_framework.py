#!/usr/bin/env python3
"""A13: symbolic framework from final-role probabilities to expected net gain.

Requirements: Python 3 and Matplotlib. Recreates PNG and vector PDF beside
this complete source; no notebook or external data needed.
Final size: 160 x 270 mm; PNG 400 dpi; ordinary labels at least 9 pt.

Payoffs remain symbolic. No Chinchiro payout multipliers or numeric profits
are invented. Parent and child independently complete their turns; G is
the parent's net gain at unit stake against one child in one match.
The conditional checks require their stated distribution/payoff assumptions.
The 3x3 matrix windows are schematics, extended over all required role pairs.
Group roles only if their payoff behavior is the same; otherwise split them.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

WIDTH_MM, HEIGHT_MM, DPI = 160, 270, 400
BASENAME = "kaiji_a13_expected_payoff_framework"
OUT = Path(__file__).resolve().parent
INK, GRAY, LINE = "#17212B", "#6B7280", "#D0D8E0"
NAVY, AMBER, PURPLE = "#2B5D7E", "#D98C3F", "#6F4A8E"

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "text.color": INK, "pdf.fonttype": 42, "ps.fonttype": 42,
    "mathtext.fontset": "dejavusans",
})


def check_symbolic_coefficients():
    """Check coefficients of symbolic g_ij without assigning any payoff value.

    For an antisymmetric table, g_ii=0 and opposite ordered pairs cancel.
    For a mixture, the coefficient of every g_ij is linear in the parent's
    role distribution. The identities are general; these exact checks use
    the two distributions already established in the project.
    """
    fair = [Fraction(n, 864) for n in (7, 35, 42, 105, 105, 105, 105, 105, 105, 108, 42)]
    dice456 = [Fraction(n, 27) for n in (0, 3, 6, 6, 6, 6, 0, 0, 0, 0, 0)]
    eta = Fraction(9, 10)
    if sum(fair) != 1 or sum(dice456) != 1:
        raise ValueError("Role distributions must be normalized")
    for p in (fair, dice456):
        # Each key denotes an unknown off-diagonal payoff g_ij with i<j.
        coefficients = defaultdict(Fraction)
        for i, pi in enumerate(p):
            for j, pj in enumerate(p):
                if i < j:
                    coefficients[(i, j)] += pi * pj
                elif i > j:
                    coefficients[(j, i)] -= pi * pj
        if any(coefficients.values()):
            raise ValueError("Antisymmetric payoffs should cancel for equal independent distributions")
    parent_mixture = [eta * a + (1 - eta) * b for a, b in zip(dice456, fair)]
    checked = 0
    for child in (fair, dice456):
        for i, pi in enumerate(parent_mixture):
            for j, cj in enumerate(child):
                # These are coefficients of g_ij, not monetary gains.
                if pi * cj != eta * dice456[i] * cj + (1 - eta) * fair[i] * cj:
                    raise ValueError("Mixture linearity fails for a fixed child distribution")
                checked += 1
    return checked


def create_figure():
    coefficient_count = check_symbolic_coefficients()
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=DPI)
    fig.patch.set_facecolor("white")
    texts, containers = [], []

    def text(x, y, s, **kwargs):
        kwargs.setdefault("ha", "center")
        kwargs.setdefault("va", "center")
        kwargs.setdefault("fontsize", 9)
        item = fig.text(x, y, s, **kwargs)
        texts.append(item)
        return item

    def box(left, bottom, width, height, fill="#F8FAFC", edge=LINE, pad=0.004):
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

    def inside(patch, x, y, s, **kwargs):
        item = text(x, y, s, **kwargs)
        containers.append((item, patch))
        return item

    text(0.5, 0.971, "From role probabilities to net gain", fontsize=13.5, fontweight="bold")
    text(0.5, 0.947, "One parent, one child; unit stake; both complete their turns.", fontsize=9.5, color=GRAY)
    text(0.5, 0.925, "Independent generation of the two final roles.", color=GRAY)
    for left, center, title, formula in (
            (0.08, 0.28, "Parent final roles", r"$\alpha_i=P_P(r_i)$"),
            (0.52, 0.72, "Child final roles", r"$\beta_j=P_C(s_j)$")):
        patch = box(left, 0.838, 0.40, 0.062, fill="#F0F5F9", edge="#B9C9D7")
        inside(patch, center, 0.884, title, fontsize=10, fontweight="bold", color=NAVY)
        inside(patch, center, 0.856, formula, fontsize=11, color=NAVY)
    arrow(0.28, 0.834, 0.28, 0.801)
    arrow(0.72, 0.834, 0.30, 0.801)

    joint = box(0.08, 0.615, 0.40, 0.182, fill="#F8FAFC")
    payoff = box(0.52, 0.615, 0.40, 0.182, fill="#FFFCF7", edge="#E5C69E")
    inside(joint, 0.28, 0.777, "Joint probabilities", fontsize=10.5, fontweight="bold")
    inside(joint, 0.28, 0.750, r"$J_{ij}=\alpha_i\beta_j$", fontsize=11, color=NAVY)
    inside(payoff, 0.72, 0.777, "Payoff matrix", fontsize=10.5, fontweight="bold")
    inside(payoff, 0.72, 0.750, "Payoff rules to be finalized", color=AMBER, fontweight="bold")
    joint_entries = [
        [r"$\alpha_1\beta_1$", r"$\alpha_1\beta_2$", r"$\cdots$"],
        [r"$\alpha_2\beta_1$", r"$\alpha_2\beta_2$", r"$\cdots$"],
        [r"$\vdots$", r"$\vdots$", r"$\ddots$"],
    ]
    payoff_entries = [
        [r"$g_{11}$", r"$g_{12}$", r"$\cdots$"],
        [r"$g_{21}$", r"$g_{22}$", r"$\cdots$"],
        [r"$\vdots$", r"$\vdots$", r"$\ddots$"],
    ]
    for left, entries, fill, color in (
            (0.10, joint_entries, "white", NAVY),
            (0.54, payoff_entries, "#FFFAF2", INK)):
        ax = fig.add_axes([left, 0.642, 0.36, 0.088])
        ax.set_axis_off()
        table = ax.table(cellText=entries, bbox=[0, 0, 1, 1], cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        for cell in table.get_celld().values():
            cell.set_facecolor(fill)
            cell.set_edgecolor(LINE)
            cell.set_linewidth(0.6)
            cell.get_text().set_color(color)
            texts.append(cell.get_text())
            containers.append((cell.get_text(), cell))
    inside(joint, 0.28, 0.628, "Rows r; columns s", color=GRAY)
    inside(payoff, 0.72, 0.628, "Split roles if payoffs differ", color=GRAY)

    arrow(0.28, 0.611, 0.5, 0.579)
    arrow(0.72, 0.611, 0.5, 0.579)
    weighted = box(0.08, 0.507, 0.84, 0.068)
    inside(weighted, 0.5, 0.559, "Elementwise weighting", fontsize=10, fontweight="bold")
    inside(weighted, 0.5, 0.532, r"$W_{ij}=J_{ij}\,g(r_i,s_j)$", fontsize=11)
    arrow(0.5, 0.503, 0.5, 0.487)
    summed = box(0.08, 0.414, 0.84, 0.068, fill="#F6F2FA", edge="#CEBEDD")
    inside(summed, 0.5, 0.468, "Sum over all role pairs", fontsize=10, fontweight="bold")
    inside(summed, 0.5, 0.437, r"$E[G]=\sum_{r,s}P_P(r)\,P_C(s)\,g(r,s)$", fontsize=12, color=PURPLE)
    text(0.5, 0.396, "G: parent net gain per unit stake, one child, one match.", fontsize=9.5)
    text(0.5, 0.374, "Positive: gain | Negative: loss | Zero: returned-stake tie, if adopted.", color=GRAY)

    check1 = box(0.08, 0.289, 0.84, 0.066)
    inside(check1, 0.5, 0.342, "Check 1: equal distributions and antisymmetry", fontsize=10, fontweight="bold")
    inside(check1, 0.5, 0.318,
           r"$P_P=P_C,\quad g(r,s)=-g(s,r)\quad\Longrightarrow\quad E[G]=0$", fontsize=10.5)
    inside(check1, 0.5, 0.299, r"Antisymmetry also requires $g(r,r)=0$.", color=GRAY)
    check2 = box(0.08, 0.140, 0.84, 0.131)
    inside(check2, 0.5, 0.257, "Check 2: linearity in the strategy mixture", fontsize=10, fontweight="bold")
    inside(check2, 0.5, 0.235, "Fixed child distribution, stake and payoff table; independent set choice.", color=GRAY)
    inside(check2, 0.5, 0.208,
           r"$E[G\mid H_1]=\eta E[G\mid456]+(1-\eta)E[G\mid\mathrm{fair}]$", fontsize=11)
    inside(check2, 0.5, 0.183,
           'For a fair child, if $E[G\\mid\\mathrm{fair}]=0$ and $\\eta=0.900$:', color=GRAY)
    inside(check2, 0.5, 0.159, '$E[G\\mid H_1]=0.900\\,E[G\\mid456]$', fontsize=11)

    text(0.5, 0.123, "Four distinct quantities", fontsize=9.5, fontweight="bold")
    for i, (label, formula, color) in enumerate((
            ("Die outcome\nmean", r"$E[X]$", NAVY),
            ("Win\nprobability", r"$P(\mathrm{win})$", INK),
            ("Strategy\nposterior", r"$P(H_1\mid\mathcal{D})$", PURPLE),
            ("Expected\nnet gain", r"$E[G]$", INK))):
        left, center = 0.08 + i * 0.21, 0.185 + i * 0.21
        patch = box(left, 0.019, 0.21, 0.089, fill="white", pad=0)
        inside(patch, center, 0.085, label, linespacing=1.25)
        inside(patch, center, 0.043, formula, fontsize=11, color=color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for item in texts:
        b = item.get_window_extent(renderer)
        if item.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {item.get_text()}')
        if b.x0 < 0 or b.y0 < 0 or b.x1 > fig.bbox.width or b.y1 > fig.bbox.height:
            raise ValueError(f'Clipped text: {item.get_text()}')
    for item, patch in containers:
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
    return fig, coefficient_count, len(texts)


def main():
    fig, coefficient_count, text_count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A13 - From role probabilities to expected net gain",
        "Subject": "Symbolic payoff framework and conditional symmetry/mixture identities; payoffs not finalized",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "payoffs_symbolic": True, "numeric_net_gain_computed": False,
        "antisymmetric_coefficients_cancel_checked": True,
        "mixture_coefficients_checked": coefficient_count,
        "text_elements_checked": text_count, "text_bounds_and_collisions_checked": True,
        "container_bounds_checked": True,
    }))


if __name__ == "__main__":
    main()

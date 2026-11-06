#!/usr/bin/env python3
"""A07: shared latent dice-set type versus independent type selection.

Requirements: Python 3 and Matplotlib. Recreates PNG and vector PDF beside
this complete source; no notebook, random sample or external data required.
Final size: 160 x 224 mm; PNG: 400 dpi; ordinary labels at least 9 pt.

The chosen model selects one common type at the start of a turn and keeps
it during rerolls. The second model is a reference alternative only.
All probabilities and High-indicator moments are computed with Fractions;
both full three-die distributions are checked over all 216 ordered triples.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from fractions import Fraction
from itertools import product, combinations
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, FancyArrowPatch

WIDTH_MM, HEIGHT_MM, DPI = 160, 224, 400
BASENAME = "kaiji_a07_shared_dice_state"
OUT = Path(__file__).resolve().parent
INK, GRAY, LINE = "#17212B", "#6B7280", "#CFD7DF"
NAVY, AMBER, PURPLE = "#2B5D7E", "#D98C3F", "#6F4A8E"
ETA = Fraction(9, 10)
TRIPLES = list(product(range(1, 7), repeat=3))
SHARED_EDGES = [("Z", f'X{i}') for i in range(1, 4)]
INDEPENDENT_EDGES = [(f'Z{i}', f'X{i}') for i in range(1, 4)]

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "text.color": INK, "pdf.fonttype": 42, "ps.fonttype": 42,
    "mathtext.fontset": "dejavusans",
})


def exact_data():
    fair = {x: Fraction(1, 216) for x in TRIPLES}
    only456 = {x: Fraction(1, 27) if min(x) >= 4 else Fraction(0) for x in TRIPLES}
    shared = {x: ETA * only456[x] + (1 - ETA) * fair[x] for x in TRIPLES}
    marginal = {x: ETA * Fraction(x >= 4, 3) + (1 - ETA) / 6 for x in range(1, 7)}
    independent = {x: marginal[x[0]] * marginal[x[1]] * marginal[x[2]] for x in TRIPLES}
    for dist in (fair, only456, shared, independent):
        if sum(dist.values()) != 1:
            raise ValueError("Distribution fails normalization")
    all_high = lambda dist: sum(p for x, p in dist.items() if min(x) >= 4)
    p0, ps, pi = map(all_high, (fair, shared, independent))
    if (p0, ps, pi) != (Fraction(1, 8), Fraction(73, 80), Fraction(6859, 8000)):
        raise ValueError("Incorrect all-High probability")
    if ps != ETA + (1 - ETA) * Fraction(1, 2) ** 3:
        raise ValueError("Shared-state mixture formula is incorrect")
    if pi != ((1 + ETA) / 2) ** 3:
        raise ValueError("Independent mixture formula is incorrect")
    if (ps / p0, pi / p0) != (Fraction(73, 10), Fraction(6859, 1000)):
        raise ValueError("Incorrect Bayes factors")
    for dist, expected_cov in ((shared, Fraction(9, 400)), (independent, Fraction(0))):
        means = [sum(p for x, p in dist.items() if x[i] >= 4) for i in range(3)]
        if means != [Fraction(19, 20)] * 3:
            raise ValueError("Incorrect marginal High probabilities")
        for i, j in combinations(range(3), 2):
            pair = sum(p for x, p in dist.items() if x[i] >= 4 and x[j] >= 4)
            if pair - means[i] * means[j] != expected_cov:
                raise ValueError("Incorrect pairwise High-indicator covariance")
            if dist is shared and pair != (1 + 3 * ETA) / 4:
                raise ValueError("Incorrect shared-state second moment")
    if ETA * (1 - ETA) / 4 != Fraction(9, 400):
        raise ValueError("Covariance formula is incorrect")
    # Check the graphical distinction: one common parent versus three separate parents.
    if len({source for source, target in SHARED_EDGES}) != 1:
        raise ValueError("Shared model must have one parent")
    if len({source for source, target in INDEPENDENT_EDGES}) != 3:
        raise ValueError("Independent model must have three parents")
    return p0, ps, pi


def create_figure():
    p0, ps, pi = exact_data()
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

    def panel(bottom, height, fill, edge):
        patch = FancyBboxPatch((0.065, bottom), 0.87, height,
                               transform=fig.transFigure,
                               boxstyle="round,pad=0.006,rounding_size=0.009",
                               facecolor=fill, edgecolor=edge, linewidth=0.7, zorder=0)
        fig.add_artist(patch)
        return patch

    def node(x, y, label, latent=False):
        w = 0.073
        h = w * WIDTH_MM / HEIGHT_MM
        patch = Ellipse((x, y), w, h, transform=fig.transFigure,
                        facecolor="#EEF2F6" if latent else "white",
                        edgecolor=GRAY, linewidth=1.0, zorder=3)
        fig.add_artist(patch)
        item = text(x, y, label, fontsize=11, zorder=4)
        containers.append((item, patch))
        return w, h

    def arrow(x1, y1, x2, y2):
        fig.add_artist(FancyArrowPatch((x1, y1), (x2, y2), transform=fig.transFigure,
                                      arrowstyle="-|>", mutation_scale=10,
                                      color=GRAY, linewidth=0.9, shrinkA=0, shrinkB=0,
                                      zorder=2))

    text(0.5, 0.968, "One shared state, dependent outcomes",
         fontsize=13, fontweight="bold")
    text(0.5, 0.930,
         "Conditional independence does not imply\nmarginal independence",
         fontsize=9.5, color=GRAY, linespacing=1.25)
    text(0.5, 0.892, 'High = {4, 5, 6}   |   Mixture under $H_1$: $\\eta=0.900$', color=GRAY)
    text(0.5, 0.870, f'$H_0$: always fair; $P(\\mathrm{{all\\ High}}\\mid H_0)=1/8={_fmt_number(float(p0))}$',
         color=NAVY)

    panel(0.600, 0.244, "#FFFCF7", "#E5C69E")
    text(0.09, 0.824, "A   Shared set", ha="left", fontsize=10.5, fontweight="bold")
    text(0.90, 0.824, "CHOSEN TURN MODEL", ha="right", fontsize=9, color=AMBER,
         fontweight="bold")
    z_y, x_y = 0.774, 0.702
    text(0.27, z_y, "One draw\nper turn", color=GRAY, linespacing=1.25)
    text(0.57, z_y + 0.010, '456 set: 90.000%', ha="left", color=AMBER)
    text(0.57, z_y - 0.012, 'Fair set: 10.000%', ha="left", color=NAVY)
    node(0.5, z_y, r"$Z$", latent=True)
    positions = (0.24, 0.5, 0.76)
    radius_y = 0.073 * WIDTH_MM / HEIGHT_MM / 2
    for i, x in enumerate(positions, 1):
        arrow(0.5, z_y - radius_y, x, x_y + radius_y)
        node(x, x_y, f'$X_{i}$')
    text(0.5, 0.663, "Given Z, the three outcomes are independent.", color=GRAY)
    text(0.5, 0.636,
         f'$P(\\mathrm{{all\\ High}}\\mid H_1)=\\eta+(1-\\eta)/8=73/80\\approx{_fmt_number(ps)}$',
         fontsize=10)
    text(0.5, 0.611,
         f'$\\mathrm{{BF}}=\\frac{{73/80}}{{1/8}}={_fmt_number(ps / p0)}$',
         fontsize=10.5)

    panel(0.328, 0.252, "#F8FAFC", LINE)
    text(0.09, 0.559, "B   Independent type selection per die",
         ha="left", fontsize=10.5, fontweight="bold")
    text(0.5, 0.534, 'Reference alternative: each type is 90.000% 456, 10.000% fair.', color=GRAY)
    z_y, x_y = 0.493, 0.421
    for i, x in enumerate(positions, 1):
        arrow(x, z_y - radius_y, x, x_y + radius_y)
        node(x, z_y, f'$Z_{i}$', latent=True)
        node(x, x_y, f'$X_{i}$')
    text(0.5, 0.382, 'Each marginal High probability is 0.950; outcomes are independent.', color=GRAY)
    text(0.5, 0.357,
         f'$P(\\mathrm{{all\\ High}}\\mid H_{{1,\\mathrm{{ind}}}})=0.950^3\\approx{_fmt_number(pi)}$',
         fontsize=10)
    text(0.5, 0.335,
         f'$\\mathrm{{BF}}_{{\\mathrm{{ind}}}}=8(0.950)^3={_fmt_number(pi / p0)}$',
         fontsize=10.5)

    text(0.09, 0.294, "Why the shared model is dependent",
         ha="left", fontsize=10.5, fontweight="bold")
    text(0.5, 0.266,
         r"Under shared-set $H_1$: $Y_i=\mathbf{1}\{X_i\geq4\}$, $i\ne j$.")
    text(0.5, 0.235, '$E[Y_i]=(1+\\eta)/2=0.950$', fontsize=10)
    text(0.5, 0.204, r"$E[Y_iY_j]=(1+3\eta)/4=0.925$", fontsize=10)
    text(0.5, 0.166,
         '$\\operatorname{Cov}(Y_i,Y_j)=\\frac{\\eta(1-\\eta)}{4}=\\frac{9}{400}\\approx0.023$',
         fontsize=11, color=PURPLE)
    text(0.5, 0.114,
         "Mixing over the same unknown type links the dice.\nGiven the type, the dice remain independent.",
         color=GRAY, linespacing=1.4)
    text(0.5, 0.059,
         "One throw shown; keep the selected set during rerolls.", color=GRAY)
    text(0.5, 0.034, "Bayes factors compare likelihoods; they are not posterior probabilities.", color=GRAY)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for item in texts:
        b = item.get_window_extent(renderer)
        if item.get_fontsize() < 9:
            raise ValueError(f'Text below 9 pt: {item.get_text()}')
        if b.x0 < 0 or b.y0 < 0 or b.x1 > fig.bbox.width or b.y1 > fig.bbox.height:
            raise ValueError(f'Clipped text: {item.get_text()}')
    # Intentional node-label containment is checked separately from text/text collisions.
    for item, patch in containers:
        inner, outer = item.get_window_extent(renderer), patch.get_window_extent(renderer)
        if inner.x0 < outer.x0 or inner.x1 > outer.x1 or inner.y0 < outer.y0 or inner.y1 > outer.y1:
            raise ValueError(f'Node label overflows: {item.get_text()}')
    for i, a in enumerate(texts):
        ba = a.get_window_extent(renderer)
        for b in texts[i+1:]:
            bb = b.get_window_extent(renderer)
            overlap_w = min(ba.x1, bb.x1) - max(ba.x0, bb.x0)
            overlap_h = min(ba.y1, bb.y1) - max(ba.y0, bb.y0)
            if overlap_w > 0.5 and overlap_h > 0.5:
                raise ValueError(f'Text collision: {a.get_text()} / {b.get_text()}')
    return fig, p0, ps, pi, len(texts)


def main():
    fig, p0, ps, pi, text_count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A07 - One shared dice-set state creates dependent outcomes",
        "Subject": "Conditional versus marginal independence; exact shared-set mixture likelihoods",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "fair_all_high": float(p0), "shared_all_high": float(ps),
        "independent_all_high": float(pi), "shared_bayes_factor": float(ps/p0),
        "independent_bayes_factor": float(pi/p0), "shared_covariance": 0.0225,
        "ordered_triples_checked_per_distribution": len(TRIPLES),
        "exact_probabilities_and_pair_moments_checked": True,
        "text_elements_checked": text_count, "text_bounds_and_collisions_checked": True,
        "node_label_bounds_checked": True,
    }))


if __name__ == "__main__":
    main()

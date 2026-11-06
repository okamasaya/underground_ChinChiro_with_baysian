#!/usr/bin/env python3
'A11: recorded stopping time versus a final-role-only record.\n\nRequirements: Python 3 and Matplotlib. Recreates PNG and vector PDF beside\nthis complete source; no notebook, random sample or external data needed.\nFinal size: 160 x 220 mm; PNG 400 dpi; ordinary labels at least 9 pt.\n\nH0 always uses a fair set. H1 selects a 456 set with probability 0.900 and\na fair set with probability 0.100 ONCE per turn and retains it for rerolls.\nStop at a completed role or after throw three; reroll only after no role.\nThe plotted likelihoods concern role EVENTS A={M=1,R=456} and B={R=456},\neach pooling the six ordered 456 permutations. They are not likelihoods\nof one particular ordered triple. For this event A, pooling permutations\ndoes not change the Bayes factor relative to the exact observed triple.\nNo posterior probabilities or payout assumptions appear in this figure.\n'

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()

from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product, permutations
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse

WIDTH_MM, HEIGHT_MM, DPI = 160, 220, 400
BASENAME = "kaiji_a11_retained_observation_information"
OUT = Path(__file__).resolve().parent
INK, GRAY, LINE = "#17212B", "#6B7280", "#D0D8E0"
NAVY, AMBER, PURPLE = "#2B5D7E", "#D98C3F", "#6F4A8E"
ETA = Fraction(9, 10)

plt.rcParams.update({
    "font.family": "Article JP Sans", "font.size": 9,
    "text.color": INK, "pdf.fonttype": 42, "ps.fonttype": 42,
    "mathtext.fontset": "dejavusans",
})


def coarse_role(x):
    s = tuple(sorted(x))
    if s == (4, 5, 6):
        return "456"
    if len(set(x)) == 3 and s != (1, 2, 3):
        return "none"
    return "other"


def terminal_distribution(one):
    """Enumerate all 3^3 coarse role sequences and sum unused future draws."""
    end = defaultdict(Fraction)
    for sequence in product(one, repeat=3):
        weight = Fraction(1)
        for r in sequence:
            weight *= one[r]
        m, role = next(((m, r) for m, r in enumerate(sequence, 1) if r != "none"), (3, "none"))
        end[(m, role)] += weight
    if sum(end.values()) != 1:
        raise ValueError("Terminal distribution must sum to one")
    return end


def exact_data():
    ends = {}
    for name, faces, total in (("fair", range(1, 7), 216), ("456", range(4, 7), 27)):
        triples = list(product(faces, repeat=3))
        counts = Counter(coarse_role(x) for x in triples)
        one = {r: Fraction(counts[r], total) for r in ("456", "none", "other")}
        if len(triples) != total or sum(one.values()) != 1:
            raise ValueError("Incorrect one-throw sample space")
        ends[name] = terminal_distribution(one)
        if ends[name][(1, "456")] != one["456"]:
            raise ValueError("Incorrect first-throw event")
        for m in (1, 2, 3):
            if ends[name][(m, "456")] != one["none"] ** (m - 1) * one["456"]:
                raise ValueError("Incorrect path probability for final role 456")
    mixed = {key: ETA * ends["456"][key] + (1 - ETA) * ends["fair"][key]
             for key in ends["fair"]}
    if sum(mixed.values()) != 1:
        raise ValueError("Mixture must be applied once per turn")
    out = {}
    for event in ("A", "B"):
        values = {}
        for name, dist in (("fair", ends["fair"]), ("456", ends["456"]), ("mixed", mixed)):
            values[name] = dist[(1, "456")] if event == "A" else sum(dist[(m, "456")] for m in (1, 2, 3))
        values["bf"] = values["mixed"] / values["fair"]
        out[event] = values
    if out["A"] != {"fair": Fraction(1, 36), "456": Fraction(2, 9),
                     "mixed": Fraction(73, 360), "bf": Fraction(73, 10)}:
        raise ValueError("Incorrect Lane A likelihoods or Bayes factor")
    if out["B"] != {"fair": Fraction(7, 144), "456": Fraction(2, 9),
                     "mixed": Fraction(59, 288), "bf": Fraction(59, 14)}:
        raise ValueError("Incorrect Lane B likelihoods or Bayes factor")
    if out["B"]["mixed"] - out["A"]["mixed"] != (1 - ETA) * (out["B"]["fair"] - out["A"]["fair"]):
        raise ValueError("Extra reroll paths must come from the fair-set component")
    fair_b = Fraction(1, 36) * (1 + Fraction(1, 2) + Fraction(1, 4))
    if fair_b != out["B"]["fair"]:
        raise ValueError("Incorrect fair-dice stopping-time marginalization")
    for x in permutations((4, 5, 6)):
        pf, p456 = Fraction(1, 216), Fraction(1, 27)
        if (ETA * p456 + (1 - ETA) * pf) / pf != out["A"]["bf"]:
            raise ValueError("Pooling the six permutations should preserve this Bayes factor")
    return out


def create_figure():
    data = exact_data()
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
                               boxstyle=f'round,pad={pad},rounding_size=0.007',
                               facecolor=fill, edgecolor=edge, linewidth=0.8, zorder=0)
        fig.add_artist(patch)
        return patch

    def arrow(x1, y1, x2, y2):
        fig.add_artist(FancyArrowPatch((x1, y1), (x2, y2), transform=fig.transFigure,
                                      arrowstyle="-|>", mutation_scale=10,
                                      color=GRAY, linewidth=0.9, shrinkA=0, shrinkB=0, zorder=1))

    def throw_node(x, y, number):
        w = 0.045
        h = w * WIDTH_MM / HEIGHT_MM
        circle = Ellipse((x, y), w, h, transform=fig.transFigure,
                          facecolor="white", edgecolor=GRAY, linewidth=0.8, zorder=2)
        fig.add_artist(circle)
        containers.append((text(x, y, str(number)), circle))
        return w / 2

    text(0.5, 0.969, "Throw history versus final role", fontsize=13.5, fontweight="bold")
    text(0.5, 0.942, '$H_0$: fair   |   $H_1$: 90.000% 456 set + 10.000% fair set', color=GRAY)
    text(0.5, 0.919, "Select one set per turn; retain it during rerolls.", color=GRAY)
    root = box(0.20, 0.848, 0.60, 0.045, fill="#EEF2F6", edge=GRAY)
    containers.append((text(0.5, 0.8705, "One played turn; two recording policies", fontsize=9.5), root))
    arrow(0.5, 0.844, 0.275, 0.818)
    arrow(0.5, 0.844, 0.725, 0.818)

    cards = []
    for lane, left, center in (("A", 0.07, 0.275), ("B", 0.52, 0.725)):
        info = data[lane]
        card = box(left, 0.214, 0.41, 0.596)
        cards.append(card)
        card_texts = []

        def lane_text(y, s, **kwargs):
            item = text(center, y, s, **kwargs)
            card_texts.append(item)
            return item

        lane_text(0.786, "A   History retained" if lane == "A" else "B   Final role only",
                  fontsize=10.5, fontweight="bold")
        lane_text(0.763, "Keep the stopping time M" if lane == "A" else "Discard the throw history", color=GRAY)
        lane_text(0.724, "456 on the FIRST throw,\nthen stop" if lane == "A" else "FINAL role is 456;\nthrow count unrecorded",
                  fontsize=10, linespacing=1.3)
        if lane == "A":
            throw_node(center, 0.668, 1)
            lane_text(0.637, "End on throw 1", color=GRAY)
            lane_text(0.607, r"$A=\{M=1,\ R=456\}$", fontsize=10)
        else:
            xs = (center - 0.105, center, center + 0.105)
            for i, x in enumerate(xs, 1):
                throw_node(x, 0.668, i)
            for x1, x2 in zip(xs, xs[1:]):
                arrow(x1 + 0.025, 0.668, x2 - 0.025, 0.668)
            lane_text(0.637, "Reroll only after no role", color=GRAY)
            lane_text(0.607, r"$B=\{R=456\}$", fontsize=10)

        lane_text(0.573, r"Fair ($H_0$)", color=NAVY, fontweight="bold")
        lane_text(0.546, f"$P({lane}\\mid H_0)={info['fair'].numerator}/{info['fair'].denominator}$", fontsize=11, color=NAVY)
        lane_text(0.505, "Pure 456 set", color=AMBER, fontweight="bold")
        lane_text(0.478, f"$P({lane}\\mid456)={info['456'].numerator}/{info['456'].denominator}$", fontsize=11, color=AMBER)
        lane_text(0.435, r"Mixed strategy ($H_1$)", color=AMBER, fontweight="bold")
        fair_fraction = f"{info['fair'].numerator}/{info['fair'].denominator}"
        lane_text(0.408, f'$0.90(2/9)+0.10({fair_fraction})$', fontsize=10)
        lane_text(0.373, f"$P({lane}\\mid H_1)={info['mixed'].numerator}/{info['mixed'].denominator}$", fontsize=11, color=AMBER)
        lane_text(0.327, "Bayes factor", fontweight="bold", color=PURPLE, fontsize=9.5)
        mixed_fraction = f"{info['mixed'].numerator}/{info['mixed'].denominator}"
        bf = info["bf"]
        lane_text(0.288, f'$\\frac{{{mixed_fraction}}}{{{fair_fraction}}}=\\frac{{{bf.numerator}}}{{{bf.denominator}}}$',
                  fontsize=12, color=PURPLE)
        lane_text(0.243, '7.300' if lane == "A" else f'$\\approx{_fmt_number(float(bf))}$',
                  fontsize=14, fontweight="bold", color=PURPLE)
        containers.extend((item, card) for item in card_texts)

    text(0.5, 0.184, "B also includes a 456 role on throws 2 or 3.", fontsize=9.5)
    text(0.5, 0.157, "Each event pools the six ordered permutations of 456.", color=GRAY)
    text(0.5, 0.119,
         r"$P(B\mid H_0)=\frac{1}{36}\left(1+\frac{1}{2}+\frac{1}{4}\right)=\frac{7}{144}$",
         fontsize=11, color=NAVY)
    text(0.5, 0.065, "Match the likelihood to the data that were actually recorded.",
         fontsize=10, fontweight="bold")
    text(0.5, 0.033, "Bayes factors are likelihood ratios, not posterior probabilities.", color=GRAY)

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
    return fig, data, len(texts)


def main():
    fig, data, text_count = create_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT / f'{BASENAME}.png', OUT / f'{BASENAME}.pdf'
    fig.savefig(png, dpi=DPI, facecolor="white")
    fig.savefig(pdf, facecolor="white", metadata={
        "Title": "A11 - Full throw history versus final role only",
        "Subject": "Recording-dependent event likelihoods under a fixed per-turn mixture strategy",
        "Creator": "Matplotlib",
    })
    plt.close(fig)
    print(json.dumps({
        "outputs": [str(png), str(pdf)], "size_mm": [WIDTH_MM, HEIGHT_MM],
        "exact_event_data": {k: {name: str(value) for name, value in v.items()} for k, v in data.items()},
        "first_throw_bayes_factor": float(data["A"]["bf"]),
        "final_only_bayes_factor": float(data["B"]["bf"]),
        "ordered_outcomes_checked": 243, "coarse_role_sequences_checked": 2 * 27,
        "exact_likelihoods_and_per_turn_mixture_checked": True,
        "six_ordered_permutation_bayes_factors_checked": True,
        "text_elements_checked": text_count, "text_bounds_and_collisions_checked": True,
        "container_bounds_checked": True,
    }))


if __name__ == "__main__":
    main()

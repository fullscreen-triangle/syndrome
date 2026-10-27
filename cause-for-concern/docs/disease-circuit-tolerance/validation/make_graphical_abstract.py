#!/usr/bin/env python3
"""
make_graphical_abstract.py -- the graphical abstract, from results.json.

One landscape panel, 13 x 5 cm at print size:

  left    a metabolic cycle with one defective edge: the sum of potential
          differences around it vanishes unless an edge datum is wrong
  centre  one log axis of |computed cycle sum|, read twice: by a fixed
          tolerance of 1e-6 (two verdicts) and by the cycle-local
          tolerance (three verdicts, bounded by the two floors)
  right   three numbers from the experimental data

The floors on the axis are the medians over the 67 cycles of measured
equilibrium constants (TECRDB). Every number drawn is read from
results.json and realdata/results_real.json, like the figure panels.

    python make_graphical_abstract.py
"""

from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(os.path.dirname(HERE), "figures")
R = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))
REAL = json.load(open(os.path.join(HERE, "realdata", "results_real.json"),
                      encoding="utf-8"))

plt.rcParams.update({
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 6.5,
    "axes.linewidth": 0.6,
})

# Verdict colours: the paper's verdict family, with the orange taken at
# the darker step (the panels' ORANGE) so that all three pass the
# lightness and colour-vision checks on white.
C_CONS, C_UND, C_INC = "#4393C3", "#D95F02", "#B2182B"
INK, MUTED, RULE = "#1A1A1A", "#555555", "#9A9A9A"

# ---- numbers --------------------------------------------------------
r1, r2 = REAL["R1_tecrdb"], REAL["R2_erythrocyte"]
cycles = r1["cycles"]
eps_num = float(np.median([c["eps_num"] for c in cycles]))
eps_data = float(np.median([c["eps_data"] for c in cycles]))
eps_star = eps_num + eps_data
gap = math.log10(eps_data / eps_num)
n_cyc = r1["cycle_space_dimension"]
n_fixed = r1["fixed_tolerance"]["flagged"]
n_inc = r1["verdicts"]["gaussian"].get("INCONSISTENT", 0)
n_und = r1["verdicts"]["gaussian"].get("UNDECIDABLE", 0)
ery_nu = r2["cycle_space_dimension"]
ery_full = r2["cycles_fully_measured"]
assert r2["pyruvate_kinase_on_a_cycle"] == [False]
EPS_FIXED = R["V2_fixed_tolerance"]["eps_fixed"]
assert EPS_FIXED == r1["fixed_tolerance"]["eps"]
XMIN, XMAX = 1e-16, 1e5


def sci(x: float) -> str:
    e = int(math.floor(math.log10(x)))
    m = x / 10 ** e
    return rf"{m:.1f}\times10^{{{e}}}" if round(m, 1) != 1.0 else rf"10^{{{e}}}"


fig = plt.figure(figsize=(13 / 2.54, 5 / 2.54))
fig.text(0.5, 0.955,
         "A cycle-consistency tolerance belongs to the cycle and the data, "
         "not the solver",
         ha="center", va="top", fontsize=7.4, fontweight="bold", color=INK)

# ---- left: the cycle ------------------------------------------------
axL = fig.add_axes([0.01, 0.06, 0.22, 0.78])
axL.set_xlim(-1.55, 1.55)
axL.set_ylim(-1.75, 1.35)
axL.set_aspect("equal")
axL.axis("off")
n = 6
pts = [(math.cos(math.pi / 2 - 2 * math.pi * k / n),
        math.sin(math.pi / 2 - 2 * math.pi * k / n)) for k in range(n)]
bad = 1                                     # the defective edge: 1 -> 2
for k in range(n):
    a, b = pts[k], pts[(k + 1) % n]
    is_bad = k == bad
    axL.add_patch(FancyArrowPatch(
        a, b, arrowstyle="-|>", mutation_scale=6,
        shrinkA=7, shrinkB=7, lw=1.8 if is_bad else 0.9,
        color=C_INC if is_bad else RULE, zorder=1))
for k, (x, y) in enumerate(pts):
    axL.plot(x, y, "o", ms=9, mfc="white", mec=INK, mew=0.8, zorder=2)
    axL.text(x, y, rf"$\mu_{k + 1}$", ha="center", va="center",
             fontsize=5.2, color=INK, zorder=3)
ax_, ay_ = pts[bad]
bx_, by_ = pts[bad + 1]
axL.text((ax_ + bx_) / 2 + 0.33, (ay_ + by_) / 2 + 0.05, "defect $D$",
         ha="left", va="center", fontsize=5.8, color=INK)
axL.text(0, 0.02, r"$H_\ell=\sum_\ell \Delta\mu$", ha="center",
         va="center", fontsize=6.3, color=INK)
axL.text(0, -1.33,
         "= 0 exactly if the edge data\nare a gradient. Errors on the\n"
         r"potentials $\mu_i$ cancel; errors" "\non an edge do not.",
         ha="center", va="top", fontsize=5.4, color=MUTED, linespacing=1.25)

# ---- centre: one axis, two readings ---------------------------------
axC = fig.add_axes([0.285, 0.25, 0.455, 0.52])
axC.set_xscale("log")
axC.set_xlim(XMIN, XMAX)
axC.set_ylim(-0.98, 1.75)
H = 0.62


def band(y, lo, hi, color, label, txt="white"):
    axC.barh(y, hi - lo, left=lo, height=H, color=color,
             edgecolor="white", linewidth=1.0, zorder=2)
    if label:
        xc = math.sqrt(lo * hi)
        axC.text(xc, y, label, ha="center", va="center", fontsize=5.6,
                 fontweight="bold", color=txt, zorder=4)


# fixed tolerance: two verdicts, split at 1e-6. Labels sit where the
# verdict is supported, outside the hatched stretch.
band(1, XMIN, EPS_FIXED, C_CONS, None)
band(1, EPS_FIXED, XMAX, C_INC, None)
for lo, hi, lab in ((XMIN, eps_num, "CONS."), (eps_star, XMAX, "INCONS.")):
    axC.text(math.sqrt(lo * hi), 1, lab, ha="center", va="center",
             fontsize=5.6, fontweight="bold", color="white", zorder=4)
# the stretch where the fixed verdict is unsupported
axC.add_patch(Rectangle((eps_num, 1 - H / 2), eps_star - eps_num, H,
                        fill=False, hatch="////", edgecolor="white",
                        linewidth=0, zorder=3))
# cycle-local tolerance: three verdicts
band(0, XMIN, eps_num, C_CONS, "CONS.")
band(0, eps_num, eps_star, C_UND, "UNDECIDABLE")
band(0, eps_star, XMAX, C_INC, "INCONS.")

axC.set_yticks([])
for y, lab in ((1, rf"fixed tolerance $\varepsilon={sci(EPS_FIXED)}$: "
                   "two verdicts"),
               (0, r"cycle-local tolerance $\varepsilon^{*}$: "
                   "three verdicts")):
    axC.text(XMIN, y + H / 2 + 0.04, lab, ha="left", va="bottom",
             fontsize=5.6, color=INK)
axC.set_xticks([1e-15, 1e-12, 1e-9, 1e-6, 1e-3, 1e0, 1e3])
axC.tick_params(axis="x", labelsize=5.6, length=2, width=0.5,
                colors=MUTED)
axC.minorticks_off()
for s in ("top", "right", "left"):
    axC.spines[s].set_visible(False)
axC.spines["bottom"].set_color(RULE)
axC.set_xlabel(r"|computed cycle sum|  (kJ/mol)", fontsize=6.0,
               color=MUTED, labelpad=1.5)

# floor markers and the gap between them
for x, txt in ((eps_num,
                rf"$\varepsilon_{{num}}={sci(eps_num)}$" "\n(arithmetic)"),
               (eps_star,
                rf"$\varepsilon_{{data}}\approx{eps_data:.0f}$" "\n"
                "(measured data)")):
    for y0, y1 in ((-0.36, H / 2), (1 - H / 2, 1 + H / 2)):
        axC.plot([x, x], [y0, y1], color=INK, lw=0.6, ls=(0, (2, 1.5)),
                 zorder=5)
    axC.text(x, -0.42, txt, ha="center", va="top", fontsize=5.0,
             color=INK, linespacing=1.1)
axC.annotate("", xy=(eps_num, 1.6), xytext=(eps_star, 1.6),
             arrowprops=dict(arrowstyle="<->", lw=0.6, color=INK,
                             shrinkA=0, shrinkB=0))
axC.text(math.sqrt(eps_num * eps_star), 1.68,
         rf"{gap:.1f} decades the data cannot resolve", ha="center",
         va="bottom", fontsize=5.4, color=INK)

# ---- right: the numbers ---------------------------------------------
facts = [
    (f"{n_fixed}/{n_cyc}", "measured-data cycles\n"
                           r"flagged by $\varepsilon=10^{-6}$"),
    (f"{n_inc}/{n_cyc}", rf"flagged by $\varepsilon^{{*}}$;"
                         f"\n{n_und} UNDECIDABLE"),
    (f"{ery_full}/{ery_nu}", "erythrocyte cycles fully\n"
                             "measured; pyruvate kinase\nlies on none"),
]
x0, y = 0.775, 0.80
for big, small in facts:
    fig.text(x0, y, big, ha="left", va="top", fontsize=9.5,
             fontweight="bold", color=INK)
    fig.text(x0, y - 0.085, small, ha="left", va="top", fontsize=5.3,
             color=MUTED, linespacing=1.2)
    y -= 0.255

os.makedirs(FIGDIR, exist_ok=True)
for ext, kw in (("png", {"dpi": 600}), ("pdf", {})):
    p = os.path.join(FIGDIR, f"graphical_abstract.{ext}")
    fig.savefig(p, facecolor="white", **kw)
    print("wrote", p)

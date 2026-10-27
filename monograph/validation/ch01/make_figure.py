#!/usr/bin/env python3
"""
make_figure.py -- figure for chapter 1: which erythrocyte enzymes lie on a
cycle, under each choice of what the medium holds.

Reads results.json (medium_closure.py) and writes
../../figures/ch01_erythrocyte_cycles.{png,pdf}. A filled circle means the
enzyme lies on a cycle of ker S_I and can therefore carry a steady flux; a
grey ring means it lies on none and carries none.

    python make_figure.py
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.normpath(os.path.join(HERE, "..", "..", "figures"))
R = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))

GROUPS = [("Glycolysis", ["HK1", "GPI", "PFKL", "ALDOA", "TPI1", "GAPDH",
                          "PGK1", "PGAM1", "ENO1", "PKLR", "LDHA"]),
          ("Rapoport–Luebering", ["BPGM", "MINPP1"]),
          ("Pentose phosphate", ["G6PD", "PGLS", "PGD", "RPE", "RPIA", "TKT",
                                 "TALDO1"]),
          ("Glutathione", ["GSR", "GPX1"]),
          ("Ca$^{2+}$ pump", ["ATP2B4"])]
HIGHLIGHT = {"PKLR", "G6PD"}

full = R["closure"]["physiological+supplied"]["enzymes_on_a_cycle"]
abl = R["medium_ablation"]


def ablated(label: str) -> dict:
    lost = set(abl[label]["enzymes_leaving_every_cycle"])
    return {g: (v and g not in lost) for g, v in full.items()}


COLS = [
    ("no medium:\nall species\ninternal", R["closure"]["none"]),
    ("glucose,\nlactate,\nwater", R["closure"]["minimal"]),
    ("plasma\n(16 species),\nannotated", R["closure"]["physiological"]),
    ("plasma,\n+ RHEA:\n27626", R["closure"]["physiological+supplied"]),
    ("… minus\nlactate", None, "L-lactate (MCT1)"),
    ("… minus\nCO$_2$", None, "CO2 (band 3, diffusion)"),
    ("… minus\noxidant\n(H$_2$O$_2$,\nGSSG)", None,
     "no oxidant (H2O2 and GSSG both held internal)"),
]

INK, MUTED, RULE, ON = "#1A1A1A", "#666666", "#BBBBBB", "#2166AC"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7,
                     "axes.linewidth": 0.5})

rows = [(grp, g) for grp, gs in GROUPS for g in gs]
fig, ax = plt.subplots(figsize=(17.0 / 2.54, 9.2 / 2.54))
ax.set_xlim(-0.6, len(COLS) - 0.4)
ax.set_ylim(len(rows) - 0.4 + 0.2, -0.8)
ax.axis("off")

for j, col in enumerate(COLS):
    if col[1] is not None:
        state = col[1]["enzymes_on_a_cycle"]
        n_emerg = col[1]["emergent_cycles"]
    else:
        state = ablated(col[2])
        n_emerg = abl[col[2]]["emergent_cycles"]
    ax.text(j, -1.0, col[0], ha="center", va="bottom", fontsize=6.4,
            color=INK, linespacing=1.15)
    ax.text(j, len(rows) - 0.05, f"{n_emerg}", ha="center", va="top",
            fontsize=6.6, color=MUTED)
    for i, (_, g) in enumerate(rows):
        if g not in state:
            continue
        if state[g]:
            ax.plot(j, i, "o", ms=6.2, mfc=ON, mec=ON, zorder=3)
        else:
            ax.plot(j, i, "o", ms=4.6, mfc="white", mec=RULE, mew=0.9,
                    zorder=3)
ax.text(-0.55, len(rows) - 0.05, "emergent cycles", ha="right", va="top",
        fontsize=6.4, color=MUTED, transform=ax.transData)
ax.plot([3.5, 3.5], [-0.5, len(rows) - 0.5], color=RULE, lw=0.6,
        ls=(0, (2, 2)), zorder=1)

y = 0
for grp, gs in GROUPS:
    ax.text(-2.85, y, grp, ha="left", va="center", fontsize=6.3,
            color=MUTED, style="italic", transform=ax.transData)
    for g in gs:
        ax.text(-0.55, y, g, ha="right", va="center", fontsize=6.6,
                color=INK, fontweight="bold" if g in HIGHLIGHT else "normal")
        y += 1
    if y < len(rows):
        ax.plot([-2.85, len(COLS) - 0.5], [y - 0.5, y - 0.5],
                color="#E6E6E6", lw=0.5, zorder=0)

ax.set_xlim(-2.9, len(COLS) - 0.4)
fig.subplots_adjust(left=0.01, right=0.99, top=0.83, bottom=0.03)
os.makedirs(FIG, exist_ok=True)
for ext, kw in (("png", {"dpi": 400}), ("pdf", {})):
    p = os.path.join(FIG, f"ch01_erythrocyte_cycles.{ext}")
    fig.savefig(p, facecolor="white", **kw)
    print("wrote", p)

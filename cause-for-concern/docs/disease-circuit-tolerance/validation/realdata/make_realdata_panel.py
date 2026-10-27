#!/usr/bin/env python3
"""
make_realdata_panel.py -- Figure 5, from results_real.json.

  A  every cycle of the measured-reaction network (TECRDB): its computed
     sum against its cycle-local tolerance, with its numerical floor, the
     fixed tolerance 1e-6, and the two calibrations of the data floor
  B  replicate measurements of one reaction, whose cycle sums are known
     to vanish: the fraction of standardised deviations beyond each
     threshold, against the Gaussian tail the data floor assumes

    python make_realdata_panel.py
"""

from __future__ import annotations

import json
import os
from statistics import NormalDist

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "figures")
R = json.load(open(os.path.join(HERE, "results_real.json"), encoding="utf-8"))

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "font.family": "DejaVu Sans",
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 10,
    "axes.titleweight": "bold", "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "legend.frameon": False, "legend.fontsize": 7.5,
})
# the verdict colours of panels 1-4 and the graphical abstract
C_UND, C_INC, INK, MUTED = "#D95F02", "#B2182B", "#1A1A1A", "#666666"
C_A = "#2166AC"

a = R["R1_tecrdb"]
cyc = a["cycles"]
q = a["quantiles"]
eps_star = np.array([c["eps_num"] + c["eps_data"] for c in cyc])
h = np.array([abs(c["H"]) for c in cyc])
en = np.array([c["eps_num"] for c in cyc])
inc = np.array([c["verdict"] == "INCONSISTENT" for c in cyc])

fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.5, 4.0),
                               gridspec_kw={"width_ratios": [1.25, 1]})

# ---- A ---------------------------------------------------------------
axA.set_xscale("log"); axA.set_yscale("log")
x0, x1 = 4, 50
axA.set_xlim(x0, x1); axA.set_ylim(1e-16, 3e2)
xs = np.array([x0, x1])
axA.plot(xs, xs, color=INK, lw=1.1)
axA.text(30, 30 * 2.4, r"$|H|=\varepsilon^{*}$", fontsize=7.5, ha="right",
         va="bottom", color=INK)
ratio = q["replicate_calibrated"] / q["gaussian"]
axA.plot(xs, ratio * xs, color=INK, lw=0.9, ls=(0, (1, 1.5)))
axA.text(5.0, 5.0 * ratio * 1.6, "replicate-calibrated", fontsize=7,
         color=MUTED, va="bottom")
axA.axhline(1e-6, color=MUTED, lw=0.9, ls=(0, (4, 2)))
axA.text(x1 * 0.95, 1e-6 * 2.2,
         rf"fixed $\varepsilon=10^{{-6}}$: flags {a['fixed_tolerance']['flagged']}"
         f" of {len(cyc)}", fontsize=7.5, ha="right", va="bottom",
         color=MUTED)
axA.scatter(eps_star, en, marker="_", s=40, color=MUTED, lw=1.0,
            label=r"numerical floor $\varepsilon_{\mathrm{num}}$")
axA.scatter(eps_star[~inc], h[~inc], s=22, color=C_UND,
            edgecolor="white", lw=0.6, zorder=3,
            label=f"UNDECIDABLE ({(~inc).sum()})")
axA.scatter(eps_star[inc], h[inc], s=26, color=C_INC, marker="D",
            edgecolor="white", lw=0.6, zorder=4,
            label=f"INCONSISTENT ({inc.sum()})")
axA.set_xlabel(r"cycle-local tolerance $\varepsilon^{*}(\ell)$ (kJ/mol)")
axA.set_ylabel(r"$|$computed cycle sum$|$ (kJ/mol)")
axA.set_yticks([1e-15, 1e-12, 1e-9, 1e-6, 1e-3, 1e0])
axA.set_xticks([5, 10, 20, 50], labels=["5", "10", "20", "50"])
axA.minorticks_off()
axA.legend(loc="center right", bbox_to_anchor=(1.0, 0.42))
axA.set_title("A   Measured equilibrium constants (TECRDB)", loc="left",
              fontsize=9.5)
axA.text(x0 * 1.05, 3e-11, "no cycle sum reaches its numerical floor:\n"
         "CONSISTENT is unattainable on measured data",
         fontsize=7, color=MUTED, va="bottom")

# ---- B ---------------------------------------------------------------
t = np.linspace(0, 6, 601)
gauss = [2 * (1 - NormalDist().cdf(v)) for v in t]
axB.set_yscale("log")
axB.plot(t, gauss, color=INK, lw=1.0, ls=(0, (4, 2)),
         label="Gaussian (assumed by the data floor)")
for dev, col, lab in (
        (np.array(a["replicate_abs_deviations"]), C_UND,
         f"all grades (n = {len(a['replicate_abs_deviations'])})"),
        (np.array(R["R1_sensitivity_grade_A_only"]["replicate_abs_deviations"]),
         C_A, "grade A only (n = {})".format(
             len(R["R1_sensitivity_grade_A_only"]
                 ["replicate_abs_deviations"])))):
    surv = [(dev > v).mean() for v in t]
    axB.step(t, np.maximum(surv, 1e-9), where="post", color=col, lw=1.4,
             label=lab)
zg = q["gaussian"]
axB.axvline(zg, color=MUTED, lw=0.7)
frac = a["replicate_calibration"]["frac_beyond_gaussian_quantile"]
axB.annotate(f"{100 * frac:.1f}% beyond the 1% point", xy=(zg, frac),
             xytext=(zg + 0.35, frac * 2.6), fontsize=7.5, color=INK,
             arrowprops=dict(arrowstyle="-", lw=0.6, color=INK))
axB.set_ylim(1e-3, 1.2); axB.set_xlim(0, 6)
axB.set_xlabel("standardised deviation of a repeated measurement, |t|")
axB.set_ylabel("fraction beyond |t|")
axB.legend(loc="lower left")
axB.set_title("B   Repeated measurements: cycles of known sum zero",
              loc="left", fontsize=9.5)

fig.tight_layout(w_pad=2.5)
p = os.path.join(FIGDIR, "panel5_measured_data.png")
fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
print("wrote", p)

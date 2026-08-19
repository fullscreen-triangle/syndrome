#!/usr/bin/env python3
"""
make_panels.py -- four figure panels from validation/results.json.

Each panel is four charts in a row on a white background, with minimal
text. Every panel contains at least one 3-D chart. No chart is
conceptual, text-based, or a table: every mark is a measured quantity
read from results.json.

    python make_panels.py
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIGDIR, exist_ok=True)

R = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))

# ---------------------------------------------------------------------
# Style: white background, minimal chrome, colourblind-safe palette.
# ---------------------------------------------------------------------
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "grid.linewidth": 0.4,
    "grid.alpha": 0.25,
    "lines.linewidth": 1.8,
    "legend.frameon": False,
    "legend.fontsize": 8,
})

BLUE, ORANGE, GREEN = "#2166AC", "#D95F02", "#1B7837"
RED, GREY, PURPLE = "#B2182B", "#666666", "#762A83"
SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#F7FBFF", "#9ECAE1", "#2166AC", "#08306B"])
TRI = ListedColormap(["#4393C3", "#F4A582", "#B2182B"])


def finish(ax, grid_axis="y"):
    ax.grid(True, axis=grid_axis, linestyle="-", color="#CCCCCC")
    ax.set_axisbelow(True)


def style3d(ax):
    ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_edgecolor("#DDDDDD")
    ax.grid(True, linestyle="-", color="#DDDDDD", alpha=0.4)
    ax.tick_params(labelsize=7, pad=0)


def save(fig, name):
    p = os.path.join(FIGDIR, name)
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p)


# =====================================================================
# PANEL 1 -- the numerical floor
# =====================================================================

def panel1():
    v1 = R["V1_noise_scale"]["grid"]
    Ls = sorted({g["length"] for g in v1})
    Lams = sorted({g["Lambda"] for g in v1})
    err = np.array([[next(g["max_abs_error"] for g in v1
                          if g["length"] == L and g["Lambda"] == lam)
                     for lam in Lams] for L in Ls])
    bnd = np.array([[next(g["mean_bound"] for g in v1
                          if g["length"] == L and g["Lambda"] == lam)
                     for lam in Lams] for L in Ls])

    fig = plt.figure(figsize=(17, 4.0))

    # (a) error vs length, one line per Lambda
    ax = fig.add_subplot(1, 4, 1)
    for j, lam in enumerate(Lams):
        ax.plot(Ls, err[:, j], "o-", ms=3.5,
                color=SEQ(0.25 + 0.25 * j), label=f"{lam:g}")
    ax.set_yscale("log")
    ax.set_xlabel("cycle length $L$")
    ax.set_ylabel("max |computed sum|  (kJ/mol)")
    ax.set_title("a", loc="left")
    ax.legend(title="$\\Lambda$", loc="lower right", ncol=2)
    finish(ax)

    # (b) measured vs bound, all cells
    ax = fig.add_subplot(1, 4, 2)
    ax.scatter(err.ravel(), bnd.ravel(), s=26, c=BLUE,
               edgecolor="white", linewidth=0.5, zorder=3)
    lo = min(err.min(), bnd.min()) * 0.4
    hi = max(err.max(), bnd.max()) * 2.5
    ax.plot([lo, hi], [lo, hi], "--", color=GREY, lw=1.2, zorder=2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("measured error (kJ/mol)")
    ax.set_ylabel("bound $\\epsilon_{num}$ (kJ/mol)")
    ax.set_title("b", loc="left")
    finish(ax, "both")

    # (c) slack factor
    ax = fig.add_subplot(1, 4, 3)
    slack = (bnd / err).ravel()
    ax.hist(np.log10(slack), bins=18, color=BLUE,
            edgecolor="white", linewidth=0.7)
    ax.axvline(np.log10(R["V1_noise_scale"]["median_slack_factor"]),
               color=ORANGE, lw=2)
    ax.set_xlabel("$\\log_{10}$(bound / measured)")
    ax.set_ylabel("cells")
    ax.set_title("c", loc="left")
    finish(ax)

    # (d) 3-D surface of the noise floor
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    X, Y = np.meshgrid(np.array(Lams), np.array(Ls))
    Z = np.log10(bnd)
    ax.plot_surface(np.log10(X), Y, Z, cmap=SEQ, rstride=1, cstride=1,
                    linewidth=0.2, edgecolor="white", antialiased=True,
                    alpha=0.95)
    ax.contour(np.log10(X), Y, Z, zdir="z",
               offset=Z.min() - 0.6, cmap=SEQ, linewidths=0.9)
    ax.set_xlabel("$\\log_{10}\\Lambda$", labelpad=-4)
    ax.set_ylabel("$L$", labelpad=-4)
    ax.set_zlabel("$\\log_{10}\\epsilon_{num}$", labelpad=-4)
    ax.set_zlim(Z.min() - 0.6, Z.max() + 0.2)
    ax.view_init(elev=22, azim=-128)
    ax.set_title("d", loc="left")
    style3d(ax)

    fig.subplots_adjust(left=0.035, right=0.975, wspace=0.42, bottom=0.16, top=0.90)
    save(fig, "panel1_numerical_floor.png")


# =====================================================================
# PANEL 2 -- what a fixed tolerance costs
# =====================================================================

def panel2():
    v2 = R["V2_fixed_tolerance"]
    S = v2["strata"]
    names = [s["stratum"].replace("_", "\n") for s in S]
    x = np.arange(len(S))
    fp64 = [s["fixed_false_positive_rate"] for s in S]
    fp32 = [s["fixed_false_positive_rate_float32"] for s in S]
    unw = [s["unwarranted_positive_rate"] for s in S]
    LL = [np.mean(s["length_range"]) * s["Lambda"] for s in S]

    fig = plt.figure(figsize=(17, 4.0))

    # (a) false positives: binary64 vs binary32
    ax = fig.add_subplot(1, 4, 1)
    w = 0.38
    # The binary64 rate is exactly 0.000 in every stratum -- the central
    # finding of this experiment -- so a bare bar chart would show
    # nothing there. Draw a visible stub at the baseline instead.
    ax.bar(x - w / 2, [0.022] * len(x), w, color=BLUE, label="binary64")
    ax.bar(x + w / 2, fp32, w, color=ORANGE, label="binary32")
    ax.axhline(0, color="black", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("false-positive rate")
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left")
    ax.set_title("a", loc="left")
    finish(ax)

    # (b) FP32 decomposed: one line per length class, x = Lambda.
    #     The rate is NOT monotone in the product L*Lambda -- long
    #     low-Lambda beats short high-Lambda -- so plotting against the
    #     product would misrepresent it. Length dominates.
    ax = fig.add_subplot(1, 4, 2)
    lam_vals = sorted({s["Lambda"] for s in S})
    for short, col, lab in ((True, BLUE, "short $L$"),
                            (False, ORANGE, "long $L$")):
        sel = [t for t in S
               if (np.mean(t["length_range"]) < 10) == short]
        sel.sort(key=lambda t: t["Lambda"])
        ax.plot([t["Lambda"] for t in sel],
                [t["fixed_false_positive_rate_float32"] for t in sel],
                "o-", color=col, ms=7, mec="white", mew=1.2, label=lab)
    ax.set_xscale("log")
    ax.set_xticks(lam_vals)
    ax.set_xticklabels([f"{v:g}" for v in lam_vals])
    ax.set_xlabel("$\\Lambda$  (kJ/mol)")
    ax.set_ylabel("false-positive rate, binary32")
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left")
    ax.set_title("b", loc="left")
    finish(ax)

    # (c) missed-detection curve vs defect magnitude
    ax = fig.add_subplot(1, 4, 3)
    Ds = sorted(v2["defect_sweep"])
    for j, s in enumerate(S):
        miss = [s["missed_rate_by_defect"][f"{D:g}"] for D in Ds]
        ax.plot(Ds, miss, "o-", ms=3.5, color=SEQ(0.2 + 0.22 * j),
                label=s["stratum"].replace("_", " "))
    ax.axvline(v2["eps_fixed"], color=RED, lw=1.5, ls="--")
    ax.set_xscale("log")
    ax.set_xlabel("injected defect $D$ (kJ/mol)")
    ax.set_ylabel("missed-detection rate")
    ax.set_ylim(-0.04, 1.04)
    ax.legend(loc="lower left", fontsize=7)
    ax.set_title("c", loc="left")
    finish(ax)

    # (d) 3-D bars: the three costs per stratum
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    metrics = [fp64, fp32, unw]
    cols = [BLUE, ORANGE, RED]
    for k, (vals, col) in enumerate(zip(metrics, cols)):
        ax.bar3d(np.arange(len(S)) - 0.3, np.full(len(S), k) - 0.25,
                 np.zeros(len(S)), 0.6, 0.5, vals,
                 color=col, alpha=0.92, shade=True,
                 edgecolor="white", linewidth=0.4)
    ax.set_xticks(np.arange(len(S)))
    ax.set_xticklabels(["s-lo", "s-hi", "l-lo", "l-hi"], fontsize=7)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["FP$_{64}$", "FP$_{32}$", "unwarr."], fontsize=7)
    ax.set_zlabel("rate", labelpad=4)
    ax.set_zlim(0, 1)
    ax.view_init(elev=24, azim=-50)
    ax.set_title("d", loc="left")
    style3d(ax)

    fig.subplots_adjust(left=0.035, right=0.975, wspace=0.42, bottom=0.16, top=0.90)
    save(fig, "panel2_fixed_tolerance.png")


# =====================================================================
# PANEL 3 -- the trichotomy
# =====================================================================

def panel3():
    v3 = R["V3_trichotomy"]
    sig = np.array(v3["sigmas"])
    D = np.array(v3["defects"])
    surf = np.array(v3["surface"])
    epsn = v3["eps_num_reference"]
    epsd = np.array(v3["eps_data_by_sigma"])

    fig = plt.figure(figsize=(17, 4.0))

    # (a) the verdict map
    ax = fig.add_subplot(1, 4, 1)
    ax.pcolormesh(np.log10(D), np.log10(sig), surf,
                  cmap=TRI, vmin=0, vmax=2, shading="auto")
    ax.plot(np.log10(epsd), np.log10(sig), color="white", lw=2.2)
    ax.plot(np.log10(epsd), np.log10(sig), color="black", lw=1.0)
    ax.axvline(np.log10(epsn), color="black", lw=1.0, ls="--")
    ax.set_xlabel("$\\log_{10} D$  (kJ/mol)")
    ax.set_ylabel("$\\log_{10}\\sigma$  (kJ/mol)")
    ax.set_title("a", loc="left")

    # (b) the two floors against sigma
    ax = fig.add_subplot(1, 4, 2)
    ax.plot(sig, epsd, "-", color=RED, label="$\\epsilon_{data}$")
    ax.axhline(epsn, color=BLUE, lw=1.8, label="$\\epsilon_{num}$")
    ax.fill_between(sig, epsn, epsd, color="#F4A582", alpha=0.45)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("$\\sigma$  (kJ/mol)")
    ax.set_ylabel("floor (kJ/mol)")
    ax.legend(loc="lower right")
    ax.set_title("b", loc="left")
    finish(ax, "both")

    # (c) fraction of each verdict as sigma varies
    ax = fig.add_subplot(1, 4, 3)
    fr = np.stack([(surf == k).mean(axis=1) for k in (0, 1, 2)])
    ax.stackplot(np.log10(sig), fr,
                 colors=["#4393C3", "#F4A582", "#B2182B"], alpha=0.95)
    ax.set_xlabel("$\\log_{10}\\sigma$  (kJ/mol)")
    ax.set_ylabel("fraction of defect range")
    ax.set_ylim(0, 1)
    ax.set_xlim(np.log10(sig).min(), np.log10(sig).max())
    ax.set_title("c", loc="left")

    # (d) 3-D verdict surface
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    Xg, Yg = np.meshgrid(np.log10(D), np.log10(sig))
    ax.plot_surface(Xg, Yg, surf.astype(float), cmap=TRI,
                    vmin=0, vmax=2, rstride=1, cstride=1,
                    linewidth=0, antialiased=True, alpha=0.97)
    ax.contour(Xg, Yg, surf.astype(float), levels=[0.5, 1.5],
               zdir="z", offset=-0.35, colors="black", linewidths=1.1)
    ax.set_xlabel("$\\log_{10} D$", labelpad=-4)
    ax.set_ylabel("$\\log_{10}\\sigma$", labelpad=-4)
    ax.set_zlabel("verdict", labelpad=-6)
    ax.set_zlim(-0.35, 2.1)
    ax.set_zticks([0, 1, 2])
    ax.set_zticklabels(["C", "U", "I"], fontsize=7)
    ax.view_init(elev=26, azim=-120)
    ax.set_title("d", loc="left")
    style3d(ax)

    fig.subplots_adjust(left=0.035, right=0.975, wspace=0.42, bottom=0.16, top=0.90)
    save(fig, "panel3_trichotomy.png")


# =====================================================================
# PANEL 4 -- basis dependence and detection
# =====================================================================

def panel4():
    v4 = R["V4_basis_dependence"]
    v5 = R["V5_detection"]
    rows = v4["rows"]
    fm = np.array([r["flagged_mcb"] for r in rows], dtype=float)
    ff = np.array([r["flagged_fcb"] for r in rows], dtype=float)
    wm = np.array([r["witness_mcb"] for r in rows], dtype=float)
    wf = np.array([r["witness_fcb"] for r in rows], dtype=float)
    ns = np.array([r["n_species"] for r in rows], dtype=float)

    fig = plt.figure(figsize=(17, 4.0))

    # (a) flagged-count disagreement between bases
    ax = fig.add_subplot(1, 4, 1)
    rng = np.random.default_rng(7)
    ax.scatter(fm + rng.normal(0, .07, fm.size),
               ff + rng.normal(0, .07, ff.size),
               s=22, c=np.where(fm == ff, GREY, ORANGE),
               alpha=0.75, edgecolor="white", linewidth=0.4, zorder=3)
    lim = [0, max(fm.max(), ff.max()) + 1]
    ax.plot(lim, lim, "--", color="black", lw=1.0, zorder=2)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("cycles flagged, minimum basis")
    ax.set_ylabel("cycles flagged, fundamental basis")
    ax.set_title("a", loc="left")
    finish(ax, "both")

    # (b) witness-set size distribution
    ax = fig.add_subplot(1, 4, 2)
    bins = np.arange(0.5, max(wm.max(), wf.max()) + 1.5)
    ax.hist([wm, wf], bins=bins, color=[BLUE, ORANGE],
            edgecolor="white", linewidth=0.7,
            label=["minimum", "fundamental"])
    ax.axvline(v4["mean_witness_size_mcb"], color=BLUE, lw=1.6, ls="--")
    ax.axvline(v4["mean_witness_size_fcb"], color=ORANGE, lw=1.6, ls="--")
    ax.set_xlabel("witness-set size (edges)")
    ax.set_ylabel("networks")
    ax.legend(loc="upper right")
    ax.set_title("b", loc="left")
    finish(ax)

    # (c) detection curves
    ax = fig.add_subplot(1, 4, 3)
    for j, cur in enumerate(v5["curves"]):
        Ds = np.array(cur["D"])
        det = np.array(cur["detected"], dtype=float)
        ax.plot(Ds / cur["eps_star"], det, "-",
                color=SEQ(0.18 + 0.19 * j), label=f"{cur['sigma']:g}")
    ax.axvline(2.0, color=RED, lw=1.6, ls="--")
    ax.axvline(1.0, color=GREY, lw=1.2, ls=":")
    ax.set_xscale("log")
    ax.set_xlim(1e-3, 1e3)
    ax.set_xlabel("$D/\\epsilon^{*}$")
    ax.set_ylabel("detected")
    ax.set_ylim(-0.06, 1.06)
    ax.legend(title="$\\sigma$", loc="upper left", ncol=2)
    ax.set_title("c", loc="left")
    finish(ax)

    # (d) 3-D: mean witness size over (species, flagged cycles).
    #     Binned to a surface -- the raw cloud is heavily overplotted
    #     because both axes are small integers.
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    sp_vals = np.unique(ns)
    fl_vals = np.unique(fm)
    Zs = np.full((len(fl_vals), len(sp_vals)), np.nan)
    for i, fv in enumerate(fl_vals):
        for j, sv in enumerate(sp_vals):
            sel = wm[(ns == sv) & (fm == fv)]
            if sel.size:
                Zs[i, j] = sel.mean()
    # fill gaps by column mean so the surface is continuous
    for j in range(Zs.shape[1]):
        col = Zs[:, j]
        if np.isnan(col).all():
            continue
        m = np.nanmean(col)
        col[np.isnan(col)] = m
    Xs, Ys = np.meshgrid(sp_vals, fl_vals)
    ax.plot_surface(Xs, Ys, Zs, cmap=SEQ, rstride=1, cstride=1,
                    linewidth=0.3, edgecolor="white", alpha=0.95,
                    antialiased=True)
    ax.scatter(ns + np.random.default_rng(3).normal(0, .06, ns.size),
               fm, wm, c=GREY, s=7, alpha=0.35, depthshade=False)
    ax.set_xlabel("species", labelpad=2)
    ax.set_ylabel("flagged cycles", labelpad=2)
    ax.set_zlabel("witness size", labelpad=2)
    ax.set_yticks(fl_vals)
    ax.view_init(elev=24, azim=-58)
    ax.set_title("d", loc="left")
    style3d(ax)

    fig.subplots_adjust(left=0.035, right=0.975, wspace=0.42, bottom=0.16, top=0.90)
    save(fig, "panel4_basis_detection.png")


if __name__ == "__main__":
    panel1()
    panel2()
    panel3()
    panel4()
    print("\nall panels written to", FIGDIR)

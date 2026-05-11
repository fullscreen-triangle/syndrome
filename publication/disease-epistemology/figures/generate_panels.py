"""
Generate 5 publication panels from validation results.
Each panel: 4 charts in a row, at least 1 three-dimensional chart per panel.
Style: white background, minimal text, all charts data-driven.
"""

import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm, gridspec
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.optimize import linprog

RNG = np.random.default_rng(42)
RESULTS = pathlib.Path(__file__).parent.parent / "validation" / "results"
OUT = pathlib.Path(__file__).parent

# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------
CMAP_MAIN = cm.viridis
CMAP_WARM = cm.plasma
CMAP_COOL = cm.cividis

def load(name):
    return json.loads((RESULTS / f"{name}.json").read_text())

def fig_style(fig):
    fig.patch.set_facecolor("white")

def ax_style(ax, is3d=False):
    ax.set_facecolor("white")
    for spine in ax.spines.values() if not is3d else []:
        spine.set_linewidth(0.6)
        spine.set_color("#aaaaaa")
    ax.tick_params(labelsize=7, color="#999999", length=3)
    if is3d:
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor("#dddddd")
        ax.yaxis.pane.set_edgecolor("#dddddd")
        ax.zaxis.pane.set_edgecolor("#dddddd")
        ax.grid(True, linewidth=0.3, color="#eeeeee")
        ax.tick_params(labelsize=6)

def label(ax, xl="", yl="", size=7):
    ax.set_xlabel(xl, fontsize=size, labelpad=3, color="#555555")
    ax.set_ylabel(yl, fontsize=size, labelpad=3, color="#555555")

def label3(ax, xl="", yl="", zl="", size=6):
    ax.set_xlabel(xl, fontsize=size, labelpad=1, color="#555555")
    ax.set_ylabel(yl, fontsize=size, labelpad=1, color="#555555")
    ax.set_zlabel(zl, fontsize=size, labelpad=1, color="#555555")

PANEL_W, PANEL_H = 14, 3.5

# ===========================================================================
# Panel 1 — Floor Positivity (E01-E05)
# ===========================================================================
def panel1():
    e01 = load("E01_floor_positivity_vs_N")
    e02 = load("E02_floor_monotone_sigma")
    e05 = load("E05_poisson_shot_noise")

    fig = plt.figure(figsize=(PANEL_W, PANEL_H), facecolor="white")
    gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.38)

    # --- 1a: beta vs N (log-log) ---
    ax = fig.add_subplot(gs[0])
    ax_style(ax)
    Ns = e01["N_values"]
    bs = e01["beta_values"]
    ax.loglog(Ns, bs, "o-", color="#2563EB", lw=1.6, ms=5, mfc="white", mew=1.4)
    # theoretical line: 1/sqrt(N)
    Nx = np.logspace(1, 7, 200)
    ax.loglog(Nx, 1.0 / np.sqrt(Nx), "--", color="#94A3B8", lw=0.9)
    label(ax, "N", "β")

    # --- 1b: beta vs sigma ---
    ax = fig.add_subplot(gs[1])
    ax_style(ax)
    sigmas = e02["sigma_values"]
    betas  = e02["beta_values"]
    ax.plot(sigmas, betas, color="#7C3AED", lw=1.8)
    ax.fill_between(sigmas, 0, betas, alpha=0.12, color="#7C3AED")
    label(ax, "σ", "β")

    # --- 1c: empirical vs theoretical floor (Poisson noise) ---
    ax = fig.add_subplot(gs[2])
    ax_style(ax)
    pn = e05["per_N_results"]
    Ns_p = sorted(int(k) for k in pn)
    emp = [pn[str(N)]["empirical_floor"] for N in Ns_p]
    the = [pn[str(N)]["theoretical_floor"] for N in Ns_p]
    xs = np.arange(len(Ns_p))
    ax.bar(xs - 0.18, the, 0.32, color="#94A3B8", label="theory")
    ax.bar(xs + 0.18, emp, 0.32, color="#2563EB", alpha=0.85, label="empirical")
    ax.set_xticks(xs)
    ax.set_xticklabels([str(N) for N in Ns_p], fontsize=6)
    label(ax, "N", "floor")

    # --- 1d: 3D surface S(x,y) = max(0, r - R) + beta ---
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax_style(ax3, is3d=True)
    u = np.linspace(-2.5, 2.5, 60)
    v = np.linspace(-2.5, 2.5, 60)
    X, Y = np.meshgrid(u, v)
    beta = 0.05
    R_cell = 1.0
    r = np.sqrt(X**2 + Y**2)
    Z = np.maximum(0, r - R_cell) + beta
    surf = ax3.plot_surface(X, Y, Z, cmap=CMAP_MAIN, alpha=0.88,
                            linewidth=0, antialiased=True, rcount=40, ccount=40)
    ax3.contourf(X, Y, Z, zdir="z", offset=Z.min(), cmap=CMAP_MAIN, alpha=0.3, levels=12)
    label3(ax3, "x₁", "x₂", "S")
    ax3.view_init(elev=28, azim=-55)

    fig.savefig(OUT / "panel_1_floor_positivity.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved panel_1_floor_positivity.png")


# ===========================================================================
# Panel 2 — Cell-Truth and Representational Invariance (E06-E10)
# ===========================================================================
def panel2():
    e09 = load("E09_cell_size_vs_beta")
    e10 = load("E10_mode_nonprivilege")

    fig = plt.figure(figsize=(PANEL_W, PANEL_H), facecolor="white")
    gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.40)

    # --- 2a: cell fraction vs beta (bubble plot) ---
    ax = fig.add_subplot(gs[0])
    ax_style(ax)
    per_s = e09["per_sigma"]
    sigmas_s = [float(k) for k in per_s]
    betas_s  = [per_s[k]["beta"] for k in per_s]
    fracs    = [per_s[k]["fraction_inside"] for k in per_s]
    scatter = ax.scatter(betas_s, fracs,
                         s=[f * 800 + 30 for f in fracs],
                         c=sigmas_s, cmap=CMAP_WARM, zorder=3, edgecolors="white", lw=0.6)
    ax.plot(betas_s, fracs, "--", color="#aaa", lw=0.7, zorder=2)
    label(ax, "β", "fraction inside C")

    # --- 2b: mode success rates (polar bar) ---
    ax = fig.add_subplot(gs[1], polar=True)
    ax.set_facecolor("white")
    modes = list(e10["mode_success_rates"].keys())
    rates = list(e10["mode_success_rates"].values())
    n_modes = len(modes)
    angles = np.linspace(0, 2 * np.pi, n_modes, endpoint=False)
    bars = ax.bar(angles, rates, width=1.8, bottom=0.88,
                  color=["#2563EB", "#7C3AED", "#059669"],
                  alpha=0.85, edgecolor="white", linewidth=0.8)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(angles)
    ax.set_xticklabels(modes, fontsize=7, color="#444")
    ax.set_yticklabels([])
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor("white")

    # --- 2c: excess-S distribution (outside cell only) vs reference floor ---
    ax = fig.add_subplot(gs[2])
    ax_style(ax)
    beta_v = 0.05
    R_cell = 1.0
    outside_pts = RNG.standard_normal((3000, 2))
    outside_pts = outside_pts / np.linalg.norm(outside_pts, axis=1, keepdims=True)
    r_out = RNG.uniform(1.05, 2.5, 3000)
    outside_pts *= r_out[:, None]
    s_out = np.linalg.norm(outside_pts, axis=1) - R_cell  # excess beyond cell boundary
    bins = np.linspace(0, 1.5, 50)
    counts, edges = np.histogram(s_out, bins=bins, density=True)
    mids = 0.5 * (edges[:-1] + edges[1:])
    ax.fill_between(mids, 0, counts, color="#F59E0B", alpha=0.55, step="mid")
    ax.step(mids, counts, color="#D97706", lw=1.0, where="mid")
    ax.axvline(0, color="#2563EB", lw=1.8, ls="-")   # the floor wall at dist=0
    label(ax, "dist(x, C)", "density")

    # --- 2d: 3D — S landscape with cell boundary visible as a plateau ---
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax_style(ax3, is3d=True)
    u = np.linspace(-2.2, 2.2, 55)
    X, Y = np.meshgrid(u, u)
    r = np.sqrt(X**2 + Y**2)
    Z = np.where(r <= 1.0, beta_v, r - 1.0 + beta_v)
    ax3.plot_surface(X, Y, Z, cmap=CMAP_COOL, alpha=0.90,
                     linewidth=0, antialiased=True, rcount=40, ccount=40)
    # Mark the plateau edge as a circle
    theta = np.linspace(0, 2 * np.pi, 100)
    ax3.plot(np.cos(theta), np.sin(theta),
             np.full(100, beta_v), color="#F59E0B", lw=1.5)
    label3(ax3, "x₁", "x₂", "S")
    ax3.view_init(elev=32, azim=40)

    fig.savefig(OUT / "panel_2_cell_truth.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved panel_2_cell_truth.png")


# ===========================================================================
# Panel 3 — Group Blindness (E11-E15)
# ===========================================================================
def panel3():
    e11 = load("E11_composite_floor_positive")
    e13 = load("E13_floor_compounds_with_n")
    e15 = load("E15_asymptotic_floor")

    fig = plt.figure(figsize=(PANEL_W, PANEL_H), facecolor="white")
    gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.40)

    # --- 3a: composite floor vs n (homogeneous ensemble) ---
    ax = fig.add_subplot(gs[0])
    ax_style(ax)
    ns = e13["n_values"]
    floors = e13["composite_floors"]
    ax.semilogy(ns, floors, "s-", color="#DC2626", lw=1.8, ms=5,
                mfc="white", mew=1.4)
    ax.fill_between(ns, 1e-28, floors, alpha=0.10, color="#DC2626")
    label(ax, "n cells", "S_flat(E)")

    # --- 3b: composite floor vs individual beta (asymptotic, n=10) ---
    ax = fig.add_subplot(gs[1])
    ax_style(ax)
    bvs = [r["beta"] for r in e15["results"]]
    cvs = [r["composite_floor"] for r in e15["results"]]
    ax.loglog(bvs, cvs, "o-", color="#7C3AED", lw=1.6, ms=4, mfc="white", mew=1.2)
    # reference: linear (if floor = beta, 1:1 line)
    bx = np.logspace(-6, -1, 100)
    ax.loglog(bx, bx, "--", color="#CBD5E1", lw=0.8)
    label(ax, "β", "S_flat(E)")

    # --- 3c: distribution of composite floors across 500 random ensembles ---
    ax = fig.add_subplot(gs[2])
    ax_style(ax)
    # Regenerate from same seed as validation
    rng2 = np.random.default_rng(42)
    all_floors = []
    for _ in range(500):
        n = rng2.integers(2, 20)
        betas = rng2.uniform(0.001, 0.5, size=n)
        prod  = float(np.prod(betas))
        s_sum = float(np.sum(betas))
        f     = prod / s_sum ** (n - 1)
        all_floors.append(f)
    log_floors = np.log10(np.clip(all_floors, 1e-30, None))
    ax.hist(log_floors, bins=40, color="#F59E0B", edgecolor="white",
            linewidth=0.4, density=True)
    label(ax, "log₁₀ S_flat", "density")

    # --- 3d: 3D surface — composite floor as function of (n, beta) ---
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax_style(ax3, is3d=True)
    ns_g  = np.arange(2, 12)
    bs_g  = np.logspace(-2, -0.3, 15)
    Ng, Bg = np.meshgrid(ns_g, bs_g)
    Fg = np.zeros_like(Ng, dtype=float)
    for i in range(Ng.shape[0]):
        for j in range(Ng.shape[1]):
            n  = int(Ng[i, j])
            b  = Bg[i, j]
            Fg[i, j] = b ** n / (n * b) ** (n - 1)
    Fg_log = np.log10(np.clip(Fg, 1e-30, None))
    ax3.plot_surface(Ng.astype(float), np.log10(Bg), Fg_log,
                     cmap=cm.RdPu, alpha=0.88,
                     linewidth=0, antialiased=True, rcount=30, ccount=30)
    label3(ax3, "n", "log β", "log S_flat")
    ax3.view_init(elev=25, azim=-60)

    fig.savefig(OUT / "panel_3_group_blindness.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved panel_3_group_blindness.png")


# ===========================================================================
# Panel 4 — Purpose as Fixed-Point (E16-E18)
# ===========================================================================
def panel4():
    e18 = load("E18_purpose_stability")

    fig = plt.figure(figsize=(PANEL_W, PANEL_H), facecolor="white")
    gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.42)

    # Fixed-point setup (reproduce from validation seed)
    rng4 = np.random.default_rng(42)
    dim = 5
    A = rng4.standard_normal((dim, dim))
    A = A / (np.linalg.norm(A) * 1.1)
    b = rng4.standard_normal(dim) * 0.2
    x_star = np.linalg.solve(np.eye(dim) - A, b)

    # --- 4a: convergence from a single trajectory ---
    ax = fig.add_subplot(gs[0])
    ax_style(ax)
    x = rng4.standard_normal(dim) * 2
    residuals = []
    for _ in range(120):
        residuals.append(float(np.linalg.norm(x - x_star)))
        x = A @ x + b
    ax.semilogy(residuals, color="#059669", lw=1.8)
    ax.axhline(1e-12, color="#CBD5E1", lw=0.7, ls="--")
    label(ax, "iteration", "‖x − x*‖")

    # --- 4b: fixed-point scatter across goal perturbations ---
    ax = fig.add_subplot(gs[1])
    ax_style(ax)
    rng_g = np.random.default_rng(0)
    fps_x, fps_y = [], []
    for _ in range(200):
        bg = b + rng_g.standard_normal(dim) * 0.002
        xg = np.linalg.solve(np.eye(dim) - A, bg)
        fps_x.append(xg[0])
        fps_y.append(xg[1])
    ax.scatter(fps_x, fps_y, s=8, c="#7C3AED", alpha=0.55, edgecolors="none")
    ax.scatter([x_star[0]], [x_star[1]], s=60, c="#DC2626", zorder=5,
               edgecolors="white", lw=0.8)
    label(ax, "x*₁", "x*₂")

    # --- 4c: residual vs perturbation norm ---
    ax = fig.add_subplot(gs[2])
    ax_style(ax)
    eps_list = e18["perturbation_norms"]
    res_list = e18["residuals_after_iteration"]
    ax.loglog(eps_list, res_list, "o", color="#F59E0B", ms=5, alpha=0.8,
              mfc="white", mew=1.2)
    ax.axhline(1e-12, color="#CBD5E1", lw=0.7, ls="--")
    label(ax, "‖ε‖", "residual")

    # --- 4d: 3D — multiple trajectories converging to fixed point ---
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax_style(ax3, is3d=True)
    rng_t = np.random.default_rng(7)
    colors_t = cm.plasma(np.linspace(0.2, 0.9, 12))
    for ci, col in enumerate(colors_t):
        x0 = x_star + rng_t.standard_normal(dim) * 1.5
        traj = [x0[:3].copy()]
        x_t = x0.copy()
        for _ in range(60):
            x_t = A @ x_t + b
            traj.append(x_t[:3].copy())
        traj = np.array(traj)
        ax3.plot(traj[:, 0], traj[:, 1], traj[:, 2],
                 lw=0.9, color=col, alpha=0.75)
    ax3.scatter([x_star[0]], [x_star[1]], [x_star[2]],
                s=60, c="#DC2626", zorder=10)
    label3(ax3, "x₁", "x₂", "x₃")
    ax3.view_init(elev=22, azim=35)

    fig.savefig(OUT / "panel_4_purpose_attractor.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved panel_4_purpose_attractor.png")


# ===========================================================================
# Panel 5 — Self-Consistency, Holonomy, and Therapeutics (E19-E25)
# ===========================================================================
def panel5():
    e21 = load("E21_template_vs_holonomy_auc")
    e22 = load("E22_local_invisibility")
    e23 = load("E23_sparse_therapeutic_lp")
    e25 = load("E25_side_effect_bound")

    fig = plt.figure(figsize=(PANEL_W, PANEL_H), facecolor="white")
    gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.42)

    # Reproduce holonomy data (same logic as E21 experiment)
    rng5 = np.random.default_rng(42)

    def make_healthy(n, r):
        phi = r.uniform(0, 2, n)
        a = np.abs(r.standard_normal((n, n)))
        a = (a + a.T) / 2
        np.fill_diagonal(a, 0)
        L = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    L[i, j] = a[i, j] + phi[i]
        return L

    def make_diseased(n, pert, r):
        L = make_healthy(n, r)
        noise = r.standard_normal((n, n)) * pert
        np.fill_diagonal(noise, 0)
        return L + noise

    def hol(L, loop):
        h = 0.0
        for k in range(len(loop)):
            i, j = loop[k], loop[(k + 1) % len(loop)]
            h += L[i, j] - L[j, i]
        return h

    n_nodes = 8
    n_loops = 8
    n_samp = 200

    scores_t, scores_h, labels = [], [], []
    L_tmpl = make_healthy(n_nodes, rng5)
    tv = L_tmpl.flatten()

    for lbl in [0]*n_samp + [1]*n_samp:
        L = make_healthy(n_nodes, rng5) if lbl == 0 else make_diseased(n_nodes, 0.8, rng5)
        scores_t.append(float(np.linalg.norm(L.flatten() - tv)))
        hs = []
        for _ in range(n_loops):
            ll = int(rng5.integers(3, n_nodes))
            lp = list(rng5.choice(n_nodes, size=ll, replace=False))
            hs.append(abs(hol(L, lp)))
        scores_h.append(float(np.mean(hs)))
        labels.append(lbl)

    labels = np.array(labels)
    scores_t = np.array(scores_t)
    scores_h = np.array(scores_h)

    def roc(y, score):
        thresholds = np.sort(np.unique(score))[::-1]
        tprs, fprs = [0], [0]
        for t in thresholds:
            pred = score >= t
            tp = np.sum(pred & (y == 1))
            fp = np.sum(pred & (y == 0))
            tprs.append(tp / np.sum(y == 1))
            fprs.append(fp / np.sum(y == 0))
        tprs.append(1); fprs.append(1)
        return np.array(fprs), np.array(tprs)

    fpr_t, tpr_t = roc(labels, scores_t)
    fpr_h, tpr_h = roc(labels, scores_h)

    # --- 5a: ROC curves ---
    ax = fig.add_subplot(gs[0])
    ax_style(ax)
    ax.plot(fpr_t, tpr_t, color="#94A3B8", lw=1.6, label="template")
    ax.plot(fpr_h, tpr_h, color="#059669", lw=1.8, label="holonomy")
    ax.plot([0, 1], [0, 1], "--", color="#e2e8f0", lw=0.8)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    label(ax, "FPR", "TPR")

    # --- 5b: log10(|H_ℓ|+ε) distribution healthy vs diseased ---
    ax = fig.add_subplot(gs[1])
    ax_style(ax)
    eps = 1e-16
    log_h = np.log10(scores_h + eps)
    bins_h = np.linspace(-17, 1, 50)
    ax.hist(log_h[labels == 0], bins=bins_h, color="#2563EB", alpha=0.70, density=True)
    ax.hist(log_h[labels == 1], bins=bins_h, color="#DC2626", alpha=0.65, density=True)
    ax.axvline(-15, color="#94A3B8", lw=0.8, ls="--")  # machine-ε reference
    label(ax, "log₁₀|H_ℓ|", "density")

    # --- 5c: L1 drug sparsity — dot plot of drug weights for a sample solution ---
    ax = fig.add_subplot(gs[2])
    ax_style(ax)
    n_loops_lp = 4
    n_drugs = 20
    rng_lp = np.random.default_rng(99)
    H0 = rng_lp.standard_normal(n_loops_lp) * 0.5
    B  = rng_lp.standard_normal((n_loops_lp, n_drugs))
    c_lp = np.concatenate([np.zeros(n_drugs), np.ones(n_drugs)])
    A_eq = np.hstack([B, np.zeros((n_loops_lp, n_drugs))])
    b_eq = -H0
    A_ub = np.vstack([np.hstack([np.eye(n_drugs), -np.eye(n_drugs)]),
                      np.hstack([-np.eye(n_drugs), -np.eye(n_drugs)])])
    b_ub = np.zeros(2 * n_drugs)
    res  = linprog(c_lp, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                   bounds=[(None, None)]*n_drugs + [(0, None)]*n_drugs,
                   method="highs")
    eta  = res.x[:n_drugs]
    colors_d = ["#2563EB" if abs(e) > 1e-4 else "#E2E8F0" for e in eta]
    ax.bar(np.arange(n_drugs), np.abs(eta), color=colors_d, edgecolor="none", width=0.7)
    ax.axhline(0, color="#aaa", lw=0.5)
    label(ax, "drug index", "|η|")

    # --- 5d: 3D holonomy landscape over 2 log-rate perturbation axes ---
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax_style(ax3, is3d=True)
    # Build a 5-node healthy circuit; perturb two specific rates
    rng_3d = np.random.default_rng(7)
    n_h = 5
    L_base = make_healthy(n_h, rng_3d)
    loop_fixed = [0, 1, 2, 3, 4]

    d1_vals = np.linspace(-2.0, 2.0, 35)
    d2_vals = np.linspace(-2.0, 2.0, 35)
    D1, D2 = np.meshgrid(d1_vals, d2_vals)
    H_surf = np.zeros_like(D1)
    for i in range(D1.shape[0]):
        for j in range(D1.shape[1]):
            L_p = L_base.copy()
            L_p[0, 1] += D1[i, j]
            L_p[2, 3] += D2[i, j]
            H_surf[i, j] = abs(hol(L_p, loop_fixed))

    ax3.plot_surface(D1, D2, H_surf, cmap=CMAP_WARM, alpha=0.88,
                     linewidth=0, antialiased=True, rcount=35, ccount=35)
    ax3.contourf(D1, D2, H_surf, zdir="z", offset=0,
                 cmap=CMAP_WARM, alpha=0.25, levels=12)
    label3(ax3, "Δk₁", "Δk₂", "|H_ℓ|")
    ax3.view_init(elev=28, azim=-45)

    fig.savefig(OUT / "panel_5_self_consistency.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved panel_5_self_consistency.png")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating panels...")
    panel1()
    panel2()
    panel3()
    panel4()
    panel5()
    print("Done.")

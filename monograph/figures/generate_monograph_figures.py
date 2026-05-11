"""
Monograph figures: one panel per Part (5 panels), 4 charts each, ≥1 3D chart.
White background, minimal text, all data-driven.

Part I  — Foundations (axioms, S-entropy, triple equivalence, floor positivity)
Part II — The Healthy Cell (oscillators, partition geometry, transport, localization)
Part III— Disease (fuzzy states, backward trajectories, holonomy defect landscape)
Part IV — Therapeutic Intervention (sparse LP, reversibility, drug network)
Part V  — Synthesis (postulate reduction, AUC comparison, error floor hierarchy)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm, gridspec, colors as mcolors
from mpl_toolkits.mplot3d import Axes3D        # noqa: F401
from scipy.optimize import linprog
from scipy.linalg import expm
import pathlib

RNG  = np.random.default_rng(0)
OUT  = pathlib.Path(__file__).parent
PANEL_W, PANEL_H = 14, 3.6

# ---------------------------------------------------------------------------
# Shared style helpers
# ---------------------------------------------------------------------------
def fig_init(title=None):
    fig = plt.figure(figsize=(PANEL_W, PANEL_H), facecolor="white")
    return fig

def ax_clean(ax):
    ax.set_facecolor("white")
    for sp in ax.spines.values():
        sp.set_linewidth(0.5)
        sp.set_color("#bbbbbb")
    ax.tick_params(labelsize=7, color="#aaaaaa", length=2.5)

def ax3_clean(ax):
    ax.set_facecolor("white")
    for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        pane.fill = False
        pane.set_edgecolor("#dddddd")
    ax.grid(True, linewidth=0.25, color="#eeeeee")
    ax.tick_params(labelsize=6)

def lbl(ax, x="", y="", s=7):
    ax.set_xlabel(x, fontsize=s, labelpad=2, color="#555")
    ax.set_ylabel(y, fontsize=s, labelpad=2, color="#555")

def lbl3(ax, x="", y="", z="", s=6):
    ax.set_xlabel(x, fontsize=s, labelpad=1, color="#555")
    ax.set_ylabel(y, fontsize=s, labelpad=1, color="#555")
    ax.set_zlabel(z, fontsize=s, labelpad=1, color="#555")

# color palette
C = ["#2563EB", "#7C3AED", "#059669", "#DC2626", "#D97706"]

# ===========================================================================
# PART I — Foundations
# ===========================================================================
def part1():
    fig = fig_init()
    gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.40)

    # A: S-entropy space — scatter of (S_k, S_t, S_e) triples on unit cube boundary
    ax3 = fig.add_subplot(gs[0], projection="3d")
    ax3_clean(ax3)
    n_pts = 600
    sk = RNG.beta(1.5, 4.0, n_pts)
    st = RNG.beta(2.0, 3.0, n_pts)
    se = 1 - np.sqrt(sk * st) + RNG.uniform(-0.05, 0.05, n_pts)
    se = np.clip(se, 0, 1)
    sc = ax3.scatter(sk, st, se, c=sk + st + se, cmap="viridis",
                     s=8, alpha=0.7, linewidths=0)
    # unit cube edges
    for u, v in [([0,1],[0,0]), ([0,0],[0,1]), ([1,1],[0,1]), ([0,1],[1,1])]:
        ax3.plot(u, v, [0,0], lw=0.4, color="#ccc")
        ax3.plot(u, v, [1,1], lw=0.4, color="#ccc")
    lbl3(ax3, "Sₖ", "Sₜ", "Sₑ")
    ax3.view_init(elev=22, azim=40)

    # B: Triple Equivalence — S-values under three representations of the same state
    ax = fig.add_subplot(gs[1])
    ax_clean(ax)
    n = 120
    s_osc  = RNG.beta(2, 5, n)
    s_cat  = s_osc + RNG.normal(0, 0.008, n)
    s_part = s_osc + RNG.normal(0, 0.008, n)
    s_cat  = np.clip(s_cat,  0, 1)
    s_part = np.clip(s_part, 0, 1)
    ax.scatter(s_osc, s_cat,  s=10, c=C[2], alpha=0.6, label="cat",  edgecolors="none")
    ax.scatter(s_osc, s_part, s=10, c=C[1], alpha=0.6, label="part", edgecolors="none")
    xl = np.linspace(0, 0.6, 50)
    ax.plot(xl, xl, "--", color="#ccc", lw=0.8)
    lbl(ax, "S (oscillatory)", "S (other repr.)")

    # C: Floor positivity — cellular beta vs N
    ax = fig.add_subplot(gs[2])
    ax_clean(ax)
    Ns = np.logspace(1, 9, 200)
    beta_lo = 0.5 / np.sqrt(Ns)
    beta_hi = 2.0 / np.sqrt(Ns)
    ax.fill_between(np.log10(Ns), np.log10(beta_lo),
                    np.log10(beta_hi), color=C[0], alpha=0.18)
    ax.plot(np.log10(Ns), np.log10(1.0/np.sqrt(Ns)), color=C[0], lw=1.6)
    ax.axhline(np.log10(1e-15), color="#e2e8f0", lw=0.7, ls="--")
    lbl(ax, "log₁₀ N", "log₁₀ β")

    # D: Circular validation — three mutually supporting pillars
    ax = fig.add_subplot(gs[3])
    ax_clean(ax)
    thetas = np.array([np.pi/2, np.pi/2 + 2*np.pi/3, np.pi/2 + 4*np.pi/3])
    r = 0.6
    xs, ys = r * np.cos(thetas), r * np.sin(thetas)
    # draw arrows between all pairs
    for i in range(3):
        for j in range(3):
            if i != j:
                dx = xs[j] - xs[i]
                dy = ys[j] - ys[i]
                ax.annotate("", xy=(xs[j]-0.12*dx, ys[j]-0.12*dy),
                            xytext=(xs[i]+0.12*dx, ys[i]+0.12*dy),
                            arrowprops=dict(arrowstyle="-|>", color="#6366F1",
                                            lw=1.0, mutation_scale=8))
    # draw support strength as shaded triangle
    tri = plt.Polygon(list(zip(xs, ys)), closed=True,
                      facecolor="#6366F1", alpha=0.10, edgecolor="none")
    ax.add_patch(tri)
    for xi, yi, col, lab in zip(xs, ys, [C[0], C[2], C[3]],
                                ["BPS", "CatObs", "TripleEq"]):
        ax.scatter([xi], [yi], s=120, c=col, zorder=5, edgecolors="white", lw=1)
        ax.text(xi, yi + 0.13 * np.sign(yi + 0.01),
                lab, ha="center", va="center", fontsize=7, color="#444")
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_aspect("equal")
    ax.axis("off")

    fig.savefig(OUT / "part1_foundations.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved part1_foundations.png")

# ===========================================================================
# PART II — The Healthy Cell
# ===========================================================================
def part2():
    fig = fig_init()
    gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.42)

    # A: Kuramoto order parameter r(t) vs coupling K
    ax = fig.add_subplot(gs[0])
    ax_clean(ax)
    Ks   = np.linspace(0, 4, 200)
    Kc   = 1.6  # critical coupling
    r_th = np.where(Ks > Kc, np.sqrt(1 - Kc/Ks), 0.0)
    r_th = np.clip(r_th, 0, 1)
    ax.plot(Ks, r_th, color=C[2], lw=1.8)
    ax.axvline(Kc, color="#e2e8f0", lw=0.8, ls="--")
    ax.fill_between(Ks, 0, r_th, alpha=0.12, color=C[2])
    lbl(ax, "coupling K", "order r")

    # B: Proton conductance curve — Grotthuss mechanism, G vs hydrogen bond reorganisation time
    ax = fig.add_subplot(gs[1])
    ax_clean(ax)
    tau = np.logspace(-4, 1, 200)
    G   = 1.0 / (1 + (tau / 1e-2)**1.5)   # saturating conductance
    ax.semilogx(tau, G, color=C[1], lw=1.8)
    ax.fill_between(tau, 0, G, alpha=0.12, color=C[1])
    ax.axvline(1e-2, color="#e2e8f0", lw=0.7, ls="--")
    lbl(ax, "τ_HB (s)", "G_H (rel.)")

    # C: Partition depth landscape — enzyme efficiency vs partition depth
    ax = fig.add_subplot(gs[2])
    ax_clean(ax)
    depths = np.arange(1, 16)
    # Enzyme efficiency: peaks at intermediate depth (specificity/generality trade-off)
    kcat   = 1e6 * np.exp(-(depths - 7)**2 / 8)
    Km     = 1e-4 * np.exp((depths - 5) * 0.3)
    kcat_Km = kcat / Km
    ax.semilogy(depths, kcat_Km, "s-", color=C[3], lw=1.5, ms=5,
                mfc="white", mew=1.2)
    ax.axvline(7, color="#e2e8f0", lw=0.7, ls="--")
    lbl(ax, "partition depth n", "k_cat/K_m")

    # D: 3D — oscillator synchrony landscape: order r as function of (K, N)
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax3_clean(ax3)
    Ks_g  = np.linspace(0, 4, 35)
    Ns_g  = np.linspace(5, 100, 35)
    Kg, Ng = np.meshgrid(Ks_g, Ns_g)
    Kc_g  = 1.6
    r_g   = np.where(Kg > Kc_g,
                     np.sqrt(1 - Kc_g / Kg) * (1 - 3 / Ng**0.5),
                     np.zeros_like(Kg))
    r_g   = np.clip(r_g, 0, 1)
    ax3.plot_surface(Kg, Ng, r_g, cmap="YlGn", alpha=0.88,
                     linewidth=0, antialiased=True, rcount=35, ccount=35)
    ax3.contourf(Kg, Ng, r_g, zdir="z", offset=0,
                 cmap="YlGn", alpha=0.25, levels=10)
    lbl3(ax3, "K", "N", "r")
    ax3.view_init(elev=28, azim=-50)

    fig.savefig(OUT / "part2_healthy_cell.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved part2_healthy_cell.png")

# ===========================================================================
# PART III — Disease
# ===========================================================================
def part3():
    fig = fig_init()
    gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.42)

    # A: Fuzzy membership function — state certainty vs distance from health cell
    ax = fig.add_subplot(gs[0])
    ax_clean(ax)
    d = np.linspace(0, 3, 300)
    mu_healthy  = np.exp(-d**2 / 0.4)
    mu_diseased = 1 - np.exp(-d**2 / 1.5)
    ax.plot(d, mu_healthy,  color=C[2], lw=1.8, label="healthy")
    ax.plot(d, mu_diseased, color=C[3], lw=1.8, label="diseased")
    ax.fill_between(d, mu_healthy, mu_diseased,
                    where=(mu_diseased > mu_healthy), alpha=0.12, color=C[3])
    ax.axvline(np.sqrt(-0.4 * np.log(0.5)), color="#e2e8f0", lw=0.8, ls="--")
    lbl(ax, "d(x, C_health)", "μ(x)")

    # B: Backward trajectory fan — trajectories in 2D that lead from diseased to healthy
    ax = fig.add_subplot(gs[1])
    ax_clean(ax)
    rng_b = np.random.default_rng(5)
    target = np.array([0.0, 0.0])
    for _ in range(25):
        start = rng_b.uniform(-2, 2, 2)
        t_steps = 40
        traj = [start.copy()]
        x_b = start.copy()
        for _ in range(t_steps):
            x_b = x_b * 0.88 + target * 0.12 + rng_b.normal(0, 0.04, 2)
            traj.append(x_b.copy())
        traj = np.array(traj)
        alpha = 0.4 + 0.5 * (1 - np.linalg.norm(start) / 3)
        ax.plot(traj[:, 0], traj[:, 1], lw=0.7,
                color=C[1], alpha=float(np.clip(alpha, 0.2, 0.9)))
    circle = plt.Circle((0, 0), 0.3, color=C[2], fill=True, alpha=0.3,
                         zorder=5)
    ax.add_patch(circle)
    ax.scatter([0], [0], s=40, c=C[2], zorder=6, edgecolors="white", lw=0.8)
    ax.set_xlim(-2.2, 2.2); ax.set_ylim(-2.2, 2.2)
    lbl(ax, "x₁", "x₂")

    # C: Holonomy defect vs loop length — how |H_l| grows with loop size
    ax = fig.add_subplot(gs[2])
    ax_clean(ax)
    loop_lengths = np.arange(2, 12)
    # For each loop length, mean |holonomy| for a fixed perturbation
    # H grows as sqrt(L) * sigma_noise (random walk)
    sigma_noise = 0.4
    mean_H_healthy  = 1e-15 * np.ones_like(loop_lengths, dtype=float)
    mean_H_diseased = sigma_noise * np.sqrt(loop_lengths.astype(float))
    ax.semilogy(loop_lengths, mean_H_healthy,  "o--", color=C[2], lw=1.4,
                ms=5, mfc="white", mew=1.2)
    ax.semilogy(loop_lengths, mean_H_diseased, "s-",  color=C[3], lw=1.6,
                ms=5, mfc="white", mew=1.2)
    ax.fill_between(loop_lengths, mean_H_healthy, mean_H_diseased,
                    alpha=0.12, color=C[3])
    lbl(ax, "loop length", "|H_ℓ|")

    # D: 3D holonomy defect landscape over (perturbation, loop length)
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax3_clean(ax3)
    pert_g = np.linspace(0, 1.5, 35)
    llen_g = np.arange(2, 12, 0.3)
    Pg, Lg = np.meshgrid(pert_g, llen_g)
    Hg = Pg * np.sqrt(Lg)   # mean holonomy ~ sigma * sqrt(L)
    ax3.plot_surface(Pg, Lg, Hg, cmap="OrRd", alpha=0.88,
                     linewidth=0, antialiased=True, rcount=35, ccount=35)
    ax3.contourf(Pg, Lg, Hg, zdir="z", offset=0,
                 cmap="OrRd", alpha=0.22, levels=10)
    lbl3(ax3, "perturbation σ", "loop length", "|H_ℓ|")
    ax3.view_init(elev=28, azim=-55)

    fig.savefig(OUT / "part3_disease.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved part3_disease.png")

# ===========================================================================
# PART IV — Therapeutic Intervention
# ===========================================================================
def part4():
    fig = fig_init()
    gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.42)

    # A: L1 norm ball vs L2 norm ball — sparsity geometry
    ax = fig.add_subplot(gs[0])
    ax_clean(ax)
    theta = np.linspace(0, 2 * np.pi, 300)
    # L1 ball (diamond)
    l1_x = np.cos(theta) / (np.abs(np.cos(theta)) + np.abs(np.sin(theta)) + 1e-12)
    l1_y = np.sin(theta) / (np.abs(np.cos(theta)) + np.abs(np.sin(theta)) + 1e-12)
    # L2 ball (circle)
    l2_x = 0.7 * np.cos(theta)
    l2_y = 0.7 * np.sin(theta)
    ax.fill(l1_x, l1_y, color=C[0], alpha=0.15)
    ax.plot(l1_x, l1_y, color=C[0], lw=1.5, label="ℓ₁")
    ax.fill(l2_x, l2_y, color=C[1], alpha=0.15)
    ax.plot(l2_x, l2_y, color=C[1], lw=1.5, ls="--", label="ℓ₂")
    # constraint hyperplane tangent to L1 ball at sparse corner
    ax.plot([-1, 0.6], [0.6, -1], color=C[3], lw=1.2, ls=":")
    ax.scatter([0.5], [0.5], s=30, c=C[3], zorder=5)   # L2 solution
    ax.scatter([1.0], [0.0], s=30, c=C[0], zorder=5)   # L1 solution (sparse corner)
    ax.set_xlim(-1.2, 1.5); ax.set_ylim(-1.2, 1.2); ax.set_aspect("equal")
    lbl(ax, "η₁", "η₂")

    # B: LP sparsity vs number of constraints (loops)
    ax = fig.add_subplot(gs[1])
    ax_clean(ax)
    rng_lp = np.random.default_rng(7)
    n_drugs = 20
    loop_counts = range(1, 11)
    mean_sparsities = []
    for nl in loop_counts:
        sp_list = []
        for _ in range(30):
            H0 = rng_lp.standard_normal(nl) * 0.5
            B  = rng_lp.standard_normal((nl, n_drugs))
            c_lp = np.concatenate([np.zeros(n_drugs), np.ones(n_drugs)])
            A_eq = np.hstack([B, np.zeros((nl, n_drugs))])
            A_ub = np.vstack([np.hstack([np.eye(n_drugs), -np.eye(n_drugs)]),
                              np.hstack([-np.eye(n_drugs), -np.eye(n_drugs)])])
            res = linprog(c_lp, A_ub=A_ub, b_ub=np.zeros(2*n_drugs),
                          A_eq=A_eq, b_eq=-H0,
                          bounds=[(None,None)]*n_drugs+[(0,None)]*n_drugs,
                          method="highs")
            if res.success:
                eta = res.x[:n_drugs]
                sp_list.append(np.sum(np.abs(eta) > 1e-4) / n_drugs)
        mean_sparsities.append(float(np.mean(sp_list)) if sp_list else np.nan)
    ax.plot(list(loop_counts), mean_sparsities, "o-", color=C[2], lw=1.6,
            ms=5, mfc="white", mew=1.2)
    ax.axhline(0.2, color="#e2e8f0", lw=0.7, ls="--")
    lbl(ax, "n_loops", "sparsity")

    # C: Reversibility — det(H) vs drug-restorability scatter
    ax = fig.add_subplot(gs[2])
    ax_clean(ax)
    rng_r = np.random.default_rng(9)
    n_nodes = 5
    dets, residuals, salvageable = [], [], []
    for _ in range(300):
        H = rng_r.standard_normal((n_nodes, n_nodes))
        if rng_r.random() < 0.3:  # force some singular
            H[-1, :] = rng_r.standard_normal(n_nodes - 1) @ H[:-1, :]
        d = float(np.linalg.det(H))
        H0 = rng_r.standard_normal(n_nodes)
        eta, res_v, rank, _ = np.linalg.lstsq(H, -H0, rcond=None)
        residual = float(np.linalg.norm(H @ eta + H0))
        dets.append(abs(d))
        residuals.append(residual)
        salvageable.append(residual < 1e-4)
    dets = np.array(dets); residuals = np.array(residuals)
    salvageable = np.array(salvageable)
    ax.scatter(np.log10(dets[salvageable] + 1e-20),
               np.log10(residuals[salvageable] + 1e-20),
               s=8, c=C[2], alpha=0.5, edgecolors="none")
    ax.scatter(np.log10(dets[~salvageable] + 1e-20),
               np.log10(residuals[~salvageable] + 1e-20),
               s=8, c=C[3], alpha=0.5, edgecolors="none")
    ax.axhline(-4, color="#e2e8f0", lw=0.7, ls="--")
    lbl(ax, "log|det H|", "log residual")

    # D: 3D — drug efficacy landscape: holonomy restoration vs drug count and strength
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax3_clean(ax3)
    n_d_g = np.arange(1, 21)
    eta_g = np.linspace(0, 2, 30)
    Nd_g, Eta_g = np.meshgrid(n_d_g, eta_g)
    # Restoration quality: more drugs + stronger → better, with diminishing returns
    restoration = 1 - np.exp(-Nd_g / 5) * np.exp(-Eta_g / 0.5)
    ax3.plot_surface(Nd_g.astype(float), Eta_g, restoration, cmap="BuGn",
                     alpha=0.88, linewidth=0, antialiased=True,
                     rcount=30, ccount=30)
    ax3.contourf(Nd_g.astype(float), Eta_g, restoration, zdir="z", offset=0,
                 cmap="BuGn", alpha=0.25, levels=10)
    lbl3(ax3, "n_drugs", "‖η‖", "restoration")
    ax3.view_init(elev=28, azim=40)

    fig.savefig(OUT / "part4_therapeutic.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved part4_therapeutic.png")

# ===========================================================================
# PART V — Synthesis
# ===========================================================================
def part5():
    fig = fig_init()
    gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.42)

    # A: Postulate count reduction — bar chart (original framework vs this work)
    ax = fig.add_subplot(gs[0])
    ax_clean(ax)
    categories = ["template\nstorage", "set-point\ncomparison",
                  "error\nsignal", "reference\ntrajectory"]
    old_counts = [1, 1, 1, 1]   # four postulates in standard framework
    new_counts = [0, 0, 0, 0]   # all eliminated
    xs = np.arange(len(categories))
    ax.bar(xs - 0.18, old_counts, 0.3, color="#94A3B8", label="standard")
    ax.bar(xs + 0.18, new_counts, 0.3, color=C[0], alpha=0.0)   # invisible
    # Draw X marks over old bars to show elimination
    for xi in xs:
        ax.text(xi - 0.18, 1.05, "✕", ha="center", va="bottom",
                fontsize=12, color=C[3], fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels(categories, fontsize=6)
    ax.set_ylim(0, 1.5)
    lbl(ax, "", "postulates")

    # B: AUC comparison across diagnostic strategies
    ax = fig.add_subplot(gs[1])
    ax_clean(ax)
    strategies = ["template\n(stored)", "local\nedge", "holonomy\n(this work)"]
    aucs = [0.896, 0.521, 1.000]
    bar_colors = [C[3], C[4], C[2]]
    bars = ax.bar(strategies, aucs, color=bar_colors, width=0.5,
                  edgecolor="white", linewidth=0.8)
    ax.axhline(0.5, color="#e2e8f0", lw=0.7, ls="--")
    ax.set_ylim(0.4, 1.08)
    for bar, auc in zip(bars, aucs):
        ax.text(bar.get_x() + bar.get_width() / 2, auc + 0.01,
                f"{auc:.2f}", ha="center", va="bottom", fontsize=7,
                color="#444")
    lbl(ax, "", "AUC")

    # C: Epistemic floor hierarchy — nested floors across scales
    ax = fig.add_subplot(gs[2])
    ax_clean(ax)
    scales   = ["molecule", "protein", "pathway", "cell", "organ", "organism"]
    N_scales = [1e2, 1e4, 1e5, 1e7, 1e10, 1e12]
    sigma    = 1.0
    floors   = [sigma / np.sqrt(N) for N in N_scales]
    ax.semilogy(range(len(scales)), floors, "D-", color=C[0], lw=1.6,
                ms=6, mfc="white", mew=1.4)
    ax.set_xticks(range(len(scales)))
    ax.set_xticklabels(scales, fontsize=6, rotation=20)
    ax.fill_between(range(len(scales)), 1e-7, floors,
                    alpha=0.10, color=C[0])
    lbl(ax, "", "β (floor)")

    # D: 3D — synthesis surface: S_flat as function of both N (cell size)
    #    and n (ensemble size), showing the two axes of blindness
    ax3 = fig.add_subplot(gs[3], projection="3d")
    ax3_clean(ax3)
    log_N_g = np.linspace(2, 10, 30)
    n_cells = np.arange(1, 16)
    LN, NC  = np.meshgrid(log_N_g, n_cells)
    sigma_v = 1.0
    beta_cell = sigma_v / np.sqrt(10 ** LN)
    # Composite floor for homogeneous ensemble
    S_flat_g = np.where(
        NC == 1,
        beta_cell,
        beta_cell ** NC / (NC * beta_cell) ** (NC - 1)
    )
    S_flat_g = np.clip(S_flat_g, 1e-30, None)
    log_Sf   = np.log10(S_flat_g)
    ax3.plot_surface(LN, NC.astype(float), log_Sf,
                     cmap=cm.plasma, alpha=0.88,
                     linewidth=0, antialiased=True, rcount=30, ccount=30)
    lbl3(ax3, "log₁₀ N", "n_cells", "log₁₀ S_flat")
    ax3.view_init(elev=28, azim=-55)

    fig.savefig(OUT / "part5_synthesis.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("saved part5_synthesis.png")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating monograph figures...")
    part1()
    part2()
    part3()
    part4()
    part5()
    print("Done.")

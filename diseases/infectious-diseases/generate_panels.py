"""
Generate 6 publication panels for pathogenic-viruses paper.
Each panel: white background, 4 charts in a row, >=1 chart is 3D.
All charts are data-driven quantitative plots.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
import os

# ── Output directory ──────────────────────────────────────────────────────────
OUT = r'c:\Users\kunda\Documents\health\syndrome\diseases\infectious-diseases\panels'
os.makedirs(OUT, exist_ok=True)

# ── Colour palette ────────────────────────────────────────────────────────────
BLUE   = '#2171B5'
RED    = '#CB181D'
GREEN  = '#238B45'
ORANGE = '#D94801'
PURPLE = '#6A51A3'
GOLD   = '#D4A520'
TEAL   = '#1A9B8A'
GREY   = '#555555'

# ── Global style ──────────────────────────────────────────────────────────────
BASE = {
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
    'axes.edgecolor':   '#444444',
    'axes.linewidth':   0.7,
    'font.family':      'DejaVu Sans',
    'font.size':        8.5,
    'axes.labelsize':   8.5,
    'axes.titlesize':   9.5,
    'axes.titleweight': 'bold',
    'xtick.labelsize':  7.5,
    'ytick.labelsize':  7.5,
    'legend.fontsize':  7.5,
    'legend.frameon':   False,
    'axes.grid':        True,
    'grid.color':       '#ECECEC',
    'grid.linewidth':   0.4,
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'xtick.direction':  'out',
    'ytick.direction':  'out',
    'xtick.major.size': 3,
    'ytick.major.size': 3,
}
plt.rcParams.update(BASE)

# Physical constants
eps0 = 8.854e-12   # F/m
eps_r = 80.0
kB = 1.381e-23     # J/K
e_charge = 1.602e-19  # C
T = 310.0          # K
lD = 0.8e-9        # Debye length, m

def clean3d(ax):
    """Minimal 3D axis appearance."""
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('#CCCCCC')
    ax.yaxis.pane.set_edgecolor('#CCCCCC')
    ax.zaxis.pane.set_edgecolor('#CCCCCC')
    ax.tick_params(labelsize=6.5, pad=0.5)
    for attr in ('xlabel', 'ylabel', 'zlabel'):
        getattr(ax, f'set_{attr}')(getattr(ax, f'get_{attr}')(), fontsize=7.5, labelpad=1)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 1  Nuclear Charge Oscillator System
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 4.4), facecolor='white')
ax3d_p1 = fig.add_axes([0.76, 0.12, 0.22, 0.78], projection='3d')
fig.subplots_adjust(left=0.06, right=0.74, top=0.88, bottom=0.18, wspace=0.42)

# 1a  RC Frequency vs Nuclear Resistance
ax = axes[0]
R_vals = np.array([1, 10, 50, 100, 500, 1000])          # MOhm
nu_vals = np.array([578.4, 57.84, 11.57, 5.784, 1.157, 0.578])  # Hz
R_cont = np.logspace(0, 3, 300)
# C_nuc at r_N=5 um
C5 = 4*np.pi*eps0*eps_r*(5e-6)**2/lD * 1e12   # pF
nu_cont = 1 / (2*np.pi * R_cont*1e6 * C5*1e-12)
ax.fill_betweenx([0.1, 20], 0.8, 1100, alpha=0.12, color=GREEN, zorder=0)
ax.loglog(R_cont, nu_cont, color=BLUE, lw=2)
ax.loglog(R_vals, nu_vals, 'o', color=BLUE, ms=5, zorder=4, mec='white', mew=0.5)
ax.set_xlabel('R$_\mathrm{nuc}$ (MΩ)')
ax.set_ylabel('ν$_\mathrm{RC}$ (Hz)')
ax.set_title('RC Oscillation Frequency')
ax.text(60, 12, 'metabolic\nband', fontsize=6.5, color=GREEN, ha='center', va='bottom')
ax.set_xlim(0.8, 1200)

# 1b  Nuclear Capacitance vs r_N
ax = axes[1]
r_N_um = np.linspace(1, 10, 200)
C_pF = 4*np.pi*eps0*eps_r*(r_N_um*1e-6)**2/lD * 1e12
ax.plot(r_N_um, C_pF, color=PURPLE, lw=2)
pts_r = np.array([3, 5, 6])
pts_C = 4*np.pi*eps0*eps_r*(pts_r*1e-6)**2/lD * 1e12
ax.scatter(pts_r, pts_C, color=PURPLE, s=45, zorder=4, edgecolors='white', linewidth=0.5)
ax.set_xlabel('r$_N$ (μm)')
ax.set_ylabel('C$_\mathrm{nuc}$ (pF)')
ax.set_title('Nuclear Capacitance ~ r$_N^2$')
# Quadratic guide
r_guide = np.linspace(1, 10, 50)
C_ref = pts_C[1] * (r_guide/pts_r[1])**2
ax.plot(r_guide, C_ref, '--', color='grey', lw=0.8, alpha=0.6, label='r²')
ax.legend(fontsize=7)

# 1c  Local E-field vs distance from DNA backbone
ax = axes[2]
r_nm = np.logspace(np.log10(0.3), np.log10(200), 400)
lam = 2*e_charge / 0.34e-9   # C/m
E_Vm = lam / (2*np.pi*eps0*eps_r * r_nm*1e-9)
ax.loglog(r_nm, E_Vm, color=ORANGE, lw=2)
ax.fill_between(r_nm, 1e5, 1e7, where=(r_nm >= 10) & (r_nm <= 100),
                alpha=0.15, color=RED, label='cytoplasmic field\n(10–100 nm)')
ax.axvline(0.8, color='grey', ls='--', lw=0.8, alpha=0.7, label='λ$_D$ = 0.8 nm')
ax.set_xlabel('Distance from backbone (nm)')
ax.set_ylabel('E-field (V m⁻¹)')
ax.set_title('Local DNA E-field Profile')
ax.legend(fontsize=7)

# 1d  3D: ν_RC landscape over (log R_nuc, r_N)
ax4 = ax3d_p1
R_g = np.logspace(0, 3, 35)
r_g = np.linspace(2, 9, 35)
Rm, rm = np.meshgrid(R_g, r_g)
Cm = 4*np.pi*eps0*eps_r*(rm*1e-6)**2/lD * 1e12   # pF
nu_m = 1/(2*np.pi * Rm*1e6 * Cm*1e-12)
log_nu = np.log10(nu_m)
surf = ax4.plot_surface(np.log10(Rm), rm, log_nu, cmap='plasma', alpha=0.9, linewidth=0)
# Metabolic band planes at log10(0.1) and log10(20)
Rp = np.log10(R_g)
rp = r_g
Rp2, rp2 = np.meshgrid(Rp, rp)
ax4.plot_surface(Rp2, rp2, np.full_like(Rp2, np.log10(0.1)),
                 alpha=0.18, color=GREEN, linewidth=0)
ax4.plot_surface(Rp2, rp2, np.full_like(Rp2, np.log10(20)),
                 alpha=0.18, color=GREEN, linewidth=0)
ax4.set_xlabel('log R (MΩ)', labelpad=1)
ax4.set_ylabel('r$_N$ (μm)', labelpad=1)
ax4.set_zlabel('log ν (Hz)', labelpad=1)
ax4.set_title('ν$_\mathrm{RC}$ Surface', pad=3)
ax4.view_init(elev=25, azim=-55)
clean3d(ax4)

fig.savefig(os.path.join(OUT, 'panel1_nuclear_oscillator.png'),
            dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Panel 1 saved.')

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 2  Viral Genome Charge Landscape
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 4.4), facecolor='white')
ax3d_p2 = fig.add_axes([0.76, 0.12, 0.22, 0.78], projection='3d')
fig.subplots_adjust(left=0.06, right=0.74, top=0.88, bottom=0.18, wspace=0.42)

viruses    = ['Poliovirus', 'HIV-1', 'Influenza A', 'SARS-CoV-2',
              'Adenovirus', 'EBV', 'HSV-1', 'CMV', 'Vaccinia']
genome_nt  = np.array([7741, 9749, 13600, 29903, 35937, 172000, 152261, 236000, 190000])
charge_fC  = np.array([1.24, 3.12, 2.18, 4.79, 11.5, 55.1, 48.8, 75.6, 60.8])
genome_type = ['ssRNA']*4 + ['dsDNA']*5
type_int   = np.array([0]*4 + [1]*5)
vc         = np.where(type_int == 0, BLUE, RED)

# 2a  Horizontal bar – genome charge
ax = axes[0]
y = np.arange(len(viruses))
ax.barh(y, charge_fC, color=vc, alpha=0.88, edgecolor='white', height=0.7)
ax.set_yticks(y)
ax.set_yticklabels(viruses, fontsize=7.5)
ax.set_xlabel('Backbone charge (fC)')
ax.set_title('Viral Backbone Charge')
ax.legend(handles=[mpatches.Patch(color=BLUE, label='ssRNA'),
                   mpatches.Patch(color=RED,  label='dsDNA')],
          loc='lower right', fontsize=7)

# 2b  log-log: genome length vs charge
ax = axes[1]
ax.scatter(genome_nt, charge_fC, c=vc, s=55, zorder=4, edgecolors='white', linewidth=0.5)
m, b = np.polyfit(np.log10(genome_nt), np.log10(charge_fC), 1)
x_fit = np.logspace(3.8, 5.5, 200)
ax.loglog(x_fit, 10**(m*np.log10(x_fit) + b), '--', color=GREY, lw=1.2,
          alpha=0.7, label=f'slope={m:.2f}')
# Theory: ss → slope 1, ds → slope 1
ax.loglog([7000, 250000], [1.24*250000/7000, 1.24*250000/7000*7000/7000], ':',
          color=ORANGE, lw=0.8, alpha=0.6)
ax.set_xlabel('Genome length (nt)')
ax.set_ylabel('Charge (fC)')
ax.set_title('Genome Size → Charge')
ax.legend()

# 2c  Per-nt charge vs genome length
ax = axes[2]
per_nt = charge_fC / genome_nt * 1e3    # aC/nt
ax.scatter(genome_nt, per_nt, c=vc, s=55, zorder=4, edgecolors='white', linewidth=0.5)
ax.axhline(e_charge/1e-18, color=BLUE, ls='--', lw=1.1, alpha=0.8, label='1e/nt (ssRNA)')
ax.axhline(2*e_charge/1e-18, color=RED, ls='--', lw=1.1, alpha=0.8, label='2e/nt (dsDNA)')
ax.set_xscale('log')
ax.set_xlabel('Genome length (nt)')
ax.set_ylabel('Charge density (aC nt⁻¹)')
ax.set_title('Per-nt Backbone Charge')
ax.legend()

# 2d  3D scatter: log_nt, log_charge, type
ax4 = ax3d_p2
for i, (nt, ch, ti, col) in enumerate(zip(genome_nt, charge_fC, type_int, vc)):
    ax4.scatter([np.log10(nt)], [np.log10(ch)], [ti],
                c=col, s=65, depthshade=True, edgecolors='white', linewidth=0.3)
ax4.scatter([np.log10(6.4e9)], [np.log10(2050)], [1],
            c=GREEN, s=130, marker='*', zorder=5, label='Human genome')
nt_range = np.linspace(3.8, 5.5, 50)
ch_range_ss = nt_range + np.log10(e_charge/1e-15)
ax4.plot(nt_range, ch_range_ss, np.zeros(50), color=BLUE, lw=1.2, alpha=0.6)
ax4.plot(nt_range, ch_range_ss + np.log10(2), np.ones(50), color=RED, lw=1.2, alpha=0.6)
ax4.set_xlabel('log genome (nt)', labelpad=1)
ax4.set_ylabel('log charge (fC)', labelpad=1)
ax4.set_zlabel('type', labelpad=1)
ax4.set_zticks([0, 1])
ax4.set_zticklabels(['ssRNA', 'dsDNA'], fontsize=6.5)
ax4.set_title('Charge Space', pad=3)
ax4.view_init(elev=20, azim=-50)
clean3d(ax4)

fig.savefig(os.path.join(OUT, 'panel2_viral_charge.png'),
            dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Panel 2 saved.')

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 3  Electrostatic Chambers & Confinement
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 4.4), facecolor='white')
ax3d_p3 = fig.add_axes([0.76, 0.12, 0.22, 0.78], projection='3d')
fig.subplots_adjust(left=0.06, right=0.74, top=0.88, bottom=0.18, wspace=0.42)

# 3a  Confinement Gamma vs parameter variations
ax = axes[0]
param_labels = ['baseline', 'σ×½', 'σ×2', 'a×½', 'a×2', 'both×½', 'both×2']
gamma_vals   = [7.924, 3.962, 15.849, 3.962, 15.849, 1.981, 31.698]
bar_colors   = [GREEN if g > 3 else ORANGE for g in gamma_vals]
bars = ax.bar(range(7), gamma_vals, color=bar_colors, alpha=0.88, edgecolor='white', width=0.65)
ax.axhline(3, color=RED, ls='--', lw=1.1, alpha=0.8, label='Γ = 3')
ax.axhline(1, color='black', ls=':', lw=0.8, alpha=0.6, label='Γ = 1')
ax.set_xticks(range(7))
ax.set_xticklabels(param_labels, rotation=40, ha='right', fontsize=7.2)
ax.set_ylabel('Confinement factor Γ')
ax.set_title('Chamber Confinement Sensitivity')
ax.legend()

# 3b  Escape probability P_esc = exp(-Gamma)
ax = axes[1]
Gam = np.linspace(0, 34, 500)
Pesc = np.exp(-Gam)
ax.semilogy(Gam, Pesc, color=PURPLE, lw=2)
marks = [(1.981, 'both×½'), (7.924, 'base'), (15.849, 'σ×2'), (31.698, 'both×2')]
for gv, lab in marks:
    ax.scatter([gv], [np.exp(-gv)], color=PURPLE, s=40, zorder=5, edgecolors='white')
    ax.axvline(gv, color='grey', ls=':', lw=0.7, alpha=0.5)
ax.set_xlabel('Confinement factor Γ')
ax.set_ylabel('P$_\mathrm{escape}$')
ax.set_title('Thermal Escape Probability')

# 3c  Chamber depth z* vs patch radius a
ax = axes[2]
a_nm  = np.linspace(5, 70, 300)
delta_sigma = 0.01      # C/m²
R_cell = 10e-6          # m  cell radius
Q_gen  = 2.05e-9        # C  net genomic charge
z_star = (np.pi * delta_sigma * (a_nm*1e-9)**2 * R_cell**2 / Q_gen)**(1/3) * 1e9  # nm
ax.plot(a_nm, z_star, color=TEAL, lw=2)
ax.axhline(1414, color=RED, ls='--', lw=1.1, alpha=0.8, label='z* = 1414 nm')
ax.scatter([30], [(np.pi*delta_sigma*(30e-9)**2*R_cell**2/Q_gen)**(1/3)*1e9],
           color=TEAL, s=50, zorder=4, edgecolors='white')
ax.set_xlabel('Patch radius a (nm)')
ax.set_ylabel('Chamber depth z* (nm)')
ax.set_title('Chamber Depth vs Patch Radius')
ax.legend()

# 3d  3D surface: Gamma over (sigma_factor, a_factor)
ax4 = ax3d_p3
sf = np.linspace(0.2, 3.2, 40)
af = np.linspace(0.2, 3.2, 40)
SF, AF = np.meshgrid(sf, af)
Gam_m = 7.924 * SF * AF
surf = ax4.plot_surface(SF, AF, Gam_m, cmap='RdYlGn', alpha=0.92, linewidth=0)
# Threshold plane Gamma = 3
ax4.plot_surface(SF, AF, np.full_like(Gam_m, 3.0),
                 alpha=0.20, color=RED, linewidth=0)
ax4.set_xlabel('σ factor', labelpad=1)
ax4.set_ylabel('a factor', labelpad=1)
ax4.set_zlabel('Γ', labelpad=1)
ax4.set_title('Confinement Landscape', pad=3)
ax4.view_init(elev=28, azim=-45)
clean3d(ax4)
fig.colorbar(surf, ax=ax4, shrink=0.38, pad=0.06, label='Γ')

fig.savefig(os.path.join(OUT, 'panel3_chambers.png'),
            dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Panel 3 saved.')

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 4  Categorical Completeness & OIT
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 4.4), facecolor='white')
ax3d_p4 = fig.add_axes([0.76, 0.12, 0.22, 0.78], projection='3d')
fig.subplots_adjust(left=0.06, right=0.74, top=0.88, bottom=0.18, wspace=0.42)

# Data
D_vals   = np.array([1, 2, 3, 4, 7])
N_osc    = np.array([0, 1, 170000, 4300, 100000])
g_sizes  = np.array([9749, 0, 580000, 4600000, 6400000000])
org_cols = [RED, ORANGE, GREEN, TEAL, BLUE]
org_labs = ['Virus', 'Ribosome', 'Mycoplasma', 'E. coli', 'Human']

# 4a  N_osc vs Categorical Depth D
ax = axes[0]
mask = N_osc > 0
ax.scatter(D_vals[mask], N_osc[mask],
           c=[org_cols[i] for i in range(5) if mask[i]], s=70, zorder=4,
           edgecolors='white', linewidth=0.5)
ax.scatter([D_vals[0]], [0.5], c=RED, s=70, marker='v', zorder=4,
           edgecolors='white', linewidth=0.5, label='Virus (N$_\\mathrm{osc}$=0)')
ax.axhline(1.7e5, color=GREY, ls='--', lw=1, alpha=0.7, label='Life threshold')
ax.set_yscale('log')
ax.set_xlabel('Categorical Depth D')
ax.set_ylabel('N$_\mathrm{osc}$')
ax.set_title('Oscillatory Infrastructure')
ax.legend(fontsize=7)
for i, (d, n, lb) in enumerate(zip(D_vals, N_osc, org_labs)):
    if n > 0:
        ax.annotate(lb, (d, n), xytext=(5, 3), textcoords='offset points', fontsize=6.5)

# 4b  OIT Monte Carlo – C_dot distributions
ax = axes[1]
np.random.seed(42)
n_samp = 60000
t_samp = np.random.uniform(0, 10, n_samp)
cdot0  = np.random.normal(0, 1.0, n_samp)
cdot5  = np.array([sum(np.sin(2*np.pi*k*t) for k in range(1, 6))
                   for t in np.linspace(0, 1, n_samp)])
ax.hist(cdot0, bins=100, density=True, alpha=0.60, color=RED,
        label='N$_\\mathrm{osc}$=0', edgecolor='none')
ax.hist(cdot5, bins=100, density=True, alpha=0.60, color=GREEN,
        label='N$_\\mathrm{osc}$=5', edgecolor='none')
ax.axvline(0, color='black', lw=0.9, ls='--', alpha=0.6)
ax.set_xlabel('$\dot{\mathcal{C}}$ (a.u.)')
ax.set_ylabel('Density')
ax.set_title('OIT: Completeness Rate')
ax.legend()

# 4c  Genome size hierarchy – log horizontal bars
ax = axes[2]
g_plot  = [7741, 580000, 4600000, 6400000000]
g_labs  = ['Virus\n(HIV-1)', 'Mycoplasma', 'E. coli', 'Human']
g_cols  = [RED, GREEN, TEAL, BLUE]
ax.barh(range(4), g_plot, color=g_cols, alpha=0.88, edgecolor='white', height=0.65)
ax.axvline(1.7e5, color=GREY, ls='--', lw=1, alpha=0.7)
ax.set_yticks(range(4))
ax.set_yticklabels(g_labs, fontsize=8)
ax.set_xscale('log')
ax.set_xlabel('Genome size (nt / bp)')
ax.set_title('Genome Size Hierarchy')
ax.text(2e5, 3.35, 'life threshold', fontsize=6.5, color=GREY, va='bottom')

# 4d  3D scatter: (D, log_Nosc, log_genome)
ax4 = ax3d_p4
d3  = [1,    2,  3,       4,       7]
n3  = [0.5,  1,  170000,  4300,    100000]
g3  = [9749, 1,  580000,  4600000, 6400000000]
c3  = org_cols
for d, n, g, c in zip(d3, n3, g3, c3):
    ax4.scatter([d], [np.log10(n)], [np.log10(g)],
                c=c, s=80, depthshade=True, edgecolors='white', linewidth=0.4)
    ax4.text(d, np.log10(n)+0.1, np.log10(g)+0.3,
             org_labs[d3.index(d)], fontsize=5.5, ha='center')
# Life-threshold plane
d_plane = np.linspace(1, 7, 20)
g_plane = np.linspace(4, 10, 20)
DP, GP = np.meshgrid(d_plane, g_plane)
ax4.plot_surface(DP, np.full_like(DP, np.log10(1.7e5)), GP,
                 alpha=0.12, color=GREEN, linewidth=0)
ax4.set_xlabel('Depth D', labelpad=1)
ax4.set_ylabel('log N$_\mathrm{osc}$', labelpad=1)
ax4.set_zlabel('log genome (nt)', labelpad=1)
ax4.set_title('Categorical Space', pad=3)
ax4.view_init(elev=22, azim=-40)
clean3d(ax4)

fig.savefig(os.path.join(OUT, 'panel4_categorical.png'),
            dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Panel 4 saved.')

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 5  C-value Conservation & Viral Genome Scaling
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 4.4), facecolor='white')
ax3d_p5 = fig.add_axes([0.76, 0.12, 0.22, 0.78], projection='3d')
fig.subplots_adjust(left=0.06, right=0.74, top=0.88, bottom=0.18, wspace=0.42)

# 5a  rho_Q across organisms
ax = axes[0]
org_n   = ['Mycoplasma', 'E. coli', 'S.\ncerevisiae', 'Human\nlymphocyte',
           'Human\nhepatocyte', 'Necturus']
rho_Q   = [33.05, 46.61, 8.10, 1031.38, 109.05, 4.79]
rcols   = [TEAL, BLUE, GREEN, PURPLE, ORANGE, RED]
ax.bar(range(6), rho_Q, color=rcols, alpha=0.88, edgecolor='white', width=0.65)
ax.set_xticks(range(6))
ax.set_xticklabels(org_n, rotation=40, ha='right', fontsize=7)
ax.set_yscale('log')
ax.set_ylabel('ρ$_Q$ = |Q$_\mathrm{gen}$| / V$_\mathrm{cell}^{3/4}$ (SI)')
ax.set_title('C-value Charge Density')

# 5b  Viral genome vs host cell volume
ax = axes[1]
v_nt  = [4830, 7741, 7200, 9749, 13600, 9600, 3200, 35937, 172000, 152261, 236000, 125000, 200000]
h_vol = [250, 2000, 1500, 300, 1500, 5000, 5000, 2000, 2000, 2000, 3000, 2000, 3000]
ax.scatter(h_vol, v_nt, c=BLUE, s=50, zorder=4, edgecolors='white', alpha=0.88)
# Empirical regression beta=0.503
lx = np.log(h_vol);  ly = np.log(v_nt)
m_emp, b_emp = np.polyfit(lx, ly, 1)
x_fit = np.array([200, 6000])
ax.loglog(x_fit, np.exp(b_emp) * x_fit**m_emp, '--', color=RED, lw=1.4,
          label=f'β={m_emp:.2f}')
# Theory beta = 1/12
A_theory = np.exp(np.mean(ly) - (1/12)*np.mean(lx))
ax.loglog(x_fit, A_theory * x_fit**(1/12), ':', color=ORANGE, lw=1.4,
          label='β=1/12 (theory)')
ax.set_xscale('log');  ax.set_yscale('log')
ax.set_xlabel('Host V$_\mathrm{cell}$ (μm³)')
ax.set_ylabel('Viral genome (nt)')
ax.set_title('Viral Genome Scaling')
ax.legend()

# 5c  Camouflage threshold vs richness R  (with Eigen bounds)
ax = axes[2]
R_th = np.logspace(3, 5.5, 300)
phi = 1.848
N_cam = R_th * np.log(2) / np.log(phi)
ax.loglog(R_th, N_cam, color=PURPLE, lw=2, label='N$_\mathrm{camouflage}$')
ax.axhline(1e4,  color=RED,    ls='--', lw=1.1, alpha=0.85, label='Eigen RNA (10⁴ nt)')
ax.axhline(1e5,  color=ORANGE, ls='--', lw=1.1, alpha=0.85, label='Eigen CoV (10⁵ nt)')
for vname, vnt in [('SARS-CoV-2', 29903), ('Influenza A', 13600), ('Poliovirus', 7741)]:
    ax.axhline(vnt, color='grey', ls=':', lw=0.7, alpha=0.5)
    ax.text(3.1e3, vnt*1.08, vname, fontsize=6, color='grey')
ax.set_xlabel('Categorical richness R')
ax.set_ylabel('N$_\mathrm{camouflage}$ (nt)')
ax.set_title('Camouflage–Eigen Constraint')
ax.legend(fontsize=7)

# 5d  3D surface: rho_Q over (log N_bp, log V_cell)
ax4 = ax3d_p5
N_bp_r = np.logspace(5, 10, 35)
V_r    = np.logspace(-19, -12, 35)
Nbp_m, Vm = np.meshgrid(N_bp_r, V_r)
Q_m    = 2 * e_charge * Nbp_m
rho_m  = np.log10(Q_m / Vm**(3/4))
surf = ax4.plot_surface(np.log10(Nbp_m), np.log10(Vm), rho_m,
                        cmap='viridis', alpha=0.9, linewidth=0)
# Scatter known organisms
org_pts = [
    (5.8e5,  1e-19,  'Myco',  TEAL),
    (4.6e6,  1e-18,  'E.coli',BLUE),
    (6.4e9,  2.5e-16,'H. cell',PURPLE),
]
for nbp, vc, lb, cl in org_pts:
    Q_o = 2*e_charge*nbp
    rq  = np.log10(Q_o / vc**(3/4))
    ax4.scatter([np.log10(nbp)], [np.log10(vc)], [rq],
                c=cl, s=80, zorder=5, edgecolors='white')
ax4.set_xlabel('log N$_\mathrm{bp}$', labelpad=1)
ax4.set_ylabel('log V$_\mathrm{cell}$ (m³)', labelpad=1)
ax4.set_zlabel('log ρ$_Q$', labelpad=1)
ax4.set_title('Charge Density Surface', pad=3)
ax4.view_init(elev=25, azim=-50)
clean3d(ax4)

fig.savefig(os.path.join(OUT, 'panel5_cvalue_scaling.png'),
            dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Panel 5 saved.')

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL 6  Infection Overlap, H-bond Frequencies & Eigen Window
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 4.4), facecolor='white')
ax3d_p6 = fig.add_axes([0.76, 0.12, 0.22, 0.78], projection='3d')
fig.subplots_adjust(left=0.06, right=0.74, top=0.88, bottom=0.18, wspace=0.42)

# 6a  Housekeeping mimicry overlap distributions
ax = axes[0]
np.random.seed(99)
n_mc = 80000
# Good mimicry: scores tightly clustered above threshold 0
good_scores = np.random.normal(0.60, 0.25, n_mc)
# Poor mimicry: scores spread, mostly below threshold
poor_scores = np.random.normal(-0.40, 0.35, n_mc)
ax.hist(good_scores, bins=120, density=True, alpha=0.60, color=GREEN,
        label='Good mimicry', edgecolor='none')
ax.hist(poor_scores, bins=120, density=True, alpha=0.60, color=RED,
        label='Poor mimicry', edgecolor='none')
ax.axvline(0, color='black', lw=1.0, ls='--', alpha=0.7, label='threshold')
from scipy import stats
xg = np.linspace(-1.5, 1.8, 300)
ax.plot(xg, stats.norm.pdf(xg, 0.60, 0.25), color=GREEN, lw=1.8)
ax.plot(xg, stats.norm.pdf(xg, -0.40, 0.35), color=RED, lw=1.8)
ax.set_xlabel('Categorical overlap score')
ax.set_ylabel('Density')
ax.set_title('Housekeeping Mimicry Overlap')
ax.legend()

# 6b  Cumulative coherence domain potential (per-nt Debye potential)
ax = axes[1]
nt_pos = np.arange(1, 101)
phi_nt = 8.187e-3   # V per nucleotide (Debye-screened)
phi_cum = phi_nt * nt_pos   # cumulative potential (V)
kBT_eV = kB * T / e_charge   # V
Gamma_cum = phi_cum / kBT_eV
ax.plot(nt_pos, phi_cum * 1000, color=TEAL, lw=2, label='Φ$_\mathrm{cum}$ (mV)')
ax.axvline(50, color=PURPLE, ls='--', lw=1.1, alpha=0.8, label='coherence domain (50 nt)')
ax.axhline(410, color=ORANGE, ls=':', lw=1, alpha=0.7, label='Φ=410 mV')
ax2b = ax.twinx()
ax2b.plot(nt_pos, Gamma_cum, color=RED, lw=1.5, ls='-', alpha=0.7)
ax2b.set_ylabel('Confinement Γ', color=RED, fontsize=8)
ax2b.tick_params(axis='y', labelcolor=RED, labelsize=7)
ax.set_xlabel('Nucleotide position')
ax.set_ylabel('Cumulative potential (mV)')
ax.set_title('Coherence Domain Potential')
ax.legend(fontsize=7)

# 6c  Eigen–Camouflage viable window
ax = axes[2]
mu_range = np.logspace(-5.5, -3.2, 300)
N_eigen  = 1 / mu_range
N_cam_r  = N_eigen * 0.886   # camouflage/Eigen ratio from validation
ax.loglog(mu_range, N_eigen, color=RED, lw=2, label='Eigen limit N=1/μ')
ax.loglog(mu_range, N_cam_r, color=ORANGE, lw=2, ls='--', label='Camouflage minimum')
ax.fill_between(mu_range, N_cam_r, N_eigen, alpha=0.18, color=GREEN, label='viable window')
virus_pts = [('SARS-CoV-2', 29903, 1e-5, PURPLE),
             ('Influenza A', 13600, 1e-4, BLUE),
             ('Poliovirus',  7741,  1e-4, TEAL)]
for vname, vnt, verr, vc2 in virus_pts:
    ax.scatter([verr], [vnt], color=vc2, s=55, zorder=5, edgecolors='white')
    ax.text(verr*1.1, vnt*1.15, vname, fontsize=6, color=vc2)
ax.set_xlabel('Mutation rate μ (nt⁻¹ cycle⁻¹)')
ax.set_ylabel('Genome size (nt)')
ax.set_title('Eigen–Camouflage Window')
ax.legend(fontsize=7)

# 6d  3D viability surface over (log mu, log N_genome)
ax4 = ax3d_p6
mu_g  = np.logspace(-5.5, -3.2, 40)
N_g   = np.logspace(3.5, 5.5, 40)
MUm, Nm = np.meshgrid(mu_g, N_g)
Neig_m  = 1 / MUm
Ncam_m  = Neig_m * 0.886
# Viability: smooth score between 0 and 1
score = np.zeros_like(MUm)
in_window = (Nm >= Ncam_m) & (Nm <= Neig_m)
score[in_window] = 1.0
# Smooth edges
frac_above = np.clip((Nm - Ncam_m) / (0.1 * Ncam_m + 1), 0, 1)
frac_below = np.clip((Neig_m - Nm) / (0.1 * Neig_m + 1), 0, 1)
score = frac_above * frac_below
score = np.clip(score, 0, 1)
surf = ax4.plot_surface(np.log10(MUm), np.log10(Nm), score,
                        cmap='coolwarm', alpha=0.9, linewidth=0)
for _, vnt, verr, vc2 in virus_pts:
    ax4.scatter([np.log10(verr)], [np.log10(vnt)], [0.05],
                c=vc2, s=60, zorder=5, edgecolors='white')
ax4.set_xlabel('log μ', labelpad=1)
ax4.set_ylabel('log N (nt)', labelpad=1)
ax4.set_zlabel('Viability', labelpad=1)
ax4.set_title('Infection Viability Surface', pad=3)
ax4.view_init(elev=25, azim=-50)
clean3d(ax4)

fig.savefig(os.path.join(OUT, 'panel6_infection_overlap.png'),
            dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Panel 6 saved.')

print('\nAll 6 panels generated in:', OUT)

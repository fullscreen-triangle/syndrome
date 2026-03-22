"""
Generate all 7 figure panels for the fuzzy circuit paper.
Each panel has 4 charts in a row, white background, minimal text.
All charts are data-driven (no conceptual diagrams or tables).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize
from matplotlib import cm

from syndrome.core.circuit import (
    BiochemicalCircuit,
    CircuitNode,
    CircuitEdge,
    FuzzyInterval,
    build_glycolysis_circuit,
    build_etc_circuit,
    build_protein_qc_circuit,
    simulate_disease_progression,
    RT,
)

FIGDIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(FIGDIR, exist_ok=True)

# Global style
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'font.size': 9,
    'axes.titlesize': 10,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'font.family': 'sans-serif',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

COLORS = {
    'healthy': '#2ecc71',
    'diseased': '#e74c3c',
    'mild': '#f39c12',
    'hub': '#3498db',
    'accent': '#9b59b6',
    'dark': '#2c3e50',
    'grey': '#95a5a6',
}


# =============================================================================
# PANEL 1: Chemical Potential & Circuit Foundations
# =============================================================================
def panel1_circuit_foundations():
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

    # 1A: Chemical potential vs concentration (log scale)
    ax = axes[0]
    c_range = np.logspace(-6, -1, 200)
    mu_0_vals = [0, -1000, -3000]
    labels = [r'$\mu_0 = 0$', r'$\mu_0 = -1$', r'$\mu_0 = -3$ kJ/mol']
    colors_local = ['#3498db', '#e74c3c', '#2ecc71']
    for mu0, label, col in zip(mu_0_vals, labels, colors_local):
        phi = mu0 + RT * np.log(c_range)
        ax.plot(c_range * 1e3, phi / 1000, color=col, lw=1.8, label=label)
    ax.set_xscale('log')
    ax.set_xlabel('[C] (mM)')
    ax.set_ylabel(r'$\phi_i$ (kJ/mol)')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('A', fontweight='bold', loc='left')

    # 1B: Conductance vs substrate (Michaelis-Menten transistor)
    ax = axes[1]
    S = np.linspace(0, 10, 200)
    Km_vals = [0.5, 1.0, 3.0]
    kcat_ET = 1.0
    for Km in Km_vals:
        G = kcat_ET / (RT * (Km + S)) * 1e6
        ax.plot(S, G, lw=1.8, label=f'$K_m={Km}$')
    ax.set_xlabel('[S] (mM)')
    ax.set_ylabel(r'$\mathcal{G}_{ij}$ ($\times 10^{-6}$)')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('B', fontweight='bold', loc='left')

    # 1C: Ohm's law analog — flux vs potential difference
    ax = axes[2]
    dphi = np.linspace(-5000, 5000, 300)
    c_s = 1e-3
    k_fwd = 1.0
    k_rev = 0.8
    # Exact flux
    J_exact = k_fwd * c_s * (1 - np.exp(-dphi / RT))
    # Linear (Ohm) approximation
    G = k_fwd * c_s / RT
    J_linear = G * dphi
    ax.plot(dphi / 1000, J_exact * 1e3, color=COLORS['dark'], lw=1.8, label='Exact')
    ax.plot(dphi / 1000, J_linear * 1e3, '--', color=COLORS['diseased'], lw=1.5, label='Ohm analog')
    ax.axhline(0, color='grey', lw=0.5)
    ax.axvline(0, color='grey', lw=0.5)
    ax.set_xlabel(r'$\Delta\phi$ (kJ/mol)')
    ax.set_ylabel(r'$J_{ij}$ (mM/s)')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('C', fontweight='bold', loc='left')

    # 1D: 3D — Categorical depth surface over (concentration, mu_0)
    ax = fig.add_subplot(1, 4, 4, projection='3d')
    axes[3].remove()
    c_grid = np.logspace(-5, -1, 40)
    mu0_grid = np.linspace(-5000, 0, 40)
    C, M = np.meshgrid(c_grid, mu0_grid)
    PHI = M + RT * np.log(C)
    H_cat = PHI / (RT * np.log(2))

    surf = ax.plot_surface(np.log10(C * 1e3), M / 1000, H_cat,
                           cmap='viridis', alpha=0.85, edgecolor='none')
    ax.set_xlabel('log[C] (mM)', fontsize=7, labelpad=2)
    ax.set_ylabel(r'$\mu_0$ (kJ/mol)', fontsize=7, labelpad=2)
    ax.set_zlabel(r'$\mathcal{H}$ (bits)', fontsize=7, labelpad=2)
    ax.tick_params(labelsize=6)
    ax.view_init(elev=25, azim=-45)
    ax.set_title('D', fontweight='bold', loc='left', pad=10)

    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, 'panel1_circuit_foundations.pdf'),
                dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGDIR, 'panel1_circuit_foundations.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    print('Panel 1 done')


# =============================================================================
# PANEL 2: Fuzzy Constraint Propagation & Trajectory Completion
# =============================================================================
def panel2_fuzzy_propagation():
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

    circuit = build_glycolysis_circuit(pk_deficient=False)
    obs = {"Glc": 5.0e-3, "ATP": 1.85e-3, "Pyr": 0.051e-3}

    # Run trajectory completion and track interval widths per iteration
    widths_history = []
    max_iter = 20
    circuit_copy = build_glycolysis_circuit(pk_deficient=False)

    # Initialize
    for name, node in circuit_copy.nodes.items():
        if name in obs:
            node.concentration = FuzzyInterval.from_measurement(
                obs[name], obs[name] * 0.1)
        else:
            node.concentration = FuzzyInterval.uniform(node.c_min, node.c_max)

    cycles = circuit_copy.find_loops()

    for it in range(max_iter):
        widths = {}
        for n in circuit_copy.nodes:
            widths[n] = circuit_copy.nodes[n].concentration.width(1.0)
        widths_history.append(widths)

        for name in circuit_copy.nodes:
            new_interval = circuit_copy.apply_fuzzy_kcl(name)
            circuit_copy.nodes[name].concentration = new_interval
        if cycles:
            circuit_copy.apply_fuzzy_kvl(cycles)
        for name, val in obs.items():
            circuit_copy.nodes[name].concentration = FuzzyInterval.from_measurement(
                val, val * 0.1)

    # 2A: Fuzzy interval narrowing over iterations (selected nodes)
    ax = axes[0]
    target_nodes = ['G6P', 'FBP', 'G3P', 'PEP', 'PG3']
    for node_name in target_nodes:
        ws = [wh.get(node_name, 0) for wh in widths_history]
        if ws[0] > 0:
            ws_norm = [w / ws[0] for w in ws]
            ax.plot(range(max_iter), ws_norm, lw=1.5, label=node_name)
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Normalised width')
    ax.set_yscale('log')
    ax.legend(fontsize=6, frameon=False, ncol=2)
    ax.set_title('A', fontweight='bold', loc='left')

    # 2B: Alpha-cut intervals for a resolved vs unresolved node
    ax = axes[1]
    resolved = circuit_copy.nodes["G6P"].concentration
    alphas = resolved.alphas
    ax.fill_betweenx(alphas, resolved.lo * 1e3, resolved.hi * 1e3,
                      alpha=0.3, color=COLORS['healthy'])
    ax.plot(resolved.lo * 1e3, alphas, color=COLORS['healthy'], lw=1.5)
    ax.plot(resolved.hi * 1e3, alphas, color=COLORS['healthy'], lw=1.5)

    # Show the initial uniform prior as reference
    ax.axvline(circuit.nodes["G6P"].c_min * 1e3, color=COLORS['grey'],
               ls='--', lw=0.8, alpha=0.5)
    ax.axvline(circuit.nodes["G6P"].c_max * 1e3, color=COLORS['grey'],
               ls='--', lw=0.8, alpha=0.5)

    ax.set_xlabel('[G6P] (mM)')
    ax.set_ylabel(r'$\alpha$')
    ax.set_title('B', fontweight='bold', loc='left')

    # 2C: Resolved concentration profile across glycolytic pathway
    ax = axes[2]
    pathway_order = ['Glc', 'G6P', 'F6P', 'FBP', 'G3P', 'BPG13',
                     'PG3', 'PG2', 'PEP', 'Pyr']
    centers = [circuit_copy.nodes[n].concentration.center() * 1e3
               for n in pathway_order]
    widths_bar = [circuit_copy.nodes[n].concentration.width(0.5) * 1e3
                  for n in pathway_order]

    x_pos = np.arange(len(pathway_order))
    ax.bar(x_pos, centers, color=COLORS['hub'], alpha=0.7, width=0.6)
    ax.errorbar(x_pos, centers, yerr=widths_bar, fmt='none',
                ecolor=COLORS['dark'], capsize=3, lw=1.2)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(pathway_order, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('[C] (mM)')
    ax.set_title('C', fontweight='bold', loc='left')

    # 2D: KCL residuals per node
    ax = axes[3]
    conc = {n: circuit_copy.nodes[n].concentration.center()
            for n in circuit_copy.nodes}
    residuals = [abs(circuit_copy.kcl_residual(n, conc)) for n in pathway_order]
    colors_r = [COLORS['healthy'] if r < 0.001 else COLORS['mild']
                for r in residuals]
    ax.bar(x_pos, residuals, color=colors_r, width=0.6)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(pathway_order, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('|KCL residual|')
    ax.set_yscale('log')
    ax.set_title('D', fontweight='bold', loc='left')

    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, 'panel2_fuzzy_propagation.pdf'),
                dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGDIR, 'panel2_fuzzy_propagation.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    print('Panel 2 done')


# =============================================================================
# PANEL 3: Reference-Free Disease Detection
# =============================================================================
def panel3_reference_free():
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

    healthy = build_glycolysis_circuit(pk_deficient=False)
    diseased = build_glycolysis_circuit(pk_deficient=True, pk_reduction=0.1)

    h_obs = {"Glc": 5.0e-3, "ATP": 1.85e-3, "Pyr": 0.051e-3}
    d_obs = {"Glc": 5.0e-3, "ATP": 0.8e-3, "Pyr": 0.01e-3}

    h_states, _, _ = healthy.trajectory_completion(h_obs, uncertainty=0.15)
    d_states, _, _ = diseased.trajectory_completion(d_obs, uncertainty=0.15)

    pathway = ['Glc', 'G6P', 'F6P', 'FBP', 'G3P', 'BPG13',
               'PG3', 'PG2', 'PEP', 'Pyr']

    # 3A: Concentration comparison healthy vs diseased
    ax = axes[0]
    h_conc = [healthy.nodes[n].concentration.center() * 1e3 for n in pathway]
    d_conc = [diseased.nodes[n].concentration.center() * 1e3 for n in pathway]
    x = np.arange(len(pathway))
    w = 0.35
    ax.bar(x - w/2, h_conc, w, color=COLORS['healthy'], label='Healthy', alpha=0.8)
    ax.bar(x + w/2, d_conc, w, color=COLORS['diseased'], label='PK-def', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(pathway, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('[C] (mM)')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('A', fontweight='bold', loc='left')

    # 3B: Flux profile comparison
    ax = axes[1]
    h_conc_d = {n: healthy.nodes[n].concentration.center() for n in healthy.nodes}
    d_conc_d = {n: diseased.nodes[n].concentration.center() for n in diseased.nodes}

    reaction_names = []
    h_fluxes = []
    d_fluxes = []
    seen = set()
    for e in healthy.edges:
        key = e.enzyme_name
        if key in seen or not key or 'ATP' in key or 'Feedback' in key or 'FBPase' in key or 'PEPCK' in key:
            continue
        seen.add(key)
        h_f = e.flux(h_conc_d.get(e.source, 1e-6), h_conc_d.get(e.target, 1e-6))
        h_fluxes.append(abs(h_f) * 1e3)
        reaction_names.append(key)

    seen2 = set()
    for e in diseased.edges:
        key = e.enzyme_name
        if key in seen2 or not key or 'ATP' in key or 'Feedback' in key or 'FBPase' in key or 'PEPCK' in key:
            continue
        seen2.add(key)
        d_f = e.flux(d_conc_d.get(e.source, 1e-6), d_conc_d.get(e.target, 1e-6))
        d_fluxes.append(abs(d_f) * 1e3)

    x2 = np.arange(len(reaction_names))
    ax.bar(x2 - w/2, h_fluxes, w, color=COLORS['healthy'], alpha=0.8)
    ax.bar(x2 + w/2, d_fluxes, w, color=COLORS['diseased'], alpha=0.8)
    ax.set_xticks(x2)
    ax.set_xticklabels(reaction_names, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('|Flux| (mM/s)')
    ax.set_title('B', fontweight='bold', loc='left')

    # 3C: ATP/ADP ratio comparison across PK reduction levels
    ax = axes[2]
    pk_reductions = np.linspace(0.01, 1.0, 20)
    atp_ratios = []
    for pk_r in pk_reductions:
        c = build_glycolysis_circuit(pk_deficient=True, pk_reduction=pk_r)
        c.trajectory_completion(
            {"Glc": 5e-3, "ATP": 1.85e-3 * pk_r, "Pyr": 0.051e-3 * pk_r},
            max_iter=20, uncertainty=0.15)
        conc = {n: c.nodes[n].concentration.center() for n in c.nodes}
        ratio = conc["ATP"] / max(conc["ADP"], 1e-10)
        atp_ratios.append(ratio)

    ax.plot(pk_reductions * 100, atp_ratios, 'o-', color=COLORS['dark'],
            markersize=4, lw=1.5)
    ax.axhline(atp_ratios[-1], color=COLORS['healthy'], ls='--', lw=1, alpha=0.5)
    ax.set_xlabel('PK activity (%)')
    ax.set_ylabel('ATP/ADP ratio')
    ax.set_title('C', fontweight='bold', loc='left')

    # 3D: KCL residual comparison at each node
    ax = axes[3]
    all_nodes = list(healthy.nodes.keys())
    h_res = [abs(healthy.kcl_residual(n, h_conc_d)) for n in all_nodes]
    d_res = [abs(diseased.kcl_residual(n, d_conc_d)) for n in all_nodes]

    x3 = np.arange(len(all_nodes))
    ax.scatter(h_res, d_res, c=COLORS['accent'], s=40, edgecolors=COLORS['dark'],
               linewidths=0.5, zorder=3)
    # Diagonal
    max_val = max(max(h_res), max(d_res)) * 1.1
    ax.plot([0, max_val], [0, max_val], '--', color=COLORS['grey'], lw=0.8)
    for i, n in enumerate(all_nodes):
        if h_res[i] > max_val * 0.3 or d_res[i] > max_val * 0.3:
            ax.annotate(n, (h_res[i], d_res[i]), fontsize=6,
                        xytext=(3, 3), textcoords='offset points')
    ax.set_xlabel('KCL residual (healthy)')
    ax.set_ylabel('KCL residual (diseased)')
    ax.set_title('D', fontweight='bold', loc='left')

    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, 'panel3_reference_free.pdf'),
                dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGDIR, 'panel3_reference_free.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    print('Panel 3 done')


# =============================================================================
# PANEL 4: Signal Variance Early Warning
# =============================================================================
def panel4_signal_variance():
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

    np.random.seed(42)
    healthy = build_glycolysis_circuit(pk_deficient=False)
    mild = build_glycolysis_circuit(pk_deficient=True, pk_reduction=0.5)
    severe = build_glycolysis_circuit(pk_deficient=True, pk_reduction=0.1)

    h_sim = simulate_disease_progression(healthy, "ATP", 0.0, n_steps=300)
    m_sim = simulate_disease_progression(mild, "ATP", 0.02, n_steps=300)
    s_sim = simulate_disease_progression(severe, "ATP", 0.05, n_steps=300)

    # 4A: ATP time series — healthy vs mild vs severe
    ax = axes[0]
    ax.plot(h_sim["signals"]["ATP"] * 1e3, color=COLORS['healthy'],
            lw=1.0, alpha=0.8, label='Healthy')
    ax.plot(m_sim["signals"]["ATP"] * 1e3, color=COLORS['mild'],
            lw=1.0, alpha=0.8, label='Mild')
    ax.plot(s_sim["signals"]["ATP"] * 1e3, color=COLORS['diseased'],
            lw=1.0, alpha=0.8, label='Severe')
    ax.set_xlabel('Step')
    ax.set_ylabel('[ATP] (mM)')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('A', fontweight='bold', loc='left')

    # 4B: Rolling variance comparison
    ax = axes[1]
    window = 20
    h_var = BiochemicalCircuit.signal_variance_from_trajectory(
        h_sim["signals"]["ATP"], window)
    m_var = BiochemicalCircuit.signal_variance_from_trajectory(
        m_sim["signals"]["ATP"], window)
    s_var = BiochemicalCircuit.signal_variance_from_trajectory(
        s_sim["signals"]["ATP"], window)

    ax.plot(h_var, color=COLORS['healthy'], lw=1.2, label='Healthy')
    ax.plot(m_var, color=COLORS['mild'], lw=1.2, label='Mild')
    ax.plot(s_var, color=COLORS['diseased'], lw=1.2, label='Severe')
    ax.set_xlabel('Step')
    ax.set_ylabel(r'Var($\Delta$[ATP])')
    ax.set_yscale('log')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('B', fontweight='bold', loc='left')

    # 4C: Multi-signal variance heatmap (diseased)
    ax = axes[2]
    signals_to_plot = ['Glc', 'G6P', 'FBP', 'G3P', 'PEP', 'Pyr', 'ATP', 'ADP']
    var_matrix = []
    n_windows = 6
    for sig in signals_to_plot:
        if sig in s_sim["signals"]:
            series = s_sim["signals"][sig]
            chunk_size = len(series) // n_windows
            row = []
            for i in range(n_windows):
                chunk = series[i * chunk_size:(i + 1) * chunk_size]
                row.append(np.var(np.diff(chunk)))
            var_matrix.append(row)

    var_arr = np.array(var_matrix)
    # Log-normalize
    var_log = np.log10(var_arr + 1e-30)
    im = ax.imshow(var_log, aspect='auto', cmap='YlOrRd', interpolation='nearest')
    ax.set_yticks(range(len(signals_to_plot)))
    ax.set_yticklabels(signals_to_plot, fontsize=7)
    ax.set_xlabel('Time window')
    ax.set_xticks(range(n_windows))
    ax.set_xticklabels([f'W{i+1}' for i in range(n_windows)], fontsize=7)
    plt.colorbar(im, ax=ax, label=r'log$_{10}$ Var', shrink=0.8)
    ax.set_title('C', fontweight='bold', loc='left')

    # 4D: Consistency index decline over time
    ax = axes[3]
    ax.plot(h_sim["consistency"], color=COLORS['healthy'], lw=1.5, label='Healthy')
    ax.plot(m_sim["consistency"], color=COLORS['mild'], lw=1.5, label='Mild')
    ax.plot(s_sim["consistency"], color=COLORS['diseased'], lw=1.5, label='Severe')
    ax.set_xlabel('Step')
    ax.set_ylabel(r'$\mathcal{C}(\mathcal{G})$')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('D', fontweight='bold', loc='left')

    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, 'panel4_signal_variance.pdf'),
                dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGDIR, 'panel4_signal_variance.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    print('Panel 4 done')


# =============================================================================
# PANEL 5: Hub Vulnerability (Mitochondrial ETC)
# =============================================================================
def panel5_hub_vulnerability():
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

    np.random.seed(42)

    # 5A: Multi-system failure — simulate ETC with Complex I inhibition
    # Show time series of multiple downstream metabolites
    ax = axes[0]
    etc_h = build_etc_circuit(complex_i_inhibited=False)
    etc_d = build_etc_circuit(complex_i_inhibited=True, inhibition_factor=0.1)

    sim_h = simulate_disease_progression(etc_h, "NADH", 0.0, n_steps=200)
    sim_d = simulate_disease_progression(etc_d, "NADH", 0.5, n_steps=200)

    # Normalise each signal to its initial value for comparison
    for sig_name, col in [("NADH", COLORS['diseased']),
                           ("UQH2", COLORS['mild']),
                           ("ATP_m", COLORS['hub']),
                           ("CytC_red", COLORS['accent'])]:
        series = sim_d["signals"][sig_name]
        normed = series / max(series[0], 1e-15)
        ax.plot(normed, color=col, lw=1.2, alpha=0.8, label=sig_name)
    ax.set_xlabel('Step')
    ax.set_ylabel('Normalised [C]')
    ax.legend(fontsize=6, frameon=False)
    ax.set_title('A', fontweight='bold', loc='left')

    # 5B: Hub node (NADH) trajectory: healthy vs inhibited
    ax = axes[1]
    ax.plot(sim_h["signals"]["NADH"] * 1e3, color=COLORS['healthy'],
            lw=1.2, label='Healthy')
    ax.plot(sim_d["signals"]["NADH"] * 1e3, color=COLORS['diseased'],
            lw=1.2, label='CI inhib.')
    ax.set_xlabel('Step')
    ax.set_ylabel('[NADH] (mM)')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('B', fontweight='bold', loc='left')

    # 5C: Total signal variance (all nodes) vs inhibition level
    ax = axes[2]
    inhibition_levels = np.linspace(0.05, 1.0, 20)
    total_var = []
    for level in inhibition_levels:
        etc = build_etc_circuit(complex_i_inhibited=True,
                                inhibition_factor=level)
        sim = simulate_disease_progression(etc, "NADH", 1.0 - level, n_steps=100)
        # Aggregate variance across all signals
        var_sum = sum(np.var(np.diff(sim["signals"][n]))
                      for n in etc.nodes if n in sim["signals"])
        total_var.append(var_sum)

    ax.plot(inhibition_levels * 100, total_var, 'o-',
            color=COLORS['hub'], markersize=4, lw=1.5)
    ax.set_xlabel('Complex I activity (%)')
    ax.set_ylabel(r'$\Sigma$ Var($\Delta$signal)')
    ax.set_yscale('log')
    ax.set_title('C', fontweight='bold', loc='left')

    # 5D: 3D — final concentration of 3 metabolites across inhibition levels
    ax = fig.add_subplot(1, 4, 4, projection='3d')
    axes[3].remove()

    levels = np.linspace(0.05, 1.0, 25)
    nadh_final = []
    uqh2_final = []
    atp_final = []
    for level in levels:
        etc = build_etc_circuit(complex_i_inhibited=True, inhibition_factor=level)
        sim = simulate_disease_progression(etc, "NADH", 1.0 - level, n_steps=80)
        nadh_final.append(sim["signals"]["NADH"][-1] * 1e3)
        uqh2_final.append(sim["signals"]["UQH2"][-1] * 1e3)
        atp_final.append(sim["signals"]["ATP_m"][-1] * 1e3)

    ax.scatter(levels * 100, np.array(nadh_final), np.array(atp_final),
               c=np.array(uqh2_final), cmap='YlOrRd', s=25, edgecolors='k', linewidths=0.3)
    ax.set_xlabel('CI act. (%)', fontsize=7, labelpad=2)
    ax.set_ylabel('[NADH] (mM)', fontsize=7, labelpad=2)
    ax.set_zlabel('[ATP] (mM)', fontsize=7, labelpad=2)
    ax.tick_params(labelsize=6)
    ax.view_init(elev=20, azim=-50)
    ax.set_title('D', fontweight='bold', loc='left', pad=10)

    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, 'panel5_hub_vulnerability.pdf'),
                dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGDIR, 'panel5_hub_vulnerability.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    print('Panel 5 done')


# =============================================================================
# PANEL 6: SOD1 Severity Ordering & Loop Length Latency
# =============================================================================
def panel6_sod1_latency():
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

    np.random.seed(42)

    # 6A: SOD1 mutation consistency trajectories
    ax = axes[0]
    mutations = {
        'A4V': 1e-2,
        'G93A': 5e-3,
        'D90A': 1e-3,
        'WT': 1e-6,
    }
    colors_mut = {'A4V': '#e74c3c', 'G93A': '#f39c12', 'D90A': '#3498db', 'WT': '#2ecc71'}

    for name, rate in mutations.items():
        pqc = build_protein_qc_circuit(misfolding_rate=rate)
        sim = simulate_disease_progression(pqc, "folded", rate, n_steps=500)
        ax.plot(sim["consistency"], color=colors_mut[name], lw=1.5, label=name)
    ax.set_xlabel('Step')
    ax.set_ylabel(r'$\mathcal{C}(\mathcal{G})$')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('A', fontweight='bold', loc='left')

    # 6B: Final [folded] protein vs misfolding rate — dose-response
    ax = axes[1]
    rates = np.logspace(-6, -1, 30)
    final_folded = []
    for r in rates:
        pqc = build_protein_qc_circuit(misfolding_rate=r)
        sim = simulate_disease_progression(pqc, "folded", r * 50, n_steps=300)
        final_folded.append(sim["signals"]["folded"][-1] * 1e3)

    ax.semilogx(rates, final_folded, 'o-', color=COLORS['accent'],
                markersize=3, lw=1.5)
    # Mark known mutations
    for name, rate in mutations.items():
        pqc = build_protein_qc_circuit(misfolding_rate=rate)
        sim = simulate_disease_progression(pqc, "folded", rate * 50, n_steps=300)
        ff = sim["signals"]["folded"][-1] * 1e3
        ax.annotate(name, (rate, ff), fontsize=7, fontweight='bold',
                    xytext=(5, 3), textcoords='offset points',
                    color=colors_mut[name])
    ax.set_xlabel(r'Misfolding rate $\delta$')
    ax.set_ylabel('[Folded protein] (mM)')
    ax.set_title('B', fontweight='bold', loc='left')

    # 6C: Signal excursion (range) vs defect rate — more defect = more drift
    ax = axes[2]
    defect_rates = np.linspace(0.0, 1.0, 20)
    excursions = []
    for dr in defect_rates:
        pqc = build_protein_qc_circuit(misfolding_rate=0.01)
        sim = simulate_disease_progression(pqc, "folded", dr, n_steps=200)
        excursions.append(np.ptp(sim["signals"]["folded"]) * 1e3)

    ax.plot(defect_rates, excursions, 'o-', color=COLORS['dark'],
            markersize=4, lw=1.5)
    ax.set_xlabel('Defect rate')
    ax.set_ylabel('Signal excursion (mM)')
    ax.set_title('C', fontweight='bold', loc='left')

    # 6D: Holonomy accumulation over traversals for different defect magnitudes
    ax = axes[3]
    traversals = np.arange(1, 101)
    deltas = [0.001, 0.005, 0.01, 0.05]
    for delta in deltas:
        holonomy = delta * traversals  # linear accumulation (Theorem 6.3)
        ax.plot(traversals, holonomy, lw=1.5, label=f'$\\delta={delta}$')
    ax.axhline(0.1, color=COLORS['grey'], ls='--', lw=0.8, alpha=0.7)
    ax.text(102, 0.1, r'$\epsilon$', fontsize=8, color=COLORS['grey'])
    ax.set_xlabel('Traversals $n$')
    ax.set_ylabel(r'$\delta_\ell^{(n)}$')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('D', fontweight='bold', loc='left')

    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, 'panel6_sod1_latency.pdf'),
                dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGDIR, 'panel6_sod1_latency.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    print('Panel 6 done')


# =============================================================================
# PANEL 7: Drug Design & Therapeutic Intervention
# =============================================================================
def panel7_drug_design():
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

    # 7A: Drug target sensitivity — bar chart of |eta| per edge
    ax = axes[0]
    diseased = build_glycolysis_circuit(pk_deficient=True, pk_reduction=0.1)
    obs = {"Glc": 5e-3, "ATP": 0.8e-3, "Pyr": 0.01e-3}
    diseased.trajectory_completion(obs, uncertainty=0.15)

    conc = {n: diseased.nodes[n].concentration.center() for n in diseased.nodes}
    node_names = list(diseased.nodes.keys())
    n_edges = len(diseased.edges)

    # Compute sensitivity
    kcl_vec = np.array([diseased.kcl_residual(n, conc) for n in node_names])
    eps = 1e-3
    sensitivity_norms = []
    edge_labels = []
    for j, edge in enumerate(diseased.edges):
        orig_k = edge.k_fwd
        edge.k_fwd = orig_k * (1 + eps)
        kcl_p = np.array([diseased.kcl_residual(n, conc) for n in node_names])
        sens = np.linalg.norm((kcl_p - kcl_vec) / eps)
        sensitivity_norms.append(sens)
        label = edge.enzyme_name if edge.enzyme_name else f'{edge.source[:3]}->{edge.target[:3]}'
        edge_labels.append(label)
        edge.k_fwd = orig_k

    sorted_idx = np.argsort(sensitivity_norms)[::-1]
    top_n = min(12, len(sorted_idx))
    top_idx = sorted_idx[:top_n]

    colors_bar = [COLORS['diseased'] if i < 3 else COLORS['grey']
                  for i in range(top_n)]
    ax.barh(range(top_n),
            [sensitivity_norms[i] for i in top_idx],
            color=colors_bar, height=0.6)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([edge_labels[i] for i in top_idx], fontsize=7)
    ax.set_xlabel('Sensitivity $\\|\\partial KCL / \\partial G_{ij}\\|$')
    ax.invert_yaxis()
    ax.set_title('A', fontweight='bold', loc='left')

    # 7B: Disease trajectory with and without drug intervention
    ax = axes[1]
    np.random.seed(42)

    # Untreated: progressive disease
    untreated = build_glycolysis_circuit(pk_deficient=True, pk_reduction=0.2)
    sim_untreated = simulate_disease_progression(
        untreated, "PEP", 0.7, n_steps=200)

    # Treated: disease + partial restoration of PK activity
    treated = build_glycolysis_circuit(pk_deficient=True, pk_reduction=0.6)
    sim_treated = simulate_disease_progression(
        treated, "PEP", 0.3, n_steps=200)

    # Healthy baseline
    healthy_bl = build_glycolysis_circuit(pk_deficient=False)
    sim_healthy_bl = simulate_disease_progression(
        healthy_bl, "PEP", 0.0, n_steps=200)

    ax.plot(sim_healthy_bl["signals"]["ATP"] * 1e3, color=COLORS['healthy'],
            lw=1.2, label='Healthy')
    ax.plot(sim_treated["signals"]["ATP"] * 1e3, color=COLORS['hub'],
            lw=1.2, label='Treated')
    ax.plot(sim_untreated["signals"]["ATP"] * 1e3, color=COLORS['diseased'],
            lw=1.2, label='Untreated')
    ax.set_xlabel('Step')
    ax.set_ylabel('[ATP] (mM)')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('B', fontweight='bold', loc='left')

    # 7C: Dose-response: PK activator drug — ATP level vs drug dose
    ax = axes[2]
    doses = np.linspace(0, 1, 25)  # 0 = no drug, 1 = full restoration
    atp_finals = []
    for dose in doses:
        pk_act = 0.1 + dose * 0.9  # from 10% to 100%
        c = build_glycolysis_circuit(pk_deficient=True, pk_reduction=pk_act)
        sim_dose = simulate_disease_progression(c, "PEP", 0.5 * (1 - dose),
                                                 n_steps=100)
        atp_finals.append(sim_dose["signals"]["ATP"][-1] * 1e3)

    ax.plot(doses * 100, atp_finals, 'o-', color=COLORS['accent'],
            markersize=3, lw=1.5)
    ax.set_xlabel('Drug dose (%)')
    ax.set_ylabel('Final [ATP] (mM)')
    ax.set_title('C', fontweight='bold', loc='left')

    # 7D: Multi-signal recovery — bar chart of signal deviation before/after treatment
    ax = axes[3]
    signals_to_compare = ['ATP', 'ADP', 'PEP', 'Pyr', 'G3P', 'FBP']
    dev_untreated = []
    dev_treated = []

    # Reference: healthy final concentrations
    h_final = {n: sim_healthy_bl["signals"][n][-1] for n in signals_to_compare
               if n in sim_healthy_bl["signals"]}

    for sig in signals_to_compare:
        if sig in sim_untreated["signals"] and sig in h_final:
            h_val = h_final[sig]
            u_val = sim_untreated["signals"][sig][-1]
            t_val = sim_treated["signals"][sig][-1]
            dev_untreated.append(abs(u_val - h_val) / max(h_val, 1e-15))
            dev_treated.append(abs(t_val - h_val) / max(h_val, 1e-15))

    x7 = np.arange(len(signals_to_compare))
    w = 0.35
    ax.bar(x7 - w/2, dev_untreated, w, color=COLORS['diseased'],
           label='Untreated', alpha=0.8)
    ax.bar(x7 + w/2, dev_treated, w, color=COLORS['hub'],
           label='Treated', alpha=0.8)
    ax.set_xticks(x7)
    ax.set_xticklabels(signals_to_compare, fontsize=8)
    ax.set_ylabel('|Deviation from healthy|')
    ax.legend(fontsize=7, frameon=False)
    ax.set_title('D', fontweight='bold', loc='left')

    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, 'panel7_drug_design.pdf'),
                dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(FIGDIR, 'panel7_drug_design.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    print('Panel 7 done')


# =============================================================================
# Main
# =============================================================================
if __name__ == '__main__':
    print('Generating figures...')
    panel1_circuit_foundations()
    panel2_fuzzy_propagation()
    panel3_reference_free()
    panel4_signal_variance()
    panel5_hub_vulnerability()
    panel6_sod1_latency()
    panel7_drug_design()
    print(f'\nAll 7 panels saved to {FIGDIR}/')

"""
Panel visualizations for disease-computing-framework.tex

5 panels, each with 4 charts in a row, at least one 3D chart per panel.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from syndrome.core.partition import partition_capacity, categorical_distance_raw
from syndrome.core.coherence import coherence_index, therapeutic_efficacy
from syndrome.core.disease import DiseaseVector, OSCILLATOR_CLASSES
from syndrome.core.s_entropy import SEntropyPoint, s_entropy_distance
from syndrome.core.trajectory import address_precision, resolve_address


def ensure_output_dir():
    """Ensure output directory exists."""
    output_dir = Path(__file__).parent.parent / "publication" / "disease-computing" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def panel_1_partition_geometry():
    """
    Panel 1: Partition Geometry
    - A: Capacity curve C(n) = 2n²
    - B: 3D partition coordinate space
    - C: Address precision vs depth
    - D: Categorical distance matrix
    """
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))

    # A: Capacity curve
    ax = axes[0]
    n_vals = np.arange(1, 11)
    capacities = [partition_capacity(n) for n in n_vals]
    ax.bar(n_vals, capacities, color='steelblue', edgecolor='black', alpha=0.8)
    ax.plot(n_vals, capacities, 'ro-', markersize=6)
    ax.set_xlabel('n', fontsize=12)
    ax.set_ylabel('C(n)', fontsize=12)
    ax.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax.grid(True, alpha=0.3)

    # B: 3D partition coordinate space
    ax = fig.add_subplot(1, 4, 2, projection='3d')
    axes[1].remove()
    n_range = range(1, 5)
    colors = plt.cm.viridis(np.linspace(0, 1, 4))
    for i, n in enumerate(n_range):
        for ell in range(n):
            for m in range(-ell, ell + 1):
                ax.scatter(n, ell, m, c=[colors[i]], s=50, alpha=0.7)
    ax.set_xlabel('n', fontsize=10)
    ax.set_ylabel('ℓ', fontsize=10)
    ax.set_zlabel('m', fontsize=10)
    ax.set_title('B', fontsize=14, fontweight='bold', loc='left')

    # C: Address precision vs depth
    ax = axes[2]
    depths = np.arange(1, 16)
    precisions = [address_precision(d) for d in depths]
    ax.semilogy(depths, precisions, 'b-o', markersize=6, linewidth=2)
    ax.fill_between(depths, precisions, alpha=0.3)
    ax.set_xlabel('Depth k', fontsize=12)
    ax.set_ylabel('Precision (1/3^k)', fontsize=12)
    ax.set_title('C', fontsize=14, fontweight='bold', loc='left')
    ax.grid(True, alpha=0.3)

    # D: Categorical distance matrix
    ax = axes[3]
    n = 2
    coords = []
    for ell in range(n):
        for m in range(-ell, ell + 1):
            for s in (-0.5, 0.5):
                coords.append((n, ell, m, s))

    dist_matrix = np.zeros((len(coords), len(coords)))
    for i, c1 in enumerate(coords):
        for j, c2 in enumerate(coords):
            dist_matrix[i, j] = categorical_distance_raw(*c1, *c2)

    im = ax.imshow(dist_matrix, cmap='viridis', aspect='auto')
    plt.colorbar(im, ax=ax, label='d_cat')
    ax.set_xlabel('State j', fontsize=12)
    ax.set_ylabel('State i', fontsize=12)
    ax.set_title('D', fontsize=14, fontweight='bold', loc='left')

    plt.tight_layout()
    return fig


def panel_2_coherence():
    """
    Panel 2: Coherence Functions
    - A: Universal coherence curve
    - B: Class-specific coherence functions
    - C: Cellular coherence surface (3D)
    - D: Coherence distribution
    """
    fig = plt.figure(figsize=(16, 4))

    # A: Universal coherence curve
    ax1 = fig.add_subplot(1, 4, 1)
    pi_obs = np.linspace(0, 1, 100)
    pi_opt, pi_deg = 1.0, 0.0
    eta = [(p - pi_deg) / (pi_opt - pi_deg) for p in pi_obs]
    ax1.plot(pi_obs, eta, 'b-', linewidth=2.5)
    ax1.fill_between(pi_obs, eta, alpha=0.3)
    ax1.axhline(0.5, color='r', linestyle='--', alpha=0.5, label='η=0.5')
    ax1.set_xlabel('Π_obs', fontsize=12)
    ax1.set_ylabel('η', fontsize=12)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # B: Class-specific coherence (folding cycles example)
    ax2 = fig.add_subplot(1, 4, 2)
    k_obs = np.arange(12, 17)
    k_min, k_max = 12, 16
    eta_fold = [(k_max - k) / (k_max - k_min) for k in k_obs]
    colors = plt.cm.RdYlGn(np.array(eta_fold))
    ax2.bar(k_obs, eta_fold, color=colors, edgecolor='black')
    ax2.set_xlabel('Folding cycles k', fontsize=12)
    ax2.set_ylabel('η_P', fontsize=12)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')
    ax2.set_xticks(k_obs)
    ax2.grid(True, alpha=0.3, axis='y')

    # C: 3D Cellular coherence surface
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    eta1 = np.linspace(0, 1, 30)
    eta2 = np.linspace(0, 1, 30)
    E1, E2 = np.meshgrid(eta1, eta2)
    # Weighted average with w1=0.6, w2=0.4
    eta_cell = 0.6 * E1 + 0.4 * E2
    ax3.plot_surface(E1, E2, eta_cell, cmap='viridis', alpha=0.8, edgecolor='none')
    ax3.set_xlabel('η₁', fontsize=10)
    ax3.set_ylabel('η₂', fontsize=10)
    ax3.set_zlabel('η_cell', fontsize=10)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')

    # D: Coherence distribution
    ax4 = fig.add_subplot(1, 4, 4)
    np.random.seed(42)
    healthy = np.random.beta(8, 2, 500)
    diseased = np.random.beta(2, 5, 500)
    ax4.hist(healthy, bins=30, alpha=0.6, color='green', label='Healthy', density=True)
    ax4.hist(diseased, bins=30, alpha=0.6, color='red', label='Diseased', density=True)
    ax4.set_xlabel('η', fontsize=12)
    ax4.set_ylabel('Density', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def panel_3_disease_state():
    """
    Panel 3: Disease State
    - A: Disease vector radar chart
    - B: 3D disease space
    - C: Severity heatmap
    - D: Disease classification boundaries
    """
    fig = plt.figure(figsize=(16, 4))

    # A: Disease vector radar chart
    ax1 = fig.add_subplot(1, 4, 1, polar=True)
    classes = OSCILLATOR_CLASSES
    n_classes = len(classes)
    angles = np.linspace(0, 2 * np.pi, n_classes, endpoint=False).tolist()
    angles += angles[:1]

    # Example disease vectors
    healthy = [0.1, 0.05, 0.08, 0.12, 0.07, 0.1, 0.06, 0.09]
    alzheimers = [0.85, 0.2, 0.15, 0.3, 0.25, 0.18, 0.22, 0.12]
    diabetes = [0.15, 0.75, 0.12, 0.2, 0.35, 0.25, 0.3, 0.18]

    for data, label, color in [(healthy, 'Healthy', 'green'),
                                (alzheimers, "Alzheimer's", 'red'),
                                (diabetes, 'Diabetes', 'orange')]:
        values = data + data[:1]
        ax1.plot(angles, values, 'o-', linewidth=2, label=label, color=color)
        ax1.fill(angles, values, alpha=0.15, color=color)

    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels(classes, fontsize=9)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=8)

    # B: 3D disease space
    ax2 = fig.add_subplot(1, 4, 2, projection='3d')
    np.random.seed(42)
    n_samples = 100
    for cls, color in [('P', 'red'), ('E', 'blue'), ('C', 'green')]:
        idx = OSCILLATOR_CLASSES.index(cls)
        base = np.zeros(8)
        base[idx] = 0.7
        samples = np.random.normal(base, 0.15, (n_samples, 8))
        samples = np.clip(samples, 0, 1)
        ax2.scatter(samples[:, 0], samples[:, 1], samples[:, 2],
                   c=color, alpha=0.5, s=20, label=f'D_{cls}')
    ax2.set_xlabel('D_P', fontsize=10)
    ax2.set_ylabel('D_E', fontsize=10)
    ax2.set_zlabel('D_C', fontsize=10)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')
    ax2.legend(fontsize=8)

    # C: Severity heatmap
    ax3 = fig.add_subplot(1, 4, 3)
    severity_data = np.random.rand(8, 8) * 0.5 + 0.25
    for i in range(8):
        severity_data[i, i] = np.random.rand() * 0.3 + 0.7
    im = ax3.imshow(severity_data, cmap='Reds', aspect='auto', vmin=0, vmax=1)
    ax3.set_xticks(range(8))
    ax3.set_yticks(range(8))
    ax3.set_xticklabels(classes, fontsize=9)
    ax3.set_yticklabels(classes, fontsize=9)
    plt.colorbar(im, ax=ax3, label='D')
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')

    # D: Disease classification boundaries (2D projection)
    ax4 = fig.add_subplot(1, 4, 4)
    n_points = 500
    np.random.seed(123)
    D_P = np.random.rand(n_points)
    D_E = np.random.rand(n_points)
    dominant = np.where(D_P > D_E, 0, 1)
    colors = ['red' if d == 0 else 'blue' for d in dominant]
    ax4.scatter(D_P, D_E, c=colors, alpha=0.5, s=15)
    ax4.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Boundary')
    ax4.set_xlabel('D_P', fontsize=12)
    ax4.set_ylabel('D_E', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)

    plt.tight_layout()
    return fig


def panel_4_trajectory():
    """
    Panel 4: Trajectory
    - A: S-entropy trajectory paths
    - B: 3D trajectory visualization
    - C: Constraint satisfaction regions
    - D: Trajectory interpolation
    """
    fig = plt.figure(figsize=(16, 4))

    # A: S-entropy trajectory paths (2D projection)
    ax1 = fig.add_subplot(1, 4, 1)
    t = np.linspace(0, 1, 100)
    # Multiple trajectory examples
    for i, (amp, phase) in enumerate([(0.2, 0), (0.15, np.pi/4), (0.25, np.pi/2)]):
        s_k = 0.8 * (1 - t) + 0.2 * t + amp * np.sin(4 * np.pi * t + phase)
        s_t = 0.7 * (1 - t) + 0.3 * t + amp * np.sin(4 * np.pi * t + phase + np.pi/3)
        s_k = np.clip(s_k, 0, 1)
        s_t = np.clip(s_t, 0, 1)
        ax1.plot(s_k, s_t, linewidth=2, alpha=0.8, label=f'γ_{i+1}')
    ax1.plot([0.8], [0.7], 'go', markersize=10, label='Initial')
    ax1.plot([0.2], [0.3], 'rs', markersize=10, label='Final')
    ax1.set_xlabel('S_k', fontsize=12)
    ax1.set_ylabel('S_t', fontsize=12)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.legend(fontsize=8)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)

    # B: 3D trajectory visualization
    ax2 = fig.add_subplot(1, 4, 2, projection='3d')
    t = np.linspace(0, 1, 100)
    s_k = 0.8 * (1 - t) + 0.2 * t
    s_t = 0.7 * (1 - t) + 0.3 * t
    s_e = 0.6 * (1 - t) + 0.4 * t + 0.1 * np.sin(6 * np.pi * t)
    ax2.plot(s_k, s_t, s_e, 'b-', linewidth=2.5)
    ax2.scatter([0.8], [0.7], [0.6], c='green', s=100, marker='o')
    ax2.scatter([0.2], [0.3], [0.4], c='red', s=100, marker='s')
    # Draw the S-entropy cube
    for i in [0, 1]:
        for j in [0, 1]:
            ax2.plot([i, i], [j, j], [0, 1], 'k-', alpha=0.2)
            ax2.plot([i, i], [0, 1], [j, j], 'k-', alpha=0.2)
            ax2.plot([0, 1], [i, i], [j, j], 'k-', alpha=0.2)
    ax2.set_xlabel('S_k', fontsize=10)
    ax2.set_ylabel('S_t', fontsize=10)
    ax2.set_zlabel('S_e', fontsize=10)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')

    # C: Constraint satisfaction regions
    ax3 = fig.add_subplot(1, 4, 3)
    x = np.linspace(0, 1, 100)
    y = np.linspace(0, 1, 100)
    X, Y = np.meshgrid(x, y)
    # Bounded constraint
    bounded = (X >= 0) & (X <= 1) & (Y >= 0) & (Y <= 1)
    # Smooth constraint (simplified as distance from diagonal)
    smooth = np.abs(X - Y) < 0.4
    # Energy constraint
    energy = X**2 + Y**2 < 0.8

    combined = bounded.astype(int) + smooth.astype(int) + energy.astype(int)
    im = ax3.contourf(X, Y, combined, levels=[0, 1, 2, 3], cmap='YlGn', alpha=0.8)
    plt.colorbar(im, ax=ax3, label='# Constraints')
    ax3.set_xlabel('S_k', fontsize=12)
    ax3.set_ylabel('S_t', fontsize=12)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')

    # D: Trajectory interpolation
    ax4 = fig.add_subplot(1, 4, 4)
    t_interp = np.linspace(0, 1, 11)
    p1 = np.array([0.8, 0.7, 0.6])
    p2 = np.array([0.2, 0.3, 0.4])
    for i, t in enumerate(t_interp):
        p = (1 - t) * p1 + t * p2
        color = plt.cm.coolwarm(t)
        ax4.scatter(t, p[0], c=[color], s=60, marker='o')
        ax4.scatter(t, p[1], c=[color], s=60, marker='s')
        ax4.scatter(t, p[2], c=[color], s=60, marker='^')
    ax4.plot(t_interp, (1 - t_interp) * p1[0] + t_interp * p2[0], 'o--', alpha=0.5, label='S_k')
    ax4.plot(t_interp, (1 - t_interp) * p1[1] + t_interp * p2[1], 's--', alpha=0.5, label='S_t')
    ax4.plot(t_interp, (1 - t_interp) * p1[2] + t_interp * p2[2], '^--', alpha=0.5, label='S_e')
    ax4.set_xlabel('t', fontsize=12)
    ax4.set_ylabel('S coordinate', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def panel_5_therapeutic():
    """
    Panel 5: Therapeutic
    - A: Efficacy curves
    - B: Treatment response trajectories
    - C: 3D efficacy surface
    - D: Combination therapy heatmap
    """
    fig = plt.figure(figsize=(16, 4))

    # A: Efficacy curves
    ax1 = fig.add_subplot(1, 4, 1)
    eta_untreated = np.linspace(0.1, 0.9, 100)
    for E, label, color in [(0.3, 'Low', 'red'), (0.6, 'Medium', 'orange'), (0.9, 'High', 'green')]:
        eta_treated = eta_untreated + E * (1 - eta_untreated)
        ax1.plot(eta_untreated, eta_treated, linewidth=2, label=f'E={E}', color=color)
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='No effect')
    ax1.set_xlabel('η_untreated', fontsize=12)
    ax1.set_ylabel('η_treated', fontsize=12)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)

    # B: Treatment response trajectories
    ax2 = fig.add_subplot(1, 4, 2)
    time = np.linspace(0, 10, 100)
    baseline = 0.4
    for tau, label in [(1, 'Fast'), (3, 'Medium'), (7, 'Slow')]:
        response = baseline + (0.95 - baseline) * (1 - np.exp(-time / tau))
        ax2.plot(time, response, linewidth=2, label=label)
    ax2.axhline(0.4, color='gray', linestyle='--', alpha=0.5, label='Baseline')
    ax2.axhline(0.95, color='green', linestyle='--', alpha=0.5, label='Target')
    ax2.set_xlabel('Time (a.u.)', fontsize=12)
    ax2.set_ylabel('η', fontsize=12)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1)

    # C: 3D efficacy surface
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    eta_u = np.linspace(0.1, 0.8, 30)
    E = np.linspace(0, 1, 30)
    EU, EE = np.meshgrid(eta_u, E)
    eta_treated = EU + EE * (1 - EU)
    efficacy_gain = eta_treated - EU
    ax3.plot_surface(EU, EE, efficacy_gain, cmap='plasma', alpha=0.8, edgecolor='none')
    ax3.set_xlabel('η_untreated', fontsize=10)
    ax3.set_ylabel('E', fontsize=10)
    ax3.set_zlabel('Δη', fontsize=10)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')

    # D: Combination therapy heatmap
    ax4 = fig.add_subplot(1, 4, 4)
    E1 = np.linspace(0, 1, 50)
    E2 = np.linspace(0, 1, 50)
    E1_grid, E2_grid = np.meshgrid(E1, E2)
    # Synergistic combination: E_combined > E1 + E2 - E1*E2
    E_combined = E1_grid + E2_grid - 0.3 * E1_grid * E2_grid
    E_combined = np.clip(E_combined, 0, 1)
    im = ax4.contourf(E1_grid, E2_grid, E_combined, levels=20, cmap='viridis')
    plt.colorbar(im, ax=ax4, label='E_combined')
    ax4.contour(E1_grid, E2_grid, E_combined, levels=[0.5, 0.7, 0.9], colors='white', linewidths=1)
    ax4.set_xlabel('E₁', fontsize=12)
    ax4.set_ylabel('E₂', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')

    plt.tight_layout()
    return fig


def generate_all_panels():
    """Generate all 5 panels for paper 1."""
    output_dir = ensure_output_dir()

    panels = [
        ('panel1_partition_geometry.pdf', panel_1_partition_geometry),
        ('panel2_coherence.pdf', panel_2_coherence),
        ('panel3_disease_state.pdf', panel_3_disease_state),
        ('panel4_trajectory.pdf', panel_4_trajectory),
        ('panel5_therapeutic.pdf', panel_5_therapeutic),
    ]

    for filename, panel_func in panels:
        print(f"Generating {filename}...")
        fig = panel_func()
        fig.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
        fig.savefig(output_dir / filename.replace('.pdf', '.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved to {output_dir / filename}")

    print(f"\nAll panels saved to: {output_dir}")


if __name__ == "__main__":
    generate_all_panels()

"""
Panel visualizations for disease-partition-state-equations.tex

5 panels, each with 4 charts in a row, at least one 3D chart per panel.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from syndrome.core.partition import partition_capacity, categorical_distance_raw, value_to_address, address_to_value
from syndrome.core.coherence import coherence_index
from syndrome.core.s_entropy import s_entropy_from_distribution
from syndrome.core.trajectory import address_precision


def ensure_output_dir():
    """Ensure output directory exists."""
    output_dir = Path(__file__).parent.parent / "publication" / "disease-state-equations" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def panel_1_partition_structure():
    """
    Panel 1: Partition Structure
    - A: Capacity growth C(n) = 2n²
    - B: 3D partition state enumeration
    - C: State count per shell
    - D: Cumulative capacity
    """
    fig = plt.figure(figsize=(16, 4))

    # A: Capacity growth
    ax1 = fig.add_subplot(1, 4, 1)
    n_vals = np.arange(1, 15)
    capacities = [partition_capacity(n) for n in n_vals]
    ax1.plot(n_vals, capacities, 'b-o', linewidth=2, markersize=6)
    ax1.fill_between(n_vals, capacities, alpha=0.3)
    # Fit curve
    n_fit = np.linspace(1, 14, 100)
    ax1.plot(n_fit, 2 * n_fit**2, 'r--', linewidth=1.5, label='C(n)=2n²')
    ax1.set_xlabel('n', fontsize=12)
    ax1.set_ylabel('C(n)', fontsize=12)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # B: 3D partition state enumeration
    ax2 = fig.add_subplot(1, 4, 2, projection='3d')
    for n in range(1, 4):
        for ell in range(n):
            for m in range(-ell, ell + 1):
                for s in (-0.5, 0.5):
                    color = 'blue' if s > 0 else 'red'
                    alpha = 0.3 + 0.2 * n
                    ax2.scatter(n, ell, m, c=color, s=40, alpha=alpha)
    ax2.set_xlabel('n', fontsize=10)
    ax2.set_ylabel('ℓ', fontsize=10)
    ax2.set_zlabel('m', fontsize=10)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')

    # C: State count per shell (broken down by ell)
    ax3 = fig.add_subplot(1, 4, 3)
    n_vals = range(1, 7)
    bottom = np.zeros(len(n_vals))
    colors = plt.cm.viridis(np.linspace(0, 1, 6))
    for ell in range(6):
        counts = []
        for n in n_vals:
            if ell < n:
                counts.append(2 * (2 * ell + 1))  # 2 for spin, 2*ell+1 for m values
            else:
                counts.append(0)
        ax3.bar(n_vals, counts, bottom=bottom, label=f'ℓ={ell}', color=colors[ell], edgecolor='black')
        bottom += np.array(counts)
    ax3.set_xlabel('n', fontsize=12)
    ax3.set_ylabel('States', fontsize=12)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')
    ax3.legend(fontsize=8, ncol=2)

    # D: Cumulative capacity
    ax4 = fig.add_subplot(1, 4, 4)
    n_vals = np.arange(1, 12)
    cum_capacity = np.cumsum([partition_capacity(n) for n in n_vals])
    ax4.fill_between(n_vals, cum_capacity, alpha=0.4, color='steelblue')
    ax4.plot(n_vals, cum_capacity, 'o-', linewidth=2, markersize=6, color='navy')
    # Analytical form: sum of 2k² from k=1 to n = n(n+1)(2n+1)/3
    n_fit = np.linspace(1, 11, 100)
    analytic = n_fit * (n_fit + 1) * (2 * n_fit + 1) / 3
    ax4.plot(n_fit, analytic, 'r--', linewidth=1.5, label='Σ C(k)')
    ax4.set_xlabel('n', fontsize=12)
    ax4.set_ylabel('Cumulative C', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def panel_2_s_entropy():
    """
    Panel 2: S-Entropy Space
    - A: 3D S-entropy cube with sample points
    - B: Entropy distance contours
    - C: Shannon entropy curve
    - D: S-entropy metric properties
    """
    fig = plt.figure(figsize=(16, 4))

    # A: 3D S-entropy cube
    ax1 = fig.add_subplot(1, 4, 1, projection='3d')

    # Draw cube edges
    for i in [0, 1]:
        for j in [0, 1]:
            ax1.plot([i, i], [j, j], [0, 1], 'k-', alpha=0.3)
            ax1.plot([i, i], [0, 1], [j, j], 'k-', alpha=0.3)
            ax1.plot([0, 1], [i, i], [j, j], 'k-', alpha=0.3)

    # Sample points in entropy space
    np.random.seed(42)
    n_points = 100
    points = np.random.rand(n_points, 3)
    colors = np.linalg.norm(points, axis=1)  # Color by total entropy
    ax1.scatter(points[:, 0], points[:, 1], points[:, 2], c=colors, cmap='plasma', s=20, alpha=0.6)
    ax1.set_xlabel('S_k', fontsize=10)
    ax1.set_ylabel('S_t', fontsize=10)
    ax1.set_zlabel('S_e', fontsize=10)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')

    # B: Entropy distance contours (from origin)
    ax2 = fig.add_subplot(1, 4, 2)
    x = np.linspace(0, 1, 100)
    y = np.linspace(0, 1, 100)
    X, Y = np.meshgrid(x, y)
    # Distance from origin in 2D projection
    D = np.sqrt(X**2 + Y**2)
    contours = ax2.contourf(X, Y, D, levels=20, cmap='viridis')
    plt.colorbar(contours, ax=ax2, label='d(S, 0)')
    ax2.contour(X, Y, D, levels=[0.5, 1.0, 1.4], colors='white', linewidths=1)
    ax2.set_xlabel('S_k', fontsize=12)
    ax2.set_ylabel('S_t', fontsize=12)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')

    # C: Shannon entropy curve
    ax3 = fig.add_subplot(1, 4, 3)
    p = np.linspace(0.01, 0.99, 100)
    # Binary entropy H(p) = -p*log(p) - (1-p)*log(1-p)
    H = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
    ax3.plot(p, H, 'b-', linewidth=2.5)
    ax3.fill_between(p, H, alpha=0.3)
    ax3.axvline(0.5, color='r', linestyle='--', alpha=0.5)
    ax3.axhline(1.0, color='gray', linestyle='--', alpha=0.5)
    ax3.set_xlabel('p', fontsize=12)
    ax3.set_ylabel('H(p)', fontsize=12)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1.1)

    # D: S-entropy metric (triangle inequality verification)
    ax4 = fig.add_subplot(1, 4, 4)
    np.random.seed(123)
    n_trials = 200
    ratios = []
    for _ in range(n_trials):
        p1 = np.random.rand(3)
        p2 = np.random.rand(3)
        p3 = np.random.rand(3)
        d12 = np.linalg.norm(p1 - p2)
        d23 = np.linalg.norm(p2 - p3)
        d13 = np.linalg.norm(p1 - p3)
        # Ratio should be <= 1 for triangle inequality
        ratio = d13 / (d12 + d23 + 1e-10)
        ratios.append(ratio)

    ax4.hist(ratios, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
    ax4.axvline(1.0, color='red', linestyle='--', linewidth=2, label='Bound')
    ax4.set_xlabel('d(A,C) / (d(A,B) + d(B,C))', fontsize=11)
    ax4.set_ylabel('Count', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def panel_3_address_resolution():
    """
    Panel 3: Address Resolution
    - A: Precision scaling (log plot)
    - B: 3D address space partitioning
    - C: Ternary encoding visualization
    - D: Resolution convergence
    """
    fig = plt.figure(figsize=(16, 4))

    # A: Precision scaling
    ax1 = fig.add_subplot(1, 4, 1)
    depths = np.arange(1, 20)
    precisions = [address_precision(d) for d in depths]
    ax1.semilogy(depths, precisions, 'b-o', markersize=6, linewidth=2)
    ax1.fill_between(depths, precisions, alpha=0.3)
    ax1.set_xlabel('Depth k', fontsize=12)
    ax1.set_ylabel('Precision 1/3^k', fontsize=12)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.grid(True, alpha=0.3)

    # B: 3D address space partitioning
    ax2 = fig.add_subplot(1, 4, 2, projection='3d')
    # Show ternary subdivision at depth 2
    for t0 in range(3):
        for t1 in range(3):
            x = t0 / 3 + t1 / 9 + 1/18
            for t2 in range(3):
                y = t2 / 3 + 1/6
                z = (t0 + t1 + t2) / 9
                color = plt.cm.tab10((t0 * 3 + t1) % 10)
                ax2.scatter(x, y, z, c=[color], s=50, alpha=0.7)

    ax2.set_xlabel('Coord 1', fontsize=10)
    ax2.set_ylabel('Coord 2', fontsize=10)
    ax2.set_zlabel('Coord 3', fontsize=10)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')

    # C: Ternary encoding visualization
    ax3 = fig.add_subplot(1, 4, 3)
    # Show interval subdivision
    levels = 4
    y_pos = 0
    for level in range(levels):
        n_intervals = 3**level
        width = 1 / n_intervals
        for i in range(n_intervals):
            color = plt.cm.Set3(i % 12)
            ax3.barh(y_pos, width, left=i * width, height=0.8, color=color, edgecolor='black')
        y_pos += 1

    ax3.set_yticks(range(levels))
    ax3.set_yticklabels([f'k={k}' for k in range(levels)])
    ax3.set_xlabel('Value range [0, 1]', fontsize=12)
    ax3.set_ylabel('Depth', fontsize=12)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')
    ax3.set_xlim(0, 1)

    # D: Resolution convergence
    ax4 = fig.add_subplot(1, 4, 4)
    target = 0.7182818  # e - 2 (arbitrary target)
    depths = range(1, 15)
    errors = []
    for d in depths:
        address = value_to_address(target, d, 0.0, 1.0)
        resolved = address_to_value(address, 0.0, 1.0)
        errors.append(abs(target - resolved))

    ax4.semilogy(list(depths), errors, 'ro-', markersize=6, linewidth=2)
    ax4.fill_between(list(depths), errors, alpha=0.3, color='red')
    theoretical = [1/3**d for d in depths]
    ax4.semilogy(list(depths), theoretical, 'b--', linewidth=1.5, label='1/3^k bound')
    ax4.set_xlabel('Address depth', fontsize=12)
    ax4.set_ylabel('|error|', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def panel_4_coherence_disease():
    """
    Panel 4: Coherence-Disease Mapping
    - A: η to D transformation
    - B: 3D mapping surface
    - C: Boundary regions
    - D: Phase transition curves
    """
    fig = plt.figure(figsize=(16, 4))

    # A: η to D transformation
    ax1 = fig.add_subplot(1, 4, 1)
    eta = np.linspace(0, 1, 100)
    D = 1 - eta
    ax1.plot(eta, D, 'b-', linewidth=3)
    ax1.fill_between(eta, D, alpha=0.3)
    ax1.plot([0, 1], [1, 0], 'r--', alpha=0.5)  # Identity line
    ax1.axhline(0.5, color='gray', linestyle=':', alpha=0.5)
    ax1.axvline(0.5, color='gray', linestyle=':', alpha=0.5)
    ax1.set_xlabel('η (Coherence)', fontsize=12)
    ax1.set_ylabel('D (Disease)', fontsize=12)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)

    # B: 3D mapping surface (two coherences to disease)
    ax2 = fig.add_subplot(1, 4, 2, projection='3d')
    eta1 = np.linspace(0, 1, 30)
    eta2 = np.linspace(0, 1, 30)
    E1, E2 = np.meshgrid(eta1, eta2)
    # Composite disease from two coherences
    D_composite = np.sqrt((1 - E1)**2 + (1 - E2)**2) / np.sqrt(2)
    surf = ax2.plot_surface(E1, E2, D_composite, cmap='RdYlGn_r', alpha=0.8, edgecolor='none')
    ax2.set_xlabel('η₁', fontsize=10)
    ax2.set_ylabel('η₂', fontsize=10)
    ax2.set_zlabel('D', fontsize=10)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')

    # C: Boundary regions (disease classification)
    ax3 = fig.add_subplot(1, 4, 3)
    x = np.linspace(0, 1, 200)
    y = np.linspace(0, 1, 200)
    X, Y = np.meshgrid(x, y)
    # Healthy region: both D_1, D_2 < 0.3
    D1, D2 = 1 - X, 1 - Y
    region = np.zeros_like(X)
    region[(D1 < 0.3) & (D2 < 0.3)] = 0  # Healthy
    region[(D1 >= 0.3) & (D1 > D2)] = 1  # Disease type 1
    region[(D2 >= 0.3) & (D2 >= D1)] = 2  # Disease type 2

    im = ax3.contourf(X, Y, region, levels=[-0.5, 0.5, 1.5, 2.5], colors=['green', 'red', 'blue'], alpha=0.6)
    ax3.contour(X, Y, region, levels=[0.5, 1.5], colors='black', linewidths=2)
    ax3.set_xlabel('η₁', fontsize=12)
    ax3.set_ylabel('η₂', fontsize=12)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)

    # D: Phase transition curves
    ax4 = fig.add_subplot(1, 4, 4)
    # Sigmoidal transition as function of stress/damage parameter
    stress = np.linspace(0, 10, 100)
    for k, label in [(1, 'Sharp'), (2, 'Moderate'), (5, 'Gradual')]:
        eta = 1 / (1 + np.exp((stress - 5) / k))
        ax4.plot(stress, eta, linewidth=2, label=label)
    ax4.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    ax4.axvline(5, color='gray', linestyle='--', alpha=0.5)
    ax4.set_xlabel('Stress parameter', fontsize=12)
    ax4.set_ylabel('η', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1)

    plt.tight_layout()
    return fig


def panel_5_thermodynamic():
    """
    Panel 5: Thermodynamic Connections
    - A: Entropy-coherence relationship
    - B: Free energy analog
    - C: 3D thermodynamic surface
    - D: Partition function scaling
    """
    fig = plt.figure(figsize=(16, 4))

    # A: Entropy-coherence relationship
    ax1 = fig.add_subplot(1, 4, 1)
    eta = np.linspace(0.01, 0.99, 100)
    # Entropy decreases with coherence
    S = -eta * np.log(eta) - (1 - eta) * np.log(1 - eta)
    S = S / np.max(S)  # Normalize
    ax1.plot(eta, S, 'b-', linewidth=2.5)
    ax1.fill_between(eta, S, alpha=0.3)
    ax1.set_xlabel('η', fontsize=12)
    ax1.set_ylabel('S(η)', fontsize=12)
    ax1.set_title('A', fontsize=14, fontweight='bold', loc='left')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)

    # B: Free energy analog F = -T*ln(Z)
    ax2 = fig.add_subplot(1, 4, 2)
    T = np.linspace(0.1, 5, 100)
    # Simple two-state partition function
    E0, E1 = 0, 1
    Z = np.exp(-E0/T) + np.exp(-E1/T)
    F = -T * np.log(Z)
    ax2.plot(T, F, 'r-', linewidth=2.5)
    ax2.fill_between(T, F, alpha=0.3, color='red')
    ax2.set_xlabel('T (temperature)', fontsize=12)
    ax2.set_ylabel('F (free energy)', fontsize=12)
    ax2.set_title('B', fontsize=14, fontweight='bold', loc='left')
    ax2.grid(True, alpha=0.3)

    # C: 3D thermodynamic surface
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    T_vals = np.linspace(0.5, 5, 30)
    E_vals = np.linspace(0, 2, 30)
    T_grid, E_grid = np.meshgrid(T_vals, E_vals)
    # Boltzmann distribution
    P = np.exp(-E_grid / T_grid)
    P = P / P.sum(axis=0, keepdims=True)  # Normalize per temperature
    ax3.plot_surface(T_grid, E_grid, P, cmap='coolwarm', alpha=0.8, edgecolor='none')
    ax3.set_xlabel('T', fontsize=10)
    ax3.set_ylabel('E', fontsize=10)
    ax3.set_zlabel('P(E)', fontsize=10)
    ax3.set_title('C', fontsize=14, fontweight='bold', loc='left')

    # D: Partition function scaling
    ax4 = fig.add_subplot(1, 4, 4)
    n_states = np.arange(2, 51)
    T_fixed = 1.0
    # Z scales with number of accessible states
    Z_vals = []
    for N in n_states:
        energies = np.linspace(0, 1, N)
        Z = np.sum(np.exp(-energies / T_fixed))
        Z_vals.append(Z)

    ax4.plot(n_states, Z_vals, 'g-o', markersize=4, linewidth=2)
    ax4.fill_between(n_states, Z_vals, alpha=0.3, color='green')
    ax4.plot(n_states, n_states * 0.63, 'r--', label='~N scaling')  # approx e^(-0.5)
    ax4.set_xlabel('N (states)', fontsize=12)
    ax4.set_ylabel('Z(T)', fontsize=12)
    ax4.set_title('D', fontsize=14, fontweight='bold', loc='left')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def generate_all_panels():
    """Generate all 5 panels for paper 2."""
    output_dir = ensure_output_dir()

    panels = [
        ('panel1_partition_structure.pdf', panel_1_partition_structure),
        ('panel2_s_entropy.pdf', panel_2_s_entropy),
        ('panel3_address_resolution.pdf', panel_3_address_resolution),
        ('panel4_coherence_disease.pdf', panel_4_coherence_disease),
        ('panel5_thermodynamic.pdf', panel_5_thermodynamic),
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

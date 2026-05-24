#!/usr/bin/env python3
"""
Generate 6 visualization panels for template-matching theory validation.
Each panel has 4 charts: 3 2D + 1 3D
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.gridspec import GridSpec
import json

# Load validation results
with open(r"c:\Users\kunda\Documents\health\syndrome\diseases\social-mechanics\validation_results.json") as f:
    results = json.load(f)

# Global figure settings
plt.rcParams['font.size'] = 9
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

# ============================================================================
# PANEL 1: Exploitation via Overlap
# ============================================================================

def create_panel_1():
    fig = plt.figure(figsize=(16, 4))
    fig.patch.set_facecolor('white')
    gs = GridSpec(1, 4, figure=fig, wspace=0.35, hspace=0.3)

    exp_data = results['experiments'][0]

    # Chart 1: Exploitation rates
    ax1 = fig.add_subplot(gs[0, 0])
    templates = [t['template'] for t in exp_data['tests']]
    rates = [t['exploitation_rate'] for t in exp_data['tests']]
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    ax1.bar(range(len(templates)), rates, color=colors, width=0.6, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Exploitation Rate', fontsize=10, fontweight='bold')
    ax1.set_xticks(range(len(templates)))
    ax1.set_xticklabels(['Perfect', 'Partial', 'Mismatch'], fontsize=9)
    ax1.set_ylim(0, max(rates) * 1.2)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Chart 2: Overlap values
    ax2 = fig.add_subplot(gs[0, 1])
    overlaps = [t['overlap'] for t in exp_data['tests']]
    ax2.plot(range(len(templates)), overlaps, 'o-', color='#2E86AB', linewidth=2.5, markersize=9, markeredgecolor='black', markeredgewidth=1.5)
    ax2.fill_between(range(len(templates)), overlaps, alpha=0.3, color='#2E86AB')
    ax2.set_ylabel('Overlap Integral', fontsize=10, fontweight='bold')
    ax2.set_xticks(range(len(templates)))
    ax2.set_xticklabels(['Perfect', 'Partial', 'Mismatch'], fontsize=9)
    ax2.set_ylim(0, max(overlaps) * 1.2)
    ax2.grid(alpha=0.3, linestyle='--')

    # Chart 3: Proportionality ratio
    ax3 = fig.add_subplot(gs[0, 2])
    ratio_data = exp_data['proportionality_test']
    categories = ['Observed\nRatio', 'Expected\nRatio']
    values = [ratio_data['ratio_perfect_to_partial'], ratio_data['expected_approximately']]
    bars = ax3.bar(categories, values, color=['#A23B72', '#2E86AB'], width=0.5, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Rate Ratio', fontsize=10, fontweight='bold')
    ax3.set_ylim(0, 2.5)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    for i, (bar, val) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height, f'{val:.2f}', ha='center', va='bottom', fontweight='bold')

    # Chart 4: 3D - Overlap surface
    ax4 = fig.add_subplot(gs[0, 3], projection='3d')
    template_space = np.linspace(0, 1, 30)
    state_space = np.linspace(0, 1, 30)
    X, Y = np.meshgrid(template_space, state_space)
    Z = np.exp(-((X - 0.5)**2 + (Y - 0.5)**2) * 20)

    surf = ax4.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8, edgecolor='none')
    ax4.set_xlabel('Template', fontsize=8)
    ax4.set_ylabel('Agent State', fontsize=8)
    ax4.set_zlabel('Overlap', fontsize=8)
    ax4.view_init(elev=25, azim=45)
    ax4.grid(False)

    plt.suptitle('Theorem 1: Exploitation via Overlap Integral', fontsize=12, fontweight='bold', y=1.02)
    return fig

# ============================================================================
# PANEL 2: Template Convergence
# ============================================================================

def create_panel_2():
    fig = plt.figure(figsize=(16, 4))
    fig.patch.set_facecolor('white')
    gs = GridSpec(1, 4, figure=fig, wspace=0.35, hspace=0.3)

    exp_data = results['experiments'][1]

    generations = [t['generation'] for t in exp_data['convergence_trace']]
    template_locs = [t['template_location'] for t in exp_data['convergence_trace']]
    overlaps = [t['overlap_with_agent_state'] for t in exp_data['convergence_trace']]

    # Chart 1: Template location drift
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(generations, template_locs, 'o-', color='#2E86AB', linewidth=2.5, markersize=6, markeredgecolor='black', markeredgewidth=1)
    ax1.fill_between(generations, template_locs, alpha=0.3, color='#2E86AB')
    ax1.axhline(y=0.5, color='red', linestyle='--', linewidth=1.5, label='Bimodal Center', alpha=0.7)
    ax1.set_ylabel('Template Location', fontsize=10, fontweight='bold')
    ax1.set_xlabel('Generation', fontsize=10, fontweight='bold')
    ax1.set_ylim(0.4, 0.9)
    ax1.grid(alpha=0.3, linestyle='--')
    ax1.legend(fontsize=8, loc='lower right')

    # Chart 2: Overlap evolution
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(generations, overlaps, 's-', color='#A23B72', linewidth=2.5, markersize=6, markeredgecolor='black', markeredgewidth=1)
    ax2.fill_between(generations, overlaps, alpha=0.3, color='#A23B72')
    ax2.set_ylabel('Overlap with Agent State', fontsize=10, fontweight='bold')
    ax2.set_xlabel('Generation', fontsize=10, fontweight='bold')
    ax2.grid(alpha=0.3, linestyle='--')

    # Chart 3: Convergence rate (derivative)
    ax3 = fig.add_subplot(gs[0, 2])
    convergence_rate = np.diff(template_locs)
    ax3.bar(generations[:-1], convergence_rate, color='#F18F01', alpha=0.7, edgecolor='black', linewidth=1.5, width=0.8)
    ax3.set_ylabel('Template Drift Rate', fontsize=10, fontweight='bold')
    ax3.set_xlabel('Generation', fontsize=10, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

    # Chart 4: 3D - Convergence trajectory
    ax4 = fig.add_subplot(gs[0, 3], projection='3d')
    generations_arr = np.array(generations)
    template_locs_arr = np.array(template_locs)
    overlaps_arr = np.array(overlaps)

    ax4.plot(generations_arr, template_locs_arr, overlaps_arr, 'o-', color='#2E86AB', linewidth=2.5, markersize=5, markeredgecolor='black', markeredgewidth=0.5)
    ax4.set_xlabel('Generation', fontsize=8)
    ax4.set_ylabel('Template Loc', fontsize=8)
    ax4.set_zlabel('Overlap', fontsize=8)
    ax4.view_init(elev=20, azim=45)
    ax4.grid(False)

    plt.suptitle('Theorem 2: Template Convergence via Co-Evolution', fontsize=12, fontweight='bold', y=1.02)
    return fig

# ============================================================================
# PANEL 3: Coordination Vulnerability
# ============================================================================

def create_panel_3():
    fig = plt.figure(figsize=(16, 4))
    fig.patch.set_facecolor('white')
    gs = GridSpec(1, 4, figure=fig, wspace=0.35, hspace=0.3)

    exp_data = results['experiments'][2]

    regimes = [r['regime'] for r in exp_data['regimes']]
    exploits = [r['exploitation_probability'] for r in exp_data['regimes']]
    coords = [r['coordination_value'] for r in exp_data['regimes']]
    weights = [r['weighting_function'] for r in exp_data['regimes']]

    # Chart 1: Exploitation probability by regime
    ax1 = fig.add_subplot(gs[0, 0])
    colors_grad = ['#FF6B6B', '#FFA07A', '#FFD700', '#87CEEB', '#4169E1']
    ax1.bar(range(len(regimes)), exploits, color=colors_grad, edgecolor='black', linewidth=1.5, width=0.65)
    ax1.set_ylabel('Exploitation Probability', fontsize=10, fontweight='bold')
    ax1.set_xticks(range(len(regimes)))
    ax1.set_xticklabels([r.replace('_', '\n') for r in regimes], fontsize=8)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Chart 2: Coordination weighting function
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(coords, weights, 'o-', color='#A23B72', linewidth=2.5, markersize=9, markeredgecolor='black', markeredgewidth=1.5)
    ax2.fill_between(coords, weights, alpha=0.3, color='#A23B72')
    ax2.set_ylabel('Weighting Function f(R)', fontsize=10, fontweight='bold')
    ax2.set_xlabel('Coordination Order Parameter', fontsize=10, fontweight='bold')
    ax2.set_ylim(0, 1.2)
    ax2.grid(alpha=0.3, linestyle='--')

    # Chart 3: Vulnerability ratio
    ax3 = fig.add_subplot(gs[0, 2])
    ratio_data = exp_data['vulnerability_ratio']
    ratio_obs = ratio_data['observed_ratio']
    ratio_exp = ratio_data['expected_ratio']

    categories = ['Observed', 'Expected']
    values = [ratio_obs, ratio_exp]
    bars = ax3.bar(categories, values, color=['#2E86AB', '#F18F01'], width=0.5, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Vulnerability Ratio', fontsize=10, fontweight='bold')
    ax3.set_ylim(0, 7)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height, f'{val:.2f}x', ha='center', va='bottom', fontweight='bold', fontsize=9)

    # Chart 4: 3D - Vulnerability surface
    ax4 = fig.add_subplot(gs[0, 3], projection='3d')
    coord_space = np.linspace(0, 1, 25)
    overlap_space = np.linspace(0, 3, 25)
    C, O = np.meshgrid(coord_space, overlap_space)

    # Weighting function
    W = np.where(C < 0.3, 0.2, np.where(C < 0.5, 0.4, np.where(C < 0.8, 0.6, np.where(C < 0.95, 0.8, 1.0))))
    Z = O * W

    surf = ax4.plot_surface(C, O, Z, cmap='plasma', alpha=0.8, edgecolor='none')
    ax4.set_xlabel('Coordination', fontsize=8)
    ax4.set_ylabel('Overlap', fontsize=8)
    ax4.set_zlabel('Exploit Rate', fontsize=8)
    ax4.view_init(elev=25, azim=45)
    ax4.grid(False)

    plt.suptitle('Theorem 3: Coordination-Dependent Vulnerability', fontsize=12, fontweight='bold', y=1.02)
    return fig

# ============================================================================
# PANEL 4: Age-Stratified Incidence
# ============================================================================

def create_panel_4():
    fig = plt.figure(figsize=(16, 4))
    fig.patch.set_facecolor('white')
    gs = GridSpec(1, 4, figure=fig, wspace=0.35, hspace=0.3)

    exp_data = results['experiments'][3]

    age_groups = [a['age_group'].replace('_', ' ') for a in exp_data['age_groups']]
    prevs = [a['prevalence'] for a in exp_data['age_groups']]
    overlaps = [a['overlap'] for a in exp_data['age_groups']]
    host_locs = [a['host_state_location'] for a in exp_data['age_groups']]
    coords = [a['coordination_weighting'] for a in exp_data['age_groups']]

    # Chart 1: Prevalence by age (U-shape)
    ax1 = fig.add_subplot(gs[0, 0])
    colors_u = ['#FF6B6B', '#FFB6C1', '#FFD700', '#87CEEB', '#4169E1']
    ax1.plot(range(len(age_groups)), prevs, 'o-', color='#2E86AB', linewidth=2.5, markersize=10, markeredgecolor='black', markeredgewidth=1.5)
    ax1.scatter(range(len(age_groups)), prevs, c=colors_u, s=200, edgecolors='black', linewidth=1.5, zorder=3)
    ax1.set_ylabel('Disease Prevalence', fontsize=10, fontweight='bold')
    ax1.set_xticks(range(len(age_groups)))
    ax1.set_xticklabels([a.split()[0] for a in age_groups], fontsize=8, rotation=45)
    ax1.grid(alpha=0.3, linestyle='--')
    ax1.fill_between(range(len(age_groups)), prevs, alpha=0.2, color='#2E86AB')

    # Chart 2: Template overlap by age
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(range(len(age_groups)), overlaps, 's-', color='#A23B72', linewidth=2.5, markersize=9, markeredgecolor='black', markeredgewidth=1.5)
    ax2.fill_between(range(len(age_groups)), overlaps, alpha=0.3, color='#A23B72')
    ax2.set_ylabel('Template Overlap', fontsize=10, fontweight='bold')
    ax2.set_xticks(range(len(age_groups)))
    ax2.set_xticklabels([a.split()[0] for a in age_groups], fontsize=8, rotation=45)
    ax2.grid(alpha=0.3, linestyle='--')

    # Chart 3: Host state location and coordination
    ax3 = fig.add_subplot(gs[0, 2])
    x = np.arange(len(age_groups))
    width = 0.35
    ax3.bar(x - width/2, host_locs, width, label='Host State Loc', color='#2E86AB', edgecolor='black', linewidth=1.5)
    ax3.bar(x + width/2, coords, width, label='Coordination', color='#F18F01', edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Value', fontsize=10, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([a.split()[0] for a in age_groups], fontsize=8, rotation=45)
    ax3.legend(fontsize=8)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')

    # Chart 4: 3D - Prevalence surface
    ax4 = fig.add_subplot(gs[0, 3], projection='3d')
    immune_space = np.linspace(0.1, 0.95, 20)
    adapt_space = np.linspace(0.2, 0.95, 20)
    I, A = np.meshgrid(immune_space, adapt_space)

    # Prevalence model: high when immune is low and adaptation is high
    Z = (1 - I) * A * np.exp(-((I - 0.3)**2 + (A - 0.8)**2) * 5)

    surf = ax4.plot_surface(I, A, Z, cmap='RdYlBu_r', alpha=0.8, edgecolor='none')
    ax4.set_xlabel('Immune State', fontsize=8)
    ax4.set_ylabel('Fire Adapt', fontsize=8)
    ax4.set_zlabel('Prevalence', fontsize=8)
    ax4.view_init(elev=25, azim=45)
    ax4.grid(False)

    plt.suptitle('Age-Stratified Disease Incidence (U-Shaped)', fontsize=12, fontweight='bold', y=1.02)
    return fig

# ============================================================================
# PANEL 5: Tropical Prevalence
# ============================================================================

def create_panel_5():
    fig = plt.figure(figsize=(16, 4))
    fig.patch.set_facecolor('white')
    gs = GridSpec(1, 4, figure=fig, wspace=0.35, hspace=0.3)

    exp_data = results['experiments'][4]

    regions = [r['region'].replace('_', ' ') for r in exp_data['regions']]
    settlement_years = [r['settlement_years'] for r in exp_data['regions']]
    convergence = [r['template_convergence'] for r in exp_data['regions']]
    prevs = [r['prevalence'] for r in exp_data['regions']]

    # Chart 1: Prevalence by region
    ax1 = fig.add_subplot(gs[0, 0])
    colors_reg = ['#FF6B6B', '#87CEEB', '#FFD700']
    ax1.bar(range(len(regions)), prevs, color=colors_reg, edgecolor='black', linewidth=1.5, width=0.65)
    ax1.set_ylabel('Disease Prevalence', fontsize=10, fontweight='bold')
    ax1.set_xticks(range(len(regions)))
    ax1.set_xticklabels([r.split()[0] for r in regions], fontsize=8)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Chart 2: Settlement time (log scale)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(range(len(regions)), settlement_years, color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1.5, width=0.65)
    ax2.set_ylabel('Settlement Years (log)', fontsize=10, fontweight='bold')
    ax2.set_yscale('log')
    ax2.set_xticks(range(len(regions)))
    ax2.set_xticklabels([r.split()[0] for r in regions], fontsize=8)
    ax2.grid(axis='y', alpha=0.3, linestyle='--', which='both')

    # Chart 3: Template convergence
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(range(len(regions)), convergence, 'o-', color='#A23B72', linewidth=2.5, markersize=10, markeredgecolor='black', markeredgewidth=1.5)
    ax3.fill_between(range(len(regions)), convergence, alpha=0.3, color='#A23B72')
    ax3.set_ylabel('Template Convergence', fontsize=10, fontweight='bold')
    ax3.set_xticks(range(len(regions)))
    ax3.set_xticklabels([r.split()[0] for r in regions], fontsize=8)
    ax3.set_ylim(0, 1.1)
    ax3.grid(alpha=0.3, linestyle='--')

    # Chart 4: 3D - Settlement time vs convergence vs prevalence
    ax4 = fig.add_subplot(gs[0, 3], projection='3d')
    time_space = np.logspace(4, 6, 20)
    tau_sat = 100000
    conv_space = 1 - np.exp(-time_space / tau_sat)
    prev_space = conv_space * 0.1

    # Create 3D scatter
    scatter = ax4.scatter(time_space, conv_space, prev_space, c=prev_space, cmap='viridis', s=100, edgecolors='black', linewidth=1)
    ax4.plot(time_space, conv_space, prev_space, '-', color='#2E86AB', linewidth=2, alpha=0.6)

    ax4.set_xlabel('Settlement Years', fontsize=8)
    ax4.set_ylabel('Convergence', fontsize=8)
    ax4.set_zlabel('Prevalence', fontsize=8)
    ax4.view_init(elev=25, azim=45)
    ax4.grid(False)

    plt.suptitle('Tropical Disease Prevalence via Co-Evolution Time', fontsize=12, fontweight='bold', y=1.02)
    return fig

# ============================================================================
# PANEL 6: Latency Dynamics
# ============================================================================

def create_panel_6():
    fig = plt.figure(figsize=(16, 4))
    fig.patch.set_facecolor('white')
    gs = GridSpec(1, 4, figure=fig, wspace=0.35, hspace=0.3)

    exp_data = results['experiments'][5]

    ages = [t['age'] for t in exp_data['age_trajectory']]
    overlaps = [t['overlap'] for t in exp_data['age_trajectory']]
    host_locs = [t['host_state_location'] for t in exp_data['age_trajectory']]
    statuses = [t['status'] for t in exp_data['age_trajectory']]

    threshold = 0.15  # Manifestation threshold from experiment

    # Chart 1: Overlap over lifetime with threshold
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(ages, overlaps, 'o-', color='#2E86AB', linewidth=2.5, markersize=6, markeredgecolor='black', markeredgewidth=1)
    ax1.axhline(y=threshold, color='red', linestyle='--', linewidth=2, label=f'Manifestation Threshold', alpha=0.8)
    ax1.fill_between(ages, overlaps, threshold, where=(np.array(overlaps) >= threshold), alpha=0.3, color='red', label='Active Disease')
    ax1.fill_between(ages, overlaps, threshold, where=(np.array(overlaps) < threshold), alpha=0.3, color='blue', label='Latent/Uninfected')
    ax1.set_ylabel('Template Overlap', fontsize=10, fontweight='bold')
    ax1.set_xlabel('Age (years)', fontsize=10, fontweight='bold')
    ax1.legend(fontsize=8, loc='upper left')
    ax1.grid(alpha=0.3, linestyle='--')

    # Chart 2: Status over lifetime (color coded)
    ax2 = fig.add_subplot(gs[0, 1])
    status_colors = {'latent': '#FFD700', 'active': '#FF4500', 'uninfected': '#87CEEB'}
    status_nums = [0 if s == 'uninfected' else 1 if s == 'latent' else 2 for s in statuses]
    scatter = ax2.scatter(ages, status_nums, c=[status_colors[s] for s in statuses], s=150, edgecolors='black', linewidth=1.5, alpha=0.8)
    ax2.set_ylabel('Disease Status', fontsize=10, fontweight='bold')
    ax2.set_xlabel('Age (years)', fontsize=10, fontweight='bold')
    ax2.set_yticks([0, 1, 2])
    ax2.set_yticklabels(['Uninfected', 'Latent', 'Active'], fontsize=9)
    ax2.grid(alpha=0.3, linestyle='--', axis='x')

    # Chart 3: Host state location over age
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(ages, host_locs, 's-', color='#A23B72', linewidth=2.5, markersize=6, markeredgecolor='black', markeredgewidth=1)
    ax3.fill_between(ages, host_locs, alpha=0.3, color='#A23B72')
    ax3.set_ylabel('Host State Location', fontsize=10, fontweight='bold')
    ax3.set_xlabel('Age (years)', fontsize=10, fontweight='bold')
    ax3.grid(alpha=0.3, linestyle='--')

    # Chart 4: 3D - Latency trajectory
    ax4 = fig.add_subplot(gs[0, 3], projection='3d')
    ages_arr = np.array(ages)
    overlaps_arr = np.array(overlaps)
    host_locs_arr = np.array(host_locs)

    # Color by status
    status_color_map = {'latent': '#FFD700', 'active': '#FF4500', 'uninfected': '#87CEEB'}
    colors_3d = [status_color_map[s] for s in statuses]

    ax4.scatter(ages_arr, host_locs_arr, overlaps_arr, c=colors_3d, s=80, edgecolors='black', linewidth=0.5, alpha=0.8)
    ax4.plot(ages_arr, host_locs_arr, overlaps_arr, '-', color='#2E86AB', linewidth=2, alpha=0.6)

    ax4.set_xlabel('Age', fontsize=8)
    ax4.set_ylabel('Host State', fontsize=8)
    ax4.set_zlabel('Overlap', fontsize=8)
    ax4.view_init(elev=25, azim=45)
    ax4.grid(False)

    plt.suptitle('Latent Infection and Reactivation Dynamics', fontsize=12, fontweight='bold', y=1.02)
    return fig

# ============================================================================
# GENERATE ALL PANELS
# ============================================================================

print("Generating visualization panels...")

panels = [
    ("Panel 1", create_panel_1),
    ("Panel 2", create_panel_2),
    ("Panel 3", create_panel_3),
    ("Panel 4", create_panel_4),
    ("Panel 5", create_panel_5),
    ("Panel 6", create_panel_6),
]

output_dir = r"c:\Users\kunda\Documents\health\syndrome\diseases\social-mechanics"

for name, create_func in panels:
    print(f"  Creating {name}...")
    fig = create_func()
    filename = f"{name.replace(' ', '_').lower()}.png"
    filepath = f"{output_dir}\\{filename}"
    fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"    Saved to {filename}")

print("\n[OK] All 6 visualization panels generated successfully!")
print(f"Output directory: {output_dir}")

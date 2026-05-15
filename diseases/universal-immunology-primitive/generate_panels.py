import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy import stats
from scipy.integrate import solve_ivp
from pathlib import Path

np.random.seed(42)
rng = np.random.RandomState(42)

ROOT = Path(r'c:\Users\kunda\Documents\health\syndrome\diseases\universal-immunology-primitive')
OUT = ROOT / 'panels'
OUT.mkdir(parents=True, exist_ok=True)

BLUE='#2171B5'; RED='#CB181D'; GREEN='#238B45'; ORANGE='#D94801'
PURPLE='#6A51A3'; TEAL='#1A9B8A'; GRAY='#636363'
COLORS=[BLUE,RED,GREEN,ORANGE,PURPLE,TEAL,GRAY,'#8B4513']

def clean3d(ax):
    ax.xaxis.pane.fill=False; ax.yaxis.pane.fill=False; ax.zaxis.pane.fill=False
    ax.xaxis.pane.set_edgecolor('#CCCCCC'); ax.yaxis.pane.set_edgecolor('#CCCCCC')
    ax.zaxis.pane.set_edgecolor('#CCCCCC'); ax.grid(True, alpha=0.3)

def sax(ax):
    ax.set_facecolor('white'); ax.tick_params(labelsize=8)
    for s in ['top','right']: ax.spines[s].set_visible(False)

def make_fig():
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.4))
    fig.patch.set_facecolor('white')
    plt.subplots_adjust(left=0.06, right=0.74, top=0.88, bottom=0.18, wspace=0.42)
    ax3 = fig.add_axes([0.76, 0.12, 0.22, 0.78], projection='3d')
    ax3.set_facecolor('white')
    return fig, axes, ax3

ALPHA = list('ACGT')
K = 12

def rand_seq(L, r=None):
    r = r or rng
    return ''.join(r.choice(ALPHA, L))

def mutate(seq, mu, r=None):
    r = r or rng
    s = list(seq)
    for i in range(len(s)):
        if r.random() < mu: s[i] = r.choice(ALPHA)
    return ''.join(s)

def channelize(seq):
    L = len(seq)
    X = np.zeros((4, L))
    for i, b in enumerate(seq): X[ALPHA.index(b), i] = 1.0
    X -= X.mean(axis=1, keepdims=True)
    return X

def embed(seq, k=K):
    X = channelize(seq)
    phi = []
    for c in range(4):
        phi.extend(np.abs(np.fft.rfft(X[c])[1:k+1]) / len(seq))
    phi = np.array(phi)
    n = np.linalg.norm(phi)
    return phi/n if n > 1e-10 else phi

def roc(scores_pos, scores_neg):
    all_s = np.concatenate([scores_pos, scores_neg])
    labs = np.concatenate([np.ones(len(scores_pos)), np.zeros(len(scores_neg))])
    idx = np.argsort(-all_s); labs = labs[idx]
    tp = np.cumsum(labs); fp = np.cumsum(1-labs)
    tpr = np.concatenate([[0], tp/tp[-1]]); fpr = np.concatenate([[0], fp/fp[-1]])
    return fpr, tpr, np.trapezoid(tpr, fpr)

# ============================================================
# PANEL 1: Spectral Sequence Representation
# ============================================================
print("Panel 1...")
fig, axes, ax3 = make_fig()

# A: channelised signal (first 60 bp)
seq_ref = rand_seq(200)
X = channelize(seq_ref)
x = np.arange(60)
ch_cols=[BLUE,RED,GREEN,ORANGE]; ch_labs=['A','C','G','T']
for c in range(4):
    axes[0].plot(x, X[c,:60]+c*0.5, color=ch_cols[c], lw=0.9, alpha=0.9, label=ch_labs[c])
axes[0].set_xlabel('Position (bp)',fontsize=9); axes[0].set_ylabel('Signal + offset',fontsize=9)
axes[0].set_title('Channelised Signal',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=7,loc='upper right'); sax(axes[0])

# B: DFT magnitude spectrum
freq_bins = np.arange(1, K+1)
width=0.18
for c in range(4):
    mags = np.abs(np.fft.rfft(X[c])[1:K+1]) / 200
    axes[1].bar(freq_bins + c*width - 0.27, mags, width=width, color=ch_cols[c], alpha=0.8, label=ch_labs[c])
axes[1].set_xlabel('Frequency bin $k$',fontsize=9); axes[1].set_ylabel(r'$|\hat{X}_{a,k}|/L$',fontsize=9)
axes[1].set_title('DFT Magnitude Spectrum',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=7); sax(axes[1])

# C: spectral similarity vs sequence identity
N_pairs = 300
mus_c = rng.uniform(0, 0.6, N_pairs)
sims_c = []
for mu in mus_c:
    s1 = rand_seq(100); s2 = mutate(s1, mu)
    sims_c.append(np.dot(embed(s1), embed(s2)))
seq_id = 1 - mus_c
m,b,r2,_,_ = stats.linregress(seq_id, sims_c)
x_fit = np.linspace(0.4, 1.0, 100)
axes[2].scatter(seq_id, sims_c, c=BLUE, s=7, alpha=0.4)
axes[2].plot(x_fit, m*x_fit+b, color=RED, lw=2, label=f'$r^2={r2**2:.2f}$')
axes[2].set_xlabel('Sequence Identity',fontsize=9); axes[2].set_ylabel(r'Spectral Similarity $\rho$',fontsize=9)
axes[2].set_title('Similarity vs Identity',fontsize=10,fontweight='bold')
axes[2].legend(fontsize=8); sax(axes[2])

# D: 3D family clusters
n_fam=6; n_mem=8
pts=[]; labs=[]
for f in range(n_fam):
    seed=rand_seq(100)
    for _ in range(n_mem):
        e = embed(mutate(seed, 0.10))
        pts.append(e[:3]); labs.append(f)
pts=np.array(pts); labs=np.array(labs)
clean3d(ax3)
for f in range(n_fam):
    m=labs==f; ax3.scatter(pts[m,0],pts[m,1],pts[m,2],c=COLORS[f],s=28,alpha=0.85)
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8); ax3.set_zlabel(r'$\psi_3$',fontsize=8)
ax3.set_title('Sequence Family\nClusters',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)

plt.suptitle('Spectral Representation of Biological Sequences',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel1_spectral_representation.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 2: MHC Binding Prediction
# ============================================================
print("Panel 2...")
fig, axes, ax3 = make_fig()
d_embed = 4*K  # embedding dimension

# Generate synthetic MHC groove spectrum (fixed direction in R^d)
mhc_spec = rng.randn(d_embed); mhc_spec /= np.linalg.norm(mhc_spec)

# Binders: random unit vectors within angle < 40 deg of MHC spectrum
def sample_near(center, n, sigma=0.25, r=rng):
    pts=[]
    for _ in range(n):
        v = center + r.randn(len(center))*sigma
        pts.append(v/np.linalg.norm(v))
    return np.array(pts)

n_bind=200; n_nonbind=200
binders = sample_near(mhc_spec, n_bind, sigma=0.3)
nonbinders = np.array([r/np.linalg.norm(r) for r in rng.randn(n_nonbind, d_embed)])

rho_bind = binders @ mhc_spec
rho_nonb = nonbinders @ mhc_spec

# A: overlaid histograms
bins=np.linspace(-0.2,1.0,30)
axes[0].hist(rho_nonb, bins=bins, color=RED, alpha=0.7, label='Non-binders', density=True)
axes[0].hist(rho_bind, bins=bins, color=BLUE, alpha=0.7, label='Binders', density=True)
axes[0].axvline(0.5, color=GRAY, ls='--', lw=1.5, label=r'$\rho^*=0.5$')
axes[0].set_xlabel(r'Spectral Similarity $\rho$',fontsize=9); axes[0].set_ylabel('Density',fontsize=9)
axes[0].set_title('MHC Binding Score Distribution',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=7); sax(axes[0])

# B: ROC curve
fpr, tpr, auc = roc(rho_bind, rho_nonb)
axes[1].plot(fpr, tpr, color=BLUE, lw=2, label=f'AUC={auc:.3f}')
axes[1].plot([0,1],[0,1], color=GRAY, ls='--', lw=1)
axes[1].set_xlabel('False Positive Rate',fontsize=9); axes[1].set_ylabel('True Positive Rate',fontsize=9)
axes[1].set_title('ROC: MHC Binding Prediction',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=8); sax(axes[1])

# C: binding ball radius r* = sqrt(2*(1-rho*)) vs rho*
rho_star = np.linspace(0.1, 0.99, 100)
r_star = np.sqrt(2*(1-rho_star))
axes[2].plot(rho_star, r_star, color=GREEN, lw=2)
axes[2].fill_between(rho_star, r_star, alpha=0.15, color=GREEN)
axes[2].axvline(0.5, color=RED, ls='--', lw=1.5, label=r'$\rho^*=0.5$')
axes[2].set_xlabel(r'Binding Threshold $\rho^*$',fontsize=9); axes[2].set_ylabel(r'Ball Radius $r^*=\sqrt{2(1-\rho^*)}$',fontsize=9)
axes[2].set_title('Binding Ball Radius',fontsize=10,fontweight='bold')
axes[2].legend(fontsize=8); sax(axes[2])

# D: 3D scatter binders vs non-binders
clean3d(ax3)
ax3.scatter(binders[:80,0],binders[:80,1],binders[:80,2],c=BLUE,s=20,alpha=0.7,label='Binders')
ax3.scatter(nonbinders[:80,0],nonbinders[:80,1],nonbinders[:80,2],c=RED,s=10,alpha=0.4,label='Non-binders')
ax3.scatter([mhc_spec[0]],[mhc_spec[1]],[mhc_spec[2]],c=ORANGE,s=120,marker='*',zorder=10)
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8); ax3.set_zlabel(r'$\psi_3$',fontsize=8)
ax3.set_title('Peptide Embedding\nSpace',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('MHC-Peptide Binding Prediction via Spectral Interference',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel2_mhc_binding.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 3: TCR Cross-reactivity
# ============================================================
print("Panel 3...")
fig, axes, ax3 = make_fig()

# TCR spectrum: fixed direction
tcr_spec = rng.randn(d_embed); tcr_spec /= np.linalg.norm(tcr_spec)

# Self-peptidome: 500 random self-peptides, compute spectra
n_self = 500
self_specs = np.array([r/np.linalg.norm(r) for r in rng.randn(n_self, d_embed)])
rho_self_tcr = self_specs @ tcr_spec

# Random foreign peptides
n_foreign = 2000
foreign_specs = np.array([r/np.linalg.norm(r) for r in rng.randn(n_foreign, d_embed)])
rho_foreign_tcr = foreign_specs @ tcr_spec

# A: distribution of rho(random_peptide, TCR)
thresholds = np.linspace(0.2, 0.9, 200)
bins2 = np.linspace(-0.5, 1.0, 40)
axes[0].hist(rho_foreign_tcr, bins=bins2, color=BLUE, alpha=0.75, density=True, label='Random peptides')
axes[0].axvline(0.5, color=RED, ls='--', lw=1.5, label=r'$\theta_{act}=0.5$')
cross_frac = np.mean(rho_foreign_tcr > 0.5)
axes[0].set_xlabel(r'$\rho$(peptide, TCR)',fontsize=9); axes[0].set_ylabel('Density',fontsize=9)
axes[0].set_title('TCR Interference Score\nDistribution',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=7); sax(axes[0])

# B: cross-reactive fraction vs threshold
cross_fracs = [np.mean(rho_foreign_tcr > th) for th in thresholds]
axes[1].semilogy(thresholds, cross_fracs, color=PURPLE, lw=2)
axes[1].axvline(0.5, color=RED, ls='--', lw=1.5)
axes[1].set_xlabel(r'Activation Threshold $\theta_{act}$',fontsize=9)
axes[1].set_ylabel('Cross-reactive Fraction',fontsize=9)
axes[1].set_title('Cross-reactivity vs Threshold',fontsize=10,fontweight='bold'); sax(axes[1])

# C: self-tolerance band (rho_self distribution with deletion threshold)
axes[2].hist(rho_self_tcr, bins=30, color=GREEN, alpha=0.75, density=True, label='Self-peptide TCR scores')
theta_del = 0.7
axes[2].axvline(theta_del, color=RED, ls='--', lw=2, label=r'$\theta_{del}=0.7$')
axes[2].axvspan(theta_del, 1.0, color=RED, alpha=0.1, label='Deletion zone')
axes[2].set_xlabel(r'$\rho$(self-pMHC, TCR)',fontsize=9); axes[2].set_ylabel('Density',fontsize=9)
axes[2].set_title('Self-Tolerance Exclusion Band',fontsize=10,fontweight='bold')
axes[2].legend(fontsize=7); sax(axes[2])

# D: 3D scatter — foreign peptides (blue), self-excluded (red), cross-reactive (green)
clean3d(ax3)
cr_mask = rho_foreign_tcr > 0.5
ax3.scatter(foreign_specs[~cr_mask,:3][:,0],foreign_specs[~cr_mask,:3][:,1],foreign_specs[~cr_mask,:3][:,2],
            c=BLUE,s=6,alpha=0.2)
ax3.scatter(foreign_specs[cr_mask,:3][:,0],foreign_specs[cr_mask,:3][:,1],foreign_specs[cr_mask,:3][:,2],
            c=GREEN,s=18,alpha=0.7,label='Cross-reactive')
ax3.scatter([tcr_spec[0]],[tcr_spec[1]],[tcr_spec[2]],c=ORANGE,s=150,marker='*',zorder=10)
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8); ax3.set_zlabel(r'$\psi_3$',fontsize=8)
ax3.set_title('TCR Recognition\nSpace',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('TCR Cross-reactivity: Spectral Bandwidth of Recognition',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel3_tcr_crossreactivity.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 4: Neoantigen Identification
# ============================================================
print("Panel 4...")
fig, axes, ax3 = make_fig()

# Generate germline peptides (base spectral positions)
n_peptides = 300
wt_specs = np.array([r/np.linalg.norm(r) for r in rng.randn(n_peptides, d_embed)])

# HLA spectrum and self-peptidome spectrum centroid
hla_spec = rng.randn(d_embed); hla_spec /= np.linalg.norm(hla_spec)
self_centroid = wt_specs.mean(axis=0); self_centroid /= np.linalg.norm(self_centroid)

# Mutate peptides at various rates to simulate somatic mutations
n_muts_range = np.arange(0, 9)
shift_mean = []; shift_std = []
for n_mut in n_muts_range:
    shifts = []
    for wt in wt_specs[:50]:
        delta = rng.randn(d_embed) * 0.1 * n_mut
        mut = wt + delta; mut /= np.linalg.norm(mut)
        shifts.append(np.linalg.norm(mut - wt))
    shift_mean.append(np.mean(shifts)); shift_std.append(np.std(shifts))

# A: spectral shift vs number of mutations
axes[0].errorbar(n_muts_range, shift_mean, yerr=shift_std, color=BLUE, lw=2, marker='o', ms=5, capsize=3)
axes[0].set_xlabel('Number of AA Mutations',fontsize=9); axes[0].set_ylabel(r'Spectral Shift $\|\Delta\psi\|$',fontsize=9)
axes[0].set_title('Spectral Shift vs Mutations',fontsize=10,fontweight='bold'); sax(axes[0])

# B: neoantigen ROC-AUC vs mutation rate
mut_rates = np.linspace(0.01, 0.5, 20)
aucs = []
for mu_rate in mut_rates:
    n_test = 100
    wt_s = np.array([r/np.linalg.norm(r) for r in rng.randn(n_test, d_embed)])
    mut_s = []
    for w in wt_s:
        delta = rng.randn(d_embed) * mu_rate * 2
        m = w + delta; m /= np.linalg.norm(m); mut_s.append(m)
    mut_s = np.array(mut_s)
    # Neoantigen score: rho_bind - rho_self
    rho_b_wt = wt_s @ hla_spec
    rho_b_mut = mut_s @ hla_spec
    rho_s_wt = wt_s @ self_centroid
    rho_s_mut = mut_s @ self_centroid
    scores = rho_b_mut - rho_s_mut
    # True neoantigens: high rho_bind AND low rho_self (vs wildtype)
    true_neo = (rho_b_mut > rho_b_wt + 0.05) | (rho_s_mut < rho_s_wt - 0.05)
    if true_neo.sum() > 5 and (~true_neo).sum() > 5:
        _, _, a = roc(scores[true_neo], scores[~true_neo])
        aucs.append(a)
    else:
        aucs.append(0.5)
axes[1].plot(mut_rates, aucs, color=GREEN, lw=2, marker='s', ms=4)
axes[1].axhline(0.5, color=GRAY, ls='--', lw=1)
axes[1].set_xlabel('Mutation Rate',fontsize=9); axes[1].set_ylabel('ROC-AUC',fontsize=9)
axes[1].set_title('Neoantigen ID ROC-AUC',fontsize=10,fontweight='bold'); sax(axes[1])
axes[1].set_ylim(0.4, 1.05)

# C: rho_bind vs rho_self scatter (4 quadrants)
n_sc=400
specs_sc = np.array([r/np.linalg.norm(r) for r in rng.randn(n_sc, d_embed)])
rho_b_sc = specs_sc @ hla_spec
rho_s_sc = specs_sc @ self_centroid
# colour by neoantigen status
is_neo = (rho_b_sc > 0.4) & (rho_s_sc < 0.3)
col_sc = np.where(is_neo, RED, BLUE)
axes[2].scatter(rho_s_sc, rho_b_sc, c=col_sc, s=8, alpha=0.5)
axes[2].axhline(0.4, color=GRAY, ls='--', lw=1)
axes[2].axvline(0.3, color=GRAY, ls='--', lw=1)
axes[2].set_xlabel(r'Self-similarity $\rho_{self}$',fontsize=9)
axes[2].set_ylabel(r'HLA binding $\rho_{bind}$',fontsize=9)
axes[2].set_title(r'Neoantigen Quadrant ($\rho_{bind}$ vs $\rho_{self}$)',fontsize=10,fontweight='bold')
sax(axes[2])

# D: 3D — wildtype vs mutant peptide spectra
clean3d(ax3)
n_3d=60
wt_3d = np.array([r/np.linalg.norm(r) for r in rng.randn(n_3d, d_embed)])
mut_3d = []
for w in wt_3d:
    delta = rng.randn(d_embed)*0.4; m=w+delta; m/=np.linalg.norm(m); mut_3d.append(m)
mut_3d=np.array(mut_3d)
ax3.scatter(wt_3d[:,0],wt_3d[:,1],wt_3d[:,2],c=BLUE,s=20,alpha=0.7,label='Germline')
ax3.scatter(mut_3d[:,0],mut_3d[:,1],mut_3d[:,2],c=RED,s=20,alpha=0.7,label='Mutant')
for i in range(0,n_3d,6):
    ax3.plot([wt_3d[i,0],mut_3d[i,0]],[wt_3d[i,1],mut_3d[i,1]],[wt_3d[i,2],mut_3d[i,2]],
             color=GRAY,lw=0.5,alpha=0.5)
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8); ax3.set_zlabel(r'$\psi_3$',fontsize=8)
ax3.set_title('Germline vs Mutant\nSpectral Shift',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Neoantigen Identification via Spectral Displacement',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel4_neoantigen.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 5: Immune Escape Prediction
# ============================================================
print("Panel 5...")
fig, axes, ax3 = make_fig()

# Base viral surface protein spectrum
viral_spec = rng.randn(d_embed); viral_spec /= np.linalg.norm(viral_spec)
ab_spec = rng.randn(d_embed); ab_spec /= np.linalg.norm(ab_spec)
rec_spec = rng.randn(d_embed); rec_spec /= np.linalg.norm(rec_spec)
w_fit = 0.8  # fitness weight

# Enumerate single-AA substitutions via random perturbations
n_variants = 200
variants = []
for _ in range(n_variants):
    delta = rng.randn(d_embed) * rng.exponential(0.25)
    v = viral_spec + delta; v /= np.linalg.norm(v)
    variants.append(v)
variants = np.array(variants)

rho_ab_var = variants @ ab_spec
rho_rec_var = variants @ rec_spec
escape_score = -rho_ab_var + w_fit * rho_rec_var

# A: top escape scores bar chart
top_idx = np.argsort(escape_score)[-40:][::-1]
top_esc = escape_score[top_idx]
col_e = [GREEN if e > 0 else GRAY for e in top_esc]
axes[0].bar(np.arange(40), top_esc, color=col_e, alpha=0.85)
axes[0].axhline(0, color=GRAY, ls='-', lw=0.8)
axes[0].set_xlabel('Variant rank',fontsize=9); axes[0].set_ylabel('Escape score $E$',fontsize=9)
axes[0].set_title('Top Escape Variants',fontsize=10,fontweight='bold'); sax(axes[0])

# B: rho_bind vs rho_escape (viable escape region)
theta_neut=0.3; theta_bind=0.0
viable = (rho_ab_var < theta_neut) & (rho_rec_var > theta_bind)
axes[1].scatter(rho_ab_var[~viable], rho_rec_var[~viable], c=GRAY, s=8, alpha=0.4, label='Non-viable')
axes[1].scatter(rho_ab_var[viable], rho_rec_var[viable], c=GREEN, s=20, alpha=0.9, label='Viable escape')
axes[1].axvline(theta_neut, color=RED, ls='--', lw=1.5)
axes[1].axhline(theta_bind, color=BLUE, ls='--', lw=1.5)
axes[1].set_xlabel(r'Ab recognition $\rho_{Ab}$',fontsize=9); axes[1].set_ylabel(r'Receptor binding $\rho_{Rec}$',fontsize=9)
axes[1].set_title('Escape Viability Landscape',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=7); sax(axes[1])

# C: compound escape — viable fraction vs antibody panel size
ab_counts = np.arange(1, 9)
ab_specs_panel = [rng.randn(d_embed) for _ in range(8)]
for s in ab_specs_panel: s /= np.linalg.norm(s)
viable_fracs = []
for n_ab in ab_counts:
    rho_all_abs = np.array([variants @ ab_specs_panel[i] for i in range(n_ab)])
    max_rho_ab = rho_all_abs.max(axis=0)
    v = (max_rho_ab < theta_neut) & (rho_rec_var > theta_bind)
    viable_fracs.append(v.mean())
axes[2].semilogy(ab_counts, np.maximum(viable_fracs, 1e-4), color=PURPLE, lw=2, marker='o', ms=6)
axes[2].set_xlabel('Number of antibodies in panel',fontsize=9)
axes[2].set_ylabel('Viable escape fraction',fontsize=9)
axes[2].set_title('Compound Escape Difficulty',fontsize=10,fontweight='bold'); sax(axes[2])

# D: 3D escape landscape (first 2 dims of variant space vs escape score)
clean3d(ax3)
sc = ax3.scatter(variants[:,0], variants[:,1], escape_score,
                 c=escape_score, cmap='RdYlGn', s=12, alpha=0.8)
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8)
ax3.set_zlabel('Escape score $E$',fontsize=8)
ax3.set_title('Escape Score\nLandscape',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Immune Escape Variant Prediction via Spectral Perturbation',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel5_escape_prediction.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 6: Empty Database Performance
# ============================================================
print("Panel 6...")
fig, axes, ax3 = make_fig()

# A: synthesis time (O(c*L*log L)) vs L
L_vals = np.logspace(1, 5, 30).astype(int)
c_vals_plot = [1, 3, 4]
for c_p, col, lab in zip(c_vals_plot, [BLUE,GREEN,ORANGE], ['c=1','c=3','c=4']):
    t_synth = c_p * L_vals * np.log2(L_vals)
    axes[0].loglog(L_vals, t_synth / t_synth[0], color=col, lw=2, label=lab)
axes[0].set_xlabel('Sequence length $L$',fontsize=9); axes[0].set_ylabel('Relative synthesis cost',fontsize=9)
axes[0].set_title(r'Synthesis Cost $\mathcal{O}(cL\log L)$',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=8); sax(axes[0])

# B: pipeline time vs database size N
N_vals = np.logspace(2, 8, 30)
d_dim = 48
t_pipeline = N_vals * d_dim  # O(N*d) dot products
t_stored = N_vals * d_dim * 4  # stored embeddings lookup (same complexity, different constant)
t_exhaustive = N_vals * 200 * 200  # O(N*m*n) alignment
axes[1].loglog(N_vals, t_pipeline/t_pipeline[0], color=BLUE, lw=2, label='Spectral (empty DB)')
axes[1].loglog(N_vals, t_exhaustive/t_exhaustive[0], color=RED, lw=2, label='Exhaustive alignment')
axes[1].set_xlabel('Database size $N$',fontsize=9); axes[1].set_ylabel('Relative cost',fontsize=9)
axes[1].set_title('Scaling vs Database Size',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=8); sax(axes[1])

# C: memory usage comparison
categories = ['Struct.\ncoords\n(PDB)', 'Stored\nembeds\n(48d)', 'Empty\ndatabase\n(this work)']
N_ref = 1e6  # 1M sequences
mem_bytes = [N_ref * 1000 * 3 * 4,  # PDB: ~1000 atoms * xyz * float32
             N_ref * 48 * 4,         # embeddings: 48 floats
             1 * 48 * 4]             # empty: just 1 working embedding
mem_MB = np.array(mem_bytes) / 1e6
col_mem = [RED, ORANGE, GREEN]
bars = axes[2].bar(categories, mem_MB, color=col_mem, alpha=0.85, width=0.5)
axes[2].set_yscale('log')
axes[2].set_ylabel('Memory (MB)',fontsize=9)
axes[2].set_title(f'Memory per {int(N_ref/1e6)}M Sequences',fontsize=10,fontweight='bold')
for bar, v in zip(bars, mem_MB):
    axes[2].text(bar.get_x()+bar.get_width()/2, v*1.5, f'{v:.0f}', ha='center', fontsize=7)
sax(axes[2])

# D: 3D surface — synthesis cost as function of L and c
L_3d = np.linspace(100, 10000, 25)
c_3d = np.array([1, 2, 3, 4])
LL, CC = np.meshgrid(L_3d, c_3d)
TT = CC * LL * np.log2(LL)
clean3d(ax3)
surf = ax3.plot_surface(LL/1000, CC, np.log10(TT), cmap='viridis', alpha=0.85)
ax3.set_xlabel('$L$ (kbp)',fontsize=8); ax3.set_ylabel('Channels $c$',fontsize=8)
ax3.set_zlabel(r'$\log_{10}$(cost)',fontsize=8)
ax3.set_title('Synthesis Cost\nSurface',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Empty Database Principle: On-Demand Spectrum Synthesis',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel6_empty_database.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

print("All panels generated in:", str(OUT))

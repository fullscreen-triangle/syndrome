import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy import stats
from scipy.integrate import solve_ivp
from scipy.signal import correlate
from pathlib import Path

np.random.seed(99)
rng = np.random.RandomState(99)

ROOT = Path(r'c:\Users\kunda\Documents\health\syndrome\diseases\pathogen-biology')
OUT = ROOT / 'panels'
OUT.mkdir(parents=True, exist_ok=True)

BLUE='#2171B5'; RED='#CB181D'; GREEN='#238B45'; ORANGE='#D94801'
PURPLE='#6A51A3'; TEAL='#1A9B8A'; GRAY='#636363'
COLORS=[BLUE,RED,GREEN,ORANGE,PURPLE,TEAL,GRAY,'#8B4513']
CLASS_NAMES=['P','E','C','M','A','G','Ca','R']

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
K = 12; d_embed = 4*K

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

def matched_filter(query, target):
    """Multi-channel matched filter cross-correlation, returns normalised rho at each lag."""
    Xq = channelize(query); Xt = channelize(target)
    Lq = len(query); Lt = len(target)
    L = Lq + Lt - 1
    R = np.zeros(Lt - Lq + 1)
    for c in range(4):
        Qhat = np.fft.rfft(Xq[c], n=L)
        That = np.fft.rfft(Xt[c], n=L)
        r_full = np.fft.irfft(np.conj(Qhat)*That, n=L)
        R += r_full[:Lt-Lq+1]
    # normalise
    normQ = np.linalg.norm(Xq, 'fro')
    # rolling window norm of target
    sq = np.sum(Xt**2, axis=0)
    sq_cum = np.concatenate([[0], np.cumsum(sq)])
    normT = np.sqrt(np.maximum(sq_cum[Lq:] - sq_cum[:Lt-Lq+1], 1e-12))
    rho = R / (normQ * normT + 1e-12)
    return rho

def roc_auc(scores_pos, scores_neg):
    all_s = np.concatenate([scores_pos, scores_neg])
    labs = np.concatenate([np.ones(len(scores_pos)), np.zeros(len(scores_neg))])
    idx = np.argsort(-all_s); labs = labs[idx]
    tp = np.cumsum(labs); fp = np.cumsum(1-labs)
    tpr = np.concatenate([[0], tp/tp[-1]]); fpr = np.concatenate([[0], fp/fp[-1]])
    return fpr, tpr, np.trapezoid(tpr, fpr)

# ============================================================
# PANEL 1: Matched Filter Pathogen Identification
# ============================================================
print("Panel 1: Matched Filter Identification...")
fig, axes, ax3 = make_fig()

mu_range = np.array([0.0, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50])
Lq_vals = [50, 100, 200]
n_trials = 30

# Compute ROC-AUC and z-scores at each mu for Lq=100
aucs = []; zscores = []
for mu in mu_range:
    pos_scores=[]; neg_scores=[]
    for _ in range(n_trials):
        Lt = 5000
        motif = rand_seq(100)
        mut_motif = mutate(motif, mu)
        pos_in = rng.randint(0, Lt-100)
        target_h1 = rand_seq(pos_in) + mut_motif + rand_seq(Lt-pos_in-100)
        target_h0 = rand_seq(Lt)
        rho_h1 = matched_filter(motif, target_h1)
        rho_h0 = matched_filter(motif, target_h0)
        pos_scores.append(rho_h1.max())
        neg_scores.append(rho_h0.max())
    _, _, a = roc_auc(np.array(pos_scores), np.array(neg_scores))
    aucs.append(a)
    # z-score
    all_h0 = np.array(neg_scores)
    zscores.append((np.mean(pos_scores)-np.mean(all_h0))/(np.std(all_h0)+1e-10))

# A: ROC-AUC vs mu
axes[0].plot(mu_range, aucs, color=BLUE, lw=2, marker='o', ms=6, label='4-ch matched filter')
axes[0].axhline(0.5, color=GRAY, ls='--', lw=1)
axes[0].set_xlabel(r'Substitution rate $\mu$',fontsize=9); axes[0].set_ylabel('ROC-AUC',fontsize=9)
axes[0].set_title('Identification ROC-AUC vs Divergence',fontsize=10,fontweight='bold')
axes[0].set_ylim(0.4, 1.05); axes[0].legend(fontsize=8); sax(axes[0])

# B: z-score vs mu
axes[1].plot(mu_range, zscores, color=PURPLE, lw=2, marker='s', ms=6)
axes[1].axhline(5, color=RED, ls='--', lw=1.5, label='Detection threshold $z=5$')
axes[1].set_xlabel(r'Substitution rate $\mu$',fontsize=9); axes[1].set_ylabel('Peak $z$-score',fontsize=9)
axes[1].set_title('Detection $z$-score vs Divergence',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=8); sax(axes[1])

# C: position recovery rate vs mu for different Lq
for Lq, col in zip(Lq_vals, [BLUE, GREEN, ORANGE]):
    rec=[]
    for mu in mu_range:
        n_rec=0
        for _ in range(20):
            Lt=5000; motif=rand_seq(Lq); mut_motif=mutate(motif,mu)
            pos=rng.randint(0,Lt-Lq)
            target=rand_seq(pos)+mut_motif+rand_seq(Lt-pos-Lq)
            rho=matched_filter(motif,target)
            pred_pos=np.argmax(rho)
            if abs(pred_pos-pos)<=2: n_rec+=1
        rec.append(n_rec/20)
    axes[2].plot(mu_range, rec, color=col, lw=2, marker='^', ms=5, label=f'$L_q={Lq}$')
axes[2].axhline(1.0, color=GRAY, ls='--', lw=0.8)
axes[2].set_xlabel(r'Substitution rate $\mu$',fontsize=9); axes[2].set_ylabel('Position recovery rate',fontsize=9)
axes[2].set_title('Position Recovery vs Divergence',fontsize=10,fontweight='bold')
axes[2].legend(fontsize=8); sax(axes[2])

# D: 3D surface — z-score as function of Lq and mu
Lq_3d = np.array([50, 100, 150, 200, 300])
mu_3d = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
Z_surf = np.zeros((len(Lq_3d), len(mu_3d)))
for i, lq in enumerate(Lq_3d):
    for j, mu in enumerate(mu_3d):
        # Approximate z-score analytically: scales as sqrt(Lq)*(1-mu)/sigma_null
        z_approx = np.sqrt(lq/50.0) * max(1-2*mu, 0.05) * 12.0
        Z_surf[i,j] = z_approx
MU3, LQ3 = np.meshgrid(mu_3d, Lq_3d/100)
clean3d(ax3)
ax3.plot_surface(MU3, LQ3, Z_surf, cmap='plasma', alpha=0.85)
ax3.set_xlabel(r'$\mu$',fontsize=8); ax3.set_ylabel('$L_q$ (x100bp)',fontsize=8); ax3.set_zlabel('$z$-score',fontsize=8)
ax3.set_title('Detection $z$-score\nSurface',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Matched Filter Pathogen Identification: Detection Performance',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel1_identification.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 2: Tropism Prediction
# ============================================================
print("Panel 2: Tropism Prediction...")
fig, axes, ax3 = make_fig()

# 5 receptor spectra (ACE2, CD4, sialic_a26, sialic_a23, TMPRSS2 analogues)
rec_names=['ACE2','CD4','Sia-2,6','Sia-2,3','TMPRSS2']
rec_specs = np.array([r/np.linalg.norm(r) for r in rng.randn(5, d_embed)])

# Generate pathogen families — each family centered near one receptor
n_fam=5; n_mem=10; n_nonfam=50
cognate_rho=[]; non_cognate_rho=[]
pathogen_specs_all=[]; pathogen_tropism=[]
for f in range(n_fam):
    for _ in range(n_mem):
        v = rec_specs[f] + rng.randn(d_embed)*0.35; v/=np.linalg.norm(v)
        pathogen_specs_all.append(v); pathogen_tropism.append(f)
        cognate_rho.append(v @ rec_specs[f])
    for _ in range(n_nonfam//n_fam):
        rand_v = rng.randn(d_embed); rand_v/=np.linalg.norm(rand_v)
        non_cognate_rho.append(rand_v @ rec_specs[f])
cognate_rho=np.array(cognate_rho); non_cognate_rho=np.array(non_cognate_rho)
pathogen_specs_all=np.array(pathogen_specs_all); pathogen_tropism=np.array(pathogen_tropism)

# A: rho distributions cognate vs non-cognate
bins=np.linspace(-0.5,1.0,35)
axes[0].hist(non_cognate_rho,bins=bins,color=GRAY,alpha=0.7,density=True,label='Non-cognate')
axes[0].hist(cognate_rho,bins=bins,color=GREEN,alpha=0.8,density=True,label='Cognate')
axes[0].axvline(0.4,color=RED,ls='--',lw=1.5,label=r'$\rho^*_{trop}$')
axes[0].set_xlabel(r'$\rho$(attachment, receptor)',fontsize=9); axes[0].set_ylabel('Density',fontsize=9)
axes[0].set_title('Tropism Score Distribution',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=7); sax(axes[0])

# B: ROC-AUC vs divergence from cognate receptor
div_vals=np.linspace(0.0,0.5,15); aucs_trop=[]
for div in div_vals:
    cog=[]; ncog=[]
    for f in range(n_fam):
        for _ in range(20):
            v=rec_specs[f]+rng.randn(d_embed)*(0.3+div*2); v/=np.linalg.norm(v)
            cog.append(v@rec_specs[f])
        for _ in range(20):
            rand_v=rng.randn(d_embed); rand_v/=np.linalg.norm(rand_v)
            ncog.append(rand_v@rec_specs[f])
    _,_,a=roc_auc(np.array(cog),np.array(ncog)); aucs_trop.append(a)
axes[1].plot(div_vals,aucs_trop,color=TEAL,lw=2,marker='o',ms=5)
axes[1].axhline(0.5,color=GRAY,ls='--',lw=1); axes[1].axhline(0.97,color=GREEN,ls=':',lw=1.5,label='AUC=0.97')
axes[1].set_xlabel('Sequence divergence from receptor',fontsize=9); axes[1].set_ylabel('Tropism ROC-AUC',fontsize=9)
axes[1].set_title('Tropism AUC vs Divergence',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=8); sax(axes[1]); axes[1].set_ylim(0.4,1.05)

# C: receptor binding scores for panel of pathogens (grouped bar)
n_show_path=5; n_show_rec=5
path_idxs=rng.choice(len(pathogen_specs_all),n_show_path,replace=False)
x_bar=np.arange(n_show_rec); width_bar=0.15
for pi,pidx in enumerate(path_idxs):
    scores=[pathogen_specs_all[pidx]@rec_specs[ri] for ri in range(n_show_rec)]
    axes[2].bar(x_bar+pi*width_bar,scores,width=width_bar,color=COLORS[pi],alpha=0.85,
                label=f'P{pi+1}')
axes[2].set_xticks(x_bar+2*width_bar); axes[2].set_xticklabels(rec_names,fontsize=7)
axes[2].axhline(0.4,color=RED,ls='--',lw=1.2,label=r'$\rho^*$')
axes[2].set_ylabel(r'Receptor binding $\rho$',fontsize=9)
axes[2].set_title('Pathogen-Receptor Binding Panel',fontsize=10,fontweight='bold')
axes[2].legend(fontsize=6,ncol=2); sax(axes[2])

# D: 3D scatter — pathogen attachment proteins by tropism
clean3d(ax3)
for f in range(n_fam):
    mask=pathogen_tropism==f
    ax3.scatter(pathogen_specs_all[mask,0],pathogen_specs_all[mask,1],pathogen_specs_all[mask,2],
                c=COLORS[f],s=30,alpha=0.8,label=rec_names[f])
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8); ax3.set_zlabel(r'$\psi_3$',fontsize=8)
ax3.set_title('Pathogen Attachment\nProtein Clusters',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Receptor-Pathogen Spectral Overlap and Tropism Prediction',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel2_tropism.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 3: Escape Variant Landscape
# ============================================================
print("Panel 3: Escape Variants...")
fig, axes, ax3 = make_fig()

viral_spec = rng.randn(d_embed); viral_spec/=np.linalg.norm(viral_spec)
ab_spec = rng.randn(d_embed); ab_spec/=np.linalg.norm(ab_spec)
rec_spec = rng.randn(d_embed); rec_spec/=np.linalg.norm(rec_spec)
w=0.8; theta_neut=0.25; theta_bind=0.05

n_var=300
variants=np.array([v/np.linalg.norm(v) for v in viral_spec+rng.randn(n_var,d_embed)*rng.exponential(0.25,(n_var,1))])
# fix shape
variants=np.array([((viral_spec + rng.randn(d_embed)*rng.exponential(0.25))/
                   np.linalg.norm(viral_spec + rng.randn(d_embed)*rng.exponential(0.25)))
                   for _ in range(n_var)])
rho_ab=variants@ab_spec; rho_rec=variants@rec_spec
escape_score=-rho_ab+w*rho_rec
viable=(rho_ab<theta_neut)&(rho_rec>theta_bind)

# A: top 40 escape scores
top40=np.argsort(escape_score)[-40:][::-1]
cols_e=[GREEN if viable[i] else ORANGE for i in top40]
axes[0].bar(np.arange(40),escape_score[top40],color=cols_e,alpha=0.85)
axes[0].axhline(0,color=GRAY,lw=0.8)
axes[0].set_xlabel('Variant rank',fontsize=9); axes[0].set_ylabel('Escape score $E$',fontsize=9)
axes[0].set_title('Top Escape Variants',fontsize=10,fontweight='bold'); sax(axes[0])

# B: binding retention vs escape score (viable region shaded)
axes[1].scatter(rho_ab[~viable],rho_rec[~viable],c=GRAY,s=8,alpha=0.35,label='Non-viable')
axes[1].scatter(rho_ab[viable],rho_rec[viable],c=GREEN,s=22,alpha=0.9,label=f'Viable ({viable.sum()})')
axes[1].axvline(theta_neut,color=RED,ls='--',lw=1.5,label=r'$\theta_{neut}$')
axes[1].axhline(theta_bind,color=BLUE,ls='--',lw=1.5,label=r'$\theta_{bind}$')
axes[1].set_xlabel(r'Ab recognition $\rho_{Ab}$',fontsize=9); axes[1].set_ylabel(r'Receptor binding $\rho_{Rec}$',fontsize=9)
axes[1].set_title('Escape Viability Space',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=7); sax(axes[1])

# C: compound escape fraction vs antibody panel size
ab_panel=[rng.randn(d_embed) for _ in range(8)]
for s in ab_panel: s/=np.linalg.norm(s)
ab_counts=np.arange(1,9); vf=[]
for na in ab_counts:
    max_rho=np.array([variants@ab_panel[i] for i in range(na)]).max(axis=0)
    vf.append(((max_rho<theta_neut)&(rho_rec>theta_bind)).mean())
axes[2].semilogy(ab_counts,np.maximum(vf,1e-4),color=PURPLE,lw=2,marker='o',ms=7)
axes[2].set_xlabel('Antibodies in panel',fontsize=9); axes[2].set_ylabel('Viable escape fraction',fontsize=9)
axes[2].set_title('Compound Escape Difficulty',fontsize=10,fontweight='bold'); sax(axes[2])

# D: 3D escape landscape surface
n_grid=20
v1_range=np.linspace(variants[:,0].min(),variants[:,0].max(),n_grid)
v2_range=np.linspace(variants[:,1].min(),variants[:,1].max(),n_grid)
V1,V2=np.meshgrid(v1_range,v2_range)
# interpolate escape score onto grid
from scipy.interpolate import griddata
ES_grid=griddata(variants[:,:2],escape_score,(V1,V2),method='linear')
clean3d(ax3)
ax3.plot_surface(V1,V2,np.nan_to_num(ES_grid),cmap='RdYlGn',alpha=0.85)
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8)
ax3.set_zlabel('Escape score',fontsize=8)
ax3.set_title('Escape Score\nLandscape',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Viral Escape Variant Landscape: Immune Evasion vs Fitness',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel3_escape_landscape.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 4: Antibiotic Resistance Prediction
# ============================================================
print("Panel 4: Antibiotic Resistance...")
fig, axes, ax3 = make_fig()

# Drug and target enzyme spectra
drug_spec=rng.randn(d_embed); drug_spec/=np.linalg.norm(drug_spec)
enzyme_spec=rng.randn(d_embed); enzyme_spec/=np.linalg.norm(enzyme_spec)
substrate_spec=rng.randn(d_embed); substrate_spec/=np.linalg.norm(substrate_spec)

# Susceptible strains: enzyme near wild-type
n_sus=80; n_res=80
sus_enzymes=np.array([e/np.linalg.norm(e) for e in enzyme_spec+rng.randn(n_sus,d_embed)*0.15])
# Resistant strains: enzyme shifted away from drug
res_direction=drug_spec-enzyme_spec; res_direction/=np.linalg.norm(res_direction)
res_enzymes=np.array([e/np.linalg.norm(e) for e in
                      (enzyme_spec - res_direction*0.5 + rng.randn(n_res,d_embed)*0.15)])

rho_drug_sus=sus_enzymes@drug_spec; rho_drug_res=res_enzymes@drug_spec
rho_sub_sus=sus_enzymes@substrate_spec; rho_sub_res=res_enzymes@substrate_spec

# A: spectral distance drug-enzyme for susceptible vs resistant
bins=np.linspace(-0.5,1.0,30)
axes[0].hist(rho_drug_res,bins=bins,color=RED,alpha=0.75,density=True,label='Resistant')
axes[0].hist(rho_drug_sus,bins=bins,color=GREEN,alpha=0.75,density=True,label='Susceptible')
axes[0].axvline(0.3,color=GRAY,ls='--',lw=1.5,label=r'$\rho^*_{drug}$')
axes[0].set_xlabel(r'$\rho$(enzyme, drug)',fontsize=9); axes[0].set_ylabel('Density',fontsize=9)
axes[0].set_title('Drug-Enzyme Spectral Overlap',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=7); sax(axes[0])

# B: resistance mutation landscape (rho reduction)
n_muts=50
mut_enzy=np.array([e/np.linalg.norm(e) for e in enzyme_spec+rng.randn(n_muts,d_embed)*rng.exponential(0.3,(n_muts,1))])
delta_rho_drug=mut_enzy@drug_spec - (enzyme_spec@drug_spec)
delta_rho_sub=mut_enzy@substrate_spec - (enzyme_spec@substrate_spec)
is_resist=(mut_enzy@drug_spec < 0.3) & (mut_enzy@substrate_spec > -0.1)
axes[1].scatter(delta_rho_sub[~is_resist],delta_rho_drug[~is_resist],c=BLUE,s=14,alpha=0.5,label='Non-resistant')
axes[1].scatter(delta_rho_sub[is_resist],delta_rho_drug[is_resist],c=RED,s=28,alpha=0.9,label='Resistance mutations')
axes[1].axhline(0,color=GRAY,lw=0.8,ls='--'); axes[1].axvline(0,color=GRAY,lw=0.8,ls='--')
axes[1].set_xlabel(r'$\Delta\rho$(enzyme, substrate)',fontsize=9)
axes[1].set_ylabel(r'$\Delta\rho$(enzyme, drug)',fontsize=9)
axes[1].set_title('Resistance Mutation\nLandscape',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=7); sax(axes[1])

# C: robustness score distribution for drug panel
n_drugs=8
drug_panel=np.array([d/np.linalg.norm(d) for d in rng.randn(n_drugs,d_embed)])
rob_scores=[]
for dp in drug_panel:
    rho_bind=enzyme_spec@dp
    min_res=min(mut_enzy@dp)
    rob_scores.append(min_res*rho_bind)
rob_scores=np.array(rob_scores)
col_rob=[GREEN if r>0 else RED for r in rob_scores]
axes[2].bar(np.arange(n_drugs)+1,rob_scores,color=col_rob,alpha=0.85)
axes[2].axhline(0,color=GRAY,lw=1)
axes[2].set_xlabel('Drug candidate',fontsize=9); axes[2].set_ylabel('Robustness score',fontsize=9)
axes[2].set_title('Drug Resistance Robustness',fontsize=10,fontweight='bold'); sax(axes[2])

# D: 3D surface — drug binding x substrate binding x robustness
db_range=np.linspace(-0.5,1.0,20); sb_range=np.linspace(-0.5,1.0,20)
DB,SB=np.meshgrid(db_range,sb_range)
ROB=DB*np.maximum(SB,0)  # robustness = drug_bind * substrate_retain
clean3d(ax3)
ax3.plot_surface(DB,SB,ROB,cmap='RdYlGn',alpha=0.85)
ax3.set_xlabel(r'$\rho_{drug}$',fontsize=8); ax3.set_ylabel(r'$\rho_{substrate}$',fontsize=8)
ax3.set_zlabel('Robustness',fontsize=8)
ax3.set_title('Drug Robustness\nSurface',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Antibiotic Resistance Prediction via Enzyme Spectral Evasion',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel4_resistance.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 5: Infection Dynamics — Coherence ODE
# ============================================================
print("Panel 5: Infection Dynamics...")
fig, axes, ax3 = make_fig()

n_classes=8; n_proteins=10
lambda_i=np.array([0.80,0.60,0.90,0.70,0.85,0.75,0.65,0.50])
gamma_i=np.array([0.30,0.25,0.35,0.28,0.32,0.27,0.22,0.18])
eta_healthy=np.ones(n_classes)*0.92
# omega_ij: spectral overlap (8 classes x 10 proteins)
omega=rng.uniform(0.05,0.85,(n_classes,n_proteins))
omega[4,:]*=1.5; omega[4,:]=np.clip(omega[4,:],0,1)  # mitochondrial class more vulnerable
C_max=rng.uniform(0.3,1.0,n_proteins)

def viral_load(t,V_max=1.0,t_peak=4.0):
    return V_max*(t/t_peak)*np.exp(1-t/t_peak)

def deta_dt(t,eta,omega,C_max,lambda_i,gamma_i,eta_healthy):
    V=viral_load(t)
    C=C_max*V
    load=omega@C
    return -lambda_i*load*eta+gamma_i*(eta_healthy-eta)

t_span=(0,14); t_eval=np.linspace(0,14,200)
sol=solve_ivp(deta_dt,t_span,eta_healthy.copy(),args=(omega,C_max,lambda_i,gamma_i,eta_healthy),
              t_eval=t_eval,method='RK45',rtol=1e-6)
D_t=1-sol.y  # shape (8, 200)

# A: D_i(t) trajectories for all 8 classes
for i in range(n_classes):
    axes[0].plot(t_eval,D_t[i],color=COLORS[i],lw=1.8,label=CLASS_NAMES[i],alpha=0.9)
axes[0].set_xlabel('Time (days)',fontsize=9); axes[0].set_ylabel('Disease index $D_i(t)$',fontsize=9)
axes[0].set_title('Host Oscillator Coherence\nDuring Infection',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=6,ncol=2); sax(axes[0])

# B: spectral overlap omega_ij (grouped bar)
x_cl=np.arange(n_classes); width_b=0.08
for j in range(min(n_proteins,5)):
    axes[1].bar(x_cl+j*width_b,omega[:,j],width=width_b,color=COLORS[j],alpha=0.8,label=f'VP{j+1}')
axes[1].set_xticks(x_cl+2*width_b); axes[1].set_xticklabels(CLASS_NAMES,fontsize=8)
axes[1].set_ylabel(r'Spectral overlap $\omega_{ij}$',fontsize=9)
axes[1].set_title('Pathogen-Host Spectral Overlap',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=6,ncol=2); sax(axes[1])

# C: peak disease index D_i^* vs viral load
V_range=np.linspace(0.1,2.0,30)
D_peak=np.zeros((n_classes,len(V_range)))
for vi,Vmax in enumerate(V_range):
    sol2=solve_ivp(deta_dt,(0,14),eta_healthy.copy(),
                   args=(omega,C_max*Vmax,lambda_i,gamma_i,eta_healthy),
                   t_eval=np.linspace(0,14,50),method='RK45')
    D_peak[:,vi]=(1-sol2.y).max(axis=1)
for i in [0,4,5]:  # P, A, G — most interesting
    axes[2].plot(V_range,D_peak[i],color=COLORS[i],lw=2,label=CLASS_NAMES[i])
axes[2].set_xlabel('Viral load $V_{max}$',fontsize=9); axes[2].set_ylabel('Peak disease index $D_i^*$',fontsize=9)
axes[2].set_title('Peak Dysfunction vs Viral Load',fontsize=10,fontweight='bold')
axes[2].legend(fontsize=8); sax(axes[2])

# D: 3D surface D_i(t) heatmap as surface (class x time)
T3,I3=np.meshgrid(t_eval,np.arange(n_classes))
clean3d(ax3)
ax3.plot_surface(I3,T3,D_t,cmap='coolwarm',alpha=0.88)
ax3.set_yticks(np.arange(0,15,7)); ax3.set_xticks(np.arange(n_classes))
ax3.set_xticklabels(CLASS_NAMES,fontsize=6)
ax3.set_xlabel('Class',fontsize=8); ax3.set_ylabel('Time (days)',fontsize=8); ax3.set_zlabel('$D_i(t)$',fontsize=8)
ax3.set_title('Disease Vector\nTrajectory $D(t)$',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Infection Dynamics: Host Oscillator Coherence Deformation',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel5_infection_dynamics.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

# ============================================================
# PANEL 6: Microbiome Dysbiosis
# ============================================================
print("Panel 6: Microbiome Dysbiosis...")
fig, axes, ax3 = make_fig()

# Host epithelial spectrum
host_spec=rng.randn(d_embed); host_spec/=np.linalg.norm(host_spec)

# 20 species spectra
n_species=20
species_specs=np.array([s/np.linalg.norm(s) for s in rng.randn(n_species,d_embed)])

# Healthy composition: biased toward species near host spectrum
rho_host_sp=species_specs@host_spec
healthy_fracs=np.exp(2*rho_host_sp); healthy_fracs/=healthy_fracs.sum()

# IBD-like composition: shifted toward dysbiotic species
dysbiotic_shift=-rho_host_sp; dysbiotic_shift-=dysbiotic_shift.min()
ibd_fracs=np.exp(2*dysbiotic_shift); ibd_fracs/=ibd_fracs.sum()

# Random compositions for scatter
n_comp=200
comp_mat=np.abs(rng.randn(n_comp,n_species))
comp_mat/=comp_mat.sum(axis=1,keepdims=True)
micro_specs=comp_mat@species_specs
micro_norms=np.linalg.norm(micro_specs,axis=1,keepdims=True)
micro_normed=micro_specs/np.maximum(micro_norms,1e-10)
eubiosis_scores=micro_normed@host_spec

# Diversity (Shannon entropy)
shannon_div=-(comp_mat*np.log(comp_mat+1e-12)).sum(axis=1)/np.log(n_species)

# A: dysbiosis score histogram (healthy vs IBD-like)
rho_star_sym=0.4
healthy_score=(healthy_fracs@species_specs); healthy_score/=np.linalg.norm(healthy_score)
healthy_rho=np.dot(healthy_score,host_spec)
ibd_score=(ibd_fracs@species_specs); ibd_score/=np.linalg.norm(ibd_score)
ibd_rho=np.dot(ibd_score,host_spec)

# generate ensemble
n_ens=150
healthy_ens=[]; ibd_ens=[]
for _ in range(n_ens):
    f=np.abs(healthy_fracs+rng.randn(n_species)*0.01); f/=f.sum()
    ms=f@species_specs; ms/=np.linalg.norm(ms)
    healthy_ens.append(ms@host_spec)
    f2=np.abs(ibd_fracs+rng.randn(n_species)*0.01); f2/=f2.sum()
    ms2=f2@species_specs; ms2/=np.linalg.norm(ms2)
    ibd_ens.append(ms2@host_spec)
healthy_ens=np.array(healthy_ens); ibd_ens=np.array(ibd_ens)
bins=np.linspace(-0.5,1.0,30)
axes[0].hist(ibd_ens,bins=bins,color=RED,alpha=0.75,density=True,label='Dysbiotic')
axes[0].hist(healthy_ens,bins=bins,color=GREEN,alpha=0.75,density=True,label='Healthy')
axes[0].axvline(rho_star_sym,color=GRAY,ls='--',lw=1.5,label=r'$\rho^*_{sym}$')
axes[0].set_xlabel(r'Host alignment $\rho(\Psi_{micro},\Psi_{host})$',fontsize=8)
axes[0].set_ylabel('Density',fontsize=9); axes[0].set_title('Microbiome-Host Spectral Alignment',fontsize=10,fontweight='bold')
axes[0].legend(fontsize=7); sax(axes[0])

# B: eubiosis score vs Shannon diversity
axes[1].scatter(shannon_div,eubiosis_scores,c=eubiosis_scores,cmap='RdYlGn',s=12,alpha=0.6)
axes[1].axhline(rho_star_sym,color=RED,ls='--',lw=1.5,label=r'$\rho^*_{sym}$')
m2,b2,_,_,_=stats.linregress(shannon_div,eubiosis_scores)
xf=np.linspace(0,1,100)
axes[1].plot(xf,m2*xf+b2,color=BLUE,lw=2,label='Trend')
axes[1].set_xlabel('Shannon diversity $H$',fontsize=9); axes[1].set_ylabel(r'Eubiosis score $\rho$',fontsize=9)
axes[1].set_title('Diversity vs Host Alignment',fontsize=10,fontweight='bold')
axes[1].legend(fontsize=7); sax(axes[1])

# C: optimal probiotic fractions f* (top 10 species)
# f* proportional to projection onto host_spec direction
proj=np.maximum(species_specs@host_spec,0)
f_star=proj/proj.sum()
top10=np.argsort(f_star)[-10:][::-1]
col_p=[GREEN if f_star[i]>0 else GRAY for i in top10]
axes[2].barh(np.arange(10),f_star[top10]*100,color=col_p,alpha=0.85)
axes[2].set_yticks(np.arange(10)); axes[2].set_yticklabels([f'Sp.{i+1}' for i in top10],fontsize=7)
axes[2].set_xlabel('Optimal fraction $f^*$ (%)',fontsize=9)
axes[2].set_title('Optimal Probiotic\nFormulation',fontsize=10,fontweight='bold'); sax(axes[2])

# D: 3D scatter — species spectra with host centroid and optimal mixture
clean3d(ax3)
rho_cls=species_specs@host_spec
sc=ax3.scatter(species_specs[:,0],species_specs[:,1],species_specs[:,2],
               c=rho_cls,cmap='RdYlGn',s=35,alpha=0.8)
ax3.scatter([host_spec[0]],[host_spec[1]],[host_spec[2]],c='gold',s=200,marker='*',zorder=10,label='Host')
mix=(f_star@species_specs); mix/=np.linalg.norm(mix)
ax3.scatter([mix[0]],[mix[1]],[mix[2]],c=GREEN,s=120,marker='^',zorder=10,label='Optimal mix')
ax3.set_xlabel(r'$\psi_1$',fontsize=8); ax3.set_ylabel(r'$\psi_2$',fontsize=8); ax3.set_zlabel(r'$\psi_3$',fontsize=8)
ax3.set_title('Microbiome Spectral\nSpace',fontsize=9,fontweight='bold'); ax3.tick_params(labelsize=7)
clean3d(ax3)

plt.suptitle('Microbiome Dysbiosis: Collective Spectral Interference with Host Epithelium',fontsize=11,fontweight='bold',y=0.98)
plt.savefig(str(OUT/'panel6_microbiome.png'),dpi=200,bbox_inches='tight',facecolor='white')
plt.close(); print("  done")

print("All 6 pathogen-biology panels written to:", str(OUT))

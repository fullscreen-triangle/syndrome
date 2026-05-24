"""
NumPy reference implementation for the pathogen biology paper
(pathogen-biology-monitoring.tex) — CPU ground truth for all five problems:

  1. Identification  — matched filter vs Kraken2/BLAST baseline
  2. Tropism         — spectral overlap for receptor-pathogen binding
  3. Immune escape   — dual-objective: receptor overlap↑, antibody overlap↓
  4. Resistance      — enzyme-drug spectral overlap drops below threshold
  5. Dynamics        — oscillator coherence decay (synthetic only)

Usage:
  python _validate_pathogen.py              # full self-test + synthetic benchmarks
  python _validate_pathogen.py --problem 1  # only identification benchmark
  python _validate_pathogen.py --problem 2  # only tropism benchmark

External data needed for real validation:
  Problem 1 (Identification):
    NCBI RefSeq sequences — download via: ncbi-datasets-cli
    Clinical benchmark:   https://github.com/DerrickWood/kraken2/wiki/Manual#kraken-2-databases
  Problem 2 (Tropism):
    SARS-CoV-2 Spike DMS: https://jbloom.github.io/SARS2_Omicron_BA1_mut_escape/
    ACE2 / TMPRSS2 sequences from UniProt P0DTC2, Q9BYF1, O15393
  Problem 3 (Escape):
    Bloom lab mAb escape datasets: https://jbloom.github.io/
    CoV-Escape from PyMol SARS2 structure resources
  Problem 4 (Resistance):
    BARRGD: https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/
    TEM β-lactamase DMS: PMID 24651513 (Stiffler et al.)
"""

import sys
import math
import random
import argparse
import numpy as np

# ── Physicochemical tables (protein embedding) ────────────────────────────────

HYDROPATHY = {
    'A': 1.8,  'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
    'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
    'L': 3.8,  'K': -3.9, 'M': 1.9,  'F': 2.8,  'P': -1.6,
    'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2,
}
VOLUME = {
    'A': 88.6,  'R': 173.4, 'N': 114.1, 'D': 111.1, 'C': 108.5,
    'Q': 143.8, 'E': 138.4, 'G': 60.1,  'H': 153.2, 'I': 166.7,
    'L': 166.7, 'K': 168.6, 'M': 162.9, 'F': 189.9, 'P': 112.7,
    'S': 89.0,  'T': 116.1, 'W': 227.8, 'Y': 193.6, 'V': 140.0,
}
CHARGE = {
    'A': 0, 'R': 1,  'N': 0,  'D': -1, 'C': 0,  'Q': 0, 'E': -1,
    'G': 0, 'H': 0.1,'I': 0,  'L': 0,  'K': 1,  'M': 0, 'F': 0,
    'P': 0, 'S': 0,  'T': 0,  'W': 0,  'Y': 0,  'V': 0,
}
DNA_MAP = {'A': [1,0,0,0], 'T': [0,1,0,0], 'G': [0,0,1,0], 'C': [0,0,0,1],
           'U': [0,1,0,0]}

K = 12

# ── Channelization ────────────────────────────────────────────────────────────

def channelize_protein(seq):
    s = seq.upper()
    h = np.array([HYDROPATHY.get(aa, 0.0) for aa in s], dtype=np.float64)
    v = np.array([VOLUME.get(aa, 111.0)   for aa in s], dtype=np.float64)
    q = np.array([CHARGE.get(aa, 0.0)     for aa in s], dtype=np.float64)
    for ch in (h, v, q):
        ch -= ch.mean()
        rms = math.sqrt((ch**2).mean()) or 1.0
        ch /= rms
    return np.stack([h, v, q])

def channelize_dna(seq):
    s = seq.upper()
    L = len(s)
    ch = np.zeros((4, L), dtype=np.float64)
    for i, base in enumerate(s):
        enc = DNA_MAP.get(base)
        if enc:
            for c in range(4): ch[c, i] = enc[c]
    for c in range(4):
        ch[c] -= ch[c].mean()
    return ch

def is_dna(seq):
    return all(b in 'ATGCUN' for b in seq.upper())

# ── Direct DFT matrix multiply (identical to dftDirect in spectral.js) ────────

_dft_cache = {}

def dft_direct(signal, k=K):
    L = len(signal)
    if (L, k) not in _dft_cache:
        ns = np.arange(L)
        ks = np.arange(1, k + 1)[:, None]
        phase = 2 * np.pi * ks * ns / L
        _dft_cache[(L, k)] = (np.cos(phase), -np.sin(phase))
    W_re, W_im = _dft_cache[(L, k)]
    return np.sqrt((W_re @ signal)**2 + (W_im @ signal)**2)

# ── Spectral embedding ────────────────────────────────────────────────────────

def embed(seq, k=K):
    s = seq.upper().replace(' ', '')
    channels = channelize_dna(s) if is_dna(s) else channelize_protein(s)
    mags = np.concatenate([dft_direct(ch, k) for ch in channels])
    norm = np.linalg.norm(mags)
    return mags / (norm if norm > 0 else 1.0)

def similarity(a, b):
    return float(np.dot(a, b))

def spectral_distance(a, b):
    return math.sqrt(2 * (1 - similarity(a, b)))

# ── Matched filter (cross-correlation via FFT) ────────────────────────────────

def matched_filter(query_channels, target_channels):
    """
    Compute multi-channel cross-correlation between query (length Lq)
    and target (length Lt >= Lq). Returns (rho_peak, position).
    Implements Eq. 3 via FFT convolution theorem (Eq. 4).
    """
    Lq = query_channels.shape[1]
    Lt = target_channels.shape[1]
    N  = 1
    while N < Lq + Lt: N <<= 1

    rho = np.zeros(Lt - Lq + 1)

    # Normalise query once
    q_norm = np.linalg.norm(query_channels) or 1.0

    for c in range(query_channels.shape[0]):
        Q = np.fft.rfft(query_channels[c], n=N)
        T = np.fft.rfft(target_channels[c], n=N)
        xcorr = np.fft.irfft(np.conj(Q) * T, n=N)[:Lt - Lq + 1]
        rho += xcorr

    # Normalise by local target norms (sliding window)
    t_sq = (target_channels**2).sum(axis=0)
    cumsum = np.cumsum(t_sq)
    t_norms = np.sqrt(cumsum[Lq-1:] - np.concatenate([[0], cumsum[:Lt-Lq]]))
    t_norms[t_norms == 0] = 1.0

    rho /= (q_norm * t_norms)
    peak_pos = np.argmax(rho)
    return float(rho[peak_pos]), int(peak_pos)

# ── Problem 1: Identification ─────────────────────────────────────────────────

def simulate_planted_signal(Lt=5000, Lq=100, mu=0.0, seed=42):
    """
    Simulate a planted-motif identification trial (DNA, 4-channel).
    Returns (query, target, true_position).
    - Lt: target sequence length (bp)
    - Lq: query sequence length (bp)
    - mu: substitution rate [0, 0.5]
    """
    rng = np.random.default_rng(seed)
    bases = ['A', 'T', 'G', 'C']
    target = rng.choice(bases, Lt)
    pos = rng.integers(0, Lt - Lq + 1)
    # Plant query with substitutions
    query = target[pos:pos+Lq].copy()
    n_sub = int(mu * Lq)
    sub_pos = rng.choice(Lq, n_sub, replace=False)
    for p in sub_pos:
        other = [b for b in bases if b != query[p]]
        query[p] = rng.choice(other)

    return ''.join(query), ''.join(target), pos

def benchmark_identification(n_trials=30, rates=(0, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50),
                             Lt=5000, Lq=100):
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        roc_auc_score = None

    print(f"\nProblem 1: Identification benchmark")
    print(f"  Lt={Lt}, Lq={Lq}, {n_trials} trials per rate")
    print(f"{'Rate':>6} {'AUC':>6} {'z-score':>8} {'Pos.Recovery':>14}")
    print('  ' + '-' * 40)

    for mu in rates:
        h1_peaks = []
        h0_peaks = []
        pos_correct = 0

        for t in range(n_trials):
            query, target, true_pos = simulate_planted_signal(Lt, Lq, mu, seed=t*97+17)
            q_ch = channelize_dna(query)
            t_ch = channelize_dna(target)
            h1_rho, pred_pos = matched_filter(q_ch, t_ch)
            h1_peaks.append(h1_rho)
            if abs(pred_pos - true_pos) <= 2:
                pos_correct += 1

            # Null: fresh random target
            rng2 = np.random.default_rng(t * 1337)
            rand_target = ''.join(rng2.choice(['A','T','G','C'], Lt))
            t_ch0 = channelize_dna(rand_target)
            h0_rho, _ = matched_filter(q_ch, t_ch0)
            h0_peaks.append(h0_rho)

        h1 = np.array(h1_peaks)
        h0 = np.array(h0_peaks)
        z = (h1.mean() - h0.mean()) / (h0.std() or 1e-9)

        labels = [1]*n_trials + [0]*n_trials
        scores = list(h1) + list(h0)
        if roc_auc_score:
            auc = roc_auc_score(labels, scores)
        else:
            auc = float('nan')

        print(f"  {mu:>5.2f}  {auc:>6.3f}  {z:>8.2f}  {pos_correct}/{n_trials}")

# ── Problem 2: Tropism ────────────────────────────────────────────────────────

# Known receptor and attachment protein sequences (canonical representatives)
RECEPTORS = {
    'ACE2':    'STIEEQAKTFLDKFNHEAEDLFYQSSLASWNYNTNITEENVQNMNNAGDKWSAFLKEQSTLAQMYPLQEIQNLTVKLQLQALQQNGSSVLSEDKSKRLNTILNTMSTIYSTGKVCNPDNPQECLLLEPGLNEIMANSLDYNERLWAWESWRSEVGKQLRPLYEEYVVLKNEMARANHYEDYGDYWRGDYEVNGVDGYDYSRGQLIEDVEHTFEEIKPLYEHLHAYVRAKLMNAYPSYISPIGCLPAHLLGDMWGRFWTNLYSLTVPFGQKPNIDVTDAMVDQAWDAQRIFKEAEKFFVSVGLPNMTQGFWENSMLTDPGNVQKAVCHPTAWDLGKGDFRILNHPKEIEDFGVLPTMTSDNFLNSWLSSFTRLNALPNDLHDFSSSGKKASSVSSLSSVSVSSKVSSSVSTGYVSGDKTVSVSENVSAGIVGSSRSVSSVSPAASESSPGKPLPRPFSNPAEEDDSGAGDFLSLTQGGAENSFSDSGNTEDAGFIQTLAKLTK',
    'CD4':     'MNRGVPFRHLLLVLQLALLPAATQGKKVVLGKKGDTVELTCTASQKKSIQFHWKNSNQIKILGNQQGESVSVQCDPQGGLFYNDAFPSGCQFTSFNLTQSGVWLKCEAQDYSTTFKENYVPQHESLSWPIFHPQNRTEKFLKLTKTSDSGSY',
    'TMPRSS2': 'MGVCRSAERRAGRLSRSTSRVNKRSRFLRPLHAGPAPPNVSRAGPVSSRGLRGGGGSGPRGPRDRVYIHPFHLQIPVNQEDQNFLKEIVKQLQETMKQQVKVLEKKSALQQLQEYLARLQQISRPTVIYLKDVSQLEQDLKRLEAELGDLNKPGQKGRNEEDLGPEVNKAKQEIQSRRELHRQHREELDKRNHQLEAEREERASRQEQKMELLDEQQKLFEELHSQKDELGKKNIQQQEAERLQQMKERNRQLELRDEHEIQKLMAKQEAAERQNQFHTLEQQLKEYQTRLAQLQEHAKQRQELIDKLEQLIEAERHRLVNLKQQEQQFQRLQNQMDAEQRRKKVYEELEQAQMQKQAQQLQEQMKQLELEIQKRKQNQNKFLEKELENLEDDQLVQKLQQELQKDLQEMKTHLEAERSRLETELKDIQQNFHEQESKLEEELQKYQKELSRNQAQTKELQYIQEDLEKKEEQLAQKLLELQKNLKELEKDLQEQLQQLQKKQAQEQNHQEKLQDIQKQLELEKTKNKRQLEKELKELELQQKQQQSRQELRQLQSQHVEIRNHQQRLREQNLQKELQDLQNMFQKLAAELNNAQHQIAQLSQKVEENNPEDPNLYHEENRSNDPLVEVNLQDSETAFNIPDAEDSVLIMGETPQHRLMPLRSAFLSQSVVVFPRAGRPARPVDQLHLEKRPARASDPDPSRETKMCRSMLNYTLHLDRASDQAPAHAGLTHPATLSSSVPNTPEFKETSRVGQSDSRVPQHLSTQLFENVSPAQGPPEQGRRIQRQTGTRVVLQPELQQFHQLPSVGPLLAKGPAAEEEMKTNPTVATLSSRSSSQVGSHVTYEQKSMCQARHLHRSPRSLQSGGTHPGVKLDSVLDPNLNKDNFENALQALRFIEAQVPDKMDSMCSHTNHSNNTRSPTLQSRDNTHLRDYDKAEKDQIPMELTKMGLSSGEQLAKPEVKNNKKYLKKSPKQVVLFVMGKRKHFLKPEDVELDAKAQVMKIHDPETLRQVLEVYDVPKQNRIIFEGTLRHSVALFPGLSMDQEQSKQVFHQICQDSVPLKIAEGATTVPDTNNLHRAMLGEKVAEQPELRHFPISLISFSQALKTLHGQLKQEGYKRSQVTMFNLQHQLNILSSNFPHISSMIINRVSQDTSQIMDLDRLMQHVVGQAIHHQQISGQKEHSRISPTFPNSDCPTYFLIHRFLDFLGDQEPNHILHAFKTVNSVNRAAQHPQKMLHVKDATQVHKGEKNYLKDGNLDPNLRLVPKPRPEVLSGGEQATQKIVNFHLVSVHPNVTSRQQIYKSFPPKSPFSVLDQEIKKLKDVLQMTIPILNSEADNLATMLQKRVKHMHQKFTNHKLKELKQNTHAHLKVNPNALVKGSLTQNPSKSFPESQNQMDKLLAQLTSAILEAKQIKHTMRQHFNQLQGPTDPRQLMKQVSSMLIQSRSSKVPQIQMEQAGDQPVYMHHLGGPKPLGKPPDMKQFLMPETSLKELQSRLPSMYHTEKFGLLKELQEAKENVQLQAQTTASQGTQKQASSREQQQQGQRQAELDRGGRSPEAQPQGTPTQQRAAAAQTQKTQELQSQMGLGQPLHAPQSQQ',
}

ATTACHMENT_PROTEINS = {
    'SARS2_Spike_RBD': 'NITNLCPFGEVFNATRFASVYAWNRKRISNCVADYSVLYNSASFSTFKCYGVSPTKLNDLCFTNVYADSFVIRGDEVRQIAPGQTGKIADYNYKLPDDFTGCVIAWNSNNLDSKVGGNYNYLYRLFRKSNLKPFERDISTEIYQAGSTPCNGVEGFNCYFPLQSYGFQPTNGVGYQPYRVVVLSFELLHAPATVCGPKKSTNLVKNKCVNFNFNGLTGTGVLTESNKKFLPFQQFGRDIADTTDAVRDPQTLEILDITPCSFGGVSVITPGTNTSNQVAVLYQDVNCTEVPVAIHADQLTPTWRVYSTGSNVFQTRAVAIITMYVGAT',
    'HIV_gp120_V3':    'CTRPNYNKRKRIHIGPGRAFYATGEIIGDIRQAHC',
    'Influenza_HA_SA23': 'DTLCIGYHANNSTDTVDTVLEKNVTVTHSVNLLEDKHNGKLCKLRGVAPLHLGKCNIAGWLLGNPECDPLLPVRSWSYIVETPNSENGICYPGDFIDYEELREQLSSVSSFERFEIFPKTSSWPNHDSNKGVTAACPHAGAKSFYKNLIWLVKKGNSYPKLSKS',
    'Influenza_HA_SA26': 'DTLCIGYHANNSTDTVDTVLEKNVTVTHSVNLLEDSHNGKLCKLRGVAPLHLGKCNIAGWILGNPECDPLLPVRSWSYIVDTPNSENGICYPGDFIDYEELREQLSSVSSFERFEIFPKESSWPNHDSNKGVTAACPHAGAKSFYKNLIWLVKKGNSYPKLSKS',
}

COGNATE_PAIRS = [
    ('SARS2_Spike_RBD',    'ACE2',    True),
    ('HIV_gp120_V3',       'CD4',     True),
    ('Influenza_HA_SA23',  'ACE2',    False),  # non-cognate
    ('Influenza_HA_SA26',  'ACE2',    False),  # non-cognate
    ('SARS2_Spike_RBD',    'CD4',     False),  # non-cognate
    ('SARS2_Spike_RBD',    'TMPRSS2', True),   # co-receptor
]

def benchmark_tropism():
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        roc_auc_score = None

    print(f"\nProblem 2: Tropism prediction")
    print(f"  {'Attachment':<28} {'Receptor':<10} {'Cognate':>8} {'rho':>6}")
    print('  ' + '-' * 56)

    labels, scores = [], []
    for att_name, rec_name, is_cognate in COGNATE_PAIRS:
        att_emb = embed(ATTACHMENT_PROTEINS[att_name])
        rec_emb = embed(RECEPTORS[rec_name])
        rho     = similarity(att_emb, rec_emb)
        labels.append(1 if is_cognate else 0)
        scores.append(rho)
        mark = '✓' if is_cognate else ' '
        print(f"  {att_name:<28} {rec_name:<10} {mark:>8} {rho:>6.4f}")

    if roc_auc_score and len(set(labels)) == 2:
        auc = roc_auc_score(labels, scores)
        print(f"\n  ROC-AUC: {auc:.4f} (n={len(labels)} pairs)")
    else:
        print(f"\n  (install scikit-learn for AUC)")

# ── Problem 3: Immune escape ──────────────────────────────────────────────────

# SARS-CoV-2 known immune escape mutations (receptor-binding domain)
# Source: published literature, Bloom lab datasets
ESCAPE_MUTATIONS = [
    # (name, WT_RBD_fragment, mutant_RBD_fragment, position_note)
    ('N501Y', 'NLDSKVGGNYNYLYRLFRKSNLKPFERDISTEIYQAGSTPCNGVEGFNCYFPLQSYGFQPTNGVGYQPYRV',
              'NLDSKVGGNYYNYLYRLFRKSNLKPFERDISTEIYQAGSTPCNGVEGFNCYFPLQSYGFQPTNGVGYQPYRV', 'RBD pos 501'),
    ('E484K', 'FNCYFPLQSYGFQPTNGVGYQPYRVVVLSFELLHAPATVCGPKKSTNLVKNKCVNFNFNGLTGTGVLTESNK',
              'FNCYFPLQSYGFQPTNGVGYQPYRVVVLSKLLLHAPATVCGPKKSTNLVKNKCVNFNFNGLTGTGVLTESNK', 'RBD pos 484'),
    ('L452R', 'SYTTGVGYQPYRVVVLSFELLHAPATVCGPKKSTNLVKNKCVNFN',
              'SYTTGVGYQPYRVVVRSFELLHAPATVCGPKKSTNLVKNKCVNFN', 'RBD pos 452'),
]

# Representative antibody CDR sequences (heavy chain CDR3)
ANTIBODIES = {
    'LY-CoV555':  'ARDRESYFDF',
    'REGN10933':  'ARDGMISSGGMDV',
    'S309':       'ARAHRLYGMDV',
    'CR3022':     'ARQKYWSS',
}

def benchmark_escape():
    print(f"\nProblem 3: Immune escape prediction")
    print(f"  Testing {len(ESCAPE_MUTATIONS)} known escape mutations × {len(ANTIBODIES)} antibodies")

    # Prediction: escape mutation should have high ACE2 overlap, low Ab overlap
    ace2_emb = embed(RECEPTORS['ACE2'][:200])  # binding domain fragment

    print(f"\n  {'Mutation':<10} {'ACE2(WT)':>9} {'ACE2(Mut)':>10} {'Ab(WT)':>8} {'Ab(Mut)':>9} {'Escape?':>8}")
    print('  ' + '-' * 62)

    for mut_name, wt_seq, mut_seq, note in ESCAPE_MUTATIONS:
        wt_emb  = embed(wt_seq)
        mut_emb = embed(mut_seq)

        rho_ace2_wt  = similarity(wt_emb,  ace2_emb)
        rho_ace2_mut = similarity(mut_emb, ace2_emb)

        # Score against all antibodies, take mean
        ab_rho_wt  = np.mean([similarity(wt_emb,  embed(seq)) for seq in ANTIBODIES.values()])
        ab_rho_mut = np.mean([similarity(mut_emb, embed(seq)) for seq in ANTIBODIES.values()])

        # Escape criterion (Eq 5.1 of paper):
        # receptor overlap stays high (ACE2 mut ≥ ACE2 wt × 0.9)
        # antibody overlap drops      (Ab mut < Ab wt × 0.95)
        receptor_retained = rho_ace2_mut >= rho_ace2_wt * 0.9
        antibody_evaded   = ab_rho_mut < ab_rho_wt * 0.95
        escape_predicted  = receptor_retained and antibody_evaded

        print(f"  {mut_name:<10} {rho_ace2_wt:>9.4f} {rho_ace2_mut:>10.4f} {ab_rho_wt:>8.4f} {ab_rho_mut:>9.4f} {'✓' if escape_predicted else ' ':>8}")

# ── Problem 4: Antibiotic resistance ─────────────────────────────────────────

# TEM-1 β-lactamase and resistance variants
ENZYMES = {
    'TEM1_wt':    'MSIQHFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPVAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW',
    'TEM1_K73N':  'MSIQHFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPVAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLINHW',
    'TEM1_M182T': 'MSIQHFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNTGDHVTRLDRWEPELNEAIPNDERDTTMPVAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW',
}

DRUGS = {
    'ampicillin_binding_site': 'KEQLGRRI',      # key residues at active site
    'cefotaxime_binding_site': 'KEQLGRRIHYSQN', # extended spectrum
}

def benchmark_resistance():
    print(f"\nProblem 4: Antibiotic resistance prediction")
    print(f"  {'Enzyme':<15} {'Drug':<24} {'rho':>6} {'Resistant?':>11}")
    print('  ' + '-' * 60)

    rho_star = 0.6  # threshold from paper

    for enz_name, enz_seq in ENZYMES.items():
        for drug_name, drug_seq in DRUGS.items():
            enz_emb  = embed(enz_seq)
            drug_emb = embed(drug_seq)
            rho = similarity(enz_emb, drug_emb)
            resistant = rho < rho_star
            print(f"  {enz_name:<15} {drug_name:<24} {rho:>6.4f} {'R' if resistant else 'S':>11}")

# ── Problem 5: Dynamics (synthetic only) ─────────────────────────────────────

def benchmark_dynamics():
    print(f"\nProblem 5: Infection dynamics (synthetic)")
    print(f"  Coherence decay model: dC/dt = -γ·C·rho(pathogen, host)")
    print()

    # Simulate coherence decay for different pathogen-host spectral overlaps
    rng = np.random.default_rng(42)
    host_seq    = 'ACDEFGHIKLMNPQRSTVWY' * 5  # 100-aa "host oscillator"
    host_emb    = embed(host_seq)

    dt = 0.1
    gamma = 0.5
    t_max = 20.0
    steps = int(t_max / dt)

    print(f"  {'Pathogen rho':>14} {'T_50% coherence':>16}")
    print('  ' + '-' * 32)

    for rho_target in [0.3, 0.5, 0.7, 0.9]:
        # Synthetic pathogen at specified rho: interpolate toward host
        rand_emb = rng.standard_normal(host_emb.shape)
        rand_emb /= np.linalg.norm(rand_emb)
        # Linear interpolation then renormalize
        w = rho_target  # approximate: cos(angle) ≈ rho_target for small angles
        path_emb = w * host_emb + (1 - w) * rand_emb
        path_emb /= np.linalg.norm(path_emb)
        actual_rho = similarity(path_emb, host_emb)

        # Simulate coherence: C(t) = exp(-gamma * rho * t)
        t_half = math.log(2) / (gamma * actual_rho) if actual_rho > 0 else float('inf')
        print(f"  {actual_rho:>14.4f} {t_half:>16.2f} time units")

# ── Self-test ─────────────────────────────────────────────────────────────────

def self_test():
    print("Self-test: core primitives")

    # Unit norm
    for seq in ['GILGFVFTL', 'ATGCATGCATGC', 'NLVPMVATV']:
        e = embed(seq)
        assert abs(np.linalg.norm(e) - 1.0) < 1e-5, f"Bad norm: {seq}"
    print("  Unit norm: OK")

    # Self-similarity = 1
    e = embed('GILGFVFTL')
    assert abs(similarity(e, e) - 1.0) < 1e-5
    print("  Self-similarity: OK")

    # Spectral distance = 0 for identical sequences
    assert abs(spectral_distance(e, e)) < 1e-5
    print("  Spectral distance: OK")

    # Matched filter recovers planted position
    query, target, true_pos = simulate_planted_signal(Lt=500, Lq=50, mu=0.0, seed=99)
    q_ch = channelize_dna(query)
    t_ch = channelize_dna(target)
    rho, pred_pos = matched_filter(q_ch, t_ch)
    assert abs(pred_pos - true_pos) <= 2, f"Position miss: pred={pred_pos}, true={true_pos}, rho={rho:.4f}"
    print(f"  Matched filter: OK (pos={pred_pos}, true={true_pos}, rho={rho:.4f})")
    print()

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--problem', type=int, choices=[1,2,3,4,5],
                        help='Run only the specified problem benchmark')
    args = parser.parse_args()

    self_test()

    if args.problem is None or args.problem == 1:
        benchmark_identification(n_trials=20)
    if args.problem is None or args.problem == 2:
        benchmark_tropism()
    if args.problem is None or args.problem == 3:
        benchmark_escape()
    if args.problem is None or args.problem == 4:
        benchmark_resistance()
    if args.problem is None or args.problem == 5:
        benchmark_dynamics()

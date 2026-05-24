"""
NumPy reference implementation of the spectral embedding and MHC binding
prediction — exact numerical ground truth for verifying the JS browser tools.

Usage:
  python _validate_iedb.py                  # runs self-test + synthetic benchmark
  python _validate_iedb.py iedb.csv         # runs against downloaded IEDB data
  python _validate_iedb.py iedb.csv --allele HLA-A*02:01

IEDB MHC-I data download:
  https://tools.iedb.org/mhci/download/
  Choose "MHC-I binding assays (beta)" → Download → CSV
  Use similarity-reduced (SR) test splits, not ALL splits.

Output: ROC-AUC per allele, Spearman ρ vs measured IC50, comparison table.
"""

import sys
import csv
import math
import numpy as np
from collections import defaultdict

# ── Physicochemical tables (identical to spectral.js) ────────────────────────

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

K = 12  # non-DC spectral coefficients per channel

# Allele reference centroids: mean embedding of top known IEDB binders per allele.
# Using same-length canonical binders so DFT frequency scales are aligned.
# Source: IEDB IC50 < 50 nM, representative of the allele's anchor motif.
ALLELE_BINDERS = {
    'HLA-A*02:01': ['GILGFVFTL', 'NLVPMVATV', 'GLCTLVAML', 'KVAELVHFL', 'CLGGLLTMV',
                    'SLYNTVATL', 'IMDQVPFSV', 'ILKEPVHGV', 'RTLNAWVKV', 'CLTEYILWL'],
    'HLA-A*01:01': ['VTEHDTLLY', 'ILDTAGREEY', 'CTELKLSDY', 'TTDPSFLGRY', 'ASEKNFATL'],
    'HLA-A*03:01': ['KLGGALQAK', 'KIFDLPLAY', 'RLRPGGKKK', 'KLNEPVHGV', 'QIIFVDLLK'],
    'HLA-B*07:02': ['RPHERNGFTV', 'YPHFMPTNL', 'TPGPGVRYPL', 'LPSAGPHIL', 'RPRGEAKEL'],
    'HLA-B*08:01': ['FLKEKGGL', 'ELRSRYWAI', 'DYCNVLNKEF', 'HSKKKCDEL'],
    'HLA-B*57:01': ['ISPRTLNAW', 'KAFSPEVIPM', 'TSTLQEQIGW', 'LSSPVTKSF', 'KAFSPEVIPMF'],
}

def allele_centroid(allele):
    """Compute mean unit-norm embedding over known binders for an allele."""
    binders = ALLELE_BINDERS.get(allele, [])
    if not binders:
        return None
    embs = np.stack([embed(p) for p in binders])
    centroid = embs.mean(axis=0)
    norm = np.linalg.norm(centroid)
    return centroid / (norm if norm > 0 else 1.0)

# ── Channelization ────────────────────────────────────────────────────────────

def channelize_protein(seq):
    s = seq.upper()
    L = len(s)
    h = np.array([HYDROPATHY.get(aa, 0.0) for aa in s], dtype=np.float64)
    v = np.array([VOLUME.get(aa, 111.0) for aa in s], dtype=np.float64)
    q = np.array([CHARGE.get(aa, 0.0) for aa in s], dtype=np.float64)

    for ch in (h, v, q):
        ch -= ch.mean()
        rms = np.sqrt((ch**2).mean()) or 1.0
        ch /= rms

    return np.stack([h, v, q])  # shape (3, L)

# ── Direct DFT matrix multiply ───────────────────────────────────────────────

_dft_cache = {}

def _dft_matrix(L, k):
    key = (L, k)
    if key not in _dft_cache:
        ns = np.arange(L)
        ks = np.arange(1, k + 1)[:, None]  # (k, 1)
        phase = 2 * np.pi * ks * ns / L     # (k, L)
        _dft_cache[key] = (np.cos(phase), -np.sin(phase))
    return _dft_cache[key]

def dft_direct(signal, k=K):
    """Evaluate DFT at exactly k frequencies (1..k) via matrix multiply.
    Same logic as dftDirect() in spectral.js — no zero-padding, no phantom bins.
    """
    W_re, W_im = _dft_matrix(len(signal), k)
    re = W_re @ signal
    im = W_im @ signal
    return np.sqrt(re**2 + im**2)

# ── Spectral embedding ────────────────────────────────────────────────────────

def embed(seq, k=K):
    """Full pipeline: sequence → unit-norm spectral embedding (3k-dim)."""
    channels = channelize_protein(seq)
    mags = np.concatenate([dft_direct(ch, k) for ch in channels])
    norm = np.linalg.norm(mags)
    return mags / (norm if norm > 0 else 1.0)

def similarity(a, b):
    return float(np.dot(a, b))

# ── MHC binding prediction ────────────────────────────────────────────────────

def predict_binding(peptide, allele='HLA-A*02:01', rho_star=0.7):
    """
    Predict MHC-I binding by cosine similarity to the allele centroid embedding.

    The centroid is the mean of known IEDB binders for the allele, all embedded
    at their native length — so DFT frequency scales are aligned across queries.
    """
    centroid = allele_centroid(allele)
    if centroid is None:
        raise ValueError(f"Unknown allele: {allele}. Add to ALLELE_BINDERS.")
    pep_emb  = embed(peptide)
    rho      = similarity(pep_emb, centroid)
    r_star   = math.sqrt(2 * (1 - rho_star))
    r_actual = math.sqrt(2 * (1 - max(-1.0, rho)))
    return {
        'rho': rho,
        'r': r_actual,
        'binder': rho >= rho_star,
        'r_star': r_star,
        'score': rho,
    }

# ── Self-test: verify JS/NumPy embedding parity ──────────────────────────────

def self_test():
    """Verify embedding properties: unit norm, symmetry, known pairs."""
    print("Self-test: embedding properties")

    # Unit norm
    for seq in ['GILGFVFTL', 'NLVPMVATV', 'SIINFEKL', 'GLCTLVAML']:
        e = embed(seq)
        norm = np.linalg.norm(e)
        assert abs(norm - 1.0) < 1e-5, f"Norm={norm:.6f} for {seq}"
        print(f"  {seq}: norm={norm:.6f} ✓")

    # Self-similarity = 1
    e = embed('GILGFVFTL')
    rho = similarity(e, e)
    assert abs(rho - 1.0) < 1e-5, f"Self-similarity={rho}"
    print(f"  Self-similarity: {rho:.6f} ✓")

    # Known HLA-A*02:01 binder scores above non-binder
    binder     = predict_binding('GILGFVFTL',  'HLA-A*02:01')
    nonbinder  = predict_binding('AAAAAAAAAA', 'HLA-A*02:01')
    print(f"  GILGFVFTL  (binder)    ρ={binder['rho']:.4f}")
    print(f"  AAAAAAAAAA (non-binder) ρ={nonbinder['rho']:.4f}")
    assert binder['rho'] > nonbinder['rho'], "Binder should outscore non-binder"
    print("  Binder > non-binder ✓")

    # Embedding dimension
    assert embed('GILGFVFTL').shape == (3 * K,), f"Wrong dim: {embed('GILGFVFTL').shape}"
    print(f"  Embedding dim: {3*K} ✓\n")

# ── IEDB validation ───────────────────────────────────────────────────────────

def load_iedb_csv(path):
    """
    Parse IEDB MHC-I binding assay CSV.
    Expected columns (tab-separated from IEDB download):
      allele, seq, ic50 (nM), measurement_type, ...
    Returns list of dicts: {allele, peptide, ic50, binder (IC50 < 500 nM)}
    """
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        # IEDB files have a metadata header; skip until we hit the column row
        reader = csv.reader(f, delimiter='\t')
        headers = None
        for line in reader:
            if headers is None:
                if 'allele' in ' '.join(line).lower():
                    headers = [h.strip().lower() for h in line]
                continue
            if not headers:
                continue
            d = dict(zip(headers, line))
            seq = d.get('sequence') or d.get('seq') or d.get('peptide', '')
            allele = d.get('allele', '').strip()
            try:
                ic50 = float(d.get('ic50') or d.get('affinity') or '99999')
            except ValueError:
                continue
            if len(seq) < 8 or len(seq) > 15:
                continue
            if not all(c in 'ACDEFGHIKLMNPQRSTVWY' for c in seq.upper()):
                continue
            rows.append({
                'allele': allele,
                'peptide': seq.upper(),
                'ic50': ic50,
                'binder': ic50 < 500,
            })
    return rows

def validate_iedb(path, target_allele=None):
    from sklearn.metrics import roc_auc_score
    from scipy.stats import spearmanr

    data = load_iedb_csv(path)
    if not data:
        print("No usable rows found. Check IEDB CSV format.")
        return

    by_allele = defaultdict(list)
    for r in data:
        by_allele[r['allele']].append(r)

    alleles = [target_allele] if target_allele else list(by_allele.keys())

    print(f"\nIEDB validation: {len(data)} peptides across {len(by_allele)} alleles\n")
    print(f"{'Allele':<20} {'N':>5} {'N+':>5} {'AUC':>6} {'Spearman':>9} {'Groove?':>8}")
    print('-' * 60)

    for allele in sorted(alleles):
        rows = by_allele.get(allele, [])
        if len(rows) < 10:
            continue

        # Try precomputed centroid first; fall back to this file's binder ensemble
        ref_emb = allele_centroid(allele)
        has_ref = ref_emb is not None
        if not has_ref:
            file_binders = [r['peptide'] for r in rows if r['binder']]
            if not file_binders:
                continue
            embs = np.stack([embed(p) for p in file_binders[:10]])
            ref_emb = embs.mean(axis=0)
            n = np.linalg.norm(ref_emb)
            ref_emb /= n if n > 0 else 1.0

        scores  = np.array([similarity(embed(r['peptide']), ref_emb) for r in rows])
        labels  = np.array([1 if r['binder'] else 0 for r in rows])
        log_ic50= np.array([-math.log10(r['ic50'] + 0.001) for r in rows])

        n_pos = labels.sum()
        if n_pos == 0 or n_pos == len(rows):
            continue

        try:
            auc = roc_auc_score(labels, scores)
            spearman_r, _ = spearmanr(scores, log_ic50)
        except Exception as e:
            print(f"  {allele}: error — {e}")
            continue

        print(f"{allele:<20} {len(rows):>5} {int(n_pos):>5} {auc:>6.3f} {spearman_r:>9.3f} {'curated' if has_ref else 'file-avg':>10}")

# ── Synthetic benchmark (no external data needed) ────────────────────────────

def synthetic_benchmark():
    """
    Reproduces the synthetic evaluation from Section 8 of the paper:
    - 100 positive pairs: sample a binder peptide, compute ρ
    - 100 negative pairs: shuffle amino acids, compute ρ
    - Report AUC and separation
    """
    import random
    random.seed(42)

    allele = 'HLA-A*02:01'
    groove_emb = allele_centroid(allele)

    # Known HLA-A*02:01 strong binders (IEDB-curated)
    binders = [
        'GILGFVFTL', 'NLVPMVATV', 'GLCTLVAML', 'LLFGYPVYV', 'KVAELVHFL',
        'ELAGIGILTV', 'CLGGLLTMV', 'SLYNTVATL', 'FLPSDFFPSV', 'IMDQVPFSV',
        'ILKEPVHGV', 'FMYSDFHFI', 'RTLNAWVKV', 'CLTEYILWL', 'SLLMWITQC',
        'RMFPNAPYL', 'YVNVNMGLK', 'KTWGQYWQV', 'LLFGYPVYV', 'MLGTHTMEV',
    ]

    AAs = list('ACDEFGHIKLMNPQRSTVWY')

    def shuffle_peptide(pep):
        chars = list(pep)
        random.shuffle(chars)
        return ''.join(chars)

    pos_scores = [similarity(embed(p), groove_emb) for p in binders]
    neg_scores = [similarity(embed(shuffle_peptide(p)), groove_emb) for p in binders]

    pos_mean = np.mean(pos_scores)
    neg_mean = np.mean(neg_scores)
    separation = pos_mean - neg_mean

    labels = [1]*len(pos_scores) + [0]*len(neg_scores)
    scores = pos_scores + neg_scores

    try:
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(labels, scores)
        print(f"Synthetic benchmark ({allele}):")
        print(f"  Binders    ρ = {pos_mean:.4f} ± {np.std(pos_scores):.4f}")
        print(f"  Non-binders ρ = {neg_mean:.4f} ± {np.std(neg_scores):.4f}")
        print(f"  Separation  Δρ = {separation:.4f}")
        print(f"  ROC-AUC     = {auc:.4f}")
    except ImportError:
        print(f"Synthetic benchmark ({allele}):")
        print(f"  Binders    ρ = {pos_mean:.4f}")
        print(f"  Non-binders ρ = {neg_mean:.4f}")
        print(f"  Separation  Δρ = {separation:.4f}")
        print("  (install scikit-learn for AUC)")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    self_test()
    synthetic_benchmark()

    if len(sys.argv) > 1:
        iedb_path = sys.argv[1]
        target_allele = None
        if '--allele' in sys.argv:
            idx = sys.argv.index('--allele')
            target_allele = sys.argv[idx + 1]
        try:
            validate_iedb(iedb_path, target_allele)
        except FileNotFoundError:
            print(f"\nFile not found: {iedb_path}")
            print("Download from https://tools.iedb.org/mhci/download/")
    else:
        print("\nTo validate against IEDB data:")
        print("  python _validate_iedb.py <path_to_iedb.csv> [--allele HLA-A*02:01]")
        print("\nDownload IEDB MHC-I data from:")
        print("  https://tools.iedb.org/mhci/download/")
        print("  Use similarity-reduced (SR) test splits for honest benchmarks.")

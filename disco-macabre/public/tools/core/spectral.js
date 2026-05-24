/**
 * spectral.js — Universal spectral embedding engine
 *
 * Implements: channelization → DFT → spectral embedding → similarity
 * for both DNA/RNA (4-channel) and protein (3-channel physicochemical) sequences.
 *
 * All operations are deterministic from sequence alone (empty database principle):
 * no pre-stored embeddings required.
 */

// ── Physicochemical tables ────────────────────────────────────────────────────

const HYDROPATHY = {
  A:1.8,  R:-4.5, N:-3.5, D:-3.5, C:2.5,  Q:-3.5, E:-3.5, G:-0.4,
  H:-3.2, I:4.5,  L:3.8,  K:-3.9, M:1.9,  F:2.8,  P:-1.6, S:-0.8,
  T:-0.7, W:-0.9, Y:-1.3, V:4.2
};

const VOLUME = {
  A:88.6,  R:173.4, N:114.1, D:111.1, C:108.5, Q:143.8, E:138.4, G:60.1,
  H:153.2, I:166.7, L:166.7, K:168.6, M:162.9, F:189.9, P:112.7, S:89.0,
  T:116.1, W:227.8, Y:193.6, V:140.0
};

const CHARGE = {
  A:0, R:1, N:0, D:-1, C:0, Q:0, E:-1, G:0, H:0.1, I:0,
  L:0, K:1, M:0, F:0, P:0, S:0, T:0, W:0, Y:0, V:0
};

const DNA_CHANNELS = { A:[1,0,0,0], T:[0,1,0,0], G:[0,0,1,0], C:[0,0,0,1],
                       U:[0,1,0,0], a:[1,0,0,0], t:[0,1,0,0], g:[0,0,1,0],
                       c:[0,0,0,1], u:[0,1,0,0] };

// ── Channelization ────────────────────────────────────────────────────────────

/**
 * Channelize a protein sequence into 3 physicochemical channels.
 * Returns { channels: Float32Array[3][L], L }
 */
function channelizeProtein(seq) {
  const s = seq.toUpperCase();
  const L = s.length;
  const h = new Float32Array(L);
  const v = new Float32Array(L);
  const q = new Float32Array(L);

  let hMean = 0, vMean = 0, qMean = 0;
  for (let i = 0; i < L; i++) {
    h[i] = HYDROPATHY[s[i]] ?? 0;
    v[i] = VOLUME[s[i]] ?? 111.0;
    q[i] = CHARGE[s[i]] ?? 0;
    hMean += h[i]; vMean += v[i]; qMean += q[i];
  }
  hMean /= L; vMean /= L; qMean /= L;
  for (let i = 0; i < L; i++) { h[i] -= hMean; v[i] -= vMean; q[i] -= qMean; }

  // Normalize each channel by its RMS
  const rms = (arr) => {
    let s = 0; for (const x of arr) s += x * x;
    return Math.sqrt(s / arr.length) || 1;
  };
  const rH = rms(h), rV = rms(v), rQ = rms(q);
  for (let i = 0; i < L; i++) { h[i] /= rH; v[i] /= rV; q[i] /= rQ; }

  return { channels: [h, v, q], L, type: 'protein' };
}

/**
 * Channelize a DNA/RNA sequence into 4 one-hot channels.
 * Returns { channels: Float32Array[4][L], L }
 */
function channelizeDNA(seq) {
  const L = seq.length;
  const ch = [new Float32Array(L), new Float32Array(L),
               new Float32Array(L), new Float32Array(L)];
  for (let i = 0; i < L; i++) {
    const enc = DNA_CHANNELS[seq[i]];
    if (enc) for (let c = 0; c < 4; c++) ch[c][i] = enc[c];
  }
  // DC subtraction
  for (let c = 0; c < 4; c++) {
    let m = 0; for (const x of ch[c]) m += x; m /= L;
    for (let i = 0; i < L; i++) ch[c][i] -= m;
  }
  return { channels: ch, L, type: 'dna' };
}

// ── DFT ──────────────────────────────────────────────────────────────────────

function nextPow2(n) { let p = 1; while (p < n) p <<= 1; return p; }

// Trig cache: key = `${L}_${k}` → {re, im} Float64Arrays of size k×L
const _dftCache = new Map();

/**
 * Direct DFT matrix multiply: evaluates DFT at exactly k frequencies (1..k).
 * O(L*k) — correct for any L, no zero-padding, no phantom zero bins.
 * Caches trig tables per (L, k) pair for repeated calls on same-length sequences.
 * Returns Float32Array of k magnitudes (bins 1..k, DC excluded).
 */
function dftDirect(signal, k) {
  const L = signal.length;
  const key = `${L}_${k}`;
  let mat = _dftCache.get(key);
  if (!mat) {
    const re = new Float64Array(k * L);
    const im = new Float64Array(k * L);
    for (let ki = 1; ki <= k; ki++) {
      for (let n = 0; n < L; n++) {
        const phase = 2 * Math.PI * ki * n / L;
        re[(ki - 1) * L + n] = Math.cos(phase);
        im[(ki - 1) * L + n] = -Math.sin(phase);
      }
    }
    mat = { re, im };
    _dftCache.set(key, mat);
  }
  const { re, im } = mat;
  const mag = new Float32Array(k);
  for (let ki = 0; ki < k; ki++) {
    let r = 0, ix = 0;
    const off = ki * L;
    for (let n = 0; n < L; n++) {
      r  += signal[n] * re[off + n];
      ix += signal[n] * im[off + n];
    }
    mag[ki] = Math.sqrt(r * r + ix * ix);
  }
  return mag;
}

/**
 * Real-input DFT via Cooley-Tukey FFT.
 * Pads to max(nextPow2(L), 32) to guarantee ≥16 positive-frequency bins
 * regardless of sequence length — used for the spectrum visualizer in mhc-binding.
 * Returns magnitude array of length N/2 (positive frequencies 0..N/2-1).
 */
function dft1d(signal) {
  const N = Math.max(nextPow2(signal.length), 32);
  const re = new Float64Array(N);
  const im = new Float64Array(N);
  for (let i = 0; i < signal.length; i++) re[i] = signal[i];

  // Bit-reversal permutation
  let j = 0;
  for (let i = 1; i < N; i++) {
    let bit = N >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }

  // Butterfly
  for (let len = 2; len <= N; len <<= 1) {
    const ang = -2 * Math.PI / len;
    const wRe = Math.cos(ang), wIm = Math.sin(ang);
    for (let i = 0; i < N; i += len) {
      let uRe = 1, uIm = 0;
      for (let k = 0; k < len / 2; k++) {
        const tRe = uRe * re[i+k+len/2] - uIm * im[i+k+len/2];
        const tIm = uRe * im[i+k+len/2] + uIm * re[i+k+len/2];
        re[i+k+len/2] = re[i+k] - tRe;
        im[i+k+len/2] = im[i+k] - tIm;
        re[i+k] += tRe; im[i+k] += tIm;
        const newURe = uRe * wRe - uIm * wIm;
        uIm = uRe * wIm + uIm * wRe; uRe = newURe;
      }
    }
  }

  const mag = new Float32Array(N / 2);
  for (let k = 0; k < N / 2; k++) mag[k] = Math.sqrt(re[k]*re[k] + im[k]*im[k]);
  return mag;
}

// ── Spectral Embedding ────────────────────────────────────────────────────────

const K = 12; // non-DC spectral coefficients per channel

/**
 * Compute the spectral embedding of a channelized sequence.
 * Returns Float32Array of dimension c*K (normalized to unit length).
 */
function embed(channelized, k = K) {
  const { channels } = channelized;
  const c = channels.length;
  const emb = new Float32Array(c * k);

  for (let ci = 0; ci < c; ci++) {
    const mag = dftDirect(channels[ci], k);
    for (let ki = 0; ki < k; ki++) emb[ci * k + ki] = mag[ki];
  }

  // L2-normalize
  let norm = 0;
  for (const x of emb) norm += x * x;
  norm = Math.sqrt(norm) || 1;
  for (let i = 0; i < emb.length; i++) emb[i] /= norm;

  return emb;
}

/**
 * Cosine similarity between two embeddings (∈ [-1, 1]).
 */
function similarity(a, b) {
  let dot = 0;
  for (let i = 0; i < a.length; i++) dot += a[i] * b[i];
  return dot;
}

/**
 * Full pipeline: sequence string → spectral embedding.
 * Autodetects DNA vs protein by character set.
 */
function embedSequence(seq) {
  const clean = seq.replace(/\s/g, '').toUpperCase();
  const isDNA = /^[ATGCUN]+$/.test(clean);
  const channelized = isDNA ? channelizeDNA(clean) : channelizeProtein(clean);
  return embed(channelized);
}

/**
 * Spectral distance: d = sqrt(2(1 - ρ)), maps similarity to Euclidean distance.
 */
function spectralDistance(a, b) {
  return Math.sqrt(2 * (1 - similarity(a, b)));
}

// ── Matched Filter (cross-correlation for long sequences) ─────────────────────

/**
 * Compute matched filter cross-correlation between query and target channel.
 * Returns peak normalized correlation ρ ∈ [-1, 1] and position of peak.
 */
function matchedFilter(queryChannel, targetChannel) {
  const Lq = queryChannel.length;
  const Lt = targetChannel.length;
  const N = nextPow2(Lq + Lt);

  const qRe = new Float64Array(N);
  const tRe = new Float64Array(N);
  const qIm = new Float64Array(N);
  const tIm = new Float64Array(N);

  for (let i = 0; i < Lq; i++) qRe[i] = queryChannel[i];
  for (let i = 0; i < Lt; i++) tRe[i] = targetChannel[i];

  // Forward FFT both
  fftInPlace(qRe, qIm, N);
  fftInPlace(tRe, tIm, N);

  // Multiply: cross-correlation = IFFT(conj(Q) * T)
  const cRe = new Float64Array(N);
  const cIm = new Float64Array(N);
  for (let k = 0; k < N; k++) {
    cRe[k] = qRe[k] * tRe[k] + qIm[k] * tIm[k];
    cIm[k] = qRe[k] * tIm[k] - qIm[k] * tRe[k];
  }
  ifftInPlace(cRe, cIm, N);

  // Peak search
  let maxVal = 0, maxPos = 0;
  for (let k = 0; k < N; k++) {
    const v = Math.abs(cRe[k]);
    if (v > maxVal) { maxVal = v; maxPos = k; }
  }

  // Normalize by sequence norms
  let qNorm = 0, tNorm = 0;
  for (const x of queryChannel) qNorm += x * x;
  for (const x of targetChannel) tNorm += x * x;
  const denom = Math.sqrt(qNorm * tNorm) || 1;

  return { rho: maxVal / denom, position: maxPos };
}

function fftInPlace(re, im, N) {
  let j = 0;
  for (let i = 1; i < N; i++) {
    let bit = N >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }
  for (let len = 2; len <= N; len <<= 1) {
    const ang = -2 * Math.PI / len;
    const wRe = Math.cos(ang), wIm = Math.sin(ang);
    for (let i = 0; i < N; i += len) {
      let uRe = 1, uIm = 0;
      for (let k = 0; k < len / 2; k++) {
        const tRe = uRe * re[i+k+len/2] - uIm * im[i+k+len/2];
        const tIm = uRe * im[i+k+len/2] + uIm * re[i+k+len/2];
        re[i+k+len/2] = re[i+k] - tRe;
        im[i+k+len/2] = im[i+k] - tIm;
        re[i+k] += tRe; im[i+k] += tIm;
        const nURe = uRe * wRe - uIm * wIm;
        uIm = uRe * wIm + uIm * wRe; uRe = nURe;
      }
    }
  }
}

function ifftInPlace(re, im, N) {
  for (let i = 0; i < N; i++) im[i] = -im[i];
  fftInPlace(re, im, N);
  for (let i = 0; i < N; i++) { re[i] /= N; im[i] = -im[i] / N; }
}

// ── Exports ───────────────────────────────────────────────────────────────────

export {
  channelizeProtein, channelizeDNA, dft1d, dftDirect, embed, embedSequence,
  similarity, spectralDistance, matchedFilter,
  HYDROPATHY, VOLUME, CHARGE, K
};

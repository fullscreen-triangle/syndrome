/**
 * cfc/sweeps.js -- parameter sweeps over the real kernel.
 *
 * These reproduce the validation experiments of the companion paper by
 * running the actual solver hundreds to thousands of times, in the
 * browser. Nothing is sampled from a fitted curve: every point is a
 * circuit that was built, solved and classified.
 *
 * Determinism: a small LCG is threaded explicitly so a given seed
 * yields the same sweep on every machine, which is what makes the
 * numbers quotable.
 */

import {
  Circuit, Cycle, admit, computeHolonomy,
  computeTolerance, cycleSum, dataFloor, fundamentalCycleBasis,
  gamma, minimumCycleBasis, numericalFloor, perturbEdge, witnessSet,
  CONSISTENT, INCONSISTENT, UNDECIDABLE,
} from "./kernel.js";

/** Deterministic LCG (MINSTD), so sweeps are reproducible. */
export function rng(seed = 20260819) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/** Build an n-species ring, optionally with chords. */
export function makeRing(n, muLo, muHi, sigma, r, chords = 0) {
  const c = new Circuit();
  for (let i = 0; i < n; i++) {
    // concentration 1 so that mu == mu0 exactly and Lambda is controlled
    c.addSpecies({ name: `S${i}`, mu0: muLo + r() * (muHi - muLo), concentration: 1, sigma });
  }
  for (let i = 0; i < n; i++) {
    c.addReaction({ name: `R${i}`, src: `S${i}`, dst: `S${(i + 1) % n}`, k: 0.1 });
  }
  for (let j = 0; j < chords; j++) {
    const a = Math.floor(r() * n);
    const b = (a + 2 + Math.floor(r() * Math.max(1, n - 3))) % n;
    if (a !== b && !c.reactions.some((x) => x.src === `S${a}` && x.dst === `S${b}`)) {
      c.addReaction({ name: `C${j}`, src: `S${a}`, dst: `S${b}`, k: 0.1 });
    }
  }
  return c.solve();
}

/** The whole-ring cycle, used where a single known cycle is wanted. */
function ringCycle(n) {
  return new Cycle(
    "ring",
    Array.from({ length: n }, (_, i) => [`R${i}`, +1]),
    [...Array.from({ length: n }, (_, i) => `S${i}`), "S0"]
  );
}

const clone = (c) => c.copy();

// =====================================================================
// V1 -- the noise scale, and the validity of the bound
// =====================================================================

export function sweepNoiseScale({
  lengths = [3, 5, 8, 12, 16, 20, 25, 30],
  ranges = [10, 100, 1000, 3000],
  trials = 24,
  seed = 20260819,
} = {}) {
  const r = rng(seed);
  const grid = [];
  let violations = 0;
  const slack = [];

  for (const L of lengths) {
    for (const lam of ranges) {
      let maxErr = 0, sumErr = 0, sumBound = 0;
      for (let t = 0; t < trials; t++) {
        const c = makeRing(L, -lam, lam, 1, r);
        const cy = ringCycle(L);
        const h = Math.abs(cycleSum(c, cy));
        const b = numericalFloor(c, cy);
        maxErr = Math.max(maxErr, h);
        sumErr += h;
        sumBound += b;
        if (h > b) violations++;
        if (h > 0) slack.push(b / h);
      }
      grid.push({
        length: L,
        lambda: lam,
        maxAbsError: maxErr,
        meanAbsError: sumErr / trials,
        meanBound: sumBound / trials,
        predicted: gamma(2 * L) * 2 * L * lam,
      });
    }
  }
  slack.sort((a, b) => a - b);
  return {
    kind: "noise",
    grid,
    violations,
    trials: lengths.length * ranges.length * trials,
    medianSlack: slack.length ? slack[Math.floor(slack.length / 2)] : null,
    maxObserved: Math.max(...grid.map((g) => g.maxAbsError)),
  };
}

// =====================================================================
// V2 -- what a fixed tolerance costs, at two precisions
// =====================================================================

/** Sum the ring in float32, where the floor rises to meet 1e-6. */
function ringSumFloat32(c, n) {
  const f32 = new Float32Array(n);
  for (let i = 0; i < n; i++) f32[i] = c.mu.get(`S${i}`);
  let acc = Math.fround(0);
  for (let i = 0; i < n; i++) {
    acc = Math.fround(acc + Math.fround(f32[(i + 1) % n] - f32[i]));
  }
  return Math.abs(acc);
}

export function sweepFixedTolerance({
  epsFixed = 1e-6,
  trials = 120,
  seed = 20260820,
} = {}) {
  const r = rng(seed);
  const strata = [
    { name: "short, low Λ", lo: 3, hi: 5, lambda: 20 },
    { name: "short, high Λ", lo: 3, hi: 5, lambda: 1800 },
    { name: "long, low Λ", lo: 15, hi: 22, lambda: 20 },
    { name: "long, high Λ", lo: 15, hi: 22, lambda: 1800 },
  ];
  const defects = [1e-8, 1e-7, 1e-6, 1e-5, 1e-3, 1e-1, 1];
  const out = [];

  for (const s of strata) {
    let fp64 = 0, fp32 = 0, unwarranted = 0;
    const miss = Object.fromEntries(defects.map((d) => [d, 0]));

    for (let t = 0; t < trials; t++) {
      const L = s.lo + Math.floor(r() * (s.hi - s.lo + 1));
      const c = makeRing(L, -s.lambda, s.lambda, 1, r);
      const cy = ringCycle(L);

      if (Math.abs(cycleSum(c, cy)) > epsFixed) fp64++;
      if (ringSumFloat32(c, L) > epsFixed) fp32++;

      for (const D of defects) {
        const d = perturbEdge(c, "R0", D);
        if (Math.abs(cycleSum(d, cy)) <= epsFixed) miss[D]++;
      }

      // A defect of 0.5 kJ/mol sits inside sigma = 1: the fixed test
      // asserts INCONSISTENT where the cycle-local test declines.
      const d = perturbEdge(c, "R0", 0.5);
      const fixedSaysBad = Math.abs(cycleSum(d, cy)) > epsFixed;
      const local = admit(computeHolonomy(d, cy), computeTolerance(d, cy)).label;
      if (fixedSaysBad && local === UNDECIDABLE) unwarranted++;
    }

    out.push({
      stratum: s.name,
      lambda: s.lambda,
      lengthRange: [s.lo, s.hi],
      n: trials,
      fp64: fp64 / trials,
      fp32: fp32 / trials,
      unwarranted: unwarranted / trials,
      missByDefect: Object.fromEntries(
        defects.map((d) => [d, miss[d] / trials])),
    });
  }

  return { kind: "fixed", epsFixed, defects, strata: out };
}

// =====================================================================
// V3 -- the trichotomy over (sigma, defect)
// =====================================================================

export function sweepTrichotomy({
  nSigma = 22,
  nDefect = 34,
  L = 6,
  lambda = 200,
  seed = 20260821,
} = {}) {
  const r = rng(seed);
  const sigmas = Array.from({ length: nSigma }, (_, i) =>
    Math.pow(10, -3 + (i / (nSigma - 1)) * 4));
  const defects = Array.from({ length: nDefect }, (_, i) =>
    Math.pow(10, -10 + (i / (nDefect - 1)) * 12));

  const base = makeRing(L, -lambda, lambda, 1, r);
  const cy = ringCycle(L);
  const epsNum = numericalFloor(base, cy);

  const code = { [CONSISTENT]: 0, [UNDECIDABLE]: 1, [INCONSISTENT]: 2 };
  const surface = [];
  const epsData = [];
  const counts = { CONSISTENT: 0, UNDECIDABLE: 0, INCONSISTENT: 0 };

  for (const s of sigmas) {
    const c = clone(base);
    for (const sp of c.species.values()) sp.sigma = s;
    epsData.push(dataFloor(c, cy));
    const row = [];
    for (const D of defects) {
      const d = perturbEdge(c, "R0", D);
      const lab = admit(computeHolonomy(d, cy), computeTolerance(d, cy)).label;
      row.push(code[lab]);
      counts[lab]++;
    }
    surface.push(row);
  }

  const total = nSigma * nDefect;
  return {
    kind: "trichotomy",
    sigmas, defects, surface, epsNum, epsData,
    counts,
    fractions: Object.fromEntries(
      Object.entries(counts).map(([k, v]) => [k, v / total])),
    gapOrders: Math.log10(epsData[Math.floor(nSigma / 2)] / epsNum),
  };
}

// =====================================================================
// V4 -- basis dependence, and the witness set
// =====================================================================

export function sweepBasis({ trials = 90, seed = 20260822 } = {}) {
  const r = rng(seed);
  const rows = [];
  let verdictDisagree = 0, flaggedDisagree = 0;
  let hitMcb = 0, hitFcb = 0, usable = 0;
  const wm = [], wf = [];

  for (let t = 0; t < trials; t++) {
    const n = 6 + Math.floor(r() * 6);
    let c = makeRing(n, -500, 500, 0.05, r, 2 + Math.floor(r() * 2));
    c = c.centrePotentials();
    const target = `R${Math.floor(r() * n)}`;
    const d = perturbEdge(c, target, 50);

    const mcb = minimumCycleBasis(d);
    const fcb = fundamentalCycleBasis(d);
    if (!mcb.length || !fcb.length) continue;
    usable++;

    const flag = (basis) => basis.filter((cy) =>
      admit(computeHolonomy(d, cy), computeTolerance(d, cy)).label === INCONSISTENT);
    const fm = flag(mcb), ff = flag(fcb);

    if ((fm.length > 0) !== (ff.length > 0)) verdictDisagree++;
    if (fm.length !== ff.length) flaggedDisagree++;

    const Wm = witnessSet(fm), Wf = witnessSet(ff);
    if (Wm.has(target)) hitMcb++;
    if (Wf.has(target)) hitFcb++;
    if (fm.length) wm.push(Wm.size);
    if (ff.length) wf.push(Wf.size);

    rows.push({
      species: n,
      flaggedMcb: fm.length, flaggedFcb: ff.length,
      witnessMcb: Wm.size, witnessFcb: Wf.size,
      meanLenMcb: mcb.reduce((a, x) => a + x.length, 0) / mcb.length,
      meanLenFcb: fcb.reduce((a, x) => a + x.length, 0) / fcb.length,
    });
  }

  const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : null);
  return {
    kind: "basis",
    trials: usable,
    verdictDisagree,
    flaggedDisagree,
    flaggedDisagreeRate: usable ? flaggedDisagree / usable : 0,
    witnessHitMcb: usable ? hitMcb / usable : 0,
    witnessHitFcb: usable ? hitFcb / usable : 0,
    meanWitnessMcb: mean(wm),
    meanWitnessFcb: mean(wf),
    rows,
  };
}

// =====================================================================
// V5 -- the detection guarantee
// =====================================================================

export function sweepDetection({
  sigmas = [0.01, 0.05, 0.2, 1, 5],
  points = 90,
  L = 6,
  lambda = 300,
  seed = 20260823,
} = {}) {
  const r = rng(seed);
  const curves = [];
  let violations = 0;

  for (const sig of sigmas) {
    const c = makeRing(L, -lambda, lambda, sig, r).centrePotentials();
    const cy = ringCycle(L);
    const tol = computeTolerance(c, cy);
    const Ds = Array.from({ length: points }, (_, i) =>
      Math.pow(10, -12 + (i / (points - 1)) * 15));
    const detected = [];
    let first = null;

    for (const D of Ds) {
      const d = perturbEdge(c, "R0", D);
      const hit = admit(computeHolonomy(d, cy), computeTolerance(d, cy)).label
        === INCONSISTENT;
      detected.push(hit ? 1 : 0);
      if (hit && first === null) first = D;
      if (D > 2 * tol.star && !hit) violations++;
    }

    curves.push({
      sigma: sig,
      epsNum: tol.numerical,
      epsData: tol.data,
      epsStar: tol.star,
      predicted: 2 * tol.star,
      empirical: first,
      ratio: first ? first / (2 * tol.star) : null,
      D: Ds,
      detected,
    });
  }

  const ratios = curves.map((c) => c.ratio).filter(Boolean);
  return {
    kind: "detection",
    curves,
    violations,
    evaluations: sigmas.length * points,
    minRatio: ratios.length ? Math.min(...ratios) : null,
    maxRatio: ratios.length ? Math.max(...ratios) : null,
  };
}

// =====================================================================
// Registry
// =====================================================================

export const SWEEPS = {
  noise: {
    id: "noise",
    label: "V1 · Noise scale",
    blurb: "The rounding error of a consistent cycle, against length and " +
      "potential range. Tests that the forward bound is never violated.",
    run: sweepNoiseScale,
    cost: "~770 circuits",
  },
  fixed: {
    id: "fixed",
    label: "V2 · Fixed tolerance",
    blurb: "What ε = 1e-6 costs: false positives at two precisions, missed " +
      "detections, and unwarranted positives.",
    run: sweepFixedTolerance,
    cost: "~480 circuits × 9 evaluations",
  },
  trichotomy: {
    id: "trichotomy",
    label: "V3 · Trichotomy",
    blurb: "The verdict over data quality × defect magnitude. Shows how " +
      "much of a realistic plane is undecidable.",
    run: sweepTrichotomy,
    cost: "~750 evaluations",
  },
  basis: {
    id: "basis",
    label: "V4 · Basis dependence",
    blurb: "Verdict is basis-independent; the flagged set is not. The " +
      "witness set is what survives.",
    run: sweepBasis,
    cost: "~90 networks × 2 bases",
  },
  detection: {
    id: "detection",
    label: "V5 · Detection",
    blurb: "Every defect above 2ε* is detected. Measures where the " +
      "empirical threshold actually sits.",
    run: sweepDetection,
    cost: "~450 evaluations",
  },
};

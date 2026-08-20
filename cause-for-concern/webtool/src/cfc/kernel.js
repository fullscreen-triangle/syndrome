/**
 * cfc/kernel.js -- the numerics, ported from the Python reference
 * implementation in ../../prototype/cfc/kernel.py.
 *
 * This is a real implementation, not a mock. Circuits are solved,
 * cycle bases are computed, and both tolerance floors are derived from
 * the same formulae the paper states:
 *
 *   mu_i    = mu0_i + RT ln c_i
 *   G_ij    = k_ij c_i / RT
 *   J_ij    = G_ij (mu_i - mu_j)
 *   eps_num = gamma_{2L} * 2 L Lambda        (Thm 3.2)
 *   eps_dat = z * sqrt(sum_i sigma_i^2)      (Thm 4.2)
 *
 * The cycle sum is identically zero for consistent edge data, so a
 * nonzero value is either rounding error or a genuine defect. Telling
 * those apart is the whole point.
 */

export const MACH_U = Math.pow(2, -53);      // IEEE-754 binary64
export const RT_DEFAULT = 2.577;             // kJ/mol at T = 310 K
export const Z_ALPHA = 2.5758293035489004;   // two-sided, alpha = 0.01

export const CONSISTENT = "CONSISTENT";
export const UNDECIDABLE = "UNDECIDABLE";
export const INCONSISTENT = "INCONSISTENT";

export class KernelError extends Error {}

// ---------------------------------------------------------------------
// Circuit
// ---------------------------------------------------------------------

export class Circuit {
  constructor(RT = RT_DEFAULT) {
    this.species = new Map();     // name -> {name, mu0, concentration, sigma}
    this.reactions = [];          // {name, src, dst, k}
    this.RT = RT;
    this.mu = new Map();
    this.G = new Map();
    this.J = new Map();
    this.edgeOffset = new Map();  // reaction name -> offset on d_e
    this.solved = false;
    this.centred = false;
    this.gaugeOffset = 0;
  }

  addSpecies(s) {
    if (!(s.concentration > 0)) {
      throw new KernelError(`species ${s.name}: concentration must be > 0`);
    }
    this.species.set(s.name, { sigma: null, ...s });
  }

  addReaction(r) {
    for (const end of [r.src, r.dst]) {
      if (!this.species.has(end)) {
        throw new KernelError(`reaction ${r.name}: unknown species '${end}'`);
      }
    }
    if (!(r.k > 0)) throw new KernelError(`reaction ${r.name}: k must be > 0`);
    const existing = this.reactions.find((x) => x.name === r.name);
    if (existing) Object.assign(existing, r);
    else this.reactions.push({ ...r });
  }

  solve() {
    this.mu = new Map();
    for (const [name, s] of this.species) {
      this.mu.set(name, s.mu0 + this.RT * Math.log(s.concentration));
    }
    this.G = new Map();
    this.J = new Map();
    for (const r of this.reactions) {
      const g = (r.k * this.species.get(r.src).concentration) / this.RT;
      this.G.set(r.name, g);
      this.J.set(r.name, g * (this.mu.get(r.src) - this.mu.get(r.dst)));
    }
    this.solved = true;
    return this;
  }

  copy() {
    const c = new Circuit(this.RT);
    for (const [k, v] of this.species) c.species.set(k, { ...v });
    c.reactions = this.reactions.map((r) => ({ ...r }));
    c.edgeOffset = new Map(this.edgeOffset);
    c.mu = new Map(this.mu);
    c.G = new Map(this.G);
    c.J = new Map(this.J);
    c.solved = this.solved;
    c.centred = this.centred;
    c.gaugeOffset = this.gaugeOffset;
    return c;
  }

  /** Edge data as supplied: gradient part plus any injected offset. */
  deltaMu(r) {
    return (
      this.mu.get(r.dst) - this.mu.get(r.src) + (this.edgeOffset.get(r.name) || 0)
    );
  }

  /**
   * Shift all potentials so max|mu| is minimised. Changes no cycle sum
   * mathematically; lowers the numerical floor, because rounding error
   * scales with operand magnitude rather than with their difference.
   */
  centrePotentials() {
    if (!this.solved) this.solve();
    const out = this.copy();
    const vals = [...out.mu.values()];
    if (vals.length) {
      const lo = Math.min(...vals);
      const hi = Math.max(...vals);
      const off = -0.5 * (lo + hi);
      for (const [k, v] of out.mu) out.mu.set(k, v + off);
      out.gaugeOffset = off;
    }
    out.centred = true;
    return out;
  }

  nodeBalance() {
    const bal = new Map();
    for (const n of this.species.keys()) bal.set(n, 0);
    for (const r of this.reactions) {
      bal.set(r.src, bal.get(r.src) - this.J.get(r.name));
      bal.set(r.dst, bal.get(r.dst) + this.J.get(r.name));
    }
    return bal;
  }

  cyclomaticNumber() {
    const n = this.species.size;
    const m = this.reactions.length;
    return m - n + countComponents(this.species.keys(), this.reactions);
  }
}

function countComponents(nodes, reactions) {
  const parent = new Map();
  for (const n of nodes) parent.set(n, n);
  const find = (x) => {
    while (parent.get(x) !== x) {
      parent.set(x, parent.get(parent.get(x)));
      x = parent.get(x);
    }
    return x;
  };
  for (const r of reactions) {
    const a = find(r.src);
    const b = find(r.dst);
    if (a !== b) parent.set(a, b);
  }
  const roots = new Set();
  for (const n of parent.keys()) roots.add(find(n));
  return roots.size;
}

// ---------------------------------------------------------------------
// Cycles
// ---------------------------------------------------------------------

export class Cycle {
  constructor(name, edges, nodes) {
    this.name = name;
    this.edges = edges;        // [[reactionName, +1|-1], ...]
    this.nodes = nodes;
  }
  get length() {
    return this.edges.length;
  }
  edgeNames() {
    return new Set(this.edges.map(([e]) => e));
  }
}

function adjacency(c, exclude = null) {
  const adj = new Map();
  for (const n of c.species.keys()) adj.set(n, []);
  for (const r of c.reactions) {
    if (r.name === exclude) continue;
    adj.get(r.src).push([r.dst, r.name]);
    adj.get(r.dst).push([r.src, r.name]);
  }
  return adj;
}

function nodesOf(edges, byName, start) {
  const nodes = [start];
  let cur = start;
  for (const [ename] of edges) {
    const r = byName.get(ename);
    const nxt = r.src === cur ? r.dst : r.src;
    nodes.push(nxt);
    cur = nxt;
  }
  return nodes;
}

function shortestPathExcluding(c, a, b, exclude) {
  const adj = adjacency(c, exclude);
  const prev = new Map([[a, null]]);
  const q = [a];
  let qi = 0;
  while (qi < q.length) {
    const u = q[qi++];
    if (u === b) break;
    for (const [v, ename] of adj.get(u) || []) {
      if (!prev.has(v)) {
        prev.set(v, [u, ename]);
        q.push(v);
      }
    }
  }
  if (!prev.has(b)) return null;
  const byName = new Map(c.reactions.map((r) => [r.name, r]));
  const out = [];
  let node = b;
  while (prev.get(node) !== null) {
    const [u, ename] = prev.get(node);
    const r = byName.get(ename);
    out.push([ename, r.src === u ? +1 : -1]);
    node = u;
  }
  out.reverse();
  return out;
}

/**
 * Greedy shortest-cycle basis. Shorter cycles intersect in fewer edges,
 * which sharpens the witness set -- the reason to prefer this over the
 * fundamental basis (paper, Remark 6.8).
 */
export function minimumCycleBasis(c) {
  const nu = c.cyclomaticNumber();
  if (nu <= 0) return [];
  const byName = new Map(c.reactions.map((r) => [r.name, r]));
  const candidates = [];
  for (const r of c.reactions) {
    const path = shortestPathExcluding(c, r.dst, r.src, r.name);
    if (!path) continue;
    const edges = [[r.name, +1], ...path];
    candidates.push(new Cycle(`cyc_${r.name}`, edges, nodesOf(edges, byName, r.src)));
  }
  candidates.sort((a, b) => a.length - b.length || a.name.localeCompare(b.name));

  // Keep only cycles independent over GF(2), using BigInt bitsets.
  const idx = new Map(c.reactions.map((r, i) => [r.name, i]));
  const basis = [];
  const chosen = [];
  for (const cy of candidates) {
    let vec = 0n;
    for (const [ename] of cy.edges) vec ^= 1n << BigInt(idx.get(ename));
    let red = vec;
    for (const bv of basis) {
      const x = red ^ bv;
      if (x < red) red = x;
    }
    if (red !== 0n) {
      basis.push(red);
      basis.sort((a, b) => (a < b ? 1 : a > b ? -1 : 0));
      chosen.push(cy);
    }
    if (chosen.length === nu) break;
  }
  return chosen;
}

/** Fundamental basis from a spanning forest -- the comparison basis. */
export function fundamentalCycleBasis(c) {
  const adj = adjacency(c);
  const parent = new Map();
  const seen = new Set();
  const treeEdges = new Set();
  for (const root of c.species.keys()) {
    if (seen.has(root)) continue;
    seen.add(root);
    parent.set(root, null);
    const stack = [root];
    while (stack.length) {
      const u = stack.pop();
      for (const [v, ename] of adj.get(u) || []) {
        if (!seen.has(v)) {
          seen.add(v);
          parent.set(v, [u, ename]);
          treeEdges.add(ename);
          stack.push(v);
        }
      }
    }
  }
  const byName = new Map(c.reactions.map((r) => [r.name, r]));
  const cycles = [];
  for (const r of c.reactions) {
    if (treeEdges.has(r.name)) continue;
    const path = treePath(r.dst, r.src, parent, byName);
    if (!path) continue;
    const edges = [[r.name, +1], ...path];
    cycles.push(new Cycle(`cyc_${r.name}`, edges, nodesOf(edges, byName, r.src)));
  }
  return cycles;
}

function treePath(a, b, parent, byName) {
  const ancA = [];
  let node = a;
  const seenA = new Map([[a, 0]]);
  while (parent.get(node)) {
    const [u, ename] = parent.get(node);
    ancA.push([ename, node, u]);
    node = u;
    seenA.set(node, ancA.length);
  }
  const pathB = [];
  node = b;
  while (!seenA.has(node)) {
    const p = parent.get(node);
    if (!p) return null;
    const [u, ename] = p;
    pathB.push([ename, node, u]);
    node = u;
  }
  const meet = node;
  const out = [];
  for (const [ename, child] of ancA.slice(0, seenA.get(meet))) {
    out.push([ename, byName.get(ename).src === child ? +1 : -1]);
  }
  for (let i = pathB.length - 1; i >= 0; i--) {
    const [ename, , par] = pathB[i];
    out.push([ename, byName.get(ename).src === par ? +1 : -1]);
  }
  return out;
}

// ---------------------------------------------------------------------
// Cycle sums and the two floors
// ---------------------------------------------------------------------

export function cycleSum(c, cy) {
  const byName = new Map(c.reactions.map((r) => [r.name, r]));
  let total = 0;
  for (const [ename, sign] of cy.edges) total += sign * c.deltaMu(byName.get(ename));
  return total;
}

export function potentialRange(c, cy) {
  const uniq = new Set(cy.nodes);
  let m = 0;
  for (const n of uniq) m = Math.max(m, Math.abs(c.mu.get(n) ?? 0));
  return m;
}

export function gamma(k, u = MACH_U) {
  const denom = 1 - k * u;
  if (denom <= 0) throw new KernelError("gamma: k*u >= 1, bound unusable");
  return (k * u) / denom;
}

/** eps_num = gamma_{2L} * 2 L Lambda  (Thm 3.2) */
export function numericalFloor(c, cy) {
  const L = cy.length;
  return gamma(2 * L) * 2 * L * potentialRange(c, cy);
}

/**
 * eps_data = z * sqrt(sum sigma_i^2), or null when any sigma is absent.
 * Returning null rather than defaulting is deliberate: a fabricated
 * uncertainty turns an unanswerable question into a confident answer.
 */
export function dataFloor(c, cy, z = Z_ALPHA) {
  let total = 0;
  for (const n of new Set(cy.nodes)) {
    const s = c.species.get(n)?.sigma;
    if (s === null || s === undefined) return null;
    total += s * s;
  }
  return z * Math.sqrt(total);
}

export function computeTolerance(c, cy, z = Z_ALPHA) {
  const numerical = numericalFloor(c, cy);
  const data = dataFloor(c, cy, z);
  return {
    loop: cy.name,
    numerical,
    data,
    star: data === null ? numerical : Math.max(numerical, data),
    dataAvailable: data !== null,
  };
}

export function computeHolonomy(c, cy) {
  return {
    loop: cy.name,
    value: cycleSum(c, cy),
    length: cy.length,
    potentialRange: potentialRange(c, cy),
  };
}

/** The three-valued classification of Definition 5.4. */
export function admit(h, t) {
  const a = Math.abs(h.value);
  let label;
  if (a <= t.numerical) label = CONSISTENT;
  else if (t.data !== null && a <= t.data) label = UNDECIDABLE;
  else if (t.data === null) label = UNDECIDABLE; // no sigma: cannot resolve
  else label = INCONSISTENT;
  return { label, holonomy: h, tolerance: t };
}

/**
 * Edges lying on EVERY flagged cycle. The basis-independent content of
 * a positive result: naming a single loop is not basis-independent.
 */
export function witnessSet(flagged) {
  if (!flagged.length) return new Set();
  let out = new Set(flagged[0].edgeNames());
  for (const cy of flagged.slice(1)) {
    const e = cy.edgeNames();
    out = new Set([...out].filter((x) => e.has(x)));
  }
  return out;
}

/**
 * Inject a genuine defect. It must be on an EDGE: shifting a node
 * potential leaves the edge data the gradient of the shifted potential,
 * so every cycle sum stays exactly zero. Only an edge offset makes the
 * data fail to be a gradient, which is what inconsistency means.
 */
export function perturbEdge(c, reactionName, delta) {
  if (!c.reactions.some((r) => r.name === reactionName)) {
    throw new KernelError(`perturb_edge: unknown reaction '${reactionName}'`);
  }
  const out = c.copy();
  out.edgeOffset.set(reactionName, (out.edgeOffset.get(reactionName) || 0) + delta);
  return out;
}

/** Node perturbation -- provided, but it cannot create inconsistency. */
export function perturbNode(c, speciesName, delta) {
  if (!c.mu.has(speciesName)) {
    throw new KernelError(`perturb: unknown species '${speciesName}'`);
  }
  const out = c.copy();
  out.mu.set(speciesName, out.mu.get(speciesName) + delta);
  return out;
}

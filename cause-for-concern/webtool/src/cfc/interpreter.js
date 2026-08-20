/**
 * cfc/interpreter.js -- executes a parsed program and records everything.
 *
 * The run record drives every chart in the IDE, so nothing plotted is
 * invented: each verdict carries the tolerance that produced it, and the
 * committed-measurement clock advances on every measurement verb.
 *
 * Terminal statuses:
 *   OK       every assertion held
 *   NEGATIVE an assertion failed or declined -- a real scientific result
 *   INVALID  a reference check failed -- no conclusion licensed at all
 *   ERROR    the program could not be run
 */

import { parse } from "./parser.js";
import {
  Circuit, Cycle, KernelError, MACH_U, RT_DEFAULT, Z_ALPHA,
  admit, computeHolonomy, computeTolerance, fundamentalCycleBasis,
  minimumCycleBasis, perturbEdge, perturbNode, witnessSet,
} from "./kernel.js";

class RuntimeHalt extends Error {
  constructor(status, message, line) {
    super(message);
    this.status = status;
    this.line = line;
  }
}
export class CFCRuntimeError extends Error {}

/** Module stand-in: attribute access yields a marker, never fake data. */
class Mod {
  constructor(name) { this.name = name; }
  get(attr) { return `<${this.name}.${attr}>`; }
}

const truthy = (v) => {
  if (v && typeof v === "object" && "label" in v && "holonomy" in v) {
    return v.label !== "INCONSISTENT";
  }
  if (Array.isArray(v)) return v.length > 0;
  if (v instanceof Set) return v.size > 0;
  if (v instanceof Map) return v.size > 0;
  if (typeof v === "string") return v.length > 0;
  return Boolean(v);
};

function jsonable(v) {
  if (v === null || v === undefined) return null;
  const t = typeof v;
  if (t === "string" || t === "boolean") return v;
  if (t === "number") return Number.isFinite(v) ? v : String(v);
  if (v instanceof Cycle) {
    return { loop: v.name, length: v.length, edges: [...v.edgeNames()].sort() };
  }
  if (v instanceof Circuit) {
    return { species: v.species.size, reactions: v.reactions.length };
  }
  if (v instanceof Set) return [...v].map(jsonable);
  if (Array.isArray(v)) return v.map(jsonable);
  if (v instanceof Mod) return `<module ${v.name}>`;
  if (t === "object") {
    const o = {};
    for (const [k, x] of Object.entries(v)) o[k] = jsonable(x);
    return o;
  }
  return String(v);
}

function collectTargets(body) {
  const out = [];
  for (const st of body) {
    if (st.type === "WhereCollect") out.push(st.target);
    else if (st.type === "Foreach") out.push(...collectTargets(st.body));
  }
  return out;
}

export class Interpreter {
  constructor(sourceName = "<program>") {
    this.env = new Map();
    this.clock = 0;
    this.floor = null;
    this.building = null;
    this.rec = {
      source: sourceName,
      status: "OK",
      floor: null,
      committedMeasurements: 0,
      environment: { machU: MACH_U, RT: RT_DEFAULT, zAlpha: Z_ALPHA },
      circuits: {},
      cycles: [],
      tolerances: [],
      verdicts: [],
      assertions: [],
      emissions: [],
      reports: [],
      witnessSet: null,
      error: null,
    };
  }

  tick(n = 1) { this.clock += n; this.rec.committedMeasurements = this.clock; }

  run(prog) {
    try {
      this.execBlock(prog.stmts);
    } catch (e) {
      if (e instanceof RuntimeHalt) {
        this.rec.status = e.status;
        this.rec.error = `line ${e.line}: ${e.message}`;
      } else if (e instanceof CFCRuntimeError || e instanceof KernelError) {
        this.rec.status = "ERROR";
        this.rec.error = e.message;
      } else throw e;
    }
    return this.rec;
  }

  execBlock(stmts) { for (const s of stmts) this.exec(s); }

  exec(s) {
    const m = this[`x_${s.type}`];
    if (!m) throw new CFCRuntimeError(`no evaluator for ${s.type}`);
    m.call(this, s);
  }

  // ---- statements ---------------------------------------------------

  x_FloorDecl(s) {
    const v = this.eval(s.value);
    if (typeof v !== "number" || !(v > 0)) {
      throw new CFCRuntimeError(`line ${s.line}: floor must be a positive number`);
    }
    this.floor = v;
    this.rec.floor = v;
  }

  x_Import(s) {
    const name = s.alias || s.module.split(".")[0];
    this.env.set(name, new Mod(s.module));
  }

  x_Let(s) { this.env.set(s.target, this.eval(s.expr)); }

  x_CircuitDecl(s) {
    let base = null;
    if (s.source) {
      const src = this.eval(s.source);
      if (src instanceof Circuit) base = src.copy();
    }
    const c = base || new Circuit();
    const prev = this.building;
    this.building = c;
    try { this.execBlock(s.body); } finally { this.building = prev; }
    this.env.set(s.name, c);
  }

  needCircuit(line) {
    if (!this.building) {
      throw new CFCRuntimeError(`line ${line}: only valid inside a circuit block`);
    }
    return this.building;
  }

  x_SpeciesDecl(s) {
    this.needCircuit(s.line).addSpecies({
      name: s.name,
      mu0: Number(this.eval(s.mu0)),
      concentration: Number(this.eval(s.concentration)),
      sigma: s.sigma ? Number(this.eval(s.sigma)) : null,
    });
  }

  x_ReactionDecl(s) {
    this.needCircuit(s.line).addReaction({
      name: s.name, src: s.src, dst: s.dst, k: Number(this.eval(s.k)),
    });
  }

  x_Solve(s) {
    const c = this.needCircuit(s.line);
    c.solve();
    this.tick();
    this.env.set(s.target, c);
    const bal = [...c.nodeBalance().values()].map(Math.abs);
    const mus = [...c.mu.values()];
    this.rec.circuits[s.target] = {
      species: c.species.size,
      reactions: c.reactions.length,
      cyclomaticNumber: c.cyclomaticNumber(),
      maxAbsNodeBalance: bal.length ? Math.max(...bal) : 0,
      potentialMin: mus.length ? Math.min(...mus) : null,
      potentialMax: mus.length ? Math.max(...mus) : null,
      centred: c.centred,
      gaugeOffset: c.gaugeOffset,
      nodes: [...c.species.keys()],
      edges: c.reactions.map((r) => ({
        name: r.name, src: r.src, dst: r.dst,
        flux: c.J.get(r.name) ?? 0,
        offset: c.edgeOffset.get(r.name) || 0,
      })),
      mu: Object.fromEntries(c.mu),
    };
  }

  lastCircuit() {
    let found = null;
    for (const v of this.env.values()) if (v instanceof Circuit && v.solved) found = v;
    return found;
  }

  x_HolonomyStmt(s) {
    const loop = this.eval(s.loop);
    const circ = this.eval(s.circuit);
    if (!(loop instanceof Cycle)) throw new CFCRuntimeError(`line ${s.line}: expected a Loop`);
    if (!(circ instanceof Circuit)) throw new CFCRuntimeError(`line ${s.line}: expected a Circuit`);
    const h = computeHolonomy(circ, loop);
    this.tick();
    this.env.set(s.target, h);
    this._lastCircuitForTolerance = circ;
  }

  x_ToleranceStmt(s) {
    const loop = this.eval(s.loop);
    if (!(loop instanceof Cycle)) throw new CFCRuntimeError(`line ${s.line}: expected a Loop`);
    const circ = this._lastCircuitForTolerance || this.lastCircuit();
    if (!circ) throw new CFCRuntimeError(`line ${s.line}: no solved circuit in scope`);
    this.eval(s.sigmaSrc);   // the `with` source is required by the grammar
    const t = computeTolerance(circ, loop);
    this.env.set(s.target, t);
    this.rec.tolerances.push({ ...t, line: s.line });
  }

  x_AdmitStmt(s) {
    const h = this.eval(s.holonomy);
    const t = this.eval(s.tolerance);
    if (!h || typeof h.value !== "number") {
      throw new CFCRuntimeError(`line ${s.line}: admit expects a Holonomy`);
    }
    if (!t || typeof t.star !== "number") {
      throw new CFCRuntimeError(
        `line ${s.line}: admit expects a Tolerance; a numeric literal is not admissible`);
    }
    const v = admit(h, t);
    this.env.set(s.target, v);
    this.rec.verdicts.push({
      verdict: v.label,
      holonomy: { ...v.holonomy, absValue: Math.abs(v.holonomy.value) },
      tolerance: v.tolerance,
      line: s.line,
    });
  }

  x_WitnessStmt(s) {
    const flagged = this.eval(s.flagged);
    if (!Array.isArray(flagged)) throw new CFCRuntimeError(`line ${s.line}: witness expects a list`);
    const w = [...witnessSet(flagged.filter((x) => x instanceof Cycle))].sort();
    this.env.set(s.target, w);
    this.rec.witnessSet = w;
  }

  x_Assert(s) {
    const ok = truthy(this.eval(s.cond));
    this.rec.assertions.push({
      line: s.line, passed: ok, otherwise: s.otherwise,
      message: ok ? s.emitOk : s.emitBad,
    });
    if (ok) {
      if (s.emitOk) this.rec.emissions.push({ line: s.line, message: s.emitOk, kind: "ok" });
      return;
    }
    if (s.emitBad) this.rec.emissions.push({ line: s.line, message: s.emitBad, kind: "bad" });
    if (s.otherwise === "invalid") {
      throw new RuntimeHalt("INVALID", s.emitBad || "reference check failed; experiment invalid", s.line);
    }
    if (s.otherwise === "decline") {
      throw new RuntimeHalt("NEGATIVE", s.emitBad || "assertion declined", s.line);
    }
    throw new RuntimeHalt("NEGATIVE", "assertion failed", s.line);
  }

  x_Emit(s) { this.rec.emissions.push({ line: s.line, message: s.message, kind: "info" }); }

  x_Report(s) {
    this.rec.reports.push({ line: s.line, values: s.items.map((e) => jsonable(this.eval(e))) });
  }

  x_Foreach(s) {
    const it = this.eval(s.iterable);
    if (!Array.isArray(it)) {
      throw new CFCRuntimeError(`line ${s.line}: foreach expects a list`);
    }
    // Pre-declare collect targets: an empty flagged set is a meaningful
    // result (nothing was inconsistent), not an unbound-name error.
    for (const t of collectTargets(s.body)) {
      if (!this.env.has(t)) this.env.set(t, []);
    }
    for (const item of it) {
      this.env.set(s.var, item);
      this.execBlock(s.body);
    }
  }

  x_WhereCollect(s) {
    if (!truthy(this.eval(s.cond))) return;
    if (!this.env.has(s.target)) this.env.set(s.target, []);
    const bucket = this.env.get(s.target);
    if (!Array.isArray(bucket)) {
      throw new CFCRuntimeError(`line ${s.line}: collect target '${s.target}' is not a list`);
    }
    bucket.push(this.eval(s.expr));
  }

  // ---- expressions --------------------------------------------------

  eval(e) {
    const m = this[`e_${e.type}`];
    if (!m) throw new CFCRuntimeError(`no evaluator for expr ${e.type}`);
    return m.call(this, e);
  }

  e_Num(e) { return e.value; }
  e_Str(e) { return e.value; }
  e_TypeLit(e) { return e.name; }
  e_ListLit(e) { return e.items.map((x) => this.eval(x)); }

  e_Name(e) {
    if (this.env.has(e.ident)) return this.env.get(e.ident);
    throw new CFCRuntimeError(`line ${e.line}: unbound name '${e.ident}'`);
  }

  e_Attr(e) {
    const base = this.eval(e.base);
    if (base instanceof Mod) return base.get(e.attr);
    if (base instanceof Cycle) {
      if (e.attr === "length") return base.length;
      if (e.attr === "name" || e.attr === "id") return base.name;
    }
    if (base && typeof base === "object" && e.attr in base) return base[e.attr];
    throw new CFCRuntimeError(`line ${e.line}: no attribute '${e.attr}'`);
  }

  e_UnOp(e) {
    const v = this.eval(e.operand);
    if (e.op === "-") return -v;
    if (e.op === "not") return !truthy(v);
    throw new CFCRuntimeError(`line ${e.line}: bad unary '${e.op}'`);
  }

  e_BinOp(e) {
    if (e.op === "and") return truthy(this.eval(e.lhs)) && truthy(this.eval(e.rhs));
    if (e.op === "or") return truthy(this.eval(e.lhs)) || truthy(this.eval(e.rhs));
    const a = this.eval(e.lhs);
    const b = this.eval(e.rhs);
    const norm = (x) => (x && typeof x === "object" && "label" in x ? x.label : x);
    switch (e.op) {
      case "==": return norm(a) === norm(b);
      case "!=": return norm(a) !== norm(b);
      case "in": {
        if (b instanceof Set) return b.has(a);
        if (Array.isArray(b)) return b.includes(a);
        if (typeof b === "string") return b.includes(String(a));
        return false;
      }
      case "+": return a + b;
      case "-": return a - b;
      case "*": return a * b;
      case "/": return a / b;
      case "<": return a < b;
      case ">": return a > b;
      case "<=": return a <= b;
      case ">=": return a >= b;
      default: throw new CFCRuntimeError(`line ${e.line}: bad operator '${e.op}'`);
    }
  }

  e_Call(e) {
    const args = e.args.map((a) => this.eval(a));
    const fn = BUILTINS[e.fn];
    if (!fn) throw new CFCRuntimeError(`line ${e.line}: unknown function '${e.fn}'`);
    try {
      return fn(this, args);
    } catch (err) {
      if (err instanceof CFCRuntimeError || err instanceof KernelError) throw err;
      throw new CFCRuntimeError(`line ${e.line}: in ${e.fn}(): ${err.message}`);
    }
  }
}

// ---------------------------------------------------------------------
// Builtins
// ---------------------------------------------------------------------

const BUILTINS = {
  centre_potentials: (I, [c]) => {
    if (!(c instanceof Circuit)) throw new CFCRuntimeError("centre_potentials expects a Circuit");
    return c.centrePotentials();
  },
  minimum_cycle_basis: (I, [c]) => {
    if (!(c instanceof Circuit)) throw new CFCRuntimeError("minimum_cycle_basis expects a Circuit");
    const b = minimumCycleBasis(c);
    I.rec.cycles = b.map((cy) => ({
      loop: cy.name, length: cy.length,
      edges: [...cy.edgeNames()].sort(), nodes: cy.nodes,
    }));
    return b;
  },
  fundamental_basis: (I, [c]) => {
    if (!(c instanceof Circuit)) throw new CFCRuntimeError("fundamental_basis expects a Circuit");
    return fundamentalCycleBasis(c);
  },
  perturb_edge: (I, [c, name, d]) => perturbEdge(c, String(name), Number(d)),
  perturb: (I, [c, name, d]) => perturbNode(c, String(name), Number(d)),
  size: (I, [x]) => (x instanceof Set ? x.size : x?.length ?? 0),
  abs: (I, [v]) => Math.abs(v && typeof v === "object" && "value" in v ? v.value : v),
  edge: (I, [x]) => String(x),
  count_where: (I, [items, label]) =>
    (items || []).filter((x) => (x?.label ?? x) === label).length,
};

export function runSource(src, name = "<program>") {
  const I = new Interpreter(name);
  let prog;
  try {
    prog = parse(src);
  } catch (e) {
    I.rec.status = "ERROR";
    I.rec.error = `parse error: ${e.message}`;
    I.rec.errorLine = e.line ?? null;
    return I.rec;
  }
  return I.run(prog);
}

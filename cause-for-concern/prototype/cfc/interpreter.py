"""
cfc.interpreter -- executes a parsed CFC program and records everything.

Design points that are load-bearing rather than incidental:

  * A committed-measurement clock advances on every measurement verb and
    never decreases. Re-measuring is a new measurement, not a cache hit.

  * `admit` is the only way to obtain a Verdict, and it takes a
    Tolerance operand, so no verdict can exist without the tolerance
    that justifies it.

  * `assert ... otherwise invalid` halts with status INVALID, which is
    distinct from a failed assertion (NEGATIVE). An invalid run licenses
    no conclusion about the hypothesis; a negative one does.

  * Everything observed is written to a JSON-serialisable record.
"""

from __future__ import annotations

import json
import math
import platform
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ast_nodes import (
    Assert, AdmitStmt, Attr, BinOp, Call, CircuitDecl, Emit, FloorDecl,
    Foreach, HolonomyStmt, Import, Let, ListLit, Name, Node, Num,
    Program, ReactionDecl, Report, Solve, SpeciesDecl, Str,
    ToleranceStmt, TypeLit, UnOp, WhereCollect, WitnessStmt,
)
from .kernel import (
    Circuit, Cycle, KernelError, Reaction, Species, Tolerance, Verdict,
    admit, compute_holonomy, compute_tolerance, fundamental_cycle_basis,
    minimum_cycle_basis, witness_set, MACH_U, RT_DEFAULT, Z_ALPHA,
)
from .parser import parse


class RuntimeHalt(Exception):
    """Raised to stop evaluation with a terminal status."""
    def __init__(self, status: str, message: str, line: int):
        super().__init__(message)
        self.status, self.message, self.line = status, message, line


class CFCRuntimeError(Exception):
    pass


@dataclass
class Record:
    """The JSON record of one run."""
    source: str = ""
    status: str = "OK"          # OK | NEGATIVE | INVALID | ERROR
    floor: Optional[float] = None
    clock: int = 0
    emissions: List[Dict[str, Any]] = field(default_factory=list)
    reports: List[Dict[str, Any]] = field(default_factory=list)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    verdicts: List[Dict[str, Any]] = field(default_factory=list)
    tolerances: List[Dict[str, Any]] = field(default_factory=list)
    circuits: Dict[str, Any] = field(default_factory=dict)
    witness: Optional[List[str]] = None
    error: Optional[str] = None
    environment: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "source": self.source,
            "status": self.status,
            "floor": self.floor,
            "committed_measurements": self.clock,
            "environment": self.environment,
            "circuits": self.circuits,
            "tolerances": self.tolerances,
            "verdicts": self.verdicts,
            "assertions": self.assertions,
            "emissions": self.emissions,
            "reports": self.reports,
            "witness_set": self.witness,
            "error": self.error,
        }


class Interpreter:
    def __init__(self, source_name: str = "<stdin>"):
        self.env: Dict[str, Any] = {}
        self.rec = Record(source=source_name)
        self.clock = 0
        self.floor: Optional[float] = None
        self._circuit_under_construction: Optional[Circuit] = None
        self.rec.environment = {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "mach_u": MACH_U,
            "RT_kJ_per_mol": RT_DEFAULT,
            "z_alpha": Z_ALPHA,
        }

    # ---------------- clock ------------------------------------------

    def tick(self, n: int = 1) -> int:
        """Advance the committed-measurement clock. Never decreases."""
        self.clock += n
        self.rec.clock = self.clock
        return self.clock

    # ---------------- entry ------------------------------------------

    def run(self, prog: Program) -> Record:
        try:
            self.exec_block(prog.stmts)
        except RuntimeHalt as h:
            self.rec.status = h.status
            self.rec.error = f"line {h.line}: {h.message}"
        except (CFCRuntimeError, KernelError) as e:
            self.rec.status = "ERROR"
            self.rec.error = str(e)
        return self.rec

    def exec_block(self, stmts: List[Node]) -> None:
        for s in stmts:
            self.exec_stmt(s)

    # ---------------- statements -------------------------------------

    def exec_stmt(self, s: Node) -> None:
        m = getattr(self, "x_" + type(s).__name__, None)
        if m is None:
            raise CFCRuntimeError(f"no evaluator for {type(s).__name__}")
        m(s)

    def x_FloorDecl(self, s: FloorDecl) -> None:
        v = self.eval(s.value)
        if not isinstance(v, (int, float)) or v <= 0:
            raise CFCRuntimeError(
                f"line {s.line}: floor must be a positive number, got {v!r}")
        self.floor = float(v)
        self.rec.floor = float(v)

    def x_Import(self, s: Import) -> None:
        name = s.alias or s.module.split(".")[0]
        self.env[name] = _Module(s.module)

    def x_Let(self, s: Let) -> None:
        self.env[s.target] = self.eval(s.expr)

    def x_CircuitDecl(self, s: CircuitDecl) -> None:
        base: Optional[Circuit] = None
        if s.source is not None:
            src = self.eval(s.source)
            if isinstance(src, Circuit):
                base = src.copy()
        c = base if base is not None else Circuit()
        prev, self._circuit_under_construction = \
            self._circuit_under_construction, c
        try:
            self.exec_block(s.body)
        finally:
            self._circuit_under_construction = prev
        self.env[s.name] = c

    def x_SpeciesDecl(self, s: SpeciesDecl) -> None:
        c = self._need_circuit(s.line)
        c.add_species(Species(
            name=s.name,
            mu0=float(self.eval(s.mu0)),
            concentration=float(self.eval(s.concentration)),
            sigma=(float(self.eval(s.sigma)) if s.sigma is not None else None),
        ))

    def x_ReactionDecl(self, s: ReactionDecl) -> None:
        c = self._need_circuit(s.line)
        k = float(self.eval(s.k))
        existing = next((r for r in c.reactions if r.name == s.name), None)
        if existing is not None:
            existing.src, existing.dst, existing.k = s.src, s.dst, k
        else:
            c.add_reaction(Reaction(s.name, s.src, s.dst, k))

    def x_Solve(self, s: Solve) -> None:
        c = self._need_circuit(s.line)
        c.solve()
        self.tick()
        self.env[s.target] = c
        bal = c.node_balance()
        self.rec.circuits[s.target] = {
            "species": len(c.species),
            "reactions": len(c.reactions),
            "cyclomatic_number": c.cyclomatic_number(),
            "max_abs_node_balance": max((abs(v) for v in bal.values()),
                                        default=0.0),
            "potential_min": min(c.mu.values()) if c.mu else None,
            "potential_max": max(c.mu.values()) if c.mu else None,
            "centred": c.centred,
            "gauge_offset": c.gauge_offset,
        }

    def x_HolonomyStmt(self, s: HolonomyStmt) -> None:
        loop = self.eval(s.loop)
        circ = self.eval(s.circuit)
        if not isinstance(loop, Cycle):
            raise CFCRuntimeError(f"line {s.line}: expected a Loop")
        if not isinstance(circ, Circuit):
            raise CFCRuntimeError(f"line {s.line}: expected a Circuit")
        h = compute_holonomy(circ, loop)
        self.tick()
        self.env[s.target] = h

    def x_ToleranceStmt(self, s: ToleranceStmt) -> None:
        loop = self.eval(s.loop)
        if not isinstance(loop, Cycle):
            raise CFCRuntimeError(f"line {s.line}: expected a Loop")
        circ = self._last_circuit()
        if circ is None:
            raise CFCRuntimeError(
                f"line {s.line}: no solved circuit in scope for tolerance")
        # The `with` source is required by the grammar; we evaluate it so
        # that a missing uncertainty table is an error at the right place.
        self.eval(s.sigma_src)
        t = compute_tolerance(circ, loop)
        self.env[s.target] = t
        self.rec.tolerances.append(t.to_json())

    def x_AdmitStmt(self, s: AdmitStmt) -> None:
        h = self.eval(s.holonomy)
        t = self.eval(s.tolerance)
        if not hasattr(h, "value"):
            raise CFCRuntimeError(f"line {s.line}: admit expects a Holonomy")
        if not isinstance(t, Tolerance):
            raise CFCRuntimeError(
                f"line {s.line}: admit expects a Tolerance; a numeric "
                f"literal is not admissible")
        v = admit(h, t)
        self.env[s.target] = v
        self.rec.verdicts.append(v.to_json())

    def x_WitnessStmt(self, s: WitnessStmt) -> None:
        flagged = self.eval(s.flagged)
        if not isinstance(flagged, list):
            raise CFCRuntimeError(f"line {s.line}: witness expects a list")
        cycles = [x for x in flagged if isinstance(x, Cycle)]
        w = sorted(witness_set(cycles))
        self.env[s.target] = w
        self.rec.witness = w

    def x_Assert(self, s: Assert) -> None:
        ok = _truthy(self.eval(s.cond))
        entry = {
            "line": s.line,
            "passed": bool(ok),
            "otherwise": s.otherwise,
            "message": s.emit_ok if ok else s.emit_bad,
        }
        self.rec.assertions.append(entry)
        if ok:
            if s.emit_ok:
                self.rec.emissions.append(
                    {"line": s.line, "message": s.emit_ok})
            return
        if s.emit_bad:
            self.rec.emissions.append({"line": s.line, "message": s.emit_bad})
        if s.otherwise == "invalid":
            raise RuntimeHalt(
                "INVALID",
                s.emit_bad or "reference check failed; experiment invalid",
                s.line)
        if s.otherwise == "decline":
            raise RuntimeHalt(
                "NEGATIVE", s.emit_bad or "assertion declined", s.line)
        raise RuntimeHalt("NEGATIVE", "assertion failed", s.line)

    def x_Emit(self, s: Emit) -> None:
        self.rec.emissions.append({"line": s.line, "message": s.message})

    def x_Report(self, s: Report) -> None:
        vals = [_jsonable(self.eval(e)) for e in s.items]
        self.rec.reports.append({"line": s.line, "values": vals})

    def x_Foreach(self, s: Foreach) -> None:
        it = self.eval(s.iterable)
        if not isinstance(it, (list, tuple)):
            raise CFCRuntimeError(
                f"line {s.line}: foreach expects a list, got {type(it).__name__}")
        # Pre-declare every collect target in the body as an empty list.
        # An empty flagged set is a meaningful result -- it means nothing
        # was inconsistent -- so it must not be an unbound-name error.
        for target in _collect_targets(s.body):
            self.env.setdefault(target, [])
        for item in it:
            self.env[s.var] = item
            self.exec_block(s.body)

    def x_WhereCollect(self, s: WhereCollect) -> None:
        if _truthy(self.eval(s.cond)):
            bucket = self.env.setdefault(s.target, [])
            if not isinstance(bucket, list):
                raise CFCRuntimeError(
                    f"line {s.line}: collect target {s.target!r} is not a list")
            bucket.append(self.eval(s.expr))

    # ---------------- helpers ----------------------------------------

    def _need_circuit(self, line: int) -> Circuit:
        if self._circuit_under_construction is None:
            raise CFCRuntimeError(
                f"line {line}: statement only valid inside a circuit block")
        return self._circuit_under_construction

    def _last_circuit(self) -> Optional[Circuit]:
        for v in reversed(list(self.env.values())):
            if isinstance(v, Circuit) and v.solved:
                return v
        return None

    # ---------------- expressions ------------------------------------

    def eval(self, e: Node) -> Any:
        m = getattr(self, "e_" + type(e).__name__, None)
        if m is None:
            raise CFCRuntimeError(f"no evaluator for expr {type(e).__name__}")
        return m(e)

    def e_Num(self, e: Num) -> float:
        return e.value

    def e_Str(self, e: Str) -> str:
        return e.value

    def e_TypeLit(self, e: TypeLit) -> str:
        return e.name

    def e_ListLit(self, e: ListLit) -> list:
        return [self.eval(x) for x in e.items]

    def e_Name(self, e: Name) -> Any:
        if e.ident in self.env:
            return self.env[e.ident]
        raise CFCRuntimeError(f"line {e.line}: unbound name {e.ident!r}")

    def e_Attr(self, e: Attr) -> Any:
        base = self.eval(e.base)
        if isinstance(base, _Module):
            return base.get(e.attr)
        if isinstance(base, Tolerance):
            return {"numerical": base.numerical, "data": base.data,
                    "star": base.star}.get(e.attr, getattr(base, e.attr, None))
        if isinstance(base, Verdict):
            return getattr(base, e.attr, None)
        if isinstance(base, Cycle):
            if e.attr == "length":
                return base.length
            if e.attr == "name":
                return base.name
        if isinstance(base, dict):
            return base.get(e.attr)
        v = getattr(base, e.attr, None)
        if v is None:
            raise CFCRuntimeError(
                f"line {e.line}: no attribute {e.attr!r}")
        return v

    def e_UnOp(self, e: UnOp) -> Any:
        v = self.eval(e.operand)
        if e.op == "-":
            return -v
        if e.op == "not":
            return not _truthy(v)
        raise CFCRuntimeError(f"line {e.line}: bad unary {e.op!r}")

    def e_BinOp(self, e: BinOp) -> Any:
        if e.op == "and":
            return _truthy(self.eval(e.lhs)) and _truthy(self.eval(e.rhs))
        if e.op == "or":
            return _truthy(self.eval(e.lhs)) or _truthy(self.eval(e.rhs))
        a, b = self.eval(e.lhs), self.eval(e.rhs)
        if e.op == "==":
            return a == b
        if e.op == "!=":
            return a != b
        if e.op == "in":
            return a in b
        try:
            if e.op == "+":
                return a + b
            if e.op == "-":
                return a - b
            if e.op == "*":
                return a * b
            if e.op == "/":
                return a / b
            if e.op == "<":
                return a < b
            if e.op == ">":
                return a > b
            if e.op == "<=":
                return a <= b
            if e.op == ">=":
                return a >= b
        except TypeError as exc:
            raise CFCRuntimeError(f"line {e.line}: {exc}") from exc
        raise CFCRuntimeError(f"line {e.line}: bad operator {e.op!r}")

    def e_Call(self, e: Call) -> Any:
        args = [self.eval(a) for a in e.args]
        fn = _BUILTINS.get(e.fn)
        if fn is None:
            raise CFCRuntimeError(f"line {e.line}: unknown function {e.fn!r}")
        try:
            return fn(self, args)
        except KernelError:
            raise
        except CFCRuntimeError:
            raise
        except Exception as exc:
            raise CFCRuntimeError(f"line {e.line}: in {e.fn}(): {exc}") from exc


# =====================================================================
# Modules and builtins
# =====================================================================

class _Module:
    """A stand-in for an external data source.

    Attribute access returns a symbolic marker rather than fabricating
    data. Programs needing real values must define them in the source,
    which keeps every number that can change a verdict in the text.
    """
    def __init__(self, name: str):
        self.name = name

    def get(self, attr: str) -> Any:
        return f"<{self.name}.{attr}>"

    def __repr__(self) -> str:
        return f"<module {self.name}>"


def _collect_targets(body: List[Node]) -> List[str]:
    """Names appearing as `collect ... into <name>` anywhere in `body`."""
    out: List[str] = []
    for st in body:
        if isinstance(st, WhereCollect):
            out.append(st.target)
        elif isinstance(st, Foreach):
            out.extend(_collect_targets(st.body))
    return out


def _truthy(v: Any) -> bool:
    if isinstance(v, Verdict):
        return v.label != "INCONSISTENT"
    if isinstance(v, (list, tuple, set, dict, str)):
        return len(v) > 0
    return bool(v)


def _jsonable(v: Any) -> Any:
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return str(v)
    if isinstance(v, Verdict):
        return v.to_json()
    if isinstance(v, Tolerance):
        return v.to_json()
    if isinstance(v, Cycle):
        return {"loop": v.name, "length": v.length,
                "edges": sorted(v.edge_names())}
    if hasattr(v, "to_json"):
        return v.to_json()
    if isinstance(v, (list, tuple, set)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, Circuit):
        return {"species": len(v.species), "reactions": len(v.reactions)}
    return repr(v)


def _b_centre(interp: Interpreter, args: List[Any]) -> Circuit:
    c = args[0]
    if not isinstance(c, Circuit):
        raise CFCRuntimeError("centre_potentials expects a Circuit")
    return c.centre_potentials()


def _b_mcb(interp: Interpreter, args: List[Any]) -> List[Cycle]:
    c = args[0]
    if not isinstance(c, Circuit):
        raise CFCRuntimeError("minimum_cycle_basis expects a Circuit")
    return minimum_cycle_basis(c)


def _b_fcb(interp: Interpreter, args: List[Any]) -> List[Cycle]:
    c = args[0]
    if not isinstance(c, Circuit):
        raise CFCRuntimeError("fundamental_basis expects a Circuit")
    return fundamental_cycle_basis(c)


def _clone_solved(c: Circuit) -> Circuit:
    out = c.copy()
    out.mu = dict(c.mu)
    out.G, out.J = dict(c.G), dict(c.J)
    out.solved, out.centred = c.solved, c.centred
    out.gauge_offset = c.gauge_offset
    return out


def _b_perturb_edge(interp: Interpreter, args: List[Any]) -> Circuit:
    """perturb_edge(circuit, "reaction", delta) -- inject a real defect.

    Adds `delta` to one edge's supplied potential difference, so the
    edge data are no longer the gradient of any potential. This is what
    thermodynamic inconsistency IS, and it is the only kind of
    perturbation a cycle-sum test can detect.
    """
    c, name, delta = args[0], args[1], float(args[2])
    if not isinstance(c, Circuit):
        raise CFCRuntimeError("perturb_edge expects a Circuit")
    if not any(r.name == name for r in c.reactions):
        raise CFCRuntimeError(f"perturb_edge: unknown reaction {name!r}")
    out = _clone_solved(c)
    out.edge_offset[name] = out.edge_offset.get(name, 0.0) + delta
    return out


def _b_perturb(interp: Interpreter, args: List[Any]) -> Circuit:
    """perturb(circuit, "species", delta) -- shift one node potential.

    NOTE: this does NOT create a thermodynamic inconsistency. Changing
    a potential leaves the edge data a gradient of the changed
    potential, so every cycle sum remains exactly zero. It is provided
    for studying how the numerical floor moves with potential
    magnitude. To inject a detectable defect use perturb_edge().
    """
    c, name, delta = args[0], args[1], float(args[2])
    if not isinstance(c, Circuit):
        raise CFCRuntimeError("perturb expects a Circuit")
    if name not in c.mu:
        raise CFCRuntimeError(f"perturb: unknown species {name!r}")
    out = _clone_solved(c)
    out.mu[name] += delta
    return out


def _b_size(interp: Interpreter, args: List[Any]) -> int:
    return len(args[0])


def _b_abs(interp: Interpreter, args: List[Any]) -> float:
    v = args[0]
    return abs(v.value) if hasattr(v, "value") else abs(v)


def _b_edge(interp: Interpreter, args: List[Any]) -> str:
    return str(args[0])


def _b_count_where(interp: Interpreter, args: List[Any]) -> int:
    items, label = args[0], args[1]
    return sum(1 for x in items
               if (x.label if isinstance(x, Verdict) else x) == label)


_BUILTINS = {
    "centre_potentials": _b_centre,
    "minimum_cycle_basis": _b_mcb,
    "fundamental_basis": _b_fcb,
    "perturb": _b_perturb,
    "perturb_edge": _b_perturb_edge,
    "size": _b_size,
    "abs": _b_abs,
    "edge": _b_edge,
    "count_where": _b_count_where,
}


# =====================================================================
# Facade
# =====================================================================

def run_source(src: str, name: str = "<string>") -> Record:
    interp = Interpreter(source_name=name)
    try:
        prog = parse(src)
    except Exception as e:
        interp.rec.status = "ERROR"
        interp.rec.error = f"parse error: {e}"
        return interp.rec
    return interp.run(prog)


def run_file(path: str) -> Record:
    with open(path, "r", encoding="utf-8") as f:
        return run_source(f.read(), name=path)


def run_to_json(path: str, out_path: Optional[str] = None) -> dict:
    rec = run_file(path).to_json()
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2, sort_keys=False)
    return rec

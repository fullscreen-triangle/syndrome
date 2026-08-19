"""
cfc.ast_nodes -- abstract syntax for the CFC prototype.

Every node carries `line` so that diagnostics, dropped residues and
tolerance provenance can be attributed to a source position.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# =====================================================================
# Expressions
# =====================================================================

@dataclass
class Node:
    line: int = 0


@dataclass
class Num(Node):
    value: float = 0.0


@dataclass
class Str(Node):
    value: str = ""


@dataclass
class Name(Node):
    ident: str = ""


@dataclass
class Attr(Node):
    """Dotted access: `t.numerical`, `Recon3D.k_PK`."""
    base: Node = None
    attr: str = ""


@dataclass
class Call(Node):
    fn: str = ""
    args: List[Node] = field(default_factory=list)


@dataclass
class BinOp(Node):
    op: str = ""
    lhs: Node = None
    rhs: Node = None


@dataclass
class UnOp(Node):
    op: str = ""
    operand: Node = None


@dataclass
class ListLit(Node):
    items: List[Node] = field(default_factory=list)


@dataclass
class TypeLit(Node):
    """A bare verdict constant such as CONSISTENT."""
    name: str = ""


# =====================================================================
# Statements
# =====================================================================

@dataclass
class FloorDecl(Node):
    value: Node = None


@dataclass
class Import(Node):
    module: str = ""
    alias: Optional[str] = None


@dataclass
class Let(Node):
    target: str = ""
    expr: Node = None


@dataclass
class SpeciesDecl(Node):
    name: str = ""
    mu0: Node = None
    concentration: Node = None
    sigma: Optional[Node] = None


@dataclass
class ReactionDecl(Node):
    name: str = ""
    src: str = ""
    dst: str = ""
    k: Node = None


@dataclass
class Solve(Node):
    target: str = ""


@dataclass
class CircuitDecl(Node):
    name: str = ""
    source: Optional[Node] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class HolonomyStmt(Node):
    """`holonomy of <loop> in <circuit> yield <id>`"""
    loop: Node = None
    circuit: Node = None
    target: str = ""


@dataclass
class ToleranceStmt(Node):
    """`tolerance of <loop> with <sigma-source> yield <id>`

    The `with` clause is REQUIRED by the grammar. A tolerance cannot be
    conjured from a literal; see the admit rule below.
    """
    loop: Node = None
    sigma_src: Optional[Node] = None
    target: str = ""


@dataclass
class AdmitStmt(Node):
    """`admit <holonomy> tolerance <tolerance> yield <id>`

    The single introduction form for Verdict. Both premises are
    mandatory at parse time, so a verdict never exists without the
    tolerance that produced it.
    """
    holonomy: Node = None
    tolerance: Node = None
    target: str = ""


@dataclass
class WitnessStmt(Node):
    flagged: Node = None
    target: str = ""


@dataclass
class Assert(Node):
    cond: Node = None
    emit_ok: Optional[str] = None
    otherwise: Optional[str] = None      # 'decline' | 'invalid' | None
    emit_bad: Optional[str] = None


@dataclass
class Emit(Node):
    message: str = ""


@dataclass
class Report(Node):
    items: List[Node] = field(default_factory=list)


@dataclass
class Foreach(Node):
    var: str = ""
    iterable: Node = None
    body: List[Node] = field(default_factory=list)


@dataclass
class WhereCollect(Node):
    """`where <cond> collect <expr> into <target>`"""
    cond: Node = None
    expr: Node = None
    target: str = ""


@dataclass
class Program(Node):
    stmts: List[Node] = field(default_factory=list)

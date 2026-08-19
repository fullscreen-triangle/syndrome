"""
cfc.kernel -- the numerics behind the language.

Implements, with no dependency beyond the standard library:

  * circuit construction   mu = mu0 + RT ln c,  G = k c / RT,  J = G dmu
  * gauge centring         (Prop. "potential offsets are a gauge freedom")
  * cycle bases            fundamental (spanning tree) and a shortest-
                           cycle greedy basis
  * cycle sums             the quantity that is identically zero
  * numerical floor        eps_num = gamma_{2L} * 2 L Lambda
  * data floor             eps_data = z * sqrt(sum sigma_i^2)
  * the three-valued verdict and the witness set

The two floors are kept apart everywhere, because collapsing them is
exactly the error the companion paper is about.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

# Unit roundoff for IEEE-754 binary64.
MACH_U = 2.0 ** -53

# Gas constant times body temperature, kJ/mol at T = 310 K.
RT_DEFAULT = 2.577

# Normal quantile for a two-sided interval at alpha = 0.01.
Z_ALPHA = 2.5758293035489004


class KernelError(Exception):
    pass


# =====================================================================
# Circuit
# =====================================================================

@dataclass
class Species:
    name: str
    mu0: float
    concentration: float
    sigma: Optional[float] = None       # uncertainty on mu, kJ/mol


@dataclass
class Reaction:
    name: str
    src: str
    dst: str
    k: float


@dataclass
class Circuit:
    species: Dict[str, Species] = field(default_factory=dict)
    reactions: List[Reaction] = field(default_factory=list)
    RT: float = RT_DEFAULT

    # populated by solve()
    mu: Dict[str, float] = field(default_factory=dict)
    G: Dict[str, float] = field(default_factory=dict)
    J: Dict[str, float] = field(default_factory=dict)
    solved: bool = False
    centred: bool = False
    gauge_offset: float = 0.0

    # Per-edge offsets applied to the potential difference of a
    # reaction, i.e. d_e = (mu_dst - mu_src) + offset_e.
    #
    # An offset makes the edge data fail to be a gradient, which IS
    # what thermodynamic inconsistency means. Perturbing a NODE
    # potential cannot do this: any change to mu leaves the data a
    # gradient of the changed mu, so every cycle sum stays exactly
    # zero. The defect has to live on an edge.
    edge_offset: Dict[str, float] = field(default_factory=dict)

    # ---- construction ------------------------------------------------

    def add_species(self, s: Species) -> None:
        if s.concentration <= 0:
            raise KernelError(
                f"species {s.name}: concentration must be > 0")
        self.species[s.name] = s

    def add_reaction(self, r: Reaction) -> None:
        for end in (r.src, r.dst):
            if end not in self.species:
                raise KernelError(
                    f"reaction {r.name}: unknown species {end!r}")
        if r.k <= 0:
            raise KernelError(f"reaction {r.name}: k must be > 0")
        self.reactions.append(r)

    # ---- solving -----------------------------------------------------

    def solve(self) -> "Circuit":
        """Compute mu, G, J.  Pure evaluation; no iteration required."""
        self.mu = {
            name: s.mu0 + self.RT * math.log(s.concentration)
            for name, s in self.species.items()
        }
        self.G, self.J = {}, {}
        for r in self.reactions:
            g = r.k * self.species[r.src].concentration / self.RT
            self.G[r.name] = g
            self.J[r.name] = g * (self.mu[r.src] - self.mu[r.dst])
        self.solved = True
        return self

    def copy(self) -> "Circuit":
        c = Circuit(
            species={k: Species(v.name, v.mu0, v.concentration, v.sigma)
                     for k, v in self.species.items()},
            reactions=[Reaction(r.name, r.src, r.dst, r.k)
                       for r in self.reactions],
            RT=self.RT,
            edge_offset=dict(self.edge_offset),
        )
        return c

    def delta_mu(self, r: Reaction) -> float:
        """Edge data d_e as supplied: gradient part plus any offset."""
        return (self.mu[r.dst] - self.mu[r.src]) + self.edge_offset.get(
            r.name, 0.0)

    # ---- gauge -------------------------------------------------------

    def centre_potentials(self) -> "Circuit":
        """Shift all potentials so max|mu| is minimised.

        Changes no cycle sum mathematically; reduces the numerical floor
        because rounding error scales with operand magnitude.
        """
        if not self.solved:
            self.solve()
        out = self.copy()
        out.mu = dict(self.mu)
        out.G, out.J = dict(self.G), dict(self.J)
        out.solved = True
        if out.mu:
            lo, hi = min(out.mu.values()), max(out.mu.values())
            offset = -0.5 * (lo + hi)
            out.mu = {k: v + offset for k, v in out.mu.items()}
            out.gauge_offset = offset
        out.centred = True
        return out

    # ---- topology ----------------------------------------------------

    def node_balance(self) -> Dict[str, float]:
        """Signed flux sum at each species (Kirchhoff current law)."""
        bal = {name: 0.0 for name in self.species}
        for r in self.reactions:
            bal[r.src] -= self.J[r.name]
            bal[r.dst] += self.J[r.name]
        return bal

    def cyclomatic_number(self) -> int:
        n = len(self.species)
        m = len(self.reactions)
        comps = _count_components(self.species.keys(), self.reactions)
        return m - n + comps


def _count_components(nodes, reactions) -> int:
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in reactions:
        a, b = find(r.src), find(r.dst)
        if a != b:
            parent[a] = b
    return len({find(n) for n in nodes})


# =====================================================================
# Cycles
# =====================================================================

@dataclass
class Cycle:
    """A cycle as a signed list of (reaction_name, orientation)."""
    name: str
    edges: List[Tuple[str, int]]        # (+1 forward, -1 reversed)
    nodes: List[str]

    @property
    def length(self) -> int:
        return len(self.edges)

    def edge_names(self) -> Set[str]:
        return {e for e, _ in self.edges}


def fundamental_cycle_basis(c: Circuit) -> List[Cycle]:
    """Cycles from the fundamental system of a spanning forest."""
    adj: Dict[str, List[Tuple[str, str]]] = {n: [] for n in c.species}
    for r in c.reactions:
        adj[r.src].append((r.dst, r.name))
        adj[r.dst].append((r.src, r.name))

    parent: Dict[str, Optional[Tuple[str, str]]] = {}
    seen: Set[str] = set()
    tree_edges: Set[str] = set()

    for root in c.species:
        if root in seen:
            continue
        seen.add(root)
        parent[root] = None
        stack = [root]
        while stack:
            u = stack.pop()
            for v, ename in adj[u]:
                if v not in seen:
                    seen.add(v)
                    parent[v] = (u, ename)
                    tree_edges.add(ename)
                    stack.append(v)

    by_name = {r.name: r for r in c.reactions}
    cycles: List[Cycle] = []
    for r in c.reactions:
        if r.name in tree_edges:
            continue
        path = _tree_path(r.dst, r.src, parent, by_name)
        if path is None:
            continue
        edges = [(r.name, +1)] + path
        nodes = _nodes_of(edges, by_name, start=r.src)
        cycles.append(Cycle(name=f"cyc_{r.name}", edges=edges, nodes=nodes))
    return cycles


def _tree_path(a: str, b: str, parent, by_name) -> Optional[List[Tuple[str, int]]]:
    """Signed edge path from a to b through the spanning forest."""
    anc_a, node = [], a
    seen_a = {a: 0}
    while parent.get(node):
        u, ename = parent[node]
        anc_a.append((ename, node, u))
        node = u
        seen_a[node] = len(anc_a)

    path_b, node = [], b
    while node not in seen_a:
        p = parent.get(node)
        if p is None:
            return None
        u, ename = p
        path_b.append((ename, node, u))
        node = u
    meet = node

    out: List[Tuple[str, int]] = []
    for ename, child, par in anc_a[:seen_a[meet]]:
        r = by_name[ename]
        out.append((ename, +1 if r.src == child else -1))
    for ename, child, par in reversed(path_b):
        r = by_name[ename]
        out.append((ename, +1 if r.src == par else -1))
    return out


def _nodes_of(edges, by_name, start: str) -> List[str]:
    nodes, cur = [start], start
    for ename, sign in edges:
        r = by_name[ename]
        nxt = r.dst if (r.src == cur) else r.src
        nodes.append(nxt)
        cur = nxt
    return nodes


def minimum_cycle_basis(c: Circuit) -> List[Cycle]:
    """Greedy shortest-cycle basis.

    For each non-tree edge, take the shortest cycle through it (BFS in
    the graph minus that edge). Shorter cycles intersect in fewer edges,
    which sharpens the witness set; that is the reason to prefer this
    over the fundamental basis.
    """
    by_name = {r.name: r for r in c.reactions}
    nu = c.cyclomatic_number()
    if nu <= 0:
        return []

    candidates: List[Cycle] = []
    for r in c.reactions:
        path = _shortest_path_excluding(c, r.dst, r.src, exclude=r.name)
        if path is None:
            continue
        edges = [(r.name, +1)] + path
        nodes = _nodes_of(edges, by_name, start=r.src)
        candidates.append(Cycle(name=f"cyc_{r.name}", edges=edges, nodes=nodes))

    candidates.sort(key=lambda cy: (cy.length, cy.name))

    # Greedily keep cycles independent over GF(2).
    ordered = [r.name for r in c.reactions]
    idx = {e: i for i, e in enumerate(ordered)}
    basis_vecs: List[int] = []
    chosen: List[Cycle] = []
    for cy in candidates:
        vec = 0
        for ename, _ in cy.edges:
            vec ^= 1 << idx[ename]
        reduced = vec
        for bv in basis_vecs:
            reduced = min(reduced, reduced ^ bv)
        if reduced:
            basis_vecs.append(reduced)
            basis_vecs.sort(reverse=True)
            chosen.append(cy)
        if len(chosen) == nu:
            break
    return chosen


def _shortest_path_excluding(c: Circuit, a: str, b: str,
                             exclude: str) -> Optional[List[Tuple[str, int]]]:
    from collections import deque
    adj: Dict[str, List[Tuple[str, str]]] = {n: [] for n in c.species}
    for r in c.reactions:
        if r.name == exclude:
            continue
        adj[r.src].append((r.dst, r.name))
        adj[r.dst].append((r.src, r.name))

    prev: Dict[str, Optional[Tuple[str, str]]] = {a: None}
    q = deque([a])
    while q:
        u = q.popleft()
        if u == b:
            break
        for v, ename in adj[u]:
            if v not in prev:
                prev[v] = (u, ename)
                q.append(v)
    if b not in prev:
        return None

    by_name = {r.name: r for r in c.reactions}
    out: List[Tuple[str, int]] = []
    node = b
    while prev[node] is not None:
        u, ename = prev[node]
        r = by_name[ename]
        out.append((ename, +1 if r.src == u else -1))
        node = u
    out.reverse()
    return out


# =====================================================================
# Cycle sums and the two floors
# =====================================================================

def cycle_sum(c: Circuit, cy: Cycle) -> float:
    """Sum of edge data around `cy`.

    If the edge data are a gradient -- i.e. every edge offset is zero --
    this telescopes to exactly zero for any potentials, so what is
    returned is pure accumulated rounding error. A nonzero edge offset
    breaks the gradient property, and its net signed traversal count
    around the cycle is what survives.
    """
    by_name = {r.name: r for r in c.reactions}
    total = 0.0
    for ename, sign in cy.edges:
        total += sign * c.delta_mu(by_name[ename])
    return total


def potential_range(c: Circuit, cy: Cycle) -> float:
    """Lambda: the largest absolute potential on the cycle."""
    return max(abs(c.mu[n]) for n in set(cy.nodes)) if cy.nodes else 0.0


def gamma(k: int, u: float = MACH_U) -> float:
    denom = 1.0 - k * u
    if denom <= 0:
        raise KernelError("gamma: k*u >= 1, error bound unusable")
    return (k * u) / denom


def numerical_floor(c: Circuit, cy: Cycle) -> float:
    """eps_num = gamma_{2L} * 2 L Lambda."""
    L = cy.length
    lam = potential_range(c, cy)
    return gamma(2 * L) * 2.0 * L * lam


def data_floor(c: Circuit, cy: Cycle,
               z: float = Z_ALPHA) -> Optional[float]:
    """eps_data = z * sqrt(sum_i sigma_i^2), or None if any sigma absent.

    Returning None rather than substituting a default is deliberate: a
    fabricated uncertainty converts an unanswerable question into a
    confident answer.
    """
    total = 0.0
    for name in set(cy.nodes):
        s = c.species[name].sigma
        if s is None:
            return None
        total += s * s
    return z * math.sqrt(total)


# =====================================================================
# Verdict
# =====================================================================

CONSISTENT = "CONSISTENT"
UNDECIDABLE = "UNDECIDABLE"
INCONSISTENT = "INCONSISTENT"


@dataclass
class Tolerance:
    numerical: float
    data: Optional[float]
    star: float
    loop: str

    def to_json(self) -> dict:
        return {
            "loop": self.loop,
            "numerical": self.numerical,
            "data": self.data,
            "star": self.star,
            "data_available": self.data is not None,
        }


@dataclass
class Holonomy:
    value: float
    loop: str
    length: int
    potential_range: float

    def to_json(self) -> dict:
        return {
            "loop": self.loop,
            "value": self.value,
            "abs_value": abs(self.value),
            "length": self.length,
            "potential_range": self.potential_range,
        }


@dataclass
class Verdict:
    """A verdict ALWAYS carries the tolerance that produced it."""
    label: str
    holonomy: Holonomy
    tolerance: Tolerance

    def to_json(self) -> dict:
        return {
            "verdict": self.label,
            "holonomy": self.holonomy.to_json(),
            "tolerance": self.tolerance.to_json(),
        }

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.label == other
        if isinstance(other, Verdict):
            return self.label == other.label
        return NotImplemented

    def __hash__(self):
        return hash(self.label)


def compute_tolerance(c: Circuit, cy: Cycle,
                      z: float = Z_ALPHA) -> Tolerance:
    en = numerical_floor(c, cy)
    ed = data_floor(c, cy, z=z)
    star = en if ed is None else max(en, ed)
    return Tolerance(numerical=en, data=ed, star=star, loop=cy.name)


def compute_holonomy(c: Circuit, cy: Cycle) -> Holonomy:
    return Holonomy(value=cycle_sum(c, cy), loop=cy.name,
                    length=cy.length, potential_range=potential_range(c, cy))


def admit(h: Holonomy, t: Tolerance) -> Verdict:
    """The three-valued classification.

    Below the numerical floor          -> CONSISTENT
    Between numerical and data floor   -> UNDECIDABLE
    Above both                         -> INCONSISTENT
    """
    a = abs(h.value)
    if a <= t.numerical:
        label = CONSISTENT
    elif t.data is not None and a <= t.data:
        label = UNDECIDABLE
    elif t.data is None and a > t.numerical:
        # No uncertainty data: cannot distinguish real defect from
        # unquantified data error.  Honest answer is UNDECIDABLE.
        label = UNDECIDABLE
    else:
        label = INCONSISTENT
    return Verdict(label=label, holonomy=h, tolerance=t)


def witness_set(flagged: Sequence[Cycle]) -> Set[str]:
    """Edges lying on EVERY flagged cycle.

    The basis-independent content of a positive result: the defect is in
    here. Naming a single loop is not basis-independent.
    """
    if not flagged:
        return set()
    out = set(flagged[0].edge_names())
    for cy in flagged[1:]:
        out &= cy.edge_names()
    return out

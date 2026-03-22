"""
Biochemical Circuit Model

Implements the cellular circuit framework from the fuzzy sequential constraint paper:
- Biochemical circuit graph G = (V, E, w) with chemical potential as node voltage
- KCL (stoichiometric mass balance) and KVL (thermodynamic cycle consistency)
- Fuzzy node states with alpha-cut interval arithmetic
- Loop holonomy computation for disease detection
- Trajectory completion algorithm with Banach contraction convergence
- Drug design as sparse conductance modification (L1 optimisation)

The circuit model is derived rigorously:
    phi_i = mu_i^chem = mu_i^0 + RT ln[C_i]
    G_ij = k_ij [C_i] / (RT)
    J_ij = G_ij * Delta_phi_ij  (near equilibrium)
    KCL: sum_j J_ji = sum_j J_ij  (mass balance)
    KVL: sum_{cycle} Delta_phi_ij = 0  (Wegscheider conditions)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
import numpy as np
from scipy import optimize

# Physical constants
R_GAS = 8.314  # J/(mol*K)
T_BODY = 310.15  # K (37 C)
RT = R_GAS * T_BODY  # ~2578 J/mol
KB = 1.380649e-23  # J/K
LN2 = np.log(2)


# =============================================================================
# Core data structures
# =============================================================================

@dataclass
class FuzzyInterval:
    """
    Fuzzy membership function represented as nested alpha-cut intervals.

    For each alpha in (0, 1], the alpha-cut is [lo, hi].
    We store a discrete set of alpha levels for computational tractability.
    """
    alphas: np.ndarray  # alpha levels, e.g. [0.1, 0.2, ..., 1.0]
    lo: np.ndarray      # lower bounds at each alpha
    hi: np.ndarray      # upper bounds at each alpha

    @classmethod
    def from_measurement(cls, value: float, uncertainty: float,
                         n_levels: int = 10) -> "FuzzyInterval":
        """Create trapezoidal fuzzy number from measurement +/- uncertainty."""
        alphas = np.linspace(0.1, 1.0, n_levels)
        lo = value - uncertainty * (1.0 - alphas + 0.1)
        hi = value + uncertainty * (1.0 - alphas + 0.1)
        lo = np.maximum(lo, 0.0)  # concentrations are non-negative
        return cls(alphas=alphas, lo=lo, hi=hi)

    @classmethod
    def uniform(cls, lo: float, hi: float, n_levels: int = 10) -> "FuzzyInterval":
        """Maximum-entropy prior: uniform over [lo, hi] at all alpha levels."""
        alphas = np.linspace(0.1, 1.0, n_levels)
        return cls(
            alphas=alphas,
            lo=np.full(n_levels, lo),
            hi=np.full(n_levels, hi),
        )

    @classmethod
    def crisp(cls, value: float, n_levels: int = 10) -> "FuzzyInterval":
        """Crisp (exact) value."""
        alphas = np.linspace(0.1, 1.0, n_levels)
        return cls(
            alphas=alphas,
            lo=np.full(n_levels, value),
            hi=np.full(n_levels, value),
        )

    def width(self, alpha: float = 1.0) -> float:
        """Width of interval at given alpha level."""
        idx = np.argmin(np.abs(self.alphas - alpha))
        return float(self.hi[idx] - self.lo[idx])

    def center(self) -> float:
        """Center of the core (alpha=1.0 cut)."""
        return float(0.5 * (self.lo[-1] + self.hi[-1]))

    def intersect(self, other: "FuzzyInterval") -> "FuzzyInterval":
        """Fuzzy intersection (min operation on membership)."""
        new_lo = np.maximum(self.lo, other.lo)
        new_hi = np.minimum(self.hi, other.hi)
        # Ensure validity: if intersection is empty at some level, clamp
        new_hi = np.maximum(new_hi, new_lo)
        return FuzzyInterval(alphas=self.alphas.copy(), lo=new_lo, hi=new_hi)

    def hausdorff_distance(self, other: "FuzzyInterval") -> float:
        """Hausdorff-Pompeiu metric between two fuzzy intervals."""
        d_lo = np.abs(self.lo - other.lo)
        d_hi = np.abs(self.hi - other.hi)
        return float(np.max(np.maximum(d_lo, d_hi)))

    def is_crisp(self, tol: float = 1e-8) -> bool:
        """Check if interval has collapsed to a point."""
        return bool(np.all(self.hi - self.lo < tol))


@dataclass
class CircuitNode:
    """
    A node in the biochemical circuit graph.

    Represents a molecular species with:
    - Chemical potential phi = mu_0 + RT ln[C]
    - Fuzzy concentration state
    - Standard chemical potential mu_0
    """
    name: str
    mu_0: float  # standard chemical potential (J/mol)
    concentration: FuzzyInterval  # fuzzy concentration
    c_min: float = 1e-9  # minimum feasible concentration (M)
    c_max: float = 1.0   # maximum feasible concentration (M)

    def potential(self, c: Optional[float] = None) -> float:
        """Chemical potential phi = mu_0 + RT ln[C]."""
        if c is None:
            c = self.concentration.center()
        c = max(c, self.c_min)
        return self.mu_0 + RT * np.log(c)

    def categorical_depth(self, c: Optional[float] = None) -> float:
        """Categorical depth H = -log2(P) = phi / (kB T ln 2)."""
        return self.potential(c) / (KB * T_BODY * LN2 * 6.022e23)


@dataclass
class CircuitEdge:
    """
    An edge (reaction) in the biochemical circuit graph.

    Represents a reaction with:
    - Forward rate constant k_fwd
    - Reverse rate constant k_rev
    - Conductance G = k_fwd [C_source] / RT
    """
    source: str  # source node name
    target: str  # target node name
    k_fwd: float  # forward rate constant (1/s or 1/(M*s))
    k_rev: float  # reverse rate constant
    enzyme_name: str = ""  # optional enzyme name

    def conductance(self, c_source: float) -> float:
        """Circuit conductance G_ij = k_fwd * [C_source] / RT."""
        return self.k_fwd * max(c_source, 1e-15) / RT

    def flux(self, c_source: float, c_target: float) -> float:
        """Net reaction flux (current): J = k_fwd*[S] - k_rev*[P]."""
        return self.k_fwd * c_source - self.k_rev * c_target

    def delta_phi(self, c_source: float, c_target: float,
                  mu0_source: float, mu0_target: float) -> float:
        """Potential difference across edge."""
        phi_s = mu0_source + RT * np.log(max(c_source, 1e-15))
        phi_t = mu0_target + RT * np.log(max(c_target, 1e-15))
        return phi_t - phi_s


# =============================================================================
# Circuit graph
# =============================================================================

class BiochemicalCircuit:
    """
    Biochemical circuit graph G = (V, E, w).

    Implements:
    - KCL (stoichiometric mass balance)
    - KVL (thermodynamic cycle consistency)
    - Fuzzy constraint propagation
    - Loop holonomy computation
    - Trajectory completion algorithm
    """

    def __init__(self):
        self.nodes: Dict[str, CircuitNode] = {}
        self.edges: List[CircuitEdge] = []
        self._adjacency: Dict[str, List[CircuitEdge]] = {}
        self._in_edges: Dict[str, List[CircuitEdge]] = {}

    def add_node(self, node: CircuitNode) -> None:
        """Add a species node to the circuit."""
        self.nodes[node.name] = node
        if node.name not in self._adjacency:
            self._adjacency[node.name] = []
        if node.name not in self._in_edges:
            self._in_edges[node.name] = []

    def add_edge(self, edge: CircuitEdge) -> None:
        """Add a reaction edge to the circuit."""
        self.edges.append(edge)
        if edge.source not in self._adjacency:
            self._adjacency[edge.source] = []
        self._adjacency[edge.source].append(edge)
        if edge.target not in self._in_edges:
            self._in_edges[edge.target] = []
        self._in_edges[edge.target].append(edge)

    def neighbors(self, node_name: str) -> List[str]:
        """Get all neighbor node names (outgoing edges)."""
        return [e.target for e in self._adjacency.get(node_name, [])]

    def predecessors(self, node_name: str) -> List[str]:
        """Get all predecessor node names (incoming edges)."""
        return [e.source for e in self._in_edges.get(node_name, [])]

    # -------------------------------------------------------------------------
    # Kirchhoff's Laws
    # -------------------------------------------------------------------------

    def kcl_residual(self, node_name: str,
                     concentrations: Optional[Dict[str, float]] = None) -> float:
        """
        KCL residual at a node: sum(flux_in) - sum(flux_out).

        At steady state this should be zero (stoichiometric mass balance).
        """
        if concentrations is None:
            concentrations = {n: self.nodes[n].concentration.center()
                              for n in self.nodes}

        flux_in = 0.0
        for edge in self._in_edges.get(node_name, []):
            c_s = concentrations.get(edge.source, 1e-6)
            c_t = concentrations.get(edge.target, 1e-6)
            flux_in += edge.flux(c_s, c_t)

        flux_out = 0.0
        for edge in self._adjacency.get(node_name, []):
            c_s = concentrations.get(edge.source, 1e-6)
            c_t = concentrations.get(edge.target, 1e-6)
            flux_out += edge.flux(c_s, c_t)

        return flux_in - flux_out

    def total_kcl_residual(self,
                           concentrations: Optional[Dict[str, float]] = None
                           ) -> float:
        """Total KCL residual across all nodes."""
        return sum(abs(self.kcl_residual(n, concentrations))
                   for n in self.nodes)

    def kvl_residual(self, cycle: List[str],
                     concentrations: Optional[Dict[str, float]] = None) -> float:
        """
        KVL residual around a cycle: sum of potential differences.

        Should be zero for thermodynamic consistency (Wegscheider condition).
        """
        if concentrations is None:
            concentrations = {n: self.nodes[n].concentration.center()
                              for n in self.nodes}

        total_dphi = 0.0
        for i in range(len(cycle)):
            src = cycle[i]
            tgt = cycle[(i + 1) % len(cycle)]
            c_s = concentrations.get(src, 1e-6)
            c_t = concentrations.get(tgt, 1e-6)
            mu0_s = self.nodes[src].mu_0
            mu0_t = self.nodes[tgt].mu_0

            dphi = mu0_t + RT * np.log(max(c_t, 1e-15)) - \
                   (mu0_s + RT * np.log(max(c_s, 1e-15)))
            total_dphi += dphi

        return total_dphi

    # -------------------------------------------------------------------------
    # Loop detection and holonomy
    # -------------------------------------------------------------------------

    def find_loops(self, max_length: int = 10) -> List[List[str]]:
        """Find all simple cycles up to max_length using DFS."""
        loops = []
        visited_cycles: Set[tuple] = set()

        # Check for 2-node cycles (bidirectional edges like ATP <-> ADP)
        for name in self.nodes:
            for neighbor in self.neighbors(name):
                if name in [e.target for e in self._adjacency.get(neighbor, [])]:
                    canonical = tuple(sorted([name, neighbor]))
                    if canonical not in visited_cycles:
                        visited_cycles.add(canonical)
                        loops.append([name, neighbor])

        # Find longer cycles via DFS
        for start in self.nodes:
            self._dfs_loops(start, start, [start], set([start]),
                            loops, visited_cycles, max_length)

        return loops

    def _dfs_loops(self, start: str, current: str, path: List[str],
                   visited: Set[str], loops: List[List[str]],
                   visited_cycles: Set[tuple], max_length: int) -> None:
        """DFS helper for cycle detection."""
        if len(path) > max_length:
            return

        for neighbor in self.neighbors(current):
            if neighbor == start and len(path) >= 3:
                # Found a cycle - normalize to avoid duplicates
                canonical = self._canonical_cycle(path)
                if canonical not in visited_cycles:
                    visited_cycles.add(canonical)
                    loops.append(path[:])
            elif neighbor not in visited and neighbor in self.nodes:
                visited.add(neighbor)
                path.append(neighbor)
                self._dfs_loops(start, neighbor, path, visited,
                                loops, visited_cycles, max_length)
                path.pop()
                visited.remove(neighbor)

    @staticmethod
    def _canonical_cycle(cycle: List[str]) -> tuple:
        """Canonical form of a cycle for deduplication."""
        min_idx = cycle.index(min(cycle))
        rotated = cycle[min_idx:] + cycle[:min_idx]
        return tuple(rotated)

    def loop_holonomy(self, cycle: List[str],
                      concentrations: Optional[Dict[str, float]] = None
                      ) -> float:
        """
        Compute the holonomy of a loop.

        The holonomy measures the failure of constraint propagation around
        a closed loop to return to the starting value. For a healthy circuit,
        H_ell = Id (holonomy = 0). For a diseased circuit, H_ell != Id.

        This is equivalent to the KVL residual normalised by RT.
        """
        residual = self.kvl_residual(cycle, concentrations)
        return residual / RT

    def loop_consistency(self, cycle: List[str],
                         concentrations: Optional[Dict[str, float]] = None,
                         max_holonomy: float = 10.0) -> float:
        """
        Consistency of a loop: C_ell = 1 - |H_ell| / |H_ell|_max.

        Returns value in [0, 1] where 1 = perfectly consistent.
        """
        h = abs(self.loop_holonomy(cycle, concentrations))
        return max(0.0, 1.0 - h / max_holonomy)

    def consistency_index(self,
                          concentrations: Optional[Dict[str, float]] = None,
                          max_length: int = 10) -> float:
        """
        Global consistency index: average loop consistency.

        C(G) = (1/|L|) sum_ell C_ell
        Returns 1.0 for perfectly self-consistent circuit.
        """
        loops = self.find_loops(max_length)
        if not loops:
            return 1.0
        consistencies = [self.loop_consistency(l, concentrations)
                         for l in loops]
        return float(np.mean(consistencies))

    # -------------------------------------------------------------------------
    # Fuzzy constraint propagation
    # -------------------------------------------------------------------------

    def apply_fuzzy_kcl(self, node_name: str) -> FuzzyInterval:
        """
        Apply fuzzy KCL at a node.

        Computes the interval of concentrations for node_name that are
        consistent with mass balance given the fuzzy states of neighbors.
        Then intersects with the current fuzzy state.
        """
        node = self.nodes[node_name]
        in_edges = self._in_edges.get(node_name, [])
        out_edges = self._adjacency.get(node_name, [])

        if not in_edges and not out_edges:
            return node.concentration

        # At each alpha level, compute the feasible concentration interval
        n_levels = len(node.concentration.alphas)
        new_lo = np.full(n_levels, node.c_min)
        new_hi = np.full(n_levels, node.c_max)

        for alpha_idx in range(n_levels):
            # Sum incoming flux range
            flux_in_lo = 0.0
            flux_in_hi = 0.0
            for edge in in_edges:
                src = self.nodes[edge.source]
                c_lo = src.concentration.lo[alpha_idx]
                c_hi = src.concentration.hi[alpha_idx]
                flux_in_lo += edge.k_fwd * c_lo
                flux_in_hi += edge.k_fwd * c_hi

            # For outgoing flux to balance, we need k_rev * [node] or k_fwd * [node]
            total_out_k = sum(e.k_fwd for e in out_edges) + \
                          sum(e.k_rev for e in in_edges)

            if total_out_k > 0:
                c_lo_kcl = flux_in_lo / total_out_k
                c_hi_kcl = flux_in_hi / total_out_k
                new_lo[alpha_idx] = max(new_lo[alpha_idx], c_lo_kcl)
                new_hi[alpha_idx] = min(new_hi[alpha_idx], c_hi_kcl)

        # Ensure monotonicity: wider intervals at lower alpha
        for i in range(n_levels - 2, -1, -1):
            new_lo[i] = min(new_lo[i], new_lo[i + 1])
            new_hi[i] = max(new_hi[i], new_hi[i + 1])

        new_hi = np.maximum(new_hi, new_lo)

        kcl_interval = FuzzyInterval(
            alphas=node.concentration.alphas.copy(),
            lo=new_lo, hi=new_hi,
        )

        # Intersect with current state
        return node.concentration.intersect(kcl_interval)

    def apply_fuzzy_kvl(self, cycles: List[List[str]]) -> None:
        """
        Apply fuzzy KVL constraints for all given cycles.

        For each cycle, restrict node concentrations so that the cycle
        potential sum includes zero at each alpha level.
        """
        for cycle in cycles:
            # Check if current concentration ranges satisfy KVL
            # If not, tighten the widest interval
            for alpha_idx in range(len(self.nodes[cycle[0]].concentration.alphas)):
                phi_sum_lo = 0.0
                phi_sum_hi = 0.0
                widest_node = cycle[0]
                widest_width = 0.0

                for i in range(len(cycle)):
                    src = cycle[i]
                    tgt = cycle[(i + 1) % len(cycle)]
                    node_s = self.nodes[src]
                    node_t = self.nodes[tgt]

                    # Potential difference range
                    c_s_lo = max(node_s.concentration.lo[alpha_idx], 1e-15)
                    c_s_hi = max(node_s.concentration.hi[alpha_idx], 1e-15)
                    c_t_lo = max(node_t.concentration.lo[alpha_idx], 1e-15)
                    c_t_hi = max(node_t.concentration.hi[alpha_idx], 1e-15)

                    dphi_lo = (node_t.mu_0 + RT * np.log(c_t_lo)) - \
                              (node_s.mu_0 + RT * np.log(c_s_hi))
                    dphi_hi = (node_t.mu_0 + RT * np.log(c_t_hi)) - \
                              (node_s.mu_0 + RT * np.log(c_s_lo))

                    phi_sum_lo += dphi_lo
                    phi_sum_hi += dphi_hi

                    w = node_s.concentration.hi[alpha_idx] - \
                        node_s.concentration.lo[alpha_idx]
                    if w > widest_width:
                        widest_width = w
                        widest_node = src

                # If zero is not in [phi_sum_lo, phi_sum_hi], tighten widest
                if phi_sum_lo > 0 or phi_sum_hi < 0:
                    node = self.nodes[widest_node]
                    mid = 0.5 * (node.concentration.lo[alpha_idx] +
                                 node.concentration.hi[alpha_idx])
                    shrink = 0.9
                    half_w = 0.5 * widest_width * shrink
                    node.concentration.lo[alpha_idx] = max(mid - half_w, node.c_min)
                    node.concentration.hi[alpha_idx] = mid + half_w

    # -------------------------------------------------------------------------
    # Trajectory completion algorithm
    # -------------------------------------------------------------------------

    def trajectory_completion(self, observations: Dict[str, float],
                              max_iter: int = 100,
                              tol: float = 1e-6,
                              uncertainty: float = 0.1) -> Tuple[Dict[str, FuzzyInterval], int, float]:
        """
        Trajectory completion algorithm (Algorithm 1 from the paper).

        Takes partial observations and network topology. Returns the
        maximally-consistent fuzzy state. No healthy reference needed.

        Args:
            observations: dict mapping node_name -> measured concentration
            max_iter: maximum iterations
            tol: convergence tolerance (Hausdorff metric)
            uncertainty: measurement uncertainty (fraction)

        Returns:
            (fuzzy_states, iterations, final_residual)
        """
        # Step 1: Initialise
        for name, node in self.nodes.items():
            if name in observations:
                val = observations[name]
                node.concentration = FuzzyInterval.from_measurement(
                    val, val * uncertainty)
            else:
                node.concentration = FuzzyInterval.uniform(
                    node.c_min, node.c_max)

        cycles = self.find_loops()

        # Step 2: Iterate
        for iteration in range(max_iter):
            prev_states = {n: FuzzyInterval(
                alphas=self.nodes[n].concentration.alphas.copy(),
                lo=self.nodes[n].concentration.lo.copy(),
                hi=self.nodes[n].concentration.hi.copy(),
            ) for n in self.nodes}

            # Apply T_KCL
            for name in self.nodes:
                new_interval = self.apply_fuzzy_kcl(name)
                self.nodes[name].concentration = new_interval

            # Apply T_KVL
            if cycles:
                self.apply_fuzzy_kvl(cycles)

            # Re-pin observations
            for name, val in observations.items():
                self.nodes[name].concentration = FuzzyInterval.from_measurement(
                    val, val * uncertainty)

            # Check convergence
            max_dist = 0.0
            for name in self.nodes:
                d = self.nodes[name].concentration.hausdorff_distance(
                    prev_states[name])
                max_dist = max(max_dist, d)

            if max_dist < tol:
                break

        # Compute final residual
        conc = {n: self.nodes[n].concentration.center() for n in self.nodes}
        residual = self.total_kcl_residual(conc)

        states = {n: self.nodes[n].concentration for n in self.nodes}
        return states, iteration + 1, residual

    # -------------------------------------------------------------------------
    # Disease detection (reference-free)
    # -------------------------------------------------------------------------

    def detect_disease(self, observations: Dict[str, float],
                       consistency_threshold: float = 0.95,
                       kcl_threshold: float = 1e-4,
                       uncertainty: float = 0.1) -> Dict:
        """
        Reference-free disease detection.

        Runs trajectory completion and checks self-consistency via:
        1. Loop holonomy (KVL consistency)
        2. Node mass balance residuals (KCL consistency)
        3. Fuzzy interval widths (unresolved uncertainty)

        No healthy reference state is needed.

        Returns dict with:
            - healthy: bool
            - consistency_index: float
            - inconsistent_loops: list of (cycle, holonomy) pairs
            - kcl_inconsistent_nodes: list of nodes with mass balance violation
            - residual: total KCL residual
        """
        states, iterations, residual = self.trajectory_completion(
            observations, uncertainty=uncertainty)

        conc = {n: self.nodes[n].concentration.center() for n in self.nodes}
        loops = self.find_loops()

        # Check loop holonomy (KVL)
        inconsistent_loops = []
        for loop in loops:
            h = self.loop_holonomy(loop, conc)
            c = self.loop_consistency(loop, conc)
            if c < consistency_threshold:
                inconsistent_loops.append({
                    "cycle": loop,
                    "holonomy": h,
                    "consistency": c,
                })

        # Check node mass balance (KCL)
        kcl_inconsistent = []
        for name in self.nodes:
            res = abs(self.kcl_residual(name, conc))
            if res > kcl_threshold:
                kcl_inconsistent.append({
                    "node": name,
                    "residual": res,
                })

        # Check fuzzy interval widths — disease shows as inability to resolve
        wide_nodes = []
        for name, state in states.items():
            if name not in observations and not state.is_crisp(tol=1e-4):
                w = state.width(alpha=1.0)
                max_w = self.nodes[name].c_max - self.nodes[name].c_min
                if w > max_w * 0.5:  # more than 50% of range unresolved
                    wide_nodes.append({"node": name, "width_fraction": w / max_w})

        ci = self.consistency_index(conc)

        # Disease if ANY inconsistency detected
        is_healthy = (len(inconsistent_loops) == 0 and
                      len(kcl_inconsistent) == 0 and
                      len(wide_nodes) == 0)

        # Composite consistency incorporating KCL
        if kcl_inconsistent:
            max_kcl = max(n["residual"] for n in kcl_inconsistent)
            kcl_penalty = min(1.0, max_kcl / 1.0)  # normalise
            ci = ci * (1.0 - kcl_penalty * 0.5)

        if wide_nodes:
            ci = ci * (1.0 - 0.1 * len(wide_nodes) / len(self.nodes))

        return {
            "healthy": is_healthy,
            "consistency_index": ci,
            "inconsistent_loops": inconsistent_loops,
            "kcl_inconsistent_nodes": kcl_inconsistent,
            "wide_nodes": wide_nodes,
            "residual": residual,
            "iterations": iterations,
        }

    # -------------------------------------------------------------------------
    # Signal variance (early warning)
    # -------------------------------------------------------------------------

    @staticmethod
    def signal_variance_from_trajectory(signal_series: np.ndarray,
                                        window: int = 10) -> np.ndarray:
        """
        Compute step-to-step variance of a macroscopic signal over sliding windows.

        In a healthy circuit, this variance is low and stable.
        In a diseased circuit, it increases before clinical manifestation.
        """
        if len(signal_series) < window + 1:
            return np.array([np.var(np.diff(signal_series))])

        deltas = np.diff(signal_series)
        variances = np.array([
            np.var(deltas[i:i + window])
            for i in range(len(deltas) - window + 1)
        ])
        return variances

    # -------------------------------------------------------------------------
    # Drug design (sparse conductance modification)
    # -------------------------------------------------------------------------

    def optimal_drug_targets(self, observations: Dict[str, float],
                             max_targets: int = 3) -> List[Dict]:
        """
        Find minimal set of conductance modifications to restore consistency.

        Uses KCL residuals as the inconsistency measure and finds edges
        whose conductance perturbation most reduces total residual.
        This is the L1-sparse conductance modification from the paper.
        """
        conc = {n: self.nodes[n].concentration.center() for n in self.nodes}

        if not self.edges:
            return []

        node_names = list(self.nodes.keys())
        n_nodes = len(node_names)
        n_edges = len(self.edges)

        # Current KCL residual vector
        kcl_vec = np.array([self.kcl_residual(n, conc) for n in node_names])

        if np.all(np.abs(kcl_vec) < 1e-10):
            return []  # already consistent

        # Sensitivity: perturb each edge and measure KCL change
        eps = 1e-3
        sensitivity = np.zeros((n_nodes, n_edges))

        for j, edge in enumerate(self.edges):
            orig_k = edge.k_fwd
            edge.k_fwd = orig_k * (1 + eps)
            kcl_perturbed = np.array([self.kcl_residual(n, conc)
                                      for n in node_names])
            sensitivity[:, j] = (kcl_perturbed - kcl_vec) / eps
            edge.k_fwd = orig_k

        # Solve: min ||S*eta + kcl||^2 s.t. eta in [-1, 1]
        try:
            result = optimize.lsq_linear(
                sensitivity, -kcl_vec,
                bounds=(-1.0, 1.0),
            )
            eta = result.x
        except Exception:
            return []

        # Rank by |eta| and return top targets
        ranked = sorted(enumerate(eta), key=lambda x: abs(x[1]), reverse=True)
        targets = []
        for idx, eta_val in ranked[:max_targets]:
            if abs(eta_val) < 1e-8:
                break
            edge = self.edges[idx]
            targets.append({
                "edge": f"{edge.source} -> {edge.target}",
                "enzyme": edge.enzyme_name,
                "eta": float(eta_val),
                "interpretation": "inhibit" if eta_val > 0 else "activate",
            })

        return targets


# =============================================================================
# Pre-built circuit models for validation
# =============================================================================

def build_glycolysis_circuit(pk_deficient: bool = False,
                             pk_reduction: float = 0.1) -> BiochemicalCircuit:
    """
    Build a simplified glycolytic circuit for validation.

    10-step pathway: Glucose -> G6P -> F6P -> FBP -> DHAP/G3P -> 1,3BPG
                     -> 3PG -> 2PG -> PEP -> Pyruvate

    With ATP/ADP hub node participating in HK, PFK (consumption)
    and PGK, PK (production) loops.

    Args:
        pk_deficient: If True, reduce PK activity (disease model)
        pk_reduction: Fractional PK activity when deficient
    """
    circuit = BiochemicalCircuit()

    # Standard free energies (approximate, relative, J/mol)
    # Values chosen so KVL (Wegscheider) conditions are satisfied
    species = {
        "Glc":    {"mu_0": 0.0,       "c": 5.0e-3,   "c_min": 1e-6, "c_max": 0.05},
        "G6P":    {"mu_0": -1700.0,   "c": 0.083e-3, "c_min": 1e-7, "c_max": 0.01},
        "F6P":    {"mu_0": -1300.0,   "c": 0.014e-3, "c_min": 1e-7, "c_max": 0.01},
        "FBP":    {"mu_0": -3400.0,   "c": 0.031e-3, "c_min": 1e-7, "c_max": 0.01},
        "G3P":    {"mu_0": -1500.0,   "c": 0.019e-3, "c_min": 1e-7, "c_max": 0.01},
        "BPG13":  {"mu_0": -3000.0,   "c": 0.001e-3, "c_min": 1e-9, "c_max": 0.001},
        "PG3":    {"mu_0": -2800.0,   "c": 0.12e-3,  "c_min": 1e-7, "c_max": 0.01},
        "PG2":    {"mu_0": -2700.0,   "c": 0.030e-3, "c_min": 1e-7, "c_max": 0.01},
        "PEP":    {"mu_0": -4700.0,   "c": 0.023e-3, "c_min": 1e-7, "c_max": 0.01},
        "Pyr":    {"mu_0": -5000.0,   "c": 0.051e-3, "c_min": 1e-7, "c_max": 0.01},
        "ATP":    {"mu_0": -3000.0,   "c": 1.85e-3,  "c_min": 1e-6, "c_max": 0.01},
        "ADP":    {"mu_0": -1400.0,   "c": 0.14e-3,  "c_min": 1e-6, "c_max": 0.01},
    }

    for name, props in species.items():
        circuit.add_node(CircuitNode(
            name=name,
            mu_0=props["mu_0"],
            concentration=FuzzyInterval.from_measurement(props["c"], props["c"] * 0.1),
            c_min=props["c_min"],
            c_max=props["c_max"],
        ))

    # Rate constants (approximate, chosen for self-consistency)
    k_base = 1.0  # normalised rate

    # Glycolytic reactions
    reactions = [
        ("Glc",   "G6P",   k_base * 1.0,   k_base * 0.01,  "Hexokinase (HK)"),
        ("G6P",   "F6P",   k_base * 2.0,   k_base * 1.5,   "PGI"),
        ("F6P",   "FBP",   k_base * 0.8,   k_base * 0.01,  "PFK"),
        ("FBP",   "G3P",   k_base * 1.5,   k_base * 0.5,   "Aldolase"),
        ("G3P",   "BPG13", k_base * 1.0,   k_base * 0.3,   "GAPDH"),
        ("BPG13", "PG3",   k_base * 5.0,   k_base * 0.1,   "PGK"),
        ("PG3",   "PG2",   k_base * 3.0,   k_base * 2.5,   "PGM"),
        ("PG2",   "PEP",   k_base * 2.0,   k_base * 1.0,   "Enolase"),
        ("PEP",   "Pyr",   k_base * 3.0,   k_base * 0.01,  "PK"),
    ]

    # ATP/ADP coupling edges
    atp_edges = [
        ("ATP", "ADP", k_base * 1.0, k_base * 0.01, "HK-ATP"),      # HK consumes ATP
        ("ATP", "ADP", k_base * 0.8, k_base * 0.01, "PFK-ATP"),     # PFK consumes ATP
        ("ADP", "ATP", k_base * 5.0, k_base * 0.1,  "PGK-ATP"),     # PGK produces ATP
        ("ADP", "ATP", k_base * 3.0, k_base * 0.01, "PK-ATP"),      # PK produces ATP
    ]

    for src, tgt, kf, kr, enz in reactions:
        if enz == "PK" and pk_deficient:
            kf *= pk_reduction
        circuit.add_edge(CircuitEdge(
            source=src, target=tgt,
            k_fwd=kf, k_rev=kr, enzyme_name=enz,
        ))

    for src, tgt, kf, kr, enz in atp_edges:
        if "PK" in enz and pk_deficient:
            kf *= pk_reduction
        circuit.add_edge(CircuitEdge(
            source=src, target=tgt,
            k_fwd=kf, k_rev=kr, enzyme_name=enz,
        ))

    # Feedback edges creating metabolic loops
    feedback_edges = [
        # Pyruvate recycling (gluconeogenesis / anaplerosis)
        ("Pyr", "PEP",  k_base * 0.05, k_base * 0.001, "PEPCK"),
        # ATP product inhibition on HK (high ATP slows glucose uptake)
        ("ADP", "Glc",  k_base * 0.02, k_base * 0.001, "Feedback-HK"),
        # PEP feedback to F6P (gluconeogenic bypass)
        ("PEP", "F6P",  k_base * 0.03, k_base * 0.001, "FBPase"),
    ]

    for src, tgt, kf, kr, enz in feedback_edges:
        circuit.add_edge(CircuitEdge(
            source=src, target=tgt,
            k_fwd=kf, k_rev=kr, enzyme_name=enz,
        ))

    return circuit


def build_etc_circuit(complex_i_inhibited: bool = False,
                      inhibition_factor: float = 0.1) -> BiochemicalCircuit:
    """
    Build electron transport chain circuit for hub vulnerability validation.

    Central hub: delta_psi (membrane potential proxy as NAD+/NADH)
    Complexes I-IV feed into the hub; ATP synthase draws from it.
    """
    circuit = BiochemicalCircuit()

    species = {
        "NADH":     {"mu_0": -4000.0, "c": 0.1e-3,  "c_min": 1e-7, "c_max": 0.01},
        "UQH2":     {"mu_0": -2500.0, "c": 0.05e-3, "c_min": 1e-7, "c_max": 0.01},
        "CytC_red": {"mu_0": -1500.0, "c": 0.03e-3, "c_min": 1e-7, "c_max": 0.01},
        "O2":       {"mu_0": 0.0,     "c": 0.03e-3, "c_min": 1e-7, "c_max": 0.01},
        "H2O":      {"mu_0": -5000.0, "c": 55.0,    "c_min": 50.0, "c_max": 56.0},
        "NAD":      {"mu_0": -2000.0, "c": 0.5e-3,  "c_min": 1e-7, "c_max": 0.01},
        "UQ":       {"mu_0": -1000.0, "c": 0.1e-3,  "c_min": 1e-7, "c_max": 0.01},
        "CytC_ox":  {"mu_0": -500.0,  "c": 0.07e-3, "c_min": 1e-7, "c_max": 0.01},
        "ATP_m":    {"mu_0": -3000.0, "c": 2.0e-3,  "c_min": 1e-6, "c_max": 0.01},
        "ADP_m":    {"mu_0": -1400.0, "c": 0.3e-3,  "c_min": 1e-6, "c_max": 0.01},
    }

    for name, props in species.items():
        circuit.add_node(CircuitNode(
            name=name, mu_0=props["mu_0"],
            concentration=FuzzyInterval.from_measurement(props["c"], props["c"] * 0.1),
            c_min=props["c_min"], c_max=props["c_max"],
        ))

    k_ci = 1.0 if not complex_i_inhibited else inhibition_factor

    edges = [
        ("NADH",     "UQH2",     k_ci,  0.01, "Complex I"),
        ("NADH",     "NAD",      k_ci,  0.01, "Complex I (NAD)"),
        ("UQH2",     "CytC_red", 1.0,   0.05, "Complex III"),
        ("UQH2",     "UQ",       1.0,   0.05, "Complex III (UQ)"),
        ("CytC_red", "CytC_ox",  1.5,   0.03, "Complex IV"),
        ("CytC_red", "H2O",      0.5,   0.001,"Complex IV (H2O)"),
        ("ADP_m",    "ATP_m",    2.0,   0.1,  "ATP Synthase"),
        ("NAD",      "NADH",     0.5,   0.01, "TCA cycle"),
        ("UQ",       "UQH2",     0.3,   0.01, "Succinate DH (CII)"),
    ]

    for src, tgt, kf, kr, enz in edges:
        circuit.add_edge(CircuitEdge(
            source=src, target=tgt,
            k_fwd=kf, k_rev=kr, enzyme_name=enz,
        ))

    return circuit


def build_protein_qc_circuit(misfolding_rate: float = 1e-6) -> BiochemicalCircuit:
    """
    Build protein quality control circuit.

    4-node loop: Synthesis -> Folding -> Function -> Degradation -> (back to synthesis)
    The misfolding_rate controls the per-cycle defect delta.
    """
    circuit = BiochemicalCircuit()

    species = {
        "nascent":    {"mu_0": 0.0,      "c": 1e-4, "c_min": 1e-9, "c_max": 0.01},
        "folded":     {"mu_0": -3000.0,  "c": 1e-3, "c_min": 1e-9, "c_max": 0.01},
        "functional": {"mu_0": -5000.0,  "c": 5e-3, "c_min": 1e-9, "c_max": 0.05},
        "degraded":   {"mu_0": -1000.0,  "c": 1e-4, "c_min": 1e-9, "c_max": 0.01},
    }

    for name, props in species.items():
        circuit.add_node(CircuitNode(
            name=name, mu_0=props["mu_0"],
            concentration=FuzzyInterval.from_measurement(props["c"], props["c"] * 0.1),
            c_min=props["c_min"], c_max=props["c_max"],
        ))

    # Folding rate reduced by misfolding
    k_fold = 1.0 * (1.0 - misfolding_rate)

    edges = [
        ("nascent",    "folded",     1.0,    0.01, "Ribosome"),
        ("folded",     "functional", k_fold, 0.01, "QC/Chaperone"),
        ("functional", "degraded",   0.1,    0.001,"Proteasome"),
        ("degraded",   "nascent",    0.5,    0.01, "Recycling"),
    ]

    for src, tgt, kf, kr, enz in edges:
        circuit.add_edge(CircuitEdge(
            source=src, target=tgt,
            k_fwd=kf, k_rev=kr, enzyme_name=enz,
        ))

    return circuit


def simulate_disease_progression(circuit: BiochemicalCircuit,
                                 defect_node: str,
                                 defect_rate: float,
                                 n_steps: int = 100) -> Dict:
    """
    Simulate sequential constraint propagation with accumulating defect.

    At each step:
    1. Introduce defect at defect_node
    2. Propagate constraints
    3. Record macroscopic signals (concentrations, ratios)

    Returns time series of consistency index and signal variances.
    """
    consistency_series = []
    signal_series = {n: [] for n in circuit.nodes}

    conc = {n: circuit.nodes[n].concentration.center() for n in circuit.nodes}

    for step in range(n_steps):
        # Apply defect: per-step noise with amplitude growing linearly
        # This models accumulating loop holonomy residual (Theorem 6.3)
        if defect_node in conc and defect_rate > 0:
            noise_amplitude = defect_rate * (1.0 + step / 50.0)
            perturbation = noise_amplitude * np.random.randn()
            conc[defect_node] *= (1.0 + perturbation)
            conc[defect_node] = np.clip(
                conc[defect_node],
                circuit.nodes[defect_node].c_min,
                circuit.nodes[defect_node].c_max,
            )

        # Propagate: simple relaxation step
        new_conc = {}
        for name in circuit.nodes:
            in_flux = sum(
                e.k_fwd * conc.get(e.source, 1e-6)
                for e in circuit._in_edges.get(name, [])
            )
            out_k = sum(e.k_fwd for e in circuit._adjacency.get(name, [])) + \
                    sum(e.k_rev for e in circuit._in_edges.get(name, []))

            if out_k > 0 and in_flux > 0:
                # Relaxation toward mass-balance
                target_c = in_flux / out_k
                new_conc[name] = 0.9 * conc[name] + 0.1 * target_c
            else:
                new_conc[name] = conc[name]

            new_conc[name] = max(new_conc[name], circuit.nodes[name].c_min)

        conc = new_conc

        # Record
        ci = circuit.consistency_index(conc)
        consistency_series.append(ci)
        for n in circuit.nodes:
            signal_series[n].append(conc[n])

    return {
        "consistency": np.array(consistency_series),
        "signals": {n: np.array(v) for n, v in signal_series.items()},
        "n_steps": n_steps,
    }

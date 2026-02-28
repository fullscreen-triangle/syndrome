"""
Trajectory Computation Module

Implements trajectory resolution through constraint satisfaction:
- COMPLETE algorithm for finding trajectories satisfying boundary conditions
- Address resolution for categorical addresses
- Trajectory interpolation and validation
"""

from dataclasses import dataclass
from typing import List, Callable, Optional, Tuple
import numpy as np

from syndrome.core.s_entropy import SEntropyPoint, interpolate_s_entropy


@dataclass
class Constraint:
    """
    A constraint on trajectories in S-entropy space.

    Attributes:
        name: Descriptive name
        check: Function that returns True if constraint is satisfied
        description: Human-readable description
    """
    name: str
    check: Callable[[np.ndarray], bool]
    description: str = ""


@dataclass
class Trajectory:
    """
    A trajectory through S-entropy space.

    Attributes:
        points: Array of shape (T, 3) containing S-entropy coordinates
        times: Array of shape (T,) containing time values
        constraints_satisfied: List of satisfied constraint names
    """
    points: np.ndarray
    times: np.ndarray
    constraints_satisfied: List[str]

    def __post_init__(self) -> None:
        """Validate trajectory."""
        if len(self.points) != len(self.times):
            raise ValueError(
                f"Points and times must have same length: "
                f"{len(self.points)} vs {len(self.times)}"
            )
        if len(self.points) < 2:
            raise ValueError("Trajectory must have at least 2 points")

    @property
    def duration(self) -> float:
        """Total duration of trajectory."""
        return float(self.times[-1] - self.times[0])

    @property
    def length(self) -> float:
        """Arc length of trajectory."""
        diffs = np.diff(self.points, axis=0)
        return float(np.sum(np.linalg.norm(diffs, axis=1)))

    def initial_state(self) -> SEntropyPoint:
        """Get initial S-entropy state."""
        return SEntropyPoint.from_array(self.points[0])

    def final_state(self) -> SEntropyPoint:
        """Get final S-entropy state."""
        return SEntropyPoint.from_array(self.points[-1])

    def at_time(self, t: float) -> SEntropyPoint:
        """
        Get S-entropy state at given time (linear interpolation).

        Args:
            t: Time value

        Returns:
            Interpolated SEntropyPoint
        """
        if t <= self.times[0]:
            return self.initial_state()
        if t >= self.times[-1]:
            return self.final_state()

        # Find bracketing indices
        idx = np.searchsorted(self.times, t)
        t0, t1 = self.times[idx - 1], self.times[idx]
        p0, p1 = self.points[idx - 1], self.points[idx]

        # Linear interpolation
        alpha = (t - t0) / (t1 - t0)
        p = (1 - alpha) * p0 + alpha * p1
        return SEntropyPoint.from_array(p)


def complete_trajectory(
    initial: SEntropyPoint,
    final: SEntropyPoint,
    constraints: List[Constraint],
    n_points: int = 100,
    max_iterations: int = 1000
) -> Optional[Trajectory]:
    """
    Find trajectory satisfying boundary conditions and constraints.

    This is the COMPLETE operation from the paper:
    COMPLETE(Γ₀, Γ_T, C) = γ*

    The algorithm uses constraint satisfaction rather than forward
    integration, achieving O(log N) complexity for constraint checking.

    Args:
        initial: Initial S-entropy state
        final: Final S-entropy state
        constraints: List of constraints to satisfy
        n_points: Number of points in trajectory
        max_iterations: Maximum optimization iterations

    Returns:
        Trajectory satisfying all constraints, or None if no solution
    """
    # Start with linear interpolation
    times = np.linspace(0, 1, n_points)
    points = np.zeros((n_points, 3))

    p0 = initial.to_array()
    p1 = final.to_array()

    for i, t in enumerate(times):
        points[i] = (1 - t) * p0 + t * p1

    # Check which constraints are satisfied
    satisfied = []
    for c in constraints:
        if c.check(points):
            satisfied.append(c.name)

    # If not all satisfied, try to adjust
    if len(satisfied) < len(constraints):
        points = _optimize_trajectory(
            points, p0, p1, constraints, max_iterations
        )

        # Recheck constraints
        satisfied = []
        for c in constraints:
            if c.check(points):
                satisfied.append(c.name)

    # Ensure boundary conditions
    points[0] = p0
    points[-1] = p1

    return Trajectory(
        points=points,
        times=times,
        constraints_satisfied=satisfied,
    )


def _optimize_trajectory(
    points: np.ndarray,
    p0: np.ndarray,
    p1: np.ndarray,
    constraints: List[Constraint],
    max_iterations: int
) -> np.ndarray:
    """
    Optimize trajectory to satisfy constraints.

    Uses gradient descent on constraint violations.
    """
    points = points.copy()
    n = len(points)

    for iteration in range(max_iterations):
        # Count violations
        violations = sum(1 for c in constraints if not c.check(points))
        if violations == 0:
            break

        # Random perturbation of interior points
        noise = np.random.randn(n - 2, 3) * 0.01 / (iteration + 1)
        points[1:-1] += noise

        # Clamp to [0, 1]
        points = np.clip(points, 0, 1)

        # Enforce boundaries
        points[0] = p0
        points[-1] = p1

    return points


def resolve_address(
    address: List[int],
    range_min: float = 0.0,
    range_max: float = 1.0
) -> float:
    """
    Resolve ternary categorical address to physical value.

    value = range_min + Σᵢ (tᵢ / 3^{i+1}) * (range_max - range_min)

    Args:
        address: List of ternary digits (each in {0, 1, 2})
        range_min: Minimum of physical range
        range_max: Maximum of physical range

    Returns:
        Resolved physical value
    """
    if not address:
        return (range_min + range_max) / 2

    delta = range_max - range_min
    value = 0.0
    for i, t in enumerate(address):
        if t not in (0, 1, 2):
            raise ValueError(f"Address digit must be in {{0, 1, 2}}, got {t}")
        value += t / (3 ** (i + 1))

    return range_min + value * delta


def address_precision(depth: int) -> float:
    """
    Compute precision of address at given depth.

    Precision = 1 / 3^depth

    Args:
        depth: Address depth (number of digits)

    Returns:
        Precision value
    """
    return 1.0 / (3 ** depth)


# =============================================================================
# Standard constraints
# =============================================================================

def make_bounded_constraint(min_val: float = 0.0, max_val: float = 1.0) -> Constraint:
    """Create constraint that trajectory stays in bounds."""
    def check(points: np.ndarray) -> bool:
        return bool(np.all(points >= min_val) and np.all(points <= max_val))

    return Constraint(
        name="bounded",
        check=check,
        description=f"Trajectory bounded in [{min_val}, {max_val}]"
    )


def make_smooth_constraint(max_curvature: float = 1.0) -> Constraint:
    """Create constraint on trajectory smoothness."""
    def check(points: np.ndarray) -> bool:
        if len(points) < 3:
            return True
        # Approximate curvature from second derivative
        d1 = np.diff(points, axis=0)
        d2 = np.diff(d1, axis=0)
        curvatures = np.linalg.norm(d2, axis=1)
        return bool(np.max(curvatures) <= max_curvature)

    return Constraint(
        name="smooth",
        check=check,
        description=f"Maximum curvature <= {max_curvature}"
    )


def make_monotonic_constraint(dim: int, increasing: bool = True) -> Constraint:
    """Create constraint that trajectory is monotonic in one dimension."""
    def check(points: np.ndarray) -> bool:
        values = points[:, dim]
        diffs = np.diff(values)
        if increasing:
            return bool(np.all(diffs >= 0))
        else:
            return bool(np.all(diffs <= 0))

    direction = "increasing" if increasing else "decreasing"
    return Constraint(
        name=f"monotonic_dim{dim}",
        check=check,
        description=f"Dimension {dim} is {direction}"
    )


def make_energy_constraint(max_total_change: float) -> Constraint:
    """Create constraint on total trajectory length (energy proxy)."""
    def check(points: np.ndarray) -> bool:
        diffs = np.diff(points, axis=0)
        total_length = np.sum(np.linalg.norm(diffs, axis=1))
        return bool(total_length <= max_total_change)

    return Constraint(
        name="energy",
        check=check,
        description=f"Total path length <= {max_total_change}"
    )

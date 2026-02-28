"""
Partition Geometry Module

Implements partition coordinates (n, ℓ, m, s) and related operations
derived from bounded phase space and categorical observation axioms.

The partition capacity C(n) = 2n² emerges as geometric necessity from
spherical symmetry of bounded phase space.
"""

from dataclasses import dataclass
from typing import Tuple, List
import numpy as np


@dataclass(frozen=True)
class PartitionCoord:
    """
    Partition coordinates in categorical space.

    Attributes:
        n: Depth coordinate (n >= 1)
        ell: Complexity coordinate (0 <= ell <= n-1)
        m: Orientation coordinate (-ell <= m <= ell)
        s: Chirality coordinate (s in {-0.5, +0.5})
    """
    n: int
    ell: int
    m: int
    s: float

    def __post_init__(self) -> None:
        """Validate partition coordinates."""
        if not is_valid_partition_coord(self.n, self.ell, self.m, self.s):
            raise ValueError(
                f"Invalid partition coordinates: n={self.n}, ℓ={self.ell}, "
                f"m={self.m}, s={self.s}"
            )

    def to_tuple(self) -> Tuple[int, int, int, float]:
        """Convert to tuple representation."""
        return (self.n, self.ell, self.m, self.s)

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for numerical operations."""
        return np.array([self.n, self.ell, self.m, self.s], dtype=np.float64)


def is_valid_partition_coord(n: int, ell: int, m: int, s: float) -> bool:
    """
    Check if partition coordinates are valid.

    Valid coordinates satisfy:
    - n >= 1 (at least one partition)
    - 0 <= ell <= n-1 (complexity bounded by depth)
    - -ell <= m <= ell (orientation bounded by complexity)
    - s in {-0.5, +0.5} (chirality is binary)

    Args:
        n: Depth coordinate
        ell: Complexity coordinate
        m: Orientation coordinate
        s: Chirality coordinate

    Returns:
        True if coordinates are valid, False otherwise
    """
    if n < 1:
        return False
    if ell < 0 or ell > n - 1:
        return False
    if m < -ell or m > ell:
        return False
    if s not in (-0.5, 0.5):
        return False
    return True


def partition_capacity(n: int) -> int:
    """
    Compute partition capacity at depth n.

    The capacity C(n) = 2n² follows from:
    - Sum over ell from 0 to n-1 of (2*ell + 1) orientations
    - Factor of 2 for chirality

    This yields the sequence: 2, 8, 18, 32, 50, 72, 98, ...
    which matches electron shell capacities in atomic physics.

    Args:
        n: Partition depth (n >= 1)

    Returns:
        Capacity C(n) = 2n²

    Raises:
        ValueError: If n < 1
    """
    if n < 1:
        raise ValueError(f"Partition depth must be >= 1, got {n}")
    return 2 * n * n


def categorical_distance(
    sigma1: PartitionCoord,
    sigma2: PartitionCoord
) -> float:
    """
    Compute categorical distance between partition states.

    The categorical distance is defined as Euclidean distance in
    partition coordinate space:

    d_cat = sqrt((n1-n2)² + (ℓ1-ℓ2)² + (m1-m2)² + (s1-s2)²)

    IMPORTANT: Categorical distance is independent of:
    - Spatial distance (d_cat ⊥ d_spatial)
    - Optical opacity (∂d_cat/∂τ = 0)

    This enables opacity-independent measurement of states behind
    arbitrary optical barriers.

    Args:
        sigma1: First partition state
        sigma2: Second partition state

    Returns:
        Categorical distance d_cat >= 0
    """
    arr1 = sigma1.to_array()
    arr2 = sigma2.to_array()
    return float(np.linalg.norm(arr1 - arr2))


def categorical_distance_raw(
    n1: int, ell1: int, m1: int, s1: float,
    n2: int, ell2: int, m2: int, s2: float
) -> float:
    """
    Compute categorical distance from raw coordinates.

    Args:
        n1, ell1, m1, s1: First partition state coordinates
        n2, ell2, m2, s2: Second partition state coordinates

    Returns:
        Categorical distance d_cat >= 0
    """
    return np.sqrt(
        (n1 - n2)**2 +
        (ell1 - ell2)**2 +
        (m1 - m2)**2 +
        (s1 - s2)**2
    )


def enumerate_partition_states(n: int) -> List[PartitionCoord]:
    """
    Enumerate all partition states at depth n.

    Args:
        n: Partition depth

    Returns:
        List of all C(n) = 2n² partition states at depth n
    """
    states = []
    for ell in range(n):
        for m in range(-ell, ell + 1):
            for s in (-0.5, 0.5):
                states.append(PartitionCoord(n=n, ell=ell, m=m, s=s))
    return states


def address_to_value(
    address: List[int],
    range_min: float = 0.0,
    range_max: float = 1.0
) -> float:
    """
    Resolve ternary categorical address to physical value.

    An address [t_0, t_1, ..., t_{k-1}] with t_i in {0, 1, 2}
    resolves to:

    value = range_min + Σ_i (t_i / 3^{i+1}) * (range_max - range_min)

    Args:
        address: List of ternary digits
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


def value_to_address(
    value: float,
    depth: int,
    range_min: float = 0.0,
    range_max: float = 1.0
) -> List[int]:
    """
    Convert physical value to ternary categorical address.

    Args:
        value: Physical value to encode
        depth: Depth of address (number of ternary digits)
        range_min: Minimum of physical range
        range_max: Maximum of physical range

    Returns:
        Ternary address as list of digits
    """
    if value < range_min or value > range_max:
        raise ValueError(
            f"Value {value} outside range [{range_min}, {range_max}]"
        )

    # Normalize to [0, 1]
    normalized = (value - range_min) / (range_max - range_min)

    address = []
    remaining = normalized
    for _ in range(depth):
        digit = int(remaining * 3)
        digit = min(digit, 2)  # Clamp to valid range
        address.append(digit)
        remaining = remaining * 3 - digit

    return address

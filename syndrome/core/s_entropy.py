"""
S-Entropy Space Module

Implements the S-entropy coordinate system S = [0,1]³ comprising:
- Sₖ: Knowledge entropy (uncertainty in state identification)
- Sₜ: Temporal entropy (uncertainty in timing relationships)
- Sₑ: Evolution entropy (uncertainty in trajectory progression)

Any categorical state in bounded phase space maps uniquely to a point in S.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np


@dataclass
class SEntropyPoint:
    """
    Point in S-entropy space.

    All coordinates are normalized to [0, 1] where:
    - 0 indicates minimum entropy (maximum certainty)
    - 1 indicates maximum entropy (maximum uncertainty)

    Attributes:
        s_k: Knowledge entropy (state identification uncertainty)
        s_t: Temporal entropy (timing uncertainty)
        s_e: Evolution entropy (trajectory uncertainty)
    """
    s_k: float
    s_t: float
    s_e: float

    def __post_init__(self) -> None:
        """Validate S-entropy coordinates."""
        for name, val in [("s_k", self.s_k), ("s_t", self.s_t), ("s_e", self.s_e)]:
            if not 0.0 <= val <= 1.0:
                raise ValueError(
                    f"S-entropy coordinate {name} must be in [0, 1], got {val}"
                )

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple representation."""
        return (self.s_k, self.s_t, self.s_e)

    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.s_k, self.s_t, self.s_e], dtype=np.float64)

    @classmethod
    def from_array(cls, arr: np.ndarray) -> "SEntropyPoint":
        """Create from numpy array."""
        if len(arr) != 3:
            raise ValueError(f"Array must have length 3, got {len(arr)}")
        return cls(s_k=float(arr[0]), s_t=float(arr[1]), s_e=float(arr[2]))

    def total_entropy(self) -> float:
        """Compute total entropy as Euclidean norm."""
        return float(np.linalg.norm(self.to_array()))

    def mean_entropy(self) -> float:
        """Compute mean entropy across coordinates."""
        return (self.s_k + self.s_t + self.s_e) / 3.0


def s_entropy_distance(p1: SEntropyPoint, p2: SEntropyPoint) -> float:
    """
    Compute distance between two S-entropy points.

    Uses Euclidean distance in the flat S-entropy space.

    Args:
        p1: First S-entropy point
        p2: Second S-entropy point

    Returns:
        Distance d >= 0
    """
    return float(np.linalg.norm(p1.to_array() - p2.to_array()))


def normalize_s_entropy(
    values: Tuple[float, float, float],
    bounds: Optional[Tuple[Tuple[float, float], ...]] = None
) -> SEntropyPoint:
    """
    Normalize raw entropy values to S-entropy coordinates.

    Args:
        values: Raw entropy values (S_k, S_t, S_e)
        bounds: Optional bounds ((min_k, max_k), (min_t, max_t), (min_e, max_e))
                If None, assumes values are already in appropriate ranges

    Returns:
        Normalized SEntropyPoint
    """
    s_k, s_t, s_e = values

    if bounds is not None:
        (min_k, max_k), (min_t, max_t), (min_e, max_e) = bounds
        s_k = (s_k - min_k) / (max_k - min_k) if max_k != min_k else 0.5
        s_t = (s_t - min_t) / (max_t - min_t) if max_t != min_t else 0.5
        s_e = (s_e - min_e) / (max_e - min_e) if max_e != min_e else 0.5

    # Clamp to [0, 1]
    s_k = max(0.0, min(1.0, s_k))
    s_t = max(0.0, min(1.0, s_t))
    s_e = max(0.0, min(1.0, s_e))

    return SEntropyPoint(s_k=s_k, s_t=s_t, s_e=s_e)


def interpolate_s_entropy(
    p1: SEntropyPoint,
    p2: SEntropyPoint,
    t: float
) -> SEntropyPoint:
    """
    Linear interpolation between two S-entropy points.

    Args:
        p1: Starting point (t=0)
        p2: Ending point (t=1)
        t: Interpolation parameter in [0, 1]

    Returns:
        Interpolated SEntropyPoint
    """
    if not 0.0 <= t <= 1.0:
        raise ValueError(f"Interpolation parameter must be in [0, 1], got {t}")

    arr = (1 - t) * p1.to_array() + t * p2.to_array()
    return SEntropyPoint.from_array(arr)


def s_entropy_from_distribution(probabilities: np.ndarray) -> float:
    """
    Compute Shannon entropy from probability distribution.

    S = -Σ p_i log(p_i)

    Normalized to [0, 1] by dividing by log(N).

    Args:
        probabilities: Probability distribution (must sum to 1)

    Returns:
        Normalized entropy in [0, 1]
    """
    # Filter out zeros to avoid log(0)
    p = probabilities[probabilities > 0]

    if len(p) == 0:
        return 0.0

    # Shannon entropy
    entropy = -np.sum(p * np.log(p))

    # Normalize by maximum entropy log(N)
    max_entropy = np.log(len(probabilities))
    if max_entropy == 0:
        return 0.0

    return float(entropy / max_entropy)


def estimate_s_entropy_from_trajectory(
    trajectory: np.ndarray,
    n_bins: int = 10
) -> SEntropyPoint:
    """
    Estimate S-entropy coordinates from a trajectory in phase space.

    Args:
        trajectory: Array of shape (T, D) where T is time steps and D is dimension
        n_bins: Number of bins for histogram estimation

    Returns:
        Estimated SEntropyPoint
    """
    if len(trajectory) < 2:
        raise ValueError("Trajectory must have at least 2 points")

    T, D = trajectory.shape

    # S_k: Knowledge entropy from state distribution
    # Histogram of positions
    hist, _ = np.histogramdd(trajectory, bins=n_bins)
    hist = hist.flatten()
    hist = hist / hist.sum()
    s_k = s_entropy_from_distribution(hist)

    # S_t: Temporal entropy from time intervals
    # Analyze regularity of trajectory timing
    velocities = np.diff(trajectory, axis=0)
    speeds = np.linalg.norm(velocities, axis=1)
    if speeds.std() > 0:
        speed_hist, _ = np.histogram(speeds, bins=n_bins, density=True)
        speed_hist = speed_hist / speed_hist.sum() if speed_hist.sum() > 0 else speed_hist
        s_t = s_entropy_from_distribution(speed_hist)
    else:
        s_t = 0.0

    # S_e: Evolution entropy from trajectory direction changes
    if T > 2:
        directions = velocities / (np.linalg.norm(velocities, axis=1, keepdims=True) + 1e-10)
        direction_changes = np.diff(directions, axis=0)
        change_magnitudes = np.linalg.norm(direction_changes, axis=1)
        if change_magnitudes.std() > 0:
            change_hist, _ = np.histogram(change_magnitudes, bins=n_bins, density=True)
            change_hist = change_hist / change_hist.sum() if change_hist.sum() > 0 else change_hist
            s_e = s_entropy_from_distribution(change_hist)
        else:
            s_e = 0.0
    else:
        s_e = 0.0

    return SEntropyPoint(s_k=s_k, s_t=s_t, s_e=s_e)

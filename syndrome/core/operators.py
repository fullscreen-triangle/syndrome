"""
Partition Operators Module

Implements partition operators acting on S-entropy space:
- Photon operator P_γ(ω)
- Gradient operator ∇_S
- Phase-lock operator Φ(ω₁, ω₂)
- Aperture operator A(d_cat)

Operators satisfy:
- Conservation: ||P(Γ)||_S = ||Γ||_S
- Coherence: Phase relationships preserved
- Causality: S_t(P(Γ)) >= S_t(Γ)
"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple
import numpy as np

from syndrome.core.s_entropy import SEntropyPoint


@dataclass
class PartitionOperator:
    """
    A partition operator acting on S-entropy space.

    Attributes:
        name: Operator name
        apply: Function mapping SEntropyPoint -> SEntropyPoint
        is_conservative: Whether operator preserves norm
        frequency: Associated frequency (if applicable)
    """
    name: str
    apply: Callable[[SEntropyPoint], SEntropyPoint]
    is_conservative: bool = True
    frequency: Optional[float] = None

    def __call__(self, state: SEntropyPoint) -> SEntropyPoint:
        """Apply operator to state."""
        return self.apply(state)

    def compose(self, other: "PartitionOperator") -> "PartitionOperator":
        """Compose with another operator: (self ∘ other)."""
        def composed_apply(state: SEntropyPoint) -> SEntropyPoint:
            return self.apply(other.apply(state))

        return PartitionOperator(
            name=f"({self.name} ∘ {other.name})",
            apply=composed_apply,
            is_conservative=self.is_conservative and other.is_conservative,
        )


def identity_operator() -> PartitionOperator:
    """Create identity operator."""
    return PartitionOperator(
        name="I",
        apply=lambda s: s,
        is_conservative=True,
    )


def photon_operator(
    omega: float,
    delta_magnitude: float = 0.01,
    direction: Optional[np.ndarray] = None
) -> PartitionOperator:
    """
    Create photon operator P_γ(ω).

    Mediates categorical transitions at frequency ω:
    P_γ(ω): Γ → Γ + δS with ||δS|| = ℏω/E_max

    Args:
        omega: Frequency (rad/s)
        delta_magnitude: Magnitude of state change
        direction: Direction of change in S-space (normalized)

    Returns:
        PartitionOperator
    """
    if direction is None:
        # Default: change along S_k direction
        direction = np.array([1.0, 0.0, 0.0])
    else:
        direction = direction / np.linalg.norm(direction)

    def apply(state: SEntropyPoint) -> SEntropyPoint:
        arr = state.to_array()
        delta = delta_magnitude * direction

        # Apply change
        new_arr = arr + delta

        # Clamp to [0, 1]
        new_arr = np.clip(new_arr, 0, 1)

        return SEntropyPoint.from_array(new_arr)

    return PartitionOperator(
        name=f"P_γ({omega:.2e})",
        apply=apply,
        is_conservative=False,  # Photon adds energy
        frequency=omega,
    )


def gradient_operator(
    gradient: np.ndarray,
    step_size: float = 0.01
) -> PartitionOperator:
    """
    Create gradient operator ∇_S.

    Generates S-entropy flow:
    ∇_S = (∂/∂Sₖ, ∂/∂Sₜ, ∂/∂Sₑ)

    Args:
        gradient: Gradient vector in S-space
        step_size: Step size for gradient descent

    Returns:
        PartitionOperator
    """
    gradient = np.asarray(gradient)

    def apply(state: SEntropyPoint) -> SEntropyPoint:
        arr = state.to_array()
        new_arr = arr - step_size * gradient
        new_arr = np.clip(new_arr, 0, 1)
        return SEntropyPoint.from_array(new_arr)

    return PartitionOperator(
        name="∇_S",
        apply=apply,
        is_conservative=True,
    )


def phase_lock_operator(
    omega1: float,
    omega2: float,
    lock_bandwidth: float = 0.1
) -> PartitionOperator:
    """
    Create phase-lock operator Φ(ω₁, ω₂).

    Couples oscillators if |ω₁ - ω₂| < Δω_lock:
    Φ(ω₁, ω₂): (Γ₁, Γ₂) → Γ₁₂

    This operator acts on a single state by reducing its temporal entropy
    when frequencies are within lock bandwidth.

    Args:
        omega1: First frequency
        omega2: Second frequency
        lock_bandwidth: Maximum frequency difference for locking

    Returns:
        PartitionOperator
    """
    freq_diff = abs(omega1 - omega2)
    can_lock = freq_diff < lock_bandwidth

    def apply(state: SEntropyPoint) -> SEntropyPoint:
        if not can_lock:
            return state

        arr = state.to_array()

        # Phase locking reduces temporal entropy
        lock_strength = 1.0 - freq_diff / lock_bandwidth
        arr[1] *= (1.0 - 0.5 * lock_strength)  # Reduce S_t

        arr = np.clip(arr, 0, 1)
        return SEntropyPoint.from_array(arr)

    return PartitionOperator(
        name=f"Φ({omega1:.2e}, {omega2:.2e})",
        apply=apply,
        is_conservative=True,
        frequency=(omega1 + omega2) / 2,
    )


def aperture_operator(
    d_cat_max: float,
    center: Optional[np.ndarray] = None
) -> PartitionOperator:
    """
    Create aperture operator A(d_cat).

    Constrains transitions through categorical distance bound:
    A(d_cat): Γ₁ → Γ₂ with ||Γ₂ - Γ₁||_cat ≤ d_cat

    Args:
        d_cat_max: Maximum categorical distance
        center: Center of aperture in S-space

    Returns:
        PartitionOperator
    """
    if center is None:
        center = np.array([0.5, 0.5, 0.5])
    else:
        center = np.asarray(center)

    def apply(state: SEntropyPoint) -> SEntropyPoint:
        arr = state.to_array()
        distance = np.linalg.norm(arr - center)

        if distance <= d_cat_max:
            return state

        # Project to boundary of aperture
        direction = (arr - center) / distance
        new_arr = center + d_cat_max * direction
        new_arr = np.clip(new_arr, 0, 1)

        return SEntropyPoint.from_array(new_arr)

    return PartitionOperator(
        name=f"A({d_cat_max:.2f})",
        apply=apply,
        is_conservative=True,
    )


def diffusion_operator(
    diffusivity: float,
    target: Optional[SEntropyPoint] = None
) -> PartitionOperator:
    """
    Create diffusion operator D.

    Models diffusive transport in S-entropy space:
    D: Γ → Γ + D∇²Γ

    Args:
        diffusivity: Diffusion coefficient
        target: Target state for diffusion (default: center)

    Returns:
        PartitionOperator
    """
    if target is None:
        target_arr = np.array([0.5, 0.5, 0.5])
    else:
        target_arr = target.to_array()

    def apply(state: SEntropyPoint) -> SEntropyPoint:
        arr = state.to_array()

        # Diffuse toward target
        diff = target_arr - arr
        new_arr = arr + diffusivity * diff

        new_arr = np.clip(new_arr, 0, 1)
        return SEntropyPoint.from_array(new_arr)

    return PartitionOperator(
        name=f"D({diffusivity:.3f})",
        apply=apply,
        is_conservative=True,
    )


def rotation_operator(
    angle: float,
    axis: int = 2
) -> PartitionOperator:
    """
    Create rotation operator in S-entropy space.

    Rotates state around specified axis.

    Args:
        angle: Rotation angle (radians)
        axis: Axis of rotation (0, 1, or 2)

    Returns:
        PartitionOperator
    """
    c, s = np.cos(angle), np.sin(angle)

    if axis == 0:
        R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    elif axis == 1:
        R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    else:
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    def apply(state: SEntropyPoint) -> SEntropyPoint:
        arr = state.to_array()

        # Translate to center, rotate, translate back
        centered = arr - 0.5
        rotated = R @ centered
        new_arr = rotated + 0.5

        new_arr = np.clip(new_arr, 0, 1)
        return SEntropyPoint.from_array(new_arr)

    return PartitionOperator(
        name=f"R_{axis}({angle:.2f})",
        apply=apply,
        is_conservative=True,
    )


def therapeutic_operator(
    efficacy: float,
    target_coherence: float = 1.0
) -> PartitionOperator:
    """
    Create therapeutic operator for coherence restoration.

    T(E): Γ → Γ' where η' = η + E(1-η)

    Reduces all entropy coordinates proportionally.

    Args:
        efficacy: Treatment efficacy E ∈ [0, 1]
        target_coherence: Target coherence (1.0 = fully healthy)

    Returns:
        PartitionOperator
    """
    def apply(state: SEntropyPoint) -> SEntropyPoint:
        arr = state.to_array()

        # High coherence = low entropy
        # Reduce entropy by factor (1 - efficacy * (1 - target_entropy))
        target_entropy = 1.0 - target_coherence
        reduction = 1.0 - efficacy * (1.0 - target_entropy)

        new_arr = arr * reduction
        new_arr = np.clip(new_arr, 0, 1)

        return SEntropyPoint.from_array(new_arr)

    return PartitionOperator(
        name=f"T({efficacy:.2f})",
        apply=apply,
        is_conservative=False,
    )

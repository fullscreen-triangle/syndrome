"""
Coherence Computation Module

Implements the universal coherence equation and related computations:

η = (Π_obs - Π_deg) / (Π_opt - Π_deg)

where:
- η ∈ [0, 1] is the coherence index
- Π_obs is the observed performance metric
- Π_opt is the optimal performance (η = 1)
- Π_deg is the degraded performance (η = 0)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Literal
import numpy as np


# Oscillator class type
OscillatorClass = Literal["P", "E", "C", "M", "A", "G", "Ca", "R"]


@dataclass
class Oscillator:
    """
    Represents a cellular oscillator with performance metrics.

    Attributes:
        osc_class: Oscillator class (P, E, C, M, A, G, Ca, R)
        pi_obs: Observed performance metric
        pi_opt: Optimal performance metric
        pi_deg: Degraded performance metric
        weight: Entropic coupling weight
        name: Optional descriptive name
    """
    osc_class: OscillatorClass
    pi_obs: float
    pi_opt: float
    pi_deg: float
    weight: float = 1.0
    name: Optional[str] = None

    def coherence(self) -> float:
        """Compute coherence index for this oscillator."""
        return coherence_index(self.pi_obs, self.pi_opt, self.pi_deg)

    def disease_index(self) -> float:
        """Compute disease index D = 1 - η."""
        return 1.0 - self.coherence()


def coherence_index(
    pi_obs: float,
    pi_opt: float,
    pi_deg: float
) -> float:
    """
    Compute the universal coherence index.

    The coherence index η is defined as:

    η = (Π_obs - Π_deg) / (Π_opt - Π_deg)    if Π_opt > Π_deg
    η = (Π_deg - Π_obs) / (Π_deg - Π_opt)    if Π_opt < Π_deg

    The result is clamped to [0, 1].

    Args:
        pi_obs: Observed performance metric
        pi_opt: Optimal performance (coherence = 1)
        pi_deg: Degraded performance (coherence = 0)

    Returns:
        Coherence index η ∈ [0, 1]

    Examples:
        >>> coherence_index(0.8, 1.0, 0.0)
        0.8
        >>> coherence_index(13, 12, 16)  # Folding cycles (fewer is better)
        0.75
    """
    if pi_opt == pi_deg:
        # Degenerate case: return 0.5 as neutral
        return 0.5

    if pi_opt > pi_deg:
        # Higher is better
        eta = (pi_obs - pi_deg) / (pi_opt - pi_deg)
    else:
        # Lower is better (e.g., folding cycles)
        eta = (pi_deg - pi_obs) / (pi_deg - pi_opt)

    # Clamp to [0, 1]
    return max(0.0, min(1.0, eta))


def cellular_coherence(
    oscillators: List[Oscillator],
    normalize_weights: bool = True
) -> float:
    """
    Compute weighted cellular coherence from oscillator ensemble.

    η_cell = (1/W) Σᵢ wᵢ ηᵢ

    where W = Σᵢ wᵢ is the total weight.

    Args:
        oscillators: List of Oscillator objects
        normalize_weights: If True, normalize weights to sum to 1

    Returns:
        Cellular coherence η_cell ∈ [0, 1]
    """
    if not oscillators:
        return 0.0

    total_weight = sum(osc.weight for osc in oscillators)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(osc.weight * osc.coherence() for osc in oscillators)

    if normalize_weights:
        return weighted_sum / total_weight
    else:
        return weighted_sum


def cellular_coherence_from_dicts(
    oscillators: List[Dict],
    normalize_weights: bool = True
) -> float:
    """
    Compute cellular coherence from list of dictionaries.

    Convenience function for working with JSON/dict data.

    Args:
        oscillators: List of dicts with keys 'pi_obs', 'pi_opt', 'pi_deg', 'weight'
        normalize_weights: If True, normalize weights

    Returns:
        Cellular coherence η_cell ∈ [0, 1]
    """
    if not oscillators:
        return 0.0

    total_weight = sum(osc.get("weight", 1.0) for osc in oscillators)
    if total_weight == 0:
        return 0.0

    weighted_sum = 0.0
    for osc in oscillators:
        eta = coherence_index(
            osc["pi_obs"],
            osc["pi_opt"],
            osc["pi_deg"]
        )
        weight = osc.get("weight", 1.0)
        weighted_sum += weight * eta

    if normalize_weights:
        return weighted_sum / total_weight
    else:
        return weighted_sum


# =============================================================================
# Class-specific coherence functions
# =============================================================================

def coherence_from_folding_cycles(
    k_obs: int,
    k_min: int = 12,
    k_max: int = 16
) -> float:
    """
    Compute coherence from protein folding cycles.

    For protein folding, fewer cycles indicates better coherence:
    η = (k_max - k_obs) / (k_max - k_min)

    Args:
        k_obs: Observed number of folding cycles
        k_min: Minimum cycles (optimal, η = 1)
        k_max: Maximum cycles (degraded, η = 0)

    Returns:
        Coherence index η ∈ [0, 1]
    """
    return coherence_index(k_obs, k_min, k_max)


def coherence_from_turnover(
    k_cat_obs: float,
    k_cat_max: float,
    k_cat_min: float = 0.0
) -> float:
    """
    Compute coherence from enzyme turnover number.

    For enzymes, higher turnover indicates better coherence:
    η = (k_cat_obs - k_cat_min) / (k_cat_max - k_cat_min)

    Args:
        k_cat_obs: Observed turnover number (s⁻¹)
        k_cat_max: Maximum turnover (optimal, η = 1)
        k_cat_min: Minimum turnover (degraded, η = 0)

    Returns:
        Coherence index η ∈ [0, 1]
    """
    return coherence_index(k_cat_obs, k_cat_max, k_cat_min)


def coherence_from_open_probability(
    p_o_obs: float,
    p_o_opt: float = 0.5,
    p_o_stuck: float = 0.0
) -> float:
    """
    Compute coherence from ion channel open probability.

    Channels have optimal open probability; deviation indicates dysfunction:
    η = 1 - |P_o_obs - P_o_opt| / |P_o_stuck - P_o_opt|

    Args:
        p_o_obs: Observed open probability
        p_o_opt: Optimal open probability
        p_o_stuck: Stuck state probability (maximally dysfunctional)

    Returns:
        Coherence index η ∈ [0, 1]
    """
    if p_o_opt == p_o_stuck:
        return 0.5

    deviation = abs(p_o_obs - p_o_opt)
    max_deviation = abs(p_o_stuck - p_o_opt)

    if max_deviation == 0:
        return 1.0 if deviation == 0 else 0.0

    return max(0.0, min(1.0, 1.0 - deviation / max_deviation))


def coherence_from_membrane_amplitude(
    delta_v_obs: float,
    delta_v_max: float = 100.0  # mV
) -> float:
    """
    Compute coherence from membrane potential oscillation amplitude.

    η = ΔV_obs / ΔV_max

    Args:
        delta_v_obs: Observed amplitude (mV)
        delta_v_max: Maximum amplitude (mV)

    Returns:
        Coherence index η ∈ [0, 1]
    """
    if delta_v_max <= 0:
        return 0.0
    return max(0.0, min(1.0, delta_v_obs / delta_v_max))


def coherence_from_frequency(
    f_obs: float,
    f_max: float,
    f_min: float = 0.0
) -> float:
    """
    Compute coherence from oscillation frequency (e.g., ATP synthesis).

    η = (f_obs - f_min) / (f_max - f_min)

    Args:
        f_obs: Observed frequency (Hz)
        f_max: Maximum frequency (optimal)
        f_min: Minimum frequency (degraded)

    Returns:
        Coherence index η ∈ [0, 1]
    """
    return coherence_index(f_obs, f_max, f_min)


def coherence_from_burst_rate(
    lambda_obs: float,
    lambda_max: float,
    lambda_min: float = 0.0
) -> float:
    """
    Compute coherence from gene expression burst rate.

    η = (λ_obs - λ_min) / (λ_max - λ_min)

    Args:
        lambda_obs: Observed burst rate (hr⁻¹)
        lambda_max: Maximum burst rate (optimal)
        lambda_min: Minimum burst rate (degraded)

    Returns:
        Coherence index η ∈ [0, 1]
    """
    return coherence_index(lambda_obs, lambda_max, lambda_min)


def coherence_from_period_stability(
    sigma_t: float,
    t_0: float = 24.0  # hours for circadian
) -> float:
    """
    Compute coherence from circadian period stability.

    η = 1 - σ_T / T_0

    Args:
        sigma_t: Period standard deviation (hours)
        t_0: Reference period (hours)

    Returns:
        Coherence index η ∈ [0, 1]
    """
    if t_0 <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - sigma_t / t_0))


# =============================================================================
# Therapeutic efficacy
# =============================================================================

def therapeutic_efficacy(
    eta_untreated: float,
    eta_treated: float,
    eta_healthy: float = 1.0
) -> float:
    """
    Compute therapeutic efficacy from coherence change.

    E = (η_treated - η_untreated) / (η_healthy - η_untreated)

    Args:
        eta_untreated: Coherence before treatment
        eta_treated: Coherence after treatment
        eta_healthy: Target healthy coherence

    Returns:
        Efficacy E ∈ [0, 1]
    """
    gap = eta_healthy - eta_untreated
    if gap <= 0:
        return 0.0 if eta_treated <= eta_untreated else 1.0

    improvement = eta_treated - eta_untreated
    return max(0.0, min(1.0, improvement / gap))


def predicted_coherence_after_treatment(
    eta_untreated: float,
    efficacy: float
) -> float:
    """
    Predict coherence after treatment with given efficacy.

    η_treated = η_untreated + E(1 - η_untreated)
             = E + (1-E)η_untreated

    Args:
        eta_untreated: Coherence before treatment
        efficacy: Treatment efficacy E ∈ [0, 1]

    Returns:
        Predicted coherence after treatment
    """
    return eta_untreated + efficacy * (1.0 - eta_untreated)

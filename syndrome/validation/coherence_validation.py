"""
Coherence Equation Validation

Validates:
- Universal coherence equation: η = (Π_obs - Π_deg) / (Π_opt - Π_deg)
- Boundary conditions (η=0 at degraded, η=1 at optimal)
- Class-specific coherence functions
- Cellular coherence aggregation
"""

from datetime import datetime
from typing import List
import numpy as np

from syndrome.core.coherence import (
    coherence_index,
    cellular_coherence,
    coherence_from_folding_cycles,
    coherence_from_turnover,
    coherence_from_open_probability,
    coherence_from_membrane_amplitude,
    coherence_from_period_stability,
    therapeutic_efficacy,
    predicted_coherence_after_treatment,
    Oscillator,
)
from syndrome.validation.types import ValidationResult


def run_coherence_validations() -> List[ValidationResult]:
    """Run all coherence equation validations."""
    results = []
    timestamp = datetime.now().isoformat()

    # Test 1: Universal coherence equation
    results.extend(_validate_universal_coherence(timestamp))

    # Test 2: Boundary conditions
    results.append(_validate_boundary_conditions(timestamp))

    # Test 3: Monotonicity
    results.append(_validate_monotonicity(timestamp))

    # Test 4: Class-specific functions
    results.extend(_validate_class_specific(timestamp))

    # Test 5: Cellular coherence aggregation
    results.append(_validate_cellular_coherence(timestamp))

    # Test 6: Therapeutic efficacy
    results.extend(_validate_therapeutic_efficacy(timestamp))

    return results


def _validate_universal_coherence(timestamp: str) -> List[ValidationResult]:
    """Validate the universal coherence equation."""
    results = []

    # Test case 1: Standard case (higher is better)
    pi_obs, pi_opt, pi_deg = 0.8, 1.0, 0.0
    expected = 0.8
    actual = coherence_index(pi_obs, pi_opt, pi_deg)

    results.append(ValidationResult(
        name="universal_coherence_standard",
        category="coherence",
        passed=abs(actual - expected) < 1e-10,
        expected=expected,
        actual=actual,
        error=abs(actual - expected),
        tolerance=1e-10,
        details={"pi_obs": pi_obs, "pi_opt": pi_opt, "pi_deg": pi_deg},
        timestamp=timestamp,
    ))

    # Test case 2: Inverse case (lower is better, e.g., folding cycles)
    k_obs, k_opt, k_deg = 13, 12, 16  # 13 cycles, optimal 12, worst 16
    expected = (16 - 13) / (16 - 12)  # = 3/4 = 0.75
    actual = coherence_index(k_obs, k_opt, k_deg)

    results.append(ValidationResult(
        name="universal_coherence_inverse",
        category="coherence",
        passed=abs(actual - expected) < 1e-10,
        expected=expected,
        actual=actual,
        error=abs(actual - expected),
        tolerance=1e-10,
        details={
            "k_obs": k_obs,
            "k_opt": k_opt,
            "k_deg": k_deg,
            "interpretation": "Lower is better (folding cycles)",
        },
        timestamp=timestamp,
    ))

    # Test case 3: Midpoint
    pi_obs, pi_opt, pi_deg = 0.5, 1.0, 0.0
    expected = 0.5
    actual = coherence_index(pi_obs, pi_opt, pi_deg)

    results.append(ValidationResult(
        name="universal_coherence_midpoint",
        category="coherence",
        passed=abs(actual - expected) < 1e-10,
        expected=expected,
        actual=actual,
        error=abs(actual - expected),
        tolerance=1e-10,
        details={"pi_obs": pi_obs, "pi_opt": pi_opt, "pi_deg": pi_deg},
        timestamp=timestamp,
    ))

    return results


def _validate_boundary_conditions(timestamp: str) -> ValidationResult:
    """Validate boundary conditions: η=1 at optimal, η=0 at degraded."""
    test_cases = []
    all_passed = True

    # At optimal
    eta_at_opt = coherence_index(1.0, 1.0, 0.0)
    test_cases.append(("optimal", eta_at_opt, 1.0))
    if abs(eta_at_opt - 1.0) > 1e-10:
        all_passed = False

    # At degraded
    eta_at_deg = coherence_index(0.0, 1.0, 0.0)
    test_cases.append(("degraded", eta_at_deg, 0.0))
    if abs(eta_at_deg - 0.0) > 1e-10:
        all_passed = False

    # Inverse case at optimal
    eta_inv_opt = coherence_index(12, 12, 16)  # k_obs = k_opt
    test_cases.append(("inverse_optimal", eta_inv_opt, 1.0))
    if abs(eta_inv_opt - 1.0) > 1e-10:
        all_passed = False

    # Inverse case at degraded
    eta_inv_deg = coherence_index(16, 12, 16)  # k_obs = k_deg
    test_cases.append(("inverse_degraded", eta_inv_deg, 0.0))
    if abs(eta_inv_deg - 0.0) > 1e-10:
        all_passed = False

    return ValidationResult(
        name="coherence_boundary_conditions",
        category="coherence",
        passed=all_passed,
        expected="η=1 at optimal, η=0 at degraded",
        actual=test_cases,
        error=0.0 if all_passed else 1.0,
        tolerance=1e-10,
        details={"test_cases": test_cases},
        timestamp=timestamp,
    )


def _validate_monotonicity(timestamp: str) -> ValidationResult:
    """Validate that coherence is monotonic in performance."""
    # For standard case (higher is better)
    pi_values = np.linspace(0, 1, 11)
    coherences = [coherence_index(p, 1.0, 0.0) for p in pi_values]

    # Check monotonicity
    diffs = np.diff(coherences)
    is_monotonic = np.all(diffs >= -1e-10)

    return ValidationResult(
        name="coherence_monotonicity",
        category="coherence",
        passed=is_monotonic,
        expected="Coherence increases monotonically with performance",
        actual=f"All differences >= 0: {is_monotonic}",
        error=0.0 if is_monotonic else float(-np.min(diffs)),
        tolerance=1e-10,
        details={
            "pi_values": pi_values.tolist(),
            "coherences": coherences,
            "differences": diffs.tolist(),
        },
        timestamp=timestamp,
    )


def _validate_class_specific(timestamp: str) -> List[ValidationResult]:
    """Validate class-specific coherence functions."""
    results = []

    # Protein folding (Class P)
    eta_fold = coherence_from_folding_cycles(13, k_min=12, k_max=16)
    expected_fold = 0.75  # (16-13)/(16-12)

    results.append(ValidationResult(
        name="protein_folding_coherence",
        category="coherence",
        passed=abs(eta_fold - expected_fold) < 1e-10,
        expected=expected_fold,
        actual=eta_fold,
        error=abs(eta_fold - expected_fold),
        tolerance=1e-10,
        details={
            "k_obs": 13,
            "k_min": 12,
            "k_max": 16,
            "interpretation": "75% coherence at 13 cycles",
        },
        timestamp=timestamp,
    ))

    # Enzyme turnover (Class E)
    eta_enzyme = coherence_from_turnover(1e5, k_cat_max=1e6, k_cat_min=0)
    expected_enzyme = 0.1  # 1e5 / 1e6

    results.append(ValidationResult(
        name="enzyme_turnover_coherence",
        category="coherence",
        passed=abs(eta_enzyme - expected_enzyme) < 1e-10,
        expected=expected_enzyme,
        actual=eta_enzyme,
        error=abs(eta_enzyme - expected_enzyme),
        tolerance=1e-10,
        details={
            "k_cat_obs": 1e5,
            "k_cat_max": 1e6,
            "interpretation": "10% of maximum turnover",
        },
        timestamp=timestamp,
    ))

    # Channel open probability (Class C)
    eta_channel = coherence_from_open_probability(0.5, p_o_opt=0.5, p_o_stuck=0.0)
    expected_channel = 1.0  # At optimal

    results.append(ValidationResult(
        name="channel_open_probability_coherence",
        category="coherence",
        passed=abs(eta_channel - expected_channel) < 1e-10,
        expected=expected_channel,
        actual=eta_channel,
        error=abs(eta_channel - expected_channel),
        tolerance=1e-10,
        details={
            "p_o_obs": 0.5,
            "p_o_opt": 0.5,
            "interpretation": "At optimal open probability",
        },
        timestamp=timestamp,
    ))

    # Membrane amplitude (Class M)
    eta_membrane = coherence_from_membrane_amplitude(80.0, delta_v_max=100.0)
    expected_membrane = 0.8

    results.append(ValidationResult(
        name="membrane_amplitude_coherence",
        category="coherence",
        passed=abs(eta_membrane - expected_membrane) < 1e-10,
        expected=expected_membrane,
        actual=eta_membrane,
        error=abs(eta_membrane - expected_membrane),
        tolerance=1e-10,
        details={
            "delta_v_obs": 80.0,
            "delta_v_max": 100.0,
        },
        timestamp=timestamp,
    ))

    # Circadian period stability (Class R)
    eta_circadian = coherence_from_period_stability(sigma_t=2.4, t_0=24.0)
    expected_circadian = 0.9  # 1 - 2.4/24

    results.append(ValidationResult(
        name="circadian_period_coherence",
        category="coherence",
        passed=abs(eta_circadian - expected_circadian) < 1e-10,
        expected=expected_circadian,
        actual=eta_circadian,
        error=abs(eta_circadian - expected_circadian),
        tolerance=1e-10,
        details={
            "sigma_t": 2.4,
            "t_0": 24.0,
            "interpretation": "10% period variation",
        },
        timestamp=timestamp,
    ))

    return results


def _validate_cellular_coherence(timestamp: str) -> ValidationResult:
    """Validate weighted cellular coherence aggregation."""
    # Create test oscillators
    oscillators = [
        Oscillator(osc_class="P", pi_obs=13, pi_opt=12, pi_deg=16, weight=1.0),  # η=0.75
        Oscillator(osc_class="E", pi_obs=5e5, pi_opt=1e6, pi_deg=0, weight=2.0),  # η=0.5
        Oscillator(osc_class="M", pi_obs=80, pi_opt=100, pi_deg=0, weight=1.0),   # η=0.8
    ]

    # Expected: (1*0.75 + 2*0.5 + 1*0.8) / (1+2+1) = 2.55/4 = 0.6375
    expected = (1*0.75 + 2*0.5 + 1*0.8) / 4
    actual = cellular_coherence(oscillators)

    return ValidationResult(
        name="cellular_coherence_weighted",
        category="coherence",
        passed=abs(actual - expected) < 1e-10,
        expected=expected,
        actual=actual,
        error=abs(actual - expected),
        tolerance=1e-10,
        details={
            "oscillator_coherences": [osc.coherence() for osc in oscillators],
            "weights": [osc.weight for osc in oscillators],
            "formula": "η_cell = Σ(w_i * η_i) / Σ(w_i)",
        },
        timestamp=timestamp,
    )


def _validate_therapeutic_efficacy(timestamp: str) -> List[ValidationResult]:
    """Validate therapeutic efficacy computation."""
    results = []

    # Test efficacy calculation
    eta_untreated = 0.4
    eta_treated = 0.7
    eta_healthy = 1.0

    # E = (0.7 - 0.4) / (1.0 - 0.4) = 0.3 / 0.6 = 0.5
    expected_efficacy = 0.5
    actual_efficacy = therapeutic_efficacy(eta_untreated, eta_treated, eta_healthy)

    results.append(ValidationResult(
        name="therapeutic_efficacy_calculation",
        category="coherence",
        passed=abs(actual_efficacy - expected_efficacy) < 1e-10,
        expected=expected_efficacy,
        actual=actual_efficacy,
        error=abs(actual_efficacy - expected_efficacy),
        tolerance=1e-10,
        details={
            "eta_untreated": eta_untreated,
            "eta_treated": eta_treated,
            "eta_healthy": eta_healthy,
            "interpretation": "50% of coherence gap closed",
        },
        timestamp=timestamp,
    ))

    # Test predicted coherence after treatment
    eta_untreated = 0.3
    efficacy = 0.5
    # η_treated = 0.3 + 0.5*(1 - 0.3) = 0.3 + 0.35 = 0.65
    expected_predicted = 0.65
    actual_predicted = predicted_coherence_after_treatment(eta_untreated, efficacy)

    results.append(ValidationResult(
        name="predicted_coherence_after_treatment",
        category="coherence",
        passed=abs(actual_predicted - expected_predicted) < 1e-10,
        expected=expected_predicted,
        actual=actual_predicted,
        error=abs(actual_predicted - expected_predicted),
        tolerance=1e-10,
        details={
            "eta_untreated": eta_untreated,
            "efficacy": efficacy,
            "formula": "η_treated = η_untreated + E(1 - η_untreated)",
        },
        timestamp=timestamp,
    ))

    # Verify consistency: efficacy from predicted should match original
    recovered_efficacy = therapeutic_efficacy(eta_untreated, actual_predicted, 1.0)

    results.append(ValidationResult(
        name="efficacy_prediction_consistency",
        category="coherence",
        passed=abs(recovered_efficacy - efficacy) < 1e-10,
        expected=efficacy,
        actual=recovered_efficacy,
        error=abs(recovered_efficacy - efficacy),
        tolerance=1e-10,
        details={
            "interpretation": "Efficacy recovered from predicted coherence matches original",
        },
        timestamp=timestamp,
    ))

    return results

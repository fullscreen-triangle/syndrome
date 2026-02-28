"""
Disease State Validation

Validates:
- Disease vector computation from oscillator ensembles
- Disease classification by dominant component
- Disease severity computation
- Disease vector metric properties
- Disease signature distance
"""

from datetime import datetime
from typing import List
import numpy as np

from syndrome.core.coherence import Oscillator
from syndrome.core.disease import (
    DiseaseVector,
    disease_vector,
    classify_disease,
    disease_severity,
    disease_signature_distance,
    healthy_vector,
    generate_disease_profile,
    OSCILLATOR_CLASSES,
    DISEASE_CLASS_NAMES,
)
from syndrome.validation.types import ValidationResult


def run_disease_validations() -> List[ValidationResult]:
    """Run all disease state validations."""
    results = []
    timestamp = datetime.now().isoformat()

    # Test 1: Disease vector from coherences
    results.extend(_validate_disease_vector_computation(timestamp))

    # Test 2: Disease classification
    results.extend(_validate_classification(timestamp))

    # Test 3: Disease severity
    results.extend(_validate_severity(timestamp))

    # Test 4: Healthy vector properties
    results.append(_validate_healthy_vector(timestamp))

    # Test 5: Disease vector bounds
    results.append(_validate_disease_bounds(timestamp))

    # Test 6: Disease signature distance
    results.extend(_validate_signature_distance(timestamp))

    # Test 7: Disease profile generation
    results.append(_validate_profile_generation(timestamp))

    return results


def _validate_disease_vector_computation(timestamp: str) -> List[ValidationResult]:
    """Validate disease vector computation from oscillator ensembles."""
    results = []

    # Test case 1: Single oscillator per class
    oscillators = [
        Oscillator(osc_class="P", pi_obs=13, pi_opt=12, pi_deg=16, weight=1.0),  # η=0.75 → D=0.25
        Oscillator(osc_class="E", pi_obs=5e5, pi_opt=1e6, pi_deg=0, weight=1.0),  # η=0.5 → D=0.5
        Oscillator(osc_class="C", pi_obs=0.3, pi_opt=0.5, pi_deg=0, weight=1.0),  # η=0.6 → D=0.4
        Oscillator(osc_class="M", pi_obs=80, pi_opt=100, pi_deg=0, weight=1.0),   # η=0.8 → D=0.2
    ]

    D = disease_vector(oscillators)

    # Expected values
    expected_D_P = 0.25  # 1 - 0.75
    expected_D_E = 0.5   # 1 - 0.5
    expected_D_C = 0.4   # 1 - 0.6
    expected_D_M = 0.2   # 1 - 0.8

    results.append(ValidationResult(
        name="disease_vector_protein_class",
        category="disease",
        passed=abs(D.D_P - expected_D_P) < 1e-10,
        expected=expected_D_P,
        actual=D.D_P,
        error=abs(D.D_P - expected_D_P),
        tolerance=1e-10,
        details={"oscillator": "P", "coherence": 0.75},
        timestamp=timestamp,
    ))

    results.append(ValidationResult(
        name="disease_vector_enzyme_class",
        category="disease",
        passed=abs(D.D_E - expected_D_E) < 1e-10,
        expected=expected_D_E,
        actual=D.D_E,
        error=abs(D.D_E - expected_D_E),
        tolerance=1e-10,
        details={"oscillator": "E", "coherence": 0.5},
        timestamp=timestamp,
    ))

    # Test case 2: Weighted aggregation within class
    oscillators_weighted = [
        Oscillator(osc_class="P", pi_obs=0.6, pi_opt=1.0, pi_deg=0, weight=2.0),  # η=0.6
        Oscillator(osc_class="P", pi_obs=0.8, pi_opt=1.0, pi_deg=0, weight=1.0),  # η=0.8
    ]
    D_weighted = disease_vector(oscillators_weighted)

    # Expected: weighted η = (2*0.6 + 1*0.8)/3 = 2.0/3 ≈ 0.6667
    # D_P = 1 - 2/3 = 1/3 ≈ 0.3333
    expected_weighted = 1.0 - (2 * 0.6 + 1 * 0.8) / 3

    results.append(ValidationResult(
        name="disease_vector_weighted_aggregation",
        category="disease",
        passed=abs(D_weighted.D_P - expected_weighted) < 1e-10,
        expected=expected_weighted,
        actual=D_weighted.D_P,
        error=abs(D_weighted.D_P - expected_weighted),
        tolerance=1e-10,
        details={
            "weights": [2.0, 1.0],
            "coherences": [0.6, 0.8],
            "interpretation": "Weighted average of coherences",
        },
        timestamp=timestamp,
    ))

    return results


def _validate_classification(timestamp: str) -> List[ValidationResult]:
    """Validate disease classification by dominant component."""
    results = []

    # Test each class as dominant
    for dominant_class in OSCILLATOR_CLASSES:
        # Create disease vector with this class dominant
        indices = {f"D_{c}": 0.1 for c in OSCILLATOR_CLASSES}
        indices[f"D_{dominant_class}"] = 0.9  # Make this class dominant

        D = DiseaseVector(**indices)
        classified = classify_disease(D)

        results.append(ValidationResult(
            name=f"classification_dominant_{dominant_class}",
            category="disease",
            passed=classified == dominant_class,
            expected=dominant_class,
            actual=classified,
            error=0.0 if classified == dominant_class else 1.0,
            tolerance=0.0,
            details={
                "dominant_value": 0.9,
                "background_value": 0.1,
                "class_name": DISEASE_CLASS_NAMES[dominant_class],
            },
            timestamp=timestamp,
        ))

    return results


def _validate_severity(timestamp: str) -> List[ValidationResult]:
    """Validate disease severity computation."""
    results = []

    # Test case 1: Uniform severity
    D_uniform = DiseaseVector(
        D_P=0.5, D_E=0.5, D_C=0.5, D_M=0.5,
        D_A=0.5, D_G=0.5, D_Ca=0.5, D_R=0.5
    )
    expected_uniform = 0.5
    actual_uniform = disease_severity(D_uniform)

    results.append(ValidationResult(
        name="severity_uniform",
        category="disease",
        passed=abs(actual_uniform - expected_uniform) < 1e-10,
        expected=expected_uniform,
        actual=actual_uniform,
        error=abs(actual_uniform - expected_uniform),
        tolerance=1e-10,
        details={"interpretation": "All classes at 50% disease index"},
        timestamp=timestamp,
    ))

    # Test case 2: Weighted severity
    D_test = DiseaseVector(
        D_P=1.0, D_E=0.0, D_C=0.0, D_M=0.0,
        D_A=0.0, D_G=0.0, D_Ca=0.0, D_R=0.0
    )
    weights = np.array([8.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])  # Heavy weight on P
    expected_weighted = 8.0 / 15.0  # 8*1.0 / sum(weights)
    actual_weighted = disease_severity(D_test, weights)

    results.append(ValidationResult(
        name="severity_weighted",
        category="disease",
        passed=abs(actual_weighted - expected_weighted) < 1e-10,
        expected=expected_weighted,
        actual=actual_weighted,
        error=abs(actual_weighted - expected_weighted),
        tolerance=1e-10,
        details={"weights": weights.tolist()},
        timestamp=timestamp,
    ))

    # Test case 3: Healthy has zero severity
    D_healthy = healthy_vector()
    expected_healthy = 0.0
    actual_healthy = disease_severity(D_healthy)

    results.append(ValidationResult(
        name="severity_healthy_zero",
        category="disease",
        passed=abs(actual_healthy - expected_healthy) < 1e-10,
        expected=expected_healthy,
        actual=actual_healthy,
        error=abs(actual_healthy - expected_healthy),
        tolerance=1e-10,
        details={"interpretation": "Healthy state has zero severity"},
        timestamp=timestamp,
    ))

    return results


def _validate_healthy_vector(timestamp: str) -> ValidationResult:
    """Validate healthy vector properties."""
    D_healthy = healthy_vector()
    arr = D_healthy.to_array()

    all_zero = np.allclose(arr, 0.0)

    return ValidationResult(
        name="healthy_vector_all_zeros",
        category="disease",
        passed=all_zero,
        expected="All disease indices = 0",
        actual=arr.tolist(),
        error=float(np.sum(np.abs(arr))),
        tolerance=1e-10,
        details={"interpretation": "Healthy = full coherence = zero disease"},
        timestamp=timestamp,
    )


def _validate_disease_bounds(timestamp: str) -> ValidationResult:
    """Validate disease vector bounds in [0, 1]."""
    test_cases = []
    all_passed = True

    # Test boundary values
    for val in [0.0, 0.5, 1.0]:
        try:
            D = DiseaseVector(
                D_P=val, D_E=val, D_C=val, D_M=val,
                D_A=val, D_G=val, D_Ca=val, D_R=val
            )
            test_cases.append((val, "valid", True))
        except ValueError:
            test_cases.append((val, "valid", False))
            all_passed = False

    # Test invalid values should raise
    for val in [-0.1, 1.1]:
        try:
            D = DiseaseVector(
                D_P=val, D_E=0.5, D_C=0.5, D_M=0.5,
                D_A=0.5, D_G=0.5, D_Ca=0.5, D_R=0.5
            )
            test_cases.append((val, "invalid_accepted", False))
            all_passed = False
        except ValueError:
            test_cases.append((val, "correctly_rejected", True))

    return ValidationResult(
        name="disease_vector_bounds",
        category="disease",
        passed=all_passed,
        expected="D_i in [0, 1] for all i",
        actual=test_cases,
        error=0.0 if all_passed else 1.0,
        tolerance=0.0,
        details={"test_cases": test_cases},
        timestamp=timestamp,
    )


def _validate_signature_distance(timestamp: str) -> List[ValidationResult]:
    """Validate disease signature distance properties."""
    results = []

    # Test case 1: Distance to self is zero
    D1 = DiseaseVector(
        D_P=0.3, D_E=0.4, D_C=0.2, D_M=0.5,
        D_A=0.1, D_G=0.6, D_Ca=0.3, D_R=0.2
    )
    self_distance = disease_signature_distance(D1, D1)

    results.append(ValidationResult(
        name="signature_distance_self_zero",
        category="disease",
        passed=abs(self_distance) < 1e-10,
        expected=0.0,
        actual=self_distance,
        error=abs(self_distance),
        tolerance=1e-10,
        details={"interpretation": "Distance to self is zero"},
        timestamp=timestamp,
    ))

    # Test case 2: Symmetry
    D2 = DiseaseVector(
        D_P=0.5, D_E=0.3, D_C=0.4, D_M=0.2,
        D_A=0.6, D_G=0.1, D_Ca=0.5, D_R=0.3
    )
    d12 = disease_signature_distance(D1, D2)
    d21 = disease_signature_distance(D2, D1)

    results.append(ValidationResult(
        name="signature_distance_symmetry",
        category="disease",
        passed=abs(d12 - d21) < 1e-10,
        expected="d(D1, D2) = d(D2, D1)",
        actual={"d12": d12, "d21": d21},
        error=abs(d12 - d21),
        tolerance=1e-10,
        details={"interpretation": "Distance is symmetric"},
        timestamp=timestamp,
    ))

    # Test case 3: Triangle inequality
    D3 = DiseaseVector(
        D_P=0.7, D_E=0.2, D_C=0.5, D_M=0.3,
        D_A=0.4, D_G=0.3, D_Ca=0.6, D_R=0.1
    )
    d13 = disease_signature_distance(D1, D3)
    d23 = disease_signature_distance(D2, D3)

    triangle_satisfied = d13 <= d12 + d23 + 1e-10

    results.append(ValidationResult(
        name="signature_distance_triangle",
        category="disease",
        passed=triangle_satisfied,
        expected="d(D1, D3) <= d(D1, D2) + d(D2, D3)",
        actual={"d13": d13, "d12": d12, "d23": d23, "sum": d12 + d23},
        error=max(0, d13 - (d12 + d23)),
        tolerance=1e-10,
        details={"interpretation": "Triangle inequality holds"},
        timestamp=timestamp,
    ))

    return results


def _validate_profile_generation(timestamp: str) -> ValidationResult:
    """Validate synthetic disease profile generation."""
    test_cases = []
    all_passed = True

    for dominant_class in OSCILLATOR_CLASSES:
        severity = 0.8
        spread = 0.1

        # Set seed for reproducibility
        np.random.seed(42)
        profile = generate_disease_profile(dominant_class, severity, spread)

        # Check dominant class has specified severity
        dominant_val = getattr(profile, f"D_{dominant_class}")
        if abs(dominant_val - severity) > 1e-10:
            all_passed = False

        # Check classification matches
        classified = classify_disease(profile)
        if classified != dominant_class:
            all_passed = False

        test_cases.append({
            "class": dominant_class,
            "dominant_value": dominant_val,
            "classified_as": classified,
            "match": classified == dominant_class,
        })

    return ValidationResult(
        name="disease_profile_generation",
        category="disease",
        passed=all_passed,
        expected="Generated profiles classify to intended dominant class",
        actual=test_cases,
        error=0.0 if all_passed else 1.0,
        tolerance=1e-10,
        details={"severity": 0.8, "spread": 0.1},
        timestamp=timestamp,
    )

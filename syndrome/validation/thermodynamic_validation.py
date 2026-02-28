"""
Thermodynamic Validation

Validates:
- S-entropy space bounds and properties
- Entropy calculation from distributions
- S-entropy distance metric properties
- Entropy normalization
- Entropy estimation from trajectories
- Connection between partition capacity and thermodynamics
"""

from datetime import datetime
from typing import List
import numpy as np

from syndrome.core.s_entropy import (
    SEntropyPoint,
    s_entropy_distance,
    normalize_s_entropy,
    interpolate_s_entropy,
    s_entropy_from_distribution,
    estimate_s_entropy_from_trajectory,
)
from syndrome.core.partition import partition_capacity
from syndrome.validation.types import ValidationResult


def run_thermodynamic_validations() -> List[ValidationResult]:
    """Run all thermodynamic validations."""
    results = []
    timestamp = datetime.now().isoformat()

    # Test 1: S-entropy bounds
    results.append(_validate_s_entropy_bounds(timestamp))

    # Test 2: S-entropy distance metric
    results.extend(_validate_s_entropy_metric(timestamp))

    # Test 3: Entropy from distribution
    results.extend(_validate_entropy_from_distribution(timestamp))

    # Test 4: S-entropy normalization
    results.append(_validate_normalization(timestamp))

    # Test 5: S-entropy interpolation
    results.append(_validate_interpolation(timestamp))

    # Test 6: Entropy estimation from trajectory
    results.append(_validate_entropy_estimation(timestamp))

    # Test 7: Partition capacity thermodynamic connection
    results.append(_validate_partition_thermodynamics(timestamp))

    # Test 8: Total and mean entropy
    results.append(_validate_entropy_aggregations(timestamp))

    return results


def _validate_s_entropy_bounds(timestamp: str) -> ValidationResult:
    """Validate S-entropy coordinates are bounded in [0, 1]."""
    test_cases = []
    all_passed = True

    # Valid boundary values
    for s_k, s_t, s_e in [(0, 0, 0), (1, 1, 1), (0.5, 0.5, 0.5), (0, 0.5, 1)]:
        try:
            point = SEntropyPoint(s_k=s_k, s_t=s_t, s_e=s_e)
            test_cases.append({
                "coords": (s_k, s_t, s_e),
                "status": "valid",
                "passed": True,
            })
        except ValueError:
            test_cases.append({
                "coords": (s_k, s_t, s_e),
                "status": "should_be_valid",
                "passed": False,
            })
            all_passed = False

    # Invalid values (should raise)
    for s_k, s_t, s_e in [(-0.1, 0.5, 0.5), (0.5, 1.1, 0.5), (0.5, 0.5, -0.5)]:
        try:
            point = SEntropyPoint(s_k=s_k, s_t=s_t, s_e=s_e)
            test_cases.append({
                "coords": (s_k, s_t, s_e),
                "status": "invalid_accepted",
                "passed": False,
            })
            all_passed = False
        except ValueError:
            test_cases.append({
                "coords": (s_k, s_t, s_e),
                "status": "correctly_rejected",
                "passed": True,
            })

    return ValidationResult(
        name="s_entropy_bounds",
        category="thermodynamic",
        passed=all_passed,
        expected="S_k, S_t, S_e in [0, 1]",
        actual=test_cases,
        error=0.0 if all_passed else 1.0,
        tolerance=0.0,
        details={"interpretation": "S-entropy space is unit cube [0,1]^3"},
        timestamp=timestamp,
    )


def _validate_s_entropy_metric(timestamp: str) -> List[ValidationResult]:
    """Validate S-entropy distance satisfies metric properties."""
    results = []

    p1 = SEntropyPoint(s_k=0.2, s_t=0.3, s_e=0.4)
    p2 = SEntropyPoint(s_k=0.5, s_t=0.6, s_e=0.7)
    p3 = SEntropyPoint(s_k=0.8, s_t=0.4, s_e=0.2)

    # Non-negativity
    d12 = s_entropy_distance(p1, p2)
    non_negative = d12 >= 0

    results.append(ValidationResult(
        name="s_entropy_distance_non_negative",
        category="thermodynamic",
        passed=non_negative,
        expected="d >= 0",
        actual=d12,
        error=0.0 if non_negative else abs(d12),
        tolerance=0.0,
        details={},
        timestamp=timestamp,
    ))

    # Identity of indiscernibles
    d11 = s_entropy_distance(p1, p1)
    identity = abs(d11) < 1e-10

    results.append(ValidationResult(
        name="s_entropy_distance_identity",
        category="thermodynamic",
        passed=identity,
        expected=0.0,
        actual=d11,
        error=abs(d11),
        tolerance=1e-10,
        details={"interpretation": "d(p, p) = 0"},
        timestamp=timestamp,
    ))

    # Symmetry
    d21 = s_entropy_distance(p2, p1)
    symmetric = abs(d12 - d21) < 1e-10

    results.append(ValidationResult(
        name="s_entropy_distance_symmetry",
        category="thermodynamic",
        passed=symmetric,
        expected="d(p1, p2) = d(p2, p1)",
        actual={"d12": d12, "d21": d21},
        error=abs(d12 - d21),
        tolerance=1e-10,
        details={},
        timestamp=timestamp,
    ))

    # Triangle inequality
    d13 = s_entropy_distance(p1, p3)
    d23 = s_entropy_distance(p2, p3)
    triangle = d13 <= d12 + d23 + 1e-10

    results.append(ValidationResult(
        name="s_entropy_distance_triangle",
        category="thermodynamic",
        passed=triangle,
        expected="d(p1, p3) <= d(p1, p2) + d(p2, p3)",
        actual={"d13": d13, "d12": d12, "d23": d23, "sum": d12 + d23},
        error=max(0, d13 - (d12 + d23)),
        tolerance=1e-10,
        details={},
        timestamp=timestamp,
    ))

    return results


def _validate_entropy_from_distribution(timestamp: str) -> List[ValidationResult]:
    """Validate Shannon entropy calculation from distributions."""
    results = []

    # Test case 1: Uniform distribution → maximum entropy
    n = 10
    uniform = np.ones(n) / n
    expected_uniform = 1.0  # Normalized to max entropy
    actual_uniform = s_entropy_from_distribution(uniform)

    results.append(ValidationResult(
        name="entropy_uniform_distribution",
        category="thermodynamic",
        passed=abs(actual_uniform - expected_uniform) < 1e-10,
        expected=expected_uniform,
        actual=actual_uniform,
        error=abs(actual_uniform - expected_uniform),
        tolerance=1e-10,
        details={"n": n, "interpretation": "Uniform → max entropy"},
        timestamp=timestamp,
    ))

    # Test case 2: Delta distribution → zero entropy
    delta = np.zeros(n)
    delta[0] = 1.0
    expected_delta = 0.0
    actual_delta = s_entropy_from_distribution(delta)

    results.append(ValidationResult(
        name="entropy_delta_distribution",
        category="thermodynamic",
        passed=abs(actual_delta - expected_delta) < 1e-10,
        expected=expected_delta,
        actual=actual_delta,
        error=abs(actual_delta - expected_delta),
        tolerance=1e-10,
        details={"interpretation": "Single certain outcome → zero entropy"},
        timestamp=timestamp,
    ))

    # Test case 3: Binary distribution
    binary = np.array([0.5, 0.5])
    expected_binary = 1.0  # Max entropy for 2 outcomes
    actual_binary = s_entropy_from_distribution(binary)

    results.append(ValidationResult(
        name="entropy_binary_distribution",
        category="thermodynamic",
        passed=abs(actual_binary - expected_binary) < 1e-10,
        expected=expected_binary,
        actual=actual_binary,
        error=abs(actual_binary - expected_binary),
        tolerance=1e-10,
        details={"interpretation": "Fair coin → max binary entropy"},
        timestamp=timestamp,
    ))

    # Test case 4: Intermediate entropy
    # p = [0.9, 0.1] should have entropy between 0 and 1
    skewed = np.array([0.9, 0.1])
    actual_skewed = s_entropy_from_distribution(skewed)
    entropy_in_range = 0 < actual_skewed < 1

    results.append(ValidationResult(
        name="entropy_intermediate",
        category="thermodynamic",
        passed=entropy_in_range,
        expected="0 < S < 1",
        actual=actual_skewed,
        error=0.0 if entropy_in_range else 1.0,
        tolerance=0.0,
        details={"distribution": skewed.tolist()},
        timestamp=timestamp,
    ))

    return results


def _validate_normalization(timestamp: str) -> ValidationResult:
    """Validate S-entropy normalization."""
    # Raw values outside [0, 1]
    raw_values = (50.0, 100.0, 75.0)
    bounds = ((0.0, 100.0), (0.0, 200.0), (50.0, 100.0))

    normalized = normalize_s_entropy(raw_values, bounds)

    # Expected: (50/100, 100/200, (75-50)/50) = (0.5, 0.5, 0.5)
    expected = (0.5, 0.5, 0.5)

    match = (
        abs(normalized.s_k - expected[0]) < 1e-10 and
        abs(normalized.s_t - expected[1]) < 1e-10 and
        abs(normalized.s_e - expected[2]) < 1e-10
    )

    return ValidationResult(
        name="s_entropy_normalization",
        category="thermodynamic",
        passed=match,
        expected=expected,
        actual=normalized.to_tuple(),
        error=np.linalg.norm(
            np.array(normalized.to_tuple()) - np.array(expected)
        ),
        tolerance=1e-10,
        details={
            "raw_values": raw_values,
            "bounds": bounds,
        },
        timestamp=timestamp,
    )


def _validate_interpolation(timestamp: str) -> ValidationResult:
    """Validate S-entropy linear interpolation."""
    p1 = SEntropyPoint(s_k=0.0, s_t=0.0, s_e=0.0)
    p2 = SEntropyPoint(s_k=1.0, s_t=1.0, s_e=1.0)

    test_cases = []
    all_passed = True

    # Test various t values
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        interpolated = interpolate_s_entropy(p1, p2, t)
        expected = (t, t, t)

        match = (
            abs(interpolated.s_k - expected[0]) < 1e-10 and
            abs(interpolated.s_t - expected[1]) < 1e-10 and
            abs(interpolated.s_e - expected[2]) < 1e-10
        )

        if not match:
            all_passed = False

        test_cases.append({
            "t": t,
            "expected": expected,
            "actual": interpolated.to_tuple(),
            "passed": match,
        })

    return ValidationResult(
        name="s_entropy_interpolation",
        category="thermodynamic",
        passed=all_passed,
        expected="Linear interpolation: p(t) = (1-t)*p1 + t*p2",
        actual=test_cases,
        error=0.0 if all_passed else 1.0,
        tolerance=1e-10,
        details={
            "p1": p1.to_tuple(),
            "p2": p2.to_tuple(),
        },
        timestamp=timestamp,
    )


def _validate_entropy_estimation(timestamp: str) -> ValidationResult:
    """Validate S-entropy estimation from trajectory."""
    # Create a simple ordered trajectory (low entropy)
    n_points = 100
    t = np.linspace(0, 1, n_points)
    trajectory_ordered = np.column_stack([t, t, t])

    s_ordered = estimate_s_entropy_from_trajectory(trajectory_ordered)

    # Create a random trajectory (high entropy)
    np.random.seed(42)
    trajectory_random = np.random.rand(n_points, 3)

    s_random = estimate_s_entropy_from_trajectory(trajectory_random)

    # Ordered trajectory should have lower entropy than random
    s_ordered_total = s_ordered.total_entropy()
    s_random_total = s_random.total_entropy()

    ordered_lower = s_ordered_total < s_random_total

    return ValidationResult(
        name="entropy_estimation_ordering",
        category="thermodynamic",
        passed=ordered_lower,
        expected="Ordered trajectory has lower entropy than random",
        actual={
            "ordered_entropy": s_ordered_total,
            "random_entropy": s_random_total,
        },
        error=0.0 if ordered_lower else (s_ordered_total - s_random_total),
        tolerance=0.0,
        details={
            "ordered_components": s_ordered.to_tuple(),
            "random_components": s_random.to_tuple(),
        },
        timestamp=timestamp,
    )


def _validate_partition_thermodynamics(timestamp: str) -> ValidationResult:
    """Validate thermodynamic connection: S = kB M ln(n)."""
    # The partition capacity C(n) = 2n^2 connects to thermodynamics through
    # S = kB * M * ln(n) where M is the multiplicity (number of states)

    # For n levels, multiplicity grows as 2n^2
    # This gives entropy S proportional to ln(2n^2) = ln(2) + 2*ln(n)

    test_cases = []
    all_passed = True

    for n in range(1, 8):
        capacity = partition_capacity(n)
        expected_capacity = 2 * n * n

        if capacity != expected_capacity:
            all_passed = False

        # Entropy proxy: ln(capacity)
        entropy_proxy = np.log(capacity) if capacity > 0 else 0

        test_cases.append({
            "n": n,
            "capacity": capacity,
            "expected": expected_capacity,
            "entropy_proxy": entropy_proxy,
            "match": capacity == expected_capacity,
        })

    # Verify entropy increases with n (thermodynamic consistency)
    entropies = [np.log(partition_capacity(n)) for n in range(1, 8)]
    entropy_increasing = all(
        entropies[i] < entropies[i+1] for i in range(len(entropies)-1)
    )

    if not entropy_increasing:
        all_passed = False

    return ValidationResult(
        name="partition_thermodynamic_connection",
        category="thermodynamic",
        passed=all_passed,
        expected="C(n) = 2n^2, entropy increases with n",
        actual={
            "test_cases": test_cases,
            "entropy_increasing": entropy_increasing,
        },
        error=0.0 if all_passed else 1.0,
        tolerance=0.0,
        details={
            "formula": "S = kB * M * ln(n), where M = C(n) = 2n^2",
            "interpretation": "Partition geometry encodes thermodynamic states",
        },
        timestamp=timestamp,
    )


def _validate_entropy_aggregations(timestamp: str) -> ValidationResult:
    """Validate total and mean entropy computations."""
    test_cases = []
    all_passed = True

    # Test several points
    points = [
        SEntropyPoint(s_k=0.3, s_t=0.4, s_e=0.5),
        SEntropyPoint(s_k=0.0, s_t=0.0, s_e=0.0),
        SEntropyPoint(s_k=1.0, s_t=1.0, s_e=1.0),
        SEntropyPoint(s_k=0.5, s_t=0.5, s_e=0.5),
    ]

    for p in points:
        arr = p.to_array()

        # Total entropy (Euclidean norm)
        expected_total = np.linalg.norm(arr)
        actual_total = p.total_entropy()
        total_match = abs(actual_total - expected_total) < 1e-10

        # Mean entropy
        expected_mean = np.mean(arr)
        actual_mean = p.mean_entropy()
        mean_match = abs(actual_mean - expected_mean) < 1e-10

        if not (total_match and mean_match):
            all_passed = False

        test_cases.append({
            "point": p.to_tuple(),
            "total": {"expected": expected_total, "actual": actual_total, "match": total_match},
            "mean": {"expected": expected_mean, "actual": actual_mean, "match": mean_match},
        })

    return ValidationResult(
        name="entropy_aggregations",
        category="thermodynamic",
        passed=all_passed,
        expected="Total = ||S||, Mean = (S_k + S_t + S_e)/3",
        actual=test_cases,
        error=0.0 if all_passed else 1.0,
        tolerance=1e-10,
        details={},
        timestamp=timestamp,
    )

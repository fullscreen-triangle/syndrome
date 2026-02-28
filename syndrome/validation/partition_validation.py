"""
Partition Geometry Validation

Validates:
- Partition capacity formula C(n) = 2n²
- Categorical distance properties
- Address resolution accuracy
"""

from datetime import datetime
from typing import List
import numpy as np

from syndrome.core.partition import (
    PartitionCoord,
    partition_capacity,
    categorical_distance,
    categorical_distance_raw,
    enumerate_partition_states,
    address_to_value,
    value_to_address,
)
from syndrome.validation.types import ValidationResult


def run_partition_validations() -> List[ValidationResult]:
    """Run all partition geometry validations."""
    results = []
    timestamp = datetime.now().isoformat()

    # Test 1: Partition capacity formula
    results.append(_validate_capacity_formula(timestamp))

    # Test 2: Capacity sequence matches electron shells
    results.append(_validate_electron_shell_sequence(timestamp))

    # Test 3: State enumeration count
    results.append(_validate_enumeration_count(timestamp))

    # Test 4: Categorical distance metric properties
    results.extend(_validate_metric_properties(timestamp))

    # Test 5: Address resolution accuracy
    results.extend(_validate_address_resolution(timestamp))

    # Test 6: Coordinate validation
    results.append(_validate_coordinate_constraints(timestamp))

    return results


def _validate_capacity_formula(timestamp: str) -> ValidationResult:
    """Validate C(n) = 2n²."""
    test_cases = [(1, 2), (2, 8), (3, 18), (4, 32), (5, 50), (6, 72), (7, 98)]

    all_passed = True
    errors = []

    for n, expected in test_cases:
        actual = partition_capacity(n)
        if actual != expected:
            all_passed = False
            errors.append(f"n={n}: expected {expected}, got {actual}")

    return ValidationResult(
        name="partition_capacity_formula",
        category="partition",
        passed=all_passed,
        expected="C(n) = 2n² for all n",
        actual="Formula verified" if all_passed else f"Errors: {errors}",
        error=0.0 if all_passed else 1.0,
        tolerance=0.0,
        details={"test_cases": test_cases},
        timestamp=timestamp,
    )


def _validate_electron_shell_sequence(timestamp: str) -> ValidationResult:
    """Validate capacity sequence matches electron shell capacities."""
    # Expected electron shell capacities: 2, 8, 18, 32, 50, ...
    electron_shells = [2, 8, 18, 32, 50, 72, 98]
    computed = [partition_capacity(n) for n in range(1, 8)]

    match = computed == electron_shells

    return ValidationResult(
        name="electron_shell_correspondence",
        category="partition",
        passed=match,
        expected=electron_shells,
        actual=computed,
        error=0.0 if match else 1.0,
        tolerance=0.0,
        details={
            "interpretation": "Partition capacity matches atomic electron shell capacities",
            "significance": "Geometric necessity, not coincidence",
        },
        timestamp=timestamp,
    )


def _validate_enumeration_count(timestamp: str) -> ValidationResult:
    """Validate that enumeration produces correct number of states."""
    all_passed = True
    details = {}

    for n in range(1, 6):
        states = enumerate_partition_states(n)
        expected_count = partition_capacity(n)
        actual_count = len(states)

        details[f"n={n}"] = {"expected": expected_count, "actual": actual_count}

        if actual_count != expected_count:
            all_passed = False

    return ValidationResult(
        name="enumeration_count",
        category="partition",
        passed=all_passed,
        expected="len(enumerate_partition_states(n)) == C(n)",
        actual="Verified" if all_passed else "Mismatch",
        error=0.0 if all_passed else 1.0,
        tolerance=0.0,
        details=details,
        timestamp=timestamp,
    )


def _validate_metric_properties(timestamp: str) -> List[ValidationResult]:
    """Validate that categorical distance is a proper metric."""
    results = []

    # Create test states
    s1 = PartitionCoord(n=3, ell=1, m=0, s=0.5)
    s2 = PartitionCoord(n=3, ell=2, m=1, s=0.5)
    s3 = PartitionCoord(n=4, ell=1, m=-1, s=-0.5)

    # Non-negativity
    d12 = categorical_distance(s1, s2)
    d11 = categorical_distance(s1, s1)

    results.append(ValidationResult(
        name="metric_non_negativity",
        category="partition",
        passed=d12 >= 0 and d11 == 0,
        expected="d(x,y) >= 0 and d(x,x) = 0",
        actual=f"d(s1,s2)={d12:.4f}, d(s1,s1)={d11:.4f}",
        error=0.0 if (d12 >= 0 and d11 == 0) else 1.0,
        tolerance=1e-10,
        details={"d12": d12, "d11": d11},
        timestamp=timestamp,
    ))

    # Symmetry
    d12 = categorical_distance(s1, s2)
    d21 = categorical_distance(s2, s1)

    results.append(ValidationResult(
        name="metric_symmetry",
        category="partition",
        passed=abs(d12 - d21) < 1e-10,
        expected="d(x,y) = d(y,x)",
        actual=f"d(s1,s2)={d12:.6f}, d(s2,s1)={d21:.6f}",
        error=abs(d12 - d21),
        tolerance=1e-10,
        details={"d12": d12, "d21": d21, "difference": abs(d12 - d21)},
        timestamp=timestamp,
    ))

    # Triangle inequality
    d12 = categorical_distance(s1, s2)
    d23 = categorical_distance(s2, s3)
    d13 = categorical_distance(s1, s3)

    triangle_holds = d13 <= d12 + d23 + 1e-10

    results.append(ValidationResult(
        name="metric_triangle_inequality",
        category="partition",
        passed=triangle_holds,
        expected="d(x,z) <= d(x,y) + d(y,z)",
        actual=f"d(s1,s3)={d13:.4f} <= {d12:.4f} + {d23:.4f} = {d12+d23:.4f}",
        error=max(0, d13 - d12 - d23),
        tolerance=1e-10,
        details={"d12": d12, "d23": d23, "d13": d13, "sum": d12 + d23},
        timestamp=timestamp,
    ))

    return results


def _validate_address_resolution(timestamp: str) -> List[ValidationResult]:
    """Validate address encoding and resolution."""
    results = []

    # Test round-trip accuracy
    test_values = [0.0, 0.25, 0.333, 0.5, 0.667, 0.75, 1.0]
    depth = 10
    max_error = 0.0

    for val in test_values:
        address = value_to_address(val, depth)
        recovered = address_to_value(address)
        error = abs(val - recovered)
        max_error = max(max_error, error)

    # Expected precision at depth 10 is 1/3^10 ≈ 1.7e-5
    expected_precision = 1.0 / (3 ** depth)

    results.append(ValidationResult(
        name="address_resolution_accuracy",
        category="partition",
        passed=max_error <= expected_precision * 2,
        expected=f"Error < {expected_precision:.2e} (theoretical precision)",
        actual=f"Max error: {max_error:.2e}",
        error=max_error,
        tolerance=expected_precision * 2,
        details={
            "test_values": test_values,
            "depth": depth,
            "theoretical_precision": expected_precision,
        },
        timestamp=timestamp,
    ))

    # Test ternary structure
    address = [1, 1, 1]  # Middle of each subdivision
    value = address_to_value(address)
    expected = 1/3 * (1/3 + 1/9 + 1/27)  # Sum of ternary fractions

    # Simplified: 1/3 + 1/9 + 1/27 = 13/27 ≈ 0.481
    expected_approx = (1/3 + 1/9 + 1/27)

    results.append(ValidationResult(
        name="ternary_structure",
        category="partition",
        passed=abs(value - expected_approx) < 0.01,
        expected=f"address [1,1,1] -> ~{expected_approx:.4f}",
        actual=f"Computed: {value:.4f}",
        error=abs(value - expected_approx),
        tolerance=0.01,
        details={"address": address, "value": value},
        timestamp=timestamp,
    ))

    return results


def _validate_coordinate_constraints(timestamp: str) -> ValidationResult:
    """Validate coordinate constraint checking."""
    valid_coords = [
        (1, 0, 0, 0.5),
        (2, 1, -1, -0.5),
        (3, 2, 2, 0.5),
        (5, 4, -4, -0.5),
    ]

    invalid_coords = [
        (0, 0, 0, 0.5),      # n < 1
        (2, 2, 0, 0.5),      # ell >= n
        (3, 1, 2, 0.5),      # |m| > ell
        (2, 1, 0, 0.3),      # s not in {-0.5, 0.5}
    ]

    valid_results = []
    invalid_results = []

    for n, ell, m, s in valid_coords:
        try:
            PartitionCoord(n=n, ell=ell, m=m, s=s)
            valid_results.append(True)
        except ValueError:
            valid_results.append(False)

    for n, ell, m, s in invalid_coords:
        try:
            PartitionCoord(n=n, ell=ell, m=m, s=s)
            invalid_results.append(False)  # Should have raised
        except ValueError:
            invalid_results.append(True)  # Correctly rejected

    all_valid_accepted = all(valid_results)
    all_invalid_rejected = all(invalid_results)

    return ValidationResult(
        name="coordinate_constraints",
        category="partition",
        passed=all_valid_accepted and all_invalid_rejected,
        expected="Valid coords accepted, invalid coords rejected",
        actual=f"Valid: {sum(valid_results)}/{len(valid_results)}, "
               f"Invalid rejected: {sum(invalid_results)}/{len(invalid_results)}",
        error=0.0 if (all_valid_accepted and all_invalid_rejected) else 1.0,
        tolerance=0.0,
        details={
            "valid_coords": valid_coords,
            "invalid_coords": invalid_coords,
            "valid_accepted": valid_results,
            "invalid_rejected": invalid_results,
        },
        timestamp=timestamp,
    )

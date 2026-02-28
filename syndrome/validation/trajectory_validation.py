"""
Trajectory Validation

Validates:
- COMPLETE algorithm for trajectory resolution
- Ternary address resolution accuracy
- Address precision scaling
- Trajectory constraints
- Boundary condition preservation
"""

from datetime import datetime
from typing import List
import numpy as np

from syndrome.core.s_entropy import SEntropyPoint
from syndrome.core.trajectory import (
    Trajectory,
    Constraint,
    complete_trajectory,
    resolve_address,
    address_precision,
    make_bounded_constraint,
    make_smooth_constraint,
    make_monotonic_constraint,
    make_energy_constraint,
)
from syndrome.validation.types import ValidationResult


def run_trajectory_validations() -> List[ValidationResult]:
    """Run all trajectory validations."""
    results = []
    timestamp = datetime.now().isoformat()

    # Test 1: Address resolution
    results.extend(_validate_address_resolution(timestamp))

    # Test 2: Address precision
    results.append(_validate_address_precision(timestamp))

    # Test 3: COMPLETE algorithm boundary conditions
    results.append(_validate_complete_boundaries(timestamp))

    # Test 4: Constraint satisfaction
    results.extend(_validate_constraints(timestamp))

    # Test 5: Trajectory properties
    results.extend(_validate_trajectory_properties(timestamp))

    # Test 6: Interpolation
    results.append(_validate_trajectory_interpolation(timestamp))

    return results


def _validate_address_resolution(timestamp: str) -> List[ValidationResult]:
    """Validate ternary address resolution accuracy."""
    results = []

    # Test case 1: Empty address → midpoint
    address_empty = []
    expected_empty = 0.5
    actual_empty = resolve_address(address_empty, 0.0, 1.0)

    results.append(ValidationResult(
        name="address_resolution_empty",
        category="trajectory",
        passed=abs(actual_empty - expected_empty) < 1e-10,
        expected=expected_empty,
        actual=actual_empty,
        error=abs(actual_empty - expected_empty),
        tolerance=1e-10,
        details={"address": address_empty, "interpretation": "Empty → midpoint"},
        timestamp=timestamp,
    ))

    # Test case 2: [0] → 0/3 = 0.0 contribution
    address_0 = [0]
    expected_0 = 0.0
    actual_0 = resolve_address(address_0, 0.0, 1.0)

    results.append(ValidationResult(
        name="address_resolution_zero",
        category="trajectory",
        passed=abs(actual_0 - expected_0) < 1e-10,
        expected=expected_0,
        actual=actual_0,
        error=abs(actual_0 - expected_0),
        tolerance=1e-10,
        details={"address": address_0},
        timestamp=timestamp,
    ))

    # Test case 3: [2] → 2/3 ≈ 0.6667
    address_2 = [2]
    expected_2 = 2.0 / 3.0
    actual_2 = resolve_address(address_2, 0.0, 1.0)

    results.append(ValidationResult(
        name="address_resolution_two",
        category="trajectory",
        passed=abs(actual_2 - expected_2) < 1e-10,
        expected=expected_2,
        actual=actual_2,
        error=abs(actual_2 - expected_2),
        tolerance=1e-10,
        details={"address": address_2},
        timestamp=timestamp,
    ))

    # Test case 4: [1, 1] → 1/3 + 1/9 = 4/9 ≈ 0.4444
    address_11 = [1, 1]
    expected_11 = 1.0 / 3.0 + 1.0 / 9.0
    actual_11 = resolve_address(address_11, 0.0, 1.0)

    results.append(ValidationResult(
        name="address_resolution_multi_digit",
        category="trajectory",
        passed=abs(actual_11 - expected_11) < 1e-10,
        expected=expected_11,
        actual=actual_11,
        error=abs(actual_11 - expected_11),
        tolerance=1e-10,
        details={"address": address_11, "calculation": "1/3 + 1/9 = 4/9"},
        timestamp=timestamp,
    ))

    # Test case 5: Range scaling
    address_range = [1]
    range_min, range_max = 10.0, 20.0
    expected_range = 10.0 + (1.0 / 3.0) * 10.0  # 10 + 10/3 ≈ 13.33
    actual_range = resolve_address(address_range, range_min, range_max)

    results.append(ValidationResult(
        name="address_resolution_range_scaling",
        category="trajectory",
        passed=abs(actual_range - expected_range) < 1e-10,
        expected=expected_range,
        actual=actual_range,
        error=abs(actual_range - expected_range),
        tolerance=1e-10,
        details={
            "address": address_range,
            "range": [range_min, range_max],
        },
        timestamp=timestamp,
    ))

    return results


def _validate_address_precision(timestamp: str) -> ValidationResult:
    """Validate address precision scaling."""
    test_cases = []
    all_passed = True

    for depth in range(1, 8):
        expected = 1.0 / (3 ** depth)
        actual = address_precision(depth)

        if abs(actual - expected) > 1e-15:
            all_passed = False

        test_cases.append({
            "depth": depth,
            "expected": expected,
            "actual": actual,
            "match": abs(actual - expected) < 1e-15,
        })

    return ValidationResult(
        name="address_precision_scaling",
        category="trajectory",
        passed=all_passed,
        expected="precision(d) = 1/3^d",
        actual=test_cases,
        error=0.0 if all_passed else 1.0,
        tolerance=1e-15,
        details={
            "formula": "precision = 1 / 3^depth",
            "interpretation": "Exponential refinement with ternary addresses",
        },
        timestamp=timestamp,
    )


def _validate_complete_boundaries(timestamp: str) -> ValidationResult:
    """Validate COMPLETE algorithm preserves boundary conditions."""
    initial = SEntropyPoint(s_k=0.1, s_t=0.2, s_e=0.3)
    final = SEntropyPoint(s_k=0.8, s_t=0.7, s_e=0.6)

    # Simple bounded constraint
    constraints = [make_bounded_constraint()]

    trajectory = complete_trajectory(initial, final, constraints, n_points=50)

    if trajectory is None:
        return ValidationResult(
            name="complete_boundary_conditions",
            category="trajectory",
            passed=False,
            expected="Trajectory found",
            actual="No trajectory found",
            error=1.0,
            tolerance=1e-10,
            details={},
            timestamp=timestamp,
        )

    # Check boundary conditions
    initial_match = np.allclose(
        trajectory.initial_state().to_array(),
        initial.to_array(),
        atol=1e-10
    )
    final_match = np.allclose(
        trajectory.final_state().to_array(),
        final.to_array(),
        atol=1e-10
    )

    all_passed = initial_match and final_match

    return ValidationResult(
        name="complete_boundary_conditions",
        category="trajectory",
        passed=all_passed,
        expected="Initial and final states preserved",
        actual={
            "initial_match": initial_match,
            "final_match": final_match,
            "trajectory_initial": trajectory.initial_state().to_tuple(),
            "trajectory_final": trajectory.final_state().to_tuple(),
        },
        error=0.0 if all_passed else 1.0,
        tolerance=1e-10,
        details={
            "initial": initial.to_tuple(),
            "final": final.to_tuple(),
            "n_points": len(trajectory.points),
        },
        timestamp=timestamp,
    )


def _validate_constraints(timestamp: str) -> List[ValidationResult]:
    """Validate trajectory constraint functions."""
    results = []

    # Test bounded constraint
    bounded = make_bounded_constraint(0.0, 1.0)

    # Valid trajectory (all in bounds)
    valid_points = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
    bounded_valid = bounded.check(valid_points)

    results.append(ValidationResult(
        name="constraint_bounded_valid",
        category="trajectory",
        passed=bounded_valid,
        expected=True,
        actual=bounded_valid,
        error=0.0 if bounded_valid else 1.0,
        tolerance=0.0,
        details={"points_range": [valid_points.min(), valid_points.max()]},
        timestamp=timestamp,
    ))

    # Invalid trajectory (out of bounds)
    invalid_points = np.array([[0.1, 0.2, 1.5], [0.4, 0.5, 0.6]])
    bounded_invalid = bounded.check(invalid_points)

    results.append(ValidationResult(
        name="constraint_bounded_invalid",
        category="trajectory",
        passed=not bounded_invalid,
        expected=False,
        actual=bounded_invalid,
        error=0.0 if not bounded_invalid else 1.0,
        tolerance=0.0,
        details={"out_of_bounds_value": 1.5},
        timestamp=timestamp,
    ))

    # Test smooth constraint
    smooth = make_smooth_constraint(max_curvature=0.5)

    # Smooth trajectory
    t = np.linspace(0, 1, 20)
    smooth_points = np.column_stack([t, t**2, t])  # Parabolic, smooth
    smooth_check = smooth.check(smooth_points)

    results.append(ValidationResult(
        name="constraint_smooth_parabolic",
        category="trajectory",
        passed=smooth_check,
        expected=True,
        actual=smooth_check,
        error=0.0 if smooth_check else 1.0,
        tolerance=0.0,
        details={"trajectory_type": "parabolic"},
        timestamp=timestamp,
    ))

    # Test monotonic constraint
    mono = make_monotonic_constraint(dim=0, increasing=True)

    # Monotonic in first dimension
    mono_points = np.array([[0.1, 0.5, 0.5], [0.3, 0.4, 0.6], [0.5, 0.6, 0.4]])
    mono_check = mono.check(mono_points)

    results.append(ValidationResult(
        name="constraint_monotonic_increasing",
        category="trajectory",
        passed=mono_check,
        expected=True,
        actual=mono_check,
        error=0.0 if mono_check else 1.0,
        tolerance=0.0,
        details={"dimension": 0, "direction": "increasing"},
        timestamp=timestamp,
    ))

    # Test energy constraint
    energy = make_energy_constraint(max_total_change=1.0)

    # Short trajectory
    short_points = np.array([[0.0, 0.0, 0.0], [0.1, 0.1, 0.1], [0.2, 0.2, 0.2]])
    energy_check = energy.check(short_points)

    results.append(ValidationResult(
        name="constraint_energy_satisfied",
        category="trajectory",
        passed=energy_check,
        expected=True,
        actual=energy_check,
        error=0.0 if energy_check else 1.0,
        tolerance=0.0,
        details={"max_total_change": 1.0},
        timestamp=timestamp,
    ))

    return results


def _validate_trajectory_properties(timestamp: str) -> List[ValidationResult]:
    """Validate trajectory object properties."""
    results = []

    # Create test trajectory
    points = np.array([
        [0.0, 0.0, 0.0],
        [0.2, 0.1, 0.1],
        [0.4, 0.3, 0.2],
        [0.6, 0.4, 0.4],
        [0.8, 0.6, 0.5],
        [1.0, 0.8, 0.7],
    ])
    times = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

    trajectory = Trajectory(
        points=points,
        times=times,
        constraints_satisfied=["bounded"],
    )

    # Test duration
    expected_duration = 1.0
    actual_duration = trajectory.duration

    results.append(ValidationResult(
        name="trajectory_duration",
        category="trajectory",
        passed=abs(actual_duration - expected_duration) < 1e-10,
        expected=expected_duration,
        actual=actual_duration,
        error=abs(actual_duration - expected_duration),
        tolerance=1e-10,
        details={"times": times.tolist()},
        timestamp=timestamp,
    ))

    # Test arc length (sum of segment lengths)
    diffs = np.diff(points, axis=0)
    expected_length = float(np.sum(np.linalg.norm(diffs, axis=1)))
    actual_length = trajectory.length

    results.append(ValidationResult(
        name="trajectory_arc_length",
        category="trajectory",
        passed=abs(actual_length - expected_length) < 1e-10,
        expected=expected_length,
        actual=actual_length,
        error=abs(actual_length - expected_length),
        tolerance=1e-10,
        details={"n_segments": len(points) - 1},
        timestamp=timestamp,
    ))

    # Test initial and final states
    initial_state = trajectory.initial_state()
    final_state = trajectory.final_state()

    initial_match = np.allclose(initial_state.to_array(), points[0])
    final_match = np.allclose(final_state.to_array(), points[-1])

    results.append(ValidationResult(
        name="trajectory_endpoint_states",
        category="trajectory",
        passed=initial_match and final_match,
        expected="Endpoints match trajectory bounds",
        actual={
            "initial": initial_state.to_tuple(),
            "final": final_state.to_tuple(),
        },
        error=0.0 if (initial_match and final_match) else 1.0,
        tolerance=1e-10,
        details={},
        timestamp=timestamp,
    ))

    return results


def _validate_trajectory_interpolation(timestamp: str) -> ValidationResult:
    """Validate trajectory time interpolation."""
    # Create simple linear trajectory
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
    ])
    times = np.array([0.0, 1.0])

    trajectory = Trajectory(
        points=points,
        times=times,
        constraints_satisfied=[],
    )

    # Test interpolation at midpoint
    t_mid = 0.5
    state_mid = trajectory.at_time(t_mid)
    expected_mid = np.array([0.5, 0.5, 0.5])

    mid_match = np.allclose(state_mid.to_array(), expected_mid)

    # Test interpolation at boundaries
    state_start = trajectory.at_time(0.0)
    state_end = trajectory.at_time(1.0)

    start_match = np.allclose(state_start.to_array(), points[0])
    end_match = np.allclose(state_end.to_array(), points[-1])

    # Test extrapolation (should clamp to boundaries)
    state_before = trajectory.at_time(-0.5)
    state_after = trajectory.at_time(1.5)

    before_match = np.allclose(state_before.to_array(), points[0])
    after_match = np.allclose(state_after.to_array(), points[-1])

    all_passed = all([mid_match, start_match, end_match, before_match, after_match])

    return ValidationResult(
        name="trajectory_interpolation",
        category="trajectory",
        passed=all_passed,
        expected="Linear interpolation with boundary clamping",
        actual={
            "mid_match": mid_match,
            "start_match": start_match,
            "end_match": end_match,
            "before_clamped": before_match,
            "after_clamped": after_match,
        },
        error=0.0 if all_passed else 1.0,
        tolerance=1e-10,
        details={
            "midpoint_state": state_mid.to_tuple(),
            "expected_midpoint": expected_mid.tolist(),
        },
        timestamp=timestamp,
    )

"""
Validation Runner

Orchestrates all validation tests and saves results to JSON/CSV.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from syndrome.validation.types import ValidationResult, ValidationSuite


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def _ensure_results_dir() -> Path:
    """Ensure results directory exists."""
    # Get project root (parent of syndrome package)
    module_path = Path(__file__).parent.parent.parent
    results_dir = module_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def save_results_json(suite: ValidationSuite, filepath: Path) -> None:
    """Save validation results to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(suite.to_dict(), f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    print(f"Results saved to: {filepath}")


def save_results_csv(suite: ValidationSuite, filepath: Path) -> None:
    """Save validation results to CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    rows = suite.to_csv_rows()

    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Results saved to: {filepath}")


def run_validation_category(
    name: str,
    run_func,
    results_dir: Path
) -> ValidationSuite:
    """
    Run a validation category and save results.

    Args:
        name: Category name
        run_func: Function that returns list of ValidationResult
        results_dir: Directory for results

    Returns:
        ValidationSuite with results
    """
    timestamp = datetime.now().isoformat()
    print(f"\n{'='*60}")
    print(f"Running {name} validations...")
    print(f"{'='*60}")

    results = run_func()

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    pass_rate = passed / len(results) if results else 0.0

    suite = ValidationSuite(
        name=name,
        results=results,
        passed=passed,
        failed=failed,
        total=len(results),
        pass_rate=pass_rate,
        timestamp=timestamp,
    )

    # Print summary
    print(f"\n{name} Results: {passed}/{len(results)} passed ({pass_rate*100:.1f}%)")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        error_str = f" (error: {r.error:.2e})" if r.error is not None else ""
        print(f"  [{status}] {r.name}{error_str}")

    # Save results
    category_dir = results_dir / name.lower().replace(" ", "_")
    save_results_json(suite, category_dir / f"{name.lower().replace(' ', '_')}_results.json")
    save_results_csv(suite, category_dir / f"{name.lower().replace(' ', '_')}_results.csv")

    return suite


def run_all_validations() -> Dict[str, ValidationSuite]:
    """
    Run all validation suites and save results.

    Returns:
        Dictionary mapping category name to ValidationSuite
    """
    # Late imports to avoid circular dependencies
    from syndrome.validation.partition_validation import run_partition_validations
    from syndrome.validation.coherence_validation import run_coherence_validations
    from syndrome.validation.disease_validation import run_disease_validations
    from syndrome.validation.trajectory_validation import run_trajectory_validations
    from syndrome.validation.thermodynamic_validation import run_thermodynamic_validations

    results_dir = _ensure_results_dir()
    timestamp = datetime.now().isoformat()

    print("\n" + "="*70)
    print("SYNDROME FRAMEWORK VALIDATION")
    print(f"Timestamp: {timestamp}")
    print("="*70)

    suites = {}

    # Run each validation category
    categories = [
        ("Partition", run_partition_validations),
        ("Coherence", run_coherence_validations),
        ("Disease", run_disease_validations),
        ("Trajectory", run_trajectory_validations),
        ("Thermodynamic", run_thermodynamic_validations),
    ]

    for name, run_func in categories:
        suite = run_validation_category(name, run_func, results_dir)
        suites[name] = suite

    # Aggregate summary
    total_passed = sum(s.passed for s in suites.values())
    total_tests = sum(s.total for s in suites.values())
    overall_pass_rate = total_passed / total_tests if total_tests > 0 else 0.0

    print("\n" + "="*70)
    print("OVERALL VALIDATION SUMMARY")
    print("="*70)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Pass rate: {overall_pass_rate*100:.1f}%")
    print("="*70)

    # Save aggregate summary
    summary = {
        "timestamp": timestamp,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_tests - total_passed,
        "overall_pass_rate": overall_pass_rate,
        "categories": {name: s.to_dict() for name, s in suites.items()},
    }

    summary_path = results_dir / "validation_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, cls=NumpyEncoder)
    print(f"\nSummary saved to: {summary_path}")

    return suites


def main():
    """Command-line entry point."""
    run_all_validations()


if __name__ == "__main__":
    main()

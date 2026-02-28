"""
Validation Types

Shared types for validation infrastructure.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import numpy as np


@dataclass
class ValidationResult:
    """
    Result of a single validation test.

    Attributes:
        name: Test name
        category: Validation category
        passed: Whether test passed
        expected: Expected value/condition
        actual: Actual computed value
        error: Relative or absolute error
        tolerance: Acceptance tolerance
        details: Additional details
        timestamp: When test was run
    """
    name: str
    category: str
    passed: bool
    expected: Any
    actual: Any
    error: Optional[float]
    tolerance: float
    details: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "expected": _serialize_value(self.expected),
            "actual": _serialize_value(self.actual),
            "error": self.error,
            "tolerance": self.tolerance,
            "details": {k: _serialize_value(v) for k, v in self.details.items()},
            "timestamp": self.timestamp,
        }


@dataclass
class ValidationSuite:
    """
    Collection of validation results.

    Attributes:
        name: Suite name
        results: List of validation results
        passed: Number of passed tests
        failed: Number of failed tests
        total: Total number of tests
        pass_rate: Fraction of tests passed
        timestamp: When suite was run
    """
    name: str
    results: List[ValidationResult]
    passed: int
    failed: int
    total: int
    pass_rate: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "passed": self.passed,
            "failed": self.failed,
            "total": self.total,
            "pass_rate": self.pass_rate,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
        }

    def to_csv_rows(self) -> List[Dict[str, Any]]:
        """Convert to list of CSV row dictionaries."""
        rows = []
        for r in self.results:
            rows.append({
                "suite": self.name,
                "test_name": r.name,
                "category": r.category,
                "passed": r.passed,
                "expected": str(r.expected),
                "actual": str(r.actual),
                "error": r.error,
                "tolerance": r.tolerance,
                "timestamp": r.timestamp,
            })
        return rows


def _serialize_value(value: Any) -> Any:
    """Serialize value for JSON."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, (np.integer, np.floating)):
        return float(value)
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    else:
        return value

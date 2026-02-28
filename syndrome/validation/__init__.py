"""
Validation Suite for Syndrome Framework

This module provides comprehensive validation of the theoretical framework
against expected mathematical properties and biological data.

All validation results are saved to JSON and CSV formats in the results/ directory.
"""

from syndrome.validation.types import ValidationResult, ValidationSuite
from syndrome.validation.runner import run_all_validations

__all__ = [
    "run_all_validations",
    "ValidationResult",
    "ValidationSuite",
]

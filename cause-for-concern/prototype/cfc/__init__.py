"""
cfc -- a prototyping implementation of the Cause-for-Concern calculus.

Scope: enough of the language to run cycle-consistency experiments with
per-cycle tolerances, and to record every run as JSON.

    from cfc import run_file
    rec = run_file("examples/kcl_tolerance.cfc")
    print(rec.status, rec.clock)

The design commitments that are not negotiable in this implementation:

  * `admit H tolerance T` is the only way to obtain a Verdict, so no
    verdict exists without the tolerance that justifies it.
  * `tolerance of L with S` requires the uncertainty source; there is no
    default, and a missing sigma yields UNDECIDABLE rather than a guess.
  * The verdict is three-valued. UNDECIDABLE is a result, not an
    abstention.
  * `otherwise invalid` halts with INVALID, distinct from NEGATIVE: an
    invalid run licenses no conclusion about the hypothesis.
"""

from .lexer import LexError, Token, TokKind, tokenize
from .parser import ParseError, parse
from .interpreter import (
    CFCRuntimeError, Interpreter, Record, RuntimeHalt,
    run_file, run_source, run_to_json,
)
from .kernel import (
    CONSISTENT, INCONSISTENT, UNDECIDABLE, Circuit, Cycle, Holonomy,
    KernelError, Reaction, Species, Tolerance, Verdict, admit,
    compute_holonomy, compute_tolerance, cycle_sum, data_floor,
    fundamental_cycle_basis, minimum_cycle_basis, numerical_floor,
    witness_set,
)

__version__ = "0.1.0"

__all__ = [
    "tokenize", "Token", "TokKind", "LexError",
    "parse", "ParseError",
    "run_source", "run_file", "run_to_json",
    "Interpreter", "Record", "RuntimeHalt", "CFCRuntimeError",
    "Circuit", "Species", "Reaction", "Cycle", "KernelError",
    "Holonomy", "Tolerance", "Verdict", "admit",
    "compute_holonomy", "compute_tolerance", "cycle_sum",
    "numerical_floor", "data_floor", "witness_set",
    "minimum_cycle_basis", "fundamental_cycle_basis",
    "CONSISTENT", "UNDECIDABLE", "INCONSISTENT",
]

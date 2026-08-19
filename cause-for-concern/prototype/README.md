# CFC prototype

A small lexer, parser, and interpreter for the Cause-for-Concern
language, scoped to the cycle-consistency experiment of
`../docs/disease-circuit-tolerance/`. Pure standard library — no
dependencies.

```bash
python test_cfc.py                              # 28 checks
python run_cfc.py examples/kcl_tolerance.cfc    # run one program
python run_cfc.py examples/*.cfc                # run all, JSON to results/
python run_cfc.py examples/kcl_tolerance.cfc --tokens   # token stream
python run_cfc.py examples/kcl_tolerance.cfc --ast      # statement list
```

Every run writes `results/<name>.json` recording the environment, the
circuits, every tolerance, every verdict with the tolerance that
produced it, all assertions, emissions, reports, and the witness set.

## Layout

| Path | Purpose |
|---|---|
| `cfc/lexer.py` | hand-written scanner, line/column tracked |
| `cfc/ast_nodes.py` | AST dataclasses |
| `cfc/parser.py` | recursive descent → AST |
| `cfc/kernel.py` | circuits, cycle bases, the two floors, verdicts |
| `cfc/interpreter.py` | evaluation, the clock, the JSON record |
| `run_cfc.py` | CLI |
| `test_cfc.py` | checks on the kernel and the language guarantees |

## The four design commitments

These are enforced, not documented aspirations.

**1. A verdict cannot exist without its tolerance.** `admit H tolerance T`
is the only production yielding a `Verdict`, and both operands are
mandatory. `examples/rejected_bare_verdict.cfc` attempts the omission
and fails to parse. There is no production comparing a holonomy to a
numeric literal, so the rule cannot be worked around in user code.

**2. A tolerance cannot be conjured.** `tolerance of L with S` requires
the `with` clause naming the uncertainty source. When a species carries
no `sigma`, the data floor is *undefined* rather than defaulted, and
every cycle above the numerical floor returns `UNDECIDABLE`. Fabricating
a default would turn an unanswerable question into a confident answer.

**3. The verdict is three-valued.**

| | condition |
|---|---|
| `CONSISTENT` | `|H| ≤ ε_num` |
| `UNDECIDABLE` | `ε_num < |H| ≤ ε_data` |
| `INCONSISTENT` | `|H| > ε*` |

`UNDECIDABLE` is a result, not an abstention: the signal is too large to
be arithmetic and too small to be resolved by data of this quality.
`examples/undecidable.cfc` runs the same 3 kJ/mol defect against
σ = 0.02 and σ = 3.0 and gets `INCONSISTENT` then `UNDECIDABLE`.

**4. `INVALID` is not `NEGATIVE`.** `assert … otherwise invalid` halts
with `INVALID`: the reference network failed its own consistency check,
so the run licenses no conclusion about the hypothesis. `otherwise
decline` yields `NEGATIVE`, which is a real result about the test. See
`examples/invalid_reference.cfc`.

## Defects live on edges, not nodes

`perturb_edge(C, "RXN", δ)` injects a detectable defect.
`perturb(C, "SPECIES", δ)` does **not** — and the test suite asserts
this as a negative control.

Shifting a node potential leaves the edge data the gradient of the
shifted potential, so every cycle sum stays exactly zero. Only an edge
offset makes the data fail to be a gradient, which is what
thermodynamic inconsistency means. This was a real bug during
development: the first version of `kcl_tolerance.cfc` perturbed a node,
detected nothing, and looked like a failure of the method rather than of
the perturbation.

## Example output

```
=== examples/kcl_tolerance.cfc ===
  status      : OK  (all assertions held)
  clock       : 5 committed measurement(s)
  verdicts    : 4 (CONSISTENT=2, INCONSISTENT=2)
  tolerances  : 4 computed
  witness set : 1 edge(s) [SHNT]
  emit L68  : validity gate passed: reference is self-consistent
  emit L102 : defect localised to a non-empty witness set
```

The witness set — edges lying on *every* flagged cycle — is the
basis-independent content of a positive result. Naming a single loop is
not basis-independent: the flagged set depends on which cycle basis was
computed, and the test suite checks that both a minimum-weight and a
fundamental basis recover the defect.

## What this prototype is not

It is a prototyping vehicle for one experiment, not an implementation of
the full CFC specification. `measure`, `localize`, `close`, and the
gap-closure machinery are lexed but not implemented. Circuits are solved
by direct evaluation, not by a nonlinear solver. There is no type
checker separate from the parser — the guarantees above are enforced
syntactically and at runtime, which is sufficient for the ones claimed
but is not the type soundness result the specification states.

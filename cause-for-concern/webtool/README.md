# CFC Workbench

A browser IDE for writing and running cycle-consistency experiments in
the Cause-for-Concern language.

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # static bundle in dist/
node test/examples.mjs   # headless: run every example
node test/browser.mjs    # end-to-end, needs `npm run preview` first
```

## Programs actually run

The kernel, lexer, parser and interpreter are ports of the Python
reference in [`../prototype/cfc/`](../prototype/cfc/), not stubs. When
you press **Run**, the browser:

1. solves the circuit — `μ = μ° + RT ln c`, `G = kc/RT`, `J = G Δμ`
2. gauge-centres the potentials
3. computes a minimum-weight cycle basis over GF(2)
4. evaluates each cycle sum
5. derives **both** floors and classifies

Numbers agree with the Python implementation to machine precision. On
the reference circuit both produce `ε_num = 4.249e-12`,
`ε_data = 11.337`, witness set `{SHNT}`.

Every chart is drawn from that record. There is no synthetic data path:
if a program computes nothing, nothing is plotted.

## The four guarantees, enforced

**A verdict cannot exist without its tolerance.** `admit H tolerance T`
is the only production yielding a `Verdict`, and both operands are
mandatory. `04_rejected.cfc` attempts the omission and fails to parse —
try deleting the `tolerance t` clause anywhere and watch it refuse.

**A tolerance cannot be conjured.** `tolerance of L with S` requires the
`with` clause. A species carrying no `sigma` yields an *undefined* data
floor rather than a default, and every cycle above the numerical floor
returns `UNDECIDABLE`.

**Verdicts are three-valued.**

| | condition |
|---|---|
| `CONSISTENT` | `\|H\| ≤ ε_num` |
| `UNDECIDABLE` | `ε_num < \|H\| ≤ ε_data` |
| `INCONSISTENT` | `\|H\| > ε*` |

**`INVALID` ≠ `NEGATIVE`.** `otherwise invalid` halts with `INVALID`:
the reference failed its own check, so the run licenses no conclusion.
`otherwise decline` gives `NEGATIVE`, a real result about the test.

## Examples

| File | Status | Shows |
|---|---|---|
| `01_validity_gate.cfc` | OK | the full protocol; witness set = `{SHNT}` |
| `02_undecidable.cfc` | OK | one defect, two data qualities, two verdicts |
| `03_invalid_reference.cfc` | INVALID | the gate halting before any diagnostic claim |
| `04_rejected.cfc` | ERROR | a verdict without a tolerance does not parse |
| `05_node_vs_edge.cfc` | OK | node perturbation detects nothing; edge does |

## Three views

**Experiments** (files icon) — the editor. Write and run `.cfc` programs;
edits persist to `localStorage` and a dot marks a modified file, with
`revert` to restore the original. `Ctrl/Cmd+Enter` runs; **auto-run**
re-runs on a debounce as you type.

**Validation lab** (flask icon) — the paper's five experiments, run live
against the same kernel. Each builds, solves and classifies hundreds of
circuits in tens of milliseconds. The **seed** is exposed: change it,
re-run, and the points move, because these are measurements.

| Sweep | Reproduces | Typical |
|---|---|---|
| V1 Noise scale | 0 bound violations, median slack ≈730× | 35 ms |
| V2 Fixed tolerance | FP 0.00 in binary64, up to 0.84 in binary32 | 60 ms |
| V3 Trichotomy | ≈81% undecidable, ≈11.5-order floor gap | 10 ms |
| V4 Basis dependence | 0 verdict disagreements, ≈35% flagged-set | 44 ms |
| V5 Detection | 0 guarantee violations, ratio ≈0.51–0.71 | 4 ms |

**Reference** (book icon) — the language reference, including which
constructs are not implemented.

## Layout

Three columns: explorer, editor, output. The output column is dragged
from its left edge (double-click the splitter to reset to 520 px) and
its width persists across reloads. Charts measure the column and redraw
at whatever width it is given, so the split can be moved freely.

Putting output beside the editor rather than beneath it roughly doubles
the visible program — about 46 lines instead of 24 at 1020 px tall —
which matters because a `.cfc` program is read as a whole: the validity
gate and the diagnostic that depends on it should be on screen together.

## Panes

**Charts** — stacked vertically with a caption above each: cycle sums
against both floors; the circuit graph with the witness set in red;
floor separation in orders of magnitude; a rotating 3-D cycle space
(length × log|H| × log ε*); verdict counts. A status strip above the
tabs carries the run status, `m`, and the verdict tally, so the outcome
is visible from any tab.

**Terminal** — the run log: circuit stats, ν, node balance, per-cycle
tolerances, verdict tally, witness set, emissions, and the committed
measurement count `m`.

**Inspector** — one row per verdict: line, cycle, L, Λ, |H|, both floors,
ε*, and the verdict. This is the table behind the charts, so a
surprising colour can be traced to its numbers.

**Record** — the full JSON, downloadable via **Export JSON**. Same shape
as the Python runner's output, so records from either are comparable.

## Editing

The gutter marks the offending line when a run fails. `Tab` inserts two
spaces. Edits persist across reloads; only files that differ from the
shipped examples are stored.

## Tests

```bash
node test/examples.mjs   # every example, headless
node test/sweeps.mjs     # every sweep, with timings
node test/browser.mjs    # 11 end-to-end checks (needs `npm run preview`)
```

The browser suite drives all five examples, the charts, the inspector,
the keyboard shortcut, all five sweeps and the reference pane, and fails
on any console error.

## Limits

This implements the tolerance/verdict fragment only. `measure`,
`localize`, `close` and the gap-closure machinery are lexed but not
implemented. Guarantees are enforced syntactically and at runtime rather
than by a separate typechecker — sufficient for the claims above, but
not the full type-soundness result the specification states.

Circuits are solved by direct evaluation, not a nonlinear solver, and
`import` yields symbolic markers rather than fetching real data: every
number that can change a verdict has to appear in the program text.

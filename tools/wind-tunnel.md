# Wind Tunnel — Usage Guide

Wind tunnel analyses whether your software system is *globally self-consistent* — whether its units coordinate toward a shared purpose rather than merely passing local tests. This guide covers installation, configuration, and every subcommand.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Rust + Cargo | ≥ 1.75 | Install via [rustup.rs](https://rustup.rs) |
| Python | ≥ 3.10 | Validation suite only — not required to run `wt` |

No external indexer is needed. Symbol resolution is built in (`wt-index`).

---

## Installation

### 1. Install Rust

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. Build and install `wt`

```sh
git clone <this-repo>
cd wind-tunnel
cargo install --path wt
```

`wt` is now on your PATH. Verify:

```sh
wt --version
```

---

## HuggingFace extraction backend (optional)

Wind tunnel can use a code model via the HuggingFace Inference API to extract
type signatures from source files that tree-sitter cannot parse completely. To
enable it:

1. Copy the example env file — **do not commit it**:
   ```sh
   cp .env.local.example .env.local
   ```

2. `.env.local` already contains your token. Source it before running `wt`:
   ```sh
   source .env.local   # bash/zsh
   # or on Windows:
   $env:HF_TOKEN = "hf_..."
   ```

   `HUGGINGFACE_HUB_TOKEN` is also accepted as an alias.

3. Optionally override the model (default: `bigcode/starcoder2-7b`):
   ```sh
   export WT_HF_MODEL=bigcode/starcoder2-15b
   ```

Both `.env.local` and `.env.local.example` are git-ignored — they will never be pushed.

---

## Extraction backends

`wt` has three strategies for reading your codebase:

| Backend | Flag | How it works |
|---|---|---|
| `auto` | `--backend auto` (default) | Tree-sitter per file; falls back to HF if the parse returns nothing |
| `treesitter` | `--backend treesitter` | AST-based exact extraction. Supports `.rs`, `.py`, `.js`, `.mjs`, `.ts`, `.tsx`. Fast, no network, no token needed. |
| `hf` | `--backend hf` | HuggingFace Inference API. Language-agnostic, probabilistic. Requires `HF_TOKEN`. |

For most Rust / Python / JS / TS projects the default `auto` is all you need.
Use `--backend hf` explicitly when the project is heavily macro-heavy, dynamically
typed, or uses a language tree-sitter does not cover.

---

## Quick start

```sh
cd /path/to/your/project

# Static analysis — no traces required
wt static

# Full protocol — with runtime traces in /tmp/traces/
wt run . /tmp/traces/
```

Both commands default to the current directory if no path is given.

---

## The web editor and the CLI

Wind tunnel has a browser editor and a local binary, and the division between
them is deliberate rather than incidental.

| | Browser | Local `wt` |
|---|---|---|
| Write and edit scripts | ✅ | via your own editor |
| Syntax highlighting, parse errors | ✅ | ✅ |
| **Measure a real codebase** | ❌ | ✅ |
| Run in CI | ❌ | ✅ |

The browser owns *authoring and presentation*. The binary owns *computation*.
The reason is not preference: analysis walks your source tree and holds the
whole symbol graph in memory. A web page cannot do that, and should not be able
to — it would mean handing your source to a server.

So the editor works with nothing installed, and you can write and share scripts
freely. The moment you press **▶ Run**, the work happens on your machine via
[`wt serve`](#wt-serve-project-dir---port-n). This is also why local runs are
faster and handle larger trees: there is no upload, no sandbox, and no request
size to respect.

**When no engine is running, the editor says so and shows nothing else.** It
will not display a regime, an `R_est`, or a verdict it did not measure. A
plausible-looking number with no measurement behind it is worse than a visible
failure, because you would act on it.

---

## Subcommands

### `wt static [<project-dir>]`

Reads the codebase, builds the dependency graph, and runs Phase 1 of the protocol.

**What it computes:**
- Synchronisation tension `ϑ(u_i, u_j)` on every edge
- Static order parameter `R_est = exp(−mean tension)`
- Coordination regime (Turbulent → Phase-locked)
- Critical coupling estimate `K_c = 2σ_ω / π`
- Decoherence zones — maximal subgraphs whose local `R_est` falls below the global value
- Cycle candidates — directed cycles whose static residual exceeds `--threshold`

**Example:**

```sh
wt static /path/to/project
```

```
Project : /path/to/project
Units   : 47   Edges: 83
Regime  : Hierarchical cascade
R_est   : 0.6143
K_c     : 0.8821
Zones   :
  R_est=0.4201  Δ=0.1942  ["payments", "ledger"]
Cycles  :
  residual=2.3401  ["payments", "ledger", "reconciler"]
```

The coloured regime label is the most important single output:

| Colour | Regime | What it means |
|---|---|---|
| Red | Turbulent | Units share no common action-cell. Expect semantic drift under any load. |
| Yellow | Aperture-dominated | Interface contracts exist but there is no shared purpose. |
| Bright yellow | Hierarchical cascade | Coherent clusters, incoherent interfaces between them. |
| Green | Coherent | Converging toward a shared action-cell. Holonomy checks are warranted. |
| Blue | Phase-locked | Partition extinction. Coordination friction is zero. |

---

### `wt dynamic [<project-dir>] <traces-dir>`

Runs Phase 2. Ingests runtime traces and measures dynamic coherence.

**What it computes:**
- `R_dyn(t)` as a time series — phase coherence as the system runs
- Live holonomy violations on candidate cycles
- Aperture drift events — units whose runtime outputs exit their declared type sets

**Traces** are JSONL files, one per unit, placed in a directory:

```
traces/
├── payments.jsonl
├── ledger.jsonl
└── reconciler.jsonl
```

Each line is one observation:

```json
{"t": 0.00, "state": [1.2, 0.4]}
{"t": 0.05, "state": [1.3, 0.4]}
```

`t` is a monotonically increasing timestamp (seconds). `state` is the unit's
observable output vector at that moment. The filename stem must match the unit's
id in the dependency graph. See [trace-format.md](trace-format.md) for the full schema.

**Example:**

```sh
wt dynamic . /tmp/traces/
```

```
Regime (actual)    : Coherent
R_dyn (final)      : 0.8712
Holonomy violations: 1
  |hol|=0.0341  ["payments", "ledger", "reconciler"]
Aperture drift     : 0
```

A holonomy violation means the cycle's actual transformation diverged from its
declared specification. See [trace-format.md](trace-format.md) for how to supply
a non-identity cycle specification.

---

### `wt purpose [<project-dir>] <traces-dir>`

Runs Phase 3. Computes contribution scores and identifies purposeless units.

**What it computes:**
- `P_OR(E)` — the ensemble's probability of reaching the action-cell under representative load
- `δS(u, E) = P_OR(E) − P_OR(E \ {u})` for each unit — how much the ensemble loses when u is removed
- Purposeless units — units where `δS ≈ 0` (within `--alpha`)

A unit is purposeless if removing it does not measurably change what the
ensemble can achieve. This is distinct from being unused: a unit may execute
on every request and still contribute nothing to global purpose.

**Example:**

```sh
wt purpose . /tmp/traces/
```

```
P_OR (full)  : 0.8431
  reconciler                      δS=0.2103
  payments                        δS=0.1847
  ledger                          δS=0.0912
  audit_log                       δS=0.0000  [purposeless]
```

**Note:** contribution scores require one ablation run per unit (the system is
re-run without each unit in turn). For large ensembles this is O(n) runs.
The static phase provides a regime map without this cost.

---

### `wt run [<project-dir>] [<traces-dir>]`

Runs all three phases in sequence and writes the result to `.wt/output.json`.

```sh
# Static only (no traces)
wt run /path/to/project

# All three phases
wt run /path/to/project /path/to/traces/
```

Phases 2 and 3 are skipped gracefully if no traces directory is provided.

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Coherent or Phase-locked |
| 1 | Below Coherent (R < 0.80) |
| 2 | Error |

This makes `wt run` composable in CI pipelines:

```sh
wt run . && echo "coherent" || echo "degraded"
```

---

### `wt report [<wt-output.json>]`

Re-renders a saved result without re-running analysis.

```sh
# Use the result from the last `wt run` in the current directory
wt report

# Specify a file explicitly
wt report /path/to/output.json
```

---

### `wt init [<project-dir>]`

Forces a rebuild of the dependency graph and caches it to `.wt/graph.json`.
Use this after adding or removing units from the project.

```sh
wt init /path/to/project
```

Subsequent `wt` calls read the cached graph without re-indexing unless `--no-cache` is passed.

---

### `wt check <script.wt> [<project-dir>]`

Runs a `.wt` script: measures what the `analyse` block asks for, evaluates the
`assert` block, and exits with a code CI can branch on.

```sh
wt check analysis.wt
wt check analysis.wt /path/to/project --json
```

A bare `.wt` path is recognised without the subcommand, so `wt analysis.wt`
works too.

```
Script : analysis.wt
Scope  : SelfCheck

  FAIL  regime >= Coherent
        regime is HierarchicalCascade, required >= Coherent
  PASS  r_est >= 0.5
  SKIP  r_dyn >= 0.8
        no r_dyn — the dynamic phase did not run

2 passed, 1 failed, 2 skipped → fail
```

**Skipped is not passed.** An assertion whose input phase never ran is reported
as `Skipped`, never as a pass. A script asserting on `r_dyn` without a
`dynamic` phase is incomplete, not clean — and exit code 3 says so.

| Exit code | Meaning |
|---|---|
| 0 | All assertions passed |
| 1 | At least one assertion failed |
| 2 | The script did not parse, or the run errored |
| 3 | Incomplete — assertions were skipped because their phase never ran |

Treat 3 as a failure in CI unless you deliberately intend a partial run.

---

### `wt serve [<project-dir>] [--port N]`

Starts a local analysis engine on `127.0.0.1` so the web editor can run scripts
against your real source tree.

```sh
cd /path/to/your/project
wt serve
```

```
wt serve — local analysis engine
  project : /path/to/your/project
  address : http://127.0.0.1:7878
  token   : 8f3c1d…

Paste the token into the web app to connect.
```

Paste that token into the editor's engine badge, and **▶ Run** measures this
project. The verdict is byte-identical to what `wt check` produces for the same
script — both go through one measurement path, so a result you see in the
browser and a result CI produces cannot diverge.

Security properties, none of them configurable:

- Binds loopback only. Never `0.0.0.0`.
- Every request needs the token, which is regenerated on each start. Stop the
  server and the page can no longer read your source.
- CORS is an explicit allowlist, never `*`.
- The project root is fixed by the launch argument. Requests carry a *script*,
  never a path — so no request-supplied path is ever opened.

The token authorises reading this project's source. Treat it like one.

---

## All flags

| Flag | Default | Applies to | Meaning |
|---|---|---|---|
| `--json` | off | all | Emit machine-readable JSON instead of the coloured terminal output |
| `--no-cache` | off | static, dynamic, purpose, run, init | Ignore `.wt/graph.json`; rebuild the dependency graph from source |
| `--backend B` | `auto` | static, dynamic, purpose, run, init | Extraction backend: `treesitter`, `hf`, or `auto` |
| `--cycle-depth N` | 12 | static, run | Maximum cycle length for Johnson's enumeration algorithm |
| `--threshold T` | 0.5 | static, run | Static residual threshold for reporting cycle candidates |
| `--tol T` | 1e-6 | dynamic, run | Holonomy violation tolerance |
| `--dt T` | 0.1 | dynamic, run | Time step for the `R_dyn` time series |
| `--alpha A` | 0.05 | purpose, run | Significance level for purposelessness detection |
| `--port N` | 7878 | serve | Port for the local engine (loopback only) |

---

## Using `wt` from any repository

After `cargo install --path wt`, the binary is in `~/.cargo/bin/wt` and available
everywhere. From inside any project:

```sh
cd ~/projects/my-service

# Static scan of this project
wt static

# Full run with traces from a local directory
wt run . ./traces/

# Bare path — treated as `wt run <path>`
wt ~/projects/my-service
```

No configuration file is needed. Wind tunnel discovers source files by walking
the project directory and skips `target/`, `node_modules/`, `.git/`, `dist/`,
`__pycache__/`, and `.wt/` automatically.

---

## Machine-readable output

All subcommands accept `--json`. The schema is `WindTunnelMetric`:

```sh
wt run . --json | jq '.regime'
wt run . --json | jq '.r_est'
wt run . --json | jq '.holonomy_violations[] | select(.magnitude > 0.01)'
wt run . --json | jq '.contribution_scores | to_entries | sort_by(-.value)'
```

The JSON is also written to `.wt/output.json` after every `wt run`.

---

## VS Code integration

The `.vscode/` directory in this repository ships three files that wire `wt`
into VS Code with no manual setup:

### tasks.json — keyboard shortcut

`Ctrl+Shift+B` runs `wt static` on the current workspace immediately.

To pick a different task: `Ctrl+Shift+P` → **Tasks: Run Task** → choose from:

| Task label | What it runs |
|---|---|
| `wt: static` | `wt static <workspace>` — default build task |
| `wt: run (static only)` | `wt run <workspace>` — all phases, no traces |
| `wt: run (with traces)` | prompts for a traces directory, then runs all three phases |
| `wt: dynamic` | `wt dynamic <workspace> <traces>` |
| `wt: purpose` | `wt purpose <workspace> <traces>` |
| `wt: report` | re-renders `.wt/output.json` |
| `wt: init (rebuild graph)` | force-rebuilds the dependency graph |
| `wt: run --json` | full run, JSON output to the terminal |

Output always appears in the integrated terminal panel.

### settings.json — wt-shell terminal profile

`settings.json` defines a terminal profile called **wt-shell** (the beaker icon).
Open it with `Ctrl+Shift+\`` → dropdown arrow → **wt-shell**.

It automatically sources `.env.local` when the terminal starts, so `HF_TOKEN`
is set without you having to do anything. This works on Windows (PowerShell),
Linux, and macOS.

> `settings.json` is git-ignored — it lives only on your machine.
> `tasks.json` and `launch.json` are committed and travel with the repo.

### Using wt in your other VS Code projects

Copy `.vscode/tasks.json` into any other project:

```sh
cp /path/to/wind-tunnel/.vscode/tasks.json /path/to/other-project/.vscode/tasks.json
```

`${workspaceFolder}` expands to that project's root automatically — no edits needed.

For the HuggingFace token, copy `settings.json` too (or set `HF_TOKEN` in your
system environment once and it will be available everywhere):

```sh
# Windows — set permanently in user environment
[System.Environment]::SetEnvironmentVariable("HF_TOKEN", "hf_...", "User")

# Linux / macOS — add to ~/.bashrc or ~/.zshrc
export HF_TOKEN=hf_...
```

Once `HF_TOKEN` is in your system environment you never need to source
`.env.local` manually again.

---

## CI integration

Commit a `.wt` script and let it define the gate. The thresholds then live in
version control and change by review, rather than sitting in a CI comment where
nobody reads them.

```yaml
# GitHub Actions example
- name: Wind Tunnel
  run: |
    cargo install --path wt
    wt check analysis.wt --json > wt-report.json
```

The step fails on exit 1 (an assertion failed) and on exit 3 (assertions were
skipped, so the run proved less than it appears to). If you deliberately want a
partial run to pass, say so explicitly rather than ignoring the code:

```sh
wt check analysis.wt; code=$?
[ $code -eq 0 ] || [ $code -eq 3 ] || exit $code
```

```sh
# Pre-commit hook
#!/usr/bin/env bash
wt check analysis.wt || { echo "wt: assertions failed"; exit 1; }
```

---

## Output files

All output is written to `.wt/` inside the analysed project:

| File | Written by | Contents |
|---|---|---|
| `.wt/graph.json` | `wt init`, first run of any subcommand | Cached dependency graph |
| `.wt/output.json` | `wt run` | Full `WindTunnelMetric` for the last run |

Both files are git-ignored by the `.gitignore` in the wind-tunnel repository itself.
Add `.wt/` to the `.gitignore` of any project you analyse.

---

## Interpreting the regime map

The regime map is the primary output. It is not a pass/fail verdict.

**Turbulent or Aperture-dominated:** The units do not share a common action-cell.
Individual tests may pass. The system will produce semantically inconsistent
outputs under load. Start with the decoherence zones — they localise the worst
coupling mismatches. Fix interface contracts (aperture/production type alignment)
before worrying about holonomy.

**Hierarchical cascade:** There are coherent clusters but their interfaces are
lossy. The cycle candidates are the next thing to examine. Run the dynamic phase
on a representative workload to see whether the static candidates produce live
violations.

**Coherent:** The system is converging. Run the full protocol including Phase 3
(contribution scores). Look for purposeless units — they carry coupling cost
without contributing to the ensemble's action-cell.

**Phase-locked:** Partition extinction has occurred. Coordination friction is
zero. The system behaves as a single unit with respect to its declared purpose.
This is the target state.
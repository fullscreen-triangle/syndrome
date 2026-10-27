# Using Agent Smith (`smith`) in any repo

Agent Smith is the runnable core of the musande framework — the split-attention
synchronised-agents theory made executable. It ships as **two integration surfaces**,
so you pick the one that fits what you're doing:

| | **The `smith` CLI** | **The `agent_smith` crate** |
|---|---|---|
| **What it is** | An installed command-line binary | A Rust library you depend on |
| **Use it when** | You want to author, check, and run agent scripts from any repo/terminal | You want to instantiate and drive agents from inside your own Rust program |
| **Needs** | Nothing — offline, deterministic, no network | A Cargo project |

Both reach the same engine. Neither ships any domain competence: the language says *what*
an agent is for and *which scenes serve it*, never *how* a scene does its work — that is a
hook you supply. This is the same empty-store discipline as `purpose`.

The DSL, the four invariants, and the theory are documented in
[crates/agent-smith/README.md](agent-smith/README.md); this file is about **using the tool
from other repos**.

---

## Part 1 — The `smith` CLI in any repo

### 1.1 Install (once)

From the musande repo, install the binary onto your PATH — exactly as `purpose` was
installed:

```bash
cd /path/to/musande
cargo install --path crates/agent-smith --bin smith
```

Confirm:

```bash
smith --version        # -> smith 0.1.0
```

The binary is self-contained: no config, no network, no provider. It goes to
`~/.cargo/bin/smith` (`%USERPROFILE%\.cargo\bin\smith.exe` on Windows). Re-run the same
`cargo install` line to upgrade after changes.

### 1.2 Write a script

An Agent Smith script (`.smith`) declares an agent by its **purpose** and the **scenes**
that serve it. Save this as `smith.smith` in any repo:

```
// The iron smith — a CHARACTER: standing purpose, runs on.
agent smith {
  purpose minimise forge_residual
  scenes {
    scene hammer   serves forge_residual with forge_hook
    scene contract serves forge_residual with contract_hook
    scene source   serves forge_residual with source_ore_hook
  }
  self {
    parts { skill, stock, orders, reputation }
    separations {
      (skill, stock: 3), (stock, orders: 2),
      (orders, reputation: 2), (reputation, skill: 2)
    }
  }
  budget 1.0
  floor  2.0
  coherence keeps { reputation, skill }
}
```

`purpose reach <outcome>` instead of `minimise <potential>` makes a **task-agent** that
halts at quiescence rather than a character that runs on. Wrap several agents in a
`society <name> { agent … tie (a, b: cost) … couple <K> }` to coordinate them.

### 1.3 The three commands

```bash
smith check smith.smith                # parse + typecheck; report χ / floor / regime
smith run   smith.smith [--ticks N] [--json]   # build + drive the tick-loop
smith show  [town|task]  [--ticks N] [--json]  # run a bundled example end-to-end
```

**`check`** — validates a script and prints, per agent, its regime (character | task),
identity invariant `χ`, realised `floor`, and whether `χ` is non-local:

```
$ smith check smith.smith
✓ smith.smith — OK (agent, 1 agent(s))
  smith        regime=character χ=4     floor=4     non-local=true  side={skill | stock}
```

On a bad script it prints the type errors with line numbers and exits non-zero:

```
$ smith check broken.smith
✗ broken.smith — 2 error(s):
  line 4: separation (p, q) cost 1 is below the floor 2
  line 3: scene "s" serves "WRONG" but the agent's purpose is "goal" (no dead scenes: every scene must serve the one purpose)
```

**`run`** — builds the script and drives the tick-loop to quiescence (or `--ticks N`),
printing a per-tick table: agent, outcome (commit | observe | decline | quiescent),
attention price, residual, delta, count, scene. Add `--json` for machine-readable output.

**`show`** — runs a bundled example (`town` = a character + a pure observer in a society;
`task` = a task-agent that halts) end-to-end, so you can see the engine work with no script
to write.

**Exit codes:** `0` OK · `1` build/type error · `2` I/O error. Good for scripting and CI.

### 1.4 Wiring an AI agent to call `smith`

To let a Claude Code / MCP-style agent author and run agent scripts, allow the commands in
the target repo's `.claude/settings.json` (or `settings.local.json`):

```jsonc
{
  "permissions": {
    "allow": [
      "Bash(smith check:*)",
      "Bash(smith run:*)",
      "Bash(smith show:*)"
    ]
  }
}
```

Then instruct the agent: *"Author agent behaviour as an Agent Smith `.smith` script and
validate it with `smith check <file>`; run it with `smith run <file>`. The DSL declares an
agent by its purpose and the scenes that serve it — never by scripting its moves."*

---

## Part 2 — The `agent_smith` crate in a Rust project

Use the library when you want to instantiate and drive agents from inside your own program
(the CLI is a thin wrapper over exactly this API).

### 2.1 Depend on it

Point Cargo at the crate. Until it is published, use a path or git dependency in your
project's `Cargo.toml`:

```toml
[dependencies]
# path (same machine / monorepo):
agent-smith = { path = "/path/to/musande/crates/agent-smith" }

# or git:
# agent-smith = { git = "https://github.com/fullscreen-triangle/musande" }
```

The crate name is `agent-smith`; you `use agent_smith::…` (Rust turns the `-` into `_`).

### 2.2 Build and run a program

```rust
use agent_smith::{build, make_town, run_town, Ctx};

fn main() {
    let source = agent_smith::EXAMPLE_TOWN; // or your own script string

    // parse -> typecheck -> compile
    let built = build(source);
    if !built.ok {
        for e in &built.errors {
            eprintln!("{e}"); // Diagnostic { message, line }
        }
        return;
    }

    // drive the tick-loop, fully offline/deterministic
    let mut town = make_town(built.program.unwrap());
    let ctx = Ctx::deterministic();
    let history = run_town(&mut town, &ctx, 30); // Vec<StepResult>

    for step in &history {
        for rec in &step.records {
            println!("{} {} count={}", rec.agent, rec.outcome.as_str(), rec.count);
        }
    }
}
```

### 2.3 Plug in a model (the one seam)

The engine is deterministic everywhere except one point: the domain judgment (the JS
`providers.think`). That is the `Hook` trait. The default `DeterministicHook` runs the
whole thing offline; supply your own to route the domain work through an LLM (or any
computation):

```rust
use agent_smith::{Agent, Candidate, Ctx, Hook, HookResult, Slice};

struct MyHook;

impl Hook for MyHook {
    fn uses_model(&self) -> bool { true }

    fn run(&self, agent: &Agent, cand: &Candidate, slice: &Slice) -> Option<HookResult> {
        // do the domain work for this firing act; report its outcome.
        // Return None to fall back to the deterministic residual descent.
        Some(HookResult {
            reduction: Some(0.2),                 // how much residual this act removes
            content: Some(format!("{} did {}", agent.name, cand.scene)),
            model: Some("my-model".into()),
        })
    }

    fn judge_sufficiency(&self, _agent: &Agent, _slice: &Slice) -> bool {
        true // tier-1 gate: is the current state enough to act now?
    }
}

// then:
let ctx = Ctx::with_hook(Box::new(MyHook));
```

The crate itself holds no domain answers — only the seam where you supply them.

### 2.4 The useful surface

| Item | What it is |
|---|---|
| `build(&str) -> BuildResult` | parse + typecheck + compile in one call |
| `make_town(Program) -> Town` / `run_town(&mut Town, &Ctx, max_ticks)` | build and drive a run |
| `step_town(&mut Town, &Ctx) -> StepResult` | one tick of the whole town |
| `Ctx::deterministic()` / `Ctx::with_hook(Box<dyn Hook>)` | offline vs. model-backed |
| `Hook`, `HookResult`, `Candidate`, `Slice`, `DeterministicHook` | the model seam |
| `character_invariant`, `realised_floor`, `water_fill`, `LogGain` | the paper's math, exposed directly |
| `EXAMPLE_TOWN`, `EXAMPLE_TASK` | ready-to-run scripts |

---

## Which surface answers which need

- *"Let me author and run agent scripts from my shell / any repo / CI."* → **the `smith`
  CLI** (Part 1).
- *"Let my Rust program instantiate agents and drive their tick-loop."* → **the
  `agent_smith` crate** (Part 2).
- *"Route the agents' domain work through a model."* → the crate's **`Hook` trait**
  (§2.3); the CLI stays deterministic by design.

## Verifying an install

From the musande repo:

```bash
cargo test -p agent-smith          # fidelity tests (χ witness, water-filling, runtime)
smith show task                    # a bundled task-agent halting at quiescence
smith show town                    # a character + a pure observer coordinating
```
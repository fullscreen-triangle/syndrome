# Sango Rine Shumba — Fleet Usage Guide

`srn-fleet` is the **agent + compute-allocation layer** of Pylon. It implements the two
papers together — `network-yield-computing-allocation.tex` (the compute market: yield
clearing, separation prices `sep(e)`) and `split-attention-agents.tex` (the agent:
character `χ`, water-filling attention, monotone count, recall-as-search, Kuramoto
society) — as a callable Rust CLI over three real machines reached by SSH: an always-on
**chromebook**, a cheap bulk **hertzner** (Hetzner) node, and an elastic **vultr** burst
node that the market summons on stall.

This guide covers four things:

1. [Generating and wiring Vultr machines](#1-generating-and-wiring-vultr-machines)
2. [Using the web app in isolation](#2-using-the-web-app-in-isolation) (Panthera)
3. [Using the Rust tool in isolation](#3-using-the-rust-tool-in-isolation) (`srn-fleet`)
4. [Integrating with Buhera OS](#4-integrating-with-buhera-os) — web (TS/WASM) and Rust

> **Status legend.** ✅ built and tested · 🟡 wired but gated (needs your credentials) ·
> 📐 contracted / planned (the design is fixed; the code is not written yet). The Rust
> tool (§3) is fully ✅. The Vultr *decision* layer is ✅; live provisioning is 🟡. The
> web app's mesh control center (§2) and the Buhera OS integration (§4) are 📐 — the
> contracts exist (`panthera/docs/buhera-pylon.md`), the surfaces are not yet built.

---

## Prerequisites

- **Rust** ≥ 1.75 (`rustup`, stable).
- **OpenSSH client** (`ssh` on `PATH`) — the fleet dispatches by shelling out to it.
- **curl** on `PATH` — used for the Vultr API (no HTTP library is linked in).
- The three machines reachable by **key-based** SSH (no password prompts): the fleet runs
  `ssh -o BatchMode=yes`, which fails fast rather than hang on a prompt.

Build once:

```bash
cd pylon/crates/srn-fleet
cargo build --release
# binary: crates/srn-fleet/target/release/srn-fleet
```

For brevity this guide calls it `srn-fleet`; use the full path or add it to `PATH`.

---

## 1. Generating and wiring Vultr machines

Vultr is the **burst** slot: latent until the market's separation price crosses a
threshold, then summoned, then destroyed when the pressure clears. There are two ways to
bring one up — do it **once by hand** to wire the account, then let the fleet do it
**automatically**.

### 1.1 One-time account setup

1. **Create a Vultr account** and generate a **Personal Access Token**:
   Vultr console → *Account → API → Enable API → Personal Access Token*. Copy it.
   Also add your workstation's public IP to the API **access control** allow-list, or the
   token is rejected.

2. **Upload an SSH key** so summoned instances trust the fleet:
   Vultr console → *Account → SSH Keys → Add SSH Key*. Paste your `~/.ssh/id_ed25519.pub`
   (the same key whose private half your fleet host holds). Note the **SSH Key ID** — the
   long UUID Vultr shows next to the key. The fleet installs this key on every burst node
   so it can `ssh root@<burst-ip>` with no password.

3. **Pick a region, plan, and OS id.** You can list them with your token:

   ```bash
   export VULTR_API_KEY=your_token_here

   # regions (id like "fra" = Frankfurt, "ewr" = New Jersey)
   curl -s -H "Authorization: Bearer $VULTR_API_KEY" \
        https://api.vultr.com/v2/regions | python -m json.tool | less

   # plans (id like "vc2-1c-1gb" = 1 vCPU / 1 GB)
   curl -s -H "Authorization: Bearer $VULTR_API_KEY" \
        https://api.vultr.com/v2/plans | python -m json.tool | less

   # OS ids (Ubuntu LTS is a safe default; note its `id`)
   curl -s -H "Authorization: Bearer $VULTR_API_KEY" \
        https://api.vultr.com/v2/os | python -m json.tool | less
   ```

   Reasonable defaults the tool ships with: `--region fra --plan vc2-1c-1gb --os-id 1743`.
   Confirm `1743` is still a current Ubuntu LTS in the `os` listing above; if not, use the
   id you found.

### 1.2 Declare Vultr as a latent burst slot

The fleet's **only** domain-facts file is `.srn/sources.toml`. Declare Vultr there with an
**empty `ssh`** — that marks it latent (its host is assigned only when summoned) and
`role = "burst"`:

```toml
# .srn/sources.toml   (copy from crates/srn-fleet/examples/sources.toml)

[[source]]
name = "chromebook"
ssh = "user@chromebook.local"     # your always-on low-latency node
cost_per_hour = 0.0
capacity = 2
role = "always-on"

[[source]]
name = "hertzner"
ssh = "root@1.2.3.4"              # your cheap bulk node (real user@host)
cost_per_hour = 0.02
capacity = 8
role = "always-on"

[[source]]
name = "vultr"
ssh = ""                          # latent — host filled in when summoned
cost_per_hour = 0.18
capacity = 4
role = "burst"
```

### 1.3 The summon decision (always safe, no money spent)

Whether to summon is a **pure decision** from the cleared market, and you can inspect it
without any credential. The trigger is deliberately sharp: a burst fires **only when the
fleet is saturated** (acts left unplaced) **and the price is rising over rounds** — not
merely because one slot happens to be the cheapest (comparative advantage alone never
summons):

```bash
srn-fleet burst --acts acts.toml --summon-at 2.0 --destroy-at 0.5
# prints sep(e) per slot, the unplaced count, and DECISION: SUMMON | HOLD | DESTROY
```

### 1.4 Provisioning for real — the double gate 🟡

Real provisioning spends money and creates a real machine, so it is guarded by **two
independent locks**. Nothing bills you unless **both** are satisfied:

| Lock | How to satisfy |
|---|---|
| `VULTR_API_KEY` present | `export VULTR_API_KEY=your_token` |
| `--live` flag passed | add `--live` to the `burst` command |

A key **alone** stays dry-run. `--live` **alone** (no key) stays dry-run. Only together do
they arm the client. When armed and the decision is `SUMMON`, the fleet:

1. `POST`s to `https://api.vultr.com/v2/instances` (via `curl`, auth header piped through
   `-K -` so the token never appears in the process list),
2. polls `GET /v2/instances/{id}` until the instance has a routable `main_ip`,
3. prints `root@<ip>` for you to paste into `sources.toml`'s `vultr` entry (replacing the
   empty `ssh`), after which `srn-fleet index` and `srn-fleet run` dispatch to it.

```bash
export VULTR_API_KEY=your_token_here
srn-fleet burst --acts acts.toml \
  --summon-at 2.0 --destroy-at 0.5 \
  --live \
  --region fra --plan vc2-1c-1gb --os-id 1743 \
  --sshkey <your-vultr-ssh-key-uuid>
```

**Tearing down.** A summoned node keeps billing until destroyed. When the market says
`DESTROY` (slack returned, price settled), destroy it by id:

```bash
curl -s -X DELETE -H "Authorization: Bearer $VULTR_API_KEY" \
     https://api.vultr.com/v2/instances/<instance-id>
```

(The fleet's `VultrClient::destroy` performs exactly this call; the CLI currently prints
the destroy *decision* and leaves the teardown to you so an id is never guessed. Wire it
into your own loop once you trust the thresholds.)

> **Safety.** Set conservative thresholds first and watch `burst` (without `--live`) for a
> few real workloads before arming it. A too-low `--summon-at` on a fleet that is merely
> using its cheapest node will still `HOLD` (because nothing is unplaced), but verify that
> on your own act mix before turning on `--live`.

---

## 2. Using the web app in isolation

The web app is **Panthera** (`panthera/`), a Next.js *pages-router* app. Today it hosts
the two papers as an interactive publication (`about`, `framework`, `state`, `trajectory`,
`validation`, `demo`, …). The **mesh / fleet control center** — the browser surface for
`srn-fleet` — is **📐 contracted but not yet built**; the plan lives in
`project_mesh_control` memory and the API shape below is what it will expose.

### 2.1 Run Panthera as it is today

```bash
cd panthera
npm install
npm run dev        # http://localhost:3000
```

This gives you the publication and demos with no fleet, no cluster, no SSH — the app
standing entirely on its own. Use this to read/annotate the theory or show the papers.

### 2.2 The planned fleet control surface 📐

The intended architecture (from `project_mesh_control` and `buhera-pylon.md`) puts a
`/mesh` (or `/cluster`) page in Panthera that talks to the fleet through Next.js API
routes — the browser never holds SSH or Vultr secrets:

```
Panthera browser UI  (/mesh page)
    │
    ├── /api/srn      → srn-node HTTP API (:7700) on each device
    ├── /api/fleet    → srn-fleet (clear / attend / burst / kuramoto)
    └── /api/metrics  → Prometheus (:9090) on the always-on node
```

The page shows: every node with its frame `(n,ℓ,m,s)`, capacity, and current price; the
network **yield** and the Kuramoto **phase-lock** indicator in the header; and the live
process-agents, each linking to its detail view. This is the browser mirror of §3's
`clear`, `attend`, `burst`, and `kuramoto` commands.

To build it (when you get to it), the memory note `project_mesh_control` lists the exact
files to add under `panthera/src/pages/api/` and `panthera/src/components/mesh/`; read
`panthera/src/pages/framework.js` and `Navbar.js` first to match the existing style.

**Bridge that exists today:** `srn-node` already serves an HTTP API on `:7700`
(`GET /status`, `POST /eval`, `GET /peers`, `GET /network/probe`, …). A `/api/srn` route
proxying to it is the smallest first step and needs no new Rust.

---

## 3. Using the Rust tool in isolation ✅

This is the fully-built path. Everything here works today with nothing but the three
machines (and even without them, in dry-run/demo form).

### 3.1 The mental model

Two markets stacked, joined at the **act**:

- **Lower (compute) market** — clears *acts* (shell commands with a work estimate) onto
  *slots* (measured machines) by **yield** = progress per unit resource. The clearing
  price is the **separation cost** `sep(e)`: high where a slot is a bottleneck, zero where
  it is redundant.
- **Upper (attention) market** — an *agent* water-fills its bounded attention budget
  across its *scenes* at a single price `p★`; low-richness scenes are dropped when busy.
- **Society layer** — nodes are oscillators; the **Kuramoto** order parameter `r` measures
  phase coherence, and a node out of phase beyond tolerance is a **fault** (not something
  to optimise away — something to flag).

State lives in `.srn/` (git-ignored): authored agents, an append-only monotone history
log per agent (the incorruptible life-count `m`), and the one facts file `sources.toml`.

### 3.2 First run

```bash
cd your-project
srn-fleet init                 # creates ./.srn/
cp path/to/examples/sources.toml .srn/sources.toml   # then edit real user@host
srn-fleet sources              # show the declared slot set E
```

### 3.3 The compute market — `index`, `clear`, `run`

```bash
# Measure the real machines over SSH → cores, latency, throughput per slot.
srn-fleet index

# Author a batch of acts (shell commands + work estimates); see examples/acts.toml:
#   [[act]]
#   id = "smith:forge:1"
#   command = "echo forging; sleep 1"
#   work = 50.0

# Decide placement by yield (comparative advantage), with separation prices — runs nothing:
srn-fleet clear --acts acts.toml

# Clear AND dispatch: SSH-run each act on its chosen slot, read exit/residual back.
srn-fleet run --acts acts.toml
#   exit 0  → residual 0      (act completed)
#   exit ≠0 → residual = work (stalled — a price signal that can summon burst capacity)
```

If no machine is reachable, `index` degrades to "unreachable" per slot rather than
crashing, and `clear` shows the acts as unplaced — safe to run anywhere.

### 3.4 The agent layer — `agent new|list|show|ask|tick|verify`

An agent is an authored **self-graph** (parts + separation costs; see `examples/smith.toml`
— two lobes joined at one edge, so its character `χ` is non-local). The tool computes `χ`
and holds it invariant across sessions.

```bash
srn-fleet agent new smith --graph examples/smith.toml   # prints χ, m=0
srn-fleet agent list                                    # id, χ, m, phase
srn-fleet agent show smith                              # graph, χ, m, drive, scenes, split

# Recall-as-search: a residual-descending walk to a structural terminus (part + m).
# It is NOT a fetch — every ask commits an act, so m advances and identical queries evolve.
srn-fleet agent ask smith "what are you forging"        # → terminus + walk + m
srn-fleet agent ask smith "what are you forging"        # → different m (ever-fresh)

# Re-check the four unconditional invariants (identity/count/search/phase) on disk:
srn-fleet agent verify smith                            # ALL INVARIANTS HOLD
```

Kill the process and `agent show smith` again — `m` is preserved (never reset). A second
agent from the *same* graph has equal `χ` but starts at `m=0`: a distinct individual.

### 3.5 The attention market — `attend`

```bash
srn-fleet attend smith --slots 10
# prints the attention price p★, and the integer dispatch-mass split across the agent's
# scenes (largest-remainder). A busy agent drops its lowest-richness scenes — the correct
# T2 reading: presence follows richness, not fairness.
```

### 3.6 The burst decision — `burst`

Covered in §1.3–§1.4. Without `--live` it is a pure, free inspection of whether the market
wants to summon Vultr.

### 3.7 The society layer — `kuramoto`

```bash
srn-fleet kuramoto --phases examples/node_phases.toml --tol-deg 30
```

Each `[[node]]` gives its phase either directly (`theta`) or as a heartbeat triple
(`now_ns`, `last_tick_ns`, `period_ns`) the tool derives θ from — no new clock is
introduced; a node's phase is just how far it is through its own heartbeat interval. Output
is the order parameter `r` (1 = locked, 0 = scattered), the mean phase ψ, and any
**desync faults**. The command exits non-zero (`3`) when a fault is present, so it composes
into health checks.

### 3.8 See it all with no machines — the demo

```bash
cd crates/srn-fleet
cargo run --example market_demo
```

Prints the full compute market (comparative-advantage placement, `sep(e)`, an overload
that raises prices), the **sharper burst controller** across rounds (seated-with-rising
price → *Hold*; saturating → *Summon*; relief → *Destroy*), and a **Kuramoto** coherence
report — all self-contained, no SSH, no credentials.

### 3.9 Command reference

| Command | What it does | Touches machines? |
|---|---|---|
| `init` | create `.srn/` | no |
| `sources` | show the declared slot set `E` | no |
| `index` | SSH-probe sources → measured slots | yes (read) |
| `clear --acts <f>` | placement plan + `sep(e)` | yes (probe) |
| `run --acts <f>` | clear then SSH-dispatch the acts | yes (execute) |
| `agent new\|list\|show\|ask\|tick\|verify` | the persistent agent layer | no |
| `attend <id> --slots N` | water-fill attention → dispatch mass, `p★` | no |
| `burst --acts <f> [--live …]` | Vultr summon/hold/destroy decision (+ provision) | probe; `--live` provisions |
| `kuramoto --phases <f> --tol-deg D` | phase coherence `r`; desync-as-fault | no |

---

## 4. Integrating with Buhera OS

Buhera OS (the **long-grass** surface) already carries a written contract for Pylon:
`panthera/docs/buhera-pylon.md`, package identity **`@buhera/pylon`**. The load-bearing
idea there is the same one this fleet is built on: **an allocated compute packet IS an
agent** — the same runtime shape musande gives vocational NPCs. So `srn-fleet` is the Rust
realization of that contract, and integration means exposing it under the `@buhera/pylon`
API the OS expects.

Buhera OS is layered, and Pylon is the bottom runtime layer:

```
long-grass (OS surface: names, dispatches, audits; the terminal + /town + /cluster)
    │  dispatches via module DSLs
    ▼
@buhera/musande  (vocational agents — smiths, scribes; χ, attention, Kuramoto)
    │  a stalled scene raises its felt drive
    ▼
@buhera/pylon    (compute-allocation agents — THIS fleet; yield market at τ₀, SRN wire)
```

There are two realizations to wire — a **web (TS/WASM)** surface the browser and Node
routes consume, and a **Rust** core for cluster deployment. The design is fixed by the
contract; below is how each maps onto what already exists in `srn-fleet`.

### 4.1 The Rust version (cluster core)

`srn-fleet` + `srn-node` already provide the machinery the `@buhera/pylon` contract §6–§7
describes; the integration is a **thin adapter**, not a rewrite:

| `@buhera/pylon` contract (`buhera-pylon.md`) | Existing srn-fleet / srn-node piece |
|---|---|
| `clearMarket(agents, nodes, tick)` → assignment + prices | `clearing::clear()` → `Plan { placements, separation }` |
| `separationCost(node, …)` = `sep(e,A)` | `clearing::separation_costs()` |
| yield-market price `p(e)` | `Plan.separation` (`sep(e)`) |
| process agent with monotone `M(t)` | `agent::Agent` + append-only `store` history (`m`) |
| four invariants (χ, m, search, phase) | `identity`, `agent`/`store`, `search`, `phase` |
| Kuramoto order parameter `R`, phase-lock ≥ 0.95 | `kuramoto::coherence()` → `r`, `is_locked()` |
| liveness: stalled queue raises price, summons capacity | `dispatch` residual + `vultr::BurstController` |
| SRN as the transmission unit; receiver-relativity | `srn-node` (`expression`, `coords`, `registry`, `propagation`) |

**What to build:** a crate (e.g. `crates/pylon-core` or a feature on `srn-fleet`) that
implements the `Cluster` operations over these, speaking **SRN expressions** on the wire
(the contract forbids JSON/gRPC between nodes — `srn-node` already encodes/decodes SRN, so
reuse it) and enforcing the non-negotiables in §5 of the contract: the mandatory `not`
boundary, monitor–control separation, and the read-only `τ₀`. The scheduler, prices,
agents, and Kuramoto are done; the missing piece is the SRN-expression front door and the
`Cluster` façade.

**Deployment shape:** run one `srn-node` per machine (already proven live over Tailscale:
laptop ↔ chromebook), and `srn-fleet` as the allocator that clears acts across them. A
Vultr burst node, once summoned and added to `sources.toml`, is just another slot — Forest
openness (SRN Thm 8.1): any SRN-capable machine is a peer, no enrolment.

### 4.2 The web version (TS / WASM)

Long-grass consumes **only** the TS/WASM surface (`buhera-pylon.md` §3); the Rust core is a
deployment detail behind it. Two build routes:

- **WASM core (faithful).** Compile the Rust market/agent/Kuramoto core to WebAssembly and
  expose the `@buhera/pylon` §6 API (`parseSrn`, `encodeTrajectory`, `clearMarket`,
  `Cluster`, re-exporting `Agent`/`AgentId` from `@buhera/musande`). This runs the real
  clearing and χ/`m`/Kuramoto logic in the browser for the single-machine demo, and the
  same code deploys to the cluster. `buhera-os/spraypaint-ts` is the existing TS workspace
  to house the bindings.
- **Node proxy (cluster).** For real cluster runs the browser can't SSH, so the TS
  `Cluster.submit()` posts to a Next.js/long-grass API route (`src/pages/api/pylon/submit.js`
  in the contract, §10.3) that validates the SRN expression parses (rejecting any missing
  its `not` boundary) and forwards to the Rust `srn-fleet` allocator server-side. Secrets
  (SSH keys, `VULTR_API_KEY`) stay on the server; the browser only ever sees cell indices
  and prices (Structural Incorruptibility, contract §5.6).

The long-grass-side files are enumerated in `buhera-pylon.md` §10 (`src/lib/cluster/pylon.js`,
`pylon-module.js`, `audit-feeder.js`, `src/pages/cluster/index.js`, terminal `:cluster` /
`:srn`). Per that document, long-grass does **zero** prep work until Pylon ships a
`@buhera/pylon` v0.1 — so the sequencing is: **(a)** stand up the WASM/TS surface over this
fleet, publish it as `@buhera/pylon`, then **(b)** long-grass wires §10 in one focused
session.

### 4.3 Where Panthera's `/mesh` fits

Panthera's planned `/mesh` page (§2.2) and long-grass's `/cluster` page (contract §10.5)
are the **same view at two front doors** — nodes with frames, prices, yield, phase-lock,
live agents. If you build the Next.js API routes for Panthera first (`/api/fleet`,
`/api/srn`), the same route handlers transfer almost directly to long-grass's
`/api/pylon/*`, since both wrap the same `srn-fleet` / `srn-node` surfaces. Building the
Panthera control center is therefore not wasted work — it is the first, standalone half of
the Buhera OS web integration.

### 4.4 Minimal first integration milestone

The contract itself names the useful early target (§17): *"exercise the SRN structural
requirements as soon as pylon can parse+evaluate a single expression in a browser, before
cluster capability lands."* Concretely:

1. Expose `parseSrn` (rejecting missing-`not`) + a single-node `submit` from the WASM core.
2. Prove **receiver-relativity** and **replay immunity** (`M` advanced) on one node — both
   already hold in `srn-node`/`agent`.
3. Only then add multi-node clearing (already in `clearing`) and the `/cluster` view.

That gives Buhera OS a real, standalone "distributed compute" demo without waiting on the
full town integration, and every piece it needs already exists in this repo — it needs
wrapping in the `@buhera/pylon` shape, not inventing.

---

## Appendix — file & state reference

| Path | Role |
|---|---|
| `.srn/sources.toml` | the ONE facts file: your machines (slot set `E`) |
| `.srn/agents/<id>.toml` | an authored agent (self-graph, drive, budget, scenes, state) |
| `.srn/history/<id>.log` | append-only monotone `m` — the incorruptible life-count |
| `crates/srn-fleet/examples/sources.toml` | template manifest (copy, then edit) |
| `crates/srn-fleet/examples/acts.toml` | example act batch for `clear`/`run` |
| `crates/srn-fleet/examples/smith.toml` | example agent self-graph (non-local χ) |
| `crates/srn-fleet/examples/node_phases.toml` | example node phases for `kuramoto` |
| `crates/srn-fleet/examples/market_demo.rs` | `cargo run --example market_demo` — full demo, no SSH |
| `panthera/docs/buhera-pylon.md` | the `@buhera/pylon` integration contract (§4 above) |

**Environment variables**

| Var | Used by | Effect |
|---|---|---|
| `VULTR_API_KEY` | `burst --live` | credential for real Vultr provisioning (one of two gates) |

Nothing in the fleet reads scheduling policy from the environment or a config file — the
theorems are the policy, and `sources.toml` is the only place domain facts live.
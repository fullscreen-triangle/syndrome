# Syndrome

**Categorical Resolution of Biological Dynamics: A First-Principles Framework
for Cellular State, Disease, and Therapeutic Intervention**

Kundai Farai Sachikonye
AIMe Registry for Artificial Intelligence · Technical University of Munich ·
School of Life Sciences Weihenstephan
`kundai.sachikonye@bitspark.com`

---

## Abstract

Conventional disease modelling treats pathology as deviation from a fixed
homeostatic reference. This repository develops the consequences of denying
that a fixed reference exists. At finite temperature a cell is a bounded
dynamical system whose constituents transition faster than any measurement
that could fix their state; the reference against which "deviation" would be
measured is not merely unknown but unconstructible from within the system.

From two axioms — that a physical system of finite energy and extent occupies
a bounded phase space, and that an observer of finite resolution partitions
that space into equivalence classes — we derive a framework in which
observation, computation, and processing are the same operation: resolution
of a categorical address. Disease is then not a distance from health but a
**failure of loop closure**: the holonomy of a state trajectory around a
cycle in the cell's reaction network, which vanishes identically when the
network is thermodynamically consistent and is nonzero exactly when it is
not.

This reformulation is productive rather than merely descriptive. It yields a
positive epistemic floor below which no observer — cell, instrument, or
clinician — can resolve state; it makes diagnosis a *localisation* problem
and therapy a *gap-closure* problem on the same object; and it applies
without modification to molecular recognition, viral infection, pathogen
surveillance, and the epidemiology of coordinated agent ensembles, each of
which reduces to the same primitive.

The repository contains the theory, its formal development as a monograph,
executable implementations in Python and Rust, a domain-specific language
with a type system that makes an unjustified diagnostic claim ungrammatical,
and a validation suite of 101 numerical experiments.

---

## 1. Theoretical foundation

### 1.1 Axioms

> **Axiom 1 (Bounded phase space).** A physical system with finite energy
> *E* < ∞ and finite spatial extent *L* < ∞ occupies a bounded region Ω of
> phase space with finite measure μ(Ω) < ∞.

> **Axiom 2 (Categorical observation).** An observer of finite resolution
> partitions Ω into equivalence classes {Ωᵢ}. States *x*, *y* ∈ Ω lie in the
> same class if and only if no measurement available to the observer
> distinguishes them.

Everything below is derived from these two statements together with standard
thermodynamics. No parameter in the framework is fitted to the phenomena it
is used to explain; where a constant appears, §4 states where it comes from.

### 1.2 Partition geometry

Categorical partitioning of a bounded spherical phase space is not free. It
generates exactly four coordinates —

| Coordinate | Symbol | Range |
|---|---|---|
| Depth | *n* | *n* ≥ 1 |
| Complexity | ℓ | 0, …, *n*−1 |
| Orientation | *m* | −ℓ, …, +ℓ |
| Chirality | *s* | ±½ |

— with partition capacity *C*(*n*) = 2*n*². The derivation is a
necessity argument, not an analogy to atomic structure: the coordinates are
forced by the requirement that a finite-resolution observer partition a
bounded space consistently.

### 1.3 The epistemic floor

An observer embedded in the system it observes cannot reduce its own
resolution limit to zero. The floor is strictly positive, and it is not a
technological limitation. Three consequences follow, developed in
`publication/disease-epistemology/`:

1. **Floor positivity.** Every bounded receiver has a strictly positive
   resolution floor.
2. **Group blindness.** An ensemble of such receivers does not average its
   way below the floor; coordination changes what is measurable, not how
   finely.
3. **Self-consistency primacy.** Because no external reference is available,
   the only admissible test is whether a system is consistent *with itself*.

The third point is the load-bearing one. It is why the diagnostic primitive
in this framework is loop closure rather than comparison to a healthy
control.

### 1.4 Triple equivalence

For bounded, measure-preserving dynamical systems the oscillatory,
categorical, and partition descriptions are isomorphic,

    O(Ω) ≅ C(Ω) ≅ P(Ω),

unified by the entropy identity *S* = *k*_B *M* ln *n*. The practical
consequence is the identity

    Obs(x) ≡ Comp(x) ≡ Proc(x):

computing a trajectory resolves the same categorical addresses that
observing it would resolve, so a computed trajectory has the same epistemic
status as an observed one. This is what licenses the computational programme
in §3.

### 1.5 Opacity independence

Categorical distance *d*_cat is a metric on partition space, provably
independent of spatial distance and of optical depth. States that are
categorically proximate remain resolvable through tissue, membrane, or
scattering medium — the barrier that defeats photon transport does not act on
categorical addresses. This is the basis of the multimodal localisation
results in `docs/multimodal-reaction-localization/`.

---

## 2. Disease formalism

### 2.1 Coherence

For an oscillator *O* with performance metric Π,

    η = (Π_obs − Π_deg) / (Π_opt − Π_deg),    η ∈ [0, 1],

with η = 1 full coherence and η = 0 none. Eight oscillator classes span the
cellular frequency range across eighteen decades:

| Class | Type | Frequency | Metric |
|---|---|---|---|
| P | Protein | 10¹³–10¹⁴ Hz | folding cycles *k* |
| E | Enzyme | 10⁶–10¹² Hz | turnover *k*_cat |
| C | Channel | 10³–10⁶ Hz | open probability *P*_o |
| M | Membrane | 10²–10³ Hz | amplitude Δ*V* |
| A | ATP | 0.1–1 Hz | frequency *f* |
| G | Genetic | 10⁻³–10⁻¹ Hz | burst rate λ |
| Ca | Calcium | 10⁻²–10⁰ Hz | regularity ρ |
| R | Circadian | 10⁻⁵ Hz | period stability σ_T⁻¹ |

Cellular coherence is the weighted mean η_cell = (1/*W*) Σᵢ *w*ᵢ ηᵢ, and the
disease vector is **D** = (1 − ηᵢ)ᵢ over the eight classes, classified by its
dominant component.

### 2.2 Disease as holonomy

The coherence vector describes *how much* is wrong. The topological
formulation describes *where*, and is the one that supports intervention.

Write a metabolic network at steady state as a resistive circuit: chemical
potentials μ = μ° + *RT* ln *c* are node voltages, conductances *G* = *kc*/*RT*
are branch conductances, and fluxes *J* = *G* Δμ are branch currents.
Kirchhoff's voltage law becomes the Wegscheider condition, and the sum of
potential differences around any cycle vanishes **identically** for a
thermodynamically consistent network — an algebraic identity, not an
approximation.

Disease is the failure of that identity. A nonzero cycle sum witnesses
inconsistency; *which* cycles are nonzero localises it. Two theorems govern
the localisation:

- The **verdict** is basis-independent — a network is consistent or it is
  not, whatever cycle basis is chosen.
- The **localisation** is not. The flagged cycle set depends on the basis.
  What survives is the **witness set**: the edges lying on every flagged
  cycle of a minimum cycle basis.

A third structural result, the **No Template Theorem**, states that no fixed
healthy reference can be constructed for such a network — which is the §1.3
floor argument arriving again from the topological side.

### 2.3 The tolerance problem

A cycle-sum test requires a tolerance ε below which a sum counts as zero.
Standard practice fixes ε at a round number (10⁻⁶ is typical) and treats it
as a solver property. `cause-for-concern/docs/disease-circuit-tolerance/`
shows this is a category error and replaces it.

Because the cycle sum of a consistent circuit is identically zero, its
computed value is *pure numerical noise*, whose scale is not a constant but
grows with cycle length ℓ and potential range Λ:

    ε_num(ℓ) ≤ γ_ℓ Λ,    γ_ℓ = ℓu / (1 − ℓu).

A second floor propagates the reported uncertainty of the thermodynamic data
through the same sum, giving ε_data. The **cycle-local tolerance** is

    ε*(ℓ) = max{ ε_num(ℓ), ε_data(ℓ) },

under which the test has a numerical false-positive rate bounded by the
arithmetic alone and detects every perturbation exceeding 2ε*. Neither
bound is available under a fixed tolerance.

The resulting classification is necessarily **three-valued**, and the third
value is not optional:

| Verdict | Condition |
|---|---|
| `CONSISTENT` | \|H\| ≤ ε_num |
| `UNDECIDABLE` | ε_num < \|H\| ≤ ε_data |
| `INCONSISTENT` | \|H\| > ε* |

A cycle whose sum falls between the floors is undecidable *from the data
supplied*; reporting it as either consistent or inconsistent is unwarranted.

### 2.4 A corrected prediction

The manuscript records a failed prediction rather than removing it. We
predicted that a fixed ε = 10⁻⁶ would fail two-sidedly. In IEEE-754 binary64
the failure is **one-sided**: rounding error tops out near 3 × 10⁻¹² even at
ℓ = 30, Λ = 3000, six orders of magnitude below the fixed tolerance, so it
manufactures no false positives at all. Its measured costs are instead total
insensitivity to defects below itself and unwarranted `INCONSISTENT` verdicts
on cycles whose defect lies inside the data's own uncertainty. The predicted
two-sided failure does appear, rising with ℓΛ as the theory requires, once
precision falls: repeating the null in binary32 gives false-positive rates
of 0.18 to 0.77 across strata.

---

## 3. Repository structure

```
syndrome/
├── monograph/          Book-length formal development (16 chapters, 5 parts)
├── publication/        Standalone papers: framework, epistemology,
│                       fuzzy circuits, state equations, hardware
├── diseases/           Domain applications: diagnosis, viruses,
│                       pathogen biology, immunology, social mechanics
├── docs/               Foundational theory and source derivations
├── cause-for-concern/  The CFC language: paper, prototype, webtool
├── syndrome/           Python implementation and validation suite
├── syndrome-rs/        Rust implementation of the core algorithms
├── results/            Validation output (JSON/CSV), 101 tests
└── disco-macabre/      Documentation site and interactive tools
```

### 3.1 The monograph

`monograph/` consolidates the framework into a single volume, *The Blind
Leading the Blind*, in five parts:

| Part | Chapters | Subject |
|---|---|---|
| I Foundations | 1–2b | Axioms, S-entropy calculus, epistemic floors, multi-agent coordination |
| II The Healthy Cell | 3–6 | Cellular state equations, observational algebra, Poincaré computing, multimodal localisation |
| III Disease | 7–8, 10–14 | Disease state equations, fuzzy circuits, viral resonance, pathogen surveillance, immunology, social mechanics, the CFC language |
| IV Therapeutic Intervention | 9, 15 | Therapeutic effect as loop-closure restoration; the intervention hierarchy |
| V Synthesis | 16 | — |

Build with `pdflatex main.tex` in `monograph/`.

### 3.2 Standalone papers

| Path | Subject |
|---|---|
| `publication/disease-computing/` | The framework paper |
| `publication/disease-epistemology/` | Floors, group blindness, self-consistency primacy |
| `publication/disease-fuzzy-circuits/` | Sequential constraint propagation in fuzzy cellular circuits |
| `publication/disease-state-equations/` | Partition-based disease state equations |
| `publication/hardware/` | Oscillator interference, shader holonomy, spectroscopic derivation |
| `diseases/infectious-diseases/` | Viral infection as host-state-dependent categorical resonance |
| `diseases/pathogen-biology/` | Spectral pathogen surveillance |
| `diseases/universal-immunology-primitive/` | Molecular recognition as oscillator interference |
| `diseases/social-mechanics/` | Template matching in coordinated agent ensembles |
| `diseases/disease-diagnosis/` | The Cause-for-Concern grammar |
| `cause-for-concern/docs/disease-circuit-tolerance/` | Cycle-local tolerance for the KCL consistency test |

---

## 4. Implementation

### 4.1 Core algorithms

| Algorithm | Input → output | Complexity |
|---|---|---|
| `COHERENCE` | Π_obs, Π_opt, Π_deg → η ∈ [0,1] | O(1) |
| `CELLULAR_COHERENCE` | weighted oscillators → η_cell | O(N) |
| `DISEASE_VECTOR` | oscillators by class → **D** ∈ [0,1]⁸ | O(N) |
| `CLASSIFY` | **D** → dominant class | O(1) |
| `CATEGORICAL_DISTANCE` | σ₁, σ₂ → *d*_cat ≥ 0 | O(1) |
| `COMPLETE` | endpoints, constraints → trajectory γ | O(N log N) |

Both a Python (`syndrome/`) and a Rust (`syndrome-rs/`) implementation are
provided.

### 4.2 The Cause-for-Concern language

`cause-for-concern/` is a domain-specific language in which the epistemic
constraints of §1.3 are enforced by the *type system* rather than by
convention. It has one primitive — the characterised perturbation — from
which diagnosis (localisation to a cell) and therapy (gap closure) are both
expressed. No disease is named anywhere in the language.

Four guarantees are enforced, not documented:

1. **A verdict cannot exist without its tolerance.** `admit H tolerance T` is
   the only production yielding a `Verdict`, and both operands are mandatory.
   A verdict without a tolerance has no derivation in the grammar.
2. **A tolerance cannot be conjured.** `tolerance of L with S` requires the
   `with` clause. A species carrying no `sigma` yields an *undefined* data
   floor rather than a default, and every cycle above the numerical floor
   returns `UNDECIDABLE`.
3. **Verdicts are three-valued**, per §2.3.
4. **`INVALID` ≠ `NEGATIVE`.** A reference network failing its own
   consistency check halts the run with `INVALID`: no conclusion is licensed,
   because the fault is in the data. A failed assertion against a valid
   reference gives `NEGATIVE`, which is a real result.

| Component | Path |
|---|---|
| Paper | `cause-for-concern/docs/disease-circuit-tolerance/` |
| Python reference implementation | `cause-for-concern/prototype/` |
| Browser workbench | `cause-for-concern/webtool/` |

The two implementations agree to machine precision. On the reference circuit
both produce ε_num = 4.249 × 10⁻¹², ε_data = 11.337, witness set {`SHNT`}.

---

## 5. Validation

The suite comprises 101 numerical experiments across six categories, all
passing:

| Category | Tests | Subject |
|---|---|---|
| Partition | 9 | Capacity formula, coordinate necessity |
| Coherence | 14 | Universal coherence equation across classes |
| Disease | 20 | Vector construction, geometric classification |
| Trajectory | 16 | Constraint-satisfaction convergence |
| Thermodynamic | 14 | Equations of state |
| Circuit | 28 | Cycle bases, both floors, verdict trichotomy |
| **Total** | **101** | pass rate 1.00 |

```python
from syndrome.validation import run_all_validations
results = run_all_validations()          # written to results/
```

Results are stored as JSON with complete metadata and as CSV summaries.

The circuit tolerance work carries a second, independent validation layer of
five sweeps (V1–V5) reproduced live in the webtool:

| Sweep | Result |
|---|---|
| V1 Noise scale | 0 bound violations; median slack ≈ 730× |
| V2 Fixed tolerance | FP 0.00 in binary64, up to 0.84 in binary32 |
| V3 Trichotomy | ≈ 81% undecidable; ≈ 11.5-order floor gap |
| V4 Basis dependence | 0 verdict disagreements; ≈ 35% flagged-set variation |
| V5 Detection | 0 guarantee violations; ratio ≈ 0.51–0.71 |

### 5.1 Falsification policy

Where measurement has contradicted a stated claim, the claim has been
corrected and the failure recorded in the manuscript rather than the
experiment adjusted. §2.4 documents one such case; the tolerance paper
retains both the failed prediction and the reasoning that produced it.

---

## 6. Usage

### 6.1 Requirements

| | |
|---|---|
| Python | ≥ 3.10, NumPy ≥ 1.24, SciPy ≥ 1.10, Pandas ≥ 2.0 |
| Rust | ≥ 1.70 |
| Node | ≥ 18 (webtool only) |
| LaTeX | any TeX Live ≥ 2021 (papers, monograph) |

### 6.2 Coherence and classification

```python
from syndrome.core import coherence_index, cellular_coherence
from syndrome.core import disease_vector, classify_disease

eta = coherence_index(pi_obs=0.8, pi_opt=1.0, pi_deg=0.0)   # 0.8

oscillators = [
    {"class": "P", "pi_obs": 13,  "pi_opt": 12,  "pi_deg": 16,  "weight": 1.0},
    {"class": "E", "pi_obs": 1e5, "pi_opt": 1e6, "pi_deg": 1e2, "weight": 1.0},
]
eta_cell = cellular_coherence(oscillators)
D = disease_vector(oscillators)
classify_disease(D)                                          # "P"
```

### 6.3 Running a CFC experiment

```bash
cd cause-for-concern/prototype
python run_cfc.py examples/kcl_tolerance.cfc     # record written as JSON
python test_cfc.py                               # 28 tests

cd ../webtool
npm install && npm run dev                       # http://localhost:5173
```

---

## 7. Contributions

1. **Partition geometry.** Necessity of the coordinates (*n*, ℓ, *m*, *s*)
   with capacity *C*(*n*) = 2*n*².
2. **Triple equivalence.** Isomorphism O(Ω) ≅ C(Ω) ≅ P(Ω) via the entropy
   identity.
3. **Fundamental identity.** Obs(*x*) ≡ Comp(*x*) ≡ Proc(*x*) through
   categorical address resolution.
4. **Opacity independence.** *d*_cat ⊥ *d*_spatial and *d*_cat ⊥ τ_optical.
5. **Epistemic floors.** Floor positivity, group blindness, and
   self-consistency primacy as the unique admissible basis for detection.
6. **Disease as holonomy.** Topological formulation of disease as loop-closure
   failure, with the No Template Theorem.
7. **Cycle-local tolerance.** Replacement of the fixed solver tolerance by
   ε* = max{ε_num, ε_data}, with complementary false-positive and detection
   bounds and a mandatory third verdict.
8. **Basis invariance.** Basis-independence of the verdict, basis-dependence
   of the localisation, and the witness set as the surviving invariant.
9. **Recognition as interference.** Molecular recognition, viral tropism, and
   pathogen surveillance reduced to a single oscillator-interference
   operation.
10. **Type-enforced epistemics.** A language in which an unjustified
    diagnostic claim is not merely discouraged but ungrammatical.

---

## 8. References

Complete bibliographies accompany each paper; the consolidated one is
`monograph/back/bibliography.bib`. Principal theoretical antecedents:

- Poincaré (1890) — recurrence theorem
- Jaynes (1957) — maximum entropy
- Maslov (1981) — semi-classical approximation
- Kuramoto (1984) — coupled oscillators
- Wegscheider (1901) — thermodynamic consistency conditions
- Higham (2002) — accuracy and stability of numerical algorithms

## 9. Citation

```bibtex
@book{sachikonye_blind,
  author    = {Sachikonye, Kundai Farai},
  title     = {The Blind Leading the Blind: Categorical Resolution of
               Biological Dynamics},
  year      = {2026},
  note      = {Monograph. Repository: https://github.com/kundai-sachikonye/syndrome}
}
```

## 10. License

MIT. See [LICENSE](LICENSE).

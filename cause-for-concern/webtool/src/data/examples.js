/**
 * Example .cfc programs. Each one runs for real in the browser against
 * the ported kernel -- none of the output is mocked.
 */

export const EXAMPLES = {
  "01_validity_gate.cfc": `-- 01_validity_gate.cfc
--
-- The main experiment: cycle-consistency with per-cycle tolerances.
--
--   1. build and solve a reference circuit
--   2. gauge-centre the potentials (lowers the numerical floor)
--   3. compute a minimum-weight cycle basis
--   4. VALIDITY GATE -- the reference must pass its own check
--   5. perturb an edge, re-evaluate, localise to the witness set
--
-- Every verdict below carries the tolerance that produced it. The
-- grammar has no production that would let one be omitted.

floor 1e-9

circuit Reference {
  species Glucose  : mu0 : -917.0,  concentration : 5.0,   sigma : 1.2
  species G6P      : mu0 : -1760.0, concentration : 0.5,   sigma : 2.4
  species FBP      : mu0 : -2600.0, concentration : 0.1,   sigma : 3.1
  species G3P      : mu0 : -1510.0, concentration : 0.05,  sigma : 2.0
  species Pyruvate : mu0 : -474.0,  concentration : 0.1,   sigma : 0.9

  reaction HK   : Glucose -> G6P,      k : 0.10
  reaction PFK  : G6P -> FBP,          k : 0.05
  reaction ALD  : FBP -> G3P,          k : 0.08
  reaction PK   : G3P -> Pyruvate,     k : 0.12
  reaction GNG  : Pyruvate -> Glucose, k : 0.02
  reaction SHNT : G6P -> G3P,          k : 0.03

  solve yield C_ref
}

-- Gauge centring changes no cycle sum; it lowers the numerical floor.
let C_centred := centre_potentials(C_ref)
let B := minimum_cycle_basis(C_centred)

report "cycles_in_basis", size(B)

-- VALIDITY GATE ---------------------------------------------------
-- A failure here is INVALID, not NEGATIVE: it says the annotations
-- are not self-consistent and licenses no conclusion whatever.

foreach loop in B {
  holonomy of loop in C_centred yield h_ref
  tolerance of loop with Reference yield t_ref
  admit h_ref tolerance t_ref yield v_ref

  report loop, h_ref, t_ref, v_ref

  assert v_ref == CONSISTENT
    emit "reference cycle consistent"
    otherwise invalid
      emit "reference network fails its own consistency check"
}

emit "validity gate passed: reference is self-consistent"

-- DIAGNOSTIC --------------------------------------------------------
-- The defect must go on an EDGE. Shifting a node potential leaves the
-- edge data the gradient of the shifted potential, so every cycle sum
-- stays exactly zero.

let C_pert := perturb_edge(C_centred, "SHNT", 40.0)

foreach loop in B {
  holonomy of loop in C_pert yield h
  tolerance of loop with Reference yield t
  admit h tolerance t yield v

  report loop, h, t, v

  where v == INCONSISTENT collect loop into flagged
}

-- Localisation is to the witness set, never to a named loop: the
-- flagged set depends on the basis, the witness set does not.
witness of flagged yield W
report "witness_set", W
report "witness_cardinality", size(W)

assert size(W) > 0
  emit "defect localised to a non-empty witness set"
  otherwise decline
    emit "no localisation at this data quality"`,

  "02_undecidable.cfc": `-- 02_undecidable.cfc
--
-- The third verdict is not a formality.
--
-- The same 3 kJ/mol defect is applied twice: once to a circuit whose
-- thermodynamics is well characterised, once to one annotated with
-- realistic component-contribution uncertainties.
--
-- A two-valued test must call the second case either CONSISTENT --
-- denying a signal that is real -- or INCONSISTENT -- asserting a
-- defect the data cannot resolve. Neither is warranted.

floor 1e-9

circuit WellCharacterised {
  species A : mu0 : -100.0, concentration : 1.0, sigma : 0.02
  species B : mu0 : -140.0, concentration : 1.0, sigma : 0.02
  species D : mu0 : -180.0, concentration : 1.0, sigma : 0.02

  reaction AB : A -> B, k : 0.1
  reaction BD : B -> D, k : 0.1
  reaction DA : D -> A, k : 0.1

  solve yield C_good
}

let G := centre_potentials(C_good)
let BG := minimum_cycle_basis(G)
let G_def := perturb_edge(G, "BD", 3.0)

foreach loop in BG {
  holonomy of loop in G_def yield hg
  tolerance of loop with WellCharacterised yield tg
  admit hg tolerance tg yield vg
  report "well_characterised", loop, hg, tg, vg

  assert vg == INCONSISTENT
    emit "3 kJ/mol resolved at sigma = 0.02"
}

circuit PoorlyCharacterised {
  species P : mu0 : -100.0, concentration : 1.0, sigma : 3.0
  species Q : mu0 : -140.0, concentration : 1.0, sigma : 3.0
  species R : mu0 : -180.0, concentration : 1.0, sigma : 3.0

  reaction PQ : P -> Q, k : 0.1
  reaction QR : Q -> R, k : 0.1
  reaction RP : R -> P, k : 0.1

  solve yield C_poor
}

let H := centre_potentials(C_poor)
let BH := minimum_cycle_basis(H)
let H_def := perturb_edge(H, "QR", 3.0)

foreach loop in BH {
  holonomy of loop in H_def yield hp
  tolerance of loop with PoorlyCharacterised yield tp
  admit hp tolerance tp yield vp
  report "poorly_characterised", loop, hp, tp, vp

  assert vp == UNDECIDABLE
    emit "same defect is UNDECIDABLE at sigma = 3.0"
}

emit "the verdict tracks data quality, as it must"`,

  "03_invalid_reference.cfc": `-- 03_invalid_reference.cfc
--
-- INVALID is not NEGATIVE.
--
-- The reference here is annotated inconsistently: its own supplied
-- edge data are not the gradient of any potential. The validity gate
-- catches this BEFORE any diagnostic claim, and halts.
--
--   NEGATIVE -- the reference was sound, the test ran, it detected
--               nothing. This says something about the test.
--
--   INVALID  -- the reference was never sound, so the test had no
--               valid substrate. This says nothing about the test.
--
-- Fixing which is which before seeing the data is what stops a failed
-- reference from being reported as whichever is convenient.

floor 1e-9

circuit BadlyAnnotated {
  species X : mu0 : -100.0, concentration : 1.0, sigma : 0.01
  species Y : mu0 : -140.0, concentration : 1.0, sigma : 0.01
  species Z : mu0 : -180.0, concentration : 1.0, sigma : 0.01

  reaction XY : X -> Y, k : 0.1
  reaction YZ : Y -> Z, k : 0.1
  reaction ZX : Z -> X, k : 0.1

  solve yield C_bad
}

-- The annotation error: this edge disagrees with the species
-- potentials by 25 kJ/mol.
let C_ann := perturb_edge(C_bad, "YZ", 25.0)
let C_c := centre_potentials(C_ann)
let BB := minimum_cycle_basis(C_c)

foreach loop in BB {
  holonomy of loop in C_c yield h
  tolerance of loop with BadlyAnnotated yield t
  admit h tolerance t yield v

  report loop, h, t, v

  assert v == CONSISTENT
    emit "reference cycle consistent"
    otherwise invalid
      emit "reference fails its own check: annotations are not internally consistent"
}

emit "this line must not appear in the record"`,

  "04_rejected.cfc": `-- 04_rejected.cfc
--
-- This program MUST NOT parse.
--
-- It attempts the thing the language exists to prevent: deciding a
-- holonomy against a hard-coded number, with no tolerance and hence no
-- record of what justified the verdict.
--
-- Expected: status ERROR, a parse error naming the missing clause.
--
-- The guarantee is syntactic, not a lint: 'admit' has exactly one
-- production and it requires a 'tolerance' operand, so there is no
-- derivation at all for the offending line. A rule that could be
-- worked around with three lines of user code would not be a rule.

floor 1e-9

circuit Small {
  species A : mu0 : -100.0, concentration : 1.0, sigma : 0.5
  species B : mu0 : -140.0, concentration : 1.0, sigma : 0.5
  species D : mu0 : -180.0, concentration : 1.0, sigma : 0.5

  reaction AB : A -> B, k : 0.1
  reaction BD : B -> D, k : 0.1
  reaction DA : D -> A, k : 0.1

  solve yield C0
}

let G := centre_potentials(C0)
let B0 := minimum_cycle_basis(G)

foreach loop in B0 {
  holonomy of loop in G yield h

  -- The offending line. No 'tolerance' clause, so no derivation:
  admit h yield v

  report loop, v
}`,

  "05_node_vs_edge.cfc": `-- 05_node_vs_edge.cfc
--
-- A defect lives on an edge, never on a node.
--
-- This is worth its own program because getting it wrong produces a
-- null result that looks exactly like a real negative. Our first
-- implementation perturbed a node, detected nothing, and briefly
-- looked like a failure of the method.
--
-- Shifting mu_i leaves the edge data the gradient of the shifted mu,
-- so by the telescoping identity every cycle sum stays exactly zero.
-- Only an edge offset makes the data fail to be a gradient.

floor 1e-9

circuit Ring {
  species A : mu0 : -100.0, concentration : 1.0, sigma : 0.05
  species B : mu0 : -140.0, concentration : 1.0, sigma : 0.05
  species D : mu0 : -180.0, concentration : 1.0, sigma : 0.05
  species E : mu0 : -160.0, concentration : 1.0, sigma : 0.05

  reaction AB : A -> B, k : 0.1
  reaction BD : B -> D, k : 0.1
  reaction DE : D -> E, k : 0.1
  reaction EA : E -> A, k : 0.1

  solve yield C0
}

let G := centre_potentials(C0)
let BR := minimum_cycle_basis(G)

-- NODE perturbation: 500 kJ/mol, and nothing is detected.
let C_node := perturb(G, "B", 500.0)

foreach loop in BR {
  holonomy of loop in C_node yield hn
  tolerance of loop with Ring yield tn
  admit hn tolerance tn yield vn
  report "node_perturbation", loop, hn, vn

  assert vn == CONSISTENT
    emit "node shift leaves the cycle sum exactly zero"
}

-- EDGE perturbation: 5 kJ/mol, and it is found.
let C_edge := perturb_edge(G, "DE", 5.0)

foreach loop in BR {
  holonomy of loop in C_edge yield he
  tolerance of loop with Ring yield te
  admit he tolerance te yield ve
  report "edge_perturbation", loop, he, ve

  where ve == INCONSISTENT collect loop into flagged
}

witness of flagged yield W
report "witness_set", W

assert size(W) > 0
  emit "edge defect detected and localised"
  otherwise decline
    emit "edge defect not detected"`,
};

export const DEFAULT_FILE = "01_validity_gate.cfc";

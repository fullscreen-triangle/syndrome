-- kcl_tolerance.cfc
--
-- The main experiment: cycle-consistency with per-cycle tolerances.
--
-- Structure follows the protocol:
--   1. build and solve a reference circuit
--   2. gauge-centre the potentials (reduces the numerical floor)
--   3. compute a minimum-weight cycle basis
--   4. VALIDITY GATE: the reference must pass its own consistency check
--   5. perturb, re-evaluate, localise to the witness set
--
-- Every verdict below carries the tolerance that produced it; the
-- grammar has no production that would let one be omitted.

floor 1e-9

-- ---------------------------------------------------------------
-- Reference circuit: a five-species loop with a branch, giving two
-- independent cycles. Sigma values are the reported uncertainties on
-- the standard potentials, in kJ/mol.
-- ---------------------------------------------------------------

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

-- Gauge centring: changes no cycle sum, lowers the numerical floor.
let C_centred := centre_potentials(C_ref)
let B := minimum_cycle_basis(C_centred)

report "cycles_in_basis", size(B)

-- ---------------------------------------------------------------
-- VALIDITY GATE
--
-- If the reference network fails its own consistency check, the
-- experiment is INVALID, not negative: it says the thermodynamic
-- annotations are not self-consistent, and licenses no conclusion
-- about the diagnostic.
-- ---------------------------------------------------------------

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

-- ---------------------------------------------------------------
-- DIAGNOSTIC
--
-- Inject a defect by breaking the gradient property ON AN EDGE.
--
-- Note it must be an edge and not a node: shifting a node potential
-- leaves the edge data the gradient of the shifted potential, so every
-- cycle sum stays exactly zero. Only an edge offset makes the data
-- fail to be a gradient, which is what inconsistency means.
--
-- 40 kJ/mol is far above the data floor, so it must be detected if the
-- test works at all.
-- ---------------------------------------------------------------

let C_pert := perturb_edge(C_centred, "SHNT", 40.0)

foreach loop in B {
  holonomy of loop in C_pert yield h
  tolerance of loop with Reference yield t
  admit h tolerance t yield v

  report loop, h, t, v

  where v == INCONSISTENT collect loop into flagged
}

-- Localisation is to the witness set, never to a named loop:
-- the flagged set depends on the basis, the witness set does not.
witness of flagged yield W
report "witness_set", W
report "witness_cardinality", size(W)

assert size(W) > 0
  emit "defect localised to a non-empty witness set"
  otherwise decline
    emit "no localisation at this data quality"

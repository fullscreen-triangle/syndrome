-- rejected_bare_verdict.cfc
--
-- This program MUST NOT parse.
--
-- It attempts the thing the language exists to prevent: deciding a
-- holonomy against a hard-coded number, with no tolerance and hence no
-- record of what justified the verdict.
--
-- Run it with:  python run_cfc.py examples/rejected_bare_verdict.cfc
-- Expected:     status ERROR, a parse error naming the missing clause.
--
-- The guarantee is syntactic, not a lint: `admit` has exactly one
-- production and it requires a `tolerance` operand, so there is no
-- derivation at all for the line below. A rule that could be worked
-- around with three lines of user code would not be a rule.

floor 1e-9

circuit Small {
  species A : mu0 : -100.0, concentration : 1.0, sigma : 0.5
  species B : mu0 : -140.0, concentration : 1.0, sigma : 0.5
  species C : mu0 : -180.0, concentration : 1.0, sigma : 0.5

  reaction AB : A -> B, k : 0.1
  reaction BC : B -> C, k : 0.1
  reaction CA : C -> A, k : 0.1

  solve yield C0
}

let G := centre_potentials(C0)
let B0 := minimum_cycle_basis(G)

foreach loop in B0 {
  holonomy of loop in G yield h

  -- The offending line. No `tolerance` clause, so no derivation:
  admit h yield v

  report loop, v
}

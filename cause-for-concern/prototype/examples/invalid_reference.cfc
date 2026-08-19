-- invalid_reference.cfc
--
-- INVALID is not NEGATIVE.
--
-- The reference network here is annotated inconsistently: its own
-- supplied edge data are not the gradient of any potential. The
-- validity gate catches this BEFORE any diagnostic claim is evaluated,
-- and halts with status INVALID.
--
-- The distinction matters because the two outcomes license different
-- conclusions:
--
--   NEGATIVE -- the reference was sound, the test ran, and it did not
--               detect the defect. This says something about the test.
--
--   INVALID  -- the reference was not sound, so the test never had a
--               valid substrate. This says nothing about the test at
--               all, and reporting it as a negative result would be a
--               misattribution.
--
-- Fixing which of these is which BEFORE seeing the data is what stops
-- a failed reference from being reported as whichever is convenient.

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

-- The annotation error: this edge's tabulated potential difference
-- disagrees with the species potentials by 25 kJ/mol.
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
      emit "reference fails its own consistency check: annotations are not internally consistent"
}

-- Never reached. The gate halts first, which is the point.
emit "this line must not appear in the record"

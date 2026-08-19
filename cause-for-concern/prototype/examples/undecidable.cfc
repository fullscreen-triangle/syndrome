-- undecidable.cfc
--
-- The third verdict is not a formality.
--
-- Two runs over the same circuit and the same defect. The defect is
-- 3 kJ/mol: far above the numerical floor (~1e-11 kJ/mol) and below the
-- data floor set by the reported uncertainties (~8 kJ/mol).
--
-- A two-valued test must call this either CONSISTENT -- denying a
-- signal that is real -- or INCONSISTENT -- asserting a defect the data
-- cannot resolve. Neither is warranted, and the honest verdict is that
-- the question is not answerable from the data supplied.

floor 1e-9

circuit WellCharacterised {
  species A : mu0 : -100.0, concentration : 1.0, sigma : 0.02
  species B : mu0 : -140.0, concentration : 1.0, sigma : 0.02
  species C : mu0 : -180.0, concentration : 1.0, sigma : 0.02

  reaction AB : A -> B, k : 0.1
  reaction BC : B -> C, k : 0.1
  reaction CA : C -> A, k : 0.1

  solve yield C_good
}

let G := centre_potentials(C_good)
let BG := minimum_cycle_basis(G)

-- With sigma = 0.02 the data floor is about 0.09 kJ/mol, so a 3 kJ/mol
-- defect is comfortably resolved: the verdict is INCONSISTENT.
let G_def := perturb_edge(G, "BC", 3.0)

foreach loop in BG {
  holonomy of loop in G_def yield hg
  tolerance of loop with WellCharacterised yield tg
  admit hg tolerance tg yield vg
  report "well_characterised", loop, hg, tg, vg
}

-- ---------------------------------------------------------------
-- The same defect, on a circuit whose thermodynamics is annotated
-- with realistic component-contribution uncertainties.
-- ---------------------------------------------------------------

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

  -- The same 3 kJ/mol defect is now inside the data's own uncertainty.
  assert vp == UNDECIDABLE
    emit "same defect is UNDECIDABLE at this data quality"
}

emit "the verdict depends on the data quality, as it must"

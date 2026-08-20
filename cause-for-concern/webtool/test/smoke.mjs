import { runSource } from "../src/cfc/interpreter.js";
const src = `
floor 1e-9
circuit Reference {
  species Glucose  : mu0 : -917.0,  concentration : 5.0,  sigma : 1.2
  species G6P      : mu0 : -1760.0, concentration : 0.5,  sigma : 2.4
  species FBP      : mu0 : -2600.0, concentration : 0.1,  sigma : 3.1
  species G3P      : mu0 : -1510.0, concentration : 0.05, sigma : 2.0
  species Pyruvate : mu0 : -474.0,  concentration : 0.1,  sigma : 0.9
  reaction HK   : Glucose -> G6P,      k : 0.10
  reaction PFK  : G6P -> FBP,          k : 0.05
  reaction ALD  : FBP -> G3P,          k : 0.08
  reaction PK   : G3P -> Pyruvate,     k : 0.12
  reaction GNG  : Pyruvate -> Glucose, k : 0.02
  reaction SHNT : G6P -> G3P,          k : 0.03
  solve yield C_ref
}
let C := centre_potentials(C_ref)
let B := minimum_cycle_basis(C)
report "cycles", size(B)
foreach loop in B {
  holonomy of loop in C yield h
  tolerance of loop with Reference yield t
  admit h tolerance t yield v
  assert v == CONSISTENT emit "ref consistent" otherwise invalid emit "ref fails"
}
emit "validity gate passed"
let P := perturb_edge(C, "SHNT", 40.0)
foreach loop in B {
  holonomy of loop in P yield h2
  tolerance of loop with Reference yield t2
  admit h2 tolerance t2 yield v2
  where v2 == INCONSISTENT collect loop into flagged
}
witness of flagged yield W
report "witness", W
assert size(W) > 0 emit "localised" otherwise decline emit "no localisation"
`;
const r = runSource(src, "test.cfc");
console.log("status:", r.status);
console.log("clock:", r.committedMeasurements);
console.log("cycles:", r.cycles.length, r.cycles.map(c=>c.loop+"("+c.length+")").join(","));
console.log("verdicts:", r.verdicts.map(v=>v.verdict).join(","));
console.log("witness:", r.witnessSet);
console.log("tol[0]: num=%s data=%s star=%s", r.tolerances[0].numerical.toExponential(3), r.tolerances[0].data.toFixed(3), r.tolerances[0].star.toFixed(3));
console.log("emissions:", r.emissions.map(e=>e.message).join(" | "));
if (r.error) console.log("error:", r.error);

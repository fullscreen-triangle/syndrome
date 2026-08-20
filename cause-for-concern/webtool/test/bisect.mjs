import { runSource } from "../src/cfc/interpreter.js";

const head = `floor 1e-9
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
`;

const steps = [
  ["circuit only", ""],
  ["centre", `let C := centre_potentials(C_ref)\n`],
  ["basis", `let C := centre_potentials(C_ref)\nlet B := minimum_cycle_basis(C)\n`],
  ["report size", `let C := centre_potentials(C_ref)\nlet B := minimum_cycle_basis(C)\nreport "cycles", size(B)\n`],
  ["foreach hol", `let C := centre_potentials(C_ref)\nlet B := minimum_cycle_basis(C)\nforeach loop in B {\n  holonomy of loop in C yield h\n}\n`],
  ["foreach tol", `let C := centre_potentials(C_ref)\nlet B := minimum_cycle_basis(C)\nforeach loop in B {\n  holonomy of loop in C yield h\n  tolerance of loop with Reference yield t\n}\n`],
  ["foreach admit", `let C := centre_potentials(C_ref)\nlet B := minimum_cycle_basis(C)\nforeach loop in B {\n  holonomy of loop in C yield h\n  tolerance of loop with Reference yield t\n  admit h tolerance t yield v\n}\n`],
];

for (const [name, tail] of steps) {
  const r = runSource(head + tail, name);
  console.log(`${name.padEnd(16)} ${r.status.padEnd(8)} ${r.error || ""}`);
}

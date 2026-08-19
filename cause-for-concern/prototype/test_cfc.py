#!/usr/bin/env python3
"""
test_cfc.py -- checks on the kernel and the language guarantees.

Run:  python test_cfc.py

Two things this suite deliberately does NOT do:

  * It does not check the interpreter against its own tolerance
    computation. Such a check passes by construction and measures
    nothing.
  * It does not assert that verdicts are stable across runs of
    different length. The clock advances on every measurement, so a
    later verdict is a different measurement, not a cache lookup.

Several checks below are negative controls: they assert that something
does NOT happen on well-formed input, and would fail if the guarantee
they test were removed.
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cfc import (  # noqa: E402
    CONSISTENT, INCONSISTENT, UNDECIDABLE, Circuit, Reaction, Species,
    admit, compute_holonomy, compute_tolerance, cycle_sum, data_floor,
    fundamental_cycle_basis, minimum_cycle_basis, numerical_floor,
    run_source, witness_set,
)

PASS = FAIL = 0
FAILURES = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))


def triangle(sigma=0.5, mus=(-100.0, -140.0, -180.0)) -> Circuit:
    c = Circuit()
    for nm, m in zip("ABC", mus):
        c.add_species(Species(nm, m, 1.0, sigma))
    c.add_reaction(Reaction("AB", "A", "B", 0.1))
    c.add_reaction(Reaction("BC", "B", "C", 0.1))
    c.add_reaction(Reaction("CA", "C", "A", 0.1))
    return c.solve()


def bigger() -> Circuit:
    c = Circuit()
    spec = [("Glucose", -917.0, 5.0), ("G6P", -1760.0, 0.5),
            ("FBP", -2600.0, 0.1), ("G3P", -1510.0, 0.05),
            ("Pyruvate", -474.0, 0.1)]
    for nm, m, cc in spec:
        c.add_species(Species(nm, m, cc, 2.0))
    for nm, a, b, k in [("HK", "Glucose", "G6P", 0.1),
                        ("PFK", "G6P", "FBP", 0.05),
                        ("ALD", "FBP", "G3P", 0.08),
                        ("PK", "G3P", "Pyruvate", 0.12),
                        ("GNG", "Pyruvate", "Glucose", 0.02),
                        ("SHNT", "G6P", "G3P", 0.03)]:
        c.add_reaction(Reaction(nm, a, b, k))
    return c.solve()


print("\n-- Exact vanishing (the identity the whole test rests on) --")
c = triangle()
B = minimum_cycle_basis(c)
check("cycle sum is exactly zero on a consistent circuit",
      all(cycle_sum(c, cy) == 0.0 for cy in B),
      str([cycle_sum(c, cy) for cy in B]))

cb = bigger()
Bb = minimum_cycle_basis(cb)
check("exact zero holds on a larger network too",
      all(abs(cycle_sum(cb, cy)) < 1e-9 for cy in Bb))

print("\n-- Node perturbation cannot create inconsistency (negative control) --")
cp = triangle()
cp.mu["B"] += 500.0
check("shifting a node potential leaves every cycle sum zero",
      all(abs(cycle_sum(cp, cy)) < 1e-9 for cy in minimum_cycle_basis(cp)),
      "a node shift must stay a gradient")

print("\n-- Edge perturbation does create inconsistency --")
ce = triangle()
ce.edge_offset["BC"] = 7.0
sums = [abs(cycle_sum(ce, cy)) for cy in minimum_cycle_basis(ce)]
check("an edge offset shows up in the cycle sum",
      any(abs(s - 7.0) < 1e-9 for s in sums), str(sums))

print("\n-- Gauge freedom --")
c1 = triangle()
c2 = c1.centre_potentials()
b1, b2 = minimum_cycle_basis(c1), minimum_cycle_basis(c2)
check("centring changes no cycle sum",
      all(abs(cycle_sum(c1, x) - cycle_sum(c2, y)) < 1e-12
          for x, y in zip(b1, b2)))
check("centring reduces the numerical floor",
      numerical_floor(c2, b2[0]) < numerical_floor(c1, b1[0]),
      f"{numerical_floor(c1, b1[0]):.3e} -> {numerical_floor(c2, b2[0]):.3e}")

print("\n-- The numerical floor scales with length and range --")
small = triangle(mus=(-10.0, -12.0, -14.0))
large = triangle(mus=(-2000.0, -2010.0, -2020.0))
fs = numerical_floor(small, minimum_cycle_basis(small)[0])
fl = numerical_floor(large, minimum_cycle_basis(large)[0])
check("higher potential range gives a higher numerical floor", fl > fs,
      f"{fs:.3e} vs {fl:.3e}")
check("the floor is strictly positive", fs > 0)

print("\n-- The data floor --")
cd = triangle(sigma=2.0)
bd = minimum_cycle_basis(cd)[0]
ed = data_floor(cd, bd)
check("data floor exceeds numerical floor by orders of magnitude",
      ed is not None and ed > 1e6 * numerical_floor(cd, bd),
      f"num={numerical_floor(cd, bd):.3e} data={ed:.3e}")

cn = triangle()
for s in cn.species.values():
    s.sigma = None
check("absent uncertainties give no data floor rather than a default",
      data_floor(cn, minimum_cycle_basis(cn)[0]) is None)

print("\n-- The three-valued verdict --")
cw = triangle(sigma=0.02)
lw = minimum_cycle_basis(cw)[0]
cw.edge_offset["BC"] = 3.0
v = admit(compute_holonomy(cw, lw), compute_tolerance(cw, lw))
check("resolvable defect on good data is INCONSISTENT",
      v.label == INCONSISTENT, v.label)

cu = triangle(sigma=3.0)
lu = minimum_cycle_basis(cu)[0]
cu.edge_offset["BC"] = 3.0
vu = admit(compute_holonomy(cu, lu), compute_tolerance(cu, lu))
check("same defect on poor data is UNDECIDABLE",
      vu.label == UNDECIDABLE, vu.label)

cc0 = triangle(sigma=0.02)
lc = minimum_cycle_basis(cc0)[0]
vc = admit(compute_holonomy(cc0, lc), compute_tolerance(cc0, lc))
check("no defect is CONSISTENT", vc.label == CONSISTENT, vc.label)

print("\n-- No false positives on a consistent circuit (negative control) --")
ok = True
for sig in (0.01, 0.5, 5.0):
    cx = triangle(sigma=sig)
    for cy in minimum_cycle_basis(cx):
        lab = admit(compute_holonomy(cx, cy),
                    compute_tolerance(cx, cy)).label
        if lab == INCONSISTENT:
            ok = False
check("a consistent circuit never returns INCONSISTENT", ok)

print("\n-- Detection guarantee: D > 2*eps_star implies flagged --")
cdet = triangle(sigma=0.02)
ld = minimum_cycle_basis(cdet)[0]
tol = compute_tolerance(cdet, ld)
cdet.edge_offset["BC"] = 2.5 * tol.star
vd = admit(compute_holonomy(cdet, ld), compute_tolerance(cdet, ld))
check("defect above 2*eps_star is detected", vd.label == INCONSISTENT,
      f"star={tol.star:.4f} D={2.5 * tol.star:.4f} -> {vd.label}")

print("\n-- Verdict is basis-independent; localisation is not --")
cbasis = bigger()
cbasis.edge_offset["SHNT"] = 60.0
mcb = minimum_cycle_basis(cbasis)
fcb = fundamental_cycle_basis(cbasis)


def any_flagged(circ, basis):
    return any(admit(compute_holonomy(circ, cy),
                     compute_tolerance(circ, cy)).label == INCONSISTENT
               for cy in basis)


check("both bases agree the network is inconsistent",
      any_flagged(cbasis, mcb) == any_flagged(cbasis, fcb) is True)

check("both bases have the cyclomatic number of elements",
      len(mcb) == len(fcb) == cbasis.cyclomatic_number(),
      f"mcb={len(mcb)} fcb={len(fcb)} nu={cbasis.cyclomatic_number()}")

print("\n-- The witness set contains the defective edge --")
flagged = [cy for cy in mcb
           if admit(compute_holonomy(cbasis, cy),
                    compute_tolerance(cbasis, cy)).label == INCONSISTENT]
W = witness_set(flagged)
check("witness set contains the perturbed edge", "SHNT" in W, str(sorted(W)))
check("witness set is non-empty when something is flagged",
      len(W) > 0 if flagged else True)

flagged_f = [cy for cy in fcb
             if admit(compute_holonomy(cbasis, cy),
                      compute_tolerance(cbasis, cy)).label == INCONSISTENT]
Wf = witness_set(flagged_f)
check("witness set contains the defect under the other basis too",
      "SHNT" in Wf, str(sorted(Wf)))

print("\n-- Language guarantees --")
bare = """
floor 1e-9
circuit S {
  species A : mu0 : -100.0, concentration : 1.0, sigma : 0.5
  species B : mu0 : -140.0, concentration : 1.0, sigma : 0.5
  species C : mu0 : -180.0, concentration : 1.0, sigma : 0.5
  reaction AB : A -> B, k : 0.1
  reaction BC : B -> C, k : 0.1
  reaction CA : C -> A, k : 0.1
  solve yield C0
}
let G := centre_potentials(C0)
let BS := minimum_cycle_basis(G)
foreach loop in BS {
  holonomy of loop in G yield h
  admit h yield v
}
"""
r = run_source(bare, "bare")
check("a verdict without a tolerance does not parse",
      r.status == "ERROR" and "tolerance" in (r.error or ""),
      r.error or "")

no_with = bare.replace("admit h yield v",
                       "tolerance of loop yield t\n  admit h tolerance t yield v")
r2 = run_source(no_with, "nowith")
check("a tolerance without a 'with' source does not parse",
      r2.status == "ERROR" and "with" in (r2.error or ""),
      r2.error or "")

good = bare.replace(
    "admit h yield v",
    "tolerance of loop with S yield t\n  admit h tolerance t yield v")
r3 = run_source(good, "good")
check("the well-formed program runs", r3.status == "OK", r3.error or "")
check("every verdict in the record carries its tolerance",
      all("tolerance" in v and v["tolerance"]["star"] > 0
          for v in r3.verdicts))

print("\n-- The clock is monotone --")
check("clock advanced once per measurement verb", r3.clock >= len(r3.verdicts),
      f"clock={r3.clock} verdicts={len(r3.verdicts)}")

zero_floor = good.replace("floor 1e-9", "floor 0")
r4 = run_source(zero_floor, "zerofloor")
check("a zero floor is rejected",
      r4.status == "ERROR" and "floor" in (r4.error or ""), r4.error or "")

print("\n-- INVALID is distinguished from NEGATIVE --")
inv = good.replace(
    "admit h tolerance t yield v",
    'admit h tolerance t yield v\n  assert v == INCONSISTENT emit "x" '
    'otherwise invalid emit "reference unsound"')
r5 = run_source(inv, "invalid")
check("otherwise invalid yields status INVALID", r5.status == "INVALID",
      r5.status)

neg = good.replace(
    "admit h tolerance t yield v",
    'admit h tolerance t yield v\n  assert v == INCONSISTENT emit "x" '
    'otherwise decline emit "not detected"')
r6 = run_source(neg, "negative")
check("otherwise decline yields status NEGATIVE", r6.status == "NEGATIVE",
      r6.status)

print(f"\n{'=' * 58}")
print(f"  {PASS} passed, {FAIL} failed")
if FAILURES:
    for f in FAILURES:
        print(f"    - {f}")
print(f"{'=' * 58}\n")
sys.exit(1 if FAIL else 0)

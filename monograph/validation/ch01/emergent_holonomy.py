#!/usr/bin/env python3
"""
emergent_holonomy.py -- the free energy the medium supplies around the
erythrocyte's glycolytic cycle (stage A).

The cycle that closes glycolysis through the medium has net exchange
glucose -> 2 lactate (protons and water held by the medium). Its holonomy
is the Gibbs energy of that exchange, which depends on the medium alone:
the standard transformed energy from component contribution, plus the
concentration term at plasma levels. ATP hydrolysis is computed for
comparison, as the unit in which the cell spends what the cycle supplies.

Conditions are those of the erythrocyte (pH 7.2, I = 0.15 M, 310.15 K,
pMg 3); plasma glucose 5 mM and lactate 1 mM are supplied values.
Needs equilibrator-api 0.8.1:

    python emergent_holonomy.py
"""

from __future__ import annotations

import json
import math
import os
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
R_GAS = 8.314462618e-3            # kJ/(mol K)
T = 310.15
PLASMA = {"glucose_M": 5e-3, "lactate_M": 1e-3}


def main() -> None:
    warnings.filterwarnings("ignore")
    from equilibrator_api import ComponentContribution, Q_

    cc = ComponentContribution()
    cc.p_h, cc.ionic_strength = Q_(7.2), Q_("0.15M")
    cc.temperature, cc.p_mg = Q_(f"{T}K"), Q_(3.0)
    out = {"conditions": {"pH": 7.2, "I_M": 0.15, "T_K": T, "pMg": 3.0},
           "plasma": PLASMA}
    for name, txt in (("glucose_to_2_lactate", "kegg:C00031 = 2 kegg:C00186"),
                      ("atp_hydrolysis",
                       "kegg:C00002 + kegg:C00001 = kegg:C00008 + "
                       "kegg:C00009")):
        dg = cc.standard_dg_prime(cc.parse_reaction_formula(txt))
        out[name] = {"dG0_prime_kJmol": round(dg.value.m_as("kJ/mol"), 2),
                     "sd_kJmol": round(dg.error.m_as("kJ/mol"), 2)}
    g = out["glucose_to_2_lactate"]
    q = PLASMA["lactate_M"] ** 2 / PLASMA["glucose_M"]
    g["dG_prime_at_plasma_kJmol"] = round(
        g["dG0_prime_kJmol"] + R_GAS * T * math.log(q), 1)
    with open(os.path.join(HERE, "holonomy.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

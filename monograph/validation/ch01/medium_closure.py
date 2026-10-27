#!/usr/bin/env python3
"""
medium_closure.py -- which reactions of the erythrocyte can carry a steady
flux, before and after the network is closed through its medium.

A steady state of an open network satisfies S_I J = 0, where S_I keeps the
rows of the species the cell must balance (internal species) and drops the
rows of the species its medium holds fixed (exchanged species). A reaction
can carry a non-zero steady flux iff it lies on a cycle of ker S_I, and it
does iff deleting its column leaves rank(S_I) unchanged. All ranks here are
computed exactly, over the rationals.

Four computations, written to results.json:

  keying    the paper's network (species merged by InChIKey connectivity,
            which merges epimers) against the network of build_network.py
            (species merged only across anomers); both fully internal
  closure   the stereo-aware network with no exchanged species (every
            species internal, as in the paper), with the minimal medium
            {glucose, L-lactate, water}, and with the physiological medium
            listed in MEDIUM
  emergent  rank S - rank S_I, the number of independent cycles that pass
            through the medium
  enzymes   for each glycolytic and pentose-phosphate enzyme, whether it
            lies on a cycle under each medium
  supplied  the physiological medium again, with the one reaction the
            annotation omits (SUPPLIED) added

Needs numpy only:

    python medium_closure.py
"""

from __future__ import annotations

import csv
import json
import os
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))

# Species the plasma holds fixed, by KEGG id, with the transport that
# exchanges them (supplied; references in the chapter).
MEDIUM_MIN = {"C00031": "D-glucose (GLUT1)",
              "C00186": "L-lactate (MCT1)",
              "C00001": "water"}
MEDIUM = {**MEDIUM_MIN,
          "C00022": "pyruvate (MCT1)",
          "C00009": "phosphate (band 3)",
          "C00011": "CO2 (band 3, diffusion)",
          "C00027": "hydrogen peroxide (diffusion)",
          "C00147": "adenine (nucleobase transport)",
          "C00212": "adenosine (ENT1)",
          "C00294": "inosine (ENT1)",
          "C00262": "hypoxanthine (ENT1)",
          "C00014": "ammonia (diffusion)",
          "C00025": "L-glutamate (amino-acid transport)",
          "C00097": "L-cysteine (amino-acid transport)",
          "C00037": "glycine (amino-acid transport)",
          "C00127": "glutathione disulfide (MRP1 export)",
          "C01330": "Na+ (pump and leak)",
          "C00238": "K+ (pump and leak)",
          "C00076": "Ca2+ (pump and leak)"}

# Reactions the annotation omits, supplied from Rhea with their reference.
# UniProtKB P29401 (human transketolase) lists only RHEA:10508,
# S7P + G3P = R5P + X5P; its second reaction, RHEA:27626, is catalysed by
# the same enzyme (EC 2.2.1.1) and closes the non-oxidative pentose
# phosphate pathway. Species by KEGG id, negative = consumed.
SUPPLIED = [{"rhea": "27626", "genes": "TKT", "uniprot": "P29401",
             "ec": "2.2.1.1", "status": "included",
             "name": "D-erythrose 4-phosphate + D-xylulose 5-phosphate = "
                     "beta-D-fructose 6-phosphate + "
                     "D-glyceraldehyde 3-phosphate",
             "kegg": {"C00279": -1, "C00231": -1, "C05345": 1,
                      "C00118": 1}}]

ENZYMES = {"HK1": "2.7.1.1", "GPI": "5.3.1.9", "PFKL": "2.7.1.11",
           "ALDOA": "4.1.2.13", "TPI1": "5.3.1.1", "GAPDH": "1.2.1.12",
           "PGK1": "2.7.2.3", "PGAM1": "5.4.2.11", "ENO1": "4.2.1.11",
           "PKLR": "2.7.1.40", "LDHA": "1.1.1.27", "BPGM": "5.4.2.4",
           "MINPP1": "3.1.3.80", "G6PD": "1.1.1.49", "PGLS": "3.1.1.31",
           "PGD": "1.1.1.44", "RPE": "5.1.3.1", "RPIA": "5.3.1.6",
           "TKT": "2.2.1.1", "TALDO1": "2.2.1.2", "GSR": "1.8.1.7",
           "GPX1": "1.11.1.9", "ATP1A1": "7.2.2.13", "ATP2B4": "7.2.2.10"}


def rank(rows: list) -> int:
    """Exact rank of an integer matrix given as a list of rows."""
    m = [[Fraction(x) for x in r] for r in rows]
    if not m:
        return 0
    rk, ncol = 0, len(m[0])
    for c in range(ncol):
        p = next((i for i in range(rk, len(m)) if m[i][c] != 0), None)
        if p is None:
            continue
        m[rk], m[p] = m[p], m[rk]
        for i in range(len(m)):
            if i != rk and m[i][c] != 0:
                f = m[i][c] / m[rk][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[rk])]
        rk += 1
    return rk


def load():
    species = {r["sid"]: r for r in
               csv.DictReader(open(os.path.join(HERE, "species.csv"),
                                   encoding="utf-8"))}
    net = [r for r in csv.DictReader(open(os.path.join(HERE, "network.csv"),
                                          encoding="utf-8"))]
    return species, net


def reactions(net, species, merge_by: str):
    """Included reactions as {species: coef}, merged by a species field,
    deduplicated up to orientation. Returns (stoich list, meta list,
    dropped count)."""
    out, meta, seen, dropped = [], [], set(), 0
    for r in net:
        if r["status"] != "included":
            continue
        st: dict = {}
        for tok in r["stoich"].split():
            v, s = tok.split("*")
            k = species[s][merge_by]
            st[k] = st.get(k, 0) + int(v)
        st = {k: v for k, v in st.items() if v}
        if not st:
            dropped += 1                      # no net chemistry after merge
            continue
        canon = tuple(sorted(st.items()))
        first = canon[0][1]
        canon = tuple((k, v if first > 0 else -v) for k, v in canon)
        if canon in seen:
            continue
        seen.add(canon)
        out.append(st)
        meta.append(r)
    return out, meta, dropped


def analyse(stoich, meta, exchanged: set) -> dict:
    sp = sorted({k for s in stoich for k in s})
    internal = [k for k in sp if k not in exchanged]
    S = [[s.get(k, 0) for s in stoich] for k in sp]
    SI = [[s.get(k, 0) for s in stoich] for k in internal]
    rS, rI = rank(S), rank(SI)
    n = len(stoich)
    on = []
    for j in range(n):
        sub = [row[:j] + row[j + 1:] for row in SI]
        on.append(rank(sub) == rI)
    enz = {}
    for g, ec in ENZYMES.items():
        hits = [on[j] for j, m in enumerate(meta)
                if g in m["genes"].split(";") and ec in m["ec"].split(";")]
        if hits:
            enz[g] = any(hits)
    return {"reactions": n, "species": len(sp),
            "exchanged_present": sorted(set(sp) & exchanged),
            "rank_S": rS, "rank_S_internal": rI,
            "closed_cycle_space": n - rS,
            "steady_flux_space": n - rI,
            "emergent_cycles": rS - rI,
            "reactions_on_a_cycle": sum(on),
            "enzymes_on_a_cycle": enz,
            "on": on}


def main() -> None:
    species, net = load()
    kegg_sid = {}
    for s, r in species.items():
        if r["kegg"]:
            kegg_sid.setdefault(r["kegg"], set()).add(s)

    out = {"keying": {}, "closure": {}}
    for label, field in (("connectivity_14", "conn14"),
                         ("stereo_aware", "sid")):
        st, meta, dropped = reactions(net, species, field)
        res = analyse(st, meta, set())
        res.pop("on")
        res["no_net_chemistry_after_merge"] = dropped
        out["keying"][label] = res

    st, meta, _ = reactions(net, species, "sid")
    sid_of = {r["kegg"]: s for s, r in sorted(species.items()) if r["kegg"]}
    supplied = []
    for r in SUPPLIED:
        r = dict(r)
        r["stoich"] = " ".join(f"{v}*{sid_of[k]}"
                               for k, v in r.pop("kegg").items())
        supplied.append(r)
    st2, meta2, _ = reactions(net + supplied, species, "sid")
    for label, med, (st, meta) in (
            ("none", {}, (st, meta)),
            ("minimal", MEDIUM_MIN, (st, meta)),
            ("physiological", MEDIUM, (st, meta)),
            ("physiological+supplied", MEDIUM, (st2, meta2))):
        ex = set().union(*(kegg_sid.get(k, set()) for k in med)) if med \
            else set()
        res = analyse(st, meta, ex)
        res["exchanged_present"] = sorted(
            {species[s]["name"] for s in res["exchanged_present"]})
        res["off_cycle"] = sorted(
            f'{m["genes"]} {m["ec"]}: {m["name"][:60]}'
            for m, o in zip(meta, res.pop("on")) if not o)
        out["closure"][label] = res
    # Which exchanged species does each enzyme's cycle need? Remove one
    # species from the physiological medium at a time (supplied network).
    need = {}
    for k, what in MEDIUM.items():
        if k not in kegg_sid:
            continue
        ex = set().union(*(kegg_sid.get(x, set()) for x in MEDIUM if x != k))
        res = analyse(st2, meta2, ex)
        lost = sorted(g for g, v in res["enzymes_on_a_cycle"].items()
                      if not v and out["closure"]["physiological+supplied"]
                      ["enzymes_on_a_cycle"].get(g))
        need[what] = {"emergent_cycles": res["emergent_cycles"],
                      "enzymes_leaving_every_cycle": lost}
    # Both oxidant entries at once: H2O2 and GSSG.
    ox = ("C00027", "C00127")
    ex = set().union(*(kegg_sid.get(x, set()) for x in MEDIUM if x not in ox))
    res = analyse(st2, meta2, ex)
    need["no oxidant (H2O2 and GSSG both held internal)"] = {
        "emergent_cycles": res["emergent_cycles"],
        "enzymes_leaving_every_cycle": sorted(
            g for g, v in res["enzymes_on_a_cycle"].items() if not v and
            out["closure"]["physiological+supplied"]["enzymes_on_a_cycle"]
            .get(g))}
    out["medium_ablation"] = need
    out["medium"] = MEDIUM
    out["supplied"] = SUPPLIED
    with open(os.path.join(HERE, "results.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    for k, v in out["keying"].items():
        print(k, {x: v[x] for x in ("reactions", "species",
                                    "closed_cycle_space",
                                    "reactions_on_a_cycle",
                                    "no_net_chemistry_after_merge")})
    for k, v in out["closure"].items():
        print(k, {x: v[x] for x in ("steady_flux_space", "emergent_cycles",
                                    "reactions_on_a_cycle")})
        print("   ", v["enzymes_on_a_cycle"])


if __name__ == "__main__":
    main()

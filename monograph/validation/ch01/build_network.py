#!/usr/bin/env python3
"""
build_network.py -- the human erythrocyte reaction network (stage A).

Rebuilds the network of the cycle-tolerance paper (cause-for-concern/docs/
disease-circuit-tolerance/validation/realdata, experiment R2) from the
same snapshot -- UniProtKB catalytic activities of 38 erythrocyte genes,
Rhea participants -- with the same exclusion rules, but identifies species
by species_key() instead of the InChIKey connectivity block, so that
anomers merge and epimers (glucose and mannose, ribulose and xylulose
5-phosphate) do not.

Writes, beside this script,
  species.csv   sid, key, conn14, chebi, kegg, formula, name
  network.csv   rhea, genes, uniprot, ec, name, status, stoich
where stoich is "coef*sid coef*sid ..." (negative = consumed).

Needs equilibrator-cache 0.8.1 with the full compound cache:

    python build_network.py
"""

from __future__ import annotations

import csv
import json
import os
import warnings
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)            # species_key.py lives beside this script
from species_key import species_key  # noqa: E402
REALDATA = os.path.normpath(os.path.join(
    HERE, "..", "..", "..", "cause-for-concern", "docs",
    "disease-circuit-tolerance", "validation", "realdata"))
RAW = os.path.join(REALDATA, "raw")


def main() -> None:
    warnings.filterwarnings("ignore")
    from equilibrator_cache import create_compound_cache_from_zenodo

    cc = create_compound_cache_from_zenodo(tier="full")
    proton = cc.get_compound("kegg:C00080").id

    # UniProt catalytic activities -> Rhea reactions (as in run_realdata.py)
    uni = json.load(open(os.path.join(RAW, "uniprot_erythrocyte.json"),
                         encoding="utf-8"))
    annot: dict = defaultdict(lambda: {"genes": set(), "acc": set(),
                                       "ec": set(), "name": ""})
    for gene, entries in uni.items():
        for e in entries:
            for c in e.get("comments", []):
                rr = c.get("reaction", {})
                for x in rr.get("reactionCrossReferences", []):
                    if x["database"] != "Rhea":
                        continue
                    a = annot[x["id"].split(":")[1]]
                    a["genes"].add(gene)
                    a["acc"].add(e["primaryAccession"])
                    if rr.get("ecNumber"):
                        a["ec"].add(rr["ecNumber"])
                    a["name"] = rr.get("name", "")

    parts: dict = defaultdict(list)
    with open(os.path.join(RAW, "rhea_participants.csv"),
              encoding="utf-8") as f:
        next(f)
        for line in f:
            rh_, order, coef, chebi = line.strip().split(",")
            parts[rh_.rsplit("/", 1)[1]].append(
                (int(order.split('"')[1]), coef.strip('"'),
                 chebi.rsplit("_", 1)[1] if chebi else None))

    species: dict = {}
    rows = []
    for rid in sorted(annot, key=int):
        a, st, why = annot[rid], defaultdict(int), None
        for order, coef, chebi in parts.get(rid, []):
            if chebi is None:
                why = "generic participant"; break
            if not coef.isdigit():
                why = "variable coefficient"; break
            c = cc.get_compound(f"chebi:CHEBI:{chebi}")
            if c is None or not c.inchi_key or not c.inchi:
                why = "no structure"; break
            if c.id == proton:
                continue
            key = species_key(c.inchi)
            if key not in species:
                kegg = next((i.accession for i in c.identifiers
                             if i.registry.namespace == "kegg"
                             and i.accession.startswith("C")), "")
                species[key] = {"key": key,
                                "conn14": c.inchi_key.split("-")[0],
                                "chebi": f"CHEBI:{chebi}", "kegg": kegg,
                                "formula": c.formula or "",
                                "name": c.get_common_name() or ""}
            st[key] += (-1 if order == 1 else 1) * int(coef)
        st = {k: v for k, v in st.items() if v}
        if why is None and not st:
            why = "no net chemistry"
        rows.append({"rhea": rid, "genes": ";".join(sorted(a["genes"])),
                     "uniprot": ";".join(sorted(a["acc"])),
                     "ec": ";".join(sorted(a["ec"])), "name": a["name"],
                     "status": why or "included", "stoich": st})

    sid = {k: f"s{i:03d}" for i, k in enumerate(sorted(species), 1)}
    with open(os.path.join(HERE, "species.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sid", "key", "conn14", "chebi",
                                          "kegg", "formula", "name"])
        w.writeheader()
        for k in sorted(species):
            w.writerow({"sid": sid[k], **species[k]})
    with open(os.path.join(HERE, "network.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rhea", "genes", "uniprot", "ec",
                                          "name", "status", "stoich"])
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["stoich"] = " ".join(f"{v}*{sid[k]}" for k, v in
                                   sorted(r["stoich"].items(),
                                          key=lambda kv: sid[kv[0]]))
            w.writerow(r)
    n_inc = sum(r["status"] == "included" for r in rows)
    print(f"{len(rows)} Rhea reactions, {n_inc} included, "
          f"{len(species)} species")


if __name__ == "__main__":
    main()

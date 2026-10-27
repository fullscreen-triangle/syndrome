#!/usr/bin/env python3
"""
fetch_sources.py -- download the experimental data the real-data analysis uses.

Three public sources, each saved verbatim under raw/ with its retrieval
date and SHA-256 recorded in raw/SOURCES.json:

  TECRDB    measured apparent equilibrium constants K' of enzyme-catalysed
            reactions (Goldberg et al. 2004, NIST), as distributed with
            component-contribution (Noor et al. 2013), pinned to one commit
  UniProt   the catalytic activities annotated in UniProtKB/Swiss-Prot for
            the human erythrocyte enzymes listed in GENES, with their Rhea
            reaction identifiers
  Rhea      the participants (ChEBI identifier, side, coefficient) of every
            one of those reactions, from the Rhea SPARQL endpoint

The analysis (run_realdata.py) reads only raw/, so it is reproducible
from the saved snapshot without network access. Re-running this script
refreshes the snapshot and will change it as the databases are updated.

    python fetch_sources.py
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

CC_COMMIT = "67d3804f7cf8e5a909ab0c81d7b3d628cd2207cb"
TECRDB_URL = ("https://raw.githubusercontent.com/eladnoor/component-contribution/"
              f"{CC_COMMIT}/src/component_contribution/data/TECRDB.csv.gz")

# Human erythrocyte central metabolism: glycolysis, the Rapoport-Luebering
# shunt, the pentose phosphate pathway, nucleotide interconversion and
# salvage, glutathione metabolism, and the two ATP-driven ion pumps --
# the scope of the published erythrocyte models (Mulquiney & Kuchel 1999).
GENES = """HK1 GPI PFKL PFKM ALDOA TPI1 GAPDH PGK1 BPGM MINPP1 PGAM1 ENO1
PKLR LDHA LDHB G6PD PGLS PGD RPE RPIA TKT TALDO1 PGM1 AK1 NME1 NME2 GSR
GPX1 GCLC GSS ADA AMPD3 PNP APRT HPRT1 PRPS1 ATP1A1 ATP2B4""".split()

RHEA_SPARQL = "https://sparql.rhea-db.org/sparql"
RHEA_QUERY = """PREFIX rh:<http://rdf.rhea-db.org/>
SELECT ?rhea ?order ?coef ?chebi WHERE {
 VALUES ?rhea { %s }
 ?rhea rh:side ?side . ?side rh:curatedOrder ?order .
 ?side ?contains ?p . ?contains rh:coefficient ?coef .
 ?p rh:compound ?c . OPTIONAL { ?c rh:chebi ?chebi . } }"""


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "cfc-realdata"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save(name: str, data: bytes, url: str, sources: dict) -> None:
    with open(os.path.join(RAW, name), "wb") as f:
        f.write(data)
    sources[name] = {"url": url, "sha256": hashlib.sha256(data).hexdigest(),
                     "bytes": len(data)}
    print(f"saved raw/{name} ({len(data)} bytes)")


def main() -> None:
    os.makedirs(RAW, exist_ok=True)
    sources = {"retrieved": datetime.date.today().isoformat()}

    save("TECRDB.csv.gz", get(TECRDB_URL), TECRDB_URL, sources)

    uniprot = {}
    for gene in GENES:
        q = f"gene_exact:{gene} AND organism_id:9606 AND reviewed:true"
        url = ("https://rest.uniprot.org/uniprotkb/search?query="
               + urllib.parse.quote(q)
               + "&fields=accession,gene_primary,protein_name,"
                 "cc_catalytic_activity&format=json")
        uniprot[gene] = json.loads(get(url))["results"]
    save("uniprot_erythrocyte.json",
         json.dumps(uniprot, indent=1, sort_keys=True).encode(),
         "https://rest.uniprot.org/uniprotkb/search (one query per gene)",
         sources)

    rhea_ids = sorted({x["id"].split(":")[1]
                       for entries in uniprot.values() for e in entries
                       for c in e.get("comments", [])
                       for x in c.get("reaction", {}).get(
                           "reactionCrossReferences", [])
                       if x["database"] == "Rhea"}, key=int)
    query = RHEA_QUERY % " ".join("rh:" + r for r in rhea_ids)
    url = RHEA_SPARQL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "csv"})
    save("rhea_participants.csv", get(url), RHEA_SPARQL, sources)
    sources["rhea_query"] = query
    sources["genes"] = GENES

    with open(os.path.join(RAW, "SOURCES.json"), "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2)
    print("wrote raw/SOURCES.json")


if __name__ == "__main__":
    main()

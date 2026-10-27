#!/usr/bin/env python3
"""
run_realdata.py -- the cycle-consistency test on experimental data.

Two experiments on the snapshot that fetch_sources.py saved under raw/:

  R1  Measured equilibrium constants (TECRDB). Every measured apparent
      constant K' is reverse-transformed to the chemical reference state
      at the conditions it was measured under (pH, ionic strength,
      temperature, pMg), exactly as component contribution prepares its
      training data (Noor et al. 2013). Each reaction is then an edge whose
      datum d_e = Delta_r G deg is an independent measurement -- not a
      difference of formation energies, which would cancel on every cycle.
      The cycle space of the measured reactions is spanned by an exact
      integer basis of ker S, and each cycle sum is judged by a fixed
      tolerance and by the cycle-local tolerance eps* = eps_num + eps_data.
      Repeated measurements of one reaction are cycles whose true sum is
      known to be zero; they calibrate the data floor on the data itself.

  R2  The human erythrocyte network. The catalytic activities annotated in
      UniProtKB/Swiss-Prot for the erythrocyte enzymes, as Rhea reactions,
      give the stoichiometry. The question is which reactions lie on a
      cycle at all -- a reaction on no cycle is invisible to any
      cycle-consistency test -- and which cycles have a measured constant
      on every edge.

Stage A needs the eQuilibrator compound cache (pKa data and structures)
and writes plain tables under derived/. Stage B needs only numpy and
pandas and writes results_real.json, so the analysis can be repeated
from derived/ without eQuilibrator:

    python run_realdata.py              # stage A then stage B
    python run_realdata.py --from-derived
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from fractions import Fraction
from statistics import NormalDist

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, DERIVED = os.path.join(HERE, "raw"), os.path.join(HERE, "derived")

R_GAS = 8.314462618e-3            # kJ/(mol K)
ALPHA = 0.01
U = 2.0 ** -53                    # unit roundoff, IEEE 754 binary64
EPS_FIXED = 1e-6                  # the customary fixed tolerance, kJ/mol
T_WINDOW = (293.15, 313.15)       # K; Delta_r G deg is not corrected for T
GRADES = ("A", "B", "C")          # TECRDB evaluation grades admitted
N_BASES = 200                     # random column orders for basis checks
SEED = 20261021
PK_EC = "2.7.1.40"


# ---------------------------------------------------------------------
# shared: reactions as sparse integer vectors, written canonically
# ---------------------------------------------------------------------

def canonical(st: dict) -> tuple[str, int]:
    """Orientation-free string for a reaction; the sign maps data to it."""
    items = sorted((k, Fraction(v)) for k, v in st.items() if v != 0)
    neg = sorted((k, -v) for k, v in items)
    sgn = 1
    if neg < items:
        items, sgn = neg, -1
    return " ".join(f"{v}*{k}" for k, v in items), sgn


def parse_canonical(s: str) -> dict:
    out = {}
    for tok in s.split():
        v, k = tok.split("*", 1)
        out[k] = Fraction(v)
    return out


# ---------------------------------------------------------------------
# stage A: transform the raw data (needs eQuilibrator)
# ---------------------------------------------------------------------

def stage_a() -> None:
    import warnings
    warnings.filterwarnings("ignore")
    from equilibrator_api import Q_
    from equilibrator_cache import create_compound_cache_from_zenodo

    cc = create_compound_cache_from_zenodo(tier="full")
    proton = cc.get_compound("kegg:C00080").id
    memo: dict = {}

    def compound(ns: str, acc: str):
        if (ns, acc) not in memo:
            memo[(ns, acc)] = cc.get_compound(f"{ns}:{acc}")
        return memo[(ns, acc)]

    def connectivity(c) -> str:
        return c.inchi_key.split("-")[0] if c.inchi_key else f"eq{c.id}"

    os.makedirs(DERIVED, exist_ok=True)

    # --- TECRDB ---------------------------------------------------------
    d = pd.read_csv(os.path.join(RAW, "TECRDB.csv.gz"))
    d = d[~d[["K'", "T", "pH"]].isna().any(axis=1)].copy()
    d["I"] = d["I"].fillna(0.25)          # component contribution defaults
    d["pMg"] = d["pMg"].fillna(14.0)

    def parse_kegg(s: str) -> dict:
        out: dict = defaultdict(Fraction)
        lhs, rhs = s.split(" = ")
        for side, sgn in ((lhs, -1), (rhs, 1)):
            for term in side.split(" + "):
                t = term.split()
                coef, cid = (Fraction(t[0]), t[1]) if len(t) == 2 \
                    else (Fraction(1), t[0])
                out[cid] += sgn * coef
        return {k: v for k, v in out.items() if v}

    def balance(rx: dict):
        """Balance O with H2O and H with H+, then drop H+ (as component
        contribution does). None if a compound lacks a structure or any
        other element is unbalanced."""
        rx = dict(rx)
        bag: dict = defaultdict(Fraction)
        for cid, v in rx.items():
            c = compound("kegg", cid)
            if c is None or not c.atom_bag:
                return None, "no structure"
            for el, n in c.atom_bag.items():
                if el != "e-":
                    bag[el] += v * n
        rx["C00001"] = rx.get("C00001", 0) - bag["O"]
        rx.pop("C00080", None)
        if any(v for el, v in bag.items() if el not in ("H", "O")):
            return None, "unbalanced"
        return {k: v for k, v in rx.items() if v}, None

    rows, dropped = [], Counter()
    for idx, r in d.iterrows():
        rx, why = balance(parse_kegg(r["REACTION IN KEGG IDS"]))
        if rx is None:
            dropped[why] += 1
            continue
        ddg = sum(float(v) * compound("kegg", cid).transform(
            p_h=Q_(r["pH"]), ionic_strength=Q_(r["I"], "M"),
            temperature=Q_(r["T"], "K"), p_mg=Q_(r["pMg"])
        ).m_as("kJ/mol") for cid, v in rx.items())
        dg0_prime = -R_GAS * r["T"] * math.log(r["K'"])
        kegg, sgn = canonical(rx)
        conn: dict = defaultdict(Fraction)
        for cid, v in rx.items():
            conn[connectivity(compound("kegg", cid))] += sgn * v
        conn_s, conn_sgn = canonical(conn)
        rows.append({
            "tecrdb_row": idx, "ref": r["REF_ID"], "ec": r["EC"],
            "enzyme": r["ENZYME NAME"], "eval": r["EVAL"],
            "T": r["T"], "pH": r["pH"], "I": r["I"], "pMg": r["pMg"],
            "dG0_prime_measured": dg0_prime, "transform": ddg,
            "reaction": kegg, "reaction_connectivity": conn_s,
            "dG0": sgn * (dg0_prime - ddg),
            # the same value, oriented as reaction_connectivity is written
            "dG0_connectivity": conn_sgn * sgn * (dg0_prime - ddg),
        })
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(DERIVED, "tecrdb_transformed.csv"), index=False)
    print(f"TECRDB: {len(d)} rows with K', T, pH; kept {len(t)}; "
          f"dropped {dict(dropped)}")

    # --- erythrocyte network (UniProt + Rhea) ---------------------------
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
    for line in open(os.path.join(RAW, "rhea_participants.csv"),
                     encoding="utf-8").read().strip().splitlines()[1:]:
        rh_, order, coef, chebi = line.split(",")
        parts[rh_.rsplit("/", 1)[1]].append(
            (int(order.split('"')[1]), coef.strip('"'),
             chebi.rsplit("_", 1)[1] if chebi else None))

    rows = []
    for rid in sorted(annot, key=int):
        a, st, why = annot[rid], defaultdict(Fraction), None
        for order, coef, chebi in parts.get(rid, []):
            if chebi is None:
                why = "generic participant"; break
            if not coef.isdigit():
                why = "variable coefficient"; break
            c = compound("chebi", "CHEBI:" + chebi)
            if c is None or not c.inchi_key:
                why = "no structure"; break
            if c.id == proton:
                continue
            st[connectivity(c)] += (-1 if order == 1 else 1) * int(coef)
        st = {k: v for k, v in st.items() if v}
        if why is None and not st:
            why = "no net chemistry"
        rows.append({
            "rhea": rid, "genes": ";".join(sorted(a["genes"])),
            "uniprot": ";".join(sorted(a["acc"])),
            "ec": ";".join(sorted(a["ec"])), "name": a["name"],
            "status": why or "included",
            "reaction_connectivity": canonical(st)[0] if why is None else "",
        })
    e = pd.DataFrame(rows)
    e.to_csv(os.path.join(DERIVED, "erythrocyte_reactions.csv"), index=False)
    print(f"erythrocyte: {len(e)} Rhea reactions, "
          f"{(e.status == 'included').sum()} included; "
          f"{e.status.value_counts().to_dict()}")


# ---------------------------------------------------------------------
# stage B: the analysis (numpy and pandas only)
# ---------------------------------------------------------------------

def gamma(n: int) -> float:
    return n * U / (1 - n * U)


def cycle_basis(reactions: list, rng=None) -> list:
    """An integer basis of ker S by exact elimination over the rationals.

    Columns are taken in the given order (permuted by rng if given); each
    non-pivot column yields one fundamental cycle. Returns a list of
    {reaction: integer coefficient} with coprime coefficients.
    """
    cols = list(reactions)
    if rng is not None:
        cols = [cols[i] for i in rng.permutation(len(cols))]
    stoich = [parse_canonical(c) for c in cols]
    species = sorted({k for s in stoich for k in s})
    rows = [{} for _ in species]
    where = {k: i for i, k in enumerate(species)}
    for j, s in enumerate(stoich):
        for k, v in s.items():
            rows[where[k]][j] = v
    pivots, reduced = [], []
    for row in rows:
        row = dict(row)
        for pc, pr in zip(pivots, reduced):
            if pc in row:
                f = row[pc]
                for k, v in pr.items():
                    nv = row.get(k, 0) - f * v
                    if nv:
                        row[k] = nv
                    else:
                        row.pop(k, None)
        if not row:
            continue
        pc = min(row)
        f = row[pc]
        row = {k: v / f for k, v in row.items()}
        for pr in reduced:
            if pc in pr:
                h = pr[pc]
                for k, v in row.items():
                    nv = pr.get(k, 0) - h * v
                    if nv:
                        pr[k] = nv
                    else:
                        pr.pop(k, None)
        pivots.append(pc)
        reduced.append(row)
    pivot_set = set(pivots)
    basis = []
    for f in (j for j in range(len(cols)) if j not in pivot_set):
        z = {f: Fraction(1)}
        for pc, pr in zip(pivots, reduced):
            if f in pr:
                z[pc] = -pr[f]
        den = math.lcm(*(v.denominator for v in z.values()))
        zi = {cols[k]: int(v * den) for k, v in z.items()}
        g = math.gcd(*zi.values())
        basis.append({k: v // g for k, v in zi.items()})
    return basis


def judge(basis: list, value: dict, sigma: dict, q: float) -> list:
    """Cycle sum, both floors and both verdicts for every basis cycle."""
    out = []
    for z in basis:
        terms = [v * value[r] for r, v in z.items()]
        h = sum(terms)                                  # as a user computes it
        e_num = gamma(len(z)) * sum(abs(x) for x in terms)
        s = math.sqrt(sum(v * v * sigma[r] ** 2 for r, v in z.items()))
        e_data = q * s
        a = abs(h)
        verdict = ("CONSISTENT" if a <= e_num else
                   "UNDECIDABLE" if a <= e_num + e_data else "INCONSISTENT")
        out.append({"length": len(z), "H": h, "eps_num": e_num,
                    "eps_data": e_data, "Z": h / s, "verdict": verdict,
                    "fixed": "INCONSISTENT" if a > EPS_FIXED
                    else "CONSISTENT", "cycle": z})
    return out


def r1(tec: pd.DataFrame) -> dict:
    m = tec[tec["T"].between(*T_WINDOW) & tec["eval"].isin(GRADES)]
    # one value per study: conditions repeated within a study are not
    # independent replicates of the reaction
    study = m.groupby(["reaction", "ref"]).dG0.mean().reset_index()
    g = study.groupby("reaction").dG0
    rx = pd.DataFrame({"value": g.mean(), "n": g.size()})
    rep = study.merge(rx, left_on="reaction", right_index=True)
    rep = rep[rep.n >= 2]
    dev = rep.dG0 - rep.value
    sigma_pool = math.sqrt((dev ** 2).sum() / (rx[rx.n >= 2].n - 1).sum())

    # Replicates as cycles of known sum zero: leave-one-out deviation of
    # each study from the others, standardised by the pooled model.
    loo = []
    for _, grp in study.groupby("reaction"):
        x = grp.dG0.to_numpy()
        n = len(x)
        if n < 2:
            continue
        for i in range(n):
            rest = np.delete(x, i)
            loo.append((x[i] - rest.mean())
                       / (sigma_pool * math.sqrt(1 + 1 / (n - 1))))
    loo = np.abs(np.array([v for v in loo if np.isfinite(v)]))
    z_gauss = NormalDist().inv_cdf(1 - ALPHA / 2)
    q_emp = float(np.quantile(loo, 1 - ALPHA))
    q_cheb = ALPHA ** -0.5
    quantiles = {"gaussian": z_gauss, "replicate_calibrated": q_emp,
                 "chebyshev": q_cheb}

    value = rx.value.to_dict()
    sigma = (sigma_pool / np.sqrt(rx.n)).to_dict()
    reactions = sorted(rx.index)
    basis = cycle_basis(reactions)
    judged = {k: judge(basis, value, sigma, q) for k, q in quantiles.items()}
    main = judged["gaussian"]
    hs = np.array([abs(c["H"]) for c in main])
    zs = np.array([c["Z"] for c in main])
    lengths = np.array([c["length"] for c in main])

    # basis dependence: the same cycle space, other fundamental bases
    rng = np.random.default_rng(SEED)
    n_flag, witness, agree = [], Counter(), 0
    ref_any = any(c["verdict"] == "INCONSISTENT" for c in main)
    for _ in range(N_BASES):
        b = cycle_basis(reactions, rng)
        jb = judge(b, value, sigma, z_gauss)
        flagged = [c for c in jb if c["verdict"] == "INCONSISTENT"]
        n_flag.append(len(flagged))
        agree += (len(flagged) > 0) == ref_any
        for r in {r for c in flagged for r in c["cycle"]}:
            witness[r] += 1
    names = m.groupby("reaction").agg(enzyme=("enzyme", "first"),
                                      ec=("ec", "first"))

    def describe(c):
        return {"H": round(c["H"], 3), "eps_star": round(c["eps_num"]
                                                         + c["eps_data"], 3),
                "Z": round(c["Z"], 2), "length": c["length"],
                "edges": [{"coef": v, "ec": names.at[r, "ec"],
                           "enzyme": names.at[r, "enzyme"],
                           "studies": int(rx.at[r, "n"]),
                           "dG0": round(value[r], 2)}
                          for r, v in c["cycle"].items()]}

    return {
        "inclusion": {"T_window_K": T_WINDOW, "grades": GRADES,
                      "measurements": int(len(m)),
                      "studies": int(len(study)),
                      "reactions": int(len(rx)),
                      "reactions_with_2plus_studies": int((rx.n >= 2).sum())},
        "sigma_pool_kJmol": sigma_pool,
        "replicate_calibration": {
            "n_deviations": int(len(loo)),
            "frac_beyond_gaussian_quantile": float((loo > z_gauss).mean()),
            "nominal": ALPHA, "q99_abs": q_emp,
            "q95_abs": float(np.quantile(loo, 0.95)),
            "max_abs": float(loo.max())},
        "quantiles": quantiles,
        "cycle_space_dimension": len(basis),
        "cycle_length": {"min": int(lengths.min()),
                         "median": float(np.median(lengths)),
                         "max": int(lengths.max())},
        "abs_cycle_sum_kJmol": {"min": float(hs.min()),
                                "median": float(np.median(hs)),
                                "max": float(hs.max())},
        "eps_num_range": [min(c["eps_num"] for c in main),
                          max(c["eps_num"] for c in main)],
        "eps_data_range": [min(c["eps_data"] for c in main),
                           max(c["eps_data"] for c in main)],
        "orders_of_magnitude_gap_median": float(np.median(
            [math.log10(c["eps_data"] / c["eps_num"]) for c in main])),
        "fixed_tolerance": {
            "eps": EPS_FIXED,
            "flagged": sum(c["fixed"] == "INCONSISTENT" for c in main),
            "flagged_at": {str(e): int((hs > e).sum())
                           for e in (1e-6, 1e-3, 1.0, 5.0, 10.0)}},
        "verdicts": {k: dict(Counter(c["verdict"] for c in v))
                     for k, v in judged.items()},
        "Z_sd": float(zs.std(ddof=1)),
        "Z_frac_beyond_gaussian_quantile": float(
            (np.abs(zs) > z_gauss).mean()),
        "flagged_cycles_gaussian": [describe(c) for c in main
                                    if c["verdict"] == "INCONSISTENT"],
        "cycles": [{k: c[k] for k in ("length", "H", "eps_num", "eps_data",
                                      "Z", "verdict")} for c in main],
        "replicate_abs_deviations": sorted(float(v) for v in loo),
        "basis_dependence": {
            "bases": N_BASES,
            "network_verdict_agreement": agree / N_BASES,
            "n_flagged_min": int(min(n_flag)), "n_flagged_max": int(max(n_flag)),
            "witness_reactions": [
                {"enzyme": names.at[r, "enzyme"], "ec": names.at[r, "ec"],
                 "studies": int(rx.at[r, "n"]), "frac_bases": k / N_BASES}
                for r, k in witness.most_common() if k / N_BASES >= 0.5]},
    }


def r2(tec: pd.DataFrame, ery: pd.DataFrame) -> dict:
    inc = ery[ery.status == "included"].drop_duplicates(
        "reaction_connectivity")
    reactions = sorted(inc.reaction_connectivity)
    stoich = [parse_canonical(r) for r in reactions]
    species = sorted({k for s in stoich for k in s})
    S = np.array([[float(s.get(k, 0)) for s in stoich] for k in species])
    rank = np.linalg.matrix_rank(S)
    on_cycle = {r: bool(np.linalg.matrix_rank(np.delete(S, j, axis=1)) == rank)
                for j, r in enumerate(reactions)}
    label = inc.set_index("reaction_connectivity")

    # measured constants matched at the level of molecular connectivity
    m = tec[tec["T"].between(*T_WINDOW) & tec["eval"].isin(GRADES)]
    study = m.groupby(["reaction_connectivity", "ref"]).dG0_connectivity.mean()
    per = study.groupby(level=0).agg(["mean", "size"])
    measured = {r: int(per.at[r, "size"]) for r in reactions if r in per.index}

    basis = cycle_basis(reactions)
    cycles = []
    for z in basis:
        cycles.append({
            "length": len(z),
            "edges_measured": sum(r in measured for r in z),
            "edges": [{"coef": v, "genes": label.at[r, "genes"],
                       "ec": label.at[r, "ec"], "name": label.at[r, "name"],
                       "studies": measured.get(r, 0)}
                      for r, v in z.items()]})
    pk = [r for r in reactions if PK_EC in label.at[r, "ec"].split(";")]
    sub = sorted(measured)
    sub_basis = cycle_basis(sub) if sub else []
    return {
        "genes": int(ery.genes.str.split(";").explode().nunique()),
        "rhea_reactions": int(len(ery)),
        "excluded": ery[ery.status != "included"].status.value_counts()
                                                 .to_dict(),
        "reactions": len(reactions), "species": len(species),
        "rank": int(rank), "cycle_space_dimension": len(reactions) - int(rank),
        "reactions_on_a_cycle": int(sum(on_cycle.values())),
        "pyruvate_kinase_on_a_cycle": [on_cycle[r] for r in pk],
        "glycolytic_reactions_on_no_cycle": sorted(
            label.at[r, "genes"] + " " + label.at[r, "ec"]
            for r in reactions if not on_cycle[r]
            and any(g in label.at[r, "genes"] for g in
                    ("HK1", "GPI", "PFK", "ALDOA", "TPI1", "GAPDH", "PGK1",
                     "PGAM1", "ENO1", "PKLR", "LDH")))[:40],
        "reactions_with_measured_K": len(measured),
        "cycles": cycles,
        "cycles_fully_measured": sum(c["edges_measured"] == c["length"]
                                     for c in cycles),
        "measured_subnetwork_cycle_space_dimension": len(sub_basis),
    }


def stage_b() -> dict:
    tec = pd.read_csv(os.path.join(DERIVED, "tecrdb_transformed.csv"))
    ery = pd.read_csv(os.path.join(DERIVED, "erythrocyte_reactions.csv"),
                      dtype=str).fillna("")
    out = {"R1_tecrdb": r1(tec), "R2_erythrocyte": r2(tec, ery)}
    sens = r1(tec[tec["eval"] == "A"])
    out["R1_sensitivity_grade_A_only"] = {
        k: sens[k] for k in ("inclusion", "sigma_pool_kJmol",
                             "cycle_space_dimension", "verdicts",
                             "fixed_tolerance", "replicate_calibration",
                             "replicate_abs_deviations")}
    out["sources"] = json.load(open(os.path.join(RAW, "SOURCES.json")))
    path = os.path.join(HERE, "results_real.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=lambda o: int(o)
                  if isinstance(o, np.integer) else str(o))
    print("wrote", path)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-derived", action="store_true")
    args = ap.parse_args()
    if not args.from_derived:
        stage_a()
    res = stage_b()
    a, b = res["R1_tecrdb"], res["R2_erythrocyte"]
    print(f"R1: {a['inclusion']['reactions']} reactions, cycle space "
          f"{a['cycle_space_dimension']}, fixed 1e-6 flags "
          f"{a['fixed_tolerance']['flagged']}; verdicts {a['verdicts']}")
    print(f"R2: {b['reactions']} reactions, cycle space "
          f"{b['cycle_space_dimension']}, PK on a cycle "
          f"{b['pyruvate_kinase_on_a_cycle']}, fully measured cycles "
          f"{b['cycles_fully_measured']}")

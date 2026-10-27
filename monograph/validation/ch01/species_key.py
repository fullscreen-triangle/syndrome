"""
species_key.py -- identify a chemical species up to anomers, not up to
stereoisomers.

The first block of an InChIKey encodes constitution only, so it merges
every stereoisomer: D-glucose with D-mannose, D-ribulose 5-phosphate with
D-xylulose 5-phosphate. Rhea, on the other hand, distinguishes alpha and
beta anomers (alpha-D-glucose 6-phosphate in one reaction, unspecified
D-glucose 6-phosphate in the next), and anomers interconvert
spontaneously in water, so a network that kept them apart would break
pathways that are continuous in the cell.

The key used here keeps every stereocentre except anomeric ones. A
stereocentre is anomeric if it is a carbon bonded to two oxygens (the
hemiacetal or hemiketal carbon of a ring sugar). Its parity is dropped;
every other parity is kept; and a centre left unspecified in the InChI
stays unspecified. Two species then share a key exactly when they have
one constitution and agree at every non-anomeric centre.

The function needs only the standard InChI string.
"""

from __future__ import annotations

import re


def _layers(inchi: str) -> dict:
    parts = inchi.split("/")
    out = {"formula": parts[1]}
    for p in parts[2:]:
        if p:
            out.setdefault(p[0], p[1:])
    return out


def _atoms(formula: str) -> list:
    """Element of each atom in InChI numbering (C first, then H skipped,
    then the rest alphabetically, which is the order of the formula)."""
    elems = []
    for sym, n in re.findall(r"([A-Z][a-z]?)(\d*)", formula.split(".")[0]):
        if sym == "H":
            continue
        elems += [sym] * (int(n) if n else 1)
    return elems


def _bonds(conn: str) -> dict:
    """Adjacency from the InChI connection layer, e.g. 7-1-2(9)3(10)..."""
    adj: dict = {}
    stack, prev = [], None
    tok = re.findall(r"\d+|[()\-,]", conn)
    for t in tok:
        if t.isdigit():
            a = int(t)
            if prev is not None:
                adj.setdefault(prev, set()).add(a)
                adj.setdefault(a, set()).add(prev)
            prev = a
        elif t == "(":
            stack.append(prev)
        elif t == ")":
            prev = stack.pop()
        elif t == ",":
            prev = stack[-1] if stack else prev
    return adj


def species_key(inchi: str) -> str:
    """Constitution plus non-anomeric stereo parities."""
    if not inchi or not inchi.startswith("InChI="):
        return ""
    L = _layers(inchi)
    formula, conn = L["formula"], L.get("c", "")
    elems = _atoms(formula)
    adj = _bonds(conn.split(";")[0])
    anomeric = {a for a, nb in adj.items()
                if 0 < a <= len(elems) and elems[a - 1] == "C"
                and sum(elems[b - 1] == "O" for b in nb
                        if 0 < b <= len(elems)) >= 2}
    kept = []
    for item in L.get("t", "").split(";")[0].split(","):
        m = re.fullmatch(r"(\d+)([-+?u])", item)
        if m and int(m.group(1)) not in anomeric and m.group(2) in "+-":
            kept.append(m.group(1) + m.group(2))
    # The /m layer flips every /t parity (an enantiomer written as its
    # mirror image); keep it so that D and L forms stay apart.
    mirror = L.get("m", "")
    double = L.get("b", "")
    # Standard InChI writes the neutral parent and puts protonation in the
    # /p layer, which is not read here, so microspecies share a key while
    # NAD+ and NADH (different formula) do not.
    return f"{formula}|{conn}|b{double}|t{','.join(kept)}|m{mirror}"

#!/usr/bin/env python3
"""
make_word.py -- Word versions of the manuscript and supplementary.

pandoc cannot evaluate cleveref, so each .tex is first copied to a
"for Word" version in which every \\Cref, \\cref, \\eqref and \\ref is
replaced by the text LaTeX printed for it, read from the compiled .aux
files. pandoc then converts that copy, resolving citations in APA style.

Run after a full LaTeX build of both documents (the .aux files must be
current):

    python make_word.py
"""

from __future__ import annotations

import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN, SUPP = "medinformatics-submission", "medinformatics-supplementary"

NAMES = {
    "theorem": ("Theorem", "Theorems"), "lemma": ("Lemma", "Lemmas"),
    "proposition": ("Proposition", "Propositions"),
    "corollary": ("Corollary", "Corollaries"),
    "definition": ("Definition", "Definitions"),
    "assumption": ("Assumption", "Assumptions"),
    "criterion": ("Criterion", "Criteria"),
    "protocol": ("Protocol", "Protocols"), "rulename": ("Rule", "Rules"),
    "remark": ("Remark", "Remarks"), "section": ("Section", "Sections"),
    "subsection": ("Section", "Sections"),
    "subsubsection": ("Section", "Sections"),
    "figure": ("Figure", "Figures"), "table": ("Table", "Tables"),
    "equation": ("Equation", "Equations"),
}
LABEL = re.compile(
    r"\\newlabel\{(?P<key>[^{}]+)@cref\}\{\{\[(?P<type>[a-z]+)\]"
    r"\[[^\]]*\]\[[^\]]*\](?P<num>[^{}]*)\}")


def read_labels(*auxes: str) -> dict:
    out = {}
    for aux in auxes:
        with open(os.path.join(HERE, aux + ".aux"), encoding="utf-8") as f:
            for m in LABEL.finditer(f.read()):
                out.setdefault(m["key"], (m["type"], m["num"]))
    return out


def number(labels: dict, key: str) -> tuple:
    if key not in labels:
        raise SystemExit(f"unresolved reference: {key} (rebuild LaTeX first)")
    typ, num = labels[key]
    return typ, (f"({num})" if typ == "equation" else num)


def join(items: list) -> str:
    return items[0] if len(items) == 1 else \
        ", ".join(items[:-1]) + " and " + items[-1]


def cref(labels: dict, keys: str, capital: bool) -> str:
    groups = []                      # consecutive runs of one type
    keys = re.sub(r"%[^\n]*\n", "", keys)        # LaTeX line continuations
    for key in (k.strip() for k in keys.split(",")):
        typ, num = number(labels, key)
        name = NAMES[typ]
        if groups and groups[-1][0] == name:
            groups[-1][1].append(num)
        else:
            groups.append((name, [num]))
    parts = []
    for (sing, plur), nums in groups:
        word = sing if len(nums) == 1 else plur
        parts.append(f"{word if capital else word.lower()} {join(nums)}")
    return join(parts)


ENVS = ("theorem", "lemma", "proposition", "corollary", "definition",
        "assumption", "criterion", "protocol", "rulename", "remark")
BEGIN = re.compile(
    r"\\begin\{(?P<env>" + "|".join(ENVS) + r")\}"
    r"(?:\[(?P<title>(?:[^\[\]]|\[[^\]]*\])*)\])?"
    r"(?P<label>\s*\\label\{(?P<key>[^}]+)\})?")
SECTION = re.compile(r"\\section\{")


def number_headings(text: str, labels: dict, supplementary: bool) -> str:
    """Write each result's heading with the number LaTeX gives it.

    pandoc numbers theorem environments without the section prefix, so
    the headings are written out here instead. Main text: Section.n, the
    counter reset at each numbered section. Supplementary: Sn, never
    reset. Every labelled result is checked against the .aux.
    """
    out, pos, sec, n = [], 0, 0, 0
    events = sorted([(m.start(), "sec", m) for m in SECTION.finditer(text)] +
                    [(m.start(), "env", m) for m in BEGIN.finditer(text)],
                    key=lambda e: e[0])
    for start, kind, m in events:
        if kind == "sec":
            sec, n = sec + 1, 0
            continue
        n += 1
        num = f"S{n}" if supplementary else f"{sec}.{n}"
        if m["key"]:
            want = labels.get(m["key"], (None, num))[1]
            if want != num:
                raise SystemExit(f"numbering drift at {m['key']}: "
                                 f"computed {num}, LaTeX says {want}")
        name = NAMES[m["env"]][0]
        title = f" ({m['title']})" if m["title"] else ""
        label = f"\\label{{{m['key']}}}" if m["key"] else ""
        out.append(text[pos:start])
        out.append(f"\\par\\noindent\\textbf{{{name} {num}{title}.}}{label} ")
        pos = m.end()
    out.append(text[pos:])
    text = "".join(out)
    return re.sub(r"\\end\{(" + "|".join(ENVS) + r")\}", r"\\par", text)


def resolve(text: str, labels: dict) -> str:
    text = re.sub(r"\\(C|c)ref\{([^}]*)\}",
                  lambda m: cref(labels, m[2], m[1] == "C"), text)
    text = re.sub(r"\\eqref\{([^}]*)\}",
                  lambda m: number(labels, m[1])[1], text)
    text = re.sub(r"\\ref\{([^}]*)\}",
                  lambda m: number(labels, m[1])[1], text)
    # The supplementary imports the main text's labels for LaTeX only.
    text = re.sub(r"\\externaldocument\{[^}]*\}\n?", "", text)
    # pandoc does not understand aliased counters and would number each
    # environment on its own; plain shared counters number as LaTeX does.
    # (The aliases exist only so that cleveref names the references,
    # which are already resolved to text above.)
    text = re.sub(r"\\newcommand\{\\newsharedtheorem\}.*?\n(?:  .*\n)",
                  "", text)
    text = re.sub(r"\\newsharedtheorem\{(\w+)\}\{([^}]*)\}",
                  r"\\newtheorem{\1}[theorem]{\2}", text)
    return text.replace("\\usepackage{aliascnt}\n", "")


def build(stem: str, labels: dict, word_tex: str,
          supplementary: bool = False) -> None:
    with open(os.path.join(HERE, stem + ".tex"), encoding="utf-8") as f:
        src = f.read()
    body_at = src.index("\\begin{document}")
    head, body = src[:body_at], src[body_at:]
    body = number_headings(body, labels, supplementary)
    with open(os.path.join(HERE, word_tex), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(resolve(head + body, labels))
    subprocess.run(
        ["pandoc", word_tex, "--citeproc", "--bibliography=references.bib",
         "--csl=apa.csl", "--resource-path=.", "-o", stem + ".docx"],
        cwd=HERE, check=True)
    print("wrote", stem + ".docx")


if __name__ == "__main__":
    main_labels = read_labels(MAIN)
    build(MAIN, main_labels, "medinformatics-forword.tex")
    build(SUPP, read_labels(SUPP, MAIN),
          "medinformatics-supplementary-forword.tex", supplementary=True)

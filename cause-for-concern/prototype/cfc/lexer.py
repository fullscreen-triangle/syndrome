"""
cfc.lexer -- tokeniser for the Cause-for-Concern prototype language.

Hand-written scanner. No dependencies. Produces a flat token list with
line/column information so that later stages can report source
positions, which the accountability design requires: a dropped residue
or an omitted tolerance has to be attributable to a place in the text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator, List, Optional


class TokKind(Enum):
    KEYWORD = auto()
    TYPENAME = auto()
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    OP = auto()
    LBRACE = auto()
    RBRACE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    NEWLINE = auto()
    EOF = auto()


# Statement/verb keywords.  Order matters only for readability.
KEYWORDS = {
    # declarations
    "floor", "import", "let", "circuit", "species", "reaction", "from",
    "network", "basis", "probe", "panel", "patient",
    # circuit verbs
    "solve", "holonomy", "of", "in", "loops", "wegscheider", "check",
    "centre_potentials", "minimum_cycle_basis", "fundamental_basis",
    # tolerance / verdict verbs  (the subject of the companion paper)
    "tolerance", "with", "admit", "witness", "perturb",
    "perturb_edge",
    # measurement verbs
    "measure", "localize", "using", "until", "close", "gap", "toward",
    "coherent", "resolved", "contested",
    # control / reporting
    "yield", "assert", "otherwise", "decline", "invalid", "emit",
    "report", "foreach", "where", "collect", "into", "scan", "against",
    "as", "and", "or", "not",
}

TYPENAMES = {
    "Circuit", "Loop", "Holonomy", "Tolerance", "Verdict", "Witness",
    "Reading", "Cell", "Gap", "Probe", "Panel", "Concern",
    "CONSISTENT", "UNDECIDABLE", "INCONSISTENT",
}

# Multi-character operators must precede their prefixes.
OPERATORS = [
    "==", "!=", "<=", ">=", ":=", "->", ">>", "||",
    "<", ">", "+", "-", "*", "/", ".", "=",
]

_NUMBER_RE = re.compile(r"""
    (?:
        \d+ \. \d* (?:[eE][+-]?\d+)?     # 1.  1.5  1.5e-6
      | \. \d+     (?:[eE][+-]?\d+)?     # .5
      | \d+        (?:[eE][+-]?\d+)?     # 1  1e-6
    )
""", re.VERBOSE)

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class LexError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"{msg} at line {line}, column {col}")
        self.msg, self.line, self.col = msg, line, col


@dataclass(frozen=True)
class Token:
    kind: TokKind
    value: str
    line: int
    col: int

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Token({self.kind.name}, {self.value!r}, {self.line}:{self.col})"

    def is_kw(self, *names: str) -> bool:
        return self.kind is TokKind.KEYWORD and self.value in names


_PUNCT = {
    "{": TokKind.LBRACE,
    "}": TokKind.RBRACE,
    "(": TokKind.LPAREN,
    ")": TokKind.RPAREN,
    "[": TokKind.LBRACKET,
    "]": TokKind.RBRACKET,
    ",": TokKind.COMMA,
    ":": TokKind.COLON,
}


def tokenize(src: str) -> List[Token]:
    """Scan `src` into a token list terminated by a single EOF token.

    Newlines are emitted as tokens because the grammar is
    statement-per-line; runs of blank lines collapse to one, so the
    parser never has to skip them in a loop.
    """
    toks: List[Token] = []
    i, line, col = 0, 1, 1
    n = len(src)

    def push(kind: TokKind, value: str, ln: int, cl: int) -> None:
        toks.append(Token(kind, value, ln, cl))

    while i < n:
        ch = src[i]

        # ---- line comment: -- to end of line -------------------------
        if ch == "-" and i + 1 < n and src[i + 1] == "-":
            while i < n and src[i] != "\n":
                i += 1
            continue

        # ---- newline -------------------------------------------------
        if ch == "\n":
            if toks and toks[-1].kind is not TokKind.NEWLINE:
                push(TokKind.NEWLINE, "\\n", line, col)
            i += 1
            line += 1
            col = 1
            continue

        # ---- other whitespace ---------------------------------------
        if ch in " \t\r":
            i += 1
            col += 1
            continue

        # ---- string --------------------------------------------------
        if ch == '"':
            start_line, start_col = line, col
            i += 1
            col += 1
            buf = []
            while True:
                if i >= n or src[i] == "\n":
                    raise LexError("unterminated string", start_line, start_col)
                if src[i] == "\\" and i + 1 < n:
                    esc = src[i + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"',
                                "\\": "\\"}.get(esc, esc))
                    i += 2
                    col += 2
                    continue
                if src[i] == '"':
                    i += 1
                    col += 1
                    break
                buf.append(src[i])
                i += 1
                col += 1
            push(TokKind.STRING, "".join(buf), start_line, start_col)
            continue

        # ---- number --------------------------------------------------
        m = _NUMBER_RE.match(src, i)
        if m and (ch.isdigit() or (ch == "." and i + 1 < n and src[i + 1].isdigit())):
            push(TokKind.NUMBER, m.group(0), line, col)
            col += len(m.group(0))
            i = m.end()
            continue

        # ---- identifier / keyword / typename -------------------------
        m = _IDENT_RE.match(src, i)
        if m:
            word = m.group(0)
            if word in KEYWORDS:
                kind = TokKind.KEYWORD
            elif word in TYPENAMES:
                kind = TokKind.TYPENAME
            else:
                kind = TokKind.IDENT
            push(kind, word, line, col)
            col += len(word)
            i = m.end()
            continue

        # ---- operators ----------------------------------------------
        for op in OPERATORS:
            if src.startswith(op, i):
                push(TokKind.OP, op, line, col)
                i += len(op)
                col += len(op)
                break
        else:
            # ---- punctuation -----------------------------------------
            if ch in _PUNCT:
                push(_PUNCT[ch], ch, line, col)
                i += 1
                col += 1
                continue
            raise LexError(f"unexpected character {ch!r}", line, col)

    if toks and toks[-1].kind is not TokKind.NEWLINE:
        push(TokKind.NEWLINE, "\\n", line, col)
    push(TokKind.EOF, "", line, col)
    return toks


def iter_significant(toks: List[Token]) -> Iterator[Token]:
    """Yield tokens with NEWLINE removed -- for expression contexts."""
    for t in toks:
        if t.kind is not TokKind.NEWLINE:
            yield t

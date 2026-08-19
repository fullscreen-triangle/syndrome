"""
cfc.parser -- recursive-descent parser producing the AST of ast_nodes.

Grammar notes worth stating, because they are the point of the language
rather than incidental syntax:

  * `admit H tolerance T yield v` is the ONLY production with a Verdict
    in its result.  Both operands are mandatory, so a verdict cannot be
    produced without the tolerance that justifies it, and a comparison
    of a holonomy against a numeric literal has no production at all.

  * `tolerance of L with S yield t` requires the `with` clause naming
    the uncertainty source.  There is no default and no literal form.

These two facts are what make the omission unwritable rather than
merely discouraged.
"""

from __future__ import annotations

from typing import List, Optional

from .ast_nodes import (
    Assert, Attr, AdmitStmt, BinOp, Call, CircuitDecl, Emit, FloorDecl,
    Foreach, HolonomyStmt, Import, Let, ListLit, Name, Node, Num,
    Program, ReactionDecl, Report, Solve, SpeciesDecl, Str, ToleranceStmt,
    TypeLit, UnOp, WhereCollect, WitnessStmt,
)
from .lexer import Token, TokKind, tokenize


class ParseError(Exception):
    def __init__(self, msg: str, tok: Token):
        super().__init__(f"{msg} at line {tok.line}, column {tok.col} "
                         f"(near {tok.value!r})")
        self.msg, self.tok = msg, tok


# Binary operator precedence, loosest first.
_PREC = [
    {"or"},
    {"and"},
    {"==", "!=", "<", ">", "<=", ">="},
    {"+", "-"},
    {"*", "/"},
]


class Parser:
    def __init__(self, toks: List[Token]):
        self.toks = toks
        self.i = 0

    # ---------------- token helpers ----------------------------------

    @property
    def cur(self) -> Token:
        return self.toks[self.i]

    def at_kw(self, *names: str) -> bool:
        return self.cur.kind is TokKind.KEYWORD and self.cur.value in names

    def at_op(self, *ops: str) -> bool:
        return self.cur.kind is TokKind.OP and self.cur.value in ops

    def advance(self) -> Token:
        t = self.cur
        if t.kind is not TokKind.EOF:
            self.i += 1
        return t

    def expect(self, kind: TokKind, value: Optional[str] = None) -> Token:
        t = self.cur
        if t.kind is not kind or (value is not None and t.value != value):
            want = value if value is not None else kind.name
            raise ParseError(f"expected {want}", t)
        return self.advance()

    def expect_kw(self, name: str) -> Token:
        if not self.at_kw(name):
            raise ParseError(f"expected keyword {name!r}", self.cur)
        return self.advance()

    def skip_newlines(self) -> None:
        while self.cur.kind is TokKind.NEWLINE:
            self.advance()

    def end_stmt(self) -> None:
        """Consume the statement terminator, tolerating EOF and '}'."""
        if self.cur.kind is TokKind.NEWLINE:
            self.advance()
        elif self.cur.kind in (TokKind.EOF, TokKind.RBRACE):
            return
        else:
            raise ParseError("expected end of statement", self.cur)

    # ---------------- entry point ------------------------------------

    def parse_program(self) -> Program:
        stmts: List[Node] = []
        self.skip_newlines()
        while self.cur.kind is not TokKind.EOF:
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return Program(line=1, stmts=stmts)

    def parse_block(self) -> List[Node]:
        self.expect(TokKind.LBRACE)
        self.skip_newlines()
        body: List[Node] = []
        while self.cur.kind is not TokKind.RBRACE:
            if self.cur.kind is TokKind.EOF:
                raise ParseError("unterminated block", self.cur)
            body.append(self.parse_stmt())
            self.skip_newlines()
        self.expect(TokKind.RBRACE)
        return body

    # ---------------- statements -------------------------------------

    def parse_stmt(self) -> Node:
        t = self.cur
        if t.kind is TokKind.KEYWORD:
            handler = {
                "floor": self.p_floor,
                "import": self.p_import,
                "let": self.p_let,
                "circuit": self.p_circuit,
                "species": self.p_species,
                "reaction": self.p_reaction,
                "solve": self.p_solve,
                "holonomy": self.p_holonomy,
                "tolerance": self.p_tolerance,
                "admit": self.p_admit,
                "witness": self.p_witness,
                "assert": self.p_assert,
                "emit": self.p_emit,
                "report": self.p_report,
                "foreach": self.p_foreach,
                "where": self.p_where,
            }.get(t.value)
            if handler is not None:
                return handler()
        raise ParseError("unrecognised statement", t)

    def p_floor(self) -> Node:
        ln = self.expect_kw("floor").line
        v = self.parse_expr()
        self.end_stmt()
        return FloorDecl(line=ln, value=v)

    def p_import(self) -> Node:
        ln = self.expect_kw("import").line
        parts = [self.expect(TokKind.IDENT).value]
        while self.at_op("."):
            self.advance()
            tok = self.cur
            if tok.kind not in (TokKind.IDENT, TokKind.TYPENAME):
                raise ParseError("expected name after '.'", tok)
            parts.append(self.advance().value)
        alias = None
        if self.at_kw("as"):
            self.advance()
            alias = self.expect(TokKind.IDENT).value
        self.end_stmt()
        return Import(line=ln, module=".".join(parts), alias=alias)

    def p_let(self) -> Node:
        ln = self.expect_kw("let").line
        target = self.expect(TokKind.IDENT).value
        if self.at_op(":="):
            self.advance()
        elif self.at_op("="):
            self.advance()
        else:
            raise ParseError("expected ':=' in let", self.cur)
        expr = self.parse_expr()
        self.end_stmt()
        return Let(line=ln, target=target, expr=expr)

    def p_circuit(self) -> Node:
        ln = self.expect_kw("circuit").line
        name = self.expect(TokKind.IDENT).value
        source = None
        if self.at_kw("from"):
            self.advance()
            source = self.parse_expr()
        body = self.parse_block() if self.cur.kind is TokKind.LBRACE else []
        self.end_stmt()
        return CircuitDecl(line=ln, name=name, source=source, body=body)

    def p_species(self) -> Node:
        ln = self.expect_kw("species").line
        name = self.expect(TokKind.IDENT).value
        self.expect(TokKind.COLON)
        fields = {}
        while True:
            key = self.expect(TokKind.IDENT).value
            self.expect(TokKind.COLON)
            fields[key] = self.parse_expr()
            if self.cur.kind is TokKind.COMMA:
                self.advance()
                continue
            break
        self.end_stmt()
        if "mu0" not in fields or "concentration" not in fields:
            raise ParseError(
                "species requires 'mu0' and 'concentration'", self.cur)
        return SpeciesDecl(line=ln, name=name, mu0=fields["mu0"],
                           concentration=fields["concentration"],
                           sigma=fields.get("sigma"))

    def p_reaction(self) -> Node:
        ln = self.expect_kw("reaction").line
        name = self.expect(TokKind.IDENT).value
        self.expect(TokKind.COLON)
        src = self.expect(TokKind.IDENT).value
        self.expect(TokKind.OP, "->")
        dst = self.expect(TokKind.IDENT).value
        self.expect(TokKind.COMMA)
        key = self.expect(TokKind.IDENT).value
        if key != "k":
            raise ParseError("expected 'k' in reaction", self.cur)
        self.expect(TokKind.COLON)
        k = self.parse_expr()
        self.end_stmt()
        return ReactionDecl(line=ln, name=name, src=src, dst=dst, k=k)

    def p_solve(self) -> Node:
        ln = self.expect_kw("solve").line
        self.expect_kw("yield")
        target = self.expect(TokKind.IDENT).value
        self.end_stmt()
        return Solve(line=ln, target=target)

    def p_holonomy(self) -> Node:
        ln = self.expect_kw("holonomy").line
        self.expect_kw("of")
        loop = self.parse_expr()
        self.expect_kw("in")
        circ = self.parse_expr()
        self.expect_kw("yield")
        target = self.expect(TokKind.IDENT).value
        self.end_stmt()
        return HolonomyStmt(line=ln, loop=loop, circuit=circ, target=target)

    def p_tolerance(self) -> Node:
        """`tolerance of L with S yield t`  --  `with` is mandatory."""
        ln = self.expect_kw("tolerance").line
        self.expect_kw("of")
        loop = self.parse_expr()
        if not self.at_kw("with"):
            raise ParseError(
                "tolerance requires a 'with <uncertainty-source>' clause; "
                "there is no default and no literal form", self.cur)
        self.advance()
        sigma_src = self.parse_expr()
        self.expect_kw("yield")
        target = self.expect(TokKind.IDENT).value
        self.end_stmt()
        return ToleranceStmt(line=ln, loop=loop, sigma_src=sigma_src,
                             target=target)

    def p_admit(self) -> Node:
        """`admit H tolerance T yield v` -- only Verdict introduction."""
        ln = self.expect_kw("admit").line
        hol = self.parse_expr()
        if not self.at_kw("tolerance"):
            raise ParseError(
                "admit requires a 'tolerance <T>' clause: a verdict may "
                "not be produced without the tolerance that justifies it",
                self.cur)
        self.advance()
        tol = self.parse_expr()
        self.expect_kw("yield")
        target = self.expect(TokKind.IDENT).value
        self.end_stmt()
        return AdmitStmt(line=ln, holonomy=hol, tolerance=tol, target=target)

    def p_witness(self) -> Node:
        ln = self.expect_kw("witness").line
        self.expect_kw("of")
        flagged = self.parse_expr()
        self.expect_kw("yield")
        target = self.expect(TokKind.IDENT).value
        self.end_stmt()
        return WitnessStmt(line=ln, flagged=flagged, target=target)

    def _peek_kw_across_newlines(self, *names: str) -> bool:
        """Look ahead past newlines for a continuation keyword.

        `assert`'s optional `emit` / `otherwise` clauses are
        conventionally written on indented continuation lines, so the
        statement terminator must not hide them.
        """
        j = self.i
        while self.toks[j].kind is TokKind.NEWLINE:
            j += 1
        t = self.toks[j]
        return t.kind is TokKind.KEYWORD and t.value in names

    def _consume_to_kw(self) -> None:
        while self.cur.kind is TokKind.NEWLINE:
            self.advance()

    def p_assert(self) -> Node:
        ln = self.expect_kw("assert").line
        cond = self.parse_expr()
        emit_ok = None
        otherwise = None
        emit_bad = None

        if self._peek_kw_across_newlines("emit"):
            self._consume_to_kw()
            self.advance()
            emit_ok = self.expect(TokKind.STRING).value

        if self._peek_kw_across_newlines("otherwise"):
            self._consume_to_kw()
            self.advance()
            self._consume_to_kw()
            if self.at_kw("decline"):
                otherwise = "decline"
                self.advance()
            elif self.at_kw("invalid"):
                otherwise = "invalid"
                self.advance()
            else:
                raise ParseError("expected 'decline' or 'invalid'", self.cur)
            if self._peek_kw_across_newlines("emit"):
                self._consume_to_kw()
                self.advance()
                emit_bad = self.expect(TokKind.STRING).value

        self.end_stmt()
        return Assert(line=ln, cond=cond, emit_ok=emit_ok,
                      otherwise=otherwise, emit_bad=emit_bad)

    def p_emit(self) -> Node:
        ln = self.expect_kw("emit").line
        msg = self.expect(TokKind.STRING).value
        self.end_stmt()
        return Emit(line=ln, message=msg)

    def p_report(self) -> Node:
        ln = self.expect_kw("report").line
        items = [self.parse_expr()]
        while self.cur.kind is TokKind.COMMA:
            self.advance()
            items.append(self.parse_expr())
        self.end_stmt()
        return Report(line=ln, items=items)

    def p_foreach(self) -> Node:
        ln = self.expect_kw("foreach").line
        var = self.expect(TokKind.IDENT).value
        self.expect_kw("in")
        it = self.parse_expr()
        body = self.parse_block()
        self.end_stmt()
        return Foreach(line=ln, var=var, iterable=it, body=body)

    def p_where(self) -> Node:
        ln = self.expect_kw("where").line
        cond = self.parse_expr()
        self.expect_kw("collect")
        expr = self.parse_expr()
        self.expect_kw("into")
        target = self.expect(TokKind.IDENT).value
        self.end_stmt()
        return WhereCollect(line=ln, cond=cond, expr=expr, target=target)

    # ---------------- expressions ------------------------------------

    def parse_expr(self, level: int = 0) -> Node:
        if level >= len(_PREC):
            return self.parse_unary()
        lhs = self.parse_expr(level + 1)
        while True:
            t = self.cur
            matched = (
                (t.kind is TokKind.OP and t.value in _PREC[level]) or
                (t.kind is TokKind.KEYWORD and t.value in _PREC[level])
            )
            if not matched:
                return lhs
            op = self.advance().value
            rhs = self.parse_expr(level + 1)
            lhs = BinOp(line=t.line, op=op, lhs=lhs, rhs=rhs)

    def parse_unary(self) -> Node:
        t = self.cur
        if self.at_op("-") or self.at_kw("not"):
            op = self.advance().value
            return UnOp(line=t.line, op=op, operand=self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self) -> Node:
        node = self.parse_atom()
        while True:
            if self.at_op("."):
                ln = self.advance().line
                tok = self.cur
                if tok.kind not in (TokKind.IDENT, TokKind.TYPENAME,
                                    TokKind.KEYWORD):
                    raise ParseError("expected attribute name", tok)
                node = Attr(line=ln, base=node, attr=self.advance().value)
            elif self.cur.kind is TokKind.LPAREN and isinstance(node, (Name, Attr)):
                ln = self.advance().line
                args: List[Node] = []
                if self.cur.kind is not TokKind.RPAREN:
                    args.append(self.parse_expr())
                    while self.cur.kind is TokKind.COMMA:
                        self.advance()
                        args.append(self.parse_expr())
                self.expect(TokKind.RPAREN)
                fname = node.ident if isinstance(node, Name) else node.attr
                node = Call(line=ln, fn=fname, args=args)
            else:
                return node

    def parse_atom(self) -> Node:
        t = self.cur
        if t.kind is TokKind.NUMBER:
            self.advance()
            return Num(line=t.line, value=float(t.value))
        if t.kind is TokKind.STRING:
            self.advance()
            return Str(line=t.line, value=t.value)
        if t.kind is TokKind.TYPENAME:
            self.advance()
            return TypeLit(line=t.line, name=t.value)
        if t.kind is TokKind.IDENT:
            self.advance()
            return Name(line=t.line, ident=t.value)
        if t.kind is TokKind.LPAREN:
            self.advance()
            e = self.parse_expr()
            self.expect(TokKind.RPAREN)
            return e
        if t.kind is TokKind.LBRACE:
            # empty collection literal `{}`
            self.advance()
            self.skip_newlines()
            self.expect(TokKind.RBRACE)
            return ListLit(line=t.line, items=[])
        if t.kind is TokKind.LBRACKET:
            self.advance()
            items: List[Node] = []
            self.skip_newlines()
            if self.cur.kind is not TokKind.RBRACKET:
                items.append(self.parse_expr())
                while self.cur.kind is TokKind.COMMA:
                    self.advance()
                    self.skip_newlines()
                    items.append(self.parse_expr())
            self.skip_newlines()
            self.expect(TokKind.RBRACKET)
            return ListLit(line=t.line, items=items)
        # Some keywords double as callable builtins.
        if t.kind is TokKind.KEYWORD and t.value in {
            "centre_potentials", "minimum_cycle_basis", "fundamental_basis",
            "perturb", "perturb_edge", "coherent", "resolved",
            "contested", "decline",
        }:
            self.advance()
            return Name(line=t.line, ident=t.value)
        raise ParseError("unexpected token in expression", t)


def parse(src: str) -> Program:
    return Parser(tokenize(src)).parse_program()

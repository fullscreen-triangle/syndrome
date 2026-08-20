/**
 * cfc/parser.js -- recursive descent, ported from the Python reference.
 *
 * The two grammar facts that carry the language's guarantees:
 *
 *   `admit H tolerance T yield v` is the ONLY production yielding a
 *   Verdict, and both operands are mandatory. A comparison of a
 *   holonomy against a numeric literal has no production at all.
 *
 *   `tolerance of L with S yield t` requires the `with` clause. There
 *   is no default and no literal form.
 *
 * These make the omission unwritable rather than merely discouraged,
 * and the IDE surfaces the resulting parse errors verbatim.
 */

import { tokenize } from "./lexer.js";

export class ParseError extends Error {
  constructor(msg, tok) {
    super(`${msg} at line ${tok.line}, column ${tok.col} (near '${tok.value}')`);
    this.tok = tok;
    this.line = tok.line;
  }
}

// `in` is deliberately NOT here. It is a binary operator only inside a
// condition (assert / where), because elsewhere it is a grammar keyword:
// `holonomy of L in C` and `foreach x in xs` both need it unconsumed.
// parseCond() below re-admits it for exactly those positions.
const PREC = [
  new Set(["or"]),
  new Set(["and"]),
  new Set(["==", "!=", "<", ">", "<=", ">="]),
  new Set(["+", "-"]),
  new Set(["*", "/"]),
];

const IN_LEVEL = 2;   // same precedence as the comparisons

const CALLABLE_KEYWORDS = new Set([
  "centre_potentials", "minimum_cycle_basis", "fundamental_basis",
  "perturb", "perturb_edge",
]);

class Parser {
  constructor(toks) {
    this.toks = toks;
    this.i = 0;
  }
  get cur() { return this.toks[this.i]; }
  atKw(...names) { return this.cur.kind === "KEYWORD" && names.includes(this.cur.value); }
  atOp(...ops) { return this.cur.kind === "OP" && ops.includes(this.cur.value); }
  advance() { const t = this.cur; if (t.kind !== "EOF") this.i++; return t; }

  expect(kind, value) {
    const t = this.cur;
    if (t.kind !== kind || (value !== undefined && t.value !== value)) {
      throw new ParseError(`expected ${value ?? kind}`, t);
    }
    return this.advance();
  }
  expectKw(name) {
    if (!this.atKw(name)) throw new ParseError(`expected keyword '${name}'`, this.cur);
    return this.advance();
  }
  skipNewlines() { while (this.cur.kind === "NEWLINE") this.advance(); }
  endStmt() {
    if (this.cur.kind === "NEWLINE") this.advance();
    else if (this.cur.kind === "EOF" || this.cur.kind === "RBRACE") return;
    else throw new ParseError("expected end of statement", this.cur);
  }
  peekKwAcrossNewlines(...names) {
    let j = this.i;
    while (this.toks[j].kind === "NEWLINE") j++;
    const t = this.toks[j];
    return t.kind === "KEYWORD" && names.includes(t.value);
  }
  consumeNewlines() { while (this.cur.kind === "NEWLINE") this.advance(); }

  parseProgram() {
    const stmts = [];
    this.skipNewlines();
    while (this.cur.kind !== "EOF") {
      stmts.push(this.parseStmt());
      this.skipNewlines();
    }
    return { type: "Program", stmts, line: 1 };
  }

  parseBlock() {
    this.expect("LBRACE");
    this.skipNewlines();
    const body = [];
    while (this.cur.kind !== "RBRACE") {
      if (this.cur.kind === "EOF") throw new ParseError("unterminated block", this.cur);
      body.push(this.parseStmt());
      this.skipNewlines();
    }
    this.expect("RBRACE");
    return body;
  }

  parseStmt() {
    const t = this.cur;
    if (t.kind === "KEYWORD") {
      const h = {
        floor: () => this.pFloor(), import: () => this.pImport(),
        let: () => this.pLet(), circuit: () => this.pCircuit(),
        species: () => this.pSpecies(), reaction: () => this.pReaction(),
        solve: () => this.pSolve(), holonomy: () => this.pHolonomy(),
        tolerance: () => this.pTolerance(), admit: () => this.pAdmit(),
        witness: () => this.pWitness(), assert: () => this.pAssert(),
        emit: () => this.pEmit(), report: () => this.pReport(),
        foreach: () => this.pForeach(), where: () => this.pWhere(),
      }[t.value];
      if (h) return h();
    }
    throw new ParseError("unrecognised statement", t);
  }

  pFloor() {
    const ln = this.expectKw("floor").line;
    const value = this.parseExpr();
    this.endStmt();
    return { type: "FloorDecl", value, line: ln };
  }

  pImport() {
    const ln = this.expectKw("import").line;
    const parts = [this.expect("IDENT").value];
    while (this.atOp(".")) {
      this.advance();
      const tok = this.cur;
      if (tok.kind !== "IDENT" && tok.kind !== "TYPENAME") {
        throw new ParseError("expected name after '.'", tok);
      }
      parts.push(this.advance().value);
    }
    let alias = null;
    if (this.atKw("as")) { this.advance(); alias = this.expect("IDENT").value; }
    this.endStmt();
    return { type: "Import", module: parts.join("."), alias, line: ln };
  }

  pLet() {
    const ln = this.expectKw("let").line;
    const target = this.expect("IDENT").value;
    if (this.atOp(":=") || this.atOp("=")) this.advance();
    else throw new ParseError("expected ':=' in let", this.cur);
    const expr = this.parseExpr();
    this.endStmt();
    return { type: "Let", target, expr, line: ln };
  }

  pCircuit() {
    const ln = this.expectKw("circuit").line;
    const name = this.expect("IDENT").value;
    let source = null;
    if (this.atKw("from")) { this.advance(); source = this.parseExpr(); }
    const body = this.cur.kind === "LBRACE" ? this.parseBlock() : [];
    this.endStmt();
    return { type: "CircuitDecl", name, source, body, line: ln };
  }

  pSpecies() {
    const ln = this.expectKw("species").line;
    const name = this.expect("IDENT").value;
    this.expect("COLON");
    const fields = {};
    for (;;) {
      const key = this.expect("IDENT").value;
      this.expect("COLON");
      fields[key] = this.parseExpr();
      if (this.cur.kind === "COMMA") { this.advance(); continue; }
      break;
    }
    this.endStmt();
    if (!("mu0" in fields) || !("concentration" in fields)) {
      throw new ParseError("species requires 'mu0' and 'concentration'", this.cur);
    }
    return {
      type: "SpeciesDecl", name, mu0: fields.mu0,
      concentration: fields.concentration, sigma: fields.sigma ?? null, line: ln,
    };
  }

  pReaction() {
    const ln = this.expectKw("reaction").line;
    const name = this.expect("IDENT").value;
    this.expect("COLON");
    const src = this.expect("IDENT").value;
    this.expect("OP", "->");
    const dst = this.expect("IDENT").value;
    this.expect("COMMA");
    const key = this.expect("IDENT").value;
    if (key !== "k") throw new ParseError("expected 'k' in reaction", this.cur);
    this.expect("COLON");
    const k = this.parseExpr();
    this.endStmt();
    return { type: "ReactionDecl", name, src, dst, k, line: ln };
  }

  pSolve() {
    const ln = this.expectKw("solve").line;
    this.expectKw("yield");
    const target = this.expect("IDENT").value;
    this.endStmt();
    return { type: "Solve", target, line: ln };
  }

  pHolonomy() {
    const ln = this.expectKw("holonomy").line;
    this.expectKw("of");
    const loop = this.parseExpr();
    this.expectKw("in");
    const circuit = this.parseExpr();
    this.expectKw("yield");
    const target = this.expect("IDENT").value;
    this.endStmt();
    return { type: "HolonomyStmt", loop, circuit, target, line: ln };
  }

  pTolerance() {
    const ln = this.expectKw("tolerance").line;
    this.expectKw("of");
    const loop = this.parseExpr();
    if (!this.atKw("with")) {
      throw new ParseError(
        "tolerance requires a 'with <uncertainty-source>' clause; " +
        "there is no default and no literal form", this.cur);
    }
    this.advance();
    const sigmaSrc = this.parseExpr();
    this.expectKw("yield");
    const target = this.expect("IDENT").value;
    this.endStmt();
    return { type: "ToleranceStmt", loop, sigmaSrc, target, line: ln };
  }

  pAdmit() {
    const ln = this.expectKw("admit").line;
    const holonomy = this.parseExpr();
    if (!this.atKw("tolerance")) {
      throw new ParseError(
        "admit requires a 'tolerance <T>' clause: a verdict may not be " +
        "produced without the tolerance that justifies it", this.cur);
    }
    this.advance();
    const tolerance = this.parseExpr();
    this.expectKw("yield");
    const target = this.expect("IDENT").value;
    this.endStmt();
    return { type: "AdmitStmt", holonomy, tolerance, target, line: ln };
  }

  pWitness() {
    const ln = this.expectKw("witness").line;
    this.expectKw("of");
    const flagged = this.parseExpr();
    this.expectKw("yield");
    const target = this.expect("IDENT").value;
    this.endStmt();
    return { type: "WitnessStmt", flagged, target, line: ln };
  }

  pAssert() {
    const ln = this.expectKw("assert").line;
    const cond = this.parseCond();
    let emitOk = null, otherwise = null, emitBad = null;
    if (this.peekKwAcrossNewlines("emit")) {
      this.consumeNewlines(); this.advance();
      emitOk = this.expect("STRING").value;
    }
    if (this.peekKwAcrossNewlines("otherwise")) {
      this.consumeNewlines(); this.advance(); this.consumeNewlines();
      if (this.atKw("decline")) { otherwise = "decline"; this.advance(); }
      else if (this.atKw("invalid")) { otherwise = "invalid"; this.advance(); }
      else throw new ParseError("expected 'decline' or 'invalid'", this.cur);
      if (this.peekKwAcrossNewlines("emit")) {
        this.consumeNewlines(); this.advance();
        emitBad = this.expect("STRING").value;
      }
    }
    this.endStmt();
    return { type: "Assert", cond, emitOk, otherwise, emitBad, line: ln };
  }

  pEmit() {
    const ln = this.expectKw("emit").line;
    const message = this.expect("STRING").value;
    this.endStmt();
    return { type: "Emit", message, line: ln };
  }

  pReport() {
    const ln = this.expectKw("report").line;
    const items = [this.parseExpr()];
    while (this.cur.kind === "COMMA") { this.advance(); items.push(this.parseExpr()); }
    this.endStmt();
    return { type: "Report", items, line: ln };
  }

  pForeach() {
    const ln = this.expectKw("foreach").line;
    const v = this.expect("IDENT").value;
    this.expectKw("in");
    const iterable = this.parseExpr();
    const body = this.parseBlock();
    this.endStmt();
    return { type: "Foreach", var: v, iterable, body, line: ln };
  }

  pWhere() {
    const ln = this.expectKw("where").line;
    const cond = this.parseCond();
    this.expectKw("collect");
    const expr = this.parseExpr();
    this.expectKw("into");
    const target = this.expect("IDENT").value;
    this.endStmt();
    return { type: "WhereCollect", cond, expr, target, line: ln };
  }

  // ---- expressions -------------------------------------------------

  /**
   * Parse an expression. `allowIn` admits the `in` operator, and is set
   * only by parseCond(); in every other position `in` belongs to the
   * enclosing statement's grammar and must be left for it.
   */
  parseExpr(level = 0, allowIn = false) {
    if (level >= PREC.length) return this.parseUnary();
    let lhs = this.parseExpr(level + 1, allowIn);
    for (;;) {
      const t = this.cur;
      const isIn = allowIn && level === IN_LEVEL &&
        t.kind === "KEYWORD" && t.value === "in";
      const hit = isIn ||
        (t.kind === "OP" && PREC[level].has(t.value)) ||
        (t.kind === "KEYWORD" && PREC[level].has(t.value));
      if (!hit) return lhs;
      const op = this.advance().value;
      const rhs = this.parseExpr(level + 1, allowIn);
      lhs = { type: "BinOp", op, lhs, rhs, line: t.line };
    }
  }

  /** Condition position: `in` is a real operator here. */
  parseCond() { return this.parseExpr(0, true); }

  parseUnary() {
    const t = this.cur;
    if (this.atOp("-") || this.atKw("not")) {
      const op = this.advance().value;
      return { type: "UnOp", op, operand: this.parseUnary(), line: t.line };
    }
    return this.parsePostfix();
  }

  parsePostfix() {
    let node = this.parseAtom();
    for (;;) {
      if (this.atOp(".")) {
        const ln = this.advance().line;
        const tok = this.cur;
        if (!["IDENT", "TYPENAME", "KEYWORD"].includes(tok.kind)) {
          throw new ParseError("expected attribute name", tok);
        }
        node = { type: "Attr", base: node, attr: this.advance().value, line: ln };
      } else if (this.cur.kind === "LPAREN" && (node.type === "Name" || node.type === "Attr")) {
        const ln = this.advance().line;
        const args = [];
        if (this.cur.kind !== "RPAREN") {
          args.push(this.parseExpr());
          while (this.cur.kind === "COMMA") { this.advance(); args.push(this.parseExpr()); }
        }
        this.expect("RPAREN");
        node = {
          type: "Call",
          fn: node.type === "Name" ? node.ident : node.attr,
          args, line: ln,
        };
      } else return node;
    }
  }

  parseAtom() {
    const t = this.cur;
    if (t.kind === "NUMBER") { this.advance(); return { type: "Num", value: parseFloat(t.value), line: t.line }; }
    if (t.kind === "STRING") { this.advance(); return { type: "Str", value: t.value, line: t.line }; }
    if (t.kind === "TYPENAME") { this.advance(); return { type: "TypeLit", name: t.value, line: t.line }; }
    if (t.kind === "IDENT") { this.advance(); return { type: "Name", ident: t.value, line: t.line }; }
    if (t.kind === "LPAREN") {
      this.advance();
      const e = this.parseExpr();
      this.expect("RPAREN");
      return e;
    }
    if (t.kind === "LBRACE") {
      this.advance(); this.skipNewlines(); this.expect("RBRACE");
      return { type: "ListLit", items: [], line: t.line };
    }
    if (t.kind === "LBRACKET") {
      this.advance();
      const items = [];
      this.skipNewlines();
      if (this.cur.kind !== "RBRACKET") {
        items.push(this.parseExpr());
        while (this.cur.kind === "COMMA") { this.advance(); this.skipNewlines(); items.push(this.parseExpr()); }
      }
      this.skipNewlines();
      this.expect("RBRACKET");
      return { type: "ListLit", items, line: t.line };
    }
    if (t.kind === "KEYWORD" && CALLABLE_KEYWORDS.has(t.value)) {
      this.advance();
      return { type: "Name", ident: t.value, line: t.line };
    }
    throw new ParseError("unexpected token in expression", t);
  }
}

export function parse(src) {
  return new Parser(tokenize(src)).parseProgram();
}

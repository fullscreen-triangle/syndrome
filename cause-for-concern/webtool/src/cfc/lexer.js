/**
 * cfc/lexer.js -- tokeniser, shared by the editor's syntax highlighter
 * and the interpreter, so that what you see coloured is exactly what
 * the parser sees.
 */

export const KEYWORDS = new Set([
  // declarations
  "floor", "import", "let", "circuit", "species", "reaction", "from",
  "network", "basis", "probe", "panel", "patient",
  // circuit verbs
  "solve", "holonomy", "of", "in", "loops", "wegscheider", "check",
  "centre_potentials", "minimum_cycle_basis", "fundamental_basis",
  // tolerance / verdict verbs
  "tolerance", "with", "admit", "witness", "perturb", "perturb_edge",
  // measurement verbs
  "measure", "localize", "using", "until", "close", "gap", "toward",
  "coherent", "resolved", "contested",
  // control / reporting
  "yield", "assert", "otherwise", "decline", "invalid", "emit",
  "report", "foreach", "where", "collect", "into", "scan", "against",
  "as", "and", "or", "not",
]);

export const TYPENAMES = new Set([
  "Circuit", "Loop", "Holonomy", "Tolerance", "Verdict", "Witness",
  "Reading", "Cell", "Gap", "Probe", "Panel", "Concern",
]);

export const CONSTANTS = new Set(["CONSISTENT", "UNDECIDABLE", "INCONSISTENT"]);

const OPERATORS = [
  "==", "!=", "<=", ">=", ":=", "->", ">>", "||",
  "<", ">", "+", "-", "*", "/", ".", "=",
];

const PUNCT = {
  "{": "LBRACE", "}": "RBRACE", "(": "LPAREN", ")": "RPAREN",
  "[": "LBRACKET", "]": "RBRACKET", ",": "COMMA", ":": "COLON",
};

export class LexError extends Error {
  constructor(msg, line, col) {
    super(`${msg} at line ${line}, column ${col}`);
    this.line = line;
    this.col = col;
  }
}

const NUM_RE = /^(?:\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?)/;
const IDENT_RE = /^[A-Za-z_][A-Za-z0-9_]*/;

export function tokenize(src) {
  const toks = [];
  let i = 0, line = 1, col = 1;
  const n = src.length;
  const push = (kind, value, ln, cl) => toks.push({ kind, value, line: ln, col: cl });

  while (i < n) {
    const ch = src[i];

    if (ch === "-" && src[i + 1] === "-") {           // comment
      while (i < n && src[i] !== "\n") i++;
      continue;
    }
    if (ch === "\n") {
      if (toks.length && toks[toks.length - 1].kind !== "NEWLINE") {
        push("NEWLINE", "\\n", line, col);
      }
      i++; line++; col = 1;
      continue;
    }
    if (ch === " " || ch === "\t" || ch === "\r") { i++; col++; continue; }

    if (ch === '"') {                                  // string
      const sl = line, sc = col;
      i++; col++;
      let buf = "";
      for (;;) {
        if (i >= n || src[i] === "\n") throw new LexError("unterminated string", sl, sc);
        if (src[i] === "\\" && i + 1 < n) {
          const e = src[i + 1];
          buf += { n: "\n", t: "\t", '"': '"', "\\": "\\" }[e] ?? e;
          i += 2; col += 2;
          continue;
        }
        if (src[i] === '"') { i++; col++; break; }
        buf += src[i]; i++; col++;
      }
      push("STRING", buf, sl, sc);
      continue;
    }

    const rest = src.slice(i);
    if (/\d/.test(ch) || (ch === "." && /\d/.test(src[i + 1] || ""))) {
      const m = NUM_RE.exec(rest);
      if (m) { push("NUMBER", m[0], line, col); i += m[0].length; col += m[0].length; continue; }
    }

    const mi = IDENT_RE.exec(rest);
    if (mi) {
      const w = mi[0];
      const kind = KEYWORDS.has(w) ? "KEYWORD"
        : TYPENAMES.has(w) || CONSTANTS.has(w) ? "TYPENAME" : "IDENT";
      push(kind, w, line, col);
      i += w.length; col += w.length;
      continue;
    }

    let matched = false;
    for (const op of OPERATORS) {
      if (rest.startsWith(op)) {
        push("OP", op, line, col);
        i += op.length; col += op.length;
        matched = true;
        break;
      }
    }
    if (matched) continue;

    if (PUNCT[ch]) { push(PUNCT[ch], ch, line, col); i++; col++; continue; }
    throw new LexError(`unexpected character '${ch}'`, line, col);
  }

  if (toks.length && toks[toks.length - 1].kind !== "NEWLINE") {
    push("NEWLINE", "\\n", line, col);
  }
  push("EOF", "", line, col);
  return toks;
}

/** Token classes for the editor, derived from the same tables. */
export function highlight(lineText) {
  const out = [];
  let i = 0;
  const n = lineText.length;
  while (i < n) {
    const ch = lineText[i];
    if (ch === "-" && lineText[i + 1] === "-") {
      out.push({ cls: "comment", text: lineText.slice(i) });
      break;
    }
    if (ch === '"') {
      let j = i + 1;
      while (j < n && lineText[j] !== '"') j++;
      out.push({ cls: "string", text: lineText.slice(i, Math.min(j + 1, n)) });
      i = j + 1;
      continue;
    }
    const rest = lineText.slice(i);
    if (/\d/.test(ch) || (ch === "." && /\d/.test(lineText[i + 1] || ""))) {
      const m = NUM_RE.exec(rest);
      if (m) { out.push({ cls: "number", text: m[0] }); i += m[0].length; continue; }
    }
    const mi = IDENT_RE.exec(rest);
    if (mi) {
      const w = mi[0];
      const cls = KEYWORDS.has(w) ? "keyword"
        : CONSTANTS.has(w) ? "constant"
        : TYPENAMES.has(w) ? "type" : "ident";
      out.push({ cls, text: w });
      i += w.length;
      continue;
    }
    if (/[><=!:.|{}[\](),*+\-/]/.test(ch)) {
      let op = ch;
      if (i + 1 < n && ":=><!|".includes(ch) && "=:>|".includes(lineText[i + 1])) {
        op += lineText[i + 1];
      }
      out.push({ cls: "operator", text: op });
      i += op.length;
      continue;
    }
    out.push({ cls: "plain", text: ch });
    i++;
  }
  return out;
}

/**
 * Reference.jsx -- the language reference, kept next to the editor so
 * the guarantees are readable while writing against them.
 */

import React from "react";

const MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";

const Code = ({ children }) => (
  <div style={{
    background: "#141414", border: "1px solid #2a2a2a", borderRadius: 4,
    padding: "8px 11px", fontFamily: MONO, fontSize: 11, color: "#9cdcfe",
    margin: "6px 0", whiteSpace: "pre-wrap", lineHeight: 1.65,
  }}>{children}</div>
);

const H = ({ children }) => (
  <div style={{
    fontSize: 12, color: "#fff", fontWeight: 600, marginTop: 20,
    marginBottom: 7, fontFamily: MONO,
  }}>{children}</div>
);

const P = ({ children }) => (
  <div style={{
    fontSize: 11.5, color: "#b0b0b0", lineHeight: 1.75, marginBottom: 8,
    maxWidth: 760,
  }}>{children}</div>
);

const K = ({ children }) => (
  <span style={{ fontFamily: MONO, color: "#569cd6" }}>{children}</span>
);

export default function Reference() {
  return (
    <div style={{ padding: "16px 22px", overflow: "auto", height: "100%" }}>
      <div style={{ fontSize: 14, color: "#fff", fontFamily: MONO }}>
        CFC language reference
      </div>
      <P>
        A small typed language for cycle-consistency experiments. Programs
        run in the browser against the same kernel the Python reference
        implementation uses; the two agree to machine precision.
      </P>

      <H>Building a circuit</H>
      <P>
        A species carries a standard potential, a concentration, and
        optionally the reported uncertainty on its potential. Omitting
        <K> sigma</K> is meaningful: it makes the data floor undefined.
      </P>
      <Code>{`circuit Reference {
  species G6P : mu0 : -1760.0, concentration : 0.5, sigma : 2.4
  reaction PFK : G6P -> FBP, k : 0.05
  solve yield C
}`}</Code>
      <P>
        <K>solve</K> computes μ = μ° + RT ln c, G = kc/RT and J = G·Δμ,
        and advances the committed-measurement clock.
      </P>

      <H>Cycles and gauge</H>
      <Code>{`let C := centre_potentials(C_ref)
let B := minimum_cycle_basis(C)`}</Code>
      <P>
        Centring shifts every potential so max |μ| is minimised. It changes
        no cycle sum — the sum telescopes — but it lowers the numerical
        floor, because rounding error scales with operand magnitude rather
        than with the difference.
      </P>

      <H>The two floors</H>
      <Code>{`holonomy of loop in C yield h
tolerance of loop with Reference yield t
admit h tolerance t yield v`}</Code>
      <P>
        <K>tolerance</K> computes both floors: ε_num = γ₂ₗ · 2LΛ from the
        arithmetic, and ε_data = z·√(Σσ²) from the reported uncertainty.
        The <K>with</K> clause is mandatory — there is no default and no
        literal form, so a tolerance cannot be conjured.
      </P>
      <P>
        <K>admit</K> is the only production yielding a <K>Verdict</K>, and
        both operands are required. Writing <K>admit h yield v</K> has no
        derivation in the grammar at all, so the omission is a parse error
        rather than a lint.
      </P>

      <H>The three verdicts</H>
      <Code>{`|H| ≤ ε_num              →  CONSISTENT
ε_num < |H| ≤ ε_data     →  UNDECIDABLE
|H| > ε*                 →  INCONSISTENT`}</Code>
      <P>
        <K>UNDECIDABLE</K> is a result, not an abstention: the signal is
        too large to be arithmetic and too small to be resolved by data of
        this quality. It also quantifies what would settle the question.
      </P>

      <H>Localisation</H>
      <Code>{`where v == INCONSISTENT collect loop into flagged
witness of flagged yield W`}</Code>
      <P>
        The witness set is the edges lying on every flagged cycle. Naming a
        single loop is not basis-independent — a different but equally
        valid cycle basis flags a different set — while the witness set
        contains the defect under any basis.
      </P>

      <H>Injecting a defect</H>
      <Code>{`perturb_edge(C, "SHNT", 40.0)   -- detectable
perturb(C, "G6P", 500.0)        -- NOT detectable`}</Code>
      <P>
        A thermodynamic inconsistency is a failure of the edge data to be
        a gradient. Shifting a node potential leaves the data the gradient
        of the shifted potential, so every cycle sum stays exactly zero.
        Only an edge offset creates a real defect — see
        <K> 05_node_vs_edge.cfc</K>.
      </P>

      <H>Terminal statuses</H>
      <Code>{`OK        every assertion held
NEGATIVE  an assertion failed or declined — a real result
INVALID   a reference check failed — no conclusion licensed
ERROR     the program could not be run`}</Code>
      <P>
        <K>otherwise invalid</K> and <K>otherwise decline</K> are not
        interchangeable. An invalid run says the substrate was never sound,
        so it licenses no conclusion about the hypothesis; a negative run
        says the test ran and did not detect the defect, which does.
      </P>

      <H>Not implemented</H>
      <P>
        This is the tolerance/verdict fragment. <K>measure</K>,
        <K> localize</K>, <K>close</K> and the gap-closure machinery are
        lexed but have no semantics here. <K>import</K> yields symbolic
        markers rather than fetching data, so every number that can change
        a verdict has to appear in the program text.
      </P>
    </div>
  );
}

/**
 * Landing.jsx -- the explanation page.
 *
 * This is the first thing a reader sees, and it has one job: to make the
 * rest of the workbench legible. It states the problem the system solves,
 * derives the two floors, gives the trichotomy, and says what the tool
 * does and does not implement.
 *
 * It is prose, not marketing: every quantitative claim here is one the
 * Lab reproduces live, and the numbers are written as the measurements
 * they are rather than rounded for effect.
 */

import React from "react";

const MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";
// Full page width: every block stretches to the pane rather than
// sitting in a fixed measure. "none" keeps the maxWidth props inert.
const COL = "none";

/* ---------------------------------------------------------------- atoms */

const H1 = ({ children }) => (
  <div style={{
    fontSize: 21, color: "#fff", fontWeight: 600, letterSpacing: -0.2,
    lineHeight: 1.35, maxWidth: COL,
  }}>{children}</div>
);

const H2 = ({ n, children }) => (
  <div style={{
    fontSize: 13, color: "#fff", fontWeight: 600, fontFamily: MONO,
    marginTop: 34, marginBottom: 10, display: "flex", gap: 10,
    alignItems: "baseline", maxWidth: COL,
  }}>
    {n !== undefined && <span style={{ color: "#569cd6", fontSize: 11.5 }}>{n}</span>}
    <span>{children}</span>
  </div>
);

const H3 = ({ children }) => (
  <div style={{
    fontSize: 11.5, color: "#d4d4d4", fontWeight: 600, fontFamily: MONO,
    marginTop: 18, marginBottom: 6, maxWidth: COL,
  }}>{children}</div>
);

const P = ({ children }) => (
  <div style={{
    fontSize: 12.5, color: "#b4b4b4", lineHeight: 1.85, marginBottom: 11,
    maxWidth: COL,
  }}>{children}</div>
);

const K = ({ children }) => (
  <span style={{ fontFamily: MONO, color: "#569cd6" }}>{children}</span>
);

const Em = ({ children }) => (
  <span style={{ color: "#d8d8d8", fontStyle: "italic" }}>{children}</span>
);

/** A displayed equation. Centred, monospaced, given room to breathe. */
const Eq = ({ children, note }) => (
  <div style={{ margin: "14px 0 16px", maxWidth: COL }}>
    <div style={{
      background: "#141414", border: "1px solid #2a2a2a", borderRadius: 5,
      padding: "13px 16px", fontFamily: MONO, fontSize: 12.5, color: "#d7d7d7",
      textAlign: "center", lineHeight: 1.9, whiteSpace: "pre-wrap",
    }}>{children}</div>
    {note && (
      <div style={{
        fontSize: 10.5, color: "#7d7d7d", fontFamily: MONO, marginTop: 5,
        textAlign: "center", lineHeight: 1.6,
      }}>{note}</div>
    )}
  </div>
);

const Code = ({ children }) => (
  <div style={{
    background: "#141414", border: "1px solid #2a2a2a", borderRadius: 4,
    padding: "10px 13px", fontFamily: MONO, fontSize: 11, color: "#9cdcfe",
    margin: "9px 0 13px", whiteSpace: "pre-wrap", lineHeight: 1.7,
    maxWidth: COL, overflowX: "auto",
  }}>{children}</div>
);

/** A stated result. The left rule marks it as load-bearing. */
const Claim = ({ kind = "Theorem", title, children }) => (
  <div style={{
    borderLeft: "2px solid #569cd6", background: "#1a1d20",
    padding: "11px 15px", margin: "13px 0", maxWidth: COL, borderRadius: "0 4px 4px 0",
  }}>
    <div style={{
      fontSize: 10.5, color: "#569cd6", fontFamily: MONO, marginBottom: 5,
      letterSpacing: 0.4, textTransform: "uppercase",
    }}>{kind}{title ? ` · ${title}` : ""}</div>
    <div style={{ fontSize: 12, color: "#c6c6c6", lineHeight: 1.8 }}>{children}</div>
  </div>
);

/** Where we were wrong. Kept visible on purpose. */
const Correction = ({ children }) => (
  <div style={{
    borderLeft: "2px solid #d19a66", background: "#201c17",
    padding: "11px 15px", margin: "13px 0", maxWidth: COL, borderRadius: "0 4px 4px 0",
  }}>
    <div style={{
      fontSize: 10.5, color: "#d19a66", fontFamily: MONO, marginBottom: 5,
      letterSpacing: 0.4, textTransform: "uppercase",
    }}>Prediction corrected by measurement</div>
    <div style={{ fontSize: 12, color: "#c6c6c6", lineHeight: 1.8 }}>{children}</div>
  </div>
);

const Table = ({ head, rows, widths }) => (
  <div style={{ margin: "12px 0 16px", maxWidth: COL, overflowX: "auto" }}>
    <table style={{
      borderCollapse: "collapse", fontSize: 11.5, fontFamily: MONO, width: "100%",
    }}>
      <thead>
        <tr>{head.map((h, i) => (
          <th key={i} style={{
            textAlign: "left", padding: "7px 12px 7px 0", color: "#8a8a8a",
            borderBottom: "1px solid #3a3a3a", fontWeight: 500,
            width: widths?.[i], whiteSpace: "nowrap",
          }}>{h}</th>
        ))}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{r.map((c, j) => (
            <td key={j} style={{
              padding: "7px 12px 7px 0", color: j === 0 ? "#d4d4d4" : "#a8a8a8",
              borderBottom: "1px solid #262626", verticalAlign: "top",
              lineHeight: 1.65,
            }}>{c}</td>
          ))}</tr>
        ))}
      </tbody>
    </table>
  </div>
);

/* ------------------------------------------------------------- verdicts */

const VERDICT = {
  CONSISTENT: "#4ec9b0",
  UNDECIDABLE: "#d19a66",
  INCONSISTENT: "#f44747",
};

const Verdict = ({ v }) => (
  <span style={{ fontFamily: MONO, color: VERDICT[v] || "#d4d4d4" }}>{v}</span>
);

/* ---------------------------------------------------------------- page */

export default function Landing({ onOpen }) {
  return (
    <div style={{
      flex: 1, overflow: "auto", height: "100%", minWidth: 0,
      padding: "34px 44px 70px",
    }}>
      {/* ---------------------------------------------------- masthead */}
      <div style={{
        fontSize: 10.5, color: "#569cd6", fontFamily: MONO, letterSpacing: 1.5,
        textTransform: "uppercase", marginBottom: 12,
      }}>
        Cause-for-Concern · Workbench
      </div>

      <H1>
        Deciding whether a metabolic network is consistent with itself,
        and saying honestly when the data cannot decide.
      </H1>

      <div style={{
        fontSize: 12.5, color: "#8e8e8e", lineHeight: 1.85, marginTop: 14,
        maxWidth: COL,
      }}>
        A language, a kernel, and a validation suite for cycle-consistency
        testing on biochemical circuits. Everything in this workbench is
        computed in your browser at the moment you ask for it: there is no
        recorded data path and no figure that was drawn in advance.
      </div>

      {/* --------------------------------------------------- abstract */}
      <H2 n="1">The problem</H2>

      <P>
        A metabolic network at steady state can be written as a resistive
        circuit. Chemical potentials are node voltages, conductances are
        branch conductances, and fluxes are branch currents:
      </P>

      <Eq note="R = 8.314 J·mol⁻¹·K⁻¹; concentrations in the same units throughout">
        {"μ = μ° + RT ln c        G = kc / RT        J = G · Δμ"}
      </Eq>

      <P>
        In this representation Kirchhoff's voltage law becomes the
        Wegscheider condition, and the sum of potential differences around
        any cycle vanishes for a thermodynamically consistent network. The
        important word is <Em>identically</Em>. The cycle sum telescopes to
        exactly zero as an algebraic identity — not approximately, not to
        within experimental error, but as a matter of arithmetic.
      </P>

      <P>
        That makes cycle sums an attractive diagnostic. A nonzero cycle sum
        witnesses inconsistency, and <Em>where</Em> it is nonzero localises
        that inconsistency to a region of the network. But any such test
        needs a tolerance ε below which a computed sum counts as zero, and
        here the standard practice fails: ε is fixed at a round number,
        typically 10⁻⁶, and treated as a property of the solver.
      </P>

      <P>
        It is not a property of the solver. It is the subject of this system.
      </P>

      {/* ------------------------------------------------------ floors */}
      <H2 n="2">Two floors, neither of them constant</H2>

      <P>
        Because the cycle sum of a consistent circuit is identically zero,
        whatever the computer returns for it is <Em>pure numerical noise</Em>.
        The scale of that noise is not a constant. Standard forward error
        analysis of a length-ℓ summation in IEEE-754 arithmetic bounds it by
        a quantity growing with both the cycle length and the largest
        absolute potential Λ on that cycle:
      </P>

      <Eq note="u = 2⁻⁵³ ≈ 1.11 × 10⁻¹⁶ for binary64">
        {"ε_num(ℓ)  ≤  γ_ℓ · Λ ,      γ_ℓ = ℓu / (1 − ℓu)"}
      </Eq>

      <P>
        A second floor has nothing to do with arithmetic. Thermodynamic data
        arrive with reported uncertainties; propagating those through the
        same cycle sum gives a scale below which a nonzero result is
        indistinguishable from the noise in the inputs:
      </P>

      <Eq note="σᵢ the reported uncertainty on each potential; z the chosen coverage factor">
        {"ε_data(ℓ)  =  z · √( Σ σᵢ² )"}
      </Eq>

      <P>
        The two floors are unrelated in origin and typically separated by
        many orders of magnitude — on the reference circuit, about eleven.
        The <Em>cycle-local tolerance</Em> is their maximum, computed per
        cycle rather than fixed for the network:
      </P>

      <Eq>{"ε*(ℓ)  =  max{ ε_num(ℓ),  ε_data(ℓ) }"}</Eq>

      <Claim kind="Theorem" title="No false positives">
        A test thresholded at ε* has a numerical false-positive rate bounded
        by the arithmetic alone.
      </Claim>

      <Claim kind="Theorem" title="Detection">
        The same test detects every perturbation exceeding 2ε*.
      </Claim>

      <P>
        The two bounds are complementary, and neither is available under a
        fixed tolerance. That is the whole argument for cycle-local ε*.
      </P>

      {/* ------------------------------------------------ trichotomy */}
      <H2 n="3">Why the verdict must be three-valued</H2>

      <P>
        Once there are two floors, a cycle sum can land between them. It is
        then too large to be rounding error and too small to be
        distinguished from the uncertainty in the data. Neither
        "consistent" nor "inconsistent" is a defensible report:
      </P>

      <Table
        head={["Verdict", "Condition", "What it licenses"]}
        widths={["18%", "26%", "56%"]}
        rows={[
          [<Verdict v="CONSISTENT" />, "|H| ≤ ε_num",
            "The sum is at the arithmetic floor. Consistent as far as the computation can tell."],
          [<Verdict v="UNDECIDABLE" />, "ε_num < |H| ≤ ε_data",
            "Above rounding, inside the data's own uncertainty. No claim in either direction is warranted from the data supplied."],
          [<Verdict v="INCONSISTENT" />, "|H| > ε*",
            "Above both floors. The network fails its own consistency condition on this cycle."],
        ]}
      />

      <P>
        The third value is not a hedge and not an implementation
        convenience. It is the honest report of a measurement that did not
        resolve the question, and the language makes it unavoidable: a
        species declared without a <K>sigma</K> yields an <Em>undefined</Em>{" "}
        data floor rather than a default, so every cycle above the numerical
        floor comes back <Verdict v="UNDECIDABLE" />. You cannot get a
        confident answer by omitting the uncertainty.
      </P>

      {/* -------------------------------------------------- basis ---- */}
      <H2 n="4">What survives a change of basis</H2>

      <P>
        Cycle sums are computed against a cycle basis, and cycle bases are
        not unique. A network with ν = m − n + c independent cycles admits
        many. If the answer depended on which one we picked, the whole
        localisation claim would be an artefact.
      </P>

      <Claim kind="Theorem" title="Verdict is basis-independent">
        A network is consistent or it is not, whatever cycle basis is chosen.
      </Claim>

      <Claim kind="Proposition" title="Localisation is not">
        The set of <Em>flagged</Em> cycles depends on the basis. A single
        defect can be made to appear in one cycle or spread across several
        by choosing differently.
      </Claim>

      <P>
        What survives is the <Em>witness set</Em>: the edges lying on every
        flagged cycle of a minimum cycle basis. It is basis-independent, and
        it contains the perturbed edge whenever detection succeeds. In the
        charts it is drawn in red on the circuit graph — that is the actual
        localisation, and the flagged cycle list is not.
      </P>

      {/* ------------------------------------------- edges not nodes -- */}
      <H2 n="5">Defects live on edges, not nodes</H2>

      <P>
        This is worth stating separately because it cost us an experiment.
        Shifting a node potential leaves the edge data a gradient — of the
        shifted potential — so every cycle sum stays exactly zero and
        nothing is detected. That is not a failure of the method; it is the
        method working correctly on data that is still consistent.
      </P>

      <P>
        Only an edge offset makes the data fail to <Em>be</Em> a gradient,
        which is what inconsistency means. The example{" "}
        <FileLink name="05_node_vs_edge.cfc" onOpen={onOpen} /> runs both
        perturbations side by side and asserts that node perturbation
        <Em> cannot</Em> produce inconsistency. It is a negative control,
        and it is in the suite because we initially got this wrong.
      </P>

      {/* ------------------------------------------------- measured --- */}
      <H2 n="6">What was measured</H2>

      <P>
        Five sweeps, reproduced live in the <Em>Validation lab</Em>. Each
        builds, solves and classifies hundreds of circuits in tens of
        milliseconds. The seed is exposed: change it, re-run, and the points
        move — because these are measurements rather than illustrations.
      </P>

      <Table
        head={["Sweep", "Question", "Result"]}
        widths={["23%", "39%", "38%"]}
        rows={[
          ["V1 · Noise scale", "Does ε_num bound the observed error?",
            "0 violations; median slack ≈ 730×"],
          ["V2 · Fixed tolerance", "What does a fixed ε = 10⁻⁶ cost?",
            "FP 0.00 in binary64; up to 0.84 in binary32"],
          ["V3 · Trichotomy", "How often is the third value needed?",
            "≈ 81% undecidable; ≈ 11.5-order floor gap"],
          ["V4 · Basis dependence", "Does the basis change the answer?",
            "0 verdict disagreements; ≈ 35% flagged-set variation"],
          ["V5 · Detection", "Is the 2ε* guarantee met?",
            "0 violations; ratio ≈ 0.51–0.71"],
        ]}
      />

      <Correction>
        We predicted that a fixed ε = 10⁻⁶ would fail <Em>two-sidedly</Em>,
        both missing real defects and manufacturing false positives. V2
        falsified the second half. In binary64 the rounding error tops out
        near 3 × 10⁻¹² even at ℓ = 30, Λ = 3000 — six orders of magnitude
        below the fixed tolerance — so it manufactures no false positives at
        all, and the measured rate was 0.000 across 1600 trials. Its real
        costs are different: it misses <Em>every</Em> defect below itself,
        and it asserts <Verdict v="INCONSISTENT" /> on cycles whose defect
        lies inside the data's own uncertainty, where no positive claim is
        warranted. The predicted two-sided failure does appear, and rises
        with ℓΛ as the theory requires, once precision falls: the same null
        in binary32 gives false-positive rates from 0.18 to 0.77. We
        corrected the claim rather than the experiment, and the manuscript
        records both.
      </Correction>

      {/* ------------------------------------------------- language --- */}
      <H2 n="7">The language enforces the epistemics</H2>

      <P>
        The constraints above are not conventions to be respected by careful
        users. They are properties of the grammar and the kernel, and a
        program that violates them does not run.
      </P>

      <H3>A verdict cannot exist without its tolerance</H3>
      <P>
        <K>admit H tolerance T</K> is the only production in the language
        that yields a <K>Verdict</K>, and both operands are mandatory. There
        is no derivation for a bare verdict.{" "}
        <FileLink name="04_rejected.cfc" onOpen={onOpen} /> attempts the
        omission and fails to parse — delete the <K>tolerance t</K> clause
        anywhere and watch it refuse.
      </P>

      <H3>A tolerance cannot be conjured</H3>
      <P>
        <K>tolerance of L with S</K> requires the <K>with</K> clause naming
        the species whose uncertainties are propagated. There is no default
        σ, because a default would be a fabricated measurement.
      </P>

      <H3>INVALID is not NEGATIVE</H3>
      <P>
        If the reference network fails its own consistency check, the fault
        is in the data and no diagnostic conclusion is licensed. The run
        halts with <span style={{ fontFamily: MONO, color: "#f44747" }}>INVALID</span>{" "}
        before any diagnostic claim is evaluated. A failed assertion against
        a <Em>valid</Em> reference is different: that is{" "}
        <span style={{ fontFamily: MONO, color: "#d19a66" }}>NEGATIVE</span>,
        a real result about the test. Conflating the two is how a broken
        instrument becomes a discovery.
      </P>

      <Code>{`circuit Reference {
  species G6P : mu0 : -1760.0, concentration : 0.5, sigma : 2.4
  reaction PFK : G6P -> FBP, k : 0.05
  solve yield C
}

basis of C yield B

foreach loop in B {
  holonomy  of loop in C          yield h
  tolerance of loop with Reference yield t
  admit h tolerance t              yield v
}`}</Code>

      {/* ---------------------------------------------------- scope --- */}
      <H2 n="8">Scope, and what this is not</H2>

      <P>
        This workbench implements the tolerance and verdict fragment of the
        Cause-for-Concern language. It is a reference implementation for the
        claims above, not the complete system described in the
        specification.
      </P>

      <Table
        head={["", "Status"]}
        widths={["44%", "56%"]}
        rows={[
          ["Circuit construction, solve, cycle basis", "Implemented"],
          ["Both floors, ε*, three-valued verdict", "Implemented"],
          ["Witness set, validity gate", "Implemented"],
          [<span><K>measure</K>, <K>localize</K>, <K>close</K></span>,
            "Lexed but not implemented"],
          ["Gap-closure machinery", "Not implemented"],
          ["Separate typechecker", "Guarantees enforced syntactically and at runtime instead"],
          ["Nonlinear solver", "Circuits are solved by direct evaluation"],
          [<span><K>import</K> of external data</span>,
            "Yields symbolic markers; every number that can change a verdict must appear in the program text"],
        ]}
      />

      <P>
        The kernel is a port of the Python reference implementation, not a
        reimplementation of its ideas. The two agree to machine precision:
        on the reference circuit both produce ε_num = 4.2486 × 10⁻¹²,
        ε_data = 11.336576, witness set {"{"}<K>SHNT</K>{"}"}. That agreement
        is what makes the browser a second implementation rather than a
        demonstration.
      </P>

      {/* ----------------------------------------------------- start -- */}
      <H2 n="9">Where to start</H2>

      <Table
        head={["Example", "Verdict", "Shows"]}
        widths={["27%", "13%", "60%"]}
        rows={[
          [<FileLink name="01_validity_gate.cfc" onOpen={onOpen} />, "OK",
            <span>The full protocol, gate first. Witness set {"{"}<K>SHNT</K>{"}"}.</span>],
          [<FileLink name="02_undecidable.cfc" onOpen={onOpen} />, "OK",
            "One defect, two data qualities, two different verdicts."],
          [<FileLink name="03_invalid_reference.cfc" onOpen={onOpen} />, "INVALID",
            "The gate halting before any diagnostic claim is evaluated."],
          [<FileLink name="04_rejected.cfc" onOpen={onOpen} />, "ERROR",
            "A verdict without a tolerance has no derivation in the grammar."],
          [<FileLink name="05_node_vs_edge.cfc" onOpen={onOpen} />, "OK",
            "The negative control: node perturbation detects nothing; edge does."],
        ]}
      />

      <div style={{ display: "flex", gap: 10, marginTop: 22, maxWidth: COL }}>
        <button
          onClick={() => onOpen?.("01_validity_gate.cfc")}
          data-testid="landing-start"
          style={{
            background: "#2d6b3f", border: "none", color: "#fff",
            padding: "9px 16px", borderRadius: 4, cursor: "pointer",
            fontSize: 12, fontFamily: MONO,
          }}>
          Open the first experiment →
        </button>
      </div>

      <div style={{
        marginTop: 40, paddingTop: 18, borderTop: "1px solid #2a2a2a",
        fontSize: 11, color: "#6f6f6f", lineHeight: 1.8, maxWidth: COL,
      }}>
        The theory, the proofs, the error analysis and the full validation
        protocol are given in <Em>Cycle-local tolerance for the Kirchhoff
        consistency test on biochemical circuits</Em>, of which this
        workbench is the executable companion.
      </div>
    </div>
  );
}

/** A filename that opens that file in the editor. */
function FileLink({ name, onOpen }) {
  return (
    <span
      onClick={() => onOpen?.(name)}
      style={{
        fontFamily: MONO, color: "#569cd6", cursor: "pointer",
        borderBottom: "1px dotted #3d5a72",
      }}
      title={`Open ${name}`}
    >{name}</span>
  );
}

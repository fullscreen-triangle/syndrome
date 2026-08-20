/**
 * SweepLab.jsx -- run the paper's validation experiments live.
 *
 * Each sweep builds, solves and classifies hundreds of circuits with
 * the same kernel the editor uses, then reports what it measured. The
 * seed is exposed: change it and the points move, because these are
 * measurements rather than illustrations.
 */

import React, { useCallback, useState } from "react";
import { SWEEPS } from "../cfc/sweeps.js";
import { SweepCharts } from "./sweepCharts.jsx";

const MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";
const TEAL = "#4ec9b0";
const RED = "#f44747";
const ORANGE = "#d19a66";

/** What each sweep establishes, stated so a pass/fail is meaningful. */
function summarise(r) {
  switch (r.kind) {
    case "noise":
      return [
        ["bound violations", `${r.violations} / ${r.trials}`, r.violations === 0],
        ["median slack", `${r.medianSlack.toFixed(0)}×`, null],
        ["largest error", r.maxObserved.toExponential(2) + " kJ/mol", null],
        ["vs ε = 1e-6", `${Math.log10(1e-6 / r.maxObserved).toFixed(1)} orders below`, null],
      ];
    case "fixed": {
      const fp64 = Math.max(...r.strata.map((s) => s.fp64));
      const fp32 = Math.max(...r.strata.map((s) => s.fp32));
      const unw = Math.max(...r.strata.map((s) => s.unwarranted));
      const miss = Math.max(...r.strata.map((s) => s.missByDefect[1e-7]));
      return [
        ["false positives, binary64", fp64.toFixed(3), fp64 === 0],
        ["false positives, binary32", fp32.toFixed(3), null],
        ["missed at D = 1e-7", miss.toFixed(3), null],
        ["unwarranted positives", unw.toFixed(3), null],
      ];
    }
    case "trichotomy":
      return [
        ["undecidable", (r.fractions.UNDECIDABLE * 100).toFixed(1) + "%",
          r.fractions.UNDECIDABLE > 0],
        ["inconsistent", (r.fractions.INCONSISTENT * 100).toFixed(1) + "%", null],
        ["floor separation", r.gapOrders.toFixed(1) + " orders", null],
        ["ε_num", r.epsNum.toExponential(2) + " kJ/mol", null],
      ];
    case "basis":
      return [
        ["verdict disagreements", `${r.verdictDisagree} / ${r.trials}`,
          r.verdictDisagree === 0],
        ["flagged-set disagreement", (r.flaggedDisagreeRate * 100).toFixed(1) + "%", null],
        ["witness contains defect", (r.witnessHitMcb * 100).toFixed(0) + "%",
          r.witnessHitMcb === 1],
        ["mean |W|", `${r.meanWitnessMcb?.toFixed(2)} min · ${r.meanWitnessFcb?.toFixed(2)} fund`, null],
      ];
    case "detection":
      return [
        ["guarantee violations", `${r.violations} / ${r.evaluations}`, r.violations === 0],
        ["empirical / guaranteed", `${r.minRatio.toFixed(2)}–${r.maxRatio.toFixed(2)}`, null],
        ["ε* range", `${r.curves[0].epsStar.toExponential(1)} … ${r.curves[r.curves.length - 1].epsStar.toExponential(1)}`, null],
        ["data qualities", `${r.curves.length} σ values`, null],
      ];
    default:
      return [];
  }
}

/** The reading -- what the numbers mean, including where they surprise. */
const READING = {
  noise: "The error grows with both L and Λ, over three decades — so no " +
    "constant tracks it. But its largest value is orders below a customary " +
    "ε = 1e-6, which is why a fixed tolerance produces no false positives " +
    "in double precision. That falsified our first prediction.",
  fixed: "In binary64 the false-positive rate is exactly zero: the threshold " +
    "sits far above the noise. Its real costs are missing every defect below " +
    "itself, and asserting INCONSISTENT on defects lying inside the data's " +
    "own uncertainty. The two-sided failure appears only at lower precision.",
  trichotomy: "The band between the two floors is most of the plane. A " +
    "two-valued test would return a confident verdict on every point in it, " +
    "and would be wrong to.",
  basis: "The network-level verdict never disagrees between bases; the " +
    "flagged set disagrees in about a third of trials. So 'the defect is in " +
    "loop ℓ' is not basis-independent, while the witness set is.",
  detection: "Every defect above 2ε* is detected, and the empirical " +
    "threshold sits at about half that — the factor of two is the price of a " +
    "two-sided guarantee, and is rarely paid.",
};

export default function SweepLab({ width }) {
  const [active, setActive] = useState("noise");
  const [seed, setSeed] = useState(20260819);
  const [results, setResults] = useState({});
  const [busy, setBusy] = useState(false);
  const [timing, setTiming] = useState({});

  const run = useCallback((id) => {
    setBusy(true);
    setTimeout(() => {
      const t0 = performance.now();
      const r = SWEEPS[id].run({ seed });
      const ms = performance.now() - t0;
      setResults((p) => ({ ...p, [id]: r }));
      setTiming((p) => ({ ...p, [id]: ms }));
      setBusy(false);
    }, 20);
  }, [seed]);

  const runAll = useCallback(() => {
    setBusy(true);
    setTimeout(() => {
      const out = {}, t = {};
      for (const id of Object.keys(SWEEPS)) {
        const t0 = performance.now();
        out[id] = SWEEPS[id].run({ seed });
        t[id] = performance.now() - t0;
      }
      setResults(out);
      setTiming(t);
      setBusy(false);
    }, 20);
  }, [seed]);

  const spec = SWEEPS[active];
  const res = results[active];

  return (
    <div style={{ display: "flex", height: "100%", minHeight: 0 }}>
      {/* sweep list */}
      <div style={{
        width: 232, borderRight: "1px solid #2a2a2a", overflow: "auto",
        flexShrink: 0, background: "#1c1c1c",
      }}>
        <div style={{
          padding: "10px 12px 6px", fontSize: 10.5, letterSpacing: 1.1,
          textTransform: "uppercase", color: "#888",
        }}>Validation sweeps</div>

        {Object.values(SWEEPS).map((s) => {
          const done = results[s.id];
          return (
            <div key={s.id} onClick={() => setActive(s.id)}
              style={{
                padding: "8px 12px", cursor: "pointer", fontSize: 11.5,
                fontFamily: MONO, borderLeft: active === s.id
                  ? "2px solid #569cd6" : "2px solid transparent",
                background: active === s.id ? "#252526" : "transparent",
                color: active === s.id ? "#fff" : "#bbb",
              }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{
                  color: done ? TEAL : "#555", fontSize: 9,
                }}>{done ? "●" : "○"}</span>
                <span>{s.label}</span>
              </div>
              <div style={{ color: "#6e6e6e", fontSize: 9.5, marginTop: 3, paddingLeft: 15 }}>
                {timing[s.id] ? `${timing[s.id].toFixed(0)} ms` : s.cost}
              </div>
            </div>
          );
        })}

        <div style={{ padding: "12px", borderTop: "1px solid #2a2a2a", marginTop: 8 }}>
          <label style={{ fontSize: 10, color: "#888", fontFamily: MONO }}>seed</label>
          <input type="number" value={seed}
            onChange={(e) => setSeed(Number(e.target.value) || 1)}
            style={{
              width: "100%", marginTop: 4, background: "#111", color: "#d4d4d4",
              border: "1px solid #333", borderRadius: 3, padding: "4px 6px",
              fontFamily: MONO, fontSize: 11,
            }} />
          <button onClick={runAll} disabled={busy}
            style={{
              width: "100%", marginTop: 8, background: busy ? "#333" : "#2d4a6b",
              color: "#fff", border: "none", borderRadius: 3, padding: "6px",
              cursor: busy ? "wait" : "pointer", fontSize: 11, fontFamily: MONO,
            }}>
            {busy ? "running…" : "Run all sweeps"}
          </button>
          <div style={{
            marginTop: 10, fontSize: 9.5, color: "#6e6e6e", lineHeight: 1.6,
          }}>
            Each sweep runs the real kernel. Change the seed and re-run:
            the points move, because they are measurements.
          </div>
        </div>
      </div>

      {/* detail */}
      <div style={{ flex: 1, overflow: "auto", minWidth: 0 }}>
        <div style={{
          padding: "12px 16px", borderBottom: "1px solid #2a2a2a",
          display: "flex", alignItems: "flex-start", gap: 16,
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, color: "#fff", fontFamily: MONO }}>
              {spec.label}
            </div>
            <div style={{
              fontSize: 11, color: "#9a9a9a", marginTop: 4, lineHeight: 1.6,
              maxWidth: 620,
            }}>
              {spec.blurb}
            </div>
          </div>
          <button onClick={() => run(active)} disabled={busy}
            style={{
              background: busy ? "#333" : "#2d6b3f", color: "#fff", border: "none",
              borderRadius: 3, padding: "6px 14px", cursor: busy ? "wait" : "pointer",
              fontSize: 11.5, fontFamily: MONO, flexShrink: 0,
            }}>
            {busy ? "running…" : res ? "Re-run" : "Run sweep"}
          </button>
        </div>

        {!res ? (
          <div style={{
            padding: 28, color: "#6f6f6f", fontFamily: MONO, fontSize: 12,
            lineHeight: 1.8,
          }}>
            Not run yet. {spec.cost} — typically under 100 ms.
          </div>
        ) : (
          <>
            <div style={{
              display: "flex", flexWrap: "wrap", gap: 10, padding: "12px 16px",
            }}>
              {summarise(res).map(([k, v, ok]) => (
                <div key={k} style={{
                  minWidth: 150, background: "#202020",
                  border: "1px solid #2d2d2d", borderRadius: 5, padding: "8px 11px",
                }}>
                  <div style={{ fontSize: 9.5, color: "#8a8a8a", fontFamily: MONO }}>
                    {k}
                  </div>
                  <div style={{
                    fontSize: 15, marginTop: 3, fontFamily: MONO,
                    color: ok === true ? TEAL : ok === false ? RED : "#e4e4e4",
                  }}>
                    {v}
                  </div>
                </div>
              ))}
            </div>

            <div style={{
              margin: "2px 16px 12px", padding: "10px 13px", background: "#1a1f24",
              borderLeft: `2px solid ${ORANGE}`, borderRadius: 3,
              fontSize: 11, color: "#b6b6b6", lineHeight: 1.7, maxWidth: 900,
            }}>
              {READING[res.kind]}
            </div>

            <div style={{
              display: "flex", flexWrap: "wrap", gap: 12, padding: "0 16px 18px",
            }}>
              <SweepCharts result={res} width={width} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

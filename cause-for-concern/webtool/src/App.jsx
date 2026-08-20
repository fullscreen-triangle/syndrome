/**
 * App.jsx -- the CFC workbench shell.
 *
 * Three views behind an activity bar:
 *   Editor  -- write and run .cfc programs against the real kernel
 *   Lab     -- the paper's validation sweeps, run live
 *   Docs    -- the language reference
 *
 * Nothing here is mocked: every number shown was computed by the
 * interpreter or the sweep engine moments before it was drawn.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Editor from "./components/Editor.jsx";
import Landing from "./components/Landing.jsx";
import Reference from "./components/Reference.jsx";
import SweepLab from "./components/SweepLab.jsx";
import ChartColumn from "./components/ChartColumn.jsx";
import { VERDICT_COLOR } from "./components/charts.jsx";
import {
  BookIcon, ChevronIcon, FileGlyph, FilesIcon, InfoIcon, LabIcon, RunIcon,
} from "./components/icons.jsx";
import { runSource } from "./cfc/interpreter.js";
import { EXAMPLES, DEFAULT_FILE } from "./data/examples.js";

const MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";
const STORE = "cfc-workbench-files-v1";

const STATUS = {
  OK: { color: "#4ec9b0", note: "every assertion held" },
  NEGATIVE: { color: "#d19a66", note: "an assertion failed or declined — a real result" },
  INVALID: { color: "#f44747", note: "a reference check failed — no conclusion licensed" },
  ERROR: { color: "#f44747", note: "the program could not be run" },
};

const fmt = (x) => {
  if (x === null || x === undefined) return "—";
  if (typeof x !== "number") return String(x);
  if (x === 0) return "0";
  const a = Math.abs(x);
  return a < 1e-3 || a >= 1e5 ? x.toExponential(3) : x.toFixed(4);
};

export default function App() {
  const [view, setView] = useState("landing");
  const [files, setFiles] = useState(() => {
    try {
      const saved = localStorage.getItem(STORE);
      if (saved) return { ...EXAMPLES, ...JSON.parse(saved) };
    } catch { /* fall through to pristine examples */ }
    return { ...EXAMPLES };
  });
  const [active, setActive] = useState(DEFAULT_FILE);
  const [open, setOpen] = useState([DEFAULT_FILE]);
  const [record, setRecord] = useState(null);
  const [tab, setTab] = useState("charts");
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState([]);
  const [outW, setOutW] = useState(() => {
    const saved = Number(localStorage.getItem("cfc-out-width"));
    return saved >= 320 ? saved : 520;
  });
  const [expOpen, setExpOpen] = useState(true);
  const [autoRun, setAutoRun] = useState(false);
  const dragRef = useRef(null);
  const codeRef = useRef("");

  const code = files[active] ?? "";
  codeRef.current = code;

  useEffect(() => {
    const t = setTimeout(() => {
      try {
        const diff = {};
        for (const [k, v] of Object.entries(files)) {
          if (EXAMPLES[k] !== v) diff[k] = v;
        }
        localStorage.setItem(STORE, JSON.stringify(diff));
      } catch { /* storage unavailable; edits stay in memory */ }
    }, 400);
    return () => clearTimeout(t);
  }, [files]);

  useEffect(() => {
    try { localStorage.setItem("cfc-out-width", String(outW)); } catch { /* ignore */ }
  }, [outW]);

  const setCode = useCallback((v) => {
    setFiles((f) => ({ ...f, [active]: v }));
  }, [active]);

  const dirty = files[active] !== EXAMPLES[active];

  const openFile = (n) => {
    setActive(n);
    setOpen((o) => (o.includes(n) ? o : [...o, n]));
    setView("editor");
  };

  const closeTab = (n, e) => {
    e.stopPropagation();
    const next = open.filter((f) => f !== n);
    setOpen(next);
    if (active === n) setActive(next[0] ?? "");
  };

  const revert = () => setFiles((f) => ({ ...f, [active]: EXAMPLES[active] }));

  const run = useCallback((src = codeRef.current, name = active) => {
    if (!name) return;
    setRunning(true);
    setTimeout(() => {
      const t0 = performance.now();
      const rec = runSource(src, name);
      const ms = performance.now() - t0;

      const L = [];
      const p = (s = "") => L.push(s);
      p(`$ cfc run ${name}`);
      p();

      if (rec.status === "ERROR") {
        p("  the program did not compile");
        p(`  ${rec.error}`);
        p();
        p("  Nothing was computed, so there is nothing to plot.");
      } else {
        for (const [nm, c] of Object.entries(rec.circuits)) {
          p(`  circuit ${nm}: ${c.species} species, ${c.reactions} reactions, ν = ${c.cyclomaticNumber}`);
          p(`    max |node balance| = ${fmt(c.maxAbsNodeBalance)}`);
          if (c.centred) p(`    gauge-centred, offset = ${fmt(c.gaugeOffset)}`);
        }
        if (rec.cycles.length) {
          p(`  cycle basis: ${rec.cycles.length} cycles, lengths ${rec.cycles.map((c) => c.length).join(", ")}`);
        }
        if (rec.tolerances.length) {
          p();
          p("  per-cycle tolerances");
          for (const t of rec.tolerances.slice(0, 14)) {
            p(`    ${t.loop.padEnd(12)} ε_num=${fmt(t.numerical)}  ε_data=${t.dataAvailable ? fmt(t.data) : "undefined"}  ε*=${fmt(t.star)}`);
          }
          if (rec.tolerances.length > 14) p(`    … ${rec.tolerances.length - 14} more`);
        }
        if (rec.verdicts.length) {
          const tally = {};
          for (const v of rec.verdicts) tally[v.verdict] = (tally[v.verdict] || 0) + 1;
          p();
          p("  verdicts: " + Object.entries(tally).map(([k, n]) => `${k}=${n}`).join("  "));
        }
        if (rec.witnessSet) {
          p(`  witness set: {${rec.witnessSet.join(", ")}}   |W| = ${rec.witnessSet.length}`);
        }
        if (rec.emissions.length) {
          p();
          for (const e of rec.emissions) p(`  emit L${e.line}: ${e.message}`);
        }
        p();
        p(`  committed measurements: m = ${rec.committedMeasurements}`);
        p(`  status: ${rec.status} — ${STATUS[rec.status].note}`);
        if (rec.error) p(`  ${rec.error}`);
      }
      p();
      p(`  finished in ${ms.toFixed(1)} ms`);

      setLog(L);
      setRecord(rec);
      setRunning(false);
      setTab(rec.status === "ERROR" ? "terminal" : "charts");
    }, 15);
  }, [active]);

  // Ctrl/Cmd+Enter runs; auto-run debounces on edit.
  useEffect(() => {
    const h = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        setView("editor");
        run();
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [run]);

  useEffect(() => {
    if (!autoRun || view !== "editor") return;
    const t = setTimeout(() => run(), 700);
    return () => clearTimeout(t);
  }, [code, autoRun, view, run]);

  // The output column is dragged from its left edge, so widening it
  // means moving left: the delta is subtracted.
  const onDragStart = (e) => {
    e.preventDefault();
    dragRef.current = { x: e.clientX, w: outW };
    const move = (ev) => {
      const d = dragRef.current;
      if (!d) return;
      const max = Math.max(360, window.innerWidth - 620);
      setOutW(Math.max(320, Math.min(max, d.w - (ev.clientX - d.x))));
    };
    const up = () => {
      dragRef.current = null;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
    };
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  const errorLine = useMemo(() => {
    if (!record?.error) return null;
    if (record.errorLine) return record.errorLine;
    const m = /line (\d+)/.exec(record.error);
    return m ? parseInt(m[1], 10) : null;
  }, [record]);

  const download = () => {
    if (!record) return;
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = active.replace(/\.cfc$/, "") + ".json";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const firstCircuit = record && Object.values(record.circuits)[0];

  return (
    <div style={{
      display: "flex", flexDirection: "column", height: "100vh",
      background: "#1e1e1e", color: "#d4d4d4",
      font: "13px 'Segoe UI', system-ui, sans-serif", overflow: "hidden",
    }}>
      {/* title bar */}
      <div style={{
        height: 36, background: "#323233", display: "flex", alignItems: "center",
        padding: "0 12px", gap: 10, borderBottom: "1px solid #252526", flexShrink: 0,
      }}>
        <span style={{ color: "#569cd6", fontWeight: 700, fontFamily: MONO, letterSpacing: 1 }}>
          CFC
        </span>
        <span style={{ opacity: 0.3 }}>│</span>
        <span style={{ fontSize: 12, color: "#bbb" }}>
          Cause-for-Concern workbench
        </span>
        <div style={{ flex: 1 }} />

        {view === "editor" && (
          <>
            <label style={{
              display: "flex", alignItems: "center", gap: 5, fontSize: 10.5,
              color: "#9a9a9a", fontFamily: MONO, cursor: "pointer",
            }}>
              <input type="checkbox" checked={autoRun}
                onChange={(e) => setAutoRun(e.target.checked)}
                style={{ accentColor: "#569cd6", cursor: "pointer" }} />
              auto-run
            </label>
            {/* Status lives in the output column's strip; repeating it
                here would be two places to read the same fact. */}
            {record && (
              <button onClick={download} style={btn("#3a3d41")}>Export JSON</button>
            )}
            <button onClick={() => run()} disabled={running || !active}
              title="Run program" data-testid="run"
              style={btn(running ? "#3a3a3a" : "#2d6b3f", running ? "wait" : "pointer")}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <RunIcon /> {running ? "Running…" : "Run"}
                <span style={{ opacity: 0.55, fontSize: 10 }}>⌃⏎</span>
              </span>
            </button>
          </>
        )}
      </div>

      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* activity bar */}
        <div style={{
          width: 46, background: "#333", display: "flex", flexDirection: "column",
          alignItems: "center", paddingTop: 6, gap: 2, flexShrink: 0,
          borderRight: "1px solid #252526",
        }}>
          {[["landing", InfoIcon, "What this is"],
            ["editor", FilesIcon, "Experiments"],
            ["lab", LabIcon, "Validation lab"],
            ["docs", BookIcon, "Reference"]].map(([id, Icon, tip]) => (
            <button key={id} onClick={() => setView(id)} title={tip}
              style={{
                width: 42, height: 42, background: "transparent", border: "none",
                borderLeft: view === id ? "2px solid #569cd6" : "2px solid transparent",
                cursor: "pointer", display: "flex", alignItems: "center",
                justifyContent: "center",
              }}>
              <Icon c={view === id ? "#fff" : "#8a8a8a"} />
            </button>
          ))}
        </div>

        {view === "landing" && <Landing onOpen={openFile} />}
        {view === "lab" && <SweepLab />}
        {view === "docs" && <Reference />}

        {view === "editor" && (
          <>
            {/* explorer */}
            <div style={{
              width: 238, background: "#252526", borderRight: "1px solid #1a1a1a",
              overflow: "auto", flexShrink: 0,
            }}>
              <div onClick={() => setExpOpen(!expOpen)}
                style={{
                  padding: "9px 10px", fontSize: 10.5, letterSpacing: 1.1,
                  textTransform: "uppercase", color: "#888", cursor: "pointer",
                  display: "flex", alignItems: "center", gap: 5,
                }}>
                <ChevronIcon open={expOpen} /> Experiments
              </div>
              {expOpen && Object.keys(files).map((f) => (
                <div key={f} onClick={() => openFile(f)} title={f}
                  style={{
                    padding: "5px 10px 5px 20px", cursor: "pointer", fontSize: 11.5,
                    background: active === f ? "#37373d" : "transparent",
                    color: active === f ? "#fff" : "#c2c2c2",
                    borderLeft: active === f ? "2px solid #569cd6" : "2px solid transparent",
                    fontFamily: MONO, display: "flex", alignItems: "center", gap: 7,
                    whiteSpace: "nowrap", overflow: "hidden",
                  }}>
                  <FileGlyph c={active === f ? "#9cdcfe" : "#6e6e6e"} />
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{f}</span>
                  {files[f] !== EXAMPLES[f] && (
                    <span style={{ color: "#d19a66", fontSize: 13, marginLeft: "auto" }}>•</span>
                  )}
                </div>
              ))}

              <div style={{
                margin: "16px 12px", paddingTop: 12, borderTop: "1px solid #333",
                fontSize: 10.5, color: "#7a7a7a", lineHeight: 1.75,
              }}>
                <div style={{ color: "#9a9a9a", marginBottom: 7, fontWeight: 600 }}>
                  Enforced guarantees
                </div>
                <div>A verdict cannot exist without its tolerance.</div>
                <div style={{ marginTop: 6 }}>A tolerance needs a named uncertainty source.</div>
                <div style={{ marginTop: 6 }}>Verdicts are three-valued.</div>
                <div style={{ marginTop: 6 }}>INVALID ≠ NEGATIVE.</div>
                <div style={{ marginTop: 10, color: "#5f5f5f" }}>
                  Try deleting a <span style={{ fontFamily: MONO }}>tolerance</span> clause —
                  it will not parse.
                </div>
              </div>
            </div>

            {/* main column */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
              <div style={{
                height: 34, background: "#252526", display: "flex",
                borderBottom: "1px solid #1a1a1a", overflowX: "auto", flexShrink: 0,
              }}>
                {open.map((f) => (
                  <div key={f} onClick={() => setActive(f)}
                    style={{
                      display: "flex", alignItems: "center", gap: 7, padding: "0 11px",
                      cursor: "pointer", fontSize: 11.5, fontFamily: MONO,
                      background: active === f ? "#1e1e1e" : "#2d2d2d",
                      color: active === f ? "#fff" : "#8a8a8a",
                      borderRight: "1px solid #252526", whiteSpace: "nowrap",
                    }}>
                    {files[f] !== EXAMPLES[f] && (
                      <span style={{ color: "#d19a66", fontSize: 12 }}>●</span>
                    )}
                    {f}
                    <span onClick={(e) => closeTab(f, e)}
                      style={{ opacity: 0.5, fontSize: 14, lineHeight: 1 }}>×</span>
                  </div>
                ))}
                <div style={{ flex: 1 }} />
                {dirty && (
                  <button onClick={revert} style={{
                    background: "transparent", border: "none", color: "#8a8a8a",
                    fontSize: 10.5, fontFamily: MONO, cursor: "pointer", padding: "0 12px",
                  }}>revert</button>
                )}
              </div>

              <Editor value={code} onChange={setCode} errorLine={errorLine} />
            </div>

            {/* splitter */}
            <div onMouseDown={onDragStart} onDoubleClick={() => setOutW(520)}
              title="Drag to resize · double-click to reset"
              style={{
                width: 5, background: "#2a2a2a", cursor: "col-resize",
                flexShrink: 0, borderLeft: "1px solid #1a1a1a",
              }} />

            {/* output column */}
            <div style={{
              width: outW, background: "#181818", display: "flex",
              flexDirection: "column", flexShrink: 0, minWidth: 0,
            }}>
              <div style={{
                height: 34, display: "flex", alignItems: "stretch",
                borderBottom: "1px solid #2a2a2a", flexShrink: 0,
                overflowX: "auto",
              }}>
                {[["charts", "Charts"], ["terminal", "Terminal"],
                  ["inspect", "Inspector"], ["json", "Record"]].map(([id, lbl]) => (
                  <button key={id} onClick={() => setTab(id)} style={{
                    background: tab === id ? "#181818" : "transparent", border: "none",
                    borderBottom: tab === id ? "2px solid #569cd6" : "2px solid transparent",
                    color: tab === id ? "#fff" : "#888", padding: "0 13px",
                    cursor: "pointer", fontSize: 11.5, fontFamily: MONO,
                    whiteSpace: "nowrap",
                  }}>{lbl}</button>
                ))}
              </div>

              {record && (
                <div style={{
                  display: "flex", alignItems: "center", gap: 11, flexWrap: "wrap",
                  padding: "6px 13px", borderBottom: "1px solid #242424",
                  fontSize: 10, fontFamily: MONO, flexShrink: 0,
                }}>
                  <span style={{ color: STATUS[record.status].color }}>
                    ● {record.status}
                  </span>
                  <span style={{ color: "#666" }}>m = {record.committedMeasurements}</span>
                  {record.status !== "ERROR" && (
                    <>
                      <span style={{ color: "#3a3a3a" }}>│</span>
                      {["CONSISTENT", "UNDECIDABLE", "INCONSISTENT"].map((k) => {
                        const n = record.verdicts.filter((v) => v.verdict === k).length;
                        return (
                          <span key={k} style={{ color: n ? VERDICT_COLOR[k] : "#4a4a4a" }}>
                            ■ {k.toLowerCase()}{n > 0 ? ` ${n}` : ""}
                          </span>
                        );
                      })}
                    </>
                  )}
                </div>
              )}

              <div style={{ flex: 1, overflow: "auto", minHeight: 0 }}>
                {tab === "charts" && <ChartColumn record={record} circuit={firstCircuit} />}
                {tab === "terminal" && <Terminal log={log} />}
                {tab === "inspect" && <Inspector record={record} />}
                {tab === "json" && (
                  <pre style={{
                    margin: 0, padding: 12, font: "11px/16px " + MONO,
                    color: "#b8d7a3", whiteSpace: "pre-wrap", wordBreak: "break-word",
                  }}>
                    {record ? JSON.stringify(record, null, 2) : "// run a program to produce a record"}
                  </pre>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function btn(bg, cursor = "pointer") {
  return {
    background: bg, color: "#fff", border: "none", borderRadius: 3,
    padding: "4px 11px", cursor, fontSize: 11.5, fontFamily: MONO,
  };
}

function Hint({ children }) {
  return <div style={{ padding: 26, color: "#6f6f6f", fontFamily: MONO, fontSize: 12, lineHeight: 1.8 }}>
    {children}
  </div>;
}

function Terminal({ log }) {
  if (!log.length) return <Hint>Press ▶ Run, or ⌃⏎, to execute the active program.</Hint>;
  return (
    <pre style={{ margin: 0, padding: 14, font: "12px/19px " + MONO, color: "#cfcfcf" }}>
      {log.map((l, i) => {
        let color = "#cfcfcf";
        if (l.startsWith("$")) color = "#569cd6";
        else if (l.includes("status: OK")) color = "#4ec9b0";
        else if (l.includes("status: INVALID") || l.includes("did not compile")) color = "#f44747";
        else if (l.includes("status: NEGATIVE")) color = "#d19a66";
        else if (l.trim().startsWith("emit")) color = "#b5cea8";
        else if (l.trim().startsWith("witness")) color = "#c586c0";
        return <div key={i} style={{ color }}>{l || "​"}</div>;
      })}
    </pre>
  );
}

/** Per-cycle table: the numbers behind each verdict, in one place. */
function Inspector({ record }) {
  if (!record) return <Hint>Run a program to inspect its cycles.</Hint>;
  if (record.status === "ERROR") return <Hint>Nothing was computed.</Hint>;
  if (!record.verdicts.length) return <Hint>This program produced no verdicts.</Hint>;

  const th = {
    textAlign: "left", padding: "6px 10px", color: "#8a8a8a",
    fontWeight: 500, borderBottom: "1px solid #2f2f2f", whiteSpace: "nowrap",
  };
  const td = { padding: "5px 10px", borderBottom: "1px solid #242424", whiteSpace: "nowrap" };

  return (
    <div style={{ padding: 12, overflow: "auto" }}>
      <table style={{ borderCollapse: "collapse", fontFamily: MONO, fontSize: 11 }}>
        <thead>
          <tr>
            {["line", "cycle", "L", "Λ", "|H|", "ε_num", "ε_data", "ε*", "verdict"]
              .map((h) => <th key={h} style={th}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {record.verdicts.map((v, i) => (
            <tr key={i}>
              <td style={{ ...td, color: "#6e6e6e" }}>{v.line}</td>
              <td style={{ ...td, color: "#9cdcfe" }}>{v.holonomy.loop}</td>
              <td style={td}>{v.holonomy.length}</td>
              <td style={td}>{fmt(v.holonomy.potentialRange)}</td>
              <td style={{ ...td, color: "#e4e4e4" }}>{fmt(Math.abs(v.holonomy.value))}</td>
              <td style={{ ...td, color: "#569cd6" }}>{fmt(v.tolerance.numerical)}</td>
              <td style={{ ...td, color: "#c586c0" }}>
                {v.tolerance.dataAvailable ? fmt(v.tolerance.data) : "undefined"}
              </td>
              <td style={td}>{fmt(v.tolerance.star)}</td>
              <td style={{ ...td, color: VERDICT_COLOR[v.verdict], fontWeight: 600 }}>
                {v.verdict}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {record.witnessSet && (
        <div style={{ marginTop: 14, fontFamily: MONO, fontSize: 11.5, color: "#c586c0" }}>
          witness set = {"{"}{record.witnessSet.join(", ")}{"}"}
          <span style={{ color: "#6e6e6e" }}>   (edges on every flagged cycle)</span>
        </div>
      )}
    </div>
  );
}

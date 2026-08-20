/**
 * ChartColumn.jsx -- the charts, laid out for a narrow vertical column.
 *
 * Each chart is given the measured width of the column rather than a
 * fixed one, so the output pane stays legible at any split position.
 * Charts are stacked with a short caption above each, because in a
 * column the reader scrolls rather than scans.
 */

import React from "react";
import {
  CircuitGraph, CycleSpace3D, FloorGapChart, ToleranceChart, VerdictBars,
} from "./charts.jsx";
import useMeasure from "./useMeasure.js";

const MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";

function Block({ caption, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {caption && (
        <div style={{
          fontSize: 10, color: "#7f7f7f", fontFamily: MONO,
          margin: "0 0 5px 2px", lineHeight: 1.5,
        }}>
          {caption}
        </div>
      )}
      {children}
    </div>
  );
}

export default function ChartColumn({ record, circuit }) {
  const [ref, w] = useMeasure(430);
  // The measured element must not itself scroll horizontally, or its
  // clientWidth would track the content rather than the column. Padding
  // is subtracted here; the floor keeps axis labels from colliding when
  // the pane is dragged very narrow.
  const cw = Math.max(300, w - 24);
  const ch = Math.round(Math.min(300, Math.max(210, cw * 0.62)));

  if (!record) {
    return <Hint innerRef={ref}>Run a program to see its charts.</Hint>;
  }

  if (record.status === "ERROR") {
    return (
      <div ref={ref} style={{ padding: 14, fontFamily: MONO }}>
        <div style={{ color: "#f44747", fontSize: 12, marginBottom: 9 }}>
          The program did not compile.
        </div>
        <div style={{
          color: "#d4d4d4", fontSize: 11, lineHeight: 1.7, background: "#241a1a",
          border: "1px solid #4a2a2a", borderRadius: 5, padding: 11,
          wordBreak: "break-word",
        }}>
          {record.error}
        </div>
        <div style={{ color: "#8a8a8a", fontSize: 10.5, marginTop: 12, lineHeight: 1.75 }}>
          There are no charts because nothing was computed. This is the
          intended behaviour when a program states something the language
          does not permit — a verdict without its tolerance has no
          derivation in the grammar at all.
        </div>
      </div>
    );
  }

  const hasV = record.verdicts.length > 0;
  if (!hasV && !circuit) {
    return <Hint innerRef={ref}>This program produced no verdicts, so there is nothing to plot.</Hint>;
  }

  return (
    <div ref={ref} style={{ padding: 12, minWidth: 0 }}>
      {hasV && (
        <Block caption="Cycle sums against both floors. Bar colour is the verdict; dashed lines are ε_num and ε_data.">
          <ToleranceChart verdicts={record.verdicts} width={cw} height={ch} />
        </Block>
      )}
      {circuit && (
        <Block caption={record.witnessSet?.length
          ? `Circuit. Red edges are the witness set — the defect lies in {${record.witnessSet.join(", ")}}.`
          : "Circuit. Edge width is |flux|."}>
          <CircuitGraph circuit={circuit} witness={record.witnessSet || []}
            width={cw} height={ch} />
        </Block>
      )}
      {record.tolerances.length > 0 && (
        <Block caption="Separation between the two floors, per cycle, in orders of magnitude.">
          <FloorGapChart tolerances={record.tolerances} width={cw} height={ch} />
        </Block>
      )}
      {hasV && (
        <Block caption="Cycles in (length, log|H|, log ε*). Drop-lines give depth without waiting for rotation.">
          <CycleSpace3D verdicts={record.verdicts} width={cw} height={ch} />
        </Block>
      )}
      {hasV && (
        <Block caption="Verdict composition.">
          <VerdictBars verdicts={record.verdicts} width={cw} height={Math.round(ch * 0.8)} />
        </Block>
      )}
    </div>
  );
}

/** Plain component: `ref` here is the callback ref from useMeasure, so
    it must be applied directly rather than forwarded. */
function Hint({ children, innerRef }) {
  return (
    <div ref={innerRef} style={{
      padding: 22, color: "#6f6f6f", fontFamily: MONO, fontSize: 11.5,
      lineHeight: 1.8,
    }}>{children}</div>
  );
}

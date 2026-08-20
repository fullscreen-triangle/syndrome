/**
 * charts.jsx -- D3 and Three.js visualisations driven by the run record.
 *
 * Every mark is a value the interpreter actually produced. There is no
 * synthetic data path: if a program does not compute a quantity, the
 * chart that would show it is not rendered.
 */

import React, { useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";
import * as THREE from "three";

export const BG = "#1e1e1e";
export const FG = "#cccccc";
export const GRID = "#333333";

export const VERDICT_COLOR = {
  CONSISTENT: "#4ec9b0",
  UNDECIDABLE: "#d19a66",
  INCONSISTENT: "#f44747",
};

const BLUE = "#569cd6";
const PURPLE = "#c586c0";
const MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";

function useD3(render, deps) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    render(svg);
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps
  return ref;
}

function axisStyle(g) {
  g.selectAll("text").attr("fill", FG).attr("font-size", 9).attr("font-family", MONO);
  g.selectAll(".domain,.tick line").attr("stroke", GRID);
}

function title(svg, w, text) {
  svg.append("text").attr("x", w / 2).attr("y", 15).text(text)
    .attr("fill", FG).attr("font-size", 11.5).attr("text-anchor", "middle")
    .attr("font-family", MONO);
}

const frame = { background: BG, borderRadius: 6, border: "1px solid #2d2d2d" };

// =====================================================================
// 1. Cycle sums against both floors  -- the paper's central picture
// =====================================================================

export function ToleranceChart({ verdicts, width = 470, height = 300 }) {
  const ref = useD3((svg) => {
    const m = { t: 30, r: 16, b: 46, l: 62 };
    const w = width - m.l - m.r, h = height - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

    const data = verdicts.map((v, i) => ({
      key: `${v.holonomy.loop}#${i}`,
      label: v.holonomy.loop.replace(/^cyc_/, ""),
      abs: Math.max(Math.abs(v.holonomy.value), 1e-18),
      num: v.tolerance.numerical,
      dat: v.tolerance.data,
      verdict: v.verdict,
    }));

    const x = d3.scaleBand().domain(data.map((d) => d.key)).range([0, w]).padding(0.28);
    const lo = d3.min(data, (d) => Math.min(d.abs, d.num)) * 0.2;
    const hi = d3.max(data, (d) => Math.max(d.abs, d.dat ?? d.num)) * 5;
    const y = d3.scaleLog().domain([lo, hi]).range([h, 0]).clamp(true);

    g.append("g").attr("transform", `translate(0,${h})`)
      .call(d3.axisBottom(x).tickFormat((k) => data.find((d) => d.key === k).label))
      .call(axisStyle);
    g.append("g").call(d3.axisLeft(y).ticks(6, ".0e")).call(axisStyle);

    data.forEach((d) => {
      const bx = x(d.key);
      g.append("rect")
        .attr("x", bx).attr("y", y(d.abs))
        .attr("width", x.bandwidth()).attr("height", Math.max(0, h - y(d.abs)))
        .attr("fill", VERDICT_COLOR[d.verdict]).attr("opacity", 0.85);
      g.append("line")
        .attr("x1", bx - 3).attr("x2", bx + x.bandwidth() + 3)
        .attr("y1", y(d.num)).attr("y2", y(d.num))
        .attr("stroke", BLUE).attr("stroke-width", 1.6).attr("stroke-dasharray", "3,2");
      if (d.dat != null) {
        g.append("line")
          .attr("x1", bx - 3).attr("x2", bx + x.bandwidth() + 3)
          .attr("y1", y(d.dat)).attr("y2", y(d.dat))
          .attr("stroke", PURPLE).attr("stroke-width", 1.6).attr("stroke-dasharray", "6,3");
      }
    });

    const leg = g.append("g").attr("transform", `translate(6,2)`);
    [["ε num", BLUE, "3,2"], ["ε data", PURPLE, "6,3"]].forEach(([t, c, dash], i) => {
      leg.append("line").attr("x1", 0).attr("x2", 18)
        .attr("y1", i * 14).attr("y2", i * 14)
        .attr("stroke", c).attr("stroke-dasharray", dash).attr("stroke-width", 1.6);
      leg.append("text").attr("x", 23).attr("y", i * 14 + 3.5).text(t)
        .attr("fill", FG).attr("font-size", 9).attr("font-family", MONO);
    });

    title(svg, width, "Cycle sums vs both tolerance floors");
    g.append("text").attr("transform", "rotate(-90)").attr("x", -h / 2).attr("y", -48)
      .text("|H| (kJ/mol)").attr("fill", "#888").attr("font-size", 9)
      .attr("text-anchor", "middle").attr("font-family", MONO);
  }, [verdicts, width, height]);

  return <svg ref={ref} width={width} height={height} style={frame} />;
}

// =====================================================================
// 2. Circuit graph, with the witness set highlighted
// =====================================================================

export function CircuitGraph({ circuit, witness = [], width = 470, height = 300 }) {
  const ref = useD3((svg) => {
    const nodes = circuit.nodes.map((id) => ({ id, mu: circuit.mu[id] }));
    // d3-force resolves `source`/`target`, so map the kernel's src/dst
    // onto those names rather than leaving them undefined.
    const links = circuit.edges.map((e) => ({
      ...e, source: e.src, target: e.dst,
    }));
    const W = new Set(witness);

    const sim = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(74).strength(0.85))
      .force("charge", d3.forceManyBody().strength(-320))
      .force("center", d3.forceCenter(width / 2, height / 2 + 6))
      .force("collide", d3.forceCollide(26))
      .stop();
    for (let i = 0; i < 320; i++) sim.tick();

    // Node circles are r=15 with a label inside, so the padding has to
    // clear the glyph rather than just the centre point -- otherwise
    // nodes at the extremes are cut off by the frame.
    const pad = 34;
    const xs = d3.extent(nodes, (d) => d.x), ys = d3.extent(nodes, (d) => d.y);
    const sx = d3.scaleLinear().domain(xs).range([pad, width - pad]);
    const sy = d3.scaleLinear().domain(ys).range([height - pad, pad + 14]);

    svg.append("defs").append("marker")
      .attr("id", "arrowhead").attr("viewBox", "0 0 10 6")
      .attr("refX", 20).attr("refY", 3)
      .attr("markerWidth", 7).attr("markerHeight", 5).attr("orient", "auto")
      .append("path").attr("d", "M0,0L10,3L0,6Z").attr("fill", "#5a5a5a");

    const fluxes = links.map((l) => Math.abs(l.flux));
    const wStroke = d3.scaleLinear()
      .domain([d3.min(fluxes) ?? 0, d3.max(fluxes) ?? 1]).range([1, 3.4]);

    links.forEach((l) => {
      const inW = W.has(l.name);
      const perturbed = Math.abs(l.offset) > 0;
      svg.append("line")
        .attr("x1", sx(l.source.x)).attr("y1", sy(l.source.y))
        .attr("x2", sx(l.target.x)).attr("y2", sy(l.target.y))
        .attr("stroke", inW ? "#f44747" : perturbed ? "#d19a66" : "#4a4a4a")
        .attr("stroke-width", inW ? 3.2 : wStroke(Math.abs(l.flux)))
        .attr("marker-end", "url(#arrowhead)");
      const mx = (sx(l.source.x) + sx(l.target.x)) / 2;
      const my = (sy(l.source.y) + sy(l.target.y)) / 2;
      svg.append("text").attr("x", mx).attr("y", my - 6).text(l.name)
        .attr("fill", inW ? "#f44747" : "#7a7a7a")
        .attr("font-size", 9).attr("text-anchor", "middle").attr("font-family", MONO)
        .attr("font-weight", inW ? "bold" : "normal");
    });

    nodes.forEach((n) => {
      svg.append("circle").attr("cx", sx(n.x)).attr("cy", sy(n.y)).attr("r", 15)
        .attr("fill", "#264f78").attr("stroke", BLUE).attr("stroke-width", 1.4);
      svg.append("text").attr("x", sx(n.x)).attr("y", sy(n.y) + 3.5)
        .text(n.id.length > 5 ? n.id.slice(0, 5) : n.id)
        .attr("fill", "#dfe7ef").attr("font-size", 8.5).attr("text-anchor", "middle")
        .attr("font-family", MONO);
    });

    title(svg, width, witness.length
      ? `Circuit — witness set {${witness.join(", ")}}`
      : "Circuit graph");
  }, [circuit, witness, width, height]);

  return <svg ref={ref} width={width} height={height} style={frame} />;
}

// =====================================================================
// 3. Floor separation: eps_num vs eps_data per cycle
// =====================================================================

export function FloorGapChart({ tolerances, width = 470, height = 300 }) {
  const ref = useD3((svg) => {
    const m = { t: 30, r: 18, b: 46, l: 62 };
    const w = width - m.l - m.r, h = height - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

    const data = tolerances.map((t, i) => ({
      key: `${t.loop}#${i}`,
      label: t.loop.replace(/^cyc_/, ""),
      num: t.numerical,
      dat: t.data,
    }));
    const x = d3.scaleBand().domain(data.map((d) => d.key)).range([0, w]).padding(0.4);
    const lo = d3.min(data, (d) => d.num) * 0.2;
    const hi = d3.max(data, (d) => d.dat ?? d.num) * 5;
    const y = d3.scaleLog().domain([lo, hi]).range([h, 0]).clamp(true);

    g.append("g").attr("transform", `translate(0,${h})`)
      .call(d3.axisBottom(x).tickFormat((k) => data.find((d) => d.key === k).label))
      .call(axisStyle);
    g.append("g").call(d3.axisLeft(y).ticks(7, ".0e")).call(axisStyle);

    data.forEach((d) => {
      const cx = x(d.key) + x.bandwidth() / 2;
      if (d.dat != null) {
        g.append("line").attr("x1", cx).attr("x2", cx)
          .attr("y1", y(d.num)).attr("y2", y(d.dat))
          .attr("stroke", "#5a4a6a").attr("stroke-width", 7).attr("opacity", 0.5);
        g.append("circle").attr("cx", cx).attr("cy", y(d.dat)).attr("r", 4.5)
          .attr("fill", PURPLE);
        const orders = Math.log10(d.dat / d.num);
        g.append("text").attr("x", cx).attr("y", y(d.dat) - 9)
          .text(`${orders.toFixed(1)}`).attr("fill", PURPLE).attr("font-size", 8.5)
          .attr("text-anchor", "middle").attr("font-family", MONO);
      }
      g.append("circle").attr("cx", cx).attr("cy", y(d.num)).attr("r", 4.5)
        .attr("fill", BLUE);
    });

    title(svg, width, "Floor separation (orders of magnitude)");
    g.append("text").attr("transform", "rotate(-90)").attr("x", -h / 2).attr("y", -48)
      .text("kJ/mol").attr("fill", "#888").attr("font-size", 9)
      .attr("text-anchor", "middle").attr("font-family", MONO);
  }, [tolerances, width, height]);

  return <svg ref={ref} width={width} height={height} style={frame} />;
}

// =====================================================================
// 4. Verdict composition
// =====================================================================

export function VerdictBars({ verdicts, width = 320, height = 300 }) {
  const ref = useD3((svg) => {
    const m = { t: 30, r: 16, b: 46, l: 48 };
    const w = width - m.l - m.r, h = height - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

    const order = ["CONSISTENT", "UNDECIDABLE", "INCONSISTENT"];
    const counts = order.map((k) => ({
      k, n: verdicts.filter((v) => v.verdict === k).length,
    }));
    const x = d3.scaleBand().domain(order).range([0, w]).padding(0.32);
    const y = d3.scaleLinear()
      .domain([0, Math.max(1, d3.max(counts, (d) => d.n))]).nice().range([h, 0]);

    g.append("g").attr("transform", `translate(0,${h})`)
      .call(d3.axisBottom(x).tickFormat((s) => s.slice(0, 5).toLowerCase()))
      .call(axisStyle);
    g.append("g").call(d3.axisLeft(y).ticks(5, "d")).call(axisStyle);

    counts.forEach((d) => {
      g.append("rect").attr("x", x(d.k)).attr("y", y(d.n))
        .attr("width", x.bandwidth()).attr("height", h - y(d.n))
        .attr("fill", VERDICT_COLOR[d.k]).attr("opacity", 0.9);
      if (d.n > 0) {
        g.append("text").attr("x", x(d.k) + x.bandwidth() / 2).attr("y", y(d.n) - 5)
          .text(d.n).attr("fill", VERDICT_COLOR[d.k]).attr("font-size", 11)
          .attr("text-anchor", "middle").attr("font-family", MONO)
          .attr("font-weight", "bold");
      }
    });

    title(svg, width, "Verdict composition");
  }, [verdicts, width, height]);

  return <svg ref={ref} width={width} height={height} style={frame} />;
}

// =====================================================================
// 5. Three.js -- cycles in (length, log|H|, log eps*) space
// =====================================================================

export function CycleSpace3D({ verdicts, width = 470, height = 300 }) {
  const mount = useRef(null);

  const pts = useMemo(() => verdicts.map((v) => ({
    L: v.holonomy.length,
    h: Math.log10(Math.max(Math.abs(v.holonomy.value), 1e-18)),
    e: Math.log10(Math.max(v.tolerance.star, 1e-18)),
    verdict: v.verdict,
  })), [verdicts]);

  useEffect(() => {
    const el = mount.current;
    if (!el || !pts.length) return;
    while (el.firstChild) el.removeChild(el.firstChild);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e1e1e);
    const camera = new THREE.PerspectiveCamera(46, width / height, 0.1, 200);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    el.appendChild(renderer.domElement);

    const ext = (f) => {
      const vs = pts.map(f);
      const lo = Math.min(...vs), hi = Math.max(...vs);
      return hi - lo < 1e-9 ? [lo - 1, hi + 1] : [lo, hi];
    };
    const [L0, L1] = ext((p) => p.L);
    const [h0, h1] = ext((p) => p.h);
    const [e0, e1] = ext((p) => p.e);
    const nx = (v, a, b) => ((v - a) / (b - a) - 0.5) * 3;

    const grid = new THREE.GridHelper(3.4, 8, 0x3a3a3a, 0x2c2c2c);
    grid.position.y = -1.7;
    scene.add(grid);

    const axMat = new THREE.LineBasicMaterial({ color: 0x555555 });
    [[[-1.7, -1.7, -1.7], [1.7, -1.7, -1.7]],
     [[-1.7, -1.7, -1.7], [-1.7, 1.7, -1.7]],
     [[-1.7, -1.7, -1.7], [-1.7, -1.7, 1.7]]].forEach(([a, b]) => {
      scene.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(...a), new THREE.Vector3(...b)]), axMat));
    });

    pts.forEach((p) => {
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.11, 18, 18),
        new THREE.MeshBasicMaterial({
          color: new THREE.Color(VERDICT_COLOR[p.verdict]),
        }));
      mesh.position.set(nx(p.L, L0, L1), nx(p.h, h0, h1), nx(p.e, e0, e1));
      scene.add(mesh);
      // drop line to the floor, so depth is readable without motion
      const g2 = new THREE.BufferGeometry().setFromPoints([
        mesh.position.clone(),
        new THREE.Vector3(mesh.position.x, -1.7, mesh.position.z)]);
      scene.add(new THREE.Line(g2, new THREE.LineBasicMaterial({
        color: new THREE.Color(VERDICT_COLOR[p.verdict]),
        transparent: true, opacity: 0.32,
      })));
    });

    let angle = 0.6, raf;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      angle += 0.0042;
      camera.position.set(5.4 * Math.cos(angle), 2.9, 5.4 * Math.sin(angle));
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
    };
    tick();

    return () => {
      cancelAnimationFrame(raf);
      renderer.dispose();
      if (renderer.domElement.parentNode === el) el.removeChild(renderer.domElement);
    };
  }, [pts, width, height]);

  return (
    <div style={{ position: "relative", ...frame, width, height, overflow: "hidden" }}>
      <div ref={mount} />
      <div style={{
        position: "absolute", top: 6, left: 0, right: 0, textAlign: "center",
        color: FG, fontSize: 11.5, fontFamily: MONO, pointerEvents: "none",
      }}>
        Cycle space — length × log|H| × log ε*
      </div>
      <div style={{
        position: "absolute", bottom: 6, left: 8, color: "#777",
        fontSize: 8.5, fontFamily: MONO, pointerEvents: "none",
      }}>
        x: length · y: log|H| · z: log ε*
      </div>
    </div>
  );
}

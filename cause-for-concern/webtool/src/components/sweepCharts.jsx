/**
 * sweepCharts.jsx -- visualisations for the parameter sweeps.
 *
 * Every mark is a circuit that was built, solved and classified in the
 * browser moments earlier. Re-running with a different seed moves the
 * points, which is the point: these are measurements, not illustrations.
 */

import React, { useEffect, useMemo, useRef } from "react";
import * as d3 from "d3";
import * as THREE from "three";

const BG = "#1e1e1e";
const FG = "#cccccc";
const GRID = "#333333";
const BLUE = "#569cd6";
const ORANGE = "#d19a66";
const PURPLE = "#c586c0";
const RED = "#f44747";
const TEAL = "#4ec9b0";
const MONO = "ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";

const SEQ = d3.scaleSequential(d3.interpolateBlues);
const frame = { background: BG, borderRadius: 6, border: "1px solid #2d2d2d" };

function useD3(render, deps) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    render(svg);
  }, deps); // eslint-disable-line
  return ref;
}

const ax = (g) => {
  g.selectAll("text").attr("fill", FG).attr("font-size", 9).attr("font-family", MONO);
  g.selectAll(".domain,.tick line").attr("stroke", GRID);
};

const title = (svg, w, t) =>
  svg.append("text").attr("x", w / 2).attr("y", 15).text(t)
    .attr("fill", FG).attr("font-size", 11.5).attr("text-anchor", "middle")
    .attr("font-family", MONO);

const label = (g, x, y, t, rot) => {
  const e = g.append("text").attr("x", x).attr("y", y).text(t)
    .attr("fill", "#888").attr("font-size", 9).attr("text-anchor", "middle")
    .attr("font-family", MONO);
  if (rot) e.attr("transform", `rotate(${rot})`);
  return e;
};

// =====================================================================
// V1 -- noise scale
// =====================================================================

export function NoiseCharts({ data, w = 468, h = 292 }) {
  const errRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 42, l: 66 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const lams = [...new Set(data.grid.map((d) => d.lambda))].sort((a, b) => a - b);
    const Ls = [...new Set(data.grid.map((d) => d.length))].sort((a, b) => a - b);

    // Some cells are computed EXACTLY -- short cycles at low potential
    // give a bit-exact zero. A log axis cannot show 0, so clamp to a
    // sentinel below the smallest nonzero value and mark it, rather
    // than dropping the point or pretending it is nonzero.
    const nz = data.grid.map((d) => d.maxAbsError).filter((v) => v > 0);
    const FLOORV = (nz.length ? Math.min(...nz) : 1e-16) * 0.25;
    const val = (d) => (d.maxAbsError > 0 ? d.maxAbsError : FLOORV);
    const anyExact = data.grid.some((d) => d.maxAbsError === 0);

    const x = d3.scaleLinear().domain(d3.extent(Ls)).range([0, W]);
    const y = d3.scaleLog()
      .domain([FLOORV * 0.6, d3.max(data.grid, (d) => d.maxAbsError) * 2])
      .range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(6)).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(6, ".0e")).call(ax);

    lams.forEach((lam, i) => {
      const pts = data.grid.filter((d) => d.lambda === lam)
        .sort((a, b) => a.length - b.length);
      const col = SEQ(0.35 + 0.18 * i);
      g.append("path").datum(pts)
        .attr("d", d3.line().x((d) => x(d.length)).y((d) => y(val(d))))
        .attr("fill", "none").attr("stroke", col).attr("stroke-width", 1.8);
      pts.forEach((p) => g.append("circle")
        .attr("cx", x(p.length)).attr("cy", y(val(p))).attr("r", 2.6)
        .attr("fill", p.maxAbsError > 0 ? col : "#1e1e1e")
        .attr("stroke", col).attr("stroke-width", 1.1));
      g.append("text").attr("x", W - 2).attr("y", y(val(pts[pts.length - 1])) - 4)
        .text(`Λ=${lam}`).attr("fill", col).attr("font-size", 8.5)
        .attr("text-anchor", "end").attr("font-family", MONO);
    });

    if (anyExact) {
      g.append("line").attr("x1", 0).attr("x2", W)
        .attr("y1", y(FLOORV)).attr("y2", y(FLOORV))
        .attr("stroke", "#4a4a4a").attr("stroke-dasharray", "2,3");
      g.append("text").attr("x", 2).attr("y", y(FLOORV) - 4)
        .text("exactly 0 (hollow)").attr("fill", "#7a7a7a")
        .attr("font-size", 8).attr("font-family", MONO);
    }

    title(svg, w, "Rounding error vs cycle length");
    label(g, W / 2, H + 34, "cycle length L");
    label(g, -H / 2, -50, "max |computed sum|", -90);
  }, [data, w, h]);

  const boundRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 42, l: 66 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const nzb = data.grid.map((d) => d.maxAbsError).filter((v) => v > 0);
    const FLOORB = (nzb.length ? Math.min(...nzb) : 1e-16) * 0.25;
    const vb = (d) => (d.maxAbsError > 0 ? d.maxAbsError : FLOORB);
    const lo = Math.min(FLOORB, d3.min(data.grid, (d) => d.meanBound)) * 0.4;
    const hi = d3.max(data.grid, (d) => Math.max(d.maxAbsError, d.meanBound)) * 2.5;
    const s = d3.scaleLog().domain([lo, hi]);
    const x = s.copy().range([0, W]), y = s.copy().range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(5, ".0e")).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(5, ".0e")).call(ax);
    g.append("line").attr("x1", 0).attr("y1", H).attr("x2", W).attr("y2", 0)
      .attr("stroke", "#666").attr("stroke-dasharray", "4,3");

    data.grid.forEach((d) => g.append("circle")
      .attr("cx", x(vb(d))).attr("cy", y(d.meanBound)).attr("r", 3.4)
      .attr("fill", BLUE).attr("opacity", 0.8).attr("stroke", "#1e1e1e")
      .attr("stroke-width", 0.5));

    g.append("text").attr("x", 6).attr("y", 12)
      .text(`${data.violations} violations / ${data.trials}`)
      .attr("fill", data.violations ? RED : TEAL).attr("font-size", 9.5)
      .attr("font-family", MONO);

    title(svg, w, "Bound vs measured (all above diagonal)");
    label(g, W / 2, H + 34, "measured error");
    label(g, -H / 2, -50, "bound ε_num", -90);
  }, [data, w, h]);

  return (
    <>
      <svg ref={errRef} width={w} height={h} style={frame} />
      <svg ref={boundRef} width={w} height={h} style={frame} />
      <NoiseSurface3D data={data} w={w} h={h} />
    </>
  );
}

function NoiseSurface3D({ data, w, h }) {
  const mount = useRef(null);
  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    while (el.firstChild) el.removeChild(el.firstChild);

    const Ls = [...new Set(data.grid.map((d) => d.length))].sort((a, b) => a - b);
    const lams = [...new Set(data.grid.map((d) => d.lambda))].sort((a, b) => a - b);
    const at = (L, lam) => data.grid.find((d) => d.length === L && d.lambda === lam);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e1e1e);
    const cam = new THREE.PerspectiveCamera(46, w / h, 0.1, 200);
    const rend = new THREE.WebGLRenderer({ antialias: true });
    rend.setPixelRatio(Math.min(devicePixelRatio, 2));
    rend.setSize(w, h);
    el.appendChild(rend.domElement);

    const zs = data.grid.map((d) => Math.log10(d.meanBound));
    const z0 = Math.min(...zs), z1 = Math.max(...zs);
    const nx = (i, n) => (i / (n - 1) - 0.5) * 3;
    const nz = (v) => ((v - z0) / (z1 - z0) - 0.5) * 2.2;

    const geo = new THREE.BufferGeometry();
    const verts = [], colors = [], idx = [];
    for (let i = 0; i < lams.length; i++) {
      for (let j = 0; j < Ls.length; j++) {
        const v = Math.log10(at(Ls[j], lams[i]).meanBound);
        verts.push(nx(i, lams.length), nz(v), nx(j, Ls.length));
        const c = new THREE.Color(d3.interpolateBlues(0.25 + 0.7 * ((v - z0) / (z1 - z0))));
        colors.push(c.r, c.g, c.b);
      }
    }
    for (let i = 0; i < lams.length - 1; i++) {
      for (let j = 0; j < Ls.length - 1; j++) {
        const a = i * Ls.length + j, b = a + 1;
        const c = (i + 1) * Ls.length + j, d = c + 1;
        idx.push(a, c, b, b, c, d);
      }
    }
    geo.setAttribute("position", new THREE.Float32BufferAttribute(verts, 3));
    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geo.setIndex(idx);
    geo.computeVertexNormals();
    scene.add(new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
      vertexColors: true, side: THREE.DoubleSide,
    })));
    const wire = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
      color: 0xffffff, wireframe: true, transparent: true, opacity: 0.14,
    }));
    scene.add(wire);

    const grid = new THREE.GridHelper(3.4, 8, 0x3a3a3a, 0x2a2a2a);
    grid.position.y = -1.35;
    scene.add(grid);

    let a = 0.7, raf;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      a += 0.0038;
      cam.position.set(4.4 * Math.cos(a), 2.2, 4.4 * Math.sin(a));
      cam.lookAt(0, -0.45, 0);
      rend.render(scene, cam);
    };
    tick();
    return () => {
      cancelAnimationFrame(raf);
      rend.dispose();
      geo.dispose();
      if (rend.domElement.parentNode === el) el.removeChild(rend.domElement);
    };
  }, [data, w, h]);

  return (
    <div style={{ position: "relative", ...frame, width: w, height: h, overflow: "hidden" }}>
      <div ref={mount} />
      <Overlay top>Numerical floor surface — log₁₀ ε_num</Overlay>
      <Overlay bottom>x: Λ · y: log ε_num · z: L</Overlay>
    </div>
  );
}

function Overlay({ children, top, bottom }) {
  return (
    <div style={{
      position: "absolute", left: 0, right: 0, pointerEvents: "none",
      textAlign: bottom ? "left" : "center",
      top: top ? 6 : undefined, bottom: bottom ? 6 : undefined,
      paddingLeft: bottom ? 9 : 0,
      color: bottom ? "#777" : FG,
      fontSize: bottom ? 8.5 : 11.5, fontFamily: MONO,
    }}>{children}</div>
  );
}

// =====================================================================
// V2 -- fixed tolerance
// =====================================================================

export function FixedCharts({ data, w = 468, h = 292 }) {
  const fpRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 54, l: 52 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const x = d3.scaleBand().domain(data.strata.map((s) => s.stratum))
      .range([0, W]).padding(0.3);
    const y = d3.scaleLinear().domain([0, 1]).range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).tickFormat((s) => s.replace(", ", "\n")))
      .call(ax).selectAll("text").attr("font-size", 8);
    g.append("g").call(d3.axisLeft(y).ticks(5)).call(ax);

    const bw = x.bandwidth() / 2;
    data.strata.forEach((s) => {
      // binary64 is exactly zero -- draw a stub so the finding is visible
      g.append("rect").attr("x", x(s.stratum)).attr("y", y(Math.max(s.fp64, 0.02)))
        .attr("width", bw).attr("height", H - y(Math.max(s.fp64, 0.02)))
        .attr("fill", BLUE);
      g.append("rect").attr("x", x(s.stratum) + bw).attr("y", y(s.fp32))
        .attr("width", bw).attr("height", H - y(s.fp32)).attr("fill", ORANGE);
    });
    g.append("line").attr("x1", 0).attr("x2", W).attr("y1", H).attr("y2", H)
      .attr("stroke", "#666");

    const leg = g.append("g").attr("transform", "translate(4,2)");
    [["binary64 (all 0.000)", BLUE], ["binary32", ORANGE]].forEach(([t, c], i) => {
      leg.append("rect").attr("x", 0).attr("y", i * 13).attr("width", 10)
        .attr("height", 9).attr("fill", c);
      leg.append("text").attr("x", 14).attr("y", i * 13 + 8).text(t)
        .attr("fill", FG).attr("font-size", 8.5).attr("font-family", MONO);
    });

    title(svg, w, "False positives — a precision phenomenon");
    label(g, -H / 2, -38, "false-positive rate", -90);
  }, [data, w, h]);

  const missRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 42, l: 52 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const x = d3.scaleLog().domain(d3.extent(data.defects)).range([0, W]);
    const y = d3.scaleLinear().domain([-0.03, 1.03]).range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(6, ".0e")).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(5)).call(ax);

    g.append("line").attr("x1", x(data.epsFixed)).attr("x2", x(data.epsFixed))
      .attr("y1", 0).attr("y2", H).attr("stroke", RED)
      .attr("stroke-dasharray", "4,3").attr("stroke-width", 1.4);
    g.append("text").attr("x", x(data.epsFixed) + 4).attr("y", 11)
      .text("ε fixed").attr("fill", RED).attr("font-size", 8.5)
      .attr("font-family", MONO);

    data.strata.forEach((s, i) => {
      const pts = data.defects.map((D) => ({ D, m: s.missByDefect[D] }));
      g.append("path").datum(pts)
        .attr("d", d3.line().x((d) => x(d.D)).y((d) => y(d.m)))
        .attr("fill", "none").attr("stroke", SEQ(0.3 + 0.17 * i))
        .attr("stroke-width", 1.8);
    });

    title(svg, w, "Missed detections below the threshold");
    label(g, W / 2, H + 34, "injected defect D (kJ/mol)");
    label(g, -H / 2, -38, "missed rate", -90);
  }, [data, w, h]);

  return (
    <>
      <svg ref={fpRef} width={w} height={h} style={frame} />
      <svg ref={missRef} width={w} height={h} style={frame} />
    </>
  );
}

// =====================================================================
// V3 -- trichotomy
// =====================================================================

const TRI_FILL = ["#4393c3", "#f4a582", "#b2182b"];

export function TrichotomyCharts({ data, w = 468, h = 292 }) {
  const mapRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 42, l: 56 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const lx = data.defects.map(Math.log10), ly = data.sigmas.map(Math.log10);
    const x = d3.scaleLinear().domain(d3.extent(lx)).range([0, W]);
    const y = d3.scaleLinear().domain(d3.extent(ly)).range([H, 0]);
    const cw = W / (lx.length - 1), ch = H / (ly.length - 1);

    data.surface.forEach((row, i) => row.forEach((v, j) => {
      g.append("rect")
        .attr("x", x(lx[j]) - cw / 2).attr("y", y(ly[i]) - ch / 2)
        .attr("width", cw + 0.6).attr("height", ch + 0.6)
        .attr("fill", TRI_FILL[v]);
    }));

    g.append("path")
      .datum(data.epsData.map((e, i) => [Math.log10(e), ly[i]]))
      .attr("d", d3.line().x((p) => x(p[0])).y((p) => y(p[1])))
      .attr("fill", "none").attr("stroke", "#fff").attr("stroke-width", 2);
    g.append("line")
      .attr("x1", x(Math.log10(data.epsNum))).attr("x2", x(Math.log10(data.epsNum)))
      .attr("y1", 0).attr("y2", H).attr("stroke", "#111")
      .attr("stroke-dasharray", "4,3");

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(6)).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(5)).call(ax);

    title(svg, w, `Verdict map — ${(data.fractions.UNDECIDABLE * 100).toFixed(1)}% undecidable`);
    label(g, W / 2, H + 34, "log₁₀ D (kJ/mol)");
    label(g, -H / 2, -42, "log₁₀ σ (kJ/mol)", -90);
  }, [data, w, h]);

  const floorRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 42, l: 62 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const x = d3.scaleLog().domain(d3.extent(data.sigmas)).range([0, W]);
    const y = d3.scaleLog()
      .domain([data.epsNum * 0.4, d3.max(data.epsData) * 3]).range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(5, ".0e")).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(7, ".0e")).call(ax);

    g.append("path")
      .datum(data.sigmas.map((s, i) => [s, data.epsData[i]]))
      .attr("d", d3.area().x((p) => x(p[0])).y0(y(data.epsNum))
        .y1((p) => y(p[1])))
      .attr("fill", "#f4a582").attr("opacity", 0.16);
    g.append("path")
      .datum(data.sigmas.map((s, i) => [s, data.epsData[i]]))
      .attr("d", d3.line().x((p) => x(p[0])).y((p) => y(p[1])))
      .attr("fill", "none").attr("stroke", RED).attr("stroke-width", 2);
    g.append("line").attr("x1", 0).attr("x2", W)
      .attr("y1", y(data.epsNum)).attr("y2", y(data.epsNum))
      .attr("stroke", BLUE).attr("stroke-width", 2);

    g.append("text").attr("x", W - 4).attr("y", y(data.epsNum) - 6)
      .text("ε_num").attr("fill", BLUE).attr("font-size", 9)
      .attr("text-anchor", "end").attr("font-family", MONO);
    g.append("text").attr("x", 6).attr("y", H / 2)
      .text("UNDECIDABLE band").attr("fill", "#c98a63").attr("font-size", 9)
      .attr("font-family", MONO);
    g.append("text").attr("x", W - 4).attr("y", 14)
      .text(`gap ≈ ${data.gapOrders.toFixed(1)} orders`)
      .attr("fill", PURPLE).attr("font-size", 9)
      .attr("text-anchor", "end").attr("font-family", MONO);

    title(svg, w, "The two floors, and the band between them");
    label(g, W / 2, H + 34, "σ (kJ/mol)");
    label(g, -H / 2, -48, "floor (kJ/mol)", -90);
  }, [data, w, h]);

  return (
    <>
      <svg ref={mapRef} width={w} height={h} style={frame} />
      <svg ref={floorRef} width={w} height={h} style={frame} />
    </>
  );
}

// =====================================================================
// V4 -- basis dependence
// =====================================================================

export function BasisCharts({ data, w = 468, h = 292 }) {
  const scatRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 44, l: 52 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const hi = Math.max(
      d3.max(data.rows, (d) => d.flaggedMcb),
      d3.max(data.rows, (d) => d.flaggedFcb)) + 1;
    const x = d3.scaleLinear().domain([0, hi]).range([0, W]);
    const y = d3.scaleLinear().domain([0, hi]).range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(hi, "d")).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(hi, "d")).call(ax);
    g.append("line").attr("x1", x(0)).attr("y1", y(0)).attr("x2", x(hi)).attr("y2", y(hi))
      .attr("stroke", "#666").attr("stroke-dasharray", "4,3");

    let k = 0;
    const jit = () => ((k = (k * 9301 + 49297) % 233280) / 233280 - 0.5) * 0.28;
    data.rows.forEach((d) => {
      const agree = d.flaggedMcb === d.flaggedFcb;
      g.append("circle")
        .attr("cx", x(d.flaggedMcb + jit())).attr("cy", y(d.flaggedFcb + jit()))
        .attr("r", 3.2).attr("fill", agree ? "#6a6a6a" : ORANGE)
        .attr("opacity", 0.8);
    });

    g.append("text").attr("x", 6).attr("y", 12)
      .text(`${(data.flaggedDisagreeRate * 100).toFixed(1)}% disagree`)
      .attr("fill", ORANGE).attr("font-size", 9.5).attr("font-family", MONO);
    g.append("text").attr("x", 6).attr("y", 25)
      .text(`verdict disagreements: ${data.verdictDisagree}`)
      .attr("fill", TEAL).attr("font-size", 9.5).attr("font-family", MONO);

    title(svg, w, "Flagged cycles — minimum vs fundamental basis");
    label(g, W / 2, H + 34, "flagged, minimum basis");
    label(g, -H / 2, -38, "flagged, fundamental", -90);
  }, [data, w, h]);

  const histRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 44, l: 52 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const all = data.rows.flatMap((d) => [d.witnessMcb, d.witnessFcb]);
    const hi = d3.max(all) + 1;
    const x = d3.scaleLinear().domain([0.5, hi]).range([0, W]);
    const bins = (key) => d3.bin().domain([0.5, hi])
      .thresholds(d3.range(0.5, hi + 1, 1))(data.rows.map((d) => d[key]));
    const bm = bins("witnessMcb"), bf = bins("witnessFcb");
    const y = d3.scaleLinear()
      .domain([0, Math.max(d3.max(bm, (b) => b.length), d3.max(bf, (b) => b.length))])
      .nice().range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(hi, "d")).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(5, "d")).call(ax);

    const draw = (bins, col, off) => bins.forEach((b) => {
      const bw = Math.max(1, (x(b.x1) - x(b.x0)) / 2 - 1);
      g.append("rect").attr("x", x(b.x0) + off * bw).attr("y", y(b.length))
        .attr("width", bw).attr("height", H - y(b.length))
        .attr("fill", col).attr("opacity", 0.85);
    });
    draw(bm, BLUE, 0);
    draw(bf, ORANGE, 1);

    const leg = g.append("g").attr("transform", `translate(${W - 118},2)`);
    [[`min  μ=${data.meanWitnessMcb?.toFixed(2)}`, BLUE],
     [`fund μ=${data.meanWitnessFcb?.toFixed(2)}`, ORANGE]].forEach(([t, c], i) => {
      leg.append("rect").attr("x", 0).attr("y", i * 13).attr("width", 10)
        .attr("height", 9).attr("fill", c);
      leg.append("text").attr("x", 14).attr("y", i * 13 + 8).text(t)
        .attr("fill", FG).attr("font-size", 8.5).attr("font-family", MONO);
    });

    title(svg, w, `Witness-set size — defect found ${(data.witnessHitMcb * 100).toFixed(0)}%`);
    label(g, W / 2, H + 34, "witness-set size (edges)");
    label(g, -H / 2, -38, "networks", -90);
  }, [data, w, h]);

  return (
    <>
      <svg ref={scatRef} width={w} height={h} style={frame} />
      <svg ref={histRef} width={w} height={h} style={frame} />
    </>
  );
}

// =====================================================================
// V5 -- detection
// =====================================================================

export function DetectionCharts({ data, w = 468, h = 292 }) {
  const curveRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 44, l: 52 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const x = d3.scaleLog().domain([1e-3, 1e3]).range([0, W]).clamp(true);
    const y = d3.scaleLinear().domain([-0.06, 1.06]).range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(7, ".0e")).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(3)).call(ax);

    [[1, "#666", ":", "ε*"], [2, RED, "4,3", "2ε*"]].forEach(([v, c, dash, t]) => {
      g.append("line").attr("x1", x(v)).attr("x2", x(v)).attr("y1", 0).attr("y2", H)
        .attr("stroke", c).attr("stroke-dasharray", dash === ":" ? "2,2" : dash)
        .attr("stroke-width", 1.4);
      g.append("text").attr("x", x(v) + 3).attr("y", 11).text(t)
        .attr("fill", c).attr("font-size", 8.5).attr("font-family", MONO);
    });

    data.curves.forEach((c, i) => {
      const pts = c.D.map((D, j) => ({ u: D / c.epsStar, d: c.detected[j] }));
      g.append("path").datum(pts)
        .attr("d", d3.line().x((p) => x(p.u)).y((p) => y(p.d))
          .curve(d3.curveStepAfter))
        .attr("fill", "none").attr("stroke", SEQ(0.3 + 0.15 * i))
        .attr("stroke-width", 1.8).attr("opacity", 0.9);
    });

    g.append("text").attr("x", 6).attr("y", H - 6)
      .text(`${data.violations} guarantee violations / ${data.evaluations}`)
      .attr("fill", data.violations ? RED : TEAL).attr("font-size", 9)
      .attr("font-family", MONO);

    title(svg, w, "Detection, in units of ε*");
    label(g, W / 2, H + 34, "D / ε*");
    label(g, -H / 2, -36, "detected", -90);
  }, [data, w, h]);

  const threshRef = useD3((svg) => {
    const m = { t: 30, r: 16, b: 44, l: 62 };
    const W = w - m.l - m.r, H = h - m.t - m.b;
    const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const s = d3.scaleLog()
      .domain([d3.min(data.curves, (c) => c.empirical) * 0.5,
               d3.max(data.curves, (c) => c.predicted) * 2]);
    const x = s.copy().range([0, W]), y = s.copy().range([H, 0]);

    g.append("g").attr("transform", `translate(0,${H})`)
      .call(d3.axisBottom(x).ticks(5, ".0e")).call(ax);
    g.append("g").call(d3.axisLeft(y).ticks(5, ".0e")).call(ax);
    g.append("line").attr("x1", 0).attr("y1", H).attr("x2", W).attr("y2", 0)
      .attr("stroke", "#666").attr("stroke-dasharray", "4,3");

    data.curves.forEach((c, i) => {
      g.append("circle").attr("cx", x(c.empirical)).attr("cy", y(c.predicted))
        .attr("r", 5).attr("fill", SEQ(0.34 + 0.14 * i))
        .attr("stroke", "#1e1e1e").attr("stroke-width", 0.8);
      g.append("text").attr("x", x(c.empirical)).attr("y", y(c.predicted) - 9)
        .text(`σ=${c.sigma}`).attr("fill", "#999").attr("font-size", 8)
        .attr("text-anchor", "middle").attr("font-family", MONO);
    });

    g.append("text").attr("x", 6).attr("y", 12)
      .text(`ratio ${data.minRatio.toFixed(2)}–${data.maxRatio.toFixed(2)}`)
      .attr("fill", TEAL).attr("font-size", 9.5).attr("font-family", MONO);

    title(svg, w, "Empirical vs guaranteed threshold");
    label(g, W / 2, H + 34, "empirical (kJ/mol)");
    label(g, -H / 2, -48, "predicted 2ε*", -90);
  }, [data, w, h]);

  return (
    <>
      <svg ref={curveRef} width={w} height={h} style={frame} />
      <svg ref={threshRef} width={w} height={h} style={frame} />
    </>
  );
}

export function SweepCharts({ result, width }) {
  if (!result) return null;
  const props = { data: result, w: width ?? 468 };
  switch (result.kind) {
    case "noise": return <NoiseCharts {...props} />;
    case "fixed": return <FixedCharts {...props} />;
    case "trichotomy": return <TrichotomyCharts {...props} />;
    case "basis": return <BasisCharts {...props} />;
    case "detection": return <DetectionCharts {...props} />;
    default: return null;
  }
}

"""
Regenerate the Block 1 <script> sections for the 5 tool HTML files,
replacing broken dc.js focus+context charts with D3.js publication figures.
For each tool:
  - #ctx-chart   → dc.js bar chart (brush only, for filtering)
  - #foc-chart   → D3.js SVG chart from the publication figure
"""

import re, os

BASE = os.path.dirname(__file__)

# ─────────────────────────────────────────────────────────────────────────────
# Shared D3 helper (injected at top of every renderFocusD3 function)
# ─────────────────────────────────────────────────────────────────────────────

AXIS_STYLE = """
    .call(a=>{
      a.select('.domain').attr('stroke','#2e3350');
      a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace');
      a.selectAll('.tick line').attr('stroke','#2e3350');
    })"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. ESCAPE PREDICTOR  — top escape-score bar chart (publication Panel A)
# ─────────────────────────────────────────────────────────────────────────────

ESCAPE_FOCUS_FN = r"""
function renderFocusD3(data, tn, tb) {
  var el = document.getElementById('focus-chart');
  if (!el) return;
  d3.select('#focus-chart').selectAll('*').remove();
  if (!data || !data.length) return;
  var W = Math.max(260, (el.clientWidth||480)-4), H = 160;
  var top = data.slice(0, 22);
  var sMax = d3.max(top, function(d){return d.score;})||0.01;
  var sMin = d3.min(top, function(d){return d.score;})||0;
  var ml=96, mr=12, mt=10, mb=22;
  var fw=W-ml-mr, fh=H-mt-mb;
  var svg = d3.select('#focus-chart').append('svg').attr('width',W).attr('height',H);
  var g = svg.append('g');
  var x = d3.scaleLinear().domain([Math.min(sMin,0), sMax*1.06]).range([0,fw]);
  var yB = d3.scaleBand().domain(d3.range(top.length)).range([mt,mt+fh]).padding(0.18);
  var xZero = ml+x(0);
  // zero line
  g.append('line').attr('x1',xZero).attr('x2',xZero).attr('y1',mt).attr('y2',mt+fh)
    .attr('stroke','#2e3350').attr('stroke-width',1);
  top.forEach(function(r,i){
    var col = r.viable?'#f87171': r.partial?'#fbbf24':'#34d399';
    var bw  = Math.abs(x(r.score)-x(0));
    var bx  = r.score>=0 ? xZero : xZero-bw;
    g.append('rect').attr('x',bx).attr('y',yB(i)).attr('width',bw).attr('height',yB.bandwidth())
      .attr('fill',col).attr('opacity',0.78);
    g.append('text').attr('x',ml-3).attr('y',yB(i)+yB.bandwidth()/2+3).attr('text-anchor','end')
      .attr('fill','#94a3b8').attr('font-size',8).attr('font-family','monospace')
      .text((r.pos+1)+r.wt+'→'+r.mut);
  });
  g.append('g').attr('transform','translate('+ml+','+(mt+fh)+')')
    .call(d3.axisBottom(x).ticks(5).tickFormat(function(d){return d.toFixed(2);}))
    .call(function(a){
      a.select('.domain').attr('stroke','#2e3350');
      a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);
      a.selectAll('.tick line').attr('stroke','#2e3350');
    });
  svg.append('text').attr('x',ml+fw/2).attr('y',H-3).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace')
    .text('Escape score  E₁ = −ρ_Ab + w·ρ_Rec  · top '+top.length+' variants');
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. RESISTANCE  — WT vs Mutant drug-binding scatter (publication Panel B)
# ─────────────────────────────────────────────────────────────────────────────

RESISTANCE_FOCUS_FN = r"""
function renderFocusD3(data) {
  var el = document.getElementById('foc-chart');
  if (!el) return;
  d3.select('#foc-chart').selectAll('*').remove();
  if (!data || !data.length) return;
  var W = Math.max(220,(el.parentElement.clientWidth||380)-32), H = 170;
  var ml=44, mr=12, mt=12, mb=30;
  var fw=W-ml-mr, fh=H-mt-mb;
  var allRho = data.map(function(d){return d.rhoWT;}).concat(data.map(function(d){return d.rhoMut;}));
  var rhoMin = (d3.min(allRho)||0)-0.04, rhoMax = (d3.max(allRho)||1)+0.04;
  var svg = d3.select('#foc-chart').append('svg').attr('width',W).attr('height',H);
  var g = svg.append('g').attr('transform','translate('+ml+','+mt+')');
  var x = d3.scaleLinear().domain([rhoMin,rhoMax]).range([0,fw]);
  var y = d3.scaleLinear().domain([rhoMin,rhoMax]).range([fh,0]);
  // grid
  g.selectAll('.gv').data(x.ticks(5)).enter().append('line')
    .attr('x1',function(d){return x(d);}).attr('x2',function(d){return x(d);})
    .attr('y1',0).attr('y2',fh).attr('stroke','#2e3350').attr('opacity',0.5);
  g.selectAll('.gh').data(y.ticks(5)).enter().append('line')
    .attr('x1',0).attr('x2',fw)
    .attr('y1',function(d){return y(d);}).attr('y2',function(d){return y(d);})
    .attr('stroke','#2e3350').attr('opacity',0.5);
  // diagonal y=x (no change line)
  g.append('line').attr('x1',x(rhoMin)).attr('y1',y(rhoMin))
    .attr('x2',x(rhoMax)).attr('y2',y(rhoMax))
    .attr('stroke','#64748b').attr('stroke-dasharray','4,3').attr('stroke-width',1);
  // points
  data.forEach(function(d){
    var col = d.cat==='Resistant'?'#f87171':d.cat==='Intermediate'?'#fbbf24':'#34d399';
    g.append('circle').attr('cx',x(d.rhoWT)).attr('cy',y(d.rhoMut))
      .attr('r',2.2).attr('fill',col).attr('opacity',0.55);
  });
  // axes
  g.append('g').attr('transform','translate(0,'+fh+')')
    .call(d3.axisBottom(x).ticks(5))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  g.append('g').call(d3.axisLeft(y).ticks(5))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  svg.append('text').attr('x',ml+fw/2).attr('y',H-3).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('ρ(WT drug binding)');
  svg.append('text').attr('transform','rotate(-90)').attr('x',-(mt+fh/2)).attr('y',12)
    .attr('text-anchor','middle').attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('ρ(Mut drug binding)');
  svg.append('text').attr('x',ml+fw/2).attr('y',mt-1).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace')
    .text('Below diagonal → resistance (reduced drug affinity)');
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. MHC BINDING  — Binding-ball radius curve (publication Panel 2C)
# ─────────────────────────────────────────────────────────────────────────────

MHC_FOCUS_FN = r"""
function renderFocusD3(rhoStar) {
  var el = document.getElementById('mhc-focus-chart');
  if (!el) return;
  d3.select('#mhc-focus-chart').selectAll('*').remove();
  var W = Math.max(260,(el.clientWidth||480)-4), H = 180;
  var ml=48, mr=18, mt=18, mb=32;
  var fw=W-ml-mr, fh=H-mt-mb;
  var svg = d3.select('#mhc-focus-chart').append('svg').attr('width',W).attr('height',H);
  var g = svg.append('g').attr('transform','translate('+ml+','+mt+')');
  var xS = d3.scaleLinear().domain([0,1]).range([0,fw]);
  var yS = d3.scaleLinear().domain([0, Math.SQRT2+0.02]).range([fh,0]);
  // curve data: r* = sqrt(2(1-rho))
  var pts = d3.range(0,1.002,0.005).map(function(r){return {r:r,v:Math.sqrt(2*(1-r))};});
  // fill area
  var area = d3.area().x(function(d){return xS(d.r);}).y0(fh).y1(function(d){return yS(d.v);}).curve(d3.curveBasis);
  g.append('path').datum(pts).attr('d',area).attr('fill','#4f8ef7').attr('opacity',0.12);
  // curve
  var line = d3.line().x(function(d){return xS(d.r);}).y(function(d){return yS(d.v);}).curve(d3.curveBasis);
  g.append('path').datum(pts).attr('d',line).attr('fill','none').attr('stroke','#4f8ef7').attr('stroke-width',2);
  // grid lines
  g.selectAll('.gy').data([0,0.2,0.4,0.6,0.8,1.0,Math.SQRT2]).enter().append('line')
    .attr('x1',0).attr('x2',fw).attr('y1',function(d){return yS(d);}).attr('y2',function(d){return yS(d);})
    .attr('stroke','#2e3350').attr('opacity',0.5);
  // current rho* marker
  var rStar = Math.sqrt(2*(1-rhoStar));
  var xM = xS(rhoStar), yM = yS(rStar);
  g.append('line').attr('x1',xM).attr('x2',xM).attr('y1',0).attr('y2',fh)
    .attr('stroke','#fbbf24').attr('stroke-dasharray','4,3').attr('stroke-width',1.5);
  g.append('line').attr('x1',0).attr('x2',xM).attr('y1',yM).attr('y2',yM)
    .attr('stroke','#fbbf24').attr('stroke-dasharray','4,3').attr('stroke-width',1.5);
  g.append('circle').attr('cx',xM).attr('cy',yM).attr('r',5).attr('fill','#fbbf24').attr('opacity',0.9);
  g.append('text').attr('x',xM+6).attr('y',yM-5).attr('fill','#fbbf24')
    .attr('font-size',9).attr('font-family','monospace')
    .text('ρ*='+rhoStar.toFixed(2)+' → r*='+rStar.toFixed(3));
  // axes
  g.append('g').attr('transform','translate(0,'+fh+')')
    .call(d3.axisBottom(xS).ticks(8))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  g.append('g').call(d3.axisLeft(yS).ticks(6))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  svg.append('text').attr('x',ml+fw/2).attr('y',H-3).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('Binding threshold ρ*');
  svg.append('text').attr('transform','rotate(-90)').attr('x',-(mt+fh/2)).attr('y',12)
    .attr('text-anchor','middle').attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('Ball radius r*');
  svg.append('text').attr('x',ml+fw/2).attr('y',mt-4).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace')
    .text('r* = √(2(1−ρ*)) — binding ball geometry (Theorem 4.1)');
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 4. TCR CROSS-REACTIVITY  — semi-log cross-reactivity fraction (Pub Panel 3B)
# ─────────────────────────────────────────────────────────────────────────────

TCR_FOCUS_FN = r"""
function renderFocusD3(results) {
  var el = document.getElementById('foc-chart');
  if (!el) return;
  d3.select('#foc-chart').selectAll('*').remove();
  if (!results || !results.length) return;
  var W = Math.max(220,(el.parentElement.clientWidth||380)-32), H = 180;
  var ml=50, mr=14, mt=14, mb=30;
  var fw=W-ml-mr, fh=H-mt-mb;
  var thetaAct = parseFloat(document.getElementById('theta').value);
  var rhos = results.map(function(d){return d.rho;});
  var n = rhos.length;
  // compute cross-reactivity fraction at each threshold
  var thresholds = d3.range(0.05, 0.96, 0.02);
  var fracs = thresholds.map(function(t){
    return {t:t, f:Math.max(1e-4, rhos.filter(function(r){return r>=t;}).length/n)};
  });
  var svg = d3.select('#foc-chart').append('svg').attr('width',W).attr('height',H);
  var g = svg.append('g').attr('transform','translate('+ml+','+mt+')');
  var xS = d3.scaleLinear().domain([0.05,0.95]).range([0,fw]);
  var yS = d3.scaleLog().domain([1e-4,1.5]).range([fh,0]).clamp(true);
  // grid at decade boundaries
  [1e-4,1e-3,1e-2,0.1,1].forEach(function(v){
    g.append('line').attr('x1',0).attr('x2',fw).attr('y1',yS(v)).attr('y2',yS(v))
      .attr('stroke','#2e3350').attr('opacity',0.55);
  });
  // area fill
  var area = d3.area().x(function(d){return xS(d.t);}).y0(fh).y1(function(d){return yS(d.f);}).curve(d3.curveBasis);
  g.append('path').datum(fracs).attr('d',area).attr('fill','#34d399').attr('opacity',0.12);
  // curve
  var line = d3.line().x(function(d){return xS(d.t);}).y(function(d){return yS(d.f);}).curve(d3.curveBasis);
  g.append('path').datum(fracs).attr('d',line).attr('fill','none').attr('stroke','#34d399').attr('stroke-width',2);
  // current theta_act marker
  var curF = Math.max(1e-4, rhos.filter(function(r){return r>=thetaAct;}).length/n);
  g.append('line').attr('x1',xS(thetaAct)).attr('x2',xS(thetaAct)).attr('y1',0).attr('y2',fh)
    .attr('stroke','#fbbf24').attr('stroke-dasharray','4,3').attr('stroke-width',1.5);
  g.append('circle').attr('cx',xS(thetaAct)).attr('cy',yS(curF)).attr('r',5).attr('fill','#fbbf24');
  g.append('text').attr('x',xS(thetaAct)+6).attr('y',yS(curF)-4)
    .attr('fill','#fbbf24').attr('font-size',9).attr('font-family','monospace')
    .text((curF*100).toFixed(1)+'%');
  // axes
  g.append('g').attr('transform','translate(0,'+fh+')')
    .call(d3.axisBottom(xS).ticks(7))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  g.append('g').call(d3.axisLeft(yS).tickValues([1e-4,1e-3,1e-2,0.1,1]).tickFormat(d3.format('.0e')))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  svg.append('text').attr('x',ml+fw/2).attr('y',H-3).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('Activation threshold θ');
  svg.append('text').attr('transform','rotate(-90)').attr('x',-(mt+fh/2)).attr('y',12)
    .attr('text-anchor','middle').attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('Cross-reactive fraction (log)');
  svg.append('text').attr('x',ml+fw/2).attr('y',mt-2).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace')
    .text('Mason’s ≥10⁶ estimate: library of '+n+' peptides');
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 5. TROPISM  — position vs ρ jitter scatter (publication Panel 2: scan plot)
# ─────────────────────────────────────────────────────────────────────────────

TROPISM_FOCUS_FN = r"""
function renderFocusD3(results) {
  var el = document.getElementById('foc-chart');
  if (!el) return;
  d3.select('#foc-chart').selectAll('*').remove();
  if (!results || !results.length) return;
  var W = Math.max(220,(el.parentElement.clientWidth||380)-32), H = 180;
  var ml=42, mr=12, mt=12, mb=30;
  var fw=W-ml-mr, fh=H-mt-mb;
  var rhoStar = parseFloat(document.getElementById('rhostar').value);
  var positions = d3.map(results, function(d){return d.pos;}).keys().map(Number).sort(function(a,b){return a-b;});
  var nPos = positions.length;
  var allRho = results.map(function(d){return d.rho;});
  var yMin = (d3.min(allRho)||0)-0.03, yMax = (d3.max(allRho)||1)+0.03;
  var xS = d3.scaleLinear().domain([0,nPos-1]).range([0,fw]);
  var yS = d3.scaleLinear().domain([yMin,yMax]).range([fh,0]);
  var posIndex = {};
  positions.forEach(function(p,i){posIndex[p]=i;});
  var svg = d3.select('#foc-chart').append('svg').attr('width',W).attr('height',H);
  var g = svg.append('g').attr('transform','translate('+ml+','+mt+')');
  // grid
  g.selectAll('.gy').data(yS.ticks(5)).enter().append('line')
    .attr('x1',0).attr('x2',fw).attr('y1',function(d){return yS(d);}).attr('y2',function(d){return yS(d);})
    .attr('stroke','#2e3350').attr('opacity',0.45);
  // rho* threshold
  g.append('line').attr('x1',0).attr('x2',fw).attr('y1',yS(rhoStar)).attr('y2',yS(rhoStar))
    .attr('stroke','#f87171').attr('stroke-dasharray','4,3').attr('stroke-width',1.5);
  g.append('text').attr('x',4).attr('y',yS(rhoStar)-3)
    .attr('fill','#f87171').attr('font-size',8).attr('font-family','monospace').text('ρ*='+rhoStar.toFixed(2));
  // WT baseline
  var wtPt = results.filter(function(d){return d.isWT;})[0];
  if(wtPt){
    g.append('line').attr('x1',0).attr('x2',fw).attr('y1',yS(wtPt.rho)).attr('y2',yS(wtPt.rho))
      .attr('stroke','#64748b').attr('stroke-dasharray','2,3').attr('stroke-width',1);
    g.append('text').attr('x',fw-2).attr('y',yS(wtPt.rho)-3).attr('text-anchor','end')
      .attr('fill','#64748b').attr('font-size',8).attr('font-family','monospace').text('WT');
  }
  // scatter points with deterministic x-jitter (based on mut char code)
  results.filter(function(d){return !d.isWT;}).forEach(function(d){
    var pi = posIndex[d.pos];
    if(pi===undefined) return;
    var jitter = ((d.mut.charCodeAt(0)%11)-5)*0.4;
    var col = d.cat==='Tropic'?'#f87171':'#4f8ef7';
    var op  = d.cat==='Tropic'?0.75:0.25;
    g.append('circle').attr('cx',xS(pi)+jitter*(fw/nPos)/10).attr('cy',yS(d.rho))
      .attr('r',2).attr('fill',col).attr('opacity',op);
  });
  // axes — show every 10th position label
  var tickPositions = positions.filter(function(_,i){return i%Math.ceil(nPos/8)===0;});
  g.append('g').attr('transform','translate(0,'+fh+')')
    .call(d3.axisBottom(xS).tickValues(tickPositions.map(function(p){return posIndex[p];}))
      .tickFormat(function(i){return positions[i];}))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  g.append('g').call(d3.axisLeft(yS).ticks(5))
    .call(function(a){a.select('.domain').attr('stroke','#2e3350');a.selectAll('.tick text').attr('fill','#64748b').attr('font-size',9);a.selectAll('.tick line').attr('stroke','#2e3350');});
  svg.append('text').attr('x',ml+fw/2).attr('y',H-3).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('Residue position');
  svg.append('text').attr('transform','rotate(-90)').attr('x',-(mt+fh/2)).attr('y',12)
    .attr('text-anchor','middle').attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace').text('ρ(variant, receptor)');
  svg.append('text').attr('x',ml+fw/2).attr('y',mt-2).attr('text-anchor','middle')
    .attr('fill','#64748b').attr('font-size',9).attr('font-family','monospace')
    .text('Mutation scan landscape — red = tropic, blue = non-tropic');
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# Patch each file: inject the D3 function and redirect the focC/focusChart
# ─────────────────────────────────────────────────────────────────────────────

def patch_file(filename, d3_fn, old_foc_block, new_foc_block, old_filter_block, new_filter_block):
    path = os.path.join(BASE, filename)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Inject D3 function just before the closing </script> of Block 1
    #    Find the last occurrence of the pattern we want to insert before
    inject_marker = old_foc_block.split('\n')[0]  # first line of old focus block
    insert_pos = html.find(inject_marker)
    if insert_pos == -1:
        print(f"  WARNING: inject marker not found in {filename}")
        return False
    html = html[:insert_pos] + d3_fn + '\n' + html[insert_pos:]

    # 2. Replace the old dc.js focus chart block with the new call
    if old_foc_block in html:
        html = html.replace(old_foc_block, new_foc_block, 1)
    else:
        print(f"  WARNING: focus block not found in {filename}")
        return False

    # 3. Replace the filter handler block
    if old_filter_block and old_filter_block in html:
        html = html.replace(old_filter_block, new_filter_block, 1)
    else:
        print(f"  WARNING: filter block not found in {filename}")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Patched: {filename}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# ESCAPE PREDICTOR patches
# ─────────────────────────────────────────────────────────────────────────────
escape_old_foc = """  // Focus line chart linked to context
  var focusChart = dc.lineChart('#focus-chart')
    .width(focW).height(160)
    .margins({top: 10, right: 10, bottom: 28, left: 38})
    .dimension(scoreDim).group(scoreGroup)
    .x(d3.scaleLinear().domain([sMin, sMax]))
    .brushOn(false).rangeChart(ctxChart)
    .renderArea(true).colors('#34d399')
    .renderHorizontalGridLines(true);"""

escape_new_foc = """  // D3.js escape score bar chart (replaces broken dc.js line chart)
  renderFocusD3(results, tn, tb);"""

escape_old_filter = """  function onFilter() {
    var active = new Set(_scoreDim.top(Infinity));
    updateScatter(_results, active, _tn, _tb);
    updateTable(_scoreDim.top(40));
  }
  [ctxChart, posChart, pieChart].forEach(function(c) {
    c.on('filtered', onFilter);
  });"""

escape_new_filter = """  function onFilter() {
    var filtered = _scoreDim.top(Infinity);
    var active = new Set(filtered);
    renderFocusD3(filtered, _tn, _tb);
    updateScatter(_results, active, _tn, _tb);
    updateTable(_scoreDim.top(40));
  }
  [ctxChart, posChart, pieChart].forEach(function(c) {
    c.on('filtered', onFilter);
  });"""

# ─────────────────────────────────────────────────────────────────────────────
# RESISTANCE patches
# ─────────────────────────────────────────────────────────────────────────────
resistance_old_foc = """  const focGrp = deltaDim.group();
  const focC = dc.barChart('#foc-chart');
  focC.width(document.getElementById('foc-chart').parentElement.clientWidth-32).height(170)
    .dimension(deltaDim).group(focGrp)
    .x(d3.scaleLinear().domain([-1,1])).xUnits(dc.units.fp.precision(0.05))
    .barPadding(0.05).outerPadding(0.02).elasticY(true)
    .colorCalculator(d=>d.key<-0.05?'#f87171':d.key>0.05?'#34d399':'#fbbf24')
    .margins({top:8,right:12,bottom:28,left:40});
  focC.rangeChart(ctxC);"""

resistance_new_foc = """  // D3.js WT vs Mutant drug-binding scatter (replaces broken dc.js bar chart)
  renderFocusD3(results);"""

resistance_old_filter = """  dcCharts=[ctxC,focC,posC,catC];
  [posC,catC].forEach(c=>c.on('filtered',()=>updateLandscape()));
  focC.on('filtered',()=>updateLandscape());"""

resistance_new_filter = """  dcCharts=[ctxC,posC,catC];
  [posC,catC,ctxC].forEach(c=>c.on('filtered',()=>{updateLandscape();renderFocusD3(deltaDim.top(Infinity));}));"""

# ─────────────────────────────────────────────────────────────────────────────
# MHC BINDING patches
# ─────────────────────────────────────────────────────────────────────────────
mhc_old_foc = """  // ── Focus line chart (linked to context brush) ────────────────────────────────
  var focusEl = document.getElementById('mhc-focus-chart');
  var focusW  = focusEl.clientWidth || 480;

  var focusChart = dc.lineChart('#mhc-focus-chart')
    .width(focusW)
    .height(180)
    .margins({top: 10, right: 10, bottom: 30, left: 40})
    .dimension(rhoDim)
    .group(rhoGroup)
    .x(d3.scaleLinear().domain(xDomain))
    .brushOn(false)
    .rangeChart(ctxChart)
    .renderArea(true)
    .colors('#34d399')
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true);

  // rho* marker line
  focusChart.on('renderlet', function(chart) {
    var x   = chart.x()(_rhoStar);
    var svg = chart.svg();
    var line = svg.select('.rhostar-line');
    if (line.empty()) {
      line = svg.append('line')
        .attr('class', 'rhostar-line')
        .attr('stroke', '#fbbf24')
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '4,3');
    }
    var ml = chart.margins().left;
    var mt = chart.margins().top;
    var mb = chart.margins().bottom;
    line
      .attr('x1', ml + x).attr('x2', ml + x)
      .attr('y1', mt).attr('y2', chart.height() - mb);
  });"""

mhc_new_foc = """  // D3.js binding ball radius curve (replaces broken dc.js line chart)
  renderFocusD3(rhoStar);"""

mhc_old_filter = """  // Re-render heatmap on any filter change
  [ctxChart, pieChart, rowChart].forEach(function(c) {
    c.on('filtered', function() { window.renderEmbHeatmap(results, rhoDim); });
  });"""

mhc_new_filter = """  // Re-render heatmap and binding ball curve on any filter change
  [ctxChart, pieChart, rowChart].forEach(function(c) {
    c.on('filtered', function() {
      renderFocusD3(_rhoStar);
      window.renderEmbHeatmap(results, rhoDim);
    });
  });"""

# ─────────────────────────────────────────────────────────────────────────────
# TCR CROSS-REACTIVITY patches
# ─────────────────────────────────────────────────────────────────────────────
tcr_old_foc = """  // Focus bar chart (linked to context)
  const focGrp = rhoDim.group();
  const focC = dc.barChart('#foc-chart');
  focC.width(document.getElementById('foc-chart').parentElement.clientWidth-32).height(180)
    .dimension(rhoDim).group(focGrp)
    .x(d3.scaleLinear().domain([-1,1]))
    .xUnits(dc.units.fp.precision(0.05))
    .barPadding(0.05).outerPadding(0.02)
    .elasticY(true).colorCalculator(d=>{
      if(d.key>=thetaAct) return '#f87171';
      if(d.key>=thetaAct-0.1) return '#fbbf24';
      return '#4f8ef7';
    })
    .margins({top:8,right:12,bottom:28,left:40});
  focC.xAxis().ticks(8);
  focC.yAxis().ticks(4);

  focC.rangeChart(ctxC);"""

tcr_new_foc = """  // D3.js semi-log cross-reactivity plot (replaces broken dc.js bar chart)
  renderFocusD3(results);"""

tcr_old_filter = """  dcCharts=[ctxC,focC,grpC,catC];

  [grpC,catC].forEach(c=>c.on('filtered',()=>updateScatter()));
  focC.on('filtered',()=>updateScatter());"""

tcr_new_filter = """  dcCharts=[ctxC,grpC,catC];

  [grpC,catC,ctxC].forEach(c=>c.on('filtered',()=>{
    updateScatter();
    renderFocusD3(rhoDim.top(Infinity));
  }));"""

# ─────────────────────────────────────────────────────────────────────────────
# TROPISM patches
# ─────────────────────────────────────────────────────────────────────────────
tropism_old_foc = """  const focGrp = rhoDim.group();
  const focC = dc.barChart('#foc-chart');
  focC.width(document.getElementById('foc-chart').parentElement.clientWidth-32).height(180)
    .dimension(rhoDim).group(focGrp)
    .x(d3.scaleLinear().domain([-1,1])).xUnits(dc.units.fp.precision(0.05))
    .barPadding(0.05).outerPadding(0.02).elasticY(true)
    .colorCalculator(d=>d.key>=rhoStar?'#f87171':'#fb923c')
    .margins({top:8,right:12,bottom:28,left:40});
  focC.rangeChart(ctxC);"""

tropism_new_foc = """  // D3.js mutation scan landscape (replaces broken dc.js bar chart)
  renderFocusD3(results);"""

tropism_old_filter = """  dcCharts=[ctxC,focC,posC,catC];
  [posC,catC].forEach(c=>c.on('filtered',()=>updateHeatmap()));
  focC.on('filtered',()=>updateHeatmap());"""

tropism_new_filter = """  dcCharts=[ctxC,posC,catC];
  [posC,catC,ctxC].forEach(c=>c.on('filtered',()=>{
    updateHeatmap();
    renderFocusD3(rhoDim.top(Infinity));
  }));"""

# ─────────────────────────────────────────────────────────────────────────────
# Run all patches
# ─────────────────────────────────────────────────────────────────────────────
print("Patching tool dashboards...")

patch_file('escape-predictor/index.html', ESCAPE_FOCUS_FN,
           escape_old_foc, escape_new_foc,
           escape_old_filter, escape_new_filter)

patch_file('resistance/index.html', RESISTANCE_FOCUS_FN,
           resistance_old_foc, resistance_new_foc,
           resistance_old_filter, resistance_new_filter)

patch_file('mhc-binding/index.html', MHC_FOCUS_FN,
           mhc_old_foc, mhc_new_foc,
           mhc_old_filter, mhc_new_filter)

patch_file('tcr-crossreactivity/index.html', TCR_FOCUS_FN,
           tcr_old_foc, tcr_new_foc,
           tcr_old_filter, tcr_new_filter)

patch_file('tropism/index.html', TROPISM_FOCUS_FN,
           tropism_old_foc, tropism_new_foc,
           tropism_old_filter, tropism_new_filter)

print("Done.")

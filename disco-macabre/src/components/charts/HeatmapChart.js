import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';

const THEME = {
  bg: '#0a0a0f',
  text: '#a0a0b0',
  axis: '#4a4a5a',
};

const HeatmapChart = ({
  data = [],
  xLabels = [],
  yLabels = [],
  width: propWidth = 500,
  height: propHeight = 300,
  colorRange = ['#0a0a0f', '#58E6D9'],
  title = '',
}) => {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: propWidth, height: propHeight });

  // Handle resize
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width } = entry.contentRect;
        if (width > 0) {
          setDimensions({ width, height: propHeight });
        }
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, [propHeight]);

  // Draw chart
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!svgRef.current || !data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const tooltip = d3.select(tooltipRef.current);

    const { width, height } = dimensions;
    const margin = {
      top: title ? 30 : 15,
      right: 15,
      bottom: 50,
      left: 60,
    };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    if (innerWidth <= 0 || innerHeight <= 0) return;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Title
    if (title) {
      svg
        .append('text')
        .attr('x', width / 2)
        .attr('y', 16)
        .attr('text-anchor', 'middle')
        .attr('fill', THEME.text)
        .attr('font-size', '12px')
        .attr('font-family', 'sans-serif')
        .text(title);
    }

    const numRows = data.length;
    const numCols = data[0] ? data[0].length : 0;
    if (numRows === 0 || numCols === 0) return;

    // Flatten data to find extent
    const flatValues = data.flat();
    const [minVal, maxVal] = d3.extent(flatValues);

    // Color scale
    const colorScale = d3
      .scaleSequential()
      .domain([minVal, maxVal])
      .interpolator(d3.interpolateRgb(colorRange[0], colorRange[1]));

    // Scales
    const xScale = d3
      .scaleBand()
      .domain(xLabels.length ? xLabels : d3.range(numCols).map(String))
      .range([0, innerWidth])
      .padding(0.05);

    const yScale = d3
      .scaleBand()
      .domain(yLabels.length ? yLabels : d3.range(numRows).map(String))
      .range([0, innerHeight])
      .padding(0.05);

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).tickSize(0))
      .call((sel) => {
        sel.select('.domain').attr('stroke', THEME.axis);
        sel
          .selectAll('.tick text')
          .attr('fill', THEME.text)
          .attr('font-size', '9px')
          .attr('transform', xLabels.some((l) => l && l.length > 4) ? 'rotate(-35)' : null)
          .attr('text-anchor', xLabels.some((l) => l && l.length > 4) ? 'end' : 'middle');
      });

    g.append('g')
      .call(d3.axisLeft(yScale).tickSize(0))
      .call((sel) => {
        sel.select('.domain').attr('stroke', THEME.axis);
        sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '9px');
      });

    // Build cell data
    const cells = [];
    for (let row = 0; row < numRows; row++) {
      for (let col = 0; col < numCols; col++) {
        cells.push({
          row,
          col,
          value: data[row][col],
          xKey: xLabels[col] || String(col),
          yKey: yLabels[row] || String(row),
        });
      }
    }

    // Cells
    g.selectAll('.cell')
      .data(cells)
      .enter()
      .append('rect')
      .attr('x', (d) => xScale(d.xKey))
      .attr('y', (d) => yScale(d.yKey))
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('rx', 2)
      .attr('fill', (d) => colorScale(d.value))
      .attr('stroke', THEME.bg)
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseenter', function (event, d) {
        d3.select(this).attr('stroke', THEME.text).attr('stroke-width', 2);
        tooltip
          .style('display', 'block')
          .style('left', event.offsetX + 12 + 'px')
          .style('top', event.offsetY - 10 + 'px')
          .html(
            `<strong>${d.yKey}, ${d.xKey}</strong><br/>` +
              `Value: ${typeof d.value === 'number' ? d.value.toFixed(3) : d.value}`
          );
      })
      .on('mousemove', function (event) {
        tooltip
          .style('left', event.offsetX + 12 + 'px')
          .style('top', event.offsetY - 10 + 'px');
      })
      .on('mouseleave', function () {
        d3.select(this).attr('stroke', THEME.bg).attr('stroke-width', 1);
        tooltip.style('display', 'none');
      });
  }, [data, xLabels, yLabels, dimensions, colorRange, title]);

  if (typeof window === 'undefined') {
    return null;
  }

  return (
    <div ref={containerRef} style={{ width: '100%', maxWidth: propWidth, position: 'relative' }}>
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        style={{ background: THEME.bg, borderRadius: '6px', display: 'block' }}
      />
      <div
        ref={tooltipRef}
        style={{
          display: 'none',
          position: 'absolute',
          pointerEvents: 'none',
          background: 'rgba(10,10,15,0.92)',
          border: '1px solid #4a4a5a',
          borderRadius: '4px',
          padding: '6px 10px',
          color: '#a0a0b0',
          fontSize: '11px',
          fontFamily: 'sans-serif',
          whiteSpace: 'nowrap',
          zIndex: 10,
        }}
      />
    </div>
  );
};

export default HeatmapChart;

import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';

const THEME = {
  bg: '#0a0a0f',
  text: '#a0a0b0',
  axis: '#4a4a5a',
  colors: ['#58E6D9', '#B63E96', '#F59E0B', '#6366F1', '#10B981', '#EF4444'],
};

const ScatterChart = ({
  data = [],
  width: propWidth = 500,
  height: propHeight = 300,
  xLabel = '',
  yLabel = '',
  showLine = false,
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
    const margin = { top: title ? 30 : 15, right: 20, bottom: xLabel ? 50 : 35, left: yLabel ? 55 : 45 };
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

    // Scales
    const xExtent = d3.extent(data, (d) => d.x);
    const yExtent = d3.extent(data, (d) => d.y);

    const xPadding = (xExtent[1] - xExtent[0]) * 0.05 || 1;
    const yPadding = (yExtent[1] - yExtent[0]) * 0.05 || 1;

    const xScale = d3
      .scaleLinear()
      .domain([xExtent[0] - xPadding, xExtent[1] + xPadding])
      .range([0, innerWidth])
      .nice();

    const yScale = d3
      .scaleLinear()
      .domain([yExtent[0] - yPadding, yExtent[1] + yPadding])
      .range([innerHeight, 0])
      .nice();

    // Grid
    g.append('g')
      .selectAll('line')
      .data(yScale.ticks(5))
      .enter()
      .append('line')
      .attr('x1', 0)
      .attr('x2', innerWidth)
      .attr('y1', (d) => yScale(d))
      .attr('y2', (d) => yScale(d))
      .attr('stroke', THEME.axis)
      .attr('stroke-opacity', 0.3)
      .attr('stroke-dasharray', '3,3');

    g.append('g')
      .selectAll('line')
      .data(xScale.ticks(6))
      .enter()
      .append('line')
      .attr('x1', (d) => xScale(d))
      .attr('x2', (d) => xScale(d))
      .attr('y1', 0)
      .attr('y2', innerHeight)
      .attr('stroke', THEME.axis)
      .attr('stroke-opacity', 0.3)
      .attr('stroke-dasharray', '3,3');

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).ticks(6).tickSize(-4))
      .call((sel) => {
        sel.select('.domain').attr('stroke', THEME.axis);
        sel.selectAll('.tick line').attr('stroke', THEME.axis);
        sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '10px');
      });

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(5).tickSize(-4))
      .call((sel) => {
        sel.select('.domain').attr('stroke', THEME.axis);
        sel.selectAll('.tick line').attr('stroke', THEME.axis);
        sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '10px');
      });

    // Axis labels
    if (xLabel) {
      g.append('text')
        .attr('x', innerWidth / 2)
        .attr('y', innerHeight + 38)
        .attr('text-anchor', 'middle')
        .attr('fill', THEME.text)
        .attr('font-size', '11px')
        .attr('font-family', 'sans-serif')
        .text(xLabel);
    }

    if (yLabel) {
      g.append('text')
        .attr('x', -(innerHeight / 2))
        .attr('y', -42)
        .attr('transform', 'rotate(-90)')
        .attr('text-anchor', 'middle')
        .attr('fill', THEME.text)
        .attr('font-size', '11px')
        .attr('font-family', 'sans-serif')
        .text(yLabel);
    }

    // Reference / trend line
    if (showLine) {
      // Compute linear regression: y = mx + b
      const n = data.length;
      const sumX = d3.sum(data, (d) => d.x);
      const sumY = d3.sum(data, (d) => d.y);
      const sumXY = d3.sum(data, (d) => d.x * d.y);
      const sumX2 = d3.sum(data, (d) => d.x * d.x);
      const denom = n * sumX2 - sumX * sumX;

      if (Math.abs(denom) > 1e-10) {
        const m = (n * sumXY - sumX * sumY) / denom;
        const b = (sumY - m * sumX) / n;

        const xDomain = xScale.domain();
        const x1 = xDomain[0];
        const x2 = xDomain[1];

        g.append('line')
          .attr('x1', xScale(x1))
          .attr('y1', yScale(m * x1 + b))
          .attr('x2', xScale(x2))
          .attr('y2', yScale(m * x2 + b))
          .attr('stroke', THEME.axis)
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '6,4')
          .attr('opacity', 0.6);
      } else {
        // Fallback: diagonal reference line
        const domain = xScale.domain();
        g.append('line')
          .attr('x1', xScale(domain[0]))
          .attr('y1', yScale(domain[0]))
          .attr('x2', xScale(domain[1]))
          .attr('y2', yScale(domain[1]))
          .attr('stroke', THEME.axis)
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '6,4')
          .attr('opacity', 0.6);
      }
    }

    // Data points
    g.selectAll('.point')
      .data(data)
      .enter()
      .append('circle')
      .attr('cx', (d) => xScale(d.x))
      .attr('cy', (d) => yScale(d.y))
      .attr('r', (d) => d.size || 4)
      .attr('fill', (d, i) => d.color || THEME.colors[i % THEME.colors.length])
      .attr('stroke', THEME.bg)
      .attr('stroke-width', 1)
      .attr('opacity', 0.85)
      .style('cursor', 'pointer')
      .on('mouseenter', function (event, d) {
        const r = d.size || 4;
        d3.select(this).transition().duration(150).attr('r', r * 1.8).attr('opacity', 1);
        tooltip
          .style('display', 'block')
          .style('left', event.offsetX + 12 + 'px')
          .style('top', event.offsetY - 10 + 'px')
          .html(
            (d.label ? `<strong>${d.label}</strong><br/>` : '') +
              `x: ${typeof d.x === 'number' ? d.x.toFixed(3) : d.x}<br/>` +
              `y: ${typeof d.y === 'number' ? d.y.toFixed(3) : d.y}`
          );
      })
      .on('mousemove', function (event) {
        tooltip
          .style('left', event.offsetX + 12 + 'px')
          .style('top', event.offsetY - 10 + 'px');
      })
      .on('mouseleave', function (event, d) {
        const r = d.size || 4;
        d3.select(this).transition().duration(150).attr('r', r).attr('opacity', 0.85);
        tooltip.style('display', 'none');
      });
  }, [data, dimensions, xLabel, yLabel, showLine, title]);

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

export default ScatterChart;

import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';

const THEME = {
  bg: '#0a0a0f',
  text: '#a0a0b0',
  axis: '#4a4a5a',
  colors: ['#58E6D9', '#B63E96', '#F59E0B', '#6366F1', '#10B981', '#EF4444'],
};

const LineChart = ({
  data = [],
  width: propWidth = 500,
  height: propHeight = 300,
  xLabel = '',
  yLabel = '',
  logScale = false,
  title = '',
}) => {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
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

    // Compute domains from all series
    const allPoints = data.flatMap((s) => s.points || []);
    if (allPoints.length === 0) return;

    const xExtent = d3.extent(allPoints, (d) => d.x);
    const yExtent = d3.extent(allPoints, (d) => d.y);

    const xScale = d3.scaleLinear().domain(xExtent).range([0, innerWidth]).nice();

    let yScale;
    if (logScale) {
      const yMin = Math.max(yExtent[0], 1e-10);
      yScale = d3.scaleLog().domain([yMin, yExtent[1]]).range([innerHeight, 0]).nice();
    } else {
      yScale = d3.scaleLinear().domain(yExtent).range([innerHeight, 0]).nice();
    }

    // Grid lines
    g.append('g')
      .attr('class', 'grid')
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

    // Axes
    const xAxis = d3.axisBottom(xScale).ticks(6).tickSize(-4);
    const yAxis = d3.axisLeft(yScale).ticks(5).tickSize(-4);

    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .call((sel) => {
        sel.select('.domain').attr('stroke', THEME.axis);
        sel.selectAll('.tick line').attr('stroke', THEME.axis);
        sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '10px');
      });

    g.append('g')
      .call(yAxis)
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

    // Line generator
    const line = d3
      .line()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y))
      .curve(d3.curveMonotoneX);

    // Draw each series
    data.forEach((series, i) => {
      const color = series.color || THEME.colors[i % THEME.colors.length];
      const points = series.points || [];
      if (points.length === 0) return;

      // Line
      g.append('path')
        .datum(points)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('d', line);

      // Dots
      g.selectAll(`.dot-${i}`)
        .data(points)
        .enter()
        .append('circle')
        .attr('cx', (d) => xScale(d.x))
        .attr('cy', (d) => yScale(d.y))
        .attr('r', 3)
        .attr('fill', color)
        .attr('stroke', THEME.bg)
        .attr('stroke-width', 1)
        .style('cursor', 'pointer')
        .on('mouseenter', function () {
          d3.select(this).transition().duration(150).attr('r', 5);
        })
        .on('mouseleave', function () {
          d3.select(this).transition().duration(150).attr('r', 3);
        });
    });

    // Legend (if multiple series)
    if (data.length > 1) {
      const legend = g
        .append('g')
        .attr('transform', `translate(${innerWidth - 10}, 5)`);

      data.forEach((series, i) => {
        const color = series.color || THEME.colors[i % THEME.colors.length];
        const row = legend.append('g').attr('transform', `translate(0, ${i * 18})`);

        row
          .append('line')
          .attr('x1', -30)
          .attr('x2', -10)
          .attr('y1', 0)
          .attr('y2', 0)
          .attr('stroke', color)
          .attr('stroke-width', 2);

        row
          .append('circle')
          .attr('cx', -20)
          .attr('cy', 0)
          .attr('r', 2.5)
          .attr('fill', color);

        row
          .append('text')
          .attr('x', -5)
          .attr('y', 0)
          .attr('dy', '0.35em')
          .attr('text-anchor', 'end')
          .attr('fill', THEME.text)
          .attr('font-size', '9px')
          .attr('font-family', 'sans-serif')
          .text(series.label || `Series ${i + 1}`);
      });
    }
  }, [data, dimensions, logScale, xLabel, yLabel, title]);

  if (typeof window === 'undefined') {
    return null;
  }

  return (
    <div ref={containerRef} style={{ width: '100%', maxWidth: propWidth }}>
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        style={{ background: THEME.bg, borderRadius: '6px', display: 'block' }}
      />
    </div>
  );
};

export default LineChart;

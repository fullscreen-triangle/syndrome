import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';

const THEME = {
  bg: '#0a0a0f',
  text: '#a0a0b0',
  axis: '#4a4a5a',
  colors: ['#58E6D9', '#B63E96', '#F59E0B', '#6366F1', '#10B981', '#EF4444'],
};

const BarChart = ({
  data = [],
  width: propWidth = 500,
  height: propHeight = 300,
  yLabel = '',
  horizontal = false,
  grouped = null,
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
    if (!svgRef.current) return;

    const isGrouped = grouped && grouped.length > 0;
    const chartData = isGrouped ? grouped : data;
    if (!chartData || chartData.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;
    const margin = {
      top: title ? 30 : 15,
      right: 15,
      bottom: horizontal ? 35 : 50,
      left: horizontal ? 80 : (yLabel ? 55 : 45),
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

    // Rounded top corners helper
    const roundedBar = (x, y, w, h, r) => {
      if (h <= 0) return '';
      r = Math.min(r, w / 2, h);
      return `M${x},${y + h}
              v${-(h - r)}
              a${r},${r} 0 0 1 ${r},${-r}
              h${w - 2 * r}
              a${r},${r} 0 0 1 ${r},${r}
              v${h - r}
              Z`;
    };

    const roundedBarHorizontal = (x, y, w, h, r) => {
      if (w <= 0) return '';
      r = Math.min(r, h / 2, w);
      return `M${x},${y}
              h${w - r}
              a${r},${r} 0 0 1 ${r},${r}
              v${h - 2 * r}
              a${r},${r} 0 0 1 ${-r},${r}
              h${-(w - r)}
              Z`;
    };

    if (isGrouped) {
      // Grouped bar chart
      const labels = grouped.map((d) => d.label);
      const allKeys = [...new Set(grouped.flatMap((d) => d.values.map((v) => v.key)))];
      const maxVal = d3.max(grouped, (d) => d3.max(d.values, (v) => v.value)) || 0;

      const x0 = d3.scaleBand().domain(labels).range([0, innerWidth]).paddingInner(0.2).paddingOuter(0.1);
      const x1 = d3.scaleBand().domain(allKeys).range([0, x0.bandwidth()]).padding(0.05);
      const y = d3.scaleLinear().domain([0, maxVal]).range([innerHeight, 0]).nice();

      // Grid
      g.append('g')
        .selectAll('line')
        .data(y.ticks(5))
        .enter()
        .append('line')
        .attr('x1', 0)
        .attr('x2', innerWidth)
        .attr('y1', (d) => y(d))
        .attr('y2', (d) => y(d))
        .attr('stroke', THEME.axis)
        .attr('stroke-opacity', 0.3)
        .attr('stroke-dasharray', '3,3');

      // Axes
      g.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x0).tickSize(0))
        .call((sel) => {
          sel.select('.domain').attr('stroke', THEME.axis);
          sel
            .selectAll('.tick text')
            .attr('fill', THEME.text)
            .attr('font-size', '9px')
            .attr('transform', 'rotate(-25)')
            .attr('text-anchor', 'end');
        });

      g.append('g')
        .call(d3.axisLeft(y).ticks(5).tickSize(-4))
        .call((sel) => {
          sel.select('.domain').attr('stroke', THEME.axis);
          sel.selectAll('.tick line').attr('stroke', THEME.axis);
          sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '10px');
        });

      // Bars
      grouped.forEach((group) => {
        const groupG = g.append('g').attr('transform', `translate(${x0(group.label)},0)`);

        group.values.forEach((v, vi) => {
          const barX = x1(v.key);
          const barW = x1.bandwidth();
          const barH = innerHeight - y(v.value);
          const barY = y(v.value);
          const color = v.color || THEME.colors[vi % THEME.colors.length];

          groupG
            .append('path')
            .attr('d', roundedBar(barX, barY, barW, barH, 3))
            .attr('fill', color)
            .style('cursor', 'pointer')
            .on('mouseenter', function () {
              d3.select(this).transition().duration(150).attr('opacity', 0.7);
            })
            .on('mouseleave', function () {
              d3.select(this).transition().duration(150).attr('opacity', 1);
            });
        });
      });

      // Legend for grouped
      const legend = g.append('g').attr('transform', `translate(${innerWidth - 10}, 5)`);
      const seenKeys = new Map();
      grouped.forEach((group) => {
        group.values.forEach((v, vi) => {
          if (!seenKeys.has(v.key)) {
            seenKeys.set(v.key, v.color || THEME.colors[vi % THEME.colors.length]);
          }
        });
      });
      let li = 0;
      seenKeys.forEach((color, key) => {
        const row = legend.append('g').attr('transform', `translate(0, ${li * 16})`);
        row.append('rect').attr('x', -40).attr('y', -5).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', color);
        row.append('text').attr('x', -26).attr('y', 0).attr('dy', '0.35em').attr('fill', THEME.text).attr('font-size', '9px').attr('font-family', 'sans-serif').text(key);
        li++;
      });
    } else if (horizontal) {
      // Horizontal bar chart
      const labels = data.map((d) => d.label);
      const maxVal = d3.max(data, (d) => d.value) || 0;

      const y = d3.scaleBand().domain(labels).range([0, innerHeight]).padding(0.25);
      const x = d3.scaleLinear().domain([0, maxVal]).range([0, innerWidth]).nice();

      // Grid
      g.append('g')
        .selectAll('line')
        .data(x.ticks(5))
        .enter()
        .append('line')
        .attr('x1', (d) => x(d))
        .attr('x2', (d) => x(d))
        .attr('y1', 0)
        .attr('y2', innerHeight)
        .attr('stroke', THEME.axis)
        .attr('stroke-opacity', 0.3)
        .attr('stroke-dasharray', '3,3');

      // Axes
      g.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).ticks(5).tickSize(-4))
        .call((sel) => {
          sel.select('.domain').attr('stroke', THEME.axis);
          sel.selectAll('.tick line').attr('stroke', THEME.axis);
          sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '10px');
        });

      g.append('g')
        .call(d3.axisLeft(y).tickSize(0))
        .call((sel) => {
          sel.select('.domain').attr('stroke', THEME.axis);
          sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '10px');
        });

      // Bars
      g.selectAll('.bar')
        .data(data)
        .enter()
        .append('path')
        .attr('d', (d) => roundedBarHorizontal(0, y(d.label), x(d.value), y.bandwidth(), 3))
        .attr('fill', (d, i) => d.color || THEME.colors[i % THEME.colors.length])
        .style('cursor', 'pointer')
        .on('mouseenter', function () {
          d3.select(this).transition().duration(150).attr('opacity', 0.7);
        })
        .on('mouseleave', function () {
          d3.select(this).transition().duration(150).attr('opacity', 1);
        });
    } else {
      // Vertical bar chart
      const labels = data.map((d) => d.label);
      const maxVal = d3.max(data, (d) => d.value) || 0;

      const x = d3.scaleBand().domain(labels).range([0, innerWidth]).padding(0.25);
      const y = d3.scaleLinear().domain([0, maxVal]).range([innerHeight, 0]).nice();

      // Grid
      g.append('g')
        .selectAll('line')
        .data(y.ticks(5))
        .enter()
        .append('line')
        .attr('x1', 0)
        .attr('x2', innerWidth)
        .attr('y1', (d) => y(d))
        .attr('y2', (d) => y(d))
        .attr('stroke', THEME.axis)
        .attr('stroke-opacity', 0.3)
        .attr('stroke-dasharray', '3,3');

      // Axes
      g.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).tickSize(0))
        .call((sel) => {
          sel.select('.domain').attr('stroke', THEME.axis);
          sel
            .selectAll('.tick text')
            .attr('fill', THEME.text)
            .attr('font-size', '9px')
            .attr('transform', labels.some((l) => l.length > 6) ? 'rotate(-25)' : null)
            .attr('text-anchor', labels.some((l) => l.length > 6) ? 'end' : 'middle');
        });

      g.append('g')
        .call(d3.axisLeft(y).ticks(5).tickSize(-4))
        .call((sel) => {
          sel.select('.domain').attr('stroke', THEME.axis);
          sel.selectAll('.tick line').attr('stroke', THEME.axis);
          sel.selectAll('.tick text').attr('fill', THEME.text).attr('font-size', '10px');
        });

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

      // Bars
      g.selectAll('.bar')
        .data(data)
        .enter()
        .append('path')
        .attr('d', (d) => {
          const barX = x(d.label);
          const barW = x.bandwidth();
          const barH = innerHeight - y(d.value);
          const barY = y(d.value);
          return roundedBar(barX, barY, barW, barH, 3);
        })
        .attr('fill', (d, i) => d.color || THEME.colors[i % THEME.colors.length])
        .style('cursor', 'pointer')
        .on('mouseenter', function () {
          d3.select(this).transition().duration(150).attr('opacity', 0.7);
        })
        .on('mouseleave', function () {
          d3.select(this).transition().duration(150).attr('opacity', 1);
        });
    }
  }, [data, grouped, dimensions, horizontal, yLabel, title]);

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

export default BarChart;

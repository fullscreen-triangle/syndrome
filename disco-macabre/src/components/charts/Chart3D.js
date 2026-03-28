import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';

const THEME = {
  bg: '#0a0a0f',
  text: '#a0a0b0',
  axis: '#4a4a5a',
  colors: ['#58E6D9', '#B63E96', '#F59E0B', '#6366F1', '#10B981', '#EF4444'],
};

// Lazy-load Three.js components to avoid SSR issues
const Canvas = dynamic(() => import('@react-three/fiber').then((mod) => mod.Canvas), { ssr: false });
const OrbitControls = dynamic(
  () => import('@react-three/drei').then((mod) => mod.OrbitControls),
  { ssr: false }
);

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  return [r, g, b];
}

// Axis line component
function AxisLine({ start, end, color }) {
  const positions = useMemo(
    () => new Float32Array([...start, ...end]),
    [start, end]
  );

  return (
    <line>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={2}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial color={color} />
    </line>
  );
}

// Axis label using drei Text
function AxisLabel({ position, text, color }) {
  // Lazy import Text from drei does not work easily, so we use a simple sprite
  return (
    <sprite position={position} scale={[0.6, 0.2, 1]}>
      <spriteMaterial color={color} opacity={0.8} transparent />
    </sprite>
  );
}

// Grid helper on XZ plane
function SubtleGrid({ size = 4, divisions = 8 }) {
  return <gridHelper args={[size, divisions, THEME.axis, THEME.axis]} position={[0, -2, 0]} />;
}

// Scatter point
function ScatterPoint({ position, color, size = 0.06 }) {
  const [r, g, b] = hexToRgb(color);
  return (
    <mesh position={position}>
      <sphereGeometry args={[size, 12, 12]} />
      <meshStandardMaterial color={[r, g, b]} emissive={[r * 0.3, g * 0.3, b * 0.3]} />
    </mesh>
  );
}

// Surface mesh built from data points via Delaunay-like grid approach
function SurfaceMesh({ data }) {
  const { positions, indices, colors } = useMemo(() => {
    if (!data || data.length < 3) return { positions: null, indices: null, colors: null };

    // Sort data by x then z for grid-based triangulation
    const sorted = [...data].sort((a, b) => a.x - b.x || a.z - b.z);

    // Get unique x and z values
    const xVals = [...new Set(sorted.map((d) => d.x))].sort((a, b) => a - b);
    const zVals = [...new Set(sorted.map((d) => d.z))].sort((a, b) => a - b);

    if (xVals.length < 2 || zVals.length < 2) return { positions: null, indices: null, colors: null };

    // Build lookup
    const lookup = new Map();
    sorted.forEach((d) => {
      lookup.set(`${d.x},${d.z}`, d);
    });

    // Normalize to [-2, 2] range
    const xExt = [xVals[0], xVals[xVals.length - 1]];
    const zExt = [zVals[0], zVals[zVals.length - 1]];
    const yExt = [
      Math.min(...sorted.map((d) => d.y)),
      Math.max(...sorted.map((d) => d.y)),
    ];
    const norm = (v, ext) => {
      const range = ext[1] - ext[0] || 1;
      return ((v - ext[0]) / range) * 4 - 2;
    };

    const posArr = [];
    const colArr = [];
    const idxMap = new Map();
    let idx = 0;

    xVals.forEach((x) => {
      zVals.forEach((z) => {
        const key = `${x},${z}`;
        const d = lookup.get(key);
        if (d) {
          posArr.push(norm(d.x, xExt), norm(d.y, yExt), norm(d.z, zExt));
          const [r, g, b] = hexToRgb(d.color || THEME.colors[0]);
          colArr.push(r, g, b);
          idxMap.set(key, idx++);
        }
      });
    });

    // Build triangles
    const triIndices = [];
    for (let i = 0; i < xVals.length - 1; i++) {
      for (let j = 0; j < zVals.length - 1; j++) {
        const a = idxMap.get(`${xVals[i]},${zVals[j]}`);
        const b = idxMap.get(`${xVals[i + 1]},${zVals[j]}`);
        const c = idxMap.get(`${xVals[i]},${zVals[j + 1]}`);
        const d = idxMap.get(`${xVals[i + 1]},${zVals[j + 1]}`);

        if (a !== undefined && b !== undefined && c !== undefined) {
          triIndices.push(a, b, c);
        }
        if (b !== undefined && d !== undefined && c !== undefined) {
          triIndices.push(b, d, c);
        }
      }
    }

    return {
      positions: new Float32Array(posArr),
      indices: new Uint16Array(triIndices),
      colors: new Float32Array(colArr),
    };
  }, [data]);

  if (!positions || !indices) return null;

  return (
    <mesh>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={positions.length / 3} array={positions} itemSize={3} />
        <bufferAttribute attach="attributes-color" count={colors.length / 3} array={colors} itemSize={3} />
        <bufferAttribute attach="index" count={indices.length} array={indices} itemSize={1} />
      </bufferGeometry>
      <meshStandardMaterial vertexColors side={2} transparent opacity={0.85} />
    </mesh>
  );
}

// Scene content
function SceneContent({ data, mode }) {
  const normalizedData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const xs = data.map((d) => d.x);
    const ys = data.map((d) => d.y);
    const zs = data.map((d) => d.z);

    const xExt = [Math.min(...xs), Math.max(...xs)];
    const yExt = [Math.min(...ys), Math.max(...ys)];
    const zExt = [Math.min(...zs), Math.max(...zs)];

    const norm = (v, ext) => {
      const range = ext[1] - ext[0] || 1;
      return ((v - ext[0]) / range) * 4 - 2;
    };

    return data.map((d, i) => ({
      ...d,
      nx: norm(d.x, xExt),
      ny: norm(d.y, yExt),
      nz: norm(d.z, zExt),
      color: d.color || THEME.colors[i % THEME.colors.length],
    }));
  }, [data]);

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[5, 5, 5]} intensity={0.8} />
      <pointLight position={[-5, -5, -5]} intensity={0.3} />
      <OrbitControls enableDamping dampingFactor={0.1} />

      {/* Axes */}
      <AxisLine start={[-2.2, -2, 0]} end={[2.2, -2, 0]} color={THEME.axis} />
      <AxisLine start={[0, -2.2, 0]} end={[0, 2.2, 0]} color={THEME.axis} />
      <AxisLine start={[0, -2, -2.2]} end={[0, -2, 2.2]} color={THEME.axis} />

      {/* Grid */}
      <SubtleGrid />

      {/* Data */}
      {mode === 'surface' ? (
        <SurfaceMesh data={data} />
      ) : (
        normalizedData.map((d, i) => (
          <ScatterPoint key={i} position={[d.nx, d.ny, d.nz]} color={d.color} />
        ))
      )}
    </>
  );
}

// Inner component that uses Three.js -- only rendered client-side
function Chart3DInner({
  data = [],
  width = 500,
  height = 400,
  xLabel = '',
  yLabel = '',
  zLabel = '',
  mode = 'scatter',
  title = '',
}) {
  return (
    <div style={{ width, height, position: 'relative' }}>
      {title && (
        <div
          style={{
            position: 'absolute',
            top: 4,
            left: 0,
            right: 0,
            textAlign: 'center',
            color: THEME.text,
            fontSize: '12px',
            fontFamily: 'sans-serif',
            zIndex: 1,
            pointerEvents: 'none',
          }}
        >
          {title}
        </div>
      )}
      <Canvas
        camera={{ position: [4, 3, 4], fov: 50 }}
        style={{ background: THEME.bg, borderRadius: '6px' }}
      >
        <SceneContent data={data} mode={mode} />
      </Canvas>
      {/* Axis labels overlaid */}
      <div
        style={{
          position: 'absolute',
          bottom: 8,
          left: '50%',
          transform: 'translateX(-50%)',
          color: THEME.text,
          fontSize: '10px',
          fontFamily: 'sans-serif',
          pointerEvents: 'none',
          opacity: 0.7,
        }}
      >
        {[xLabel && `X: ${xLabel}`, yLabel && `Y: ${yLabel}`, zLabel && `Z: ${zLabel}`]
          .filter(Boolean)
          .join('  |  ')}
      </div>
    </div>
  );
}

// Export a dynamic wrapper that disables SSR
const Chart3D = dynamic(
  () =>
    Promise.resolve(Chart3DInner),
  { ssr: false }
);

export default Chart3D;

import React, { useRef, useMemo, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import * as THREE from "three";

/* ---------- Skeleton Model ---------- */
function SkeletonModel() {
  const group = useRef();
  const { scene } = useGLTF("/model/skeleton_comp-transformed.glb");

  // Apply wireframe / semi-transparent scientific material
  useMemo(() => {
    scene.traverse((child) => {
      if (child.isMesh) {
        child.material = new THREE.MeshPhongMaterial({
          color: new THREE.Color("#c0d8e8"),
          wireframe: true,
          transparent: true,
          opacity: 0.35,
          emissive: new THREE.Color("#58E6D9"),
          emissiveIntensity: 0.08,
        });
      }
    });
  }, [scene]);

  useFrame((_, delta) => {
    if (group.current) {
      group.current.rotation.y += delta * 0.12;
    }
  });

  return (
    <group ref={group} scale={1.6} position={[0, -1.8, 0]}>
      <primitive object={scene} />
    </group>
  );
}

/* ---------- Particle Network ---------- */
function ParticleNetwork({ count = 250, radius = 6 }) {
  const meshRef = useRef();
  const lineRef = useRef();

  // Generate particle positions once
  const { positions, connections } = useMemo(() => {
    const pos = [];
    for (let i = 0; i < count; i++) {
      pos.push(
        (Math.random() - 0.5) * radius * 2,
        (Math.random() - 0.5) * radius * 2,
        (Math.random() - 0.5) * radius * 2
      );
    }

    // Connect nearby particles (thin lines)
    const threshold = radius * 0.45;
    const lineVerts = [];
    for (let i = 0; i < count; i++) {
      for (let j = i + 1; j < count; j++) {
        const dx = pos[i * 3] - pos[j * 3];
        const dy = pos[i * 3 + 1] - pos[j * 3 + 1];
        const dz = pos[i * 3 + 2] - pos[j * 3 + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < threshold) {
          lineVerts.push(
            pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2],
            pos[j * 3], pos[j * 3 + 1], pos[j * 3 + 2]
          );
        }
      }
    }

    return {
      positions: new Float32Array(pos),
      connections: new Float32Array(lineVerts),
    };
  }, [count, radius]);

  // Gentle drift
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.02;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.015) * 0.1;
    }
    if (lineRef.current) {
      lineRef.current.rotation.y = state.clock.elapsedTime * 0.02;
      lineRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.015) * 0.1;
    }
  });

  return (
    <>
      {/* Particle spheres via instanced points */}
      <points ref={meshRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            array={positions}
            count={positions.length / 3}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.04}
          color="#58E6D9"
          transparent
          opacity={0.7}
          sizeAttenuation
        />
      </points>

      {/* Connection lines */}
      {connections.length > 0 && (
        <lineSegments ref={lineRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              array={connections}
              count={connections.length / 3}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial
            color="#58E6D9"
            transparent
            opacity={0.08}
          />
        </lineSegments>
      )}
    </>
  );
}

/* ---------- Lighting Rig ---------- */
function Lighting() {
  return (
    <>
      <ambientLight intensity={0.15} color="#ffffff" />
      <pointLight position={[5, 5, 5]} intensity={0.8} color="#58E6D9" distance={20} />
      <pointLight position={[-5, -3, -5]} intensity={0.5} color="#B63E96" distance={20} />
      <pointLight position={[0, 4, -3]} intensity={0.3} color="#58E6D9" distance={15} />
      <spotLight
        position={[0, 8, 0]}
        angle={0.5}
        penumbra={1}
        intensity={0.4}
        color="#B63E96"
      />
    </>
  );
}

/* ---------- Loader Fallback ---------- */
function LoadingFallback() {
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#58E6D9",
        fontFamily: "var(--font-mont), sans-serif",
        fontSize: "0.875rem",
        letterSpacing: "0.1em",
        background: "#0a0a0f",
      }}
    >
      Loading...
    </div>
  );
}

/* ---------- Scene (inner) ---------- */
function Scene() {
  return (
    <>
      <Lighting />
      <fog attach="fog" args={["#0a0a0f", 5, 18]} />
      <SkeletonModel />
      <ParticleNetwork />
      <OrbitControls
        autoRotate
        autoRotateSpeed={0.4}
        enableZoom={false}
        enablePan={false}
        maxPolarAngle={Math.PI * 0.65}
        minPolarAngle={Math.PI * 0.35}
      />
    </>
  );
}

/* ---------- Exported Component ---------- */
export default function HeroSceneInner() {
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Suspense fallback={<LoadingFallback />}>
        <Canvas
          camera={{ position: [0, 0, 6], fov: 50 }}
          style={{ background: "#0a0a0f" }}
          gl={{ antialias: true, alpha: false }}
          dpr={[1, 1.5]}
        >
          <Scene />
        </Canvas>
      </Suspense>
    </div>
  );
}

// Pre-load the model
useGLTF.preload("/model/skeleton_comp-transformed.glb");

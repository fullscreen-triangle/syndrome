import Head from "next/head";
import Layout from "@/components/Layout";
import TransitionEffect from "@/components/TransitionEffect";
import AnimatedText from "@/components/AnimatedText";
import { motion } from "framer-motion";
import { LineChart, BarChart, HeatmapChart, ScatterChart, Chart3D } from "@/components/charts";

const sectionVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

function ChartCard({ title, children }) {
  return (
    <div className="bg-[#12121a] rounded-lg p-4 border border-[#58E6D9]/10">
      {title && (
        <h4 className="text-sm text-[#a0a0b0] mb-2 font-medium">{title}</h4>
      )}
      <div className="w-full flex justify-center">{children}</div>
    </div>
  );
}

export default function Equations({
  entropyProxyByDepth,
  entropyComparison,
  sEntropyPoints3D,
  distanceScatter,
  precisionScaling,
  addressResolutionBars,
  trajectoryInterpolation,
  trajectoryEntropyBars,
}) {
  return (
    <>
      <Head>
        <title>Disease Computing Framework | Equations of State</title>
        <meta
          name="description"
          content="Thermodynamic validation and trajectory computation in the Disease Computing Framework."
        />
      </Head>

      <TransitionEffect />

      <main className="mb-16 flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Equations of State"
            className="mb-16 !text-8xl !leading-tight lg:!text-7xl sm:mb-8 sm:!text-6xl xs:!text-4xl"
          />

          {/* Section 1: Entropy Bounds */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Entropy Bounds
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              The partition-thermodynamic connection shows entropy increasing
              monotonically with partition depth n. The entropy proxy
              S&nbsp;=&nbsp;k<sub>B</sub>&middot;M&middot;ln(n) encodes the
              information capacity of each depth level through
              C(n)&nbsp;=&nbsp;2n&sup2;.
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="Entropy Proxy vs Partition Depth">
                <LineChart
                  data={[
                    {
                      label: "S(n)",
                      color: "#58E6D9",
                      points: entropyProxyByDepth,
                    },
                  ]}
                  width={500}
                  height={300}
                  xLabel="Partition Depth n"
                  yLabel="Entropy Proxy"
                  title="Entropy Growth with Depth"
                />
              </ChartCard>

              <ChartCard title="Entropy Distribution Comparison">
                <BarChart
                  data={entropyComparison}
                  width={500}
                  height={300}
                  yLabel="Entropy S"
                  title="Entropy Across Distributions"
                />
              </ChartCard>
            </div>
          </motion.div>

          {/* Section 2: S-Entropy Space */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              S-Entropy Space
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              The S-entropy space is the unit cube [0,1]&sup3; with coordinates
              (S<sub>k</sub>, S<sub>t</sub>, S<sub>e</sub>). The categorical
              distance metric d satisfies non-negativity, identity of
              indiscernibles, symmetry, and the triangle inequality.
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="S-Entropy Points in [0,1]^3">
                <Chart3D
                  data={sEntropyPoints3D}
                  width={500}
                  height={300}
                  xLabel="S_k"
                  yLabel="S_t"
                  zLabel="S_e"
                  mode="scatter"
                  title="Valid S-Entropy Coordinates"
                />
              </ChartCard>

              <ChartCard title="Distance Metrics">
                <ScatterChart
                  data={distanceScatter}
                  width={500}
                  height={300}
                  xLabel="Point Pair"
                  yLabel="Distance d"
                  title="Pairwise S-Entropy Distances"
                />
              </ChartCard>
            </div>
          </motion.div>

          {/* Section 3: Address Resolution */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Address Resolution
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              Ternary addresses resolve positions with exponentially increasing
              precision: precision(d)&nbsp;=&nbsp;1/3<sup>d</sup>. Each
              additional digit of the address triples the resolution, enabling
              arbitrarily fine localization within the state space.
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="Precision Scaling (Log Scale)">
                <LineChart
                  data={[
                    {
                      label: "1/3^d",
                      color: "#F59E0B",
                      points: precisionScaling,
                    },
                  ]}
                  width={500}
                  height={300}
                  xLabel="Depth d"
                  yLabel="Precision (log)"
                  title="Exponential Precision Refinement"
                />
              </ChartCard>

              <ChartCard title="Address Resolution Values">
                <BarChart
                  data={addressResolutionBars}
                  width={500}
                  height={300}
                  yLabel="Resolved Value"
                  title="Ternary Address Resolution"
                />
              </ChartCard>
            </div>
          </motion.div>

          {/* Section 4: Trajectory Computation */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Trajectory Computation
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              Trajectories through S-entropy space are computed via linear
              interpolation with boundary clamping. The arc length measures the
              total distance traversed, while entropy estimation distinguishes
              ordered from random trajectories.
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="Trajectory Interpolation (S_k Component)">
                <LineChart
                  data={[
                    {
                      label: "S_k(t)",
                      color: "#58E6D9",
                      points: trajectoryInterpolation,
                    },
                  ]}
                  width={500}
                  height={300}
                  xLabel="Time t"
                  yLabel="S_k"
                  title="Linear Interpolation in S-Entropy Space"
                />
              </ChartCard>

              <ChartCard title="Ordered vs Random Trajectory Entropy">
                <BarChart
                  data={trajectoryEntropyBars}
                  width={500}
                  height={300}
                  yLabel="Trajectory Entropy"
                  title="Entropy Ordering Validation"
                />
              </ChartCard>
            </div>
          </motion.div>
        </Layout>
      </main>
    </>
  );
}

export async function getStaticProps() {
  const fs = require("fs");
  const path = require("path");

  const readJSON = (filename) => {
    const filePath = path.join(process.cwd(), "public/data", filename);
    return JSON.parse(fs.readFileSync(filePath, "utf-8"));
  };

  const thermoResults = readJSON("thermodynamic_results.json");
  const trajectoryResults = readJSON("trajectory_results.json");

  // --- Chart 1: Entropy proxy vs partition depth ---
  const partitionConnection = thermoResults.results.find(
    (r) => r.name === "partition_thermodynamic_connection"
  );
  const entropyProxyByDepth = partitionConnection.actual.test_cases.map(
    (tc) => ({
      x: tc.n,
      y: parseFloat(tc.entropy_proxy.toFixed(3)),
    })
  );

  // --- Chart 2: Entropy comparison bars ---
  const entropyComparison = [
    {
      label: "Uniform (n=10)",
      value: thermoResults.results.find(
        (r) => r.name === "entropy_uniform_distribution"
      ).actual,
      color: "#58E6D9",
    },
    {
      label: "Binary Fair Coin",
      value: thermoResults.results.find(
        (r) => r.name === "entropy_binary_distribution"
      ).actual,
      color: "#6366F1",
    },
    {
      label: "Intermediate (0.9/0.1)",
      value: thermoResults.results.find(
        (r) => r.name === "entropy_intermediate"
      ).actual,
      color: "#F59E0B",
    },
    {
      label: "Delta",
      value: Math.abs(
        thermoResults.results.find(
          (r) => r.name === "entropy_delta_distribution"
        ).actual
      ),
      color: "#EF4444",
    },
  ];

  // --- Chart 3: S-entropy 3D points ---
  const boundsTest = thermoResults.results.find(
    (r) => r.name === "s_entropy_bounds"
  );
  const validCoords = boundsTest.actual.filter(
    (pt) => pt.status === "valid"
  );
  // Include additional points from normalization and aggregations
  const normTest = thermoResults.results.find(
    (r) => r.name === "s_entropy_normalization"
  );
  const aggTest = thermoResults.results.find(
    (r) => r.name === "entropy_aggregations"
  );

  const sEntropyPoints3D = [
    ...validCoords.map((pt) => ({
      x: pt.coords[0],
      y: pt.coords[1],
      z: pt.coords[2],
      color: "#58E6D9",
    })),
    {
      x: normTest.actual[0],
      y: normTest.actual[1],
      z: normTest.actual[2],
      color: "#F59E0B",
    },
    ...aggTest.actual.map((pt) => ({
      x: pt.point[0],
      y: pt.point[1],
      z: pt.point[2],
      color: "#B63E96",
    })),
  ];

  // --- Chart 4: Distance scatter ---
  const distNonNeg = thermoResults.results.find(
    (r) => r.name === "s_entropy_distance_non_negative"
  );
  const distSym = thermoResults.results.find(
    (r) => r.name === "s_entropy_distance_symmetry"
  );
  const distTri = thermoResults.results.find(
    (r) => r.name === "s_entropy_distance_triangle"
  );

  const distanceScatter = [
    { x: 1, y: parseFloat(distNonNeg.actual.toFixed(3)), color: "#58E6D9" },
    { x: 2, y: parseFloat(distSym.actual.d12.toFixed(3)), color: "#6366F1" },
    { x: 3, y: parseFloat(distSym.actual.d21.toFixed(3)), color: "#6366F1" },
    { x: 4, y: parseFloat(distTri.actual.d12.toFixed(3)), color: "#F59E0B" },
    { x: 5, y: parseFloat(distTri.actual.d23.toFixed(3)), color: "#F59E0B" },
    { x: 6, y: parseFloat(distTri.actual.d13.toFixed(3)), color: "#B63E96" },
  ];

  // --- Chart 5: Precision scaling ---
  const precisionTest = trajectoryResults.results.find(
    (r) => r.name === "address_precision_scaling"
  );
  const precisionScaling = precisionTest.actual.map((pt) => ({
    x: pt.depth,
    y: parseFloat(pt.actual.toFixed(6)),
  }));

  // --- Chart 6: Address resolution bars ---
  const addrEmpty = trajectoryResults.results.find(
    (r) => r.name === "address_resolution_empty"
  );
  const addrZero = trajectoryResults.results.find(
    (r) => r.name === "address_resolution_zero"
  );
  const addrTwo = trajectoryResults.results.find(
    (r) => r.name === "address_resolution_two"
  );
  const addrMulti = trajectoryResults.results.find(
    (r) => r.name === "address_resolution_multi_digit"
  );
  const addrRange = trajectoryResults.results.find(
    (r) => r.name === "address_resolution_range_scaling"
  );

  const addressResolutionBars = [
    {
      label: "[] (empty)",
      value: parseFloat(addrEmpty.actual.toFixed(3)),
      color: "#58E6D9",
    },
    {
      label: "[0]",
      value: parseFloat(addrZero.actual.toFixed(3)),
      color: "#6366F1",
    },
    {
      label: "[2]",
      value: parseFloat(addrTwo.actual.toFixed(3)),
      color: "#F59E0B",
    },
    {
      label: "[1,1]",
      value: parseFloat(addrMulti.actual.toFixed(3)),
      color: "#B63E96",
    },
    {
      label: "[1] in [10,20]",
      value: parseFloat(addrRange.actual.toFixed(3)),
      color: "#10B981",
    },
  ];

  // --- Chart 7: Trajectory interpolation ---
  const interpTest = thermoResults.results.find(
    (r) => r.name === "s_entropy_interpolation"
  );
  const trajectoryInterpolation = interpTest.actual.map((pt) => ({
    x: pt.t,
    y: pt.actual[0],
  }));

  // --- Chart 8: Ordered vs random trajectory entropy ---
  const orderingTest = thermoResults.results.find(
    (r) => r.name === "entropy_estimation_ordering"
  );
  const trajectoryEntropyBars = [
    {
      label: "Ordered",
      value: parseFloat(orderingTest.actual.ordered_entropy.toFixed(3)),
      color: "#10B981",
    },
    {
      label: "Random",
      value: parseFloat(orderingTest.actual.random_entropy.toFixed(3)),
      color: "#EF4444",
    },
  ];

  return {
    props: {
      entropyProxyByDepth,
      entropyComparison,
      sEntropyPoints3D,
      distanceScatter,
      precisionScaling,
      addressResolutionBars,
      trajectoryInterpolation,
      trajectoryEntropyBars,
    },
  };
}

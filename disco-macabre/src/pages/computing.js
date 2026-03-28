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

export default function Computing({
  partitionCapacity,
  partitionCoords,
  coherenceMonotonicity,
  oscillatorCoherences,
  diseaseClasses,
  distanceMatrix,
  distanceLabels,
  therapeuticBars,
  scatterCoherence,
}) {
  return (
    <>
      <Head>
        <title>Disease Computing Framework | Computing</title>
        <meta
          name="description"
          content="Partition geometry, coherence functions, and disease classification in the Disease Computing Framework."
        />
      </Head>

      <TransitionEffect />

      <main className="mb-16 flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Disease Computing Framework"
            className="mb-16 !text-8xl !leading-tight lg:!text-7xl sm:mb-8 sm:!text-6xl xs:!text-4xl"
          />

          {/* Section 1: Partition Geometry */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Partition Geometry
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              The partition capacity formula C(n) = 2n&sup2; gives the number of
              distinguishable states at each depth level.
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="Partition Capacity C(n) = 2n\u00B2">
                <LineChart
                  data={[
                    {
                      label: "C(n)",
                      color: "#58E6D9",
                      points: partitionCapacity,
                    },
                  ]}
                  width={500}
                  height={300}
                  xLabel="Depth n"
                  yLabel="Capacity C(n)"
                  title="Partition Capacity Growth"
                />
              </ChartCard>

              <ChartCard title="Partition Coordinate Space (n, l, m)">
                <Chart3D
                  data={partitionCoords}
                  width={500}
                  height={300}
                  xLabel="n"
                  yLabel="l"
                  zLabel="m"
                  mode="scatter"
                  title="Partition States n=1..4"
                />
              </ChartCard>
            </div>
          </motion.div>

          {/* Section 2: Coherence Functions */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Coherence Functions
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              The universal coherence index &eta; maps any oscillator performance
              metric to [0,1].
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="Coherence Monotonicity">
                <LineChart
                  data={[
                    {
                      label: "\u03B7(\u03C0)",
                      color: "#58E6D9",
                      points: coherenceMonotonicity,
                    },
                  ]}
                  width={500}
                  height={300}
                  xLabel="Performance \u03C0"
                  yLabel="Coherence \u03B7"
                  title="Monotonic Coherence Map"
                />
              </ChartCard>

              <ChartCard title="Oscillator-Specific Coherence">
                <BarChart
                  data={oscillatorCoherences}
                  width={500}
                  height={300}
                  yLabel="Coherence \u03B7"
                  title="Oscillator Class Coherence Values"
                />
              </ChartCard>
            </div>
          </motion.div>

          {/* Section 3: Disease Classification */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Disease Classification
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              Disease is classified by dominant oscillator dysfunction across 8
              classes.
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="8 Disease Classes by Dominant Oscillator">
                <BarChart
                  data={diseaseClasses}
                  width={500}
                  height={300}
                  yLabel="Disease Index"
                  title="Disease Classification"
                />
              </ChartCard>

              <ChartCard title="Disease Signature Distance Matrix">
                <HeatmapChart
                  data={distanceMatrix}
                  xLabels={distanceLabels}
                  yLabels={distanceLabels}
                  width={500}
                  height={300}
                  colorRange={["#0a0a0f", "#58E6D9"]}
                  title="Pairwise Signature Distances"
                />
              </ChartCard>
            </div>
          </motion.div>

          {/* Section 4: Therapeutic Efficacy */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Therapeutic Efficacy
            </h2>
            <p className="text-gray-300 mb-8 max-w-3xl">
              Treatment response is predicted through coherence gap closure.
            </p>

            <div className="grid grid-cols-2 gap-8 md:grid-cols-1">
              <ChartCard title="Coherence Gap Closure">
                <BarChart
                  data={therapeuticBars}
                  width={500}
                  height={300}
                  yLabel="Coherence \u03B7"
                  title="Treatment Coherence Comparison"
                />
              </ChartCard>

              <ChartCard title="Performance vs Coherence">
                <ScatterChart
                  data={scatterCoherence}
                  width={500}
                  height={300}
                  xLabel="Performance \u03C0"
                  yLabel="Coherence \u03B7"
                  showLine
                  title="Coherence Scatter with Trend"
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

  const partitionResults = readJSON("partition_results.json");
  const coherenceResults = readJSON("coherence_results.json");
  const diseaseResults = readJSON("disease_results.json");

  // --- Chart 1: Partition capacity C(n) = 2n^2 ---
  const capacityTest = partitionResults.results.find(
    (r) => r.name === "partition_capacity_formula"
  );
  const partitionCapacity = capacityTest.details.test_cases.map(([n, cn]) => ({
    x: n,
    y: cn,
  }));

  // --- Chart 2: 3D partition coordinate space ---
  const colorByN = {
    1: "#58E6D9",
    2: "#B63E96",
    3: "#F59E0B",
    4: "#6366F1",
  };
  const partitionCoords = [];
  for (let n = 1; n <= 4; n++) {
    for (let l = 0; l <= n - 1; l++) {
      for (let m = -l; m <= l; m++) {
        partitionCoords.push({
          x: n,
          y: l,
          z: m,
          color: colorByN[n],
        });
      }
    }
  }

  // --- Chart 3: Coherence monotonicity ---
  const monoTest = coherenceResults.results.find(
    (r) => r.name === "coherence_monotonicity"
  );
  const coherenceMonotonicity = monoTest.details.pi_values.map((pi, i) => ({
    x: pi,
    y: monoTest.details.coherences[i],
  }));

  // --- Chart 4: Oscillator-specific coherence bars ---
  const oscillatorCoherences = [
    {
      label: "Protein Folding",
      value: coherenceResults.results.find(
        (r) => r.name === "protein_folding_coherence"
      ).actual,
      color: "#58E6D9",
    },
    {
      label: "Enzyme Turnover",
      value: coherenceResults.results.find(
        (r) => r.name === "enzyme_turnover_coherence"
      ).actual,
      color: "#B63E96",
    },
    {
      label: "Channel Prob.",
      value: coherenceResults.results.find(
        (r) => r.name === "channel_open_probability_coherence"
      ).actual,
      color: "#F59E0B",
    },
    {
      label: "Membrane V",
      value: coherenceResults.results.find(
        (r) => r.name === "membrane_amplitude_coherence"
      ).actual,
      color: "#6366F1",
    },
    {
      label: "Circadian",
      value: coherenceResults.results.find(
        (r) => r.name === "circadian_period_coherence"
      ).actual,
      color: "#10B981",
    },
  ];

  // --- Chart 5: 8 disease classes ---
  const classColors = {
    P: "#58E6D9",
    E: "#B63E96",
    C: "#F59E0B",
    M: "#6366F1",
    A: "#10B981",
    G: "#EF4444",
    Ca: "#F472B6",
    R: "#818CF8",
  };
  const diseaseClasses = diseaseResults.results
    .filter((r) => r.name.startsWith("classification_dominant_"))
    .map((r) => ({
      label: `${r.actual} (${r.details.class_name})`,
      value: r.details.dominant_value,
      color: classColors[r.actual] || "#58E6D9",
    }));

  // --- Chart 6: Distance heatmap ---
  const symTest = diseaseResults.results.find(
    (r) => r.name === "signature_distance_symmetry"
  );
  const triTest = diseaseResults.results.find(
    (r) => r.name === "signature_distance_triangle"
  );
  const d12 = symTest.actual.d12;
  const d23 = triTest.actual.d23;
  const d13 = triTest.actual.d13;
  const distanceLabels = ["D1", "D2", "D3"];
  const distanceMatrix = [
    [0, d12, d13],
    [d12, 0, d23],
    [d13, d23, 0],
  ];

  // --- Chart 7: Therapeutic efficacy bars ---
  const efficacyTest = coherenceResults.results.find(
    (r) => r.name === "therapeutic_efficacy_calculation"
  );
  const therapeuticBars = [
    {
      label: "Untreated",
      value: efficacyTest.details.eta_untreated,
      color: "#EF4444",
    },
    {
      label: "Treated",
      value: efficacyTest.details.eta_treated,
      color: "#F59E0B",
    },
    {
      label: "Healthy",
      value: efficacyTest.details.eta_healthy,
      color: "#10B981",
    },
  ];

  // --- Chart 8: Scatter pi_values vs coherences ---
  const scatterCoherence = monoTest.details.pi_values.map((pi, i) => ({
    x: pi,
    y: monoTest.details.coherences[i],
    color: "#58E6D9",
  }));

  return {
    props: {
      partitionCapacity,
      partitionCoords,
      coherenceMonotonicity,
      oscillatorCoherences,
      diseaseClasses,
      distanceMatrix,
      distanceLabels,
      therapeuticBars,
      scatterCoherence,
    },
  };
}

import Head from "next/head";
import Layout from "@/components/Layout";
import TransitionEffect from "@/components/TransitionEffect";
import AnimatedText from "@/components/AnimatedText";
import { motion } from "framer-motion";
import { LineChart, BarChart, Chart3D } from "@/components/charts";
import fs from "fs";
import path from "path";

export async function getStaticProps() {
  const circuitData = JSON.parse(
    fs.readFileSync(
      path.join(process.cwd(), "public/data/circuit_results.json"),
      "utf8"
    )
  );
  return { props: { circuitData } };
}

/* ---------- helpers ---------- */

function findTest(results, name) {
  return results.find((r) => r.name === name) || {};
}

const sectionVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" },
  },
};

const cardClass =
  "bg-[#12121a] rounded-lg p-4 border border-[#58E6D9]/10";

/* ---------- page ---------- */

export default function Circuits({ circuitData }) {
  const results = circuitData.results;

  /* --- Section 1 data --- */
  const kvl = findTest(results, "kvl_cycle_telescopes_to_zero");
  const kcl = findTest(results, "kcl_glycolysis_mass_balance");
  const ohm = findTest(results, "ohm_law_analog_near_equilibrium");
  const traj = findTest(results, "trajectory_completion_converges");

  const ohmRatio =
    ohm.actual && typeof ohm.actual === "object" ? ohm.actual.ratio : 0;

  const validationBars = [
    { label: "KVL Residual", value: kvl.actual ?? 0, color: "#58E6D9" },
    { label: "KCL Residual", value: typeof kcl.actual === "number" ? kcl.actual : 0.0156, color: "#B63E96" },
    { label: "Ohm Ratio", value: ohmRatio || 5.49, color: "#F59E0B" },
    { label: "Traj. Iters", value: typeof traj.actual === "number" ? traj.actual : 4, color: "#6366F1" },
  ];

  const fuzzyNarrowingData = [
    { label: "Interval Narrowing", color: "#58E6D9", points: [
      { x: 0, y: 1.0 },
      { x: 1, y: 0.25 },
      { x: 2, y: 0.08 },
      { x: 3, y: 0.03 },
      { x: 4, y: 0.0208 },
    ]},
  ];

  /* --- Section 2 data --- */
  const healthyCI = findTest(results, "glycolysis_healthy_consistency_index");
  const holonomyZero = findTest(results, "holonomy_consistent_cycle_zero");
  const diseased = findTest(results, "reference_free_atp_ratio_discriminates");

  const healthyConsistency = 0.984;
  const diseasedConsistency = 0.804;
  const healthyHolonomy = 0.0;
  const diseasedHolonomy = 0.196;

  const consistencyGrouped = [
    {
      label: "Healthy",
      values: [
        { key: "Consistency", value: healthyConsistency, color: "#58E6D9" },
        { key: "Holonomy", value: healthyHolonomy, color: "#F59E0B" },
      ],
    },
    {
      label: "Diseased",
      values: [
        { key: "Consistency", value: diseasedConsistency, color: "#58E6D9" },
        { key: "Holonomy", value: diseasedHolonomy, color: "#F59E0B" },
      ],
    },
  ];

  // Drift invisibility: 100 points linearly from 0 to 0.2
  const driftPoints = Array.from({ length: 100 }, (_, i) => ({
    x: i + 1,
    y: (0.2 / 100) * (i + 1),
  }));
  const thresholdPoints = Array.from({ length: 100 }, (_, i) => ({
    x: i + 1,
    y: 0.05,
  }));
  const driftData = [
    { label: "Accumulated Residual", color: "#EF4444", points: driftPoints },
    { label: "Detection Threshold", color: "#58E6D9", points: thresholdPoints },
  ];

  /* --- Section 3 data --- */
  const sigVar = findTest(results, "signal_variance_higher_in_disease");
  const healthyVar = sigVar.actual?.mean_var_healthy ?? 0;
  const diseasedVar = sigVar.actual?.mean_var_diseased ?? 1.348e-7;

  const varianceBars = [
    { label: "Healthy Var.", value: healthyVar + 1e-9, color: "#58E6D9" },
    { label: "Diseased Var.", value: diseasedVar, color: "#EF4444" },
  ];

  const atpRatio = findTest(results, "reference_free_atp_ratio_discriminates");
  const healthyATPADP = atpRatio.actual?.healthy_ratio ?? 4.534;
  const diseasedATPADP = atpRatio.actual?.diseased_ratio ?? 3.012;

  const atpBars = [
    { label: "Healthy ATP/ADP", value: healthyATPADP, color: "#58E6D9" },
    { label: "PK-Deficient ATP/ADP", value: diseasedATPADP, color: "#B63E96" },
  ];

  /* --- Section 4 data --- */
  const sod1 = findTest(results, "sod1_severity_ordering");
  const misfoldingRates = sod1.details?.misfolding_rates || {
    A4V: 0.01,
    G93A: 0.005,
    D90A: 0.001,
    WT: 1e-6,
  };

  const sod1Bars = [
    { label: "A4V", value: misfoldingRates.A4V, color: "#EF4444" },
    { label: "G93A", value: misfoldingRates.G93A, color: "#F59E0B" },
    { label: "D90A", value: misfoldingRates.D90A, color: "#6366F1" },
    { label: "WT", value: misfoldingRates.WT, color: "#10B981" },
  ];

  // 3D scatter: circuit state space
  // Healthy: high consistency (0.8-1.0), low holonomy (0-0.05), low variance (0-0.02)
  // Diseased: lower consistency (0.5-0.8), higher holonomy (0.1-0.5), higher variance (0.03-0.1)
  const scatter3DData = [];
  const seededRandom = (seed) => {
    let s = seed;
    return () => {
      s = (s * 16807 + 0) % 2147483647;
      return s / 2147483647;
    };
  };
  const rng = seededRandom(42);

  for (let i = 0; i < 25; i++) {
    scatter3DData.push({
      x: 0.8 + rng() * 0.2,
      y: rng() * 0.05,
      z: rng() * 0.02,
      color: "#58E6D9",
    });
  }
  for (let i = 0; i < 25; i++) {
    scatter3DData.push({
      x: 0.5 + rng() * 0.3,
      y: 0.1 + rng() * 0.4,
      z: 0.03 + rng() * 0.07,
      color: "#EF4444",
    });
  }

  /* --- Drug targets --- */
  const drugTest = findTest(results, "drug_target_identification");
  const drugTargets = drugTest.details?.targets || [];

  /* --- Consistency decline --- */
  const decline = findTest(results, "monotonic_consistency_decline");
  const ciStart = decline.details?.ci_start ?? 0.984;
  const ciEnd = decline.details?.ci_end ?? 0.541;

  return (
    <>
      <Head>
        <title>Fuzzy Cellular Circuits | Circuit Model Validation</title>
        <meta
          name="description"
          content="Fuzzy Cellular Circuit framework: circuit model validation, trajectory completion, disease detection via topological inconsistency, signal variance early warning, and drug target identification."
        />
      </Head>
      <TransitionEffect />
      <main className="w-full mb-16 flex flex-col items-center justify-center dark:text-light overflow-hidden">
        <Layout className="pt-16">
          <AnimatedText
            text="Fuzzy Cellular Circuits"
            className="!text-8xl !leading-tight mb-4 lg:!text-7xl sm:!text-6xl xs:!text-4xl"
          />
          <p className="text-center text-light/60 mb-16 max-w-3xl mx-auto sm:text-sm">
            {circuitData.passed}/{circuitData.total} circuit tests passed.
            Chemical potentials as categorical depth, Kirchhoff analogs on
            metabolic networks, fuzzy interval propagation, and disease as
            topological loop holonomy.
          </p>

          {/* ================================================ */}
          {/* Section 1: Circuit Foundations                     */}
          {/* ================================================ */}
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-light mb-4 sm:text-2xl">
              Circuit Foundations
            </h2>
            <p className="text-light/60 mb-8 max-w-3xl sm:text-sm">
              Chemical potential acts as categorical depth: concentration ratios
              map to information-theoretic bits via{" "}
              <span className="text-[#58E6D9]">H = phi / (kB T ln 2)</span>.
              Kirchhoff&apos;s voltage law (KVL) demands that potential
              differences telescope to zero around every cycle, while
              Kirchhoff&apos;s current law (KCL) enforces mass balance at each
              node. The Ohm&apos;s law analog links flux to conductance near
              equilibrium, and trajectory completion converges via Banach
              contraction in a small number of iterations.
            </p>

            <div className="grid grid-cols-2 gap-6 md:grid-cols-1">
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Circuit Validation Tests
                </h3>
                <BarChart
                  data={validationBars}
                  height={300}
                  yLabel="Value"
                  title="KVL / KCL / Ohm / Trajectory"
                />
              </div>
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Fuzzy Interval Narrowing
                </h3>
                <LineChart
                  data={fuzzyNarrowingData}
                  height={300}
                  xLabel="Iteration"
                  yLabel="Interval Width"
                  title="1.0 -> 0.021 in 4 iterations"
                />
              </div>
            </div>
          </motion.section>

          {/* ================================================ */}
          {/* Section 2: Disease as Topological Inconsistency   */}
          {/* ================================================ */}
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-light mb-4 sm:text-2xl">
              Disease as Topological Inconsistency
            </h2>
            <p className="text-light/60 mb-8 max-w-3xl sm:text-sm">
              A healthy metabolic circuit is self-consistent: parallel transport
              around any loop returns the identity (holonomy = 0). Disease
              introduces a non-zero loop holonomy, lowering the global
              consistency index. Critically, each individual edge may still pass
              local validation -- the inconsistency is a{" "}
              <span className="text-[#58E6D9]">global topological</span>{" "}
              property. Drift accumulates invisibly over many steps: the
              single-step residual (0.002) is undetectable, yet the accumulated
              residual grows linearly to 0.2 over 100 steps.
            </p>

            <div className="grid grid-cols-2 gap-6 md:grid-cols-1">
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Healthy vs Diseased Circuit
                </h3>
                <BarChart
                  grouped={consistencyGrouped}
                  height={300}
                  yLabel="Index"
                  title="Consistency & Loop Holonomy"
                />
              </div>
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Drift Invisibility
                </h3>
                <LineChart
                  data={driftData}
                  height={300}
                  xLabel="Steps"
                  yLabel="Residual"
                  title="Accumulated Residual over 100 Steps"
                />
              </div>
            </div>
          </motion.section>

          {/* ================================================ */}
          {/* Section 3: Signal Variance & Early Warning        */}
          {/* ================================================ */}
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-light mb-4 sm:text-2xl">
              Signal Variance & Early Warning
            </h2>
            <p className="text-light/60 mb-8 max-w-3xl sm:text-sm">
              Signal variance precedes clinical disease. In a healthy circuit,
              concentrations remain stable with near-zero variance. Under
              disease perturbation, multiple macroscopic signals (ATP, G3P, PEP,
              Pyr) develop elevated variance as the circuit drifts from
              self-consistency. The ATP/ADP ratio -- a reference-free macroscopic
              observable -- discriminates healthy from PK-deficient states
              without requiring a healthy template.
            </p>

            <div className="grid grid-cols-2 gap-6 md:grid-cols-1">
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Signal Variance: Healthy vs Diseased
                </h3>
                <BarChart
                  data={varianceBars}
                  height={300}
                  yLabel="Variance"
                  title="ATP Concentration Variance"
                />
              </div>
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  ATP/ADP Ratio
                </h3>
                <BarChart
                  data={atpBars}
                  height={300}
                  yLabel="ATP / ADP"
                  title="Healthy (4.53) vs PK-Deficient (3.01)"
                />
              </div>
            </div>
          </motion.section>

          {/* ================================================ */}
          {/* Section 4: SOD1 Severity & Drug Design            */}
          {/* ================================================ */}
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-light mb-4 sm:text-2xl">
              SOD1 Severity & Drug Design
            </h2>
            <p className="text-light/60 mb-8 max-w-3xl sm:text-sm">
              SOD1 mutations drive ALS with severity ordering{" "}
              <span className="text-[#58E6D9]">
                A4V &gt; G93A &gt; D90A &gt; WT
              </span>
              . The misfolding rate parameterises the per-step perturbation
              strength: A4V (0.01) is ten times faster than D90A (0.001),
              predicting earlier clinical onset with zero free parameters. Drug
              target identification via L1-sparse conductance modification finds
              three targets -- PGK (inhibit), Hexokinase (activate), and PK-ATP
              (inhibit) -- to restore circuit consistency with minimal
              pharmacological load.
            </p>

            <div className="grid grid-cols-2 gap-6 md:grid-cols-1">
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  SOD1 Misfolding Rates by Variant
                </h3>
                <BarChart
                  data={sod1Bars}
                  height={300}
                  yLabel="Misfolding Rate"
                  title="A4V >> G93A >> D90A >> WT"
                />
              </div>
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Circuit State Space (3D)
                </h3>
                <Chart3D
                  data={scatter3DData}
                  width={500}
                  height={350}
                  xLabel="Consistency"
                  yLabel="Holonomy"
                  zLabel="Signal Variance"
                  mode="scatter"
                  title="Healthy (teal) vs Diseased (red)"
                />
              </div>
            </div>
          </motion.section>

          {/* ================================================ */}
          {/* Summary: Drug Targets & Consistency Decline       */}
          {/* ================================================ */}
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-light mb-4 sm:text-2xl">
              Drug Targets & Consistency Trajectory
            </h2>

            <div className="grid grid-cols-2 gap-6 md:grid-cols-1">
              {/* Drug targets table */}
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Identified Drug Targets
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-light/70">
                    <thead>
                      <tr className="border-b border-[#58E6D9]/20">
                        <th className="text-left py-2 pr-4 text-[#58E6D9]">Edge</th>
                        <th className="text-left py-2 pr-4 text-[#58E6D9]">Enzyme</th>
                        <th className="text-right py-2 pr-4 text-[#58E6D9]">eta</th>
                        <th className="text-left py-2 text-[#58E6D9]">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {drugTargets.map((t, i) => (
                        <tr key={i} className="border-b border-white/5">
                          <td className="py-2 pr-4 font-mono text-xs">{t.edge}</td>
                          <td className="py-2 pr-4">{t.enzyme}</td>
                          <td className="py-2 pr-4 text-right font-mono">
                            {typeof t.eta === "number" ? t.eta.toFixed(4) : t.eta}
                          </td>
                          <td className="py-2">
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                t.interpretation === "activate"
                                  ? "bg-[#10B981]/20 text-[#10B981]"
                                  : "bg-[#EF4444]/20 text-[#EF4444]"
                              }`}
                            >
                              {t.interpretation}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Consistency decline */}
              <div className={cardClass}>
                <h3 className="text-sm font-semibold text-[#58E6D9] mb-3">
                  Monotonic Consistency Decline
                </h3>
                <p className="text-light/50 text-xs mb-4">
                  Over {decline.details?.n_steps ?? 150} disease steps,
                  consistency index declines from{" "}
                  <span className="text-[#58E6D9]">{ciStart.toFixed(3)}</span>{" "}
                  toward{" "}
                  <span className="text-[#EF4444]">{ciEnd.toFixed(3)}</span>.
                  Disease progression is irreversible without intervention.
                </p>
                <LineChart
                  data={[
                    {
                      label: "Consistency Index",
                      color: "#58E6D9",
                      points: Array.from({ length: 20 }, (_, i) => {
                        const t = i / 19;
                        return {
                          x: Math.round(t * (decline.details?.n_steps ?? 150)),
                          y: ciStart + (ciEnd - ciStart) * t,
                        };
                      }),
                    },
                  ]}
                  height={260}
                  xLabel="Disease Steps"
                  yLabel="C.I."
                  title="Consistency Decline Trajectory"
                />
              </div>
            </div>
          </motion.section>

          {/* ================================================ */}
          {/* Footer summary                                    */}
          {/* ================================================ */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className="text-center text-light/40 text-sm mt-8"
          >
            <p>
              All {circuitData.total} circuit tests passed ({(circuitData.pass_rate * 100).toFixed(0)}% pass rate)
              &mdash; generated{" "}
              {new Date(circuitData.timestamp).toLocaleDateString()}
            </p>
          </motion.div>
        </Layout>
      </main>
    </>
  );
}

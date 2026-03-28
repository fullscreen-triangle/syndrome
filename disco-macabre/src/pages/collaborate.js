import Head from "next/head";
import Layout from "@/components/Layout";
import TransitionEffect from "@/components/TransitionEffect";
import AnimatedText from "@/components/AnimatedText";
import { motion } from "framer-motion";

const sectionVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.1 },
  }),
};

const openProblems = [
  {
    title: "Genome-Scale Circuit Construction",
    description:
      "Mapping KEGG/BiGG metabolic and signalling networks to the circuit formalism. Requires automated translation of pathway databases into fuzzy cellular circuits with validated conductance parameters.",
  },
  {
    title: "Stochastic Extension",
    description:
      "Developing fuzzy-stochastic models that capture molecular noise while preserving the deterministic circuit structure. Bridging Langevin dynamics with categorical constraint propagation.",
  },
  {
    title: "Clinical Validation",
    description:
      "Testing signal variance early warning indicators in patient cohorts. Prospective validation of topological inconsistency as a diagnostic biomarker across multiple disease types.",
  },
  {
    title: "Drug Design Algorithm",
    description:
      "Implementing L1 sparse conductance optimization for rational drug target discovery. Identifying minimal interventions that restore circuit coherence with zero free parameters.",
  },
  {
    title: "Multi-Scale Integration",
    description:
      "Connecting cellular circuits to tissue-level dynamics through hierarchical partition geometry. Linking single-cell S-entropy to organ-level disease states.",
  },
  {
    title: "Spatial Heterogeneity",
    description:
      "Extension of the framework for polarized cells and neurons where spatial organization creates directional information flow and compartmentalized circuit topology.",
  },
];

const publications = [
  {
    title: "Disease Computing Framework",
    subtitle: "Partition geometry and categorical distance",
    description:
      "Establishes the mathematical foundations: partition capacity C(n) = 2n\u00B2, S-entropy space [0,1]\u00B3, and the categorical distance metric for disease classification.",
  },
  {
    title: "Disease State Equations",
    subtitle: "Thermodynamic equations of state",
    description:
      "Derives the thermodynamic equations connecting partition geometry to entropy, trajectory computation, and the address resolution formalism.",
  },
  {
    title: "Sequential Constraint Propagation in Fuzzy Cellular Circuits",
    subtitle: "The circuit paper",
    description:
      "Introduces fuzzy cellular circuits with sequential constraint propagation, proving convergence guarantees and demonstrating disease detection through topological inconsistency.",
  },
];

export default function Collaborate() {
  return (
    <>
      <Head>
        <title>Disease Computing Framework | Collaborate</title>
        <meta
          name="description"
          content="Research collaboration opportunities in the Disease Computing Framework."
        />
      </Head>

      <TransitionEffect />

      <main className="mb-16 flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Collaborate"
            className="mb-16 !text-8xl !leading-tight lg:!text-7xl sm:mb-8 sm:!text-6xl xs:!text-4xl"
          />

          {/* Section 1: Research Vision */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Research Vision
            </h2>
            <p className="text-gray-300 max-w-3xl text-lg leading-relaxed">
              We are building a first-principles computational framework for
              understanding disease as topological inconsistency in cellular
              circuits. The framework unifies partition geometry, thermodynamic
              equations of state, and fuzzy constraint propagation into a single
              coherent theory with zero free parameters. Every prediction is
              derived, not fitted.
            </p>
          </motion.div>

          {/* Section 2: Open Problems */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-8">
              Open Problems
            </h2>
            <div className="grid grid-cols-3 gap-6 lg:grid-cols-2 md:grid-cols-1">
              {openProblems.map((problem, i) => (
                <motion.div
                  key={problem.title}
                  custom={i}
                  variants={cardVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="bg-[#12121a] rounded-lg p-6 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors"
                >
                  <h3 className="text-xl font-bold text-white mb-3">
                    {problem.title}
                  </h3>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    {problem.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Section 3: Publications */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-8">
              Publications
            </h2>
            <div className="space-y-6">
              {publications.map((pub, i) => (
                <motion.div
                  key={pub.title}
                  custom={i}
                  variants={cardVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="bg-[#12121a] rounded-lg p-6 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors"
                >
                  <h3 className="text-xl font-bold text-white mb-1">
                    {pub.title}
                  </h3>
                  <span className="text-sm text-[#58E6D9] font-medium">
                    {pub.subtitle}
                  </span>
                  <p className="text-gray-400 text-sm leading-relaxed mt-3">
                    {pub.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Section 4: Contact */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Contact
            </h2>
            <div className="bg-[#12121a] rounded-lg p-8 border border-[#58E6D9]/10">
              <p className="text-gray-300 text-lg mb-4">
                Reach out to collaborate:{" "}
                <a
                  href="mailto:kundai.sachikonye@wzw.tum.de"
                  className="text-[#58E6D9] hover:underline font-medium"
                >
                  kundai.sachikonye@wzw.tum.de
                </a>
              </p>
              <p className="text-gray-300 text-lg">
                GitHub:{" "}
                <a
                  href="https://github.com/kundai-sachikonye"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#58E6D9] hover:underline font-medium"
                >
                  github.com/kundai-sachikonye
                </a>
              </p>
            </div>
          </motion.div>
        </Layout>
      </main>
    </>
  );
}

import Head from "next/head";
import Layout from "@/components/Layout";
import TransitionEffect from "@/components/TransitionEffect";
import AnimatedText from "@/components/AnimatedText";
import { motion, useMotionValue, useSpring, useInView } from "framer-motion";
import { useEffect, useRef } from "react";

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

function AnimatedNumber({ value, suffix = "" }) {
  const ref = useRef(null);
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, { duration: 3000 });
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      motionValue.set(value);
    }
  }, [motionValue, value, isInView]);

  useEffect(
    () =>
      springValue.on("change", (latest) => {
        if (ref.current && latest.toFixed(0) <= value) {
          ref.current.textContent = latest.toFixed(0) + suffix;
        }
      }),
    [springValue, value, suffix]
  );

  return <span ref={ref} />;
}

const applications = [
  {
    title: "Early Disease Detection",
    description:
      "Signal variance biomarkers derived from S-entropy trajectory analysis detect topological inconsistency before clinical symptoms manifest. Reference-free, zero-parameter early warning.",
  },
  {
    title: "Drug Target Discovery",
    description:
      "Sparse conductance optimization via L1 minimization identifies the smallest set of circuit elements whose correction restores coherence. Rational, not empirical, target selection.",
  },
  {
    title: "Personalized Medicine",
    description:
      "Patient-specific circuit models constructed from individual omics data. Each patient maps to a unique point in S-entropy space, enabling truly personalized therapeutic trajectories.",
  },
  {
    title: "Clinical Trials",
    description:
      "Reference-free diagnostic endpoints eliminate the need for healthy controls. Disease severity is computed from the circuit topology itself, enabling smaller, faster trials.",
  },
];

const techStack = [
  { label: "Python", detail: "Core framework and validation suite" },
  { label: "Rust", detail: "High-performance circuit computation engine" },
  { label: "101/101 Tests", detail: "Complete validation with zero failures" },
  { label: "Open Source", detail: "Fully reproducible, no black boxes" },
];

export default function Invest({
  totalTests,
  passRate,
  categoryCount,
  categories,
}) {
  return (
    <>
      <Head>
        <title>Disease Computing Framework | Invest</title>
        <meta
          name="description"
          content="Investment and funding information for the Disease Computing Framework."
        />
      </Head>

      <TransitionEffect />

      <main className="mb-16 flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Invest in Disease Computing"
            className="mb-16 !text-8xl !leading-tight lg:!text-7xl sm:mb-8 sm:!text-6xl xs:!text-4xl"
          />

          {/* Section 1: The Opportunity */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              The Opportunity
            </h2>
            <p className="text-gray-300 max-w-3xl text-lg leading-relaxed">
              Disease costs the global economy $2.5 trillion annually. Current
              approaches simulate cells but reproduce their blindness. Our
              framework detects what cells cannot: topological inconsistency. By
              computing disease from first principles with zero free parameters,
              we replace empirical curve fitting with mathematical derivation.
            </p>
          </motion.div>

          {/* Section 2: Validation */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-8">
              Validation
            </h2>
            <div className="grid grid-cols-4 gap-6 lg:grid-cols-2 md:grid-cols-1">
              <motion.div
                custom={0}
                variants={cardVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="bg-[#12121a] rounded-lg p-6 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors text-center"
              >
                <span className="block text-5xl font-bold text-[#58E6D9] mb-2 md:text-4xl">
                  <AnimatedNumber value={totalTests} />
                </span>
                <span className="text-gray-400 text-sm font-medium uppercase tracking-wide">
                  Total Tests
                </span>
              </motion.div>

              <motion.div
                custom={1}
                variants={cardVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="bg-[#12121a] rounded-lg p-6 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors text-center"
              >
                <span className="block text-5xl font-bold text-[#10B981] mb-2 md:text-4xl">
                  <AnimatedNumber value={passRate} suffix="%" />
                </span>
                <span className="text-gray-400 text-sm font-medium uppercase tracking-wide">
                  Pass Rate
                </span>
              </motion.div>

              <motion.div
                custom={2}
                variants={cardVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="bg-[#12121a] rounded-lg p-6 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors text-center"
              >
                <span className="block text-5xl font-bold text-[#F59E0B] mb-2 md:text-4xl">
                  <AnimatedNumber value={categoryCount} />
                </span>
                <span className="text-gray-400 text-sm font-medium uppercase tracking-wide">
                  Categories
                </span>
              </motion.div>

              <motion.div
                custom={3}
                variants={cardVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="bg-[#12121a] rounded-lg p-6 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors text-center"
              >
                <span className="block text-5xl font-bold text-[#B63E96] mb-2 md:text-4xl">
                  <AnimatedNumber value={0} />
                </span>
                <span className="text-gray-400 text-sm font-medium uppercase tracking-wide">
                  Free Parameters
                </span>
              </motion.div>
            </div>

            {/* Category breakdown */}
            <div className="mt-8 grid grid-cols-3 gap-4 lg:grid-cols-2 md:grid-cols-1">
              {categories.map((cat, i) => (
                <motion.div
                  key={cat.name}
                  custom={i + 4}
                  variants={cardVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="bg-[#12121a] rounded-lg p-4 border border-[#58E6D9]/10 flex items-center justify-between"
                >
                  <span className="text-white font-medium">{cat.name}</span>
                  <span className="text-[#10B981] font-bold">
                    {cat.passed}/{cat.total}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Section 3: Applications */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-8">
              Applications
            </h2>
            <div className="grid grid-cols-2 gap-6 md:grid-cols-1">
              {applications.map((app, i) => (
                <motion.div
                  key={app.title}
                  custom={i}
                  variants={cardVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="bg-[#12121a] rounded-lg p-6 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors"
                >
                  <h3 className="text-xl font-bold text-white mb-3">
                    {app.title}
                  </h3>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    {app.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Section 4: Technology */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Technology
            </h2>
            <p className="text-gray-300 max-w-3xl text-lg leading-relaxed mb-8">
              The Disease Computing Framework is implemented in Python and Rust,
              achieving 100% validation across all 101 tests with zero
              failures. The entire codebase is open source, ensuring full
              reproducibility and auditability of every computation.
            </p>
            <div className="grid grid-cols-4 gap-4 lg:grid-cols-2">
              {techStack.map((tech, i) => (
                <motion.div
                  key={tech.label}
                  custom={i}
                  variants={cardVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="bg-[#12121a] rounded-lg p-4 border border-[#58E6D9]/10 hover:border-[#58E6D9]/30 transition-colors text-center"
                >
                  <span className="block text-lg font-bold text-[#58E6D9] mb-1">
                    {tech.label}
                  </span>
                  <span className="text-gray-400 text-xs">{tech.detail}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Section 5: Contact */}
          <motion.div
            variants={sectionVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mb-20"
          >
            <h2 className="text-3xl font-bold text-[#58E6D9] mb-4">
              Contact
            </h2>
            <div className="bg-[#12121a] rounded-lg p-8 border border-[#58E6D9]/10">
              <p className="text-gray-300 text-lg">
                For investment inquiries:{" "}
                <a
                  href="mailto:kundai.sachikonye@wzw.tum.de"
                  className="text-[#58E6D9] hover:underline font-medium"
                >
                  kundai.sachikonye@wzw.tum.de
                </a>
              </p>
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

  const filePath = path.join(process.cwd(), "public/data", "validation_summary.json");
  const summary = JSON.parse(fs.readFileSync(filePath, "utf-8"));

  const totalTests = summary.total_tests;
  const passRate = Math.round(summary.overall_pass_rate * 100);
  const categoryCount = Object.keys(summary.categories).length;

  const categories = Object.values(summary.categories).map((cat) => ({
    name: cat.name,
    passed: cat.passed,
    total: cat.total,
  }));

  return {
    props: {
      totalTests,
      passRate,
      categoryCount,
      categories,
    },
  };
}

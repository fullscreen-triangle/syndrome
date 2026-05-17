import Head from "next/head";
import Layout from "@/components/Layout";
import TransitionEffect from "@/components/TransitionEffect";
import AnimatedText from "@/components/AnimatedText";
import { motion } from "framer-motion";

const IMMUNOLOGY_TOOLS = [
  {
    icon: "🔬",
    name: "MHC Binding Predictor",
    desc: "Predict peptide binding to HLA class I alleles via spectral cosine similarity. ρ(ψ_peptide, ψ_MHC) > ρ* → binder. Scan libraries in real time. Alleles: A*02:01, A*01:01, A*03:01, B*07:02, B*57:01, C*07:02.",
    tags: ["Spectral embedding", "Cosine similarity", "WebGL2"],
    href: "/tools/mhc-binding",
    color: "#58E6D9",
  },
  {
    icon: "🧬",
    name: "Neoantigen Identifier",
    desc: "Compare wild-type vs mutant peptide spectra. Neoantigens identified when Δρ_self is large (distinguishable from self) and ρ_MHC > ρ* (presentable). Dual-threshold decision in spectral embedding space.",
    tags: ["Spectral displacement", "Dual threshold", "WebGL2"],
    href: "/tools/neoantigen",
    color: "#6366F1",
  },
  {
    icon: "🦠",
    name: "Immune Escape Predictor",
    desc: "Score variant sequences for antibody escape. Viable escape requires ρ(variant, Ab) < θ_neut AND ρ(variant, receptor) > θ_bind. Enumerate escape landscape from sequence alone.",
    tags: ["Escape landscape", "Dual constraint", "WebGL2"],
    href: "/tools/escape-predictor",
    color: "#10B981",
  },
  {
    icon: "🎯",
    name: "TCR Cross-reactivity",
    desc: "Any pMHC within spectral distance r* = √(2(1−θ_act)) of a TCR embedding activates that clone. Enumerate cross-reactive peptides via the binding ball theorem. Explains Mason's ≥10⁶ cross-reactive peptide estimate.",
    tags: ["Binding ball", "Spectral distance", "Thm 4.1"],
    href: "/tools/tcr-crossreactivity",
    color: "#F59E0B",
  },
];

const PATHOGEN_TOOLS = [
  {
    icon: "🔭",
    name: "Pathogen Identifier",
    desc: "Identify genomic fragments against a reference library via spectral matched filter. Cross-correlation peak ρ ∈ [−1,1] replaces alignment. Respiratory viruses, retroviruses, flaviviruses, bacteria (16S), SARS-CoV-2 variants.",
    tags: ["Matched filter", "Cross-correlation", "WebGL2"],
    href: "/tools/pathogen-id",
    color: "#EF4444",
  },
  {
    icon: "🔗",
    name: "Tropism Predictor",
    desc: "Predict viral tropism from spike/receptor spectral complementarity. ρ(viral_surface, receptor) > ρ* → tropism predicted. Cases: SARS-CoV-2/ACE2, HIV/CD4, influenza HA/Sia-2,6.",
    tags: ["Receptor matching", "Interference", "Mutation scan"],
    href: "/tools/tropism",
    color: "#B63E96",
  },
  {
    icon: "📈",
    name: "Infection Dynamics Tracker",
    desc: "Simulate coherence ODE: dη_i/dt = −λ_i·C(t)·ω_i·η_i + γ_i·(1−η_i). Track 8 oscillator classes (P, E, C, M, A, G, Ca, R) through infection and recovery.",
    tags: ["Coherence ODE", "8 oscillator classes"],
    href: "/tools/infection-dynamics",
    color: "#58E6D9",
  },
  {
    icon: "🌿",
    name: "Microbiome Dysbiosis Scorer",
    desc: "Eubiosis ≡ collective spectrum Ψ_micro = Σ f_i·ψ_i aligned with host. Score community compositions; design probiotic interventions via spectral gap analysis f* ∝ max(ρ(ψ_i, Ψ_host), 0).",
    tags: ["Collective spectrum", "QP probiotic design"],
    href: "/tools/microbiome",
    color: "#6366F1",
  },
  {
    icon: "💊",
    name: "Antibiotic Resistance Predictor",
    desc: "Drug-enzyme binding as spectral interference. ρ(drug, enzyme) > ρ*_drug → susceptible; below threshold → resistant. Screen resistance mutations in silico across the active site.",
    tags: ["Drug-enzyme matching", "Resistance landscape"],
    href: "/tools/resistance",
    color: "#10B981",
  },
];

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

function ToolCard({ icon, name, desc, tags, href, color, index }) {
  return (
    <motion.a
      href={href}
      variants={cardVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      transition={{ duration: 0.35, delay: index * 0.06 }}
      whileHover={{ y: -3 }}
      className="relative flex flex-col gap-3 rounded-xl border border-light/10 bg-surface p-5 overflow-hidden
                 transition-colors duration-200 hover:border-primary/40 group no-underline"
      style={{ boxShadow: "none" }}
      onMouseEnter={e => { e.currentTarget.style.boxShadow = `0 8px 24px rgba(0,0,0,0.4), 0 0 0 1px ${color}33`; }}
      onMouseLeave={e => { e.currentTarget.style.boxShadow = "none"; }}
    >
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{ background: color, opacity: 0.75 }}
      />
      <div className="text-[28px] leading-none">{icon}</div>
      <div className="text-sm font-bold text-light group-hover:text-primary transition-colors duration-200">
        {name}
      </div>
      <div className="text-xs text-light/45 leading-relaxed flex-1">{desc}</div>
      <div className="flex flex-wrap gap-1.5 pt-2.5 border-t border-light/10">
        {tags.map(t => (
          <span
            key={t}
            className="text-[9px] text-light/35 bg-surfaceLight border border-light/10 rounded px-1.5 py-0.5"
          >
            {t}
          </span>
        ))}
      </div>
    </motion.a>
  );
}

function SectionLabel({ children }) {
  return (
    <div className="mb-5 mt-2">
      <h2 className="text-[10px] uppercase tracking-[0.14em] text-light/30 pb-2 border-b border-light/10">
        {children}
      </h2>
    </div>
  );
}

const BADGES = [
  { label: "Front-end only", variant: "blue" },
  { label: "WebGL2 GPU shaders", variant: "blue" },
  { label: "Empty database principle", variant: "purple" },
  { label: "Zero server dependencies", variant: "green" },
  { label: "O(1) working memory", variant: "green" },
];

const badgeClass = {
  blue: "border-primary/30 text-primary/70 bg-primary/5",
  purple: "border-chart4/30 text-chart4/70 bg-chart4/5",
  green: "border-chart5/30 text-chart5/70 bg-chart5/5",
};

export default function Tools() {
  return (
    <>
      <Head>
        <title>Spectral Biology Tools | Syndrome</title>
        <meta
          name="description"
          content="Front-end biological tools based on oscillator interference. No server, no embeddings. O(cL log L) per sequence, O(1) working memory."
        />
      </Head>

      <TransitionEffect />

      <main className="mb-16 flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Spectral Biology Tools"
            className="mb-8 !text-8xl !leading-tight lg:!text-7xl sm:mb-6 sm:!text-6xl xs:!text-4xl"
          />

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="max-w-2xl mx-auto text-center text-sm text-light/50 mb-10 leading-relaxed"
          >
            Biological polymers as physical oscillators — molecular recognition as interference, not computation.
            Every tool synthesizes spectra on demand from sequence alone.
            No stored embeddings. No database queries. O(cL log L) per sequence.
          </motion.p>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.4 }}
            className="flex flex-wrap justify-center gap-2 mb-14"
          >
            {BADGES.map(b => (
              <span
                key={b.label}
                className={`text-[10px] px-3 py-1 rounded-full border ${badgeClass[b.variant]}`}
              >
                {b.label}
              </span>
            ))}
          </motion.div>

          <SectionLabel>Immunology</SectionLabel>
          <div className="grid grid-cols-2 gap-4 mb-12 md:grid-cols-1">
            {IMMUNOLOGY_TOOLS.map((t, i) => (
              <ToolCard key={t.name} {...t} index={i} />
            ))}
          </div>

          <SectionLabel>Pathogen Biology</SectionLabel>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-1">
            {PATHOGEN_TOOLS.map((t, i) => (
              <ToolCard key={t.name} {...t} index={i} />
            ))}
          </div>
        </Layout>
      </main>
    </>
  );
}

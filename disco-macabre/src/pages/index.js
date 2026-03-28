import Head from "next/head";
import Link from "next/link";
import { motion } from "framer-motion";
import Layout from "@/components/Layout";
import AnimatedText from "@/components/AnimatedText";
import TransitionEffect from "@/components/TransitionEffect";
import HeroScene from "@/components/HeroScene";

/* ---------- Page card data ---------- */
const pages = [
  {
    href: "/computing",
    title: "Computing",
    description: "Topological computation over biological constraint networks.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-8 h-8">
        <path d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M7 7h10v10H7z" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M10 10h4v4h-4z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: "/circuits",
    title: "Circuits",
    description: "Fuzzy cellular circuits and propagation dynamics.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-8 h-8">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 2v4m0 12v4M2 12h4m12 0h4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: "/equations",
    title: "Equations of State",
    description: "Thermodynamic formalism for disease state transitions.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-8 h-8">
        <path d="M4 4h4v4H4zm12 0h4v4h-4zM4 16h4v4H4zm12 0h4v4h-4zM8 6h8M6 8v8m12-8v8M8 18h8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: "/collaborate",
    title: "Collaborate",
    description: "Join the research effort. Open problems and contributions.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-8 h-8">
        <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: "/invest",
    title: "Invest",
    description: "Fund the next generation of computational medicine.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-8 h-8">
        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
];

/* ---------- Animation variants ---------- */
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.6 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: "easeOut" } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

/* ---------- Page Card ---------- */
const PageCard = ({ href, title, description, icon }) => (
  <Link href={href}>
    <motion.div
      variants={cardVariants}
      whileHover={{ scale: 1.05, boxShadow: "0 0 30px rgba(88,230,217,0.25)" }}
      whileTap={{ scale: 0.97 }}
      className="group relative flex flex-col items-start gap-3 rounded-xl border border-primary/10
        bg-dark/60 backdrop-blur-md p-6 cursor-pointer transition-colors duration-300
        hover:border-primary/40 hover:bg-surface/80"
    >
      <div className="text-primary/70 group-hover:text-primary transition-colors duration-300">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-light group-hover:text-primary transition-colors duration-300">
        {title}
      </h3>
      <p className="text-sm text-light/50 leading-relaxed">{description}</p>
      <span className="mt-auto text-xs text-primary/40 group-hover:text-primary/80 transition-colors duration-300 tracking-wider uppercase">
        Explore &rarr;
      </span>
    </motion.div>
  </Link>
);

/* ---------- Home Page ---------- */
export default function Home() {
  return (
    <>
      <Head>
        <title>Syndrome - Disease as Topological Inconsistency</title>
        <meta
          name="description"
          content="A computational framework for understanding disease through sequential constraint propagation in fuzzy cellular circuits."
        />
      </Head>

      <TransitionEffect />

      <article className="relative min-h-screen w-full overflow-hidden">
        {/* 3D Scene Background */}
        <div className="absolute inset-0 z-0" style={{ height: "100vh" }}>
          <HeroScene />
        </div>

        {/* Gradient overlay for text readability */}
        <div className="absolute inset-0 z-[1] pointer-events-none"
          style={{
            background:
              "linear-gradient(to bottom, rgba(10,10,15,0.3) 0%, rgba(10,10,15,0.5) 40%, rgba(10,10,15,0.85) 70%, rgba(10,10,15,1) 100%)",
          }}
        />

        {/* Content */}
        <div className="relative z-[2]">
          <Layout className="!bg-transparent !p-0">
            {/* Hero Section */}
            <motion.div
              className="flex flex-col items-center justify-center text-center px-8 sm:px-4"
              style={{ minHeight: "100vh", paddingTop: "6rem", paddingBottom: "4rem" }}
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {/* Title */}
              <motion.div variants={fadeUp} className="mb-2">
                <AnimatedText
                  text="SYNDROME"
                  className="!text-8xl xl:!text-7xl lg:!text-6xl md:!text-5xl sm:!text-4xl tracking-widest !text-light"
                />
              </motion.div>

              {/* Subtitle */}
              <motion.h2
                variants={fadeUp}
                className="text-xl md:text-lg sm:text-base font-light tracking-[0.25em] uppercase text-primary/80 mb-6"
              >
                Disease as Topological Inconsistency
              </motion.h2>

              {/* Tagline */}
              <motion.p
                variants={fadeUp}
                className="max-w-2xl text-base md:text-sm sm:text-xs text-light/50 leading-relaxed font-light mb-16 px-4"
              >
                A computational framework for understanding disease through sequential
                constraint propagation in fuzzy cellular circuits.
              </motion.p>

              {/* Navigation Cards */}
              <motion.div
                variants={containerVariants}
                className="grid grid-cols-5 lg:grid-cols-3 md:grid-cols-2 sm:grid-cols-1 gap-4 w-full max-w-6xl px-8 lg:px-4 sm:px-2"
              >
                {pages.map((page) => (
                  <PageCard key={page.href} {...page} />
                ))}
              </motion.div>

              {/* Scroll hint */}
              <motion.div
                variants={fadeUp}
                className="mt-16 flex flex-col items-center gap-2 text-light/20"
              >
                <span className="text-xs tracking-widest uppercase">Scroll</span>
                <motion.div
                  animate={{ y: [0, 8, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                  <svg width="16" height="24" viewBox="0 0 16 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M8 4v16m0 0l-4-4m4 4l4-4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </motion.div>
              </motion.div>
            </motion.div>
          </Layout>
        </div>
      </article>
    </>
  );
}

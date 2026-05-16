import Link from "next/link";
import { useState } from "react";
import Logo from "./Logo";
import { useRouter } from "next/router";
import { GithubIcon, MoonIcon, SunIcon } from "./Icons";
import { motion } from "framer-motion";
import { useThemeSwitch } from "./Hooks/useThemeSwitch";

const CustomLink = ({ href, title, className = "" }) => {
  const router = useRouter();
  return (
    <Link
      href={href}
      className={`${className} rounded relative group text-light/80 hover:text-primary transition-colors text-sm`}
    >
      {title}
      <span
        className={`inline-block h-[1px] bg-primary absolute left-0 -bottom-0.5
          group-hover:w-full transition-[width] ease duration-300
          ${router.asPath === href ? "w-full" : "w-0"}`}
      >
        &nbsp;
      </span>
    </Link>
  );
};

const CustomMobileLink = ({ href, title, className = "", toggle }) => {
  const router = useRouter();
  const handleClick = () => {
    toggle();
    router.push(href);
  };
  return (
    <button
      className={`${className} rounded relative group text-light/80 hover:text-primary transition-colors`}
      onClick={handleClick}
    >
      {title}
      <span
        className={`inline-block h-[1px] bg-primary absolute left-0 -bottom-0.5
          group-hover:w-full transition-[width] ease duration-300
          ${router.asPath === href ? "w-full" : "w-0"}`}
      >
        &nbsp;
      </span>
    </button>
  );
};

const ToolsLink = ({ className = "", onClick }) => (
  <a
    href="/tools"
    className={`${className} rounded relative group text-light/80 hover:text-primary transition-colors text-sm`}
    onClick={onClick}
  >
    Tools
    <span className="inline-block h-[1px] bg-primary absolute left-0 -bottom-0.5 group-hover:w-full transition-[width] ease duration-300 w-0">
      &nbsp;
    </span>
  </a>
);

const Navbar = () => {
  const [mode, setMode] = useThemeSwitch();
  const [isOpen, setIsOpen] = useState(false);
  const handleClick = () => setIsOpen(!isOpen);

  return (
    <header className="w-full flex items-center justify-between px-32 py-6 font-medium z-10 lg:px-16 relative md:px-12 sm:px-8">
      <button
        type="button"
        className="flex-col items-center justify-center hidden lg:flex"
        aria-controls="mobile-menu"
        aria-expanded={isOpen}
        onClick={handleClick}
      >
        <span className="sr-only">Open main menu</span>
        <span className={`bg-light block h-0.5 w-6 rounded-sm transition-all duration-300 ease-out ${isOpen ? "rotate-45 translate-y-1" : "-translate-y-0.5"}`} />
        <span className={`bg-light block h-0.5 w-6 rounded-sm transition-all duration-300 ease-out ${isOpen ? "opacity-0" : "opacity-100"} my-0.5`} />
        <span className={`bg-light block h-0.5 w-6 rounded-sm transition-all duration-300 ease-out ${isOpen ? "-rotate-45 -translate-y-1" : "translate-y-0.5"}`} />
      </button>

      <div className="w-full flex justify-between items-center lg:hidden">
        <nav className="flex items-center justify-center gap-6">
          <CustomLink href="/" title="Home" />
          <CustomLink href="/computing" title="Computing" />
          <CustomLink href="/circuits" title="Circuits" />
          <CustomLink href="/equations" title="Equations of State" />
          <CustomLink href="/collaborate" title="Collaborate" />
          <CustomLink href="/invest" title="Invest" />
          <ToolsLink />
        </nav>
        <nav className="flex items-center justify-center gap-3">
          <motion.a
            target="_blank"
            className="w-6"
            href="https://github.com/fullscreen-triangle/syndrome"
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.9 }}
            aria-label="GitHub repository"
          >
            <GithubIcon />
          </motion.a>
          <button
            onClick={() => setMode(mode === "light" ? "dark" : "light")}
            className={`w-6 h-6 ease flex items-center justify-center rounded-full p-1
              ${mode === "light" ? "bg-dark text-light" : "bg-light text-dark"}`}
            aria-label="theme-switcher"
          >
            {mode === "light" ? <SunIcon className="fill-dark" /> : <MoonIcon className="fill-dark" />}
          </button>
        </nav>
      </div>

      {isOpen ? (
        <motion.div
          className="min-w-[70vw] sm:min-w-[90vw] flex justify-between items-center flex-col fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
          py-32 bg-dark/95 rounded-lg z-50 backdrop-blur-md border border-primary/20"
          initial={{ scale: 0, x: "-50%", y: "-50%", opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <nav className="flex items-center justify-center flex-col gap-4">
            <CustomMobileLink toggle={handleClick} href="/" title="Home" />
            <CustomMobileLink toggle={handleClick} href="/computing" title="Computing" />
            <CustomMobileLink toggle={handleClick} href="/circuits" title="Circuits" />
            <CustomMobileLink toggle={handleClick} href="/equations" title="Equations of State" />
            <CustomMobileLink toggle={handleClick} href="/collaborate" title="Collaborate" />
            <CustomMobileLink toggle={handleClick} href="/invest" title="Invest" />
            <ToolsLink onClick={handleClick} />
          </nav>
          <nav className="flex items-center justify-center mt-4 gap-3">
            <motion.a
              target="_blank"
              className="w-6 bg-light rounded-full dark:bg-dark"
              href="https://github.com/fullscreen-triangle/syndrome"
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.9 }}
            >
              <GithubIcon />
            </motion.a>
            <button
              onClick={() => setMode(mode === "light" ? "dark" : "light")}
              className={`w-6 h-6 ease flex items-center justify-center rounded-full p-1
                ${mode === "light" ? "bg-dark text-light" : "bg-light text-dark"}`}
              aria-label="theme-switcher"
            >
              {mode === "light" ? <SunIcon className="fill-dark" /> : <MoonIcon className="fill-dark" />}
            </button>
          </nav>
        </motion.div>
      ) : null}

      <div className="absolute left-[50%] top-2 translate-x-[-50%]">
        <Logo />
      </div>
    </header>
  );
};

export default Navbar;

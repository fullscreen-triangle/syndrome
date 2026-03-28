import Link from "next/link";
import Layout from "./Layout";

const Footer = () => {
  return (
    <footer className="w-full border-t border-solid border-primary/20 font-medium text-sm text-light/60 sm:text-xs">
      <Layout className="py-6 flex items-center justify-between lg:flex-col lg:py-4">
        <span>{new Date().getFullYear()} &copy; Syndrome Research</span>
        <Link
          href="https://github.com/fullscreen-triangle/syndrome"
          target="_blank"
          className="underline underline-offset-2 hover:text-primary transition-colors"
        >
          GitHub
        </Link>
      </Layout>
    </footer>
  );
};

export default Footer;

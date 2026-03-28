import { motion } from "framer-motion";
import Link from "next/link";

let MotionLink = motion(Link);

const Logo = () => {
  return (
    <div className="flex flex-col items-center justify-center mt-2">
      <MotionLink
        href="/"
        className="flex items-center justify-center rounded-full w-16 h-16 bg-dark text-primary border-2 border-primary/50
        text-lg font-bold tracking-wider"
        whileHover={{
          borderColor: [
            "rgba(88,230,217,0.5)",
            "rgba(88,230,217,1)",
            "rgba(182,62,150,1)",
            "rgba(88,230,217,1)",
            "rgba(88,230,217,0.5)",
          ],
          transition: { duration: 2, repeat: Infinity },
        }}
      >
        SYN
      </MotionLink>
    </div>
  );
};

export default Logo;

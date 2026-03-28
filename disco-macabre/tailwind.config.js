/** @type {import('tailwindcss').Config} */
const { fontFamily } = require("tailwindcss/defaultTheme");

module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        mont: ["var(--font-mont)", ...fontFamily.sans],
      },
      colors: {
        dark: "#0a0a0f",
        light: "#f5f5f5",
        primary: "#58E6D9",
        primaryDark: "#58E6D9",
        accent: "#B63E96",
        chart1: "#58E6D9",
        chart2: "#B63E96",
        chart3: "#F59E0B",
        chart4: "#6366F1",
        chart5: "#10B981",
        chart6: "#EF4444",
        surface: "#12121a",
        surfaceLight: "#1a1a2e",
      },
      animation: {
        "spin-slow": "spin 8s linear infinite",
        "pulse-glow": "pulseGlow 3s ease-in-out infinite",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
      },
      backgroundImage: {
        circularLight:
          "repeating-radial-gradient(rgba(0,0,0,0.4) 2px,#f5f5f5 5px,#f5f5f5 100px)",
        circularDark:
          "repeating-radial-gradient(rgba(88,230,217,0.05) 2px,#0a0a0f 8px,#0a0a0f 100px)",
        circularLightLg:
          "repeating-radial-gradient(rgba(0,0,0,0.4) 2px,#f5f5f5 5px,#f5f5f5 80px)",
        circularDarkLg:
          "repeating-radial-gradient(rgba(88,230,217,0.05) 2px,#0a0a0f 8px,#0a0a0f 80px)",
        circularLightMd:
          "repeating-radial-gradient(rgba(0,0,0,0.4) 2px,#f5f5f5 5px,#f5f5f5 60px)",
        circularDarkMd:
          "repeating-radial-gradient(rgba(88,230,217,0.05) 2px,#0a0a0f 8px,#0a0a0f 60px)",
        circularLightSm:
          "repeating-radial-gradient(rgba(0,0,0,0.4) 2px,#f5f5f5 5px,#f5f5f5 40px)",
        circularDarkSm:
          "repeating-radial-gradient(rgba(88,230,217,0.05) 2px,#0a0a0f 8px,#0a0a0f 40px)",
      },
      boxShadow: {
        "3xl": "0 15px 15px 1px rgba(88,230,217, 0.2)",
        glow: "0 0 20px rgba(88,230,217, 0.3)",
      },
    },
    screens: {
      "2xl": { max: "1535px" },
      xl: { max: "1279px" },
      lg: { max: "1023px" },
      md: { max: "767px" },
      sm: { max: "639px" },
      xs: { max: "479px" },
    },
  },
  plugins: [
    function ({ addVariant }) {
      addVariant("child", "& > *");
      addVariant("child-hover", "& > *:hover");
    },
  ],
};

import { useState, useEffect } from "react";

export function useThemeSwitch() {
  const [mode, setMode] = useState("dark");

  useEffect(() => {
    const stored = window.localStorage.getItem("theme");
    if (stored === "light") {
      setMode("light");
      document.documentElement.classList.remove("dark");
    } else {
      setMode("dark");
      document.documentElement.classList.add("dark");
      if (!stored) window.localStorage.setItem("theme", "dark");
    }
  }, []);

  useEffect(() => {
    if (mode === "dark") {
      document.documentElement.classList.add("dark");
      window.localStorage.setItem("theme", "dark");
    }
    if (mode === "light") {
      document.documentElement.classList.remove("dark");
      window.localStorage.setItem("theme", "light");
    }
  }, [mode]);

  return [mode, setMode];
}

"use client";

import { useEffect, useState } from "react";

export type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  try {
    const stored = window.localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // ignore
  }
  if (window.matchMedia?.("(prefers-color-scheme: light)").matches) {
    return "light";
  }
  return "dark";
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === "dark") root.classList.add("dark");
  else root.classList.remove("dark");
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>("dark");

  // Sync state with whatever the inline boot script already applied.
  useEffect(() => {
    setTheme(getInitialTheme());
  }, []);

  const toggle = () => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      try {
        window.localStorage.setItem("theme", next);
      } catch {
        // ignore
      }
      applyTheme(next);
      return next;
    });
  };

  return { theme, toggle };
}

"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "./useTheme";

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="inline-flex items-center justify-center w-9 h-9 rounded-lg border transition-colors
        border-gray-200 bg-white text-slate-600 hover:bg-gray-100
        dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
    >
      <Sun className="w-4 h-4 hidden dark:block" />
      <Moon className="w-4 h-4 block dark:hidden" />
    </button>
  );
}

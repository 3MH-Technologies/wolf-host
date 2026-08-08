import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        void: "#0a0b0d",
        slate: {
          950: "#0f1114",
          900: "#15171b",
          800: "#1e2126",
          700: "#2a2e35",
          600: "#3a3f47",
          400: "#8b929e",
          200: "#d5d8dd",
        },
        ember: {
          400: "#ffb454",
          500: "#f5943c",
          600: "#d9772a",
        },
        signal: {
          green: "#4ade80",
          red: "#f87171",
          blue: "#60a5fa",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(245, 148, 60, 0.25)",
      },
    },
  },
  plugins: [],
};

export default config;

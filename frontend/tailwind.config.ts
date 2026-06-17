import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        bg: "#09111a",
        panel: "#101c2a",
        panelAlt: "#132536",
        line: "#27445e",
        accent: "#ff8f3f",
        accentSoft: "#ffc287",
        ok: "#34d399",
        warn: "#fbbf24",
        danger: "#f87171",
        copy: "#e7eef6",
        muted: "#99aabd"
      },
      boxShadow: {
        panel: "0 18px 42px rgba(3, 10, 18, 0.35)"
      },
      fontFamily: {
        sans: ["Segoe UI", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;

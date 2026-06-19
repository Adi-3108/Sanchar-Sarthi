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
        bg: "#f5f7fb",
        panel: "#ffffff",
        panelAlt: "#eef4ff",
        line: "#c8d5e6",
        accent: "#0f5ea8",
        accentSoft: "#2f7ec2",
        ok: "#137a3d",
        warn: "#9a6700",
        danger: "#b42318",
        copy: "#172033",
        muted: "#5c6b80"
      },
      boxShadow: {
        panel: "0 14px 34px rgba(23, 32, 51, 0.10)"
      },
      fontFamily: {
        sans: ["Segoe UI", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;

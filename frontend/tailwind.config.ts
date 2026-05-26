import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0f1117",
          elevated: "#161b26",
          border: "#1e293b",
        },
        accent: {
          DEFAULT: "#3b82f6",
          muted: "#1d4ed8",
          glow: "#60a5fa",
        },
        success: "#22c55e",
        warning: "#eab308",
        error: "#ef4444",
      },
    },
  },
  plugins: [],
};

export default config;

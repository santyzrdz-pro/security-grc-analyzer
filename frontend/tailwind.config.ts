import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(222 47% 7%)",
        surface: "hsl(222 40% 11%)",
        "surface-2": "hsl(222 34% 15%)",
        border: "hsl(217 30% 22%)",
        muted: "hsl(215 20% 65%)",
        foreground: "hsl(210 40% 98%)",
        primary: "hsl(217 91% 60%)",
        "primary-foreground": "hsl(0 0% 100%)",
        success: "hsl(142 71% 45%)",
        warning: "hsl(38 92% 50%)",
        danger: "hsl(0 84% 60%)",
        critical: "hsl(0 72% 51%)",
      },
      borderRadius: {
        xl: "0.9rem",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Arial"],
      },
    },
  },
  plugins: [],
};

export default config;

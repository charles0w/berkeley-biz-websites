import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // Banned by design-taste-frontend / minimalist-ui / high-end-visual-design:
        // Inter, Roboto, Arial, Open Sans, Helvetica.
        // Substitutes loaded via globals.css from Google Fonts.
        display: ['"Newsreader"', "ui-serif", "Georgia", "serif"],
        body: ['"Plus Jakarta Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        // Back-compat alias: components that still reference font-heading keep working.
        heading: ['"Newsreader"', "ui-serif", "Georgia", "serif"],
      },
      colors: {
        cream: "#FDFBF7",
        paper: "#F5F1E8",
        ink: "#2F3437",
        // Editorial-luxury palette (high-end-visual-design archetype B):
        espresso: {
          DEFAULT: "#2C1810",
          soft: "#3D2418",
          ink: "#1A0F08",
        },
        sage: "#6B7B5E",
        mute: "#8A7A6B",
        stone: {
          50: "#FAFAF8",
          100: "#F5F1E8",
          200: "#E8E2D3",
          300: "#D0C8B4",
          400: "#A89E89",
          500: "#8A7A6B",
          600: "#605548",
          700: "#3D2418",
          800: "#2C1810",
          900: "#1A0F08",
        },
      },
      letterSpacing: {
        tightest: "-0.04em",
        "extra-wide": "0.16em",
        widest: "0.3em",
      },
      // Ultra-diffuse, low-opacity shadows only (banned: shadow-md/lg/xl per minimalist-ui).
      boxShadow: {
        "ambient-sm": "0 1px 2px rgba(44, 24, 16, 0.04), 0 2px 8px rgba(44, 24, 16, 0.03)",
        ambient: "0 4px 24px rgba(44, 24, 16, 0.04), 0 1px 3px rgba(44, 24, 16, 0.05)",
        "ambient-lg": "0 24px 48px -12px rgba(44, 24, 16, 0.05), 0 2px 8px rgba(44, 24, 16, 0.03)",
      },
      borderRadius: {
        sharp: "2px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.8s cubic-bezier(0.22, 1, 0.36, 1) both",
        "pulse-soft": "pulse-soft 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;

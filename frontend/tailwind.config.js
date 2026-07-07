/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Single clean family — minimal, portfolio-grade
        display: [
          '"Instrument Sans"',
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
        sans: ['"Instrument Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        // FIFA 2026 palette: near-monochrome black + white + GOLD (institutional).
        // Token names kept stable: pitch = deep brass-gold accent, gold = bright
        // trophy gold, electric = same gold family (legacy "away" usage).
        pitch: {
          50: "#faf7ee",
          100: "#f2e9cf",
          200: "#e6d29b",
          300: "#d7b968",
          400: "#c9a24b",
          500: "#b1863a",
          600: "#916b2c",
          700: "#785a27",
          800: "#5f471f",
          900: "#493716",
          950: "#2e230d",
        },
        gold: {
          50: "#fbf8ec",
          100: "#f7efd0",
          200: "#efdca0",
          300: "#e6c86f",
          400: "#dab84e",
          500: "#cda63c",
          600: "#b58a2f",
          700: "#8f6b28",
          800: "#6f5321",
          900: "#574019",
        },
        electric: {
          600: "#b58a2f",
          500: "#cda63c",
          400: "#dab84e",
        },
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pop-in": {
          "0%": { opacity: "0", transform: "scale(0.92)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
        "pop-in": "pop-in 0.35s cubic-bezier(0.22, 1, 0.36, 1) both",
      },
    },
  },
  plugins: [],
};

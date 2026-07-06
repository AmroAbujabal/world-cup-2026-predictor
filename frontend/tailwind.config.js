/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Russo One = bold sport/esport impact display; Chakra Petch = techy UI/body
        display: ['"Russo One"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Chakra Petch"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        // World Cup brand — pitch green, gold trophy, electric accent
        pitch: {
          950: "#032217",
          900: "#053825",
          800: "#065f36",
          700: "#047857",
          600: "#059669",
          500: "#10b981",
          400: "#34d399",
        },
        gold: {
          500: "#f59e0b",
          400: "#fbbf24",
          300: "#fcd34d",
        },
        electric: {
          600: "#2563eb",
          500: "#3b82f6",
          400: "#60a5fa",
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

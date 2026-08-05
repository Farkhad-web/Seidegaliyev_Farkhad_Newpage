/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b0e14",
          900: "#12161f",
          800: "#1a1f2b",
          700: "#242a38",
          600: "#333b4d",
          500: "#4b5468",
          400: "#6b7488",
          300: "#9aa2b3",
          200: "#c6cbd6",
          100: "#e8eaef",
        },
        brand: {
          500: "#6d5ef8",
          400: "#8b7ffa",
          300: "#a99cfc",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        blink: { "0%, 100%": { opacity: 1 }, "50%": { opacity: 0 } },
        fadeIn: { from: { opacity: 0, transform: "translateY(4px)" }, to: { opacity: 1, transform: "translateY(0)" } },
      },
      animation: {
        blink: "blink 1s steps(1) infinite",
        fadeIn: "fadeIn 0.2s ease-out",
      },
    },
  },
  plugins: [],
};

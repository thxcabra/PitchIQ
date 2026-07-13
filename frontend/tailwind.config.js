/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        pitch: {
          bg: "#0a0e1a",        // app background (deep)
          bg2: "#0d1220",       // subtle raised background
          card: "#111725",      // surface
          card2: "#161d2e",     // elevated / hover surface
          line: "#212a3e",      // subtle border
          line2: "#2c374f",     // stronger border
          accent: "#34d399",    // primary (football green)
          accent2: "#38bdf8",   // secondary (sky, comparisons/charts)
          text: "#e8edf5",
          sub: "#98a5bc",
          muted: "#5b6880",
        },
      },
      fontFamily: {
        sans: ["'Geist Variable'", "Geist", "system-ui", "sans-serif"],
        mono: ["'Geist Mono Variable'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.3), inset 0 0 0 1px rgba(255,255,255,0.03)",
        lift: "0 10px 30px -8px rgba(0,0,0,0.55), inset 0 0 0 1px rgba(52,211,153,0.28)",
        glow: "0 0 0 1px rgba(52,211,153,0.3), 0 6px 20px -4px rgba(52,211,153,0.15)",
      },
      keyframes: {
        "fade-up": { "0%": { opacity: 0, transform: "translateY(6px)" }, "100%": { opacity: 1, transform: "none" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: {
        "fade-up": "fade-up 240ms cubic-bezier(0.16,1,0.3,1) both",
      },
    },
  },
  plugins: [],
};

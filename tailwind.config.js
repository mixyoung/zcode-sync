/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: "var(--bg-canvas)",
        surface: "var(--bg-surface)",
        "surface-alt": "var(--bg-surface-alt)",
        "surface-hover": "var(--bg-surface-hover)",
        input: "var(--bg-input)",
        subtle: "var(--border-subtle)",
        "subtle-hover": "var(--border-subtle-hover)",
        primary: "var(--color-primary)",
        "primary-hover": "var(--color-primary-hover)",
        "badge-custom-bg": "var(--badge-custom-bg)",
        "badge-custom-border": "var(--badge-custom-border)",
        "badge-custom-text": "var(--badge-custom-text)",
        "badge-official-bg": "var(--badge-official-bg)",
        "badge-official-border": "var(--badge-official-border)",
        "badge-official-text": "var(--badge-official-text)",
      },
      textColor: {
        main: "var(--text-primary)",
        sub: "var(--text-secondary)",
        dim: "var(--text-muted)",
      },
      fontFamily: {
        sans: ["Segoe UI", "Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["Consolas", "Cascadia Mono", "JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}

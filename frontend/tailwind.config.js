/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'dc-bg': '#0a0e17',
        'dc-card': '#111827',
        'dc-border': '#1f2937',
        'dc-text': '#f3f4f6',
        'dc-text-secondary': '#9ca3af',
        'dc-primary': '#1a5f2a',
        'dc-secondary': '#2e7d32',
        'dc-accent': '#4caf50',
        'dc-danger': '#d32f2f',
        'dc-warning': '#f57c00',
        'dc-chart-grid': '#1f2937',
        'dc-yield-gross': '#4caf50',
        'dc-yield-net': '#2e7d32',
        'dc-cost-comm': '#f57c00',
        'dc-cost-tobin': '#d32f2f',
        'dc-cost-tax': '#7c3aed',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
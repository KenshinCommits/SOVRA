/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          dark: '#0f172a',
          panel: '#1e293b',
          border: '#334155',
          text: '#f8fafc',
          accent: '#38bdf8',
          success: '#22c55e',
          warning: '#eab308',
          error: '#ef4444'
        }
      }
    },
  },
  plugins: [],
}

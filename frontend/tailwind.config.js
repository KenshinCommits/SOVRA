/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
        display: ['"Space Grotesk"', 'sans-serif'],
      },
      colors: {
        industrial: {
          base: '#050505',
          panel: '#111111',
          surface: '#1a1a1a',
          border: '#333333',
          text: '#e0e0e0',
          muted: '#888888',
          accent: '#d97706', // Restrained amber
          accentHover: '#b45309',
          success: '#166534',
          successText: '#4ade80',
          warning: '#854d0e',
          warningText: '#facc15',
          error: '#7f1d1d',
          errorText: '#f87171'
        }
      }
    },
  },
  plugins: [],
}

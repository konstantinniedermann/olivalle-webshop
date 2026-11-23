/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './app/**/*.py',
    './static/js/neu.js',
  ],
  theme: {
    extend: {
      colors: {
        accent: '#f1d600',
        // Neues Kunden-Frontend (/neu) — ergänzt, bestehende Werte bleiben
        creme: '#FAF6EC',
        sand: '#F0E8D6',
        hain: { DEFAULT: '#25301A', 700: '#3A4A26', 500: '#6B7F3F', 200: '#C9D3B0' },
        oel: { DEFAULT: '#C9A227', hell: '#EBD27A' },
        terra: '#B8482B',
      },
      fontFamily: {
        display: ['"Amatic SC"', 'cursive'],
        body: ['Lora', 'serif'],
        titel: ['Fraunces', 'Georgia', 'serif'],
        text: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

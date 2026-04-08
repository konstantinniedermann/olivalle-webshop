/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './app/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        accent: '#f1d600',
      },
      fontFamily: {
        display: ['"Amatic SC"', 'cursive'],
        body: ['Lora', 'serif'],
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: '#18110c',
          subtle: '#241710',
          darkSurface: '#2b1c13',
          panel: '#fdfbf7',
          panelSubtle: '#f7f2ea',
          border: '#3d291d',
          borderCard: '#d8cbb8',
          primary: '#f25c24',
          primaryHover: '#d94c17',
          gold: '#d97706',
          text: '#1e140f',
          textInverse: '#fbf8f2',
          textMuted: '#786558',
          textMutedInverse: '#a08c7e',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}

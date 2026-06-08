/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-jakarta)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'Georgia', 'serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      colors: {
        stone: {
          25: '#fdfcfb',
        },
      },
      boxShadow: {
        'ambient': '0 4px 24px 0 rgba(0,0,0,0.06), 0 1px 4px 0 rgba(0,0,0,0.04)',
        'ambient-md': '0 6px 32px 0 rgba(0,0,0,0.07), 0 2px 6px 0 rgba(0,0,0,0.04)',
        'ambient-lg': '0 10px 56px 0 rgba(0,0,0,0.09), 0 3px 10px 0 rgba(0,0,0,0.05)',
      },
    },
  },
  plugins: [],
}

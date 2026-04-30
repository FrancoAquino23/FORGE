/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        forge: {
          bg:      '#080b0e',
          surface: '#0f1318',
          card:    '#141920',
          border:  '#1e2a35',
          primary: '#f59e0b',
          dim:     '#b45309',
          text:    '#e2e8f0',
          muted:   '#64748b',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out forwards',
      },
      keyframes: {
        slideIn: {
          from: { transform: 'translateX(110%)', opacity: '0' },
          to:   { transform: 'translateX(0)',    opacity: '1' },
        },
      },
      boxShadow: {
        forge:    '0 0 24px rgba(245,158,11,0.12)',
        'forge-lg': '0 0 48px rgba(245,158,11,0.22)',
      },
    },
  },
  plugins: [],
};

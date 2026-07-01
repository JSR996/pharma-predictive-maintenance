/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#EEF4FB',  // blue-tinted cleanroom page
        surface:  '#FFFFFF',  // white cards
        surface2: '#F1F5FB',  // inner fill: pills, tracks, badges
        border:   '#DBE7F3',  // hairline borders
        brand:    '#1D4ED8',  // brand / UI accent (pharma blue)
        critical: '#DC2626',
        warning:  '#B45309',  // AA-legible amber for text; graphics use #D97706
        normal:   '#16A34A',  // healthy status (green)
        muted:    '#94A3B8',
        text:     '#12233B',  // navy ink
        subtext:  '#5B7089',  // muted label
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body:    ['Inter', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      zIndex: {
        // Semantic scale — no arbitrary 999s.
        dropdown: '10',
        sticky:   '20',
        overlay:  '30',
        modal:    '40',
        toast:    '50',
        tooltip:  '60',
      },
    },
  },
  plugins: [],
}

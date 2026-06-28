/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#0A0E1A',
        surface:  '#111827',
        surface2: '#1F2937',
        border:   '#374151',
        teal:     '#00D4AA',
        critical: '#EF4444',
        warning:  '#F59E0B',
        normal:   '#00D4AA',
        muted:    '#6B7280',
        text:     '#F9FAFB',
        subtext:  '#9CA3AF',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body:    ['Inter', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}

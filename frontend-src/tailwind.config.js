/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        canvas:  '#0c0e17',
        surface: '#13161f',
        edge:    '#1a1d2e',
        ridge:   '#232740',
        indigo: {
          50: '#ebf5fb',
          100: '#d6eaf8',
          200: '#aed6f1',
          300: '#85c1e9',
          400: '#3498DB', // Primary Sky Blue
          500: '#2980B9',
          600: '#2471a3',
          700: '#1f618d',
          800: '#1a5276',
          900: '#154360',
        },
        violet: {
          50: '#fefde8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#F1C40F', // Secondary Sunshine Yellow
          500: '#d4ac0d',
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        }
      },
      boxShadow: {
        card: '0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04)',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(-6px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        fadeUp: 'fadeUp 0.22s ease forwards',
        fadeIn: 'fadeIn 0.2s ease forwards',
      },
      backgroundImage: {
        'mesh-dark': "radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,0.2) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,0.2) 0, transparent 50%)",
      }
    },
  },
  plugins: [],
}

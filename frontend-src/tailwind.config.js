/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Merriweather', 'serif'], // Added a serif for elegant library typography
      },
      colors: {
        canvas:  '#f8f9fa', // Soft off-white paper background
        surface: '#ffffff', // Pure white cards
        edge:    '#e9ecef', // Light grey borders
        ridge:   '#dee2e6', // Slightly darker borders
        primary: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#627d98', // Soft slate blue
          600: '#486581',
          700: '#334e68',
          800: '#243b53',
          900: '#102a43', // Deep navy for headings
        },
        accent: {
          50: '#fdf3ea',
          100: '#fbe2c7',
          200: '#f8cda0',
          300: '#f5b575',
          400: '#f29c49',
          500: '#ef821d', // Warm orange/sepia highlight
          600: '#cf6c12',
          700: '#aa550d',
          800: '#84400a',
          900: '#612d08',
        }
      },
      boxShadow: {
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        floating: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
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
        'mesh-light': "radial-gradient(at 0% 0%, rgba(239,130,29,0.05) 0, transparent 50%), radial-gradient(at 100% 0%, rgba(98,125,152,0.05) 0, transparent 50%)",
      }
    },
  },
  plugins: [],
}

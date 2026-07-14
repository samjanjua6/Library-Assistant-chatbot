import { motion } from 'framer-motion'
import { useTheme } from '../contexts/ThemeContext'

const SunIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </svg>
)

const MoonIcon = () => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
)

/**
 * ThemeToggle — an animated pill switch (moon ↔ sun).
 * The thumb slides on a spring; icons fade in/out.
 */
export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  return (
    <motion.button
      onClick={toggle}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="relative flex items-center w-14 h-7 rounded-full cursor-pointer shrink-0"
      style={{
        background: 'var(--glass-bg)',
        border: '1px solid var(--border)',
        backdropFilter: 'blur(12px)',
      }}
    >
      {/* Sliding thumb */}
      <motion.div
        animate={{ x: isDark ? 2 : 30 }}
        transition={{ type: 'spring', stiffness: 350, damping: 25 }}
        className="absolute w-5 h-5 rounded-full flex items-center justify-center text-white"
        style={{
          background: 'linear-gradient(135deg, #3498DB, #2980B9)',
          boxShadow: '0 2px 8px rgba(52, 152, 219, 0.5)',
        }}
      >
        <motion.span
          initial={false}
          animate={{ opacity: 1, rotate: isDark ? 0 : 180 }}
          transition={{ duration: 0.25 }}
        >
          {isDark ? <MoonIcon /> : <SunIcon />}
        </motion.span>
      </motion.div>

      {/* Track icons (dim) */}
      <span className="absolute left-[6px] opacity-30 pointer-events-none" style={{ color: 'var(--text-1)' }}>
        <MoonIcon />
      </span>
      <span className="absolute right-[6px] opacity-30 pointer-events-none" style={{ color: 'var(--text-1)' }}>
        <SunIcon />
      </span>
    </motion.button>
  )
}

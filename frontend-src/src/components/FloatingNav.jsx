import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Code, Globe } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

// Reusable glass style object (works in both themes via CSS vars)
const glass = {
  background:    'var(--glass-bg)',
  border:        '1px solid var(--border)',
  
  
}

export default function FloatingNav() {
  return (
    <motion.nav
      initial={{ y: -60, x: '-50%', opacity: 0 }}
      animate={{ y: 0, x: '-50%', opacity: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 22, delay: 0.1 }}
      style={{ ...glass, boxShadow: 'var(--shadow)' }}
      className="fixed top-5 left-1/2 z-50 flex items-center justify-between px-5 py-2.5 rounded-full w-[92%] max-w-4xl"
    >
      {/* Brand */}
      <div className="flex items-center gap-2.5">
        <span className="text-xl leading-none" aria-hidden>⚡</span>
        <span
          className="text-lg font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent"
        >
          Zylo
        </span>
      </div>

      {/* Links */}
      <div className="hidden md:flex items-center gap-7 text-sm font-medium" style={{ color: 'var(--text-primary-700)' }}>
        <a href="#features" className="hover:opacity-100 transition-opacity" style={{ color: 'var(--text-primary-700)' }}>Features</a>
        <a href="#tech"     className="hover:opacity-100 transition-opacity" style={{ color: 'var(--text-primary-700)' }}>Tech</a>
        <a href="#security" className="hover:opacity-100 transition-opacity" style={{ color: 'var(--text-primary-700)' }}>Security</a>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Social icons */}
        <div className="hidden sm:flex items-center gap-3 pr-3" style={{ borderRight: '1px solid var(--border)' }}>
          <a href="#" style={{ color: 'var(--text-primary-700)' }} className="hover:opacity-80 transition-opacity"><Code size={17} /></a>
          <a href="#" style={{ color: 'var(--text-primary-700)' }} className="hover:opacity-80 transition-opacity"><Globe size={17} /></a>
        </div>

        <ThemeToggle />

        <Link to="/login">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            style={{ ...glass, color: 'var(--text-primary-900)' }}
            className="px-4 py-1.5 rounded-full text-sm font-semibold"
          >
            Launch App
          </motion.button>
        </Link>
      </div>
    </motion.nav>
  )
}

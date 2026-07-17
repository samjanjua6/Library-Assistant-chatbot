import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowRight, Shield, Zap } from 'lucide-react'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.14, delayChildren: 0.3 }
  }
}

const itemVariants = {
  hidden:   { opacity: 0, y: 28 },
  visible:  { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 14 } }
}

const glass = {
  background:    'var(--glass-bg)',
  border:        '1px solid var(--border)',
  backdropFilter:'blur(16px)',
  WebkitBackdropFilter: 'blur(16px)',
}

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center pt-28 pb-16 overflow-hidden px-6">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-4xl mx-auto text-center flex flex-col items-center"
      >
        {/* Live badge */}
        <motion.div
          variants={itemVariants}
          style={{ ...glass }}
          className="mb-8 flex items-center gap-2 px-4 py-1.5 rounded-full"
        >
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-medium tracking-wide uppercase" style={{ color: 'var(--text-2)' }}>
            Zylo v2.1 with CI/CD is LIVE! 🚀
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          variants={itemVariants}
          className="text-6xl md:text-8xl font-bold tracking-tighter mb-6 leading-[1.05]"
          style={{ color: 'var(--text-1)' }}
        >
          Manage your books with{' '}
          <br />
          <span className="bg-gradient-to-br from-indigo-400 via-violet-400 to-violet-500 bg-clip-text text-transparent">
            Zylo Library AI.
          </span>
        </motion.h1>

        {/* Sub-head */}
        <motion.p
          variants={itemVariants}
          className="text-lg md:text-xl max-w-2xl mb-12 font-light leading-relaxed"
          style={{ color: 'var(--text-2)' }}
        >
          Your personal Library Book Assistant. Search the catalog, check availability, borrow, and return books seamlessly through natural conversation.
        </motion.p>

        {/* CTAs */}
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-center gap-4">
          <Link to="/login">
            <motion.button
              whileHover={{ scale: 1.02, opacity: 0.92 }}
              whileTap={{ scale: 0.98 }}
              className="group flex items-center gap-2 px-8 py-4 rounded-2xl font-semibold text-white"
              style={{ background: 'linear-gradient(135deg, #3498DB, #2980B9)', boxShadow: '0 4px 20px rgba(52, 152, 219, 0.35)' }}
            >
              Start Chatting
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </motion.button>
          </Link>

          <a href="https://github.com/samjanjua6/zylo-fast-api/tree/main" target="_blank" rel="noreferrer">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              style={{ ...glass, color: 'var(--text-1)' }}
              className="flex items-center gap-2 px-8 py-4 rounded-2xl font-medium"
            >
              View on GitHub
            </motion.button>
          </a>
        </motion.div>

        {/* Feature pills */}
        <motion.div variants={itemVariants} className="mt-24 grid grid-cols-1 sm:grid-cols-3 gap-5 w-full max-w-2xl">
          {[
            { icon: <Zap size={18} className="text-amber-400" />, label: 'Real-time via WebSocket' },
            { icon: <Shield size={18} className="text-indigo-400" />, label: 'JWT Authenticated' },
            { icon: <span className="text-lg">✨</span>, label: 'Glassmorphism UI' },
          ].map((item, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.03, boxShadow: 'var(--shadow)' }}
              style={{ ...glass }}
              className="flex flex-col items-center gap-3 p-6 rounded-3xl cursor-default"
            >
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ background: 'var(--glass-hi)', border: '1px solid var(--border)' }}
              >
                {item.icon}
              </div>
              <p className="text-sm font-semibold" style={{ color: 'var(--text-1)' }}>{item.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </section>
  )
}

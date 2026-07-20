import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import LoginForm from '../components/LoginForm'
import SignupForm from '../components/SignupForm'
import ThemeToggle from '../components/ThemeToggle'

const glass = {
  background:    'var(--glass-bg)',
  border:        '1px solid var(--border)',
  backdropFilter:'blur(24px)',
  WebkitBackdropFilter: 'blur(24px)',
  boxShadow:     'var(--shadow)',
}

function SegmentedControl({ mode, onChange }) {
  return (
    <div
      role="tablist"
      className="flex p-1 rounded-xl mb-7"
      style={{ background: 'var(--glass-input)', border: '1px solid var(--border-s)' }}
    >
      {['login', 'signup'].map((m) => (
        <button
          key={m}
          role="tab"
          aria-selected={mode === m}
          onClick={() => onChange(m)}
          className="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200 relative"
          style={{ color: mode === m ? 'var(--text-1)' : 'var(--text-2)' }}
        >
          {mode === m && (
            <motion.span
              layoutId="pill-active"
              className="absolute inset-0 rounded-lg"
              style={{ background: 'var(--pill-active)' }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            />
          )}
          <span className="relative z-10">{m === 'login' ? 'Sign In' : 'Sign Up'}</span>
        </button>
      ))}
    </div>
  )
}

function Alert({ alert }) {
  if (!alert) return null
  const isSuccess = alert.type === 'success'
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      role="alert"
      className="mb-5 px-4 py-3 rounded-xl text-sm border"
      style={{
        background: isSuccess ? 'rgba(52,211,153,0.08)' : 'rgba(239,68,68,0.08)',
        borderColor: isSuccess ? 'rgba(52,211,153,0.2)' : 'rgba(239,68,68,0.2)',
        color: isSuccess ? '#34d399' : '#f87171',
      }}
    >
      {alert.message}
    </motion.div>
  )
}

export default function AuthPage() {
  const [mode, setMode] = useState('login')
  const [alert, setAlert] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (localStorage.getItem('zylo_token')) {
      navigate('/chat', { replace: true })
    }
  }, [navigate])

  if (localStorage.getItem('zylo_token')) {
    return null
  }

  function handleModeChange(next) { setAlert(null); setMode(next) }

  function handleLoginSuccess(data) {
    localStorage.setItem('zylo_token', data.access_token)
    localStorage.setItem('zylo_username', data.user.username)
    navigate('/chat', { replace: true })
  }

  function handleSignupSuccess(username) {
    setAlert({ type: 'success', message: `✓ Account "${username}" created — sign in now.` })
    setMode('login')
  }

  function handleGoogleLogin() {
    window.location.href = '/auth/google/login'
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Theme toggle (fixed top-right) */}
      <div className="fixed top-5 right-5 z-50">
        <ThemeToggle />
      </div>

      <div className="relative w-full max-w-sm">
        {/* Brand */}
        <motion.header
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 150, damping: 15 }}
          className="flex items-center justify-center gap-2.5 mb-7"
        >
          <span className="text-2xl leading-none" aria-hidden>⚡</span>
          <span className="text-[1.65rem] font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent tracking-tight">
            Zylo
          </span>
        </motion.header>

        {/* Card */}
        <motion.main
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 120, damping: 14, delay: 0.1 }}
          style={glass}
          className="rounded-3xl p-8"
        >
          <SegmentedControl mode={mode} onChange={handleModeChange} />

          <Alert alert={alert} />

          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, x: mode === 'login' ? -12 : 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: mode === 'login' ? 12 : -12 }}
              transition={{ duration: 0.18 }}
            >
              {mode === 'login' ? (
                <LoginForm
                  onSuccess={handleLoginSuccess}
                  onError={(msg) => setAlert({ type: 'error', message: msg })}
                />
              ) : (
                <SignupForm
                  onSuccess={handleSignupSuccess}
                  onError={(msg) => setAlert({ type: 'error', message: msg })}
                />
              )}
            </motion.div>
          </AnimatePresence>

          {/* ── Divider ── */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px" style={{ background: 'var(--border)' }} />
            <span className="text-xs font-medium" style={{ color: 'var(--text-3)' }}>or</span>
            <div className="flex-1 h-px" style={{ background: 'var(--border)' }} />
          </div>

          {/* ── Google Sign-In ── */}
          <motion.button
            onClick={handleGoogleLogin}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors"
            style={{
              background: 'var(--glass-input)',
              border: '1px solid var(--border)',
              color: 'var(--text-1)',
            }}
          >
            {/* Google "G" SVG */}
            <svg width="18" height="18" viewBox="0 0 48 48">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              <path fill="none" d="M0 0h48v48H0z"/>
            </svg>
            Continue with Google
          </motion.button>
        </motion.main>

        <p className="text-center text-xs mt-5" style={{ color: 'var(--text-3)' }}>
          Secured with JWT · Powered by FastAPI
        </p>
      </div>
    </div>
  )
}

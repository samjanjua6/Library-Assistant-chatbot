import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import LoginForm from '../components/LoginForm'
import SignupForm from '../components/SignupForm'

/** Segmented pill control — switches between Login and Signup states */
function SegmentedControl({ mode, onChange }) {
  const base =
    'flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200 cursor-pointer'
  const active = 'bg-ridge text-slate-100'
  const inactive = 'text-slate-500 hover:text-slate-300'

  return (
    <div
      role="tablist"
      className="flex bg-canvas border border-edge rounded-xl p-1 mb-8"
    >
      <button
        role="tab"
        aria-selected={mode === 'login'}
        onClick={() => onChange('login')}
        className={`${base} ${mode === 'login' ? active : inactive}`}
      >
        Sign In
      </button>
      <button
        role="tab"
        aria-selected={mode === 'signup'}
        onClick={() => onChange('signup')}
        className={`${base} ${mode === 'signup' ? active : inactive}`}
      >
        Sign Up
      </button>
    </div>
  )
}

/** Inline status banner — shown above the form when something happens */
function Alert({ alert }) {
  if (!alert) return null
  const styles =
    alert.type === 'success'
      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
      : 'bg-red-500/10 border-red-500/20 text-red-300'
  return (
    <div
      role="alert"
      className={`mb-5 px-4 py-3 rounded-xl text-sm border ${styles} animate-[fadeIn_0.2s_ease]`}
    >
      {alert.message}
    </div>
  )
}

/**
 * AuthPage
 *
 * Design decisions:
 * - Only ONE form is ever visible at a time — driven by `mode` state.
 * - Toggle is a segmented pill at the top of the card (no hidden tabs).
 * - The accent gradient is reserved exclusively for the CTA submit button.
 * - Card sits on a deep canvas; it has a slightly lighter background + edge border.
 * - Inputs are bare (transparent-dark bg, subtle border, indigo focus ring).
 */
export default function AuthPage() {
  const [mode, setMode] = useState('login')
  const [alert, setAlert] = useState(null)
  const navigate = useNavigate()

  // Redirect if already logged in
  if (localStorage.getItem('zylo_token')) {
    navigate('/chat', { replace: true })
    return null
  }

  function handleModeChange(next) {
    setAlert(null)
    setMode(next)
  }

  function handleLoginSuccess(data) {
    localStorage.setItem('zylo_token', data.access_token)
    localStorage.setItem('zylo_username', data.user.username)
    navigate('/chat', { replace: true })
  }

  function handleSignupSuccess(username) {
    setAlert({
      type: 'success',
      message: `✓ Account "${username}" created — sign in now.`,
    })
    setMode('login')
  }

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-4 relative overflow-hidden">
      {/* Subtle ambient glow — does not dominate */}
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute -top-48 -left-48 w-[500px] h-[500px] rounded-full bg-indigo-600/8 blur-3xl" />
        <div className="absolute -bottom-48 -right-32 w-[400px] h-[400px] rounded-full bg-violet-600/6 blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        {/* ── Brand mark ── */}
        <header className="flex items-center justify-center gap-2.5 mb-8">
          <span className="text-2xl leading-none" aria-hidden>⚡</span>
          <span className="text-[1.6rem] font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent tracking-tight">
            Zylo
          </span>
        </header>

        {/* ── Auth card ── */}
        <main className="bg-surface border border-edge rounded-2xl p-8 shadow-card">
          <SegmentedControl mode={mode} onChange={handleModeChange} />

          <Alert alert={alert} />

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
        </main>

        {/* ── Footer note ── */}
        <p className="text-center text-xs text-slate-700 mt-5">
          Secured with JWT · Powered by FastAPI
        </p>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { apiPost } from '../lib/api'
import InputField from './InputField'
import SubmitButton from './SubmitButton'

/**
 * SignupForm
 *
 * Props:
 *   onSuccess(username) — called with the new username on successful registration
 *   onError(message)    — called with an error string on failure
 */
export default function SignupForm({ onSuccess, onError }) {
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    setLoading(true)
    try {
      const data = await apiPost('/signup', {
        username: fd.get('username'),
        email: fd.get('email'),
        password: fd.get('password'),
      })
      onSuccess(data.username)
    } catch (err) {
      onError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <InputField
        id="signup-username"
        name="username"
        type="text"
        label="Username"
        placeholder="alice"
        autoComplete="username"
        required
        minLength={3}
        maxLength={50}
      />
      <InputField
        id="signup-email"
        name="email"
        type="email"
        label="Email"
        placeholder="alice@example.com"
        autoComplete="email"
        required
      />
      <InputField
        id="signup-password"
        name="password"
        type="password"
        label={
          <span className="flex items-baseline gap-2">
            Password
            <span className="text-xs text-slate-600 font-normal">min. 6 characters</span>
          </span>
        }
        placeholder="Create a strong password"
        autoComplete="new-password"
        required
        minLength={6}
      />
      <SubmitButton loading={loading}>Create Account</SubmitButton>
    </form>
  )
}

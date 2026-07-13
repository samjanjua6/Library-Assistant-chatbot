import { useState } from 'react'
import { apiPost } from '../lib/api'
import InputField from './InputField'
import SubmitButton from './SubmitButton'

/**
 * LoginForm
 *
 * Props:
 *   onSuccess(data)  — called with the full token response when login succeeds
 *   onError(message) — called with an error string on failure
 */
export default function LoginForm({ onSuccess, onError }) {
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    setLoading(true)
    try {
      const data = await apiPost('/login', {
        username_or_email: fd.get('username_or_email'),
        password: fd.get('password'),
      })
      onSuccess(data)
    } catch (err) {
      onError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <InputField
        id="login-identifier"
        name="username_or_email"
        type="text"
        label="Username or email"
        placeholder="alice or alice@example.com"
        autoComplete="username"
        required
      />
      <InputField
        id="login-password"
        name="password"
        type="password"
        label="Password"
        placeholder="Your password"
        autoComplete="current-password"
        required
      />
      <SubmitButton loading={loading}>Sign In</SubmitButton>
    </form>
  )
}

import { useRef } from 'react'

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

export default function ChatInput({ onSend, disabled, isStreaming }) {
  const inputRef = useRef(null)

  function handleSubmit(e) {
    e.preventDefault()
    const text = inputRef.current?.value.trim()
    if (!text) return
    onSend(text)
    inputRef.current.value = ''
    inputRef.current.focus()
  }

  const isLocked = disabled || isStreaming
  const placeholder = disabled ? 'Connecting…' : isStreaming ? 'Zylo AI is thinking…' : 'Type your message here…'

  return (
    <footer
      className="shrink-0 px-6 pb-6 pt-3"
      style={{ borderTop: '1px solid var(--border)', background: 'var(--glass-bg)', backdropFilter: 'blur(20px)' }}
    >
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 px-5 py-2 rounded-2xl transition-all duration-150"
        style={{
          background:  'var(--glass-input)',
          border:      '1px solid var(--border)',
          backdropFilter: 'blur(16px)',
        }}
        onFocusCapture={e => e.currentTarget.style.borderColor = 'rgba(52,152,219,0.45)'}
        onBlurCapture={e =>  e.currentTarget.style.borderColor = 'var(--border)'}
      >
        <input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          disabled={isLocked}
          maxLength={2000}
          aria-label="Message input"
          className="flex-1 bg-transparent outline-none text-sm disabled:cursor-not-allowed"
          style={{
            color: 'var(--text-1)',
          }}
        />
        <button
          type="submit"
          disabled={isLocked}
          aria-label="Send message"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-white shrink-0 transition-all duration-150 hover:opacity-85 hover:scale-105 active:scale-100 disabled:opacity-30 disabled:cursor-not-allowed"
          style={{ background: 'linear-gradient(135deg,#3498DB,#2980B9)', boxShadow: '0 2px 12px rgba(52,152,219,0.4)' }}
        >
          <SendIcon />
        </button>
      </form>
      <p className="text-center text-xs mt-2.5" style={{ color: 'var(--text-3)' }}>
        Secured with JWT · Real-time via WebSocket
      </p>
    </footer>
  )
}

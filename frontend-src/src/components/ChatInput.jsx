import { useRef } from 'react'

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

export default function ChatInput({ onSend, disabled }) {
  const inputRef = useRef(null)

  function handleSubmit(e) {
    e.preventDefault()
    const text = inputRef.current?.value.trim()
    if (!text) return
    onSend(text)
    inputRef.current.value = ''
    inputRef.current.focus()
  }

  return (
    <footer className="shrink-0 px-6 pb-6 pt-3 bg-surface border-t border-edge">
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 bg-canvas border border-edge rounded-2xl px-5 py-2 focus-within:border-indigo-500/40 focus-within:ring-2 focus-within:ring-indigo-500/8 transition-all duration-150"
      >
        <input
          ref={inputRef}
          type="text"
          placeholder={disabled ? 'Connecting…' : 'Send a message…'}
          disabled={disabled}
          maxLength={2000}
          aria-label="Message input"
          className="flex-1 bg-transparent outline-none text-sm text-slate-100 placeholder-slate-600 py-2 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={disabled}
          aria-label="Send message"
          className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-white shrink-0 shadow-[0_2px_12px_rgba(99,102,241,0.4)] hover:opacity-85 hover:scale-105 active:scale-100 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-150"
        >
          <SendIcon />
        </button>
      </form>
      <p className="text-center text-xs text-slate-700 mt-2.5">
        Secured with JWT · Real-time via WebSocket
      </p>
    </footer>
  )
}

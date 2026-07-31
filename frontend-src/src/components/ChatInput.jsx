import { useRef, useState } from 'react'

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

const PaperclipIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
  </svg>
)

const MAX_BYTES = 20 * 1024 * 1024   // 20 MB
const ALLOWED_EXTS = new Set(['.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx', '.json'])

export default function ChatInput({ onSend, disabled, isStreaming, onFileUpload, sessionId }) {
  const inputRef  = useRef(null)
  const fileRef   = useRef(null)
  const [fileErr, setFileErr] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const text = inputRef.current?.value.trim()
    if (!text) return
    onSend(text)
    inputRef.current.value = ''
    inputRef.current.focus()
  }

  function handleFileClick() {
    if (!sessionId) {
      setFileErr('Start a chat session first before uploading a file.')
      setTimeout(() => setFileErr(''), 3500)
      return
    }
    setFileErr('')
    fileRef.current?.click()
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    // Reset so the same file can be re-selected if needed
    e.target.value = ''

    // Client-side guards (server also validates)
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTS.has(ext)) {
      setFileErr(`File type "${ext}" is not allowed.`)
      setTimeout(() => setFileErr(''), 4000)
      return
    }
    if (file.size > MAX_BYTES) {
      setFileErr(`File too large (${(file.size / 1e6).toFixed(1)} MB). Max is 20 MB.`)
      setTimeout(() => setFileErr(''), 4000)
      return
    }

    setFileErr('')
    if (onFileUpload) onFileUpload(file)
  }

  const isLocked = disabled || isStreaming
  const placeholder = disabled ? 'Connecting…' : isStreaming ? 'Zylo AI is thinking…' : 'Type your message here…'

  return (
    <footer
      className="shrink-0 px-6 pb-6 pt-3"
      style={{ borderTop: '1px solid var(--border)', background: 'var(--glass-bg)',  }}
    >
      {fileErr && (
        <p className="text-xs text-rose-400 text-center mb-2 animate-pulse">{fileErr}</p>
      )}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 px-5 py-2 rounded-2xl transition-all duration-150"
        style={{
          background:  'var(--glass-input)',
          border:      '1px solid var(--border)',
          
        }}
        onFocusCapture={e => e.currentTarget.style.borderColor = 'rgba(52,152,219,0.45)'}
        onBlurCapture={e =>  e.currentTarget.style.borderColor = 'var(--border)'}
      >
        {/* Hidden file input */}
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.json,.pptx"
          onChange={handleFileChange}
          aria-label="Upload file"
        />

        {/* Paperclip button */}
        <button
          type="button"
          onClick={handleFileClick}
          disabled={isLocked}
          title="Attach a file (PDF, DOCX, TXT, MD, CSV, XLSX, JSON — max 20 MB)"
          aria-label="Attach file"
          className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 transition-all duration-150 hover:opacity-85 hover:scale-105 active:scale-100 disabled:opacity-30 disabled:cursor-not-allowed"
          style={{ background: 'var(--glass-hi)', border: '1px solid var(--border)', color: 'var(--text-primary-700)' }}
        >
          <PaperclipIcon />
        </button>

        <input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          disabled={isLocked}
          maxLength={2000}
          aria-label="Message input"
          className="flex-1 bg-transparent outline-none text-sm disabled:cursor-not-allowed"
          style={{
            color: 'var(--text-primary-900)',
          }}
        />
        <button
          type="submit"
          disabled={isLocked}
          aria-label="Send message"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-primary-900 shrink-0 transition-all duration-150 hover:opacity-85 hover:scale-105 active:scale-100 disabled:opacity-30 disabled:cursor-not-allowed"
          style={{ background: 'linear-gradient(135deg,#3498DB,#2980B9)', boxShadow: '0 2px 12px rgba(52,152,219,0.4)' }}
        >
          <SendIcon />
        </button>
      </form>
      <p className="text-center text-xs mt-2.5" style={{ color: 'var(--text-primary-500)' }}>
        Secured with JWT · Real-time via WebSocket
      </p>
    </footer>
  )
}

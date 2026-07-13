import { useEffect, useRef } from 'react'

function BotIntro() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 text-center py-16 gap-4">
      <div className="text-5xl leading-none" aria-hidden>🤖</div>
      <h1 className="text-lg font-semibold text-slate-200">Zylo AI Bot</h1>
      <p className="text-sm text-slate-500 max-w-xs">
        Your authenticated assistant is ready. Send a message to start.
      </p>
    </div>
  )
}

function Message({ msg, username }) {
  if (msg.type === 'system') {
    return (
      <div className="flex justify-center">
        <span className="text-xs text-slate-600 border border-edge rounded-lg px-3 py-1.5">
          {msg.text}
        </span>
      </div>
    )
  }

  const isUser = msg.type === 'user'
  const initial = username.charAt(0).toUpperCase()

  return (
    <div className={`flex items-end gap-2.5 ${isUser ? 'flex-row-reverse' : ''} animate-[fadeUp_0.2s_ease]`}>
      {/* Avatar */}
      <div
        className={[
          'w-7 h-7 rounded-full flex items-center justify-center text-xs shrink-0 font-semibold',
          isUser
            ? 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white uppercase'
            : 'bg-[#1a1d2e] border border-edge text-base',
        ].join(' ')}
        aria-hidden
      >
        {isUser ? initial : '🤖'}
      </div>

      {/* Bubble */}
      <div
        className={[
          'max-w-[70%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed',
          isUser
            ? 'bg-indigo-500/20 border border-indigo-500/20 text-indigo-100 rounded-br-sm'
            : 'bg-surface border border-edge text-slate-200 rounded-bl-sm',
        ].join(' ')}
      >
        {msg.text}
      </div>
    </div>
  )
}

export default function MessageList({ messages, username }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <main
      className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-3"
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
    >
      {messages.length === 0 ? (
        <BotIntro />
      ) : (
        messages.map((msg) => (
          <Message key={msg.id} msg={msg} username={username} />
        ))
      )}
      <div ref={bottomRef} />
    </main>
  )
}

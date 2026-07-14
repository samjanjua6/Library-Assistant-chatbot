import { useEffect, useRef } from 'react'

function formatMessageText(text) {
  if (!text) return '';
  
  // Split by newlines
  const lines = text.split('\n');
  
  return lines.map((line, index) => {
    let cleanLine = line.trim();
    let isBullet = false;
    
    // Check for bullet point (* or -)
    if (cleanLine.startsWith('*') || cleanLine.startsWith('-')) {
      isBullet = true;
      // Remove the bullet prefix
      cleanLine = cleanLine.replace(/^[*+-]\s*/, '');
    }
    
    // Parse bold text (**text**)
    const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
    const content = parts.map((part, pIdx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={pIdx} className="font-bold">{part.slice(2, -2)}</strong>;
      }
      return part;
    });

    if (isBullet) {
      return (
        <div key={index} className="flex gap-2 items-start mt-1 pl-2">
          <span className="text-indigo-400 select-none">•</span>
          <span className="flex-1">{content}</span>
        </div>
      );
    }
    
    return (
      <p key={index} className={cleanLine === '' ? 'h-2' : ''}>
        {content}
      </p>
    );
  });
}

function BotIntro() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 text-center py-16 gap-4">
      <div className="text-5xl leading-none" aria-hidden>🤖</div>
      <h1 className="text-lg font-semibold" style={{ color: 'var(--text-1)' }}>Zylo English Learning AI</h1>
      <p className="text-sm max-w-xs" style={{ color: 'var(--text-2)' }}>
        Your personal English language tutor is ready. Send a message to start practicing.
      </p>
    </div>
  )
}

function Message({ msg, username }) {
  if (msg.type === 'system') {
    return (
      <div className="flex justify-center">
        <span
          className="text-xs rounded-lg px-3 py-1.5"
          style={{ color: 'var(--text-2)', border: '1px solid var(--border)', background: 'var(--glass-bg)' }}
        >
          {msg.text}
        </span>
      </div>
    )
  }

  const isUser = msg.type === 'user'
  const initial = username.charAt(0).toUpperCase()

  return (
    <div className={`flex items-end gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-xs shrink-0 font-semibold"
        style={
          isUser
            ? { background: 'linear-gradient(135deg,#3498DB,#2980B9)', color: '#fff' }
            : { background: 'var(--glass-hi)', border: '1px solid var(--border)', color: 'var(--text-1)', fontSize: '1rem' }
        }
        aria-hidden
      >
        {isUser ? initial.toUpperCase() : '🤖'}
      </div>

      {/* Bubble */}
      <div
        className="max-w-[70%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed space-y-1"
        style={
          isUser
            ? {
                background:  'rgba(52,152,219,0.18)',
                border:      '1px solid rgba(52,152,219,0.25)',
                color:       'var(--text-1)',
                borderBottomRightRadius: '4px',
              }
            : {
                background:  'var(--glass-bg)',
                backdropFilter: 'blur(12px)',
                border:      '1px solid var(--border)',
                color:       'var(--text-1)',
                borderBottomLeftRadius: '4px',
              }
        }
      >
        {formatMessageText(msg.text)}
        {/* Blinking cursor while streaming */}
        {msg.streaming && (
          <span className="inline-block w-0.5 h-3.5 ml-0.5 align-middle rounded-sm animate-pulse" style={{ background: 'var(--text-2)' }} />
        )}
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
      {messages.length === 0 ? <BotIntro /> : messages.map(msg => (
        <Message key={msg.id} msg={msg} username={username} />
      ))}
      <div ref={bottomRef} />
    </main>
  )
}

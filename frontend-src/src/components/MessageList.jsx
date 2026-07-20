import { useEffect, useRef, useState } from 'react'

function MetricsBar({ label, value, color }) {
  const pct = value !== null ? Math.round(value * 100) : null
  const barColor = pct === null ? 'bg-gray-600'
    : pct >= 75 ? 'bg-emerald-500'
    : pct >= 45 ? 'bg-amber-400'
    : 'bg-rose-500'

  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex justify-between items-center">
        <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: 'var(--text-2)' }}>{label}</span>
        <span className={`text-[10px] font-bold ${pct === null ? 'text-gray-500' : pct >= 75 ? 'text-emerald-400' : pct >= 45 ? 'text-amber-400' : 'text-rose-400'}`}>
          {pct === null ? 'N/A' : `${pct}%`}
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full" style={{ background: 'var(--glass-hi)' }}>
        <div
          className={`h-1.5 rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: pct === null ? '0%' : `${pct}%` }}
        />
      </div>
    </div>
  )
}

function MetricsCard({ metrics }) {
  const [open, setOpen] = useState(false)
  if (!metrics) return null

  const { precision, recall, f1_score, relevant_chunks, total_chunks } = metrics
  const hasData = precision !== null

  return (
    <div className="mt-2 pt-1.5 border-t border-dashed" style={{ borderColor: 'var(--border)' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="text-[10px] uppercase font-bold tracking-wider hover:opacity-85 transition-opacity flex items-center gap-1.5 outline-none"
        style={{ color: 'var(--text-2)' }}
      >
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
        {open ? 'Hide Metrics' : 'Show RAG Metrics'}
      </button>

      {open && (
        <div
          className="mt-1.5 p-3 rounded-xl flex flex-col gap-2"
          style={{ background: 'var(--glass-input)', border: '1px solid var(--border)' }}
        >
          <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: 'var(--text-2)' }}>📊 RAG Retrieval Evaluation</p>
          <MetricsBar label="Precision" value={precision} />
          <MetricsBar label="Recall" value={recall} />
          <MetricsBar label="F1 Score" value={f1_score} />
          <div className="pt-1 border-t" style={{ borderColor: 'var(--border)' }}>
            <p className="text-[10px]" style={{ color: 'var(--text-2)' }}>
              {hasData
                ? <>{relevant_chunks} of {total_chunks} retrieved chunks were <span className="text-emerald-400 font-semibold">relevant</span></>
                : 'Evaluation unavailable for this response.'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

function BotMessageFooter({ msg }) {
  const [tab, setTab] = useState(null) // null | 'usage' | 'metrics'
  const hasUsage   = !!msg.usage
  const hasMetrics = !!msg.metrics

  if (!hasUsage && !hasMetrics) return null

  const { precision, recall, f1_score, relevant_chunks, total_chunks } = msg.metrics ?? {}
  const hasMetricData = precision !== null && precision !== undefined

  return (
    <div className="mt-2 pt-1.5 border-t border-dashed" style={{ borderColor: 'var(--border)' }}>
      {/* Tab buttons row */}
      <div className="flex items-center gap-3">
        {hasUsage && (
          <button
            onClick={() => setTab(t => t === 'usage' ? null : 'usage')}
            className="text-[10px] uppercase font-bold tracking-wider hover:opacity-85 transition-opacity flex items-center gap-1 outline-none"
            style={{ color: tab === 'usage' ? 'var(--text-1)' : 'var(--text-2)' }}
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            Usage & Cost
          </button>
        )}
        {hasUsage && hasMetrics && (
          <span className="text-[10px]" style={{ color: 'var(--border)' }}>|</span>
        )}
        {hasMetrics && (
          <button
            onClick={() => setTab(t => t === 'metrics' ? null : 'metrics')}
            className="text-[10px] uppercase font-bold tracking-wider hover:opacity-85 transition-opacity flex items-center gap-1 outline-none"
            style={{ color: tab === 'metrics' ? 'var(--text-1)' : 'var(--text-2)' }}
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            RAG Metrics
          </button>
        )}
      </div>

      {/* Usage panel */}
      {tab === 'usage' && (
        <div className="mt-1.5 p-2 rounded-lg text-[10px] font-mono flex flex-col gap-0.5"
          style={{ background: 'var(--glass-input)', border: '1px solid var(--border)', color: 'var(--text-1)' }}>
          <div>Prompt Tokens: <span className="font-semibold text-sky-500">{msg.usage.prompt_tokens}</span></div>
          <div>Completion Tokens: <span className="font-semibold text-sky-500">{msg.usage.completion_tokens}</span></div>
          <div>Estimated Cost: <span className="font-semibold text-emerald-500">${msg.usage.cost.toFixed(6)}</span></div>
        </div>
      )}

      {/* Metrics panel */}
      {tab === 'metrics' && (
        <div className="mt-1.5 p-3 rounded-xl flex flex-col gap-2"
          style={{ background: 'var(--glass-input)', border: '1px solid var(--border)' }}>
          <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: 'var(--text-2)' }}>📊 RAG Retrieval Evaluation</p>
          <MetricsBar label="Precision" value={hasMetricData ? precision : null} />
          <MetricsBar label="Recall"    value={hasMetricData ? recall    : null} />
          <MetricsBar label="F1 Score"  value={hasMetricData ? f1_score  : null} />
          <div className="pt-1 border-t" style={{ borderColor: 'var(--border)' }}>
            <p className="text-[10px]" style={{ color: 'var(--text-2)' }}>
              {hasMetricData
                ? <>{relevant_chunks} of {total_chunks} retrieved chunks were <span className="text-emerald-400 font-semibold">relevant</span></>
                : 'Evaluation unavailable for this response.'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

function formatMessageText(text) {
  if (!text) return '';
  
  // Split by newlines
  const lines = text.split('\n');
  
  return lines.map((line, index) => {
    let cleanLine = line.trim();
    let isBullet = false;
    
    // Check for bullet point (* or -) followed by a space
    if (/^[*+-]\s+/.test(cleanLine)) {
      isBullet = true;
      // Remove the bullet prefix
      cleanLine = cleanLine.replace(/^[*+-]\s+/, '');
    }
    
    // Parse bold text (**text**)
    const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
    const content = parts.map((part, pIdx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={pIdx} className="font-bold">{part.slice(2, -2)}</strong>;
      }
      
      // Parse italic text (*text* or _text_)
      const italicParts = part.split(/(\*[^*_]+\*|_[^*_]+_)/g);
      if (italicParts.length > 1) {
        return <span key={pIdx}>{italicParts.map((iPart, iIdx) => {
          if ((iPart.startsWith('*') && iPart.endsWith('*')) || (iPart.startsWith('_') && iPart.endsWith('_'))) {
            return <em key={iIdx} className="italic">{iPart.slice(1, -1)}</em>;
          }
          return iPart;
        })}</span>;
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
      <h1 className="text-lg font-semibold" style={{ color: 'var(--text-1)' }}>Zylo Library Assistant</h1>
      <p className="text-sm max-w-xs" style={{ color: 'var(--text-2)' }}>
        Your personal library assistant is ready. Send a message to search for books, check availability, or manage loans.
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

        {/* Unified footer: Usage & Cost + RAG Metrics */}
        {!isUser && <BotMessageFooter msg={msg} />}
      </div>
    </div>
  )
}

export default function MessageList({ messages, username, toolStatus }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, toolStatus])

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
      {toolStatus && (
        <div className="flex items-end gap-2.5">
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-xs shrink-0 font-semibold"
            style={{ background: 'var(--glass-hi)', border: '1px solid var(--border)', color: 'var(--text-1)', fontSize: '1rem' }}
            aria-hidden
          >
            🤖
          </div>
          <div
            className="max-w-[70%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed space-y-1 flex items-center gap-3"
            style={{
                background:  'var(--glass-bg)',
                backdropFilter: 'blur(12px)',
                border:      '1px solid var(--border)',
                color:       'var(--text-1)',
                borderBottomLeftRadius: '4px',
            }}
          >
            <div className="flex gap-1 items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
            <span className="italic" style={{ color: 'var(--text-2)' }}>{toolStatus}</span>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </main>
  )
}

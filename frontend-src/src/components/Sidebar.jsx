import React, { useState, useEffect } from 'react'

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  isOpen,
}) {
  const [chunkSize, setChunkSize] = useState(() => Number(localStorage.getItem('zylo_chunk_size')) || 1000)
  const [chunkOverlap, setChunkOverlap] = useState(() => Number(localStorage.getItem('zylo_chunk_overlap')) || 200)
  const [isReingesting, setIsReingesting] = useState(false)

  useEffect(() => { localStorage.setItem('zylo_chunk_size', chunkSize) }, [chunkSize])
  useEffect(() => { localStorage.setItem('zylo_chunk_overlap', chunkOverlap) }, [chunkOverlap])

  const handleReingest = async () => {
    setIsReingesting(true)
    const token = localStorage.getItem('zylo_token')
    try {
      const res = await fetch('/api/library/admin/knowledge-base/reingest', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ chunk_size: chunkSize, chunk_overlap: chunkOverlap })
      })
      if (res.ok) {
        alert("Knowledge Base successfully rebuilt with new chunk settings!")
      } else {
        alert("Failed to rebuild knowledge base. Check console.")
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIsReingesting(false)
    }
  }

  return (
    <div
      className="flex flex-col h-full shrink-0 transition-all duration-300 overflow-hidden"
      style={{
        width: isOpen ? '16rem' : '0px',
        opacity: isOpen ? 1 : 0,
        borderRight: isOpen ? '1px solid var(--border)' : '0px solid transparent',
        background: 'var(--glass-bg)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}
    >
      <div className="w-64 h-full flex flex-col">
        <div className="p-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border)' }}>
          <h2 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--text-1)' }}>Chat History</h2>
          <button
            onClick={onNewSession}
            className="p-1.5 rounded-md hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            title="New Chat"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--text-1)' }}>
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map(session => (
            <div key={session.id} className="relative group">
              <button
                onClick={() => onSelectSession(session.id)}
                className="w-full text-left px-3 py-2 rounded-lg transition-colors text-sm truncate pr-8"
                style={{
                  background: activeSessionId === session.id ? 'var(--input-bg)' : 'transparent',
                  color: activeSessionId === session.id ? 'var(--text-1)' : 'var(--text-2)',
                  border: activeSessionId === session.id ? '1px solid var(--border)' : '1px solid transparent'
                }}
              >
                {session.title || "New Chat"}
                <div className="text-[10px] opacity-60 mt-0.5">
                  {new Date(session.created_at).toLocaleDateString()}
                </div>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDeleteSession(session.id)
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 opacity-0 group-hover:opacity-100 rounded-md hover:bg-red-500/10 text-red-400 transition-all duration-200"
                title="Delete Chat"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 6h18" />
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                </svg>
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="text-xs text-center py-4" style={{ color: 'var(--text-2)' }}>
              No chat history
            </div>
          )}
        </div>

        {/* Quick Chunking Settings Panel */}
        <div className="p-4 flex flex-col gap-3" style={{ borderTop: '1px solid var(--border)', background: 'var(--glass-input)' }}>
          <h2 className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--text-2)' }}>Quick Chunking Settings</h2>
          
          <div className="flex items-center justify-between gap-2">
            <div className="flex flex-col w-1/2">
              <label className="text-[10px] mb-1" style={{ color: 'var(--text-2)' }}>Chunk Size</label>
              <input 
                type="number" 
                value={chunkSize}
                onChange={e => setChunkSize(Number(e.target.value))}
                className="bg-black/10 border border-[var(--border)] rounded px-2 py-1 text-xs text-[var(--text-1)] outline-none focus:border-indigo-500 transition-colors" 
              />
            </div>
            <div className="flex flex-col w-1/2">
              <label className="text-[10px] mb-1" style={{ color: 'var(--text-2)' }}>Overlap</label>
              <input 
                type="number" 
                value={chunkOverlap}
                onChange={e => setChunkOverlap(Number(e.target.value))}
                className="bg-black/10 border border-[var(--border)] rounded px-2 py-1 text-xs text-[var(--text-1)] outline-none focus:border-indigo-500 transition-colors" 
              />
            </div>
          </div>
          
          <button
            onClick={handleReingest}
            disabled={isReingesting}
            className={`w-full py-1.5 rounded text-xs font-semibold flex items-center justify-center gap-1 transition-all ${
              isReingesting ? 'bg-fuchsia-500/50 text-fuchsia-200 cursor-not-allowed' : 'bg-fuchsia-500 text-white hover:bg-fuchsia-400'
            }`}
          >
            {isReingesting ? (
              <>
                <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Rebuilding...
              </>
            ) : (
              'Re-chunk & Index'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

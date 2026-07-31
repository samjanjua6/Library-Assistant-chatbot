import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../components/TopBar'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import Sidebar from '../components/Sidebar'
import AnimatedMeshBackground from '../components/AnimatedMeshBackground'

const DONE_SENTINEL = '[DONE]'

function useWebSocket(token, sessionId, onChunk, onStatusChange, skipReconnectRef) {
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      if (skipReconnectRef?.current) {
        skipReconnectRef.current = false
        return
      }
      wsRef.current.close(1000)
    }
    
    if (!token) return

    onStatusChange('connecting')

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    let url = `${proto}//${location.host}/ws/chat?token=${encodeURIComponent(token)}`
    if (sessionId) {
      url += `&session_id=${sessionId}`
    }
    
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen    = () => { if (wsRef.current === ws) onStatusChange('online') }
    ws.onmessage = (e) => { if (wsRef.current === ws) onChunk(e.data) }
    ws.onclose   = (e) => {
      if (wsRef.current !== ws) return
      onStatusChange('offline')
      if (e.code === 1008) {
        onStatusChange('expired')
      } else if (e.code !== 1000) {
        reconnectTimer.current = setTimeout(connect, 3000)
      }
    }
    ws.onerror = () => { if (wsRef.current === ws) onStatusChange('error') }
  }, [token, sessionId, onChunk, onStatusChange, skipReconnectRef])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      if (skipReconnectRef?.current) {
        return
      }
      wsRef.current?.close(1000)
    }
  }, [connect, skipReconnectRef])

  const send = useCallback((text) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(text)
    }
  }, [])

  return { send }
}

export default function ChatPage() {
  const navigate = useNavigate()

  // ── Handle Google OAuth redirect (?token=...&username=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlToken    = params.get('token')
    const urlUsername = params.get('username')
    if (urlToken) {
      localStorage.setItem('zylo_token',    urlToken)
      localStorage.setItem('zylo_username', urlUsername || 'You')
      // Force a clean reload so the app re-initializes with the new token
      window.location.replace('/chat')
    }
  }, [])

  const token    = localStorage.getItem('zylo_token') ?? ''
  const username = localStorage.getItem('zylo_username') ?? 'You'

  const [messages, setMessages]     = useState([])
  const [wsStatus, setWsStatus]     = useState('offline')
  const [isStreaming, setIsStreaming] = useState(false)
  const [toolStatus, setToolStatus] = useState('')
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const skipWsReconnectRef = useRef(false)
  const [showSidebar, setShowSidebar] = useState(true)

  // ── Session document state ──────────────────────────────────────────────────
  const [activeDocumentId, setActiveDocumentId] = useState(null)
  const [activeDocumentName, setActiveDocumentName] = useState('')
  const [uploadStatus, setUploadStatus] = useState(null) // null | 'uploading' | 'processing' | 'ready' | 'failed'
  const [uploadError, setUploadError] = useState('')
  const docPollRef = useRef(null)

  // Fetch all sessions on mount
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch('/api/chat/sessions', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
        if (data.length > 0 && !activeSessionId) {
          setActiveSessionId(data[0].id)
        }
      }
    } catch (err) {
      console.error("Failed to fetch sessions", err)
    }
  }, [token, activeSessionId])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  // Fetch messages when active session changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([])
      return
    }
    
    async function fetchMessages() {
      try {
        const res = await fetch(`/api/chat/sessions/${activeSessionId}/messages`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (res.ok) {
          const data = await res.json()
          setMessages(data.map(m => ({
            id: m.id,
            text: m.content,
            type: m.role === 'model' ? 'bot' : 'user',
            streaming: false
          })))
        }
      } catch (err) {
        console.error("Failed to fetch messages", err)
      }
    }
    fetchMessages()
  }, [activeSessionId, token])

  const createNewSession = async () => {
    // Do not create a new session if the current session has no user messages
    const hasUserMessages = messages.some(m => m.type === 'user');
    if (!hasUserMessages) return;

    try {
      const res = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const newSession = await res.json()
        setSessions(prev => [newSession, ...prev])
        skipWsReconnectRef.current = false
        setActiveSessionId(newSession.id)
        setMessages([])
      }
    } catch (err) {
      console.error("Failed to create new session", err)
    }
  }

  // Append a brand-new message bubble
  const addMessage = useCallback((text, type) => {
    setMessages(prev => [...prev, { id: Date.now() + Math.random(), text, type, streaming: false }])
  }, [])

  // Start a streaming bot bubble (empty, will be filled token-by-token)
  const startBotStream = useCallback(() => {
    const id = Date.now() + Math.random()
    setMessages(prev => [...prev, { id, text: '', type: 'bot', streaming: true }])
    setIsStreaming(true)
    return id
  }, [])

  // Append a token chunk to the last streaming bubble
  const appendToLastBot = useCallback((chunk) => {
    setMessages(prev => {
      const copy = [...prev]
      const last = copy[copy.length - 1]
      if (last?.streaming) {
        copy[copy.length - 1] = { ...last, text: last.text + chunk }
      }
      return copy
    })
  }, [])

  // Mark the last streaming bubble as complete
  const finishBotStream = useCallback(() => {
    setMessages(prev => {
      const copy = [...prev]
      const last = copy[copy.length - 1]
      if (last?.streaming) {
        copy[copy.length - 1] = { ...last, streaming: false }
      }
      return copy
    })
    setIsStreaming(false)
  }, [])

  // Track whether we have an active streaming bubble
  const streamingRef = useRef(false)

  const handleChunk = useCallback((data) => {
    if (data.startsWith('[SESSION_ID:')) {
      const newId = parseInt(data.replace('[SESSION_ID:', '').replace(']', ''))
      skipWsReconnectRef.current = true
      setActiveSessionId(newId)
      fetchSessions() // to refresh sidebar
      return
    }
    if (data.startsWith('[USAGE:')) {
      const usageJson = data.replace('[USAGE:', '').replace(/\]$/, '')
      try {
        const usage = JSON.parse(usageJson)
        setMessages(prev => {
          const copy = [...prev]
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].type === 'bot') {
              copy[i] = { ...copy[i], usage }
              break
            }
          }
          return copy
        })
      } catch (e) {
        console.error("Failed to parse token usage statistics:", e)
      }
      return
    }
    if (data.startsWith('[METRICS:')) {
      const metricsJson = data.replace('[METRICS:', '').replace(/\]$/, '')
      try {
        const metrics = JSON.parse(metricsJson)
        setMessages(prev => {
          const copy = [...prev]
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].type === 'bot') {
              copy[i] = { ...copy[i], metrics }
              break
            }
          }
          return copy
        })
      } catch (e) {
        console.error("Failed to parse metrics:", e)
      }
      return
    }
    if (data.startsWith('[CHUNKS:')) {
      const chunksJson = data.replace('[CHUNKS:', '').replace(/\]$/, '')
      try {
        const chunks = JSON.parse(chunksJson)
        setMessages(prev => {
          const copy = [...prev]
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].type === 'bot') {
              copy[i] = { ...copy[i], chunks }
              break
            }
          }
          return copy
        })
      } catch (e) {
        console.error("Failed to parse chunks:", e)
      }
      return
    }
    if (data.startsWith('[DOC_READY:')) {
      try {
        const json = data.replace('[DOC_READY:', '').replace(/\]$/, '')
        const info = JSON.parse(json)
        setActiveDocumentId(info.document_id)
        setActiveDocumentName(info.filename)
        setUploadStatus('ready')
      } catch (e) { /* ignore */ }
      return
    }
    if (data.startsWith('[DOC_STATUS:')) {
      try {
        const json = data.replace('[DOC_STATUS:', '').replace(/\]$/, '')
        const info = JSON.parse(json)
        if (info.status === 'ready') {
          setActiveDocumentId(info.document_id)
          setActiveDocumentName(info.filename)
          setUploadStatus('ready')
          if (docPollRef.current) clearInterval(docPollRef.current)
        } else if (info.status === 'failed') {
          setUploadStatus('failed')
          setUploadError(info.error_message || 'Processing failed.')
          if (docPollRef.current) clearInterval(docPollRef.current)
        } else {
          // 'pending' and 'processing' both show the spinner — 'pending' means
          // the ARQ job hasn't been picked up yet, which is visually the same
          setUploadStatus('processing')
        }
      } catch (e) { /* ignore */ }
      return
    }
    if (data.startsWith('[STATUS:')) {
      const statusMsg = data.replace('[STATUS:', '').replace(/\]$/, '')
      setToolStatus(statusMsg)
      return
    }
    // First non-DONE message after quiet period → start a new bubble
    if (data === DONE_SENTINEL) {
      finishBotStream()
      streamingRef.current = false
      setToolStatus('')
      return
    }
    if (!streamingRef.current) {
      startBotStream()
      streamingRef.current = true
      setToolStatus('')
    }
    appendToLastBot(data)
  }, [startBotStream, appendToLastBot, finishBotStream, fetchSessions])

  const handleStatus = useCallback((status) => {
    setWsStatus(status)
    if (status === 'expired') {
      addMessage('⚠ Session expired. Redirecting to login…', 'system')
      localStorage.removeItem('zylo_token')
      localStorage.removeItem('zylo_username')
      setTimeout(() => navigate('/login', { replace: true }), 1800)
    } else if (status === 'error') {
      addMessage('Connection error — check the backend.', 'system')
    }
  }, [addMessage, navigate])

  const { send } = useWebSocket(token, activeSessionId, handleChunk, handleStatus, skipWsReconnectRef)

  // ── File upload handler ─────────────────────────────────────────────────────
  const handleFileUpload = useCallback(async (file) => {
    if (!activeSessionId) return
    setUploadStatus('uploading')
    setUploadError('')
    setActiveDocumentId(null)
    setActiveDocumentName(file.name)
    if (docPollRef.current) clearInterval(docPollRef.current)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`/api/chat/sessions/${activeSessionId}/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) {
        setUploadStatus('failed')
        setUploadError(data.detail || 'Upload failed.')
        return
      }

      const docId = data.document_id
      // If the server already processed it synchronously (Redis down fallback),
      // still notify the backend WebSocket so it sets active_document before
      // the user sends their first question.
      if (data.status === 'ready') {
        setActiveDocumentId(docId)
        setUploadStatus('ready')
        // One ping so the WS handler updates its active_document reference
        setTimeout(() => send(`[CHECK_DOC:${docId}]`), 300)
        return
      }

      // Otherwise poll via WebSocket [CHECK_DOC:] frames every 2 seconds
      setUploadStatus('processing')
      docPollRef.current = setInterval(() => {
        send(`[CHECK_DOC:${docId}]`)
      }, 2000)

      // Safety timeout: stop polling after 90 seconds
      setTimeout(() => {
        if (docPollRef.current) {
          clearInterval(docPollRef.current)
          docPollRef.current = null
        }
      }, 90000)

    } catch (err) {
      setUploadStatus('failed')
      setUploadError('Network error during upload.')
    }
  }, [activeSessionId, token, send])

  function handleSend(text) {
    if (!text.trim() || wsStatus !== 'online' || isStreaming) return
    streamingRef.current = false
    setToolStatus('')
    addMessage(text, 'user')
    send(text)
  }

  function handleLogout() {
    localStorage.removeItem('zylo_token')
    localStorage.removeItem('zylo_username')
    navigate('/login', { replace: true })
  }

  const deleteSession = async (id) => {
    try {
      const res = await fetch(`/api/chat/sessions/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.id !== id))
        if (activeSessionId === id) {
          setActiveSessionId(null)
          setMessages([])
        }
      }
    } catch (err) {
      console.error("Failed to delete session", err)
    }
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden relative font-sans text-primary-900">
      <AnimatedMeshBackground />
      <TopBar 
        username={username} 
        wsStatus={wsStatus} 
        onLogout={handleLogout} 
        onToggleSidebar={() => setShowSidebar(!showSidebar)}
        isSidebarOpen={showSidebar}
        onDashboard={() => navigate('/dashboard')}
        onAdmin={() => navigate('/admin')}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={(id) => {
            skipWsReconnectRef.current = false
            setActiveSessionId(id)
          }}
          onNewSession={createNewSession}
          onDeleteSession={deleteSession}
          isOpen={showSidebar}
        />
        <div className="flex flex-col flex-1 min-w-0">
          <MessageList messages={messages} username={username} toolStatus={toolStatus} />

          {/* ── Document status pill ───────────────────────────────────── */}
          {uploadStatus && (
            <div
              className="mx-6 mb-2 px-4 py-2 rounded-xl text-xs flex items-center gap-2 border"
              style={{
                background: uploadStatus === 'ready' ? 'rgba(16,185,129,0.12)'
                  : uploadStatus === 'failed' ? 'rgba(239,68,68,0.12)'
                  : 'rgba(99,102,241,0.12)',
                borderColor: uploadStatus === 'ready' ? 'rgba(16,185,129,0.3)'
                  : uploadStatus === 'failed' ? 'rgba(239,68,68,0.3)'
                  : 'rgba(99,102,241,0.3)',
                color: uploadStatus === 'ready' ? '#34d399'
                  : uploadStatus === 'failed' ? '#f87171'
                  : '#a5b4fc',
              }}
            >
              {uploadStatus === 'uploading' && (
                <><span className="w-3 h-3 rounded-full border-2 border-t-indigo-400 border-r-indigo-400 border-b-transparent border-l-transparent animate-spin" />Uploading {activeDocumentName}…</>
              )}
              {uploadStatus === 'processing' && (
                <><span className="w-3 h-3 rounded-full border-2 border-t-indigo-400 border-r-indigo-400 border-b-transparent border-l-transparent animate-spin" />Indexing {activeDocumentName}…<span className="ml-1 opacity-60">(this may take a few seconds)</span></>
              )}
              {uploadStatus === 'ready' && (
                <><span>📎</span><span className="font-medium">{activeDocumentName}</span><span className="opacity-70">ready — you can now ask questions about this file</span>
                  <button onClick={() => { setUploadStatus(null); setActiveDocumentId(null); setActiveDocumentName('') }} className="ml-auto opacity-50 hover:opacity-100 text-base leading-none">×</button>
                </>
              )}
              {uploadStatus === 'failed' && (
                <><span>⚠</span><span>{uploadError || 'Processing failed.'}</span>
                  <button onClick={() => setUploadStatus(null)} className="ml-auto opacity-50 hover:opacity-100 text-base leading-none">×</button>
                </>
              )}
            </div>
          )}

          <ChatInput
            onSend={handleSend}
            disabled={wsStatus !== 'online'}
            isStreaming={isStreaming}
            onFileUpload={handleFileUpload}
            sessionId={activeSessionId}
          />
        </div>
      </div>
    </div>
  )
}

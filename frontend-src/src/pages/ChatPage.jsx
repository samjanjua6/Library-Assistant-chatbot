import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../components/TopBar'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'

function useWebSocket(token, onMessage, onStatusChange) {
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    onStatusChange('connecting')

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${proto}//${location.host}/ws/chat?token=${encodeURIComponent(token)}`)
    wsRef.current = ws

    ws.onopen    = () => onStatusChange('online')
    ws.onmessage = (e) => onMessage(e.data)
    ws.onclose   = (e) => {
      onStatusChange('offline')
      if (e.code === 1008) {
        onStatusChange('expired')
      } else if (e.code !== 1000) {
        reconnectTimer.current = setTimeout(connect, 3000)
      }
    }
    ws.onerror = () => onStatusChange('error')
  }, [token, onMessage, onStatusChange])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close(1000)
    }
  }, [connect])

  const send = useCallback((text) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(text)
    }
  }, [])

  return { send }
}

export default function ChatPage() {
  const navigate = useNavigate()
  const token    = localStorage.getItem('zylo_token') ?? ''
  const username = localStorage.getItem('zylo_username') ?? 'You'

  const [messages, setMessages]   = useState([])
  const [wsStatus, setWsStatus]   = useState('offline')

  const addMessage = useCallback((text, type) => {
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), text, type }])
  }, [])

  const handleMessage = useCallback((text) => {
    addMessage(text, 'bot')
  }, [addMessage])

  const handleStatus = useCallback((status) => {
    setWsStatus(status)
    if (status === 'expired') {
      addMessage('⚠ Session expired. Redirecting to login…', 'system')
      localStorage.removeItem('zylo_token')
      localStorage.removeItem('zylo_username')
      setTimeout(() => navigate('/', { replace: true }), 1800)
    } else if (status === 'error') {
      addMessage('Connection error — check the backend.', 'system')
    }
  }, [addMessage, navigate])

  const { send } = useWebSocket(token, handleMessage, handleStatus)

  function handleSend(text) {
    if (!text.trim() || wsStatus !== 'online') return
    addMessage(text, 'user')
    send(text)
  }

  function handleLogout() {
    localStorage.removeItem('zylo_token')
    localStorage.removeItem('zylo_username')
    navigate('/', { replace: true })
  }

  return (
    <div className="flex flex-col h-screen bg-canvas">
      <TopBar username={username} wsStatus={wsStatus} onLogout={handleLogout} />
      <MessageList messages={messages} username={username} />
      <ChatInput onSend={handleSend} disabled={wsStatus !== 'online'} />
    </div>
  )
}

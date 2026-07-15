import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import AuthPage from './pages/AuthPage'
import ChatPage from './pages/ChatPage'

/** Guard: redirect unauthenticated users to /login */
function PrivateRoute({ children }) {
  const hasToken = localStorage.getItem('zylo_token') || new URLSearchParams(window.location.search).has('token')
  return hasToken ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* New public landing page */}
        <Route path="/" element={<LandingPage />} />
        
        {/* Auth routes */}
        <Route path="/login" element={<AuthPage />} />
        
        {/* Protected routes */}
        <Route
          path="/chat"
          element={
            <PrivateRoute>
              <ChatPage />
            </PrivateRoute>
          }
        />
        
        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

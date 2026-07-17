import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function DashboardPage() {
  const [loans, setLoans] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const fetchLoans = async () => {
    try {
      const token = localStorage.getItem('zylo_token')
      const res = await fetch('/api/library/loans', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to fetch loans')
      const data = await res.json()
      setLoans(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLoans()
  }, [])

  const handleReturn = async (bookId) => {
    try {
      const token = localStorage.getItem('zylo_token')
      const res = await fetch(`/api/library/loans/${bookId}/return`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to return book')
      }
      // Refresh the list
      fetchLoans()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('zylo_token')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-1)] font-sans flex flex-col">
      <header className="px-6 py-4 border-b border-[var(--border)] flex justify-between items-center bg-[var(--glass-bg)] backdrop-blur-md">
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-indigo-500">
          Zylo Dashboard
        </h1>
        <div className="flex gap-4">
          <button onClick={() => navigate('/chat')} className="text-sm font-medium hover:text-sky-400 transition-colors">Chat</button>
          <button onClick={() => navigate('/admin')} className="text-sm font-medium hover:text-emerald-400 transition-colors">Admin</button>
          <button onClick={handleLogout} className="text-sm font-medium text-rose-400 hover:text-rose-300 transition-colors">Logout</button>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-10">
        <div className="mb-8">
          <h2 className="text-3xl font-semibold mb-2">My Active Loans</h2>
          <p className="text-[var(--text-2)]">Manage the books you are currently borrowing.</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <span className="w-8 h-8 rounded-full border-2 border-t-sky-500 border-r-sky-500 border-b-transparent border-l-transparent animate-spin"></span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
            {error}
          </div>
        ) : loans.length === 0 ? (
          <div className="text-center py-20 px-6 rounded-2xl bg-[var(--glass-bg)] border border-[var(--border)]">
            <div className="text-6xl mb-4 opacity-50">📚</div>
            <h3 className="text-xl font-medium mb-2">No Active Loans</h3>
            <p className="text-[var(--text-2)] mb-6">You haven't borrowed any books yet.</p>
            <button onClick={() => navigate('/chat')} className="px-6 py-2 rounded-full bg-sky-500 hover:bg-sky-400 text-white font-medium transition-colors">
              Talk to the Assistant to Borrow a Book
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loans.map(loan => {
              const due = new Date(loan.due_date)
              const now = new Date()
              const totalDays = 14
              const daysLeft = Math.ceil((due - now) / (1000 * 60 * 60 * 24))
              const progress = Math.max(0, Math.min(100, ((totalDays - daysLeft) / totalDays) * 100))
              
              const isLate = daysLeft < 0

              return (
                <div key={loan.id} className="rounded-2xl p-6 flex flex-col gap-4 border border-[var(--border)] bg-[var(--glass-input)] shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                  <div>
                    <h3 className="text-lg font-bold text-sky-100">{loan.title}</h3>
                    <p className="text-sm text-sky-400/80">by {loan.author}</p>
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-[var(--text-2)]">Time remaining</span>
                      <span className={isLate ? 'text-rose-400 font-bold' : 'text-emerald-400 font-medium'}>
                        {isLate ? 'Overdue' : `${daysLeft} days left`}
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-[var(--glass-hi)] rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${isLate ? 'bg-rose-500' : 'bg-emerald-500'}`} 
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                    <div className="mt-2 text-xs text-[var(--text-2)]">
                      Due: {due.toLocaleDateString()}
                    </div>
                  </div>

                  <button 
                    onClick={() => handleReturn(loan.book_id)}
                    className="mt-2 w-full py-2.5 rounded-xl bg-[var(--glass-hi)] hover:bg-sky-500 hover:text-white border border-[var(--border)] font-medium text-sm transition-all flex items-center justify-center gap-2 group"
                  >
                    <span>Return Book</span>
                    <svg className="w-4 h-4 opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}

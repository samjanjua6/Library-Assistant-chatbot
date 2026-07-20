import { useEffect, useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

const FILE_TYPE_COLORS = {
  PDF: 'bg-red-500/20 text-red-300',
  TXT: 'bg-sky-500/20 text-sky-300',
  MD:  'bg-violet-500/20 text-violet-300',
  DOCX:'bg-blue-500/20 text-blue-300',
  CSV: 'bg-emerald-500/20 text-emerald-300',
  JSON:'bg-amber-500/20 text-amber-300',
  XLSX:'bg-green-500/20 text-green-300',
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function KnowledgeBaseManager() {
  const [docs, setDocs] = useState([])
  const [uploading, setUploading] = useState(false)
  const [statusMsg, setStatusMsg] = useState(null) // { type: 'success'|'error', text }
  const [isDragging, setIsDragging] = useState(false)
  const [chunkSize, setChunkSize] = useState(() => Number(localStorage.getItem('zylo_chunk_size')) || 1000)
  const [chunkOverlap, setChunkOverlap] = useState(() => Number(localStorage.getItem('zylo_chunk_overlap')) || 200)

  useEffect(() => { localStorage.setItem('zylo_chunk_size', chunkSize) }, [chunkSize])
  useEffect(() => { localStorage.setItem('zylo_chunk_overlap', chunkOverlap) }, [chunkOverlap])
  const fileRef = useRef()
  const token = localStorage.getItem('zylo_token')
  const headers = { Authorization: `Bearer ${token}` }

  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch('/api/library/admin/knowledge-base', { headers })
      if (res.ok) {
        const data = await res.json()
        setDocs(data.documents)
      }
    } catch (e) { /* silent */ }
  }, [])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const handleUpload = async (files) => {
    if (!files || files.length === 0) return
    setUploading(true)
    setStatusMsg(null)
    const results = []
    for (const file of files) {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('chunk_size', chunkSize)
      fd.append('chunk_overlap', chunkOverlap)
      try {
        const res = await fetch('/api/library/admin/knowledge-base/upload', {
          method: 'POST', headers, body: fd
        })
        const data = await res.json()
        if (res.ok) results.push({ ok: true, name: file.name, msg: data.message })
        else results.push({ ok: false, name: file.name, msg: data.detail })
      } catch (e) {
        results.push({ ok: false, name: file.name, msg: e.message })
      }
    }
    await fetchDocs()
    setUploading(false)
    const failed = results.filter(r => !r.ok)
    if (failed.length === 0) {
      setStatusMsg({ type: 'success', text: `✓ ${results.length} file(s) uploaded successfully!` })
    } else {
      setStatusMsg({ type: 'error', text: `${failed.length} file(s) failed: ${failed.map(f => `${f.name} (${f.msg})`).join(', ')}` })
    }
    setTimeout(() => setStatusMsg(null), 5000)
  }

  const handleDelete = async (filename) => {
    if (!window.confirm(`Delete "${filename}" from the knowledge base?`)) return
    try {
      const res = await fetch(`/api/library/admin/knowledge-base/file/${encodeURIComponent(filename)}`, {
        method: 'DELETE', headers
      })
      if (res.ok) {
        setDocs(d => d.filter(f => f.filename !== filename))
        setStatusMsg({ type: 'success', text: `✓ "${filename}" deleted.` })
        setTimeout(() => setStatusMsg(null), 3000)
      }
    } catch (e) { setStatusMsg({ type: 'error', text: e.message }) }
  }

  const handleClearAll = async () => {
    if (!window.confirm('Clear the ENTIRE knowledge base? This cannot be undone.')) return
    try {
      await fetch('/api/library/admin/knowledge-base', { method: 'DELETE', headers })
      setDocs([])
      setStatusMsg({ type: 'success', text: '✓ Knowledge base cleared.' })
      setTimeout(() => setStatusMsg(null), 3000)
    } catch (e) { setStatusMsg({ type: 'error', text: e.message }) }
  }

  return (
    <section className="bg-[var(--glass-input)] border border-[var(--border)] rounded-2xl p-6 shadow-lg flex flex-col gap-4">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <svg className="w-5 h-5 text-fuchsia-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Knowledge Base
        <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-fuchsia-500/20 text-fuchsia-300 font-normal">{docs.length} file{docs.length !== 1 ? 's' : ''}</span>
      </h2>

      {/* Status message */}
      {statusMsg && (
        <div className={`text-sm px-4 py-2 rounded-lg ${statusMsg.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
          {statusMsg.text}
        </div>
      )}

      {/* Drag-and-drop upload zone */}
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={e => { e.preventDefault(); setIsDragging(false); handleUpload(Array.from(e.dataTransfer.files)) }}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging ? 'border-fuchsia-400 bg-fuchsia-500/10' : 'border-[var(--border)] hover:border-fuchsia-500/50 hover:bg-fuchsia-500/5'
        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input
          ref={fileRef}
          type="file"
          multiple
          accept=".txt,.pdf,.md,.docx,.csv,.json,.xlsx"
          className="hidden"
          onChange={e => handleUpload(Array.from(e.target.files))}
        />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-fuchsia-400/30 border-t-fuchsia-400 rounded-full animate-spin" />
            <p className="text-sm text-fuchsia-400 font-medium">Ingesting documents...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <svg className="w-10 h-10 text-fuchsia-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-sm font-semibold text-[var(--text-1)]">Drop files here or click to browse</p>
            <p className="text-xs text-[var(--text-2)]">PDF · TXT · MD · DOCX · CSV · JSON · XLSX</p>
          </div>
        )}
      </div>

      {/* Chunking Configuration */}
      <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-[var(--glass-hi)] border border-[var(--border)]">
        <div className="col-span-2">
          <p className="text-xs font-semibold text-fuchsia-400 uppercase tracking-wide mb-2">Chunking Settings</p>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-[var(--text-2)] flex items-center gap-1">
            Chunk Size
            <span className="text-[10px] text-[var(--text-2)] opacity-60">(characters)</span>
          </label>
          <input
            type="number" min="100" max="4000" step="100"
            value={chunkSize}
            onChange={e => setChunkSize(parseInt(e.target.value))}
            className="bg-[var(--bg-main)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-fuchsia-500 transition-colors"
          />
          <p className="text-[10px] text-[var(--text-2)] opacity-60">How many characters per chunk. Smaller = more precise, larger = more context.</p>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-[var(--text-2)] flex items-center gap-1">
            Chunk Overlap
            <span className="text-[10px] text-[var(--text-2)] opacity-60">(characters)</span>
          </label>
          <input
            type="number" min="0" max="500" step="50"
            value={chunkOverlap}
            onChange={e => setChunkOverlap(parseInt(e.target.value))}
            className="bg-[var(--bg-main)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-fuchsia-500 transition-colors"
          />
          <p className="text-[10px] text-[var(--text-2)] opacity-60">How many characters overlap between chunks. Helps maintain context at boundaries.</p>
        </div>
      </div>

      {/* Document list */}
      {docs.length > 0 ? (
        <div className="flex flex-col gap-2 max-h-72 overflow-y-auto pr-1">
          {docs.map(doc => (
            <div key={doc.filename} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-[var(--glass-hi)] border border-[var(--border)] group">
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md shrink-0 ${FILE_TYPE_COLORS[doc.file_type] ?? 'bg-gray-500/20 text-gray-300'}`}>
                {doc.file_type}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{doc.filename}</p>
                <p className="text-xs text-[var(--text-2)]">{formatBytes(doc.size_bytes)}</p>
              </div>
              <button
                onClick={() => handleDelete(doc.filename)}
                className="shrink-0 p-1.5 rounded-lg text-[var(--text-2)] hover:text-rose-400 hover:bg-rose-500/10 transition-colors opacity-0 group-hover:opacity-100"
                title="Delete document"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-center text-[var(--text-2)] py-4">No documents in the knowledge base yet.</p>
      )}

      {docs.length > 0 && (
        <button
          onClick={handleClearAll}
          className="mt-2 py-2.5 rounded-xl border border-rose-500/40 text-rose-400 hover:bg-rose-500 hover:text-white text-sm font-semibold transition-colors"
        >
          Clear All Documents
        </button>
      )}
    </section>
  )
}


export default function AdminPage() {
  const [books, setBooks] = useState([])
  const [totalBooks, setTotalBooks] = useState(0)
  const [page, setPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [loans, setLoans] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  // New book form state
  const [newTitle, setNewTitle] = useState('')
  const [newAuthor, setNewAuthor] = useState('')
  const [newGenre, setNewGenre] = useState('')
  const [newTotalCopies, setNewTotalCopies] = useState(1)

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const token = localStorage.getItem('zylo_token')
      const headers = { Authorization: `Bearer ${token}` }
      
      const skip = (page - 1) * 10
      const limit = 10
      const searchParam = searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''
      
      const [booksRes, loansRes, usersRes] = await Promise.all([
        fetch(`/api/library/admin/books?skip=${skip}&limit=${limit}${searchParam}`, { headers }),
        fetch('/api/library/admin/loans', { headers }),
        fetch('/api/admin/users', { headers })
      ])
      
      if (booksRes.status === 401 || loansRes.status === 401 || usersRes.status === 401) {
        handleLogout()
        return
      }
      
      if (booksRes.status === 403 || loansRes.status === 403 || usersRes.status === 403) {
        throw new Error('FORBIDDEN')
      }
      if (!booksRes.ok || !loansRes.ok || !usersRes.ok) {
        throw new Error('FORBIDDEN') // Treat any unexpected error (like 404) as forbidden just to be safe on the admin page, or generic error.
      }
        
      const booksData = await booksRes.json()
      setBooks(booksData.books)
      setTotalBooks(booksData.total)
      setLoans(await loansRes.json())
      setUsers(await usersRes.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [page])

  // Debounce search query changes
  useEffect(() => {
    setPage(1) // Reset to first page on new search
    const timer = setTimeout(() => {
      fetchData()
    }, 500)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const handleAddBook = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('zylo_token')
      const res = await fetch('/api/library/admin/books', {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: newTitle,
          author: newAuthor,
          genre: newGenre,
          total_copies: parseInt(newTotalCopies)
        })
      })
      if (!res.ok) throw new Error('Failed to add book')
      
      setNewTitle('')
      setNewAuthor('')
      setNewGenre('')
      setNewTotalCopies(1)
      fetchData()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleUpdateInventory = async (bookId, total, available) => {
    try {
      const token = localStorage.getItem('zylo_token')
      const res = await fetch(`/api/library/admin/books/${bookId}`, {
        method: 'PUT',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          total_copies: parseInt(total),
          available_copies: parseInt(available)
        })
      })
      if (!res.ok) throw new Error('Failed to update inventory')
      fetchData()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleToggleRole = async (userId) => {
    try {
      const token = localStorage.getItem('zylo_token')
      const res = await fetch(`/api/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to toggle admin role')
      fetchData()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('zylo_token')
    navigate('/login')
  }



  if (error === 'FORBIDDEN') {
    return (
      <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-1)] font-sans flex flex-col items-center justify-center p-6">
        <div className="max-w-md w-full bg-[var(--glass-bg)] border border-[var(--border)] rounded-2xl p-8 text-center shadow-2xl">
          <div className="text-6xl mb-6">🔒</div>
          <h1 className="text-2xl font-bold text-rose-400 mb-4">Restricted Access</h1>
          <p className="text-[var(--text-2)] mb-8">
            Sorry, you don't have the necessary administrator permissions to view this page.
          </p>
          <button 
            onClick={() => navigate('/chat')}
            className="w-full py-3 rounded-xl bg-[var(--glass-hi)] hover:bg-sky-500 hover:text-white border border-[var(--border)] font-semibold transition-all"
          >
            Return to Chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-1)] font-sans flex flex-col">
      <header className="px-6 py-4 border-b border-[var(--border)] flex justify-between items-center bg-[var(--glass-bg)] backdrop-blur-md sticky top-0 z-50">
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-500">
          Zylo Admin Panel
        </h1>
        <div className="flex gap-4">
          <button onClick={() => navigate('/chat')} className="text-sm font-medium hover:text-sky-400 transition-colors">Chat</button>
          <button onClick={() => navigate('/dashboard')} className="text-sm font-medium hover:text-indigo-400 transition-colors">Dashboard</button>
          <button onClick={handleLogout} className="text-sm font-medium text-rose-400 hover:text-rose-300 transition-colors">Logout</button>
        </div>
      </header>

      <main className="flex-1 w-full mx-auto px-6 py-10 grid grid-cols-1 xl:grid-cols-3 gap-8 max-w-7xl">
        
        {/* Left Column: Manage Books & Add Book */}
        <div className="xl:col-span-2 flex flex-col gap-8">
          
          {/* Add New Book Section */}
          <section className="bg-[var(--glass-input)] border border-[var(--border)] rounded-2xl p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add New Book
            </h2>
            <form onSubmit={handleAddBook} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input type="text" placeholder="Title" required value={newTitle} onChange={e => setNewTitle(e.target.value)} className="bg-[var(--glass-hi)] border border-[var(--border)] rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500 transition-colors" />
              <input type="text" placeholder="Author" required value={newAuthor} onChange={e => setNewAuthor(e.target.value)} className="bg-[var(--glass-hi)] border border-[var(--border)] rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500 transition-colors" />
              <input type="text" placeholder="Genre" value={newGenre} onChange={e => setNewGenre(e.target.value)} className="bg-[var(--glass-hi)] border border-[var(--border)] rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500 transition-colors" />
              <div className="flex gap-2 items-center">
                <label className="text-sm text-[var(--text-2)] whitespace-nowrap">Total Copies:</label>
                <input type="number" min="1" required value={newTotalCopies} onChange={e => setNewTotalCopies(e.target.value)} className="w-full bg-[var(--glass-hi)] border border-[var(--border)] rounded-lg px-4 py-2 focus:outline-none focus:border-emerald-500 transition-colors" />
              </div>
              <button type="submit" className="md:col-span-2 py-3 mt-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold transition-colors shadow-lg shadow-emerald-500/20">
                Add to Catalog
              </button>
            </form>
          </section>

          {/* Book Catalog Section */}
          <section className="bg-[var(--glass-input)] border border-[var(--border)] rounded-2xl p-6 shadow-lg flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-4 gap-4 flex-wrap">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <svg className="w-5 h-5 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Book Catalog Inventory
              </h2>
              <input 
                type="text" 
                placeholder="Search title or author..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-[var(--bg-main)] border border-[var(--border)] rounded-xl px-4 py-2 focus:outline-none focus:border-sky-500 transition-colors max-w-xs w-full"
              />
            </div>
            <div className="overflow-x-auto flex-1 mb-4">
              {loading ? (
                <div className="flex justify-center py-10"><span className="animate-pulse">Loading data...</span></div>
              ) : error ? (
                <div className="text-rose-400">{error}</div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-sm text-[var(--text-2)]">
                      <th className="pb-3 pr-4 font-medium">ID</th>
                      <th className="pb-3 pr-4 font-medium">Title & Author</th>
                      <th className="pb-3 pr-4 font-medium">Total</th>
                      <th className="pb-3 font-medium">Available</th>
                    </tr>
                  </thead>
                  <tbody>
                    {books.map(book => (
                      <tr key={book.id} className="border-b border-[var(--border)]/50 hover:bg-[var(--glass-hi)] transition-colors">
                        <td className="py-3 pr-4 text-xs text-[var(--text-2)]">#{book.id}</td>
                        <td className="py-3 pr-4">
                          <div className="font-semibold text-sky-100">{book.title}</div>
                          <div className="text-xs text-[var(--text-2)]">{book.author}</div>
                        </td>
                        <td className="py-3 pr-4">
                          <input 
                            type="number" 
                            className="w-16 bg-[var(--bg-main)] border border-[var(--border)] rounded px-2 py-1 text-sm focus:outline-none focus:border-sky-500" 
                            defaultValue={book.total_copies}
                            onBlur={(e) => handleUpdateInventory(book.id, e.target.value, book.available_copies)}
                          />
                        </td>
                        <td className="py-3">
                          <input 
                            type="number" 
                            className="w-16 bg-[var(--bg-main)] border border-[var(--border)] rounded px-2 py-1 text-sm focus:outline-none focus:border-sky-500" 
                            defaultValue={book.available_copies}
                            onBlur={(e) => handleUpdateInventory(book.id, book.total_copies, e.target.value)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            
            {/* Pagination Controls */}
            {!loading && totalBooks > 0 && (
              <div className="flex justify-between items-center mt-auto pt-4 border-t border-[var(--border)]">
                <button 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 rounded-lg bg-[var(--glass-hi)] border border-[var(--border)] disabled:opacity-50 hover:bg-[var(--border)] transition-colors text-sm font-medium"
                >
                  Previous
                </button>
                <span className="text-sm text-[var(--text-2)]">
                  Page {page} of {Math.ceil(totalBooks / 10)} ({totalBooks} books total)
                </span>
                <button 
                  onClick={() => setPage(p => Math.min(Math.ceil(totalBooks / 10), p + 1))}
                  disabled={page >= Math.ceil(totalBooks / 10)}
                  className="px-4 py-2 rounded-lg bg-[var(--glass-hi)] border border-[var(--border)] disabled:opacity-50 hover:bg-[var(--border)] transition-colors text-sm font-medium"
                >
                  Next
                </button>
              </div>
            )}
          </section>


          {/* Knowledge Base Section */}
          <KnowledgeBaseManager />


          {/* Manage Users Section */}
          <section className="bg-[var(--glass-input)] border border-[var(--border)] rounded-2xl p-6 shadow-lg flex flex-col">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              Manage Users
            </h2>
            <div className="overflow-x-auto flex-1">
              {loading ? (
                <div className="flex justify-center py-10"><span className="animate-pulse">Loading data...</span></div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-sm text-[var(--text-2)]">
                      <th className="pb-3 pr-4 font-medium">User</th>
                      <th className="pb-3 pr-4 font-medium">Joined</th>
                      <th className="pb-3 font-medium">Administrator</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(user => (
                      <tr key={user.id} className="border-b border-[var(--border)]/50 hover:bg-[var(--glass-hi)] transition-colors">
                        <td className="py-3 pr-4">
                          <div className="font-semibold text-sky-100">@{user.username}</div>
                          <div className="text-xs text-[var(--text-2)]">{user.email}</div>
                        </td>
                        <td className="py-3 pr-4 text-xs text-[var(--text-2)]">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3">
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              className="sr-only peer" 
                              checked={user.is_admin}
                              onChange={() => handleToggleRole(user.id)}
                            />
                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-500"></div>
                            <span className="ml-3 text-xs font-medium text-[var(--text-2)]">
                              {user.is_admin ? 'Admin' : 'User'}
                            </span>
                          </label>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>

        </div>

        {/* Right Column: Global Active Loans */}
        <section className="bg-[var(--glass-input)] border border-[var(--border)] rounded-2xl p-6 shadow-lg flex flex-col h-[calc(100vh-8rem)] sticky top-24">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Global Active Loans
          </h2>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
            {loading ? null : loans.length === 0 ? (
              <div className="text-center py-10 text-[var(--text-2)] text-sm">No active loans right now.</div>
            ) : (
              loans.map(loan => {
                const isLate = new Date(loan.due_date) < new Date()
                return (
                  <div key={loan.id} className="p-4 rounded-xl border border-[var(--border)] bg-[var(--glass-hi)] flex flex-col gap-2">
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-medium px-2 py-1 rounded bg-indigo-500/20 text-indigo-300">
                        User: @{loan.username}
                      </span>
                      {isLate && (
                        <span className="text-xs font-bold text-rose-400 bg-rose-500/10 px-2 py-1 rounded">OVERDUE</span>
                      )}
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">{loan.title}</h4>
                      <p className="text-xs text-[var(--text-2)] mt-1">Due: {new Date(loan.due_date).toLocaleDateString()}</p>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </section>

      </main>
    </div>
  )
}

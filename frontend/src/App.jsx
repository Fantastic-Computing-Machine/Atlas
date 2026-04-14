import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import ConnectPage from './pages/ConnectPage'
import ScopesPage from './pages/ScopesPage'
import DashboardPage from './pages/DashboardPage'
import { auth } from './services/api'
import './App.css'

function App() {
  const [connectionStatus, setConnectionStatus] = useState(null)
  const [userId, setUserId] = useState(() => localStorage.getItem('atlas_user_id'))
  const location = useLocation()

  // Check for OAuth callback params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const status = params.get('status')
    const returnedUserId = params.get('user_id')
    
    if (status === 'success' && returnedUserId) {
      setUserId(returnedUserId)
      localStorage.setItem('atlas_user_id', returnedUserId)
      // Clean up URL
      window.history.replaceState({}, '', '/connect')
    }
  }, [])

  // Fetch connection status
  useEffect(() => {
    if (!userId) return
    
    auth.getStatus(userId)
      .then(setConnectionStatus)
      .catch(() => setConnectionStatus(null))
  }, [userId])

  const isConnected = connectionStatus?.connected === true

  const handleDisconnect = async () => {
    if (!userId) return
    await auth.disconnect(userId)
    setConnectionStatus(null)
    setUserId(null)
    localStorage.removeItem('atlas_user_id')
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">⚛</div>
          <h1>Atlas</h1>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/connect" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🔗</span>
            Connect
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">📊</span>
            Dashboard
          </NavLink>
          <NavLink to="/scopes" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">🎯</span>
            Scopes
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className={`status-dot ${isConnected ? 'connected' : ''}`}></span>
            <span>{isConnected ? connectionStatus.email || 'Connected' : 'Not connected'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="app-main">
        <Routes>
          <Route path="/" element={<ConnectPage userId={userId} status={connectionStatus} onDisconnect={handleDisconnect} />} />
          <Route path="/connect" element={<ConnectPage userId={userId} status={connectionStatus} onDisconnect={handleDisconnect} />} />
          <Route path="/dashboard" element={<DashboardPage userId={userId} isConnected={isConnected} />} />
          <Route path="/scopes" element={<ScopesPage userId={userId} isConnected={isConnected} />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

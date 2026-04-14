import { useState, useEffect } from 'react'
import { messages } from '../services/api'

export default function DashboardPage({ userId, isConnected }) {
  const [syncStatus, setSyncStatus] = useState(null)
  const [messageList, setMessageList] = useState(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [syncing, setSyncing] = useState(false)
  const [loading, setLoading] = useState(true)

  // Fetch data on mount
  useEffect(() => {
    if (!userId || !isConnected) {
      setLoading(false)
      return
    }
    loadData()
  }, [userId, isConnected, page])

  const loadData = async () => {
    setLoading(true)
    try {
      const [status, msgs] = await Promise.all([
        messages.syncStatus(userId),
        messages.list(userId, { page, pageSize: 30, search: search || undefined }),
      ])
      setSyncStatus(status)
      setMessageList(msgs)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async (incremental = false) => {
    setSyncing(true)
    try {
      await messages.triggerSync(userId, { incremental })
      await loadData()
    } catch (error) {
      console.error('Sync failed:', error)
    } finally {
      setSyncing(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    loadData()
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    const now = new Date()
    const diff = now - d
    
    if (diff < 86400000) {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    if (diff < 604800000) {
      return d.toLocaleDateString([], { weekday: 'short' })
    }
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  const formatSender = (from) => {
    if (!from) return 'Unknown'
    // Extract name from "Name <email>" format
    const match = from.match(/^"?([^"<]+)"?\s*</)
    return match ? match[1].trim() : from.split('@')[0]
  }

  if (!isConnected) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h2>Dashboard</h2>
          <p>Your inbox overview and synced messages.</p>
        </div>
        <div className="glass-card empty-state">
          <div className="empty-icon">📬</div>
          <h3>Gmail Not Connected</h3>
          <p>Connect your Gmail account to see your inbox dashboard and synced messages.</p>
          <a href="/connect" className="btn btn-primary">Connect Gmail</a>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Your inbox overview and synced messages.</p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📧</div>
          <div className="stat-value">{syncStatus?.message_count?.toLocaleString() || '0'}</div>
          <div className="stat-label">Messages Synced</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🔄</div>
          <div className="stat-value" style={{ fontSize: 'var(--font-size-xl)' }}>
            {syncStatus?.status || 'Unknown'}
          </div>
          <div className="stat-label">Sync Status</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🕐</div>
          <div className="stat-value" style={{ fontSize: 'var(--font-size-lg)' }}>
            {syncStatus?.last_sync_at
              ? new Date(syncStatus.last_sync_at).toLocaleString()
              : 'Never'}
          </div>
          <div className="stat-label">Last Sync</div>
        </div>
      </div>

      {/* Actions */}
      <div className="glass-card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="glass-card-header">
          <h3>Sync Controls</h3>
          <div style={{ display: 'flex', gap: 'var(--space-md)' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleSync(true)}
              disabled={syncing}
            >
              {syncing ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '🔄'}
              Incremental Sync
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => handleSync(false)}
              disabled={syncing}
            >
              {syncing ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '📥'}
              Full Sync
            </button>
          </div>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: 'var(--space-md)' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Search messages by subject, sender, or snippet..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ flex: 1 }}
          />
          <button type="submit" className="btn btn-secondary">Search</button>
        </form>
      </div>

      {/* Message List */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 'var(--space-2xl)', textAlign: 'center' }}>
            <span className="loading-spinner">
              <span className="spinner"></span>
              Loading messages...
            </span>
          </div>
        ) : messageList?.messages?.length > 0 ? (
          <>
            <div className="message-list" style={{ border: 'none' }}>
              {messageList.messages.map((msg) => (
                <div
                  key={msg.gmail_message_id}
                  className={`message-item ${msg.is_read === false ? 'unread' : ''}`}
                >
                  <div className="message-from">{formatSender(msg.from_header)}</div>
                  <div className="message-content">
                    <div className="message-subject">{msg.subject || '(no subject)'}</div>
                    <div className="message-snippet">{msg.snippet}</div>
                  </div>
                  <div className="message-meta">
                    <div className="message-date">{formatDate(msg.internal_date)}</div>
                    <div className="message-labels">
                      {msg.has_attachments && <span className="tag tag-primary" style={{ fontSize: '0.65rem', padding: '1px 6px' }}>📎</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: 'var(--space-md) var(--space-lg)',
              borderTop: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)'
            }}>
              <span>
                Showing {((page - 1) * 30) + 1}–{Math.min(page * 30, messageList.total)} of {messageList.total}
              </span>
              <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  ← Prev
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={page * 30 >= messageList.total}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next →
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No Messages Yet</h3>
            <p>Run a sync to fetch your Gmail messages, then they'll appear here.</p>
            <button className="btn btn-primary" onClick={() => handleSync(false)} disabled={syncing}>
              Start Initial Sync
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

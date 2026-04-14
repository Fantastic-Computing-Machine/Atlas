import { useState } from 'react'
import { auth } from '../services/api'

export default function ConnectPage({ userId, status, onDisconnect }) {
  const [loading, setLoading] = useState(false)

  const handleConnect = async () => {
    setLoading(true)
    try {
      const result = await auth.getConnectUrl()
      window.location.href = result.authorization_url
    } catch (error) {
      console.error('Failed to get connect URL:', error)
      setLoading(false)
    }
  }

  const isConnected = status?.connected === true

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>Connect Gmail</h2>
        <p>Link your Gmail account to unlock intelligent inbox organization and natural-language research.</p>
      </div>

      {isConnected ? (
        /* Connected State */
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-lg)', marginBottom: 'var(--space-xl)' }}>
            <div style={{
              width: 56, height: 56, borderRadius: 'var(--radius-lg)',
              background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem'
            }}>
              ✓
            </div>
            <div>
              <h3 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 600, marginBottom: 4 }}>
                Gmail Connected
              </h3>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                {status.email || 'Your account is linked and ready'}
              </p>
            </div>
          </div>

          <div className="stats-grid" style={{ marginBottom: 'var(--space-lg)' }}>
            <div className="stat-card">
              <div className="stat-icon">📧</div>
              <div className="stat-value">{status.message_count?.toLocaleString() || '—'}</div>
              <div className="stat-label">Messages Synced</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🔒</div>
              <div className="stat-value">{status.granted_scopes?.length || 0}</div>
              <div className="stat-label">API Scopes</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🕐</div>
              <div className="stat-value" style={{ fontSize: 'var(--font-size-lg)' }}>
                {status.last_sync_at ? new Date(status.last_sync_at).toLocaleDateString() : 'Never'}
              </div>
              <div className="stat-label">Last Sync</div>
            </div>
          </div>

          {status.granted_scopes && (
            <div style={{ marginBottom: 'var(--space-xl)' }}>
              <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-sm)' }}>
                Granted Permissions
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)' }}>
                {status.granted_scopes.map((scope, i) => (
                  <span key={i} className="tag tag-primary">
                    {scope.split('/').pop()}
                  </span>
                ))}
              </div>
            </div>
          )}

          <button className="btn btn-danger" onClick={onDisconnect}>
            Disconnect Gmail
          </button>
        </div>
      ) : (
        /* Disconnected State — Hero */
        <div className="glass-card connect-hero">
          <div className="connect-icon">📬</div>
          <h2>Connect Your Gmail</h2>
          <p>
            Atlas uses read-only access to organize your inbox with AI-powered labels 
            and answer natural-language questions about your email.
          </p>

          <button 
            className="btn btn-primary btn-lg" 
            onClick={handleConnect}
            disabled={loading}
          >
            {loading ? (
              <span className="loading-spinner">
                <span className="spinner"></span>
                Connecting...
              </span>
            ) : (
              <>
                <span>🔐</span>
                Connect with Google
              </>
            )}
          </button>

          <div className="connect-features">
            <div className="feature-item">
              <div className="feature-icon">🏷️</div>
              <h4>Smart Labels</h4>
              <p>Define custom labels with plain-English descriptions. Atlas classifies your email consistently.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔍</div>
              <h4>Natural-Language Search</h4>
              <p>Ask questions like "How many recruiters contacted me last month?" and get evidence-backed answers.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🎯</div>
              <h4>Mailbox Scopes</h4>
              <p>Control exactly what Atlas can search — Primary only, exclude Promotions, last 30 days, and more.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔒</div>
              <h4>Privacy First</h4>
              <p>Local-first architecture. Your tokens are encrypted at rest. No data leaves your machine.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

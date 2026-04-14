import { useState, useEffect } from 'react'
import { scopes } from '../services/api'

// Gmail system labels for the scope builder
const SYSTEM_LABELS = [
  { id: 'INBOX', name: 'Inbox', icon: '📥' },
  { id: 'CATEGORY_PERSONAL', name: 'Personal', icon: '👤' },
  { id: 'CATEGORY_SOCIAL', name: 'Social', icon: '👥' },
  { id: 'CATEGORY_PROMOTIONS', name: 'Promotions', icon: '📢' },
  { id: 'CATEGORY_UPDATES', name: 'Updates', icon: '🔔' },
  { id: 'CATEGORY_FORUMS', name: 'Forums', icon: '💬' },
  { id: 'SENT', name: 'Sent', icon: '📤' },
  { id: 'STARRED', name: 'Starred', icon: '⭐' },
  { id: 'IMPORTANT', name: 'Important', icon: '⚡' },
]

export default function ScopesPage({ userId, isConnected }) {
  const [scopeList, setScopeList] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({
    name: '',
    include_system_labels: [],
    exclude_system_labels: [],
    default_date_window: 180,
  })

  useEffect(() => {
    if (!userId || !isConnected) {
      setLoading(false)
      return
    }
    loadScopes()
  }, [userId, isConnected])

  const loadScopes = async () => {
    setLoading(true)
    try {
      const data = await scopes.list(userId)
      setScopeList(data)
    } catch (error) {
      console.error('Failed to load scopes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await scopes.create(userId, {
        ...formData,
        include_system_labels: formData.include_system_labels.length > 0 ? formData.include_system_labels : null,
        exclude_system_labels: formData.exclude_system_labels.length > 0 ? formData.exclude_system_labels : null,
      })
      setShowModal(false)
      setFormData({ name: '', include_system_labels: [], exclude_system_labels: [], default_date_window: 180 })
      await loadScopes()
    } catch (error) {
      console.error('Failed to create scope:', error)
    }
  }

  const handleDelete = async (scopeId) => {
    if (!confirm('Delete this scope?')) return
    try {
      await scopes.delete(scopeId)
      await loadScopes()
    } catch (error) {
      console.error('Failed to delete scope:', error)
    }
  }

  const toggleLabel = (labelId, field) => {
    setFormData(prev => {
      const current = prev[field]
      const updated = current.includes(labelId)
        ? current.filter(id => id !== labelId)
        : [...current, labelId]
      return { ...prev, [field]: updated }
    })
  }

  if (!isConnected) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h2>Mailbox Scopes</h2>
          <p>Define what segments of your mailbox Atlas can search and organize.</p>
        </div>
        <div className="glass-card empty-state">
          <div className="empty-icon">🎯</div>
          <h3>Gmail Not Connected</h3>
          <p>Connect your Gmail account first to create and manage mailbox scopes.</p>
          <a href="/connect" className="btn btn-primary">Connect Gmail</a>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Mailbox Scopes</h2>
          <p>Define what segments of your mailbox Atlas can search and organize.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + New Scope
        </button>
      </div>

      {loading ? (
        <div style={{ padding: 'var(--space-2xl)', textAlign: 'center' }}>
          <span className="loading-spinner">
            <span className="spinner"></span>
            Loading scopes...
          </span>
        </div>
      ) : scopeList.length > 0 ? (
        <div className="scope-grid">
          {scopeList.map((scope) => (
            <div key={scope.id} className="scope-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <h4>{scope.name}</h4>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(scope.id)}
                  style={{ padding: '4px 8px', fontSize: '0.7rem' }}
                >
                  ✕
                </button>
              </div>

              {scope.include_system_labels?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-sm)' }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', display: 'block', marginBottom: 4 }}>
                    Include:
                  </span>
                  <div className="scope-labels">
                    {scope.include_system_labels.map(lbl => {
                      const info = SYSTEM_LABELS.find(s => s.id === lbl)
                      return (
                        <span key={lbl} className="tag tag-success">
                          {info?.icon || '📁'} {info?.name || lbl}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              {scope.exclude_system_labels?.length > 0 && (
                <div style={{ marginBottom: 'var(--space-sm)' }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', display: 'block', marginBottom: 4 }}>
                    Exclude:
                  </span>
                  <div className="scope-labels">
                    {scope.exclude_system_labels.map(lbl => {
                      const info = SYSTEM_LABELS.find(s => s.id === lbl)
                      return (
                        <span key={lbl} className="tag tag-danger">
                          {info?.icon || '📁'} {info?.name || lbl}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              <div className="scope-meta">
                📅 Last {scope.default_date_window} days
                &nbsp;·&nbsp;
                Created {new Date(scope.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-card empty-state">
          <div className="empty-icon">🎯</div>
          <h3>No Scopes Yet</h3>
          <p>Create a scope to define which parts of your mailbox Atlas should search and organize.</p>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            Create Your First Scope
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Scope</h3>
              <button className="btn btn-icon btn-secondary" onClick={() => setShowModal(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Scope Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Primary Only, Work Emails, Everything..."
                  value={formData.name}
                  onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Include Labels</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)' }}>
                  {SYSTEM_LABELS.map(lbl => (
                    <button
                      key={lbl.id}
                      type="button"
                      className={`tag ${formData.include_system_labels.includes(lbl.id) ? 'tag-success' : 'tag-primary'}`}
                      style={{ cursor: 'pointer', transition: 'all var(--transition-fast)' }}
                      onClick={() => toggleLabel(lbl.id, 'include_system_labels')}
                    >
                      {lbl.icon} {lbl.name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Exclude Labels</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)' }}>
                  {SYSTEM_LABELS.map(lbl => (
                    <button
                      key={lbl.id}
                      type="button"
                      className={`tag ${formData.exclude_system_labels.includes(lbl.id) ? 'tag-danger' : 'tag-primary'}`}
                      style={{ cursor: 'pointer', transition: 'all var(--transition-fast)' }}
                      onClick={() => toggleLabel(lbl.id, 'exclude_system_labels')}
                    >
                      {lbl.icon} {lbl.name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Date Window (days)</label>
                <input
                  type="number"
                  className="form-input"
                  min="1"
                  max="3650"
                  value={formData.default_date_window}
                  onChange={e => setFormData(prev => ({ ...prev, default_date_window: parseInt(e.target.value) || 180 }))}
                />
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={!formData.name}>
                  Create Scope
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Atlas — API Service Layer
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = '/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new ApiError(
        data.detail || `Request failed with status ${response.status}`,
        response.status,
        data
      );
    }

    // Handle 204 No Content
    if (response.status === 204) return null;
    
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(error.message || 'Network error', 0, null);
  }
}

// ── Auth ────────────────────────────────────

export const auth = {
  getConnectUrl: () => request('/auth/connect'),
  
  getStatus: (userId) => request(`/auth/status?user_id=${userId}`),
  
  disconnect: (userId) => request(`/auth/disconnect?user_id=${userId}`, { method: 'POST' }),
};

// ── Scopes ──────────────────────────────────

export const scopes = {
  list: (userId) => request(`/scopes?user_id=${userId}`),
  
  get: (scopeId) => request(`/scopes/${scopeId}`),
  
  create: (userId, data) => request(`/scopes?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  update: (scopeId, data) => request(`/scopes/${scopeId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  
  delete: (scopeId) => request(`/scopes/${scopeId}`, { method: 'DELETE' }),
  
  preview: (scopeId, userId) => request(`/scopes/${scopeId}/preview?user_id=${userId}`, {
    method: 'POST',
  }),
};

// ── Messages ────────────────────────────────

export const messages = {
  list: (userId, { page = 1, pageSize = 50, search, label } = {}) => {
    const params = new URLSearchParams({ user_id: userId, page, page_size: pageSize });
    if (search) params.set('search', search);
    if (label) params.set('label', label);
    return request(`/messages?${params}`);
  },
  
  syncStatus: (userId) => request(`/messages/sync/status?user_id=${userId}`),
  
  triggerSync: (userId, { days, incremental = false } = {}) => {
    const params = new URLSearchParams({ user_id: userId });
    if (days) params.set('days', days);
    if (incremental) params.set('incremental', 'true');
    return request(`/messages/sync?${params}`, { method: 'POST' });
  },
  
  labels: (userId) => request(`/messages/labels?user_id=${userId}`),
};

// ── Health ──────────────────────────────────

export const system = {
  health: () => request('/health'),
};

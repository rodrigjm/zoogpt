import { useAuthStore } from '../stores/authStore'

const API_BASE = '/api/admin'

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchWithAuth(endpoint: string, options: FetchOptions = {}): Promise<Response> {
  const { token, logout } = useAuthStore.getState()
  const { params, ...fetchOptions } = options

  // Build URL with query params
  let url = `${API_BASE}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.set(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += `?${queryString}`
    }
  }

  const headers = new Headers(fetchOptions.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (!headers.has('Content-Type') && fetchOptions.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  })

  if (response.status === 401) {
    logout()
    throw new ApiError(401, 'Session expired. Please login again.')
  }

  return response
}

async function api<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const response = await fetchWithAuth(endpoint, options)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new ApiError(response.status, error.detail || 'Request failed')
  }

  return response.json()
}

// Analytics API
export const analyticsApi = {
  getDashboard: (days = 7) =>
    api<import('../types').DashboardData>('/analytics/dashboard', { params: { days } }),

  getSessions: (params?: { start_date?: string; end_date?: string; limit?: number; offset?: number }) =>
    api<{ total: number; sessions: import('../types').SessionSummary[] }>('/analytics/sessions', { params }),

  getSessionInteractions: (sessionId: string, limit = 100) =>
    api<{ total: number; interactions: import('../types').InteractionDetail[] }>(
      `/analytics/sessions/${sessionId}/interactions`,
      { params: { limit } }
    ),

  searchInteractions: (params?: {
    search?: string
    animal?: string
    start_date?: string
    end_date?: string
    min_confidence?: number
    limit?: number
    offset?: number
  }) =>
    api<{ total: number; interactions: import('../types').InteractionDetail[] }>('/analytics/interactions', { params }),

  getLatencyBreakdown: (days = 7) =>
    api<import('../types').LatencyBreakdown>('/analytics/latency-breakdown', { params: { days } }),
}

// Knowledge Base API
export const kbApi = {
  getAnimals: (params?: { search?: string; category?: string; is_active?: boolean; limit?: number; offset?: number }) =>
    api<{ total: number; animals: import('../types').Animal[] }>('/kb/animals', { params }),

  createAnimal: (data: { name: string; display_name: string; category?: string }) =>
    api<import('../types').Animal>('/kb/animals', { method: 'POST', body: JSON.stringify(data) }),

  getAnimal: (id: number) =>
    api<import('../types').AnimalDetail>(`/kb/animals/${id}`),

  updateAnimal: (id: number, data: { display_name?: string; category?: string; is_active?: boolean }) =>
    api<import('../types').Animal>(`/kb/animals/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteAnimal: (id: number) =>
    fetchWithAuth(`/kb/animals/${id}`, { method: 'DELETE' }),

  addSource: (animalId: number, data: { title: string; url?: string; content: string }) =>
    api<import('../types').Source>(`/kb/animals/${animalId}/sources`, { method: 'POST', body: JSON.stringify(data) }),

  deleteSource: (animalId: number, sourceId: number) =>
    fetchWithAuth(`/kb/animals/${animalId}/sources/${sourceId}`, { method: 'DELETE' }),

  getIndexStatus: () =>
    api<import('../types').IndexStatus>('/kb/index/status'),

  rebuildIndex: () =>
    api<{ job_id: string; status: string; started_at: string }>('/kb/index/rebuild', { method: 'POST' }),
}

// Configuration API
export const configApi = {
  getPrompts: () =>
    api<import('../types').PromptsConfig>('/config/prompts'),

  updatePrompts: (data: import('../types').PromptsConfig) =>
    api<import('../types').PromptsConfig>('/config/prompts', { method: 'PUT', body: JSON.stringify(data) }),

  getModel: () =>
    api<import('../types').ModelConfig>('/config/model'),

  updateModel: (data: import('../types').ModelConfig) =>
    api<import('../types').ModelConfig>('/config/model', { method: 'PUT', body: JSON.stringify(data) }),

  getTTS: () =>
    api<import('../types').TTSConfig>('/config/tts'),

  updateTTS: (data: Partial<import('../types').TTSConfig>) =>
    api<import('../types').TTSConfig>('/config/tts', { method: 'PUT', body: JSON.stringify(data) }),

  getFullConfig: () =>
    api<import('../types').FullConfig>('/config/full'),
}

// Images API
export const imagesApi = {
  getAnimals: () =>
    api<{ animals: Record<string, import('../types').AnimalImageConfig> }>('/images/animals'),

  getAnimal: (name: string) =>
    api<import('../types').AnimalImageDetail>(`/images/animals/${encodeURIComponent(name)}`),

  updateAnimal: (name: string, data: import('../types').UpdateAnimalImagesRequest) =>
    api<import('../types').AnimalImageDetail>(`/images/animals/${encodeURIComponent(name)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  uploadImage: async (name: string, file: File): Promise<import('../types').ImageUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const { token } = useAuthStore.getState()
    const response = await fetch(`${API_BASE}/images/animals/${encodeURIComponent(name)}/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new ApiError(response.status, error.detail || 'Upload failed')
    }

    return response.json()
  },

  deleteImage: (name: string, filename: string) =>
    fetchWithAuth(`/images/animals/${encodeURIComponent(name)}/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    }),

  syncImages: () =>
    api<{ ok: boolean; added: string[]; removed: string[]; total_files: number }>('/images/sync', { method: 'POST' }),
}

// Feedback API
export const feedbackApi = {
  getStats: (days = 7) =>
    api<import('../types').FeedbackStats>('/feedback/stats', { params: { days } }),

  getList: (params?: { type?: string; flagged?: boolean; limit?: number; offset?: number }) =>
    api<{ total: number; items: import('../types').FeedbackItem[] }>('/feedback/list', { params }),

  toggleFlag: (id: number) =>
    api<import('../types').FeedbackItem>(`/feedback/${id}/flag`, { method: 'PATCH' }),

  markReviewed: (id: number) =>
    api<import('../types').FeedbackItem>(`/feedback/${id}/reviewed`, { method: 'PATCH' }),
}

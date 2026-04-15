const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export interface PaperTradingSession {
  id: number
  session_id: string
  strategy_id: string
  symbols: string[]
  initial_cash: number
  start_date: string | null
  end_date: string | null
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'success' | 'error'
  logs: string | null
  created_at: string
  updated_at: string
}

export interface PaperTradingSessionCreatePayload {
  session_id: string
  strategy_id: string
  symbols: string[]
  initial_cash: number
  start_date?: string
  end_date?: string
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }
  if (resp.status === 204) {
    return undefined as unknown as T
  }
  return resp.json() as Promise<T>
}

export const paperTradingApi = {
  list(): Promise<PaperTradingSession[]> {
    return request('/paper-trading/sessions')
  },
  get(session_id: string): Promise<PaperTradingSession> {
    return request(`/paper-trading/sessions/${session_id}`)
  },
  create(payload: PaperTradingSessionCreatePayload): Promise<PaperTradingSession> {
    return request('/paper-trading/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  remove(session_id: string): Promise<void> {
    return request(`/paper-trading/sessions/${session_id}`, {
      method: 'DELETE',
    })
  },
  run(session_id: string): Promise<PaperTradingSession> {
    return request(`/paper-trading/sessions/${session_id}/run`, {
      method: 'POST',
    })
  },
  stop(session_id: string): Promise<PaperTradingSession> {
    return request(`/paper-trading/sessions/${session_id}/stop`, {
      method: 'POST',
    })
  },
}

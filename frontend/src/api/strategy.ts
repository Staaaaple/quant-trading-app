const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export interface Strategy {
  id: number
  strategy_id: string
  name: string
  code: string
  created_at: string
  updated_at: string
}

export interface StrategyCreatePayload {
  strategy_id: string
  name: string
  code: string
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

export const strategyApi = {
  list(): Promise<Strategy[]> {
    return request('/strategies')
  },
  get(strategy_id: string): Promise<Strategy> {
    return request(`/strategies/${strategy_id}`)
  },
  create(payload: StrategyCreatePayload): Promise<Strategy> {
    return request('/strategies', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  update(strategy_id: string, payload: Partial<StrategyCreatePayload>): Promise<Strategy> {
    return request(`/strategies/${strategy_id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
  remove(strategy_id: string): Promise<void> {
    return request(`/strategies/${strategy_id}`, {
      method: 'DELETE',
    })
  },
}

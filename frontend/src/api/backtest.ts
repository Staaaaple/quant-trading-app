const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export interface Backtest {
  id: number
  backtest_id: string
  strategy_id: string
  status: 'pending' | 'running' | 'success' | 'failed'
  start_date: string
  end_date: string
  initial_cash: number
  metrics: Record<string, any> | null
  logs: string | null
  created_at: string
  updated_at: string
}

export interface BacktestCreatePayload {
  backtest_id: string
  strategy_id: string
  start_date: string
  end_date: string
  initial_cash: number
}

export interface BacktestRunPayload {
  symbols: string[]
  start_date: string
  end_date: string
  initial_cash: number
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

export const backtestApi = {
  list(): Promise<Backtest[]> {
    return request('/backtests')
  },
  get(backtest_id: string): Promise<Backtest> {
    return request(`/backtests/${backtest_id}`)
  },
  create(payload: BacktestCreatePayload): Promise<Backtest> {
    return request('/backtests', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  run(backtest_id: string, payload: BacktestRunPayload): Promise<Backtest> {
    return request(`/backtests/${backtest_id}/run`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export interface RiskStrategyConfig {
  strategy_id: string
  max_position_pct: number
  max_daily_drawdown: number
  blacklist: string
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

export const riskStrategyApi = {
  get(strategy_id: string): Promise<RiskStrategyConfig> {
    return request(`/risk-strategies/${strategy_id}`)
  },
  create(payload: RiskStrategyConfig): Promise<RiskStrategyConfig> {
    return request('/risk-strategies', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  update(strategy_id: string, payload: Partial<RiskStrategyConfig>): Promise<RiskStrategyConfig> {
    return request(`/risk-strategies/${strategy_id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
}

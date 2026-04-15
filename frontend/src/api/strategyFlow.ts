const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export interface StrategyFlow {
  id: number
  flow_id: string
  name: string
  picker_strategy_id: string | null
  risk_strategy_id: string | null
  trade_strategy_id: string
  created_at: string
  updated_at: string
}

export interface StrategyFlowCreatePayload {
  flow_id: string
  name: string
  picker_strategy_id?: string
  risk_strategy_id?: string
  trade_strategy_id: string
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

export const strategyFlowApi = {
  list(): Promise<StrategyFlow[]> {
    return request('/strategy-flows')
  },
  get(flow_id: string): Promise<StrategyFlow> {
    return request(`/strategy-flows/${flow_id}`)
  },
  create(payload: StrategyFlowCreatePayload): Promise<StrategyFlow> {
    return request('/strategy-flows', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  update(flow_id: string, payload: Partial<StrategyFlowCreatePayload>): Promise<StrategyFlow> {
    return request(`/strategy-flows/${flow_id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
  remove(flow_id: string): Promise<void> {
    return request(`/strategy-flows/${flow_id}`, {
      method: 'DELETE',
    })
  },
}

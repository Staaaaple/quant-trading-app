import { request } from './client'

export interface Strategy {
  id: number
  strategy_id: string
  name: string
  type: string
  code: string
  created_at: string
  updated_at: string
}

export interface StrategyCreatePayload {
  strategy_id: string
  name: string
  code: string
  type?: string
}

export const strategyApi = {
  list(query?: string): Promise<Strategy[]> {
    return request(`/strategies${query || ''}`)
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

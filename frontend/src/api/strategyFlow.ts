import { request } from './client'

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

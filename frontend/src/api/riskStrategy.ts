import { request } from './client'

export interface RiskStrategyConfig {
  strategy_id: string
  max_position_pct: number
  max_daily_drawdown: number
  blacklist: string
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

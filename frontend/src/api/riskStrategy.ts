import { delay } from './mock/utils'
import { DEMO_RISK_STRATEGY } from './mock/demoData'

export interface RiskStrategyConfig {
  strategy_id: string
  max_position_pct: number
  max_daily_drawdown: number
  blacklist: string
}

export const riskStrategyApi = {
  get(_strategy_id: string): Promise<RiskStrategyConfig> {
    return delay(300).then(() => DEMO_RISK_STRATEGY as RiskStrategyConfig)
  },
  create(payload: RiskStrategyConfig): Promise<RiskStrategyConfig> {
    return delay(500).then(() => payload)
  },
  update(_strategy_id: string, payload: Partial<RiskStrategyConfig>): Promise<RiskStrategyConfig> {
    return delay(400).then(() => ({ ...DEMO_RISK_STRATEGY, ...payload } as RiskStrategyConfig))
  },
}

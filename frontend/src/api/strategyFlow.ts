import { delay } from './mock/utils'
import { DEMO_STRATEGY_FLOWS } from './mock/demoData'

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
    return delay(300).then(() => DEMO_STRATEGY_FLOWS as StrategyFlow[])
  },
  get(_flow_id: string): Promise<StrategyFlow> {
    return delay(300).then(() => DEMO_STRATEGY_FLOWS[0] as StrategyFlow)
  },
  create(payload: StrategyFlowCreatePayload): Promise<StrategyFlow> {
    return delay(500).then(() => ({ ...DEMO_STRATEGY_FLOWS[0], ...payload } as StrategyFlow))
  },
  update(flow_id: string, payload: Partial<StrategyFlowCreatePayload>): Promise<StrategyFlow> {
    return delay(400).then(() => {
      const existing = DEMO_STRATEGY_FLOWS.find((f: any) => f.flow_id === flow_id) || DEMO_STRATEGY_FLOWS[0]
      return { ...existing, ...payload } as StrategyFlow
    })
  },
  remove(_flow_id: string): Promise<void> {
    return delay(300).then(() => undefined)
  },
}

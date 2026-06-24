import { delay } from './mock/utils'
import { DEMO_BACKTEST, DEMO_BACKTESTS } from './mock/demoData'

export interface Backtest {
  id: number
  backtest_id: string
  strategy_id: string
  status: 'pending' | 'running' | 'success' | 'failed'
  start_date: string
  end_date: string
  initial_cash: number
  metrics: Record<string, any> | null
  benchmark_metrics: Record<string, any> | null
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

export const backtestApi = {
  list(): Promise<Backtest[]> {
    return delay(300).then(() => DEMO_BACKTESTS as Backtest[])
  },
  get(backtest_id: string): Promise<Backtest> {
    const bt = DEMO_BACKTESTS.find((b) => b.backtest_id === backtest_id) || DEMO_BACKTEST
    return delay(300).then(() => bt as Backtest)
  },
  create(payload: BacktestCreatePayload): Promise<Backtest> {
    return delay(500).then(() => ({ ...DEMO_BACKTEST, ...payload } as Backtest))
  },
  run(_backtest_id: string, payload: BacktestRunPayload): Promise<Backtest> {
    return delay(800).then(() => ({ ...DEMO_BACKTEST, ...payload } as Backtest))
  },
  remove(_backtest_id: string): Promise<void> {
    return delay(300).then(() => undefined)
  },
}

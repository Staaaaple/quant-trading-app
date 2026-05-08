import { request } from './client'

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
  remove(backtest_id: string): Promise<void> {
    return request(`/backtests/${backtest_id}`, {
      method: 'DELETE',
    })
  },
}

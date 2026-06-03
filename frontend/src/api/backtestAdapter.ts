import client from './client'

export interface BacktestAdapterPayload {
  portfolio_id: string
  symbols: string[]
  start_date: string
  end_date: string
  initial_cash: number
  strategy_configs?: Record<string, any>[]
}

export interface BacktestAdapterResult {
  backtest_id: string
  status: string
  metrics: {
    total_return: number
    annual_return: number
    sharpe_ratio: number
    max_drawdown: number
    volatility: number
    win_rate: number
  }
  benchmark_metrics?: {
    total_return: number
    annual_return: number
    max_drawdown: number
  }
  trades: Array<{
    date: string
    symbol: string
    action: string
    quantity: number
    price: number
  }>
  daily_values: Array<{
    date: string
    value: number
  }>
}

export const backtestAdapterApi = {
  run: (payload: BacktestAdapterPayload) =>
    client.post<BacktestAdapterResult>('/backtest-adapter/run', payload).then(r => r.data),
}

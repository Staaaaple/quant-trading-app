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

// 模拟内存中的回测记录，初始为空
// 点「一键运行回测」后才会生成记录
const createdBacktests: Backtest[] = []
let nextId = 1

function findTemplate(strategy_id: string) {
  return DEMO_BACKTESTS.find((b) => b.strategy_id === strategy_id) || DEMO_BACKTEST
}

export const backtestApi = {
  list(): Promise<Backtest[]> {
    return delay(300).then(() => [...createdBacktests])
  },
  get(backtest_id: string): Promise<Backtest> {
    const bt = createdBacktests.find((b) => b.backtest_id === backtest_id)
      || DEMO_BACKTESTS.find((b) => b.backtest_id === backtest_id)
      || DEMO_BACKTEST
    return delay(300).then(() => bt as Backtest)
  },
  create(payload: BacktestCreatePayload): Promise<Backtest> {
    const now = new Date().toISOString()
    const bt: Backtest = {
      id: nextId++,
      backtest_id: payload.backtest_id,
      strategy_id: payload.strategy_id,
      status: 'pending',
      start_date: payload.start_date,
      end_date: payload.end_date,
      initial_cash: payload.initial_cash,
      metrics: null,
      benchmark_metrics: null,
      logs: null,
      created_at: now,
      updated_at: now,
    }
    createdBacktests.push(bt)
    return delay(150).then(() => bt)
  },
  run(backtest_id: string, payload: BacktestRunPayload): Promise<Backtest> {
    const now = new Date().toISOString()
    const existing = createdBacktests.find((b) => b.backtest_id === backtest_id)
    const template = findTemplate(existing?.strategy_id || '')
    if (existing) {
      existing.status = 'success'
      existing.metrics = template.metrics
      existing.benchmark_metrics = template.benchmark_metrics
      existing.logs = template.logs
      existing.updated_at = now
    }
    return delay(250).then(() => {
      if (existing) return existing
      // fallback：如果找不到已创建记录，返回模板数据
      return {
        ...template,
        backtest_id,
        ...payload,
        status: 'success',
      } as Backtest
    })
  },
  remove(backtest_id: string): Promise<void> {
    const idx = createdBacktests.findIndex((b) => b.backtest_id === backtest_id)
    if (idx >= 0) createdBacktests.splice(idx, 1)
    return delay(300).then(() => undefined)
  },
}

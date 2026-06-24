import { delay } from './mock/utils'
import { DEMO_REAL_TRADES, DEMO_REAL_POSITIONS, DEMO_SYNC_LOGS, DEMO_PAPER_SIGNALS } from './mock/demoData'

export interface RealTrade {
  id: number
  signal_id: string | null
  strategy_id: string
  symbol: string
  side: string
  quantity: number
  price: number
  commission: number
  stamp_tax: number
  transfer_fee: number
  total_cost: number
  sync_status: string
  source: string
  remark: string | null
  synced_at: string
}

export interface RealTradeCreatePayload {
  signal_id?: string | null
  strategy_id: string
  symbol: string
  side: string
  quantity: number
  price: number
  commission?: number
  stamp_tax?: number
  transfer_fee?: number
  total_cost: number
  sync_status?: string
  source?: string
  remark?: string | null
}

export interface RealPosition {
  id: number
  strategy_id: string
  symbol: string
  quantity: number
  available_qty: number
  avg_cost: number
  total_cost: number
  market_value: number
  floating_pnl: number
  updated_at: string
}

export interface SyncLog {
  id: number
  signal_id: string | null
  strategy_id: string
  symbol: string
  signal_side: string | null
  signal_qty: number | null
  signal_price: number | null
  actual_qty: number | null
  actual_price: number | null
  diff_reason: string | null
  created_at: string
}

export interface DiffItem {
  symbol: string
  status: 'match' | 'mismatch' | 'missing_real' | 'extra_real'
  signal_qty: number
  signal_side: string | null
  real_qty: number
  message: string
}

export interface DiffResult {
  strategy_id: string
  diffs: DiffItem[]
}

export interface PaperSignal {
  id: number
  signal_id: string
  strategy_id: string
  symbol: string
  side: string
  quantity: number
  price: number | null
  status: string
  remark: string | null
  signal_at: string
}

export interface PendingSummary {
  pending_count: number
  overdue_count: number
  threshold_minutes: number
}

export interface DailyReport {
  trade_date: string
  strategy_id: string
  simulated_signals_count: number
  pending_signals_count: number
  synced_signals_count: number
  real_trades_count: number
  real_pnl: number
  positions: { symbol: string; quantity: number; avg_cost: number }[]
  diffs: DiffItem[]
  unsynced_list: DiffItem[]
  message: string
}

export const syncApi = {
  listTrades(): Promise<RealTrade[]> {
    return delay(300).then(() => DEMO_REAL_TRADES as RealTrade[])
  },
  createTrade(payload: RealTradeCreatePayload): Promise<RealTrade> {
    return delay(400).then(() => ({ id: Date.now(), ...payload, synced_at: new Date().toISOString() } as RealTrade))
  },
  deleteTrade(_tradeId: number): Promise<void> {
    return delay(300).then(() => undefined)
  },
  listPositions(_strategyId?: string): Promise<RealPosition[]> {
    return delay(300).then(() => DEMO_REAL_POSITIONS as RealPosition[])
  },
  listLogs(): Promise<SyncLog[]> {
    return delay(300).then(() => DEMO_SYNC_LOGS as SyncLog[])
  },
  getDiff(_strategyId: string): Promise<DiffResult> {
    return delay(300).then(() => ({ strategy_id: _strategyId, diffs: [] }))
  },
  listSignals(_strategyId?: string, _status?: string): Promise<PaperSignal[]> {
    return delay(300).then(() => DEMO_PAPER_SIGNALS as PaperSignal[])
  },
  getPendingSummary(_thresholdMinutes = 30): Promise<PendingSummary> {
    return delay(300).then(() => ({ pending_count: 0, overdue_count: 0, threshold_minutes: _thresholdMinutes }))
  },
  getDailyReport(_strategyId: string, _tradeDate?: string): Promise<DailyReport> {
    return delay(400).then(() => ({
      trade_date: _tradeDate || new Date().toISOString().split('T')[0],
      strategy_id: _strategyId,
      simulated_signals_count: 0,
      pending_signals_count: 0,
      synced_signals_count: 0,
      real_trades_count: 0,
      real_pnl: 0,
      positions: [],
      diffs: [],
      unsynced_list: [],
      message: '今日无交易',
    }))
  },
  batchSync(_items: { signal_id: string; actual_price: number; actual_qty?: number; sync_status?: string; remark?: string }[]): Promise<{ created: number; errors: string[] }> {
    return delay(500).then(() => ({ created: _items.length, errors: [] }))
  },
  importCsv(_file: File): Promise<{ created: number; errors: string[] }> {
    return delay(800).then(() => ({ created: 0, errors: [] }))
  },
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

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

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }
  if (resp.status === 204) {
    return undefined as unknown as T
  }
  return resp.json() as Promise<T>
}

export const syncApi = {
  listTrades(): Promise<RealTrade[]> {
    return request('/sync/trades')
  },
  createTrade(payload: RealTradeCreatePayload): Promise<RealTrade> {
    return request('/sync/trades', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  deleteTrade(tradeId: number): Promise<void> {
    return request(`/sync/trades/${tradeId}`, {
      method: 'DELETE',
    })
  },
  listPositions(strategyId?: string): Promise<RealPosition[]> {
    const query = strategyId ? `?strategy_id=${encodeURIComponent(strategyId)}` : ''
    return request(`/sync/positions${query}`)
  },
  listLogs(): Promise<SyncLog[]> {
    return request('/sync/logs')
  },
  getDiff(strategyId: string): Promise<DiffResult> {
    return request(`/sync/diff/${encodeURIComponent(strategyId)}`)
  },
  listSignals(strategyId?: string, status?: string): Promise<PaperSignal[]> {
    const params = new URLSearchParams()
    if (strategyId) params.append('strategy_id', strategyId)
    if (status) params.append('status', status)
    const query = params.toString() ? `?${params.toString()}` : ''
    return request(`/paper-trading/signals${query}`)
  },
  getPendingSummary(thresholdMinutes = 30): Promise<PendingSummary> {
    return request(`/sync/pending-summary?threshold_minutes=${thresholdMinutes}`)
  },
  getDailyReport(strategyId: string, tradeDate?: string): Promise<DailyReport> {
    const q = tradeDate ? `?trade_date=${tradeDate}` : ''
    return request(`/sync/daily-report/${encodeURIComponent(strategyId)}${q}`)
  },
  batchSync(items: { signal_id: string; actual_price: number; actual_qty?: number; sync_status?: string; remark?: string }[]): Promise<{ created: number; errors: string[] }> {
    return request('/sync/batch-sync', {
      method: 'POST',
      body: JSON.stringify(items),
    })
  },
  importCsv(file: File): Promise<{ created: number; errors: string[] }> {
    const formData = new FormData()
    formData.append('file', file)
    return fetch(`${API_BASE}/sync/import-csv`, {
      method: 'POST',
      body: formData,
    }).then(async (resp) => {
      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(`HTTP ${resp.status}: ${text}`)
      }
      return resp.json()
    })
  },
}

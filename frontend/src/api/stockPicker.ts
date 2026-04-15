const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export interface StockPoolItem {
  id: number
  symbol: string
  name?: string
  score?: number
  reason?: string
}

export interface StockPool {
  id: number
  pool_id: string
  picker_id: string
  name: string
  is_builtin_weekly: boolean
  generated_at: string
  expires_at?: string
  items: StockPoolItem[]
}

export interface PickerRun {
  id: number
  run_id: string
  picker_id: string
  status: string
  result_count?: number
  logs?: string
  created_at: string
  finished_at?: string
}

export interface WeeklySummary {
  has_new_weekly: boolean
  pool?: StockPool
  generated_at?: string
  item_count: number
}

export interface NotificationSettings {
  id: number
  weekly_picker_push: boolean
  updated_at: string
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

export const stockPickerApi = {
  runPicker(picker_id: string): Promise<StockPool> {
    return request('/stock-picker/run', {
      method: 'POST',
      body: JSON.stringify({ picker_id }),
    })
  },
  listPools(picker_id?: string): Promise<StockPool[]> {
    const qs = picker_id ? `?picker_id=${encodeURIComponent(picker_id)}` : ''
    return request(`/stock-picker/pools${qs}`)
  },
  getPool(pool_id: string): Promise<StockPool> {
    return request(`/stock-picker/pools/${pool_id}`)
  },
  listRuns(picker_id?: string): Promise<PickerRun[]> {
    const qs = picker_id ? `?picker_id=${encodeURIComponent(picker_id)}` : ''
    return request(`/stock-picker/runs${qs}`)
  },
  getWeeklySummary(): Promise<WeeklySummary> {
    return request('/stock-picker/weekly-summary')
  },
  getNotificationSettings(): Promise<NotificationSettings> {
    return request('/stock-picker/notification-settings')
  },
  updateNotificationSettings(payload: { weekly_picker_push: boolean }): Promise<NotificationSettings> {
    return request('/stock-picker/notification-settings', {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
}

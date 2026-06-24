import { delay } from './mock/utils'
import { DEMO_STOCK_POOLS, DEMO_PICKER_RUNS } from './mock/demoData'

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

export const stockPickerApi = {
  runPicker(_picker_id: string): Promise<StockPool> {
    return delay(500).then(() => DEMO_STOCK_POOLS[0] as StockPool)
  },
  listPools(_picker_id?: string): Promise<StockPool[]> {
    return delay(300).then(() => DEMO_STOCK_POOLS as StockPool[])
  },
  getPool(_pool_id: string): Promise<StockPool> {
    return delay(300).then(() => DEMO_STOCK_POOLS[0] as StockPool)
  },
  listRuns(_picker_id?: string): Promise<PickerRun[]> {
    return delay(300).then(() => DEMO_PICKER_RUNS as PickerRun[])
  },
  getWeeklySummary(): Promise<WeeklySummary> {
    return delay(300).then(() => ({
      has_new_weekly: true,
      pool: DEMO_STOCK_POOLS[0] as StockPool,
      generated_at: new Date().toISOString(),
      item_count: 3,
    }))
  },
  getNotificationSettings(): Promise<NotificationSettings> {
    return delay(300).then(() => ({
      id: 1,
      weekly_picker_push: true,
      updated_at: new Date().toISOString(),
    }))
  },
  updateNotificationSettings(payload: { weekly_picker_push: boolean }): Promise<NotificationSettings> {
    return delay(400).then(() => ({
      id: 1,
      weekly_picker_push: payload.weekly_picker_push,
      updated_at: new Date().toISOString(),
    }))
  },
}

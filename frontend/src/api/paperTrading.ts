import { delay } from './mock/utils'
import { DEMO_PAPER_TRADING_DAILY_RECORDS, DEMO_PAPER_TRADING_MONTHLY_STATS } from './mock/demoData'

export interface PaperTradingDailyRecord {
  id: number
  user_id: number
  portfolio_id: number | null
  record_date: string
  daily_return: number
  cumulative_return: number
  nav: number
  report_id: number | null
  asset_snapshot: string | null
  created_at: string
  updated_at: string | null
}

export interface PaperTradingMonthlyStat {
  id: number
  user_id: number
  portfolio_id: number | null
  year_month: string
  monthly_return: number
  cumulative_return_at_month_end: number
  record_count: number
  created_at: string
  updated_at: string | null
}

export const paperTradingApi = {
  listDailyRecords(_params?: {
    portfolio_id?: number
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<PaperTradingDailyRecord[]> {
    return delay(300).then(() => DEMO_PAPER_TRADING_DAILY_RECORDS as PaperTradingDailyRecord[])
  },

  listMonthlyStats(_params?: { portfolio_id?: number; limit?: number }): Promise<PaperTradingMonthlyStat[]> {
    return delay(300).then(() => DEMO_PAPER_TRADING_MONTHLY_STATS as PaperTradingMonthlyStat[])
  },

  getLatest(_params?: { portfolio_id?: number }): Promise<PaperTradingDailyRecord | null> {
    return delay(300).then(() => {
      const records = DEMO_PAPER_TRADING_DAILY_RECORDS as PaperTradingDailyRecord[]
      return records[records.length - 1] || null
    })
  },

  syncDaily(_report_date?: string): Promise<{ detail: string; result: Record<string, unknown> }> {
    return delay(500).then(() => ({ detail: '同步完成', result: {} }))
  },

  calcMonthly(_year_month?: string): Promise<{ detail: string; result: Record<string, unknown> }> {
    return delay(500).then(() => ({ detail: '计算完成', result: {} }))
  },
}

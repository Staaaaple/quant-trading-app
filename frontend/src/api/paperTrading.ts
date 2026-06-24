import { request } from './client'

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
  listDailyRecords(params?: {
    portfolio_id?: number
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<PaperTradingDailyRecord[]> {
    const search = new URLSearchParams()
    if (params?.portfolio_id) search.set('portfolio_id', String(params.portfolio_id))
    if (params?.start_date) search.set('start_date', params.start_date)
    if (params?.end_date) search.set('end_date', params.end_date)
    if (params?.limit) search.set('limit', String(params.limit))
    const qs = search.toString()
    return request(`/paper-trading/daily-records${qs ? `?${qs}` : ''}`)
  },

  listMonthlyStats(params?: { portfolio_id?: number; limit?: number }): Promise<PaperTradingMonthlyStat[]> {
    const search = new URLSearchParams()
    if (params?.portfolio_id) search.set('portfolio_id', String(params.portfolio_id))
    if (params?.limit) search.set('limit', String(params.limit))
    const qs = search.toString()
    return request(`/paper-trading/monthly-stats${qs ? `?${qs}` : ''}`)
  },

  getLatest(params?: { portfolio_id?: number }): Promise<PaperTradingDailyRecord | null> {
    const search = new URLSearchParams()
    if (params?.portfolio_id) search.set('portfolio_id', String(params.portfolio_id))
    const qs = search.toString()
    return request(`/paper-trading/latest${qs ? `?${qs}` : ''}`)
  },

  syncDaily(report_date?: string): Promise<{ detail: string; result: Record<string, unknown> }> {
    const search = new URLSearchParams()
    if (report_date) search.set('report_date', report_date)
    const qs = search.toString()
    return request(`/paper-trading/sync-daily${qs ? `?${qs}` : ''}`, { method: 'POST' })
  },

  calcMonthly(year_month?: string): Promise<{ detail: string; result: Record<string, unknown> }> {
    const search = new URLSearchParams()
    if (year_month) search.set('year_month', year_month)
    const qs = search.toString()
    return request(`/paper-trading/calc-monthly${qs ? `?${qs}` : ''}`, { method: 'POST' })
  },
}

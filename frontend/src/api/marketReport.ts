import client from './client'

// ── 市场报告 ──

export interface MarketReportPayload {
  portfolio_id?: number
  report_type?: 'auto' | 'daily' | 'weekly'
}

export function generateMarketReport(payload: MarketReportPayload) {
  return client.post<{ success: boolean; data: any }>('/fullchain/market-report/generate', payload)
}

export function getLatestMarketReport(userId: number, reportType: 'daily' | 'weekly' = 'daily') {
  return client.get<{ success: boolean; data: any; message?: string }>(`/fullchain/market-report/latest/${userId}?report_type=${reportType}`)
}

export function listMarketReports(
  userId: number,
  reportType?: 'daily' | 'weekly',
  limit?: number,
) {
  const params = new URLSearchParams()
  if (reportType) params.append('report_type', reportType)
  if (limit) params.append('limit', String(limit))
  const query = params.toString()
  return client.get<{ success: boolean; data: any[] }>(`/fullchain/market-report/list/${userId}${query ? `?${query}` : ''}`)
}

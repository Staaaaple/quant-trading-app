import { delay } from './mock/utils'
import { DEMO_DAILY_REPORT, DEMO_WEEKLY_REPORT } from './mock/demoData'

// ── 市场报告 ──

export interface MarketReportPayload {
  portfolio_id?: number
  report_type?: 'auto' | 'daily' | 'weekly'
}

export function generateMarketReport(_payload: MarketReportPayload) {
  return delay(500).then(() => ({ data: { success: true, data: DEMO_DAILY_REPORT } }))
}

export function getLatestMarketReport(_userId: number, reportType: 'daily' | 'weekly' = 'daily') {
  return delay(400).then(() => ({
    data: {
      success: true,
      data: reportType === 'daily' ? DEMO_DAILY_REPORT : DEMO_WEEKLY_REPORT,
      message: undefined as string | undefined,
    },
  }))
}

export function listMarketReports(
  _userId: number,
  reportType?: 'daily' | 'weekly',
  _limit?: number,
) {
  return delay(400).then(() => ({
    data: {
      success: true,
      data: reportType === 'weekly' ? [DEMO_WEEKLY_REPORT] : [DEMO_DAILY_REPORT],
    },
  }))
}

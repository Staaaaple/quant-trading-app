import { delay } from './mock/utils'
import { DEMO_DAILY_REPORT, DEMO_WEEKLY_REPORT } from './mock/demoData'

// ── 市场报告 ──

export interface MarketReportPayload {
  portfolio_id?: number
  report_type?: 'auto' | 'daily' | 'weekly'
}

function toFrontendReport(report: Record<string, any>) {
  return {
    report_type: report.report_type,
    report_date: report.report_date,
    page1: report.page1_market_overview,
    page2: report.page2_portfolio_performance,
    page3: report.page3_weekly_market,
  }
}

// 内存中保存已生成的报告，初始为空（与后端行为一致）
let generatedDaily: Record<string, any> | null = null
let generatedWeekly: Record<string, any> | null = null

export function generateMarketReport(payload: MarketReportPayload) {
  const type = payload.report_type === 'weekly' ? 'weekly' : 'daily'
  const report = type === 'weekly'
    ? { ...DEMO_WEEKLY_REPORT, report_date: new Date().toISOString().split('T')[0] }
    : { ...DEMO_DAILY_REPORT, report_date: new Date().toISOString().split('T')[0] }

  if (type === 'weekly') {
    generatedWeekly = report
  } else {
    generatedDaily = report
  }

  return delay(500).then(() => ({ data: { success: true, data: toFrontendReport(report) } }))
}

export function getLatestMarketReport(_userId: number, reportType: 'daily' | 'weekly' = 'daily') {
  const report = reportType === 'weekly' ? generatedWeekly : generatedDaily
  return delay(400).then(() => ({
    data: {
      success: true,
      data: report ? toFrontendReport(report) : null,
      message: report ? undefined : `暂无${reportType}报告，请点击生成报告`,
    },
  }))
}

export function listMarketReports(
  _userId: number,
  reportType?: 'daily' | 'weekly',
  _limit?: number,
) {
  const list: Record<string, any>[] = []
  if (!reportType || reportType === 'daily') {
    if (generatedDaily) list.push(toFrontendReport(generatedDaily))
  }
  if (!reportType || reportType === 'weekly') {
    if (generatedWeekly) list.push(toFrontendReport(generatedWeekly))
  }
  return delay(400).then(() => ({
    data: {
      success: true,
      data: list,
    },
  }))
}

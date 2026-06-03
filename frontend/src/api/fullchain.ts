import client from './client'

// ── 教学引导 ──

export interface OnboardingPayload {
  profile: Record<string, any>
  portfolio: Record<string, any>
}

export function generateOnboarding(payload: OnboardingPayload) {
  return client.post('/fullchain/onboarding/generate', payload)
}

// ── 建仓助手 ──

export interface BuildingPlanPayload {
  total_capital: number
  portfolio_config: Record<string, any>
  risk_label?: string
  market_cycle?: string
}

export function createBuildingPlan(payload: BuildingPlanPayload) {
  return client.post('/fullchain/building/plan', payload)
}

export function getBatchDetail(batchNo: number, payload: Omit<BuildingPlanPayload, 'market_cycle'>) {
  return client.post(`/fullchain/building/batch/${batchNo}`, payload)
}

// ── 推送系统 ──

export interface DailyPushPayload {
  user_id: number
  portfolio: Record<string, any>
  market_signal: Record<string, any>
  strategy_signals: any[]
}

export function generateDailyPush(payload: DailyPushPayload) {
  return client.post('/fullchain/push/daily', payload)
}

export function generateLifespanAlert(payload: {
  portfolio: Record<string, any>
  lifespan_data: Record<string, any>
}) {
  return client.post('/fullchain/push/lifespan-alert', payload)
}

export function generateCycleAlert(payload: {
  old_cycle: string
  new_cycle: string
  market_signal: Record<string, any>
}) {
  return client.post('/fullchain/push/cycle-alert', payload)
}

// ── 调仓提醒 ──

export interface RebalanceCheckPayload {
  portfolio: Record<string, any>
  market_signal: Record<string, any>
  lifespan_data: Record<string, any>
  last_rebalance_date?: string
}

export function checkRebalance(payload: RebalanceCheckPayload) {
  return client.post('/fullchain/rebalance/check', payload)
}

export function getAlternativeStrategies(payload: {
  target_holding: Record<string, any>
  strategy_pool: any[]
  profile: Record<string, any>
  market_signal: Record<string, any>
  top_n?: number
}) {
  return client.post('/fullchain/rebalance/alternatives', payload)
}

export function createRebalancePlan(payload: {
  portfolio: Record<string, any>
  triggers: any[]
  alternatives: Record<string, any[]>
}) {
  return client.post('/fullchain/rebalance/plan', payload)
}

// ── 周报 ──

export interface WeeklyReportPayload {
  user_id: number
  portfolio: Record<string, any>
  market_signal: Record<string, any>
  performance_data: Record<string, any>
  lifespan_data: Record<string, any>
}

export function generateWeeklyReport(payload: WeeklyReportPayload) {
  return client.post('/fullchain/weekly-report/generate', payload)
}

export function getLatestWeeklyReport(userId: number) {
  return client.get(`/fullchain/weekly-report/latest/${userId}`)
}

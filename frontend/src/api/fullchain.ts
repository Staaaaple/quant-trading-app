import { delay } from './mock/utils'
import { DEMO_PORTFOLIO, DEMO_MARKET_SIGNAL } from './mock/demoData'

// ── 教学引导 ──

export interface OnboardingPayload {
  profile: Record<string, any>
  portfolio: Record<string, any>
}

export function generateOnboarding(_payload: OnboardingPayload) {
  return delay(500).then(() => ({ data: { success: true, data: { message: ' onboarding 生成完成' } } }))
}

// ── 建仓助手 ──

export interface BuildingPlanPayload {
  total_capital: number
  portfolio_config: Record<string, any>
  risk_label?: string
  market_cycle?: string
}

export function createBuildingPlan(_payload: BuildingPlanPayload) {
  return delay(500).then(() => ({ data: { success: true, data: { batches: 3, plan: [] } } }))
}

export function getBatchDetail(_batchNo: number, _payload: Omit<BuildingPlanPayload, 'market_cycle'>) {
  return delay(400).then(() => ({ data: { success: true, data: { batch_no: _batchNo, holdings: [] } } }))
}

// ── 推送系统 ──

export interface DailyPushPayload {
  portfolio: Record<string, any>
  market_signal: Record<string, any>
  strategy_signals: any[]
}

export function generateDailyPush(_payload: DailyPushPayload) {
  return delay(500).then(() => ({ data: { success: true, data: { message: '今日推送已生成' } } }))
}

export function generateLifespanAlert(_payload: {
  portfolio: Record<string, any>
  lifespan_data: Record<string, any>
}) {
  return delay(400).then(() => ({ data: { success: true, data: { message: '寿命预警已生成' } } }))
}

export function generateCycleAlert(_payload: {
  old_cycle: string
  new_cycle: string
  market_signal: Record<string, any>
}) {
  return delay(400).then(() => ({ data: { success: true, data: { message: '周期切换提醒已生成' } } }))
}

// ── 调仓提醒 ──

export interface RebalanceCheckPayload {
  portfolio: Record<string, any>
  market_signal: Record<string, any>
  lifespan_data: Record<string, any>
  last_rebalance_date?: string
}

export function checkRebalance(_payload: RebalanceCheckPayload) {
  return delay(500).then(() => ({ data: { success: true, data: { need_rebalance: false, triggers: [] } } }))
}

export function getAlternativeStrategies(_payload: {
  target_holding: Record<string, any>
  strategy_pool: any[]
  profile: Record<string, any>
  market_signal: Record<string, any>
  top_n?: number
}) {
  return delay(500).then(() => ({ data: { success: true, data: { alternatives: [] } } }))
}

export function createRebalancePlan(_payload: {
  portfolio: Record<string, any>
  triggers: any[]
  alternatives: Record<string, any[]>
}) {
  return delay(500).then(() => ({ data: { success: true, data: { plan_id: 'plan_demo_001', actions: [] } } }))
}

// ── 寿命监控 ──

export function runLifespanCheck() {
  return delay(500).then(() => ({ data: { success: true, data: { message: '寿命检查完成' } } }))
}

export function getLifespanTrend(_strategyId: string, _months?: number) {
  return delay(400).then(() => ({ data: { success: true, data: { trend: [] } } }))
}

export function getLifespanAlerts() {
  return delay(400).then(() => ({ data: { success: true, data: { alerts: [] } } }))
}

export function getPortfolioLifespan(_portfolioId: string) {
  return delay(400).then(() => ({ data: { success: true, data: { portfolio_id: _portfolioId, lifespan_months: 30 } } }))
}

export function getReplacementStrategies(_payload: {
  strategy_id: string
  top_k?: number
}) {
  return delay(500).then(() => ({ data: { success: true, data: { replacements: [] } } }))
}

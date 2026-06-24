<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import {
  generateMarketReport,
  getLatestMarketReport,
  listMarketReports,
} from '@/api/marketReport'

type ReportType = 'daily' | 'weekly'
type ActiveTab = 'market' | 'portfolio' | 'weekly'

interface IndexData {
  name: string
  symbol: string
  change_pct: number
  open: number
  high: number
  low: number
  close: number
  prev_close: number
  volume: number
  amount: number
}

interface SectorData {
  name: string
  change_pct: number
  fund_flow: number
  main_force: number
  rank: number
}

interface Policy {
  publish_time?: string
  publisher?: string
  title: string
  core_items?: string[]
  market_reaction?: string
  significance?: string
}

interface PolicyChanges {
  has_policy: boolean
  summary: string
  policies: Policy[]
}

interface RiskSignals {
  volatility_regime: string
  sentiment: string
  alerts: string[]
}

interface NorthboundFund {
  net_inflow: number
  cumulative_inflow: number
  leading_sectors: string[]
  external_env: string
  inference: string
}

interface Outlook {
  short_term: string
  medium_term: string
  risks: string[]
}

interface Page1MarketOverview {
  market_summary: string
  index_performance: {
    indices: IndexData[]
    intraday_narrative: string
  }
  sector_performance: {
    sectors: SectorData[]
    fund_flow_summary: string
    intraday_narrative: string
  }
  policy_changes: PolicyChanges
  risk_signals: RiskSignals
  northbound_fund: NorthboundFund
  outlook: Outlook
}

interface AssetPerformance {
  symbol: string
  name: string
  asset_class: string
  weight: number
  price: number
  change_pct: number
  daily_return: number
  contribution: number
}

interface Page2PortfolioPerformance {
  portfolio_return: number
  portfolio_return_pct: string
  benchmark_return: number
  excess_return: number
  asset_performances: AssetPerformance[]
  best_contributor: AssetPerformance | null
  worst_contributor: AssetPerformance | null
  summary: string
}

interface Page3WeeklyMarket {
  week_start: string
  week_end: string
  market_summary: string
  index_performance: { indices: any[] }
  sector_performance: { sectors: any[] }
  policy_changes: PolicyChanges
  risk_signals: RiskSignals
  northbound_fund: any
  outlook: Outlook
}

interface MarketReport {
  report_type: ReportType
  report_date: string
  page1: Page1MarketOverview | null
  page2: Page2PortfolioPerformance | null
  page3: Page3WeeklyMarket | null
}

const userStore = useUserStore()
const report = ref<MarketReport | null>(null)
const loading = ref(false)
const generating = ref(false)
const activeTab = ref<ActiveTab>('market')
const reportType = ref<ReportType>('daily')

const userId = computed(() => userStore.currentUserId || 1)

const hasWeeklyPage = computed(() => reportType.value === 'weekly' || report.value?.report_type === 'weekly')

async function loadReport() {
  loading.value = true
  try {
    const res = await getLatestMarketReport(userId.value, reportType.value)
    if (res.data?.data) {
      report.value = res.data.data
    } else {
      report.value = null
    }
  } catch (e) {
    console.error('Failed to load report:', e)
    report.value = null
  } finally {
    loading.value = false
  }
}

async function generateReport() {
  generating.value = true
  try {
    await generateMarketReport({
      report_type: reportType.value,
    })
    await loadReport()
  } catch (e) {
    console.error('Failed to generate report:', e)
  } finally {
    generating.value = false
  }
}

function switchTab(tab: ActiveTab) {
  activeTab.value = tab
}

function switchReportType(type: ReportType) {
  reportType.value = type
  activeTab.value = 'market'
  loadReport()
}

function getReturnClass(val: number) {
  return val >= 0 ? 'positive' : 'negative'
}

function getReturnSign(val: number) {
  return val >= 0 ? '+' : ''
}

function formatAmount(val: number) {
  return `${val >= 0 ? '+' : ''}${(val / 100000000).toFixed(2)}亿`
}

function formatFundFlow(val: number) {
  return `${val >= 0 ? '+' : ''}${(val / 10000).toFixed(1)}亿`
}

onMounted(() => {
  loadReport()
})
</script>

<template>
  <div class="market-report-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <div class="header-title">
          <span class="header-label">MARKET</span>
          <span class="header-name">市场报告</span>
        </div>
        <div class="header-actions">
          <span class="report-date">{{ report?.report_date || '—' }}</span>
          <button
            class="generate-btn"
            :disabled="generating"
            @click="generateReport"
          >
            {{ generating ? '生成中...' : '生成报告' }}
          </button>
        </div>
      </div>
    </header>

    <!-- Report Type Toggle -->
    <div class="type-toggle">
      <button
        class="type-btn"
        :class="{ active: reportType === 'daily' }"
        @click="switchReportType('daily')"
      >
        每日报告
      </button>
      <button
        class="type-btn"
        :class="{ active: reportType === 'weekly' }"
        @click="switchReportType('weekly')"
      >
        每周报告
      </button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'market' }"
        @click="switchTab('market')"
      >
        今日市场
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'portfolio' }"
        @click="switchTab('portfolio')"
      >
        组合表现
      </button>
      <button
        v-if="hasWeeklyPage"
        class="tab"
        :class="{ active: activeTab === 'weekly' }"
        @click="switchTab('weekly')"
      >
        本周市场
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">加载报告中...</div>

    <!-- Empty -->
    <div v-else-if="!report" class="empty-state">
      <div class="empty-title">暂无{{ reportType === 'weekly' ? '每周' : '每日' }}报告</div>
      <div class="empty-desc">点击下方按钮生成最新市场报告</div>
      <button class="generate-btn large" :disabled="generating" @click="generateReport">
        {{ generating ? '生成中...' : '生成报告' }}
      </button>
    </div>

    <!-- Tab 1: 今日市场 -->
    <div v-else-if="activeTab === 'market' && report.page1" class="tab-content">
      <!-- 市场综述 -->
      <div class="summary-card">
        <div class="card-label">市场综述</div>
        <div class="summary-text">{{ report.page1.market_summary }}</div>
      </div>

      <!-- 指数表现 -->
      <div class="section">
        <div class="section-title">指数表现</div>
        <div class="index-grid">
          <div
            v-for="idx in report.page1.index_performance.indices"
            :key="idx.symbol"
            class="index-card"
          >
            <div class="index-name">{{ idx.name }}</div>
            <div class="index-value" :class="getReturnClass(idx.change_pct)">
              {{ getReturnSign(idx.change_pct) }}{{ idx.change_pct.toFixed(2) }}%
            </div>
            <div class="index-detail">
              <span>高 {{ idx.high.toFixed(2) }}</span>
              <span>低 {{ idx.low.toFixed(2) }}</span>
            </div>
          </div>
        </div>
        <div class="narrative-box">
          <span class="narrative-label">分时走势</span>
          <p class="narrative-text">{{ report.page1.index_performance.intraday_narrative }}</p>
        </div>
      </div>

      <!-- 板块表现 -->
      <div class="section">
        <div class="section-title">板块表现与资金流向</div>
        <div class="fund-flow-summary">{{ report.page1.sector_performance.fund_flow_summary }}</div>
        <div class="sector-list">
          <div
            v-for="s in report.page1.sector_performance.sectors"
            :key="s.name"
            class="sector-item"
          >
            <span class="sector-name">{{ s.name }}</span>
            <div class="sector-bar-wrap">
              <div
                class="sector-bar"
                :class="getReturnClass(s.change_pct)"
                :style="{ width: `${Math.min(Math.abs(s.change_pct) * 10, 100)}%` }"
              ></div>
            </div>
            <span class="sector-change" :class="getReturnClass(s.change_pct)">
              {{ getReturnSign(s.change_pct) }}{{ s.change_pct.toFixed(2) }}%
            </span>
            <span class="sector-flow" :class="s.fund_flow > 0 ? 'positive' : 'negative'">
              {{ formatFundFlow(s.fund_flow) }}
            </span>
          </div>
        </div>
        <div class="narrative-box">
          <span class="narrative-label">分时资金流向</span>
          <p class="narrative-text">{{ report.page1.sector_performance.intraday_narrative }}</p>
        </div>
      </div>

      <!-- 政策变动 -->
      <div class="section">
        <div class="section-title">政策变动</div>
        <div v-if="!report.page1.policy_changes.has_policy" class="policy-card policy-none">
          无
        </div>
        <div v-else class="policy-list">
          <div
            v-for="(policy, idx) in report.page1.policy_changes.policies"
            :key="idx"
            class="policy-card"
          >
            <div class="policy-title">{{ policy.title }}</div>
            <div class="policy-meta">
              <span v-if="policy.publish_time">发布时间：{{ policy.publish_time }}</span>
              <span v-if="policy.publisher">发布主体：{{ policy.publisher }}</span>
            </div>
            <div v-if="policy.core_items?.length" class="policy-items">
              <div class="policy-subtitle">核心条款</div>
              <ul>
                <li v-for="(item, iidx) in policy.core_items" :key="iidx">{{ item }}</li>
              </ul>
            </div>
            <div v-if="policy.market_reaction" class="policy-section">
              <div class="policy-subtitle">市场反应</div>
              <p>{{ policy.market_reaction }}</p>
            </div>
            <div v-if="policy.significance" class="policy-section">
              <div class="policy-subtitle">政策意义</div>
              <p>{{ policy.significance }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 风险信号 -->
      <div class="section">
        <div class="section-title">市场特征与风险信号</div>
        <div class="risk-grid">
          <div class="risk-item">
            <span class="risk-label">波动率环境</span>
            <span class="risk-val">{{ report.page1.risk_signals.volatility_regime }}</span>
          </div>
          <div class="risk-item">
            <span class="risk-label">市场情绪</span>
            <span class="risk-val">{{ report.page1.risk_signals.sentiment }}</span>
          </div>
        </div>
        <div v-if="report.page1.risk_signals.alerts.length" class="alert-list">
          <div
            v-for="alert in report.page1.risk_signals.alerts"
            :key="alert"
            class="alert-item"
          >
            {{ alert }}
          </div>
        </div>
      </div>

      <!-- 北向资金 -->
      <div class="section">
        <div class="section-title">北向资金与外部环境</div>
        <div class="northbound-card">
          <div class="nb-main">
            <div class="nb-item">
              <span class="nb-label">当日净流入</span>
              <span class="nb-value" :class="getReturnClass(report.page1.northbound_fund.net_inflow)">
                {{ getReturnSign(report.page1.northbound_fund.net_inflow) }}
                {{ report.page1.northbound_fund.net_inflow.toFixed(2) }}亿
              </span>
            </div>
            <div class="nb-item">
              <span class="nb-label">累计净流入</span>
              <span class="nb-value">{{ report.page1.northbound_fund.cumulative_inflow.toFixed(2) }}亿</span>
            </div>
          </div>
          <div v-if="report.page1.northbound_fund.leading_sectors.length" class="nb-sectors">
            <span class="nb-label">偏好板块</span>
            <div class="nb-tags">
              <span v-for="s in report.page1.northbound_fund.leading_sectors" :key="s" class="nb-tag">{{ s }}</span>
            </div>
          </div>
          <p class="nb-env">{{ report.page1.northbound_fund.external_env }}</p>
          <p class="nb-inference">{{ report.page1.northbound_fund.inference }}</p>
        </div>
      </div>

      <!-- 后市展望 -->
      <div class="section">
        <div class="section-title">后市展望</div>
        <div class="outlook-card">
          <div class="outlook-section">
            <div class="outlook-subtitle">短期（1-3个交易日）</div>
            <p>{{ report.page1.outlook.short_term }}</p>
          </div>
          <div class="outlook-section">
            <div class="outlook-subtitle">中期（1-2周）</div>
            <p>{{ report.page1.outlook.medium_term }}</p>
          </div>
          <div v-if="report.page1.outlook.risks.length" class="outlook-section">
            <div class="outlook-subtitle">风险提示</div>
            <ul>
              <li v-for="risk in report.page1.outlook.risks" :key="risk">{{ risk }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: 组合表现 -->
    <div v-else-if="activeTab === 'portfolio' && report.page2" class="tab-content">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-label">今日收益</div>
          <div class="card-value" :class="getReturnClass(report.page2.portfolio_return)">
            {{ report.page2.portfolio_return_pct }}
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">基准收益</div>
          <div class="card-value" :class="getReturnClass(report.page2.benchmark_return)">
            {{ getReturnSign(report.page2.benchmark_return) }}{{ (report.page2.benchmark_return * 100).toFixed(2) }}%
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">超额收益</div>
          <div class="card-value" :class="getReturnClass(report.page2.excess_return)">
            {{ getReturnSign(report.page2.excess_return) }}{{ (report.page2.excess_return * 100).toFixed(2) }}%
          </div>
        </div>
      </div>

      <!-- Best/Worst -->
      <div class="contributors">
        <div v-if="report.page2.best_contributor" class="contributor-card best">
          <div class="contributor-label">最佳贡献</div>
          <div class="contributor-name">{{ report.page2.best_contributor.name }}</div>
          <div class="contributor-return positive">
            {{ getReturnSign(report.page2.best_contributor.daily_return) }}{{ (report.page2.best_contributor.daily_return * 100).toFixed(2) }}%
          </div>
        </div>
        <div v-if="report.page2.worst_contributor" class="contributor-card worst">
          <div class="contributor-label">最差贡献</div>
          <div class="contributor-name">{{ report.page2.worst_contributor.name }}</div>
          <div class="contributor-return negative">
            {{ getReturnSign(report.page2.worst_contributor.daily_return) }}{{ (report.page2.worst_contributor.daily_return * 100).toFixed(2) }}%
          </div>
        </div>
      </div>

      <!-- Assets Table -->
      <div class="section">
        <div class="section-title">资产表现</div>
        <div class="assets-table">
          <div class="table-header">
            <span>标的</span>
            <span>类别</span>
            <span>权重</span>
            <span>涨跌</span>
            <span>贡献</span>
          </div>
          <div
            v-for="a in report.page2.asset_performances"
            :key="a.symbol"
            class="table-row"
          >
            <div class="col-symbol">
              <span class="symbol-code">{{ a.symbol }}</span>
              <span class="symbol-name">{{ a.name }}</span>
            </div>
            <span class="col-class">{{ a.asset_class }}</span>
            <span class="col-weight">{{ (a.weight * 100).toFixed(0) }}%</span>
            <span class="col-return" :class="getReturnClass(a.daily_return)">
              {{ getReturnSign(a.daily_return) }}{{ (a.daily_return * 100).toFixed(2) }}%
            </span>
            <span class="col-contribution" :class="getReturnClass(a.contribution)">
              {{ getReturnSign(a.contribution) }}{{ (a.contribution * 100).toFixed(2) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Summary -->
      <div class="summary-card">
        <div class="summary-text">{{ report.page2.summary }}</div>
      </div>
    </div>

    <!-- Tab 3: 本周市场 -->
    <div v-else-if="activeTab === 'weekly' && report.page3" class="tab-content">
      <!-- 周度市场综述 -->
      <div class="summary-card">
        <div class="card-label">本周市场综述</div>
        <div class="summary-text">{{ report.page3.market_summary }}</div>
      </div>

      <!-- 周度指数 -->
      <div class="section">
        <div class="section-title">周度指数表现</div>
        <div class="index-grid">
          <div
            v-for="idx in report.page3.index_performance.indices"
            :key="idx.symbol"
            class="index-card"
          >
            <div class="index-name">{{ idx.name }}</div>
            <div class="index-value" :class="getReturnClass(idx.week_change_pct)">
              {{ getReturnSign(idx.week_change_pct) }}{{ (idx.week_change_pct * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </div>

      <!-- 周度板块 -->
      <div class="section">
        <div class="section-title">周度板块表现</div>
        <div class="sector-list">
          <div
            v-for="s in report.page3.sector_performance.sectors"
            :key="s.name"
            class="sector-item"
          >
            <span class="sector-name">{{ s.name }}</span>
            <span class="sector-change" :class="getReturnClass(s.week_change_pct)">
              {{ getReturnSign(s.week_change_pct) }}{{ (s.week_change_pct * 100).toFixed(2) }}%
            </span>
            <span class="sector-flow" :class="s.week_fund_flow > 0 ? 'positive' : 'negative'">
              {{ getReturnSign(s.week_fund_flow) }}{{ s.week_fund_flow.toFixed(1) }}亿
            </span>
          </div>
        </div>
      </div>

      <!-- 周度展望 -->
      <div class="section">
        <div class="section-title">下周展望</div>
        <div class="outlook-card">
          <div class="outlook-section">
            <div class="outlook-subtitle">短期</div>
            <p>{{ report.page3.outlook.short_term }}</p>
          </div>
          <div class="outlook-section">
            <div class="outlook-subtitle">中期</div>
            <p>{{ report.page3.outlook.medium_term }}</p>
          </div>
          <div v-if="report.page3.outlook.risks.length" class="outlook-section">
            <div class="outlook-subtitle">风险提示</div>
            <ul>
              <li v-for="risk in report.page3.outlook.risks" :key="risk">{{ risk }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.market-report-page {
  min-height: 100vh;
  background: #fafafa;
  position: relative;
  padding-bottom: 32px;
}

.texture-noise {
  position: fixed; inset: 0; z-index: 0;
  opacity: 0.035; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat; background-size: 128px 128px;
}
.texture-grid {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: linear-gradient(rgba(0,0,0,0.028) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.028) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
}

/* Header */
.page-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.85);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  padding: 16px 0;
}
.page-header-inner {
  max-width: 720px; margin: 0 auto; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.header-title { display: flex; flex-direction: column; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 1.1rem; font-weight: 700; color: #171717; letter-spacing: -0.02em; }
.header-actions {
  display: flex; align-items: center; gap: 12px;
}
.report-date { font-size: 0.8rem; color: #a3a3a3; font-weight: 500; }
.generate-btn {
  padding: 8px 14px;
  border: none; border-radius: 10px;
  background: #171717; color: #fff;
  font-size: 0.78rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.generate-btn:hover:not(:disabled) { background: #333; }
.generate-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.generate-btn.large { padding: 12px 24px; font-size: 0.9rem; margin-top: 16px; }

/* Type Toggle */
.type-toggle {
  max-width: 720px; margin: 16px auto 0; padding: 0 24px;
  display: flex; gap: 8px;
  position: relative; z-index: 1;
}
.type-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px;
  background: #fff;
  font-family: inherit; font-size: 0.8rem; font-weight: 600; color: #a3a3a3;
  cursor: pointer; transition: all 0.2s;
}
.type-btn.active {
  background: #171717; color: #fff;
  border-color: #171717;
}

/* Tabs */
.tabs {
  max-width: 720px; margin: 12px auto 0; padding: 0 24px;
  display: flex; gap: 8px;
  position: relative; z-index: 1;
}
.tab {
  flex: 1;
  padding: 12px;
  border: none; border-radius: 12px;
  background: transparent;
  font-family: inherit; font-size: 0.85rem; font-weight: 600; color: #a3a3a3;
  cursor: pointer; transition: all 0.2s ease;
}
.tab.active {
  background: #171717; color: #fff;
}

/* Tab Content */
.tab-content {
  max-width: 720px; margin: 16px auto; padding: 0 24px;
  position: relative; z-index: 1;
}

/* Loading / Empty */
.loading-state, .empty-state {
  max-width: 720px; margin: 48px auto; padding: 0 24px;
  text-align: center; color: #737373;
  position: relative; z-index: 1;
}
.empty-title { font-size: 1rem; font-weight: 700; color: #171717; margin-bottom: 8px; }
.empty-desc { font-size: 0.85rem; color: #a3a3a3; }

/* Summary Card */
.summary-card {
  background: #fff; border-radius: 16px;
  padding: 18px;
  border: 1px solid rgba(0,0,0,0.05);
}
.card-label { font-size: 0.72rem; font-weight: 700; color: #a3a3a3; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; }
.summary-text { font-size: 0.9rem; color: #525252; line-height: 1.7; }

/* Section */
.section { margin-top: 24px; }
.section-title { font-size: 0.9rem; font-weight: 700; color: #171717; margin-bottom: 12px; }

/* Index Grid */
.index-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.index-card {
  background: #fff; border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(0,0,0,0.05);
}
.index-name { font-size: 0.75rem; color: #a3a3a3; margin-bottom: 6px; }
.index-value { font-size: 1.3rem; font-weight: 700; }
.index-detail {
  display: flex; gap: 10px; margin-top: 8px;
  font-size: 0.72rem; color: #737373;
}

/* Narrative Box */
.narrative-box {
  background: #f0f9ff; border-radius: 12px;
  padding: 14px 16px; margin-top: 12px;
  border: 1px solid rgba(59, 130, 246, 0.1);
}
.narrative-label {
  font-size: 0.7rem; font-weight: 700; color: #3b82f6;
  display: block; margin-bottom: 6px;
}
.narrative-text { font-size: 0.85rem; color: #525252; line-height: 1.6; margin: 0; }

/* Fund Flow Summary */
.fund-flow-summary {
  background: #fff; border-radius: 12px;
  padding: 14px 16px; margin-bottom: 12px;
  border: 1px solid rgba(0,0,0,0.05);
  font-size: 0.85rem; color: #525252; line-height: 1.6;
}

/* Sector List */
.sector-list {
  display: flex; flex-direction: column; gap: 8px;
}
.sector-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px;
  background: #fff; border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.05);
}
.sector-name { font-size: 0.85rem; font-weight: 600; width: 80px; flex-shrink: 0; }
.sector-bar-wrap {
  flex: 1; height: 6px;
  background: #f0f0f0; border-radius: 999px;
  overflow: hidden;
}
.sector-bar { height: 100%; border-radius: 999px; background: #171717; }
.sector-bar.negative { background: #dc2626; }
.sector-change { font-size: 0.85rem; font-weight: 600; min-width: 60px; text-align: right; }
.sector-flow { font-size: 0.75rem; min-width: 70px; text-align: right; }

/* Policy */
.policy-list { display: flex; flex-direction: column; gap: 10px; }
.policy-card {
  background: #fff; border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  font-size: 0.85rem; color: #525252; line-height: 1.6;
}
.policy-card.policy-none {
  background: #fafafa; color: #a3a3a3; text-align: center;
}
.policy-title { font-size: 0.95rem; font-weight: 700; color: #171717; margin-bottom: 8px; }
.policy-meta { display: flex; gap: 12px; font-size: 0.75rem; color: #a3a3a3; margin-bottom: 12px; }
.policy-subtitle { font-size: 0.75rem; font-weight: 700; color: #171717; margin-bottom: 6px; }
.policy-items ul { margin: 0; padding-left: 18px; }
.policy-items li { margin-bottom: 4px; }
.policy-section { margin-top: 12px; }
.policy-section p { margin: 0; }

/* Risk */
.risk-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.risk-item {
  background: #fff; border-radius: 12px;
  padding: 14px;
  border: 1px solid rgba(0,0,0,0.05);
  display: flex; flex-direction: column; gap: 4px;
}
.risk-label { font-size: 0.72rem; color: #a3a3a3; }
.risk-val { font-size: 1rem; font-weight: 700; color: #171717; }
.alert-list { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.alert-item {
  background: #fff; border-radius: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(0,0,0,0.05);
  border-left: 3px solid #f59e0b;
  font-size: 0.85rem; color: #525252;
}

/* Northbound */
.northbound-card {
  background: #fff; border-radius: 16px;
  padding: 18px;
  border: 1px solid rgba(0,0,0,0.05);
}
.nb-main {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
  margin-bottom: 14px;
}
.nb-item { display: flex; flex-direction: column; gap: 4px; }
.nb-label { font-size: 0.72rem; color: #a3a3a3; }
.nb-value { font-size: 1.2rem; font-weight: 700; }
.nb-sectors {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px; flex-wrap: wrap;
}
.nb-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.nb-tag {
  font-size: 0.75rem; padding: 4px 10px;
  background: #f0fdf4; color: #166534;
  border-radius: 6px;
}
.nb-env, .nb-inference {
  font-size: 0.82rem; color: #525252;
  line-height: 1.5; margin: 0;
}
.nb-inference { margin-top: 8px; font-weight: 600; }

/* Outlook */
.outlook-card {
  background: #fff; border-radius: 16px;
  padding: 18px;
  border: 1px solid rgba(0,0,0,0.05);
  font-size: 0.85rem; color: #525252; line-height: 1.7;
}
.outlook-section { margin-bottom: 14px; }
.outlook-section:last-child { margin-bottom: 0; }
.outlook-subtitle { font-size: 0.8rem; font-weight: 700; color: #171717; margin-bottom: 6px; }
.outlook-section p { margin: 0; }
.outlook-section ul { margin: 0; padding-left: 18px; }
.outlook-section li { margin-bottom: 4px; }

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.summary-cards .summary-card {
  padding: 16px;
}
.summary-cards .summary-card .card-value {
  font-size: 1.3rem; font-weight: 700;
}

/* Contributors */
.contributors {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 10px;
}
.contributor-card {
  background: #fff; border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(0,0,0,0.05);
}
.contributor-card.best { border-left: 3px solid #16a34a; }
.contributor-card.worst { border-left: 3px solid #dc2626; }
.contributor-label { font-size: 0.7rem; color: #a3a3a3; margin-bottom: 4px; }
.contributor-name { font-size: 0.9rem; font-weight: 600; color: #171717; }
.contributor-return { font-size: 1rem; font-weight: 700; margin-top: 4px; }
.contributor-return.positive { color: #16a34a; }
.contributor-return.negative { color: #dc2626; }

/* Assets Table */
.assets-table {
  background: #fff; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  overflow: hidden;
}
.assets-table .table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 12px 16px;
  background: #fafafa;
  font-size: 0.7rem; font-weight: 700; color: #a3a3a3;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.assets-table .table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(0,0,0,0.04);
  font-size: 0.85rem;
}
.col-symbol { display: flex; flex-direction: column; gap: 2px; }
.symbol-code { font-weight: 700; color: #171717; }
.symbol-name { font-size: 0.75rem; color: #a3a3a3; }
.col-class { font-size: 0.75rem; color: #737373; }
.col-weight, .col-return, .col-contribution { font-weight: 600; }
.positive { color: #16a34a; }
.negative { color: #dc2626; }

@media (min-width: 768px) {
  .page-header-inner,
  .type-toggle,
  .tabs,
  .tab-content {
    padding-left: 32px;
    padding-right: 32px;
  }
}
</style>

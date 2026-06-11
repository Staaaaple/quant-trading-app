<script setup lang="ts">
import { ref } from 'vue'

interface HoldingPerf {
  symbol: string
  name: string
  weekly_return: number
  weight: number
  contribution: number
}

interface WeeklyReport {
  week_start: string
  week_end: string
  performance: {
    weekly_return: number
    weekly_return_pct: string
    cum_return: number
    cum_return_pct: string
    benchmark_return: number
    benchmark_return_pct: string
    excess_return: number
    excess_return_pct: string
    max_drawdown: number
    max_drawdown_pct: string
    holding_performances: HoldingPerf[]
    best_contributor: HoldingPerf | null
    worst_contributor: HoldingPerf | null
    summary: string
  }
  market_review: {
    market_cycle: string
    market_cycle_cn: string
    composite_score: number
    composite_score_pct: string
    mood: string
    summary: string
    layers: {
      name: string
      score: number
      score_pct: string
      trend: string
      trend_icon: string
    }[]
  }
  outlook: {
    predicted_cycle: string
    predicted_cycle_cn: string
    prediction_confidence: number
    title: string
    content: string
    opportunities: string[]
    risks: string[]
    personalized_advice: string
  }
  lifespan_alerts: {
    portfolio_lifespan: number
    portfolio_health: number
    alerts: any[]
    alert_count: number
    has_alert: boolean
  }
  recommended_actions: {
    priority: string
    action: string
    reason: string
  }[]
}

// 从 sessionStorage 获取组合和市场数据生成周报
function generateReport(): WeeklyReport {
  const portfolioStored = sessionStorage.getItem('latest_portfolio')
  const signalStored = sessionStorage.getItem('latest_market_signal')

  let portfolio: any = null
  let signal: any = null

  if (portfolioStored) {
    try { portfolio = JSON.parse(portfolioStored) } catch (e) {}
  }
  if (signalStored) {
    try { signal = JSON.parse(signalStored) } catch (e) {}
  }

  const bindings = portfolio?.portfolio?.bindings || []
  const saa = portfolio?.portfolio?.saa?.weights || {}

  // 生成持仓表现（基于回测结果，若无回测则显示0）
  const holdingPerformances: HoldingPerf[] = bindings.map((b: any) => {
    const bt = b.backtest_result
    // 使用回测数据计算周收益，若无回测数据则显示为0
    const weeklyReturn = bt?.return ? bt.return / 52 : 0 // 年化收益转周收益
    return {
      symbol: b.symbol,
      name: b.name || b.symbol,
      weekly_return: weeklyReturn,
      weight: b.weight || 0.1,
      contribution: weeklyReturn * (b.weight || 0.1),
    }
  })

  // 计算汇总
  const weeklyReturn = holdingPerformances.reduce((sum, h) => sum + h.contribution, 0)
  const bestContributor = holdingPerformances.length > 0
    ? holdingPerformances.reduce((best, h) => h.contribution > best.contribution ? h : best, holdingPerformances[0])
    : null
  const worstContributor = holdingPerformances.length > 0
    ? holdingPerformances.reduce((worst, h) => h.contribution < worst.contribution ? h : worst, holdingPerformances[0])
    : null

  // 市场回顾
  const marketCycle = signal?.market_cycle || 'recovery'
  const cycleMap: Record<string, string> = {
    expansion: '扩张期', peak: '过热期', contraction: '衰退期', trough: '萧条期', recovery: '复苏期',
  }
  const compositeScore = signal?.composite_score || 50

  // 五层信号
  const layers = [
    { name: '宏观层', score: signal?.macro?.score ?? 0.5, trend: 'stable', trend_icon: '→' },
    { name: '地缘政治', score: (signal?.geo?.overall_risk ? 1 - signal.geo.overall_risk : 0.5), trend: 'stable', trend_icon: '→' },
    { name: '行业景气', score: signal?.industry?.score ?? 0.5, trend: 'up', trend_icon: '↑' },
    { name: '社会实事', score: signal?.social?.score ?? 0.5, trend: 'stable', trend_icon: '→' },
    { name: '资产内部', score: signal?.internal?.score ?? 0.5, trend: 'down', trend_icon: '↓' },
  ]

  const now = new Date()
  const weekEnd = new Date(now)
  const weekStart = new Date(now)
  weekStart.setDate(weekStart.getDate() - 7)

  return {
    week_start: weekStart.toISOString().split('T')[0],
    week_end: weekEnd.toISOString().split('T')[0],
    performance: {
      weekly_return: weeklyReturn,
      weekly_return_pct: `${weeklyReturn >= 0 ? '+' : ''}${(weeklyReturn * 100).toFixed(2)}%`,
      cum_return: 0,
      cum_return_pct: '0.00%',
      benchmark_return: weeklyReturn * 0.7,
      benchmark_return_pct: `${weeklyReturn >= 0 ? '+' : ''}${(weeklyReturn * 70).toFixed(2)}%`,
      excess_return: weeklyReturn * 0.3,
      excess_return_pct: `${weeklyReturn >= 0 ? '+' : ''}${(weeklyReturn * 30).toFixed(2)}%`,
      max_drawdown: 0.03,
      max_drawdown_pct: '3.0%',
      holding_performances: holdingPerformances,
      best_contributor: bestContributor,
      worst_contributor: worstContributor,
      summary: weeklyReturn >= 0 ? '本周表现良好，实现正收益' : '本周市场调整，组合小幅回撤',
    },
    market_review: {
      market_cycle: marketCycle,
      market_cycle_cn: cycleMap[marketCycle] || '复苏期',
      composite_score: compositeScore / 100,
      composite_score_pct: `${compositeScore}%`,
      mood: signal?.market_mood || '中性偏乐观',
      summary: `本周市场处于${cycleMap[marketCycle] || '复苏期'}，综合评分${compositeScore}%。`,
      layers: layers.map(l => ({
        ...l,
        score_pct: `${Math.round(l.score * 100)}%`,
      })),
    },
    outlook: {
      predicted_cycle: 'expansion',
      predicted_cycle_cn: '扩张期',
      prediction_confidence: 0.65,
      title: '扩张期延续',
      content: '经济扩张趋势有望延续，关注企业盈利数据和政策动向。',
      opportunities: ['周期性行业', '成长股', '科技板块'],
      risks: ['通胀压力', '政策收紧预期'],
      personalized_advice: saa.stock > 0.5
        ? '当前股票仓位较高，扩张期适合继续持有，关注止盈机会。'
        : '扩张期适合适度增配股票，把握上涨机会。',
    },
    lifespan_alerts: {
      portfolio_lifespan: portfolio?.portfolio?.portfolio_lifespan || 12,
      portfolio_health: portfolio?.portfolio?.portfolio_health || 75,
      alerts: [],
      alert_count: 0,
      has_alert: false,
    },
    recommended_actions: [
      { priority: 'low', action: '持有观望', reason: '当前无明确操作信号，继续持有' },
    ],
  }
}

const report = ref<WeeklyReport>(generateReport())

const activeTab = ref<'performance' | 'market' | 'outlook'>('performance')

function getReturnClass(val: number) {
  return val >= 0 ? 'positive' : 'negative'
}

function getReturnSign(val: number) {
  return val >= 0 ? '+' : ''
}
</script>

<template>
  <div class="weekly-report-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <div class="header-title">
          <span class="header-label">WEEKLY</span>
          <span class="header-name">周报</span>
        </div>
        <div class="header-date">
          {{ report.week_start }} ~ {{ report.week_end }}
        </div>
      </div>
    </header>

    <!-- Tabs -->
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'performance' }"
        @click="activeTab = 'performance'"
      >
        组合表现
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'market' }"
        @click="activeTab = 'market'"
      >
        市场回顾
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'outlook' }"
        @click="activeTab = 'outlook'"
      >
        下周展望
      </button>
    </div>

    <!-- Performance Tab -->
    <div v-if="activeTab === 'performance'" class="tab-content">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-label">本周收益</div>
          <div class="card-value" :class="getReturnClass(report.performance.weekly_return)">
            {{ report.performance.weekly_return_pct }}
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">累计收益</div>
          <div class="card-value" :class="getReturnClass(report.performance.cum_return)">
            {{ report.performance.cum_return_pct }}
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">相对基准</div>
          <div class="card-value" :class="getReturnClass(report.performance.excess_return)">
            {{ report.performance.excess_return_pct }}
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">最大回撤</div>
          <div class="card-value negative">
            {{ report.performance.max_drawdown_pct }}
          </div>
        </div>
      </div>

      <!-- Best/Worst -->
      <div class="contributors">
        <div v-if="report.performance.best_contributor" class="contributor-card best">
          <div class="contributor-label">最佳贡献</div>
          <div class="contributor-name">{{ report.performance.best_contributor.name }}</div>
          <div class="contributor-return positive">
            {{ getReturnSign(report.performance.best_contributor.weekly_return) }}
            {{ (report.performance.best_contributor.weekly_return * 100).toFixed(2) }}%
          </div>
        </div>
        <div v-if="report.performance.worst_contributor" class="contributor-card worst">
          <div class="contributor-label">最差贡献</div>
          <div class="contributor-name">{{ report.performance.worst_contributor.name }}</div>
          <div class="contributor-return negative">
            {{ getReturnSign(report.performance.worst_contributor.weekly_return) }}
            {{ (report.performance.worst_contributor.weekly_return * 100).toFixed(2) }}%
          </div>
        </div>
      </div>

      <!-- Holdings Table -->
      <div class="section">
        <div class="section-title">持仓表现</div>
        <div class="holdings-table">
          <div class="table-header">
            <span>标的</span>
            <span>权重</span>
            <span>本周收益</span>
            <span>贡献</span>
          </div>
          <div
            v-for="h in report.performance.holding_performances"
            :key="h.symbol"
            class="table-row"
          >
            <div class="col-symbol">
              <span class="symbol-code">{{ h.symbol }}</span>
              <span class="symbol-name">{{ h.name }}</span>
            </div>
            <span class="col-weight">{{ (h.weight * 100).toFixed(0) }}%</span>
            <span class="col-return" :class="getReturnClass(h.weekly_return)">
              {{ getReturnSign(h.weekly_return) }}{{ (h.weekly_return * 100).toFixed(2) }}%
            </span>
            <span class="col-contribution" :class="getReturnClass(h.contribution)">
              {{ getReturnSign(h.contribution) }}{{ (h.contribution * 100).toFixed(2) }}%
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Market Review Tab -->
    <div v-if="activeTab === 'market'" class="tab-content">
      <!-- Market Cycle -->
      <div class="cycle-card">
        <div class="cycle-label">当前周期</div>
        <div class="cycle-value">{{ report.market_review.market_cycle_cn }}</div>
        <div class="cycle-score">
          综合评分 {{ report.market_review.composite_score_pct }}
          <span class="cycle-mood">({{ report.market_review.mood }})</span>
        </div>
        <div class="cycle-summary">{{ report.market_review.summary }}</div>
      </div>

      <!-- Five Layers -->
      <div class="section">
        <div class="section-title">五层信号</div>
        <div class="layers-list">
          <div
            v-for="layer in report.market_review.layers"
            :key="layer.name"
            class="layer-item"
          >
            <div class="layer-info">
              <span class="layer-name">{{ layer.name }}</span>
              <span class="layer-trend">{{ layer.trend_icon }}</span>
            </div>
            <div class="layer-bar-wrap">
              <div class="layer-bar-bg">
                <div
                  class="layer-bar-fill"
                  :style="{ width: layer.score_pct }"
                ></div>
              </div>
              <span class="layer-score">{{ layer.score_pct }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Outlook Tab -->
    <div v-if="activeTab === 'outlook'" class="tab-content">
      <!-- Prediction -->
      <div class="outlook-card">
        <div class="outlook-header">
          <div class="outlook-cycle">
            预测周期: {{ report.outlook.predicted_cycle_cn }}
          </div>
          <div class="outlook-confidence">
            置信度 {{ (report.outlook.prediction_confidence * 100).toFixed(0) }}%
          </div>
        </div>
        <div class="outlook-title">{{ report.outlook.title }}</div>
        <div class="outlook-content">{{ report.outlook.content }}</div>
      </div>

      <!-- Personalized Advice -->
      <div class="advice-card">
        <div class="advice-label">💡 个性化建议</div>
        <div class="advice-text">{{ report.outlook.personalized_advice }}</div>
      </div>

      <!-- Opportunities -->
      <div class="section">
        <div class="section-title">关注机会</div>
        <div class="tags-list">
          <span
            v-for="opp in report.outlook.opportunities"
            :key="opp"
            class="tag tag-opportunity"
          >
            {{ opp }}
          </span>
        </div>
      </div>

      <!-- Risks -->
      <div class="section">
        <div class="section-title">风险提示</div>
        <div class="tags-list">
          <span
            v-for="risk in report.outlook.risks"
            :key="risk"
            class="tag tag-risk"
          >
            {{ risk }}
          </span>
        </div>
      </div>

      <!-- Recommended Actions -->
      <div class="section">
        <div class="section-title">操作建议</div>
        <div class="actions-list">
          <div
            v-for="(action, idx) in report.recommended_actions"
            :key="idx"
            class="action-item"
            :class="action.priority"
          >
            <div class="action-priority">{{ action.priority === 'high' ? '高' : action.priority === 'normal' ? '中' : '低' }}</div>
            <div class="action-body">
              <div class="action-name">{{ action.action }}</div>
              <div class="action-reason">{{ action.reason }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.weekly-report-page {
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
.header-date { font-size: 0.8rem; color: #a3a3a3; font-weight: 500; }

/* Tabs */
.tabs {
  max-width: 720px; margin: 16px auto 0; padding: 0 24px;
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

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.summary-card {
  background: #fff; border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(0,0,0,0.05);
}
.card-label { font-size: 0.75rem; color: #a3a3a3; margin-bottom: 8px; }
.card-value { font-size: 1.3rem; font-weight: 700; }
.card-value.positive { color: #16a34a; }
.card-value.negative { color: #dc2626; }

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

/* Section */
.section { margin-top: 24px; }
.section-title { font-size: 0.9rem; font-weight: 700; color: #171717; margin-bottom: 12px; }

/* Holdings Table */
.holdings-table {
  background: #fff; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  overflow: hidden;
}
.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 12px 16px;
  background: #fafafa;
  font-size: 0.7rem; font-weight: 700; color: #a3a3a3;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(0,0,0,0.04);
  font-size: 0.85rem;
}
.col-symbol { display: flex; flex-direction: column; gap: 2px; }
.symbol-code { font-weight: 700; color: #171717; }
.symbol-name { font-size: 0.75rem; color: #a3a3a3; }
.col-weight, .col-return, .col-contribution { font-weight: 600; }
.positive { color: #16a34a; }
.negative { color: #dc2626; }

/* Cycle Card */
.cycle-card {
  background: #fff; border-radius: 20px;
  padding: 20px;
  border: 1px solid rgba(0,0,0,0.05);
}
.cycle-label { font-size: 0.7rem; font-weight: 700; color: #a3a3a3; text-transform: uppercase; letter-spacing: 0.05em; }
.cycle-value { font-size: 1.5rem; font-weight: 700; color: #171717; margin-top: 4px; }
.cycle-score { font-size: 0.85rem; color: #525252; margin-top: 4px; }
.cycle-mood { color: #a3a3a3; }
.cycle-summary { font-size: 0.85rem; color: #737373; margin-top: 12px; line-height: 1.5; }

/* Layers */
.layers-list {
  display: flex; flex-direction: column; gap: 12px;
}
.layer-item {
  background: #fff; border-radius: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(0,0,0,0.05);
}
.layer-info {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.layer-name { font-size: 0.85rem; font-weight: 600; color: #171717; }
.layer-trend { font-size: 1rem; }
.layer-bar-wrap {
  display: flex; align-items: center; gap: 10px;
}
.layer-bar-bg {
  flex: 1; height: 6px; background: #f0f0f0; border-radius: 999px; overflow: hidden;
}
.layer-bar-fill {
  height: 100%; background: #171717; border-radius: 999px;
  transition: width 0.5s ease;
}
.layer-score { font-size: 0.78rem; font-weight: 600; color: #525252; min-width: 40px; text-align: right; }

/* Outlook */
.outlook-card {
  background: #fff; border-radius: 20px;
  padding: 20px;
  border: 1px solid rgba(0,0,0,0.05);
}
.outlook-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.outlook-cycle { font-size: 0.85rem; font-weight: 600; color: #171717; }
.outlook-confidence { font-size: 0.78rem; color: #a3a3a3; }
.outlook-title { font-size: 1.1rem; font-weight: 700; color: #171717; }
.outlook-content { font-size: 0.85rem; color: #525252; margin-top: 8px; line-height: 1.6; }

/* Advice */
.advice-card {
  background: #f0f9ff; border-radius: 16px;
  padding: 16px;
  margin-top: 12px;
  border: 1px solid rgba(59, 130, 246, 0.1);
}
.advice-label { font-size: 0.8rem; font-weight: 700; color: #3b82f6; margin-bottom: 4px; }
.advice-text { font-size: 0.85rem; color: #525252; line-height: 1.5; }

/* Tags */
.tags-list { display: flex; flex-wrap: wrap; gap: 8px; }
.tag {
  padding: 8px 14px; border-radius: 10px;
  font-size: 0.8rem; font-weight: 600;
}
.tag-opportunity { background: #dcfce7; color: #16a34a; }
.tag-risk { background: #fee2e2; color: #dc2626; }

/* Actions */
.actions-list { display: flex; flex-direction: column; gap: 10px; }
.action-item {
  display: flex; align-items: flex-start; gap: 12px;
  background: #fff; border-radius: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(0,0,0,0.05);
}
.action-item.high { border-left: 3px solid #dc2626; }
.action-item.normal { border-left: 3px solid #f59e0b; }
.action-item.low { border-left: 3px solid #16a34a; }
.action-priority {
  width: 24px; height: 24px; border-radius: 50%;
  background: #f5f5f5; color: #737373;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; flex-shrink: 0;
}
.action-name { font-size: 0.9rem; font-weight: 600; color: #171717; }
.action-reason { font-size: 0.8rem; color: #737373; margin-top: 2px; }

@media (min-width: 768px) {
  .page-header-inner,
  .tabs,
  .tab-content {
    padding-left: 32px;
    padding-right: 32px;
  }
}
</style>

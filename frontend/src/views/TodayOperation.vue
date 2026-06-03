<script setup lang="ts">
import { ref, computed } from 'vue'

interface Operation {
  symbol: string
  name: string
  action: string
  action_cn: string
  reason: string
  strategy_name: string
  confidence: number
  suggested_amount: number
  teaching_card?: {
    title: string
    content: string
  }
}

interface Holding {
  symbol: string
  name: string
  reason: string
}

interface DailyPush {
  has_operation: boolean
  title: string
  date: string
  summary?: string
  operations?: Operation[]
  holdings?: Holding[]
  market_brief: string
  priority?: string
}

// Mock data for demonstration
const pushData = ref<DailyPush>({
  has_operation: true,
  title: '今日操作提示 (2个信号)',
  date: new Date().toISOString().split('T')[0],
  operations: [
    {
      symbol: '510300',
      name: '沪深300ETF',
      action: 'buy',
      action_cn: '买入',
      reason: '双均线策略触发金叉信号，且组合股票仓位偏离目标',
      strategy_name: '双均线趋势',
      confidence: 0.82,
      suggested_amount: 5000,
      teaching_card: {
        title: '什么是金叉？',
        content: '短期均线上穿长期均线，通常被视为买入信号。表明短期趋势转强。',
      },
    },
    {
      symbol: '518880',
      name: '黄金ETF',
      action: 'sell',
      action_cn: '卖出',
      reason: '趋势跟踪策略触发死叉信号，黄金短期承压',
      strategy_name: '趋势跟踪',
      confidence: 0.75,
      suggested_amount: 3000,
      teaching_card: {
        title: '什么是死叉？',
        content: '短期均线下穿长期均线，通常被视为卖出信号。表明短期趋势转弱。',
      },
    },
  ],
  holdings: [
    { symbol: '510500', name: '中证500ETF', reason: '策略未触发信号，继续持有' },
    { symbol: '511010', name: '国债ETF', reason: '无明确信号，继续持有' },
  ],
  market_brief: '当前市场处于复苏期，综合评分58%，整体中性偏乐观',
  priority: 'normal',
})

const confirmedOps = ref<Set<string>>(new Set())
const ignoredOps = ref<Set<string>>(new Set())
const showTeaching = ref<string | null>(null)

function confirmOperation(symbol: string) {
  confirmedOps.value.add(symbol)
}

function ignoreOperation(symbol: string) {
  ignoredOps.value.add(symbol)
}

function toggleTeaching(symbol: string) {
  showTeaching.value = showTeaching.value === symbol ? null : symbol
}

const pendingOps = computed(() => {
  return pushData.value.operations?.filter(
    op => !confirmedOps.value.has(op.symbol) && !ignoredOps.value.has(op.symbol)
  ) || []
})

const isAllHandled = computed(() => {
  return pendingOps.value.length === 0
})

function getActionClass(action: string) {
  return action === 'buy' ? 'action-buy' : action === 'sell' ? 'action-sell' : 'action-hold'
}

function getActionIcon(action: string) {
  return action === 'buy' ? '↑' : action === 'sell' ? '↓' : '—'
}
</script>

<template>
  <div class="today-op-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <div class="header-title">
          <span class="header-label">TODAY</span>
          <span class="header-name">今日操作</span>
        </div>
        <div class="header-date">{{ pushData.date }}</div>
      </div>
    </header>

    <!-- Market Brief -->
    <div class="market-brief">
      <div class="brief-icon">📊</div>
      <div class="brief-text">{{ pushData.market_brief }}</div>
    </div>

    <!-- No Operation State -->
    <div v-if="!pushData.has_operation || isAllHandled" class="no-operation">
      <div class="no-op-icon">✓</div>
      <h3>今日持有</h3>
      <p>所有标的均无操作信号，继续持有</p>
      <div class="holdings-list">
        <div v-for="h in pushData.holdings" :key="h.symbol" class="holding-item">
          <span class="holding-name">{{ h.name }}</span>
          <span class="holding-reason">{{ h.reason }}</span>
        </div>
      </div>
    </div>

    <!-- Operations List -->
    <div v-else class="operations-list">
      <div class="section-title">
        <span class="section-badge">{{ pendingOps.length }}</span>
        <span>待处理信号</span>
      </div>

      <div
        v-for="op in pendingOps"
        :key="op.symbol"
        class="operation-card"
        :class="getActionClass(op.action)"
      >
        <div class="op-header">
          <div class="op-action-badge" :class="getActionClass(op.action)">
            <span class="op-icon">{{ getActionIcon(op.action) }}</span>
            <span>{{ op.action_cn }}</span>
          </div>
          <div class="op-confidence">
            置信度 {{ (op.confidence * 100).toFixed(0) }}%
          </div>
        </div>

        <div class="op-body">
          <div class="op-symbol">
            <span class="symbol-code">{{ op.symbol }}</span>
            <span class="symbol-name">{{ op.name }}</span>
          </div>

          <div class="op-reason">
            <div class="reason-label">信号原因</div>
            <div class="reason-text">{{ op.reason }}</div>
          </div>

          <div class="op-strategy">
            <span class="strategy-label">触发策略</span>
            <span class="strategy-name">{{ op.strategy_name }}</span>
          </div>

          <div class="op-amount">
            <span class="amount-label">建议金额</span>
            <span class="amount-value">¥{{ op.suggested_amount.toLocaleString() }}</span>
          </div>
        </div>

        <!-- Teaching Card -->
        <div v-if="op.teaching_card" class="teaching-section">
          <button
            class="teaching-toggle"
            @click="toggleTeaching(op.symbol)"
          >
            <span>📖 {{ op.teaching_card.title }}</span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              :style="{ transform: showTeaching === op.symbol ? 'rotate(180deg)' : '' }"
            >
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          <div
            v-if="showTeaching === op.symbol"
            class="teaching-content"
          >
            {{ op.teaching_card.content }}
          </div>
        </div>

        <!-- Actions -->
        <div class="op-actions">
          <button
            class="btn-ignore"
            @click="ignoreOperation(op.symbol)"
          >
            忽略
          </button>
          <button
            class="btn-confirm"
            :class="op.action"
            @click="confirmOperation(op.symbol)"
          >
            <span v-if="op.action === 'buy'">确认买入</span>
            <span v-else>确认卖出</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Holdings -->
    <div v-if="pushData.holdings && pushData.holdings.length > 0" class="holdings-section">
      <div class="section-title">
        <span class="section-badge hold">{{ pushData.holdings.length }}</span>
        <span>继续持有</span>
      </div>
      <div class="holdings-grid">
        <div
          v-for="h in pushData.holdings"
          :key="h.symbol"
          class="holding-card"
        >
          <div class="holding-symbol">{{ h.symbol }}</div>
          <div class="holding-name">{{ h.name }}</div>
          <div class="holding-status">持有</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.today-op-page {
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

/* Market Brief */
.market-brief {
  max-width: 720px; margin: 16px auto; padding: 0 24px;
  display: flex; align-items: center; gap: 12px;
  background: #fff; border-radius: 16px;
  padding: 16px 20px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  position: relative; z-index: 1;
}
.brief-icon { font-size: 1.2rem; }
.brief-text { font-size: 0.85rem; color: #525252; font-weight: 500; }

/* No Operation */
.no-operation {
  max-width: 720px; margin: 24px auto; padding: 0 24px;
  text-align: center;
  position: relative; z-index: 1;
}
.no-op-icon {
  width: 64px; height: 64px; border-radius: 50%;
  background: #dcfce7; color: #16a34a;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; margin: 0 auto 16px;
}
.no-operation h3 { font-size: 1.2rem; font-weight: 700; color: #171717; margin: 0 0 8px; }
.no-operation p { font-size: 0.85rem; color: #737373; margin: 0 0 20px; }

.holdings-list {
  display: flex; flex-direction: column; gap: 8px;
}
.holding-item {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(0,0,0,0.05);
}
.holding-name { font-size: 0.9rem; font-weight: 600; color: #171717; }
.holding-reason { font-size: 0.78rem; color: #a3a3a3; }

/* Section Title */
.section-title {
  max-width: 720px; margin: 24px auto 12px; padding: 0 24px;
  display: flex; align-items: center; gap: 10px;
  font-size: 0.9rem; font-weight: 700; color: #171717;
  position: relative; z-index: 1;
}
.section-badge {
  width: 24px; height: 24px; border-radius: 50%;
  background: #171717; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700;
}
.section-badge.hold { background: #e5e5e5; color: #737373; }

/* Operations */
.operations-list {
  max-width: 720px; margin: 0 auto; padding: 0 24px;
  display: flex; flex-direction: column; gap: 16px;
  position: relative; z-index: 1;
}

.operation-card {
  background: #fff; border-radius: 20px;
  padding: 20px;
  border: 2px solid transparent;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
  transition: all 0.2s ease;
}
.operation-card.action-buy { border-color: rgba(34, 197, 94, 0.2); }
.operation-card.action-sell { border-color: rgba(239, 68, 68, 0.2); }

.op-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.op-action-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 10px;
  font-size: 0.8rem; font-weight: 700;
}
.op-action-badge.action-buy { background: #dcfce7; color: #16a34a; }
.op-action-badge.action-sell { background: #fee2e2; color: #dc2626; }
.op-icon { font-size: 0.9rem; }
.op-confidence { font-size: 0.78rem; color: #a3a3a3; font-weight: 500; }

.op-body {
  display: flex; flex-direction: column; gap: 12px;
}
.op-symbol {
  display: flex; align-items: center; gap: 10px;
}
.symbol-code { font-size: 1rem; font-weight: 700; color: #171717; }
.symbol-name { font-size: 0.85rem; color: #737373; }

.op-reason {
  background: #fafafa; border-radius: 12px;
  padding: 12px 14px;
}
.reason-label { font-size: 0.7rem; font-weight: 700; color: #a3a3a3; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.reason-text { font-size: 0.85rem; color: #525252; line-height: 1.5; }

.op-strategy, .op-amount {
  display: flex; align-items: center; justify-content: space-between;
}
.strategy-label, .amount-label { font-size: 0.8rem; color: #a3a3a3; }
.strategy-name { font-size: 0.85rem; font-weight: 600; color: #525252; }
.amount-value { font-size: 1rem; font-weight: 700; color: #171717; }

/* Teaching */
.teaching-section {
  margin-top: 12px;
  border-top: 1px solid rgba(0,0,0,0.05);
  padding-top: 12px;
}
.teaching-toggle {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; padding: 10px 0;
  background: none; border: none;
  font-size: 0.85rem; font-weight: 600; color: #525252;
  cursor: pointer; font-family: inherit;
}
.teaching-content {
  background: #f0f9ff; border-radius: 12px;
  padding: 14px;
  font-size: 0.85rem; color: #525252; line-height: 1.6;
  margin-top: 4px;
}

/* Actions */
.op-actions {
  display: flex; gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0,0,0,0.05);
}
.btn-ignore {
  flex: 1;
  padding: 14px;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 14px;
  background: #fff; color: #737373;
  font-family: inherit; font-size: 0.88rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-ignore:hover { border-color: rgba(0,0,0,0.15); color: #171717; }

.btn-confirm {
  flex: 2;
  padding: 14px;
  border: none; border-radius: 14px;
  font-family: inherit; font-size: 0.88rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-confirm.buy { background: #16a34a; color: #fff; }
.btn-confirm.buy:hover { background: #15803d; }
.btn-confirm.sell { background: #dc2626; color: #fff; }
.btn-confirm.sell:hover { background: #b91c1c; }

/* Holdings Section */
.holdings-section {
  max-width: 720px; margin: 24px auto; padding: 0 24px;
  position: relative; z-index: 1;
}
.holdings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}
.holding-card {
  background: #fff; border-radius: 14px;
  padding: 14px;
  border: 1px solid rgba(0,0,0,0.05);
  text-align: center;
}
.holding-symbol { font-size: 0.85rem; font-weight: 700; color: #171717; }
.holding-name { font-size: 0.75rem; color: #a3a3a3; margin-top: 4px; }
.holding-status {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 10px; border-radius: 8px;
  background: #f5f5f5; color: #737373;
  font-size: 0.7rem; font-weight: 600;
}

@media (min-width: 768px) {
  .operations-list,
  .holdings-section,
  .market-brief,
  .no-operation,
  .section-title {
    padding-left: 32px;
    padding-right: 32px;
  }
}
</style>

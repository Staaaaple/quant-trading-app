<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { backtestApi, type Backtest } from '@/api/backtest'
import { dnaApi, type StrategyDNA, type StrategyPhylogeny } from '@/api/dna'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

const route = useRoute()
const router = useRouter()
const backtestId = route.params.backtest_id as string

const backtest = ref<Backtest | null>(null)
const dna = ref<StrategyDNA | null>(null)
const phylogeny = ref<StrategyPhylogeny | null>(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const bt = await backtestApi.get(backtestId)
    backtest.value = bt
    // Load eco data in parallel
    const [dnaData, phyloData] = await Promise.all([
      dnaApi.getDNA(bt.strategy_id).catch(() => null),
      dnaApi.getPhylogeny(bt.strategy_id).catch(() => null),
    ])
    dna.value = dnaData
    phylogeny.value = phyloData
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  load()
})

function returnClass(val: number | undefined | null) {
  if (val === undefined || val === null) return ''
  return val >= 0 ? 'text-profit' : 'text-loss'
}

function fmtPct(val: number | undefined | null): string {
  if (val === undefined || val === null || val === '') return '-'
  const n = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(n)) return '-'
  return `${(n * 100).toFixed(2)}%`
}

function fmtNum(val: number | undefined | null, digits = 2): string {
  if (val === undefined || val === null || val === '') return '-'
  const n = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(n)) return '-'
  return n.toFixed(digits)
}

function fmtInt(val: number | undefined | null): string {
  if (val === undefined || val === null || val === '') return '-'
  const n = typeof val === 'string' ? parseInt(val) : val
  if (isNaN(n)) return '-'
  return String(n)
}

// ── Metrics comparison ──
const metricsRows = computed(() => {
  if (!backtest.value) return []
  const s = backtest.value.metrics || {}
  const b = backtest.value.benchmark_metrics || {}

  const rows = [
    { label: '总收益', s: s.total_return, b: b.total_return, fmt: fmtPct },
    { label: '年化收益', s: s.annualized_return, b: b.annualized_return, fmt: fmtPct },
    { label: '夏普比率', s: s.sharpe_ratio, b: b.sharpe_ratio, fmt: (v: any) => fmtNum(v) },
    { label: '索提诺比率', s: s.sortino_ratio, b: b.sortino_ratio, fmt: (v: any) => fmtNum(v) },
    { label: '卡玛比率', s: s.calmar_ratio, b: b.calmar_ratio, fmt: (v: any) => fmtNum(v) },
    { label: '最大回撤', s: s.max_drawdown, b: b.max_drawdown, fmt: fmtPct },
    { label: '波动率', s: s.volatility, b: b.volatility, fmt: fmtPct },
    { label: '胜率', s: s.win_rate, b: b.win_rate, fmt: fmtPct },
    { label: '持仓时间占比', s: s.exposure_time_pct, b: b.exposure_time_pct, fmt: fmtPct },
    { label: '交易次数', s: s.trade_count, b: b.trade_count, fmt: fmtInt },
    { label: '总K线数', s: s.total_bars, b: b.total_bars, fmt: fmtInt },
  ]

  // Filter out rows where both values are empty
  return rows.filter(r => r.s !== undefined && r.s !== null || r.b !== undefined && r.b !== null)
})

const hasBenchmark = computed(() => !!backtest.value?.benchmark_metrics)

function diffLabel(sVal: any, bVal: any) {
  if (sVal === undefined || sVal === null || bVal === undefined || bVal === null) return '-'
  const s = typeof sVal === 'string' ? parseFloat(sVal) : sVal
  const b = typeof bVal === 'string' ? parseFloat(bVal) : bVal
  if (isNaN(s) || isNaN(b)) return '-'
  const delta = s - b
  const sign = delta > 0 ? '+' : ''
  return `${sign}${(delta * 100).toFixed(2)}%`
}

function diffClass(sVal: any, bVal: any) {
  if (sVal === undefined || sVal === null || bVal === undefined || bVal === null) return ''
  const s = typeof sVal === 'string' ? parseFloat(sVal) : sVal
  const b = typeof bVal === 'string' ? parseFloat(bVal) : bVal
  if (isNaN(s) || isNaN(b)) return ''
  // For drawdown, lower is better
  const isInverse = ['最大回撤'].includes('')
  const delta = s - b
  if (isInverse) return delta < 0 ? 'text-profit' : 'text-loss'
  return delta >= 0 ? 'text-profit' : 'text-loss'
}

// ── Eco helpers ──
const healthColor = (score: number) => {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#d97706'
  return '#92400e'
}
const healthLabel = (score: number) => {
  if (score >= 80) return '健康'
  if (score >= 60) return '一般'
  return '需关注'
}
const phaseMap: Record<string, string> = { young: '年轻', mature: '成熟', aging: '衰老', endangered: '濒危' }
</script>

<template>
  <div class="page">
    <div v-if="error" class="error-card">
      <p>{{ error }}</p>
      <button class="btn btn--primary" @click="router.back()">返回</button>
    </div>

    <template v-else-if="backtest">
      <!-- Header -->
      <div class="detail-header">
        <div class="header-left">
          <button class="back-btn" @click="router.back()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            回测中心
          </button>
          <h1 class="detail-title">{{ backtest.backtest_id }}</h1>
          <div class="detail-meta">
            <span class="meta-item">
              <span class="meta-label">策略</span>
              <RouterLink :to="`/dna-report/${backtest.strategy_id}`" class="meta-link mono">
                {{ backtest.strategy_id }}
              </RouterLink>
            </span>
            <span class="meta-sep">·</span>
            <span class="meta-item">
              <span class="meta-label">周期</span>
              {{ backtest.start_date }} ~ {{ backtest.end_date }}
            </span>
            <span class="meta-sep">·</span>
            <span class="meta-item">
              <span class="meta-label">初始资金</span>
              {{ backtest.initial_cash.toLocaleString() }}
            </span>
            <span class="meta-sep">·</span>
            <span class="meta-item">
              <span class="meta-label">状态</span>
              <span :class="['status-badge', `status-badge--${backtest.status}`]">
                {{ backtest.status }}
              </span>
            </span>
          </div>
        </div>
      </div>

      <!-- Metrics Comparison -->
      <div class="section">
        <h2 class="section-title">
          <span class="section-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
          </span>
          回测指标对比
        </h2>

        <div v-if="!hasBenchmark" class="empty-state">
          <p>基准数据缺失 — 该回测在基准对比功能上线前运行，或运行过程中出错。</p>
        </div>

        <div class="metrics-grid">
          <!-- Strategy highlight cards -->
          <div class="metric-hero" :class="returnClass(backtest.metrics?.total_return)">
            <div class="metric-hero-label">策略总收益</div>
            <div class="metric-hero-value">{{ fmtPct(backtest.metrics?.total_return) }}</div>
          </div>
          <div class="metric-hero" :class="returnClass(backtest.benchmark_metrics?.total_return)">
            <div class="metric-hero-label">基准总收益（买入持有）</div>
            <div class="metric-hero-value">{{ fmtPct(backtest.benchmark_metrics?.total_return) }}</div>
          </div>
        </div>

        <div class="comparison-table-wrap">
          <table class="comparison-table">
            <thead>
              <tr>
                <th>指标</th>
                <th class="col-strategy">策略</th>
                <th v-if="hasBenchmark" class="col-benchmark">基准</th>
                <th v-if="hasBenchmark" class="col-delta">超额</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in metricsRows" :key="row.label">
                <td class="row-label">{{ row.label }}</td>
                <td class="col-strategy" :class="returnClass(row.s)">{{ row.fmt(row.s) }}</td>
                <td v-if="hasBenchmark" class="col-benchmark" :class="returnClass(row.b)">{{ row.fmt(row.b) }}</td>
                <td v-if="hasBenchmark" class="col-delta" :class="diffClass(row.s, row.b)">
                  {{ diffLabel(row.s, row.b) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Eco Snapshot -->
      <div v-if="dna" class="section">
        <h2 class="section-title">
          <span class="section-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
          </span>
          策略生态快照
        </h2>
        <div class="eco-grid">
          <!-- Health -->
          <div class="eco-card">
            <div class="eco-card-header">
              <span class="eco-card-title">健康度</span>
              <span v-if="dna.inbreeding_coefficient > 0.3" class="eco-badge eco-badge--warn">近亲风险</span>
            </div>
            <div class="eco-card-body">
              <div class="eco-score" :style="{ color: healthColor(dna.health_birth_score) }">
                {{ dna.health_birth_score }}
              </div>
              <div class="eco-score-label">{{ healthLabel(dna.health_birth_score) }}</div>
              <div class="eco-score-sub">
                多样性 {{ (dna.gene_diversity_score * 100).toFixed(0) }}%
                · 近亲系数 {{ dna.inbreeding_coefficient }}
              </div>
            </div>
          </div>

          <!-- Metabolic -->
          <div class="eco-card">
            <div class="eco-card-header">
              <span class="eco-card-title">代谢特征</span>
              <span v-if="dna.metabolic_syndrome" class="eco-badge eco-badge--danger">代谢综合征</span>
            </div>
            <div class="eco-card-body">
              <div class="eco-metabolic-row">
                <span class="eco-metabolic-label">信息代谢率</span>
                <span class="eco-metabolic-value">{{ dna.metabolic_rate }}/天</span>
              </div>
              <div class="eco-bar">
                <div
                  class="eco-bar-fill"
                  :style="{
                    width: `${Math.min(dna.metabolic_rate * 100, 100)}%`,
                    background: dna.metabolic_rate > 0.2 ? '#b91c1c' : dna.metabolic_rate > 0.08 ? '#d97706' : '#16a34a'
                  }"
                />
              </div>
              <div class="eco-metabolic-row" style="margin-top: 12px;">
                <span class="eco-metabolic-label">生态位宽度</span>
                <span class="eco-metabolic-value">{{ (dna.niche_width * 100).toFixed(0) }}%</span>
              </div>
              <div class="eco-bar">
                <div
                  class="eco-bar-fill"
                  :style="{
                    width: `${dna.niche_width * 100}%`,
                    background: dna.niche_width > 0.6 ? '#16a34a' : dna.niche_width > 0.3 ? '#d97706' : '#92400e'
                  }"
                />
              </div>
            </div>
          </div>

          <!-- Lifespan -->
          <div class="eco-card">
            <div class="eco-card-header">
              <span class="eco-card-title">寿命预测</span>
              <span :class="['phase-badge', `phase-${dna.lifespan_phase}`]">
                {{ phaseMap[dna.lifespan_phase] || '成熟' }}
              </span>
            </div>
            <div class="eco-card-body">
              <div class="eco-score">{{ dna.lifespan_months }}</div>
              <div class="eco-score-label">预计剩余寿命（月）</div>
              <div class="eco-score-sub">
                老化速度 {{ (dna.aging_velocity * 100).toFixed(1) }}%
              </div>
            </div>
          </div>

          <!-- Family -->
          <div class="eco-card">
            <div class="eco-card-header">
              <span class="eco-card-title">家族归属</span>
              <span v-if="phylogeny?.inbreeding_warning" class="eco-badge eco-badge--warn">近亲警告</span>
            </div>
            <div class="eco-card-body">
              <div class="eco-family-name">
                {{ phylogeny?.family_name || dna.family_name || '未归类' }}
              </div>
              <div class="eco-score-label">{{ phylogeny?.relatives?.length || 0 }} 个亲属策略</div>
              <div class="eco-score-sub">
                同质性风险 {{ ((phylogeny?.homogeneity_risk || 0) * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
        </div>

        <!-- Gene Tags Mini -->
        <div class="gene-mini">
          <div v-for="layer in [
            { title: '特征层', genes: dna.feature_genes, color: '#16a34a' },
            { title: '信号层', genes: dna.signal_genes, color: '#d97706' },
            { title: '风控层', genes: dna.risk_genes, color: '#b91c1c' },
            { title: '执行层', genes: dna.execution_genes, color: '#3b82f6' },
          ]" :key="layer.title" class="gene-mini-col">
            <div class="gene-mini-header" :style="{ color: layer.color }">
              {{ layer.title }}
              <span class="gene-mini-count">{{ layer.genes.length }}</span>
            </div>
            <div class="gene-mini-tags">
              <span v-for="g in layer.genes" :key="g" class="gene-mini-tag">{{ g }}</span>
              <span v-if="!layer.genes.length" class="gene-mini-empty">未检测到</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Logs -->
      <div class="section">
        <h2 class="section-title">
          <span class="section-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </span>
          运行日志
        </h2>
        <pre v-if="backtest.logs" class="log-block">{{ typeof backtest.logs === 'string' ? backtest.logs : JSON.stringify(backtest.logs, null, 2) }}</pre>
        <p v-else class="empty-state">暂无日志</p>
      </div>
    </template>

    <LoadingOverlay :visible="loading" text="加载回测详情..." />
  </div>
</template>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
}

/* Header */
.detail-header {
  margin-bottom: var(--space-2xl);
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: var(--space-lg);
}

.back-btn:hover {
  border-color: var(--border-focus);
  color: var(--text-primary);
}

.detail-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
  letter-spacing: -0.02em;
}

.detail-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-sm) var(--space-lg);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
}

.meta-label {
  color: var(--text-muted);
}

.meta-link {
  color: var(--accent);
  text-decoration: none;
}

.meta-link:hover {
  text-decoration: underline;
}

.meta-sep {
  color: var(--text-muted);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge--success {
  background: rgba(22, 163, 74, 0.1);
  color: #16a34a;
}

.status-badge--pending {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.status-badge--running {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.status-badge--failed {
  background: rgba(185, 28, 28, 0.1);
  color: #b91c1c;
}

/* Section */
.section {
  margin-bottom: var(--space-2xl);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-xl) 0;
}

.section-icon {
  display: flex;
  align-items: center;
  color: var(--text-muted);
}

/* Metrics */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.metric-hero {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
  text-align: center;
}

.metric-hero-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.metric-hero-value {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1;
}

/* Comparison Table */
.comparison-table-wrap {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.comparison-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.9rem;
}

.comparison-table th,
.comparison-table td {
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.comparison-table th {
  background: var(--bg-base);
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.comparison-table tbody tr:last-child td {
  border-bottom: none;
}

.comparison-table tbody tr:hover {
  background: var(--bg-surface-hover);
}

.row-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.col-strategy,
.col-benchmark,
.col-delta {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-delta {
  font-weight: 600;
}

/* Eco Grid */
.eco-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.eco-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.eco-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.eco-card-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.eco-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
}

.eco-badge--warn {
  background: rgba(217, 119, 6, 0.1);
  color: #d97706;
}

.eco-badge--danger {
  background: rgba(185, 28, 28, 0.1);
  color: #b91c1c;
}

.eco-card-body {
  text-align: center;
}

.eco-score {
  font-size: 2.2rem;
  font-weight: 800;
  line-height: 1;
  color: var(--text-primary);
}

.eco-score-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.eco-score-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 8px;
  line-height: 1.5;
}

.eco-metabolic-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.eco-metabolic-label {
  color: var(--text-secondary);
}

.eco-metabolic-value {
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.eco-bar {
  width: 100%;
  height: 6px;
  background: var(--border-subtle);
  border-radius: 999px;
  overflow: hidden;
}

.eco-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.eco-family-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.phase-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
}

.phase-young {
  background: rgba(22, 163, 74, 0.1);
  color: #16a34a;
}

.phase-mature {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.phase-aging {
  background: rgba(217, 119, 6, 0.1);
  color: #d97706;
}

.phase-endangered {
  background: rgba(185, 28, 28, 0.1);
  color: #b91c1c;
}

/* Gene Mini */
.gene-mini {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-xl);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.gene-mini-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: var(--space-sm);
}

.gene-mini-count {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--text-muted);
  background: var(--bg-base);
  padding: 2px 8px;
  border-radius: 999px;
}

.gene-mini-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.gene-mini-tag {
  font-size: 0.75rem;
  padding: 3px 8px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
}

.gene-mini-empty {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-style: italic;
}

/* Logs */
.log-block {
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  font-size: 0.8rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
}

/* Misc */
.empty-state {
  text-align: center;
  color: var(--text-muted);
  padding: var(--space-2xl);
  font-size: 0.9rem;
}

.error-card {
  text-align: center;
  padding: var(--space-3xl);
  color: var(--error);
}

.error-card p {
  margin-bottom: var(--space-lg);
}

.text-profit {
  color: var(--profit);
  font-weight: 600;
}

.text-loss {
  color: var(--loss);
  font-weight: 600;
}

.mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Responsive */
@media (max-width: 900px) {
  .eco-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .gene-mini {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  .eco-grid {
    grid-template-columns: 1fr;
  }
  .gene-mini {
    grid-template-columns: 1fr;
  }
  .detail-meta {
    flex-direction: column;
    align-items: flex-start;
  }
  .meta-sep {
    display: none;
  }
}
</style>

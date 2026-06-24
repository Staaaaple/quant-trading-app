<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { backtestApi, type Backtest } from '@/api/backtest'

const router = useRouter()
const backtests = ref<Backtest[]>([])
const loading = ref(true)
const running = ref(false)

// ── 配置回测状态 ──
interface PortfolioBinding {
  strategy_id: string
  strategy_name?: string
  strategy_family?: string
  symbol?: string
  symbol_name?: string
  name?: string
  code?: string
  weight?: number
  sector?: string
}

const portfolioBindings = ref<PortfolioBinding[]>([])
const startDate = ref('')
const endDate = ref('')
const initialCash = ref(100000)
const configError = ref('')

function defaultDateRange() {
  const end = new Date()
  const start = new Date()
  start.setFullYear(end.getFullYear() - 1)
  endDate.value = end.toISOString().split('T')[0] || ''
  startDate.value = start.toISOString().split('T')[0] || ''
}

function loadPortfolio() {
  configError.value = ''
  const stored = sessionStorage.getItem('latest_portfolio')
  if (!stored) {
    portfolioBindings.value = []
    configError.value = '未检测到组合数据，请先在组合页面生成组合。'
    return
  }
  try {
    const portfolio = JSON.parse(stored)
    const bindings = portfolio?.portfolio?.bindings || []
    portfolioBindings.value = bindings.map((b: any) => ({
      strategy_id: b.strategy_id,
      strategy_name: b.strategy_name,
      strategy_family: b.strategy_family,
      symbol: b.symbol,
      symbol_name: b.symbol_name,
      name: b.name,
      code: b.code,
      weight: b.weight,
      sector: b.sector,
    })).filter((b: PortfolioBinding) => b.strategy_id)
    if (portfolioBindings.value.length === 0) {
      configError.value = '组合中未找到可回测的策略。'
    }
  } catch (e) {
    portfolioBindings.value = []
    configError.value = '组合数据解析失败。'
  }
}

const validBindings = computed(() =>
  portfolioBindings.value.filter(b => b.strategy_id && b.symbol)
)

const missingSymbolBindings = computed(() =>
  portfolioBindings.value.filter(b => b.strategy_id && !b.symbol)
)

// ── 回测显示名称映射 ──
const strategyDisplayMap = computed(() => {
  const map: Record<string, string> = {}
  portfolioBindings.value.forEach((b) => {
    if (!b.strategy_id) return
    let displayName = b.strategy_id
    const namePart = b.symbol_name || b.name || b.strategy_name
    const codePart = b.symbol || b.code || b.strategy_id
    if (namePart || codePart) {
      displayName = [namePart, codePart].filter(Boolean).join(' ')
    }
    map[b.strategy_id] = displayName
  })
  return map
})

function getBacktestDisplayName(bt: Backtest): string {
  return strategyDisplayMap.value[bt.strategy_id] || bt.strategy_id
}

interface GroupSummary {
  totalCash: number
  weightedReturn: number
  weightedSharpe: number
  maxDrawdown: number
  count: number
}

function computeGroupSummary(items: Backtest[]): GroupSummary {
  const totalCash = items.reduce((sum, bt) => sum + bt.initial_cash, 0)
  let weightedReturn = 0
  let weightedSharpe = 0
  let maxDrawdown = 0
  if (totalCash > 0) {
    weightedReturn = items.reduce(
      (sum, bt) => sum + (bt.metrics?.total_return || 0) * bt.initial_cash,
      0
    ) / totalCash
    weightedSharpe = items.reduce(
      (sum, bt) => sum + (bt.metrics?.sharpe_ratio || 0) * bt.initial_cash,
      0
    ) / totalCash
  }
  maxDrawdown = items.reduce(
    (max, bt) => Math.max(max, bt.metrics?.max_drawdown || 0),
    0
  )
  return { totalCash, weightedReturn, weightedSharpe, maxDrawdown, count: items.length }
}

// ── 按回测时间段分组 ──
const groupedBacktests = computed(() => {
  const groups: Record<string, Backtest[]> = {}
  backtests.value.forEach((bt) => {
    const key = `${bt.start_date} ~ ${bt.end_date}`
    if (!groups[key]) groups[key] = []
    groups[key].push(bt)
  })
  return Object.entries(groups).sort((a, b) => {
    const tA = a[1][0]?.created_at || ''
    const tB = b[1][0]?.created_at || ''
    return tB.localeCompare(tA)
  })
})

function generateBacktestId(strategyId: string): string {
  return `bt-${strategyId}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
}

async function runSingleBacktest(binding: PortfolioBinding): Promise<{ ok: boolean; strategyId: string; error?: string }> {
  const backtestId = generateBacktestId(binding.strategy_id)
  try {
    await backtestApi.create({
      backtest_id: backtestId,
      strategy_id: binding.strategy_id,
      start_date: startDate.value,
      end_date: endDate.value,
      initial_cash: initialCash.value,
    })
    await backtestApi.run(backtestId, {
      symbols: binding.symbol ? [binding.symbol] : [],
      start_date: startDate.value,
      end_date: endDate.value,
      initial_cash: initialCash.value,
    })
    return { ok: true, strategyId: binding.strategy_id }
  } catch (e: any) {
    return { ok: false, strategyId: binding.strategy_id, error: e.message || '未知错误' }
  }
}

async function runBacktests() {
  if (validBindings.value.length === 0) {
    configError.value = '没有可回测的策略，请确认组合中包含带标的的策略。'
    return
  }
  if (!startDate.value || !endDate.value) {
    configError.value = '请选择回测开始和结束日期。'
    return
  }
  if (startDate.value >= endDate.value) {
    configError.value = '结束日期必须晚于开始日期。'
    return
  }

  running.value = true
  configError.value = ''
  try {
    const results = await Promise.allSettled(
      validBindings.value.map(b => runSingleBacktest(b))
    )
    const successes = results.filter(r => r.status === 'fulfilled' && r.value.ok).length
    const failures = results.filter(r => r.status === 'rejected' || (r.status === 'fulfilled' && !r.value.ok)).length
    alert(`回测提交完成：成功 ${successes} 个，失败 ${failures} 个`)
    await loadBacktests()
  } catch (e) {
    console.error('Run backtests failed:', e)
    alert('回测运行失败')
  } finally {
    running.value = false
  }
}

// ── 回测列表 ──
async function loadBacktests() {
  loading.value = true
  try {
    backtests.value = await backtestApi.list()
  } catch (e) {
    console.error('Failed to load backtests:', e)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/')
}

function goDetail(id: string) {
  router.push(`/backtests/${id}`)
}

function statusClass(status: string): string {
  const map: Record<string, string> = {
    'success': 'status-success',
    'failed': 'status-failed',
    'running': 'status-running',
    'pending': 'status-pending',
  }
  return map[status] || 'status-pending'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    'success': '成功',
    'failed': '失败',
    'running': '运行中',
    'pending': '等待中',
  }
  return map[status] || status
}

// ── 分组折叠 ──
const expandedGroups = ref<Set<string>>(new Set())

function isGroupExpanded(period: string): boolean {
  return expandedGroups.value.has(period)
}

function toggleGroup(period: string) {
  if (expandedGroups.value.has(period)) {
    expandedGroups.value.delete(period)
  } else {
    expandedGroups.value.add(period)
  }
}

// ── 分组备注（本地存储） ──
const GROUP_NOTES_KEY = 'backtest_group_notes'
const groupNotes = ref<Record<string, string>>({})
const editingGroupNote = ref<string | null>(null)
const groupNoteDraft = ref('')

function loadGroupNotes() {
  try {
    const raw = localStorage.getItem(GROUP_NOTES_KEY)
    groupNotes.value = raw ? JSON.parse(raw) : {}
  } catch {
    groupNotes.value = {}
  }
}

function saveGroupNotes() {
  localStorage.setItem(GROUP_NOTES_KEY, JSON.stringify(groupNotes.value))
}

function startEditGroupNote(period: string) {
  editingGroupNote.value = period
  groupNoteDraft.value = groupNotes.value[period] || ''
}

function saveGroupNote(period: string) {
  const trimmed = groupNoteDraft.value.trim()
  if (trimmed) {
    groupNotes.value[period] = trimmed
  } else {
    delete groupNotes.value[period]
  }
  saveGroupNotes()
  editingGroupNote.value = null
}

function cancelEditGroupNote() {
  editingGroupNote.value = null
  groupNoteDraft.value = ''
}

// ── 删除分组回测 ──
async function removeGroup(period: string, items: Backtest[]) {
  if (!confirm(`确定删除「${period}」的全部 ${items.length} 条回测记录？`)) return
  try {
    await Promise.all(items.map((bt) => backtestApi.remove(bt.backtest_id)))
    delete groupNotes.value[period]
    saveGroupNotes()
    await loadBacktests()
  } catch (e) {
    console.error('Delete group failed:', e)
    alert('删除失败')
    await loadBacktests()
  }
}

onMounted(() => {
  defaultDateRange()
  loadPortfolio()
  loadBacktests()
  loadGroupNotes()
})
</script>

<template>
  <div class="backtest-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <div class="header-title">
          <span class="header-label">BACKTEST CENTER</span>
          <span class="header-name">回测中心</span>
        </div>
        <div class="header-placeholder"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="backtest-content">
      <div v-if="loading" class="loading-state">加载回测记录...</div>

      <template v-else>
        <!-- 配置回测 -->
        <div class="config-card">
          <div class="config-header">
            <div class="config-title">
              <span class="config-label">CONFIGURE</span>
              <span class="config-name">配置回测</span>
            </div>
            <button class="import-btn" @click="loadPortfolio">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
                <path d="M16 21h5v-5"/>
              </svg>
              <span>重新导入组合</span>
            </button>
          </div>

          <div v-if="configError" class="config-error">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 8v4"/>
              <path d="M12 16h.01"/>
            </svg>
            <span>{{ configError }}</span>
          </div>

          <div v-if="portfolioBindings.length > 0" class="portfolio-summary">
            <div class="summary-row">
              <span class="summary-text">已导入 <strong>{{ portfolioBindings.length }}</strong> 个策略，</span>
              <span class="summary-text">可回测 <strong>{{ validBindings.length }}</strong> 个</span>
            </div>
            <div class="binding-list">
              <div v-for="b in validBindings" :key="b.strategy_id" class="binding-tag">
                <span class="binding-name">{{ b.strategy_name || b.strategy_id }}</span>
                <span v-if="b.symbol" class="binding-symbol">{{ b.symbol }}</span>
                <span v-if="b.weight" class="binding-weight">{{ (b.weight * 100).toFixed(0) }}%</span>
              </div>
            </div>
            <div v-if="missingSymbolBindings.length > 0" class="missing-tip">
              以下策略缺少标的，无法回测：{{ missingSymbolBindings.map(b => b.strategy_name || b.strategy_id).join('、') }}
            </div>
          </div>

          <div class="config-form">
            <div class="form-group">
              <label class="form-label">回测区间</label>
              <div class="date-range">
                <input v-model="startDate" type="date" class="form-input" />
                <span class="date-sep">~</span>
                <input v-model="endDate" type="date" class="form-input" />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">初始资金</label>
              <div class="cash-input">
                <span class="cash-prefix">¥</span>
                <input v-model.number="initialCash" type="number" class="form-input" min="10000" step="10000" />
              </div>
            </div>
          </div>

          <button class="run-btn" :disabled="running || validBindings.length === 0" @click="runBacktests">
            <span v-if="running">正在运行回测...</span>
            <span v-else>一键运行回测</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/>
              <path d="m12 5 7 7-7 7"/>
            </svg>
          </button>
        </div>

        <!-- Stats -->
        <div class="stats-bar">
          <div class="stat-pill">
            <span class="stat-num">{{ backtests.length }}</span>
            <span class="stat-label">总回测</span>
          </div>
          <div class="stat-pill">
            <span class="stat-num">{{ backtests.filter(b => b.status === 'success').length }}</span>
            <span class="stat-label">成功</span>
          </div>
          <div class="stat-pill">
            <span class="stat-num">{{ backtests.filter(b => b.status === 'running').length }}</span>
            <span class="stat-label">运行中</span>
          </div>
        </div>

        <!-- List -->
        <div class="backtest-groups">
          <div
            v-for="[period, items] in groupedBacktests"
            :key="period"
            class="backtest-group"
          >
            <div
              class="backtest-group-title"
              role="button"
              tabindex="0"
              :aria-expanded="isGroupExpanded(period)"
              @click="toggleGroup(period)"
              @keydown.enter.prevent="toggleGroup(period)"
              @keydown.space.prevent="toggleGroup(period)"
            >
              <span class="group-chevron" :class="{ expanded: isGroupExpanded(period) }">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m6 9 6 6 6-6"/>
                </svg>
              </span>
              <span class="group-period">{{ period }}</span>
              <div class="group-note" @click.stop>
                <input
                  v-if="editingGroupNote === period"
                  v-model="groupNoteDraft"
                  class="note-input group-note-input"
                  placeholder="输入备注，回车保存"
                  @blur="saveGroupNote(period)"
                  @keydown.enter="saveGroupNote(period)"
                  @keydown.esc="cancelEditGroupNote"
                  @click.stop
                />
                <template v-else>
                  <span
                    v-if="groupNotes[period]"
                    class="note-text"
                    @click.stop="startEditGroupNote(period)"
                  >
                    {{ groupNotes[period] }}
                  </span>
                  <button
                    v-else
                    class="note-add"
                    @click.stop="startEditGroupNote(period)"
                  >
                    + 备注
                  </button>
                </template>
              </div>
              <span class="group-count">{{ items.length }} 条</span>
              <button
                class="delete-group-btn"
                title="删除该时段全部回测"
                @click.stop="removeGroup(period, items)"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                  <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
            <div
              v-show="isGroupExpanded(period)"
              class="backtest-list"
            >
              <div class="group-summary-card">
                <div class="group-summary-title">组合汇总</div>
                <div class="group-summary-metrics">
                  <div class="metric">
                    <span class="metric-label">总资金</span>
                    <span class="metric-val">¥{{ Math.round(computeGroupSummary(items).totalCash).toLocaleString() }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">加权收益</span>
                    <span
                      class="metric-val"
                      :class="computeGroupSummary(items).weightedReturn >= 0 ? 'up' : 'down'"
                    >
                      {{ computeGroupSummary(items).weightedReturn >= 0 ? '+' : '' }}{{ (computeGroupSummary(items).weightedReturn * 100).toFixed(2) }}%
                    </span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">加权夏普</span>
                    <span class="metric-val">{{ computeGroupSummary(items).weightedSharpe.toFixed(2) }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">最大回撤</span>
                    <span class="metric-val down">{{ (computeGroupSummary(items).maxDrawdown * 100).toFixed(2) }}%</span>
                  </div>
                </div>
              </div>
              <div
                v-for="bt in items"
                :key="bt.id"
                class="backtest-card"
                @click="goDetail(bt.backtest_id)"
              >
                <div class="backtest-header">
                  <div class="backtest-info">
                    <div class="backtest-name">{{ getBacktestDisplayName(bt) }}</div>
                  </div>
                  <span :class="['status-badge', statusClass(bt.status)]">
                    {{ statusLabel(bt.status) }}
                  </span>
                </div>
                <div class="backtest-meta">
                  <span>初始资金 ¥{{ bt.initial_cash.toLocaleString() }}</span>
                  <span>{{ new Date(bt.created_at).toLocaleString() }}</span>
                </div>
                <div v-if="bt.metrics" class="backtest-metrics">
                  <div class="metric">
                    <span class="metric-label">总收益</span>
                    <span class="metric-val" :class="bt.metrics.total_return >= 0 ? 'up' : 'down'">
                      {{ bt.metrics.total_return >= 0 ? '+' : '' }}{{ (bt.metrics.total_return * 100).toFixed(2) }}%
                    </span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">夏普</span>
                    <span class="metric-val">{{ bt.metrics.sharpe_ratio?.toFixed(2) || '—' }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">最大回撤</span>
                    <span class="metric-val down">{{ (bt.metrics.max_drawdown * 100).toFixed(2) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="backtests.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2"/>
              <path d="M3 9h18"/>
              <path d="M9 21V9"/>
            </svg>
          </div>
          <p class="empty-text">暂无回测记录</p>
          <p class="empty-sub">在上方配置回测模块中一键导入组合并运行</p>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.backtest-page {
  min-height: 100vh;
  background: #fafafa;
  position: relative;
  padding-bottom: 24px;
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
}
.page-header-inner {
  max-width: 720px; margin: 0 auto; padding: 12px 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.back-btn {
  width: 36px; height: 36px;
  border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.7);
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.back-btn:hover { background: #fff; border-color: rgba(0,0,0,0.1); color: #171717; }
.header-title { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }
.header-placeholder { width: 36px; }

/* Content */
.backtest-content {
  max-width: 720px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}
.loading-state { text-align: center; padding: 60px 0; color: #a3a3a3; font-size: 0.9rem; }

/* Config Card */
.config-card {
  background: #fff; border-radius: 20px; padding: 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.config-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.config-title { display: flex; flex-direction: column; gap: 2px; }
.config-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.config-name { font-size: 1rem; font-weight: 700; color: #171717; }
.import-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 12px;
  background: #fafafa; border: 1px solid rgba(0,0,0,0.06);
  border-radius: 10px;
  font-size: 0.75rem; font-weight: 600; color: #525252;
  cursor: pointer; transition: all 0.2s;
}
.import-btn:hover { background: #f5f5f5; border-color: rgba(0,0,0,0.1); color: #171717; }

.config-error {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 14px; margin-bottom: 14px;
  background: #fef2f2; border: 1px solid rgba(239,68,68,0.12);
  border-radius: 12px; color: #991b1b; font-size: 0.8rem;
}

.portfolio-summary { margin-bottom: 18px; }
.summary-row {
  display: flex; gap: 12px;
  font-size: 0.82rem; color: #525252; margin-bottom: 10px;
}
.summary-row strong { color: #171717; }
.binding-list {
  display: flex; flex-wrap: wrap; gap: 8px;
}
.binding-tag {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px;
  background: #fafafa; border: 1px solid rgba(0,0,0,0.05);
  border-radius: 8px; font-size: 0.76rem;
}
.binding-name { font-weight: 600; color: #171717; }
.binding-symbol { color: #737373; font-family: ui-monospace, SFMono-Regular, monospace; }
.binding-weight {
  color: #6366f1; font-weight: 600;
  background: #eef2ff; padding: 1px 6px; border-radius: 4px;
}
.missing-tip {
  margin-top: 10px; font-size: 0.75rem; color: #d97706;
}

.config-form {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-bottom: 18px;
}
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 0.75rem; font-weight: 600; color: #525252; }
.form-input {
  height: 42px;
  padding: 0 12px;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px;
  background: #fafafa;
  font-size: 0.85rem; color: #171717;
  outline: none; transition: all 0.2s;
}
.form-input:focus {
  border-color: rgba(99,102,241,0.4);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.08);
}
.date-range { display: flex; align-items: center; gap: 10px; }
.date-sep { color: #a3a3a3; font-weight: 600; }
.cash-input {
  display: flex; align-items: center;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px; background: #fafafa;
  overflow: hidden;
}
.cash-input:focus-within {
  border-color: rgba(99,102,241,0.4);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.08);
}
.cash-prefix {
  padding: 0 12px; color: #737373; font-weight: 600;
  border-right: 1px solid rgba(0,0,0,0.06);
}
.cash-input .form-input {
  flex: 1; border: none; border-radius: 0; background: transparent;
  box-shadow: none;
}

.run-btn {
  width: 100%;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 16px;
  background: #171717; color: #fff;
  border: none; border-radius: 14px;
  font-size: 0.9rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
}
.run-btn:hover:not(:disabled) {
  background: #262626;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}
.run-btn:disabled {
  background: #d4d4d4; color: #fff; cursor: not-allowed;
}

/* Stats */
.stats-bar { display: flex; gap: 10px; }
.stat-pill {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  padding: 14px; background: #fff;
  border-radius: 16px; border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.stat-num { font-size: 1.3rem; font-weight: 700; color: #171717; }
.stat-label { font-size: 0.72rem; color: #a3a3a3; margin-top: 4px; }

/* Cards */
.backtest-groups { display: flex; flex-direction: column; gap: 20px; }
.backtest-group-title {
  position: sticky; top: 68px; z-index: 10;
  display: flex; align-items: center; gap: 10px;
  width: 100%;
  padding: 10px 16px; margin: 0 -8px 12px;
  background: rgba(250,250,250,0.92);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 12px;
  font-size: 0.85rem; font-weight: 700; color: #171717;
  cursor: pointer; transition: all 0.2s;
  outline: none; user-select: none;
}
.backtest-group-title:hover {
  background: #fff;
  border-color: rgba(0,0,0,0.08);
}
.group-chevron {
  display: flex; align-items: center; justify-content: center;
  color: #a3a3a3;
  transition: transform 0.2s ease;
}
.group-chevron.expanded { transform: rotate(180deg); }
.group-period { flex: 1; text-align: left; }
.group-count {
  font-size: 0.72rem; font-weight: 600; color: #737373;
  background: rgba(0,0,0,0.04); padding: 2px 8px; border-radius: 6px;
}
.backtest-list { display: flex; flex-direction: column; gap: 10px; }
.backtest-card {
  background: #fff; border-radius: 16px; padding: 18px 20px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  transition: all 0.2s ease; cursor: pointer;
}
.backtest-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border-color: rgba(0,0,0,0.08);
  transform: translateY(-1px);
}
.group-summary-card {
  background: #f8fafc; border-radius: 16px; padding: 16px 20px;
  border: 1px solid rgba(0,0,0,0.05);
  margin-bottom: 4px;
}
.group-summary-title {
  font-size: 0.78rem; font-weight: 700; color: #525252; margin-bottom: 10px;
}
.group-summary-metrics { display: flex; gap: 24px; }
.group-summary-metrics .metric-label { font-size: 0.68rem; color: #a3a3a3; }
.group-summary-metrics .metric-val { font-size: 0.95rem; font-weight: 700; color: #171717; }
.backtest-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.group-note {
  flex: 1;
  display: flex; align-items: center;
  justify-content: flex-end;
  min-width: 0;
}
.group-note-input {
  max-width: 220px;
  height: 28px;
  padding: 0 8px;
  font-size: 0.75rem;
}
.delete-group-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: 1px solid rgba(0,0,0,0.06);
  border-radius: 8px; color: #a3a3a3;
  cursor: pointer; transition: all 0.2s;
  flex-shrink: 0;
}
.delete-group-btn:hover {
  background: #fef2f2; border-color: rgba(239,68,68,0.2); color: #991b1b;
}
.backtest-name { font-size: 0.95rem; font-weight: 700; color: #171717; }
.status-badge {
  font-size: 0.7rem; font-weight: 600; padding: 4px 10px;
  border-radius: 6px;
}
.status-success { background: #f0fdf4; color: #166534; }
.status-failed { background: #fef2f2; color: #991b1b; }
.status-running { background: #eff6ff; color: #1e40af; }
.status-pending { background: #f5f5f5; color: #525252; }
.backtest-meta {
  display: flex; gap: 16px;
  font-size: 0.75rem; color: #a3a3a3;
  margin-bottom: 12px;
}
.note-input {
  width: 100%; height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(99,102,241,0.35);
  border-radius: 8px;
  background: #fff;
  font-size: 0.78rem; color: #171717;
  outline: none;
}
.note-input:focus {
  border-color: rgba(99,102,241,0.6);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.08);
}
.note-text {
  display: inline-block;
  font-size: 0.78rem; color: #4f46e5; font-weight: 600;
  background: #eef2ff; padding: 4px 10px; border-radius: 8px;
  cursor: pointer; transition: all 0.2s;
}
.note-text:hover { background: #e0e7ff; }
.note-add {
  padding: 4px 10px;
  background: transparent; border: 1px dashed rgba(0,0,0,0.15);
  border-radius: 8px;
  font-size: 0.75rem; font-weight: 600; color: #737373;
  cursor: pointer; transition: all 0.2s;
}
.note-add:hover {
  border-color: rgba(99,102,241,0.4); color: #4f46e5;
}
.backtest-metrics { display: flex; gap: 20px; }
.metric { display: flex; flex-direction: column; gap: 2px; }
.metric-label { font-size: 0.68rem; color: #a3a3a3; }
.metric-val { font-size: 0.9rem; font-weight: 600; color: #171717; }
.metric-val.up { color: #166534; }
.metric-val.down { color: #991b1b; }

/* Empty */
.empty-state { text-align: center; padding: 60px 0; }
.empty-icon { color: #e5e5e5; margin-bottom: 16px; }
.empty-text { font-size: 0.9rem; font-weight: 600; color: #525252; margin: 0 0 6px; }
.empty-sub { font-size: 0.78rem; color: #a3a3a3; margin: 0; }

@media (min-width: 640px) {
  .config-form { grid-template-columns: 1.2fr 1fr; }
}

@media (min-width: 768px) {
  .backtest-content { padding: 24px 32px 40px; }
}
</style>

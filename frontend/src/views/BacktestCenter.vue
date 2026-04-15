<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { backtestApi, type Backtest } from '@/api/backtest'
import { strategyApi, type Strategy } from '@/api/strategy'
import { strategyFlowApi, type StrategyFlow } from '@/api/strategyFlow'
import { stockPickerApi, type StockPool } from '@/api/stockPicker'
import SparklineChart from '@/components/SparklineChart.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

const { t } = useI18n()
const route = useRoute()

const backtests = ref<Backtest[]>([])
const strategies = ref<Strategy[]>([])
const flows = ref<StrategyFlow[]>([])
const stockPools = ref<StockPool[]>([])
const loading = ref(false)
const toast = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

const showCreate = ref(false)
const newBacktest = ref({
  backtest_id: '',
  strategy_id: '',
  symbols: '000001',
  start_date: '2024-01-01',
  end_date: '2024-03-01',
  initial_cash: 100000,
})
const selectedPoolId = ref('')

const summary = computed(() => {
  const total = backtests.value.length
  const success = backtests.value.filter(b => b.status === 'success').length
  const pending = backtests.value.filter(b => b.status === 'pending').length
  const avgReturn =
    total > 0
      ? backtests.value.reduce((sum, b) => sum + (b.metrics?.total_return || 0), 0) / total
      : 0
  return { total, success, pending, avgReturn }
})

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

async function loadBacktests() {
  backtests.value = await backtestApi.list()
}

async function loadStrategies() {
  const [s, f] = await Promise.all([
    strategyApi.list('?strategy_type=trade'),
    strategyFlowApi.list(),
  ])
  strategies.value = s
  flows.value = f
  const allIds = [...s.map(x => x.strategy_id), ...f.map(x => x.flow_id)]
  if (allIds.length && !newBacktest.value.strategy_id) {
    newBacktest.value.strategy_id = allIds[0]!
  }
}

function isFlow(id: string) {
  return flows.value.some(f => f.flow_id === id)
}

async function loadStockPools() {
  try {
    stockPools.value = await stockPickerApi.listPools()
  } catch {
    // ignore
  }
}

function importFromPool(poolId: string) {
  const pool = stockPools.value.find(p => p.pool_id === poolId)
  if (pool && pool.items.length) {
    newBacktest.value.symbols = pool.items.map(i => i.symbol).join(',')
  }
}

async function createBacktest() {
  if (!newBacktest.value.backtest_id || !newBacktest.value.strategy_id) {
    showToast(t('backtest.fillRequired'))
    return
  }
  loading.value = true
  try {
    await backtestApi.create({
      backtest_id: newBacktest.value.backtest_id,
      strategy_id: newBacktest.value.strategy_id,
      start_date: newBacktest.value.start_date,
      end_date: newBacktest.value.end_date,
      initial_cash: newBacktest.value.initial_cash,
    })
    showToast(t('backtest.createSuccess'))
    showCreate.value = false
    newBacktest.value.backtest_id = ''
    await loadBacktests()
  } catch (e: any) {
    showToast(t('backtest.createError') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

async function runBacktest(bt: Backtest) {
  loading.value = true
  try {
    await backtestApi.run(bt.backtest_id, {
      symbols: newBacktest.value.symbols.split(',').map(s => s.trim()),
      start_date: bt.start_date,
      end_date: bt.end_date,
      initial_cash: bt.initial_cash,
    })
    showToast(t('backtest.runSuccess'))
    await loadBacktests()
  } catch (e: any) {
    showToast(t('backtest.runError') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

function formatMetrics(metrics: Record<string, any> | null) {
  if (!metrics) return '-'
  const items = []
  if (metrics.total_return !== undefined)
    items.push(`${t('backtest.totalReturn')}: ${(metrics.total_return * 100).toFixed(2)}%`)
  if (metrics.sharpe_ratio !== undefined)
    items.push(`${t('backtest.sharpeRatio')}: ${metrics.sharpe_ratio.toFixed(2)}`)
  if (metrics.max_drawdown !== undefined)
    items.push(`${t('backtest.maxDrawdown')}: ${(metrics.max_drawdown * 100).toFixed(2)}%`)
  return items.join(' | ') || JSON.stringify(metrics)
}

function statusClass(status: string) {
  return `status-badge--${status}`
}

function returnClass(val: number | undefined) {
  if (val === undefined || val === null) return ''
  return val >= 0 ? 'text-profit' : 'text-loss'
}

onMounted(() => {
  loadBacktests()
  loadStrategies()
  loadStockPools()
  const poolId = route.query.poolId as string | undefined
  if (poolId) {
    showCreate.value = true
    selectedPoolId.value = poolId
    // Delay import until pools are loaded
    setTimeout(() => importFromPool(poolId), 300)
  }
})
</script>

<template>
  <div class="page">
    <!-- Summary Cards -->
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-label">{{ t('common.total') }}</div>
        <div class="summary-value">{{ summary.total }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ t('common.success') }}</div>
        <div class="summary-value" style="color: var(--success)">{{ summary.success }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ t('common.pending') }}</div>
        <div class="summary-value" style="color: var(--warning)">{{ summary.pending }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ t('backtest.totalReturn') }}</div>
        <div class="summary-value" :class="returnClass(summary.avgReturn)">
          {{ (summary.avgReturn * 100).toFixed(2) }}%
        </div>
      </div>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>

    <!-- Create form -->
    <div class="form-section">
      <button v-if="!showCreate" class="btn btn--primary" @click="showCreate = true">
        + {{ t('backtest.new') }}
      </button>
      <div v-else class="card form-card">
        <div class="form-grid">
          <div class="form-group">
            <label>{{ t('backtest.backtestId') }}</label>
            <input v-model="newBacktest.backtest_id" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>{{ t('common.strategy') }}</label>
            <select v-model="newBacktest.strategy_id" class="form-input">
              <optgroup :label="t('strategy.tabs.trade')">
                <option v-for="s in strategies" :key="s.strategy_id" :value="s.strategy_id">
                  {{ s.name }}
                </option>
              </optgroup>
              <optgroup :label="t('strategy.tabs.flow')">
                <option v-for="f in flows" :key="f.flow_id" :value="f.flow_id">
                  {{ f.name }}
                </option>
              </optgroup>
            </select>
            <div v-if="isFlow(newBacktest.strategy_id)" class="flow-hint">
              {{ t('flow.runHint') }}
            </div>
          </div>
          <div class="form-group">
            <label>{{ t('common.symbols') }}</label>
            <input v-model="newBacktest.symbols" type="text" class="form-input" />
            <select v-model="selectedPoolId" class="form-input pool-select" @change="importFromPool(selectedPoolId)">
              <option value="">{{ t('stockPicker.importFromPool') }}</option>
              <option v-for="pool in stockPools" :key="pool.pool_id" :value="pool.pool_id">
                {{ pool.name }} ({{ pool.items.length }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ t('common.startDate') }}</label>
            <input v-model="newBacktest.start_date" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>{{ t('common.endDate') }}</label>
            <input v-model="newBacktest.end_date" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>{{ t('common.initialCash') }}</label>
            <input v-model.number="newBacktest.initial_cash" type="number" class="form-input" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn--secondary" @click="showCreate = false">{{ t('common.cancel') }}</button>
          <button class="btn btn--primary" :disabled="loading" @click="createBacktest">
            {{ t('common.create') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="card table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('common.id') }}</th>
            <th>{{ t('common.strategy') }}</th>
            <th>{{ t('backtest.dateRange') }}</th>
            <th class="col-numeric">{{ t('common.initialCash') }}</th>
            <th class="col-numeric">{{ t('backtest.totalReturn') }}</th>
            <th class="col-numeric">{{ t('backtest.sharpeRatio') }}</th>
            <th class="col-numeric">{{ t('backtest.maxDrawdown') }}</th>
            <th class="col-numeric">{{ t('common.status') }}</th>
            <th class="col-chart">{{ t('common.metrics') }}</th>
            <th class="col-actions">{{ t('common.operations') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bt in backtests" :key="bt.backtest_id">
            <td class="mono">{{ bt.backtest_id }}</td>
            <td class="mono">{{ bt.strategy_id }}</td>
            <td>{{ bt.start_date }} ~ {{ bt.end_date }}</td>
            <td class="col-numeric">{{ bt.initial_cash.toLocaleString() }}</td>
            <td class="col-numeric" :class="returnClass(bt.metrics?.total_return)">
              {{ bt.metrics?.total_return !== undefined ? (bt.metrics.total_return * 100).toFixed(2) + '%' : '-' }}
            </td>
            <td class="col-numeric">
              {{ bt.metrics?.sharpe_ratio !== undefined ? bt.metrics.sharpe_ratio.toFixed(2) : '-' }}
            </td>
            <td class="col-numeric" :class="returnClass(bt.metrics?.max_drawdown)">
              {{ bt.metrics?.max_drawdown !== undefined ? (bt.metrics.max_drawdown * 100).toFixed(2) + '%' : '-' }}
            </td>
            <td>
              <span :class="['status-badge', statusClass(bt.status)]">{{ t(`status.${bt.status}`) }}</span>
            </td>
            <td class="col-chart">
              <SparklineChart :total-return="bt.metrics?.total_return" />
            </td>
            <td class="col-actions">
              <button
                v-if="bt.status === 'pending' || bt.status === 'failed'"
                class="btn btn--primary btn--sm"
                :disabled="loading"
                @click="runBacktest(bt)"
              >
                {{ t('common.run') }}
              </button>
            </td>
          </tr>
          <tr v-if="!backtests.length">
            <td colspan="10" class="empty-cell">{{ t('common.empty') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <LoadingOverlay :visible="loading" :text="t('common.loading')" />
  </div>
</template>

<style scoped>
.page {
  padding: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.summary-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.summary-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.summary-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.toast {
  margin-bottom: var(--space-lg);
  padding: var(--space-sm) var(--space-lg);
  background: var(--success-subtle);
  color: #047857;
  font-size: 0.9rem;
  font-weight: 500;
  border-radius: var(--radius-md);
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.form-section {
  margin-bottom: var(--space-xl);
}

.form-card {
  padding: var(--space-2xl);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.form-group label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-subtle);
}

.table-card {
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.9rem;
}

.data-table th,
.data-table td {
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.data-table th {
  background: var(--bg-surface);
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.data-table tbody tr:hover {
  background: var(--bg-surface-hover);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.col-numeric {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-actions {
  text-align: right;
}

.col-chart {
  width: 120px;
  min-width: 120px;
}

.mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
}

.empty-cell {
  text-align: center;
  color: var(--text-muted);
  padding: var(--space-3xl);
}

.text-profit {
  color: var(--profit);
  font-weight: 500;
}

.text-loss {
  color: var(--loss);
  font-weight: 500;
}

.pool-select {
  margin-top: var(--space-sm);
  font-size: 0.85rem;
}

.flow-hint {
  margin-top: var(--space-sm);
  font-size: 0.8rem;
  color: var(--accent);
}
</style>

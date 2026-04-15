<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { paperTradingApi, type PaperTradingSession } from '@/api/paperTrading'
import { strategyApi, type Strategy } from '@/api/strategy'
import { syncApi, type DiffItem, type PaperSignal, type DailyReport } from '@/api/sync'
import { accountSettingsApi, type AccountSettings } from '@/api/accountSettings'

const { t } = useI18n()

const sessions = ref<PaperTradingSession[]>([])
const strategies = ref<Strategy[]>([])
const loading = ref(false)
const toast = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

const showCreate = ref(false)
const newSession = ref({
  session_id: '',
  strategy_id: '',
  symbols: '000001',
  start_date: '2024-01-01',
  end_date: '2024-03-01',
  initial_cash: 100000,
})

const summary = computed(() => {
  const total = sessions.value.length
  const running = sessions.value.filter(s => s.status === 'running').length
  const idle = sessions.value.filter(s => s.status === 'idle' || s.status === 'error').length
  return { total, running, idle }
})

// Sync / Diff state
const diffResult = ref<DiffItem[]>([])
const pendingSignals = ref<PaperSignal[]>([])
const selectedStrategyId = ref('')
const showSyncModal = ref(false)
const syncForm = ref({
  signal_id: '',
  strategy_id: '',
  symbol: '',
  side: 'Buy',
  quantity: 0,
  price: 0,
  commission: 0,
  stamp_tax: 0,
  transfer_fee: 0,
  total_cost: 0,
  sync_status: 'synced',
  remark: '',
})

// Account settings
const accountSettings = ref<AccountSettings | null>(null)
const showSettingsModal = ref(false)
const settingsForm = ref({
  commission_rate: 0.00025,
  min_commission: 5,
  stamp_tax_rate: 0.0005,
  transfer_fee_rate: 0.00002,
  is_sh_market: true,
})

// Daily report
const dailyReport = ref<DailyReport | null>(null)
const showReportModal = ref(false)
const reportDate = ref('')

// Batch sync
const showBatchModal = ref(false)
const batchSignals = ref<PaperSignal[]>([])
const batchForm = ref<{ signal_id: string; actual_price: number; actual_qty: number; sync_status: string; checked: boolean }[]>([])

// CSV import
const csvFileInput = ref<HTMLInputElement | null>(null)

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

async function loadSessions() {
  sessions.value = await paperTradingApi.list()
}

async function loadStrategies() {
  strategies.value = await strategyApi.list()
  if (strategies.value.length && !newSession.value.strategy_id) {
    newSession.value.strategy_id = strategies.value[0]!.strategy_id
  }
  if (strategies.value.length && !selectedStrategyId.value) {
    selectedStrategyId.value = strategies.value[0]!.strategy_id
    await loadDiff()
  }
}

async function loadAccountSettings() {
  try {
    accountSettings.value = await accountSettingsApi.get()
    if (accountSettings.value) {
      settingsForm.value = { ...accountSettings.value }
    }
  } catch {
    // ignore
  }
}

async function createSession() {
  if (!newSession.value.session_id || !newSession.value.strategy_id) {
    showToast(t('paperTrading.fillRequired'))
    return
  }
  loading.value = true
  try {
    await paperTradingApi.create({
      session_id: newSession.value.session_id,
      strategy_id: newSession.value.strategy_id,
      symbols: newSession.value.symbols.split(',').map(s => s.trim()),
      start_date: newSession.value.start_date,
      end_date: newSession.value.end_date,
      initial_cash: newSession.value.initial_cash,
    })
    showToast(t('paperTrading.createSuccess'))
    showCreate.value = false
    newSession.value.session_id = ''
    await loadSessions()
  } catch (e: any) {
    showToast(t('paperTrading.createError') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

async function runSession(s: PaperTradingSession) {
  loading.value = true
  try {
    await paperTradingApi.run(s.session_id)
    showToast(t('paperTrading.runSuccess'))
    await loadSessions()
    await loadDiff()
  } catch (e: any) {
    showToast(t('paperTrading.runError') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

async function stopSession(s: PaperTradingSession) {
  loading.value = true
  try {
    await paperTradingApi.stop(s.session_id)
    showToast(t('paperTrading.stopSuccess'))
    await loadSessions()
  } catch (e: any) {
    showToast(t('paperTrading.stopError') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

async function deleteSession(s: PaperTradingSession) {
  if (!confirm(t('common.confirmDelete'))) return
  try {
    await paperTradingApi.remove(s.session_id)
    await loadSessions()
  } catch (e: any) {
    showToast(t('common.error') + ': ' + e.message)
  }
}

function parseLogs(logs: string | null) {
  if (!logs) return null
  try {
    return JSON.parse(logs)
  } catch {
    return { raw: logs }
  }
}

function statusClass(status: string) {
  return `status-badge--${status}`
}

// Diff & Sync
async function loadDiff() {
  if (!selectedStrategyId.value) return
  try {
    const diff = await syncApi.getDiff(selectedStrategyId.value)
    diffResult.value = diff.diffs
    const signals = await syncApi.listSignals(selectedStrategyId.value, 'pending')
    pendingSignals.value = signals
  } catch (e: any) {
    showToast('Diff 加载失败: ' + e.message)
  }
}

function calculateFeesLocal(side: string, quantity: number, price: number) {
  const s = accountSettings.value
  if (!s) return { commission: 0, stamp_tax: 0, transfer_fee: 0 }
  const amount = quantity * price
  const commission = Math.max(amount * s.commission_rate, s.min_commission)
  const transferFee = amount * s.transfer_fee_rate
  const stampTax = side.toLowerCase() === 'sell' ? amount * s.stamp_tax_rate : 0
  return {
    commission: Math.round(commission * 100) / 100,
    stamp_tax: Math.round(stampTax * 100) / 100,
    transfer_fee: Math.round(transferFee * 100) / 100,
  }
}

function openSyncModal(signal: PaperSignal) {
  const fees = calculateFeesLocal(signal.side, signal.quantity, signal.price || 0)
  const totalCost = signal.quantity * (signal.price || 0) + fees.commission + fees.stamp_tax + fees.transfer_fee
  syncForm.value = {
    signal_id: signal.signal_id,
    strategy_id: signal.strategy_id,
    symbol: signal.symbol,
    side: signal.side,
    quantity: signal.quantity,
    price: signal.price || 0,
    commission: fees.commission,
    stamp_tax: fees.stamp_tax,
    transfer_fee: fees.transfer_fee,
    total_cost: Math.round(totalCost * 100) / 100,
    sync_status: 'synced',
    remark: '',
  }
  showSyncModal.value = true
}

function closeSyncModal() {
  showSyncModal.value = false
}

function recalcTotal() {
  const qty = syncForm.value.quantity
  const price = syncForm.value.price
  const fees = calculateFeesLocal(syncForm.value.side, qty, price)
  syncForm.value.commission = fees.commission
  syncForm.value.stamp_tax = fees.stamp_tax
  syncForm.value.transfer_fee = fees.transfer_fee
  syncForm.value.total_cost = Math.round((qty * price + fees.commission + fees.stamp_tax + fees.transfer_fee) * 100) / 100
}

async function submitSync() {
  loading.value = true
  try {
    await syncApi.createTrade({
      signal_id: syncForm.value.signal_id,
      strategy_id: syncForm.value.strategy_id,
      symbol: syncForm.value.symbol,
      side: syncForm.value.side,
      quantity: syncForm.value.quantity,
      price: syncForm.value.price,
      commission: syncForm.value.commission,
      stamp_tax: syncForm.value.stamp_tax,
      transfer_fee: syncForm.value.transfer_fee,
      total_cost: syncForm.value.total_cost,
      sync_status: syncForm.value.sync_status,
      remark: syncForm.value.remark || null,
    })
    showToast('同步成功')
    closeSyncModal()
    await loadDiff()
  } catch (e: any) {
    showToast('同步失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function diffStatusClass(status: string) {
  if (status === 'match') return 'diff-match'
  if (status === 'extra_real') return 'diff-extra'
  return 'diff-mismatch'
}

// Account settings modal
function openSettingsModal() {
  showSettingsModal.value = true
}

function closeSettingsModal() {
  showSettingsModal.value = false
}

async function saveSettings() {
  loading.value = true
  try {
    await accountSettingsApi.update({ ...settingsForm.value })
    showToast('账户设置已保存')
    await loadAccountSettings()
    closeSettingsModal()
  } catch (e: any) {
    showToast('保存失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

// Daily report
async function loadDailyReport() {
  if (!selectedStrategyId.value) return
  try {
    dailyReport.value = await syncApi.getDailyReport(selectedStrategyId.value, reportDate.value || undefined)
    showReportModal.value = true
  } catch (e: any) {
    showToast('对账单加载失败: ' + e.message)
  }
}

function closeReportModal() {
  showReportModal.value = false
}

// Batch sync
async function openBatchModal() {
  if (!selectedStrategyId.value) {
    showToast('请先选择策略')
    return
  }
  try {
    const signals = await syncApi.listSignals(selectedStrategyId.value, 'pending')
    batchSignals.value = signals
    batchForm.value = signals.map(s => ({
      signal_id: s.signal_id,
      actual_price: s.price || 0,
      actual_qty: s.quantity,
      sync_status: 'synced',
      checked: false,
    }))
    showBatchModal.value = true
  } catch (e: any) {
    showToast('加载信号失败: ' + e.message)
  }
}

function closeBatchModal() {
  showBatchModal.value = false
}

async function submitBatchSync() {
  const items = batchForm.value
    .filter((b, i) => b.checked && batchSignals.value[i])
    .map((b, i) => {
      const sig = batchSignals.value[i]!
      return {
        signal_id: sig.signal_id,
        actual_price: b.actual_price,
        actual_qty: b.actual_qty,
        sync_status: b.sync_status,
        remark: '',
      }
    })
  if (!items.length) {
    showToast('请至少勾选一条信号')
    return
  }
  loading.value = true
  try {
    const res = await syncApi.batchSync(items)
    showToast(`批量同步完成，成功 ${res.created} 条`)
    closeBatchModal()
    await loadDiff()
  } catch (e: any) {
    showToast('批量同步失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

// CSV import
function triggerCsvUpload() {
  csvFileInput.value?.click()
}

async function handleCsvUpload(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  loading.value = true
  try {
    const res = await syncApi.importCsv(file)
    showToast(`CSV 导入完成，成功 ${res.created} 条`)
    await loadDiff()
  } catch (err: any) {
    showToast('CSV 导入失败: ' + err.message)
  } finally {
    loading.value = false
    if (csvFileInput.value) csvFileInput.value.value = ''
  }
}

onMounted(() => {
  loadSessions()
  loadStrategies()
  loadAccountSettings()
  const today = new Date()
  reportDate.value = today.toISOString().split('T')[0] || ''
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
        <div class="summary-label">{{ t('status.running') }}</div>
        <div class="summary-value" style="color: var(--warning)">{{ summary.running }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ t('status.idle') }}</div>
        <div class="summary-value" style="color: var(--info)">{{ summary.idle }}</div>
      </div>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>

    <!-- Diff Dashboard -->
    <div class="card diff-card">
      <div class="diff-header">
        <h3 class="diff-title">持仓对比看板</h3>
        <div class="diff-actions">
          <select v-model="selectedStrategyId" class="form-input" @change="loadDiff">
            <option v-for="s in strategies" :key="s.strategy_id" :value="s.strategy_id">
              {{ s.name }} ({{ s.strategy_id }})
            </option>
          </select>
          <button class="btn btn--secondary btn--sm" @click="openBatchModal">批量补录</button>
          <button class="btn btn--secondary btn--sm" @click="loadDailyReport">对账单</button>
          <button class="btn btn--ghost btn--sm" @click="openSettingsModal">账户设置</button>
        </div>
      </div>

      <div v-if="diffResult.length" class="diff-body">
        <table class="diff-table">
          <thead>
            <tr>
              <th>标的</th>
              <th>状态</th>
              <th>模拟数量</th>
              <th>真实数量</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in diffResult" :key="d.symbol">
              <td class="mono">{{ d.symbol }}</td>
              <td>
                <span class="diff-badge" :class="diffStatusClass(d.status)">
                  {{ d.status === 'match' ? '一致' : d.status === 'extra_real' ? '额外持仓' : '待同步' }}
                </span>
              </td>
              <td class="mono">{{ d.signal_qty }}</td>
              <td class="mono">{{ d.real_qty }}</td>
              <td>{{ d.message }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="pendingSignals.length" class="pending-section">
          <h4 class="pending-title">待同步信号</h4>
          <div class="pending-list">
            <div v-for="sig in pendingSignals" :key="sig.signal_id" class="pending-item">
              <div class="pending-info">
                <span class="mono">{{ sig.symbol }}</span>
                <span class="pending-side">{{ sig.side }}</span>
                <span class="mono">{{ sig.quantity }} @ {{ sig.price ?? '-' }}</span>
              </div>
              <button class="btn btn--primary btn--sm" @click="openSyncModal(sig)">同步</button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="diff-empty">暂无对比数据，请选择策略并运行模拟盘</div>
    </div>

    <!-- Toolbar -->
    <div class="form-section toolbar">
      <div class="toolbar-left">
        <button v-if="!showCreate" class="btn btn--primary" @click="showCreate = true">
          + {{ t('paperTrading.newSession') }}
        </button>
      </div>
      <div class="toolbar-right">
        <input ref="csvFileInput" type="file" accept=".csv" style="display: none" @change="handleCsvUpload" />
        <button class="btn btn--secondary" @click="triggerCsvUpload">导入 CSV 交割单</button>
      </div>
    </div>

    <!-- Create form -->
    <div v-if="showCreate" class="card form-card" style="margin-bottom: var(--space-xl)">
      <div class="form-grid">
        <div class="form-group">
          <label>{{ t('paperTrading.sessionId') }}</label>
          <input v-model="newSession.session_id" type="text" class="form-input" />
        </div>
        <div class="form-group">
          <label>{{ t('common.strategy') }}</label>
          <select v-model="newSession.strategy_id" class="form-input">
            <option v-for="s in strategies" :key="s.strategy_id" :value="s.strategy_id">
              {{ s.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ t('common.symbols') }}</label>
          <input v-model="newSession.symbols" type="text" class="form-input" />
        </div>
        <div class="form-group">
          <label>{{ t('common.startDate') }}</label>
          <input v-model="newSession.start_date" type="text" class="form-input" />
        </div>
        <div class="form-group">
          <label>{{ t('common.endDate') }}</label>
          <input v-model="newSession.end_date" type="text" class="form-input" />
        </div>
        <div class="form-group">
          <label>{{ t('common.initialCash') }}</label>
          <input v-model.number="newSession.initial_cash" type="number" class="form-input" />
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn--secondary" @click="showCreate = false">{{ t('common.cancel') }}</button>
        <button class="btn btn--primary" :disabled="loading" @click="createSession">
          {{ t('common.create') }}
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="card table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('common.id') }}</th>
            <th>{{ t('common.strategy') }}</th>
            <th>{{ t('common.symbols') }}</th>
            <th>{{ t('backtest.dateRange') }}</th>
            <th>{{ t('common.status') }}</th>
            <th>{{ t('common.logs') }}</th>
            <th class="col-actions">{{ t('common.operations') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sessions" :key="s.session_id">
            <td class="mono">{{ s.session_id }}</td>
            <td class="mono">{{ s.strategy_id }}</td>
            <td>{{ Array.isArray(s.symbols) ? s.symbols.join(', ') : s.symbols }}</td>
            <td>{{ s.start_date || '-' }} ~ {{ s.end_date || '-' }}</td>
            <td>
              <span :class="['status-badge', statusClass(s.status)]">{{ t(`status.${s.status}`) }}</span>
            </td>
            <td class="logs">
              <span v-if="parseLogs(s.logs)?.signals_created !== undefined">
                {{ t('paperTrading.signals') }}: {{ parseLogs(s.logs).signals_created }}
              </span>
              <span v-else-if="parseLogs(s.logs)?.raw">
                {{ parseLogs(s.logs).raw.slice(0, 40) }}
              </span>
              <span v-else>-</span>
            </td>
            <td class="col-actions">
              <div class="action-group">
                <button
                  v-if="s.status === 'idle' || s.status === 'error'"
                  class="btn btn--primary btn--sm"
                  :disabled="loading"
                  @click="runSession(s)"
                >
                  {{ t('common.run') }}
                </button>
                <button
                  v-if="s.status === 'running'"
                  class="btn btn--secondary btn--sm"
                  :disabled="loading"
                  @click="stopSession(s)"
                >
                  {{ t('common.stop') }}
                </button>
                <button
                  class="btn btn--danger btn--sm"
                  :disabled="loading"
                  @click="deleteSession(s)"
                >
                  {{ t('common.delete') }}
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!sessions.length">
            <td colspan="7" class="empty-cell">{{ t('common.empty') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Sync Modal -->
    <div v-if="showSyncModal" class="modal-overlay" @click.self="closeSyncModal">
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">一键同步真实成交</h3>
          <button class="modal-close" @click="closeSyncModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid-2">
            <div class="form-group">
              <label>标的</label>
              <input v-model="syncForm.symbol" type="text" class="form-input" disabled />
            </div>
            <div class="form-group">
              <label>方向</label>
              <input v-model="syncForm.side" type="text" class="form-input" disabled />
            </div>
            <div class="form-group">
              <label>成交数量</label>
              <input v-model.number="syncForm.quantity" type="number" class="form-input" @input="recalcTotal" />
            </div>
            <div class="form-group">
              <label>成交价格</label>
              <input v-model.number="syncForm.price" type="number" class="form-input" @input="recalcTotal" />
            </div>
            <div class="form-group">
              <label>佣金</label>
              <input v-model.number="syncForm.commission" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>印花税</label>
              <input v-model.number="syncForm.stamp_tax" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>过户费</label>
              <input v-model.number="syncForm.transfer_fee" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>总成本</label>
              <input v-model.number="syncForm.total_cost" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>同步状态</label>
              <select v-model="syncForm.sync_status" class="form-input">
                <option value="synced">全部成交</option>
                <option value="partial">部分成交</option>
                <option value="cancelled">已撤单</option>
              </select>
            </div>
            <div class="form-group">
              <label>备注</label>
              <input v-model="syncForm.remark" type="text" class="form-input" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--secondary" @click="closeSyncModal">{{ t('common.cancel') }}</button>
          <button class="btn btn--primary" :disabled="loading" @click="submitSync">确认同步</button>
        </div>
      </div>
    </div>

    <!-- Account Settings Modal -->
    <div v-if="showSettingsModal" class="modal-overlay" @click.self="closeSettingsModal">
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">账户设置（费用计算）</h3>
          <button class="modal-close" @click="closeSettingsModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid-2">
            <div class="form-group">
              <label>佣金率</label>
              <input v-model.number="settingsForm.commission_rate" type="number" step="0.00001" class="form-input" />
            </div>
            <div class="form-group">
              <label>最低佣金（元）</label>
              <input v-model.number="settingsForm.min_commission" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>印花税率</label>
              <input v-model.number="settingsForm.stamp_tax_rate" type="number" step="0.00001" class="form-input" />
            </div>
            <div class="form-group">
              <label>过户费率</label>
              <input v-model.number="settingsForm.transfer_fee_rate" type="number" step="0.00001" class="form-input" />
            </div>
            <div class="form-group" style="grid-column: 1 / -1">
              <label>
                <input v-model="settingsForm.is_sh_market" type="checkbox" />
                沪市股票（收取过户费）
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--secondary" @click="closeSettingsModal">取消</button>
          <button class="btn btn--primary" :disabled="loading" @click="saveSettings">保存</button>
        </div>
      </div>
    </div>

    <!-- Daily Report Modal -->
    <div v-if="showReportModal" class="modal-overlay" @click.self="closeReportModal">
      <div class="modal modal--wide">
        <div class="modal-header">
          <h3 class="modal-title">对账单草稿</h3>
          <button class="modal-close" @click="closeReportModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group" style="margin-bottom: var(--space-lg)">
            <label>日期</label>
            <input v-model="reportDate" type="date" class="form-input" style="width: 200px" @change="loadDailyReport" />
          </div>
          <div v-if="dailyReport" class="report-body">
            <p class="report-summary">{{ dailyReport.message }}</p>
            <div class="report-grid">
              <div class="report-item">
                <div class="report-label">模拟信号数</div>
                <div class="report-value">{{ dailyReport.simulated_signals_count }}</div>
              </div>
              <div class="report-item">
                <div class="report-label">待同步信号</div>
                <div class="report-value">{{ dailyReport.pending_signals_count }}</div>
              </div>
              <div class="report-item">
                <div class="report-label">已同步信号</div>
                <div class="report-value">{{ dailyReport.synced_signals_count }}</div>
              </div>
              <div class="report-item">
                <div class="report-label">真实交易数</div>
                <div class="report-value">{{ dailyReport.real_trades_count }}</div>
              </div>
              <div class="report-item">
                <div class="report-label">真实盈亏</div>
                <div class="report-value" :class="dailyReport.real_pnl >= 0 ? 'text-profit' : 'text-loss'">{{ dailyReport.real_pnl.toFixed(2) }}</div>
              </div>
            </div>

            <h4 class="report-section-title">持仓差异</h4>
            <table v-if="dailyReport.unsynced_list.length" class="diff-table">
              <thead>
                <tr><th>标的</th><th>状态</th><th>模拟</th><th>真实</th><th>说明</th></tr>
              </thead>
              <tbody>
                <tr v-for="u in dailyReport.unsynced_list" :key="u.symbol">
                  <td class="mono">{{ u.symbol }}</td>
                  <td><span class="diff-badge" :class="diffStatusClass(u.status)">{{ u.status === 'match' ? '一致' : u.status === 'extra_real' ? '额外' : '待同步' }}</span></td>
                  <td class="mono">{{ u.signal_qty }}</td>
                  <td class="mono">{{ u.real_qty }}</td>
                  <td>{{ u.message }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="report-empty">无持仓差异</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--secondary" @click="closeReportModal">关闭</button>
        </div>
      </div>
    </div>

    <!-- Batch Sync Modal -->
    <div v-if="showBatchModal" class="modal-overlay" @click.self="closeBatchModal">
      <div class="modal modal--wide">
        <div class="modal-header">
          <h3 class="modal-title">批量补录模式</h3>
          <button class="modal-close" @click="closeBatchModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="batchSignals.length" class="batch-list">
            <div v-for="(sig, idx) in batchSignals" :key="sig.signal_id" class="batch-item">
              <input v-model="batchForm[idx]!.checked" type="checkbox" />
              <span class="mono" style="width: 80px">{{ sig.symbol }}</span>
              <span style="width: 50px">{{ sig.side }}</span>
              <span class="mono" style="width: 80px">{{ sig.quantity }}</span>
              <span style="width: 120px">
                <label class="batch-label">实际价</label>
                <input v-model.number="batchForm[idx]!.actual_price" type="number" class="form-input batch-input" />
              </span>
              <span style="width: 100px">
                <label class="batch-label">实际量</label>
                <input v-model.number="batchForm[idx]!.actual_qty" type="number" class="form-input batch-input" />
              </span>
              <span style="width: 120px">
                <label class="batch-label">状态</label>
                <select v-model="batchForm[idx]!.sync_status" class="form-input batch-input">
                  <option value="synced">全部成交</option>
                  <option value="partial">部分成交</option>
                  <option value="cancelled">已撤单</option>
                </select>
              </span>
            </div>
          </div>
          <div v-else class="diff-empty">该策略下没有待同步信号</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--secondary" @click="closeBatchModal">取消</button>
          <button class="btn btn--primary" :disabled="loading" @click="submitBatchSync">提交批量同步</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: var(--space-md);
}

.diff-card {
  padding: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.diff-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
  gap: var(--space-md);
}

.diff-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.diff-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.diff-actions .form-input {
  width: 220px;
}

.diff-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.9rem;
}

.diff-table th,
.diff-table td {
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.diff-table th {
  background: var(--bg-surface);
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.diff-table tbody tr:last-child td {
  border-bottom: none;
}

.diff-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 500;
}

.diff-match {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

.diff-mismatch {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.diff-extra {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.diff-empty {
  color: var(--text-muted);
  font-size: 0.9rem;
  padding: var(--space-lg) 0;
}

.pending-section {
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-subtle);
}

.pending-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.pending-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.pending-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.pending-info {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.pending-side {
  font-weight: 500;
  color: var(--accent);
}

.form-card {
  padding: var(--space-2xl);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
}

.form-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
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

.col-actions {
  text-align: right;
}

.action-group {
  display: inline-flex;
  gap: var(--space-sm);
}

.mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
}

.logs {
  font-size: 0.85rem;
  color: var(--text-secondary);
  max-width: 240px;
}

.empty-cell {
  text-align: center;
  color: var(--text-muted);
  padding: var(--space-3xl);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  width: 520px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
  box-shadow: var(--shadow-lg);
}

.modal--wide {
  width: 840px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-2xl);
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  color: var(--text-muted);
  cursor: pointer;
}

.modal-body {
  padding: var(--space-2xl);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-2xl);
  border-top: 1px solid var(--border-subtle);
}

.report-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.report-summary {
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--space-lg);
}

.report-item {
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-lg);
}

.report-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.report-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.report-section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: var(--space-md);
}

.report-empty {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.text-profit {
  color: var(--profit);
}

.text-loss {
  color: var(--loss);
}

.batch-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-height: 60vh;
  overflow: auto;
}

.batch-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
}

.batch-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  display: block;
  margin-bottom: 2px;
}

.batch-input {
  padding: 6px 8px;
  font-size: 0.85rem;
}
</style>

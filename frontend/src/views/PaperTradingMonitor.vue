<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { paperTradingApi, type PaperTradingSession } from '@/api/paperTrading'
import { strategyApi, type Strategy } from '@/api/strategy'

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

onMounted(() => {
  loadSessions()
  loadStrategies()
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

    <!-- Create form -->
    <div class="form-section">
      <button v-if="!showCreate" class="btn btn--primary" @click="showCreate = true">
        + {{ t('paperTrading.newSession') }}
      </button>
      <div v-else class="card form-card">
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
</style>

<script setup lang="ts">
import { ref, onMounted, computed, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { stockPickerApi, type StockPool, type PickerRun } from '@/api/stockPicker'
import { strategyApi, type Strategy } from '@/api/strategy'
import { useRouter } from 'vue-router'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

const { t } = useI18n()
const router = useRouter()
const extensions = [python(), oneDark]

const pickers = ref<Strategy[]>([])
const currentPicker = ref<Strategy | null>(null)
const code = ref('')
const name = ref('')
const pickerId = ref('')
const isEditing = ref(false)
const showEditor = ref(false)
const loading = ref(false)
const running = ref(false)
const toast = ref('')
const toastType = ref<'success' | 'error'>('success')

const pools = ref<StockPool[]>([])
const runs = ref<PickerRun[]>([])
const showSettings = ref(false)

const builtinPickerId = 'builtin_weekly_picker'

const showOverlay = computed(() => loading.value || running.value)

let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toast.value = msg
  toastType.value = type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

async function loadPickers() {
  pickers.value = await strategyApi.list('?strategy_type=picker')
}

async function loadPools() {
  try {
    pools.value = await stockPickerApi.listPools()
  } catch (e: any) {
    console.error('loadPools failed:', e)
  }
}

async function loadRuns(pickerId?: string) {
  try {
    runs.value = await stockPickerApi.listRuns(pickerId)
  } catch {
    // ignore
  }
}

function selectPicker(p: Strategy) {
  currentPicker.value = p
  code.value = p.code
  name.value = p.name
  pickerId.value = p.strategy_id
  isEditing.value = true
  loadRuns(p.strategy_id)
}

function createNew() {
  currentPicker.value = null
  code.value = `import akshare as ak
import pandas as pd

def pick_stocks():
    df = ak.stock_zh_a_spot_em()
    # 在此编写你的选股逻辑
    return [
        {"symbol": "000001", "name": "平安银行", "score": 10.0, "reason": "示例"}
    ]
`
  name.value = ''
  pickerId.value = 'picker_' + Date.now()
  isEditing.value = true
  runs.value = []
}

watch(isEditing, (val) => {
  showEditor.value = val
})

async function savePicker() {
  if (!name.value || !pickerId.value) {
    showToast(t('stockPicker.fillRequired'), 'error')
    return
  }
  loading.value = true
  try {
    if (currentPicker.value) {
      await strategyApi.update(currentPicker.value.strategy_id, {
        name: name.value,
        code: code.value,
      })
      showToast(t('stockPicker.saveSuccess'))
    } else {
      await strategyApi.create({
        strategy_id: pickerId.value,
        name: name.value,
        code: code.value,
        type: 'picker',
      })
      showToast(t('stockPicker.createSuccess'))
      currentPicker.value = await strategyApi.get(pickerId.value)
    }
    await loadPickers()
  } catch (e: any) {
    showToast(t('stockPicker.saveError') + ': ' + e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function deletePicker(p: Strategy) {
  if (p.strategy_id === builtinPickerId) {
    showToast(t('stockPicker.cannotDeleteBuiltin'), 'error')
    return
  }
  if (!confirm(t('stockPicker.confirmDelete', { name: p.name }))) return
  try {
    await strategyApi.remove(p.strategy_id)
    if (currentPicker.value?.strategy_id === p.strategy_id) {
      currentPicker.value = null
      isEditing.value = false
    }
    await loadPickers()
    showToast(t('stockPicker.deleteSuccess'))
  } catch (e: any) {
    showToast(t('stockPicker.deleteError') + ': ' + e.message, 'error')
  }
}

async function runPicker() {
  if (!currentPicker.value) return
  running.value = true
  try {
    const pool = await stockPickerApi.runPicker(currentPicker.value.strategy_id)
    showToast(t('stockPicker.runSuccess', { count: pool.items.length }))
    pools.value = [pool, ...pools.value.filter(p => p.pool_id !== pool.pool_id)]
    await loadRuns(currentPicker.value.strategy_id)
  } catch (e: any) {
    showToast(t('stockPicker.runError') + ': ' + e.message, 'error')
  } finally {
    running.value = false
  }
}

function goToBacktestWithPool(poolId: string) {
  router.push({ path: '/backtests', query: { poolId } })
}

function formatDate(d?: string) {
  if (!d) return '-'
  return new Date(d).toLocaleString()
}

onMounted(() => {
  loadPickers()
  loadPools()
})

onBeforeUnmount(() => {
  showEditor.value = false
})
</script>

<template>
  <div class="picker-workshop">
    <!-- Left panel: picker list -->
    <aside class="panel panel--left">
      <div class="panel-header">
        <h2 class="panel-title">{{ t('stockPicker.list') }}</h2>
        <button class="btn btn--primary btn--sm" @click="createNew">+ {{ t('stockPicker.new') }}</button>
      </div>

      <ul class="list">
        <li
          v-for="p in pickers"
          :key="p.strategy_id"
          :class="['list-item', { active: currentPicker?.strategy_id === p.strategy_id, builtin: p.strategy_id === builtinPickerId }]"
          @click="selectPicker(p)"
        >
          <div class="list-content">
            <div class="list-title">
              {{ p.name }}
              <span v-if="p.strategy_id === builtinPickerId" class="builtin-tag">{{ t('stockPicker.builtin') }}</span>
            </div>
            <div class="list-meta">{{ p.strategy_id }}</div>
          </div>
          <button
            v-if="p.strategy_id !== builtinPickerId"
            class="btn btn--ghost btn--sm list-action"
            @click.stop="deletePicker(p)"
          >
            {{ t('common.delete') }}
          </button>
        </li>
      </ul>
    </aside>

    <!-- Right panel: editor + results -->
    <main class="panel panel--right">
      <div v-if="!isEditing" class="empty-state">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="m16 18 6-6-6-6"/>
            <path d="m8 6-6 6 6 6"/>
          </svg>
        </div>
        <p class="empty-text">{{ t('stockPicker.editorPlaceholder') }}</p>
        <button class="btn btn--primary" @click="createNew">{{ t('stockPicker.new') }}</button>
      </div>

      <template v-else>
        <div class="editor-toolbar">
          <div class="toolbar-fields">
            <div class="field">
              <label>{{ t('common.name') }}</label>
              <input v-model="name" type="text" class="form-input" />
            </div>
            <div class="field">
              <label>{{ t('stockPicker.pickerId') }}</label>
              <input v-model="pickerId" type="text" class="form-input" :disabled="!!currentPicker" />
            </div>
          </div>
          <div class="toolbar-actions">
            <button class="btn btn--primary" :disabled="loading" @click="savePicker">
              {{ loading ? t('common.saving') : t('common.save') }}
            </button>
            <button
              v-if="currentPicker"
              class="btn btn--secondary"
              :disabled="running"
              @click="runPicker"
            >
              {{ running ? t('stockPicker.running') : t('stockPicker.run') }}
            </button>
          </div>
        </div>

        <div v-if="toast" :class="['toast', toastType]">{{ toast }}</div>

        <div class="editor-body">
          <Codemirror
            v-if="showEditor"
            v-model="code"
            :extensions="extensions"
            :style="{ height: '100%' }"
            :indent-with-tab="true"
            :tab-size="4"
          />
        </div>

        <!-- Recent pools -->
        <div v-if="pools.filter(p => p.picker_id === currentPicker?.strategy_id).length" class="results-section">
          <h4 class="results-title">{{ t('stockPicker.recentResults') }}</h4>
          <div
            v-for="pool in pools.filter(p => p.picker_id === currentPicker?.strategy_id).slice(0, 3)"
            :key="pool.pool_id"
            class="result-card"
          >
            <div class="result-header">
              <span class="result-name">{{ pool.name }}</span>
              <span class="result-meta">{{ formatDate(pool.generated_at) }} · {{ pool.items.length }} {{ t('stockPicker.stocks') }}</span>
            </div>
            <div class="result-items">
              <span v-for="item in pool.items.slice(0, 8)" :key="item.id" class="result-chip">
                {{ item.symbol }}
              </span>
              <span v-if="pool.items.length > 8" class="result-chip more">+{{ pool.items.length - 8 }}</span>
            </div>
            <div class="result-actions">
              <button class="btn btn--ghost btn--sm" @click="goToBacktestWithPool(pool.pool_id)">
                {{ t('stockPicker.createBacktest') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Run history -->
        <div v-if="runs.length" class="results-section">
          <h4 class="results-title">{{ t('stockPicker.runHistory') }}</h4>
          <table class="run-table">
            <thead>
              <tr>
                <th>{{ t('stockPicker.runTime') }}</th>
                <th>{{ t('common.status') }}</th>
                <th>{{ t('stockPicker.resultCount') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="run in runs.slice(0, 10)" :key="run.run_id">
                <td>{{ formatDate(run.created_at) }}</td>
                <td>
                  <span :class="['status-badge', run.status]">{{ t(`stockPicker.status.${run.status}`) }}</span>
                </td>
                <td>{{ run.result_count ?? '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </main>

    <LoadingOverlay :visible="showOverlay" :text="t('common.loading')" />
  </div>
</template>

<style scoped>
.picker-workshop {
  display: flex;
  height: calc(100vh - var(--header-height) - (var(--space-3xl) * 2) - 60px);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.panel {
  display: flex;
  flex-direction: column;
}

.panel--left {
  width: 300px;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
}

.panel--right {
  flex: 1;
  min-width: 0;
  background: var(--bg-base);
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-xl) var(--space-2xl);
  border-bottom: 1px solid var(--border-subtle);
}

.panel-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.list {
  list-style: none;
  margin: 0;
  padding: var(--space-md);
  overflow-y: auto;
  flex: 1;
}

.list-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: var(--space-xs);
}

.list-item:hover {
  background: var(--bg-surface-hover);
}

.list-item.active {
  background: var(--accent-subtle);
  box-shadow: inset 2px 0 0 var(--accent);
}

.list-item.active .list-title {
  color: var(--accent);
  font-weight: 600;
}

.list-item.builtin .list-title {
  color: #8b5cf6;
}

.builtin-tag {
  font-size: 0.7rem;
  font-weight: 600;
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.12);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  margin-left: var(--space-sm);
}

.list-content {
  flex: 1;
  min-width: 0;
}

.list-title {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.list-action {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.list-item:hover .list-action {
  opacity: 1;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-xl);
  color: var(--text-muted);
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-surface-hover);
  border-radius: 50%;
  color: var(--text-secondary);
}

.empty-text {
  font-size: 1rem;
  color: var(--text-secondary);
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-xl);
  padding: var(--space-lg) var(--space-2xl);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  flex-wrap: wrap;
}

.toolbar-fields {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  flex: 1;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.field {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.field label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.field .form-input {
  width: 220px;
}

.toast {
  padding: var(--space-sm) var(--space-2xl);
  font-size: 0.85rem;
  font-weight: 500;
}

.toast.success {
  background: var(--success-subtle);
  color: #047857;
}

.toast.error {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.editor-body {
  height: 360px;
  overflow: hidden;
  padding: var(--space-lg);
}

.editor-body :deep(.cm-editor) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.results-section {
  padding: var(--space-xl) var(--space-2xl);
  border-top: 1px solid var(--border-subtle);
}

.results-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.result-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  margin-bottom: var(--space-md);
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.result-name {
  font-weight: 600;
  color: var(--text-primary);
}

.result-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.result-items {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.result-chip {
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-surface-hover);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.result-chip.more {
  background: transparent;
  color: var(--text-muted);
}

.result-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
}

.run-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.run-table th,
.run-table td {
  text-align: left;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--border-subtle);
}

.run-table th {
  color: var(--text-secondary);
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.running {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.success {
  background: var(--success-subtle);
  color: #047857;
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.btn--secondary {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}

.btn--secondary:hover {
  background: var(--border-subtle);
}
</style>

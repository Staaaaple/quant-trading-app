<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { strategyApi, type Strategy } from '@/api/strategy'
import { strategyFlowApi, type StrategyFlow } from '@/api/strategyFlow'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

const { t } = useI18n()

const flows = ref<StrategyFlow[]>([])
const currentFlow = ref<StrategyFlow | null>(null)
const flowId = ref('')
const name = ref('')
const pickerId = ref('')
const riskId = ref('')
const tradeId = ref('')
const isEditing = ref(false)
const loading = ref(false)
const toast = ref('')

const pickers = ref<Strategy[]>([])
const risks = ref<Strategy[]>([])
const trades = ref<Strategy[]>([])

let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

async function loadStrategies() {
  try {
    const [p, r, tr] = await Promise.all([
      strategyApi.list('?strategy_type=picker'),
      strategyApi.list('?strategy_type=risk'),
      strategyApi.list('?strategy_type=trade'),
    ])
    pickers.value = p
    risks.value = r
    trades.value = tr
  } catch (e: any) {
    console.error('loadStrategies failed:', e)
  }
}

async function loadFlows() {
  try {
    flows.value = await strategyFlowApi.list()
  } catch (e: any) {
    console.error('loadFlows failed:', e)
    flows.value = []
  }
}

function selectFlow(f: StrategyFlow) {
  currentFlow.value = f
  flowId.value = f.flow_id
  name.value = f.name
  pickerId.value = f.picker_strategy_id || ''
  riskId.value = f.risk_strategy_id || ''
  tradeId.value = f.trade_strategy_id
  isEditing.value = true
}

function createNew() {
  currentFlow.value = null
  flowId.value = 'flow_' + Date.now()
  name.value = ''
  pickerId.value = ''
  riskId.value = ''
  tradeId.value = ''
  isEditing.value = true
}

async function saveFlow() {
  if (!name.value || !flowId.value || !tradeId.value) {
    showToast(t('flow.fillRequired'))
    return
  }
  loading.value = true
  try {
    if (currentFlow.value) {
      await strategyFlowApi.update(currentFlow.value.flow_id, {
        name: name.value,
        picker_strategy_id: pickerId.value || undefined,
        risk_strategy_id: riskId.value || undefined,
        trade_strategy_id: tradeId.value,
      })
      showToast(t('flow.saveSuccess'))
    } else {
      await strategyFlowApi.create({
        flow_id: flowId.value,
        name: name.value,
        picker_strategy_id: pickerId.value || undefined,
        risk_strategy_id: riskId.value || undefined,
        trade_strategy_id: tradeId.value,
      })
      showToast(t('flow.createSuccess'))
      currentFlow.value = await strategyFlowApi.get(flowId.value)
    }
    await loadFlows()
  } catch (e: any) {
    showToast(t('flow.saveError') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

async function deleteFlow(f: StrategyFlow) {
  if (!confirm(t('flow.confirmDelete', { name: f.name }))) return
  try {
    await strategyFlowApi.remove(f.flow_id)
    if (currentFlow.value?.flow_id === f.flow_id) {
      currentFlow.value = null
      isEditing.value = false
    }
    await loadFlows()
    showToast(t('flow.deleteSuccess'))
  } catch (e: any) {
    showToast(t('flow.deleteError') + ': ' + e.message)
  }
}

function strategyName(id: string) {
  const all = [...pickers.value, ...risks.value, ...trades.value]
  return all.find(s => s.strategy_id === id)?.name || id
}

onMounted(() => {
  loadStrategies()
  loadFlows()
})
</script>

<template>
  <div class="flow-workshop">
    <!-- Left panel: flow list -->
    <aside class="panel panel--left">
      <div class="panel-header">
        <h2 class="panel-title">{{ t('flow.list') }}</h2>
        <button class="btn btn--primary btn--sm" @click="createNew">+ {{ t('flow.new') }}</button>
      </div>

      <ul class="list">
        <li
          v-for="f in flows"
          :key="f.flow_id"
          :class="['list-item', { active: currentFlow?.flow_id === f.flow_id }]"
          @click="selectFlow(f)"
        >
          <div class="list-content">
            <div class="list-title">{{ f.name }}</div>
            <div class="list-meta">{{ f.flow_id }}</div>
          </div>
          <button
            class="btn btn--ghost btn--sm list-action"
            @click.stop="deleteFlow(f)"
          >
            {{ t('common.delete') }}
          </button>
        </li>
      </ul>
    </aside>

    <!-- Right panel: editor -->
    <main class="panel panel--right">
      <div v-if="!isEditing" class="empty-state">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="m16 18 6-6-6-6"/>
            <path d="m8 6-6 6 6 6"/>
          </svg>
        </div>
        <p class="empty-text">{{ t('flow.editorPlaceholder') }}</p>
        <button class="btn btn--primary" @click="createNew">{{ t('flow.new') }}</button>
      </div>

      <template v-else>
        <div class="editor-toolbar">
          <div class="toolbar-fields">
            <div class="field">
              <label>{{ t('common.name') }}</label>
              <input v-model="name" type="text" class="form-input" />
            </div>
            <div class="field">
              <label>{{ t('flow.flowId') }}</label>
              <input
                v-model="flowId"
                type="text"
                class="form-input"
                :disabled="!!currentFlow"
              />
            </div>
          </div>
          <button class="btn btn--primary" :disabled="loading" @click="saveFlow">
            {{ loading ? t('common.saving') : t('common.save') }}
          </button>
        </div>

        <div v-if="toast" class="toast">{{ toast }}</div>

        <div class="flow-builder">
          <div class="node">
            <div class="node-badge picker">{{ t('flow.pickerNode') }}</div>
            <div class="node-body">
              <select v-model="pickerId" class="form-input">
                <option value="">{{ t('flow.noPicker') }}</option>
                <option v-for="s in pickers" :key="s.strategy_id" :value="s.strategy_id">
                  {{ s.name }} ({{ s.strategy_id }})
                </option>
              </select>
              <div v-if="pickerId" class="node-selected">{{ strategyName(pickerId) }}</div>
            </div>
          </div>

          <div class="arrow">↓</div>

          <div class="node">
            <div class="node-badge risk">{{ t('flow.riskNode') }}</div>
            <div class="node-body">
              <select v-model="riskId" class="form-input">
                <option value="">{{ t('flow.noRisk') }}</option>
                <option v-for="s in risks" :key="s.strategy_id" :value="s.strategy_id">
                  {{ s.name }} ({{ s.strategy_id }})
                </option>
              </select>
              <div v-if="riskId" class="node-selected">{{ strategyName(riskId) }}</div>
            </div>
          </div>

          <div class="arrow">↓</div>

          <div class="node">
            <div class="node-badge trade">{{ t('flow.tradeNode') }}</div>
            <div class="node-body">
              <select v-model="tradeId" class="form-input" :class="{ invalid: !tradeId }">
                <option value="">{{ t('flow.selectTrade') }}</option>
                <option v-for="s in trades" :key="s.strategy_id" :value="s.strategy_id">
                  {{ s.name }} ({{ s.strategy_id }})
                </option>
              </select>
              <div v-if="tradeId" class="node-selected">{{ strategyName(tradeId) }}</div>
            </div>
          </div>
        </div>
      </template>
    </main>

    <LoadingOverlay :visible="loading" :text="t('common.loading')" />
  </div>
</template>

<style scoped>
.flow-workshop {
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
  background: var(--success-subtle);
  color: #047857;
  font-size: 0.85rem;
  font-weight: 500;
}

.flow-builder {
  padding: var(--space-2xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
}

.node {
  width: 100%;
  max-width: 480px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.node-badge {
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
}

.node-badge.picker {
  background: #8b5cf6;
}

.node-badge.risk {
  background: #f59e0b;
}

.node-badge.trade {
  background: #10b981;
}

.node-body {
  padding: var(--space-lg);
}

.node-body select {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 0.95rem;
}

.node-body select.invalid {
  border-color: var(--error);
}

.node-selected {
  margin-top: var(--space-sm);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.arrow {
  font-size: 1.5rem;
  color: var(--text-muted);
  font-weight: 600;
}
</style>

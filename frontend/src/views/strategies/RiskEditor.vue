<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { strategyApi, type Strategy } from '@/api/strategy'
import { riskStrategyApi, type RiskStrategyConfig } from '@/api/riskStrategy'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

const { t } = useI18n()
const extensions = [python(), oneDark]

const strategies = ref<Strategy[]>([])
const currentStrategy = ref<Strategy | null>(null)
const code = ref('')
const name = ref('')
const strategyId = ref('')
const isEditing = ref(false)
const showEditor = ref(false)
const loading = ref(false)
const toast = ref('')

const maxPositionPct = ref(0.2)
const maxDailyDrawdown = ref(0.05)
const blacklist = ref('')

let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

async function loadStrategies() {
  try {
    strategies.value = await strategyApi.list('?strategy_type=risk')
  } catch (e: any) {
    console.error('loadStrategies failed:', e)
    strategies.value = []
  }
}

async function loadRiskConfig(s: Strategy) {
  try {
    const cfg = await riskStrategyApi.get(s.strategy_id)
    maxPositionPct.value = cfg.max_position_pct
    maxDailyDrawdown.value = cfg.max_daily_drawdown
    blacklist.value = cfg.blacklist
  } catch {
    maxPositionPct.value = 0.2
    maxDailyDrawdown.value = 0.05
    blacklist.value = ''
  }
}

function selectStrategy(s: Strategy) {
  currentStrategy.value = s
  code.value = s.code
  name.value = s.name
  strategyId.value = s.strategy_id
  isEditing.value = true
  loadRiskConfig(s)
}

function createNew() {
  currentStrategy.value = null
  code.value = `def risk_check(context):
    """
    风控检查函数。
    context 包含: portfolio, positions, orders, current_date 等信息。
    返回 dict: {"passed": bool, "reason": str}
    """
    return {"passed": True, "reason": ""}
`
  name.value = ''
  strategyId.value = 'risk_' + Date.now()
  isEditing.value = true
  maxPositionPct.value = 0.2
  maxDailyDrawdown.value = 0.05
  blacklist.value = ''
}

async function saveStrategy() {
  if (!name.value || !strategyId.value) {
    showToast(t('strategy.fillRequired'))
    return
  }
  loading.value = true
  try {
    if (currentStrategy.value) {
      await strategyApi.update(currentStrategy.value.strategy_id, {
        name: name.value,
        code: code.value,
      })
      await riskStrategyApi.update(currentStrategy.value.strategy_id, {
        max_position_pct: maxPositionPct.value,
        max_daily_drawdown: maxDailyDrawdown.value,
        blacklist: blacklist.value,
      })
      showToast(t('strategy.saveSuccess'))
    } else {
      await strategyApi.create({
        strategy_id: strategyId.value,
        name: name.value,
        code: code.value,
        type: 'risk',
      })
      await riskStrategyApi.create({
        strategy_id: strategyId.value,
        max_position_pct: maxPositionPct.value,
        max_daily_drawdown: maxDailyDrawdown.value,
        blacklist: blacklist.value,
      })
      showToast(t('strategy.createSuccess'))
      currentStrategy.value = await strategyApi.get(strategyId.value)
    }
    await loadStrategies()
  } catch (e: any) {
    showToast(t('strategy.saveError') + ': ' + e.message)
  } finally {
    loading.value = false
  }
}

async function deleteStrategy(s: Strategy) {
  if (!confirm(t('strategy.confirmDelete', { name: s.name }))) return
  try {
    await strategyApi.remove(s.strategy_id)
    if (currentStrategy.value?.strategy_id === s.strategy_id) {
      currentStrategy.value = null
      isEditing.value = false
    }
    await loadStrategies()
    showToast(t('strategy.deleteSuccess'))
  } catch (e: any) {
    showToast(t('strategy.deleteError') + ': ' + e.message)
  }
}

watch(isEditing, (val) => {
  showEditor.value = val
})

onMounted(() => {
  loadStrategies()
})

onBeforeUnmount(() => {
  showEditor.value = false
})
</script>

<template>
  <div class="workshop">
    <!-- Left panel: strategy list -->
    <aside class="panel panel--left">
      <div class="panel-header">
        <h2 class="panel-title">{{ t('strategy.list') }}</h2>
        <button class="btn btn--primary btn--sm" @click="createNew">+ {{ t('strategy.new') }}</button>
      </div>

      <ul class="list">
        <li
          v-for="s in strategies"
          :key="s.strategy_id"
          :class="['list-item', { active: currentStrategy?.strategy_id === s.strategy_id }]"
          @click="selectStrategy(s)"
        >
          <div class="list-content">
            <div class="list-title">{{ s.name }}</div>
            <div class="list-meta">{{ s.strategy_id }}</div>
          </div>
          <button
            class="btn btn--ghost btn--sm list-action"
            @click.stop="deleteStrategy(s)"
          >
            {{ t('common.delete') }}
          </button>
        </li>
      </ul>
    </aside>

    <!-- Right panel: editor + config -->
    <main class="panel panel--right">
      <div v-if="!isEditing" class="empty-state">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="m16 18 6-6-6-6"/>
            <path d="m8 6-6 6 6 6"/>
          </svg>
        </div>
        <p class="empty-text">{{ t('strategy.editorPlaceholder') }}</p>
        <button class="btn btn--primary" @click="createNew">{{ t('strategy.new') }}</button>
      </div>

      <template v-else>
        <div class="editor-toolbar">
          <div class="toolbar-fields">
            <div class="field">
              <label>{{ t('common.name') }}</label>
              <input v-model="name" type="text" class="form-input" />
            </div>
            <div class="field">
              <label>{{ t('strategy.strategyId') }}</label>
              <input
                v-model="strategyId"
                type="text"
                class="form-input"
                :disabled="!!currentStrategy"
              />
            </div>
          </div>
          <button class="btn btn--primary" :disabled="loading" @click="saveStrategy">
            {{ loading ? t('common.saving') : t('common.save') }}
          </button>
        </div>

        <div v-if="toast" class="toast">{{ toast }}</div>

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

        <div class="config-section">
          <h4 class="config-title">{{ t('risk.configTitle') }}</h4>
          <div class="config-grid">
            <div class="config-field">
              <label>{{ t('risk.maxPositionPct') }}</label>
              <input v-model.number="maxPositionPct" type="number" step="0.01" min="0" max="1" class="form-input" />
            </div>
            <div class="config-field">
              <label>{{ t('risk.maxDailyDrawdown') }}</label>
              <input v-model.number="maxDailyDrawdown" type="number" step="0.01" min="0" max="1" class="form-input" />
            </div>
            <div class="config-field full">
              <label>{{ t('risk.blacklist') }}</label>
              <input v-model="blacklist" type="text" class="form-input" :placeholder="t('risk.blacklistPlaceholder')" />
            </div>
          </div>
        </div>
      </template>
    </main>

    <LoadingOverlay :visible="loading" :text="t('common.loading')" />
  </div>
</template>

<style scoped>
.workshop {
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

.editor-body {
  height: 280px;
  overflow: hidden;
  padding: var(--space-lg);
}

.editor-body :deep(.cm-editor) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.config-section {
  padding: var(--space-xl) var(--space-2xl);
  border-top: 1px solid var(--border-subtle);
}

.config-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-lg);
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.config-field.full {
  grid-column: 1 / -1;
}

.config-field label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.config-field .form-input {
  width: 100%;
}
</style>

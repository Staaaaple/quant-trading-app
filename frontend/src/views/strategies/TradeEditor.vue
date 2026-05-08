<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { strategyApi, type Strategy } from '@/api/strategy'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import PipelineEditor from '@/components/pipeline/PipelineEditor.vue'

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
const showApiDoc = ref(false)

// Mode switch: 'visual' (pipeline) | 'code' (developer)
const editMode = ref<'visual' | 'code'>('visual')

// Pipeline config
const defaultPipelineConfig = () => ({
  version: '1.0',
  stages: [
    {
      id: 'init-1',
      type: 'init',
      config: { history_depth: 30, max_position_pct: 0.95 },
    },
    {
      id: 'indicator-1',
      type: 'indicator',
      config: {
        indicators: [
          { name: 'ma5', type: 'MA', period: 5, field: 'close' },
          { name: 'ma20', type: 'MA', period: 20, field: 'close' },
        ],
      },
    },
    {
      id: 'risk-1',
      type: 'risk',
      config: { checks: [] },
    },
    {
      id: 'signal-1',
      type: 'signal',
      config: {
        groups: [
          {
            id: 'buy-signal',
            direction: 'buy',
            logic: 'AND',
            conditions: [
              { left: { indicator: 'ma5' }, op: 'cross_up', right: { indicator: 'ma20' } },
            ],
          },
          {
            id: 'sell-signal',
            direction: 'sell',
            logic: 'AND',
            conditions: [
              { left: { indicator: 'ma5' }, op: 'cross_down', right: { indicator: 'ma20' } },
            ],
          },
        ],
      },
    },
    {
      id: 'action-1',
      type: 'action',
      config: {
        rules: [
          { signal_group: 'buy-signal', action: 'order_target_percent', weight: 0.5 },
          { signal_group: 'sell-signal', action: 'order_target_percent', weight: 0.0 },
        ],
      },
    },
  ],
})

const pipelineConfig = ref<Record<string, any>>(defaultPipelineConfig())

let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

async function loadStrategies() {
  try {
    strategies.value = await strategyApi.list('?strategy_type=trade')
  } catch (e: any) {
    console.error('loadStrategies failed:', e)
    strategies.value = []
  }
}

function selectStrategy(s: Strategy) {
  currentStrategy.value = s
  name.value = s.name
  strategyId.value = s.strategy_id
  code.value = s.code
  if (s.pipeline_config) {
    pipelineConfig.value = JSON.parse(JSON.stringify(s.pipeline_config))
    editMode.value = 'visual'
  } else {
    editMode.value = 'code'
  }
  isEditing.value = true
}

function createNew() {
  currentStrategy.value = null
  pipelineConfig.value = defaultPipelineConfig()
  code.value = ''
  name.value = ''
  strategyId.value = 'trade_' + Date.now()
  editMode.value = 'visual'
  isEditing.value = true
}

async function saveStrategy() {
  if (!name.value || !strategyId.value) {
    showToast(t('strategy.fillRequired'))
    return
  }
  loading.value = true
  try {
    const payload: any = {
      name: name.value,
    }
    if (editMode.value === 'visual') {
      payload.pipeline_config = pipelineConfig.value
    } else {
      payload.code = code.value
    }

    if (currentStrategy.value) {
      await strategyApi.update(currentStrategy.value.strategy_id, payload)
      showToast(t('strategy.saveSuccess'))
    } else {
      await strategyApi.create({
        strategy_id: strategyId.value,
        name: name.value,
        type: 'trade',
        ...payload,
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

    <!-- Right panel: editor -->
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
          <div class="toolbar-actions">
            <!-- Mode Switch -->
            <div class="mode-switch">
              <button
                class="mode-btn"
                :class="{ 'mode-btn--active': editMode === 'visual' }"
                @click="editMode = 'visual'"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                可视化模式
              </button>
              <button
                class="mode-btn"
                :class="{ 'mode-btn--active': editMode === 'code' }"
                @click="editMode = 'code'"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                开发者模式
              </button>
            </div>
            <button
              class="btn btn--secondary"
              :class="{ 'btn--active': showApiDoc }"
              @click="showApiDoc = !showApiDoc"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/><path d="M8 7h6"/><path d="M8 11h8"/></svg>
              API 参考
            </button>
            <button class="btn btn--primary" :disabled="loading" @click="saveStrategy">
              {{ loading ? t('common.saving') : t('common.save') }}
            </button>
          </div>
        </div>

        <div v-if="toast" class="toast">{{ toast }}</div>

        <div class="editor-body">
          <div class="editor-main" :class="{ 'editor-main--with-doc': showApiDoc }">
            <!-- Visual Mode -->
            <PipelineEditor
              v-if="editMode === 'visual'"
              v-model="pipelineConfig"
            />
            <!-- Code Mode -->
            <Codemirror
              v-else-if="showEditor"
              v-model="code"
              :extensions="extensions"
              :style="{ height: '100%' }"
              :indent-with-tab="true"
              :tab-size="4"
            />
          </div>

          <!-- API Reference Panel -->
          <div v-if="showApiDoc" class="api-doc-panel">
            <!-- ... existing API doc content ... -->
            <div class="api-doc-header">
              <h3 class="api-doc-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/><path d="M8 7h6"/><path d="M8 11h8"/></svg>
                API 参考
              </h3>
              <button class="api-doc-close" @click="showApiDoc = false">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>
            <div class="api-doc-body">
              <div class="api-doc-section">
                <h4 class="api-doc-section-title">基本结构</h4>
                <pre class="api-doc-code">from akquant import Strategy

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__()

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(21, symbol, field="close")
        if len(closes) < 20:
            return
        ma = closes[-20:].mean()
        pos = self.get_position(symbol)
        if bar.close > ma and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif bar.close < ma and pos > 0:
            self.order_target_percent(0.0, symbol)</pre>
              </div>
              <div class="api-doc-section">
                <h4 class="api-doc-section-title">核心方法</h4>
                <div class="api-doc-table">
                  <div class="api-doc-row"><code class="api-doc-name">on_bar(bar)</code><span class="api-doc-desc">每个 K 线到达时触发</span></div>
                  <div class="api-doc-row"><code class="api-doc-name">get_history(count, symbol, field='close')</code><span class="api-doc-desc">获取历史数据</span></div>
                  <div class="api-doc-row"><code class="api-doc-name">set_history_depth(n)</code><span class="api-doc-desc">设置历史数据缓存深度</span></div>
                  <div class="api-doc-row"><code class="api-doc-name">order_target_percent(weight, symbol)</code><span class="api-doc-desc">目标仓位下单</span></div>
                  <div class="api-doc-row"><code class="api-doc-name">get_position(symbol)</code><span class="api-doc-desc">获取当前持仓数量</span></div>
                </div>
              </div>
              <div class="api-doc-section">
                <h4 class="api-doc-section-title">注意事项</h4>
                <ul class="api-doc-list">
                  <li>策略必须继承 <code>from akquant import Strategy</code></li>
                  <li>get_history 前需调用 set_history_depth(n)</li>
                  <li>order_target_percent(0.0, symbol) 表示清仓</li>
                </ul>
              </div>
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
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
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
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: var(--space-lg);
  gap: var(--space-lg);
}

.editor-main {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.editor-main--with-doc {
  flex: 1;
}

.editor-body :deep(.cm-editor) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

/* Mode Switch */
.mode-switch {
  display: flex;
  align-items: center;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 2px;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.mode-btn:hover {
  color: var(--text-primary);
}

.mode-btn--active {
  background: var(--accent-subtle);
  color: var(--accent);
}

/* API Doc Panel */
.api-doc-panel {
  width: 360px;
  min-width: 360px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.api-doc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.api-doc-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.api-doc-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.api-doc-close:hover {
  background: var(--bg-base);
  color: var(--text-primary);
}

.api-doc-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md) var(--space-lg);
}

.api-doc-section {
  margin-bottom: var(--space-lg);
}

.api-doc-section:last-child {
  margin-bottom: 0;
}

.api-doc-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--space-sm) 0;
}

.api-doc-code {
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  font-size: 0.75rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.api-doc-table {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.api-doc-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.api-doc-name {
  font-size: 0.78rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--text-primary);
  font-weight: 500;
}

.api-doc-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.api-doc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.api-doc-list li {
  font-size: 0.78rem;
  color: var(--text-secondary);
  padding: 4px 0;
  padding-left: 16px;
  position: relative;
  line-height: 1.5;
}

.api-doc-list li::before {
  content: '·';
  position: absolute;
  left: 0;
  color: var(--text-muted);
  font-weight: 700;
}

.api-doc-list code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.75rem;
  color: var(--accent);
}

.btn--active {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: var(--accent);
}

/* Responsive */
@media (max-width: 1100px) {
  .api-doc-panel {
    width: 300px;
    min-width: 300px;
  }
}

@media (max-width: 900px) {
  .api-doc-panel {
    width: 260px;
    min-width: 260px;
  }
}
</style>

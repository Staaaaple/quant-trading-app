<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { strategyApi, type Strategy } from '@/api/strategy'
import { dnaApi, type StrategyDNASummary, type DNAPreview } from '@/api/dna'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import GenePanel from '@/components/GenePanel.vue'

const { t } = useI18n()
const extensions = [python(), oneDark]

const strategies = ref<Strategy[]>([])
const currentStrategy = ref<Strategy | null>(null)
const dnaSummaries = ref<StrategyDNASummary[]>([])
const code = ref('')
const name = ref('')
const strategyId = ref('')
const isEditing = ref(false)
const showEditor = ref(false)
const loading = ref(false)
const toast = ref('')

let toastTimer: ReturnType<typeof setTimeout> | null = null
let previewTimer: ReturnType<typeof setTimeout> | null = null

const previewData = ref<DNAPreview | null>(null)
const previewLoading = ref(false)
const previewError = ref('')

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

async function loadStrategies() {
  try {
    strategies.value = await strategyApi.list()
  } catch (e: any) {
    console.error('loadStrategies failed:', e)
    strategies.value = []
  }
  await loadDNA()
}

async function loadDNA() {
  try {
    dnaSummaries.value = await dnaApi.listAll()
  } catch {
    dnaSummaries.value = []
  }
}

function getDna(strategyId: string) {
  return dnaSummaries.value.find(d => d.strategy_id === strategyId)
}

async function previewDNA() {
  if (!code.value || code.value.length < 50) {
    previewData.value = null
    return
  }
  previewLoading.value = true
  previewError.value = ''
  try {
    previewData.value = await dnaApi.preview(strategyId.value || 'preview_' + Date.now(), code.value)
  } catch (e: any) {
    previewError.value = e.message
    previewData.value = null
  } finally {
    previewLoading.value = false
  }
}

function debouncedPreview() {
  if (previewTimer) clearTimeout(previewTimer)
  previewTimer = setTimeout(previewDNA, 3000)
}

function similarityWarning() {
  if (!previewData.value || !dnaSummaries.value.length) return null
  const previewGenes = new Set([
    ...previewData.value.feature_genes,
    ...previewData.value.signal_genes,
  ])
  if (!previewGenes.size) return null

  let maxOverlap = 0
  let mostSimilar = ''
  for (const dna of dnaSummaries.value) {
    if (dna.strategy_id === strategyId.value) continue
    const existingGenes = new Set([
      ...(dna.feature_genes || []),
      ...(dna.signal_genes || []),
    ])
    const intersection = [...previewGenes].filter(g => existingGenes.has(g))
    const union = new Set([...previewGenes, ...existingGenes])
    const similarity = union.size ? intersection.length / union.size : 0
    if (similarity > maxOverlap) {
      maxOverlap = similarity
      mostSimilar = dna.name || dna.strategy_id
    }
  }
  if (maxOverlap > 0.5) {
    return `与「${mostSimilar}」基因重叠度 ${(maxOverlap * 100).toFixed(0)}%，存在近亲繁殖风险`
  }
  return null
}

function healthColor(score: number) {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#d97706'
  return '#92400e'
}

function selectStrategy(s: Strategy) {
  currentStrategy.value = s
  code.value = s.code
  name.value = s.name
  strategyId.value = s.strategy_id
  isEditing.value = true
}

function createNew() {
  currentStrategy.value = null
  code.value = `from akquant import Strategy

class MyStrategy(Strategy):
    def on_bar(self, bar):
        pass
`
  name.value = ''
  strategyId.value = 'strategy_' + Date.now()
  isEditing.value = true
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
      showToast(t('strategy.saveSuccess'))
    } else {
      await strategyApi.create({
        strategy_id: strategyId.value,
        name: name.value,
        code: code.value,
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

watch(code, () => {
  if (isEditing.value) {
    debouncedPreview()
  }
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
          <div class="list-health-dot">
            <span
              v-if="getDna(s.strategy_id)"
              class="health-dot"
              :style="{ background: healthColor(getDna(s.strategy_id)!.health_birth_score) }"
              :title="`健康度: ${getDna(s.strategy_id)!.health_birth_score}`"
            ></span>
            <span v-else class="health-dot health-dot--empty"></span>
          </div>
          <div class="list-content">
            <div class="list-title">{{ s.name }}</div>
            <div class="list-meta">{{ s.strategy_id }}</div>
          </div>
          <RouterLink
            v-if="s.strategy_id"
            :to="`/dna-report/${s.strategy_id}`"
            class="btn btn--ghost btn--sm list-action"
            @click.stop
          >
            基因
          </RouterLink>
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

        <!-- Real-time DNA Preview (方案三) -->
        <div class="preview-panel">
          <div class="preview-header">
            <span class="preview-title">基因实时预览</span>
            <span v-if="previewLoading" class="preview-status">分析中...</span>
            <span v-else-if="previewData" class="preview-status preview-status--ready">已就绪</span>
          </div>
          <div v-if="previewError" class="preview-error">{{ previewError }}</div>
          <div v-else-if="previewData" class="preview-body">
            <div class="preview-scores">
              <div class="preview-score">
                <div class="preview-score-value" :style="{ color: healthColor(previewData.health_birth_score) }">{{ previewData.health_birth_score }}</div>
                <div class="preview-score-label">健康度</div>
              </div>
              <div class="preview-score">
                <div class="preview-score-value">{{ (previewData.gene_diversity_score * 100).toFixed(0) }}%</div>
                <div class="preview-score-label">多样性</div>
              </div>
              <div class="preview-score">
                <div class="preview-score-value">{{ (previewData.metabolic_rate * 100).toFixed(0) }}%</div>
                <div class="preview-score-label">代谢率</div>
              </div>
            </div>
            <div v-if="similarityWarning()" class="preview-warning">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
              {{ similarityWarning() }}
            </div>
            <div class="preview-genes">
              <div class="preview-gene-group">
                <span class="preview-gene-label">特征</span>
                <span v-for="g in previewData.feature_genes.slice(0, 6)" :key="g" class="preview-gene-tag">{{ g }}</span>
                <span v-if="!previewData.feature_genes.length" class="preview-gene-empty">未检测到</span>
              </div>
              <div class="preview-gene-group">
                <span class="preview-gene-label">信号</span>
                <span v-for="g in previewData.signal_genes.slice(0, 6)" :key="g" class="preview-gene-tag preview-gene-tag--signal">{{ g }}</span>
                <span v-if="!previewData.signal_genes.length" class="preview-gene-empty">未检测到</span>
              </div>
              <div class="preview-gene-group">
                <span class="preview-gene-label">风控</span>
                <span v-for="g in previewData.risk_genes.slice(0, 6)" :key="g" class="preview-gene-tag preview-gene-tag--risk">{{ g }}</span>
                <span v-if="!previewData.risk_genes.length" class="preview-gene-empty">未检测到</span>
              </div>
            </div>
          </div>
          <div v-else class="preview-placeholder">输入代码 3 秒后将自动生成基因预览...</div>
        </div>

        <GenePanel v-if="currentStrategy?.strategy_id" :strategy-id="currentStrategy.strategy_id" />
      </template>
    </main>

    <LoadingOverlay :visible="loading" :text="t('common.loading')" />
  </div>
</template>

<style scoped>
.workshop {
  display: flex;
  height: calc(100vh - var(--header-height) - (var(--space-3xl) * 2));
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
  overflow: hidden;
  padding: var(--space-lg);
}

.editor-body :deep(.cm-editor) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.list-health-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding-right: var(--space-sm);
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: block;
}

.health-dot--empty {
  background: var(--border-subtle);
}

/* Real-time DNA Preview (方案三) */
.preview-panel {
  margin-top: var(--space-lg);
  padding: var(--space-lg) var(--space-xl);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.preview-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.preview-status {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.preview-status--ready {
  color: var(--success);
}

.preview-error {
  padding: var(--space-sm) var(--space-md);
  background: var(--error-subtle);
  color: var(--error);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.preview-placeholder {
  font-size: 0.85rem;
  color: var(--text-muted);
  padding: var(--space-md) 0;
}

.preview-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.preview-scores {
  display: flex;
  gap: var(--space-xl);
}

.preview-score {
  text-align: center;
}

.preview-score-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.preview-score-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.preview-warning {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-sm);
  color: #991b1b;
  font-size: 0.8rem;
}

.preview-genes {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.preview-gene-group {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.preview-gene-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
  width: 36px;
  flex-shrink: 0;
}

.preview-gene-tag {
  padding: 2px 8px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--accent);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.preview-gene-tag--signal {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.preview-gene-tag--risk {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.preview-gene-empty {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-style: italic;
}
</style>

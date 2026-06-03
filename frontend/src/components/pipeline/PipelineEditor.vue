<script setup lang="ts">
import { ref, computed } from 'vue'
import { strategyApi } from '@/api/strategy'
import PipelineStageInit from './PipelineStageInit.vue'
import PipelineStageIndicator from './PipelineStageIndicator.vue'
import PipelineStageRisk from './PipelineStageRisk.vue'
import PipelineStageSignal from './PipelineStageSignal.vue'
import PipelineStageAction from './PipelineStageAction.vue'

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: Record<string, any>): void
}>()

const loading = ref(false)
const previewCode = ref('')
const showPreview = ref(false)
const toast = ref('')

const nlText = ref('')
const nlLoading = ref(false)
const nlResult = ref<any>(null)
const nlOriginalText = ref('')  // 保存解析时的原始文本，用于反复对照查看
const showNlConfirm = ref(false)
const nlGeneratedStages = ref<Set<string>>(new Set())

const config = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const stages = computed(() => config.value.stages || [])

function getStage(type: string) {
  return stages.value.find((s: any) => s.type === type)
}

function getStageConfig(type: string) {
  const s = getStage(type)
  return s ? s.config : {}
}

function setStageConfig(type: string, cfg: any) {
  const list = [...stages.value]
  const idx = list.findIndex((s: any) => s.type === type)
  if (idx >= 0) {
    list[idx] = { ...list[idx], config: cfg }
  } else {
    list.push({ id: `${type}-1`, type, config: cfg })
  }
  config.value = { ...config.value, stages: list }
  // 用户手动修改后，清除该阶段的自然语言标记
  const s = new Set(nlGeneratedStages.value)
  s.delete(type)
  nlGeneratedStages.value = s
}

const availableIndicators = computed(() => {
  const indStage = getStage('indicator')
  if (!indStage?.config?.indicators) return []
  return indStage.config.indicators.map((i: any) => i.name)
})

const signalGroups = computed(() => {
  const sigStage = getStage('signal')
  if (!sigStage?.config?.groups) return []
  return sigStage.config.groups.map((g: any) => g.id)
})

interface TextSegment {
  text: string
  type: 'matched' | 'unmatched' | 'gap'
  label?: string
}

const textSegments = computed(() => {
  if (!nlResult.value || !nlOriginalText.value) return []
  const text = nlOriginalText.value
  const matched: [number, number, string][] = nlResult.value.matched_spans || []
  const unmatched: [number, number][] = nlResult.value.unmatched_spans || []

  const spans: Array<{ start: number; end: number; type: 'matched' | 'unmatched'; label?: string }> = []
  for (const [s, e, label] of matched) {
    spans.push({ start: s, end: e, type: 'matched', label })
  }
  for (const [s, e] of unmatched) {
    spans.push({ start: s, end: e, type: 'unmatched' })
  }
  spans.sort((a, b) => a.start - b.start)

  const segments: TextSegment[] = []
  let pos = 0
  for (const span of spans) {
    if (span.start > pos) {
      segments.push({ text: text.slice(pos, span.start), type: 'gap' })
    }
    if (span.end > pos) {
      segments.push({
        text: text.slice(Math.max(pos, span.start), span.end),
        type: span.type,
        label: span.label,
      })
      pos = span.end
    }
  }
  if (pos < text.length) {
    segments.push({ text: text.slice(pos), type: 'gap' })
  }

  return segments
})

const expandedStages = ref<Set<string>>(new Set(['init', 'indicator', 'signal', 'action']))

function toggleStage(type: string) {
  const s = new Set(expandedStages.value)
  if (s.has(type)) {
    s.delete(type)
  } else {
    s.add(type)
  }
  expandedStages.value = s
}

async function onPreviewCode() {
  loading.value = true
  try {
    const res = await strategyApi.previewCode(config.value)
    previewCode.value = res.code
    showPreview.value = true
  } catch (e: any) {
    toast.value = '代码预览失败: ' + e.message
    setTimeout(() => (toast.value = ''), 3000)
  } finally {
    loading.value = false
  }
}

async function onParseNl() {
  if (!nlText.value.trim()) return
  nlLoading.value = true
  try {
    const text = nlText.value.trim()
    const res = await strategyApi.parseNl(text)
    nlResult.value = res
    nlOriginalText.value = text
    showNlConfirm.value = true
  } catch (e: any) {
    toast.value = '解析失败: ' + e.message
    setTimeout(() => (toast.value = ''), 3000)
  } finally {
    nlLoading.value = false
  }
}

function applyNlResult() {
  if (!nlResult.value?.pipeline_config) return
  config.value = { ...nlResult.value.pipeline_config }
  // 标记自然语言生成的阶段
  const generated = new Set<string>()
  for (const stage of nlResult.value.pipeline_config.stages || []) {
    generated.add(stage.type)
  }
  nlGeneratedStages.value = generated
  showNlConfirm.value = false
  nlText.value = ''
  // 保留 nlResult 和 nlOriginalText，方便用户反复查看对照
  // Expand relevant stages
  expandedStages.value = new Set(['init', 'indicator', 'risk', 'signal', 'action'])
}

const STAGE_META: Record<string, { title: string; icon: string; color: string }> = {
  init: { title: '初始化', icon: '⚙️', color: '#6b7280' },
  indicator: { title: '指标计算', icon: '📊', color: '#2563eb' },
  risk: { title: '风控检查', icon: '🛡️', color: '#d97706' },
  signal: { title: '信号规则', icon: '🔔', color: '#16a34a' },
  action: { title: '交易执行', icon: '💰', color: '#b91c1c' },
}
</script>

<template>
  <div class="pipeline-editor">
    <!-- NL Input -->
    <div class="nl-card">
      <div class="nl-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="nl-title">自然语言速配</span>
        <span class="nl-hint">用中文描述策略，系统自动解析</span>
      </div>
      <div class="nl-body">
        <textarea
          v-model="nlText"
          class="nl-textarea"
          rows="2"
          placeholder="例如：当MA5上穿MA20且RSI小于70时买入半仓，最大回撤5%止损"
          @keydown.enter.prevent="onParseNl"
        />
        <div class="nl-actions">
          <button
            v-if="nlResult"
            class="btn btn--ghost btn--sm"
            @click="showNlConfirm = true"
          >
            查看解析
          </button>
          <button
            class="btn btn--primary btn--sm"
            @click="onParseNl"
            :disabled="nlLoading || !nlText.trim()"
          >
            {{ nlLoading ? '解析中...' : '解析' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="pipeline-toolbar">
      <button class="btn btn--secondary" @click="onPreviewCode" :disabled="loading">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round"
        >
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        预览代码
      </button>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>

    <!-- Stage Cards -->
    <div class="stages-list">
      <div
        v-for="stype in ['init', 'indicator', 'risk', 'signal', 'action']"
        :key="stype"
        class="stage-card"
        :class="{ 'stage-card--expanded': expandedStages.has(stype) }"
      >
        <div class="stage-header" @click="toggleStage(stype)">
          <span class="stage-badge" :style="{ background: STAGE_META[stype].color + '15', color: STAGE_META[stype].color }">
            {{ STAGE_META[stype].icon }} {{ STAGE_META[stype].title }}
            <span v-if="nlGeneratedStages.has(stype)" class="nl-badge">NL</span>
          </span>
          <svg
            width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"
            class="stage-chevron"
            :class="{ 'stage-chevron--open': expandedStages.has(stype) }"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>

        <div v-show="expandedStages.has(stype)" class="stage-body">
          <PipelineStageInit
            v-if="stype === 'init'"
            :config="getStageConfig('init')"
            :is-nl-generated="nlGeneratedStages.has('init')"
            @update:config="setStageConfig('init', $event)"
          />
          <PipelineStageIndicator
            v-else-if="stype === 'indicator'"
            :indicators="getStageConfig('indicator').indicators || []"
            :is-nl-generated="nlGeneratedStages.has('indicator')"
            @update:indicators="setStageConfig('indicator', { ...getStageConfig('indicator'), indicators: $event })"
          />
          <PipelineStageRisk
            v-else-if="stype === 'risk'"
            :checks="getStageConfig('risk').checks || []"
            :is-nl-generated="nlGeneratedStages.has('risk')"
            @update:checks="setStageConfig('risk', { ...getStageConfig('risk'), checks: $event })"
          />
          <PipelineStageSignal
            v-else-if="stype === 'signal'"
            :groups="getStageConfig('signal').groups || []"
            :available-indicators="availableIndicators"
            :is-nl-generated="nlGeneratedStages.has('signal')"
            @update:groups="setStageConfig('signal', { ...getStageConfig('signal'), groups: $event })"
          />
          <PipelineStageAction
            v-else-if="stype === 'action'"
            :rules="getStageConfig('action').rules || []"
            :signal-groups="signalGroups"
            :is-nl-generated="nlGeneratedStages.has('action')"
            @update:rules="setStageConfig('action', { ...getStageConfig('action'), rules: $event })"
          />
        </div>
      </div>
    </div>

    <!-- Code Preview Modal -->
    <div v-if="showPreview" class="modal-overlay" @click.self="showPreview = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>生成的代码预览</h3>
          <button class="btn btn--ghost btn--sm" @click="showPreview = false">关闭</button>
        </div>
        <pre class="code-block"><code>{{ previewCode }}</code></pre>
      </div>
    </div>

    <!-- NL Confirm Modal -->
    <div v-if="showNlConfirm && nlResult" class="modal-overlay" @click.self="showNlConfirm = false">
      <div class="modal-content" style="max-width: 560px;">
        <div class="modal-header">
          <h3>解析结果确认</h3>
          <button class="btn btn--ghost btn--sm" @click="showNlConfirm = false">关闭</button>
        </div>
        <div class="nl-confirm-body">
          <!-- Confidence -->
          <div class="nl-confidence">
            <span class="nl-confidence-label">理解度</span>
            <div class="nl-confidence-bar">
              <div
                class="nl-confidence-fill"
                :style="{
                  width: `${Math.round(nlResult.confidence * 100)}%`,
                  background: nlResult.confidence >= 0.7 ? '#16a34a' : nlResult.confidence >= 0.4 ? '#d97706' : '#b91c1c'
                }"
              />
            </div>
            <span class="nl-confidence-value">{{ Math.round(nlResult.confidence * 100) }}%</span>
          </div>

          <!-- Source text with highlights -->
          <div class="nl-source">
            <div class="nl-source-title">原文对照</div>
            <div class="nl-source-text">
              <span
                v-for="(seg, idx) in textSegments"
                :key="idx"
                :class="{
                  'nl-source-matched': seg.type === 'matched',
                  'nl-source-unmatched': seg.type === 'unmatched' || seg.type === 'gap'
                }"
                :title="seg.label"
              >{{ seg.text }}</span>
            </div>
          </div>

          <!-- Summary -->
          <div v-if="nlResult.pipeline_config" class="nl-summary">
            <div class="nl-summary-row">
              <span class="nl-summary-label">识别阶段</span>
              <span class="nl-summary-value">{{ nlResult.pipeline_config.stages.map((s: any) => STAGE_META[s.type]?.title || s.type).join('、') }}</span>
            </div>
          </div>

          <!-- Warnings -->
          <div v-if="nlResult.warnings.length" class="nl-warnings">
            <div v-for="(w, idx) in nlResult.warnings" :key="idx" class="nl-warning-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              {{ w }}
            </div>
          </div>

          <!-- Complex keywords -->
          <div v-if="nlResult.complex_keywords_found.length" class="nl-complex">
            <div class="nl-complex-title">以下功能需开发者模式实现：</div>
            <div class="nl-complex-tags">
              <span v-for="kw in nlResult.complex_keywords_found" :key="kw" class="nl-complex-tag">{{ kw }}</span>
            </div>
          </div>

          <!-- Unmatched -->
          <div v-if="nlResult.unmatched_spans.length" class="nl-unmatched">
            <div class="nl-unmatched-title">未理解表述：</div>
            <div class="nl-unmatched-list">
              <span
                v-for="(span, idx) in nlResult.unmatched_spans.slice(0, 5)"
                :key="idx"
                class="nl-unmatched-chip"
              >
                {{ nlOriginalText.slice(span[0], span[1]).trim() }}
              </span>
            </div>
          </div>

          <div v-if="!nlResult.pipeline_config" class="nl-empty">
            未能生成可识别的流水线配置，请尝试更清晰地描述指标和交易条件。
          </div>
        </div>

        <div class="nl-confirm-footer">
          <button class="btn btn--ghost" @click="showNlConfirm = false">取消</button>
          <button
            v-if="nlResult.pipeline_config"
            class="btn btn--primary"
            @click="applyNlResult"
            :disabled="nlResult.confidence < 0.3"
          >
            应用配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pipeline-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  height: 100%;
  overflow-y: auto;
}

.pipeline-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
}

.stages-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.stage-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.stage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  cursor: pointer;
  user-select: none;
  transition: background 0.15s ease;
}

.stage-header:hover {
  background: var(--bg-surface-hover);
}

.stage-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.85rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: var(--radius-md);
}

.nl-badge {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 5px;
  background: #f59e0b;
  color: #fff;
  border-radius: 4px;
  margin-left: 2px;
}

.stage-chevron {
  color: var(--text-muted);
  transition: transform 0.2s ease;
}

.stage-chevron--open {
  transform: rotate(180deg);
}

.stage-body {
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--border-subtle);
}

.toast {
  padding: var(--space-sm) var(--space-lg);
  background: var(--error-subtle, #fef2f2);
  color: var(--error, #b91c1c);
  font-size: 0.85rem;
  font-weight: 500;
  border-radius: var(--radius-md);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: var(--space-xl);
}

.modal-content {
  background: var(--bg-base);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--border-subtle);
}

.modal-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.code-block {
  flex: 1;
  overflow: auto;
  padding: var(--space-lg) var(--space-xl);
  margin: 0;
  background: var(--bg-base);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
  color: var(--text-secondary);
}

/* NL Input Card */
.nl-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-md) var(--space-lg);
}

.nl-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  color: var(--text-secondary);
}

.nl-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.nl-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-left: auto;
}

.nl-body {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
}

.nl-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  align-items: stretch;
  flex-shrink: 0;
}

.nl-textarea {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 0.85rem;
  line-height: 1.5;
  resize: vertical;
  font-family: inherit;
}

.nl-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

/* NL Confirm Modal */
.nl-confirm-body {
  padding: var(--space-lg) var(--space-xl);
  overflow-y: auto;
  max-height: 60vh;
}

.nl-confidence {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.nl-confidence-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.nl-confidence-bar {
  flex: 1;
  height: 8px;
  background: var(--border-subtle);
  border-radius: 999px;
  overflow: hidden;
}

.nl-confidence-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease;
}

.nl-confidence-value {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 40px;
  text-align: right;
}

.nl-source {
  margin-bottom: var(--space-lg);
}

.nl-source-title {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.nl-source-text {
  font-size: 0.85rem;
  line-height: 1.8;
  color: var(--text-primary);
  padding: var(--space-md);
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  white-space: pre-wrap;
  word-break: break-all;
}

.nl-source-matched {
  background: rgba(22, 163, 74, 0.12);
  border-radius: 3px;
  padding: 1px 2px;
  color: #14532d;
}

.nl-source-unmatched {
  color: var(--text-muted);
}

.nl-summary {
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
}

.nl-summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.nl-summary-label {
  color: var(--text-secondary);
}

.nl-summary-value {
  color: var(--text-primary);
  font-weight: 600;
}

.nl-warnings {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.nl-warning-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: rgba(217, 119, 6, 0.08);
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  color: #92400e;
  line-height: 1.5;
}

.nl-complex {
  margin-bottom: var(--space-lg);
}

.nl-complex-title {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.nl-complex-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.nl-complex-tag {
  font-size: 0.75rem;
  padding: 3px 10px;
  background: rgba(185, 28, 28, 0.08);
  color: #b91c1c;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.nl-unmatched {
  margin-bottom: var(--space-lg);
}

.nl-unmatched-title {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.nl-unmatched-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.nl-unmatched-chip {
  font-size: 0.75rem;
  padding: 3px 10px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  border-radius: var(--radius-sm);
}

.nl-empty {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-muted);
  font-size: 0.85rem;
}

.nl-confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-xl);
  border-top: 1px solid var(--border-subtle);
}

.nl-confirm-footer .btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

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
            @update:config="setStageConfig('init', $event)"
          />
          <PipelineStageIndicator
            v-else-if="stype === 'indicator'"
            :indicators="getStageConfig('indicator').indicators || []"
            @update:indicators="setStageConfig('indicator', { ...getStageConfig('indicator'), indicators: $event })"
          />
          <PipelineStageRisk
            v-else-if="stype === 'risk'"
            :checks="getStageConfig('risk').checks || []"
            @update:checks="setStageConfig('risk', { ...getStageConfig('risk'), checks: $event })"
          />
          <PipelineStageSignal
            v-else-if="stype === 'signal'"
            :groups="getStageConfig('signal').groups || []"
            :available-indicators="availableIndicators"
            @update:groups="setStageConfig('signal', { ...getStageConfig('signal'), groups: $event })"
          />
          <PipelineStageAction
            v-else-if="stype === 'action'"
            :rules="getStageConfig('action').rules || []"
            :signal-groups="signalGroups"
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
</style>

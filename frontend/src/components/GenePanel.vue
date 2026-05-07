<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { dnaApi, type StrategyDNASummary } from '@/api/dna'
import GeneTag from './GeneTag.vue'

const props = defineProps<{
  strategyId: string
}>()

const dna = ref<StrategyDNASummary | null>(null)
const loading = ref(false)
const error = ref('')
const expanded = ref(false)

async function loadDNA() {
  if (!props.strategyId) return
  loading.value = true
  error.value = ''
  try {
    dna.value = await dnaApi.getSummary(props.strategyId)
  } catch (e: any) {
    error.value = e.message
    dna.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.strategyId, () => {
  loadDNA()
}, { immediate: true })

const healthColor = (score: number) => {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#d97706'
  return '#92400e'
}

const healthLabel = (score: number) => {
  if (score >= 80) return '健康'
  if (score >= 60) return '一般'
  return '需关注'
}
</script>

<template>
  <div class="gene-panel">
    <div class="gene-panel-header" @click="expanded = !expanded">
      <div class="gene-panel-title">
        <span class="gene-panel-icon">🧬</span>
        <span>基因面板</span>
      </div>
      <div class="gene-panel-meta">
        <span v-if="dna" class="health-dot" :style="{ background: healthColor(dna.health_birth_score) }"></span>
        <span v-if="dna" class="health-text" :style="{ color: healthColor(dna.health_birth_score) }">
          {{ dna.health_birth_score }}% {{ healthLabel(dna.health_birth_score) }}
        </span>
        <span class="expand-icon">{{ expanded ? '▼' : '▶' }}</span>
      </div>
    </div>

    <div v-if="expanded" class="gene-panel-body">
      <div v-if="loading" class="gene-loading">测序中...</div>
      <div v-else-if="error" class="gene-error">{{ error }}</div>
      <div v-else-if="dna" class="gene-content">
        <div class="gene-scores">
          <div class="gene-score-item">
            <div class="gene-score-value" :style="{ color: healthColor(dna.health_birth_score) }">
              {{ dna.health_birth_score }}
            </div>
            <div class="gene-score-label">健康度</div>
          </div>
          <div class="gene-score-item">
            <div class="gene-score-value">{{ (dna.gene_diversity_score * 100).toFixed(0) }}%</div>
            <div class="gene-score-label">多样性</div>
          </div>
        </div>

        <div class="gene-layers">
          <div class="gene-layer" v-if="dna.feature_genes.length">
            <div class="gene-layer-label">特征层</div>
            <div class="gene-layer-tags">
              <GeneTag v-for="g in dna.feature_genes.slice(0, 4)" :key="g" :label="g" variant="feature" />
            </div>
          </div>
          <div class="gene-layer" v-if="dna.signal_genes.length">
            <div class="gene-layer-label">信号层</div>
            <div class="gene-layer-tags">
              <GeneTag v-for="g in dna.signal_genes.slice(0, 4)" :key="g" :label="g" variant="signal" />
            </div>
          </div>
        </div>
      </div>
      <div v-else class="gene-empty">
        保存策略后自动生成基因分析
      </div>
    </div>
  </div>
</template>

<style scoped>
.gene-panel {
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
}
.gene-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-xl);
  cursor: pointer;
  user-select: none;
  transition: background 0.15s ease;
}
.gene-panel-header:hover {
  background: var(--bg-surface-hover);
}
.gene-panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}
.gene-panel-icon {
  font-size: 1rem;
}
.gene-panel-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.8rem;
}
.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.health-text {
  font-weight: 500;
}
.expand-icon {
  color: var(--text-muted);
  font-size: 0.7rem;
  margin-left: var(--space-sm);
}
.gene-panel-body {
  padding: 0 var(--space-xl) var(--space-lg);
}
.gene-loading,
.gene-error,
.gene-empty {
  font-size: 0.85rem;
  color: var(--text-muted);
  padding: var(--space-md) 0;
}
.gene-error {
  color: var(--error);
}
.gene-scores {
  display: flex;
  gap: var(--space-xl);
  margin-bottom: var(--space-lg);
}
.gene-score-item {
  text-align: center;
}
.gene-score-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.gene-score-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.gene-layers {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.gene-layer-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.gene-layer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}
</style>

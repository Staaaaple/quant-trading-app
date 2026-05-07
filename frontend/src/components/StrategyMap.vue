<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { dnaApi, type StrategyDNASummary } from '@/api/dna'
import { strategyApi } from '@/api/strategy'
import GeneTag from './GeneTag.vue'

const props = defineProps<{
  showImport?: boolean
}>()

const strategies = ref<StrategyDNASummary[]>([])
const loading = ref(true)
const error = ref('')
const importing = ref<string | null>(null)
const importSuccess = ref<string | null>(null)

async function loadStrategies() {
  loading.value = true
  try {
    strategies.value = await dnaApi.listAll()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const families = computed(() => {
  const map: Record<string, StrategyDNASummary[]> = {}
  for (const s of strategies.value) {
    // Use backend family_name if available, fallback to id-based detection
    const family = s.family_name || _detectFamilyFallback(s.strategy_id)
    if (!map[family]) map[family] = []
    map[family]!.push(s)
  }
  return map
})

function _detectFamilyFallback(sid: string): string {
  if (sid.includes('dual_ma') || sid.includes('triple') || sid.includes('macd') || sid.includes('breakout') || sid.includes('ema')) {
    return '趋势跟踪家族'
  } else if (sid.includes('rsi') || sid.includes('kdj') || sid.includes('volume') || sid.includes('momentum_20d')) {
    return '动量家族'
  } else if (sid.includes('boll') || sid.includes('volatility')) {
    return '均值回归家族'
  } else if (sid.includes('pe_pb') || sid.includes('roe') || sid.includes('small') || sid.includes('momentum_value')) {
    return '多因子家族'
  } else if (sid.includes('atr') || sid.includes('position') || sid.includes('dynamic')) {
    return '风控增强家族'
  } else if (sid === 'builtin_weekly_picker') {
    return '系统内置'
  }
  return '其他'
}

const familyColors: Record<string, string> = {
  '趋势跟踪家族': '#16a34a',
  '动量家族': '#d97706',
  '均值回归家族': '#3b82f6',
  '多因子家族': '#8b5cf6',
  '风控增强家族': '#b91c1c',
  '系统内置': '#6b7280',
  '其他': '#6b7280',
}

function healthColor(score: number) {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#d97706'
  return '#92400e'
}

async function importStrategy(strategy: StrategyDNASummary) {
  if (!props.showImport) return
  importing.value = strategy.strategy_id
  try {
    // Get full strategy details
    const source = await strategyApi.get(strategy.strategy_id)
    // Create new strategy with modified ID
    const newId = `imported_${strategy.strategy_id}_${Date.now()}`
    await strategyApi.create({
      strategy_id: newId,
      name: `${source.name} (导入)`,
      code: source.code,
      type: source.type,
    })
    importSuccess.value = strategy.strategy_id
    setTimeout(() => importSuccess.value = null, 2000)
  } catch (e: any) {
    error.value = e.message
  } finally {
    importing.value = null
  }
}

onMounted(() => {
  loadStrategies()
})
</script>

<template>
  <div class="strategy-map">
    <div v-if="loading" class="loading">加载策略地图中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="map-content">
      <div v-for="(items, family) in families" :key="family" class="family-section">
        <div class="family-header">
          <span class="family-dot" :style="{ background: familyColors[family] || '#6b7280' }"></span>
          <h3 class="family-name">{{ family }}</h3>
          <span class="family-count">{{ items.length }} 个策略</span>
        </div>
        <div class="family-grid">
          <div
            v-for="s in items"
            :key="s.strategy_id"
            class="strategy-card"
            :class="{ imported: importSuccess === s.strategy_id }"
          >
            <div class="card-header">
              <div class="card-title">{{ s.name }}</div>
              <div class="card-health" :style="{ color: healthColor(s.health_birth_score) }">
                {{ s.health_birth_score }}%
              </div>
            </div>
            <div class="card-meta">
              <span class="meta-item">多样性 {{ (s.gene_diversity_score * 100).toFixed(0) }}%</span>
              <span class="meta-item">{{ s.feature_genes.length }} 特征基因</span>
              <span class="meta-item">{{ s.signal_genes.length }} 信号基因</span>
            </div>
            <div class="card-genes">
              <GeneTag
                v-for="g in s.feature_genes.slice(0, 3)"
                :key="g"
                :label="g"
                variant="feature"
              />
              <GeneTag
                v-for="g in s.signal_genes.slice(0, 2)"
                :key="g"
                :label="g"
                variant="signal"
              />
            </div>
            <div v-if="showImport" class="card-actions">
              <button
                class="btn btn--primary btn--sm"
                :disabled="importing === s.strategy_id"
                @click="importStrategy(s)"
              >
                {{ importing === s.strategy_id ? '导入中...' : (importSuccess === s.strategy_id ? '已导入!' : '导入策略') }}
              </button>
              <RouterLink
                :to="`/dna-report/${s.strategy_id}`"
                class="btn btn--ghost btn--sm"
              >
                基因报告
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.strategy-map {
  padding: var(--space-xl);
}
.loading, .error {
  text-align: center;
  padding: var(--space-3xl);
  color: var(--text-muted);
}
.error {
  color: var(--error);
}
.family-section {
  margin-bottom: var(--space-2xl);
}
.family-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--border-subtle);
}
.family-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.family-name {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.family-count {
  margin-left: auto;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.family-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-lg);
}
.strategy-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  transition: all 0.2s ease;
}
.strategy-card:hover {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.strategy-card.imported {
  border-color: var(--success);
  background: var(--success-subtle);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}
.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}
.card-health {
  font-size: 1.1rem;
  font-weight: 700;
}
.card-meta {
  display: flex;
  gap: var(--space-md);
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-bottom: var(--space-md);
}
.card-genes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
  min-height: 32px;
}
.card-actions {
  display: flex;
  gap: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-subtle);
}
</style>
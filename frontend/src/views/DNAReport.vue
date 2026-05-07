<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { dnaApi, type StrategyDNA, type StrategyPhylogeny } from '@/api/dna'
import GeneTag from '@/components/GeneTag.vue'

const route = useRoute()
const strategyId = route.params.strategy_id as string

const dna = ref<StrategyDNA | null>(null)
const phylogeny = ref<StrategyPhylogeny | null>(null)
const loading = ref(true)
const error = ref('')

async function loadDNA() {
  loading.value = true
  error.value = ''
  try {
    const [dnaData, phyloData] = await Promise.all([
      dnaApi.getDNA(strategyId),
      dnaApi.getPhylogeny(strategyId),
    ])
    dna.value = dnaData
    phylogeny.value = phyloData
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDNA()
})

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
  <div class="dna-report">
    <div v-if="loading" class="loading">加载基因报告中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="dna" class="report-content">
      <!-- Header -->
      <div class="report-header">
        <div class="report-title">
          <span class="dna-icon">🧬</span>
          <h2>基因报告</h2>
        </div>
        <div class="report-actions">
          <RouterLink to="/strategies" class="report-action-btn" title="编辑策略">
            <span>✏️</span> 编辑
          </RouterLink>
          <RouterLink to="/backtests" class="report-action-btn" title="回测">
            <span>📊</span> 回测
          </RouterLink>
          <RouterLink to="/paper-trading" class="report-action-btn" title="模拟盘">
            <span>📈</span> 模拟盘
          </RouterLink>
        </div>
        <div class="report-meta">
          <span class="strategy-id">{{ dna.strategy_id }}</span>
          <span class="version">测序版本 {{ dna.sequence_version }}</span>
        </div>
      </div>

      <!-- Health Score Card -->
      <div class="health-card">
        <div class="health-main">
          <div class="health-score" :style="{ color: healthColor(dna.health_birth_score) }">
            {{ dna.health_birth_score }}
          </div>
          <div class="health-label">健康度</div>
          <div class="health-status" :style="{ color: healthColor(dna.health_birth_score) }">
            {{ healthLabel(dna.health_birth_score) }}
          </div>
        </div>
        <div class="health-divider"></div>
        <div class="health-secondary">
          <div class="health-item">
            <div class="health-item-value">{{ (dna.gene_diversity_score * 100).toFixed(0) }}%</div>
            <div class="health-item-label">基因多样性</div>
          </div>
          <div class="health-item">
            <div class="health-item-value">{{ dna.inbreeding_coefficient }}</div>
            <div class="health-item-label">近亲系数</div>
          </div>
        </div>
      </div>

      <!-- Gene Layers -->
      <div class="gene-sections">
        <div class="gene-section">
          <div class="gene-section-header">
            <span class="gene-section-icon" style="color: #16a34a;">🧬</span>
            <h3>特征层基因</h3>
            <span class="gene-count">{{ dna.feature_genes.length }}</span>
          </div>
          <div class="gene-tags">
            <GeneTag
              v-for="g in dna.feature_genes"
              :key="g"
              :label="g"
              variant="feature"
            />
          </div>
          <p v-if="!dna.feature_genes.length" class="gene-empty">
            未检测到特征基因 — 策略可能未使用常见技术指标
          </p>
        </div>

        <div class="gene-section">
          <div class="gene-section-header">
            <span class="gene-section-icon" style="color: #d97706;">📡</span>
            <h3>信号层基因</h3>
            <span class="gene-count">{{ dna.signal_genes.length }}</span>
          </div>
          <div class="gene-tags">
            <GeneTag
              v-for="g in dna.signal_genes"
              :key="g"
              :label="g"
              variant="signal"
            />
          </div>
          <p v-if="!dna.signal_genes.length" class="gene-empty">
            未检测到信号基因
          </p>
        </div>

        <div class="gene-section">
          <div class="gene-section-header">
            <span class="gene-section-icon" style="color: #b91c1c;">🛡️</span>
            <h3>风控层基因</h3>
            <span class="gene-count">{{ dna.risk_genes.length }}</span>
          </div>
          <div class="gene-tags">
            <GeneTag
              v-for="g in dna.risk_genes"
              :key="g"
              :label="g"
              variant="risk"
            />
          </div>
          <p v-if="!dna.risk_genes.length" class="gene-empty">
            未检测到风控基因 — 建议增加止损或仓位管理逻辑
          </p>
        </div>

        <div class="gene-section">
          <div class="gene-section-header">
            <span class="gene-section-icon" style="color: #3b82f6;">⚡</span>
            <h3>执行层基因</h3>
            <span class="gene-count">{{ dna.execution_genes.length }}</span>
          </div>
          <div class="gene-tags">
            <GeneTag
              v-for="g in dna.execution_genes"
              :key="g"
              :label="g"
              variant="execution"
            />
          </div>
          <p v-if="!dna.execution_genes.length" class="gene-empty">
            未检测到执行层基因
          </p>
        </div>
      </div>

      <!-- Metabolic Profile -->
      <div class="metabolic-card">
        <div class="metabolic-header-row">
          <h3>代谢分析</h3>
          <span v-if="dna.metabolic_syndrome" class="syndrome-badge">
            代谢综合征
          </span>
        </div>
        <div class="metabolic-body">
          <div class="metabolic-item">
            <div class="metabolic-label">
              <span>信息代谢率</span>
              <span class="metabolic-value">{{ dna.metabolic_rate }}/天</span>
            </div>
            <div class="metabolic-bar-wrap">
              <div class="metabolic-bar">
                <div
                  class="metabolic-fill"
                  :style="{ width: `${dna.metabolic_rate * 100}%`, background: dna.metabolic_rate > 0.2 ? '#b91c1c' : dna.metabolic_rate > 0.08 ? '#d97706' : '#16a34a' }"
                ></div>
              </div>
              <span class="metabolic-hint">
                {{ dna.metabolic_rate > 0.2 ? '高频 — 极度依赖最新数据' : dna.metabolic_rate > 0.08 ? '中频 — 需要定期更新' : '低频 — 逻辑稳定' }}
              </span>
            </div>
          </div>
          <div class="metabolic-item">
            <div class="metabolic-label">
              <span>生态位宽度</span>
              <span class="metabolic-value">{{ (dna.niche_width * 100).toFixed(0) }}%</span>
            </div>
            <div class="metabolic-bar-wrap">
              <div class="metabolic-bar">
                <div
                  class="metabolic-fill"
                  :style="{ width: `${dna.niche_width * 100}%`, background: dna.niche_width > 0.6 ? '#16a34a' : dna.niche_width > 0.3 ? '#d97706' : '#92400e' }"
                ></div>
              </div>
              <span class="metabolic-hint">
                {{ dna.niche_width > 0.6 ? '通用型 — 适应力强' : dna.niche_width > 0.3 ? '一般 — 部分场景适用' : '专精型 — 生态位狭窄' }}
              </span>
            </div>
          </div>
          <div v-if="dna.metabolic_markers?.length" class="metabolic-markers">
            <h4>代谢异常标记</h4>
            <div class="marker-tags">
              <span v-for="marker in dna.metabolic_markers" :key="marker" class="marker-tag">
                {{ marker }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Lifespan Prediction -->
      <div v-if="dna" class="lifespan-card">
        <div class="lifespan-header-row">
          <h3>寿命预测</h3>
          <span :class="['phase-badge', `phase-${dna.lifespan_phase}`]">
            {{ dna.lifespan_phase_label || { young: '年轻', mature: '成熟', aging: '衰老', endangered: '濒危' }[dna.lifespan_phase] || '成熟' }}
          </span>
        </div>
        <div class="lifespan-body">
          <div class="lifespan-main">
            <div class="lifespan-number">{{ dna.lifespan_months }}</div>
            <div class="lifespan-unit">个月</div>
            <div class="lifespan-label">预计剩余寿命</div>
          </div>
          <div class="lifespan-divider"></div>
          <div class="lifespan-details">
            <div class="lifespan-item">
              <div class="lifespan-item-value" :style="{ color: dna.aging_velocity > 0.15 ? '#b91c1c' : dna.aging_velocity > 0.08 ? '#d97706' : '#16a34a' }">
                {{ (dna.aging_velocity * 100).toFixed(1) }}%
              </div>
              <div class="lifespan-item-label">月老化速度</div>
            </div>
            <div class="lifespan-item">
              <div class="lifespan-item-value">{{ dna.lifespan_phase_label || { young: '年轻', mature: '成熟', aging: '衰老', endangered: '濒危' }[dna.lifespan_phase] || '成熟' }}</div>
              <div class="lifespan-item-label">当前阶段</div>
            </div>
          </div>
        </div>
        <div v-if="dna.lifespan_recommendations?.length" class="lifespan-recommendations">
          <h4>优化建议</h4>
          <ul>
            <li v-for="rec in dna.lifespan_recommendations" :key="rec">{{ rec }}</li>
          </ul>
        </div>
      </div>

      <!-- Family & Phylogeny -->
      <div v-if="phylogeny" class="family-card">
        <div class="family-header-row">
          <h3>家族与系统发育</h3>
          <span v-if="phylogeny.inbreeding_warning" class="inbreeding-badge">
            近亲警告
          </span>
        </div>
        <div class="family-body">
          <div class="family-info">
            <p><strong>家族:</strong> {{ phylogeny.family_name || '未归类' }}</p>
            <p><strong>家族 ID:</strong> {{ phylogeny.family_id || '-' }}</p>
            <p><strong>同质性风险:</strong> {{ (phylogeny.homogeneity_risk * 100).toFixed(1) }}%</p>
          </div>
          <div v-if="phylogeny.relatives?.length" class="relatives-section">
            <h4>最近亲属</h4>
            <div class="relatives-list">
              <div
                v-for="r in phylogeny.relatives"
                :key="r.strategy_id"
                class="relative-item"
              >
                <div class="relative-info">
                  <RouterLink
                    :to="`/dna-report/${r.strategy_id}`"
                    class="relative-name"
                  >
                    {{ r.name }}
                  </RouterLink>
                  <span class="relative-id">{{ r.strategy_id }}</span>
                </div>
                <div class="relative-similarity">
                  <div class="similarity-bar">
                    <div
                      class="similarity-fill"
                      :style="{ width: `${r.similarity * 100}%` }"
                    ></div>
                  </div>
                  <span class="similarity-value">{{ (r.similarity * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sequencing Metadata -->
      <div class="meta-footer">
        <span>测序时间: {{ new Date(dna.sequenced_at).toLocaleString() }}</span>
        <span>状态: {{ dna.status }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dna-report {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-2xl);
}

.loading, .error {
  text-align: center;
  padding: var(--space-3xl);
  color: var(--text-muted);
}

.error {
  color: var(--error);
}

.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-md);
  margin-bottom: var(--space-2xl);
}

.report-header-left {
  flex: 1;
  min-width: 0;
}

.report-title {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-sm);
}

.report-title h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.dna-icon {
  font-size: 1.5rem;
}

.report-meta {
  display: flex;
  gap: var(--space-lg);
  font-size: 0.85rem;
  color: var(--text-muted);
}

.strategy-id {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.report-actions {
  display: flex;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.report-action-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s ease;
}

.report-action-btn:hover {
  border-color: var(--border-focus);
  color: var(--text-primary);
  background: var(--bg-surface-hover);
}

/* Health Card */
.health-card {
  display: flex;
  align-items: center;
  gap: var(--space-2xl);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
  margin-bottom: var(--space-2xl);
}

.health-main {
  text-align: center;
  min-width: 120px;
}

.health-score {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1;
}

.health-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: var(--space-sm);
}

.health-status {
  font-size: 0.9rem;
  font-weight: 600;
  margin-top: 2px;
}

.health-divider {
  width: 1px;
  height: 80px;
  background: var(--border-subtle);
}

.health-secondary {
  display: flex;
  gap: var(--space-2xl);
}

.health-item {
  text-align: center;
}

.health-item-value {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
}

.health-item-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Gene Sections */
.gene-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.gene-section {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.gene-section-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.gene-section-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.gene-section-icon {
  font-size: 1.1rem;
}

.gene-count {
  margin-left: auto;
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--bg-base);
  padding: 2px 8px;
  border-radius: 999px;
}

.gene-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.gene-empty {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-style: italic;
  padding: var(--space-sm) 0;
}

/* Family Card */
.family-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.family-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.family-header-row h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.inbreeding-badge {
  background: var(--error-bg, rgba(185, 28, 28, 0.1));
  color: var(--error, #b91c1c);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
}

.family-body {
  display: grid;
  gap: var(--space-xl);
}

.family-info p {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm) 0;
}

.family-info p:last-child {
  margin-bottom: 0;
}

/* Relatives */
.relatives-section h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--space-md) 0;
}

.relatives-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.relative-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-base);
  border-radius: var(--radius-md);
}

.relative-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.relative-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  text-decoration: none;
}

.relative-name:hover {
  color: var(--accent);
}

.relative-id {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.relative-similarity {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.similarity-bar {
  width: 80px;
  height: 6px;
  background: var(--border-subtle);
  border-radius: 999px;
  overflow: hidden;
}

.similarity-fill {
  height: 100%;
  background: var(--accent, #16a34a);
  border-radius: 999px;
  transition: width 0.4s ease;
}

.similarity-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  min-width: 40px;
  text-align: right;
}

/* Metabolic Card */
.metabolic-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.metabolic-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.metabolic-header-row h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.syndrome-badge {
  background: rgba(185, 28, 28, 0.1);
  color: #b91c1c;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
}

.metabolic-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.metabolic-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.metabolic-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metabolic-label span:first-child {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
}

.metabolic-value {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.metabolic-bar-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metabolic-bar {
  width: 100%;
  height: 8px;
  background: var(--border-subtle);
  border-radius: 999px;
  overflow: hidden;
}

.metabolic-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.metabolic-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.metabolic-markers h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--space-sm) 0;
}

.marker-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.marker-tag {
  font-size: 0.78rem;
  font-weight: 500;
  color: #92400e;
  background: rgba(146, 64, 14, 0.08);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
}

/* Lifespan Card */
.lifespan-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.lifespan-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.lifespan-header-row h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.phase-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
}

.phase-young {
  background: rgba(22, 163, 74, 0.1);
  color: #16a34a;
}

.phase-mature {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.phase-aging {
  background: rgba(217, 119, 6, 0.1);
  color: #d97706;
}

.phase-endangered {
  background: rgba(185, 28, 28, 0.1);
  color: #b91c1c;
}

.lifespan-body {
  display: flex;
  align-items: center;
  gap: var(--space-2xl);
  margin-bottom: var(--space-lg);
}

.lifespan-main {
  text-align: center;
  min-width: 120px;
}

.lifespan-number {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1;
  color: var(--text-primary);
}

.lifespan-unit {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.lifespan-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.lifespan-divider {
  width: 1px;
  height: 80px;
  background: var(--border-subtle);
}

.lifespan-details {
  display: flex;
  gap: var(--space-2xl);
}

.lifespan-item {
  text-align: center;
}

.lifespan-item-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
}

.lifespan-item-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.lifespan-recommendations h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--space-sm) 0;
}

.lifespan-recommendations ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.lifespan-recommendations li {
  font-size: 0.85rem;
  color: var(--text-secondary);
  padding: 6px 0;
  padding-left: 20px;
  position: relative;
}

.lifespan-recommendations li::before {
  content: '→';
  position: absolute;
  left: 0;
  color: var(--accent, #16a34a);
  font-weight: 600;
}

/* Meta Footer */
.meta-footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-muted);
  padding-top: var(--space-xl);
  border-top: 1px solid var(--border-subtle);
}
</style>
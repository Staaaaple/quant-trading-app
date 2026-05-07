<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, GraphChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, RadarComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { dnaApi, type EcosystemOverview, type StrategyDNASummary } from '@/api/dna'
import StrategyMap from '@/components/StrategyMap.vue'

use([CanvasRenderer, BarChart, PieChart, GraphChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, RadarComponent, TitleComponent])

const ecosystem = ref<EcosystemOverview | null>(null)
const strategies = ref<StrategyDNASummary[]>([])
const loading = ref(true)
const error = ref('')

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [eco, all] = await Promise.all([
      dnaApi.getEcosystem(),
      dnaApi.listAll(),
    ])
    ecosystem.value = eco
    strategies.value = all
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

const hasUserStrategies = computed(() => {
  return strategies.value.some(s => !s.strategy_id.startsWith('preset_') && !s.strategy_id.startsWith('builtin_'))
})

// Ideal ecosystem demo data (shown when user has no strategies)
const idealEcosystem = {
  total_strategies: 22,
  family_count: 7,
  avg_health_score: 66.2,
  avg_diversity: 49.4,
  inbreeding_risk_count: 20,
}

const familyColors: Record<string, string> = {
  '趋势跟踪家族': '#16a34a',
  '动量家族': '#d97706',
  '均值回归家族': '#3b82f6',
  '多因子家族': '#8b5cf6',
  '风控增强家族': '#b91c1c',
  '系统内置': '#6b7280',
  '其他': '#9ca3af',
}

const phaseColors: Record<string, string> = {
  '年轻(36+)': '#16a34a',
  '成熟(12-36)': '#3b82f6',
  '衰老(3-12)': '#d97706',
  '濒危(<3)': '#b91c1c',
}

const familyChartOption = computed(() => {
  if (!ecosystem.value) return {}
  const data = ecosystem.value.family_distribution
  return {
    grid: { left: 16, right: 32, top: 16, bottom: 8 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 12, color: '#4b5563' },
    },
    tooltip: { trigger: 'axis', formatter: '{b}: {c}' },
    series: [{
      type: 'bar',
      data: data.map(d => ({
        value: d.count,
        itemStyle: { color: familyColors[d.name] || '#9ca3af', borderRadius: [0, 4, 4, 0] },
      })),
      barWidth: 18,
      label: { show: true, position: 'right', fontSize: 12, color: '#6b7280' },
    }],
  }
})

const lifespanChartOption = computed(() => {
  if (!ecosystem.value) return {}
  const dist = ecosystem.value.lifespan_distribution
  return {
    color: ['#16a34a', '#3b82f6', '#d97706', '#b91c1c'],
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { show: false },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
      },
      labelLine: { show: false },
      data: Object.entries(dist).map(([name, value]) => ({ name, value })),
    }],
  }
})

const metabolicChartOption = computed(() => {
  if (!ecosystem.value) return {}
  const data = ecosystem.value.metabolic_ranking.slice(0, 10)
  return {
    grid: { left: 16, right: 48, top: 16, bottom: 8 },
    xAxis: { type: 'value', show: false, max: 0.4 },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 11, color: '#4b5563', width: 100, overflow: 'truncate' },
    },
    tooltip: { trigger: 'axis', formatter: '{b}: {c}/天' },
    series: [{
      type: 'bar',
      data: data.map(d => ({
        value: d.metabolic_rate,
        itemStyle: {
          color: d.metabolic_rate > 0.2 ? '#b91c1c' : d.metabolic_rate > 0.1 ? '#d97706' : '#16a34a',
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barWidth: 14,
      label: { show: true, position: 'right', fontSize: 11, color: '#6b7280', formatter: '{c}' },
    }],
  }
})

const radarChartOption = computed(() => {
  if (!ecosystem.value || !ecosystem.value.family_radar.length) return {}
  return {
    tooltip: { trigger: 'item' },
    legend: {
      data: ecosystem.value.family_radar.map(f => f.name),
      bottom: 0,
      textStyle: { fontSize: 11, color: '#6b7280' },
      itemWidth: 10,
      itemHeight: 10,
    },
    radar: {
      indicator: ecosystem.value.radar_indicators,
      radius: '65%',
      center: ['50%', '48%'],
      axisName: { fontSize: 11, color: '#6b7280' },
      splitArea: { areaStyle: { color: ['rgba(248,250,252,0.8)', 'rgba(241,245,249,0.6)'] } },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
    },
    series: [{
      type: 'radar',
      data: ecosystem.value.family_radar.map(f => ({
        value: f.value,
        name: f.name,
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 4,
      })),
    }],
  }
})

const familyTreeOption = computed(() => {
  if (!ecosystem.value) return {}
  const network = ecosystem.value.family_network
  if (!network.nodes.length) return {}

  const categories = Array.from(new Set(network.nodes.map(n => n.family))).map(name => ({
    name,
    itemStyle: { color: familyColors[name] || '#9ca3af' },
  }))

  return {
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const d = params.data
          return `${d.name}<br/>家族: ${d.family}<br/>健康度: ${d.health}<br/>寿命: ${d.lifespan}月`
        }
        return `${params.data.source} ↔ ${params.data.target}<br/>相似度: ${(params.data.value * 100).toFixed(1)}%`
      },
    },
    legend: {
      data: categories.map(c => c.name),
      top: 8,
      textStyle: { fontSize: 11, color: '#6b7280' },
      itemWidth: 10,
      itemHeight: 10,
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: network.nodes.map(n => ({
        ...n,
        category: categories.findIndex(c => c.name === n.family),
        itemStyle: { color: familyColors[n.family] || '#9ca3af' },
        label: { show: n.symbolSize > 18, fontSize: 10, color: '#374151' },
      })),
      links: network.links.map(l => ({
        ...l,
        lineStyle: { color: '#cbd5e1', width: 1 + l.value * 2, curveness: 0.1 },
      })),
      categories,
      roam: true,
      draggable: true,
      force: {
        repulsion: 300,
        edgeLength: [40, 120],
        gravity: 0.1,
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 3 },
      },
    }],
  }
})

function healthColor(score: number) {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#d97706'
  return '#92400e'
}

function phaseColor(phase: string) {
  if (phase === 'young') return '#16a34a'
  if (phase === 'mature') return '#3b82f6'
  if (phase === 'aging') return '#d97706'
  return '#b91c1c'
}

function phaseLabel(phase: string) {
  const labels: Record<string, string> = { young: '年轻', mature: '成熟', aging: '衰老', endangered: '濒危' }
  return labels[phase] || phase
}
</script>

<template>
  <div class="eco-dashboard">
    <!-- Loading / Error -->
    <div v-if="loading" class="eco-loading">加载生态数据中...</div>
    <div v-else-if="error" class="eco-error">{{ error }}</div>

    <!-- Empty State: No user strategies yet -->
    <template v-else-if="!hasUserStrategies">
      <div class="eco-hero">
        <div class="eco-hero-content">
          <h1 class="eco-hero-title">
            <span class="eco-hero-icon">🌿</span>
            策略生态系统
          </h1>
          <p class="eco-hero-desc">
            你的生态尚为空。下方是预设策略群落的理想生态预览。导入策略后，仪表盘将显示你的真实生态数据。
          </p>
        </div>
        <RouterLink to="/strategy-map" class="btn btn--primary">
          从策略地图导入
        </RouterLink>
      </div>

      <!-- Preview Stats -->
      <div class="eco-kpi-row">
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" style="color: #16a34a;">🧬</div>
          <div class="eco-kpi-value">{{ idealEcosystem.total_strategies }}</div>
          <div class="eco-kpi-label">预设策略库</div>
        </div>
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" style="color: #8b5cf6;">🏛️</div>
          <div class="eco-kpi-value">{{ idealEcosystem.family_count }}</div>
          <div class="eco-kpi-label">基因家族</div>
        </div>
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" style="color: #d97706;">💚</div>
          <div class="eco-kpi-value" style="color: #d97706;">{{ idealEcosystem.avg_health_score }}</div>
          <div class="eco-kpi-label">平均健康度</div>
        </div>
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" style="color: #b91c1c;">⚠️</div>
          <div class="eco-kpi-value" style="color: #b91c1c;">{{ idealEcosystem.inbreeding_risk_count }}</div>
          <div class="eco-kpi-label">近亲风险</div>
        </div>
      </div>

      <div class="eco-preview-note">
        <span class="eco-preview-badge">预览</span>
        <span>导入策略后，此处将显示你的真实生态仪表盘</span>
      </div>

      <!-- Strategy Map (read-only preview) -->
      <div class="eco-map-section">
        <h2 class="eco-section-title">
          <span>🗺️</span> 预设策略地图
        </h2>
        <StrategyMap />
      </div>
    </template>

    <!-- Dashboard: User has strategies -->
    <template v-else-if="ecosystem">
      <div class="eco-hero">
        <div class="eco-hero-content">
          <h1 class="eco-hero-title">
            <span class="eco-hero-icon">🌿</span>
            策略生态系统
          </h1>
          <p class="eco-hero-desc">
            观察你的策略群落。{{ ecosystem.total_strategies }} 个策略有机体分布在 {{ ecosystem.family_count }} 个基因家族中。
          </p>
        </div>
        <RouterLink to="/strategy-map" class="btn btn--primary">
          浏览策略地图
        </RouterLink>
      </div>

      <!-- KPI Row -->
      <div class="eco-kpi-row">
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" style="color: #16a34a;">🧬</div>
          <div class="eco-kpi-value">{{ ecosystem.total_strategies }}</div>
          <div class="eco-kpi-label">策略有机体</div>
        </div>
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" style="color: #8b5cf6;">🏛️</div>
          <div class="eco-kpi-value">{{ ecosystem.family_count }}</div>
          <div class="eco-kpi-label">基因家族</div>
        </div>
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" :style="{ color: healthColor(ecosystem.avg_health_score) }">💚</div>
          <div class="eco-kpi-value" :style="{ color: healthColor(ecosystem.avg_health_score) }">
            {{ ecosystem.avg_health_score }}
          </div>
          <div class="eco-kpi-label">平均健康度</div>
        </div>
        <div class="eco-kpi-card">
          <div class="eco-kpi-icon" :style="{ color: ecosystem.endangered_count > 0 ? '#b91c1c' : '#16a34a' }">
            {{ ecosystem.endangered_count > 0 ? '⏳' : '✅' }}
          </div>
          <div class="eco-kpi-value" :style="{ color: ecosystem.endangered_count > 0 ? '#b91c1c' : '#16a34a' }">
            {{ ecosystem.avg_lifespan }}
          </div>
          <div class="eco-kpi-label">平均寿命（月）</div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="eco-charts-row">
        <div class="eco-chart-card">
          <h3 class="eco-chart-title">家族分布</h3>
          <VChart :option="familyChartOption" autoresize style="width: 100%; height: 240px;" />
        </div>
        <div class="eco-chart-card">
          <h3 class="eco-chart-title">寿命阶段分布</h3>
          <div class="eco-pie-wrap">
            <VChart :option="lifespanChartOption" autoresize style="width: 100%; height: 220px;" />
            <div class="eco-pie-legend">
              <div class="eco-legend-item">
                <span class="eco-legend-dot" style="background: #16a34a;"></span>
                <span>年轻 {{ ecosystem.lifespan_distribution['年轻(36+)'] || 0 }}</span>
              </div>
              <div class="eco-legend-item">
                <span class="eco-legend-dot" style="background: #3b82f6;"></span>
                <span>成熟 {{ ecosystem.lifespan_distribution['成熟(12-36)'] || 0 }}</span>
              </div>
              <div class="eco-legend-item">
                <span class="eco-legend-dot" style="background: #d97706;"></span>
                <span>衰老 {{ ecosystem.lifespan_distribution['衰老(3-12)'] || 0 }}</span>
              </div>
              <div class="eco-legend-item">
                <span class="eco-legend-dot" style="background: #b91c1c;"></span>
                <span>濒危 {{ ecosystem.lifespan_distribution['濒危(<3)'] || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Phase 4: Analysis Row -->
      <div class="eco-analysis-row">
        <div class="eco-chart-card">
          <h3 class="eco-chart-title">代谢率排名（Top 10）</h3>
          <VChart :option="metabolicChartOption" autoresize style="width: 100%; height: 280px;" />
        </div>
        <div class="eco-chart-card">
          <h3 class="eco-chart-title">家族竞争雷达</h3>
          <VChart :option="radarChartOption" autoresize style="width: 100%; height: 280px;" />
        </div>
      </div>

      <!-- Phase 4: Family Tree -->
      <div class="eco-tree-card">
        <h3 class="eco-chart-title">策略家族关系网络</h3>
        <p class="eco-tree-hint">节点大小代表健康度，连线粗细代表基因相似度。可拖拽、缩放。</p>
        <VChart :option="familyTreeOption" autoresize style="width: 100%; height: 400px;" />
      </div>

      <!-- Bottom Row -->
      <div class="eco-bottom-row">
        <!-- Low Health Alert -->
        <div class="eco-panel">
          <div class="eco-panel-header">
            <h3 class="eco-panel-title">
              <span class="eco-panel-icon" style="color: #92400e;">🍂</span>
              需关注策略
            </h3>
            <span class="eco-panel-count">{{ ecosystem.low_health_strategies.length }}</span>
          </div>
          <div v-if="ecosystem.low_health_strategies.length" class="eco-alert-list">
            <div
              v-for="s in ecosystem.low_health_strategies"
              :key="s.strategy_id"
              class="eco-alert-item"
            >
              <RouterLink :to="`/dna-report/${s.strategy_id}`" class="eco-alert-main">
                <div class="eco-alert-info">
                  <span class="eco-alert-name">{{ s.name }}</span>
                  <span class="eco-alert-family">{{ s.family_name || '未归类' }}</span>
                </div>
                <div class="eco-alert-health">
                  <div class="eco-alert-bar">
                    <div class="eco-alert-fill" :style="{ width: `${s.health_birth_score}%`, background: healthColor(s.health_birth_score) }"></div>
                  </div>
                  <span class="eco-alert-score">{{ s.health_birth_score }}</span>
                </div>
              </RouterLink>
              <div class="eco-alert-actions">
                <RouterLink to="/strategies" class="eco-action-btn" title="编辑策略">✏️</RouterLink>
                <RouterLink to="/backtests" class="eco-action-btn" title="回测">📊</RouterLink>
                <RouterLink to="/paper-trading" class="eco-action-btn" title="模拟盘">📈</RouterLink>
              </div>
            </div>
          </div>
          <div v-else class="eco-empty">所有策略健康度良好</div>
        </div>

        <!-- Lifespan Alert -->
        <div class="eco-panel">
          <div class="eco-panel-header">
            <h3 class="eco-panel-title">
              <span class="eco-panel-icon" style="color: #b91c1c;">⏳</span>
              寿命预警
            </h3>
            <span v-if="ecosystem.endangered_count > 0" class="eco-panel-count">{{ ecosystem.endangered_count }}</span>
          </div>
          <div v-if="ecosystem.short_lifespan_strategies.length" class="eco-alert-list">
            <div
              v-for="s in ecosystem.short_lifespan_strategies"
              :key="s.strategy_id"
              class="eco-alert-item"
            >
              <RouterLink :to="`/dna-report/${s.strategy_id}`" class="eco-alert-main">
                <div class="eco-alert-info">
                  <span class="eco-alert-name">{{ s.name }}</span>
                  <span class="eco-alert-family">{{ s.family_name || '未归类' }}</span>
                </div>
                <div class="eco-alert-health">
                  <span :style="{ color: s.lifespan_months < 3 ? '#b91c1c' : '#d97706', fontWeight: 700, fontSize: '0.85rem' }">
                    {{ s.lifespan_months }}月
                  </span>
                </div>
              </RouterLink>
              <div class="eco-alert-actions">
                <RouterLink to="/strategies" class="eco-action-btn" title="编辑策略">✏️</RouterLink>
                <RouterLink to="/backtests" class="eco-action-btn" title="回测">📊</RouterLink>
                <RouterLink to="/paper-trading" class="eco-action-btn" title="模拟盘">📈</RouterLink>
              </div>
            </div>
          </div>
          <div v-else class="eco-empty">所有策略寿命健康</div>
        </div>

        <!-- Strategy Graveyard -->
        <div class="eco-panel">
          <div class="eco-panel-header">
            <h3 class="eco-panel-title">
              <span class="eco-panel-icon" style="color: #6b7280;">🪦</span>
              策略墓地
            </h3>
          </div>
          <div v-if="ecosystem.endangered_count > 0" class="eco-alert-list">
            <div
              v-for="s in ecosystem.short_lifespan_strategies.filter(x => x.lifespan_months < 3)"
              :key="s.strategy_id"
              class="eco-alert-item"
            >
              <RouterLink :to="`/dna-report/${s.strategy_id}`" class="eco-alert-main">
                <div class="eco-alert-info">
                  <span class="eco-alert-name">{{ s.name }}</span>
                  <span class="eco-alert-family">{{ s.family_name || '未归类' }}</span>
                </div>
                <span class="eco-grave-badge">濒危</span>
              </RouterLink>
              <div class="eco-alert-actions">
                <RouterLink to="/strategies" class="eco-action-btn" title="编辑策略">✏️</RouterLink>
                <RouterLink to="/backtests" class="eco-action-btn" title="回测">📊</RouterLink>
                <RouterLink to="/paper-trading" class="eco-action-btn" title="模拟盘">📈</RouterLink>
              </div>
            </div>
          </div>
          <div v-else-if="ecosystem.short_lifespan_strategies.length" class="eco-alert-list">
            <div
              v-for="s in ecosystem.short_lifespan_strategies"
              :key="s.strategy_id"
              class="eco-alert-item"
            >
              <RouterLink :to="`/dna-report/${s.strategy_id}`" class="eco-alert-main">
                <div class="eco-alert-info">
                  <span class="eco-alert-name">{{ s.name }}</span>
                  <span class="eco-alert-family">{{ s.family_name || '未归类' }}</span>
                </div>
                <span class="eco-aging-badge">{{ s.lifespan_months }}月</span>
              </RouterLink>
              <div class="eco-alert-actions">
                <RouterLink to="/strategies" class="eco-action-btn" title="编辑策略">✏️</RouterLink>
                <RouterLink to="/backtests" class="eco-action-btn" title="回测">📊</RouterLink>
                <RouterLink to="/paper-trading" class="eco-action-btn" title="模拟盘">📈</RouterLink>
              </div>
            </div>
          </div>
          <div v-else class="eco-empty">
            <p>暂无濒危策略</p>
            <p class="eco-grave-hint">策略墓地收录寿命极短（&lt;3月）或已失效的策略</p>
          </div>
        </div>

        <!-- Quick Nav + Recent -->
        <div class="eco-panel">
          <div class="eco-panel-header">
            <h3 class="eco-panel-title">
              <span class="eco-panel-icon" style="color: #16a34a;">🌱</span>
              最新加入
            </h3>
          </div>
          <div class="eco-recent-list">
            <div
              v-for="s in ecosystem.recent_strategies"
              :key="s.strategy_id"
              class="eco-recent-item"
            >
              <RouterLink :to="`/dna-report/${s.strategy_id}`" class="eco-recent-main">
                <div class="eco-recent-info">
                  <span class="eco-recent-name">{{ s.name }}</span>
                  <span class="eco-recent-family">{{ s.family_name || '未归类' }}</span>
                </div>
                <span class="eco-recent-health" :style="{ color: healthColor(s.health_birth_score) }">
                  {{ s.health_birth_score }}
                </span>
              </RouterLink>
              <div class="eco-alert-actions">
                <RouterLink to="/strategies" class="eco-action-btn" title="编辑策略">✏️</RouterLink>
                <RouterLink to="/backtests" class="eco-action-btn" title="回测">📊</RouterLink>
                <RouterLink to="/paper-trading" class="eco-action-btn" title="模拟盘">📈</RouterLink>
              </div>
            </div>
          </div>
          <div class="eco-quick-nav">
            <RouterLink to="/strategy-map" class="eco-nav-btn">
              <span>🗺️</span> 策略地图
            </RouterLink>
            <RouterLink to="/backtests" class="eco-nav-btn">
              <span>📊</span> 回测中心
            </RouterLink>
            <RouterLink to="/paper-trading" class="eco-nav-btn">
              <span>📈</span> 模拟盘
            </RouterLink>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.eco-dashboard {
  padding: 0;
}

/* Hero */
.eco-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-xl);
  margin-bottom: var(--space-3xl);
  padding-bottom: var(--space-xl);
  border-bottom: 1px solid var(--border-subtle);
}

.eco-hero-title {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
  letter-spacing: -0.02em;
}

.eco-hero-icon {
  font-size: 1.4rem;
}

.eco-hero-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
  max-width: 480px;
  line-height: 1.5;
}

/* Preview Note */
.eco-preview-note {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-2xl);
  padding: var(--space-md) var(--space-lg);
  background: rgba(22, 163, 74, 0.06);
  border: 1px solid rgba(22, 163, 74, 0.15);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.eco-preview-badge {
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
  background: #16a34a;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Map Section */
.eco-map-section {
  margin-bottom: var(--space-2xl);
}

.eco-section-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-lg) 0;
}

/* KPI */
.eco-kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-lg);
  margin-bottom: var(--space-2xl);
}

.eco-kpi-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  text-align: center;
  transition: all 0.2s ease;
}

.eco-kpi-card:hover {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-sm);
}

.eco-kpi-icon {
  font-size: 1.4rem;
  margin-bottom: var(--space-sm);
}

.eco-kpi-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: var(--space-xs);
}

.eco-kpi-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}

/* Charts */
.eco-charts-row {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.eco-analysis-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.eco-chart-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.eco-chart-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
  letter-spacing: -0.01em;
}

.eco-pie-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
}

.eco-pie-legend {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  min-width: 100px;
}

.eco-legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.eco-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Family Tree */
.eco-tree-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  margin-bottom: var(--space-2xl);
}

.eco-tree-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: -8px 0 var(--space-md) 0;
}

/* Bottom Row */
.eco-bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: var(--space-xl);
}

.eco-panel {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.eco-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}

.eco-panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.eco-panel-icon {
  font-size: 1.1rem;
}

.eco-panel-count {
  font-size: 0.75rem;
  font-weight: 600;
  color: #92400e;
  background: rgba(146, 64, 14, 0.08);
  padding: 2px 10px;
  border-radius: 999px;
}

/* Alert list */
.eco-alert-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.eco-alert-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-base);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: background 0.15s ease;
}

.eco-alert-item:hover {
  background: var(--bg-surface-hover);
}

.eco-alert-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.eco-alert-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.eco-alert-family {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.eco-alert-health {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.eco-alert-bar {
  width: 60px;
  height: 5px;
  background: var(--border-subtle);
  border-radius: 999px;
  overflow: hidden;
}

.eco-alert-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.eco-alert-score {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  min-width: 32px;
  text-align: right;
}

.eco-grave-badge {
  font-size: 0.7rem;
  font-weight: 600;
  color: #b91c1c;
  background: rgba(185, 28, 28, 0.08);
  padding: 2px 8px;
  border-radius: 999px;
}

.eco-aging-badge {
  font-size: 0.7rem;
  font-weight: 600;
  color: #d97706;
  background: rgba(217, 119, 6, 0.08);
  padding: 2px 8px;
  border-radius: 999px;
}

.eco-grave-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: var(--space-sm);
}

/* Alert item with actions */
.eco-alert-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  flex: 1;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}

.eco-alert-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.eco-alert-item:hover .eco-alert-actions {
  opacity: 1;
}

.eco-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  text-decoration: none;
  transition: all 0.15s ease;
  cursor: pointer;
}

.eco-action-btn:hover {
  background: var(--bg-surface-hover);
}

/* Recent list */
.eco-recent-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-xl);
}

.eco-recent-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-base);
  border-radius: var(--radius-md);
  transition: background 0.15s ease;
}

.eco-recent-item:hover {
  background: var(--bg-surface-hover);
}

.eco-recent-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  flex: 1;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}

.eco-recent-item:hover .eco-alert-actions {
  opacity: 1;
}

.eco-recent-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.eco-recent-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.eco-recent-family {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.eco-recent-health {
  font-size: 0.85rem;
  font-weight: 700;
  min-width: 40px;
  text-align: right;
}

/* Quick Nav */
.eco-quick-nav {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-subtle);
}

.eco-nav-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
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

.eco-nav-btn:hover {
  border-color: var(--border-focus);
  color: var(--text-primary);
  background: var(--bg-surface-hover);
}

/* Loading / Error */
.eco-loading,
.eco-error {
  text-align: center;
  padding: var(--space-3xl);
  color: var(--text-muted);
}

.eco-error {
  color: var(--error);
}

.eco-empty {
  text-align: center;
  padding: var(--space-xl);
  color: var(--text-muted);
  font-size: 0.85rem;
}

/* Responsive */
@media (max-width: 1200px) {
  .eco-bottom-row {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 900px) {
  .eco-charts-row,
  .eco-analysis-row {
    grid-template-columns: 1fr;
  }
  .eco-bottom-row {
    grid-template-columns: 1fr;
  }
}
</style>

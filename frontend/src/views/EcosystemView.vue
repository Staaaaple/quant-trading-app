<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart, PieChart, BarChart, RadarChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, GraphicComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { dnaApi, type EcosystemOverview, type StrategyDNASummary } from '@/api/dna'

use([
  CanvasRenderer, GraphChart, PieChart, BarChart, RadarChart,
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, GraphicComponent,
])

const ecosystem = ref<EcosystemOverview | null>(null)
const strategies = ref<StrategyDNASummary[]>([])
const loading = ref(true)
const error = ref('')
const router = useRouter()

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [eco, list] = await Promise.all([
      dnaApi.getEcosystem(),
      dnaApi.listAll(),
    ])
    ecosystem.value = eco
    strategies.value = list
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

/* ── 家族中文名映射 ── */
const FAMILY_NAME_MAP: Record<string, string> = {
  trend: '趋势',
  momentum: '动量',
  mean_reversion: '均值回归',
  breakout: '突破',
  value: '价值',
  quality: '质量',
  multi_factor: '多因子',
  ml: '机器学习',
  fixed_income: '固定收益',
  commodity: '商品',
  cash: '现金',
  other: '其他',
}

function familyNameCN(name: string): string {
  return FAMILY_NAME_MAP[name?.toLowerCase()] || name || '其他'
}

/* ── 当前组合中使用的策略 ID ── */
const usedStrategyIds = computed(() => {
  try {
    const stored = sessionStorage.getItem('latest_portfolio')
    if (!stored) return new Set<string>()
    const portfolio = JSON.parse(stored)
    const bindings = portfolio?.portfolio?.bindings || []
    return new Set<string>(bindings.map((b: any) => b.strategy_id).filter(Boolean))
  } catch (e) {
    return new Set<string>()
  }
})

const usedCount = computed(() => usedStrategyIds.value.size)

/* ── 仅资产组合中的策略 ── */
const portfolioStrategies = computed(() =>
  strategies.value.filter(s => usedStrategyIds.value.has(s.strategy_id))
)

function healthBucket(score: number): string {
  if (score >= 80) return '优秀(80+)'
  if (score >= 60) return '良好(60-80)'
  return '需关注(<60)'
}

function lifespanBucket(months: number): string {
  if (months >= 36) return '年轻(36+)'
  if (months >= 12) return '成熟(12-36)'
  if (months >= 3) return '衰老(3-12)'
  return '濒危(<3)'
}

function lifespanPhase(months: number): string {
  if (months >= 36) return 'young'
  if (months >= 12) return 'mature'
  if (months >= 3) return 'aging'
  return 'endangered'
}

function avg(nums: number[]): number {
  if (!nums.length) return 0
  return nums.reduce((a, b) => a + b, 0) / nums.length
}

const portfolioMetrics = computed(() => {
  const list = portfolioStrategies.value
  if (!list.length || !ecosystem.value) return null

  const families = [...new Set(list.map(s => s.family_name).filter(Boolean))]
  const familyDistribution = families.map(name => ({
    name: name as string,
    count: list.filter(s => s.family_name === name).length,
  })).sort((a, b) => b.count - a.count)

  const healthScores = list.map(s => s.health_birth_score)
  const lifespans = list.map(s => s.lifespan_months)
  const metabolicRates = list.map(s => s.metabolic_rate)
  const nicheWidths = list.map(s => s.niche_width)
  const diversityScores = list.map(s => s.gene_diversity_score)

  const healthDistribution: Record<string, number> = {}
  healthScores.forEach(s => {
    const b = healthBucket(s)
    healthDistribution[b] = (healthDistribution[b] || 0) + 1
  })

  const lifespanDistribution: Record<string, number> = {}
  lifespans.forEach(m => {
    const b = lifespanBucket(m)
    lifespanDistribution[b] = (lifespanDistribution[b] || 0) + 1
  })

  // 从 ecosystem 数组中过滤出组合内策略，保留后端计算字段
  const eco = ecosystem.value
  const inPortfolio = (s: { strategy_id?: string }) => usedStrategyIds.value.has(s.strategy_id || '')

  const lowHealth = (eco.low_health_strategies || []).filter(inPortfolio)
  const shortLifespan = (eco.short_lifespan_strategies || []).filter(inPortfolio)
  const highMetabolic = (eco.high_metabolic_strategies || []).filter(inPortfolio)
  const recent = (eco.recent_strategies || []).filter(inPortfolio)
  const metabolicRank = (eco.metabolic_ranking || []).filter(inPortfolio)
    .sort((a, b) => b.metabolic_rate - a.metabolic_rate)

  // 雷达：按家族聚合组合内策略
  const indicatorNames = eco.radar_indicators?.map(i => i.name) || ['健康度', '多样性', '代谢稳定性', '生态位宽度', '差异化']
  const familyGroups = new Map<string, StrategyDNASummary[]>()
  list.forEach(s => {
    const fam = s.family_name || 'other'
    if (!familyGroups.has(fam)) familyGroups.set(fam, [])
    familyGroups.get(fam)!.push(s)
  })
  const familyRadar = Array.from(familyGroups.entries()).map(([name, items]) => ({
    name,
    value: [
      avg(items.map(s => s.health_birth_score)),
      avg(items.map(s => s.gene_diversity_score * 100)),
      avg(items.map(s => 1 - s.metabolic_rate)),
      avg(items.map(s => s.niche_width)),
      avg(items.map(s => 1 - s.homogeneity_risk)),
    ],
  }))

  return {
    total_strategies: list.length,
    family_count: families.length,
    avg_health_score: avg(healthScores),
    min_health_score: Math.min(...healthScores),
    max_health_score: Math.max(...healthScores),
    avg_diversity: avg(diversityScores),
    inbreeding_risk_count: list.filter(s => s.inbreeding_warning).length,
    family_distribution: familyDistribution,
    health_distribution: healthDistribution,
    lifespan_distribution: lifespanDistribution,
    low_health_strategies: lowHealth,
    recent_strategies: recent,
    avg_metabolic_rate: avg(metabolicRates),
    avg_niche_width: avg(nicheWidths),
    syndrome_count: highMetabolic.filter((s: any) => s.metabolic_syndrome).length,
    high_metabolic_strategies: highMetabolic,
    avg_lifespan: avg(lifespans),
    endangered_count: lifespans.filter(m => m < 3).length,
    short_lifespan_strategies: shortLifespan,
    metabolic_ranking: metabolicRank,
    family_radar: familyRadar,
    radar_indicators: eco.radar_indicators || [],
  }
})

/* ── 概览统计 ── */
const stats = computed(() => {
  const e = portfolioMetrics.value
  if (!e) return null
  return [
    { label: '策略总数', value: e.total_strategies, color: '#171717', sub: '个组合策略' },
    { label: '策略家族', value: e.family_count, color: '#3b82f6', sub: '个家族分支' },
    { label: '平均健康度', value: e.avg_health_score.toFixed(1), color: '#22c55e', sub: '出生评分' },
    { label: '濒危策略', value: e.endangered_count, color: '#ef4444', sub: '需立即关注' },
    { label: '平均寿命', value: e.avg_lifespan.toFixed(1) + '月', color: '#d97706', sub: '预计剩余' },
    { label: '近亲风险', value: e.inbreeding_risk_count, color: '#ec4899', sub: '同质性过高' },
  ]
})

/* ── 家族分布饼图 ── */
const familyPieOption = computed(() => {
  const e = portfolioMetrics.value
  if (!e?.family_distribution.length) return {}
  const data = e.family_distribution
  const total = data.reduce((s, d) => s + d.count, 0)
  return {
    tooltip: { trigger: 'item', formatter: (p: any) => `${familyNameCN(p.name)}: ${p.value} (${p.percent}%)` },
    legend: {
      bottom: 0, left: 'center', itemWidth: 10, itemHeight: 10,
      textStyle: { fontSize: 11, color: '#737373' },
      formatter: (name: string) => familyNameCN(name),
    },
    series: [{
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: (p: any) => `${familyNameCN(p.name)}\n${p.value}`, fontSize: 11, lineHeight: 14, color: '#525252' },
      labelLine: { length: 10, length2: 10 },
      data: data.map((d, i) => ({
        name: d.name,
        value: d.count,
        itemStyle: { color: FAMILY_COLORS[i % FAMILY_COLORS.length] },
      })),
    }],
    graphic: [{
      type: 'text',
      left: 'center',
      top: '41%',
      style: { text: String(total), textAlign: 'center', fill: '#171717', fontSize: 26, fontWeight: 700, fontFamily: 'Inter, sans-serif' },
    }, {
      type: 'text',
      left: 'center',
      top: '48%',
      style: { text: '策略', textAlign: 'center', fill: '#a3a3a3', fontSize: 12, fontFamily: 'Inter, sans-serif' },
    }],
  }
})

/* ── 健康度分布柱状图 ── */
const healthBarOption = computed(() => {
  const e = portfolioMetrics.value
  if (!e?.health_distribution) return {}
  const labels = Object.keys(e.health_distribution)
  const values = Object.values(e.health_distribution)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 20, right: 16, bottom: 30, left: 40 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#e5e5e5' } },
      axisLabel: { color: '#737373', fontSize: 11, fontFamily: 'Inter, sans-serif' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
      axisLabel: { color: '#a3a3a3', fontSize: 11 },
    },
    series: [{
      type: 'bar',
      barWidth: '48%',
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: (params: any) => {
          const colors = ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444']
          return colors[params.dataIndex] || '#6366f1'
        },
      },
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.08)' } },
      data: values,
    }],
  }
})

/* ── 寿命分布柱状图 ── */
const lifespanBarOption = computed(() => {
  const e = portfolioMetrics.value
  if (!e?.lifespan_distribution) return {}
  const labels = Object.keys(e.lifespan_distribution)
  const values = Object.values(e.lifespan_distribution)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 20, right: 16, bottom: 30, left: 40 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#e5e5e5' } },
      axisLabel: { color: '#737373', fontSize: 11, fontFamily: 'Inter, sans-serif' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
      axisLabel: { color: '#a3a3a3', fontSize: 11 },
    },
    series: [{
      type: 'bar',
      barWidth: '48%',
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: (params: any) => {
          const colors = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e']
          return colors[params.dataIndex] || '#6366f1'
        },
      },
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.08)' } },
      data: values,
    }],
  }
})

/* ── 雷达图 ── */
const radarOption = computed(() => {
  const e = portfolioMetrics.value
  if (!e?.family_radar.length || !e?.radar_indicators.length) return {}
  return {
    tooltip: {},
    legend: { bottom: 0, data: e.family_radar.map(f => familyNameCN(f.name)), textStyle: { fontSize: 11, color: '#737373' } },
    radar: {
      indicator: e.radar_indicators.map(i => ({ name: i.name, max: i.max })),
      radius: '58%',
      axisName: { color: '#737373', fontSize: 11, fontFamily: 'Inter, sans-serif' },
      splitArea: { areaStyle: { color: ['#fafafa', '#fff'] } },
      axisLine: { lineStyle: { color: '#e5e5e5' } },
      splitLine: { lineStyle: { color: '#e5e5e5' } },
    },
    series: [{
      type: 'radar',
      data: e.family_radar.map((f, i) => ({
        name: familyNameCN(f.name),
        value: f.value,
        lineStyle: { color: FAMILY_COLORS[i % FAMILY_COLORS.length], width: 2 },
        itemStyle: { color: FAMILY_COLORS[i % FAMILY_COLORS.length] },
        areaStyle: { color: FAMILY_COLORS[i % FAMILY_COLORS.length], opacity: 0.08 },
        symbol: 'circle',
        symbolSize: 5,
      })),
    }],
  }
})

/* ── 关系网络图 ── */
const networkOption = computed(() => {
  if (!ecosystem.value?.family_network) return {}
  const net = ecosystem.value.family_network
  const usedIds = usedStrategyIds.value

  const USED_COLOR = '#6366f1'
  const UNUSED_FILL = '#e5e7eb'
  const UNUSED_STROKE = '#9ca3af'

  const nodes = net.nodes.map(n => {
    const isUsed = usedIds.has(n.id)
    return {
      ...n,
      used: isUsed,
      category: isUsed ? 0 : 1,
      symbol: 'circle',
      itemStyle: {
        color: isUsed ? USED_COLOR : UNUSED_FILL,
        borderColor: isUsed ? '#ffffff' : UNUSED_STROKE,
        borderWidth: isUsed ? 3 : 2,
        shadowBlur: isUsed ? 14 : 0,
        shadowColor: isUsed ? `${USED_COLOR}55` : 'transparent',
      },
      label: {
        show: true,
        fontSize: 11,
        position: 'bottom',
        distance: 6,
        color: isUsed ? '#312e81' : '#6b7280',
        fontWeight: isUsed ? 600 : 400,
      },
      symbolSize: isUsed ? 24 + n.health / 8 : 16,
    }
  })

  const links = net.links.map(l => ({
    ...l,
    label: {
      show: true,
      formatter: `${(l.value * 100).toFixed(0)}%`,
      fontSize: 9,
      color: '#94a3b8',
    },
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: 'rgba(0,0,0,0.06)',
      borderWidth: 1,
      textStyle: { color: '#1f2937' },
      extraCssText: 'box-shadow:0 8px 24px rgba(0,0,0,0.08);border-radius:10px;',
      formatter: (p: any) => {
        if (p.dataType === 'node') {
          const status = p.data.used ? '组合使用中' : '参考策略（未使用）'
          return `<div style="padding:4px 2px">`
            + `<div style="font-size:13px;font-weight:700;margin-bottom:6px;color:#111827">${p.data.name}</div>`
            + `<div style="font-size:12px;line-height:1.7;color:#4b5563">`
            + `<span style="display:inline-block;width:52px;color:#9ca3af">家族</span>${familyNameCN(p.data.family)}<br/>`
            + `<span style="display:inline-block;width:52px;color:#9ca3af">状态</span>${status}<br/>`
            + `<span style="display:inline-block;width:52px;color:#9ca3af">健康度</span>${p.data.health}<br/>`
            + `<span style="display:inline-block;width:52px;color:#9ca3af">寿命</span>${p.data.lifespan}月`
            + `</div></div>`
        }
        return `<div style="padding:4px 2px;font-size:12px;line-height:1.6">`
          + `<div style="font-weight:600;margin-bottom:4px;color:#111827">关联关系</div>`
          + `<span style="color:#4b5563">${p.data.source}</span> <span style="color:#9ca3af">→</span> <span style="color:#4b5563">${p.data.target}</span><br/>`
          + `<span style="color:#9ca3af">相似度</span> <span style="font-weight:700;color:#6366f1">${(p.data.value * 100).toFixed(1)}%</span>`
          + `</div>`
      },
    },
    legend: {
      bottom: 6,
      left: 'center',
      itemWidth: 10,
      itemHeight: 10,
      icon: 'circle',
      data: ['组合使用中', '参考策略（未使用）'],
      textStyle: { fontSize: 12, color: '#4b5563' },
    },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      zoom: 1.05,
      scaleLimit: { min: 0.5, max: 3 },
      center: ['50%', '48%'],
      label: { show: true, fontSize: 11, position: 'bottom' },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 3 },
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(99,102,241,0.35)' },
      },
      force: {
        repulsion: 260,
        edgeLength: [70, 130],
        gravity: 0.12,
        friction: 0.08,
        layoutAnimation: false,
      },
      data: nodes,
      links,
      categories: [
        { name: '组合使用中', itemStyle: { color: USED_COLOR } },
        { name: '参考策略（未使用）', itemStyle: { color: UNUSED_FILL, borderColor: UNUSED_STROKE } },
      ],
      lineStyle: {
        color: '#94a3b8',
        curveness: 0.2,
        opacity: 0.5,
        width: 1.5,
      },
      edgeLabel: {
        show: true,
        fontSize: 9,
        color: '#94a3b8',
      },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 8],
    }],
  }
})

const FAMILY_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#a855f7']

/* ── 列表 ── */
const endangeredList = computed(() => portfolioMetrics.value?.short_lifespan_strategies || [])
const lowHealthList = computed(() => portfolioMetrics.value?.low_health_strategies || [])
const highMetabolicList = computed(() => portfolioMetrics.value?.high_metabolic_strategies || [])

function getPhaseLabel(phase: string) {
  const map: Record<string, string> = { young: '年轻', mature: '成熟', aging: '衰老', endangered: '濒危' }
  return map[phase] || phase
}
function getPhaseColor(phase: string) {
  const map: Record<string, string> = { young: '#22c55e', mature: '#3b82f6', aging: '#d97706', endangered: '#ef4444' }
  return map[phase] || '#737373'
}
function getHealthColor(score: number) {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#d97706'
  return '#ef4444'
}
</script>

<template>
  <div class="eco-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="header-back" @click="router.back()" title="返回上一页">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <div class="header-title">
          <span class="header-label">ECOSYSTEM</span>
          <span class="header-name">生态系统</span>
        </div>
        <div class="header-placeholder"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="eco-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>正在扫描生态系统...</span>
      </div>

      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button class="btn-primary" @click="loadData">重试</button>
      </div>

      <template v-else-if="ecosystem">
        <!-- 组合未加载提示 -->
        <div v-if="!usedCount" class="portfolio-notice">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4"/>
            <path d="M12 8h.01"/>
          </svg>
          <span>当前未加载资产组合，上方统计图表仅展示组合内策略；关系网络中灰色节点为参考策略，组合策略将高亮显示。</span>
        </div>

        <!-- 概览统计 -->
        <div class="stats-grid">
          <div v-for="s in stats" :key="s.label" class="stat-card">
            <div class="stat-accent" :style="{ background: s.color }"></div>
            <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
            <div class="stat-sub">{{ s.sub }}</div>
          </div>
        </div>
        <div class="annotation-bar">
          <div class="annotation-dot"></div>
          <div class="annotation-content">
            <span class="annotation-title">概览说明：</span>
            <span class="annotation-text">上方 6 项指标帮你快速判断组合生态的健康状态。策略家族越多、健康度越高、寿命越长、近亲风险越少，组合越稳健。</span>
          </div>
        </div>

        <!-- 上排图表 -->
        <div class="chart-row three-col">
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">FAMILY</span>
              <span class="chart-name">家族分布</span>
            </div>
            <v-chart v-if="usedCount" class="chart chart-pie" :option="familyPieOption" autoresize />
            <div v-else class="chart-empty">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="1.5">
                <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/>
                <path d="M22 12A10 10 0 0 0 12 2v10z"/>
              </svg>
              <span>加载资产组合后展示</span>
            </div>
            <div class="chart-annotation">
              <div class="annotation-dot"></div>
              <p><strong>家族</strong>是按策略核心逻辑划分的群体（如趋势、动量、价值等）。家族越分散，组合越不容易因某一种风格失效而整体受挫。</p>
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">HEALTH</span>
              <span class="chart-name">健康度分布</span>
            </div>
            <v-chart v-if="usedCount" class="chart chart-bar" :option="healthBarOption" autoresize />
            <div v-else class="chart-empty">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="1.5">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              <span>加载资产组合后展示</span>
            </div>
            <div class="chart-annotation">
              <div class="annotation-dot"></div>
              <p><strong>健康度</strong>是策略"出生评分"，综合评估策略代码质量、风控完整性和逻辑合理性。健康度低的策略更容易在实际运行中出现异常。</p>
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">LIFESPAN</span>
              <span class="chart-name">寿命分布</span>
            </div>
            <v-chart v-if="usedCount" class="chart chart-bar" :option="lifespanBarOption" autoresize />
            <div v-else class="chart-empty">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>加载资产组合后展示</span>
            </div>
            <div class="chart-annotation">
              <div class="annotation-dot"></div>
              <p><strong>寿命</strong>表示策略预计还能有效运行的剩余时间。年轻策略（36月+）生命力强，濒危策略（<3月）需要尽快替换。</p>
            </div>
          </div>
        </div>

        <!-- 中排图表 -->
        <div class="chart-row two-col">
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">RADAR</span>
              <span class="chart-name">家族能力雷达</span>
            </div>
            <v-chart v-if="usedCount" class="chart chart-radar" :option="radarOption" autoresize />
            <div v-else class="chart-empty">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="1.5">
                <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/>
                <polyline points="12 22 12 15.5"/>
                <polyline points="22 8.5 12 15.5 2 8.5"/>
                <polyline points="2 15.5 12 8.5 22 15.5"/>
                <polyline points="12 2 12 8.5"/>
              </svg>
              <span>加载资产组合后展示</span>
            </div>
            <div class="chart-annotation">
              <div class="annotation-dot"></div>
              <p><strong>能力雷达</strong>对比不同策略家族在健康度、多样性、代谢稳定性等维度的平均表现。面积越均衡的家族，越适合作为组合的压舱石。</p>
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <span class="chart-label">NETWORK</span>
              <span class="chart-name">策略关系网络</span>
              <span class="chart-hint">{{ usedCount ? `组合中 ${usedCount} 个策略高亮` : '未加载组合，全部显示为参考策略' }}</span>
            </div>
            <v-chart class="chart chart-network" :option="networkOption" autoresize />
            <div class="chart-annotation">
              <div class="annotation-dot"></div>
              <p><strong>关系网络</strong>中每个节点是一个策略，连线代表策略间的相似度。相似度过高的策略会"近亲繁殖"，降低组合多样性；颜色高亮的节点为当前组合正在使用的策略。</p>
            </div>
          </div>
        </div>

        <!-- 底部列表 -->
        <div class="section-title">
          <span class="section-label">MONITORING</span>
          <span class="section-name">策略监控</span>
        </div>
        <div class="annotation-bar light">
          <div class="annotation-dot"></div>
          <div class="annotation-content">
            <span class="annotation-title">监控说明：</span>
            <span class="annotation-text">系统持续跟踪三类风险信号：<strong>濒危策略</strong>（剩余寿命不足，需替换）、<strong>需关注策略</strong>（健康度低，需排查）、<strong>代谢活跃策略</strong>（过度优化，容易失效）。及时处理这些预警，能让组合保持长期生命力。</span>
          </div>
        </div>

        <div class="list-row">
          <!-- 濒危策略 -->
          <div class="list-card">
            <div class="list-header">
              <div class="list-header-left">
                <span class="status-dot" style="background:#ef4444"></span>
                <h3>濒危策略</h3>
              </div>
              <span class="list-count">{{ endangeredList.length }}</span>
            </div>
            <p class="list-annotation">剩余寿命 <strong>不足 3 个月</strong>的策略，失效风险极高，建议尽快寻找替代方案。</p>
            <div v-if="!endangeredList.length" class="list-empty">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="1.5" style="margin-bottom:8px">
                <circle cx="12" cy="12" r="10"/>
                <path d="m9 12 2 2 4-4"/>
              </svg>
              <div>暂无濒危策略</div>
            </div>
            <div v-else class="list-body">
              <div v-for="s in endangeredList" :key="s.strategy_id" class="list-item">
                <div class="list-item-main">
                  <div class="list-item-name">{{ s.name }}</div>
                  <div class="list-item-meta">{{ s.family_name || '未归类' }}</div>
                </div>
                <div class="list-item-badges">
                  <span class="tag" :style="{ background: getPhaseColor(s.lifespan_phase) + '15', color: getPhaseColor(s.lifespan_phase), borderColor: getPhaseColor(s.lifespan_phase) + '20' }">
                    {{ getPhaseLabel(s.lifespan_phase) }}
                  </span>
                  <span class="tag tag-red">{{ s.lifespan_months }}月</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 低健康度 -->
          <div class="list-card">
            <div class="list-header">
              <div class="list-header-left">
                <span class="status-dot" style="background:#d97706"></span>
                <h3>需关注策略</h3>
              </div>
              <span class="list-count">{{ lowHealthList.length }}</span>
            </div>
            <p class="list-annotation">健康度评分<strong>低于 60</strong>的策略，可能存在代码缺陷、风控不足或逻辑漏洞，需要重点排查。</p>
            <div v-if="!lowHealthList.length" class="list-empty">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="1.5" style="margin-bottom:8px">
                <circle cx="12" cy="12" r="10"/>
                <path d="m9 12 2 2 4-4"/>
              </svg>
              <div>所有策略健康度良好</div>
            </div>
            <div v-else class="list-body">
              <div v-for="s in lowHealthList" :key="s.strategy_id" class="list-item">
                <div class="list-item-main">
                  <div class="list-item-name">{{ s.name }}</div>
                  <div class="list-item-meta">{{ s.family_name || '未归类' }}</div>
                </div>
                <div class="list-item-badges">
                  <span class="tag" :style="{ background: getHealthColor(s.health_birth_score) + '12', color: getHealthColor(s.health_birth_score), borderColor: getHealthColor(s.health_birth_score) + '18' }">
                    健康 {{ s.health_birth_score }}
                  </span>
                  <span class="tag">多样性 {{ (s.gene_diversity_score * 100).toFixed(0) }}%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 代谢活跃 -->
          <div class="list-card">
            <div class="list-header">
              <div class="list-header-left">
                <span class="status-dot" style="background:#6366f1"></span>
                <h3>代谢活跃</h3>
              </div>
              <span class="list-count">{{ highMetabolicList.length }}</span>
            </div>
            <p class="list-annotation"><strong>代谢率高</strong>意味着策略对历史数据过度拟合，未来失效速度快。若同时生态位窄，还会触发"代谢综合征"。</p>
            <div v-if="!highMetabolicList.length" class="list-empty">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="1.5" style="margin-bottom:8px">
                <circle cx="12" cy="12" r="10"/>
                <path d="m9 12 2 2 4-4"/>
              </svg>
              <div>代谢水平正常</div>
            </div>
            <div v-else class="list-body">
              <div v-for="s in highMetabolicList" :key="s.strategy_id" class="list-item">
                <div class="list-item-main">
                  <div class="list-item-name">{{ s.name }}</div>
                  <div class="list-item-meta">{{ s.family_name || '未归类' }}</div>
                </div>
                <div class="list-item-badges">
                  <span v-if="s.metabolic_syndrome" class="tag tag-red">代谢综合征</span>
                  <span class="tag tag-blue">{{ (s.metabolic_rate * 100).toFixed(0) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.eco-page {
  min-height: 100vh;
  background: #fafafa;
  position: relative;
  padding-bottom: 24px;
}

.texture-noise {
  position: fixed; inset: 0; z-index: 0;
  opacity: 0.035; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat; background-size: 128px 128px;
}
.texture-grid {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: linear-gradient(rgba(0,0,0,0.028) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.028) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
}

/* Header */
.page-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.85);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.page-header-inner {
  max-width: 1200px; margin: 0 auto; padding: 12px 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.header-title { display: flex; flex-direction: column; align-items: center; gap: 2px; flex: 1; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }
.header-back {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.06);
  background: #fff;
  color: #525252;
  cursor: pointer;
  transition: all 0.2s ease;
}
.header-back:hover {
  background: #f5f5f5;
  border-color: rgba(0,0,0,0.1);
  color: #171717;
  transform: translateX(-1px);
}
.header-placeholder { width: 36px; }

/* Content */
.eco-content {
  max-width: 1200px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

.loading-state, .error-state {
  text-align: center; padding: 60px 20px; color: #a3a3a3;
}
.error-state p { margin-bottom: 20px; }
.spinner {
  width: 20px; height: 20px;
  border: 2px solid #e5e5e5; border-top-color: #171717; border-radius: 50%;
  animation: spin 0.8s linear infinite; display: inline-block; vertical-align: middle; margin-right: 10px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}
.stat-card {
  text-align: center; padding: 18px 12px 14px;
  background: #fff; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.05);
  position: relative; overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  transform: translateY(-1px);
  border-color: rgba(0,0,0,0.08);
}
.stat-accent {
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.stat-value {
  font-size: 1.5rem; font-weight: 800; line-height: 1;
  margin-bottom: 6px; letter-spacing: -0.02em;
}
.stat-label {
  font-size: 0.72rem; font-weight: 600; color: #171717;
  margin-bottom: 2px;
}
.stat-sub {
  font-size: 0.65rem; color: #a3a3a3;
}

/* Section Title */
.section-title {
  display: flex; align-items: baseline; gap: 10px;
  padding: 8px 4px 0;
}
.section-label { font-size: 0.62rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.section-name { font-size: 0.9rem; font-weight: 600; color: #171717; }

/* Charts */
.chart-row {
  display: grid; gap: 14px;
}
.chart-row.three-col { grid-template-columns: 1.2fr 1fr 1fr; }
.chart-row.two-col { grid-template-columns: 1fr 1.5fr; }

.chart-card {
  background: #fff; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  padding: 18px 20px 14px;
  transition: all 0.2s ease;
}
.chart-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border-color: rgba(0,0,0,0.08);
}

.chart-header {
  display: flex; align-items: baseline; gap: 8px;
  margin-bottom: 14px;
}
.chart-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.chart-name { font-size: 0.88rem; font-weight: 600; color: #171717; }
.chart-hint {
  margin-left: auto;
  font-size: 0.7rem; font-weight: 400; color: #a3a3a3;
  background: #f5f5f5; padding: 2px 8px; border-radius: 999px;
}

/* Annotations */
.annotation-bar {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px 16px;
  background: #f8fafc; border: 1px solid rgba(0,0,0,0.04);
  border-radius: 12px; margin-top: 4px;
}
.annotation-bar.light {
  background: #fff;
}
.annotation-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #6366f1;
  margin-top: 6px;
  flex-shrink: 0;
}
.annotation-content {
  font-size: 0.78rem; color: #525252;
  line-height: 1.6;
}
.annotation-title {
  font-weight: 700; color: #171717;
}
.annotation-text {
  color: #525252;
}
.annotation-text strong {
  color: #171717; font-weight: 700;
}

.chart-annotation {
  display: flex; align-items: flex-start; gap: 8px;
  margin-top: 10px;
  padding-top: 12px;
  border-top: 1px solid rgba(0,0,0,0.04);
}
.chart-annotation p {
  font-size: 0.72rem; color: #525252;
  line-height: 1.6; margin: 0;
}
.chart-annotation strong {
  color: #171717; font-weight: 700;
}

.list-annotation {
  font-size: 0.72rem; color: #525252;
  line-height: 1.55; margin: -6px 0 12px;
}
.list-annotation strong {
  color: #171717; font-weight: 700;
}

.chart { width: 100%; height: 240px; }
.chart-pie { height: 260px; }
.chart-radar { height: 300px; }
.chart-network { height: 360px; }

.chart-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 240px; color: #a3a3a3; font-size: 0.8rem; gap: 10px;
}
.chart-pie + .chart-empty, .chart-card:has(.chart-pie) .chart-empty { height: 260px; }
.chart-radar + .chart-empty, .chart-card:has(.chart-radar) .chart-empty { height: 300px; }

.portfolio-notice {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px;
  background: #eff6ff; border: 1px solid rgba(59,130,246,0.15);
  border-radius: 12px; color: #1e40af; font-size: 0.8rem;
}
.portfolio-notice svg { flex-shrink: 0; }

/* Lists */
.list-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.list-card {
  background: #fff; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  padding: 18px 20px 14px;
}

.list-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.list-header-left {
  display: flex; align-items: center; gap: 8px;
}
.list-header h3 {
  font-size: 0.88rem; font-weight: 600; color: #171717; margin: 0;
}
.status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  flex-shrink: 0;
}
.list-count {
  font-size: 0.72rem; font-weight: 700; color: #a3a3a3;
  background: #f5f5f5; padding: 2px 8px; border-radius: 999px;
}

.list-empty {
  text-align: center; padding: 32px 20px; color: #a3a3a3;
  font-size: 0.8rem; display: flex; flex-direction: column; align-items: center;
}

.list-body {
  display: flex; flex-direction: column; gap: 8px;
}

.list-item {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: #fafafa; border-radius: 10px;
  transition: background 0.15s;
  border: 1px solid transparent;
}
.list-item:hover {
  background: #f5f5f5;
  border-color: rgba(0,0,0,0.04);
}

.list-item-main { min-width: 0; }
.list-item-name {
  font-size: 0.82rem; font-weight: 600; color: #171717;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.list-item-meta {
  font-size: 0.7rem; color: #a3a3a3; margin-top: 2px;
}

.list-item-badges {
  display: flex; gap: 6px; flex-shrink: 0;
}

.tag {
  display: inline-flex; align-items: center;
  padding: 3px 8px; border-radius: 6px;
  font-size: 0.68rem; font-weight: 600;
  border: 1px solid rgba(0,0,0,0.06);
  background: #f5f5f5; color: #525252;
  white-space: nowrap;
}
.tag-green { background: #f0fdf4; color: #166534; border-color: rgba(34,197,94,0.12); }
.tag-red { background: #fef2f2; color: #991b1b; border-color: rgba(239,68,68,0.12); }
.tag-blue { background: #eff6ff; color: #1e40af; border-color: rgba(59,130,246,0.12); }

/* Responsive */
@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
  .chart-row.three-col { grid-template-columns: 1fr 1fr; }
  .chart-row.two-col { grid-template-columns: 1fr; }
  .list-row { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-row.three-col,
  .chart-row.two-col,
  .list-row { grid-template-columns: 1fr; }
  .eco-content { padding: 12px 16px 24px; }
}
</style>

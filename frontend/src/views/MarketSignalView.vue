<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marketSignalApi, type MarketSignalLatest } from '@/api/marketSignal'

const router = useRouter()

const signal = ref<MarketSignalLatest | null>(null)
const loading = ref(true)
const error = ref('')

// 模态框状态
const activeModal = ref<string | null>(null)

// 周期可视化展开状态
const cycleExpanded = ref(false)

function toggleCycleExpand() {
  cycleExpanded.value = !cycleExpanded.value
}

function goToPortfolio() {
  router.push('/portfolio')
}

function goToProfile() {
  router.push('/profile/summary')
}

// 获取当前周期在四象限中的坐标
function getCurrentCycleCoords() {
  if (!signal.value?.cycle_analysis?.fused_coordinates) return { x: 0, y: 0 }
  const coords = signal.value.cycle_analysis.fused_coordinates
  return {
    x: coords.growth ?? 0,
    y: coords.inflation ?? 0,
  }
}

// 将坐标映射到 SVG 坐标系（400x280 画布）
function mapToSvg(x: number, y: number) {
  // x: growth (-1~1) → 80~320
  // y: inflation (-1~1) → 200~80（注意Y轴翻转）
  const svgX = 200 + x * 140
  const svgY = 140 - y * 80
  return { x: svgX, y: svgY }
}

// 生成周期曲线路径（四象限的椭圆弧线）
function cycleCurvePath() {
  const center = { x: 50, y: 50 }
  const rx = 35
  const ry = 35
  // 画一个顺时针的椭圆，从复苏开始
  return `M ${center.x + rx} ${center.y} A ${rx} ${ry} 0 1 1 ${center.x - rx} ${center.y} A ${rx} ${ry} 0 1 1 ${center.x + rx} ${center.y}`
}

// 获取当前点位在曲线上的位置（限制在合理范围内）
function getCurrentPointOnCurve() {
  const coords = getCurrentCycleCoords()
  // 限制坐标范围，确保点在画布内
  const clampedX = Math.max(-0.9, Math.min(0.9, coords.x))
  const clampedY = Math.max(-0.9, Math.min(0.9, coords.y))
  return mapToSvg(clampedX, clampedY)
}

async function loadSignal() {
  loading.value = true
  error.value = ''
  try {
    signal.value = await marketSignalApi.getLatest()
    // 存储到 sessionStorage，供其他页面使用
    if (signal.value) {
      sessionStorage.setItem('latest_market_signal', JSON.stringify(signal.value))
    }
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSignal()
})

function openModal(layerId: string) {
  activeModal.value = layerId
  document.body.style.overflow = 'hidden'
}

function closeModal() {
  activeModal.value = null
  document.body.style.overflow = ''
}

function scoreColor(score: number | null): string {
  if (score === null) return '#a3a3a3'
  if (score >= 70) return '#22c55e'
  if (score >= 50) return '#d97706'
  return '#ef4444'
}

function scoreBg(score: number | null): string {
  if (score === null) return '#f5f5f5'
  if (score >= 70) return '#f0fdf4'
  if (score >= 50) return '#fffbeb'
  return '#fef2f2'
}

function cycleBadgeClass(cycle: string): string {
  const map: Record<string, string> = {
    '复苏': 'badge-green',
    '过热': 'badge-red',
    '滞胀': 'badge-amber',
    '衰退': 'badge-gray',
  }
  return map[cycle] || 'badge-gray'
}

// ── 几何图标组件 ──
const GeoIcons: Record<string, { viewBox: string; paths: string[] }> = {
  macro: {
    viewBox: '0 0 36 36',
    paths: [
      'M6 28h24M6 28V14l6-6 6 4 6-8 6 6v18',
      'M6 14h24',
    ],
  },
  geo: {
    viewBox: '0 0 36 36',
    paths: [
      'M18 4c7.7 0 14 6.3 14 14s-6.3 14-14 14S4 25.7 4 18 10.3 4 18 4z',
      'M18 4v28M4 18h28',
      'M7.5 10.5a14 14 0 0 0 0 15M28.5 10.5a14 14 0 0 1 0 15',
    ],
  },
  industry: {
    viewBox: '0 0 36 36',
    paths: [
      'M8 30V16l4-2v16M16 30V12l4-2v20M24 30V10l4-2v22',
      'M6 30h24',
    ],
  },
  social: {
    viewBox: '0 0 36 36',
    paths: [
      'M18 8c3.3 0 6 2.7 6 6s-2.7 6-6 6-6-2.7-6-6 2.7-6 6-6z',
      'M8 32c0-5.5 4.5-10 10-10s10 4.5 10 10',
      'M26 14c2.2 0 4 1.8 4 4s-1.8 4-4 4',
      'M28 26c0-3.3-2.7-6-6-6',
    ],
  },
  internal: {
    viewBox: '0 0 36 36',
    paths: [
      'M6 28h24M8 28V20h4v8M16 28V14h4v14M24 28V10h4v18',
    ],
  },
}

// ── 板块配置（中文标题 + 小白说明）──
const LAYER_CONFIG: Record<string, {
  title: string
  subtitle: string
  weight: string
  desc: string
  what: string
  explain: string
  impact: string
  factors: { label: string; desc: string }[]
}> = {
  macro: {
    title: '宏观基本面',
    subtitle: '经济大环境',
    weight: '权重 30%',
    desc: '看国家经济整体状况，像看天气决定出门穿什么',
    what: '宏观基本面反映的是一个国家整体经济的健康状况，包括经济增长速度、物价水平、货币宽松程度等。就像你出门前要看天气决定穿什么衣服一样，投资前也要看经济大环境。',
    explain: '我们采集 GDP、CPI、PMI、M2 和 LPR 等关键指标。GDP 增长快说明经济有活力；CPI 温和上涨（1%-3%）是最佳状态；PMI 超过 50 说明制造业在扩张；M2 增速适中表示流动性合理；LPR 下行意味着融资成本降低，利好股市。',
    impact: '当宏观评分高时（经济复苏期），适合增加股票仓位，尤其是周期性行业如金融、地产、基建。当宏观评分低时（滞胀或衰退），应降低仓位，增加债券和现金配置。',
    factors: [
      { label: 'GDP趋势', desc: '国内生产总值增速，反映经济整体活力' },
      { label: '通胀水平', desc: 'CPI 消费者物价指数，温和通胀利好股市' },
      { label: '流动性', desc: 'M2 货币供应量增速，宽松利好资产价格' },
      { label: '利率趋势', desc: 'LPR 贷款基准利率，下行降低融资成本' },
    ],
  },
  geo: {
    title: '地缘政治',
    subtitle: '国际局势风险',
    weight: '权重 20%',
    desc: '关注国际冲突和贸易摩擦，像关注小区周边安全',
    what: '地缘政治风险指的是国家之间的冲突、贸易摩擦、制裁等事件对市场的影响。就像你关注小区周边是否安全一样，投资也要关注国际局势是否稳定。',
    explain: '我们监控中美关系、台海局势、俄乌冲突、中东局势等热点。当这些地区发生冲突或紧张升级时，市场避险情绪会升温，黄金、美元等避险资产会上涨，而股票等风险资产会下跌。',
    impact: '地缘风险高时，减少股票 exposure，增加黄金、国债等避险资产。关注受影响的行业：科技（芯片禁令）、能源（石油禁运）、军工（军费增加）、农业（粮食安全）。',
    factors: [
      { label: '整体风险', desc: '综合评估当前国际局势紧张程度' },
      { label: '风险等级', desc: '低/中/高三档，直观判断避险需求' },
      { label: '避险需求', desc: '市场资金流向黄金、国债等安全资产的程度' },
    ],
  },
  industry: {
    title: '行业景气度',
    subtitle: '哪些行业在风口',
    weight: '权重 20%',
    desc: '追踪热门行业动态，像看哪个商圈人气旺',
    what: '行业景气度反映不同行业的活跃程度和发展前景。就像你想开店会选人气旺的商圈一样，投资也要选景气度高的行业。',
    explain: '我们通过分析财经新闻中各行业的提及频率和情绪来判断景气度。科技、新能源、医药、消费、金融、军工、能源、汽车、传媒、农业十大行业，哪个被提到越多、情绪越正面，景气度就越高。',
    impact: '景气度高的行业（推荐列表）适合重点配置；景气度低的行业（回避列表）应减少 exposure。行业轮动是 A 股重要特征，紧跟景气度变化能显著提升收益。',
    factors: [
      { label: '行业热力图', desc: '十大行业景气度评分，一目了然' },
      { label: '推荐行业', desc: '当前景气度最高的行业，值得重点关注' },
      { label: '回避行业', desc: '景气度低迷的行业，暂时规避' },
    ],
  },
  social: {
    title: '社会实事',
    subtitle: '大众关注的热点',
    weight: '权重 15%',
    desc: '捕捉社会趋势变化，像感知流行风向',
    what: '社会实事反映的是大众关注的热点话题和长期社会趋势。就像你要感知流行风向才能选对商品一样，投资也要紧跟社会趋势。',
    explain: '我们追踪 AI 革命、老龄化、新能源出海、消费降级、国产替代、数字经济、绿色转型、全球化重构等八大社会主题。这些主题往往催生长期投资机会，比如老龄化带来医药和养老产业需求，AI 革命带动算力和应用板块。',
    impact: '社会主题强度高的方向，往往有持续数年的投资机会。比如「国产替代」主题强时，半导体、信创、工业软件等板块会有政策支持和资金关注；「消费降级」主题强时，拼多多、折扣零售等性价比业态受益。',
    factors: [
      { label: '热点主题', desc: '当前最受关注的社会趋势话题' },
      { label: '主题强度', desc: '各主题在新闻中的提及频率和热度' },
      { label: '消费信心', desc: '大众消费意愿，影响消费板块表现' },
    ],
  },
  internal: {
    title: '资产内部',
    subtitle: '股市自身状态',
    weight: '权重 15%',
    desc: '观察股市自身指标，像体检看自身健康',
    what: '资产内部信号反映的是股市自身的运行状态，不依赖外部环境。就像体检看自身健康指标一样，这些指标告诉你股市现在是贪婪还是恐惧。',
    explain: '我们监控股债利差（股票性价比）、市场情绪（贪婪/恐惧指数）、风格轮动（大盘/小盘、成长/价值）、成交量趋势和波动率。股债利差高说明股票比债券更有吸引力；市场情绪极端时往往意味着反转。',
    impact: '市场情绪贪婪时（如连续大涨、放量），应警惕回调风险，适当减仓。市场情绪恐惧时（如连续大跌、缩量），往往是布局良机，可适当加仓。风格轮动提示你当前该配大盘还是小盘、成长还是价值。',
    factors: [
      { label: '市场情绪', desc: '贪婪/中性/恐惧，判断市场极端状态' },
      { label: '股债利差', desc: '股票收益率 vs 债券收益率，衡量性价比' },
      { label: '风格轮动', desc: '大盘/小盘、成长/价值的当前主导风格' },
      { label: '波动率', desc: '市场波动程度，高波动意味着高风险高收益' },
    ],
  },
}

// ── 经济周期四阶段坐标（用于可视化）──
const CYCLE_PHASES = [
  { name: '复苏', x: 0.8, y: -0.5, color: '#22c55e', desc: '经济回升，通胀温和' },
  { name: '过热', x: 1.0, y: 1.0, color: '#ef4444', desc: '经济偏热，通胀上行' },
  { name: '滞胀', x: -0.5, y: 0.8, color: '#d97706', desc: '经济放缓，通胀仍高' },
  { name: '衰退', x: -0.8, y: -0.8, color: '#737373', desc: '经济下行，通缩压力' },
]

const layerOrder = ['macro', 'geo', 'industry', 'social', 'internal']
</script>

<template>
  <div class="signal-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <div class="header-left">
          <button class="back-btn" @click="goToProfile" title="返回投资画像">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 12H5"/>
              <path d="m12 19-7-7 7-7"/>
            </svg>
          </button>
          <h1 class="page-title">市场仪表盘</h1>
        </div>
        <button class="refresh-btn" @click="loadSignal" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 16h5v5"/>
          </svg>
        </button>
      </div>
    </header>

    <div class="signal-content">
      <div v-if="loading" class="loading-state">加载市场信号...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>

      <template v-else-if="signal">
        <!-- Summary Card -->
        <div class="summary-card" :class="{ expanded: cycleExpanded }">
          <div class="summary-main">
            <div class="summary-left">
              <div class="summary-label">市场综合评分</div>
              <div class="summary-cycle">
                <span :class="['cycle-badge', cycleBadgeClass(signal.market_cycle)]">
                  {{ signal.market_cycle }}
                </span>
                <span v-if="signal.cycle_analysis" class="confidence-badge">
                  置信度 {{ signal.cycle_analysis.confidence }}%
                </span>
              </div>
              <div class="summary-mood">{{ signal.market_mood }}</div>
              <div v-if="signal.cycle_analysis" class="cycle-models">
                <span
                  v-for="m in signal.cycle_analysis.model_results"
                  :key="m.model"
                  class="model-tag"
                  :title="m.description"
                >
                  {{ m.model }}: {{ m.phase }}
                </span>
              </div>
            </div>
            <div class="summary-right">
              <div class="score-value" :style="{ color: scoreColor(signal.composite_score + 50) }">
                {{ signal.composite_score > 0 ? '+' : '' }}{{ signal.composite_score }}
              </div>
              <div class="score-label">-50 ~ +50</div>
            </div>
          </div>

          <!-- Expand Button -->
          <button class="expand-cycle-btn" @click="toggleCycleExpand">
            <span>{{ cycleExpanded ? '收起周期图' : '查看经济周期' }}</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ transform: cycleExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }">
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </button>

          <!-- Cycle Visualization -->
          <Transition name="cycle-expand">
            <div v-if="cycleExpanded" class="cycle-visualization">
              <!-- Big Cycle Chart -->
              <div class="cycle-chart-container">
                <svg viewBox="0 0 400 280" class="cycle-chart-big">
                  <defs>
                    <!-- Arrow marker -->
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                      <polygon points="0 0, 10 3.5, 0 7" fill="#171717" opacity="0.6"/>
                    </marker>
                    <!-- Glow filter for current dot -->
                    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                      <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                      </feMerge>
                    </filter>
                  </defs>

                  <!-- Background quadrant fills -->
                  <rect x="200" y="10" width="190" height="125" fill="#f0fdf4" opacity="0.5" rx="8"/>
                  <rect x="200" y="145" width="190" height="125" fill="#fef2f2" opacity="0.5" rx="8"/>
                  <rect x="10" y="145" width="190" height="125" fill="#fffbeb" opacity="0.5" rx="8"/>
                  <rect x="10" y="10" width="190" height="125" fill="#f5f5f5" opacity="0.5" rx="8"/>

                  <!-- Axis lines -->
                  <line x1="200" y1="15" x2="200" y2="265" stroke="#d4d4d4" stroke-width="1" stroke-dasharray="4 4"/>
                  <line x1="15" y1="140" x2="385" y2="140" stroke="#d4d4d4" stroke-width="1" stroke-dasharray="4 4"/>

                  <!-- Axis labels -->
                  <text x="375" y="155" class="axis-label-big" text-anchor="end" fill="#737373">经济增长 →</text>
                  <text x="190" y="25" class="axis-label-big" text-anchor="end" fill="#737373">← 通胀</text>

                  <!-- Phase labels in corners -->
                  <text x="360" y="30" class="phase-corner-label" text-anchor="end" fill="#166534">复苏</text>
                  <text x="360" y="260" class="phase-corner-label" text-anchor="end" fill="#991b1b">过热</text>
                  <text x="40" y="260" class="phase-corner-label" text-anchor="start" fill="#92400e">滞胀</text>
                  <text x="40" y="30" class="phase-corner-label" text-anchor="start" fill="#525252">衰退</text>

                  <!-- Main cycle curve with arrow -->
                  <path
                    d="M 320 80 Q 360 140 320 200 Q 280 260 200 240 Q 120 220 80 160 Q 40 100 80 60 Q 120 20 200 40 Q 280 60 320 80"
                    fill="none"
                    stroke="#171717"
                    stroke-width="2.5"
                    stroke-linecap="round"
                    marker-end="url(#arrowhead)"
                    opacity="0.7"
                  />

                  <!-- Direction arrows along the curve -->
                  <path
                    d="M 200 40 Q 280 60 320 80"
                    fill="none"
                    stroke="#171717"
                    stroke-width="1.5"
                    stroke-dasharray="6 4"
                    opacity="0.3"
                  />
                  <path
                    d="M 320 80 Q 360 140 320 200"
                    fill="none"
                    stroke="#171717"
                    stroke-width="1.5"
                    stroke-dasharray="6 4"
                    opacity="0.3"
                  />
                  <path
                    d="M 320 200 Q 280 260 200 240"
                    fill="none"
                    stroke="#171717"
                    stroke-width="1.5"
                    stroke-dasharray="6 4"
                    opacity="0.3"
                  />
                  <path
                    d="M 200 240 Q 120 220 80 160"
                    fill="none"
                    stroke="#171717"
                    stroke-width="1.5"
                    stroke-dasharray="6 4"
                    opacity="0.3"
                  />
                  <path
                    d="M 80 160 Q 40 100 80 60"
                    fill="none"
                    stroke="#171717"
                    stroke-width="1.5"
                    stroke-dasharray="6 4"
                    opacity="0.3"
                  />
                  <path
                    d="M 80 60 Q 120 20 200 40"
                    fill="none"
                    stroke="#171717"
                    stroke-width="1.5"
                    stroke-dasharray="6 4"
                    opacity="0.3"
                  />

                  <!-- Phase dots -->
                  <circle cx="320" cy="80" r="5" fill="#22c55e" opacity="0.8"/>
                  <circle cx="320" cy="200" r="5" fill="#ef4444" opacity="0.8"/>
                  <circle cx="80" cy="200" r="5" fill="#d97706" opacity="0.8"/>
                  <circle cx="80" cy="80" r="5" fill="#737373" opacity="0.8"/>

                  <!-- Current position -->
                  <g v-if="signal.cycle_analysis">
                    <circle
                      :cx="getCurrentPointOnCurve().x"
                      :cy="getCurrentPointOnCurve().y"
                      r="18"
                      fill="none"
                      stroke="#171717"
                      stroke-width="1"
                      opacity="0.15"
                    >
                      <animate attributeName="r" values="18;24;18" dur="2s" repeatCount="indefinite"/>
                      <animate attributeName="opacity" values="0.15;0.05;0.15" dur="2s" repeatCount="indefinite"/>
                    </circle>
                    <circle
                      :cx="getCurrentPointOnCurve().x"
                      :cy="getCurrentPointOnCurve().y"
                      r="8"
                      fill="#171717"
                      filter="url(#glow)"
                    />
                    <text
                      :x="getCurrentPointOnCurve().x"
                      :y="getCurrentPointOnCurve().y - 16"
                      class="current-label"
                      text-anchor="middle"
                      fill="#171717"
                      font-weight="700"
                    >当前</text>
                  </g>
                </svg>
              </div>

              <!-- Phase cards -->
              <div class="phase-cards">
                <div
                  v-for="phase in CYCLE_PHASES"
                  :key="phase.name"
                  class="phase-card"
                  :class="{ 'phase-active': signal.market_cycle?.includes(phase.name) }"
                >
                  <div class="phase-card-header">
                    <span class="phase-card-dot" :style="{ background: phase.color }"></span>
                    <span class="phase-card-name">{{ phase.name }}</span>
                  </div>
                  <p class="phase-card-desc">{{ phase.desc }}</p>
                </div>
              </div>

              <!-- Current position info -->
              <div v-if="signal.cycle_analysis" class="current-position">
                <div class="position-label">当前位置</div>
                <div class="position-detail">
                  <span class="position-phase">{{ signal.cycle_analysis.final_phase }}</span>
                  <span class="position-coords">
                    增长 {{ signal.cycle_analysis.fused_coordinates.growth?.toFixed(2) }}
                    · 通胀 {{ signal.cycle_analysis.fused_coordinates.inflation?.toFixed(2) }}
                  </span>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Dashboard Grid -->
        <div class="dashboard-grid">
          <div
            v-for="key in layerOrder"
            :key="key"
            class="dashboard-card"
            :class="`card-${key}`"
          >
            <!-- Card Header -->
            <div class="dash-header">
              <div class="dash-title-group">
                <span class="dash-icon">
                  <svg v-if="GeoIcons[key]" :viewBox="GeoIcons[key].viewBox" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path v-for="(p, i) in GeoIcons[key].paths" :key="i" :d="p" />
                  </svg>
                </span>
                <div>
                  <div class="dash-title">{{ LAYER_CONFIG[key]?.title }}</div>
                  <div class="dash-subtitle">{{ LAYER_CONFIG[key]?.subtitle }}</div>
                </div>
              </div>
              <div class="dash-actions">
                <span class="dash-weight">{{ LAYER_CONFIG[key]?.weight }}</span>
                <button class="expand-btn" @click.stop="openModal(key)" title="查看详情">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m21 21-6-6m6 6v-4.8m0 4.8h-4.8"/>
                    <path d="M3 16.2V21m0 0h4.8M3 21l6-6"/>
                    <path d="M21 7.8V3m0 0h-4.8M21 3l-6 6"/>
                    <path d="M3 7.8V3m0 0h4.8M3 3l6 6"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Card Body -->
            <div class="dash-body">
              <!-- Score Ring -->
              <div class="score-ring-wrap">
                <svg viewBox="0 0 80 80" class="score-ring">
                  <circle cx="40" cy="40" r="32" fill="none" stroke="#f0f0f0" stroke-width="6"/>
                  <circle
                    cx="40" cy="40" r="32" fill="none"
                    :stroke="scoreColor(
                      key === 'geo'
                        ? (signal.geo.score ?? 50)
                        : (signal[key as keyof MarketSignalLatest] as any)?.score ?? 50
                    )"
                    stroke-width="6" stroke-linecap="round"
                    :stroke-dasharray="`${
                      ((key === 'geo'
                        ? (signal.geo.score ?? 50)
                        : (signal[key as keyof MarketSignalLatest] as any)?.score ?? 50) / 100) * 201
                      } 201`"
                    stroke-dashoffset="0"
                    transform="rotate(-90 40 40)"
                  />
                </svg>
                <div class="ring-center">
                  <span class="ring-score" :style="{ color: scoreColor(
                    key === 'geo'
                      ? (signal.geo.score ?? 50)
                      : (signal[key as keyof MarketSignalLatest] as any)?.score ?? 50
                  ) }">
                    {{ key === 'geo'
                      ? (signal.geo.score ?? '-')
                      : (signal[key as keyof MarketSignalLatest] as any)?.score ?? '-'
                    }}
                  </span>
                </div>
              </div>

              <!-- Quick Info -->
              <div class="quick-info">
                <p class="quick-desc">{{ LAYER_CONFIG[key]?.desc }}</p>

                <!-- Macro specific -->
                <template v-if="key === 'macro' && signal.macro">
                  <div class="mini-grid">
                    <div class="mini-item">
                      <span class="mini-label">GDP</span>
                      <span class="mini-val">{{ signal.macro.gdp_trend || '-' }}</span>
                    </div>
                    <div class="mini-item">
                      <span class="mini-label">通胀</span>
                      <span class="mini-val">{{ signal.macro.inflation_level || '-' }}</span>
                    </div>
                    <div class="mini-item">
                      <span class="mini-label">流动性</span>
                      <span class="mini-val">{{ signal.macro.liquidity || '-' }}</span>
                    </div>
                    <div class="mini-item">
                      <span class="mini-label">利率</span>
                      <span class="mini-val">{{ signal.macro.interest_rate || '-' }}</span>
                    </div>
                  </div>
                </template>

                <!-- Geo specific -->
                <template v-if="key === 'geo' && signal.geo">
                  <div class="mini-list">
                    <div class="mini-row">
                      <span class="mini-label">风险等级</span>
                      <span class="mini-val" :class="`risk-${signal.geo.risk_level}`">{{ signal.geo.risk_level === 'high' ? '高' : signal.geo.risk_level === 'medium' ? '中' : '低' }}</span>
                    </div>
                    <div class="mini-row">
                      <span class="mini-label">避险需求</span>
                      <span class="mini-val">{{ signal.geo.safe_haven_demand || '-' }}</span>
                    </div>
                  </div>
                </template>

                <!-- Industry specific -->
                <template v-if="key === 'industry' && signal.industry">
                  <div class="mini-tags">
                    <span v-if="signal.industry.recommended?.length" class="mini-tag mini-tag-green">{{ signal.industry.recommended[0] }} 推荐</span>
                    <span v-if="signal.industry.avoid?.length" class="mini-tag mini-tag-red">{{ signal.industry.avoid[0] }} 回避</span>
                    <span v-if="!signal.industry.recommended?.length && !signal.industry.avoid?.length" class="mini-tag">暂无明确信号</span>
                  </div>
                </template>

                <!-- Social specific -->
                <template v-if="key === 'social' && signal.social">
                  <div class="mini-tags">
                    <span v-for="t in (signal.social.major_themes || []).slice(0, 2)" :key="t" class="mini-tag mini-tag-dark">{{ t }}</span>
                    <span v-if="!signal.social.major_themes?.length" class="mini-tag">暂无热点主题</span>
                  </div>
                </template>

                <!-- Internal specific -->
                <template v-if="key === 'internal' && signal.internal">
                  <div class="mini-list">
                    <div class="mini-row">
                      <span class="mini-label">情绪</span>
                      <span class="mini-val">{{ signal.internal.sentiment || '-' }}</span>
                    </div>
                    <div class="mini-row">
                      <span class="mini-label">股债利差</span>
                      <span class="mini-val">{{ signal.internal.equity_bond_spread?.toFixed(2) || '-' }}%</span>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- Next Step Card -->
          <div class="dashboard-card next-step-card" @click="goToPortfolio">
            <div class="next-step-content">
              <div class="next-step-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12h14"/>
                  <path d="m12 5 7 7-7 7"/>
                </svg>
              </div>
              <div class="next-step-text">
                <div class="next-step-title">下一步</div>
                <div class="next-step-subtitle">资产组合与策略推荐</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Detail Modal -->
    <Transition name="modal">
      <div v-if="activeModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <!-- Modal Header -->
          <div class="modal-header">
            <div class="modal-title-group">
              <span class="modal-icon">
                <svg v-if="activeModal && activeModal in GeoIcons" :viewBox="GeoIcons[activeModal as keyof typeof GeoIcons].viewBox" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path v-for="(p, i) in GeoIcons[activeModal as keyof typeof GeoIcons].paths" :key="i" :d="p" />
                </svg>
              </span>
              <div>
                <h2 class="modal-title">{{ LAYER_CONFIG[activeModal!]?.title }}</h2>
                <span class="modal-weight">{{ LAYER_CONFIG[activeModal!]?.weight }}</span>
              </div>
            </div>
            <button class="modal-close" @click="closeModal">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
              </svg>
            </button>
          </div>

          <!-- Score Banner -->
          <div class="modal-score-banner" :style="{ background: scoreBg(
            activeModal === 'geo'
              ? (signal?.geo.score ?? 50)
              : (signal?.[activeModal as keyof MarketSignalLatest] as any)?.score ?? 50
          ) }">
            <div class="modal-score-val" :style="{ color: scoreColor(
              activeModal === 'geo'
                ? (signal?.geo.score ?? 50)
                : (signal?.[activeModal as keyof MarketSignalLatest] as any)?.score ?? 50
            ) }">
              {{ activeModal === 'geo'
                ? (signal?.geo.score ?? '-')
                : (signal?.[activeModal as keyof MarketSignalLatest] as any)?.score ?? '-'
              }}
            </div>
            <div class="modal-score-label">当前评分</div>
          </div>

          <!-- Modal Body -->
          <div class="modal-body">
            <!-- What -->
            <div class="explain-section">
              <h3 class="explain-title">
                <span class="explain-dot" style="background:#171717"></span>
                这是什么？
              </h3>
              <p class="explain-text">{{ LAYER_CONFIG[activeModal!]?.what }}</p>
            </div>

            <!-- Explain -->
            <div class="explain-section">
              <h3 class="explain-title">
                <span class="explain-dot" style="background:#525252"></span>
                数据怎么解读？
              </h3>
              <p class="explain-text">{{ LAYER_CONFIG[activeModal!]?.explain }}</p>
            </div>

            <!-- Impact -->
            <div class="explain-section">
              <h3 class="explain-title">
                <span class="explain-dot" style="background:#a3a3a3"></span>
                对投资有什么影响？
              </h3>
              <p class="explain-text">{{ LAYER_CONFIG[activeModal!]?.impact }}</p>
            </div>

            <!-- Factors -->
            <div class="explain-section">
              <h3 class="explain-title">
                <span class="explain-dot" style="background:#d4d4d4"></span>
                关键指标说明
              </h3>
              <div class="factor-list">
                <div v-for="f in LAYER_CONFIG[activeModal!]?.factors || []" :key="f.label" class="factor-item">
                  <span class="factor-label">{{ f.label }}</span>
                  <span class="factor-desc">{{ f.desc }}</span>
                </div>
              </div>
            </div>

            <!-- Raw Data -->
            <div v-if="activeModal === 'industry' && signal?.industry?.heatmap" class="explain-section">
              <h3 class="explain-title">
                <span class="explain-dot" style="background:#22c55e"></span>
                行业热力图
              </h3>
              <div class="heatmap-list">
                <div v-for="(score, name) in signal.industry.heatmap" :key="name" class="heatmap-item">
                  <span class="heatmap-name">{{ name }}</span>
                  <div class="heatmap-bar">
                    <div class="heatmap-fill" :style="{ width: `${score}%`, background: scoreColor(score) }"></div>
                  </div>
                  <span class="heatmap-score">{{ score }}</span>
                </div>
              </div>
            </div>

            <div v-if="activeModal === 'social' && signal?.social?.theme_strength" class="explain-section">
              <h3 class="explain-title">
                <span class="explain-dot" style="background:#d97706"></span>
                主题强度
              </h3>
              <div class="heatmap-list">
                <div v-for="(score, name) in signal.social.theme_strength" :key="name" class="heatmap-item">
                  <span class="heatmap-name">{{ name }}</span>
                  <div class="heatmap-bar">
                    <div class="heatmap-fill" :style="{ width: `${Math.min(score, 100)}%`, background: scoreColor(score) }"></div>
                  </div>
                  <span class="heatmap-score">{{ score.toFixed(1) }}</span>
                </div>
              </div>
            </div>

            <!-- Cycle Analysis (Macro modal only) -->
            <div v-if="activeModal === 'macro' && signal?.cycle_analysis" class="explain-section">
              <h3 class="explain-title">
                <span class="explain-dot" style="background:#171717"></span>
                多模型周期分析
              </h3>
              <div class="cycle-fusion-card">
                <div class="fusion-header">
                  <span class="fusion-phase">{{ signal.cycle_analysis.final_phase }}</span>
                  <span class="fusion-confidence">置信度 {{ signal.cycle_analysis.confidence }}%</span>
                </div>
                <p class="fusion-desc">{{ signal.cycle_analysis.final_description }}</p>
                <p class="fusion-asset">
                  <strong>资产偏好：</strong>{{ signal.cycle_analysis.final_asset_preference }}
                </p>
              </div>
              <div class="model-results">
                <div v-for="m in signal.cycle_analysis.model_results" :key="m.model" class="model-result-item">
                  <div class="model-result-header">
                    <span class="model-name">{{ m.model }}</span>
                    <span class="model-phase">{{ m.phase }}</span>
                  </div>
                  <p class="model-desc">{{ m.description }}</p>
                  <p class="model-asset">{{ m.asset_preference }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.signal-page {
  min-height: 100vh;
  background: #fafafa;
  position: relative;
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

.page-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.82);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.page-header-inner {
  max-width: 720px; margin: 0 auto; padding: 14px 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.header-left {
  display: flex; align-items: center; gap: 10px;
}
.back-btn {
  width: 36px; height: 36px;
  border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.7);
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.back-btn:hover { background: #fff; border-color: rgba(0,0,0,0.1); color: #171717; }
.page-title {
  font-size: 1.2rem; font-weight: 700; color: #171717;
  letter-spacing: -0.02em;
}
.refresh-btn {
  width: 36px; height: 36px;
  border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.7);
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.refresh-btn:hover { background: #fff; border-color: rgba(0,0,0,0.1); color: #171717; }
.refresh-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.signal-content {
  max-width: 720px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 16px;
  position: relative; z-index: 1;
}
.loading-state, .error-state {
  text-align: center; padding: 60px 0; color: #a3a3a3; font-size: 0.9rem;
}
.error-state { color: #ef4444; }

/* Summary Card */
.summary-card {
  background: #fff; border-radius: 20px; padding: 24px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
  display: flex; flex-direction: column;
  gap: 16px;
}
.summary-card.expanded {
  padding-bottom: 20px;
}
.summary-main {
  display: flex; align-items: center; justify-content: space-between;
}
.summary-label {
  font-size: 0.62rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 10px;
}
.summary-cycle { margin-bottom: 6px; }
.cycle-badge {
  display: inline-block; padding: 5px 13px;
  font-size: 0.85rem; font-weight: 600;
  border-radius: 8px; letter-spacing: -0.01em;
}
.badge-green { background: #f0fdf4; color: #166534; }
.badge-red { background: #fef2f2; color: #991b1b; }
.badge-amber { background: #fffbeb; color: #92400e; }
.badge-gray { background: #f5f5f5; color: #525252; }
.summary-mood { font-size: 0.82rem; color: #737373; }

.confidence-badge {
  display: inline-block; padding: 3px 10px;
  font-size: 0.7rem; font-weight: 600; color: #525252;
  background: #f5f5f5; border-radius: 6px;
  margin-left: 8px; border: 1px solid rgba(0,0,0,0.04);
}

.cycle-models {
  display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px;
}
.model-tag {
  font-size: 0.68rem; font-weight: 500; padding: 4px 10px;
  background: #fafafa; color: #737373;
  border-radius: 6px; border: 1px solid rgba(0,0,0,0.04);
  cursor: help;
}

.score-value {
  font-size: 2.2rem; font-weight: 800;
  line-height: 1; letter-spacing: -0.03em;
}
.score-label {
  font-size: 0.58rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.12em; text-transform: uppercase;
  text-align: right; margin-top: 4px;
}

/* Expand Cycle Button */
.expand-cycle-btn {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  width: 100%; padding: 10px;
  border: 1px solid rgba(0,0,0,0.06); border-radius: 12px;
  background: #fafafa; color: #737373;
  font-size: 0.78rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
}
.expand-cycle-btn:hover {
  background: #f0f0f0; color: #171717;
}
.expand-cycle-btn svg {
  transition: transform 0.3s ease;
}

/* Cycle Visualization */
.cycle-visualization {
  display: flex; flex-direction: column; gap: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(0,0,0,0.06);
}

/* Big Cycle Chart */
.cycle-chart-container {
  width: 100%;
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.06);
  padding: 16px;
}
.cycle-chart-big {
  width: 100%; height: auto;
  display: block;
}
.cycle-chart-big .axis-label-big {
  font-size: 11px;
  font-weight: 500;
}
.cycle-chart-big .phase-corner-label {
  font-size: 14px;
  font-weight: 700;
  opacity: 0.6;
}
.cycle-chart-big .current-label {
  font-size: 11px;
}

/* Phase Cards */
.phase-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.phase-card {
  padding: 14px 12px;
  background: #fafafa;
  border-radius: 12px;
  border: 2px solid transparent;
  transition: all 0.25s ease;
  text-align: center;
}
.phase-card.phase-active {
  background: #fff;
  border-color: #171717;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transform: translateY(-2px);
}
.phase-card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 6px;
}
.phase-card-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.phase-card-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #171717;
}
.phase-card-desc {
  font-size: 0.72rem;
  color: #a3a3a3;
  margin: 0;
  line-height: 1.4;
}

/* Current Position */
.current-position {
  text-align: center;
  padding: 16px;
  background: #171717;
  border-radius: 14px;
  color: #fff;
}
.position-label {
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(255,255,255,0.5);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.position-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}
.position-phase {
  font-size: 1.2rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.02em;
}
.position-coords {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.6);
  font-family: ui-monospace, SFMono-Regular, monospace;
}

/* Cycle expand transition */
.cycle-expand-enter-active,
.cycle-expand-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  max-height: 800px;
  opacity: 1;
}
.cycle-expand-enter-from,
.cycle-expand-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.dashboard-card {
  background: #fff; border-radius: 18px; padding: 18px 20px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
}
.dashboard-card:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  border-color: rgba(0,0,0,0.08);
  transform: translateY(-1px);
}

/* Card Header */
.dash-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 14px;
}
.dash-title-group {
  display: flex; align-items: center; gap: 10px;
}
.dash-icon {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: #fafafa; border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.04);
  color: #525252;
}
.dash-title {
  font-size: 0.95rem; font-weight: 700; color: #171717;
  letter-spacing: -0.02em; line-height: 1.3;
}
.dash-subtitle {
  font-size: 0.72rem; color: #a3a3a3; margin-top: 1px;
}
.dash-actions {
  display: flex; align-items: center; gap: 8px;
}
.dash-weight {
  font-size: 0.65rem; font-weight: 600; color: #d4d4d4;
  letter-spacing: 0.04em;
  padding: 3px 8px; background: #fafafa; border-radius: 6px;
  border: 1px solid rgba(0,0,0,0.04);
}
.expand-btn {
  width: 32px; height: 32px; border-radius: 8px;
  border: 1px solid rgba(0,0,0,0.06); background: #fafafa;
  display: flex; align-items: center; justify-content: center;
  color: #a3a3a3; cursor: pointer; transition: all 0.2s;
}
.expand-btn:hover {
  background: #171717; border-color: #171717; color: #fff;
  transform: scale(1.05);
}

/* Card Body */
.dash-body {
  display: flex; align-items: center; gap: 16px;
}

/* Score Ring */
.score-ring-wrap {
  position: relative; width: 72px; height: 72px; flex-shrink: 0;
}
.score-ring { width: 100%; height: 100%; }
.ring-center {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  text-align: center;
}
.ring-score {
  font-size: 1.1rem; font-weight: 800; letter-spacing: -0.02em;
}

/* Quick Info */
.quick-info { flex: 1; min-width: 0; }
.quick-desc {
  font-size: 0.78rem; color: #737373; line-height: 1.5;
  margin-bottom: 10px;
}

/* Mini Grid */
.mini-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px;
}
.mini-item {
  display: flex; flex-direction: column; gap: 1px;
  padding: 7px 10px; background: #fafafa; border-radius: 8px;
}
.mini-label { font-size: 0.65rem; color: #a3a3a3; }
.mini-val { font-size: 0.82rem; font-weight: 600; color: #171717; }

/* Mini List */
.mini-list { display: flex; flex-direction: column; gap: 6px; }
.mini-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; background: #fafafa; border-radius: 8px;
}
.mini-row .mini-label { font-size: 0.72rem; color: #525252; }
.mini-row .mini-val { font-size: 0.82rem; font-weight: 600; color: #171717; }
.risk-high { color: #ef4444 !important; }
.risk-medium { color: #d97706 !important; }
.risk-low { color: #22c55e !important; }

/* Mini Tags */
.mini-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.mini-tag {
  font-size: 0.72rem; font-weight: 500; padding: 5px 10px;
  border-radius: 8px; background: #f5f5f5; color: #525252;
  border: 1px solid rgba(0,0,0,0.04);
}
.mini-tag-green { background: #f0fdf4; color: #166534; border-color: rgba(34,197,94,0.12); }
.mini-tag-red { background: #fef2f2; color: #991b1b; border-color: rgba(239,68,68,0.12); }
.mini-tag-dark { background: #171717; color: #fff; border-color: transparent; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(8px);
  display: flex; align-items: flex-end; justify-content: center;
  padding: 0;
}
.modal-content {
  background: #fff; border-radius: 24px 24px 0 0;
  width: 100%; max-width: 720px; max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 -8px 40px rgba(0,0,0,0.15);
  animation: modalSlideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes modalSlideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  position: sticky; top: 0; background: #fff; z-index: 2;
}
.modal-title-group {
  display: flex; align-items: center; gap: 12px;
}
.modal-icon {
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  background: #fafafa; border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.04);
  color: #525252;
}
.modal-title {
  font-size: 1.1rem; font-weight: 700; color: #171717;
  letter-spacing: -0.02em; margin: 0;
}
.modal-weight {
  font-size: 0.72rem; color: #a3a3a3; font-weight: 500;
}
.modal-close {
  width: 36px; height: 36px; border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.06); background: #fafafa;
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.modal-close:hover { background: #171717; border-color: #171717; color: #fff; }

.modal-score-banner {
  padding: 20px 24px;
  display: flex; align-items: center; gap: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}
.modal-score-val {
  font-size: 2rem; font-weight: 800; letter-spacing: -0.03em;
}
.modal-score-label {
  font-size: 0.75rem; color: #a3a3a3; font-weight: 500;
}

.modal-body {
  padding: 20px 24px 32px;
  display: flex; flex-direction: column; gap: 24px;
}

.explain-section {}
.explain-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.88rem; font-weight: 700; color: #171717;
  margin: 0 0 10px; letter-spacing: -0.01em;
}
.explain-dot {
  width: 8px; height: 8px; border-radius: 50%;
  flex-shrink: 0;
}
.explain-text {
  font-size: 0.82rem; color: #525252; line-height: 1.7;
  margin: 0;
}

.factor-list {
  display: flex; flex-direction: column; gap: 8px;
}
.factor-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 10px 14px; background: #fafafa; border-radius: 10px;
}
.factor-label {
  font-size: 0.82rem; font-weight: 600; color: #171717;
}
.factor-desc {
  font-size: 0.75rem; color: #a3a3a3; line-height: 1.5;
}

.heatmap-list {
  display: flex; flex-direction: column; gap: 8px;
}
.heatmap-item {
  display: flex; align-items: center; gap: 10px;
}
.heatmap-name {
  font-size: 0.8rem; color: #525252; width: 60px; flex-shrink: 0;
}
.heatmap-bar {
  flex: 1; height: 6px; background: #f0f0f0; border-radius: 999px; overflow: hidden;
}
.heatmap-fill { height: 100%; border-radius: 999px; transition: width 0.5s ease; }
.heatmap-score {
  font-size: 0.75rem; font-weight: 600; color: #171717; width: 32px; text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Cycle Analysis */
.cycle-fusion-card {
  background: #fafafa; border-radius: 14px; padding: 16px 18px;
  border: 1px solid rgba(0,0,0,0.04); margin-bottom: 14px;
}
.fusion-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px;
}
.fusion-phase {
  font-size: 1rem; font-weight: 700; color: #171717;
  letter-spacing: -0.02em;
}
.fusion-confidence {
  font-size: 0.72rem; font-weight: 600; color: #22c55e;
  padding: 4px 10px; background: #f0fdf4; border-radius: 6px;
}
.fusion-desc {
  font-size: 0.82rem; color: #525252; line-height: 1.6; margin: 0 0 8px;
}
.fusion-asset {
  font-size: 0.78rem; color: #737373; margin: 0;
}
.fusion-asset strong { color: #171717; font-weight: 600; }

.model-results {
  display: flex; flex-direction: column; gap: 10px;
}
.model-result-item {
  padding: 14px 16px; background: #fafafa; border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.04);
}
.model-result-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}
.model-name {
  font-size: 0.82rem; font-weight: 600; color: #171717;
}
.model-phase {
  font-size: 0.75rem; font-weight: 600; color: #525252;
  padding: 3px 10px; background: #fff; border-radius: 6px;
  border: 1px solid rgba(0,0,0,0.06);
}
.model-desc {
  font-size: 0.78rem; color: #737373; line-height: 1.5; margin: 0 0 4px;
}
.model-asset {
  font-size: 0.72rem; color: #a3a3a3; margin: 0;
}

/* Modal Transition */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: translateY(100%);
}

/* Next Step Card */
.next-step-card {
  background: #171717;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}
.next-step-card:hover {
  background: #262626;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}
.next-step-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
}
.next-step-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.next-step-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
}
.next-step-subtitle {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.5);
}

/* Responsive */
@media (max-width: 480px) {
  .phase-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .cycle-chart-container {
    padding: 8px;
  }
  .position-detail {
    flex-direction: column;
    gap: 6px;
  }
}

@media (min-width: 640px) {
  .dashboard-grid {
    grid-template-columns: 1fr 1fr;
  }
  .modal-overlay {
    align-items: center;
    padding: 24px;
  }
  .modal-content {
    border-radius: 24px;
    max-height: 85vh;
  }
}

@media (min-width: 768px) {
  .signal-content { padding: 24px 32px 40px; }
  .dashboard-grid { gap: 14px; }
}
</style>

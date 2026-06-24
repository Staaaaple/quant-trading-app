<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { portfolioApi, type PortfolioDesignResult, type PortfolioProgressEvent, type PortfolioTask } from '@/api/portfolio'
import { profileApi, type InvestorProfile } from '@/api/profile'
import { marketSignalApi } from '@/api/marketSignal'
import LegalNotice from '@/components/LegalNotice.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// ── 从 sessionStorage 或 API 获取组合数据 ──
const portfolioData = ref<PortfolioDesignResult | null>(null)
const loading = ref(true)
const error = ref('')

// ── 任务化构建状态 ──
const taskId = ref<number | null>(null)
let pollTimer: number | null = null
const POLL_INTERVAL_MS = 2000

// 演示用户 30 秒组合动画只播放一次（每次切换回演示用户后重置）
const DEMO_ANIMATION_KEY = 'demo_portfolio_animation_shown'

function isDemoAnimationShown() {
  return sessionStorage.getItem(DEMO_ANIMATION_KEY) === '1'
}

function markDemoAnimationShown() {
  sessionStorage.setItem(DEMO_ANIMATION_KEY, '1')
}

/** 隐秘重置：清除演示动画已播放标记，下次进入会重新播放 */
function resetDemoAnimation() {
  sessionStorage.removeItem(DEMO_ANIMATION_KEY)
  sessionStorage.removeItem('latest_portfolio')
  window.location.reload()
}

// ── 组合构建状态 ──
const isBuilding = ref(false)
const buildingElapsed = ref(0)
const buildingEstimate = ref<number | null>(null)
const buildingSteps = ref([
  { label: '分析投资者画像', active: true, done: false },
  { label: '获取市场信号', active: false, done: false },
  { label: 'Hybrid引擎匹配策略', active: false, done: false },
  { label: 'RAG质检引擎审核', active: false, done: false },
  { label: '生成最终组合', active: false, done: false },
])

// 获取 SAA 权重（真实数据）
const saaWeights = computed(() => {
  return portfolioData.value?.portfolio?.saa?.weights || {
    stock: 0.45,
    bond: 0.35,
    commodity: 0.12,
    cash: 0.08,
  }
})

// 构建资产配置数据（从后端 SAA 权重 + bindings）
const assetAllocation = computed(() => {
  const weights = saaWeights.value
  const bindings = portfolioData.value?.portfolio?.bindings || []

  // 按资产类别分组 holdings
  const holdingsByAsset: Record<string, Array<{name: string, code: string, weight: number, reason: string}>> = {
    stock: [],
    etf: [],
    bond: [],
    commodity: [],
    cash: [],
  }

  bindings.forEach((b: any) => {
    const assetClass = b.asset_class?.toLowerCase() || 'stock'
    const target = holdingsByAsset[assetClass] || holdingsByAsset.stock
    target.push({
      name: b.name || b.symbol,
      code: b.symbol,
      weight: Math.round((b.weight || 0) * 100),
      reason: b.reasoning || b.data_source || '策略绑定',
    })
  })

  // 如果没有 bindings，使用默认配置
  if (bindings.length === 0) {
    holdingsByAsset.stock = [{ name: '沪深300ETF', code: '510300', weight: 100, reason: '核心宽基指数' }]
    holdingsByAsset.bond = [{ name: '国债ETF', code: '511010', weight: 100, reason: '无信用风险' }]
    holdingsByAsset.commodity = [{ name: '黄金ETF', code: '518880', weight: 100, reason: '避险资产' }]
    holdingsByAsset.cash = [{ name: '银华日利', code: '511880', weight: 100, reason: '场内货币基金' }]
  }

  return [
    {
      id: 'stock',
      name: '股票',
      pct: Math.round((weights.stock || 0) * 100),
      color: '#171717',
      desc: 'A股核心资产+行业龙头',
      holdings: holdingsByAsset.stock,
    },
    {
      id: 'etf',
      name: 'ETF',
      pct: Math.round((weights.etf || 0) * 100),
      color: '#404040',
      desc: '行业/主题ETF分散配置',
      holdings: holdingsByAsset.etf,
    },
    {
      id: 'bond',
      name: '债券',
      pct: Math.round((weights.bond || 0) * 100),
      color: '#525252',
      desc: '国债+高等级信用债',
      holdings: holdingsByAsset.bond,
    },
    {
      id: 'commodity',
      name: '商品',
      pct: Math.round((weights.commodity || 0) * 100),
      color: '#a3a3a3',
      desc: '黄金+大宗商品',
      holdings: holdingsByAsset.commodity,
    },
    {
      id: 'cash',
      name: '现金',
      pct: Math.round((weights.cash || 0) * 100),
      color: '#d4d4d4',
      desc: '货币基金+活期存款',
      holdings: holdingsByAsset.cash,
    },
  ]
})

// ── 展开状态 ──
const expandedAsset = ref<string | null>(null)
const showBuyGuide = ref(false)
const activeAssetName = ref('')

function toggleAsset(id: string) {
  expandedAsset.value = expandedAsset.value === id ? null : id
}

function openBuyGuide(assetName: string) {
  activeAssetName.value = assetName
  showBuyGuide.value = true
  document.body.style.overflow = 'hidden'
}

function closeBuyGuide() {
  showBuyGuide.value = false
  activeAssetName.value = ''
  document.body.style.overflow = ''
}

function goBack() {
  router.push('/')
}

function goNext() {
  router.push('/portfolio/strategies/guide')
}

function goToEcosystem() {
  router.push('/ecosystem')
}

function goProfile() {
  router.push('/profile')
}

function goBuildingGuide() {
  router.push('/building-guide')
}

// ── 各资产购买指引 ──
interface BuyGuide {
  channels: string[]
  steps: string[]
  tips: string[]
  examples: { name: string; code: string; desc: string }[]
}

const BUY_GUIDES: Record<string, BuyGuide> = {
  '股票': {
    channels: ['证券账户（股票/ETF）', '场外基金账户（ETF联接基金）'],
    steps: [
      '在券商 APP 交易界面输入 ETF 代码，如 510300（沪深300ETF）',
      '查看实时价格、涨跌幅和盘口挂单量',
      '选择「买入」，输入数量（100 份的整数倍）',
      '交易时间：9:30-11:30、13:00-15:00',
      '成交后在「持仓」中核对数量和成本',
    ],
    tips: [
      'ETF 最小买入单位为 100 份（1手）',
      '建议使用限价单，避免盘中突然拉升时追高',
      '优先选择日均成交额 > 1 亿的 ETF，流动性更好',
    ],
    examples: [
      { name: '沪深300ETF', code: '510300', desc: 'A股核心宽基指数' },
      { name: '中证500ETF', code: '510500', desc: '中小盘成长代表' },
      { name: '创业板ETF', code: '159915', desc: '创业板核心资产' },
    ],
  },
  '债券': {
    channels: ['证券账户（债券ETF/国债逆回购）', '场外基金账户（债券基金）'],
    steps: [
      '搜索债券 ETF，如 511010（国债ETF）或 511220（城投债ETF）',
      '与股票 ETF 一样按 100 份整数倍买入',
      '收盘后闲置资金可做 1 天期国债逆回购（代码 204001）',
      '场外路径：理财/基金 → 搜索债券基金代码 → 申购',
      '确认债券类资产占组合目标比例',
    ],
    tips: [
      '利率下行周期，长久期债券价格上涨；利率上行周期，短久期债券更抗跌',
      '国债逆回购在月末、季末、年末收益率通常更高',
      '信用债 ETF 收益更高，但需要关注信用风险',
    ],
    examples: [
      { name: '国债ETF', code: '511010', desc: '无信用风险，波动小' },
      { name: '十年国债ETF', code: '019547', desc: '长久期，利率敏感' },
      { name: '银华日利', code: '511880', desc: '场内货币基金，流动性好' },
    ],
  },
  '商品': {
    channels: ['证券账户（商品ETF/黄金ETF）', '场外基金账户（黄金ETF联接）'],
    steps: [
      '搜索黄金 ETF，如 518880（黄金 ETF）',
      '按 100 份整数倍买入，交易规则与股票 ETF 相同',
      '或选择场外黄金 ETF 联接基金（如 000216）',
      '关注国际金价、美元指数和地缘风险事件',
      '商品配置一般不超过组合的 15%',
    ],
    tips: [
      '黄金适合作为「保险」配置，不宜重仓',
      '通胀预期升温、地缘风险加剧时可适当增加比例',
      '商品 ETF 跟踪现货或期货价格，注意跟踪误差',
    ],
    examples: [
      { name: '黄金ETF', code: '518880', desc: '国内流动性最好的黄金ETF' },
      { name: '黄金ETF联接', code: '000216', desc: '场外申购，无需证券账户' },
    ],
  },
  '现金': {
    channels: [
      '券商/股票 APP：场内货币基金、国债逆回购、券商余额理财',
      '银行 APP / 支付宝 / 微信理财通 / 天天基金：场外货币基金',
    ],
    steps: [
      '场内货币基金：在券商 APP 交易界面搜索 511880（银华日利）或 511990（华宝添益），像买股票一样按 100 份整数倍买入。',
      '场外货币基金：在银行 APP、支付宝、微信理财通或天天基金搜索基金代码（如 003474、000198）申购，T+1 确认。',
      '国债逆回购：在券商 APP 找到「国债理财/逆回购」专区，选择 1 天期 204001（沪市）或 131810（深市）出借资金。',
      '券商余额理财：在券商 APP 开通「余额自动理财」，收盘后闲置资金自动转入货币基金。',
      '保留部分现金在银行卡或证券账户余额，用于逢低加仓。',
    ],
    tips: [
      '货币基金 T+1 可取，适合存放备用金',
      '国债逆回购到期自动到账，节假日前的收益通常更高',
      '现金管理的核心是「随取随用」，不要追求高收益而牺牲流动性',
    ],
    examples: [
      { name: '银华日利', code: '511880', desc: '场内货币基金，T+0 交易' },
      { name: '华宝添益', code: '511990', desc: '场内货币基金，规模大' },
      { name: '国债逆回购', code: '204001', desc: '1 天期，收盘后出借闲置资金' },
    ],
  },
}

const activeGuide = computed(() => BUY_GUIDES[activeAssetName.value] || null)

// ── 构建流程 ──
function estimateRemainingTime(elapsedMs: number): number {
  const elapsedSec = elapsedMs / 1000
  const scenarios = [
    { maxDuration: 5, label: 'fast' },
    { maxDuration: 14, label: 'normal' },
    { maxDuration: 25, label: 'poor' },
    { maxDuration: 50, label: 'worst' },
  ]
  for (const s of scenarios) {
    if (elapsedSec < s.maxDuration) {
      return Math.max(1, Math.ceil(s.maxDuration - elapsedSec))
    }
  }
  return Math.max(1, Math.ceil(50 - elapsedSec))
}

function getSmoothedEstimate(elapsedMs: number, prev: number | null): number {
  const raw = estimateRemainingTime(elapsedMs)
  return prev === null ? raw : Math.min(prev, raw)
}

function updateBuildingStepsFromProgress(step: string | undefined, message?: string) {
  // 重置所有步骤状态
  buildingSteps.value.forEach((s) => {
    s.active = false
    s.done = false
  })

  // 根据后端进度点亮步骤
  const stepOrder: Record<string, number> = {
    start: 0,
    saa: 1,
    saa_review: 2,
    taa: 2,
    taa_review: 2,
    binding: 3,
    dynamic_picker: 3,
    backtest: 3,
    binding_review: 4,
    risk_config: 4,
    risk_review: 4,
    reliability: 4,
    reliability_review: 4,
    lifespan: 5,
    final_review: 5,
    done: 5,
  }

  const activeIndex = step ? stepOrder[step] ?? 2 : 2

  buildingSteps.value.forEach((s, idx) => {
    if (idx < activeIndex) {
      s.done = true
    } else if (idx === activeIndex) {
      s.active = true
    }
  })

  // 可选：把当前消息显示在某一步上
  if (message && activeIndex >= 0 && activeIndex < buildingSteps.value.length) {
    buildingSteps.value[activeIndex].label = message
  }
}

async function readSSEStream(
  response: Response,
  onEvent: (event: PortfolioProgressEvent) => void,
) {
  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim()
        if (data && data !== 'heartbeat') {
          try {
            onEvent(JSON.parse(data))
          } catch (e) {
            console.warn('Failed to parse SSE event:', data)
          }
        }
      }
    }
  }
}

async function designPortfolioWithRAG() {
  try {
    // 加载画像
    const p = await profileApi.getMine()
    if (!p) {
      error.value = '未能加载画像数据，请先完成问卷'
      isBuilding.value = false
      return
    }

    // 加载市场信号
    let signal = null
    try {
      signal = await marketSignalApi.getLatest()
      if (signal) {
        sessionStorage.setItem('latest_market_signal', JSON.stringify(signal))
      }
    } catch (e) {
      console.error('Failed to load market signal:', e)
    }

    // 构建画像向量
    const profileVector = {
      risk_tolerance: p.risk_tolerance,
      loss_aversion: p.loss_aversion,
      herding_tendency: p.herding_tendency,
      overconfidence: p.overconfidence,
      delayed_gratification: p.delayed_gratification,
      security_need: p.security_need,
      time_horizon_score: p.time_horizon_score,
      experience_level: p.experience_level,
      capital_tier: p.capital_tier,
      income_stability: p.income_stability,
      debt_pressure: p.debt_pressure,
      information_processing: p.information_processing,
      social_pressure: p.social_pressure,
      emergency_response: p.emergency_response,
      anchoring_effect: p.anchoring_effect,
      diversification_preference: p.diversification_preference,
      stop_loss_discipline: p.stop_loss_discipline,
      emotional_stability: p.emotional_stability,
    }

    const marketSignal = {
      macro_score: signal?.macro?.score ?? 0.5,
      geo_risk: signal?.geo?.overall_risk ?? 0.5,
      industry_scores: signal?.industry?.heatmap ?? {},
      social_trends: signal?.social?.major_themes ?? [],
    }

    // 使用 SSE 流式调用
    const response = await portfolioApi.designStream({
      profile_vector: profileVector,
      market_signal: marketSignal,
      use_dynamic_picker: false,
    })

    if (!response.ok) {
      throw new Error(`design-with-rag/stream failed: ${response.status}`)
    }

    await readSSEStream(response, (event) => {
      if (event.type === 'task' && event.task_id) {
        taskId.value = event.task_id
        localStorage.setItem('portfolio_task_id', String(event.task_id))
      } else if (event.type === 'progress') {
        updateBuildingStepsFromProgress(event.step, event.message)
      } else if (event.type === 'result') {
        const result = event.portfolio
        portfolioData.value = result
        sessionStorage.setItem('latest_portfolio', JSON.stringify(result))
      } else if (event.type === 'error') {
        throw new Error(event.message_error || '组合生成失败')
      }
    })
  } catch (e: any) {
    console.error('Failed to design portfolio:', e)
    error.value = '组合生成失败，请返回首页重试'
  } finally {
    isBuilding.value = false
  }
}

/** 提交异步设计任务并通过轮询跟踪进度 */
async function submitDesignTask() {
  try {
    // 加载画像
    const p = await profileApi.getMine()
    if (!p) {
      error.value = '未能加载画像数据，请先完成问卷'
      isBuilding.value = false
      return
    }

    // 加载市场信号
    let signal = null
    try {
      signal = await marketSignalApi.getLatest()
      if (signal) {
        sessionStorage.setItem('latest_market_signal', JSON.stringify(signal))
      }
    } catch (e) {
      console.error('Failed to load market signal:', e)
    }

    // 构建画像向量
    const profileVector = {
      risk_tolerance: p.risk_tolerance,
      loss_aversion: p.loss_aversion,
      herding_tendency: p.herding_tendency,
      overconfidence: p.overconfidence,
      delayed_gratification: p.delayed_gratification,
      security_need: p.security_need,
      time_horizon_score: p.time_horizon_score,
      experience_level: p.experience_level,
      capital_tier: p.capital_tier,
      income_stability: p.income_stability,
      debt_pressure: p.debt_pressure,
      information_processing: p.information_processing,
      social_pressure: p.social_pressure,
      emergency_response: p.emergency_response,
      anchoring_effect: p.anchoring_effect,
      diversification_preference: p.diversification_preference,
      stop_loss_discipline: p.stop_loss_discipline,
      emotional_stability: p.emotional_stability,
    }

    const marketSignal = {
      macro_score: signal?.macro?.score ?? 0.5,
      geo_risk: signal?.geo?.overall_risk ?? 0.5,
      industry_scores: signal?.industry?.heatmap ?? {},
      social_trends: signal?.social?.major_themes ?? [],
    }

    // 提交异步任务
    const task = await portfolioApi.designAsync({
      profile_vector: profileVector,
      market_signal: marketSignal,
      use_dynamic_picker: false,
    })

    if (task?.task_id) {
      taskId.value = task.task_id
      localStorage.setItem('portfolio_task_id', String(task.task_id))
      pollTaskStatus(task.task_id)
    } else {
      throw new Error('No task_id returned')
    }
  } catch (e: any) {
    console.error('Failed to submit design task:', e)
    error.value = '组合生成失败，请返回首页重试'
    isBuilding.value = false
  } finally {
    loading.value = false
  }
}

/** 轮询任务状态 */
async function pollTaskStatus(id: number) {
  if (pollTimer) {
    window.clearTimeout(pollTimer)
    pollTimer = null
  }

  try {
    const task = await portfolioApi.getTaskStatus(id)
    taskId.value = task.task_id

    if (task.status === 'completed' && task.result) {
      portfolioData.value = task.result as PortfolioDesignResult
      sessionStorage.setItem('latest_portfolio', JSON.stringify(task.result))
      loading.value = false
      isBuilding.value = false
      return
    }

    if (task.status === 'failed') {
      error.value = task.error_message || '组合生成失败'
      loading.value = false
      isBuilding.value = false
      return
    }

    // running / pending：继续轮询
    isBuilding.value = true
    loading.value = false
    updateBuildingStepsFromProgress(
      task.current_step,
      task.current_step ? `进度 ${Math.round((task.progress || 0) * 100)}%` : undefined,
    )
    pollTimer = window.setTimeout(() => pollTaskStatus(id), POLL_INTERVAL_MS)
  } catch (e: any) {
    console.error('Failed to poll task status:', e)
    error.value = '获取任务状态失败'
    loading.value = false
    isBuilding.value = false
  }
}

function startBuildingProcess() {
  if (userStore.isDemo) {
    if (isDemoAnimationShown()) {
      loadDemoPortfolioDirectly()
    } else {
      runDemoBuild()
    }
    return
  }
  isBuilding.value = true
  loading.value = false
  error.value = ''

  // 初始状态：分析投资者画像已完成，获取市场信号已完成
  updateBuildingStepsFromProgress('start')

  submitDesignTask()
}

/** 演示用户：30 秒加载动画 + 预置组合 */
async function runDemoBuild() {
  isBuilding.value = true
  loading.value = false
  error.value = ''
  buildingEstimate.value = 30
  buildingElapsed.value = 0
  updateBuildingStepsFromProgress('start')
  sessionStorage.removeItem('latest_portfolio')
  portfolioData.value = null

  const startTime = Date.now()
  const interval = window.setInterval(() => {
    const elapsedSec = Math.floor((Date.now() - startTime) / 1000)
    buildingElapsed.value = elapsedSec
    buildingEstimate.value = Math.max(0, 30 - elapsedSec)

    if (elapsedSec === 6) updateBuildingStepsFromProgress('market_signal')
    else if (elapsedSec === 12) updateBuildingStepsFromProgress('binding')
    else if (elapsedSec === 18) updateBuildingStepsFromProgress('risk_config')
    else if (elapsedSec === 24) updateBuildingStepsFromProgress('reliability')
    else if (elapsedSec === 28) updateBuildingStepsFromProgress('final_review')
  }, 1000)

  try {
    const task = await portfolioApi.designAsync({ profile_vector: {}, market_signal: {} } as any)
    if (!task.task_id) {
      throw new Error('演示任务创建失败')
    }

    let current = await portfolioApi.getTaskStatus(task.task_id)
    let safety = 0
    while ((current.status === 'pending' || current.status === 'running') && safety < 120) {
      await new Promise(r => setTimeout(r, 500))
      current = await portfolioApi.getTaskStatus(task.task_id)
      safety += 1
    }

    // 保证至少播放 30 秒动画
    const elapsed = Date.now() - startTime
    const remaining = Math.max(0, 30000 - elapsed)
    if (remaining > 0) {
      await new Promise(r => setTimeout(r, remaining))
    }

    if (current.status === 'completed' && current.result?.portfolio) {
      portfolioData.value = current.result as PortfolioDesignResult
      sessionStorage.setItem('latest_portfolio', JSON.stringify(current.result))
      markDemoAnimationShown()
    } else {
      error.value = current.error_message || '演示数据加载失败'
    }
  } catch (e: any) {
    error.value = e.message || '演示数据加载失败'
  } finally {
    window.clearInterval(interval)
    isBuilding.value = false
    loading.value = false
  }
}

/** 演示用户：已播放过动画，直接加载预置组合 */
async function loadDemoPortfolioDirectly() {
  loading.value = true
  isBuilding.value = false
  error.value = ''
  try {
    // 优先使用 sessionStorage 缓存，避免重复请求
    const cached = sessionStorage.getItem('latest_portfolio')
    if (cached) {
      try {
        portfolioData.value = JSON.parse(cached)
        loading.value = false
        return
      } catch (e) {
        console.error('Failed to parse cached portfolio:', e)
      }
    }
    const task = await portfolioApi.designAsync({ profile_vector: {}, market_signal: {} } as any)
    if (task.status === 'completed' && task.result?.portfolio) {
      portfolioData.value = task.result as PortfolioDesignResult
      sessionStorage.setItem('latest_portfolio', JSON.stringify(task.result))
    } else {
      throw new Error('演示数据加载失败')
    }
  } catch (e: any) {
    error.value = e.message || '演示数据加载失败'
  } finally {
    loading.value = false
  }
}

/** 重新生成（使用 SSE 实时进度） */
function regenerateWithSSE() {
  if (userStore.isDemo) {
    runDemoBuild()
    return
  }
  if (pollTimer) {
    window.clearTimeout(pollTimer)
    pollTimer = null
  }
  localStorage.removeItem('portfolio_task_id')
  sessionStorage.removeItem('latest_portfolio')
  taskId.value = null
  portfolioData.value = null
  startBuildingProcessWithSSE()
}

function startBuildingProcessWithSSE() {
  if (userStore.isDemo) {
    if (isDemoAnimationShown()) {
      loadDemoPortfolioDirectly()
    } else {
      runDemoBuild()
    }
    return
  }
  isBuilding.value = true
  loading.value = false
  error.value = ''
  updateBuildingStepsFromProgress('start')
  designPortfolioWithRAG().finally(() => {
    loading.value = false
  })
}

// ── 环形图计算 ──
const donutSegments = computed(() => {
  const total = assetAllocation.value.reduce((s, a) => s + a.pct, 0)
  let offset = 0
  return assetAllocation.value.map(a => {
    const dash = (a.pct / total) * 289
    const seg = { ...a, dash, offset }
    offset -= dash
    return seg
  })
})

const totalPct = computed(() => assetAllocation.value.reduce((s, a) => s + a.pct, 0))

// ── 风控配置 ──
const riskConfig = computed(() => {
  return portfolioData.value?.portfolio?.risk_config || {
    stop_loss: 0.08,
    max_position: 0.20,
    max_drawdown: 0.15,
    rebalance_threshold: 0.05,
  }
})

// ── 可靠性 ──
const reliability = computed(() => {
  return portfolioData.value?.portfolio?.reliability || {
    confidence: 0.6,
    reliability_level: '中',
  }
})

// ── 采纳状态 ──
const adoptionStatus = computed(() => {
  return portfolioData.value?.portfolio?.reliability?.adoption_status || null
})

const isAdopted = computed(() => {
  return adoptionStatus.value?.adopted ?? false
})

// ── 基准对比 ──
const benchmarkComparison = computed(() => {
  return portfolioData.value?.portfolio?.reliability?.benchmark_comparison || null
})

const benchmarkMetrics = computed(() => {
  if (!benchmarkComparison.value) return []
  return [
    benchmarkComparison.value.custom_benchmark,
    benchmarkComparison.value.csi300,
    benchmarkComparison.value.equal_weight,
    benchmarkComparison.value.sixty_forty,
  ].filter(Boolean)
})

const overallBenchmarkScore = computed(() => {
  return benchmarkComparison.value?.overall_score ?? 0
})

// ── 组合寿命 ──
const portfolioLifespan = computed(() => {
  return portfolioData.value?.portfolio?.portfolio_lifespan || 12
})

// ── 加载数据 ──
onMounted(() => {
  // 演示用户：跳过本地缓存，直接走演示构建流程
  if (userStore.isDemo) {
    localStorage.removeItem('portfolio_task_id')
    // 只有还没播放过动画时才清除缓存，让动画完整加载；已播放过则保留缓存直接显示
    if (!isDemoAnimationShown()) {
      sessionStorage.removeItem('latest_portfolio')
    }
    startBuildingProcess()
    return
  }

  // 1. 优先从 localStorage 读取任务 ID（刷新/断线恢复）
  const storedTaskId = localStorage.getItem('portfolio_task_id')
  if (storedTaskId) {
    const id = parseInt(storedTaskId, 10)
    if (!isNaN(id)) {
      taskId.value = id
      loading.value = true
      pollTaskStatus(id)
      return
    }
  }

  // 2. 兼容旧逻辑：从 sessionStorage 读取结果
  const stored = sessionStorage.getItem('latest_portfolio')
  if (stored) {
    try {
      portfolioData.value = JSON.parse(stored)
      loading.value = false
      return
    } catch (e) {
      console.error('Failed to parse stored portfolio:', e)
    }
  }

  // 3. 没有任务也没有结果，进入构建等待模式
  startBuildingProcess()
})
</script>

<template>
  <div class="portfolio-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-label">PORTFOLIO</span>
          <span class="header-name">资产组合</span>
        </div>
        <button
          v-if="userStore.isDemo"
          class="demo-reset-btn"
          title="重置演示动画"
          @click="resetDemoAnimation"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
          </svg>
        </button>
        <div v-else style="width: 36px"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="portfolio-content">
      <LegalNotice
        title="组合构建声明"
        :show-data-source="true"
        :show-investment-disclaimer="true"
        :show-privacy="true"
        :show-license="true"
        :show-crawler="false"
      />

      <!-- Loading -->
      <div v-if="loading" class="loading-state">加载组合数据中...</div>

      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button class="btn-primary" @click="goBack">返回首页</button>
      </div>

      <!-- Building State -->
      <div v-else-if="isBuilding" class="building-state">
        <div class="building-animation">
          <div class="building-spinner"></div>
          <div class="building-pulse"></div>
        </div>
        <h2 class="building-title">正在构建您的投资组合</h2>
        <p class="building-subtitle">Hybrid + RAG 双引擎运行中</p>
        <div class="building-steps">
          <div
            v-for="(step, idx) in buildingSteps"
            :key="idx"
            class="step-item"
            :class="{ active: step.active, done: step.done }"
          >
            <div class="step-dot">
              <svg
                v-if="step.done"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <span class="step-label">{{ step.label }}</span>
          </div>
        </div>
        <div class="guide-card" @click="goBuildingGuide">
          <div class="guide-icon">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
          </div>
          <div class="guide-content">
            <p class="guide-title">还没有投资账户？</p>
            <p class="guide-desc">3分钟学会开户，跟着引导一步步来</p>
          </div>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        </div>
      </div>

      <template v-else>
        <!-- Adoption Alert -->
        <div v-if="adoptionStatus && !isAdopted" class="adoption-alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <triangle points="12 2 22 20 2 20" />
            <line x1="12" y1="10" x2="12" y2="14" />
            <line x1="12" y1="18" x2="12.01" y2="18" />
          </svg>
          <div class="adoption-alert-content">
            <div class="adoption-alert-title">组合未达采纳标准</div>
            <div class="adoption-alert-desc">
              {{ adoptionStatus.reason }}
            </div>
          </div>
        </div>

        <div v-else-if="adoptionStatus && isAdopted" class="adoption-success">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span>{{ adoptionStatus.reason }}</span>
        </div>

        <!-- Reliability Banner -->
        <div class="reliability-banner" v-if="reliability">
          <div class="reliability-item">
            <span class="reliability-label">可靠性</span>
            <span class="reliability-val" :class="`level-${reliability.reliability_level}`">
              {{ reliability.reliability_level }}
            </span>
          </div>
          <div class="reliability-item">
            <span class="reliability-label">置信度</span>
            <span class="reliability-val">{{ Math.round((reliability.confidence || 0) * 100) }}%</span>
          </div>
          <div class="reliability-item">
            <span class="reliability-label">采纳状态</span>
            <span class="reliability-val" :class="isAdopted ? 'level-高' : 'level-低'">
              {{ isAdopted ? '已采纳' : '未达标' }}
            </span>
          </div>
          <div class="reliability-item clickable" @click="goToEcosystem">
            <span class="reliability-label">组合寿命</span>
            <span class="reliability-val">{{ portfolioLifespan }}月</span>
          </div>
        </div>

        <!-- Benchmark Comparison Card -->
        <div class="benchmark-card" v-if="benchmarkComparison">
          <div class="benchmark-header">
            <span class="benchmark-label">基准对比</span>
            <span class="benchmark-sub">策略 vs 多种被动持有方案</span>
          </div>
          <div class="benchmark-list">
            <div
              v-for="metric in benchmarkMetrics"
              :key="metric.name"
              class="benchmark-item"
            >
              <div class="benchmark-info">
                <div class="benchmark-name">{{ metric.name }}</div>
                <div class="benchmark-desc">{{ metric.description }}</div>
              </div>
              <div class="benchmark-returns">
                <div class="benchmark-return">
                  <span class="return-label">基准</span>
                  <span class="return-val" :class="metric.benchmark_return >= 0 ? 'positive' : 'negative'">
                    {{ (metric.benchmark_return * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="benchmark-return">
                  <span class="return-label">策略</span>
                  <span class="return-val" :class="metric.strategy_return >= 0 ? 'positive' : 'negative'">
                    {{ (metric.strategy_return * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="benchmark-return">
                  <span class="return-label">超额</span>
                  <span class="return-val" :class="metric.excess_return >= 0 ? 'positive' : 'negative'">
                    {{ (metric.excess_return * 100).toFixed(1) }}%
                  </span>
                </div>
              </div>
              <div class="benchmark-passed" :class="metric.passed ? 'passed' : 'failed'">
                {{ metric.passed ? '跑赢' : '跑输' }}
              </div>
            </div>
          </div>
          <div class="benchmark-overall">
            <div class="benchmark-overall-label">综合评分</div>
            <div class="benchmark-progress">
              <div class="benchmark-progress-bar" :style="{ width: `${overallBenchmarkScore * 100}%` }"></div>
            </div>
            <div class="benchmark-overall-score">{{ Math.round(overallBenchmarkScore * 100) }}%</div>
          </div>
        </div>

        <!-- Allocation Chart -->
        <div class="alloc-card">
          <div class="alloc-header">
            <span class="alloc-label">资产配置</span>
            <span class="alloc-sub">基于画像风险等级与市场周期动态调整</span>
          </div>

          <div class="donut-wrap">
            <svg viewBox="0 0 120 120" class="donut-svg">
              <circle cx="60" cy="60" r="46" fill="none" stroke="#f0f0f0" stroke-width="12"/>
              <circle
                v-for="seg in donutSegments"
                :key="seg.id"
                cx="60" cy="60" r="46" fill="none"
                :stroke="seg.color"
                stroke-width="12" stroke-linecap="round"
                :stroke-dasharray="`${seg.dash} 289`"
                :stroke-dashoffset="seg.offset"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="donut-center">
              <div class="donut-total">{{ totalPct }}%</div>
              <div class="donut-total-label">总配置</div>
            </div>
          </div>

          <!-- Legend -->
          <div class="alloc-legend">
            <div
              v-for="asset in assetAllocation"
              :key="asset.id"
              class="legend-item"
              :class="{ active: expandedAsset === asset.id }"
              @click="toggleAsset(asset.id)"
            >
              <div class="legend-left">
                <span class="legend-dot" :style="{ background: asset.color }"></span>
                <div>
                  <div class="legend-name">{{ asset.name }}</div>
                  <div class="legend-desc">{{ asset.desc }}</div>
                </div>
              </div>
              <div class="legend-right">
                <span class="legend-pct">{{ asset.pct }}%</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="legend-chevron" :style="{ transform: expandedAsset === asset.id ? 'rotate(180deg)' : 'rotate(0deg)' }">
                  <path d="m6 9 6 6 6-6"/>
                </svg>
              </div>
            </div>
          </div>

          <!-- Building Guide Button -->
          <button class="building-guide-btn" @click="goBuildingGuide">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3v18"/>
              <path d="M8 21h8"/>
              <path d="M7 3h10"/>
              <path d="M7 7h10"/>
              <path d="M7 11h10"/>
              <path d="M7 15h10"/>
            </svg>
            <span>查看建仓引导</span>
          </button>
        </div>

        <!-- Expanded Asset Detail -->
        <Transition name="asset-expand">
          <div v-if="expandedAsset" class="asset-detail">
            <div
              v-for="asset in assetAllocation.filter(a => a.id === expandedAsset)"
              :key="asset.id"
              class="detail-card"
            >
              <div class="detail-header">
                <span class="detail-dot" :style="{ background: asset.color }"></span>
                <span class="detail-title">{{ asset.name }} · 策略绑定</span>
              </div>

              <!-- System Recommended Holdings -->
              <div class="holdings-list">
                <div class="holdings-header">
                  <span class="holdings-label">系统推荐持仓</span>
                  <span class="holdings-sub">基于Hybrid引擎动态选股</span>
                </div>
                <div
                  v-for="holding in asset.holdings"
                  :key="holding.code"
                  class="holding-item"
                >
                  <div class="holding-main">
                    <div class="holding-info">
                      <span class="holding-name">{{ holding.name }}</span>
                      <span class="holding-code">{{ holding.code }}</span>
                    </div>
                    <div class="holding-weight">
                      <div class="weight-bar-wrap">
                        <div class="weight-bar" :style="{ width: holding.weight + '%', background: asset.color }"></div>
                      </div>
                      <span class="weight-pct">{{ holding.weight }}%</span>
                    </div>
                  </div>
                  <p class="holding-reason">{{ holding.reason }}</p>
                </div>
              </div>

              <!-- Buy Guide Button -->
              <button class="buy-guide-btn" @click="openBuyGuide(asset.name)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4"/>
                  <path d="M12 8h.01"/>
                </svg>
                <span>购买指引</span>
              </button>
            </div>
          </div>
        </Transition>

        <!-- Risk Config -->
        <div class="risk-card" v-if="riskConfig">
          <div class="risk-header">
            <span class="risk-label">风控配置</span>
          </div>
          <div class="risk-grid">
            <div class="risk-item">
              <span class="risk-name">止损线</span>
              <span class="risk-val">{{ Math.round((riskConfig.stop_loss || 0) * 100) }}%</span>
            </div>
            <div class="risk-item">
              <span class="risk-name">最大回撤</span>
              <span class="risk-val">{{ Math.round((riskConfig.max_drawdown || 0) * 100) }}%</span>
            </div>
            <div class="risk-item">
              <span class="risk-name">单标的上限</span>
              <span class="risk-val">{{ Math.round((riskConfig.max_position || 0) * 100) }}%</span>
            </div>
            <div class="risk-item">
              <span class="risk-name">再平衡阈值</span>
              <span class="risk-val">{{ Math.round((riskConfig.rebalance_threshold || 0) * 100) }}%</span>
            </div>
          </div>
        </div>

        <!-- Summary Footer -->
        <div class="summary-footer">
          <div class="summary-item">
            <span class="summary-label">股票占比</span>
            <span class="summary-val">{{ saaWeights.stock ? Math.round(saaWeights.stock * 100) : 45 }}%</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">最大回撤</span>
            <span class="summary-val">&lt;{{ Math.round((riskConfig.max_drawdown || 0.15) * 100) }}%</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">再平衡</span>
            <span class="summary-val">{{ riskConfig.rebalance_threshold ? (riskConfig.rebalance_threshold * 100 >= 5 ? '季度' : '月度') : '季度' }}</span>
          </div>
        </div>

        <!-- Next Page Button -->
        <button
          class="next-page-btn"
          :class="{ disabled: !isAdopted }"
          :disabled="!isAdopted"
          @click="goNext"
        >
          <span>{{ isAdopted ? '下一页：匹配投资策略' : '置信度未达标，请重新定制' }}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14"/>
            <path d="m12 5 7 7-7 7"/>
          </svg>
        </button>

        <!-- Rebuild Button -->
        <button class="rebuild-btn" @click="regenerateWithSSE">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
            <path d="M8 16H3v5"/>
          </svg>
          <span>重新定制组合</span>
        </button>
      </template>
    </div>

    <!-- Buy Guide Modal -->
    <Transition name="modal">
      <div v-if="showBuyGuide" class="modal-overlay" @click.self="closeBuyGuide">
        <div class="modal-content">
          <div class="modal-header">
            <h3 class="modal-title">{{ activeAssetName }}购买指引</h3>
            <button class="modal-close" @click="closeBuyGuide">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>

          <div class="modal-body">
            <div v-if="activeGuide" class="buy-guide-content">
              <!-- 示例标的 -->
              <div class="guide-section">
                <div class="guide-section-title">常见标的示例</div>
                <div class="guide-examples">
                  <div
                    v-for="ex in activeGuide.examples"
                    :key="ex.code"
                    class="guide-example-card"
                  >
                    <div class="guide-example-name">{{ ex.name }}</div>
                    <div class="guide-example-code">{{ ex.code }}</div>
                    <div class="guide-example-desc">{{ ex.desc }}</div>
                  </div>
                </div>
              </div>

              <!-- 购买渠道 -->
              <div class="guide-section">
                <div class="guide-section-title">购买渠道</div>
                <ul class="guide-list">
                  <li v-for="ch in activeGuide.channels" :key="ch">{{ ch }}</li>
                </ul>
              </div>

              <!-- 操作步骤 -->
              <div class="guide-section">
                <div class="guide-section-title">操作步骤</div>
                <ol class="guide-list numbered">
                  <li v-for="(step, idx) in activeGuide.steps" :key="idx">{{ step }}</li>
                </ol>
              </div>

              <!-- 注意事项 -->
              <div class="guide-section">
                <div class="guide-section-title">注意事项</div>
                <div class="guide-tips">
                  <div
                    v-for="(tip, idx) in activeGuide.tips"
                    :key="idx"
                    class="guide-tip"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                      <path d="M12 16v-4"/>
                      <path d="M12 8h.01"/>
                    </svg>
                    <span>{{ tip }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="guide-placeholder">
              <div class="guide-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <p class="guide-text">暂无该资产的购买指引</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.portfolio-page {
  min-height: 100vh;
  background: #fafafa;
  position: relative;
  padding-bottom: 32px;
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
  max-width: 720px; margin: 0 auto; padding: 12px 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.back-btn {
  width: 36px; height: 36px;
  border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.7);
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.back-btn:hover { background: #fff; border-color: rgba(0,0,0,0.1); color: #171717; }
.demo-reset-btn {
  width: 36px; height: 36px;
  border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.5);
  display: flex; align-items: center; justify-content: center;
  color: #a3a3a3; cursor: pointer; transition: all 0.2s;
  opacity: 0.25;
}
.demo-reset-btn:hover {
  opacity: 1;
  background: #fff; border-color: rgba(0,0,0,0.1); color: #6366f1;
}
.header-title { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }

/* Content */
.portfolio-content {
  max-width: 720px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 16px;
  position: relative; z-index: 1;
}
.loading-state, .error-state {
  text-align: center; padding: 60px 20px; color: #a3a3a3;
}
.error-state p { margin-bottom: 20px; }

/* Reliability Banner */
.reliability-banner {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.reliability-item {
  text-align: center; padding: 16px 12px;
  background: #fff; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.05);
}
.reliability-item.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}
.reliability-item.clickable:hover {
  background: #f5f3ff;
  border-color: #c4b5fd;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99,102,241,0.12);
}
.reliability-item.clickable:hover .reliability-label {
  color: #6366f1;
}
.reliability-item.clickable:hover .reliability-val {
  color: #4f46e5;
}
.reliability-label { font-size: 0.68rem; color: #a3a3a3; display: block; margin-bottom: 6px; }
.reliability-val { font-size: 1.1rem; font-weight: 700; color: #171717; }
.level-高 { color: #22c55e; }
.level-中 { color: #d97706; }
.level-低 { color: #ef4444; }

/* Adoption Alert */
.adoption-alert {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px; background: #fff7ed; border-radius: 16px;
  border: 1px solid rgba(217, 119, 6, 0.15);
  color: #b45309;
}
.adoption-alert svg { flex-shrink: 0; margin-top: 2px; }
.adoption-alert-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 4px; }
.adoption-alert-desc { font-size: 0.78rem; line-height: 1.5; opacity: 0.9; }

.adoption-success {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; background: #f0fdf4; border-radius: 16px;
  border: 1px solid rgba(34, 197, 94, 0.15);
  color: #15803d; font-size: 0.85rem; font-weight: 600;
}

/* Benchmark Card */
.benchmark-card {
  background: #fff; border-radius: 20px; padding: 24px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
}
.benchmark-header {
  text-align: center; margin-bottom: 20px;
}
.benchmark-label {
  font-size: 0.62rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.1em; text-transform: uppercase;
  display: block; margin-bottom: 4px;
}
.benchmark-sub { font-size: 0.78rem; color: #a3a3a3; }

.benchmark-list { display: flex; flex-direction: column; gap: 10px; }
.benchmark-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; background: #fafafa; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.04);
}
.benchmark-info { flex: 1; }
.benchmark-name { font-size: 0.88rem; font-weight: 700; color: #171717; }
.benchmark-desc { font-size: 0.7rem; color: #a3a3a3; margin-top: 2px; }
.benchmark-returns {
  display: flex; gap: 16px; margin-right: 16px;
}
.benchmark-return { text-align: center; }
.return-label { display: block; font-size: 0.65rem; color: #a3a3a3; margin-bottom: 2px; }
.return-val { font-size: 0.9rem; font-weight: 700; }
.return-val.positive { color: #22c55e; }
.return-val.negative { color: #ef4444; }
.benchmark-passed {
  padding: 5px 10px; border-radius: 8px; font-size: 0.72rem; font-weight: 700;
}
.benchmark-passed.passed { background: #dcfce7; color: #166534; }
.benchmark-passed.failed { background: #fee2e2; color: #991b1b; }

.benchmark-overall {
  display: flex; align-items: center; gap: 12px;
  margin-top: 18px; padding-top: 18px;
  border-top: 1px solid rgba(0,0,0,0.05);
}
.benchmark-overall-label { font-size: 0.82rem; font-weight: 700; color: #171717; }
.benchmark-progress {
  flex: 1; height: 8px; background: #e5e5e5; border-radius: 999px; overflow: hidden;
}
.benchmark-progress-bar {
  height: 100%; background: #171717; border-radius: 999px;
  transition: width 0.5s ease;
}
.benchmark-overall-score { font-size: 1rem; font-weight: 800; color: #171717; min-width: 44px; text-align: right; }

.next-page-btn.disabled {
  background: #a3a3a3; cursor: not-allowed;
  box-shadow: none;
}
.next-page-btn.disabled:hover {
  background: #a3a3a3; transform: none;
  box-shadow: none;
}

/* Allocation Card */
.alloc-card {
  background: #fff; border-radius: 20px; padding: 24px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
}
.alloc-header {
  text-align: center; margin-bottom: 20px;
}
.alloc-label {
  font-size: 0.62rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.1em; text-transform: uppercase;
  display: block; margin-bottom: 4px;
}
.alloc-sub {
  font-size: 0.78rem; color: #a3a3a3;
}

/* Donut */
.donut-wrap {
  width: 180px; height: 180px; margin: 0 auto 24px;
  position: relative;
}
.donut-svg { width: 100%; height: 100%; }
.donut-center {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%); text-align: center;
}
.donut-total { font-size: 1.8rem; font-weight: 800; color: #171717; line-height: 1; }
.donut-total-label { font-size: 0.65rem; color: #a3a3a3; letter-spacing: 0.06em; }

/* Legend */
.alloc-legend {
  display: flex; flex-direction: column; gap: 8px;
}
.legend-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; background: #fafafa; border-radius: 12px;
  border: 2px solid transparent; cursor: pointer;
  transition: all 0.2s ease;
}
.legend-item:hover {
  background: #f5f5f5; border-color: rgba(0,0,0,0.06);
}
.legend-item.active {
  background: #fff; border-color: #171717;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.legend-left {
  display: flex; align-items: center; gap: 12px;
}
.legend-dot {
  width: 10px; height: 10px; border-radius: 50%;
  flex-shrink: 0;
}
.legend-name {
  font-size: 0.9rem; font-weight: 600; color: #171717;
}
.legend-desc {
  font-size: 0.72rem; color: #a3a3a3; margin-top: 1px;
}
.legend-right {
  display: flex; align-items: center; gap: 10px;
}
.legend-pct {
  font-size: 1.1rem; font-weight: 700; color: #171717;
}
.legend-chevron {
  color: #a3a3a3; transition: transform 0.3s ease;
}

/* Asset Detail */
.asset-detail {
  display: flex; flex-direction: column; gap: 12px;
}
.detail-card {
  background: #fff; border-radius: 20px; padding: 20px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.detail-header {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px;
}
.detail-dot {
  width: 10px; height: 10px; border-radius: 50%;
}
.detail-title {
  font-size: 0.95rem; font-weight: 700; color: #171717;
}

/* Holdings List */
.holdings-list {
  display: flex; flex-direction: column; gap: 12px;
  margin-bottom: 16px;
}
.holdings-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 4px;
}
.holdings-label {
  font-size: 0.82rem; font-weight: 600; color: #171717;
}
.holdings-sub {
  font-size: 0.72rem; color: #a3a3a3;
}
.holding-item {
  padding: 14px 16px; background: #fafafa; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.04);
  transition: all 0.2s ease;
}
.holding-item:hover {
  background: #f5f5f5; border-color: rgba(0,0,0,0.08);
}
.holding-main {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.holding-info {
  display: flex; align-items: center; gap: 10px;
}
.holding-name {
  font-size: 0.9rem; font-weight: 600; color: #171717;
}
.holding-code {
  font-size: 0.72rem; color: #a3a3a3;
  font-family: ui-monospace, SFMono-Regular, monospace;
  background: #f0f0f0; padding: 2px 6px; border-radius: 4px;
}
.holding-weight {
  display: flex; align-items: center; gap: 10px;
  min-width: 120px;
}
.weight-bar-wrap {
  flex: 1; height: 6px; background: #e5e5e5; border-radius: 999px; overflow: hidden;
}
.weight-bar {
  height: 100%; border-radius: 999px; transition: width 0.5s ease;
}
.weight-pct {
  font-size: 0.85rem; font-weight: 700; color: #171717;
  min-width: 36px; text-align: right;
}
.holding-reason {
  font-size: 0.78rem; color: #737373; line-height: 1.5;
  margin: 0;
}

/* Risk Card */
.risk-card {
  background: #fff; border-radius: 20px; padding: 20px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.risk-header {
  margin-bottom: 14px;
}
.risk-label {
  font-size: 0.62rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.1em; text-transform: uppercase;
}
.risk-grid {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.risk-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; background: #fafafa; border-radius: 10px;
}
.risk-name { font-size: 0.78rem; color: #737373; }
.risk-val { font-size: 0.9rem; font-weight: 700; color: #171717; }

/* Guide Placeholder */
.guide-placeholder {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 40px 20px; text-align: center;
}
.guide-icon {
  width: 64px; height: 64px; border-radius: 16px;
  background: #fafafa; color: #a3a3a3;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.guide-text {
  font-size: 1rem; font-weight: 600; color: #171717;
  margin: 0 0 6px;
}
.guide-sub {
  font-size: 0.82rem; color: #a3a3a3; margin: 0;
}

/* Buy Guide Button */
.buy-guide-btn {
  width: 100%; padding: 14px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  background: #fafafa; border: 1.5px dashed #d4d4d4;
  border-radius: 12px; color: #737373;
  font-size: 0.85rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
  font-family: inherit;
}
.buy-guide-btn:hover {
  background: #f5f5f5; border-color: #171717; color: #171717;
}

/* Buy Guide Content */
.buy-guide-content {
  display: flex; flex-direction: column;
  gap: 20px;
}
.guide-section {}
.guide-section-title {
  font-size: 0.8rem; font-weight: 700;
  color: #171717; margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.guide-examples {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 10px;
}
.guide-example-card {
  background: #fafafa;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}
.guide-example-name {
  font-size: 0.85rem; font-weight: 700;
  color: #171717; margin-bottom: 2px;
}
.guide-example-code {
  font-size: 0.75rem; font-weight: 600;
  color: #6366f1; margin-bottom: 4px;
}
.guide-example-desc {
  font-size: 0.7rem; color: #737373;
  line-height: 1.4;
}
.guide-list {
  margin: 0; padding-left: 18px;
  font-size: 0.82rem; color: #525252;
  line-height: 1.7;
}
.guide-list.numbered {
  list-style-type: decimal;
}
.guide-list li {
  margin-bottom: 4px;
}
.guide-tips {
  display: flex; flex-direction: column;
  gap: 8px;
}
.guide-tip {
  display: flex; align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: #fffbeb;
  border: 1px solid rgba(217,119,6,0.12);
  border-radius: 10px;
  color: #92400e;
  font-size: 0.78rem;
  line-height: 1.5;
}
.guide-tip svg {
  flex-shrink: 0; margin-top: 1px;
}

/* Summary Footer */
.summary-footer {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 10px; margin-top: 8px;
}
.summary-item {
  text-align: center; padding: 16px 12px;
  background: #fff; border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.05);
}
.summary-item .summary-label {
  font-size: 0.68rem; color: #a3a3a3;
  display: block; margin-bottom: 6px;
}
.summary-item .summary-val {
  font-size: 1.1rem; font-weight: 700; color: #171717;
}

/* Next Page Button */
.next-page-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 17px 24px; border: none; border-radius: 16px;
  background: #171717; color: #fff; font-family: inherit;
  font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
  cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 8px;
}
.next-page-btn:hover {
  background: #262626; transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.18);
}

/* Building Guide Button */
.building-guide-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 16px 24px; border: none; border-radius: 16px;
  background: #4f46e5; color: #fff; font-family: inherit;
  font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
  cursor: pointer; box-shadow: 0 4px 16px rgba(79,70,229,0.2);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 12px;
}
.building-guide-btn:hover {
  background: #4338ca; transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(79,70,229,0.3);
}

/* Rebuild Button */
.rebuild-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 14px 24px; border: 1.5px dashed #d4d4d4;
  border-radius: 16px; background: transparent; color: #737373;
  font-family: inherit; font-size: 0.85rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
  margin-top: 10px;
}
.rebuild-btn:hover {
  border-color: #171717; color: #171717; background: #fafafa;
}

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(8px);
  display: flex; align-items: flex-end; justify-content: center;
  padding: 0;
}
.modal-content {
  background: #fff; border-radius: 24px 24px 0 0;
  width: 100%; max-width: 720px; max-height: 85vh;
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
.modal-title {
  font-size: 1.1rem; font-weight: 700; color: #171717;
  margin: 0; letter-spacing: -0.02em;
}
.modal-close {
  width: 36px; height: 36px; border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.06); background: #fafafa;
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.modal-close:hover { background: #171717; border-color: #171717; color: #fff; }

.modal-body {
  padding: 24px;
}

/* Transitions */
.asset-expand-enter-active,
.asset-expand-leave-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  max-height: 800px; opacity: 1;
}
.asset-expand-enter-from,
.asset-expand-leave-to {
  max-height: 0; opacity: 0; overflow: hidden;
}

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

/* ========== Building State ========== */
.building-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  gap: 20px;
}

.building-animation {
  position: relative;
  width: 80px;
  height: 80px;
}

.building-spinner {
  width: 80px;
  height: 80px;
  border: 3px solid #e5e5e5;
  border-top-color: #171717;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.building-pulse {
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 2px solid rgba(23, 23, 23, 0.1);
  animation: pulse-ring 2s ease-out infinite;
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

.building-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #171717;
  margin: 0;
  text-align: center;
}

.building-subtitle {
  font-size: 0.85rem;
  color: #a3a3a3;
  margin: 0;
}

.building-steps {
  width: 100%;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  background: #fafafa;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.step-item.active {
  background: #fff;
  border-color: rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.step-item.done {
  background: #f0fdf4;
  border-color: rgba(34, 197, 94, 0.15);
}

.step-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e5e5e5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.step-item.active .step-dot {
  background: #171717;
  animation: pulse-dot 2s ease-in-out infinite;
}

.step-item.done .step-dot {
  background: #22c55e;
  color: #fff;
}

.step-label {
  font-size: 0.85rem;
  color: #737373;
  transition: color 0.3s ease;
}

.step-item.active .step-label {
  color: #171717;
  font-weight: 600;
}

.step-item.done .step-label {
  color: #166534;
}

/* Guide Card */
.guide-card {
  width: 100%;
  max-width: 320px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: #fff;
  border-radius: 16px;
  border: 1.5px dashed #d4d4d4;
  cursor: pointer;
  transition: all 0.25s ease;
  margin-top: 8px;
}

.guide-card:hover {
  border-color: #171717;
  background: #fafafa;
  transform: translateY(-1px);
}

.guide-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #fafafa;
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #737373;
  flex-shrink: 0;
  transition: all 0.25s ease;
}

.guide-card:hover .guide-icon {
  background: #171717;
  color: #fff;
  border-color: #171717;
}

.guide-content {
  flex: 1;
}

.guide-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #171717;
  margin: 0 0 2px;
}

.guide-desc {
  font-size: 0.78rem;
  color: #a3a3a3;
  margin: 0;
}

.guide-card > svg:last-child {
  color: #d4d4d4;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.guide-card:hover > svg:last-child {
  color: #171717;
  transform: translateX(2px);
}

@media (min-width: 640px) {
  .modal-overlay { align-items: center; padding: 24px; }
  .modal-content { border-radius: 24px; max-height: 85vh; }
}

@media (min-width: 768px) {
  .portfolio-content { padding: 24px 32px 40px; }
}
</style>

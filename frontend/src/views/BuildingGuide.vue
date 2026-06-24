<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const currentStep = ref(0)
const completedSteps = ref(new Set<number>())
const loading = ref(true)

// ── 当前组合持仓 ──
interface PortfolioHolding {
  name: string
  code: string
  weight: number
  asset_class: string
  reason?: string
}

const portfolioHoldings = ref<PortfolioHolding[]>([])
const portfolioWeights = ref({ stock: 0, bond: 0, commodity: 0, cash: 0 })
const hasPortfolio = ref(false)
const portfolioCollapsed = ref(true)

function loadPortfolio() {
  try {
    const stored = sessionStorage.getItem('latest_portfolio')
    if (!stored) return
    const data = JSON.parse(stored)
    const weights = data?.portfolio?.saa?.weights || {}
    portfolioWeights.value = {
      stock: weights.stock || 0,
      bond: weights.bond || 0,
      commodity: weights.commodity || 0,
      cash: weights.cash || 0,
    }
    const bindings = data?.portfolio?.bindings || []
    portfolioHoldings.value = bindings.map((b: any) => ({
      name: b.name || '未命名',
      code: b.code || b.strategy_id || '',
      weight: Math.round((b.weight || 0) * 100),
      asset_class: b.asset_class?.toLowerCase() || 'stock',
      reason: b.reason || '',
    }))
    hasPortfolio.value = portfolioHoldings.value.length > 0
  } catch (e) {
    console.error('Failed to load portfolio:', e)
  }
}

function goBackToPortfolio() {
  router.push('/portfolio')
}

interface GuideStep {
  title: string
  subtitle: string
  description: string
  checklist: { text: string; checked: boolean }[]
  tip: string
  tipType: 'info' | 'warning' | 'success'
}

const STEPS: GuideStep[] = [
  {
    title: '开户前准备',
    subtitle: 'STEP 1',
    description: '正式开户前，先准备好材料和基础知识，避免开户过程中反复中断。',
    checklist: [
      { text: '准备本人二代身份证原件', checked: false },
      { text: '准备本人名下的一类银行卡（推荐大行借记卡）', checked: false },
      { text: '确保手机号为本人实名且在正常使用', checked: false },
      { text: '下载 2-3 家券商 APP 做初步对比', checked: false },
      { text: '完成券商内的风险测评问卷', checked: false },
    ],
    tip: '风险测评结果会决定你能交易的产品范围。如果被评为保守型，可能无法购买股票型 ETF，需要重新评估自己的风险承受能力。',
    tipType: 'info',
  },
  {
    title: '选择券商开户',
    subtitle: 'STEP 2',
    description: '券商是买卖场内基金和股票的唯一通道，佣金、APP体验和ETF覆盖是三大核心考量。',
    checklist: [
      { text: '股票/ETF 佣金率 ≤ 0.025%（万2.5）', checked: false },
      { text: '无最低 5 元佣金限制（或可申请免除）', checked: false },
      { text: 'APP 支持 ETF 条件单、网格交易、智能盯盘', checked: false },
      { text: '支持场外基金申购且费率 1 折', checked: false },
      { text: '线上完成开户：上传身份证 → 视频认证 → 绑定银行卡 → 设置密码', checked: false },
      { text: '等待 1 个交易日审核通过并收到资金账号', checked: false },
    ],
    tip: '新手建议优先选择 TOP10 大券商（如华泰、国泰、中信、广发等），系统稳定性更好，ETF品种也更全。',
    tipType: 'warning',
  },
  {
    title: '银证转账入金',
    subtitle: 'STEP 3',
    description: '资金从银行卡转入证券账户后，才能下单购买股票、ETF、基金等产品。',
    checklist: [
      { text: '在券商 APP 中找到「银证转账」入口', checked: false },
      { text: '绑定银行卡并设置银行密码、资金密码', checked: false },
      { text: '交易日 9:00-16:00 转入第一批资金', checked: false },
      { text: '确认资金已到达证券账户「可用资金」', checked: false },
      { text: '了解当日转出限额（通常 5 万-500 万不等）', checked: false },
    ],
    tip: '银证转账只在交易日 9:00-16:00 开放。建议一次性把计划投入资金的 80% 转入证券账户，避免多次转账。',
    tipType: 'warning',
  },
  {
    title: '购买股票类资产',
    subtitle: 'STEP 4',
    description: '股票类资产是组合的进攻部分，主要通过股票型 ETF 来实现，既分散个股风险，又保留股市收益弹性。',
    checklist: [
      { text: '在交易界面输入 ETF 代码（如 510300 沪深300ETF）', checked: false },
      { text: '确认当前价格、涨跌幅和盘口流动性', checked: false },
      { text: '选择「买入」，输入数量和价格（或市价单）', checked: false },
      { text: '交易时间下单：9:30-11:30、13:00-15:00', checked: false },
      { text: '最小买入单位为 100 份（1手），按 100 的整数倍递增', checked: false },
      { text: '成交后在「持仓」中核对数量和成本', checked: false },
    ],
    tip: 'ETF 价格会实时波动，建议用「限价单」分批买入，避免在盘中突然拉升时追高。',
    tipType: 'info',
  },
  {
    title: '购买债券类资产',
    subtitle: 'STEP 5',
    description: '债券类资产是组合的压舱石，波动小、收益稳。可通过债券 ETF、国债逆回购或债券基金配置。',
    checklist: [
      { text: '搜索国债 ETF（如 019547、511010）或信用债 ETF', checked: false },
      { text: '与股票 ETF 一样，按手买入（100 份/手）', checked: false },
      { text: '了解国债逆回购：收盘后闲置资金可 1 天期出借（代码 204001）', checked: false },
      { text: '场外债券基金申购路径：理财/基金 → 搜索基金代码 → 申购', checked: false },
      { text: '确认债券类资产占组合目标比例', checked: false },
    ],
    tip: '利率下行周期，长久期债券价格上涨；利率上行周期，短久期债券更抗跌。根据宏观信号调整久期。',
    tipType: 'info',
  },
  {
    title: '购买商品类资产',
    subtitle: 'STEP 6',
    description: '商品类资产（主要是黄金）能在通胀升温或地缘冲突时起到对冲作用。',
    checklist: [
      { text: '搜索黄金 ETF（如 518880 黄金 ETF）', checked: false },
      { text: '按 100 份整数倍买入，交易规则与股票 ETF 相同', checked: false },
      { text: '或选择场外黄金 ETF 联接基金（代码如 000216）', checked: false },
      { text: '关注国际金价、美元指数和地缘风险事件', checked: false },
      { text: '商品配置一般不超过组合的 15%', checked: false },
    ],
    tip: '黄金适合作为"保险"配置，不宜重仓。一般在通胀预期升温、地缘风险加剧时适当增加比例。',
    tipType: 'warning',
  },
  {
    title: '现金管理',
    subtitle: 'STEP 7',
    description: '现金不是闲着，而是要产生稳定收益。货币基金、国债逆回购和券商余额理财是三种常见工具，下面分别说明在哪里买。',
    checklist: [
      { text: '场内货币基金（如 511880 银华日利）：在券商/股票 APP 像买股票一样直接买入，100 份起，T+0 交易、T+1 可取。', checked: false },
      { text: '场外货币基金（如 003474）：在银行 APP、支付宝、微信理财通、天天基金等平台搜索基金代码申购，T+1 确认。', checked: false },
      { text: '国债逆回购：只能在券商 APP 操作，进入「国债理财/逆回购」专区，选 1 天期 204001（沪市）或 131810（深市）。', checked: false },
      { text: '券商余额理财：在券商 APP 开通「余额自动理财」，收盘后自动归集证券账户里的闲置资金。', checked: false },
      { text: '保留一定机动现金在银行卡或证券账户余额，用于逢低加仓。', checked: false },
    ],
    tip: '现金管理的核心是「随取随用」。场内货基用券商 APP 最方便；场外货基用银行/支付宝/理财通/天天基金都能买；逆回购和余额理财只能在券商 APP 操作。',
    tipType: 'success',
  },
  {
    title: '第一批建仓（40%）',
    subtitle: 'STEP 8',
    description: '不要一次性满仓，先买入计划资金的 40%，试探市场水温并降低择时风险。',
    checklist: [
      { text: '按组合权重计算每只标的应买入金额', checked: false },
      { text: '优先买入流动性好的宽基 ETF（日均成交额 > 1 亿）', checked: false },
      { text: '在交易时间内用限价单分批下单', checked: false },
      { text: '记录每只标的买入价格和数量', checked: false },
      { text: '核对持仓市值与目标权重的偏差', checked: false },
    ],
    tip: '第一批以股票类 ETF 为主。如果建仓时市场处于高位，可以把第一批比例降到 30%，留更多资金给后续分批。',
    tipType: 'info',
  },
  {
    title: '第二批建仓（35%）',
    subtitle: 'STEP 9',
    description: '2 周后，根据市场走势补齐债券类和商品类资产，并逢低加仓股票类。',
    checklist: [
      { text: '再次银证转账，转入第二批资金', checked: false },
      { text: '若股票类标的下跌 5% 以上，可逢低补仓', checked: false },
      { text: '买入债券 ETF 或债券基金至目标比例', checked: false },
      { text: '买入黄金/商品 ETF 至目标比例', checked: false },
      { text: '更新持仓记录表', checked: false },
    ],
    tip: '第二批是平衡股债比例的关键。如果第一批建仓后市场上涨，第二批就多买债券；如果下跌，就多买股票。',
    tipType: 'success',
  },
  {
    title: '第三批建仓（25%）',
    subtitle: 'STEP 10',
    description: '1 个月后，补齐剩余仓位，让实际持仓尽量贴近组合目标权重。',
    checklist: [
      { text: '转入第三批资金', checked: false },
      { text: '检查当前各资产权重与目标权重的偏差', checked: false },
      { text: '买入偏差的资产，卖出（或减少买入）超配的资产', checked: false },
      { text: '核对持仓与组合方案一致', checked: false },
      { text: '截图保存持仓页面作为记录', checked: false },
    ],
    tip: '第三批完成后，组合的初始建仓就结束了。后续进入「持有+再平衡」阶段，不需要频繁交易。',
    tipType: 'success',
  },
  {
    title: '设置预警与再平衡',
    subtitle: 'STEP 11',
    description: '建仓完成只是开始，持续监控和定期再平衡才能让组合长期保持健康。',
    checklist: [
      { text: '为各标的设置价格涨跌预警（如 ±10%）', checked: false },
      { text: '开启 APP 推送通知', checked: false },
      { text: '设置策略寿命预警，关注生态系统中的濒危策略', checked: false },
      { text: '每季度检查一次权重偏差，偏差 > 5% 时做再平衡', checked: false },
      { text: '每天开盘前查看今日操作建议', checked: false },
    ],
    tip: '再平衡的本质是「低买高卖」：卖出涨得多的资产，买入跌得多的资产，让组合回到目标比例。',
    tipType: 'info',
  },
]

onMounted(() => {
  loadPortfolio()
  // 加载进度
  const saved = localStorage.getItem('building_guide_progress')
  if (saved) {
    const data = JSON.parse(saved)
    currentStep.value = data.currentStep || 0
    completedSteps.value = new Set(data.completedSteps || [])
    // 恢复 checklist 状态
    data.checklist?.forEach((stepChecks: boolean[], stepIdx: number) => {
      stepChecks.forEach((checked, itemIdx) => {
        if (STEPS[stepIdx]?.checklist[itemIdx]) {
          STEPS[stepIdx].checklist[itemIdx].checked = checked
        }
      })
    })
  }
  loading.value = false
})

function saveProgress() {
  localStorage.setItem('building_guide_progress', JSON.stringify({
    currentStep: currentStep.value,
    completedSteps: Array.from(completedSteps.value),
    checklist: STEPS.map(s => s.checklist.map(c => c.checked)),
  }))
}

function toggleCheck(stepIdx: number, itemIdx: number) {
  STEPS[stepIdx].checklist[itemIdx].checked = !STEPS[stepIdx].checklist[itemIdx].checked
  // 检查是否所有项都完成
  const allChecked = STEPS[stepIdx].checklist.every(c => c.checked)
  if (allChecked) {
    completedSteps.value.add(stepIdx)
  } else {
    completedSteps.value.delete(stepIdx)
  }
  saveProgress()
}

function nextStep() {
  if (currentStep.value < STEPS.length - 1) {
    currentStep.value++
    saveProgress()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
    saveProgress()
  }
}

function goToStep(idx: number) {
  currentStep.value = idx
  saveProgress()
}

function finish() {
  completedSteps.value.add(STEPS.length - 1)
  saveProgress()
  router.push('/')
}

const tipIcon = (type: string) => {
  const icons: Record<string, string> = {
    info: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm0-15v6m0 4h.01',
    warning: 'M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4m0 4h.01',
    success: 'M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3',
  }
  return icons[type] || icons.info
}

const tipColor = (type: string) => {
  const colors: Record<string, { bg: string; border: string; text: string }> = {
    info: { bg: '#eff6ff', border: 'rgba(59,130,246,0.15)', text: '#1e40af' },
    warning: { bg: '#fffbeb', border: 'rgba(217,119,6,0.15)', text: '#92400e' },
    success: { bg: '#f0fdf4', border: 'rgba(34,197,94,0.15)', text: '#166534' },
  }
  return colors[type] || colors.info
}
</script>

<template>
  <div class="guide-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="$router.back()">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <div class="header-title">
          <span class="header-label">BUILDING GUIDE</span>
          <span class="header-name">建仓引导</span>
        </div>
        <button class="portfolio-link" @click="goBackToPortfolio">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          <span>回组合</span>
        </button>
      </div>
      <div class="header-sub">
        <div class="step-counter">步骤 {{ currentStep + 1 }}/{{ STEPS.length }}</div>
      </div>
      <div class="progress-wrap">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }"></div>
        </div>
      </div>
    </header>

    <!-- Step Navigator (Desktop) -->
    <nav class="step-nav">
      <button
        v-for="(step, idx) in STEPS"
        :key="idx"
        class="step-nav-item"
        :class="{
          active: idx === currentStep,
          completed: completedSteps.has(idx),
        }"
        @click="goToStep(idx)"
      >
        <span class="step-nav-num">{{ String(idx + 1).padStart(2, '0') }}</span>
        <span class="step-nav-title">{{ step.title }}</span>
        <svg v-if="completedSteps.has(idx)" class="step-nav-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </button>
    </nav>

    <!-- Content -->
    <div class="guide-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>


      <div v-if="!loading" class="step-card">
        <div class="step-badge">{{ STEPS[currentStep]?.subtitle }}</div>
        <h2 class="step-title">{{ STEPS[currentStep]?.title }}</h2>
        <p class="step-desc">{{ STEPS[currentStep]?.description }}</p>

        <!-- Checklist -->
        <div class="checklist">
          <label
            v-for="(item, idx) in STEPS[currentStep]?.checklist"
            :key="idx"
            class="check-item"
            :class="{ checked: item.checked }"
          >
            <span class="check-box" @click.stop="toggleCheck(currentStep, idx)">
              <svg v-if="item.checked" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span class="check-text">{{ item.text }}</span>
          </label>
        </div>

        <!-- Tip -->
        <div class="tip-box" :style="{ background: tipColor(STEPS[currentStep]?.tipType).bg, borderColor: tipColor(STEPS[currentStep]?.tipType).border }">
          <svg class="tip-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :style="{ color: tipColor(STEPS[currentStep]?.tipType).text }">
            <path :d="tipIcon(STEPS[currentStep]?.tipType)"/>
          </svg>
          <span class="tip-text" :style="{ color: tipColor(STEPS[currentStep]?.tipType).text }">{{ STEPS[currentStep]?.tip }}</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="guide-footer">
      <button v-if="currentStep > 0" class="btn-secondary" @click="prevStep">上一步</button>
      <div v-else></div>

      <button class="btn-primary" @click="currentStep < STEPS.length - 1 ? nextStep() : finish()">
        <span>{{ currentStep < STEPS.length - 1 ? '下一步' : '完成建仓引导' }}</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12h14"/>
          <path d="m12 5 7 7-7 7"/>
        </svg>
      </button>
    </div>

    <!-- Floating Portfolio Summary -->
    <div v-if="hasPortfolio" class="portfolio-float" :class="{ collapsed: portfolioCollapsed }">
      <button v-if="portfolioCollapsed" class="portfolio-float-collapsed" @click="portfolioCollapsed = false">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>组合配置</span>
      </button>

      <div v-else class="portfolio-summary-card portfolio-float-card">
        <div class="portfolio-summary-header">
          <div class="portfolio-summary-title">当前组合配置</div>
          <div class="portfolio-summary-actions">
            <button class="portfolio-summary-link" @click="goBackToPortfolio">
              返回组合页
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
            </button>
            <button class="portfolio-summary-close" @click="portfolioCollapsed = true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m18 15-6-6-6 6"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="portfolio-weights">
          <div class="weight-chip stock">
            <span class="weight-chip-label">股票</span>
            <span class="weight-chip-value">{{ Math.round(portfolioWeights.stock * 100) }}%</span>
          </div>
          <div class="weight-chip bond">
            <span class="weight-chip-label">债券</span>
            <span class="weight-chip-value">{{ Math.round(portfolioWeights.bond * 100) }}%</span>
          </div>
          <div class="weight-chip commodity">
            <span class="weight-chip-label">商品</span>
            <span class="weight-chip-value">{{ Math.round(portfolioWeights.commodity * 100) }}%</span>
          </div>
          <div class="weight-chip cash">
            <span class="weight-chip-label">现金</span>
            <span class="weight-chip-value">{{ Math.round(portfolioWeights.cash * 100) }}%</span>
          </div>
        </div>

        <div class="portfolio-holdings portfolio-float-holdings">
          <div class="holdings-header">
            <span>标的</span>
            <span>目标仓位</span>
          </div>
          <div
            v-for="h in portfolioHoldings"
            :key="h.code"
            class="holding-row"
          >
            <div class="holding-info">
              <span class="holding-name">{{ h.name }}</span>
              <span class="holding-code">{{ h.code }}</span>
            </div>
            <div class="holding-weight-bar">
              <div class="holding-weight-track">
                <div
                  class="holding-weight-fill"
                  :class="h.asset_class"
                  :style="{ width: h.weight + '%' }"
                ></div>
              </div>
              <span class="holding-weight-text">{{ h.weight }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-page {
  min-height: 100vh;
  background: #fafafa;
  display: flex;
  flex-direction: column;
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

/* Header */
.page-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.85);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  padding: 12px 0 0;
}
.page-header-inner {
  max-width: 800px; margin: 0 auto; padding: 0 24px;
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
.header-title { display: flex; flex-direction: column; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }
.step-counter { font-size: 0.78rem; color: #a3a3a3; font-weight: 500; }

.portfolio-link {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.08);
  background: #fff;
  color: #525252;
  font-size: 0.78rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.portfolio-link:hover {
  background: #f5f5f5; color: #171717;
  border-color: rgba(0,0,0,0.12);
}
.header-sub {
  max-width: 800px; margin: 8px auto 0; padding: 0 24px;
}

.progress-wrap {
  max-width: 800px; margin: 12px auto 0; padding: 0 24px;
}
.progress-track {
  height: 3px; background: #e5e5e5; border-radius: 999px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: #171717; border-radius: 999px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Step Nav */
.step-nav {
  display: none;
  max-width: 800px; margin: 0 auto; padding: 16px 24px 0;
  gap: 8px; flex-wrap: wrap; position: relative; z-index: 1;
}
@media (min-width: 768px) {
  .step-nav { display: flex; }
}
.step-nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.06);
  background: #fff;
  color: #737373;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.step-nav-item:hover {
  border-color: rgba(0,0,0,0.1);
  color: #171717;
}
.step-nav-item.active {
  background: #171717;
  color: #fff;
  border-color: #171717;
}
.step-nav-item.completed {
  border-color: rgba(34,197,94,0.2);
  color: #166534;
  background: #f0fdf4;
}
.step-nav-num {
  font-size: 0.65rem;
  font-weight: 700;
  opacity: 0.5;
}
.step-nav-check {
  color: #22c55e;
}

/* Content */
.guide-content {
  flex: 1;
  max-width: 800px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; position: relative; z-index: 1;
}
.loading-state {
  display: flex; align-items: center; gap: 12px;
  justify-content: center; padding: 60px;
  color: #a3a3a3;
}
.spinner {
  width: 20px; height: 20px;
  border: 2px solid #e5e5e5; border-top-color: #171717; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Portfolio Summary Card */
.portfolio-summary-card {
  background: #fff; border-radius: 20px;
  padding: 20px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
}
.portfolio-summary-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.portfolio-summary-title {
  font-size: 1rem; font-weight: 700; color: #171717;
}
.portfolio-summary-link {
  display: flex; align-items: center; gap: 4px;
  font-size: 0.78rem; font-weight: 600;
  color: #4f46e5; background: transparent;
  border: none; cursor: pointer;
}
.portfolio-summary-link:hover { color: #4338ca; }

/* Floating Portfolio Summary */
.portfolio-float {
  position: fixed;
  top: 84px;
  right: calc(max(16px, 50% - 400px + 16px));
  z-index: 60;
  max-width: calc(100vw - 32px);
  width: 340px;
  transition: all 0.25s ease;
}
.portfolio-float-collapsed {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  background: #171717; color: #fff;
  border: none; border-radius: 999px;
  font-size: 0.85rem; font-weight: 600;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  cursor: pointer; transition: all 0.2s ease;
  float: right;
}
.portfolio-float-collapsed:hover {
  background: #262626;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.2);
}
.portfolio-float-card {
  max-height: calc(100vh - 96px);
  display: flex; flex-direction: column;
  overflow: hidden;
}
.portfolio-summary-actions {
  display: flex; align-items: center; gap: 8px;
}
.portfolio-summary-close {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: #fafafa; border: 1px solid rgba(0,0,0,0.06);
  border-radius: 8px; color: #525252;
  cursor: pointer; transition: all 0.2s;
}
.portfolio-summary-close:hover {
  background: #f5f5f5; color: #171717;
}
.portfolio-float-holdings {
  overflow-y: auto;
  padding-right: 4px;
  margin-right: -4px;
}
.portfolio-float-holdings::-webkit-scrollbar { width: 4px; }
.portfolio-float-holdings::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15); border-radius: 4px;
}

@media (max-width: 420px) {
  .portfolio-float { width: calc(100vw - 32px); }
}

.portfolio-weights {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 10px; margin-bottom: 20px;
}
.weight-chip {
  display: flex; flex-direction: column; align-items: center;
  gap: 4px; padding: 12px 8px;
  border-radius: 12px; background: #fafafa;
  border: 1px solid rgba(0,0,0,0.04);
}
.weight-chip-label { font-size: 0.72rem; color: #737373; font-weight: 500; }
.weight-chip-value { font-size: 1rem; font-weight: 800; color: #171717; }
.weight-chip.stock { background: #eef2ff; }
.weight-chip.bond { background: #eff6ff; }
.weight-chip.commodity { background: #fffbeb; }
.weight-chip.cash { background: #f0fdf4; }

.holdings-header {
  display: flex; justify-content: space-between;
  font-size: 0.7rem; font-weight: 700; color: #a3a3a3;
  text-transform: uppercase; letter-spacing: 0.05em;
  margin-bottom: 10px; padding: 0 4px;
}
.holding-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  background: #fafafa; border-radius: 12px;
  margin-bottom: 8px;
}
.holding-info {
  display: flex; flex-direction: column;
  gap: 2px; min-width: 0;
}
.holding-name {
  font-size: 0.85rem; font-weight: 600; color: #171717;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.holding-code {
  font-size: 0.72rem; color: #a3a3a3; font-weight: 500;
}
.holding-weight-bar {
  display: flex; align-items: center; gap: 10px;
  width: 140px; flex-shrink: 0;
}
.holding-weight-track {
  flex: 1; height: 6px;
  background: #e5e5e5; border-radius: 999px;
  overflow: hidden;
}
.holding-weight-fill {
  height: 100%; border-radius: 999px;
}
.holding-weight-fill.stock { background: #6366f1; }
.holding-weight-fill.bond { background: #3b82f6; }
.holding-weight-fill.commodity { background: #f59e0b; }
.holding-weight-fill.cash { background: #10b981; }
.holding-weight-text {
  font-size: 0.8rem; font-weight: 700; color: #171717;
  min-width: 36px; text-align: right;
}

.step-card {
  background: #fff; border-radius: 20px;
  padding: 28px 24px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
}
.step-badge {
  font-size: 0.6rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.1em; margin-bottom: 12px;
}
.step-title {
  font-size: 1.3rem; font-weight: 700; color: #171717;
  margin: 0 0 8px; letter-spacing: -0.02em;
}
.step-desc {
  font-size: 0.85rem; color: #737373; margin: 0 0 24px;
  line-height: 1.6;
}

/* Checklist */
.checklist {
  display: flex; flex-direction: column; gap: 10px;
  margin-bottom: 24px;
}
.check-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px 16px;
  background: #fafafa;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.2s;
}
.check-item:hover {
  border-color: rgba(0,0,0,0.08);
  background: #f5f5f5;
}
.check-item.checked {
  background: #f0fdf4;
  border-color: rgba(34,197,94,0.15);
}
.check-box {
  width: 22px; height: 22px; border-radius: 6px;
  border: 2px solid #d4d4d4;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
  transition: all 0.2s;
  color: #fff;
}
.check-item.checked .check-box {
  background: #22c55e;
  border-color: #22c55e;
}
.check-text {
  font-size: 0.85rem; color: #525252;
  line-height: 1.5; font-weight: 500;
  transition: color 0.2s;
}
.check-item.checked .check-text {
  color: #166534;
  text-decoration: line-through;
  text-decoration-color: rgba(22,197,94,0.3);
}

/* Tip */
.tip-box {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid;
}
.tip-icon {
  flex-shrink: 0; margin-top: 1px;
}
.tip-text {
  font-size: 0.82rem;
  line-height: 1.6;
  font-weight: 500;
}

/* Footer */
.guide-footer {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 50;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(20px) saturate(1.3);
  border-top: 1px solid rgba(0,0,0,0.05);
  max-width: 800px; margin: 0 auto;
  padding: 12px 24px calc(12px + env(safe-area-inset-bottom, 0px));
  display: flex; align-items: center; justify-content: space-between;
}

.btn-primary {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 28px;
  border: none; border-radius: 14px;
  background: #171717; color: #fff;
  font-family: inherit; font-size: 0.88rem; font-weight: 600;
  letter-spacing: -0.01em; cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary:hover { background: #262626; transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,0,0,0.15); }

.btn-secondary {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 24px;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 14px;
  background: #fff; color: #525252;
  font-family: inherit; font-size: 0.88rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-secondary:hover { border-color: rgba(0,0,0,0.12); color: #171717; }

@media (min-width: 768px) {
  .guide-content { padding: 28px 32px 40px; }
  .guide-footer {
    border-radius: 16px 16px 0 0;
    border: 1px solid rgba(0,0,0,0.05); border-bottom: none;
    bottom: 12px;
  }
}
</style>

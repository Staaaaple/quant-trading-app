<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import LegalNotice from '@/components/LegalNotice.vue'

const router = useRouter()

// ── 模拟策略匹配数据（后端未做，前端占位）──
const portfolioLifespan = ref({
  totalMonths: 18,
  startDate: '2026-06',
  endDate: '2027-12',
  healthScore: 85,
})

const assetStrategies = ref([
  {
    assetName: '股票',
    assetCode: '300750/562360/601138',
    color: '#171717',
    strategy: {
      name: '多因子量化选股',
      desc: '融合估值+动量+质量三因子，AI动态调仓',
      lifespanMonths: 12,
      currentMonth: 3,
      platform: 'QMT',
      apiType: 'Python API',
      apiDoc: 'https://qmt.thinktrader.com',
      status: '运行中',
    },
    nextStep: '开通 QMT 实盘权限，配置 Python 策略文件',
  },
  {
    assetName: '债券',
    assetCode: '019742/110037',
    color: '#525252',
    strategy: {
      name: '利率曲线骑乘',
      desc: '捕捉期限利差，久期动态管理',
      lifespanMonths: 24,
      currentMonth: 6,
      platform: '聚宽',
      apiType: 'REST API',
      apiDoc: 'https://www.joinquant.com',
      status: '运行中',
    },
    nextStep: '确认债券篮子权限，接入 JoinQuant REST API',
  },
  {
    assetName: '商品',
    assetCode: '518880/159985',
    color: '#a3a3a3',
    strategy: {
      name: '趋势跟踪CTA',
      desc: '多周期均线突破，自动止盈止损',
      lifespanMonths: 8,
      currentMonth: 2,
      platform: '掘金量化',
      apiType: 'Python SDK',
      apiDoc: 'https://www.myquant.cn',
      status: '运行中',
    },
    nextStep: '申请期货账户，部署 CTA 策略到掘金量化',
  },
  {
    assetName: '现金',
    assetCode: '000198',
    color: '#d4d4d4',
    strategy: {
      name: '智能现金管理',
      desc: '货币基金轮动，T+0快速赎回',
      lifespanMonths: 36,
      currentMonth: 12,
      platform: '支付宝',
      apiType: 'OpenAPI',
      apiDoc: 'https://open.alipay.com',
      status: '长期',
    },
    nextStep: '授权货币基金自动申购赎回',
  },
])

const executionSteps = ref([
  { phase: '准备阶段', date: '2026-06', action: '开通各平台账号与 API 权限', status: 'done' },
  { phase: '接入阶段', date: '2026-06', action: '完成策略代码部署与回测验证', status: 'done' },
  { phase: '部署阶段', date: '2026-07', action: '启动实盘交易并设置风控阈值', status: 'active' },
  { phase: '监控阶段', date: '持续', action: '每日跟踪信号、每月评估策略健康度', status: 'pending' },
])

const liveInterfaces = ref([
  {
    platform: 'QMT',
    apiType: 'Python API',
    license: 'commercial',
    status: 'pending',
    docUrl: 'https://qmt.thinktrader.com',
    steps: ['开通券商 QMT 权限', '下载 XtQuant', '配置交易账户'],
  },
  {
    platform: '聚宽',
    apiType: 'REST API',
    license: 'commercial',
    status: 'pending',
    docUrl: 'https://www.joinquant.com',
    steps: ['注册聚宽账号', '申请实盘权限', '绑定券商'],
  },
  {
    platform: '掘金量化',
    apiType: 'Python SDK',
    license: 'commercial',
    status: 'pending',
    docUrl: 'https://www.myquant.cn',
    steps: ['开通期货账户', '安装 myquant SDK', '配置策略托管'],
  },
  {
    platform: 'vn.py',
    apiType: 'Python 开源框架',
    license: 'opensource',
    status: 'ready',
    docUrl: 'https://www.vnpy.com',
    steps: ['pip install vnpy', '选择券商/CTP 网关', '启动策略引擎'],
  },
])

const backtestInterfaces = ref([
  {
    platform: 'Backtrader',
    apiType: 'Python 回测框架',
    license: 'opensource',
    status: 'ready',
    docUrl: 'https://www.backtrader.com',
    steps: ['pip install backtrader', '准备行情数据', '编写 Strategy 类'],
  },
  {
    platform: 'Zipline',
    apiType: 'Python 回测框架',
    license: 'opensource',
    status: 'pending',
    docUrl: 'https://www.zipline.io',
    steps: ['pip install zipline-reloaded', '注册 bundle 数据源', '运行回测'],
  },
  {
    platform: '聚宽',
    apiType: '云端回测',
    license: 'commercial',
    status: 'pending',
    docUrl: 'https://www.joinquant.com',
    steps: ['注册账号', '上传策略代码', '点击回测'],
  },
  {
    platform: 'Ricequant',
    apiType: '云端回测',
    license: 'commercial',
    status: 'pending',
    docUrl: 'https://www.ricequant.com',
    steps: ['注册米筐账号', '使用 rqalpha 编写策略', '提交回测任务'],
  },
])

const tutorials = ref([
  { step: 1, title: '开通实盘权限', desc: '在对应券商/平台完成实名认证并申请量化交易权限。' },
  { step: 2, title: '部署策略代码', desc: '将本地策略文件上传至平台，或调用 API 接入自托管环境。' },
  { step: 3, title: '配置风控参数', desc: '设置单笔止损、仓位上限、日回撤阈值等风控规则。' },
  { step: 4, title: '启动自动交易', desc: '开启信号订阅，确认委托模式后启动实盘自动执行。' },
  { step: 5, title: '每日监控与调优', desc: '查看成交记录、策略健康度，定期复盘并优化参数。' },
])

const totalProgress = computed(() => {
  const total = portfolioLifespan.value.totalMonths
  const current = assetStrategies.value.reduce((s, a) => s + a.strategy.currentMonth, 0) / assetStrategies.value.length
  return Math.round((current / total) * 100)
})

const completedSteps = computed(() => executionSteps.value.filter(s => s.status === 'done').length)
const readyInterfaces = computed(() => liveInterfaces.value.filter(i => i.status === 'ready').length)
const readyBacktests = computed(() => backtestInterfaces.value.filter(i => i.status === 'ready').length)

function goBack() {
  router.push('/portfolio')
}

function goLifespan() {
  router.push('/ecosystem')
}

function goBacktests() {
  router.push('/backtests')
}

function lifespanPct(current: number, total: number) {
  return Math.round((current / total) * 100)
}

function lifespanStatus(current: number, total: number) {
  const pct = current / total
  if (pct < 0.3) return '早期'
  if (pct < 0.7) return '中期'
  if (pct < 0.9) return '后期'
  return '即将到期'
}

function lifespanColor(current: number, total: number) {
  const pct = current / total
  if (pct < 0.3) return '#22c55e'
  if (pct < 0.7) return '#d97706'
  return '#ef4444'
}

function stepIcon(status: string) {
  if (status === 'done') return '✓'
  if (status === 'active') return '●'
  return '○'
}

function stepColor(status: string) {
  if (status === 'done') return '#22c55e'
  if (status === 'active') return '#6366f1'
  return '#d4d4d4'
}

function interfaceStatusText(status: string) {
  if (status === 'ready') return '已接入'
  return '待接入'
}

function interfaceStatusColor(status: string) {
  if (status === 'ready') return '#22c55e'
  return '#d97706'
}

function licenseText(license: string) {
  return license === 'opensource' ? '开源' : '商业'
}

function licenseColor(license: string) {
  return license === 'opensource' ? '#22c55e' : '#6366f1'
}

function scrollToExecution() {
  document.getElementById('execution-section')?.scrollIntoView({ behavior: 'smooth' })
}

function confirmExecution() {
  alert('执行方案已确认（演示）')
}
</script>

<template>
  <div class="strategy-match-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <div class="header-title">
          <span class="header-label">STRATEGIES</span>
          <span class="header-name">策略匹配与执行</span>
        </div>
        <div style="width: 36px"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="match-content">
      <LegalNotice
        title="策略匹配与执行声明"
        :show-data-source="true"
        :show-investment-disclaimer="true"
        :show-privacy="true"
        :show-license="true"
        :show-crawler="true"
      />

      <!-- 组合总寿命 -->
      <div class="lifespan-card" @click="goLifespan">
        <div class="lifespan-header">
          <div>
            <div class="lifespan-label">组合总寿命</div>
            <div class="lifespan-period">{{ portfolioLifespan.startDate }} ~ {{ portfolioLifespan.endDate }}</div>
          </div>
          <div class="lifespan-health">
            <span class="health-score">{{ portfolioLifespan.healthScore }}</span>
            <span class="health-label">健康度</span>
          </div>
        </div>

        <div class="lifespan-progress-wrap">
          <div class="lifespan-bar-bg">
            <div class="lifespan-bar-fill" :style="{ width: totalProgress + '%' }"></div>
          </div>
          <div class="lifespan-progress-text">
            <span>已运行 {{ Math.round(assetStrategies.reduce((s, a) => s + a.strategy.currentMonth, 0) / assetStrategies.length) }} 个月</span>
            <span>剩余 {{ portfolioLifespan.totalMonths - Math.round(assetStrategies.reduce((s, a) => s + a.strategy.currentMonth, 0) / assetStrategies.length) }} 个月</span>
          </div>
        </div>

        <div class="lifespan-arrow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9 18 6-6-6-6"/>
          </svg>
        </div>
      </div>

      <!-- 策略卡片 -->
      <div class="strategy-list">
        <div v-for="item in assetStrategies" :key="item.assetName" class="strategy-card">
          <div class="strategy-card-header">
            <div class="asset-info">
              <span class="asset-dot" :style="{ background: item.color }"></span>
              <div>
                <div class="asset-name">{{ item.assetName }}</div>
                <div class="asset-code">{{ item.assetCode }}</div>
              </div>
            </div>
            <span class="strategy-status" :style="{ color: lifespanColor(item.strategy.currentMonth, item.strategy.lifespanMonths) }">
              {{ lifespanStatus(item.strategy.currentMonth, item.strategy.lifespanMonths) }}
            </span>
          </div>

          <div class="strategy-info">
            <div class="strategy-name">{{ item.strategy.name }}</div>
            <p class="strategy-desc">{{ item.strategy.desc }}</p>
          </div>

          <div class="platform-row">
            <div class="platform-badge">
              <span class="platform-name">{{ item.strategy.platform }}</span>
              <span class="platform-api">{{ item.strategy.apiType }}</span>
            </div>
            <a :href="item.strategy.apiDoc" target="_blank" class="api-link" @click.stop>
              <span>API文档</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" x2="21" y1="14" y2="3"/>
              </svg>
            </a>
          </div>

          <div class="next-step-box">
            <span class="next-step-label">下一步</span>
            <span class="next-step-text">{{ item.nextStep }}</span>
          </div>

          <div class="strategy-lifespan">
            <div class="lifespan-top">
              <span class="lifespan-label-small">策略寿命</span>
              <span class="lifespan-nums">{{ item.strategy.currentMonth }} / {{ item.strategy.lifespanMonths }} 月</span>
            </div>
            <div class="lifespan-bar-bg-small">
              <div class="lifespan-bar-fill-small" :style="{ width: lifespanPct(item.strategy.currentMonth, item.strategy.lifespanMonths) + '%', background: lifespanColor(item.strategy.currentMonth, item.strategy.lifespanMonths) }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 执行方案 -->
      <div id="execution-section" class="section-card">
        <div class="section-header">
          <span class="section-label">EXECUTION</span>
          <span class="section-name">执行方案</span>
          <span class="section-badge">{{ completedSteps }} / {{ executionSteps.length }} 已完成</span>
        </div>

        <div class="timeline">
          <div v-for="(step, i) in executionSteps" :key="step.phase" class="timeline-item">
            <div class="timeline-marker" :style="{ background: stepColor(step.status), color: '#fff' }">
              {{ stepIcon(step.status) }}
            </div>
            <div class="timeline-body">
              <div class="timeline-top">
                <span class="timeline-phase">{{ step.phase }}</span>
                <span class="timeline-date">{{ step.date }}</span>
              </div>
              <div class="timeline-action">{{ step.action }}</div>
            </div>
            <div v-if="i < executionSteps.length - 1" class="timeline-line"></div>
          </div>
        </div>
      </div>

      <!-- 实盘接口 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-label">LIVE API</span>
          <span class="section-name">实盘接口</span>
          <span class="section-badge">{{ readyInterfaces }} / {{ liveInterfaces.length }} 已接入</span>
        </div>

        <div class="interface-list">
          <div v-for="item in liveInterfaces" :key="item.platform" class="interface-card">
            <div class="interface-header">
              <div class="interface-title">
                <span class="interface-platform">{{ item.platform }}</span>
                <span class="interface-api">{{ item.apiType }}</span>
              </div>
              <div class="interface-tags">
                <span class="interface-tag" :style="{ color: licenseColor(item.license), background: licenseColor(item.license) + '12' }">{{ licenseText(item.license) }}</span>
                <span class="interface-status" :style="{ color: interfaceStatusColor(item.status) }">{{ interfaceStatusText(item.status) }}</span>
              </div>
            </div>

            <div class="interface-steps">
              <div v-for="(s, idx) in item.steps" :key="idx" class="interface-step">
                <span class="interface-step-num">{{ idx + 1 }}</span>
                <span class="interface-step-text">{{ s }}</span>
              </div>
            </div>

            <a :href="item.docUrl" target="_blank" class="interface-doc">
              <span>查看官方接入文档</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" x2="21" y1="14" y2="3"/>
              </svg>
            </a>
          </div>
        </div>
      </div>

      <!-- 回测接口 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-label">BACKTEST</span>
          <span class="section-name">回测接口</span>
          <span class="section-badge">{{ readyBacktests }} / {{ backtestInterfaces.length }} 已接入</span>
        </div>

        <div class="interface-list">
          <div v-for="item in backtestInterfaces" :key="item.platform" class="interface-card">
            <div class="interface-header">
              <div class="interface-title">
                <span class="interface-platform">{{ item.platform }}</span>
                <span class="interface-api">{{ item.apiType }}</span>
              </div>
              <div class="interface-tags">
                <span class="interface-tag" :style="{ color: licenseColor(item.license), background: licenseColor(item.license) + '12' }">{{ licenseText(item.license) }}</span>
                <span class="interface-status" :style="{ color: interfaceStatusColor(item.status) }">{{ interfaceStatusText(item.status) }}</span>
              </div>
            </div>

            <div class="interface-steps">
              <div v-for="(s, idx) in item.steps" :key="idx" class="interface-step">
                <span class="interface-step-num">{{ idx + 1 }}</span>
                <span class="interface-step-text">{{ s }}</span>
              </div>
            </div>

            <a :href="item.docUrl" target="_blank" class="interface-doc">
              <span>查看官方接入文档</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" x2="21" y1="14" y2="3"/>
              </svg>
            </a>
          </div>
        </div>

        <button class="secondary-btn" @click="goBacktests">
          <span>进入回测中心</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14"/>
            <path d="m12 5 7 7-7 7"/>
          </svg>
        </button>
      </div>

      <!-- 实盘教学 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-label">TUTORIAL</span>
          <span class="section-name">实盘教学</span>
        </div>

        <div class="tutorial-list">
          <div v-for="t in tutorials" :key="t.step" class="tutorial-card">
            <div class="tutorial-step">{{ t.step }}</div>
            <div class="tutorial-body">
              <div class="tutorial-title">{{ t.title }}</div>
              <div class="tutorial-desc">{{ t.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer CTA -->
      <div class="footer-cta">
        <button class="primary-btn" @click="confirmExecution">
          <span>确认并开始执行</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14"/>
            <path d="m12 5 7 7-7 7"/>
          </svg>
        </button>
      </div>

      <!-- Footer Note -->
      <div class="footer-note">
        <p>策略寿命到期后系统将自动推荐替换策略</p>
        <p>量化接口需自行开通对应平台账号</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.strategy-match-page {
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
.header-title { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }

/* Content */
.match-content {
  max-width: 720px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 16px;
  position: relative; z-index: 1;
}

/* Lifespan Card */
.lifespan-card {
  background: #171717; border-radius: 20px; padding: 24px 22px;
  color: #fff; cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}
.lifespan-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
.lifespan-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 20px;
}
.lifespan-label {
  font-size: 0.65rem; font-weight: 700; color: rgba(255,255,255,0.5);
  letter-spacing: 0.1em; text-transform: uppercase;
  margin-bottom: 6px;
}
.lifespan-period {
  font-size: 0.85rem; color: rgba(255,255,255,0.7);
  font-family: ui-monospace, SFMono-Regular, monospace;
}
.lifespan-health {
  text-align: center;
}
.health-score {
  font-size: 1.8rem; font-weight: 800; color: #fff;
  display: block; line-height: 1;
}
.health-label {
  font-size: 0.65rem; color: rgba(255,255,255,0.5);
  letter-spacing: 0.05em;
}
.lifespan-progress-wrap {
  margin-bottom: 4px;
}
.lifespan-bar-bg {
  height: 8px; background: rgba(255,255,255,0.1);
  border-radius: 999px; overflow: hidden; margin-bottom: 10px;
}
.lifespan-bar-fill {
  height: 100%; background: #fff; border-radius: 999px;
  transition: width 0.5s ease;
}
.lifespan-progress-text {
  display: flex; justify-content: space-between;
  font-size: 0.75rem; color: rgba(255,255,255,0.5);
}
.lifespan-arrow {
  position: absolute; right: 16px; top: 50%;
  transform: translateY(-50%);
  color: rgba(255,255,255,0.3);
}

/* Strategy Cards */
.strategy-list {
  display: flex; flex-direction: column; gap: 12px;
}
.strategy-card {
  background: #fff; border-radius: 18px; padding: 20px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.2s ease;
}
.strategy-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border-color: rgba(0,0,0,0.08);
}
.strategy-card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.asset-info {
  display: flex; align-items: center; gap: 10px;
}
.asset-dot {
  width: 10px; height: 10px; border-radius: 50%;
  flex-shrink: 0;
}
.asset-name {
  font-size: 0.95rem; font-weight: 700; color: #171717;
}
.asset-code {
  font-size: 0.72rem; color: #a3a3a3;
  font-family: ui-monospace, SFMono-Regular, monospace;
}
.strategy-status {
  font-size: 0.75rem; font-weight: 600;
  padding: 4px 10px; background: #fafafa;
  border-radius: 6px;
}
.strategy-info {
  margin-bottom: 14px;
}
.strategy-name {
  font-size: 0.92rem; font-weight: 600; color: #171717;
  margin-bottom: 4px;
}
.strategy-desc {
  font-size: 0.78rem; color: #737373; line-height: 1.5;
  margin: 0;
}
.platform-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.platform-badge {
  display: flex; align-items: center; gap: 8px;
}
.platform-name {
  font-size: 0.82rem; font-weight: 600; color: #171717;
  padding: 5px 12px; background: #fafafa;
  border-radius: 8px; border: 1px solid rgba(0,0,0,0.06);
}
.platform-api {
  font-size: 0.72rem; color: #a3a3a3;
}
.api-link {
  display: flex; align-items: center; gap: 4px;
  font-size: 0.75rem; color: #525252;
  text-decoration: none; padding: 5px 10px;
  background: #fafafa; border-radius: 6px;
  transition: all 0.2s;
}
.api-link:hover {
  background: #f0f0f0; color: #171717;
}
.next-step-box {
  display: flex; flex-direction: column; gap: 4px;
  padding: 12px 14px; background: #fafafa;
  border-radius: 10px; margin-bottom: 14px;
  border: 1px solid rgba(0,0,0,0.04);
}
.next-step-label {
  font-size: 0.68rem; font-weight: 700; color: #6366f1;
  letter-spacing: 0.05em;
}
.next-step-text {
  font-size: 0.8rem; color: #171717; line-height: 1.5;
}
.strategy-lifespan {
  padding-top: 14px;
  border-top: 1px solid rgba(0,0,0,0.05);
}
.lifespan-top {
  display: flex; justify-content: space-between;
  margin-bottom: 8px;
}
.lifespan-label-small {
  font-size: 0.72rem; color: #a3a3a3;
}
.lifespan-nums {
  font-size: 0.78rem; font-weight: 600; color: #171717;
  font-family: ui-monospace, SFMono-Regular, monospace;
}
.lifespan-bar-bg-small {
  height: 6px; background: #f0f0f0;
  border-radius: 999px; overflow: hidden;
}
.lifespan-bar-fill-small {
  height: 100%; border-radius: 999px;
  transition: width 0.5s ease;
}

/* Section Card */
.section-card {
  background: #fff; border-radius: 20px; padding: 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.section-header {
  display: flex; align-items: baseline; gap: 8px;
  margin-bottom: 18px;
}
.section-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.section-name { font-size: 0.95rem; font-weight: 700; color: #171717; flex: 1; }
.section-badge {
  font-size: 0.72rem; font-weight: 600; color: #6366f1;
  background: #eef2ff; padding: 4px 10px; border-radius: 6px;
}

/* Timeline */
.timeline {
  display: flex; flex-direction: column; gap: 0;
}
.timeline-item {
  display: flex; gap: 14px;
  position: relative;
  padding-bottom: 20px;
}
.timeline-marker {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700;
  flex-shrink: 0; z-index: 1;
}
.timeline-line {
  position: absolute; left: 11px; top: 24px; bottom: 0;
  width: 2px; background: #f0f0f0;
}
.timeline-body {
  flex: 1; padding-top: 2px;
}
.timeline-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 4px;
}
.timeline-phase {
  font-size: 0.85rem; font-weight: 700; color: #171717;
}
.timeline-date {
  font-size: 0.72rem; color: #a3a3a3;
  font-family: ui-monospace, SFMono-Regular, monospace;
}
.timeline-action {
  font-size: 0.8rem; color: #525252; line-height: 1.5;
}

/* Live Interface */
.interface-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
.interface-card {
  background: #fafafa; border-radius: 14px; padding: 16px 18px;
  border: 1px solid rgba(0,0,0,0.04);
}
.interface-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.interface-title {
  display: flex; align-items: baseline; gap: 8px;
}
.interface-platform {
  font-size: 0.9rem; font-weight: 700; color: #171717;
}
.interface-api {
  font-size: 0.72rem; color: #a3a3a3;
}
.interface-tags {
  display: flex; align-items: center; gap: 6px;
}
.interface-tag {
  font-size: 0.68rem; font-weight: 600;
  padding: 3px 8px; border-radius: 6px;
}
.interface-status {
  font-size: 0.75rem; font-weight: 600;
  padding: 3px 10px; background: #fff;
  border-radius: 6px;
}
.interface-steps {
  display: flex; flex-direction: column; gap: 8px;
  margin-bottom: 12px;
}
.interface-step {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.78rem; color: #525252;
}
.interface-step-num {
  width: 18px; height: 18px; border-radius: 50%;
  background: #e5e7eb; color: #525252;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 700;
  flex-shrink: 0;
}
.interface-doc {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 0.75rem; color: #6366f1; text-decoration: none;
  font-weight: 500;
}
.interface-doc:hover { color: #4f46e5; }

/* Tutorial */
.tutorial-list {
  display: flex; flex-direction: column; gap: 10px;
}
.tutorial-card {
  display: flex; gap: 14px;
  background: #fafafa; border-radius: 12px; padding: 14px 16px;
  border: 1px solid rgba(0,0,0,0.04);
}
.tutorial-step {
  width: 28px; height: 28px; border-radius: 50%;
  background: #171717; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700;
  flex-shrink: 0;
}
.tutorial-body { flex: 1; }
.tutorial-title {
  font-size: 0.85rem; font-weight: 700; color: #171717;
  margin-bottom: 2px;
}
.tutorial-desc {
  font-size: 0.76rem; color: #737373; line-height: 1.5;
}

/* Footer CTA */
.footer-cta {
  margin-top: 8px;
}
.primary-btn {
  width: 100%;
  display: flex;
  align-items: center; justify-content: center; gap: 8px;
  padding: 16px;
  background: #171717; color: #fff;
  border: none; border-radius: 14px;
  font-size: 0.9rem; font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.primary-btn:hover {
  background: #262626;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}
.secondary-btn {
  width: 100%;
  display: flex;
  align-items: center; justify-content: center; gap: 8px;
  padding: 14px 16px;
  margin-top: 16px;
  background: #fff; color: #171717;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 14px;
  font-size: 0.9rem; font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.secondary-btn:hover {
  background: #fafafa;
  border-color: rgba(0,0,0,0.12);
  transform: translateY(-1px);
}

.footer-note {
  text-align: center; padding: 16px;
}
.footer-note p {
  font-size: 0.72rem; color: #a3a3a3; margin: 4px 0;
}

@media (min-width: 640px) {
  .interface-list { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 768px) {
  .match-content { padding: 24px 32px 40px; }
}
</style>

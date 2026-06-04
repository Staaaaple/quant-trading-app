<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

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
      platformIcon: 'qmt',
      apiType: 'Python API',
      apiDoc: 'https://qmt.thinktrader.com',
      status: '运行中',
    },
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
      platformIcon: 'joinquant',
      apiType: 'REST API',
      apiDoc: 'https://www.joinquant.com',
      status: '运行中',
    },
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
      platformIcon: 'myquant',
      apiType: 'Python SDK',
      apiDoc: 'https://www.myquant.cn',
      status: '运行中',
    },
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
      platformIcon: 'alipay',
      apiType: 'OpenAPI',
      apiDoc: 'https://open.alipay.com',
      status: '长期',
    },
  },
])

// 计算总寿命进度
const totalProgress = computed(() => {
  const total = portfolioLifespan.value.totalMonths
  const current = assetStrategies.value.reduce((s, a) => s + a.strategy.currentMonth, 0) / assetStrategies.value.length
  return Math.round((current / total) * 100)
})

function goBack() {
  router.push('/portfolio')
}

function goLifespan() {
  router.push('/lifespan')
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
</script>

<template>
  <div class="strategy-match-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-label">STRATEGIES</span>
          <span class="header-name">策略匹配</span>
        </div>
        <div style="width: 36px"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="match-content">
      <!-- Total Lifespan Card -->
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
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
        </div>
      </div>

      <!-- Strategy Cards -->
      <div class="strategy-list">
        <div
          v-for="item in assetStrategies"
          :key="item.assetName"
          class="strategy-card"
        >
          <!-- Asset Header -->
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

          <!-- Strategy Info -->
          <div class="strategy-info">
            <div class="strategy-name">{{ item.strategy.name }}</div>
            <p class="strategy-desc">{{ item.strategy.desc }}</p>
          </div>

          <!-- Platform & API -->
          <div class="platform-row">
            <div class="platform-badge">
              <span class="platform-name">{{ item.strategy.platform }}</span>
              <span class="platform-api">{{ item.strategy.apiType }}</span>
            </div>
            <a :href="item.strategy.apiDoc" target="_blank" class="api-link" @click.stop>
              <span>API文档</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/></svg>
            </a>
          </div>

          <!-- Lifespan -->
          <div class="strategy-lifespan">
            <div class="lifespan-top">
              <span class="lifespan-label-small">策略寿命</span>
              <span class="lifespan-nums">{{ item.strategy.currentMonth }} / {{ item.strategy.lifespanMonths }} 月</span>
            </div>
            <div class="lifespan-bar-bg-small">
              <div
                class="lifespan-bar-fill-small"
                :style="{
                  width: lifespanPct(item.strategy.currentMonth, item.strategy.lifespanMonths) + '%',
                  background: lifespanColor(item.strategy.currentMonth, item.strategy.lifespanMonths)
                }"
              ></div>
            </div>
          </div>
        </div>
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

/* Card Header */
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

/* Strategy Info */
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

/* Platform Row */
.platform-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
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

/* Lifespan Bar */
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

/* Footer Note */
.footer-note {
  text-align: center; padding: 16px;
}
.footer-note p {
  font-size: 0.72rem; color: #a3a3a3; margin: 4px 0;
}

@media (min-width: 768px) {
  .match-content { padding: 24px 32px 40px; }
}
</style>

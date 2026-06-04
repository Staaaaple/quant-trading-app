<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ── 模拟资产配置数据（后端未做，前端占位）──
// 系统推荐的具体持仓组合
const assetAllocation = ref([
  {
    id: 'stock',
    name: '股票',
    pct: 45,
    color: '#171717',
    desc: 'A股核心资产+行业龙头',
    // 系统推荐的具体持仓组合
    holdings: [
      { name: '宁德时代', code: '300750', weight: 50, reason: '新能源龙头，动力电池全球第一' },
      { name: '机器人ETF', code: '562360', weight: 30, reason: '人形机器人赛道，政策+产业双驱动' },
      { name: '工业富联', code: '601138', weight: 20, reason: 'AI服务器代工，算力基建核心标的' },
    ],
  },
  {
    id: 'bond',
    name: '债券',
    pct: 30,
    color: '#525252',
    desc: '国债+高等级信用债',
    holdings: [
      { name: '24国债05', code: '019742', weight: 60, reason: '10年期国债，票息2.5%，避险首选' },
      { name: '易方达纯债A', code: '110037', weight: 40, reason: '老牌债基，年化4.2%，波动极低' },
    ],
  },
  {
    id: 'commodity',
    name: '商品',
    pct: 15,
    color: '#a3a3a3',
    desc: '黄金+大宗商品',
    holdings: [
      { name: '黄金ETF', code: '518880', weight: 70, reason: '地缘冲突+降息预期，黄金避险需求上升' },
      { name: '豆粕ETF', code: '159985', weight: 30, reason: '农产品通胀对冲，南美干旱支撑价格' },
    ],
  },
  {
    id: 'cash',
    name: '现金',
    pct: 10,
    color: '#d4d4d4',
    desc: '货币基金+活期存款',
    holdings: [
      { name: '天弘余额宝', code: '000198', weight: 100, reason: 'T+0赎回，年化1.8%，流动性最佳' },
    ],
  },
])

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
  router.push('/market')
}

function goNext() {
  router.push('/portfolio/strategies')
}

function goProfile() {
  router.push('/profile')
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
        <div style="width: 36px"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="portfolio-content">
      <!-- Allocation Chart -->
      <div class="alloc-card">
        <div class="alloc-header">
          <span class="alloc-label">资产配置</span>
          <span class="alloc-sub">基于当前经济周期深度衰退调整</span>
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
              <span class="detail-title">{{ asset.name }} · 策略选择</span>
            </div>

            <!-- System Recommended Holdings -->
            <div class="holdings-list">
              <div class="holdings-header">
                <span class="holdings-label">系统推荐组合</span>
                <span class="holdings-sub">基于当前深度衰退周期调整</span>
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
              <span>详细的指引</span>
            </button>
          </div>
        </div>
      </Transition>

      <!-- Summary Footer -->
      <div class="summary-footer">
        <div class="summary-item">
          <span class="summary-label">预期年化</span>
          <span class="summary-val">8-12%</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">最大回撤</span>
          <span class="summary-val">&lt;15%</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">再平衡</span>
          <span class="summary-val">季度</span>
        </div>
      </div>

      <!-- Next Page Button -->
      <button class="next-page-btn" @click="goNext">
        <span>下一页：匹配投资策略</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12h14"/>
          <path d="m12 5 7 7-7 7"/>
        </svg>
      </button>

      <!-- Rebuild Button -->
      <button class="rebuild-btn" @click="goProfile">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
          <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
          <path d="M8 16H3v5"/>
        </svg>
        <span>重新定制组合</span>
      </button>
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
            <div class="placeholder-guide">
              <div class="placeholder-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <p class="placeholder-text">详细的指引</p>
              <p class="placeholder-sub">购买教程正在编写中，敬请期待</p>
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
.header-title { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }

/* Content */
.portfolio-content {
  max-width: 720px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 16px;
  position: relative; z-index: 1;
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

/* Placeholder Guide */
.placeholder-guide {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 40px 20px; text-align: center;
}
.placeholder-icon {
  width: 64px; height: 64px; border-radius: 16px;
  background: #fafafa; color: #a3a3a3;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.placeholder-text {
  font-size: 1rem; font-weight: 600; color: #171717;
  margin: 0 0 6px;
}
.placeholder-sub {
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

/* Guide Steps */
.guide-steps {
  display: flex; flex-direction: column; gap: 16px;
  margin-bottom: 24px;
}
.guide-step {
  display: flex; gap: 14px; align-items: flex-start;
}
.step-num {
  width: 28px; height: 28px; border-radius: 50%;
  background: #171717; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.82rem; font-weight: 700;
  flex-shrink: 0;
}
.step-text {
  font-size: 0.88rem; color: #525252; line-height: 1.6;
  margin: 4px 0 0;
}

/* Guide Tip */
.guide-tip {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 16px; background: #fafafa;
  border-radius: 14px; border: 1px solid rgba(0,0,0,0.04);
}
.tip-icon {
  width: 32px; height: 32px; border-radius: 10px;
  background: #171717; color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.tip-text {
  font-size: 0.85rem; color: #525252; line-height: 1.6;
  margin: 0;
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

@media (min-width: 640px) {
  .modal-overlay { align-items: center; padding: 24px; }
  .modal-content { border-radius: 24px; max-height: 85vh; }
}

@media (min-width: 768px) {
  .portfolio-content { padding: 24px 32px 40px; }
}
</style>

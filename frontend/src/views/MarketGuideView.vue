<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  TrendingUp,
  TrendingDown,
  Minus,
  CircleGauge,
  BadgePercent,
  Banknote,
  Users,
  Globe,
  MapPin,
  AlertTriangle,
  ChartArea,
  ChartCandlestick,
  Wallet,
} from '@lucide/vue'

const router = useRouter()

function closeGuide() {
  router.push('/market')
}

const cards = [
  {
    key: 'cycle',
    title: '经济周期',
    subtitle: '经济的“春夏秋冬”',
    desc: '经济就像四季一样循环往复：衰退后迎来复苏，复苏走向繁荣，繁荣过热后又会调整。我们做的，就是判断现在处于哪个季节，从而决定该“播种”还是“收割”。',
    bg: 'linear-gradient(135deg, #fef9c3 0%, #fde68a 100%)',
    textColor: '#854d0e',
    accentColor: '#a16207',
  },
  {
    key: 'macro',
    title: '宏观基本面',
    subtitle: '经济的“体检报告”',
    desc: 'GDP 是经济的体温，通胀是血压，利率是心跳，就业是活力。四项指标合起来，告诉我们经济是健康强壮，还是需要静养观察。',
    bg: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
    textColor: '#1e40af',
    accentColor: '#1d4ed8',
  },
  {
    key: 'geo',
    title: '地缘政治',
    subtitle: '全球的“天气系统”',
    desc: '国际关系、地区冲突、政策变化就像天气系统，会影响贸易、能源和资金流动。有时候一阵“暴风雨”就能让全球市场波动加剧。',
    bg: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
    textColor: '#991b1b',
    accentColor: '#b91c1c',
  },
  {
    key: 'market',
    title: '金融市场状态',
    subtitle: '资金的“实时投票”',
    desc: '股票、债券、商品、现金每天都在被全球资金投票。当风险情绪高时资金涌向股票，避险情绪浓时则躲进债券和黄金。看懂投票结果，就看清了市场方向。',
    bg: 'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)',
    textColor: '#166534',
    accentColor: '#15803d',
  },
]

const cycleSteps = [
  { label: '复苏', icon: TrendingUp },
  { label: '繁荣', icon: TrendingUp },
  { label: '衰退', icon: TrendingDown },
  { label: '萧条', icon: Minus },
]
</script>

<template>
  <div class="guide-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="guide-header">
      <div class="guide-header-inner">
        <div class="brand">
          <div class="brand-mark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span class="brand-name">QUANT<span class="brand-muted">EVO</span></span>
        </div>
        <button class="close-btn" @click="closeGuide" aria-label="关闭引导">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 6 6 18"/>
            <path d="m6 6 12 12"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- Content -->
    <main class="guide-content">
      <div class="hero-section">
        <div class="hero-badge">市场行情</div>
        <h1 class="hero-title">了解市场，从小白开始</h1>
        <p class="hero-desc">
          在查看实时信号之前，先用 4 张图读懂影响市场的核心因素。
        </p>
      </div>

      <div class="cards-grid">
        <div
          v-for="card in cards"
          :key="card.key"
          class="info-card"
        >
          <div class="card-visual" :style="{ background: card.bg, color: card.textColor }">
            <!-- 经济周期：横向四阶段 -->
            <div v-if="card.key === 'cycle'" class="visual-cycle">
              <div
                v-for="(step, idx) in cycleSteps"
                :key="step.label"
                class="cycle-step"
              >
                <div class="step-bubble">
                  <component :is="step.icon" :size="24" :color="card.accentColor" stroke-width="2.2" />
                </div>
                <span class="step-label">{{ step.label }}</span>
                <span v-if="idx < cycleSteps.length - 1" class="step-arrow">→</span>
              </div>
            </div>

            <!-- 宏观基本面：2x2 统一图标 -->
            <div v-if="card.key === 'macro'" class="visual-macro">
              <div class="macro-item">
                <div class="macro-bubble">
                  <CircleGauge :size="28" :color="card.accentColor" stroke-width="2" />
                </div>
                <span class="macro-label">GDP · 体温</span>
              </div>
              <div class="macro-item">
                <div class="macro-bubble">
                  <BadgePercent :size="28" :color="card.accentColor" stroke-width="2" />
                </div>
                <span class="macro-label">通胀 · 血压</span>
              </div>
              <div class="macro-item">
                <div class="macro-bubble">
                  <Banknote :size="28" :color="card.accentColor" stroke-width="2" />
                </div>
                <span class="macro-label">利率 · 心跳</span>
              </div>
              <div class="macro-item">
                <div class="macro-bubble">
                  <Users :size="28" :color="card.accentColor" stroke-width="2" />
                </div>
                <span class="macro-label">就业 · 活力</span>
              </div>
            </div>

            <!-- 地缘政治：地球 + 三个同色系热点 -->
            <div v-if="card.key === 'geo'" class="visual-geo">
              <div class="geo-globe">
                <Globe :size="64" :color="card.accentColor" stroke-width="1.6" />
              </div>
              <div class="geo-hotspots">
                <div class="hotspot">
                  <MapPin :size="20" color="#fff" stroke-width="2.2" />
                </div>
                <div class="hotspot">
                  <AlertTriangle :size="20" color="#fff" stroke-width="2.2" />
                </div>
                <div class="hotspot">
                  <MapPin :size="20" color="#fff" stroke-width="2.2" />
                </div>
              </div>
            </div>

            <!-- 金融市场状态：简洁双图 -->
            <div v-if="card.key === 'market'" class="visual-market">
              <div class="market-left">
                <div class="market-big-card">
                  <ChartArea :size="56" :color="card.accentColor" stroke-width="1.6" />
                  <span class="big-card-label">趋势</span>
                </div>
              </div>
              <div class="market-right">
                <div class="market-small-card">
                  <ChartCandlestick :size="28" :color="card.accentColor" stroke-width="2" />
                  <span class="small-card-label">K线</span>
                </div>
                <div class="market-small-card">
                  <Wallet :size="28" :color="card.accentColor" stroke-width="2" />
                  <span class="small-card-label">资金</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div class="card-subtitle">{{ card.subtitle }}</div>
            <h3 class="card-title">{{ card.title }}</h3>
            <p class="card-desc">{{ card.desc }}</p>
          </div>
        </div>
      </div>

      <div class="cta-section">
        <button class="btn-primary" @click="closeGuide">
          <span>明白了，查看信号仪表盘</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14"/>
            <path d="m12 5 7 7-7 7"/>
          </svg>
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.guide-page {
  min-height: 100vh;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  position: relative;
  padding-bottom: 40px;
}

/* Textures */
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
.guide-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.82);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.guide-header-inner {
  max-width: 960px; margin: 0 auto; padding: 14px 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.brand { display: flex; align-items: center; gap: 10px; }
.brand-mark {
  width: 32px; height: 32px; border-radius: 10px;
  background: #171717; display: flex; align-items: center; justify-content: center;
  color: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.brand-name { font-size: 1.05rem; font-weight: 700; letter-spacing: -0.03em; color: #171717; }
.brand-muted { font-weight: 400; color: #a3a3a3; }

.close-btn {
  width: 38px; height: 38px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: #fff; border: 1px solid rgba(0,0,0,0.08);
  color: #525252; cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.close-btn:hover {
  background: #f5f5f5; color: #171717;
  transform: rotate(90deg);
}

/* Content */
.guide-content {
  flex: 1;
  max-width: 960px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 24px;
  position: relative; z-index: 1;
}

/* Hero */
.hero-section { text-align: center; padding: 20px 0 8px; }
.hero-badge {
  display: inline-block; padding: 6px 14px;
  background: #dcfce7; color: #166534;
  font-size: 0.72rem; font-weight: 700;
  border-radius: 999px; margin-bottom: 14px;
  letter-spacing: 0.02em;
}
.hero-title {
  font-size: 1.8rem; font-weight: 800; color: #171717;
  margin: 0 0 10px; letter-spacing: -0.03em;
}
.hero-desc {
  font-size: 0.9rem; color: #737373; margin: 0;
  max-width: 480px; margin-left: auto; margin-right: auto;
  line-height: 1.6;
}

/* Cards Grid */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}
@media (max-width: 760px) {
  .cards-grid { grid-template-columns: 1fr; }
}

.info-card {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}

.card-visual {
  height: 180px;
  display: flex; align-items: center; justify-content: center;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* ---------- 经济周期 ---------- */
.visual-cycle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
}
.cycle-step {
  display: flex;
  align-items: center;
  gap: 8px;
}
.step-bubble {
  width: 42px; height: 42px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  display: flex; align-items: center; justify-content: center;
}
.step-label {
  font-size: 12px; font-weight: 700;
  color: currentColor;
}
.step-arrow {
  font-size: 16px; font-weight: 700;
  color: currentColor;
  opacity: 0.5;
}

/* ---------- 宏观基本面 ---------- */
.visual-macro {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  width: 100%;
  max-width: 260px;
}
.macro-item {
  background: rgba(255,255,255,0.85);
  border-radius: 16px;
  padding: 14px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}
.macro-bubble {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: rgba(255,255,255,0.6);
  display: flex; align-items: center; justify-content: center;
}
.macro-label {
  font-size: 11px; font-weight: 700;
  color: currentColor;
  text-align: center;
}

/* ---------- 地缘政治 ---------- */
.visual-geo {
  display: flex;
  align-items: center;
  gap: 28px;
}
.geo-globe {
  width: 88px; height: 88px;
  border-radius: 50%;
  background: rgba(255,255,255,0.85);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}
.geo-hotspots {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.hotspot {
  width: 34px; height: 34px;
  border-radius: 10px;
  background: #b91c1c;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 3px 10px rgba(0,0,0,0.12);
}
.hotspot:nth-child(2) { opacity: 0.75; }
.hotspot:nth-child(3) { opacity: 0.55; }

/* ---------- 金融市场状态 ---------- */
.visual-market {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  max-width: 260px;
}
.market-left { flex: 1.2; }
.market-right {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.market-big-card {
  background: rgba(255,255,255,0.9);
  border-radius: 18px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.06);
}
.big-card-label {
  font-size: 12px; font-weight: 700;
  color: currentColor;
}
.market-small-card {
  background: rgba(255,255,255,0.9);
  border-radius: 14px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}
.small-card-label {
  font-size: 11px; font-weight: 700;
  color: currentColor;
}

/* Card body */
.card-body { padding: 22px; }
.card-subtitle {
  font-size: 0.72rem; font-weight: 700;
  color: #a3a3a3; text-transform: uppercase;
  letter-spacing: 0.08em; margin-bottom: 8px;
}
.card-title {
  font-size: 1.15rem; font-weight: 800;
  color: #171717; margin: 0 0 10px;
  letter-spacing: -0.02em;
}
.card-desc {
  font-size: 0.85rem; color: #525252;
  line-height: 1.7; margin: 0;
}

/* CTA */
.cta-section {
  display: flex; flex-direction: column;
  align-items: center; margin-top: 8px;
}
.btn-primary {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; max-width: 420px;
  padding: 17px 24px; border: none; border-radius: 16px;
  background: #171717; color: #fff; font-family: inherit;
  font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
  cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary:hover { background: #262626; transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.18); }
</style>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  PieChart,
  Scale,
  RefreshCcw,
  UserCog,
} from '@lucide/vue'

const router = useRouter()

function closeGuide() {
  router.push('/portfolio')
}

const features = [
  {
    icon: PieChart,
    title: '分散风险',
    desc: '不要把所有鸡蛋放在一个篮子里。股票、债券、商品、现金搭配，单一资产跌的时候其他资产可能稳得住。',
  },
  {
    icon: Scale,
    title: '平衡收益',
    desc: '高收益往往伴随高风险。通过资产组合，可以在自己能承受的风险范围内，争取更稳健的回报。',
  },
  {
    icon: RefreshCcw,
    title: '动态再平衡',
    desc: '市场会变化，组合也会偏离目标。定期把比例调回目标配置，相当于“低买高卖”的纪律操作。',
  },
  {
    icon: UserCog,
    title: '匹配画像',
    desc: '你的风险偏好、投资期限和收益目标，决定了适合你的组合比例。组合应该是为你量身定制的。',
  },
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
        <div class="hero-badge">资产组合</div>
        <h1 class="hero-title">为什么要做资产组合？</h1>
        <p class="hero-desc">
          看懂市场只是第一步，把资金合理分配到不同资产中，才是投资的关键。
        </p>
      </div>

      <div class="main-visual">
        <div class="visual-left">
          <div class="pie-center">
            <PieChart :size="64" color="#4f46e5" stroke-width="1.6" />
            <span class="pie-label">资产配置</span>
          </div>
        </div>
        <div class="visual-right">
          <div class="asset-bars">
            <div class="asset-bar">
              <span class="bar-dot stock"></span>
              <span class="bar-fill"></span>
              <span class="bar-label">股票</span>
            </div>
            <div class="asset-bar">
              <span class="bar-dot bond"></span>
              <span class="bar-fill bond"></span>
              <span class="bar-label">债券</span>
            </div>
            <div class="asset-bar">
              <span class="bar-dot commodity"></span>
              <span class="bar-fill commodity"></span>
              <span class="bar-label">商品</span>
            </div>
            <div class="asset-bar">
              <span class="bar-dot cash"></span>
              <span class="bar-fill cash"></span>
              <span class="bar-label">现金</span>
            </div>
          </div>
        </div>
      </div>

      <div class="cards-grid">
        <div
          v-for="(feature, idx) in features"
          :key="feature.title"
          class="info-card"
        >
          <div class="card-icon">
            <component :is="feature.icon" :size="28" color="#4f46e5" stroke-width="2" />
          </div>
          <div class="card-body">
            <div class="card-index">0{{ idx + 1 }}</div>
            <h3 class="card-title">{{ feature.title }}</h3>
            <p class="card-desc">{{ feature.desc }}</p>
          </div>
        </div>
      </div>

      <div class="cta-section">
        <button class="btn-primary" @click="closeGuide">
          <span>明白了，开始构建组合</span>
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
  max-width: 800px; margin: 0 auto; padding: 14px 24px;
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
  max-width: 800px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 24px;
  position: relative; z-index: 1;
}

/* Hero */
.hero-section { text-align: center; padding: 20px 0 4px; }
.hero-badge {
  display: inline-block; padding: 6px 14px;
  background: #e0e7ff; color: #4338ca;
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

/* Main Visual */
.main-visual {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  border-radius: 24px;
  padding: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}
@media (max-width: 640px) {
  .main-visual { flex-direction: column; gap: 24px; }
}

.visual-left {
  display: flex; align-items: center; justify-content: center;
}
.pie-center {
  width: 130px; height: 130px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 8px 28px rgba(0,0,0,0.1);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 8px;
}
.pie-label {
  font-size: 12px; font-weight: 800;
  color: #4338ca;
}

.visual-right { min-width: 220px; }
.asset-bars {
  display: flex; flex-direction: column;
  gap: 14px;
}
.asset-bar {
  display: flex; align-items: center;
  gap: 10px;
}
.bar-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.bar-dot.stock { background: #6366f1; }
.bar-dot.bond { background: #3b82f6; }
.bar-dot.commodity { background: #f59e0b; }
.bar-dot.cash { background: #10b981; }

.bar-fill {
  height: 10px;
  border-radius: 999px;
  background: #6366f1;
  flex: 1;
  max-width: 140px;
}
.bar-fill.bond { background: #3b82f6; width: 90px; flex: none; }
.bar-fill.commodity { background: #f59e0b; width: 55px; flex: none; }
.bar-fill.cash { background: #10b981; width: 35px; flex: none; }

.bar-label {
  font-size: 12px; font-weight: 700;
  color: #374151;
  min-width: 40px;
}

/* Cards Grid */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
@media (max-width: 720px) {
  .cards-grid { grid-template-columns: 1fr; }
}

.info-card {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.03);
  display: flex;
  gap: 16px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.info-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(0,0,0,0.06);
}

.card-icon {
  width: 48px; height: 48px;
  border-radius: 14px;
  background: #eef2ff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.card-body { flex: 1; }
.card-index {
  font-size: 11px; font-weight: 800;
  color: #c7d2fe;
  margin-bottom: 4px;
}
.card-title {
  font-size: 1.05rem; font-weight: 800;
  color: #171717; margin: 0 0 6px;
  letter-spacing: -0.02em;
}
.card-desc {
  font-size: 0.82rem; color: #525252;
  line-height: 1.65; margin: 0;
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

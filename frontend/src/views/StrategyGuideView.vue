<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  Target,
  CalendarClock,
  TrendingUp,
  Landmark,
  Package,
  Banknote,
  Network,
  Dna,
  RefreshCcw,
} from '@lucide/vue'

const router = useRouter()

function closeGuide() {
  router.push('/portfolio/strategies')
}

const assets = [
  {
    icon: TrendingUp,
    name: '股票',
    strategy: '中长期趋势跟踪',
    desc: '跟随经济周期和企业盈利趋势，在复苏与繁荣期加大配置，在过热与衰退期降低 exposure。',
    color: '#6366f1',
  },
  {
    icon: Landmark,
    name: '债券',
    strategy: '利率周期与久期管理',
    desc: '利率下行时拉长久期获取资本利得，利率上行时缩短久期、提高信用资质防御。',
    color: '#3b82f6',
  },
  {
    icon: Package,
    name: '商品',
    strategy: '通胀对冲与周期配置',
    desc: '在通胀升温或供给受限时配置商品，起到分散股票债券风险、保值增值的作用。',
    color: '#f59e0b',
  },
  {
    icon: Banknote,
    name: '现金',
    strategy: '机会成本与风险控制',
    desc: '保留一定现金应对波动和突发事件，也为市场大跌时逢低买入保留弹药。',
    color: '#10b981',
  },
]

const ecosystem = [
  {
    icon: Network,
    title: '策略网络',
    desc: '不同策略像生态系统中的物种一样相互协作。股票趋势、债券套利、商品对冲等策略各司其职，组合在一起才能覆盖更多市场状态。',
  },
  {
    icon: Dna,
    title: '策略基因',
    desc: '每个策略都有自己的风格基因，比如价值、趋势、动量、均值回归。基因差异越大，策略间的互补性越强，组合越稳定。',
  },
  {
    icon: RefreshCcw,
    title: '动态进化',
    desc: '市场变化时策略会新陈代谢。系统持续监控策略健康度、寿命和近亲关系，优胜劣汰，让整个组合保持生命力。',
  },
]

const ecosystemValue = [
  {
    title: '抗单一策略失效',
    desc: '没有永远有效的策略。生态通过多策略并行，降低某个策略突然失效带来的冲击。',
  },
  {
    title: '适应不同市场环境',
    desc: '趋势策略在牛市表现好，套利策略在震荡市更稳。生态让组合在牛熊转换中都有应对手段。',
  },
  {
    title: '持续自我更新',
    desc: '通过寿命预警、健康度评分和基因多样性分析，及时发现衰老策略并引入新策略。',
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
        <div class="hero-badge">投资策略</div>
        <h1 class="hero-title">中长线策略与策略生态</h1>
        <p class="hero-desc">
          资产配置决定大方向，具体策略决定如何落地。不同资产适合不同的中长线打法。
        </p>
      </div>

      <!-- 资产策略 -->
      <section class="section">
        <div class="section-title">
          <CalendarClock :size="18" color="#6366f1" stroke-width="2.2" />
          <span>不同资产的中长线策略</span>
        </div>

        <div class="asset-grid">
          <div
            v-for="asset in assets"
            :key="asset.name"
            class="asset-card"
          >
            <div class="asset-header">
              <div class="asset-icon" :style="{ background: asset.color + '1a', color: asset.color }">
                <component :is="asset.icon" :size="24" :color="asset.color" stroke-width="2.2" />
              </div>
              <div class="asset-meta">
                <span class="asset-name">{{ asset.name }}</span>
                <span class="asset-strategy">{{ asset.strategy }}</span>
              </div>
            </div>
            <p class="asset-desc">{{ asset.desc }}</p>
          </div>
        </div>
      </section>

      <!-- 策略生态 -->
      <section class="section ecosystem-section">
        <div class="section-title">
          <Target :size="18" color="#6366f1" stroke-width="2.2" />
          <span>什么是策略生态系统？</span>
        </div>

        <p class="ecosystem-intro">
          策略生态系统把每个交易策略当成一个「生命体」：它有基因（交易逻辑）、有健康状态、有寿命周期，也会衰老和失效。单个策略很难在所有市场环境下都赚钱，但一群风格不同、优势互补的策略组合在一起，就能像自然生态一样具备更强的抗风险能力和自我更新能力。
        </p>

        <div class="ecosystem-grid">
          <div
            v-for="item in ecosystem"
            :key="item.title"
            class="ecosystem-card"
          >
            <div class="ecosystem-icon">
              <component :is="item.icon" :size="28" color="#4f46e5" stroke-width="2" />
            </div>
            <div class="ecosystem-body">
              <h3 class="ecosystem-title">{{ item.title }}</h3>
              <p class="ecosystem-desc">{{ item.desc }}</p>
            </div>
          </div>
        </div>

        <div class="value-section">
          <div class="value-title">策略生态的价值</div>
          <div class="value-grid">
            <div
              v-for="item in ecosystemValue"
              :key="item.title"
              class="value-card"
            >
              <div class="value-dot"></div>
              <div class="value-body">
                <div class="value-card-title">{{ item.title }}</div>
                <p class="value-card-desc">{{ item.desc }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="ecosystem-hint">
          <div class="hint-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4"/>
              <path d="M12 8h.01"/>
            </svg>
          </div>
          <div class="hint-body">
            <div class="hint-title">小提示</div>
            <p class="hint-desc">
              生成组合后，在组合详情页点击 <strong>「组合寿命」</strong>，即可进入 <strong>策略生态系统</strong>，查看策略健康度、寿命预警、基因多样性等完整分析。
            </p>
          </div>
        </div>
      </section>

      <div class="cta-section">
        <button class="btn-primary" @click="closeGuide">
          <span>明白了，匹配投资策略</span>
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
  max-width: 880px; margin: 0 auto; padding: 14px 24px;
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
  max-width: 880px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex;
  flex-direction: column; gap: 28px;
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

/* Section */
.section {
  background: #fff;
  border-radius: 24px;
  padding: 24px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 4px 16px rgba(0,0,0,0.03);
}
.section-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 1.05rem; font-weight: 800;
  color: #171717;
  margin-bottom: 20px;
}

/* Asset Grid */
.asset-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
@media (max-width: 720px) {
  .asset-grid { grid-template-columns: 1fr; }
}

.asset-card {
  background: #fafafa;
  border-radius: 18px;
  padding: 18px;
  border: 1px solid rgba(0,0,0,0.04);
  transition: all 0.2s ease;
}
.asset-card:hover {
  background: #fff;
  box-shadow: 0 6px 16px rgba(0,0,0,0.05);
}

.asset-header {
  display: flex; align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.asset-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.asset-meta {
  display: flex; flex-direction: column;
  gap: 2px;
}
.asset-name {
  font-size: 1rem; font-weight: 800;
  color: #171717;
}
.asset-strategy {
  font-size: 0.78rem; font-weight: 600;
  color: #6366f1;
}

.asset-desc {
  font-size: 0.82rem; color: #525252;
  line-height: 1.65; margin: 0;
}

/* Ecosystem */
.ecosystem-section {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border: none;
}
.ecosystem-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
@media (max-width: 720px) {
  .ecosystem-grid { grid-template-columns: 1fr; }
}

.ecosystem-card {
  background: rgba(255,255,255,0.9);
  border-radius: 18px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  box-shadow: 0 3px 12px rgba(0,0,0,0.04);
}
.ecosystem-icon {
  width: 48px; height: 48px;
  border-radius: 14px;
  background: #eef2ff;
  display: flex; align-items: center; justify-content: center;
}
.ecosystem-title {
  font-size: 0.95rem; font-weight: 800;
  color: #171717; margin: 0;
}
.ecosystem-desc {
  font-size: 0.78rem; color: #525252;
  line-height: 1.6; margin: 0;
}

/* Ecosystem Intro */
.ecosystem-intro {
  font-size: 0.88rem; color: #374151;
  line-height: 1.75; margin: 0 0 20px;
}

/* Value Section */
.value-section { margin-top: 24px; }
.value-title {
  font-size: 0.9rem; font-weight: 800;
  color: #171717; margin-bottom: 14px;
}
.value-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
@media (max-width: 720px) {
  .value-grid { grid-template-columns: 1fr; }
}
.value-card {
  background: rgba(255,255,255,0.85);
  border-radius: 14px;
  padding: 14px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.value-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #6366f1;
  margin-top: 6px;
  flex-shrink: 0;
}
.value-card-title {
  font-size: 0.85rem; font-weight: 800;
  color: #171717; margin-bottom: 4px;
}
.value-card-desc {
  font-size: 0.75rem; color: #525252;
  line-height: 1.55; margin: 0;
}

/* Ecosystem Hint */
.ecosystem-hint {
  margin-top: 20px;
  background: rgba(255,255,255,0.92);
  border: 1px dashed #c7d2fe;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.hint-icon {
  width: 34px; height: 34px;
  border-radius: 10px;
  background: #e0e7ff;
  color: #4f46e5;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.hint-title {
  font-size: 0.82rem; font-weight: 800;
  color: #4f46e5; margin-bottom: 4px;
}
.hint-desc {
  font-size: 0.78rem; color: #525252;
  line-height: 1.6; margin: 0;
}
.hint-desc strong {
  color: #171717; font-weight: 800;
}

/* CTA */
.cta-section {
  display: flex; flex-direction: column;
  align-items: center; margin-top: 4px;
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

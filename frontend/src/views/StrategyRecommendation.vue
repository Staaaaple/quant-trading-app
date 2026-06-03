<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Mock recommendations
const recommendations = ref([
  {
    id: 'r1',
    title: '科技ETF增强策略',
    family: '动量策略',
    reason: '当前科技行业景气度高，AI趋势持续，适合增配',
    expectedReturn: '15-20%',
    riskLevel: '中高',
    sharpe: 1.2,
    maxDrawdown: '-15%',
    match: 92,
  },
  {
    id: 'r2',
    title: '红利低波动策略',
    family: '低波动',
    reason: '防御性配置，提供稳定现金流',
    expectedReturn: '8-12%',
    riskLevel: '中低',
    sharpe: 0.9,
    maxDrawdown: '-8%',
    match: 85,
  },
  {
    id: 'r3',
    title: '商品趋势跟踪',
    family: '趋势跟踪',
    reason: '通胀预期上升，商品类资产对冲',
    expectedReturn: '10-15%',
    riskLevel: '中等',
    sharpe: 0.8,
    maxDrawdown: '-12%',
    match: 78,
  },
])

function goBack() {
  router.push('/')
}

function goPortfolio() {
  router.push('/portfolio')
}

onMounted(() => {
  // TODO: Load from API
})
</script>

<template>
  <div class="recommendation-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-label">RECOMMENDATIONS</span>
          <span class="header-name">策略推荐</span>
        </div>
        <div class="header-placeholder"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="recommendation-content">
      <div class="intro-card">
        <div class="intro-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5c0-2 2-3 4-3z"/>
            <path d="M8 13v4"/><path d="M16 13v4"/><path d="M12 15v4"/>
          </svg>
        </div>
        <div class="intro-text">
          <h2 class="intro-title">为你精选的策略</h2>
          <p class="intro-desc">基于你的画像和市场信号，AI 筛选出以下匹配度最高的策略</p>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="rec-list">
        <div v-for="rec in recommendations" :key="rec.id" class="rec-card">
          <div class="rec-header">
            <div class="rec-info">
              <div class="rec-title">{{ rec.title }}</div>
              <div class="rec-family">{{ rec.family }}</div>
            </div>
            <div class="rec-match">
              <div class="match-ring">
                <svg viewBox="0 0 40 40" class="match-svg">
                  <circle cx="20" cy="20" r="16" fill="none" stroke="#f0f0f0" stroke-width="3"/>
                  <circle cx="20" cy="20" r="16" fill="none" stroke="#171717" stroke-width="3" stroke-linecap="round"
                    :stroke-dasharray="`${rec.match / 100 * 100.5} 100.5`" stroke-dashoffset="0" transform="rotate(-90 20 20)"/>
                </svg>
                <div class="match-val">{{ rec.match }}</div>
              </div>
              <div class="match-label">匹配度</div>
            </div>
          </div>

          <div class="rec-reason">
            <span class="reason-label">推荐理由</span>
            <p class="reason-text">{{ rec.reason }}</p>
          </div>

          <div class="rec-metrics">
            <div class="metric">
              <span class="metric-label">预期收益</span>
              <span class="metric-val">{{ rec.expectedReturn }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">风险等级</span>
              <span class="metric-val">{{ rec.riskLevel }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">夏普</span>
              <span class="metric-val">{{ rec.sharpe }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">最大回撤</span>
              <span class="metric-val down">{{ rec.maxDrawdown }}</span>
            </div>
          </div>

          <button class="rec-btn" @click="goPortfolio">
            <span>加入组合</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recommendation-page {
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
.header-placeholder { width: 36px; }

/* Content */
.recommendation-content {
  max-width: 720px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

/* Intro */
.intro-card {
  display: flex; align-items: center; gap: 16px;
  padding: 20px; background: #fff;
  border-radius: 16px; border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.intro-icon {
  width: 48px; height: 48px; border-radius: 14px;
  background: #171717; color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.intro-title { font-size: 1rem; font-weight: 600; color: #171717; margin: 0 0 4px; }
.intro-desc { font-size: 0.78rem; color: #737373; margin: 0; }

/* Recommendations */
.rec-list { display: flex; flex-direction: column; gap: 12px; }
.rec-card {
  background: #fff; border-radius: 20px; padding: 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.rec-card:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.03), 0 12px 32px rgba(0,0,0,0.06);
  transform: translateY(-1px); border-color: rgba(0,0,0,0.08);
}
.rec-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.rec-title { font-size: 0.95rem; font-weight: 600; color: #171717; }
.rec-family { font-size: 0.72rem; color: #a3a3a3; margin-top: 2px; }
.rec-match { text-align: center; }
.match-ring { position: relative; width: 44px; height: 44px; }
.match-svg { width: 100%; height: 100%; }
.match-val { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 0.75rem; font-weight: 700; color: #171717; }
.match-label { font-size: 0.6rem; color: #a3a3a3; margin-top: 2px; }

.rec-reason { margin-bottom: 16px; padding: 12px 14px; background: #fafafa; border-radius: 12px; }
.reason-label { font-size: 0.65rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.08em; text-transform: uppercase; }
.reason-text { font-size: 0.82rem; color: #525252; margin: 6px 0 0; line-height: 1.5; }

.rec-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }
.metric { display: flex; flex-direction: column; gap: 2px; padding: 10px 12px; background: #fafafa; border-radius: 10px; }
.metric-label { font-size: 0.68rem; color: #a3a3a3; }
.metric-val { font-size: 0.88rem; font-weight: 600; color: #171717; }
.metric-val.down { color: #991b1b; }

.rec-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  width: 100%; padding: 14px; border: 1px solid rgba(0,0,0,0.08); border-radius: 14px;
  background: #fff; color: #171717; font-family: inherit;
  font-size: 0.85rem; font-weight: 600; cursor: pointer;
  transition: all 0.2s ease;
}
.rec-btn:hover { background: #171717; color: #fff; border-color: #171717; }

@media (min-width: 768px) {
  .recommendation-content { padding: 24px 32px 40px; }
  .rec-metrics { grid-template-columns: repeat(4, 1fr); }
}
</style>

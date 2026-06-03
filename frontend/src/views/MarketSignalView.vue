<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { marketSignalApi, type MarketSignalLatest } from '@/api/marketSignal'

const signal = ref<MarketSignalLatest | null>(null)
const loading = ref(true)
const error = ref('')

async function loadSignal() {
  loading.value = true
  error.value = ''
  try {
    signal.value = await marketSignalApi.getLatest()
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSignal()
})

function scoreColor(score: number | null): string {
  if (score === null) return '#a3a3a3'
  if (score >= 70) return '#22c55e'
  if (score >= 50) return '#d97706'
  return '#ef4444'
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
</script>

<template>
  <div class="signal-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <header class="page-header">
      <div class="page-header-inner">
        <h1 class="page-title">市场信号</h1>
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
        <div class="summary-card">
          <div class="summary-left">
            <div class="summary-label">MARKET OVERVIEW</div>
            <div class="summary-cycle">
              <span :class="['cycle-badge', cycleBadgeClass(signal.market_cycle)]">
                {{ signal.market_cycle }}
              </span>
            </div>
            <div class="summary-mood">{{ signal.market_mood }}</div>
          </div>
          <div class="summary-right">
            <div class="score-value" :style="{ color: scoreColor(signal.composite_score + 50) }">
              {{ signal.composite_score > 0 ? '+' : '' }}{{ signal.composite_score }}
            </div>
            <div class="score-label">COMPOSITE</div>
          </div>
        </div>

        <!-- Layer Cards -->
        <div class="layer-card">
          <div class="layer-header">
            <span class="layer-label">MACRO</span>
            <span class="layer-score" :style="{ color: scoreColor(signal.macro.score) }">{{ signal.macro.score }}</span>
          </div>
          <div class="layer-body">
            <div class="macro-grid">
              <div class="macro-item">
                <span class="macro-key">GDP趋势</span>
                <span class="macro-val">{{ signal.macro.gdp_trend || '-' }}</span>
              </div>
              <div class="macro-item">
                <span class="macro-key">通胀水平</span>
                <span class="macro-val">{{ signal.macro.inflation_level || '-' }}</span>
              </div>
              <div class="macro-item">
                <span class="macro-key">流动性</span>
                <span class="macro-val">{{ signal.macro.liquidity || '-' }}</span>
              </div>
              <div class="macro-item">
                <span class="macro-key">利率趋势</span>
                <span class="macro-val">{{ signal.macro.interest_rate || '-' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="layer-card">
          <div class="layer-header">
            <span class="layer-label">GEOPOLITICAL</span>
            <span class="layer-score" :style="{ color: scoreColor(signal.geo.score) }">{{ signal.geo.score }}</span>
          </div>
          <div class="layer-body">
            <div class="geo-row">
              <span class="geo-key">整体风险</span>
              <span class="geo-val">{{ signal.geo.overall_risk }} ({{ signal.geo.risk_level }})</span>
            </div>
            <div class="geo-row">
              <span class="geo-key">避险需求</span>
              <span class="geo-val">{{ signal.geo.safe_haven_demand || '-' }}</span>
            </div>
          </div>
        </div>

        <div class="layer-card">
          <div class="layer-header">
            <span class="layer-label">INDUSTRY</span>
            <span class="layer-score" :style="{ color: scoreColor(signal.industry.score) }">{{ signal.industry.score }}</span>
          </div>
          <div class="layer-body">
            <div class="industry-list">
              <div v-for="(score, name) in signal.industry.heatmap" :key="name" class="industry-item">
                <span class="industry-name">{{ name }}</span>
                <div class="industry-bar">
                  <div class="industry-fill" :style="{ width: `${score}%`, background: scoreColor(score) }"></div>
                </div>
                <span class="industry-score">{{ score }}</span>
              </div>
            </div>
            <div v-if="signal.industry.recommended?.length" class="industry-tags">
              <span v-for="s in signal.industry.recommended" :key="s" class="tag tag-green">{{ s }}</span>
            </div>
          </div>
        </div>

        <div class="layer-card">
          <div class="layer-header">
            <span class="layer-label">SOCIAL</span>
            <span class="layer-score" :style="{ color: scoreColor(signal.social.score) }">{{ signal.social.score }}</span>
          </div>
          <div class="layer-body">
            <div v-if="signal.social.major_themes?.length" class="theme-list">
              <span v-for="t in signal.social.major_themes" :key="t" class="theme-tag">{{ t }}</span>
            </div>
            <div v-else class="empty-text">暂无热点主题</div>
          </div>
        </div>

        <div class="layer-card">
          <div class="layer-header">
            <span class="layer-label">INTERNAL</span>
            <span class="layer-score" :style="{ color: scoreColor(signal.internal.score) }">{{ signal.internal.score }}</span>
          </div>
          <div class="layer-body">
            <div class="internal-grid">
              <div class="internal-item">
                <span class="internal-key">市场情绪</span>
                <span class="internal-val">{{ signal.internal.sentiment || '-' }}</span>
              </div>
              <div class="internal-item">
                <span class="internal-key">股债利差</span>
                <span class="internal-val">{{ signal.internal.equity_bond_spread?.toFixed(2) || '-' }}%</span>
              </div>
              <div class="internal-item">
                <span class="internal-key">风格轮动</span>
                <span class="internal-val">{{ signal.internal.style_rotation || '-' }}</span>
              </div>
              <div class="internal-item">
                <span class="internal-key">波动率</span>
                <span class="internal-val">{{ signal.internal.volatility_regime || '-' }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
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
  width: 100%; display: flex; flex-direction: column; gap: 14px;
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

.score-value {
  font-size: 2.2rem; font-weight: 800;
  line-height: 1; letter-spacing: -0.03em;
}
.score-label {
  font-size: 0.58rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.12em; text-transform: uppercase;
  text-align: right; margin-top: 4px;
}

/* Layer Cards */
.layer-card {
  background: #fff; border-radius: 16px; padding: 20px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.2s ease;
}
.layer-card:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  border-color: rgba(0,0,0,0.08);
}
.layer-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.layer-label {
  font-size: 0.62rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.1em; text-transform: uppercase;
}
.layer-score {
  font-size: 1.1rem; font-weight: 700; letter-spacing: -0.02em;
}

/* Macro */
.macro-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.macro-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 10px 12px; background: #fafafa; border-radius: 10px;
}
.macro-key { font-size: 0.72rem; color: #a3a3a3; }
.macro-val { font-size: 0.9rem; font-weight: 600; color: #171717; }

/* Geo */
.geo-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid rgba(0,0,0,0.04);
}
.geo-row:last-child { border-bottom: none; }
.geo-key { font-size: 0.82rem; color: #525252; }
.geo-val { font-size: 0.82rem; font-weight: 600; color: #171717; }

/* Industry */
.industry-list { display: flex; flex-direction: column; gap: 8px; }
.industry-item {
  display: flex; align-items: center; gap: 10px;
}
.industry-name { font-size: 0.8rem; color: #525252; width: 50px; flex-shrink: 0; }
.industry-bar {
  flex: 1; height: 5px; background: #f0f0f0; border-radius: 999px; overflow: hidden;
}
.industry-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
.industry-score { font-size: 0.75rem; font-weight: 600; color: #171717; width: 28px; text-align: right; }
.industry-tags { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.tag {
  font-size: 0.72rem; font-weight: 500; padding: 5px 11px;
  border-radius: 8px; background: #f5f5f5; color: #525252;
  border: 1px solid rgba(0,0,0,0.04);
}
.tag-green {
  background: #f0fdf4; color: #166534; border-color: rgba(34,197,94,0.12);
}

/* Social */
.theme-list { display: flex; gap: 8px; flex-wrap: wrap; }
.theme-tag {
  font-size: 0.78rem; font-weight: 500;
  padding: 8px 14px; background: #171717; color: #fff;
  border-radius: 10px;
}
.empty-text { font-size: 0.82rem; color: #a3a3a3; text-align: center; padding: 12px 0; }

/* Internal */
.internal-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.internal-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 10px 12px; background: #fafafa; border-radius: 10px;
}
.internal-key { font-size: 0.72rem; color: #a3a3a3; }
.internal-val { font-size: 0.9rem; font-weight: 600; color: #171717; }

@media (min-width: 768px) {
  .signal-content { padding: 24px 32px 40px; }
}
</style>

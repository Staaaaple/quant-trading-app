<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Mock data - will be replaced with API call
const strategies = ref([
  { id: 's1', name: '沪深300ETF低波动动量', family: '动量策略', lifespan: 18, health: 85, status: 'healthy' },
  { id: 's2', name: '中证500机器学习多因子', family: '多因子', lifespan: 12, health: 72, status: 'healthy' },
  { id: 's3', name: '黄金ETF趋势跟踪', family: '趋势跟踪', lifespan: 2, health: 45, status: 'warning' },
  { id: 's4', name: '国债ETF利率趋势', family: '利率策略', lifespan: 24, health: 90, status: 'healthy' },
  { id: 's5', name: '可转债ETF低波动筛选', family: '低波动', lifespan: 20, health: 78, status: 'healthy' },
])

const alerts = ref([
  { type: 'warning', message: '黄金ETF策略寿命仅剩2个月', action: '查看替代' },
])

function goBack() {
  router.push('/portfolio/strategies')
}

function getLifespanColor(months: number): string {
  if (months >= 12) return '#22c55e'
  if (months >= 6) return '#d97706'
  return '#ef4444'
}

function getHealthColor(score: number): string {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#d97706'
  return '#ef4444'
}

function getStatusClass(status: string): string {
  const map: Record<string, string> = {
    'healthy': 'status-healthy',
    'warning': 'status-warning',
    'critical': 'status-critical',
  }
  return map[status] || 'status-healthy'
}

onMounted(() => {
  // TODO: Load from API
})
</script>

<template>
  <div class="lifespan-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-label">LIFESPAN MONITOR</span>
          <span class="header-name">寿命监控</span>
        </div>
        <div class="header-placeholder"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="lifespan-content">
      <!-- Alerts -->
      <div v-for="(alert, idx) in alerts" :key="idx" class="alert-box">
        <span class="alert-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
        </span>
        <span class="alert-txt">{{ alert.message }}</span>
        <span class="alert-link">{{ alert.action }}</span>
      </div>

      <!-- Strategy List -->
      <div class="section-title">
        <span class="section-label">STRATEGIES</span>
        <span class="section-count">{{ strategies.length }} 个策略</span>
      </div>

      <div class="strategy-list">
        <div v-for="s in strategies" :key="s.id" class="strategy-card">
          <div class="strategy-header">
            <div class="strategy-info">
              <div class="strategy-name">{{ s.name }}</div>
              <div class="strategy-family">{{ s.family }}</div>
            </div>
            <span :class="['status-badge', getStatusClass(s.status)]">
              {{ s.status === 'healthy' ? '健康' : s.status === 'warning' ? '预警' : '危急' }}
            </span>
          </div>

          <div class="strategy-metrics">
            <div class="metric">
              <div class="metric-label">剩余寿命</div>
              <div class="metric-bar">
                <div class="metric-fill" :style="{ width: `${Math.min(s.lifespan / 24 * 100, 100)}%`, background: getLifespanColor(s.lifespan) }"></div>
              </div>
              <div class="metric-val" :style="{ color: getLifespanColor(s.lifespan) }">{{ s.lifespan }}月</div>
            </div>
            <div class="metric">
              <div class="metric-label">健康度</div>
              <div class="metric-bar">
                <div class="metric-fill" :style="{ width: `${s.health}%`, background: getHealthColor(s.health) }"></div>
              </div>
              <div class="metric-val" :style="{ color: getHealthColor(s.health) }">{{ s.health }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="legend-bar">
        <div class="legend-item">
          <span class="legend-dot" style="background:#22c55e"></span>
          <span>健康 (≥12月)</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background:#d97706"></span>
          <span>预警 (6-12月)</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background:#ef4444"></span>
          <span>危急 (<6月)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lifespan-page {
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
.lifespan-content {
  max-width: 720px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

/* Alert */
.alert-box {
  display: flex; align-items: center; gap: 9px;
  padding: 13px 15px;
  background: linear-gradient(90deg, #fafafa, #f5f5f5);
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.04);
  position: relative; overflow: hidden;
}
.alert-box::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: #ef4444; border-radius: 12px 0 0 12px;
}
.alert-icon { color: #ef4444; display: flex; align-items: center; margin-left: 6px; }
.alert-txt { font-size: 0.8rem; color: #525252; flex: 1; font-weight: 500; }
.alert-link {
  font-size: 0.75rem; font-weight: 600; color: #171717;
  cursor: pointer; white-space: nowrap; letter-spacing: -0.01em;
  padding: 3px 8px; border-radius: 6px; background: rgba(0,0,0,0.03);
  transition: background 0.2s;
}
.alert-link:hover { background: rgba(0,0,0,0.06); }

/* Section */
.section-title { display: flex; align-items: center; justify-content: space-between; padding: 4px 4px 0; }
.section-label { font-size: 0.62rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.section-count { font-size: 0.75rem; color: #a3a3a3; }

/* Strategy Cards */
.strategy-list { display: flex; flex-direction: column; gap: 10px; }
.strategy-card {
  background: #fff; border-radius: 16px; padding: 18px 20px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  transition: all 0.2s ease;
}
.strategy-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.04); border-color: rgba(0,0,0,0.08); }
.strategy-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.strategy-name { font-size: 0.9rem; font-weight: 600; color: #171717; }
.strategy-family { font-size: 0.72rem; color: #a3a3a3; margin-top: 2px; }
.status-badge {
  font-size: 0.7rem; font-weight: 600; padding: 4px 10px;
  border-radius: 6px;
}
.status-healthy { background: #f0fdf4; color: #166534; }
.status-warning { background: #fffbeb; color: #92400e; }
.status-critical { background: #fef2f2; color: #991b1b; }

/* Metrics */
.strategy-metrics { display: flex; flex-direction: column; gap: 10px; }
.metric { display: flex; align-items: center; gap: 10px; }
.metric-label { font-size: 0.72rem; color: #a3a3a3; width: 60px; flex-shrink: 0; }
.metric-bar { flex: 1; height: 5px; background: #f0f0f0; border-radius: 999px; overflow: hidden; }
.metric-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
.metric-val { font-size: 0.82rem; font-weight: 600; min-width: 40px; text-align: right; }

/* Legend */
.legend-bar {
  display: flex; justify-content: center; gap: 20px;
  padding: 14px; background: #fff;
  border-radius: 12px; border: 1px solid rgba(0,0,0,0.05);
}
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: #737373; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }

@media (min-width: 768px) {
  .lifespan-content { padding: 24px 32px 40px; }
}
</style>

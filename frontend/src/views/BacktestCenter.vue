<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { backtestApi, type Backtest } from '@/api/backtest'

const router = useRouter()
const backtests = ref<Backtest[]>([])
const loading = ref(true)

async function loadBacktests() {
  loading.value = true
  try {
    backtests.value = await backtestApi.list()
  } catch (e) {
    console.error('Failed to load backtests:', e)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/')
}

function goDetail(id: string) {
  router.push(`/backtests/${id}`)
}

function statusClass(status: string): string {
  const map: Record<string, string> = {
    'success': 'status-success',
    'failed': 'status-failed',
    'running': 'status-running',
    'pending': 'status-pending',
  }
  return map[status] || 'status-pending'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    'success': '成功',
    'failed': '失败',
    'running': '运行中',
    'pending': '等待中',
  }
  return map[status] || status
}

onMounted(() => {
  loadBacktests()
})
</script>

<template>
  <div class="backtest-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-label">BACKTEST CENTER</span>
          <span class="header-name">回测中心</span>
        </div>
        <div class="header-placeholder"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="backtest-content">
      <div v-if="loading" class="loading-state">加载回测记录...</div>

      <template v-else>
        <!-- Stats -->
        <div class="stats-bar">
          <div class="stat-pill">
            <span class="stat-num">{{ backtests.length }}</span>
            <span class="stat-label">总回测</span>
          </div>
          <div class="stat-pill">
            <span class="stat-num">{{ backtests.filter(b => b.status === 'success').length }}</span>
            <span class="stat-label">成功</span>
          </div>
          <div class="stat-pill">
            <span class="stat-num">{{ backtests.filter(b => b.status === 'running').length }}</span>
            <span class="stat-label">运行中</span>
          </div>
        </div>

        <!-- List -->
        <div class="backtest-list">
          <div
            v-for="bt in backtests"
            :key="bt.id"
            class="backtest-card"
            @click="goDetail(bt.backtest_id)"
          >
            <div class="backtest-header">
              <div class="backtest-info">
                <div class="backtest-id">{{ bt.backtest_id }}</div>
                <div class="backtest-strategy">{{ bt.strategy_id }}</div>
              </div>
              <span :class="['status-badge', statusClass(bt.status)]">
                {{ statusLabel(bt.status) }}
              </span>
            </div>
            <div class="backtest-meta">
              <span>{{ bt.start_date }} ~ {{ bt.end_date }}</span>
              <span>初始资金 ¥{{ bt.initial_cash.toLocaleString() }}</span>
            </div>
            <div v-if="bt.metrics" class="backtest-metrics">
              <div class="metric">
                <span class="metric-label">总收益</span>
                <span class="metric-val" :class="bt.metrics.total_return >= 0 ? 'up' : 'down'">
                  {{ bt.metrics.total_return >= 0 ? '+' : '' }}{{ (bt.metrics.total_return * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="metric">
                <span class="metric-label">夏普</span>
                <span class="metric-val">{{ bt.metrics.sharpe_ratio?.toFixed(2) || '—' }}</span>
              </div>
              <div class="metric">
                <span class="metric-label">最大回撤</span>
                <span class="metric-val down">{{ (bt.metrics.max_drawdown * 100).toFixed(2) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="backtests.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2"/>
              <path d="M3 9h18"/>
              <path d="M9 21V9"/>
            </svg>
          </div>
          <p class="empty-text">暂无回测记录</p>
          <p class="empty-sub">在组合页面点击"回测验证"开始你的第一次回测</p>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.backtest-page {
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
.backtest-content {
  max-width: 720px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}
.loading-state { text-align: center; padding: 60px 0; color: #a3a3a3; font-size: 0.9rem; }

/* Stats */
.stats-bar { display: flex; gap: 10px; }
.stat-pill {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  padding: 14px; background: #fff;
  border-radius: 16px; border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.stat-num { font-size: 1.3rem; font-weight: 700; color: #171717; }
.stat-label { font-size: 0.72rem; color: #a3a3a3; margin-top: 4px; }

/* Cards */
.backtest-list { display: flex; flex-direction: column; gap: 10px; }
.backtest-card {
  background: #fff; border-radius: 16px; padding: 18px 20px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  transition: all 0.2s ease; cursor: pointer;
}
.backtest-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border-color: rgba(0,0,0,0.08);
  transform: translateY(-1px);
}
.backtest-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.backtest-id { font-size: 0.88rem; font-weight: 600; color: #171717; }
.backtest-strategy { font-size: 0.72rem; color: #a3a3a3; margin-top: 2px; }
.status-badge {
  font-size: 0.7rem; font-weight: 600; padding: 4px 10px;
  border-radius: 6px;
}
.status-success { background: #f0fdf4; color: #166534; }
.status-failed { background: #fef2f2; color: #991b1b; }
.status-running { background: #eff6ff; color: #1e40af; }
.status-pending { background: #f5f5f5; color: #525252; }
.backtest-meta {
  display: flex; gap: 16px;
  font-size: 0.75rem; color: #a3a3a3;
  margin-bottom: 12px;
}
.backtest-metrics { display: flex; gap: 20px; }
.metric { display: flex; flex-direction: column; gap: 2px; }
.metric-label { font-size: 0.68rem; color: #a3a3a3; }
.metric-val { font-size: 0.9rem; font-weight: 600; color: #171717; }
.metric-val.up { color: #166534; }
.metric-val.down { color: #991b1b; }

/* Empty */
.empty-state { text-align: center; padding: 60px 0; }
.empty-icon { color: #e5e5e5; margin-bottom: 16px; }
.empty-text { font-size: 0.9rem; font-weight: 600; color: #525252; margin: 0 0 6px; }
.empty-sub { font-size: 0.78rem; color: #a3a3a3; margin: 0; }

@media (min-width: 768px) {
  .backtest-content { padding: 24px 32px 40px; }
}
</style>

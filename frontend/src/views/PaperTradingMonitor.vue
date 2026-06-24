<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { paperTradingApi, type PaperTradingDailyRecord, type PaperTradingMonthlyStat } from '@/api/paperTrading'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, TitleComponent])

const router = useRouter()
const loading = ref(false)
const toast = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

const dailyRecords = ref<PaperTradingDailyRecord[]>([])
const monthlyStats = ref<PaperTradingMonthlyStat[]>([])
const latestRecord = ref<PaperTradingDailyRecord | null>(null)

const chartOption = computed(() => {
  const dates = dailyRecords.value.map(r => r.record_date)
  const values = dailyRecords.value.map(r => r.cumulative_return * 100)
  const lastValue = values.length ? values[values.length - 1] : 0
  const color = (lastValue ?? 0) >= 0 ? '#16a34a' : '#dc2626'
  return {
    title: { text: '累计收益率', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}<br/>累计收益: ${p[0].value.toFixed(2)}%` },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color, width: 2 },
      areaStyle: { color: `${color}20` },
    }],
  }
})

const summary = computed(() => {
  const latest = latestRecord.value
  const first = dailyRecords.value[0]
  return {
    totalDays: dailyRecords.value.length,
    cumulativeReturnPct: latest ? latest.cumulative_return * 100 : 0,
    latestDailyReturnPct: latest ? latest.daily_return * 100 : 0,
    nav: latest ? latest.nav : 1.0,
    startDate: first ? first.record_date : '-',
    endDate: latest ? latest.record_date : '-',
  }
})

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}

function goBack() {
  router.push('/')
}

async function loadData() {
  loading.value = true
  try {
    const [daily, monthly, latest] = await Promise.all([
      paperTradingApi.listDailyRecords({ limit: 365 }),
      paperTradingApi.listMonthlyStats({ limit: 24 }),
      paperTradingApi.getLatest(),
    ])
    dailyRecords.value = daily
    monthlyStats.value = monthly
    latestRecord.value = latest
  } catch (e: any) {
    showToast('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function syncDaily() {
  loading.value = true
  try {
    await paperTradingApi.syncDaily()
    showToast('同步成功')
    await loadData()
  } catch (e: any) {
    showToast('同步失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function calcMonthly() {
  loading.value = true
  try {
    await paperTradingApi.calcMonthly()
    showToast('月度统计完成')
    await loadData()
  } catch (e: any) {
    showToast('月度统计失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function fmtPct(n: number) {
  const sign = n >= 0 ? '+' : ''
  return `${sign}${n.toFixed(2)}%`
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <div class="header-title">
          <span class="header-label">PAPER TRADING</span>
          <span class="header-name">模拟盘统计</span>
        </div>
        <div class="header-placeholder"></div>
      </div>
    </header>

    <div class="page-content">
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-value" :style="{ color: summary.cumulativeReturnPct >= 0 ? '#16a34a' : '#dc2626' }">
            {{ fmtPct(summary.cumulativeReturnPct) }}
          </div>
          <div class="summary-label">累计收益率</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ summary.nav.toFixed(4) }}</div>
          <div class="summary-label">净值</div>
        </div>
        <div class="summary-card">
          <div class="summary-value" :style="{ color: summary.latestDailyReturnPct >= 0 ? '#16a34a' : '#dc2626' }">
            {{ fmtPct(summary.latestDailyReturnPct) }}
          </div>
          <div class="summary-label">最新日收益</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ summary.totalDays }}</div>
          <div class="summary-label">统计天数</div>
        </div>
      </div>

      <div v-if="toast" class="toast">{{ toast }}</div>

      <div class="card chart-card">
        <div class="chart-actions">
          <button class="btn btn--secondary btn--sm" :disabled="loading" @click="syncDaily">同步今日</button>
          <button class="btn btn--ghost btn--sm" :disabled="loading" @click="calcMonthly">月度统计</button>
        </div>
        <VChart v-if="dailyRecords.length" class="chart" :option="chartOption" autoresize />
        <div v-else class="empty-state">暂无模拟盘数据，点击「同步今日」开始统计</div>
      </div>

      <div class="card table-card">
        <h3 class="section-title">月度收益率</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>月份</th>
              <th>月度收益率</th>
              <th>月末累计收益</th>
              <th>有效记录数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in monthlyStats" :key="m.year_month">
              <td>{{ m.year_month }}</td>
              <td :class="m.monthly_return >= 0 ? 'text-profit' : 'text-loss'">
                {{ fmtPct(m.monthly_return * 100) }}
              </td>
              <td :class="m.cumulative_return_at_month_end >= 0 ? 'text-profit' : 'text-loss'">
                {{ fmtPct(m.cumulative_return_at_month_end * 100) }}
              </td>
              <td>{{ m.record_count }}</td>
            </tr>
            <tr v-if="!monthlyStats.length">
              <td colspan="4" class="empty-cell">暂无月度统计</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card table-card">
        <h3 class="section-title">每日记录</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>日收益率</th>
              <th>累计收益率</th>
              <th>净值</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in dailyRecords.slice().reverse()" :key="r.record_date">
              <td>{{ r.record_date }}</td>
              <td :class="r.daily_return >= 0 ? 'text-profit' : 'text-loss'">
                {{ fmtPct(r.daily_return * 100) }}
              </td>
              <td :class="r.cumulative_return >= 0 ? 'text-profit' : 'text-loss'">
                {{ fmtPct(r.cumulative_return * 100) }}
              </td>
              <td>{{ r.nav.toFixed(4) }}</td>
            </tr>
            <tr v-if="!dailyRecords.length">
              <td colspan="4" class="empty-cell">暂无每日记录</td>
            </tr>
          </tbody>
        </table>
      </div>

      <LoadingOverlay :visible="loading" text="加载中..." />
    </div>
  </div>
</template>

<style scoped>
.page {
  --bg-base: #fafafa;
  --bg-surface: #ffffff;
  --border-subtle: rgba(0,0,0,0.05);
  --text-primary: #171717;
  --text-secondary: #525252;
  --text-muted: #a3a3a3;
  --accent: #6366f1;
  --success: #22c55e;
  --error: #ef4444;

  min-height: 100vh;
  background: var(--bg-base);
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

.page-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.85);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.page-header-inner {
  max-width: 960px; margin: 0 auto; padding: 12px 24px;
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

.page-content {
  max-width: 960px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

.summary-grid {
  display: flex; gap: 10px;
}
.summary-card {
  flex: 1;
  display: flex; flex-direction: column; align-items: center;
  padding: 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.summary-label {
  font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;
}
.summary-value {
  font-size: 1.3rem; font-weight: 700; color: var(--text-primary);
}

.toast {
  padding: 12px 14px;
  background: #f0fdf4;
  color: #166534;
  font-size: 0.85rem; font-weight: 600;
  border-radius: 12px;
  border: 1px solid rgba(34,197,94,0.15);
}

.card {
  background: var(--bg-surface);
  border-radius: 20px;
  border: 1px solid var(--border-subtle);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  padding: 22px;
}

.chart-card { position: relative; }
.chart-actions {
  position: absolute; top: 18px; right: 18px;
  display: flex; gap: 8px; z-index: 2;
}
.chart { width: 100%; height: 320px; }
.empty-state {
  height: 320px; display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); font-size: 0.9rem;
}

.section-title {
  font-size: 1rem; font-weight: 700; color: var(--text-primary);
  margin-bottom: 14px;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.9rem;
}
.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}
.data-table th {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.8rem;
}
.data-table tbody tr:last-child td { border-bottom: none; }
.empty-cell {
  text-align: center;
  color: var(--text-muted);
  padding: 32px;
}

.btn--secondary {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 14px;
  background: #fff; color: #525252;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 12px;
  font-size: 0.78rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
}
.btn--secondary:hover:not(:disabled) { border-color: rgba(0,0,0,0.12); color: #171717; }
.btn--ghost {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 14px;
  background: transparent; color: #737373;
  border: none; border-radius: 12px;
  font-size: 0.78rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
}
.btn--ghost:hover:not(:disabled) { background: #f5f5f5; color: #171717; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.text-profit { color: #16a34a; }
.text-loss { color: #dc2626; }

@media (min-width: 768px) {
  .page-content { padding: 24px 32px 40px; }
}
@media (max-width: 640px) {
  .summary-grid { flex-wrap: wrap; }
  .summary-card { min-width: calc(50% - 5px); }
  .chart-actions { position: static; margin-bottom: 12px; justify-content: flex-end; }
}
</style>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface ABTest {
  id: number
  name: string
  description: string | null
  hypothesis: string | null
  target_metric: string
  variant_a_name: string
  variant_b_name: string
  status: string
  start_date: string | null
  end_date: string | null
  target_sample_size: number
  current_sample_a: number
  current_sample_b: number
  significance_level: number
}

interface TestStats {
  test_id: number
  test_name: string
  target_metric: string
  variant_a: { count: number; mean: number; std: number; min: number; max: number } | null
  variant_b: { count: number; mean: number; std: number; min: number; max: number } | null
  p_value: number | null
  significant: boolean
  winner: string
  status: string
}

const tests = ref<ABTest[]>([])
const currentStats = ref<TestStats | null>(null)
const loading = ref(true)
const error = ref('')

async function loadTests() {
  loading.value = true
  error.value = ''
  try {
    const resp = await fetch('/api/v1/ab-tests')
    if (resp.ok) {
      tests.value = await resp.json()
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadStats(testId: number) {
  currentStats.value = null
  try {
    const resp = await fetch(`/api/v1/ab-tests/${testId}/statistics`)
    if (resp.ok) {
      currentStats.value = await resp.json()
    }
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

onMounted(loadTests)

function statusLabel(s: string) {
  const map: Record<string, string> = {
    draft: '草稿', running: '运行中', paused: '已暂停',
    completed: '已完成', archived: '已归档',
  }
  return map[s] || s
}

function statusColor(s: string) {
  const map: Record<string, string> = {
    draft: '#737373', running: '#22c55e', paused: '#d97706',
    completed: '#3b82f6', archived: '#a3a3a3',
  }
  return map[s] || '#737373'
}

function metricLabel(m: string) {
  const map: Record<string, string> = {
    return: '收益率', sharpe: '夏普比率', max_drawdown: '最大回撤',
    user_satisfaction: '用户满意度', conversion: '转化率',
  }
  return map[m] || m
}

function winnerLabel(w: string) {
  const map: Record<string, string> = {
    A: '变体A胜出', B: '变体B胜出', tie: '平局',
    inconclusive: '结果不确定',
  }
  return map[w] || w
}

function winnerColor(w: string) {
  const map: Record<string, string> = {
    A: '#3b82f6', B: '#8b5cf6', tie: '#d97706',
    inconclusive: '#737373',
  }
  return map[w] || '#737373'
}

const demoTests: ABTest[] = [
  {
    id: 1,
    name: '动量 vs 均值回归策略推荐',
    description: '对比两种策略模板在相同市场环境下的推荐效果',
    hypothesis: '动量策略在牛市中推荐转化率高于均值回归策略',
    target_metric: 'return',
    variant_a_name: '动量策略推荐',
    variant_b_name: '均值回归策略推荐',
    status: 'running',
    start_date: '2026-06-01T00:00:00',
    end_date: null,
    target_sample_size: 200,
    current_sample_a: 87,
    current_sample_b: 93,
    significance_level: 0.05,
  },
  {
    id: 2,
    name: '激进 vs 保守SAA配置',
    description: '对比两种资产配置方案的长期收益表现',
    hypothesis: '激进型配置（股票70%）的长期收益显著高于保守型（股票50%）',
    target_metric: 'sharpe',
    variant_a_name: '激进配置 (70%股票)',
    variant_b_name: '保守配置 (50%股票)',
    status: 'completed',
    start_date: '2026-01-01T00:00:00',
    end_date: '2026-05-31T00:00:00',
    target_sample_size: 150,
    current_sample_a: 150,
    current_sample_b: 150,
    significance_level: 0.05,
  },
  {
    id: 3,
    name: '科技行业权重 25% vs 15%',
    description: '测试不同科技行业配置比例的效果',
    hypothesis: '科技行业25%配置的收益风险比优于15%',
    target_metric: 'return',
    variant_a_name: '科技25%',
    variant_b_name: '科技15%',
    status: 'draft',
    start_date: null,
    end_date: null,
    target_sample_size: 100,
    current_sample_a: 0,
    current_sample_b: 0,
    significance_level: 0.05,
  },
]

const demoStats: Record<number, TestStats> = {
  1: {
    test_id: 1,
    test_name: '动量 vs 均值回归策略推荐',
    target_metric: 'return',
    variant_a: { count: 87, mean: 0.0856, std: 0.0321, min: 0.0213, max: 0.1523 },
    variant_b: { count: 93, mean: 0.0623, std: 0.0289, min: 0.0156, max: 0.1187 },
    p_value: 0.0234,
    significant: true,
    winner: 'A',
    status: 'running',
  },
  2: {
    test_id: 2,
    test_name: '激进 vs 保守SAA配置',
    target_metric: 'sharpe',
    variant_a: { count: 150, mean: 1.234, std: 0.456, min: 0.321, max: 2.156 },
    variant_b: { count: 150, mean: 1.187, std: 0.398, min: 0.287, max: 1.987 },
    p_value: 0.1876,
    significant: false,
    winner: 'inconclusive',
    status: 'completed',
  },
}

function selectTest(test: ABTest) {
  // 优先使用演示数据
  if (demoStats[test.id]) {
    currentStats.value = demoStats[test.id]
    return
  }
  loadStats(test.id)
}
</script>

<template>
  <div class="ab-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <div class="header-title">
          <span class="header-label">A/B TESTING</span>
          <span class="header-name">策略对比实验</span>
        </div>
      </div>
    </header>

    <!-- Content -->
    <div class="ab-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>

      <template v-else>
        <!-- Test List -->
        <div class="section-title">
          <span class="section-label">EXPERIMENTS</span>
          <span class="section-name">实验列表</span>
        </div>

        <div class="test-list">
          <div
            v-for="test in demoTests"
            :key="test.id"
            class="test-card"
            :class="{ active: currentStats?.test_id === test.id }"
            @click="selectTest(test)"
          >
            <div class="test-header">
              <div class="test-name">{{ test.name }}</div>
              <span class="test-status" :style="{ color: statusColor(test.status), background: statusColor(test.status) + '12' }"
                @click="selectTest(test)"
              >
                {{ statusLabel(test.status) }}
              </span>
            </div>
            <div class="test-desc">{{ test.description }}</div>
            <div class="test-meta">
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  @click="selectTest(test)"
                >
                  <path d="M12 20v-6M6 20V10M18 20V4"/>
                </svg>
                {{ metricLabel(test.target_metric) }}
              </span>
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  @click="selectTest(test)"
                >
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                {{ test.current_sample_a + test.current_sample_b }} / {{ test.target_sample_size }}
              </span>
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  @click="selectTest(test)"
                >
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                <span v-if="test.start_date"
                  @click="selectTest(test)"
                >
                  {{ new Date(test.start_date).toLocaleDateString() }}
                  {{ test.end_date ? ' - ' + new Date(test.end_date).toLocaleDateString() : ' 至今' }}
                </span>
                <span v-else
                  @click="selectTest(test)"
                >未开始</span>
              </span>
            </div>

            <!-- Progress bar -->
            <div class="test-progress"
              @click="selectTest(test)"
            >
              <div class="progress-track"
                @click="selectTest(test)"
              >
                <div
                  class="progress-fill-a"
                  :style="{ width: `${(test.current_sample_a / test.target_sample_size) * 100}%` }"
                  @click="selectTest(test)"
                ></div>
                <div
                  class="progress-fill-b"
                  :style="{ width: `${(test.current_sample_b / test.target_sample_size) * 100}%`, left: `${(test.current_sample_a / test.target_sample_size) * 100}%` }"
                  @click="selectTest(test)"
                ></div>
              </div>
              <div class="progress-labels"
                @click="selectTest(test)"
              >
                <span style="color:#3b82f6"
                  @click="selectTest(test)"
                >A: {{ test.current_sample_a }}</span>
                <span style="color:#8b5cf6"
                  @click="selectTest(test)"
                >B: {{ test.current_sample_b }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats Detail -->
        <div v-if="currentStats" class="stats-section"
          @click="selectTest(test)"
        >
          <div class="section-title"
            @click="selectTest(test)"
          >
            <span class="section-label"
              @click="selectTest(test)"
            >RESULTS</span>
            <span class="section-name"
              @click="selectTest(test)"
            >实验结果</span>
          </div>

          <div class="stats-card"
            @click="selectTest(test)"
          >
            <!-- Winner banner -->
            <div v-if="currentStats.significant" class="winner-banner" :style="{ background: winnerColor(currentStats.winner) + '12' }"
              @click="selectTest(test)"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" :stroke="winnerColor(currentStats.winner)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                @click="selectTest(test)"
              >
                <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
                <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
                <path d="M4 22h16"/>
                <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/>
                <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>
                <circle cx="12" cy="9" r="5"/>
              </svg>
              <span :style="{ color: winnerColor(currentStats.winner) }"
                @click="selectTest(test)"
              >{{ winnerLabel(currentStats.winner) }}</span>
              <span class="p-value" v-if="currentStats.p_value"
                @click="selectTest(test)"
              >p = {{ currentStats.p_value }} < {{ demoTests.find(t => t.id === currentStats.test_id)?.significance_level || 0.05 }}</span>
            </div>
            <div v-else-if="currentStats.winner === 'inconclusive'" class="winner-banner" style="background:#f5f5f5"
              @click="selectTest(test)"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#737373" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                @click="selectTest(test)"
              >
                <circle cx="12" cy="12" r="10"/>
                <path d="M8 15h8"/>
                <path d="M9 9h.01"/>
                <path d="M15 9h.01"/>
              </svg>
              <span style="color:#737373"
                @click="selectTest(test)"
              >结果未达到统计显著性</span>
              <span class="p-value" v-if="currentStats.p_value"
                @click="selectTest(test)"
              >p = {{ currentStats.p_value }} >= {{ demoTests.find(t => t.id === currentStats.test_id)?.significance_level || 0.05 }}</span>
            </div>

            <!-- Comparison table -->
            <div class="comparison-table"
              @click="selectTest(test)"
            >
              <div class="table-header"
                @click="selectTest(test)"
              >
                <div class="th"
                  @click="selectTest(test)"
                >指标</div>
                <div class="th variant-a"
                  @click="selectTest(test)"
                >
                  <span class="variant-dot" style="background:#3b82f6"
                    @click="selectTest(test)"
                  ></span>
                  {{ demoTests.find(t => t.id === currentStats.test_id)?.variant_a_name || '变体A' }}
                </div>
                <div class="th variant-b"
                  @click="selectTest(test)"
                >
                  <span class="variant-dot" style="background:#8b5cf6"
                    @click="selectTest(test)"
                  ></span>
                  {{ demoTests.find(t => t.id === currentStats.test_id)?.variant_b_name || '变体B' }}
                </div>
              </div>
              <div class="table-row"
                @click="selectTest(test)"
              >
                <div class="td label"
                  @click="selectTest(test)"
                >样本量</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_a?.count || 0 }}</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_b?.count || 0 }}</div>
              </div>
              <div class="table-row highlight"
                @click="selectTest(test)"
              >
                <div class="td label"
                  @click="selectTest(test)"
                >平均值</div>
                <div class="td" :class="{ winner: currentStats.winner === 'A' }"
                  @click="selectTest(test)"
                >{{ currentStats.variant_a?.mean?.toFixed(4) || '-' }}</div>
                <div class="td" :class="{ winner: currentStats.winner === 'B' }"
                  @click="selectTest(test)"
                >{{ currentStats.variant_b?.mean?.toFixed(4) || '-' }}</div>
              </div>
              <div class="table-row"
                @click="selectTest(test)"
              >
                <div class="td label"
                  @click="selectTest(test)"
                >标准差</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_a?.std?.toFixed(4) || '-' }}</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_b?.std?.toFixed(4) || '-' }}</div>
              </div>
              <div class="table-row"
                @click="selectTest(test)"
              >
                <div class="td label"
                  @click="selectTest(test)"
                >最小值</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_a?.min?.toFixed(4) || '-' }}</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_b?.min?.toFixed(4) || '-' }}</div>
              </div>
              <div class="table-row"
                @click="selectTest(test)"
              >
                <div class="td label"
                  @click="selectTest(test)"
                >最大值</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_a?.max?.toFixed(4) || '-' }}</div>
                <div class="td"
                  @click="selectTest(test)"
                >{{ currentStats.variant_b?.max?.toFixed(4) || '-' }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.ab-page {
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
  max-width: 800px; margin: 0 auto; padding: 12px 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.header-title { display: flex; flex-direction: column; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }

/* Content */
.ab-content {
  max-width: 800px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

.loading-state {
  text-align: center; padding: 60px 20px; color: #a3a3a3;
  display: flex; align-items: center; justify-content: center; gap: 10px;
}
.spinner {
  width: 20px; height: 20px;
  border: 2px solid #e5e5e5; border-top-color: #171717; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Section */
.section-title {
  display: flex; align-items: baseline; gap: 10px;
  padding: 8px 4px 0;
}
.section-label { font-size: 0.62rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.section-name { font-size: 0.9rem; font-weight: 600; color: #171717; }

/* Test Cards */
.test-list { display: flex; flex-direction: column; gap: 10px; }

.test-card {
  background: #fff; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  padding: 18px 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.test-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border-color: rgba(0,0,0,0.08);
}
.test-card.active {
  border-color: #171717;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

.test-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}
.test-name {
  font-size: 0.9rem; font-weight: 600; color: #171717;
}
.test-status {
  font-size: 0.68rem; font-weight: 600;
  padding: 3px 10px; border-radius: 999px;
}

.test-desc {
  font-size: 0.78rem; color: #737373;
  margin-bottom: 12px; line-height: 1.5;
}

.test-meta {
  display: flex; gap: 16px; flex-wrap: wrap;
  margin-bottom: 12px;
}
.meta-item {
  display: flex; align-items: center; gap: 5px;
  font-size: 0.72rem; color: #a3a3a3;
}

.test-progress {}
.progress-track {
  height: 6px; background: #f0f0f0;
  border-radius: 999px; overflow: hidden;
  position: relative;
}
.progress-fill-a {
  position: absolute; left: 0; top: 0; bottom: 0;
  background: #3b82f6; border-radius: 999px;
  transition: width 0.4s;
}
.progress-fill-b {
  position: absolute; top: 0; bottom: 0;
  background: #8b5cf6; border-radius: 999px;
  transition: width 0.4s, left 0.4s;
}
.progress-labels {
  display: flex; justify-content: space-between;
  margin-top: 6px;
  font-size: 0.68rem; font-weight: 600;
}

/* Stats */
.stats-card {
  background: #fff; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.05);
  padding: 20px;
}

.winner-banner {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-radius: 12px;
  margin-bottom: 20px;
  font-size: 0.88rem; font-weight: 600;
}
.p-value {
  margin-left: auto;
  font-size: 0.72rem; font-weight: 500;
  color: #737373;
}

/* Comparison Table */
.comparison-table {}
.table-header {
  display: grid; grid-template-columns: 1fr 1.2fr 1.2fr;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
}
.th {
  font-size: 0.72rem; font-weight: 700;
  color: #a3a3a3; text-transform: uppercase;
  letter-spacing: 0.05em;
  display: flex; align-items: center; gap: 6px;
}
.variant-a { color: #3b82f6; }
.variant-b { color: #8b5cf6; }

.variant-dot {
  width: 7px; height: 7px; border-radius: 50%;
}

.table-row {
  display: grid; grid-template-columns: 1fr 1.2fr 1.2fr;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #f5f5f5;
}
.table-row:last-child { border-bottom: none; }
.table-row.highlight { background: #fafafa; border-radius: 8px; }

.td {
  font-size: 0.82rem; color: #171717;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
.td.label {
  font-family: inherit; color: #737373; font-weight: 500;
}
.td.winner {
  font-weight: 700;
  color: #22c55e;
}

@media (min-width: 768px) {
  .ab-content { padding: 24px 32px 40px; }
}
</style>

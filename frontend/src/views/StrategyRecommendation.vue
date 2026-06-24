<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import LegalNotice from '@/components/LegalNotice.vue'

const router = useRouter()

// ── 从 sessionStorage 获取组合数据 ──
const portfolioData = ref<any>(null)
const loading = ref(true)
const error = ref('')

// 从 bindings 生成策略推荐
const recommendations = computed(() => {
  const bindings = portfolioData.value?.portfolio?.bindings || []
  if (bindings.length === 0) return []

  return bindings.map((b: any, idx: number) => {
    // 计算匹配度（基于weight和llm_score）
    const match = Math.min(95, Math.round(
      ((b.weight || 0.1) * 50 + (b.llm_score || 0.5) * 50) * 100
    ))

    // 预期收益（简化估算）
    const expectedReturn = match >= 85 ? '12-18%' : match >= 70 ? '8-14%' : '5-10%'
    const riskLevel = (b.weight || 0) > 0.15 ? '中高' : (b.weight || 0) > 0.08 ? '中等' : '中低'

    return {
      id: b.strategy_id || `rec_${idx}`,
      title: b.strategy_name || `${b.sector_name}策略`,
      family: b.strategy_family || '未分类',
      reason: b.reasoning || `基于${b.sector_name}行业景气度与策略模板匹配`,
      expectedReturn,
      riskLevel,
      sharpe: b.composite_score ? (b.composite_score * 2).toFixed(1) : '1.0',
      maxDrawdown: `-${Math.round((b.weight || 0.1) * 100 + 5)}%`,
      match,
      symbol: b.symbol,
      weight: b.weight,
    }
  }).sort((a: any, b: any) => b.match - a.match)
})

function goBack() {
  router.push('/')
}

function goPortfolio() {
  router.push('/portfolio')
}

onMounted(() => {
  const stored = sessionStorage.getItem('latest_portfolio')
  if (stored) {
    try {
      portfolioData.value = JSON.parse(stored)
    } catch (e) {
      error.value = '数据解析失败'
    }
  } else {
    error.value = '暂无推荐数据，请返回首页生成组合'
  }
  loading.value = false
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
      <LegalNotice
        title="策略推荐声明"
        :show-data-source="true"
        :show-investment-disclaimer="true"
        :show-privacy="true"
        :show-license="true"
        :show-crawler="false"
      />

      <!-- Loading -->
      <div v-if="loading" class="loading-state">加载中...</div>

      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button class="btn-primary" @click="goBack">返回首页</button>
      </div>

      <template v-else>
        <!-- Intro -->
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
                <div class="rec-family">{{ rec.family }} · {{ rec.symbol }}</div>
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
              <span>查看组合</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </template>
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
.loading-state, .error-state {
  text-align: center; padding: 60px 20px; color: #a3a3a3;
}
.error-state p { margin-bottom: 20px; }

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

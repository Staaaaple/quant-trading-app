<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { profileApi, type InvestorProfile } from '@/api/profile'
import { marketSignalApi, type MarketSignalLatest } from '@/api/marketSignal'
import { portfolioApi, type PortfolioDesignResult } from '@/api/portfolio'
import UserSwitcher from '@/components/UserSwitcher.vue'
import LegalNotice from '@/components/LegalNotice.vue'
import LandingView from './LandingView.vue'

const router = useRouter()
const userStore = useUserStore()

const hasProfile = ref(false)
const profile = ref<InvestorProfile | null>(null)
const signal = ref<MarketSignalLatest | null>(null)
const portfolio = ref<PortfolioDesignResult | null>(null)
const loading = ref(true)

async function checkProfile() {
  loading.value = true
  try {
    // 等待用户 store 加载完成
    if (!userStore.currentUserId) {
      await userStore.loadUsers()
    }

    if (!userStore.currentUserId) {
      hasProfile.value = false
      return
    }

    const p = await profileApi.getMine()
    if (p) {
      hasProfile.value = true
      profile.value = p
      // Load market signal and design portfolio
      await loadDashboardData(p)
    } else {
      hasProfile.value = false
    }
  } catch (e) {
    console.error('Failed to check profile:', e)
    hasProfile.value = false
  } finally {
    loading.value = false
  }
}

/** 监听用户切换事件 */
function handleUserSwitched() {
  // 重置状态并重新加载
  hasProfile.value = false
  profile.value = null
  signal.value = null
  portfolio.value = null
  checkProfile()
}

async function loadDashboardData(p: InvestorProfile) {
  try {
    // 1. 先加载市场信号（立即展示仪表盘）
    signal.value = await marketSignalApi.getLatest()
    if (signal.value) {
      sessionStorage.setItem('latest_market_signal', JSON.stringify(signal.value))
    }
  } catch (e) {
    console.error('Failed to load market signal:', e)
  }

  // 2. 后台生成组合（不阻塞仪表盘渲染）
  // 用户在浏览画像和信号页面时，组合在后台生成
  generatePortfolioInBackground(p)
}

/** 后台生成组合——不阻塞 UI，使用异步任务 */
async function generatePortfolioInBackground(p: InvestorProfile) {
  try {
    // 1. 先检查是否已有任务（running / completed）
    const latestTask = await portfolioApi.getMyLatestTask()
    if (latestTask?.task_id && (latestTask.status === 'running' || latestTask.status === 'completed')) {
      localStorage.setItem('portfolio_task_id', String(latestTask.task_id))
      if (latestTask.status === 'completed' && latestTask.result) {
        portfolio.value = latestTask.result
        sessionStorage.setItem('latest_portfolio', JSON.stringify(latestTask.result))
      }
      return
    }

    // 2. 构造请求参数
    const profileVector = {
      risk_tolerance: p.risk_tolerance,
      loss_aversion: p.loss_aversion,
      herding_tendency: p.herding_tendency,
      overconfidence: p.overconfidence,
      delayed_gratification: p.delayed_gratification,
      security_need: p.security_need,
      time_horizon_score: p.time_horizon_score,
      experience_level: p.experience_level,
      capital_tier: p.capital_tier,
      income_stability: p.income_stability,
      debt_pressure: p.debt_pressure,
      information_processing: p.information_processing,
      social_pressure: p.social_pressure,
      emergency_response: p.emergency_response,
      anchoring_effect: p.anchoring_effect,
      diversification_preference: p.diversification_preference,
      stop_loss_discipline: p.stop_loss_discipline,
      emotional_stability: p.emotional_stability,
    }

    const marketSignal = {
      macro_score: signal.value?.macro?.score ?? 0.5,
      geo_risk: signal.value?.geo?.overall_risk ?? 0.5,
      industry_scores: signal.value?.industry?.heatmap ?? {},
      social_trends: signal.value?.social?.major_themes ?? [],
    }

    // 3. 提交异步任务
    const task = await portfolioApi.designAsync({
      profile_vector: profileVector,
      market_signal: marketSignal,
    })

    if (task?.task_id) {
      localStorage.setItem('portfolio_task_id', String(task.task_id))
      if (task.status === 'completed' && task.result) {
        portfolio.value = task.result
        sessionStorage.setItem('latest_portfolio', JSON.stringify(task.result))
      }
    }
  } catch (e) {
    console.error('Failed to design portfolio in background:', e)
  }
}

function goProfile() {
  router.push('/profile')
}

function goMarket() {
  router.push('/market')
}

function goPortfolio() {
  router.push('/portfolio')
}

function goRecommendation() {
  router.push('/recommendation')
}

function goLifespan() {
  router.push('/ecosystem')
}

function goBacktests() {
  router.push('/backtests')
}

function scoreColor(score: number | null): string {
  if (score === null) return '#a3a3a3'
  if (score >= 70) return '#22c55e'
  if (score >= 50) return '#d97706'
  return '#ef4444'
}

const userName = ref('User')

onMounted(() => {
  checkProfile()
  window.addEventListener('user:switched', handleUserSwitched)
})

onUnmounted(() => {
  window.removeEventListener('user:switched', handleUserSwitched)
})
</script>

<template>
  <div class="home-page">
    <!-- Textures -->
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>
    <div class="texture-spotlight"></div>

    <!-- Header -->
    <header class="home-header">
      <div class="home-header-inner">
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
        <UserSwitcher />
      </div>
    </header>

    <!-- Content -->
    <div class="home-content">
      <LegalNotice
        title="使用声明"
        :show-data-source="true"
        :show-investment-disclaimer="true"
        :show-privacy="true"
        :show-license="true"
        :show-crawler="true"
      />

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- ========== EMPTY STATE ========== -->
      <template v-else-if="!hasProfile">
        <LandingView @start="goProfile" />
      </template>

      <!-- ========== DASHBOARD ========== -->
      <template v-else>
        <!-- Market Card -->
        <div class="card market-card" @click="goMarket">
          <div class="card-glow"></div>
          <div class="card-inner">
            <div class="card-top">
              <span class="card-label">MARKET STATE</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </div>
            <div class="market-body">
              <div class="market-info">
                <div class="market-cycle">
                  <span class="cycle-badge">{{ signal?.market_cycle || '—' }}</span>
                  <span v-if="signal" class="cycle-dot"></span>
                </div>
                <div class="market-mood">{{ signal?.market_mood || '加载中...' }}</div>
              </div>
              <div class="market-score-box">
                <span class="score-val" :style="{ color: scoreColor((signal?.composite_score || 0) + 50) }">
                  {{ (signal?.composite_score ?? 0) > 0 ? '+' : '' }}{{ signal?.composite_score ?? 0 }}
                </span>
                <span class="score-label">SCORE</span>
              </div>
            </div>
            <div class="market-tags">
              <span class="tag">地缘: {{ signal?.geo.risk_level || '—' }}</span>
              <span v-if="signal?.industry.recommended?.length" class="tag tag-active">{{ signal.industry.recommended[0] }}: 高景气</span>
              <span v-if="signal?.social.major_themes?.length" class="tag tag-active">{{ signal.social.major_themes[0] }} ↑</span>
            </div>
          </div>
        </div>

        <!-- Portfolio Card -->
        <div class="card portfolio-card" @click="goPortfolio">
          <div class="card-glow"></div>
          <div class="card-inner">
            <div class="card-top">
              <span class="card-label">PORTFOLIO</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </div>
            <div class="portfolio-body">
              <div class="stats-row">
                <div class="stat">
                  <div class="stat-label">预期年化</div>
                  <div class="stat-val">{{ portfolio?.summary?.stock_ratio ? '10-14%' : '—' }}</div>
                </div>
                <div class="stat">
                  <div class="stat-label">组合健康度</div>
                  <div class="stat-val">{{ portfolio?.summary?.health_score || '—' }}</div>
                </div>
              </div>
              <div class="meta-row">
                <div class="meta-item">
                  <span class="meta-dot" :class="(portfolio?.summary?.health_score ?? 0) >= 70 ? 'meta-green' : 'meta-amber'"></span>
                  <span>健康度 {{ portfolio?.summary?.health_score || '—' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-dot meta-amber"></span>
                  <span>寿命 {{ portfolio?.summary?.expected_lifespan || '—' }}</span>
                </div>
              </div>
            </div>
            <!-- Alert -->
            <div v-if="(portfolio?.portfolio?.portfolio_lifespan ?? 12) < 3" class="alert-box">
              <span class="alert-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
              </span>
              <span class="alert-txt">策略寿命即将到期，建议关注替代方案</span>
              <span class="alert-link" @click.stop="goLifespan">查看替代</span>
            </div>
          </div>
        </div>

        <!-- Action Grid -->
        <div class="action-grid">
          <button class="action-cell" @click="goProfile">
            <div class="action-icon-wrap">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
            </div>
            <span>调整画像</span>
          </button>
          <button class="action-cell" @click="goPortfolio">
            <div class="action-icon-wrap">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
            </div>
            <span>查看组合</span>
          </button>
          <button class="action-cell" @click="goMarket">
            <div class="action-icon-wrap">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            </div>
            <span>市场信号</span>
          </button>
          <button class="action-cell" @click="goRecommendation">
            <div class="action-icon-wrap">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5c0-2 2-3 4-3z"/><path d="M8 13v4"/><path d="M16 13v4"/><path d="M12 15v4"/></svg>
            </div>
            <span>策略推荐</span>
          </button>
        </div>

        <!-- Allocation Card -->
        <div class="card alloc-card">
          <div class="card-glow"></div>
          <div class="card-inner">
            <div class="card-top">
              <span class="card-label">ALLOCATION</span>
            </div>
            <div class="alloc-body">
              <div class="donut-wrap">
                <svg viewBox="0 0 120 120" class="donut-svg">
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#f0f0f0" stroke-width="10"/>
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#171717" stroke-width="10" stroke-linecap="round"
                    :stroke-dasharray="`${(portfolio?.portfolio?.saa?.weights?.stock || 0.45) * 289} 289`" stroke-dashoffset="0" transform="rotate(-90 60 60)"/>
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#404040" stroke-width="10" stroke-linecap="round"
                    :stroke-dasharray="`${(portfolio?.portfolio?.saa?.weights?.bond || 0.35) * 289} 289`"
                    :stroke-dashoffset="`${-(portfolio?.portfolio?.saa?.weights?.stock || 0.45) * 289}`" transform="rotate(-90 60 60)"/>
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#737373" stroke-width="10" stroke-linecap="round"
                    :stroke-dasharray="`${(portfolio?.portfolio?.saa?.weights?.commodity || 0.12) * 289} 289`"
                    :stroke-dashoffset="`${-((portfolio?.portfolio?.saa?.weights?.stock || 0.45) + (portfolio?.portfolio?.saa?.weights?.bond || 0.35)) * 289}`" transform="rotate(-90 60 60)"/>
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#a3a3a3" stroke-width="10" stroke-linecap="round"
                    :stroke-dasharray="`${(portfolio?.portfolio?.saa?.weights?.cash || 0.08) * 289} 289`"
                    :stroke-dashoffset="`${-((portfolio?.portfolio?.saa?.weights?.stock || 0.45) + (portfolio?.portfolio?.saa?.weights?.bond || 0.35) + (portfolio?.portfolio?.saa?.weights?.commodity || 0.12)) * 289}`" transform="rotate(-90 60 60)"/>
                </svg>
                <div class="donut-center">
                  <div class="donut-label">股票</div>
                  <div class="donut-val">{{ Math.round((portfolio?.portfolio?.saa?.weights?.stock || 0.45) * 100) }}%</div>
                </div>
              </div>
              <div class="alloc-legend">
                <div class="leg-row">
                  <span class="leg-dot" style="background:#171717"></span>
                  <span class="leg-name">股票</span>
                  <span class="leg-pct">{{ Math.round((portfolio?.portfolio?.saa?.weights?.stock || 0.45) * 100) }}%</span>
                </div>
                <div class="leg-row">
                  <span class="leg-dot" style="background:#404040"></span>
                  <span class="leg-name">债券</span>
                  <span class="leg-pct">{{ Math.round((portfolio?.portfolio?.saa?.weights?.bond || 0.35) * 100) }}%</span>
                </div>
                <div class="leg-row">
                  <span class="leg-dot" style="background:#737373"></span>
                  <span class="leg-name">商品</span>
                  <span class="leg-pct">{{ Math.round((portfolio?.portfolio?.saa?.weights?.commodity || 0.12) * 100) }}%</span>
                </div>
                <div class="leg-row">
                  <span class="leg-dot" style="background:#a3a3a3"></span>
                  <span class="leg-name">现金</span>
                  <span class="leg-pct">{{ Math.round((portfolio?.portfolio?.saa?.weights?.cash || 0.08) * 100) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
          <button class="quick-btn" @click="goBacktests">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
            <span>回测中心</span>
          </button>
          <button class="quick-btn" @click="goLifespan">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span>寿命监控</span>
          </button>
        </div>
      </template>
    </div>

    <!-- Bottom Tab Bar -->
    <nav class="tabbar">
      <div class="tabbar-item active">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>首页</span>
      </div>
      <div class="tabbar-item" @click="goMarket">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        <span>市场</span>
      </div>
      <div class="tabbar-item" @click="goPortfolio">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
        <span>组合</span>
      </div>
      <div class="tabbar-item">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
        <span>设置</span>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  position: relative;
  padding-bottom: 88px;
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
.texture-spotlight {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,0,0,0.04) 0%, transparent 70%),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(0,0,0,0.02) 0%, transparent 60%);
}

/* Header */
.home-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.82);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.home-header-inner {
  max-width: 720px; margin: 0 auto; padding: 14px 24px;
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

.user-pill {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 14px 4px 4px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 999px;
  font-size: 0.78rem; color: #525252;
}
.user-avatar {
  width: 24px; height: 24px; border-radius: 50%;
  background: #171717; color: #fff;
  font-size: 0.7rem; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
}
.user-name { font-weight: 500; letter-spacing: -0.01em; }

/* Content */
.home-content {
  flex: 1;
  max-width: 720px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}
.loading-state { text-align: center; padding: 80px 20px; color: #a3a3a3; display: flex; flex-direction: column; align-items: center; gap: 16px; }
.loading-state .loading-spinner {
  width: 40px; height: 40px;
  border: 3px solid #e5e5e5;
  border-top-color: #171717;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.loading-state p { font-size: 1rem; font-weight: 500; color: #525252; margin: 0; }
.loading-state .loading-sub { font-size: 0.78rem; color: #a3a3a3; }
.loading-state.designing .loading-spinner { border-top-color: #22c55e; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ========== EMPTY STATE ========== */
.hero-empty { text-align: center; padding: 20px 0 8px; position: relative; }
.hero-glow {
  position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
  width: 300px; height: 200px;
  background: radial-gradient(ellipse, rgba(0,0,0,0.04) 0%, transparent 70%);
  pointer-events: none; z-index: 0;
}
.hero-visual { width: 280px; height: 200px; margin: 0 auto 20px; position: relative; z-index: 1; }
.hero-svg { width: 100%; height: 100%; }
.hero-title {
  font-size: 2rem; font-weight: 800; color: #171717;
  margin: 0 0 10px; letter-spacing: -0.04em; line-height: 1.1;
}
.gradient-text {
  background: linear-gradient(135deg, #171717 0%, #525252 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-desc { font-size: 0.88rem; color: #737373; margin: 0; line-height: 1.6; font-weight: 400; }

/* Features */
.feature-list { display: flex; flex-direction: column; gap: 10px; }
.feature-card {
  display: flex; align-items: center; gap: 0;
  padding: 18px 20px; background: #fff; border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 12px rgba(0,0,0,0.02);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer; position: relative; overflow: hidden;
}
.feature-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.04), transparent);
}
.feature-card:hover {
  border-color: rgba(0,0,0,0.1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.03), 0 8px 24px rgba(0,0,0,0.06);
  transform: translateY(-2px);
}
.feature-card:hover svg { color: #171717; transform: translateX(3px); }
.feature-card svg { color: #d4d4d4; flex-shrink: 0; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.feature-num { font-size: 0.65rem; font-weight: 700; color: #e5e5e5; letter-spacing: 0.08em; min-width: 22px; text-align: center; }
.feature-line { width: 1px; height: 28px; background: rgba(0,0,0,0.05); margin: 0 14px; flex-shrink: 0; }
.feature-content { flex: 1; }
.feature-title { font-size: 0.88rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }
.feature-desc { font-size: 0.76rem; color: #a3a3a3; margin-top: 3px; }

/* CTA */
.btn-primary {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 17px 24px; border: none; border-radius: 16px;
  background: #171717; color: #fff; font-family: inherit;
  font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
  cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative; overflow: hidden;
}
.btn-primary:hover { background: #262626; transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.18); }

.subline {
  text-align: center; font-size: 0.74rem; color: #a3a3a3; margin: 4px 0 0;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.pulse-dot {
  width: 5px; height: 5px; border-radius: 50%; background: #22c55e;
  display: inline-block; animation: pulse-dot 2.2s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.3); }
  50% { opacity: 0.6; box-shadow: 0 0 0 4px rgba(34,197,94,0); }
}

/* ========== DASHBOARD ========== */
/* Cards */
.card {
  position: relative; border-radius: 20px; background: #fff;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden; cursor: pointer;
}
.card:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.03), 0 12px 32px rgba(0,0,0,0.06);
  transform: translateY(-1px); border-color: rgba(0,0,0,0.08);
}
.card-glow {
  position: absolute; top: -40%; right: -20%;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(0,0,0,0.025) 0%, transparent 70%);
  pointer-events: none; opacity: 0; transition: opacity 0.3s ease;
}
.card:hover .card-glow { opacity: 1; }
.card-inner { position: relative; z-index: 1; padding: 20px 22px; }
.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-label { font-size: 0.62rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; text-transform: uppercase; }
.card-top svg { color: #e5e5e5; transition: color 0.2s; }
.card:hover .card-top svg { color: #a3a3a3; }

/* Market Card */
.market-body { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.market-info { display: flex; flex-direction: column; gap: 5px; }
.market-cycle { display: flex; align-items: center; gap: 8px; }
.cycle-badge {
  display: inline-block; padding: 5px 13px;
  background: #171717; color: #fff;
  font-size: 0.85rem; font-weight: 600; border-radius: 8px; letter-spacing: -0.01em;
}
.cycle-dot {
  width: 7px; height: 7px; border-radius: 50%; background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34,197,94,0.15);
  animation: pulse-dot 2.2s ease-in-out infinite;
}
.market-mood { font-size: 0.82rem; color: #737373; }
.market-score-box { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.score-val { font-size: 1.8rem; font-weight: 800; line-height: 1; letter-spacing: -0.03em; }
.score-label { font-size: 0.58rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.12em; }
.market-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.tag {
  font-size: 0.72rem; font-weight: 500; padding: 5px 11px;
  border-radius: 8px; background: #f5f5f5; color: #525252;
  border: 1px solid rgba(0,0,0,0.04); transition: all 0.2s ease;
}
.tag-active { background: #f0fdf4; color: #166534; border-color: rgba(34,197,94,0.15); }

/* Portfolio Card */
.stats-row { display: flex; gap: 32px; margin-bottom: 14px; }
.stat-label { font-size: 0.68rem; color: #a3a3a3; margin-bottom: 5px; letter-spacing: 0.03em; font-weight: 500; }
.stat-val { font-size: 1.45rem; font-weight: 700; color: #171717; letter-spacing: -0.02em; }
.meta-row { display: flex; gap: 20px; }
.meta-item { display: flex; align-items: center; gap: 7px; font-size: 0.78rem; color: #737373; font-weight: 500; }
.meta-dot { width: 6px; height: 6px; border-radius: 50%; }
.meta-green { background: #22c55e; }
.meta-amber { background: #d97706; }

/* Alert Box */
.alert-box {
  display: flex; align-items: center; gap: 9px;
  margin-top: 16px; padding: 13px 15px;
  background: linear-gradient(90deg, #fafafa, #f5f5f5);
  border-radius: 12px; border: 1px solid rgba(0,0,0,0.04);
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

/* Action Grid */
.action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.action-cell {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 22px 12px; background: #fff;
  border: 1px solid rgba(0,0,0,0.05); border-radius: 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 12px rgba(0,0,0,0.02);
  cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit; color: #525252; position: relative; overflow: hidden;
}
.action-cell::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.03), transparent);
}
.action-cell:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.03), 0 8px 24px rgba(0,0,0,0.05);
  transform: translateY(-2px); border-color: rgba(0,0,0,0.1); color: #171717;
}
.action-icon-wrap {
  width: 44px; height: 44px; border-radius: 12px;
  background: #fafafa; border: 1px solid rgba(0,0,0,0.04);
  display: flex; align-items: center; justify-content: center;
  color: #a3a3a3; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.action-cell:hover .action-icon-wrap {
  background: #171717; border-color: #171717; color: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
.action-cell span:last-child { font-size: 0.78rem; font-weight: 500; letter-spacing: -0.01em; }

/* Allocation Card */
.alloc-body { display: flex; align-items: center; gap: 28px; }
.donut-wrap { position: relative; width: 110px; height: 110px; flex-shrink: 0; }
.donut-svg { width: 100%; height: 100%; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.04)); }
.donut-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.donut-label { font-size: 0.62rem; color: #a3a3a3; letter-spacing: 0.06em; font-weight: 500; }
.donut-val { font-size: 1.2rem; font-weight: 700; color: #171717; letter-spacing: -0.02em; }
.alloc-legend { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.leg-row { display: flex; align-items: center; gap: 10px; }
.leg-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.leg-name { font-size: 0.82rem; color: #525252; flex: 1; font-weight: 500; }
.leg-pct { font-size: 0.82rem; font-weight: 600; color: #171717; font-variant-numeric: tabular-nums; }

/* Quick Actions */
.quick-actions { display: flex; gap: 10px; }
.quick-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px; background: #fff; border: 1px solid rgba(0,0,0,0.05);
  border-radius: 14px; font-family: inherit; font-size: 0.82rem;
  font-weight: 500; color: #525252; cursor: pointer;
  transition: all 0.2s ease;
}
.quick-btn:hover { border-color: rgba(0,0,0,0.1); color: #171717; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }

/* Tabbar */
.tabbar {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 50;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(20px) saturate(1.3);
  border-top: 1px solid rgba(0,0,0,0.05);
  display: flex; justify-content: space-around;
  padding: 8px 0 calc(8px + env(safe-area-inset-bottom, 0px));
}
.tabbar-item {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 6px 20px; color: #d4d4d4; cursor: pointer;
  transition: all 0.2s ease; border-radius: 12px; position: relative;
}
.tabbar-item:hover { color: #737373; }
.tabbar-item.active { color: #171717; }
.tabbar-item.active::before {
  content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 20px; height: 3px; background: #171717; border-radius: 0 0 3px 3px;
}
.tabbar-item span { font-size: 0.6rem; font-weight: 600; letter-spacing: 0.02em; }

/* Responsive */
@media (min-width: 768px) {
  .home-content { padding: 24px 32px 40px; }
  .hero-title { font-size: 2.6rem; }
  .hero-visual { width: 340px; height: 240px; }
  .feature-list { flex-direction: row; gap: 12px; }
  .feature-card { flex: 1; flex-direction: column; text-align: center; padding: 28px 20px; gap: 12px; }
  .feature-line { display: none; }
  .feature-num { font-size: 0.7rem; }
  .feature-card svg { margin-top: 8px; }
  .action-grid { grid-template-columns: repeat(4, 1fr); }
  .tabbar {
    max-width: 720px; left: 50%; transform: translateX(-50%);
    border-radius: 16px 16px 0 0; border: 1px solid rgba(0,0,0,0.05);
    border-bottom: none; bottom: 12px; box-shadow: 0 -4px 24px rgba(0,0,0,0.04);
  }
}
</style>

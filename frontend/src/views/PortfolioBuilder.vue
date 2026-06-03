<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { profileApi, type InvestorProfile } from '@/api/profile'
import { marketSignalApi, type MarketSignalLatest } from '@/api/marketSignal'
import { portfolioApi, type PortfolioDesignResult } from '@/api/portfolio'

const router = useRouter()

const profile = ref<InvestorProfile | null>(null)
const signal = ref<MarketSignalLatest | null>(null)
const portfolio = ref<PortfolioDesignResult | null>(null)
const loading = ref(true)
const activeTab = ref<'overview' | 'allocation' | 'risk'>('overview')

async function loadData() {
  loading.value = true
  try {
    const users = await userApi.list()
    if (users.length === 0) {
      router.push('/')
      return
    }
    const user = users[0]
    if (!user) {
      router.push('/')
      return
    }
    const p = await profileApi.getByUser(user.id)
    if (!p) {
      router.push('/')
      return
    }
    profile.value = p

    // Load market signal
    try {
      signal.value = await marketSignalApi.getLatest()
    } catch (e) {
      console.error('Failed to load market signal:', e)
    }

    // Design portfolio
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
    }

    const marketSignal = {
      macro_score: signal.value?.macro.score ?? 0.5,
      geo_risk: signal.value?.geo.overall_risk ?? 0.5,
      industry_scores: signal.value?.industry.heatmap ?? {},
      social_trends: signal.value?.social.major_themes ?? [],
    }

    portfolio.value = await portfolioApi.design({
      profile_vector: profileVector,
      market_signal: marketSignal,
    })
  } catch (e) {
    console.error('Failed to load portfolio:', e)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/')
}

function goOnboarding() {
  router.push('/onboarding')
}

function goBacktests() {
  router.push('/backtests')
}

const weights = ref<Record<string, number>>({})

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="portfolio-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-label">PORTFOLIO</span>
          <span class="header-name">我的组合</span>
        </div>
        <div class="header-actions">
          <button class="icon-btn" @click="goBacktests" title="回测">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          </button>
        </div>
      </div>

      <!-- Tab Switcher -->
      <div class="tab-switcher">
        <button :class="['tab-btn', { active: activeTab === 'overview' }]" @click="activeTab = 'overview'">概览</button>
        <button :class="['tab-btn', { active: activeTab === 'allocation' }]" @click="activeTab = 'allocation'">配置</button>
        <button :class="['tab-btn', { active: activeTab === 'risk' }]" @click="activeTab = 'risk'">风控</button>
      </div>
    </header>

    <!-- Content -->
    <div class="portfolio-content">
      <div v-if="loading" class="loading-state">加载组合数据...</div>

      <template v-else-if="portfolio">
        <!-- ===== OVERVIEW TAB ===== -->
        <template v-if="activeTab === 'overview'">
          <!-- Summary Card -->
          <div class="card summary-card">
            <div class="card-glow"></div>
            <div class="card-inner">
              <div class="summary-grid">
                <div class="summary-item">
                  <div class="summary-label">预期年化</div>
                  <div class="summary-val">10-14%</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">最大回撤</div>
                  <div class="summary-val">&lt;18%</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">胜率</div>
                  <div class="summary-val">55%</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">夏普比率</div>
                  <div class="summary-val">0.9</div>
                </div>
              </div>
              <div class="summary-divider"></div>
              <div class="summary-meta">
                <div class="meta-tag">
                  <span class="meta-dot meta-amber"></span>
                  <span>寿命 {{ portfolio.summary.expected_lifespan }}</span>
                </div>
                <div class="meta-tag">
                  <span class="meta-dot meta-green"></span>
                  <span>健康度 {{ portfolio.summary.health_score }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Strategy Bindings -->
          <div class="section-title">
            <span class="section-label">STRATEGIES</span>
            <span class="section-count">{{ portfolio.summary.total_strategies }} 个策略</span>
          </div>

          <div class="strategy-list">
            <div v-for="(binding, idx) in portfolio.portfolio.bindings" :key="idx" class="strategy-card">
              <div class="strategy-header">
                <div class="strategy-info">
                  <div class="strategy-name">{{ binding.strategy_name }}</div>
                  <div class="strategy-family">{{ binding.strategy_family }}</div>
                </div>
                <div class="strategy-weight">{{ Math.round(binding.weight * 100) }}%</div>
              </div>
              <div class="strategy-sector">
                <span class="sector-tag">{{ binding.sector_name }}</span>
                <span class="lifespan-tag">寿命 12月</span>
              </div>
            </div>
          </div>

          <!-- Rationale -->
          <div class="card rationale-card">
            <div class="card-inner">
              <div class="card-top">
                <span class="card-label">RATIONALE</span>
              </div>
              <p class="rationale-text">{{ portfolio.portfolio.saa.rationale }}</p>
            </div>
          </div>

          <!-- CTA -->
          <button class="btn-primary" @click="goOnboarding">
            <span>应用组合</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>
        </template>

        <!-- ===== ALLOCATION TAB ===== -->
        <template v-if="activeTab === 'allocation'">
          <div class="card alloc-detail-card">
            <div class="card-inner">
              <div class="card-top">
                <span class="card-label">ASSET ALLOCATION</span>
              </div>
              <div class="alloc-chart">
                <div class="donut-wrap large">
                  <svg viewBox="0 0 120 120" class="donut-svg">
                    <circle cx="60" cy="60" r="46" fill="none" stroke="#f0f0f0" stroke-width="10"/>
                    <circle cx="60" cy="60" r="46" fill="none" stroke="#171717" stroke-width="10" stroke-linecap="round"
                      :stroke-dasharray="`${(portfolio.portfolio.saa.weights.stock || 0.45) * 289} 289`" stroke-dashoffset="0" transform="rotate(-90 60 60)"/>
                    <circle cx="60" cy="60" r="46" fill="none" stroke="#404040" stroke-width="10" stroke-linecap="round"
                      :stroke-dasharray="`${(portfolio.portfolio.saa.weights.bond || 0.35) * 289} 289`"
                      :stroke-dashoffset="`${-(portfolio.portfolio.saa.weights.stock || 0.45) * 289}`" transform="rotate(-90 60 60)"/>
                    <circle cx="60" cy="60" r="46" fill="none" stroke="#737373" stroke-width="10" stroke-linecap="round"
                      :stroke-dasharray="`${(portfolio.portfolio.saa.weights.commodity || 0.12) * 289} 289`"
                      :stroke-dashoffset="`${-((portfolio.portfolio.saa.weights.stock || 0.45) + (portfolio.portfolio.saa.weights.bond || 0.35)) * 289}`" transform="rotate(-90 60 60)"/>
                    <circle cx="60" cy="60" r="46" fill="none" stroke="#a3a3a3" stroke-width="10" stroke-linecap="round"
                      :stroke-dasharray="`${(portfolio.portfolio.saa.weights.cash || 0.08) * 289} 289`"
                      :stroke-dashoffset="`${-((portfolio.portfolio.saa.weights.stock || 0.45) + (portfolio.portfolio.saa.weights.bond || 0.35) + (portfolio.portfolio.saa.weights.commodity || 0.12)) * 289}`" transform="rotate(-90 60 60)"/>
                  </svg>
                  <div class="donut-center">
                    <div class="donut-label">股票</div>
                    <div class="donut-val">{{ Math.round((portfolio.portfolio.saa.weights.stock || 0.45) * 100) }}%</div>
                  </div>
                </div>
              </div>
              <div class="alloc-legend-detail">
                <div class="leg-row large">
                  <span class="leg-dot" style="background:#171717"></span>
                  <span class="leg-name">股票</span>
                  <span class="leg-pct">{{ Math.round((portfolio.portfolio.saa.weights.stock || 0.45) * 100) }}%</span>
                </div>
                <div class="leg-row large">
                  <span class="leg-dot" style="background:#404040"></span>
                  <span class="leg-name">债券</span>
                  <span class="leg-pct">{{ Math.round((portfolio.portfolio.saa.weights.bond || 0.35) * 100) }}%</span>
                </div>
                <div class="leg-row large">
                  <span class="leg-dot" style="background:#737373"></span>
                  <span class="leg-name">商品</span>
                  <span class="leg-pct">{{ Math.round((portfolio.portfolio.saa.weights.commodity || 0.12) * 100) }}%</span>
                </div>
                <div class="leg-row large">
                  <span class="leg-dot" style="background:#a3a3a3"></span>
                  <span class="leg-name">现金</span>
                  <span class="leg-pct">{{ Math.round((portfolio.portfolio.saa.weights.cash || 0.08) * 100) }}%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- TAA Detail -->
          <div class="card taa-card">
            <div class="card-inner">
              <div class="card-top">
                <span class="card-label">TACTICAL ALLOCATION</span>
              </div>
              <div class="taa-content">
                <p class="taa-rationale">{{ portfolio.portfolio.taa.rationale || '基于当前市场周期和行业景气度进行战术调整' }}</p>
              </div>
            </div>
          </div>
        </template>

        <!-- ===== RISK TAB ===== -->
        <template v-if="activeTab === 'risk'">
          <div class="card risk-card">
            <div class="card-inner">
              <div class="card-top">
                <span class="card-label">RISK CONFIG</span>
              </div>
              <div class="risk-grid">
                <div class="risk-item">
                  <div class="risk-label">止损线</div>
                  <div class="risk-val">{{ Math.round((portfolio.portfolio.risk_config.stop_loss || 0.08) * 100) }}%</div>
                </div>
                <div class="risk-item">
                  <div class="risk-label">单标的上限</div>
                  <div class="risk-val">{{ Math.round((portfolio.portfolio.risk_config.max_position || 0.20) * 100) }}%</div>
                </div>
                <div class="risk-item">
                  <div class="risk-label">最大回撤硬止损</div>
                  <div class="risk-val">{{ Math.round((portfolio.portfolio.risk_config.max_drawdown || 0.15) * 100) }}%</div>
                </div>
                <div class="risk-item">
                  <div class="risk-label">再平衡触发</div>
                  <div class="risk-val">{{ Math.round((portfolio.portfolio.risk_config.rebalance_threshold || 0.05) * 100) }}%</div>
                </div>
              </div>
              <div class="risk-rationale">
                <p>{{ portfolio.portfolio.risk_config.rationale }}</p>
              </div>
            </div>
          </div>

          <!-- Reliability -->
          <div class="card reliability-card">
            <div class="card-inner">
              <div class="card-top">
                <span class="card-label">RELIABILITY</span>
              </div>
              <div class="reliability-score">
                <div class="score-ring">
                  <svg viewBox="0 0 100 100" class="ring-svg">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#f0f0f0" stroke-width="8"/>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#171717" stroke-width="8" stroke-linecap="round"
                      :stroke-dasharray="`${(portfolio.portfolio.reliability.confidence || 0.7) * 264} 264`" stroke-dashoffset="0" transform="rotate(-90 50 50)"/>
                  </svg>
                  <div class="ring-center">
                    <div class="ring-val">{{ Math.round((portfolio.portfolio.reliability.confidence || 0.7) * 100) }}</div>
                    <div class="ring-label">置信度</div>
                  </div>
                </div>
                <div class="reliability-level">
                  <div class="level-badge">{{ portfolio.portfolio.reliability.reliability_level }}</div>
                  <div class="level-desc">可靠性等级</div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<style scoped>
.portfolio-page {
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
.header-actions { display: flex; gap: 8px; }
.icon-btn {
  width: 36px; height: 36px;
  border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.7);
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.icon-btn:hover { background: #fff; border-color: rgba(0,0,0,0.1); color: #171717; }

/* Tab Switcher */
.tab-switcher {
  max-width: 720px; margin: 0 auto;
  padding: 8px 24px 12px;
  display: flex; gap: 8px;
}
.tab-btn {
  flex: 1; padding: 10px;
  border-radius: 12px; border: 1px solid transparent;
  background: transparent; color: #a3a3a3;
  font-size: 0.82rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
  font-family: inherit;
}
.tab-btn:hover { background: rgba(0,0,0,0.04); color: #525252; }
.tab-btn.active { background: #171717; color: #fff; }

/* Content */
.portfolio-content {
  max-width: 720px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}
.loading-state { text-align: center; padding: 60px 0; color: #a3a3a3; font-size: 0.9rem; }

/* Cards */
.card {
  position: relative; border-radius: 20px; background: #fff;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
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

/* Summary */
.summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.summary-item { text-align: center; }
.summary-label { font-size: 0.68rem; color: #a3a3a3; margin-bottom: 6px; letter-spacing: 0.03em; }
.summary-val { font-size: 1.3rem; font-weight: 700; color: #171717; letter-spacing: -0.02em; }
.summary-divider { height: 1px; background: rgba(0,0,0,0.05); margin: 16px 0; }
.summary-meta { display: flex; justify-content: center; gap: 20px; }
.meta-tag { display: flex; align-items: center; gap: 7px; font-size: 0.78rem; color: #737373; font-weight: 500; }
.meta-dot { width: 6px; height: 6px; border-radius: 50%; }
.meta-green { background: #22c55e; }
.meta-amber { background: #d97706; }

/* Section Title */
.section-title { display: flex; align-items: center; justify-content: space-between; padding: 4px 4px 0; }
.section-label { font-size: 0.62rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.section-count { font-size: 0.75rem; color: #a3a3a3; }

/* Strategy List */
.strategy-list { display: flex; flex-direction: column; gap: 10px; }
.strategy-card {
  background: #fff; border-radius: 16px; padding: 18px 20px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  transition: all 0.2s ease;
}
.strategy-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.04); border-color: rgba(0,0,0,0.08); }
.strategy-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.strategy-name { font-size: 0.92rem; font-weight: 600; color: #171717; }
.strategy-family { font-size: 0.72rem; color: #a3a3a3; margin-top: 2px; }
.strategy-weight { font-size: 1.1rem; font-weight: 700; color: #171717; }
.strategy-sector { display: flex; gap: 8px; }
.sector-tag {
  font-size: 0.72rem; font-weight: 500; padding: 4px 10px;
  border-radius: 6px; background: #f5f5f5; color: #525252;
}
.lifespan-tag {
  font-size: 0.72rem; font-weight: 500; padding: 4px 10px;
  border-radius: 6px; background: #fffbeb; color: #92400e;
}

/* Rationale */
.rationale-text { font-size: 0.85rem; color: #525252; line-height: 1.7; margin: 0; }

/* CTA */
.btn-primary {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 17px 24px; border: none; border-radius: 16px;
  background: #171717; color: #fff; font-family: inherit;
  font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
  cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary:hover { background: #262626; transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.18); }

/* Allocation Detail */
.alloc-chart { display: flex; justify-content: center; padding: 20px 0; }
.donut-wrap.large { width: 160px; height: 160px; }
.donut-svg { width: 100%; height: 100%; }
.donut-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.donut-label { font-size: 0.65rem; color: #a3a3a3; letter-spacing: 0.06em; }
.donut-val { font-size: 1.4rem; font-weight: 700; color: #171717; }
.alloc-legend-detail { display: flex; flex-direction: column; gap: 12px; padding-top: 8px; }
.leg-row.large { padding: 10px 12px; background: #fafafa; border-radius: 10px; }
.leg-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.leg-name { font-size: 0.85rem; color: #525252; flex: 1; font-weight: 500; }
.leg-pct { font-size: 0.85rem; font-weight: 600; color: #171717; }

/* TAA */
.taa-rationale { font-size: 0.85rem; color: #525252; line-height: 1.7; margin: 0; }

/* Risk */
.risk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.risk-item {
  text-align: center; padding: 16px 12px;
  background: #fafafa; border-radius: 12px;
}
.risk-label { font-size: 0.72rem; color: #a3a3a3; margin-bottom: 8px; }
.risk-val { font-size: 1.2rem; font-weight: 700; color: #171717; }
.risk-rationale { margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.05); }
.risk-rationale p { font-size: 0.82rem; color: #737373; line-height: 1.6; margin: 0; }

/* Reliability */
.reliability-score { display: flex; align-items: center; justify-content: space-around; padding: 20px 0; }
.score-ring { position: relative; width: 120px; height: 120px; }
.ring-svg { width: 100%; height: 100%; }
.ring-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.ring-val { font-size: 1.8rem; font-weight: 800; color: #171717; line-height: 1; }
.ring-label { font-size: 0.65rem; color: #a3a3a3; letter-spacing: 0.06em; }
.reliability-level { text-align: center; }
.level-badge {
  display: inline-block; padding: 6px 16px;
  background: #171717; color: #fff;
  font-size: 0.9rem; font-weight: 600; border-radius: 8px;
}
.level-desc { font-size: 0.72rem; color: #a3a3a3; margin-top: 8px; }

@media (min-width: 768px) {
  .portfolio-content { padding: 24px 32px 40px; }
  .summary-grid { grid-template-columns: repeat(4, 1fr); }
}
</style>

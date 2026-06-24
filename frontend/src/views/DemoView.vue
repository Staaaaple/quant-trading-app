<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref<'empty' | 'dashboard'>('empty')

const userName = 'User_01'
const totalAssets = '¥128,500'
const totalReturn = '+12.5%'
const healthScore = 78
const lifespanMonths = 15
const marketCycle = '复苏期'
const marketScore = '+42'
const marketMood = '中性偏乐观'
</script>

<template>
  <div class="demo-page">
    <!-- Layered textures -->
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>
    <div class="texture-spotlight"></div>

    <!-- Top Bar -->
    <header class="topbar">
      <div class="topbar-inner">
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
        <div class="user-pill">
          <span class="user-avatar">{{ userName[0] }}</span>
          <span class="user-name">{{ userName }}</span>
          <svg class="user-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
    </header>

    <!-- Tab Switcher -->
    <div class="tab-switcher">
      <button :class="['tab-btn', { active: activeTab === 'empty' }]" @click="activeTab = 'empty'">空状态</button>
      <button :class="['tab-btn', { active: activeTab === 'dashboard' }]" @click="activeTab = 'dashboard'">Dashboard</button>
    </div>

    <!-- ======== EMPTY STATE ======== -->
    <div v-if="activeTab === 'empty'" class="content">
      <!-- Hero with massive typography -->
      <div class="hero-empty">
        <div class="hero-glow"></div>
        <div class="hero-visual">
          <svg viewBox="0 0 400 260" class="hero-svg">
            <defs>
              <linearGradient id="coneGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#262626"/>
                <stop offset="100%" stop-color="#0a0a0a"/>
              </linearGradient>
              <linearGradient id="barGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#525252"/>
                <stop offset="100%" stop-color="#171717"/>
              </linearGradient>
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>
            <ellipse cx="200" cy="210" rx="130" ry="28" fill="none" stroke="#262626" stroke-width="1"/>
            <ellipse cx="200" cy="200" rx="110" ry="23" fill="none" stroke="#333" stroke-width="1"/>
            <ellipse cx="200" cy="190" rx="90" ry="18" fill="url(#coneGrad)" stroke="#404040" stroke-width="1"/>
            <path d="M155 190 L200 85 L245 190 Z" fill="#141414" stroke="#525252" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M177 190 L200 125 L223 190 Z" fill="#1f1f1f" opacity="0.5"/>
            <line x1="200" y1="85" x2="200" y2="55" stroke="#737373" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="200" cy="52" r="3" fill="#a3a3a3" filter="url(#glow)">
              <animate attributeName="cy" values="52;48;52" dur="2.5s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="1;0.5;1" dur="2.5s" repeatCount="indefinite"/>
            </circle>
            <rect x="65" y="130" width="10" height="55" rx="5" fill="url(#barGrad)" opacity="0.7">
              <animate attributeName="height" values="55;75;55" dur="3.2s" repeatCount="indefinite"/>
              <animate attributeName="y" values="130;110;130" dur="3.2s" repeatCount="indefinite"/>
            </rect>
            <rect x="82" y="110" width="10" height="75" rx="5" fill="url(#barGrad)" opacity="0.5">
              <animate attributeName="height" values="75;95;75" dur="2.8s" repeatCount="indefinite"/>
              <animate attributeName="y" values="110;90;110" dur="2.8s" repeatCount="indefinite"/>
            </rect>
            <rect x="308" y="120" width="10" height="65" rx="5" fill="url(#barGrad)" opacity="0.6">
              <animate attributeName="height" values="65;85;65" dur="3.5s" repeatCount="indefinite"/>
              <animate attributeName="y" values="120;100;120" dur="3.5s" repeatCount="indefinite"/>
            </rect>
            <rect x="325" y="140" width="10" height="45" rx="5" fill="url(#barGrad)" opacity="0.4">
              <animate attributeName="height" values="45;65;45" dur="2.5s" repeatCount="indefinite"/>
              <animate attributeName="y" values="140;120;140" dur="2.5s" repeatCount="indefinite"/>
            </rect>
            <line x1="95" y1="165" x2="140" y2="180" stroke="#333" stroke-width="0.8" stroke-dasharray="3 3"/>
            <line x1="260" y1="180" x2="305" y2="165" stroke="#333" stroke-width="0.8" stroke-dasharray="3 3"/>
          </svg>
        </div>

        <h1 class="hero-title">
          <span class="gradient-text">构建你的投资组合</span>
        </h1>
        <p class="hero-desc">基于市场五层信号模型，AI 为你定制策略配置</p>
      </div>

      <!-- Feature cards with bold shadows -->
      <div class="feature-list">
        <div class="feature-card">
          <div class="feature-num">01</div>
          <div class="feature-line"></div>
          <div class="feature-content">
            <div class="feature-title">投资者画像</div>
            <div class="feature-desc">15 维向量刻画风险偏好与行为特征</div>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </div>
        <div class="feature-card">
          <div class="feature-num">02</div>
          <div class="feature-line"></div>
          <div class="feature-content">
            <div class="feature-title">组合生成</div>
            <div class="feature-desc">Hybrid 引擎动态匹配策略与标的</div>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </div>
        <div class="feature-card">
          <div class="feature-num">03</div>
          <div class="feature-line"></div>
          <div class="feature-content">
            <div class="feature-title">全链路服务</div>
            <div class="feature-desc">从画像到调仓的全程量化陪伴</div>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </div>
      </div>

      <!-- Bold CTA -->
      <button class="btn-primary">
        <span>开始画像</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      </button>

      <p class="subline">
        <span class="pulse-dot"></span>
        本周已有 <strong>147</strong> 位用户完成画像
      </p>
    </div>

    <!-- ======== DASHBOARD ======== -->
    <div v-else class="content">
      <!-- Market Card with gradient border -->
      <div class="card market-card">
        <div class="card-glow"></div>
        <div class="card-inner">
          <div class="card-top">
            <span class="card-label">MARKET STATE</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </div>
          <div class="market-body">
            <div class="market-info">
              <div class="market-cycle">
                <span class="cycle-badge">{{ marketCycle }}</span>
                <span class="cycle-dot"></span>
              </div>
              <div class="market-mood">{{ marketMood }}</div>
            </div>
            <div class="market-score-box">
              <span class="score-val">{{ marketScore }}</span>
              <span class="score-label">SCORE</span>
            </div>
          </div>
          <div class="market-tags">
            <span class="tag">地缘风险: 中</span>
            <span class="tag tag-active">科技: 高景气</span>
            <span class="tag tag-active">AI 趋势 ↑</span>
          </div>
        </div>
      </div>

      <!-- Portfolio Card -->
      <div class="card portfolio-card">
        <div class="card-glow"></div>
        <div class="card-inner">
          <div class="card-top">
            <span class="card-label">PORTFOLIO</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </div>
          <div class="portfolio-body">
            <div class="stats-row">
              <div class="stat">
                <div class="stat-label">总资产</div>
                <div class="stat-val">{{ totalAssets }}</div>
              </div>
              <div class="stat">
                <div class="stat-label">累计收益</div>
                <div class="stat-val stat-up">{{ totalReturn }}</div>
              </div>
            </div>
            <div class="chart-wrap">
              <svg viewBox="0 0 320 70" preserveAspectRatio="none" class="chart-svg">
                <defs>
                  <linearGradient id="chartArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#171717" stop-opacity="0.12"/>
                    <stop offset="100%" stop-color="#171717" stop-opacity="0"/>
                  </linearGradient>
                </defs>
                <path d="M0,55 Q25,52 50,48 T100,42 T150,38 T200,30 T250,25 T320,18" fill="none" stroke="#171717" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M0,55 Q25,52 50,48 T100,42 T150,38 T200,30 T250,25 T320,18 L320,70 L0,70 Z" fill="url(#chartArea)"/>
              </svg>
            </div>
            <div class="meta-row">
              <div class="meta-item">
                <span class="meta-dot meta-green"></span>
                <span>健康度 {{ healthScore }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-dot meta-amber"></span>
                <span>寿命 {{ lifespanMonths }} 月</span>
              </div>
            </div>
          </div>
          <div class="alert-box">
            <span class="alert-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
            </span>
            <span class="alert-txt">黄金 ETF 策略寿命剩余 2 月</span>
            <span class="alert-link">查看替代</span>
          </div>
        </div>
      </div>

      <!-- Action Grid with strong depth -->
      <div class="action-grid">
        <button class="action-cell">
          <div class="action-icon-wrap">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
          </div>
          <span>调整画像</span>
        </button>
        <button class="action-cell">
          <div class="action-icon-wrap">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          </div>
          <span>今日操作</span>
        </button>
        <button class="action-cell">
          <div class="action-icon-wrap">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
          </div>
          <span>市场信号</span>
        </button>
        <button class="action-cell">
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
                <circle cx="60" cy="60" r="46" fill="none" stroke="#171717" stroke-width="10" stroke-linecap="round" stroke-dasharray="145 289" stroke-dashoffset="0" transform="rotate(-90 60 60)"/>
                <circle cx="60" cy="60" r="46" fill="none" stroke="#404040" stroke-width="10" stroke-linecap="round" stroke-dasharray="113 289" stroke-dashoffset="-145" transform="rotate(-90 60 60)"/>
                <circle cx="60" cy="60" r="46" fill="none" stroke="#737373" stroke-width="10" stroke-linecap="round" stroke-dasharray="39 289" stroke-dashoffset="-258" transform="rotate(-90 60 60)"/>
                <circle cx="60" cy="60" r="46" fill="none" stroke="#a3a3a3" stroke-width="10" stroke-linecap="round" stroke-dasharray="26 289" stroke-dashoffset="-297" transform="rotate(-90 60 60)"/>
              </svg>
              <div class="donut-center">
                <div class="donut-label">股票</div>
                <div class="donut-val">45%</div>
              </div>
            </div>
            <div class="alloc-legend">
              <div class="leg-row">
                <span class="leg-dot" style="background:#171717"></span>
                <span class="leg-name">股票</span>
                <span class="leg-pct">45%</span>
              </div>
              <div class="leg-row">
                <span class="leg-dot" style="background:#404040"></span>
                <span class="leg-name">债券</span>
                <span class="leg-pct">35%</span>
              </div>
              <div class="leg-row">
                <span class="leg-dot" style="background:#737373"></span>
                <span class="leg-name">商品</span>
                <span class="leg-pct">12%</span>
              </div>
              <div class="leg-row">
                <span class="leg-dot" style="background:#a3a3a3"></span>
                <span class="leg-name">现金</span>
                <span class="leg-pct">8%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Tab Bar -->
    <nav class="tabbar">
      <div class="tabbar-item active">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>首页</span>
      </div>
      <div class="tabbar-item">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        <span>市场</span>
      </div>
      <div class="tabbar-item">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
        <span>组合</span>
      </div>
      <div class="tabbar-item">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43-.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
        <span>设置</span>
      </div>
    </nav>
  </div>
</template>

<style scoped>
/* ======= Base ======= */
.demo-page {
  min-height: 100vh;
  background: #fafafa;
  font-family: 'Inter', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
  color: #171717;
  display: flex;
  flex-direction: column;
  position: relative;
  padding-bottom: 88px;
  -webkit-font-smoothing: antialiased;
}

/* ======= Textures ======= */
.texture-noise {
  position: fixed;
  inset: 0;
  z-index: 0;
  opacity: 0.035;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 128px 128px;
}

.texture-grid {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(0,0,0,0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.028) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
}

.texture-spotlight {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,0,0,0.04) 0%, transparent 70%),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(0,0,0,0.02) 0%, transparent 60%);
}

/* ======= Top Bar ======= */
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(250, 250, 250, 0.82);
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.topbar-inner {
  max-width: 720px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #171717;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.brand-name {
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #171717;
}

.brand-muted {
  font-weight: 400;
  color: #a3a3a3;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 14px 4px 4px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 999px;
  font-size: 0.78rem;
  color: #525252;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-pill:hover {
  border-color: rgba(0,0,0,0.12);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #171717;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-name {
  font-weight: 500;
  letter-spacing: -0.01em;
}

.user-chevron {
  color: #d4d4d4;
  transition: color 0.2s;
}

.user-pill:hover .user-chevron {
  color: #737373;
}

/* ======= Tab Switcher ======= */
.tab-switcher {
  display: flex;
  justify-content: center;
  gap: 6px;
  padding: 16px 24px 8px;
  position: relative;
  z-index: 1;
}

.tab-btn {
  padding: 8px 18px;
  border-radius: 999px;
  border: 1px solid transparent;
  background: transparent;
  color: #a3a3a3;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  letter-spacing: 0.02em;
}

.tab-btn:hover {
  background: rgba(0,0,0,0.04);
  color: #525252;
}

.tab-btn.active {
  background: #171717;
  color: #fff;
  border-color: #171717;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}

/* ======= Content ======= */
.content {
  max-width: 720px;
  margin: 0 auto;
  padding: 16px 24px 32px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: relative;
  z-index: 1;
}

/* ======= Empty State ======= */
.hero-empty {
  text-align: center;
  padding: 20px 0 8px;
  position: relative;
}

.hero-glow {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 300px;
  height: 200px;
  background: radial-gradient(ellipse, rgba(0,0,0,0.04) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.hero-visual {
  width: 280px;
  height: 200px;
  margin: 0 auto 20px;
  position: relative;
  z-index: 1;
}

.hero-svg {
  width: 100%;
  height: 100%;
}

.hero-title {
  font-size: 2rem;
  font-weight: 800;
  color: #171717;
  margin: 0 0 10px;
  letter-spacing: -0.04em;
  line-height: 1.1;
  position: relative;
  z-index: 1;
}

.gradient-text {
  background: linear-gradient(135deg, #171717 0%, #525252 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 0.88rem;
  color: #737373;
  margin: 0;
  line-height: 1.6;
  font-weight: 400;
}

/* Feature cards — bold, with depth */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feature-card {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 18px 20px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow:
    0 1px 2px rgba(0,0,0,0.02),
    0 4px 12px rgba(0,0,0,0.02);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.04), transparent);
}

.feature-card:hover {
  border-color: rgba(0,0,0,0.1);
  box-shadow:
    0 2px 4px rgba(0,0,0,0.03),
    0 8px 24px rgba(0,0,0,0.06);
  transform: translateY(-2px);
}

.feature-card:hover svg {
  color: #171717;
  transform: translateX(3px);
}

.feature-card svg {
  color: #d4d4d4;
  flex-shrink: 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-num {
  font-size: 0.65rem;
  font-weight: 700;
  color: #e5e5e5;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.08em;
  min-width: 22px;
  text-align: center;
}

.feature-line {
  width: 1px;
  height: 28px;
  background: rgba(0,0,0,0.05);
  margin: 0 14px;
  flex-shrink: 0;
}

.feature-content {
  flex: 1;
}

.feature-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: #171717;
  letter-spacing: -0.01em;
}

.feature-desc {
  font-size: 0.76rem;
  color: #a3a3a3;
  margin-top: 3px;
}

/* CTA — bold, commanding */
.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 17px 24px;
  border: none;
  border-radius: 16px;
  background: #171717;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  letter-spacing: -0.01em;
  margin-top: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  position: relative;
  overflow: hidden;
}

.btn-primary::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  transition: left 0.5s ease;
}

.btn-primary:hover {
  background: #262626;
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.18);
}

.btn-primary:hover::before {
  left: 100%;
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}

.subline {
  text-align: center;
  font-size: 0.74rem;
  color: #a3a3a3;
  margin: 4px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.pulse-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
  animation: pulse-dot 2.2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.3); }
  50% { opacity: 0.6; box-shadow: 0 0 0 4px rgba(34,197,94,0); }
}

/* ======= Cards (Dashboard) ======= */
.card {
  position: relative;
  border-radius: 20px;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow:
    0 1px 2px rgba(0,0,0,0.02),
    0 4px 16px rgba(0,0,0,0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.card:hover {
  box-shadow:
    0 2px 4px rgba(0,0,0,0.03),
    0 12px 32px rgba(0,0,0,0.06);
  transform: translateY(-1px);
  border-color: rgba(0,0,0,0.08);
}

.card-glow {
  position: absolute;
  top: -40%;
  right: -20%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(0,0,0,0.025) 0%, transparent 70%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.card:hover .card-glow {
  opacity: 1;
}

.card-inner {
  position: relative;
  z-index: 1;
  padding: 20px 22px;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-label {
  font-size: 0.62rem;
  font-weight: 700;
  color: #d4d4d4;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.card-top svg {
  color: #e5e5e5;
  transition: color 0.2s;
}

.card:hover .card-top svg {
  color: #a3a3a3;
}

/* Market Card */
.market-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.market-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.market-cycle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cycle-badge {
  display: inline-block;
  padding: 5px 13px;
  background: #171717;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  letter-spacing: -0.01em;
}

.cycle-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34,197,94,0.15);
  animation: pulse-dot 2.2s ease-in-out infinite;
}

.market-mood {
  font-size: 0.82rem;
  color: #737373;
}

.market-score-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.score-val {
  font-size: 1.8rem;
  font-weight: 800;
  color: #171717;
  line-height: 1;
  letter-spacing: -0.03em;
}

.score-label {
  font-size: 0.58rem;
  font-weight: 700;
  color: #d4d4d4;
  letter-spacing: 0.12em;
}

.market-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: 0.72rem;
  font-weight: 500;
  padding: 5px 11px;
  border-radius: 8px;
  background: #f5f5f5;
  color: #525252;
  border: 1px solid rgba(0,0,0,0.04);
  transition: all 0.2s ease;
}

.tag-active {
  background: #f0fdf4;
  color: #166534;
  border-color: rgba(34,197,94,0.15);
}

/* Portfolio Card */
.stats-row {
  display: flex;
  gap: 32px;
  margin-bottom: 14px;
}

.stat-label {
  font-size: 0.68rem;
  color: #a3a3a3;
  margin-bottom: 5px;
  letter-spacing: 0.03em;
  font-weight: 500;
}

.stat-val {
  font-size: 1.45rem;
  font-weight: 700;
  color: #171717;
  letter-spacing: -0.02em;
}

.stat-up {
  color: #171717;
}

.chart-wrap {
  height: 52px;
  margin-bottom: 14px;
}

.chart-svg {
  width: 100%;
  height: 100%;
}

.meta-row {
  display: flex;
  gap: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.78rem;
  color: #737373;
  font-weight: 500;
}

.meta-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.meta-green { background: #22c55e; }
.meta-amber { background: #d97706; }

/* Alert Box */
.alert-box {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 16px;
  padding: 13px 15px;
  background: linear-gradient(90deg, #fafafa, #f5f5f5);
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.04);
  position: relative;
  overflow: hidden;
}

.alert-box::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #ef4444;
  border-radius: 12px 0 0 12px;
}

.alert-icon {
  color: #ef4444;
  display: flex;
  align-items: center;
  margin-left: 6px;
}

.alert-txt {
  font-size: 0.8rem;
  color: #525252;
  flex: 1;
  font-weight: 500;
}

.alert-link {
  font-size: 0.75rem;
  font-weight: 600;
  color: #171717;
  cursor: pointer;
  white-space: nowrap;
  letter-spacing: -0.01em;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(0,0,0,0.03);
  transition: background 0.2s;
}

.alert-link:hover {
  background: rgba(0,0,0,0.06);
}

/* Action Grid */
.action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.action-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 22px 12px;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 16px;
  box-shadow:
    0 1px 2px rgba(0,0,0,0.02),
    0 4px 12px rgba(0,0,0,0.02);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  color: #525252;
  position: relative;
  overflow: hidden;
}

.action-cell::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.03), transparent);
}

.action-cell:hover {
  box-shadow:
    0 2px 4px rgba(0,0,0,0.03),
    0 8px 24px rgba(0,0,0,0.05);
  transform: translateY(-2px);
  border-color: rgba(0,0,0,0.1);
  color: #171717;
}

.action-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #fafafa;
  border: 1px solid rgba(0,0,0,0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a3a3a3;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-cell:hover .action-icon-wrap {
  background: #171717;
  border-color: #171717;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.action-cell span:last-child {
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: -0.01em;
}

/* Allocation Card */
.alloc-body {
  display: flex;
  align-items: center;
  gap: 28px;
}

.donut-wrap {
  position: relative;
  width: 110px;
  height: 110px;
  flex-shrink: 0;
}

.donut-svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.04));
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.donut-label {
  font-size: 0.62rem;
  color: #a3a3a3;
  letter-spacing: 0.06em;
  font-weight: 500;
}

.donut-val {
  font-size: 1.2rem;
  font-weight: 700;
  color: #171717;
  letter-spacing: -0.02em;
}

.alloc-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.leg-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.leg-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.leg-name {
  font-size: 0.82rem;
  color: #525252;
  flex: 1;
  font-weight: 500;
}

.leg-pct {
  font-size: 0.82rem;
  font-weight: 600;
  color: #171717;
  font-variant-numeric: tabular-nums;
}

/* ======= Bottom Tab Bar ======= */
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  border-top: 1px solid rgba(0,0,0,0.05);
  display: flex;
  justify-content: space-around;
  padding: 8px 0 calc(8px + env(safe-area-inset-bottom, 0px));
}

.tabbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 20px;
  color: #d4d4d4;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 12px;
  position: relative;
}

.tabbar-item:hover {
  color: #737373;
}

.tabbar-item.active {
  color: #171717;
}

.tabbar-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: #171717;
  border-radius: 0 0 3px 3px;
}

.tabbar-item span {
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* ======= Responsive ======= */
@media (min-width: 768px) {
  .content {
    padding: 24px 32px 40px;
  }

  .hero-title {
    font-size: 2.6rem;
  }

  .hero-visual {
    width: 340px;
    height: 240px;
  }

  .feature-list {
    flex-direction: row;
    gap: 12px;
  }

  .feature-card {
    flex: 1;
    flex-direction: column;
    text-align: center;
    padding: 28px 20px;
    gap: 12px;
  }

  .feature-line {
    display: none;
  }

  .feature-num {
    font-size: 0.7rem;
  }

  .feature-card svg {
    margin-top: 8px;
  }

  .action-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .tabbar {
    max-width: 720px;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 16px 16px 0 0;
    border: 1px solid rgba(0,0,0,0.05);
    border-bottom: none;
    bottom: 12px;
    box-shadow: 0 -4px 24px rgba(0,0,0,0.04);
  }
}
</style>
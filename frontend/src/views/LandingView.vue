<script setup lang="ts">
const emit = defineEmits<{
  start: []
}>()
</script>

<template>
  <div class="landing-page">
    <!-- Layered textures -->
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>
    <div class="texture-spotlight"></div>

    <!-- Content -->
    <div class="content">
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
        <div class="feature-card" @click="emit('start')">
          <div class="feature-num">01</div>
          <div class="feature-line"></div>
          <div class="feature-content">
            <div class="feature-title">投资者画像</div>
            <div class="feature-desc">15 维向量刻画风险偏好与行为特征</div>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </div>
        <div class="feature-card" @click="emit('start')">
          <div class="feature-num">02</div>
          <div class="feature-line"></div>
          <div class="feature-content">
            <div class="feature-title">组合生成</div>
            <div class="feature-desc">Hybrid 引擎动态匹配策略与标的</div>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </div>
        <div class="feature-card" @click="emit('start')">
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
      <button class="btn-primary" @click="emit('start')">
        <span>开始画像</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      </button>

      <p class="subline">
        <span class="pulse-dot"></span>
        本周已有 <strong>147</strong> 位用户完成画像
      </p>
    </div>
  </div>
</template>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: #fafafa;
  font-family: 'Inter', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
  color: #171717;
  display: flex;
  flex-direction: column;
  position: relative;
  -webkit-font-smoothing: antialiased;
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
  background-image:
    linear-gradient(rgba(0,0,0,0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.028) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
}
.texture-spotlight {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,0,0,0.04) 0%, transparent 70%),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(0,0,0,0.02) 0%, transparent 60%);
}

/* Content */
.content {
  flex: 1;
  max-width: 720px; margin: 0 auto; padding: 16px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

/* Empty State */
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
  position: relative; z-index: 1;
}
.gradient-text {
  background: linear-gradient(135deg, #171717 0%, #525252 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-desc { font-size: 0.88rem; color: #737373; margin: 0; line-height: 1.6; font-weight: 400; }

/* Feature cards */
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
.btn-primary::before {
  content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  transition: left 0.5s ease;
}
.btn-primary:hover { background: #262626; transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.18); }
.btn-primary:hover::before { left: 100%; }
.btn-primary:active { transform: translateY(0); box-shadow: 0 2px 8px rgba(0,0,0,0.12); }

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

/* Responsive */
@media (min-width: 768px) {
  .content { padding: 24px 32px 40px; }
  .hero-title { font-size: 2.6rem; }
  .hero-visual { width: 340px; height: 240px; }
  .feature-list { flex-direction: row; gap: 12px; }
  .feature-card { flex: 1; flex-direction: column; text-align: center; padding: 28px 20px; gap: 12px; }
  .feature-line { display: none; }
  .feature-num { font-size: 0.7rem; }
  .feature-card svg { margin-top: 8px; }
}
</style>

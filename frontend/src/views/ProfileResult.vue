<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { profileApi, type InvestorProfile } from '@/api/profile'

const router = useRouter()
const userStore = useUserStore()

const profile = ref<InvestorProfile | null>(null)
const loading = ref(true)

const radarDimensions = [
  { key: 'risk_tolerance', label: '风险承受' },
  { key: 'loss_aversion', label: '损失厌恶' },
  { key: 'herding_tendency', label: '从众倾向' },
  { key: 'overconfidence', label: '过度自信' },
  { key: 'delayed_gratification', label: '延迟满足' },
  { key: 'security_need', label: '安全需求' },
]

async function loadProfile() {
  loading.value = true
  try {
    if (!userStore.currentUserId) {
      await userStore.loadUsers()
    }
    if (userStore.currentUserId) {
      const p = await profileApi.getMine()
      if (p) profile.value = p
    }
  } catch (e) {
    console.error('Failed to load profile:', e)
  } finally {
    loading.value = false
  }
}

function goPortfolio() {
  router.push('/portfolio')
}

function goHome() {
  router.push('/')
}

function getRadarValue(key: string): number {
  if (!profile.value) return 0.5
  return (profile.value as any)[key] ?? 0.5
}

function getRiskLabel(): string {
  if (!profile.value?.risk_label) return '稳健型'
  const map: Record<string, string> = {
    '保守型': '保守型',
    '稳健型': '稳健型',
    '平衡型': '平衡型',
    '积极型': '积极型',
    '激进型': '激进型',
  }
  return map[profile.value.risk_label] || profile.value.risk_label
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <div class="result-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <button class="back-btn" @click="goHome">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-label">PROFILE RESULT</span>
          <span class="header-name">画像结果</span>
        </div>
        <div class="header-placeholder"></div>
      </div>
    </header>

    <!-- Content -->
    <div class="result-content">
      <div v-if="loading" class="loading-state">加载画像结果...</div>

      <template v-else-if="profile">
        <!-- Profile Label -->
        <div class="profile-hero">
          <div class="profile-badge">
            <span class="profile-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </span>
            <span class="profile-label-text">{{ getRiskLabel() }}投资者</span>
          </div>
          <h1 class="profile-title">
            你的投资画像已生成
          </h1>
          <p class="profile-desc">
            基于 {{ Object.keys(profile.answers_json).length }} 题问卷，AI 分析了你的风险偏好与行为特征
          </p>
        </div>

        <!-- Radar Chart -->
        <div class="card radar-card">
          <div class="card-inner">
            <div class="card-top">
              <span class="card-label">BEHAVIOR RADAR</span>
            </div>
            <div class="radar-chart">
              <svg viewBox="0 0 200 200" class="radar-svg">
                <!-- Grid -->
                <polygon points="100,20 170,60 170,140 100,180 30,140 30,60" fill="none" stroke="#f0f0f0" stroke-width="1"/>
                <polygon points="100,40 150,70 150,130 100,160 50,130 50,70" fill="none" stroke="#f0f0f0" stroke-width="1"/>
                <polygon points="100,60 130,80 130,120 100,140 70,120 70,80" fill="none" stroke="#f0f0f0" stroke-width="1"/>
                <!-- Axes -->
                <line x1="100" y1="100" x2="100" y2="20" stroke="#e5e5e5" stroke-width="1"/>
                <line x1="100" y1="100" x2="170" y2="60" stroke="#e5e5e5" stroke-width="1"/>
                <line x1="100" y1="100" x2="170" y2="140" stroke="#e5e5e5" stroke-width="1"/>
                <line x1="100" y1="100" x2="100" y2="180" stroke="#e5e5e5" stroke-width="1"/>
                <line x1="100" y1="100" x2="30" y2="140" stroke="#e5e5e5" stroke-width="1"/>
                <line x1="100" y1="100" x2="30" y2="60" stroke="#e5e5e5" stroke-width="1"/>
                <!-- Data polygon -->
                <polygon
                  :points="radarDimensions.map((d, i) => {
                    const angle = (Math.PI * 2 * i / 6) - Math.PI / 2
                    const val = getRadarValue(d.key)
                    const r = 30 + val * 60
                    return `${100 + r * Math.cos(angle)},${100 + r * Math.sin(angle)}`
                  }).join(' ')"
                  fill="rgba(23,23,23,0.08)"
                  stroke="#171717"
                  stroke-width="1.5"
                />
                <!-- Data points -->
                <circle
                  v-for="(d, i) in radarDimensions"
                  :key="i"
                  :cx="100 + (30 + getRadarValue(d.key) * 60) * Math.cos((Math.PI * 2 * i / 6) - Math.PI / 2)"
                  :cy="100 + (30 + getRadarValue(d.key) * 60) * Math.sin((Math.PI * 2 * i / 6) - Math.PI / 2)"
                  r="3"
                  fill="#171717"
                />
                <!-- Labels -->
                <text x="100" y="14" text-anchor="middle" font-size="8" fill="#a3a3a3">风险承受</text>
                <text x="180" y="55" text-anchor="start" font-size="8" fill="#a3a3a3">损失厌恶</text>
                <text x="180" y="155" text-anchor="start" font-size="8" fill="#a3a3a3">从众倾向</text>
                <text x="100" y="196" text-anchor="middle" font-size="8" fill="#a3a3a3">安全需求</text>
                <text x="20" y="155" text-anchor="end" font-size="8" fill="#a3a3a3">延迟满足</text>
                <text x="20" y="55" text-anchor="end" font-size="8" fill="#a3a3a3">过度自信</text>
              </svg>
            </div>
          </div>
        </div>

        <!-- Dimension Cards -->
        <div class="dimension-list">
          <div v-for="dim in radarDimensions" :key="dim.key" class="dimension-card">
            <div class="dimension-info">
              <div class="dimension-name">{{ dim.label }}</div>
              <div class="dimension-bar">
                <div class="dimension-fill" :style="{ width: `${getRadarValue(dim.key) * 100}%` }"></div>
              </div>
            </div>
            <div class="dimension-score">{{ Math.round(getRadarValue(dim.key) * 100) }}</div>
          </div>
        </div>

        <!-- Suggested Allocation Preview -->
        <div class="card preview-card">
          <div class="card-inner">
            <div class="card-top">
              <span class="card-label">SUGGESTED ALLOCATION</span>
            </div>
            <div class="preview-alloc">
              <div class="preview-item">
                <span class="preview-dot" style="background:#171717"></span>
                <span class="preview-name">股票</span>
                <span class="preview-pct">45-60%</span>
              </div>
              <div class="preview-item">
                <span class="preview-dot" style="background:#404040"></span>
                <span class="preview-name">债券</span>
                <span class="preview-pct">25-35%</span>
              </div>
              <div class="preview-item">
                <span class="preview-dot" style="background:#737373"></span>
                <span class="preview-name">商品</span>
                <span class="preview-pct">8-12%</span>
              </div>
              <div class="preview-item">
                <span class="preview-dot" style="background:#a3a3a3"></span>
                <span class="preview-name">现金</span>
                <span class="preview-pct">5-8%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- CTA -->
        <button class="btn-primary" @click="goPortfolio">
          <span>查看完整组合</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </button>

        <button class="btn-secondary" @click="goHome">
          <span>返回首页</span>
        </button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.result-page {
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
.result-content {
  max-width: 720px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}
.loading-state { text-align: center; padding: 60px 0; color: #a3a3a3; font-size: 0.9rem; }

/* Profile Hero */
.profile-hero { text-align: center; padding: 16px 0 8px; }
.profile-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 18px; background: #171717; color: #fff;
  border-radius: 999px; margin-bottom: 16px;
}
.profile-icon { display: flex; align-items: center; }
.profile-label-text { font-size: 0.85rem; font-weight: 600; letter-spacing: -0.01em; }
.profile-title { font-size: 1.5rem; font-weight: 700; color: #171717; margin: 0 0 8px; letter-spacing: -0.02em; }
.profile-desc { font-size: 0.82rem; color: #737373; margin: 0; }

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
.card-inner { position: relative; z-index: 1; padding: 20px 22px; }
.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-label { font-size: 0.62rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; text-transform: uppercase; }

/* Radar */
.radar-chart { display: flex; justify-content: center; padding: 8px 0; }
.radar-svg { width: 200px; height: 200px; }

/* Dimensions */
.dimension-list { display: flex; flex-direction: column; gap: 10px; }
.dimension-card {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 18px; background: #fff;
  border-radius: 16px; border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.dimension-info { flex: 1; }
.dimension-name { font-size: 0.85rem; font-weight: 500; color: #171717; margin-bottom: 8px; }
.dimension-bar { height: 4px; background: #f0f0f0; border-radius: 999px; overflow: hidden; }
.dimension-fill { height: 100%; background: #171717; border-radius: 999px; transition: width 0.6s ease; }
.dimension-score { font-size: 1rem; font-weight: 700; color: #171717; min-width: 32px; text-align: right; }

/* Preview */
.preview-alloc { display: flex; flex-direction: column; gap: 12px; }
.preview-item { display: flex; align-items: center; gap: 10px; }
.preview-dot { width: 8px; height: 8px; border-radius: 2px; }
.preview-name { font-size: 0.85rem; color: #525252; flex: 1; font-weight: 500; }
.preview-pct { font-size: 0.85rem; font-weight: 600; color: #171717; }

/* Buttons */
.btn-primary {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 17px 24px; border: none; border-radius: 16px;
  background: #171717; color: #fff; font-family: inherit;
  font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
  cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary:hover { background: #262626; transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.18); }

.btn-secondary {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 24px; border: 1px solid rgba(0,0,0,0.08); border-radius: 16px;
  background: #fff; color: #525252; font-family: inherit;
  font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: all 0.2s ease;
}
.btn-secondary:hover { border-color: rgba(0,0,0,0.12); color: #171717; }

@media (min-width: 768px) {
  .result-content { padding: 24px 32px 40px; }
}
</style>

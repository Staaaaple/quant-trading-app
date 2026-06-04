<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { profileApi, type InvestorProfile } from '@/api/profile'

const router = useRouter()
const userStore = useUserStore()

const profile = ref<InvestorProfile | null>(null)
const loading = ref(true)

// 投资风格描述映射
const riskStyleMap: Record<string, { title: string; desc: string; allocation: string }> = {
  '保守型': {
    title: '稳健守护者',
    desc: '您偏好低风险、稳定收益的投资方式，注重本金安全，适合以债券和现金为主的防御型配置。',
    allocation: '建议以债券型基金、货币基金为主，股票配置不超过20%',
  },
  '稳健型': {
    title: '平衡配置者',
    desc: '您愿意承担适度风险以获取更好回报，追求收益与风险的平衡，适合股债均衡的配置策略。',
    allocation: '建议股债均衡配置，股票40%-60%，债券30%-50%，保留10%现金',
  },
  '积极型': {
    title: '成长追求者',
    desc: '您对市场有一定理解，愿意承担较高风险以追求超额收益，适合偏股型的成长配置。',
    allocation: '建议股票60%-80%，债券15%-30%，可适当配置行业主题基金',
  },
  '激进型': {
    title: '机会捕捉者',
    desc: '您具备较强的风险承受能力，善于把握市场机会，适合高弹性的进攻型配置。',
    allocation: '建议股票80%以上，可配置高弹性品种，保留少量现金应对波动',
  },
}

const timeStyleMap: Record<string, string> = {
  '短期': '关注1-3个月的市场机会，适合波段操作',
  '中期': '关注3-12个月的趋势变化，适合趋势跟踪',
  '长期': '关注1年以上的价值投资，适合长期持有',
}

const styleInfo = computed(() => {
  const label = profile.value?.risk_label || '稳健型'
  return riskStyleMap[label] || riskStyleMap['稳健型']
})

const timeInfo = computed(() => {
  const label = profile.value?.time_horizon_label || '中期'
  return timeStyleMap[label] || timeStyleMap['中期']
})

// 核心特征标签
const coreTraits = computed(() => {
  if (!profile.value) return []
  const p = profile.value
  const traits = []

  // 风险偏好
  if (p.risk_tolerance >= 7) traits.push({ label: '高风险偏好', type: 'risk' })
  else if (p.risk_tolerance <= 3) traits.push({ label: '低风险偏好', type: 'safe' })

  // 损失厌恶
  if (p.loss_aversion >= 7) traits.push({ label: '损失敏感', type: 'safe' })
  else if (p.loss_aversion <= 3) traits.push({ label: '损失钝感', type: 'risk' })

  // 信息处理
  if (p.information_processing >= 7) traits.push({ label: '独立研究', type: 'pro' })
  else if (p.information_processing <= 3) traits.push({ label: '跟随市场', type: 'follow' })

  // 情绪稳定
  if (p.emotional_stability >= 7) traits.push({ label: '情绪稳定', type: 'pro' })
  else if (p.emotional_stability <= 3) traits.push({ label: '情绪敏感', type: 'follow' })

  // 止损纪律
  if (p.stop_loss_discipline >= 7) traits.push({ label: '纪律严明', type: 'pro' })

  // 分散化
  if (p.diversification_preference >= 7) traits.push({ label: '多元配置', type: 'pro' })

  return traits
})

async function loadProfile() {
  loading.value = true
  try {
    if (!userStore.currentUserId) {
      await userStore.loadUsers()
    }
    const p = await profileApi.getMine()
    if (p) profile.value = p
  } catch (e) {
    console.error('Failed to load profile:', e)
  } finally {
    loading.value = false
  }
}

function goMarket() {
  router.push('/market')
}

function goHome() {
  router.push('/')
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <div class="summary-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="summary-header">
      <div class="summary-header-inner">
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
      </div>
    </header>

    <!-- Content -->
    <div class="summary-content">
      <div v-if="loading" class="loading-state">加载中...</div>

      <template v-else-if="profile">
        <!-- 主标题 -->
        <div class="hero-section">
          <div class="hero-badge">画像已生成</div>
          <h1 class="hero-title">您的投资画像</h1>
          <p class="hero-desc">基于18维问卷分析，为您定制的投资风格评估</p>
        </div>

        <!-- 核心标签卡片 -->
        <div class="main-card">
          <div class="card-glow"></div>
          <div class="card-inner">
            <!-- 投资风格 -->
            <div class="style-section">
              <div class="style-label">您的投资偏好是</div>
              <div class="style-title">{{ styleInfo.title }}</div>
              <div class="style-tags">
                <span class="tag tag-primary">{{ profile.risk_label }}</span>
                <span class="tag tag-secondary">{{ profile.time_horizon_label }}投资</span>
                <span class="tag tag-secondary">{{ profile.experience_label }}</span>
              </div>
            </div>

            <!-- 分割线 -->
            <div class="divider"></div>

            <!-- 风格描述 -->
            <div class="desc-section">
              <p class="desc-text">{{ styleInfo.desc }}</p>
            </div>

            <!-- 建议配置 -->
            <div class="allocation-section">
              <div class="allocation-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
                建议投资风格
              </div>
              <p class="allocation-text">{{ styleInfo.allocation }}</p>
            </div>

            <!-- 时间维度 -->
            <div class="time-section">
              <div class="time-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                投资时间视角
              </div>
              <p class="time-text">{{ timeInfo }}</p>
            </div>
          </div>
        </div>

        <!-- 核心特征标签 -->
        <div class="traits-section">
          <div class="traits-label">核心特征</div>
          <div class="traits-list">
            <span
              v-for="trait in coreTraits"
              :key="trait.label"
              :class="['trait-tag', `trait-${trait.type}`]"
            >
              {{ trait.label }}
            </span>
          </div>
        </div>

        <!-- CTA -->
        <div class="cta-section">
          <button class="btn-primary" @click="goMarket">
            <span>下一步，查看当今行情</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/>
              <path d="m12 5 7 7-7 7"/>
            </svg>
          </button>
          <button class="btn-text" @click="goHome">
            返回首页
          </button>
        </div>
      </template>

      <div v-else class="error-state">
        <p>未能加载画像数据</p>
        <button class="btn-primary" @click="goHome">返回首页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary-page {
  min-height: 100vh;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  position: relative;
  padding-bottom: 40px;
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

/* Header */
.summary-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.82);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.summary-header-inner {
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

/* Content */
.summary-content {
  flex: 1;
  max-width: 720px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 20px;
  position: relative; z-index: 1;
}
.loading-state { text-align: center; padding: 60px 0; color: #a3a3a3; font-size: 0.9rem; }

/* Hero */
.hero-section { text-align: center; padding: 20px 0 8px; }
.hero-badge {
  display: inline-block; padding: 6px 14px;
  background: #dcfce7; color: #166534;
  font-size: 0.72rem; font-weight: 700;
  border-radius: 999px; margin-bottom: 14px;
  letter-spacing: 0.02em;
}
.hero-title {
  font-size: 1.8rem; font-weight: 800; color: #171717;
  margin: 0 0 8px; letter-spacing: -0.03em;
}
.hero-desc { font-size: 0.85rem; color: #a3a3a3; margin: 0; }

/* Main Card */
.main-card {
  position: relative; border-radius: 24px; background: #fff;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  overflow: hidden;
}
.card-glow {
  position: absolute; top: -40%; right: -20%;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(0,0,0,0.02) 0%, transparent 70%);
  pointer-events: none;
}
.card-inner { position: relative; z-index: 1; padding: 28px 24px; }

/* Style Section */
.style-section { text-align: center; margin-bottom: 20px; }
.style-label {
  font-size: 0.72rem; font-weight: 700; color: #a3a3a3;
  text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: 10px;
}
.style-title {
  font-size: 1.5rem; font-weight: 800; color: #171717;
  letter-spacing: -0.02em; margin-bottom: 14px;
}
.style-tags { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.tag {
  font-size: 0.78rem; font-weight: 600;
  padding: 6px 14px; border-radius: 10px;
}
.tag-primary {
  background: #171717; color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.tag-secondary {
  background: #f5f5f5; color: #525252;
  border: 1px solid rgba(0,0,0,0.06);
}

/* Divider */
.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.06), transparent);
  margin: 20px 0;
}

/* Desc Section */
.desc-section { margin-bottom: 20px; }
.desc-text {
  font-size: 0.9rem; color: #525252; line-height: 1.7;
  text-align: center; margin: 0;
}

/* Allocation Section */
.allocation-section, .time-section {
  background: #fafafa;
  border-radius: 16px;
  padding: 16px 18px;
  margin-bottom: 12px;
}
.allocation-label, .time-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.78rem; font-weight: 700; color: #171717;
  margin-bottom: 8px;
}
.allocation-label svg, .time-label svg { color: #a3a3a3; }
.allocation-text, .time-text {
  font-size: 0.85rem; color: #525252; line-height: 1.6;
  margin: 0;
}

/* Traits Section */
.traits-section { margin-top: 4px; }
.traits-label {
  font-size: 0.72rem; font-weight: 700; color: #a3a3a3;
  text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: 10px;
}
.traits-list { display: flex; gap: 8px; flex-wrap: wrap; }
.trait-tag {
  font-size: 0.78rem; font-weight: 500;
  padding: 6px 12px; border-radius: 8px;
}
.trait-risk { background: #fef3c7; color: #92400e; }
.trait-safe { background: #dbeafe; color: #1e40af; }
.trait-pro { background: #dcfce7; color: #166534; }
.trait-follow { background: #f3f4f6; color: #4b5563; }

/* CTA */
.cta-section {
  display: flex; flex-direction: column; gap: 12px;
  align-items: center; margin-top: 8px;
}
.btn-primary {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 17px 24px; border: none; border-radius: 16px;
  background: #171717; color: #fff; font-family: inherit;
  font-size: 0.9rem; font-weight: 600; letter-spacing: -0.01em;
  cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary:hover { background: #262626; transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.18); }
.btn-text {
  font-size: 0.85rem; color: #a3a3a3;
  background: transparent; border: none;
  cursor: pointer; padding: 8px;
  transition: color 0.2s;
}
.btn-text:hover { color: #525252; }

/* Error */
.error-state { text-align: center; padding: 60px 0; }
.error-state p { color: #a3a3a3; margin-bottom: 20px; }
</style>

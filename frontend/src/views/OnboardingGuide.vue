<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentStep = ref(0)

const STEPS = [
  {
    title: '了解你的组合策略',
    content: '为什么选这些标的？',
    items: [
      '你是积极型投资者，复苏期适合增配股票',
      '科技行业景气度高，AI趋势强，所以科技ETF占比较高',
      '黄金作为避险资产，对冲地缘政治风险',
    ],
  },
  {
    title: '挑选券商',
    content: '挑选标准（不推具体券商）',
    items: [
      '佣金率 ≤ 0.025%（万2.5）',
      'APP体验好（支持条件单、智能盯盘）',
      '提供基金申购费1折优惠',
      '有研报和投顾服务（小白需要学习资源）',
    ],
  },
  {
    title: '建仓计划',
    content: '分批买入，降低择时风险',
    items: [
      '第1批(本周): 40% 资金 → 买入股票类ETF',
      '第2批(2周后): 35% 资金 → 买入债券类+商品类',
      '第3批(1月后): 25% 资金 → 补齐剩余仓位',
    ],
  },
  {
    title: '日常跟进',
    content: '如何持续管理你的组合',
    items: [
      '每天开盘前查看推送（有操作才推，无操作显示"今日持有"）',
      '每周五查看周报（收益/市场回顾/下周展望）',
      '收到预警时及时查看（策略到期/周期切换/寿命预警）',
      '季度再平衡时确认调仓方案',
    ],
  },
]

function nextStep() {
  if (currentStep.value < STEPS.length - 1) {
    currentStep.value++
  } else {
    finish()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function finish() {
  router.push('/')
}
</script>

<template>
  <div class="onboarding-page">
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="page-header">
      <div class="page-header-inner">
        <div class="header-title">
          <span class="header-label">ONBOARDING</span>
          <span class="header-name">新手指引</span>
        </div>
        <div class="step-counter">
          步骤 {{ currentStep + 1 }}/{{ STEPS.length }}
        </div>
      </div>
      <!-- Progress -->
      <div class="progress-wrap">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }"></div>
        </div>
      </div>
    </header>

    <!-- Content -->
    <div class="onboarding-content">
      <div class="step-card">
        <div class="step-number">0{{ currentStep + 1 }}</div>
        <h2 class="step-title">{{ STEPS[currentStep]?.title }}</h2>
        <p class="step-subtitle">{{ STEPS[currentStep]?.content }}</p>

        <div class="step-items">
          <div v-for="(item, idx) in (STEPS[currentStep]?.items || [])" :key="idx" class="step-item">
            <span class="item-bullet">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span class="item-text">{{ item }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="onboarding-footer">
      <button
        v-if="currentStep > 0"
        class="btn-secondary"
        @click="prevStep"
      >
        上一步
      </button>
      <div v-else></div>

      <button
        class="btn-primary"
        @click="nextStep"
      >
        <span v-if="currentStep < STEPS.length - 1">下一步</span>
        <span v-else>完成，进入首页</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12h14"/>
          <path d="m12 5 7 7-7 7"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.onboarding-page {
  min-height: 100vh;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  position: relative;
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
  padding: 12px 0 0;
}
.page-header-inner {
  max-width: 720px; margin: 0 auto; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.header-title { display: flex; flex-direction: column; gap: 2px; }
.header-label { font-size: 0.6rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.1em; }
.header-name { font-size: 0.95rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }
.step-counter { font-size: 0.78rem; color: #a3a3a3; font-weight: 500; }

.progress-wrap {
  max-width: 720px; margin: 12px auto 0; padding: 0 24px;
}
.progress-track {
  height: 3px; background: #e5e5e5; border-radius: 999px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: #171717; border-radius: 999px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Content */
.onboarding-content {
  flex: 1;
  max-width: 720px; margin: 0 auto; padding: 24px 24px 32px;
  width: 100%; position: relative; z-index: 1;
}

.step-card {
  background: #fff; border-radius: 20px;
  padding: 28px 24px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03);
}
.step-number {
  font-size: 0.65rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.1em; margin-bottom: 12px;
}
.step-title {
  font-size: 1.3rem; font-weight: 700; color: #171717;
  margin: 0 0 8px; letter-spacing: -0.02em;
}
.step-subtitle {
  font-size: 0.85rem; color: #737373; margin: 0 0 24px;
}

.step-items { display: flex; flex-direction: column; gap: 14px; }
.step-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px 16px; background: #fafafa;
  border-radius: 14px; border: 1px solid rgba(0,0,0,0.04);
}
.item-bullet {
  width: 22px; height: 22px; border-radius: 50%;
  background: #171717; color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
}
.item-text { font-size: 0.85rem; color: #525252; line-height: 1.6; font-weight: 500; }

/* Footer */
.onboarding-footer {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 50;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(20px) saturate(1.3);
  border-top: 1px solid rgba(0,0,0,0.05);
  max-width: 720px; margin: 0 auto;
  padding: 12px 24px calc(12px + env(safe-area-inset-bottom, 0px));
  display: flex; align-items: center; justify-content: space-between;
}

.btn-primary {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 28px;
  border: none; border-radius: 14px;
  background: #171717; color: #fff;
  font-family: inherit; font-size: 0.88rem; font-weight: 600;
  letter-spacing: -0.01em; cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary:hover { background: #262626; transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,0,0,0.15); }

.btn-secondary {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 24px;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 14px;
  background: #fff; color: #525252;
  font-family: inherit; font-size: 0.88rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-secondary:hover { border-color: rgba(0,0,0,0.12); color: #171717; }

@media (min-width: 768px) {
  .onboarding-content { padding: 32px 32px 40px; }
  .onboarding-footer {
    border-radius: 16px 16px 0 0;
    border: 1px solid rgba(0,0,0,0.05); border-bottom: none;
    bottom: 12px;
  }
}
</style>

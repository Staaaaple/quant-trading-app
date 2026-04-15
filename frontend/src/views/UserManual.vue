<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const steps = [
  {
    key: 'strategy',
    icon: 'strategy',
    color: '#6366f1',
    route: '/strategies',
    itemCount: 5,
  },
  {
    key: 'backtest',
    icon: 'backtest',
    color: '#10b981',
    route: '/backtests',
    itemCount: 3,
  },
  {
    key: 'paperTrading',
    icon: 'paper',
    color: '#f59e0b',
    route: '/paper-trading',
    itemCount: 3,
  },
  {
    key: 'sync',
    icon: 'sync',
    color: '#ec4899',
    route: '/paper-trading',
    itemCount: 5,
  },
  {
    key: 'stockPicker',
    icon: 'picker',
    color: '#14b8a6',
    route: '/strategies/picker',
    itemCount: 4,
  },
]

const tips = ['tip1', 'tip2', 'tip3', 'tip4', 'tip5', 'tip6', 'tip7', 'tip8', 'tip9']
</script>

<template>
  <div class="manual">
    <section class="intro">
      <h2 class="intro-title">{{ t('manual.introTitle') }}</h2>
      <p class="intro-desc">{{ t('manual.introDesc') }}</p>
    </section>

    <div class="steps">
      <div v-for="(step, index) in steps" :key="step.key" class="step-card">
        <div class="step-header">
          <div class="step-number" :style="{ background: step.color + '20', color: step.color }">
            {{ index + 1 }}
          </div>
          <div class="step-icon" :style="{ background: step.color + '12', color: step.color }">
            <svg v-if="step.icon === 'strategy'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
            <svg v-else-if="step.icon === 'backtest'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2"/>
              <path d="M3 9h18"/>
              <path d="M9 21V9"/>
            </svg>
            <svg v-else-if="step.icon === 'paper'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="22" x2="18" y1="12" y2="12"/>
              <line x1="6" x2="2" y1="12" y2="12"/>
              <line x1="12" x2="12" y1="6" y2="2"/>
              <line x1="12" x2="12" y1="22" y2="18"/>
            </svg>
            <svg v-else-if="step.icon === 'picker'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"/>
              <path d="M7 12h10"/>
              <path d="M10 18h4"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/>
              <path d="M21 12v5H5a2 2 0 0 0 0 4h14v-4"/>
              <path d="M3 12h18"/>
            </svg>
          </div>
          <h3 class="step-title">{{ t(`manual.steps.${step.key}.title`) }}</h3>
        </div>
        <p class="step-desc">{{ t(`manual.steps.${step.key}.desc`) }}</p>
        <ul class="step-list">
          <li v-for="i in step.itemCount" :key="i">{{ t(`manual.steps.${step.key}.item${i}`) }}</li>
        </ul>
        <RouterLink v-if="step.route" :to="step.route" class="step-link">
          {{ t('manual.goTo') }} {{ t(`nav.${step.key === 'sync' ? 'paperTrading' : step.key}`) }} →
        </RouterLink>
      </div>
    </div>

    <section class="tips card">
      <h3 class="tips-title">{{ t('manual.tipsTitle') }}</h3>
      <ul class="tips-list">
        <li v-for="tip in tips" :key="tip">{{ t(`manual.${tip}`) }}</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.manual {
  padding: 0;
}

.intro {
  margin-bottom: var(--space-3xl);
}

.intro-title {
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.intro-desc {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 720px;
}

.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-xl);
  margin-bottom: var(--space-3xl);
}

.step-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}

.step-card:hover {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-md);
}

.step-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.step-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 700;
}

.step-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
}

.step-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
}

.step-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.55;
  margin-bottom: var(--space-lg);
}

.step-list {
  list-style: disc;
  padding-left: var(--space-lg);
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
  margin-bottom: var(--space-lg);
  flex: 1;
}

.step-link {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--accent);
  text-decoration: none;
  transition: opacity 0.15s ease;
}

.step-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.tips {
  padding: var(--space-2xl);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.tips-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.tips-list {
  list-style: disc;
  padding-left: var(--space-lg);
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.8;
}
</style>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="home">
    <div class="hero">
      <h1 class="hero-title">{{ t('app.name') }}</h1>
      <p class="hero-desc">
        {{ t('nav.strategies') }} · {{ t('nav.backtests') }} · {{ t('nav.paperTrading') }}
      </p>
    </div>

    <div class="cards">
      <RouterLink to="/strategies" class="card link-card">
        <div class="card-icon" style="background: rgba(99, 102, 241, 0.08); color: #6366f1;">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
        </div>
        <div class="card-title">{{ t('nav.strategies') }}</div>
        <div class="card-desc">{{ t('strategy.title') }}</div>
      </RouterLink>

      <RouterLink to="/backtests" class="card link-card">
        <div class="card-icon" style="background: rgba(16, 185, 129, 0.08); color: #10b981;">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="18" height="18" x="3" y="3" rx="2"/>
            <path d="M3 9h18"/>
            <path d="M9 21V9"/>
          </svg>
        </div>
        <div class="card-title">{{ t('nav.backtests') }}</div>
        <div class="card-desc">{{ t('backtest.title') }}</div>
      </RouterLink>

      <RouterLink to="/paper-trading" class="card link-card">
        <div class="card-icon" style="background: rgba(245, 158, 11, 0.08); color: #f59e0b;">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="22" x2="18" y1="12" y2="12"/>
            <line x1="6" x2="2" y1="12" y2="12"/>
            <line x1="12" x2="12" y1="6" y2="2"/>
            <line x1="12" x2="12" y1="22" y2="18"/>
          </svg>
        </div>
        <div class="card-title">{{ t('nav.paperTrading') }}</div>
        <div class="card-desc">{{ t('paperTrading.title') }}</div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.home {
  padding: 0;
}

.hero {
  margin-bottom: var(--space-3xl);
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin-bottom: var(--space-sm);
}

.hero-desc {
  font-size: 1.15rem;
  color: var(--text-secondary);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--space-xl);
}

.link-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-2xl);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all 0.25s ease;
  text-decoration: none;
}

.link-card:hover {
  background: var(--bg-surface-hover);
  border-color: var(--border-focus);
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: transform 0.25s ease;
}

.link-card:hover .card-icon {
  transform: scale(1.05);
}

.card-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
}
</style>

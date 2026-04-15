<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { supportedLocales, type SupportedLocale } from './i18n'
import { syncApi } from './api/sync'
import { stockPickerApi, type WeeklySummary } from './api/stockPicker'

const route = useRoute()
const { locale, t } = useI18n()

const pageTitle = computed(() => {
  const key = route.meta.titleKey as string
  return key ? t(key) : ''
})

function changeLanguage(lang: SupportedLocale) {
  locale.value = lang
  localStorage.setItem('locale', lang)
}

const pendingSummary = ref({ pending_count: 0, overdue_count: 0 })
const weeklySummary = ref<WeeklySummary>({ has_new_weekly: false, item_count: 0 })

async function loadPendingSummary() {
  try {
    pendingSummary.value = await syncApi.getPendingSummary()
  } catch {
    // ignore
  }
}

async function loadWeeklySummary() {
  try {
    weeklySummary.value = await stockPickerApi.getWeeklySummary()
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadPendingSummary()
  setInterval(loadPendingSummary, 60000)
  loadWeeklySummary()
  setInterval(loadWeeklySummary, 60000)
})
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">Q</div>
        <div class="brand-name">{{ t('app.name') }}</div>
      </div>

      <nav class="nav">
        <RouterLink to="/" class="nav-item" exact-active-class="active">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          </span>
          <span>{{ t('nav.home') }}</span>
        </RouterLink>
        <RouterLink to="/strategies" class="nav-item" exact-active-class="active">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
          </span>
          <span>{{ t('nav.strategies') }}</span>
        </RouterLink>
        <RouterLink to="/backtests" class="nav-item" exact-active-class="active">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          </span>
          <span>{{ t('nav.backtests') }}</span>
        </RouterLink>
        <RouterLink to="/stock-pickers" class="nav-item" exact-active-class="active">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M7 12h10"/><path d="M10 18h4"/></svg>
          </span>
          <span>{{ t('nav.stockPickers') }}</span>
          <span v-if="weeklySummary.has_new_weekly" class="nav-badge">{{ weeklySummary.item_count }}</span>
        </RouterLink>
        <RouterLink to="/paper-trading" class="nav-item" exact-active-class="active">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" x2="18" y1="12" y2="12"/><line x1="6" x2="2" y1="12" y2="12"/><line x1="12" x2="12" y1="6" y2="2"/><line x1="12" x2="12" y1="22" y2="18"/></svg>
          </span>
          <span>{{ t('nav.paperTrading') }}</span>
          <span v-if="pendingSummary.overdue_count > 0" class="nav-badge">{{ pendingSummary.overdue_count }}</span>
        </RouterLink>
        <RouterLink to="/manual" class="nav-item" exact-active-class="active">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20"/><path d="M8 7h6"/><path d="M8 11h8"/></svg>
          </span>
          <span>{{ t('nav.manual') }}</span>
        </RouterLink>
      </nav>

      <div class="lang-switcher">
        <label>{{ t('app.language') }}</label>
        <div class="lang-options">
          <button
            v-for="loc in supportedLocales"
            :key="loc.code"
            :class="['lang-btn', { active: locale === loc.code }]"
            @click="changeLanguage(loc.code)"
          >
            {{ loc.name }}
          </button>
        </div>
      </div>
    </aside>

    <main class="main">
      <header class="page-header-bar">
        <h1 class="page-header-title">{{ pageTitle }}</h1>
      </header>
      <div class="main-content">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  padding: var(--space-2xl) var(--space-xl);
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 50;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-3xl);
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  color: #fff;
  font-weight: 700;
  font-size: 1.1rem;
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}

.brand-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-subtle);
  color: var(--accent);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.8;
}

.nav-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--error);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 9999px;
  padding: 0 6px;
}

.lang-switcher {
  margin-top: auto;
  padding-top: var(--space-xl);
  border-top: 1px solid var(--border-subtle);
}

.lang-switcher label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-sm);
}

.lang-options {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.lang-btn {
  padding: var(--space-xs) var(--space-sm);
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.lang-btn:hover {
  border-color: var(--border-focus);
  color: var(--text-primary);
}

.lang-btn.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 500;
}

.main {
  flex: 1;
  min-width: 0;
  background: var(--bg-base);
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
}

.page-header-bar {
  height: var(--header-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  padding: 0 var(--space-3xl);
  position: sticky;
  top: 0;
  z-index: 40;
}

.page-header-title {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.main-content {
  flex: 1;
  padding: var(--space-3xl);
  max-width: var(--content-max-width);
  width: 100%;
  margin: 0 auto;
}
</style>

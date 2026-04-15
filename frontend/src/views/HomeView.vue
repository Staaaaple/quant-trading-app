<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { stockPickerApi, type WeeklySummary } from '@/api/stockPicker'

const { t } = useI18n()

const weeklySummary = ref<WeeklySummary>({ has_new_weekly: false, item_count: 0 })
const showWeeklyModal = ref(false)

async function loadWeeklySummary() {
  try {
    weeklySummary.value = await stockPickerApi.getWeeklySummary()
  } catch {
    // ignore
  }
}

function openWeeklyModal() {
  showWeeklyModal.value = true
}

function closeWeeklyModal() {
  showWeeklyModal.value = false
}

onMounted(() => {
  loadWeeklySummary()
})
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
      <!-- Weekly picks card -->
      <div class="card link-card" @click="openWeeklyModal">
        <div class="card-icon" style="background: rgba(139, 92, 246, 0.08); color: #8b5cf6;">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"/>
            <path d="M7 12h10"/>
            <path d="M10 18h4"/>
          </svg>
        </div>
        <div class="card-title">{{ t('stockPicker.weeklyTitle') }}</div>
        <div v-if="weeklySummary.has_new_weekly" class="card-desc">
          {{ weeklySummary.item_count }} {{ t('stockPicker.stocks') }}
        </div>
        <div v-else class="card-desc">{{ t('home.noWeeklyYet') }}</div>
      </div>

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

    <!-- Weekly Picks Modal -->
    <div v-if="showWeeklyModal" class="modal-backdrop" @click.self="closeWeeklyModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="modal-title">{{ t('stockPicker.weeklyTitle') }}</h3>
          <button class="modal-close" @click="closeWeeklyModal">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="weeklySummary.pool?.items?.length" class="stock-list">
            <div
              v-for="item in weeklySummary.pool.items"
              :key="item.symbol"
              class="stock-item"
            >
              <div class="stock-main">
                <span class="stock-symbol">{{ item.symbol }}</span>
                <span v-if="item.name" class="stock-name">{{ item.name }}</span>
                <span v-if="item.score !== undefined" class="stock-score">{{ item.score.toFixed(3) }}</span>
              </div>
              <div v-if="item.reason" class="stock-reason">{{ item.reason }}</div>
            </div>
          </div>
          <div v-else class="empty-state">{{ t('home.noWeeklyYet') }}</div>
        </div>
        <div class="modal-footer">
          <RouterLink to="/strategies/picker" class="btn btn--primary" @click="closeWeeklyModal">
            {{ t('manual.goTo') }}
          </RouterLink>
        </div>
      </div>
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

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: var(--space-xl);
}

.modal-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 640px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-xl) var(--space-2xl);
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: var(--text-secondary);
  cursor: pointer;
}

.modal-body {
  padding: var(--space-lg) var(--space-2xl);
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-2xl);
  border-top: 1px solid var(--border-subtle);
}

.stock-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.stock-item {
  padding: var(--space-md);
  background: var(--bg-surface-hover);
  border-radius: var(--radius-md);
}

.stock-main {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-xs);
}

.stock-symbol {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-weight: 600;
  color: var(--text-primary);
}

.stock-name {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.stock-score {
  margin-left: auto;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--accent);
  background: rgba(99, 102, 241, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.stock-reason {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.empty-state {
  text-align: center;
  color: var(--text-muted);
  padding: var(--space-3xl);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn--primary {
  background: var(--accent);
  color: #fff;
}
</style>

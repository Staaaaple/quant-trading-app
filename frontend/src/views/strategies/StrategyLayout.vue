<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { stockPickerApi, type WeeklySummary } from '@/api/stockPicker'

const { t } = useI18n()
const route = useRoute()

const weeklySummary = ref<WeeklySummary>({ has_new_weekly: false, item_count: 0 })
let summaryTimer: ReturnType<typeof setInterval> | null = null

async function loadWeeklySummary() {
  try {
    weeklySummary.value = await stockPickerApi.getWeeklySummary()
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadWeeklySummary()
  summaryTimer = setInterval(loadWeeklySummary, 60000)
})

onBeforeUnmount(() => {
  if (summaryTimer) clearInterval(summaryTimer)
})

const tabs = [
  { key: 'picker', labelKey: 'strategy.tabs.picker', to: '/strategies/picker' },
  { key: 'trade', labelKey: 'strategy.tabs.trade', to: '/strategies/trade' },
  { key: 'risk', labelKey: 'strategy.tabs.risk', to: '/strategies/risk' },
  { key: 'flow', labelKey: 'strategy.tabs.flow', to: '/strategies/flow' },
]
</script>

<template>
  <div class="strategy-layout">
    <div class="strategy-tabs">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.key"
        :to="tab.to"
        :class="['tab-link', { active: route.path.startsWith(tab.to) }]"
      >
        <span>{{ t(tab.labelKey) }}</span>
        <span v-if="tab.key === 'picker' && weeklySummary.has_new_weekly" class="tab-badge">
          {{ weeklySummary.item_count }}
        </span>
      </RouterLink>
    </div>
    <div class="strategy-content">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.strategy-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.strategy-tabs {
  display: flex;
  gap: var(--space-xs);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: var(--space-lg);
}

.tab-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
}

.tab-link:hover {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
}

.tab-link.active {
  background: var(--accent-subtle);
  color: var(--accent);
}

.tab-badge {
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--error);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 9999px;
  padding: 0 5px;
}

.strategy-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>

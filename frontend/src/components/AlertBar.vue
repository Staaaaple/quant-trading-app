<script setup lang="ts">
import { computed } from 'vue'

interface Alert {
  id: string
  type: 'lifespan' | 'cycle' | 'deviation' | 'rebalance'
  level: 'red' | 'yellow'
  title: string
  message: string
  action?: string
  actionText?: string
}

const props = defineProps<{
  alerts: Alert[]
}>()

const emit = defineEmits<{
  (e: 'action', alertId: string): void
  (e: 'dismiss', alertId: string): void
}>()

const visibleAlerts = computed(() => {
  return props.alerts.filter(a => a.level === 'red').slice(0, 2)
})

function getAlertIcon(type: string) {
  const icons: Record<string, string> = {
    lifespan: '⏱️',
    cycle: '🔄',
    deviation: '⚖️',
    rebalance: '📊',
  }
  return icons[type] || '⚠️'
}

function getAlertClass(level: string) {
  return level === 'red' ? 'alert-red' : 'alert-yellow'
}
</script>

<template>
  <div v-if="visibleAlerts.length > 0" class="alert-bar">
    <div
      v-for="alert in visibleAlerts"
      :key="alert.id"
      class="alert-item"
      :class="getAlertClass(alert.level)"
    >
      <span class="alert-icon">{{ getAlertIcon(alert.type) }}</span>
      <span class="alert-text">{{ alert.message }}</span>
      <button
        v-if="alert.action"
        class="alert-action"
        @click="emit('action', alert.id)"
      >
        {{ alert.actionText || '查看' }}
      </button>
      <button
        class="alert-dismiss"
        @click="emit('dismiss', alert.id)"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <path d="M18 6 6 18"/>
          <path d="m6 6 12 12"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.alert-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  font-size: 0.82rem;
  font-weight: 500;
}

.alert-item.alert-red {
  background: #fef2f2;
  color: #dc2626;
  border-bottom: 1px solid #fee2e2;
}

.alert-item.alert-yellow {
  background: #fffbeb;
  color: #d97706;
  border-bottom: 1px solid #fef3c7;
}

.alert-icon { font-size: 1rem; flex-shrink: 0; }
.alert-text { flex: 1; line-height: 1.4; }

.alert-action {
  padding: 6px 12px;
  border-radius: 8px;
  border: none;
  background: rgba(0,0,0,0.08);
  color: inherit;
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s ease;
}
.alert-action:hover { background: rgba(0,0,0,0.12); }

.alert-dismiss {
  width: 24px; height: 24px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: opacity 0.2s ease;
  flex-shrink: 0;
}
.alert-dismiss:hover { opacity: 1; }
</style>

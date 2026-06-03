<script setup lang="ts">
import { ref, computed } from 'vue'

interface Notification {
  id: string
  type: 'daily_op' | 'weekly_report' | 'rebalance_alert' | 'lifespan_alert' | 'cycle_alert'
  title: string
  summary: string
  isRead: boolean
  createdAt: string
  priority: 'high' | 'normal' | 'low'
}

const props = defineProps<{
  notifications: Notification[]
}>()

const emit = defineEmits<{
  (e: 'read', id: string): void
  (e: 'readAll'): void
}>()

const isOpen = ref(false)

const unreadCount = computed(() => {
  return props.notifications.filter(n => !n.isRead).length
})

const sortedNotifications = computed(() => {
  return [...props.notifications].sort((a, b) => {
    // Unread first, then by date
    if (a.isRead !== b.isRead) return a.isRead ? 1 : -1
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  })
})

function getNotificationIcon(type: string) {
  const icons: Record<string, string> = {
    daily_op: '📈',
    weekly_report: '📊',
    rebalance_alert: '⚖️',
    lifespan_alert: '⏱️',
    cycle_alert: '🔄',
  }
  return icons[type] || '📌'
}

function getPriorityClass(priority: string) {
  return `priority-${priority}`
}

function toggleOpen() {
  isOpen.value = !isOpen.value
}

function handleRead(id: string) {
  emit('read', id)
}

function handleReadAll() {
  emit('readAll')
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="notification-badge">
    <button class="badge-trigger" @click="toggleOpen">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
      </svg>
      <span v-if="unreadCount > 0" class="badge-count">{{ unreadCount }}</span>
    </button>

    <div v-if="isOpen" class="notification-dropdown">
      <div class="dropdown-header">
        <span class="dropdown-title">通知</span>
        <button v-if="unreadCount > 0" class="read-all-btn" @click="handleReadAll">
          全部已读
        </button>
      </div>

      <div v-if="sortedNotifications.length === 0" class="empty-state">
        暂无通知
      </div>

      <div v-else class="notification-list">
        <div
          v-for="notification in sortedNotifications"
          :key="notification.id"
          class="notification-item"
          :class="{ unread: !notification.isRead, [getPriorityClass(notification.priority)]: true }"
          @click="handleRead(notification.id)"
        >
          <div class="notification-icon">{{ getNotificationIcon(notification.type) }}</div>
          <div class="notification-body">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-summary">{{ notification.summary }}</div>
            <div class="notification-time">{{ formatTime(notification.createdAt) }}</div>
          </div>
          <div v-if="!notification.isRead" class="unread-dot"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notification-badge {
  position: relative;
}

.badge-trigger {
  position: relative;
  width: 40px; height: 40px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: #525252;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.badge-trigger:hover {
  background: rgba(0,0,0,0.05);
  color: #171717;
}

.badge-count {
  position: absolute;
  top: 4px; right: 4px;
  min-width: 18px; height: 18px;
  border-radius: 999px;
  background: #dc2626; color: #fff;
  font-size: 0.65rem; font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  max-height: 480px;
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
  overflow: hidden;
  z-index: 200;
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.dropdown-title { font-size: 0.95rem; font-weight: 700; color: #171717; }
.read-all-btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: none;
  background: #f5f5f5;
  color: #525252;
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.read-all-btn:hover { background: #e5e5e5; color: #171717; }

.empty-state {
  padding: 40px;
  text-align: center;
  font-size: 0.85rem;
  color: #a3a3a3;
}

.notification-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.15s ease;
  border-bottom: 1px solid rgba(0,0,0,0.03);
}
.notification-item:hover { background: #fafafa; }
.notification-item.unread { background: #fafafa; }
.notification-item.unread:hover { background: #f5f5f5; }

.notification-icon { font-size: 1.2rem; flex-shrink: 0; margin-top: 2px; }

.notification-body { flex: 1; min-width: 0; }
.notification-title { font-size: 0.85rem; font-weight: 600; color: #171717; }
.notification-summary { font-size: 0.78rem; color: #737373; margin-top: 2px; line-height: 1.4; }
.notification-time { font-size: 0.7rem; color: #a3a3a3; margin-top: 4px; }

.unread-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  flex-shrink: 0;
  margin-top: 6px;
}

.priority-high .notification-title { color: #dc2626; }
</style>

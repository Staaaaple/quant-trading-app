<script setup lang="ts">
defineProps<{
  visible: boolean
  text?: string
}>()
</script>

<template>
  <Teleport v-if="visible" to="body">
    <div class="loading-overlay">
      <div class="loading-box">
        <div class="loading-spinner" />
        <div v-if="text" class="loading-text">{{ text }}</div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(2px);
  z-index: 9999;
}

.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-2xl) var(--space-3xl);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.loading-text {
  font-size: 0.95rem;
  color: var(--text-secondary);
  font-weight: 500;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

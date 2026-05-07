<script setup lang="ts">
defineProps<{
  label: string
  variant?: 'feature' | 'signal' | 'risk' | 'execution'
}>()

const variantMap = {
  feature: { bg: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', icon: '🧬' },
  signal: { bg: 'rgba(217, 119, 6, 0.1)', color: '#d97706', icon: '📡' },
  risk: { bg: 'rgba(185, 28, 28, 0.08)', color: '#b91c1c', icon: '🛡️' },
  execution: { bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', icon: '⚡' },
} as const

type VariantKey = keyof typeof variantMap

function getStyle(v: string): typeof variantMap[VariantKey] {
  return variantMap[(v as VariantKey) || 'feature']
}
</script>

<template>
  <span
    class="gene-tag"
    :style="{
      background: getStyle(variant || '').bg,
      color: getStyle(variant || '').color,
    }"
  >
    <span class="gene-icon">{{ getStyle(variant || '').icon }}</span>
    {{ label }}
  </span>
</template>

<style scoped>
.gene-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 500;
  white-space: nowrap;
}
.gene-icon {
  font-size: 0.85rem;
}
</style>

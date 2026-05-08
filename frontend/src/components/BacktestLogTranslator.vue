<script setup lang="ts">
interface RiskBlock {
  type: string
  threshold: number
  actual: number
  action: string
  date: string
  symbol: string
}

const props = defineProps<{
  riskBlocks: RiskBlock[]
}>()

const TYPE_LABELS: Record<string, string> = {
  max_drawdown: '最大回撤限制',
  max_position: '最大持仓限制',
}

const ACTION_LABELS: Record<string, string> = {
  block_buy: '已禁止开新仓',
  block_all: '已禁止全部交易',
  warn: '触发警告',
}

function translateBlock(block: RiskBlock): string {
  const typeLabel = TYPE_LABELS[block.type] || block.type
  const actionLabel = ACTION_LABELS[block.action] || block.action
  const actualPct = (block.actual * 100).toFixed(2)
  const thresholdPct = (block.threshold * 100).toFixed(2)
  return `${block.date} · ${typeLabel}：实际 ${actualPct}% 超过阈值 ${thresholdPct}%，${actionLabel}`
}
</script>

<template>
  <div class="risk-log-panel">
    <div class="risk-log-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      风控阻断记录
      <span class="risk-log-count">{{ riskBlocks.length }} 次</span>
    </div>
    <div class="risk-log-list">
      <div v-for="(block, idx) in riskBlocks" :key="idx" class="risk-log-item">
        <span class="risk-log-dot" />
        <span class="risk-log-text">{{ translateBlock(block) }}</span>
      </div>
      <div v-if="!riskBlocks.length" class="risk-log-empty">
        本次回测未触发任何风控阻断
      </div>
    </div>
  </div>
</template>

<style scoped>
.risk-log-panel {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.risk-log-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-base);
  border-bottom: 1px solid var(--border-subtle);
}

.risk-log-count {
  margin-left: auto;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-surface);
  padding: 2px 8px;
  border-radius: 999px;
}

.risk-log-list {
  padding: var(--space-sm) 0;
  max-height: 320px;
  overflow-y: auto;
}

.risk-log-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.risk-log-item:hover {
  background: var(--bg-surface-hover);
}

.risk-log-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #d97706;
  margin-top: 6px;
  flex-shrink: 0;
}

.risk-log-text {
  word-break: break-word;
}

.risk-log-empty {
  padding: var(--space-xl) var(--space-lg);
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-muted);
  font-style: italic;
}
</style>

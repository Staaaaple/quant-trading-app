<script setup lang="ts">
interface RiskCheck {
  type: string
  threshold: number
  action: string
}

const props = defineProps<{
  checks: RiskCheck[]
}>()

const emit = defineEmits<{
  (e: 'update:checks', v: RiskCheck[]): void
}>()

const CHECK_TYPES = [
  { value: 'max_drawdown', label: '最大回撤' },
  { value: 'max_position', label: '最大持仓比例' },
]

const ACTIONS = [
  { value: 'block_buy', label: '禁止买入' },
  { value: 'block_all', label: '禁止交易' },
  { value: 'warn', label: '仅警告' },
]

function addCheck() {
  const list = [...props.checks]
  list.push({ type: 'max_drawdown', threshold: 0.05, action: 'block_buy' })
  emit('update:checks', list)
}

function removeCheck(idx: number) {
  const list = [...props.checks]
  list.splice(idx, 1)
  emit('update:checks', list)
}

function updateCheck(idx: number, patch: Partial<RiskCheck>) {
  const list = [...props.checks]
  list[idx] = { ...list[idx], ...patch }
  emit('update:checks', list)
}
</script>

<template>
  <div class="stage-form">
    <div v-for="(check, idx) in checks" :key="idx" class="check-row">
      <select
        :value="check.type"
        @change="updateCheck(idx, { type: ($event.target as HTMLSelectElement).value })"
        class="form-select"
      >
        <option v-for="t in CHECK_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
      </select>
      <span class="check-sep">></span>
      <input
        :value="check.threshold"
        @input="updateCheck(idx, { threshold: Number(($event.target as HTMLInputElement).value) || 0 })"
        type="number"
        min="0"
        max="1"
        step="0.01"
        class="form-input form-input--xs"
      />
      <select
        :value="check.action"
        @change="updateCheck(idx, { action: ($event.target as HTMLSelectElement).value })"
        class="form-select"
      >
        <option v-for="a in ACTIONS" :key="a.value" :value="a.value">{{ a.label }}</option>
      </select>
      <button class="btn btn--ghost btn--sm" @click="removeCheck(idx)">删除</button>
    </div>
    <button class="btn btn--secondary btn--sm" @click="addCheck">+ 添加风控规则</button>
  </div>
</template>

<style scoped>
.stage-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.check-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.check-sep {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.form-input--xs {
  width: 70px;
}

.form-select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 0.85rem;
}
</style>

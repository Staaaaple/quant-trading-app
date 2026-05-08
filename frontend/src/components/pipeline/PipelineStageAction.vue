<script setup lang="ts">
interface ActionRule {
  signal_group: string
  action: string
  weight: number
}

const props = defineProps<{
  rules: ActionRule[]
  signalGroups: string[]
}>()

const emit = defineEmits<{
  (e: 'update:rules', v: ActionRule[]): void
}>()

function addRule() {
  const list = [...props.rules]
  list.push({
    signal_group: props.signalGroups[0] || '',
    action: 'order_target_percent',
    weight: 0.5,
  })
  emit('update:rules', list)
}

function removeRule(idx: number) {
  const list = [...props.rules]
  list.splice(idx, 1)
  emit('update:rules', list)
}

function updateRule(idx: number, patch: Partial<ActionRule>) {
  const list = [...props.rules]
  list[idx] = { ...list[idx], ...patch }
  emit('update:rules', list)
}
</script>

<template>
  <div class="stage-form">
    <div v-for="(rule, idx) in rules" :key="idx" class="rule-row">
      <span class="rule-label">当</span>
      <select
        :value="rule.signal_group"
        @change="updateRule(idx, { signal_group: ($event.target as HTMLSelectElement).value })"
        class="form-select"
      >
        <option v-for="g in signalGroups" :key="g" :value="g">{{ g }}</option>
      </select>
      <span class="rule-label">命中时</span>
      <select
        :value="rule.action"
        @change="updateRule(idx, { action: ($event.target as HTMLSelectElement).value })"
        class="form-select"
      >
        <option value="order_target_percent">调整仓位至</option>
      </select>
      <div class="slider-wrap">
        <input
          :value="Math.round(rule.weight * 100)"
          @input="updateRule(idx, { weight: Number(($event.target as HTMLInputElement).value) / 100 })"
          type="range"
          min="0"
          max="100"
          class="form-slider"
        />
        <span class="slider-value" :class="{ 'text-loss': rule.weight === 0 }">{{ Math.round(rule.weight * 100) }}%</span>
      </div>
      <button class="btn btn--ghost btn--sm" @click="removeRule(idx)">删除</button>
    </div>
    <button class="btn btn--secondary btn--sm" @click="addRule">+ 添加执行规则</button>
  </div>
</template>

<style scoped>
.stage-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.rule-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.rule-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.slider-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.form-slider {
  width: 100px;
}

.slider-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 40px;
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

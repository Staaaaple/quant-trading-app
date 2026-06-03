<script setup lang="ts">
import { computed } from 'vue'

interface IndicatorDef {
  name: string
  type: string
  period: number
  field: string
}

const props = defineProps<{
  indicators: IndicatorDef[]
  isNlGenerated?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:indicators', v: IndicatorDef[]): void
}>()

const INDICATOR_TYPES = [
  { value: 'MA', label: 'MA（简单均线）' },
  { value: 'EMA', label: 'EMA（指数均线）' },
  { value: 'RSI', label: 'RSI（相对强弱）' },
  { value: 'MACD', label: 'MACD' },
  { value: 'KDJ', label: 'KDJ' },
  { value: 'BOLL', label: 'BOLL（布林带）' },
  { value: 'PRICE', label: '价格' },
  { value: 'VOLUME', label: '成交量' },
]

const FIELDS = ['close', 'open', 'high', 'low', 'volume']

function addIndicator() {
  const list = [...props.indicators]
  list.push({ name: `ind${list.length + 1}`, type: 'MA', period: 5, field: 'close' })
  emit('update:indicators', list)
}

function removeIndicator(idx: number) {
  const list = [...props.indicators]
  list.splice(idx, 1)
  emit('update:indicators', list)
}

function updateIndicator(idx: number, patch: Partial<IndicatorDef>) {
  const list = [...props.indicators]
  list[idx] = { ...list[idx], ...patch }
  emit('update:indicators', list)
}

const nameMap = computed(() => {
  const map = new Map<string, number>()
  props.indicators.forEach((ind, i) => {
    map.set(ind.name, (map.get(ind.name) || 0) + 1)
  })
  return map
})
</script>

<template>
  <div class="stage-form">
    <div v-for="(ind, idx) in indicators" :key="idx" class="indicator-row">
      <input
        :value="ind.name"
        @input="updateIndicator(idx, { name: ($event.target as HTMLInputElement).value })"
        type="text"
        class="form-input"
        :class="{ 'input-error': nameMap.get(ind.name)! > 1, 'nl-field': isNlGenerated }"
        placeholder="指标名"
      />
      <select
        :value="ind.type"
        @change="updateIndicator(idx, { type: ($event.target as HTMLSelectElement).value })"
        class="form-select"
        :class="{ 'nl-field': isNlGenerated }"
      >
        <option v-for="t in INDICATOR_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
      </select>
      <input
        v-if="ind.type !== 'PRICE' && ind.type !== 'VOLUME'"
        :value="ind.period"
        @input="updateIndicator(idx, { period: Number(($event.target as HTMLInputElement).value) || 5 })"
        type="number"
        min="1"
        max="250"
        class="form-input form-input--xs"
        :class="{ 'nl-field': isNlGenerated }"
        placeholder="周期"
      />
      <select
        v-if="ind.type === 'PRICE'"
        :value="ind.field"
        @change="updateIndicator(idx, { field: ($event.target as HTMLSelectElement).value })"
        class="form-select"
        :class="{ 'nl-field': isNlGenerated }"
      >
        <option v-for="f in FIELDS" :key="f" :value="f">{{ f }}</option>
      </select>
      <button class="btn btn--ghost btn--sm" @click="removeIndicator(idx)">删除</button>
    </div>
    <button class="btn btn--secondary btn--sm" @click="addIndicator">+ 添加指标</button>
  </div>
</template>

<style scoped>
.stage-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.indicator-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.form-input {
  width: 120px;
}

.form-input--xs {
  width: 60px;
}

.form-select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 0.85rem;
}

.input-error {
  border-color: var(--error) !important;
}

.nl-field {
  outline: 2px solid #f59e0b !important;
  outline-offset: 1px;
  background: rgba(245, 158, 11, 0.06);
}
</style>

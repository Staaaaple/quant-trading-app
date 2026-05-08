<script setup lang="ts">
import { computed } from 'vue'

interface InitConfig {
  history_depth?: number
  max_position_pct?: number
}

const props = defineProps<{
  config: InitConfig
}>()

const emit = defineEmits<{
  (e: 'update:config', v: InitConfig): void
}>()

const depth = computed({
  get: () => props.config.history_depth ?? 30,
  set: (v) => emit('update:config', { ...props.config, history_depth: v }),
})

const maxPos = computed({
  get: () => Math.round((props.config.max_position_pct ?? 0.95) * 100),
  set: (v) => emit('update:config', { ...props.config, max_position_pct: v / 100 }),
})
</script>

<template>
  <div class="stage-form">
    <div class="form-row">
      <label class="form-label">历史数据深度</label>
      <input v-model.number="depth" type="number" min="5" max="250" class="form-input form-input--sm" />
      <span class="form-hint">根K线（影响指标计算所需数据量）</span>
    </div>
    <div class="form-row">
      <label class="form-label">最大持仓比例</label>
      <div class="slider-wrap">
        <input v-model.number="maxPos" type="range" min="10" max="100" class="form-slider" />
        <span class="slider-value">{{ maxPos }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stage-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.form-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.form-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 100px;
}

.form-input--sm {
  width: 80px;
}

.form-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.slider-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex: 1;
}

.form-slider {
  flex: 1;
  max-width: 200px;
}

.slider-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 40px;
}
</style>

<script setup lang="ts">
interface ConditionOperand {
  indicator?: string | null
  value?: number | null
}

interface Condition {
  left: ConditionOperand
  op: string
  right: ConditionOperand
}

interface SignalGroup {
  id: string
  direction: string
  logic: string
  conditions: Condition[]
}

const props = defineProps<{
  groups: SignalGroup[]
  availableIndicators: string[]
  isNlGenerated?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:groups', v: SignalGroup[]): void
}>()

const OPS = [
  { value: 'cross_up', label: '上穿' },
  { value: 'cross_down', label: '下穿' },
  { value: 'gt', label: '>' },
  { value: 'gte', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'lte', label: '<=' },
  { value: 'eq', label: '=' },
]

function addGroup() {
  const list = [...props.groups]
  list.push({
    id: `signal-${list.length + 1}`,
    direction: 'buy',
    logic: 'AND',
    conditions: [{ left: { indicator: null, value: null }, op: 'cross_up', right: { indicator: null, value: null } }],
  })
  emit('update:groups', list)
}

function removeGroup(idx: number) {
  const list = [...props.groups]
  list.splice(idx, 1)
  emit('update:groups', list)
}

function updateGroup(idx: number, patch: Partial<SignalGroup>) {
  const list = [...props.groups]
  list[idx] = { ...list[idx], ...patch }
  emit('update:groups', list)
}

function addCondition(gidx: number) {
  const list = [...props.groups]
  list[gidx].conditions.push({ left: { indicator: null, value: null }, op: 'gt', right: { indicator: null, value: null } })
  emit('update:groups', list)
}

function removeCondition(gidx: number, cidx: number) {
  const list = [...props.groups]
  list[gidx].conditions.splice(cidx, 1)
  emit('update:groups', list)
}

function updateCondition(gidx: number, cidx: number, patch: Partial<Condition>) {
  const list = [...props.groups]
  list[gidx].conditions[cidx] = { ...list[gidx].conditions[cidx], ...patch }
  emit('update:groups', list)
}

function setOperand(side: 'left' | 'right', gidx: number, cidx: number, type: 'indicator' | 'value', val: any) {
  const list = [...props.groups]
  const cond = list[gidx].conditions[cidx]
  if (type === 'indicator') {
    cond[side] = { indicator: val ?? null, value: null }
  } else {
    cond[side] = { indicator: null, value: Number(val) || 0 }
  }
  emit('update:groups', list)
}

function operandType(op: ConditionOperand): 'indicator' | 'value' {
  if (op.indicator != null) return 'indicator'
  return 'value'
}
</script>

<template>
  <div class="stage-form">
    <div v-for="(group, gidx) in groups" :key="gidx" class="group-card">
      <div class="group-header">
        <input
          :value="group.id"
          @input="updateGroup(gidx, { id: ($event.target as HTMLInputElement).value })"
          type="text"
          class="form-input"
          :class="{ 'nl-field': isNlGenerated }"
          placeholder="信号组名称"
        />
        <select
          :value="group.direction"
          @change="updateGroup(gidx, { direction: ($event.target as HTMLSelectElement).value })"
          class="form-select"
          :class="{ 'nl-field': isNlGenerated }"
        >
          <option value="buy">买入</option>
          <option value="sell">卖出</option>
        </select>
        <select
          :value="group.logic"
          @change="updateGroup(gidx, { logic: ($event.target as HTMLSelectElement).value })"
          class="form-select"
          :class="{ 'nl-field': isNlGenerated }"
        >
          <option value="AND">全部满足</option>
          <option value="OR">任一满足</option>
        </select>
        <button class="btn btn--ghost btn--sm" @click="removeGroup(gidx)">删除</button>
      </div>

      <div class="conditions">
        <div v-for="(cond, cidx) in group.conditions" :key="cidx" class="condition-row">
          <div class="operand">
            <select
              :value="operandType(cond.left)"
              @change="setOperand('left', gidx, cidx, ($event.target as HTMLSelectElement).value as 'indicator' | 'value', ($event.target as HTMLSelectElement).value === 'indicator' ? '' : 0)"
              class="form-select form-select--type"
              :class="{ 'nl-field': isNlGenerated }"
            >
              <option value="indicator">指标</option>
              <option value="value">数值</option>
            </select>
            <select
              v-if="operandType(cond.left) === 'indicator'"
              :value="cond.left.indicator || ''"
              @change="setOperand('left', gidx, cidx, 'indicator', ($event.target as HTMLSelectElement).value)"
              class="form-select"
              :class="{ 'nl-field': isNlGenerated }"
            >
              <option value="">选择指标</option>
              <option v-for="ind in availableIndicators" :key="ind" :value="ind">{{ ind }}</option>
            </select>
            <input
              v-else
              :value="cond.left.value ?? ''"
              @input="setOperand('left', gidx, cidx, 'value', ($event.target as HTMLInputElement).value)"
              type="number"
              class="form-input form-input--sm"
              :class="{ 'nl-field': isNlGenerated }"
              placeholder="数值"
            />
          </div>

          <select
            :value="cond.op"
            @change="updateCondition(gidx, cidx, { op: ($event.target as HTMLSelectElement).value })"
            class="form-select"
            :class="{ 'nl-field': isNlGenerated }"
          >
            <option v-for="op in OPS" :key="op.value" :value="op.value">{{ op.label }}</option>
          </select>

          <div class="operand">
            <select
              :value="operandType(cond.right)"
              @change="setOperand('right', gidx, cidx, ($event.target as HTMLSelectElement).value as 'indicator' | 'value', ($event.target as HTMLSelectElement).value === 'indicator' ? '' : 0)"
              class="form-select form-select--type"
              :class="{ 'nl-field': isNlGenerated }"
            >
              <option value="indicator">指标</option>
              <option value="value">数值</option>
            </select>
            <select
              v-if="operandType(cond.right) === 'indicator'"
              :value="cond.right.indicator || ''"
              @change="setOperand('right', gidx, cidx, 'indicator', ($event.target as HTMLSelectElement).value)"
              class="form-select"
              :class="{ 'nl-field': isNlGenerated }"
            >
              <option value="">选择指标</option>
              <option v-for="ind in availableIndicators" :key="ind" :value="ind">{{ ind }}</option>
            </select>
            <input
              v-else
              :value="cond.right.value ?? ''"
              @input="setOperand('right', gidx, cidx, 'value', ($event.target as HTMLInputElement).value)"
              type="number"
              class="form-input form-input--sm"
              :class="{ 'nl-field': isNlGenerated }"
              placeholder="数值"
            />
          </div>

          <button class="btn btn--ghost btn--sm" @click="removeCondition(gidx, cidx)">删除</button>
        </div>
        <button class="btn btn--secondary btn--sm" @click="addCondition(gidx)">+ 添加条件</button>
      </div>
    </div>
    <button class="btn btn--primary btn--sm" @click="addGroup">+ 添加信号组</button>
  </div>
</template>

<style scoped>
.stage-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.group-card {
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.group-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.conditions {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.condition-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.operand {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.form-select--type {
  width: 70px;
}

.form-input--sm {
  width: 90px;
}

.form-select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 0.85rem;
}

.nl-field {
  outline: 2px solid #f59e0b !important;
  outline-offset: 1px;
  background: rgba(245, 158, 11, 0.06);
}
</style>

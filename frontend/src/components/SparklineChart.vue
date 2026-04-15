<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { computed } from 'vue'

use([CanvasRenderer, LineChart, GridComponent])

const props = defineProps<{
  totalReturn: number | undefined
}>()

const option = computed(() => {
  const ret = props.totalReturn ?? 0
  const isPositive = ret >= 0
  const color = isPositive ? '#ef4444' : '#10b981'

  // Generate a simple simulated equity curve from 0 to totalReturn
  const data: number[] = []
  const days = 30
  let value = 0
  for (let i = 0; i < days; i++) {
    const step = (ret / days) * (0.8 + Math.random() * 0.4)
    value += step
    data.push(Number((value * 100).toFixed(2)))
  }
  // Ensure final point matches
  data[data.length - 1] = Number((ret * 100).toFixed(2))

  return {
    grid: { left: 0, right: 0, top: 2, bottom: 2 },
    xAxis: { type: 'category', show: false, data: Array.from({ length: days }, (_, i) => i) },
    yAxis: { type: 'value', show: false },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: isPositive ? 'rgba(239,68,68,0.25)' : 'rgba(16,185,129,0.25)' },
              { offset: 1, color: isPositive ? 'rgba(239,68,68,0.02)' : 'rgba(16,185,129,0.02)' },
            ],
          },
        },
        data,
      },
    ],
  }
})
</script>

<template>
  <VChart
    v-if="totalReturn !== undefined && totalReturn !== null"
    :option="option"
    autoresize
    style="width: 100%; height: 40px;"
  />
  <span v-else class="empty">-</span>
</template>

<style scoped>
.empty {
  color: var(--text-muted);
  font-size: 0.85rem;
}
</style>

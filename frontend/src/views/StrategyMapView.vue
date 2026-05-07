<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import StrategyMap from '@/components/StrategyMap.vue'

const { t } = useI18n()
</script>

<template>
  <div class="strategy-map-view">
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">🗺️</span>
        策略地图
      </h1>
      <p class="page-desc">
        浏览预设策略库，按基因家族分类。选择策略导入到你的生态系统中。
      </p>
    </div>
    <StrategyMap show-import />
  </div>
</template>

<style scoped>
.strategy-map-view {
  padding: var(--space-2xl);
}
.page-header {
  margin-bottom: var(--space-2xl);
}
.page-title {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}
.title-icon {
  font-size: 1.4rem;
}
.page-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { supportedLocales, type SupportedLocale } from './i18n'
import { syncApi } from './api/sync'
import { dnaApi } from './api/dna'
import UserSwitcher from './components/UserSwitcher.vue'

import { useUserStore } from './stores/user'

const route = useRoute()
const router = useRouter()
const { locale, t } = useI18n()
const userStore = useUserStore()

const menuOpen = ref(false)

const menuGroups = [
  {
    title: '首页与引导',
    items: [
      { label: '首页', path: '/' },
    ],
  },
  {
    title: '投资者画像',
    items: [
      { label: '画像问卷', path: '/profile' },
      { label: '画像摘要', path: '/profile/summary' },
    ],
  },
  {
    title: '市场信号',
    items: [
      { label: '市场仪表盘', path: '/market' },
      { label: '市场引导', path: '/market/guide' },
    ],
  },
  {
    title: '资产组合',
    items: [
      { label: '组合构建', path: '/portfolio' },
      { label: '组合引导', path: '/portfolio/guide' },
      { label: '策略匹配', path: '/portfolio/strategies' },
      { label: '策略引导', path: '/portfolio/strategies/guide' },
    ],
  },
  {
    title: '策略生态',
    items: [
      { label: '生态系统', path: '/ecosystem' },
      { label: '策略地图', path: '/strategy-map' },
      { label: '建仓引导', path: '/building-guide' },
    ],
  },
  {
    title: '工具与监控',
    items: [
      { label: '回测中心', path: '/backtests' },
      { label: '策略对比', path: '/ab-tests' },
      { label: '模拟交易', path: '/paper-trading' },
      { label: '市场报告', path: '/market-report' },
      { label: '今日操作', path: '/today-operation' },
    ],
  },
]

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function navigateTo(path: string) {
  menuOpen.value = false
  router.push(path)
}

const pageTitle = computed(() => {
  const key = route.meta.titleKey as string
  return key ? t(key) : ''
})

function changeLanguage(lang: SupportedLocale) {
  locale.value = lang
  localStorage.setItem('locale', lang)
}

const pendingSummary = ref({ pending_count: 0, overdue_count: 0 })
const ecoAlertCount = ref(0)

async function loadPendingSummary() {
  try {
    pendingSummary.value = await syncApi.getPendingSummary()
  } catch {
    // ignore
  }
}

async function loadEcoAlert() {
  try {
    const eco = await dnaApi.getEcosystem()
    ecoAlertCount.value = (eco.endangered_count || 0) + (eco.short_lifespan_strategies?.length || 0)
  } catch {
    // ignore
  }
}

onMounted(async () => {
  await userStore.loadUsers()

  // 切离演示用户后，清除组合动画已播放标记，确保下次切回演示用户仍会播放
  if (!userStore.isDemo) {
    sessionStorage.removeItem('demo_portfolio_animation_shown')
  }

  loadPendingSummary()
  setInterval(loadPendingSummary, 60000)
  loadEcoAlert()
  setInterval(loadEcoAlert, 300000)
})
</script>

<template>
  <!-- Global Menu Button -->
  <button class="menu-toggle" @click="toggleMenu" aria-label="打开菜单">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 5h16"/>
      <path d="M4 12h16"/>
      <path d="M4 19h16"/>
    </svg>
  </button>

  <!-- Menu Drawer -->
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="menuOpen" class="menu-overlay" @click.self="closeMenu">
        <Transition name="drawer-slide">
          <div v-if="menuOpen" class="menu-drawer">
            <div class="menu-header">
              <div class="menu-brand">
                <div class="menu-brand-icon">Q</div>
                <span class="menu-brand-name">QUANTEVO</span>
              </div>
              <button class="menu-close" @click="closeMenu" aria-label="关闭菜单">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 6 6 18"/>
                  <path d="m6 6 12 12"/>
                </svg>
              </button>
            </div>

            <div class="menu-body">
              <div v-for="group in menuGroups" :key="group.title" class="menu-group">
                <div class="menu-group-title">{{ group.title }}</div>
                <nav class="menu-group-items">
                  <button
                    v-for="item in group.items"
                    :key="item.path"
                    class="menu-item"
                    :class="{ active: route.path === item.path }"
                    @click="navigateTo(item.path)"
                  >
                    <span class="menu-dot"></span>
                    <span>{{ item.label }}</span>
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>

  <div v-if="route.meta.layout === 'demo'" class="demo-layout">
    <RouterView />
    <div class="disclaimer">
      <strong>本应用仅供学习交流，不构成任何投资建议。</strong>
      市场有风险，投资需谨慎。本平台非持牌证券投资顾问，所有组合、策略、标的代码及买卖信号均为算法示例。
      数据来源于 akshare 等公开数据源，版权归原数据提供方所有。
      使用本应用即表示您同意我们的《隐私政策》与《用户协议》。
    </div>
  </div>
  <div v-else class="layout">
    <main class="main">
      <header class="page-header-bar">
        <h1 class="page-header-title">{{ pageTitle }}</h1>
        <UserSwitcher />
      </header>
      <div class="main-content">
        <RouterView />
      </div>
      <div class="disclaimer">
        <strong>本应用仅供学习交流，不构成任何投资建议。</strong>
        市场有风险，投资需谨慎。本平台非持牌证券投资顾问。数据来源于公开数据源，版权归原数据提供方所有。
      </div>
    </main>
  </div>
</template>

<style>
.demo-layout {
  min-height: 100vh;
}

.layout {
  display: flex;
  min-height: 100vh;
}

.main {
  flex: 1;
  min-width: 0;
  background: var(--bg-base);
  display: flex;
  flex-direction: column;
}

.page-header-bar {
  height: var(--header-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-3xl);
  position: sticky;
  top: 0;
  z-index: 40;
}

.page-header-title {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.main-content {
  flex: 1;
  padding: var(--space-3xl);
  max-width: var(--content-max-width);
  width: 100%;
  margin: 0 auto;
}

.disclaimer {
  position: fixed;
  bottom: 8px;
  right: 12px;
  font-size: 0.72rem;
  color: #525252;
  opacity: 0.85;
  z-index: 100;
  pointer-events: none;
  text-align: right;
  line-height: 1.5;
  max-width: 360px;
  background: rgba(255, 255, 255, 0.92);
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.demo-layout .disclaimer {
  bottom: 8px;
  right: 12px;
}

.disclaimer strong {
  color: #171717;
  font-weight: 600;
}

/* Global Menu */
.menu-toggle {
  position: fixed;
  top: 14px;
  left: 14px;
  z-index: 200;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.08);
  color: #171717;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transition: all 0.2s ease;
}
.menu-toggle:hover {
  background: #f5f5f5;
  transform: scale(1.05);
}

.menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 210;
  background: rgba(0,0,0,0.35);
  backdrop-filter: blur(4px);
}
.menu-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  max-width: 85vw;
  background: #fff;
  z-index: 211;
  display: flex;
  flex-direction: column;
  box-shadow: 8px 0 32px rgba(0,0,0,0.12);
}

.menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.menu-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.menu-brand-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
}
.menu-brand-name {
  font-size: 1rem;
  font-weight: 700;
  color: #171717;
  letter-spacing: -0.02em;
}
.menu-close {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.08);
  background: #fff;
  color: #525252;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.menu-close:hover {
  background: #f5f5f5;
  color: #171717;
  transform: rotate(90deg);
}

.menu-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 14px 24px;
}
.menu-group {
  margin-bottom: 18px;
}
.menu-group-title {
  font-size: 0.65rem;
  font-weight: 700;
  color: #a3a3a3;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0 8px;
  margin-bottom: 6px;
}
.menu-group-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #525252;
  font-size: 0.9rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
  width: 100%;
}
.menu-item:hover {
  background: #f5f5f5;
  color: #171717;
}
.menu-item.active {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}
.menu-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.4;
}
.menu-item.active .menu-dot {
  opacity: 1;
}

/* Drawer Transitions */
.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(-100%);
}
</style>

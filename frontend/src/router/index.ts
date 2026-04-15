import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      meta: { titleKey: 'nav.home' },
      component: HomeView,
    },
    {
      path: '/strategies',
      name: 'strategies',
      meta: { titleKey: 'strategy.title' },
      component: () => import('../views/StrategyWorkshop.vue'),
    },
    {
      path: '/backtests',
      name: 'backtests',
      meta: { titleKey: 'backtest.title' },
      component: () => import('../views/BacktestCenter.vue'),
    },
    {
      path: '/paper-trading',
      name: 'paper-trading',
      meta: { titleKey: 'paperTrading.title' },
      component: () => import('../views/PaperTradingMonitor.vue'),
    },
    {
      path: '/stock-pickers',
      name: 'stock-pickers',
      meta: { titleKey: 'stockPicker.title' },
      component: () => import('../views/StockPicker.vue'),
    },
    {
      path: '/manual',
      name: 'manual',
      meta: { titleKey: 'manual.title' },
      component: () => import('../views/UserManual.vue'),
    },
  ],
})

export default router

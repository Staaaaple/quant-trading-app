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
      component: () => import('../views/strategies/StrategyLayout.vue'),
      redirect: '/strategies/trade',
      children: [
        {
          path: 'picker',
          name: 'strategy-picker',
          meta: { titleKey: 'stockPicker.title' },
          component: () => import('../views/strategies/PickerEditor.vue'),
        },
        {
          path: 'trade',
          name: 'strategy-trade',
          meta: { titleKey: 'strategy.title' },
          component: () => import('../views/strategies/TradeEditor.vue'),
        },
        {
          path: 'risk',
          name: 'strategy-risk',
          meta: { titleKey: 'strategy.riskTitle' },
          component: () => import('../views/strategies/RiskEditor.vue'),
        },
        {
          path: 'flow',
          name: 'strategy-flow',
          meta: { titleKey: 'strategy.flowTitle' },
          component: () => import('../views/strategies/FlowEditor.vue'),
        },
      ],
    },
    {
      path: '/backtests',
      name: 'backtests',
      meta: { titleKey: 'backtest.title' },
      component: () => import('../views/BacktestCenter.vue'),
    },
    {
      path: '/backtests/:backtest_id',
      name: 'backtest-detail',
      meta: { titleKey: 'backtest.detailTitle' },
      component: () => import('../views/BacktestDetail.vue'),
    },
    {
      path: '/paper-trading',
      name: 'paper-trading',
      meta: { titleKey: 'paperTrading.title' },
      component: () => import('../views/PaperTradingMonitor.vue'),
    },
    {
      path: '/manual',
      name: 'manual',
      meta: { titleKey: 'manual.title' },
      component: () => import('../views/UserManual.vue'),
    },
    {
      path: '/strategy-map',
      name: 'strategy-map',
      meta: { titleKey: 'strategyMap.title' },
      component: () => import('../views/StrategyMapView.vue'),
    },
    {
      path: '/dna-report/:strategy_id',
      name: 'dna-report',
      meta: { titleKey: 'dna.reportTitle' },
      component: () => import('../views/DNAReport.vue'),
    },
  ],
})

export default router

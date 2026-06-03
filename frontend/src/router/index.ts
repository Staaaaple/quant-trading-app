import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: HomeView,
    },
    {
      path: '/demo',
      name: 'demo',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/DemoView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/ProfileWizard.vue'),
    },
    {
      path: '/profile/result',
      name: 'profile-result',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/ProfileResult.vue'),
    },
    {
      path: '/market',
      name: 'market',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/MarketSignalView.vue'),
    },
    {
      path: '/portfolio',
      name: 'portfolio',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/PortfolioBuilder.vue'),
    },
    {
      path: '/recommendation',
      name: 'recommendation',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/StrategyRecommendation.vue'),
    },
    {
      path: '/lifespan',
      name: 'lifespan',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/LifespanCenter.vue'),
    },
    {
      path: '/backtests',
      name: 'backtests',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/BacktestCenter.vue'),
    },
    {
      path: '/backtests/:backtest_id',
      name: 'backtest-detail',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/BacktestDetail.vue'),
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/OnboardingGuide.vue'),
    },
    {
      path: '/today-operation',
      name: 'today-operation',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/TodayOperation.vue'),
    },
    {
      path: '/weekly-report',
      name: 'weekly-report',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/WeeklyReport.vue'),
    },
    // Legacy routes (保留原有功能)
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

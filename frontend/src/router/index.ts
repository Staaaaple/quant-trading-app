import { createRouter, createWebHistory } from 'vue-router'
import DemoView from '../views/DemoView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: DemoView,
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
      path: '/profile/summary',
      name: 'profile-summary',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/ProfileSummary.vue'),
    },
    {
      path: '/market/guide',
      name: 'market-guide',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/MarketGuideView.vue'),
    },
    {
      path: '/market',
      name: 'market',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/MarketSignalView.vue'),
    },
    {
      path: '/portfolio/guide',
      name: 'portfolio-guide',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/PortfolioGuideView.vue'),
    },
    {
      path: '/portfolio',
      name: 'portfolio',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/PortfolioBuilder.vue'),
    },
    {
      path: '/portfolio/strategies/guide',
      name: 'strategy-guide',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/StrategyGuideView.vue'),
    },
    {
      path: '/portfolio/strategies',
      name: 'portfolio-strategies',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/StrategyMatch.vue'),
    },
    {
      path: '/recommendation',
      name: 'recommendation',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/StrategyRecommendation.vue'),
    },
    {
      path: '/ecosystem',
      name: 'ecosystem',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/EcosystemView.vue'),
    },
    {
      path: '/building-guide',
      name: 'building-guide',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/BuildingGuide.vue'),
    },
    {
      path: '/ab-tests',
      name: 'ab-tests',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/ABTestDashboard.vue'),
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
      path: '/today-operation',
      name: 'today-operation',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/TodayOperation.vue'),
    },
    {
      path: '/market-report',
      name: 'market-report',
      meta: { titleKey: 'nav.home', layout: 'demo' },
      component: () => import('../views/MarketReport.vue'),
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

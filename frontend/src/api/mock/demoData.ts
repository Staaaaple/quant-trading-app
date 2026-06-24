/**
 * Demo/mock data converted from backend/app/services/demo_data.py
 * All data is static simulation, no external API dependencies.
 */

import { delay, now, today } from './utils'

// ── 演示用户名称 ──
export const DEMO_USER_NAME = '演示用户'

// ── 演示组合 ──
export const DEMO_PORTFOLIO: Record<string, any> = {
  portfolio_id: 'pf_demo_001',
  adopted: true,
  name: '演示稳健平衡组合',
  saa: {
    risk_profile: { name: '稳健型' },
    weights: {
      stock: 0.15,
      etf: 0.25,
      bond: 0.35,
      cash: 0.15,
      commodity: 0.10,
    },
    rationale: '基于稳健型画像的防御性战略资产配置：债券与现金提供安全垫，ETF 分散权益风险，个股适度增强',
    data_source: 'saa_engine (demo)',
  },
  taa: {
    overweight: ['国债ETF', '银行ETF'],
    underweight: ['科技ETF'],
    rationale: '当前市场周期下偏防御的战术调整，控制个股与高波动权益暴露',
    data_source: 'taa_engine (demo)',
  },
  bindings: [
    { symbol: '159995', name: '科技ETF', asset_class: 'ETF', weight: 0.0700, strategy_id: 'demo_s1', sector: '科技', sector_name: '科技' },
    { symbol: '159928', name: '消费ETF', asset_class: 'ETF', weight: 0.0600, strategy_id: 'demo_s2', sector: '消费', sector_name: '消费' },
    { symbol: '512800', name: '银行ETF', asset_class: 'ETF', weight: 0.0500, strategy_id: 'demo_s3', sector: '金融', sector_name: '金融' },
    { symbol: '512100', name: '工业ETF', asset_class: 'ETF', weight: 0.0300, strategy_id: 'demo_s4', sector: '工业', sector_name: '工业' },
    { symbol: '512170', name: '医疗ETF', asset_class: 'ETF', weight: 0.0400, strategy_id: 'demo_s5', sector: '医药', sector_name: '医药' },
    { symbol: '511010', name: '国债ETF', asset_class: 'bond', weight: 0.3500, strategy_id: 'demo_s6', sector: '债券', sector_name: '债券' },
    { symbol: '511880', name: '银华日利', asset_class: 'cash', weight: 0.1500, strategy_id: 'demo_s7', sector: '现金', sector_name: '现金' },
    { symbol: '518880', name: '黄金ETF', asset_class: 'commodity', weight: 0.1000, strategy_id: 'demo_s8', sector: '商品', sector_name: '商品' },
    { symbol: '300394', name: '天孚通信', asset_class: 'stock', weight: 0.1500, strategy_id: 'demo_s9', sector: '通信', sector_name: '通信' },
  ],
  risk_config: {
    stop_loss: 0.06,
    max_position: 0.12,
    max_drawdown: 0.10,
    rebalance_threshold: 0.03,
    risk_level: '中低风险',
    rationale: '演示风控配置：严格控制单一权益仓位与组合最大回撤',
    data_source: 'rule_engine (demo)',
  },
  reliability: {
    score: 84.0,
    confidence: 0.84,
    reliability_level: '高',
    backtest_available: true,
    stress_test_available: true,
    monte_carlo_available: true,
    adoption_status: { adopted: true, reason: '通过 RAG 质检' },
    rationale: '历史回测与压力测试表现稳定，波动率低于基准',
    data_source: 'backtest_summary (demo)',
  },
  portfolio_lifespan: 30,
  portfolio_health: 86,
  backtest_summary: {
    annual_return: 0.058,
    sharpe_ratio: 0.98,
    max_drawdown: 0.06,
    trade_count: 8,
    win_rate: 0.62,
    data_source: 'backtest_adapter (demo)',
  },
  created_at: now(),
  status: 'adopted',
  data_sources: {
    profile: 'demo_profile',
    market_signal: 'demo_market_signal',
    saa: 'saa_engine (demo)',
    taa: 'taa_engine (demo)',
    bindings: 'hybrid_designer (demo)',
    risk_config: 'rule_engine (demo)',
    reliability: 'backtest_summary (demo)',
  },
  dynamic_picking: null,
}

// ── 演示投资者画像 ──
export const DEMO_INVESTOR_PROFILE: Record<string, any> = {
  id: 1,
  user_id: 1,
  answers_json: {
    q1: 'b',
    q2: 'c',
    q3: 'a',
    q4: 'b',
    q5: 'c',
    q6: 'a',
    q7: 'b',
    q8: 'c',
    q9: 'b',
    q10: 'a',
    q11: 'b',
    q12: 'c',
    q13: 'b',
    q14: 'a',
    q15: 'b',
    q16: 'b',
    q17: 'c',
    q18: 'a',
  },
  risk_tolerance: 0.55,
  loss_aversion: 0.60,
  herding_tendency: 0.45,
  overconfidence: 0.40,
  delayed_gratification: 0.65,
  security_need: 0.70,
  time_horizon_score: 0.60,
  experience_level: 0.50,
  capital_tier: 0.55,
  income_stability: 0.65,
  debt_pressure: 0.30,
  information_processing: 0.55,
  social_pressure: 0.40,
  emergency_response: 0.60,
  anchoring_effect: 0.45,
  diversification_preference: 0.65,
  stop_loss_discipline: 0.55,
  emotional_stability: 0.60,
  risk_label: '稳健型',
  time_horizon_label: '中期',
  experience_label: '中等',
  is_active: true,
  created_at: now(),
  updated_at: now(),
}

// ── 演示市场信号 ──
export const DEMO_MARKET_SIGNAL: Record<string, any> = {
  date: today(),
  composite_score: 68.5,
  market_mood: '中性偏乐观',
  market_cycle: '复苏期',
  macro: {
    cycle_phase: '复苏',
    gdp_trend: '企稳',
    inflation_level: '温和',
    liquidity: '中性',
    interest_rate: '持平',
    score: 65.0,
    cycle_analysis: {
      final_phase: '复苏期',
      final_description: '经济从底部回升，企业盈利改善，风险偏好逐步恢复',
      final_asset_preference: '股票 > 债券 > 现金',
      confidence: 0.72,
      fused_coordinates: { x: 0.35, y: 0.55 },
      model_results: [
        { model: '美林时钟', phase: '复苏', description: '经济上行+通胀下行', asset_preference: '股票', score: 0.70, inputs: { gdp: 0.6, inflation: 0.3 } },
        { model: '货币信用周期', phase: '宽货币+宽信用', description: '流动性充裕，信用扩张', asset_preference: '股票', score: 0.75, inputs: { money: 0.7, credit: 0.6 } },
      ],
      consistency: 0.72,
      data_completeness: 0.85,
    },
  },
  geo: {
    overall_risk: 0.35,
    risk_level: '低',
    safe_haven_demand: '低',
    score: 75.0,
  },
  industry: {
    heatmap: { 半导体: 0.85, 银行: 0.70, 医药: 0.55, 白酒: 0.40, 新能源: 0.65 },
    recommended: ['半导体', '银行', '新能源'],
    avoid: ['白酒', '房地产'],
    score: 62.0,
  },
  social: {
    major_themes: ['AI算力', '国产替代', '高股息'],
    theme_strength: { 'AI算力': 0.80, '国产替代': 0.75, '高股息': 0.65 },
    consumer_confidence: '温和回升',
    score: 68.0,
  },
  internal: {
    equity_bond_spread: 0.035,
    sentiment: '中性偏乐观',
    style_rotation: '成长向价值切换中',
    volatility_regime: '低波动',
    score: 70.0,
  },
}

// ── 演示回测指标 ──
export const DEMO_BACKTEST_METRICS: Record<string, any> = {
  total_return: 0.145,
  annual_return: 0.058,
  annualized_return: 0.058,
  sharpe_ratio: 0.98,
  max_drawdown: 0.06,
  volatility: 0.12,
  trade_count: 8,
  win_rate: 0.62,
  avg_return_per_trade: 0.0073,
}

export const DEMO_BACKTEST_BENCHMARK_METRICS: Record<string, any> = {
  total_return: 0.1021,
  annual_return: 0.058,
  annualized_return: 0.058,
  sharpe_ratio: 0.78,
  max_drawdown: 0.14,
  volatility: 0.16,
}

// ── 演示回测 ──
export const DEMO_BACKTEST: Record<string, any> = {
  id: 1,
  backtest_id: 'bt_demo_001',
  strategy_id: 'demo_s1',
  status: 'success',
  start_date: '2023-01-01',
  end_date: '2024-12-31',
  initial_cash: 100000,
  metrics: DEMO_BACKTEST_METRICS,
  benchmark_metrics: DEMO_BACKTEST_BENCHMARK_METRICS,
  logs: '回测完成：总收益 14.5%，夏普比率 0.98，最大回撤 6%',
  created_at: now(),
  updated_at: now(),
}

// ── 演示市场报告：分页1 ──
const DEMO_PAGE1: Record<string, any> = {
  market_summary: '今日市场窄幅震荡，主要指数小幅收涨，北向资金净流入约 25 亿元。当前市场处于复苏期，综合情绪中性偏乐观，五层信号综合评分 68.5。',
  index_performance: {
    indices: [
      { name: '上证指数', symbol: '000001', change_pct: 0.34, open: 3040.12, high: 3055.67, low: 3038.45, close: 3050.21, prev_close: 3039.88, volume: 320000000, amount: 42000000000 },
      { name: '深证成指', symbol: '399001', change_pct: 0.52, open: 9769.33, high: 9845.18, low: 9741.26, close: 9820.14, prev_close: 9769.33, volume: 410000000, amount: 56000000000 },
      { name: '沪深300', symbol: '000300', change_pct: 0.41, open: 3565.80, high: 3592.15, low: 3558.92, close: 3580.66, prev_close: 3565.80, volume: 150000000, amount: 28000000000 },
      { name: '中证500', symbol: '000905', change_pct: 0.63, open: 5386.18, high: 5442.07, low: 5369.45, close: 5420.33, prev_close: 5386.18, volume: 180000000, amount: 24000000000 },
      { name: '创业板指', symbol: '399006', change_pct: 0.78, open: 1865.42, high: 1892.17, low: 1858.03, close: 1880.55, prev_close: 1865.42, volume: 220000000, amount: 32000000000 },
    ],
    intraday_narrative: '早盘小幅高开后震荡整理，午后科技板块带动指数走强，尾盘维持红盘报收。',
  },
  sector_performance: {
    sectors: [
      { name: '半导体', change_pct: 2.17, fund_flow: 1250000000, main_force: 850000000, rank: 1 },
      { name: '银行', change_pct: 1.05, fund_flow: 830000000, main_force: 520000000, rank: 2 },
      { name: '医药', change_pct: 0.34, fund_flow: 210000000, main_force: 120000000, rank: 4 },
      { name: '白酒', change_pct: -0.52, fund_flow: -420000000, main_force: -280000000, rank: 5 },
    ],
    fund_flow_summary: '主力资金净流入半导体、银行板块，白酒板块小幅流出。',
    intraday_narrative: '上午资金偏向防守，午后科技成长板块获得资金回流。',
  },
  policy_changes: {
    has_policy: false,
    summary: '今日无重大政策发布',
    policies: [],
  },
  risk_signals: {
    volatility_regime: '低波动',
    sentiment: '中性偏乐观',
    alerts: ['注意科技股分化', '关注北向资金流向'],
  },
  northbound_fund: {
    net_inflow: 25.3,
    cumulative_inflow: 1250.5,
    leading_sectors: ['半导体', '银行'],
    external_env: '美联储维持利率不变',
    inference: '外资延续净流入，偏好成长与金融板块',
  },
  outlook: {
    short_term: '预计市场维持震荡，个股分化加剧',
    medium_term: '关注业绩披露窗口与政策落地节奏',
    risks: ['外部地缘风险', '汇率波动', '科技股估值承压'],
  },
}

// ── 演示市场报告：分页2 ──
const DEMO_PAGE2: Record<string, any> = {
  portfolio_return: 0.0042,
  portfolio_return_pct: '+0.42%',
  benchmark_return: 0.0041,
  excess_return: 0.00007,
  summary: '今日组合小幅收涨，个股与科技板块贡献居前，黄金小幅回调。',
  asset_performances: [
    { symbol: '159995', name: '科技ETF', asset_class: 'ETF', weight: 0.0700, price: 2.92, change_pct: 1.85, daily_return: 0.0185, contribution: 0.00130 },
    { symbol: '159928', name: '消费ETF', asset_class: 'ETF', weight: 0.0600, price: 0.627, change_pct: 0.62, daily_return: 0.0062, contribution: 0.00037 },
    { symbol: '512800', name: '银行ETF', asset_class: 'ETF', weight: 0.0500, price: 0.771, change_pct: 0.98, daily_return: 0.0098, contribution: 0.00049 },
    { symbol: '512100', name: '工业ETF', asset_class: 'ETF', weight: 0.0300, price: 3.58, change_pct: -0.41, daily_return: -0.0041, contribution: -0.00012 },
    { symbol: '512170', name: '医疗ETF', asset_class: 'ETF', weight: 0.0400, price: 0.297, change_pct: 0.23, daily_return: 0.0023, contribution: 0.00009 },
    { symbol: '511010', name: '国债ETF', asset_class: 'bond', weight: 0.3500, price: 141.463, change_pct: 0.018, daily_return: 0.00018, contribution: 0.00006 },
    { symbol: '511880', name: '银华日利', asset_class: 'cash', weight: 0.1500, price: 100.541, change_pct: 0.003, daily_return: 0.00003, contribution: 0.00001 },
    { symbol: '518880', name: '黄金ETF', asset_class: 'commodity', weight: 0.1000, price: 8.716, change_pct: -0.28, daily_return: -0.0028, contribution: -0.00028 },
    { symbol: '300394', name: '天孚通信', asset_class: 'stock', weight: 0.1500, price: 326.12, change_pct: 1.50, daily_return: 0.0150, contribution: 0.00225 },
  ],
  best_contributor: { symbol: '300394', name: '天孚通信', asset_class: 'stock', weight: 0.15, price: 326.12, change_pct: 1.50, daily_return: 0.0150, contribution: 0.00225 },
  worst_contributor: { symbol: '518880', name: '黄金ETF', asset_class: 'commodity', weight: 0.10, price: 8.716, change_pct: -0.28, daily_return: -0.0028, contribution: -0.00028 },
}

// ── 演示市场报告：分页3（每周） ──
function getWeekStart(): string {
  const d = new Date()
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  const start = new Date(d.setDate(diff))
  return start.toISOString().split('T')[0]
}

function getWeekEnd(): string {
  const start = new Date(getWeekStart())
  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  return end.toISOString().split('T')[0]
}

const DEMO_PAGE3: Record<string, any> = {
  week_start: getWeekStart(),
  week_end: getWeekEnd(),
  market_summary: '本周市场先抑后扬，科技板块领涨，北向资金累计净流入约 80 亿元。',
  index_performance: {
    indices: [
      { name: '上证指数', symbol: '000001', change_pct: 1.2, open: 3015.33, high: 3060.18, low: 3008.92, close: 3050.21, prev_close: 3015.33, volume: 1500000000, amount: 200000000000 },
      { name: '深证成指', symbol: '399001', change_pct: 1.8, open: 9648.56, high: 9855.30, low: 9612.18, close: 9820.14, prev_close: 9648.56, volume: 1900000000, amount: 260000000000 },
      { name: '沪深300', symbol: '000300', change_pct: 1.5, open: 3528.24, high: 3595.10, low: 3512.67, close: 3580.66, prev_close: 3528.24, volume: 700000000, amount: 130000000000 },
    ],
    intraday_narrative: '周一至周三震荡整理，周四科技板块带动市场反弹，周五维持强势。',
  },
  sector_performance: {
    sectors: [
      { name: '半导体', change_pct: 4.5, fund_flow: 5800000000, main_force: 3900000000, rank: 1 },
      { name: '银行', change_pct: 2.2, fund_flow: 3100000000, main_force: 2100000000, rank: 2 },
      { name: '医药', change_pct: 0.8, fund_flow: 800000000, main_force: 520000000, rank: 3 },
    ],
    fund_flow_summary: '本周主力资金持续流入半导体与银行板块，医药板块小幅流入。',
    intraday_narrative: '资金从消费向科技成长切换，周期股表现分化。',
  },
  policy_changes: {
    has_policy: false,
    summary: '本周无重大政策发布',
    policies: [],
  },
  risk_signals: {
    volatility_regime: '中等波动',
    sentiment: '中性偏乐观',
    alerts: ['科技股短期涨幅较大', '关注周五美股走势'],
  },
  northbound_fund: {
    net_inflow: 80.6,
    cumulative_inflow: 1305.2,
    leading_sectors: ['半导体', '银行', '新能源'],
    external_env: '美元指数走弱，人民币汇率企稳',
    inference: '外资加仓成长与金融，风险偏好回升',
  },
  outlook: {
    short_term: '预计下周市场维持震荡，关注业绩披露',
    medium_term: '经济复苏预期延续，结构性机会为主',
    risks: ['外部地缘风险', '美联储政策预期变化'],
  },
}

// ── 演示日报 ──
export const DEMO_DAILY_REPORT: Record<string, any> = {
  user_id: 1,
  portfolio_id: 1,
  report_type: 'daily',
  report_date: today(),
  page1_market_overview: DEMO_PAGE1,
  page2_portfolio_performance: DEMO_PAGE2,
  page3_weekly_market: null,
}

// ── 演示周报 ──
export const DEMO_WEEKLY_REPORT: Record<string, any> = {
  user_id: 1,
  portfolio_id: 1,
  report_type: 'weekly',
  report_date: today(),
  page1_market_overview: DEMO_PAGE1,
  page2_portfolio_performance: DEMO_PAGE2,
  page3_weekly_market: DEMO_PAGE3,
}

// ── 演示模拟盘日记录（3天） ──
export const DEMO_PAPER_TRADING_DAILY_RECORDS: Record<string, any>[] = [
  {
    id: 1,
    user_id: 1,
    portfolio_id: 1,
    record_date: (() => { const d = new Date(); d.setDate(d.getDate() - 3); return d.toISOString().split('T')[0]; })(),
    daily_return: 0.008,
    cumulative_return: 0.008,
    nav: 1.008,
    report_id: null,
    asset_snapshot: null,
    created_at: now(),
    updated_at: null,
  },
  {
    id: 2,
    user_id: 1,
    portfolio_id: 1,
    record_date: (() => { const d = new Date(); d.setDate(d.getDate() - 2); return d.toISOString().split('T')[0]; })(),
    daily_return: -0.005,
    cumulative_return: 0.003,
    nav: 1.003,
    report_id: null,
    asset_snapshot: null,
    created_at: now(),
    updated_at: null,
  },
  {
    id: 3,
    user_id: 1,
    portfolio_id: 1,
    record_date: (() => { const d = new Date(); d.setDate(d.getDate() - 1); return d.toISOString().split('T')[0]; })(),
    daily_return: 0.012,
    cumulative_return: 0.015,
    nav: 1.015,
    report_id: null,
    asset_snapshot: null,
    created_at: now(),
    updated_at: null,
  },
]

// ── 演示模拟盘月统计 ──
export const DEMO_PAPER_TRADING_MONTHLY_STATS: Record<string, any>[] = [
  {
    id: 1,
    user_id: 1,
    portfolio_id: 1,
    year_month: (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`; })(),
    monthly_return: 0.015,
    cumulative_return_at_month_end: 0.015,
    record_count: 3,
    created_at: now(),
    updated_at: null,
  },
]

// ── 演示用户 ──
export const DEMO_USER: Record<string, any> = {
  id: 1,
  name: DEMO_USER_NAME,
  avatar_url: null,
  is_active: true,
  is_demo: true,
  created_at: now(),
  updated_at: now(),
}

// ── 演示策略列表 ──
export const DEMO_STRATEGIES: Record<string, any>[] = [
  { id: 1, strategy_id: 'demo_s1', name: '科技ETF趋势策略', type: 'trend', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['ma20', 'rsi'] }, created_at: now(), updated_at: now() },
  { id: 2, strategy_id: 'demo_s2', name: '消费ETF均值回归', type: 'mean_reversion', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['bollinger', 'zscore'] }, created_at: now(), updated_at: now() },
  { id: 3, strategy_id: 'demo_s3', name: '银行ETF高股息', type: 'dividend', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['dy', 'pe'] }, created_at: now(), updated_at: now() },
  { id: 4, strategy_id: 'demo_s4', name: '工业ETF周期跟踪', type: 'cycle', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['pmi', 'inventory'] }, created_at: now(), updated_at: now() },
  { id: 5, strategy_id: 'demo_s5', name: '医疗ETF防御配置', type: 'defensive', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['beta', 'volatility'] }, created_at: now(), updated_at: now() },
  { id: 6, strategy_id: 'demo_s6', name: '国债ETF利率策略', type: 'rate', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['yield_curve'] }, created_at: now(), updated_at: now() },
  { id: 7, strategy_id: 'demo_s7', name: '现金管理策略', type: 'cash', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: null, created_at: now(), updated_at: now() },
  { id: 8, strategy_id: 'demo_s8', name: '黄金ETF避险策略', type: 'safe_haven', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['usd_index', 'real_rate'] }, created_at: now(), updated_at: now() },
  { id: 9, strategy_id: 'demo_s9', name: '天孚通信成长策略', type: 'growth', code: 'def handle_bar(context, bar):\n    pass', pipeline_config: { indicators: ['revenue_growth', 'margin'] }, created_at: now(), updated_at: now() },
]

// ── 演示策略DNA ──
export const DEMO_DNA: Record<string, any> = {
  strategy_id: 'demo_s1',
  feature_genes: ['ma20', 'volume_ratio', 'atr'],
  signal_genes: ['crossover', 'momentum_break'],
  risk_genes: ['max_drawdown_guard', 'position_limit'],
  execution_genes: ['twap', 'slippage_control'],
  gene_diversity_score: 0.78,
  health_birth_score: 0.82,
  inbreeding_coefficient: 0.15,
  family_id: 'family_trend',
  family_name: '趋势家族',
  sequence_version: 'v1.0',
  sequenced_at: now(),
  status: 'active',
  error_message: null,
  metabolic_rate: 0.65,
  niche_width: 0.70,
  metabolic_syndrome: false,
  metabolic_markers: ['stable'],
  lifespan_months: 24,
  lifespan_phase: 'mature',
  lifespan_phase_label: '成熟期',
  aging_velocity: 0.12,
  lifespan_recommendations: ['定期再训练', '监控过拟合'],
}

// ── 演示策略流 ──
export const DEMO_STRATEGY_FLOWS: Record<string, any>[] = [
  { id: 1, flow_id: 'flow_demo_001', name: '主交易流', picker_strategy_id: null, risk_strategy_id: null, trade_strategy_id: 'demo_s1', created_at: now(), updated_at: now() },
]

// ── 演示股票池 ──
export const DEMO_STOCK_POOLS: Record<string, any>[] = [
  {
    id: 1,
    pool_id: 'pool_demo_001',
    picker_id: 'picker_demo_001',
    name: '本周精选池',
    is_builtin_weekly: true,
    generated_at: now(),
    expires_at: (() => { const d = new Date(); d.setDate(d.getDate() + 7); return d.toISOString(); })(),
    items: [
      { id: 1, symbol: '300394', name: '天孚通信', score: 0.85, reason: '光模块龙头，业绩高增' },
      { id: 2, symbol: '159995', name: '科技ETF', score: 0.78, reason: 'AI算力主题' },
      { id: 3, symbol: '512800', name: '银行ETF', score: 0.72, reason: '高股息防御' },
    ],
  },
]

// ── 演示选股运行记录 ──
export const DEMO_PICKER_RUNS: Record<string, any>[] = [
  { id: 1, run_id: 'run_demo_001', picker_id: 'picker_demo_001', status: 'success', result_count: 3, logs: '选股完成', created_at: now(), finished_at: now() },
]

// ── 演示风控策略 ──
export const DEMO_RISK_STRATEGY: Record<string, any> = {
  strategy_id: 'demo_risk_001',
  max_position_pct: 0.15,
  max_daily_drawdown: 0.03,
  blacklist: 'ST,*ST',
}

// ── 演示账户设置 ──
export const DEMO_ACCOUNT_SETTINGS: Record<string, any> = {
  id: 1,
  commission_rate: 0.00025,
  min_commission: 5,
  stamp_tax_rate: 0.001,
  transfer_fee_rate: 0.00002,
  is_sh_market: true,
}

// ── 演示同步数据 ──
export const DEMO_REAL_TRADES: Record<string, any>[] = [
  { id: 1, signal_id: 'sig_001', strategy_id: 'demo_s1', symbol: '300394', side: 'buy', quantity: 100, price: 320.0, commission: 8.0, stamp_tax: 0, transfer_fee: 0.64, total_cost: 32008.64, sync_status: 'synced', source: 'manual', remark: null, synced_at: now() },
]

export const DEMO_REAL_POSITIONS: Record<string, any>[] = [
  { id: 1, strategy_id: 'demo_s1', symbol: '300394', quantity: 100, available_qty: 100, avg_cost: 320.0, total_cost: 32000.0, market_value: 32612.0, floating_pnl: 612.0, updated_at: now() },
]

export const DEMO_SYNC_LOGS: Record<string, any>[] = []

export const DEMO_PAPER_SIGNALS: Record<string, any>[] = [
  { id: 1, signal_id: 'sig_001', strategy_id: 'demo_s1', symbol: '300394', side: 'buy', quantity: 100, price: 320.0, status: 'executed', remark: null, signal_at: now() },
]

// ── 演示画像问题 ──
export const DEMO_QUESTIONS: Record<string, any>[] = [
  { id: 'q1', category: '风险承受', question: '如果您的投资组合在一个月内下跌20%，您会怎么做？', options: [{ label: '立即全部卖出', scores: { risk_tolerance: 0.1 } }, { label: '卖出部分', scores: { risk_tolerance: 0.4 } }, { label: '继续持有', scores: { risk_tolerance: 0.7 } }, { label: '逢低加仓', scores: { risk_tolerance: 0.9 } }] },
  { id: 'q2', category: '投资期限', question: '您计划的投资期限是多久？', options: [{ label: '1年以内', scores: { time_horizon_score: 0.2 } }, { label: '1-3年', scores: { time_horizon_score: 0.5 } }, { label: '3-5年', scores: { time_horizon_score: 0.7 } }, { label: '5年以上', scores: { time_horizon_score: 0.9 } }] },
]

// ── 演示回测适配器结果 ──
export const DEMO_BACKTEST_ADAPTER_RESULT: Record<string, any> = {
  backtest_id: 'bt_adapter_demo_001',
  status: 'success',
  metrics: {
    total_return: 0.145,
    annual_return: 0.058,
    sharpe_ratio: 0.98,
    max_drawdown: 0.06,
    volatility: 0.12,
    win_rate: 0.62,
  },
  benchmark_metrics: {
    total_return: 0.1021,
    annual_return: 0.058,
    max_drawdown: 0.14,
  },
  trades: [
    { date: '2023-03-15', symbol: '300394', action: 'buy', quantity: 100, price: 280.0 },
    { date: '2023-06-20', symbol: '159995', action: 'buy', quantity: 500, price: 2.5 },
    { date: '2023-09-10', symbol: '300394', action: 'sell', quantity: 50, price: 310.0 },
  ],
  daily_values: [
    { date: '2023-01-01', value: 100000 },
    { date: '2023-06-01', value: 105000 },
    { date: '2023-12-01', value: 110000 },
    { date: '2024-12-31', value: 114500 },
  ],
}

// ── 演示生态系统概览 ──
export const DEMO_ECOSYSTEM: Record<string, any> = {
  total_strategies: 9,
  family_count: 5,
  avg_health_score: 0.78,
  min_health_score: 0.65,
  max_health_score: 0.88,
  avg_diversity: 0.72,
  inbreeding_risk_count: 1,
  family_distribution: [
    { name: '趋势家族', count: 3 },
    { name: '均值回归家族', count: 2 },
    { name: '防御家族', count: 2 },
    { name: '周期家族', count: 1 },
    { name: '成长家族', count: 1 },
  ],
  health_distribution: { excellent: 3, good: 4, fair: 2 },
  low_health_strategies: [],
  recent_strategies: [
    { strategy_id: 'demo_s9', name: '天孚通信成长策略', health_birth_score: 0.85, gene_diversity_score: 0.80, family_name: '成长家族' },
  ],
  avg_metabolic_rate: 0.60,
  avg_niche_width: 0.65,
  syndrome_count: 0,
  high_metabolic_strategies: [],
  avg_lifespan: 20,
  lifespan_distribution: { young: 3, mature: 4, aging: 2 },
  endangered_count: 0,
  short_lifespan_strategies: [],
  metabolic_ranking: [
    { strategy_id: 'demo_s1', name: '科技ETF趋势策略', metabolic_rate: 0.65, niche_width: 0.70, family_name: '趋势家族' },
  ],
  family_radar: [
    { name: '趋势家族', value: [0.8, 0.7, 0.6, 0.75, 0.65] },
  ],
  radar_indicators: [
    { name: '健康度', max: 1 },
    { name: '多样性', max: 1 },
    { name: '代谢率', max: 1 },
    { name: '寿命', max: 1 },
    { name: '生态位', max: 1 },
  ],
  family_network: {
    nodes: [
      { id: 'demo_s1', name: '科技ETF趋势策略', family: '趋势家族', family_id: 'family_trend', health: 0.82, lifespan: 24, metabolic_rate: 0.65, value: 1, symbolSize: 20 },
    ],
    links: [
      { source: 'demo_s1', target: 'demo_s2', value: 0.5 },
    ],
  },
}

// ── 演示组合设计结果（用于 portfolioApi.design） ──
export const DEMO_PORTFOLIO_DESIGN_RESULT: Record<string, any> = {
  success: true,
  adopted: true,
  portfolio: {
    portfolio_id: 'pf_demo_001',
    adopted: true,
    saa: {
      weights: {
        stock: 0.15,
        etf: 0.25,
        bond: 0.35,
        cash: 0.15,
        commodity: 0.10,
      },
      rationale: '基于稳健型画像的防御性战略资产配置',
      risk_profile: { name: '稳健型' },
    },
    taa: {
      overweight: ['国债ETF', '银行ETF'],
      underweight: ['科技ETF'],
      rationale: '当前市场周期下偏防御的战术调整',
    },
    bindings: DEMO_PORTFOLIO.bindings.map((b: any) => ({
      ...b,
      strategy_name: b.name,
      strategy_family: 'demo',
      health_score: 80,
      lifespan_months: 24,
      backtest_warnings: [],
      data_source: 'demo',
    })),
    risk_config: {
      stop_loss: 0.06,
      max_position: 0.12,
      max_drawdown: 0.10,
      rebalance_threshold: 0.03,
      rationale: '演示风控配置',
    },
    reliability: {
      confidence: 0.84,
      reliability_level: '高',
      backtest_available: true,
      stress_test_available: true,
      monte_carlo_available: true,
      benchmark_comparison: {
        custom_benchmark: { name: '自定义基准', description: '60/40组合', benchmark_return: 0.058, strategy_return: 0.058, excess_return: 0, benchmark_drawdown: 0.08, strategy_drawdown: 0.06, passed: true, score: 85 },
        csi300: { name: '沪深300', description: '沪深300指数', benchmark_return: 0.045, strategy_return: 0.058, excess_return: 0.013, benchmark_drawdown: 0.18, strategy_drawdown: 0.06, passed: true, score: 80 },
        equal_weight: { name: '等权', description: '等权配置', benchmark_return: 0.05, strategy_return: 0.058, excess_return: 0.008, benchmark_drawdown: 0.15, strategy_drawdown: 0.06, passed: true, score: 75 },
        sixty_forty: { name: '60/40', description: '股债60/40', benchmark_return: 0.055, strategy_return: 0.058, excess_return: 0.003, benchmark_drawdown: 0.12, strategy_drawdown: 0.06, passed: true, score: 70 },
        overall_score: 78,
        strategy_return: 0.058,
        strategy_drawdown: 0.06,
      },
      adoption_status: { adopted: true, threshold: 0.7, confidence: 0.84, reason: '通过 RAG 质检' },
    },
    portfolio_lifespan: 30,
    portfolio_health: 86,
    status: 'adopted',
  },
  validation: {
    valid: true,
    issues: [],
    warnings: [],
  },
  summary: {
    total_strategies: 9,
    stock_ratio: '15%',
    top_sector: '债券',
    risk_level: '中低风险',
    expected_lifespan: '30个月',
    health_score: 86,
  },
  rag_reviews: [
    { step: 'SAA检查', passed: true, issues: [], suggestions: [] },
    { step: 'TAA检查', passed: true, issues: [], suggestions: [] },
    { step: '绑定检查', passed: true, issues: [], suggestions: [] },
  ],
  rag_adjusted: false,
  rag_adjustment_count: 0,
}

// ── 演示组合任务 ──
export const DEMO_PORTFOLIO_TASK: Record<string, any> = {
  task_id: 1,
  user_id: 1,
  status: 'completed',
  current_step: '完成',
  progress: 100,
  result: DEMO_PORTFOLIO_DESIGN_RESULT,
  error_message: null,
  created_at: now(),
  updated_at: now(),
  completed_at: now(),
}

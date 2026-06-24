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
    q1_capital: '5万-20万',
    q2_age: '36-45岁',
    q3_experience: ['基金'],
    q4_income_stability: '一般，偶尔波动',
    q5_debt_pressure: '10%-30%',
    q6_diversification: '2-3种（如银行理财+基金）',
    q7_risk_tolerance: '10%-20%',
    q8_stop_loss: '偶尔执行',
    q9_loss_scenario: '不动，等反弹',
    q10_anchoring: '看趋势决定，不纠结成本',
    q11_time_horizon: '1年',
    q12_security_need: '要卖一部分投资',
    q13_herding: '先研究一下再决定',
    q14_overconfidence: '市场好，运气好',
    q15_info_processing: '结合多个来源交叉验证',
    q16_delayed_gratification: '继续持有，等更高收益',
    q17_social_pressure: '不受影响，按自己节奏',
    q18_emotional_stability: '暂停交易，冷静分析原因',
  },
  // 18维 profile_vector，由 backend compute_profile_vector() 逻辑计算得出
  risk_tolerance: 5.0,
  loss_aversion: 3.33,
  herding_tendency: 2.67,
  overconfidence: 3.0,
  delayed_gratification: 6.5,
  security_need: 5.5,
  time_horizon_score: 6.5,
  experience_level: 4.0,
  capital_tier: 4.5,
  income_stability: 4.0,
  debt_pressure: 5.0,
  information_processing: 6.8,
  social_pressure: 2.0,
  emergency_response: 3.0,
  anchoring_effect: 2.0,
  diversification_preference: 4.0,
  stop_loss_discipline: 6.0,
  emotional_stability: 6.0,
  risk_label: '稳健型',
  time_horizon_label: '中期',
  experience_label: '新手',
  is_active: true,
  created_at: now(),
  updated_at: now(),
}

// ── 演示市场信号 ──
export const DEMO_MARKET_SIGNAL: Record<string, any> = {
  date: today(),
  composite_score: 68.5,
  market_mood: '中性偏悲观',
  market_cycle: '衰退期',
  macro: {
    cycle_phase: '衰退',
    gdp_trend: '下行',
    inflation_level: '下行',
    liquidity: '偏紧',
    interest_rate: '下行',
    score: 42.0,
    cycle_analysis: {
      final_phase: '衰退期',
      final_description: '经济下行、通胀回落，企业盈利承压，风险资产承压，防御性资产配置优先',
      final_asset_preference: '债券 > 现金 > 股票',
      confidence: 0.68,
      fused_coordinates: { x: 0.25, y: 0.35 },
      model_results: [
        { model: '美林时钟', phase: '衰退', description: '经济下行+通胀下行', asset_preference: '债券', score: 0.75, inputs: { gdp: 0.3, inflation: 0.2 } },
        { model: '货币信用周期', phase: '宽货币+紧信用', description: '流动性宽松但信用扩张不足', asset_preference: '债券', score: 0.65, inputs: { money: 0.7, credit: 0.3 } },
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

// ── 策略家族映射 ──
const STRATEGY_FAMILY_MAP: Record<string, { family_id: string; family_name: string }> = {
  demo_s1: { family_id: 'family_trend', family_name: '趋势家族' },
  demo_s2: { family_id: 'family_mr', family_name: '均值回归家族' },
  demo_s3: { family_id: 'family_value', family_name: '价值家族' },
  demo_s4: { family_id: 'family_cycle', family_name: '周期家族' },
  demo_s5: { family_id: 'family_def', family_name: '防御家族' },
  demo_s6: { family_id: 'family_fixed', family_name: '固定收益家族' },
  demo_s7: { family_id: 'family_cash', family_name: '现金家族' },
  demo_s8: { family_id: 'family_commodity', family_name: '商品家族' },
  demo_s9: { family_id: 'family_growth', family_name: '成长家族' },
}

const STRATEGY_NAMES: Record<string, string> = {
  demo_s1: '科技ETF趋势策略',
  demo_s2: '消费ETF均值回归',
  demo_s3: '银行ETF高股息',
  demo_s4: '工业ETF周期跟踪',
  demo_s5: '医疗ETF防御配置',
  demo_s6: '国债ETF利率策略',
  demo_s7: '现金管理策略',
  demo_s8: '黄金ETF避险策略',
  demo_s9: '天孚通信成长策略',
}

// ── 按资产类型生成差异化回测指标（与 backend get_demo_backtest_metrics 一致） ──
function makeMetrics(seed: string, assetClass: string): Record<string, any> {
  // 确定性伪随机
  function _seedFloat(s: string, low: number, high: number): number {
    let h = 0
    for (let i = 0; i < s.length; i++) {
      h = ((h << 5) - h + s.charCodeAt(i)) | 0
    }
    h = Math.abs(h)
    return low + (h % 10000) / 10000 * (high - low)
  }

  let baseReturn: number, volatility: number, maxDd: number

  if (assetClass === 'bond') {
    baseReturn = _seedFloat(seed + '_ret', 0.020, 0.045)
    volatility = _seedFloat(seed + '_vol', 0.020, 0.040)
    maxDd = _seedFloat(seed + '_dd', 0.010, 0.030)
  } else if (assetClass === 'cash') {
    baseReturn = _seedFloat(seed + '_ret', 0.005, 0.020)
    volatility = _seedFloat(seed + '_vol', 0.001, 0.005)
    maxDd = 0.0
  } else if (assetClass === 'commodity') {
    baseReturn = _seedFloat(seed + '_ret', 0.030, 0.080)
    volatility = _seedFloat(seed + '_vol', 0.100, 0.160)
    maxDd = _seedFloat(seed + '_dd', 0.050, 0.120)
  } else if (assetClass === 'stock') {
    baseReturn = _seedFloat(seed + '_ret', -0.050, 0.150)
    volatility = _seedFloat(seed + '_vol', 0.220, 0.380)
    maxDd = _seedFloat(seed + '_dd', 0.100, 0.250)
  } else {
    // ETF
    baseReturn = _seedFloat(seed + '_ret', 0.020, 0.100)
    volatility = _seedFloat(seed + '_vol', 0.120, 0.220)
    maxDd = _seedFloat(seed + '_dd', 0.060, 0.150)
  }

  const sharpe = volatility > 0 ? baseReturn / volatility : 0.0
  const winRate = _seedFloat(seed + '_wr', 0.45, 0.70)
  const tradeCount = Math.floor(_seedFloat(seed + '_tc', 5, 25))
  const totalReturn = baseReturn * _seedFloat(seed + '_tr', 1.5, 2.5)
  const sortino = sharpe * 1.15
  const calmar = maxDd > 0 ? baseReturn / maxDd : baseReturn * 10
  const exposureTime = _seedFloat(seed + '_exp', 0.40, 0.85)

  return {
    total_return: Math.round(totalReturn * 10000) / 10000,
    annual_return: Math.round(baseReturn * 10000) / 10000,
    annualized_return: Math.round(baseReturn * 10000) / 10000,
    sharpe_ratio: Math.round(sharpe * 100) / 100,
    sortino_ratio: Math.round(sortino * 100) / 100,
    calmar_ratio: Math.round(calmar * 100) / 100,
    max_drawdown: Math.round(maxDd * 10000) / 10000,
    volatility: Math.round(volatility * 10000) / 10000,
    win_rate: Math.round(winRate * 100) / 100,
    trade_count: tradeCount,
    avg_return_per_trade: Math.round((baseReturn / (tradeCount || 1)) * 10000) / 10000,
    exposure_time_pct: Math.round(exposureTime * 100) / 100,
    total_bars: 252,
  }
}

const ASSET_CLASSES: Record<string, string> = {
  demo_s1: 'ETF',
  demo_s2: 'ETF',
  demo_s3: 'ETF',
  demo_s4: 'ETF',
  demo_s5: 'ETF',
  demo_s6: 'bond',
  demo_s7: 'cash',
  demo_s8: 'commodity',
  demo_s9: 'stock',
}

// ── 演示回测指标（组合级，向后兼容） ──
export const DEMO_BACKTEST_METRICS: Record<string, any> = makeMetrics('demo_portfolio', 'ETF')

export const DEMO_BACKTEST_BENCHMARK_METRICS: Record<string, any> = {
  total_return: 0.1021,
  annual_return: 0.058,
  annualized_return: 0.058,
  sharpe_ratio: 0.78,
  max_drawdown: 0.14,
  volatility: 0.16,
  win_rate: 0.55,
  trade_count: 0,
  exposure_time_pct: 1.0,
  total_bars: 252,
}

// ── 演示回测列表（9条，与组合 bindings 一一对应） ──
function makeBacktest(strategyId: string, idx: number): Record<string, any> {
  const assetClass = ASSET_CLASSES[strategyId] || 'ETF'
  const metrics = makeMetrics(strategyId, assetClass)
  const startDate = '2023-01-01'
  const endDate = '2024-12-31'
  const backtestId = `bt_${strategyId}_2023_2024`

  // 生成模拟 K 线和交易日志
  const candles: any[] = []
  const trades: any[] = []
  const riskBlocks: any[] = []
  let price = 100.0
  const dates: string[] = []
  for (let i = 0; i < 60; i++) {
    const d = new Date('2023-06-01')
    d.setDate(d.getDate() + i * 4)
    dates.push(d.toISOString().split('T')[0])
    const change = (Math.random() - 0.48) * (assetClass === 'stock' ? 8 : assetClass === 'commodity' ? 5 : 2)
    const open = price
    const close = price + change
    const high = Math.max(open, close) + Math.random() * 2
    const low = Math.min(open, close) - Math.random() * 2
    candles.push({ date: dates[dates.length - 1], open: Math.round(open * 100) / 100, close: Math.round(close * 100) / 100, high: Math.round(high * 100) / 100, low: Math.round(low * 100) / 100 })
    price = close

    // 偶尔插入交易
    if (i === 10) {
      trades.push({ entry_time: dates[dates.length - 1] + ' 10:00:00', entry_price: Math.round(open * 100) / 100, symbol: 'DEMO', quantity: 100 })
    }
    if (i === 35 && trades.length > 0) {
      trades[0].exit_time = dates[dates.length - 1] + ' 14:00:00'
      trades[0].exit_price = Math.round(close * 100) / 100
      trades[0].pnl = Math.round((close - trades[0].entry_price) * 100 * 100) / 100
    }
  }

  riskBlocks.push({
    type: 'position_limit',
    level: 'info',
    message: '仓位控制在限制范围内',
    timestamp: dates[dates.length - 1] + ' 15:00:00',
  })

  const logs = JSON.stringify({
    candles: { DEMO: candles },
    trades,
    risk_blocks: riskBlocks,
  })

  return {
    id: idx + 1,
    backtest_id: backtestId,
    strategy_id: strategyId,
    status: 'success',
    start_date: startDate,
    end_date: endDate,
    initial_cash: 100000,
    metrics,
    benchmark_metrics: DEMO_BACKTEST_BENCHMARK_METRICS,
    logs,
    created_at: (() => { const d = new Date(); d.setDate(d.getDate() - (9 - idx)); return d.toISOString(); })(),
    updated_at: now(),
  }
}

export const DEMO_BACKTESTS: Record<string, any>[] = [
  'demo_s1', 'demo_s2', 'demo_s3', 'demo_s4', 'demo_s5',
  'demo_s6', 'demo_s7', 'demo_s8', 'demo_s9',
].map((sid, i) => makeBacktest(sid, i))

// 保留单条向后兼容
export const DEMO_BACKTEST = DEMO_BACKTESTS[0]

// ── 演示市场报告：分页1 ──
const DEMO_PAGE1: Record<string, any> = {
  market_summary: '今日市场窄幅震荡，主要指数小幅收跌，北向资金净流出约 15 亿元。当前市场处于衰退期，综合情绪中性偏悲观，五层信号综合评分 42.0。',
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

// ── 演示策略DNA（9条，与 bindings 一一对应） ──
function makeDNA(strategyId: string): Record<string, any> {
  const fam = STRATEGY_FAMILY_MAP[strategyId]
  const name = STRATEGY_NAMES[strategyId]

  // 确定性伪随机辅助
  function _seedFloat(s: string, low: number, high: number): number {
    let h = 0
    for (let i = 0; i < s.length; i++) {
      h = ((h << 5) - h + s.charCodeAt(i)) | 0
    }
    h = Math.abs(h)
    return low + (h % 10000) / 10000 * (high - low)
  }

  const diversity = _seedFloat(strategyId + '_div', 0.55, 0.92)
  const health = _seedFloat(strategyId + '_health', 65, 95)
  const inbreeding = _seedFloat(strategyId + '_inb', 0.05, 0.35)
  const metabolic = _seedFloat(strategyId + '_meta', 0.30, 0.85)
  const niche = _seedFloat(strategyId + '_niche', 0.40, 0.90)
  const lifespan = Math.floor(_seedFloat(strategyId + '_life', 6, 42))
  const aging = _seedFloat(strategyId + '_aging', 0.05, 0.25)

  const genePools: Record<string, string[]> = {
    demo_s1: { f: ['ma20', 'volume_ratio', 'atr'], s: ['crossover', 'momentum_break'], r: ['max_drawdown_guard', 'position_limit'], e: ['twap', 'slippage_control'] },
    demo_s2: { f: ['bollinger', 'zscore', 'mean_deviation'], s: ['reversion_signal', 'oversold_bounce'], r: ['time_stop', 'volatility_guard'], e: ['vwap', 'iceberg'] },
    demo_s3: { f: ['dy', 'pe', 'pb'], s: ['dividend_yield_filter', 'value_screen'], r: ['sector_limit', 'concentration_guard'], e: ['twap', 'market_on_close'] },
    demo_s4: { f: ['pmi', 'inventory_turnover', 'capacity_utilization'], s: ['cycle_phase', 'inventory_signal'], r: ['drawdown_guard', 'trend_filter'], e: ['vwap', 'participation'] },
    demo_s5: { f: ['beta', 'volatility', 'defensive_score'], s: ['low_beta_filter', 'defensive_trigger'], r: ['max_position', 'stop_loss'], e: ['twap', 'slippage_control'] },
    demo_s6: { f: ['yield_curve', 'duration', 'credit_spread'], s: ['rate_direction', 'curve_steepness'], r: ['duration_limit', 'credit_guard'], e: ['twap', 'market_on_close'] },
    demo_s7: { f: ['liquidity', 'maturity'], s: ['cash_signal'], r: ['liquidity_guard'], e: ['market_on_close'] },
    demo_s8: { f: ['usd_index', 'real_rate', 'safe_haven_score'], s: ['gold_momentum', 'risk_off_trigger'], r: ['volatility_guard', 'drawdown_guard'], e: ['vwap', 'slippage_control'] },
    demo_s9: { f: ['revenue_growth', 'margin', 'roe'], s: ['growth_momentum', 'earnings_surprise'], r: ['position_limit', 'stop_loss'], e: ['twap', 'iceberg'] },
  }

  const genes = genePools[strategyId] || { f: ['feature_a'], s: ['signal_a'], r: ['risk_a'], e: ['exec_a'] }

  return {
    strategy_id: strategyId,
    feature_genes: genes.f,
    signal_genes: genes.s,
    risk_genes: genes.r,
    execution_genes: genes.e,
    gene_diversity_score: Math.round(diversity * 100) / 100,
    health_birth_score: Math.round(health * 100) / 100,
    inbreeding_coefficient: Math.round(inbreeding * 100) / 100,
    family_id: fam.family_id,
    family_name: fam.family_name,
    sequence_version: 'v1.0',
    sequenced_at: now(),
    status: 'active',
    error_message: null,
    metabolic_rate: Math.round(metabolic * 100) / 100,
    niche_width: Math.round(niche * 100) / 100,
    metabolic_syndrome: metabolic > 0.7 && niche < 0.5,
    metabolic_markers: metabolic > 0.7 ? ['high_turnover'] : ['stable'],
    lifespan_months: lifespan,
    lifespan_phase: lifespan >= 36 ? 'young' : lifespan >= 12 ? 'mature' : lifespan >= 3 ? 'aging' : 'endangered',
    lifespan_phase_label: lifespan >= 36 ? '年轻期' : lifespan >= 12 ? '成熟期' : lifespan >= 3 ? '衰老期' : '濒危期',
    aging_velocity: Math.round(aging * 100) / 100,
    lifespan_recommendations: ['定期再训练', '监控过拟合'],
  }
}

export const DEMO_DNA_MAP: Record<string, Record<string, any>> = {
  demo_s1: makeDNA('demo_s1'),
  demo_s2: makeDNA('demo_s2'),
  demo_s3: makeDNA('demo_s3'),
  demo_s4: makeDNA('demo_s4'),
  demo_s5: makeDNA('demo_s5'),
  demo_s6: makeDNA('demo_s6'),
  demo_s7: makeDNA('demo_s7'),
  demo_s8: makeDNA('demo_s8'),
  demo_s9: makeDNA('demo_s9'),
}

// 保留单条向后兼容（默认返回 demo_s1）
export const DEMO_DNA = DEMO_DNA_MAP['demo_s1']

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

// ── 演示画像问题（18题，与 backend QUESTIONS 完全一致） ──
export const DEMO_QUESTIONS: Record<string, any>[] = [
  // ===== Step 1: 基本信息 (6题) =====
  {
    id: 'q1_capital',
    category: 'basic',
    question: '你的投资资金规模是多少？',
    options: [
      { label: '小于5万', scores: { capital_tier: 2 } },
      { label: '5万-20万', scores: { capital_tier: 4 } },
      { label: '20万-100万', scores: { capital_tier: 6 } },
      { label: '大于100万', scores: { capital_tier: 9 } },
    ],
  },
  {
    id: 'q2_age',
    category: 'basic',
    question: '你的年龄区间？',
    options: [
      { label: '18-25岁', scores: { time_horizon_score: 9 } },
      { label: '26-35岁', scores: { time_horizon_score: 8 } },
      { label: '36-45岁', scores: { time_horizon_score: 6 } },
      { label: '46-55岁', scores: { time_horizon_score: 4 } },
      { label: '55岁以上', scores: { time_horizon_score: 2 } },
    ],
  },
  {
    id: 'q3_experience',
    category: 'basic',
    question: '你买过哪些投资产品？（可多选）',
    multi: true,
    options: [
      { label: '银行理财/余额宝', scores: { experience_level: 2, risk_tolerance: 3 } },
      { label: '基金', scores: { experience_level: 4, risk_tolerance: 4 } },
      { label: '股票', scores: { experience_level: 6, risk_tolerance: 6 } },
      { label: '期货/期权/加密货币', scores: { experience_level: 9, risk_tolerance: 8 } },
    ],
  },
  {
    id: 'q4_income_stability',
    category: 'basic',
    question: '你的月收入稳定性如何？',
    options: [
      { label: '自由职业/不稳定', scores: { income_stability: 2 } },
      { label: '一般，偶尔波动', scores: { income_stability: 4 } },
      { label: '较稳定，偶有奖金', scores: { income_stability: 6 } },
      { label: '非常稳定（公务员/大厂等）', scores: { income_stability: 9 } },
    ],
  },
  {
    id: 'q5_debt_pressure',
    category: 'basic',
    question: '每月还贷/负债占收入的比例？',
    options: [
      { label: '无负债', scores: { debt_pressure: 1, security_need: 3 } },
      { label: '10%以下', scores: { debt_pressure: 2, security_need: 4 } },
      { label: '10%-30%', scores: { debt_pressure: 5, security_need: 6 } },
      { label: '30%-50%', scores: { debt_pressure: 7, security_need: 8 } },
      { label: '50%以上', scores: { debt_pressure: 9, security_need: 9 } },
    ],
  },
  {
    id: 'q6_diversification',
    category: 'basic',
    question: '你倾向于如何配置投资？',
    options: [
      { label: '只买一种（如只存银行或只买股票）', scores: { diversification_preference: 1 } },
      { label: '2-3种（如银行理财+基金）', scores: { diversification_preference: 4 } },
      { label: '4-5种（股票+债券+基金+黄金等）', scores: { diversification_preference: 7 } },
      { label: '全球多元配置（跨市场跨资产）', scores: { diversification_preference: 9 } },
    ],
  },
  // ===== Step 2: 风险偏好 (6题) =====
  {
    id: 'q7_risk_tolerance',
    category: 'risk',
    question: '你能接受的最大单年亏损是多少？',
    options: [
      { label: '不能亏，保本第一', scores: { risk_tolerance: 1, loss_aversion: 9 } },
      { label: '5%以内', scores: { risk_tolerance: 3, loss_aversion: 7 } },
      { label: '10%-20%', scores: { risk_tolerance: 6, loss_aversion: 4 } },
      { label: '20%-30%', scores: { risk_tolerance: 8, loss_aversion: 2 } },
      { label: '30%以上，能扛住', scores: { risk_tolerance: 9, loss_aversion: 1 } },
    ],
  },
  {
    id: 'q8_stop_loss',
    category: 'risk',
    question: '买入前是否会设定止损点（如跌10%就卖）？',
    options: [
      { label: '从不设止损', scores: { stop_loss_discipline: 1, emotional_stability: 3 } },
      { label: '想过但没执行过', scores: { stop_loss_discipline: 3, emotional_stability: 4 } },
      { label: '偶尔执行', scores: { stop_loss_discipline: 6, emotional_stability: 6 } },
      { label: '严格执行，触达就卖', scores: { stop_loss_discipline: 9, emotional_stability: 8 } },
    ],
  },
  {
    id: 'q9_loss_scenario',
    category: 'risk',
    question: '持仓跌20%后，你的第一反应是？',
    options: [
      { label: '立刻全部清仓', scores: { loss_aversion: 9, emergency_response: 9, emotional_stability: 2 } },
      { label: '减仓一半', scores: { loss_aversion: 6, emergency_response: 6, emotional_stability: 4 } },
      { label: '不动，等反弹', scores: { loss_aversion: 4, emergency_response: 3, emotional_stability: 5 } },
      { label: '加仓摊低成本', scores: { loss_aversion: 2, emergency_response: 1, emotional_stability: 6 } },
      { label: '检查基本面，再决定', scores: { loss_aversion: 3, emergency_response: 2, information_processing: 7, emotional_stability: 8 } },
    ],
  },
  {
    id: 'q10_anchoring',
    category: 'risk',
    question: '10元买入跌到7元，涨回9元，你会？',
    options: [
      { label: '解套就卖，再也不碰', scores: { anchoring_effect: 9, loss_aversion: 8 } },
      { label: '等涨回10元再卖', scores: { anchoring_effect: 7, loss_aversion: 5 } },
      { label: '看趋势决定，不纠结成本', scores: { anchoring_effect: 2, loss_aversion: 2, information_processing: 6 } },
      { label: '该加仓，便宜了', scores: { anchoring_effect: 1, loss_aversion: 1, risk_tolerance: 8 } },
    ],
  },
  {
    id: 'q11_time_horizon',
    category: 'risk',
    question: '你能接受多久看不到明显收益？',
    options: [
      { label: '1个月', scores: { time_horizon_score: 2, delayed_gratification: 2 } },
      { label: '3个月', scores: { time_horizon_score: 4, delayed_gratification: 4 } },
      { label: '1年', scores: { time_horizon_score: 7, delayed_gratification: 6 } },
      { label: '3年以上', scores: { time_horizon_score: 9, delayed_gratification: 9 } },
    ],
  },
  {
    id: 'q12_security_need',
    category: 'risk',
    question: '急用3万时，你的投资账户能否立刻拿出？',
    options: [
      { label: '完全没问题，随时可取', scores: { security_need: 2, capital_tier: 8 } },
      { label: '要卖一部分投资', scores: { security_need: 5, capital_tier: 5 } },
      { label: '凑不齐，大部分都在投资里', scores: { security_need: 8, capital_tier: 3 } },
      { label: '没想过这问题', scores: { security_need: 6, capital_tier: 4 } },
    ],
  },
  // ===== Step 3: 行为特征 (6题) =====
  {
    id: 'q13_herding',
    category: 'behavior',
    question: '朋友说某股票涨了30%，你的反应是？',
    options: [
      { label: '马上跟买，怕错过', scores: { herding_tendency: 9, information_processing: 2, overconfidence: 5 } },
      { label: '先研究一下再决定', scores: { herding_tendency: 4, information_processing: 7, overconfidence: 4 } },
      { label: '不为所动，有自己的判断', scores: { herding_tendency: 2, information_processing: 8, overconfidence: 3 } },
      { label: '觉得涨多了该卖了，不会追高', scores: { herding_tendency: 5, information_processing: 6, overconfidence: 4 } },
    ],
  },
  {
    id: 'q14_overconfidence',
    category: 'behavior',
    question: '连续3个月盈利20%，你觉得主要原因是？',
    options: [
      { label: '我眼光好，有天赋', scores: { overconfidence: 9, information_processing: 2 } },
      { label: '我做了研究，方法对', scores: { overconfidence: 6, information_processing: 6 } },
      { label: '市场好，运气好', scores: { overconfidence: 2, information_processing: 7 } },
      { label: '样本太小，不能说明什么', scores: { overconfidence: 1, information_processing: 9 } },
    ],
  },
  {
    id: 'q15_info_processing',
    category: 'behavior',
    question: '看到一条投资相关新闻，你会？',
    options: [
      { label: '立刻据此操作', scores: { information_processing: 1, herding_tendency: 7, overconfidence: 6 } },
      { label: '查一下消息来源是否可靠', scores: { information_processing: 5, herding_tendency: 4, overconfidence: 4 } },
      { label: '结合多个来源交叉验证', scores: { information_processing: 8, herding_tendency: 2, overconfidence: 3 } },
      { label: '忽略，等市场消化后再看', scores: { information_processing: 7, herding_tendency: 2, overconfidence: 2 } },
    ],
  },
  {
    id: 'q16_delayed_gratification',
    category: 'behavior',
    question: '投资盈利10%后，你会？',
    options: [
      { label: '立刻卖出落袋为安', scores: { delayed_gratification: 2, anchoring_effect: 7 } },
      { label: '卖出一半，留一半', scores: { delayed_gratification: 4, anchoring_effect: 4 } },
      { label: '继续持有，等更高收益', scores: { delayed_gratification: 7, anchoring_effect: 2 } },
      { label: '用利润再投入', scores: { delayed_gratification: 9, anchoring_effect: 1 } },
    ],
  },
  {
    id: 'q17_social_pressure',
    category: 'behavior',
    question: '家人/朋友反对你的投资决策，你会？',
    options: [
      { label: '立刻停止，听他们的', scores: { social_pressure: 9, herding_tendency: 7 } },
      { label: '减少投入，缓和矛盾', scores: { social_pressure: 6, herding_tendency: 5 } },
      { label: '不受影响，按自己节奏', scores: { social_pressure: 2, herding_tendency: 2 } },
      { label: '用数据和收益说服他们', scores: { social_pressure: 3, herding_tendency: 2, information_processing: 5 } },
    ],
  },
  {
    id: 'q18_emotional_stability',
    category: 'behavior',
    question: '连续3天亏损，累计跌15%，你会？',
    options: [
      { label: '恐慌清仓，再也不投', scores: { emotional_stability: 1, emergency_response: 9, loss_aversion: 9 } },
      { label: '焦虑但不动，不知道怎么办', scores: { emotional_stability: 3, emergency_response: 5, loss_aversion: 6 } },
      { label: '暂停交易，冷静分析原因', scores: { emotional_stability: 7, emergency_response: 3, information_processing: 6 } },
      { label: '按计划执行，情绪不影响决策', scores: { emotional_stability: 9, emergency_response: 1, stop_loss_discipline: 8 } },
    ],
  },
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

// ── 演示生态系统概览（与 portfolio 的 9 个策略一致） ──
function buildEcosystem(): Record<string, any> {
  const allDNA = Object.values(DEMO_DNA_MAP)

  // 家族分布
  const familyCounts = new Map<string, number>()
  allDNA.forEach((d) => {
    const fam = d.family_name || '其他'
    familyCounts.set(fam, (familyCounts.get(fam) || 0) + 1)
  })
  const familyDistribution = Array.from(familyCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  // 健康度分布（使用与 EcosystemView.vue healthBucket 一致的 key）
  const healthDistribution: Record<string, number> = {}
  allDNA.forEach((d) => {
    const score = d.health_birth_score
    const bucket = score >= 80 ? '优秀(80+)' : score >= 60 ? '良好(60-80)' : '需关注(<60)'
    healthDistribution[bucket] = (healthDistribution[bucket] || 0) + 1
  })

  // 寿命分布（使用与 EcosystemView.vue lifespanBucket 一致的 key）
  const lifespanDistribution: Record<string, number> = {}
  allDNA.forEach((d) => {
    const m = d.lifespan_months
    const bucket = m >= 36 ? '年轻(36+)' : m >= 12 ? '成熟(12-36)' : m >= 3 ? '衰老(3-12)' : '濒危(<3)'
    lifespanDistribution[bucket] = (lifespanDistribution[bucket] || 0) + 1
  })

  const healthScores = allDNA.map((d) => d.health_birth_score)
  const lifespans = allDNA.map((d) => d.lifespan_months)
  const metabolicRates = allDNA.map((d) => d.metabolic_rate)
  const nicheWidths = allDNA.map((d) => d.niche_width)
  const diversityScores = allDNA.map((d) => d.gene_diversity_score)

  const avg = (nums: number[]) => (nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : 0)

  const lowHealth = allDNA
    .filter((d) => d.health_birth_score < 60)
    .map((d) => ({
      strategy_id: d.strategy_id,
      name: STRATEGY_NAMES[d.strategy_id],
      health_birth_score: d.health_birth_score,
      gene_diversity_score: d.gene_diversity_score,
      family_name: d.family_name,
    }))

  const shortLifespan = allDNA
    .filter((d) => d.lifespan_months < 12)
    .map((d) => ({
      strategy_id: d.strategy_id,
      name: STRATEGY_NAMES[d.strategy_id],
      lifespan_months: d.lifespan_months,
      lifespan_phase: d.lifespan_phase,
      aging_velocity: d.aging_velocity,
      family_name: d.family_name,
    }))

  const highMetabolic = allDNA
    .filter((d) => d.metabolic_rate > 0.5)
    .map((d) => ({
      strategy_id: d.strategy_id,
      name: STRATEGY_NAMES[d.strategy_id],
      metabolic_rate: d.metabolic_rate,
      niche_width: d.niche_width,
      metabolic_syndrome: d.metabolic_syndrome,
      family_name: d.family_name,
    }))

  const metabolicRank = allDNA
    .map((d) => ({
      strategy_id: d.strategy_id,
      name: STRATEGY_NAMES[d.strategy_id],
      metabolic_rate: d.metabolic_rate,
      niche_width: d.niche_width,
      family_name: d.family_name,
    }))
    .sort((a, b) => b.metabolic_rate - a.metabolic_rate)

  const recentStrategies = allDNA
    .slice(-3)
    .map((d) => ({
      strategy_id: d.strategy_id,
      name: STRATEGY_NAMES[d.strategy_id],
      health_birth_score: d.health_birth_score,
      gene_diversity_score: d.gene_diversity_score,
      family_name: d.family_name,
    }))

  // 雷达指标（与 EcosystemView.vue 中 indicatorNames 默认值一致）
  const radarIndicators = [
    { name: '健康度', max: 100 },
    { name: '多样性', max: 100 },
    { name: '代谢稳定性', max: 100 },
    { name: '生态位宽度', max: 100 },
    { name: '差异化', max: 100 },
  ]

  // 家族雷达：按家族聚合
  const familyGroups = new Map<string, typeof allDNA>()
  allDNA.forEach((d) => {
    const fam = d.family_name || '其他'
    if (!familyGroups.has(fam)) familyGroups.set(fam, [])
    familyGroups.get(fam)!.push(d)
  })

  const familyRadar = Array.from(familyGroups.entries()).map(([name, items]) => ({
    name,
    value: [
      avg(items.map((s) => s.health_birth_score)),
      avg(items.map((s) => s.gene_diversity_score * 100)),
      avg(items.map((s) => (1 - s.metabolic_rate) * 100)),
      avg(items.map((s) => s.niche_width * 100)),
      avg(items.map((s) => (1 - s.inbreeding_coefficient) * 100)),
    ],
  }))

  // 关系网络：9 个节点 + 两两相似度连线
  const nodes = allDNA.map((d) => ({
    id: d.strategy_id,
    name: STRATEGY_NAMES[d.strategy_id],
    family: d.family_name || '其他',
    family_id: d.family_id || 'family_other',
    health: d.health_birth_score,
    lifespan: d.lifespan_months,
    metabolic_rate: d.metabolic_rate,
    value: 1,
    symbolSize: 20,
  }))

  const links: { source: string; target: string; value: number }[] = []
  // 资产类别亲缘关系：同大类资产策略关联度更高
  const assetClassAffinity: Record<string, Record<string, number>> = {
    ETF: { ETF: 0.35, stock: 0.20, bond: 0.05, cash: 0.02, commodity: 0.10 },
    stock: { ETF: 0.20, stock: 0.30, bond: 0.02, cash: 0.02, commodity: 0.08 },
    bond: { ETF: 0.05, stock: 0.02, bond: 0.40, cash: 0.25, commodity: 0.03 },
    cash: { ETF: 0.02, stock: 0.02, bond: 0.25, cash: 0.30, commodity: 0.02 },
    commodity: { ETF: 0.10, stock: 0.08, bond: 0.03, cash: 0.02, commodity: 0.35 },
  }
  const portfolioBindings = DEMO_PORTFOLIO.bindings as Array<{ strategy_id: string; asset_class: string }>
  const strategyAssetClass: Record<string, string> = {}
  portfolioBindings.forEach((b) => { strategyAssetClass[b.strategy_id] = b.asset_class })

  for (let i = 0; i < allDNA.length; i++) {
    for (let j = i + 1; j < allDNA.length; j++) {
      const a = allDNA[i]
      const b = allDNA[j]
      const classA = strategyAssetClass[a.strategy_id] || 'other'
      const classB = strategyAssetClass[b.strategy_id] || 'other'
      const assetAffinity = (assetClassAffinity[classA] && assetClassAffinity[classA][classB]) || 0.05
      const sameFamily = a.family_id === b.family_id ? 0.25 : 0.0
      const geneOverlap = a.feature_genes.filter((g: string) => b.feature_genes.includes(g)).length / Math.max(a.feature_genes.length, b.feature_genes.length)
      const similarity = Math.min(0.92, sameFamily + assetAffinity + geneOverlap * 0.25 + 0.08)
      if (similarity > 0.18) {
        links.push({ source: a.strategy_id, target: b.strategy_id, value: Math.round(similarity * 100) / 100 })
      }
    }
  }

  return {
    total_strategies: allDNA.length,
    family_count: familyCounts.size,
    avg_health_score: avg(healthScores),
    min_health_score: Math.min(...healthScores),
    max_health_score: Math.max(...healthScores),
    avg_diversity: avg(diversityScores),
    inbreeding_risk_count: allDNA.filter((d) => d.inbreeding_coefficient > 0.3).length,
    family_distribution: familyDistribution,
    health_distribution: healthDistribution,
    low_health_strategies: lowHealth,
    recent_strategies: recentStrategies,
    avg_metabolic_rate: avg(metabolicRates),
    avg_niche_width: avg(nicheWidths),
    syndrome_count: highMetabolic.filter((s) => s.metabolic_syndrome).length,
    high_metabolic_strategies: highMetabolic,
    avg_lifespan: avg(lifespans),
    endangered_count: lifespans.filter((m) => m < 3).length,
    short_lifespan_strategies: shortLifespan,
    metabolic_ranking: metabolicRank,
    family_radar: familyRadar,
    radar_indicators: radarIndicators,
    family_network: { nodes, links },
  }
}

export const DEMO_ECOSYSTEM = buildEcosystem()

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

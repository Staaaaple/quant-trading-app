import { delay } from './mock/utils'
import { DEMO_DNA, DEMO_ECOSYSTEM } from './mock/demoData'

export interface StrategyDNA {
  strategy_id: string
  feature_genes: string[]
  signal_genes: string[]
  risk_genes: string[]
  execution_genes: string[]
  gene_diversity_score: number
  health_birth_score: number
  inbreeding_coefficient: number
  family_id: string | null
  family_name: string | null
  sequence_version: string
  sequenced_at: string
  status: string
  error_message: string | null
  metabolic_rate: number
  niche_width: number
  metabolic_syndrome: boolean
  metabolic_markers: string[]
  lifespan_months: number
  lifespan_phase: string
  lifespan_phase_label: string
  aging_velocity: number
  lifespan_recommendations: string[]
}

export interface StrategyDNASummary {
  strategy_id: string
  name: string
  gene_diversity_score: number
  health_birth_score: number
  feature_genes: string[]
  signal_genes: string[]
  status: string
  family_id: string | null
  family_name: string | null

  // Integration fields for eco-pre-check (方案一)
  metabolic_rate: number
  niche_width: number
  inbreeding_warning: boolean
  homogeneity_risk: number
  lifespan_months: number
}

export interface GeneMatch {
  strategy_id: string
  name: string
  similarity: number
}

export interface StrategyPhylogeny {
  strategy_id: string
  family_id: string | null
  family_name: string | null
  relatives: GeneMatch[]
  homogeneity_risk: number
  inbreeding_warning: boolean
}

export interface FamilyInfo {
  family_id: string
  family_name: string
  count: number
}

export interface DNAPreview {
  strategy_id: string
  feature_genes: string[]
  signal_genes: string[]
  risk_genes: string[]
  execution_genes: string[]
  gene_diversity_score: number
  health_birth_score: number
  gene_vector: number[]
  metabolic_rate: number
  niche_width: number
  metabolic_syndrome: boolean
  metabolic_markers: string[]
  ast_features: Record<string, any>
}

export interface EcosystemOverview {
  total_strategies: number
  family_count: number
  avg_health_score: number
  min_health_score: number
  max_health_score: number
  avg_diversity: number
  inbreeding_risk_count: number
  family_distribution: { name: string; count: number }[]
  health_distribution: Record<string, number>
  low_health_strategies: {
    strategy_id: string
    name: string
    health_birth_score: number
    gene_diversity_score: number
    family_name: string | null
  }[]
  recent_strategies: {
    strategy_id: string
    name: string
    health_birth_score: number
    gene_diversity_score: number
    family_name: string | null
  }[]
  avg_metabolic_rate: number
  avg_niche_width: number
  syndrome_count: number
  high_metabolic_strategies: {
    strategy_id: string
    name: string
    metabolic_rate: number
    niche_width: number
    metabolic_syndrome: boolean
    family_name: string | null
  }[]
  avg_lifespan: number
  lifespan_distribution: Record<string, number>
  endangered_count: number
  short_lifespan_strategies: {
    strategy_id: string
    name: string
    lifespan_months: number
    lifespan_phase: string
    aging_velocity: number
    family_name: string | null
  }[]
  metabolic_ranking: {
    strategy_id: string
    name: string
    metabolic_rate: number
    niche_width: number
    family_name: string | null
  }[]
  family_radar: {
    name: string
    value: number[]
  }[]
  radar_indicators: { name: string; max: number }[]
  family_network: {
    nodes: {
      id: string
      name: string
      family: string
      family_id: string
      health: number
      lifespan: number
      metabolic_rate: number
      value: number
      symbolSize: number
    }[]
    links: { source: string; target: string; value: number }[]
  }
}

export const dnaApi = {
  getDNA(_strategy_id: string): Promise<StrategyDNA> {
    return delay(300).then(() => DEMO_DNA as StrategyDNA)
  },
  getSummary(_strategy_id: string): Promise<StrategyDNASummary> {
    return delay(300).then(() => ({
      strategy_id: 'demo_s1',
      name: '科技ETF趋势策略',
      gene_diversity_score: 0.78,
      health_birth_score: 0.82,
      feature_genes: ['ma20', 'volume_ratio', 'atr'],
      signal_genes: ['crossover', 'momentum_break'],
      status: 'active',
      family_id: 'family_trend',
      family_name: '趋势家族',
      metabolic_rate: 0.65,
      niche_width: 0.70,
      inbreeding_warning: false,
      homogeneity_risk: 0.15,
      lifespan_months: 24,
    }))
  },
  sequence(_strategy_id: string): Promise<StrategyDNA> {
    return delay(500).then(() => DEMO_DNA as StrategyDNA)
  },
  preview(_strategy_id: string, _code: string): Promise<DNAPreview> {
    return delay(600).then(() => ({
      strategy_id: 'demo_s1',
      feature_genes: ['ma20', 'volume_ratio', 'atr'],
      signal_genes: ['crossover', 'momentum_break'],
      risk_genes: ['max_drawdown_guard', 'position_limit'],
      execution_genes: ['twap', 'slippage_control'],
      gene_diversity_score: 0.78,
      health_birth_score: 0.82,
      gene_vector: [0.1, 0.2, 0.3, 0.4],
      metabolic_rate: 0.65,
      niche_width: 0.70,
      metabolic_syndrome: false,
      metabolic_markers: ['stable'],
      ast_features: {},
    }))
  },
  listAll(): Promise<StrategyDNASummary[]> {
    return delay(300).then(() => [
      {
        strategy_id: 'demo_s1',
        name: '科技ETF趋势策略',
        gene_diversity_score: 0.78,
        health_birth_score: 0.82,
        feature_genes: ['ma20', 'volume_ratio', 'atr'],
        signal_genes: ['crossover', 'momentum_break'],
        status: 'active',
        family_id: 'family_trend',
        family_name: '趋势家族',
        metabolic_rate: 0.65,
        niche_width: 0.70,
        inbreeding_warning: false,
        homogeneity_risk: 0.15,
        lifespan_months: 24,
      },
    ])
  },
  getPhylogeny(_strategy_id: string): Promise<StrategyPhylogeny> {
    return delay(300).then(() => ({
      strategy_id: 'demo_s1',
      family_id: 'family_trend',
      family_name: '趋势家族',
      relatives: [
        { strategy_id: 'demo_s2', name: '消费ETF均值回归', similarity: 0.45 },
      ],
      homogeneity_risk: 0.15,
      inbreeding_warning: false,
    }))
  },
  computePhylogeny(): Promise<{ status: string; message: string }> {
    return delay(500).then(() => ({ status: 'ok', message: '系统发育计算完成' }))
  },
  listFamilies(): Promise<FamilyInfo[]> {
    return delay(300).then(() => [
      { family_id: 'family_trend', family_name: '趋势家族', count: 3 },
      { family_id: 'family_mr', family_name: '均值回归家族', count: 2 },
      { family_id: 'family_def', family_name: '防御家族', count: 2 },
    ])
  },
  getEcosystem(): Promise<EcosystemOverview> {
    return delay(400).then(() => DEMO_ECOSYSTEM as EcosystemOverview)
  },
  getLifespan(_strategy_id: string): Promise<{
    strategy_id: string
    lifespan_months: number
    lifespan_phase: string
    lifespan_phase_label: string
    aging_velocity: number
    lifespan_recommendations: string[]
  }> {
    return delay(300).then(() => ({
      strategy_id: 'demo_s1',
      lifespan_months: 24,
      lifespan_phase: 'mature',
      lifespan_phase_label: '成熟期',
      aging_velocity: 0.12,
      lifespan_recommendations: ['定期再训练', '监控过拟合'],
    }))
  },
  computeLifespans(): Promise<{ status: string; message: string }> {
    return delay(500).then(() => ({ status: 'ok', message: '寿命计算完成' }))
  },
}

import { delay } from './mock/utils'
import { DEMO_DNA, DEMO_DNA_MAP, DEMO_ECOSYSTEM } from './mock/demoData'

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
  getDNA(strategy_id: string): Promise<StrategyDNA> {
    const dna = DEMO_DNA_MAP[strategy_id] || DEMO_DNA
    return delay(300).then(() => dna as StrategyDNA)
  },
  getSummary(strategy_id: string): Promise<StrategyDNASummary> {
    const dna = DEMO_DNA_MAP[strategy_id] || DEMO_DNA
    return delay(300).then(() => ({
      strategy_id: dna.strategy_id,
      name: (() => {
        const names: Record<string, string> = {
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
        return names[dna.strategy_id] || dna.strategy_id
      })(),
      gene_diversity_score: dna.gene_diversity_score,
      health_birth_score: dna.health_birth_score,
      feature_genes: dna.feature_genes,
      signal_genes: dna.signal_genes,
      status: dna.status,
      family_id: dna.family_id,
      family_name: dna.family_name,
      metabolic_rate: dna.metabolic_rate,
      niche_width: dna.niche_width,
      inbreeding_warning: dna.inbreeding_coefficient > 0.3,
      homogeneity_risk: dna.inbreeding_coefficient,
      lifespan_months: dna.lifespan_months,
    }))
  },
  sequence(strategy_id: string): Promise<StrategyDNA> {
    const dna = DEMO_DNA_MAP[strategy_id] || DEMO_DNA
    return delay(500).then(() => dna as StrategyDNA)
  },
  preview(_strategy_id: string, _code: string): Promise<DNAPreview> {
    return delay(600).then(() => ({
      strategy_id: 'demo_s1',
      feature_genes: ['ma20', 'volume_ratio', 'atr'],
      signal_genes: ['crossover', 'momentum_break'],
      risk_genes: ['max_drawdown_guard', 'position_limit'],
      execution_genes: ['twap', 'slippage_control'],
      gene_diversity_score: 0.78,
      health_birth_score: 82,
      gene_vector: [0.1, 0.2, 0.3, 0.4],
      metabolic_rate: 0.65,
      niche_width: 0.70,
      metabolic_syndrome: false,
      metabolic_markers: ['stable'],
      ast_features: {},
    }))
  },
  listAll(): Promise<StrategyDNASummary[]> {
    const all = Object.values(DEMO_DNA_MAP)
    const names: Record<string, string> = {
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
    return delay(300).then(() =>
      all.map((dna) => ({
        strategy_id: dna.strategy_id,
        name: names[dna.strategy_id] || dna.strategy_id,
        gene_diversity_score: dna.gene_diversity_score,
        health_birth_score: dna.health_birth_score,
        feature_genes: dna.feature_genes,
        signal_genes: dna.signal_genes,
        status: dna.status,
        family_id: dna.family_id,
        family_name: dna.family_name,
        metabolic_rate: dna.metabolic_rate,
        niche_width: dna.niche_width,
        inbreeding_warning: dna.inbreeding_coefficient > 0.3,
        homogeneity_risk: dna.inbreeding_coefficient,
        lifespan_months: dna.lifespan_months,
      }))
    )
  },
  getPhylogeny(strategy_id: string): Promise<StrategyPhylogeny> {
    const dna = DEMO_DNA_MAP[strategy_id] || DEMO_DNA
    const all = Object.values(DEMO_DNA_MAP)
    // 找同家族的其他策略作为 relatives
    const relatives = all
      .filter((d) => d.family_id === dna.family_id && d.strategy_id !== dna.strategy_id)
      .map((d) => ({
        strategy_id: d.strategy_id,
        name: (() => {
          const names: Record<string, string> = {
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
          return names[d.strategy_id] || d.strategy_id
        })(),
        similarity: 0.45,
      }))
    return delay(300).then(() => ({
      strategy_id: dna.strategy_id,
      family_id: dna.family_id,
      family_name: dna.family_name,
      relatives,
      homogeneity_risk: dna.inbreeding_coefficient,
      inbreeding_warning: dna.inbreeding_coefficient > 0.3,
    }))
  },
  computePhylogeny(): Promise<{ status: string; message: string }> {
    return delay(500).then(() => ({ status: 'ok', message: '系统发育计算完成' }))
  },
  listFamilies(): Promise<FamilyInfo[]> {
    return delay(300).then(() => [
      { family_id: 'family_trend', family_name: '趋势家族', count: 1 },
      { family_id: 'family_mr', family_name: '均值回归家族', count: 1 },
      { family_id: 'family_value', family_name: '价值家族', count: 1 },
      { family_id: 'family_cycle', family_name: '周期家族', count: 1 },
      { family_id: 'family_def', family_name: '防御家族', count: 1 },
      { family_id: 'family_fixed', family_name: '固定收益家族', count: 1 },
      { family_id: 'family_cash', family_name: '现金家族', count: 1 },
      { family_id: 'family_commodity', family_name: '商品家族', count: 1 },
      { family_id: 'family_growth', family_name: '成长家族', count: 1 },
    ])
  },
  getEcosystem(): Promise<EcosystemOverview> {
    return delay(400).then(() => DEMO_ECOSYSTEM as EcosystemOverview)
  },
  getLifespan(strategy_id: string): Promise<{
    strategy_id: string
    lifespan_months: number
    lifespan_phase: string
    lifespan_phase_label: string
    aging_velocity: number
    lifespan_recommendations: string[]
  }> {
    const dna = DEMO_DNA_MAP[strategy_id] || DEMO_DNA
    return delay(300).then(() => ({
      strategy_id: dna.strategy_id,
      lifespan_months: dna.lifespan_months,
      lifespan_phase: dna.lifespan_phase,
      lifespan_phase_label: dna.lifespan_phase_label,
      aging_velocity: dna.aging_velocity,
      lifespan_recommendations: dna.lifespan_recommendations,
    }))
  },
  computeLifespans(): Promise<{ status: string; message: string }> {
    return delay(500).then(() => ({ status: 'ok', message: '寿命计算完成' }))
  },
}

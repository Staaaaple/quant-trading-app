import { request } from './client'

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
    return request(`/strategies/${strategy_id}/dna`)
  },
  getSummary(strategy_id: string): Promise<StrategyDNASummary> {
    return request(`/strategies/${strategy_id}/dna/summary`)
  },
  sequence(strategy_id: string): Promise<StrategyDNA> {
    return request(`/strategies/${strategy_id}/dna/sequence`, {
      method: 'POST',
    })
  },
  preview(strategy_id: string, code: string): Promise<DNAPreview> {
    return request(`/dna/preview`, {
      method: 'POST',
      body: JSON.stringify({ strategy_id, code }),
    })
  },
  listAll(): Promise<StrategyDNASummary[]> {
    return request(`/dna/list`)
  },
  getPhylogeny(strategy_id: string): Promise<StrategyPhylogeny> {
    return request(`/strategies/${strategy_id}/phylogeny`)
  },
  computePhylogeny(): Promise<{ status: string; message: string }> {
    return request(`/dna/phylogeny/compute`, { method: 'POST' })
  },
  listFamilies(): Promise<FamilyInfo[]> {
    return request(`/dna/families`)
  },
  getEcosystem(): Promise<EcosystemOverview> {
    return request(`/dna/ecosystem`)
  },
  getLifespan(strategy_id: string): Promise<{
    strategy_id: string
    lifespan_months: number
    lifespan_phase: string
    lifespan_phase_label: string
    aging_velocity: number
    lifespan_recommendations: string[]
  }> {
    return request(`/strategies/${strategy_id}/lifespan`)
  },
  computeLifespans(): Promise<{ status: string; message: string }> {
    return request(`/dna/lifespan/compute`, { method: 'POST' })
  },
}

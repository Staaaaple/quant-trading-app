import { delay } from './mock/utils'
import { DEMO_MARKET_SIGNAL } from './mock/demoData'

export interface MacroLayer {
  cycle_phase: string | null
  gdp_trend: string | null
  inflation_level: string | null
  liquidity: string | null
  interest_rate: string | null
  score: number | null
  cycle_analysis?: CycleAnalysis | null
}

export interface CycleAnalysis {
  final_phase: string
  final_description: string
  final_asset_preference: string
  confidence: number
  fused_coordinates: Record<string, number>
  model_results: CycleModelResult[]
  consistency: number
  data_completeness: number
}

export interface CycleModelResult {
  model: string
  phase: string
  description: string
  asset_preference: string
  score: number
  inputs: Record<string, number | null>
}

export interface GeoLayer {
  overall_risk: number | null
  risk_level: string | null
  safe_haven_demand: string | null
  score: number | null
}

export interface IndustryLayer {
  heatmap: Record<string, number> | null
  recommended: string[] | null
  avoid: string[] | null
  score: number | null
}

export interface SocialLayer {
  major_themes: string[] | null
  theme_strength: Record<string, number> | null
  consumer_confidence: string | null
  score: number | null
}

export interface InternalLayer {
  equity_bond_spread: number | null
  sentiment: string | null
  style_rotation: string | null
  volatility_regime: string | null
  score: number | null
}

export interface MarketSignalLatest {
  date: string
  composite_score: number
  market_mood: string
  market_cycle: string
  cycle_analysis?: CycleAnalysis | null
  macro: MacroLayer
  geo: GeoLayer
  industry: IndustryLayer
  social: SocialLayer
  internal: InternalLayer
}

export const marketSignalApi = {
  getLatest: () => delay(400).then(() => DEMO_MARKET_SIGNAL as MarketSignalLatest),
  collect: () => delay(500).then(() => ({ success: true })),
}

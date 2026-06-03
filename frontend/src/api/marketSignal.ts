import client from './client'

export interface MacroLayer {
  cycle_phase: string | null
  gdp_trend: string | null
  inflation_level: string | null
  liquidity: string | null
  interest_rate: string | null
  score: number | null
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
  macro: MacroLayer
  geo: GeoLayer
  industry: IndustryLayer
  social: SocialLayer
  internal: InternalLayer
}

export const marketSignalApi = {
  getLatest: () => client.get<MarketSignalLatest>('/market-signals/latest').then(r => r.data),
  collect: () => client.post<unknown>('/market-signals/collect').then(r => r.data),
}

import client from './client'

export interface PortfolioDesignPayload {
  profile_vector: Record<string, number>
  market_signal: Record<string, any>
  strategy_pool?: any[]
  use_rag_gate?: boolean
  rag_strictness?: string
}

export interface PortfolioDesignResult {
  success: boolean
  portfolio: {
    portfolio_id: string
    saa: {
      weights: Record<string, number>
      rationale: string
      risk_profile: Record<string, any>
    }
    taa: Record<string, any>
    bindings: Array<{
      sector: string
      sector_name: string
      weight: number
      strategy_id: string
      strategy_name: string
      strategy_family: string
      symbol?: string
      symbol_name?: string
      health_score?: number
      lifespan_months?: number
    }>
    risk_config: {
      stop_loss: number
      max_position: number
      max_drawdown: number
      rebalance_threshold: number
      rationale: string
    }
    reliability: {
      confidence: number
      reliability_level: string
      backtest_available: boolean
      stress_test_available: boolean
      monte_carlo_available: boolean
    }
    portfolio_lifespan: number
    portfolio_health: number
    status: string
  }
  validation: {
    valid: boolean
    issues: string[]
    warnings: string[]
  }
  summary: {
    total_strategies: number
    stock_ratio: string
    top_sector: string
    risk_level: string
    expected_lifespan: string
    health_score: number
  }
  // RAG specific fields
  rag_reviews?: Array<{
    step: string
    passed: boolean
    issues: string[]
    suggestions: string[]
  }>
  rag_adjusted?: boolean
  rag_adjustment_count?: number
}

/**
 * Portfolio API - 仅使用RAG版本
 *
 * 所有组合设计都通过 /portfolios/design-with-rag 端点，
 * 启用RAG质量门控确保组合质量。
 */
export const portfolioApi = {
  /**
   * 设计投资组合（带RAG质检）
   *
   * 这是唯一的设计入口，自动启用RAG质量门控。
   * 非RAG版本已被移除，确保所有组合都经过质检。
   */
  design: (payload: PortfolioDesignPayload) =>
    client.post<PortfolioDesignResult>('/portfolios/design-with-rag', {
      ...payload,
      use_rag_gate: true,  // 强制启用RAG
      rag_strictness: 'normal',
    }).then(r => r.data),
}

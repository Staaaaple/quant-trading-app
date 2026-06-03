import client from './client'

export interface PortfolioDesignPayload {
  profile_vector: Record<string, number>
  market_signal: Record<string, any>
  strategy_pool?: any[]
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
}

export const portfolioApi = {
  design: (payload: PortfolioDesignPayload) =>
    client.post<PortfolioDesignResult>('/portfolios/design', payload).then(r => r.data),
}

import { delay } from './mock/utils'
import {
  DEMO_PORTFOLIO_DESIGN_RESULT,
  DEMO_PORTFOLIO_TASK,
  DEMO_MARKET_SIGNAL,
} from './mock/demoData'

export interface PortfolioDesignPayload {
  profile_vector: Record<string, number>
  market_signal: Record<string, any>
  strategy_pool?: any[]
  use_rag_gate?: boolean
  use_dynamic_picker?: boolean
  rag_strictness?: string
}

export interface BenchmarkMetric {
  name: string
  description: string
  benchmark_return: number
  strategy_return: number
  excess_return: number
  benchmark_drawdown: number
  strategy_drawdown: number
  passed: boolean
  score: number
}

export interface BenchmarkComparison {
  custom_benchmark: BenchmarkMetric
  csi300: BenchmarkMetric
  equal_weight: BenchmarkMetric
  sixty_forty: BenchmarkMetric
  overall_score: number
  strategy_return: number
  strategy_drawdown: number
}

export interface AdoptionStatus {
  adopted: boolean
  threshold: number
  confidence: number
  reason: string
}

export interface PortfolioDesignResult {
  success: boolean
  adopted?: boolean
  portfolio: {
    portfolio_id: string
    adopted?: boolean
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
      backtest_warnings?: string[]
      data_source?: string
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
      benchmark_comparison?: BenchmarkComparison
      adoption_status?: AdoptionStatus
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

export interface PortfolioTask {
  task_id: number
  user_id?: number
  status: 'pending' | 'running' | 'completed' | 'failed' | null
  current_step?: string
  progress?: number
  result?: PortfolioDesignResult
  error_message?: string
  created_at?: string
  updated_at?: string
  completed_at?: string
}

export interface PortfolioProgressEvent {
  type: 'task' | 'progress' | 'result' | 'error'
  task_id?: number
  step?: string
  message?: string
  progress?: number
  adopted?: boolean
  portfolio?: any
  success?: boolean
  validation?: any
  summary?: any
  rag_reviews?: any[]
  rag_adjusted?: boolean
  rag_adjustment_count?: number
  message_error?: string
}

/**
 * Portfolio API - Mock version
 */
export const portfolioApi = {
  design: (payload: PortfolioDesignPayload) =>
    delay(800).then(() => {
      const result = { ...DEMO_PORTFOLIO_DESIGN_RESULT } as PortfolioDesignResult
      // Merge any provided payload data
      if (payload.market_signal) {
        result.portfolio = {
          ...result.portfolio,
          ...DEMO_PORTFOLIO_DESIGN_RESULT.portfolio,
        }
      }
      return result
    }),

  designAsync: (payload: PortfolioDesignPayload) =>
    delay(500).then(() => {
      const task = { ...DEMO_PORTFOLIO_TASK } as PortfolioTask
      if (payload.market_signal) {
        task.result = { ...DEMO_PORTFOLIO_DESIGN_RESULT } as PortfolioDesignResult
      }
      return task
    }),

  getTaskStatus: (_taskId: number) =>
    delay(300).then(() => ({ ...DEMO_PORTFOLIO_TASK } as PortfolioTask)),

  getMyLatestTask: () =>
    delay(300).then(() => ({ ...DEMO_PORTFOLIO_TASK } as PortfolioTask)),

  designStream: (payload: PortfolioDesignPayload) => {
    // Return a mock Response-like object that the caller can read
    const encoder = new TextEncoder()
    const events: PortfolioProgressEvent[] = [
      { type: 'task', task_id: 1, step: 'started' },
      { type: 'progress', task_id: 1, step: 'SAA配置', progress: 25, message: '正在计算战略资产配置...' },
      { type: 'progress', task_id: 1, step: 'TAA配置', progress: 50, message: '正在计算战术资产配置...' },
      { type: 'progress', task_id: 1, step: '策略绑定', progress: 75, message: '正在绑定策略...' },
      { type: 'result', task_id: 1, ...DEMO_PORTFOLIO_DESIGN_RESULT },
    ]

    const stream = new ReadableStream({
      start(controller) {
        let i = 0
        function push() {
          if (i >= events.length) {
            controller.close()
            return
          }
          const event = events[i++]
          const data = `data: ${JSON.stringify(event)}\n\n`
          controller.enqueue(encoder.encode(data))
          setTimeout(push, 300)
        }
        setTimeout(push, 100)
      },
    })

    return Promise.resolve(new Response(stream, {
      headers: { 'content-type': 'text/event-stream' },
    }))
  },
}

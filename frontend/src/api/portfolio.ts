import client from './client'

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

  /**
   * 提交异步组合设计任务.
   *
   * 立即返回 task_id，后端在后台持续运行。
   * 同一用户已有 running 任务时返回已有 task_id。
   */
  designAsync: (payload: PortfolioDesignPayload) =>
    client.post<PortfolioTask>('/portfolios/design-async', {
      ...payload,
      use_rag_gate: true,
      rag_strictness: 'normal',
    }).then(r => r.data),

  /**
   * 查询指定任务状态.
   */
  getTaskStatus: (taskId: number) =>
    client.get<PortfolioTask>(`/portfolios/tasks/${taskId}`).then(r => r.data),

  /**
   * 获取当前用户最新的组合设计任务.
   */
  getMyLatestTask: () =>
    client.get<PortfolioTask>('/portfolios/tasks/me').then(r => r.data),

  /**
   * 设计投资组合（SSE 流式进度版）
   *
   * 返回 fetch Response，调用方需手动读取 SSE 流。
   * 第一个事件可能是 {type: 'task', task_id: ...}。
   */
  designStream: (payload: PortfolioDesignPayload) => {
    const url = new URL('/api/v1/portfolios/design-with-rag/stream', window.location.origin)
    // 通过 POST body 发送参数需要改用 fetch ReadableStream，
    // 但 SSE 原生只支持 GET/POST。这里用 POST + fetch 手动读取 SSE。
    const userId = localStorage.getItem('active_user_id')
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (userId) {
      headers['X-User-Id'] = userId
    }
    return fetch(url.toString(), {
      method: 'POST',
      headers,
      body: JSON.stringify({ ...payload, use_rag_gate: true }),
    })
  },
}

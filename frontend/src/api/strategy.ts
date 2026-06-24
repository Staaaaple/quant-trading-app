import { delay } from './mock/utils'
import { DEMO_STRATEGIES, DEMO_DNA, DEMO_ECOSYSTEM } from './mock/demoData'

export interface Strategy {
  id: number
  strategy_id: string
  name: string
  type: string
  code: string
  pipeline_config: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface StrategyCreatePayload {
  strategy_id: string
  name: string
  code?: string
  type?: string
  pipeline_config?: Record<string, any>
}

export interface CodePreviewResponse {
  code: string
}

export interface NlParseResponse {
  pipeline_config: Record<string, any> | null
  confidence: number
  warnings: string[]
  complex_keywords_found: string[]
  matched_spans: [number, number, string][]
  unmatched_spans: [number, number][]
}

export const strategyApi = {
  list(_query?: string): Promise<Strategy[]> {
    return delay(300).then(() => DEMO_STRATEGIES as Strategy[])
  },
  get(_strategy_id: string): Promise<Strategy> {
    return delay(300).then(() => DEMO_STRATEGIES[0] as Strategy)
  },
  create(payload: StrategyCreatePayload): Promise<Strategy> {
    return delay(500).then(() => ({ ...DEMO_STRATEGIES[0], ...payload } as Strategy))
  },
  update(strategy_id: string, payload: Partial<StrategyCreatePayload>): Promise<Strategy> {
    return delay(400).then(() => {
      const existing = DEMO_STRATEGIES.find((s: any) => s.strategy_id === strategy_id) || DEMO_STRATEGIES[0]
      return { ...existing, ...payload } as Strategy
    })
  },
  remove(_strategy_id: string): Promise<void> {
    return delay(300).then(() => undefined)
  },
  previewCode(_pipelineConfig: Record<string, any>): Promise<CodePreviewResponse> {
    return delay(600).then(() => ({ code: 'def handle_bar(context, bar):\n    pass\n' }))
  },
  parseNl(_text: string): Promise<NlParseResponse> {
    return delay(600).then(() => ({
      pipeline_config: { indicators: ['ma20', 'rsi'] },
      confidence: 0.85,
      warnings: [],
      complex_keywords_found: [],
      matched_spans: [],
      unmatched_spans: [],
    }))
  },
}

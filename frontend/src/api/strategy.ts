import { request } from './client'

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
  list(query?: string): Promise<Strategy[]> {
    return request(`/strategies${query || ''}`)
  },
  get(strategy_id: string): Promise<Strategy> {
    return request(`/strategies/${strategy_id}`)
  },
  create(payload: StrategyCreatePayload): Promise<Strategy> {
    return request('/strategies', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  update(strategy_id: string, payload: Partial<StrategyCreatePayload>): Promise<Strategy> {
    return request(`/strategies/${strategy_id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
  remove(strategy_id: string): Promise<void> {
    return request(`/strategies/${strategy_id}`, {
      method: 'DELETE',
    })
  },
  previewCode(pipelineConfig: Record<string, any>): Promise<CodePreviewResponse> {
    return request('/strategies/preview-code', {
      method: 'POST',
      body: JSON.stringify({ pipeline_config: pipelineConfig }),
    })
  },
  parseNl(text: string): Promise<NlParseResponse> {
    return request('/strategies/parse-nl', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },
}

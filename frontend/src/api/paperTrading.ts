import { request } from './client'

export interface PaperTradingSession {
  id: number
  session_id: string
  strategy_id: string
  symbols: string[]
  initial_cash: number
  start_date: string | null
  end_date: string | null
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'success' | 'error'
  stop_reason: string | null
  logs: string | null
  created_at: string
  updated_at: string
}

export interface PaperTradingSessionCreatePayload {
  session_id: string
  strategy_id: string
  symbols: string[]
  initial_cash: number
  start_date?: string
  end_date?: string
}

export const paperTradingApi = {
  list(): Promise<PaperTradingSession[]> {
    return request('/paper-trading/sessions')
  },
  get(session_id: string): Promise<PaperTradingSession> {
    return request(`/paper-trading/sessions/${session_id}`)
  },
  create(payload: PaperTradingSessionCreatePayload): Promise<PaperTradingSession> {
    return request('/paper-trading/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  remove(session_id: string): Promise<void> {
    return request(`/paper-trading/sessions/${session_id}`, {
      method: 'DELETE',
    })
  },
  run(session_id: string): Promise<PaperTradingSession> {
    return request(`/paper-trading/sessions/${session_id}/run`, {
      method: 'POST',
    })
  },
  stop(session_id: string, stop_reason?: string): Promise<PaperTradingSession> {
    return request(`/paper-trading/sessions/${session_id}/stop`, {
      method: 'POST',
      body: stop_reason ? JSON.stringify({ stop_reason }) : undefined,
    })
  },
}

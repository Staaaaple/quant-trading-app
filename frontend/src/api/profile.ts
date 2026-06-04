import client from './client'

export interface Question {
  id: string
  category: string
  question: string
  options: {
    label: string
    scores: Record<string, number>
  }[]
}

export interface ProfileVector {
  risk_tolerance: number
  loss_aversion: number
  herding_tendency: number
  overconfidence: number
  delayed_gratification: number
  security_need: number
  time_horizon_score: number
  experience_level: number
  capital_tier: number
  income_stability: number
  debt_pressure: number
  information_processing: number
  social_pressure: number
  emergency_response: number
  anchoring_effect: number
  // NEW v2
  diversification_preference: number
  stop_loss_discipline: number
  emotional_stability: number
}

export interface ProfileLabels {
  risk_label: string
  time_horizon_label: string
  experience_label: string
}

export interface InvestorProfile {
  id: number
  user_id: number
  answers_json: Record<string, string | string[]>
  risk_tolerance: number
  loss_aversion: number
  herding_tendency: number
  overconfidence: number
  delayed_gratification: number
  security_need: number
  time_horizon_score: number
  experience_level: number
  capital_tier: number
  income_stability: number
  debt_pressure: number
  information_processing: number
  social_pressure: number
  emergency_response: number
  anchoring_effect: number
  // NEW v2
  diversification_preference: number
  stop_loss_discipline: number
  emotional_stability: number
  risk_label: string | null
  time_horizon_label: string | null
  experience_label: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export const profileApi = {
  getQuestions: () => client.get<Question[]>('/profiles/questions').then(r => r.data),
  preview: (answers: Record<string, string | string[]>) => client.post<{ vector: ProfileVector; labels: ProfileLabels }>('/profiles/preview', answers).then(r => r.data),
  /** 创建画像（user_id 从 header 自动获取） */
  create: (answers: Record<string, string | string[]>) => client.post<InvestorProfile>('/profiles', { answers_json: answers }).then(r => r.data),
  /** 获取当前用户的画像 */
  getMine: () => client.get<InvestorProfile | null>('/profiles/me').then(r => r.data),
  /** 更新画像（user_id 从 header 自动获取） */
  update: (profileId: number, answers: Record<string, string | string[]>) => client.put<InvestorProfile>(`/profiles/${profileId}`, { answers_json: answers }).then(r => r.data),
}

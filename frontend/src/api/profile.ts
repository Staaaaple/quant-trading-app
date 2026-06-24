import { delay } from './mock/utils'
import { DEMO_QUESTIONS, DEMO_INVESTOR_PROFILE } from './mock/demoData'

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
  getQuestions: () => delay(300).then(() => DEMO_QUESTIONS as Question[]),
  preview: (answers: Record<string, string | string[]>) =>
    delay(400).then(() => ({
      vector: {
        risk_tolerance: 0.55,
        loss_aversion: 0.60,
        herding_tendency: 0.45,
        overconfidence: 0.40,
        delayed_gratification: 0.65,
        security_need: 0.70,
        time_horizon_score: 0.60,
        experience_level: 0.50,
        capital_tier: 0.55,
        income_stability: 0.65,
        debt_pressure: 0.30,
        information_processing: 0.55,
        social_pressure: 0.40,
        emergency_response: 0.60,
        anchoring_effect: 0.45,
        diversification_preference: 0.65,
        stop_loss_discipline: 0.55,
        emotional_stability: 0.60,
      } as ProfileVector,
      labels: { risk_label: '稳健型', time_horizon_label: '中期', experience_label: '中等' } as ProfileLabels,
    })),
  create: (answers: Record<string, string | string[]>) =>
    delay(500).then(() => ({ ...DEMO_INVESTOR_PROFILE, answers_json: answers } as InvestorProfile)),
  getMine: () => delay(300).then(() => DEMO_INVESTOR_PROFILE as InvestorProfile),
  update: (_profileId: number, answers: Record<string, string | string[]>) =>
    delay(500).then(() => ({ ...DEMO_INVESTOR_PROFILE, answers_json: answers } as InvestorProfile)),
}

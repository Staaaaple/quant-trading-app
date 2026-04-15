const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export interface AccountSettings {
  id: number
  commission_rate: number
  min_commission: number
  stamp_tax_rate: number
  transfer_fee_rate: number
  is_sh_market: boolean
}

export interface AccountSettingsPayload {
  commission_rate: number
  min_commission: number
  stamp_tax_rate: number
  transfer_fee_rate: number
  is_sh_market: boolean
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }
  if (resp.status === 204) {
    return undefined as unknown as T
  }
  return resp.json() as Promise<T>
}

export const accountSettingsApi = {
  get(): Promise<AccountSettings> {
    return request('/account-settings')
  },
  update(payload: AccountSettingsPayload): Promise<AccountSettings> {
    return request('/account-settings', {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  },
}

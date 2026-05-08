import { request } from './client'

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

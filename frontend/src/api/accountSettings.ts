import { delay } from './mock/utils'
import { DEMO_ACCOUNT_SETTINGS } from './mock/demoData'

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
    return delay(300).then(() => DEMO_ACCOUNT_SETTINGS as AccountSettings)
  },
  update(payload: AccountSettingsPayload): Promise<AccountSettings> {
    return delay(400).then(() => ({ ...DEMO_ACCOUNT_SETTINGS, ...payload } as AccountSettings))
  },
}

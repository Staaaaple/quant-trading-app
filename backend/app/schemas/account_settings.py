from pydantic import BaseModel, ConfigDict


class AccountSettingsBase(BaseModel):
    commission_rate: float = 0.00025
    min_commission: float = 5.0
    stamp_tax_rate: float = 0.0005
    transfer_fee_rate: float = 0.00002
    is_sh_market: bool = True


class AccountSettingsCreate(AccountSettingsBase):
    pass


class AccountSettingsRead(AccountSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

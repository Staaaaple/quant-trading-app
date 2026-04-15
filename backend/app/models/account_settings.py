from sqlalchemy import Column, Integer, String, Float, Boolean
from app.db.base import Base


class AccountSettings(Base):
    __tablename__ = "account_settings"

    id = Column(Integer, primary_key=True, index=True)
    commission_rate = Column(Float, default=0.00025)  # 佣金率，默认 0.025%
    min_commission = Column(Float, default=5.0)       # 最低佣金 5 元
    stamp_tax_rate = Column(Float, default=0.0005)    # 印花税率 0.05%
    transfer_fee_rate = Column(Float, default=0.00002) # 过户费率 0.002%
    is_sh_market = Column(Boolean, default=True)      # 是否沪市（用于过户费计算）

from pydantic import BaseModel


class RiskStrategyConfigBase(BaseModel):
    max_position_pct: float = 0.2
    max_daily_drawdown: float = 0.05
    blacklist: str = ""


class RiskStrategyConfigCreate(RiskStrategyConfigBase):
    strategy_id: str


class RiskStrategyConfigUpdate(RiskStrategyConfigBase):
    pass


class RiskStrategyConfigRead(RiskStrategyConfigBase):
    strategy_id: str

    class Config:
        from_attributes = True

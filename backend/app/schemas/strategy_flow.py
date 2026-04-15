from pydantic import BaseModel, ConfigDict
from datetime import datetime


class StrategyFlowBase(BaseModel):
    flow_id: str
    name: str
    picker_strategy_id: str | None = None
    risk_strategy_id: str | None = None
    trade_strategy_id: str


class StrategyFlowCreate(StrategyFlowBase):
    pass


class StrategyFlowUpdate(BaseModel):
    name: str | None = None
    picker_strategy_id: str | None = None
    risk_strategy_id: str | None = None
    trade_strategy_id: str | None = None


class StrategyFlowRead(StrategyFlowBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

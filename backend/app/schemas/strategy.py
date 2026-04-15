from pydantic import BaseModel, ConfigDict
from datetime import datetime


class StrategyBase(BaseModel):
    strategy_id: str
    name: str
    description: str | None = None
    code: str


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    code: str | None = None


class StrategyRead(StrategyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

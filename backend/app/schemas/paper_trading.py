import json

from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime


class PaperTradingSessionBase(BaseModel):
    session_id: str
    strategy_id: str
    symbols: list[str]
    initial_cash: float = 100000.0
    start_date: str | None = None
    end_date: str | None = None
    status: str = "idle"
    logs: str | None = None

    @field_validator("symbols", mode="before")
    @classmethod
    def _parse_symbols_json(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class PaperTradingSessionCreate(BaseModel):
    session_id: str
    strategy_id: str
    symbols: list[str]
    initial_cash: float = 100000.0
    start_date: str | None = None
    end_date: str | None = None


class PaperTradingSessionRead(PaperTradingSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PaperTradingSessionUpdate(BaseModel):
    status: str | None = None
    logs: str | None = None
    end_date: str | None = None


class PaperSignalBase(BaseModel):
    signal_id: str
    strategy_id: str
    symbol: str
    side: str
    quantity: float
    price: float | None = None
    status: str = "pending"
    remark: str | None = None


class PaperSignalCreate(PaperSignalBase):
    pass


class PaperSignalUpdate(BaseModel):
    status: str | None = None
    remark: str | None = None


class PaperSignalRead(PaperSignalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    signal_at: datetime

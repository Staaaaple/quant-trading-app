from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any


class BacktestBase(BaseModel):
    backtest_id: str
    strategy_id: str
    status: str = "pending"
    start_date: str | None = None
    end_date: str | None = None
    initial_cash: float = 100000.0


class BacktestCreate(BacktestBase):
    pass


class BacktestUpdate(BaseModel):
    status: str | None = None
    metrics: dict[str, Any] | None = None
    benchmark_metrics: dict[str, Any] | None = None
    logs: str | None = None
    output_path: str | None = None


class BacktestRead(BacktestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metrics: dict[str, Any] | None = None
    benchmark_metrics: dict[str, Any] | None = None
    logs: str | None = None
    output_path: str | None = None
    created_at: datetime
    updated_at: datetime


class BacktestRunPayload(BaseModel):
    symbols: list[str]
    start_date: str
    end_date: str
    initial_cash: float = 100000.0

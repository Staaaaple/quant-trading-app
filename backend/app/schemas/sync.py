from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RealTradeBase(BaseModel):
    signal_id: str | None = None
    strategy_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float = 0.0
    stamp_tax: float = 0.0
    transfer_fee: float = 0.0
    total_cost: float
    sync_status: str = "synced"
    source: str = "manual"
    remark: str | None = None


class RealTradeCreate(RealTradeBase):
    pass


class RealTradeRead(RealTradeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    synced_at: datetime


class RealPositionBase(BaseModel):
    strategy_id: str
    symbol: str
    quantity: float = 0.0
    available_qty: float = 0.0
    avg_cost: float = 0.0
    total_cost: float = 0.0
    market_value: float = 0.0
    floating_pnl: float = 0.0


class RealPositionRead(RealPositionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


class SyncLogBase(BaseModel):
    signal_id: str | None = None
    strategy_id: str
    symbol: str
    signal_side: str | None = None
    signal_qty: float | None = None
    signal_price: float | None = None
    actual_qty: float | None = None
    actual_price: float | None = None
    diff_reason: str | None = None


class SyncLogCreate(SyncLogBase):
    pass


class SyncLogRead(SyncLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

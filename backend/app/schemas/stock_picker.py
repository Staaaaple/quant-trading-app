from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List


class StockPoolItemBase(BaseModel):
    symbol: str
    name: str | None = None
    score: float | None = None
    reason: str | None = None


class StockPoolItemRead(StockPoolItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class StockPoolBase(BaseModel):
    pool_id: str
    picker_id: str
    name: str
    is_builtin_weekly: bool = False


class StockPoolCreate(StockPoolBase):
    pass


class StockPoolRead(StockPoolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    generated_at: datetime
    expires_at: datetime | None = None
    items: List[StockPoolItemRead] = []


class PickerRunBase(BaseModel):
    run_id: str
    picker_id: str
    status: str = "pending"
    result_count: int | None = None
    logs: str | None = None


class PickerRunRead(PickerRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    finished_at: datetime | None = None


class NotificationSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    weekly_picker_push: bool
    updated_at: datetime


class NotificationSettingsUpdate(BaseModel):
    weekly_picker_push: bool


class RunPickerRequest(BaseModel):
    picker_id: str


class WeeklyPickerSummary(BaseModel):
    has_new_weekly: bool
    pool: StockPoolRead | None = None
    generated_at: datetime | None = None
    item_count: int = 0

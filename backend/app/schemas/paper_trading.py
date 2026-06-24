import json
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class PaperTradingDailyRecordBase(BaseModel):
    record_date: str
    daily_return: float
    cumulative_return: float
    nav: float


class PaperTradingDailyRecordRead(PaperTradingDailyRecordBase):
    id: int
    user_id: int
    portfolio_id: int | None
    report_id: int | None
    asset_snapshot: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PaperTradingMonthlyStatBase(BaseModel):
    year_month: str
    monthly_return: float
    cumulative_return_at_month_end: float
    record_count: int


class PaperTradingMonthlyStatRead(PaperTradingMonthlyStatBase):
    id: int
    user_id: int
    portfolio_id: int | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
